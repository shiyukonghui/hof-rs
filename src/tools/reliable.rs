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
use crate::tools::endpoint::McpEndpointUnavailableError;
use crate::tools::mcp::{McpError, McpTransportError, RpcCorrelation};
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
    /// DR-29: the request/response identity, when the failure carries one (a
    /// `McpResponseDesync` knows which ids it saw).  Boxed so the failure stays
    /// small enough to travel inside a `Result`.
    pub correlation: Box<RpcCorrelation>,
    /// DR-56: the classified retry verdict of this failure.  Set once, by
    /// [`failure_from`], so the retry ring never re-derives it and a business
    /// error can never be retried by accident.  See [`is_retryable_failure`].
    pub retryable: bool,
    /// DR-55: whether this failure **is** the endpoint's liveness verdict (the
    /// endpoint was already declared unavailable, so nothing was sent).  A
    /// readiness poll ends on it; a business error — which is an answer — does
    /// not carry it.
    pub endpoint_verdict: bool,
}

impl McpFailure {
    pub fn new(tool: &str, code: Option<i64>, message: impl Into<String>, attempts: u32) -> Self {
        Self {
            tool: tool.to_string(),
            code,
            message: message.into(),
            attempts,
            correlation: Box::new(RpcCorrelation::default()),
            retryable: false,
            endpoint_verdict: false,
        }
    }

    pub fn with_correlation(mut self, correlation: RpcCorrelation) -> Self {
        self.correlation = Box::new(correlation);
        self
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

/// DR-56: **the** classifier the retry ring consults.
///
/// One named function, no scattered special cases: a failure is retryable only
/// when it is a *transport* failure ([`McpTransportError`]).  A JSON-RPC business
/// error (`-32602`, `-32603`, …) is a verdict — asking again cannot turn it into
/// a success, and `smoke-t6` proved the cost of pretending otherwise: the same
/// `-32602` was retried three times.
///
/// An error that carries no classification is treated as non-retryable on
/// purpose: in a system whose failure records must be trustworthy, the
/// conservative direction is to report the real failure once instead of
/// laundering it through retries.
pub fn is_retryable_failure(error: &McpFailure) -> bool {
    error.retryable
}

/// Turn an opaque channel error into a structured failure, recovering the
/// JSON-RPC identity when the error carries one (DR-20/DR-29) and classifying it
/// for the retry ring (DR-56).
fn failure_from(tool: &str, error: &anyhow::Error, attempt: u32) -> McpFailure {
    if let Some(mcp) = error.downcast_ref::<McpError>() {
        // A JSON-RPC business error is a verdict: never retryable.
        return McpFailure::new(tool, Some(mcp.code), mcp.message.clone(), attempt);
    }
    if let Some(transport) = error.downcast_ref::<McpTransportError>() {
        let mut failure = McpFailure::new(tool, None, transport.to_string(), attempt);
        failure.retryable = true;
        return failure;
    }
    if let Some(refusal) = error.downcast_ref::<McpEndpointUnavailableError>() {
        // DR-55: nothing was sent, so there is nothing to retry and no point
        // polling — the endpoint's verdict is already recorded.
        let mut failure = McpFailure::new(tool, None, refusal.message.clone(), attempt);
        failure.endpoint_verdict = true;
        return failure;
    }
    // DR-29: a desync knows exactly which ids it saw; keep them.
    if let Some(crate::errors::HofError::McpResponseDesync {
        expected_id,
        got_ids,
        sync_probes,
    }) = crate::errors::as_hof_error(error)
    {
        return McpFailure::new(tool, None, error.to_string(), attempt).with_correlation(
            RpcCorrelation {
                request_id: Some(*expected_id),
                response_id: None,
                sync_probes: *sync_probes,
                mismatched_ids: got_ids.clone(),
            },
        );
    }
    McpFailure::new(tool, None, error.to_string(), attempt)
}

/// DR-29: one successful MCP call together with its correlation facts.
#[derive(Clone, Debug)]
pub struct TracedCall {
    pub payload: Value,
    pub correlation: RpcCorrelation,
}

/// Call one MCP tool, retrying a **retryable** (transport) failure up to
/// `max_retries` extra times.
///
/// The returned error is the *last* real failure: retrying never launders a
/// `-32603` into an empty success.  DR-56: the ring is also **class-aware** — a
/// JSON-RPC business error is returned after exactly one attempt (see
/// [`is_retryable_failure`]).
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
    Ok(
        call_with_retries_traced(tools, role, tool, args, max_retries, retry_delay_ms, log)
            .await?
            .payload,
    )
}

/// DR-56: may a second attempt be made after this failure?
///
/// `total` is the budget for this call (`1 + max_retries`); the ring stops early
/// when the budget is spent **or** when the failure's class says retrying cannot
/// help.
fn another_attempt_is_allowed(attempt: u32, total: u32, last: Option<&McpFailure>) -> bool {
    if attempt >= total {
        return false;
    }
    // No recorded failure cannot happen on this path, and if it somehow does,
    // stopping is the conservative direction.
    last.map(is_retryable_failure).unwrap_or(false)
}

/// DR-29: [`call_with_retries`] plus the `request_id`/`response_id`/probe
/// counts of the successful round trip.
#[allow(clippy::too_many_arguments)]
pub async fn call_with_retries_traced(
    tools: &dyn ToolChannel,
    role: Role,
    tool: &str,
    args: Value,
    max_retries: u32,
    retry_delay_ms: u64,
    log: Option<&McpErrorLog>,
) -> Result<TracedCall, McpFailure> {
    let total = 1 + max_retries;
    let mut last: Option<McpFailure> = None;
    for attempt in 1..=total {
        match tools.call_with_meta(role, tool, args.clone()).await {
            Ok((result, correlation)) => {
                return Ok(TracedCall {
                    payload: result.payload,
                    correlation,
                })
            }
            Err(error) => {
                let failure = failure_from(tool, &error, attempt);
                if let Some(log) = log {
                    log.record(tool, &failure)
                        .map_err(|write| McpFailure::new(tool, None, write.to_string(), attempt))?;
                }
                last = Some(failure);
            }
        }
        if another_attempt_is_allowed(attempt, total, last.as_ref()) && retry_delay_ms > 0 {
            tokio::time::sleep(Duration::from_millis(retry_delay_ms)).await;
        }
        if !another_attempt_is_allowed(attempt, total, last.as_ref()) {
            // Either the budget is spent or the class forbids a retry; both mean
            // the ring ends here, with `last` still holding the real failure.
            break;
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
    /// DR-29: the correlation facts of the poll that succeeded.
    pub correlation: RpcCorrelation,
}

/// DR-20: after `editor_play_scene`, poll `tool` (normally `running_game_get_scene_tree`) every
/// `poll_interval_ms` until it answers or `timeout_secs` elapses.
///
/// A zero timeout still performs one attempt, so the reported failure is the
/// real one instead of a synthetic "not tried".
///
/// DR-55/DR-56: polling continues on **business** errors on purpose — a game
/// that is still starting up legitimately answers `-32603 等待游戏响应超时` until
/// it is ready, and `smoke-t3` showed the cost of ending a poll early.  What
/// stops a poll instantly is the DR-55 verdict: once the channel has marked the
/// endpoint unavailable, every attempt is refused before a request is sent, so
/// the poll returns after exactly one refusal instead of burning its deadline.
pub async fn wait_for_game_ready(
    tools: &dyn ToolChannel,
    role: Role,
    tool: &str,
    args: Value,
    timeout_secs: u64,
    poll_interval_ms: u64,
    log: Option<&McpErrorLog>,
) -> ReadyOutcome {
    wait_for_ready_matching(
        tools,
        role,
        tool,
        args,
        timeout_secs,
        poll_interval_ms,
        log,
        // The permissive predicate: a successful answer is enough, and the
        // count it reports is not consulted here.
        |_| Ok(1usize),
    )
    .await
}

/// DR-72 ⑤ (D1): readiness is **an answer of the right shape**, not merely an
/// answer.
///
/// DR-70's round-game start polled `running_game_get_scene_tree` and accepted
/// any successful reply, while the battery's own `play_scene_ready` step applied
/// `describe_scene_tree_shape` to the same payload.  Two readiness predicates
/// for one question is a defect: a stub or half-started game could confirm the
/// round's route while the battery refused the very same reply.
///
/// `shape` receives the raw payload of every successful poll (before any
/// unwrapping — the caller decides what to unwrap) and returns the node count or
/// the reason the payload is not a scene tree.  A wrong-but-successful answer
/// keeps the poll going, because a game that is still starting legitimately
/// answers like that for a while; when the deadline is reached the last failure
/// **is** the shape refusal, so the verdict names the real problem instead of a
/// generic timeout.
///
/// DR-86 ②: the poll opens and closes the channel's **cold-start window** around
/// its loop.  `smoke-t16`'s round of record marked its game endpoint unavailable
/// after two transport failures *inside this poll* — before any
/// `running_game_*` call had succeeded — and every later semantic call was then
/// refused with `attempt(s)=0`, so the round produced no behaviour reading at
/// all.  A poll is the one place a transport failure means "the process is still
/// starting"; while this window is open and the endpoint has never answered, the
/// channel tolerates [`crate::tools::endpoint::COLD_START_DEATH_THRESHOLD`]
/// consecutive failures instead of two, so a listener that binds a moment later
/// is still reached.  The bound is kept: an endpoint that truly never answers is
/// marked unavailable with its true failure count, and the refusal is unchanged.
#[allow(clippy::too_many_arguments)]
pub async fn wait_for_ready_matching(
    tools: &dyn ToolChannel,
    role: Role,
    tool: &str,
    args: Value,
    timeout_secs: u64,
    poll_interval_ms: u64,
    log: Option<&McpErrorLog>,
    shape: impl Fn(&Value) -> Result<usize, String>,
) -> ReadyOutcome {
    let deadline = Instant::now() + Duration::from_secs(timeout_secs);
    let mut attempts = 0u32;
    // DR-86 ②: the window is opened before the first attempt and closed on every
    // exit path below, so no call outside a readiness wait is ever granted it.
    tools.set_cold_start_grace(tool, true);
    let outcome = loop {
        attempts += 1;
        let mut shape_failure: Option<McpFailure> = None;
        let failure = match tools.call_with_meta(role, tool, args.clone()).await {
            Ok((result, correlation)) => match shape(&result.payload) {
                Ok(_) => {
                    break ReadyOutcome {
                        ok: true,
                        attempts,
                        payload: Some(result.payload),
                        failure: None,
                        correlation,
                    }
                }
                Err(problem) => {
                    let failure = McpFailure::new(
                        tool,
                        None,
                        format!("the payload answered but it is not readiness evidence: {problem}"),
                        attempts,
                    )
                    .with_correlation(correlation);
                    if let Some(log) = log {
                        let _ = log.record(tool, &failure);
                    }
                    shape_failure = Some(failure.clone());
                    failure
                }
            },
            Err(error) => {
                let failure = failure_from(tool, &error, attempts);
                if let Some(log) = log {
                    let _ = log.record(tool, &failure);
                }
                failure
            }
        };
        if Instant::now() >= deadline {
            break ReadyOutcome {
                ok: false,
                attempts,
                payload: None,
                // A shape refusal is the *specific* answer, so it wins over the
                // generic "the deadline passed": the verdict names what was
                // wrong with the payload rather than blaming the clock.
                failure: Some(shape_failure.unwrap_or(failure)),
                correlation: RpcCorrelation::default(),
            };
        }
        // A wrong shape is a **successful answer** but not readiness: the game is
        // reachable, so the poll keeps asking — a game that has just been started
        // may answer with a stub for a moment — and gives up at the deadline with
        // the shape refusal rather than accepting it.
        //
        // DR-55: a poll must not keep knocking on an endpoint that has already
        // been declared dead.  The refusal carries the endpoint verdict and no
        // retryable class (nothing was sent), so the poll ends on it instead of
        // burning its whole deadline — exactly the readiness budget `smoke-t6`
        // wasted.  A **business** error still polls: a game that is merely not
        // ready yet answers like that until it is.
        if failure.endpoint_verdict {
            break ReadyOutcome {
                ok: false,
                attempts,
                payload: None,
                failure: Some(failure),
                correlation: RpcCorrelation::default(),
            };
        }
        if poll_interval_ms > 0 {
            tokio::time::sleep(Duration::from_millis(poll_interval_ms)).await;
        }
    };
    tools.set_cold_start_grace(tool, false);
    outcome
}
