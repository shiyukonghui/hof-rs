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
    ///
    /// **Only caches.**  DR-11: everything listed here is invisible to
    /// [`crate::runtime::policy::hash_tree`] and to the snapshot store, so
    /// putting a real artifact path here silently disables the R2/R3
    /// write-detection for that path.
    fn cache_excludes(&self) -> Vec<String>;

    /// Deterministic build/boot check.  DR-1: it runs against the **real
    /// workspace** (which is also the project the editor has open, D7) and
    /// *before* `A_t` is frozen, so anything it produces is part of the
    /// candidate identity instead of showing up later as pre-QA drift.
    async fn build_check(
        &self,
        workspace: &Path,
        tools: &dyn ToolChannel,
    ) -> anyhow::Result<Vec<ExecRecord>>;

    /// Markdown playbook injected into the Tester's view.
    fn evidence_playbook(&self) -> String;

    /// Tools visible to a role (used to build `TOOLS.md`).
    fn tool_policy(&self, role: Role) -> Vec<String>;

    fn doctor(&self, workspace: &Path) -> anyhow::Result<Vec<DoctorItem>>;
}
