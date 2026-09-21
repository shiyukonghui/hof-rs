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
use crate::tools::mcp::{RpcCorrelation, SessionSyncReport, PROBE_TOOL};
use crate::tools::reliable::{
    call_with_retries_traced, wait_for_game_ready, McpErrorLog, McpFailure, ReadyOutcome,
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

/// The scene text out of a `get_scene_file_content` payload, whatever shape the
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
        }
    }

    async fn call(&self, tool: &str, args: Value) -> Result<TracedCall, McpFailure> {
        // DR-24: the battery is the runtime's deterministic stage, not the
        // Tester.  It must be able to `reload_project`/`open_scene` (which the
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
        wait_for_game_ready(
            self.tools,
            Role::Developer,
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
        // DR-29: the correlation header comes first, so a reader can tell which
        // response belonged to which request before reading any payload.
        let header = rpc_header(&calls);
        let doc = json!({
            "step": step.id,
            "request_id": header["request_id"],
            "response_id": header["response_id"],
            "sync_probes": header["sync_probes"],
            "mismatched_ids": header["mismatched_ids"],
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
        // DR-24: the editor is forced onto the on-disk truth *before* anything
        // is asked about errors (smoke-t2 showed an in-memory scene that
        // disagreed with the `.tscn` on disk).
        self.step_project_reload_and_open().await?;
        self.step_scene_structure().await?;
        self.step_editor_errors().await?;
        let scene_tree = self.step_play_scene().await?;
        self.step_scene_tree(scene_tree.clone()).await?;
        self.step_screenshot().await?;
        self.step_input_replay().await?;
        self.step_node_assertions(scene_tree).await?;
        self.step_stop_scene().await?;
        Ok(self.records)
    }

    /// DR-24 (new 1). `reload_project` + `open_scene(<main>)`.
    ///
    /// Without this the editor keeps whatever scene it had in memory, so a
    /// scene that is legal on disk can still report stale errors — and the
    /// reverse, which is exactly how `play_scene` managed to lie in `smoke-t2`.
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
        match self.call("reload_project", reload_args.clone()).await {
            Ok(call) => calls.push(call_ok(
                "reload_project",
                &reload_args,
                &call.payload,
                &call.correlation,
            )),
            Err(failure) => {
                notes.push(format!("FAILED reload_project: {}", failure.observation()));
                calls.push(call_fail("reload_project", &reload_args, &failure));
            }
        }

        let open_args = json!({"path": main_scene});
        match self.call("open_scene", open_args.clone()).await {
            Ok(call) => calls.push(call_ok(
                "open_scene",
                &open_args,
                &call.payload,
                &call.correlation,
            )),
            Err(failure) => {
                notes.push(format!(
                    "FAILED open_scene({main_scene}): {}",
                    failure.observation()
                ));
                calls.push(call_fail("open_scene", &open_args, &failure));
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
        let (ok, observation, call) = match self.call("get_scene_file_content", args.clone()).await
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
                                "get_scene_file_content",
                                &args,
                                &call.payload,
                                &call.correlation,
                            ),
                        )
                    }
                    None => (
                        false,
                        format!(
                            "FAILED get_scene_file_content returned no scene text for {scene}: \
                             {parsed} (UNAVAILABLE: the scene cannot be checked)"
                        ),
                        call_ok(
                            "get_scene_file_content",
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
                call_fail("get_scene_file_content", &args, &failure),
            ),
        };
        self.finish(step, ExecKind::Assert, None, observation, ok, vec![call])
            .await
    }

    /// 3. Editor error baseline — taken *before* the project is started.
    async fn step_editor_errors(&mut self) -> anyhow::Result<()> {
        let step = BatteryStep {
            id: "editor_errors_baseline".to_string(),
            supports: vec!["N1".to_string(), "N3".to_string()],
            timeout_secs: self.limits.timeout_seconds,
            retries: self.limits.max_retries,
        };
        let args = json!({"max_lines": 50});
        let (ok, observation, call) = match self.call("get_editor_errors", args.clone()).await {
            Ok(call) => {
                let parsed = unwrap_mcp_payload(&call.payload);
                let observation = describe_editor_errors(&parsed);
                // DR-30: an `errors` array is what makes this payload an editor
                // report at all.  `smoke-t3` received the *scene text* here and
                // the observation blamed the wrong thing.
                let (ok, observation) = match parsed.get("errors").and_then(Value::as_array) {
                    Some(errors) if errors.is_empty() => (true, observation),
                    Some(_) => (
                        false,
                        format!("{observation} (UNAVAILABLE: the editor is not clean)"),
                    ),
                    None => (
                        false,
                        format!(
                            "FAILED get_editor_errors returned no `errors` array: {parsed} \
                             (UNAVAILABLE: the payload does not answer the question)"
                        ),
                    ),
                };
                (
                    ok,
                    observation,
                    call_ok("get_editor_errors", &args, &call.payload, &call.correlation),
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
        match play {
            Ok(call) => {
                // DR-30: `play_scene`'s own reply is **not** readiness evidence.
                // It is recorded, and then a scene tree is demanded.
                calls.push(call_ok(
                    "play_scene",
                    &play_args,
                    &call.payload,
                    &call.correlation,
                ));
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
        }

        let tree_args = json!({"max_depth": -1});
        let ready = self.ready("get_game_scene_tree", tree_args.clone()).await;
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
                    "get_game_scene_tree",
                    &tree_args,
                    &payload,
                    &correlation,
                ));
                let tree = unwrap_mcp_payload(&payload);
                match describe_scene_tree_shape(&tree) {
                    Ok(nodes) => {
                        let observation = format!(
                            "main scene booted; the game answered get_game_scene_tree after \
                             {attempts} poll(s) with {nodes} node(s) carrying a path and a type"
                        );
                        self.finish(step, ExecKind::RuntimeTrace, None, observation, true, calls)
                            .await?;
                        Ok(Some(tree))
                    }
                    Err(problem) => {
                        let observation = format!(
                            "FAILED the readiness reply is not a scene tree ({problem}): {tree} \
                             (UNAVAILABLE: `play_scene`'s own reply is never readiness evidence)"
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
            Ok(call) => {
                calls.push(call_ok(
                    "get_game_scene_tree",
                    &args,
                    &call.payload,
                    &call.correlation,
                ));
                Some(unwrap_mcp_payload(&call.payload))
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
    /// DR-30: a `path` may only be written when the PNG **really exists**.  When
    /// the server hands the image back inline as base64 (what `capture_frames`
    /// does), the runtime materializes it first.
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
        let mut notes: Vec<String> = Vec::new();
        let mut materialized = false;

        match self.call("get_game_screenshot", args.clone()).await {
            Ok(call) => {
                calls.push(call_ok(
                    "get_game_screenshot",
                    &args,
                    &call.payload,
                    &call.correlation,
                ));
                if absolute.is_file() {
                    // The tool wrote it itself.
                } else if let Some(bytes) = extract_inline_image(&unwrap_mcp_payload(&call.payload))
                {
                    write_png(&absolute, &bytes)?;
                    materialized = true;
                } else {
                    notes.push(format!(
                        "FAILED get_game_screenshot reported success but no file exists at {} \
                         and the payload carried no inline image",
                        absolute.display()
                    ));
                }
            }
            Err(failure) => {
                calls.push(call_fail("get_game_screenshot", &args, &failure));
                notes.push(failure.observation());
            }
        }

        if !absolute.is_file() {
            let frames_args = json!({"count": 1, "frame_interval": 10});
            match self.call("capture_frames", frames_args.clone()).await {
                Ok(call) => {
                    calls.push(call_ok(
                        "capture_frames",
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
                            "FAILED capture_frames returned no inline image: {parsed}"
                        )),
                    }
                }
                Err(failure) => {
                    calls.push(call_fail("capture_frames", &frames_args, &failure));
                    notes.push(failure.observation());
                }
            }
        }

        // One decision point, and it is about the disk, not about a reply.
        let (ok, path, observation) = if absolute.is_file() {
            let size = std::fs::metadata(&absolute).map(|m| m.len()).unwrap_or(0);
            (
                true,
                Some(relative.clone()),
                format!(
                    "screenshot written to {relative} ({size} byte(s)){}",
                    if materialized {
                        "; materialized from an inline base64 image"
                    } else {
                        ""
                    }
                ),
            )
        } else {
            (
                false,
                None,
                format!(
                    "FAILED screenshot unavailable: {} (UNAVAILABLE: no PNG exists on disk, so no \
                     path may be claimed)",
                    notes.join(" / ")
                ),
            )
        };
        self.finish(step, ExecKind::Screenshot, path, observation, ok, calls)
            .await?;
        Ok(())
    }

    /// 5. Input replay: drive `move_right` / `jump` / `move_left` and record
    ///    the `Player` position over time.
    ///
    /// DR-30: at least one frame **position sample** per recording is required,
    /// and a delivered action that leaves the position untouched is
    /// `INPUT_HAD_NO_EFFECT` (`ok = false`), not a success.
    ///
    /// DR-33: before anything is simulated, `get_input_actions` records whether
    /// the action exists in the InputMap and which keys it is bound to, so the
    /// Tester can tell "the input was never bound" (`ACTION_NOT_BOUND`) from
    /// "the controller ignores the input" (`INPUT_HAD_NO_EFFECT`).
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

        // DR-33: action availability first (read-only, no side effects).
        let probe_args = json!({});
        let bindings = match self.call("get_input_actions", probe_args.clone()).await {
            Ok(call) => {
                calls.push(call_ok(
                    "get_input_actions",
                    &probe_args,
                    &call.payload,
                    &call.correlation,
                ));
                parse_input_actions(&unwrap_mcp_payload(&call.payload))
            }
            Err(failure) => {
                calls.push(call_fail("get_input_actions", &probe_args, &failure));
                summaries.push(format!(
                    "ACTION_BINDING_UNKNOWN: get_input_actions failed: {}",
                    failure.message
                ));
                None
            }
        };
        let known = bindings.is_some();

        // `(label, action, frames, expected to move the node)`.
        for (label, action, frames, expect_movement) in [
            ("move_right", "move_right", 60u64, true),
            ("move_right_release", "move_right", 10, false),
            ("jump", "jump", 30, true),
            ("move_left", "move_left", 60, true),
        ] {
            let keys = bindings
                .as_ref()
                .and_then(|bindings| bindings.get(action).cloned());
            if known && keys.is_none() && expect_movement {
                // DR-33: the project never declared this action (PRD P3).
                needs_p3 = true;
                ok = false;
                summaries.push(format!(
                    "{label}: ACTION_NOT_BOUND (the InputMap declares no `{action}`)"
                ));
                continue;
            }
            let binding = keys
                .map(|keys| format!("keys={keys:?}"))
                .unwrap_or_else(|| "keys=unknown".to_string());

            let press_args = json!({"action": action, "pressed": true});
            match self.call("simulate_action", press_args.clone()).await {
                Ok(call) => calls.push(call_ok(
                    "simulate_action",
                    &press_args,
                    &call.payload,
                    &call.correlation,
                )),
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
                Ok(call) => {
                    let parsed = unwrap_mcp_payload(&call.payload);
                    let quadruple = replay_quadruple(action, &parsed);
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
                        "monitor_properties",
                        &monitor_args,
                        &call.payload,
                        &call.correlation,
                    );
                    if let Some(quadruple) = &quadruple {
                        entry["quadruple"] = quadruple.clone();
                    }
                    calls.push(entry);
                    match quadruple {
                        None => {
                            ok = false;
                            summaries.push(format!(
                                "{label}: NO_FRAME_SAMPLES ({})",
                                describe_monitor(label, &parsed)
                            ));
                        }
                        Some(quadruple) => {
                            let moved = quadruple["before_position"] != quadruple["after_position"];
                            if expect_movement && !moved {
                                ok = false;
                                if !known {
                                    // Without availability evidence both failure
                                    // modes are still possible.
                                    needs_p3 = true;
                                    summaries.push(format!(
                                        "{label}: {frames_seen} frame(s) ({binding}) \
                                         ACTION_BINDING_UNKNOWN + INPUT_HAD_NO_EFFECT {quadruple}"
                                    ));
                                } else {
                                    summaries.push(format!(
                                        "{label}: {frames_seen} frame(s) ({binding}) \
                                         INPUT_HAD_NO_EFFECT {quadruple}"
                                    ));
                                }
                            } else {
                                summaries.push(format!(
                                    "{label}: {frames_seen} frame(s) ({binding}) {quadruple}"
                                ));
                            }
                        }
                    }
                }
                Err(failure) => {
                    calls.push(call_fail("monitor_properties", &monitor_args, &failure));
                    summaries.push(format!("{label}: FAILED {}", failure.message));
                    ok = false;
                }
            }
            let release_args = json!({"action": action, "pressed": false});
            match self.call("simulate_action", release_args.clone()).await {
                Ok(call) => calls.push(call_ok(
                    "simulate_action",
                    &release_args,
                    &call.payload,
                    &call.correlation,
                )),
                Err(failure) => {
                    calls.push(call_fail("simulate_action", &release_args, &failure));
                    summaries.push(format!("{label}: release FAILED {}", failure.message));
                    ok = false;
                }
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
                Ok(call) => {
                    let parsed = unwrap_mcp_payload(&call.payload);
                    calls.push(call_ok(
                        "get_game_node_properties",
                        &args,
                        &call.payload,
                        &call.correlation,
                    ));
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
                Ok(call) => {
                    let parsed = unwrap_mcp_payload(&call.payload);
                    calls.push(call_ok(
                        "get_collision_info",
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
            Ok(call) => (
                true,
                format!("stop_scene: {}", unwrap_mcp_payload(&call.payload)),
                call_ok("stop_scene", &args, &call.payload, &call.correlation),
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

// ---------------------------------------------------------------------------
// DR-29: the session synchronization report
// ---------------------------------------------------------------------------

/// DR-29: where a battery session records its `get_project_info` correlation
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
/// `smoke-t3`'s `play_scene_ready` accepted `play_scene`'s reply here; the
/// difference between the two payloads is exactly this shape.
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

/// DR-30: the inline image of a `capture_frames`-style payload, decoded from
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
fn replay_quadruple(action: &str, payload: &Value) -> Option<Value> {
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
| `play_scene_ready` | N1 | `play_scene` succeeded and the game answered `get_game_scene_tree` **with a scene tree** (a reply of another shape is not readiness evidence) |
| `scene_tree` | N2, F5 | the running node tree exists, with a `path` and a `type` on every node |
| `screenshot` | N2, F4, F13, F16 | a PNG really exists under `.hoh/evidence/` (a reported path alone is not evidence) |
| `input_replay` | F1, F2, F3 (+P3 when an InputMap action is missing) | `move_right`/`jump`/`move_left` recordings of `Player.position`. Each call in `raw/input_replay.json` carries the `(action, before_position, after_position, velocity)` quadruple and the InputMap binding; `INPUT_HAD_NO_EFFECT` means the action was delivered and the position did not change, `ACTION_NOT_BOUND` means the action does not exist |
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
