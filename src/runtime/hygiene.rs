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
}

impl OutOfTreeWatch {
    pub fn new(root: PathBuf, project: Option<PathBuf>) -> Self {
        let last = scan(&root, project.as_deref());
        Self {
            root,
            project,
            last,
        }
    }

    /// Diff the tree against the previous observation and advance the baseline.
    pub fn observe(&mut self) -> Vec<String> {
        let now = scan(&self.root, self.project.as_deref());
        let changed = changed_paths(&self.last, &now);
        self.last = now;
        changed
    }
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
// DR-59: the previous round's deterministic evidence must not be readable here
// ---------------------------------------------------------------------------

/// DR-59: the workspace-relative deterministic evidence area (DR-17).
pub const DETERMINISTIC_EVIDENCE_DIR: &str = ".hoh/deterministic";

/// DR-49/DR-59: how many `.stale-` names are tried before the rename gives up.
const STALE_NAME_ATTEMPTS: u32 = 64;

/// DR-49/DR-59: the name a superseded path is moved to.
///
/// One convention, two call sites: `invalidate_artifact` (DR-49, the
/// pre-existing screenshot file) and [`quarantine_previous_evidence`] (DR-59,
/// the whole evidence directory).  Keeping the suffix in one place is what
/// keeps "superseded" greppable and auditable across the repository.
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
/// unconditionally: a clean round start must not litter the workspace with an
/// empty `*.stale-*` sibling.
fn should_quarantine(live: &Path) -> bool {
    live.exists()
}

/// DR-59: move the previous round's deterministic evidence out of the live read
/// path before any role of the new round runs.
///
/// `smoke-t7` proved the leak is real, not theoretical: that round started with
/// `smoke-t6`'s `.hoh/deterministic/**` still on disk, the Developer read it, and
/// `runs/smoke-t7/iter-1/traj/developer.attempt1.json` `.messages[54]` carries
/// the *previous* round's `pid 108432`, its "the editor is not clean" verdict and
/// its `os error 10061` transport failure into the new round's model context.
///
/// The evidence is **renamed, never deleted**: the previous round's readings stay
/// on disk — and out of the artifact hash, because `.hoh` is excluded (DR-11) —
/// under the repository's DR-49 `.stale-<ts>` convention, which is already the
/// marker this code base uses for "superseded, do not trust".  Returns the
/// workspace-relative quarantine name when something was moved, and `None` when
/// the round started clean.
pub fn quarantine_previous_evidence(workspace: &Path) -> anyhow::Result<Option<String>> {
    let live = workspace.join(DETERMINISTIC_EVIDENCE_DIR);
    if !should_quarantine(&live) {
        return Ok(None);
    }
    let base = live
        .file_name()
        .map(|name| name.to_string_lossy().into_owned())
        .unwrap_or_else(|| "deterministic".to_string());
    let stamp = crate::adapter::engine::now_seconds();
    for attempt in 0..STALE_NAME_ATTEMPTS {
        let target = live.with_file_name(stale_name(&base, stamp, attempt));
        if !target.exists() {
            std::fs::rename(&live, &target)?;
            return Ok(Some(relativize(workspace, &target)));
        }
    }
    // DR-49's single-file case may fall back to deleting once its name window is
    // exhausted.  A whole round of evidence must not be deleted, and must not be
    // left in the live path either — both outcomes would break this decision —
    // so the round stops loudly instead.
    anyhow::bail!(
        "DR-59: could not move {DETERMINISTIC_EVIDENCE_DIR} aside: all \
         {STALE_NAME_ATTEMPTS} `.stale-{stamp}` names are taken"
    )
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

    #[test]
    fn suspicious_files_ignores_the_runtime_directories() {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path();
        write(&root.join(".hoh/scratch/_probe.gd"), "x\n");
        write(&root.join(".godot/_tmp_cache"), "x\n");
        write(&root.join("scenes/main.tscn"), "x\n");
        assert!(suspicious_files(root).is_empty());
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
    // DR-59
    // -----------------------------------------------------------------------

    /// DR-59: the previous round's evidence is **moved**, byte-for-byte, and the
    /// live read path is left empty.
    #[test]
    fn quarantine_moves_the_evidence_aside_and_keeps_the_bytes() {
        let temp = tempfile::tempdir().unwrap();
        let workspace = temp.path().join("workspace");
        write(
            &workspace.join(".hoh/deterministic/battery.json"),
            "the editor is not clean\n",
        );
        write(&workspace.join(".hoh/deterministic/raw/probe.json"), "{}\n");

        let moved = quarantine_previous_evidence(&workspace)
            .unwrap()
            .expect("a round over old evidence must move it aside");

        assert!(moved.starts_with(".hoh/deterministic.stale-"), "{moved}");
        assert!(
            !workspace.join(DETERMINISTIC_EVIDENCE_DIR).exists(),
            "the live evidence path must be empty after the quarantine"
        );
        assert_eq!(
            std::fs::read_to_string(workspace.join(&moved).join("battery.json")).unwrap(),
            "the editor is not clean\n",
            "the previous round's bytes must survive the move"
        );
        assert!(workspace.join(&moved).join("raw/probe.json").is_file());
    }

    /// DR-59: the counter-direction — a clean start quarantines nothing and
    /// creates nothing.
    #[test]
    fn quarantine_is_a_no_op_on_a_clean_start() {
        let temp = tempfile::tempdir().unwrap();
        let workspace = temp.path().join("workspace");
        std::fs::create_dir_all(&workspace).unwrap();

        assert!(quarantine_previous_evidence(&workspace).unwrap().is_none());
        let entries: Vec<String> = std::fs::read_dir(&workspace)
            .unwrap()
            .map(|entry| entry.unwrap().file_name().to_string_lossy().into_owned())
            .collect();
        assert!(
            entries.is_empty(),
            "a clean round start must not create anything: {entries:?}"
        );
    }

    /// DR-59: two quarantines inside the same second must not overwrite each
    /// other — the `.stale-<ts>-<attempt>` window is what makes the move safe.
    #[test]
    fn a_second_quarantine_in_the_same_second_does_not_collide() {
        let temp = tempfile::tempdir().unwrap();
        let workspace = temp.path().join("workspace");

        write(&workspace.join(".hoh/deterministic/battery.json"), "round one\n");
        let first = quarantine_previous_evidence(&workspace).unwrap().unwrap();
        write(&workspace.join(".hoh/deterministic/battery.json"), "round two\n");
        let second = quarantine_previous_evidence(&workspace).unwrap().unwrap();

        assert_ne!(first, second);
        assert_eq!(
            std::fs::read_to_string(workspace.join(&first).join("battery.json")).unwrap(),
            "round one\n"
        );
        assert_eq!(
            std::fs::read_to_string(workspace.join(&second).join("battery.json")).unwrap(),
            "round two\n"
        );
    }
}
