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
use mini_swe_agent::{
    Agent, AgentConfig, AgentError, AgentMode, DefaultAgent, Message, Model, Output,
};
use serde_json::Value;

use crate::harness::Harness;
use crate::runtime::role::{RoleInvocation, RoleOutcome};
use crate::runtime::usage::extract_usage;

/// Round-4 repair: a model that counts its own calls, so the step budget the
/// guard enforces is stated in the **same unit the prompt uses**.
///
/// mini's `DefaultAgent::check_limits` counts model calls (`n_calls`) and
/// `AgentConfig.step_limit` is written in that unit.  The guard sits one layer
/// below, where a single model response can carry several actions, so counting
/// there measures something else — measured, not assumed: round 4's first attempt
/// cut a Developer call after 30 model calls because its 30 responses emitted 44
/// actions.  This wrapper is where the count is taken, and the guard reads the
/// same counter.
struct CountingModel {
    inner: Box<dyn Model>,
    steps: crate::harness::guard::StepCounter,
}

impl CountingModel {
    fn new(inner: Box<dyn Model>, steps: crate::harness::guard::StepCounter) -> Self {
        Self { inner, steps }
    }
}

#[async_trait::async_trait]
impl Model for CountingModel {
    fn model_name(&self) -> &str {
        self.inner.model_name()
    }

    async fn query(
        &self,
        messages: &[Message],
        kwargs: Option<Value>,
    ) -> mini_swe_agent::Result<Message> {
        // The count is taken **before** the call, exactly as mini takes it: a
        // failed query still consumed a step, so a broken provider cannot make a
        // call's budget disappear.
        self.steps.increment();
        self.inner.query(messages, kwargs).await
    }

    fn format_message(&self, message: Message) -> mini_swe_agent::Result<Message> {
        self.inner.format_message(message)
    }

    fn format_observation_messages(
        &self,
        message: &Message,
        outputs: &[Output],
        template_vars: &Value,
    ) -> mini_swe_agent::Result<Vec<Message>> {
        self.inner
            .format_observation_messages(message, outputs, template_vars)
    }

    fn get_template_vars(&self) -> Value {
        self.inner.get_template_vars()
    }

    fn serialize(&self) -> Value {
        self.inner.serialize()
    }
}

/// Round-1 write-path batch: what one finished `agent.run` means.
///
/// The three normal terminations (a submit, a limits/time interrupt, a format
/// error) are not failures of the harness; a fail-fast abort carried in an
/// `AgentError::Other` is our **own** first-class status; anything else is an
/// infrastructure failure and stays an error.
///
/// It is a free function so the mapping can be pinned without a model: the
/// branch that turns `HOH_FAIL_FAST <STATUS>` into `RoleOutcome::exit_status` is
/// the whole point of the sentinel, and a test can build the same
/// `AgentError::Other` mini would.
pub fn classify_run_result(
    result: mini_swe_agent::Result<serde_json::Value>,
) -> Result<Option<&'static str>, String> {
    match result {
        // `Interrupt` is one of the normal termination paths (submit, limits).
        Ok(_) | Err(AgentError::Interrupt(_)) | Err(AgentError::Format(_)) => Ok(None),
        Err(AgentError::Other(error)) => {
            match crate::harness::guard::fail_fast_status(&error.to_string()) {
                Some(status) => Ok(Some(status)),
                None => Err(error.to_string()),
            }
        }
    }
}

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
        // DR-14: fail fast on an undeclared wire identity.  `hoh doctor` and the
        // offline double-lock test verify the *actual* traffic; this guard makes
        // a missing declaration a configuration error instead of a silent run
        // against an unspecified model.
        let wire = crate::config::wire_model_name_of(&inv.model);
        if wire.trim().is_empty() {
            anyhow::bail!(
                "model.wire_model_name is empty for role {} iteration {}; the on-the-wire model \
                 id must be declared in configuration (DR-14)",
                inv.role.as_str(),
                inv.iteration
            );
        }

        let model = LlmConnectorModel::from_value_with_mode(inv.model.clone(), ApiMode::ToolCalls)
            .map_err(|error| anyhow::anyhow!("could not build the model: {error}"))?;
        // Round-4 repair: one step is one **model call**, counted where the calls
        // are made, and the guard enforces the budget on the same count.
        let steps = crate::harness::guard::StepCounter::new();
        let model = CountingModel::new(Box::new(model), steps.clone());

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
        // DR-69 ③: bound every tool result before it can become the next
        // request's observation.  Attempt A of `smoke-t9` died because a single
        // 15,570,803-byte result was replayed in full.
        let environment = crate::harness::cap::CappedEnvironment::new(
            Box::new(environment),
            inv.limits.max_tool_output_bytes as usize,
        );
        // Round-1 write-path batch: the first-class write/read path plus the two
        // fail-fast guards.  It sits **outside** the cap so a directive's output
        // is produced by the harness itself and a repeated failing action aborts
        // the call with our own status instead of the external agent's string.
        //
        // Round-2 repair (cost batch), round-4 repair: the guard is constructed
        // with the repeated-success tripwire and with the step budget, and it is
        // the guard — not a number frozen into `AgentConfig` before the call —
        // that **enforces** the progress-responsive budget, at the step.
        let environment = crate::harness::guard::WriteGuardEnvironment::with_limits(
            Box::new(environment),
            inv.cwd.clone(),
            inv.limits.max_action_failures as u32,
            inv.limits.artifact_write_budget_seconds,
            crate::harness::guard::ArtifactKind::for_role(inv.role),
            inv.limits.max_repeated_actions,
            inv.limits.step_limit,
            inv.limits.wrap_up_steps,
            inv.limits.steps_per_artifact,
        )
        // The counter the model increments: the guard's step number is the
        // prompt's step number, and both are model calls.
        .sharing_steps(steps);
        // Round-4 repair: mini's own `step_limit` is the **flat ceiling** — the
        // number the prompt body calls "at most N steps" — and the progress gate
        // is enforced by the guard, at the step, against a value it re-reads every
        // time.  Round 3 set this field to the *gated* 43, so the gate could never
        // lift: the model was told a write would remove the gate and then the call
        // was killed at 43 anyway (`ROUND-3-REPORT.md` §2).
        let flat_step_limit = inv.limits.step_limit;
        let live_step_limit = if flat_step_limit == 0 {
            0
        } else {
            environment.effective_step_budget().min(flat_step_limit)
        };
        // The prompt's numbers must be the numbers the call is held to: the body's
        // flat ceiling, and the gated budget that is really in force right now.
        // The system prompt was already rendered by the caller, so this is a
        // **narrow numeric substitution** — re-rendering the whole template here
        // would apply the shell-variable pass a second time.
        let system_prompt = crate::harness::guard::state_the_effective_budget(
            &inv.system_prompt,
            live_step_limit,
            flat_step_limit,
            inv.limits.wrap_up_steps,
        );

        let config = AgentConfig {
            system_template: "{{hoh_system_prompt}}".to_string(),
            instance_template: "{{task}}".to_string(),
            step_limit: flat_step_limit,
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
        let kwargs = serde_json::json!({ "hoh_system_prompt": system_prompt });

        let started = Instant::now();
        let result = agent.run(&task_text, Some(kwargs)).await;
        let duration_ms = started.elapsed().as_millis() as u64;

        // Round-1 write-path batch: a fail-fast abort is **our** judgement, not
        // an infrastructure failure.  `agent.run` reports it as
        // `AgentError::Other` because that is the only channel an environment
        // has; the status embedded in the message is recovered here and becomes
        // the call's `exit_status`, so the round result carries a first-class
        // fact instead of the external agent's string.
        let fail_fast = match classify_run_result(result) {
            Ok(status) => status,
            Err(message) => {
                return Err(anyhow::anyhow!(
                    "harness failed for role {} iteration {}: {message}",
                    inv.role.as_str(),
                    inv.iteration
                ));
            }
        };

        let last = agent.messages.last();
        let exit_status = match fail_fast {
            Some(status) => status.to_string(),
            None => last
                .map(|message| message.exit_status().to_string())
                .unwrap_or_default(),
        };
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

#[cfg(test)]
mod tests {
    use super::*;

    fn fail_fast_error(status: &str) -> AgentError {
        AgentError::other(anyhow::anyhow!(
            "{} {status}: the same action failed 3 time(s)",
            crate::harness::guard::FAIL_FAST_MARKER
        ))
    }

    /// The sentinel survives mini's opaque `AgentError::Other` and becomes a
    /// first-class status — that is the whole reason it exists.
    #[test]
    fn a_fail_fast_abort_becomes_a_first_class_exit_status() {
        for status in [
            crate::harness::guard::REPEATED_ACTION_STATUS,
            crate::harness::guard::ARTIFACT_BUDGET_STATUS,
        ] {
            assert_eq!(
                classify_run_result(Err(fail_fast_error(status))),
                Ok(Some(status)),
                "`{status}` must be recovered from the message"
            );
        }
    }

    /// A real infrastructure failure stays an error: the harness must not relabel
    /// it as a role-completion status.
    #[test]
    fn an_infrastructure_failure_is_still_an_error() {
        let error = AgentError::other(anyhow::anyhow!("llm-connector chat request failed"));
        let message = classify_run_result(Err(error)).expect_err("not a role status");
        assert!(message.contains("chat request failed"), "{message}");
    }

    /// The three normal terminations are not failures of the harness.
    #[test]
    fn a_normal_termination_carries_no_invented_status() {
        assert_eq!(classify_run_result(Ok(serde_json::Value::Null)), Ok(None));
        let interrupt = mini_swe_agent::FlowInterrupt::limits_exceeded();
        assert_eq!(
            classify_run_result(Err(AgentError::Interrupt(interrupt))),
            Ok(None)
        );
    }
}
