//! The build contract's executable half: the policy `prepare()` enforces, the
//! builder it runs, and the frozen set it checks afterwards.
//!
//! Bevy is a compiled engine, so a round's cost *is* a build cost, and the
//! measured facts (SPIKE-1 §3.5, SPIKE-2 §0.2) are sharp:
//!
//! * a shared, persistent target directory turns a 5 minute cold build into a
//!   ~12 s warm one;
//! * **only while the feature set is frozen** — a feature-set change in the same
//!   directory recompiled `bevy`/`bevy_internal` and cost **236 s**;
//! * the lockfile must not move inside a round, and a move is not "a failure"
//!   but "this round is not comparable", which is why the hash is carried in
//!   `meta.json` instead of being a hard stop.
//!
//! Design choices that are deliberate rather than incidental:
//!
//! * **The build runs offline by default.**  `BuildPolicy::offline` is `true`,
//!   and `prepare()` is the only place a round's build happens, so a round cannot
//!   silently fetch a new dependency and change what it measured.
//! * **The builder is a trait.**  A real round gets [`CargoBuilder`]; a test
//!   gets a fake, which is the only way the budget and budget-overrun paths can
//!   be exercised without paying five minutes or having a network.
//! * **A budget overrun is reported, not raised.**  `prepare()` returns the
//!   `Prepared` and records the overrun, because DESIGN-DETAIL §7 classifies a
//!   budget overrun as `build_budget_exceeded` — a gate fact, not a defect of the
//!   game.

use std::io::Read;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::Arc;
use std::time::{Duration, Instant};

use serde_json::json;

use crate::adapter::AdapterError;

/// The pinned Bevy version (D296: 0.19.1).
pub const BEVY_VERSION: &str = "0.19.1";

/// The frozen Bevy feature set.  `bevy_remote` is the observation surface
/// (SPIKE-1 §1.4); everything else is Bevy's default set, which the PRD's
/// dependency line leaves on.
pub const FROZEN_FEATURES: &[&str] = &["bevy_remote"];

/// Whether Bevy's default features stay enabled.  Turning them off is route B in
/// SPIKE-2 (no `bevy_winit` in the dependency graph at all) and would remove
/// `Sprite`/`Camera2d` from the game's source — a different contract, not a
/// performance tweak.
pub const FROZEN_DEFAULT_FEATURES: bool = true;

/// The budget upper bounds (DESIGN-DETAIL §5, SPIKE-2 §10-7).
pub const COLD_BUILD_BUDGET_MILLIS: u64 = 600_000;
pub const WARM_BUILD_BUDGET_MILLIS: u64 = 120_000;
pub const ROUND_BUDGET_MILLIS: u64 = 300_000;
pub const ENDPOINT_READY_BUDGET_MILLIS: u64 = 30_000;

/// The frozen feature set's hash, recorded in `meta.json.feature_sha256`.  A
/// drift here is what makes a warm build 236 s instead of 12 s, so it is
/// measured per round rather than assumed.
pub fn feature_set_sha256() -> String {
    crate::runtime::policy::sha256_hex(
        crate::adapter::bevy::contract::canonical_json(&feature_set_value()).as_bytes(),
    )
}

/// The pinned feature-set hash literal (see [`feature_set_sha256`]).
pub const FEATURE_SET_SHA256: &str =
    "d6a90ba39e67b9e05fd28d97cc570dc989a03e8ec7a15ba93d077d5fe95d1f96";

/// `sha256` of a `Cargo.lock`'s bytes, or an explicit task-level failure when it
/// cannot be read (an unreadable lockfile is not a lockfile that did not drift).
pub fn lockfile_sha256(path: &Path) -> Result<String, AdapterError> {
    let bytes = std::fs::read(path).map_err(|error| {
        AdapterError::Malformed(format!("`{}` could not be read: {error}", path.display()))
    })?;
    Ok(crate::runtime::policy::sha256_hex(&bytes))
}

/// DESIGN-DETAIL §5: the lockfile must not change inside a round.  Drift is
/// reported, not repaired.
pub fn lockfile_matches(expected_sha256: &str, path: &Path) -> Result<(), AdapterError> {
    let actual = lockfile_sha256(path)?;
    if actual == expected_sha256 {
        return Ok(());
    }
    Err(AdapterError::Malformed(format!(
        "the lockfile changed inside the round: expected {expected_sha256}, measured {actual} — \
         this round is not comparable with its predecessors"
    )))
}

/// The three budget bounds a completed build is judged against.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct BuildBudget {
    pub cold_millis: u64,
    pub warm_millis: u64,
    pub round_millis: u64,
}

impl Default for BuildBudget {
    fn default() -> Self {
        Self {
            cold_millis: COLD_BUILD_BUDGET_MILLIS,
            warm_millis: WARM_BUILD_BUDGET_MILLIS,
            round_millis: ROUND_BUDGET_MILLIS,
        }
    }
}

impl BuildBudget {
    /// `warm == true` writes a round that reused the persistent target
    /// directory, so the warm bound applies.
    pub fn exceeded(&self, elapsed_millis: u64, warm: bool) -> Option<u64> {
        let bound = if warm {
            self.warm_millis
        } else {
            self.cold_millis
        };
        (elapsed_millis > bound).then_some(bound)
    }
}

/// The feature-set document the hash is taken over.  It is a value, not a
/// comment, so changing a feature necessarily changes the hash.
pub fn feature_set_value() -> serde_json::Value {
    json!({
        "bevy": BEVY_VERSION,
        "default_features": FROZEN_DEFAULT_FEATURES,
        "features": FROZEN_FEATURES,
    })
}

/// The build and cache policy `prepare()` enforces (DESIGN-DETAIL §5).
#[derive(Clone, Debug)]
pub struct BuildPolicy {
    /// The **shared persistent** target directory.  `None` means the workspace's
    /// own `target/`, which is what a single-project round uses.
    pub target_dir: Option<PathBuf>,
    /// The lockfile hash this round is pinned to, or `None` when the round is
    /// **explicitly** not comparing lockfiles.
    ///
    /// It is an `Option` rather than an empty string because an empty string is
    /// not a pin: comparing a measured hash against it produces "pinned to
    /// <empty>", which is a reason no reader can act on (B2-1).  `None` means
    /// "no comparison was requested", and `prepare()` says so instead.
    pub lock_sha256: Option<String>,
    /// The feature-set hash this round is pinned to.
    pub feature_sha256: String,
    pub budget: BuildBudget,
    /// Whether the build must run without touching the network.
    pub offline: bool,
    /// **Round-0 warm-up** (DESIGN-DETAIL §5): compile the dependency graph
    /// before the round's own artifact, so the round being measured is the warm
    /// one.  It is a separate build, and its duration is *not* the artifact's
    /// build time — a warm-up that took 250 s must not make the artifact look
    /// like a 250 s build.
    pub warmup: bool,
    /// Extra arguments for `cargo build`.
    pub extra_args: Vec<String>,
}

impl Default for BuildPolicy {
    fn default() -> Self {
        Self {
            target_dir: None,
            lock_sha256: None,
            feature_sha256: FEATURE_SET_SHA256.to_string(),
            budget: BuildBudget::default(),
            offline: true,
            warmup: false,
            extra_args: Vec::new(),
        }
    }
}

impl BuildPolicy {
    /// A policy pinned to the lockfile on disk.  `prepare()` refuses a lockfile
    /// that no longer hashes to this.
    pub fn pinned_to(workspace: &Path, target_dir: Option<PathBuf>) -> Result<Self, AdapterError> {
        Ok(Self {
            lock_sha256: Some(lockfile_sha256(&workspace.join("Cargo.lock"))?),
            ..Self::pinned_if_available(workspace, target_dir)
        })
    }

    /// A policy pinned to the lockfile when there is one to pin, and explicitly
    /// unpinned otherwise.  It is what an adapter constructed for a workspace
    /// uses, so the real path is pinned **by construction** rather than left
    /// comparing against an empty string (B2-1).
    pub fn pinned_if_available(workspace: &Path, target_dir: Option<PathBuf>) -> Self {
        let lock_sha256 = lockfile_sha256(&workspace.join("Cargo.lock")).ok();
        Self {
            target_dir,
            lock_sha256,
            ..Self::default()
        }
    }

    /// Whether this round compares the lockfile it measured.
    pub fn is_locked(&self) -> bool {
        self.lock_sha256.is_some()
    }

    /// The round-0 policy (DESIGN-DETAIL §5): the same pins, with the dependency
    /// graph warmed first.
    pub fn with_warmup(mut self) -> Self {
        self.warmup = true;
        self
    }
}

/// One build request.  It is a value so a fake builder can inspect it and a test
/// can assert the policy reached the builder unchanged.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct BuildRequest {
    pub manifest: PathBuf,
    pub workspace: PathBuf,
    pub target_dir: Option<PathBuf>,
    pub timeout: Duration,
}

/// What a build did.  `cache_hit` is the round's own judgement of whether this
/// was a warm build (the binary existed and nothing was recompiled); it selects
/// the budget the duration is compared against.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct BuildOutcome {
    pub binary: PathBuf,
    pub elapsed_millis: u64,
    pub cache_hit: bool,
    pub exit_code: Option<i32>,
    /// The build's own output, verbatim (it is `build.log`).
    pub output: String,
}

impl BuildOutcome {
    /// The one line `build.log` opens with.
    pub fn log_line(&self) -> String {
        format!(
            "cargo build: exit {:?}, {} ms, {}",
            self.exit_code,
            self.elapsed_millis,
            if self.cache_hit { "warm" } else { "cold" }
        )
    }
}

/// How a spawned build process ended.
///
/// It exists so the deadline is enforced *inside* the wait rather than checked
/// afterwards: a build that hangs must not hang the round (B2-5).
#[derive(Debug)]
pub enum ChildEnd {
    /// The child exited on its own.
    Exited { code: Option<i32>, output: String },
    /// The child outlived its budget and was killed.
    TimedOut { output: String },
}

/// Wait for `child` for at most `timeout`, draining both pipes on reader threads
/// so a child that fills a pipe buffer cannot deadlock the wait.
///
/// On expiry the child is **killed** and reaped, and the caller is told it timed
/// out: `BuildRequest.timeout` is what the budget means, and a budget that is
/// only measured after the fact is not enforced (B2-5).
pub fn wait_with_timeout(
    child: &mut std::process::Child,
    timeout: Duration,
) -> Result<ChildEnd, String> {
    let drain = |pipe: Option<Box<dyn Read + Send>>| {
        pipe.map(|mut pipe| {
            std::thread::spawn(move || {
                let mut buffer = Vec::new();
                let _ = pipe.read_to_end(&mut buffer);
                buffer
            })
        })
    };
    let stdout = drain(
        child
            .stdout
            .take()
            .map(|pipe| Box::new(pipe) as Box<dyn Read + Send>),
    );
    let stderr = drain(
        child
            .stderr
            .take()
            .map(|pipe| Box::new(pipe) as Box<dyn Read + Send>),
    );
    let started = Instant::now();
    let status = loop {
        match child.try_wait() {
            Ok(Some(finished)) => break finished,
            Ok(None) => {}
            Err(error) => {
                return Err(format!("the process state could not be read: {error}"));
            }
        }
        if started.elapsed() >= timeout {
            let pid = child.id();
            let _ = child.kill();
            kill_tree(pid);
            let _ = child.wait();
            // The pipe readers are deliberately **not** joined here: a killed
            // build can leave a descendant (cargo leaves rustc) holding the pipe
            // open, and blocking on that would defeat the deadline this function
            // exists to enforce.  Their output is unused on a timeout.
            return Ok(ChildEnd::TimedOut {
                output: String::new(),
            });
        }
        std::thread::sleep(Duration::from_millis(20));
    };
    let mut text = String::new();
    if let Some(reader) = stdout {
        text.push_str(&String::from_utf8_lossy(&reader.join().unwrap_or_default()));
    }
    if let Some(reader) = stderr {
        text.push_str(&String::from_utf8_lossy(&reader.join().unwrap_or_default()));
    }
    Ok(ChildEnd::Exited {
        code: status.code(),
        output: text,
    })
}

/// Kill a process **and its descendants**, so a timed-out build cannot leave a
/// compiler running behind the round.
///
/// On Windows `Child::kill` terminates only the direct child; `cargo` starts
/// `rustc`, which would keep the pipes open and keep compiling.  On other
/// platforms the direct kill is what is available without a process group, and
/// the caller does not wait on the pipes, so the round still returns.
#[cfg(windows)]
fn kill_tree(pid: u32) {
    let _ = Command::new("taskkill")
        .args(["/F", "/T", "/PID", &pid.to_string()])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status();
}

#[cfg(not(windows))]
fn kill_tree(_pid: u32) {}

/// A builder.  `Send + Sync` so an adapter can be moved between the round's
/// stages; `&self` so a shared builder cannot be mutated mid-round.
pub trait Builder: Send + Sync {
    fn build(&self, request: &BuildRequest) -> Result<BuildOutcome, AdapterError>;
}

/// A boxed builder, for the adapters that take one by injection.
pub type DynBuilder = Arc<dyn Builder>;

/// The real builder: `cargo build`, with the policy's arguments.
#[derive(Clone, Debug, Default)]
pub struct CargoBuilder {
    /// The `cargo` program, when it is not on `PATH` under that name.
    pub program: Option<PathBuf>,
    /// Extra arguments (the policy's are appended after these).
    pub args: Vec<String>,
    /// Whether to pass `--offline`.
    pub offline: bool,
}

impl CargoBuilder {
    pub fn new() -> Self {
        Self {
            program: None,
            args: Vec::new(),
            offline: true,
        }
    }

    pub fn with_program(mut self, program: impl Into<PathBuf>) -> Self {
        self.program = Some(program.into());
        self
    }
}

impl Builder for CargoBuilder {
    fn build(&self, request: &BuildRequest) -> Result<BuildOutcome, AdapterError> {
        let program = self
            .program
            .clone()
            .unwrap_or_else(|| PathBuf::from("cargo"));
        let mut command = Command::new(&program);
        command
            .arg("build")
            .arg("--manifest-path")
            .arg(&request.manifest);
        if self.offline {
            command.arg("--offline");
        }
        if let Some(target_dir) = &request.target_dir {
            command.arg("--target-dir").arg(target_dir);
        }
        for arg in self.args.iter() {
            command.arg(arg);
        }
        command
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());
        let started = Instant::now();
        let mut child = command.spawn().map_err(|error| AdapterError::Transport {
            endpoint: crate::adapter::bevy::brp::endpoint(),
            message: format!("`{}` could not be started: {error}", program.display()),
        })?;
        let end = wait_with_timeout(&mut child, request.timeout).map_err(|message| {
            AdapterError::Transport {
                endpoint: crate::adapter::bevy::brp::endpoint(),
                message: format!("the build's output could not be collected: {message}"),
            }
        })?;
        let elapsed_millis = started.elapsed().as_millis() as u64;
        let (exit_code, text) = match end {
            // The budget is enforced, not measured after the fact: a build that
            // hangs is killed and reported as a budget fact (B2-5).
            ChildEnd::TimedOut { .. } => {
                return Err(AdapterError::BuildBudgetExceeded {
                    budget_millis: request.timeout.as_millis() as u64,
                    observed_millis: elapsed_millis,
                });
            }
            ChildEnd::Exited { code, output } => (code, output),
        };
        let binary = crate::adapter::bevy::launch::debug_binary(
            &request.workspace,
            crate::adapter::bevy::contract::GAME_CRATE,
            request.target_dir.as_deref(),
        );
        let cache_hit = text
            .lines()
            .all(|line| !line.starts_with("   Compiling bevy"));
        Ok(BuildOutcome {
            binary,
            elapsed_millis,
            cache_hit,
            exit_code,
            output: text,
        })
    }
}

/// The frozen feature set as a resolved list, sorted and deduplicated.
///
/// It is the reference both modes compare against: the real reader filters the
/// resolved graph down to this list, and a test can state the same list directly.
pub fn frozen_feature_list() -> Vec<String> {
    let mut features: Vec<String> = FROZEN_FEATURES
        .iter()
        .map(|name| name.to_string())
        .collect();
    features.sort();
    features.dedup();
    features
}

/// The hash of a resolved feature list, recorded as
/// `meta.json.feature_sha256`.
///
/// It hashes the **whole feature-set document** with the given list substituted
/// for the frozen one, so a resolved set that equals the frozen set produces
/// exactly [`FEATURE_SET_SHA256`] and any difference (an added feature, a lost
/// one, a different order — the canonical form sorts) moves it.  Defensive on
/// purpose: two lists with the same features hash the same regardless of input
/// ordering or duplication.
pub fn feature_hash_of(features: &[String]) -> String {
    let mut features: Vec<String> = features.to_vec();
    features.sort();
    features.dedup();
    let mut value = feature_set_value();
    value["features"] = json!(features);
    crate::runtime::policy::sha256_hex(
        crate::adapter::bevy::contract::canonical_json(&value).as_bytes(),
    )
}

/// The resolved feature set of a workspace.
///
/// It is **only** about the feature set (B2-1): the contract's type paths are a
/// different concern with a different source, a different pin and a different
/// failure reason, and they are read by [`ContractPathReader`].  Conflating the
/// two is what once fed Bevy feature names to the type-path check.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ResolvedFeatures {
    /// The hash of the resolved feature set, compared against
    /// [`FEATURE_SET_SHA256`].
    pub feature_sha256: String,
    /// The resolved features the frozen contract names: what the round actually
    /// compiled with.
    pub features: Vec<String>,
}

/// Where `prepare()` gets the workspace's resolved feature set.
///
/// It is a trait for one reason: the real implementation invokes `cargo metadata`
/// (slow, needs the lockfile resolved), and a test must be able to state the
/// resolved set without spawning cargo.
pub trait FeatureReader: Send + Sync {
    fn resolved_features(
        &self,
        workspace: &Path,
        crate_name: &str,
    ) -> Result<ResolvedFeatures, AdapterError>;
}

/// Where `prepare()` learns which **contract type paths** the game declares.
///
/// This is deliberately separate from [`FeatureReader`] (B2-1).  `cargo metadata`
/// resolves features and dependencies; it says nothing about reflectable types,
/// so the contract check reads the game's own source for the `register_type`
/// declarations the PRD requires (C2).  Each reader has its own pin
/// ([`FEATURE_SET_SHA256`] and [`crate::adapter::bevy::contract::CONTRACT`]) and
/// its own failure reason.
pub trait ContractPathReader: Send + Sync {
    fn declared_contract_paths(
        &self,
        workspace: &Path,
        crate_name: &str,
    ) -> Result<Vec<String>, AdapterError>;
}

/// The real feature reader: `cargo metadata`.
///
/// `cargo metadata` resolves the dependency graph without building it, so the
/// feature set a round actually compiled *can* be checked.  It reads the
/// **resolved** set (`resolve.nodes[].features`), not the declared feature table
/// of Bevy's manifest: the declared table is a property of Bevy 0.19.1, so it
/// would assert little more than "Bevy has `bevy_remote`" and could never notice
/// that the game did not enable it (B2-4).
///
/// The check is conservative in one direction on purpose: a crate named `bevy`
/// whose resolved feature set does not carry the frozen feature(s) is a
/// **contract violation**, because the frozen hash would no longer describe what
/// was built.
#[derive(Clone, Debug, Default)]
pub struct CargoMetadataFeatures {
    /// `None` runs `cargo metadata`; `Some` answers from this document.  The
    /// seam exists so a test can drive the **real** reader — and therefore
    /// `prepare()` — with a recorded `cargo metadata` document and no cargo.
    document: Option<Arc<serde_json::Value>>,
}

impl CargoMetadataFeatures {
    /// The real reader: it runs `cargo metadata`.
    pub fn new() -> Self {
        Self::default()
    }

    /// A reader over a document a test supplies.  The document is read exactly
    /// as `cargo metadata`'s output is, so this exercises the real parsing.
    pub fn from_document(document: serde_json::Value) -> Self {
        Self {
            document: Some(Arc::new(document)),
        }
    }

    /// The document to read: the injected one, or a fresh `cargo metadata`.
    fn metadata(&self, workspace: &Path) -> Result<serde_json::Value, AdapterError> {
        if let Some(document) = &self.document {
            return Ok((**document).clone());
        }
        let manifest = workspace.join("Cargo.toml");
        if !manifest.is_file() {
            return Err(AdapterError::ContractViolation(format!(
                "`{}` does not exist, so the resolved feature set cannot be measured",
                manifest.display()
            )));
        }
        let output = Command::new("cargo")
            .args(["metadata", "--format-version", "1", "--offline"])
            .arg("--manifest-path")
            .arg(&manifest)
            .stdin(Stdio::null())
            .output()
            .map_err(|error| AdapterError::Transport {
                endpoint: crate::adapter::bevy::brp::endpoint(),
                message: format!("`cargo metadata` could not be started: {error}"),
            })?;
        if !output.status.success() {
            return Err(AdapterError::Malformed(format!(
                "`cargo metadata` failed with {:?}: {}",
                output.status.code(),
                String::from_utf8_lossy(&output.stderr)
            )));
        }
        serde_json::from_slice(&output.stdout).map_err(|error| {
            AdapterError::Malformed(format!("`cargo metadata` did not produce JSON: {error}"))
        })
    }

    /// The package id of the `bevy` package in a `cargo metadata` document.
    pub fn bevy_package_id(metadata: &serde_json::Value) -> Option<String> {
        let packages = metadata.get("packages")?.as_array()?;
        for package in packages {
            if package.get("name").and_then(|value| value.as_str()) == Some("bevy") {
                if let Some(id) = package.get("id").and_then(|value| value.as_str()) {
                    return Some(id.to_string());
                }
            }
        }
        None
    }

    /// The **resolved** feature list of the `bevy` package: the features the
    /// round's dependency graph actually activated (`resolve.nodes[].features`),
    /// sorted and deduplicated (B2-4).
    ///
    /// A document without a `resolve` section cannot answer this question: a
    /// declared table is not what was compiled, so it is `None` rather than a
    /// fallback.
    pub fn resolved_bevy_features(metadata: &serde_json::Value) -> Option<Vec<String>> {
        let id = Self::bevy_package_id(metadata)?;
        let nodes = metadata.get("resolve")?.get("nodes")?.as_array()?;
        for node in nodes {
            if node.get("id").and_then(|value| value.as_str()) != Some(id.as_str()) {
                continue;
            }
            let mut features: Vec<String> = node
                .get("features")
                .and_then(|value| value.as_array())
                .map(|features| {
                    features
                        .iter()
                        .filter_map(|feature| feature.as_str().map(str::to_string))
                        .collect()
                })
                .unwrap_or_default();
            features.sort();
            features.dedup();
            return Some(features);
        }
        Some(Vec::new())
    }

    /// The *frozen* part of a resolved feature list: the features the contract
    /// names, in the contract's own order, with any that the resolved graph does
    /// not carry reported as missing.
    ///
    /// The filter matters.  A real `cargo metadata` reports every feature Bevy
    /// *declares* for every target and optional dependency, hundreds of them, and
    /// hashing that list would make the frozen hash a statement about Bevy's
    /// manifest rather than about what this adapter builds with.  The contract's
    /// claim is narrower and checkable: the features the round relies on.
    pub fn frozen_part(resolved: &[String], frozen: &[String]) -> (Vec<String>, Vec<String>) {
        let mut present = Vec::new();
        let mut missing = Vec::new();
        for feature in frozen {
            if resolved.iter().any(|candidate| candidate == feature) {
                present.push(feature.clone());
            } else {
                missing.push(feature.clone());
            }
        }
        (present, missing)
    }
}

impl FeatureReader for CargoMetadataFeatures {
    fn resolved_features(
        &self,
        workspace: &Path,
        _crate_name: &str,
    ) -> Result<ResolvedFeatures, AdapterError> {
        let metadata = self.metadata(workspace)?;
        let Some(resolved) = Self::resolved_bevy_features(&metadata) else {
            return Err(AdapterError::ContractViolation(
                "the `cargo metadata` document carries no resolved feature set for the `bevy` \
                 package (no `packages[].id` match in `resolve.nodes[].features`), so what the \
                 round actually compiled cannot be verified — a declared feature table is not \
                 what was built (B2-4)"
                    .to_string(),
            ));
        };
        let frozen = frozen_feature_list();
        let (present, missing) = Self::frozen_part(&resolved, &frozen);
        if !missing.is_empty() {
            return Err(AdapterError::ContractViolation(format!(
                "compared the resolved Bevy feature set ({resolved:?}) against the frozen feature \
                 set ({frozen:?}): the resolved graph does not carry {missing:?} — a feature-set \
                 drift is what turns a warm ~12 s build into ~236 s (DESIGN-DETAIL §5)"
            )));
        }
        let feature_sha256 = feature_hash_of(&present);
        if feature_sha256 != feature_set_sha256() {
            return Err(AdapterError::ContractViolation(format!(
                "compared the resolved frozen feature set {present:?} (hashed {feature_sha256}) \
                 against the frozen feature set (pinned {FEATURE_SET_SHA256})"
            )));
        }
        Ok(ResolvedFeatures {
            feature_sha256,
            features: present,
        })
    }
}

/// The real contract-path reader: the **game's own source**.
///
/// The PRD (C2) requires the game to declare its contract types with
/// `register_type`, and a crate cannot spell its own extern path for its own
/// types, so the reader matches the type **name** in `register_type::<…>` and
/// maps it to the frozen fully qualified path under
/// `hof_game::contract`.  The engine's own `Transform` is registered by Bevy,
/// not by the game, and is reported as present on that basis.
#[derive(Clone, Debug, Default)]
pub struct SourceContractPaths;

impl SourceContractPaths {
    /// Every `register_type::<…>` type name in one source text.
    pub fn registered_type_names(source: &str) -> Vec<String> {
        let mut names = Vec::new();
        let mut rest = source;
        while let Some(at) = rest.find("register_type::<") {
            let after = &rest[at + "register_type::<".len()..];
            if let Some(end) = after.find('>') {
                let argument = after[..end].trim();
                let name = argument.rsplit("::").next().unwrap_or(argument).trim();
                if !name.is_empty() {
                    names.push(name.to_string());
                }
            }
            rest = after;
        }
        names.sort();
        names.dedup();
        names
    }

    /// The frozen contract paths a source text declares.
    pub fn declared_paths_in(source: &str) -> Vec<String> {
        let names = Self::registered_type_names(source);
        let mut paths: Vec<String> = crate::adapter::bevy::contract::CONTRACT
            .iter()
            .filter(|entry| {
                entry.type_path != crate::adapter::bevy::contract::ENGINE_TRANSFORM_PATH
            })
            .filter(|entry| names.iter().any(|name| name == entry.type_name()))
            .map(|entry| entry.type_path.to_string())
            .collect();
        paths.push(crate::adapter::bevy::contract::ENGINE_TRANSFORM_PATH.to_string());
        paths.sort();
        paths.dedup();
        paths
    }

    /// Every `.rs` file under a workspace's `src/`, concatenated.
    fn game_source(workspace: &Path) -> Result<String, AdapterError> {
        let source_root = workspace.join("src");
        if !source_root.is_dir() {
            return Err(AdapterError::ContractViolation(format!(
                "`{}` does not exist, so the game's declared contract types cannot be read",
                source_root.display()
            )));
        }
        let mut text = String::new();
        let mut stack = vec![source_root.clone()];
        while let Some(directory) = stack.pop() {
            let entries = std::fs::read_dir(&directory).map_err(|error| {
                AdapterError::Malformed(format!(
                    "`{}` could not be read: {error}",
                    directory.display()
                ))
            })?;
            for entry in entries {
                let entry = entry.map_err(|error| {
                    AdapterError::Malformed(format!(
                        "an entry of `{}` could not be read: {error}",
                        directory.display()
                    ))
                })?;
                let path = entry.path();
                if path.is_dir() {
                    stack.push(path);
                } else if path.extension().and_then(|extension| extension.to_str()) == Some("rs") {
                    let file = std::fs::read_to_string(&path).map_err(|error| {
                        AdapterError::Malformed(format!(
                            "`{}` could not be read: {error}",
                            path.display()
                        ))
                    })?;
                    text.push_str(&file);
                    text.push('\n');
                }
            }
        }
        Ok(text)
    }
}

impl ContractPathReader for SourceContractPaths {
    fn declared_contract_paths(
        &self,
        workspace: &Path,
        _crate_name: &str,
    ) -> Result<Vec<String>, AdapterError> {
        let source = Self::game_source(workspace)?;
        Ok(Self::declared_paths_in(&source))
    }
}

impl SourceContractPaths {
    /// The frozen contract paths a workspace's own source declares, callable
    /// without importing the trait.  It is the same reader
    /// `BevyAdapter::prepare` uses, so a caller that asks "is this artifact
    /// usable?" cannot get a different answer from the one the build contract
    /// gives.
    pub fn declared_for(workspace: &Path, crate_name: &str) -> Result<Vec<String>, AdapterError> {
        <Self as ContractPathReader>::declared_contract_paths(&Self, workspace, crate_name)
    }
}

/// A contract-path reader that answers from a script.
#[derive(Clone, Debug, Default)]
pub struct FakeContractPaths {
    pub paths: Vec<String>,
}

impl FakeContractPaths {
    /// The frozen contract, so the contract check passes.
    pub fn frozen() -> Self {
        Self {
            paths: crate::adapter::bevy::contract::CONTRACT
                .iter()
                .map(|entry| entry.type_path.to_string())
                .collect(),
        }
    }

    /// The frozen contract without one path.
    pub fn missing(path: &str) -> Self {
        let mut paths = Self::frozen();
        paths.paths.retain(|candidate| candidate != path);
        paths
    }
}

impl ContractPathReader for FakeContractPaths {
    fn declared_contract_paths(
        &self,
        _workspace: &Path,
        _crate_name: &str,
    ) -> Result<Vec<String>, AdapterError> {
        Ok(self.paths.clone())
    }
}

/// A builder that answers from a script.  It exists so the budget, the overrun
/// and the "no binary" paths are exercised in the default gate, where there is
/// no engine, no game and no network.
#[derive(Clone)]
pub struct FakeBuilder {
    outcome: Result<BuildOutcome, String>,
    /// Every request the builder was given.
    pub requests: Arc<std::sync::Mutex<Vec<BuildRequest>>>,
}

impl std::fmt::Debug for FakeBuilder {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("FakeBuilder")
            .field("ok", &self.outcome.is_ok())
            .finish()
    }
}

impl FakeBuilder {
    pub fn succeeding(binary: impl Into<PathBuf>, elapsed_millis: u64) -> Self {
        Self {
            outcome: Ok(BuildOutcome {
                binary: binary.into(),
                elapsed_millis,
                cache_hit: elapsed_millis <= WARM_BUILD_BUDGET_MILLIS,
                exit_code: Some(0),
                output: "   Compiling hof_game v0.1.0\n".to_string(),
            }),
            requests: Arc::new(std::sync::Mutex::new(Vec::new())),
        }
    }

    pub fn failing(message: impl Into<String>) -> Self {
        Self {
            outcome: Err(message.into()),
            requests: Arc::new(std::sync::Mutex::new(Vec::new())),
        }
    }

    pub fn requests(&self) -> Vec<BuildRequest> {
        self.requests
            .lock()
            .map(|requests| requests.clone())
            .unwrap_or_default()
    }
}

impl Builder for FakeBuilder {
    fn build(&self, request: &BuildRequest) -> Result<BuildOutcome, AdapterError> {
        if let Ok(mut requests) = self.requests.lock() {
            requests.push(request.clone());
        }
        match &self.outcome {
            Ok(outcome) => Ok(outcome.clone()),
            Err(message) => Err(AdapterError::Malformed(message.clone())),
        }
    }
}

/// A feature reader that answers from a script.
#[derive(Clone, Debug, Default)]
pub struct FakeFeatures {
    pub feature_sha256: String,
    pub features: Vec<String>,
}

impl FakeFeatures {
    /// The frozen set, so `prepare()`'s feature check passes.
    pub fn frozen() -> Self {
        Self {
            feature_sha256: feature_hash_of(&frozen_feature_list()),
            features: frozen_feature_list(),
        }
    }

    /// A set whose hash has drifted, so the feature check has to refuse it.
    pub fn drifted() -> Self {
        Self {
            feature_sha256: "0".repeat(64),
            features: frozen_feature_list(),
        }
    }
}

impl FeatureReader for FakeFeatures {
    fn resolved_features(
        &self,
        _workspace: &Path,
        _crate_name: &str,
    ) -> Result<ResolvedFeatures, AdapterError> {
        Ok(ResolvedFeatures {
            feature_sha256: self.feature_sha256.clone(),
            features: self.features.clone(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_budgets_are_the_designs_numbers() {
        assert_eq!(COLD_BUILD_BUDGET_MILLIS, 600_000);
        assert_eq!(WARM_BUILD_BUDGET_MILLIS, 120_000);
        assert_eq!(ROUND_BUDGET_MILLIS, 300_000);
        assert_eq!(ENDPOINT_READY_BUDGET_MILLIS, 30_000);
        assert_eq!(BEVY_VERSION, "0.19.1");
    }

    #[test]
    fn a_warm_overrun_is_judged_against_the_warm_bound() {
        let budget = BuildBudget::default();
        assert_eq!(budget.exceeded(100_000, true), None);
        assert_eq!(budget.exceeded(100_000, false), None);
        assert_eq!(budget.exceeded(150_000, true), Some(120_000));
        assert_eq!(budget.exceeded(150_000, false), None);
        assert_eq!(budget.exceeded(700_000, false), Some(600_000));
    }

    #[test]
    fn the_feature_hash_is_pinned_and_moves_with_the_feature_set() {
        assert_eq!(feature_set_sha256(), FEATURE_SET_SHA256);
        let value = feature_set_value();
        assert_eq!(
            canonical(&value),
            r#"{"bevy":"0.19.1","default_features":true,"features":["bevy_remote"]}"#
        );
    }

    #[test]
    fn a_lockfile_drift_is_reported_verbatim() {
        let dir = tempfile::tempdir().unwrap();
        let lock = dir.path().join("Cargo.lock");
        std::fs::write(&lock, b"# locked\n").unwrap();
        let hash = lockfile_sha256(&lock).unwrap();
        assert!(lockfile_matches(&hash, &lock).is_ok());
        std::fs::write(&lock, b"# drifted\n").unwrap();
        let error = lockfile_matches(&hash, &lock).unwrap_err();
        assert!(error.to_string().contains("not comparable"), "{error}");
    }

    #[test]
    fn an_unreadable_lockfile_is_an_error_not_an_empty_hash() {
        let error = lockfile_sha256(Path::new("no-such-lockfile-anywhere.lock")).unwrap_err();
        assert!(error.to_string().contains("could not be read"), "{error}");
    }

    #[test]
    fn a_pinned_policy_carries_the_lockfile_it_measured() {
        let dir = tempfile::tempdir().unwrap();
        let lock = dir.path().join("Cargo.lock");
        std::fs::write(&lock, b"# locked\n").unwrap();
        let policy = BuildPolicy::pinned_to(dir.path(), Some(PathBuf::from("F:/shared"))).unwrap();
        assert_eq!(policy.lock_sha256, Some(lockfile_sha256(&lock).unwrap()));
        assert!(policy.is_locked());
        assert_eq!(policy.target_dir, Some(PathBuf::from("F:/shared")));
        assert!(policy.offline, "a round never builds with the network on");
        assert_eq!(policy.feature_sha256, FEATURE_SET_SHA256);
    }

    /// B2-1: an unpinned policy is an explicit state, not an empty string.  A
    /// workspace with no lockfile is explicitly unpinned; one with a lockfile is
    /// pinned by construction.
    #[test]
    fn a_policy_pins_the_lockfile_it_can_read_and_says_so_when_it_cannot() {
        let with_lock = tempfile::tempdir().expect("a temporary workspace");
        std::fs::write(with_lock.path().join("Cargo.lock"), b"# locked\n").expect("a lockfile");
        let pinned = BuildPolicy::pinned_if_available(with_lock.path(), None);
        assert!(pinned.is_locked());
        assert_eq!(
            pinned.lock_sha256,
            Some(lockfile_sha256(&with_lock.path().join("Cargo.lock")).unwrap())
        );

        let bare = tempfile::tempdir().expect("a temporary workspace");
        let unpinned = BuildPolicy::pinned_if_available(bare.path(), None);
        assert!(
            !unpinned.is_locked(),
            "there is no lockfile to pin, so the policy must say it is not pinned"
        );
        assert!(
            BuildPolicy::default().lock_sha256.is_none(),
            "the default policy never claims a pin it does not have"
        );
    }

    #[test]
    fn the_round_zero_policy_warms_the_graph_first_but_a_normal_round_does_not() {
        assert!(
            !BuildPolicy::default().warmup,
            "a normal round builds once; round 0 opts in"
        );
        assert!(BuildPolicy::default().with_warmup().warmup);
    }

    /// A program that sleeps far past any budget this test uses, and ignores its
    /// arguments (so it can stand in for `cargo`).
    fn a_sleeper_program(directory: &Path) -> PathBuf {
        if cfg!(windows) {
            let path = directory.join("sleeper.cmd");
            std::fs::write(&path, "@echo off\r\nping -n 30 127.0.0.1 >nul\r\n").expect("sleeper");
            path
        } else {
            let path = directory.join("sleeper.sh");
            std::fs::write(&path, "#!/bin/sh\nsleep 30\n").expect("sleeper");
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                let mut permissions = std::fs::metadata(&path).expect("metadata").permissions();
                permissions.set_mode(0o755);
                std::fs::set_permissions(&path, permissions).expect("executable bit");
            }
            path
        }
    }

    fn a_live_child() -> std::process::Child {
        let mut command = if cfg!(windows) {
            let mut command = Command::new("cmd.exe");
            command.args(["/C", "ping -n 30 127.0.0.1 >nul"]);
            command
        } else {
            let mut command = Command::new("/bin/sh");
            command.args(["-c", "sleep 30"]);
            command
        };
        command
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .expect("a live child process")
    }

    /// B2-5: the deadline is enforced **inside** the wait.  A build that hangs
    /// must be killed and reported as a budget fact, not block the round forever.
    #[test]
    fn a_build_that_outlives_its_budget_is_killed_and_reported() {
        let mut child = a_live_child();
        let started = Instant::now();
        let end = wait_with_timeout(&mut child, Duration::from_millis(400)).expect("a wait");
        assert!(
            matches!(end, ChildEnd::TimedOut { .. }),
            "a sleeping build must time out, got {end:?}"
        );
        assert!(
            started.elapsed() < Duration::from_secs(10),
            "the wait honoured its budget: {:?}",
            started.elapsed()
        );
        // It was reaped, not orphaned.
        assert!(
            child.try_wait().expect("a status").is_some(),
            "the killed child was waited for"
        );
    }

    /// B2-5, end to end: `CargoBuilder` reads `BuildRequest.timeout` instead of
    /// blocking in `wait_with_output`.
    #[test]
    fn the_cargo_builder_honours_the_requests_timeout() {
        let directory = tempfile::tempdir().expect("a temporary directory");
        let program = a_sleeper_program(directory.path());
        let request = BuildRequest {
            manifest: directory.path().join("Cargo.toml"),
            workspace: directory.path().to_path_buf(),
            target_dir: None,
            timeout: Duration::from_millis(500),
        };
        let started = Instant::now();
        let error = CargoBuilder::new()
            .with_program(program)
            .build(&request)
            .expect_err("a hung build is a budget failure");
        match error {
            AdapterError::BuildBudgetExceeded {
                budget_millis: 500, ..
            } => {}
            other => panic!("expected a budget failure, got {other:?}"),
        }
        assert!(
            started.elapsed() < Duration::from_secs(10),
            "the build did not block forever: {:?}",
            started.elapsed()
        );
    }

    #[test]
    fn the_fake_builder_records_the_request_it_was_given() {
        let builder = FakeBuilder::succeeding("F:/x/hof_game.exe", 12_000);
        let request = BuildRequest {
            manifest: PathBuf::from("F:/x/Cargo.toml"),
            workspace: PathBuf::from("F:/x"),
            target_dir: Some(PathBuf::from("F:/shared")),
            timeout: Duration::from_millis(600_000),
        };
        let outcome = builder.build(&request).unwrap();
        assert_eq!(outcome.binary, PathBuf::from("F:/x/hof_game.exe"));
        assert!(outcome.cache_hit);
        assert!(outcome.log_line().contains("warm"));
        assert_eq!(builder.requests(), vec![request]);
    }

    /// B2-4: the reader takes the **resolved** feature set
    /// (`resolve.nodes[].features`), not the declared table of Bevy's manifest.
    #[test]
    fn the_metadata_feature_reader_reads_the_resolved_set_not_the_declared_table() {
        let metadata = json!({
            "packages": [
                {"name": "hof_game", "id": "path+file:///g#hof_game@0.1.0", "features": {}},
                {"name": "bevy", "id": "registry+https://x#bevy@0.19.1",
                 "features": {"bevy_remote": [], "bevy_winit": []}},
            ],
            "resolve": {"nodes": [
                {"id": "path+file:///g#hof_game@0.1.0", "features": []},
                {"id": "registry+https://x#bevy@0.19.1",
                 "features": ["bevy_remote", "default", "bevy_asset", "bevy_remote"]},
            ]}
        });
        assert_eq!(
            CargoMetadataFeatures::bevy_package_id(&metadata).as_deref(),
            Some("registry+https://x#bevy@0.19.1")
        );
        assert_eq!(
            CargoMetadataFeatures::resolved_bevy_features(&metadata),
            Some(vec![
                "bevy_asset".to_string(),
                "bevy_remote".to_string(),
                "default".to_string()
            ]),
            "the resolved set is sorted, deduplicated and taken from `resolve.nodes`"
        );

        // The declared table says `bevy_remote` is available; the resolved graph
        // does not carry it.  The check must follow the resolved graph, or a game
        // that never enabled the feature would pass while the 236 s penalty was
        // real.
        let drifted = json!({
            "packages": [{"name": "bevy", "id": "b", "features": {"bevy_remote": []}}],
            "resolve": {"nodes": [{"id": "b", "features": ["default"]}]}
        });
        let resolved = CargoMetadataFeatures::resolved_bevy_features(&drifted).expect("resolved");
        let (_, missing) = CargoMetadataFeatures::frozen_part(&resolved, &frozen_feature_list());
        assert_eq!(missing, vec!["bevy_remote".to_string()]);

        // A document with no resolved section cannot answer the question at all:
        // a declared table is not a fallback.
        let declared_only = json!({ "packages": [{"name": "bevy", "id": "b", "features": {}}] });
        assert_eq!(
            CargoMetadataFeatures::resolved_bevy_features(&declared_only),
            None
        );
    }

    /// B2-1: the contract-path reader is about type paths, from the game's own
    /// source, and it is the only place feature names could have leaked into the
    /// contract check.
    #[test]
    fn the_source_contract_reader_reads_register_type_declarations() {
        let source = r#"
            use bevy::prelude::*;
            fn wire(app: &mut App) {
                app.register_type::<Player>();
                app.register_type::<contract::Grounded>();
                app.register_type::<hof_game::contract::CoinCounter>();
                app.register_type::<crate::contract::WinFlag>();
                app.register_type::<FrameCounter>();
                app.register_type::<InputIntent>();
            }
        "#;
        let paths = SourceContractPaths::declared_paths_in(source);
        for path in [
            "hof_game::contract::Player",
            "hof_game::contract::Grounded",
            "hof_game::contract::CoinCounter",
            "hof_game::contract::WinFlag",
            "hof_game::contract::FrameCounter",
            "hof_game::contract::InputIntent",
            "bevy_transform::components::transform::Transform",
        ] {
            assert!(paths.iter().any(|candidate| candidate == path), "{path}");
        }
        // A feature name is not a type path, and cannot sneak into the check.
        assert!(
            !paths.iter().any(|candidate| candidate == "bevy_remote"),
            "a feature name is not a contract path: {paths:?}"
        );

        let partial = SourceContractPaths::declared_paths_in("app.register_type::<Player>();");
        assert!(partial
            .iter()
            .any(|path| path == "hof_game::contract::Player"));
        assert!(
            !partial
                .iter()
                .any(|path| path == "hof_game::contract::Grounded"),
            "a missing declaration is not invented: {partial:?}"
        );
        assert_eq!(
            SourceContractPaths::registered_type_names(
                "a.register_type::<Player>(); b.register_type::<contract::Grounded>();"
            ),
            vec!["Grounded".to_string(), "Player".to_string()]
        );
    }

    #[test]
    fn the_resolved_feature_set_is_filtered_to_the_frozen_list() {
        // A real `cargo metadata` resolves hundreds of features; only the ones
        // the contract names may enter the hash, or the hash would be a statement
        // about Bevy's manifest instead of about this round's build.
        let resolved = vec![
            "bevy_remote".to_string(),
            "bevy_winit".to_string(),
            "png".to_string(),
        ];
        let (present, missing) =
            CargoMetadataFeatures::frozen_part(&resolved, &frozen_feature_list());
        assert_eq!(present, vec!["bevy_remote".to_string()]);
        assert!(missing.is_empty());
        assert_eq!(feature_hash_of(&present), FEATURE_SET_SHA256);
        let (_, missing) = CargoMetadataFeatures::frozen_part(&[], &frozen_feature_list());
        assert_eq!(missing, vec!["bevy_remote".to_string()]);
    }

    #[test]
    fn the_feature_hash_ignores_order_and_duplication() {
        let a = vec!["bevy_remote".to_string()];
        let b = vec!["bevy_remote".to_string(), "bevy_remote".to_string()];
        assert_eq!(feature_hash_of(&a), feature_hash_of(&b));
        // The frozen list hashes to the frozen document: that is what makes the
        // pin meaningful.
        assert_eq!(feature_hash_of(&a), FEATURE_SET_SHA256);
        assert_eq!(
            feature_hash_of(&frozen_feature_list()),
            feature_set_sha256()
        );
        // And a drift moves it, which is the whole point of the pin.
        let drifted = vec!["bevy_remote".to_string(), "bevy_winit".to_string()];
        assert_ne!(feature_hash_of(&drifted), FEATURE_SET_SHA256);
    }

    fn canonical(value: &serde_json::Value) -> String {
        crate::adapter::bevy::contract::canonical_json(value)
    }
}
