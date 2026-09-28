//! R13 — the role tool boundary.  Default-deny for Planner and Tester, full
//! access for the Developer, and a structured rejection on the CLI bridge.
//!
//! DR-42: every name below is a member of the four-channel contract
//! (`tests/fixtures/mcp/tools_list.json`); `the_role_lists_only_name_contract_tools`
//! keeps them from rotting.

use std::path::PathBuf;
use std::process::Command;

use hof_rs::model::Role;
use hof_rs::tools::policy::{denial_payload, is_mutating, tool_allowed, QA_ALLOW_EXACT};

/// The captured contract snapshot, so the lists can be checked against it.
const FIXTURE: &str = include_str!("fixtures/mcp/tools_list.json");

fn contract_names() -> Vec<String> {
    let value: serde_json::Value = serde_json::from_str(FIXTURE).expect("fixture json");
    value
        .pointer("/result/tools")
        .and_then(serde_json::Value::as_array)
        .expect("result.tools")
        .iter()
        .filter_map(|tool| tool.get("name").and_then(serde_json::Value::as_str))
        .map(ToOwned::to_owned)
        .collect()
}

/// Every mutating tool of the contract must be refused for the Tester (R13).
/// A representative name per writing verb of the new vocabulary.
const TESTER_MUST_BE_DENIED: &[&str] = &[
    "editor_add_node",
    "editor_add_input_action",
    "editor_bake_navigation_mesh",
    "editor_connect_signal",
    "editor_delete_node",
    "editor_disconnect_signal",
    "editor_duplicate_node",
    "editor_execute_gdscript",
    "editor_remove_all_tilemap_cells",
    "editor_remove_node_selection",
    "editor_remove_output_log",
    "editor_rename_node",
    "editor_reparent_node",
    "editor_rescan_project_filesystem",
    "editor_reload_plugin",
    "editor_set_node_property",
    "editor_set_node_property_batch",
    "editor_set_node_property_updates",
    "editor_set_node_script",
    "editor_set_tilemap_cell",
    "editor_set_tilemap_cells_in_rect",
    "os_deploy_to_android_device",
    "project_create_scene_file",
    "project_edit_script",
    "project_set_node_property_across_scenes",
    "project_set_setting",
    "project_write_text_file",
    "running_game_execute_gdscript",
    "running_game_set_node_property",
];

const TESTER_MUST_BE_ALLOWED: &[&str] = &[
    // read verbs
    "editor_get_errors",
    "editor_get_scene_tree",
    "editor_find_nodes_by_type",
    "editor_analyze_screenshot_diff",
    "editor_get_test_report",
    "project_get_info",
    "project_list_scripts",
    "project_read_script",
    "project_search_file_names",
    "project_analyze_scene_complexity",
    "project_detect_circular_dependencies",
    "running_game_get_scene_tree",
    "running_game_find_node_when_available",
    // execution / assertion verbs
    "editor_play_scene",
    "editor_stop_scene",
    "editor_simulate_input_sequence",
    "editor_simulate_input_action",
    "running_game_capture_frames",
    "running_game_get_node_property_samples",
    "running_game_run_test_scenario",
    "running_game_run_stress_test",
    "running_game_assert_node_state",
    "running_game_simulate_button_click_by_text",
    // §5.4's two evidence-driving exceptions (DR-42 QA_ALLOW_EXACT)
    "running_game_create_input_recording",
    "running_game_stop_input_recording",
    "running_game_play_input_recording",
    "running_game_move_player_to_target",
];

/// DR-42 hygiene: the two lists above may only name real contract tools.  A
/// retired or invented name here would silently test nothing.
#[test]
fn the_role_lists_only_name_contract_tools() {
    let known: std::collections::BTreeSet<String> = contract_names().into_iter().collect();
    for tool in TESTER_MUST_BE_DENIED
        .iter()
        .chain(TESTER_MUST_BE_ALLOWED.iter())
    {
        assert!(
            known.contains(*tool),
            "`{tool}` is not in the 177-tool contract (DR-42)"
        );
    }
}

/// DR-42 ③: no artifact-changing tool of the *whole contract* is reachable by
/// the QA role — not just the samples listed above.  The only names exempted
/// are the two documented evidence-driving exceptions (`QA_ALLOW_EXACT`),
/// which drive the running game instead of the artifact.
#[test]
fn qa_is_denied_every_mutating_tool_of_the_contract() {
    let mutating: Vec<String> = contract_names()
        .into_iter()
        .filter(|name| is_mutating(name))
        .collect();
    assert!(
        mutating.len() > 50,
        "the contract must contain many writing verbs, found {}",
        mutating.len()
    );
    assert_eq!(
        QA_ALLOW_EXACT.len(),
        2,
        "DR-42 allows exactly two evidence-driving exceptions"
    );
    for tool in QA_ALLOW_EXACT {
        assert!(
            tool_allowed(Role::Tester, tool),
            "the documented exception `{tool}` must stay callable"
        );
        assert!(
            is_mutating(tool),
            "`{tool}` is an exception precisely because its verb looks like a write"
        );
    }
    for tool in &mutating {
        if QA_ALLOW_EXACT.contains(&tool.as_str()) {
            continue;
        }
        assert!(
            !tool_allowed(Role::Tester, tool),
            "the QA role must not be able to call `{tool}` (R13)"
        );
    }
    // Over the whole contract, exactly the two documented names with a writing
    // verb stay reachable — nothing else.
    let reachable: Vec<&String> = mutating
        .iter()
        .filter(|name| tool_allowed(Role::Tester, name))
        .collect();
    assert_eq!(reachable.len(), QA_ALLOW_EXACT.len(), "{reachable:?}");
}

/// DR-42 ②: the Planner is denied every tool of the contract, and in
/// particular every writing one.
#[test]
fn planner_is_denied_every_tool_of_the_contract() {
    for tool in contract_names() {
        assert!(
            !tool_allowed(Role::Planner, &tool),
            "the planner is planning-only and must not call `{tool}`"
        );
    }
}

#[test]
fn tester_denied_mutating_tools() {
    for tool in TESTER_MUST_BE_DENIED {
        assert!(
            !tool_allowed(Role::Tester, tool),
            "the tester must not be allowed to call `{tool}`"
        );
    }
    // The two "debugging" tools are explicitly banned too (§5.4).
    for tool in [
        "running_game_set_node_property",
        "running_game_execute_gdscript",
    ] {
        assert!(!tool_allowed(Role::Tester, tool));
    }
    // Read/execute tools stay available.
    for tool in TESTER_MUST_BE_ALLOWED {
        assert!(
            tool_allowed(Role::Tester, tool),
            "the tester must be allowed to call `{tool}`"
        );
    }
}

#[test]
fn developer_allowed_all() {
    let sample: Vec<&str> = TESTER_MUST_BE_ALLOWED
        .iter()
        .chain(TESTER_MUST_BE_DENIED.iter())
        .copied()
        .collect();
    for tool in sample {
        assert!(
            tool_allowed(Role::Developer, tool),
            "the developer is the single writer and must be allowed `{tool}`"
        );
    }
    assert!(tool_allowed(Role::Developer, "some_future_tool"));
}

#[test]
fn planner_denied_all_mcp() {
    let sample: Vec<&str> = TESTER_MUST_BE_ALLOWED
        .iter()
        .chain(TESTER_MUST_BE_DENIED.iter())
        .copied()
        .collect();
    for tool in sample {
        assert!(
            !tool_allowed(Role::Planner, tool),
            "the planner is planning-only and must not call `{tool}`"
        );
    }
    assert!(!tool_allowed(Role::Planner, "brand_new_tool"));
}

#[test]
fn default_deny_unknown() {
    for tool in ["frobnicate_world", "totally_new_mcp_tool", "x"] {
        assert!(!tool_allowed(Role::Tester, tool), "{tool} must be denied");
        assert!(!tool_allowed(Role::Planner, tool), "{tool} must be denied");
        assert!(tool_allowed(Role::Developer, tool), "{tool} is dev-allowed");
    }

    let payload = denial_payload(Role::Tester, "totally_new_mcp_tool");
    assert_eq!(payload["error"], serde_json::json!("tool_not_permitted"));
    assert_eq!(
        payload["hint"],
        serde_json::json!("Tool not in this role's allowlist.")
    );
}

/// DR-7: the rejection text must distinguish "this role may not mutate" from
/// "not in this role's allowlist".  The Planner owns no MCP tool at all, so
/// every MCP tool is an allowlist denial for it.
#[test]
fn denial_hints_distinguish_mutation_from_allowlist() {
    assert_eq!(
        denial_payload(Role::Tester, "editor_add_node")["hint"],
        serde_json::json!("This role may not mutate the artifact.")
    );
    assert_eq!(
        denial_payload(Role::Tester, "running_game_execute_gdscript")["hint"],
        serde_json::json!("This role may not mutate the artifact.")
    );
    assert_eq!(
        denial_payload(Role::Planner, "editor_get_errors")["hint"],
        serde_json::json!("Tool not in this role's allowlist.")
    );
    assert_eq!(
        denial_payload(Role::Planner, "editor_add_node")["hint"],
        serde_json::json!("Tool not in this role's allowlist.")
    );
    assert_eq!(
        denial_payload(Role::Tester, "totally_unknown_mcp_tool")["hint"],
        serde_json::json!("Tool not in this role's allowlist.")
    );

    // The CLI bridge must print the same distinct texts.
    let binary = env!("CARGO_BIN_EXE_hoh");
    for (role, tool, expected) in [
        ("planner", "editor_get_errors", "allowlist"),
        ("tester", "editor_add_node", "may not mutate"),
    ] {
        let output = Command::new(binary)
            .args(["tools", "call", tool, "--role", role])
            .current_dir(PathBuf::from(env!("CARGO_MANIFEST_DIR")))
            .output()
            .expect("the hoh binary must be runnable");
        assert_eq!(output.status.code(), Some(2));
        let stdout = String::from_utf8_lossy(&output.stdout);
        assert!(
            stdout.contains(expected),
            "`{role}` calling `{tool}` should say `{expected}`: {stdout}"
        );
    }
}

/// The CLI bridge must refuse before touching any network or configuration.
#[test]
fn tools_call_denied_exit_code_two() {
    let binary = env!("CARGO_BIN_EXE_hoh");
    for tool in ["editor_add_node", "totally_new_mcp_tool"] {
        let output = Command::new(binary)
            .args(["tools", "call", tool, "--role", "tester"])
            .current_dir(PathBuf::from(env!("CARGO_MANIFEST_DIR")))
            .output()
            .expect("the hoh binary must be runnable");
        assert_eq!(
            output.status.code(),
            Some(2),
            "denied tool `{tool}` must exit 2, stderr: {}",
            String::from_utf8_lossy(&output.stderr)
        );
        let stdout = String::from_utf8_lossy(&output.stdout);
        assert!(
            stdout.contains("tool_not_permitted"),
            "missing structured rejection for `{tool}`: {stdout}"
        );
        assert!(stdout.contains("\"role\": \"tester\""));
    }

    // The Planner is denied every MCP tool as well.
    let output = Command::new(binary)
        .args(["tools", "call", "editor_get_errors", "--role", "planner"])
        .current_dir(PathBuf::from(env!("CARGO_MANIFEST_DIR")))
        .output()
        .expect("the hoh binary must be runnable");
    assert_eq!(output.status.code(), Some(2));
    assert!(String::from_utf8_lossy(&output.stdout).contains("tool_not_permitted"));
}

/// The Developer has no submittable artifact; `submit` must refuse it.
#[test]
fn submit_developer_is_refused() {
    let temp = tempfile::tempdir().unwrap();
    let file = temp.path().join("developer.md");
    std::fs::write(&file, "anything").unwrap();

    let output = Command::new(env!("CARGO_BIN_EXE_hoh"))
        .args(["submit", "--role", "developer", "--file"])
        .arg(&file)
        .current_dir(PathBuf::from(env!("CARGO_MANIFEST_DIR")))
        .output()
        .expect("the hoh binary must be runnable");
    assert_eq!(output.status.code(), Some(2));
    assert!(String::from_utf8_lossy(&output.stdout).contains("tool_not_permitted"));
}

/// The inner gate of §4.3: `hoh submit` validates immediately, writes the
/// canonical path on success, and reports precise issues (exit 3) on failure.
#[test]
fn submit_validates_and_writes_the_canonical_artifact() {
    let temp = tempfile::tempdir().unwrap();
    let artifact_dir = temp.path().join("view/.hoh");
    std::fs::create_dir_all(&artifact_dir).unwrap();
    let binary = env!("CARGO_BIN_EXE_hoh");
    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));

    // Valid plan -> written to the canonical path, exit 0.
    let good = manifest.join("tests/fixtures/plan_ok.md");
    let output = Command::new(binary)
        .args(["submit", "--role", "planner", "--file"])
        .arg(&good)
        .env("HOH_ARTIFACT_DIR", &artifact_dir)
        .current_dir(&manifest)
        .output()
        .unwrap();
    assert_eq!(
        output.status.code(),
        Some(0),
        "stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let written = artifact_dir.join("plan.md");
    assert!(written.is_file());
    assert_eq!(
        std::fs::read_to_string(&written).unwrap(),
        std::fs::read_to_string(&good).unwrap()
    );

    // The missing Preservation Gate -> precise issues, exit 3, nothing written.
    let bad = manifest.join("tests/fixtures/plan_missing_gate.md");
    let output = Command::new(binary)
        .args(["submit", "--role", "planner", "--file"])
        .arg(&bad)
        .env("HOH_ARTIFACT_DIR", &artifact_dir)
        .current_dir(&manifest)
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(3));
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("missing_section"), "stdout: {stdout}");
    assert!(stdout.contains("\"ok\": false"));
    assert_eq!(
        std::fs::read_to_string(&written).unwrap(),
        std::fs::read_to_string(&good).unwrap(),
        "a rejected submission must not overwrite the previous artifact"
    );

    // The dangling-evidence fixture is rejected for the Tester as well.
    let output = Command::new(binary)
        .args(["submit", "--role", "tester", "--file"])
        .arg(manifest.join("tests/fixtures/evidence_dangling.json"))
        .env("HOH_ARTIFACT_DIR", &artifact_dir)
        .current_dir(&manifest)
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(3));
    let stdout = String::from_utf8_lossy(&output.stdout);
    // A6/FIX-11: `"ok": false` must be asserted explicitly — the string `ok`
    // alone also matches a successful `{"ok": true}` body.
    assert!(stdout.contains("\"ok\": false"), "stdout: {stdout}");
    assert!(stdout.contains("dangling_evidence"), "stdout: {stdout}");
}

/// DR-10 (A1): the *same* check runs inside `hoh submit` — the inner gate has
/// no candidate identity, but it does have the view root, so an escaping path
/// must be refused there too even though the target file really exists.
#[test]
fn submit_rejects_an_escaping_evidence_path() {
    let temp = tempfile::tempdir().unwrap();
    let view = temp.path().join("view");
    let artifact_dir = view.join(".hoh");
    std::fs::create_dir_all(&artifact_dir).unwrap();
    // The file exists, one level above the view root.
    std::fs::write(temp.path().join("outside_secret.txt"), "secret\n").unwrap();

    let escaping = temp.path().join("escaping_evidence.json");
    std::fs::write(
        &escaping,
        r#"{
  "iteration": 1,
  "qa_status": "partial",
  "verified_records": [
    {
      "claim_id": "F1",
      "claim": "player moves right",
      "execution_records": [
        {"type": "assert", "path": "../outside_secret.txt", "observation": "leaked"}
      ],
      "status": "verified"
    }
  ],
  "gap_records": [],
  "planner_handoff": {"preservation_constraints": [], "update_targets": [], "validation_requirements": []}
}
"#,
    )
    .unwrap();

    let output = Command::new(env!("CARGO_BIN_EXE_hoh"))
        .args(["submit", "--role", "tester", "--file"])
        .arg(&escaping)
        .env("HOH_ARTIFACT_DIR", &artifact_dir)
        .current_dir(PathBuf::from(env!("CARGO_MANIFEST_DIR")))
        .output()
        .unwrap();
    assert_eq!(
        output.status.code(),
        Some(3),
        "stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("dangling_evidence"), "stdout: {stdout}");
    assert!(!artifact_dir.join("evidence.json").exists());
}
