//! C9/C10 — the on-the-wire model id is locked by observing a real HTTP
//! request.  `effective_model_name` is `pub(crate)` in mini, so the only
//! trustworthy way to assert the wire value is to serve the request ourselves.

use std::io::{Read, Write};
use std::net::TcpListener;
use std::sync::mpsc;

use mini_swe_agent::environments::{LocalEnvironment, LocalEnvironmentConfig};
use mini_swe_agent::models::{ApiMode, LlmConnectorModel};
use mini_swe_agent::{Agent, AgentConfig, AgentMode, DefaultAgent, Model};
use serde_json::{json, Value};

/// A single-request HTTP server that records the request body it received.
///
/// `std::net` is used deliberately: it is part of the standard library, always
/// available offline, and cannot drift the way an HTTP client dependency can.
fn spawn_fake_chat_server() -> (u16, mpsc::Receiver<Value>) {
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
            if let Ok(value) = serde_json::from_slice::<Value>(body) {
                let _ = sender.send(value);
            }

            let response_body = chat_completion();
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
fn chat_completion() -> String {
    json!({
        "id": "chatcmpl-fake",
        "object": "chat.completion",
        "created": 0,
        "model": "qwen/qwen3.8-27b",
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

#[tokio::test]
async fn wire_model_id_is_exact() {
    let (port, received) = spawn_fake_chat_server();
    let model_json = json!({
        "model_name": "openai/qwen/qwen3.8-27b",
        "provider": "openai_compatible",
        "service_name": "openai_compatible",
        "base_url": format!("http://127.0.0.1:{port}"),
        "api_key": "lm-studio",
        "use_tool_calls": true,
        "request_timeout_secs": 30,
        "max_retries": 1
    });

    let model =
        LlmConnectorModel::from_value_with_mode(model_json, ApiMode::ToolCalls).expect("model");
    // The configured identity keeps the `openai/` prefix (that is what D6 strips).
    assert_eq!(model.model_name(), "openai/qwen/qwen3.8-27b");

    let temp = tempfile::tempdir().expect("tempdir");
    let env_config = LocalEnvironmentConfig {
        cwd: temp.path().to_string_lossy().into_owned(),
        timeout: 30,
        env: Default::default(),
    };
    let environment = LocalEnvironment::new(env_config);

    let config = AgentConfig {
        system_template: "{{hoh_system_prompt}}".to_string(),
        instance_template: "{{task}}".to_string(),
        step_limit: 4,
        // 0.0 is mandatory: mini's default of 3.0 would abort a local run.
        cost_limit: 0.0,
        wall_time_limit_seconds: 60,
        max_consecutive_format_errors: 3,
        output_path: None,
        mode: AgentMode::Yolo,
        whitelist_actions: Vec::new(),
        confirm_exit: false,
    };
    let mut agent = DefaultAgent::new(Box::new(model), Box::new(environment), config);

    let _ = agent
        .run(
            "say hello",
            Some(json!({"hoh_system_prompt": "you are the planner"})),
        )
        .await;

    let request = received
        .recv_timeout(std::time::Duration::from_secs(60))
        .expect("the fake server must receive a chat request");

    assert_eq!(
        request["model"],
        json!("qwen/qwen3.8-27b"),
        "the on-the-wire model id must be exactly the canonical LM Studio id (C9)"
    );
    // The role text must travel as a template *value*, not as template source.
    assert_eq!(
        request["messages"][0]["content"],
        json!("you are the planner")
    );
    assert_eq!(request["messages"][1]["content"], json!("say hello"));
}
