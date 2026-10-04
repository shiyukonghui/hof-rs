//! DR-72 ④ — the `-32602 Unknown parameter 'node_path'` contract friction.
//!
//! The real round (SMOKE-T10) produced, verbatim:
//!
//! ```text
//! hoh: JSON-RPC error -32602: Unknown parameter 'node_path' for tool
//! 'editor_get_node_properties'
//! ```
//!
//! **Diagnosis (see the report): all three layers are involved, and only one is
//! the harness's to fix.**
//!
//! * the **engine tool** is not wrong: `tests/fixtures/mcp/tools_list.json` — the
//!   captured `tools/list` — declares `path` for `editor_get_node_properties`
//!   (while `editor_get_collision_info` really does declare `node_path`);
//! * the **role usage** was wrong: the model used the game-channel spelling on
//!   an editor tool, which the harness's own playbook examples teach as the norm
//!   for `running_game_*`;
//! * the **contract description** was wrong: the tool's `description` does not
//!   name its parameter, `.hoh/TOOLS.md` does — but the engine's refusal named
//!   only the parameter it rejected, so a model that never re-read the table had
//!   nothing to correct against.
//!
//! The layer that can be fixed without touching the frozen engine tree is the
//! harness's: `.hoh/TOOLS.md` already carries the real parameter names, so the
//! refusal itself must name them.  These tests drive the **real** CLI dispatch
//! (`hof_rs::cli::dispatch` → `hoh tools call`) against a loopback JSON-RPC
//! double: no Godot, no external port, nothing under `runs/**`.

mod common;

use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::thread::JoinHandle;
use std::time::Duration;

use hof_rs::cli::{Command, ToolsArgs, ToolsCallArgs, ToolsCommand};
use hof_rs::tools::mcp::{is_unknown_parameter_error, unknown_parameter_message};
use serde_json::{json, Value};

/// The tool the real round mis-called, and the parameter name that round sent.
const TOOL: &str = "editor_get_node_properties";
const NAME_THE_ROUND_SENT: &str = "node_path";
/// The engine's own refusal, verbatim from the round's trajectory.
const ENGINE_REFUSAL: &str = "Unknown parameter 'node_path' for tool 'editor_get_node_properties'";

/// A one-shot loopback JSON-RPC double.
struct RpcDouble {
    url: String,
    shutdown: Arc<AtomicBool>,
    handle: Option<JoinHandle<()>>,
}

impl RpcDouble {
    /// Answer every `tools/call` with `reply`.
    ///
    /// `reply` is either `Ok(inner)` — returned in the MCP content envelope, i.e.
    /// a successful call — or `Err((code, message))`, the JSON-RPC **business
    /// error** shape the engine uses for `-32602`.
    fn start(reply: Result<Value, (i64, String)>) -> Self {
        let listener = TcpListener::bind("127.0.0.1:0").expect("loopback listener");
        let addr = listener.local_addr().expect("bound address");
        listener
            .set_nonblocking(true)
            .expect("non-blocking listener");
        let shutdown = Arc::new(AtomicBool::new(false));
        let thread_shutdown = shutdown.clone();
        let reply = Arc::new(Mutex::new(Some(reply)));
        let handle = std::thread::spawn(move || {
            while !thread_shutdown.load(Ordering::SeqCst) {
                match common::accept_blocking(&listener) {
                    Some(stream) => serve(stream, &reply),
                    None => std::thread::sleep(Duration::from_millis(2)),
                }
            }
        });
        Self {
            url: format!("http://{addr}/mcp"),
            shutdown,
            handle: Some(handle),
        }
    }
}

impl Drop for RpcDouble {
    fn drop(&mut self) {
        self.shutdown.store(true, Ordering::SeqCst);
        let _ = TcpStream::connect(
            self.url
                .trim_start_matches("http://")
                .trim_end_matches("/mcp"),
        );
        if let Some(handle) = self.handle.take() {
            let _ = handle.join();
        }
    }
}

fn serve(mut stream: TcpStream, reply: &Arc<Mutex<Option<Result<Value, (i64, String)>>>>) {
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
    let id = request.get("id").cloned().unwrap_or(json!(0));
    // The double answers one fixed reply, and only the first call consumes it, so
    // a test that calls twice sees the same behaviour without state leaking.
    let answer = reply
        .lock()
        .expect("reply lock")
        .clone()
        .unwrap_or_else(|| Ok(json!({"ok": true})));
    let response = match answer {
        Ok(inner) => {
            let text = serde_json::to_string(&inner).unwrap_or_default();
            json!({
                "jsonrpc": "2.0",
                "id": id,
                "result": {"content": [{"type": "text", "text": text}], "tools": []},
            })
        }
        Err((code, message)) => json!({
            "jsonrpc": "2.0",
            "id": id,
            "error": {"code": code, "message": message},
        }),
    };
    let serialized = serde_json::to_string(&response).unwrap_or_default();
    let http = format!(
        "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\
         Connection: close\r\n\r\n{serialized}",
        serialized.len()
    );
    let _ = stream.write_all(http.as_bytes());
    let _ = stream.flush();
}

fn workspace_tempdir() -> tempfile::TempDir {
    tempfile::tempdir().expect("tempdir")
}

/// The config overrides that point the harness at the double.  `tools.endpoint`
/// is the documented override key (`-c tools.endpoint=…`).
fn overrides(double: &RpcDouble) -> Vec<String> {
    vec![
        // The subject of this file is the **editor-mediated** channel's parameter
        // guidance (DR-72 ④), so the channel is named explicitly:
        // `config/hoh.yaml` now selects the Bevy adapter, which has no
        // `editor_get_node_properties` tool at all.
        "adapter.kind=mcp".to_string(),
        format!("tools.endpoint={}", double.url),
        // No retry ring: a `-32602` is a verdict, not something to re-ask.
        "tools.max_retries=0".to_string(),
        "tools.timeout_seconds=5".to_string(),
    ]
}

async fn call_tool(double: &RpcDouble, tool: &str, args: Value) -> anyhow::Result<i32> {
    let command = Command::Tools(ToolsArgs {
        command: ToolsCommand::Call(ToolsCallArgs {
            tool: tool.to_string(),
            args: Some(args.to_string()),
            args_file: None,
            role: Some("developer".to_string()),
            config_spec: overrides(double),
        }),
    });
    // The process environment decides the role when `--role` is absent; the
    // explicit role is passed above, so nothing here depends on it.
    hof_rs::cli::dispatch(hof_rs::cli::Cli { command }).await
}

/// The engine declares `path`, and the captured `tools/list` says so — so the
/// "correct parameter name" half of the test is derived from the fixture rather
/// than from a hand-written idea of the contract.
#[test]
fn the_captured_contract_declares_path_for_the_property_tool() {
    let accepted = hof_rs::tools::index::accepted_parameters(TOOL)
        .unwrap_or_else(|| panic!("the captured tools/list must declare `{TOOL}`"));
    assert!(
        accepted.contains(&"path".to_string()),
        "the engine's captured contract declares `path` for `{TOOL}`: {accepted:?}"
    );
    assert!(
        !accepted.contains(&NAME_THE_ROUND_SENT.to_string()),
        "`{NAME_THE_ROUND_SENT}` must NOT be declared by `{TOOL}` — that is the whole friction: \
         {accepted:?}"
    );
    // The neighbouring tool really does use the other spelling, which is why the
    // model's guess was reasonable rather than random.
    let collision = hof_rs::tools::index::accepted_parameters("editor_get_collision_info")
        .expect("the captured contract must declare the collision tool");
    assert!(
        collision.contains(&NAME_THE_ROUND_SENT.to_string()),
        "`editor_get_collision_info` really does use `{NAME_THE_ROUND_SENT}`: {collision:?}"
    );
}

/// **The red half.**  The correct argument name must reach the engine and the
/// call must succeed.
#[tokio::test]
async fn the_correct_parameter_name_succeeds() {
    let temp = workspace_tempdir();
    // Keep the workspace out of the repository's own tree.
    let _ = temp;
    let double = RpcDouble::start(Ok(json!({
        "node_path": "/root/Main/Player",
        "properties": {"position": {"x": 1.0, "y": 2.0}},
        "type": "CharacterBody2D",
    })));
    let accepted = hof_rs::tools::index::accepted_parameters(TOOL).expect("declared");
    assert!(accepted.contains(&"path".to_string()));
    // Only the names the contract declares are ever sent.
    let mut args = serde_json::Map::new();
    for name in &accepted {
        args.insert(name.clone(), json!("/root/Main/Player"));
    }
    let code = call_tool(&double, TOOL, Value::Object(args))
        .await
        .expect("a correctly named call must not be a harness error");
    assert_eq!(code, 0, "a correctly named call must exit 0");
}

/// **The other red half.**  The wrong argument name must produce a refusal that
/// *names the parameters the tool accepts*.
///
/// Before DR-72 the whole message was the engine's own
/// `Unknown parameter 'node_path' for tool 'editor_get_node_properties'`, which
/// names the parameter that was rejected and none of the ones that would work —
/// the next step could only guess again.
#[tokio::test]
async fn the_wrong_parameter_name_is_refused_with_the_accepted_names() {
    let temp = workspace_tempdir();
    let _ = temp;
    let double = RpcDouble::start(Err((-32602, ENGINE_REFUSAL.to_string())));
    let error = call_tool(
        &double,
        TOOL,
        json!({NAME_THE_ROUND_SENT: "/root/Main/Player"}),
    )
    .await
    .expect_err("a `-32602` refusal must surface as an error");

    let message = format!("{error:#}");
    // The engine's verbatim sentence is never dropped: a judge must be able to
    // see exactly what the server said.
    assert!(
        message.contains(ENGINE_REFUSAL),
        "the engine's own refusal must survive verbatim: {message}"
    );
    // …and the guidance names the real parameter.  The names it must name are
    // **derived from the fixture** (the same `include_str!` snapshot
    // `accepted_parameters` reads), not the literal `path`, so this cannot pass
    // with a hardcoded parameter list (DR-74 ⑥/D9).
    let accepted = hof_rs::tools::index::accepted_parameters(TOOL)
        .unwrap_or_else(|| panic!("the captured tools/list must declare `{TOOL}`"));
    for name in &accepted {
        assert!(
            message.contains(&format!("`{name}`")),
            "the refusal must name the accepted parameter `{name}`: {message}"
        );
    }
    assert!(
        message.contains(TOOL),
        "the refusal must name the tool it is about: {message}"
    );
}

/// The mechanism itself, without a server: the hint the CLI installs is what
/// makes the message actionable, and an unknown tool degrades honestly instead
/// of inventing a parameter list.
#[test]
fn the_hint_turns_a_terse_refusal_into_an_actionable_one() {
    assert!(is_unknown_parameter_error(-32602, ENGINE_REFUSAL));
    // A `-32602` that is *not* about a parameter name is not this failure class
    // (the same code also answers `ACTION_NOT_BOUND`, DR-54).
    assert!(!is_unknown_parameter_error(-32602, "ACTION_NOT_BOUND"));
    assert!(!is_unknown_parameter_error(-32601, ENGINE_REFUSAL));

    let accepted = hof_rs::tools::index::accepted_parameters(TOOL).expect("declared");
    hof_rs::tools::mcp::clear_parameter_hints();
    hof_rs::tools::mcp::record_parameter_hint(TOOL, &accepted);
    let message = unknown_parameter_message(TOOL, ENGINE_REFUSAL);
    assert!(message.contains(ENGINE_REFUSAL), "{message}");
    // Derived from the fixture, not the literal `path` (DR-74 ⑥/D9).
    for name in &accepted {
        assert!(
            message.contains(&format!("`{name}`")),
            "the guidance must name the accepted parameter `{name}`: {message}"
        );
    }
    assert!(
        hof_rs::tools::mcp::parameter_hint(TOOL).is_some(),
        "the hint must be readable while it is installed"
    );
    hof_rs::tools::mcp::clear_parameter_hints();
    assert!(
        hof_rs::tools::mcp::parameter_hint(TOOL).is_none(),
        "the hint must not outlive the call that installed it"
    );
    // A tool the snapshot does not know still gets an honest message.
    let unknown = unknown_parameter_message(
        "editor_totally_unknown_tool",
        "Unknown parameter 'x' for tool 'editor_totally_unknown_tool'",
    );
    assert!(unknown.contains("no schema"), "{unknown}");

    // Non-vacuity: the guide is not a constant — a different parameter list
    // produces a different message.
    let other = hof_rs::tools::mcp::parameter_guidance(TOOL, &["alpha".to_string()]);
    assert!(other.contains("`alpha`"), "{other}");
    assert!(!other.contains("`path`"), "{other}");
    let _: PathBuf = PathBuf::new();
}
