//! `SchemaGate`: the outer half of the double gate (§4.3).
//!
//! The role may self-heal inside its own call via `hoh submit`; this gate is
//! the paper-level bounded retry.  Exhausting the retries is a failure — it is
//! never silently downgraded to "passed", and a previous iteration's artifact
//! is never substituted.

use serde_json::Value;

use crate::errors::HofError;
use crate::harness::Harness;
use crate::model::{
    parse_plan, validate_evidence, validate_evidence_shape, validate_plan, DevelopmentDoc,
    EvidenceBundle, IssueCode, Role, SchemaIssue, EVIDENCE_SKELETON, PLAN_SKELETON,
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

/// Run the Planner until `D_t` validates, or fail after `1 + max_retries`.
pub async fn gate_plan(
    harness: &dyn Harness,
    base: &RoleInvocation,
    max_retries: u32,
) -> anyhow::Result<DevelopmentDoc> {
    assert_fully_rendered("planner system prompt", &base.system_prompt)?;
    assert_fully_rendered("planner task prompt", &base.task_prompt)?;

    let traj_dir = base
        .trajectory_path
        .parent()
        .map(|path| path.to_path_buf())
        .unwrap_or_else(|| std::path::PathBuf::from("."));
    let expected = base.cwd.join(Role::Planner.artifact_rel_path());
    let total = 1 + max_retries;
    let mut issues_log: Vec<Vec<SchemaIssue>> = Vec::new();
    let mut context: Option<String> = base.retry_context.clone();

    for attempt in 1..=total {
        let mut invocation = base.clone();
        invocation.trajectory_path = attempt_trajectory(&traj_dir, Role::Planner, attempt);
        invocation.retry_context = context.clone();
        invoke_once(harness, &invocation).await?;

        let issues = match std::fs::read_to_string(&expected) {
            Err(error) => vec![SchemaIssue::new(
                IssueCode::Json,
                format!(
                    "the planner artifact is missing: expected `{}` ({error})",
                    expected.display()
                ),
            )],
            Ok(raw) => {
                let doc = parse_plan(&raw, invocation.iteration, expected.clone());
                match validate_plan(&doc) {
                    Ok(()) => return Ok(doc),
                    Err(issues) => issues,
                }
            }
        };
        context = Some(retry_context(&expected, &issues, PLAN_SKELETON));
        issues_log.push(issues);
    }

    Err(HofError::SchemaFailure {
        role: Role::Planner,
        attempts: total,
        issues: issues_log,
    }
    .into())
}

/// Run the Tester until `E_t` validates and binds to the candidate, or fail.
pub async fn gate_evidence(
    harness: &dyn Harness,
    base: &RoleInvocation,
    candidate_id: &str,
    max_retries: u32,
) -> anyhow::Result<EvidenceBundle> {
    assert_fully_rendered("tester system prompt", &base.system_prompt)?;
    assert_fully_rendered("tester task prompt", &base.task_prompt)?;

    let traj_dir = base
        .trajectory_path
        .parent()
        .map(|path| path.to_path_buf())
        .unwrap_or_else(|| std::path::PathBuf::from("."));
    let expected = base.cwd.join(Role::Tester.artifact_rel_path());
    let total = 1 + max_retries;
    let mut issues_log: Vec<Vec<SchemaIssue>> = Vec::new();
    let mut context: Option<String> = base.retry_context.clone();

    for attempt in 1..=total {
        let mut invocation = base.clone();
        invocation.trajectory_path = attempt_trajectory(&traj_dir, Role::Tester, attempt);
        invocation.retry_context = context.clone();
        invoke_once(harness, &invocation).await?;

        let issues = match std::fs::read_to_string(&expected) {
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
                                    Ok(()) if issues.is_empty() => return Ok(bundle),
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
        context = Some(retry_context(&expected, &issues, EVIDENCE_SKELETON));
        issues_log.push(issues);
    }

    Err(HofError::SchemaFailure {
        role: Role::Tester,
        attempts: total,
        issues: issues_log,
    }
    .into())
}
