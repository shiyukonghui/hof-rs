//! `BevyAdapter`: the engine-specific half of the capability surface
//! (DESIGN-OVERVIEW §1, DESIGN-DETAIL §1 and §5).
//!
//! It owns the four things that have to be true of a round against Bevy 0.19.1:
//!
//! 1. **A build with a budget and a cache policy** ([`build`]): `cargo build` into
//!    the shared persistent target directory, with the frozen feature set and the
//!    frozen lockfile verified *before* anything is launched, and the measured
//!    duration judged against the cold/warm bound.
//! 2. **A launch with the same binary in headless mode** ([`launch`]), waiting on
//!    **15702 only**.
//! 3. **Semantic reads and level-triggered injections** through the two-layer MCP
//!    surface, one BRP call at a time, with the frame of every reading coming
//!    from the game's own counter (D297 (b)).
//! 4. **A battery** that drives the five E3 observations and keeps every raw call
//!    as evidence ([`battery`]).
//!
//! Failure semantics are the trait's (see [`crate::adapter`]): a build or launch
//! that did not happen is a typed `Err`, while a read that could not observe
//! anything is a [`Reading`] that says so.  Nothing here panics.

pub mod battery;
pub mod brp;
pub mod build;
pub mod contract;
pub mod launch;
pub mod prd;
pub mod project;
pub mod round;
pub mod scaffold;

use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use std::time::Duration;

use serde_json::{json, Value};

use crate::adapter::bevy::battery::BatteryDriver;
use crate::adapter::bevy::brp::BrpClient;
use crate::adapter::bevy::build::{Builder, ContractPathReader, FeatureReader};
use crate::adapter::bevy::launch::LaunchConfig;
use crate::adapter::mcp::evidence::{CallEvidence, RoundHashes};
use crate::adapter::mcp::server::{BevyMcpServer, GameProcess as ServerProcess};
use crate::adapter::{
    AdapterError, EngineId, FrameMark, GameAdapter, GateVerdict, Health, InjectionReport, Intent,
    Prepared, Project, Reading, RunningGame, SemanticKind, StopReport,
};

/// Why a task-level step failed.  Every variant maps onto [`AdapterError`], so
/// the gate's classification (`infrastructure_failure` vs a project defect) is
/// decided by the trait's error type, not here.
#[derive(Clone, Debug, PartialEq, Eq, thiserror::Error)]
pub enum AdapterStepError {
    #[error("the build contract was violated: {0}")]
    Contract(String),
    #[error("the build did not run: {0}")]
    Build(String),
    #[error("the game could not be started: {0}")]
    Launch(String),
    #[error("no game process is running, so there is nothing to {action}")]
    NoGame { action: &'static str },
    #[error("the round evidence could not be written: {0}")]
    Evidence(String),
}

impl From<AdapterStepError> for AdapterError {
    fn from(error: AdapterStepError) -> Self {
        match error {
            AdapterStepError::Contract(message) => AdapterError::ContractViolation(message),
            AdapterStepError::Build(message) => AdapterError::Transport {
                endpoint: brp::endpoint(),
                message: format!("the build did not run: {message}"),
            },
            AdapterStepError::Launch(message) => AdapterError::Transport {
                endpoint: brp::endpoint(),
                message: message.clone(),
            },
            AdapterStepError::NoGame { action } => AdapterError::Transport {
                endpoint: brp::endpoint(),
                message: format!("no game process is running, so there is nothing to {action}"),
            },
            AdapterStepError::Evidence(message) => AdapterError::Malformed(message),
        }
    }
}

/// The adapter's configuration.  Everything the adapter can be told is here, so
/// a test can shrink a budget without patching a constant and a round can record
/// exactly what it used.
#[derive(Clone, Debug)]
pub struct BevyAdapterConfig {
    pub build_policy: build::BuildPolicy,
    pub launch: LaunchConfig,
    /// The round name the evidence directory uses.
    pub round: String,
    /// `true` to write `runs/bevy-<round>/` when a battery finishes.  The default
    /// is `false`: a round that did not ask for evidence does not write any.
    pub write_evidence: bool,
    /// DESIGN-DETAIL §6: the directory `runs/bevy-<round>/` is created under.
    /// `.` means the working directory, which for a round is the repository root.
    pub evidence_root: std::path::PathBuf,
}

impl Default for BevyAdapterConfig {
    fn default() -> Self {
        Self {
            build_policy: build::BuildPolicy::default(),
            launch: LaunchConfig::default(),
            round: "bevy-b2".to_string(),
            write_evidence: false,
            evidence_root: PathBuf::from("."),
        }
    }
}

/// The Bevy 0.19.1 adapter.
pub struct BevyAdapter {
    workspace: PathBuf,
    endpoint: String,
    headless: bool,
    build_policy: build::BuildPolicy,
    launch: LaunchConfig,
    round: String,
    write_evidence: bool,
    /// The build contract check's injectable feature reader.  An `Arc` rather
    /// than a `Box` so a round can hand the same reader to the second adapter
    /// [`BevyAdapter::round_peer`] builds (a real round builds, launches and
    /// observes through a peer, so that the caller's own process state — and the
    /// fake a test injected — is neither disturbed nor lost).
    features: Arc<dyn FeatureReader>,
    /// The contract check's injectable type-path reader.  It is a separate seam
    /// from `features` on purpose (B2-1): a feature set and a type path are two
    /// different claims with two different sources and two different reasons.
    contract_reader: Arc<dyn ContractPathReader>,
    /// The injected builder (a test supplies a fake one; a round supplies none
    /// and gets [`build::CargoBuilder`]).
    builder: Option<build::DynBuilder>,
    client: BrpClient,
    server: BevyMcpServer,
    process: Option<launch::GameProcess>,
    stderr: Arc<Mutex<String>>,
    game_frame: Option<u64>,
    prepared: Option<Prepared>,
    evidence: Vec<CallEvidence>,
    build_millis: u64,
    budget_millis: Option<u64>,
    last_build_output: String,
    last_contract_paths: Vec<String>,
    last_stop: Option<crate::adapter::StopReport>,
    /// DESIGN-DETAIL §6: where this adapter writes `runs/bevy-<round>/`.
    evidence_root: PathBuf,
    /// DR-70 ①: the game process that lives for the **whole round window**,
    /// started by [`crate::adapter::ProjectAdapter::start_round_game`] before the
    /// first role and stopped by `stop_round_game` on every exit path.  It is
    /// kept behind a `Mutex` because both of those take `&self` (the runtime
    /// holds the adapter behind a shared reference for the whole round) while
    /// owning a `Child` is inherently exclusive.
    round_game: Mutex<Option<launch::GameProcess>>,
}

impl std::fmt::Debug for BevyAdapter {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("BevyAdapter")
            .field("workspace", &self.workspace)
            .field("endpoint", &self.endpoint)
            .field("headless", &self.headless)
            .field("round", &self.round)
            .field("pid", &self.process.as_ref().map(|process| process.pid()))
            .field("game_frame", &self.game_frame)
            .finish()
    }
}

impl BevyAdapter {
    /// An adapter for `workspace`, with the frozen policies and the real builder.
    pub fn at(workspace: impl Into<PathBuf>) -> Self {
        let config = BevyAdapterConfig::default();
        let endpoint = config.launch.endpoint();
        let client = BrpClient::new(&endpoint, Duration::from_secs(5));
        let workspace = workspace.into();
        // The lockfile the round compares against is the one the adapter was
        // constructed with (B2-1): the default policy is explicitly unpinned, not
        // an empty string, so pinning here is what makes the real path coherent.
        let build_policy =
            build::BuildPolicy::pinned_if_available(&workspace, config.build_policy.target_dir);
        Self {
            workspace,
            endpoint,
            headless: config.launch.headless,
            build_policy,
            launch: config.launch,
            round: config.round,
            write_evidence: config.write_evidence,
            evidence_root: config.evidence_root,
            features: Arc::new(build::CargoMetadataFeatures::new()),
            contract_reader: Arc::new(build::SourceContractPaths),
            builder: None,
            server: BevyMcpServer::new(client.clone()),
            client,
            process: None,
            stderr: Arc::new(Mutex::new(String::new())),
            game_frame: None,
            prepared: None,
            evidence: Vec::new(),
            build_millis: 0,
            budget_millis: None,
            last_build_output: String::new(),
            last_contract_paths: Vec::new(),
            last_stop: None,
            round_game: Mutex::new(None),
        }
    }

    /// Apply a whole configuration.
    pub fn with_config(mut self, config: BevyAdapterConfig) -> Self {
        self.endpoint = config.launch.endpoint();
        self.headless = config.launch.headless;
        self.build_policy = config.build_policy;
        self.launch = config.launch;
        self.round = config.round;
        self.write_evidence = config.write_evidence;
        self.evidence_root = config.evidence_root;
        self.client = BrpClient::new(
            &self.endpoint,
            self.launch.probe_timeout.max(Duration::from_millis(50)),
        );
        self.server = BevyMcpServer::new(self.client.clone());
        self
    }

    /// Point the adapter at another endpoint.
    ///
    /// The **only** reason this exists is a test with an in-process fake: a round
    /// must address 15702 (SPIKE-2 §0.4), and [`BevyAdapterConfig`] cannot name
    /// another port.  [`BevyAdapter::is_pinned_endpoint`] lets a report prove
    /// which endpoint was used.
    pub fn with_endpoint(mut self, endpoint: impl Into<String>) -> Self {
        self.endpoint = endpoint.into();
        self.client = BrpClient::new(&self.endpoint, Duration::from_secs(5));
        self.server = BevyMcpServer::new(self.client.clone());
        self
    }

    /// Is this adapter addressing the pinned main-world endpoint?
    pub fn is_pinned_endpoint(&self) -> bool {
        self.endpoint == brp::endpoint()
    }

    pub fn with_features(mut self, features: Box<dyn FeatureReader>) -> Self {
        self.features = Arc::from(features);
        self
    }

    /// Inject the contract-path reader (a test uses a fake; a round uses the
    /// game's own source).
    pub fn with_contract_paths(mut self, reader: Box<dyn ContractPathReader>) -> Self {
        self.contract_reader = Arc::from(reader);
        self
    }

    pub fn with_builder(mut self, builder: build::DynBuilder) -> Self {
        self.builder = Some(builder);
        self
    }

    pub fn with_round(mut self, round: impl Into<String>) -> Self {
        self.round = round.into();
        self
    }

    pub fn with_evidence_writing(mut self, write: bool) -> Self {
        self.write_evidence = write;
        self
    }

    /// DESIGN-DETAIL §6: where `runs/bevy-<round>/` is written.
    pub fn with_evidence_root(mut self, root: impl Into<PathBuf>) -> Self {
        self.evidence_root = root.into();
        self
    }

    /// The round name this adapter's evidence directory carries.
    pub fn round_name(&self) -> String {
        self.round.clone()
    }

    /// The root `runs/bevy-<round>/` is created under.
    pub fn evidence_root(&self) -> PathBuf {
        self.evidence_root.clone()
    }

    /// Whether this adapter was asked to write its round evidence.
    pub fn writes_evidence(&self) -> bool {
        self.write_evidence
    }

    /// The identity of the binary a round launches: path, size and digest.
    ///
    /// It is recorded in `launch.json` because "which artifact produced these
    /// observations?" is the same question `meta.json.engine` answers for an
    /// adapter that drives a separate engine binary — and Bevy has none, so the
    /// game binary *is* the engine.  A stale artifact in a shared target
    /// directory is exactly the failure this makes visible.
    pub fn built_binary_identity(&self) -> Value {
        let Some(target) = self.build_policy.target_dir.clone() else {
            return json!({"reason": "the build policy names no target directory"});
        };
        let name = if cfg!(windows) {
            format!("{}.exe", crate::adapter::bevy::contract::GAME_CRATE)
        } else {
            crate::adapter::bevy::contract::GAME_CRATE.to_string()
        };
        let path = target.join("debug").join(name);
        match std::fs::read(&path) {
            Ok(bytes) => json!({
                "path": path.display().to_string(),
                "size_bytes": bytes.len(),
                "sha256": crate::runtime::policy::sha256_hex(&bytes),
            }),
            Err(error) => json!({
                "path": path.display().to_string(),
                "reason": format!("the built binary could not be read: {error}"),
            }),
        }
    }

    /// Take the process the round-game window owns, so a caller can stop it.
    pub fn take_process(&mut self) -> Option<launch::GameProcess> {
        self.round_game.lock().ok().and_then(|mut game| game.take())
    }

    /// A second adapter over the **same configuration**: same build policy, same
    /// launch configuration, same evidence settings and the same injected seams
    /// (the feature reader, the contract-path reader and the builder are `Arc`s).
    ///
    /// A round builds, launches and observes through a peer so that the adapter
    /// the runtime holds keeps its own process state free: the round's game and
    /// the caller's game are two different processes, and conflating them is how
    /// a dead pid reaches a published route.
    pub fn round_peer(&self) -> Self {
        Self {
            workspace: self.workspace.clone(),
            endpoint: self.endpoint.clone(),
            headless: self.headless,
            build_policy: self.build_policy.clone(),
            launch: self.launch.clone(),
            round: self.round.clone(),
            write_evidence: self.write_evidence,
            evidence_root: self.evidence_root.clone(),
            features: Arc::clone(&self.features),
            contract_reader: Arc::clone(&self.contract_reader),
            builder: self.builder.clone(),
            client: self.client.clone(),
            server: BevyMcpServer::new(self.client.clone()),
            process: None,
            stderr: Arc::new(Mutex::new(String::new())),
            game_frame: None,
            prepared: None,
            evidence: Vec::new(),
            build_millis: 0,
            budget_millis: None,
            last_build_output: String::new(),
            last_contract_paths: Vec::new(),
            last_stop: None,
            round_game: Mutex::new(None),
        }
    }

    /// Use the adapter's own BRP client (the default).  Present so a round can
    /// hand in a client whose timeouts differ from the probe's.
    pub fn with_client(mut self, client: BrpClient) -> Self {
        self.endpoint = client.endpoint().to_string();
        self.client = client.clone();
        self.server = BevyMcpServer::new(client);
        self
    }

    pub fn endpoint(&self) -> &str {
        &self.endpoint
    }

    /// The launch configuration this adapter would use, including the endpoint
    /// hand-off.
    ///
    /// When the adapter is not on the pinned endpoint, both the game's
    /// environment and the **readiness probe** are pointed at the adapter's
    /// endpoint: the probe and the adapter must agree, or a test against a fake
    /// endpoint waits 30 s on the wrong port (B2-6).
    pub fn launch_config(&self) -> LaunchConfig {
        let mut config = self.launch.clone();
        config.headless = self.headless;
        if !self.is_pinned_endpoint() {
            config.endpoint_override = Some(self.endpoint.clone());
            config.env.push((
                "HOF_BRP_ENDPOINT_OVERRIDE".to_string(),
                self.endpoint.clone(),
            ));
        }
        config
    }

    pub fn workspace(&self) -> &Path {
        &self.workspace
    }

    pub fn server(&self) -> &BevyMcpServer {
        &self.server
    }

    pub fn process(&self) -> Option<&launch::GameProcess> {
        self.process.as_ref()
    }

    /// The last game frame observed through the contract's counter, or `None`.
    pub fn game_frame(&self) -> Option<u64> {
        self.game_frame
    }

    /// The build's measured duration, in milliseconds.
    pub fn build_millis(&self) -> u64 {
        self.build_millis
    }

    /// The bound the build exceeded, when it exceeded one.
    pub fn budget_millis(&self) -> Option<u64> {
        self.budget_millis
    }

    /// Whether this round compares the lockfile it measured against a pin.
    pub fn is_lockfile_pinned(&self) -> bool {
        self.build_policy.is_locked()
    }

    /// The build contract's per-round values, as the evidence records them.
    pub fn round_hashes(&self) -> Result<RoundHashes, AdapterError> {
        RoundHashes::measure(&self.workspace.join("Cargo.lock"))
    }

    /// The evidence records made since the last call to
    /// [`BevyAdapter::take_evidence`].
    pub fn take_evidence(&mut self) -> Vec<CallEvidence> {
        std::mem::take(&mut self.evidence)
    }

    /// The last build's output (verbatim, for `build.log`).
    pub fn build_log(&self) -> &str {
        &self.last_build_output
    }

    /// The contract type paths the game declared, as the last `prepare` read
    /// them from the game's own source.
    pub fn contract_paths(&self) -> &[String] {
        &self.last_contract_paths
    }

    /// The last stop's observation, when the game has been stopped.
    pub fn last_stop(&self) -> Option<&crate::adapter::StopReport> {
        self.last_stop.as_ref()
    }

    /// One semantic read, recorded as evidence.
    ///
    /// The recording itself lives in [`super::round`] so a round's battery and
    /// this method cannot drift apart in what they send or what they keep.
    pub fn read_recorded(&mut self, tool: &str, args: Value) -> anyhow::Result<Reading> {
        let kind = match tool {
            "bevy_player_transform" => SemanticKind::PlayerTransform,
            "bevy_grounded" => SemanticKind::Grounded,
            "bevy_coin_counter" => SemanticKind::CoinCounter,
            "bevy_win_flag" => SemanticKind::WinFlag,
            other => {
                anyhow::bail!("`{other}` is not a read surface");
            }
        };
        let _ = args;
        crate::adapter::bevy::round::read_recorded(
            &mut self.server,
            &mut self.evidence,
            &mut self.game_frame,
            kind,
        )
    }

    /// One injection, recorded as evidence.
    pub fn inject_recorded(
        &mut self,
        intent: &Intent,
        level: bool,
    ) -> anyhow::Result<InjectionReport> {
        crate::adapter::bevy::round::inject_recorded(
            &mut self.server,
            &mut self.evidence,
            &mut self.game_frame,
            intent,
            level,
        )
    }

    /// Wait for `n` frames of the game, recorded as evidence.
    pub fn wait_frames_recorded(&mut self, n: u32) -> anyhow::Result<FrameMark> {
        crate::adapter::bevy::round::wait_frames_recorded(
            &mut self.server,
            &mut self.evidence,
            &mut self.game_frame,
            n,
        )
    }

    /// The five E3 observations, driven through the semantic tools.
    pub fn run_battery(&mut self) -> anyhow::Result<battery::E3Observations> {
        let observations = battery::BatteryRun::new(self).run()?;
        Ok(observations)
    }
}

impl BatteryDriver for BevyAdapter {
    fn read(&mut self, kind: SemanticKind) -> anyhow::Result<Reading> {
        self.read_recorded(kind.tool(), json!({}))
    }

    fn inject(&mut self, intent: &Intent, level: bool) -> anyhow::Result<InjectionReport> {
        self.inject_recorded(intent, level)
    }

    fn wait_frames(&mut self, n: u32) -> anyhow::Result<FrameMark> {
        self.wait_frames_recorded(n)
    }

    fn take_evidence(&mut self) -> Vec<CallEvidence> {
        BevyAdapter::take_evidence(self)
    }
}

/// The `GameAdapter` implementation.  See the module docs for the failure levels.
impl GameAdapter for BevyAdapter {
    fn engine(&self) -> EngineId {
        EngineId::Bevy0191
    }

    fn prepare(&mut self, project: &Project) -> anyhow::Result<Prepared> {
        let workspace = project.workspace.clone();
        // The contract is checked before the build, not after: a workspace that
        // cannot satisfy it is a project defect, and no build would fix that.
        let manifest = workspace.join("Cargo.toml");
        let text = std::fs::read_to_string(&manifest).map_err(|error| {
            AdapterStepError::Contract(format!(
                "`{}` could not be read: {error}",
                manifest.display()
            ))
        })?;
        crate::adapter::bevy::contract::check_game_crate_name(&text)?;

        let lockfile = workspace.join("Cargo.lock");
        let hashes = RoundHashes::measure(&lockfile)?;
        match &self.build_policy.lock_sha256 {
            // A pin is a real pin: the reason names both values it compared.
            Some(expected) if *expected != hashes.lock_sha256 => {
                return Err(AdapterStepError::Contract(format!(
                    "compared this round's lockfile hash {actual} against the hash this round is \
                     pinned to ({expected}): a lockfile that moves inside a round makes the round \
                     incomparable with its predecessors",
                    actual = hashes.lock_sha256,
                ))
                .into());
            }
            Some(_) => {}
            // No comparison was requested (B2-1).  Saying so is honest; inventing
            // a comparison against the empty string is not.
            None => {
                self.last_build_output.push_str(
                    "this round is not pinned to a lockfile: the measured lockfile was \
                     recorded in `meta.json`, but no cross-round comparison was requested\n",
                );
            }
        }

        let request = build::BuildRequest {
            manifest: manifest.clone(),
            workspace: workspace.clone(),
            target_dir: self.build_policy.target_dir.clone(),
            timeout: Duration::from_millis(self.build_policy.budget.cold_millis),
        };
        let run = |request: &build::BuildRequest| match &self.builder {
            Some(builder) => builder.build(request),
            None => build::CargoBuilder::new().build(request),
        };
        if self.build_policy.warmup {
            // Round 0 (DESIGN-DETAIL §5): compile the graph first, and keep its
            // duration out of the artifact's build time.
            let warm = run(&request)?;
            self.last_build_output = format!("warm-up: {}\n", warm.log_line());
        }
        // A typed build failure (`BuildBudgetExceeded`, a spawn failure) is
        // propagated as itself rather than re-wrapped, so the gate can classify
        // it (DESIGN-DETAIL §7).
        let outcome = run(&request)?;
        self.build_millis = outcome.elapsed_millis;
        self.last_build_output.push_str(&outcome.log_line());

        // The frozen feature set, measured from the **resolved** dependency graph
        // (B2-4).  This check is about the feature set and nothing else, so its
        // reason is about features.
        let features = self
            .features
            .resolved_features(&workspace, crate::adapter::bevy::contract::GAME_CRATE)?;
        if features.feature_sha256 != build::FEATURE_SET_SHA256 {
            return Err(AdapterStepError::Contract(format!(
                "compared the resolved Bevy feature set {features:?} (hashed {measured}) against \
                 the frozen feature set (pinned {frozen}): a feature-set change is what turns a \
                 warm ~12 s build into ~236 s (DESIGN-DETAIL §5)",
                features = features.features,
                measured = features.feature_sha256,
                frozen = build::FEATURE_SET_SHA256,
            ))
            .into());
        }

        // The contract's **type paths** are a separate concern with a separate
        // source and a separate reason (B2-1).  The reader reads what the game
        // declared; the check names the specific path that is missing and says
        // what it compared.
        let declared = self
            .contract_reader
            .declared_contract_paths(&workspace, crate::adapter::bevy::contract::GAME_CRATE)?;
        crate::adapter::bevy::contract::check_declared_contract_paths(
            &declared,
            &format!(
                "the game source under `{}`",
                workspace.join("src").display()
            ),
        )?;
        self.last_contract_paths = declared;

        self.budget_millis = self
            .build_policy
            .budget
            .exceeded(outcome.elapsed_millis, outcome.cache_hit);
        if let Some(bound) = self.budget_millis {
            // The overrun is recorded, not discarded: a gate needs to know the
            // round went over its bound even when the build itself succeeded.
            self.last_build_output.push_str(&format!(
                "\nthe build used {} ms, over the {} ms bound",
                outcome.elapsed_millis, bound
            ));
        }

        let prepared = Prepared {
            workspace: workspace.clone(),
            artifact: Some(outcome.binary.clone()),
            build_millis: outcome.elapsed_millis,
            detail: self.last_build_output.clone(),
        };
        self.prepared = Some(prepared.clone());
        Ok(prepared)
    }

    fn start(&mut self, prepared: &Prepared) -> anyhow::Result<RunningGame> {
        let binary = prepared
            .artifact
            .clone()
            .ok_or_else(|| AdapterStepError::Build("the build produced no binary".to_string()))?;
        self.stderr = Arc::new(Mutex::new(String::new()));
        let launch_config = self.launch_config();
        let process = crate::adapter::bevy::launch::start_game(
            &binary,
            &launch_config,
            Arc::clone(&self.stderr),
        )
        .map_err(|error| AdapterStepError::Launch(error.to_string()))?;
        let pid = process.pid();
        let headless = process.headless();
        self.server.install_process(ServerProcess {
            pid,
            stderr_tail: process.stderr_tail(),
        });
        self.process = Some(process);
        Ok(RunningGame {
            pid,
            endpoint: Some(self.endpoint.clone()),
            headless,
        })
    }

    fn stop(&mut self, _game: RunningGame) -> anyhow::Result<StopReport> {
        let Some(process) = self.process.take() else {
            return Err(AdapterStepError::NoGame { action: "stop" }.into());
        };
        let evidence = process
            .stop()
            .map_err(|message| AdapterStepError::Build(message))?;
        self.server.clear_process();
        let report = StopReport {
            exit_code: evidence.exit_code,
            stderr_tail: evidence.stderr_tail,
        };
        self.last_stop = Some(report.clone());
        Ok(report)
    }

    fn read(&mut self, kind: SemanticKind) -> anyhow::Result<Reading> {
        self.read_recorded(kind.tool(), json!({}))
    }

    fn inject(&mut self, intent: &Intent, level: bool) -> anyhow::Result<InjectionReport> {
        self.inject_recorded(intent, level)
    }

    fn wait_frames(&mut self, n: u32) -> anyhow::Result<FrameMark> {
        self.wait_frames_recorded(n)
    }

    fn health(&self) -> anyhow::Result<Health> {
        let Some(process) = self.process.as_ref() else {
            return Err(AdapterError::unsupported(
                "health",
                "no game process is running: an unknown process is never reported as alive",
            )
            .into());
        };
        // A process the launcher owns: `is_running` is the honest liveness check,
        // and the stderr tail is the only place a Bevy panic is visible.
        Ok(Health {
            alive: process.is_running(),
            stderr_tail: process.stderr_tail(),
        })
    }

    fn validate_artifact(&self, project: &Project) -> anyhow::Result<GateVerdict> {
        let mut probe = BevyAdapter::at(project.workspace.clone())
            .with_features(Box::new(StaticFeatures::frozen()));
        let verdict = match probe.prepare(project) {
            Ok(prepared) => {
                let over_budget = probe.budget_millis.is_some();
                GateVerdict {
                    applicable: true,
                    launchable: !over_budget,
                    reasons: if over_budget {
                        vec![prepared.detail.clone()]
                    } else {
                        Vec::new()
                    },
                }
            }
            Err(error) => GateVerdict {
                applicable: true,
                launchable: false,
                reasons: vec![error.to_string()],
            },
        };
        Ok(verdict)
    }
}

/// A feature reader that reports the frozen feature set, for callers that do not
/// want to pay for `cargo metadata` (a real round uses
/// [`build::CargoMetadataFeatures`], which reads the workspace's resolved graph).
///
/// It says nothing about the contract's type paths: since B2-1 those are read by
/// [`build::SourceContractPaths`] from the game's own source.
#[derive(Clone, Debug, Default)]
pub struct StaticFeatures;

impl StaticFeatures {
    pub fn frozen() -> Self {
        Self
    }
}

impl FeatureReader for StaticFeatures {
    fn resolved_features(
        &self,
        _workspace: &Path,
        _crate_name: &str,
    ) -> Result<build::ResolvedFeatures, AdapterError> {
        Ok(build::ResolvedFeatures {
            feature_sha256: build::FEATURE_SET_SHA256.to_string(),
            features: build::frozen_feature_list(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::adapter::bevy::brp::fake::{FakeBrp, Reply};
    use crate::adapter::bevy::build::{
        CargoMetadataFeatures, FakeBuilder, FakeContractPaths, FakeFeatures,
    };
    use std::sync::atomic::{AtomicU64, Ordering};

    /// A driver that behaves like the game `PRD.md` describes: the player stands
    /// on the ground, moves when the intent says so, collects one coin when it
    /// has walked, wins after that, and jumps when the jump intent is held.
    ///
    /// It is a real driver over the real semantic layer: every value it reports
    /// comes back through `BevyMcpServer` and a fake BRP socket, so the battery
    /// is exercised end to end without an engine.
    #[derive(Default)]
    struct ScriptedGame;

    impl BatteryDriver for ScriptedGame {
        fn read(&mut self, kind: SemanticKind) -> anyhow::Result<Reading> {
            let _ = kind;
            anyhow::bail!("the scripted game is driven through the adapter")
        }

        fn inject(&mut self, _intent: &Intent, _level: bool) -> anyhow::Result<InjectionReport> {
            anyhow::bail!("the scripted game is driven through the adapter")
        }

        fn wait_frames(&mut self, _n: u32) -> anyhow::Result<FrameMark> {
            anyhow::bail!("the scripted game is driven through the adapter")
        }

        fn take_evidence(&mut self) -> Vec<CallEvidence> {
            Vec::new()
        }
    }

    /// The whole adapter, over an in-process fake BRP endpoint.  The frame
    /// counter advances one per read, exactly like a game's own clock, so the
    /// battery's `frame` values are the *game's* and not an ordinal (D297 (b)).
    struct GameState {
        /// The shared game clock: the counter the wire reports **is** the frame
        /// the game simulated, so an arc sample and a frame number cannot
        /// disagree.
        clock: Arc<AtomicU64>,
        intent: serde_json::Value,
        grounded_reads: u64,
        x: f64,
        y: f64,
        coins: i64,
        won: bool,
        jumped: bool,
        jump_age: u64,
        /// The "monotone fall" game: it can only ever descend.  It exists so the
        /// criterion that was red in the Godot era stays red, and so the case is
        /// covered in the default gate rather than only on a real engine.
        never_rise: bool,
    }

    impl GameState {
        fn new() -> Self {
            Self {
                intent: serde_json::json!({"move_dir": 0, "jump_pressed": false}),
                grounded_reads: 0,
                x: 0.0,
                y: -200.0,
                clock: Arc::new(AtomicU64::new(1)),
                coins: 0,
                won: false,
                jumped: false,
                jump_age: 0,
                never_rise: false,
            }
        }

        /// Simulate exactly one game frame and advance the clock with it.  One
        /// frame per game call is what makes the jump arc visible: a real game at
        /// 60 FPS shows the rise across several reads, and a double that jumped
        /// eight frames per call would show only the descent.
        fn tick(&mut self) {
            self.clock.fetch_add(1, Ordering::SeqCst);
            self.advance();
        }

        /// One game frame.  This is the game's own state machine; the wire only
        /// carries it.
        fn advance(&mut self) {
            // The intent is level-triggered and the game clears the edge itself
            // (PRD C3).
            let dir = self.intent["move_dir"].as_i64().unwrap_or(0);
            let jump = self.intent["jump_pressed"].as_bool().unwrap_or(false);
            if jump && !self.jumped {
                self.jumped = true;
                self.jump_age = 0;
            }
            if self.never_rise {
                // A fall with no rise: no value of `y` here is ever greater than
                // the one before it.
                self.y -= 30.0;
            } else if self.jumped {
                self.jump_age += 1;
                // A real arc: up for five frames, down for as long again.
                if self.jump_age <= 5 {
                    self.y += 30.0;
                } else if self.jump_age <= 16 {
                    self.y -= 30.0;
                } else {
                    self.y = -200.0;
                    self.jumped = false;
                }
            }
            if dir != 0 {
                self.x += 8.0 * dir as f64;
                if dir > 0 && self.x > 30.0 && self.coins == 0 {
                    self.coins = 1;
                }
                if dir > 0 && self.coins >= 1 && self.x > 70.0 {
                    self.won = true;
                }
            }
            let _ = self.grounded_reads;
        }
    }

    /// The game's answer to one request.  A function, not a closure, so the fake
    /// server's `'static` reply closure can call it with its own share of the
    /// state.
    fn answer_from(
        state: &Arc<std::sync::Mutex<GameState>>,
        request: &serde_json::Value,
        _prior: &[serde_json::Value],
    ) -> serde_json::Value {
        let mut state = state.lock().expect("the game state");
        // A running game advances while it is being read, so every call (except
        // the frame counter, which is answered before this point) is one frame of
        // its life.
        state.tick();
        let method = request["method"].as_str().unwrap_or_default();
        match method {
            "world.get_resources" => match request["params"]["resource"]
                .as_str()
                .unwrap_or_default()
            {
                "hof_game::contract::FrameCounter" => {
                    serde_json::json!({"value": {"frames": state.clock.load(Ordering::SeqCst)}})
                }
                "hof_game::contract::CoinCounter" => {
                    serde_json::json!({"value": {"coins": state.coins, "target": 1}})
                }
                "hof_game::contract::WinFlag" => serde_json::json!({"value": {"won": state.won}}),
                _ => serde_json::json!({"value": {}}),
            },
            "world.mutate_resources" => {
                // The write lands in the game's intent and the game consumes it
                // on its next frames; the reply is `null`, as BRP's is.
                let path = request["params"]["path"]
                    .as_str()
                    .unwrap_or_default()
                    .to_string();
                if let Some(field) = state.intent.get_mut(&path) {
                    *field = request["params"]["value"].clone();
                }
                serde_json::Value::Null
            }
            "world.query" => {
                state.grounded_reads += 1;
                // Grounded alternates only because the jump said so.
                let grounded = !state.jumped;
                serde_json::json!([{
                    "entity": 7u64,
                    "components": {
                        "bevy_transform::components::transform::Transform": {
                            "translation": [state.x, state.y, 0.0],
                            "rotation": [0.0, 0.0, 0.0, 1.0],
                            "scale": [1.0, 1.0, 1.0],
                        },
                        "hof_game::contract::Grounded": {"on_ground": grounded},
                    },
                }])
            }
            _ => serde_json::Value::Null,
        }
    }

    /// One request, answered from the game's state.  Both doubles below share
    /// it, so the "all five hold" game and the "monotone fall" game cannot drift
    /// apart in how they speak BRP.
    fn handle_request(
        state: &Arc<std::sync::Mutex<GameState>>,
        request: &serde_json::Value,
        prior: &[std::string::String],
    ) -> (u16, String) {
        let id = request
            .get("id")
            .cloned()
            .unwrap_or(serde_json::Value::Null);
        if request["method"] == serde_json::json!("world.get_resources")
            && request["params"]["resource"]
                == serde_json::json!("hof_game::contract::FrameCounter")
        {
            // A real game's counter moves with time, so the reader must be able
            // to wait for it to move: each read advances the game's *scheduled*
            // frame by one and reports it.  The game itself catches up to that
            // frame before it answers anything.
            let clock = {
                let game = state.lock().expect("the game state");
                Arc::clone(&game.clock)
            };
            let frames = clock.fetch_add(1, Ordering::SeqCst) + 1;
            return (
                200,
                serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {"value": {"frames": frames}},
                })
                .to_string(),
            );
        }
        let prior: Vec<serde_json::Value> = prior
            .iter()
            .filter_map(|body| serde_json::from_str(body).ok())
            .collect();
        let result = answer_from(state, request, &prior);
        (
            200,
            serde_json::json!({"jsonrpc": "2.0", "id": id, "result": result}).to_string(),
        )
    }

    /// A fake BRP server whose every answer comes from [`handle_request`], so
    /// both the "all five hold" game and the "monotone fall" game speak the same
    /// protocol.
    fn game_server(state: &Arc<std::sync::Mutex<GameState>>) -> (FakeBrp, BevyMcpServer) {
        let game = Arc::clone(state);
        let reply = Reply::From(Arc::new(move |request: &str, prior: &[String]| {
            let parsed: serde_json::Value =
                serde_json::from_str(request).expect("a JSON request body");
            let (_status, body) = handle_request(&game, &parsed, prior);
            Reply::Raw200(body)
        }));
        let fake = FakeBrp::spawn(vec![reply]);
        let client = BrpClient::new(fake.endpoint(), Duration::from_millis(2_000));
        (fake, BevyMcpServer::new(client))
    }

    /// The E3 battery, end to end over the fake socket: all nine observations
    /// hold, every one of them keeps its raw calls, and no call is a batch.
    #[test]
    fn the_battery_observes_every_e3_behaviour_in_order() {
        let state = Arc::new(std::sync::Mutex::new(GameState::new()));
        let (fake, server) = game_server(&state);
        // Configure first, then install the fake client: the configuration
        // rebuilds the client and the server, so the order matters.
        let mut adapter = BevyAdapter::at(".")
            .with_config(BevyAdapterConfig::default())
            .with_client(BrpClient::new(
                fake.endpoint(),
                Duration::from_millis(2_000),
            ));
        // The adapter owns its own server; point it at the same fake.
        adapter.server = server;
        let observations = adapter.run_battery().expect("the battery runs");
        assert!(observations.aborted.is_none(), "{:?}", observations.aborted);
        assert!(
            observations.passed(),
            "not every criterion held: {} | coins={:?} win={:?} jump={:?} left={:?} release={:?} \
             win_position={:?} payload={:?}",
            observations.summary_line(),
            observations.coins.failure,
            observations.win.failure,
            observations.jump.failure,
            observations.movement_left.failure,
            observations.movement_release.failure,
            observations.win_position.failure,
            observations.grounded_payload.failure
        );
        // ④ really is an arc with both directions, from the game's frames.
        let arc = observations.jump.arc.as_ref().expect("the jump arc");
        assert!(arc.rising > 0, "rise={}", arc.rising);
        assert!(arc.falling > 0, "fall={}", arc.falling);
        assert!(
            arc.peak > arc.first,
            "peak={} first={}",
            arc.peak,
            arc.first
        );
        // ⑤ has a readable ground state before take-off.
        assert!(!observations.grounded.readings.is_empty());
        // P1-left: the negative direction really moved the player backwards, and
        // the evidence says so with the two readings.
        let left = &observations.movement_left;
        let xs: Vec<f64> = left
            .readings
            .iter()
            .filter_map(|reading| reading.value.get("x").and_then(serde_json::Value::as_f64))
            .collect();
        assert_eq!(xs.len(), 2, "the leftward check keeps both readings");
        assert!(xs[1] < xs[0], "move_dir = -1 must move x down: {xs:?}");
        // P1-release: the two readings of the release window are the same x.
        let release_xs: Vec<f64> = observations
            .movement_release
            .readings
            .iter()
            .filter_map(|reading| reading.value.get("x").and_then(serde_json::Value::as_f64))
            .collect();
        assert_eq!(release_xs.len(), 2);
        assert_eq!(release_xs[0], release_xs[1], "writing 0 must stop it");
        // P3-position: the transform sample is at or after the win frame.
        let win_position = &observations.win_position;
        assert_eq!(win_position.readings.len(), 2, "the flag and the position");
        assert!(
            win_position.readings[1].frame >= win_position.readings[0].frame,
            "the position sample must not predate the win frame: {:?}",
            win_position.readings
        );
        // P5-gate: the payload stands on its own.
        let payload = &observations.grounded_payload;
        assert_eq!(payload.readings.len(), 1);
        assert!(
            payload.readings[0]
                .value
                .get("grounded")
                .map(serde_json::Value::is_boolean)
                .unwrap_or(false),
            "the stand-alone payload must carry a boolean: {:?}",
            payload.readings[0].value
        );
        // Every call of the battery is a single BRP object, never a batch.
        for body in fake.requests() {
            let parsed: serde_json::Value =
                serde_json::from_str(&body).expect("a JSON request body");
            assert!(parsed.is_object(), "a batch was sent: {body}");
        }
        assert_eq!(fake.read_failures(), Vec::<String>::new());
        // And the raw calls are kept as evidence.
        let calls = observations.all_calls();
        assert!(
            calls.len() > 10,
            "one call record per phase: {}",
            calls.len()
        );
        assert!(
            calls.iter().any(|call| call
                .brp_methods
                .iter()
                .any(|method| method == "world.mutate_resources")),
            "the injections are in the evidence"
        );
        assert!(calls.iter().all(|call| !call.brp_methods.is_empty()));
    }

    /// The frame in every reading is the GAME's counter, and it advances because
    /// the game advanced — not because the adapter polled.
    #[test]
    fn every_reading_carries_the_games_own_frame_counter() {
        let state = Arc::new(std::sync::Mutex::new(GameState::new()));
        let (fake, server) = game_server(&state);
        // Configure first, then install the fake client: the configuration
        // rebuilds the client and the server, so the order matters.
        let mut adapter = BevyAdapter::at(".")
            .with_config(BevyAdapterConfig::default())
            .with_client(BrpClient::new(
                fake.endpoint(),
                Duration::from_millis(2_000),
            ));
        adapter.server = server;
        let observations = adapter.run_battery().expect("the battery runs");
        let positions = observations.readings_of(SemanticKind::PlayerTransform);
        assert!(positions.len() > 3);
        // The observations overlap (the win-position sample is taken inside the
        // coin/win window), so the flattened list is not one chronology; what the
        // contract promises is that **the game's own frames never go backwards**,
        // which is checked window by window below.  `readings_of` is used rather
        // than `all_observations` on purpose: it is the projection a report reads.
        let frames: Vec<u64> = positions.iter().map(|reading| reading.frame).collect();
        let mut sorted = frames.clone();
        sorted.sort_unstable();
        assert_eq!(
            frames.len(),
            sorted.len(),
            "every position reading keeps its frame"
        );
        assert!(
            frames.iter().max().copied().unwrap_or(0) > frames.iter().min().copied().unwrap_or(0),
            "the game advanced its own frames during the battery: {frames:?}"
        );
        // Per observation, the frames are a chronology: a single window never
        // reads a frame it already passed.
        for observation in observations.all_observations() {
            let window: Vec<u64> = observation
                .readings
                .iter()
                .map(|reading| reading.frame)
                .collect();
            let mut sorted = window.clone();
            sorted.sort_unstable();
            assert_eq!(
                window, sorted,
                "a window's frames must only ever advance: {window:?}"
            );
        }
    }

    /// A game whose jump only ever falls is a **failed** criterion, and the
    /// failure says why — the reading that was red in the Godot era stays red.
    #[test]
    fn a_monotone_fall_makes_the_jump_criterion_fail_with_a_reason() {
        let state = Arc::new(std::sync::Mutex::new(GameState::new()));
        {
            // The game only ever descends: nothing about this arc rises.
            let mut game = state.lock().expect("the game state");
            game.never_rise = true;
            game.grounded_reads = 0;
            game.y = -100.0;
        }
        let falling = Arc::clone(&state);
        let reply = Reply::From(Arc::new(move |request: &str, prior: &[String]| {
            let parsed: serde_json::Value =
                serde_json::from_str(request).expect("a JSON request body");
            let (status, body) = handle_request(&falling, &parsed, prior);
            let _ = status;
            Reply::Raw200(body)
        }));
        let fake = FakeBrp::spawn(vec![reply]);
        let mut adapter = BevyAdapter::at(".")
            .with_config(BevyAdapterConfig::default())
            .with_client(BrpClient::new(
                fake.endpoint(),
                Duration::from_millis(2_000),
            ));
        let observations = adapter.run_battery().expect("the battery runs");
        let failure = observations
            .jump
            .failure
            .clone()
            .expect("a monotone fall is not a jump");
        assert!(failure.contains("monotone fall"), "{failure}");
        assert!(!observations.jump.observed);
        assert_eq!(
            observations.jump.arc.as_ref().map(|arc| arc.rising),
            Some(0),
            "{:?}",
            observations.jump.arc
        );
    }

    /// A battery that cannot read anything at all is an **abort**, not nine
    /// fabricated readings, and every gap says so.
    #[test]
    fn a_battery_that_cannot_read_aborts_and_gaps_every_criterion() {
        let fake = FakeBrp::spawn(vec![Reply::Json(serde_json::json!({
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -23502, "message": "Unknown resource type: FrameCounter"},
        }))]);
        // Configure first, then install the fake client: the configuration
        // rebuilds the client and the server, so the order matters.
        let mut adapter = BevyAdapter::at(".")
            .with_config(BevyAdapterConfig::default())
            .with_client(BrpClient::new(
                fake.endpoint(),
                Duration::from_millis(2_000),
            ));
        let observations = adapter.run_battery().expect("the battery answers");
        assert!(
            observations.aborted.is_some(),
            "a battery with no frame aborts"
        );
        assert!(!observations.passed());
        let gaps = observations.gaps();
        assert_eq!(gaps.len(), 9);
        for (name, reason) in gaps {
            assert!(
                reason.contains("not observed"),
                "{name} must say it was not observed: {reason}"
            );
        }
    }

    /// `prepare()` refuses a workspace whose crate is not the frozen one, and it
    /// refuses it **before** running a build.
    #[test]
    fn prepare_refuses_a_game_that_is_not_the_frozen_crate() {
        let directory = tempfile::tempdir().expect("a temporary workspace");
        std::fs::write(
            directory.path().join("Cargo.toml"),
            "[package]\nname = \"some_other_game\"\n",
        )
        .expect("a manifest");
        std::fs::write(directory.path().join("Cargo.lock"), "# lock\n").expect("a lockfile");
        let builder = Arc::new(FakeBuilder::succeeding(
            directory.path().join("target/debug/hof_game"),
            1_000,
        ));
        let mut adapter = BevyAdapter::at(directory.path())
            .with_builder(builder.clone())
            .with_features(Box::new(FakeFeatures::frozen()))
            .with_contract_paths(Box::new(FakeContractPaths::frozen()));
        let error = adapter
            .prepare(&Project::at(directory.path()))
            .expect_err("a differently named crate is a contract violation");
        let typed = error.downcast_ref::<AdapterError>();
        assert!(
            matches!(typed, Some(AdapterError::ContractViolation(_))),
            "{error:?}"
        );
        assert!(
            builder.requests().is_empty(),
            "the contract is checked before the build"
        );
    }

    /// `prepare()` runs the build with the policy's arguments, records the
    /// measured duration, and reports an overrun **without** raising it: a
    /// budget overrun is a gate fact (DESIGN-DETAIL §7), not a game defect.
    #[test]
    fn prepare_measures_the_build_and_reports_an_overrun_without_failing() {
        let directory = tempfile::tempdir().expect("a temporary workspace");
        std::fs::write(
            directory.path().join("Cargo.toml"),
            "[package]\nname = \"hof_game\"\nversion = \"0.1.0\"\n",
        )
        .expect("a manifest");
        std::fs::write(directory.path().join("Cargo.lock"), "# lock\n").expect("a lockfile");
        let builder = Arc::new(FakeBuilder::succeeding(
            directory.path().join("target/debug/hof_game"),
            crate::adapter::bevy::build::COLD_BUILD_BUDGET_MILLIS + 1_000,
        ));
        let policy = crate::adapter::bevy::build::BuildPolicy::pinned_to(
            directory.path(),
            Some(directory.path().join("shared-target")),
        )
        .expect("the policy pins the lockfile");
        let mut adapter = BevyAdapter::at(directory.path())
            .with_builder(builder.clone())
            .with_features(Box::new(FakeFeatures::frozen()))
            .with_contract_paths(Box::new(FakeContractPaths::frozen()))
            .with_config(BevyAdapterConfig {
                build_policy: policy,
                ..BevyAdapterConfig::default()
            });
        let prepared = adapter
            .prepare(&Project::at(directory.path()))
            .expect("an over-budget build still prepared");
        assert_eq!(adapter.build_millis(), 601_000);
        assert_eq!(
            adapter.budget_millis(),
            Some(crate::adapter::bevy::build::COLD_BUILD_BUDGET_MILLIS)
        );
        assert!(prepared.detail.contains("over the"));
        assert_eq!(
            builder.requests()[0].target_dir,
            Some(directory.path().join("shared-target")),
            "the shared persistent target directory reached the builder"
        );
    }

    /// Round 0's warm-up is a **separate** build, and its duration is not the
    /// artifact's build time: a 250 s warm-up must not make the artifact look
    /// like a 250 s build.
    #[test]
    fn prepare_warms_the_graph_first_and_keeps_the_warmup_out_of_the_build_time() {
        let directory = tempfile::tempdir().expect("a temporary workspace");
        std::fs::write(
            directory.path().join("Cargo.toml"),
            "[package]\nname = \"hof_game\"\n",
        )
        .expect("a manifest");
        std::fs::write(directory.path().join("Cargo.lock"), "# lock\n").expect("a lockfile");
        let builder = Arc::new(FakeBuilder::succeeding(
            directory.path().join("target/debug/hof_game"),
            12_000,
        ));
        let policy = crate::adapter::bevy::build::BuildPolicy::pinned_to(directory.path(), None)
            .expect("the policy pins the lockfile")
            .with_warmup();
        let mut adapter = BevyAdapter::at(directory.path())
            .with_builder(builder.clone())
            .with_features(Box::new(FakeFeatures::frozen()))
            .with_contract_paths(Box::new(FakeContractPaths::frozen()))
            .with_config(BevyAdapterConfig {
                build_policy: policy,
                ..BevyAdapterConfig::default()
            });
        let prepared = adapter
            .prepare(&Project::at(directory.path()))
            .expect("a warmed round prepares");
        assert_eq!(
            builder.requests().len(),
            2,
            "the warm-up and the artifact build are two builds"
        );
        assert_eq!(
            adapter.build_millis(),
            12_000,
            "the artifact's own build time"
        );
        assert!(prepared.detail.contains("warm-up:"), "{}", prepared.detail);
    }

    /// A lockfile that moved since the policy was pinned is refused: the round
    /// would not be comparable with its predecessors.
    #[test]
    fn prepare_refuses_a_lockfile_that_moved_inside_the_round() {
        let directory = tempfile::tempdir().expect("a temporary workspace");
        std::fs::write(
            directory.path().join("Cargo.toml"),
            "[package]\nname = \"hof_game\"\n",
        )
        .expect("a manifest");
        let lock = directory.path().join("Cargo.lock");
        std::fs::write(&lock, "# lock\n").expect("a lockfile");
        let policy =
            crate::adapter::bevy::build::BuildPolicy::pinned_to(directory.path(), None).unwrap();
        std::fs::write(&lock, "# the lockfile moved\n").expect("a drifted lockfile");
        let mut adapter = BevyAdapter::at(directory.path())
            .with_builder(Arc::new(FakeBuilder::succeeding("x", 1)))
            .with_features(Box::new(FakeFeatures::frozen()))
            .with_contract_paths(Box::new(FakeContractPaths::frozen()))
            .with_config(BevyAdapterConfig {
                build_policy: policy,
                ..BevyAdapterConfig::default()
            });
        let error = adapter
            .prepare(&Project::at(directory.path()))
            .expect_err("a moved lockfile is refused");
        assert!(
            error.to_string().contains("incomparable")
                || error.to_string().contains("not comparable"),
            "{error}"
        );
    }

    /// A game project on disk: the frozen crate name, a lockfile, and a source
    /// tree that declares the contract types the PRD requires.  `registered` is
    /// the list of `register_type` names to write.
    fn a_game_project(directory: &Path, registered: &[&str]) {
        std::fs::create_dir_all(directory.join("src")).expect("a source tree");
        std::fs::write(
            directory.join("Cargo.toml"),
            "[package]\nname = \"hof_game\"\nversion = \"0.1.0\"\n",
        )
        .expect("a manifest");
        std::fs::write(directory.join("Cargo.lock"), "# lock\n").expect("a lockfile");
        let mut source = String::from("use bevy::prelude::*;\n");
        for name in registered {
            source.push_str(&format!(
                "fn wire_{name}(app: &mut App) {{ app.register_type::<{name}>(); }}\n"
            ));
        }
        std::fs::write(directory.join("src").join("contract.rs"), source)
            .expect("a contract module");
    }

    /// A `cargo metadata` document in which the **resolved** graph of the bevy
    /// package carries `bevy_remote`.
    fn metadata_with_resolved_features() -> serde_json::Value {
        serde_json::json!({
            "packages": [
                {"name": "hof_game", "id": "path+file:///g#hof_game@0.1.0", "features": {}},
                {"name": "bevy", "id": "registry+https://x#bevy@0.19.1",
                 "features": {"bevy_remote": [], "bevy_winit": []}},
            ],
            "resolve": {"nodes": [
                {"id": "path+file:///g#hof_game@0.1.0", "features": []},
                {"id": "registry+https://x#bevy@0.19.1",
                 "features": ["bevy_remote", "default", "bevy_asset"]},
            ]}
        })
    }

    const ALL_CONTRACT_NAMES: &[&str] = &[
        "Player",
        "Grounded",
        "CoinCounter",
        "WinFlag",
        "FrameCounter",
        "InputIntent",
    ];

    /// B2-1: the **real** reader path reaches the build and the contract check.
    /// It must not fail with "pinned to <empty>" (the default policy used to
    /// carry no pin) or with all seven paths missing (the feature reader used to
    /// feed feature names to the type-path check).
    #[test]
    fn a_real_project_reaches_the_build_and_the_contract_check_with_coherent_reasons() {
        let directory = tempfile::tempdir().expect("a temporary workspace");
        a_game_project(directory.path(), ALL_CONTRACT_NAMES);
        let builder = Arc::new(FakeBuilder::succeeding(
            directory.path().join("target/debug/hof_game"),
            12_000,
        ));
        let mut adapter = BevyAdapter::at(directory.path())
            .with_builder(builder.clone())
            .with_features(Box::new(CargoMetadataFeatures::from_document(
                metadata_with_resolved_features(),
            )));
        let prepared = adapter
            .prepare(&Project::at(directory.path()))
            .expect("a compliant project prepares");
        assert_eq!(builder.requests().len(), 1, "the build really ran");
        assert!(
            adapter.is_lockfile_pinned(),
            "the adapter pinned the lockfile it was constructed with"
        );
        assert_eq!(
            adapter.contract_paths().len(),
            crate::adapter::bevy::contract::CONTRACT.len(),
            "the contract reader read the seven declared paths: {:?}",
            adapter.contract_paths()
        );
        // Neither nonsense reason may appear on a compliant project.
        assert!(
            !prepared.detail.contains("pinned to"),
            "{}",
            prepared.detail
        );
        assert!(!prepared.detail.contains("missing"), "{}", prepared.detail);
    }

    /// B2-1: a project that fails the **contract** check names the specific
    /// missing path, after the build it paid for.
    #[test]
    fn a_missing_contract_registration_names_the_specific_path() {
        let directory = tempfile::tempdir().expect("a temporary workspace");
        let registered: Vec<&str> = ALL_CONTRACT_NAMES
            .iter()
            .copied()
            .filter(|name| *name != "Grounded")
            .collect();
        a_game_project(directory.path(), &registered);
        let builder = Arc::new(FakeBuilder::succeeding(
            directory.path().join("target/debug/hof_game"),
            12_000,
        ));
        let mut adapter = BevyAdapter::at(directory.path())
            .with_builder(builder.clone())
            .with_features(Box::new(CargoMetadataFeatures::from_document(
                metadata_with_resolved_features(),
            )));
        let error = adapter
            .prepare(&Project::at(directory.path()))
            .expect_err("a missing contract type is a project defect");
        let typed = error.downcast_ref::<AdapterError>();
        assert!(
            matches!(typed, Some(AdapterError::ContractViolation(_))),
            "{error:?}"
        );
        let message = error.to_string();
        assert!(
            message.contains("hof_game::contract::Grounded"),
            "the reason must name the specific missing path: {message}"
        );
        assert!(
            !message.contains("hof_game::contract::Player"),
            "it must not list paths that are present: {message}"
        );
        assert!(
            !message.contains("bevy_remote"),
            "a contract failure is not a feature failure: {message}"
        );
        assert_eq!(
            builder.requests().len(),
            1,
            "the build was reached before the contract check"
        );
    }

    /// B2-4: a project whose **declared** feature table carries `bevy_remote`
    /// but whose **resolved** graph does not is refused — that is the drift that
    /// costs the documented warm-increment penalty.
    #[test]
    fn the_feature_check_reads_the_resolved_graph_not_the_declared_table() {
        let directory = tempfile::tempdir().expect("a temporary workspace");
        a_game_project(directory.path(), ALL_CONTRACT_NAMES);
        let drifted = serde_json::json!({
            "packages": [
                {"name": "hof_game", "id": "g", "features": {}},
                {"name": "bevy", "id": "b", "features": {"bevy_remote": []}},
            ],
            "resolve": {"nodes": [
                {"id": "g", "features": []},
                {"id": "b", "features": ["default"]},
            ]}
        });
        let builder = Arc::new(FakeBuilder::succeeding("x", 12_000));
        let mut adapter = BevyAdapter::at(directory.path())
            .with_builder(builder)
            .with_features(Box::new(CargoMetadataFeatures::from_document(drifted)));
        let error = adapter
            .prepare(&Project::at(directory.path()))
            .expect_err("a resolved drift is refused");
        let message = error.to_string();
        assert!(message.contains("bevy_remote"), "{message}");
        assert!(
            message.contains("resolved"),
            "the reason must say which set it compared: {message}"
        );
        assert!(
            !message.contains("contract type path"),
            "a feature failure is not a path failure: {message}"
        );
    }

    /// B2-1: the feature check has its own reason and its own pin, so a drifted
    /// feature hash is refused without mentioning type paths.
    #[test]
    fn the_feature_check_has_its_own_reason_and_pin() {
        let directory = tempfile::tempdir().expect("a temporary workspace");
        a_game_project(directory.path(), ALL_CONTRACT_NAMES);
        let builder = Arc::new(FakeBuilder::succeeding("x", 12_000));
        let mut adapter = BevyAdapter::at(directory.path())
            .with_builder(builder)
            .with_features(Box::new(FakeFeatures::drifted()))
            .with_contract_paths(Box::new(FakeContractPaths::frozen()));
        let error = adapter
            .prepare(&Project::at(directory.path()))
            .expect_err("a drifted feature hash is refused");
        let message = error.to_string();
        assert!(message.contains("feature set"), "{message}");
        assert!(
            message.contains(build::FEATURE_SET_SHA256),
            "the reason quotes the pin it compared against: {message}"
        );
        assert!(
            !message.contains("type path"),
            "the reason is about features, not paths: {message}"
        );
    }

    /// The adapter's endpoint is the pinned main-world port, and the only way to
    /// address another one is the explicit test override.
    #[test]
    fn the_adapter_addresses_only_the_pinned_endpoint_by_default() {
        let adapter = BevyAdapter::at(".");
        assert!(adapter.is_pinned_endpoint());
        assert_eq!(adapter.endpoint(), "http://127.0.0.1:15702/");
        let elsewhere = BevyAdapter::at(".").with_endpoint("http://127.0.0.1:0/");
        assert!(!elsewhere.is_pinned_endpoint());
    }

    /// B2-6: when the adapter is moved off 15702 the game's environment **and**
    /// the readiness probe move with it, so the two cannot disagree.
    #[test]
    fn a_moved_endpoint_reaches_the_readiness_probe_not_only_the_environment() {
        let pinned = BevyAdapter::at(".").launch_config();
        assert_eq!(pinned.endpoint(), "http://127.0.0.1:15702/");
        assert!(
            pinned.env.is_empty(),
            "a pinned round sets no endpoint override: {:?}",
            pinned.env
        );

        let adapter = BevyAdapter::at(".").with_endpoint("http://127.0.0.1:19999/");
        let config = adapter.launch_config();
        assert_eq!(config.endpoint(), "http://127.0.0.1:19999/");
        assert_eq!(
            config.probe_client().endpoint(),
            config.endpoint(),
            "the readiness probe must use the adapter's endpoint"
        );
        assert!(
            config
                .env
                .iter()
                .any(|(name, value)| name == "HOF_BRP_ENDPOINT_OVERRIDE"
                    && value == "http://127.0.0.1:19999/"),
            "the game is told the same endpoint: {:?}",
            config.env
        );
    }

    /// `stop` without a game is a task-level failure, not a fabricated report,
    /// and `health` without a game never claims the process is alive.
    #[test]
    fn stopping_or_health_checking_without_a_game_is_a_typed_failure() {
        let mut adapter = BevyAdapter::at(".");
        let error = adapter
            .stop(RunningGame {
                pid: 1,
                endpoint: None,
                headless: true,
            })
            .expect_err("there is no game to stop");
        assert!(error.to_string().contains("no game process"), "{error}");
        let error = adapter.health().expect_err("no process is known");
        let typed = error.downcast_ref::<AdapterError>();
        assert!(
            matches!(typed, Some(AdapterError::Unsupported { .. })),
            "{error:?}"
        );
    }

    /// The scripted game is unused on its own; it exists to name the failure mode
    /// of driving the battery without a transport.
    #[test]
    fn the_scripted_game_refuses_to_pretend_it_is_a_transport() {
        let mut game = ScriptedGame;
        let driver: &mut dyn BatteryDriver = &mut game;
        assert!(driver.read(SemanticKind::Grounded).is_err());
        assert!(driver.inject(&Intent::Move { dir: 1 }, true).is_err());
        assert!(driver.wait_frames(1).is_err());
        assert!(driver.take_evidence().is_empty());
    }
}
