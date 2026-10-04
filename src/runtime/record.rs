//! Run and per-iteration record writing (§4.9).
//!
//! Every decision the runtime makes is materialized: a run that cannot be
//! audited is a bug, not an inconvenience.

use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::model::{Ablation, EvidenceDiff, Role, SchemaIssue, Spec, Usage};
use crate::runtime::schema::AttemptOutcome;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RunMeta {
    pub run_id: String,
    pub spec: Spec,
    pub ablation: Ablation,
    pub iterations: u32,
    pub model_identity: String,
    pub started_at: u64,
    pub hoh_version: String,
    pub warnings: Vec<String>,
    /// The model section exactly as it is passed to the harness.
    pub config: serde_json::Value,
    /// DR-21: how the workspace was prepared for this run.
    #[serde(default)]
    pub start_state: crate::runtime::start_state::StartState,
    /// DR-44: which engine binary produced this run's evidence.  The block has a
    /// fixed shape: an unknown value is `null` plus a reason, never omitted.
    #[serde(default)]
    pub engine: crate::adapter::EngineIdentity,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct IterResult {
    pub ok: bool,
    pub failed_role: Option<Role>,
    pub reason: String,
    pub issues: Vec<SchemaIssue>,
    pub warnings: Vec<String>,
    pub candidate_id: Option<String>,
    pub version_id: Option<String>,
    pub usage: Vec<Usage>,
    pub durations_ms: Vec<(String, u64)>,
    /// DR-2: present on every result (empty unless a contract violation was
    /// detected), so a failure always names the files that changed.
    pub evidence_diff: EvidenceDiff,
    /// DR-18: true when this iteration spent its one allowed wrap-up retry on a
    /// role that ended with `LimitsExceeded` before producing a valid artifact.
    #[serde(default)]
    pub wrap_up_retry_used: bool,
    /// DR-22: every role attempt of this iteration, with its exit status,
    /// duration, usage and artifact path.
    #[serde(default)]
    pub attempts: Vec<AttemptOutcome>,
    /// DR-19: how many files under `runs/<id>` had a known secret value
    /// replaced by `<redacted>`.  The value itself is never recorded.
    #[serde(default)]
    pub secret_redactions: u64,
    /// DR-24/DR-27: "can the frozen `A_t` start?", kept separate from `ok`
    /// ("did the loop complete?").
    #[serde(default)]
    pub artifact_gate: crate::model::ArtifactGate,
    /// DR-24: whether this iteration spent its one allowed targeted repair.
    #[serde(default)]
    pub repair_retry_used: bool,
    /// DR-24: the `ok` summary of every battery pass of this iteration.
    #[serde(default)]
    pub battery_passes: Vec<crate::model::BatteryPassSummary>,
    /// DR-25: files created/modified outside the project tree by a role.
    #[serde(default)]
    pub out_of_tree_writes: Vec<String>,
    /// DR-28: report-only artifact hygiene of the frozen `A_t`.
    #[serde(default)]
    pub artifact_hygiene: crate::model::ArtifactHygiene,
    /// DR-39: how much of the PRD this iteration's `E_t` accounts for.  Derived
    /// from the Tester's own claim lists; the runtime never judges a claim.
    #[serde(default)]
    pub prd_coverage: crate::model::PrdCoverage,
    /// DR-37: why the wrap-up retry was (not) triggered —
    /// `artifact_missing` | `not_triggered`.
    #[serde(default = "default_wrap_up_retry_reason")]
    pub wrap_up_retry_reason: String,
    /// Round-1 write-path batch: every role attempt that ended **without writing
    /// the artifact it declared**, as the harness's own fact rather than the
    /// external agent's exit status.  Empty on a round in which every role wrote
    /// what it was supposed to.
    #[serde(default)]
    pub write_failures: Vec<crate::runtime::write_failure::RoleWriteFailure>,
}

/// DR-37: the default is the honest one — the retry was not triggered.
pub fn default_wrap_up_retry_reason() -> String {
    WRAP_UP_NOT_TRIGGERED.to_string()
}

/// DR-37: the artifact really was missing/invalid when the retry was spent.
pub const WRAP_UP_ARTIFACT_MISSING: &str = "artifact_missing";
/// DR-37: no wrap-up retry was spent in this iteration.
pub const WRAP_UP_NOT_TRIGGERED: &str = "not_triggered";

impl IterResult {
    pub fn ok() -> Self {
        Self {
            ok: true,
            failed_role: None,
            reason: "ok".to_string(),
            issues: Vec::new(),
            warnings: Vec::new(),
            candidate_id: None,
            version_id: None,
            usage: Vec::new(),
            durations_ms: Vec::new(),
            evidence_diff: EvidenceDiff::default(),
            wrap_up_retry_used: false,
            attempts: Vec::new(),
            secret_redactions: 0,
            artifact_gate: crate::model::ArtifactGate::default(),
            repair_retry_used: false,
            battery_passes: Vec::new(),
            out_of_tree_writes: Vec::new(),
            artifact_hygiene: crate::model::ArtifactHygiene::default(),
            prd_coverage: crate::model::PrdCoverage::default(),
            wrap_up_retry_reason: default_wrap_up_retry_reason(),
            write_failures: Vec::new(),
        }
    }
}

fn write_json(path: &Path, value: &impl Serialize) -> anyhow::Result<()> {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let serialized = serde_json::to_string_pretty(value)?;
    crate::runtime::snapshot::write_atomic(path, serialized.as_bytes())
}

/// Write `runs/<id>/meta.json`.
///
/// DR-16: redaction happens at the sink, not at every call site, so a caller
/// that accidentally hands over a secret-bearing model section still cannot
/// persist it.
pub fn write_run_meta(run_dir: &Path, meta: &RunMeta) -> anyhow::Result<()> {
    let mut redacted = meta.clone();
    redacted.config = crate::config::redact_model_value(&meta.config);
    write_json(&run_dir.join("meta.json"), &redacted)
}

/// Write `runs/<id>/iter-<t>/result.json`.
pub fn write_iter_result(
    run_dir: &Path,
    iteration: u32,
    result: &IterResult,
) -> anyhow::Result<()> {
    write_json(
        &run_dir.join(format!("iter-{iteration}/result.json")),
        result,
    )
}

/// DR-22: the attempt-level detail written into `usage.json` alongside the
/// per-role summary.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AttemptUsage {
    pub role: String,
    pub iteration: u32,
    pub attempt: u32,
    pub exit_status: String,
    pub duration_ms: u64,
    pub artifact_path: String,
    pub artifact_valid: bool,
    pub calls: u64,
    pub prompt_tokens: Option<u64>,
    pub completion_tokens: Option<u64>,
    pub total_tokens: Option<u64>,
    pub cache_hit_tokens: Option<u64>,
    pub cache_miss_tokens: Option<u64>,
    pub usage_known: bool,
}

impl AttemptUsage {
    pub fn from_attempt(attempt: &AttemptOutcome) -> Self {
        let usage = &attempt.usage;
        Self {
            role: attempt.role.as_str().to_string(),
            iteration: attempt.iteration,
            attempt: attempt.attempt,
            exit_status: attempt.exit_status.clone(),
            duration_ms: attempt.duration_ms,
            artifact_path: attempt.artifact_path.to_string_lossy().into_owned(),
            artifact_valid: attempt.artifact_valid,
            calls: usage.calls,
            prompt_tokens: usage.prompt_tokens,
            completion_tokens: usage.completion_tokens,
            total_tokens: usage.total_tokens,
            cache_hit_tokens: usage.cache_hit_tokens,
            cache_miss_tokens: usage.cache_miss_tokens,
            usage_known: usage.usage_known,
        }
    }
}

/// Write `runs/<id>/iter-<t>/usage.json`.
///
/// DR-22: the per-role summary is preserved under `summary`, and the
/// attempt-level detail is added under `attempts`.
pub fn write_usage(
    run_dir: &Path,
    iteration: u32,
    summary: &[Usage],
    attempts: &[AttemptOutcome],
) -> anyhow::Result<()> {
    let value = serde_json::json!({
        "schema": 1,
        "summary": summary,
        "attempts": attempts.iter().map(AttemptUsage::from_attempt).collect::<Vec<_>>(),
    });
    write_json(
        &run_dir.join(format!("iter-{iteration}/usage.json")),
        &value,
    )
}

/// DR-22: write the symmetric log for every attempt of a role and annotate the
/// trajectory with the same facts.
///
/// The log and the trajectory both carry `exit_status`, `duration_ms`, `usage`
/// and `artifact_path`, so a single failed call can always be identified.
pub fn record_attempts(
    run_dir: &Path,
    iteration: u32,
    attempts: &[AttemptOutcome],
    note: Option<&str>,
) -> anyhow::Result<()> {
    for (index, attempt) in attempts.iter().enumerate() {
        let last = index + 1 == attempts.len();
        let enriched = enrich_trajectory(attempt).unwrap_or(false);
        let log = serde_json::json!({
            "role": attempt.role.as_str(),
            "iteration": attempt.iteration,
            "attempt": attempt.attempt,
            "exit_status": attempt.exit_status,
            "duration_ms": attempt.duration_ms,
            "usage": attempt.usage,
            "artifact_path": attempt.artifact_path.to_string_lossy(),
            "artifact_valid": attempt.artifact_valid,
            "exit_was_limits": attempt.exit_was_limits,
            "trajectory_enriched": enriched,
            // Only the final attempt of a batch carries the batch note (e.g.
            // "schema_failure after 3 attempts").
            "notes": if last { note.unwrap_or("") } else { "" },
        });
        let path = run_dir.join(format!(
            "iter-{iteration}/logs/{}.attempt{}.log",
            attempt.role.as_str(),
            attempt.attempt
        ));
        write_json(&path, &log)?;
    }
    Ok(())
}

/// Add the `hoh` block to a trajectory so it states the same facts as its log.
///
/// Best effort: a trajectory that is missing or not a JSON object is left
/// alone (the log still records `trajectory_enriched = false`), because an
/// enrichment failure must never mask the actual round outcome.
fn enrich_trajectory(attempt: &AttemptOutcome) -> anyhow::Result<bool> {
    let Ok(raw) = std::fs::read_to_string(&attempt.trajectory_path) else {
        return Ok(false);
    };
    let Ok(mut value) = serde_json::from_str::<serde_json::Value>(&raw) else {
        return Ok(false);
    };
    let Some(object) = value.as_object_mut() else {
        return Ok(false);
    };
    object.insert(
        "hoh".to_string(),
        serde_json::json!({
            "role": attempt.role.as_str(),
            "iteration": attempt.iteration,
            "attempt": attempt.attempt,
            "exit_status": attempt.exit_status,
            "duration_ms": attempt.duration_ms,
            "usage": attempt.usage,
            "artifact_path": attempt.artifact_path.to_string_lossy(),
            "artifact_valid": attempt.artifact_valid,
            "exit_was_limits": attempt.exit_was_limits,
        }),
    );
    write_atomic_shim(&attempt.trajectory_path, &value)?;
    Ok(true)
}

fn write_atomic_shim(path: &Path, value: &serde_json::Value) -> anyhow::Result<()> {
    crate::runtime::snapshot::write_atomic(path, serde_json::to_string_pretty(value)?.as_bytes())
}

/// Write `runs/<id>/iter-<t>/logs/<role>.log`.
pub fn write_log(run_dir: &Path, iteration: u32, role: &str, text: &str) -> anyhow::Result<()> {
    let path = run_dir.join(format!("iter-{iteration}/logs/{role}.log"));
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    std::fs::write(path, text.replace("\r\n", "\n"))?;
    Ok(())
}

/// DR-72 ② / DR-74 ⑥(D4): how many `iter-<n>` directories a run directory
/// currently has.
///
/// The redaction sweep seals every `iter-*/{candidate,traj}` it can see — it
/// deliberately does **not** seal `iter-*/planner-view`, because DR-19 requires a
/// role's own environment dump to be erased in place (see
/// `run_loop::frozen_evidence_roots`) — so it has to know the highest iteration
/// that exists rather than the configured iteration count (a failed first
/// iteration has no `iter-2`).
pub fn iteration_directories(run_dir: &Path) -> u32 {
    let mut highest = 0u32;
    let Ok(entries) = std::fs::read_dir(run_dir) else {
        return 0;
    };
    for entry in entries.flatten() {
        let name = entry.file_name();
        let name = name.to_string_lossy();
        if let Some(digits) = name.strip_prefix("iter-") {
            if let Ok(number) = digits.parse::<u32>() {
                highest = highest.max(number);
            }
        }
    }
    highest
}

/// Append a warning line to the run-level warning log (`warnings.log`).
pub fn append_warning(run_dir: &Path, warning: &str) -> anyhow::Result<()> {
    use std::io::Write;
    let path = run_dir.join("warnings.log");
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let mut file = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)?;
    writeln!(file, "{warning}")?;
    Ok(())
}
