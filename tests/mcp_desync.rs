//! DR-29 — a JSON-RPC response must belong to the request that asked for it.
//!
//! `smoke-t3` met a server on 9877 that answers **one request behind** and
//! carries a stale id from a previous session: `id=1` → `resp.id=704`, `id=2` →
//! the `id=1` response, `id=3` → the `id=2` response.  The client only read
//! `result`, so `project_read_scene_file_content` received `editor_open_scene`'s reply and
//! `editor_get_errors` received the scene text; the launch gate produced a
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

use hof_rs::errors::HofError;
use hof_rs::tools::mcp::McpClient;
use serde_json::{json, Value};

/// Unwrap the MCP `tools/call` envelope (`content[*].text`) into the payload the
/// server actually reported.  Every real evidence fixture has this shape, so the
/// assertions below read the payload the way a caller does.
fn unwrap_mcp_payload(payload: &Value) -> Value {
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
    /// The action of the last `editor_simulate_input_action`, so `running_game_get_node_property_samples` (which
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
        if request["params"]["name"].as_str() == Some("running_game_capture_screenshot") {
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
    if tool == "running_game_get_node_property_samples" {
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
        "editor_rescan_project_filesystem".to_string(),
        json!({"content": [{"type": "text", "text": "{\"reloaded\": true}"}]}),
    );
    replies.insert(
        "editor_open_scene".to_string(),
        json!({"content": [{"type": "text", "text": "{\"opened\": true}"}]}),
    );
    replies.insert(
        "project_read_scene_file_content".to_string(),
        json!({"content": [{"type": "text", "text": json!({
            "content": "[gd_scene load_steps=2 format=3]\n\n\
                        [node name=\"Main\" type=\"Node2D\"]\n\n\
                        [node name=\"Player\" type=\"CharacterBody2D\" parent=\".\"]\n"
        }).to_string()}]}),
    );
    replies.insert(
        "editor_get_errors".to_string(),
        fixture("editor_errors_clean.json"),
    );
    replies.insert(
        "editor_play_scene".to_string(),
        fixture("play_scene_ok.json"),
    );
    replies.insert(
        "running_game_get_scene_tree".to_string(),
        scene_tree_reply(),
    );
    replies.insert(
        "running_game_capture_screenshot".to_string(),
        json!({"content": [{"type": "text", "text": "{\"path\": \"frame\", \"size\": 686}"}]}),
    );
    replies.insert(
        "running_game_capture_frames".to_string(),
        inline_png_reply(),
    );
    replies.insert(
        "editor_get_input_actions".to_string(),
        json!({"content": [{"type": "text", "text": json!({"actions": [
            {"name": "move_left", "keys": ["A"]},
            {"name": "move_right", "keys": ["D"]},
            {"name": "jump", "keys": ["Space"]},
        ]}).to_string()}]}),
    );
    replies.insert(
        "editor_simulate_input_action".to_string(),
        fixture("simulate_action_ok.json"),
    );
    replies.insert(
        "running_game_get_node_properties".to_string(),
        fixture("player_properties.json"),
    );
    replies.insert(
        "editor_get_collision_info".to_string(),
        fixture("ground_collision.json"),
    );
    replies.insert(
        "editor_stop_scene".to_string(),
        json!({"content": [{"type": "text", "text": "{\"stopped\": true}"}]}),
    );
    replies.insert(
        "project_get_info".to_string(),
        json!({"content": [{"type": "text", "text": "{\"project\": \"HoH Mario\"}"}]}),
    );
    replies
}

// ---------------------------------------------------------------------------
// ① a correct server needs no probe
// ---------------------------------------------------------------------------

#[test]
fn a_correct_server_needs_zero_probes() {
    let server = FakeMcp::normal(battery_replies());
    let client = McpClient::new(server.url(), 5, 0);

    let (payload, correlation) = client
        .call_traced("editor_get_errors", json!({}))
        .expect("the server answers its own request");
    let inner = unwrap_mcp_payload(&payload);
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
        .call_traced("running_game_get_scene_tree", json!({"max_depth": -1}))
        .expect("the response is flushed out by one probe");
    assert!(
        text_of(&payload).contains("Main"),
        "the call must receive its own scene tree: {payload}"
    );
    assert_eq!(correlation.sync_probes, 1, "exactly one probe was needed");
    assert_ne!(correlation.response_id, Some(704));
    assert_eq!(correlation.mismatched_ids, vec![704]);
    assert_eq!(correlation.observed_offset(), Some(703));
    assert_eq!(server.tool_calls("project_get_info"), 1);
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
        .call_traced("editor_get_errors", json!({}))
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
        server.tool_calls("project_get_info"),
        2,
        "the probes are read-only and bounded"
    );
}

// ---------------------------------------------------------------------------
// ④ a mis-correlated payload is never used, whatever its shape
// ---------------------------------------------------------------------------

/// The decisive case: the response that arrives for `editor_get_errors` is the
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
        .call_traced("editor_get_errors", json!({}))
        .expect("the real errors arrive after one probe");
    let inner = unwrap_mcp_payload(&payload);
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
        .call_traced("editor_get_errors", json!({}))
        .expect_err("an unaligned server must never look like success");
    assert!(
        error.to_string().contains("desync"),
        "the failure must name the reason: {error}"
    );
}
