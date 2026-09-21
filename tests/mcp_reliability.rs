//! DR-20 — MCP readiness waiting, bounded retries, and diagnosable failures.
//!
//! The first real smoke run produced `-32603 无法打开日志文件`,
//! `等待游戏响应超时 (5秒)` and `截图文件不存在…MCPScreenshot autoload 未激活`,
//! plus a `--args-file` resolution failure.  None of these may be silently
//! reinterpreted as "no errors".

use std::collections::VecDeque;
use std::path::Path;
use std::sync::Mutex;

use hof_rs::model::Role;
use hof_rs::tools::mcp::McpError;
use hof_rs::tools::reliable::{
    call_with_retries, wait_for_game_ready, McpErrorLog, READY_POLL_INTERVAL_MS, RETRY_INTERVAL_MS,
};
use hof_rs::tools::{ToolChannel, ToolResult};
use serde_json::{json, Value};

/// Real captured stderr of the first smoke run (see `tests/fixtures/mcp`).
fn fixture(name: &str) -> String {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/fixtures/mcp")
        .join(name);
    std::fs::read_to_string(&path).unwrap_or_else(|error| panic!("{path:?}: {error}"))
}

/// The `message` half of a captured `hoh: JSON-RPC error <code>: <message>` line.
fn captured_message(name: &str) -> String {
    let raw = fixture(name);
    raw.trim_start_matches("hoh: ").to_string()
}

#[derive(Clone)]
enum Reply {
    Ok(Value),
    Err(McpError),
}

#[derive(Default)]
struct ScriptedChannel {
    replies: Mutex<VecDeque<Reply>>,
    calls: Mutex<Vec<String>>,
}

impl ScriptedChannel {
    fn new(replies: Vec<Reply>) -> Self {
        Self {
            replies: Mutex::new(replies.into()),
            calls: Mutex::new(Vec::new()),
        }
    }

    fn call_count(&self) -> usize {
        self.calls.lock().unwrap().len()
    }
}

#[async_trait::async_trait]
impl ToolChannel for ScriptedChannel {
    fn allowed(&self, _role: Role, _tool: &str) -> bool {
        true
    }

    fn index_markdown(&self, _role: Role) -> String {
        String::new()
    }

    async fn call(&self, _role: Role, tool: &str, _args: Value) -> anyhow::Result<ToolResult> {
        self.calls.lock().unwrap().push(tool.to_string());
        let reply = self
            .replies
            .lock()
            .unwrap()
            .pop_front()
            .unwrap_or_else(|| panic!("ScriptedChannel ran out of replies for `{tool}`"));
        match reply {
            Reply::Ok(payload) => Ok(ToolResult { ok: true, payload }),
            Reply::Err(error) => Err(error.into()),
        }
    }
}

/// DR-20: the documented intervals are 500 ms (readiness) and 1 s (retries).
#[test]
fn the_documented_intervals_are_not_negotiable() {
    assert_eq!(READY_POLL_INTERVAL_MS, 500);
    assert_eq!(RETRY_INTERVAL_MS, 1000);
}

/// DR-20 ①: three failures, then the game answers — the poll succeeds and the
/// call count is exactly the number of attempts it took.
#[tokio::test]
async fn readiness_poll_succeeds_after_three_failures() {
    let timeout_message = captured_message("editor_errors_failure.txt");
    let channel = ScriptedChannel::new(vec![
        Reply::Err(McpError::new(-32603, timeout_message.clone())),
        Reply::Err(McpError::new(-32603, timeout_message.clone())),
        Reply::Err(McpError::new(-32603, timeout_message.clone())),
        Reply::Ok(json!({"tree": {"name": "Main"}})),
    ]);

    let outcome = wait_for_game_ready(
        &channel,
        Role::Tester,
        "get_game_scene_tree",
        json!({}),
        30,
        /* poll interval for the test only */ 5,
        None,
    )
    .await;

    assert!(outcome.ok, "the poll must succeed: {outcome:?}");
    assert_eq!(outcome.attempts, 4, "three failures plus one success");
    assert_eq!(channel.call_count(), 4);
    assert_eq!(
        outcome.payload.as_ref().unwrap()["tree"]["name"],
        json!("Main")
    );
}

/// DR-20 ②: a timeout is reported as a failure, and the verbatim JSON-RPC
/// code/message is written to `.hoh/deterministic/mcp-errors.jsonl`.
#[tokio::test]
async fn readiness_timeout_is_recorded_verbatim() {
    let temp = tempfile::tempdir().unwrap();
    let workspace = temp.path().join("workspace");
    std::fs::create_dir_all(&workspace).unwrap();
    let log = McpErrorLog::new(&workspace);

    let message = captured_message("screenshot_failure.txt");
    let channel = ScriptedChannel::new(vec![Reply::Err(McpError::new(-32603, message.clone()))]);

    let outcome = wait_for_game_ready(
        &channel,
        Role::Tester,
        "get_game_scene_tree",
        json!({}),
        /* timeout */ 0,
        5,
        Some(&log),
    )
    .await;

    assert!(!outcome.ok, "a zero-budget wait cannot succeed");
    let failure = outcome.failure.as_ref().expect("a failure is recorded");
    assert_eq!(failure.code, Some(-32603));
    assert!(failure.message.contains("截图文件不存在"), "{failure:?}");
    assert!(failure.observation().contains("FAILED"), "{failure:?}");
    assert!(
        failure.observation().contains("UNAVAILABLE") || failure.observation().contains("FAILED")
    );

    let raw = std::fs::read_to_string(log.path()).expect("mcp-errors.jsonl");
    let lines: Vec<&str> = raw.lines().filter(|line| !line.trim().is_empty()).collect();
    assert_eq!(lines.len(), 1, "one failure, one line: {raw}");
    let entry: Value = serde_json::from_str(lines[0]).expect("jsonl line");
    assert_eq!(entry["tool"], json!("get_game_scene_tree"));
    assert_eq!(entry["code"], json!(-32603));
    assert_eq!(entry["attempt"], json!(1));
    assert!(
        entry["message"]
            .as_str()
            .unwrap()
            .contains("截图文件不存在"),
        "{entry}"
    );
    assert!(entry["timestamp"].is_u64(), "{entry}");
}

/// DR-20: `get_editor_errors` failures are retried `max_retries` times and the
/// last real error survives; a success short-circuits the retries.
#[tokio::test]
async fn retries_are_bounded_and_preserve_the_real_error() {
    let message = captured_message("editor_errors_failure.txt");
    let channel = ScriptedChannel::new(vec![
        Reply::Err(McpError::new(-32603, message.clone())),
        Reply::Err(McpError::new(-32603, message.clone())),
        Reply::Err(McpError::new(-32603, message.clone())),
    ]);
    let outcome = call_with_retries(
        &channel,
        Role::Tester,
        "get_editor_errors",
        json!({}),
        2,
        0,
        None,
    )
    .await;
    let failure = outcome.expect_err("all attempts failed");
    assert_eq!(failure.attempts, 3, "1 try + 2 retries");
    assert_eq!(failure.code, Some(-32603));
    assert_eq!(channel.call_count(), 3);

    let channel = ScriptedChannel::new(vec![
        Reply::Err(McpError::new(-32603, message)),
        Reply::Ok(json!({"errors": []})),
    ]);
    let value = call_with_retries(
        &channel,
        Role::Tester,
        "get_editor_errors",
        json!({}),
        2,
        0,
        None,
    )
    .await
    .expect("the second attempt succeeds");
    assert_eq!(value, json!({"errors": []}));
    assert_eq!(channel.call_count(), 2);
}

/// DR-20: `--args-file` accepts an absolute path, and a missing file names the
/// absolute path it expected (the first smoke run failed with a bare relative
/// path that could not be located).
#[test]
fn args_file_resolution_is_absolute_and_diagnosable() {
    let temp = tempfile::tempdir().unwrap();
    let existing = temp.path().join("args.json");
    std::fs::write(&existing, r#"{"node_path": "/root/Main/Player"}"#).unwrap();
    let value = hof_rs::tools::bridge::parse_args(None, Some(&existing)).unwrap();
    assert_eq!(value["node_path"], json!("/root/Main/Player"));

    let missing = temp.path().join("nested/does_not_exist.json");
    let error = hof_rs::tools::bridge::parse_args(None, Some(&missing))
        .expect_err("a missing args file must fail");
    let text = error.to_string();
    assert!(
        text.contains(&missing.to_string_lossy().to_string()),
        "the error must name the expected path: {text}"
    );
    assert!(
        !text.contains("nested/does_not_exist.json\"")
            || text.contains(temp.path().to_str().unwrap()),
        "the path must be absolute: {text}"
    );

    // A relative path is resolved against the working directory and reported
    // as an absolute path.
    let relative = Path::new("this/relative/file-does-not-exist.json");
    let error = hof_rs::tools::bridge::parse_args(None, Some(relative)).unwrap_err();
    let text = error.to_string();
    let cwd = std::env::current_dir().unwrap();
    assert!(
        text.contains(&cwd.to_string_lossy().replace('\\', "/"))
            || text.contains(&cwd.to_string_lossy().to_string()),
        "the relative path must be reported absolutely ({cwd:?}): {text}"
    );
}
