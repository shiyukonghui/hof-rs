//! DR-24 — the pre-freeze "launchable" gate and the one-shot targeted repair.
//!
//! The second real smoke run completed the whole loop with a legal `E_1` while
//! `scenes/main.tscn` had **no root node** (`Invalid scene`), so `editor_play_scene`
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

/// DR-79 ③: the same scene **plus** a non-empty entry script, which is the extra
/// condition `GodotAdapter::developer_artifact_valid` puts on "a usable
/// artifact" (`wrap_up_budget.rs`'s `VALID_DEV_SCENE`, kept local here because
/// that file's constant is private to it).
const SCENE_WITH_ENTRY_SCRIPT: &str = "[gd_scene load_steps=2 format=3]\n\n\
[ext_resource type=\"Script\" path=\"res://scripts/player.gd\" id=\"1\"]\n\n\
[node name=\"Main\" type=\"Node2D\"]\n\
script = ExtResource(\"1\")\n";

// ---------------------------------------------------------------------------
// A scripted channel that answers from the scene really present on disk
// ---------------------------------------------------------------------------

/// DR-48: the two informational `[MCP]` startup banners, **verbatim** — they are
/// byte-identical to the engine's own literals
/// (`godot-mcp/godot/modules/mcp_server/mcp_server.cpp:605` and `:645`) and to
/// what the `smoke-t6` round's log carried.
const ENGINE_TRACE_BANNER: &str =
    "[MCP] trace=off (default; use --mcp-trace=<path> or godot_mcp/trace_file to enable)";
const ENGINE_CAPTURE_BANNER: &str = "[MCP] capture=off (default; use --mcp-capture=on_error|every_call together with --mcp-trace=<path>)";

/// DR-48: the genuine engine error the exemption must **never** swallow.  It
/// carries the `[MCP]` prefix and is a real ERROR line.
const ENGINE_MCP_ERROR: &str =
    "ERROR: [MCP] SceneTree never became available; MCP server disabled.";

struct GateChannel {
    workspace: PathBuf,
    calls: Mutex<Vec<(String, Value)>>,
    /// DR-48: an `editor_get_errors` payload answered verbatim instead of the
    /// scene-derived one.
    editor_errors: Option<Value>,
    /// DR-81 ②: the **window anchor** reading — the log tail as it stood before
    /// the project reload.  `None` models "the anchor window was empty", which is
    /// the pre-existing behaviour every earlier test relied on.
    editor_errors_anchor: Option<Value>,
    /// DR-51: the game endpoint registrations, and whether the battery has
    /// already invalidated the route (`editor_stop_scene`).
    registrations: Mutex<Vec<hof_rs::tools::endpoint::GameEndpointRecord>>,
    route_cleared: std::sync::atomic::AtomicBool,
}

impl GateChannel {
    fn new(workspace: &Path) -> Self {
        Self {
            workspace: workspace.to_path_buf(),
            calls: Mutex::new(Vec::new()),
            editor_errors: None,
            editor_errors_anchor: None,
            registrations: Mutex::new(Vec::new()),
            route_cleared: std::sync::atomic::AtomicBool::new(false),
        }
    }

    /// DR-48: answer `editor_get_errors` with `errors` verbatim.
    fn with_editor_errors(workspace: &Path, errors: &[&str]) -> Self {
        Self {
            workspace: workspace.to_path_buf(),
            calls: Mutex::new(Vec::new()),
            editor_errors: Some(
                json!({"available": true, "count": errors.len(), "errors": errors}),
            ),
            // DR-81 ②: the window anchor stands **before** the reload, so the
            // configured errors are new in this window.
            editor_errors_anchor: Some(json!({"available": true, "count": 0, "errors": []})),
            registrations: Mutex::new(Vec::new()),
            route_cleared: std::sync::atomic::AtomicBool::new(false),
        }
    }

    /// DR-81 ②: a channel whose **anchor** and **judged** readings are both
    /// scripted, so "the same line was already in the log tail before this
    /// window" can be reproduced.
    fn with_windowed_editor_errors(workspace: &Path, anchor: &[&str], judged: &[&str]) -> Self {
        Self {
            workspace: workspace.to_path_buf(),
            calls: Mutex::new(Vec::new()),
            editor_errors: Some(
                json!({"available": true, "count": judged.len(), "errors": judged}),
            ),
            editor_errors_anchor: Some(
                json!({"available": true, "count": anchor.len(), "errors": anchor}),
            ),
            registrations: Mutex::new(Vec::new()),
            route_cleared: std::sync::atomic::AtomicBool::new(false),
        }
    }

    /// DR-51: did the battery's `editor_stop_scene` step clear the route?
    fn route_cleared(&self) -> bool {
        self.route_cleared.load(std::sync::atomic::Ordering::SeqCst)
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
            "editor_rescan_project_filesystem" => json!({"reloaded": true}),
            "editor_open_scene" => {
                json!({"opened": args.get("path").cloned().unwrap_or(Value::Null)})
            }
            "project_read_scene_file_content" => match self.scene_text() {
                Some(text) => json!({"path": args["path"], "content": text}),
                None => {
                    return Err(
                        McpError::new(-32603, "场景文件不存在: res://scenes/main.tscn").into(),
                    )
                }
            },
            "editor_get_errors" => {
                // DR-81 ②: the battery reads the log tail twice — a wide anchor
                // before the reload and the judged reading (`max_lines: 50`)
                // after it.  The double answers each from its own script.
                let anchor_call = args
                    .get("max_lines")
                    .and_then(Value::as_u64)
                    .map(|lines| lines > 50)
                    .unwrap_or(false);
                let configured = if anchor_call {
                    &self.editor_errors_anchor
                } else {
                    &self.editor_errors
                };
                if let Some(payload) = configured {
                    payload.clone()
                } else if self.scene_valid() {
                    json!({"errors": []})
                } else {
                    return Err(McpError::new(
                        -32603,
                        "Invalid scene: root node Ground cannot specify a parent node",
                    )
                    .into());
                }
            }
            // DR-43: `editor_play_scene` announces the game endpoint it created.
            // This double plays both channels, so it announces a port that the
            // registration records while the double keeps answering itself.
            "editor_play_scene" => {
                json!({"playing": true, "mcp_port": 9878, "mcp_port_source": "auto_free_port"})
            }
            "running_game_get_scene_tree" => {
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

    /// DR-51: the route is what `running_game_*` calls use, and the battery's
    /// `editor_stop_scene` clears it.
    async fn register_game_endpoint(
        &self,
        record: hof_rs::tools::endpoint::GameEndpointRecord,
    ) -> anyhow::Result<()> {
        self.registrations.lock().unwrap().push(record);
        self.route_cleared
            .store(false, std::sync::atomic::Ordering::SeqCst);
        Ok(())
    }

    /// DR-71 ①: the battery now installs the announced endpoint for in-process
    /// routing and publishes it only after the readiness poll, so the identity
    /// DR-51 captures is recorded here.  The DR-51 assertions are unchanged.
    async fn install_game_endpoint(
        &self,
        record: hof_rs::tools::endpoint::GameEndpointRecord,
    ) -> anyhow::Result<()> {
        self.registrations.lock().unwrap().push(record);
        self.route_cleared
            .store(false, std::sync::atomic::Ordering::SeqCst);
        Ok(())
    }

    async fn clear_game_endpoint(&self) {
        self.route_cleared
            .store(true, std::sync::atomic::Ordering::SeqCst);
    }

    async fn game_endpoint(&self) -> Option<hof_rs::tools::endpoint::GameEndpointRecord> {
        if self.route_cleared() {
            return None;
        }
        self.registrations.lock().unwrap().last().cloned()
    }

    async fn game_endpoint_history(&self) -> Option<hof_rs::tools::endpoint::GameEndpointRecord> {
        self.registrations.lock().unwrap().last().cloned()
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
    /// DR-51: the tool double, so a test can see what `editor_stop_scene` did.
    channel: Arc<GateChannel>,
}

fn adapter(_root: &Path) -> GodotAdapter {
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
    run_gate_with_errors(root, script, None).await
}

/// DR-48: the same run, with `editor_get_errors` answered from a fixed payload.
async fn run_gate_with_errors(
    root: &Path,
    script: Vec<FakeStep>,
    editor_errors: Option<Vec<&str>>,
) -> GateRun {
    run_gate_with_window(root, script, None, editor_errors).await
}

/// DR-81 ②: the same run with **both** editor-log readings scripted — the anchor
/// (before the reload) and the judged reading (after it).
async fn run_gate_with_window(
    root: &Path,
    script: Vec<FakeStep>,
    anchor: Option<Vec<&str>>,
    judged: Option<Vec<&str>>,
) -> GateRun {
    let mut cfg: HohConfig = test_config(root, 1);
    cfg.runtime.spec = root.join("spec.md");
    let spec = write_spec(root);
    let harness = FakeHarness::new(script);
    let observer = harness.clone();
    let workspace = cfg.runtime.workspace.clone();
    let run_dir = cfg.runtime.runs_dir.join("run-1");
    let channel = Arc::new(match (&anchor, &judged) {
        (Some(anchor), Some(judged)) => {
            GateChannel::with_windowed_editor_errors(&workspace, anchor, judged)
        }
        (None, Some(judged)) => GateChannel::with_editor_errors(&workspace, judged),
        _ => GateChannel::new(&workspace),
    });
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
        channel,
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
// ③b the repair attempt's `artifact_valid` is measured again, not assumed
// ---------------------------------------------------------------------------

/// The developer attempt whose number is `attempt`, as the result recorded it.
fn developer_attempt_artifact_valid(run: &GateRun, attempt: u32) -> Option<bool> {
    run.result["attempts"]
        .as_array()?
        .iter()
        .find(|entry| entry["role"] == json!("developer") && entry["attempt"] == json!(attempt))
        .and_then(|entry| entry["artifact_valid"].as_bool())
}

/// DR-79 ③: the targeted repair's `artifact_valid` must be the adapter's real
/// answer for the repaired workspace.
///
/// The repair block used to record `artifact_valid: workspace.is_dir()` — an
/// always-true check — so `smoke-t13`'s attempt 2 reported `true` whatever the
/// repair had done to the project, and a repair that *broke* the scene would
/// have looked exactly like one that fixed it.  Both directions are pinned here,
/// so neither "always true" nor "always false" can pass.
#[tokio::test]
async fn the_repair_attempt_artifact_validity_is_measured_not_assumed() {
    // (a) the repair leaves the scene broken: the flag must be false.
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let broken = run_gate(
        root,
        vec![
            plan_step(),
            developer_writes(SCENE_WITHOUT_ROOT),
            developer_writes(SCENE_WITHOUT_ROOT), // the repair changes nothing usable
            tester_step(),
        ],
    )
    .await;
    assert_eq!(broken.result["repair_retry_used"], json!(true));
    assert_eq!(
        developer_attempt_artifact_valid(&broken, 1),
        Some(false),
        "attempt 1 left the scene invalid"
    );
    assert_eq!(
        developer_attempt_artifact_valid(&broken, 2),
        Some(false),
        "a repair that leaves the scene invalid must not be recorded as a valid artifact: {:?}",
        broken.result["attempts"]
    );

    // (b) the counter-direction: the same field is true when the repair really
    // produced a usable scene, so the fix cannot pass by hardcoding `false`.
    // `SCENE_WITH_ENTRY_SCRIPT` is launchable *and* references a non-empty entry
    // script, which is what `developer_artifact_valid` asks for.
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let repaired = run_gate(
        root,
        vec![
            plan_step(),
            developer_writes(SCENE_WITHOUT_ROOT),
            developer_writes_scene_and_player(SCENE_WITH_ENTRY_SCRIPT, "extends Node2D\n"),
            tester_step(),
        ],
    )
    .await;
    assert_eq!(repaired.result["repair_retry_used"], json!(true));
    assert_eq!(
        developer_attempt_artifact_valid(&repaired, 2),
        Some(true),
        "a repair that produced a usable scene must be recorded as valid: {:?}",
        repaired.result["attempts"]
    );
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

// ---------------------------------------------------------------------------
// ⑤ DR-51 — the endpoint facts must reach `meta.json`
// ---------------------------------------------------------------------------

/// DR-51: `smoke-t6`'s `meta.json.engine.mcp.game_endpoint` was structurally
/// always `null`: the battery registered the endpoint, then its own
/// `editor_stop_scene` step cleared the registration, and only afterwards did
/// the run loop look at it.  The endpoint is now captured when it is registered
/// and persisted even though the route is gone.
#[tokio::test]
async fn the_run_meta_keeps_the_game_endpoint_the_battery_registered() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let run = run_gate(
        root,
        vec![
            plan_step(),
            developer_writes(SCENE_WITH_ROOT),
            tester_step(),
        ],
    )
    .await;

    assert!(
        run.channel.route_cleared(),
        "the battery must have run editor_stop_scene (the condition that used to erase the field)"
    );
    assert!(
        run.channel.game_endpoint().await.is_none(),
        "the route itself must be gone (DR-43)"
    );

    let meta: Value = serde_json::from_str(&read(&run.run_dir.join("meta.json"))).unwrap();
    let endpoint = &meta["engine"]["mcp"]["game_endpoint"];
    assert_eq!(
        endpoint["endpoint"],
        json!("http://127.0.0.1:9878/mcp"),
        "the announced game endpoint must be recorded (DR-51): {meta}"
    );
    assert_eq!(endpoint["port"], json!(9878));
    assert_eq!(endpoint["source"], json!("auto_free_port"));
    assert_eq!(
        meta["engine"]["mcp"]["game_endpoint_reason"],
        json!(null),
        "a known endpoint has no reason: {meta}"
    );

    // DR-51: this adapter declares no engine binary, so no `GET /mcp` is
    // attempted at all and the null+reason contract still holds for the status.
    assert_eq!(meta["engine"]["mcp"]["editor_status"], json!(null));
    assert!(meta["engine"]["mcp"]["editor_status_reason"].is_string());
}

// ---------------------------------------------------------------------------
// ⑥ DR-48 — the engine's own INFO banners must not close the gate
// ---------------------------------------------------------------------------

/// DR-48: `smoke-t6` closed the gate on the engine's informational banner
/// (`[MCP] capture=off (…on_error…)`), because the **engine** classifies a log
/// line as an error with a case-insensitive `contains("ERROR")`
/// (`editor_read_scene_inspector.cpp:249`) and `on_error` matches.  The editor
/// was in fact clean: the same round booted the scene and answered
/// `running_game_get_scene_tree` with 50 nodes.
#[tokio::test]
async fn an_engine_info_banner_does_not_close_the_gate() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let run = run_gate_with_errors(
        root,
        vec![
            plan_step(),
            developer_writes(SCENE_WITH_ROOT),
            tester_step(), // never consumed: no repair may be triggered
        ],
        Some(vec![ENGINE_CAPTURE_BANNER, ENGINE_TRACE_BANNER]),
    )
    .await;

    assert_eq!(
        run.result["artifact_gate"]["launchable"],
        json!(true),
        "the engine's own INFO banner is not an editor error (DR-48): {:?}",
        run.result["artifact_gate"]["reasons"]
    );
    assert_eq!(
        run.result["repair_retry_used"],
        json!(false),
        "an exempted banner must never burn the repair budget (DR-48)"
    );
    assert_eq!(
        run.records.iter().map(|r| r.role).collect::<Vec<_>>(),
        vec![Role::Planner, Role::Developer, Role::Tester]
    );

    // The raw payload is still recorded verbatim: the exemption changes the
    // verdict, never the evidence.
    let battery: Vec<Value> = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/battery.json"),
    ))
    .unwrap();
    let baseline = battery
        .iter()
        .find(|record| record["step_id"] == json!("editor_errors_baseline"))
        .expect("the baseline step must exist");
    assert_eq!(baseline["ok"], json!(true));
    let observation = baseline["record"]["observation"].as_str().unwrap();
    assert!(
        observation.contains("capture=off"),
        "the observation must carry the verbatim banner: {observation}"
    );
    let raw: Value = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/raw/editor_errors_baseline.json"),
    ))
    .unwrap();
    assert_eq!(raw["calls"][0]["ok"], json!(true));
    assert!(
        raw["calls"][0]["payload"]
            .to_string()
            .contains("capture=off"),
        "the raw record must keep the payload: {raw}"
    );
}

/// DR-48 counterexample ①: a real `ERROR:` line still closes the gate.
#[tokio::test]
async fn a_real_editor_error_still_closes_the_gate() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let run = run_gate_with_errors(
        root,
        vec![
            plan_step(),
            developer_writes(SCENE_WITH_ROOT),
            developer_writes(SCENE_WITH_ROOT), // the one targeted repair
            tester_step(),
        ],
        Some(vec![
            ENGINE_CAPTURE_BANNER,
            r#"ERROR: res://scripts/main.gd:1 - Parse Error: Unexpected identifier "using" in class body."#,
        ]),
    )
    .await;

    assert_eq!(
        run.result["artifact_gate"]["launchable"],
        json!(false),
        "a real ERROR line must still close the gate (DR-48)"
    );
    assert_eq!(run.result["repair_retry_used"], json!(true));
    let reasons = run.result["artifact_gate"]["reasons"].as_array().unwrap();
    assert!(
        reasons
            .iter()
            .any(|reason| reason.as_str().unwrap_or("").contains("Parse Error")),
        "the reason must carry the surviving error: {reasons:?}"
    );
}

/// DR-48 counterexample ②: the engine also prints an `ERROR:` line **with** the
/// `[MCP]` prefix (`mcp_server.cpp`, "SceneTree never became available").  A
/// `[MCP]`-prefix whitelist would swallow it; the exact-banner rule must not.
#[tokio::test]
async fn an_error_carrying_the_mcp_prefix_still_closes_the_gate() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let run = run_gate_with_errors(
        root,
        vec![
            plan_step(),
            developer_writes(SCENE_WITH_ROOT),
            developer_writes(SCENE_WITH_ROOT),
            tester_step(),
        ],
        Some(vec![ENGINE_MCP_ERROR]),
    )
    .await;

    assert_eq!(
        run.result["artifact_gate"]["launchable"],
        json!(false),
        "`ERROR: [MCP] …` is a real error; only the exact INFO banner is exempt (DR-48)"
    );
    let reasons = run.result["artifact_gate"]["reasons"].as_array().unwrap();
    assert!(
        reasons.iter().any(|reason| reason
            .as_str()
            .unwrap_or("")
            .contains("SceneTree never became available")),
        "the reason must quote the real error: {reasons:?}"
    );
}

/// DR-48 counterexample ③: a `[MCP]`-prefixed line that is **not** one of the
/// known banners is not exempt either (no prefix rule, and no shape guessing).
#[tokio::test]
async fn an_unknown_mcp_prefixed_line_still_closes_the_gate() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let run = run_gate_with_errors(
        root,
        vec![
            plan_step(),
            developer_writes(SCENE_WITH_ROOT),
            developer_writes(SCENE_WITH_ROOT),
            tester_step(),
        ],
        Some(vec!["[MCP] capture=off"]),
    )
    .await;

    assert_eq!(
        run.result["artifact_gate"]["launchable"],
        json!(false),
        "a truncated/unknown `[MCP]` line is not the known banner: fail closed (DR-48)"
    );
}

// ---------------------------------------------------------------------------
// ⑦ DR-68 ② — the launch gate may not be closed by a stale editor log line
// ---------------------------------------------------------------------------

/// The line `smoke-t8` read at 07:19:33 — naming `_update_facing_visual`, which
/// exists in **neither** `A_0` nor `A_1` of the round.
const STALE_PLAYER_ERROR: &str = r#"ERROR: res://scripts/player.gd:31 - Parse Error: Function "_update_facing_visual()" not found in base self."#;

/// A `player.gd` whose **line 31** is `body`, padded with real-looking lines, so
/// the fixtures can name the same `res://…:31` position the real log did.
fn player_gd_line_31(body: &str) -> String {
    let mut text = String::from("extends CharacterBody2D\n\n");
    while text.lines().count() < 30 {
        text.push_str("\tpass\n");
    }
    text.push_str(body);
    text.push('\n');
    assert_eq!(text.lines().count(), 31, "the fixture must have 31 lines");
    text
}

fn developer_writes_scene_and_player(scene: &str, player: &str) -> FakeStep {
    FakeStep::new(Role::Developer)
        .writing("scenes/main.tscn", scene)
        .writing("scripts/player.gd", player)
}

/// `smoke-t8`: the editor's **append-only log** still carried a parse error for
/// `player.gd:31` twelve minutes after the file had been rewritten, so the gate
/// closed, DR-24 spent a 60-step repair (4.02M tokens, 11m24s) and the repair
/// wrote nothing.  The line the log quoted is no longer the line the file has,
/// so the current project cannot reproduce the error.
#[tokio::test]
async fn a_stale_editor_log_line_does_not_close_the_gate() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let run = run_gate_with_errors(
        root,
        vec![
            plan_step(),
            developer_writes_scene_and_player(
                SCENE_WITH_ROOT,
                &player_gd_line_31("\t_apply_facing_visual()"),
            ),
            // Never consumed: no repair may be triggered by log residue.
            tester_step(),
        ],
        Some(vec![STALE_PLAYER_ERROR]),
    )
    .await;

    assert_eq!(
        run.result["artifact_gate"]["launchable"],
        json!(true),
        "the current project cannot produce this error, so it must not close the gate: {:?}",
        run.result["artifact_gate"]["reasons"]
    );
    assert_eq!(
        run.result["repair_retry_used"],
        json!(false),
        "log residue must never burn the one repair retry"
    );
    assert_eq!(
        run.records.iter().map(|r| r.role).collect::<Vec<_>>(),
        vec![Role::Planner, Role::Developer, Role::Tester],
        "no second Developer call may be triggered by a stale line"
    );

    // The raw payload keeps the line verbatim: the verdict changes, not the
    // evidence — and the observation says what was dismissed.
    let battery: Vec<Value> = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/battery.json"),
    ))
    .unwrap();
    let baseline = battery
        .iter()
        .find(|record| record["step_id"] == json!("editor_errors_baseline"))
        .expect("the baseline step must exist");
    assert_eq!(baseline["ok"], json!(true));
    let observation = baseline["record"]["observation"].as_str().unwrap();
    assert!(
        observation.contains("_update_facing_visual"),
        "the dismissed line must stay verbatim in the observation: {observation}"
    );
    assert!(
        observation.contains("stale"),
        "the observation must say the line was dismissed as not reproducible: {observation}"
    );
}

/// The reverse control: the same call, the same file, and the log line names the
/// symbol that really is on line 31 — i.e. the error describes the current bytes
/// (a call to a function the file never defines).  It must still close the gate.
#[tokio::test]
async fn a_reproducible_parse_error_still_closes_the_gate() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let run = run_gate_with_errors(
        root,
        vec![
            plan_step(),
            developer_writes_scene_and_player(
                SCENE_WITH_ROOT,
                &player_gd_line_31("\t_missing_from_this_file()"),
            ),
            developer_writes_scene_and_player(
                SCENE_WITH_ROOT,
                &player_gd_line_31("\t_missing_from_this_file()"),
            ),
            tester_step(),
        ],
        Some(vec![
            r#"ERROR: res://scripts/player.gd:31 - Parse Error: Function "_missing_from_this_file()" not found in base self."#,
        ]),
    )
    .await;

    assert_eq!(
        run.result["artifact_gate"]["launchable"],
        json!(false),
        "a log line the current bytes still reproduce must close the gate: {:?}",
        run.result["artifact_gate"]["reasons"]
    );
    assert_eq!(
        run.result["repair_retry_used"],
        json!(true),
        "a reproducible parse error must still trigger the one targeted repair"
    );
}

// ---------------------------------------------------------------------------
// ⑧ DR-81 ① — an editor *infrastructure* failure is not a project defect
// ---------------------------------------------------------------------------

/// `smoke-t14`'s one surviving line, verbatim: the editor could not write its
/// own cache file after `--fresh-workspace` removed the `.godot` directory it had
/// open.  It names no file in the produced project.
const CACHE_WRITE_ERROR: &str = "ERROR: Cannot create file \
    'res://.godot/editor/filesystem_cache10'. Check user write permissions.";

/// A genuine script defect, in the same `ERROR: res://…` shape.  It must never be
/// exempted by the infrastructure rule.
const NEW_SCRIPT_ERROR: &str = r#"ERROR: res://scripts/main.gd:12 - Parse Error: Unexpected identifier "using" in class body."#;

/// A line that was already in the editor's append-only log **before** this
/// window's anchor, in the shape the editor really writes for a parse error
/// (`main.gd:8`, the `smoke-t14` pass-1 error).  It carries no `Function "X()"`
/// symbol, so DR-68's staleness rule keeps it — only the time window can
/// distinguish it from an error the candidate produced.
const OLD_LOG_TAIL_ERROR: &str =
    r#"ERROR: res://scripts/main.gd:8 - Parse Error: Expected new line after "\"."#;

/// The `editor_errors_baseline` observation recorded in the frozen candidate.
fn baseline_observation(run: &GateRun) -> String {
    let battery: Vec<Value> = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/battery.json"),
    ))
    .unwrap();
    battery
        .iter()
        .find(|record| record["step_id"] == json!("editor_errors_baseline"))
        .expect("the baseline step must exist")["record"]["observation"]
        .as_str()
        .expect("an observation string")
        .to_string()
}

/// DR-81 ①: the cache-write failure `smoke-t14` froze on is the editor's own
/// infrastructure, not a defect of the produced project.  The two mandatory gate
/// steps disagreed (the project booted and answered 22 nodes while the editor log
/// carried this one line), and the whole round was frozen `launchable=false` and
/// exited 6.  The exemption is **additive**: it is a named classification of the
/// text, not a loosening of the predicate.
#[tokio::test]
async fn an_editor_infrastructure_failure_does_not_close_the_gate() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let run = run_gate_with_errors(
        root,
        vec![
            plan_step(),
            developer_writes(SCENE_WITH_ROOT),
            tester_step(), // never consumed: infrastructure noise may not repair
        ],
        Some(vec![CACHE_WRITE_ERROR]),
    )
    .await;

    assert_eq!(
        run.result["artifact_gate"]["launchable"],
        json!(true),
        "an editor cache-write failure is not a project defect: {:?}",
        run.result["artifact_gate"]["reasons"]
    );
    assert_eq!(
        run.result["repair_retry_used"],
        json!(false),
        "infrastructure noise must never burn the one repair retry"
    );
    assert_eq!(
        run.records.iter().map(|r| r.role).collect::<Vec<_>>(),
        vec![Role::Planner, Role::Developer, Role::Tester]
    );

    // The verdict changes; the evidence does not.  Both the verbatim line and the
    // classification token are recorded, so the distinction is auditable.
    let observation = baseline_observation(&run);
    assert!(
        observation.contains("filesystem_cache10"),
        "the verbatim line must survive the exemption: {observation}"
    );
    assert!(
        observation.contains("editor_infrastructure_failures=1"),
        "the classification must be recorded as its own token: {observation}"
    );
    assert!(
        observation.contains("project_defects_new=0"),
        "no project defect may be claimed: {observation}"
    );
    let raw: Value = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/raw/editor_errors_baseline.json"),
    ))
    .unwrap();
    assert!(
        raw.to_string().contains("filesystem_cache10"),
        "the raw payload must keep the line verbatim: {raw}"
    );
    let battery: Vec<Value> = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/battery.json"),
    ))
    .unwrap();
    let baseline = battery
        .iter()
        .find(|record| record["step_id"] == json!("editor_errors_baseline"))
        .unwrap();
    assert_eq!(baseline["ok"], json!(true));
}

/// DR-81 ① counter-direction: exempting the editor's infrastructure must never
/// swallow a real script error.  `smoke-t14` pass 1 carried
/// `res://scripts/main.gd:8 - Parse Error` and only the one-shot repair removed
/// it, so this is the regression pin DR-48's blunt predicate used to hold.
#[tokio::test]
async fn an_infrastructure_failure_does_not_mask_a_real_script_error() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let run = run_gate_with_errors(
        root,
        vec![
            plan_step(),
            developer_writes(SCENE_WITH_ROOT),
            developer_writes(SCENE_WITH_ROOT), // the one targeted repair
            tester_step(),
        ],
        Some(vec![NEW_SCRIPT_ERROR, CACHE_WRITE_ERROR]),
    )
    .await;

    assert_eq!(
        run.result["artifact_gate"]["launchable"],
        json!(false),
        "a real parse error must still close the gate: {:?}",
        run.result["artifact_gate"]["reasons"]
    );
    assert_eq!(run.result["repair_retry_used"], json!(true));
    let reasons = run.result["artifact_gate"]["reasons"].as_array().unwrap();
    assert!(
        reasons
            .iter()
            .any(|reason| reason.as_str().unwrap_or("").contains("Parse Error")),
        "the reason must quote the surviving script error: {reasons:?}"
    );
    let observation = baseline_observation(&run);
    assert!(
        observation.contains("editor_infrastructure_failures=1"),
        "{observation}"
    );
    assert!(
        observation.contains("project_defects_new=1"),
        "{observation}"
    );
}

/// DR-81 ① boundary: a line that merely mentions `.godot` is **not** exempt
/// unless it also carries the editor's cache/write-failure wording.  This keeps
/// the rule a named classification instead of a namespace wildcard.
#[test]
fn the_infrastructure_classifier_is_narrow() {
    use hof_rs::adapter::godot::editor_error_is_infrastructure;
    assert!(editor_error_is_infrastructure(CACHE_WRITE_ERROR));
    assert!(!editor_error_is_infrastructure(NEW_SCRIPT_ERROR));
    assert!(!editor_error_is_infrastructure(OLD_LOG_TAIL_ERROR));
    // The engine's real error under the `[MCP]` prefix is not infrastructure.
    assert!(!editor_error_is_infrastructure(
        "ERROR: [MCP] SceneTree never became available; MCP server disabled."
    ));
    // A `.godot` mention without failure wording is not an infrastructure error.
    assert!(!editor_error_is_infrastructure(
        "ERROR: res://.godot/editor/filesystem_cache10 is stale."
    ));
    // The failure wording without the editor's own namespace is not either.
    assert!(!editor_error_is_infrastructure(
        "ERROR: Cannot create file 'res://scripts/main.gd'. Check user write permissions."
    ));
}

// ---------------------------------------------------------------------------
// ⑨ DR-81 ② — a log-tail reading is not a hard verdict; the window is
// ---------------------------------------------------------------------------

/// DR-81 ②: the editor's log is append-only, so a line that was already there
/// **before this window's anchor** describes an older state, not the candidate.
/// `smoke-t14` measured the instability directly: the same `editor_get_errors`
/// call returned this class of line at the freeze and a non-error `[MCP]` line
/// 48 minutes later.
#[tokio::test]
async fn an_old_editor_log_line_outside_the_window_does_not_close_the_gate() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let run = run_gate_with_window(
        root,
        vec![
            plan_step(),
            developer_writes(SCENE_WITH_ROOT),
            tester_step(), // never consumed: log residue may not repair
        ],
        Some(vec![OLD_LOG_TAIL_ERROR]),
        Some(vec![OLD_LOG_TAIL_ERROR]),
    )
    .await;

    assert_eq!(
        run.result["artifact_gate"]["launchable"],
        json!(true),
        "a line already present before the window anchor is not a verdict on the project: {:?}",
        run.result["artifact_gate"]["reasons"]
    );
    assert_eq!(
        run.result["repair_retry_used"],
        json!(false),
        "pre-existing log residue must never burn the one repair retry"
    );
    assert_eq!(
        run.records.iter().map(|r| r.role).collect::<Vec<_>>(),
        vec![Role::Planner, Role::Developer, Role::Tester]
    );

    let observation = baseline_observation(&run);
    assert!(
        observation.contains("project_defects_new=0"),
        "the window criterion must be recorded as its own token: {observation}"
    );
    assert!(
        observation.contains("pre-existing"),
        "the dismissal must name its reason: {observation}"
    );
    assert!(
        observation.contains("main.gd:8"),
        "the dismissed line stays verbatim in the observation: {observation}"
    );
    // The criterion and the window it used are recorded next to the evidence
    // (in the raw document's generic `channel` slot, the same one DR-35 uses).
    let raw: Value = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/raw/editor_errors_baseline.json"),
    ))
    .unwrap();
    let window = &raw["channel"]["editor_error_window"];
    assert!(
        window["criterion"].is_string(),
        "the raw record must state the window criterion: {raw}"
    );
    assert!(
        window["anchor"]
            .as_str()
            .unwrap_or("")
            .contains("project_reload_and_open"),
        "the raw record must state when the anchor was taken: {raw}"
    );
    assert_eq!(window["pre_existing_lines"], json!(1));
}

/// DR-81 ② counter-direction: an error that is **new since the anchor** is the
/// candidate's, and it must still close the gate and trigger the repair.
#[tokio::test]
async fn a_real_script_error_new_in_the_window_still_closes_the_gate() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let run = run_gate_with_window(
        root,
        vec![
            plan_step(),
            developer_writes(SCENE_WITH_ROOT),
            developer_writes(SCENE_WITH_ROOT), // the one targeted repair
            tester_step(),
        ],
        Some(vec![OLD_LOG_TAIL_ERROR]),
        Some(vec![OLD_LOG_TAIL_ERROR, NEW_SCRIPT_ERROR]),
    )
    .await;

    assert_eq!(
        run.result["artifact_gate"]["launchable"],
        json!(false),
        "an error that appeared after the anchor is the candidate's: {:?}",
        run.result["artifact_gate"]["reasons"]
    );
    assert_eq!(
        run.result["repair_retry_used"],
        json!(true),
        "a new error must still trigger the one targeted repair"
    );
    let reasons = run.result["artifact_gate"]["reasons"].as_array().unwrap();
    assert!(
        reasons
            .iter()
            .any(|reason| reason.as_str().unwrap_or("").contains("main.gd:12")),
        "the reason must quote the new error: {reasons:?}"
    );
    let observation = baseline_observation(&run);
    assert!(
        observation.contains("project_defects_new=1"),
        "{observation}"
    );
    assert!(
        observation.contains("pre-existing"),
        "the pre-existing line must be distinguished from the new one: {observation}"
    );
}
