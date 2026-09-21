//! Run and per-iteration record writing (§4.9).
//!
//! Every decision the runtime makes is materialized: a run that cannot be
//! audited is a bug, not an inconvenience.

use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::model::{Ablation, EvidenceDiff, Role, SchemaIssue, Spec, Usage};

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
}

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

/// Write `runs/<id>/iter-<t>/usage.json`.
pub fn write_usage(run_dir: &Path, iteration: u32, usage: &[Usage]) -> anyhow::Result<()> {
    write_json(
        &run_dir.join(format!("iter-{iteration}/usage.json")),
        &usage,
    )
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
