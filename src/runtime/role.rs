//! Role invocation transaction types (R1).

use std::collections::BTreeMap;
use std::path::PathBuf;

use crate::config::AgentLimits;
use crate::model::{Role, Usage};

/// Everything one role call needs.  The harness only sees this value: there is
/// no shared conversation state between roles by construction.
#[derive(Clone, Debug)]
pub struct RoleInvocation {
    pub role: Role,
    pub iteration: u32,
    /// Fully rendered system prompt (no jinja syntax left).
    pub system_prompt: String,
    /// Fully rendered task prompt.
    pub task_prompt: String,
    /// Role view root.
    pub cwd: PathBuf,
    pub env: BTreeMap<String, String>,
    pub limits: AgentLimits,
    /// Model configuration passed to mini untouched.
    pub model: serde_json::Value,
    pub trajectory_path: PathBuf,
    /// Schema-failure text for attempt 2/3.
    pub retry_context: Option<String>,
}

/// Result of one role call.
#[derive(Clone, Debug)]
pub struct RoleOutcome {
    pub role: Role,
    pub iteration: u32,
    pub attempts: u32,
    pub exit_status: String,
    pub submission: String,
    pub trajectory_path: PathBuf,
    pub usage: Usage,
    pub duration_ms: u64,
    /// Round-5 cost repair: what the context fold did to this call.
    ///
    /// `None` for a harness that does not fold (the offline test harness and
    /// any other double), which is the honest value — "no fold was applied" is
    /// not the same fact as "a fold removed zero bytes".
    pub compaction: Option<crate::harness::compact::CompactStats>,
    /// Round-5 cost repair: how many model calls this call made, as the guard
    /// counted them.  It is the number `step_limit` is written in, so recording
    /// it makes "the budget bound this call" checkable from the result.
    pub steps: u64,
}
