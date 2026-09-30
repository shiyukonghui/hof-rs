//! DR-71 ①: the round's route may only be published next to a game the start has
//! **confirmed** is answering.
//!
//! DR-70 moved the round-game start before the first role, but the real
//! `GodotAdapter` registered (published) the record at `godot.rs:3853` **before**
//! it polled readiness at `:3856-3876`, and bailed at `:3871` without withdrawing.
//! The DR-70 acceptance's out-of-repo probe measured the consequence: a fresh or
//! not-yet-ready project could leave a route visible inside the first role's
//! window, and a route whose port answers is adopted (probe case C) — a route that
//! lies about a game the start could not confirm.
//!
//! These tests drive the **real, production** `GodotAdapter::start_round_game`
//! against loopback MCP doubles: no Godot, no external service, no network beyond
//! `127.0.0.1`, and nothing under `runs/**`.

mod common;

use std::io::{Read, Write};
use std::net::{SocketAddr, TcpListener, TcpStream};
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::thread::JoinHandle;
use std::time::Duration;

use hof_rs::adapter::godot::BatteryLimits;
use hof_rs::adapter::{GodotAdapter, ProjectAdapter};
use hof_rs::config::GodotConfig;
use hof_rs::tools::endpoint::{game_route_path, load_game_route};
use hof_rs::tools::{McpChannel, ToolChannel};
use serde_json::{json, Value};

/// A loopback JSON-RPC double whose answer depends on the requested tool name.
///
/// `replies` maps an exact `params.name` to the **inner** payload; the server wraps
/// it in the MCP content envelope the real engine uses (`content[0].text` holds the
/// JSON), which is what `unwrap_mcp_payload` reads.
struct RpcDouble {
    addr: SocketAddr,
    tools: Arc<Mutex<Vec<String>>>,
    shutdown: Arc<AtomicBool>,
    handle: Option<JoinHandle<()>>,
    /// DR-71 ①: an optional file whose existence is recorded at every request, so a
    /// test can ask "was the route already visible to a role while this call was in
    /// flight?" — the ordering property itself, not just its end state.
    watch: Arc<Mutex<Option<PathBuf>>>,
    sightings: Arc<Mutex<Vec<(String, bool)>>>,
}

impl RpcDouble {
    fn start(replies: Vec<(String, Value)>) -> Self {
        let listener = TcpListener::bind("127.0.0.1:0").expect("loopback listener");
        let addr = listener.local_addr().expect("bound address");
        listener
            .set_nonblocking(true)
            .expect("non-blocking listener");
        let tools = Arc::new(Mutex::new(Vec::new()));
        let shutdown = Arc::new(AtomicBool::new(false));
        let replies = Arc::new(replies);
        let sightings = Arc::new(Mutex::new(Vec::new()));
        let watch = Arc::new(Mutex::new(None));
        let thread_tools = tools.clone();
        let thread_shutdown = shutdown.clone();
        let thread_sightings = sightings.clone();
        let thread_watch = watch.clone();
        let handle = std::thread::spawn(move || {
            while !thread_shutdown.load(Ordering::SeqCst) {
                match common::accept_blocking(&listener) {
                    Some(stream) => serve(
                        stream,
                        &thread_tools,
                        &replies,
                        &thread_watch,
                        &thread_sightings,
                    ),
                    None => std::thread::sleep(Duration::from_millis(2)),
                }
            }
        });
        Self {
            addr,
            tools,
            shutdown,
            handle: Some(handle),
            watch,
            sightings,
        }
    }

    /// Watch `path`: every later request records whether it exists.
    fn watching(self, path: PathBuf) -> Self {
        *self.watch.lock().expect("watch lock") = Some(path);
        self
    }

    fn sightings(&self) -> Vec<(String, bool)> {
        self.sightings.lock().expect("sightings lock").clone()
    }

    fn url(&self) -> String {
        format!("http://{}/mcp", self.addr)
    }

    fn port(&self) -> u16 {
        self.addr.port()
    }

    fn tools(&self) -> Vec<String> {
        self.tools.lock().expect("tools lock").clone()
    }
}

impl Drop for RpcDouble {
    fn drop(&mut self) {
        self.shutdown.store(true, Ordering::SeqCst);
        let _ = TcpStream::connect(self.addr);
        if let Some(handle) = self.handle.take() {
            let _ = handle.join();
        }
    }
}

fn serve(
    mut stream: TcpStream,
    tools: &Arc<Mutex<Vec<String>>>,
    replies: &Arc<Vec<(String, Value)>>,
    watch: &Arc<Mutex<Option<PathBuf>>>,
    sightings: &Arc<Mutex<Vec<(String, bool)>>>,
) {
    let _ = stream.set_read_timeout(Some(Duration::from_secs(5)));
    let mut buffer = Vec::new();
    let mut chunk = [0u8; 1024];
    let mut header_end = None;
    while header_end.is_none() {
        match stream.read(&mut chunk) {
            Ok(0) | Err(_) => return,
            Ok(read) => buffer.extend_from_slice(&chunk[..read]),
        }
        if let Some(position) = buffer.windows(4).position(|window| window == b"\r\n\r\n") {
            header_end = Some(position + 4);
        }
    }
    let Some(header_end) = header_end else {
        return;
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
    while buffer.len() < header_end + length {
        match stream.read(&mut chunk) {
            Ok(0) | Err(_) => break,
            Ok(read) => buffer.extend_from_slice(&chunk[..read]),
        }
    }
    let body = String::from_utf8_lossy(&buffer[header_end..buffer.len().min(header_end + length)]);
    let request: Value = serde_json::from_str(&body).unwrap_or(json!({}));
    let name = request["params"]["name"]
        .as_str()
        .unwrap_or_default()
        .to_string();
    tools.lock().expect("tools lock").push(name.clone());
    // DR-71 ①: record what a role process would have seen at this instant.
    if let Some(path) = watch.lock().expect("watch lock").as_ref() {
        sightings
            .lock()
            .expect("sightings lock")
            .push((name.clone(), path.exists()));
    }

    let inner = replies
        .iter()
        .find(|(tool, _)| tool == &name)
        .map(|(_, payload)| payload.clone())
        .unwrap_or_else(|| json!({"ok": true}));
    let id = request.get("id").cloned().unwrap_or(json!(0));
    let text = serde_json::to_string(&inner).unwrap_or_default();
    let response = json!({
        "jsonrpc": "2.0",
        "id": id,
        "result": {"content": [{"type": "text", "text": text}], "tools": []},
    });
    let serialized = serde_json::to_string(&response).unwrap_or_default();
    let http = format!(
        "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\
         Connection: close\r\n\r\n{serialized}",
        serialized.len()
    );
    let _ = stream.write_all(http.as_bytes());
    let _ = stream.flush();
}

/// A port nothing is listening on: the readiness poll is refused immediately.
fn closed_port() -> u16 {
    let listener = TcpListener::bind("127.0.0.1:0").expect("probe listener");
    let port = listener.local_addr().expect("probe address").port();
    drop(listener);
    port
}

fn godot_config() -> GodotConfig {
    GodotConfig {
        editor_binary: PathBuf::new(),
        cache_excludes: Vec::new(),
        main_scene: "res://scenes/main.tscn".to_string(),
    }
}

fn adapter() -> GodotAdapter {
    GodotAdapter::new(godot_config(), false).with_battery_limits(BatteryLimits {
        // Short, so a refused poll finishes after the DR-55 verdict instead of
        // burning a production-sized deadline.
        ready_timeout_seconds: 3,
        max_retries: 0,
        timeout_seconds: 5,
    })
}

/// The editor's `editor_play_scene` reply: an endpoint announcement in the engine's
/// documented shape.
fn play_scene_reply(endpoint: String, port: u16) -> Value {
    json!({
        "endpoint": endpoint,
        "mcp_port": port,
        "mcp_port_source": "auto_free_port",
        "pid": std::process::id(),
    })
}

fn run_dir(root: &std::path::Path) -> PathBuf {
    let dir = root.join("runs/run-1");
    std::fs::create_dir_all(&dir).expect("run dir");
    dir
}

/// A game that **never becomes ready** must fail the start and publish nothing.
#[tokio::test]
async fn a_start_that_never_becomes_ready_publishes_no_route() {
    let root = tempfile::tempdir().expect("tempdir");
    let route = game_route_path(&run_dir(root.path()));
    let port = closed_port();
    let editor = RpcDouble::start(vec![(
        "editor_play_scene".to_string(),
        play_scene_reply(format!("http://127.0.0.1:{port}/mcp"), port),
    )]);

    let channel = McpChannel::new(editor.url(), 5, 0);
    channel.use_game_route_file(route.clone());
    let outcome = adapter()
        .start_round_game(root.path(), &channel as &dyn ToolChannel)
        .await;

    assert!(
        outcome.is_err(),
        "a game that never answers the readiness poll must fail the start: {outcome:?}"
    );
    assert!(
        !route.exists(),
        "the record must not be published before readiness is confirmed; found {:?}",
        std::fs::read_to_string(&route)
    );
    assert!(
        channel.game_endpoint().await.is_none(),
        "a failed start must not leave an in-process game route either"
    );
    assert!(
        editor
            .tools()
            .iter()
            .any(|tool| tool == "editor_play_scene"),
        "the double must have been driven through `editor_play_scene`: {:?}",
        editor.tools()
    );
}

/// A game the readiness poll **does** reach must be published with the record the
/// start confirmed.
#[tokio::test]
async fn a_ready_game_is_published_with_the_record_the_start_confirmed() {
    let root = tempfile::tempdir().expect("tempdir");
    let route = game_route_path(&run_dir(root.path()));
    let game = RpcDouble::start(vec![(
        "running_game_get_scene_tree".to_string(),
        json!({"tree": {"name": "Main", "path": "/root/Main"}}),
    )]);
    let editor = RpcDouble::start(vec![(
        "editor_play_scene".to_string(),
        play_scene_reply(game.url(), game.port()),
    )]);

    let channel = McpChannel::new(editor.url(), 5, 0);
    channel.use_game_route_file(route.clone());
    let outcome = adapter()
        .start_round_game(root.path(), &channel as &dyn ToolChannel)
        .await;

    let record = outcome
        .expect("a ready game must start")
        .expect("the Godot adapter offers a round game");
    let published = load_game_route(&route).expect("the confirmed route must be published");
    assert_eq!(
        published, record,
        "the published record must be the one the readiness poll confirmed"
    );
    assert_eq!(
        game.tools(),
        vec!["running_game_get_scene_tree".to_string()],
        "the readiness poll must have gone to the announced game endpoint"
    );
}

/// A publish failure must be **visible**.  DR-70's `register_game_endpoint` threw
/// the result away (`let _ = publish_game_route(...)`) while a comment next to it
/// called the same failure fatal, so the round believed a route existed that every
/// role then failed to reach (A5).
#[tokio::test]
async fn a_publish_failure_is_reported_instead_of_swallowed() {
    let root = tempfile::tempdir().expect("tempdir");
    let route = game_route_path(&run_dir(root.path()));
    // The route path is occupied by a directory, so `publish_game_route` cannot
    // replace it.  The game itself answers, so readiness is confirmed and the
    // failure can only come from the publication.
    std::fs::create_dir_all(&route).expect("obstacle directory");
    let game = RpcDouble::start(vec![(
        "running_game_get_scene_tree".to_string(),
        json!({"tree": {"name": "Main", "path": "/root/Main"}}),
    )]);
    let editor = RpcDouble::start(vec![(
        "editor_play_scene".to_string(),
        play_scene_reply(game.url(), game.port()),
    )]);

    let channel = McpChannel::new(editor.url(), 5, 0);
    channel.use_game_route_file(route.clone());
    let outcome = adapter()
        .start_round_game(root.path(), &channel as &dyn ToolChannel)
        .await;

    assert!(
        outcome.is_err(),
        "a route that could not be published must fail the start, not be swallowed: {outcome:?}"
    );
    assert!(
        route.is_dir(),
        "the obstacle must still be the directory: nothing was published"
    );
    assert!(
        channel.game_endpoint().await.is_none(),
        "a start whose route could not be published must not keep an in-process route"
    );
    assert!(
        !std::fs::read_dir(route.parent().expect("route parent"))
            .expect("run dir")
            .filter_map(Result::ok)
            .any(|entry| entry.file_name().to_string_lossy().contains("tmp-publish")),
        "a failed publish must not leave its temporary file behind"
    );
}

/// DR-71 ①: the same invariant inside the **battery**.  Its `play_scene_ready`
/// step also boots a game, and DR-70 published the announced endpoint before it
/// polled readiness there too — a play that never becomes observable would have
/// left a route for the Tester window (the round stops its own session before the
/// battery, so the battery's route is the only one in that window).
///
/// The game double here **answers**, but not with a scene tree, so the step is
/// unconfirmed while the game endpoint is genuinely in the call path — and the
/// double records whether the route file existed at the moment each request
/// arrived.  Asserting the end state alone would not discriminate: the battery's
/// own `editor_stop_scene` step withdraws the file at the end either way.
#[tokio::test]
async fn an_unconfirmed_battery_play_never_exposes_a_route() {
    let root = tempfile::tempdir().expect("tempdir");
    let workspace = root.path().join("workspace");
    std::fs::create_dir_all(&workspace).expect("workspace");
    let route = game_route_path(&run_dir(root.path()));

    let game = RpcDouble::start(vec![(
        "running_game_get_scene_tree".to_string(),
        // `editor_play_scene`'s own reply is never readiness evidence, and neither
        // is an answer that is not a scene tree.
        json!({"tree": "not a scene tree at all"}),
    )])
    .watching(route.clone());
    let editor = RpcDouble::start(vec![(
        "editor_play_scene".to_string(),
        play_scene_reply(game.url(), game.port()),
    )]);

    let channel = McpChannel::new(editor.url(), 5, 0);
    channel.use_game_route_file(route.clone());
    let records = adapter()
        .evidence_battery(&workspace, &channel as &dyn ToolChannel)
        .await
        .expect("the battery completes and records its steps");

    let play = records
        .iter()
        .find(|record| record.step_id == "play_scene_ready")
        .unwrap_or_else(|| panic!("the battery must declare `play_scene_ready`: {records:?}"));
    assert!(
        !play.ok,
        "a play whose readiness reply is not a scene tree must not be recorded as ok: {play:?}"
    );

    let sightings = game.sightings();
    assert!(
        !sightings.is_empty(),
        "the readiness poll must have reached the announced game endpoint"
    );
    let exposed: Vec<_> = sightings
        .iter()
        .filter(|(_, existed)| *existed)
        .map(|(tool, _)| tool.clone())
        .collect();
    assert!(
        exposed.is_empty(),
        "the battery published the route before it confirmed readiness, so the game endpoint saw \
         it in flight during {exposed:?}; the whole sequence was {sightings:?}"
    );
    assert!(
        !route.exists(),
        "the unconfirmed battery play must not leave a route for the Tester window: {:?}",
        std::fs::read_to_string(&route)
    );
    assert!(
        channel.game_endpoint().await.is_none(),
        "the failed battery play must not leave an in-process route either"
    );
}
