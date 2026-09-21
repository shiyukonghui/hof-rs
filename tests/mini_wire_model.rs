//! DR-14 double-lock + DR-16 key hygiene, observed through **real HTTP traffic**.
//!
//! Two facts cannot be trusted from the inside: the exact `model` string that
//! reaches the wire (`effective_model_name` is `pub(crate)` in mini) and the
//! fact that the secret is never persisted.  Both are therefore asserted
//! against a local fake endpoint's byte-level view of the request, and against
//! mini's own trajectory file.
//!
//! Nothing here is hard-coded to a vendor: the expected wire id is read from
//! `config/hoh.yaml`, so switching models is a configuration-only change.
//! The credential is a placeholder (`test-key-not-a-secret`) supplied through
//! the environment, exactly as DR-16 prescribes.

use std::io::{Read, Write};
use std::net::TcpListener;
use std::sync::mpsc;
use std::sync::Mutex;

use mini_swe_agent::environments::{LocalEnvironment, LocalEnvironmentConfig};
use mini_swe_agent::models::{ApiMode, LlmConnectorModel};
use mini_swe_agent::{Agent, AgentConfig, AgentMode, DefaultAgent, Model};
use serde_json::{json, Value};

use hof_rs::config::{export_model_api_key, load_config};

const FAKE_KEY: &str = "test-key-not-a-secret";
static ENV_LOCK: Mutex<()> = Mutex::new(());

#[derive(Debug, Clone)]
struct Recorded {
    headers: String,
    body: Value,
}

/// A loopback HTTP server that records every request it receives and answers
/// with a chat completion whose single tool call terminates the agent loop.
///
/// `std::net` is used deliberately: it is part of the standard library, always
/// available offline, and cannot drift the way an HTTP client dependency can.
fn spawn_fake_chat_server(response_model: String) -> (u16, mpsc::Receiver<Recorded>) {
    let listener = TcpListener::bind("127.0.0.1:0").expect("bind loopback");
    let port = listener.local_addr().expect("addr").port();
    let (sender, receiver) = mpsc::channel();

    std::thread::spawn(move || {
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

            let body = &raw[header_end..raw.len().min(header_end + content_length)];
            let _ = sender.send(Recorded {
                headers: headers.clone(),
                body: serde_json::from_slice(body).unwrap_or(Value::Null),
            });

            let response_body = chat_completion(&response_model);
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

/// A chat completion whose single tool call terminates the agent loop.
fn chat_completion(response_model: &str) -> String {
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
                        "arguments": "{\"command\":\"echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT\"}"
                    }
                }]
            },
            "finish_reason": "tool_calls"
        }],
        "usage": {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10}
    })
    .to_string()
}

fn authorization_of(headers: &str) -> String {
    headers
        .lines()
        .find(|line| line.to_ascii_lowercase().starts_with("authorization:"))
        .map(|line| line[line.find(':').unwrap() + 1..].trim().to_string())
        .unwrap_or_default()
}

fn run_agent_and_collect(
    config: &hof_rs::config::HohConfig,
    trajectory: &std::path::Path,
    mode: ApiMode,
) -> Vec<mini_swe_agent::Message> {
    let model = LlmConnectorModel::from_value_with_mode(config.model.clone(), mode)
        .expect("model must build from the shipped configuration");
    assert_eq!(
        model.model_name(),
        config.model_name(),
        "the configured model name must survive mini's resolution (DR-14)"
    );

    let temp = tempfile::tempdir().expect("tempdir");
    let env_config = LocalEnvironmentConfig {
        cwd: temp.path().to_string_lossy().into_owned(),
        timeout: 30,
        env: Default::default(),
    };
    let environment = LocalEnvironment::new(env_config);

    let agent_config = AgentConfig {
        system_template: "{{hoh_system_prompt}}".to_string(),
        instance_template: "{{task}}".to_string(),
        step_limit: 4,
        // 0.0 is mandatory: mini's default of 3.0 would abort a local run.
        cost_limit: 0.0,
        wall_time_limit_seconds: 60,
        max_consecutive_format_errors: 3,
        output_path: Some(trajectory.to_path_buf()),
        mode: AgentMode::Yolo,
        whitelist_actions: Vec::new(),
        confirm_exit: false,
    };
    let mut agent = DefaultAgent::new(Box::new(model), Box::new(environment), agent_config);

    let runtime = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .expect("runtime");
    let _ = runtime.block_on(agent.run(
        "say hello",
        Some(json!({"hoh_system_prompt": "you are the planner"})),
    ));
    agent.messages
}

#[test]
fn wire_model_id_is_exact_and_the_secret_only_travels_in_the_environment() {
    let guard = ENV_LOCK
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    let saved_openai = std::env::var("OPENAI_API_KEY").ok();
    let saved_hoh = std::env::var("HOH_MODEL_API_KEY").ok();

    // The expected wire id comes from configuration, never from this file.
    let wire = load_config(&[])
        .expect("default config")
        .wire_model_name()
        .to_string();
    assert!(!wire.is_empty(), "config must declare wire_model_name");

    let (port, received) = spawn_fake_chat_server(wire.clone());
    std::env::set_var("HOH_MODEL_API_KEY", FAKE_KEY);
    std::env::remove_var("OPENAI_API_KEY");

    let config = load_config(&[
        "config/hoh.yaml".to_string(),
        format!("model.base_url=http://127.0.0.1:{port}/v1"),
    ])
    .expect("override config");
    // DR-16: the secret is exported into the HoH process environment (mini's
    // own fallback variable) and never written into the model JSON.
    assert_eq!(
        export_model_api_key(&config).as_deref(),
        Some(FAKE_KEY),
        "the env key must be resolved"
    );
    assert!(
        config.model.get("api_key").is_none_or(Value::is_null),
        "the model JSON handed to mini must not carry a secret: {}",
        config.model
    );

    let temp = tempfile::tempdir().expect("tempdir");
    let trajectory = temp.path().join("traj/planner.attempt1.json");
    std::fs::create_dir_all(trajectory.parent().unwrap()).expect("mkdir");

    let messages = run_agent_and_collect(&config, &trajectory, ApiMode::ToolCalls);
    assert!(!messages.is_empty(), "the fake agent must have run");

    let request = received
        .recv_timeout(std::time::Duration::from_secs(60))
        .expect("the fake server must receive a chat request");

    assert_eq!(
        request.body["model"],
        json!(wire),
        "the on-the-wire model id must be exactly the configured wire_model_name (C9/DR-14)"
    );
    // The role text must travel as a template *value*, not as template source.
    assert_eq!(
        request.body["messages"][0]["content"],
        json!("you are the planner")
    );
    assert_eq!(request.body["messages"][1]["content"], json!("say hello"));
    // DR-15/DR-16: the environment key must be the one that authenticates.
    assert_eq!(
        authorization_of(&request.headers),
        format!("Bearer {FAKE_KEY}"),
        "the request must be authenticated with the env-resolved key:\n{}",
        request.headers
    );

    // DR-16: mini writes `info.config.model` and `environment.config` into the
    // trajectory; neither may contain the secret.
    let raw = std::fs::read_to_string(&trajectory).expect("the trajectory must exist");
    assert!(
        !raw.contains(FAKE_KEY),
        "the secret leaked into the trajectory"
    );
    let value: Value = serde_json::from_str(&raw).expect("trajectory json");
    assert!(
        value["info"]["config"]["model"]["api_key"].is_null(),
        "trajectory model.api_key must be null: {}",
        value["info"]["config"]["model"]
    );

    // Restore the environment.
    match saved_openai {
        Some(value) => std::env::set_var("OPENAI_API_KEY", value),
        None => std::env::remove_var("OPENAI_API_KEY"),
    }
    match saved_hoh {
        Some(value) => std::env::set_var("HOH_MODEL_API_KEY", value),
        None => std::env::remove_var("HOH_MODEL_API_KEY"),
    }
    drop(guard);
}
