//! DR-29 — a JSON-RPC response must belong to the request that asked for it.
//!
//! `smoke-t3` met a server on 9877 that answers **one request behind** and
//! carries a stale id from a previous session: `id=1` → `resp.id=704`, `id=2` →
//! the `id=1` response, `id=3` → the `id=2` response.  The client only read
//! `result`, so `get_scene_file_content` received `open_scene`'s reply and
//! `get_editor_errors` received the scene text; the launch gate produced a
//! false negative and 13.4 minutes / 4.35M tokens went into repairing a defect
//! that did not exist.
//!
//! Everything below runs against a **programmable fake HTTP server**
//! (`std::net::TcpListener`); 127.0.0.1:9877 is never contacted.

mod common;

use std::collections::{HashMap, VecDeque};
use std::io::{Read, Write};
use std::net::{SocketAddr, TcpListener, TcpStream};
use std::path::Path;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::thread::JoinHandle;

use common::*;
use hof_rs::adapter::godot::{BatteryLimits, GodotAdapter, SESSION_SYNC_FILE};
use hof_rs::adapter::ProjectAdapter;
use hof_rs::config::{GodotConfig, HohConfig};
use hof_rs::errors::HofError;
use hof_rs::model::Ablation;
use hof_rs::tools::mcp::{McpClient, SessionSyncReport};
use hof_rs::tools::McpChannel;
use serde_json::{json, Value};

// ---------------------------------------------------------------------------
// The programmable server
// ---------------------------------------------------------------------------

/// One request the server is still holding, with the reply it will produce.
#[derive(Clone, Debug)]
struct Pending {
    id: Value,
    payload: Value,
}

#[derive(Clone, Debug)]
enum Mode {
    /// A correct server: the response carries the request's own id.
    Normal,
    /// `smoke-t3`: the new request is queued and the **oldest** pending one is
    /// answered, so every response lags by one.  The queue is seeded with the
    /// stale requests a previous session left behind.
    Lag,
    /// The response id never matches, no matter how many probes arrive.
    Stale { id: u64, payload: Value },
}

struct State {
    mode: Mode,
    queue: VecDeque<Pending>,
    replies: HashMap<String, Value>,
    log: Vec<Value>,
    /// The action of the last `simulate_action`, so `monitor_properties` (which
    /// does not name one) can answer with a plausible recording.
    last_action: String,
    monitor_frames: u64,
}

struct FakeMcp {
    addr: SocketAddr,
    state: Arc<Mutex<State>>,
    shutdown: Arc<AtomicBool>,
    handle: Option<JoinHandle<()>>,
}

const PNG_BYTES: &[u8] =
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\
\x00\x00\x00\x1f\x15\xc4\x89";

impl FakeMcp {
    fn start(mode: Mode, replies: HashMap<String, Value>) -> Self {
        let listener = TcpListener::bind("127.0.0.1:0").expect("a loopback listener");
        let addr = listener.local_addr().expect("the bound address");
        let state = Arc::new(Mutex::new(State {
            mode,
            queue: VecDeque::new(),
            replies,
            log: Vec::new(),
            last_action: "move_right".to_string(),
            monitor_frames: 60,
        }));
        let shutdown = Arc::new(AtomicBool::new(false));
        let thread_state = state.clone();
        let thread_shutdown = shutdown.clone();
        let handle = std::thread::spawn(move || {
            for stream in listener.incoming() {
                if thread_shutdown.load(Ordering::SeqCst) {
                    break;
                }
                let Ok(stream) = stream else { continue };
                serve(stream, &thread_state);
            }
        });
        Self {
            addr,
            state,
            shutdown,
            handle: Some(handle),
        }
    }

    /// A correct server: `results` maps a tool name to its `result` payload.
    fn normal(replies: HashMap<String, Value>) -> Self {
        Self::start(Mode::Normal, replies)
    }

    /// The `smoke-t3` shape: `seed` holds the stale (id, payload) pairs a
    /// previous session left in the server's queue.
    fn lagging(replies: HashMap<String, Value>, seed: Vec<Pending>) -> Self {
        let server = Self::start(Mode::Lag, replies);
        server.state.lock().unwrap().queue.extend(seed);
        server
    }

    fn stale(replies: HashMap<String, Value>, id: u64, payload: Value) -> Self {
        Self::start(Mode::Stale { id, payload }, replies)
    }

    fn url(&self) -> String {
        format!("http://{}/mcp", self.addr)
    }

    fn requests(&self) -> Vec<Value> {
        self.state.lock().unwrap().log.clone()
    }

    fn request_count(&self) -> usize {
        self.requests().len()
    }

    fn tool_calls(&self, tool: &str) -> usize {
        self.requests()
            .iter()
            .filter(|request| request["params"]["name"].as_str() == Some(tool))
            .count()
    }
}

impl Drop for FakeMcp {
    fn drop(&mut self) {
        self.shutdown.store(true, Ordering::SeqCst);
        // Unblock `accept` so the thread can observe the flag and exit.
        let _ = TcpStream::connect(self.addr);
        if let Some(handle) = self.handle.take() {
            let _ = handle.join();
        }
    }
}

fn serve(mut stream: TcpStream, state: &Arc<Mutex<State>>) {
    let Some(request) = read_request(&mut stream) else {
        return;
    };
    let body = {
        let mut state = state.lock().unwrap();
        state.log.push(request.clone());
        let id = request.get("id").cloned().unwrap_or(json!(0));
        if request["params"]["name"].as_str() == Some("get_game_screenshot") {
            if let Some(path) = request["params"]["arguments"]["save_path"].as_str() {
                if let Some(parent) = Path::new(path).parent() {
                    let _ = std::fs::create_dir_all(parent);
                }
                let _ = std::fs::write(path, PNG_BYTES);
            }
        }
        if let Some(action) = request["params"]["arguments"]["action"].as_str() {
            state.last_action = action.to_string();
        }
        if let Some(frames) = request["params"]["arguments"]["frame_count"].as_u64() {
            state.monitor_frames = frames;
        }
        let payload = reply_payload(&state, &request);
        match state.mode.clone() {
            Mode::Normal => rpc_response(id, payload),
            Mode::Stale { id: stale, payload } => rpc_response(json!(stale), payload),
            Mode::Lag => {
                state.queue.push_back(Pending { id, payload });
                let pending = state.queue.pop_front().expect("the queue is never empty");
                rpc_response(pending.id, pending.payload)
            }
        }
    };
    let serialized = serde_json::to_string(&body).unwrap_or_default();
    let response = format!(
        "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: \
         close\r\n\r\n{}",
        serialized.len(),
        serialized
    );
    let _ = stream.write_all(response.as_bytes());
    let _ = stream.flush();
}

fn rpc_response(id: Value, result: Value) -> Value {
    json!({"jsonrpc": "2.0", "id": id, "result": result})
}

fn reply_payload(state: &State, request: &Value) -> Value {
    let method = request["method"].as_str().unwrap_or("");
    if method == "tools/list" {
        return json!({"tools": []});
    }
    let tool = request["params"]["name"].as_str().unwrap_or("");
    if tool == "monitor_properties" {
        // The recording follows the last simulated action, exactly like the
        // real server's.
        let frames = request["params"]["arguments"]["frame_count"]
            .as_u64()
            .unwrap_or(state.monitor_frames);
        let action = state.last_action.clone();
        return monitor_reply(&action, frames);
    }
    state
        .replies
        .get(tool)
        .cloned()
        .unwrap_or_else(|| json!({"ok": true, "tool": tool}))
}

fn read_request(stream: &mut TcpStream) -> Option<Value> {
    let mut buffer = Vec::new();
    let mut chunk = [0u8; 1024];
    // Headers first.
    while !buffer.windows(4).any(|window| window == b"\r\n\r\n") {
        let read = stream.read(&mut chunk).ok()?;
        if read == 0 {
            return None;
        }
        buffer.extend_from_slice(&chunk[..read]);
    }
    let headers_end = buffer.windows(4).position(|window| window == b"\r\n\r\n")? + 4;
    let headers = String::from_utf8_lossy(&buffer[..headers_end]).to_string();
    let length: usize = headers
        .lines()
        .find_map(|line| {
            let (name, value) = line.split_once(':')?;
            if name.eq_ignore_ascii_case("content-length") {
                value.trim().parse().ok()
            } else {
                None
            }
        })
        .unwrap_or(0);
    while buffer.len() < headers_end + length {
        let read = stream.read(&mut chunk).ok()?;
        if read == 0 {
            break;
        }
        buffer.extend_from_slice(&chunk[..read]);
    }
    serde_json::from_slice(&buffer[headers_end..]).ok()
}

// ---------------------------------------------------------------------------
// Fixtures for the end-to-end battery run
// ---------------------------------------------------------------------------

fn fixture(name: &str) -> Value {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/fixtures/mcp")
        .join(name);
    let raw = std::fs::read_to_string(&path).unwrap_or_else(|error| panic!("{path:?}: {error}"));
    serde_json::from_str(&raw).unwrap_or_else(|error| panic!("{name}: {error}"))
}

fn text_of(payload: &Value) -> String {
    payload["content"][0]["text"]
        .as_str()
        .unwrap_or_else(|| panic!("no text content in {payload}"))
        .to_string()
}

/// The running scene tree, with the `Label` the HUD step requires.
fn scene_tree_reply() -> Value {
    let mut payload = fixture("node_tree.json");
    let mut tree: Value = serde_json::from_str(&text_of(&payload)).unwrap();
    let hud = tree["tree"]["children"]
        .as_array_mut()
        .unwrap()
        .iter_mut()
        .find(|child| child["name"] == json!("HUD"))
        .expect("HUD exists");
    hud["children"] = json!([{
        "name": "Score",
        "path": "/root/Main/HUD/Score",
        "type": "Label",
        "children": []
    }]);
    payload["content"][0]["text"] = Value::String(tree.to_string());
    payload
}

/// A recording that actually responds to the simulated action.
fn monitor_reply(action: &str, frames: u64) -> Value {
    let mut samples = Vec::new();
    for frame in 0..frames {
        let (x, y) = match action {
            "move_left" => (100.0 - frame as f64, 283.0),
            "jump" => (60.0, (frame as f64 * 2.0) % 80.0),
            _ => (frame as f64 * 2.0, 283.0),
        };
        samples.push(json!({"frame": frame, "position": {"x": x, "y": y}}));
    }
    json!({"content": [{"type": "text", "text": json!({
        "frame_count": frames,
        "node_path": "Player",
        "samples": samples,
    }).to_string()}]})
}

fn inline_png_reply() -> Value {
    json!({"content": [{"type": "text", "text": json!({
        "count": 1,
        "frames": [{"height": 180,
                    "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="}],
    }).to_string()}]})
}

fn battery_replies() -> HashMap<String, Value> {
    let mut replies: HashMap<String, Value> = HashMap::new();
    replies.insert(
        "reload_project".to_string(),
        json!({"content": [{"type": "text", "text": "{\"reloaded\": true}"}]}),
    );
    replies.insert(
        "open_scene".to_string(),
        json!({"content": [{"type": "text", "text": "{\"opened\": true}"}]}),
    );
    replies.insert(
        "get_scene_file_content".to_string(),
        json!({"content": [{"type": "text", "text": json!({
            "content": "[gd_scene load_steps=2 format=3]\n\n\
                        [node name=\"Main\" type=\"Node2D\"]\n\n\
                        [node name=\"Player\" type=\"CharacterBody2D\" parent=\".\"]\n"
        }).to_string()}]}),
    );
    replies.insert(
        "get_editor_errors".to_string(),
        fixture("editor_errors_clean.json"),
    );
    replies.insert("play_scene".to_string(), fixture("play_scene_ok.json"));
    replies.insert("get_game_scene_tree".to_string(), scene_tree_reply());
    replies.insert(
        "get_game_screenshot".to_string(),
        json!({"content": [{"type": "text", "text": "{\"path\": \"frame\", \"size\": 686}"}]}),
    );
    replies.insert("capture_frames".to_string(), inline_png_reply());
    replies.insert(
        "get_input_actions".to_string(),
        json!({"content": [{"type": "text", "text": json!({"actions": [
            {"name": "move_left", "keys": ["A"]},
            {"name": "move_right", "keys": ["D"]},
            {"name": "jump", "keys": ["Space"]},
        ]}).to_string()}]}),
    );
    replies.insert(
        "simulate_action".to_string(),
        fixture("simulate_action_ok.json"),
    );
    replies.insert(
        "get_game_node_properties".to_string(),
        fixture("player_properties.json"),
    );
    replies.insert(
        "get_collision_info".to_string(),
        fixture("ground_collision.json"),
    );
    replies.insert(
        "stop_scene".to_string(),
        json!({"content": [{"type": "text", "text": "{\"stopped\": true}"}]}),
    );
    replies.insert(
        "get_project_info".to_string(),
        json!({"content": [{"type": "text", "text": "{\"project\": \"HoH Mario\"}"}]}),
    );
    replies
}

/// The per-tool replies, with `monitor_properties` synthesized from the last
/// simulated action.
fn battery_server(mode: Mode) -> FakeMcp {
    match mode {
        Mode::Normal => FakeMcp::normal(battery_replies()),
        Mode::Lag => FakeMcp::lagging(
            battery_replies(),
            // The stale request the previous session left in the queue: its
            // reply is the scene text, which is exactly what `smoke-t3`'s
            // `get_editor_errors` received.
            vec![Pending {
                id: json!(704),
                payload: json!({"content": [{"type": "text", "text": "{\"content\": \"[gd_scene \
                    load_steps=2 format=3]\"}"}]}),
            }],
        ),
        Mode::Stale { id, payload } => FakeMcp::stale(battery_replies(), id, payload),
    }
}

// ---------------------------------------------------------------------------
// ① a correct server needs no probe
// ---------------------------------------------------------------------------

#[test]
fn a_correct_server_needs_zero_probes() {
    let server = FakeMcp::normal(battery_replies());
    let client = McpClient::new(server.url(), 5, 0);

    let (payload, correlation) = client
        .call_traced("get_editor_errors", json!({}))
        .expect("the server answers its own request");
    let inner = hof_rs::adapter::godot::unwrap_mcp_payload(&payload);
    assert_eq!(inner["errors"], json!([]));
    assert_eq!(correlation.request_id, Some(1));
    assert_eq!(correlation.response_id, Some(1));
    assert_eq!(correlation.sync_probes, 0);
    assert!(correlation.mismatched_ids.is_empty());
    assert_eq!(
        server.request_count(),
        1,
        "no probe request may be sent to a healthy server"
    );
}

// ---------------------------------------------------------------------------
// ② a one-step-behind server is re-correlated with exactly one probe
// ---------------------------------------------------------------------------

#[test]
fn a_lagging_server_is_re_correlated() {
    let server = FakeMcp::lagging(
        battery_replies(),
        vec![Pending {
            id: json!(704),
            payload: json!("stale session payload"),
        }],
    );
    let client = McpClient::new(server.url(), 5, 0);

    let (payload, correlation) = client
        .call_traced("get_game_scene_tree", json!({"max_depth": -1}))
        .expect("the response is flushed out by one probe");
    assert!(
        text_of(&payload).contains("Main"),
        "the call must receive its own scene tree: {payload}"
    );
    assert_eq!(correlation.sync_probes, 1, "exactly one probe was needed");
    assert_ne!(correlation.response_id, Some(704));
    assert_eq!(correlation.mismatched_ids, vec![704]);
    assert_eq!(correlation.observed_offset(), Some(703));
    assert_eq!(server.tool_calls("get_project_info"), 1);
}

// ---------------------------------------------------------------------------
// ③ persistent misalignment is a typed failure
// ---------------------------------------------------------------------------

#[test]
fn a_persistently_desynced_server_returns_a_typed_error() {
    let server = FakeMcp::stale(
        battery_replies(),
        704,
        json!({"errors": [], "count": 0, "note": "belongs to another request"}),
    );
    let client = McpClient::new(server.url(), 5, 0).with_max_sync_retries(2);

    let error = client
        .call_traced("get_editor_errors", json!({}))
        .expect_err("a response that never carries our id is not a result");
    let desync = error
        .downcast_ref::<HofError>()
        .unwrap_or_else(|| panic!("the error must stay typed: {error}"));
    match desync {
        HofError::McpResponseDesync {
            expected_id,
            got_ids,
            sync_probes,
        } => {
            assert_eq!(*expected_id, 1);
            assert_eq!(*sync_probes, 2, "the configured budget is respected");
            assert_eq!(got_ids, &vec![704, 704, 704]);
        }
        other => panic!("expected McpResponseDesync, got {other:?}"),
    }
    assert_eq!(desync.exit_code(), 4, "an unavailable dependency");
    assert_eq!(
        server.tool_calls("get_project_info"),
        2,
        "the probes are read-only and bounded"
    );
}

// ---------------------------------------------------------------------------
// ④ a mis-correlated payload is never used, whatever its shape
// ---------------------------------------------------------------------------

/// The decisive case: the response that arrives for `get_editor_errors` is the
/// **scene text** (a completely different shape).  It must never be returned as
/// this call's result — not as `count=0`, not as anything else.
#[test]
fn a_mis_correlated_payload_of_another_shape_is_never_used() {
    let scene_text = json!({"content": [{"type": "text", "text":
        "{\"content\": \"[gd_scene load_steps=18 format=3]\"}"}]});
    let server = FakeMcp::lagging(
        battery_replies(),
        vec![Pending {
            id: json!(704),
            payload: scene_text.clone(),
        }],
    );
    let client = McpClient::new(server.url(), 5, 0);

    let (payload, correlation) = client
        .call_traced("get_editor_errors", json!({}))
        .expect("the real errors arrive after one probe");
    let inner = hof_rs::adapter::godot::unwrap_mcp_payload(&payload);
    assert!(
        inner.get("errors").is_some(),
        "the call must receive the editor report: {payload}"
    );
    assert!(
        !payload.to_string().contains("gd_scene"),
        "the scene text that arrived first must never be used: {payload}"
    );
    assert_eq!(correlation.sync_probes, 1);

    // And when the server *never* aligns, the call fails instead of returning
    // whatever arrived (the `count=0` trap).
    let server = FakeMcp::stale(battery_replies(), 704, json!({"errors": [], "count": 0}));
    let client = McpClient::new(server.url(), 5, 0);
    let error = client
        .call_traced("get_editor_errors", json!({}))
        .expect_err("an unaligned server must never look like success");
    assert!(
        error.to_string().contains("desync"),
        "the failure must name the reason: {error}"
    );
}

/// The same, one level up: the battery step must not report a clean editor when
/// the payload that arrived was the scene text.
#[tokio::test]
async fn a_battery_step_never_reports_a_mis_correlated_payload_as_success() {
    let temp = tempfile::tempdir().unwrap();
    let workspace = temp.path().join("workspace");
    std::fs::create_dir_all(&workspace).unwrap();
    let server = FakeMcp::stale(
        battery_replies(),
        704,
        json!({"content": [{"type": "text", "text":
            "{\"content\": \"[gd_scene load_steps=2 format=3]\"}"}]}),
    );
    let channel = McpChannel::new(server.url(), 5, 0);
    let adapter = godot_adapter(temp.path(), &workspace);

    let records = adapter
        .evidence_battery(&workspace, &channel)
        .await
        .expect("the battery never fails the round by itself");
    let editor = records
        .iter()
        .find(|record| record.step_id == "editor_errors_baseline")
        .expect("the gate step exists");
    assert!(
        !editor.ok,
        "an unreachable answer is not a clean editor: {:?}",
        editor.record
    );
    assert!(
        editor.record.observation.contains("desync")
            || editor.record.observation.contains("UNAVAILABLE"),
        "{}",
        editor.record.observation
    );
}

// ---------------------------------------------------------------------------
// ⑤ the raw payload carries request_id / response_id / sync_probes
// ---------------------------------------------------------------------------

fn godot_adapter(root: &Path, _workspace: &Path) -> GodotAdapter {
    GodotAdapter::new(
        GodotConfig {
            editor_binary: std::path::PathBuf::new(),
            cache_excludes: vec![".gotdot".to_string()],
            main_scene: "res://scenes/main.tscn".to_string(),
        },
        true,
    )
    .with_battery_limits(BatteryLimits {
        ready_timeout_seconds: 2,
        max_retries: 0,
        timeout_seconds: 5,
    })
}

fn raw_of(workspace: &Path, step: &str) -> Value {
    let path = workspace.join(format!(".hoh/deterministic/raw/{step}.json"));
    let raw = std::fs::read_to_string(&path).unwrap_or_else(|error| panic!("{path:?}: {error}"));
    serde_json::from_str(&raw).expect("raw payload json")
}

#[tokio::test]
async fn every_battery_raw_payload_records_the_jsonrpc_correlation() {
    let temp = tempfile::tempdir().unwrap();
    let workspace = temp.path().join("workspace");
    std::fs::create_dir_all(&workspace).unwrap();
    let server = battery_server(Mode::Lag);
    let channel = McpChannel::new(server.url(), 5, 0);
    let adapter = godot_adapter(temp.path(), &workspace);

    let records = adapter
        .evidence_battery(&workspace, &channel)
        .await
        .expect("the battery completes");

    for record in &records {
        let raw = raw_of(&workspace, &record.step_id);
        for key in ["request_id", "response_id", "sync_probes"] {
            assert!(
                raw.get(key).is_some(),
                "{}: the raw header is missing `{key}`: {raw}",
                record.step_id
            );
        }
        assert!(
            raw["request_id"].is_u64(),
            "{}: the request id must be recorded: {raw}",
            record.step_id
        );
        assert!(
            raw["sync_probes"].as_u64().unwrap_or(0) >= 1,
            "every call needed a probe against the lagging server: {raw}"
        );
    }

    // The editor step really saw the editor report, not the stale scene text.
    let editor = raw_of(&workspace, "editor_errors_baseline");
    assert!(
        editor["calls"][0]["payload"]["content"][0]["text"]
            .as_str()
            .unwrap_or("")
            .contains("\"errors\""),
        "{editor}"
    );
    assert!(
        !editor.to_string().contains("gd_scene"),
        "the stale payload must not appear as this step's evidence: {editor}"
    );

    // The session probe left a durable report.
    let sync: SessionSyncReport = serde_json::from_str(
        &std::fs::read_to_string(workspace.join(SESSION_SYNC_FILE)).expect("mcp-sync.json"),
    )
    .expect("the report parses");
    assert!(sync.available, "{sync:?}");
    assert!(
        sync.desynced,
        "the lagging server must be detected: {sync:?}"
    );
    assert!(sync.probes >= 1, "{sync:?}");
}

// ---------------------------------------------------------------------------
// ⑥ the desync reaches result.json.warnings
// ---------------------------------------------------------------------------

#[tokio::test]
async fn a_desynchronized_session_is_reported_in_result_json_warnings() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let mut cfg: HohConfig = test_config(root, 1);
    cfg.runtime.spec = root.join("spec.md");
    cfg.tools.max_sync_retries = 4;
    let spec = write_spec(root);
    let server = battery_server(Mode::Lag);

    let orchestrator = hof_rs::runtime::run_loop::Orchestrator {
        harness: Box::new(FakeHarness::new(happy_script())),
        adapter: Box::new(godot_adapter(root, &cfg.runtime.workspace)),
        tools: Arc::new(McpChannel::new(server.url(), 5, 0)),
        cfg,
        ablation: Ablation::default(),
        force_init: true,
        start_state: hof_rs::runtime::start_state::StartState::as_is(),
    };
    hof_rs::runtime::run_loop::run(&orchestrator, &spec, "run-1")
        .await
        .expect("the desync is a warning, not a crash");

    let result: Value = serde_json::from_str(&read(&root.join("runs/run-1/iter-1/result.json")))
        .expect("result.json");
    let warnings = result["warnings"].as_array().expect("warnings");
    let desync = warnings
        .iter()
        .filter_map(Value::as_str)
        .find(|warning| warning.starts_with("mcp_desync_detected"))
        .unwrap_or_else(|| panic!("mcp_desync_detected must be recorded: {warnings:?}"));
    // The offset the *session probe itself* observed: by the time the battery
    // starts, `index_markdown`'s `tools/list` has already consumed the +703
    // stale entry, so the probe sees the ordinary "one request behind" −1.
    assert!(desync.contains("id_offset=-1"), "{desync}");
    assert!(desync.contains("probes="), "{desync}");
}

/// A healthy session must not produce the warning (no unconditional noise).
#[tokio::test]
async fn a_healthy_session_records_no_desync_warning() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let mut cfg: HohConfig = test_config(root, 1);
    cfg.runtime.spec = root.join("spec.md");
    let spec = write_spec(root);
    let server = battery_server(Mode::Normal);

    let orchestrator = hof_rs::runtime::run_loop::Orchestrator {
        harness: Box::new(FakeHarness::new(happy_script())),
        adapter: Box::new(godot_adapter(root, &cfg.runtime.workspace)),
        tools: Arc::new(McpChannel::new(server.url(), 5, 0)),
        cfg,
        ablation: Ablation::default(),
        force_init: true,
        start_state: hof_rs::runtime::start_state::StartState::as_is(),
    };
    hof_rs::runtime::run_loop::run(&orchestrator, &spec, "run-1")
        .await
        .expect("the happy path completes");

    let result: Value = serde_json::from_str(&read(&root.join("runs/run-1/iter-1/result.json")))
        .expect("result.json");
    let warnings = result["warnings"].as_array().expect("warnings");
    assert!(
        !warnings
            .iter()
            .filter_map(Value::as_str)
            .any(|warning| warning.starts_with("mcp_desync_detected")),
        "a healthy server must not be reported as desynchronized: {warnings:?}"
    );
}

/// The monitor replies are synthesized from the last simulated action, which
/// needs the server to hold no state; the helper is kept honest by asserting
/// both shapes exist.
#[test]
fn the_monitor_reply_helper_covers_both_actions() {
    let moving = monitor_reply("move_right", 3);
    let idle = monitor_reply("jump", 3);
    assert!(text_of(&moving).contains("\"x\":4.0"));
    assert!(text_of(&idle).contains("\"y\":4.0"));
}
