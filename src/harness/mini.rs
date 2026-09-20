//! The concrete harness: one fresh `mini_swe_agent::DefaultAgent` per call.
//!
//! Two details are load-bearing and must not be "simplified":
//!
//! 1. `system_template` / `instance_template` are *fixed* placeholders; the
//!    role text travels as **template variable values**.  Values are never
//!    re-parsed by minijinja, whereas text spliced into a template would be
//!    (evidence JSON and GDScript both contain `{`).
//! 2. `AgentConfig::cost_limit` is taken from limits and the default config
//!    sets it to `0.0`: mini's own default of `3.0` would abort a local run
//!    with `LimitsExceeded`.

use std::time::Instant;

use mini_swe_agent::environments::{LocalEnvironment, LocalEnvironmentConfig};
use mini_swe_agent::models::{ApiMode, LlmConnectorModel};
use mini_swe_agent::{Agent, AgentConfig, AgentError, AgentMode, DefaultAgent};
use serde_json::Value;

use crate::harness::Harness;
use crate::runtime::role::{RoleInvocation, RoleOutcome};
use crate::runtime::usage::extract_usage;

#[derive(Debug, Default)]
pub struct MiniHarness;

impl MiniHarness {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait::async_trait]
impl Harness for MiniHarness {
    async fn invoke(&self, inv: &RoleInvocation) -> anyhow::Result<RoleOutcome> {
        let model = LlmConnectorModel::from_value_with_mode(inv.model.clone(), ApiMode::ToolCalls)
            .map_err(|error| anyhow::anyhow!("could not build the model: {error}"))?;

        let env_config = LocalEnvironmentConfig {
            cwd: inv.cwd.to_string_lossy().into_owned(),
            timeout: inv.limits.command_timeout_seconds,
            env: inv
                .env
                .iter()
                .map(|(key, value)| (key.clone(), Value::String(value.clone())))
                .collect(),
        };
        let environment = LocalEnvironment::new(env_config);

        let config = AgentConfig {
            system_template: "{{hoh_system_prompt}}".to_string(),
            instance_template: "{{task}}".to_string(),
            step_limit: inv.limits.step_limit,
            cost_limit: inv.limits.cost_limit,
            wall_time_limit_seconds: inv.limits.wall_time_limit_seconds,
            max_consecutive_format_errors: inv.limits.max_consecutive_format_errors,
            output_path: Some(inv.trajectory_path.clone()),
            mode: AgentMode::Yolo,
            whitelist_actions: Vec::new(),
            confirm_exit: false,
        };

        if let Some(parent) = inv.trajectory_path.parent() {
            std::fs::create_dir_all(parent).map_err(|error| {
                anyhow::anyhow!(
                    "could not create trajectory directory {}: {error}",
                    parent.display()
                )
            })?;
        }

        let mut agent = DefaultAgent::new(Box::new(model), Box::new(environment), config);
        let task_text = match &inv.retry_context {
            Some(context) => format!("{}\n\n---\n\n{}", inv.task_prompt, context),
            None => inv.task_prompt.clone(),
        };
        let kwargs = serde_json::json!({ "hoh_system_prompt": inv.system_prompt });

        let started = Instant::now();
        let result = agent.run(&task_text, Some(kwargs)).await;
        let duration_ms = started.elapsed().as_millis() as u64;

        match result {
            // Interrupt is one of the normal termination paths (submit, limits).
            Ok(_) | Err(AgentError::Interrupt(_)) | Err(AgentError::Format(_)) => {}
            Err(AgentError::Other(error)) => {
                return Err(anyhow::anyhow!(
                    "harness failed for role {} iteration {}: {error}",
                    inv.role.as_str(),
                    inv.iteration
                ));
            }
        }

        let last = agent.messages.last();
        let exit_status = last
            .map(|message| message.exit_status().to_string())
            .unwrap_or_default();
        let submission = last
            .map(|message| message.submission().to_string())
            .unwrap_or_default();

        // The trajectory is the source of truth for usage (D2/C8).
        let usage = extract_usage(&inv.trajectory_path, inv.role, inv.iteration)?;

        Ok(RoleOutcome {
            role: inv.role,
            iteration: inv.iteration,
            attempts: 1,
            exit_status,
            submission,
            trajectory_path: inv.trajectory_path.clone(),
            usage,
            duration_ms,
        })
    }
}
