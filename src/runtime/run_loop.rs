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
use crate::errors::{as_hof_error, HofError};
use crate::harness::Harness;
use crate::model::{
    empty_evidence, parse_plan, Ablation, ContractViolation, DevelopmentDoc, EvidenceDiff, Role,
    SchemaIssue, Spec, Usage,
};
use crate::prompts;
use crate::runtime::evidence::write_evidence;
use crate::runtime::invoke::{
    attempt_trajectory, invoke_once, is_limits_exceeded, render_prompt_with_budget, role_env,
    WRAP_UP_RETRY_CONTEXT,
};
use crate::runtime::policy::{
    assert_unchanged, diff_manifests, hash_tree, tree_manifest, HashExcludes,
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

fn skill_inputs() -> Vec<(String, String)> {
    prompts::skills()
        .into_iter()
        .map(|(name, content)| (format!(".hoh/skills/{name}"), content.to_string()))
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
) -> anyhow::Result<()> {
    write_usage(run_dir, iteration, &usage, &attempts)?;
    let result = IterResult {
        ok: false,
        failed_role: Some(role),
        reason: reason.to_string(),
        issues,
        warnings,
        candidate_id: None,
        version_id: None,
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
        ..IterResult::ok()
    };
    write_iter_result(run_dir, iteration, &result)
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

/// DR-29: turn the battery session's synchronization report into an iteration
/// warning.  A desynchronized MCP endpoint mislabels every payload it returns,
/// so the round must say so in `result.json.warnings` instead of quietly
/// publishing evidence that belongs to another call.
fn note_mcp_desync(warnings: &mut Vec<String>, workspace: &Path) {
    let path = workspace.join(crate::adapter::godot::SESSION_SYNC_FILE);
    let Ok(raw) = std::fs::read_to_string(&path) else {
        return;
    };
    let Ok(report) = serde_json::from_str::<crate::tools::mcp::SessionSyncReport>(&raw) else {
        return;
    };
    if !report.desynced {
        return;
    }
    let warning = crate::adapter::godot::desync_warning(&report);
    if !warnings.iter().any(|existing| existing == &warning) {
        warnings.push(warning);
    }
}

/// A manifest that could not be produced must not mask the violation itself.
fn manifest_or_empty(
    root: &Path,
    excludes: &[String],
) -> std::collections::BTreeMap<String, String> {
    tree_manifest(root, excludes).unwrap_or_default()
}

/// DR-24: one battery pass.  The directory is rebuilt from scratch so a
/// second (post-repair) pass never leaves the first pass's raw payloads
/// behind to be mistaken for the frozen `A_t` evidence.
async fn run_battery_pass(
    workspace: &Path,
    adapter: &dyn ProjectAdapter,
    tools: &dyn ToolChannel,
    engine: &crate::adapter::EngineIdentity,
) -> anyhow::Result<Vec<crate::adapter::BatteryRecord>> {
    let deterministic_dir = workspace.join(".hoh/deterministic");
    let _ = std::fs::remove_dir_all(&deterministic_dir);
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

/// Run the whole HoH loop.
pub async fn run(
    orchestrator: &Orchestrator,
    spec: &Spec,
    run_id: &str,
) -> anyhow::Result<RunSummary> {
    let cfg = &orchestrator.cfg;
    let run_dir = cfg.runtime.runs_dir.join(run_id);
    std::fs::create_dir_all(&run_dir)?;

    let workspace = cfg.runtime.workspace.clone();
    std::fs::create_dir_all(&workspace)?;
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

    let excludes = HashExcludes::new(orchestrator.adapter.cache_excludes()).merged();
    let store = VersionStore::new(run_dir.join("versions"));

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
                system_prompt: render_prompt_with_budget(
                    prompts::PLANNER_PROMPT,
                    iteration,
                    &cfg.agent,
                ),
                task_prompt: prompts::planner_task(iteration),
                cwd: planner_view.clone(),
                env: role_env(cfg, run_id, Role::Planner, iteration, &planner_view),
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
                        wrap_base.system_prompt = render_prompt_with_budget(
                            prompts::PLANNER_PROMPT,
                            iteration,
                            &wrap_base.limits,
                        );
                        wrap_base.retry_context = Some(WRAP_UP_RETRY_CONTEXT.to_string());
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
            iter_secret_redactions += crate::runtime::secrets::redact_tree(&run_dir, &secrets)?;
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
            )?;
            return Err(HofError::contract(violation).into());
        }

        // ---------------- Developer (single writer) ----------------
        if !orchestrator.ablation.warm_start && iteration > 1 {
            store.rollback(&workspace, &excludes, &a0.version_id)?;
        }
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
            system_prompt: render_prompt_with_budget(
                prompts::DEVELOPER_PROMPT,
                iteration,
                &cfg.agent,
            ),
            task_prompt: prompts::developer_task(iteration),
            cwd: workspace.clone(),
            env: role_env(cfg, run_id, Role::Developer, iteration, &workspace),
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
            wrap_base.system_prompt =
                render_prompt_with_budget(prompts::DEVELOPER_PROMPT, iteration, &wrap_base.limits);
            wrap_base.retry_context = Some(WRAP_UP_RETRY_CONTEXT.to_string());
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
        note_source_reads(&mut iter_warnings, &developer_attempts, &out_of_tree_root);
        // One summary entry per role, already carrying every attempt so far; the
        // targeted repair below merges into the same entry (DR-31).
        let developer_usage_index = iter_usage.len();
        iter_usage.push(developer_usage);
        // DR-25: the Developer may only write inside the project.
        iter_out_of_tree.extend(out_of_tree_watch.observe());
        // DR-19: scrub after the developer (the only writer) too.
        iter_secret_redactions += crate::runtime::secrets::redact_tree(&run_dir, &secrets)?;

        let h_dev_after = hash_tree(&workspace, &excludes)?;
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

        // ---------------- Deterministic evidence battery (DR-1/DR-17) ------
        // It runs on the *real workspace* (the project the editor has open,
        // D7) and before `A_t` is frozen: whatever it produces — including
        // editor side effects — is part of the candidate identity instead of
        // surfacing later as pre-QA drift.
        let deterministic_dir = workspace.join(".hoh/deterministic");
        let mut battery = run_battery_pass(
            &workspace,
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
        // DR-29: the session-start probe's verdict travels with the iteration.
        note_mcp_desync(&mut iter_warnings, &workspace);
        // DR-24: the pre-freeze launchable gate.  The paper's "keep the
        // project buildable and runnable" is checked here, not requested in a
        // prompt: a battery that cannot open the main scene means `A_t` is not
        // a usable artifact, however green the rest of the loop is.
        let mut launch_gate = crate::adapter::evaluate_launchable(&battery);
        let mut battery_passes = vec![battery_summary(1, &battery, &launch_gate)];
        let mut iter_repair_retry_used = false;
        if launch_gate.applicable && !launch_gate.launchable {
            // DR-24: at most ONE targeted repair per iteration.  A false gate
            // is never silently frozen as a success.
            iter_repair_retry_used = true;
            let mut context = crate::adapter::repair_context(&battery);
            context.push_str("\nGate verdict:\n");
            for reason in &launch_gate.reasons {
                context.push_str(&format!("- {reason}\n"));
            }
            let repair_attempt = developer_attempts.len() as u32 + 1;
            let mut repair = developer.clone();
            repair.limits.step_limit = cfg.agent.repair_steps;
            repair.system_prompt =
                render_prompt_with_budget(prompts::DEVELOPER_PROMPT, iteration, &repair.limits);
            repair.retry_context = Some(context);
            repair.trajectory_path = attempt_trajectory(&traj_dir, Role::Developer, repair_attempt);
            let repair_outcome = invoke_once(&*orchestrator.harness, &repair).await?;
            developer_attempts.push(AttemptOutcome {
                role: Role::Developer,
                iteration,
                attempt: repair_attempt,
                exit_status: repair_outcome.exit_status.clone(),
                duration_ms: repair_outcome.duration_ms,
                usage: repair_outcome.usage.clone(),
                trajectory_path: repair_outcome.trajectory_path.clone(),
                artifact_path: workspace.clone(),
                artifact_valid: workspace.is_dir(),
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
            iter_secret_redactions += crate::runtime::secrets::redact_tree(&run_dir, &secrets)?;
            record_attempts(
                &run_dir,
                iteration,
                &developer_attempts,
                Some("launch_gate_repair: the pre-freeze launchable gate failed"),
            )?;

            // Re-run the battery on the repaired workspace and judge again.
            battery = run_battery_pass(
                &workspace,
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
            // DR-29: the second pass runs its own session probe.
            note_mcp_desync(&mut iter_warnings, &workspace);
            launch_gate = crate::adapter::evaluate_launchable(&battery);
            battery_passes.push(battery_summary(2, &battery, &launch_gate));
        }
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
            )?;
            return Err(HofError::contract(ContractViolation::WorkspaceDriftBeforeQa).into());
        }

        // ---------------- Tester (frozen candidate) ----------------
        let h_cand_before = hash_tree(&candidate, &excludes)?;
        let m_cand_before = tree_manifest(&candidate, &excludes)?;
        let h_ws_before = hash_tree(&workspace, &excludes)?;
        let m_ws_before = tree_manifest(&workspace, &excludes)?;
        let tester_base = RoleInvocation {
            role: Role::Tester,
            iteration,
            system_prompt: render_prompt_with_budget(prompts::TESTER_PROMPT, iteration, &cfg.agent),
            task_prompt: prompts::tester_task(iteration),
            cwd: candidate.clone(),
            env: role_env(cfg, run_id, Role::Tester, iteration, &candidate),
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
                    wrap_base.system_prompt = render_prompt_with_budget(
                        prompts::TESTER_PROMPT,
                        iteration,
                        &wrap_base.limits,
                    );
                    wrap_base.retry_context = Some(WRAP_UP_RETRY_CONTEXT.to_string());
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
        iter_secret_redactions += crate::runtime::secrets::redact_tree(&run_dir, &secrets)?;

        // Detection comes first: a contaminated round is a failure no matter
        // how good the evidence looks.
        let h_cand_after = hash_tree(&candidate, &excludes)?;
        let h_ws_after = hash_tree(&workspace, &excludes)?;
        if let Err(violation) = assert_unchanged("tester/candidate", &h_cand_before, &h_cand_after)
        {
            let diff = diff_manifests(&m_cand_before, &manifest_or_empty(&candidate, &excludes));
            return fail_contract(
                &run_dir,
                iteration,
                Role::Tester,
                violation,
                iter_usage,
                durations,
                iter_warnings,
                diff,
                iter_attempts,
                iter_secret_redactions,
                iter_out_of_tree.iter().cloned().collect(),
            );
        }
        if let Err(violation) = assert_unchanged("tester/workspace", &h_ws_before, &h_ws_after) {
            let diff = diff_manifests(&m_ws_before, &manifest_or_empty(&workspace, &excludes));
            return fail_contract(
                &run_dir,
                iteration,
                Role::Tester,
                violation,
                iter_usage,
                durations,
                iter_warnings,
                diff,
                iter_attempts,
                iter_secret_redactions,
                iter_out_of_tree.iter().cloned().collect(),
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
        iter_secret_redactions += crate::runtime::secrets::redact_tree(&run_dir, &secrets)?;
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
        // DR-24/DR-27: the gate verdict travels with the iteration result, so
        // a completed loop over an unlaunchable artifact can never look green.
        result.artifact_gate = launch_gate.clone();
        result.repair_retry_used = iter_repair_retry_used;
        result.battery_passes = battery_passes.clone();
        result.out_of_tree_writes = iter_out_of_tree.iter().cloned().collect();
        // DR-28: report-only hygiene of the frozen `A_t`.
        result.artifact_hygiene = crate::model::ArtifactHygiene {
            suspicious_files: crate::runtime::hygiene::suspicious_files(&workspace),
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
    crate::runtime::secrets::redact_tree(&run_dir, &secrets)?;

    Ok(RunSummary {
        run_id: run_id.to_string(),
        iterations_completed: cfg.runtime.iterations,
        final_version_id,
        total_usage,
        ok: true,
        artifact_gate: last_gate
            .unwrap_or_else(|| crate::model::ArtifactGate::not_applicable("no iteration ran")),
        prd_coverage: last_coverage,
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
    )?;
    Err(HofError::contract(violation).into())
}
