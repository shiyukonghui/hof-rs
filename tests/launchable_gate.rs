//! DR-24 — the pre-freeze "launchable" gate and the one-shot targeted repair.
//!
//! The second real smoke run completed the whole loop with a legal `E_1` while
//! `scenes/main.tscn` had **no root node** (`Invalid scene`), so `play_scene`
//! lied (`playing: true`) and 6/7 battery steps failed.  The paper's "keep the
//! project buildable and runnable" must be a *checked gate*, not a request.
//!
//! These tests drive the real `GodotAdapter` battery through a scripted MCP
//! channel that answers from the scene on disk, so `launchable` flips exactly
//! when the Developer repairs the scene.

mod common;

use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};

use common::*;
use hof_rs::adapter::godot::{validate_scene_structure, BatteryLimits, GodotAdapter};
use hof_rs::config::{GodotConfig, HohConfig};
use hof_rs::model::{Ablation, Role};
use hof_rs::tools::mcp::McpError;
use hof_rs::tools::{ToolChannel, ToolResult};
use serde_json::{json, Value};

/// Main scene with **no root node**: every declaration carries `parent="."`.
/// This is the verbatim shape of the `smoke-t2` failure.
const SCENE_WITHOUT_ROOT: &str = r#"[gd_scene load_steps=2 format=3]

[node name="Ground" type="StaticBody2D" parent="."]

[node name="Player" type="CharacterBody2D" parent="."]
"#;

/// A legal minimal scene: exactly one root, everything else parented.
const SCENE_WITH_ROOT: &str = r#"[gd_scene load_steps=2 format=3]

[node name="Main" type="Node2D"]

[node name="Ground" type="StaticBody2D" parent="."]

[node name="Player" type="CharacterBody2D" parent="."]
"#;

// ---------------------------------------------------------------------------
// A scripted channel that answers from the scene really present on disk
// ---------------------------------------------------------------------------

struct GateChannel {
    workspace: PathBuf,
    calls: Mutex<Vec<(String, Value)>>,
}

impl GateChannel {
    fn new(workspace: &Path) -> Self {
        Self {
            workspace: workspace.to_path_buf(),
            calls: Mutex::new(Vec::new()),
        }
    }

    fn scene_text(&self) -> Option<String> {
        std::fs::read_to_string(self.workspace.join("scenes/main.tscn")).ok()
    }

    fn scene_valid(&self) -> bool {
        self.scene_text()
            .map(|text| validate_scene_structure(&text).ok)
            .unwrap_or(false)
    }
}

#[async_trait::async_trait]
impl ToolChannel for GateChannel {
    fn allowed(&self, _role: Role, _tool: &str) -> bool {
        true
    }

    fn index_markdown(&self, _role: Role) -> String {
        "# tools\n".to_string()
    }

    async fn call(&self, _role: Role, tool: &str, args: Value) -> anyhow::Result<ToolResult> {
        self.calls
            .lock()
            .unwrap()
            .push((tool.to_string(), args.clone()));
        let payload = match tool {
            "reload_project" => json!({"reloaded": true}),
            "open_scene" => json!({"opened": args.get("path").cloned().unwrap_or(Value::Null)}),
            "get_scene_file_content" => match self.scene_text() {
                Some(text) => json!({"path": args["path"], "content": text}),
                None => {
                    return Err(
                        McpError::new(-32603, "场景文件不存在: res://scenes/main.tscn").into(),
                    )
                }
            },
            "get_editor_errors" => {
                if self.scene_valid() {
                    json!({"errors": []})
                } else {
                    return Err(McpError::new(
                        -32603,
                        "Invalid scene: root node Ground cannot specify a parent node",
                    )
                    .into());
                }
            }
            "play_scene" => json!({"playing": true}),
            "get_game_scene_tree" => {
                if self.scene_valid() {
                    json!({
                        "tree": {
                            "name": "Main",
                            "path": "/root/Main",
                            "type": "Node2D",
                            "children": [{"name": "Player", "path": "/root/Main/Player", "type": "CharacterBody2D", "children": []}]
                        }
                    })
                } else {
                    return Err(McpError::new(-32603, "等待游戏响应超时 (5秒)").into());
                }
            }
            other => return Err(McpError::new(-32603, format!("unscripted tool `{other}`")).into()),
        };
        Ok(ToolResult { ok: true, payload })
    }
}

// ---------------------------------------------------------------------------
// Run helper
// ---------------------------------------------------------------------------

struct GateRun {
    run_dir: PathBuf,
    workspace: PathBuf,
    records: Vec<InvocationRecord>,
    result: Value,
}

fn adapter(root: &Path) -> GodotAdapter {
    GodotAdapter::new(
        GodotConfig {
            editor_binary: std::path::PathBuf::new(),
            cache_excludes: vec![".godot".to_string()],
            main_scene: "res://scenes/main.tscn".to_string(),
        },
        true,
    )
    .with_battery_limits(BatteryLimits {
        ready_timeout_seconds: 0,
        max_retries: 0,
        timeout_seconds: 5,
    })
}

async fn run_gate(root: &Path, script: Vec<FakeStep>) -> GateRun {
    let mut cfg: HohConfig = test_config(root, 1);
    cfg.runtime.spec = root.join("spec.md");
    let spec = write_spec(root);
    let harness = FakeHarness::new(script);
    let observer = harness.clone();
    let workspace = cfg.runtime.workspace.clone();
    let run_dir = cfg.runtime.runs_dir.join("run-1");
    let channel = Arc::new(GateChannel::new(&workspace));
    let orchestrator = hof_rs::runtime::run_loop::Orchestrator {
        harness: Box::new(harness),
        adapter: Box::new(adapter(root)),
        tools: channel.clone(),
        cfg,
        ablation: Ablation::default(),
        force_init: true,
        start_state: hof_rs::runtime::start_state::StartState::as_is(),
    };
    hof_rs::runtime::run_loop::run(&orchestrator, &spec, "run-1")
        .await
        .expect("DR-24's gate never fails the round by itself");

    let result: Value =
        serde_json::from_str(&read(&run_dir.join("iter-1/result.json"))).expect("result.json");
    GateRun {
        run_dir,
        workspace,
        records: observer.records(),
        result,
    }
}

fn plan_step() -> FakeStep {
    FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN)
}

fn tester_step() -> FakeStep {
    FakeStep::new(Role::Tester)
        .writing(".hoh/evidence/move.json", "{}\n")
        .writing(".hoh/evidence.json", &ok_evidence(1, ""))
}

fn developer_writes(scene: &str) -> FakeStep {
    FakeStep::new(Role::Developer).writing("scenes/main.tscn", scene)
}

fn developer_invocations(run: &GateRun) -> Vec<&InvocationRecord> {
    run.records
        .iter()
        .filter(|record| record.role == Role::Developer)
        .collect()
}

// ---------------------------------------------------------------------------
// ① the scene-structure validator produces an executable hint
// ---------------------------------------------------------------------------

#[test]
fn a_scene_without_a_root_node_is_rejected_with_an_executable_hint() {
    let report = validate_scene_structure(SCENE_WITHOUT_ROOT);
    assert!(!report.ok, "a scene without a root node must be rejected");
    let text = report.problems.join("\n");
    assert!(
        text.contains("line 3"),
        "the hint must name the offending line: {text}"
    );
    assert!(
        text.contains("parent=\".\""),
        "the hint must quote the current content: {text}"
    );
    assert!(
        text.to_lowercase().contains("correct form"),
        "the hint must state the correct form: {text}"
    );
    assert!(
        text.contains("[node name=\"Main\" type=\"Node2D\"]"),
        "the hint must show the root-node line to write: {text}"
    );
    assert!(
        text.contains("[node name=\"Main\" type=\"Node2D\"]"),
        "the hint must show the canonical root declaration"
    );
}

#[test]
fn a_well_formed_scene_passes_the_structure_check() {
    let report = validate_scene_structure(SCENE_WITH_ROOT);
    assert!(report.ok, "problems: {:?}", report.problems);
    assert!(report.problems.is_empty());
}

#[test]
fn a_child_without_a_parent_attribute_is_rejected() {
    let text = "[gd_scene format=3]\n\n[node name=\"Main\" type=\"Node2D\"]\n\n\
                [node name=\"Player\" type=\"CharacterBody2D\"]\n";
    let report = validate_scene_structure(text);
    assert!(!report.ok);
    let joined = report.problems.join("\n");
    assert!(joined.contains("line 5"), "{joined}");
    assert!(joined.to_lowercase().contains("parent="), "{joined}");
}

#[test]
fn a_parent_path_that_resolves_to_nothing_is_rejected() {
    let text = "[gd_scene format=3]\n\n[node name=\"Main\" type=\"Node2D\"]\n\n\
                [node name=\"Player\" type=\"CharacterBody2D\" parent=\"Nowhere\"]\n";
    let report = validate_scene_structure(text);
    assert!(!report.ok);
    let joined = report.problems.join("\n");
    assert!(joined.contains("line 5"), "{joined}");
    assert!(joined.contains("Nowhere"), "{joined}");
}

// ---------------------------------------------------------------------------
// ② both passes fail -> exactly one repair, then freeze with gate=false
// ---------------------------------------------------------------------------

#[tokio::test]
async fn a_broken_scene_triggers_exactly_one_targeted_repair() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let run = run_gate(
        root,
        vec![
            plan_step(),
            developer_writes(SCENE_WITHOUT_ROOT),
            developer_writes(SCENE_WITHOUT_ROOT), // the one repair call
            tester_step(),
        ],
    )
    .await;

    let developers = developer_invocations(&run);
    assert_eq!(
        developers.len(),
        2,
        "DR-24 allows exactly one repair call: {:?}",
        run.records.iter().map(|r| r.role).collect::<Vec<_>>()
    );

    let repair = developers[1];
    let context = repair
        .retry_context
        .as_deref()
        .expect("the repair call must carry a retry_context");
    assert!(
        context.contains("editor_errors_baseline") && context.contains("play_scene_ready"),
        "the retry context must name the failed gate steps: {context}"
    );
    assert!(
        context.contains("-32603") || context.contains("Invalid scene"),
        "the retry context must carry the verbatim engine/JSON-RPC error: {context}"
    );
    assert!(
        context.to_lowercase().contains("line ") && context.to_lowercase().contains("correct form"),
        "the retry context must carry the scene-structure hint: {context}"
    );
    assert!(
        context.contains("launchable"),
        "the retry context must state that only launchability may be fixed: {context}"
    );
    assert!(
        repair.limits.contains("step_limit: 60"),
        "the repair budget is agent.repair_steps (60): {}",
        repair.limits
    );

    // Both batteries are recorded, the gate stays false, and the round still
    // advances (the freeze happened).
    assert_eq!(run.result["repair_retry_used"], json!(true));
    assert_eq!(run.result["artifact_gate"]["applicable"], json!(true));
    assert_eq!(run.result["artifact_gate"]["launchable"], json!(false));
    let reasons = run.result["artifact_gate"]["reasons"]
        .as_array()
        .expect("reasons");
    assert!(
        reasons.iter().any(|reason| reason
            .as_str()
            .unwrap_or("")
            .contains("editor_errors_baseline")),
        "reasons must quote the failed steps: {reasons:?}"
    );
    let passes = run.result["battery_passes"].as_array().expect("passes");
    assert_eq!(passes.len(), 2, "both battery passes must be recorded");
    assert_eq!(passes[0]["launchable"], json!(false));
    assert_eq!(passes[1]["launchable"], json!(false));
    assert!(run.result["candidate_id"].as_str().is_some());
    assert!(
        run.run_dir.join("iter-1/candidate").is_dir(),
        "the candidate view must still be built"
    );

    // The scene-structure step is the actionable half of the failure: the
    // battery record itself must carry the line number and the correct form.
    let battery: Vec<Value> = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/battery.json"),
    ))
    .unwrap();
    let structure = battery
        .iter()
        .find(|record| record["step_id"] == json!("scene_structure"))
        .expect("the scene_structure step must exist");
    assert_eq!(structure["ok"], json!(false));
    let observation = structure["record"]["observation"].as_str().unwrap();
    assert!(observation.contains("line 3"), "{observation}");
    assert!(
        observation.to_lowercase().contains("correct form"),
        "{observation}"
    );
    assert!(
        structure["supports"]
            .as_array()
            .unwrap()
            .iter()
            .any(|id| id == "N1"),
        "the structure step supports N1: {structure}"
    );
}

// ---------------------------------------------------------------------------
// ③ a successful repair freezes normally with gate=true
// ---------------------------------------------------------------------------

#[tokio::test]
async fn a_successful_repair_freezes_with_the_gate_open() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let run = run_gate(
        root,
        vec![
            plan_step(),
            developer_writes(SCENE_WITHOUT_ROOT),
            developer_writes(SCENE_WITH_ROOT), // the targeted repair
            tester_step(),
        ],
    )
    .await;

    assert_eq!(developer_invocations(&run).len(), 2);
    assert_eq!(run.result["artifact_gate"]["launchable"], json!(true));
    assert_eq!(run.result["repair_retry_used"], json!(true));
    let passes = run.result["battery_passes"].as_array().unwrap();
    assert_eq!(passes.len(), 2);
    assert_eq!(passes[0]["launchable"], json!(false));
    assert_eq!(passes[1]["launchable"], json!(true));
    // The frozen A_t contains the repaired scene.
    assert!(validate_scene_structure(&read(&run.workspace.join("scenes/main.tscn"))).ok);
}

// ---------------------------------------------------------------------------
// ④ an always-true gate never repairs
// ---------------------------------------------------------------------------

#[tokio::test]
async fn a_launchable_project_never_invokes_a_repair() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let run = run_gate(
        root,
        vec![
            plan_step(),
            developer_writes(SCENE_WITH_ROOT),
            tester_step(), // never consumed if no repair happens
        ],
    )
    .await;

    assert_eq!(
        run.records.iter().map(|r| r.role).collect::<Vec<_>>(),
        vec![Role::Planner, Role::Developer, Role::Tester]
    );
    assert_eq!(run.result["artifact_gate"]["launchable"], json!(true));
    assert_eq!(run.result["repair_retry_used"], json!(false));
    assert_eq!(run.result["battery_passes"].as_array().unwrap().len(), 1);
}
