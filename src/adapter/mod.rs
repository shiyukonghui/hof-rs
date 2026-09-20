//! The project adapter boundary: everything project-type specific (what `A₀`
//! looks like, how to run a deterministic check, how to collect evidence)
//! lives behind this trait, so Godot is just the first implementation (A3).

pub mod godot;
pub mod test_adapter;

pub use godot::GodotAdapter;
pub use test_adapter::TestAdapter;

use std::path::Path;

use crate::model::{ExecKind, ExecRecord, Role};
use crate::tools::ToolChannel;

/// One deterministic build/boot observation produced by the adapter.
#[derive(Clone, Debug)]
pub struct BuildRecord {
    pub kind: ExecKind,
    pub path: Option<String>,
    pub observation: String,
}

#[derive(Clone, Debug, serde::Serialize, serde::Deserialize)]
pub struct DoctorItem {
    pub name: String,
    pub ok: bool,
    pub detail: String,
}

#[async_trait::async_trait]
pub trait ProjectAdapter: Send + Sync {
    /// Idempotent `A₀` scaffolding.
    fn initialize(&self, workspace: &Path) -> anyhow::Result<()>;

    /// Cache directories that must never enter a view, a hash, or a snapshot.
    fn cache_excludes(&self) -> Vec<String>;

    /// Deterministic build/boot check against the candidate view.
    async fn build_check(
        &self,
        candidate_view: &Path,
        tools: &dyn ToolChannel,
    ) -> anyhow::Result<Vec<ExecRecord>>;

    /// Markdown playbook injected into the Tester's view.
    fn evidence_playbook(&self) -> String;

    /// Tools visible to a role (used to build `TOOLS.md`).
    fn tool_policy(&self, role: Role) -> Vec<String>;

    fn doctor(&self, workspace: &Path) -> anyhow::Result<Vec<DoctorItem>>;
}
