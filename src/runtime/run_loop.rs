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
use crate::runtime::invoke::{attempt_trajectory, invoke_once, render_prompt, role_env};
use crate::runtime::policy::{
    assert_unchanged, diff_manifests, hash_tree, tree_manifest, HashExcludes,
};
use crate::runtime::record::{
    append_warning, write_iter_result, write_log, write_run_meta, write_usage, IterResult, RunMeta,
};
use crate::runtime::role::RoleInvocation;
use crate::runtime::schema::{gate_evidence, gate_plan};
use crate::runtime::snapshot::VersionStore;
use crate::runtime::usage::{merge_usage, usage_from_attempts};
use crate::runtime::view::{build_view, copy_tree, write_inputs, ViewSpec};
use crate::tools::ToolChannel;

/// The D7 scope limitation is recorded, never hidden.
pub const MCP_SCOPE_WARNING: &str =
    "qa_scope: MCP acts on the project open in the editor (the real workspace) while the Tester \
     evaluates a frozen copy; the runtime binds both to one candidate identity with pre-QA and \
     around-QA hash assertions (D7).";

pub struct Orchestrator {
    pub harness: Box<dyn Harness>,
    pub adapter: Box<dyn ProjectAdapter>,
    pub tools: Arc<dyn ToolChannel>,
    pub cfg: HohConfig,
    pub ablation: Ablation,
    /// Whether `initialize` may replace an existing non-empty workspace.
    pub force_init: bool,
}

#[derive(Clone, Debug)]
pub struct RunSummary {
    pub run_id: String,
    pub iterations_completed: u32,
    pub final_version_id: Option<String>,
    pub total_usage: Usage,
    pub ok: bool,
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
) -> anyhow::Result<()> {
    write_usage(run_dir, iteration, &usage)?;
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
    };
    write_iter_result(run_dir, iteration, &result)
}

/// A manifest that could not be produced must not mask the violation itself.
fn manifest_or_empty(
    root: &Path,
    excludes: &[String],
) -> std::collections::BTreeMap<String, String> {
    tree_manifest(root, excludes).unwrap_or_default()
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

    let excludes = HashExcludes::new(orchestrator.adapter.cache_excludes()).merged();
    let store = VersionStore::new(run_dir.join("versions"));

    let warnings = vec![MCP_SCOPE_WARNING.to_string()];
    let meta = RunMeta {
        run_id: run_id.to_string(),
        spec: spec.clone(),
        ablation: orchestrator.ablation,
        iterations: cfg.runtime.iterations,
        model_identity: cfg.model_identity(),
        started_at: now_seconds(),
        hoh_version: env!("CARGO_PKG_VERSION").to_string(),
        warnings: warnings.clone(),
        config: cfg.model.clone(),
    };
    write_run_meta(&run_dir, &meta)?;
    append_warning(&run_dir, MCP_SCOPE_WARNING)?;

    // A0 is snapshotted before anything else so warm_start=false can restore it.
    let a0 = store.snapshot_role(&workspace, &excludes, 0, "init", "A0 initial artifact")?;

    let total_text = spec_text(spec)?;
    let mut total_usage = Usage {
        role: "total".to_string(),
        ..Usage::default()
    };
    let mut final_version_id: Option<String> = None;
    let mut first_plan: Option<PathBuf> = None;

    for iteration in 1..=cfg.runtime.iterations {
        let iter_dir = run_dir.join(format!("iter-{iteration}"));
        let traj_dir = iter_dir.join("traj");
        std::fs::create_dir_all(&traj_dir)?;
        std::fs::create_dir_all(iter_dir.join("logs"))?;

        let mut iter_usage: Vec<Usage> = Vec::new();
        let mut durations: Vec<(String, u64)> = Vec::new();
        // DR-6: the D7 scope limitation is restated in *every* iteration result,
        // not only in `meta.json` and `warnings.log`.
        let mut iter_warnings: Vec<String> = vec![MCP_SCOPE_WARNING.to_string()];

        // ---------------- Planner (read-only) ----------------
        let h_pre = hash_tree(&workspace, &excludes)?;
        let m_pre = tree_manifest(&workspace, &excludes)?;
        let plan_path = iter_dir.join("plan.md");
        let planner_view = iter_dir.join("planner-view");

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
                system_prompt: render_prompt(prompts::PLANNER_PROMPT, iteration),
                task_prompt: prompts::planner_task(iteration),
                cwd: planner_view.clone(),
                env: role_env(cfg, run_id, Role::Planner, iteration, &planner_view),
                limits: cfg.agent.clone(),
                model: cfg.model.clone(),
                trajectory_path: attempt_trajectory(&traj_dir, Role::Planner, 1),
                retry_context: None,
            };

            let started = Instant::now();
            let outcome = gate_plan(
                &*orchestrator.harness,
                &base,
                cfg.runtime.max_schema_retries,
            )
            .await;
            durations.push(("planner".to_string(), started.elapsed().as_millis() as u64));
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
                    write_log(
                        &run_dir,
                        iteration,
                        "planner",
                        &format!(
                            "schema_failure after {} attempts: {error}",
                            1 + cfg.runtime.max_schema_retries
                        ),
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
            write_log(
                &run_dir,
                iteration,
                "planner",
                &format!(
                    "contract violation: {}\nevidence_diff: {}",
                    violation.code(),
                    pretty(&diff)
                ),
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
        ];
        developer_inputs.extend(skill_inputs());
        write_inputs(&workspace, &developer_inputs)?;

        let h_dev_before = hash_tree(&workspace, &excludes)?;
        let developer = RoleInvocation {
            role: Role::Developer,
            iteration,
            system_prompt: render_prompt(prompts::DEVELOPER_PROMPT, iteration),
            task_prompt: prompts::developer_task(iteration),
            cwd: workspace.clone(),
            env: role_env(cfg, run_id, Role::Developer, iteration, &workspace),
            limits: cfg.agent.clone(),
            model: cfg.model.clone(),
            trajectory_path: traj_dir.join("developer.json"),
            retry_context: None,
        };
        let developer_outcome = invoke_once(&*orchestrator.harness, &developer).await?;
        durations.push(("developer".to_string(), developer_outcome.duration_ms));
        iter_usage.push(developer_outcome.usage.clone());
        write_log(
            &run_dir,
            iteration,
            "developer",
            &format!(
                "exit_status={} duration_ms={} submission={}\n",
                developer_outcome.exit_status,
                developer_outcome.duration_ms,
                developer_outcome.submission
            ),
        )?;

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

        // ---------------- Deterministic build check (DR-1) ----------------
        // It runs on the *real workspace* (the project the editor has open,
        // D7) and before `A_t` is frozen: whatever it produces — including
        // editor side effects — is part of the candidate identity instead of
        // surfacing later as pre-QA drift.
        let deterministic_dir = workspace.join(".hoh/deterministic");
        let _ = std::fs::remove_dir_all(&deterministic_dir);
        std::fs::create_dir_all(&deterministic_dir)?;
        let deterministic = orchestrator
            .adapter
            .build_check(&workspace, &*orchestrator.tools)
            .await?;
        std::fs::write(
            deterministic_dir.join("deterministic.json"),
            pretty(&deterministic),
        )?;
        write_log(
            &run_dir,
            iteration,
            "deterministic",
            &format!(
                "deterministic stage on the real workspace produced {} record(s)\n{}",
                deterministic.len(),
                pretty(&deterministic)
            ),
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

        // ---------------- QA pre-check: the artifact must still be A_t -------
        let workspace_now = hash_tree(&workspace, &excludes)?;
        if workspace_now != version.candidate_id {
            let m_ws = manifest_or_empty(&workspace, &excludes);
            let m_frozen = manifest_or_empty(&store.root.join(&version.version_id), &excludes);
            let diff = diff_manifests(&m_frozen, &m_ws);
            write_log(
                &run_dir,
                iteration,
                "tester",
                &format!(
                    "contract violation: {} (workspace {} != candidate {})\nevidence_diff: {}",
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
            system_prompt: render_prompt(prompts::TESTER_PROMPT, iteration),
            task_prompt: prompts::tester_task(iteration),
            cwd: candidate.clone(),
            env: role_env(cfg, run_id, Role::Tester, iteration, &candidate),
            limits: cfg.agent.clone(),
            model: cfg.model.clone(),
            trajectory_path: attempt_trajectory(&traj_dir, Role::Tester, 1),
            retry_context: None,
        };
        let started = Instant::now();
        let gate = gate_evidence(
            &*orchestrator.harness,
            &tester_base,
            &version.candidate_id,
            cfg.runtime.max_schema_retries,
        )
        .await;
        durations.push(("tester".to_string(), started.elapsed().as_millis() as u64));
        let tester_usage = usage_from_attempts(&traj_dir, Role::Tester, iteration)?;
        iter_usage.push(tester_usage);

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
                write_log(
                    &run_dir,
                    iteration,
                    "tester",
                    &format!(
                        "schema_failure after {} attempts: {error}",
                        1 + cfg.runtime.max_schema_retries
                    ),
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
        write_log(
            &run_dir,
            iteration,
            "tester",
            &format!(
                "qa_status={:?} verified={} gaps={} candidate_id={}\n",
                bundle.qa_status,
                bundle.verified_records.len(),
                bundle.gap_records.len(),
                version.candidate_id
            ),
        )?;

        for usage in &iter_usage {
            merge_usage(&mut total_usage, usage);
        }
        write_usage(&run_dir, iteration, &iter_usage)?;

        let mut result = IterResult::ok();
        result.warnings = iter_warnings;
        result.candidate_id = Some(version.candidate_id.clone());
        result.version_id = Some(version.version_id.clone());
        result.usage = iter_usage;
        result.durations_ms = durations;
        write_iter_result(&run_dir, iteration, &result)?;
    }

    Ok(RunSummary {
        run_id: run_id.to_string(),
        iterations_completed: cfg.runtime.iterations,
        final_version_id,
        total_usage,
        ok: true,
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
) -> anyhow::Result<RunSummary> {
    write_log(
        run_dir,
        iteration,
        role.as_str(),
        &format!(
            "contract violation: {}\nevidence_diff: {}",
            violation.code(),
            pretty(&evidence_diff)
        ),
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
    )?;
    Err(HofError::contract(violation).into())
}
