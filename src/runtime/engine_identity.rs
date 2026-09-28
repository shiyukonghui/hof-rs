//! DR-44: assembling the engine identity for a run.
//!
//! The adapter says *which* binary it drives (`ProjectAdapter::engine_binary`)
//! and the probe says *what that binary is* (size, digest, verbatim
//! `--version`) and *who is actually listening* on the editor port.  Everything
//! goes through mini's existing [`mini_swe_agent::Environment`] abstraction:
//! that is what keeps this checkable offline against a fake environment, and
//! why no crate dependency was added for one pre-flight probe.
//!
//! This module is the only place that constructs a real
//! `LocalEnvironment` for the probe, and it does so **only** when the adapter
//! declares an engine binary.

use std::path::Path;

use serde_json::Value;

use crate::adapter::engine::{self, EngineIdentity};
use crate::adapter::ProjectAdapter;

/// DR-51: how long the `GET /mcp` status read may take.
///
/// Short on purpose: it is a pre-flight fact, not a tool call, and a slow or
/// dead endpoint must never delay the run.
pub const STATUS_TIMEOUT_SECONDS: u64 = 5;

/// DR-51: the `GET /mcp` body to record, or `Value::Null`.
///
/// Split out of [`probe`] so the gate ("only an adapter that drives an engine
/// may touch the network") and the two outcomes ("the real body" / "null + the
/// existing reason on any failure") are testable without a live endpoint.
/// `fetch` is injected for exactly that reason; [`probe`] passes
/// [`crate::tools::mcp::fetch_editor_status`].
pub fn editor_status_for(
    drives_engine: bool,
    editor_endpoint: &str,
    fetch: impl FnOnce(&str) -> Result<Value, String>,
) -> Value {
    if !drives_engine {
        // An adapter that drives no engine must not touch the network at all;
        // `EngineIdentity::unavailable`'s null+reason contract stays intact.
        return Value::Null;
    }
    match fetch(editor_endpoint) {
        Ok(body) => body,
        // A failed status read is a reason, never a run failure: the field stays
        // `null` and `probe_identity` attaches the reason.
        Err(_) => Value::Null,
    }
}

/// DR-44: the engine identity of this run.
///
/// `game_endpoint` is `None` for the first call — the endpoint does not exist
/// until `editor_play_scene` has run — and the block then carries the reason.
/// DR-51: `editor_status` is the verbatim `GET /mcp` body, read here.
pub async fn probe(
    adapter: &dyn ProjectAdapter,
    workspace: &Path,
    editor_endpoint: &str,
    game_endpoint: Option<crate::tools::endpoint::GameEndpointRecord>,
) -> EngineIdentity {
    let Some(binary) = adapter.engine_binary() else {
        return EngineIdentity::unavailable(format!(
            "this adapter ({}) drives no engine binary, so there is no identity to check",
            adapter.engine_kind()
        ));
    };
    // DR-51: the status is read before the identity is assembled, so the block
    // carries the real body (or `null`, with the reason `probe_identity` adds).
    let editor_status = editor_status_for(true, editor_endpoint, |endpoint| {
        crate::tools::mcp::fetch_editor_status(endpoint, STATUS_TIMEOUT_SECONDS)
    });
    let mut config = mini_swe_agent::environments::LocalEnvironmentConfig::default();
    config.cwd = workspace.to_string_lossy().into_owned();
    config.timeout = engine::PROBE_TIMEOUT_SECONDS;
    let environment = mini_swe_agent::environments::LocalEnvironment::new(config);
    let mut identity = engine::probe_identity(
        &environment,
        Some(&binary),
        Some(editor_endpoint),
        game_endpoint,
        editor_status,
    )
    .await;
    identity.kind = adapter.engine_kind().to_string();
    identity
}
