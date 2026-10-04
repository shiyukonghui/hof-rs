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

/// The adapter's configured **cache** excludes, normalized and de-duplicated.
///
/// These are the directories `hash_tree` deliberately does not see: R10 keeps
/// `version_id` stable, so they must not enter the artifact identity.  They are
/// exposed separately so the runtime can *observe* them without hashing them —
/// a write into a frozen view through one of these prefixes is invisible to that
/// identity, but it is still a role write, and no reading may report it as "no
/// role wrote".
///
/// The runtime's own always-excluded paths are filtered out: `.hoh/**` is the
/// Tester's legitimate submission area, not a cache.
pub fn cache_prefixes(excludes: &[String]) -> Vec<String> {
    let mut items: Vec<String> = Vec::new();
    for item in excludes {
        let normalized = item.replace('\\', "/");
        let normalized = normalized.trim_end_matches('/');
        if normalized.is_empty() || normalized == ".hoh" || normalized == ".git" {
            continue;
        }
        if !items.iter().any(|existing| existing == normalized) {
            items.push(normalized.to_string());
        }
    }
    items
}

/// Per-file digest of the adapter's configured cache directories, keyed by the
/// path exactly as `hash_tree` would name it (`<prefix>/<relative>`).
///
/// This is a read-only projection for the excluded-path watch.  It is **not** a
/// second artifact identity and never feeds `hash_tree`, so `version_id` stays
/// stable (R10) and the frozen snapshot keeps its meaning.
pub fn cache_manifest(
    root: &Path,
    prefixes: &[String],
) -> anyhow::Result<std::collections::BTreeMap<String, String>> {
    let mut manifest = std::collections::BTreeMap::new();
    for prefix in prefixes {
        let directory = root.join(prefix);
        if !directory.exists() {
            continue;
        }
        for (relative, digest) in tree_manifest(&directory, &[])? {
            manifest.insert(format!("{prefix}/{relative}"), digest);
        }
    }
    Ok(manifest)
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

/// Per-file content digest of a tree, keyed by POSIX relative path.
///
/// `hash_tree` answers "did anything change?"; this answers "what changed?".
/// `hash_tree` is deliberately left untouched so `version_id` stays stable
/// (R10) — this is an additional read-only projection, not a second hashing
/// implementation.
pub fn tree_manifest(
    root: &Path,
    excludes: &[String],
) -> anyhow::Result<std::collections::BTreeMap<String, String>> {
    let mut manifest = std::collections::BTreeMap::new();
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
            let bytes = std::fs::read(entry.path()).map_err(|error| {
                anyhow::anyhow!("could not read {}: {error}", entry.path().display())
            })?;
            manifest.insert(rel, sha256_hex(&bytes));
        }
    }
    Ok(manifest)
}

/// The maximum number of paths reported per category (DR-2).
pub const EVIDENCE_DIFF_LIMIT: usize = 50;

/// DR-2: turn two manifests into a concrete, sorted difference report.
pub fn diff_manifests(
    before: &std::collections::BTreeMap<String, String>,
    after: &std::collections::BTreeMap<String, String>,
) -> crate::model::EvidenceDiff {
    let mut diff = crate::model::EvidenceDiff::default();
    for (path, digest) in after {
        match before.get(path) {
            None => diff.added.push(path.clone()),
            Some(previous) if previous != digest => diff.modified.push(path.clone()),
            Some(_) => {}
        }
    }
    for path in before.keys() {
        if !after.contains_key(path) {
            diff.removed.push(path.clone());
        }
    }
    diff.added.sort();
    diff.modified.sort();
    diff.removed.sort();
    diff.added.truncate(EVIDENCE_DIFF_LIMIT);
    diff.modified.truncate(EVIDENCE_DIFF_LIMIT);
    diff.removed.truncate(EVIDENCE_DIFF_LIMIT);
    diff
}

/// Canonical tool policy table (§5.4, rewritten for the four-channel contract
/// by DR-42).  `crate::tools::policy` re-exports these so both the tool channel
/// and the runtime agree by construction.
///
/// The old table was keyed on the *first noun* of an unprefixed name
/// (`get_*`, `add_*`, and a handful of bare scene verbs).  In the new contract the first
/// component is the **channel** (`editor_`, `project_`, `running_game_`, `os_`),
/// so the rule is keyed on the second component, the **verb**, plus an explicit
/// exception list for the evidence-driving tools whose verb happens to be a
/// writing one.
pub mod tool_matrix {
    use crate::model::Role;

    /// Planner gets no MCP tool at all (`*` documents "everything").
    ///
    /// DR-42 describes the Planner's scope as "read-only channels only".  The
    /// allowlist stays **empty**, which satisfies that in the strongest form —
    /// no mutating verb can ever reach the Planner — and keeps the pre-existing
    /// DR-7 contract (`§5.4`: the Planner owns no MCP tool) and its tests
    /// intact.  Making the Planner *able* to call read tools would be a
    /// behaviour widening that the design does not ask for, so it is not done
    /// here.
    pub const PLANNER_DENY_PREFIXES: &[&str] = &["*"];

    /// The four channels of the new contract (DR-42).
    pub const CHANNEL_PREFIXES: &[&str] = &["editor_", "project_", "running_game_", "os_"];

    /// Read-only / evidence-collecting verbs.  A tool whose verb is in this set
    /// does not change the artifact, so the QA role may call it (R13).
    ///
    /// `simulate` / `play` / `stop` / `run` / `capture` mutate *runtime* state or
    /// write an evidence file, never the product under evaluation: §5.4 and
    /// DR-17/DR-30/DR-35 make those the QA role's execution primitive, which is
    /// why they stay in the read side.
    const QA_READ_VERBS: &[&str] = &[
        "get", "list", "read", "search", "find", "analyze", "detect", "simulate", "assert",
        "capture", "play", "stop", "run",
    ];

    /// Verbs that can change the artifact (or the state of the object being
    /// evaluated).  The QA role never gets one of these, with the two
    /// documented exceptions below (DR-42 / R13).
    const MUTATING_VERBS: &[&str] = &[
        "add",
        "create",
        "remove",
        "delete",
        "set",
        "edit",
        "rename",
        "reparent",
        "move",
        "duplicate",
        "connect",
        "disconnect",
        "execute",
        "export",
        "deploy",
        "reload",
        "rescan",
        "bake",
        "open",
        "save",
        "setup",
        "convert",
        "update",
        "build",
        "write",
    ];

    /// The QA role's explicit exceptions: evidence-driving tools whose verb
    /// looks like a write but never touches the product.
    ///
    /// * `running_game_create_input_recording` — recording a run writes a
    ///   recording file, not a project change (§5.4 allows starting a recording);
    /// * `running_game_move_player_to_target` — scripted player movement is
    ///   input simulation (§5.4 allows moving the player to a target).
    ///
    /// §5.4's hard prohibitions — the game-side property setter and the
    /// game-side script executor — are deliberately **not** here.
    pub const QA_ALLOW_EXACT: &[&str] = &[
        "running_game_create_input_recording",
        "running_game_move_player_to_target",
    ];

    /// The Bevy 0.19.1 tool surface, by name (DESIGN-DETAIL §2).
    ///
    /// It needs an explicit list because the four-channel rule above is keyed on
    /// the *engine module's* `<channel>_<verb>_…` naming, and the Bevy surface is
    /// not named that way: the semantic tools are `bevy_*` and the generic layer
    /// passes the BRP verbs through with their own dotted names
    /// (`world.get_resources`).  Without this list the QA role would be denied
    /// every observation tool — which is precisely the "the new engine's tools
    /// are a rename of the old engine's" mistake `REQUIREMENTS.md` §8 warns
    /// about, in its most damaging direction.
    ///
    /// Everything here is either a **read** of the running game's semantic state
    /// or an **input injection**: none of them can change the frozen candidate
    /// (the artifact is the project on disk, and the running game is a child
    /// process the QA window is allowed to drive — §5.4's
    /// `running_game_move_player_to_target` is the same permission, one engine
    /// later).
    pub const BEVY_QA_ALLOW: &[&str] = &[
        // The semantic layer: read the five observed surfaces.
        "bevy_player_transform",
        "bevy_grounded",
        "bevy_coin_counter",
        "bevy_win_flag",
        "bevy_wait_frames",
        "bevy_health",
        // The semantic layer: the injection surface (evidence-driving).
        "bevy_inject_move",
        "bevy_inject_jump",
        // The generic layer's read verbs, passed through to BRP unchanged.
        "rpc.discover",
        "world.query",
        "world.get_components",
        "world.get_resources",
        "world.list_components",
        "world.list_resources",
        "world.list_entities",
        "world.get_components+watch",
        "registry.schema",
    ];

    /// Is this tool one of the Bevy surface's QA-readable/driving tools?
    pub fn is_bevy_qa_allowed(tool: &str) -> bool {
        BEVY_QA_ALLOW.contains(&tool)
    }

    /// The verb of a four-channel name (`<channel>_<verb>_<object>...`).
    ///
    /// `None` means "not a name of this contract" — an invented name used by a
    /// test, or a future tool the snapshot does not know yet.
    pub fn verb_of(tool: &str) -> Option<&str> {
        let rest = CHANNEL_PREFIXES
            .iter()
            .find_map(|channel| tool.strip_prefix(channel))?;
        let verb = rest.split('_').next().unwrap_or("");
        if verb.is_empty() {
            None
        } else {
            Some(verb)
        }
    }

    /// Would this tool change the artifact?  Unknown (unprefixed) names are not
    /// classified as mutating: they are refused for Planner/Tester by the
    /// default-deny *allowlist*, which keeps DR-7's two denial texts distinct.
    pub fn is_mutating(tool: &str) -> bool {
        match verb_of(tool) {
            Some(verb) => MUTATING_VERBS.contains(&verb),
            None => false,
        }
    }

    pub fn is_tester_allowed(tool: &str) -> bool {
        if QA_ALLOW_EXACT.contains(&tool) {
            return true;
        }
        if is_bevy_qa_allowed(tool) {
            return true;
        }
        match verb_of(tool) {
            Some(verb) => QA_READ_VERBS.contains(&verb),
            None => false,
        }
    }

    /// Default-deny matrix.  Unknown tool names are denied for Planner and
    /// Tester; only the Developer may use the full tool set.
    ///
    /// DR-42: for the QA role the explicit evidence-driving exceptions
    /// ([`QA_ALLOW_EXACT`]) override the writing-verb rule; everything else
    /// whose verb can write is denied before the allowlist is even consulted.
    pub fn tool_allowed(role: Role, tool: &str) -> bool {
        match role {
            Role::Developer => true,
            Role::Planner => false,
            Role::Tester => {
                is_tester_allowed(tool) && (QA_ALLOW_EXACT.contains(&tool) || !is_mutating(tool))
            }
        }
    }

    /// Structured reason used by `hoh tools call` and by the tool channel.
    ///
    /// DR-7: the two situations are factually different and must not share a
    /// message — a write-class tool that the role is forbidden to use is a
    /// mutation denial, while anything outside the role's allowlist (including
    /// every unknown tool, and every MCP tool for the Planner) is an allowlist
    /// denial.
    pub fn denial_reason(role: Role, tool: &str) -> &'static str {
        match role {
            Role::Tester if is_mutating(tool) => "This role may not mutate the artifact.",
            _ => "Tool not in this role's allowlist.",
        }
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

    /// DR-42: the verb is the component after the channel prefix.
    #[test]
    fn the_verb_is_the_component_after_the_channel() {
        assert_eq!(tool_matrix::verb_of("editor_get_errors"), Some("get"));
        assert_eq!(
            tool_matrix::verb_of("project_create_script"),
            Some("create")
        );
        assert_eq!(
            tool_matrix::verb_of("running_game_get_scene_tree"),
            Some("get")
        );
        assert_eq!(
            tool_matrix::verb_of("os_deploy_to_android_device"),
            Some("deploy")
        );
        // Not a contract name: the old vocabulary and partial prefixes.
        assert_eq!(tool_matrix::verb_of("bare_verb_name"), None);
        assert_eq!(tool_matrix::verb_of("editor_"), None);
    }

    /// DR-42 ②/③: a read-only role is never handed a writing verb.
    #[test]
    fn a_write_verb_is_never_granted_to_a_read_only_role() {
        for tool in [
            "editor_add_node",
            "project_create_script",
            "editor_delete_node",
            "editor_remove_node_selection",
            "editor_set_node_property",
            "project_edit_script",
            "editor_execute_gdscript",
            "running_game_execute_gdscript",
            "running_game_set_node_property",
            "editor_rescan_project_filesystem",
            "os_deploy_to_android_device",
            "project_write_text_file",
        ] {
            assert!(
                !tool_allowed(Role::Planner, tool),
                "the planner must never get `{tool}`"
            );
            assert!(
                !tool_allowed(Role::Tester, tool),
                "the QA role must never get `{tool}` (R13)"
            );
        }
    }

    /// DR-42: the QA role keeps exactly the read-only and evidence-driving
    /// scope — including the two documented exceptions and nothing more.
    #[test]
    fn qa_keeps_only_its_read_only_and_evidence_driving_scope() {
        for tool in [
            "editor_get_errors",
            "editor_get_scene_tree",
            "project_get_info",
            "project_read_script",
            "project_search_file_names",
            "editor_play_scene",
            "editor_stop_scene",
            "editor_simulate_input_sequence",
            // §5.4's evidence-driving exceptions.
            "running_game_create_input_recording",
            "running_game_move_player_to_target",
            "running_game_run_test_scenario",
            "running_game_assert_node_state",
            "running_game_capture_frames",
            "running_game_get_node_property_samples",
        ] {
            assert!(
                tool_allowed(Role::Tester, tool),
                "the QA role must keep `{tool}`"
            );
        }
        // §5.4's hard prohibitions stay prohibitions.
        assert!(!tool_allowed(Role::Tester, "running_game_execute_gdscript"));
        assert!(!tool_allowed(
            Role::Tester,
            "running_game_set_node_property"
        ));
        assert!(!tool_allowed(
            Role::Tester,
            "project_set_node_property_across_scenes"
        ));
    }

    /// The Bevy surface is not named `<channel>_<verb>_…`, so the QA role's
    /// observation tools need an explicit list.  This test is the security half
    /// of that list: every read/injection the round needs is allowed, and every
    /// verb that could **change the running world** is refused.
    #[test]
    fn the_bevy_surface_gives_the_qa_role_reads_and_injections_but_no_world_writes() {
        for tool in [
            "bevy_player_transform",
            "bevy_grounded",
            "bevy_coin_counter",
            "bevy_win_flag",
            "bevy_wait_frames",
            "bevy_health",
            "bevy_inject_move",
            "bevy_inject_jump",
            "rpc.discover",
            "world.query",
            "world.get_components",
            "world.get_resources",
            "world.list_components",
            "world.list_resources",
            "world.list_entities",
            "world.get_components+watch",
            "registry.schema",
        ] {
            assert!(
                tool_allowed(Role::Tester, tool),
                "the QA role needs `{tool}` to produce E3 evidence"
            );
        }
        // A world write is not a read: the adapter's own contract check is the
        // only thing that may change the game, and it drives its own process.
        for tool in [
            "world.mutate_resources",
            "world.mutate_components",
            "world.insert_components",
            "world.remove_components",
            "world.spawn_entity",
            "world.despawn_entity",
            "world.reparent_entities",
            "world.trigger_event",
            "world.write_message",
            "world.insert_resource",
            "world.remove_resource",
        ] {
            assert!(
                !tool_allowed(Role::Tester, tool),
                "the QA role must never be handed the world write `{tool}`"
            );
        }
        // The full list is exactly the QA allowlist for this engine: a tool that
        // is not named there is denied, so adding one is a visible decision.
        for tool in crate::adapter::mcp::all_tools() {
            if tool.mutating && !tool_matrix::BEVY_QA_ALLOW.contains(&tool.name) {
                assert!(
                    !tool_allowed(Role::Tester, tool.name),
                    "`{}` is declared mutating and must be denied",
                    tool.name
                );
            }
        }
    }

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

    /// DR-88 ④: the cache watch names exactly the adapter's cache directories —
    /// normalized, de-duplicated, and never the Tester's own submission area.
    #[test]
    fn the_cache_watch_names_only_the_adapter_cache_directories() {
        let excludes = vec![
            ".godot".to_string(),
            ".import\\".to_string(),
            ".godot/".to_string(),
            ".hoh".to_string(),
            ".git".to_string(),
            String::new(),
        ];
        assert_eq!(
            cache_prefixes(&excludes),
            vec![".godot".to_string(), ".import".to_string()]
        );
    }

    /// The cache manifest keeps `hash_tree`'s path names, so a difference names
    /// the file a reader would look for — and it is a projection, not a second
    /// identity: the admissibility of the hashed tree is untouched by it.
    #[test]
    fn the_cache_manifest_names_the_cache_paths_and_leaves_the_hash_alone() {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path();
        std::fs::create_dir_all(root.join(".godot/imported")).unwrap();
        std::fs::write(root.join(".godot/imported/cache.bin"), b"cache\n").unwrap();
        std::fs::write(root.join("project.godot"), b"config_version=5\n").unwrap();

        let prefixes = cache_prefixes(&[".godot".to_string()]);
        let manifest = cache_manifest(root, &prefixes).unwrap();
        assert_eq!(
            manifest.keys().cloned().collect::<Vec<_>>(),
            vec![".godot/imported/cache.bin".to_string()]
        );

        let excludes = HashExcludes::new([".godot"]).merged();
        let before = hash_tree(root, &excludes).unwrap();
        std::fs::write(root.join(".godot/imported/cache.bin"), b"changed\n").unwrap();
        assert_eq!(
            hash_tree(root, &excludes).unwrap(),
            before,
            "the cache must stay outside the artifact identity (R10)"
        );
        let after = cache_manifest(root, &prefixes).unwrap();
        assert_ne!(manifest, after, "but the watch must see the change");
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
