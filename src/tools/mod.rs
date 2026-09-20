//! The tool boundary: role-scoped access to the project's MCP tool server.
//!
//! This is the single enforcement point for R13 — a denied tool is refused by
//! code, never by prompt convention.

pub mod policy;

use crate::model::Role;

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
