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

#[cfg(test)]
mod tests {
    use super::*;

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
