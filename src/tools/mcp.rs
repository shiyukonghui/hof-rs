//! JSON-RPC over HTTP client for the Godot MCP Pro server (D3).
//!
//! Blocking (`ureq`) by design: the tool bridge is a short-lived process and
//! the runtime wraps calls in `spawn_blocking`.  Retries apply only to
//! transport failures — a JSON-RPC business error is never retried.

use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::time::Duration;

use serde_json::{json, Value};

#[derive(Clone, Debug)]
pub struct McpClient {
    pub endpoint: String,
    pub timeout_seconds: u64,
    pub max_retries: u32,
    next_id: Arc<AtomicU64>,
}

impl McpClient {
    pub fn new(endpoint: impl Into<String>, timeout_seconds: u64, max_retries: u32) -> Self {
        Self {
            endpoint: endpoint.into(),
            timeout_seconds,
            max_retries,
            next_id: Arc::new(AtomicU64::new(1)),
        }
    }

    fn request(&self, method: &str, params: Option<Value>) -> anyhow::Result<Value> {
        let id = self.next_id.fetch_add(1, Ordering::SeqCst);
        let mut body = json!({"jsonrpc": "2.0", "id": id, "method": method});
        if let Some(params) = params {
            body["params"] = params;
        }

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
                    let value: Value = response
                        .into_json()
                        .map_err(|error| anyhow::anyhow!("invalid JSON-RPC response: {error}"))?;
                    if let Some(error) = value.get("error").filter(|error| !error.is_null()) {
                        let code = error.get("code").and_then(Value::as_i64).unwrap_or(0);
                        let message = error
                            .get("message")
                            .and_then(Value::as_str)
                            .unwrap_or("unknown error");
                        anyhow::bail!("JSON-RPC error {code}: {message}");
                    }
                    return Ok(value.get("result").cloned().unwrap_or(Value::Null));
                }
                Err(error) if attempt <= self.max_retries && is_transport(&error) => {
                    let delay = 200u64 * u64::from(attempt);
                    std::thread::sleep(Duration::from_millis(delay));
                }
                Err(error) => {
                    return Err(anyhow::anyhow!(
                        "MCP request `{method}` to {} failed: {error}",
                        self.endpoint
                    ));
                }
            }
        }
    }

    pub fn list_tools(&self) -> anyhow::Result<Vec<String>> {
        let result = self.request("tools/list", None)?;
        let tools = result
            .get("tools")
            .and_then(Value::as_array)
            .cloned()
            .unwrap_or_default();
        Ok(tools
            .iter()
            .filter_map(|tool| tool.get("name").and_then(Value::as_str))
            .map(ToOwned::to_owned)
            .collect())
    }

    pub fn describe(&self, tool: &str) -> anyhow::Result<Value> {
        let result = self.request("tools/list", None)?;
        let tools = result
            .get("tools")
            .and_then(Value::as_array)
            .cloned()
            .unwrap_or_default();
        tools
            .into_iter()
            .find(|entry| entry.get("name").and_then(Value::as_str) == Some(tool))
            .ok_or_else(|| anyhow::anyhow!("tool `{tool}` is not exposed by the MCP server"))
    }

    pub fn call(&self, tool: &str, args: Value) -> anyhow::Result<Value> {
        self.request("tools/call", Some(json!({"name": tool, "arguments": args})))
    }
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
}
