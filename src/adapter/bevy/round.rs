//! One **real** round against a **real** Bevy process (DESIGN-DETAIL §6, §8.5).
//!
//! Everything in this module exists to turn the adapter's capability surface
//! into the two things a round needs:
//!
//! 1. the **deterministic evidence battery** (`ProjectAdapter::evidence_battery`):
//!    build the candidate, launch it headless, drive the five E3 observations
//!    through the semantic tools, stop it, and report one
//!    [`crate::adapter::BatteryRecord`] per step — including the two DR-24 gate
//!    steps the harness's `evaluate_launchable` reads;
//! 2. the **round evidence layout** of DESIGN-DETAIL §6, written under
//!    `<evidence root>/runs/bevy-<round>/` and nowhere else.
//!
//! The two honesty rules of `battery.rs` carry through here unchanged: a
//! criterion that could not be *measured* is a gap with a reason (never a
//! fabricated pass), and a task-level failure (the build did not run, the
//! endpoint never answered) is a red gate step with the verbatim reason — it is
//! never reported as "the game behaved".
//!
//! The step ids are the harness's own (`adapter::GATE_STEP_IDS`): the gate
//! classification is reused rather than reinvented, which is what DESIGN-DETAIL
//! §1 asks for.  `the_gate_step_ids_are_the_harnesss` pins the two literals
//! against that constant, so a rename cannot leave the Bevy battery declaring a
//! gate step nobody reads.

use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

use serde_json::{json, Value};

use crate::adapter::bevy::battery::{BatteryDriver, E3Observations};
use crate::adapter::bevy::brp;
use crate::adapter::bevy::build;
use crate::adapter::bevy::{BevyAdapter, LaunchFacts};
use crate::adapter::mcp::evidence::{
    self, CallEvidence, RoundEvidence, RoundHashes, BUILD_LOG_FILE, LAUNCH_FILE, META_FILE, QA_DIR,
    READINGS_DIR,
};
use crate::adapter::mcp::server::{BevyMcpServer, GameProcess, ToolError};
use crate::adapter::GameAdapter;
use crate::adapter::{
    BatteryRecord, FrameMark, InjectionReport, Intent, Project, Reading, SemanticKind,
};
use crate::model::{ExecKind, ExecRecord};

/// The DR-24 gate step that means "the candidate has no project-level defect".
/// It is `GATE_STEP_IDS[0]`, pinned by a test.
pub const BUILT_STEP_ID: &str = "editor_errors_baseline";
/// The DR-24 gate step that means "the candidate builds, boots, and answers".
/// It is `GATE_STEP_IDS[1]`, pinned by a test.
pub const READY_STEP_ID: &str = "play_scene_ready";
/// The nine E3 observation steps.  Each carries the PRD id it can produce
/// evidence for, so a Tester's claim has a skeleton to be checked against.
///
/// The last four are the **missing battery steps** round 1's Tester recorded as
/// gaps: `P1-left` (the negative direction), `P1-release` (writing `0` stops the
/// player), `P3-position` (a transform sample at the win frame) and `P5-gate` (a
/// ground-state payload that stands on its own).  The first five keep their ids
/// and their order, so nothing was renamed or removed to make room.
pub const E3_STEPS: &[(&str, &str, &str)] = &[
    ("e3_movement", "P1", "movement"),
    ("e3_coin_counter", "P2", "coins"),
    ("e3_win_flag", "P3", "win"),
    ("e3_jump_arc", "P4", "jump"),
    ("e3_grounded", "P5", "grounded"),
    ("e3_movement_left", "P1", "movement_left"),
    ("e3_movement_release", "P1", "movement_release"),
    ("e3_win_position", "P3", "win_position"),
    ("e3_grounded_payload", "P5", "grounded_payload"),
];

// ---------------------------------------------------------------------------
// The recording proxy over one game
// ---------------------------------------------------------------------------

/// The one place a semantic read/inject/wait is turned into a BRP call plus its
/// evidence record.  Both the `GameAdapter` methods on [`BevyAdapter`] and the
/// battery's driver go through these free functions, so a round and a unit test
/// cannot drift apart in what they send or what they keep.
pub fn read_recorded(
    server: &mut BevyMcpServer,
    evidence: &mut Vec<CallEvidence>,
    game_frame: &mut Option<u64>,
    kind: SemanticKind,
) -> anyhow::Result<Reading> {
    let (call, record) = server.call_with_evidence(kind.tool(), json!({}));
    evidence.push(record);
    match call.error {
        Some(error) => Ok(Reading::not_observed(
            kind,
            game_frame.unwrap_or(0),
            describe(&error),
        )),
        None => {
            let value = call.result.unwrap_or(Value::Null);
            let frame = value
                .get("frame")
                .and_then(Value::as_u64)
                .or(*game_frame)
                .unwrap_or(0);
            *game_frame = Some(frame);
            Ok(Reading::observed(kind, frame, value))
        }
    }
}

/// One injection, recorded.
pub fn inject_recorded(
    server: &mut BevyMcpServer,
    evidence: &mut Vec<CallEvidence>,
    game_frame: &mut Option<u64>,
    intent: &Intent,
    level: bool,
) -> anyhow::Result<InjectionReport> {
    let args = match intent {
        Intent::Move { dir } => json!({"dir": dir, "level": level}),
        Intent::Jump { press } => json!({"press": press}),
    };
    let (call, record) = server.call_with_evidence(intent.tool(), args);
    evidence.push(record);
    match call.error {
        Some(error) => Ok(InjectionReport::refused(
            game_frame.unwrap_or(0),
            describe(&error),
        )),
        None => {
            let frame = call
                .result
                .as_ref()
                .and_then(|value| value.get("frame"))
                .and_then(Value::as_u64)
                .or(*game_frame)
                .unwrap_or(0);
            *game_frame = Some(frame);
            Ok(InjectionReport::accepted(frame))
        }
    }
}

/// One frame-advance, recorded.  `bevy_wait_frames` is a task-level action: a
/// frame counter that never moves is an `Err`, not a reading.
pub fn wait_frames_recorded(
    server: &mut BevyMcpServer,
    evidence: &mut Vec<CallEvidence>,
    game_frame: &mut Option<u64>,
    n: u32,
) -> anyhow::Result<FrameMark> {
    let (call, record) = server.call_with_evidence("bevy_wait_frames", json!({"n": n}));
    evidence.push(record);
    match call.error {
        Some(error) => anyhow::bail!("{}", describe(&error)),
        None => {
            let frame = call
                .result
                .as_ref()
                .and_then(|value| value.get("frame_after"))
                .and_then(Value::as_u64)
                .or(*game_frame)
                .unwrap_or(0);
            *game_frame = Some(frame);
            Ok(FrameMark {
                requested: n,
                frame,
            })
        }
    }
}

/// A classified tool failure, verbatim: `kind (code N): message`.
pub fn describe(error: &ToolError) -> String {
    format!(
        "{} (code {}): {}",
        error.kind,
        error
            .code
            .map(|code| code.to_string())
            .unwrap_or_else(|| "none".to_string()),
        error.message
    )
}

/// One game process plus the MCP-over-BRP server that talks to it, with the
/// evidence window of a whole round.  It is what a real round observes through.
#[derive(Debug)]
pub struct Session {
    server: BevyMcpServer,
    evidence: Vec<CallEvidence>,
    game_frame: Option<u64>,
}

impl Session {
    pub fn new(endpoint: &str, timeout: Duration) -> Self {
        Self {
            server: BevyMcpServer::new(brp::BrpClient::new(endpoint, timeout)),
            evidence: Vec::new(),
            game_frame: None,
        }
    }

    /// Tell `bevy_health` which process it is reporting on.  A separate process
    /// (a role's `hoh tools call`) does not own the child, so it installs the
    /// pid the published route names and has no stderr of its own to offer —
    /// which it says rather than inventing an empty tail.
    pub fn install_process(&mut self, pid: u32, stderr_tail: String) {
        self.server
            .install_process(GameProcess { pid, stderr_tail });
    }

    /// The game's own frame, as last observed through the contract's counter.
    pub fn game_frame(&self) -> Option<u64> {
        self.game_frame
    }

    pub fn evidence(&self) -> &[CallEvidence] {
        &self.evidence
    }

    /// One tool call with its raw evidence record, **without** adding it to this
    /// session's battery evidence.  A role's `hoh tools call` keeps its own
    /// copies (`role-calls/`), so mixing them into the adapter's window would
    /// blur "the battery observed this" and "a role observed this".
    pub fn call_with_evidence(
        &mut self,
        tool: &str,
        args: Value,
    ) -> (crate::adapter::mcp::server::ToolCall, CallEvidence) {
        self.server.call_with_evidence(tool, args)
    }
}

impl BatteryDriver for Session {
    fn read(&mut self, kind: SemanticKind) -> anyhow::Result<Reading> {
        read_recorded(
            &mut self.server,
            &mut self.evidence,
            &mut self.game_frame,
            kind,
        )
    }

    fn inject(&mut self, intent: &Intent, level: bool) -> anyhow::Result<InjectionReport> {
        inject_recorded(
            &mut self.server,
            &mut self.evidence,
            &mut self.game_frame,
            intent,
            level,
        )
    }

    fn wait_frames(&mut self, n: u32) -> anyhow::Result<FrameMark> {
        wait_frames_recorded(
            &mut self.server,
            &mut self.evidence,
            &mut self.game_frame,
            n,
        )
    }

    fn take_evidence(&mut self) -> Vec<CallEvidence> {
        std::mem::take(&mut self.evidence)
    }
}

// ---------------------------------------------------------------------------
// The battery records
// ---------------------------------------------------------------------------

fn record(
    step_id: &str,
    supports: Vec<String>,
    kind: ExecKind,
    path: Option<String>,
    observation: String,
    ok: bool,
    raw_path: Option<String>,
) -> BatteryRecord {
    BatteryRecord {
        step_id: step_id.to_string(),
        supports,
        record: ExecRecord {
            kind,
            path,
            observation,
            candidate_id: String::new(),
        },
        ok,
        raw_path,
    }
}

/// The two gate steps plus the five E3 steps, shaped from one battery outcome.
///
/// Pure, so the "a gap with a reason is not a pass" property is testable in the
/// default gate without an engine: the caller hands in the observations and the
/// build/launch facts.
pub fn battery_records(
    build_ok: bool,
    build_observation: &str,
    ready_ok: bool,
    ready_observation: &str,
    observations: Option<&E3Observations>,
) -> Vec<BatteryRecord> {
    let mut records = vec![
        record(
            BUILT_STEP_ID,
            Vec::new(),
            ExecKind::Build,
            Some(format!(".hoh/deterministic/{BUILT_STEP_ID}.json")),
            build_observation.to_string(),
            build_ok,
            None,
        ),
        record(
            READY_STEP_ID,
            Vec::new(),
            ExecKind::RuntimeTrace,
            Some(format!(".hoh/deterministic/{READY_STEP_ID}.json")),
            ready_observation.to_string(),
            ready_ok,
            None,
        ),
    ];
    let Some(observations) = observations else {
        // No battery ran at all: every criterion is a gap, and saying so is the
        // only honest option (E6).
        for (step_id, prd, _) in E3_STEPS {
            records.push(record(
                step_id,
                vec![(*prd).to_string()],
                ExecKind::RuntimeTrace,
                None,
                "not observed: the battery did not run".to_string(),
                false,
                None,
            ));
        }
        return records;
    };
    let named = |name: &str| -> Option<&crate::adapter::bevy::battery::Observation> {
        observations.named(name)
    };
    for (step_id, prd, name) in E3_STEPS {
        let observation = named(name).expect("a named observation");
        let mut observation_text = if observation.observed {
            format!("{step_id}: observed")
        } else {
            format!(
                "{step_id}: {}",
                observation
                    .failure
                    .clone()
                    .unwrap_or_else(|| "not observed".to_string())
            )
        };
        // Round-5 repair (defect RA-8): a **definitional** step says so in the
        // record the round writes, not only in the observation it came from.  The
        // acceptance's point was that two of the nine steps add no discriminating
        // power; a reader of the round's own records must be able to see that
        // without reading the battery's internals.
        if let Some(reason) = observation.definitional_reason() {
            observation_text.push_str(" [definitional: ");
            observation_text.push_str(reason);
            observation_text.push(']');
        }
        records.push(record(
            step_id,
            vec![(*prd).to_string()],
            ExecKind::RuntimeTrace,
            None,
            observation_text,
            observation.observed,
            Some(format!("{READINGS_DIR}/e3-observations.json")),
        ));
    }
    records
}

// ---------------------------------------------------------------------------
// The round
// ---------------------------------------------------------------------------

/// Everything one round's battery produced, in the form the caller records.
pub struct RoundReport {
    pub records: Vec<BatteryRecord>,
    pub observations: Option<E3Observations>,
    pub gate: crate::model::ArtifactGate,
    pub hashes: Option<RoundHashes>,
    pub build_log: String,
    pub launch: Value,
    pub evidence_dir: Option<PathBuf>,
    pub build_millis: u64,
    pub ready_millis: u64,
    pub battery_millis: u64,
    /// The task-level failure that stopped the round before the battery ran, if
    /// any.  It is already reflected in `records`; it is kept here so a caller
    /// can propagate it if its own contract requires that.
    pub failure: Option<String>,
}

impl RoundReport {
    /// The gate verdict, evaluated from the records exactly as the runtime does.
    pub fn evaluate(records: &[BatteryRecord]) -> crate::model::ArtifactGate {
        crate::adapter::evaluate_launchable(records)
    }
}

/// The facts one round folds into its report, so the four exit paths share one
/// builder instead of four near-copies.
struct Facts {
    records: Vec<BatteryRecord>,
    observations: Option<E3Observations>,
    build_log: String,
    launch: Value,
    hashes: Option<RoundHashes>,
    build_millis: u64,
    ready_millis: u64,
    battery_millis: u64,
    failure: Option<String>,
}

impl Facts {
    fn red(reason: String, build_ok: bool) -> Self {
        let records = battery_records(build_ok, &reason, false, &reason, None);
        Self {
            records,
            observations: None,
            build_log: format!("{reason}\n"),
            launch: json!({"error": reason.clone()}),
            hashes: None,
            build_millis: 0,
            ready_millis: 0,
            battery_millis: 0,
            failure: Some(reason),
        }
    }
}

/// Build, launch, drive the five observations, stop, and write the evidence.
///
/// **Never returns `Err`.**  A build that does not compile, an endpoint that
/// never answers, a game that dies: each is folded into the records as a red
/// gate step with the verbatim reason, which is what lets the runtime run its
/// repair retry and then report the gate honestly instead of failing at a point
/// nothing else understands.
pub fn run(adapter: &mut BevyAdapter, workspace: &Path) -> RoundReport {
    let manifest = workspace.join("Cargo.toml");

    // ---- the candidate -----------------------------------------------------
    let prepared = match adapter.prepare(&Project::at(workspace.to_path_buf())) {
        Ok(prepared) => prepared,
        Err(error) => {
            let reason = format!(
                "the candidate could not be built as a Bevy project (`{}`): {error}",
                manifest.display()
            );
            return finish(adapter, Facts::red(reason, false));
        }
    };
    let build_millis = prepared.build_millis;
    let hashes = adapter.round_hashes().ok();
    let contract_paths = adapter.contract_paths().to_vec();
    let build_observation = format!(
        "the candidate built ({} ms, {} contract type path(s) declared: {}); frozen feature set {}",
        prepared.build_millis,
        contract_paths.len(),
        contract_paths.join(", "),
        build::FEATURE_SET_SHA256
    );

    // ---- the process -------------------------------------------------------
    let started = Instant::now();
    let game = match adapter.start(&prepared) {
        Ok(game) => game,
        Err(error) => {
            let reason = format!("the candidate built but could not be launched: {error}");
            let mut facts = Facts::red(reason, true);
            facts.build_log = adapter.build_log().to_string();
            facts.records = battery_records(
                true,
                &build_observation,
                false,
                &facts.failure.clone().unwrap_or_default(),
                None,
            );
            facts.hashes = hashes;
            facts.build_millis = build_millis;
            return finish(adapter, facts);
        }
    };
    let ready_millis = started.elapsed().as_millis() as u64;
    let pid = game.pid;
    let headless = game.headless;
    let endpoint = adapter.endpoint().to_string();
    // Which artifact produced these observations: the game binary's own digest —
    // and, since the round-2 repair, **which process actually answered**, which
    // is what `start` proved before it returned.  A `launch.json` that names
    // only the pid it hoped for is what let round 2 attribute two batteries to
    // the A0 scaffold without any file saying so.
    let binary = adapter.built_binary_identity();
    let launch_facts = adapter.last_launch().cloned();
    let mut launch_json = json!({
        "headless": headless,
        "endpoint": endpoint,
        "pid": pid,
        "ready_millis": ready_millis,
        "binary": binary,
        // Round-4 repair (the transport gap): a launch is a process boundary and
        // `start` rebuilds the observing client's connection pool at it.  This
        // counter is that rule's own witness in a real round's evidence: 0 would
        // mean the pass observed through a pool that outlived the process it was
        // opened to, which is the shape round 3's `G-transport` failure had.
        "client_generation": adapter.client_generation(),
    });
    // The authority witness: the process that answered, the nonce that proves
    // it, and the pids the ledger sweep reaped before the launch.
    if let Some(facts) = launch_facts.as_ref() {
        let identity = identity_fields(facts);
        launch_json["identity"] = json!({
            "scheme": "per-launch nonce published by the game as the contract's \
                       `ProcessNonce` resource and read back over BRP",
            "spawned_pid": facts.spawned_pid,
            "nonce": facts.nonce,
            "answered_nonce": facts.answered_nonce,
            "launch_image": facts.launch_image,
            "built_binary": facts.built_binary,
            "listening_pid": facts.listening_pid,
            "reaped_pids": facts.reaped_pids,
            "ledger": facts.ledger,
            "answering_pid": identity.answering_pid,
            "verified": identity.verified,
            "verified_rule": identity.verified_rule,
        });
    } else {
        launch_json["identity"] = json!({
            "verified": false,
            "reason": "the launch produced no identity facts, so no observation through this \
                       endpoint can be attributed to a process",
        });
    }

    // ---- the observations --------------------------------------------------
    let battery_started = Instant::now();
    let observations = adapter.run_battery().ok();
    let battery_millis = battery_started.elapsed().as_millis() as u64;
    let summary = observations
        .as_ref()
        .map(E3Observations::summary_line)
        .unwrap_or_else(|| "E3 ABORTED: the battery produced no observations".to_string());

    // ---- the stop ----------------------------------------------------------
    let stop = adapter.stop(game).ok();
    // Round-2 repair: "we asked it to stop" is not "it stopped".  A live game
    // that outlives this pass is the stale listener the *next* pass would
    // observe, so the death is verified here and a survivor is killed and, if it
    // still refuses to die, named in the record.
    launch_json["stop"] = match &stop {
        Some(report) => json!({
            "exit_code": report.exit_code,
            "stderr_tail": report.stderr_tail,
            "pid_dead": verified_dead(pid, STOP_DEATH_GRACE),
            "grace_millis": STOP_DEATH_GRACE.as_millis() as u64,
        }),
        None => json!({"error": "the game process could not be stopped"}),
    };
    launch_json["battery_millis"] = json!(battery_millis);

    let ready_ok = observations
        .as_ref()
        .map(|observations| observations.aborted.is_none())
        .unwrap_or(false);
    let ready_observation = format!(
        "the game answered on {endpoint} after {ready_millis} ms (pid {pid}, {}); {summary}",
        if headless { "headless" } else { "windowed" }
    );
    let records = battery_records(
        true,
        &build_observation,
        ready_ok,
        &ready_observation,
        observations.as_ref(),
    );
    finish(
        adapter,
        Facts {
            records,
            observations,
            build_log: adapter.build_log().to_string(),
            launch: launch_json,
            hashes,
            build_millis,
            ready_millis,
            battery_millis,
            failure: None,
        },
    )
}

/// Fold the round's facts into a report, the gate verdict included, and write
/// the evidence **before** the gate is handed out, so a red gate still leaves
/// the raw calls behind.
fn finish(adapter: &BevyAdapter, facts: Facts) -> RoundReport {
    let gate = RoundReport::evaluate(&facts.records);
    let calls: Vec<CallEvidence> = facts
        .observations
        .as_ref()
        .map(E3Observations::all_calls)
        .unwrap_or_default();
    let evidence_dir = if adapter.writes_evidence() {
        write_round_evidence(adapter, &facts, &gate, &calls)
    } else {
        None
    };
    RoundReport {
        records: facts.records,
        observations: facts.observations,
        gate,
        hashes: facts.hashes,
        build_log: facts.build_log,
        launch: facts.launch,
        evidence_dir,
        build_millis: facts.build_millis,
        ready_millis: facts.ready_millis,
        battery_millis: facts.battery_millis,
        failure: facts.failure,
    }
}

/// DESIGN-DETAIL §6: write the round's directory and nothing else.
fn write_round_evidence(
    adapter: &BevyAdapter,
    facts: &Facts,
    gate: &crate::model::ArtifactGate,
    calls: &[CallEvidence],
) -> Option<PathBuf> {
    let root = adapter.evidence_root();
    let round = adapter.round_name();
    let fallback = RoundHashes {
        contract_sha256: crate::adapter::bevy::contract::contract_sha256(),
        feature_sha256: build::feature_set_sha256(),
        lock_sha256: String::new(),
    };
    let hashes = facts.hashes.clone().unwrap_or(fallback);
    let mut evidence = RoundEvidence::new(round.clone(), hashes.clone());
    evidence.segments = json!({
        "build_millis": facts.build_millis,
        "ready_millis": facts.ready_millis,
        "battery_millis": facts.battery_millis,
        "headless": facts.launch.get("headless").cloned().unwrap_or(json!(true)),
        "endpoint": facts.launch.get("endpoint").cloned().unwrap_or(json!(brp::endpoint())),
        "pid": facts.launch.get("pid").cloned().unwrap_or(Value::Null),
        "exit_code_source": format!(
            "the harness runtime writes the round's exit code into runs/{round}/exit_code (its own \
             run directory); this battery runs before the round ends and cannot know it"
        ),
        "battery": facts
            .observations
            .as_ref()
            .map(E3Observations::summary_line)
            .unwrap_or_else(|| "E3 ABORTED: the battery produced no observations".to_string()),
        "failure": facts.failure.clone(),
    });
    evidence.build_log = facts.build_log.clone();
    evidence.launch = json!({
        "headless": facts.launch.get("headless").cloned().unwrap_or(json!(true)),
        "endpoint": facts.launch.get("endpoint").cloned().unwrap_or(json!(brp::endpoint())),
        "pid": facts.launch.get("pid").cloned().unwrap_or(Value::Null),
        "ready_millis": facts.ready_millis,
        "binary": facts.launch.get("binary").cloned().unwrap_or(Value::Null),
        "client_generation": facts.launch.get("client_generation").cloned().unwrap_or(Value::Null),
        "identity": facts.launch.get("identity").cloned().unwrap_or(Value::Null),
        "stop": facts.launch.get("stop").cloned().unwrap_or(Value::Null),
    });
    evidence.gate = serde_json::to_value(gate).ok();
    evidence.calls = calls.to_vec();
    // `readings/<surface>.json`, one file per semantic surface, plus the whole
    // observation set.  A reader can therefore check a single criterion without
    // replaying the battery.
    if let Some(observations) = facts.observations.as_ref() {
        evidence.readings.push((
            "e3-observations".to_string(),
            serde_json::to_value(observations).unwrap_or(Value::Null),
        ));
        for kind in SemanticKind::ALL {
            let readings: Vec<&Reading> = observations.readings_of(*kind);
            if readings.is_empty() {
                continue;
            }
            evidence.readings.push((
                kind.as_str().to_string(),
                serde_json::to_value(&readings).unwrap_or(Value::Null),
            ));
        }
    }
    let written = match evidence::write_round(&root, &evidence) {
        Ok(directory) => directory,
        Err(_) => return None,
    };
    // The QA material the Tester consumes, in the layout the design fixes.  It
    // points at the harness's own Tester artifacts rather than copying them: the
    // Tester's evidence belongs to the harness run, and a copy could silently
    // diverge from it.
    let qa = written.join(QA_DIR);
    let _ = std::fs::create_dir_all(&qa);
    let summary = facts
        .observations
        .as_ref()
        .map(E3Observations::summary_line)
        .unwrap_or_else(|| "E3 ABORTED: the battery produced no observations".to_string());
    let _ = std::fs::write(qa.join("e3-summary.txt"), format!("{summary}\n"));
    let gaps: Vec<Value> = facts
        .observations
        .as_ref()
        .map(|observations| {
            observations
                .gaps()
                .into_iter()
                .map(|(name, reason)| json!({"criterion": name, "reason": reason}))
                .collect()
        })
        .unwrap_or_default();
    let pointer = json!({
        "round": round,
        "evidence_directory": written.display().to_string(),
        "harness_run_directory": root.join("runs").join(&round).display().to_string(),
        "contract_sha256": hashes.contract_sha256,
        "feature_sha256": hashes.feature_sha256,
        "lock_sha256": hashes.lock_sha256,
        "gate": gate,
        "battery": summary,
        "gaps": gaps,
        "tester_material": "the harness writes the Tester's evidence.json and QA report under its \
                            own run directory (runs/<run-id>/iter-<n>/); this pointer names the \
                            round whose raw calls back those claims",
        "files": {
            "meta": META_FILE,
            "build_log": BUILD_LOG_FILE,
            "launch": LAUNCH_FILE,
            "step_ids": facts
                .records
                .iter()
                .map(|record| record.step_id.clone())
                .collect::<Vec<_>>(),
        },
    });
    let _ = std::fs::write(
        qa.join("pointer.json"),
        serde_json::to_string_pretty(&pointer).unwrap_or_default(),
    );
    Some(written)
}

/// A readiness poll for a game that a **role** announced (DR-78 ②), reused by the
/// adapter's publisher.
pub fn wait_for_endpoint(
    endpoint: &str,
    budget: Duration,
    interval: Duration,
) -> Result<u64, String> {
    let client = brp::BrpClient::new(endpoint.to_string(), Duration::from_secs(2));
    let started = Instant::now();
    let deadline = started + budget;
    loop {
        if client.discover().is_ok() {
            return Ok(started.elapsed().as_millis() as u64);
        }
        if Instant::now() >= deadline {
            return Err(format!(
                "the game did not answer on {endpoint} within {} ms",
                budget.as_millis()
            ));
        }
        std::thread::sleep(interval.min(deadline.saturating_duration_since(Instant::now())));
    }
}

/// `bevy_health` in a process that does not own the child: the pid is known (the
/// published route names it) but its stderr is not reachable, and that is what
/// the tail says.
pub const FOREIGN_PROCESS_STDERR: &str =
    "the game's stderr is not reachable from this process; it is recorded in the round's \
     launch.json by the process that started the game";

/// The two `identity` fields that used to be written as literals, computed from
/// the launch's own recorded facts.
///
/// `ROUND-3-REPORT.md` §1 flagged the pair: `verified` was the constant `true`
/// and `answering_pid` a **copy of** `spawned_pid`, so both were true whenever an
/// identity object existed and neither was independent evidence.
///
/// Round 4 computed them and left one gap, which `.spec/bevy/ACCEPTANCE-ROUNDS.md`
/// filed as RA-4: `verified` was `!nonce.is_empty()`, and every launch that
/// *returns* carries a nonce, so the field could not distinguish anything —
/// "computed in form, but true for every successful launch".  Round 5 makes it a
/// statement about **three recorded readings**, all of them in the same record:
///
/// 1. `facts.nonce` — the value generated before the spawn and passed only in
///    this child's environment;
/// 2. `facts.answered_nonce` — what the endpoint actually served back when
///    readiness read the contract's `ProcessNonce` (a reply serving anything else
///    is `LaunchError::IdentityMismatch`, so a returned launch carries this);
/// 3. `facts.listening_pid == facts.spawned_pid` — the OS's own TCP table naming
///    the process this launch started as the listener.
///
/// `verified` is true only when all three hold.  That makes it **false** for the
/// shapes a reader must be able to tell apart: a launch whose nonce never came
/// back, one whose read-back was a different value, one whose process the OS does
/// not name as the listener, and one where the TCP table could not be read at
/// all.  `answering_pid` stays "the OS reading, as read" so a disagreement is
/// visible rather than hidden.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct IdentityFields {
    /// The pid the OS TCP table named as the listener, as read.
    pub answering_pid: Option<u32>,
    /// Whether all three readings agree.
    pub verified: bool,
    /// The exact rule that produced `verified`, so a reader never has to infer it
    /// from the field's name.
    pub verified_rule: &'static str,
}

pub fn identity_fields(facts: &LaunchFacts) -> IdentityFields {
    let nonce_proved = !facts.nonce.trim().is_empty();
    let read_back_matches = facts
        .answered_nonce
        .as_deref()
        .map(|answered| !answered.trim().is_empty() && Some(answered) == Some(facts.nonce.as_str()))
        .unwrap_or(false);
    let os_names_the_spawned_process =
        facts.listening_pid.is_some() && facts.listening_pid == Some(facts.spawned_pid);
    IdentityFields {
        answering_pid: facts.listening_pid,
        verified: nonce_proved && read_back_matches && os_names_the_spawned_process,
        verified_rule: VERIFIED_RULE,
    }
}

/// What `identity.verified` means, written into the record so a reader does not
/// have to infer the rule from the field's name.
pub const VERIFIED_RULE: &str =
    "verified is true only when all three of this launch's own readings agree: (1) it carries a \
     non-empty per-launch nonce, generated before the spawn and passed only in the game's \
     environment; (2) `answered_nonce` is that same value, i.e. the endpoint served THIS nonce \
     back when readiness read the contract's `ProcessNonce` (a reply serving any other value is \
     refused and the launch fails, so a returned launch recorded what it read); and (3) \
     `listening_pid` equals `spawned_pid`, i.e. the OS's own TCP table names the process this \
     launch started as the listener on the endpoint. A launch whose read-back was not recorded, \
     whose read-back differed, whose process the OS does not name as the listener, or whose TCP \
     table could not be read, is verified false — and the fields that made it false stay in the \
     record. `answering_pid` is the OS reading as read (it can be absent, and it can disagree).";

/// The default timeout for the MCP server a round talks through.
pub const SESSION_TIMEOUT: Duration = Duration::from_secs(5);

/// Round-2 repair: how long a stopped game is given to actually die before it is
/// killed, and then before the death is declared unverified.
pub const STOP_DEATH_GRACE: Duration = Duration::from_secs(5);

/// Round-2 repair: verify that a stopped process is really gone, killing it and
/// re-verifying when it is not.
///
/// It answers one question with evidence: **is the pid dead?**  `stop_process`
/// already escalates to `kill`, but round 2 proved that a stop can be reported
/// while a game keeps answering the endpoint — three `hof_game.exe` processes
/// were alive after the round exited 0.  A survivor is therefore killed by pid
/// and, when it still survives, the answer is `false` with the reason, which is
/// what the round records.
pub fn verified_dead(pid: u32, grace: Duration) -> bool {
    if crate::adapter::bevy::launch::wait_for_pid_death(pid, grace) {
        return true;
    }
    let _ = crate::adapter::bevy::launch::kill_pid_and_verify(pid, grace);
    crate::adapter::bevy::launch::wait_for_pid_death(pid, grace)
}

/// The workspace-side evidence: `.hoh/deterministic/**`.
///
/// This is the half the **Tester** reads.  The Tester evaluates a *view of the
/// workspace*, so the round directory (`runs/bevy-<round>/`, which lives beside
/// the repository's other runs) is not in front of it: the adapter's contract
/// (`ProjectAdapter::evidence_battery`) is that every raw payload is written
/// under `<workspace>/.hoh/deterministic/raw/` and that one record per step is
/// returned with a `path` naming `.hoh/deterministic/<step>.json`.
///
/// ```text
/// .hoh/deterministic/battery.json          # every step: ok, observation, path
/// .hoh/deterministic/<step>.json           # that step's own record
/// .hoh/deterministic/raw/<step>.json       # the verbatim payloads behind it
/// .hoh/deterministic/mcp-errors.jsonl      # every failed call
/// ```
pub fn write_workspace_payloads(workspace: &Path, report: &RoundReport) -> std::io::Result<()> {
    let root = workspace.join(".hoh/deterministic");
    let raw = root.join("raw");
    std::fs::create_dir_all(&raw)?;

    let calls = report
        .observations
        .as_ref()
        .map(E3Observations::all_calls)
        .unwrap_or_default();

    let steps: Vec<Value> = report
        .records
        .iter()
        .map(|record| {
            json!({
                "step_id": record.step_id,
                "supports": record.supports,
                "ok": record.ok,
                "observation": record.record.observation,
                "path": record.record.path,
                "raw_path": record.raw_path,
            })
        })
        .collect();
    let battery = json!({
        "steps": steps,
        "build_millis": report.build_millis,
        "ready_millis": report.ready_millis,
        "battery_millis": report.battery_millis,
        "gate": report.gate,
        "hashes": report.hashes.as_ref().map(|hashes| json!({
            "contract_sha256": hashes.contract_sha256,
            "feature_sha256": hashes.feature_sha256,
            "lock_sha256": hashes.lock_sha256,
        })),
        "failure": report.failure,
        "note": "one entry per battery step; `ok = false` means the evidence is unavailable, not \
                 that the product failed — a step that is not observed is a `gap` for the Tester, \
                 never a `verified`",
    });
    std::fs::write(
        root.join("battery.json"),
        serde_json::to_string_pretty(&battery).unwrap_or_default(),
    )?;

    for record in &report.records {
        let payload = json!({
            "step_id": record.step_id,
            "supports": record.supports,
            "ok": record.ok,
            "observation": record.record.observation,
            "path": record.record.path,
            "raw_path": record.raw_path,
        });
        std::fs::write(
            root.join(format!("{}.json", record.step_id)),
            serde_json::to_string_pretty(&payload).unwrap_or_default(),
        )?;
    }

    // The verbatim payloads behind each criterion.  `raw/e3_*.json` holds the
    // observation *and* the raw MCP→BRP exchanges, because that is what a claim
    // citing it has to be checkable against.
    if let Some(observations) = report.observations.as_ref() {
        // Driven by `E3_STEPS` rather than a second hard-coded list: a criterion
        // that is in the battery but not here would be a step nobody can cite,
        // which is the round-1 gap this batch closes.
        let criteria = E3_STEPS.iter().map(|(step_id, _, name)| {
            (
                *step_id,
                observations
                    .named(name)
                    .expect("every E3 step names an observation the battery really holds"),
            )
        });
        for (name, observation) in criteria {
            let payload = json!({
                "criterion": name,
                "observed": observation.observed,
                "failure": observation.failure,
                "arc": observation.arc,
                "readings": observation.readings,
                "calls": observation.calls,
            });
            std::fs::write(
                raw.join(format!("{name}.json")),
                serde_json::to_string_pretty(&payload).unwrap_or_default(),
            )?;
        }
    }
    std::fs::write(
        raw.join("editor_errors_baseline.json"),
        serde_json::to_string_pretty(&json!({
            "build_millis": report.build_millis,
            "feature_sha256": build::feature_set_sha256(),
            "contract_sha256": crate::adapter::bevy::contract::contract_sha256(),
            "observation": report
                .records
                .iter()
                .find(|record| record.step_id == BUILT_STEP_ID)
                .map(|record| record.record.observation.clone())
                .unwrap_or_default(),
        }))
        .unwrap_or_default(),
    )?;
    std::fs::write(
        raw.join("play_scene_ready.json"),
        serde_json::to_string_pretty(&json!({
            "launch": report.launch,
            "ready_millis": report.ready_millis,
            "battery_millis": report.battery_millis,
            "observation": report
                .records
                .iter()
                .find(|record| record.step_id == READY_STEP_ID)
                .map(|record| record.record.observation.clone())
                .unwrap_or_default(),
        }))
        .unwrap_or_default(),
    )?;

    let failures: String = calls
        .iter()
        .filter(|call| call.error.is_some())
        .map(|call| {
            serde_json::to_string(&json!({
                "seq": call.seq,
                "tool": call.tool,
                "error": call.error,
            }))
            .unwrap_or_default()
        })
        .map(|line| format!("{line}\n"))
        .collect();
    std::fs::write(root.join("mcp-errors.jsonl"), failures)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::adapter::bevy::battery::{observation, JumpArc, Observation};

    #[test]
    fn the_gate_step_ids_are_the_harnesss() {
        assert_eq!(BUILT_STEP_ID, crate::adapter::GATE_STEP_IDS[0]);
        assert_eq!(READY_STEP_ID, crate::adapter::GATE_STEP_IDS[1]);
        assert_eq!(
            gate_step_ids(),
            ["editor_errors_baseline", "play_scene_ready"]
        );
    }

    fn gate_step_ids() -> [&'static str; 2] {
        [BUILT_STEP_ID, READY_STEP_ID]
    }

    /// Round-5 repair (defect RA-4): the identity fields are computed, and
    /// `verified` **discriminates** — it is false for every shape a reader has to
    /// be able to tell apart from the proved one, not merely for a hand-built
    /// empty nonce.  Each case below is a launch this harness can really have.
    #[test]
    fn the_identity_fields_are_computed_from_the_facts_not_asserted() {
        fn facts(nonce: &str, answered: Option<&str>, listening: Option<u32>) -> LaunchFacts {
            LaunchFacts {
                spawned_pid: 4242,
                nonce: nonce.to_string(),
                launch_image: "image".to_string(),
                built_binary: "built".to_string(),
                listening_pid: listening,
                answered_nonce: answered.map(str::to_string),
                ledger: None,
                reaped_pids: vec![17],
            }
        }
        // The proved case: the launch's nonce, that same nonce read back off the
        // wire, and the OS naming the spawned pid.
        let proved = identity_fields(&facts("5b1d0e2a", Some("5b1d0e2a"), Some(4242)));
        assert_eq!(proved.answering_pid, Some(4242));
        assert!(proved.verified, "all three readings agree: {proved:?}");
        assert!(
            proved.verified_rule.contains("all three"),
            "the record states the rule it applied: {}",
            proved.verified_rule
        );

        // The OS disagrees: recorded as read, and `verified` is false — that is
        // what makes `answering_pid == spawned_pid` a check rather than decoration.
        let disagreement = identity_fields(&facts("5b1d0e2a", Some("5b1d0e2a"), Some(17)));
        assert_eq!(
            disagreement.answering_pid,
            Some(17),
            "the OS reading is recorded **as read**: a disagreement is not hidden"
        );
        assert!(!disagreement.verified, "a different process listens here");

        // The TCP table could not be read: the record says None, and `verified`
        // is false rather than resting on the nonce alone.
        let unreadable = identity_fields(&facts("5b1d0e2a", Some("5b1d0e2a"), None));
        assert_eq!(unreadable.answering_pid, None);
        assert!(!unreadable.verified, "no OS reading, no verification");

        // The read-back was a different value (a stale session's nonce).
        let stale = identity_fields(&facts("5b1d0e2a", Some("the-previous-session"), Some(4242)));
        assert!(
            !stale.verified,
            "a reply serving another nonce is not this launch"
        );

        // The read-back was not recorded at all.
        let unrecorded = identity_fields(&facts("5b1d0e2a", None, Some(4242)));
        assert!(
            !unrecorded.verified,
            "a proof with no recorded read-back is not a recorded proof"
        );

        // No nonce, whatever else holds.
        for nonce in ["", "   "] {
            assert!(
                !identity_fields(&facts(nonce, Some("5b1d0e2a"), Some(4242))).verified,
                "with no nonce there is no proof of identity, whatever the OS says"
            );
        }
    }

    #[test]
    fn the_nine_e3_steps_name_the_prds_behaviours_and_keep_the_original_five() {
        // The four steps added for round 1's open gaps must not have displaced or
        // renamed any of the original five: their ids and their PRD mapping are
        // the skeleton the round-1 evidence is cited against.
        assert_eq!(
            &E3_STEPS[..5],
            &[
                ("e3_movement", "P1", "movement"),
                ("e3_coin_counter", "P2", "coins"),
                ("e3_win_flag", "P3", "win"),
                ("e3_jump_arc", "P4", "jump"),
                ("e3_grounded", "P5", "grounded"),
            ]
        );
        assert_eq!(E3_STEPS.len(), 9);
        let supports: Vec<&str> = E3_STEPS.iter().map(|(_, prd, _)| *prd).collect();
        assert_eq!(
            supports,
            vec!["P1", "P2", "P3", "P4", "P5", "P1", "P1", "P3", "P5"],
            "the four additions support P1/P1/P3/P5 and add no new PRD id"
        );
        // Every declared step names an observation the battery really holds, so
        // `write_workspace_payloads` can never be asked for a payload that does
        // not exist.
        for (step_id, _, name) in E3_STEPS {
            assert!(
                crate::adapter::bevy::battery::NAMED_OBSERVATIONS
                    .iter()
                    .any(|(candidate, _)| candidate == name),
                "`{step_id}` names `{name}`, which is not one of the battery's observations"
            );
        }
    }

    #[test]
    fn a_failed_build_closes_the_gate_and_still_names_every_criterion() {
        let records = battery_records(
            false,
            "the candidate could not be built",
            false,
            "the candidate could not be built",
            None,
        );
        let gate = RoundReport::evaluate(&records);
        assert!(gate.applicable && !gate.launchable, "{gate:?}");
        assert_eq!(records.len(), 11, "two gate steps + nine criteria");
        for record in &records {
            assert!(!record.ok, "{} must be red", record.step_id);
        }
        assert!(records[0].record.observation.contains("could not be built"));
        assert!(records[1].record.observation.contains("could not be built"));
        assert!(records[10].record.observation.contains("did not run"));
    }

    /// A criterion that was **measured false** is a red step; a criterion that
    /// was never observed is a red step with the gap's own reason.  Neither is a
    /// pass, and the two reasons are different strings.
    #[test]
    fn a_gap_and_a_measured_failure_are_both_red_but_say_different_things() {
        let mut observations = E3Observations {
            movement: Observation::not_observed("no player entity", Vec::new()),
            coins: observation(
                false,
                Some("the coin counter never rose above 0 (last reading 0)".to_string()),
                Vec::new(),
                None,
                Vec::new(),
            ),
            win: observation(true, None, Vec::new(), None, Vec::new()),
            jump: observation(
                false,
                Some(
                    "the arc never rises (rise=0, fall=4): a monotone fall is not a jump"
                        .to_string(),
                ),
                Vec::new(),
                Some(JumpArc {
                    peak: -200.0,
                    first: -100.0,
                    rising: 0,
                    falling: 4,
                    samples: Vec::new(),
                }),
                Vec::new(),
            ),
            grounded: observation(true, None, Vec::new(), None, Vec::new()),
            movement_left: observation(
                false,
                Some(
                    "injecting `move_dir = -1` changed `x` by 8 (from 0 to 8), which is not \
                     leftward motion"
                        .to_string(),
                ),
                Vec::new(),
                None,
                Vec::new(),
            ),
            movement_release: observation(true, None, Vec::new(), None, Vec::new()),
            win_position: observation(true, None, Vec::new(), None, Vec::new()),
            grounded_payload: observation(true, None, Vec::new(), None, Vec::new()),
            aborted: None,
        };
        let records = battery_records(
            true,
            "built",
            true,
            "the game answered and the battery ran",
            Some(&observations),
        );
        let by_id = |id: &str| records.iter().find(|record| record.step_id == id).unwrap();
        assert!(by_id(BUILT_STEP_ID).ok);
        assert!(by_id(READY_STEP_ID).ok, "the process was observable");
        assert!(!by_id("e3_movement").ok);
        assert!(by_id("e3_movement")
            .record
            .observation
            .contains("not observed"));
        assert!(!by_id("e3_coin_counter").ok);
        assert!(!by_id("e3_coin_counter")
            .record
            .observation
            .contains("not observed"));
        assert!(by_id("e3_win_flag").ok);
        assert!(!by_id("e3_jump_arc").ok);
        assert!(by_id("e3_jump_arc")
            .record
            .observation
            .contains("monotone fall"));
        assert!(by_id("e3_grounded").ok);
        // The four round-1 gaps are their own steps, and a measured failure is a
        // red step with the measured reason — never a pass and never a gap.
        assert!(!by_id("e3_movement_left").ok);
        assert!(by_id("e3_movement_left")
            .record
            .observation
            .contains("leftward motion"));
        assert!(!by_id("e3_movement_left")
            .record
            .observation
            .contains("not observed"));
        assert!(by_id("e3_movement_release").ok);
        assert!(by_id("e3_win_position").ok);
        assert!(by_id("e3_grounded_payload").ok);
        // The gate is about the artifact, not the criteria: a game that boots but
        // does not behave is `launchable` and its observations are red.
        assert!(RoundReport::evaluate(&records).launchable);
        observations.aborted = Some("the game process died".to_string());
        let aborted = battery_records(true, "built", false, "died", Some(&observations));
        assert!(!RoundReport::evaluate(&aborted).launchable);
    }

    /// Round-5 repair (defect RA-8): the two definitional steps say so **in the
    /// round's own record**, so a reader counting behavioural proofs is not misled
    /// by two steps that any in-order run satisfies.
    #[test]
    fn the_definitional_battery_steps_say_so_in_the_rounds_record() {
        // The same shape the battery builds: every step starts "not observed",
        // and the two definitional ones carry the label.
        let blank = || {
            crate::adapter::bevy::battery::Observation::not_observed(
                "the battery has not run",
                Vec::new(),
            )
        };
        let mut observations = E3Observations {
            movement: blank(),
            coins: blank(),
            win: blank(),
            jump: blank(),
            grounded: blank(),
            movement_left: blank(),
            movement_release: blank(),
            win_position: blank(),
            grounded_payload: blank(),
            aborted: None,
        };
        observations.coins = observation(true, None, Vec::new(), None, Vec::new());
        observations.win_position = crate::adapter::bevy::battery::Observation {
            definitional: true,
            definitional_note: Some("definitional: satisfied by any in-order read".to_string()),
            ..observation(true, None, Vec::new(), None, Vec::new())
        };
        let records = battery_records(
            true,
            "built",
            true,
            "the game answered and the battery ran",
            Some(&observations),
        );
        let by_id = |id: &str| records.iter().find(|record| record.step_id == id).unwrap();
        let win_position = &by_id("e3_win_position").record.observation;
        assert!(
            win_position.contains("[definitional: "),
            "a definitional step must be labelled in the record the round writes: {win_position}"
        );
        assert!(
            win_position.contains("any in-order read"),
            "and the label must carry the reason: {win_position}"
        );
        // The control: a non-definitional step is not labelled.
        let coins = &by_id("e3_coin_counter").record.observation;
        assert!(
            !coins.contains("[definitional: "),
            "only the definitional steps carry the label: {coins}"
        );
    }

    #[test]
    fn the_session_is_a_battery_driver_and_says_not_observed_on_a_dead_endpoint() {
        // No endpoint: every call fails, and the driver must say "not observed"
        // rather than invent a value.  This is the path a real round takes when
        // the game dies mid-battery.
        let mut session = Session::new(&refused_endpoint(), Duration::from_millis(120));
        let reading = session.read(SemanticKind::CoinCounter).unwrap();
        assert!(reading.failed, "a dead endpoint is not a coin reading");
        assert_eq!(reading.value, Value::Null);
        assert_eq!(session.game_frame(), None);
        assert_eq!(session.evidence().len(), 1);
        assert!(session.evidence()[0].error.is_some());
    }

    /// A port nothing listens on, derived rather than hard-coded.
    fn refused_endpoint() -> String {
        format!("http://127.0.0.1:{}/", brp::fake::refused_port())
    }
}
