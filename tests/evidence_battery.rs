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

/// DR-24: a scene that passes the structure check (exactly one root node).
const VALID_SCENE: &str = "[gd_scene load_steps=2 format=3]\n\n\
[node name=\"Main\" type=\"Node2D\"]\n\n\
[node name=\"Ground\" type=\"StaticBody2D\" parent=\".\"]\n\n\
[node name=\"Player\" type=\"CharacterBody2D\" parent=\".\"]\n";

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

/// DR-30: how the mocked `running_game_capture_screenshot` / `running_game_capture_frames` behave.
#[derive(Clone, Copy, PartialEq, Eq)]
enum ScreenshotMode {
    /// The tool writes the PNG the battery asked for.
    WritesFile,
    /// The tool answers `ok` but nothing lands on disk and no image is carried
    /// inline (`smoke-t3` reported `path` for a file that did not exist).
    ReportsSuccessButNoFile,
    /// The primary tool fails and `running_game_capture_frames` answers with an inline
    /// base64 PNG, which the runtime must materialize itself.
    InlineBase64Fallback,
}

/// DR-33: what `editor_get_input_actions` says about the InputMap.
#[derive(Clone, Copy, PartialEq, Eq)]
enum InputActionsMode {
    /// `move_left` / `move_right` / `jump` are bound.
    Bound,
    /// The InputMap has no such action.
    Missing,
    /// The payload captured in `smoke-t5`: the **editor's** InputMap, which
    /// lists only the engine's built-in `ui_*` actions.
    RealEditorMap,
}

/// DR-35: what the **game process** answers to `running_game_execute_gdscript`.
#[derive(Clone, Copy, PartialEq, Eq)]
enum GameInputMode {
    /// The action exists in the game and the press is observable.
    Ok,
    /// The game's `InputMap` really has no such action.
    ActionMissing,
    /// `running_game_execute_gdscript` fails the way it did in `smoke-t5`
    /// (`Invalid named index 'Input' for base type Object`).
    ProbeFails,
}

struct FixtureChannel {
    calls: Mutex<Vec<(String, Value)>>,
    /// `tool -> sticky error`.
    fail_always: Mutex<HashMap<String, McpError>>,
    /// `tool -> canned reply`, used to build malformed payloads.
    overrides: Mutex<HashMap<String, Value>>,
    goal_shape_count: u32,
    player_shape_count: u32,
    hud_label: bool,
    /// DR-30/DR-33: whether the replayed `Player` actually moves.
    moving: bool,
    screenshot: ScreenshotMode,
    input_actions: InputActionsMode,
    /// DR-35: the game-process input channel.
    game_input: GameInputMode,
    /// DR-35: whether a game-side `action_press` is currently held.
    pressed_in_game: Mutex<bool>,
    /// The action of the most recent `editor_simulate_input_action`, so `running_game_get_node_property_samples`
    /// (which does not name an action) can answer plausibly.
    last_action: Mutex<String>,
}

impl FixtureChannel {
    fn green() -> Self {
        Self {
            calls: Mutex::new(Vec::new()),
            fail_always: Mutex::new(HashMap::new()),
            overrides: Mutex::new(HashMap::new()),
            goal_shape_count: 1,
            player_shape_count: 1,
            hud_label: true,
            moving: true,
            screenshot: ScreenshotMode::WritesFile,
            input_actions: InputActionsMode::Bound,
            game_input: GameInputMode::Ok,
            pressed_in_game: Mutex::new(false),
            last_action: Mutex::new("move_right".to_string()),
        }
    }

    fn fail_always(mut self, tool: &str, error: McpError) -> Self {
        self.fail_always
            .get_mut()
            .unwrap()
            .insert(tool.to_string(), error);
        self
    }

    /// DR-30: answer `tool` with a payload of the wrong shape.
    fn with_reply(mut self, tool: &str, payload: Value) -> Self {
        self.overrides
            .get_mut()
            .unwrap()
            .insert(tool.to_string(), payload);
        self
    }

    fn with_goal_shape_count(mut self, count: u32) -> Self {
        self.goal_shape_count = count;
        self
    }

    fn with_input_actions(mut self, mode: InputActionsMode) -> Self {
        self.input_actions = mode;
        self
    }

    /// DR-35: choose what the **game process** answers.
    fn with_game_input(mut self, mode: GameInputMode) -> Self {
        self.game_input = mode;
        self
    }

    fn with_moving(mut self, moving: bool) -> Self {
        self.moving = moving;
        self
    }

    fn with_screenshot(mut self, mode: ScreenshotMode) -> Self {
        self.screenshot = mode;
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

/// A PNG payload carrying one inline base64 image (the `running_game_capture_frames` shape
/// captured in `smoke-t3`).
const INLINE_PNG_TEXT: &str =
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg==";

fn inline_png_bytes() -> Vec<u8> {
    vec![
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44,
        0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x08, 0x06, 0x00, 0x00, 0x00, 0x1F,
        0x15, 0xC4, 0x89, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x44, 0x41, 0x54, 0x78, 0xDA, 0x63, 0xFC,
        0xCF, 0xC0, 0xF0, 0x1F, 0x00, 0x05, 0x00, 0x01, 0xFF, 0xAB, 0xCE, 0x36, 0x89, 0x00, 0x00,
        0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
    ]
}

/// The `running_game_capture_screenshot` "I saved it" reply (no image inline).
fn screenshot_ok_payload() -> Value {
    json!({"content": [{"type": "text", "text": "{\"path\": \"frame\", \"size\": 686}"}]})
}

/// The `running_game_capture_frames` reply captured in `smoke-t3`: the image travels inline
/// as base64 and it is the runtime's job to put it on disk.
fn inline_frames_payload() -> Value {
    let inner = json!({
        "count": 1,
        "frames": [{"height": 180, "image_base64": INLINE_PNG_TEXT}],
    });
    json!({"content": [{"type": "text", "text": inner.to_string()}]})
}

/// A `running_game_get_node_property_samples` recording: either the captured `Player` that never
/// moves (`smoke-t3`: `(60.0, 283.999)` for all 60 frames) or a recording that
/// responds to `action`.
fn monitor_payload(action: &str, frames: u64, moving: bool) -> Value {
    let mut samples = Vec::new();
    for frame in 0..frames {
        let (x, y) = if !moving {
            (60.0, 283.998992919922)
        } else {
            match action {
                "move_left" => (100.0 - frame as f64, 283.0),
                "jump" => (60.0, (frame as f64 * 2.0) % 80.0),
                _ => (frame as f64 * 2.0, 283.0),
            }
        };
        samples.push(json!({
            "frame": frame,
            "position": {"x": x, "y": y},
        }));
    }
    let inner = json!({
        "frame_count": frames,
        "node_path": "Player",
        "samples": samples,
    });
    json!({"content": [{"type": "text", "text": inner.to_string()}]})
}

/// The `editor_get_input_actions` reply for the requested mode.
fn input_actions_payload(mode: InputActionsMode) -> Value {
    if mode == InputActionsMode::RealEditorMap {
        // The verbatim payload the battery collected in `smoke-t5`: the editor's
        // own InputMap, listing only the engine's built-in `ui_*` actions.
        let real: Value = fixture("input_replay_smoke_t5.json");
        return real["calls"][0]["payload"].clone();
    }
    let actions = match mode {
        InputActionsMode::Bound => json!([
            {"name": "move_left", "keys": ["A", "Left"]},
            {"name": "move_right", "keys": ["D", "Right"]},
            {"name": "jump", "keys": ["Space", "W"]},
        ]),
        InputActionsMode::Missing => json!([{"name": "ui_accept", "keys": ["Enter"]}]),
        InputActionsMode::RealEditorMap => unreachable!("handled above"),
    };
    let inner = json!({"actions": actions});
    json!({"content": [{"type": "text", "text": inner.to_string()}]})
}

/// DR-35: one `running_game_execute_gdscript` reply, in the addon's
/// `{"result": str(value)}` shape.
fn game_script_payload(reading: &str) -> Value {
    let inner = json!({"result": reading});
    json!({"content": [{"type": "text", "text": inner.to_string()}]})
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
        if let Some(payload) = self.overrides.lock().unwrap().get(tool).cloned() {
            return Ok(ToolResult { ok: true, payload });
        }

        let payload = match tool {
            "editor_rescan_project_filesystem" => {
                json!({"content": [{"type": "text", "text": "{\"reloaded\": true}"}]})
            }
            "editor_open_scene" => json!({"content": [{"type": "text", "text": "{\"opened\": true}"}]}),
            "project_read_scene_file_content" => json!({
                "content": [{"type": "text", "text": json!({"content": VALID_SCENE}).to_string()}]
            }),
            "editor_get_errors" => fixture("editor_errors_clean.json"),
            "editor_play_scene" => fixture("play_scene_ok.json"),
            "running_game_get_scene_tree" => node_tree_payload(self.hud_label),
            "editor_get_input_actions" => input_actions_payload(self.input_actions),
            "running_game_capture_screenshot" => match self.screenshot {
                ScreenshotMode::WritesFile => {
                    if let Some(save_path) = args.get("save_path").and_then(Value::as_str) {
                        if let Some(parent) = Path::new(save_path).parent() {
                            std::fs::create_dir_all(parent)?;
                        }
                        std::fs::write(save_path, inline_png_bytes())?;
                    }
                    screenshot_ok_payload()
                }
                // The smoke-t3 shape: an `ok` reply naming a file that was never
                // written.
                ScreenshotMode::ReportsSuccessButNoFile => screenshot_ok_payload(),
                ScreenshotMode::InlineBase64Fallback => {
                    return Err(captured_error("screenshot_failure.txt").into());
                }
            },
            "running_game_capture_frames" => match self.screenshot {
                ScreenshotMode::ReportsSuccessButNoFile => json!({
                    "content": [{"type": "text", "text":
                        "{\"frames\": [\"frame-00.png\"], \"count\": 1}"}]
                }),
                _ => inline_frames_payload(),
            },
            "editor_simulate_input_action" => {
                if let Some(action) = args.get("action").and_then(Value::as_str) {
                    *self.last_action.lock().unwrap() = action.to_string();
                }
                fixture("simulate_action_ok.json")
            }
            // DR-35: the game-process input channel.  The probe scripts are the
            // real ones (`str(InputMap.has_action(...))` and friends), so this
            // branch keys on them.
            "running_game_execute_gdscript" => {
                if self.game_input == GameInputMode::ProbeFails {
                    return Err(captured_error("game_script_input_unreachable.txt").into());
                }
                let code = args.get("code").and_then(Value::as_str).unwrap_or("");
                let bound = self.game_input == GameInputMode::Ok;
                if code.contains("action_press") {
                    *self.pressed_in_game.lock().unwrap() = true;
                    game_script_payload("<null>")
                } else if code.contains("action_release") {
                    *self.pressed_in_game.lock().unwrap() = false;
                    game_script_payload("<null>")
                } else if code.contains("has_action") {
                    game_script_payload(if bound { "true" } else { "false" })
                } else if code.contains("get_axis") {
                    let pressed = *self.pressed_in_game.lock().unwrap();
                    let moving = bound && pressed && self.moving;
                    game_script_payload(if moving { "1.0" } else { "0.0" })
                } else if code.contains("is_action_pressed") {
                    let pressed = *self.pressed_in_game.lock().unwrap();
                    game_script_payload(if bound && pressed { "true" } else { "false" })
                } else if code.contains("position") {
                    let pressed = *self.pressed_in_game.lock().unwrap();
                    let x = if bound && pressed && self.moving {
                        80.0
                    } else {
                        60.0
                    };
                    game_script_payload(&format!("{x},283.999"))
                } else {
                    panic!("FixtureChannel got an unexpected game script: {code}")
                }
            }
            "running_game_get_node_property_samples" => {
                let action = self.last_action.lock().unwrap().clone();
                let frames = args
                    .get("frame_count")
                    .and_then(Value::as_u64)
                    .unwrap_or(60);
                // DR-35: the game moves only when the **game process** received
                // the press.  An editor-side `editor_simulate_input_action` cannot move it,
                // which is exactly the `smoke-t5` finding.
                let pressed_in_game = *self.pressed_in_game.lock().unwrap();
                let moves = self.moving && self.game_input == GameInputMode::Ok && pressed_in_game;
                monitor_payload(&action, frames, moves)
            }
            "running_game_get_node_properties" => match args["node_path"].as_str().unwrap_or("") {
                "Player" => fixture("player_properties.json"),
                "Goal" => fixture("goal_properties.json"),
                "HUD" => fixture("hud_properties.json"),
                other => panic!("no fixture for node {other}"),
            },
            "editor_get_collision_info" => match args["node_path"].as_str().unwrap_or("") {
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
            "editor_stop_scene" => json!({"content": [{"type": "text", "text": "{\"stopped\": true}"}]}),
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

fn godot_adapter(_root: &Path, ready_timeout_seconds: u64) -> GodotAdapter {
    GodotAdapter::new(
        GodotConfig {
            editor_binary: std::path::PathBuf::new(),
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
    run_battery_with_script(root, channel, ready_timeout_seconds, happy_script()).await
}

/// Same, with an explicit script: a failing gate consumes one extra Developer
/// call (DR-24's targeted repair), so those cases need a fourth scripted step.
async fn run_battery_with_script(
    root: &Path,
    channel: Arc<FixtureChannel>,
    ready_timeout_seconds: u64,
    script: Vec<FakeStep>,
) -> BatteryRun {
    run_battery_opts(root, channel, ready_timeout_seconds, script, None).await
}

/// DR-36: the same run with an explicit `runtime.max_evidence_bytes`.
async fn run_battery_with_evidence_limit(
    root: &Path,
    channel: Arc<FixtureChannel>,
    ready_timeout_seconds: u64,
    max_evidence_bytes: u64,
) -> BatteryRun {
    run_battery_opts(
        root,
        channel,
        ready_timeout_seconds,
        happy_script(),
        Some(max_evidence_bytes),
    )
    .await
}

async fn run_battery_opts(
    root: &Path,
    channel: Arc<FixtureChannel>,
    ready_timeout_seconds: u64,
    script: Vec<FakeStep>,
    max_evidence_bytes: Option<u64>,
) -> BatteryRun {
    let mut cfg: HohConfig = test_config(root, 1);
    cfg.runtime.spec = root.join("spec.md");
    if let Some(limit) = max_evidence_bytes {
        cfg.runtime.max_evidence_bytes = limit;
    }
    let spec = write_spec(root);
    let harness = FakeHarness::new(script);
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
        start_state: hof_rs::runtime::start_state::StartState::as_is(),
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

/// The happy path plus the one targeted repair call DR-24 issues when the gate
/// closes (the scripted channel below fails a gate step on purpose).
fn repairing_script() -> Vec<FakeStep> {
    vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Developer),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{\"moved\":true}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ]
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
        // DR-33: `ACTION_NOT_BOUND` is evidence about the PRD's engineering
        // constraint P3 (named InputMap actions) as well as about F1/F2.
        .chain((1..=6).map(|index| format!("P{index}")))
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
            "project_reload_and_open",
            "scene_structure",
            "editor_errors_baseline",
            "play_scene_ready",
            "scene_tree",
            "screenshot",
            "input_channel_probe",
            "input_replay",
            "node_and_collision_assertions",
            "editor_stop_scene",
        ],
        "DR-24 inserts the reload/open and scene-structure steps before the editor errors"
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

    // The replayed recording drives F1's evidence.  DR-30/DR-33: the captured
    // `smoke-t3` recording was **constant** (`(60.0, 283.999)` for 120 frames),
    // so it can no longer serve as the green fixture — it is now the
    // `INPUT_HAD_NO_EFFECT` counter-example and the green path uses a recording
    // that actually responds to the simulated action.
    let replay = step(&run.records, "input_replay");
    assert_eq!(replay.record.kind, hof_rs::model::ExecKind::Replay);
    assert!(
        replay.record.observation.contains("60 frame(s)"),
        "the monitor recording must be summarized: {}",
        replay.record.observation
    );
    assert!(
        replay.record.observation.contains("before_position")
            && replay.record.observation.contains("after_position"),
        "the before/after positions must be recorded: {}",
        replay.record.observation
    );
    assert!(
        replay.record.observation.contains("move_right")
            && replay.record.observation.contains("jump")
            && replay.record.observation.contains("move_left"),
        "all three named actions must be replayed: {}",
        replay.record.observation
    );

    // Readiness waited for the game before touching it.
    assert!(
        channel.call_count("running_game_get_scene_tree") >= 2,
        "the readiness poll plus the tree step must both call it"
    );
    // The screenshot artifact is reported as a relative path **and** the bytes
    // are really on disk (DR-30).
    let screenshot = step(&run.records, "screenshot");
    assert_eq!(
        screenshot.record.path.as_deref(),
        Some(".hoh/evidence/frame-00.png"),
        "the screenshot must be referenced relatively"
    );
    let png = std::fs::read(run.workspace.join(".hoh/evidence/frame-00.png"))
        .expect("the reported screenshot must exist on disk");
    assert_eq!(
        png,
        inline_png_bytes(),
        "the file must be the PNG the tool produced, byte for byte"
    );
    assert_eq!(&png[..8], b"\x89PNG\r\n\x1a\n", "a real PNG signature");

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
        "editor_get_errors",
        captured_error("editor_errors_failure.txt"),
    ));
    let run = run_battery_with_script(root, channel, 30, repairing_script()).await;

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
    assert_eq!(entry["tool"], json!("editor_get_errors"));
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
            .fail_always("running_game_capture_screenshot", error.clone())
            .fail_always("running_game_capture_frames", error),
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
        "running_game_get_scene_tree",
        McpError::new(-32603, "等待游戏响应超时 (5秒)"),
    ));
    let run = run_battery_with_script(
        root,
        channel,
        /* ready timeout */ 0,
        repairing_script(),
    )
    .await;

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
        raw.lines().any(|line| line.contains("running_game_get_scene_tree")),
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

// ---------------------------------------------------------------------------
// DR-30 — a payload's *shape* is the evidence, not "a response arrived"
// ---------------------------------------------------------------------------

/// `smoke-t3`'s `play_scene_ready` accepted `editor_play_scene`'s own reply
/// (`{"mode":"main","playing":true}`) because the readiness poll only asked
/// whether the call succeeded.  Readiness must be confirmed by a scene tree.
#[tokio::test]
async fn play_scene_ready_refuses_a_payload_that_is_not_a_scene_tree() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green().with_reply(
        "running_game_get_scene_tree",
        json!({"content": [{"type": "text", "text": "{\"mode\":\"main\",\"playing\":true}"}]}),
    ));
    let run = run_battery_with_script(root, channel, 1, repairing_script()).await;

    let record = step(&run.records, "play_scene_ready");
    assert!(
        !record.ok,
        "editor_play_scene's own reply is not readiness evidence: {:?}",
        record.record
    );
    assert!(
        record.record.observation.contains("UNAVAILABLE"),
        "{}",
        record.record.observation
    );
    assert!(
        record.record.observation.contains("scene tree")
            || record.record.observation.contains("node"),
        "the observation must name what was missing: {}",
        record.record.observation
    );
    assert!(
        !record.record.observation.contains("booted"),
        "the step may not claim the scene booted: {}",
        record.record.observation
    );
}

/// `smoke-t3`'s `editor_errors_baseline` received the scene *text* instead of an
/// errors array.  `ok=false` is right; the observation must also say the payload
/// had the wrong shape and keep it verbatim.
#[tokio::test]
async fn editor_errors_baseline_requires_an_errors_array() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let scene_text = "{\"content\":\"[gd_scene load_steps=2 format=3]\"}";
    let channel = Arc::new(FixtureChannel::green().with_reply(
        "editor_get_errors",
        json!({"content": [{"type": "text", "text": scene_text}]}),
    ));
    let run = run_battery_with_script(root, channel, 30, repairing_script()).await;

    let record = step(&run.records, "editor_errors_baseline");
    assert!(!record.ok);
    assert!(
        record.record.observation.contains("gd_scene"),
        "the raw payload must be quoted: {}",
        record.record.observation
    );
    assert!(
        record.record.observation.contains("no `errors` array"),
        "the missing `errors` array must be named explicitly: {}",
        record.record.observation
    );
}

/// A recording with no position sample is not evidence of movement.
#[tokio::test]
async fn input_replay_without_frame_samples_is_a_failure() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green().with_reply(
        "running_game_get_node_property_samples",
        json!({"content": [{"type": "text", "text": "{\"frame_count\":0,\"samples\":[]}"}]}),
    ));
    let run = run_battery(root, channel, 30).await;

    let record = step(&run.records, "input_replay");
    assert!(!record.ok, "`0 frame(s), position unknown` is not ok=true");
    assert!(
        record.record.observation.contains("NO_FRAME_SAMPLES"),
        "{}",
        record.record.observation
    );
}

/// The captured `smoke-t3` recording: `editor_simulate_input_action` is acknowledged but
/// `Player.position` never changes.  That is `INPUT_HAD_NO_EFFECT`, and the
/// `(action, before, after, velocity)` quadruple must be on record.
#[tokio::test]
async fn input_replay_records_a_delivered_action_without_effect() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green().with_moving(false));
    let run = run_battery(root, channel, 30).await;

    let record = step(&run.records, "input_replay");
    assert!(!record.ok);
    assert!(
        record.record.observation.contains("INPUT_HAD_NO_EFFECT"),
        "{}",
        record.record.observation
    );
    assert!(
        record.supports.iter().any(|id| id == "F1") && record.supports.iter().any(|id| id == "F2"),
        "the Tester needs F1/F2 to judge the gap: {:?}",
        record.supports
    );

    // The quadruple is written into the raw payload of the monitor calls.
    let raw: Value = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/raw/input_replay.json"),
    ))
    .unwrap();
    let quadruples: Vec<&Value> = raw["calls"]
        .as_array()
        .unwrap()
        .iter()
        .filter_map(|call| call.get("quadruple"))
        .collect();
    assert!(
        !quadruples.is_empty(),
        "every replay entry must record its quadruple: {raw}"
    );
    let first = quadruples[0];
    for key in ["action", "before_position", "after_position", "velocity"] {
        assert!(
            first.get(key).is_some(),
            "quadruple is missing {key}: {first}"
        );
    }
    assert_eq!(first["action"], json!("move_right"));
    assert_eq!(first["before_position"], first["after_position"]);
    assert_eq!(first["velocity"], json!({"x": 0.0, "y": 0.0}));
}

/// DR-33 ①/DR-35 ②: the **game process** InputMap has no `move_right` at all —
/// a different, and much more actionable, fact than "the input had no effect".
/// Under DR-35 this verdict may only come from the game-process probe.
#[tokio::test]
async fn input_replay_reports_an_action_that_is_not_bound() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(
        FixtureChannel::green()
            .with_input_actions(InputActionsMode::Missing)
            .with_game_input(GameInputMode::ActionMissing)
            .with_moving(false),
    );
    let run = run_battery(root, channel, 30).await;

    let probe = step(&run.records, "input_channel_probe");
    assert!(!probe.ok);
    assert!(
        probe.record.observation.contains("ACTION_NOT_BOUND"),
        "{}",
        probe.record.observation
    );
    assert!(
        probe.supports.iter().any(|id| id == "P3"),
        "a missing InputMap action is P3 evidence: {:?}",
        probe.supports
    );

    let record = step(&run.records, "input_replay");
    assert!(!record.ok);
    assert!(
        record.record.observation.contains("ACTION_NOT_BOUND"),
        "{}",
        record.record.observation
    );
    for id in ["F1", "F2", "P3"] {
        assert!(
            record.supports.iter().any(|support| support == id),
            "a missing InputMap action is P3 evidence as well: {:?}",
            record.supports
        );
    }
    // The binding evidence itself must reach the raw payload.
    let raw: Value = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/raw/input_replay.json"),
    ))
    .unwrap();
    let text = raw.to_string();
    assert!(
        text.contains("editor_get_input_actions"),
        "the availability probe must be recorded: {text}"
    );
    assert!(
        !record.record.observation.contains("INPUT_HAD_NO_EFFECT"),
        "an unbound action was never delivered: {}",
        record.record.observation
    );
}

// ---------------------------------------------------------------------------
// DR-35 — the input channel is the *game* process, not the editor
// ---------------------------------------------------------------------------

/// DR-35 ①: the game process reports the action, the press moves `get_axis` and
/// the player: the channel is usable and the replay is green.
#[tokio::test]
async fn a_usable_game_channel_makes_the_replay_green() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green());
    let run = run_battery(root, channel.clone(), 30).await;

    let probe = step(&run.records, "input_channel_probe");
    assert!(
        probe.ok,
        "the game channel works: {:?}",
        probe.record.observation
    );
    assert!(
        probe.record.observation.contains("GAME_INPUT_CHANNEL_OK"),
        "{}",
        probe.record.observation
    );

    let replay = step(&run.records, "input_replay");
    assert!(
        replay.ok,
        "the replay is judged on game-process movement: {:?}",
        replay.record.observation
    );
    assert!(
        replay.record.observation.contains("GAME_INPUT_CHANNEL_OK"),
        "{}",
        replay.record.observation
    );
    assert!(
        replay.record.observation.contains("game_process"),
        "{}",
        replay.record.observation
    );
    // The game-side injection really went through `running_game_execute_gdscript`.
    assert!(
        channel.call_count("running_game_execute_gdscript") >= 8,
        "the probe and the replay must drive the game process directly"
    );
    // DR-35: the raw probe payload is persisted verbatim.
    let raw: Value = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/raw/input_channel_probe.json"),
    ))
    .unwrap();
    assert_eq!(raw["step"], json!("input_channel_probe"));
    assert_eq!(
        raw["channel"]["capability"],
        json!("GAME_INPUT_CHANNEL_OK"),
        "{raw}"
    );
    assert_eq!(raw["channel"]["has_action"], json!(true));
    assert!(
        raw["calls"]
            .as_array()
            .unwrap()
            .iter()
            .filter(|call| call["tool"] == json!("running_game_execute_gdscript"))
            .count()
            >= 6,
        "every probe reading must be recorded verbatim: {raw}"
    );
}

/// DR-35 ③: the probe itself fails (exactly the `smoke-t5` error: the addon's
/// `Expression` cannot see the `Input` singleton).  That is *unknown*, never
/// `ACTION_NOT_BOUND`.
#[tokio::test]
async fn a_failed_probe_is_unknown_never_not_bound() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green().with_game_input(GameInputMode::ProbeFails));
    let run = run_battery(root, channel, 30).await;

    let probe = step(&run.records, "input_channel_probe");
    assert!(!probe.ok, "an unreadable probe is not usable evidence");
    assert!(
        probe.record.observation.contains("ACTION_BINDING_UNKNOWN"),
        "{}",
        probe.record.observation
    );
    assert!(
        !probe.record.observation.contains("ACTION_NOT_BOUND"),
        "a failed probe must never be downgraded: {}",
        probe.record.observation
    );

    let replay = step(&run.records, "input_replay");
    assert!(!replay.ok);
    assert!(
        replay.record.observation.contains("ACTION_BINDING_UNKNOWN"),
        "{}",
        replay.record.observation
    );
    assert!(
        !replay.record.observation.contains("ACTION_NOT_BOUND"),
        "{}",
        replay.record.observation
    );

    // The verbatim error text travelled into the raw payload.
    let raw = read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/raw/input_channel_probe.json"),
    );
    assert!(
        raw.contains("Invalid named index"),
        "the real failure must be quoted: {raw}"
    );
}

/// DR-35 — **the root-cause regression**: `smoke-t5`'s editor-side InputMap (the
/// verbatim payload, which lists only the built-in `ui_*` actions) plus a
/// game-process probe that cannot be read must NOT produce `ACTION_NOT_BOUND`.
///
/// That false negative went as far as the Planner's `update_targets`, i.e. the
/// next round would have paid ~50M tokens to fix a defect that never existed.
#[tokio::test]
async fn the_editor_input_map_can_never_claim_an_action_is_not_bound() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(
        FixtureChannel::green()
            .with_input_actions(InputActionsMode::RealEditorMap)
            .with_game_input(GameInputMode::ProbeFails),
    );
    let run = run_battery(root, channel, 30).await;

    for id in ["input_channel_probe", "input_replay"] {
        let record = step(&run.records, id);
        assert!(
            !record.record.observation.contains("ACTION_NOT_BOUND"),
            "step `{id}` took the editor's InputMap for the game's: {}",
            record.record.observation
        );
        assert!(
            record.record.observation.contains("ACTION_BINDING_UNKNOWN"),
            "step `{id}` must report the honest unknown: {}",
            record.record.observation
        );
    }
    let replay = step(&run.records, "input_replay");
    assert!(
        replay.record.observation.contains("EDITOR_SIDE_INJECTION"),
        "the editor-side record must be labelled: {}",
        replay.record.observation
    );

    // The whole raw tree must be free of the false verdict.
    for id in ["input_channel_probe", "input_replay"] {
        let raw = read(
            &run.run_dir
                .join(format!("iter-1/candidate/.hoh/deterministic/raw/{id}.json")),
        );
        assert!(
            !raw.contains("ACTION_NOT_BOUND"),
            "nothing in `{id}` may say ACTION_NOT_BOUND: {raw}"
        );
    }
}

/// DR-35 ④: the editor accepts the injection but the game process never moves.
/// The round must fail and the editor-side record must be labelled — an
/// editor-side "success" is not evidence about the game.
#[tokio::test]
async fn an_editor_side_success_without_game_movement_is_labelled_and_fails() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green().with_moving(false));
    let run = run_battery(root, channel, 30).await;

    let replay = step(&run.records, "input_replay");
    assert!(!replay.ok, "{}", replay.record.observation);
    assert!(
        replay.record.observation.contains("EDITOR_SIDE_INJECTION"),
        "{}",
        replay.record.observation
    );
    assert!(
        replay.record.observation.contains("INPUT_HAD_NO_EFFECT"),
        "{}",
        replay.record.observation
    );
    assert!(
        replay.record.observation.contains("editor_process"),
        "the editor-side channel must be named: {}",
        replay.record.observation
    );
}

/// DR-35 ⑤: every quadruple names the process it was observed in; editor-side
/// calls carry the editor channel and the injection marker.
#[tokio::test]
async fn every_quadruple_names_its_channel() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green());
    let run = run_battery(root, channel, 30).await;

    let raw: Value = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/raw/input_replay.json"),
    ))
    .unwrap();
    let quadruples: Vec<&Value> = raw["calls"]
        .as_array()
        .unwrap()
        .iter()
        .filter_map(|call| call.get("quadruple"))
        .collect();
    assert!(!quadruples.is_empty(), "{raw}");
    for quadruple in &quadruples {
        assert_eq!(
            quadruple["channel"],
            json!("game_process"),
            "the position samples are game-forwarded: {quadruple}"
        );
    }
    let editor_calls: Vec<&Value> = raw["calls"]
        .as_array()
        .unwrap()
        .iter()
        .filter(|call| call["tool"] == json!("editor_simulate_input_action"))
        .collect();
    assert!(!editor_calls.is_empty());
    for call in editor_calls {
        assert!(
            call["label"]
                .as_str()
                .unwrap_or_default()
                .contains("EDITOR_SIDE_INJECTION"),
            "an editor-side injection must be labelled: {call}"
        );
    }
}

/// DR-35: the real 50-node game scene tree captured in `smoke-t5` is accepted by
/// the `scene_tree` step (a real shape, not a synthesized one).
#[tokio::test]
async fn the_real_game_scene_tree_fixture_is_accepted() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let real: Value = fixture("game_scene_tree_real.json");
    let payload = real["calls"][0]["payload"].clone();
    let channel = Arc::new(FixtureChannel::green().with_reply("running_game_get_scene_tree", payload));
    let run = run_battery(root, channel, 30).await;

    let record = step(&run.records, "scene_tree");
    assert!(
        record.ok,
        "the captured tree carries a path and a type on every node: {:?}",
        record.record.observation
    );
    assert!(
        record.record.observation.contains("50 node"),
        "{}",
        record.record.observation
    );
}

/// DR-30: `screenshot` may only claim a `path` when the PNG really exists.
#[tokio::test]
async fn screenshot_never_claims_a_path_that_does_not_exist() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel =
        Arc::new(FixtureChannel::green().with_screenshot(ScreenshotMode::ReportsSuccessButNoFile));
    let run = run_battery(root, channel, 30).await;

    let record = step(&run.records, "screenshot");
    assert!(
        !record.ok,
        "a reported success without a file is not evidence: {:?}",
        record.record
    );
    assert!(
        record.record.path.is_none(),
        "no path may be claimed: {:?}",
        record.record
    );
    assert!(
        record.record.observation.contains("UNAVAILABLE"),
        "{}",
        record.record.observation
    );
    assert!(!run.workspace.join(".hoh/evidence/frame-00.png").exists());
}

/// DR-30: an inline base64 image must be materialized by the runtime before a
/// `path` may be written (this is exactly what `smoke-t3` got from
/// `running_game_capture_frames` and then mishandled).
#[tokio::test]
async fn screenshot_materializes_an_inline_base64_png() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel =
        Arc::new(FixtureChannel::green().with_screenshot(ScreenshotMode::InlineBase64Fallback));
    let run = run_battery(root, channel, 30).await;

    let record = step(&run.records, "screenshot");
    assert!(
        record.ok,
        "the image was carried inline and can be written: {:?}",
        record.record
    );
    assert_eq!(
        record.record.path.as_deref(),
        Some(".hoh/evidence/frame-00.png")
    );
    let png = std::fs::read(run.workspace.join(".hoh/evidence/frame-00.png"))
        .expect("the inline image must have been written to disk");
    assert_eq!(png, inline_png_bytes(), "the decoded bytes must be exact");
}

/// DR-30: the scene tree needs node paths **and** types.
#[tokio::test]
async fn scene_tree_requires_node_paths_and_types() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    // Children exist, but no node carries a `path`/`type`.
    let channel = Arc::new(FixtureChannel::green().with_reply(
        "running_game_get_scene_tree",
        json!({"content": [{"type": "text", "text":
            "{\"tree\": {\"children\": [{\"name\": \"Player\"}]}}"}]}),
    ));
    let run = run_battery_with_script(root, channel, 1, repairing_script()).await;

    let record = step(&run.records, "scene_tree");
    assert!(
        !record.ok,
        "a nameless node list is not a scene tree: {:?}",
        record.record
    );
    assert!(
        record.record.observation.contains("UNAVAILABLE"),
        "{}",
        record.record.observation
    );
    assert!(
        record.record.observation.contains("path") || record.record.observation.contains("type"),
        "the observation must name what was missing: {}",
        record.record.observation
    );
}

// ---------------------------------------------------------------------------
// DR-36 — the evidence has to be visible inside the frozen candidate
// ---------------------------------------------------------------------------

/// DR-36 ①/②: `smoke-t5` wrote a real 4246-byte PNG into
/// `<workspace>/.hoh/evidence/` and the Tester reported "file does not exist"
/// (gap G19) because the candidate view only copied `.hoh/deterministic/**`.
/// The screenshot must be present in the candidate, byte for byte, and the
/// `ExecRecord`'s relative path must resolve inside the candidate root.
#[tokio::test]
async fn the_battery_evidence_is_copied_into_the_frozen_candidate() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green());
    let run = run_battery(root, channel, 30).await;

    let workspace_png = run.workspace.join(".hoh/evidence/frame-00.png");
    let candidate_png = run
        .run_dir
        .join("iter-1/candidate/.hoh/evidence/frame-00.png");
    assert!(
        workspace_png.is_file(),
        "the battery must have produced the real PNG first"
    );
    assert!(
        candidate_png.is_file(),
        "the frozen candidate must carry the evidence (DR-36): {}",
        candidate_png.display()
    );
    assert_eq!(
        std::fs::read(&candidate_png).unwrap(),
        std::fs::read(&workspace_png).unwrap(),
        "the copy must be byte-identical"
    );

    let screenshot = step(&run.records, "screenshot");
    let relative = screenshot
        .record
        .path
        .as_deref()
        .expect("the screenshot names its artifact");
    assert!(
        run.run_dir
            .join("iter-1/candidate")
            .join(relative)
            .is_file(),
        "the Tester resolves `{relative}` against the candidate root"
    );
}

/// DR-36 ③: an oversized evidence file is **still copied** — it is reported, not
/// dropped.  The threshold is a configuration knob (`runtime.max_evidence_bytes`).
#[tokio::test]
async fn an_oversized_evidence_file_is_copied_and_reported() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green());
    // The PNG is 87 bytes; a 10-byte budget makes it oversized.
    let run = run_battery_with_evidence_limit(root, channel, 30, 10).await;

    let candidate_png = run
        .run_dir
        .join("iter-1/candidate/.hoh/evidence/frame-00.png");
    assert!(
        candidate_png.is_file(),
        "an oversized file must still be copied, never silently skipped"
    );
    let size = std::fs::metadata(&candidate_png).unwrap().len();
    assert!(size > 10, "the fixture must really exceed the limit");

    let result: Value =
        serde_json::from_str(&read(&run.run_dir.join("iter-1/result.json"))).unwrap();
    let warnings = result["warnings"].as_array().expect("warnings");
    assert!(
        warnings
            .iter()
            .filter_map(Value::as_str)
            .any(|warning| warning.starts_with("evidence_too_large")
                && warning.contains("frame-00.png")
                && warning.contains(&size.to_string())),
        "the oversize must be reported with its size: {warnings:?}"
    );
}
