//! DR-70 ①: the game route must cover the **whole round**.
//!
//! DR-69 published the route inside the battery's `editor_play_scene` step
//! (`src/adapter/godot.rs`), which the runtime reaches *after* the Developer and
//! *before* the Tester (`src/runtime/run_loop.rs`).  The acceptance measured the
//! consequence (D1, major): in the normal flow **no role process ever overlapped
//! the route's lifetime**, so every role's `hoh tools call running_game_*` still
//! ended in `game_endpoint_unavailable`; the only overlap was a by-product of a
//! battery error.
//!
//! These tests drive the **real** `run_loop::run` with the real phase order and,
//! *inside* the Developer and Tester steps, start the **real `hoh` binary** as a
//! role shell would.  They assert the property the task book asks for: the
//! publish window **contains** the role window, and a role process actually reads
//! the published route.

mod common;

use std::io::{Read, Write};
use std::net::{SocketAddr, TcpListener, TcpStream};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::thread::JoinHandle;
use std::time::Duration;

use common::{run_scenario_with_tools, FakeAdapter, FakeStep, RoundGameStub};
use hof_rs::model::{Ablation, Role};
use hof_rs::tools::endpoint::game_route_path;
use hof_rs::tools::{McpChannel, ToolChannel};
use serde_json::{json, Value};

/// A loopback JSON-RPC double: it records the tool names it was asked for and
/// answers every request with a `tools/list`-shaped result.
struct LoopbackMcp {
    addr: SocketAddr,
    tools: Arc<Mutex<Vec<String>>>,
    shutdown: Arc<AtomicBool>,
    handle: Option<JoinHandle<()>>,
}

impl LoopbackMcp {
    fn start() -> Self {
        let listener = TcpListener::bind("127.0.0.1:0").expect("loopback listener");
        let addr = listener.local_addr().expect("bound address");
        listener
            .set_nonblocking(true)
            .expect("non-blocking listener");
        let tools = Arc::new(Mutex::new(Vec::new()));
        let shutdown = Arc::new(AtomicBool::new(false));
        let thread_tools = tools.clone();
        let thread_shutdown = shutdown.clone();
        let handle = std::thread::spawn(move || {
            while !thread_shutdown.load(Ordering::SeqCst) {
                match common::accept_blocking(&listener) {
                    Some(stream) => serve(stream, &thread_tools),
                    None => std::thread::sleep(Duration::from_millis(2)),
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

    fn tools(&self) -> Vec<String> {
        self.tools.lock().expect("tools lock").clone()
    }
}

impl Drop for LoopbackMcp {
    fn drop(&mut self) {
        self.shutdown.store(true, Ordering::SeqCst);
        let _ = TcpStream::connect(self.addr);
        if let Some(handle) = self.handle.take() {
            let _ = handle.join();
        }
    }
}

fn serve(mut stream: TcpStream, tools: &Arc<Mutex<Vec<String>>>) {
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
    if let Some(name) = request["params"]["name"].as_str() {
        tools.lock().expect("tools lock").push(name.to_string());
    }
    let id = request.get("id").cloned().unwrap_or(json!(0));
    let inner = json!({"tree": {"name": "Main", "path": "/root/Main"}}).to_string();
    let body = json!({
        "jsonrpc": "2.0",
        "id": id,
        "result": {"content": [{"type": "text", "text": inner}], "tools": []},
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

/// One observation of "can a role reach the game right now?", taken from inside
/// a scripted role step.
#[derive(Clone, Debug)]
struct RoleProbe {
    route_exists: bool,
    exit_code: Option<i32>,
    stdout: String,
    stderr: String,
}

impl RoleProbe {
    fn combined(&self) -> String {
        format!("{}{}", self.stdout, self.stderr)
    }
}

/// Run the **real `hoh` binary** exactly as a role's shell would, and record what
/// the role could see at that moment.
fn probe_as_role(route: &Path, editor_url: &str) -> RoleProbe {
    let output = Command::new(env!("CARGO_BIN_EXE_hoh"))
        .args([
            "tools",
            "call",
            "running_game_get_scene_tree",
            "--role",
            "developer",
            "-c",
            &format!("tools.endpoint={editor_url}"),
            "-c",
            "tools.max_retries=0",
            "-c",
            "tools.timeout_seconds=5",
        ])
        .current_dir(PathBuf::from(env!("CARGO_MANIFEST_DIR")))
        .env("HOH_GAME_ROUTE", route)
        .output()
        .expect("the hoh binary must be runnable");
    RoleProbe {
        route_exists: route.exists(),
        exit_code: output.status.code(),
        stdout: String::from_utf8_lossy(&output.stdout).into_owned(),
        stderr: String::from_utf8_lossy(&output.stderr).into_owned(),
    }
}

fn run_root() -> tempfile::TempDir {
    tempfile::tempdir().expect("tempdir")
}

fn route_of(root: &Path) -> PathBuf {
    game_route_path(&root.join("runs/run-1"))
}

/// A role shell intermediary: every probe appends its observation to `sink`.
fn recording_probe(
    route: PathBuf,
    editor_url: String,
    sink: Arc<Mutex<Vec<RoleProbe>>>,
) -> impl Fn() + Send + Sync + 'static {
    move || {
        let probe = probe_as_role(&route, &editor_url);
        sink.lock().expect("sink lock").push(probe);
    }
}

/// The headline property: a real role process reaches the game endpoint **during
/// the Developer step** and **during the Tester step** — i.e. the publish window
/// contains the role window, which is exactly what DR-69 lacked.
#[tokio::test]
async fn the_published_route_covers_the_developer_and_tester_windows() {
    let root = run_root();
    let editor = LoopbackMcp::start();
    let game = LoopbackMcp::start();
    let route = route_of(root.path());
    let stub = Arc::new(RoundGameStub::new(
        game.url(),
        game.port(),
        std::process::id(),
    ));

    let observed: Arc<Mutex<Vec<RoleProbe>>> = Arc::new(Mutex::new(Vec::new()));
    let developer_step = FakeStep::new(Role::Developer)
        .writing("project.godot", "config_version=5\n")
        .probing(recording_probe(
            route.clone(),
            editor.url(),
            observed.clone(),
        ));
    let tester_step = FakeStep::new(Role::Tester)
        .writing(".hoh/evidence/move.json", "{\"moved\":true}\n")
        .writing(".hoh/evidence.json", &common::ok_evidence(1, ""))
        .probing(recording_probe(
            route.clone(),
            editor.url(),
            observed.clone(),
        ));
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", common::OK_PLAN),
        developer_step,
        tester_step,
    ];

    let channel: Arc<dyn ToolChannel> = Arc::new(McpChannel::new(editor.url(), 5, 0));
    let adapter = FakeAdapter::new().with_round_game(stub.clone());
    let (result, _records) = run_scenario_with_tools(
        root.path(),
        1,
        script,
        Ablation::default(),
        adapter,
        channel,
    )
    .await;
    assert!(result.is_ok(), "the scenario must complete: {result:?}");

    let probes = observed.lock().expect("sink lock").clone();
    assert_eq!(
        probes.len(),
        2,
        "the Developer and the Tester steps must each have probed the role shell"
    );
    for (index, label) in [(0usize, "Developer"), (1usize, "Tester")] {
        let probe = &probes[index];
        assert!(
            probe.route_exists,
            "entering the {label} phase the published route must already exist: {probe:?}"
        );
        assert_eq!(
            probe.exit_code,
            Some(0),
            "a real role shell must reach the game endpoint during the {label} phase\n{}",
            probe.combined()
        );
        assert!(
            !probe.combined().contains("game_endpoint_unavailable"),
            "the {label}'s call must not be refused: {}",
            probe.combined()
        );
    }

    assert_eq!(
        game.tools(),
        vec![
            "running_game_get_scene_tree".to_string(),
            "running_game_get_scene_tree".to_string()
        ],
        "the game endpoint must have served both role calls"
    );
    assert!(
        !editor
            .tools()
            .iter()
            .any(|tool| tool.starts_with("running_game_")),
        "the editor endpoint must never receive a running_game_* request: {:?}",
        editor.tools()
    );

    // The window is opened and closed around the roles, not inside the battery.
    assert!(
        stub.starts() >= 2,
        "the round's session must be started for the Developer window and again for the \
         Tester window, saw {}",
        stub.starts()
    );
    assert!(
        stub.stops() >= 2,
        "the battery's own game must not overlap the round's session, saw {}",
        stub.stops()
    );
    assert!(
        !route.exists(),
        "the route must be withdrawn when the round ends"
    );
}

/// The route must not outlive the round even when the round **fails**: the
/// contract gate returns `Err` before the battery ever runs, which is the error
/// path DR-69's acceptance found leaving the file behind.
#[tokio::test]
async fn a_failing_round_still_withdraws_the_published_route() {
    let root = run_root();
    let editor = LoopbackMcp::start();
    let game = LoopbackMcp::start();
    let route = route_of(root.path());
    let stub = Arc::new(RoundGameStub::new(
        game.url(),
        game.port(),
        std::process::id(),
    ));

    let observed: Arc<Mutex<Vec<RoleProbe>>> = Arc::new(Mutex::new(Vec::new()));
    // A Developer that changes nothing trips the `NoEngineeringWrite` contract
    // gate, so the round returns `Err` before the battery.
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", common::OK_PLAN),
        FakeStep::new(Role::Developer).probing(recording_probe(
            route.clone(),
            editor.url(),
            observed.clone(),
        )),
    ];

    let channel: Arc<dyn ToolChannel> = Arc::new(McpChannel::new(editor.url(), 5, 0));
    let adapter = FakeAdapter::new().with_round_game(stub.clone());
    let (result, _records) = run_scenario_with_tools(
        root.path(),
        1,
        script,
        Ablation::default(),
        adapter,
        channel,
    )
    .await;
    assert!(result.is_err(), "the contract gate must fail the round");

    let probes = observed.lock().expect("sink lock").clone();
    assert_eq!(probes.len(), 1);
    assert!(
        probes[0].route_exists,
        "the route must still have been published for the Developer: {:?}",
        probes[0]
    );
    assert_eq!(
        probes[0].exit_code,
        Some(0),
        "the Developer's shell must have reached the game\n{}",
        probes[0].combined()
    );
    assert!(
        stub.stops() >= 1,
        "the error path must tear the session down"
    );
    assert!(
        !route.exists(),
        "a round that failed before the battery must still withdraw its published route"
    );
}

/// A route left behind by an earlier round must **not** be inherited, however
/// healthy it looks: the runtime withdraws the file before anything can adopt it,
/// so a role never reaches another round's game.
#[tokio::test]
async fn a_route_left_by_another_round_is_not_inherited() {
    let root = run_root();
    let editor = LoopbackMcp::start();
    let decoy = LoopbackMcp::start();
    let route = route_of(root.path());

    // An earlier round's record: live endpoint, live pid, fresh file — it passes
    // every check DR-70 ② makes, which is exactly why the *runtime* has to take
    // it out of the way.
    std::fs::create_dir_all(route.parent().expect("route parent")).expect("run dir");
    std::fs::write(
        &route,
        serde_json::to_string(&json!({
            "endpoint": decoy.url(),
            "port": decoy.port(),
            "source": "auto_free_port",
            "pid": std::process::id(),
        }))
        .expect("route json"),
    )
    .expect("planted route");

    let observed: Arc<Mutex<Vec<RoleProbe>>> = Arc::new(Mutex::new(Vec::new()));
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", common::OK_PLAN),
        FakeStep::new(Role::Developer)
            .writing("project.godot", "config_version=5\n")
            .probing(recording_probe(
                route.clone(),
                editor.url(),
                observed.clone(),
            )),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{\"moved\":true}\n")
            .writing(".hoh/evidence.json", &common::ok_evidence(1, "")),
    ];

    let channel: Arc<dyn ToolChannel> = Arc::new(McpChannel::new(editor.url(), 5, 0));
    // No round game: nothing republishes the file, so what the role sees is
    // purely what the runtime did with the leftover.
    let adapter = FakeAdapter::new();
    let (result, _records) = run_scenario_with_tools(
        root.path(),
        1,
        script,
        Ablation::default(),
        adapter,
        channel,
    )
    .await;
    assert!(result.is_ok(), "the scenario must complete: {result:?}");

    let probes = observed.lock().expect("sink lock").clone();
    assert_eq!(probes.len(), 1);
    assert!(
        !probes[0].route_exists,
        "the leftover route must be withdrawn before any role runs: {:?}",
        probes[0]
    );
    assert_ne!(
        probes[0].exit_code,
        Some(0),
        "with the leftover gone there is no game route, so the call must fail: {}",
        probes[0].combined()
    );
    assert!(
        probes[0].combined().contains("game_endpoint_unavailable"),
        "the failure must be DR-43's explicit refusal: {}",
        probes[0].combined()
    );
    assert!(
        decoy.tools().is_empty(),
        "another round's game must never be reached: {:?}",
        decoy.tools()
    );
}
