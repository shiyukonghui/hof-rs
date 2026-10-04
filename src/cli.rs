//! clap definition and subcommand dispatch for the `hoh` binary.

use std::path::PathBuf;
use std::process::ExitCode;

use clap::{Parser, Subcommand};

use crate::config::DEFAULT_CONFIG_SPEC;
use crate::errors::exit_code_of;

#[derive(Parser, Debug)]
#[command(name = "hoh", version, about = "Harness-of-Harness runtime")]
pub struct Cli {
    #[command(subcommand)]
    pub command: Command,
}

#[derive(Subcommand, Debug)]
pub enum Command {
    Run(RunArgs),
    Doctor(DoctorArgs),
    Status(StatusArgs),
    Rollback(RollbackArgs),
    Tools(ToolsArgs),
    Submit(SubmitArgs),
    SpecHash(SpecHashArgs),
    Init(InitArgs),
}

#[derive(clap::Args, Debug, Clone)]
pub struct RunArgs {
    #[arg(long)]
    pub spec: Option<PathBuf>,
    #[arg(long)]
    pub project: Option<PathBuf>,
    #[arg(long, default_value_t = 3)]
    pub iterations: u32,
    #[arg(long)]
    pub run_id: Option<String>,
    #[arg(long, default_value = "test")]
    pub adapter: String,
    #[arg(short = 'c', long = "config")]
    pub config_spec: Vec<String>,
    #[arg(long, default_value_t = 2)]
    pub max_schema_retries: u32,
    /// Ablation switches, e.g. `--ablate plan_update=false`.
    #[arg(long)]
    pub ablate: Vec<String>,
    /// Destructive: scaffold `A0` even when the workspace already contains a
    /// non-empty, non-scaffold directory (existing files can be overwritten).
    /// Never needed for an already initialized workspace: `initialize`
    /// is idempotent (DR-9).
    #[arg(long)]
    pub force_init: bool,
    /// DR-21: empty the configured workspace and rebuild `A₀` before running.
    /// The workspace directory must already exist; it is never created or
    /// guessed, and no path outside it is ever touched.
    #[arg(long)]
    pub fresh_workspace: bool,
    /// DR-21: roll the workspace back to this run's `A₀` snapshot before
    /// running.  Fails (without touching the workspace) when no such snapshot
    /// exists.
    #[arg(long)]
    pub reset_workspace: bool,
    #[arg(long)]
    pub resume: bool,
}

#[derive(clap::Args, Debug, Clone)]
pub struct DoctorArgs {
    #[arg(long)]
    pub project: Option<PathBuf>,
    #[arg(long, default_value = "test")]
    pub adapter: String,
    #[arg(short = 'c', long = "config")]
    pub config_spec: Vec<String>,
}

/// DR-40: prepare `A₀` **without** the editor or the model.
///
/// The circular dependency that made this necessary: emptying and rebuilding
/// `A₀` requires the editor to be closed, but `hoh run` refuses to start until
/// the doctor pre-check can reach the editor's MCP endpoint.
///
/// This subcommand therefore only ever calls `ProjectAdapter::initialize` (plus
/// the optional purge): no model endpoint probe, no MCP probe, no API key.
#[derive(clap::Args, Debug, Clone)]
pub struct InitArgs {
    #[arg(long)]
    pub project: Option<PathBuf>,
    #[arg(long, default_value = "test")]
    pub adapter: String,
    #[arg(short = 'c', long = "config")]
    pub config_spec: Vec<String>,
    /// Empty the configured workspace before rebuilding `A₀` (DR-21 semantics).
    #[arg(long)]
    pub fresh_workspace: bool,
    /// Allow scaffolding over a non-empty, non-scaffold directory.
    #[arg(long)]
    pub force_init: bool,
}

#[derive(clap::Args, Debug, Clone)]
pub struct StatusArgs {
    #[arg(long)]
    pub run_id: Option<String>,
    #[arg(long)]
    pub runs_dir: Option<PathBuf>,
}

#[derive(clap::Args, Debug, Clone)]
pub struct RollbackArgs {
    #[arg(long)]
    pub run_id: String,
    #[arg(long)]
    pub to: String,
    #[arg(long)]
    pub project: Option<PathBuf>,
    #[arg(long)]
    pub runs_dir: Option<PathBuf>,
}

#[derive(clap::Args, Debug, Clone)]
pub struct ToolsArgs {
    #[command(subcommand)]
    pub command: ToolsCommand,
}

#[derive(Subcommand, Debug, Clone)]
pub enum ToolsCommand {
    /// Call one MCP tool through the role-scoped policy gate.
    Call(ToolsCallArgs),
    /// List the MCP tools visible to a role.
    List(ToolsListArgs),
    /// Describe one MCP tool.
    Describe(ToolsDescribeArgs),
}

#[derive(clap::Args, Debug, Clone)]
pub struct ToolsCallArgs {
    pub tool: String,
    #[arg(long)]
    pub args: Option<String>,
    #[arg(long)]
    pub args_file: Option<PathBuf>,
    #[arg(long)]
    pub role: Option<String>,
    #[arg(short = 'c', long = "config")]
    pub config_spec: Vec<String>,
}

#[derive(clap::Args, Debug, Clone)]
pub struct ToolsListArgs {
    #[arg(long)]
    pub role: Option<String>,
    #[arg(short = 'c', long = "config")]
    pub config_spec: Vec<String>,
}

#[derive(clap::Args, Debug, Clone)]
pub struct ToolsDescribeArgs {
    pub tool: String,
    #[arg(short = 'c', long = "config")]
    pub config_spec: Vec<String>,
}

#[derive(clap::Args, Debug, Clone)]
pub struct SubmitArgs {
    #[arg(long)]
    pub role: String,
    #[arg(long)]
    pub file: PathBuf,
}

#[derive(clap::Args, Debug, Clone)]
pub struct SpecHashArgs {
    #[arg(long)]
    pub spec: Option<PathBuf>,
}

/// Build the ordered config spec list (file first, CLI overrides last).
pub fn config_specs(overrides: &[String]) -> Vec<String> {
    let mut specs = vec![DEFAULT_CONFIG_SPEC.to_string()];
    specs.extend(overrides.iter().cloned());
    specs
}

/// Entry point used by `main.rs`; never panics, always returns an exit code.
pub async fn main_entry() -> ExitCode {
    let cli = Cli::parse();
    let code = match dispatch(cli).await {
        Ok(code) => code,
        Err(error) => {
            eprintln!("hoh: {error:#}");
            exit_code_of(&error)
        }
    };
    ExitCode::from(code as u8)
}

pub async fn dispatch(cli: Cli) -> anyhow::Result<i32> {
    match cli.command {
        Command::SpecHash(args) => crate::cli_impl::spec_hash(args).await,
        Command::Tools(args) => crate::cli_impl::tools(args).await,
        Command::Submit(args) => crate::cli_impl::submit(args).await,
        Command::Doctor(args) => crate::cli_impl::doctor(args).await,
        Command::Init(args) => crate::cli_impl::init(args).await,
        Command::Run(args) => crate::cli_impl::run(args).await,
        Command::Status(args) => crate::cli_impl::status(args).await,
        Command::Rollback(args) => crate::cli_impl::rollback(args).await,
    }
}

/// Parse `--ablate name=false` into an [`crate::model::Ablation`].
pub fn parse_ablation(specs: &[String]) -> anyhow::Result<crate::model::Ablation> {
    let mut ablation = crate::model::Ablation::default();
    for spec in specs {
        let (name, value) = spec.split_once('=').ok_or_else(|| {
            anyhow::anyhow!("invalid ablation `{spec}`: expected name=true|false")
        })?;
        let enabled = match value.trim().to_ascii_lowercase().as_str() {
            "true" | "1" | "on" => true,
            "false" | "0" | "off" => false,
            other => anyhow::bail!("invalid ablation value `{other}` for `{name}`"),
        };
        match name.trim() {
            "plan_update" => ablation.plan_update = enabled,
            "evidence_feedback" => ablation.evidence_feedback = enabled,
            "warm_start" => ablation.warm_start = enabled,
            other => anyhow::bail!("unknown ablation switch `{other}`"),
        }
    }
    Ok(ablation)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::load_config;
    use crate::errors::{as_hof_error, HofError};

    #[test]
    fn doctor_rejects_invalid_model_identity() {
        // C9/C10/C11 + DR-14: a missing explicit provider, a blank
        // `wire_model_name`, or a secret in the file must be rejected before
        // any run starts.  The check knows no concrete model name.
        let specs = config_specs(&["model.provider=aliyun".to_string()]);
        let error = load_config(&specs).expect_err("implicit provider must be rejected");
        let hof = as_hof_error(&error).expect("typed error");
        assert!(matches!(hof, HofError::ModelIdentityViolation { .. }));
        assert_eq!(hof.exit_code(), 2);

        let specs = config_specs(&["model.wire_model_name=".to_string()]);
        let error = load_config(&specs).expect_err("blank wire id must be rejected");
        assert!(matches!(
            as_hof_error(&error),
            Some(HofError::ModelIdentityViolation { .. })
        ));

        let specs = config_specs(&["model.api_key=must-not-be-stored".to_string()]);
        let error = load_config(&specs).expect_err("a config secret must be rejected (C11)");
        assert!(matches!(
            as_hof_error(&error),
            Some(HofError::ModelIdentityViolation { .. })
        ));
    }

    #[test]
    fn ablation_parsing_is_strict() {
        let ablation = parse_ablation(&["plan_update=false".to_string()]).unwrap();
        assert!(!ablation.plan_update);
        assert!(ablation.evidence_feedback);
        assert!(ablation.warm_start);
        assert!(parse_ablation(&["nope=false".to_string()]).is_err());
        assert!(parse_ablation(&["plan_update=maybe".to_string()]).is_err());
    }
}
