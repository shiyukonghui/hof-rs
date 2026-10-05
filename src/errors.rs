//! Typed runtime errors and their CLI exit-code mapping.
//!
//! Exit codes (`DESIGN-DETAIL.md` §8):
//! `0` success, `2` contract/usage error, `3` schema retries exhausted,
//! `4` external dependency unavailable, `5` harness/model error.

use thiserror::Error;

use crate::model::{ContractViolation, Role, SchemaIssue};

#[derive(Debug, Error)]
pub enum HofError {
    #[error("configuration error: {0}")]
    Config(String),

    /// DR-14: the violation carries the offending **configuration values**
    /// rather than a hard-coded model name.  `actual` must never contain secret
    /// material (C11).
    #[error("model identity violation: {reason}; expected `{expected}`, got `{actual}`")]
    ModelIdentityViolation {
        reason: String,
        expected: String,
        actual: String,
    },

    #[error("contract violation: {violation:?} ({code})")]
    Contract {
        violation: ContractViolation,
        code: &'static str,
    },

    #[error("schema failure for role {role:?} after {attempts} attempt(s)")]
    SchemaFailure {
        role: Role,
        attempts: u32,
        issues: Vec<Vec<SchemaIssue>>,
    },

    #[error("external dependency unavailable: {0}")]
    External(String),

    #[error("harness error: {0}")]
    Harness(String),

    #[error("adapter error: {0}")]
    Adapter(String),

    /// DR-8: `status` asked for a runs directory or run id that does not exist.
    /// A usage error is exit 2; exit 5 is reserved for harness/model failures.
    #[error("run not found: {0}")]
    RunNotFound(String),

    /// DR-8: `rollback` asked for a version that has no snapshot.  Exit 2.
    #[error("version not found: {0}")]
    VersionNotFound(String),

    /// DR-29: the server answered, but never with the id we asked for.  The
    /// payloads that did arrive were parked, never used; the caller must treat
    /// the call as a failure (and may never silently substitute another id's
    /// `result`).
    #[error(
        "MCP response desync: request id {expected_id} was never answered; received id(s) \
         {got_ids:?} after {sync_probes} probe(s)"
    )]
    McpResponseDesync {
        expected_id: u64,
        got_ids: Vec<u64>,
        sync_probes: u32,
    },

    #[error("tool_not_permitted: role={role} tool={tool}")]
    ToolNotPermitted { role: String, tool: String },
}

impl HofError {
    pub fn contract(violation: ContractViolation) -> Self {
        HofError::Contract {
            violation,
            code: violation.code(),
        }
    }

    pub fn exit_code(&self) -> i32 {
        match self {
            HofError::Config(_)
            | HofError::ModelIdentityViolation { .. }
            | HofError::Contract { .. }
            | HofError::RunNotFound(_)
            | HofError::VersionNotFound(_)
            | HofError::ToolNotPermitted { .. }
            | HofError::Adapter(_) => 2,
            HofError::SchemaFailure { .. } => 3,
            // DR-29: a desynchronized MCP endpoint is an unavailable external
            // dependency, not a harness bug.
            HofError::External(_) | HofError::McpResponseDesync { .. } => 4,
            HofError::Harness(_) => 5,
        }
    }
}

/// Extract the typed error from an `anyhow` chain, if any.
pub fn as_hof_error(error: &anyhow::Error) -> Option<&HofError> {
    error.downcast_ref::<HofError>()
}

/// Exit code for an arbitrary `anyhow` error.
pub fn exit_code_of(error: &anyhow::Error) -> i32 {
    as_hof_error(error).map(HofError::exit_code).unwrap_or(5)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exit_codes_match_the_design() {
        assert_eq!(HofError::Config("x".into()).exit_code(), 2);
        assert_eq!(
            HofError::ModelIdentityViolation {
                reason: "model.provider must be explicit (C10)".into(),
                expected: "openai_compatible".into(),
                actual: "aliyun".into()
            }
            .exit_code(),
            2
        );
        assert_eq!(
            HofError::contract(ContractViolation::ReadOnlyRoleWroteArtifact).exit_code(),
            2
        );
        // Round-5 repair: `ResumeNotImplemented` is gone — `--resume` is
        // implemented, and the exit code its refusal used to carry (2, a usage
        // error) is the one its precondition failures carry now.
        assert_eq!(
            HofError::Config(
                "--resume: runs/round4 does not exist, so there is no interrupted round to \
                 continue"
                    .into()
            )
            .exit_code(),
            2
        );
        assert_eq!(HofError::RunNotFound("runs".into()).exit_code(), 2);
        assert_eq!(HofError::VersionNotFound("abc".into()).exit_code(), 2);
        assert_eq!(
            HofError::SchemaFailure {
                role: Role::Planner,
                attempts: 3,
                issues: vec![]
            }
            .exit_code(),
            3
        );
        assert_eq!(HofError::External("godot".into()).exit_code(), 4);
        assert_eq!(
            HofError::McpResponseDesync {
                expected_id: 2,
                got_ids: vec![1],
                sync_probes: 4
            }
            .exit_code(),
            4
        );
        assert_eq!(HofError::Harness("boom".into()).exit_code(), 5);
    }

    #[test]
    fn anyhow_downcast_finds_the_typed_error() {
        let error: anyhow::Error = HofError::RunNotFound("runs/round4".into()).into();
        assert!(matches!(
            as_hof_error(&error),
            Some(HofError::RunNotFound(_))
        ));
        assert_eq!(exit_code_of(&error), 2);
    }
}
