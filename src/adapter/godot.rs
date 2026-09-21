//! `GodotAdapter`: the first project adapter (A3).
//!
//! It knows three things: what a minimal Godot 4 project looks like, which MCP
//! tools constitute a deterministic build/boot check, and what a Tester must
//! collect as evidence.

use std::path::Path;

use serde_json::{json, Value};

use crate::adapter::{BatteryRecord, BatteryStep, DoctorItem, ProjectAdapter};
use crate::config::GodotConfig;
use crate::model::{ExecKind, ExecRecord, Role};
use crate::tools::reliable::{
    call_with_retries, wait_for_game_ready, McpErrorLog, McpFailure, ReadyOutcome,
    READY_POLL_INTERVAL_MS, RETRY_INTERVAL_MS,
};
use crate::tools::ToolChannel;

/// DR-20/DR-17: the knobs the battery needs, taken from `config.tools`.
#[derive(Clone, Debug)]
pub struct BatteryLimits {
    pub ready_timeout_seconds: u64,
    pub max_retries: u32,
    pub timeout_seconds: u64,
}

impl Default for BatteryLimits {
    fn default() -> Self {
        Self {
            ready_timeout_seconds: 30,
            max_retries: 2,
            timeout_seconds: 120,
        }
    }
}

#[derive(Clone, Debug)]
pub struct GodotAdapter {
    pub config: GodotConfig,
    pub force_init: bool,
    pub battery: BatteryLimits,
}

const PROJECT_GODOT: &str = r#"; Engine configuration file.
config_version=5

[application]

config/name="HoH Mario"
run/main_scene="res://scenes/main.tscn"
config/features=PackedStringArray("4.7")

[display]

window/size/viewport_width=640
window/size/viewport_height=360

[input]

move_left={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":4194319,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
]
}
move_right={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":4194321,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
]
}
jump={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":32,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
]
}

[rendering]

renderer/rendering_method="gl_compatibility"

[editor_plugins]

enabled=PackedStringArray("res://addons/godot_mcp_rs/plugin.cfg")
"#;

/// The plugin entry `initialize` must guarantee (DR-4).
pub const MCP_PLUGIN_PATH: &str = "res://addons/godot_mcp_rs/plugin.cfg";
const EDITOR_PLUGINS_HEADER: &str = "[editor_plugins]";

const MAIN_SCENE: &str = r#"[gd_scene load_steps=2 format=3]

[node name="Main" type="Node2D"]

[node name="Ground" type="StaticBody2D" parent="."]

[node name="CollisionShape2D" type="CollisionShape2D" parent="Ground"]

[node name="Player" type="CharacterBody2D" parent="."]

[node name="Goal" type="Area2D" parent="."]

[node name="HUD" type="CanvasLayer" parent="."]
"#;

impl GodotAdapter {
    pub fn new(config: GodotConfig, force_init: bool) -> Self {
        Self {
            config,
            force_init,
            battery: BatteryLimits::default(),
        }
    }

    /// DR-17/DR-20: adopt the `tools.*` settings for the evidence battery.
    pub fn with_battery_limits(mut self, battery: BatteryLimits) -> Self {
        self.battery = battery;
        self
    }
}

/// Unwrap the MCP `tools/call` envelope (`content[*].text`) into the payload the
/// server actually reported.  Every real evidence fixture has this shape.
pub fn unwrap_mcp_payload(payload: &Value) -> Value {
    let Some(content) = payload.get("content").and_then(Value::as_array) else {
        return payload.clone();
    };
    let texts: Vec<String> = content
        .iter()
        .filter_map(|item| item.get("text").and_then(Value::as_str))
        .map(ToOwned::to_owned)
        .collect();
    match texts.len() {
        0 => payload.clone(),
        1 => serde_json::from_str(&texts[0]).unwrap_or_else(|_| Value::String(texts[0].clone())),
        _ => Value::Array(texts.into_iter().map(Value::String).collect()),
    }
}

fn call_ok(tool: &str, args: &Value, payload: &Value) -> Value {
    json!({"tool": tool, "args": args, "ok": true, "payload": payload})
}

fn call_fail(tool: &str, args: &Value, failure: &McpFailure) -> Value {
    json!({
        "tool": tool,
        "args": args,
        "ok": false,
        "error": {"code": failure.code, "message": failure.message, "attempts": failure.attempts},
    })
}

/// DR-17: the deterministic evidence battery, executed on the real workspace.
///
/// The step order is frozen by the design; each step declares the PRD
/// requirements (`F1..F17` / `N1..N4`) it can produce evidence for, and a
/// failed step is recorded honestly (`ok = false`, verbatim JSON-RPC text,
/// `UNAVAILABLE`) instead of being skipped.
struct BatterySession<'a> {
    workspace: &'a Path,
    tools: &'a dyn ToolChannel,
    limits: &'a BatteryLimits,
    log: McpErrorLog,
    records: Vec<BatteryRecord>,
}

impl<'a> BatterySession<'a> {
    fn new(workspace: &'a Path, tools: &'a dyn ToolChannel, limits: &'a BatteryLimits) -> Self {
        Self {
            workspace,
            tools,
            limits,
            log: McpErrorLog::new(workspace),
            records: Vec::new(),
        }
    }

    async fn call(&self, tool: &str, args: Value) -> Result<Value, McpFailure> {
        call_with_retries(
            self.tools,
            Role::Tester,
            tool,
            args,
            self.limits.max_retries,
            RETRY_INTERVAL_MS,
            Some(&self.log),
        )
        .await
    }

    async fn ready(&self, tool: &str, args: Value) -> ReadyOutcome {
        wait_for_game_ready(
            self.tools,
            Role::Tester,
            tool,
            args,
            self.limits.ready_timeout_seconds,
            READY_POLL_INTERVAL_MS,
            Some(&self.log),
        )
        .await
    }

    /// Persist the step's raw payloads and build its record.
    async fn finish(
        &mut self,
        step: BatteryStep,
        kind: ExecKind,
        path: Option<String>,
        observation: String,
        ok: bool,
        calls: Vec<Value>,
    ) -> anyhow::Result<()> {
        let rel = format!(".hoh/deterministic/raw/{}.json", step.id);
        let doc = json!({
            "step": step.id,
            "supports": step.supports,
            "ok": ok,
            "calls": calls,
        });
        let target = self.workspace.join(&rel);
        if let Some(parent) = target.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let mut serialized = serde_json::to_string_pretty(&doc)?;
        if !serialized.ends_with('\n') {
            serialized.push('\n');
        }
        std::fs::write(&target, serialized)?;
        self.records.push(BatteryRecord {
            step_id: step.id,
            supports: step.supports,
            record: ExecRecord {
                kind,
                path,
                observation,
                candidate_id: String::new(),
            },
            ok,
            raw_path: Some(rel),
        });
        Ok(())
    }

    async fn run(mut self) -> anyhow::Result<Vec<BatteryRecord>> {
        self.step_editor_errors().await?;
        let scene_tree = self.step_play_scene().await?;
        self.step_scene_tree(scene_tree.clone()).await?;
        self.step_screenshot().await?;
        self.step_input_replay().await?;
        self.step_node_assertions(scene_tree).await?;
        self.step_stop_scene().await?;
        Ok(self.records)
    }

    /// 1. Editor error baseline — taken *before* the project is started.
    async fn step_editor_errors(&mut self) -> anyhow::Result<()> {
        let step = BatteryStep {
            id: "editor_errors_baseline".to_string(),
            supports: vec!["N1".to_string(), "N3".to_string()],
            timeout_secs: self.limits.timeout_seconds,
            retries: self.limits.max_retries,
        };
        let args = json!({"max_lines": 50});
        let (ok, observation, call) = match self.call("get_editor_errors", args.clone()).await {
            Ok(payload) => {
                let parsed = unwrap_mcp_payload(&payload);
                let observation = describe_editor_errors(&parsed);
                let ok = parsed
                    .get("errors")
                    .and_then(Value::as_array)
                    .map(|errors| errors.is_empty())
                    .unwrap_or(false);
                let observation = if ok {
                    observation
                } else {
                    format!("{observation} (UNAVAILABLE: the editor is not clean)")
                };
                (
                    ok,
                    observation,
                    call_ok("get_editor_errors", &args, &payload),
                )
            }
            Err(failure) => (
                false,
                failure.observation(),
                call_fail("get_editor_errors", &args, &failure),
            ),
        };
        self.finish(step, ExecKind::Build, None, observation, ok, vec![call])
            .await
    }

    /// 2. `play_scene` plus the readiness wait (DR-20).
    async fn step_play_scene(&mut self) -> anyhow::Result<Option<Value>> {
        let step = BatteryStep {
            id: "play_scene_ready".to_string(),
            supports: vec!["N1".to_string()],
            timeout_secs: self.limits.ready_timeout_seconds,
            retries: self.limits.max_retries,
        };
        let play_args = json!({"mode": "main"});
        let mut calls = Vec::new();
        let play = self.call("play_scene", play_args.clone()).await;
        let play = match play {
            Ok(payload) => {
                calls.push(call_ok("play_scene", &play_args, &payload));
                payload
            }
            Err(failure) => {
                calls.push(call_fail("play_scene", &play_args, &failure));
                let observation =
                    format!("FAILED play_scene: {} (UNAVAILABLE)", failure.observation());
                self.finish(
                    step,
                    ExecKind::RuntimeTrace,
                    None,
                    observation,
                    false,
                    calls,
                )
                .await?;
                return Ok(None);
            }
        };
        let _ = play;

        let tree_args = json!({"max_depth": -1});
        let ready = self.ready("get_game_scene_tree", tree_args.clone()).await;
        match ready {
            ReadyOutcome {
                ok: true,
                attempts,
                payload,
                ..
            } => {
                let payload = payload.expect("a successful readiness poll carries a payload");
                calls.push(call_ok("get_game_scene_tree", &tree_args, &payload));
                let tree = unwrap_mcp_payload(&payload);
                let observation = format!(
                    "main scene booted; the game answered get_game_scene_tree after {attempts} \
                     poll(s); scene tree: {tree}"
                );
                self.finish(step, ExecKind::RuntimeTrace, None, observation, true, calls)
                    .await?;
                Ok(Some(tree))
            }
            ReadyOutcome {
                ok: false,
                attempts,
                failure,
                ..
            } => {
                let failure = failure
                    .unwrap_or_else(|| McpFailure::new("get_game_scene_tree", None, "timeout", 0));
                calls.push(call_fail("get_game_scene_tree", &tree_args, &failure));
                let observation = format!(
                    "FAILED the main scene was started but never became observable after \
                     {attempts} poll(s): {} (UNAVAILABLE)",
                    failure.observation()
                );
                self.finish(
                    step,
                    ExecKind::RuntimeTrace,
                    None,
                    observation,
                    false,
                    calls,
                )
                .await?;
                Ok(None)
            }
        }
    }

    /// 3. The running scene tree (node existence).
    async fn step_scene_tree(&mut self, cached: Option<Value>) -> anyhow::Result<()> {
        let step = BatteryStep {
            id: "scene_tree".to_string(),
            supports: vec!["N2".to_string(), "F5".to_string()],
            timeout_secs: self.limits.timeout_seconds,
            retries: self.limits.max_retries,
        };
        let args = json!({"max_depth": -1});
        let mut calls = Vec::new();
        let tree: Option<Value> = match self.call("get_game_scene_tree", args.clone()).await {
            Ok(payload) => {
                calls.push(call_ok("get_game_scene_tree", &args, &payload));
                Some(unwrap_mcp_payload(&payload))
            }
            Err(failure) => {
                calls.push(call_fail("get_game_scene_tree", &args, &failure));
                // The readiness poll already captured a tree for this run; it
                // is a legitimate fallback, but the failed fresh call is never
                // hidden.
                match cached {
                    Some(cached) => {
                        calls.push(json!({
                            "tool": "get_game_scene_tree",
                            "source": "play_scene_ready",
                            "payload": cached,
                        }));
                        Some(cached)
                    }
                    None => None,
                }
            }
        };
        let has_children = tree
            .as_ref()
            .and_then(|tree| tree.get("tree"))
            .and_then(|root| root.get("children"))
            .and_then(Value::as_array)
            .map(|children| !children.is_empty())
            .unwrap_or(false);
        let observation = match &tree {
            Some(tree) if has_children => format!("scene tree: {tree}"),
            Some(tree) => format!(
                "FAILED the scene tree has no children: {tree} (UNAVAILABLE: no node evidence)"
            ),
            None => "FAILED no scene tree was captured (UNAVAILABLE)".to_string(),
        };
        self.finish(
            step,
            ExecKind::RuntimeTrace,
            None,
            observation,
            has_children,
            calls,
        )
        .await?;
        Ok(())
    }

    /// 4. Screenshot, stored under `.hoh/evidence/` and referenced relatively.
    async fn step_screenshot(&mut self) -> anyhow::Result<()> {
        let step = BatteryStep {
            id: "screenshot".to_string(),
            supports: vec![
                "N2".to_string(),
                "F4".to_string(),
                "F13".to_string(),
                "F16".to_string(),
            ],
            timeout_secs: self.limits.timeout_seconds,
            retries: self.limits.max_retries,
        };
        let relative = ".hoh/evidence/frame-00.png".to_string();
        let absolute = self.workspace.join(&relative);
        if let Some(parent) = absolute.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let save_path = absolute.to_string_lossy().into_owned();
        let args = json!({"save_path": save_path});
        let mut calls = Vec::new();

        let primary = self.call("get_game_screenshot", args.clone()).await;
        let outcome = match primary {
            Ok(payload) => {
                calls.push(call_ok("get_game_screenshot", &args, &payload));
                if absolute.is_file() {
                    Ok(format!(
                        "screenshot written to {relative}: {}",
                        unwrap_mcp_payload(&payload)
                    ))
                } else {
                    Err(format!(
                        "FAILED get_game_screenshot reported success but no file exists at {} \
                         (UNAVAILABLE)",
                        absolute.display()
                    ))
                }
            }
            Err(failure) => {
                calls.push(call_fail("get_game_screenshot", &args, &failure));
                let frames_args = json!({"count": 1, "frame_interval": 10});
                match self.call("capture_frames", frames_args.clone()).await {
                    Ok(payload) => {
                        calls.push(call_ok("capture_frames", &frames_args, &payload));
                        Ok(format!(
                            "get_game_screenshot failed ({}); capture_frames returned {}",
                            failure.observation(),
                            unwrap_mcp_payload(&payload)
                        ))
                    }
                    Err(frames_failure) => Err(format!(
                        "FAILED screenshot unavailable: {} / {} (UNAVAILABLE)",
                        failure.observation(),
                        frames_failure.observation()
                    )),
                }
            }
        };
        let (ok, observation, path) = match outcome {
            Ok(observation) => (true, observation, Some(relative)),
            Err(observation) => (false, observation, None),
        };
        self.finish(step, ExecKind::Screenshot, path, observation, ok, calls)
            .await?;
        Ok(())
    }

    /// 5. Input replay: drive `move_right` / `jump` / `move_left` and record
    ///    the `Player` position over time.
    async fn step_input_replay(&mut self) -> anyhow::Result<()> {
        let step = BatteryStep {
            id: "input_replay".to_string(),
            supports: vec!["F1".to_string(), "F2".to_string(), "F3".to_string()],
            timeout_secs: self.limits.timeout_seconds,
            retries: self.limits.max_retries,
        };
        let mut calls = Vec::new();
        let mut summaries: Vec<String> = Vec::new();
        let mut ok = true;

        for (label, action, frames) in [
            ("move_right", "move_right", 60u64),
            ("move_right_release", "move_right", 10),
            ("jump", "jump", 30),
            ("move_left", "move_left", 60),
        ] {
            let press_args = json!({"action": action, "pressed": true});
            match self.call("simulate_action", press_args.clone()).await {
                Ok(payload) => calls.push(call_ok("simulate_action", &press_args, &payload)),
                Err(failure) => {
                    calls.push(call_fail("simulate_action", &press_args, &failure));
                    summaries.push(format!("{label}: FAILED {}", failure.message));
                    ok = false;
                    continue;
                }
            }
            let monitor_args = json!({
                "node_path": "Player",
                "properties": ["position"],
                "frame_count": frames,
                "frame_interval": 1,
            });
            match self.call("monitor_properties", monitor_args.clone()).await {
                Ok(payload) => {
                    calls.push(call_ok("monitor_properties", &monitor_args, &payload));
                    summaries.push(describe_monitor(label, &unwrap_mcp_payload(&payload)));
                }
                Err(failure) => {
                    calls.push(call_fail("monitor_properties", &monitor_args, &failure));
                    summaries.push(format!("{label}: FAILED {}", failure.message));
                    ok = false;
                }
            }
            let release_args = json!({"action": action, "pressed": false});
            match self.call("simulate_action", release_args.clone()).await {
                Ok(payload) => calls.push(call_ok("simulate_action", &release_args, &payload)),
                Err(failure) => {
                    calls.push(call_fail("simulate_action", &release_args, &failure));
                    ok = false;
                }
            }
        }

        let observation = if ok {
            format!("input replay: {}", summaries.join("; "))
        } else {
            format!(
                "FAILED input replay: {} (UNAVAILABLE: the recording is incomplete)",
                summaries.join("; ")
            )
        };
        self.finish(step, ExecKind::Replay, None, observation, ok, calls)
            .await?;
        Ok(())
    }

    /// 6. Node properties, collision shapes, and HUD text.
    async fn step_node_assertions(&mut self, scene_tree: Option<Value>) -> anyhow::Result<()> {
        let step = BatteryStep {
            id: "node_and_collision_assertions".to_string(),
            supports: vec![
                "F5".to_string(),
                "F6".to_string(),
                "F10".to_string(),
                "F13".to_string(),
                "F14".to_string(),
                "F16".to_string(),
            ],
            timeout_secs: self.limits.timeout_seconds,
            retries: self.limits.max_retries,
        };
        let mut calls = Vec::new();
        let mut ok = true;
        let mut property_summary: Vec<String> = Vec::new();

        for node in ["Player", "Goal", "HUD"] {
            let args = json!({"node_path": node});
            match self.call("get_game_node_properties", args.clone()).await {
                Ok(payload) => {
                    let parsed = unwrap_mcp_payload(&payload);
                    calls.push(call_ok("get_game_node_properties", &args, &payload));
                    let present = parsed
                        .get("name")
                        .and_then(Value::as_str)
                        .map(|name| !name.is_empty())
                        .unwrap_or(false);
                    property_summary
                        .push(format!("{node}={}", if present { "ok" } else { "missing" }));
                    if !present {
                        ok = false;
                    }
                }
                Err(failure) => {
                    calls.push(call_fail("get_game_node_properties", &args, &failure));
                    property_summary.push(format!("{node}=FAILED"));
                    ok = false;
                }
            }
        }

        let mut shape_summary: Vec<String> = Vec::new();
        for node in ["Ground", "Player", "Goal"] {
            let args = json!({"node_path": node});
            match self.call("get_collision_info", args.clone()).await {
                Ok(payload) => {
                    let parsed = unwrap_mcp_payload(&payload);
                    calls.push(call_ok("get_collision_info", &args, &payload));
                    let shapes = parsed
                        .get("shape_count")
                        .and_then(Value::as_u64)
                        .unwrap_or(0);
                    shape_summary.push(format!("{node}={shapes}"));
                    if shapes == 0 {
                        // DR-17/DR-23: a physics body with no shape cannot
                        // satisfy F5/F6/F13, and the evidence is unavailable.
                        ok = false;
                    }
                }
                Err(failure) => {
                    calls.push(call_fail("get_collision_info", &args, &failure));
                    shape_summary.push(format!("{node}=FAILED"));
                    ok = false;
                }
            }
        }

        let text_nodes = scene_tree.as_ref().map(count_hud_text_nodes).unwrap_or(0);
        if text_nodes == 0 {
            ok = false;
        }

        let observation = format!(
            "node properties: {}; collision shape_count: {}; HUD visible text node(s): {}{}",
            property_summary.join(", "),
            shape_summary.join(", "),
            text_nodes,
            if ok {
                String::new()
            } else {
                " (UNAVAILABLE: at least one required node or collision shape is missing)"
                    .to_string()
            }
        );
        self.finish(step, ExecKind::Assert, None, observation, ok, calls)
            .await?;
        Ok(())
    }

    /// 7. Stop the running scene so the next stage starts clean.
    async fn step_stop_scene(&mut self) -> anyhow::Result<()> {
        let step = BatteryStep {
            id: "stop_scene".to_string(),
            supports: vec!["N1".to_string()],
            timeout_secs: self.limits.timeout_seconds,
            retries: self.limits.max_retries,
        };
        let args = json!({});
        let (ok, observation, call) = match self.call("stop_scene", args.clone()).await {
            Ok(payload) => (
                true,
                format!("stop_scene: {}", unwrap_mcp_payload(&payload)),
                call_ok("stop_scene", &args, &payload),
            ),
            Err(failure) => (
                false,
                format!("FAILED stop_scene: {} (UNAVAILABLE)", failure.observation()),
                call_fail("stop_scene", &args, &failure),
            ),
        };
        self.finish(
            step,
            ExecKind::RuntimeTrace,
            None,
            observation,
            ok,
            vec![call],
        )
        .await
    }
}

/// DR-17 step 5: a compact, human-checkable summary of one recording.
fn describe_monitor(label: &str, payload: &Value) -> String {
    let frames = payload
        .get("frame_count")
        .and_then(Value::as_u64)
        .unwrap_or(0);
    let positions: Vec<(f64, f64)> = payload
        .get("samples")
        .and_then(Value::as_array)
        .map(|samples| {
            samples
                .iter()
                .filter_map(|sample| sample.get("position").and_then(Value::as_object))
                .map(|position| {
                    (
                        position.get("x").and_then(Value::as_f64).unwrap_or(0.0),
                        position.get("y").and_then(Value::as_f64).unwrap_or(0.0),
                    )
                })
                .collect()
        })
        .unwrap_or_default();
    let span = match (positions.first(), positions.last()) {
        (Some(first), Some(last)) => format!(
            "({:.1},{:.1}) -> ({:.1},{:.1})",
            first.0, first.1, last.0, last.1
        ),
        _ => "unknown".to_string(),
    };
    format!("{label}: {frames} frame(s), position {span}")
}

/// Count visible text nodes (`Label`/`Button`/…) anywhere under `HUD`.
fn count_hud_text_nodes(tree: &Value) -> usize {
    let Some(root) = tree.get("tree") else {
        return 0;
    };
    let mut count = 0;
    visit_nodes(root, &mut |node| {
        let path = node.get("path").and_then(Value::as_str).unwrap_or("");
        let kind = node.get("type").and_then(Value::as_str).unwrap_or("");
        let is_text = matches!(
            kind,
            "Label" | "RichTextLabel" | "Label3D" | "Button" | "LinkButton" | "CheckBox"
        );
        if is_text && path.contains("/HUD/") {
            count += 1;
        }
    });
    count
}

fn visit_nodes(node: &Value, visit: &mut impl FnMut(&Value)) {
    visit(node);
    if let Some(children) = node.get("children").and_then(Value::as_array) {
        for child in children {
            visit_nodes(child, visit);
        }
    }
}

/// Write `lines` back as an LF-terminated file.
fn write_lines(path: &Path, lines: &[String]) -> anyhow::Result<()> {
    let mut text = lines.join("\n");
    text.push('\n');
    std::fs::write(path, text)?;
    Ok(())
}

/// Guarantee `[editor_plugins]` + `enabled` contains the MCP plugin (DR-4).
///
/// Idempotent by construction: when the entry is already present the file is
/// left byte-for-byte untouched, and an existing `enabled` list keeps every
/// other plugin it names.
fn ensure_plugin_enabled(project_file: &Path) -> anyhow::Result<()> {
    let raw = std::fs::read_to_string(project_file)?;
    let mut lines: Vec<String> = raw.lines().map(ToOwned::to_owned).collect();

    let Some(header) = lines
        .iter()
        .position(|line| line.trim() == EDITOR_PLUGINS_HEADER)
    else {
        lines.push(String::new());
        lines.push(EDITOR_PLUGINS_HEADER.to_string());
        lines.push(String::new());
        lines.push(format!("enabled=PackedStringArray(\"{MCP_PLUGIN_PATH}\")"));
        return write_lines(project_file, &lines);
    };

    let end = (header + 1..lines.len())
        .find(|&index| lines[index].trim_start().starts_with('['))
        .unwrap_or(lines.len());
    let enabled = (header + 1..end).find(|&index| lines[index].trim_start().starts_with("enabled"));
    let Some(enabled) = enabled else {
        lines.insert(
            header + 1,
            format!("enabled=PackedStringArray(\"{MCP_PLUGIN_PATH}\")"),
        );
        return write_lines(project_file, &lines);
    };

    if lines[enabled].contains(MCP_PLUGIN_PATH) {
        // Already enabled: never touch the file.
        return Ok(());
    }

    let line = lines[enabled].clone();
    match (line.find('('), line.rfind(')')) {
        (Some(open), Some(close)) if close > open => {
            let inner = line[open + 1..close].trim();
            let inner = if inner.is_empty() {
                format!("\"{MCP_PLUGIN_PATH}\"")
            } else {
                format!("{inner}, \"{MCP_PLUGIN_PATH}\"")
            };
            lines[enabled] = format!(
                "{}PackedStringArray({inner}){}",
                &line[..open],
                &line[close + 1..]
            );
        }
        _ => {
            lines[enabled] = format!("enabled=PackedStringArray(\"{MCP_PLUGIN_PATH}\")");
        }
    }
    write_lines(project_file, &lines)
}

#[async_trait::async_trait]
impl ProjectAdapter for GodotAdapter {
    fn initialize(&self, workspace: &Path) -> anyhow::Result<()> {
        std::fs::create_dir_all(workspace)?;
        let project_file = workspace.join("project.godot");
        if project_file.is_file() {
            // Already a Godot project: scaffolding is a no-op, but the MCP
            // plugin enablement is still enforced (DR-4), so an `A₀` that was
            // created earlier can be repaired in place.
            return ensure_plugin_enabled(&project_file);
        }
        let non_empty = std::fs::read_dir(workspace)?.next().is_some();
        if non_empty && !self.force_init {
            anyhow::bail!(
                "workspace {} already exists and is not empty; pass --force-init to scaffold \
                 over it",
                workspace.display()
            );
        }

        std::fs::write(&project_file, PROJECT_GODOT)?;
        std::fs::create_dir_all(workspace.join("scenes"))?;
        std::fs::write(workspace.join("scenes/main.tscn"), MAIN_SCENE)?;
        std::fs::create_dir_all(workspace.join("scripts"))?;
        std::fs::write(
            workspace.join("scripts/README.md"),
            "# Scripts\n\nGDScript sources live here.\n",
        )?;

        let addon_source = &self.config.addon_source;
        if addon_source.is_dir() {
            let destination = workspace.join("addons/godot_mcp_rs");
            crate::runtime::view::copy_tree(addon_source, &destination, &[])?;
        } else {
            std::fs::write(
                workspace.join("ADDON_MISSING.txt"),
                format!(
                    "The Godot MCP addon source {} does not exist on this machine.\n",
                    addon_source.display()
                ),
            )?;
        }
        ensure_plugin_enabled(&project_file)?;
        Ok(())
    }

    /// Cache directories only.
    ///
    /// DR-11: adding a *real* artifact path here silently disables the
    /// `hash_tree` based write-detection of R2/R3 — the runtime excludes these
    /// names from hashing and from snapshots, so an excluded file can no longer
    /// be seen when a read-only role writes it.
    fn cache_excludes(&self) -> Vec<String> {
        let mut excludes = vec![".hoh".to_string(), ".git".to_string()];
        excludes.extend(self.config.cache_excludes.iter().cloned());
        excludes
    }

    /// DR-17: the seven-step deterministic evidence battery.
    ///
    /// Runs on the real workspace before `A_t` is frozen and hands the Tester a
    /// complete, honestly-failed record set instead of making it collect the
    /// evidence itself.
    async fn evidence_battery(
        &self,
        workspace: &Path,
        tools: &dyn ToolChannel,
    ) -> anyhow::Result<Vec<BatteryRecord>> {
        std::fs::create_dir_all(workspace.join(".hoh/deterministic/raw"))?;
        BatterySession::new(workspace, tools, &self.battery)
            .run()
            .await
    }

    async fn build_check(
        &self,
        _workspace: &Path,
        tools: &dyn ToolChannel,
    ) -> anyhow::Result<Vec<ExecRecord>> {
        let mut records = Vec::new();

        // 1. reload_project is executed by the runtime because the Tester is
        //    not allowed to call it; the result is informational only.
        let _ = tools
            .call(Role::Developer, "reload_project", serde_json::json!({}))
            .await;

        // 2. Editor errors.  DR-5: decide on the parsed `errors` array, never
        //    on a substring heuristic — an observation may legally contain the
        //    word "error" while the editor is clean, and vice versa.
        let errors = tools
            .call(Role::Tester, "get_editor_errors", serde_json::json!({}))
            .await;
        let observation = match errors {
            Ok(result) => describe_editor_errors(&result.payload),
            Err(error) => format!("get_editor_errors failed: {error}"),
        };
        records.push(ExecRecord {
            kind: ExecKind::Build,
            path: None,
            observation,
            candidate_id: String::new(),
        });

        // 3. Boot the main scene, snapshot the tree, then stop it.
        let play_args = serde_json::json!({"scene_path": self.config.main_scene});
        let play = tools.call(Role::Tester, "play_scene", play_args).await;
        let boot_observation = match play {
            Ok(_) => {
                let tree = tools
                    .call(Role::Tester, "get_game_scene_tree", serde_json::json!({}))
                    .await;
                let _ = tools
                    .call(Role::Tester, "stop_scene", serde_json::json!({}))
                    .await;
                match tree {
                    Ok(result) => format!("main scene booted; scene tree: {}", result.payload),
                    Err(error) => {
                        format!("main scene booted but get_game_scene_tree failed: {error}")
                    }
                }
            }
            Err(error) => format!("play_scene failed: {error}"),
        };
        records.push(ExecRecord {
            kind: ExecKind::RuntimeTrace,
            path: None,
            observation: boot_observation,
            candidate_id: String::new(),
        });

        Ok(records)
    }

    fn evidence_playbook(&self) -> String {
        r#"# Evidence playbook (Godot)

The runtime already ran the deterministic battery. Start by reading
`.hoh/deterministic/battery.json`: each entry names the PRD requirements it
`supports`, its observation and whether it is usable (`ok`). The verbatim
payloads are in `.hoh/deterministic/raw/<step>.json`.

Reference every artifact by a **relative** path (`.hoh/deterministic/...` or
`.hoh/evidence/...`). A step with `ok = false` is `UNAVAILABLE`: the claims it
supports must be `gap`.

## Battery steps and what they can support
| step_id | supports | what it shows |
|---|---|---|
| `editor_errors_baseline` | N1, N3 | the editor opens the project with no script errors |
| `play_scene_ready` | N1 | `play_scene` succeeded and the game answered `get_game_scene_tree` |
| `scene_tree` | N2, F5 | the running node tree exists |
| `screenshot` | N2, F4, F13, F16 | a frame was captured under `.hoh/evidence/` |
| `input_replay` | F1, F2, F3 | `move_right`/`jump`/`move_left` recordings of `Player.position` |
| `node_and_collision_assertions` | F5, F6, F10, F13, F14, F16 | node properties, `shape_count` per body, HUD text nodes |
| `stop_scene` | N1 | the game stopped cleanly |

## If you need a closer look (read-only / execution only)
```
$HOH_HOH_BIN tools call get_game_node_properties --args-file $HOH_ARTIFACT_DIR/args/props.json
# props.json: {"node_path":"Player","properties":["position"]}
$HOH_HOH_BIN tools call monitor_properties --args-file $HOH_ARTIFACT_DIR/args/monitor.json
# monitor.json: {"node_path":"Player","properties":["position"],"frame_count":60,"frame_interval":1}
$HOH_HOH_BIN tools call simulate_action --args-file $HOH_ARTIFACT_DIR/args/press.json
# press.json: {"action":"move_right","pressed":true}
$HOH_HOH_BIN tools call simulate_sequence --args-file $HOH_ARTIFACT_DIR/args/seq.json
# seq.json: {"events":[{"type":"action","action":"jump","pressed":true},
#                      {"type":"action","action":"jump","pressed":false}],"frame_delay":1}
$HOH_HOH_BIN tools call capture_frames --args-file $HOH_ARTIFACT_DIR/args/frames.json
# frames.json: {"count":1,"frame_interval":10}; frames land under `.hoh/evidence/`
$HOH_HOH_BIN tools call get_collision_info --args-file $HOH_ARTIFACT_DIR/args/col.json
# col.json: {"node_path":"Goal"}
$HOH_HOH_BIN tools call assert_node_state --args-file $HOH_ARTIFACT_DIR/args/assert.json
# assert.json: {"node_path":"Player","property":"position:x","operator":"gt","expected":0}
```

## Rules
- One `execution_records` entry per observation, with the verbatim output.
- A claim is `verified` only if the cited record visibly shows the behaviour.
- Anything you could not observe is a `gap` with `player_impact` and
  `recommended_update`.
- Never modify the project: use `simulate_*` inputs only.
"#
        .to_string()
    }

    fn tool_policy(&self, role: Role) -> Vec<String> {
        // The authoritative filter is the role matrix in the tool channel; this
        // list only documents the intent for `TOOLS.md` consumers.
        match role {
            Role::Planner => Vec::new(),
            Role::Developer => vec!["*".to_string()],
            Role::Tester => vec![
                "get_*".to_string(),
                "list_*".to_string(),
                "simulate_*".to_string(),
                "assert_*".to_string(),
                "capture_frames".to_string(),
                "play_scene".to_string(),
                "stop_scene".to_string(),
                "monitor_properties".to_string(),
            ],
        }
    }

    fn doctor(&self, workspace: &Path) -> anyhow::Result<Vec<DoctorItem>> {
        let mut items = Vec::new();
        let project = workspace.join("project.godot");
        items.push(DoctorItem {
            name: "godot.project_file".to_string(),
            ok: project.is_file(),
            detail: project.display().to_string(),
        });
        let addon = workspace.join("addons/godot_mcp_rs");
        items.push(DoctorItem {
            name: "godot.mcp_addon".to_string(),
            ok: addon.is_dir(),
            detail: addon.display().to_string(),
        });
        // DR-6: the editor-scope limitation cannot be verified from the
        // filesystem, so it is published as an explicit human-confirmation item
        // (ok = true: it never blocks a run, but it is never hidden either).
        items.push(DoctorItem {
            name: "godot.editor_scope".to_string(),
            ok: true,
            detail: format!(
                "{} Confirm manually that the project currently open in the editor is exactly \
                 this workspace ({}); the runtime cannot verify it.",
                crate::runtime::run_loop::MCP_SCOPE_WARNING,
                workspace.display()
            ),
        });
        Ok(items)
    }
}

/// DR-5: turn a `get_editor_errors` payload into an observation.
///
/// The editor's answer is the authoritative signal.  A payload that is not an
/// object carrying an `errors` array cannot be interpreted as "clean", so it is
/// conservatively recorded as an error together with its verbatim text.
fn describe_editor_errors(payload: &serde_json::Value) -> String {
    let rendered = payload.to_string();
    match payload.get("errors").and_then(serde_json::Value::as_array) {
        Some(errors) if errors.is_empty() => "editor has no errors".to_string(),
        Some(errors) => format!(
            "editor reported {} error(s):\n{rendered}",
            errors.len()
        ),
        None => format!(
            "the get_editor_errors payload could not be parsed as JSON (treated as errors):\n{rendered}"
        ),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::tools::ToolResult;
    use serde_json::Value;

    fn adapter(addon: &Path) -> GodotAdapter {
        GodotAdapter::new(
            GodotConfig {
                addon_source: addon.to_path_buf(),
                cache_excludes: vec![".godot".to_string(), ".import".to_string()],
                main_scene: "res://scenes/main.tscn".to_string(),
            },
            false,
        )
    }

    /// Minimal MCP stand-in: `get_editor_errors` returns a canned payload.
    struct StubChannel {
        errors: Value,
    }

    #[async_trait::async_trait]
    impl ToolChannel for StubChannel {
        fn allowed(&self, _role: Role, _tool: &str) -> bool {
            true
        }

        fn index_markdown(&self, _role: Role) -> String {
            String::new()
        }

        async fn call(&self, _role: Role, tool: &str, _args: Value) -> anyhow::Result<ToolResult> {
            let payload = match tool {
                "get_editor_errors" => self.errors.clone(),
                "play_scene" => serde_json::json!({"ok": true}),
                "get_game_scene_tree" => serde_json::json!({"tree": []}),
                _ => serde_json::json!({}),
            };
            Ok(ToolResult { ok: true, payload })
        }
    }

    async fn build_record(errors: Value) -> ExecRecord {
        let temp = tempfile::tempdir().unwrap();
        let workspace = temp.path().join("mario");
        std::fs::create_dir_all(&workspace).unwrap();
        let channel = StubChannel { errors };
        adapter(&temp.path().join("addon"))
            .build_check(&workspace, &channel)
            .await
            .unwrap()
            .into_iter()
            .next()
            .expect("the build record is always produced")
    }

    #[test]
    fn initializes_a_minimal_project() {
        let temp = tempfile::tempdir().unwrap();
        let workspace = temp.path().join("mario");
        let addon = temp.path().join("addon");
        std::fs::create_dir_all(&addon).unwrap();
        std::fs::write(addon.join("plugin.cfg"), "[plugin]\n").unwrap();

        adapter(&addon).initialize(&workspace).unwrap();

        let project = std::fs::read_to_string(workspace.join("project.godot")).unwrap();
        for action in ["move_left", "move_right", "jump"] {
            assert!(project.contains(action), "missing input action {action}");
        }
        assert!(workspace.join("scenes/main.tscn").is_file());
        assert!(workspace.join("addons/godot_mcp_rs/plugin.cfg").is_file());
    }

    #[test]
    fn initialization_is_idempotent_but_never_clobbers_a_foreign_directory() {
        let temp = tempfile::tempdir().unwrap();
        let addon = temp.path().join("addon");
        let workspace = temp.path().join("mario");

        adapter(&addon).initialize(&workspace).unwrap();
        std::fs::write(workspace.join("scripts/player.gd"), "extends Node\n").unwrap();
        // A second call on an existing Godot project is a no-op.
        adapter(&addon).initialize(&workspace).unwrap();
        assert!(workspace.join("scripts/player.gd").is_file());

        // A non-empty directory that is not a Godot project is refused.
        let foreign = temp.path().join("foreign");
        std::fs::create_dir_all(&foreign).unwrap();
        std::fs::write(foreign.join("notes.txt"), "hello\n").unwrap();
        assert!(adapter(&addon).initialize(&foreign).is_err());
    }

    /// DR-4: `initialize` enables the MCP plugin exactly once and never
    /// rewrites a project file that already lists it.
    #[test]
    fn initialize_enables_the_mcp_plugin_idempotently() {
        let temp = tempfile::tempdir().unwrap();
        let addon = temp.path().join("addon");
        std::fs::create_dir_all(&addon).unwrap();
        std::fs::write(addon.join("plugin.cfg"), "[plugin]\n").unwrap();
        let workspace = temp.path().join("mario");

        adapter(&addon).initialize(&workspace).unwrap();
        let first = std::fs::read_to_string(workspace.join("project.godot")).unwrap();
        assert!(first.contains("[editor_plugins]"), "project: {first}");
        assert_eq!(
            first.matches(MCP_PLUGIN_PATH).count(),
            1,
            "the plugin entry must appear exactly once: {first}"
        );

        adapter(&addon).initialize(&workspace).unwrap();
        let second = std::fs::read_to_string(workspace.join("project.godot")).unwrap();
        assert_eq!(first, second, "a second initialize must not touch the file");
        assert_eq!(second.matches(MCP_PLUGIN_PATH).count(), 1);
    }

    /// DR-4: a pre-existing `enabled` list keeps its other entries.
    #[test]
    fn initialize_preserves_other_enabled_plugins() {
        let temp = tempfile::tempdir().unwrap();
        let addon = temp.path().join("addon");
        let workspace = temp.path().join("mario");
        std::fs::create_dir_all(&workspace).unwrap();
        std::fs::write(
            workspace.join("project.godot"),
            "config_version=5\n\n[editor_plugins]\n\n\
             enabled=PackedStringArray(\"res://addons/other/plugin.cfg\")\n",
        )
        .unwrap();

        adapter(&addon).initialize(&workspace).unwrap();
        let updated = std::fs::read_to_string(workspace.join("project.godot")).unwrap();
        assert!(
            updated.contains("res://addons/other/plugin.cfg"),
            "{updated}"
        );
        assert_eq!(updated.matches(MCP_PLUGIN_PATH).count(), 1, "{updated}");

        adapter(&addon).initialize(&workspace).unwrap();
        assert_eq!(
            updated,
            std::fs::read_to_string(workspace.join("project.godot")).unwrap()
        );
    }

    /// DR-5: editor errors are decided by the parsed `errors` array length, not
    /// by a substring heuristic.
    #[tokio::test]
    async fn editor_errors_are_parsed_as_json() {
        // No errors — including the whitespace variant and a payload that
        // merely mentions the word "error".
        for payload in [
            serde_json::json!({"errors": []}),
            serde_json::json!({"status": "ok", "errors": []}),
            serde_json::json!({"errors": [], "note": "there is no error here"}),
        ] {
            let record = build_record(payload).await;
            assert_eq!(
                record.observation, "editor has no errors",
                "payload treated as an error: {}",
                record.observation
            );
        }

        // One error.
        let record = build_record(serde_json::json!({"errors": [{"message": "x"}]})).await;
        assert!(
            record.observation.contains("editor reported 1 error"),
            "{}",
            record.observation
        );
        assert!(record.observation.contains('x'));

        // Not the expected JSON shape at all -> conservatively "has errors".
        let record = build_record(serde_json::json!("exploded: not a json object")).await;
        assert!(
            record.observation.contains("treated as errors"),
            "{}",
            record.observation
        );
    }

    /// DR-6: the editor-scope limitation is published as an explicit,
    /// human-confirmation doctor item instead of being silently assumed.
    #[test]
    fn doctor_publishes_the_editor_scope_confirmation() {
        let temp = tempfile::tempdir().unwrap();
        let items = adapter(&temp.path().join("addon"))
            .doctor(temp.path())
            .unwrap();
        let scope = items
            .iter()
            .find(|item| item.name == "godot.editor_scope")
            .expect("godot.editor_scope must be reported");
        assert!(scope.ok, "the confirmation item never blocks a run");
        assert!(
            scope
                .detail
                .contains(crate::runtime::run_loop::MCP_SCOPE_WARNING),
            "detail: {}",
            scope.detail
        );
        assert!(
            scope.detail.to_lowercase().contains("confirm"),
            "detail: {}",
            scope.detail
        );
    }

    #[test]
    fn cache_excludes_always_contain_the_runtime_paths() {
        let temp = tempfile::tempdir().unwrap();
        let excludes = adapter(&temp.path().join("addon")).cache_excludes();
        assert!(excludes.contains(&".hoh".to_string()));
        assert!(excludes.contains(&".git".to_string()));
        assert!(excludes.contains(&".godot".to_string()));
    }

    #[test]
    fn playbook_covers_the_four_evidence_kinds() {
        let temp = tempfile::tempdir().unwrap();
        let playbook = adapter(&temp.path().join("addon")).evidence_playbook();
        for needle in [
            "simulate_sequence",
            "capture_frames",
            "monitor_properties",
            "assert_node_state",
            ".hoh/evidence/",
        ] {
            assert!(playbook.contains(needle), "playbook is missing {needle}");
        }
    }
}
