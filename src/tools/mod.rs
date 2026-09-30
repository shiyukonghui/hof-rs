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
use endpoint::{EndpointLiveness, GameEndpointRecord, ToolScope};
use mcp::{McpClient, McpTransportError, RpcCorrelation, SessionSyncReport};

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

    /// DR-69 ①: tell this channel where the run publishes its game route, and
    /// adopt what is already published there.
    ///
    /// A role's `hoh tools call` is a **separate process** from the run that
    /// started the game, so the in-memory route alone can never be reached
    /// (`smoke-t9`: `mcp_port=61183` announced, and still
    /// `game_endpoint_unavailable`, exit 5).  The channel that registers the
    /// endpoint publishes it to `path`; a channel pointed at the same path
    /// resolves it again.  The default implementation accepts the path and
    /// adopts nothing, which is what a single-endpoint double wants.
    fn use_game_route_file(&self, _path: std::path::PathBuf) -> Option<GameEndpointRecord> {
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

    /// DR-55: the recorded liveness of one endpoint, when the channel tracks it.
    ///
    /// A channel that serves exactly one endpoint (a test double,
    /// `ShellOnlyChannel`) has no such verdict to report and answers `None`
    /// rather than inventing a healthy one.
    async fn endpoint_liveness(&self, _endpoint: &str) -> Option<EndpointLiveness> {
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
    /// DR-69 ①: where the run publishes the game route so a **later process**
    /// (a role's `hoh tools call`) can resolve it.
    game_route_file: std::sync::Arc<std::sync::Mutex<Option<std::path::PathBuf>>>,
    /// DR-70 ②: why the published route was **not** adopted, when it was not.
    /// The reason travels into the refusal so a stale route is never reported as
    /// "nothing is registered yet".
    route_refusal: std::sync::Arc<std::sync::Mutex<Option<String>>>,
    /// DR-55: the per-endpoint liveness verdict, keyed by the JSON-RPC URL.
    liveness:
        std::sync::Arc<std::sync::Mutex<std::collections::BTreeMap<String, EndpointLiveness>>>,
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
            game_route_file: std::sync::Arc::new(std::sync::Mutex::new(None)),
            route_refusal: std::sync::Arc::new(std::sync::Mutex::new(None)),
            liveness: std::sync::Arc::new(std::sync::Mutex::new(std::collections::BTreeMap::new())),
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
    fn client_for(&self, tool: &str) -> anyhow::Result<(McpClient, String)> {
        match endpoint::scope_of(tool) {
            ToolScope::Editor => Ok((self.editor.clone(), self.editor.endpoint.clone())),
            ToolScope::Game => {
                let guard = self
                    .game
                    .lock()
                    .map_err(|_| anyhow::anyhow!("the game endpoint registry is poisoned"))?;
                match guard.as_ref() {
                    Some(route) => Ok((route.client.clone(), route.record.endpoint.clone())),
                    None => {
                        // DR-70 ②: when a published route *was* found and refused,
                        // say why.  "a stale route degraded into a transport
                        // failure" is exactly what DR-43's explicit refusal must
                        // prevent, and a refusal that hides its reason is only
                        // half a refusal.
                        let refused = self
                            .route_refusal
                            .lock()
                            .ok()
                            .and_then(|refusal| refusal.clone());
                        match refused {
                            Some(reason) => anyhow::bail!(
                                "game_endpoint_unavailable: `{tool}` runs in the game process \
                                 and only the game endpoint serves it; the published route was \
                                 found and **refused**: {reason}. No request was sent, so this \
                                 is an explicit refusal, not a transport failure. Falling back \
                                 to the editor endpoint is not allowed (DR-43)."
                            ),
                            None => anyhow::bail!(
                                "game_endpoint_unavailable: `{tool}` runs in the game process \
                                 and only the game endpoint serves it; no game endpoint is \
                                 registered yet (`editor_play_scene` must have answered with \
                                 `endpoint` or `mcp_port`). Falling back to the editor endpoint \
                                 is not allowed (DR-43)."
                            ),
                        }
                    }
                }
            }
        }
    }

    /// DR-55: fold one call outcome into the endpoint's liveness record.
    ///
    /// `Ok` covers **every** answer, a JSON-RPC business error included: a
    /// business error is not a transport failure and must never count toward the
    /// streak (DR-56's classification is what keeps them apart).
    fn observe_liveness(&self, endpoint: &str, outcome: Result<(), ()>) {
        let Ok(mut map) = self.liveness.lock() else {
            return;
        };
        map.entry(endpoint.to_string())
            .or_insert_with(|| EndpointLiveness::new(endpoint))
            .observe(outcome);
    }

    /// DR-55: the liveness verdict of one endpoint.
    pub fn endpoint_state(&self, endpoint: &str) -> Option<EndpointLiveness> {
        self.liveness.lock().ok()?.get(endpoint).cloned()
    }

    /// DR-55: register a freshly announced endpoint so it starts from a clean
    /// slate.  A verdict about the previous address must not leak onto this one.
    fn arm_endpoint(&self, endpoint: &str) {
        if let Ok(mut map) = self.liveness.lock() {
            map.insert(
                endpoint.to_string(),
                EndpointLiveness::new(endpoint.to_string()),
            );
        }
    }

    /// DR-69 ①: adopt `record` as this channel's game route **without**
    /// publishing it again.
    ///
    /// The single place both [`ToolChannel::register_game_endpoint`] (the run
    /// that announced the endpoint) and [`ToolChannel::use_game_route_file`] (a
    /// later process reading the published record) go through, so the two
    /// cannot drift apart.
    fn install_game_route(&self, record: GameEndpointRecord) -> anyhow::Result<()> {
        let client = McpClient::new(
            record.endpoint.clone(),
            self.timeout_seconds,
            self.max_retries,
        )
        .with_max_sync_retries(self.max_sync_retries);
        // DR-55: a fresh endpoint starts alive, whatever happened to the address
        // it replaces.
        self.arm_endpoint(&record.endpoint);
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

    /// DR-69 ①: the path this channel publishes its game route to, if any.
    fn route_file(&self) -> Option<std::path::PathBuf> {
        self.game_route_file.lock().ok()?.clone()
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
        let (client, endpoint) = self.client_for(tool)?;
        // DR-55: an endpoint that has already been declared dead is not attempted
        // again — no request, no retry, no waiting.  The refusal carries
        // `UNAVAILABLE` and the stable `endpoint_state` field.
        if let Some(liveness) = self.endpoint_state(&endpoint) {
            if liveness.unavailable {
                return Err(endpoint::McpEndpointUnavailableError::new(liveness, tool).into());
            }
        }
        let tool_name = tool.to_string();
        let outcome = tokio::task::spawn_blocking(move || client.call_traced(&tool_name, args))
            .await
            .map_err(|error| anyhow::anyhow!("the MCP call task failed: {error}"))?;
        match outcome {
            Ok((payload, correlation)) => {
                self.observe_liveness(&endpoint, Ok(()));
                Ok((ToolResult { ok: true, payload }, correlation))
            }
            Err(error) => {
                let is_transport = error.downcast_ref::<McpTransportError>().is_some();
                if is_transport {
                    self.observe_liveness(&endpoint, Err(()));
                } else {
                    // A business error is an answer: the endpoint is alive.
                    self.observe_liveness(&endpoint, Ok(()));
                }
                Err(error)
            }
        }
    }

    async fn session_sync_probe(&self) -> SessionSyncReport {
        let client = self.editor.clone();
        tokio::task::spawn_blocking(move || client.session_sync_probe())
            .await
            .unwrap_or_else(|error| SessionSyncReport::unavailable(error.to_string()))
    }

    async fn register_game_endpoint(&self, record: GameEndpointRecord) -> anyhow::Result<()> {
        // DR-69 ①: the route is published **before** the registration is
        // returned, so a role process that starts the moment the battery
        // registered the endpoint can already resolve it.  A publish failure is
        // best effort: it must not fail the battery step that announced the
        // endpoint, and the in-process route below still works.
        if let Some(path) = self.route_file() {
            let _ = endpoint::publish_game_route(&path, &record);
        }
        self.install_game_route(record)
    }

    async fn clear_game_endpoint(&self) {
        if let Ok(mut guard) = self.game.lock() {
            *guard = None;
        }
        // DR-69 ①: a stopped game must not stay resolvable through the published
        // file either, or a later process would reach a dead port.
        if let Some(path) = self.route_file() {
            endpoint::withdraw_game_route(&path);
        }
    }

    /// DR-69 ①: point this channel at the run's published route and adopt what
    /// is already there.
    ///
    /// This is the whole of road (A): `HOH_GAME_ROUTE` names the file, and a
    /// fresh process resolves the same route the run registered.
    ///
    /// DR-70 ②: adoption is **checked** first (freshness, the recorded pid's
    /// liveness, and whether anything still answers there).  A stale record is
    /// refused here, so the caller keeps DR-43's explicit
    /// `game_endpoint_unavailable` instead of sending the call into an opaque
    /// transport failure — the acceptance's own counter-example (D6).
    fn use_game_route_file(&self, path: std::path::PathBuf) -> Option<GameEndpointRecord> {
        if let Ok(mut guard) = self.game_route_file.lock() {
            *guard = Some(path.clone());
        }
        let record = endpoint::load_game_route(&path)?;
        // A malformed record cannot be adopted; `load_game_route` already
        // refuses one, and the caller keeps failing loudly (DR-43).
        let refused = match endpoint::validate_published_route(&path, &record) {
            Ok(()) => None,
            Err(refusal) => Some(refusal.reason()),
        };
        if let Ok(mut guard) = self.route_refusal.lock() {
            *guard = refused.clone();
        }
        if refused.is_some() {
            return None;
        }
        self.install_game_route(record.clone()).ok()?;
        Some(record)
    }

    async fn game_endpoint(&self) -> Option<GameEndpointRecord> {
        self.game
            .lock()
            .ok()
            .and_then(|guard| guard.as_ref().map(|route| route.record.clone()))
    }

    async fn game_endpoint_history(&self) -> Option<GameEndpointRecord> {
        self.game_history
            .lock()
            .ok()
            .and_then(|guard| guard.clone())
    }

    async fn endpoint_liveness(&self, endpoint: &str) -> Option<EndpointLiveness> {
        self.endpoint_state(endpoint)
    }
}
