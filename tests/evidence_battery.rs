//! DR-17 — the deterministic evidence battery.
//!
//! The battery moves evidence *collection* from the Tester into the runtime:
//! before `A_t` is frozen, the adapter drives the real workspace through a
//! fixed sequence of read-only/execution MCP calls, records every raw payload
//! under `.hoh/deterministic/raw/`, and summarizes the result in
//! `.hoh/deterministic/battery.json` — which is then copied into the candidate
//! view so the Tester judges instead of collects.
//!
//! The channel below is driven by the **real** payloads captured during the
//! first smoke run (`tests/fixtures/mcp`).  Where that run was a negative
//! baseline the fixture is repaired in-test on purpose: the real HUD had no
//! `Label` and the real `Player` had `shape_count=0`, which is exactly the
//! defect the battery must catch (see the `goal_collision_empty` case below).

mod common;

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};

use common::*;
use hof_rs::adapter::godot::GodotAdapter;
use hof_rs::adapter::BatteryRecord;
use hof_rs::config::{GodotConfig, HohConfig};
use hof_rs::model::{Ablation, Role};
use hof_rs::tools::mcp::McpError;
use hof_rs::tools::{ToolChannel, ToolResult};
use serde_json::{json, Value};

// ---------------------------------------------------------------------------
// Fixture loading
// ---------------------------------------------------------------------------

fn fixture_raw(name: &str) -> String {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/fixtures/mcp")
        .join(name);
    std::fs::read_to_string(&path).unwrap_or_else(|error| panic!("{path:?}: {error}"))
}

fn fixture(name: &str) -> Value {
    serde_json::from_str(&fixture_raw(name)).unwrap_or_else(|error| panic!("{name}: {error}"))
}

/// The real MCP `tools/call` envelope wraps the payload in `content[0].text`.
fn text_of(payload: &Value) -> String {
    payload["content"][0]["text"]
        .as_str()
        .unwrap_or_else(|| panic!("no text content in {payload}"))
        .to_string()
}

/// The captured `hoh: JSON-RPC error <code>: <message>` line, as an error.
fn captured_error(name: &str) -> McpError {
    let raw = fixture_raw(name);
    let rest = raw.trim_start().trim_start_matches("hoh: ");
    let rest = rest
        .trim_start_matches("JSON-RPC error ")
        .trim_start_matches("-32603: ");
    McpError::new(-32603, rest.to_string())
}

/// The real scene tree, optionally with a `Label` added under `HUD`.
///
/// The real run's HUD was a bare `CanvasLayer` with no text node, which is one
/// of the defects DR-23 exists to prevent; the green path therefore needs the
/// repaired tree while the failure paths use the captured one unchanged.
fn node_tree_payload(hud_label: bool) -> Value {
    let mut payload = fixture("node_tree.json");
    if hud_label {
        let mut tree: Value = serde_json::from_str(&text_of(&payload)).unwrap();
        let main = &mut tree["tree"];
        let hud = main["children"]
            .as_array_mut()
            .unwrap()
            .iter_mut()
            .find(|child| child["name"] == json!("HUD"))
            .expect("HUD exists in the captured tree");
        hud["children"] = json!([{
            "name": "Score",
            "path": "/root/Main/HUD/Score",
            "type": "Label",
            "children": []
        }]);
        payload["content"][0]["text"] = Value::String(tree.to_string());
    }
    payload
}

/// A collision payload derived from the captured `Ground` one.
///
/// The real `Player`/`Goal` payloads reported `shape_count=0`; the value is
/// parameterized here so one fixture covers both the healthy and the broken
/// world (the broken case reuses the captured `goal_collision_empty.json`).
fn collision_from_ground(node_path: &str, node_type: &str, shape_count: u32) -> Value {
    let mut payload = fixture("ground_collision.json");
    let mut inner: Value = serde_json::from_str(&text_of(&payload)).unwrap();
    inner["node_path"] = json!(node_path);
    inner["node_type"] = json!(node_type);
    inner["shape_count"] = json!(shape_count);
    if shape_count == 0 {
        inner["collision_shapes"] = json!([]);
    } else {
        inner["collision_shapes"][0]["has_shape"] = json!(true);
    }
    payload["content"][0]["text"] = Value::String(inner.to_string());
    payload
}

// ---------------------------------------------------------------------------
// The fixture-driven channel
// ---------------------------------------------------------------------------

struct FixtureChannel {
    calls: Mutex<Vec<(String, Value)>>,
    /// `tool -> sticky error`.
    fail_always: Mutex<HashMap<String, McpError>>,
    goal_shape_count: u32,
    player_shape_count: u32,
    hud_label: bool,
    save_screenshot: bool,
}

impl FixtureChannel {
    fn green() -> Self {
        Self {
            calls: Mutex::new(Vec::new()),
            fail_always: Mutex::new(HashMap::new()),
            goal_shape_count: 1,
            player_shape_count: 1,
            hud_label: true,
            save_screenshot: true,
        }
    }

    fn fail_always(mut self, tool: &str, error: McpError) -> Self {
        self.fail_always
            .get_mut()
            .unwrap()
            .insert(tool.to_string(), error);
        self
    }

    fn with_goal_shape_count(mut self, count: u32) -> Self {
        self.goal_shape_count = count;
        self
    }

    fn calls_of(&self, tool: &str) -> Vec<Value> {
        self.calls
            .lock()
            .unwrap()
            .iter()
            .filter(|(name, _)| name == tool)
            .map(|(_, args)| args.clone())
            .collect()
    }

    fn call_count(&self, tool: &str) -> usize {
        self.calls_of(tool).len()
    }
}

#[async_trait::async_trait]
impl ToolChannel for FixtureChannel {
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

        if let Some(error) = self.fail_always.lock().unwrap().get(tool).cloned() {
            return Err(error.into());
        }

        let payload = match tool {
            "get_editor_errors" => fixture("editor_errors_clean.json"),
            "play_scene" => fixture("play_scene_ok.json"),
            "get_game_scene_tree" => node_tree_payload(self.hud_label),
            "get_game_screenshot" => {
                if self.save_screenshot {
                    if let Some(save_path) = args.get("save_path").and_then(Value::as_str) {
                        if let Some(parent) = Path::new(save_path).parent() {
                            std::fs::create_dir_all(parent)?;
                        }
                        // A 1x1 transparent PNG placeholder: the battery only
                        // requires the reported artifact to exist.
                        std::fs::write(save_path, b"\x89PNG\r\n\x1a\n")?;
                    }
                }
                json!({"content": [{"type": "text", "text": "{\"path\": \"frame\", \"size\": 686}"}]})
            }
            "capture_frames" => json!({
                "content": [{"type": "text", "text": "{\"frames\": [\"frame-00.png\"], \"count\": 1}"}]
            }),
            "simulate_action" => fixture("simulate_action_ok.json"),
            "monitor_properties" => fixture("monitor_hold_right.json"),
            "get_game_node_properties" => match args["node_path"].as_str().unwrap_or("") {
                "Player" => fixture("player_properties.json"),
                "Goal" => fixture("goal_properties.json"),
                "HUD" => fixture("hud_properties.json"),
                other => panic!("no fixture for node {other}"),
            },
            "get_collision_info" => match args["node_path"].as_str().unwrap_or("") {
                "Ground" => fixture("ground_collision.json"),
                "Player" => {
                    collision_from_ground("Player", "CharacterBody2D", self.player_shape_count)
                }
                "Goal" => {
                    if self.goal_shape_count == 0 {
                        // The captured real payload of the broken Goal.
                        fixture("goal_collision_empty.json")
                    } else {
                        collision_from_ground("Goal", "Area2D", self.goal_shape_count)
                    }
                }
                other => panic!("no collision fixture for node {other}"),
            },
            "stop_scene" => json!({"content": [{"type": "text", "text": "{\"stopped\": true}"}]}),
            other => panic!("FixtureChannel has no reply for `{other}`"),
        };
        Ok(ToolResult { ok: true, payload })
    }
}

// ---------------------------------------------------------------------------
// One complete run with the real adapter + the fixture channel
// ---------------------------------------------------------------------------

struct BatteryRun {
    run_dir: PathBuf,
    workspace: PathBuf,
    records: Vec<BatteryRecord>,
}

fn godot_adapter(root: &Path, ready_timeout_seconds: u64) -> GodotAdapter {
    GodotAdapter::new(
        GodotConfig {
            addon_source: root.join("no-such-addon"),
            cache_excludes: vec![".godot".to_string()],
            main_scene: "res://scenes/main.tscn".to_string(),
        },
        true,
    )
    .with_battery_limits(hof_rs::adapter::godot::BatteryLimits {
        ready_timeout_seconds,
        max_retries: 0,
        timeout_seconds: 5,
    })
}

/// Run one iteration end-to-end so the candidate copy is exercised too.
async fn run_battery(
    root: &Path,
    channel: Arc<FixtureChannel>,
    ready_timeout_seconds: u64,
) -> BatteryRun {
    let mut cfg: HohConfig = test_config(root, 1);
    cfg.runtime.spec = root.join("spec.md");
    let spec = write_spec(root);
    let harness = FakeHarness::new(happy_script());
    let adapter = godot_adapter(root, ready_timeout_seconds);
    let workspace = cfg.runtime.workspace.clone();
    let run_dir = cfg.runtime.runs_dir.join("run-1");
    let orchestrator = hof_rs::runtime::run_loop::Orchestrator {
        harness: Box::new(harness),
        adapter: Box::new(adapter),
        tools: channel.clone(),
        cfg,
        ablation: Ablation::default(),
        force_init: true,
    };
    hof_rs::runtime::run_loop::run(&orchestrator, &spec, "run-1")
        .await
        .expect("the battery never fails the round by itself");

    let battery_path = run_dir.join("iter-1/candidate/.hoh/deterministic/battery.json");
    let raw = std::fs::read_to_string(&battery_path)
        .unwrap_or_else(|error| panic!("{battery_path:?}: {error}"));
    let records: Vec<BatteryRecord> = serde_json::from_str(&raw).expect("battery.json");
    BatteryRun {
        run_dir,
        workspace,
        records,
    }
}

fn step<'a>(records: &'a [BatteryRecord], id: &str) -> &'a BatteryRecord {
    records
        .iter()
        .find(|record| record.step_id == id)
        .unwrap_or_else(|| panic!("missing battery step `{id}`: {records:?}"))
}

fn valid_supports(records: &[BatteryRecord]) -> bool {
    let allowed: Vec<String> = (1..=17)
        .map(|index| format!("F{index}"))
        .chain((1..=4).map(|index| format!("N{index}")))
        .collect();
    records
        .iter()
        .all(|record| record.supports.iter().all(|id| allowed.contains(id)))
}

// ---------------------------------------------------------------------------
// ① green path
// ---------------------------------------------------------------------------

#[tokio::test]
async fn green_battery_records_every_step_and_copies_into_the_candidate() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green());
    let run = run_battery(root, channel.clone(), 30).await;

    let ids: Vec<&str> = run
        .records
        .iter()
        .map(|record| record.step_id.as_str())
        .collect();
    assert_eq!(
        ids,
        vec![
            "editor_errors_baseline",
            "play_scene_ready",
            "scene_tree",
            "screenshot",
            "input_replay",
            "node_and_collision_assertions",
            "stop_scene",
        ],
        "DR-17 fixes the step order"
    );
    for record in &run.records {
        assert!(
            record.ok,
            "step {} failed: {:?}",
            record.step_id, record.record
        );
        assert!(
            !record.supports.is_empty(),
            "step {} must declare its PRD supports",
            record.step_id
        );
        let raw_path = record
            .raw_path
            .as_ref()
            .expect("every step keeps a raw file");
        assert!(
            raw_path.starts_with(".hoh/deterministic/raw/"),
            "{raw_path}"
        );
        assert!(
            run.workspace.join(raw_path).is_file(),
            "raw payload missing on the real workspace: {raw_path}"
        );
        assert!(
            run.run_dir
                .join("iter-1/candidate")
                .join(raw_path)
                .is_file(),
            "raw payload was not copied into the candidate: {raw_path}"
        );
    }
    assert!(valid_supports(&run.records));

    // The real 120-frame hold-right recording drives F1's evidence.
    let replay = step(&run.records, "input_replay");
    assert_eq!(replay.record.kind, hof_rs::model::ExecKind::Replay);
    assert!(
        replay.record.observation.contains("120"),
        "the monitor recording must be summarized: {}",
        replay.record.observation
    );

    // Readiness waited for the game before touching it.
    assert!(
        channel.call_count("get_game_scene_tree") >= 2,
        "the readiness poll plus the tree step must both call it"
    );
    // The screenshot artifact is reported as a relative path.
    let screenshot = step(&run.records, "screenshot");
    assert_eq!(
        screenshot.record.path.as_deref(),
        Some(".hoh/evidence/frame-00.png"),
        "the screenshot must be referenced relatively"
    );

    // The Tester view carries the battery and the playbook.
    let candidate = run.run_dir.join("iter-1/candidate/.hoh");
    assert!(candidate.join("deterministic/battery.json").is_file());
    assert!(candidate.join("EVIDENCE_PLAYBOOK.md").is_file());
}

/// DR-17: the Tester's job is judgement, not collection.
#[test]
fn tester_prompt_is_judgement_first() {
    let prompt = hof_rs::prompts::TESTER_PROMPT.to_lowercase();
    assert!(
        prompt.contains("battery") || prompt.contains("deterministic"),
        "the tester must be pointed at the battery"
    );
    assert!(
        prompt.contains("judge") || prompt.contains("judgement") || prompt.contains("judgment"),
        "the tester's primary job must be judging"
    );
    assert!(
        prompt.contains("relative"),
        "evidence paths must be relative"
    );
    assert!(
        prompt.contains("gap"),
        "unsupported claims must be recorded as gaps"
    );
}

// ---------------------------------------------------------------------------
// ② editor errors unavailable
// ---------------------------------------------------------------------------

#[tokio::test]
async fn editor_error_failure_is_recorded_verbatim() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green().fail_always(
        "get_editor_errors",
        captured_error("editor_errors_failure.txt"),
    ));
    let run = run_battery(root, channel, 30).await;

    let record = step(&run.records, "editor_errors_baseline");
    assert!(!record.ok, "a failed baseline must be `ok=false`");
    assert!(
        record.record.observation.contains("-32603"),
        "the JSON-RPC code must survive: {}",
        record.record.observation
    );
    assert!(
        record.record.observation.contains("FAILED"),
        "{}",
        record.record.observation
    );
    assert!(
        record.record.observation.contains("UNAVAILABLE"),
        "{}",
        record.record.observation
    );

    let journal = run.workspace.join(".hoh/deterministic/mcp-errors.jsonl");
    let raw = std::fs::read_to_string(&journal).expect("mcp-errors.jsonl");
    let entry: Value = serde_json::from_str(raw.lines().next().unwrap()).unwrap();
    assert_eq!(entry["tool"], json!("get_editor_errors"));
    assert_eq!(entry["code"], json!(-32603));
    assert!(run
        .run_dir
        .join("iter-1/candidate/.hoh/deterministic/mcp-errors.jsonl")
        .is_file());
}

// ---------------------------------------------------------------------------
// ③ screenshot unavailable
// ---------------------------------------------------------------------------

#[tokio::test]
async fn screenshot_failure_is_not_disguised_as_a_clean_step() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let error = captured_error("screenshot_failure.txt");
    let channel = Arc::new(
        FixtureChannel::green()
            .fail_always("get_game_screenshot", error.clone())
            .fail_always("capture_frames", error),
    );
    let run = run_battery(root, channel, 30).await;

    let record = step(&run.records, "screenshot");
    assert!(!record.ok);
    assert!(
        record.record.observation.contains("截图文件不存在"),
        "the verbatim message must be carried: {}",
        record.record.observation
    );
    assert!(record.record.observation.contains("FAILED"));
    assert!(record.record.path.is_none(), "no artifact may be claimed");
}

// ---------------------------------------------------------------------------
// ④ readiness timeout
// ---------------------------------------------------------------------------

#[tokio::test]
async fn readiness_timeout_fails_the_step_and_is_journalled() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green().fail_always(
        "get_game_scene_tree",
        McpError::new(-32603, "等待游戏响应超时 (5秒)"),
    ));
    let run = run_battery(root, channel, /* ready timeout */ 0).await;

    let record = step(&run.records, "play_scene_ready");
    assert!(!record.ok, "a timed-out readiness wait is a failure");
    assert!(
        record.record.observation.contains("UNAVAILABLE"),
        "{}",
        record.record.observation
    );
    assert!(
        record.record.observation.contains("等待游戏响应超时"),
        "{}",
        record.record.observation
    );

    let raw = std::fs::read_to_string(run.workspace.join(".hoh/deterministic/mcp-errors.jsonl"))
        .expect("mcp-errors.jsonl");
    assert!(
        raw.lines().any(|line| line.contains("get_game_scene_tree")),
        "{raw}"
    );
}

// ---------------------------------------------------------------------------
// ⑤ Goal without a collision shape
// ---------------------------------------------------------------------------

#[tokio::test]
async fn goal_without_a_collision_shape_fails_the_assertion_step() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green().with_goal_shape_count(0));
    let run = run_battery(root, channel, 30).await;

    let record = step(&run.records, "node_and_collision_assertions");
    assert!(!record.ok, "shape_count=0 must fail the battery assertion");
    assert!(
        record.record.observation.contains("Goal"),
        "{}",
        record.record.observation
    );
    assert!(
        record.record.observation.contains("shape_count")
            || record.record.observation.contains("collision"),
        "{}",
        record.record.observation
    );
    assert!(
        record.supports.iter().any(|id| id == "F13"),
        "the Goal assertion supports the victory requirement: {:?}",
        record.supports
    );
}

// ---------------------------------------------------------------------------
// Battery shape
// ---------------------------------------------------------------------------

#[tokio::test]
async fn battery_json_has_the_frozen_shape() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green());
    let run = run_battery(root, channel, 30).await;

    let raw = std::fs::read_to_string(
        run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/battery.json"),
    )
    .unwrap();
    let value: Value = serde_json::from_str(&raw).unwrap();
    let first = &value.as_array().unwrap()[0];
    for key in ["step_id", "supports", "record", "ok", "raw_path"] {
        assert!(first.get(key).is_some(), "battery entry is missing {key}");
    }
    assert_eq!(first["record"]["type"], json!("build"));
}
