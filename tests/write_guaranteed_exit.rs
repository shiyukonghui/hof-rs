//! The **write-guaranteed exit** (cost batch, after
//! `LIVE-COMPLETION-MEASUREMENT.md`).
//!
//! The measurement that motivates this file, in one sentence: a Developer call
//! must come in under 1,500,000 tokens, the zero-context floor for a 150-call
//! live call is 2,077,238, so the criterion needs a *call bound*, and the only
//! recorded call that came in under the criterion was cheap because the harness
//! aborted it with **nothing written** (`NoEngineeringWrite`, exit 2).
//!
//! So a bound is only safe next to a guarantee, and this is that guarantee: a
//! call may end at the role's own completion request **only once the artifact
//! the call declares exists**, and a role that asks to end before writing is
//! told so and continues in the same call.
//!
//! Every test below drives the production path — a real `DefaultAgent`, the real
//! `run_compacting_agent` loop, the real `WriteGuardEnvironment`, and a **real**
//! `LocalEnvironment` (`cmd.exe`), which is the only thing that raises the
//! `Submitted` flow interrupt for `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`
//! (`mini-swe-agent-rust-mini/rust/src/environments/local.rs:118-128`).  No
//! model, no network, and no round is involved: the model is a script.

use std::path::PathBuf;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Mutex;

use hof_rs::harness::compact::{run_compacting_agent, CallProgress, CompactPolicy};
use hof_rs::harness::guard::{ArtifactKind, WriteGuardEnvironment, STEP_BUDGET_STATUS};
use hof_rs::harness::render_write;
use mini_swe_agent::environments::LocalEnvironmentConfig;
use mini_swe_agent::{
    AgentConfig, AgentError, AgentMode, DefaultAgent, LocalEnvironment, Message, Model, Output,
};
use serde_json::{json, Value};

/// The command mini documents as the only legal end of a role call.
const COMPLETE: &str = "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT";

/// The extra key a refusal carries, so a refusal is auditable in the trajectory
/// (and so is the count of them in a live round).
const COMPLETION_REFUSED_KEY: &str = "hoh_exit_refused";

/// The step budget one test call runs under.
#[derive(Clone, Copy, Debug)]
struct Budget {
    step_limit: u64,
    wrap_up_steps: u64,
    steps_per_artifact: u64,
}

impl Budget {
    /// The live configuration's shape, scaled down so a test is fast.
    fn gated() -> Self {
        Self {
            step_limit: 8,
            wrap_up_steps: 1,
            steps_per_artifact: 4,
        }
    }
}

/// A model that runs a fixed script: one list of shell commands per model call.
///
/// It records every message list it was handed, so a test can prove what the
/// role actually saw — including the refusal the guard returned.
struct ScriptedModel {
    script: Vec<Vec<String>>,
    seen: std::sync::Arc<Mutex<Vec<Vec<Message>>>>,
    calls: AtomicUsize,
}

impl ScriptedModel {
    fn new(script: Vec<Vec<String>>) -> (Self, std::sync::Arc<Mutex<Vec<Vec<Message>>>>) {
        let seen = std::sync::Arc::new(Mutex::new(Vec::new()));
        (
            Self {
                script,
                seen: seen.clone(),
                calls: AtomicUsize::new(0),
            },
            seen,
        )
    }
}

#[async_trait::async_trait]
impl Model for ScriptedModel {
    fn model_name(&self) -> &str {
        "scripted"
    }

    async fn query(
        &self,
        messages: &[Message],
        _kwargs: Option<Value>,
    ) -> mini_swe_agent::Result<Message> {
        self.seen
            .lock()
            .expect("the seen lock")
            .push(messages.to_vec());
        let call = self.calls.fetch_add(1, Ordering::SeqCst);
        let commands = self
            .script
            .get(call)
            .cloned()
            .unwrap_or_else(|| vec!["echo idle".to_string()]);
        let actions: Vec<Value> = commands
            .iter()
            .enumerate()
            .map(|(index, command)| {
                json!({"command": command, "tool_call_id": format!("call-{call}-{index}")})
            })
            .collect();
        let mut message = Message::assistant("");
        message.set_extra("actions", Value::Array(actions));
        Ok(message)
    }

    /// The observation shape mini produces in `ApiMode::ToolCalls`: one message
    /// per action, `tool` when the action carries a call id, and the output's own
    /// `extra` block merged in (which is how `hoh_exit_refused` is auditable).
    fn format_observation_messages(
        &self,
        message: &Message,
        outputs: &[Output],
        _template_vars: &Value,
    ) -> mini_swe_agent::Result<Vec<Message>> {
        let actions = message.actions().map_err(AgentError::other)?;
        let not_executed = Output::success("", -1);
        let mut messages = Vec::new();
        for (index, action) in actions.iter().enumerate() {
            let output = outputs.get(index).unwrap_or(&not_executed);
            let body = format!(
                "<returncode>{}</returncode>\n<output>\n{}\n</output>\n",
                output.returncode, output.output
            );
            let mut observation = Message::new(
                if action.tool_call_id.is_some() {
                    "tool"
                } else {
                    "user"
                },
                body,
            );
            if let Some(id) = &action.tool_call_id {
                observation.set_extra("tool_call_id", json!(id));
            }
            observation.set_extra("returncode", json!(output.returncode));
            for (key, value) in &output.extra {
                observation.set_extra(key.clone(), value.clone());
            }
            messages.push(observation);
        }
        Ok(messages)
    }

    fn get_template_vars(&self) -> Value {
        json!({})
    }

    fn serialize(&self) -> Value {
        json!({})
    }
}

/// One call under test: the production loop, the production guard, and a real
/// `cmd.exe` behind it.
struct Call {
    outcome: hof_rs::harness::compact::LoopOutcome,
    project: PathBuf,
    trajectory: PathBuf,
    seen: std::sync::Arc<Mutex<Vec<Vec<Message>>>>,
    _temp: tempfile::TempDir,
}

impl Call {
    fn refusals(&self) -> Vec<Value> {
        let raw = std::fs::read_to_string(&self.trajectory).expect("the loop saves the trajectory");
        let stored: Value = serde_json::from_str(&raw).expect("trajectory json");
        stored["messages"]
            .as_array()
            .expect("a message list")
            .iter()
            .filter(|message| message["extra"][COMPLETION_REFUSED_KEY] == json!(true))
            .cloned()
            .collect()
    }

    fn message_on_call(&self, call: usize) -> String {
        let seen = self.seen.lock().expect("the seen lock");
        let messages = seen.get(call).expect("the model was called");
        serde_json::to_string(messages).expect("messages serialize")
    }
}

async fn run(script: Vec<Vec<String>>, budget: Budget) -> Call {
    let temp = tempfile::tempdir().expect("tempdir");
    let project = temp.path().join("project");
    std::fs::create_dir_all(&project).expect("the project directory");

    let local = LocalEnvironment::new(LocalEnvironmentConfig {
        cwd: project.to_string_lossy().into_owned(),
        env: Default::default(),
        timeout: 60,
    });
    let progress = CallProgress::default();
    let guard = WriteGuardEnvironment::with_limits(
        Box::new(local),
        project.clone(),
        3,
        0,
        // The Developer's artifact kind: a write to a file **inside the project**.
        ArtifactKind::ProjectFile,
        // The repeated-success tripwire and the wall-clock artifact budget are
        // off: this file is about the exit, and neither can make the scripted
        // calls in it flaky.
        0,
        budget.step_limit,
        budget.wrap_up_steps,
        budget.steps_per_artifact,
    )
    .sharing_steps(progress.steps.clone());

    let (model, seen) = ScriptedModel::new(script);
    let trajectory = temp.path().join("traj/developer.attempt1.json");
    let config = AgentConfig {
        system_template: "{{hoh_system_prompt}}".to_string(),
        instance_template: "{{task}}".to_string(),
        step_limit: budget.step_limit,
        cost_limit: 0.0,
        wall_time_limit_seconds: 0,
        max_consecutive_format_errors: 3,
        output_path: Some(trajectory.clone()),
        mode: AgentMode::Yolo,
        whitelist_actions: Vec::new(),
        confirm_exit: false,
    };
    let agent = DefaultAgent::new(Box::new(model), Box::new(guard), config);
    let outcome = run_compacting_agent(
        agent,
        progress,
        CompactPolicy::default(),
        "stub task",
        Some(json!({"hoh_system_prompt": "stub system prompt"})),
    )
    .await
    .expect("the loop runs");

    Call {
        outcome,
        project,
        trajectory,
        seen,
        _temp: temp,
    }
}

// ---------------------------------------------------------------------------
// The permission: having written, the documented command ends the call there.
// ---------------------------------------------------------------------------

/// The whole point of the criterion: **the earliest legitimate exit is the turn
/// after the write**.  If the artifact exists, nothing else may stand between the
/// role and its exit — no minimum call count, no extra confirmation.
#[tokio::test]
async fn a_write_then_the_completion_command_ends_the_call_at_that_turn() {
    let call = run(
        vec![
            vec![render_write("src/game.rs", "fn main() {}\n")],
            vec![COMPLETE.to_string()],
        ],
        Budget::gated(),
    )
    .await;

    assert_eq!(
        call.outcome.exit_status, "Submitted",
        "{}",
        call.outcome.exit_status
    );
    assert_eq!(
        call.outcome.steps, 2,
        "the call must end at the second model call, the one that ran the completion command"
    );
    assert!(call.refusals().is_empty(), "nothing was refused");
    let written = std::fs::read_to_string(call.project.join("src/game.rs")).expect("the write");
    assert_eq!(
        written, "fn main() {}\n",
        "the bytes must be the directive's"
    );
}

/// A response that writes and completes in one turn also ends there: the write
/// is what the exit needed, and it happened in this very call.
#[tokio::test]
async fn a_write_and_the_completion_in_one_response_end_the_call() {
    let call = run(
        vec![vec![
            render_write("src/game.rs", "fn main() {}\n"),
            COMPLETE.to_string(),
        ]],
        Budget::gated(),
    )
    .await;

    assert_eq!(call.outcome.exit_status, "Submitted");
    assert_eq!(call.outcome.steps, 1, "one model call, one exit");
    assert!(call.project.join("src/game.rs").is_file());
    assert!(call.refusals().is_empty());
}

// ---------------------------------------------------------------------------
// The guarantee: a call with no engineering write may not end that way.
// ---------------------------------------------------------------------------

/// The measured failure mode of the round this batch follows, as a test: the
/// Developer ran the completion command having written nothing inside the
/// project.  Before this repair the call ended there, the Developer stage changed
/// nothing, and the round died with `NoEngineeringWrite` (exit 2).
///
/// Now the exit is refused, the role is told exactly what is missing, the call
/// continues, and the same role ends it legitimately one write later.
#[tokio::test]
async fn a_completion_request_without_the_engineering_write_is_refused_and_the_call_continues() {
    let call = run(
        vec![
            vec![COMPLETE.to_string()],
            vec![render_write("src/game.rs", "fn main() {}\n")],
            vec![COMPLETE.to_string()],
        ],
        Budget::gated(),
    )
    .await;

    assert_eq!(
        call.outcome.exit_status, "Submitted",
        "{}",
        call.outcome.exit_status
    );
    assert_eq!(
        call.outcome.steps, 3,
        "the refused completion must not have ended the call (steps = {})",
        call.outcome.steps
    );
    assert!(
        call.project.join("src/game.rs").is_file(),
        "the forced continuation must have produced the engineering write"
    );

    let refusals = call.refusals();
    assert_eq!(refusals.len(), 1, "exactly the first exit was refused");
    let refusal = refusals[0]["content"].as_str().unwrap_or_default();
    assert!(
        refusal.contains("exit refused"),
        "the refusal must say what happened: {refusal}"
    );
    assert!(
        refusal.contains("has not yet written"),
        "the refusal must name the missing artifact: {refusal}"
    );
    assert!(
        refusal.contains("HOH_WRITE_FILE"),
        "the refusal must say how to write it: {refusal}"
    );

    // What the role was actually handed on the second call: the refusal, so the
    // continuation is a *targeted* one rather than a silent retry.
    let second = call.message_on_call(1);
    assert!(
        second.contains("exit refused") && second.contains("HOH_WRITE_FILE"),
        "the second call must see the refusal and the write directive: {second}"
    );
}

/// A write to `.hoh/scratch` is not the engineering write, exactly as it is not
/// for the step budget (`ArtifactKind::counts`).  A call that has only scribbled
/// in its own scratch directory has not produced the increment the round is
/// graded on, so its completion is refused too.
#[tokio::test]
async fn a_scratch_write_is_not_an_engineering_write() {
    let call = run(
        vec![
            vec![render_write(".hoh/scratch/notes.md", "a note\n")],
            vec![COMPLETE.to_string()],
            vec![render_write("src/game.rs", "fn main() {}\n")],
            vec![COMPLETE.to_string()],
        ],
        Budget::gated(),
    )
    .await;

    assert_eq!(call.outcome.exit_status, "Submitted");
    assert_eq!(
        call.outcome.steps, 4,
        "the scratch write must not satisfy the exit gate (steps = {})",
        call.outcome.steps
    );
    assert_eq!(call.refusals().len(), 1);
    assert!(call.project.join(".hoh/scratch/notes.md").is_file());
    assert!(call.project.join("src/game.rs").is_file());
}

/// A call that never writes still cannot grind: the unwritten step budget ends it
/// with the harness's own status, which the runtime treats as a failure — and
/// which, at the round level, is the `NoEngineeringWrite` measurement.  The gate
/// added above this test must not have touched that.
#[tokio::test]
async fn the_unwritten_step_budget_guard_still_ends_a_call_that_never_writes() {
    let call = run(vec![], Budget::gated()).await;

    assert_eq!(
        call.outcome.exit_status, STEP_BUDGET_STATUS,
        "an unwritten call must still be cut by its budget (exit_status = {})",
        call.outcome.exit_status
    );
    assert_eq!(call.outcome.steps, 4, "budget = 1 + 8/4 = 3, enforced at 4");
    assert!(
        hof_rs::runtime::write_failure::is_failure_status(&call.outcome.exit_status),
        "the runtime must still read this as a failure, not as a clean end"
    );
    assert!(
        !call.project.join("src/game.rs").exists(),
        "the test's script wrote nothing"
    );
    assert!(call.refusals().is_empty());
}

/// The control for the gate: a **plain** command is untouched.  It cannot end a
/// call at all (mini's rule is the marker's first output line with exit code 0),
/// so it just runs, produces an ordinary observation, and the call continues to
/// the write and the real completion.
#[tokio::test]
async fn a_plain_command_is_not_a_completion_request_and_is_untouched() {
    let call = run(
        vec![
            vec!["echo submit".to_string()],
            vec![render_write("src/game.rs", "fn main() {}\n")],
            vec![COMPLETE.to_string()],
        ],
        Budget::gated(),
    )
    .await;

    assert_eq!(call.outcome.exit_status, "Submitted");
    assert_eq!(
        call.outcome.steps, 3,
        "the plain command ran and changed nothing"
    );
    assert!(call.refusals().is_empty(), "nothing was refused");
}
