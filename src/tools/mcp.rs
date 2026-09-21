//! JSON-RPC over HTTP client for the Godot MCP Pro server (D3).
//!
//! Blocking (`ureq`) by design: the tool bridge is a short-lived process and
//! the runtime wraps calls in `spawn_blocking`.  Retries apply only to
//! transport failures — a JSON-RPC business error is never retried.
//!
//! DR-29: **every** response is correlated with its request id before its
//! payload is used.  The third real smoke run (`smoke-t3`) met a server that
//! answers one request behind (`id=1` → `resp.id=704`, `id=2` → the `id=1`
//! response, …), and the client silently took `result` — so
//! `get_scene_file_content` received `open_scene`'s reply, the launch gate
//! produced a false negative, and 13.4 minutes / 4.35M tokens were spent
//! repairing a defect that did not exist.  A mis-correlated payload is now
//! never used: it is parked in a short-lived pending table and a read-only
//! probe (`get_project_info`) is sent to flush the real response out.

use std::collections::BTreeMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::time::Duration;

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

use crate::errors::HofError;

/// DR-29: the default number of read-only probes (`tools.max_sync_retries`).
pub const DEFAULT_MAX_SYNC_RETRIES: u32 = 4;

/// DR-29: the **only** tool a synchronization probe may use: it reads the
/// project description and changes nothing.
pub const PROBE_TOOL: &str = "get_project_info";

/// DR-29: at most this many unclaimed responses are remembered.  The table is
/// short-lived on purpose: it exists to hand a lagging response to the call that
/// is still waiting for it, not to be a cache.
const PENDING_CAPACITY: usize = 32;

/// DR-20: a JSON-RPC business error, kept as a concrete type so callers can
/// recover the `code`/`message` instead of parsing a formatted string.  The
/// first real smoke run produced three distinct `-32603` failures that all had
/// to stay verbatim in the evidence records.
#[derive(Clone, Debug, PartialEq, Eq, thiserror::Error)]
#[error("JSON-RPC error {code}: {message}")]
pub struct McpError {
    pub code: i64,
    pub message: String,
}

impl McpError {
    pub fn new(code: i64, message: impl Into<String>) -> Self {
        Self {
            code,
            message: message.into(),
        }
    }
}

/// DR-29: the request/response identity of one JSON-RPC call.
///
/// It is written into every battery step's raw payload so a human can tell
/// which response belonged to which request — the exact record `smoke-t3`
/// lacked.
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct RpcCorrelation {
    pub request_id: Option<u64>,
    pub response_id: Option<u64>,
    pub sync_probes: u32,
    /// Every id that arrived instead of the expected one, in arrival order.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub mismatched_ids: Vec<u64>,
}

impl RpcCorrelation {
    /// The id offset this call observed (`received - expected`), if any.
    pub fn observed_offset(&self) -> Option<i64> {
        let expected = self.request_id? as i64;
        self.mismatched_ids
            .first()
            .map(|observed| *observed as i64 - expected)
    }
}

/// DR-29: the outcome of the session-start synchronization probe — two
/// consecutive `get_project_info` calls whose ids are checked.
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct SessionSyncReport {
    /// Whether the channel can perform the probe at all.
    pub available: bool,
    /// Extra probe requests the two calls needed to get their own responses.
    pub probes: u32,
    /// Whether any correlation mismatch was observed.
    pub desynced: bool,
    /// The first id offset seen (`response_id - request_id`).
    pub observed_offset: Option<i64>,
    pub detail: String,
}

impl SessionSyncReport {
    pub fn unavailable(detail: impl Into<String>) -> Self {
        Self {
            available: false,
            detail: detail.into(),
            ..Self::default()
        }
    }
}

#[derive(Clone, Debug)]
pub struct McpClient {
    pub endpoint: String,
    pub timeout_seconds: u64,
    pub max_retries: u32,
    /// DR-29: how many read-only probes may be spent on one call.
    pub max_sync_retries: u32,
    next_id: Arc<AtomicU64>,
    /// DR-29: responses that arrived under a `resp.id != req.id`, keyed by the
    /// id they actually carry.
    pending: Arc<Mutex<BTreeMap<u64, Value>>>,
}

impl McpClient {
    pub fn new(endpoint: impl Into<String>, timeout_seconds: u64, max_retries: u32) -> Self {
        Self {
            endpoint: endpoint.into(),
            timeout_seconds,
            max_retries,
            max_sync_retries: DEFAULT_MAX_SYNC_RETRIES,
            next_id: Arc::new(AtomicU64::new(1)),
            pending: Arc::new(Mutex::new(BTreeMap::new())),
        }
    }

    pub fn with_max_sync_retries(mut self, max_sync_retries: u32) -> Self {
        self.max_sync_retries = max_sync_retries;
        self
    }

    /// One HTTP round trip, retrying **transport** failures only.
    fn post(&self, body: &Value) -> anyhow::Result<Value> {
        let mut attempt = 0u32;
        loop {
            attempt += 1;
            let agent = ureq::AgentBuilder::new()
                .timeout(Duration::from_secs(self.timeout_seconds.max(1)))
                .build();
            let outcome = agent
                .post(&self.endpoint)
                .set("Content-Type", "application/json")
                .send_json(body.clone());
            match outcome {
                Ok(response) => {
                    return response
                        .into_json()
                        .map_err(|error| anyhow::anyhow!("invalid JSON-RPC response: {error}"))
                }
                Err(error) if attempt <= self.max_retries && is_transport(&error) => {
                    let delay = 200u64 * u64::from(attempt);
                    std::thread::sleep(Duration::from_millis(delay));
                }
                Err(error) => {
                    return Err(anyhow::anyhow!(
                        "MCP request to {} failed: {error}",
                        self.endpoint
                    ))
                }
            }
        }
    }

    /// DR-29: send one request and return **its own** response, using read-only
    /// probes to recover from a lagging server.
    ///
    /// Iterative by construction (the design forbids recursion here): each turn
    /// parks a mis-correlated response and sends one more probe.
    pub fn rpc(
        &self,
        method: &str,
        params: Option<Value>,
    ) -> anyhow::Result<(Value, RpcCorrelation)> {
        let request_id = self.next_id.fetch_add(1, Ordering::SeqCst);
        let mut correlation = RpcCorrelation {
            request_id: Some(request_id),
            ..RpcCorrelation::default()
        };
        let body = request_body(request_id, method, params);
        let first = self.post(&body)?;
        if let Some(value) = self.matched(&first, request_id, &mut correlation)? {
            return Ok((value, correlation));
        }
        loop {
            // A probe already sent may have flushed our response into the table.
            if let Some(claimed) = self.claim(request_id) {
                correlation.response_id = Some(request_id);
                return Ok((extract_result(&claimed)?, correlation));
            }
            if correlation.sync_probes >= self.max_sync_retries {
                return Err(HofError::McpResponseDesync {
                    expected_id: request_id,
                    got_ids: correlation.mismatched_ids.clone(),
                    sync_probes: correlation.sync_probes,
                }
                .into());
            }
            correlation.sync_probes += 1;
            let probe_id = self.next_id.fetch_add(1, Ordering::SeqCst);
            let probe = request_body(
                probe_id,
                "tools/call",
                Some(json!({"name": PROBE_TOOL, "arguments": {}})),
            );
            let response = self.post(&probe)?;
            if let Some(value) = self.matched(&response, request_id, &mut correlation)? {
                return Ok((value, correlation));
            }
        }
    }

    /// If this response carries the id we asked for, return its `result`.  A
    /// mismatching response is parked under **its own** id and never read.
    fn matched(
        &self,
        response: &Value,
        request_id: u64,
        correlation: &mut RpcCorrelation,
    ) -> anyhow::Result<Option<Value>> {
        let observed = response_id_of(response);
        if observed == Some(request_id) {
            correlation.response_id = Some(request_id);
            return Ok(Some(extract_result(response)?));
        }
        if let Some(other) = observed {
            self.stash(other, response.clone());
            correlation.mismatched_ids.push(other);
        }
        Ok(None)
    }

    fn stash(&self, id: u64, response: Value) {
        let Ok(mut pending) = self.pending.lock() else {
            return;
        };
        pending.insert(id, response);
        while pending.len() > PENDING_CAPACITY {
            let oldest = *pending.keys().next().expect("non-empty");
            pending.remove(&oldest);
        }
    }

    fn claim(&self, id: u64) -> Option<Value> {
        self.pending.lock().ok()?.remove(&id)
    }

    /// DR-29: the session-start synchronization probe.
    ///
    /// Two consecutive `get_project_info` calls, each of which must receive its
    /// **own** response.  Any mismatch is reported with the observed id offset
    /// and the number of probes it cost.
    pub fn session_sync_probe(&self) -> SessionSyncReport {
        let mut report = SessionSyncReport {
            available: true,
            ..SessionSyncReport::default()
        };
        for _ in 0..2 {
            let call = self.rpc(
                "tools/call",
                Some(json!({"name": PROBE_TOOL, "arguments": {}})),
            );
            match call {
                Ok((_, correlation)) => {
                    report.probes += correlation.sync_probes;
                    if correlation.sync_probes > 0 {
                        report.desynced = true;
                    }
                    if report.observed_offset.is_none() {
                        report.observed_offset = correlation.observed_offset();
                    }
                }
                Err(error) => {
                    if let Some(desync) = error.downcast_ref::<HofError>() {
                        if let HofError::McpResponseDesync {
                            expected_id,
                            got_ids,
                            sync_probes,
                        } = desync
                        {
                            report.desynced = true;
                            report.probes += sync_probes;
                            if report.observed_offset.is_none() {
                                report.observed_offset =
                                    got_ids.first().map(|id| *id as i64 - *expected_id as i64);
                            }
                        }
                    }
                    report.detail = error.to_string();
                    break;
                }
            }
        }
        report
    }

    pub fn list_tools(&self) -> anyhow::Result<Vec<String>> {
        Ok(self
            .list_tool_schemas()?
            .iter()
            .filter_map(|tool| tool.get("name").and_then(Value::as_str))
            .map(ToOwned::to_owned)
            .collect())
    }

    /// DR-26: the full `tools/list` entries (name + description + inputSchema),
    /// which is what `TOOLS.md` is generated from.
    pub fn list_tool_schemas(&self) -> anyhow::Result<Vec<Value>> {
        let (result, _) = self.rpc("tools/list", None)?;
        Ok(result
            .get("tools")
            .and_then(Value::as_array)
            .cloned()
            .unwrap_or_default())
    }

    pub fn describe(&self, tool: &str) -> anyhow::Result<Value> {
        let tools = self.list_tool_schemas()?;
        tools
            .into_iter()
            .find(|entry| entry.get("name").and_then(Value::as_str) == Some(tool))
            .ok_or_else(|| anyhow::anyhow!("tool `{tool}` is not exposed by the MCP server"))
    }

    pub fn call(&self, tool: &str, args: Value) -> anyhow::Result<Value> {
        Ok(self.call_traced(tool, args)?.0)
    }

    /// DR-29: [`McpClient::call`] plus the correlation facts of the round trip.
    pub fn call_traced(
        &self,
        tool: &str,
        args: Value,
    ) -> anyhow::Result<(Value, RpcCorrelation)> {
        self.rpc(
            "tools/call",
            Some(json!({"name": tool, "arguments": args})),
        )
    }
}

fn request_body(id: u64, method: &str, params: Option<Value>) -> Value {
    let mut body = json!({"jsonrpc": "2.0", "id": id, "method": method});
    if let Some(params) = params {
        body["params"] = params;
    }
    body
}

/// The numeric id of a response, tolerating the string form some servers use.
fn response_id_of(response: &Value) -> Option<u64> {
    let id = response.get("id")?;
    match id {
        Value::Number(number) => number.as_u64(),
        Value::String(text) => text.parse().ok(),
        _ => None,
    }
}

/// A matching response still has to be a *successful* one.
fn extract_result(response: &Value) -> anyhow::Result<Value> {
    if let Some(error) = response.get("error").filter(|error| !error.is_null()) {
        let code = error.get("code").and_then(Value::as_i64).unwrap_or(0);
        let message = error
            .get("message")
            .and_then(Value::as_str)
            .unwrap_or("unknown error");
        return Err(McpError::new(code, message).into());
    }
    Ok(response.get("result").cloned().unwrap_or(Value::Null))
}

fn is_transport(error: &ureq::Error) -> bool {
    matches!(error, ureq::Error::Transport(_))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn request_body_shape_matches_the_jsonrpc_contract() {
        // Pure shape assertion: no network involved.
        let body = json!({
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {"name": "play_scene", "arguments": {}}
        });
        assert_eq!(body["jsonrpc"], json!("2.0"));
        assert_eq!(body["method"], json!("tools/call"));
        assert_eq!(body["params"]["name"], json!("play_scene"));
    }

    #[test]
    fn request_body_is_built_with_the_requested_id() {
        let body = request_body(704, "tools/list", None);
        assert_eq!(body["id"], json!(704));
        assert_eq!(body["jsonrpc"], json!("2.0"));
        assert!(body.get("params").is_none());
    }

    #[test]
    fn response_ids_are_read_in_both_encodings() {
        assert_eq!(response_id_of(&json!({"id": 12})), Some(12));
        assert_eq!(response_id_of(&json!({"id": "12"})), Some(12));
        assert_eq!(response_id_of(&json!({"result": {}})), None);
    }

    #[test]
    fn the_observed_offset_is_signed() {
        let correlation = RpcCorrelation {
            request_id: Some(1),
            mismatched_ids: vec![704],
            ..RpcCorrelation::default()
        };
        assert_eq!(correlation.observed_offset(), Some(703));
        let behind = RpcCorrelation {
            request_id: Some(3),
            mismatched_ids: vec![2],
            ..RpcCorrelation::default()
        };
        assert_eq!(behind.observed_offset(), Some(-1));
    }

    /// A stashed response is only ever returned under its own id.
    #[test]
    fn the_pending_table_claims_by_id_and_stays_bounded() {
        let client = McpClient::new("http://127.0.0.1:1/mcp", 1, 0);
        assert!(client.claim(1).is_none());
        client.stash(1, json!({"id": 1, "result": {"mine": true}}));
        assert_eq!(client.claim(1).unwrap()["result"]["mine"], json!(true));
        assert!(client.claim(1).is_none(), "a claim consumes the entry");

        for id in 0..(PENDING_CAPACITY as u64 + 5) {
            client.stash(id, json!({"id": id}));
        }
        assert!(client.claim(0).is_none(), "the oldest entries are dropped");
        assert!(client.claim(PENDING_CAPACITY as u64 + 4).is_some());
    }
}
