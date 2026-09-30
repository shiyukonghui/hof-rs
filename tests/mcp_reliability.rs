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
use hof_rs::tools::mcp::{McpError, McpTransportError};
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
    /// DR-56: a transport-layer failure — the class the retry ring may retry.
    Transport(McpTransportError),
    /// DR-56: a failure with no classified class at all.
    Plain(String),
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
            Reply::Transport(error) => Err(error.into()),
            Reply::Plain(message) => Err(anyhow::anyhow!(message)),
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
        "running_game_get_scene_tree",
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
        "running_game_get_scene_tree",
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
    assert_eq!(entry["tool"], json!("running_game_get_scene_tree"));
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

/// DR-20 (revised by DR-56): transport failures are retried `max_retries` times
/// and the last **real** failure survives; a success short-circuits the retries.
///
/// The reply is a transport failure rather than a JSON-RPC business error: since
/// DR-56 the retry ring is class-aware and a business error is attempted exactly
/// once, so the only failure class that can still exhaust a retry budget is the
/// transport one.  `retries_are_class_aware_business_errors_are_never_retried`
/// covers the other half.
#[tokio::test]
async fn retries_are_bounded_and_preserve_the_real_error() {
    let message = captured_message("editor_errors_failure.txt");
    let transport = || McpTransportError::new("http://127.0.0.1:9877/mcp", message.clone());
    let channel = ScriptedChannel::new(vec![
        Reply::Transport(transport()),
        Reply::Transport(transport()),
        Reply::Transport(transport()),
    ]);
    let outcome = call_with_retries(
        &channel,
        Role::Tester,
        "editor_get_errors",
        json!({}),
        2,
        0,
        None,
    )
    .await;
    let failure = outcome.expect_err("all attempts failed");
    assert_eq!(failure.attempts, 3, "1 try + 2 retries");
    // A transport failure carries no JSON-RPC code — nothing may invent one.
    assert_eq!(failure.code, None);
    assert!(
        failure.message.contains(&message),
        "the last real failure must survive verbatim: {failure:?}"
    );
    assert_eq!(channel.call_count(), 3);

    let channel = ScriptedChannel::new(vec![
        Reply::Transport(transport()),
        Reply::Ok(json!({"errors": []})),
    ]);
    let value = call_with_retries(
        &channel,
        Role::Tester,
        "editor_get_errors",
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

/// DR-56 ①: a JSON-RPC **business** error is a verdict, not a hiccup.
///
/// `smoke-t6` retried the very same `-32602` three times because
/// `call_with_retries_traced` retried every failure alike.  A contract/argument
/// error cannot become a success by asking again, so it must be attempted
/// **exactly once** — and the returned failure must still be that real error.
#[tokio::test]
async fn retries_are_class_aware_business_errors_are_never_retried() {
    let temp = tempfile::tempdir().unwrap();
    let workspace = temp.path().join("workspace");
    std::fs::create_dir_all(&workspace).unwrap();
    let log = McpErrorLog::new(&workspace);

    // `-32602` is the code the engine really answered for the malformed
    // `save_path`, and the code `smoke-t6` burned three attempts on.
    let parse_error = "-32602 Invalid params: `save_path` must be a res:// or user:// path";
    let channel = ScriptedChannel::new(vec![
        Reply::Err(McpError::new(-32602, parse_error)),
        Reply::Err(McpError::new(-32602, parse_error)),
        Reply::Err(McpError::new(-32602, parse_error)),
    ]);
    let outcome = call_with_retries(
        &channel,
        Role::Tester,
        "running_game_capture_screenshot",
        json!({}),
        2,
        0,
        Some(&log),
    )
    .await;
    let failure = outcome.expect_err("the business error is returned");
    assert_eq!(
        failure.code,
        Some(-32602),
        "the real JSON-RPC code must survive: {failure:?}"
    );
    assert!(
        failure.message.contains("Invalid params"),
        "the real message must survive: {failure:?}"
    );
    assert_eq!(failure.attempts, 1, "a business error is attempted once");
    assert_eq!(
        channel.call_count(),
        1,
        "no second attempt may be made for a business error"
    );

    // Only the single real attempt is journalled — the journal is per failed
    // attempt, so a phantom retry would show up here.
    let raw = std::fs::read_to_string(log.path()).expect("mcp-errors.jsonl");
    let lines: Vec<&str> = raw.lines().filter(|line| !line.trim().is_empty()).collect();
    assert_eq!(lines.len(), 1, "one attempt, one journal line: {raw}");
    let entry: Value = serde_json::from_str(lines[0]).unwrap();
    assert_eq!(entry["code"], json!(-32602));
    assert_eq!(entry["attempt"], json!(1));
}

/// DR-56 ②: the classification is the single decider, and it is asserted on the
/// failure objects the retry ring really builds.
///
/// A classifier that answers "retry" unconditionally is exactly the `smoke-t6`
/// defect, so it is asserted from both directions here (and re-proved
/// non-vacuously by plant-and-revert in the batch report).
#[tokio::test]
async fn the_retry_classifier_is_the_single_decider() {
    // Transport failures: retryable.
    let transport = McpTransportError::new(
        "http://127.0.0.1:65333/mcp",
        "MCP transport failure: Error encountered in the status line",
    );
    let channel = ScriptedChannel::new(vec![
        Reply::Transport(transport.clone()),
        Reply::Transport(transport.clone()),
        Reply::Transport(transport.clone()),
        Reply::Transport(transport),
    ]);
    let failure = call_with_retries(
        &channel,
        Role::Tester,
        "running_game_get_scene_tree",
        json!({}),
        3,
        0,
        None,
    )
    .await
    .expect_err("every attempt is a transport failure");
    assert_eq!(
        channel.call_count(),
        4,
        "a transport failure is retryable, so the ring really retries (DR-56 ②)"
    );
    assert_eq!(failure.attempts, 4, "the last real failure is reported");
    assert_eq!(
        failure.code, None,
        "a transport failure has no JSON-RPC code"
    );
    assert!(
        failure
            .message
            .contains("Error encountered in the status line"),
        "the transport text survives verbatim: {failure:?}"
    );

    // A failure with no classified class is not retryable: a real, unclassified
    // error is reported once instead of being laundered through retries.
    let channel = ScriptedChannel::new(vec![Reply::Plain(
        "game_endpoint_unavailable: no game endpoint is registered".to_string(),
    )]);
    let failure = call_with_retries(
        &channel,
        Role::Tester,
        "running_game_get_scene_tree",
        json!({}),
        3,
        0,
        None,
    )
    .await
    .expect_err("the unclassified failure is returned");
    assert_eq!(
        channel.call_count(),
        1,
        "an unclassified failure must not be retried (DR-56)"
    );
    assert_eq!(failure.attempts, 1);
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
