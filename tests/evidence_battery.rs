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

/// DR-58: the frozen **real-machine** payloads (`tests/fixtures/dr58`; source
/// files and their sha256 are in `MANIFEST.json`).  Where a reply shape is what
/// the batch corrects, the double must answer with the engine's own bytes
/// rather than with a hand-written idea of the shape.
fn dr58_fixture_raw(name: &str) -> String {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/fixtures/dr58")
        .join(name);
    std::fs::read_to_string(&path).unwrap_or_else(|error| panic!("{path:?}: {error}"))
}

/// DR-58: the exact `payload` envelope the engine answered for `node`, lifted
/// verbatim out of the captured `node_and_collision_assertions` record.
fn real_node_properties(node: &str) -> Value {
    let raw: Value = serde_json::from_str(&dr58_fixture_raw(
        "smoke_t7_node_and_collision_assertions.json",
    ))
    .unwrap();
    raw["calls"]
        .as_array()
        .unwrap()
        .iter()
        .find(|call| {
            call["tool"] == json!("running_game_get_node_properties")
                && call["args"]["node_path"] == json!(node)
        })
        .map(|call| call["payload"].clone())
        .unwrap_or_else(|| panic!("no real payload for node `{node}`"))
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
/// DR-73 ③: the scene tree this fixture reports, with the HUD cells the
/// interaction mode implies (see `FixtureChannel::interaction_properties`).
fn node_tree_payload(hud_label: bool, interaction: InteractionMode) -> Value {
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
        // DR-73 ③: the HUD cell the public specification names.  The interaction
        // window finds the coin counter by the *specification's* wording
        // (`Coins:`), so the green fixture has to carry it — and the visible text
        // node count is unaffected because the added cells are labels too.
        // The interaction mode decides whether the specification's own `Coins:`
        // cell exists at all; `UnreadableCounter` is the counter-example where the
        // counter has no readable shape and F10 must be a gap.
        let cells: Vec<Value> = if interaction == InteractionMode::UnreadableCounter {
            vec![json!({
                "name": "Score",
                "path": "/root/Main/HUD/Score",
                "type": "Label",
                "text": "Score: 0",
                "children": []
            })]
        } else {
            vec![
                json!({
                    "name": "Score",
                    "path": "/root/Main/HUD/Score",
                    "type": "Label",
                    "text": "Lives: 3  Coins: 0  Time: 120",
                    "children": []
                }),
                json!({
                    "name": "Lives",
                    "path": "/root/Main/HUD/Lives",
                    "type": "Label",
                    "text": "Lives: 3",
                    "children": []
                }),
                json!({
                    "name": "Coins",
                    "path": "/root/Main/HUD/Coins",
                    "type": "Label",
                    "text": "Coins: 0",
                    "children": []
                }),
                json!({
                    "name": "Time",
                    "path": "/root/Main/HUD/Time",
                    "type": "Label",
                    "text": "Time: 120",
                    "children": []
                }),
            ]
        };
        hud["children"] = Value::Array(cells);
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

/// DR-30/DR-49: how the mocked `running_game_capture_screenshot` /
/// `running_game_capture_frames` behave.
#[derive(Clone, Copy, PartialEq, Eq)]
enum ScreenshotMode {
    /// DR-49: the contract shape — the engine answers an inline base64 PNG when
    /// the call carries no `save_path` (`running_game_capture.cpp:56-60`).
    InlineImage,
    /// The tool answers `ok` but nothing lands on disk and no image is carried
    /// inline (`smoke-t3` reported `path` for a file that did not exist).
    ReportsSuccessButNoFile,
    /// The primary tool fails and `running_game_capture_frames` answers with an inline
    /// base64 PNG, which the runtime must materialize itself.
    InlineBase64Fallback,
    /// DR-49: the primary tool answers success without an image, while the
    /// `running_game_capture_frames` fallback *does* carry one.  A stale file on
    /// disk used to suppress that fallback.
    SilentPrimaryFramesInline,
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
    /// DR-52: the payload `smoke-t6` actually received —
    /// `{"actions": ["jump","move_left","move_right","spatial_editor/…","ui_*"],
    /// "count": 92}` — an array of **names**.  The pre-DR-52 parser returned an
    /// empty map for it, which is how the diagnostic came to state the opposite
    /// of its own raw record.
    EngineArray,
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

/// DR-58: what the **real** engine answered for the `input_axis` property.
#[derive(Clone, Copy, PartialEq, Eq)]
enum AxisMode {
    /// The double's synthetic reading, which the battery's own movement
    /// scenario uses.
    Value,
    /// DR-69: a reading that **contradicts** the held direction -- the engine
    /// reports `+1` while `move_left` is held.  Nothing else in the battery can
    /// catch this shape: the sampled positions are unaffected, so only the
    /// `INPUT_AXIS_NOT_CHANGED` branch can be red for it.
    WrongSign,
    /// The real `smoke-t7` reading: `input_axis` is `null` in every sample and
    /// the scenario's assert says the node "does not have the property", so the
    /// axis can carry no evidence at all.  Reachability must then come from
    /// `running_game_get_node_properties` — the DR-58 fix under test.
    Unreadable,
}

/// DR-68 ③/⑧: how the replayed `Player` moves, so a fixture can reproduce the
/// two masking shapes separately.
#[derive(Clone, Copy, PartialEq, Eq)]
enum MovementMode {
    /// Each action moves the axis it is supposed to move (the green double).
    Intended,
    /// The **target** axis never moves while the other one does — the shape
    /// gravity produces in `smoke-t8`, where a horizontally dead `move_left`
    /// still changed `y` and the whole-vector predicate called it movement.
    OtherAxisOnly,
    /// Nothing moves at all (`smoke-t3`/`smoke-t5`).
    None,
}

/// DR-73 ③: what the fixture reports for the **interaction** observables — the
/// coin counter and the goal flag.
///
/// `smoke-t10` is the `NoPickup` × `NoWin` cell: the Developer's `coin.gd`
/// connected `body_entered` and the `goal.gd` connected `body_entered` too, the
/// player physically swept both coins in the rightward window, and the HUD still
/// read `Coins: 0` for the whole round with `Goal.reached` never true.  A double
/// that always reported the pickup could not have caught that.
#[derive(Clone, Copy, PartialEq, Eq)]
enum InteractionMode {
    /// The green double: a coin is really picked up and the goal is reachable.
    Working,
    /// The coin counter never grows and the goal flag never turns — the round's
    /// own state.
    NoPickupNoWin,
    /// A level that lets the player sweep every coin but puts the goal past the
    /// end of the traversable ground.
    NoWin,
    /// A HUD with no `Coins:` label at all.
    UnreadableCounter,
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
    /// DR-30/DR-33: whether (and how) the replayed `Player` actually moves.
    movement: MovementMode,
    screenshot: ScreenshotMode,
    input_actions: InputActionsMode,
    /// DR-35: the game-process input channel.
    game_input: GameInputMode,
    /// DR-58: how the `input_axis` property is read.
    axis: AxisMode,
    /// DR-68 ③: the actions the **game process** is really holding, in press
    /// order.  The pre-DR-68 double kept a single bool, so it could not model
    /// the defect at all: once `move_right` had been injected it silently stayed
    /// held, and `Input.get_axis("move_left","move_right")` returned 0 for every
    /// later direction.
    held_in_game: Mutex<Vec<String>>,
    /// The action of the most recent `editor_simulate_input_action`, so `running_game_get_node_property_samples`
    /// (which does not name an action) can answer plausibly.
    last_action: Mutex<String>,
    /// DR-73 ③: is the interaction window currently driving?  `input_replay` also
    /// presses `move_right`, and a double that let those windows fill the counter
    /// would credit the interaction step with coins it never swept.
    driving: Arc<std::sync::atomic::AtomicBool>,
    /// DR-73 ③: how many times the interaction window has started a drive — the
    /// window resets its own starting condition each time it runs.
    drives: Mutex<u32>,
    /// DR-73 ③: the drive generation the fixture has already applied.
    last_drive: Mutex<u32>,
    /// DR-73 ③: what the interaction observables report.
    interaction: InteractionMode,
    /// DR-73 ③: how many sweeps have happened in this session (bumped by the
    /// game-process replay when `interaction` is `Working`).
    interactions: Mutex<u32>,
    /// DR-73 ③: the furthest right the sampled `Player` series has been.
    max_x: Mutex<f64>,
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
            movement: MovementMode::Intended,
            screenshot: ScreenshotMode::InlineImage,
            input_actions: InputActionsMode::Bound,
            game_input: GameInputMode::Ok,
            axis: AxisMode::Value,
            held_in_game: Mutex::new(Vec::new()),
            last_action: Mutex::new("move_right".to_string()),
            driving: Arc::new(std::sync::atomic::AtomicBool::new(false)),
            drives: Mutex::new(0),
            last_drive: Mutex::new(0),
            interaction: InteractionMode::Working,
            interactions: Mutex::new(0),
            max_x: Mutex::new(60.0),
        }
    }

    /// DR-73 ③: choose what the interaction observables report.
    fn with_interaction(mut self, mode: InteractionMode) -> Self {
        self.interaction = mode;
        self
    }

    /// DR-73 ③: one game-process sweep of `move_right`.  The player travels far
    /// enough to reach the green level's coin and goal but not an
    /// `unreachable` one.
    fn sweep_in_game(&self, action: &str) {
        if action != "move_right" || !self.driving() {
            return;
        }
        // The interaction window starts a **fresh** drive each time it runs, so
        // the game-side position advances from the same starting condition the
        // window observed.  The generation is bumped by the window's own goal
        // read, which is its last read before it starts driving.
        let generation = self.drives();
        {
            let mut last = self.last_drive.lock().unwrap();
            if *last != generation {
                *last = generation;
                *self.max_x.lock().unwrap() = 60.0;
            }
        }
        let mut max_x = self.max_x.lock().unwrap();
        *max_x += 260.0;
        let swept = *max_x > 300.0;
        drop(max_x);
        // `NoWin` still picks the coin up (that is what makes it a *separate*
        // failure); only `NoPickupNoWin` is the round's own "swept but nothing
        // happened" state.
        if swept && self.interaction != InteractionMode::NoPickupNoWin {
            let mut interactions = self.interactions.lock().unwrap();
            *interactions += 1;
        }
    }

    fn driving(&self) -> bool {
        self.driving.load(std::sync::atomic::Ordering::SeqCst)
    }

    /// DR-73 ③: how many sweeps have happened.
    fn interactions(&self) -> u32 {
        *self.interactions.lock().unwrap()
    }

    /// DR-73 ③: how many drives the window started.
    fn drives(&self) -> u32 {
        *self.drives.lock().unwrap()
    }
    /// DR-73 ③: arm the drive — the interaction step's own switch, so the
    /// `input_replay` windows before it cannot credit it with a sweep.  The
    /// window arms itself through the `Goal` property read that precedes its
    /// drive, which is the last thing it does before the batches start.
    fn arm_drive(&self) {
        self.driving
            .store(true, std::sync::atomic::Ordering::SeqCst);
        let mut drives = self.drives.lock().unwrap();
        *drives += 1;
    }

    /// DR-73 ③: has the player been driven far enough to reach the goal?
    fn goal_reached(&self) -> bool {
        let goal_x = match self.interaction {
            InteractionMode::NoWin | InteractionMode::NoPickupNoWin => 100_000.0,
            _ => 260.0,
        };
        *self.max_x.lock().unwrap() >= goal_x
    }

    /// DR-73 ③: the HUD label a node read is about, or `None` for a node the
    /// interaction fixture says nothing about.
    fn interaction_label(&self, node_path: &str) -> Option<String> {
        let name = node_path.rsplit('/').next().unwrap_or(node_path);
        match name {
            "Coins" if self.interaction != InteractionMode::UnreadableCounter => {
                Some(format!("Coins: {}", self.interactions()))
            }
            "Lives" => Some("Lives: 3".to_string()),
            "Score" if self.interaction != InteractionMode::UnreadableCounter => Some(format!(
                "Lives: 3  Coins: {}  Time: 120",
                self.interactions()
            )),
            "Time" => Some("Time: 120".to_string()),
            "Result" => Some(String::new()),
            _ => None,
        }
    }

    /// DR-73 ③: the synthetic `running_game_get_node_properties` reply for the
    /// interaction reads, or `None` when the node is not one of them (the caller
    /// then answers with the captured real payload, so the pre-DR-73 checks keep
    /// their own evidence).
    fn interaction_properties(&self, node_path: &str) -> Option<Value> {
        let name = node_path.rsplit('/').next().unwrap_or(node_path);
        // The engine resolves a read to the node's own absolute path (DR-58);
        // the fixture answers in the same shape so a caller can tell a resolved
        // read from a guessed one.
        let resolved = format!("/root/Main/{name}");
        if let Some(label) = self.interaction_label(name) {
            let inner = json!({
                "node_path": resolved,
                "properties": {"text": label, "visible": true},
                "type": "Label",
            });
            return Some(json!({"content": [{"type": "text", "text": inner.to_string()}]}));
        }
        match name {
            "Goal" => {
                // `smoke-t10`'s shape: the flag is at x=6400 while the player's
                // reachable maximum is about 320.
                let position_x = match self.interaction {
                    InteractionMode::NoWin => 6400.0,
                    _ => 260.0,
                };
                let inner = json!({
                    "node_path": resolved,
                    "properties": {
                        "reached": self.goal_reached(),
                        "position": {"x": position_x, "y": 280.0},
                    },
                    "type": "Area2D",
                });
                Some(json!({"content": [{"type": "text", "text": inner.to_string()}]}))
            }
            "Player" => {
                let inner = json!({
                    "node_path": resolved,
                    "properties": {"position": {"x": 60.0, "y": 283.999}, "facing": 1},
                    "type": "CharacterBody2D",
                });
                Some(json!({"content": [{"type": "text", "text": inner.to_string()}]}))
            }
            _ => None,
        }
    }

    /// DR-73 ③: the engine's `running_game_assert_node_state` answer for the HUD
    /// counter's `text`, judged against the **live** label the properties reader
    /// would return — the same discipline [`sample_positions`] applies to the
    /// position assertion.
    fn assert_text(&self, node_path: &str, args: &Value) -> Value {
        let name = node_path.rsplit('/').next().unwrap_or(node_path);
        let label = self
            .interaction_label(name)
            .unwrap_or_else(|| "<no label>".to_string());
        let actual = json!(label);
        let expected = args.get("expected").cloned().unwrap_or(Value::Null);
        let operator = args
            .get("operator")
            .and_then(Value::as_str)
            .unwrap_or("eq")
            .to_string();
        let passed = match operator.as_str() {
            "neq" => actual != expected,
            _ => actual == expected,
        };
        let inner = json!({
            "assertion": "node_state",
            "node_path": node_path,
            "resolved_node_path": format!("/root/Main/{name}"),
            "property": "text",
            "operator": operator,
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "reason": format!("expected text {operator} {expected}, found {actual}"),
        });
        json!({"content": [{"type": "text", "text": inner.to_string()}]})
    }

    /// DR-73 ③: the same for the goal's `reached` flag.
    fn assert_reached(&self, node_path: &str, args: &Value) -> Value {
        let name = node_path.rsplit('/').next().unwrap_or(node_path);
        let actual = json!(self.goal_reached());
        let expected = args.get("expected").cloned().unwrap_or(Value::Null);
        let operator = args
            .get("operator")
            .and_then(Value::as_str)
            .unwrap_or("eq")
            .to_string();
        let passed = match operator.as_str() {
            "neq" => actual != expected,
            _ => actual == expected,
        };
        let inner = json!({
            "assertion": "node_state",
            "node_path": node_path,
            "resolved_node_path": format!("/root/Main/{name}"),
            "property": "reached",
            "operator": operator,
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "reason": format!("expected reached {operator} {expected}, found {actual}"),
        });
        json!({"content": [{"type": "text", "text": inner.to_string()}]})
    }

    /// DR-68 ③: the game's `Input.get_axis("move_left","move_right")`, computed
    /// from what the game process is really holding.  **Both held ⇒ 0** — that
    /// single line is the `smoke-t8` artifact.
    fn game_axis(&self) -> f64 {
        let held = self.held_in_game.lock().unwrap();
        let left = held.iter().any(|action| action == "move_left");
        let right = held.iter().any(|action| action == "move_right");
        match (left, right) {
            (true, true) | (false, false) => 0.0,
            (false, true) => 1.0,
            (true, false) => -1.0,
        }
    }

    fn press_in_game(&self, action: &str) {
        let mut held = self.held_in_game.lock().unwrap();
        if !held.iter().any(|existing| existing == action) {
            held.push(action.to_string());
        }
        *self.last_action.lock().unwrap() = action.to_string();
    }

    fn release_in_game(&self, action: &str) {
        self.held_in_game
            .lock()
            .unwrap()
            .retain(|existing| existing != action);
    }

    fn anything_held(&self) -> bool {
        !self.held_in_game.lock().unwrap().is_empty()
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

    /// DR-58: choose what the `input_axis` reading looks like.
    fn with_axis_mode(mut self, mode: AxisMode) -> Self {
        self.axis = mode;
        self
    }

    fn with_moving(mut self, moving: bool) -> Self {
        self.movement = if moving {
            MovementMode::Intended
        } else {
            MovementMode::None
        };
        self
    }

    /// DR-68 ⑧: only the *other* axis moves — the masking shape gravity gives.
    fn with_movement(mut self, movement: MovementMode) -> Self {
        self.movement = movement;
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

    /// Every recorded call, in arrival order — used by the DR-52 parameter-shape
    /// audit.
    fn all_calls(&self) -> Vec<(String, Value)> {
        self.calls.lock().unwrap().clone()
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

/// DR-49: the engine's reply when the call carries **no** `save_path` — the
/// picture travels inline, exactly as `running_game_capture.cpp:120-127` writes
/// it.
fn screenshot_inline_payload() -> Value {
    let inner = json!({
        "format": "png",
        "height": 1,
        "width": 1,
        "image_base64": INLINE_PNG_TEXT,
    });
    json!({"content": [{"type": "text", "text": inner.to_string()}]})
}

/// DR-49: the `-32602` the engine answers when `save_path` is not a `res://` or
/// `user://` path (`running_game_capture.cpp:62-63`; the message is the one
/// `smoke-t6` captured three times).
fn invalid_save_path(save_path: &str) -> McpError {
    McpError::new(
        -32602,
        format!("Parameter 'save_path' must start with 'res://' or 'user://', got '{save_path}'"),
    )
}

/// DR-58: the `-32602` the real game-scope runner answers for **any**
/// `scene_path` value, verbatim from
/// `tests/fixtures/dr58/smoke_t7_input_channel_probe.json` (`'current'`) and the
/// captured experiment (`'main'`, `'res://scenes/main.tscn'`).
fn scene_path_refusal(value: &str) -> String {
    format!(
        "Parameter 'scene_path' ('{value}') is not supported by the game-scope runner: the \
         migration source used it to make the *editor* play a scene before the steps ran, and this \
         tool runs inside the game process that is already running. Use editor_play_scene (editor \
         endpoint) first, then run the scenario against the running game"
    )
}

/// DR-58: the real accepted `running_game_run_test_scenario` reply, frozen from
/// `smoke-t7` — `in_input_map: true` / `injected: 1` for the input step, and no
/// `observed`/`actual` for the `input_axis` assert, because the node does not
/// have that property.
fn real_scenario_payload() -> Value {
    let entry: Value =
        serde_json::from_str(&dr58_fixture_raw("smoke_t7_sc_04_scene_path_omitted.json")).unwrap();
    json!({
        "content": [{"type": "text", "text": entry["parsed"]["result"]["content"][0]["text"].clone()}]
    })
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

/// A `running_game_get_node_property_samples` recording: the captured `Player`
/// that never moves (`smoke-t3`: `(60.0, 283.999)` for all 60 frames), one that
/// responds to `action` on the axis that action is supposed to move, or one
/// where only the other axis moves (`smoke-t8`'s gravity).
///
/// DR-68 ③: `axis` is the game's real
/// `Input.get_axis("move_left","move_right")`.  When it is `0` while a move
/// action is held — both directions held at once, the `smoke-t8` artifact — the
/// horizontal position **cannot** change, and only gravity moves `y`.
fn monitor_payload(action: &str, frames: u64, movement: MovementMode, axis: f64) -> Value {
    let mut samples = Vec::new();
    for (index, (x, y)) in sample_positions(action, frames, movement, axis)
        .into_iter()
        .enumerate()
    {
        samples.push(json!({
            "frame": index,
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

/// DR-69 ④: the per-frame `Player.position` a replay window really observes.
///
/// Extracted from [`monitor_payload`] so the `running_game_assert_node_state`
/// double reports the **same** reading the sampler returns: the assertion is
/// about the position the replayed action produced, and a double whose two
/// answers disagreed would make the test prove nothing.
fn sample_positions(
    action: &str,
    frames: u64,
    movement: MovementMode,
    axis: f64,
) -> Vec<(f64, f64)> {
    let mut samples = Vec::new();
    for frame in 0..frames {
        let frame = frame as f64;
        let (x, y) = match movement {
            MovementMode::None => (60.0, 283.998992919922),
            MovementMode::OtherAxisOnly => (60.0, 283.0 + frame),
            MovementMode::Intended if action == "jump" => (60.0, (frame * 2.0) % 80.0),
            MovementMode::Intended if action == "move_left" => {
                if axis < 0.0 {
                    (100.0 - frame, 283.0)
                } else {
                    // Dead axis: the x position is pinned and gravity moves y.
                    (100.0, 283.0 + frame)
                }
            }
            MovementMode::Intended => {
                if axis > 0.0 {
                    (frame * 2.0, 283.0)
                } else {
                    (60.0, 283.0 + frame)
                }
            }
        };
        samples.push((x, y));
    }
    samples
}

/// The `editor_get_input_actions` reply for the requested mode.
fn input_actions_payload(mode: InputActionsMode) -> Value {
    if mode == InputActionsMode::RealEditorMap {
        // The verbatim payload the battery collected in `smoke-t5`: the editor's
        // own InputMap, listing only the engine's built-in `ui_*` actions.
        let real: Value = fixture("input_replay_smoke_t5.json");
        return real["calls"][0]["payload"].clone();
    }
    if mode == InputActionsMode::EngineArray {
        // DR-52: the verbatim shape of the `smoke-t6` record — an array of
        // action **names**, the three project actions first.
        let inner = json!({
            "actions": [
                "jump", "move_left", "move_right",
                "spatial_editor/freelook_up", "ui_accept", "ui_cancel",
            ],
            "count": 6,
        });
        return json!({"content": [{"type": "text", "text": inner.to_string()}]});
    }
    let actions = match mode {
        InputActionsMode::Bound => json!([
            {"name": "move_left", "keys": ["A", "Left"]},
            {"name": "move_right", "keys": ["D", "Right"]},
            {"name": "jump", "keys": ["Space", "W"]},
        ]),
        InputActionsMode::Missing => json!([{"name": "ui_accept", "keys": ["Enter"]}]),
        InputActionsMode::RealEditorMap | InputActionsMode::EngineArray => {
            unreachable!("handled above")
        }
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

/// DR-50: the engine's answer to a body that has **no** `return`, verbatim from
/// `running_game_script_execution.cpp:399-404` (`smoke-t6` received this four
/// times, once per value-reading probe).
fn void_script_payload() -> Value {
    let inner = json!({
        "note": "The body returned no value (result is null / result_type \"Nil\"). This is not \
                 evidence that the body had an effect: it is also what a body with no `return`, \
                 and what a body whose statements were all no-ops, answer.",
        "result": null,
        "result_type": "Nil",
    });
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
            "editor_open_scene" => {
                json!({"content": [{"type": "text", "text": "{\"opened\": true}"}]})
            }
            "project_read_scene_file_content" => json!({
                "content": [{"type": "text", "text": json!({"content": VALID_SCENE}).to_string()}]
            }),
            "editor_get_errors" => fixture("editor_errors_clean.json"),
            "editor_play_scene" => fixture("play_scene_ok.json"),
            "running_game_get_scene_tree" => node_tree_payload(self.hud_label, self.interaction),
            "editor_get_input_actions" => input_actions_payload(self.input_actions),
            "running_game_capture_screenshot" => {
                // DR-49: the double enforces the engine's **value domain** before
                // it enforces anything else, so a regression to a filesystem
                // `save_path` cannot pass the battery unnoticed.
                if let Some(save_path) = args.get("save_path").and_then(Value::as_str) {
                    if !(save_path.starts_with("res://") || save_path.starts_with("user://")) {
                        return Err(invalid_save_path(save_path).into());
                    }
                }
                match self.screenshot {
                    ScreenshotMode::InlineImage => screenshot_inline_payload(),
                    ScreenshotMode::ReportsSuccessButNoFile
                    | ScreenshotMode::SilentPrimaryFramesInline => screenshot_ok_payload(),
                    ScreenshotMode::InlineBase64Fallback => {
                        return Err(captured_error("screenshot_failure.txt").into());
                    }
                }
            }
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
            //
            // DR-50: the double models the engine's *body* semantics
            // (`running_game_script_execution.cpp:57-82`): `code` is compiled
            // into a function body, so a body with **no** `return` answers
            // `{"result":null,"result_type":"Nil"}` and nothing can be read from
            // it.  A mutation stays a statement; a reading needs its `return`.
            "running_game_execute_gdscript" => {
                if self.game_input == GameInputMode::ProbeFails {
                    return Err(captured_error("game_script_input_unreachable.txt").into());
                }
                let code = args.get("code").and_then(Value::as_str).unwrap_or("");
                let bound = self.game_input == GameInputMode::Ok;
                let returns_a_value = code.trim_start().starts_with("return ");
                // The mutation marker is `Input.action_press(`, not `action_press`:
                // `Input.is_action_pressed(...)` contains the latter as a substring.
                if code.contains("Input.action_press(") {
                    self.press_in_game("legacy_script");
                    void_script_payload()
                } else if code.contains("Input.action_release(") {
                    self.release_in_game("legacy_script");
                    self.held_in_game.lock().unwrap().clear();
                    void_script_payload()
                } else if !returns_a_value {
                    // A value-reading probe without `return` is what `smoke-t6`
                    // sent: the engine answers Nil, so the reading is absent.
                    void_script_payload()
                } else if code.contains("has_action") {
                    game_script_payload(if bound { "true" } else { "false" })
                } else if code.contains("get_axis") {
                    let reading = if bound { self.game_axis() } else { 0.0 };
                    game_script_payload(&format!("{reading}"))
                } else if code.contains("is_action_pressed") {
                    game_script_payload(if bound && self.anything_held() {
                        "true"
                    } else {
                        "false"
                    })
                } else if code.contains("position") {
                    let moved =
                        bound && self.anything_held() && self.movement == MovementMode::Intended;
                    let x = if moved { 80.0 } else { 60.0 };
                    game_script_payload(&format!("{x},283.999"))
                } else {
                    panic!("FixtureChannel got an unexpected game script: {code}")
                }
            }
            // DR-54: the contract's semantic input API.  The battery injects an
            // action by recording and replaying it, so the double decides what
            // the game's `InputMap` holds exactly as it does for the old script
            // probe: `GameInputMode::ActionMissing` refuses the action.
            "running_game_create_input_recording" => {
                if self.game_input == GameInputMode::ProbeFails {
                    // DR-35/DR-54: the same channel failure `smoke-t5` met — the
                    // game-process input API is not reachable, so nothing can be
                    // concluded about the InputMap.
                    return Err(captured_error("game_script_input_unreachable.txt").into());
                }
                json!({"content": [{"type": "text", "text": "{\"recording\": true}"}]})
            }
            "running_game_stop_input_recording" => {
                if self.game_input == GameInputMode::ProbeFails {
                    return Err(captured_error("game_script_input_unreachable.txt").into());
                }
                json!({"content": [{"type": "text", "text": "{\"events\": [], \"count\": 0}"}]})
            }
            "running_game_play_input_recording" => {
                if self.game_input == GameInputMode::ProbeFails {
                    return Err(captured_error("game_script_input_unreachable.txt").into());
                }
                if self.game_input == GameInputMode::ActionMissing {
                    let action = args
                        .get("events")
                        .and_then(Value::as_array)
                        .and_then(|events| events.first())
                        .and_then(|event| event.get("action"))
                        .and_then(Value::as_str)
                        .unwrap_or("")
                        .to_string();
                    return Err(McpError::new(
                        -32602,
                        format!("ACTION_NOT_BOUND: no such action in this InputMap: `{action}`"),
                    )
                    .into());
                }
                let action = args
                    .get("events")
                    .and_then(Value::as_array)
                    .and_then(|events| events.first())
                    .and_then(|event| event.get("action"))
                    .and_then(Value::as_str)
                    .unwrap_or("move_right")
                    .to_string();
                // DR-68 ③: an event really is a press **or** a release.  The old
                // double always answered `pressed = true`, which is precisely why
                // it could not show that the previous direction stayed held.
                let pressed = args
                    .get("events")
                    .and_then(Value::as_array)
                    .and_then(|events| events.first())
                    .and_then(|event| event.get("pressed"))
                    .and_then(Value::as_bool)
                    .unwrap_or(true);
                if pressed {
                    self.press_in_game(&action);
                } else {
                    self.release_in_game(&action);
                }
                json!({"content": [{"type": "text", "text": "{\"replayed\": true, \"count\": 1}"}]})
            }
            "running_game_run_test_scenario" => {
                if self.game_input == GameInputMode::ProbeFails {
                    return Err(captured_error("game_script_input_unreachable.txt").into());
                }
                if self.game_input == GameInputMode::ActionMissing {
                    return Err(McpError::new(
                        -32602,
                        "ACTION_NOT_BOUND: no such action in this InputMap: `move_right`",
                    )
                    .into());
                }
                // DR-58: the real game-scope runner refuses **every**
                // `scene_path` value — captured verbatim in
                // `tests/fixtures/dr58/smoke_t7_*` (see the manifest).  The
                // double enforces the engine's own answer, so a regression to
                // "send a scene_path" cannot pass the battery unnoticed.
                if let Some(scene_path) = args.get("scene_path").and_then(Value::as_str) {
                    return Err(McpError::new(-32602, scene_path_refusal(scene_path)).into());
                }
                // DR-58: when the axis is unreadable the double answers the
                // engine's **real** frozen reply — `in_input_map: true,
                // injected: 1`, and no `observed`/`actual` reading at all.
                if self.axis == AxisMode::Unreadable {
                    return Ok(ToolResult {
                        ok: true,
                        payload: real_scenario_payload(),
                    });
                }
                let action = args
                    .get("steps")
                    .and_then(Value::as_array)
                    .and_then(|steps| {
                        steps
                            .iter()
                            .find(|step| step["type"] == json!("input"))
                            .and_then(|step| step.get("action"))
                    })
                    .and_then(Value::as_str)
                    .unwrap_or("move_right")
                    .to_string();
                // DR-68 ③: the scenario's `input` step carries `pressed` too, and
                // a release step must really release.
                let pressed = args
                    .get("steps")
                    .and_then(Value::as_array)
                    .and_then(|steps| {
                        steps
                            .iter()
                            .find(|step| step["type"] == json!("input"))
                            .and_then(|step| step.get("pressed"))
                    })
                    .and_then(Value::as_bool)
                    .unwrap_or(true);
                if pressed {
                    self.press_in_game(&action);
                } else {
                    self.release_in_game(&action);
                }
                let bound = self.game_input == GameInputMode::Ok;
                let axis = if bound { self.game_axis() } else { 0.0 };
                // DR-73 ③: a scenario really drives the game for the frames it
                // waits, so a sweep happens here too — the interaction window
                // drives through this same scenario runner.
                if bound {
                    self.sweep_in_game(&action);
                }
                let inner = json!({
                    "observed_axis": axis,
                    "results": [
                        {"index": 0, "type": "input", "action": action, "ok": true},
                        {"index": 1, "type": "wait", "ok": true, "waited_seconds": 0.0},
                        {"index": 2, "type": "assert", "node_path": "Player",
                         "property": "input_axis", "operator": "eq",
                         "expected": 0, "observed": axis, "ok": true},
                    ],
                });
                json!({"content": [{"type": "text", "text": inner.to_string()}]})
            }
            "running_game_get_node_property_samples" => {
                if self.game_input == GameInputMode::ProbeFails {
                    // The game-process reading itself is unavailable.
                    return Err(captured_error("game_script_input_unreachable.txt").into());
                }
                let action = self.last_action.lock().unwrap().clone();
                let frames = args
                    .get("frame_count")
                    .and_then(Value::as_u64)
                    .unwrap_or(60);
                // DR-54: the axis has its own semantic sample shape; the
                // classification reads it from the **last** sample.
                let properties: Vec<String> = args
                    .get("properties")
                    .and_then(Value::as_array)
                    .map(|items| {
                        items
                            .iter()
                            .filter_map(Value::as_str)
                            .map(ToOwned::to_owned)
                            .collect()
                    })
                    .unwrap_or_default();
                if properties.iter().any(|name| name == "input_axis") {
                    if self.axis == AxisMode::Unreadable {
                        // DR-58: the engine's real `smoke-t7` sample —
                        // `{"frame_count":1,"node_path":"/root/Main/Player",
                        //   "samples":[{"frame":0,"input_axis":null}]}`.
                        let inner = json!({
                            "node_path": "/root/Main/Player",
                            "frame_count": 1,
                            "samples": [{"frame": 0, "input_axis": null}],
                        });
                        return Ok(ToolResult {
                            ok: true,
                            payload: json!({"content": [{"type": "text", "text": inner.to_string()}]}),
                        });
                    }
                    // DR-68 ③: the reading is the game's real axis — both
                    // directions held ⇒ `0`, which is what made `smoke-t8`'s
                    // `move_left` window immobile whichever implementation it had.
                    let axis = if self.axis == AxisMode::WrongSign {
                        // DR-69 (DEF-1): a reading that contradicts `move_left`.
                        1.0
                    } else if self.game_input == GameInputMode::Ok {
                        self.game_axis()
                    } else {
                        0.0
                    };
                    let inner = json!({
                        "node_path": "Player",
                        "frame_count": 1,
                        "samples": [{"frame": 0, "properties": {"input_axis": axis}}],
                    });
                    return Ok(ToolResult {
                        ok: true,
                        payload: json!({"content": [{"type": "text", "text": inner.to_string()}]}),
                    });
                }
                let moves = self.game_input == GameInputMode::Ok;
                // DR-73 ③: while the interaction window is driving, the sampled
                // series is the game's own rightward travel — the double models
                // it as a monotone ramp so the recorded `player max x` reflects
                // the drive instead of whichever action the replay happened to
                // hold.  The ramp ends at the position the fixture's own drive
                // state says the player reached.
                if self.driving() && moves {
                    let end = *self.max_x.lock().unwrap();
                    let start = (end - 260.0).max(0.0);
                    let mut samples = Vec::new();
                    for frame in 0..frames {
                        let progress = if frames <= 1 {
                            1.0
                        } else {
                            frame as f64 / (frames - 1) as f64
                        };
                        let x = start + (end - start) * progress;
                        samples.push(json!({"frame": frame, "position": {"x": x, "y": 283.0}}));
                    }
                    let inner = json!({
                        "frame_count": frames,
                        "node_path": "Player",
                        "samples": samples,
                    });
                    return Ok(ToolResult {
                        ok: true,
                        payload: json!({"content": [{"type": "text", "text": inner.to_string()}]}),
                    });
                }
                monitor_payload(
                    &action,
                    frames,
                    self.movement,
                    if moves { self.game_axis() } else { 0.0 },
                )
            }
            // DR-58: the engine's **real** reply, verbatim from `smoke-t7`:
            // `{"node_path":"/root/Main/…","properties":{…},"type":…}` — there is
            // no top-level `name`, so the old predicate (which read one) is a
            // constant `false` here.  Driven by the frozen bytes on purpose.
            // DR-69 ④: the positional assertion, in the engine's own verdict shape
            // (`running_game_assertion.cpp:95-162`): `node_path`, `property`,
            // `operator`, `expected` in; `passed` + `actual` + `reason` out.  A
            // property the node does not have is `-32001`, which is what makes an
            // assertion on a missing property diagnosable instead of a
            // `passed:false` against `null`.
            "running_game_assert_node_state" => {
                let node_path = args
                    .get("node_path")
                    .and_then(Value::as_str)
                    .unwrap_or("")
                    .to_string();
                let property = args
                    .get("property")
                    .and_then(Value::as_str)
                    .unwrap_or("")
                    .to_string();
                if property != "position" {
                    // DR-73 ③: the interaction window asserts on the HUD
                    // counter's `text` and on the goal's `reached` flag, so the
                    // double answers those two as well.  Every other property
                    // keeps the engine's real `-32001` answer, which is what a
                    // probe on a property the node does not have really gets.
                    return match property.as_str() {
                        "text" => Ok(ToolResult {
                            ok: true,
                            payload: self.assert_text(&node_path, &args),
                        }),
                        "reached" => Ok(ToolResult {
                            ok: true,
                            payload: self.assert_reached(&node_path, &args),
                        }),
                        _ => Err(hof_rs::tools::mcp::McpError::new(
                            -32001,
                            format!(
                                "Property '{property}' on node '{node_path}': Use \
                                 running_game_get_node_properties to list the properties the node \
                                 really has"
                            ),
                        )
                        .into()),
                    };
                }
                let operator = args
                    .get("operator")
                    .and_then(Value::as_str)
                    .unwrap_or("eq")
                    .to_string();
                let action = self.last_action.lock().unwrap().clone();
                let axis = if self.game_input == GameInputMode::Ok {
                    self.game_axis()
                } else {
                    0.0
                };
                let positions = sample_positions(&action, 60, self.movement, axis);
                let last = positions.last().copied().unwrap_or((0.0, 0.0));
                let expected = args.get("expected").cloned().unwrap_or(Value::Null);
                let actual = json!({"x": last.0, "y": last.1});
                let passed = match operator.as_str() {
                    "neq" => actual != expected,
                    "gt" => last.0 > expected.as_f64().unwrap_or(0.0),
                    "lt" => last.0 < expected.as_f64().unwrap_or(0.0),
                    _ => actual == expected,
                };
                let reason = format!("expected {property} {operator} {expected}, found {actual}");
                let inner = json!({
                    "assertion": "node_state",
                    "node_path": node_path,
                    "resolved_node_path": "/root/Main/Player",
                    "property": property,
                    "operator": operator,
                    "expected": expected,
                    "actual": actual,
                    "passed": passed,
                    "reason": reason,
                });
                json!({"content": [{"type": "text", "text": inner.to_string()}]})
            }
            "running_game_get_node_properties" => {
                let node_path = args["node_path"].as_str().unwrap_or("").to_string();
                let name = node_path.rsplit('/').next().unwrap_or(&node_path);
                // DR-73 ③: the interaction window reads `Goal`'s flag last before
                // it starts driving, so that read is the point at which the
                // game-side drive state is armed fresh for this window.
                if name == "Goal" {
                    self.arm_drive();
                }
                match self.interaction_properties(&node_path) {
                    Some(payload) => payload,
                    None => real_node_properties(&node_path),
                }
            }
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
            "editor_stop_scene" => {
                json!({"content": [{"type": "text", "text": "{\"stopped\": true}"}]})
            }
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

/// DR-68 ④: run one iteration that is **expected to fail after the freeze**, and
/// hand back the round's error plus its `result.json`.  `run_battery_opts`
/// unwraps the result; this one must not, because the failure *is* the subject.
async fn run_failing_battery(
    root: &Path,
    channel: Arc<FixtureChannel>,
    ready_timeout_seconds: u64,
    script: Vec<FakeStep>,
    max_schema_retries: u32,
) -> (anyhow::Error, PathBuf) {
    let mut cfg: HohConfig = test_config(root, 1);
    cfg.runtime.spec = root.join("spec.md");
    cfg.runtime.max_schema_retries = max_schema_retries;
    let spec = write_spec(root);
    let harness = FakeHarness::new(script);
    let adapter = godot_adapter(root, ready_timeout_seconds);
    let run_dir = cfg.runtime.runs_dir.join("run-1");
    let orchestrator = hof_rs::runtime::run_loop::Orchestrator {
        harness: Box::new(harness),
        adapter: Box::new(adapter),
        tools: channel,
        cfg,
        ablation: Ablation::default(),
        force_init: true,
        start_state: hof_rs::runtime::start_state::StartState::as_is(),
    };
    let error = hof_rs::runtime::run_loop::run(&orchestrator, &spec, "run-1")
        .await
        .expect_err("this scenario is the failure path");
    (error, run_dir)
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
            "interaction_evidence",
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
        raw.lines()
            .any(|line| line.contains("running_game_get_scene_tree")),
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
// DR-58 — the real `running_game_get_node_properties` reply shape (G20)
// ---------------------------------------------------------------------------

/// DR-58 ③/G20: the **real** payloads the engine sent for `Player` / `Goal` /
/// `HUD` must be scored as resolved nodes, not as `missing`.  The double answers
/// with the engine's own bytes, so this is the exact failure `smoke-t7`'s QA
/// recorded as gap G20.
#[tokio::test]
async fn real_node_properties_payloads_are_not_scored_as_missing() {
    let temp = tempfile::tempdir().unwrap();
    let channel = Arc::new(FixtureChannel::green());
    let run = run_battery(temp.path(), channel, 30).await;

    let record = step(&run.records, "node_and_collision_assertions");
    assert!(record.ok, "{:?}", record.record);
    for node in ["Player", "Goal", "HUD"] {
        assert!(
            record.record.observation.contains(&format!("{node}=ok")),
            "{node} must be read as resolved: {}",
            record.record.observation
        );
        assert!(
            !record
                .record
                .observation
                .contains(&format!("{node}=missing")),
            "{node} was scored missing on a successful payload: {}",
            record.record.observation
        );
    }

    // …and it is really the engine's shape that was judged, not a repaired one.
    let raw: Value = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/raw/node_and_collision_assertions.json"),
    ))
    .unwrap();
    for node in ["Player", "Goal", "HUD"] {
        let call = raw["calls"]
            .as_array()
            .unwrap()
            .iter()
            .find(|call| {
                call["tool"] == json!("running_game_get_node_properties")
                    && call["args"]["node_path"] == json!(node)
            })
            .unwrap_or_else(|| panic!("no recorded call for {node}"));
        assert_eq!(call["ok"], json!(true), "{call}");
        let payload: Value =
            serde_json::from_str(call["payload"]["content"][0]["text"].as_str().unwrap()).unwrap();
        assert!(
            payload.get("name").is_none(),
            "the real reply has no top-level name: {payload}"
        );
        assert!(payload["properties"].is_object(), "{payload}");
    }
}

/// DR-58 ④ — the counterexample at the step level: a payload that does **not**
/// prove a resolved node must still be `missing` and must still fail the step.
/// A predicate that was made constant `true` to make the round look better would
/// pass the test above and fail here.
#[tokio::test]
async fn a_malformed_node_properties_payload_is_still_scored_as_missing() {
    let temp = tempfile::tempdir().unwrap();
    let channel = Arc::new(FixtureChannel::green().with_reply(
        "running_game_get_node_properties",
        // Exactly the shape the pre-DR-58 code read: a top-level `name`.
        json!({"content": [{"type": "text", "text": "{\"name\":\"Player\"}"}]}),
    ));
    let run = run_battery(temp.path(), channel, 30).await;

    let record = step(&run.records, "node_and_collision_assertions");
    assert!(
        !record.ok,
        "an unresolved payload is not evidence: {:?}",
        record.record
    );
    for node in ["Player", "Goal", "HUD"] {
        assert!(
            record
                .record
                .observation
                .contains(&format!("{node}=missing")),
            "{node} must stay missing: {}",
            record.record.observation
        );
    }
}

// ---------------------------------------------------------------------------
// DR-58 — game-process reachability from the real node-properties reply
// ---------------------------------------------------------------------------

/// DR-58 ①: with the engine's **real** `input_axis` reading (`null`) the axis can
/// prove nothing, so `game_process_reachable` must come from
/// `running_game_get_node_properties` — and it must come out `true`.
#[tokio::test]
async fn a_real_node_properties_reply_makes_the_game_process_reachable() {
    let temp = tempfile::tempdir().unwrap();
    let channel = Arc::new(FixtureChannel::green().with_axis_mode(AxisMode::Unreadable));
    let run = run_battery(temp.path(), channel, 30).await;

    let raw: Value = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/raw/input_channel_probe.json"),
    ))
    .unwrap();
    // The axis really carried nothing, so reachability cannot have come from it.
    assert_eq!(raw["channel"]["axis_before"], json!(null), "{raw}");
    assert_eq!(
        raw["channel"]["game_process_reachable"],
        json!(true),
        "the real node-properties reply proves the game process: {}",
        raw["channel"]["detail"]
    );
    assert_eq!(
        raw["channel"]["capability"],
        json!("GAME_INPUT_CHANNEL_OK"),
        "{}",
        raw["channel"]["detail"]
    );

    // …and the reading is the engine's own semantic payload.
    let call = raw["calls"]
        .as_array()
        .unwrap()
        .iter()
        .find(|call| call["tool"] == json!("running_game_get_node_properties"))
        .expect("the semantic node read is recorded");
    assert_eq!(call["ok"], json!(true), "{call}");
    let payload: Value =
        serde_json::from_str(call["payload"]["content"][0]["text"].as_str().unwrap()).unwrap();
    assert!(
        payload["node_path"]
            .as_str()
            .unwrap()
            .starts_with("/root/Main/"),
        "the resolved path is what proves the read: {payload}"
    );
    assert!(payload["properties"].is_object(), "{payload}");
}

/// DR-58 ④ — the counterexample: a payload that does **not** prove the node must
/// not establish reachability either.  A predicate made constant `true` (to make
/// the round look better) would pass the test above and fail here.
#[tokio::test]
async fn a_malformed_node_properties_reply_does_not_prove_the_game_process() {
    let temp = tempfile::tempdir().unwrap();
    let channel = Arc::new(
        FixtureChannel::green()
            .with_axis_mode(AxisMode::Unreadable)
            .with_reply(
                "running_game_get_node_properties",
                json!({"content": [{"type": "text", "text": "{\"name\":\"Player\"}"}]}),
            ),
    );
    let run = run_battery(temp.path(), channel, 30).await;

    let raw: Value = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/raw/input_channel_probe.json"),
    ))
    .unwrap();
    assert_eq!(
        raw["channel"]["game_process_reachable"],
        json!(false),
        "a top-level name proves nothing: {}",
        raw["channel"]["detail"]
    );
    assert_eq!(
        raw["channel"]["capability"],
        json!("ACTION_BINDING_UNKNOWN"),
        "an unreadable channel is never upgraded: {}",
        raw["channel"]["detail"]
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
// DR-52 — diagnostics must agree with their own raw records, and every call
//         must conform to the contract's parameter shape
// ---------------------------------------------------------------------------

/// The recorded `editor_get_input_actions` call of `input_replay`, and the
/// action list the engine really returned.
fn recorded_editor_actions(run: &BatteryRun) -> (String, Vec<Value>) {
    let raw: Value = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/raw/input_replay.json"),
    ))
    .unwrap();
    let call = raw["calls"]
        .as_array()
        .unwrap()
        .iter()
        .find(|call| call["tool"] == json!("editor_get_input_actions"))
        .expect("the editor-side InputMap read must be recorded");
    let text = call["payload"]["content"][0]["text"]
        .as_str()
        .expect("the MCP envelope");
    let inner: Value = serde_json::from_str(text).expect("the payload JSON");
    let actions = inner["actions"]
        .as_array()
        .expect("the engine answers an `actions` array")
        .clone();
    (text.to_string(), actions)
}

/// DR-52 (DEF-E): `deterministic.json` claimed the editor InputMap "does not
/// list move_left/move_right/jump" while its own `raw/input_replay.json`
/// recorded an `actions` array whose **first three entries are exactly those
/// names**.  The diagnostic is now derived from the same parse the record shows,
/// and it publishes the count it read so the two can be compared.
#[tokio::test]
async fn the_editor_input_map_diagnostic_agrees_with_its_own_record() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(
        FixtureChannel::green()
            .with_input_actions(InputActionsMode::EngineArray)
            .with_game_input(GameInputMode::Ok),
    );
    let run = run_battery(root, channel, 30).await;

    let (text, actions) = recorded_editor_actions(&run);
    let names: Vec<String> = actions
        .iter()
        .filter_map(|action| action.as_str().map(ToOwned::to_owned))
        .collect();
    for wanted in ["move_left", "move_right", "jump"] {
        assert!(
            names.iter().any(|name| name == wanted),
            "the fixture must really carry `{wanted}`: {names:?}"
        );
    }

    let replay = step(&run.records, "input_replay");
    let observation = &replay.record.observation;
    assert!(
        observation.contains("lists all three actions"),
        "the diagnostic must agree with the record it quotes (DR-52): {observation}"
    );
    assert!(
        !observation.contains("does not list"),
        "the smoke-t6 contradiction must be gone: {observation}"
    );
    assert!(
        observation.contains(&format!("{} action(s)", names.len())),
        "the diagnostic must publish the count it read ({}) — raw record: {text}",
        names.len()
    );

    // And the same self-consistency holds in the other direction: `move_left`
    // really absent must still be reported as absent, with the count.
    let channel =
        Arc::new(FixtureChannel::green().with_input_actions(InputActionsMode::RealEditorMap));
    let temp = tempfile::tempdir().unwrap();
    let run = run_battery(temp.path(), channel, 30).await;
    let (_, actions) = recorded_editor_actions(&run);
    let observation = &step(&run.records, "input_replay").record.observation;
    assert!(
        observation.contains("does not list"),
        "an editor map without the project actions must say so: {observation}"
    );
    assert!(
        observation.contains(&format!("{} action(s)", actions.len())),
        "the count must match the record ({}): {observation}",
        actions.len()
    );
}

/// DR-52: does this argument set conform to the contract's `inputSchema`?
///
/// Deliberately a **test-side** checker: it is an audit of the arguments hof-rs
/// builds against the fixture contract (the same `tools/list` snapshot the
/// runtime embeds), not a runtime behaviour.
fn check_arguments(tool: &str, schema: &Value, args: &Value) -> Result<(), String> {
    let properties = schema
        .pointer("/inputSchema/properties")
        .and_then(Value::as_object);
    let required: Vec<&str> = schema
        .pointer("/inputSchema/required")
        .and_then(Value::as_array)
        .map(|items| items.iter().filter_map(Value::as_str).collect())
        .unwrap_or_default();
    let Some(args) = args.as_object() else {
        return Err(format!("`{tool}`: arguments must be a JSON object"));
    };
    for (name, value) in args {
        let Some(property) = properties.and_then(|properties| properties.get(name)) else {
            return Err(format!("`{tool}`: `{name}` is not a declared parameter"));
        };
        let declared = property
            .get("type")
            .and_then(Value::as_str)
            .unwrap_or("any");
        let matches = match declared {
            "string" => value.is_string(),
            "integer" => value.is_i64() || value.is_u64(),
            "number" => value.is_number(),
            "boolean" => value.is_boolean(),
            "array" => value.is_array(),
            "object" => value.is_object(),
            "any" | _ => true,
        };
        if !matches {
            return Err(format!(
                "`{tool}`: `{name}` must be {declared}, got {value}"
            ));
        }
    }
    for name in required {
        if !args.contains_key(name) {
            return Err(format!("`{tool}`: required parameter `{name}` is missing"));
        }
    }

    // Value domains the JSON Schema cannot express, taken from the engine itself.
    if tool == "running_game_capture_screenshot" {
        if let Some(save_path) = args.get("save_path").and_then(Value::as_str) {
            if !(save_path.starts_with("res://") || save_path.starts_with("user://")) {
                return Err(format!(
                    "`{tool}`: `save_path` must start with res:// or user:// \
                     (running_game_capture.cpp:62-63), got `{save_path}`"
                ));
            }
        }
    }
    if tool == "running_game_execute_gdscript" {
        let code = args.get("code").and_then(Value::as_str).unwrap_or("");
        if code.trim().is_empty() {
            return Err(format!("`{tool}`: `code` must not be blank"));
        }
        // DR-50: `code` is a GDScript function **body**
        // (running_game_script_execution.cpp:57-59).  A void call may not be
        // used as a value — `str(Input.action_press(...))` does not compile
        // (gdscript_analyzer.cpp:3498), and that is exactly the body `smoke-t6`
        // sent as its fifth (hanging) call.  Whether a *reading* is actually
        // `return`-ed is enforced by `the_game_probe_calls_are_gdscript_bodies`.
        for void_call in ["Input.action_press(", "Input.action_release("] {
            if let Some(position) = code.find(void_call) {
                // The void call used as a value looks like `str(<void call>)`.
                let used_as_value = code[..position].contains("str(");
                if used_as_value {
                    return Err(format!(
                        "`{tool}`: `code` uses the void call `{void_call}…)` as a value; it must \
                         stay a statement"
                    ));
                }
            }
        }
    }
    Ok(())
}

/// DR-52: the checker must have teeth — the three violations this batch exists
/// to remove are all rejected by it, on the verbatim `smoke-t6` argument.
#[test]
fn the_parameter_shape_checker_rejects_the_smoke_t6_violations() {
    let schemas = hof_rs::tools::index::embedded_tool_schemas();
    let schema = |name: &str| {
        schemas
            .iter()
            .find(|tool| tool["name"] == json!(name))
            .unwrap_or_else(|| panic!("`{name}` must be in the contract"))
    };

    // DEF-B: the filesystem path the engine refused with -32602 three times.
    let violation = check_arguments(
        "running_game_capture_screenshot",
        schema("running_game_capture_screenshot"),
        &json!({"save_path": ".workspace/mario\\.hoh/evidence/frame-00.png"}),
    )
    .expect_err("a filesystem save_path violates the contract");
    assert!(violation.contains("res:// or user://"), "{violation}");
    // …and the fixed shape is accepted.
    check_arguments(
        "running_game_capture_screenshot",
        schema("running_game_capture_screenshot"),
        &json!({}),
    )
    .expect("the inline form takes no save_path");

    // Unknown parameter / missing required parameter / wrong type.
    let violation = check_arguments(
        "editor_get_errors",
        schema("editor_get_errors"),
        &json!({"bogus": 1}),
    )
    .expect_err("an undeclared parameter must be rejected");
    assert!(
        violation.contains("not a declared parameter"),
        "{violation}"
    );
    let violation = check_arguments("editor_open_scene", schema("editor_open_scene"), &json!({}))
        .expect_err("a missing required parameter must be rejected");
    assert!(
        violation.contains("required parameter `path`"),
        "{violation}"
    );
    let violation = check_arguments(
        "editor_get_errors",
        schema("editor_get_errors"),
        &json!({"max_lines": "fifty"}),
    )
    .expect_err("a wrong type must be rejected");
    assert!(violation.contains("must be integer"), "{violation}");

    // DR-50: the fifth (`smoke-t6`) `execute_gdscript` body — a void call used as
    // a value — is rejected, and both fixed forms are accepted.
    let violation = check_arguments(
        "running_game_execute_gdscript",
        schema("running_game_execute_gdscript"),
        &json!({"code": "str(Input.action_press(\"move_right\"))"}),
    )
    .expect_err("a void call may not be used as a value");
    assert!(violation.contains("must stay a statement"), "{violation}");
    for code in [
        "return str(InputMap.has_action(\"move_right\"))",
        "Input.action_press(\"move_right\")",
    ] {
        check_arguments(
            "running_game_execute_gdscript",
            schema("running_game_execute_gdscript"),
            &json!({"code": code}),
        )
        .unwrap_or_else(|violation| panic!("the fixed body must be accepted: {violation}"));
    }
    let violation = check_arguments(
        "running_game_execute_gdscript",
        schema("running_game_execute_gdscript"),
        &json!({"code": "   "}),
    )
    .expect_err("a blank body must be rejected");
    assert!(violation.contains("must not be blank"), "{violation}");
}

/// DR-52: **every** tool hof-rs calls, with the arguments it really sends, must
/// conform to the 177-tool contract's parameter shape.
///
/// The list below is the audit's coverage requirement: a new call site (or a
/// renamed call) makes this test fail until it is covered here.
#[tokio::test]
async fn every_tool_call_hof_rs_makes_matches_the_contract_schema() {
    const AUDITED_TOOLS: &[&str] = &[
        "editor_get_collision_info",
        "editor_get_errors",
        "editor_get_input_actions",
        "editor_open_scene",
        "editor_play_scene",
        "editor_rescan_project_filesystem",
        "editor_simulate_input_action",
        "editor_stop_scene",
        "project_read_scene_file_content",
        "running_game_capture_frames",
        "running_game_capture_screenshot",
        // DR-54: the semantic capabilities E3's critical path is built on.  A
        // call site that stops using them (or a renamed one) fails this audit.
        "running_game_create_input_recording",
        "running_game_execute_gdscript",
        "running_game_get_node_properties",
        "running_game_get_node_property_samples",
        "running_game_get_scene_tree",
        "running_game_play_input_recording",
        "running_game_run_test_scenario",
        "running_game_stop_input_recording",
    ];

    let mut recorded: Vec<(String, Value)> = Vec::new();
    for mode in [
        ScreenshotMode::InlineImage,
        ScreenshotMode::InlineBase64Fallback,
    ] {
        let temp = tempfile::tempdir().unwrap();
        let channel = Arc::new(FixtureChannel::green().with_screenshot(mode));
        run_battery(temp.path(), channel.clone(), 30).await;
        recorded.extend(channel.all_calls());
    }

    let schemas = hof_rs::tools::index::embedded_tool_schemas();
    let mut checked: std::collections::BTreeSet<String> = std::collections::BTreeSet::new();
    for (tool, args) in &recorded {
        // The battery's own step ids are not tool calls; the fixture channel
        // only records tools it was asked to run, so every entry is one.
        let schema = schemas
            .iter()
            .find(|entry| entry["name"] == json!(tool))
            .unwrap_or_else(|| panic!("`{tool}` is not in the 177-tool contract"));
        check_arguments(tool, schema, args)
            .unwrap_or_else(|violation| panic!("parameter shape violation: {violation}"));
        checked.insert(tool.clone());
    }

    for tool in AUDITED_TOOLS {
        assert!(
            checked.contains(*tool),
            "`{tool}` is called by hof-rs but was never audited: {checked:?}"
        );
    }
}

// ---------------------------------------------------------------------------
// DR-35 — the input channel is the *game* process, not the editor
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// DR-50 — `running_game_execute_gdscript` takes a GDScript *body*
// ---------------------------------------------------------------------------

/// DR-50A (kept under DR-54): `running_game_execute_gdscript` takes a GDScript
/// **function body**, so every call hof-rs still makes must be a body that
/// returns a value.
///
/// `smoke-t6`'s four transport-successful probe calls all answered
/// `{"result":null,"result_type":"Nil"}`, because the scripts were bare
/// expressions.  Since DR-54 the battery's critical path no longer uses this
/// tool at all — what remains is the read-only position probe — so this test now
/// asserts the surviving calls are body-shaped **and** that no side-effecting
/// mutation is a GDScript call any more.  The double in this file models the
/// engine's Nil answer, so a regression here also fails the end-to-end battery.
#[tokio::test]
async fn every_surviving_execute_gdscript_call_is_a_gdscript_body() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green());
    let run = run_battery(root, channel.clone(), 30).await;

    let mut scripts: Vec<String> = Vec::new();
    for step_id in ["input_channel_probe", "input_replay"] {
        let raw: Value = serde_json::from_str(&read(&run.run_dir.join(format!(
            "iter-1/candidate/.hoh/deterministic/raw/{step_id}.json"
        ))))
        .unwrap();
        scripts.extend(
            raw["calls"]
                .as_array()
                .unwrap()
                .iter()
                .filter(|call| call["tool"] == json!("running_game_execute_gdscript"))
                .filter_map(|call| call["args"]["code"].as_str().map(ToOwned::to_owned)),
        );
    }

    // DR-54: the read-only probe is still exercised, so the shape guard has real
    // subjects — but it is the *only* remaining user of this tool on the critical
    // path.
    assert!(
        !scripts.is_empty(),
        "the read-only position probe must still run: {scripts:?}"
    );
    for script in &scripts {
        let trimmed = script.trim_start();
        assert!(
            trimmed.starts_with("return "),
            "a value-reading body must `return` its reading (DR-50A): {script}"
        );
        // DR-50: a void call used as a value does not compile — the exact body
        // that took the game endpoint down in `smoke-t6`.
        assert!(
            !script.contains("Input.action_press(") && !script.contains("Input.action_release("),
            "input injection must not be a caller-assembled script any more (DR-54): {script}"
        );
    }

    // And the readings must actually arrive: a body without `return` answers Nil,
    // which the double reproduces, so the capability verdict proves it.
    assert!(
        step(&run.records, "input_channel_probe")
            .record
            .observation
            .contains("GAME_INPUT_CHANNEL_OK"),
        "the readings must be readable: {:?}",
        step(&run.records, "input_channel_probe").record.observation
    );
}

/// DR-54 ①: the input channel's **critical assertion** is built on the
/// contract's semantic tools, not on caller-assembled GDScript.
///
/// `input_channel_probe` classifies `GAME_INPUT_CHANNEL_OK` / `ACTION_NOT_BOUND`
/// / `ACTION_BINDING_UNKNOWN`, and `input_replay`'s F1/F2/F3 verdict reads that
/// classification — so this is the load-bearing path.  It must be produced by
/// the semantic input API (`create_input_recording` + `play_input_recording` +
/// `running_game_run_test_scenario`) and the semantic reader
/// (`get_node_property_samples`), with `execute_gdscript` reduced to a read-only
/// probe whose value is recorded but never the sole evidence.
#[tokio::test]
async fn the_input_channel_critical_path_is_built_on_semantic_tools() {
    let temp = tempfile::tempdir().unwrap();
    let channel = Arc::new(FixtureChannel::green());
    let run = run_battery(temp.path(), channel.clone(), 30).await;

    let raw: Value = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/raw/input_channel_probe.json"),
    ))
    .unwrap();
    let tools_of = |raw: &Value| -> Vec<String> {
        raw["calls"]
            .as_array()
            .unwrap()
            .iter()
            .filter_map(|call| call["tool"].as_str().map(ToOwned::to_owned))
            .collect()
    };
    let tools = tools_of(&raw);
    for semantic_tool in [
        "running_game_create_input_recording",
        "running_game_play_input_recording",
        "running_game_run_test_scenario",
        "running_game_get_node_property_samples",
    ] {
        assert!(
            tools.iter().any(|tool| tool == semantic_tool),
            "`{semantic_tool}` must carry the probe: {tools:?}"
        );
    }

    // The classification came out of the semantic evidence …
    assert_eq!(raw["channel"]["capability"], json!("GAME_INPUT_CHANNEL_OK"));
    assert_eq!(raw["channel"]["pressed"], json!(true));

    // … and the supplementary GDScript call is a read-only probe: it returns a
    // value and it mutates nothing.
    let script_calls: Vec<&Value> = raw["calls"]
        .as_array()
        .unwrap()
        .iter()
        .filter(|call| call["tool"] == json!("running_game_execute_gdscript"))
        .collect();
    assert!(
        !script_calls.is_empty(),
        "the read-only probe is kept: {raw}"
    );
    for call in &script_calls {
        let code = call["args"]["code"].as_str().unwrap_or("");
        assert!(
            code.trim_start().starts_with("return "),
            "a read-only probe must return its reading: {call}"
        );
        assert!(
            !code.contains("Input.action_press(") && !code.contains("Input.action_release("),
            "a read-only probe must not inject input (DR-54): {call}"
        );
    }
}

/// DR-54 ① (continued): the replay's injection goes through the semantic input
/// API too — no `execute_gdscript` call may be the thing that presses a key.
#[tokio::test]
async fn the_input_replay_injection_is_semantic_not_gdscript() {
    let temp = tempfile::tempdir().unwrap();
    let channel = Arc::new(FixtureChannel::green());
    let run = run_battery(temp.path(), channel.clone(), 30).await;

    for (action, label) in [
        ("move_right", "move_right"),
        ("jump", "jump"),
        ("move_left", "move_left"),
    ] {
        let injected = channel.calls_of("running_game_play_input_recording");
        assert!(
            injected.iter().any(|args| args["events"]
                .as_array()
                .map(|events| events.iter().any(|event| event["action"] == json!(action)))
                .unwrap_or(false)),
            "`{action}` must be injected through the semantic recording API: {injected:?}"
        );
        assert!(
            channel
                .calls_of("running_game_run_test_scenario")
                .iter()
                .any(|args| args["steps"]
                    .as_array()
                    .map(|steps| steps.iter().any(|step| step["action"] == json!(action)))
                    .unwrap_or(false)),
            "the scenario runner must drive `{action}`: {:?}",
            channel.calls_of("running_game_run_test_scenario")
        );

        // The step's own record carries the semantic reader under a label that
        // names the action, so the reading is attributable.
        let raw: Value = serde_json::from_str(&read(
            &run.run_dir
                .join("iter-1/candidate/.hoh/deterministic/raw/input_replay.json"),
        ))
        .unwrap();
        let labels: Vec<String> = raw["calls"]
            .as_array()
            .unwrap()
            .iter()
            .filter(|call| call["tool"] == json!("running_game_get_node_property_samples"))
            .map(|call| call["label"].as_str().unwrap_or("<none>").to_string())
            .collect();
        assert!(
            labels
                .iter()
                .any(|value| value.starts_with(&format!("{label}:"))),
            "the `{label}` position samples must be semantic and attributable: {labels:?}"
        );
    }

    // The position evidence is the semantic sample's quadruple.
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
        quadruples.len() >= 4,
        "at least one game-process quadruple per replayed action (plus the probe's own sample): {raw}"
    );
    for quadruple in quadruples {
        assert_eq!(quadruple["channel"], json!("game_process"));
    }
}

/// DR-54 ②: the semantic tool is the load-bearing call.  When the semantic input
/// API refuses the action and the semantic reader cannot be read, the probe must
/// report `ACTION_BINDING_UNKNOWN` — the legacy GDScript probe answering happily
/// must not rescue the verdict.
#[tokio::test]
async fn a_semantic_refusal_is_not_rescued_by_the_gdscript_probe() {
    let temp = tempfile::tempdir().unwrap();
    let channel = Arc::new(
        FixtureChannel::green()
            .fail_always(
                "running_game_play_input_recording",
                McpError::new(-32602, "no game endpoint answered the recording replay"),
            )
            .fail_always(
                "running_game_run_test_scenario",
                McpError::new(-32602, "no game endpoint answered the scenario"),
            )
            .fail_always(
                "running_game_get_node_property_samples",
                McpError::new(-32602, "no game endpoint answered the samples"),
            ),
    );
    let run = run_battery(temp.path(), channel, 30).await;

    let probe = step(&run.records, "input_channel_probe");
    assert!(
        !probe.ok,
        "a semantic refusal cannot be a usable channel: {:?}",
        probe.record.observation
    );
    assert!(
        probe.record.observation.contains("ACTION_BINDING_UNKNOWN"),
        "{}",
        probe.record.observation
    );
    assert!(
        !probe.record.observation.contains("ACTION_NOT_BOUND"),
        "an unreadable channel is never downgraded: {}",
        probe.record.observation
    );
    // The read-only GDScript probe *did* answer (the double still serves it), and
    // that must be visible as supplementary — it changed nothing.
    assert!(
        probe
            .record
            .observation
            .contains("read-only execute_gdscript probe=Some"),
        "the supplementary probe's reading must be recorded: {}",
        probe.record.observation
    );
}

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
    // The game-side injection really went through the semantic input API
    // (DR-54), and the legacy script probe is no longer what drives it.
    assert!(
        channel.call_count("running_game_play_input_recording") >= 4,
        "the probe and the replay must drive the game process through the semantic API"
    );
    assert!(
        channel.call_count("running_game_run_test_scenario") >= 4,
        "every action must be driven through the semantic scenario runner"
    );
    let script_mutations: Vec<Value> = channel
        .calls_of("running_game_execute_gdscript")
        .into_iter()
        .filter(|args| {
            let code = args["code"].as_str().unwrap_or("");
            code.contains("Input.action_press(") || code.contains("Input.action_release(")
        })
        .collect();
    assert!(
        script_mutations.is_empty(),
        "no input injection may be a caller-assembled script any more (DR-54): {script_mutations:?}"
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
    assert_eq!(raw["channel"]["pressed"], json!(true));
    // Every semantic step of the probe is recorded verbatim, and the read-only
    // GDScript probe is recorded too.
    for tool in [
        "running_game_create_input_recording",
        "running_game_play_input_recording",
        "running_game_run_test_scenario",
        "running_game_get_node_property_samples",
        "running_game_execute_gdscript",
    ] {
        assert!(
            raw["calls"]
                .as_array()
                .unwrap()
                .iter()
                .any(|call| call["tool"] == json!(tool)),
            "`{tool}` must be recorded verbatim: {raw}"
        );
    }
}

/// DR-58 ①: the scenario runner's **real** request shape.
///
/// The engine refuses `scene_path` for every value it was given, so the battery
/// must omit the member entirely — and the recorded call must then really
/// succeed.  Non-vacuity: the same engine-modelled double answers the old
/// `"current"` shape with the engine's verbatim `-32602`, so a test that only
/// checked "the call happened" could not pass.
#[tokio::test]
async fn the_scenario_request_omits_scene_path_because_the_runner_refuses_every_value() {
    let temp = tempfile::tempdir().unwrap();
    let channel = Arc::new(FixtureChannel::green());
    let run = run_battery(temp.path(), channel.clone(), 30).await;

    let scenario_calls = channel.calls_of("running_game_run_test_scenario");
    assert!(
        !scenario_calls.is_empty(),
        "the semantic scenario runner must still be exercised"
    );
    for args in &scenario_calls {
        assert!(
            args.get("scene_path").is_none(),
            "the game-scope runner refuses every scene_path value (DR-58): {args}"
        );
        assert!(
            args["steps"].is_array(),
            "the real shape the runner accepts is `steps` only: {args}"
        );
    }

    // … and the recorded call is a real success, not a quoted refusal.
    let raw: Value = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/raw/input_channel_probe.json"),
    ))
    .unwrap();
    let call = raw["calls"]
        .as_array()
        .unwrap()
        .iter()
        .find(|call| call["tool"] == json!("running_game_run_test_scenario"))
        .expect("the scenario call is recorded verbatim");
    assert_eq!(call["ok"], json!(true), "{call}");
    assert!(call.get("error").is_none(), "{call}");
    assert!(
        call["payload"]["content"].is_array(),
        "the accepted reply is the per-step result envelope: {call}"
    );
    assert!(
        raw["channel"]["pressed"] == json!(true),
        "the injection the runner carried must be recorded: {raw}"
    );

    // Non-vacuity: the *wrong* shape is refused by the same double, in the
    // engine's own words.
    let wrong = json!({"scene_path": "current", "steps": [{"type": "wait", "seconds": 0.0}]});
    let error = channel
        .call(Role::Tester, "running_game_run_test_scenario", wrong)
        .await
        .expect_err("a scene_path-carrying request must be refused");
    let text = error.to_string();
    assert!(text.contains("-32602"), "{text}");
    assert!(
        text.contains(&scene_path_refusal("current")),
        "the engine's verbatim refusal must be reproduced: {text}"
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

// ---------------------------------------------------------------------------
// DR-68 ③/⑧ — the replay must release the previous input, and movement is judged
//               on the action's own axis
// ---------------------------------------------------------------------------

/// The `input_replay` step's raw call list, in arrival order.
fn replay_calls(run: &BatteryRun) -> Vec<Value> {
    let raw: Value = serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/raw/input_replay.json"),
    ))
    .unwrap();
    raw["calls"].as_array().cloned().unwrap_or_default()
}

/// The position quadruple the replay recorded for `action` (the samples call
/// carries no label of its own; the quadruple names its action).
fn quadruple_of(calls: &[Value], action: &str) -> Value {
    calls
        .iter()
        .filter_map(|call| call.get("quadruple"))
        .find(|quadruple| quadruple["action"] == json!(action))
        .cloned()
        .unwrap_or_else(|| panic!("no quadruple for `{action}` in {calls:?}"))
}

/// DR-68 ③(a): `smoke-t8` injected **every** direction with `pressed = true` and
/// never released one inside the game process, so by the `move_left` window
/// `move_right` was still held.  `Input.get_axis("move_left","move_right")`
/// therefore returned `0` and the character could not move on `x` whichever
/// implementation it had — the two directions cancelled.  The replay must clear
/// the previous input **inside the game** before testing a new direction, and
/// the axis reading must show the change.
#[tokio::test]
async fn the_input_replay_releases_the_previous_direction_before_the_next_one() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green());
    let run = run_battery(root, channel.clone(), 30).await;

    let calls = replay_calls(&run);
    let event_matches = |call: &Value, action: &str, pressed: bool| -> bool {
        call["tool"] == json!("running_game_play_input_recording")
            && call["args"]["events"]
                .as_array()
                .map(|events| {
                    events.iter().any(|event| {
                        event["action"] == json!(action) && event["pressed"] == json!(pressed)
                    })
                })
                .unwrap_or(false)
    };

    // The release really went through the **game-process** semantic API (the
    // editor-side `editor_simulate_input_action` release cannot reach the game).
    let releases: Vec<&Value> = calls
        .iter()
        .filter(|call| {
            call["tool"] == json!("running_game_play_input_recording")
                && call["args"]["events"]
                    .as_array()
                    .map(|events| events.iter().any(|event| event["pressed"] == json!(false)))
                    .unwrap_or(false)
        })
        .collect();
    assert!(
        !releases.is_empty(),
        "DR-68 ③(a): the replay must release the previous input inside the game: {calls:?}"
    );
    let released: Vec<&str> = releases
        .iter()
        .flat_map(|call| call["args"]["events"].as_array().unwrap())
        .filter(|event| event["pressed"] == json!(false))
        .filter_map(|event| event["action"].as_str())
        .collect();
    assert!(
        released.contains(&"move_right"),
        "the held `move_right` must be released before another direction is tested: {released:?}"
    );

    // …and the release precedes the `move_left` press, in playback order.
    let release_index = calls
        .iter()
        .position(|call| event_matches(call, "move_right", false))
        .expect("`move_right` is released through the semantic API");
    let press_index = calls
        .iter()
        .position(|call| event_matches(call, "move_left", true))
        .expect("`move_left` is injected through the semantic API");
    assert!(
        release_index < press_index,
        "the release must come first (release at {release_index}, move_left press at \
         {press_index}): {calls:?}"
    );

    // The consequence: `move_left` really moves on `x`, and the step stays green.
    let replay = step(&run.records, "input_replay");
    assert!(
        replay.ok,
        "the replay is green: {}",
        replay.record.observation
    );
    let quadruple = quadruple_of(&calls, "move_left");
    let before = quadruple["before_position"]["x"].as_f64().unwrap();
    let after = quadruple["after_position"]["x"].as_f64().unwrap();
    assert!(
        after < before,
        "with the previous direction released, `move_left` must move -x: {quadruple}"
    );

    // The axis reading, when the engine gives one, must have changed too.
    let axis_readings: Vec<&Value> = calls
        .iter()
        .filter(|call| {
            call["tool"] == json!("running_game_get_node_property_samples")
                && call["label"]
                    .as_str()
                    .unwrap_or_default()
                    .contains("game_axis")
        })
        .collect();
    assert!(
        !axis_readings.is_empty(),
        "the replay records its game-process axis readings: {calls:?}"
    );
    assert!(
        axis_readings
            .iter()
            .filter(|call| call["label"]
                .as_str()
                .unwrap_or_default()
                .starts_with("move_left"))
            .all(|call| {
                let text = call["payload"]["content"][0]["text"]
                    .as_str()
                    .unwrap_or("{}");
                text.contains("\"input_axis\":-1") || text.contains("\"input_axis\":null")
            }),
        "the `move_left` axis reading must be -1 (or unreadable, as the real engine \
         answers): {axis_readings:?}"
    );
}

/// DR-68 ⑧: the movement predicate must judge the **intended axis**.  `smoke-t8`
/// scored `move_left` as `ok = true` because `before_position != after_position`
/// compared the whole vector and gravity had moved `y` while `x` was pinned at
/// `584.363` for all 60 frames.
#[tokio::test]
async fn a_dead_target_axis_is_not_movement_even_when_the_other_axis_moves() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green().with_movement(MovementMode::OtherAxisOnly));
    let run = run_battery(root, channel, 30).await;

    let calls = replay_calls(&run);
    let quadruple = quadruple_of(&calls, "move_left");
    assert_eq!(
        quadruple["before_position"]["x"], quadruple["after_position"]["x"],
        "the fixture must reproduce the artifact: x is pinned: {quadruple}"
    );
    assert_ne!(
        quadruple["before_position"]["y"], quadruple["after_position"]["y"],
        "…while the other axis moved (gravity): {quadruple}"
    );

    let replay = step(&run.records, "input_replay");
    assert!(
        !replay.ok,
        "a dead `x` axis is not movement, however much `y` moved: {}",
        replay.record.observation
    );
    assert!(
        replay.record.observation.contains("INPUT_HAD_NO_EFFECT"),
        "{}",
        replay.record.observation
    );
    assert!(
        replay.record.observation.contains("axis=x"),
        "the observation must name the axis it judged: {}",
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
    let channel =
        Arc::new(FixtureChannel::green().with_reply("running_game_get_scene_tree", payload));
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

// ---------------------------------------------------------------------------
// DR-49 — the screenshot must be *this run's* artifact
// ---------------------------------------------------------------------------

/// The stale PNG `smoke-t6` found on disk: a 2026-09-21 file that made the step
/// report success while the engine had refused the call three times.
const STALE_PNG: &[u8] = b"a PNG from an earlier round, never this run's\n";

fn place_stale_screenshot(workspace: &Path) {
    let target = workspace.join(".hoh/evidence/frame-00.png");
    std::fs::create_dir_all(target.parent().unwrap()).unwrap();
    std::fs::write(&target, STALE_PNG).unwrap();
}

/// DR-49 ①/②: the call must use the contract's writable form, never a
/// filesystem path — `running_game_capture.cpp:62-63` refuses anything but
/// `res://`/`user://` with `-32602` (three times in `smoke-t6`).
#[tokio::test]
async fn the_screenshot_call_carries_no_filesystem_path() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green());
    let run = run_battery(root, channel.clone(), 30).await;

    let calls = channel.calls_of("running_game_capture_screenshot");
    assert!(!calls.is_empty(), "the step must have called the tool");
    for args in &calls {
        match args.get("save_path").and_then(Value::as_str) {
            None => {}
            Some(save_path) => assert!(
                save_path.starts_with("res://") || save_path.starts_with("user://"),
                "a filesystem `save_path` is a contract violation (DR-49): {save_path}"
            ),
        }
    }
    // The contract shape this batch commits to: no `save_path` at all, with the
    // runtime materializing the inline image.
    assert_eq!(
        calls[0],
        json!({}),
        "the call must not carry a filesystem `save_path` (DR-49)"
    );

    let record = step(&run.records, "screenshot");
    assert!(record.ok, "{:?}", record.record);
    assert_eq!(
        record.record.path.as_deref(),
        Some(".hoh/evidence/frame-00.png")
    );
}

/// DR-49 ②/③: a pre-existing PNG must not satisfy the step.  This is the
/// `smoke-t6` reproduction: the engine refuses the call (or answers without an
/// image) and a stale file is the only thing on disk.
#[tokio::test]
async fn a_stale_png_is_never_mistaken_for_this_runs_screenshot() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel =
        Arc::new(FixtureChannel::green().with_screenshot(ScreenshotMode::ReportsSuccessButNoFile));
    place_stale_screenshot(&root.join("workspace"));

    let run = run_battery(root, channel, 30).await;

    let record = step(&run.records, "screenshot");
    assert!(
        !record.ok,
        "a PNG that was already on disk is not this run's evidence (DR-49): {:?}",
        record.record
    );
    assert!(
        record.record.path.is_none(),
        "no path may be claimed from a stale file: {:?}",
        record.record
    );
    assert!(
        record.record.observation.contains("UNAVAILABLE"),
        "{}",
        record.record.observation
    );
    assert!(
        !run.workspace.join(".hoh/evidence/frame-00.png").exists(),
        "the stale file must have been invalidated before the call (DR-49)"
    );
}

/// DR-49 ④: a stale file used to **suppress** the `running_game_capture_frames`
/// fallback (`godot.rs:1081` tested `is_file()`), so a real inline image was
/// never materialized.  The fallback is now decided by "do we have this run's
/// image yet?", not by the disk.
#[tokio::test]
async fn a_stale_png_does_not_suppress_the_frames_fallback() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(
        FixtureChannel::green().with_screenshot(ScreenshotMode::SilentPrimaryFramesInline),
    );
    place_stale_screenshot(&root.join("workspace"));

    let run = run_battery(root, channel.clone(), 30).await;

    // DR-69 ④: the count is scoped to the `screenshot` step's own raw record.
    // Since DR-69 the `input_replay` step also captures frames (before/after per
    // replayed action) and therefore also falls back, so a battery-wide counter
    // no longer identifies this step's fallback.  The requirement -- **exactly
    // one** fallback for the screenshot step -- is unchanged and is now asserted
    // on the record that belongs to it.
    let screenshot_raw: Value = serde_json::from_str(&read(
        &run.workspace.join(".hoh/deterministic/raw/screenshot.json"),
    ))
    .expect("raw/screenshot.json");
    let fallbacks = screenshot_raw["calls"]
        .as_array()
        .cloned()
        .unwrap_or_default()
        .iter()
        .filter(|call| call["tool"] == json!("running_game_capture_frames"))
        .count();
    assert_eq!(
        fallbacks, 1,
        "the fallback must be attempted even when a file already exists (DR-49): {screenshot_raw}"
    );
    let record = step(&run.records, "screenshot");
    assert!(
        record.ok,
        "the fallback carried a real image: {:?}",
        record.record
    );
    assert_eq!(
        record.record.path.as_deref(),
        Some(".hoh/evidence/frame-00.png")
    );
    assert_eq!(
        std::fs::read(run.workspace.join(".hoh/evidence/frame-00.png"))
            .expect("the fallback image must be on disk"),
        inline_png_bytes(),
        "the artifact must be the fallback's image, not the stale bytes (DR-49)"
    );
}

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
// DR-69 ③ — the aborted battery pass is saved before it is cleared
// ---------------------------------------------------------------------------

/// DR-69 ③: a round that spends its one repair retry runs the battery **twice**,
/// and DR-24 rebuilds `.hoh/deterministic` for the second pass.  The first
/// pass's bytes must therefore be moved to `runs/<id>/quarantine/**` before the
/// directory is cleared — `smoke-t9`' lesson ("save first, then clean") applied
/// one level down.
#[tokio::test]
async fn an_aborted_battery_pass_is_preserved_before_its_directory_is_cleared() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    // The scene tree never arrives, so the launchable gate stays closed and
    // DR-24 spends exactly one targeted repair — the second battery pass.
    let channel = Arc::new(FixtureChannel::green().fail_always(
        "running_game_get_scene_tree",
        captured_error("editor_errors_failure.txt"),
    ));
    let run = run_battery_with_script(root, channel, 1, repairing_script()).await;

    let result: Value =
        serde_json::from_str(&read(&run.run_dir.join("iter-1/result.json"))).expect("result.json");
    assert_eq!(
        result["repair_retry_used"],
        json!(true),
        "the fixture must really have run a second battery pass: {result}"
    );

    let quarantine = run.run_dir.join("quarantine");
    let listing: Vec<String> = walkdir::WalkDir::new(&run.run_dir)
        .into_iter()
        .filter_map(|entry| entry.ok())
        .map(|entry| entry.path().to_string_lossy().into_owned())
        .collect();
    let preserved: Vec<std::path::PathBuf> = walkdir::WalkDir::new(&quarantine)
        .into_iter()
        .filter_map(|entry| entry.ok())
        .filter(|entry| {
            entry.file_type().is_dir()
                && entry
                    .file_name()
                    .to_string_lossy()
                    .starts_with("deterministic-pass-1.stale-")
        })
        .map(|entry| entry.into_path())
        .collect();
    assert_eq!(
        preserved.len(),
        1,
        "the aborted first pass must be preserved exactly once under {}\nrun dir listing: {listing:#?}",
        quarantine.display()
    );
    let first = &preserved[0];
    assert!(
        first.join("raw/play_scene_ready.json").is_file(),
        "the aborted pass's raw payloads must survive: {}",
        first.display()
    );
    assert!(
        first.join("raw/input_replay.json").is_file(),
        "every raw payload of the aborted pass must survive, not only the first: {}",
        first.display()
    );
    assert!(
        first.join("mcp-errors.jsonl").is_file(),
        "the aborted pass's transport journal must survive: {}",
        first.display()
    );
    // And the frozen candidate still carries the **second** pass, not the first.
    let frozen = run
        .run_dir
        .join("iter-1/candidate/.hoh/deterministic/battery.json");
    assert!(
        frozen.is_file(),
        "the frozen candidate still keeps the current pass: {}",
        frozen.display()
    );
}

// ---------------------------------------------------------------------------
// DR-69 ④: the E3 evidence form must be reachable inside a round
// ---------------------------------------------------------------------------

/// DR-69 ④: `REQUIREMENTS.md:114` fixes E3's **evidence form** as a replay
/// plus **before/after screenshots** plus a node-state assertion.  `smoke-t9`'s
/// independent experiment observed all four behaviours on real hardware, yet the
/// round itself could never have judged E3 `met`: the battery's `input_replay`
/// produced neither the frames nor the assertion.
///
/// The load-bearing reading must be **positional**: the engine answers `null`
/// for the axis query on real hardware (DR-58), so an axis-value assertion
/// cannot be what E3 rests on.
#[tokio::test]
async fn the_input_replay_produces_before_and_after_frames_and_a_positional_assertion() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green());
    let run = run_battery(root, channel.clone(), 30).await;

    let raw = read(
        &run.workspace
            .join(".hoh/deterministic/raw/input_replay.json"),
    );
    let parsed: Value = serde_json::from_str(&raw).expect("raw input_replay.json");
    let calls = parsed["calls"].as_array().cloned().unwrap_or_default();

    let labels: Vec<String> = calls
        .iter()
        .filter_map(|call| call["label"].as_str().map(ToOwned::to_owned))
        .collect();

    for label in ["move_right", "move_left", "jump"] {
        assert!(
            labels.contains(&format!("{label}:replay_frame_before")),
            "the replay of `{label}` must capture a BEFORE frame: {labels:?}"
        );
        assert!(
            labels.contains(&format!("{label}:replay_frame_after")),
            "the replay of `{label}` must capture an AFTER frame: {labels:?}"
        );
        assert!(
            labels
                .iter()
                .any(|entry| entry == &format!("{label}:replay_assert_moved")),
            "the replay of `{label}` must assert the position in the game process: {labels:?}"
        );
    }

    // Both frames really exist, byte for byte, as this run's PNGs.
    for label in ["move_right", "move_left", "jump"] {
        for phase in ["before", "after"] {
            let relative = format!(".hoh/evidence/replay-{label}-{phase}.png");
            let on_disk = run.workspace.join(&relative);
            assert!(
                on_disk.is_file(),
                "the {phase} frame of `{label}` must be on disk: {relative}"
            );
            assert_eq!(
                std::fs::read(&on_disk).unwrap(),
                inline_png_bytes(),
                "{relative} must be the PNG the tool produced"
            );
            assert!(
                run.run_dir
                    .join("iter-1/candidate")
                    .join(&relative)
                    .is_file(),
                "E3's evidence form must reach the frozen candidate: {relative}"
            );
        }
    }

    // The assertion is positional and uses the engine's own argument names.
    let mut assertions = 0;
    for call in &calls {
        if call["tool"] != json!("running_game_assert_node_state") {
            continue;
        }
        assertions += 1;
        assert_eq!(call["ok"], json!(true), "{call}");
        assert_eq!(call["args"]["node_path"], json!("Player"), "{call}");
        assert_eq!(call["args"]["property"], json!("position"), "{call}");
        assert_eq!(call["args"]["operator"], json!("neq"), "{call}");
        assert!(
            call["args"]["expected"]["x"].is_number(),
            "the expectation must be the sampled starting position: {call}"
        );
        assert!(
            call["payload"]["content"][0]["text"]
                .as_str()
                .unwrap_or("")
                .contains("\"passed\":true"),
            "the positional assertion must pass for a moving replay: {call}"
        );
    }
    assert!(
        assertions >= 3,
        "one positional assertion per moving window: {assertions}"
    );

    assert!(
        channel.call_count("running_game_assert_node_state") >= 3,
        "the assertion must really have been called"
    );
    assert!(
        channel
            .calls_of("running_game_capture_screenshot")
            .iter()
            .filter(|args| args.get("save_path").is_none())
            .count()
            >= 6,
        "every replay frame must use the engine's inline form (no `save_path`, DR-49)"
    );
}

/// DR-69 ④: a replay whose position never changes must be red in the
/// **positional assertion** as well as in the sample deltas, and the record must
/// say which of the two failed.
#[tokio::test]
async fn a_dead_axis_is_red_in_the_positional_assertion_too() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green().with_movement(MovementMode::None));
    let run = run_battery(root, channel, 30).await;

    let replay = step(&run.records, "input_replay");
    assert!(!replay.ok, "a dead axis must be red: {:?}", replay.record);
    let raw = read(
        &run.workspace
            .join(".hoh/deterministic/raw/input_replay.json"),
    );
    let parsed: Value = serde_json::from_str(&raw).expect("raw input_replay.json");
    let failed_asserts = parsed["calls"]
        .as_array()
        .unwrap()
        .iter()
        .filter(|call| {
            call["tool"] == json!("running_game_assert_node_state")
                && call["payload"]["content"][0]["text"]
                    .as_str()
                    .unwrap_or("")
                    .contains("\"passed\":false")
        })
        .count();
    assert!(
        failed_asserts >= 3,
        "the positional assertion must fail when nothing moves: {failed_asserts}"
    );
    assert!(
        replay.record.observation.contains("POSITION_UNCHANGED")
            || replay.record.observation.contains("INPUT_HAD_NO_EFFECT"),
        "the observation must name the failure: {}",
        replay.record.observation
    );
}

// ---------------------------------------------------------------------------
// DR-69 (DEF-1) -- the axis cross-check has its own coverage
// ---------------------------------------------------------------------------

/// DR-69 (DEF-1): `INPUT_AXIS_NOT_CHANGED` (`godot.rs`) had **no** coverage --
/// deleting the branch left all 41 battery tests green, because no fixture ever
/// produced a reading that contradicted the held direction.  This one does.
///
/// The sampled positions stay correct on purpose: the failure can only come from
/// the axis cross-check, so this test is red for that branch and nothing else.
#[tokio::test]
async fn an_axis_reading_that_contradicts_the_held_direction_is_red() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green().with_axis_mode(AxisMode::WrongSign));
    let run = run_battery(root, channel, 30).await;

    let replay = step(&run.records, "input_replay");
    assert!(
        !replay.ok,
        "a contradictory axis reading must be red: {:?}",
        replay.record
    );
    assert!(
        replay.record.observation.contains("INPUT_AXIS_NOT_CHANGED"),
        "the observation must name the branch that failed: {}",
        replay.record.observation
    );
    assert!(
        !replay.record.observation.contains("INPUT_HAD_NO_EFFECT"),
        "the movement itself was correct; only the axis reading contradicted it: {}",
        replay.record.observation
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

// ---------------------------------------------------------------------------
// DR-68 ④ — the failure stub must carry the facts the round really produced
// ---------------------------------------------------------------------------

/// `smoke-t8` failed at the **Tester's schema gate**, i.e. *after* the battery
/// had run 11/11 and after `A_1` was frozen, yet `iter-1/result.json` persisted
/// `battery_passes: []`, `candidate_id: null` and `version_id: null`.  Read on
/// its own — which is how a launcher, `status`, or the next batch reads it —
/// that stub says "nothing happened", so the round's reproducibility criterion
/// fails exactly where it matters.
///
/// This test drives the real adapter and the real battery through that failure
/// and asserts the three fields are the round's own values, not a default.
#[tokio::test]
async fn a_failed_rounds_result_json_carries_the_real_battery_and_candidate() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let channel = Arc::new(FixtureChannel::green());
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer)
            .writing("project.godot", "config_version=5\n")
            .writing("scripts/player.gd", "extends CharacterBody2D\n"),
        // Present but structurally invalid: the runtime rejects it, and the
        // round fails *after* the freeze — the `smoke-t8` failure class.
        FakeStep::new(Role::Tester).writing(".hoh/evidence.json", &bad_evidence()),
    ];
    let (error, run_dir) = run_failing_battery(root, channel.clone(), 30, script, 0).await;
    let typed = hof_rs::errors::as_hof_error(&error).expect("a typed failure");
    assert!(
        matches!(typed, hof_rs::errors::HofError::SchemaFailure { .. }),
        "the scenario must fail on the Tester's schema gate, got {typed:?}"
    );

    let result: Value = serde_json::from_str(&read(&run_dir.join("iter-1/result.json"))).unwrap();
    assert_eq!(result["ok"], json!(false), "{result}");
    assert_eq!(result["failed_role"], json!("tester"), "{result}");

    // ① the candidate identity the round really froze.
    let candidate_id = result["candidate_id"]
        .as_str()
        .unwrap_or_else(|| panic!("candidate_id must be the real A_1, not null: {result}"));
    assert_eq!(
        candidate_id.len(),
        64,
        "A_1 is a sha256 hex digest: {candidate_id}"
    );
    let version_id = result["version_id"]
        .as_str()
        .unwrap_or_else(|| panic!("version_id must be the real snapshot, not null: {result}"));

    // …and it is the same identity the version index stores, so the value is not
    // merely well-shaped.
    let index: Value = serde_json::from_str(&read(&run_dir.join("versions/index.json"))).unwrap();
    let versions = index["versions"].as_array().expect("versions");
    assert!(
        versions
            .iter()
            .any(|entry| entry["version_id"] == json!(version_id)
                && entry["candidate_id"] == json!(candidate_id)),
        "result.json must name the version the store actually wrote: {index}"
    );

    // ② the battery the round really ran (11 steps, all ok in this fixture).
    let passes = result["battery_passes"].as_array().unwrap_or_else(|| {
        panic!("battery_passes must not be empty on the failure path: {result}")
    });
    assert_eq!(passes.len(), 1, "one pass ran: {passes:?}");
    let steps = passes[0]["steps"].as_array().expect("step list");
    assert!(
        steps.len() >= 10,
        "the persisted pass must list every battery step, not a stub: {steps:?}"
    );
    assert!(
        steps.iter().all(|step| step[1] == json!(true)),
        "this fixture's battery is green; the failure is the Tester's: {steps:?}"
    );

    // The report's §5 "after" evidence is this line, printed by the same run
    // that makes the assertions (`cargo test … -- --nocapture`).
    println!(
        "DR-68 failure stub (after): candidate_id={candidate_id} version_id={version_id} \
         battery_passes={} steps={}",
        passes.len(),
        steps.len()
    );
}

// ---------------------------------------------------------------------------
// DR-73 ③ — E3's other two behaviours must be observed in-round
// ---------------------------------------------------------------------------
//
// `REQUIREMENTS.md:114` names four behaviours.  `input_replay` observed two of
// them, so `smoke-t10` ended with `Coins: 0` for the whole round and
// `Goal.reached` never true, and E3 was `not_met` for a reason no role could see
// in the evidence it was handed.  The tests below are the acceptance shape for
// the window that closes that hole: **the battery's own products must carry a
// pickup assertion and a win assertion, in the same evidence form the movement
// windows use** (before/after frames plus an engine-accepted node-state
// assertion), and a project that does not deliver them must be recorded as a gap
// rather than passing.

/// The canonical green run for these tests.
async fn interaction_run(root: &Path, mode: InteractionMode) -> (BatteryRun, Arc<FixtureChannel>) {
    let channel = Arc::new(FixtureChannel::green().with_interaction(mode));
    let run = run_battery(root, channel.clone(), 30).await;
    (run, channel)
}

fn interaction_raw(run: &BatteryRun) -> Value {
    serde_json::from_str(&read(
        &run.run_dir
            .join("iter-1/candidate/.hoh/deterministic/raw/interaction_evidence.json"),
    ))
    .unwrap()
}

/// DR-73 ③: the battery really produces the pickup evidence — a counter read
/// that grew, a `text:neq <before>` assertion the engine accepted, and the two
/// frames of the window.
#[tokio::test]
async fn the_interaction_window_records_a_real_coin_pickup_and_its_assertion() {
    let temp = tempfile::tempdir().unwrap();
    let (run, channel) = interaction_run(temp.path(), InteractionMode::Working).await;

    let step = step(&run.records, "interaction_evidence");
    assert!(
        step.ok,
        "the interaction window must be green on a project that delivers the behaviour: {}",
        step.record.observation
    );
    for support in ["F10", "F13"] {
        assert!(
            step.supports.iter().any(|id| id == support),
            "the window must declare {support}: {:?}",
            step.supports
        );
    }
    assert!(
        step.record.observation.contains("COIN_PICKED_UP"),
        "the pickup must be named in the observation: {}",
        step.record.observation
    );
    assert!(
        step.record.observation.contains("WIN_DRIVEN"),
        "the win must be named in the observation: {}",
        step.record.observation
    );

    // The evidence form: before/after frames, really on disk.
    for phase in ["before", "after"] {
        let relative = format!(".hoh/evidence/replay-interaction-{phase}.png");
        let bytes = std::fs::read(run.workspace.join(&relative))
            .unwrap_or_else(|error| panic!("{relative}: {error}"));
        assert_eq!(&bytes[..8], b"\x89PNG\r\n\x1a\n", "a real PNG signature");
    }

    let raw = interaction_raw(&run);
    let calls = raw["calls"].as_array().expect("raw call list");
    // The frame captures carry the labels the rest of the battery uses.
    for phase in ["before", "after"] {
        assert!(
            calls.iter().any(|call| {
                call["label"] == json!(format!("interaction:replay_frame_{phase}"))
                    && call["tool"] == json!("running_game_capture_screenshot")
            }),
            "the {phase} frame must be captured by the window: {calls:?}"
        );
    }

    // The pickup assertion is positional/stateful on purpose: `input_axis`
    // answers `null` on real hardware (DR-58), so the counter's text is the
    // observable.  The expectation is the **before** reading, and the engine's
    // answer must be `passed: true`.
    let pickup = calls
        .iter()
        .find(|call| call["label"] == json!("interaction:replay_assert_picked_up"))
        .unwrap_or_else(|| panic!("no pickup assertion was made: {calls:?}"));
    assert_eq!(pickup["tool"], json!("running_game_assert_node_state"));
    assert_eq!(pickup["args"]["property"], json!("text"));
    assert_eq!(pickup["args"]["operator"], json!("neq"));
    // The expectation is the window's own **before** reading, taken from the
    // first coin-counter read the window made — not a constant the test invented.
    let first_counter_read = calls
        .iter()
        .find(|call| {
            call["tool"] == json!("running_game_get_node_properties")
                && call["args"]["node_path"]
                    .as_str()
                    .map(|path| path.ends_with("Coins"))
                    .unwrap_or(false)
        })
        .expect("the window reads the counter before it drives");
    let before_payload: Value = serde_json::from_str(
        first_counter_read["payload"]["content"][0]["text"]
            .as_str()
            .unwrap(),
    )
    .unwrap();
    assert_eq!(
        pickup["args"]["expected"],
        json!(before_payload["properties"]["text"]
            .as_str()
            .unwrap()
            .to_string()),
        "the expectation is the window's own before reading"
    );
    let payload: Value =
        serde_json::from_str(pickup["payload"]["content"][0]["text"].as_str().unwrap()).unwrap();
    assert_eq!(
        payload["passed"],
        json!(true),
        "the engine must accept the pickup assertion: {payload}"
    );
    assert_eq!(payload["actual"], json!("Coins: 1"), "{payload}");

    // The win assertion, the same shape against the goal's own flag.
    let won = calls
        .iter()
        .find(|call| call["label"] == json!("interaction:replay_assert_won"))
        .unwrap_or_else(|| panic!("no win assertion was made: {calls:?}"));
    assert_eq!(won["tool"], json!("running_game_assert_node_state"));
    assert_eq!(won["args"]["property"], json!("reached"));
    assert_eq!(won["args"]["operator"], json!("neq"));
    assert_eq!(won["args"]["expected"], json!(false));
    let payload: Value =
        serde_json::from_str(won["payload"]["content"][0]["text"].as_str().unwrap()).unwrap();
    assert_eq!(payload["passed"], json!(true), "{payload}");

    // The assertions are about what the game did, not about what the harness
    // wished: the window never wrote a property, it only read and drove input.
    let tool_names: Vec<&str> = calls
        .iter()
        .filter_map(|call| call["tool"].as_str())
        .collect();
    assert!(
        !tool_names
            .iter()
            .any(|name| name.contains("set_node_property")),
        "the window must not write the behaviour it claims to observe: {tool_names:?}"
    );
    assert!(tool_names
        .iter()
        .any(|name| name.starts_with("running_game_") && name.contains("assert")));
    assert!(
        tool_names.contains(&"running_game_run_test_scenario")
            || tool_names.contains(&"running_game_play_input_recording"),
        "the window must drive the game through the contract's semantic input API: {tool_names:?}"
    );

    // The window stops as soon as the goal is reached instead of spending the
    // whole batch budget.
    assert!(
        channel.interactions() > 0,
        "the drive really reached the level's coin"
    );
    assert!(
        step.record
            .observation
            .contains("stopped as soon as the win was observed"),
        "the win must end the drive early: {}",
        step.record.observation
    );
}

/// DR-73 ③: the round's own state.  The player sweeps both coins, the HUD never
/// moves off `Coins: 0` and the goal flag never turns, so the window is a
/// **gap** with the numbers that say why.
#[tokio::test]
async fn a_project_that_never_picks_a_coin_up_is_recorded_as_a_gap() {
    let temp = tempfile::tempdir().unwrap();
    let (run, _) = interaction_run(temp.path(), InteractionMode::NoPickupNoWin).await;

    let step = step(&run.records, "interaction_evidence");
    assert!(
        !step.ok,
        "a project with no pickup must not pass the interaction window: {}",
        step.record.observation
    );
    let observation = &step.record.observation;
    assert!(
        observation.contains("COIN_NOT_PICKED_UP"),
        "the coin gap must be named: {observation}"
    );
    assert!(
        observation.contains("WIN_NOT_DRIVEN"),
        "the win gap must be named: {observation}"
    );
    assert!(
        observation.contains("Coins: 0 -> Coins: 0"),
        "the counter readings must be in the record: {observation}"
    );
    assert!(
        observation.contains("player max x=") && observation.contains("goal.position="),
        "the reachability numbers must be in the record: {observation}"
    );
    assert!(
        observation.starts_with("FAILED interaction:") && observation.contains("UNAVAILABLE"),
        "an unobservable behaviour is unavailable evidence, not a soft pass: {observation}"
    );

    // The refusal is the engine's: the same assertion that passes on the green
    // fixture answers `passed: false` here, so the record cannot be explained
    // away as "the window never asked".
    let raw = interaction_raw(&run);
    let calls = raw["calls"].as_array().expect("raw call list");
    let pickup = calls
        .iter()
        .find(|call| call["label"] == json!("interaction:replay_assert_picked_up"))
        .expect("the window asks even when the answer is no");
    let payload: Value =
        serde_json::from_str(pickup["payload"]["content"][0]["text"].as_str().unwrap()).unwrap();
    assert_eq!(payload["passed"], json!(false), "{payload}");
    assert_eq!(payload["actual"], json!("Coins: 0"), "{payload}");
}

/// DR-73 ③: a level whose goal sits past the end of the traversable ground.  The
/// pickup still happens, so the two behaviours are judged **separately** — a
/// single "E3 okay" flag could not express this, and `smoke-t10`'s two gaps were
/// exactly that.
#[tokio::test]
async fn a_level_whose_goal_is_unreachable_fails_only_the_win_half() {
    let temp = tempfile::tempdir().unwrap();
    let (run, _) = interaction_run(temp.path(), InteractionMode::NoWin).await;

    let observation = &step(&run.records, "interaction_evidence")
        .record
        .observation;
    assert!(
        observation.contains("COIN_PICKED_UP"),
        "the pickup must still be observed: {observation}"
    );
    assert!(
        observation.contains("WIN_NOT_DRIVEN"),
        "the unreachable goal must be reported as a win gap: {observation}"
    );
    assert!(
        observation.contains("goal.position=Some(") && observation.contains("6400"),
        "the goal's own position must be in the record, so 'unreachable' is measurable: {observation}"
    );
    assert!(
        observation.contains("player max x=Some(320"),
        "the player's reachable maximum must be in the record: {observation}"
    );
}

/// DR-73 ③: no `Coins:` label at all.  The window must say the counter is
/// unreadable rather than reading a missing cell as "zero coins, no pickup" —
/// the two are different gaps with different fixes.
#[tokio::test]
async fn a_hud_without_a_coin_cell_is_reported_as_unreadable_not_as_zero() {
    let temp = tempfile::tempdir().unwrap();
    let (run, _) = interaction_run(temp.path(), InteractionMode::UnreadableCounter).await;

    let observation = &step(&run.records, "interaction_evidence")
        .record
        .observation;
    assert!(
        observation.contains("COIN_COUNTER_UNREADABLE"),
        "an unreadable counter is its own verdict: {observation}"
    );
    assert!(
        !observation.contains("COIN_NOT_PICKED_UP"),
        "an unreadable counter must not be reported as a measured zero: {observation}"
    );
}
