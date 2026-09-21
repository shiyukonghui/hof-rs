//! The tool boundary: role-scoped access to the project's MCP tool server.
//!
//! This is the single enforcement point for R13 — a denied tool is refused by
//! code, never by prompt convention.

pub mod bridge;
pub mod index;
pub mod mcp;
pub mod policy;
pub mod reliable;

use crate::model::Role;
use mcp::{McpClient, RpcCorrelation, SessionSyncReport};

#[derive(Clone, Debug, serde::Serialize, serde::Deserialize)]
pub struct ToolResult {
    pub ok: bool,
    pub payload: serde_json::Value,
}

#[async_trait::async_trait]
pub trait ToolChannel: Send + Sync {
    /// May this role call this tool?  Default-deny (§5.4).
    fn allowed(&self, role: Role, tool: &str) -> bool;

    /// Markdown index injected as `.hoh/TOOLS.md`.
    fn index_markdown(&self, role: Role) -> String;

    async fn call(
        &self,
        role: Role,
        tool: &str,
        args: serde_json::Value,
    ) -> anyhow::Result<ToolResult>;

    /// DR-29: [`ToolChannel::call`] plus the JSON-RPC correlation facts, which
    /// travel into the battery's raw payloads.  Channels without a JSON-RPC
    /// transport simply report an empty correlation.
    async fn call_with_meta(
        &self,
        role: Role,
        tool: &str,
        args: serde_json::Value,
    ) -> anyhow::Result<(ToolResult, RpcCorrelation)> {
        Ok((
            self.call(role, tool, args).await?,
            RpcCorrelation::default(),
        ))
    }

    /// DR-29: the session-start probe — two consecutive read-only calls whose
    /// ids must match.  A channel that cannot do this says so explicitly
    /// instead of reporting a healthy `false`.
    async fn session_sync_probe(&self) -> SessionSyncReport {
        SessionSyncReport::unavailable("this tool channel exposes no JSON-RPC correlation probe")
    }
}

/// A channel that exposes no MCP tools at all (used for offline/dry runs).
#[derive(Debug, Default)]
pub struct ShellOnlyChannel;

#[async_trait::async_trait]
impl ToolChannel for ShellOnlyChannel {
    fn allowed(&self, _role: Role, _tool: &str) -> bool {
        false
    }

    fn index_markdown(&self, _role: Role) -> String {
        "# Available tools\n\nNo MCP tool channel is configured; use shell commands only.\n"
            .to_string()
    }

    async fn call(
        &self,
        _role: Role,
        tool: &str,
        _args: serde_json::Value,
    ) -> anyhow::Result<ToolResult> {
        anyhow::bail!("no tool channel is configured (requested `{tool}`)")
    }
}

/// The real channel: Godot MCP Pro over JSON-RPC, filtered by the role matrix.
#[derive(Clone, Debug)]
pub struct McpChannel {
    client: McpClient,
}

impl McpChannel {
    pub fn new(endpoint: impl Into<String>, timeout_seconds: u64, max_retries: u32) -> Self {
        Self {
            client: McpClient::new(endpoint, timeout_seconds, max_retries),
        }
    }

    /// DR-29: set `tools.max_sync_retries`.
    pub fn with_max_sync_retries(mut self, max_sync_retries: u32) -> Self {
        self.client = self.client.with_max_sync_retries(max_sync_retries);
        self
    }

    pub fn client(&self) -> &McpClient {
        &self.client
    }
}

#[async_trait::async_trait]
impl ToolChannel for McpChannel {
    fn allowed(&self, role: Role, tool: &str) -> bool {
        policy::tool_allowed(role, tool)
    }

    /// DR-26: the index carries the **real schemas** (parameter names, types and
    /// required flags), generated from the live `tools/list` when the editor is
    /// reachable and from the embedded snapshot otherwise.  A role that has the
    /// schema never has to read the harness sources to guess an API.
    fn index_markdown(&self, role: Role) -> String {
        match self.client.list_tool_schemas() {
            Ok(schemas) if !schemas.is_empty() => index::render_tools_markdown(role, &schemas),
            _ => index::render_tools_markdown(role, &index::embedded_tool_schemas()),
        }
    }

    async fn call(
        &self,
        role: Role,
        tool: &str,
        args: serde_json::Value,
    ) -> anyhow::Result<ToolResult> {
        Ok(self.call_with_meta(role, tool, args).await?.0)
    }

    async fn call_with_meta(
        &self,
        role: Role,
        tool: &str,
        args: serde_json::Value,
    ) -> anyhow::Result<(ToolResult, RpcCorrelation)> {
        if !self.allowed(role, tool) {
            anyhow::bail!("tool_not_permitted: role={} tool={tool}", role.as_str());
        }
        let client = self.client.clone();
        let tool_name = tool.to_string();
        let (payload, correlation) =
            tokio::task::spawn_blocking(move || client.call_traced(&tool_name, args)).await??;
        Ok((ToolResult { ok: true, payload }, correlation))
    }

    async fn session_sync_probe(&self) -> SessionSyncReport {
        let client = self.client.clone();
        tokio::task::spawn_blocking(move || client.session_sync_probe())
            .await
            .unwrap_or_else(|error| SessionSyncReport::unavailable(error.to_string()))
    }
}
