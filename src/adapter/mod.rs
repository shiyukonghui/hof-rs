//! The project adapter boundary: everything project-type specific (what `A₀`
//! looks like, how to run a deterministic check, how to collect evidence)
//! lives behind this trait, so the game engine is just one implementation of it.

pub mod bevy;
pub mod engine;
pub mod mcp;
pub mod test_adapter;

pub use engine::EngineIdentity;
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
    /// so an adapter that has no battery yet still works; an engine adapter
    /// overrides it with its real, engine-specific battery.
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

    /// DR-70 ①: start the game session that lives for the **whole round**.
    ///
    /// DR-69 published the game route inside the battery's `editor_play_scene` step,
    /// i.e. *after* the Developer and *before* the Tester, so in the normal flow
    /// no role process ever overlapped the published route (the acceptance's D1,
    /// major).  The runtime now starts the round's game **before the first role**
    /// and keeps the route published for the window in which the Developer and
    /// the Tester run; the battery starts its own instance later, because it must
    /// observe the candidate the Developer just produced.
    ///
    /// The adapter that registers the endpoint is the one that publishes the
    /// route, so this is where the publish happens.  `Ok(None)` means "this
    /// adapter has no game session to offer" — the default, which is what every
    /// non-engine adapter and every test double wants.
    async fn start_round_game(
        &self,
        _workspace: &Path,
        _tools: &dyn ToolChannel,
    ) -> anyhow::Result<Option<crate::tools::endpoint::GameEndpointRecord>> {
        Ok(None)
    }

    /// DR-70 ①: stop that session and withdraw the published route.
    ///
    /// Called by the runtime on **every** exit path of a round — the summary, an
    /// `Err` from any stage, and the contract-gate returns — so no error path
    /// leaves a route pointing at a stopped game.
    async fn stop_round_game(&self, _tools: &dyn ToolChannel) -> anyhow::Result<()> {
        Ok(())
    }

    /// DR-78 ②: a **role** — not the runtime — started a game with
    /// `editor_play_scene`.  This is the publisher half of the
    /// publish/adopt boundary: the reply announced an endpoint, and the adapter
    /// that can judge readiness is the one that makes that endpoint visible to
    /// another process.
    ///
    /// `smoke-t11` measured the defect this closes: the Tester called
    /// `editor_play_scene` (pid 4784), the very next
    /// `type runs\smoke-t11\game_endpoint.json` still printed the *previous*
    /// round's pid 33536, and all three `running_game_*` CLI calls were refused
    /// with `game_endpoint_unavailable`.  Before this method the only publisher
    /// was the runtime battery's own game step, so a role's process could play a
    /// scene whose route was never written.
    ///
    /// The order is the round start's order and is not a detail: the announced
    /// endpoint is installed for in-process routing, the readiness poll runs
    /// against it, and publication happens **after** readiness — so an
    /// unconfirmed game cannot leave a route behind.  A refusal here is a hard
    /// error (the caller must exit non-zero): silently keeping the previous
    /// route is the same lie in a different place, and falling back to the
    /// editor endpoint is what DR-43 forbids.
    ///
    /// The default is `Ok(None)`: an adapter with no game endpoint to publish
    /// (every non-engine adapter and every test double).
    async fn publish_role_started_game_route(
        &self,
        _tools: &dyn ToolChannel,
        _role: Role,
        _announced: &serde_json::Value,
    ) -> anyhow::Result<Option<crate::tools::endpoint::GameEndpointRecord>> {
        Ok(None)
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

    /// DR-86 ②: the **verbatim** defects behind [`Self::developer_artifact_valid`].
    ///
    /// A wrap-up retry that can still rewrite the artifact must be told what is
    /// wrong; `smoke-t16` proved the cost of the alternative, because the retry
    /// that wrote the 20-byte scene received only "write the artifact NOW".
    /// Returning an empty list is honest when no defect was measured — the
    /// caller states that explicitly instead of inventing one.
    fn developer_artifact_defects(&self, _workspace: &Path) -> Vec<String> {
        Vec::new()
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

// ---------------------------------------------------------------------------
// DESIGN-DETAIL §1: the engine-neutral runtime capability surface
// ---------------------------------------------------------------------------
//
// [`ProjectAdapter`] above is the *build-time* boundary (what `A₀` looks like,
// what the deterministic battery is).  [`GameAdapter`] is the *runtime*
// boundary: build the artifact, start the game, observe semantic state inside
// the running process, inject level-triggered input, and answer "is this
// artifact deliverable".  It is named after capabilities rather than engines so
// nothing about Bevy appears in this module (`runtime/**` and this trait stay
// engine-agnostic).
//
// **Failure semantics (binding, DESIGN-DETAIL §1 and §7).**  Every method
// returns `Result`; **no method may panic**.  There are exactly two failure
// levels and they are not interchangeable:
//
// * **task-level failure → `Err`**: the thing the caller asked the adapter to
//   *do* did not happen (build, launch, stop, advance frames), or the
//   infrastructure that would carry the answer is missing (endpoint timeout).
//   The caller must not treat the round as observed.
// * **evidence-level failure → a reading that says why**: the adapter *did*
//   answer, and the answer is "not observed, because …"
//   ([`Reading::not_observed`], [`InjectionReport::refused`]).  This is what
//   lets the deterministic battery record a `gap` ("not observed") instead of
//   inventing proof — E6's honesty requirement is only enforceable if this
//   distinction exists.

/// The engine an adapter drives.
#[derive(Clone, Copy, Debug, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub enum EngineId {
    /// Bevy 0.19.1 (the pinned engine).
    Bevy0191,
}

impl EngineId {
    pub fn as_str(self) -> &'static str {
        match self {
            EngineId::Bevy0191 => "bevy-0.19.1",
        }
    }
}

/// The project an adapter works on: a workspace directory.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Project {
    pub workspace: PathBuf,
}

impl Project {
    pub fn at(workspace: impl Into<PathBuf>) -> Self {
        Self {
            workspace: workspace.into(),
        }
    }
}

/// The artifact [`GameAdapter::prepare`] produced.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Prepared {
    pub workspace: PathBuf,
    /// The executable to launch, when the engine produces one.
    pub artifact: Option<PathBuf>,
    /// How long the build took, in milliseconds (the build contract's budget input).
    pub build_millis: u64,
    /// Free-form, verbatim detail for the round's `build.log` line.
    pub detail: String,
}

impl Prepared {
    pub fn new(workspace: PathBuf) -> Self {
        Self {
            workspace,
            artifact: None,
            build_millis: 0,
            detail: String::new(),
        }
    }
}

/// A game process [`GameAdapter::start`] brought up and confirmed observable.
#[derive(Clone, Debug, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub struct RunningGame {
    pub pid: u32,
    /// The endpoint readiness was confirmed on (`http://127.0.0.1:15702/` for Bevy).
    pub endpoint: Option<String>,
    /// Whether the process was started in the no-window/no-GPU mode (SPIKE-2 C6).
    pub headless: bool,
}

/// What [`GameAdapter::stop`] observed while shutting the process down.
#[derive(Clone, Debug, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub struct StopReport {
    pub exit_code: Option<i32>,
    pub stderr_tail: String,
}

/// The four semantic surfaces the deterministic battery reads (DESIGN-DETAIL §2.2).
#[derive(Clone, Copy, Debug, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub enum SemanticKind {
    PlayerTransform,
    Grounded,
    CoinCounter,
    WinFlag,
}

impl SemanticKind {
    /// The battery's four reads, in the design's order.
    pub const ALL: &'static [SemanticKind] = &[
        SemanticKind::PlayerTransform,
        SemanticKind::Grounded,
        SemanticKind::CoinCounter,
        SemanticKind::WinFlag,
    ];

    /// The evidence file stem (`readings/<as_str>.json`).
    pub fn as_str(self) -> &'static str {
        match self {
            SemanticKind::PlayerTransform => "player_transform",
            SemanticKind::Grounded => "grounded",
            SemanticKind::CoinCounter => "coin_counter",
            SemanticKind::WinFlag => "win_flag",
        }
    }

    /// The semantic MCP tool that reads this surface.
    pub fn tool(self) -> &'static str {
        match self {
            SemanticKind::PlayerTransform => "bevy_player_transform",
            SemanticKind::Grounded => "bevy_grounded",
            SemanticKind::CoinCounter => "bevy_coin_counter",
            SemanticKind::WinFlag => "bevy_win_flag",
        }
    }
}

/// One semantic observation.
///
/// `failed == true` is the **evidence-level** failure from the module docs: the
/// read was attempted, and its answer is "not observed", with
/// [`Reading::reason`] saying why.  `value` is `Value::Null` in that case, so a
/// battery that ignores `failed` cannot turn a missing observation into data.
#[derive(Clone, Debug, PartialEq, serde::Serialize, serde::Deserialize)]
pub struct Reading {
    pub kind: SemanticKind,
    pub failed: bool,
    pub reason: Option<String>,
    pub value: serde_json::Value,
    pub frame: u64,
}

impl Reading {
    pub fn observed(kind: SemanticKind, frame: u64, value: serde_json::Value) -> Self {
        Self {
            kind,
            failed: false,
            reason: None,
            value,
            frame,
        }
    }

    /// The honest "the adapter answered, and the answer is: not observed".
    pub fn not_observed(kind: SemanticKind, frame: u64, reason: impl Into<String>) -> Self {
        Self {
            kind,
            failed: true,
            reason: Some(reason.into()),
            value: serde_json::Value::Null,
            frame,
        }
    }

    pub fn is_observed(&self) -> bool {
        !self.failed
    }
}

/// An injection request: the contract's `InputIntent` field and the value to
/// write into it.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Intent {
    /// `move_dir`: `-1` left, `0` stop, `1` right (level-triggered).
    Move { dir: i8 },
    /// `jump_pressed`: level-triggered, the game clears the edge itself.
    Jump { press: bool },
}

impl Intent {
    /// The `move_dir` rule of the semantic layer's schema (`-1|0|1`), enforced
    /// once, here, so no caller can write an out-of-range direction.
    pub fn move_dir(dir: i8) -> anyhow::Result<Self> {
        if !(-1..=1).contains(&dir) {
            anyhow::bail!("`dir` must be -1, 0 or 1 (got {dir})");
        }
        Ok(Intent::Move { dir })
    }

    /// The slip of the contract's intent field this intent writes.
    pub fn field(&self) -> &'static str {
        match self {
            Intent::Move { .. } => "move_dir",
            Intent::Jump { .. } => "jump_pressed",
        }
    }

    /// The JSON value written into that field.
    pub fn value(&self) -> serde_json::Value {
        match self {
            Intent::Move { dir } => serde_json::json!(dir),
            Intent::Jump { press } => serde_json::json!(press),
        }
    }

    /// The semantic tool this intent belongs to.
    pub fn tool(&self) -> &'static str {
        match self {
            Intent::Move { .. } => "bevy_inject_move",
            Intent::Jump { .. } => "bevy_inject_jump",
        }
    }
}

/// What [`GameAdapter::inject`] observed.  `accepted == false` is the
/// **evidence-level** failure: the input was not delivered, and `reason` says
/// why — the battery records "not injected" rather than assuming motion.
#[derive(Clone, Debug, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub struct InjectionReport {
    pub accepted: bool,
    pub reason: Option<String>,
    pub frame: u64,
}

impl InjectionReport {
    pub fn accepted(frame: u64) -> Self {
        Self {
            accepted: true,
            reason: None,
            frame,
        }
    }

    pub fn refused(frame: u64, reason: impl Into<String>) -> Self {
        Self {
            accepted: false,
            reason: Some(reason.into()),
            frame,
        }
    }
}

/// The frame the adapter is on after [`GameAdapter::wait_frames`].
#[derive(Clone, Copy, Debug, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub struct FrameMark {
    pub requested: u32,
    pub frame: u64,
}

/// Process liveness plus the tail of its error output (BRP has no log verb, so
/// the process side is the only place a panic can be seen).
#[derive(Clone, Debug, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub struct Health {
    pub alive: bool,
    pub stderr_tail: String,
}

/// DESIGN-DETAIL §1 names the gate verdict `GateVerdict`; the harness already
/// has exactly this type, and the design requires the *existing* gate
/// classification to be reused, so it is an alias rather than a copy.
pub type GateVerdict = crate::model::ArtifactGate;

/// Task-level adapter failures.  These are the `Err` side of the failure
/// semantics above: each variant says what class of failure it is, which is what
/// the gate needs (`EndpointTimeout` is an **infrastructure** failure and must
/// not be reported as a project defect; `ContractViolation` is a project defect,
/// because the PRD requires the surface to exist).
#[derive(Clone, Debug, PartialEq, Eq, thiserror::Error)]
pub enum AdapterError {
    /// The engine cannot do this synchronously (an editor-mediated, asynchronous
    /// engine cannot offer `prepare`/`start`/`stop` on this surface without an
    /// async bridge).
    #[error("adapter capability `{capability}` is not supported: {reason}")]
    Unsupported {
        capability: &'static str,
        reason: String,
    },
    /// The endpoint never answered inside the readiness budget (DESIGN-DETAIL §7).
    #[error("endpoint {endpoint} was not ready within {budget_millis} ms")]
    EndpointTimeout {
        endpoint: String,
        budget_millis: u64,
    },
    /// The game does not declare what the frozen contract requires (§7).
    #[error("contract violation: {0}")]
    ContractViolation(String),
    /// The build outlived its budget and was killed (DESIGN-DETAIL §7).  It is a
    /// **budget** fact, not a defect of the game, which is why it is a variant of
    /// its own and maps onto the gate's `build_budget_exceeded`.
    #[error(
        "the build exceeded its {budget_millis} ms budget and was killed after {observed_millis} ms"
    )]
    BuildBudgetExceeded {
        budget_millis: u64,
        observed_millis: u64,
    },
    /// The transport itself failed (refused, closed, timed out).
    #[error("BRP transport failure to {endpoint}: {message}")]
    Transport { endpoint: String, message: String },
    /// A JSON-RPC error, even though HTTP answered 200 (§7).
    #[error("JSON-RPC error {code}: {message}")]
    Rpc { code: i64, message: String },
    /// The body was not the JSON-RPC document the protocol promises.
    #[error("malformed BRP reply: {0}")]
    Malformed(String),
}

impl AdapterError {
    /// The honest "this engine cannot do that on this surface" answer.
    pub fn unsupported(capability: &'static str, reason: impl Into<String>) -> Self {
        AdapterError::Unsupported {
            capability,
            reason: reason.into(),
        }
    }
}

/// The engine-neutral runtime capability surface (DESIGN-DETAIL §1).
///
/// Implementors must not panic; see the module docs above for the two failure
/// levels.  `wait_frames` stays a method of its own (the design's open item ①):
/// frame advance is an *action* with its own failure class, not a settle
/// parameter of a read.
pub trait GameAdapter {
    /// Which engine this adapter drives.
    fn engine(&self) -> EngineId;

    /// Build the artifact and validate the build contract (features, lockfile,
    /// budget).  `Err` is a task-level failure: there is nothing to start.
    fn prepare(&mut self, project: &Project) -> anyhow::Result<Prepared>;

    /// Start the game and **wait until it is observable** (Bevy: poll 15702
    /// until `rpc.discover` answers, 30 s budget).  `Err` is task-level.
    fn start(&mut self, prepared: &Prepared) -> anyhow::Result<RunningGame>;

    /// Stop the game, keeping its output as evidence.  `Err` is task-level.
    fn stop(&mut self, game: RunningGame) -> anyhow::Result<StopReport>;

    /// Read one semantic surface, **one call at a time** (never a JSON-RPC
    /// batch: SPIKE-2 C4 measured that a batch is not frame-atomic).  A
    /// surface that cannot be read comes back as
    /// [`Reading::not_observed`], not as an `Err`.
    fn read(&mut self, kind: SemanticKind) -> anyhow::Result<Reading>;

    /// Inject a level-triggered intent (`level == false` means a one-shot edge
    /// the game still clears itself).  A delivery that did not happen comes
    /// back as [`InjectionReport::refused`], not as an `Err`.
    fn inject(&mut self, intent: &Intent, level: bool) -> anyhow::Result<InjectionReport>;

    /// Advance the observation point by `n` frames.  `Err` is task-level.
    fn wait_frames(&mut self, n: u32) -> anyhow::Result<FrameMark>;

    /// Is the process still alive, and what does its error output end with?
    fn health(&self) -> anyhow::Result<Health>;

    /// Judge the artifact's deliverability with the harness's existing gate
    /// classification.
    fn validate_artifact(&self, project: &Project) -> anyhow::Result<GateVerdict>;
}

#[cfg(test)]
mod game_adapter_tests {
    use super::*;
    use serde_json::json;

    /// DESIGN-DETAIL §8.3: the contract is exercised against a **fake**
    /// implementation as well as the real ones, so "nothing panics" and the two
    /// failure levels are properties of the trait, not of one engine.
    #[derive(Default)]
    struct FakeGameAdapter {
        reads: Vec<SemanticKind>,
        injections: Vec<(&'static str, serde_json::Value)>,
        started: Option<RunningGame>,
    }

    impl GameAdapter for FakeGameAdapter {
        fn engine(&self) -> EngineId {
            EngineId::Bevy0191
        }

        fn prepare(&mut self, project: &Project) -> anyhow::Result<Prepared> {
            Ok(Prepared::new(project.workspace.clone()))
        }

        fn start(&mut self, prepared: &Prepared) -> anyhow::Result<RunningGame> {
            let game = RunningGame {
                pid: 4242,
                endpoint: Some("http://127.0.0.1:15702/".to_string()),
                headless: true,
            };
            self.started = Some(game.clone());
            let _ = prepared;
            Ok(game)
        }

        fn stop(&mut self, _game: RunningGame) -> anyhow::Result<StopReport> {
            Ok(StopReport {
                exit_code: Some(0),
                stderr_tail: String::new(),
            })
        }

        fn read(&mut self, kind: SemanticKind) -> anyhow::Result<Reading> {
            self.reads.push(kind);
            Ok(Reading::not_observed(
                kind,
                0,
                "the fake adapter observes nothing",
            ))
        }

        fn inject(&mut self, intent: &Intent, _level: bool) -> anyhow::Result<InjectionReport> {
            self.injections.push((intent.field(), intent.value()));
            Ok(InjectionReport::accepted(0))
        }

        fn wait_frames(&mut self, n: u32) -> anyhow::Result<FrameMark> {
            Ok(FrameMark {
                requested: n,
                frame: u64::from(n),
            })
        }

        fn health(&self) -> anyhow::Result<Health> {
            Ok(Health {
                alive: true,
                stderr_tail: String::new(),
            })
        }

        fn validate_artifact(&self, _project: &Project) -> anyhow::Result<GateVerdict> {
            Ok(ArtifactGate {
                applicable: true,
                launchable: true,
                reasons: Vec::new(),
            })
        }
    }

    #[test]
    fn the_capability_surface_is_object_safe() {
        let boxed: Box<dyn GameAdapter> = Box::new(FakeGameAdapter::default());
        assert_eq!(boxed.engine(), EngineId::Bevy0191);
        assert_eq!(boxed.engine().as_str(), "bevy-0.19.1");
    }

    #[test]
    fn an_unobserved_read_says_why_and_never_carries_a_value() {
        let reading = Reading::not_observed(SemanticKind::CoinCounter, 7, "no such resource");
        assert!(reading.failed);
        assert!(!reading.is_observed());
        assert_eq!(reading.reason.as_deref(), Some("no such resource"));
        assert_eq!(reading.value, serde_json::Value::Null);
        assert_eq!(reading.frame, 7);

        let observed = Reading::observed(SemanticKind::CoinCounter, 7, json!({"coins": 2}));
        assert!(observed.is_observed());
        assert_eq!(observed.reason, None);
        assert_eq!(observed.value, json!({"coins": 2}));
    }

    #[test]
    fn a_refused_injection_says_why_and_is_not_accepted() {
        let refused = InjectionReport::refused(3, "no game is running");
        assert!(!refused.accepted);
        assert_eq!(refused.reason.as_deref(), Some("no game is running"));
        assert!(InjectionReport::accepted(3).accepted);
    }

    #[test]
    fn the_move_direction_is_validated_once_for_every_adapter() {
        assert_eq!(Intent::move_dir(-1).unwrap(), Intent::Move { dir: -1 });
        assert_eq!(Intent::move_dir(0).unwrap(), Intent::Move { dir: 0 });
        assert_eq!(Intent::move_dir(1).unwrap(), Intent::Move { dir: 1 });
        assert!(Intent::move_dir(2).is_err());
        assert!(Intent::move_dir(-7).is_err());
    }

    #[test]
    fn an_intent_names_the_contract_field_it_writes() {
        assert_eq!(Intent::Move { dir: 1 }.field(), "move_dir");
        assert_eq!(Intent::Move { dir: 1 }.value(), json!(1));
        assert_eq!(Intent::Jump { press: true }.field(), "jump_pressed");
        assert_eq!(Intent::Jump { press: true }.value(), json!(true));
        assert_eq!(Intent::Jump { press: true }.tool(), "bevy_inject_jump");
    }

    #[test]
    fn the_semantic_kinds_are_the_designs_four_reads() {
        assert_eq!(SemanticKind::ALL.len(), 4);
        assert_eq!(
            SemanticKind::PlayerTransform.tool(),
            "bevy_player_transform"
        );
        assert_eq!(SemanticKind::Grounded.as_str(), "grounded");
        assert_eq!(SemanticKind::CoinCounter.tool(), "bevy_coin_counter");
        assert_eq!(SemanticKind::WinFlag.as_str(), "win_flag");
    }

    #[test]
    fn a_task_level_failure_is_typed_not_a_string() {
        let error = AdapterError::unsupported("start", "the engine has no game process here");
        assert!(error.to_string().contains("not supported"));
        let timeout = AdapterError::EndpointTimeout {
            endpoint: "http://127.0.0.1:15702/".to_string(),
            budget_millis: 30_000,
        };
        assert!(timeout.to_string().contains("30000"));
    }
}
