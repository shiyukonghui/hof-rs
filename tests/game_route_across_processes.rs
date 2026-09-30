//! DR-69 ① — the root cause: a role's `hoh tools call` cannot reach the game
//! endpoint.
//!
//! `smoke-t9` measured it: the game was running and `editor_play_scene` had
//! announced `mcp_port=61183`, yet a **fresh** role process asking for
//! `running_game_get_scene_tree` was refused with `game_endpoint_unavailable`
//! (exit 5).  The route lives only in the harness process's memory
//! (`src/tools/mod.rs` `McpChannel::game`, `register_game_endpoint` at `:312`),
//! and every `hoh tools call` builds a brand-new channel
//! (`src/cli_impl.rs:53` → `bridge::channel_for` at `src/tools/bridge.rs:227`),
//! so the route is **always** empty in a role process.
//!
//! Road (A) — chosen here — makes the route resolvable across processes: the
//! run that registers the endpoint also *publishes* it to a controlled file,
//! and a later process adopts that file.  Everything here is offline: the
//! endpoints are loopback HTTP doubles and no real port is touched.

use std::io::{Read, Write};
use std::net::{SocketAddr, TcpListener, TcpStream};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::thread::JoinHandle;
use std::time::Duration;

use serde_json::{json, Value};

/// DR-69: the published route file name, pinned here as a literal so the red
/// test does not depend on the constant it is meant to introduce.  The green
/// phase asserts that the production constant equals this string.
const ROUTE_FILE: &str = "game_endpoint.json";

/// A loopback JSON-RPC double that records the tool names it was asked for.
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
                    Ok((stream, _)) => {
                        stream
                            .set_nonblocking(false)
                            .expect("an accepted stream must block on reads");
                        serve(stream, &thread_tools);
                    }
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

/// A minimal MCP `tools/call` responder: one request, one `result`, close.
fn serve(mut stream: TcpStream, tools: &Arc<Mutex<Vec<String>>>) {
    let _ = stream.set_read_timeout(Some(Duration::from_secs(5)));
    let mut buffer = Vec::new();
    let mut chunk = [0u8; 1024];
    loop {
        let read = match stream.read(&mut chunk) {
            Ok(0) => return,
            Ok(read) => read,
            Err(_) => return,
        };
        buffer.extend_from_slice(&chunk[..read]);
        let Some(header_end) = find(&buffer, b"\r\n\r\n") else {
            continue;
        };
        let headers = String::from_utf8_lossy(&buffer[..header_end]).into_owned();
        let length = headers
            .lines()
            .find_map(|line| {
                line.to_ascii_lowercase()
                    .strip_prefix("content-length:")
                    .map(|value| value.trim().parse::<usize>().unwrap_or(0))
            })
            .unwrap_or(0);
        if buffer.len() < header_end + 4 + length {
            continue;
        }
        let body = String::from_utf8_lossy(&buffer[header_end + 4..header_end + 4 + length]);
        let request: Value = serde_json::from_str(&body).unwrap_or(json!({}));
        if let Some(name) = request["params"]["name"].as_str() {
            tools.lock().unwrap().push(name.to_string());
        }
        let id = request.get("id").cloned().unwrap_or(json!(0));
        let inner = json!({"tree": {"name": "Main", "path": "/root/Main"}}).to_string();
        let body = json!({
            "jsonrpc": "2.0",
            "id": id,
            "result": {"content": [{"type": "text", "text": inner}]},
        });
        let serialized = serde_json::to_string(&body).unwrap_or_default();
        let response = format!(
            "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\
             Connection: close\r\n\r\n{serialized}",
            serialized.len()
        );
        let _ = stream.write_all(response.as_bytes());
        let _ = stream.flush();
        return;
    }
}

/// Byte search, so a multi-byte body slice is indexed on the raw buffer.
fn find(haystack: &[u8], needle: &[u8]) -> Option<usize> {
    haystack
        .windows(needle.len())
        .position(|window| window == needle)
}

/// The published route file, in the exact shape the runtime writes.
fn publish_route(run_dir: &Path, game: &RecordingMcp) -> PathBuf {
    std::fs::create_dir_all(run_dir).expect("run dir");
    let path = run_dir.join(ROUTE_FILE);
    let record = json!({
        "endpoint": game.url(),
        "port": game.addr.port(),
        "source": "auto_free_port",
        "pid": 4242,
    });
    std::fs::write(&path, serde_json::to_string(&record).unwrap()).expect("route file");
    path
}

/// Run the real `hoh` binary as a role's shell would: a **fresh process**.
fn role_tools_call(tool: &str, editor_url: &str, route: Option<&Path>) -> std::process::Output {
    let mut command = Command::new(env!("CARGO_BIN_EXE_hoh"));
    command
        .args([
            "tools",
            "call",
            tool,
            "--role",
            "developer",
            "-c",
            &format!("tools.endpoint={editor_url}"),
            "-c",
            "tools.max_retries=0",
            "-c",
            "tools.timeout_seconds=5",
        ])
        .current_dir(PathBuf::from(env!("CARGO_MANIFEST_DIR")));
    match route {
        Some(path) => {
            command.env("HOH_GAME_ROUTE", path);
        }
        None => {
            command.env_remove("HOH_GAME_ROUTE");
        }
    }
    command.output().expect("the hoh binary must be runnable")
}

// ---------------------------------------------------------------------------
// ① the red test: a role shell reaching the game endpoint across processes
// ---------------------------------------------------------------------------

/// DR-69 ① (road A): with the route published by the run that registered it, a
/// **later, separate process** must be able to run a `running_game_*` tool.
///
/// This is the criterion the task book states: "游戏在跑时，角色 shell 的一条
/// `hoh tools call running_game_*` 必须成功".  The live game cannot be started
/// offline, so the evidence is a loopback game endpoint plus the *published
/// route* — the structural dependency the real round failed on.
#[test]
fn a_role_shell_reaches_the_published_game_endpoint_across_processes() {
    let temp = tempfile::tempdir().unwrap();
    let editor = RecordingMcp::start();
    let game = RecordingMcp::start();
    let route = publish_route(&temp.path().join("runs/run-1"), &game);

    let output = role_tools_call("running_game_get_scene_tree", &editor.url(), Some(&route));
    let stdout = String::from_utf8_lossy(&output.stdout).into_owned();
    let stderr = String::from_utf8_lossy(&output.stderr).into_owned();

    assert_eq!(
        output.status.code(),
        Some(0),
        "the role shell must reach the game endpoint the run published\nstdout: {stdout}\nstderr: {stderr}"
    );
    assert_eq!(
        game.tools(),
        vec!["running_game_get_scene_tree".to_string()],
        "the game endpoint must have served the request"
    );
    assert!(
        !editor
            .tools()
            .iter()
            .any(|tool| tool.starts_with("running_game_")),
        "the editor endpoint must never receive a running_game_* request: {:?}",
        editor.tools()
    );
    assert!(
        !stdout.contains("game_endpoint_unavailable"),
        "the refusal must be gone: {stdout}"
    );
}

/// DR-43 is **not** weakened: with no published route, a `running_game_*` call
/// from a fresh process must still fail loudly and must not fall back to the
/// editor endpoint.
#[test]
fn without_a_published_route_the_game_call_still_fails_loudly() {
    let editor = RecordingMcp::start();
    let output = role_tools_call("running_game_get_scene_tree", &editor.url(), None);
    let stdout = String::from_utf8_lossy(&output.stdout).into_owned();
    let stderr = String::from_utf8_lossy(&output.stderr).into_owned();
    let combined = format!("{stdout}{stderr}");

    assert_ne!(
        output.status.code(),
        Some(0),
        "an unresolvable game endpoint must not be reported as success"
    );
    assert!(
        combined.contains("game_endpoint_unavailable"),
        "the refusal text must name the missing endpoint: {combined}"
    );
    assert!(
        editor.tools().is_empty(),
        "no request may be sent to the editor for a game tool: {:?}",
        editor.tools()
    );
}

/// DR-69 ①: the run that registers the endpoint publishes it — and
/// `editor_stop_scene` withdraws it again, so a later process can never reach a
/// **stale** port (DR-43's guarantee, one process wider).
#[tokio::test]
async fn registering_publishes_the_route_and_stopping_withdraws_it() {
    use hof_rs::tools::endpoint::{
        endpoint_for_port, game_route_path, GameEndpointRecord, GAME_ROUTE_FILE,
        SOURCE_AUTO_FREE_PORT,
    };
    use hof_rs::tools::{McpChannel, ToolChannel};

    // The literal the red test used and the production constant are one string.
    assert_eq!(GAME_ROUTE_FILE, ROUTE_FILE);

    let temp = tempfile::tempdir().unwrap();
    let run_dir = temp.path().join("runs/run-1");
    std::fs::create_dir_all(&run_dir).unwrap();
    let published = game_route_path(&run_dir);
    let channel = McpChannel::new("http://127.0.0.1:1/mcp", 5, 0);
    channel.use_game_route_file(published.clone());

    let record = GameEndpointRecord {
        endpoint: endpoint_for_port(63999),
        port: Some(63999),
        source: SOURCE_AUTO_FREE_PORT.to_string(),
        pid: Some(11),
    };
    channel
        .register_game_endpoint(record.clone())
        .await
        .expect("registration");

    let raw = std::fs::read_to_string(&published)
        .unwrap_or_else(|error| panic!("the route must be published at {published:?}: {error}"));
    let parsed: GameEndpointRecord = serde_json::from_str(&raw).expect("the published JSON");
    assert_eq!(parsed, record);

    // A brand-new channel — i.e. another process — adopts it.
    let other = McpChannel::new("http://127.0.0.1:1/mcp", 5, 0);
    assert_eq!(
        other.use_game_route_file(published.clone()),
        Some(record.clone())
    );

    // `editor_stop_scene` withdraws the route for everyone.
    channel.clear_game_endpoint().await;
    assert!(
        !published.exists(),
        "a stopped game must not stay resolvable across processes"
    );
    let third = McpChannel::new("http://127.0.0.1:1/mcp", 5, 0);
    assert!(third.use_game_route_file(published).is_none());
}
