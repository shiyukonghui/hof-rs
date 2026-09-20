//! R13 — the role tool boundary.  Default-deny for Planner and Tester, full
//! access for the Developer, and a structured rejection on the CLI bridge.

use std::path::PathBuf;
use std::process::Command;

use hof_rs::model::Role;
use hof_rs::tools::policy::{denial_payload, tool_allowed};

/// Every mutating tool listed in §5.4 must be refused for the Tester.
const TESTER_MUST_BE_DENIED: &[&str] = &[
    "add_node",
    "create_scene",
    "delete_node",
    "remove_node",
    "set_property",
    "update_node",
    "move_node",
    "rename_node",
    "duplicate_node",
    "edit_script",
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

const TESTER_MUST_BE_ALLOWED: &[&str] = &[
    "get_editor_errors",
    "get_game_scene_tree",
    "get_project_info",
    "list_nodes",
    "read_file",
    "search_nodes",
    "find_node",
    "analyze_scene",
    "detect_collisions",
    "play_scene",
    "stop_scene",
    "simulate_sequence",
    "simulate_action",
    "capture_frames",
    "monitor_properties",
    "start_recording",
    "stop_recording",
    "replay_recording",
    "assert_node_state",
    "compare_screenshots",
    "run_test_scenario",
    "run_stress_test",
    "get_test_report",
    "wait_for_node",
    "click_button_by_text",
    "navigate_to",
    "move_to",
];

#[test]
fn tester_denied_mutating_tools() {
    for tool in TESTER_MUST_BE_DENIED {
        assert!(
            !tool_allowed(Role::Tester, tool),
            "the tester must not be allowed to call `{tool}`"
        );
    }
    // The two "debugging" tools are explicitly banned too.
    for tool in ["set_game_node_property", "execute_game_script"] {
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
    assert!(payload["hint"].as_str().unwrap().contains("default deny"));
}

/// The CLI bridge must refuse before touching any network or configuration.
#[test]
fn tools_call_denied_exit_code_two() {
    let binary = env!("CARGO_BIN_EXE_hoh");
    for tool in ["add_node", "totally_new_mcp_tool"] {
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
        .args(["tools", "call", "get_editor_errors", "--role", "planner"])
        .current_dir(PathBuf::from(env!("CARGO_MANIFEST_DIR")))
        .output()
        .expect("the hoh binary must be runnable");
    assert_eq!(output.status.code(), Some(2));
    assert!(String::from_utf8_lossy(&output.stdout).contains("tool_not_permitted"));
}
