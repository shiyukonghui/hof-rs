//! The **post-write call bound** (cost batch, after `ACCEPTANCE-WRITE-GUARANTEE.md`
//! defect D1 and `SPIKE-COST-LEVERS.md` lever 4).
//!
//! The measurement this file answers, in one paragraph.  A Developer call must
//! come in under `agent.artifact_write_budget_tokens` = 1,500,000 tokens.  The
//! zero-context floor for a 150-call live call is 2,077,238, so the criterion is
//! arithmetically unreachable at 150 calls and the only remaining lever is to end
//! the call earlier.  The write-guaranteed exit supplies the permission half: a
//! call may end at its own completion request only once its counted engineering
//! write exists, and an exit before the write is refused.  This file supplies the
//! ceiling half: **once the write exists, the call runs under a second, tighter
//! step budget** rather than the flat 150.
//!
//! The number is measured, not chosen.  The guard allows exactly `B` model calls
//! and bills one more (`steps > budget`), so a bound `B` costs the prefix sum of
//! the recorded per-call usage over calls `1..=B+1`.  The largest prefix still
//! under the criterion is 44 / 40 / 36 / 81 calls for `round4-iter-1/2/3` and
//! `livecost1-iter-1` and 78 / 74 for the two live post-fix producing calls, so
//! the binding recording is `round4-iter-3` at **36** calls: `B = 35` is the
//! largest bound that brings every recorded Developer call under the criterion.
//! Below the bound, `B = 36` misses it by 2,443 tokens (1,502,443 = 1.002x on the
//! same recording), and `B >= 33` is required for no recorded call to be cut
//! before its write under even the flat reading of the number.

use hof_rs::config::{export_model_api_key, load_config, AgentLimits};

/// The shipped post-write call bound, and the reason for this exact number.
///
/// The binding recording is `round4-iter-3`: prefix tokens are 1,452,307 at 36
/// model calls (0.968x) and 1,502,443 at 37 (1.002x).  The guard's rule
/// `steps > budget` bills `B + 1` calls, so `B = 35` is the largest bound whose
/// every recorded call stays under the criterion, and the residual headroom on
/// the binding recording is 47,693 tokens (3.2%).
const POST_WRITE_STEP_LIMIT: u64 = 35;

/// The unwritten allowance the bound must not touch:
/// `wrap_up_steps + step_limit / steps_per_artifact` = `25 + 150 / 8` = **43**
/// model calls, which the measured round ended at 44 billed calls.
const UNWRITTEN_STEP_LIMIT: u64 = 43;

// ---------------------------------------------------------------------------
// The configuration is where the number lives, so it is asserted there first.
// ---------------------------------------------------------------------------

/// The criterion is about how many calls a producing Developer call makes, so the
/// bound must be a fact about the shipped configuration rather than a constant in
/// the harness: this is the arithmetic the round actually runs on.
#[test]
fn the_shipped_configuration_bounds_a_call_that_has_written() {
    let config = load_config(&[]).expect("the shipped configuration must load");
    assert_eq!(config.agent.step_limit, 150);
    assert_eq!(config.agent.wrap_up_steps, 25);
    assert_eq!(config.agent.steps_per_artifact, 8);
    assert_eq!(
        config.agent.effective_step_limit(false),
        UNWRITTEN_STEP_LIMIT,
        "a call that has written nothing keeps the unwritten allowance"
    );
    assert_eq!(
        config.agent.effective_step_limit(true),
        POST_WRITE_STEP_LIMIT,
        "a call that has written its artifact must run under the post-write bound, not the flat 150"
    );
    assert!(
        config.agent.effective_step_limit(true) < config.agent.step_limit,
        "the post-write bound is the *tighter* allowance: it only exists once the write does"
    );
    assert!(
        config.agent.effective_step_limit(false) > config.agent.effective_step_limit(true),
        "the shipped shape is the measured one: the unwritten allowance (43) is wider than the \
         post-write bound (35), because the post-write call has already produced its increment"
    );
}

/// The bound is a shipped number with a documented derivation, so the
/// configuration file must carry it (and the `[budget]` note reads it back).
#[test]
fn the_configuration_states_the_post_write_bound() {
    let text = std::fs::read_to_string("config/hoh.yaml").expect("the shipped config file");
    assert!(
        text.contains("post_write_step_limit: 35"),
        "config/hoh.yaml must ship the post-write bound as a named number, not leave it implicit"
    );
}

/// The control: a zero post-write bound means "no post-write ceiling" rather than
/// "end the call immediately" — a zero that cut a producing call at one step would
/// be a different, silently failing feature.  It is also the library default, so a
/// caller that does not name the field keeps the pre-repair behaviour exactly.
#[test]
fn a_zero_post_write_bound_disables_the_ceiling() {
    let limits = AgentLimits {
        step_limit: 150,
        wrap_up_steps: 25,
        steps_per_artifact: 8,
        ..AgentLimits::default()
    };
    assert_eq!(
        AgentLimits::default().post_write_step_limit,
        0,
        "the library default must be the pre-repair behaviour, not a hidden ceiling"
    );
    let disabled = AgentLimits {
        post_write_step_limit: 0,
        ..limits.clone()
    };
    assert_eq!(
        disabled.effective_step_limit(true),
        150,
        "0 means no post-write ceiling, so the written budget is the flat limit"
    );
    let unbounded_write = AgentLimits {
        post_write_step_limit: 0,
        steps_per_artifact: 0,
        ..limits.clone()
    };
    assert_eq!(unbounded_write.effective_step_limit(true), 150);
    assert_eq!(unbounded_write.effective_step_limit(false), 150);
}

/// The written budget may never exceed the flat ceiling: the post-write bound is
/// a tighter allowance, not a second, larger one.
#[test]
fn the_post_write_bound_is_capped_by_the_flat_limit() {
    let limits = AgentLimits {
        step_limit: 20,
        wrap_up_steps: 5,
        steps_per_artifact: 8,
        post_write_step_limit: 35,
        ..AgentLimits::default()
    };
    assert_eq!(
        limits.effective_step_limit(true),
        20,
        "a post-write bound above the flat limit must not raise the ceiling"
    );
    assert_eq!(limits.effective_step_limit(false), 7, "5 + max(20/8, 1)");
}

// ---------------------------------------------------------------------------
// The production path: the configuration number must reach the guard.
// ---------------------------------------------------------------------------

use std::io::{Read, Write};
use std::net::TcpListener;
use std::path::PathBuf;
use std::sync::mpsc;
use std::sync::Mutex;

use hof_rs::harness::guard::STEP_BUDGET_STATUS;
use hof_rs::harness::{render_write, Harness, MiniHarness};
use hof_rs::model::Role;
use hof_rs::runtime::role::RoleInvocation;
use serde_json::json;

/// A dummy credential, exactly as `tests/harness_cap_wiring.rs` uses one: the
/// endpoint is a loopback fake, so no real key exists anywhere in this test.
const FAKE_KEY: &str = "test-key-not-a-secret";
static ENV_LOCK: Mutex<()> = Mutex::new(());

/// One chat request the fake endpoint received, so a test can prove the script
/// really ran (and that the call was cut where it claims).
struct Recorded {
    body: Vec<u8>,
}

/// A loopback OpenAI-compatible endpoint that answers call 1 with the write
/// directive `first` and every later call with a harmless idle command.
///
/// This is the same fake-endpoint pattern `tests/harness_cap_wiring.rs` uses for
/// the tool-output ceiling: it exists because the value under test lives in the
/// **configuration** and a test that builds the guard itself could never prove
/// that `MiniHarness::invoke` passes it on.  No model and no network are involved.
fn spawn_chat_server(
    response_model: String,
    first: String,
    write: bool,
) -> (u16, mpsc::Receiver<Recorded>) {
    let listener = TcpListener::bind("127.0.0.1:0").expect("bind loopback");
    let port = listener.local_addr().expect("addr").port();
    let (sender, receiver) = mpsc::channel();

    std::thread::spawn(move || {
        let mut index = 0usize;
        for stream in listener.incoming() {
            let Ok(mut stream) = stream else { break };
            let mut raw: Vec<u8> = Vec::new();
            let mut buffer = [0u8; 8192];
            let mut header_end = None;
            while header_end.is_none() {
                match stream.read(&mut buffer) {
                    Ok(0) | Err(_) => break,
                    Ok(count) => raw.extend_from_slice(&buffer[..count]),
                }
                if let Some(position) = raw.windows(4).position(|window| window == b"\r\n\r\n") {
                    header_end = Some(position + 4);
                }
            }
            let Some(header_end) = header_end else {
                continue;
            };
            let headers = String::from_utf8_lossy(&raw[..header_end]).to_string();
            let content_length = headers
                .lines()
                .find_map(|line| {
                    let (key, value) = line.split_once(':')?;
                    if key.eq_ignore_ascii_case("content-length") {
                        value.trim().parse::<usize>().ok()
                    } else {
                        None
                    }
                })
                .unwrap_or(0);
            while raw.len() < header_end + content_length {
                match stream.read(&mut buffer) {
                    Ok(0) | Err(_) => break,
                    Ok(count) => raw.extend_from_slice(&buffer[..count]),
                }
            }
            let _ = sender.send(Recorded {
                body: raw[header_end..raw.len().min(header_end + content_length)].to_vec(),
            });

            // Call 1 is the one that may write; every later call is a distinct
            // idle command so neither the repeated-action tripwire nor a pending
            // `echo COMPLETE_...` can decide the ending for us.
            let command = if index == 0 && write {
                first.clone()
            } else if index == 0 {
                "echo idle".to_string()
            } else {
                format!("echo idle {index}")
            };
            let response_body = tool_call_completion(&response_model, &command);
            index += 1;
            let response = format!(
                "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\
                 Connection: close\r\n\r\n{}",
                response_body.len(),
                response_body
            );
            let _ = stream.write_all(response.as_bytes());
            let _ = stream.flush();
        }
    });

    (port, receiver)
}

/// A chat completion whose single tool call runs `command` in the shell (the
/// guard intercepts `HOH_WRITE_FILE` before the shell ever sees it).
fn tool_call_completion(response_model: &str, command: &str) -> String {
    json!({
        "id": "chatcmpl-fake",
        "object": "chat.completion",
        "created": 0,
        "model": response_model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "bash",
                        "arguments": json!({"command": command}).to_string()
                    }
                }]
            },
            "finish_reason": "tool_calls"
        }],
        "usage": {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10}
    })
    .to_string()
}

/// The scaled-down shape of the shipped configuration, so the two budgets are
/// distinguishable and both sit under mini's own flat backstop:
/// `step_limit = 8`, `wrap_up_steps = 1`, `steps_per_artifact = 2` give the
/// unwritten allowance `1 + 8/2 = 5` model calls, and `post_write_step_limit = 3`
/// gives a written call 3.
#[derive(Clone, Copy, Debug)]
struct Shape {
    step_limit: u64,
    wrap_up_steps: u64,
    steps_per_artifact: u64,
    post_write_step_limit: u64,
}

impl Shape {
    fn scaled() -> Self {
        Self {
            step_limit: 8,
            wrap_up_steps: 1,
            steps_per_artifact: 2,
            post_write_step_limit: 3,
        }
    }
}

/// The outcome of one real `MiniHarness::invoke`, plus what the fake endpoint saw
/// and what landed on disk — so the ending is checked beside the evidence that the
/// call really did (or really did not) write.
struct Call {
    outcome: hof_rs::runtime::role::RoleOutcome,
    /// Every request body the endpoint received, in order.
    bodies: Vec<Vec<u8>>,
    /// The project directory, kept alive by `_temp`.
    project: PathBuf,
    _temp: tempfile::TempDir,
}

impl Call {
    fn requests(&self) -> usize {
        self.bodies.len()
    }

    fn any_body_mentions(&self, needle: &str) -> bool {
        self.bodies
            .iter()
            .any(|body| String::from_utf8_lossy(body).contains(needle))
    }
}

async fn run(shape: Shape, write: bool) -> Call {
    let _guard = ENV_LOCK
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    let saved_hoh = std::env::var("HOH_MODEL_API_KEY").ok();
    let saved_openai = std::env::var("OPENAI_API_KEY").ok();

    let base = load_config(&[]).expect("the shipped configuration must load");
    let wire = base.wire_model_name().to_string();
    let temp = tempfile::tempdir().expect("tempdir");
    let project = temp.path().join("project");
    std::fs::create_dir_all(&project).expect("the project directory");
    let (port, received) =
        spawn_chat_server(wire, render_write("src/game.rs", "fn main() {}\n"), write);
    std::env::set_var("HOH_MODEL_API_KEY", FAKE_KEY);
    std::env::remove_var("OPENAI_API_KEY");
    let config = load_config(&[
        "config/hoh.yaml".to_string(),
        format!("model.base_url=http://127.0.0.1:{port}/v1"),
    ])
    .expect("override config");
    export_model_api_key(&config);

    let invocation = RoleInvocation {
        role: Role::Developer,
        iteration: 1,
        system_prompt: "you are the developer".to_string(),
        task_prompt: "keep working on the project".to_string(),
        cwd: project.clone(),
        env: Default::default(),
        limits: AgentLimits {
            step_limit: shape.step_limit,
            wrap_up_steps: shape.wrap_up_steps,
            steps_per_artifact: shape.steps_per_artifact,
            post_write_step_limit: shape.post_write_step_limit,
            cost_limit: 0.0,
            wall_time_limit_seconds: 120,
            command_timeout_seconds: 120,
            ..AgentLimits::default()
        },
        model: config.model.clone(),
        trajectory_path: temp.path().join("traj/developer.attempt1.json"),
        retry_context: None,
    };

    let outcome = MiniHarness::new()
        .invoke(&invocation)
        .await
        .expect("the harness must run");
    let mut bodies = Vec::new();
    while let Ok(recorded) = received.recv_timeout(std::time::Duration::from_millis(500)) {
        bodies.push(recorded.body);
    }
    assert!(
        std::fs::read_to_string(temp.path().join("traj/developer.attempt1.json")).is_ok(),
        "the call must have been recorded"
    );

    match saved_hoh {
        Some(value) => std::env::set_var("HOH_MODEL_API_KEY", value),
        None => std::env::remove_var("HOH_MODEL_API_KEY"),
    }
    match saved_openai {
        Some(value) => std::env::set_var("OPENAI_API_KEY", value),
        None => std::env::remove_var("OPENAI_API_KEY"),
    }

    Call {
        outcome,
        bodies,
        project,
        _temp: temp,
    }
}

/// **The bound.**  A call that has written its engineering file runs under the
/// post-write budget, not under the flat 150 — and not under the wider unwritten
/// allowance either.  The guard allows exactly `budget` model calls and refuses
/// the next one, so budget 3 ends the call at 4 calls with the guard's own
/// `StepBudgetExceeded` status.
#[tokio::test]
async fn a_call_that_has_written_ends_at_the_post_write_bound() {
    let call = run(Shape::scaled(), true).await;
    assert_eq!(
        call.outcome.exit_status, STEP_BUDGET_STATUS,
        "a written call must be cut by the post-write bound (exit_status = {})",
        call.outcome.exit_status
    );
    assert_eq!(
        call.outcome.steps, 4,
        "budget = 3, enforced at steps > 3, so the call spends 4 model calls (steps = {})",
        call.outcome.steps
    );
    assert_eq!(
        call.requests(),
        4,
        "the endpoint must have been asked exactly as often as the call billed model calls"
    );
    assert!(
        call.project.join("src/game.rs").is_file(),
        "the counted engineering write must really have landed on disk, or the post-write bound \
         would be enforcing a budget for a write that never happened"
    );
    assert!(
        call.any_body_mentions("src/game.rs"),
        "the write's own observation must have been carried into a later request"
    );
    assert!(
        hof_rs::runtime::write_failure::is_failure_status(&call.outcome.exit_status),
        "the runtime must still read the bound's ending as a budget failure, not a clean end"
    );
}

/// **The control.**  A call that has written *nothing* is untouched by this
/// bound: it keeps the unwritten allowance (`wrap_up_steps + step_limit /
/// steps_per_artifact` = 5 here, the shipped 43), so the post-write ceiling cannot
/// be the thing that cuts a call before its artifact exists.  This is also the
/// behaviour the round's `no_engineering_write` failure depends on.
#[tokio::test]
async fn a_call_that_has_not_written_keeps_the_unwritten_allowance() {
    let call = run(Shape::scaled(), false).await;
    assert_eq!(
        call.outcome.exit_status, STEP_BUDGET_STATUS,
        "an unwritten call is still cut by its own budget (exit_status = {})",
        call.outcome.exit_status
    );
    assert_eq!(
        call.outcome.steps, 6,
        "the unwritten allowance is 1 + 8/2 = 5, enforced at steps > 5, so 6 model calls \
         (steps = {}); the post-write bound of 3 must not have been consulted",
        call.outcome.steps
    );
    assert!(
        call.outcome.steps > 4,
        "an unwritten call must get strictly more than the post-write bound, or the bound is \
         cutting calls before their write"
    );
    assert!(
        !call.project.join("src/game.rs").exists(),
        "the test's script wrote nothing, so the unwritten allowance is the one that applied"
    );
    assert!(
        hof_rs::runtime::write_failure::is_failure_status(&call.outcome.exit_status),
        "a call that never wrote still ends as a failure the runtime records"
    );
}
