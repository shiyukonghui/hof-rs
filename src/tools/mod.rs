//! The tool boundary: role-scoped access to the project's MCP tool server.
//!
//! This is the single enforcement point for R13 — a denied tool is refused by
//! code, never by prompt convention.

pub mod bridge;
pub mod mcp;
pub mod policy;
pub mod reliable;

use crate::model::Role;
use mcp::McpClient;

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

    pub fn client(&self) -> &McpClient {
        &self.client
    }

    /// Group tool names into a compact markdown index (never the full 175
    /// schemas: progressive disclosure, DESIGN-OVERVIEW §4.8).
    fn index_from(&self, role: Role, tools: &[String]) -> String {
        let mut visible: Vec<&String> = tools
            .iter()
            .filter(|tool| policy::tool_allowed(role, tool))
            .collect();
        visible.sort();
        let mut markdown = format!(
            "# Available tools for `{}`\n\n{} tool(s) visible. Call one with:\n\n```\n\
             $HOH_HOH_BIN tools call <tool> --args-file <path>\n```\n\n\
             Get the exact arguments with `$HOH_HOH_BIN tools describe <tool>`.\n\n",
            role.as_str(),
            visible.len()
        );
        if visible.is_empty() {
            markdown.push_str(
                "This role may not call any MCP tool. Use read-only shell commands only.\n",
            );
            return markdown;
        }
        for tool in visible {
            markdown.push_str(&format!("- `{tool}`\n"));
        }
        markdown
    }
}

#[async_trait::async_trait]
impl ToolChannel for McpChannel {
    fn allowed(&self, role: Role, tool: &str) -> bool {
        policy::tool_allowed(role, tool)
    }

    fn index_markdown(&self, role: Role) -> String {
        match self.client.list_tools() {
            Ok(tools) => self.index_from(role, &tools),
            Err(error) => format!(
                "# Available tools for `{}`\n\nWARNING: the MCP tool index is unavailable: \
                 {error}\n\nDo not assume any tool exists; check with \
                 `$HOH_HOH_BIN tools list`.\n",
                role.as_str()
            ),
        }
    }

    async fn call(
        &self,
        role: Role,
        tool: &str,
        args: serde_json::Value,
    ) -> anyhow::Result<ToolResult> {
        if !self.allowed(role, tool) {
            anyhow::bail!("tool_not_permitted: role={} tool={tool}", role.as_str());
        }
        let client = self.client.clone();
        let tool_name = tool.to_string();
        let payload = tokio::task::spawn_blocking(move || client.call(&tool_name, args)).await??;
        Ok(ToolResult { ok: true, payload })
    }
}
