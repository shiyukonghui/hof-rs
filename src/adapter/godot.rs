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
use crate::tools::endpoint::{self, GameEndpointRecord};
use crate::tools::mcp::{RpcCorrelation, SessionSyncReport, PROBE_TOOL};
use crate::tools::reliable::{
    call_with_retries_traced, wait_for_ready_matching, McpErrorLog, McpFailure, ReadyOutcome,
    TracedCall, READY_POLL_INTERVAL_MS, RETRY_INTERVAL_MS,
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
config/features=PackedStringArray("4.8")

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
"#;

/// DR-41: the retired GDExtension channel's plugin entry.  It is no longer
/// installed; the constant survives because the **reverse cleanup** has to
/// recognise it in an `A0` inherited from an earlier version.
pub const MCP_PLUGIN_PATH: &str = "res://addons/godot_mcp_rs/plugin.cfg";
/// DR-41: the exact directory the retired addon lived in (only this path).
pub const BUNDLED_ADDON_DIR: &str = "addons/godot_mcp_rs";
/// DR-41: the stale cache entry that made Godot load the retired GDExtension
/// even when `[editor_plugins]` did not name it.
pub const BUNDLED_ADDON_EXTENSION: &str = "res://addons/godot_mcp_rs/godot_mcp_rs.gdextension";
/// DR-41: the engine's extension cache.
const EXTENSION_LIST_CACHE: &str = ".godot/extension_list.cfg";
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

// ---------------------------------------------------------------------------
// DR-24: scene-structure validation (the Developer's executable feedback)
// ---------------------------------------------------------------------------

/// The result of the `.tscn` structure check.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SceneStructureReport {
    pub ok: bool,
    /// One message per problem: offending line number, the current content and
    /// the correct form.  Empty when `ok`.
    pub problems: Vec<String>,
}

/// The root-node line quoted in every hint: the shape Godot accepts.
const ROOT_EXAMPLE: &str = "[node name=\"Main\" type=\"Node2D\"]";

/// Extract `key="value"` from a `[node ...]` body.
fn node_attribute(body: &str, key: &str) -> Option<String> {
    let needle = format!("{key}=\"");
    let start = body.find(&needle)? + needle.len();
    let end = body[start..].find('"')? + start;
    Some(body[start..end].to_string())
}

/// DR-24: validate the `[node ...]` declarations of a `.tscn` text.
///
/// Rules (the ones Godot enforces at load time, and the ones `smoke-t2` broke):
/// 1. exactly one root node — the first `[node ...]` line must have **no**
///    `parent=` attribute (otherwise Godot reports
///    `Invalid scene: root node X cannot specify a parent node`);
/// 2. every other `[node ...]` line must declare `parent=`;
/// 3. every path referenced by `parent=` must resolve to a declared node.
///
/// Every failure names the line number, quotes the current line and states the
/// correct form, so the message is directly actionable.
pub fn validate_scene_structure(text: &str) -> SceneStructureReport {
    validate_scene_structure_in(text, None)
}

/// Same as [`validate_scene_structure`], with an optional `res://` root for the
/// `[ext_resource ... path="res://..."]` existence check.
pub fn validate_scene_structure_in(
    text: &str,
    project_root: Option<&Path>,
) -> SceneStructureReport {
    let mut problems = Vec::new();

    // (line number, whole line, name, parent)
    let mut nodes: Vec<(usize, String, String, Option<String>)> = Vec::new();
    for (index, raw) in text.lines().enumerate() {
        let line_no = index + 1;
        let trimmed = raw.trim();
        let Some(rest) = trimmed.strip_prefix("[node ") else {
            continue;
        };
        let body = rest.trim_end_matches(']');
        let name = node_attribute(body, "name").unwrap_or_default();
        let parent = node_attribute(body, "parent");
        nodes.push((line_no, trimmed.to_string(), name, parent));
    }

    if nodes.is_empty() {
        problems.push(format!(
            "no `[node ...]` declaration was found: a scene must declare exactly one root node. \
             Correct form: {ROOT_EXAMPLE}"
        ));
        return SceneStructureReport {
            ok: false,
            problems,
        };
    }

    let (root_line, root_text, root_name, root_parent) = &nodes[0];
    if root_parent.is_some() {
        problems.push(format!(
            "line {root_line}: the FIRST `[node ...]` declaration is the scene root and must NOT \
             carry a `parent=` attribute — Godot rejects this with `Invalid scene: root node \
             {root_name} cannot specify a parent node`. Current line: {root_text}. Correct form: \
             {ROOT_EXAMPLE} (no parent)."
        ));
    }

    // Resolve the declared node paths.  `.` is the root; a child of the root
    // declares `parent="."`, a grandchild declares `parent="Parent/Child"`.
    let mut declared: std::collections::BTreeSet<String> = std::collections::BTreeSet::new();
    declared.insert(".".to_string());
    if root_parent.is_none() && !root_name.is_empty() {
        declared.insert(root_name.clone());
    }
    let mut pending: Vec<&(usize, String, String, Option<String>)> = nodes.iter().skip(1).collect();
    for entry in &pending {
        if entry.3.is_none() {
            problems.push(format!(
                "line {}: this is not the root node, so it must declare a `parent=`. Current line: \
                 {}. Correct form: [node name=\"{}\" type=\"...\" parent=\".\"] (use `parent=\".\"` \
                 for a direct child of the root).",
                entry.0, entry.1, entry.2
            ));
        }
    }
    loop {
        let mut progressed = false;
        let mut remaining = Vec::new();
        for entry in pending {
            let Some(parent) = &entry.3 else {
                progressed = true; // already reported, do not repeat
                continue;
            };
            if parent != "." && !declared.contains(parent.as_str()) {
                remaining.push(entry);
                continue;
            }
            if entry.2.is_empty() {
                problems.push(format!(
                    "line {}: the node has no `name=` attribute. Current line: {}. Correct form: \
                     {ROOT_EXAMPLE}.",
                    entry.0, entry.1
                ));
            } else if parent == "." {
                declared.insert(entry.2.clone());
            } else {
                declared.insert(format!("{parent}/{}", entry.2));
            }
            progressed = true;
        }
        let done = remaining.is_empty();
        pending = remaining;
        if done || !progressed {
            break;
        }
    }
    for entry in pending {
        let parent = entry.3.clone().unwrap_or_default();
        problems.push(format!(
            "line {}: `parent=\"{parent}\"` does not resolve to a declared node. Current line: {}. \
             Declare the parent node before this line, or use `parent=\".\"` for a direct child of \
             the root.",
            entry.0, entry.1
        ));
    }

    // `res://` references must exist when we know the project root.
    if let Some(root) = project_root {
        for (index, raw) in text.lines().enumerate() {
            let line_no = index + 1;
            let trimmed = raw.trim();
            let Some(rest) = trimmed.strip_prefix("[ext_resource ") else {
                continue;
            };
            let body = rest.trim_end_matches(']');
            let Some(path) = node_attribute(body, "path") else {
                continue;
            };
            if let Some(relative) = path.strip_prefix("res://") {
                if !root.join(relative).exists() {
                    problems.push(format!(
                        "line {line_no}: the referenced resource `{path}` does not exist on disk. \
                         Current line: {trimmed}. Correct form: create that file first, or remove \
                         the `[ext_resource ...]` line that points at it."
                    ));
                }
            }
        }
    }

    SceneStructureReport {
        ok: problems.is_empty(),
        problems,
    }
}

/// DR-37: is the Developer's artifact usable?
///
/// The criterion DR-37 pins down: the configured main scene must exist, pass the
/// same DR-24 structure check the battery runs, and reference at least one
/// existing, non-empty script.  Anything that cannot be established counts as
/// **not** valid (conservative) — that only ever *enables* the wrap-up retry,
/// never suppresses it.
pub fn developer_artifact_valid_in(workspace: &Path, main_scene: &str) -> bool {
    let Some(relative) = main_scene.strip_prefix("res://") else {
        return false;
    };
    let Ok(text) = std::fs::read_to_string(workspace.join(relative)) else {
        return false;
    };
    if text.trim().is_empty() || !validate_scene_structure_in(&text, Some(workspace)).ok {
        return false;
    }
    let referenced = script_resource_ids(&text);
    if referenced.is_empty() {
        return false;
    }
    let resources = ext_resource_paths(&text);
    referenced.iter().all(|id| {
        let Some(path) = resources
            .get(id)
            .and_then(|path| path.strip_prefix("res://"))
        else {
            return false;
        };
        std::fs::metadata(workspace.join(path))
            .map(|meta| meta.is_file() && meta.len() > 0)
            .unwrap_or(false)
    })
}

/// `id -> res:// path` of every `[ext_resource ...]` line.
fn ext_resource_paths(text: &str) -> std::collections::BTreeMap<String, String> {
    let mut resources = std::collections::BTreeMap::new();
    for raw in text.lines() {
        let trimmed = raw.trim();
        let Some(rest) = trimmed.strip_prefix("[ext_resource ") else {
            continue;
        };
        let body = rest.trim_end_matches(']');
        if let (Some(id), Some(path)) = (node_attribute(body, "id"), node_attribute(body, "path")) {
            resources.insert(id, path);
        }
    }
    resources
}

/// The resource ids a scene uses as a `script` (`script = ExtResource("1")`).
fn script_resource_ids(text: &str) -> Vec<String> {
    let mut ids = Vec::new();
    for raw in text.lines() {
        let trimmed = raw.trim();
        let Some(rest) = trimmed.strip_prefix("script") else {
            continue;
        };
        let Some(start) = rest.find("ExtResource(\"") else {
            continue;
        };
        let value = &rest[start + "ExtResource(\"".len()..];
        let Some(end) = value.find('"') else {
            continue;
        };
        ids.push(value[..end].to_string());
    }
    ids
}

/// The scene text out of a `project_read_scene_file_content` payload, whatever shape the
/// server chose (a bare string, `content`, `text`, `scene.content`, ...).
fn scene_text_of(payload: &Value) -> Option<String> {
    match payload {
        Value::String(text) if !text.is_empty() => Some(text.clone()),
        Value::Object(object) => {
            for key in ["content", "text", "source", "file_content", "scene", "data"] {
                if let Some(found) = object.get(key).and_then(scene_text_of) {
                    return Some(found);
                }
            }
            None
        }
        _ => None,
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

fn call_ok(tool: &str, args: &Value, payload: &Value, correlation: &RpcCorrelation) -> Value {
    let mut entry = json!({"tool": tool, "args": args, "ok": true, "payload": payload});
    apply_correlation(&mut entry, correlation);
    entry
}

fn call_fail(tool: &str, args: &Value, failure: &McpFailure) -> Value {
    let mut entry = json!({
        "tool": tool,
        "args": args,
        "ok": false,
        "error": {"code": failure.code, "message": failure.message, "attempts": failure.attempts},
    });
    apply_correlation(&mut entry, &failure.correlation);
    entry
}

/// DR-29: every call entry carries the ids it was matched against.
fn apply_correlation(entry: &mut Value, correlation: &RpcCorrelation) {
    entry["request_id"] = json!(correlation.request_id);
    entry["response_id"] = json!(correlation.response_id);
    entry["sync_probes"] = json!(correlation.sync_probes);
    if !correlation.mismatched_ids.is_empty() {
        entry["mismatched_ids"] = json!(correlation.mismatched_ids);
    }
}

/// DR-29: the step-level header written at the top of every raw payload file —
/// `request_id` / `response_id` / `sync_probes` — so no response can ever be
/// attributed to the wrong call again.
fn rpc_header(calls: &[Value]) -> Value {
    let first = calls.iter().find(|call| {
        call.get("request_id")
            .map(|id| !id.is_null())
            .unwrap_or(false)
    });
    let probes: u64 = calls
        .iter()
        .filter_map(|call| call.get("sync_probes").and_then(Value::as_u64))
        .sum();
    let mismatched: Vec<Value> = calls
        .iter()
        .filter_map(|call| call.get("mismatched_ids"))
        .flat_map(|ids| ids.as_array().cloned().unwrap_or_default())
        .collect();
    json!({
        "request_id": first.and_then(|call| call.get("request_id")).cloned().unwrap_or(Value::Null),
        "response_id": first.and_then(|call| call.get("response_id")).cloned().unwrap_or(Value::Null),
        "sync_probes": probes,
        "mismatched_ids": mismatched,
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
    /// DR-24: the main scene the battery reloads/opens/validates.
    main_scene: String,
    log: McpErrorLog,
    records: Vec<BatteryRecord>,
    /// DR-35: the channel probe's verdict, filled in before `input_replay`.
    channel: InputChannelProbe,
    /// DR-81 ②: the editor-log tail as it stood **before** the project reload —
    /// the window anchor the judged reading is compared against.  `None` means the
    /// anchor could not be taken (the call failed, or the payload was not an
    /// editor report); the window is then fail-closed.
    editor_error_anchor: Option<Vec<String>>,
    /// DR-81 ②: the anchor request and its verbatim answer, recorded next to the
    /// judged reading so the window criterion is auditable.
    editor_error_anchor_raw: Value,
}

impl<'a> BatterySession<'a> {
    fn new(
        workspace: &'a Path,
        tools: &'a dyn ToolChannel,
        limits: &'a BatteryLimits,
        main_scene: String,
    ) -> Self {
        Self {
            workspace,
            tools,
            limits,
            main_scene,
            log: McpErrorLog::new(workspace),
            records: Vec::new(),
            channel: InputChannelProbe::default(),
            editor_error_anchor: None,
            editor_error_anchor_raw: Value::Null,
        }
    }

    async fn call(&self, tool: &str, args: Value) -> Result<TracedCall, McpFailure> {
        // DR-24: the battery is the runtime's deterministic stage, not the
        // Tester.  It must be able to `editor_rescan_project_filesystem`/`editor_open_scene` (which the
        // Tester is forbidden to call) so the editor reflects the on-disk
        // scene before the errors are read.
        call_with_retries_traced(
            self.tools,
            Role::Developer,
            tool,
            args,
            self.limits.max_retries,
            RETRY_INTERVAL_MS,
            Some(&self.log),
        )
        .await
    }

    async fn ready(&self, tool: &str, args: Value) -> ReadyOutcome {
        // DR-72 ⑤ (D1): the battery's readiness predicate is the **scene-tree
        // shape** check, and it is now the same one the round's start uses.
        wait_for_ready_matching(
            self.tools,
            Role::Developer,
            tool,
            args,
            self.limits.ready_timeout_seconds,
            READY_POLL_INTERVAL_MS,
            Some(&self.log),
            scene_tree_readiness,
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
        self.finish_with(step, kind, path, observation, ok, calls, Value::Null)
            .await
    }

    /// Same, with one extra top-level object in the raw document.
    ///
    /// DR-35 uses it for the channel verdict, so `raw/input_channel_probe.json`
    /// states the capability next to the verbatim payloads that produced it.
    #[allow(clippy::too_many_arguments)]
    async fn finish_with(
        &mut self,
        step: BatteryStep,
        kind: ExecKind,
        path: Option<String>,
        observation: String,
        ok: bool,
        calls: Vec<Value>,
        extra: Value,
    ) -> anyhow::Result<()> {
        let rel = format!(".hoh/deterministic/raw/{}.json", step.id);
        // DR-29: the correlation header comes first, so a reader can tell which
        // response belonged to which request before reading any payload.
        let header = rpc_header(&calls);
        let mut doc = json!({
            "step": step.id,
            "request_id": header["request_id"],
            "response_id": header["response_id"],
            "sync_probes": header["sync_probes"],
            "mismatched_ids": header["mismatched_ids"],
            "supports": step.supports,
            "ok": ok,
            "calls": calls,
        });
        if !extra.is_null() {
            if let Some(object) = doc.as_object_mut() {
                object.insert("channel".to_string(), extra);
            }
        }
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

    /// DR-29: the session-start synchronization probe.  Its report is written to
    /// `.hoh/deterministic/mcp-sync.json`, which the run loop turns into a
    /// `mcp_desync_detected` warning on the iteration result.
    async fn session_sync_probe(&self) {
        let report = self.tools.session_sync_probe().await;
        let target = self.workspace.join(SESSION_SYNC_FILE);
        if let Some(parent) = target.parent() {
            let _ = std::fs::create_dir_all(parent);
        }
        if let Ok(mut serialized) = serde_json::to_string_pretty(&report) {
            if !serialized.ends_with('\n') {
                serialized.push('\n');
            }
            let _ = std::fs::write(&target, serialized);
        }
    }

    async fn run(mut self) -> anyhow::Result<Vec<BatteryRecord>> {
        // DR-29: correlate before collecting anything: a desynchronized server
        // mislabels every payload below.
        self.session_sync_probe().await;
        // DR-81 ②: the window anchor is read **before** the project is reloaded.
        // The reload is what makes the editor surface the current on-disk
        // project, so the anchor is the log tail as it stood before this round's
        // candidate could contribute to it; the judged reading then splits into
        // "already there" and "new in this window".
        self.anchor_editor_error_window().await;
        // DR-24: the editor is forced onto the on-disk truth *before* anything
        // is asked about errors (smoke-t2 showed an in-memory scene that
        // disagreed with the `.tscn` on disk).
        self.step_project_reload_and_open().await?;
        self.step_scene_structure().await?;
        self.step_editor_errors().await?;
        let scene_tree = self.step_play_scene().await?;
        self.step_scene_tree(scene_tree.clone()).await?;
        self.step_screenshot().await?;
        // DR-78 ③: the **observing** window runs before the windows that can
        // consume what it observes.  `smoke-t11` measured the defect this
        // fixes: `input_replay` sat at index 7 and `interaction_evidence` at
        // index 8, the replay's `move_right` window swept `Coin1` (`x=400`
        // between `192.000045776367` and `408.333038330078`), and the
        // interaction window's first reading was therefore `Coins: 1` — with
        // `main.gd` starting at `0` and `coin.gd::collect()` the only increment,
        // F10's `0 -> 1` claim was unreachable by construction, not unobserved.
        //
        // The order is pinned by
        // `the_coin_observing_window_runs_before_every_consuming_window` in
        // `tests/evidence_battery.rs`, which runs the battery and reads the
        // order of the records it produced.
        self.step_interaction_evidence(scene_tree.clone()).await?;
        self.channel = self.step_input_channel_probe().await?;
        self.step_input_replay().await?;
        self.step_node_assertions(scene_tree).await?;
        self.step_stop_scene().await?;
        Ok(self.records)
    }

    /// DR-24 (new 1). `editor_rescan_project_filesystem` + `editor_open_scene(<main>)`.
    ///
    /// Without this the editor keeps whatever scene it had in memory, so a
    /// scene that is legal on disk can still report stale errors — and the
    /// reverse, which is exactly how `editor_play_scene` managed to lie in `smoke-t2`.
    async fn step_project_reload_and_open(&mut self) -> anyhow::Result<()> {
        let step = BatteryStep {
            id: crate::adapter::PROJECT_RELOAD_STEP_ID.to_string(),
            supports: vec!["N1".to_string()],
            timeout_secs: self.limits.timeout_seconds,
            retries: self.limits.max_retries,
        };
        let main_scene = self.main_scene.clone();
        let mut calls = Vec::new();
        let mut notes: Vec<String> = Vec::new();

        let reload_args = json!({});
        match self
            .call("editor_rescan_project_filesystem", reload_args.clone())
            .await
        {
            Ok(call) => calls.push(call_ok(
                "editor_rescan_project_filesystem",
                &reload_args,
                &call.payload,
                &call.correlation,
            )),
            Err(failure) => {
                notes.push(format!(
                    "FAILED editor_rescan_project_filesystem: {}",
                    failure.observation()
                ));
                calls.push(call_fail(
                    "editor_rescan_project_filesystem",
                    &reload_args,
                    &failure,
                ));
            }
        }

        let open_args = json!({"path": main_scene});
        match self.call("editor_open_scene", open_args.clone()).await {
            Ok(call) => calls.push(call_ok(
                "editor_open_scene",
                &open_args,
                &call.payload,
                &call.correlation,
            )),
            Err(failure) => {
                notes.push(format!(
                    "FAILED editor_open_scene({main_scene}): {}",
                    failure.observation()
                ));
                calls.push(call_fail("editor_open_scene", &open_args, &failure));
            }
        }

        let ok = notes.is_empty();
        let observation = if ok {
            format!(
                "reloaded the project and opened {main_scene}; the editor now reflects the \
                 on-disk scene"
            )
        } else {
            format!(
                "{} (UNAVAILABLE: the editor may still hold a stale in-memory scene)",
                notes.join(" | ")
            )
        };
        self.finish(step, ExecKind::Build, None, observation, ok, calls)
            .await
    }

    /// DR-24 (new 2). Validate the `.tscn` text of the main scene.
    ///
    /// The observation is the *executable* hint: line number, current content,
    /// correct form.
    async fn step_scene_structure(&mut self) -> anyhow::Result<()> {
        let step = BatteryStep {
            id: crate::adapter::SCENE_STRUCTURE_STEP_ID.to_string(),
            // F5 (main scene/nodes), F6 (player physics body), N1 (launchable).
            supports: vec!["N1".to_string(), "F5".to_string(), "F6".to_string()],
            timeout_secs: self.limits.timeout_seconds,
            retries: self.limits.max_retries,
        };
        let scene = self.main_scene.clone();
        let args = json!({"path": scene});
        let (ok, observation, call) = match self
            .call("project_read_scene_file_content", args.clone())
            .await
        {
            Ok(call) => {
                let parsed = unwrap_mcp_payload(&call.payload);
                match scene_text_of(&parsed) {
                    Some(text) => {
                        let report = validate_scene_structure_in(&text, Some(self.workspace));
                        let ok = report.ok;
                        let observation = if ok {
                            format!(
                                "scene structure ok: {scene} declares exactly one root node and \
                                 every child's `parent=` resolves"
                            )
                        } else {
                            format!(
                                "FAILED scene structure for {scene}: {} (UNAVAILABLE: Godot cannot \
                                 load this scene)",
                                report.problems.join(" | ")
                            )
                        };
                        (
                            ok,
                            observation,
                            call_ok(
                                "project_read_scene_file_content",
                                &args,
                                &call.payload,
                                &call.correlation,
                            ),
                        )
                    }
                    None => (
                        false,
                        format!(
                            "FAILED project_read_scene_file_content returned no scene text for {scene}: \
                             {parsed} (UNAVAILABLE: the scene cannot be checked)"
                        ),
                        call_ok(
                            "project_read_scene_file_content",
                            &args,
                            &call.payload,
                            &call.correlation,
                        ),
                    ),
                }
            }
            Err(failure) => (
                false,
                failure.observation(),
                call_fail("project_read_scene_file_content", &args, &failure),
            ),
        };
        self.finish(step, ExecKind::Assert, None, observation, ok, vec![call])
            .await
    }

    /// 3. Editor error baseline — taken *before* the project is started.
    ///
    /// DR-81 ①/②: the reading is judged, not taken literally.  DR-48's exact
    /// banners are information, DR-68 removes lines the on-disk project can no
    /// longer produce, DR-81 ① removes the editor's own infrastructure failures
    /// (the `smoke-t14` cache-write line) and DR-81 ② keeps only the lines whose
    /// occurrence count grew since the window anchor.  The remaining lines are the
    /// project defect, and they still close the gate — the `smoke-t14` pass-1
    /// `res://scripts/main.gd:8 - Parse Error` is the regression pin.
    async fn step_editor_errors(&mut self) -> anyhow::Result<()> {
        let step = BatteryStep {
            id: "editor_errors_baseline".to_string(),
            supports: vec!["N1".to_string(), "N3".to_string()],
            timeout_secs: self.limits.timeout_seconds,
            retries: self.limits.max_retries,
        };
        let args = json!({"max_lines": 50});
        let mut verdict = None;
        let (ok, observation, call) = match self.call("editor_get_errors", args.clone()).await {
            Ok(call) => {
                let parsed = unwrap_mcp_payload(&call.payload);
                // DR-30: an `errors` array is what makes this payload an editor
                // report at all.  `smoke-t3` received the *scene text* here and
                // the observation blamed the wrong thing.
                let judged = match parsed.get("errors").and_then(Value::as_array) {
                    Some(errors) if errors.is_empty() => EditorErrorVerdict {
                        ok: true,
                        observation: format!(
                            "{} (editor has no errors; editor_infrastructure_failures=0, \
                             project_defects_new=0)",
                            describe_editor_errors(&parsed)
                        ),
                        banners: 0,
                        stale: 0,
                        infrastructure: 0,
                        new_defects: 0,
                        pre_existing: 0,
                    },
                    Some(errors) => judge_editor_errors(
                        &parsed,
                        errors,
                        self.workspace,
                        self.editor_error_anchor.as_deref(),
                    ),
                    None => EditorErrorVerdict {
                        ok: false,
                        observation: format!(
                            "FAILED editor_get_errors returned no `errors` array: {parsed} \
                             (UNAVAILABLE: the payload does not answer the question)"
                        ),
                        banners: 0,
                        stale: 0,
                        infrastructure: 0,
                        new_defects: 0,
                        pre_existing: 0,
                    },
                };
                let (ok, observation) = (judged.ok, judged.observation.clone());
                verdict = Some(judged);
                (
                    ok,
                    observation,
                    call_ok("editor_get_errors", &args, &call.payload, &call.correlation),
                )
            }
            Err(failure) => (
                false,
                failure.observation(),
                call_fail("editor_get_errors", &args, &failure),
            ),
        };
        // DR-81 ②: the window and its counts are part of the evidence, not a
        // narration: a reader can see when the anchor was taken, what it held and
        // how the judged reading was split.
        let window = match &verdict {
            Some(verdict) => json!({
                "criterion": EDITOR_ERROR_WINDOW_CRITERION,
                "anchor": format!(
                    "editor_get_errors max_lines={EDITOR_ERROR_ANCHOR_MAX_LINES} taken \
                     immediately before `project_reload_and_open`; the judged reading is \
                     max_lines=50 taken after it"
                ),
                "anchor_line_count": self.editor_error_anchor.as_ref().map(Vec::len),
                "anchor_request_and_answer": self.editor_error_anchor_raw.clone(),
                "banners": verdict.banners,
                "stale": verdict.stale,
                "editor_infrastructure_failures": verdict.infrastructure,
                "pre_existing_lines": verdict.pre_existing,
                "project_defects_new": verdict.new_defects,
            }),
            None => json!({
                "criterion": EDITOR_ERROR_WINDOW_CRITERION,
                "anchor": format!(
                    "editor_get_errors max_lines={EDITOR_ERROR_ANCHOR_MAX_LINES} taken \
                     immediately before `project_reload_and_open`"
                ),
                "anchor_line_count": self.editor_error_anchor.as_ref().map(Vec::len),
                "anchor_request_and_answer": self.editor_error_anchor_raw.clone(),
                "note": "the judged reading never arrived, so no window split was computed",
            }),
        };
        self.finish_with(
            step,
            ExecKind::Build,
            None,
            observation,
            ok,
            vec![call],
            json!({"editor_error_window": window}),
        )
        .await
    }

    /// DR-81 ②: read the editor-log tail **before** the project reload and keep it
    /// as the window anchor.
    ///
    /// The call asks for the whole tail ([`EDITOR_ERROR_ANCHOR_MAX_LINES`]) so the
    /// anchor is a superset of anything the judged reading can contain.  A failed
    /// call, or a payload that is not an editor report, leaves the anchor `None`;
    /// [`partition_editor_errors_in_window`] then treats every judged line as new,
    /// which is the conservative direction.
    async fn anchor_editor_error_window(&mut self) {
        let args = json!({"max_lines": EDITOR_ERROR_ANCHOR_MAX_LINES});
        match self.call("editor_get_errors", args.clone()).await {
            Ok(call) => {
                let parsed = unwrap_mcp_payload(&call.payload);
                self.editor_error_anchor =
                    parsed
                        .get("errors")
                        .and_then(Value::as_array)
                        .map(|errors| {
                            errors
                                .iter()
                                .filter_map(|line| line.as_str().map(ToString::to_string))
                                .collect::<Vec<String>>()
                        });
                self.editor_error_anchor_raw =
                    call_ok("editor_get_errors", &args, &call.payload, &call.correlation);
            }
            Err(failure) => {
                self.editor_error_anchor = None;
                self.editor_error_anchor_raw = call_fail("editor_get_errors", &args, &failure);
            }
        }
    }

    /// 2. `editor_play_scene` plus the readiness wait (DR-20).
    async fn step_play_scene(&mut self) -> anyhow::Result<Option<Value>> {
        let step = BatteryStep {
            id: "play_scene_ready".to_string(),
            supports: vec!["N1".to_string()],
            timeout_secs: self.limits.ready_timeout_seconds,
            retries: self.limits.max_retries,
        };
        let play_args = json!({"mode": "main"});
        let mut calls = Vec::new();
        let play = self.call("editor_play_scene", play_args.clone()).await;
        match play {
            Ok(call) => {
                // DR-30: `editor_play_scene`'s own reply is **not** readiness
                // evidence.  It is recorded, and then a scene tree is demanded.
                calls.push(call_ok(
                    "editor_play_scene",
                    &play_args,
                    &call.payload,
                    &call.correlation,
                ));
                // DR-43: the same reply is the **only** source of the game
                // endpoint.  Registering it must succeed; a failure fails the
                // step instead of falling back to the editor endpoint.
                //
                // DR-71 ①: the announced endpoint is installed for in-process
                // routing only.  The route becomes visible to another process
                // **after** the readiness poll below, so a battery play that never
                // becomes observable cannot publish a route a later role would
                // adopt (the same lie DR-70's acceptance measured, one step over).
                let endpoint = parse_game_endpoint(&call.payload);
                let registered = match &endpoint {
                    Ok(record) => self.tools.install_game_endpoint(record.clone()).await,
                    Err(problem) => Err(anyhow::anyhow!(problem.clone())),
                };
                if let Err(error) = registered {
                    let endpoint = endpoint.ok();
                    calls.push(json!({
                        "tool": "editor_play_scene",
                        "ok": false,
                        "game_endpoint": endpoint,
                        "error": {"code": Value::Null, "message": error.to_string()},
                    }));
                    let observation = format!(
                        "FAILED editor_play_scene did not register a game endpoint: {error} \
                         (UNAVAILABLE: running_game_* tools have no endpoint, so this step fails \
                         -- silently falling back to the editor endpoint is forbidden, DR-43)"
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
                    return Ok(None);
                }
            }
            Err(failure) => {
                calls.push(call_fail("editor_play_scene", &play_args, &failure));
                let observation = format!(
                    "FAILED editor_play_scene: {} (UNAVAILABLE)",
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
                return Ok(None);
            }
        }

        let tree_args = json!({"max_depth": -1});
        let ready = self
            .ready("running_game_get_scene_tree", tree_args.clone())
            .await;
        match ready {
            ReadyOutcome {
                ok: true,
                attempts,
                payload,
                correlation,
                ..
            } => {
                let payload = payload.expect("a successful readiness poll carries a payload");
                calls.push(call_ok(
                    "running_game_get_scene_tree",
                    &tree_args,
                    &payload,
                    &correlation,
                ));
                let tree = unwrap_mcp_payload(&payload);
                match describe_scene_tree_shape(&tree) {
                    Ok(nodes) => {
                        // DR-71 ①: readiness is confirmed, so this is the first
                        // moment the route may become visible to a role process.
                        if let Err(error) = self.tools.publish_game_endpoint().await {
                            self.tools.clear_game_endpoint().await;
                            calls.push(json!({
                                "tool": "publish_game_route",
                                "ok": false,
                                "error": {"code": Value::Null, "message": error.to_string()},
                            }));
                            let observation = format!(
                                "FAILED the main scene booted but its route could not be \
                                 published: {error} (UNAVAILABLE: every `running_game_*` call \
                                 would have to be refused, so the step must not report success)"
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
                            return Ok(None);
                        }
                        let observation = format!(
                            "main scene booted; the game answered running_game_get_scene_tree after \
                             {attempts} poll(s) with {nodes} node(s) carrying a path and a type"
                        );
                        self.finish(step, ExecKind::RuntimeTrace, None, observation, true, calls)
                            .await?;
                        Ok(Some(tree))
                    }
                    Err(problem) => {
                        // DR-71 ①: an unconfirmed play leaves no route behind.
                        self.tools.clear_game_endpoint().await;
                        let observation = format!(
                            "FAILED the readiness reply is not a scene tree ({problem}): {tree} \
                             (UNAVAILABLE: `editor_play_scene`'s own reply is never readiness evidence)"
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
            ReadyOutcome {
                ok: false,
                attempts,
                failure,
                ..
            } => {
                // DR-71 ①: a play that never became observable must not leave a
                // route for a later role to adopt.
                self.tools.clear_game_endpoint().await;
                let failure = failure.unwrap_or_else(|| {
                    McpFailure::new("running_game_get_scene_tree", None, "timeout", 0)
                });
                calls.push(call_fail(
                    "running_game_get_scene_tree",
                    &tree_args,
                    &failure,
                ));
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
        let tree: Option<Value> = match self.call("running_game_get_scene_tree", args.clone()).await
        {
            Ok(call) => {
                calls.push(call_ok(
                    "running_game_get_scene_tree",
                    &args,
                    &call.payload,
                    &call.correlation,
                ));
                Some(unwrap_mcp_payload(&call.payload))
            }
            Err(failure) => {
                calls.push(call_fail("running_game_get_scene_tree", &args, &failure));
                // The readiness poll already captured a tree for this run; it
                // is a legitimate fallback, but the failed fresh call is never
                // hidden.
                match cached {
                    Some(cached) => {
                        calls.push(json!({
                            "tool": "running_game_get_scene_tree",
                            "source": "play_scene_ready",
                            "payload": cached,
                        }));
                        Some(cached)
                    }
                    None => None,
                }
            }
        };
        // DR-30: node *paths and types* are the evidence; a list of names (or a
        // payload that is not a tree at all) is not.
        let shape = tree
            .as_ref()
            .map(describe_scene_tree_shape)
            .unwrap_or_else(|| Err("no scene tree was captured".to_string()));
        let (ok, observation) = match &shape {
            Ok(nodes) => (
                true,
                format!("scene tree: {nodes} node(s) with a path and a type"),
            ),
            Err(problem) => (
                false,
                format!(
                    "FAILED the scene tree is unusable ({problem}): {} (UNAVAILABLE: no node \
                     evidence)",
                    tree.as_ref()
                        .map(Value::to_string)
                        .unwrap_or_else(|| "<none>".to_string())
                ),
            ),
        };
        self.finish(step, ExecKind::RuntimeTrace, None, observation, ok, calls)
            .await?;
        Ok(())
    }

    /// 4. Screenshot, stored under `.hoh/evidence/` and referenced relatively.
    ///
    /// DR-30: a `path` may only be written when the PNG **really exists**.
    ///
    /// DR-49: it must also be **this run's** PNG.
    ///
    /// * the call carries **no** `save_path` — the engine accepts only
    ///   `res://`/`user://` (`running_game_capture.cpp:62-63`) and hof-rs used to
    ///   send a filesystem path, which was refused with `-32602` three times in
    ///   `smoke-t6`; without it the engine answers the image inline
    ///   (`running_game_capture.cpp:56-60`) and the runtime materializes it;
    /// * whatever is already at the target path is invalidated **before** the
    ///   call (`*.stale-<ts>`), so `smoke-t6`'s 2026-09-21 PNG cannot be
    ///   mistaken for this run's evidence;
    /// * the step's `ok` is decided on **freshness** (the artifact state changed
    ///   across the call), never on `is_file()`;
    /// * the `running_game_capture_frames` fallback is chosen by "we have no
    ///   image from this run", so a stale file can no longer suppress it.
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
        let mut calls = Vec::new();
        let mut notes: Vec<String> = Vec::new();
        let mut materialized = false;

        // DR-49 ②: the state before the call, and the invalidation that makes
        // "the path is occupied" impossible to inherit from an earlier round.
        let before = artifact_fingerprint(&absolute);
        match invalidate_artifact(&absolute) {
            Ok(Some(stale)) => notes.push(format!(
                "invalidated a pre-existing {stale} before the call"
            )),
            Ok(None) => {}
            Err(error) => notes.push(format!(
                "FAILED to invalidate the pre-existing artifact at {}: {error}",
                absolute.display()
            )),
        }

        // DR-49 ①: no `save_path` — the contract's writable forms are the only
        // accepted ones, and the inline form needs none.
        let args = json!({});
        match self
            .call("running_game_capture_screenshot", args.clone())
            .await
        {
            Ok(call) => {
                calls.push(call_ok(
                    "running_game_capture_screenshot",
                    &args,
                    &call.payload,
                    &call.correlation,
                ));
                let parsed = unwrap_mcp_payload(&call.payload);
                match extract_inline_image(&parsed) {
                    Some(bytes) => {
                        write_png(&absolute, &bytes)?;
                        materialized = true;
                    }
                    None => notes.push(format!(
                        "FAILED running_game_capture_screenshot reported success but carried no \
                         inline image: {parsed}"
                    )),
                }
            }
            Err(failure) => {
                calls.push(call_fail(
                    "running_game_capture_screenshot",
                    &args,
                    &failure,
                ));
                notes.push(failure.observation());
            }
        }

        // DR-49 ④: the fallback is about "this run has no image yet" — it is
        // never short-circuited by a file that happened to be on disk.
        if !materialized {
            let frames_args = json!({"count": 1, "frame_interval": 10});
            match self
                .call("running_game_capture_frames", frames_args.clone())
                .await
            {
                Ok(call) => {
                    calls.push(call_ok(
                        "running_game_capture_frames",
                        &frames_args,
                        &call.payload,
                        &call.correlation,
                    ));
                    let parsed = unwrap_mcp_payload(&call.payload);
                    match extract_inline_image(&parsed) {
                        Some(bytes) => {
                            write_png(&absolute, &bytes)?;
                            materialized = true;
                        }
                        None => notes.push(format!(
                            "FAILED running_game_capture_frames returned no inline image: {parsed}"
                        )),
                    }
                }
                Err(failure) => {
                    calls.push(call_fail(
                        "running_game_capture_frames",
                        &frames_args,
                        &failure,
                    ));
                    notes.push(failure.observation());
                }
            }
        }

        // DR-49 ③: one decision point, and it is about **freshness**, not about
        // the mere existence of a file.
        let after = artifact_fingerprint(&absolute);
        let (ok, path, observation) = if artifact_is_fresh(before.as_ref(), after.as_ref()) {
            let size = std::fs::metadata(&absolute).map(|m| m.len()).unwrap_or(0);
            let provenance = if materialized {
                "; materialized from an inline base64 image"
            } else {
                ""
            };
            let extra = if notes.is_empty() {
                String::new()
            } else {
                format!("; {}", notes.join(" / "))
            };
            (
                true,
                Some(relative.clone()),
                format!("screenshot written to {relative} ({size} byte(s)){provenance}{extra}"),
            )
        } else {
            (
                false,
                None,
                format!(
                    "FAILED screenshot unavailable: {} (UNAVAILABLE: no PNG produced by this run \
                     exists at {relative}; DR-49 decides on freshness, not on `is_file()`)",
                    notes.join(" / ")
                ),
            )
        };
        self.finish(step, ExecKind::Screenshot, path, observation, ok, calls)
            .await?;
        Ok(())
    }

    /// DR-35 — 4b. Channel capability probe, run in the **game process**.
    ///
    /// `smoke-t5` reported `ACTION_NOT_BOUND` for `move_right` even though
    /// `A_1`'s `project.godot` declared it, because the availability probe
    /// (`editor_get_input_actions`) and the injection tool (`editor_simulate_input_action`) both live
    /// in the **editor** process while the game is a separate process behind a
    /// `user://` file IPC.  The recorded verdict poisoned the round: the next
    /// Planner would have gone off to "fix" a non-existent defect.
    ///
    /// DR-54: this step asks the game process through the contract's **semantic**
    /// tools, and distinguishes three states:
    ///
    /// * `GAME_INPUT_CHANNEL_OK` — the action exists in the game and the semantic
    ///   input injection was accepted, with a semantic reading arriving;
    /// * `ACTION_NOT_BOUND` — a semantic tool **answered** that the game's
    ///   `InputMap` has no such action (the only honest way to reach this
    ///   verdict);
    /// * `ACTION_BINDING_UNKNOWN` — the probe failed or its shape is not
    ///   readable.  Never downgraded to `ACTION_NOT_BOUND`.
    ///
    /// Note on "press, wait N frames, re-read": a GDScript probe body cannot
    /// `await`.  DR-54 removes that constraint from the critical path — the
    /// injection and the "how is the axis now" reading are the contract's own
    /// semantic tools (`running_game_create_input_recording` +
    /// `running_game_play_input_recording` + `running_game_run_test_scenario`),
    /// and the frames elapse inside the game process through the game-forwarded
    /// `running_game_get_node_property_samples`.
    async fn step_input_channel_probe(&mut self) -> anyhow::Result<InputChannelProbe> {
        let step = BatteryStep {
            id: INPUT_PROBE_STEP_ID.to_string(),
            supports: vec!["F1".to_string(), "F2".to_string()],
            timeout_secs: self.limits.timeout_seconds,
            retries: self.limits.max_retries,
        };
        let mut calls = Vec::new();
        let mut notes: Vec<String> = Vec::new();

        // DR-54: the channel probe is built on the contract's **semantic**
        // tools.  The old form asked the game to run caller-assembled GDScript
        // (`InputMap.has_action` / `Input.is_action_pressed` / `Input.get_axis`)
        // and made the whole classification depend on whether those strings
        // compiled — `smoke-t6`'s structural fragility, and the path that took
        // the game endpoint down (DR-50B).

        // (a) `running_game_get_node_properties` names the node and proves the
        //     game process answers at all.  It is a plain semantic read.
        let properties_args = json!({"node_path": "Player"});
        let mut game_process_reachable = false;
        match self
            .record_semantic_call(
                semantic::NODE_PROPERTIES,
                properties_args,
                "player_properties",
                &mut calls,
            )
            .await
        {
            Ok(call) => {
                let parsed = unwrap_mcp_payload(&call.payload);
                // DR-58: the real reply proves the read by its `node_path` +
                // `properties`; there is no top-level `name` (reading one made
                // this a constant `false`).  See `node_properties_read`.
                game_process_reachable = node_properties_read(&parsed);
            }
            Err(failure) => notes.push(format!(
                "{} failed: {}",
                semantic::NODE_PROPERTIES,
                failure.observation()
            )),
        }

        // (b) `running_game_get_node_property_samples` on the well-known InputMap
        //     axis is the semantic "how is the input axis right now" reading.
        let axis_before = self
            .semantic_axis_sample("move_right:axis_before", &mut calls)
            .await;
        if axis_before.is_some() {
            game_process_reachable = true;
        }

        // (c) Inject the action and read the axis back through the semantic
        //     input API (recording + scenario), then sample `Player.position`.
        let (pressed, refusal, refusal_code) = self
            .semantic_inject_action_detailed(PROBE_ACTION, "move_right", &mut calls)
            .await;
        // The scenario's own report of the axis it observed is the semantic
        // "after" reading; a reply that carries none leaves it `None` rather
        // than inventing one.
        let axis_after = calls
            .iter()
            .rev()
            .find(|call| {
                call["tool"] == json!(semantic::TEST_SCENARIO)
                    && call["label"].as_str() == Some("move_right:test_scenario")
            })
            .and_then(|call| call["observed_axis"].as_f64());
        let (_, refusal_from_frames) = self
            .semantic_sample_positions(
                PROBE_ACTION,
                "Player",
                PROBE_FRAME_COUNT,
                "move_right:frames",
                &mut calls,
            )
            .await
            .unwrap_or((Value::Null, String::new()));
        let mut moved_while_pressed = false;
        if let (Some(before), Some(after)) = (axis_before, axis_after) {
            moved_while_pressed = (before - after).abs() > f64::EPSILON;
        }
        if let Some(refusal) = &refusal {
            notes.push(refusal.clone());
        }
        if !refusal_from_frames.is_empty() {
            notes.push(refusal_from_frames);
        }

        // (d) DR-54: one **read-only** `running_game_execute_gdscript` probe is
        //     kept as a supplementary cross-check.  It is a self-contained
        //     function body with an explicit `return` (DR-50A), and it is
        //     deliberately **not** consulted by the classification below: its
        //     value may corroborate, never carry, a critical assertion.
        let (probe_position, probe_refusal) = self
            .game_script(
                &probe_scripts::player_position(),
                "read_only_player_position",
                &mut calls,
            )
            .await;
        if probe_position.is_none() {
            if let Some(refusal) = probe_refusal {
                notes.push(format!("read-only probe: {refusal}"));
            }
        }

        // (e) Which of the three project actions the project *declares* is a
        //     diagnostic on disk, never evidence of a running binding.
        let declared =
            project_declared_actions(self.workspace, &["move_left", "move_right", "jump"]);
        let declared_note = if declared.is_empty() {
            "project.godot declares none of move_left/move_right/jump".to_string()
        } else {
            format!("project.godot declares {declared:?} (diagnostic only)")
        };

        // (f) Classify from the **semantic** evidence.
        //
        //     `GameInputChannelOk` needs the semantic injection to have been
        //     accepted *and* a semantic reading to have arrived.  A **business
        //     error that itself says the action is not bound** is the engine
        //     answering "I know no such action in this InputMap", which is the
        //     only honest way to reach `ACTION_NOT_BOUND`; anything without an
        //     answer (a transport failure, an unreadable reply) stays
        //     `ACTION_BINDING_UNKNOWN` and is never downgraded (DR-35).
        //
        //     The *code alone is not enough*: `-32602` is also what a malformed
        //     request gets, and reading that as "the action is not bound" would
        //     be exactly the class of false verdict DR-35 exists to prevent.
        let not_bound = refusal_code.map(is_action_not_bound_code).unwrap_or(false)
            && refusal
                .as_deref()
                .map(|text| text.contains(ACTION_NOT_BOUND_MARKER))
                .unwrap_or(false);
        let capability = match (pressed, axis_after.is_some() || game_process_reachable) {
            (true, true) => InputChannelCapability::GameInputChannelOk,
            _ if not_bound => InputChannelCapability::ActionNotBound,
            _ => InputChannelCapability::ActionBindingUnknown,
        };
        let evidence_note = format!(
            "game process via semantic tools: reachable={game_process_reachable}, \
             axis_before={axis_before:?}, injection accepted={pressed}, axis_after={axis_after:?}, \
             axis moved={moved_while_pressed}; read-only execute_gdscript probe={probe_position:?} \
             (supplementary only, DR-54)"
        );
        let detail = match capability {
            InputChannelCapability::GameInputChannelOk => {
                format!("{evidence_note}; {declared_note}")
            }
            _ => format!(
                "the game-process probe could not be read ({}) ; {declared_note}; {evidence_note}",
                if notes.is_empty() {
                    "no semantic reading arrived".to_string()
                } else {
                    notes.join(" | ")
                }
            ),
        };

        let probe = InputChannelProbe {
            capability,
            game_process_reachable,
            is_pressed_before: None,
            axis_before,
            axis_after,
            pressed,
            moved_while_pressed,
            declared_in_project_godot: declared,
            detail,
        };
        let ok = capability == InputChannelCapability::GameInputChannelOk;
        let mut step = step;
        if capability == InputChannelCapability::ActionNotBound
            && !step.supports.contains(&"P3".to_string())
        {
            step.supports.push("P3".to_string());
        }
        let observation = if ok {
            format!("input channel probe: {}", probe.observation())
        } else {
            format!(
                "FAILED input channel probe: {} (UNAVAILABLE: no usable game-process input \
                 channel, so the replay below cannot judge F1/F2)",
                probe.observation()
            )
        };
        let extra = serde_json::to_value(&probe)?;
        self.finish_with(step, ExecKind::Replay, None, observation, ok, calls, extra)
            .await?;
        Ok(probe)
    }

    /// DR-69 ④: capture one replay frame and materialize it under
    /// `.hoh/evidence/`.
    ///
    /// `REQUIREMENTS.md:114` fixes E3's evidence form as a replay **with
    /// before/after screenshots**, and `smoke-t9` showed the round could never
    /// satisfy it: the battery produced frames only in its own `screenshot`
    /// step, never around a replayed action.  The capture follows DR-49 exactly:
    /// no `save_path` (the engine accepts only `res://`/`user://` and answers the
    /// image inline without one), the target is invalidated first so an earlier
    /// round's PNG cannot be inherited, and `running_game_capture_frames` is the
    /// fallback when this run has no image yet.
    async fn capture_replay_frame(
        &self,
        label: &str,
        phase: &str,
        calls: &mut Vec<Value>,
    ) -> Option<String> {
        let relative = format!(".hoh/evidence/replay-{label}-{phase}.png");
        let absolute = self.workspace.join(&relative);
        if let Some(parent) = absolute.parent() {
            let _ = std::fs::create_dir_all(parent);
        }
        let _ = invalidate_artifact(&absolute);
        let call_label = format!("{label}:replay_frame_{phase}");
        let mut materialized: Option<String> = None;

        let args = json!({});
        match self
            .call("running_game_capture_screenshot", args.clone())
            .await
        {
            Ok(call) => {
                let parsed = unwrap_mcp_payload(&call.payload);
                calls.push(labeled(
                    call_ok(
                        "running_game_capture_screenshot",
                        &args,
                        &call.payload,
                        &call.correlation,
                    ),
                    &call_label,
                ));
                if let Some(bytes) = extract_inline_image(&parsed) {
                    if write_png(&absolute, &bytes).is_ok() {
                        materialized = Some(relative.clone());
                    }
                }
            }
            Err(failure) => {
                calls.push(labeled(
                    call_fail("running_game_capture_screenshot", &args, &failure),
                    &call_label,
                ));
            }
        }
        if materialized.is_none() {
            let frames_args = json!({"count": 1, "frame_interval": 10});
            match self
                .call("running_game_capture_frames", frames_args.clone())
                .await
            {
                Ok(call) => {
                    let parsed = unwrap_mcp_payload(&call.payload);
                    calls.push(labeled(
                        call_ok(
                            "running_game_capture_frames",
                            &frames_args,
                            &call.payload,
                            &call.correlation,
                        ),
                        &call_label,
                    ));
                    if let Some(bytes) = extract_inline_image(&parsed) {
                        if write_png(&absolute, &bytes).is_ok() {
                            materialized = Some(relative.clone());
                        }
                    }
                }
                Err(failure) => {
                    calls.push(labeled(
                        call_fail("running_game_capture_frames", &frames_args, &failure),
                        &call_label,
                    ));
                }
            }
        }
        materialized
    }

    /// DR-69 ④: assert **inside the game process** that the player's position
    /// differs from `expected`.
    ///
    /// The reading is positional on purpose.  `input_axis` answers `null` on real
    /// hardware (DR-58, re-measured in `smoke-t9`), so an axis-value assertion is
    /// not something E3 can rest on; the engine's own `position` property is.
    /// `expected` is the window's **first sample**, not the pre-injection
    /// reading, so the verdict does not depend on how many frames pass between
    /// the injection and the first sample (the ~14-frame lag the SMOKE-T9
    /// acceptance measured).
    ///
    /// Returns `Some(passed)` when the engine answered a verdict, and `None` when
    /// the assertion could not be made at all (a missing node or property, or an
    /// unreachable game process).  The two must not be confused.
    async fn assert_replay_moved(
        &self,
        label: &str,
        expected: &Value,
        calls: &mut Vec<Value>,
    ) -> Option<bool> {
        let args = json!({
            "node_path": "Player",
            "property": "position",
            "operator": "neq",
            "expected": expected,
        });
        let call_label = format!("{label}:replay_assert_moved");
        match self.call(semantic::ASSERT_NODE_STATE, args.clone()).await {
            Ok(call) => {
                let parsed = unwrap_mcp_payload(&call.payload);
                calls.push(labeled(
                    call_ok(
                        semantic::ASSERT_NODE_STATE,
                        &args,
                        &call.payload,
                        &call.correlation,
                    ),
                    &call_label,
                ));
                parsed.get("passed").and_then(Value::as_bool)
            }
            Err(failure) => {
                calls.push(labeled(
                    call_fail(semantic::ASSERT_NODE_STATE, &args, &failure),
                    &call_label,
                ));
                None
            }
        }
    }

    /// DR-54: one semantic read of the well-known InputMap axis.
    ///
    /// `Input.get_axis` is not a node property, so the semantic reader for it is
    /// `running_game_get_node_property_samples` on the documented
    /// [`SCENARIO_AXIS`] member; the reply is reduced to its `after` value.
    async fn semantic_axis_sample(&self, label: &str, calls: &mut Vec<Value>) -> Option<f64> {
        let args = json!({
            "node_path": "Player",
            "properties": [SCENARIO_AXIS],
            "frame_count": ONE_FRAME,
            "frame_interval": 1,
        });
        match self.call(semantic::PROPERTY_SAMPLES, args.clone()).await {
            Ok(call) => {
                let parsed = unwrap_mcp_payload(&call.payload);
                calls.push(labeled(
                    call_ok(
                        semantic::PROPERTY_SAMPLES,
                        &args,
                        &call.payload,
                        &call.correlation,
                    ),
                    label,
                ));
                observed_after(&parsed, SCENARIO_AXIS)
            }
            Err(failure) => {
                calls.push(labeled(
                    call_fail(semantic::PROPERTY_SAMPLES, &args, &failure),
                    label,
                ));
                None
            }
        }
    }

    /// Run one `running_game_execute_gdscript` expression and record the call.
    ///
    /// DR-54: this helper is kept for **read-only probes only**.  Since DR-54 no
    /// critical assertion may depend on it, so callers must treat its result as
    /// supplementary: the semantic tools above are what the battery's verdicts
    /// are built on.  Its `code` is always a self-contained GDScript function
    /// body with an explicit `return` (DR-50A).
    ///
    /// The returned tuple is `(reading, verbatim failure text)`; the text is
    /// what turns a failed probe into a diagnosable `ACTION_BINDING_UNKNOWN`
    /// instead of a guessed `ACTION_NOT_BOUND`.
    async fn game_script(
        &self,
        code: &str,
        label: &str,
        calls: &mut Vec<Value>,
    ) -> (Option<(f64, f64)>, Option<String>) {
        let args = json!({ "code": code });
        match self
            .call("running_game_execute_gdscript", args.clone())
            .await
        {
            Ok(call) => {
                let parsed = unwrap_mcp_payload(&call.payload);
                let reading = game_script_position(&parsed);
                calls.push(labeled(
                    call_ok(
                        "running_game_execute_gdscript",
                        &args,
                        &call.payload,
                        &call.correlation,
                    ),
                    label,
                ));
                let failure = (reading.is_none()).then(|| parsed.to_string());
                (reading, failure)
            }
            Err(failure) => {
                calls.push(labeled(
                    call_fail("running_game_execute_gdscript", &args, &failure),
                    label,
                ));
                (None, Some(failure.observation()))
            }
        }
    }

    /// DR-54: inject one game-process action through the contract's **semantic**
    /// input API and let the semantic scenario runner drive it.
    ///
    /// The recording API is used (rather than a caller-assembled
    /// `Input.action_press(...)` body) for two reasons: it is the contract's own
    /// "inject an input event" capability, and replaying a recorded event is the
    /// engine's real input path — which is what the `input` steps of
    /// `running_game_run_test_scenario` drive too.
    ///
    /// Returned: `(whether the injection was accepted, refusal)`.  The axis and
    /// the player's position are read separately through
    /// [`BatterySession::semantic_axis_sample`] and
    /// [`BatterySession::semantic_sample_positions`], so every reading the
    /// classification uses comes from a semantic tool.
    async fn semantic_inject_action(
        &self,
        action: &str,
        label: &str,
        calls: &mut Vec<Value>,
    ) -> (bool, Option<String>) {
        let (injected, refusal, _) = self
            .semantic_inject_action_detailed(action, label, calls)
            .await;
        (injected, refusal)
    }

    /// [`BatterySession::semantic_inject_action`] plus the JSON-RPC code of the
    /// refusal, which is what tells "the game's InputMap has no such action" (a
    /// `-32602` **answer** from the engine, DR-54) from "the channel could not be
    /// read at all" (no answer).
    async fn semantic_inject_action_detailed(
        &self,
        action: &str,
        label: &str,
        calls: &mut Vec<Value>,
    ) -> (bool, Option<String>, Option<i64>) {
        let mut recorded = false;
        let mut refusal = None;
        let mut refusal_code: Option<i64> = None;

        // (a) Begin a recording; this is the contract's input-recording entry.
        let create_args = json!({});
        match self
            .call(semantic::CREATE_INPUT_RECORDING, create_args.clone())
            .await
        {
            Ok(call) => {
                calls.push(labeled(
                    call_ok(
                        semantic::CREATE_INPUT_RECORDING,
                        &create_args,
                        &call.payload,
                        &call.correlation,
                    ),
                    &format!("{label}:create_input_recording"),
                ));
                recorded = true;
            }
            Err(failure) => {
                calls.push(labeled(
                    call_fail(semantic::CREATE_INPUT_RECORDING, &create_args, &failure),
                    &format!("{label}:create_input_recording"),
                ));
                refusal_code = failure.code;
                refusal = Some(failure.observation());
            }
        }

        // (b) The injection itself: replaying the recorded event is the engine's
        //     input path, so this is what "deliver the action" means.
        let mut injected = false;
        if recorded {
            let play_args = json!({"events": [{"type": "action", "action": action, "pressed": true}], "speed": 1.0});
            match self
                .call(semantic::PLAY_INPUT_RECORDING, play_args.clone())
                .await
            {
                Ok(call) => {
                    calls.push(labeled(
                        call_ok(
                            semantic::PLAY_INPUT_RECORDING,
                            &play_args,
                            &call.payload,
                            &call.correlation,
                        ),
                        &format!("{label}:play_input_recording"),
                    ));
                    injected = true;
                }
                Err(failure) => {
                    calls.push(labeled(
                        call_fail(semantic::PLAY_INPUT_RECORDING, &play_args, &failure),
                        &format!("{label}:play_input_recording"),
                    ));
                    refusal_code = failure.code;
                    refusal = Some(failure.observation());
                }
            }
        }

        // (c) Read the axis through the semantic scenario runner: an `input` step
        //     drives the action, a `wait` gives the game a frame, and an `assert`
        //     step names the observable.  The scenario is the contract's
        //     "inject input and observe" capability.
        //
        //     DR-58: the member list is `steps` **only**.  The real game-scope
        //     runner refuses `scene_path` for *every* value — it runs inside the
        //     already-running game, so there is no scene for it to play.  The
        //     evidence (frozen under `tests/fixtures/dr58`, sources in
        //     `runs/smoke-t7/**`): hof-rs's own `"current"` answer was
        //     `{"code":-32602, "message":"Parameter 'scene_path' ('current') is
        //     not supported by the game-scope runner …"}`, while the captured
        //     requests that omit the member all answer per-step results.  The
        //     contract document advertises `scene_path` as an optional string,
        //     which is exactly why it can never settle this question (DR-58's
        //     rule: shapes come from captured payloads, not from the document).
        let axis_args = json!({
            "steps": [
                {"type": "input", "action": action, "pressed": true},
                {"type": "wait", "seconds": 0.0},
                {"type": "assert", "node_path": "Player", "property": SCENARIO_AXIS, "expected": 0},
            ],
        });
        match self.call(semantic::TEST_SCENARIO, axis_args.clone()).await {
            Ok(call) => {
                let parsed = unwrap_mcp_payload(&call.payload);
                let mut entry = call_ok(
                    semantic::TEST_SCENARIO,
                    &axis_args,
                    &call.payload,
                    &call.correlation,
                );
                // The scenario's own report of the action it drove is kept
                // verbatim next to the reading, so the record shows *which*
                // action moved the axis.
                entry["observed_axis"] = parsed
                    .get("observed_axis")
                    .cloned()
                    .or_else(|| scenario_axis(&parsed).map(Value::from))
                    .unwrap_or(Value::Null);
                calls.push(labeled(entry, &format!("{label}:test_scenario")));
                injected = true;
            }
            Err(failure) => {
                calls.push(labeled(
                    call_fail(semantic::TEST_SCENARIO, &axis_args, &failure),
                    &format!("{label}:test_scenario"),
                ));
                if refusal.is_none() {
                    refusal_code = failure.code;
                    refusal = Some(failure.observation());
                }
            }
        }

        // (e) Stop the recording and release the injected action.
        if recorded {
            let stop_args = json!({});
            let _ = self
                .record_semantic_call(
                    semantic::STOP_INPUT_RECORDING,
                    stop_args,
                    &format!("{label}:stop_input_recording"),
                    calls,
                )
                .await;
        }
        (injected, refusal, refusal_code)
    }

    /// DR-54: one semantic call, recorded in the step's `calls` array the same
    /// way the probes are — every entry carries the tool, the arguments, the
    /// verbatim payload and the JSON-RPC correlation.
    async fn record_semantic_call(
        &self,
        tool: &str,
        args: Value,
        label: &str,
        calls: &mut Vec<Value>,
    ) -> Result<TracedCall, McpFailure> {
        match self.call(tool, args.clone()).await {
            Ok(call) => {
                calls.push(labeled(
                    call_ok(tool, &args, &call.payload, &call.correlation),
                    label,
                ));
                Ok(call)
            }
            Err(failure) => {
                calls.push(labeled(call_fail(tool, &args, &failure), label));
                Err(failure)
            }
        }
    }

    /// DR-68 ③(a): release one action **inside the game process**.
    ///
    /// The four "release" calls `smoke-t8` recorded all went through
    /// `editor_simulate_input_action` — a different process that cannot drive
    /// the game — so the game never let go of `move_right`, and every later
    /// direction was tested with its opposite still held.  This is the same
    /// semantic input path the press uses
    /// (`running_game_play_input_recording`), carrying `pressed: false`.
    ///
    /// Returns whether the game-process API accepted the release.  A refusal is
    /// recorded and reported but never silently dropped; the caller's summary
    /// says so next to the direction it was clearing for.
    async fn semantic_release_action(
        &self,
        action: &str,
        label: &str,
        calls: &mut Vec<Value>,
    ) -> bool {
        let args = json!({"events": [{"type": "action", "action": action, "pressed": false}], "speed": 1.0});
        self.record_semantic_call(semantic::PLAY_INPUT_RECORDING, args, label, calls)
            .await
            .is_ok()
    }

    /// DR-54: the semantic `Player.position` sample — `before`/`after` come from
    /// `running_game_get_node_property_samples`, not from a script.
    ///
    /// Returns `None` when a quadruple was read, and `Some((payload, refusal))`
    /// when it was not, so the caller can record the step honestly.
    async fn semantic_sample_positions(
        &self,
        action: &str,
        node: &str,
        frames: u64,
        label: &str,
        calls: &mut Vec<Value>,
    ) -> Option<(Value, String)> {
        let args = json!({
            "node_path": node,
            "properties": ["position"],
            "frame_count": frames,
            "frame_interval": 1,
        });
        match self.call(semantic::PROPERTY_SAMPLES, args.clone()).await {
            Ok(call) => {
                let parsed = unwrap_mcp_payload(&call.payload);
                let quadruple = replay_quadruple(action, &parsed, GAME_PROCESS_CHANNEL);
                let mut entry = call_ok(
                    semantic::PROPERTY_SAMPLES,
                    &args,
                    &call.payload,
                    &call.correlation,
                );
                if let Some(quadruple) = &quadruple {
                    entry["quadruple"] = quadruple.clone();
                }
                calls.push(labeled(entry, label));
                match quadruple {
                    Some(_) => None,
                    None => Some((
                        parsed.clone(),
                        format!(
                            "{} returned no frame samples: {parsed}",
                            semantic::PROPERTY_SAMPLES
                        ),
                    )),
                }
            }
            Err(failure) => {
                calls.push(labeled(
                    call_fail(semantic::PROPERTY_SAMPLES, &args, &failure),
                    label,
                ));
                Some((Value::Null, failure.observation()))
            }
        }
    }

    /// DR-73 ③: the semantic `Player.position` sample as **raw pairs**, for the
    /// interaction window.  [`semantic_sample_positions`] reduces the same reply
    /// to its `(action, channel, before, after, velocity)` quadruple; the
    /// interaction window needs the per-frame series instead (a maximum rightward
    /// extent), so both read the one call through one shape.
    async fn semantic_sample_pairs(
        &self,
        frames: u64,
        label: &str,
        calls: &mut Vec<Value>,
    ) -> Option<Vec<(f64, f64)>> {
        let args = json!({
            "node_path": "Player",
            "properties": ["position"],
            "frame_count": frames,
            "frame_interval": 1,
        });
        match self.call(semantic::PROPERTY_SAMPLES, args.clone()).await {
            Ok(call) => {
                let parsed = unwrap_mcp_payload(&call.payload);
                calls.push(labeled(
                    call_ok(
                        semantic::PROPERTY_SAMPLES,
                        &args,
                        &call.payload,
                        &call.correlation,
                    ),
                    label,
                ));
                required_sample_pairs(&parsed)
            }
            Err(failure) => {
                calls.push(labeled(
                    call_fail(semantic::PROPERTY_SAMPLES, &args, &failure),
                    label,
                ));
                None
            }
        }
    }

    /// 5. Input replay: drive `move_right` / `jump` / `move_left` and record
    ///    the `Player` position over time.
    ///
    /// DR-30: at least one frame **position sample** per recording is required,
    /// and a delivered action that leaves the position untouched is
    /// `INPUT_HAD_NO_EFFECT` (`ok = false`), not a success.
    ///
    /// DR-33: the InputMap bindings and the
    /// `(action, before_position, after_position, velocity)` quadruple are
    /// recorded so "the input was never bound" can be told from "the controller
    /// ignores the input".
    ///
    /// DR-35: the **game process** decides.  DR-54: injection now goes through
    /// the contract's semantic input API
    /// (`running_game_create_input_recording` + `running_game_play_input_recording`)
    /// and the decisive position comes from the game-forwarded
    /// `running_game_get_node_property_samples`; the editor-side
    /// `editor_simulate_input_action` is kept only as a supplementary record and
    /// is labelled `EDITOR_SIDE_INJECTION` everywhere it appears, because it can
    /// never reach the game process.
    async fn step_input_replay(&mut self) -> anyhow::Result<()> {
        let mut step = BatteryStep {
            id: "input_replay".to_string(),
            supports: vec!["F1".to_string(), "F2".to_string(), "F3".to_string()],
            timeout_secs: self.limits.timeout_seconds,
            retries: self.limits.max_retries,
        };
        let mut calls = Vec::new();
        let mut summaries: Vec<String> = Vec::new();
        let mut ok = true;
        let mut needs_p3 = false;
        let capability = self.channel.capability;

        // DR-33/DR-35: the editor-side InputMap is recorded as **supplementary**
        // evidence only.  `smoke-t5` proved it cannot speak for the game process:
        // it lists the editor's built-in `ui_*` actions and none of the project's
        // `move_*` ones, which is how a working project got a false
        // `ACTION_NOT_BOUND`.
        let probe_args = json!({});
        let editor_bindings = match self
            .call("editor_get_input_actions", probe_args.clone())
            .await
        {
            Ok(call) => {
                calls.push(labeled(
                    call_ok(
                        "editor_get_input_actions",
                        &probe_args,
                        &call.payload,
                        &call.correlation,
                    ),
                    "editor_side_injection",
                ));
                parse_input_actions(&unwrap_mcp_payload(&call.payload))
            }
            Err(failure) => {
                calls.push(labeled(
                    call_fail("editor_get_input_actions", &probe_args, &failure),
                    "editor_side_injection",
                ));
                None
            }
        };
        let editor_note = match &editor_bindings {
            Some(bindings) => {
                let missing: Vec<&str> = ["move_left", "move_right", "jump"]
                    .into_iter()
                    .filter(|action| !bindings.contains_key(*action))
                    .collect();
                // DR-52: the count is published so the sentence can be checked
                // against the raw `editor_get_input_actions` payload it
                // describes — `smoke-t6`'s diagnostic contradicted its own record
                // (92 actions, the three named ones first, reported as absent).
                if missing.is_empty() {
                    format!(
                        "EDITOR_SIDE_INJECTION: the editor InputMap lists all three actions \
                         ({} action(s) read; this is still not game-process evidence)",
                        bindings.len()
                    )
                } else {
                    format!(
                        "EDITOR_SIDE_INJECTION: the editor InputMap does not list {missing:?} \
                         ({} action(s) read) — that is the editor's own map, not the game's (DR-35)",
                        bindings.len()
                    )
                }
            }
            None => "EDITOR_SIDE_INJECTION: editor_get_input_actions was unavailable".to_string(),
        };
        summaries.push(format!(
            "channel={} ({})",
            capability.code(),
            self.channel.detail
        ));
        summaries.push(editor_note);

        // `(label, action, frames, expected to move the node)`.
        //
        // DR-68 ③(a): every direction is tested from a **clean** game input
        // state.  `smoke-t8` injected every direction with `pressed = true` and
        // never released one *inside the game process* (the four releases all
        // went through `editor_simulate_input_action`, which cannot drive the
        // game), so by the `move_left` window `move_right` was still held:
        // `Input.get_axis("move_left","move_right")` returned 0 and the
        // character could not move horizontally whatever the game's code did.
        let mut held_in_game: Vec<&str> = Vec::new();
        // DR-82 ①: was the jump window of this pass really driven from the
        // ground?  A window whose ground probe refused is **unobserved**, and the
        // raw document must say so — a `jump_reading` attached to a window the
        // harness declined to drive would let a reader score a fall (or an arc
        // the game never produced) as evidence.
        let mut jump_driven = false;
        for (label, action, frames, expect_movement) in [
            ("move_right", "move_right", 60u64, true),
            ("move_right_release", "move_right", 10, false),
            ("jump", "jump", 30, true),
            ("move_left", "move_left", 60, true),
        ] {
            if capability == InputChannelCapability::ActionNotBound {
                // DR-35: only a *game-process* absence reaches this verdict.
                needs_p3 = true;
                ok = false;
                summaries.push(format!(
                    "{label}: ACTION_NOT_BOUND (the game-process InputMap declares no `{action}`)"
                ));
                continue;
            }

            // DR-68 ③(a): reset the previous input **inside the game** before
            // testing a new direction, so two directions can never cancel.
            for previous in held_in_game.drain(..) {
                let released = self
                    .semantic_release_action(previous, &format!("{label}:reset"), &mut calls)
                    .await;
                summaries.push(format!(
                    "{label}: released `{previous}` in the game process before testing \
                     `{action}` (accepted={released})"
                ));
            }

            // DR-82 ①: **a jump window may only be driven from the ground.**
            //
            // `smoke-t15` measured what happens otherwise: the interaction and
            // probe windows had already carried the player 290 px past the end of
            // the only floor, so the `jump` window was pressed in mid-air, the
            // recorded series was a monotone free fall (`min` at index 0,
            // `rise = 0.0`, velocity `+42`) and the engine's `position:neq` still
            // answered `passed=true` — a delivered input read as an observed
            // behaviour.  The harness has no ground query, so the question "is
            // there ground below the player?" is answered by the only reading that
            // can answer it: a short position sample taken immediately before the
            // injection, judged by [`player_is_resting_on_ground`].  A player on a
            // floor holds `y` exactly; a falling one does not.
            //
            // A probe that cannot be read **fails closed**: the window is recorded
            // as unobserved rather than driven blind.
            let airborne_before_jump = if action == "jump" {
                let probe_args = json!({
                    "node_path": "Player",
                    "properties": ["position"],
                    "frame_count": JUMP_GROUND_PROBE_FRAMES,
                    "frame_interval": 1,
                });
                let resting = match self
                    .call("running_game_get_node_property_samples", probe_args.clone())
                    .await
                {
                    Ok(call) => {
                        let parsed = unwrap_mcp_payload(&call.payload);
                        let resting =
                            player_is_resting_on_ground(required_sample_pairs(&parsed).as_deref());
                        calls.push(labeled(
                            call_ok(
                                "running_game_get_node_property_samples",
                                &probe_args,
                                &call.payload,
                                &call.correlation,
                            ),
                            "jump:ground_probe",
                        ));
                        resting
                    }
                    Err(failure) => {
                        calls.push(labeled(
                            call_fail(
                                "running_game_get_node_property_samples",
                                &probe_args,
                                &failure,
                            ),
                            "jump:ground_probe",
                        ));
                        false
                    }
                };
                summaries.push(format!(
                    "{label}: JUMP_GROUND_PROBE {JUMP_GROUND_PROBE_FRAMES} frame(s) before the \
                     injection -> resting_on_ground={resting} \
                     (a window driven off the ground cannot be recorded as an observed jump)"
                ));
                if !resting {
                    summaries.push(format!(
                        "{label}: {JUMP_NOT_DRIVEN} (the player is not resting on ground in this \
                         window, so pressing jump could only record gravity; the level is not \
                         rewritten and the window is left unobserved)"
                    ));
                    if expect_movement {
                        ok = false;
                    }
                }
                !resting
            } else {
                false
            };

            // DR-69 ④: the BEFORE frame of this window, captured while the
            // game is in the state the samples below are compared against.
            let before_frame = self.capture_replay_frame(label, "before", &mut calls).await;
            if before_frame.is_none() {
                summaries.push(format!(
                    "{label}: REPLAY_FRAME_MISSING (the before frame of this window could not \
                     be produced)"
                ));
                if expect_movement {
                    ok = false;
                }
            }

            // (a) Game-process injection, through the contract's semantic input
            //     API (DR-54): `create_input_recording` -> `play_input_recording`
            //     -> `running_game_run_test_scenario` -> `stop_input_recording`.
            //     With an
            //     unknown channel there is no point pretending: the same tools
            //     that failed the probe fail here, and the recording is an honest
            //     gap.
            //
            //     DR-82 ①: a jump window whose probe said the player is airborne is
            //     not injected at all — recording "the jump had no effect" would
            //     blame the project for a drive the harness chose.
            let game_injected = if airborne_before_jump {
                false
            } else if capability == InputChannelCapability::GameInputChannelOk {
                let (injected, refusal) =
                    self.semantic_inject_action(action, label, &mut calls).await;
                if let Some(refusal) = refusal {
                    summaries.push(format!("{label}: {refusal}"));
                }
                if injected {
                    held_in_game.push(action);
                }
                if injected && action == "jump" {
                    jump_driven = true;
                }
                injected
            } else {
                summaries.push(format!(
                    "{label}: game-process injection unavailable ({}); recording the editor-side \
                     attempt only",
                    InputChannelCapability::ActionBindingUnknown.code()
                ));
                false
            };

            // (b) Editor-side injection: supplementary, never decisive.
            let press_args = json!({"action": action, "pressed": true});
            let editor_delivered = match self
                .call("editor_simulate_input_action", press_args.clone())
                .await
            {
                Ok(call) => {
                    calls.push(labeled(
                        call_ok(
                            "editor_simulate_input_action",
                            &press_args,
                            &call.payload,
                            &call.correlation,
                        ),
                        &format!("{label}:{EDITOR_SIDE_INJECTION_MARKER}"),
                    ));
                    true
                }
                Err(failure) => {
                    calls.push(labeled(
                        call_fail("editor_simulate_input_action", &press_args, &failure),
                        &format!("{label}:{EDITOR_SIDE_INJECTION_MARKER}"),
                    ));
                    false
                }
            };
            let editor_marker = if editor_delivered {
                format!(
                    "({EDITOR_SIDE_INJECTION_MARKER}: editor_simulate_input_action acknowledged on the editor \
                     side; channel={EDITOR_PROCESS_CHANNEL})"
                )
            } else {
                format!(
                    "({EDITOR_SIDE_INJECTION_MARKER}: editor_simulate_input_action failed on the editor side; \
                     channel={EDITOR_PROCESS_CHANNEL})"
                )
            };

            // (c) The decisive observation: frames sampled inside the game.
            let monitor_args = json!({
                "node_path": "Player",
                "properties": ["position"],
                "frame_count": frames,
                "frame_interval": 1,
            });
            match self
                .call(
                    "running_game_get_node_property_samples",
                    monitor_args.clone(),
                )
                .await
            {
                Ok(call) => {
                    let parsed = unwrap_mcp_payload(&call.payload);
                    let quadruple = replay_quadruple(action, &parsed, GAME_PROCESS_CHANNEL);
                    let frames_seen = parsed
                        .get("frame_count")
                        .and_then(Value::as_u64)
                        .or_else(|| {
                            parsed
                                .get("samples")
                                .and_then(Value::as_array)
                                .map(|samples| samples.len() as u64)
                        })
                        .unwrap_or(0);
                    let mut entry = call_ok(
                        "running_game_get_node_property_samples",
                        &monitor_args,
                        &call.payload,
                        &call.correlation,
                    );
                    if let Some(quadruple) = &quadruple {
                        entry["quadruple"] = quadruple.clone();
                    }
                    // DR-82 ①: the window's own `y` shape, recorded next to the
                    // quadruple so "an arc was observed" is checkable from the raw
                    // document rather than from the summary sentence.  Only a
                    // window that was **driven** carries one: an unobserved window
                    // has no jump reading to score, whatever the game happened to
                    // do while it was not being driven.
                    let jump = (action == "jump" && jump_driven)
                        .then(|| jump_reading(&parsed))
                        .flatten();
                    if let Some(reading) = jump {
                        entry["jump_reading"] = json!({
                            "rise": reading.rise,
                            "monotone_fall": reading.monotone_fall,
                            "shows_an_arc": reading.shows_an_arc(),
                            "verdict": reading.verdict(),
                        });
                    }
                    calls.push(entry);
                    match quadruple {
                        None => {
                            ok = false;
                            summaries.push(format!(
                                "{label}: NO_FRAME_SAMPLES ({}) {editor_marker}",
                                describe_monitor(label, &parsed)
                            ));
                        }
                        Some(quadruple) => {
                            // DR-68 ⑧: judge the action's **own** axis.  The old
                            // whole-vector `before != after` comparison scored
                            // `move_left` as movement in `smoke-t8` because
                            // gravity moved `y` while `x` was pinned at 584.363
                            // for all 60 frames — a masking false green.
                            //
                            // DR-82 ①: for a jump the bar is higher than "the
                            // axis moved": `smoke-t15`'s window moved `y` by
                            // 1060 px and was still not a jump — it was a fall.
                            // An observed jump must show an **arc**
                            // ([`JumpReading::shows_an_arc`]), and a window that
                            // does not is recorded as unobserved, never as a pass.
                            let movement = movement_on_intended_axis(&quadruple);
                            let arc_failure = match (action == "jump", jump) {
                                (true, Some(reading)) if !reading.shows_an_arc() => Some(reading),
                                _ => None,
                            };
                            if expect_movement && (!movement.moved || arc_failure.is_some()) {
                                ok = false;
                                if let Some(reading) = arc_failure {
                                    summaries.push(format!(
                                        "{label}: {frames_seen} frame(s) \
                                         channel={GAME_PROCESS_CHANNEL} {quadruple} \
                                         axis={} delta={:.6} rise={:.6} \
                                         monotone_fall={} {} (a delivered jump input that only \
                                         fell is not an observed jump; the window is recorded \
                                         as unobserved) {editor_marker}",
                                        movement.axis,
                                        movement.delta,
                                        reading.rise,
                                        reading.monotone_fall,
                                        reading.verdict()
                                    ));
                                } else if capability == InputChannelCapability::GameInputChannelOk {
                                    summaries.push(format!(
                                        "{label}: {frames_seen} frame(s) \
                                         channel={GAME_PROCESS_CHANNEL} {quadruple} \
                                         axis={} delta={:.6} INPUT_HAD_NO_EFFECT {editor_marker}",
                                        movement.axis, movement.delta
                                    ));
                                } else {
                                    // DR-35: both failure modes are still possible.
                                    needs_p3 = true;
                                    summaries.push(format!(
                                        "{label}: {frames_seen} frame(s) \
                                         channel={GAME_PROCESS_CHANNEL} {quadruple} \
                                         axis={} delta={:.6} \
                                         ACTION_BINDING_UNKNOWN + INPUT_HAD_NO_EFFECT \
                                         {editor_marker}",
                                        movement.axis, movement.delta
                                    ));
                                }
                            } else {
                                summaries.push(format!(
                                    "{label}: {frames_seen} frame(s) \
                                     channel={GAME_PROCESS_CHANNEL} {quadruple} axis={} \
                                     delta={:.6} {} {editor_marker}",
                                    movement.axis,
                                    movement.delta,
                                    match jump {
                                        Some(reading) => format!(
                                            "rise={:.6} monotone_fall={} {}",
                                            reading.rise,
                                            reading.monotone_fall,
                                            reading.verdict()
                                        ),
                                        None => String::new(),
                                    }
                                ));
                            }
                            // DR-69 ④: the AFTER frame of this window.
                            let after_frame =
                                self.capture_replay_frame(label, "after", &mut calls).await;
                            if after_frame.is_none() {
                                summaries.push(format!(
                                    "{label}: REPLAY_FRAME_MISSING (the after frame of this \
                                     window could not be produced)"
                                ));
                                if expect_movement {
                                    ok = false;
                                }
                            }

                            // DR-69 ④: the positional assertion the E3 evidence form
                            // requires, made inside the game process.  The expectation is
                            // this window's **first sample**, so the ~14-frame
                            // injection/sampling lag cannot make the verdict depend on its
                            // own offset.
                            let expected_position = quadruple["before_position"].clone();
                            match self
                                .assert_replay_moved(label, &expected_position, &mut calls)
                                .await
                            {
                                Some(true) => summaries.push(format!(
                                    "{label}: POSITION_ASSERT_PASSED \
                                     (position:neq {expected_position} in the game process)"
                                )),
                                Some(false) => {
                                    summaries.push(format!(
                                        "{label}: POSITION_UNCHANGED (the assertion \
                                         position:neq {expected_position} failed inside the game \
                                         process)"
                                    ));
                                    if expect_movement {
                                        ok = false;
                                    }
                                }
                                None => {
                                    summaries.push(format!(
                                        "{label}: POSITION_ASSERTION_UNAVAILABLE (the game \
                                         process could not answer `position:neq`; no \
                                         behavioural evidence for this window)"
                                    ));
                                    if expect_movement {
                                        ok = false;
                                    }
                                }
                            }
                        }
                    }
                }
                Err(failure) => {
                    calls.push(call_fail(
                        "running_game_get_node_property_samples",
                        &monitor_args,
                        &failure,
                    ));
                    summaries.push(format!(
                        "{label}: FAILED {} {editor_marker}",
                        failure.observation()
                    ));
                    ok = false;
                }
            }

            // (d) Re-read the axis inside the game process after the frames —
            //     through the **semantic** reader (DR-54), never a script.
            //
            //     DR-68 ③(a): "the previous input was released" is only half the
            //     claim; the axis reading must show the change, otherwise a
            //     still-cancelling pair of held directions reads as a green
            //     replay.  When the engine answers `null` (its real behaviour for
            //     `input_axis`, DR-58) there is no reading to assert on, and the
            //     position samples above stay the decisive evidence.
            if game_injected {
                let axis = self
                    .semantic_axis_sample(&format!("{label}:game_axis"), &mut calls)
                    .await;
                summaries.push(format!(
                    "{label}: game-process {SCENARIO_AXIS} after {frames} frame(s) = {axis:?}"
                ));
                if let (Some(reading), Some(expected)) = (axis, expected_axis_sign(action)) {
                    if reading.signum() != expected {
                        ok = false;
                        summaries.push(format!(
                            "{label}: INPUT_AXIS_NOT_CHANGED (expected sign {expected}, read \
                             {reading}; a still-held opposite direction cancels the axis)"
                        ));
                    }
                }
            }

            // (e) Editor-side release, same supplementary status.
            let release_args = json!({"action": action, "pressed": false});
            match self
                .call("editor_simulate_input_action", release_args.clone())
                .await
            {
                Ok(call) => calls.push(labeled(
                    call_ok(
                        "editor_simulate_input_action",
                        &release_args,
                        &call.payload,
                        &call.correlation,
                    ),
                    &format!("{label}:{EDITOR_SIDE_INJECTION_MARKER}:release"),
                )),
                Err(failure) => calls.push(labeled(
                    call_fail("editor_simulate_input_action", &release_args, &failure),
                    &format!("{label}:{EDITOR_SIDE_INJECTION_MARKER}:release"),
                )),
            }
        }

        if needs_p3 {
            step.supports.push("P3".to_string());
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

    /// DR-73 ③: **interaction evidence** — the two E3 behaviours the battery
    /// never observed, in the same evidence form the movement windows already
    /// use (before/after frames plus an engine-accepted node-state assertion).
    ///
    /// `REQUIREMENTS.md:114` (E3) names four behaviours: movement, jumping, "at
    /// least one interactable object" and "one end/win condition".  `input_replay`
    /// covers the first two; `smoke-t10` therefore ended with E3 `not_met` even
    /// though the Developer had written coin and goal scripts, because **nothing
    /// in the round ever asked whether a coin was picked up or whether the win
    /// branch ran**.  `running_game_assert_node_state` can answer both, and the
    /// answer is a *closure* assertion on a property the game itself changed:
    ///
    /// * the coin counter label's text must grow over the window, and
    /// * the goal node's [`GOAL_REACHED_PROPERTY`] must still be false before and
    ///   must be true after (an `eq` on the before-read and a `neq` on it),
    ///
    /// Neither is a value the harness writes.  The window only does what a player
    /// does: it holds [`INTERACTION_DRIVE_ACTION`] and observes.  A project where
    /// the player can never touch a coin takes the `COIN_NOT_PICKED_UP` branch,
    /// and one whose goal is not reached splits into two **different** verdicts
    /// (DR-76 ②): `WIN_UNREACHED_WITHIN_BUDGET` / `WIN_NOT_DRIVEN` when the
    /// window's own budget ran out (a coverage verdict, which claims nothing
    /// about the level) and `WIN_BLOCKED_UNDER_MOVE_RIGHT` (DR-77 ③; it was
    /// called `WIN_UNREACHABLE_GEOMETRICALLY`, which said more than this window
    /// measures) when the sampled player stopped advancing with budget still
    /// unspent.  The second name is deliberately bounded by
    /// [`INTERACTION_DRIVE_ACTION`]: the window only ever **holds that one
    /// action**, so the verdict is "holding `move_right` did not advance the
    /// player" and it says nothing about whether a jump, or any other input the
    /// window never sends, could pass.  Both are recorded as
    /// honest `ok = false` for this step, which is what makes the round's own
    /// evidence able to say what E3 still needs.
    async fn step_interaction_evidence(&mut self, scene_tree: Option<Value>) -> anyhow::Result<()> {
        let step = BatteryStep {
            id: "interaction_evidence".to_string(),
            supports: vec![
                "F10".to_string(),
                "F13".to_string(),
                "F11".to_string(),
                "F12".to_string(),
            ],
            timeout_secs: self.limits.timeout_seconds,
            retries: self.limits.max_retries,
        };
        let mut calls = Vec::new();
        let mut summaries: Vec<String> = Vec::new();

        // (a) The HUD cell the coin count lives in.  The scene tree names nodes —
        //     `name`, `path`, `type` — and carries **no text**: every one of the 10
        //     frozen scene-tree payloads from five rounds has exactly those three
        //     keys on a `Label` (DR-76 ①, the DR-73 A1/O1 defect).  The counter
        //     therefore cannot be identified *from the tree*; the tree is used only
        //     to enumerate the `Label`s under `HUD`, and each candidate's `text` is
        //     read through `running_game_get_node_properties`.  The first whose text
        //     starts with the specification's own prefix is the counter; a HUD
        //     where nothing reads that way is an explicit "unreadable", never a
        //     silent zero.
        let candidates = scene_tree
            .as_ref()
            .map(hud_label_candidates)
            .unwrap_or_default();
        summaries.push(format!(
            "interaction: HUD counter candidates (from the scene tree's `name`/`path` only; each \
             text read through `{}`) = {candidates:?}",
            semantic::NODE_PROPERTIES
        ));
        let mut coin_label: Option<String> = None;
        let mut coin_before: Option<String> = None;
        for candidate in &candidates {
            let text = self
                .read_hud_text(Some(candidate.as_str()), &mut calls)
                .await;
            if let Some(text) = text {
                if text.trim_start().starts_with(COIN_COUNTER_PREFIX) {
                    coin_label = Some(candidate.clone());
                    coin_before = Some(text);
                    break;
                }
            }
        }

        // (b) The BEFORE reading of the other observable, and the BEFORE frame.
        //     The counter's before-reading is the one the candidate scan just took
        //     (`coin_before`); it is deliberately not read twice, so the assertion's
        //     expectation is the very reading the scan selected the cell with.
        let goal_before = self
            .read_node_property(GOAL_POSITION_NODE, GOAL_REACHED_PROPERTY, &mut calls)
            .await;
        let before_frame = self
            .capture_replay_frame("interaction", "before", &mut calls)
            .await;
        if before_frame.is_none() {
            summaries.push(format!(
                "interaction: REPLAY_FRAME_MISSING (the before frame of the interaction window \
                 could not be produced)"
            ));
        }

        // (c) The goal's own position, so "the flag is past the end of the level"
        //     is a number in the record.
        let goal_position = self
            .read_node_property(GOAL_POSITION_NODE, "position", &mut calls)
            .await;
        summaries.push(format!(
            "interaction: before readings coin={coin_before:?} goal.{GOAL_REACHED_PROPERTY}={goal_before:?} \
             goal.position={goal_position:?}"
        ));

        // (d) Drive right and sample, batch by batch, until the win is observed
        //     or the batch budget runs out.  The action is held in the game
        //     process across batches (`semantic_inject_action` presses it), so
        //     the player keeps travelling between samples.
        //
        //     DR-76 ②: the loop also records **why** it stopped, because "the
        //     budget ran out" and "the level stopped the player" are different
        //     diagnoses and must never share a verdict.  A batch that moves the
        //     sampled maximum by less than [`INTERACTION_MIN_PROGRESS_PX`] is a
        //     stalled batch; two in a row, with budget left, mean the held action
        //     cannot advance the player any further.
        let mut max_x: Option<f64> = None;
        let mut batches = 0usize;
        let mut stopped_early = false;
        let mut stalled_batches = 0usize;
        let mut stalled = false;
        let mut drive_incomplete = false;
        if !is_false(&goal_before) {
            // The goal already reports `reached` before the drive — either the
            // round's own condition ran at boot or the property is not a flag at
            // all.  Either way the window cannot prove the drive caused it.
            summaries.push(format!(
                "interaction: GOAL_FLAG_NOT_FALSE_BEFORE (goal.{GOAL_REACHED_PROPERTY}={goal_before:?}: \
                 the win branch cannot be attributed to this window)"
            ));
        } else {
            // DR-78 ③: clear the actions this window does not drive, **inside the
            // game process**, before the first batch.  The window's own drive is
            // only `INTERACTION_DRIVE_ACTION`, and `player.gd` reads
            // `Input.get_axis("move_left", "move_right")`: a stale opposite
            // action left over from an earlier window makes the axis `0`, so the
            // player stands still while the injection really succeeded.  A
            // refusal is recorded, never swallowed — an un-cleared action is the
            // difference between "the window did not advance the player" and "the
            // player could not advance", and DR-77's lesson is that those two may
            // not share a sentence.
            for stale in INTERACTION_STALE_ACTIONS {
                if !self
                    .semantic_release_action(
                        stale,
                        &format!("interaction:release_stale_{stale}"),
                        &mut calls,
                    )
                    .await
                {
                    summaries.push(format!(
                        "interaction: STALE_ACTION_NOT_RELEASED (the game-process input channel \
                         refused to release `{stale}` before `{INTERACTION_DRIVE_ACTION}` was \
                         held; a held `{stale}` cancels the drive, so this run cannot tell \"the \
                         player did not advance\" from \"the player could not\")"
                    ));
                }
            }
            for batch in 0..INTERACTION_MAX_BATCHES {
                batches = batch + 1;
                let label = format!("interaction:batch{}", batch + 1);
                let (injected, refusal) = self
                    .semantic_inject_action(INTERACTION_DRIVE_ACTION, &label, &mut calls)
                    .await;
                if let Some(refusal) = refusal {
                    summaries.push(format!("{label}: {refusal}"));
                }
                if !injected {
                    summaries.push(format!(
                        "{label}: DRIVE_NOT_INJECTED (the game-process input channel refused \
                         `{INTERACTION_DRIVE_ACTION}`)"
                    ));
                    drive_incomplete = true;
                    break;
                }
                let before_batch = max_x;
                match self
                    .semantic_sample_pairs(INTERACTION_BATCH_FRAMES, &label, &mut calls)
                    .await
                {
                    Some(positions) => {
                        for (x, _) in positions {
                            max_x = Some(max_x.map_or(x, |current: f64| current.max(x)));
                        }
                    }
                    None => {
                        summaries.push(format!("{label}: NO_FRAME_SAMPLES"));
                        drive_incomplete = true;
                        break;
                    }
                }
                let advanced = match (max_x, before_batch) {
                    (Some(now), Some(previous)) => now > previous + INTERACTION_MIN_PROGRESS_PX,
                    (Some(_), None) => true,
                    _ => false,
                };
                if advanced {
                    stalled_batches = 0;
                } else {
                    stalled_batches += 1;
                }
                if stalled_batches >= INTERACTION_STALL_BATCHES {
                    stalled = true;
                    break;
                }
                match self
                    .read_node_property(GOAL_POSITION_NODE, GOAL_REACHED_PROPERTY, &mut calls)
                    .await
                {
                    Some(Value::Bool(true)) => {
                        stopped_early = true;
                        break;
                    }
                    Some(Value::Bool(false)) => {}
                    other => {
                        summaries.push(format!(
                            "interaction: GOAL_FLAG_UNREADABLE (goal.{GOAL_REACHED_PROPERTY}={other:?} \
                             after batch {}: the win state cannot be observed)",
                            batch + 1
                        ));
                        drive_incomplete = true;
                        break;
                    }
                }
            }
        }
        // DR-76 ②: the numbers the coverage/geometry split is made of.
        let goal_x = goal_position
            .as_ref()
            .and_then(|value| value.get("x"))
            .and_then(Value::as_f64);
        let coverage_shortfall_px = match (max_x, goal_x) {
            (Some(reached), Some(goal)) => Some(goal - reached),
            _ => None,
        };
        let budget_exhausted =
            !stopped_early && !stalled && !drive_incomplete && batches >= INTERACTION_MAX_BATCHES;
        let batches_left = INTERACTION_MAX_BATCHES.saturating_sub(batches);
        summaries.push(format!(
            "interaction: drove `{INTERACTION_DRIVE_ACTION}` for {batches} of \
             {INTERACTION_MAX_BATCHES} batch(es) ({INTERACTION_BATCH_FRAMES} frame(s) each, \
             {INTERACTION_DRIVE_FRAMES} frames budgeted), player max x={max_x:?}, \
             goal.position={goal_position:?}, coverage_shortfall_px={coverage_shortfall_px:?}{}{}",
            if stopped_early {
                ", stopped as soon as the win was observed"
            } else {
                ""
            },
            if stalled {
                format!(
                    ", stopped after {INTERACTION_STALL_BATCHES} batch(es) without forward \
                     progress with {batches_left} batch(es) of budget left"
                )
            } else {
                String::new()
            }
        ));

        // (e) The AFTER frame, then the AFTER readings of both observables.
        let after_frame = self
            .capture_replay_frame("interaction", "after", &mut calls)
            .await;
        if after_frame.is_none() {
            summaries.push(format!(
                "interaction: REPLAY_FRAME_MISSING (the after frame of the interaction window \
                 could not be produced)"
            ));
        }
        let coin_after = self.read_hud_text(coin_label.as_deref(), &mut calls).await;
        let goal_after = self
            .read_node_property(GOAL_POSITION_NODE, GOAL_REACHED_PROPERTY, &mut calls)
            .await;

        let mut ok = true;

        // (f) Coin pickup, in the engine's own verdict shape.  The engine
        //     answered `Coins: N`; the assertion is `N after > N before`, which
        //     is false if the counter never grew — the `smoke-t10` state.
        match (coin_label.as_deref(), coin_before, coin_after) {
            (Some(path), Some(before), Some(after)) => {
                summaries.push(format!(
                    "interaction: coin counter `{path}` {before} -> {after}"
                ));
                match (coin_count(&before), coin_count(&after)) {
                    (Some(before_count), Some(after_count)) => {
                        // The engine compares **strings**, so the expectation is
                        // the label's own before text, not a number: a `gt`/`lt`
                        // on a `text` property would not be the same assertion.
                        let expected = json!(before.clone());
                        match self
                            .assert_property(
                                path,
                                "text",
                                "neq",
                                expected.clone(),
                                "interaction:replay_assert_picked_up",
                                &mut calls,
                            )
                            .await
                        {
                            Some(true) if after_count > before_count => summaries.push(format!(
                                "interaction: COIN_PICKED_UP (the counter grew {before_count} -> \
                                 {after_count}; `text:neq {expected}` accepted in the game process)"
                            )),
                            Some(true) => {
                                ok = false;
                                summaries.push(format!(
                                    "interaction: COIN_COUNTER_CHANGED_WITHOUT_A_PICKUP (text \
                                     changed {before:?} -> {after:?} but the count did not grow)"
                                ));
                            }
                            Some(false) => {
                                ok = false;
                                summaries.push(format!(
                                    "interaction: COIN_NOT_PICKED_UP (the counter stayed \
                                     {before_count} over {batches} driven batch(es); `text:neq \
                                     {expected}` was refused inside the game process)"
                                ));
                            }
                            None => {
                                ok = false;
                                summaries.push(format!(
                                    "interaction: COIN_ASSERTION_UNAVAILABLE (the game process \
                                     could not answer `text:neq {expected}` on `{path}`)"
                                ));
                            }
                        }
                    }
                    _ => {
                        ok = false;
                        summaries.push(format!(
                            "interaction: COIN_COUNTER_UNREADABLE (the label `{path}` carries \
                             {after:?}, which has no `{COIN_COUNTER_PREFIX} <number>` to compare)"
                        ));
                    }
                }
            }
            (None, _, _) => {
                ok = false;
                summaries.push(format!(
                    "interaction: COIN_COUNTER_UNREADABLE (no `Label` under `HUD` whose text \
                     starts with `{COIN_COUNTER_PREFIX}`; F10 cannot be observed)"
                ));
            }
            (Some(path), before, after) => {
                ok = false;
                summaries.push(format!(
                    "interaction: COIN_COUNTER_UNREADABLE (`{path}` could not be read twice; \
                     before={before:?} after={after:?})"
                ));
            }
        }

        // (g) The win branch, in the same shape: the flag must still be false
        //     before, and must be true after the drive.
        let goal_won = is_false(&goal_before) && is_true(&goal_after);
        let goal_lost = is_false(&goal_before) && is_false(&goal_after);
        match (goal_before, goal_after) {
            _ if goal_won => {
                let expected = json!(false);
                match self
                    .assert_property(
                        GOAL_POSITION_NODE,
                        GOAL_REACHED_PROPERTY,
                        "neq",
                        expected.clone(),
                        "interaction:replay_assert_won",
                        &mut calls,
                    )
                    .await
                {
                    Some(true) => summaries.push(format!(
                        "interaction: WIN_DRIVEN (goal.{GOAL_REACHED_PROPERTY} false -> true \
                         while the player drove right; `{GOAL_REACHED_PROPERTY}:neq false` \
                         accepted in the game process)"
                    )),
                    Some(false) => {
                        ok = false;
                        summaries.push(format!(
                            "interaction: WIN_ASSERTION_REFUSED (the reading says the flag \
                             changed but the engine answered false for \
                             `{GOAL_REACHED_PROPERTY}:neq false`)"
                        ));
                    }
                    None => {
                        ok = false;
                        summaries.push(format!(
                            "interaction: WIN_ASSERTION_UNAVAILABLE (the game process could not \
                             answer `{GOAL_REACHED_PROPERTY}:neq false`)"
                        ));
                    }
                }
            }
            _ if goal_lost => {
                ok = false;
                // DR-76 ②: **coverage is not geometry.**  Two very different
                // causes used to be reported with the one word `WIN_NOT_DRIVEN`,
                // and the record's `(player max x, goal.position)` pair then read
                // like unreachability even when the budget was the only limit —
                // which is exactly the false diagnosis `4deefc8` committed (the
                // level is continuous to x=6800; the replay simply never drove
                // far enough).  The verdict now says which of the two it is, and
                // the `WIN_BLOCKED_UNDER_MOVE_RIGHT` one is only reachable when
                // the budget was **not** the limit.
                if stalled && batches_left > 0 {
                    summaries.push(format!(
                        "interaction: WIN_BLOCKED_UNDER_MOVE_RIGHT (goal.{GOAL_REACHED_PROPERTY} \
                         stayed false and the sampled player x did not advance over \
                         {INTERACTION_STALL_BATCHES} consecutive batch(es) of \
                         `{INTERACTION_DRIVE_ACTION}` while {batches_left} batch(es) of the \
                         {INTERACTION_MAX_BATCHES}-batch budget were still unspent; player max \
                         x={max_x:?}, goal.position={goal_position:?}, \
                         coverage_shortfall_px={coverage_shortfall_px:?} — the bound is the level \
                         or the game logic, not the window's coverage; this conclusion is bounded \
                         by the movement direction: the window only holds \
                         `{INTERACTION_DRIVE_ACTION}` and never jumps, so it says nothing about \
                         whether a jump or another input could pass)"
                    ));
                } else if budget_exhausted {
                    summaries.push(format!(
                        "interaction: WIN_UNREACHED_WITHIN_BUDGET / WIN_NOT_DRIVEN (the window \
                         spent all {INTERACTION_MAX_BATCHES} batch(es) = \
                         {INTERACTION_DRIVE_FRAMES} frames of `{INTERACTION_DRIVE_ACTION}` and \
                         goal.{GOAL_REACHED_PROPERTY} stayed false; player max x={max_x:?}, \
                         goal.position={goal_position:?}, \
                         coverage_shortfall_px={coverage_shortfall_px:?} — this is a COVERAGE \
                         verdict, not a geometry verdict: the window did not reach the trigger, \
                         so nothing is claimed about whether the level is passable)"
                    ));
                } else {
                    summaries.push(format!(
                        "interaction: WIN_NOT_DRIVEN (the drive could not be completed \
                         ({batches} of {INTERACTION_MAX_BATCHES} batch(es) ran); player max \
                         x={max_x:?}, goal.position={goal_position:?}, \
                         coverage_shortfall_px={coverage_shortfall_px:?}; no conclusion about the \
                         level is drawn from an incomplete drive)"
                    ));
                }
            }
            (before, _) if !is_false(&before) => {
                ok = false;
                summaries.push(format!(
                    "interaction: WIN_NOT_OBSERVABLE (goal.{GOAL_REACHED_PROPERTY} was {before:?} \
                     before the drive, so this window cannot attribute the win to the player)"
                ));
            }
            (_, after) => {
                ok = false;
                summaries.push(format!(
                    "interaction: WIN_NOT_OBSERVABLE (goal.{GOAL_REACHED_PROPERTY}={after:?} \
                     after the drive; the win state could not be read)"
                ));
            }
        }

        let observation = if ok {
            format!("interaction: {}", summaries.join("; "))
        } else {
            format!(
                "FAILED interaction: {} (UNAVAILABLE: at least one E3 interaction behaviour is \
                 not observable on this candidate)",
                summaries.join("; ")
            )
        };
        self.finish(step, ExecKind::Replay, None, observation, ok, calls)
            .await?;
        Ok(())
    }

    /// DR-73 ③: read one node property through the semantic reader and record the
    /// call.  `None` means the property could not be read — which is not the same
    /// as a property that answered `false`.
    async fn read_node_property(
        &self,
        node_path: &str,
        property: &str,
        calls: &mut Vec<Value>,
    ) -> Option<Value> {
        let args = json!({"node_path": node_path, "properties": [property]});
        match self.call(semantic::NODE_PROPERTIES, args.clone()).await {
            Ok(call) => {
                let parsed = unwrap_mcp_payload(&call.payload);
                calls.push(labeled(
                    call_ok(
                        semantic::NODE_PROPERTIES,
                        &args,
                        &call.payload,
                        &call.correlation,
                    ),
                    &format!("interaction:read_{node_path}_{property}"),
                ));
                node_property_value(&parsed, property)
            }
            Err(failure) => {
                calls.push(labeled(
                    call_fail(semantic::NODE_PROPERTIES, &args, &failure),
                    &format!("interaction:read_{node_path}_{property}"),
                ));
                None
            }
        }
    }

    /// DR-73 ③: read a HUD `Label`'s text through the semantic reader.
    async fn read_hud_text(
        &self,
        node_path: Option<&str>,
        calls: &mut Vec<Value>,
    ) -> Option<String> {
        let path = node_path?;
        let args = json!({"node_path": path, "properties": ["text"]});
        match self.call(semantic::NODE_PROPERTIES, args.clone()).await {
            Ok(call) => {
                let parsed = unwrap_mcp_payload(&call.payload);
                calls.push(labeled(
                    call_ok(
                        semantic::NODE_PROPERTIES,
                        &args,
                        &call.payload,
                        &call.correlation,
                    ),
                    &format!("interaction:read_{path}_text"),
                ));
                node_property_value(&parsed, "text").and_then(|value| {
                    value
                        .as_str()
                        .map(ToOwned::to_owned)
                        .or_else(|| Some(value.to_string()))
                })
            }
            Err(failure) => {
                calls.push(labeled(
                    call_fail(semantic::NODE_PROPERTIES, &args, &failure),
                    &format!("interaction:read_{path}_text"),
                ));
                None
            }
        }
    }

    /// DR-73 ③: one engine-side node-state assertion, in the shape the movement
    /// windows already use.  `expected` is the **before** reading, so the
    /// assertion asks "did this property close while the player acted?".
    async fn assert_property(
        &self,
        node_path: &str,
        property: &str,
        operator: &str,
        expected: Value,
        label: &str,
        calls: &mut Vec<Value>,
    ) -> Option<bool> {
        let args = json!({
            "node_path": node_path,
            "property": property,
            "operator": operator,
            "expected": expected,
        });
        match self.call(semantic::ASSERT_NODE_STATE, args.clone()).await {
            Ok(call) => {
                let parsed = unwrap_mcp_payload(&call.payload);
                calls.push(labeled(
                    call_ok(
                        semantic::ASSERT_NODE_STATE,
                        &args,
                        &call.payload,
                        &call.correlation,
                    ),
                    label,
                ));
                parsed.get("passed").and_then(Value::as_bool)
            }
            Err(failure) => {
                calls.push(labeled(
                    call_fail(semantic::ASSERT_NODE_STATE, &args, &failure),
                    label,
                ));
                None
            }
        }
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
            match self
                .call("running_game_get_node_properties", args.clone())
                .await
            {
                Ok(call) => {
                    let parsed = unwrap_mcp_payload(&call.payload);
                    calls.push(call_ok(
                        "running_game_get_node_properties",
                        &args,
                        &call.payload,
                        &call.correlation,
                    ));
                    // DR-58/G20: the real reply proves the node by its
                    // `node_path` + `properties`, not by a top-level `name` it
                    // never carries (see `node_properties_read`).
                    let present = node_properties_read(&parsed);
                    property_summary
                        .push(format!("{node}={}", if present { "ok" } else { "missing" }));
                    if !present {
                        ok = false;
                    }
                }
                Err(failure) => {
                    calls.push(call_fail(
                        "running_game_get_node_properties",
                        &args,
                        &failure,
                    ));
                    property_summary.push(format!("{node}=FAILED"));
                    ok = false;
                }
            }
        }

        let mut shape_summary: Vec<String> = Vec::new();
        for node in ["Ground", "Player", "Goal"] {
            let args = json!({"node_path": node});
            match self.call("editor_get_collision_info", args.clone()).await {
                Ok(call) => {
                    let parsed = unwrap_mcp_payload(&call.payload);
                    calls.push(call_ok(
                        "editor_get_collision_info",
                        &args,
                        &call.payload,
                        &call.correlation,
                    ));
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
                    calls.push(call_fail("editor_get_collision_info", &args, &failure));
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
            id: "editor_stop_scene".to_string(),
            supports: vec!["N1".to_string()],
            timeout_secs: self.limits.timeout_seconds,
            retries: self.limits.max_retries,
        };
        let args = json!({});
        let (ok, observation, call) = match self.call("editor_stop_scene", args.clone()).await {
            Ok(call) => (
                true,
                format!("editor_stop_scene: {}", unwrap_mcp_payload(&call.payload)),
                call_ok("editor_stop_scene", &args, &call.payload, &call.correlation),
            ),
            Err(failure) => (
                false,
                format!(
                    "FAILED editor_stop_scene: {} (UNAVAILABLE)",
                    failure.observation()
                ),
                call_fail("editor_stop_scene", &args, &failure),
            ),
        };
        // DR-43: whatever the stop reported, the game endpoint is not a valid
        // destination any more.  Dropping it here means a later
        // `running_game_*` call fails loudly instead of reaching a stale port.
        let invalidated = self.tools.game_endpoint().await;
        self.tools.clear_game_endpoint().await;
        let mut call = call;
        if let Some(record) = invalidated {
            call["game_endpoint_invalidated"] = json!(record);
        }
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

// ---------------------------------------------------------------------------
// DR-29: the session synchronization report
// ---------------------------------------------------------------------------

/// DR-29: where a battery session records its `project_get_info` correlation
/// probe, relative to the workspace.
pub const SESSION_SYNC_FILE: &str = ".hoh/deterministic/mcp-sync.json";

/// DR-29: the `result.json.warnings` entry for a desynchronized session.  It
/// carries the observed id offset and the probe count, because "something was
/// wrong" is not actionable.
pub fn desync_warning(report: &SessionSyncReport) -> String {
    let offset = report
        .observed_offset
        .map(|offset| offset.to_string())
        .unwrap_or_else(|| "unknown".to_string());
    format!(
        "mcp_desync_detected: id_offset={offset} probes={} (the MCP server answered with a \
         different request id; the client re-correlated with read-only `{PROBE_TOOL}` probes)",
        report.probes
    )
}

// ---------------------------------------------------------------------------
// DR-43: the game endpoint
// ---------------------------------------------------------------------------

/// DR-43: read the game endpoint out of an `editor_play_scene` reply.
///
/// The contract lets the engine announce it in one of two ways, in this order:
/// an explicit `endpoint`, or an `mcp_port` the endpoint is derived from.
/// `mcp_port_source` is recorded **verbatim** when the engine declares one of
/// the two documented values; when it declares none, the record says
/// `undeclared` rather than inventing `argument`/`auto_free_port`.
///
/// A reply that announces neither is an error: the caller registers nothing and
/// the step fails, because a guessed endpoint would route every later
/// `running_game_*` call somewhere that cannot answer it.
pub fn parse_game_endpoint(payload: &Value) -> Result<GameEndpointRecord, String> {
    let inner = unwrap_mcp_payload(payload);
    let announced = inner
        .get("endpoint")
        .and_then(Value::as_str)
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .map(ToOwned::to_owned);
    let port = inner
        .get("mcp_port")
        .and_then(Value::as_u64)
        .and_then(|port| u16::try_from(port).ok())
        .or_else(|| announced.as_deref().and_then(endpoint::port_of_endpoint));
    let Some(endpoint) = announced.or_else(|| port.map(endpoint::endpoint_for_port)) else {
        return Err(format!(
            "the reply announced neither an `endpoint` nor an `mcp_port`, so the game endpoint \
             cannot be registered (DR-43): {inner}"
        ));
    };
    let source = match inner.get("mcp_port_source").and_then(Value::as_str) {
        Some(declared) if declared == endpoint::SOURCE_ARGUMENT => endpoint::SOURCE_ARGUMENT,
        Some(declared) if declared == endpoint::SOURCE_AUTO_FREE_PORT => {
            endpoint::SOURCE_AUTO_FREE_PORT
        }
        _ => endpoint::SOURCE_UNDECLARED,
    };
    let pid = inner
        .get("pid")
        .and_then(Value::as_u64)
        .and_then(|pid| u32::try_from(pid).ok());
    Ok(GameEndpointRecord {
        endpoint,
        port,
        source: source.to_string(),
        pid,
    })
}

// ---------------------------------------------------------------------------
// DR-30: payload shape helpers
// ---------------------------------------------------------------------------

/// DR-30: the nodes of a scene-tree payload, i.e. every object reachable from
/// `tree`/`scene` that looks like a node.
fn scene_tree_nodes(payload: &Value) -> Vec<&Value> {
    let Some(root) = payload.get("tree").or_else(|| payload.get("scene")) else {
        return Vec::new();
    };
    let mut nodes = Vec::new();
    let mut stack = vec![root];
    while let Some(node) = stack.pop() {
        let Some(object) = node.as_object() else {
            continue;
        };
        if object.contains_key("name") || object.contains_key("path") || object.contains_key("type")
        {
            nodes.push(node);
        }
        if let Some(children) = object.get("children").and_then(Value::as_array) {
            stack.extend(children.iter());
        }
    }
    nodes
}

/// DR-30: a payload is a scene tree only when its nodes carry both a `path` and
/// a `type`.  Returns the node count, or the reason it is not usable.
///
/// `smoke-t3`'s `play_scene_ready` accepted `editor_play_scene`'s reply here; the
/// difference between the two payloads is exactly this shape.
///
/// DR-72 ⑤ (D1): this is also the **readiness predicate** both poll paths use
/// (`wait_for_ready_matching(… , scene_tree_readiness)`), so "the game answered"
/// can never mean two different things in two places again.
fn scene_tree_readiness(payload: &Value) -> Result<usize, String> {
    describe_scene_tree_shape(&unwrap_mcp_payload(payload))
}

fn describe_scene_tree_shape(payload: &Value) -> Result<usize, String> {
    let nodes = scene_tree_nodes(payload);
    if nodes.is_empty() {
        return Err(format!(
            "the payload carries no node with a `path`/`type` under `tree`: {payload}"
        ));
    }
    let mut untyped = 0usize;
    for node in &nodes {
        let path = node.get("path").and_then(Value::as_str).unwrap_or("");
        let kind = node.get("type").and_then(Value::as_str).unwrap_or("");
        if path.is_empty() || kind.is_empty() {
            untyped += 1;
        }
    }
    if untyped > 0 {
        return Err(format!(
            "{untyped} of {} node(s) have no `path`/`type`: {payload}",
            nodes.len()
        ));
    }
    Ok(nodes.len())
}

/// DR-30: the inline image of a `running_game_capture_frames`-style payload, decoded from
/// base64.  Returns `None` when the payload carries no image or the bytes are
/// not a PNG.
fn extract_inline_image(payload: &Value) -> Option<Vec<u8>> {
    fn walk(node: &Value, out: &mut Option<Vec<u8>>) {
        if out.is_some() {
            return;
        }
        match node {
            Value::String(text) => {
                if text.starts_with(BASE64_PNG_PREFIX) {
                    *out = decode_base64(text).filter(|bytes| is_png(bytes));
                }
            }
            Value::Array(items) => items.iter().for_each(|item| walk(item, out)),
            Value::Object(fields) => {
                for (key, value) in fields {
                    let image_key = matches!(
                        key.as_str(),
                        "image_base64" | "png_base64" | "base64" | "image" | "data" | "screenshot"
                    );
                    if image_key {
                        if let Value::String(text) = value {
                            *out = decode_base64(text).filter(|bytes| is_png(bytes));
                        }
                    }
                    if out.is_none() {
                        walk(value, out);
                    }
                }
            }
            _ => {}
        }
    }
    let mut found = None;
    walk(payload, &mut found);
    found
}

const BASE64_PNG_PREFIX: &str = "iVBORw0KGgo";
const PNG_SIGNATURE: &[u8] = b"\x89PNG\r\n\x1a\n";

fn is_png(bytes: &[u8]) -> bool {
    bytes.starts_with(PNG_SIGNATURE)
}

/// DR-30: writing the screenshot is the only thing that makes a `path` a fact.
fn write_png(path: &Path, bytes: &[u8]) -> anyhow::Result<()> {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    std::fs::write(path, bytes)?;
    Ok(())
}

/// DR-49: what an artifact looked like at one instant.
///
/// Freshness is decided on the artifact **state**, so "a file exists at the
/// target" can never be enough on its own: a PNG left behind by an earlier
/// round has the same path but not the same bytes/metadata.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ArtifactFingerprint {
    pub size: u64,
    /// Modification time in nanoseconds since the Unix epoch.
    pub mtime_unix_nanos: u128,
    pub sha256: String,
}

/// DR-49: the fingerprint of `path`, or `None` when there is no readable file.
pub fn artifact_fingerprint(path: &Path) -> Option<ArtifactFingerprint> {
    let metadata = std::fs::metadata(path).ok()?;
    if !metadata.is_file() {
        return None;
    }
    let bytes = std::fs::read(path).ok()?;
    let mtime_unix_nanos = metadata
        .modified()
        .ok()
        .and_then(|time| {
            time.duration_since(std::time::UNIX_EPOCH)
                .ok()
                .map(|duration| duration.as_nanos())
        })
        .unwrap_or(0);
    Some(ArtifactFingerprint {
        size: metadata.len(),
        mtime_unix_nanos,
        sha256: crate::runtime::policy::sha256_hex(&bytes),
    })
}

/// DR-49 ③: did **this** call produce the artifact?
///
/// * nothing on disk — never fresh (a `path` may not be claimed);
/// * nothing before, something now — fresh;
/// * something before and after — fresh only when the bytes or the timestamp
///   actually changed, i.e. when this call rewrote it.
pub fn artifact_is_fresh(
    before: Option<&ArtifactFingerprint>,
    after: Option<&ArtifactFingerprint>,
) -> bool {
    match (before, after) {
        (_, None) => false,
        (None, Some(_)) => true,
        (Some(before), Some(after)) => before != after,
    }
}

/// DR-49 ②: get a pre-existing artifact out of the target path **before** the
/// call, so "the file exists" cannot be satisfied by an older round.
///
/// It is renamed to `<name>.stale-<unix seconds>` rather than deleted: the old
/// artifact stays auditable (it is hidden from the artifact hash — `.hoh` is
/// excluded — and from the hygiene scans, which ignore `.hoh`), while the
/// target itself is empty for the duration of the call.  `None` means there was
/// nothing to invalidate.
///
/// DR-62: the move is accompanied by an explicit [`SupersededSet::record`] in
/// the directory the artifact lives in, and that record — not the
/// `.stale-<ts>` name — is what the candidate-view copies consult.  The record
/// happens **before** the rename: if it cannot be written the invalidation
/// fails loudly rather than moving the bytes aside with no structural trace.
pub fn invalidate_artifact(path: &Path) -> std::io::Result<Option<String>> {
    if !path.is_file() {
        return Ok(None);
    }
    let base = path
        .file_name()
        .map(|name| name.to_string_lossy().into_owned())
        .unwrap_or_else(|| "artifact".to_string());
    let stamp = crate::adapter::engine::now_seconds();
    for attempt in 0..64u32 {
        // DR-59: one naming convention for both producer sites — this one and
        // `hygiene::quarantine_previous_evidence`.
        let name = crate::runtime::hygiene::stale_name(&base, stamp, attempt);
        let candidate = path.with_file_name(&name);
        if !candidate.exists() {
            // DR-62: the structural record first (see the doc comment above).
            if let Some(directory) = path.parent() {
                crate::runtime::hygiene::SupersededSet::record(directory, &name)?;
            }
            std::fs::rename(path, &candidate)?;
            return Ok(Some(name));
        }
    }
    // The name space is a per-second window of 64 names; if it is exhausted the
    // invalidation must still happen, so the file is removed instead of being
    // silently left in place (which would let a stale file be claimed).
    std::fs::remove_file(path)?;
    Ok(Some(format!(
        "{base} (removed: no free .stale-{stamp} name)"
    )))
}

/// Decode standard-alphabet base64 (padding optional).
///
/// Hand-rolled on purpose: the only job is to turn the MCP server's inline PNG
/// into bytes, and the repository is built offline.
fn decode_base64(input: &str) -> Option<Vec<u8>> {
    let mut out = Vec::with_capacity(input.len() / 4 * 3);
    let mut buffer: u32 = 0;
    let mut bits: u32 = 0;
    for byte in input.bytes() {
        let value = match byte {
            b'A'..=b'Z' => byte - b'A',
            b'a'..=b'z' => byte - b'a' + 26,
            b'0'..=b'9' => byte - b'0' + 52,
            b'+' => 62,
            b'/' => 63,
            b'=' => break,
            b'\r' | b'\n' | b' ' | b'\t' => continue,
            _ => return None,
        } as u32;
        buffer = (buffer << 6) | value;
        bits += 6;
        if bits >= 8 {
            bits -= 8;
            out.push(((buffer >> bits) & 0xFF) as u8);
        }
    }
    if out.is_empty() {
        None
    } else {
        Some(out)
    }
}

// ---------------------------------------------------------------------------
// DR-33: InputMap bindings and the replay quadruple
// ---------------------------------------------------------------------------

/// DR-33: `action -> bound keys`, or `None` when the payload's shape is not a
/// binding list at all (which must not be mistaken for "no such action").
fn parse_input_actions(payload: &Value) -> Option<std::collections::BTreeMap<String, Vec<String>>> {
    fn keys_of(value: &Value) -> Vec<String> {
        match value {
            Value::String(text) => vec![text.clone()],
            Value::Array(items) => items.iter().flat_map(keys_of).collect(),
            Value::Object(fields) => ["keys", "key", "events", "bindings", "bound_keys"]
                .iter()
                .filter_map(|key| fields.get(*key))
                .flat_map(keys_of)
                .collect(),
            _ => Vec::new(),
        }
    }

    let container = payload
        .get("actions")
        .or_else(|| payload.get("input_map"))
        .or_else(|| payload.get("inputs"))?;
    let mut bindings = std::collections::BTreeMap::new();
    match container {
        Value::Object(map) => {
            for (name, value) in map {
                bindings.insert(name.clone(), keys_of(value));
            }
        }
        Value::Array(items) => {
            for item in items {
                // DR-52: the engine's `editor_get_input_actions` answers
                // `{"actions": ["jump", "move_left", …], "count": N}` — an array
                // of **names**.  The pre-DR-52 parser only understood the retired
                // addon's `[{"name": …, "keys": …}]` shape, silently skipped
                // every string and returned an *empty* map, which made the
                // `input_replay` diagnostic state the opposite of its own raw
                // record ("the editor InputMap does not list move_left …").
                if let Some(name) = item.as_str() {
                    bindings.insert(name.to_string(), Vec::new());
                    continue;
                }
                let Some(name) = item
                    .get("name")
                    .or_else(|| item.get("action"))
                    .and_then(Value::as_str)
                else {
                    continue;
                };
                bindings.insert(name.to_string(), keys_of(item));
            }
        }
        _ => return None,
    }
    Some(bindings)
}

/// DR-30: `(action, before_position, after_position, velocity)`.
///
/// `None` means there was not a single frame carrying a `position` — the
/// `0 frame(s), position unknown` case `smoke-t3` reported as `ok = true`.
///
/// DR-35: every quadruple also names the **process** it was observed in, so a
/// reader can never mistake an editor-side reading for game-process evidence.
fn replay_quadruple(action: &str, payload: &Value, channel: &str) -> Option<Value> {
    let samples = payload.get("samples").and_then(Value::as_array)?;
    let positions: Vec<&Value> = samples
        .iter()
        .filter_map(|sample| sample.get("position"))
        .collect();
    let first = positions.first()?;
    let last = positions.last()?;
    let velocity = payload
        .get("velocity")
        .cloned()
        .or_else(|| {
            samples
                .iter()
                .rev()
                .find_map(|sample| sample.get("velocity").cloned())
        })
        .unwrap_or_else(|| derived_velocity(&positions));
    Some(json!({
        "action": action,
        "channel": channel,
        "before_position": position_of(first),
        "after_position": position_of(last),
        "velocity": velocity_of(&velocity),
    }))
}

fn position_of(value: &Value) -> Value {
    json!({
        "x": value.get("x").and_then(Value::as_f64).unwrap_or(0.0),
        "y": value.get("y").and_then(Value::as_f64).unwrap_or(0.0),
    })
}

/// DR-68 ⑧: what one replayed action did to the axis it is supposed to move.
#[derive(Clone, Copy, Debug)]
pub struct AxisMovement {
    /// `"x"` for the horizontal actions, `"y"` for `jump`.
    pub axis: &'static str,
    /// `after - before` **on that axis only**.
    pub delta: f64,
    /// Any change on that axis counts; a change on another axis never does.
    pub moved: bool,
}

/// DR-68 ⑧: judge the replay on the action's **intended axis**.
///
/// The predicate this replaces was `before_position != after_position`, i.e. a
/// whole-vector comparison.  `smoke-t8` scored `move_left` as `ok = true` that
/// way: the character was falling (`y` 270.94 → 283.99) while `x` stayed exactly
/// `584.363` for all 60 frames, so gravity alone produced "movement".  A
/// horizontally dead action scored as a success next to the same action's real
/// failure in the QA gap list — the masking false green the acceptance found.
///
/// The comparison is exact (no epsilon): the question is "did this axis move at
/// all", and a pinned axis repeats the same float verbatim.
pub fn movement_on_intended_axis(quadruple: &Value) -> AxisMovement {
    let axis = intended_axis(quadruple["action"].as_str().unwrap_or(""));
    let component = |position: &Value, key: &str| position[key].as_f64().unwrap_or(0.0);
    let delta = component(&quadruple["after_position"], axis)
        - component(&quadruple["before_position"], axis);
    AxisMovement {
        axis,
        delta,
        moved: delta != 0.0,
    }
}

/// The axis an action is supposed to move.
fn intended_axis(action: &str) -> &'static str {
    if action == "jump" {
        "y"
    } else {
        "x"
    }
}

// ---------------------------------------------------------------------------
// DR-82 ①: a jump window must be driven from the ground, and its reading must
// be an arc
// ---------------------------------------------------------------------------

/// DR-82 ①: how many frames the pre-jump ground probe observes.
///
/// Two frames is the smallest series that can distinguish "resting" from
/// "moving": a single sample says nothing about whether the player is supported.
pub const JUMP_GROUND_PROBE_FRAMES: u64 = 2;

/// DR-82 ①: the token a jump window that was **not driven** carries.
///
/// It is deliberately not `INPUT_HAD_NO_EFFECT`: nothing was delivered, so the
/// window says nothing about the project's jump — the harness refused to drive it
/// off the ground.  A reader who wants to know whether the game's jump works must
/// see "unobserved", not "broken".
pub const JUMP_NOT_DRIVEN: &str = "JUMP_NOT_DRIVEN";

/// DR-82 ①: how much `y` may vary across the probe and still count as resting.
///
/// `Player.position` is a character coordinate, not a physics velocity; a player
/// walking on a floor holds `y` exactly (the frozen `smoke-t15` interaction
/// window sampled `263.925201416016` for every one of its 840 frames), while a
/// falling one changes it by tens of pixels per frame.  The tolerance is
/// therefore only there to absorb float noise.
pub const JUMP_GROUND_EPSILON: f64 = 0.001;

/// DR-82 ①: is a sampled `y` series the reading of a player **resting on
/// ground**?
///
/// This is the predicate the pre-jump probe is judged with, and it is
/// deliberately brittle: a resting player's `y` does not change at all, so a
/// series whose `y` moves by more than [`JUMP_GROUND_EPSILON`] is *not* resting.
/// It says nothing about the level's geometry — the harness has no ground query
/// — but it answers the only question that matters before pressing jump: *is the
/// player supported right now?*  `smoke-t15`'s jump window was driven 290 px past
/// the end of the only floor, at `y = 1492.8` and falling at `+42`; a probe there
/// reads a moving `y` and refuses the window.
///
/// `None` (no usable samples) is **not** resting: an unreadable probe must fail
/// closed exactly like an unreadable channel.
pub fn player_is_resting_on_ground(samples: Option<&[(f64, f64)]>) -> bool {
    let Some(samples) = samples else {
        return false;
    };
    if samples.len() < 2 {
        return false;
    }
    let first = samples[0].1;
    samples
        .iter()
        .all(|(_, y)| (y - first).abs() <= JUMP_GROUND_EPSILON)
}

/// DR-82 ①: what one jump window's `y` series really shows.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct JumpReading {
    /// How far the player rose **above the window's first sample**, in pixels:
    /// `first(y) - min(y)`.  Zero means the highest point *is* the first sample,
    /// i.e. the window started at the top of whatever motion it recorded — which
    /// is the T15 free fall (`rise = 0.0`, `min` at index 0), and a negative
    /// value would mean the player never returned to the window's start.
    ///
    /// The sign is stated in this comment because the acceptance computed the
    /// same quantity as `min - first`: `1492.8 - 1492.8 = 0.0` is the same zero,
    /// and the sign that makes "the player rose" a positive number is this one.
    pub rise: f64,
    /// Is `y` non-decreasing across the whole window?
    pub monotone_fall: bool,
}

impl JumpReading {
    /// DR-82 ①: a window may be recorded as an **observed jump** only when it
    /// shows an upward arc: the player's highest point comes after the window's
    /// first sample (`rise > 0`) and the series is not a monotone fall.
    ///
    /// `smoke-t15`'s window had `min` at index 0 and `rise = 0.0`; it was a free
    /// fall, and the engine's `position:neq` passed only because the position had
    /// changed — which is exactly the `injected != moved` confusion this rule
    /// removes.
    pub fn shows_an_arc(&self) -> bool {
        self.rise > 0.0 && !self.monotone_fall
    }

    /// The one-word name the record uses, so a reader can tell a rejected window
    /// from an absent one.
    pub fn verdict(&self) -> &'static str {
        if self.shows_an_arc() {
            "JUMP_ARC_OBSERVED"
        } else if self.monotone_fall {
            "JUMP_DEGENERATE_FALL"
        } else {
            "JUMP_NO_RISE"
        }
    }
}

/// DR-82 ①: read a `running_game_get_node_property_samples` payload's `y`
/// series as a [`JumpReading`], or `None` when the payload carried no usable
/// position samples (which must not be confused with a degenerate reading: no
/// evidence is not evidence of a fall).
pub fn jump_reading(payload: &Value) -> Option<JumpReading> {
    let samples = payload.get("samples").and_then(Value::as_array)?;
    let mut ys: Vec<f64> = Vec::new();
    for sample in samples {
        let y = sample.get("position")?.get("y")?.as_f64()?;
        ys.push(y);
    }
    jump_reading_of(&ys)
}

/// DR-82 ①: the arithmetic of [`JumpReading`] over an explicit `y` series.
///
/// `min` and monotonicity are computed by their definitions rather than by
/// comparing the endpoints, because the T15 window's endpoints *did* differ — it
/// was the *shape* that made it a free fall.
pub fn jump_reading_of(ys: &[f64]) -> Option<JumpReading> {
    let first = *ys.first()?;
    let min = ys.iter().copied().fold(f64::INFINITY, f64::min);
    let monotone_fall = ys.windows(2).all(|pair| pair[1] >= pair[0]);
    Some(JumpReading {
        rise: first - min,
        monotone_fall,
    })
}

/// DR-68 ③(a): the sign `Input.get_axis("move_left","move_right")` must show
/// while `action` is held.  `None` for an action that is not part of that axis
/// (`jump`), where the reading carries no expectation.
fn expected_axis_sign(action: &str) -> Option<f64> {
    match action {
        "move_left" => Some(-1.0),
        "move_right" => Some(1.0),
        _ => None,
    }
}

fn velocity_of(value: &Value) -> Value {
    json!({
        "x": value.get("x").and_then(Value::as_f64).unwrap_or(0.0),
        "y": value.get("y").and_then(Value::as_f64).unwrap_or(0.0),
    })
}

/// The per-frame delta of the last two samples, so a constant recording yields
/// a real `(0, 0)` instead of a missing field.
fn derived_velocity(positions: &[&Value]) -> Value {
    let (Some(previous), Some(last)) = (
        positions
            .len()
            .checked_sub(2)
            .and_then(|i| positions.get(i)),
        positions.last(),
    ) else {
        return json!({"x": 0.0, "y": 0.0});
    };
    let delta = |key: &str| {
        last.get(key).and_then(Value::as_f64).unwrap_or(0.0)
            - previous.get(key).and_then(Value::as_f64).unwrap_or(0.0)
    };
    json!({"x": delta("x"), "y": delta("y")})
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

// ---------------------------------------------------------------------------
// DR-35: the game-process input channel
// ---------------------------------------------------------------------------

/// DR-35: the battery step that probes the **game process** before any input
/// evidence is collected.
pub const INPUT_PROBE_STEP_ID: &str = "input_channel_probe";

/// DR-78 ③: the battery step that drives `move_right` and samples the player's
/// own travel.  Named here because the ordering rule below is about this step.
pub const INPUT_REPLAY_STEP_ID: &str = "input_replay";

/// DR-78 ③: the battery step that observes the coin counter's transition.
pub const COIN_OBSERVING_BATTERY_STEP: &str = "interaction_evidence";

/// DR-78 ③: the battery steps that **hold a horizontal action and sample the
/// player's travel**, and can therefore sweep a coin before the observing window
/// ever sees the counter move.
///
/// This is not a stylistic list.  `smoke-t11` proved the consequence: the
/// `input_replay` `move_right` window carried the player from `192.000045776367`
/// to `408.333038330078`, i.e. straight through `Coin1` at `x=400`; the only one
/// of eleven frames with a coin in it was `replay-move_right-before.png`; and the
/// interaction window — which runs *after* it — read `Coins: 1` as its first
/// reading.  `main.gd` starts at `0` and `coin.gd::collect()` is the only
/// increment, so the `0 -> 1` transition F10's claim names was structurally
/// unobservable from that point on.
///
/// The rule the list encodes: [`COIN_OBSERVING_BATTERY_STEP`] must run **before**
/// every step in it.  `the_coin_observing_window_runs_before_every_consuming_window`
/// in `tests/evidence_battery.rs` executes the battery and reddens if the order
/// is changed, which is what makes the rule a test instead of a comment.
pub const COIN_CONSUMING_BATTERY_STEPS: [&str; 2] = [INPUT_PROBE_STEP_ID, INPUT_REPLAY_STEP_ID];

/// DR-35: the action the channel probe drives.
pub const PROBE_ACTION: &str = "move_right";
/// DR-35: how many frames the game gets between `action_press` and the re-read.
pub const PROBE_FRAME_COUNT: u64 = 30;

/// DR-54: the platformer actions the evidence battery's input steps drive, in
/// the order they are exercised.
pub const PLATFORMER_ACTIONS: [&str; 3] = ["move_right", "move_left", "jump"];

/// DR-35: the `running_game_execute_gdscript` payloads, i.e. GDScript *expressions* run
/// inside the **game** process by the addon's `mcp_runtime_agent.gd`.
///
/// They are wrapped in `str(...)` for two reasons: the addon answers
/// `{"result": str(result)}` (a null result is not a usable shape), and the
/// position read must arrive as one parseable string.
///
/// The shape of `mcp_runtime_agent.gd::_cmd_execute_script` is decisive here:
/// it runs `Expression.execute([], self, false)` with the autoload node as the
/// base instance, so **only members of that node are resolvable** — engine
/// singletons (`Input`, `InputMap`, `Engine`, …) and global classes are not.
/// See D29 裁决 6 for the measurement; that is exactly why a probe failure must
/// be recorded as `ACTION_BINDING_UNKNOWN` instead of being read as
/// `ACTION_NOT_BOUND`.
///
/// DR-50: `running_game_execute_gdscript`'s `code` is a GDScript **function
/// body** (`running_game_script_execution.cpp:57-59`), so a value leaves the
/// body only through `return`.  `smoke-t6` sent bare expressions, so all four
/// transport-successful probe calls answered
/// `{"result":null,"result_type":"Nil"}` and the channel could never be read.
/// Two shapes follow, and they are different on purpose:
///
/// * a **reading** (`has_action`, `is_action_pressed`, `axis`, `position`) is
///   `return <expression>`;
/// * a **mutation** (`action_press`, `action_release`) stays a statement,
///   because those engine calls return `void` and this engine refuses to use a
///   void call as a value (`gdscript_analyzer.cpp:3498`: `Cannot get return
///   value of call to "action_press()" because it returns "void".`).
pub mod probe_scripts {
    use super::PROBE_ACTION;

    /// `InputMap.has_action(<action>)` inside the game process.
    pub fn has_action(action: &str) -> String {
        format!("return str(InputMap.has_action(\"{action}\"))")
    }

    /// `Input.is_action_pressed(<action>)` inside the game process.
    pub fn is_action_pressed(action: &str) -> String {
        format!("return str(Input.is_action_pressed(\"{action}\"))")
    }

    /// `Input.get_axis("move_left", "move_right")` inside the game process.
    pub fn axis() -> String {
        "return str(Input.get_axis(\"move_left\", \"move_right\"))".to_string()
    }

    /// `Input.action_press(<action>)` inside the game process.
    ///
    /// A statement: the engine call returns `void`, so `return`/`str()` on it
    /// would not compile (DR-50).
    pub fn press(action: &str) -> String {
        format!("Input.action_press(\"{action}\")")
    }

    /// `Input.action_release(<action>)` inside the game process.  A statement,
    /// like [`press`].
    pub fn release(action: &str) -> String {
        format!("Input.action_release(\"{action}\")")
    }

    /// `Player.position` inside the game process.
    ///
    /// This one deliberately uses no engine singleton: `get_tree()` is a member
    /// of the base node, so it resolves.  It is the "is the game process
    /// reachable at all?" half of the probe, kept apart from the
    /// "is `Input` reachable?" half.
    pub fn player_position() -> String {
        "return str(get_tree().current_scene.get_node_or_null(\"Player\").position.x) + \",\" + \
         str(get_tree().current_scene.get_node_or_null(\"Player\").position.y)"
            .to_string()
    }

    /// The default probe action, for callers that do not pick one.
    pub fn default_action() -> &'static str {
        PROBE_ACTION
    }
}

/// DR-73 ③: the label prefix the public specification uses for the collected
/// coin counter (`PRD-mario.md` F10: "the HUD coin count +1").
///
/// The cell is **declared** here so the interaction step reads the same wording
/// the product is written against, and a Tester quoting a claim can map it back
/// to the observation line.  The step matches a `Label` whose text *starts with*
/// this prefix, so both `Coins: 3` and `Coins: 3/120` are read; a HUD that names
/// the counter without the prefix is reported as `COIN_COUNTER_UNREADABLE`, not
/// silently treated as "no pickup".
pub const COIN_COUNTER_PREFIX: &str = "Coins:";

/// DR-73 ③: the property a goal node exposes when the win branch ran.
///
/// The step never sets it: the engine's own assertion tool observes it, so "the
/// game drove its win branch" is what the record shows rather than what the
/// harness wished.
pub const GOAL_REACHED_PROPERTY: &str = "reached";

/// DR-73 ③: the goal's own position, read through the semantic property reader
/// so "the goal is physically past the end of the level" is measurable instead
/// of guessed.
pub const GOAL_POSITION_NODE: &str = "Goal";

/// DR-73 ③: the action that carries the player through the level while the
/// interaction window observes.  A single named action can reach a coin and a
/// goal placed anywhere to the right, which is how the PRD lays out the level
/// (F17: one-way rightward progress).
pub const INTERACTION_DRIVE_ACTION: &str = "move_right";

/// DR-73 ③ / DR-76 ②: how many drive/sample batches the interaction window is
/// willing to spend, and how many frames each batch samples.
///
/// The window stops early as soon as the win is observed, so the cost is paid
/// only by a project whose level is long — which is exactly the project whose
/// reachability is in question.
///
/// The budget is a **promise about the specification**, not a taste.  `PRD-mario.md`
/// F17 bounds a full traversal at `30–120` seconds, so a window that cannot drive
/// for 120 seconds cannot observe the win of a level the specification allows.
/// The DR-73 budget was `24 × 60 = 1440` frames = 24 s ≈ 5280 px, while the frozen
/// `smoke-t10` goal's trigger sits 6308 px from spawn: even a flawless game was
/// recorded as a win gap, and the record's `(player max x, goal.position)` pair
/// then read like unreachability even though the ground really spans to x=6800
/// (A2/A3).  `INTERACTION_MAX_BATCHES` is therefore
/// [`SPEC_MAX_TRAVERSAL_SECONDS`]-worth of one-second batches plus
/// [`INTERACTION_BUDGET_MARGIN_BATCHES`] of slack, and
/// `tests/evidence_battery.rs` pins both the arithmetic and the behaviour: a
/// change here has to redden a test.
pub const SPEC_MAX_TRAVERSAL_SECONDS: u64 = 120;
/// DR-76 ②: ten one-second batches (≈2200 px at the frozen 220 px/s) of margin
/// over the specification's own longest traversal.
pub const INTERACTION_BUDGET_MARGIN_BATCHES: usize = 10;
pub const INTERACTION_MAX_BATCHES: usize =
    SPEC_MAX_TRAVERSAL_SECONDS as usize + INTERACTION_BUDGET_MARGIN_BATCHES;
pub const INTERACTION_BATCH_FRAMES: u64 = 60;
/// DR-76 ②: how far the window can drive in total, in frames of game time.
pub const INTERACTION_DRIVE_FRAMES: u64 = INTERACTION_MAX_BATCHES as u64 * INTERACTION_BATCH_FRAMES;
/// DR-76 ②: a batch that moves the sampled maximum x by less than this is a
/// stalled batch.  One frame at the frozen 220 px/s is 3.6667 px, so `1.0` px
/// separates "the player is still travelling" from "the player is not".
pub const INTERACTION_MIN_PROGRESS_PX: f64 = 1.0;
/// DR-76 ②: how many consecutive stalled batches mean the held action cannot
/// advance the player — the `WIN_BLOCKED_UNDER_MOVE_RIGHT` verdict, only ever
/// reachable with budget left to spend.
pub const INTERACTION_STALL_BATCHES: usize = 2;

/// DR-78 ③: the actions the interaction window must **clear inside the game
/// process** before it starts driving.
///
/// The window only ever holds [`INTERACTION_DRIVE_ACTION`]; anything else that is
/// still held cancels it.  `player.gd` moves by
/// `Input.get_axis("move_left", "move_right")`, so a leftover `move_left` makes
/// the axis `0` and the player stand still **while the window is really
/// pressing** — which is exactly the `smoke-t11` interaction window: 180 of 180
/// samples at `x=225.000045776367`, a run that had just been travelling left at
/// full speed (`239.666732788086` was its previous sample, `14.666687011719 px` =
/// four frames earlier), and a `facing: -1` at the end of the window.
///
/// `input_replay` clears the *previous* direction at the start of each of its
/// windows (`the_input_replay_releases_the_previous_direction_before_the_next_one`),
/// but its **last** window has no successor to clear for it, so `move_left` was
/// still held when the next step ran.  Releasing the stale actions here makes the
/// observing window self-sufficient: it no longer depends on the order of the
/// steps around it for its own drive to work.
pub const INTERACTION_STALE_ACTIONS: [&str; 1] = ["move_left"];

/// DR-54: the semantic game tools the evidence battery is built on.
///
/// The contract (177 tools) already knows what "inject an action", "look at the
/// input axis", "assert a node property" and "move the player" mean.  Building
/// those out of caller-assembled GDScript made the battery's decidability depend
/// on whether a string compiles — `smoke-t6`'s structural fragility, and the
/// exact path that took the game endpoint down (DR-50B).  These names are the
/// single place the semantic capabilities are spelled.
pub mod semantic {
    /// Inject an action (via the recorded-input API) and observe the axis, in
    /// one semantic call.
    pub const TEST_SCENARIO: &str = "running_game_run_test_scenario";
    /// The game-side sample of a node property over frames — the semantic reader.
    pub const PROPERTY_SAMPLES: &str = "running_game_get_node_property_samples";
    /// Begin recording the game's input events.
    pub const CREATE_INPUT_RECORDING: &str = "running_game_create_input_recording";
    /// Replay the recorded input events.
    pub const PLAY_INPUT_RECORDING: &str = "running_game_play_input_recording";
    /// Stop recording and return the recorded events.
    pub const STOP_INPUT_RECORDING: &str = "running_game_stop_input_recording";
    /// Assert one node property against an expectation.
    pub const ASSERT_NODE_STATE: &str = "running_game_assert_node_state";
    /// Move the player to a target position.
    pub const MOVE_PLAYER_TO_TARGET: &str = "running_game_move_player_to_target";
    /// Read one node's properties (no sampling).
    pub const NODE_PROPERTIES: &str = "running_game_get_node_properties";
}

/// DR-54: the game-side property the scenarios drive and observe.
pub const SCENARIO_AXIS: &str = "input_axis";

/// DR-54: the readiness sample the battery uses when it needs one game frame of a
/// node property instead of a caller-assembled read.
pub const ONE_FRAME: u64 = 1;

/// DR-54: the JSON-RPC code the engine answers when the request is valid but the
/// game's `InputMap` has no such action.
///
/// It is the same `-32602` the contract documents for "the argument names
/// something this endpoint cannot resolve", and it is an **answer** — which is
/// what makes `ACTION_NOT_BOUND` an honest verdict instead of a guess.  A
/// transport failure has no code at all, so the two can never be confused.
///
/// The code is necessary but not sufficient: `-32602` is also what a malformed
/// request gets, so the refusal must also **say** it
/// ([`ACTION_NOT_BOUND_MARKER`]).
pub fn is_action_not_bound_code(code: i64) -> bool {
    code == -32602
}

/// DR-54: the token a semantic input refusal must carry to be read as "the
/// game's `InputMap` has no such action".
pub const ACTION_NOT_BOUND_MARKER: &str = "ACTION_NOT_BOUND";

/// DR-35: the three-state capability of the game-process input channel.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, serde::Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum InputChannelCapability {
    /// The action exists in the game process and pressing it moved the axis
    /// and/or the player: the channel is usable.
    GameInputChannelOk,
    /// The action really does not exist in the **game** `InputMap`.  This is the
    /// only honest way to reach `ACTION_NOT_BOUND`.
    ActionNotBound,
    /// The probe itself failed or its shape could not be read.  Never downgrade
    /// this to `ACTION_NOT_BOUND` (DR-35).
    #[default]
    ActionBindingUnknown,
}

impl InputChannelCapability {
    pub fn code(self) -> &'static str {
        match self {
            InputChannelCapability::GameInputChannelOk => "GAME_INPUT_CHANNEL_OK",
            InputChannelCapability::ActionNotBound => "ACTION_NOT_BOUND",
            InputChannelCapability::ActionBindingUnknown => "ACTION_BINDING_UNKNOWN",
        }
    }

    /// Every code a Tester may search for, in one place.
    pub fn all_codes() -> [&'static str; 3] {
        [
            "GAME_INPUT_CHANNEL_OK",
            "ACTION_NOT_BOUND",
            "ACTION_BINDING_UNKNOWN",
        ]
    }
}

/// DR-35: the full outcome of the channel probe, carried into `input_replay` so
/// both steps tell the same story.
///
/// DR-57 (DEF-2): the field `has_action: Option<bool>` was **deleted** here.  It
/// had been hard-wired to `None` since the semantic migration (the verdict no
/// longer reads `InputMap.has_action`), nothing in the tree ever read it, yet it
/// was serialized into the published raw evidence
/// (`.hoh/deterministic/raw/input_channel_probe.json`), where a consumer could
/// read `null` as "the action does not exist" — a conclusion this field never
/// carried.  Deleting it removes the ambiguity at the source; the `pressed`
/// field below is the semantic evidence that replaced it.  Do not re-add a
/// field here unless it has a reader.
#[derive(Clone, Debug, Default, serde::Serialize)]
pub struct InputChannelProbe {
    pub capability: InputChannelCapability,
    /// The game process answered a `Player.position` read.
    pub game_process_reachable: bool,
    pub is_pressed_before: Option<bool>,
    pub axis_before: Option<f64>,
    pub axis_after: Option<f64>,
    pub pressed: bool,
    pub moved_while_pressed: bool,
    /// DR-35 diagnostic only: which of the three PRD actions `project.godot`
    /// *declares*.  Never evidence of behaviour — a declaration is not a
    /// running binding.
    pub declared_in_project_godot: Vec<String>,
    /// Why the capability came out the way it did.
    pub detail: String,
}

impl InputChannelProbe {
    /// The one-line marker every consumer can search for by literal.
    pub fn observation(&self) -> String {
        format!("{} ({})", self.capability.code(), self.detail)
    }
}

/// DR-35: the game-process reading of one `running_game_execute_gdscript` reply.
///
/// The addon answers `{"result": str(value)}`, so the value is normally a
/// string; a raw boolean/number is accepted too, because an addon that stops
/// double-`str()`-ing its result must not turn into `ACTION_BINDING_UNKNOWN`.
fn game_script_result(payload: &Value) -> Option<Value> {
    let inner = unwrap_mcp_payload(payload);
    inner.get("result").cloned()
}

/// DR-54: the boolean/number readers of a `running_game_execute_gdscript` reply.
///
/// Since DR-54 the read-only probe only reads a position (`game_script_position`,
/// which is still used), so these two are kept **for their tests**: they document
/// and pin the parser's strictness — a reply whose shape is not a boolean/number
/// is `None`, never a guessed reading — which is the property the whole probe
/// design rests on (`smoke-t5` turned an unreadable probe into a false
/// `ACTION_NOT_BOUND`).
#[cfg(test)]
fn game_script_bool(payload: &Value) -> Option<bool> {
    match game_script_result(payload)? {
        Value::Bool(value) => Some(value),
        Value::String(text) => match text.trim().to_ascii_lowercase().as_str() {
            "true" => Some(true),
            "false" => Some(false),
            _ => None,
        },
        _ => None,
    }
}

#[cfg(test)]
fn game_script_f64(payload: &Value) -> Option<f64> {
    match game_script_result(payload)? {
        Value::Number(number) => number.as_f64(),
        Value::String(text) => text.trim().parse::<f64>().ok(),
        _ => None,
    }
}

/// DR-35: `(x, y)` out of the `"x,y"` position script.
fn game_script_position(payload: &Value) -> Option<(f64, f64)> {
    let text = match game_script_result(payload)? {
        Value::String(text) => text,
        _ => return None,
    };
    let (x, y) = text.split_once(',')?;
    Some((x.trim().parse().ok()?, y.trim().parse().ok()?))
}

/// DR-54: the observed axis out of a `running_game_run_test_scenario` reply.
///
/// The runner answers a per-step result list; the axis is whatever the
/// `input_axis` step reported under `observed` (or `actual`, the two names the
/// contract's assert steps use).  A shape that carries neither is `None` — never
/// a guessed reading.
fn scenario_axis(payload: &Value) -> Option<f64> {
    let inner = unwrap_mcp_payload(payload);
    let results = inner
        .get("results")
        .or_else(|| inner.get("steps"))
        .or_else(|| inner.get("observations"))
        .and_then(Value::as_array)?;
    for entry in results {
        if entry.get("property").and_then(Value::as_str) != Some(SCENARIO_AXIS) {
            continue;
        }
        for key in ["observed", "actual", "value"] {
            if let Some(value) = entry.get(key) {
                if let Some(number) = as_f64(value) {
                    return Some(number);
                }
            }
        }
    }
    None
}

/// Accepts both a JSON number and its string form (the engine's assert steps
/// echo observed values either way).
fn as_f64(value: &Value) -> Option<f64> {
    match value {
        Value::Number(number) => number.as_f64(),
        Value::String(text) => text.trim().parse().ok(),
        _ => None,
    }
}

/// DR-54: the **last** observed value of `property` in a
/// `running_game_get_node_property_samples` reply — the "after" reading.
///
/// The reply's `samples` entries carry the property as a direct member (`{x,y}`
/// for `position`) or under a `properties` object; both real shapes are accepted
/// and anything else is `None`, never a guessed reading.
fn observed_after(payload: &Value, property: &str) -> Option<f64> {
    let samples = payload.get("samples").and_then(Value::as_array)?;
    let last = samples.last()?;
    for key in ["properties", "values", "values_by_property"] {
        if let Some(value) = last.get(key).and_then(|object| object.get(property)) {
            if let Some(number) = as_f64(value) {
                return Some(number);
            }
        }
    }
    as_f64(last.get(property)?)
}

// ---------------------------------------------------------------------------
// DR-58: the engine's **real** reply shapes (captured, not inferred)
// ---------------------------------------------------------------------------

/// DR-58: is this `running_game_get_node_properties` payload a **resolved node
/// read**?
///
/// The real shape was captured on the real machine and is frozen under
/// `tests/fixtures/dr58/` (`MANIFEST.json` names each source under `runs/**`
/// and its sha256); engine `4.8.dev.mono.custom_build.035edfce7`.  The payload
/// is
///
/// ```json
/// {"node_path": "/root/Main/Player", "properties": { "name": "Player", … }, "type": "CharacterBody2D"}
/// ```
///
/// There is **no top-level `name`**: the node's name is a member of
/// `properties`, and only for node types that have one.  Reading `name`
/// (DR-54 at the channel probe, and the older `00601476` at the node assertions)
/// therefore made the predicate a constant `false` and scored successful
/// payloads as `missing` (QA gap G20).
///
/// A reply counts as a resolved read when it names a **non-empty** `node_path`
/// *and* carries a **non-empty** `properties` dictionary.  Both are required so
/// the predicate is not vacuous: `{}`, `{"name":"Player"}`,
/// `{"node_path":"/root/Main/Player"}`, and
/// `{"node_path":"/root/Main/Player","properties":{}}` all stay `false`.  The
/// pre-DR-58 top-level-`name` fixture shape stays `false` as well — DR-58 keeps
/// no compatibility layer for a shape the real engine does not send.
pub fn node_properties_read(payload: &Value) -> bool {
    let resolved = payload
        .get("node_path")
        .and_then(Value::as_str)
        .map(|path| !path.is_empty())
        .unwrap_or(false);
    let properties = payload
        .get("properties")
        .and_then(Value::as_object)
        .map(|properties| !properties.is_empty())
        .unwrap_or(false);
    resolved && properties
}

/// DR-35: which of `actions` the project declares in `project.godot`.
///
/// Diagnostic only.  It exists to separate "the tool chain could not read the
/// game's InputMap" from "the project never declared the action", which is the
/// difference between a `ACTION_BINDING_UNKNOWN` and a real defect — the exact
/// confusion that cost `smoke-t5` a whole round.
pub fn project_declared_actions(workspace: &Path, actions: &[&str]) -> Vec<String> {
    let Ok(text) = std::fs::read_to_string(workspace.join("project.godot")) else {
        return Vec::new();
    };
    let mut in_input = false;
    let mut declared: Vec<String> = Vec::new();
    for raw in text.lines() {
        let line = raw.trim();
        if line.starts_with('[') {
            in_input = line.starts_with("[input]");
            continue;
        }
        if !in_input {
            continue;
        }
        let Some(name) = line.split('=').next().map(str::trim) else {
            continue;
        };
        if name.is_empty() {
            continue;
        }
        if actions.contains(&name) && !declared.iter().any(|d| d == name) {
            declared.push(name.to_string());
        }
    }
    declared
}

/// DR-35: the two processes whose observations must never be conflated.  The
/// editor can inject input into itself (`Input.parse_input_event`) and read its
/// own `InputMap`, but it cannot reach the game process.
pub const GAME_PROCESS_CHANNEL: &str = "game_process";
pub const EDITOR_PROCESS_CHANNEL: &str = "editor_process";
/// DR-35: the literal a Tester searches for to recognise an editor-side record.
pub const EDITOR_SIDE_INJECTION_MARKER: &str = "EDITOR_SIDE_INJECTION";

/// Attach a `label` to a recorded call, so one step's payload list stays
/// readable when the same tool is called several times (DR-35).
fn labeled(mut entry: Value, label: &str) -> Value {
    if let Some(object) = entry.as_object_mut() {
        object.insert("label".to_string(), Value::String(label.to_string()));
    }
    entry
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

/// DR-76 ①: the `NodePath`s of every `Label` under `HUD`, in tree order.
///
/// The interaction window has to find the coin counter without knowing what the
/// round named it — but it may **not** do so from the node's text, because the
/// real `running_game_get_scene_tree` reply does not carry one.  Every one of the
/// 10 frozen scene-tree payloads from the five rounds that produced them
/// (`runs/smoke-t5|t6|t7|t8|t10`, `scene_tree.json` and `play_scene_ready.json`)
/// gives a `Label` exactly `name`, `path` and `type`; the DR-73 window required a
/// `text` member, so on real hardware it found no counter at all and every round
/// answered `COIN_COUNTER_UNREADABLE` no matter what the game did (A1/O1).
///
/// This function therefore uses the tree only for what the tree really has: the
/// set of candidate cells, located by their own `/root/...` paths — the form the
/// semantic reader resolves.  The caller reads each candidate's `text` through
/// `running_game_get_node_properties` and keeps the one that starts with the
/// specification's prefix.  A `Label` outside `HUD` is not a candidate, which is
/// where the HUD cell is required to be (N2).
pub fn hud_label_candidates(tree: &Value) -> Vec<String> {
    let Some(root) = tree.get("tree") else {
        return Vec::new();
    };
    let mut found: Vec<String> = Vec::new();
    visit_nodes(root, &mut |node| {
        let kind = node.get("type").and_then(Value::as_str).unwrap_or("");
        if kind != "Label" {
            return;
        }
        let path = node.get("path").and_then(Value::as_str).unwrap_or("");
        if !path.contains("/HUD/") {
            return;
        }
        found.push(path.to_string());
    });
    found
}

/// DR-73 ③: one property out of a `running_game_get_node_properties` reply.
///
/// The real engine answers `{"node_path":..., "properties":{<name>:<value>}}`
/// (DR-58), so the value is read from `properties`; the flat spelling is
/// accepted too because the contract's own example uses it.  A property that is
/// absent answers `None`, which the caller must not confuse with `false`.
pub fn node_property_value(payload: &Value, property: &str) -> Option<Value> {
    payload
        .get("properties")
        .and_then(|properties| properties.get(property))
        .cloned()
        .or_else(|| payload.get(property).cloned())
}

/// DR-73 ③: the exact `(x, y)` pairs out of a
/// `running_game_get_node_property_samples` reply, or `None` when it carried no
/// usable samples.  Unlike [`replay_quadruple`] this keeps the whole series.
fn required_sample_pairs(payload: &Value) -> Option<Vec<(f64, f64)>> {
    let samples = payload.get("samples").and_then(Value::as_array)?;
    let mut pairs = Vec::new();
    for sample in samples {
        let position = sample.get("position")?;
        let x = position.get("x").and_then(Value::as_f64)?;
        let y = position.get("y").and_then(Value::as_f64)?;
        pairs.push((x, y));
    }
    if pairs.is_empty() {
        None
    } else {
        Some(pairs)
    }
}

/// DR-73 ③: the number a `Coins: <n>` label carries, or `None` when the text is
/// not that shape.  `None` is deliberately distinct from `0`: "the HUD has no
/// readable counter" is not "the counter says zero".
pub fn coin_count(text: &str) -> Option<i64> {
    let rest = text.trim_start().strip_prefix(COIN_COUNTER_PREFIX)?;
    let digits: String = rest
        .trim_start()
        .chars()
        .take_while(|character| character.is_ascii_digit())
        .collect();
    digits.parse::<i64>().ok()
}

/// DR-73 ③: the boolean a JSON property reading carries, distinguished from "the
/// property could not be read at all".  `Some(Value::Bool(false))` is a reading;
/// `None` is the absence of one, and the two take different branches.
pub fn is_false(value: &Option<Value>) -> bool {
    matches!(value, Some(Value::Bool(false)))
}

pub fn is_true(value: &Option<Value>) -> bool {
    matches!(value, Some(Value::Bool(true)))
}

/// DR-41: drop the stale GDExtension line from `.godot/extension_list.cfg`.
///
/// Every other line survives byte-for-byte (the file is re-assembled from the
/// original line slices), and a cache that becomes empty is deleted instead of
/// being left as an empty file that Godot might still read.
fn remove_stale_extension_cache(workspace: &Path) -> anyhow::Result<()> {
    let cache = workspace.join(EXTENSION_LIST_CACHE);
    let Ok(raw) = std::fs::read_to_string(&cache) else {
        return Ok(());
    };
    let kept: String = raw
        .split_inclusive('\n')
        .filter(|line| line.trim_end() != BUNDLED_ADDON_EXTENSION)
        .collect();
    if kept == raw {
        // Nothing named the retired extension: never touch the file.
        return Ok(());
    }
    if kept.trim().is_empty() {
        std::fs::remove_file(&cache)?;
        return Ok(());
    }
    std::fs::write(&cache, kept)?;
    Ok(())
}

/// DR-41: remove `<workspace>/addons/godot_mcp_rs/` — that exact path only.
fn remove_bundled_addon_dir(workspace: &Path) -> anyhow::Result<()> {
    let addon = workspace.join(BUNDLED_ADDON_DIR);
    if addon.is_dir() {
        std::fs::remove_dir_all(&addon)?;
    }
    Ok(())
}

/// DR-41/DR-53: what one `enabled=` line's edit does.
///
/// The pre-DR-53 signature was `Option<String>`, where `None` meant *both*
/// "the list became empty" and "this line is not a `PackedStringArray` at all".
/// `enabled=true` was therefore treated as an emptied list and deleted the whole
/// `[editor_plugins]` section — a parse failure silently modifying the file,
/// which violates DR-41's byte-conservative rule.
#[derive(Clone, Debug, PartialEq, Eq)]
enum PackedArrayEdit {
    /// The entry is not in the list: the caller must not write.
    Absent,
    /// The entry was removed and other entries remain.
    Updated(String),
    /// The list became empty, so the line (and its section) has to go.
    Emptied,
    /// The line is not a `PackedStringArray(...)`; the outcome cannot be known,
    /// so nothing may be touched.
    Unrecognised,
}

/// `enabled=PackedStringArray(...)` minus one quoted entry.
fn packed_string_array_without(line: &str, entry: &str) -> PackedArrayEdit {
    let Some(open) = line.find('(') else {
        return PackedArrayEdit::Unrecognised;
    };
    let Some(close) = line.rfind(')') else {
        return PackedArrayEdit::Unrecognised;
    };
    if close <= open {
        return PackedArrayEdit::Unrecognised;
    }
    let inner = &line[open + 1..close];
    // The keyword must be `PackedStringArray` (or a bare `enabled=` list) and
    // nothing may follow the closing parenthesis but whitespace.
    let keyword = line[..open].trim();
    let tail = line[close + 1..].trim();
    let known_keyword = keyword.ends_with("PackedStringArray")
        || keyword == "enabled"
        || keyword.ends_with("enabled");
    if !known_keyword || !tail.is_empty() {
        return PackedArrayEdit::Unrecognised;
    }
    let quoted = format!("\"{entry}\"");
    let items: Vec<&str> = inner
        .split(',')
        .map(str::trim)
        .filter(|item| !item.is_empty())
        .collect();
    let kept: Vec<&str> = items
        .iter()
        .copied()
        .filter(|item| *item != quoted)
        .collect();
    if kept.len() == items.len() {
        return PackedArrayEdit::Absent;
    }
    if kept.is_empty() {
        return PackedArrayEdit::Emptied;
    }
    PackedArrayEdit::Updated(format!(
        "{}({}){}",
        &line[..open],
        kept.join(", "),
        &line[close + 1..]
    ))
}

/// DR-41/DR-53: the outcome of the reverse-cleanup pass.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum AddonCleanup {
    /// Nothing named the retired plugin: the file is byte-identical.
    Untouched(&'static str),
    /// The retired entry was removed (and the section, if it became empty).
    Removed,
    /// The `[editor_plugins]` section could not be parsed: the file is
    /// byte-identical, and this is why.
    Unparseable(String),
}

impl AddonCleanup {
    /// Was the file rewritten?
    pub fn changed(&self) -> bool {
        matches!(self, AddonCleanup::Removed)
    }

    /// Why the file was left alone, when it was left alone for a reason worth
    /// reporting (DR-53).
    pub fn reason(&self) -> Option<&str> {
        match self {
            AddonCleanup::Untouched(_) => None,
            AddonCleanup::Removed => None,
            AddonCleanup::Unparseable(reason) => Some(reason),
        }
    }
}

/// Reverse of the retired DR-4 behaviour: guarantee the bundled GDExtension
/// channel is **disabled** (DR-41).
///
/// Idempotent by construction and byte-conservative: when the file does not
/// mention the retired plugin (or has no `[editor_plugins]` section at all) it
/// is left exactly as it is; when it does, only the offending entry is removed
/// from the `enabled` list and every sibling stays byte-for-byte.  A list that
/// becomes empty takes the whole section with it.
///
/// DR-53: a **malformed** `enabled=` line (one that is not a
/// `PackedStringArray(...)`) is `Unparseable`, and the file is left untouched.
fn ensure_bundled_addon_disabled(project_file: &Path) -> anyhow::Result<AddonCleanup> {
    let raw = std::fs::read_to_string(project_file)?;
    let lines: Vec<&str> = raw.split_inclusive('\n').collect();

    let Some(header) = lines
        .iter()
        .position(|line| line.trim_end() == EDITOR_PLUGINS_HEADER)
    else {
        return Ok(AddonCleanup::Untouched(
            "there is no `[editor_plugins]` section",
        ));
    };
    let end = (header + 1..lines.len())
        .find(|&index| lines[index].trim_start().starts_with('['))
        .unwrap_or(lines.len());
    let Some(enabled) =
        (header + 1..end).find(|&index| lines[index].trim_start().starts_with("enabled"))
    else {
        return Ok(AddonCleanup::Untouched(
            "the `[editor_plugins]` section declares no `enabled` list",
        ));
    };

    match packed_string_array_without(lines[enabled], MCP_PLUGIN_PATH) {
        PackedArrayEdit::Unrecognised => Ok(AddonCleanup::Unparseable(format!(
            "the `[editor_plugins]` `enabled=` line is not a `PackedStringArray(...)`, so whether \
             it names {MCP_PLUGIN_PATH} cannot be decided; the file was left untouched (DR-53): {}",
            lines[enabled].trim_end()
        ))),
        PackedArrayEdit::Absent => Ok(AddonCleanup::Untouched(
            "the `enabled` list does not name the retired plugin",
        )),
        PackedArrayEdit::Updated(updated) => {
            if updated == lines[enabled] {
                // Already satisfied: never touch the file.
                return Ok(AddonCleanup::Untouched("the file is already clean"));
            }
            let mut kept = lines.clone();
            kept[enabled] = updated.as_str();
            std::fs::write(project_file, kept.concat())?;
            Ok(AddonCleanup::Removed)
        }
        PackedArrayEdit::Emptied => {
            // The list is empty now: the section must go entirely.
            let mut kept: Vec<&str> = Vec::with_capacity(lines.len());
            kept.extend_from_slice(&lines[..header]);
            kept.extend_from_slice(&lines[end..]);
            // Removing the section must not leave a doubled blank separator.
            if header > 0
                && kept[header - 1].trim().is_empty()
                && kept.get(header).map(|line| line.trim().is_empty()) == Some(true)
            {
                kept.remove(header);
            }
            if kept.concat() == raw {
                return Ok(AddonCleanup::Untouched("the file is already clean"));
            }
            std::fs::write(project_file, kept.concat())?;
            Ok(AddonCleanup::Removed)
        }
    }
}

#[async_trait::async_trait]
impl ProjectAdapter for GodotAdapter {
    fn initialize(&self, workspace: &Path) -> anyhow::Result<()> {
        std::fs::create_dir_all(workspace)?;
        let project_file = workspace.join("project.godot");
        if project_file.is_file() {
            // Already a Godot project.  DR-41: an `A₀` produced by an earlier
            // version still carries the retired GDExtension channel, so the
            // reverse cleanup is enforced in place — idempotently, and without
            // touching a project that never had it.
            //
            // DR-53: a file whose `enabled=` line cannot be parsed is left
            // byte-identical, and the reason is reported instead of hidden.
            let cleanup = ensure_bundled_addon_disabled(&project_file)?;
            if let Some(reason) = cleanup.reason() {
                tracing::warn!("{reason}");
            }
            remove_bundled_addon_dir(workspace)?;
            remove_stale_extension_cache(workspace)?;
            return Ok(());
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

        // DR-41 (C4): the MCP tool channel is the engine's **native module**.
        // Nothing is copied into the project, so there is nothing that could be
        // missing either — there is nothing copied in and no marker file.  The reverse cleanup still runs so a `--force-init` over an
        // old directory cannot resurrect the retired channel.
        remove_bundled_addon_dir(workspace)?;
        remove_stale_extension_cache(workspace)?;
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

    /// DR-37: the Developer's artifact is the project itself; it counts as valid
    /// only when the main scene is structurally sound and names a non-empty
    /// script.
    fn developer_artifact_valid(&self, workspace: &Path) -> bool {
        developer_artifact_valid_in(workspace, &self.config.main_scene)
    }

    /// DR-17: the deterministic evidence battery.
    ///
    /// DR-24 adds two steps in front of the editor-error baseline:
    /// `project_reload_and_open` (the editor is forced onto the on-disk scene)
    /// and `scene_structure` (the `.tscn` root/parent check whose message is the
    /// Developer's executable hint).
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
        BatterySession::new(
            workspace,
            tools,
            &self.battery,
            self.config.main_scene.clone(),
        )
        .run()
        .await
    }

    /// DR-70 ①: the game session the whole round runs against.
    ///
    /// It is started before the first role, so the route a role's `hoh tools
    /// call` adopts is published for the entire window in which the Planner,
    /// the Developer and (after the battery restarts it) the Tester run.  The
    /// readiness poll is not decoration: DR-70 ② refuses a published route whose
    /// destination does not answer, so the record must be published only next to
    /// a game that is actually answering.
    ///
    /// DR-71 ①: "only next to a game that is actually answering" is now the
    /// **order of the two steps**, not a hope about their timing.  The announced
    /// endpoint is installed for in-process routing, the readiness poll runs
    /// against it, and publication happens afterwards — so a poll that fails
    /// cannot leave a route behind, and a publication that fails fails the start
    /// instead of being swallowed.
    async fn start_round_game(
        &self,
        _workspace: &Path,
        tools: &dyn ToolChannel,
    ) -> anyhow::Result<Option<crate::tools::endpoint::GameEndpointRecord>> {
        let play_args = json!({"mode": "main"});
        let call = tools
            .call(Role::Developer, "editor_play_scene", play_args)
            .await
            .map_err(|error| anyhow::anyhow!("editor_play_scene: {error}"))?;
        let record = parse_game_endpoint(&call.payload).map_err(anyhow::Error::msg)?;
        // DR-71 ①: the announced endpoint is installed for **in-process routing
        // only**; it is not published yet.  DR-70 published it here and polled
        // readiness afterwards, so a poll that failed at `:3871` left a route the
        // first role could adopt — the DR-70 acceptance observed exactly that
        // (probe case B/C: `Some(true)` inside the first role's window).
        tools.install_game_endpoint(record.clone()).await?;

        let tree_args = json!({"max_depth": -1});
        // DR-72 ⑤ (D1): the round's readiness predicate is the battery's, so a
        // reply that is not a scene tree can never confirm the round's route.
        let ready = wait_for_ready_matching(
            tools,
            Role::Developer,
            "running_game_get_scene_tree",
            tree_args,
            self.battery.ready_timeout_seconds,
            READY_POLL_INTERVAL_MS,
            None,
            scene_tree_readiness,
        )
        .await;
        if !ready.ok {
            let problem = ready
                .failure
                .map(|failure| failure.observation())
                .unwrap_or_else(|| "no attempt was made".to_string());
            // The route must not survive a start that was never confirmed:
            // `clear_game_endpoint` drops the in-process route and withdraws the
            // published file, so there is nothing for a role to adopt.
            tools.clear_game_endpoint().await;
            anyhow::bail!(
                "the round's game did not answer `running_game_get_scene_tree` after {} poll(s): \
                 {problem}",
                ready.attempts
            );
        }

        // Readiness is confirmed: only now may the route become visible to another
        // process.  A publish failure is a **failed start**, not a discarded value
        // (DR-70 acceptance A5): the round would otherwise believe a route exists
        // that every role fails to reach.
        if let Err(error) = tools.publish_game_endpoint().await {
            tools.clear_game_endpoint().await;
            return Err(error.context(
                "the round's game is ready but its route could not be published, so no role \
                 could reach it",
            ));
        }
        Ok(Some(record))
    }

    /// DR-70 ①: stop the round's game and withdraw the route.
    ///
    /// Whatever the stop reports, the route is withdrawn: the runtime calls this
    /// on every exit path, including the ones where the battery never reached its
    /// own `editor_stop_scene` (the `?` that skipped it is exactly the error path
    /// DR-69's acceptance found leaving a file behind).
    async fn stop_round_game(&self, tools: &dyn ToolChannel) -> anyhow::Result<()> {
        let _ = tools
            .call(Role::Developer, "editor_stop_scene", json!({}))
            .await;
        tools.clear_game_endpoint().await;
        Ok(())
    }

    /// DR-78 ②: publish the route of a game a **role** started.
    ///
    /// `smoke-t11` (F-T11-1) is the measurement this closes.  The Tester ran
    /// `hoh tools call editor_play_scene` and the engine answered pid 4784 /
    /// port 57902; the very next command in the same shell,
    /// `type runs\smoke-t11\game_endpoint.json`, still printed pid 33536 /
    /// port 56821 — a process that no longer existed — and all three
    /// `running_game_*` calls were refused with DR-43's explicit
    /// `game_endpoint_unavailable`.  The publisher was only ever the runtime
    /// battery's own `play_scene_ready` step, so **a route a role starts is a
    /// route nobody writes**.
    ///
    /// The publisher/adopter boundary is now explicit: this method (reached
    /// through `ProjectAdapter`, driven by `hoh tools call editor_play_scene`)
    /// is the only role-side publisher, and
    /// [`crate::tools::bridge::adopt_published_game_route`] is the only adopter.
    /// They meet at `runs/<id>/game_endpoint.json` and nowhere else.
    ///
    /// The order is the round start's order, for the same reason: install for
    /// in-process routing, confirm readiness against the **installed** route,
    /// and only then publish — an unconfirmed game must not leave a route for
    /// another process, and a publish that fails is a failure, not a discarded
    /// value.  Every failure path withdraws the route (DR-43: the refusal a call
    /// gets must be the explicit one, never the editor endpoint).
    async fn publish_role_started_game_route(
        &self,
        tools: &dyn ToolChannel,
        role: Role,
        announced: &Value,
    ) -> anyhow::Result<Option<crate::tools::endpoint::GameEndpointRecord>> {
        // DR-43: the reply is the **only** source of the endpoint.  A reply that
        // announces neither `endpoint` nor `mcp_port` cannot be published, and a
        // guessed endpoint would route every later `running_game_*` call
        // somewhere that cannot answer it.
        let record = parse_game_endpoint(announced).map_err(anyhow::Error::msg)?;
        tools.install_game_endpoint(record.clone()).await?;

        let tree_args = json!({"max_depth": -1});
        // DR-72 ⑤ (D1): the readiness predicate is the battery's own scene-tree
        // shape check, so "the game answered" cannot mean two things in two
        // places.  The poll runs as the role that asked for the scene, so a role
        // that may not read the tree cannot have a route published in its name.
        let ready = wait_for_ready_matching(
            tools,
            role,
            "running_game_get_scene_tree",
            tree_args,
            self.battery.ready_timeout_seconds,
            READY_POLL_INTERVAL_MS,
            None,
            scene_tree_readiness,
        )
        .await;
        if !ready.ok {
            let problem = ready
                .failure
                .map(|failure| failure.observation())
                .unwrap_or_else(|| "no attempt was made".to_string());
            // DR-71 ①: no readiness, no route.  The old record must not survive
            // as a stand-in for the game this call just replaced.
            tools.clear_game_endpoint().await;
            anyhow::bail!(
                "the game the role started with `editor_play_scene` did not answer \
                 `running_game_get_scene_tree` after {} poll(s): {problem}",
                ready.attempts
            );
        }

        if let Err(error) = tools.publish_game_endpoint().await {
            tools.clear_game_endpoint().await;
            return Err(error.context(
                "the role-started game is ready but its route could not be published, so no later \
                 process could reach it; the previous route must not stand in for this one (DR-43)",
            ));
        }
        Ok(Some(record))
    }

    async fn build_check(
        &self,
        _workspace: &Path,
        tools: &dyn ToolChannel,
    ) -> anyhow::Result<Vec<ExecRecord>> {
        let mut records = Vec::new();

        // 1. editor_rescan_project_filesystem is executed by the runtime because the Tester is
        //    not allowed to call it; the result is informational only.
        let _ = tools
            .call(
                Role::Developer,
                "editor_rescan_project_filesystem",
                serde_json::json!({}),
            )
            .await;

        // 2. Editor errors.  DR-5: decide on the parsed `errors` array, never
        //    on a substring heuristic — an observation may legally contain the
        //    word "error" while the editor is clean, and vice versa.
        let errors = tools
            .call(Role::Tester, "editor_get_errors", serde_json::json!({}))
            .await;
        let observation = match errors {
            Ok(result) => describe_editor_errors(&result.payload),
            Err(error) => format!("editor_get_errors failed: {error}"),
        };
        records.push(ExecRecord {
            kind: ExecKind::Build,
            path: None,
            observation,
            candidate_id: String::new(),
        });

        // 3. Boot the main scene, snapshot the tree, then stop it.
        let play_args = serde_json::json!({"scene_path": self.config.main_scene});
        let play = tools
            .call(Role::Tester, "editor_play_scene", play_args)
            .await;
        let boot_observation = match play {
            Ok(_) => {
                let tree = tools
                    .call(
                        Role::Tester,
                        "running_game_get_scene_tree",
                        serde_json::json!({}),
                    )
                    .await;
                let _ = tools
                    .call(Role::Tester, "editor_stop_scene", serde_json::json!({}))
                    .await;
                match tree {
                    Ok(result) => format!("main scene booted; scene tree: {}", result.payload),
                    Err(error) => {
                        format!("main scene booted but running_game_get_scene_tree failed: {error}")
                    }
                }
            }
            Err(error) => format!("editor_play_scene failed: {error}"),
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
        // DR-66 ①: the playbook is executed by the Tester, whose real shell is
        // mini's `LocalEnvironment` shell.  The body names every harness path
        // through a `{{HOH_*}}` placeholder and the flavor is applied once, at
        // the end, so the delivered text can never spell the wrong dialect.
        let body = r#"# Evidence playbook (Godot)

The runtime already ran the deterministic battery. Start by reading
`.hoh/deterministic/battery.json`: each entry names the PRD requirements it
`supports`, its observation and whether it is usable (`ok`). The verbatim
payloads are in `.hoh/deterministic/raw/<step>.json`.

Reference every artifact by a **relative** path (`.hoh/deterministic/...` or
`.hoh/evidence/...`). A step with `ok = false` is `UNAVAILABLE`: the claims it
supports must be `gap`.

`input_channel_probe` and `input_replay` are about the **game process**. Judge
them from the game-process readings only (`channel = game_process`). Anything
labelled `EDITOR_SIDE_INJECTION` comes from the editor process, which cannot
reach the running game, and is recorded for completeness rather than as
evidence. `ACTION_BINDING_UNKNOWN` means the channel could not be read: record a
gap, and never write it up as "the action is missing" — that false conclusion
already sent one round off to fix a defect that did not exist.

Every `raw/<step>.json` starts with the JSON-RPC identity of the call its
payload belongs to: `request_id`, `response_id` and `sync_probes`. A payload
whose response carried another request's id is stored under that id and is
**never** used as this step's result; a non-empty `mismatched_ids` lists what
arrived for someone else. When `.hoh/deterministic/mcp-sync.json` reports
`"desynced": true`, the endpoint answered with foreign ids and
`result.json.warnings` carries `mcp_desync_detected`.

## Battery steps and what they can support
| step_id | supports | what it shows |
|---|---|---|
| `project_reload_and_open` | N1 | the editor was reloaded and the main scene opened (on-disk truth) |
| `scene_structure` | N1, F5, F6 | the `.tscn` text has exactly one root node and resolvable `parent=` paths |
| `editor_errors_baseline` | N1, N3 | the editor opens the project with no script errors |
| `play_scene_ready` | N1 | `editor_play_scene` succeeded and the game answered `running_game_get_scene_tree` **with a scene tree** (a reply of another shape is not readiness evidence) |
| `scene_tree` | N2, F5 | the running node tree exists, with a `path` and a `type` on every node |
| `screenshot` | N2, F4, F13, F16 | a PNG really exists under `.hoh/evidence/` (a reported path alone is not evidence) |
| `input_channel_probe` | F1, F2 (+P3 when a semantic tool really reports no such action) | the **game process** answered the contract's semantic tools (`running_game_get_node_properties`, `running_game_get_node_property_samples`, `running_game_create_input_recording` + `running_game_play_input_recording`, `running_game_run_test_scenario`) and reports `GAME_INPUT_CHANNEL_OK`, `ACTION_NOT_BOUND` or `ACTION_BINDING_UNKNOWN`. The raw payload is `.hoh/deterministic/raw/input_channel_probe.json`; its `channel` object carries every reading verbatim, and the one remaining `running_game_execute_gdscript` call is a **read-only** position probe that never decides the verdict (DR-54) |
| `input_replay` | F1, F2, F3 (+P3 when an InputMap action is missing) | `move_right`/`jump`/`move_left` recordings of `Player.position`, sampled **inside the game process** (`running_game_get_node_property_samples`, game-forwarded) after the action was injected through the semantic input API (`running_game_create_input_recording` + `running_game_play_input_recording` + `running_game_run_test_scenario`). Each call in `raw/input_replay.json` carries the `(action, channel, before_position, after_position, velocity)` quadruple. The editor-side `editor_simulate_input_action` is recorded for completeness only and is labelled `EDITOR_SIDE_INJECTION`: the editor is a different process and cannot drive the game. `INPUT_HAD_NO_EFFECT` means the action was delivered inside the game and the position did not change; `ACTION_NOT_BOUND` means a semantic tool answered that the game's InputMap has no such action; `ACTION_BINDING_UNKNOWN` means the channel could not be read and must **not** be read as a missing action. **DR-69 ④**: E3's evidence form (`REQUIREMENTS.md:114`) needs before/after frames and a node-state assertion, so each window also captures `.hoh/evidence/replay-<action>-before.png` and `-after.png` (`running_game_capture_screenshot`, inline form, labelled `<action>:replay_frame_before` / `_after`) and asserts `Player.position != <first sample>` with the engine's own `running_game_assert_node_state` (`property: position`, `operator: neq`, labelled `<action>:replay_assert_moved`). The assertion is **positional on purpose**: `input_axis` answers `null` on real hardware (DR-58) and the ~14-frame injection/sampling lag makes a total-displacement assertion untrustworthy, so the expectation is the window's own first sample. `POSITION_UNCHANGED` / `POSITION_ASSERTION_UNAVAILABLE` / `REPLAY_FRAME_MISSING` are the three honest failures of that form |
| `interaction_evidence` | F10, F13 (and F11/F12 structurally) | **DR-73 ③**: E3 names **four** behaviours, and until this step the battery observed two — `smoke-t10` ended with `Coins: 0` for the whole round and `Goal.reached` never true while the evidence handed to the Tester could not say so. The window enumerates the `Label`s under `HUD` from the scene tree's `name`/`path` (**the tree itself carries no text** — DR-76 ①) and reads each candidate's `text` through `running_game_get_node_properties`, keeping the one whose text starts with `Coins:`; it reads the goal node's `reached` flag, captures `.hoh/evidence/replay-interaction-{before,after}.png`, holds `move_right` for up to `INTERACTION_MAX_BATCHES` one-second batches of `running_game_get_node_property_samples` — the specification's 120 s maximum traversal (F17) plus margin, DR-76 ② — (stopping as soon as the win is observed), and then asserts both closures **with the engine's own `running_game_assert_node_state`**: `text:neq <before reading>` on the counter and `reached:neq false` on the goal. `COIN_PICKED_UP` / `WIN_DRIVEN` are the greens; `COIN_NOT_PICKED_UP` (the counter never moved), `WIN_NOT_DRIVEN` split into the two diagnoses it has to keep apart — `WIN_UNREACHED_WITHIN_BUDGET` (the window's own budget ran out: a coverage verdict that claims nothing about the level) and `WIN_BLOCKED_UNDER_MOVE_RIGHT` (DR-77 ③ — the player stopped advancing with budget unspent **while the window held `move_right`, the only action it ever sends**; the name it had until then, `WIN_UNREACHABLE_GEOMETRICALLY`, promised a proof about the level that this window cannot make, because it never jumps) — with the record carrying `player max x`, `goal.position` and `coverage_shortfall_px`; `COIN_COUNTER_UNREADABLE` (no `Coins:` label) and `GOAL_FLAG_NOT_FALSE_BEFORE` (the flag was already true, so the drive cannot be credited) are the honest failures. The window never writes a property: it drives input and reads state, which is what makes "the game drove its own win branch" a reading rather than a wish. **It is a game-process window**, judged exactly like `input_replay` above |
| `node_and_collision_assertions` | F5, F6, F10, F13, F14, F16 | node properties, `shape_count` per body, HUD text nodes |
| `editor_stop_scene` | N1 | the game stopped cleanly |

## If you need a closer look (read-only / execution only)
```
{{HOH_HOH_BIN}} tools call running_game_get_node_properties --args-file {{HOH_ARTIFACT_DIR}}/args/props.json
# props.json: {"node_path":"Player","properties":["position"]}
{{HOH_HOH_BIN}} tools call running_game_get_node_property_samples --args-file {{HOH_ARTIFACT_DIR}}/args/monitor.json
# monitor.json: {"node_path":"Player","properties":["position"],"frame_count":60,"frame_interval":1}
{{HOH_HOH_BIN}} tools call running_game_create_input_recording --args '{}'
{{HOH_HOH_BIN}} tools call running_game_play_input_recording --args-file {{HOH_ARTIFACT_DIR}}/args/play.json
# play.json: {"events":[{"type":"action","action":"move_right","pressed":true}],"speed":1.0}
{{HOH_HOH_BIN}} tools call running_game_run_test_scenario --args-file {{HOH_ARTIFACT_DIR}}/args/scenario.json
# scenario.json: {"steps":[{"type":"input","action":"move_right","pressed":true},
#                          {"type":"wait","seconds":0.5},
#                          {"type":"assert","node_path":"Player","property":"position:x","operator":"gt","expected":0}]}
# DR-58: never send `scene_path` — the game-scope runner answers -32602 for every
# value (it runs inside the already-running game); the member list is `steps` only.
{{HOH_HOH_BIN}} tools call running_game_stop_input_recording --args '{}'
{{HOH_HOH_BIN}} tools call editor_simulate_input_action --args-file {{HOH_ARTIFACT_DIR}}/args/press.json
# press.json: {"action":"move_right","pressed":true}
{{HOH_HOH_BIN}} tools call editor_simulate_input_sequence --args-file {{HOH_ARTIFACT_DIR}}/args/seq.json
# seq.json: {"events":[{"type":"action","action":"jump","pressed":true},
#                      {"type":"action","action":"jump","pressed":false}],"frame_delay":1}
{{HOH_HOH_BIN}} tools call running_game_capture_frames --args-file {{HOH_ARTIFACT_DIR}}/args/frames.json
# frames.json: {"count":1,"frame_interval":10}; frames land under `.hoh/evidence/`
{{HOH_HOH_BIN}} tools call editor_get_collision_info --args-file {{HOH_ARTIFACT_DIR}}/args/col.json
# col.json: {"node_path":"Goal"}
{{HOH_HOH_BIN}} tools call running_game_assert_node_state --args-file {{HOH_ARTIFACT_DIR}}/args/assert.json
# assert.json: {"node_path":"Player","property":"position:x","operator":"gt","expected":0}
```

## Rules
- One `execution_records` entry per observation, with the verbatim output.
- A claim is `verified` only if the cited record visibly shows the behaviour.
- Anything you could not observe is a `gap` with `player_impact` and
  `recommended_update`.
- Never modify the project: use `simulate_*` inputs only.
"#;
        crate::runtime::shell::render_command_vars(body, crate::runtime::shell::ShellFlavor::HOST)
    }

    /// DR-44: the binary the operator configured, or `None` when the key is
    /// absent/empty (the engine identity then records `null` + a reason).
    fn engine_binary(&self) -> Option<std::path::PathBuf> {
        crate::adapter::engine::configured_binary_path(&self.config.editor_binary)
    }

    fn engine_kind(&self) -> &'static str {
        crate::adapter::engine::ENGINE_KIND_GODOT
    }

    fn tool_policy(&self, role: Role) -> Vec<String> {
        // The authoritative filter is the role matrix in the tool channel; this
        // list only documents the intent for `TOOLS.md` consumers.
        match role {
            Role::Planner => Vec::new(),
            Role::Developer => vec!["*".to_string()],
            // DR-42: the four-channel contract's read verbs plus the evidence
            // ring tools the QA role is allowed to drive (§5.4).
            Role::Tester => vec![
                "editor_get_*".to_string(),
                "editor_list_*".to_string(),
                "editor_find_*".to_string(),
                "editor_analyze_*".to_string(),
                "editor_assert_*".to_string(),
                "editor_simulate_*".to_string(),
                "editor_capture_*".to_string(),
                "editor_play_scene".to_string(),
                "editor_stop_scene".to_string(),
                "project_get_*".to_string(),
                "project_list_*".to_string(),
                "project_read_*".to_string(),
                "project_search_*".to_string(),
                "project_find_*".to_string(),
                "project_analyze_*".to_string(),
                "project_detect_*".to_string(),
                "running_game_get_*".to_string(),
                "running_game_find_*".to_string(),
                "running_game_capture_*".to_string(),
                "running_game_assert_*".to_string(),
                "running_game_run_*".to_string(),
                "running_game_simulate_*".to_string(),
                "running_game_create_input_recording".to_string(),
                "running_game_stop_input_recording".to_string(),
                "running_game_play_input_recording".to_string(),
                "running_game_move_player_to_target".to_string(),
                "os_list_*".to_string(),
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
        // DR-41: the retired GDExtension channel must not come back.  The item
        // is reported so a legacy `A0` that still carries it is visible in
        // `hoh doctor` instead of silently double-binding port 9877.
        let addon = workspace.join(BUNDLED_ADDON_DIR);
        items.push(DoctorItem {
            name: "godot.bundled_addon".to_string(),
            ok: !addon.exists(),
            detail: format!(
                "{} must not exist: the MCP channel is the engine's native module (DR-41)",
                addon.display()
            ),
        });
        let cache = workspace.join(EXTENSION_LIST_CACHE);
        let stale_cache = std::fs::read_to_string(&cache)
            .map(|text| text.contains(BUNDLED_ADDON_EXTENSION))
            .unwrap_or(false);
        items.push(DoctorItem {
            name: "godot.extension_cache".to_string(),
            ok: !stale_cache,
            detail: format!(
                "{} must not reference {BUNDLED_ADDON_EXTENSION} (DR-41)",
                cache.display()
            ),
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

/// DR-48: the engine's own informational `[MCP]` startup banners, **verbatim**.
///
/// They are byte-identical to the engine's literals in this checkout
/// (`godot-mcp/godot/modules/mcp_server/mcp_server.cpp:605` and `:645`) and to
/// the lines the `smoke-t6` round's log carried.  They exist as **data** so the
/// exemption is one auditable list with one matcher, never a scattering of
/// special-case `if`s.
///
/// Why they arrive as "errors" at all: the engine classifies an editor log line
/// as an error with a case-insensitive `contains("ERROR")`
/// (`tools/editor_read_scene_inspector.cpp:249`), and the capture banner
/// contains `on_error`.  The banner is information, not a defect.
pub const ENGINE_INFO_BANNERS: &[&str] = &[
    "[MCP] trace=off (default; use --mcp-trace=<path> or godot_mcp/trace_file to enable)",
    "[MCP] capture=off (default; use --mcp-capture=on_error|every_call together with --mcp-trace=<path>)",
];

/// DR-48: is this editor log line one of the engine's informational banners?
///
/// The match is **exact** (after trimming the line): the banners are fixed
/// literals with no variable component, so anything else — including a genuine
/// `ERROR: [MCP] SceneTree never became available; MCP server disabled.`, which
/// the engine also prints — is **not** exempt and keeps the original
/// "the editor is not clean" verdict (fail closed).
///
/// A `[MCP]` **prefix** test is deliberately forbidden here: the engine prints
/// real errors under that prefix.
pub fn is_engine_info_banner(line: &str) -> bool {
    let line = line.trim();
    ENGINE_INFO_BANNERS.contains(&line)
}

/// DR-48: the reported lines that are **not** engine info banners.
///
/// A non-string entry, an unknown line and any real error are all kept, so the
/// gate stays conservative: only an exactly known banner is ignored.
pub fn non_banner_editor_errors(errors: &[serde_json::Value]) -> Vec<&serde_json::Value> {
    errors
        .iter()
        .filter(|line| !line.as_str().map(is_engine_info_banner).unwrap_or(false))
        .collect()
}

/// DR-68 ②: the `res://<path>:<line>` a GDScript editor error points at.
///
/// The path is returned **relative** (as written, so `scripts/player.gd`), which
/// is what [`crate::adapter::godot`]'s workspace joins need.
fn res_source_position(line: &str) -> Option<(String, usize)> {
    let rest = line.split("res://").nth(1)?;
    let colon = rest.find(':')?;
    let (path, after) = rest.split_at(colon);
    let digits: String = after[1..]
        .chars()
        .take_while(|character| character.is_ascii_digit())
        .collect();
    if path.is_empty() || digits.is_empty() {
        return None;
    }
    Some((path.to_string(), digits.parse().ok()?))
}

/// DR-68 ②: the symbol a `Function "name()"` parse error names, without `()`.
fn quoted_function_name(line: &str) -> Option<String> {
    let start = line.find("Function \"")? + "Function \"".len();
    let rest = &line[start..];
    let end = rest.find('"')?;
    let symbol = rest[..end].trim_end_matches("()").trim();
    if symbol.is_empty() {
        None
    } else {
        Some(symbol.to_string())
    }
}

/// DR-68 ②: is this editor-log error line **stale** — i.e. can the project on
/// disk no longer produce it?
///
/// The mechanism this closes: `editor_get_errors` reads the editor's append-only
/// **log**, not the current project.  `smoke-t8` read
/// `ERROR: res://scripts/player.gd:31 - Parse Error: Function
/// "_update_facing_visual()" not found in base self.` at 07:19:33, twelve
/// minutes after `player.gd` had been rewritten to call
/// `_apply_facing_visual()`; the gate closed, DR-24 spent 60 steps / 4.02M
/// tokens / 11m24s on a repair, and that repair wrote nothing.
///
/// The rule is deliberately **narrow and fail-closed**: it returns `true` only
/// for the exact shape the real round produced — a `res://<file>:<line>` that
/// exists, a `Function "…()"` symbol, and a current line 31 that does **not**
/// mention that symbol.  Everything else (an unparseable line, a missing file, a
/// line number out of range, another message shape) is **kept**, because "I
/// cannot interpret this" must never read as "this is fine".
///
/// Why the symbol test is the right freshness probe: a *genuine* current
/// `Function "X()" not found in base self.` means the file calls `X()` at that
/// position — so the symbol **is** on the line.  Only a line that has since been
/// rewritten to something else fails the test.
pub fn editor_error_is_stale(line: &str, workspace: &Path) -> bool {
    let Some((relative, number)) = res_source_position(line) else {
        return false;
    };
    let Some(symbol) = quoted_function_name(line) else {
        return false;
    };
    let Ok(text) = std::fs::read_to_string(workspace.join(&relative)) else {
        // Cannot check it: keep it (fail closed).
        return false;
    };
    let Some(current) = text.lines().nth(number.saturating_sub(1)) else {
        // The file is shorter than the log claims: cannot check it, keep it.
        return false;
    };
    !current.contains(&symbol)
}

/// DR-68 ②: split the reported editor lines into `(still reproducible, stale)`.
///
/// Used by the `editor_errors_baseline` gate step, so a log line that no longer
/// describes the project cannot close the gate **or** trigger the one allowed
/// repair.
pub fn partition_editor_errors<'a>(
    reported: &[&'a serde_json::Value],
    workspace: &Path,
) -> (Vec<&'a serde_json::Value>, Vec<&'a serde_json::Value>) {
    let mut fresh = Vec::new();
    let mut stale = Vec::new();
    for line in reported {
        match line.as_str() {
            Some(text) if editor_error_is_stale(text, workspace) => stale.push(*line),
            _ => fresh.push(*line),
        }
    }
    (fresh, stale)
}

/// DR-81 ①: the editor's **own cache namespace**.
///
/// Every cache file Godot writes for a project lives under `res://.godot/`, and
/// the runtime already excludes `.godot` from hashing, from snapshots and from
/// every view (DR-11) — nothing under it is part of the produced project.  A log
/// line that names a path here and reports an I/O failure is the editor failing
/// to maintain its own bookkeeping, not the project failing to build.
pub const EDITOR_CACHE_NAMESPACE: &str = "res://.godot/";

/// DR-81 ①: the **verbatim** failure wordings the editor uses when a write of its
/// own cache file fails.
///
/// `smoke-t14`'s line is `ERROR: Cannot create file
/// 'res://.godot/editor/filesystem_cache10'. Check user write permissions.`
/// (`--fresh-workspace` had just removed the `.godot` tree the running editor had
/// open).  The phrases are matched case-insensitively and only **together with
/// [`EDITOR_CACHE_NAMESPACE`]**, so the exemption is a named classification of an
/// editor-infrastructure failure, never a namespace wildcard: a real
/// `res://scripts/main.gd:8 - Parse Error` carries none of them.
pub const EDITOR_INFRASTRUCTURE_ERROR_PHRASES: &[&str] = &[
    "cannot create file",
    "cannot open file",
    "can't open file",
    "error opening file",
    "failed to write",
    "check user write permissions",
];

/// DR-81 ①: is this editor-log line the editor's **own infrastructure** failing?
///
/// The rule is deliberately **narrow and additive**: it is true only when the
/// line names the editor's cache namespace *and* carries one of the named
/// failure wordings.  Everything else — including every script/compile error —
/// keeps the original fail-closed verdict, which is what `smoke-t14` pass 1
/// (`res://scripts/main.gd:8 - Parse Error`) requires.
pub fn editor_error_is_infrastructure(line: &str) -> bool {
    let lower = line.to_ascii_lowercase();
    lower.contains(EDITOR_CACHE_NAMESPACE)
        && EDITOR_INFRASTRUCTURE_ERROR_PHRASES
            .iter()
            .any(|phrase| lower.contains(phrase))
}

/// DR-81 ①: split fresh editor errors into `(editor infrastructure, project)`.
///
/// A non-string entry is never infrastructure: it cannot be classified, so it
/// stays on the project side (fail closed).
pub fn partition_editor_infrastructure<'a>(
    lines: &[&'a serde_json::Value],
) -> (Vec<&'a serde_json::Value>, Vec<&'a serde_json::Value>) {
    lines.iter().partition(|line| {
        line.as_str()
            .map(editor_error_is_infrastructure)
            .unwrap_or(false)
    })
}

/// DR-81 ②: the `max_lines` window of the **anchor** reading.
///
/// The anchor asks for the whole tail (the engine answers everything when the
/// window is larger than the log), because it must contain every line the judged
/// reading can possibly contain.
pub const EDITOR_ERROR_ANCHOR_MAX_LINES: u64 = 2000;

/// DR-81 ②: the criterion the window implements, recorded verbatim in the raw
/// payload next to the evidence.
pub const EDITOR_ERROR_WINDOW_CRITERION: &str =
    "an editor log line closes the gate only when it is not an exact DR-48 engine \
     banner, not stale by DR-68, not editor infrastructure by DR-81 ①, and its number of \
     occurrences grew between the pre-reload anchor reading and the judged reading";

/// DR-81 ②: split the project-side lines into `(new in this window, pre-existing)`.
///
/// `smoke-t14` measured why a raw log-tail reading cannot be a hard verdict: the
/// editor's log is append-only, so a line that was already there before the
/// round's window describes an older state.  The window is anchored by an
/// `editor_get_errors` reading taken **before** `project_reload_and_open` — the
/// reload is what makes the editor surface the current on-disk project — and a
/// judged line is new only when its **occurrence count** exceeds the anchor's.
///
/// Counting rather than set membership is load-bearing: a second occurrence of an
/// identical line means the reload really re-produced it, and only the occurrence
/// that is *not* in the anchor closes the gate.
///
/// `None` (the anchor could not be taken, or was not an editor report) is
/// **fail-closed**: every line counts as new.
pub fn partition_editor_errors_in_window<'a>(
    anchor: Option<&[String]>,
    judged: &[&'a serde_json::Value],
) -> (Vec<&'a serde_json::Value>, Vec<&'a serde_json::Value>) {
    let Some(anchor) = anchor else {
        return (judged.to_vec(), Vec::new());
    };
    let mut remaining: Vec<&str> = anchor.iter().map(String::as_str).collect();
    let mut new = Vec::new();
    let mut pre_existing = Vec::new();
    for line in judged {
        match line.as_str() {
            Some(text) => match remaining.iter().position(|candidate| *candidate == text) {
                Some(index) => {
                    remaining.swap_remove(index);
                    pre_existing.push(*line);
                }
                None => new.push(*line),
            },
            // A non-string entry cannot be compared with the anchor: keep it.
            None => new.push(*line),
        }
    }
    (new, pre_existing)
}

/// DR-81 ①/②: the outcome of judging one `editor_get_errors` reading.
struct EditorErrorVerdict {
    ok: bool,
    observation: String,
    banners: usize,
    stale: usize,
    infrastructure: usize,
    new_defects: usize,
    pre_existing: usize,
}

/// DR-81 ①/②: judge an `editor_get_errors` reading.
///
/// The order is the whole decision, and each stage is documented where it is
/// defined: exact DR-48 banners are information; DR-68 removes lines the project
/// on disk can no longer produce; DR-81 ① removes the editor's own
/// infrastructure failures; DR-81 ② keeps only lines whose occurrence count grew
/// since the pre-reload anchor.  Whatever is left is the project defect.
fn judge_editor_errors(
    parsed: &serde_json::Value,
    errors: &[serde_json::Value],
    workspace: &Path,
    anchor: Option<&[String]>,
) -> EditorErrorVerdict {
    let base = describe_editor_errors(parsed);
    let reported = non_banner_editor_errors(errors);
    let banners = errors.len().saturating_sub(reported.len());
    let (fresh, stale) = partition_editor_errors(&reported, workspace);
    let (infrastructure, project) = partition_editor_infrastructure(&fresh);
    let (new_defects, pre_existing) = partition_editor_errors_in_window(anchor, &project);

    let exemptions = format!(
        "{} engine banner(s) by DR-48, {} stale line(s) by DR-68, {} editor-infrastructure \
         line(s) by DR-81 ①, {} pre-existing line(s) before the window anchor by DR-81 ②",
        banners,
        stale.len(),
        infrastructure.len(),
        pre_existing.len()
    );
    let window = format!(
        "window anchored with max_lines={EDITOR_ERROR_ANCHOR_MAX_LINES} before \
         `project_reload_and_open`, judged with max_lines=50 after it; \
         editor_infrastructure_failures={}, project_defects_new={}",
        infrastructure.len(),
        new_defects.len()
    );
    let (ok, observation) = if new_defects.is_empty() {
        (
            true,
            format!("{base} (no line closes the gate: {exemptions}; {window})"),
        )
    } else {
        (
            false,
            format!(
                "{base} (UNAVAILABLE: the editor is not clean; {} line(s) reproducible and new \
                 in this window; {exemptions}; {window})",
                new_defects.len()
            ),
        )
    };
    EditorErrorVerdict {
        ok,
        observation,
        banners,
        stale: stale.len(),
        infrastructure: infrastructure.len(),
        new_defects: new_defects.len(),
        pre_existing: pre_existing.len(),
    }
}

/// DR-5: turn a `editor_get_errors` payload into an observation.
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
            "the editor_get_errors payload could not be parsed as JSON (treated as errors):\n{rendered}"
        ),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::tools::ToolResult;
    use serde_json::Value;

    fn adapter(_addon: &Path) -> GodotAdapter {
        GodotAdapter::new(
            GodotConfig {
                editor_binary: std::path::PathBuf::new(),
                cache_excludes: vec![".godot".to_string(), ".import".to_string()],
                main_scene: "res://scenes/main.tscn".to_string(),
            },
            false,
        )
    }

    /// Minimal MCP stand-in: `editor_get_errors` returns a canned payload.
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
                "editor_get_errors" => self.errors.clone(),
                "editor_play_scene" => serde_json::json!({"ok": true}),
                "running_game_get_scene_tree" => serde_json::json!({"tree": []}),
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
        // DR-41: the MCP channel is the engine's native module (C4); the
        // retired GDExtension addon must never be copied into `A0` again.
        assert!(
            !workspace.join("addons/godot_mcp_rs/plugin.cfg").exists(),
            "the bundled GDExtension addon must not be installed (DR-41)"
        );
        assert!(
            !workspace.join("ADDON_MISSING.txt").exists(),
            "there is no addon to miss any more (DR-41)"
        );
    }

    /// DR-41: the project template must not name the retired plugin channel and
    /// must declare the 4.8 engine generation.
    #[test]
    fn the_project_template_drops_the_gdextension_channel() {
        assert!(
            !PROJECT_GODOT.contains("[editor_plugins]"),
            "the template must not enable an editor plugin (DR-41)"
        );
        assert!(
            !PROJECT_GODOT.contains(MCP_PLUGIN_PATH),
            "the template must not name the retired plugin (DR-41)"
        );
        assert!(
            PROJECT_GODOT.contains("config/features=PackedStringArray(\"4.8\")"),
            "the template must declare the 4.8 engine generation (DR-41)"
        );
        assert!(
            !PROJECT_GODOT.contains("PackedStringArray(\"4.7\")"),
            "the 4.7 generation is gone (DR-41)"
        );
    }

    /// DR-41: an `A0` created by an earlier version still carries the retired
    /// channel in three places, and `initialize` must reverse all three
    /// **idempotently**: the second call must not change a single byte.
    #[test]
    fn initialize_removes_a_legacy_bundled_addon_idempotently() {
        let temp = tempfile::tempdir().unwrap();
        let workspace = temp.path().join("mario");
        std::fs::create_dir_all(workspace.join("addons/godot_mcp_rs")).unwrap();
        std::fs::write(
            workspace.join("addons/godot_mcp_rs/plugin.cfg"),
            "[plugin]\n",
        )
        .unwrap();
        std::fs::create_dir_all(workspace.join(".godot")).unwrap();
        std::fs::write(
            workspace.join(".godot/extension_list.cfg"),
            "res://addons/someone_else/other.gdextension\n\
             res://addons/godot_mcp_rs/godot_mcp_rs.gdextension\n",
        )
        .unwrap();
        std::fs::write(
            workspace.join("project.godot"),
            "config_version=5\n\n[editor_plugins]\n\n\
             enabled=PackedStringArray(\"res://addons/other/plugin.cfg\", \
             \"res://addons/godot_mcp_rs/plugin.cfg\")\n",
        )
        .unwrap();

        adapter(&temp.path().join("no-such-addon"))
            .initialize(&workspace)
            .unwrap();

        assert!(
            !workspace.join("addons/godot_mcp_rs").exists(),
            "the exact addon directory must be removed (DR-41)"
        );
        let cache = std::fs::read_to_string(workspace.join(".godot/extension_list.cfg")).unwrap();
        assert_eq!(
            cache, "res://addons/someone_else/other.gdextension\n",
            "every other cache line must survive byte-for-byte (DR-41)"
        );
        let project = std::fs::read_to_string(workspace.join("project.godot")).unwrap();
        assert_eq!(
            project,
            "config_version=5\n\n[editor_plugins]\n\n\
             enabled=PackedStringArray(\"res://addons/other/plugin.cfg\")\n",
            "the other enabled plugin must survive byte-for-byte (DR-41)"
        );

        // Idempotence: the cleanup must be satisfied on the second call.
        let before = (
            project.clone(),
            cache.clone(),
            std::fs::read(workspace.join(".godot/extension_list.cfg")).unwrap(),
        );
        adapter(&temp.path().join("no-such-addon"))
            .initialize(&workspace)
            .unwrap();
        assert_eq!(
            std::fs::read_to_string(workspace.join("project.godot")).unwrap(),
            before.0,
            "a second initialize must not touch project.godot (DR-41)"
        );
        assert_eq!(
            std::fs::read(workspace.join(".godot/extension_list.cfg")).unwrap(),
            before.2,
            "a second initialize must not touch the extension cache (DR-41)"
        );
    }

    /// DR-41: when the retired plugin is the *only* entry, the empty remains
    /// must be removed — the section from `project.godot` and the cache file
    /// itself — instead of being left as an empty husk.
    #[test]
    fn initialize_removes_empty_remains_of_the_retired_channel() {
        let temp = tempfile::tempdir().unwrap();
        let workspace = temp.path().join("mario");
        std::fs::create_dir_all(workspace.join(".godot")).unwrap();
        std::fs::write(
            workspace.join(".godot/extension_list.cfg"),
            "res://addons/godot_mcp_rs/godot_mcp_rs.gdextension\n",
        )
        .unwrap();
        std::fs::write(
            workspace.join("project.godot"),
            "config_version=5\n\n[application]\n\nconfig/name=\"x\"\n\n[editor_plugins]\n\n\
             enabled=PackedStringArray(\"res://addons/godot_mcp_rs/plugin.cfg\")\n",
        )
        .unwrap();

        adapter(&temp.path().join("no-such-addon"))
            .initialize(&workspace)
            .unwrap();

        let project = std::fs::read_to_string(workspace.join("project.godot")).unwrap();
        assert!(
            !project.contains(EDITOR_PLUGINS_HEADER),
            "an empty `[editor_plugins]` section must go entirely (DR-41): {project:?}"
        );
        assert!(project.contains("config/name=\"x\""), "{project:?}");
        assert!(
            !workspace.join(".godot/extension_list.cfg").exists(),
            "an emptied extension cache must be deleted (DR-41)"
        );

        let once = std::fs::read_to_string(workspace.join("project.godot")).unwrap();
        adapter(&temp.path().join("no-such-addon"))
            .initialize(&workspace)
            .unwrap();
        assert_eq!(
            once,
            std::fs::read_to_string(workspace.join("project.godot")).unwrap(),
            "the cleanup must be idempotent (DR-41)"
        );
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

    /// DR-41: a project that never carried the retired channel — or an enabled
    /// list that names other plugins only — must be left byte-for-byte alone.
    #[test]
    fn initialize_never_touches_a_project_without_the_retired_channel() {
        let temp = tempfile::tempdir().unwrap();
        let workspace = temp.path().join("mario");
        std::fs::create_dir_all(&workspace).unwrap();
        std::fs::write(
            workspace.join("project.godot"),
            "config_version=5\n\n[application]\n\nconfig/name=\"x\"\n\n[editor_plugins]\n\n\
             enabled=PackedStringArray(\"res://addons/other/plugin.cfg\")\n",
        )
        .unwrap();
        let before = std::fs::read(workspace.join("project.godot")).unwrap();

        adapter(&temp.path().join("no-such-addon"))
            .initialize(&workspace)
            .unwrap();

        assert_eq!(
            std::fs::read(workspace.join("project.godot")).unwrap(),
            before,
            "an unrelated project must be byte-identical afterwards (DR-41)"
        );
        assert!(!workspace.join(".godot").exists());
        assert!(!workspace.join("addons").exists());
    }

    /// DR-53 (DEF-2): a **malformed** `enabled=` line — one that is not a
    /// `PackedStringArray(...)` at all — must not modify the file.
    ///
    /// The pre-DR-53 parser returned `None` for a line without parentheses, and
    /// `None` meant "the list became empty"; so `enabled=true` deleted the whole
    /// `[editor_plugins]` section.  Parsing failure is now its own outcome with
    /// a reason, and the file stays byte-identical.
    #[test]
    fn a_malformed_enabled_line_leaves_the_project_untouched() {
        let temp = tempfile::tempdir().unwrap();
        let workspace = temp.path().join("mario");
        std::fs::create_dir_all(&workspace).unwrap();
        let text = "config_version=5\n\n[application]\n\nconfig/name=\"x\"\n\n[editor_plugins]\n\n\
                    enabled=true\n";
        std::fs::write(workspace.join("project.godot"), text).unwrap();

        let outcome = ensure_bundled_addon_disabled(&workspace.join("project.godot")).unwrap();
        assert!(
            !outcome.changed(),
            "a file it cannot parse must never be rewritten (DR-53): {outcome:?}"
        );
        let reason = outcome.reason().unwrap_or_default();
        assert!(
            reason.contains("PackedStringArray"),
            "the reason must name what it could not read: {reason}"
        );
        assert!(reason.contains("enabled"), "{reason}");
        assert_eq!(
            std::fs::read_to_string(workspace.join("project.godot")).unwrap(),
            text,
            "the file must be byte-identical (DR-53)"
        );

        // The same through the public entry point.
        adapter(&temp.path().join("no-such-addon"))
            .initialize(&workspace)
            .unwrap();
        assert_eq!(
            std::fs::read_to_string(workspace.join("project.godot")).unwrap(),
            text,
            "`initialize` must not modify it either (DR-53)"
        );
    }

    /// DR-53 (DEF-2): the three parse outcomes, and the fourth that refuses to
    /// guess.
    #[test]
    fn the_enabled_line_edit_distinguishes_absent_updated_emptied_and_malformed() {
        let entry = MCP_PLUGIN_PATH;
        // The entry is not in the list: the caller must not write.
        assert_eq!(
            packed_string_array_without(
                &format!(
                    "enabled=PackedStringArray(\"{}\")",
                    "res://addons/other/plugin.cfg"
                ),
                entry
            ),
            PackedArrayEdit::Absent
        );
        // The entry is one of several: only it goes.
        assert_eq!(
            packed_string_array_without(
                &format!(
                    "enabled=PackedStringArray(\"{}\", \"{entry}\")",
                    "res://addons/other/plugin.cfg"
                ),
                entry
            ),
            PackedArrayEdit::Updated(format!(
                "enabled=PackedStringArray(\"{}\")",
                "res://addons/other/plugin.cfg"
            ))
        );
        // The entry was the only one: the line goes.
        assert_eq!(
            packed_string_array_without(&format!("enabled=PackedStringArray(\"{entry}\")"), entry),
            PackedArrayEdit::Emptied
        );
        // Malformed shapes are refused, never guessed at.
        for line in [
            "enabled=true",
            "enabled=",
            "enabled=PackedStringArray",
            "enabled=PackedStringArray)",
            "enabled=PackedStringArray()extra",
        ] {
            if line == "enabled=PackedStringArray()extra" {
                // `()extra` has no `)` *after* the `(`; it is malformed too.
                assert_eq!(
                    packed_string_array_without(line, entry),
                    PackedArrayEdit::Unrecognised,
                    "{line}"
                );
                continue;
            }
            assert_eq!(
                packed_string_array_without(line, entry),
                PackedArrayEdit::Unrecognised,
                "{line}"
            );
        }
        // `enabled=PackedStringArray()` (a legal empty list) is *not* malformed:
        // the retired entry is simply absent.
        assert_eq!(
            packed_string_array_without("enabled=PackedStringArray()", entry),
            PackedArrayEdit::Absent
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

    /// DR-48: the exemption is an **exact** banner list with one named matcher.
    ///
    /// The counterexamples matter more than the positive cases: the engine
    /// prints a real `ERROR: [MCP] …` line, so a `[MCP]`-prefix rule would be a
    /// silent regression of the gate.
    #[test]
    fn only_the_exact_engine_info_banners_are_exempt() {
        for banner in ENGINE_INFO_BANNERS {
            assert!(
                is_engine_info_banner(banner),
                "the engine's own banner must be exempt: {banner}"
            );
            // Trailing whitespace (a log line may end in `\r`) does not hide it.
            assert!(is_engine_info_banner(&format!("{banner}\r\n")));
        }

        for line in [
            // A real engine error that carries the `[MCP]` prefix — the trap
            // D221 names explicitly.
            "ERROR: [MCP] SceneTree never became available; MCP server disabled.",
            // A real GDScript/parse error.
            r#"SCRIPT ERROR: Parse Error: Unexpected identifier "using" in class body."#,
            r#"ERROR: res://scripts/main.gd:1 - Parse Error: Unexpected identifier "using" in class body."#,
            // The `[MCP]` prefix alone, a truncated banner, and an *unknown*
            // `[MCP]` line: none of them may be guessed at (fail closed).
            "[MCP] capture=off",
            "[MCP] capture=enabled: mode=every_call viewport=2d dir=/tmp diff_image=false scale=2",
            "[MCP] role=game configured_port=63698 source=cmdline listen=true",
            "[MCP] listening on 127.0.0.1:63698 (editor=false, tools=73)",
            "[MCP] SceneTree never became available; MCP server disabled.",
            "error",
            "",
        ] {
            assert!(
                !is_engine_info_banner(line),
                "this line must NOT be exempt (DR-48 fails closed): {line}"
            );
        }
    }

    /// DR-48: the classification keeps every line except an exact banner, and a
    /// payload that is *only* banners is clean.
    #[test]
    fn the_banner_filter_keeps_every_other_line() {
        let banner = ENGINE_INFO_BANNERS[1];
        let error = "ERROR: [MCP] SceneTree never became available; MCP server disabled.";
        let mixed = serde_json::json!([banner, error, 42, {"message": "x"}]);
        let reported = non_banner_editor_errors(mixed.as_array().unwrap());
        assert_eq!(
            reported.len(),
            3,
            "a real error, a non-string and an object all survive: {reported:?}"
        );
        assert!(reported.iter().any(|line| line.as_str() == Some(error)));

        let only_banners = serde_json::json!([ENGINE_INFO_BANNERS[0], banner]);
        assert!(
            non_banner_editor_errors(only_banners.as_array().unwrap()).is_empty(),
            "only the engine's own banners were reported"
        );
    }

    /// DR-68 ②: the staleness probe, against a real `player.gd` on disk.
    ///
    /// Positive: the log names `_update_facing_visual()` at line 31 while the
    /// current line 31 calls `_apply_facing_visual()` — the `smoke-t8` case.
    /// Negative (fail closed): a line the current bytes still reproduce, another
    /// message shape, a missing file, and a line number past the end of the file.
    #[test]
    fn a_log_line_is_stale_only_when_the_current_bytes_cannot_reproduce_it() {
        let temp = tempfile::tempdir().unwrap();
        let workspace = temp.path();
        std::fs::create_dir_all(workspace.join("scripts")).unwrap();
        let mut player = String::from("extends CharacterBody2D\n\n");
        while player.lines().count() < 30 {
            player.push_str("\tpass\n");
        }
        player.push_str("\t_apply_facing_visual()\n");
        assert_eq!(player.lines().count(), 31);
        std::fs::write(workspace.join("scripts/player.gd"), &player).unwrap();

        let stale = r#"ERROR: res://scripts/player.gd:31 - Parse Error: Function "_update_facing_visual()" not found in base self."#;
        assert!(
            editor_error_is_stale(stale, workspace),
            "the log quotes a symbol the current line 31 no longer has"
        );

        // The same line rewritten to call the missing symbol: a *current* error,
        // because a real `not found in base self` means the call is on the line.
        let mut current = player.clone();
        current.truncate(current.len() - "\t_apply_facing_visual()\n".len());
        current.push_str("\t_missing_from_this_file()\n");
        std::fs::write(workspace.join("scripts/player.gd"), &current).unwrap();
        let reproducible = r#"ERROR: res://scripts/player.gd:31 - Parse Error: Function "_missing_from_this_file()" not found in base self."#;
        assert!(
            !editor_error_is_stale(reproducible, workspace),
            "the current bytes still produce this complaint"
        );

        // Everything the probe cannot interpret is kept (fail closed).
        for kept in [
            // A real error with no `res://` position at all.
            "ERROR: [MCP] SceneTree never became available; MCP server disabled.",
            // Another message shape at the same position.
            r#"ERROR: res://scripts/player.gd:31 - Parse Error: Unexpected identifier "using" in class body."#,
            // A file that does not exist in the workspace.
            r#"ERROR: res://scripts/absent.gd:31 - Parse Error: Function "_x()" not found in base self."#,
            // A line number past the end of the file.
            r#"ERROR: res://scripts/player.gd:900 - Parse Error: Function "_x()" not found in base self."#,
        ] {
            assert!(
                !editor_error_is_stale(kept, workspace),
                "an uninterpretable line must never be dismissed: {kept}"
            );
        }

        // And the split keeps the reported order while classifying each line.
        let banner = ENGINE_INFO_BANNERS[0];
        let reported = serde_json::json!([current_line_error(), banner]);
        let (fresh, dismissed) = partition_editor_errors(
            &non_banner_editor_errors(reported.as_array().unwrap()),
            workspace,
        );
        assert_eq!(fresh.len(), 1, "the banner is filtered first: {fresh:?}");
        assert!(dismissed.is_empty());
    }

    fn current_line_error() -> serde_json::Value {
        serde_json::json!(
            r#"ERROR: res://scripts/player.gd:31 - Parse Error: Function "_missing_from_this_file()" not found in base self."#
        )
    }

    /// DR-52: the engine's `editor_get_input_actions` answers an array of action
    /// **names** (`{"actions": ["jump", "move_left", …], "count": 92}`); the
    /// retired addon answered objects.  Both must be read, and a payload whose
    /// shape is neither must stay `None` (never "no such action").
    #[test]
    fn the_input_action_list_is_read_from_the_engine_shape() {
        // The verbatim smoke-t6 shape (abbreviated to the first entries).
        let engine = json!({
            "actions": ["jump", "move_left", "move_right", "spatial_editor/freelook_up", "ui_accept"],
            "count": 5,
        });
        let bindings = parse_input_actions(&engine).expect("an `actions` array is a binding list");
        assert_eq!(bindings.len(), 5);
        for action in ["move_left", "move_right", "jump"] {
            assert!(bindings.contains_key(action), "{action}: {bindings:?}");
        }
        // The faithful reading is what removes the `smoke-t6` contradiction: an
        // empty map claimed the three actions were absent.
        assert!(!bindings.is_empty());

        // The addon-era object shape still works (name + keys).
        let addon = json!({"actions": [{"name": "jump", "keys": ["Space", "W"]}]});
        let bindings = parse_input_actions(&addon).expect("the object shape still parses");
        assert_eq!(bindings.get("jump").map(Vec::len), Some(2));

        // An object map is accepted as before.
        let mapped = json!({"actions": {"jump": ["Space"]}});
        let bindings = parse_input_actions(&mapped).expect("a map parses");
        assert_eq!(bindings.get("jump").map(Vec::len), Some(1));

        // A payload that is not a binding list at all is `None`, never `{}`.
        assert!(parse_input_actions(&json!({"count": 92})).is_none());
        assert!(parse_input_actions(&json!({"actions": 3})).is_none());
        assert!(parse_input_actions(&json!([])).is_none());
    }

    /// DR-50: `running_game_execute_gdscript` takes a GDScript **function body**,
    /// so a reading is `return <expr>` and a void mutation stays a statement.
    ///
    /// `smoke-t6`'s four transport-successful probe calls all answered
    /// `{"result":null,"result_type":"Nil"}`, because the scripts were bare
    /// expressions.  A regression here silently un-reads the whole game channel
    /// (the double in `tests/evidence_battery.rs` models the engine's Nil answer,
    /// so it also fails the end-to-end battery).
    #[test]
    fn the_game_probe_scripts_are_body_shaped() {
        for reading in [
            probe_scripts::has_action("move_right"),
            probe_scripts::is_action_pressed("move_right"),
            probe_scripts::axis(),
            probe_scripts::player_position(),
        ] {
            assert!(
                reading.trim_start().starts_with("return "),
                "a value-reading probe must `return` its reading: {reading}"
            );
        }
        for mutation in [
            probe_scripts::press("move_right"),
            probe_scripts::release("move_right"),
        ] {
            assert!(
                !mutation.trim_start().starts_with("return "),
                "`Input.action_press`/`action_release` return void: a `return` would not compile: \
                 {mutation}"
            );
            assert!(
                !mutation.contains("str("),
                "a void call may not be used as a value (`str(Input.action_press(...))` is a \
                 compile error, gdscript_analyzer.cpp:3498): {mutation}"
            );
        }
    }

    /// DR-49: freshness is a property of the artifact **state**, and a
    /// pre-existing file is invalidated rather than trusted.
    #[test]
    fn freshness_is_decided_on_the_artifact_state_not_on_existence() {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("frame-00.png");

        // Nothing before, nothing after: never fresh.
        assert!(!artifact_is_fresh(None, None));
        // Created by the call.
        std::fs::write(&path, b"one").unwrap();
        let first = artifact_fingerprint(&path).expect("fingerprint");
        assert!(artifact_is_fresh(None, Some(&first)));
        // Unchanged across the call: not this run's artifact.
        assert!(!artifact_is_fresh(Some(&first), Some(&first)));
        // Rewritten with different bytes: fresh.
        std::fs::write(&path, b"two").unwrap();
        let second = artifact_fingerprint(&path).expect("fingerprint");
        assert!(artifact_is_fresh(Some(&first), Some(&second)));
        // Deleted: never fresh, and no path may be claimed.
        std::fs::remove_file(&path).unwrap();
        assert!(!artifact_is_fresh(Some(&first), None));
        assert!(artifact_fingerprint(&path).is_none());
    }

    /// DR-49 ②: the pre-existing artifact is renamed out of the way, not left in
    /// place, and the operation is idempotent/`None` when there is nothing.
    #[test]
    fn invalidating_an_artifact_moves_it_aside() {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("frame-00.png");
        assert_eq!(invalidate_artifact(&path).unwrap(), None);

        std::fs::write(&path, b"2026-09-21 stale png").unwrap();
        let stale = invalidate_artifact(&path)
            .unwrap()
            .expect("a pre-existing file must be moved aside");
        assert!(stale.starts_with("frame-00.png.stale-"), "{stale}");
        assert!(
            !path.exists(),
            "the target must be empty for the duration of the call"
        );
        let moved = temp.path().join(&stale);
        assert_eq!(
            std::fs::read(&moved).unwrap(),
            b"2026-09-21 stale png",
            "the stale artifact stays auditable under its new name"
        );
        // DR-62: the move is mirrored by an explicit structural record in the
        // same directory — the criterion the view copies consult, and the only
        // one: the `.stale-<ts>` name itself now decides nothing.
        let recorded = crate::runtime::hygiene::SupersededSet::load(temp.path()).unwrap();
        assert!(
            recorded.contains(&stale),
            "DR-62: the supersession must be recorded in the manifest: {recorded:?}"
        );
        assert!(
            crate::runtime::hygiene::is_superseded(temp.path(), &stale).unwrap(),
            "DR-62: the recorded supersession must be discoverable from the tree root"
        );
        // A second invalidation has nothing left to do.
        assert_eq!(invalidate_artifact(&path).unwrap(), None);
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
            "editor_simulate_input_sequence",
            "running_game_capture_frames",
            "running_game_get_node_property_samples",
            "running_game_assert_node_state",
            ".hoh/evidence/",
        ] {
            assert!(playbook.contains(needle), "playbook is missing {needle}");
        }
    }

    /// DR-35: `smoke-t5`'s real defect was that the battery judged the game with
    /// editor-side tools.  The playbook must tell the Tester which process each
    /// record came from.
    #[test]
    fn playbook_explains_the_game_process_channel() {
        let temp = tempfile::tempdir().unwrap();
        let playbook = adapter(&temp.path().join("addon")).evidence_playbook();
        for needle in [
            "input_channel_probe",
            "game_process",
            "EDITOR_SIDE_INJECTION",
            "ACTION_BINDING_UNKNOWN",
            "ACTION_NOT_BOUND",
        ] {
            assert!(playbook.contains(needle), "playbook is missing {needle}");
        }
    }

    // -----------------------------------------------------------------------
    // DR-35: the game-process probe
    // -----------------------------------------------------------------------

    /// DR-50: the probe scripts are one-line GDScript **bodies**.
    ///
    /// The pre-DR-50 form was derived from the retired GDExtension addon, which
    /// evaluated a single `Expression` and stringified it (`str(...)`, no
    /// `return`).  The MCP-native engine compiles `code` into a function body
    /// instead (`running_game_script_execution.cpp:57-82`), so the reading half
    /// is `return str(...)` and the void mutation half is a plain statement.
    /// Every assertion the old test made about one-line-ness, the `get_tree()`
    /// reachability of the position read and the absence of engine singletons in
    /// it is kept; the obsolete `starts_with("str(")`/`!contains("return ")`
    /// pair is replaced by the body-shaped form.
    #[test]
    fn the_probe_scripts_are_single_line_bodies() {
        for script in [
            probe_scripts::has_action("move_right"),
            probe_scripts::is_action_pressed("move_right"),
            probe_scripts::axis(),
            probe_scripts::player_position(),
        ] {
            assert!(script.starts_with("return str("), "{script}");
            assert!(!script.contains('\n'), "a probe body is one line: {script}");
        }
        for script in [
            probe_scripts::press("move_right"),
            probe_scripts::release("move_right"),
        ] {
            assert!(script.starts_with("Input.action_"), "{script}");
            assert!(!script.contains('\n'), "a probe body is one line: {script}");
        }
        assert_eq!(
            probe_scripts::has_action("jump"),
            "return str(InputMap.has_action(\"jump\"))"
        );
        // The position read must stay reachable: it uses `get_tree()` on the
        // generated body's base node, never an engine singleton.
        let position = probe_scripts::player_position();
        assert!(position.contains("get_tree()"), "{position}");
        assert!(!position.contains("Engine"), "{position}");
    }

    /// The addon answers `{"result": str(value)}`; a raw boolean/number must keep
    /// working, and anything else must be `None` (never a guessed reading).
    #[test]
    fn the_game_script_readings_are_parsed_strictly() {
        let envelope = |text: &str| json!({"content": [{"type": "text", "text": text}]});
        assert_eq!(
            game_script_bool(&envelope(r#"{"result":"true"}"#)),
            Some(true)
        );
        assert_eq!(
            game_script_bool(&envelope(r#"{"result":"FALSE"}"#)),
            Some(false)
        );
        assert_eq!(
            game_script_bool(&envelope(r#"{"result":true}"#)),
            Some(true)
        );
        assert_eq!(game_script_bool(&envelope(r#"{"result":"maybe"}"#)), None);
        assert_eq!(game_script_f64(&envelope(r#"{"result":"1.0"}"#)), Some(1.0));
        assert_eq!(game_script_f64(&envelope(r#"{"result":0.5}"#)), Some(0.5));
        assert_eq!(
            game_script_f64(&envelope(r#"{"result":"-0.5"}"#)),
            Some(-0.5)
        );
        assert_eq!(game_script_f64(&envelope(r#"{"result":"<null>"}"#)), None);
        assert_eq!(
            game_script_position(&envelope(r#"{"result":"60.0,283.999"}"#)),
            Some((60.0, 283.999))
        );
        // The real `smoke-t5` failure shape carries no `result` at all.
        assert_eq!(game_script_bool(&envelope(r#"{"error":"Invalid"}"#)), None);
        assert_eq!(
            game_script_position(&envelope(r#"{"error":"Invalid"}"#)),
            None
        );
    }

    /// DR-35: `project.godot` is read only for the diagnosis — a declaration is
    /// not a running binding.
    #[test]
    fn project_declared_actions_reads_only_the_input_section() {
        let temp = tempfile::tempdir().unwrap();
        std::fs::write(
            temp.path().join("project.godot"),
            "config_version=5\n\n[move_right]\n\n[input]\nmove_left={\n}\n# move_right is a comment\n\
             move_right={\n}\n\n[rendering]\njump={}\n",
        )
        .unwrap();
        let declared = project_declared_actions(temp.path(), &["move_left", "move_right", "jump"]);
        assert_eq!(
            declared,
            vec!["move_left".to_string(), "move_right".to_string()],
            "jump is declared in another section, and a comment is not a declaration"
        );
        assert!(
            project_declared_actions(&temp.path().join("missing"), &["move_right"]).is_empty(),
            "a workspace without project.godot declares nothing"
        );
    }

    /// DR-35: the three capability codes are the literals a Tester searches for,
    /// and the default is the honest one (`UNKNOWN`, never `NOT_BOUND`).
    #[test]
    fn the_capability_codes_are_the_searchable_literals() {
        assert_eq!(
            InputChannelCapability::all_codes(),
            [
                "GAME_INPUT_CHANNEL_OK",
                "ACTION_NOT_BOUND",
                "ACTION_BINDING_UNKNOWN"
            ]
        );
        assert_eq!(
            InputChannelCapability::default().code(),
            "ACTION_BINDING_UNKNOWN"
        );
        assert!(
            InputChannelProbe::default()
                .observation()
                .starts_with("ACTION_BINDING_UNKNOWN"),
            "an empty probe is not evidence of anything"
        );
    }

    /// DR-35 ⑤: a quadruple always names the process it was observed in.
    #[test]
    fn the_quadruple_carries_its_channel() {
        let payload = json!({
            "frame_count": 2,
            "samples": [
                {"frame": 0, "position": {"x": 0.0, "y": 0.0}},
                {"frame": 1, "position": {"x": 8.0, "y": 0.0}},
            ],
        });
        let game = replay_quadruple("move_right", &payload, GAME_PROCESS_CHANNEL).unwrap();
        assert_eq!(game["channel"], json!(GAME_PROCESS_CHANNEL));
        assert_eq!(game["before_position"], json!({"x": 0.0, "y": 0.0}));
        assert_eq!(game["after_position"], json!({"x": 8.0, "y": 0.0}));

        let editor = replay_quadruple("move_right", &payload, EDITOR_PROCESS_CHANNEL).unwrap();
        assert_eq!(editor["channel"], json!(EDITOR_PROCESS_CHANNEL));
        assert_ne!(
            game["channel"], editor["channel"],
            "the two processes must stay distinguishable"
        );

        // No frame samples at all is still `None`, not a zeroed quadruple.
        assert!(replay_quadruple(
            "move_right",
            &json!({"frame_count": 0, "samples": []}),
            GAME_PROCESS_CHANNEL
        )
        .is_none());
    }
}
