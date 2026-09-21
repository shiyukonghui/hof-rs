//! DR-20: reliable MCP calls — readiness polling, bounded retries, and a
//! verbatim error journal.
//!
//! The first real smoke run failed with three distinct `-32603` errors and one
//! readiness timeout.  Two rules follow from that:
//!
//! 1. a failure is *evidence that the evidence is unavailable* — it must be
//!    recorded with its raw `code`/`message`, never reinterpreted as "no
//!    errors"; and
//! 2. calls that depend on the running game must wait for the game to exist
//!    before they are attempted, instead of reading a half-started scene.

use std::path::{Path, PathBuf};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

use serde_json::Value;

use crate::model::Role;
use crate::tools::mcp::McpError;
use crate::tools::ToolChannel;

/// The documented readiness poll interval (DR-20).
pub const READY_POLL_INTERVAL_MS: u64 = 500;
/// The documented retry interval (DR-20).
pub const RETRY_INTERVAL_MS: u64 = 1000;

/// One failed MCP call, with the JSON-RPC identity preserved.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct McpFailure {
    pub tool: String,
    /// `Some(code)` when the server answered with a JSON-RPC error.
    pub code: Option<i64>,
    pub message: String,
    /// How many attempts had been made when this failure was recorded.
    pub attempts: u32,
}

impl McpFailure {
    pub fn new(tool: &str, code: Option<i64>, message: impl Into<String>, attempts: u32) -> Self {
        Self {
            tool: tool.to_string(),
            code,
            message: message.into(),
            attempts,
        }
    }

    /// The failure text carried into `BatteryRecord.observation`.
    ///
    /// It always contains `FAILED` and `UNAVAILABLE` so a downstream judge can
    /// never mistake an unavailable evidence step for a clean one (DR-20/DR-17).
    pub fn observation(&self) -> String {
        let code = self
            .code
            .map(|code| code.to_string())
            .unwrap_or_else(|| "n/a".to_string());
        format!(
            "FAILED tool={} attempt(s)={} code={} message={} \
             (UNAVAILABLE: this evidence could not be collected)",
            self.tool, self.attempts, code, self.message
        )
    }
}

/// The append-only journal of every failed MCP attempt, at
/// `<workspace>/.hoh/deterministic/mcp-errors.jsonl`.
#[derive(Clone, Debug)]
pub struct McpErrorLog {
    path: PathBuf,
}

impl McpErrorLog {
    pub fn new(workspace: &Path) -> Self {
        Self {
            path: workspace.join(".hoh/deterministic/mcp-errors.jsonl"),
        }
    }

    pub fn path(&self) -> &Path {
        &self.path
    }

    /// Append one line per **failed attempt** (not per failed call): a retried
    /// call that failed three times leaves three lines.
    pub fn record(&self, tool: &str, failure: &McpFailure) -> anyhow::Result<()> {
        if let Some(parent) = self.path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|duration| duration.as_secs())
            .unwrap_or(0);
        let line = serde_json::json!({
            "timestamp": timestamp,
            "tool": tool,
            "code": failure.code,
            "message": failure.message,
            "attempt": failure.attempts,
        });
        use std::io::Write;
        let mut file = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.path)?;
        writeln!(file, "{}", serde_json::to_string(&line)?)?;
        Ok(())
    }
}

/// Turn an opaque channel error into a structured failure, recovering the
/// JSON-RPC identity when the error carries one (DR-20).
fn failure_from(tool: &str, error: &anyhow::Error, attempt: u32) -> McpFailure {
    match error.downcast_ref::<McpError>() {
        Some(mcp) => McpFailure::new(tool, Some(mcp.code), mcp.message.clone(), attempt),
        None => McpFailure::new(tool, None, error.to_string(), attempt),
    }
}

/// Call one MCP tool, retrying a failure up to `max_retries` extra times.
///
/// The returned error is the *last* real failure: retrying never launders a
/// `-32603` into an empty success.
#[allow(clippy::too_many_arguments)]
pub async fn call_with_retries(
    tools: &dyn ToolChannel,
    role: Role,
    tool: &str,
    args: Value,
    max_retries: u32,
    retry_delay_ms: u64,
    log: Option<&McpErrorLog>,
) -> Result<Value, McpFailure> {
    let total = 1 + max_retries;
    let mut last: Option<McpFailure> = None;
    for attempt in 1..=total {
        match tools.call(role, tool, args.clone()).await {
            Ok(result) => return Ok(result.payload),
            Err(error) => {
                let failure = failure_from(tool, &error, attempt);
                if let Some(log) = log {
                    log.record(tool, &failure)
                        .map_err(|write| McpFailure::new(tool, None, write.to_string(), attempt))?;
                }
                last = Some(failure);
            }
        }
        if attempt < total && retry_delay_ms > 0 {
            tokio::time::sleep(Duration::from_millis(retry_delay_ms)).await;
        }
    }
    Err(last.unwrap_or_else(|| McpFailure::new(tool, None, "no attempt was made", 0)))
}

/// The result of waiting for the running game to become observable.
#[derive(Clone, Debug)]
pub struct ReadyOutcome {
    pub ok: bool,
    pub attempts: u32,
    pub payload: Option<Value>,
    pub failure: Option<McpFailure>,
}

/// DR-20: after `play_scene`, poll `tool` (normally `get_game_scene_tree`) every
/// `poll_interval_ms` until it answers or `timeout_secs` elapses.
///
/// A zero timeout still performs one attempt, so the reported failure is the
/// real one instead of a synthetic "not tried".
pub async fn wait_for_game_ready(
    tools: &dyn ToolChannel,
    role: Role,
    tool: &str,
    args: Value,
    timeout_secs: u64,
    poll_interval_ms: u64,
    log: Option<&McpErrorLog>,
) -> ReadyOutcome {
    let deadline = Instant::now() + Duration::from_secs(timeout_secs);
    let mut attempts = 0u32;
    loop {
        attempts += 1;
        let failure = match tools.call(role, tool, args.clone()).await {
            Ok(result) => {
                return ReadyOutcome {
                    ok: true,
                    attempts,
                    payload: Some(result.payload),
                    failure: None,
                }
            }
            Err(error) => {
                let failure = failure_from(tool, &error, attempts);
                if let Some(log) = log {
                    let _ = log.record(tool, &failure);
                }
                failure
            }
        };
        if Instant::now() >= deadline {
            return ReadyOutcome {
                ok: false,
                attempts,
                payload: None,
                failure: Some(failure),
            };
        }
        if poll_interval_ms > 0 {
            tokio::time::sleep(Duration::from_millis(poll_interval_ms)).await;
        }
    }
}
