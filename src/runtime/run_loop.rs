//! The Orchestrator: the deterministic main loop (§4.4, §4.10, DR-1).
//!
//! Per iteration: planner (read-only) → developer (single writer) →
//! deterministic build/exec on the **real workspace** → freeze `A_t` (hash +
//! snapshot) → candidate copy → tester (frozen candidate) → record.
//!
//! Every stage boundary is a hash assertion, because a copy can always be
//! escaped with an absolute path; every violation also carries a concrete
//! file-level difference list (DR-2).

use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::{Instant, SystemTime, UNIX_EPOCH};

use crate::adapter::ProjectAdapter;
use crate::config::HohConfig;
use crate::errors::{as_hof_error, exit_code_of, HofError};
use crate::harness::Harness;
use crate::model::{
    empty_evidence, parse_plan, Ablation, ContractViolation, DevelopmentDoc, EvidenceDiff, Role,
    SchemaIssue, Spec, Usage,
};
use crate::prompts;
use crate::runtime::evidence::write_evidence;
use crate::runtime::integrity::IntegrityFinding;
use crate::runtime::invoke::{
    attempt_trajectory, invoke_once, is_limits_exceeded, render_prompt_with_budget_and_shell,
    role_env, wrap_up_context,
};
use crate::runtime::policy::{
    assert_unchanged, cache_manifest, cache_prefixes, diff_manifests, hash_tree, tree_manifest,
    HashExcludes,
};
use crate::runtime::record::{
    append_warning, record_attempts, write_iter_result, write_run_meta, write_usage, IterResult,
    RunMeta,
};
use crate::runtime::role::RoleInvocation;
use crate::runtime::schema::{gate_evidence_traced, gate_plan_traced, AttemptOutcome};
use crate::runtime::snapshot::VersionStore;
use crate::runtime::usage::{merge_usage, usage_from_attempts};
use crate::runtime::view::{build_view, copy_tree, write_inputs, ViewSpec};
use crate::tools::ToolChannel;

/// DR-18: the wrap-up retry never gets more than this many steps, whatever
/// `agent.wrap_up_steps` says.
pub const WRAP_UP_RETRY_MAX_STEPS: u64 = 30;

/// DR-66 ④: the step by which the Developer must already have produced at
/// least one engineering write.
///
/// The number is derived from the budget the runtime already imposes, not
/// invented: a quarter of the call is the band in which the measured
/// `smoke-t7` Developer had still produced nothing while spending its steps on
/// shell dialect errors - and from `wrap_up_steps` on, the Developer's own
/// prompt already orders it to stop exploring and write.  The deadline is
/// therefore "well before wrap-up begins", the earliest schedule on which a
/// real increment still leaves room to validate it.  It is capped at
/// `wrap_up_steps` so the instruction can never contradict the wrap-up rule.
///
/// DR-67 (DEF-5): this value is an **instruction published to the Developer**,
/// and it is the *only* thing it is.  It is rendered into the prompt
/// (`[budget]`) and into the `no_engineering_write` warning text; the runtime
/// does **not** compare it against a step counter, and no message may claim it
/// does.  Turning it into a hard step gate would need its own measurement (an
/// agent that legitimately starts writing at step 26 would be failed by a
/// literal counter), which is why the reviewer's option "make the wording
/// factual" was chosen over "check K".
pub fn developer_write_deadline(limits: &crate::config::AgentLimits) -> u64 {
    (limits.step_limit / 4).min(limits.wrap_up_steps).max(1)
}

/// The D7 scope limitation is recorded, never hidden.
pub const MCP_SCOPE_WARNING: &str =
    "qa_scope: MCP acts on the project open in the editor (the real workspace) while the Tester \
     evaluates a frozen copy; the runtime binds both to one candidate identity with pre-QA and \
     around-QA hash assertions (D7).";

/// DR-59/DR-61: the round started over the previous round's evidence and moved
/// it out of every role's working directory before any role ran.
pub const PREVIOUS_EVIDENCE_QUARANTINED: &str = "previous_evidence_quarantined";

pub struct Orchestrator {
    pub harness: Box<dyn Harness>,
    pub adapter: Box<dyn ProjectAdapter>,
    pub tools: Arc<dyn ToolChannel>,
    pub cfg: HohConfig,
    pub ablation: Ablation,
    /// Whether `initialize` may replace an existing non-empty workspace.
    pub force_init: bool,
    /// DR-21: how the workspace was prepared before this run started.
    pub start_state: crate::runtime::start_state::StartState,
}

#[derive(Clone, Debug)]
pub struct RunSummary {
    pub run_id: String,
    pub iterations_completed: u32,
    pub final_version_id: Option<String>,
    pub total_usage: Usage,
    pub ok: bool,
    /// DR-27: the gate verdict of the last completed iteration.  `ok` answers
    /// "did the loop finish?"; this answers "is the artifact usable?".
    pub artifact_gate: crate::model::ArtifactGate,
    /// DR-39: how much of the PRD the last completed iteration's `E_t` accounts
    /// for.  A third, independent axis — `gate ok` is not "the product works".
    pub prd_coverage: crate::model::PrdCoverage,
    /// DR-67 (DEF-2): the exit code this run must be **finalised** with when the
    /// loop itself returned an error instead of a summary.
    ///
    /// The gap this closes: a failed round returns `Err`, so there is no
    /// `RunSummary` at all, and the only `finalize_run` call site (on the `Ok`
    /// path) was therefore unreachable for exactly the failures that matter.
    /// `runs/<id>/exit_code` and `meta.json.exit_code` were consequently never
    /// written for a failed round, and the one place that *could* have carried
    /// the verdict — the `!ok` branch of `run_exit_code_for` — was dead in
    /// production, because the only production `RunSummary` was built on the
    /// success exit with `ok: true` hard-coded.
    ///
    /// `None` means "no failure to carry"; the code is then derived from the
    /// artifact gate exactly as before (DR-27).  `Some(code)` is set by the
    /// dispatcher from the **real** `anyhow::Error`, so what is persisted is the
    /// same number `hoh::errors::exit_code_of` gives the process, and the
    /// `!ok` branch is reachable from production data rather than from a
    /// hand-built object in a test.
    pub failure_exit_code: Option<i32>,
}

/// DR-67 (DEF-2): the run summary for a round that **failed**.
///
/// Built from the real `anyhow::Error`, never from a test's hand-written object:
/// the exit code comes from [`exit_code_of`], the same function the process
/// entry point uses (`src/cli.rs::main_entry`), so the two persisted locations
/// (`runs/<id>/exit_code`, `meta.json.exit_code`) and the process exit code
/// cannot diverge.
///
/// `artifact_gate` is `not_applicable` because a round that failed before its
/// loop ended never produced a gate verdict; `finalize_run` stores it, and the
/// failure code in `failure_exit_code` is what decides the exit code.
pub fn failed_run_summary(run_id: &str, error: &anyhow::Error) -> RunSummary {
    RunSummary {
        run_id: run_id.to_string(),
        iterations_completed: 0,
        final_version_id: None,
        total_usage: Usage::default(),
        ok: false,
        artifact_gate: crate::model::ArtifactGate::not_applicable(
            "the round failed; no artifact gate was produced",
        ),
        prd_coverage: crate::model::PrdCoverage::default(),
        failure_exit_code: Some(exit_code_of(error)),
    }
}

fn now_seconds() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .unwrap_or(0)
}

fn spec_text(spec: &Spec) -> anyhow::Result<String> {
    std::fs::read_to_string(&spec.path)
        .map_err(|error| anyhow::anyhow!("could not read spec {}: {error}", spec.path.display()))
}

fn pretty(value: &impl serde::Serialize) -> String {
    let mut text = serde_json::to_string_pretty(value).unwrap_or_default();
    if !text.ends_with('\n') {
        text.push('\n');
    }
    text
}

/// `.hoh/evidence.json` for the Planner: `E_{t-1}`, or an explicit empty bundle
/// when there is no previous evidence or when the feedback ablation is on.
fn planner_evidence(run_dir: &Path, iteration: u32, ablation: &Ablation) -> anyhow::Result<String> {
    if iteration == 1 || !ablation.evidence_feedback {
        return Ok(pretty(&empty_evidence(iteration - 1)));
    }
    let path = run_dir.join(format!("iter-{}/evidence.json", iteration - 1));
    match std::fs::read_to_string(&path) {
        Ok(raw) => Ok(raw),
        Err(_) => Ok(pretty(&empty_evidence(iteration - 1))),
    }
}

/// `.hoh/EVIDENCE_HISTORY.md`: the verified/gap summary of the previous round.
fn evidence_history(run_dir: &Path, iteration: u32) -> String {
    if iteration == 1 {
        return "# Evidence history\n\nNo previous evidence: this is the first iteration.\n"
            .to_string();
    }
    let path = run_dir.join(format!("iter-{}/evidence.json", iteration - 1));
    let Ok(raw) = std::fs::read_to_string(&path) else {
        return "# Evidence history\n\nPrevious evidence is unavailable.\n".to_string();
    };
    let Ok(bundle) = serde_json::from_str::<crate::model::EvidenceBundle>(&raw) else {
        return "# Evidence history\n\nPrevious evidence could not be parsed.\n".to_string();
    };
    let mut text = format!(
        "# Evidence history (iteration {})\n\nQA status: {:?}\n\n## Previously verified\n",
        bundle.iteration, bundle.qa_status
    );
    for record in &bundle.verified_records {
        text.push_str(&format!("- [{}] {}\n", record.claim_id, record.claim));
    }
    text.push_str("\n## Open gaps\n");
    for record in &bundle.gap_records {
        text.push_str(&format!("- [{}] {}\n", record.claim_id, record.claim));
    }
    text.push_str("\n## Planner handoff\n");
    for item in &bundle.planner_handoff.update_targets {
        text.push_str(&format!("- update: {item}\n"));
    }
    for item in &bundle.planner_handoff.preservation_constraints {
        text.push_str(&format!("- preserve: {item}\n"));
    }
    text
}

/// DR-66 ①: the skills as delivered - the `{{HOH_*}}` placeholders are
/// resolved for the role's real shell, exactly like the prompts.  A skill that
/// spells a POSIX call into a cmd shell is the `smoke-t7` defect.
fn skill_inputs() -> Vec<(String, String)> {
    prompts::skill_documents(crate::runtime::shell::ShellFlavor::HOST)
        .into_iter()
        .map(|(name, content)| (format!(".hoh/skills/{name}"), content))
        .collect()
}

#[allow(clippy::too_many_arguments)]
fn finalize_failure(
    run_dir: &Path,
    iteration: u32,
    role: Role,
    reason: &str,
    issues: Vec<SchemaIssue>,
    warnings: Vec<String>,
    usage: Vec<Usage>,
    durations: Vec<(String, u64)>,
    evidence_diff: EvidenceDiff,
    wrap_up_retry_used: bool,
    attempts: Vec<AttemptOutcome>,
    secret_redactions: u64,
    out_of_tree_writes: Vec<String>,
    facts: FailureFacts,
) -> anyhow::Result<()> {
    write_usage(run_dir, iteration, &usage, &attempts)?;
    let result = IterResult {
        ok: false,
        failed_role: Some(role),
        reason: reason.to_string(),
        issues,
        warnings,
        candidate_id: facts.candidate_id,
        version_id: facts.version_id,
        usage,
        durations_ms: durations,
        evidence_diff,
        wrap_up_retry_used,
        // DR-37: a wrap-up retry is only ever spent because the artifact was
        // missing or invalid, so the reason follows from the flag.
        wrap_up_retry_reason: if wrap_up_retry_used {
            crate::runtime::record::WRAP_UP_ARTIFACT_MISSING.to_string()
        } else {
            crate::runtime::record::WRAP_UP_NOT_TRIGGERED.to_string()
        },
        attempts,
        secret_redactions,
        out_of_tree_writes,
        battery_passes: facts.battery_passes,
        // DR-86 ④: a gate that was really evaluated survives the failure that
        // came after it; only a round that never reached a gate keeps the
        // `not_applicable` stub, which is then truthful.
        artifact_gate: facts.artifact_gate.unwrap_or_else(|| {
            crate::model::ArtifactGate::not_applicable(
                "the round failed; no artifact gate was produced",
            )
        }),
        // Round-1 write-path batch: a role that ended without writing the
        // artifact it declared is a fact this runtime measured, so a failure
        // path records it exactly like the gate verdict above.
        write_failures: facts.write_failures,
        ..IterResult::ok()
    };
    write_iter_result(run_dir, iteration, &result)
}

/// DR-86 ②: the verbatim schema issues a rejected attempt was failed for, as the
/// lines a write-capable wrap-up retry can act on.
///
/// `smoke-t16`'s decisive corruption came from a wrap-up retry whose prompt was
/// the bare "write the artifact NOW" instruction.  The retry that followed it DID
/// receive the verbatim failure list — and could not fix it in budget either —
/// but the one whose write corrupted the artifact received nothing.  This helper
/// turns the runtime's own rejection into that list, and says so when there is
/// genuinely nothing to quote rather than pretending there is.
fn schema_diagnostics(error: &anyhow::Error) -> Vec<String> {
    if let Some(HofError::SchemaFailure { issues, .. }) = as_hof_error(error) {
        let lines: Vec<String> = issues
            .iter()
            .rev()
            .find(|attempt| !attempt.is_empty())
            .map(|attempt| crate::runtime::schema::issue_lines(attempt))
            .unwrap_or_default();
        if !lines.is_empty() {
            return lines;
        }
    }
    vec![error.to_string()]
}

/// DR-86 ①: record every delivered-fragment / foreign-escape finding in the
/// iteration's warnings and in the run's warning log, once per finding.
fn note_integrity_findings(
    run_dir: &Path,
    iteration: u32,
    warnings: &mut Vec<String>,
    findings: &[IntegrityFinding],
    when: &str,
) -> anyhow::Result<()> {
    for finding in findings {
        let line = finding.render();
        if warnings.iter().any(|existing| existing == &line) {
            continue;
        }
        warnings.push(line.clone());
        append_warning(
            run_dir,
            &format!("iteration {iteration}: {when}: DR-86 delivered-artifact integrity: {line}"),
        )?;
    }
    Ok(())
}

/// DR-68 ④: the facts a **failed** round really produced, when it failed after
/// they existed.
///
/// `smoke-t8` failed at the Tester's schema gate — i.e. after the battery had
/// run 11/11 and after `A_1` was frozen — yet `iter-1/result.json` persisted
/// `candidate_id: null`, `version_id: null` and `battery_passes: []`.  A reader
/// of that one file therefore concluded "nothing happened", which is false and
/// which breaks the reproducibility criterion on exactly the path that needs it.
///
/// The failure sites that run *before* the freeze (the Planner, the Developer's
/// zero-write gate) genuinely have none of these and pass
/// [`FailureFacts::default`]: there the stub is truthful, not lazy.
#[derive(Clone, Debug, Default)]
pub struct FailureFacts {
    /// `A_t`'s content hash, once it exists.
    pub candidate_id: Option<String>,
    /// The snapshot store's id for that same artifact.
    pub version_id: Option<String>,
    /// Every battery pass the round ran, with its per-step verdicts.
    pub battery_passes: Vec<crate::model::BatteryPassSummary>,
    /// DR-86 ④: the artifact gate verdict the round had already produced.
    ///
    /// `smoke-t16`'s first round failed **after** the battery with
    /// `reason=contract_violation` (the Tester wrote into the frozen candidate
    /// view), and its `result.json` carries
    /// `artifact_gate={"applicable":false,...}` — the gate verdict existed and was
    /// thrown away by the failure path, so the round ended with a contract
    /// violation and no gate verdict at all.  A gate that was really evaluated is
    /// now persisted even when a later stage fails, because a verdict is evidence
    /// and evidence is never discarded.
    pub artifact_gate: Option<crate::model::ArtifactGate>,
    /// Round-1 write-path batch: the role attempts that ended without writing the
    /// artifact they declared, as the harness's own judgement.  Carried through
    /// the failure paths for the same reason the gate verdict is: it is a fact
    /// the runtime measured, so a failure may not erase it.
    pub write_failures: Vec<crate::runtime::write_failure::RoleWriteFailure>,
}

/// DR-26/DR-32/DR-38: report-only trace of a role reading the harness sources,
/// the harness repository root, or an external repository (all three are
/// forbidden by the prompts precisely because the tool schema is already in
/// `TOOLS.md`).  Behaviour never changes.
///
/// DR-32: only the trajectory's **tool calls** are scanned.  `smoke-t3` scanned
/// the whole trajectory text and therefore matched the system prompt's own list
/// of forbidden paths — a permanent false positive.
///
/// DR-38: the harness repository root is injected at runtime (`harness_root`),
/// never hard-coded, so `dir <repo root>` and `dir /b /s *.yaml | findstr hoh`
/// are traced as well.
fn note_source_reads(warnings: &mut Vec<String>, attempts: &[AttemptOutcome], harness_root: &Path) {
    if warnings
        .iter()
        .any(|warning| warning == "harness_source_read")
    {
        return;
    }
    for attempt in attempts {
        let Ok(raw) = std::fs::read_to_string(&attempt.trajectory_path) else {
            continue;
        };
        if crate::runtime::hygiene::mentions_forbidden_source_in_actions_with_root(
            &raw,
            Some(harness_root),
        ) {
            warnings.push("harness_source_read".to_string());
            return;
        }
    }
}

/// A manifest that could not be produced must not mask the violation itself.
fn manifest_or_empty(
    root: &Path,
    excludes: &[String],
) -> std::collections::BTreeMap<String, String> {
    tree_manifest(root, excludes).unwrap_or_default()
}

/// DR-72 ③: the engineering increment of one iteration is `A_{t-1} -> A_t`.
///
/// `evidence_diff` used to be populated **only** on a contract-violation path,
/// so a real round that changed 7 files still persisted
/// `{"added":[],"modified":[],"removed":[]}` and could not be told apart from an
/// honest "nothing changed" (the DR-68 R7 finding, `F-T10-3`).  This computes
/// the same projection the violation paths use, from the iteration's **starting**
/// manifest to the **frozen** artifact, and records it on the success path too.
///
/// The diff is of the *project tree* under the runtime's own exclusion rule, so
/// it is reproducible: a re-runner walks the frozen `versions/<version_id>/`
/// snapshot and its predecessor with the same excluding walk and gets the same
/// lists.
fn iteration_evidence_diff(
    before: &std::collections::BTreeMap<String, String>,
    root: &Path,
    excludes: &[String],
) -> EvidenceDiff {
    let after = manifest_or_empty(root, excludes);
    diff_manifests(before, &after)
}

/// DR-72 ②: the areas of a run directory that must never be rewritten in place.
///
/// D276: three rounds have now been damaged by "redact the evidence in place".
/// The frozen areas are exactly the ones a consumer parses or cites:
///
/// * `iter-*/candidate/**` — the frozen `A_t` view the Tester reads and cites;
/// * `versions/**` — the content-addressed snapshots;
/// * `iter-*/traj/**` — the role trajectories, which the runtime itself reads
///   back (usage extraction, attempt enrichment, source-read tracing) and which
///   `TASK-SMOKE-T10-ACCEPTANCE.md` names as E1's evidence form;
/// * `quarantine/**` — a previous round's bytes, kept for audit.
///
/// **`iter-*/planner-view/**` is deliberately not here.**  DR-19 still requires
/// the credential's *location* not to survive anywhere under `runs/<id>`, a role
/// can write an environment dump into its own view, and nothing parses a
/// planner-view file — so that is the one view where an in-place rewrite is both
/// necessary and harmless (`secret_isolation.rs`:
/// `a_leaked_secret_is_erased_and_counted` is the test that pins it).
fn frozen_evidence_roots(run_dir: &Path, iterations: u32) -> crate::runtime::secrets::SealedAreas {
    let mut roots = vec![run_dir.join("versions"), run_dir.join("quarantine")];
    for iteration in 1..=iterations {
        let iter_dir = run_dir.join(format!("iter-{iteration}"));
        roots.push(iter_dir.join("candidate"));
        roots.push(iter_dir.join("traj"));
    }
    crate::runtime::secrets::SealedAreas::new(roots)
}

/// DR-19/DR-72 ②: one redaction sweep over the run directory.
///
/// The frozen evidence areas are sealed, so this never rewrites a trajectory,
/// a frozen candidate or a snapshot in place; a hit inside a sealed area is
/// materialized as a generated `<name>.redacted.<ext>` copy next to the
/// original, which is left byte-for-byte unchanged.  A splice that would break a
/// JSON document is refused and reported as a warning instead of being written.
///
/// Returns the number of scrubbed files, i.e. the value DR-19's
/// `secret_redactions` has always reported.
fn redaction_sweep(
    run_dir: &Path,
    secrets: &[String],
    warnings: &mut Vec<String>,
) -> anyhow::Result<u64> {
    let iterations = crate::runtime::record::iteration_directories(run_dir);
    let sealed = frozen_evidence_roots(run_dir, iterations);
    let report = crate::runtime::secrets::redact_tree_traced(run_dir, secrets, &sealed)?;
    for (path, problem) in &report.refusals {
        let warning = format!(
            "{}: {}",
            path.strip_prefix(run_dir).unwrap_or(path).display(),
            problem
        );
        if !warnings.iter().any(|existing| existing == &warning) {
            warnings.push(warning.clone());
        }
    }
    for copy in &report.copies {
        let warning = format!(
            "frozen evidence kept in place; the redacted form was generated as {} (the original \
             is byte-unchanged, DR-72 ②)",
            copy.file_name()
                .map(|name| name.to_string_lossy().into_owned())
                .unwrap_or_else(|| crate::runtime::secrets::REDACTED_COPY_SUFFIX.to_string())
        );
        if !warnings.iter().any(|existing| existing == &warning) {
            warnings.push(warning);
        }
    }
    Ok(report.hits())
}

/// DR-69: how many files are under `root` (0 when it does not exist).
///
/// Used only to say *which* zero-increment shape a round produced: "the
/// Developer wrote, but only outside the project" and "the Developer wrote
/// nothing at all" are two different facts, and the artifact hash is silent
/// about both.
fn count_files(root: &Path) -> u64 {
    let mut count = 0u64;
    for entry in walkdir::WalkDir::new(root).follow_links(false) {
        if let Ok(entry) = entry {
            if entry.file_type().is_file() {
                count += 1;
            }
        }
    }
    count
}

/// Round-1 write-path batch: did the role leave a **non-empty** file at the path
/// its declared artifact lives at?
///
/// The measurement is the runtime's own, so a role's claim ("I wrote it") and an
/// external agent's exit status can neither create nor hide the fact.
fn wrote_non_empty(path: &Path) -> bool {
    std::fs::metadata(path)
        .map(|metadata| metadata.is_file() && metadata.len() > 0)
        .unwrap_or(false)
}

/// Round-1 write-path batch: record each write failure in the iteration's
/// warnings and in the run's warning log, once per failure.
fn note_write_failures(
    run_dir: &Path,
    iteration: u32,
    warnings: &mut Vec<String>,
    failures: &[crate::runtime::write_failure::RoleWriteFailure],
) -> anyhow::Result<()> {
    for failure in failures {
        let line = failure.render();
        if !warnings.iter().any(|existing| existing == &line) {
            warnings.push(line.clone());
        }
        append_warning(run_dir, &format!("iteration {iteration}: {line}"))?;
    }
    Ok(())
}

/// DR-69 ③: move an aborted attempt's evidence out of the way **before** its
/// directory is deleted ("save first, then clean").
///
/// `smoke-t9`' attempt A ended with `llm-connector chat request failed`, and the
/// only way to retry was to delete the round's own `runs/smoke-t9` directory —
/// which is how a 16.4 MB trajectory became unrecoverable.  The runtime has the
/// same shape one level down: a battery pass rebuilds `.hoh/deterministic` from
/// scratch (DR-24), so the first pass's raw payloads used to be destroyed the
/// moment a repair started a second pass.
///
/// The bytes are *moved*, never copied and never deleted: `preserved` names
/// where they went, and the caller may recreate the directory it needs.
pub fn preserve_then_clear(dir: &Path, preserve_root: &Path, label: &str) -> Option<PathBuf> {
    if !dir.exists() {
        return None;
    }
    let has_content = std::fs::read_dir(dir)
        .map(|entries| entries.into_iter().next().is_some())
        .unwrap_or(false);
    if !has_content {
        let _ = std::fs::remove_dir_all(dir);
        return None;
    }
    let target = preserve_root.join(format!("{label}.stale-{}", now_seconds()));
    if std::fs::create_dir_all(preserve_root).is_err() {
        return None;
    }
    match std::fs::rename(dir, &target) {
        Ok(()) => Some(target),
        Err(_) => {
            // A rename can fail across volumes; a recursive copy is the fallback
            // and it is still "save first, then clean".
            if copy_dir_recursive(dir, &target).is_err() {
                return None;
            }
            let _ = std::fs::remove_dir_all(dir);
            Some(target)
        }
    }
}

/// DR-69 ③: the fallback copy used when `rename` cannot move a directory.
fn copy_dir_recursive(from: &Path, to: &Path) -> std::io::Result<()> {
    std::fs::create_dir_all(to)?;
    for entry in std::fs::read_dir(from)? {
        let entry = entry?;
        let target = to.join(entry.file_name());
        if entry.file_type()?.is_dir() {
            copy_dir_recursive(&entry.path(), &target)?;
        } else {
            std::fs::copy(entry.path(), &target)?;
        }
    }
    Ok(())
}

/// DR-24: one battery pass.  The directory is rebuilt from scratch so a
/// second (post-repair) pass never leaves the first pass's raw payloads
/// behind to be mistaken for the frozen `A_t` evidence.
///
/// DR-69 ③: "rebuilt from scratch" used to mean "destroyed".  The aborted
/// pass's bytes are now preserved under `runs/<id>/quarantine/` **before** the
/// directory is cleared.
async fn run_battery_pass(
    workspace: &Path,
    run_dir: &Path,
    pass: u32,
    adapter: &dyn ProjectAdapter,
    tools: &dyn ToolChannel,
    engine: &crate::adapter::EngineIdentity,
) -> anyhow::Result<Vec<crate::adapter::BatteryRecord>> {
    let deterministic_dir = workspace.join(".hoh/deterministic");
    // The label names the pass whose evidence is being **replaced**, so the
    // preserved directory says which attempt those bytes belong to.
    let preserved = preserve_then_clear(
        &deterministic_dir,
        &run_dir.join("quarantine"),
        &format!("deterministic-pass-{}", pass.saturating_sub(1)),
    );
    if let Some(target) = preserved {
        append_warning(
            run_dir,
            &format!(
                "DR-69: battery pass {pass} replaced pass {}'s evidence; those bytes were \
                 preserved at {} (first saved, then cleared)",
                pass.saturating_sub(1),
                target.display()
            ),
        )?;
    }
    std::fs::create_dir_all(&deterministic_dir)?;
    let mut records = adapter.evidence_battery(workspace, tools).await?;
    // DR-44 ⑤: the engine identity is a **gate step**, so a round whose
    // evidence came from another binary than the configured one cannot freeze as
    // launchable.  It is appended only when the adapter drives an engine binary;
    // an adapter without one has no identity to check (and inventing a failing
    // step would fail every run of that adapter).
    if let Some(record) = crate::adapter::engine::gate_record(engine) {
        records.push(record);
    }
    Ok(records)
}

/// DR-24: the recorded `ok` summary of one battery pass.
fn battery_summary(
    pass: u32,
    battery: &[crate::adapter::BatteryRecord],
    gate: &crate::model::ArtifactGate,
) -> crate::model::BatteryPassSummary {
    crate::model::BatteryPassSummary {
        pass,
        launchable: gate.launchable,
        steps: battery
            .iter()
            .map(|record| (record.step_id.clone(), record.ok))
            .collect(),
    }
}

fn qa_report_fallback(bundle: &crate::model::EvidenceBundle) -> String {
    let mut text = format!(
        "# QA report (iteration {})\n\nQA status: {:?}\n\n## Verified\n",
        bundle.iteration, bundle.qa_status
    );
    for record in &bundle.verified_records {
        text.push_str(&format!("- [{}] {}\n", record.claim_id, record.claim));
    }
    text.push_str("\n## Gaps\n");
    for record in &bundle.gap_records {
        text.push_str(&format!(
            "- [{}] {} (impact: {}; next: {})\n",
            record.claim_id,
            record.claim,
            record.player_impact.as_deref().unwrap_or("-"),
            record.recommended_update.as_deref().unwrap_or("-")
        ));
    }
    text
}

/// DR-70 ①: start the round's game session, publishing the route with it.
///
/// A failure here is **not** fatal.  The battery's `play_scene_ready` step is
/// still the gate that decides whether the artifact is launchable, and a round
/// whose editor cannot start a game must record that honestly instead of failing
/// at a new, earlier point that nothing else understands.  What the failure must
/// not do is stay silent: `game_endpoint_unavailable` for every role of the round
/// is then the *expected* outcome, and the warning says so.
///
/// DR-71 ①: the failure must also leave **no route**.  The adapter is the one
/// that publishes, and an adapter that published before it confirmed readiness
/// (DR-70's shape, and still the order inside the battery) would otherwise hand
/// the first role a route the start could not confirm — the acceptance observed
/// exactly that (`Some(true)` inside the first role's window).  Withdrawing here
/// makes "start failed ⇒ no route" true for *every* adapter, including one whose
/// own failure path forgets: the channel drops the in-process route and the file
/// is removed (DR-43's explicit refusal stays what a role sees).
async fn start_round_game(orchestrator: &Orchestrator, workspace: &Path, run_dir: &Path) {
    match orchestrator
        .adapter
        .start_round_game(workspace, &*orchestrator.tools)
        .await
    {
        Ok(_) => {}
        Err(error) => {
            // Idempotent, and deliberately not conditional on what the adapter
            // managed to do before it failed.
            orchestrator.tools.clear_game_endpoint().await;
            crate::tools::endpoint::withdraw_game_route(&crate::tools::endpoint::game_route_path(
                run_dir,
            ));
            let _ = append_warning(
                run_dir,
                &format!(
                    "DR-70: the round's game session could not be started ({error}); the game \
                     route stays withdrawn until the battery starts its own game, so every \
                     `running_game_*` call from a role shell fails with \
                     `game_endpoint_unavailable` (DR-43) for this window"
                ),
            );
        }
    }
}

/// DR-70 ①: stop the round's game session and withdraw its published route.
async fn stop_round_game(orchestrator: &Orchestrator, run_dir: &Path) {
    if let Err(error) = orchestrator
        .adapter
        .stop_round_game(&*orchestrator.tools)
        .await
    {
        let _ = append_warning(
            run_dir,
            &format!("DR-70: stopping the round's game session failed: {error}"),
        );
    }
    // Belt and braces: the session must not outlive the window it was started
    // for, whatever the adapter managed (DR-70 ①, "withdraw on error paths too").
    crate::tools::endpoint::withdraw_game_route(&crate::tools::endpoint::game_route_path(run_dir));
}

/// Run the whole HoH loop.
///
/// DR-70 ①: the game route lives for the **whole round**.  `run_inner` starts the
/// round's game before the first role; this wrapper tears the session down on
/// every exit path — the summary, an `Err` from any stage, and the contract-gate
/// returns — so no role's window falls outside the publish window and no error
/// path leaves a route behind pointing at a stopped game.
pub async fn run(
    orchestrator: &Orchestrator,
    spec: &Spec,
    run_id: &str,
) -> anyhow::Result<RunSummary> {
    let outcome = run_inner(orchestrator, spec, run_id).await;
    let run_dir = orchestrator.cfg.runtime.runs_dir.join(run_id);
    stop_round_game(orchestrator, &run_dir).await;
    outcome
}

async fn run_inner(
    orchestrator: &Orchestrator,
    spec: &Spec,
    run_id: &str,
) -> anyhow::Result<RunSummary> {
    let cfg = &orchestrator.cfg;

    let run_dir = cfg.runtime.runs_dir.join(run_id);
    std::fs::create_dir_all(&run_dir)?;

    let workspace = cfg.runtime.workspace.clone();
    std::fs::create_dir_all(&workspace)?;
    // DR-70 ①/②: the run's route file is **not inherited**.  Whatever a previous
    // round — or a crash, or a deliberately reused `--run-id` — left at this
    // path is withdrawn before anything can adopt it, and only then is the
    // channel pointed at the path so every registration publishes there.  The
    // route then exists only for windows this round itself opened.
    let route_path = crate::tools::endpoint::game_route_path(&run_dir);
    crate::tools::endpoint::withdraw_game_route(&route_path);
    orchestrator.tools.use_game_route_file(route_path);
    orchestrator.adapter.initialize(&workspace)?;
    let _ = orchestrator.force_init; // the adapter decides what "already exists" means

    // DR-59/DR-61: a new round must not be able to read the previous round's
    // evidence — not through the prompt-named paths and not through a wildcard
    // walk of `.hoh` either.  `smoke-t7` proves the leak is real: that round
    // started with `smoke-t6`'s `.hoh/deterministic/**` still on disk, the
    // Developer read it, and `runs/smoke-t7/iter-1/traj/developer.attempt1.json`
    // `.messages[54]` carries the *previous* round's `pid 108432`, its "the editor
    // is not clean" verdict and its `os error 10061` transport failure into the
    // new round's model context.
    //
    // This runs before the `A_0` snapshot and before any role, so the live
    // evidence paths are empty for the whole round.  DR-61 moves every measured
    // previous-round area (`hygiene::QUARANTINE_AREAS`) to
    // `runs/<run_id>/quarantine/…` — **outside** the workspace, i.e. outside the
    // Developer's cwd and outside both view roots (`iter-<n>/{planner-view,candidate}`)
    // — under the DR-49 `.stale-<ts>` name, never deleted.  `.hoh` is excluded
    // from the artifact hash (DR-11), so the move cannot perturb `A_0`/`A_t`.
    let quarantined = crate::runtime::hygiene::quarantine_previous_evidence(&workspace, &run_dir)?;

    // DR-88 ④: the adapter's cache directories are outside the artifact
    // identity (R10 keeps `version_id` stable), which used to make a write
    // through one of them invisible to every reading here.  They are observed
    // separately instead of hashed: see the QA window below.
    let cache_watch = cache_prefixes(&orchestrator.adapter.cache_excludes());
    let excludes = HashExcludes::new(orchestrator.adapter.cache_excludes()).merged();
    let store = VersionStore::new(run_dir.join("versions"));
    // Round-1 write-path batch: the adapter's warm build cache, exported into
    // every role's environment so a role's `cargo build --offline` reuses it
    // instead of building a second full tree inside the project.
    let build_target_dir = orchestrator.adapter.build_target_dir();

    // DR-19: the values that must never survive anywhere under `runs/<id>`.
    let secrets = crate::runtime::secrets::known_secrets(cfg);

    let mut warnings = vec![MCP_SCOPE_WARNING.to_string()];
    if !quarantined.is_empty() {
        warnings.push(PREVIOUS_EVIDENCE_QUARANTINED.to_string());
        for area in &quarantined {
            append_warning(
                &run_dir,
                &format!(
                    "DR-61: moved the previous round's {} out of this round's read path to {}; \
                     no role's working directory can reach those bytes (they are kept, not \
                     deleted)",
                    area.live,
                    area.target.display()
                ),
            )?;
        }
    }
    // DR-44: which engine binary are we driving?  The probe runs through mini's
    // `Environment` abstraction (no new dependency), and it is skipped entirely
    // when the adapter drives no engine binary — an adapter without one has no
    // identity to check.
    let engine = crate::runtime::engine_identity::probe(
        orchestrator.adapter.as_ref(),
        &workspace,
        &cfg.tools.endpoint,
        None,
    )
    .await;
    let mut meta = RunMeta {
        run_id: run_id.to_string(),
        spec: spec.clone(),
        ablation: orchestrator.ablation,
        iterations: cfg.runtime.iterations,
        model_identity: cfg.model_identity(),
        started_at: now_seconds(),
        hoh_version: env!("CARGO_PKG_VERSION").to_string(),
        warnings: warnings.clone(),
        config: cfg.model.clone(),
        start_state: orchestrator.start_state.clone(),
        engine,
    };
    write_run_meta(&run_dir, &meta)?;
    append_warning(&run_dir, MCP_SCOPE_WARNING)?;

    // DR-26: the generated schema index is cached in the run directory.  Each
    // role view gets its own role-scoped `.hoh/TOOLS.md`; this copy records the
    // exact document the round was produced against.
    let tools_index = orchestrator.tools.index_markdown(Role::Developer);
    std::fs::write(
        run_dir.join("TOOLS.md"),
        format!(
            "# Generated tool schema cache (DR-26, developer scope)\n\n\
             A live `tools/list` wins; when the editor is offline the embedded schema snapshot \
             is used. Role views receive their own scoped copy at `.hoh/TOOLS.md`.\n\n{tools_index}"
        ),
    )?;

    // A0 is snapshotted before anything else so warm_start=false can restore it.
    let a0 = store.snapshot_role(&workspace, &excludes, 0, "init", "A0 initial artifact")?;

    let total_text = spec_text(spec)?;
    let mut total_usage = Usage {
        role: "total".to_string(),
        ..Usage::default()
    };
    let mut final_version_id: Option<String> = None;
    let mut first_plan: Option<PathBuf> = None;
    let mut last_gate: Option<crate::model::ArtifactGate> = None;
    let mut last_coverage = crate::model::PrdCoverage::default();
    // DR-72 ③: the manifest this iteration started from (`A_{t-1}`), so the
    // success path can state the engineering increment it produced.  It is
    // assigned at the top of every iteration and read at the end of one, which
    // the compiler's flow analysis cannot see across the loop boundary.
    #[allow(unused_assignments)]
    let mut iteration_start_manifest: Option<std::collections::BTreeMap<String, String>> = None;

    // DR-25: watch HoH's own working directory (outside the project) for writes
    // a role should never make.  Report-only; the baseline advances once per
    // observation so a path is reported exactly once.
    let out_of_tree_root = cfg
        .runtime
        .out_of_tree_root
        .clone()
        .unwrap_or_else(|| std::env::current_dir().unwrap_or_else(|_| PathBuf::from(".")));
    let mut out_of_tree_watch = crate::runtime::hygiene::OutOfTreeWatch::new(
        // DR-38: the same root doubles as the injected harness repository root
        // for the `harness_source_read` trace, so the watch takes a copy.
        out_of_tree_root.clone(),
        Some(crate::runtime::invoke::absolute_path(&workspace)),
    );

    // DR-70 ①: the round's game session is started **here**, before the Planner,
    // so the published route covers the whole window in which the Developer and
    // the Tester run.  DR-69 published it inside the battery's `editor_play_scene`
    // step — after the Developer and before the Tester — which is why the
    // acceptance found that no role process ever overlapped it (D1).
    start_round_game(orchestrator, &workspace, &run_dir).await;

    for iteration in 1..=cfg.runtime.iterations {
        let iter_dir = run_dir.join(format!("iter-{iteration}"));
        let traj_dir = iter_dir.join("traj");
        std::fs::create_dir_all(&traj_dir)?;
        std::fs::create_dir_all(iter_dir.join("logs"))?;

        let mut iter_usage: Vec<Usage> = Vec::new();
        let mut durations: Vec<(String, u64)> = Vec::new();
        // DR-22: every role attempt of this iteration, in invocation order.
        let mut iter_attempts: Vec<AttemptOutcome> = Vec::new();
        // DR-18: whether this iteration spent a wrap-up retry.
        let mut iter_wrap_up_retry_used = false;
        // DR-37: why it did (or did not) — `artifact_missing` | `not_triggered`.
        let mut iter_wrap_up_retry_reason =
            crate::runtime::record::WRAP_UP_NOT_TRIGGERED.to_string();
        // DR-19: files scrubbed of a known secret during this iteration.
        let mut iter_secret_redactions: u64 = 0;
        // DR-6: the D7 scope limitation is restated in *every* iteration result,
        // not only in `meta.json` and `warnings.log`.
        let mut iter_warnings: Vec<String> = vec![MCP_SCOPE_WARNING.to_string()];
        // DR-25: out-of-tree paths reported for this iteration.
        let mut iter_out_of_tree: std::collections::BTreeSet<String> =
            std::collections::BTreeSet::new();

        // ---------------- Planner (read-only) ----------------
        let h_pre = hash_tree(&workspace, &excludes)?;
        let m_pre = tree_manifest(&workspace, &excludes)?;
        let plan_path = iter_dir.join("plan.md");
        let planner_view = iter_dir.join("planner-view");
        // DR-22: hoisted so the post-planner contract check can annotate the
        // attempt logs even when the Planner was skipped by the ablation.
        let mut planner_attempts: Vec<AttemptOutcome> = Vec::new();

        let doc: DevelopmentDoc = if orchestrator.ablation.plan_update || iteration == 1 {
            let source = if iteration == 1 || orchestrator.ablation.warm_start {
                workspace.clone()
            } else {
                store.root.join(&a0.version_id)
            };
            let mut inputs = vec![
                (".hoh/TASK.md".to_string(), total_text.clone()),
                (
                    ".hoh/evidence.json".to_string(),
                    planner_evidence(&run_dir, iteration, &orchestrator.ablation)?,
                ),
                (
                    ".hoh/TOOLS.md".to_string(),
                    orchestrator.tools.index_markdown(Role::Planner),
                ),
                (
                    ".hoh/SCAFFOLD.md".to_string(),
                    prompts::SCAFFOLD.to_string(),
                ),
            ];
            inputs.extend(skill_inputs());
            build_view(&ViewSpec {
                root: planner_view.clone(),
                source: Some(source),
                excludes: excludes.clone(),
                private_excludes: cfg.runtime.private_excludes.clone(),
                inputs,
            })?;

            let base = RoleInvocation {
                role: Role::Planner,
                iteration,
                system_prompt: render_prompt_with_budget_and_shell(
                    prompts::PLANNER_PROMPT,
                    iteration,
                    &cfg.agent,
                    crate::runtime::shell::ShellFlavor::HOST,
                ),
                task_prompt: prompts::planner_task_with_shell(
                    iteration,
                    crate::runtime::shell::ShellFlavor::HOST,
                ),
                cwd: planner_view.clone(),
                env: role_env(
                    cfg,
                    run_id,
                    Role::Planner,
                    iteration,
                    &planner_view,
                    build_target_dir.as_deref(),
                ),
                limits: cfg.agent.clone(),
                model: cfg.model.clone(),
                trajectory_path: attempt_trajectory(&traj_dir, Role::Planner, 1),
                retry_context: None,
            };

            let started = Instant::now();
            let (gate_result, gathered_attempts) = gate_plan_traced(
                &*orchestrator.harness,
                &base,
                cfg.runtime.max_schema_retries,
                1,
            )
            .await;
            planner_attempts = gathered_attempts;
            let mut wrap_up_retry_used = false;
            let outcome = match gate_result {
                Ok(doc) => Ok(doc),
                Err(error) => {
                    if planner_attempts
                        .last()
                        .map(|a| a.exit_was_limits)
                        .unwrap_or(false)
                    {
                        // DR-18: exactly one small wrap-up retry per role/round.
                        wrap_up_retry_used = true;
                        iter_wrap_up_retry_reason =
                            crate::runtime::record::WRAP_UP_ARTIFACT_MISSING.to_string();
                        let mut wrap_base = base.clone();
                        wrap_base.limits.step_limit =
                            cfg.agent.wrap_up_steps.min(WRAP_UP_RETRY_MAX_STEPS);
                        wrap_base.system_prompt = render_prompt_with_budget_and_shell(
                            prompts::PLANNER_PROMPT,
                            iteration,
                            &wrap_base.limits,
                            crate::runtime::shell::ShellFlavor::HOST,
                        );
                        wrap_base.retry_context =
                            Some(wrap_up_context(&schema_diagnostics(&error)));
                        let first = planner_attempts.len() as u32 + 1;
                        let (retry_result, retry_attempts) =
                            gate_plan_traced(&*orchestrator.harness, &wrap_base, 0, first).await;
                        planner_attempts.extend(retry_attempts);
                        retry_result
                    } else {
                        Err(error)
                    }
                }
            };
            durations.push(("planner".to_string(), started.elapsed().as_millis() as u64));
            // DR-25: the Planner must not write anywhere but its own view.
            iter_out_of_tree.extend(out_of_tree_watch.observe());
            // DR-19: scrub the run directory after the role has run, before its
            // output is recorded as an artifact.
            iter_secret_redactions += redaction_sweep(&run_dir, &secrets, &mut iter_warnings)?;
            if wrap_up_retry_used {
                iter_wrap_up_retry_used = true;
            }
            iter_attempts.extend(planner_attempts.clone());
            note_source_reads(&mut iter_warnings, &planner_attempts, &out_of_tree_root);
            // DR-22: one symmetric trajectory/log pair per attempt.
            let planner_note = outcome
                .as_ref()
                .err()
                .map(|error| format!("planner gate failed: {error}"));
            record_attempts(
                &run_dir,
                iteration,
                &planner_attempts,
                planner_note.as_deref(),
            )?;
            let planner_usage = usage_from_attempts(&traj_dir, Role::Planner, iteration)?;
            iter_usage.push(planner_usage.clone());

            match outcome {
                Ok(doc) => {
                    std::fs::write(&plan_path, &doc.raw)?;
                    let doc = parse_plan(&doc.raw, iteration, plan_path.clone());
                    if iteration == 1 {
                        first_plan = Some(plan_path.clone());
                    }
                    doc
                }
                Err(error) => {
                    let issues = match as_hof_error(&error) {
                        Some(HofError::SchemaFailure { issues, .. }) => {
                            issues.iter().flatten().cloned().collect()
                        }
                        _ => Vec::new(),
                    };
                    // Round-1 write-path batch: the Planner's declared artifact
                    // is `.hoh/plan.md`; the runtime measures whether it is
                    // there, and records the miss as its own fact.
                    let planner_write_failures = crate::runtime::write_failure::assess_all(
                        &planner_attempts,
                        wrote_non_empty(&planner_view.join(".hoh/plan.md")),
                        crate::runtime::write_failure::DECLARED_PLANNER,
                        cfg.agent.artifact_write_budget_tokens,
                    );
                    note_write_failures(
                        &run_dir,
                        iteration,
                        &mut iter_warnings,
                        &planner_write_failures,
                    )?;
                    finalize_failure(
                        &run_dir,
                        iteration,
                        Role::Planner,
                        "schema_failure",
                        issues,
                        iter_warnings.clone(),
                        iter_usage.clone(),
                        durations.clone(),
                        EvidenceDiff::default(),
                        iter_wrap_up_retry_used,
                        iter_attempts.clone(),
                        iter_secret_redactions,
                        iter_out_of_tree.iter().cloned().collect(),
                        FailureFacts {
                            write_failures: planner_write_failures,
                            ..FailureFacts::default()
                        },
                    )?;
                    return Err(error);
                }
            }
        } else {
            // plan_update=false: D_t := D_1, the Planner is not called at all.
            let source = first_plan.clone().ok_or_else(|| {
                anyhow::anyhow!("plan_update=false requires an existing plan from iteration 1")
            })?;
            let raw = std::fs::read_to_string(&source)?;
            std::fs::write(&plan_path, &raw)?;
            parse_plan(&raw, iteration, plan_path.clone())
        };

        // Planner must not have touched the real artifact (R2).
        let h_post = hash_tree(&workspace, &excludes)?;
        if let Err(violation) = assert_unchanged("planner", &h_pre, &h_post) {
            let m_post = manifest_or_empty(&workspace, &excludes);
            let diff = diff_manifests(&m_pre, &m_post);
            // DR-22: the note lands on the attempt log instead of a side file.
            record_attempts(
                &run_dir,
                iteration,
                &planner_attempts,
                Some(&format!(
                    "contract_violation: {} (evidence_diff: {})",
                    violation.code(),
                    pretty(&diff)
                )),
            )?;
            finalize_failure(
                &run_dir,
                iteration,
                Role::Planner,
                "contract_violation",
                Vec::new(),
                {
                    let mut all = iter_warnings.clone();
                    all.push(violation.code().to_string());
                    all
                },
                iter_usage.clone(),
                durations.clone(),
                diff,
                iter_wrap_up_retry_used,
                iter_attempts.clone(),
                iter_secret_redactions,
                iter_out_of_tree.iter().cloned().collect(),
                FailureFacts::default(),
            )?;
            return Err(HofError::contract(violation).into());
        }

        // ---------------- Developer (single writer) ----------------
        if !orchestrator.ablation.warm_start && iteration > 1 {
            store.rollback(&workspace, &excludes, &a0.version_id)?;
        }
        // DR-72 ③: the increment this iteration is about to produce starts here,
        // measured with the runtime's own walk and exclusion rule.  The Planner's
        // pre-check above already covers iteration 1; re-measuring after the
        // rollback keeps the same definition for every iteration.
        iteration_start_manifest = Some(manifest_or_empty(&workspace, &excludes));
        let mut developer_inputs = vec![
            (".hoh/TASK.md".to_string(), total_text.clone()),
            (".hoh/plan.md".to_string(), doc.raw.clone()),
            (
                ".hoh/TOOLS.md".to_string(),
                orchestrator.tools.index_markdown(Role::Developer),
            ),
            (
                ".hoh/EVIDENCE_HISTORY.md".to_string(),
                evidence_history(&run_dir, iteration),
            ),
            // DR-26: a concise index of what already exists, so the Developer
            // does not have to explore the filesystem (or the harness sources)
            // to orient itself.
            (
                ".hoh/PROJECT_MAP.md".to_string(),
                crate::runtime::project_map::render_project_map(
                    &workspace,
                    &excludes,
                    iteration,
                    orchestrator.ablation.warm_start,
                ),
            ),
        ];
        developer_inputs.extend(skill_inputs());
        write_inputs(&workspace, &developer_inputs)?;

        let h_dev_before = hash_tree(&workspace, &excludes)?;
        let developer = RoleInvocation {
            role: Role::Developer,
            iteration,
            system_prompt: render_prompt_with_budget_and_shell(
                prompts::DEVELOPER_PROMPT,
                iteration,
                &cfg.agent,
                crate::runtime::shell::ShellFlavor::HOST,
            ),
            task_prompt: prompts::developer_task_with_shell(
                iteration,
                crate::runtime::shell::ShellFlavor::HOST,
            ),
            cwd: workspace.clone(),
            env: role_env(
                cfg,
                run_id,
                Role::Developer,
                iteration,
                &workspace,
                build_target_dir.as_deref(),
            ),
            limits: cfg.agent.clone(),
            model: cfg.model.clone(),
            trajectory_path: attempt_trajectory(&traj_dir, Role::Developer, 1),
            retry_context: None,
        };
        let mut developer_outcome = invoke_once(&*orchestrator.harness, &developer).await?;
        let mut developer_limits = is_limits_exceeded(&developer_outcome.exit_status);
        // DR-31: the per-role usage of this iteration, filed **as each attempt
        // ends**.  `smoke-t3` lost the Developer's first attempt (7,134,952
        // tokens / 799.8 s) because `developer_outcome.usage` was read *after*
        // the wrap-up retry had replaced it.
        let mut developer_usage = developer_outcome.usage.clone();
        durations.push(("developer".to_string(), developer_outcome.duration_ms));
        // DR-37: "is the project usable?" — the same question DR-18's wrap-up
        // retry exists to answer.  `artifact_valid` is the adapter's real check
        // (never `workspace.is_dir()`, which is always true).
        let developer_artifact_valid = orchestrator.adapter.developer_artifact_valid(&workspace);
        let mut developer_attempts: Vec<AttemptOutcome> = vec![AttemptOutcome {
            role: Role::Developer,
            iteration,
            attempt: 1,
            exit_status: developer_outcome.exit_status.clone(),
            duration_ms: developer_outcome.duration_ms,
            usage: developer_outcome.usage.clone(),
            trajectory_path: developer_outcome.trajectory_path.clone(),
            artifact_path: developer.cwd.clone(),
            artifact_valid: developer_artifact_valid,
            exit_was_limits: developer_limits,
        }];
        // DR-18/DR-37: the Developer has no submitted artifact (the project is
        // the artifact), so the wrap-up rule triggers only when the budget ran
        // out **and** the artifact is not usable.  `smoke-t5` spent 0.94M tokens
        // / 3.1 minutes on a retry whose artifact was already valid.
        if developer_limits && !developer_artifact_valid {
            iter_wrap_up_retry_used = true;
            iter_wrap_up_retry_reason =
                crate::runtime::record::WRAP_UP_ARTIFACT_MISSING.to_string();
            let mut wrap_base = developer.clone();
            wrap_base.limits.step_limit = cfg.agent.wrap_up_steps.min(WRAP_UP_RETRY_MAX_STEPS);
            wrap_base.system_prompt = render_prompt_with_budget_and_shell(
                prompts::DEVELOPER_PROMPT,
                iteration,
                &wrap_base.limits,
                crate::runtime::shell::ShellFlavor::HOST,
            );
            wrap_base.retry_context = Some(wrap_up_context(
                &orchestrator.adapter.developer_artifact_defects(&workspace),
            ));
            wrap_base.trajectory_path = attempt_trajectory(&traj_dir, Role::Developer, 2);
            developer_outcome = invoke_once(&*orchestrator.harness, &wrap_base).await?;
            developer_limits = is_limits_exceeded(&developer_outcome.exit_status);
            // DR-31: immediately, before any later assignment can shadow it.
            merge_usage(&mut developer_usage, &developer_outcome.usage);
            durations.push((
                "developer_wrap_up".to_string(),
                developer_outcome.duration_ms,
            ));
            developer_attempts.push(AttemptOutcome {
                role: Role::Developer,
                iteration,
                attempt: 2,
                exit_status: developer_outcome.exit_status.clone(),
                duration_ms: developer_outcome.duration_ms,
                usage: developer_outcome.usage.clone(),
                trajectory_path: developer_outcome.trajectory_path.clone(),
                artifact_path: developer.cwd.clone(),
                artifact_valid: developer_artifact_valid,
                exit_was_limits: developer_limits,
            });
        }
        // DR-22: the Developer now uses the same `attempt` naming as the other
        // roles, so every attempt has a trajectory and a log.
        record_attempts(&run_dir, iteration, &developer_attempts, None)?;
        iter_attempts.extend(developer_attempts.clone());
        // DR-86 ①: **the delivery boundary.**  The Developer (and, when it ran,
        // the wrap-up retry) has finished writing, so this is where the runtime
        // decides whether what is on disk is a whole document or the surviving
        // fragment of one.  The findings are recorded here, before the battery,
        // so the one targeted repair below can be handed them — a repair cannot
        // fix a file it is never told about.
        let mut integrity_findings = crate::runtime::integrity::audit_tree(&workspace, &excludes)?;
        note_integrity_findings(
            &run_dir,
            iteration,
            &mut iter_warnings,
            &integrity_findings,
            "after the developer stage",
        )?;
        note_source_reads(&mut iter_warnings, &developer_attempts, &out_of_tree_root);
        // One summary entry per role, already carrying every attempt so far; the
        // targeted repair below merges into the same entry (DR-31).
        let developer_usage_index = iter_usage.len();
        iter_usage.push(developer_usage);
        // DR-25: the Developer may only write inside the project.
        iter_out_of_tree.extend(out_of_tree_watch.observe());
        // DR-19: scrub after the developer (the only writer) too.
        iter_secret_redactions += redaction_sweep(&run_dir, &secrets, &mut iter_warnings)?;

        // DR-66 ④: **this is the signal that used to be a mere warning.**
        //
        // `h_dev_before`/`h_dev_after` bracket the whole Developer stage,
        // including the wrap-up retry, and `.hoh/**` is hash-excluded, so
        // equality means: not one byte of the project changed because of this
        // stage.  `REQUIREMENTS.md` E1 requires "the Developer produces a Godot
        // project increment", so a round in that state cannot satisfy the
        // criterion.  In `smoke-t7` the round nevertheless reported
        // `ok = true`, `exit_code = 0` and `artifact_gate.launchable = true`,
        // with `no_progress` only in `warnings` - a green run that proved
        // nothing.
        //
        // DR-66 splits the two meanings apart: `no_progress` stays the
        // *description* of the same measurement, and `no_engineering_write` is
        // the **violation**.  The violation is recorded and the round fails, so
        // no future green can be read as "the Developer produced an increment"
        // unless it did.
        // DR-67 §3 (DEF-3 option A): the gate is about the **measurement**, not
        // about *why* the Developer stopped.  DR-66 had narrowed it to "the
        // Developer's last attempt ended with `LimitsExceeded`", justified by
        // "a wider gate would collide with the existing offline fixtures" — a
        // reason the independent acceptance disproved: of the 32
        // `FakeStep::new(Role::Developer)` blocks under `tests/**`, the only one
        // whose every write lands under `.hoh/**` is the zero-increment fixture
        // that same batch added.  With the reason gone, so is the narrowing.
        //
        // The cost of the narrowing was explicit in DR-66's report §7-3: a round
        // that finished normally with zero increment still reported `ok = true`
        // and exit code 0.  That is the very failure class E1 is about, so it is
        // now closed: equality of the two hashes is the whole condition.
        let h_dev_after = hash_tree(&workspace, &excludes)?;
        // Round-1 write-path batch: the harness's **own** judgement about the
        // Developer stage.  "The artifact tree shows no write" is a measurement
        // the runtime has; the attempt's exit status and token total are its own
        // records; together they make "this role never wrote its declared
        // artifact" a first-class fact instead of an external agent's string.
        // It is computed here, before any early return can drop it.
        let developer_write_failures = crate::runtime::write_failure::assess_all(
            &developer_attempts,
            h_dev_before != h_dev_after,
            crate::runtime::write_failure::DECLARED_DEVELOPER,
            cfg.agent.artifact_write_budget_tokens,
        );
        if h_dev_before == h_dev_after {
            let warning = ContractViolation::NoProgress.code();
            iter_warnings.push(warning.to_string());
            append_warning(
                &run_dir,
                &format!(
                    "iteration {iteration}: {warning} (the developer stage produced no change)"
                ),
            )?;
        }
        note_write_failures(
            &run_dir,
            iteration,
            &mut iter_warnings,
            &developer_write_failures,
        )?;
        if h_dev_before == h_dev_after {
            let violation = ContractViolation::NoEngineeringWrite;
            // DR-67 (DEF-5): this text must describe the condition that is
            // actually checked.  DR-66 claimed a step-budget/K-step trigger that
            // nothing tested (`developer_write_deadline` is rendered into the
            // prompt but never compared against anything here), and a runtime
            // message may not assert a check that does not exist.
            // DR-69: the gate is a measurement of the artifact tree, and the
            // task book asks which zero-increment shape a round produced.  The
            // hash cannot answer that on its own, but "did the Developer write
            // anywhere at all?" can be measured: the scratch directory is where
            // DR-28 sends every probe.  Both facts are recorded, and the
            // ambiguity that remains is stated rather than hidden.
            let scratch_files = count_files(&workspace.join(".hoh/scratch"));
            let shape = if scratch_files == 0 {
                "the Developer produced no write at all"
            } else {
                "the Developer wrote, but every write went to an excluded path"
            };
            append_warning(
                &run_dir,
                &format!(
                    "iteration {iteration}: contract violation {} (the developer stage ended \
                     with no engineering write: no file in the artifact tree outside the \
                     hash-excluded runtime paths changed; every write went to an excluded path \
                     such as `.hoh/scratch`, `.godot/**` or `.import/**`). Zero-increment shape: \
                     {scratch_files} file(s) under `.hoh/scratch` at the gate, so {shape}. \
                     This gate measures the artifact tree, so it cannot distinguish `the \
                     project needed no change` from `the Developer changed nothing`: both are \
                     the same measurement, and the criterion it serves (E1) is stated for a \
                     project the Developer is meant to change.",
                    violation.code()
                ),
            )?;
            let mut warnings = iter_warnings.clone();
            warnings.push(violation.code().to_string());
            finalize_failure(
                &run_dir,
                iteration,
                Role::Developer,
                "contract_violation",
                Vec::new(),
                warnings,
                iter_usage.clone(),
                durations.clone(),
                EvidenceDiff::default(),
                iter_wrap_up_retry_used,
                iter_attempts.clone(),
                iter_secret_redactions,
                iter_out_of_tree.iter().cloned().collect(),
                // DR-68 ④: no freeze, no battery yet — the empty facts are the
                // truth here, not a stub (see `FailureFacts`).  Round-1
                // write-path batch: the one fact that *does* exist here is the
                // Developer's missed artifact, so it is carried.
                FailureFacts {
                    write_failures: developer_write_failures.clone(),
                    ..FailureFacts::default()
                },
            )?;
            return Err(HofError::contract(violation).into());
        }

        // DR-70 ①: the battery starts its own game on the **frozen candidate**
        // (the Developer has just changed the code), so the round's session is
        // stopped first — two `editor_play_scene` calls must never overlap — and
        // the route is withdrawn with it.  It is started again below, so the
        // freeze and the Tester keep running inside a published window.
        stop_round_game(orchestrator, &run_dir).await;

        // ---------------- Deterministic evidence battery (DR-1/DR-17) ------
        // It runs on the *real workspace* (the project the editor has open,
        // D7) and before `A_t` is frozen: whatever it produces — including
        // editor side effects — is part of the candidate identity instead of
        // surfacing later as pre-QA drift.
        let deterministic_dir = workspace.join(".hoh/deterministic");
        let mut battery = run_battery_pass(
            &workspace,
            &run_dir,
            1,
            &*orchestrator.adapter,
            &*orchestrator.tools,
            &meta.engine,
        )
        .await?;
        // DR-43/DR-44/DR-51: the game endpoint only exists after
        // `editor_play_scene` has run, so it is written back into `meta.json` as
        // soon as the pass that registered it is over.  The **history** is used,
        // not the live route: the battery's own `editor_stop_scene` step clears
        // the route before this line runs, which is exactly how the field was
        // structurally always `null` in `smoke-t6`.
        if let Some(registered) = orchestrator.tools.game_endpoint_history().await {
            if crate::adapter::engine::record_game_endpoint(&mut meta.engine, &registered) {
                let _ = write_run_meta(&run_dir, &meta);
            }
        }
        // DR-24: the pre-freeze launchable gate.  The paper's "keep the
        // project buildable and runnable" is checked here, not requested in a
        // prompt: a battery that cannot open the main scene means `A_t` is not
        // a usable artifact, however green the rest of the loop is.
        let mut launch_gate = crate::adapter::evaluate_launchable(&battery);
        let mut battery_passes = vec![battery_summary(1, &battery, &launch_gate)];
        let mut iter_repair_retry_used = false;
        if launch_gate.applicable && !launch_gate.launchable {
            // DR-70 ①: the repair retry is a **Developer** call, so it runs
            // inside the round's window: its game session is started again for
            // it, and stopped again before the second battery pass restarts the
            // game on the repaired candidate.
            start_round_game(orchestrator, &workspace, &run_dir).await;
            // DR-24: at most ONE targeted repair per iteration.  A false gate
            // is never silently frozen as a success.
            iter_repair_retry_used = true;
            let mut context = crate::adapter::repair_context(&battery);
            context.push_str("\nGate verdict:\n");
            for reason in &launch_gate.reasons {
                context.push_str(&format!("- {reason}\n"));
            }
            // DR-86 ①: the delivered-artifact integrity audit, verbatim, so the
            // repair call is told *which file* is a fragment and *why* the bytes
            // cannot be a whole document — the same class of evidence the gate
            // gives it, one step earlier.
            if !integrity_findings.is_empty() {
                context.push_str(
                    "\nDelivered-artifact integrity audit (DR-86 ①, verbatim — these files are \
                     fragments or carry a foreign shell escape, and each must be rewritten as a \
                     whole document):\n",
                );
                for finding in &integrity_findings {
                    context.push_str(&format!("- {}\n", finding.render()));
                }
            }
            let repair_attempt = developer_attempts.len() as u32 + 1;
            let mut repair = developer.clone();
            repair.limits.step_limit = cfg.agent.repair_steps;
            repair.system_prompt = render_prompt_with_budget_and_shell(
                prompts::DEVELOPER_PROMPT,
                iteration,
                &repair.limits,
                crate::runtime::shell::ShellFlavor::HOST,
            );
            repair.retry_context = Some(context);
            repair.trajectory_path = attempt_trajectory(&traj_dir, Role::Developer, repair_attempt);
            let repair_outcome = invoke_once(&*orchestrator.harness, &repair).await?;
            // DR-79 ③: the repair is a **new** attempt against a workspace the
            // model may have changed, so "is the project usable?" is asked again
            // instead of being answered with `workspace.is_dir()`.  The directory
            // always exists, so the old expression was unconditionally true: a
            // repair that broke `scenes/main.tscn` was recorded exactly like one
            // that fixed it (`smoke-t13` attempt 2 carried `artifact_valid=true`
            // because of it).  This is the same adapter check attempt 1 uses.
            let repair_artifact_valid = orchestrator.adapter.developer_artifact_valid(&workspace);
            developer_attempts.push(AttemptOutcome {
                role: Role::Developer,
                iteration,
                attempt: repair_attempt,
                exit_status: repair_outcome.exit_status.clone(),
                duration_ms: repair_outcome.duration_ms,
                usage: repair_outcome.usage.clone(),
                trajectory_path: repair_outcome.trajectory_path.clone(),
                artifact_path: workspace.clone(),
                artifact_valid: repair_artifact_valid,
                exit_was_limits: is_limits_exceeded(&repair_outcome.exit_status),
            });
            iter_attempts.push(developer_attempts.last().cloned().expect("just pushed"));
            note_source_reads(&mut iter_warnings, &developer_attempts, &out_of_tree_root);
            // DR-31: the repair is still the Developer role, so it merges into
            // the same per-role summary entry instead of adding a second one.
            merge_usage(
                &mut iter_usage[developer_usage_index],
                &repair_outcome.usage,
            );
            durations.push(("developer_repair".to_string(), repair_outcome.duration_ms));
            iter_out_of_tree.extend(out_of_tree_watch.observe());
            iter_secret_redactions += redaction_sweep(&run_dir, &secrets, &mut iter_warnings)?;
            record_attempts(
                &run_dir,
                iteration,
                &developer_attempts,
                Some("launch_gate_repair: the pre-freeze launchable gate failed"),
            )?;

            // Re-run the battery on the repaired workspace and judge again.
            stop_round_game(orchestrator, &run_dir).await;
            battery = run_battery_pass(
                &workspace,
                &run_dir,
                2,
                &*orchestrator.adapter,
                &*orchestrator.tools,
                &meta.engine,
            )
            .await?;
            // DR-51: the second pass registers its own game endpoint (a new port
            // and pid); fold it in immediately, before its own stop step can
            // clear the route.
            if let Some(registered) = orchestrator.tools.game_endpoint_history().await {
                if crate::adapter::engine::record_game_endpoint(&mut meta.engine, &registered) {
                    let _ = write_run_meta(&run_dir, &meta);
                }
            }
            launch_gate = crate::adapter::evaluate_launchable(&battery);
            battery_passes.push(battery_summary(2, &battery, &launch_gate));
        }
        // DR-86 ①: re-measure after the **last** write-capable retry.  Whether or
        // not a repair ran, a delivered file that is a fragment must not be
        // treated as a delivered artifact: the finding becomes a gate reason so
        // `launchable=false` names the truncation itself, not only the editor's
        // downstream parse error.  This only ever *adds* a reason — the DR-24
        // classification of real project defects against infrastructure is
        // untouched, and a project that is genuinely whole is unaffected.
        integrity_findings = crate::runtime::integrity::audit_tree(&workspace, &excludes)?;
        note_integrity_findings(
            &run_dir,
            iteration,
            &mut iter_warnings,
            &integrity_findings,
            "after the last write-capable retry",
        )?;
        if !integrity_findings.is_empty() {
            if !launch_gate.applicable {
                // The battery declared no gate step, so its `gate_not_applicable`
                // note described the *battery*.  The integrity check is a gate
                // check that always applies, so that note must not survive next
                // to `applicable: true`.
                launch_gate
                    .reasons
                    .retain(|reason| !reason.starts_with("gate_not_applicable"));
            }
            for finding in &integrity_findings {
                let reason = format!("artifact_integrity: {}", finding.render());
                if !launch_gate
                    .reasons
                    .iter()
                    .any(|existing| existing == &reason)
                {
                    launch_gate.reasons.push(reason);
                }
            }
            launch_gate.applicable = true;
            launch_gate.launchable = false;
            if let Some(last) = battery_passes.last_mut() {
                last.launchable = launch_gate.launchable;
            }
        }
        // DR-70 ①: the battery's pass(es) are over and its own `editor_stop_scene`
        // has withdrawn the route.  The round's session is started again here so
        // the freeze and the Tester run inside a published window that points at
        // a game built from the candidate the battery just measured.
        start_round_game(orchestrator, &workspace, &run_dir).await;
        if launch_gate.applicable && !launch_gate.launchable {
            // DR-24: the second failure is honest, not fatal — the round still
            // advances, and `result.json.artifact_gate.launchable = false`
            // makes the QA gap inevitable and visible.
            append_warning(
                &run_dir,
                &format!(
                    "iteration {iteration}: the artifact is not launchable after the one allowed \
                     repair retry; freezing A{iteration} anyway (artifact_gate.launchable=false)"
                ),
            )?;
        }
        // DR-17: the summary and the flat record list are both materialized so
        // the Tester (and a human reviewer) can read either shape.
        std::fs::write(deterministic_dir.join("battery.json"), pretty(&battery))?;
        let deterministic: Vec<crate::model::ExecRecord> =
            battery.iter().map(|entry| entry.record.clone()).collect();
        std::fs::write(
            deterministic_dir.join("deterministic.json"),
            pretty(&deterministic),
        )?;
        let deterministic_log = format!(
            "deterministic evidence battery on the real workspace produced {} step(s), {} of \
             them ok; launchable={} (battery pass(es): {}, repair_retry_used={})\n{}",
            battery.len(),
            battery.iter().filter(|entry| entry.ok).count(),
            launch_gate.launchable,
            battery_passes.len(),
            iter_repair_retry_used,
            pretty(&battery)
        );
        // DR-1: the log travels into the frozen view together with the records.
        std::fs::write(
            deterministic_dir.join("deterministic.log"),
            &deterministic_log,
        )?;
        for (index, record) in deterministic.iter().enumerate() {
            std::fs::write(
                deterministic_dir.join(format!("record-{index:02}.json")),
                pretty(record),
            )?;
        }

        // ---------------- Freeze A_t ----------------
        let h_det = hash_tree(&workspace, &excludes)?;
        let version = store.snapshot_role(
            &workspace,
            &excludes,
            iteration,
            "developer",
            &format!("A{iteration} after the developer and deterministic stages"),
        )?;
        debug_assert_eq!(version.candidate_id, h_det);
        final_version_id = Some(version.version_id.clone());

        // ---------------- Candidate view (from the frozen snapshot) --------
        let candidate = iter_dir.join("candidate");
        let mut candidate_inputs = vec![
            (".hoh/TASK.md".to_string(), total_text.clone()),
            (".hoh/plan.md".to_string(), doc.raw.clone()),
            (
                ".hoh/TOOLS.md".to_string(),
                orchestrator.tools.index_markdown(Role::Tester),
            ),
            (
                ".hoh/EVIDENCE_PLAYBOOK.md".to_string(),
                orchestrator.adapter.evidence_playbook(),
            ),
            // Placeholder artifact: the Tester must produce the real one.
            (".hoh/evidence.json".to_string(), String::new()),
        ];
        candidate_inputs.extend(skill_inputs());
        build_view(&ViewSpec {
            root: candidate.clone(),
            source: Some(store.root.join(&version.version_id)),
            excludes: excludes.clone(),
            private_excludes: cfg.runtime.private_excludes.clone(),
            inputs: candidate_inputs,
        })?;
        // DR-1: the deterministic records (and the adapter's own logs) are
        // copied into the frozen view so the Tester can cite them relatively.
        // DR-62: `copy_tree` applies the same structural supersession criterion
        // as `copy_evidence`, so a recorded supersession cannot enter through
        // this copy path either (DR-61 R-3 / acceptance R-B).
        copy_tree(
            &deterministic_dir,
            &candidate.join(".hoh/deterministic"),
            &[],
        )?;
        // DR-36: the *evidence* the battery produced (screenshots, replays,
        // recordings) must be visible to the Tester too.  `smoke-t5` lost a real
        // 4246-byte PNG here and reported it as missing (gap G19).
        for (relative, size) in crate::runtime::view::copy_evidence(
            &workspace.join(".hoh/evidence"),
            &candidate.join(".hoh/evidence"),
            cfg.runtime.max_evidence_bytes,
        )? {
            let warning = format!(
                "evidence_too_large: {} ({} byte(s) > {} byte(s)); the file was copied anyway",
                relative, size, cfg.runtime.max_evidence_bytes
            );
            iter_warnings.push(warning.clone());
            append_warning(&run_dir, &format!("iteration {iteration}: {warning}"))?;
        }

        // ---------------- QA pre-check: the artifact must still be A_t -------
        let workspace_now = hash_tree(&workspace, &excludes)?;
        if workspace_now != version.candidate_id {
            let m_ws = manifest_or_empty(&workspace, &excludes);
            let m_frozen = manifest_or_empty(&store.root.join(&version.version_id), &excludes);
            let diff = diff_manifests(&m_frozen, &m_ws);
            // No tester attempt has run yet, so this cannot be an attempt-log
            // note; it goes to the run-level warning log.
            append_warning(
                &run_dir,
                &format!(
                    "iteration {iteration}: contract violation {} (workspace {} != candidate {}) \
                     evidence_diff: {}",
                    ContractViolation::WorkspaceDriftBeforeQa.code(),
                    workspace_now,
                    version.candidate_id,
                    pretty(&diff)
                ),
            )?;
            finalize_failure(
                &run_dir,
                iteration,
                Role::Tester,
                "contract_violation",
                Vec::new(),
                {
                    let mut all = iter_warnings.clone();
                    all.push(ContractViolation::WorkspaceDriftBeforeQa.code().to_string());
                    all
                },
                iter_usage.clone(),
                durations.clone(),
                diff,
                iter_wrap_up_retry_used,
                iter_attempts.clone(),
                iter_secret_redactions,
                iter_out_of_tree.iter().cloned().collect(),
                // DR-68 ④: the freeze and the battery already happened, so this
                // failure must not erase them from `result.json`.  DR-86 ④ adds
                // the gate verdict to the same list for the same reason.
                FailureFacts {
                    candidate_id: Some(version.candidate_id.clone()),
                    version_id: Some(version.version_id.clone()),
                    battery_passes: battery_passes.clone(),
                    artifact_gate: Some(launch_gate.clone()),
                    ..FailureFacts::default()
                },
            )?;
            return Err(HofError::contract(ContractViolation::WorkspaceDriftBeforeQa).into());
        }

        // ---------------- Tester (frozen candidate) ----------------
        let h_cand_before = hash_tree(&candidate, &excludes)?;
        let m_cand_before = tree_manifest(&candidate, &excludes)?;
        let h_ws_before = hash_tree(&workspace, &excludes)?;
        let m_ws_before = tree_manifest(&workspace, &excludes)?;
        // DR-88 ④: the excluded-path watch, taken from the same moment as the
        // hashed identity.  The candidate view is copied from the snapshot with
        // the caches excluded, so it starts with none of these directories: any
        // path that appears under one of them during QA is a role's write.
        let cache_before = cache_manifest(&candidate, &cache_watch)?;
        let tester_base = RoleInvocation {
            role: Role::Tester,
            iteration,
            system_prompt: render_prompt_with_budget_and_shell(
                prompts::TESTER_PROMPT,
                iteration,
                &cfg.agent,
                crate::runtime::shell::ShellFlavor::HOST,
            ),
            task_prompt: prompts::tester_task_with_shell(
                iteration,
                crate::runtime::shell::ShellFlavor::HOST,
            ),
            cwd: candidate.clone(),
            env: role_env(
                cfg,
                run_id,
                Role::Tester,
                iteration,
                &candidate,
                build_target_dir.as_deref(),
            ),
            limits: cfg.agent.clone(),
            model: cfg.model.clone(),
            trajectory_path: attempt_trajectory(&traj_dir, Role::Tester, 1),
            retry_context: None,
        };
        let started = Instant::now();
        let (gate_result, mut tester_attempts) = gate_evidence_traced(
            &*orchestrator.harness,
            &tester_base,
            &version.candidate_id,
            cfg.runtime.max_schema_retries,
            1,
        )
        .await;
        let mut tester_wrap_up_retry_used = false;
        let gate = match gate_result {
            Ok(bundle) => Ok(bundle),
            Err(error) => {
                if tester_attempts
                    .last()
                    .map(|a| a.exit_was_limits)
                    .unwrap_or(false)
                {
                    // DR-18: exactly one small wrap-up retry per role/round.
                    tester_wrap_up_retry_used = true;
                    iter_wrap_up_retry_used = true;
                    iter_wrap_up_retry_reason =
                        crate::runtime::record::WRAP_UP_ARTIFACT_MISSING.to_string();
                    let mut wrap_base = tester_base.clone();
                    wrap_base.limits.step_limit =
                        cfg.agent.wrap_up_steps.min(WRAP_UP_RETRY_MAX_STEPS);
                    wrap_base.system_prompt = render_prompt_with_budget_and_shell(
                        prompts::TESTER_PROMPT,
                        iteration,
                        &wrap_base.limits,
                        crate::runtime::shell::ShellFlavor::HOST,
                    );
                    wrap_base.retry_context = Some(wrap_up_context(&schema_diagnostics(&error)));
                    let first = tester_attempts.len() as u32 + 1;
                    let (retry_result, retry_attempts) = gate_evidence_traced(
                        &*orchestrator.harness,
                        &wrap_base,
                        &version.candidate_id,
                        0,
                        first,
                    )
                    .await;
                    tester_attempts.extend(retry_attempts);
                    retry_result
                } else {
                    Err(error)
                }
            }
        };
        let _ = tester_wrap_up_retry_used;
        durations.push(("tester".to_string(), started.elapsed().as_millis() as u64));
        iter_attempts.extend(tester_attempts.clone());
        note_source_reads(&mut iter_warnings, &tester_attempts, &out_of_tree_root);
        // DR-25: the Tester is read-only; any write outside its view is reported.
        iter_out_of_tree.extend(out_of_tree_watch.observe());
        // DR-22: symmetric trajectory/log pair per tester attempt.
        let tester_note = gate
            .as_ref()
            .err()
            .map(|error| format!("tester gate failed: {error}"));
        record_attempts(
            &run_dir,
            iteration,
            &tester_attempts,
            tester_note.as_deref(),
        )?;
        let tester_usage = usage_from_attempts(&traj_dir, Role::Tester, iteration)?;
        iter_usage.push(tester_usage);
        // DR-19: scrub after the tester before any of its output is recorded.
        iter_secret_redactions += redaction_sweep(&run_dir, &secrets, &mut iter_warnings)?;

        // Detection comes first: a contaminated round is a failure no matter
        // how good the evidence looks.
        let h_cand_after = hash_tree(&candidate, &excludes)?;
        let h_ws_after = hash_tree(&workspace, &excludes)?;
        // DR-88 ④: the excluded-path watch.  A write through one of the
        // adapter's configured cache excludes is invisible to `hash_tree` (R10
        // keeps `version_id` stable, which is exactly why they are excluded),
        // so before this batch a round could read `ok=true`, carry no
        // `qa_contaminated_*` warning and still have left a role's bytes in
        // `.godot/**` of the frozen view.  The directories are therefore
        // observed on their own, the bytes are preserved as evidence, and the
        // round is rejected exactly as for a write the hash can see.
        let cache_after = cache_manifest(&candidate, &cache_watch)?;
        let candidate_cache_diff = diff_manifests(&cache_before, &cache_after);
        if !candidate_cache_diff.is_empty() {
            let preserve_root = iter_dir.join("tester-writes/cache-candidate");
            let preservation_failures = crate::runtime::frozen_view::preserve_excluded_writes(
                &candidate,
                &preserve_root,
                &candidate_cache_diff,
            );
            let mut detail = format!(
                "added={:?} modified={:?} removed={:?}",
                candidate_cache_diff.added,
                candidate_cache_diff.modified,
                candidate_cache_diff.removed
            );
            for failure in &preservation_failures {
                detail.push_str(&format!("; {failure}"));
            }
            let token = "qa_wrote_cache_candidate".to_string();
            if !iter_warnings.contains(&token) {
                iter_warnings.push(token.clone());
            }
            append_warning(
                &run_dir,
                &format!(
                    "iteration {iteration}: {token} (DR-88 ④): a role wrote into the frozen \
                     candidate view through the adapter's configured cache excludes \
                     {cache_watch:?}, which the artifact hash deliberately does not cover \
                     (R10 keeps `version_id` stable).  {detail}. The added bytes were moved out \
                     to iter-{iteration}/tester-writes/cache-candidate/; the round is rejected \
                     exactly as for a write the hash can see."
                ),
            )?;
        }
        let candidate_violation =
            assert_unchanged("tester/candidate", &h_cand_before, &h_cand_after).err();
        let workspace_violation =
            assert_unchanged("tester/workspace", &h_ws_before, &h_ws_after).err();
        if candidate_violation.is_some() || workspace_violation.is_some() {
            // DR-86 ④ / D295(b): the frozen view is re-established from the
            // immutable A_t snapshot, and every byte a role wrote is
            // **preserved** — never deleted — under `iter-N/tester-writes/`.
            // `smoke-t16`'s first round ended right here with
            // `reason=contract_violation` and `artifact_gate.applicable=false`,
            // i.e. with **no gate verdict at all**; the property this guard
            // establishes is that the verdict already produced is never thrown
            // away.  It is not a licence for the round to pass: the violation is
            // still reported and still fails the round below.
            let violation = candidate_violation
                .or(workspace_violation)
                .unwrap_or(crate::model::ContractViolation::QaContaminatedCandidate);
            let frozen_version = store.root.join(&version.version_id);
            let mut restored: Vec<(&str, crate::runtime::frozen_view::RestoreReport)> = Vec::new();
            if candidate_violation.is_some() {
                let report = crate::runtime::frozen_view::restore_frozen_view(
                    &candidate,
                    &frozen_version,
                    &m_cand_before,
                    &excludes,
                    &iter_dir.join("tester-writes/candidate"),
                )?;
                restored.push(("candidate", report));
            }
            if workspace_violation.is_some() {
                let report = crate::runtime::frozen_view::restore_frozen_view(
                    &workspace,
                    &frozen_version,
                    &m_ws_before,
                    &excludes,
                    &iter_dir.join("tester-writes/workspace"),
                )?;
                restored.push(("workspace", report));
            }
            let mut failures: Vec<String> = Vec::new();
            for (label, report) in &restored {
                let token = format!("qa_contaminated_{label}_restored");
                if !iter_warnings.iter().any(|warning| warning == &token) {
                    iter_warnings.push(token.clone());
                }
                append_warning(
                    &run_dir,
                    &format!(
                        "iteration {iteration}: {token} (DR-86 ④): a role wrote into the frozen \
                         {label} view; the frozen bytes were restored from the A{iteration} \
                         snapshot and every stray byte was preserved under \
                         iter-{iteration}/tester-writes/{label}/. Report: {}",
                        report.render()
                    ),
                )?;
                failures.extend(report.failures.iter().cloned());
            }
            let candidate_restored = crate::runtime::frozen_view::matches_manifest(
                &candidate,
                &m_cand_before,
                &excludes,
            )?;
            let workspace_restored =
                crate::runtime::frozen_view::matches_manifest(&workspace, &m_ws_before, &excludes)?;
            // A false equality must say *what* is still different: "the restore
            // did not verify" is only actionable with the residual difference.
            if !candidate_restored {
                failures.push(format!(
                    "the candidate view is not back to its frozen bytes after the restoration: {}",
                    pretty(&diff_manifests(
                        &m_cand_before,
                        &manifest_or_empty(&candidate, &excludes)
                    ))
                ));
            }
            if !workspace_restored {
                failures.push(format!(
                    "the workspace is not back to its frozen bytes after the restoration: {}",
                    pretty(&diff_manifests(
                        &m_ws_before,
                        &manifest_or_empty(&workspace, &excludes)
                    ))
                ));
            }
            if !failures.is_empty() {
                // The guard could not put the frozen bytes back, so the round
                // fails loudly — exactly as it did before this repair — but now
                // the real gate verdict travels with the failure instead of being
                // discarded.
                let mut all = iter_warnings.clone();
                for (label, report) in &restored {
                    all.push(format!("qa_restore_failed_{label}: {}", report.render()));
                }
                all.push(violation.code().to_string());
                return fail_contract(
                    &run_dir,
                    iteration,
                    Role::Tester,
                    violation,
                    iter_usage,
                    durations,
                    all,
                    diff_manifests(&m_cand_before, &manifest_or_empty(&candidate, &excludes)),
                    iter_attempts,
                    iter_secret_redactions,
                    iter_out_of_tree.iter().cloned().collect(),
                    FailureFacts {
                        candidate_id: Some(version.candidate_id.clone()),
                        version_id: Some(version.version_id.clone()),
                        battery_passes: battery_passes.clone(),
                        artifact_gate: Some(launch_gate.clone()),
                        ..FailureFacts::default()
                    },
                );
            }
            // D295(b): detection, restoration and preservation are exactly the
            // acts that make the violation **auditable** — they are not a repair
            // that makes the round compliant.  `REQUIREMENTS.md` R4/R13 say a QA
            // write into the frozen snapshot is **rejected**, and a criterion
            // measures compliance, not repairability, so the round still fails
            // here; what changed versus `smoke-t16` is that it now fails **with**
            // the real gate verdict the battery already produced (`artifact_gate`
            // above) instead of throwing that verdict away and publishing a
            // `not_applicable` stub.  `result.json.ok` is false and
            // `reason=contract_violation`; read together with the `qa_*`
            // warnings that is what distinguishes the round from one in which no
            // role wrote at all.  The hash alone cannot make that distinction:
            // it never covers the adapter's configured cache excludes, which the
            // watch above observes separately.
            return fail_contract(
                &run_dir,
                iteration,
                Role::Tester,
                violation,
                iter_usage,
                durations,
                iter_warnings.clone(),
                diff_manifests(&m_cand_before, &manifest_or_empty(&candidate, &excludes)),
                iter_attempts,
                iter_secret_redactions,
                iter_out_of_tree.iter().cloned().collect(),
                FailureFacts {
                    candidate_id: Some(version.candidate_id.clone()),
                    version_id: Some(version.version_id.clone()),
                    battery_passes: battery_passes.clone(),
                    artifact_gate: Some(launch_gate.clone()),
                    ..FailureFacts::default()
                },
            );
        }

        // DR-88 ④: a write found **only** by the excluded-path watch is the same
        // contract violation as one the hash can see — R4/R13 reject a QA write
        // into the frozen snapshot, and the exclusion is a hash boundary, not a
        // licence.  The distinction is preserved in the record: this round
        // carries `qa_wrote_cache_candidate` rather than
        // `qa_contaminated_candidate_restored`, because the bytes were moved out
        // as evidence rather than restored from a snapshot that does not hold
        // them, and the criterion's reading requires that token to be absent.
        if !candidate_cache_diff.is_empty() {
            return fail_contract(
                &run_dir,
                iteration,
                Role::Tester,
                ContractViolation::QaContaminatedCandidate,
                iter_usage,
                durations,
                iter_warnings.clone(),
                candidate_cache_diff,
                iter_attempts,
                iter_secret_redactions,
                iter_out_of_tree.iter().cloned().collect(),
                FailureFacts {
                    candidate_id: Some(version.candidate_id.clone()),
                    version_id: Some(version.version_id.clone()),
                    battery_passes: battery_passes.clone(),
                    artifact_gate: Some(launch_gate.clone()),
                    ..FailureFacts::default()
                },
            );
        }

        let bundle = match gate {
            Ok(bundle) => bundle,
            Err(error) => {
                let issues = match as_hof_error(&error) {
                    Some(HofError::SchemaFailure { issues, .. }) => {
                        issues.iter().flatten().cloned().collect()
                    }
                    _ => Vec::new(),
                };
                // Round-1 write-path batch: the Tester's declared artifact is
                // `.hoh/evidence.json`; whether the frozen view really carries a
                // non-empty one is a measurement, not the agent's claim.
                let tester_write_failures = crate::runtime::write_failure::assess_all(
                    &tester_attempts,
                    wrote_non_empty(&candidate.join(".hoh/evidence.json")),
                    crate::runtime::write_failure::DECLARED_TESTER,
                    cfg.agent.artifact_write_budget_tokens,
                );
                note_write_failures(
                    &run_dir,
                    iteration,
                    &mut iter_warnings,
                    &tester_write_failures,
                )?;
                finalize_failure(
                    &run_dir,
                    iteration,
                    Role::Tester,
                    "schema_failure",
                    issues,
                    iter_warnings.clone(),
                    iter_usage.clone(),
                    durations.clone(),
                    EvidenceDiff::default(),
                    iter_wrap_up_retry_used,
                    iter_attempts.clone(),
                    iter_secret_redactions,
                    iter_out_of_tree.iter().cloned().collect(),
                    // DR-68 ④: this is the `smoke-t8` failure class — the round
                    // froze `A_t` and ran the whole battery before the Tester's
                    // evidence was rejected.  Persist what really happened.
                    FailureFacts {
                        candidate_id: Some(version.candidate_id.clone()),
                        version_id: Some(version.version_id.clone()),
                        battery_passes: battery_passes.clone(),
                        artifact_gate: Some(launch_gate.clone()),
                        write_failures: tester_write_failures,
                    },
                )?;
                return Err(error);
            }
        };

        // ---------------- Record ----------------
        write_evidence(&iter_dir.join("evidence.json"), &bundle)?;
        let submitted_report = candidate.join(".hoh/qa_report.md");
        let report = if submitted_report.is_file() {
            std::fs::read_to_string(&submitted_report)?
        } else {
            qa_report_fallback(&bundle)
        };
        std::fs::write(iter_dir.join("qa_report.md"), report.replace("\r\n", "\n"))?;

        for usage in &iter_usage {
            merge_usage(&mut total_usage, usage);
        }
        write_usage(&run_dir, iteration, &iter_usage, &iter_attempts)?;

        // DR-19: one last sweep, so nothing written between the last stage and
        // here can leave a credential behind.
        iter_secret_redactions += redaction_sweep(&run_dir, &secrets, &mut iter_warnings)?;
        let mut result = IterResult::ok();
        result.warnings = iter_warnings;
        result.candidate_id = Some(version.candidate_id.clone());
        result.version_id = Some(version.version_id.clone());
        result.usage = iter_usage;
        result.durations_ms = durations;
        result.wrap_up_retry_used = iter_wrap_up_retry_used;
        result.wrap_up_retry_reason = iter_wrap_up_retry_reason;
        result.attempts = iter_attempts;
        result.secret_redactions = iter_secret_redactions;
        // DR-72 ③: the real engineering increment, on the **success** path too.
        // It is measured from the iteration's starting manifest to the frozen
        // `A_t` snapshot, i.e. from the same two trees the contract-violation
        // paths use, so "nothing changed" and "the field was never filled in" are
        // finally distinguishable.
        result.evidence_diff = match iteration_start_manifest.as_ref() {
            Some(before) => {
                iteration_evidence_diff(before, &store.root.join(&version.version_id), &excludes)
            }
            // Unreachable: the success path only exists after an iteration ran,
            // which is exactly where the manifest is captured.  An empty
            // starting manifest would be a lie, so say so instead.
            None => unreachable!(
                "the success path cannot run without an iteration start manifest (DR-72 ③)"
            ),
        };
        // DR-24/DR-27: the gate verdict travels with the iteration result, so
        // a completed loop over an unlaunchable artifact can never look green.
        result.artifact_gate = launch_gate.clone();
        result.repair_retry_used = iter_repair_retry_used;
        result.battery_passes = battery_passes.clone();
        // Round-1 write-path batch: the round result states, in its own words,
        // every role attempt that did not write the artifact it declared.
        result.write_failures = developer_write_failures.clone();
        result.out_of_tree_writes = iter_out_of_tree.iter().cloned().collect();
        // DR-28: report-only hygiene of the frozen `A_t`.
        result.artifact_hygiene = crate::model::ArtifactHygiene {
            suspicious_files: crate::runtime::hygiene::suspicious_files(&workspace),
            // DR-69: the `-p` directory a `mkdir -p` under cmd leaves behind is
            // invisible to the file scan and to the hash.
            suspicious_directories: crate::runtime::hygiene::suspicious_directories(&workspace),
        };
        // DR-39: the PRD coverage travels with the gate, so `exit 0 + gate ok`
        // can never be read as "the product is good" on its own.
        result.prd_coverage = crate::model::PrdCoverage::from_bundle(&bundle);
        last_gate = Some(launch_gate);
        last_coverage = result.prd_coverage.clone();
        write_iter_result(&run_dir, iteration, &result)?;
    }

    // DR-19: run-level sweep for anything written outside the per-iteration
    // windows (warnings.log, meta.json, version snapshots).
    let mut sweep_warnings: Vec<String> = Vec::new();
    // DR-79 ①: "report-only" was the whole of DR-25, and `smoke-t13` shows the
    // cost — three untracked `.tmp_*.json` files left in the repository root
    // with nothing to remove them.  The round now removes **the temporaries it
    // watched itself create** (the watcher's union across the round, so a file
    // that pre-dated the round is never touched; the eligibility rule is
    // `hygiene::is_root_temporary`, one component of a temporary name shape)
    // and records the removal below.  The write stays in
    // `out_of_tree_writes`: the fact is evidence, the litter is not.
    let cleaned = crate::runtime::hygiene::clean_round_temporaries(
        &out_of_tree_root,
        &out_of_tree_watch.observed(),
    );
    if !cleaned.is_empty() {
        sweep_warnings.push(format!(
            "out_of_tree_cleanup: removed {} round-temporary file(s) from {}: {}",
            cleaned.len(),
            out_of_tree_root.display(),
            cleaned.join(", ")
        ));
    }
    redaction_sweep(&run_dir, &secrets, &mut sweep_warnings)?;
    for warning in &sweep_warnings {
        append_warning(&run_dir, warning)?;
    }

    Ok(RunSummary {
        run_id: run_id.to_string(),
        iterations_completed: cfg.runtime.iterations,
        final_version_id,
        total_usage,
        // DR-66 ④: the verdict, not a constant.  A round that reached this
        // point has no failed iteration; a failed one returns its own summary
        // and never reaches the loop's end.  `finalize_run` turns `ok = false`
        // into a non-zero exit code, which is what makes the E1-class failure
        // visible to anything that only reads `result.json.ok` or the exit code.
        ok: true,
        artifact_gate: last_gate
            .unwrap_or_else(|| crate::model::ArtifactGate::not_applicable("no iteration ran")),
        prd_coverage: last_coverage,
        // DR-67 (DEF-2): the loop finished, so there is no failure to carry —
        // the exit code comes from the artifact gate alone (DR-27).
        failure_exit_code: None,
    })
}

#[allow(clippy::too_many_arguments)]
fn fail_contract(
    run_dir: &Path,
    iteration: u32,
    role: Role,
    violation: ContractViolation,
    usage: Vec<Usage>,
    durations: Vec<(String, u64)>,
    warnings: Vec<String>,
    evidence_diff: EvidenceDiff,
    attempts: Vec<AttemptOutcome>,
    secret_redactions: u64,
    out_of_tree_writes: Vec<String>,
    facts: FailureFacts,
) -> anyhow::Result<RunSummary> {
    // DR-22: the violation is a note on the attempt log, not a side file.
    record_attempts(
        run_dir,
        iteration,
        &attempts,
        Some(&format!(
            "contract_violation: {} (evidence_diff: {})",
            violation.code(),
            pretty(&evidence_diff)
        )),
    )?;
    finalize_failure(
        run_dir,
        iteration,
        role,
        "contract_violation",
        Vec::new(),
        {
            let mut all = warnings;
            all.push(violation.code().to_string());
            all
        },
        usage,
        durations,
        evidence_diff,
        false,
        attempts,
        secret_redactions,
        out_of_tree_writes,
        facts,
    )?;
    Err(HofError::contract(violation).into())
}

#[cfg(test)]
mod tests {
    use super::*;

    /// DR-74 ⑤: the sealed-area list must be the **production** list.
    ///
    /// The DR-72 acceptance planted the removal of
    /// `roots.push(iter_dir.join("traj"))` (DR-74 ⑤) and every suite stayed
    /// green: the only test that built a `SealedAreas` built its own list, so
    /// "a trajectory is never rewritten" was invisible to a future edit.  This
    /// test drives [`frozen_evidence_roots`] itself, so deleting any root —
    /// `traj` included — reddens it.
    #[test]
    fn the_production_sealed_areas_cover_every_frozen_root() {
        let run_dir = Path::new("runs/run-1");
        let sealed = frozen_evidence_roots(run_dir, 2);
        assert!(
            !sealed.is_empty(),
            "the production sealed list must never be empty"
        );

        for relative in [
            "versions/aaaa/env.json",
            "quarantine/.hoh.stale-1/deterministic/raw/x.json",
            "iter-1/candidate/.hoh/evidence.json",
            "iter-1/traj/tester.attempt1.json",
            "iter-2/candidate/.hoh/evidence.json",
            "iter-2/traj/planner.attempt1.json",
        ] {
            assert!(
                sealed.contains(&run_dir.join(relative)),
                "`{relative}` is frozen evidence and must be sealed by the production list"
            );
        }

        // The deliberate exception (DR-19, DR-74 ⑥/D4): a role's own
        // planner-view dump is erased **in place**, so it must NOT be sealed.
        // Sealing it reddens `secret_isolation::a_leaked_secret_is_erased_and_counted`.
        assert!(
            !sealed.contains(&run_dir.join("iter-1/planner-view/env-dump.txt")),
            "`iter-*/planner-view` is deliberately not sealed (DR-19)"
        );
        // Containment is component-wise: a sibling whose name shares a prefix is
        // not inside a sealed root.
        assert!(!sealed.contains(&run_dir.join("iter-1/candidate-evil/x.json")));
        assert!(!sealed.contains(&run_dir.join("versions-evil/x.json")));
        // Only the iterations that exist are sealed.
        assert!(!sealed.contains(&run_dir.join("iter-3/traj/x.json")));
    }
}
