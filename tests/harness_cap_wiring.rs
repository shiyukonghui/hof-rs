//! DR-70 ④: the tool-output ceiling must be wired into the **harness the runtime
//! actually calls**.
//!
//! DR-69 ③ built `cap_tool_output` and wrapped the environment in
//! `CappedEnvironment` inside `MiniHarness::invoke`, but nothing exercised the
//! wrapper through `MiniHarness::invoke`: deleting `src/harness/mini.rs:66-69`
//! left `--test tool_output_ceiling` green and the whole suite at `0 failed`
//! (the acceptance's plant P-B2, D4).  Every test in `tool_output_ceiling.rs`
//! builds `CappedEnvironment` itself, so it can only prove the *function* is
//! correct — never that the harness uses it.
//!
//! This test drives the real `MiniHarness::invoke` against a loopback chat
//! endpoint that answers with one tool call producing a 2 MiB result, and then
//! inspects **the payload of the next request**.  That request is the boundary
//! the `smoke-t9` incident crossed: the observation is replayed verbatim into the
//! following prompt.  Delete the wrapper and the next request carries the whole
//! 2 MiB again, so this test goes red instead of staying green.

use std::io::{Read, Write};
use std::net::TcpListener;
use std::sync::mpsc;
use std::sync::Mutex;

use hof_rs::config::{export_model_api_key, load_config, AgentLimits};
use hof_rs::harness::cap::TRUNCATION_MARKER;
use hof_rs::harness::{Harness, MiniHarness};
use hof_rs::model::Role;
use hof_rs::runtime::role::RoleInvocation;
use serde_json::json;

const FAKE_KEY: &str = "test-key-not-a-secret";
const PAYLOAD_BYTES: usize = 2 * 1024 * 1024;
const CEILING_BYTES: u64 = 4096;
/// The distinct byte the shell tool prints; the next request must not carry it.
const FILLER: u8 = b'y';
static ENV_LOCK: Mutex<()> = Mutex::new(());

/// Does `bytes` contain `count` consecutive copies of `byte`?
fn contains_run(bytes: &[u8], byte: u8, count: usize) -> bool {
    bytes
        .windows(count)
        .any(|window| window.iter().all(|candidate| *candidate == byte))
}

/// One recorded chat request: its raw body, exactly as the model endpoint saw it.
struct Recorded {
    body: Vec<u8>,
}

/// A loopback chat endpoint that answers the first request with a tool call
/// producing a 2 MiB shell result, and every later request with the terminal
/// submit.  Every request body is recorded.
fn spawn_scripted_chat_server(response_model: String) -> (u16, mpsc::Receiver<Recorded>) {
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
            let Some(header_end) = header_end else { continue };
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

            let response_body = if index == 0 {
                tool_call_completion(&response_model, "type big.txt")
            } else {
                tool_call_completion(&response_model, "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT")
            };
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

/// A chat completion whose single tool call asks the shell for `command`.
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

/// The whole test: one real `MiniHarness::invoke`, and the bytes of the request
/// that follows the oversized tool result.
#[tokio::test]
async fn the_harness_itself_bounds_what_the_next_request_carries() {
    let _guard = ENV_LOCK
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    let saved_hoh = std::env::var("HOH_MODEL_API_KEY").ok();
    let saved_openai = std::env::var("OPENAI_API_KEY").ok();

    let wire = load_config(&[])
        .expect("the shipped configuration must load")
        .wire_model_name()
        .to_string();
    assert!(!wire.is_empty(), "config must declare wire_model_name");

    let temp = tempfile::tempdir().expect("tempdir");
    let big = temp.path().join("big.txt");
    std::fs::write(&big, vec![FILLER; PAYLOAD_BYTES]).expect("the oversized fixture");

    let (port, received) = spawn_scripted_chat_server(wire.clone());
    std::env::set_var("HOH_MODEL_API_KEY", FAKE_KEY);
    std::env::remove_var("OPENAI_API_KEY");
    let config = load_config(&[
        "config/hoh.yaml".to_string(),
        format!("model.base_url=http://127.0.0.1:{port}/v1"),
    ])
    .expect("override config");
    export_model_api_key(&config);

    let trajectory = temp.path().join("traj/developer.attempt1.json");
    let invocation = RoleInvocation {
        role: Role::Developer,
        iteration: 1,
        system_prompt: "you are the developer".to_string(),
        task_prompt: "print the fixture".to_string(),
        cwd: temp.path().to_path_buf(),
        env: Default::default(),
        limits: AgentLimits {
            step_limit: 4,
            cost_limit: 0.0,
            wall_time_limit_seconds: 120,
            command_timeout_seconds: 120,
            max_tool_output_bytes: CEILING_BYTES,
            ..AgentLimits::default()
        },
        model: config.model.clone(),
        trajectory_path: trajectory.clone(),
        retry_context: None,
    };

    let harness = MiniHarness::new();
    let outcome = harness.invoke(&invocation).await.expect("the harness must run");
    assert_eq!(outcome.role, Role::Developer);

    // The first request is the prompt; the **second** one carries the oversized
    // tool result.  Anything the harness lets through is replayed there, which is
    // the `smoke-t9` failure mode.
    let first = received
        .recv_timeout(std::time::Duration::from_secs(120))
        .expect("the endpoint must receive the first chat request");
    assert!(
        !contains_run(&first.body, FILLER, 1024),
        "the prompt must not already carry the fixture"
    );
    let second = received
        .recv_timeout(std::time::Duration::from_secs(120))
        .expect("the endpoint must receive the request that follows the tool call");
    let second_text = String::from_utf8_lossy(&second.body).into_owned();

    assert!(
        !contains_run(&second.body, FILLER, 64 * 1024),
        "the request that follows the 2 MiB tool result must not carry it: {} bytes were sent",
        second.body.len()
    );
    assert!(
        second_text.contains(TRUNCATION_MARKER),
        "the carried observation must be the explicitly annotated truncation, not a silent cut"
    );
    assert!(
        second.body.len() < 256 * 1024,
        "a 2 MiB tool result with a {CEILING_BYTES}-byte ceiling must not produce a {} byte \
         request",
        second.body.len()
    );

    match saved_hoh {
        Some(value) => std::env::set_var("HOH_MODEL_API_KEY", value),
        None => std::env::remove_var("HOH_MODEL_API_KEY"),
    }
    match saved_openai {
        Some(value) => std::env::set_var("OPENAI_API_KEY", value),
        None => std::env::remove_var("OPENAI_API_KEY"),
    }
}
