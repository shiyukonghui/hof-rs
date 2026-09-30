//! `SchemaGate`: the outer half of the double gate (§4.3).
//!
//! The role may self-heal inside its own call via `hoh submit`; this gate is
//! the paper-level bounded retry.  Exhausting the retries is a failure — it is
//! never silently downgraded to "passed", and a previous iteration's artifact
//! is never substituted.

use std::path::PathBuf;

use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::errors::HofError;
use crate::harness::Harness;
use crate::model::{
    parse_plan, validate_evidence, validate_evidence_shape, validate_plan, DevelopmentDoc,
    EvidenceBundle, IssueCode, Role, SchemaIssue, Usage, EVIDENCE_SKELETON, PLAN_SKELETON,
};
use crate::runtime::evidence::bind;
use crate::runtime::invoke::{assert_fully_rendered, attempt_trajectory, invoke_once};
use crate::runtime::role::RoleInvocation;

/// Diagnostics of a gate run: how many attempts were spent and what was wrong.
#[derive(Clone, Debug, Default)]
pub struct GateOutcome {
    pub attempts: u32,
    pub issues: Vec<Vec<SchemaIssue>>,
}

/// DR-22: one role *attempt* as observed by the runtime.  Every attempt must
/// leave both a trajectory and a symmetric log, and both must state this
/// record's fields, so a failed round can always be attributed to one call.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AttemptOutcome {
    pub role: Role,
    pub iteration: u32,
    pub attempt: u32,
    pub exit_status: String,
    pub duration_ms: u64,
    pub usage: Usage,
    /// Absolute path of the trajectory written by this attempt.
    pub trajectory_path: PathBuf,
    /// Absolute path of the artifact the attempt was supposed to produce.
    pub artifact_path: PathBuf,
    pub artifact_valid: bool,
    /// DR-18: true when the call ended because its step budget ran out.
    pub exit_was_limits: bool,
}

fn issue_list(issues: &[SchemaIssue]) -> String {
    issues
        .iter()
        .map(|issue| format!("- [{}] {}", issue.code.as_str(), issue.message))
        .collect::<Vec<_>>()
        .join("\n")
}

fn retry_context(expected: &std::path::Path, issues: &[SchemaIssue], skeleton: &str) -> String {
    format!(
        "SCHEMA VALIDATION FAILED. Your previous submission was rejected by the runtime.\n\n\
         Expected artifact path: {}\n\n\
         Issues:\n{}\n\n\
         Submit exactly this structure (replace the placeholders; do not rename files):\n\n{}\n\
         Fix the file and submit it again before you finish.",
        expected.display(),
        issue_list(issues),
        skeleton
    )
}

/// DR-68 ①: the **shape** block, delivered on every attempt — including the
/// first.
///
/// `smoke-t8` showed why: `EVIDENCE_SKELETON` was only ever attached as *retry
/// context*, so a role that never got a retry was never told the structure it
/// was being validated against.  The Tester's artifact was rejected for
/// `missing field \`type\`` after 150 steps, and the very retry that would have
/// carried the skeleton was suppressed — one mechanism, two independent gaps.
/// Telling the model the shape up front costs one paragraph and removes the
/// first of them.
fn shape_context(expected: &std::path::Path, skeleton: &str) -> String {
    format!(
        "REQUIRED ARTIFACT SHAPE. The runtime validates `{}` against this exact structure. \
         Produce it from your **first** attempt; do not wait to be told it was wrong. The field \
         names are case-sensitive; every key shown below is required, and a placeholder means \
         \"replace it\":\n\n{}\n",
        expected.display(),
        skeleton
    )
}

/// DR-68 ①: the first attempt's context.  `base` is whatever the caller already
/// wanted the attempt to see (a wrap-up instruction, a repair context); the
/// shape block is appended so it can never be the thing that is missing.
fn first_attempt_context(base: Option<&str>, expected: &std::path::Path, skeleton: &str) -> String {
    let shape = shape_context(expected, skeleton);
    match base {
        Some(extra) if !extra.is_empty() => format!("{extra}\n\n---\n\n{shape}"),
        _ => shape,
    }
}

/// Run the Planner until `D_t` validates, or fail after `1 + max_retries`.
pub async fn gate_plan(
    harness: &dyn Harness,
    base: &RoleInvocation,
    max_retries: u32,
) -> anyhow::Result<DevelopmentDoc> {
    gate_plan_traced(harness, base, max_retries, 1).await.0
}

/// DR-18/DR-22: the traced Planner gate.
///
/// It also implements the "stop burning steps" rule: when an attempt ends with
/// `LimitsExceeded` *and* its artifact is still missing or invalid, the
/// remaining schema retries cannot succeed either (they would only exhaust the
/// same budget again), so the loop stops and lets the runtime decide whether a
/// small wrap-up retry is allowed.
pub async fn gate_plan_traced(
    harness: &dyn Harness,
    base: &RoleInvocation,
    max_retries: u32,
    first_attempt: u32,
) -> (anyhow::Result<DevelopmentDoc>, Vec<AttemptOutcome>) {
    if let Err(error) = assert_fully_rendered("planner system prompt", &base.system_prompt) {
        return (Err(error), Vec::new());
    }
    if let Err(error) = assert_fully_rendered("planner task prompt", &base.task_prompt) {
        return (Err(error), Vec::new());
    }

    let traj_dir = base
        .trajectory_path
        .parent()
        .map(|path| path.to_path_buf())
        .unwrap_or_else(|| std::path::PathBuf::from("."));
    let expected = base.cwd.join(Role::Planner.artifact_rel_path());
    let total = 1 + max_retries;
    let mut attempts: Vec<AttemptOutcome> = Vec::new();
    let mut issues_log: Vec<Vec<SchemaIssue>> = Vec::new();
    // DR-68 ①: the shape travels with the **first** attempt too.
    let mut context: Option<String> = Some(first_attempt_context(
        base.retry_context.as_deref(),
        &expected,
        PLAN_SKELETON,
    ));
    // DR-68 ①(b): at most one shape-carrying retry after a `LimitsExceeded`.
    let mut shape_retry_spent = false;

    for index in 0..total {
        let attempt = first_attempt + index;
        let mut invocation = base.clone();
        invocation.trajectory_path = attempt_trajectory(&traj_dir, Role::Planner, attempt);
        invocation.retry_context = context.clone();
        let outcome = match invoke_once(harness, &invocation).await {
            Ok(outcome) => outcome,
            Err(error) => return (Err(error), attempts),
        };

        let (issues, doc) = match std::fs::read_to_string(&expected) {
            Err(error) => (
                vec![SchemaIssue::new(
                    IssueCode::Json,
                    format!(
                        "the planner artifact is missing: expected `{}` ({error})",
                        expected.display()
                    ),
                )],
                None,
            ),
            Ok(raw) => {
                let doc = parse_plan(&raw, invocation.iteration, expected.clone());
                match validate_plan(&doc) {
                    Ok(()) => (Vec::new(), Some(doc)),
                    Err(issues) => (issues, None),
                }
            }
        };
        let limits = crate::runtime::invoke::is_limits_exceeded(&outcome.exit_status);
        attempts.push(AttemptOutcome {
            role: Role::Planner,
            iteration: invocation.iteration,
            attempt,
            exit_status: outcome.exit_status.clone(),
            duration_ms: outcome.duration_ms,
            usage: outcome.usage.clone(),
            trajectory_path: invocation.trajectory_path.clone(),
            artifact_path: expected.clone(),
            artifact_valid: doc.is_some(),
            exit_was_limits: limits,
        });
        if let Some(doc) = doc {
            return (Ok(doc), attempts);
        }
        context = Some(retry_context(&expected, &issues, PLAN_SKELETON));
        issues_log.push(issues);
        if limits && (shape_retry_spent || !expected.is_file()) {
            // DR-18: more schema retries would only exhaust the same budget.
            // DR-68 ①(b): unless the artifact is **present but invalid** — then
            // exactly one retry with the shape is still a concrete repair
            // rather than a re-run of the same budget.
            break;
        }
        if limits {
            shape_retry_spent = true;
        }
    }

    let attempts_made = attempts.len() as u32;
    (
        Err(HofError::SchemaFailure {
            role: Role::Planner,
            attempts: attempts_made,
            issues: issues_log,
        }
        .into()),
        attempts,
    )
}

/// Run the Tester until `E_t` validates and binds to the candidate, or fail.
pub async fn gate_evidence(
    harness: &dyn Harness,
    base: &RoleInvocation,
    candidate_id: &str,
    max_retries: u32,
) -> anyhow::Result<EvidenceBundle> {
    gate_evidence_traced(harness, base, candidate_id, max_retries, 1)
        .await
        .0
}

/// DR-18/DR-22: the traced Tester gate (same wrap-up rule as the Planner gate).
pub async fn gate_evidence_traced(
    harness: &dyn Harness,
    base: &RoleInvocation,
    candidate_id: &str,
    max_retries: u32,
    first_attempt: u32,
) -> (anyhow::Result<EvidenceBundle>, Vec<AttemptOutcome>) {
    if let Err(error) = assert_fully_rendered("tester system prompt", &base.system_prompt) {
        return (Err(error), Vec::new());
    }
    if let Err(error) = assert_fully_rendered("tester task prompt", &base.task_prompt) {
        return (Err(error), Vec::new());
    }

    let traj_dir = base
        .trajectory_path
        .parent()
        .map(|path| path.to_path_buf())
        .unwrap_or_else(|| std::path::PathBuf::from("."));
    let expected = base.cwd.join(Role::Tester.artifact_rel_path());
    let total = 1 + max_retries;
    let mut attempts: Vec<AttemptOutcome> = Vec::new();
    let mut issues_log: Vec<Vec<SchemaIssue>> = Vec::new();
    // DR-68 ①: `EVIDENCE_SKELETON` reaches the **first** attempt, not only a
    // retry.  `smoke-t8`'s Tester never saw it at all.
    let mut context: Option<String> = Some(first_attempt_context(
        base.retry_context.as_deref(),
        &expected,
        EVIDENCE_SKELETON,
    ));
    // DR-68 ①(b): at most one shape-carrying retry after a `LimitsExceeded`.
    let mut shape_retry_spent = false;

    for index in 0..total {
        let attempt = first_attempt + index;
        let mut invocation = base.clone();
        invocation.trajectory_path = attempt_trajectory(&traj_dir, Role::Tester, attempt);
        invocation.retry_context = context.clone();
        let outcome = match invoke_once(harness, &invocation).await {
            Ok(outcome) => outcome,
            Err(error) => return (Err(error), attempts),
        };

        let (issues, bundle) = validate_tester_artifact(&expected, candidate_id, &invocation);
        let limits = crate::runtime::invoke::is_limits_exceeded(&outcome.exit_status);
        attempts.push(AttemptOutcome {
            role: Role::Tester,
            iteration: invocation.iteration,
            attempt,
            exit_status: outcome.exit_status.clone(),
            duration_ms: outcome.duration_ms,
            usage: outcome.usage.clone(),
            trajectory_path: invocation.trajectory_path.clone(),
            artifact_path: expected.clone(),
            artifact_valid: bundle.is_some(),
            exit_was_limits: limits,
        });
        if let Some(bundle) = bundle {
            return (Ok(bundle), attempts);
        }
        context = Some(retry_context(&expected, &issues, EVIDENCE_SKELETON));
        issues_log.push(issues);
        if limits && (shape_retry_spent || !expected.is_file()) {
            // DR-18: more schema retries would only exhaust the same budget.
            // DR-68 ①(b): unless the artifact is **present but invalid** — then
            // exactly one retry with the complete shape is a concrete repair.
            // `smoke-t8` broke here with a present, shape-invalid artifact, so
            // the retry that could have fixed it never ran and the round ended
            // with `schema failure for role Tester after 1 attempt(s)`.
            break;
        }
        if limits {
            shape_retry_spent = true;
        }
    }

    let attempts_made = attempts.len() as u32;
    (
        Err(HofError::SchemaFailure {
            role: Role::Tester,
            attempts: attempts_made,
            issues: issues_log,
        }
        .into()),
        attempts,
    )
}

/// Validate + bind one Tester artifact.  `Ok` carries the bound bundle.
fn validate_tester_artifact(
    expected: &std::path::Path,
    candidate_id: &str,
    invocation: &RoleInvocation,
) -> (Vec<SchemaIssue>, Option<EvidenceBundle>) {
    let issues = match std::fs::read_to_string(expected) {
        Err(error) => vec![SchemaIssue::new(
            IssueCode::Json,
            format!(
                "the tester artifact is missing: expected `{}` ({error})",
                expected.display()
            ),
        )],
        Ok(raw) => match serde_json::from_str::<Value>(&raw) {
            Err(error) => vec![SchemaIssue::new(
                IssueCode::Json,
                format!("evidence is not valid JSON: {error}"),
            )],
            Ok(value) => {
                let shape = validate_evidence_shape(&value);
                if !shape.is_empty() {
                    shape
                } else {
                    match serde_json::from_value::<EvidenceBundle>(value) {
                        Err(error) => vec![SchemaIssue::new(
                            IssueCode::Json,
                            format!("evidence does not match the required structure: {error}"),
                        )],
                        Ok(mut bundle) => {
                            let mut issues = validate_evidence(&bundle, candidate_id)
                                .err()
                                .unwrap_or_default();
                            match bind(&mut bundle, candidate_id, &invocation.cwd) {
                                Ok(()) if issues.is_empty() => return (Vec::new(), Some(bundle)),
                                Ok(()) => {}
                                Err(bind_issues) => issues.extend(bind_issues),
                            }
                            issues
                        }
                    }
                }
            }
        },
    };
    (issues, None)
}
