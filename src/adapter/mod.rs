//! The project adapter boundary: everything project-type specific (what `A₀`
//! looks like, how to run a deterministic check, how to collect evidence)
//! lives behind this trait, so Godot is just the first implementation (A3).

pub mod engine;
pub mod godot;
pub mod test_adapter;

pub use engine::EngineIdentity;
pub use godot::GodotAdapter;
pub use test_adapter::TestAdapter;

use std::path::{Path, PathBuf};

use crate::model::{ArtifactGate, ExecKind, ExecRecord, Role};
use crate::tools::ToolChannel;

/// DR-24/DR-44: the battery steps that decide `launchable`.
///
/// The first two are mandatory — an adapter that declares neither has no gate.
/// `engine_identity` is a gate step **when the battery declares it**, which is
/// exactly when the adapter drives a real engine binary (DR-44 ⑤).
pub const GATE_STEP_IDS: &[&str] = &[
    "editor_errors_baseline",
    "play_scene_ready",
    engine::ENGINE_IDENTITY_STEP_ID,
];
/// DR-24: the step that reloads the project and opens the main scene before the
/// editor is asked for its errors.
pub const PROJECT_RELOAD_STEP_ID: &str = "project_reload_and_open";
/// DR-24: the `.tscn` structure validator step.
pub const SCENE_STRUCTURE_STEP_ID: &str = "scene_structure";

/// DR-24: evaluate the pre-freeze gate from one battery pass.
///
/// `launchable := editor_errors_baseline.ok && play_scene_ready.ok` (plus every
/// other declared gate step, i.e. `engine_identity` — DR-44 ⑤).  When the
/// battery declares neither required step (an adapter without a gate), the gate
/// is reported as *not applicable* rather than silently "open": a check that did
/// not run must never be confused with a check that passed.
pub fn evaluate_launchable(records: &[BatteryRecord]) -> ArtifactGate {
    let find = |id: &str| records.iter().find(|record| record.step_id == id);
    let (Some(_editor), Some(_play)) = (find(GATE_STEP_IDS[0]), find(GATE_STEP_IDS[1])) else {
        return ArtifactGate::not_applicable(format!(
            "gate_not_applicable: this adapter's battery declares no `{}`/`{}` step",
            GATE_STEP_IDS[0], GATE_STEP_IDS[1]
        ));
    };

    let mut reasons = Vec::new();
    // Every declared gate step must be ok.  A gate step the battery did not
    // declare (an adapter without an engine binary, DR-44) is skipped instead of
    // being invented.
    for id in GATE_STEP_IDS {
        if let Some(record) = find(id).filter(|record| !record.ok) {
            reasons.push(format!("{}: {}", record.step_id, record.record.observation));
        }
    }
    // DR-24: the scene-structure hint is the most actionable part of the
    // failure; it belongs in the gate reasons as well as in the repair context.
    if let Some(structure) = find(SCENE_STRUCTURE_STEP_ID).filter(|record| !record.ok) {
        reasons.push(format!(
            "{}: {}",
            structure.step_id, structure.record.observation
        ));
    }

    ArtifactGate {
        applicable: true,
        launchable: reasons.is_empty(),
        reasons,
    }
}

/// DR-24: the actionable text handed to a repair call.
pub fn repair_context(records: &[BatteryRecord]) -> String {
    let mut text = String::from(
        "LAUNCH GATE FAILED. The deterministic evidence battery could not start the frozen \
         candidate. Fix ONLY what is needed to make the project launchable: repair the main \
         scene / scripts so that `editor_get_errors` is clean and the main scene boots. Do not \
         add features, do not start new work, do not restructure the project.\n\nFailed battery \
         evidence (verbatim):\n",
    );
    for record in records {
        if !record.ok {
            text.push_str(&format!(
                "- {}: {}\n",
                record.step_id, record.record.observation
            ));
        }
    }
    text
}

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

    /// DR-37: is the Developer role's artifact (the project itself) at least
    /// *usable*?
    ///
    /// DR-18's wrap-up retry exists to rescue a round whose artifact is missing;
    /// `smoke-t5` showed it being spent on a Developer whose artifact was
    /// already valid (0.94M tokens / 3.1 minutes, no change to the increment).
    /// The retry is therefore gated on this answer.
    ///
    /// The default is **`false`** — the conservative answer DR-37 demands when
    /// validity cannot be established, and the behaviour every adapter had
    /// before this check existed.
    fn developer_artifact_valid(&self, _workspace: &Path) -> bool {
        false
    }

    /// Markdown playbook injected into the Tester's view.
    fn evidence_playbook(&self) -> String;

    /// Tools visible to a role (used to build `TOOLS.md`).
    fn tool_policy(&self, role: Role) -> Vec<String>;

    /// DR-44: the engine binary this adapter drives, when it has one.
    ///
    /// `None` means "this adapter does not identify an engine": the runtime then
    /// records an all-`null` `meta.json.engine` block (with a reason) and adds
    /// no `engine_identity` gate step, because there is no identity to check.
    fn engine_binary(&self) -> Option<PathBuf> {
        None
    }

    /// DR-44: the engine kind written into `meta.json.engine.kind`.
    fn engine_kind(&self) -> &'static str {
        engine::ENGINE_KIND_UNKNOWN
    }

    fn doctor(&self, workspace: &Path) -> anyhow::Result<Vec<DoctorItem>>;
}
