//! The harness boundary: "turn a role invocation into one agent execution".

pub mod mini;

pub use mini::MiniHarness;

use crate::runtime::role::{RoleInvocation, RoleOutcome};

/// A harness wraps one fixed harness–model configuration.  Implementations
/// must be stateless across calls: every `invoke` is an independent execution
/// (R1).
#[async_trait::async_trait]
pub trait Harness: Send + Sync {
    async fn invoke(&self, inv: &RoleInvocation) -> anyhow::Result<RoleOutcome>;
}
