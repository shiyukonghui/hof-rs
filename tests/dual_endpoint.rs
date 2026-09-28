//! DR-43 — the two MCP endpoints.
//!
//! Under the new contract the editor endpoint (9877) serves `editor_*`,
//! `project_*` and `os_*` only; the **running game is a separate endpoint** that
//! `editor_play_scene` creates and announces (`endpoint` / `mcp_port` /
//! `mcp_port_source` / `pid`).  Two rules follow, and both are checked here:
//!
//! * a `running_game_*` call must **never** be sent to the editor endpoint —
//!   not even as a fallback when the game endpoint is unknown (that fallback
//!   would silently produce fabricated evidence);
//! * after `editor_stop_scene` the game endpoint is dead, so later
//!   `running_game_*` calls must fail instead of reaching a stale port.
//!
//! Everything here is offline: the endpoints are loopback HTTP doubles.

use std::io::{Read, Write};
use std::net::{SocketAddr, TcpListener, TcpStream};
use std::path::Path;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::thread::JoinHandle;
use std::time::Duration;

use hof_rs::adapter::godot::{parse_game_endpoint, BatteryLimits, GodotAdapter};
use hof_rs::adapter::ProjectAdapter;
use hof_rs::config::GodotConfig;
use hof_rs::model::Role;
use hof_rs::tools::endpoint::{
    endpoint_for_port, scope_of, GameEndpointRecord, ToolScope, SOURCE_ARGUMENT,
    SOURCE_AUTO_FREE_PORT, SOURCE_UNDECLARED,
};
use hof_rs::tools::{McpChannel, ToolChannel, ToolResult};
use serde_json::{json, Value};

// ---------------------------------------------------------------------------
// A loopback JSON-RPC double that records the tool names it was asked for
// ---------------------------------------------------------------------------

struct RecordingMcp {
    addr: SocketAddr,
    tools: Arc<Mutex<Vec<String>>>,
    shutdown: Arc<AtomicBool>,
    handle: Option<JoinHandle<()>>,
}

impl RecordingMcp {
    fn start() -> Self {
        let listener = TcpListener::bind("127.0.0.1:0").expect("loopback listener");
        let addr = listener.local_addr().expect("bound address");
        listener
            .set_nonblocking(true)
            .expect("a non-blocking listener");
        let tools = Arc::new(Mutex::new(Vec::new()));
        let shutdown = Arc::new(AtomicBool::new(false));
        let thread_tools = tools.clone();
        let thread_shutdown = shutdown.clone();
        let handle = std::thread::spawn(move || {
            while !thread_shutdown.load(Ordering::SeqCst) {
                match listener.accept() {
                    Ok((stream, _)) => serve(stream, &thread_tools),
                    Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => {
                        std::thread::sleep(Duration::from_millis(2));
                    }
                    Err(_) => break,
                }
            }
        });
        Self {
            addr,
            tools,
            shutdown,
            handle: Some(handle),
        }
    }

    fn url(&self) -> String {
        format!("http://{}/mcp", self.addr)
    }

    fn port(&self) -> u16 {
        self.addr.port()
    }

    /// The tool names this endpoint was asked to run, in arrival order.
    fn tools(&self) -> Vec<String> {
        self.tools.lock().unwrap().clone()
    }
}

impl Drop for RecordingMcp {
    fn drop(&mut self) {
        self.shutdown.store(true, Ordering::SeqCst);
        let _ = TcpStream::connect(self.addr);
        if let Some(handle) = self.handle.take() {
            let _ = handle.join();
        }
    }
}

fn serve(mut stream: TcpStream, tools: &Arc<Mutex<Vec<String>>>) {
    let Some(request) = read_request(&mut stream) else {
        return;
    };
    if let Some(name) = request["params"]["name"].as_str() {
        tools.lock().unwrap().push(name.to_string());
    }
    let id = request.get("id").cloned().unwrap_or(json!(0));
    let body = json!({
        "jsonrpc": "2.0",
        "id": id,
        "result": {"content": [{"type": "text", "text": "{\"ok\": true}"}]},
    });
    let serialized = serde_json::to_string(&body).unwrap_or_default();
    let response = format!(
        "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\
         Connection: close\r\n\r\n{serialized}",
        serialized.len()
    );
    let _ = stream.write_all(response.as_bytes());
    let _ = stream.flush();
}

fn read_request(stream: &mut TcpStream) -> Option<Value> {
    stream.set_read_timeout(Some(Duration::from_secs(5))).ok()?;
    let mut buffer = Vec::new();
    let mut chunk = [0u8; 1024];
    loop {
        let read = stream.read(&mut chunk).ok()?;
        if read == 0 {
            break;
        }
        buffer.extend_from_slice(&chunk[..read]);
        let text = String::from_utf8_lossy(&buffer).into_owned();
        if let Some(header_end) = text.find("\r\n\r\n") {
            let length = text
                .lines()
                .find_map(|line| {
                    line.to_ascii_lowercase()
                        .strip_prefix("content-length:")
                        .map(|value| value.trim().parse::<usize>().unwrap_or(0))
                })
                .unwrap_or(0);
            if buffer.len() >= header_end + 4 + length {
                return serde_json::from_str(&text[header_end + 4..]).ok();
            }
        }
    }
    None
}

// ---------------------------------------------------------------------------
// ① scope routing
// ---------------------------------------------------------------------------

#[test]
fn the_scope_of_a_tool_is_decided_by_its_channel_prefix() {
    assert_eq!(scope_of("editor_play_scene"), ToolScope::Editor);
    assert_eq!(scope_of("project_get_info"), ToolScope::Editor);
    assert_eq!(scope_of("os_list_android_devices"), ToolScope::Editor);
    assert_eq!(scope_of("running_game_get_scene_tree"), ToolScope::Game);
}

#[tokio::test]
async fn running_game_tools_never_reach_the_editor_endpoint() {
    let editor = RecordingMcp::start();
    let game = RecordingMcp::start();
    let channel = McpChannel::new(editor.url(), 5, 0);

    channel
        .call(Role::Developer, "editor_get_errors", json!({}))
        .await
        .expect("an editor tool must reach the editor endpoint");
    assert_eq!(editor.tools(), vec!["editor_get_errors".to_string()]);

    // Before registration there is no game endpoint: the call must fail and
    // must not be silently sent to the editor (DR-43 forbids that fallback).
    let error = channel
        .call(Role::Developer, "running_game_get_scene_tree", json!({}))
        .await
        .expect_err("an unregistered game endpoint must be an error, not a fallback");
    assert!(
        error.to_string().contains("game_endpoint_unavailable"),
        "the error must name the missing endpoint: {error}"
    );
    assert!(
        editor.tools().len() == 1 && game.tools().is_empty(),
        "no request may have been sent: editor={:?} game={:?}",
        editor.tools(),
        game.tools()
    );

    // The battery registers what `editor_play_scene` announced.
    channel
        .register_game_endpoint(GameEndpointRecord {
            endpoint: game.url(),
            port: Some(game.port()),
            source: SOURCE_AUTO_FREE_PORT.to_string(),
            pid: Some(4242),
        })
        .await
        .expect("registration");

    channel
        .call(Role::Developer, "running_game_get_scene_tree", json!({}))
        .await
        .expect("a game tool must reach the game endpoint");
    assert_eq!(
        game.tools(),
        vec!["running_game_get_scene_tree".to_string()]
    );
    assert!(
        !editor
            .tools()
            .iter()
            .any(|tool| tool.starts_with("running_game_")),
        "the editor endpoint must never see a running_game_* request: {:?}",
        editor.tools()
    );

    // project_* still belongs to the editor.
    channel
        .call(Role::Developer, "project_get_info", json!({}))
        .await
        .expect("a project tool must reach the editor endpoint");
    assert!(editor.tools().contains(&"project_get_info".to_string()));
    assert!(!game.tools().contains(&"project_get_info".to_string()));
}

#[tokio::test]
async fn stop_scene_invalidates_the_game_endpoint() {
    let editor = RecordingMcp::start();
    let game = RecordingMcp::start();
    let channel = McpChannel::new(editor.url(), 5, 0);
    channel
        .register_game_endpoint(GameEndpointRecord {
            endpoint: game.url(),
            port: Some(game.port()),
            source: SOURCE_ARGUMENT.to_string(),
            pid: Some(7),
        })
        .await
        .expect("registration");

    channel
        .call(Role::Developer, "running_game_get_scene_tree", json!({}))
        .await
        .expect("the game endpoint is live");
    assert_eq!(game.tools().len(), 1);

    channel.clear_game_endpoint().await;
    assert!(
        channel.game_endpoint().await.is_none(),
        "the registered endpoint must be gone"
    );

    let error = channel
        .call(Role::Developer, "running_game_get_scene_tree", json!({}))
        .await
        .expect_err("a dead game endpoint must make the call fail");
    assert!(error.to_string().contains("game_endpoint_unavailable"));
    assert_eq!(
        game.tools().len(),
        1,
        "the call must not reach the stale port: {:?}",
        game.tools()
    );
}

/// DR-51: `editor_stop_scene` invalidates the **route**, not the fact that this
/// run registered a game endpoint.  Without this, `smoke-t6`'s
/// `meta.json.engine.mcp.game_endpoint` was structurally always `null`: the
/// battery's stop step cleared the registration before the run loop ever looked
/// at it.
#[tokio::test]
async fn the_registered_game_endpoint_survives_the_route_being_cleared() {
    let channel = McpChannel::new("http://127.0.0.1:1/mcp", 5, 0);
    let record = GameEndpointRecord {
        endpoint: "http://127.0.0.1:63698/mcp".to_string(),
        port: Some(63698),
        source: SOURCE_AUTO_FREE_PORT.to_string(),
        pid: Some(101872),
    };

    assert!(channel.game_endpoint_history().await.is_none());
    channel
        .register_game_endpoint(record.clone())
        .await
        .expect("registration");

    assert_eq!(channel.game_endpoint().await, Some(record.clone()));
    assert_eq!(channel.game_endpoint_history().await, Some(record.clone()));

    channel.clear_game_endpoint().await;
    assert!(
        channel.game_endpoint().await.is_none(),
        "the *route* must be gone so a later call fails loudly (DR-43)"
    );
    assert_eq!(
        channel.game_endpoint_history().await,
        Some(record),
        "the identity of the endpoint this run used must not be erased (DR-51)"
    );
}

// ---------------------------------------------------------------------------
// ② the `editor_play_scene` reply is the only source of the game endpoint
// ---------------------------------------------------------------------------

#[test]
fn the_play_scene_reply_is_parsed_into_the_game_endpoint() {
    let envelope = |inner: Value| {
        json!({"content": [{"type": "text", "text": inner.to_string()}]})
    };

    // `endpoint` wins; `mcp_port_source` is recorded verbatim.
    let record = parse_game_endpoint(&envelope(json!({
        "endpoint": "http://127.0.0.1:9899/mcp",
        "mcp_port": 9899,
        "mcp_port_source": "argument",
        "pid": 77,
        "playing": true,
    })))
    .expect("the reply announces its endpoint");
    assert_eq!(record.endpoint, "http://127.0.0.1:9899/mcp");
    assert_eq!(record.port, Some(9899));
    assert_eq!(record.source, "argument");
    assert_eq!(record.pid, Some(77));

    // Otherwise the endpoint is derived from `mcp_port`.
    let record = parse_game_endpoint(&json!({
        "mcp_port": 9900,
        "mcp_port_source": "auto_free_port",
    }))
    .expect("the reply announces a port");
    assert_eq!(record.endpoint, endpoint_for_port(9900));
    assert_eq!(record.port, Some(9900));
    assert_eq!(record.source, "auto_free_port");
    assert_eq!(record.pid, None);

    // The pre-DR-43 reply shape (no endpoint, no port) is a hard failure:
    // the caller must not guess one.
    let error = parse_game_endpoint(&json!({"mode": "main", "playing": true}))
        .expect_err("a reply without an endpoint must not produce one");
    assert!(error.contains("mcp_port"), "{error}");
    assert!(error.contains("endpoint"), "{error}");
}

/// DR-53 (DEF-3): `mcp_port_source`'s third value.  The engine may announce an
/// endpoint without a port source, or with one this contract does not know; both
/// must be recorded as `undeclared` rather than invented as
/// `argument`/`auto_free_port`.  (`smoke-t6` only exercised `auto_free_port`.)
#[test]
fn an_endpoint_without_a_declared_port_source_is_undeclared() {
    let envelope = |inner: Value| {
        json!({"content": [{"type": "text", "text": inner.to_string()}]})
    };

    // The field is absent.
    let record = parse_game_endpoint(&envelope(json!({
        "endpoint": "http://127.0.0.1:9899/mcp",
        "pid": 77,
        "playing": true,
    })))
    .expect("an explicit endpoint needs no port source");
    assert_eq!(record.source, SOURCE_UNDECLARED);
    assert_eq!(record.port, Some(9899));

    // The field carries a value this contract does not document.
    let record = parse_game_endpoint(&envelope(json!({
        "mcp_port": 9900,
        "mcp_port_source": "invented_source",
    })))
    .expect("an mcp_port needs no documented source");
    assert_eq!(record.source, SOURCE_UNDECLARED);

    // And the two documented values are still recorded verbatim.
    assert_eq!(
        parse_game_endpoint(&envelope(json!({"mcp_port": 9900, "mcp_port_source": "argument"})))
            .unwrap()
            .source,
        SOURCE_ARGUMENT
    );
    assert_eq!(
        parse_game_endpoint(&envelope(json!({"mcp_port": 9900, "mcp_port_source": "auto_free_port"})))
            .unwrap()
            .source,
        SOURCE_AUTO_FREE_PORT
    );
}

// ---------------------------------------------------------------------------
// ③ the battery registers (or fails) — never falls back
// ---------------------------------------------------------------------------

#[derive(Default)]
struct RegistrationChannel {
    play_reply: Value,
    registrations: Mutex<Vec<GameEndpointRecord>>,
    clears: Mutex<u32>,
}

impl RegistrationChannel {
    fn with_play_reply(play_reply: Value) -> Self {
        Self {
            play_reply,
            ..Self::default()
        }
    }

    fn registered(&self) -> Vec<GameEndpointRecord> {
        self.registrations.lock().unwrap().clone()
    }

    fn clears(&self) -> u32 {
        *self.clears.lock().unwrap()
    }
}

#[async_trait::async_trait]
impl ToolChannel for RegistrationChannel {
    fn allowed(&self, _role: Role, _tool: &str) -> bool {
        true
    }

    fn index_markdown(&self, _role: Role) -> String {
        String::new()
    }

    async fn call(&self, _role: Role, tool: &str, _args: Value) -> anyhow::Result<ToolResult> {
        let payload = match tool {
            "editor_play_scene" => self.play_reply.clone(),
            "running_game_get_scene_tree" => json!({"content": [{"type": "text", "text":
                "{\"tree\":{\"name\":\"Main\",\"path\":\"/root/Main\",\"type\":\"Node2D\"}}"}]}),
            _ => json!({}),
        };
        Ok(ToolResult { ok: true, payload })
    }

    async fn register_game_endpoint(&self, record: GameEndpointRecord) -> anyhow::Result<()> {
        self.registrations.lock().unwrap().push(record);
        Ok(())
    }

    async fn clear_game_endpoint(&self) {
        *self.clears.lock().unwrap() += 1;
    }
}

fn battery_adapter() -> GodotAdapter {
    GodotAdapter::new(
        GodotConfig {
            editor_binary: std::path::PathBuf::new(),
            cache_excludes: vec![],
            main_scene: "res://scenes/main.tscn".to_string(),
        },
        false,
    )
    .with_battery_limits(BatteryLimits {
        ready_timeout_seconds: 0,
        max_retries: 0,
        timeout_seconds: 5,
    })
}

async fn run_battery(workspace: &Path, channel: &RegistrationChannel) -> Vec<Value> {
    let records = battery_adapter()
        .evidence_battery(workspace, channel)
        .await
        .expect("the battery completes");
    serde_json::to_value(&records)
        .expect("records serialize")
        .as_array()
        .cloned()
        .unwrap_or_default()
}

fn step<'a>(records: &'a [Value], id: &str) -> &'a Value {
    records
        .iter()
        .find(|record| record["step_id"] == json!(id))
        .unwrap_or_else(|| panic!("the battery must declare `{id}`: {records:?}"))
}

#[tokio::test]
async fn the_play_scene_step_registers_the_announced_endpoint() {
    let temp = tempfile::tempdir().unwrap();
    let workspace = temp.path().join("workspace");
    std::fs::create_dir_all(&workspace).unwrap();
    let channel = RegistrationChannel::with_play_reply(json!({
        "content": [{"type": "text", "text": json!({
            "playing": true,
            "mcp_port": 9901,
            "mcp_port_source": "auto_free_port",
            "pid": 4242,
        }).to_string()}]
    }));

    let records = run_battery(&workspace, &channel).await;

    let play = step(&records, "play_scene_ready");
    assert_eq!(
        play["ok"],
        json!(true),
        "the step must succeed: {}",
        play["record"]["observation"]
    );
    let registered = channel.registered();
    assert_eq!(registered.len(), 1, "{registered:?}");
    assert_eq!(registered[0].endpoint, endpoint_for_port(9901));
    assert_eq!(registered[0].port, Some(9901));
    assert_eq!(registered[0].source, "auto_free_port");
    assert_eq!(registered[0].pid, Some(4242));

    // `editor_stop_scene` invalidates it again (DR-43).
    assert!(
        channel.clears() >= 1,
        "the stop step must invalidate the game endpoint"
    );
}

#[tokio::test]
async fn the_play_scene_step_fails_when_no_endpoint_is_announced() {
    let temp = tempfile::tempdir().unwrap();
    let workspace = temp.path().join("workspace");
    std::fs::create_dir_all(&workspace).unwrap();
    // Exactly the shape the old channel used to answer with.
    let channel = RegistrationChannel::with_play_reply(json!({
        "content": [{"type": "text", "text": "{\"mode\":\"main\",\"playing\":true}"}]
    }));

    let records = run_battery(&workspace, &channel).await;

    let play = step(&records, "play_scene_ready");
    assert_eq!(
        play["ok"],
        json!(false),
        "a reply without an endpoint must fail the step: {play}"
    );
    let observation = play["record"]["observation"].as_str().unwrap_or("");
    assert!(
        observation.contains("mcp_port") || observation.contains("endpoint"),
        "the observation must name what is missing: {observation}"
    );
    assert!(
        observation.contains("UNAVAILABLE"),
        "the failure must be honest: {observation}"
    );
    assert!(
        channel.registered().is_empty(),
        "nothing may be registered without an announced endpoint"
    );
    // The raw payload must carry the failed registration attempt itself (the
    // observation lives in the record, asserted above).
    let raw = std::fs::read_to_string(
        workspace.join(".hoh/deterministic/raw/play_scene_ready.json"),
    )
    .expect("the raw payload exists");
    assert!(
        raw.contains("neither an `endpoint` nor an `mcp_port`")
            && raw.contains("\"ok\": false"),
        "the raw payload must record the failure: {raw}"
    );
}
