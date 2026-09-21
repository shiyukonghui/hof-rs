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

/// DR-17: one declared step of the deterministic evidence battery.
#[derive(Clone, Debug, serde::Serialize, serde::Deserialize)]
pub struct BatteryStep {
    pub id: String,
    /// The PRD requirements this step can produce evidence for (`F1..F17`,
    /// `N1..N4`).  It is the skeleton a Tester claim is checked against.
    pub supports: Vec<String>,
    pub timeout_secs: u64,
    pub retries: u32,
}

/// DR-17: the outcome of one battery step.
///
/// `ok = false` means **the evidence is unavailable**, not that the product
/// failed: the observation carries the raw JSON-RPC code/message so the Tester
/// records a `gap` for the steps this one supports instead of inventing proof.
#[derive(Clone, Debug, serde::Serialize, serde::Deserialize)]
pub struct BatteryRecord {
    pub step_id: String,
    pub supports: Vec<String>,
    pub record: ExecRecord,
    pub ok: bool,
    /// Relative (POSIX) path of the raw payload, under
    /// `.hoh/deterministic/raw/`.
    pub raw_path: Option<String>,
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

    /// DR-17: the deterministic **evidence battery**.
    ///
    /// Runs on the real workspace before the freeze, writes every raw payload
    /// under `<workspace>/.hoh/deterministic/raw/`, and returns one record per
    /// declared step.  The default implementation adapts [`Self::build_check`]
    /// so an adapter that has no battery yet still works; `GodotAdapter`
    /// overrides it with the real seven-step battery.
    async fn evidence_battery(
        &self,
        workspace: &Path,
        tools: &dyn ToolChannel,
    ) -> anyhow::Result<Vec<BatteryRecord>> {
        let records = self.build_check(workspace, tools).await?;
        Ok(records
            .into_iter()
            .enumerate()
            .map(|(index, record)| BatteryRecord {
                step_id: format!("build_check_{index}"),
                supports: Vec::new(),
                ok: record.observation.contains("no errors") || record.path.is_some(),
                record,
                raw_path: None,
            })
            .collect())
    }

    /// Markdown playbook injected into the Tester's view.
    fn evidence_playbook(&self) -> String;

    /// Tools visible to a role (used to build `TOOLS.md`).
    fn tool_policy(&self, role: Role) -> Vec<String>;

    fn doctor(&self, workspace: &Path) -> anyhow::Result<Vec<DoctorItem>>;
}
