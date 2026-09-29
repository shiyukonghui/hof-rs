//! DR-43: the two MCP endpoints of the new contract.
//!
//! The engine's native MCP module serves `editor_*`, `project_*` and `os_*` on
//! the editor endpoint (9877).  The **running game is a separate process with
//! its own endpoint**: `editor_play_scene` starts it with an injected
//! `--mcp-port` and reports `endpoint` / `mcp_port` / `mcp_port_source` / `pid`
//! in its reply.  `running_game_*` tools exist **only** there.
//!
//! Routing is therefore a property of the tool name, and it is decided in one
//! place so the tool channel and the adapter cannot disagree.

use serde::{Deserialize, Serialize};

/// The channel a tool belongs to, derived from its name.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ToolScope {
    /// `editor_*`, `project_*`, `os_*` — served by the editor endpoint.
    Editor,
    /// `running_game_*` — served only by the game endpoint.
    Game,
}

/// The game channel's prefix (DR-42/DR-43).
pub const GAME_CHANNEL_PREFIX: &str = "running_game_";

/// The JSON-RPC path of the MCP module.
pub const MCP_PATH: &str = "/mcp";

/// DR-43: `mcp_port_source` when the port was passed as an explicit argument.
pub const SOURCE_ARGUMENT: &str = "argument";
/// DR-43: `mcp_port_source` when the engine picked a free port itself.
pub const SOURCE_AUTO_FREE_PORT: &str = "auto_free_port";
/// Recorded when the server announces a port but not its provenance.  Writing
/// one of the two documented values instead would be inventing a fact.
pub const SOURCE_UNDECLARED: &str = "undeclared";

/// The endpoint a tool of this name must be sent to.
pub fn scope_of(tool: &str) -> ToolScope {
    if tool.starts_with(GAME_CHANNEL_PREFIX) {
        ToolScope::Game
    } else {
        ToolScope::Editor
    }
}

/// `http://127.0.0.1:<port>/mcp` — the documented loopback form.
pub fn endpoint_for_port(port: u16) -> String {
    format!("http://127.0.0.1:{port}{MCP_PATH}")
}

/// The port of a loopback endpoint, when it carries one explicitly.
pub fn port_of_endpoint(endpoint: &str) -> Option<u16> {
    let authority = endpoint
        .split_once("://")
        .map(|(_, rest)| rest)
        .unwrap_or(endpoint);
    let authority = authority.split('/').next().unwrap_or(authority);
    let (_, port) = authority.rsplit_once(':')?;
    port.parse().ok()
}

/// DR-43: what `editor_play_scene` announced about the game endpoint.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct GameEndpointRecord {
    /// The JSON-RPC URL of the running game.
    pub endpoint: String,
    /// The injected port, when it can be determined.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub port: Option<u16>,
    /// `argument` | `auto_free_port` | `undeclared` (see [`SOURCE_UNDECLARED`]).
    pub source: String,
    /// The game process id, when the engine reported one.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub pid: Option<u32>,
}

/// DR-55: how many **consecutive transport-layer failures** kill an endpoint.
///
/// Two, not one: the first failure is still retried as before (a hiccup must not
/// cost a whole round), but a second consecutive one is a verdict.  `smoke-t6`
/// burned about 12 minutes re-attempting a game endpoint that had already
/// stopped answering at the transport layer.
pub const ENDPOINT_DEATH_THRESHOLD: u32 = 2;

/// DR-55: the liveness verdict of one endpoint, as a **stable evidence field**.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EndpointState {
    /// Still being attempted; the streak is below the threshold.
    Alive,
    /// Killed by [`ENDPOINT_DEATH_THRESHOLD`] consecutive transport failures.
    /// Every later call is refused immediately with `UNAVAILABLE`.
    Unavailable,
}

impl Default for EndpointState {
    fn default() -> Self {
        Self::Alive
    }
}

impl EndpointState {
    pub fn code(self) -> &'static str {
        match self {
            EndpointState::Alive => "alive",
            EndpointState::Unavailable => "unavailable",
        }
    }
}

/// DR-55: the recorded liveness of one endpoint.
///
/// The field names are the contract: `endpoint`, `state`, `unavailable`,
/// `consecutive_transport_failures` and `transport_failures_at_mark`.  A consumer
/// must be able to tell "the endpoint was declared dead" from "the tool answered
/// with a business error" without reading prose.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct EndpointLiveness {
    /// The endpoint this verdict is about (its JSON-RPC URL).
    pub endpoint: String,
    /// The stable verdict field.
    pub state: EndpointState,
    /// Whether this endpoint may not be attempted again.
    pub unavailable: bool,
    /// The current run of consecutive transport failures.  A success resets it;
    /// a business error never touches it (DR-56's classification decides).
    pub consecutive_transport_failures: u32,
    /// The streak at the moment the endpoint was marked unavailable, so the
    /// record can always answer "how many failures killed it?".
    pub transport_failures_at_mark: u32,
}

impl EndpointLiveness {
    pub fn new(endpoint: impl Into<String>) -> Self {
        Self {
            endpoint: endpoint.into(),
            state: EndpointState::Alive,
            unavailable: false,
            consecutive_transport_failures: 0,
            transport_failures_at_mark: 0,
        }
    }

    /// Fold one observed call outcome into the state.
    ///
    /// `outcome` is `Ok(())` for any answer — including a JSON-RPC **business
    /// error**, which is an answer, not a transport failure — and `Err(())` for a
    /// transport-layer failure.
    ///
    /// A dead endpoint stays dead and its counter is frozen: the record must say
    /// how many failures killed it, and later refusals are not failures of the
    /// endpoint (nothing was sent).
    pub fn observe(&mut self, outcome: Result<(), ()>) {
        if self.unavailable {
            return;
        }
        match outcome {
            Ok(()) => {
                self.consecutive_transport_failures = 0;
            }
            Err(()) => {
                self.consecutive_transport_failures += 1;
                if self.consecutive_transport_failures >= ENDPOINT_DEATH_THRESHOLD {
                    self.state = EndpointState::Unavailable;
                    self.unavailable = true;
                    self.transport_failures_at_mark = self.consecutive_transport_failures;
                }
            }
        }
    }

    /// The refusal every later call to a dead endpoint gets.  `UNAVAILABLE` and
    /// the stable field name are both present, so a judge can never read this as
    /// a clean or a business failure.
    pub fn refusal(&self, tool: &str) -> String {
        format!(
            "FAILED tool={tool} attempt(s)=0 code=n/a message=game_endpoint_unavailable: the \
             endpoint {endpoint} was marked {state} after {failures} consecutive transport \
             failures; no request was sent and no retry was made (UNAVAILABLE: this evidence \
             could not be collected) endpoint_state={json}",
            endpoint = self.endpoint,
            state = self.state.code(),
            failures = self.transport_failures_at_mark,
            json = serde_json::to_string(self).unwrap_or_else(|_| "{}".to_string()),
        )
    }
}

/// DR-55: the endpoint a failed call was sent to, when the failure is a
/// transport one.
pub fn transport_endpoint(error: &anyhow::Error) -> Option<String> {
    error
        .downcast_ref::<crate::tools::mcp::McpTransportError>()
        .map(|transport| transport.endpoint.clone())
}

/// DR-55: the refusal a dead endpoint answers with — a typed marker so the
/// retry ring and the readiness poll can recognise "no request was sent" from
/// "the server answered with an error" without parsing a message.
#[derive(Clone, Debug, PartialEq, Eq, thiserror::Error)]
#[error("{message}")]
pub struct McpEndpointUnavailableError {
    /// The verbatim refusal text (it carries `UNAVAILABLE`, the endpoint, the
    /// state and the failure count).
    pub message: String,
    /// The endpoint that was declared unavailable.
    pub endpoint: String,
    /// The recorded liveness verdict at the moment of the refusal.
    pub liveness: EndpointLiveness,
}

impl McpEndpointUnavailableError {
    pub fn new(liveness: EndpointLiveness, tool: &str) -> Self {
        Self {
            message: liveness.refusal(tool),
            endpoint: liveness.endpoint.clone(),
            liveness,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// DR-55: two consecutive transport failures kill the endpoint; a success
    /// resets the streak; a business error is not a transport failure at all.
    #[test]
    fn the_liveness_state_counts_consecutive_transport_failures_only() {
        let mut liveness = EndpointLiveness::new("http://127.0.0.1:1/mcp");
        assert!(!liveness.unavailable);
        assert_eq!(liveness.consecutive_transport_failures, 0);

        // One transport failure: not dead (the first failure still retries).
        liveness.observe(Err(()));
        assert_eq!(liveness.consecutive_transport_failures, 1);
        assert!(!liveness.unavailable);

        // A success resets the streak.
        liveness.observe(Ok(()));
        assert_eq!(liveness.consecutive_transport_failures, 0);

        // Business errors are answers: `Ok` in this fold, they never count.
        for _ in 0..5 {
            liveness.observe(Ok(()));
        }
        assert_eq!(liveness.consecutive_transport_failures, 0);
        assert!(!liveness.unavailable);

        // Two consecutive failures: dead, and the mark records the count.
        liveness.observe(Err(()));
        liveness.observe(Err(()));
        assert!(liveness.unavailable);
        assert_eq!(liveness.transport_failures_at_mark, 2);
        assert_eq!(liveness.state.code(), "unavailable");

        // A dead endpoint stays dead and its mark is frozen.
        liveness.observe(Err(()));
        liveness.observe(Err(()));
        assert_eq!(liveness.transport_failures_at_mark, 2);
        assert_eq!(liveness.consecutive_transport_failures, 2);
    }

    /// DR-55: the refusal text carries the stable field name and the count, so a
    /// reader can tell when the endpoint died and how many failures it took.
    #[test]
    fn the_refusal_names_the_state_and_the_failure_count() {
        let mut liveness = EndpointLiveness::new("http://127.0.0.1:65333/mcp");
        liveness.observe(Err(()));
        liveness.observe(Err(()));
        let text = liveness.refusal("running_game_get_node_property_samples");
        assert!(text.contains("UNAVAILABLE"), "{text}");
        assert!(text.contains("game_endpoint_unavailable"), "{text}");
        assert!(text.contains("endpoint_state"), "{text}");
        assert!(text.contains("2 consecutive transport failures"), "{text}");
        assert!(text.contains("attempt(s)=0"), "{text}");
        assert!(
            text.contains("running_game_get_node_property_samples"),
            "{text}"
        );
    }

    #[test]
    fn the_scope_comes_from_the_channel_prefix() {
        assert_eq!(scope_of("editor_get_errors"), ToolScope::Editor);
        assert_eq!(scope_of("project_get_info"), ToolScope::Editor);
        assert_eq!(scope_of("os_deploy_to_android_device"), ToolScope::Editor);
        assert_eq!(scope_of("running_game_get_scene_tree"), ToolScope::Game);
        // Anything unrecognised stays on the editor endpoint: that endpoint is
        // the one a caller can always be told about.
        assert_eq!(scope_of("not_a_tool"), ToolScope::Editor);
    }

    #[test]
    fn the_loopback_endpoint_round_trips_through_its_port() {
        assert_eq!(endpoint_for_port(9877), "http://127.0.0.1:9877/mcp");
        assert_eq!(port_of_endpoint("http://127.0.0.1:9877/mcp"), Some(9877));
        assert_eq!(port_of_endpoint("127.0.0.1:9999/mcp"), Some(9999));
        assert_eq!(port_of_endpoint("http://127.0.0.1/mcp"), None);
    }
}
