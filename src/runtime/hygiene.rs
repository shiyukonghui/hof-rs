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

/// DR-26/DR-32: does this **tool command or argument** mention the harness
/// sources or an external repository checkout?  Report-only: behaviour never
/// changes.
///
/// DR-32: the marker set is only ever applied to tool text.  The whole-repo
/// variants are deliberately broad (`src/`, `.spec/`) because the prompts
/// themselves name those paths, so anything narrower would miss a real read —
/// see [`mentions_forbidden_source_in_actions`].
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
    ];
    MARKERS.iter().any(|marker| text.contains(marker))
}

/// DR-32: scan **only** the tool calls of a trajectory (`messages[*].extra.
/// actions[*]`, plus the arguments nested inside them).
///
/// `smoke-t3` produced an unconditional `harness_source_read` warning: the
/// detector ran over the raw trajectory text, where the system prompt's own
/// "never read `src/**`" sentence matched.  The prompt can never be evidence of
/// what the role *did*.
pub fn mentions_forbidden_source_in_actions(trajectory: &str) -> bool {
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
                        if mentions_forbidden_source(text) {
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
                {"command": "hoh tools call read_script",
                 "args": {"path": "F:\\RustProjects\\godot-mcp-pro\\x.gd"}}
            ]}}]
        })
        .to_string();
        assert!(mentions_forbidden_source_in_actions(&args_only));

        // A trajectory that is not JSON yields no evidence (never a guess).
        assert!(!mentions_forbidden_source_in_actions("not json"));
    }

    #[test]
    fn suspicious_files_ignores_the_runtime_directories() {        let temp = tempfile::tempdir().unwrap();
        let root = temp.path();
        write(&root.join(".hoh/scratch/_probe.gd"), "x\n");
        write(&root.join(".godot/_tmp_cache"), "x\n");
        write(&root.join("scenes/main.tscn"), "x\n");
        assert!(suspicious_files(root).is_empty());
    }
}
