//! The harness's **own** judgement about a role that did not write the artifact
//! it declared (round-1 write-path batch).
//!
//! Round 1's Developer spent 140 model calls, 54.4 minutes and 10.4M prompt
//! tokens and ended with `RepeatedFormatError` — and that string was the *only*
//! place the failure was visible, because it is an exit status of the external
//! coding agent and appeared nowhere in this crate.  A round in which a role
//! never managed to write its declared artifact therefore could not be told
//! apart, from the harness's own records, from one in which it wrote everything
//! and stopped cleanly.
//!
//! This module turns the measurement the runtime already has — "did the artifact
//! tree change?" / "is the declared file there?" — plus the attempt's exit
//! status and token usage, into a first-class [`RoleWriteFailure`] that is
//! persisted in the round result and in `warnings.log`.
//!
//! Two rules keep it honest:
//!
//! * A role that **did** write its artifact produces no entry, whatever its exit
//!   status was: the fact under judgement is the artifact, not the agent's mood.
//! * An entry is only produced for a status the runtime knows is a failure, or
//!   for a call that spent more than `agent.artifact_write_budget_tokens`
//!   without writing.  An unknown status is never quietly reclassified.

use serde::{Deserialize, Serialize};

use crate::model::Role;

/// The Developer's declared artifact: a file inside the project.
pub const DECLARED_DEVELOPER: &str =
    "a file inside the project (the candidate increment, outside the hash-excluded paths)";
/// The Planner's declared artifact.
pub const DECLARED_PLANNER: &str = ".hoh/plan.md";
/// The Tester's declared artifact.
pub const DECLARED_TESTER: &str = ".hoh/evidence.json";

/// The exit statuses that mean "this call did not finish the work it was given".
///
/// `RepeatedFormatError` is mini's; `RepeatedActionError` and
/// `ArtifactBudgetExceeded` are ours (`crate::harness::guard`).  `LimitsExceeded`
/// and `TimeExceeded` are the two budgets mini itself enforces.
pub fn is_failure_status(status: &str) -> bool {
    matches!(
        status,
        "LimitsExceeded"
            | "TimeExceeded"
            | "RepeatedFormatError"
            | "RepeatedActionError"
            | "ArtifactBudgetExceeded"
    )
}

/// One role call that did not write the artifact it declared.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct RoleWriteFailure {
    pub role: Role,
    pub attempt: u32,
    /// The call's exit status, verbatim (`LimitsExceeded`, `RepeatedFormatError`,
    /// …).  It is evidence, not the judgement.
    pub exit_status: String,
    /// What the role was supposed to write.
    pub declared_artifact: String,
    /// Always `false`: an entry only exists when the artifact was not written.
    pub artifact_written: bool,
    /// The runtime's own sentence about what this means.
    pub reason: String,
}

impl RoleWriteFailure {
    /// The one-line form written into `warnings.log`.
    pub fn render(&self) -> String {
        format!(
            "role_write_failure: {} attempt {} ended `{}` without writing {}: {}",
            self.role.as_str(),
            self.attempt,
            self.exit_status,
            self.declared_artifact,
            self.reason
        )
    }
}

/// Assess one role attempt.
///
/// `artifact_written` is the runtime's own measurement of the artifact tree (the
/// Developer's before/after hashes, the Planner's/Tester's declared file), never
/// the agent's claim.  `total_tokens` is the attempt's recorded usage when it is
/// known.
pub fn assess(
    role: Role,
    attempt: u32,
    exit_status: &str,
    artifact_written: bool,
    declared_artifact: &str,
    total_tokens: Option<u64>,
    token_budget: u64,
) -> Option<RoleWriteFailure> {
    if artifact_written {
        return None;
    }
    let status = exit_status.trim();
    if is_failure_status(status) {
        return Some(RoleWriteFailure {
            role,
            attempt,
            exit_status: status.to_string(),
            declared_artifact: declared_artifact.to_string(),
            artifact_written: false,
            reason: format!(
                "the call ended with `{status}` and the artifact tree shows no write to {}",
                declared_artifact
            ),
        });
    }
    if token_budget > 0 {
        if let Some(tokens) = total_tokens.filter(|tokens| *tokens >= token_budget) {
            return Some(RoleWriteFailure {
                role,
                attempt,
                exit_status: if status.is_empty() {
                    "unknown".to_string()
                } else {
                    status.to_string()
                },
                declared_artifact: declared_artifact.to_string(),
                artifact_written: false,
                reason: format!(
                    "the call spent {tokens} token(s) without writing {}, over the \
                     `agent.artifact_write_budget_tokens` budget of {token_budget}",
                    declared_artifact
                ),
            });
        }
    }
    None
}

/// Assess a whole batch of attempts of one role.
pub fn assess_all(
    attempts: &[crate::runtime::schema::AttemptOutcome],
    artifact_written: bool,
    declared_artifact: &str,
    token_budget: u64,
) -> Vec<RoleWriteFailure> {
    attempts
        .iter()
        .filter_map(|attempt| {
            assess(
                attempt.role,
                attempt.attempt,
                &attempt.exit_status,
                artifact_written,
                declared_artifact,
                attempt.usage.total_tokens,
                token_budget,
            )
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn a_role_that_wrote_its_artifact_is_never_reported() {
        assert!(assess(
            Role::Developer,
            1,
            "RepeatedFormatError",
            true,
            DECLARED_DEVELOPER,
            Some(10_000_000),
            1_500_000,
        )
        .is_none());
    }

    #[test]
    fn a_failed_call_that_wrote_nothing_is_a_first_class_fact() {
        let failure = assess(
            Role::Developer,
            1,
            "RepeatedFormatError",
            false,
            DECLARED_DEVELOPER,
            Some(10_379_180),
            1_500_000,
        )
        .expect("round 1's shape");
        assert_eq!(failure.role, Role::Developer);
        assert_eq!(failure.attempt, 1);
        assert!(!failure.artifact_written);
        assert!(
            failure.reason.contains("RepeatedFormatError"),
            "{failure:?}"
        );
        assert!(failure.reason.contains("no write"), "{failure:?}");
        assert!(failure.render().contains("role_write_failure"));
        assert!(failure.render().contains("RepeatedFormatError"));
        // The serialized form is what the round result carries.
        let json = serde_json::to_value(&failure).expect("serializable");
        assert_eq!(json["role"], "developer");
        assert_eq!(json["artifact_written"], false);
    }

    #[test]
    fn our_own_statuses_are_failures_too() {
        for status in [
            "LimitsExceeded",
            "TimeExceeded",
            "RepeatedFormatError",
            "RepeatedActionError",
            "ArtifactBudgetExceeded",
        ] {
            assert!(is_failure_status(status), "{status}");
        }
        for status in ["", "Submitted", "Completed", "unknown"] {
            assert!(!is_failure_status(status), "{status:?}");
        }
    }

    #[test]
    fn an_unknown_status_is_not_reclassified_unless_the_token_budget_was_blown() {
        assert!(assess(
            Role::Tester,
            1,
            "Completed",
            false,
            DECLARED_TESTER,
            Some(10),
            1_500_000
        )
        .is_none());
        let over = assess(
            Role::Tester,
            1,
            "Completed",
            false,
            DECLARED_TESTER,
            Some(2_000_000),
            1_500_000,
        )
        .expect("the token budget is the runtime's own measurement");
        assert!(over.reason.contains("2000000"), "{}", over.reason);
        assert!(over.reason.contains("artifact_write_budget_tokens"));
    }

    #[test]
    fn a_zero_token_budget_disables_the_token_half() {
        assert!(assess(
            Role::Developer,
            1,
            "Completed",
            false,
            DECLARED_DEVELOPER,
            Some(u64::MAX),
            0
        )
        .is_none());
    }
}
