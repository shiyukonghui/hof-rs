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

    #[error(
        "model identity violation: expected model_name `openai/qwen/qwen3.8-27b` and provider \
         `openai_compatible`, got model_name `{model_name}` / provider `{provider}` (C9/C10)"
    )]
    ModelIdentityViolation {
        model_name: String,
        provider: String,
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

    #[error("resume_not_implemented")]
    ResumeNotImplemented,

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
            | HofError::ResumeNotImplemented
            | HofError::ToolNotPermitted { .. }
            | HofError::Adapter(_) => 2,
            HofError::SchemaFailure { .. } => 3,
            HofError::External(_) => 4,
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
                model_name: "qwen/qwen3.8-27b".into(),
                provider: "openai_compatible".into()
            }
            .exit_code(),
            2
        );
        assert_eq!(
            HofError::contract(ContractViolation::ReadOnlyRoleWroteArtifact).exit_code(),
            2
        );
        assert_eq!(HofError::ResumeNotImplemented.exit_code(), 2);
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
        assert_eq!(HofError::Harness("boom".into()).exit_code(), 5);
    }

    #[test]
    fn anyhow_downcast_finds_the_typed_error() {
        let error: anyhow::Error = HofError::ResumeNotImplemented.into();
        assert!(matches!(
            as_hof_error(&error),
            Some(HofError::ResumeNotImplemented)
        ));
        assert_eq!(exit_code_of(&error), 2);
    }
}
