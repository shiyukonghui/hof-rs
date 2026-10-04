//! The Bevy tool channel: the role-facing half of the thin MCP server
//! (DESIGN-OVERVIEW §1, DESIGN-DETAIL §2).
//!
//! `McpChannel` speaks to a long-lived *engine module* that exposes an MCP
//! server over HTTP.  Bevy has no such thing: the game exposes Bevy Remote
//! Protocol (`127.0.0.1:15702`), and the MCP tool surface is **this crate's own
//! library**.  So this channel is deliberately simpler than `McpChannel` — it
//! holds one gateway to one BRP endpoint and calls the frozen tool surface
//! directly — and it is what makes a role's separate `hoh tools call` process
//! able to observe the game the runtime started (DR-69/DR-70).
//!
//! Two behaviours are inherited from `McpChannel` on purpose, because a role's
//! shell depends on them:
//!
//! * **the published route** (`HOH_GAME_ROUTE` → `use_game_route_file`) is the
//!   only way a fresh process learns the endpoint, and a stale route is
//!   **refused with a reason** rather than degraded into a transport failure
//!   (DR-43/DR-70 ②);
//! * **the call is denied before anything is sent** (R13): `allowed` is checked
//!   first, so a forbidden tool never reaches the wire.
//!
//! A role's calls are raw evidence too.  When the channel knows the round's
//! directory (the route file lives in it), every call is written verbatim to
//! `role-calls/<role>-<seq>-<tool>.json` **inside that round's directory** — the
//! one place `runs/**` may be written (REQUIREMENTS §4.6) — so "the Tester
//! observed it" is checkable against the bytes the game answered.

use std::path::PathBuf;
use std::sync::Mutex;

use serde_json::Value;

use crate::adapter::bevy::brp;
use crate::adapter::bevy::project::role_session;
use crate::adapter::bevy::round::{describe, Session, SESSION_TIMEOUT};
use crate::adapter::mcp::evidence::CallEvidence;
use crate::model::Role;
use crate::tools::endpoint::{self, GameEndpointRecord};
use crate::tools::{ToolChannel, ToolResult};

/// The sub-directory of a round directory that holds the **roles'** raw calls.
/// The battery's own calls live in `calls/`; keeping them apart means a
/// reader can tell "the adapter observed this" from "a role observed this".
pub const ROLE_CALLS_DIR: &str = "role-calls";

/// The tool channel a Bevy round and every role process uses.
#[derive(Debug)]
pub struct BevyToolChannel {
    /// The endpoint the channel currently talks to: the pinned main-world
    /// endpoint until a route is installed.
    endpoint: Mutex<String>,
    session: Mutex<Session>,
    /// DR-69 ①: where the run publishes its route, when this channel knows.
    route_file: Mutex<Option<PathBuf>>,
    route: Mutex<Option<GameEndpointRecord>>,
    /// DR-51: the last endpoint ever registered, kept after the route is cleared.
    history: Mutex<Option<GameEndpointRecord>>,
    /// DR-70 ②: why a published route was refused, when one was.
    refusal: Mutex<Option<String>>,
}

impl BevyToolChannel {
    /// A channel on the pinned endpoint (15702) until a route says otherwise.
    pub fn new() -> Self {
        let endpoint = brp::endpoint();
        Self {
            session: Mutex::new(Session::new(&endpoint, SESSION_TIMEOUT)),
            endpoint: Mutex::new(endpoint),
            route_file: Mutex::new(None),
            route: Mutex::new(None),
            history: Mutex::new(None),
            refusal: Mutex::new(None),
        }
    }

    /// A channel pointed at another endpoint (a test with an in-process fake).
    pub fn at(endpoint: impl Into<String>) -> Self {
        let channel = Self::new();
        let endpoint = endpoint.into();
        channel.install_endpoint(&endpoint, None);
        channel
    }

    pub fn endpoint(&self) -> String {
        self.endpoint
            .lock()
            .map(|endpoint| endpoint.clone())
            .unwrap_or_else(|poisoned| poisoned.into_inner().clone())
    }

    /// Point the channel at `endpoint`, replacing the BRP gateway.
    fn install_endpoint(&self, endpoint: &str, pid: Option<u32>) {
        let mut endpoint_lock = match self.endpoint.lock() {
            Ok(lock) => lock,
            Err(poisoned) => poisoned.into_inner(),
        };
        *endpoint_lock = endpoint.to_string();
        let mut session = match self.session.lock() {
            Ok(lock) => lock,
            Err(poisoned) => poisoned.into_inner(),
        };
        *session = role_session(endpoint, pid);
    }

    /// Adopt a route in memory (no publication).
    fn install_route(&self, record: GameEndpointRecord) {
        self.install_endpoint(&record.endpoint, record.pid);
        if let Ok(mut route) = self.route.lock() {
            *route = Some(record.clone());
        }
        if let Ok(mut history) = self.history.lock() {
            *history = Some(record);
        }
    }

    /// Write one role call's raw evidence inside the round's own directory.
    ///
    /// Best effort by design: failing to keep a copy of the call must never turn
    /// the call itself into a failure, and there is no evidence directory to
    /// write to when the channel was never told where the round lives.
    ///
    /// DR-96 ①: the name is stamped with the call's own **timestamp**, not with
    /// [`CallEvidence::seq`].  Every `hoh tools call` is a separate process, so
    /// the session counter restarts at 1: naming by `seq` let the second call of
    /// a tool overwrite the first, and round 1 kept one file per tool although
    /// its roles made ~295 calls between them.
    fn record_role_call(&self, role: Role, evidence: &CallEvidence) {
        let Some(directory) = self.role_calls_dir() else {
            return;
        };
        if std::fs::create_dir_all(&directory).is_err() {
            return;
        }
        let tool = crate::adapter::mcp::evidence::sanitize_tool_name(&evidence.tool);
        let mut name = format!("{}-{}-{}.json", role.as_str(), evidence.timestamp_ms, tool);
        // Two calls in the same millisecond are still two calls: never overwrite.
        let mut attempt = 1_u32;
        while directory.join(&name).exists() {
            attempt += 1;
            name = format!(
                "{}-{}-{}-{}.json",
                role.as_str(),
                evidence.timestamp_ms,
                tool,
                attempt
            );
        }
        let _ = std::fs::write(
            directory.join(name),
            serde_json::to_string_pretty(&evidence.to_json()).unwrap_or_default(),
        );
    }

    /// `runs/<run-id>/role-calls`, derived from the published route's path.
    fn role_calls_dir(&self) -> Option<PathBuf> {
        let path = self.route_file.lock().ok()?.clone()?;
        Some(path.parent()?.join(ROLE_CALLS_DIR))
    }
}

impl Default for BevyToolChannel {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait::async_trait]
impl ToolChannel for BevyToolChannel {
    fn allowed(&self, role: Role, tool: &str) -> bool {
        crate::tools::policy::tool_allowed(role, tool)
    }

    /// DR-26: the index carries the real schemas of the **frozen** Bevy tool
    /// list, filtered by the role matrix, so a role never has to read this
    /// crate's sources to learn an argument name.
    fn index_markdown(&self, role: Role) -> String {
        let list = crate::adapter::mcp::tool_list();
        let schemas: Vec<Value> = list
            .get("tools")
            .and_then(Value::as_array)
            .cloned()
            .unwrap_or_default();
        crate::tools::index::render_tools_markdown(role, &schemas)
    }

    async fn call(&self, role: Role, tool: &str, args: Value) -> anyhow::Result<ToolResult> {
        if !self.allowed(role, tool) {
            anyhow::bail!("tool_not_permitted: role={} tool={tool}", role.as_str());
        }
        if let Some(reason) = self.refusal.lock().ok().and_then(|refusal| refusal.clone()) {
            anyhow::bail!(
                "game_endpoint_unavailable: the published game route was found and **refused**: \
                 {reason}. No request was sent, so this is an explicit refusal, not a transport \
                 failure (DR-43)."
            );
        }
        let (call, evidence) = {
            let mut session = match self.session.lock() {
                Ok(lock) => lock,
                Err(poisoned) => poisoned.into_inner(),
            };
            session.call_with_evidence(tool, args)
        };
        self.record_role_call(role, &evidence);
        match call.error {
            Some(error) => anyhow::bail!("`{tool}`: {}", describe(&error)),
            None => Ok(ToolResult {
                ok: true,
                payload: call.result.unwrap_or(Value::Null),
            }),
        }
    }

    /// DR-69 ①: adopt the route the run published, checking it first.
    fn use_game_route_file(&self, path: PathBuf) -> Option<GameEndpointRecord> {
        if let Ok(mut slot) = self.route_file.lock() {
            *slot = Some(path.clone());
        }
        let record = endpoint::load_game_route(&path)?;
        let refused = match endpoint::validate_published_route(&path, &record) {
            Ok(()) => None,
            Err(refusal) => Some(refusal.reason()),
        };
        if let Ok(mut slot) = self.refusal.lock() {
            *slot = refused.clone();
        }
        if refused.is_some() {
            return None;
        }
        self.install_route(record.clone());
        Some(record)
    }

    /// DR-71 ①: adopt an announced endpoint **without** publishing it.
    async fn install_game_endpoint(&self, record: GameEndpointRecord) -> anyhow::Result<()> {
        self.install_route(record);
        Ok(())
    }

    /// DR-71 ①: publish the route this channel holds, surfacing any failure.
    async fn publish_game_endpoint(&self) -> anyhow::Result<()> {
        let Some(path) = self.route_file.lock().ok().and_then(|slot| slot.clone()) else {
            // No published-route file was configured: there is nothing to
            // publish, and that is not a failure.
            return Ok(());
        };
        let record = self
            .route
            .lock()
            .ok()
            .and_then(|slot| slot.clone())
            .ok_or_else(|| {
                anyhow::anyhow!(
                    "no game endpoint is installed, so there is nothing to publish to {path:?}"
                )
            })?;
        endpoint::publish_game_route(&path, &record).map_err(|error| {
            anyhow::anyhow!(
                "the game route {path:?} could not be published for endpoint `{}`: {error}",
                record.endpoint
            )
        })
    }

    /// DR-43: the game endpoint is gone.  Later calls must fail rather than
    /// reach a stale port, so the published file goes with it.
    async fn clear_game_endpoint(&self) {
        if let Ok(mut route) = self.route.lock() {
            *route = None;
        }
        if let Some(path) = self.route_file.lock().ok().and_then(|slot| slot.clone()) {
            endpoint::withdraw_game_route(&path);
        }
    }

    async fn game_endpoint(&self) -> Option<GameEndpointRecord> {
        self.route.lock().ok().and_then(|route| route.clone())
    }

    async fn game_endpoint_history(&self) -> Option<GameEndpointRecord> {
        self.history.lock().ok().and_then(|history| history.clone())
    }
}

/// The endpoint a role's channel should start from, given a configuration: the
/// pinned main-world endpoint.  A published route replaces it; a round does not
/// choose a port (SPIKE-2 §0.4).
pub fn default_endpoint() -> String {
    brp::endpoint()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::adapter::mcp::TOOL_COUNT;
    use serde_json::json;
    use std::path::Path;

    #[test]
    fn the_channel_starts_on_the_pinned_endpoint_and_advertises_the_frozen_surface() {
        let channel = BevyToolChannel::new();
        assert_eq!(channel.endpoint(), brp::endpoint());
        let markdown = channel.index_markdown(Role::Tester);
        for tool in ["bevy_coin_counter", "bevy_wait_frames", "world.query"] {
            assert!(
                markdown.contains(tool),
                "`{tool}` must be in the Tester's index"
            );
        }
        assert!(markdown.contains("bevy_inject_move"));
        assert!(channel
            .index_markdown(Role::Planner)
            .contains("may not call"));
        assert_eq!(
            crate::adapter::mcp::all_tools().len(),
            TOOL_COUNT,
            "the advertised surface is the frozen one"
        );
    }

    #[test]
    fn a_denied_tool_is_refused_before_any_request_is_made() {
        // Port nothing listens on: if the denial were checked after the call,
        // this would surface as a transport error instead of a policy refusal.
        let channel =
            BevyToolChannel::at(format!("http://127.0.0.1:{}/", brp::fake::refused_port()));
        let runtime = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .expect("a runtime");
        let error = runtime
            .block_on(channel.call(Role::Tester, "editor_add_node", Value::Null))
            .expect_err("a forbidden tool is refused");
        assert!(error.to_string().contains("tool_not_permitted"), "{error}");
    }

    #[test]
    fn a_call_on_a_dead_endpoint_is_a_typed_failure_not_a_value() {
        let channel =
            BevyToolChannel::at(format!("http://127.0.0.1:{}/", brp::fake::refused_port()));
        let runtime = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .expect("a runtime");
        let error = runtime
            .block_on(channel.call(Role::Tester, "bevy_coin_counter", serde_json::json!({})))
            .expect_err("a dead endpoint is not a reading");
        let text = error.to_string();
        assert!(text.contains("bevy_coin_counter"), "{text}");
        assert!(text.contains("transport"), "{text}");
    }

    #[test]
    fn a_missing_route_file_is_not_adopted() {
        let channel = BevyToolChannel::new();
        assert_eq!(
            channel.use_game_route_file(PathBuf::from("no/such/route.json")),
            None
        );
        assert_eq!(
            channel.endpoint(),
            brp::endpoint(),
            "a refused route must not re-point the channel"
        );
    }

    #[test]
    fn the_role_calls_directory_is_derived_from_the_route_file_only() {
        let channel = BevyToolChannel::new();
        assert!(channel.role_calls_dir().is_none());
        if let Ok(mut slot) = channel.route_file.lock() {
            *slot = Some(Path::new("F:/runs/r1/game_endpoint.json").to_path_buf());
        }
        assert_eq!(
            channel.role_calls_dir(),
            Some(Path::new("F:/runs/r1").join(ROLE_CALLS_DIR)),
            "a role's calls are evidence inside the round's own directory"
        );
    }

    /// DR-96 ①: a role's calls are separate processes, so their session counters
    /// both start at 1.  A second call of the same tool must add a file, not
    /// replace the first one — round 1 lost 285 of its 295 role calls to exactly
    /// that overwrite.
    #[test]
    fn two_calls_of_one_tool_leave_two_files() {
        let temp = tempfile::tempdir().expect("a temporary root");
        let channel = BevyToolChannel::new();
        if let Ok(mut slot) = channel.route_file.lock() {
            *slot = Some(temp.path().join("game_endpoint.json"));
        }
        let call = |tool: &str, timestamp_ms: u128| CallEvidence {
            seq: 1,
            tool: tool.to_string(),
            layer: "semantic",
            brp_methods: vec!["world.get_resources".to_string()],
            requests: vec![json!({"resource": "hof_game::contract::CoinCounter"})],
            responses: vec![json!({"value": {"coins": 1}})],
            result: Some(json!({"coins": 1, "frame": 12})),
            error: None,
            timestamp_ms,
        };
        channel.record_role_call(Role::Tester, &call("bevy_coin_counter", 1_791_000_000_000));
        channel.record_role_call(Role::Tester, &call("bevy_coin_counter", 1_791_000_000_001));
        // The same millisecond is still a second call.
        channel.record_role_call(Role::Tester, &call("bevy_coin_counter", 1_791_000_000_001));
        let directory = channel.role_calls_dir().expect("the route names the round");
        let mut names: Vec<String> = std::fs::read_dir(&directory)
            .expect("the directory exists")
            .flatten()
            .map(|entry| entry.file_name().to_string_lossy().into_owned())
            .collect();
        names.sort();
        assert_eq!(
            names,
            vec![
                "tester-1791000000000-bevy_coin_counter.json",
                "tester-1791000000001-bevy_coin_counter-2.json",
                "tester-1791000000001-bevy_coin_counter.json",
            ],
            "every call keeps its own raw evidence file"
        );
    }
}
