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

use crate::adapter::engine::{self, EngineIdentity};
use crate::adapter::ProjectAdapter;

/// DR-44: the engine identity of this run.
///
/// `game_endpoint` is `None` for the first call — the endpoint does not exist
/// until `editor_play_scene` has run — and the block then carries the reason.
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
    let mut config = mini_swe_agent::environments::LocalEnvironmentConfig::default();
    config.cwd = workspace.to_string_lossy().into_owned();
    config.timeout = engine::PROBE_TIMEOUT_SECONDS;
    let environment = mini_swe_agent::environments::LocalEnvironment::new(config);
    let mut identity = engine::probe_identity(
        &environment,
        Some(&binary),
        Some(editor_endpoint),
        game_endpoint,
        serde_json::Value::Null,
    )
    .await;
    identity.kind = adapter.engine_kind().to_string();
    identity
}
