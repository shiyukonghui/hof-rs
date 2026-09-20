//! Permission enforcement: content-addressed tree hashing plus the role tool
//! allow/deny matrix.
//!
//! "Prevention" (view isolation) and "detection" (hash assertions) are both
//! mandatory: a copy can never stop an agent from writing to the real project
//! through an absolute path, so the before/after hash assertions are the
//! enforcement point (`DESIGN-DETAIL.md` §4.4).

use std::path::Path;

use sha2::{Digest, Sha256};
use walkdir::WalkDir;

use crate::model::{ContractViolation, Role};

/// Lowercase hex sha256 of arbitrary bytes.
pub fn sha256_hex(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("{:x}", hasher.finalize())
}

/// Exclude list wrapper so callers cannot accidentally pass a different set to
/// hashing and to copying.
#[derive(Clone, Debug, Default)]
pub struct HashExcludes(pub Vec<String>);

impl HashExcludes {
    pub fn new(items: impl IntoIterator<Item = impl Into<String>>) -> Self {
        Self(items.into_iter().map(Into::into).collect())
    }

    pub fn as_slice(&self) -> &[String] {
        &self.0
    }

    /// Merge the always-excluded runtime paths with adapter cache excludes.
    pub fn merged(&self) -> Vec<String> {
        let mut items = vec![".hoh".to_string(), ".git".to_string()];
        for item in &self.0 {
            let normalized = item.replace('\\', "/");
            if !normalized.is_empty() && !items.contains(&normalized) {
                items.push(normalized);
            }
        }
        items
    }
}

/// Does `rel` (POSIX-style, relative to the tree root) fall under an exclude?
pub fn is_excluded(rel: &str, excludes: &[String]) -> bool {
    excludes
        .iter()
        .any(|exclude| rel == exclude || rel.starts_with(&format!("{exclude}/")))
}

fn relativize(root: &Path, path: &Path) -> String {
    let rel = path.strip_prefix(root).unwrap_or(path);
    rel.components()
        .map(|component| component.as_os_str().to_string_lossy().into_owned())
        .collect::<Vec<_>>()
        .join("/")
}

/// The single hashing implementation used by both permission checks and the
/// version store.  Identity = sha256 over the sorted
/// `relpath\n{len}\n{bytes}\n` stream of every non-excluded file.
pub fn hash_tree(root: &Path, excludes: &[String]) -> anyhow::Result<String> {
    let mut files: Vec<(String, std::path::PathBuf)> = Vec::new();
    if root.exists() {
        for entry in WalkDir::new(root).follow_links(false) {
            let entry = entry?;
            if !entry.file_type().is_file() {
                continue;
            }
            let rel = relativize(root, entry.path());
            if is_excluded(&rel, excludes) {
                continue;
            }
            files.push((rel, entry.path().to_path_buf()));
        }
    }
    files.sort_by(|a, b| a.0.cmp(&b.0));

    let mut hasher = Sha256::new();
    for (rel, path) in files {
        let bytes = std::fs::read(&path)
            .map_err(|error| anyhow::anyhow!("could not read {}: {error}", path.display()))?;
        hasher.update(rel.as_bytes());
        hasher.update(b"\n");
        hasher.update(bytes.len().to_string().as_bytes());
        hasher.update(b"\n");
        hasher.update(&bytes);
        hasher.update(b"\n");
    }
    Ok(format!("{:x}", hasher.finalize()))
}

/// Detection half of the permission model: a tree that must not change did.
///
/// The label decides which contract violation is reported, because the runtime
/// contract differs per stage (`DESIGN-DETAIL.md` §4.4).
pub fn assert_unchanged(label: &str, before: &str, after: &str) -> Result<(), ContractViolation> {
    if before == after {
        return Ok(());
    }
    let violation = if label.contains("tester/candidate") {
        ContractViolation::QaContaminatedCandidate
    } else {
        ContractViolation::ReadOnlyRoleWroteArtifact
    };
    Err(violation)
}

/// Canonical tool policy table (§5.4).  `crate::tools::policy` re-exports
/// these so both the tool channel and the runtime agree by construction.
pub mod tool_matrix {
    use crate::model::Role;

    /// Planner gets no MCP tool at all (`*` documents "everything").
    pub const PLANNER_DENY_PREFIXES: &[&str] = &["*"];

    /// Tester: read-only / execution / evidence collection prefixes.
    const TESTER_ALLOW_PREFIXES: &[&str] = &[
        "get_",
        "list_",
        "read_",
        "search_",
        "find_",
        "analyze_",
        "detect_",
        "simulate_",
        "assert_",
    ];

    /// Tester: read-only / execution / evidence collection exact names.
    const TESTER_ALLOW_EXACT: &[&str] = &[
        "play_scene",
        "stop_scene",
        "capture_frames",
        "monitor_properties",
        "start_recording",
        "stop_recording",
        "replay_recording",
        "compare_screenshots",
        "run_test_scenario",
        "run_stress_test",
        "get_test_report",
        "wait_for_node",
        "click_button_by_text",
        "navigate_to",
        "move_to",
        "cross_scene_set_property",
    ];

    /// Tester: mutating prefixes — hit means deny, no exceptions.
    const MUTATING_PREFIXES: &[&str] = &[
        "add_", "create_", "delete_", "remove_", "set_", "update_", "edit_",
    ];

    /// Tester: mutating exact names — hit means deny, no exceptions.
    const MUTATING_EXACT: &[&str] = &[
        "move_node",
        "rename_node",
        "duplicate_node",
        "attach_script",
        "connect_signal",
        "disconnect_signal",
        "tilemap_set_cell",
        "tilemap_fill_rect",
        "tilemap_clear",
        "batch_set_property",
        "cross_scene_set_property",
        "export_project",
        "execute_editor_script",
        "execute_game_script",
        "reload_plugin",
        "reload_project",
        "set_game_node_property",
        "set_project_setting",
        "set_input_action",
        "bake_navigation_mesh",
        "clear_output",
        "clear_editor_selection",
    ];

    pub fn is_mutating(tool: &str) -> bool {
        MUTATING_EXACT.contains(&tool) || MUTATING_PREFIXES.iter().any(|p| tool.starts_with(p))
    }

    pub fn is_tester_allowed(tool: &str) -> bool {
        TESTER_ALLOW_EXACT.contains(&tool)
            || TESTER_ALLOW_PREFIXES.iter().any(|p| tool.starts_with(p))
    }

    /// Default-deny matrix.  Unknown tool names are denied for Planner and
    /// Tester; only the Developer may use the full tool set.
    pub fn tool_allowed(role: Role, tool: &str) -> bool {
        match role {
            Role::Developer => true,
            Role::Planner => false,
            Role::Tester => {
                if is_mutating(tool) {
                    return false;
                }
                is_tester_allowed(tool)
            }
        }
    }

    /// Structured reason used by `hoh tools call` and by the tool channel.
    pub fn denial_reason(role: Role, tool: &str) -> &'static str {
        if tool_matrix_is_unknown(role, tool) {
            "This tool is not on the role's allowed list (default deny)."
        } else {
            "This role may not mutate the artifact."
        }
    }

    fn tool_matrix_is_unknown(role: Role, tool: &str) -> bool {
        role == Role::Tester && !is_tester_allowed(tool) && !is_mutating(tool)
    }
}

pub use tool_matrix::PLANNER_DENY_PREFIXES;

/// Default-deny role/tool matrix (§5.4).
pub fn tool_allowed(role: Role, tool: &str) -> bool {
    tool_matrix::tool_allowed(role, tool)
}

/// Human-readable denial reason for the CLI bridge.
pub fn denial_reason(role: Role, tool: &str) -> &'static str {
    tool_matrix::denial_reason(role, tool)
}

/// Convenience: is this role allowed to submit an artifact at all?
pub fn role_may_submit(role: Role) -> bool {
    matches!(role, Role::Planner | Role::Tester)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn merged_excludes_always_contain_the_runtime_paths() {
        let excludes = HashExcludes::new([".godot", ".hoh"]).merged();
        assert!(excludes.contains(&".hoh".to_string()));
        assert!(excludes.contains(&".git".to_string()));
        assert!(excludes.contains(&".godot".to_string()));
        // No duplicates even when the adapter repeats a runtime path.
        assert_eq!(excludes.iter().filter(|item| *item == ".hoh").count(), 1);
    }

    #[test]
    fn exclusion_is_prefix_based() {
        let excludes = vec![".hoh".to_string(), "cache".to_string()];
        assert!(is_excluded(".hoh/plan.md", &excludes));
        assert!(is_excluded("cache/deep/file.bin", &excludes));
        assert!(!is_excluded("scripts/player.gd", &excludes));
        assert!(!is_excluded("cacheable.txt", &excludes));
    }

    #[test]
    fn empty_tree_hashes_deterministically() {
        let temp = tempfile::tempdir().unwrap();
        let empty = temp.path().join("missing");
        assert_eq!(
            hash_tree(&empty, &[]).unwrap(),
            hash_tree(&empty, &[]).unwrap()
        );
    }

    #[test]
    fn label_selects_the_contract_violation() {
        assert!(assert_unchanged("planner", "a", "a").is_ok());
        assert_eq!(
            assert_unchanged("planner", "a", "b"),
            Err(ContractViolation::ReadOnlyRoleWroteArtifact)
        );
        assert_eq!(
            assert_unchanged("tester/candidate", "a", "b"),
            Err(ContractViolation::QaContaminatedCandidate)
        );
        assert_eq!(
            assert_unchanged("tester/workspace", "a", "b"),
            Err(ContractViolation::ReadOnlyRoleWroteArtifact)
        );
    }
}
