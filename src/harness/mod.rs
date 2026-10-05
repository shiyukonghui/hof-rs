//! The harness boundary: "turn a role invocation into one agent execution".

pub mod cap;
pub mod compact;
pub mod directive;
pub mod guard;
pub mod mini;
pub mod write_audit;

pub use cap::{cap_tool_output, CappedEnvironment, CappedOutput};
pub use compact::{compact_history, CompactPolicy, CompactStats};
pub use directive::{parse_directive, render_read, render_write, Directive};
pub use guard::{ArtifactKind, WriteGuardEnvironment};
pub use mini::MiniHarness;

use crate::runtime::role::{RoleInvocation, RoleOutcome};

/// A harness wraps one fixed harness–model configuration.  Implementations
/// must be stateless across calls: every `invoke` is an independent execution
/// (R1).
#[async_trait::async_trait]
pub trait Harness: Send + Sync {
    async fn invoke(&self, inv: &RoleInvocation) -> anyhow::Result<RoleOutcome>;
}
