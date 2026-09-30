//! DR-45 — the machine-checkable "the migration is done" guard.
//!
//! Three checks must stay green **together**; any one of them alone can be
//! satisfied while the repository is still half-migrated.
//!
//! 1. every tool in the fixture is a four-channel name
//!    (`^(editor|project|running_game|os)_[a-z0-9_]+$`) and the count is 177;
//! 2. the retired 174-name vocabulary occurs **nowhere** in `src/**`,
//!    `tests/**` or `src/prompts/**` (whole-word scan);
//! 3. conversely, every four-channel name the code *quotes* (or passes to
//!    `tools call`) is a real member of the fixture contract.
//!
//! False positives and how they are avoided:
//! * check 2 looks for the exact frozen 174 names as whole words, not for
//!   "anything that is not in the fixture".  The tests deliberately use
//!   *invented* names (`totally_unknown_mcp_tool`, `brand_new_tool`, ...) to
//!   prove default-deny, and a not-in-fixture rule would flag them.
//! * check 3 only inspects tokens inside a quote (`` `name` `` / `"name"`) or
//!   directly after `tools call `, so an identifier such as
//!   `project_declared_actions` — which merely *looks* like a channel name — is
//!   never mistaken for a tool call.
//! * the few quoted tokens that match the channel shape without being tools are
//!   listed explicitly in [`NON_TOOL_PREFIXED_TOKENS`]; nothing else is
//!   excluded.
//! * two files are outside the check-2 scan and are named in
//!   [`SCAN_EXCLUDES`]: this guard itself (it has to spell the retired
//!   vocabulary out) and the contract fixture (its prose fields may name a
//!   retired tool while explaining a rename).
//!
//! False negatives that remain: a retired name built at run time by string
//! concatenation, or one hidden in a file type not listed in [`SCANNED_SUFFIXES`],
//! would not be seen.  Both are impossible for a literal tool call, which is
//! what this guard exists to catch.

use std::path::{Path, PathBuf};

/// The retired vocabulary: the 174 unprefixed names of the GDExtension-era
/// contract, verbatim from the engine-side rename map
/// (`godot-mcp/godot/modules/mcp_server/docs/tool-rename-map.json`, `old_name`;
/// sha256 of that file at DR-42 is
/// `2f552719f6a23fe328df0a2944c6048824c1b2a750aebc0fe2cabbcd3529c2bd`).
const OLD_VOCABULARY: &[&str] = &[
    "get_project_info",
    "get_filesystem_tree",
    "search_files",
    "search_in_files",
    "get_project_settings",
    "set_project_setting",
    "uid_to_project_path",
    "project_path_to_uid",
    "get_scene_tree",
    "get_scene_file_content",
    "open_scene",
    "delete_scene",
    "add_scene_instance",
    "get_scene_exports",
    "play_scene",
    "stop_scene",
    "save_scene",
    "create_scene",
    "add_node",
    "delete_node",
    "rename_node",
    "update_property",
    "get_node_properties",
    "duplicate_node",
    "connect_signal",
    "disconnect_signal",
    "move_node",
    "add_resource",
    "set_anchor_preset",
    "get_node_groups",
    "set_node_groups",
    "find_nodes_in_group",
    "get_editor_selection",
    "select_nodes",
    "clear_editor_selection",
    "execute_editor_script",
    "get_editor_errors",
    "get_output_log",
    "get_editor_screenshot",
    "get_game_screenshot",
    "clear_output",
    "reload_plugin",
    "reload_project",
    "get_signals",
    "compare_screenshots",
    "set_auto_dismiss",
    "get_editor_camera",
    "set_editor_camera",
    "get_game_scene_tree",
    "get_game_node_properties",
    "set_game_node_property",
    "capture_frames",
    "monitor_properties",
    "execute_game_script",
    "start_recording",
    "stop_recording",
    "replay_recording",
    "find_nodes_by_script",
    "get_autoload",
    "batch_get_properties",
    "find_ui_elements",
    "click_button_by_text",
    "wait_for_node",
    "find_nearby_nodes",
    "navigate_to",
    "move_to",
    "watch_signals",
    "get_performance_monitors",
    "get_editor_performance",
    "list_scripts",
    "read_script",
    "create_script",
    "edit_script",
    "attach_script",
    "get_open_scripts",
    "validate_script",
    "simulate_key",
    "simulate_mouse_click",
    "simulate_mouse_move",
    "simulate_action",
    "get_input_actions",
    "set_input_action",
    "simulate_sequence",
    "find_nodes_by_type",
    "batch_set_property",
    "find_signal_connections",
    "batch_add_nodes",
    "find_node_references",
    "get_scene_dependencies",
    "cross_scene_set_property",
    "list_animations",
    "create_animation",
    "add_animation_track",
    "set_animation_keyframe",
    "get_animation_info",
    "remove_animation",
    "tilemap_get_info",
    "tilemap_get_used_cells",
    "tilemap_clear",
    "tilemap_set_cell",
    "tilemap_fill_rect",
    "tilemap_get_cell",
    "read_resource",
    "add_autoload",
    "remove_autoload",
    "edit_resource",
    "create_resource",
    "get_resource_preview",
    "get_export_info",
    "list_export_presets",
    "export_project",
    "read_shader",
    "create_shader",
    "edit_shader",
    "assign_shader_material",
    "set_shader_param",
    "get_shader_params",
    "add_raycast",
    "setup_collision",
    "set_physics_layers",
    "get_physics_layers",
    "setup_physics_body",
    "get_collision_info",
    "add_mesh_instance",
    "setup_camera_3d",
    "setup_lighting",
    "set_material_3d",
    "setup_environment",
    "add_gridmap",
    "add_audio_player",
    "get_audio_info",
    "get_audio_bus_layout",
    "add_audio_bus",
    "set_audio_bus",
    "add_audio_bus_effect",
    "create_theme",
    "set_theme_color",
    "set_theme_constant",
    "set_theme_font_size",
    "set_theme_stylebox",
    "setup_control",
    "get_theme_info",
    "create_animation_tree",
    "get_animation_tree_structure",
    "add_state_machine_state",
    "remove_state_machine_state",
    "add_state_machine_transition",
    "remove_state_machine_transition",
    "set_blend_tree_node",
    "set_tree_parameter",
    "setup_navigation_region",
    "bake_navigation_mesh",
    "setup_navigation_agent",
    "set_navigation_layers",
    "get_navigation_info",
    "create_particles",
    "set_particle_material",
    "set_particle_color_gradient",
    "apply_particle_preset",
    "get_particle_info",
    "find_unused_resources",
    "analyze_signal_flow",
    "analyze_scene_complexity",
    "find_script_references",
    "detect_circular_dependencies",
    "get_project_statistics",
    "run_test_scenario",
    "assert_node_state",
    "assert_screen_text",
    "run_stress_test",
    "get_test_report",
    "list_android_devices",
    "get_android_preset_info",
    "deploy_to_android",
];

/// Quoted tokens that match the four-channel shape, whose verb is a real
/// contract verb, and which are nevertheless not tool names.
///
/// Only the deterministic battery's step ids qualify, and of them only one has
/// a verb the contract itself uses: `project_reload_and_open`.  Everything else
/// that merely *looks* like a channel name (`editor_errors_baseline`,
/// `editor_process`, `editor_status`, `os_error`, ...) is already rejected by
/// the verb filter below, because its second component is not a verb of the
/// contract.  There is no other exclusion.
const NON_TOOL_PREFIXED_TOKENS: &[&str] = &["project_reload_and_open"];

/// Files the whole-word vocabulary scan deliberately skips.
const SCAN_EXCLUDES: &[&str] = &[
    "tests/tool_vocabulary.rs",
    "tests/fixtures/mcp/tools_list.json",
];

/// File types the scans walk.
const SCANNED_SUFFIXES: &[&str] = &[".rs", ".md", ".json", ".yaml", ".yml", ".toml", ".txt"];

const FIXTURE: &str = include_str!("fixtures/mcp/tools_list.json");

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn fixture_names() -> Vec<String> {
    let value: serde_json::Value = serde_json::from_str(FIXTURE.trim_start_matches('\u{feff}'))
        .expect("the MCP fixture must be valid JSON");
    value
        .pointer("/result/tools")
        .and_then(serde_json::Value::as_array)
        .expect("the fixture must carry `result.tools`")
        .iter()
        .filter_map(|tool| tool.get("name").and_then(serde_json::Value::as_str))
        .map(ToOwned::to_owned)
        .collect()
}

/// `^(editor|project|running_game|os)_[a-z0-9_]+$`, spelled out so the guard
/// depends on nothing but `std`.
fn is_four_channel_name(name: &str) -> bool {
    const CHANNELS: &[&str] = &["running_game_", "editor_", "project_", "os_"];
    let Some(rest) = CHANNELS
        .iter()
        .find_map(|channel| name.strip_prefix(channel))
    else {
        return false;
    };
    !rest.is_empty()
        && !rest.starts_with('_')
        && !rest.ends_with('_')
        && rest.chars().all(|character| {
            character.is_ascii_lowercase() || character.is_ascii_digit() || character == '_'
        })
}

/// The verbs the contract itself uses, i.e. the second component of every
/// fixture name.  A quoted token whose second component is not one of these is
/// not a tool name (it is a step id, a JSON field or prose), which is what makes
/// check 3 free of false positives.
fn contract_verbs(names: &[String]) -> std::collections::BTreeSet<String> {
    names
        .iter()
        .filter_map(|name| second_component(name).map(ToOwned::to_owned))
        .collect()
}

/// The component after the channel prefix.
fn second_component(name: &str) -> Option<&str> {
    const CHANNELS: &[&str] = &["running_game_", "editor_", "project_", "os_"];
    let rest = CHANNELS
        .iter()
        .find_map(|channel| name.strip_prefix(channel))?;
    rest.split('_').next()
}

/// Every significant file under `src/`, `tests/` and `src/prompts/`.
fn scanned_files() -> Vec<(String, String)> {
    fn walk(root: &Path, dir: &Path, out: &mut Vec<(String, String)>) {
        let Ok(entries) = std::fs::read_dir(dir) else {
            return;
        };
        for entry in entries.flatten() {
            let path = entry.path();
            let name = entry.file_name().to_string_lossy().into_owned();
            if entry.file_type().map(|kind| kind.is_dir()).unwrap_or(false) {
                if name == "target" || name == ".git" {
                    continue;
                }
                walk(root, &path, out);
                continue;
            }
            let relative = path
                .strip_prefix(root)
                .unwrap_or(&path)
                .to_string_lossy()
                .replace('\\', "/");
            if SCAN_EXCLUDES.contains(&relative.as_str()) {
                continue;
            }
            if !SCANNED_SUFFIXES
                .iter()
                .any(|suffix| relative.ends_with(suffix))
            {
                continue;
            }
            if let Ok(text) = std::fs::read_to_string(&path) {
                out.push((relative, text));
            }
        }
    }
    let root = repo_root();
    let mut out = Vec::new();
    for dir in ["src", "tests"] {
        walk(&root, &root.join(dir), &mut out);
    }
    out
}

/// Does `text` contain `needle` as a whole word (`[A-Za-z0-9_]` boundaries)?
fn contains_whole_word(text: &str, needle: &str) -> bool {
    fn is_word(character: char) -> bool {
        character.is_ascii_alphanumeric() || character == '_'
    }
    let mut from = 0usize;
    while let Some(offset) = text[from..].find(needle) {
        let start = from + offset;
        let end = start + needle.len();
        let before_ok = text[..start]
            .chars()
            .next_back()
            .map(|c| !is_word(c))
            .unwrap_or(true);
        let after_ok = text[end..]
            .chars()
            .next()
            .map(|c| !is_word(c))
            .unwrap_or(true);
        if before_ok && after_ok {
            return true;
        }
        from = start + 1;
        if from >= text.len() {
            break;
        }
    }
    false
}

/// The four-channel-shaped tokens of `text` that sit inside quotes or directly
/// after `tools call `.
fn quoted_tool_tokens(text: &str, verbs: &std::collections::BTreeSet<String>) -> Vec<String> {
    fn token_char(character: char) -> bool {
        character.is_ascii_lowercase() || character.is_ascii_digit() || character == '_'
    }
    let characters: Vec<char> = text.chars().collect();
    let mut tokens = Vec::new();
    let mut index = 0usize;
    while index < characters.len() {
        if !characters[index].is_ascii_lowercase() {
            index += 1;
            continue;
        }
        let start = index;
        let mut end = index;
        while end < characters.len() && token_char(characters[end]) {
            end += 1;
        }
        let token: String = characters[start..end].iter().collect();
        let is_tool_shaped = is_four_channel_name(&token)
            && second_component(&token).is_some_and(|verb| verbs.contains(verb));
        if is_tool_shaped {
            let before = if start > 0 {
                characters[start - 1]
            } else {
                ' '
            };
            let after = if end < characters.len() {
                characters[end]
            } else {
                ' '
            };
            let quoted = (before == '"' || before == '`') && (after == '"' || after == '`');
            let offset = text
                .char_indices()
                .nth(start)
                .map(|(offset, _)| offset)
                .unwrap_or(0);
            let call_form = text[..offset].ends_with("tools call ");
            if quoted || call_form {
                tokens.push(token);
            }
        }
        index = end.max(start + 1);
    }
    tokens
}

/// DR-45 ①: the fixture is the 177-tool four-channel contract.
#[test]
fn the_fixture_is_the_four_channel_contract() {
    let names = fixture_names();
    assert_eq!(
        names.len(),
        177,
        "the fixture must carry the 177-tool contract (DR-42)"
    );
    for name in &names {
        assert!(
            is_four_channel_name(name),
            "`{name}` is not `(editor|project|running_game|os)_<verb>_<object>` (DR-42)"
        );
    }
    for channel in ["editor_", "project_", "running_game_", "os_"] {
        assert!(
            names.iter().any(|name| name.starts_with(channel)),
            "the contract must use the `{channel}` channel (DR-42)"
        );
    }
}

/// DR-45 ②: the retired vocabulary is gone from every scanned file.
#[test]
fn the_retired_vocabulary_is_gone() {
    let files = scanned_files();
    assert!(files.len() > 50, "the scan must actually see the tree");
    let mut found: Vec<String> = Vec::new();
    for (relative, text) in &files {
        for name in OLD_VOCABULARY {
            if contains_whole_word(text, name) {
                found.push(format!("{relative}: {name}"));
            }
        }
    }
    assert!(
        found.is_empty(),
        "the retired GDExtension-era vocabulary still appears in {} place(s) (DR-45):\n{}",
        found.len(),
        found.join("\n")
    );
}

/// DR-45 ③: every quoted four-channel token is a real member of the contract.
#[test]
fn every_quoted_tool_name_exists_in_the_contract() {
    let names = fixture_names();
    let known: std::collections::BTreeSet<String> = names.iter().cloned().collect();
    let verbs = contract_verbs(&names);
    let mut unknown: Vec<String> = Vec::new();
    for (relative, text) in scanned_files() {
        for token in quoted_tool_tokens(&text, &verbs) {
            if NON_TOOL_PREFIXED_TOKENS.contains(&token.as_str()) {
                continue;
            }
            if !known.contains(&token) {
                unknown.push(format!("{relative}: {token}"));
            }
        }
    }
    unknown.sort();
    unknown.dedup();
    assert!(
        unknown.is_empty(),
        "these quoted names are not in the fixture contract (DR-45):\n{}",
        unknown.join("\n")
    );
}

/// Sanity: the guard must be able to tell a retired name from a new one, so it
/// cannot pass by being blind.
#[test]
fn the_guard_recognises_both_vocabularies() {
    assert!(contains_whole_word(
        "self.call(\"play_scene\")",
        "play_scene"
    ));
    assert!(!contains_whole_word(
        "self.call(\"editor_play_scene\")",
        "play_scene"
    ));
    assert!(is_four_channel_name("running_game_get_scene_tree"));
    assert!(is_four_channel_name("os_list_android_devices"));
    assert!(!is_four_channel_name("project_declared_actions("));
    assert!(!is_four_channel_name("editor_"));
    assert!(!is_four_channel_name("play_scene"));
    let verbs = contract_verbs(&fixture_names());
    let tokens = quoted_tool_tokens(
        "self.call(\"editor_play_scene\") and project_declared_actions(&x) and \"editor_status\"",
        &verbs,
    );
    assert_eq!(tokens, vec!["editor_play_scene".to_string()]);
}
