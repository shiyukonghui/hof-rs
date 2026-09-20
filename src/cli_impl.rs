//! Subcommand implementations.  Kept separate from `cli.rs` so the clap
//! surface stays declarative and the `hoh` binary entry point stays tiny.

use crate::cli::config_specs;
use crate::cli::{DoctorArgs, RollbackArgs, SpecHashArgs, StatusArgs, SubmitArgs, ToolsArgs};
use crate::config::load_spec;
use crate::errors::HofError;

pub async fn spec_hash(args: SpecHashArgs) -> anyhow::Result<i32> {
    let path = args
        .spec
        .unwrap_or_else(|| std::path::PathBuf::from(".spec/hof-rs/PRD-mario.md"));
    let spec = load_spec(&path)?;
    println!("{}", spec.sha256);
    Ok(0)
}

pub async fn tools(_args: ToolsArgs) -> anyhow::Result<i32> {
    Err(HofError::Config("tools channel is not wired yet".to_string()).into())
}

pub async fn submit(_args: SubmitArgs) -> anyhow::Result<i32> {
    Err(HofError::Config("submit is not wired yet".to_string()).into())
}

pub async fn doctor(_args: DoctorArgs) -> anyhow::Result<i32> {
    Err(HofError::Config("doctor is not wired yet".to_string()).into())
}

pub async fn run(_args: crate::cli::RunArgs) -> anyhow::Result<i32> {
    Err(HofError::Config("run is not wired yet".to_string()).into())
}

pub async fn status(_args: StatusArgs) -> anyhow::Result<i32> {
    Err(HofError::Config("status is not wired yet".to_string()).into())
}

pub async fn rollback(_args: RollbackArgs) -> anyhow::Result<i32> {
    Err(HofError::Config("rollback is not wired yet".to_string()).into())
}

/// Helper shared by the subcommands that need a loaded config.
pub fn load_with(overrides: &[String]) -> anyhow::Result<crate::config::HohConfig> {
    crate::config::load_config(&config_specs(overrides))
}
