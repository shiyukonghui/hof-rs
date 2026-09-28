//! The tool boundary: role-scoped access to the project's MCP tool server.
//!
//! This is the single enforcement point for R13 — a denied tool is refused by
//! code, never by prompt convention.

pub mod bridge;
pub mod endpoint;
pub mod index;
pub mod mcp;
pub mod policy;
pub mod reliable;

use crate::model::Role;
use endpoint::{GameEndpointRecord, ToolScope};
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

    /// DR-43: register the game endpoint `editor_play_scene` announced.
    ///
    /// A channel that serves exactly one endpoint — a test double, or
    /// `ShellOnlyChannel` — accepts the registration without routing anything:
    /// it has no second endpoint to route to.  The real [`McpChannel`] routes
    /// `running_game_*` there, and **fails** a game call when nothing is
    /// registered (never silently falls back to the editor endpoint).
    async fn register_game_endpoint(&self, _record: GameEndpointRecord) -> anyhow::Result<()> {
        Ok(())
    }

    /// DR-43: the game endpoint is gone (`editor_stop_scene`).  Later
    /// `running_game_*` calls must fail rather than reach a stale port.
    async fn clear_game_endpoint(&self) {}

    /// DR-43: the game endpoint this channel currently routes to.
    async fn game_endpoint(&self) -> Option<GameEndpointRecord> {
        None
    }

    /// DR-51: the last game endpoint this channel ever **registered**, even
    /// after [`ToolChannel::clear_game_endpoint`] invalidated the route.
    ///
    /// The route and the identity are two different facts: `editor_stop_scene`
    /// legitimately drops the route (a later `running_game_*` call must fail),
    /// but "which game endpoint did this run use?" must survive, or
    /// `meta.json.engine.mcp.game_endpoint` is structurally always `null` —
    /// which is exactly `smoke-t6`'s DEF-D.
    async fn game_endpoint_history(&self) -> Option<GameEndpointRecord> {
        None
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

/// The real channel: the engine's native MCP module over JSON-RPC, filtered by
/// the role matrix and routed per scope (DR-43).
///
/// One channel object owns **both** endpoints: the editor endpoint it was
/// constructed with, and the game endpoint `editor_play_scene` announced.  The
/// game route is created lazily and dropped by `editor_stop_scene`, so its
/// JSON-RPC id counter survives a whole game session (DR-29) without outliving
/// it.
#[derive(Clone, Debug)]
pub struct McpChannel {
    editor: McpClient,
    game: std::sync::Arc<std::sync::Mutex<Option<GameRoute>>>,
    /// DR-51: the last endpoint that was registered, kept after the route is
    /// cleared so the run's identity record does not lose it.
    game_history: std::sync::Arc<std::sync::Mutex<Option<GameEndpointRecord>>>,
    timeout_seconds: u64,
    max_retries: u32,
    max_sync_retries: u32,
}

/// DR-43: a registered game endpoint plus the client that talks to it.
#[derive(Clone, Debug)]
struct GameRoute {
    record: GameEndpointRecord,
    client: McpClient,
}

impl McpChannel {
    pub fn new(endpoint: impl Into<String>, timeout_seconds: u64, max_retries: u32) -> Self {
        Self {
            editor: McpClient::new(endpoint, timeout_seconds, max_retries),
            game: std::sync::Arc::new(std::sync::Mutex::new(None)),
            game_history: std::sync::Arc::new(std::sync::Mutex::new(None)),
            timeout_seconds,
            max_retries,
            max_sync_retries: mcp::DEFAULT_MAX_SYNC_RETRIES,
        }
    }

    /// DR-29: set `tools.max_sync_retries`.
    pub fn with_max_sync_retries(mut self, max_sync_retries: u32) -> Self {
        self.max_sync_retries = max_sync_retries;
        self.editor = self.editor.with_max_sync_retries(max_sync_retries);
        self
    }

    pub fn client(&self) -> &McpClient {
        &self.editor
    }

    /// DR-43: the client for one call, chosen by the tool's scope.
    ///
    /// A `running_game_*` tool without a registered game endpoint is a **hard
    /// error**: falling back to the editor endpoint would send the call to a
    /// server that does not implement it and dress the failure up as evidence.
    fn client_for(&self, tool: &str) -> anyhow::Result<McpClient> {
        match endpoint::scope_of(tool) {
            ToolScope::Editor => Ok(self.editor.clone()),
            ToolScope::Game => {
                let guard = self
                    .game
                    .lock()
                    .map_err(|_| anyhow::anyhow!("the game endpoint registry is poisoned"))?;
                match guard.as_ref() {
                    Some(route) => Ok(route.client.clone()),
                    None => anyhow::bail!(
                        "game_endpoint_unavailable: `{tool}` runs in the game process and only \
                         the game endpoint serves it; no game endpoint is registered yet \
                         (`editor_play_scene` must have answered with `endpoint` or `mcp_port`). \
                         Falling back to the editor endpoint is not allowed (DR-43)."
                    ),
                }
            }
        }
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
        match self.editor.list_tool_schemas() {
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
        // DR-43: the scope decides the endpoint *before* any request is sent.
        let client = self.client_for(tool)?;
        let tool_name = tool.to_string();
        let (payload, correlation) =
            tokio::task::spawn_blocking(move || client.call_traced(&tool_name, args)).await??;
        Ok((ToolResult { ok: true, payload }, correlation))
    }

    async fn session_sync_probe(&self) -> SessionSyncReport {
        let client = self.editor.clone();
        tokio::task::spawn_blocking(move || client.session_sync_probe())
            .await
            .unwrap_or_else(|error| SessionSyncReport::unavailable(error.to_string()))
    }

    async fn register_game_endpoint(&self, record: GameEndpointRecord) -> anyhow::Result<()> {
        let client = McpClient::new(record.endpoint.clone(), self.timeout_seconds, self.max_retries)
            .with_max_sync_retries(self.max_sync_retries);
        let mut guard = self
            .game
            .lock()
            .map_err(|_| anyhow::anyhow!("the game endpoint registry is poisoned"))?;
        *guard = Some(GameRoute {
            record: record.clone(),
            client,
        });
        // DR-51: the identity is captured **at registration time**, before
        // anything may clear the route.
        if let Ok(mut history) = self.game_history.lock() {
            *history = Some(record);
        }
        Ok(())
    }

    async fn clear_game_endpoint(&self) {
        if let Ok(mut guard) = self.game.lock() {
            *guard = None;
        }
    }

    async fn game_endpoint(&self) -> Option<GameEndpointRecord> {
        self.game
            .lock()
            .ok()
            .and_then(|guard| guard.as_ref().map(|route| route.record.clone()))
    }

    async fn game_endpoint_history(&self) -> Option<GameEndpointRecord> {
        self.game_history.lock().ok().and_then(|guard| guard.clone())
    }
}
