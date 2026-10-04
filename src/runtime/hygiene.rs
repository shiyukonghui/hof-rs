//! DR-25 / DR-28: artifact hygiene.
//!
//! Two report-only scans:
//!
//! * [`OutOfTreeWatch`] answers "did a role write outside the project tree?"
//!   (`smoke-t2` left a `.hoh_live_args/` directory in the repository root and a
//!   bypass `gen_scene.py`, neither of which is visible to the artifact hash),
//!   and
//! * [`suspicious_files`] answers "is the frozen `A_t` littered with probe
//!   files?" (`_probe.gd`, `tmp_args.json`, `*.bak`, ...).
//!
//! Nothing here ever deletes anything: the runtime records, the Planner plans
//! the cleanup, and the Tester judges the gap.

use std::collections::{BTreeMap, BTreeSet};
use std::path::{Path, PathBuf};
use std::time::UNIX_EPOCH;

/// DR-25: at most this many out-of-tree paths are recorded per iteration.
pub const OUT_OF_TREE_LIMIT: usize = 50;
/// DR-28: at most this many suspicious files are recorded.
pub const SUSPICIOUS_LIMIT: usize = 50;

/// Path components that never take part in either scan.
fn ignored_component(name: &str) -> bool {
    matches!(
        name,
        ".git" | ".workspace" | "runs" | "target" | "node_modules"
    ) || name.starts_with(".hoh")
}

/// DR-28: the directories the hygiene scan of a frozen `A_t` ignores.
fn hygiene_ignored(name: &str) -> bool {
    matches!(name, ".hoh" | ".godot" | ".import" | ".git")
}

fn relativize(root: &Path, path: &Path) -> String {
    path.strip_prefix(root)
        .unwrap_or(path)
        .components()
        .map(|component| component.as_os_str().to_string_lossy().into_owned())
        .collect::<Vec<_>>()
        .join("/")
}

/// `relative path -> (byte length, mtime nanos)` of every scanned file.
///
/// Metadata only (no content hashing): the scan runs after every role call, and
/// the question is "did this file change?", which `(len, mtime)` answers.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct TreeSnapshot(pub BTreeMap<String, (u64, u64)>);

/// Scan `root`, skipping the runtime's own trees and the project subtree.
pub fn scan(root: &Path, project: Option<&Path>) -> TreeSnapshot {
    let mut files = BTreeMap::new();
    if !root.exists() {
        return TreeSnapshot(files);
    }
    let project_rel = project.and_then(|project| project.strip_prefix(root).ok());
    let walker = walkdir::WalkDir::new(root)
        .follow_links(false)
        .into_iter()
        .filter_entry(|entry| {
            entry.depth() == 0 || !ignored_component(&entry.file_name().to_string_lossy())
        });
    for entry in walker.flatten() {
        if !entry.file_type().is_file() {
            continue;
        }
        let path = entry.path();
        if let Some(project_rel) = project_rel {
            if !project_rel.as_os_str().is_empty() {
                if let Ok(relative) = path.strip_prefix(root) {
                    if relative.starts_with(project_rel) {
                        continue;
                    }
                }
            }
        }
        let metadata = match entry.metadata() {
            Ok(metadata) => metadata,
            Err(_) => continue,
        };
        let mtime = metadata
            .modified()
            .ok()
            .and_then(|time| time.duration_since(UNIX_EPOCH).ok())
            .map(|duration| duration.as_nanos() as u64)
            .unwrap_or(0);
        files.insert(relativize(root, path), (metadata.len(), mtime));
    }
    TreeSnapshot(files)
}

/// New or modified paths in `after` relative to `before`, sorted and capped.
pub fn changed_paths(before: &TreeSnapshot, after: &TreeSnapshot) -> Vec<String> {
    let mut changed = BTreeSet::new();
    for (path, meta) in &after.0 {
        match before.0.get(path) {
            None => {
                changed.insert(path.clone());
            }
            Some(previous) if previous != meta => {
                changed.insert(path.clone());
            }
            Some(_) => {}
        }
    }
    changed.into_iter().take(OUT_OF_TREE_LIMIT).collect()
}

/// DR-25: watch HoH's own working directory across role calls.
pub struct OutOfTreeWatch {
    root: PathBuf,
    project: Option<PathBuf>,
    last: TreeSnapshot,
    /// DR-79 ①: every path observed since the round started.
    ///
    /// [`observe`](Self::observe)'s return value is consumed by the iteration
    /// it belongs to, so it cannot also answer the round-close question ("what
    /// did this round leave in the root?").  Remembering the union here keeps
    /// that answer independent of the iteration boundary.
    observed: BTreeSet<String>,
}

impl OutOfTreeWatch {
    pub fn new(root: PathBuf, project: Option<PathBuf>) -> Self {
        let last = scan(&root, project.as_deref());
        Self {
            root,
            project,
            last,
            observed: BTreeSet::new(),
        }
    }

    /// Diff the tree against the previous observation and advance the baseline.
    pub fn observe(&mut self) -> Vec<String> {
        let now = scan(&self.root, self.project.as_deref());
        let changed = changed_paths(&self.last, &now);
        self.last = now;
        self.observed.extend(changed.iter().cloned());
        changed
    }

    /// DR-79 ①: every path the watch saw appear or change during the round.
    pub fn observed(&self) -> Vec<String> {
        self.observed.iter().cloned().collect()
    }
}

/// DR-79 ①: is `relative` one of the **root-level temporary** shapes a role
/// leaves behind in the scanned root?
///
/// This is the whole eligibility rule for
/// [`clean_round_temporaries`], and it is deliberately narrow: a single path
/// component, and a name shape that reads as round scratch.  A project file
/// never matches, and no path with a separator matches, so the cleanup cannot
/// reach into a project or another directory even if the watcher reported one.
///
/// DR-81 ④ widens the shape with [`is_round_scratch_name`].  DR-79's four
/// families (`.tmp_*`, `tmp_*`, `*.tmp`, `*.bak`) could not see `smoke-t14`'s
/// root litter (`l.json`, `p2.json`, `pv.json`, `r.json` — the Tester's own
/// scenario/args payloads), so the round left them in the repository root.
pub fn is_root_temporary(relative: &str) -> bool {
    if relative.is_empty() || relative.contains('/') || relative.contains('\\') {
        return false;
    }
    if relative == "." || relative == ".." {
        return false;
    }
    let lower = relative.to_ascii_lowercase();
    lower.starts_with(".tmp_")
        || lower.starts_with("tmp_")
        || lower.ends_with(".tmp")
        || lower.ends_with(".bak")
        || is_round_scratch_name(&lower)
}

/// DR-81 ④: the extensions a round's own root scratch payload carries.
///
/// Measured: every one of `smoke-t14`'s four survivors is a `.json` written for
/// an MCP `--args-file` / scenario call.  `.txt`, `.log` and the like are
/// **not** in the set: a text file in the repository root is exactly the shape a
/// deliberate, content-bearing out-of-tree write takes, and the cleanup must not
/// be able to destroy one.
pub const ROOT_SCRATCH_EXTENSIONS: &[&str] = &["json"];

/// DR-81 ④: the longest stem that still reads as a machine-generated scratch name
/// rather than a deliberate document (`l`, `p2`, `pv`, `r` are 1–2 characters).
/// The bound is what keeps `analysis.json` / `results.json` — and any other
/// plausibly hand-authored payload — out of the cleanup.
pub const ROOT_SCRATCH_STEM_MAX: usize = 4;

/// DR-81 ④: the largest payload a scratch removal may touch.  A real scratch
/// payload is a small argument file; a large JSON in the repository root is a
/// product, so it is left alone (and stays reported in `out_of_tree_writes`).
pub const ROOT_SCRATCH_MAX_BYTES: u64 = 8192;

/// DR-81 ④: is `lower` (already lower-cased) a terse round-scratch name — a short
/// `[a-z0-9_]` stem plus a [`ROOT_SCRATCH_EXTENSIONS`] extension?
///
/// This is a **name-shape** rule inside the bigger eligibility rule: the caller
/// has already proved the path is one component of the round's scanned root and
/// that the watcher saw the round create it, and only a regular file is ever
/// removed.  A directory, a nested path and any file that pre-dates the round can
/// never match.
pub fn is_round_scratch_name(lower: &str) -> bool {
    let Some((stem, extension)) = lower.rsplit_once('.') else {
        return false;
    };
    if stem.is_empty() || stem.len() > ROOT_SCRATCH_STEM_MAX {
        return false;
    }
    if !stem.chars().all(|character| {
        character.is_ascii_lowercase() || character.is_ascii_digit() || character == '_'
    }) {
        return false;
    }
    ROOT_SCRATCH_EXTENSIONS.contains(&extension)
}

/// DR-79 ①: remove the round's own known temporary files from the scanned root,
/// returning the relative paths actually removed.
///
/// Report-only was the whole of DR-25, and the measured cost is a repository
/// root that keeps accumulating untracked litter: `smoke-t13`'s Developer left
/// `.tmp_coin.json` / `.tmp_goal.json` / `.tmp_hud.json` in `F:\moonbit-hof-rs`
/// and `result.json.out_of_tree_writes` recorded them without anything ever
/// removing them.  The containment is bounded by construction:
///
/// * a path must come from `observed` — the watcher's own diff against the
///   tree as it was when the round started, so a file that was already there is
///   never touched;
/// * [`is_root_temporary`] must accept it: exactly one path component and a
///   temporary name shape (DR-81 ④ adds the terse round-scratch family);
/// * a path matched only by the DR-81 scratch family must additionally be a
///   **small regular file** ([`ROOT_SCRATCH_MAX_BYTES`]), never a directory;
/// * only a **file** is removed (never a directory, never a wildcard, never
///   `rm`), and the joined path is re-checked to be a direct child of `root`.
///
/// The caller records the returned names, so the removal is part of the round's
/// own record rather than a silent side effect.  A genuine out-of-tree write is
/// not destroyed: it survives when it pre-dates the round, sits in a
/// subdirectory, carries a non-scratch extension, has a stem longer than
/// [`ROOT_SCRATCH_STEM_MAX`], or is larger than [`ROOT_SCRATCH_MAX_BYTES`] — and
/// in every case the write remains a fact in `out_of_tree_writes`.
pub fn clean_round_temporaries(root: &Path, observed: &[String]) -> Vec<String> {
    let mut removed: Vec<String> = Vec::new();
    for relative in observed {
        if !is_root_temporary(relative) {
            continue;
        }
        // `is_root_temporary` proved this is one component with no separator, so
        // the join cannot escape `root`; the parent check states that invariant
        // in code rather than leaving it to the reader.
        let path = root.join(relative);
        if path.parent() != Some(root) {
            continue;
        }
        if !path.is_file() {
            continue;
        }
        if is_round_scratch_name(&relative.to_ascii_lowercase()) {
            let Ok(metadata) = path.metadata() else {
                continue;
            };
            if metadata.len() > ROOT_SCRATCH_MAX_BYTES {
                continue;
            }
        }
        if std::fs::remove_file(&path).is_ok() {
            removed.push(relative.clone());
        }
    }
    removed.sort();
    removed
}

/// DR-28: probe/litter files inside a frozen `A_t`, relative to its root.
///
/// Patterns: `_*`, `tmp_*`, `*.bak`, `*.tmp`, plus suspicious helper scripts
/// left at the project root (`*.py`, `*.sh`, `*.ps1` — the `gen_scene.py`
/// bypass that produced the invalid `main.tscn` of `smoke-t2`).
pub fn suspicious_files(root: &Path) -> Vec<String> {
    let mut found = BTreeSet::new();
    if !root.exists() {
        return Vec::new();
    }
    let walker = walkdir::WalkDir::new(root)
        .follow_links(false)
        .into_iter()
        .filter_entry(|entry| {
            entry.depth() == 0 || !hygiene_ignored(&entry.file_name().to_string_lossy())
        });
    for entry in walker.flatten() {
        if !entry.file_type().is_file() {
            continue;
        }
        let relative = relativize(root, entry.path());
        let name = entry.file_name().to_string_lossy().to_ascii_lowercase();
        let pattern_hit = name.starts_with('_')
            || name.starts_with("tmp_")
            || name.ends_with(".bak")
            || name.ends_with(".tmp");
        let root_helper_script = !relative.contains('/')
            && (name.ends_with(".py") || name.ends_with(".sh") || name.ends_with(".ps1"));
        if pattern_hit || root_helper_script {
            found.insert(relative);
        }
    }
    found.into_iter().take(SUSPICIOUS_LIMIT).collect()
}

/// DR-69: probe/litter **directories** inside a frozen `A_t`, relative to its
/// root.
///
/// `smoke-t9` produced one under `cmd`: `mkdir -p "<scratch>/args"` does not have
/// POSIX semantics there, so it created a literal directory named `-p` next to
/// the intended one.  The empty directory is invisible to the content hash and
/// to [`suspicious_files`] (which only ever looks at files), and it was carried
/// into `A_0` and every snapshot that follows.  A name that only a shell
/// accident or an unexpanded variable can produce is reported here.
pub fn suspicious_directories(root: &Path) -> Vec<String> {
    let mut found = BTreeSet::new();
    if !root.exists() {
        return Vec::new();
    }
    let walker = walkdir::WalkDir::new(root)
        .follow_links(false)
        .into_iter()
        .filter_entry(|entry| {
            entry.depth() == 0 || !hygiene_ignored(&entry.file_name().to_string_lossy())
        });
    for entry in walker.flatten() {
        if !entry.file_type().is_dir() || entry.depth() == 0 {
            continue;
        }
        let name = entry.file_name().to_string_lossy().into_owned();
        let lower = name.to_ascii_lowercase();
        // A leading `-` is a shell option that was taken as a name (`-p`, `-r`);
        // `%VAR%`/`$VAR` is an unexpanded variable; the rest are the DR-28 probe
        // shapes applied to a directory.
        let pattern_hit = lower.starts_with('-')
            || lower.starts_with('_')
            || lower.starts_with("tmp_")
            || lower.ends_with(".bak")
            || lower.ends_with(".tmp")
            || name.contains('%')
            || name.contains('$');
        if pattern_hit {
            found.insert(relativize(root, entry.path()));
        }
    }
    found.into_iter().take(SUSPICIOUS_LIMIT).collect()
}

/// DR-26/DR-32/DR-38: does this **tool command or argument** mention the harness
/// sources, the harness repository root, or an external repository checkout?
/// Report-only: behaviour never changes.
///
/// DR-32: the marker set is only ever applied to tool text.  The whole-repo
/// variants are deliberately broad (`src/`, `.spec/`) because the prompts
/// themselves name those paths, so anything narrower would miss a real read —
/// see [`mentions_forbidden_source_in_actions`].
///
/// DR-38: `smoke-t5` produced two detours the old set missed — `dir` over the
/// repository root and `dir /b /s *.yaml | findstr hoh` — because the set named
/// neither `config/**`, `DECISIONS.md`, `Cargo.toml` nor the repository root.
pub fn mentions_forbidden_source(text: &str) -> bool {
    const MARKERS: &[&str] = &[
        "src/",
        "src\\",
        ".spec/",
        ".spec\\",
        "tests/fixtures",
        "tests/common",
        "tests\\common",
        "RustProjects",
        ".git/",
        ".git\\",
        // DR-38: the rest of the harness repository.
        "config/",
        "config\\",
        "DECISIONS.md",
        "Cargo.toml",
    ];
    MARKERS.iter().any(|marker| text.contains(marker))
}

/// DR-38: verbs that walk or search a directory tree.
const LISTING_VERBS: &[&str] = &[
    "dir",
    "ls",
    "find",
    "findstr",
    "grep",
    "get-childitem",
    "gci",
    "tree",
    "select-string",
];

/// DR-38: is this text a *whole-tree* enumeration (a wildcard or an explicit
/// recursive flag)?  A plain `dir scenes` names one directory and is not.
fn has_enumerating_pattern(text: &str) -> bool {
    if text.contains("*.") || text.contains("**") {
        return true;
    }
    text.to_ascii_lowercase()
        .split_whitespace()
        .any(|token| matches!(token, "/s" | "-r" | "-recurse" | "--recursive"))
}

/// DR-38: does the command aim at the harness itself by name?
///
/// `.hoh` is the runtime's own artifact directory, so listing
/// `.hoh/deterministic/*.json` is ordinary in-project work — the runtime's own
/// name is removed before the harness token is looked for.
fn contains_harness_token(text: &str) -> bool {
    let lowered = text.to_ascii_lowercase().replace(".hoh", "");
    ["harness", "hof-rs", "decisions.md", "cargo.toml"]
        .iter()
        .any(|token| lowered.contains(token))
        || lowered.contains("hoh")
}

/// DR-38: a recursive listing/search aimed at the harness tree (the second
/// `smoke-t5` detour: `dir /b /s *.yaml | findstr hoh`).
pub fn enumerates_harness_tree(text: &str) -> bool {
    LISTING_VERBS.iter().any(|verb| text.contains(verb))
        && has_enumerating_pattern(text)
        && contains_harness_token(text)
}

/// DR-38: the harness repository root is injected at runtime (never hard-coded
/// into `src/**`), so a command that names it in either separator style counts.
pub fn mentions_harness_root(text: &str, harness_root: &Path) -> bool {
    fn normalize(value: &str) -> String {
        value.replace('\\', "/").to_ascii_lowercase()
    }
    let root = normalize(&harness_root.to_string_lossy());
    !root.is_empty() && normalize(text).contains(&root)
}

/// DR-32/DR-38: scan **only** the tool calls of a trajectory (`messages[*].
/// extra.actions[*]`, plus the arguments nested inside them).
///
/// `smoke-t3` produced an unconditional `harness_source_read` warning: the
/// detector ran over the raw trajectory text, where the system prompt's own
/// "never read `src/**`" sentence matched.  The prompt can never be evidence of
/// what the role *did*.
pub fn mentions_forbidden_source_in_actions(trajectory: &str) -> bool {
    mentions_forbidden_source_in_actions_with_root(trajectory, None)
}

/// DR-38: the same scan with the harness repository root injected.
pub fn mentions_forbidden_source_in_actions_with_root(
    trajectory: &str,
    harness_root: Option<&Path>,
) -> bool {
    let Ok(value) = serde_json::from_str::<serde_json::Value>(trajectory) else {
        return false;
    };
    let Some(messages) = value.get("messages").and_then(serde_json::Value::as_array) else {
        return false;
    };
    for message in messages {
        let Some(actions) = message
            .get("extra")
            .and_then(|extra| extra.get("actions"))
            .and_then(serde_json::Value::as_array)
        else {
            continue;
        };
        for action in actions {
            let mut stack = vec![action];
            while let Some(node) = stack.pop() {
                match node {
                    serde_json::Value::String(text) => {
                        let hit = mentions_forbidden_source(text)
                            || enumerates_harness_tree(text)
                            || harness_root
                                .map(|root| mentions_harness_root(text, root))
                                .unwrap_or(false);
                        if hit {
                            return true;
                        }
                    }
                    serde_json::Value::Array(items) => stack.extend(items.iter()),
                    serde_json::Value::Object(fields) => stack.extend(fields.values()),
                    _ => {}
                }
            }
        }
    }
    false
}

// ---------------------------------------------------------------------------
// DR-59/DR-61: the previous round's evidence must not be READABLE here
// ---------------------------------------------------------------------------

/// DR-59: the workspace-relative deterministic evidence area (DR-17).
pub const DETERMINISTIC_EVIDENCE_DIR: &str = ".hoh/deterministic";

/// DR-61: the runtime artifact directory itself — the whole tree a previous
/// round leaves behind.
pub const ARTIFACT_DIR: &str = ".hoh";

/// DR-61: the evidence *artifact* area (DR-36 screenshots, replays, recordings).
/// One of the families a measured two-round replay found reachable inside
/// [`ARTIFACT_DIR`].
pub const EVIDENCE_DIR: &str = ".hoh/evidence";

/// DR-61: the single evidence bundle path.  The Developer rewrites it, but it is
/// role-writable, so it is inside the quarantined tree like everything else.
pub const EVIDENCE_BUNDLE: &str = ".hoh/evidence.json";

/// DR-61: the MCP argument payloads roles write for `--args-file`.
pub const ARGS_DIR: &str = ".hoh/args";

/// DR-61: the DR-28 probe scratch area.
pub const SCRATCH_DIR: &str = ".hoh/scratch";

/// DR-61: the run-directory child the previous round's bytes are moved under.
///
/// It is a child of `runs/<run_id>` — **outside** the workspace, outside every
/// role's working directory (`workspace`, `runs/<id>/iter-<n>/planner-view`,
/// `runs/<id>/iter-<n>/candidate`), and outside the run directory's own
/// iteration tree.  Being the run directory's child (rather than a sibling of
/// it) keeps `hoh status`'s `latest_run_id` — which lists the *directories* of
/// `runs/` — from mistaking a quarantine for a run, and puts the bytes under the
/// DR-19 secret scan, which walks `runs/<id>/**`.
pub const QUARANTINE_DIR: &str = "quarantine";

/// DR-61: what a round start takes out of the read path.
///
/// **One entry — the whole [`ARTIFACT_DIR`] tree — and that is a measured
/// decision, not a shortcut.**  The batch began from a curated list of the areas
/// a two-round replay measured as reachable leftovers
/// ([`DETERMINISTIC_EVIDENCE_DIR`], [`EVIDENCE_DIR`], [`EVIDENCE_BUNDLE`],
/// [`ARGS_DIR`], [`SCRATCH_DIR`]).  The regression test then seeded **every**
/// `.hoh` sibling a real workspace carries (the `smoke-t7` pre-run inventory
/// plus `.workspace/mario/.hoh`) and measured what the round overwrites:
/// `.hoh/{TASK.md,plan.md,TOOLS.md,EVIDENCE_HISTORY.md,PROJECT_MAP.md}` and
/// `.hoh/skills/**` are rewritten by `write_inputs` before the Developer
/// (`run_loop.rs:672-697`) — but `.hoh/SCAFFOLD.md`, which the runtime injects
/// into the *views* only (`run_loop.rs:498`), and any other role-authored
/// `.hoh/<name>` are **not**.  A curated list therefore cannot make "a walk of
/// `.hoh` cannot reach the previous round's bytes" true; only moving the whole
/// tree can.  `.hoh` is the runtime's own artifact directory throughout and is
/// excluded from the artifact identity (`policy.rs`), so the move cannot perturb
/// `A_0`/`A_t`; a round tolerates a missing `.hoh`, because every producer and
/// `write_inputs` create the directories they write into.
pub const QUARANTINE_AREAS: &[&str] = &[ARTIFACT_DIR];

/// DR-49/DR-59: how many `.stale-` names are tried before the rename gives up.
const STALE_NAME_ATTEMPTS: u32 = 64;

/// DR-62: the explicit **supersession manifest**: a JSON list of the paths
/// (relative to the directory that holds it) the runtime has superseded.
///
/// DR-49/DR-61 decided "a superseded file must not enter the frozen candidate"
/// with a *filename* predicate (`is_expired_name`, i.e.
/// `name.contains(".stale-")`).  Independent acceptance measured the defect that
/// convention creates: a role that names **this round's** artifact `*.stale-*`
/// has it silently hidden from the Tester.  DR-62 therefore decides on a
/// structural fact — the explicit record the producer writes — and a name alone
/// means nothing at all.
///
/// The manifest is per-directory, so a lookup consults the manifest of the copy
/// root and of every directory on the way to the entry (see [`is_superseded`]);
/// the manifest file itself is runtime bookkeeping, never view content
/// ([`is_runtime_bookkeeping`]).
pub const SUPERSEDED_MANIFEST: &str = ".superseded.json";

/// DR-62: is this relative path (or one of its components) the supersession
/// manifest itself?  Runtime bookkeeping must not be copied into a view.
pub fn is_runtime_bookkeeping(relative: &str) -> bool {
    relative
        .split('/')
        .any(|component| component == SUPERSEDED_MANIFEST)
}

/// DR-62: what was superseded, as an explicit record rather than a name shape.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct SupersededSet {
    entries: BTreeSet<String>,
}

impl SupersededSet {
    /// Read the manifest of `directory`.
    ///
    /// A missing manifest is the normal case and yields an empty set.  An
    /// unreadable or malformed one is an **error**: a corrupt record must never
    /// silently re-admit superseded bytes into a view.
    pub fn load(directory: &Path) -> std::io::Result<Self> {
        let path = directory.join(SUPERSEDED_MANIFEST);
        if !path.exists() {
            return Ok(Self::default());
        }
        let text = std::fs::read_to_string(&path)?;
        let entries: Vec<String> = serde_json::from_str(&text).map_err(|error| {
            std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                format!(
                    "DR-62: {} is not a JSON list of superseded paths: {error}",
                    path.display()
                ),
            )
        })?;
        Ok(Self {
            entries: entries.into_iter().collect(),
        })
    }

    /// How many supersessions are recorded.
    pub fn len(&self) -> usize {
        self.entries.len()
    }

    /// Is nothing recorded?
    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    /// Is `relative` (relative to the manifest's directory) recorded?
    pub fn contains(&self, relative: &str) -> bool {
        self.entries.contains(relative)
    }

    /// DR-62: record `relative` as superseded in `directory`'s manifest,
    /// creating or extending it.  Returns the manifest path it wrote.
    pub fn record(directory: &Path, relative: &str) -> std::io::Result<PathBuf> {
        let path = directory.join(SUPERSEDED_MANIFEST);
        let mut set = Self::load(directory)?;
        if set.entries.insert(relative.to_string()) {
            let list: Vec<&str> = set.entries.iter().map(String::as_str).collect();
            let mut text = serde_json::to_string_pretty(&list)
                .map_err(|error| std::io::Error::new(std::io::ErrorKind::InvalidData, error))?;
            text.push('\n');
            std::fs::write(&path, text)?;
        }
        Ok(path)
    }
}

/// DR-62: is `relative` (a path relative to `root`) explicitly recorded as
/// superseded, by the manifest of `root` or of any directory on the way to it?
pub fn is_superseded(root: &Path, relative: &str) -> std::io::Result<bool> {
    let mut directory = root.to_path_buf();
    let mut remaining = relative;
    loop {
        if SupersededSet::load(&directory)?.contains(remaining) {
            return Ok(true);
        }
        match remaining.split_once('/') {
            Some((head, tail)) => {
                directory.push(head);
                remaining = tail;
            }
            None => return Ok(false),
        }
    }
}

/// DR-49: what an artifact looked like at one instant.
///
/// Freshness is decided on the artifact **state**, so "a file exists at the
/// target" can never be enough on its own: a file left behind by an earlier
/// round has the same path but not the same bytes/metadata.  This is
/// engine-neutral: it is the producer half of the DR-49/DR-62 contract every
/// adapter that writes a file artifact has to honour.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ArtifactFingerprint {
    pub size: u64,
    /// Modification time in nanoseconds since the Unix epoch.
    pub mtime_unix_nanos: u128,
    pub sha256: String,
}

/// DR-49: the fingerprint of `path`, or `None` when there is no readable file.
pub fn artifact_fingerprint(path: &Path) -> Option<ArtifactFingerprint> {
    let metadata = std::fs::metadata(path).ok()?;
    if !metadata.is_file() {
        return None;
    }
    let bytes = std::fs::read(path).ok()?;
    let mtime_unix_nanos = metadata
        .modified()
        .ok()
        .and_then(|time| {
            time.duration_since(std::time::UNIX_EPOCH)
                .ok()
                .map(|duration| duration.as_nanos())
        })
        .unwrap_or(0);
    Some(ArtifactFingerprint {
        size: metadata.len(),
        mtime_unix_nanos,
        sha256: crate::runtime::policy::sha256_hex(&bytes),
    })
}

/// DR-49 ③: did **this** call produce the artifact?
///
/// * nothing on disk — never fresh (a `path` may not be claimed);
/// * nothing before, something now — fresh;
/// * something before and after — fresh only when the bytes or the timestamp
///   actually changed, i.e. when this call rewrote it.
pub fn artifact_is_fresh(
    before: Option<&ArtifactFingerprint>,
    after: Option<&ArtifactFingerprint>,
) -> bool {
    match (before, after) {
        (_, None) => false,
        (None, Some(_)) => true,
        (Some(before), Some(after)) => before != after,
    }
}

/// DR-49 ②: get a pre-existing artifact out of the target path **before** the
/// call, so "the file exists" cannot be satisfied by an older round.
///
/// It is renamed to `<name>.stale-<unix seconds>` rather than deleted: the old
/// artifact stays auditable (it is hidden from the artifact hash — `.hoh` is
/// excluded — and from the hygiene scans, which ignore `.hoh`), while the
/// target itself is empty for the duration of the call.  `None` means there was
/// nothing to invalidate.
///
/// DR-62: the move is accompanied by an explicit [`SupersededSet::record`] in
/// the directory the artifact lives in, and that record — not the
/// `.stale-<ts>` name — is what the candidate-view copies consult.  The record
/// happens **before** the rename: if it cannot be written the invalidation
/// fails loudly rather than moving the bytes aside with no structural trace.
pub fn invalidate_artifact(path: &Path) -> std::io::Result<Option<String>> {
    if !path.is_file() {
        return Ok(None);
    }
    let base = path
        .file_name()
        .map(|name| name.to_string_lossy().into_owned())
        .unwrap_or_else(|| "artifact".to_string());
    let stamp = crate::adapter::engine::now_seconds();
    for attempt in 0..64u32 {
        // DR-59: one naming convention for both producer sites — this one and
        // [`quarantine_previous_evidence`].
        let name = stale_name(&base, stamp, attempt);
        let candidate = path.with_file_name(&name);
        if !candidate.exists() {
            // DR-62: the structural record first (see the doc comment above).
            if let Some(directory) = path.parent() {
                SupersededSet::record(directory, &name)?;
            }
            std::fs::rename(path, &candidate)?;
            return Ok(Some(name));
        }
    }
    // The name space is a per-second window of 64 names; if it is exhausted the
    // invalidation must still happen, so the file is removed instead of being
    // silently left in place (which would let a stale file be claimed).
    std::fs::remove_file(path)?;
    Ok(Some(format!(
        "{base} (removed: no free .stale-{stamp} name)"
    )))
}

/// DR-49/DR-59: the name a superseded path is moved to.
///
/// One naming convention, two producer sites: [`invalidate_artifact`] (DR-49,
/// the pre-existing file artifact) and [`quarantine_previous_evidence`] (DR-59,
/// the whole evidence directory).  Keeping the suffix in one place keeps
/// "superseded" greppable and auditable across the repository.
///
/// DR-62: this is a **producer-side audit name only**.  No consumer decides
/// anything from it any more — the skip criterion is the explicit
/// [`SUPERSEDED_MANIFEST`] record — so a file a role happens to name
/// `*.stale-*` is never hidden (see `view::copy_evidence` / `view::copy_tree`).
pub fn stale_name(base: &str, stamp: u64, attempt: u32) -> String {
    if attempt == 0 {
        format!("{base}.stale-{stamp}")
    } else {
        format!("{base}.stale-{stamp}-{attempt}")
    }
}

/// DR-59: is there anything to move aside?
///
/// Whether a round needs to quarantine is decided by the state on disk, never
/// unconditionally: a clean round start must not litter the workspace *or the
/// run directory* with an empty `*.stale-*` sibling / `quarantine/` directory.
fn should_quarantine(live: &Path) -> bool {
    live.exists()
}

/// DR-61: one workspace-relative area moved out of the round's read path.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct QuarantinedArea {
    /// The workspace-relative live path that was moved, e.g. `.hoh/deterministic`.
    pub live: &'static str,
    /// Where it now lives — outside every role's working directory.
    pub target: PathBuf,
}

/// DR-61: is `destination` inside `workspace` (lexically, and — when both ends
/// exist — after canonicalization, so a symlink or junction cannot smuggle the
/// destination back into the role's cwd)?
fn destination_is_inside_workspace(workspace: &Path, destination: &Path) -> bool {
    let lexical = crate::runtime::invoke::absolute_path(destination)
        .starts_with(crate::runtime::invoke::absolute_path(workspace));
    let canonical = match (
        std::fs::canonicalize(workspace),
        std::fs::canonicalize(destination),
    ) {
        (Ok(workspace), Ok(destination)) => destination.starts_with(&workspace),
        _ => false,
    };
    lexical || canonical
}

/// DR-59/DR-61: move the previous round's evidence **out of the role's working
/// directory** before any role of the new round runs.
///
/// `smoke-t7` proved the leak is real, not theoretical: that round started with
/// `smoke-t6`'s `.hoh/deterministic/**` still on disk, the Developer read it, and
/// `runs/smoke-t7/iter-1/traj/developer.attempt1.json` `.messages[54]` carries
/// the *previous* round's `pid 108432`, its "the editor is not clean" verdict and
/// its `os error 10061` transport failure into the new round's model context.
///
/// DR-59 moved those bytes to `<workspace>/.hoh/deterministic.stale-<ts>/` —
/// still inside the role's cwd, so a wildcard read (`ls .hoh`) still reached
/// them; independent acceptance measured exactly that (DEF-1) and measured that
/// `.hoh/evidence/**` was never isolated at all (DEF-2).  DR-61 therefore moves
/// every [`QUARANTINE_AREAS`] entry to `runs/<run_id>/quarantine/<name>.stale-<ts>`,
/// which a traversal of the working directory cannot reach.
///
/// The evidence is **renamed, never deleted**: the previous round's readings stay
/// on disk — and out of the artifact hash, because `.hoh` is excluded (DR-11) —
/// under the repository's DR-49 `.stale-<ts>` convention, which is already the
/// marker this code base uses for "superseded, do not trust".  Returns one
/// [`QuarantinedArea`] per area that was moved, and an empty vector when the
/// round started clean.
pub fn quarantine_previous_evidence(
    workspace: &Path,
    run_dir: &Path,
) -> anyhow::Result<Vec<QuarantinedArea>> {
    let existing: Vec<&'static str> = QUARANTINE_AREAS
        .iter()
        .copied()
        .filter(|area| should_quarantine(&workspace.join(area)))
        .collect();
    if existing.is_empty() {
        return Ok(Vec::new());
    }

    let root = run_dir.join(QUARANTINE_DIR);
    // DR-61: structural precondition.  A destination inside the workspace would
    // reproduce exactly the defect this decision removes, so the round stops
    // loudly instead of pretending to isolate.
    if crate::runtime::invoke::absolute_path(&root)
        .starts_with(crate::runtime::invoke::absolute_path(workspace))
    {
        anyhow::bail!(
            "DR-61: refusing to quarantine into {} — it is inside the workspace {}; the \
             previous round's evidence would still be reachable from every role's cwd",
            root.display(),
            workspace.display()
        );
    }
    std::fs::create_dir_all(&root)?;
    if destination_is_inside_workspace(workspace, &root) {
        // Remove the empty directory this call just created before failing.
        let _ = std::fs::remove_dir(&root);
        anyhow::bail!(
            "DR-61: refusing to quarantine into {} — it resolves inside the workspace {}",
            root.display(),
            workspace.display()
        );
    }

    let stamp = crate::adapter::engine::now_seconds();
    let mut moved = Vec::new();
    for area in existing {
        let live = workspace.join(area);
        let base = live
            .file_name()
            .map(|name| name.to_string_lossy().into_owned())
            .unwrap_or_else(|| area.rsplit('/').next().unwrap_or(area).to_string());
        let mut target = None;
        for attempt in 0..STALE_NAME_ATTEMPTS {
            let candidate = root.join(stale_name(&base, stamp, attempt));
            if !candidate.exists() {
                target = Some(candidate);
                break;
            }
        }
        // DR-49's single-file case may fall back to deleting once its name window
        // is exhausted.  A whole round of evidence must not be deleted, and must
        // not be left in the live path either — both outcomes would break this
        // decision — so the round stops loudly instead.
        let Some(target) = target else {
            anyhow::bail!(
                "DR-61: could not move {area} aside: all {STALE_NAME_ATTEMPTS} \
                 `.stale-{stamp}` names under {} are taken",
                root.display()
            )
        };
        std::fs::rename(&live, &target)?;
        moved.push(QuarantinedArea { live: area, target });
    }
    Ok(moved)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn write(path: &Path, content: &str) {
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent).unwrap();
        }
        std::fs::write(path, content).unwrap();
    }

    #[test]
    fn the_watch_reports_new_and_modified_files_once() {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path();
        write(&root.join("project/keep.txt"), "project\n");
        let mut watch = OutOfTreeWatch::new(root.to_path_buf(), Some(root.join("project")));

        write(&root.join("stray.txt"), "out of tree\n");
        assert_eq!(watch.observe(), vec!["stray.txt".to_string()]);
        assert!(
            watch.observe().is_empty(),
            "an unchanged tree must not be reported twice"
        );

        write(&root.join("stray.txt"), "changed\n");
        assert_eq!(watch.observe(), vec!["stray.txt".to_string()]);
    }

    #[test]
    fn the_watch_ignores_the_runtime_trees_and_the_project() {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path();
        let mut watch = OutOfTreeWatch::new(root.to_path_buf(), Some(root.join("project")));
        write(&root.join("project/new.txt"), "x\n");
        write(&root.join("runs/run-1/x.json"), "{}\n");
        write(&root.join("target/debug/x"), "x\n");
        write(&root.join(".hoh_live_args/a.json"), "{}\n");
        write(&root.join(".git/objects/x"), "x\n");
        assert!(watch.observe().is_empty(), "{:?}", watch.observe());
    }

    #[test]
    fn suspicious_files_matches_probe_patterns() {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path();
        write(&root.join("_probe.gd"), "x\n");
        write(&root.join("tmp_x.json"), "{}\n");
        write(&root.join("scripts/_helper.gd"), "x\n");
        write(&root.join("notes.bak"), "x\n");
        write(&root.join("clean.gd"), "x\n");
        write(&root.join("project.godot"), "x\n");
        let found = suspicious_files(root);
        assert_eq!(
            found,
            vec![
                "_probe.gd".to_string(),
                "notes.bak".to_string(),
                "scripts/_helper.gd".to_string(),
                "tmp_x.json".to_string(),
            ]
        );
    }

    /// DR-32: the prompt is not evidence; a tool command is.
    #[test]
    fn the_source_read_scan_ignores_prompts_and_reads_tool_commands() {
        let prompt_only = serde_json::json!({
            "messages": [
                {"role": "system", "content": "never read src/runtime/** or .spec/**",
                 "extra": {"actions": []}},
                {"role": "assistant", "content": "sure", "extra": {"actions": []}}
            ]
        })
        .to_string();
        assert!(
            !mentions_forbidden_source_in_actions(&prompt_only),
            "a prompt that names the forbidden paths is not a read"
        );

        let with_command = serde_json::json!({
            "messages": [
                {"role": "system", "content": "never read src/runtime/**"},
                {"role": "assistant", "content": "",
                 "extra": {"actions": [{"command": "cat src/config.rs"}]}}
            ]
        })
        .to_string();
        assert!(mentions_forbidden_source_in_actions(&with_command));

        // The arguments nested inside an action count too.
        let args_only = serde_json::json!({
            "messages": [{"role": "assistant", "extra": {"actions": [
                {"command": "hoh tools call project_read_script",
                 "args": {"path": "F:\\RustProjects\\godot-mcp-pro\\x.gd"}}
            ]}}]
        })
        .to_string();
        assert!(mentions_forbidden_source_in_actions(&args_only));

        // A trajectory that is not JSON yields no evidence (never a guess).
        assert!(!mentions_forbidden_source_in_actions("not json"));
    }

    /// DR-69: the directory-shaped litter a file-only scan cannot see.  The
    /// `-p` name is the measured one (`smoke-t9`; `mkdir -p` under cmd).
    #[test]
    fn suspicious_directories_sees_the_shell_accident_a_file_scan_misses() {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path();
        std::fs::create_dir_all(root.join("-p")).unwrap();
        std::fs::create_dir_all(root.join("scripts/_helpers")).unwrap();
        std::fs::create_dir_all(root.join("scenes")).unwrap();
        std::fs::create_dir_all(root.join(".hoh/scratch/tmp_probe")).unwrap();
        std::fs::create_dir_all(root.join("%TEMP%")).unwrap();

        let found = suspicious_directories(root);
        assert_eq!(
            found,
            vec![
                "%TEMP%".to_string(),
                "-p".to_string(),
                "scripts/_helpers".to_string(),
            ],
            "the `-p`/`_`/`%VAR%` shapes are litter; `scenes` is content and `.hoh` is the runtime's own tree"
        );
        // The measured blind spot: a file-only scan reports nothing at all.
        assert!(
            suspicious_files(root).is_empty(),
            "the file scan is blind to directories -- that is the defect"
        );
    }

    #[test]
    fn suspicious_files_ignores_the_runtime_directories() {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path();
        write(&root.join(".hoh/scratch/_probe.gd"), "x\n");
        write(&root.join(".godot/_tmp_cache"), "x\n");
        write(&root.join("scenes/main.tscn"), "x\n");
        assert!(suspicious_files(root).is_empty());
    }

    /// DR-79 ①: the eligibility rule is deliberately narrow — one path
    /// component, and only the temporary shapes a role actually leaves behind.
    /// A project file, a nested file and a directory are never eligible, so the
    /// cleanup can never reach project content.
    #[test]
    fn only_root_level_temporary_shapes_are_round_litter() {
        for name in [
            ".tmp_coin.json",
            ".tmp_hud.json",
            "tmp_args.json",
            "notes.tmp",
            "notes.bak",
        ] {
            assert!(is_root_temporary(name), "`{name}` is the measured shape");
        }
        for name in [
            "project.godot",
            "scenes/main.tscn",
            "runs/x.json",
            "sub/.tmp_x.json",
            "sub\\tmp_x.json",
            ".tmp_dir/probe.txt",
            "notes.tmp.bak.json",
            "_probe.gd",
            "..",
            ".",
            "",
        ] {
            assert!(
                !is_root_temporary(name),
                "`{name}` must never be treated as round litter"
            );
        }
    }

    /// DR-79 ①: the cleanup removes exactly the observed root temporaries, leaves
    /// everything else byte-for-byte on disk, and reports what it removed so the
    /// record can name it.
    #[test]
    fn the_cleanup_removes_only_the_root_temporaries_the_watch_observed() {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path();
        write(&root.join(".tmp_coin.json"), "{}\n");
        write(&root.join(".tmp_goal.json"), "{}\n");
        write(&root.join("keep.txt"), "project content\n");
        write(&root.join("scenes/main.tscn"), "[gd_scene format=3]\n");
        write(&root.join("stray_dir/probe.txt"), "probe\n");
        write(&root.join("stray_dir/.tmp_nested.json"), "{}\n");

        let observed: Vec<String> = vec![
            ".tmp_coin.json",
            ".tmp_goal.json",
            "keep.txt",
            "scenes/main.tscn",
            "stray_dir/probe.txt",
            "stray_dir/.tmp_nested.json",
        ]
        .into_iter()
        .map(String::from)
        .collect();

        let removed = clean_round_temporaries(root, &observed);

        assert_eq!(
            removed,
            vec![".tmp_coin.json".to_string(), ".tmp_goal.json".to_string()],
            "only the observed root temporaries may be removed"
        );
        assert!(!root.join(".tmp_coin.json").exists());
        assert!(!root.join(".tmp_goal.json").exists());
        assert_eq!(
            std::fs::read_to_string(root.join("keep.txt")).unwrap(),
            "project content\n"
        );
        assert!(root.join("scenes/main.tscn").is_file());
        assert!(root.join("stray_dir/probe.txt").is_file());
        assert!(
            root.join("stray_dir/.tmp_nested.json").is_file(),
            "a nested path is out of scope: the cleanup is root-level by construction"
        );
    }

    /// DR-81 ④: the measured `smoke-t14` litter — the tester's scenario/args
    /// payloads written to the repository root under terse machine names
    /// (`l.json`, `p2.json`, `pv.json`, `r.json`).  DR-79's four shapes
    /// (`.tmp_*`/`tmp_*`/`*.tmp`/`*.bak`) could not see them, so the round left
    /// them behind.
    #[test]
    fn the_terse_round_scratch_names_are_round_litter() {
        for name in ["l.json", "p2.json", "pv.json", "r.json"] {
            assert!(
                is_root_temporary(name),
                "`{name}` is the measured T14 scratch shape"
            );
        }
        // The bound stays: one component, a scratch extension, and a stem short
        // enough to be machine-generated.  Everything else is out of scope.
        for name in [
            "sub/l.json",
            "sub\\l.json",
            "l.txt",
            "l.log.out",
            "abcde.json",
            "analysis.json",
            "results.json",
            "project.godot",
            "l.tmp.bak.json",
            "_probe.gd",
            "..",
            ".",
            "",
        ] {
            assert!(
                !is_root_temporary(name),
                "`{name}` must never be treated as round litter"
            );
        }
        // The boundary itself: a four-character stem is still terse scratch.
        assert!(is_root_temporary("abcd.json"));
    }

    /// DR-81 ④: the cleanup removes the round's own terse scratch and nothing
    /// else — a pre-existing file the watcher never observed, a directory with
    /// the scratch name, a nested path and an oversized payload all survive.
    #[test]
    fn the_cleanup_removes_only_the_observed_root_scratch() {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path();
        write(&root.join("l.json"), "{}\n");
        write(&root.join("p2.json"), "{}\n");
        write(&root.join("pv.json"), "{}\n");
        write(&root.join("r.json"), "{}\n");
        // Genuine content that happens to live in the root.
        write(&root.join("keep.txt"), "project content\n");
        write(&root.join("project.godot"), "[application]\n");
        // A pre-existing short-named JSON the round did **not** create: it is on
        // disk but is deliberately absent from `observed`.
        write(&root.join("old.json"), "not mine\n");
        // A directory carrying a scratch name: never removed.
        std::fs::create_dir_all(root.join("dir_scratch")).unwrap();
        write(&root.join("dir_scratch/inner.json"), "{}\n");
        // An oversized payload: bounded out of the scratch family.
        let big = "x".repeat((ROOT_SCRATCH_MAX_BYTES + 1) as usize);
        write(&root.join("big.json"), &big);

        let observed: Vec<String> = [
            "l.json",
            "p2.json",
            "pv.json",
            "r.json",
            "keep.txt",
            "project.godot",
            "dir_scratch",
            "big.json",
            "sub/l.json",
        ]
        .into_iter()
        .map(String::from)
        .collect();

        let removed = clean_round_temporaries(root, &observed);

        assert_eq!(
            removed,
            vec![
                "l.json".to_string(),
                "p2.json".to_string(),
                "pv.json".to_string(),
                "r.json".to_string(),
            ],
            "only the observed terse round scratch may be removed"
        );
        assert!(!root.join("l.json").exists());
        assert!(!root.join("r.json").exists());
        for survivor in ["keep.txt", "project.godot", "old.json", "big.json"] {
            assert!(
                root.join(survivor).is_file(),
                "`{survivor}` must survive the cleanup"
            );
        }
        assert!(root.join("dir_scratch/inner.json").is_file());
    }

    /// DR-79 ①: the watch remembers every path it ever observed, because the
    /// per-iteration return value is consumed by the iteration record and the
    /// round-close cleanup runs after the loop.
    #[test]
    fn the_watch_remembers_what_it_observed_across_the_round() {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path();
        let mut watch = OutOfTreeWatch::new(root.to_path_buf(), None);
        write(&root.join(".tmp_first.json"), "{}\n");
        assert_eq!(watch.observe(), vec![".tmp_first.json".to_string()]);
        write(&root.join(".tmp_second.json"), "{}\n");
        let _ = watch.observe();
        let observed = watch.observed();
        assert!(
            observed.contains(&".tmp_first.json".to_string())
                && observed.contains(&".tmp_second.json".to_string()),
            "both observations must survive: {observed:?}"
        );
    }

    /// DR-38: the marker set has to name the whole harness repository, not just
    /// `src/**`, `.spec/**`, `tests/**` and the external checkout.
    #[test]
    fn the_marker_set_covers_config_decisions_and_the_manifest() {
        for command in [
            "dir config\\*.yaml",
            "type config/hoh.yaml",
            "Get-Content config\\hoh.yaml",
            "cat DECISIONS.md",
            "type Cargo.toml",
        ] {
            assert!(mentions_forbidden_source(command), "`{command}`");
        }
        assert!(!mentions_forbidden_source(
            "godot --headless --check-only res://x.gd"
        ));
    }

    /// DR-38: `dir /b /s *.yaml | findstr hoh` names no path, yet it is a
    /// whole-tree search aimed at the harness by name.
    #[test]
    fn a_recursive_search_for_the_harness_is_a_harness_read() {
        assert!(enumerates_harness_tree("dir /b /s *.yaml | findstr hoh"));
        assert!(enumerates_harness_tree("grep -r hoh harness/"));
        // In-project work is not a harness read.
        assert!(!enumerates_harness_tree("dir scenes\\*.tscn"));
        assert!(
            !enumerates_harness_tree("ls .hoh/deterministic/*.json"),
            "the runtime's own artifact directory is ordinary project work"
        );
        assert!(!enumerates_harness_tree(
            "godot --headless --check-only res://x.gd"
        ));
    }

    /// DR-38: the repository root is injected at runtime, never hard-coded, and
    /// either separator style must match.
    #[test]
    fn the_injected_harness_root_is_matched_in_both_separator_styles() {
        let root = std::path::Path::new("F:/harness/repo");
        assert!(mentions_harness_root("dir F:/harness/repo", root));
        assert!(mentions_harness_root(
            "powershell -Command \"Set-Location 'F:\\\\harness\\\\repo'; dir F:\\harness\\repo\"",
            root
        ));
        assert!(!mentions_harness_root("dir F:/other/repo", root));

        let trajectory = serde_json::json!({
            "messages": [{"role": "assistant", "extra": {"actions": [
                {"command": "dir F:/harness/repo"}
            ]}}]
        })
        .to_string();
        assert!(mentions_forbidden_source_in_actions_with_root(
            &trajectory,
            Some(root)
        ));
        assert!(
            !mentions_forbidden_source_in_actions(&trajectory),
            "without the injected root the command names no marker"
        );
    }

    // -----------------------------------------------------------------------
    // DR-59 / DR-61
    // -----------------------------------------------------------------------

    /// Every file under `root`, as `relative path -> bytes`.
    fn walk(root: &Path) -> BTreeMap<String, Vec<u8>> {
        let mut files = BTreeMap::new();
        for entry in walkdir::WalkDir::new(root).follow_links(false) {
            let Ok(entry) = entry else { continue };
            if !entry.file_type().is_file() {
                continue;
            }
            let relative = relativize(root, entry.path());
            files.insert(relative, std::fs::read(entry.path()).unwrap_or_default());
        }
        files
    }

    /// The seeds of one finished round: the measured at-risk families **and** the
    /// `.hoh` siblings the round rewrites, so "the whole tree moved" is checked
    /// against a workspace that looks like a real one.
    fn seed_previous_round(workspace: &Path) {
        write(
            &workspace.join(".hoh/deterministic/battery.json"),
            "round one\n",
        );
        write(&workspace.join(".hoh/deterministic/raw/probe.json"), "{}\n");
        write(&workspace.join(".hoh/evidence/frame-00.png"), "png\n");
        write(&workspace.join(".hoh/evidence.json"), "{}\n");
        write(&workspace.join(".hoh/args/probe.json"), "{}\n");
        write(&workspace.join(".hoh/scratch/probe.txt"), "probe\n");
        // Measured: the round never rewrites this one (it is injected into the
        // views only, `run_loop.rs:498`), so a curated list would leave it behind.
        write(&workspace.join(".hoh/SCAFFOLD.md"), "scaffold\n");
        write(&workspace.join(".hoh/skills/godot-dev.md"), "skill\n");
    }

    /// DR-61: the previous round's whole `.hoh` tree is **moved out of the
    /// workspace** byte-for-byte, including the families a curated list would
    /// keep moving and the siblings it would miss, and a walk of `.hoh` can no
    /// longer reach one byte of it.
    #[test]
    fn quarantine_moves_the_whole_artifact_tree_out_of_the_workspace() {
        let temp = tempfile::tempdir().unwrap();
        let workspace = temp.path().join("workspace");
        let run_dir = temp.path().join("runs/run-1");
        seed_previous_round(&workspace);

        let moved = quarantine_previous_evidence(&workspace, &run_dir).unwrap();

        let lives: Vec<&str> = moved.iter().map(|area| area.live).collect();
        assert_eq!(lives, QUARANTINE_AREAS, "the artifact tree must be moved");
        assert_eq!(lives, vec![ARTIFACT_DIR]);
        assert!(
            !workspace.join(ARTIFACT_DIR).exists(),
            "the live artifact tree must be gone after the quarantine"
        );
        for area in &moved {
            assert!(
                area.target.starts_with(run_dir.join(QUARANTINE_DIR)),
                "{} must be moved into the run's quarantine: {:?}",
                area.live,
                area.target
            );
            assert!(
                !area.target.starts_with(&workspace),
                "{} must not be moved back inside the workspace: {:?}",
                area.live,
                area.target
            );
        }

        // The bytes survive, and a wildcard walk of `.hoh` cannot reach them.
        // (The moved entry carries the `.stale-<ts>` suffix, so lookups match on
        // a substring rather than on an exact key.)
        let kept = walk(&run_dir.join(QUARANTINE_DIR));
        let preserved = |needle: &str| {
            kept.iter()
                .find(|(path, _)| path.contains(needle))
                .map(|(_, bytes)| bytes.as_slice())
        };
        assert_eq!(
            preserved("battery.json"),
            Some(b"round one\n".as_slice()),
            "the previous round's bytes must survive the move: {:?}",
            kept.keys().collect::<Vec<_>>()
        );
        assert_eq!(preserved("raw/probe.json"), Some(b"{}\n".as_slice()));
        assert_eq!(
            preserved("frame-00.png"),
            Some(b"png\n".as_slice()),
            "the evidence dir must be moved: {:?}",
            kept.keys().collect::<Vec<_>>()
        );
        assert_eq!(
            preserved("evidence.json"),
            Some(b"{}\n".as_slice()),
            "the evidence bundle must be moved: {:?}",
            kept.keys().collect::<Vec<_>>()
        );
        assert_eq!(
            preserved("args/probe.json"),
            Some(b"{}\n".as_slice()),
            "the args family must be moved: {:?}",
            kept.keys().collect::<Vec<_>>()
        );
        assert_eq!(preserved("scratch/probe.txt"), Some(b"probe\n".as_slice()));
        // The sibling a curated list would have left behind is in the quarantine
        // too: the round never rewrites it.
        assert_eq!(preserved("SCAFFOLD.md"), Some(b"scaffold\n".as_slice()));
        assert_eq!(
            preserved("skills/godot-dev.md"),
            Some(b"skill\n".as_slice())
        );

        // Nothing is left in the cwd to walk: the workspace held only `.hoh`.
        let reached = walk(&workspace);
        assert!(
            reached.is_empty(),
            "a walk of the workspace still reaches previous-round bytes: {:?}",
            reached.keys().collect::<Vec<_>>()
        );
        assert!(
            !reached.keys().any(|path| path.contains(".stale-")),
            "a walk of the workspace still reaches a `.stale-*` entry: {:?}",
            reached.keys().collect::<Vec<_>>()
        );
    }

    /// DR-59/DR-61: the counter-direction — a clean start quarantines nothing,
    /// creates nothing, and does not even create the run's quarantine directory.
    #[test]
    fn quarantine_is_a_no_op_on_a_clean_start() {
        let temp = tempfile::tempdir().unwrap();
        let workspace = temp.path().join("workspace");
        let run_dir = temp.path().join("runs/run-1");
        std::fs::create_dir_all(&workspace).unwrap();
        std::fs::create_dir_all(&run_dir).unwrap();

        assert!(quarantine_previous_evidence(&workspace, &run_dir)
            .unwrap()
            .is_empty());
        let entries: Vec<String> = std::fs::read_dir(&workspace)
            .unwrap()
            .map(|entry| entry.unwrap().file_name().to_string_lossy().into_owned())
            .collect();
        assert!(
            entries.is_empty(),
            "a clean round start must not create anything: {entries:?}"
        );
        assert!(
            !run_dir.join(QUARANTINE_DIR).exists(),
            "a clean round start must not create an empty quarantine directory"
        );
    }

    /// DR-59/DR-61: two quarantines inside the same second must not overwrite
    /// each other — the `.stale-<ts>-<attempt>` window is what makes the move safe.
    #[test]
    fn a_second_quarantine_in_the_same_second_does_not_collide() {
        let temp = tempfile::tempdir().unwrap();
        let workspace = temp.path().join("workspace");
        let run_dir = temp.path().join("runs/run-1");

        write(
            &workspace.join(".hoh/deterministic/battery.json"),
            "round one\n",
        );
        let first = quarantine_previous_evidence(&workspace, &run_dir).unwrap();
        write(
            &workspace.join(".hoh/deterministic/battery.json"),
            "round two\n",
        );
        let second = quarantine_previous_evidence(&workspace, &run_dir).unwrap();

        assert_eq!(first[0].live, ARTIFACT_DIR);
        assert_ne!(first[0].target, second[0].target);
        assert_eq!(
            std::fs::read_to_string(first[0].target.join("deterministic/battery.json")).unwrap(),
            "round one\n"
        );
        assert_eq!(
            std::fs::read_to_string(second[0].target.join("deterministic/battery.json")).unwrap(),
            "round two\n"
        );
    }

    /// DR-61: when the destination would be inside the workspace — the defect
    /// this decision removes — the round must stop loudly, not isolate in name
    /// only.  Nothing may have been moved by the failed call.
    #[test]
    fn quarantine_refuses_a_destination_inside_the_workspace() {
        let temp = tempfile::tempdir().unwrap();
        let workspace = temp.path().join("workspace");
        write(
            &workspace.join(".hoh/deterministic/battery.json"),
            "round one\n",
        );
        let run_dir = workspace.join("nested-run");

        let error = quarantine_previous_evidence(&workspace, &run_dir)
            .expect_err("a destination inside the workspace must be refused");

        let message = error.to_string();
        assert!(message.contains("DR-61"), "{message}");
        assert!(message.contains("inside the workspace"), "{message}");
        assert!(
            workspace.join(".hoh/deterministic/battery.json").is_file(),
            "a refused quarantine must not have moved anything"
        );
    }

    /// DR-62: the supersession decision is the **explicit record**, never the
    /// name.  Same test as DR-61's `is_expired_name` check, re-pointed at the
    /// structural criterion and strictly extended: the name alone decides
    /// nothing any more.
    #[test]
    fn the_superseded_marker_is_recognized_by_one_predicate() {
        let temp = tempfile::tempdir().unwrap();
        let directory = temp.path();
        assert!(SupersededSet::load(directory).unwrap().is_empty());

        let recorded = stale_name("frame-00.png", 1790663544, 0);
        assert_eq!(recorded, "frame-00.png.stale-1790663544");
        SupersededSet::record(directory, &recorded).unwrap();

        let set = SupersededSet::load(directory).unwrap();
        assert_eq!(set.len(), 1);
        assert!(set.contains(&recorded), "the recorded path is superseded");
        assert!(is_superseded(directory, &recorded).unwrap());
        assert!(
            !is_superseded(directory, "frame-00.png").unwrap(),
            "the live path itself is not superseded"
        );
        assert!(
            !is_superseded(directory, "another-file.stale-1790663544").unwrap(),
            "DR-62: a `.stale-`-shaped name the manifest never recorded is not \
             superseded — the name alone means nothing"
        );
    }

    /// DR-62: the manifest is per-directory, so a path is superseded when the
    /// manifest of the copy root, or of any directory on the way to it, records
    /// the remainder of that path.
    #[test]
    fn a_supersession_recorded_in_a_subdirectory_manifest_is_found_from_the_root() {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path();
        write(&root.join("replay/round.json"), "superseded\n");
        SupersededSet::record(&root.join("replay"), "round.json").unwrap();

        assert!(is_superseded(root, "replay/round.json").unwrap());
        assert!(!is_superseded(root, "replay/other.json").unwrap());
        assert!(
            std::fs::read_to_string(root.join("replay").join(SUPERSEDED_MANIFEST))
                .unwrap()
                .contains("round.json")
        );
    }

    /// DR-62: the manifest is runtime bookkeeping, never view content — and a
    /// malformed record is an error, so a corrupt manifest cannot silently
    /// re-admit superseded bytes.
    #[test]
    fn the_manifest_is_bookkeeping_and_a_malformed_one_is_an_error() {
        assert!(is_runtime_bookkeeping(SUPERSEDED_MANIFEST));
        assert!(is_runtime_bookkeeping(&format!(
            "evidence/{SUPERSEDED_MANIFEST}"
        )));
        assert!(!is_runtime_bookkeeping("evidence/frame-00.png"));

        let temp = tempfile::tempdir().unwrap();
        write(&temp.path().join(SUPERSEDED_MANIFEST), "{not json}\n");
        let error = SupersededSet::load(temp.path()).unwrap_err();
        assert_eq!(error.kind(), std::io::ErrorKind::InvalidData);
        assert!(is_superseded(temp.path(), "anything").is_err());
    }

    /// DR-49: freshness is a property of the artifact **state**, and a
    /// pre-existing file is invalidated rather than trusted.
    #[test]
    fn freshness_is_decided_on_the_artifact_state_not_on_existence() {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("frame-00.png");

        // Nothing before, nothing after: never fresh.
        assert!(!artifact_is_fresh(None, None));
        // Created by the call.
        write(&path, "one");
        let first = artifact_fingerprint(&path).expect("fingerprint");
        assert!(artifact_is_fresh(None, Some(&first)));
        // Unchanged across the call: not this run's artifact.
        assert!(!artifact_is_fresh(Some(&first), Some(&first)));
        // Rewritten with different bytes: fresh.
        write(&path, "two");
        let second = artifact_fingerprint(&path).expect("fingerprint");
        assert!(artifact_is_fresh(Some(&first), Some(&second)));
        // Deleted: never fresh, and no path may be claimed.
        std::fs::remove_file(&path).unwrap();
        assert!(!artifact_is_fresh(Some(&first), None));
        assert!(artifact_fingerprint(&path).is_none());
    }

    /// DR-49 ②: the pre-existing artifact is renamed out of the way, not left in
    /// place, and the operation is idempotent/`None` when there is nothing.
    #[test]
    fn invalidating_an_artifact_moves_it_aside() {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("frame-00.png");
        assert_eq!(invalidate_artifact(&path).unwrap(), None);

        write(&path, "2026-09-21 stale png");
        let stale = invalidate_artifact(&path)
            .unwrap()
            .expect("a pre-existing file must be moved aside");
        assert!(stale.starts_with("frame-00.png.stale-"), "{stale}");
        assert!(
            !path.exists(),
            "the target must be empty for the duration of the call"
        );
        let moved = temp.path().join(&stale);
        assert_eq!(
            std::fs::read(&moved).unwrap(),
            b"2026-09-21 stale png",
            "the stale artifact stays auditable under its new name"
        );
        // DR-62: the move is mirrored by an explicit structural record in the
        // same directory — the criterion the view copies consult, and the only
        // one: the `.stale-<ts>` name itself now decides nothing.
        let recorded = SupersededSet::load(temp.path()).unwrap();
        assert!(
            recorded.contains(&stale),
            "DR-62: the supersession must be recorded in the manifest: {recorded:?}"
        );
        assert!(
            is_superseded(temp.path(), &stale).unwrap(),
            "DR-62: the recorded supersession must be discoverable from the tree root"
        );
        // A second invalidation has nothing left to do.
        assert_eq!(invalidate_artifact(&path).unwrap(), None);
    }
}
