//! DR-15 / DR-16 (C11/C12) — `hoh doctor` probes are generic and authenticated:
//!
//! * `model.chat` carries `Authorization: Bearer <resolved api_key>` and locks
//!   the **response** `model` field to the configured `wire_model_name`;
//! * `model.resident` (LM Studio's `/api/v0/models`) only runs on loopback and
//!   is `ok = true` when skipped — it must never block a run (C12);
//! * the bare-id duplicate rule is derived from `wire_model_name`, not from a
//!   hard-coded vendor id.
//!
//! Every endpoint here is a local `std::net::TcpListener`; nothing touches the
//! network and no real credential is involved.

use std::io::{Read, Write};
use std::net::TcpListener;
use std::sync::mpsc;
use std::sync::Mutex;

use hof_rs::adapter::{DoctorItem, TestAdapter};
use hof_rs::cli_impl::doctor_checks;
use hof_rs::config::load_config;

/// The fake secret.  It is deliberately shaped like a placeholder so the
/// repository-wide `sk-` audit stays clean.
const FAKE_KEY: &str = "test-key-not-a-secret";

/// Serializes every test that touches process-global environment variables.
static ENV_LOCK: Mutex<()> = Mutex::new(());

#[derive(Debug, Clone)]
struct Recorded {
    path: String,
    headers: String,
    body: serde_json::Value,
}

#[derive(Debug, Clone)]
struct FakeEndpoint {
    /// `model` field echoed in the chat completion response.
    response_model: String,
    /// `null` => the `/api/v0/models` API is absent (404).
    models: Option<serde_json::Value>,
}

/// A loopback HTTP endpoint serving `POST /v1/chat/completions` and,
/// optionally, `GET /api/v0/models`.
fn spawn_fake_endpoint(spec: FakeEndpoint) -> (u16, mpsc::Receiver<Recorded>) {
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
            let path = headers
                .lines()
                .next()
                .and_then(|line| line.split_whitespace().nth(1))
                .unwrap_or("")
                .to_string();
            let _ = sender.send(Recorded {
                path: path.clone(),
                headers: headers.clone(),
                body: serde_json::from_slice(body).unwrap_or(serde_json::Value::Null),
            });

            let response = if path.ends_with("/chat/completions") {
                let payload = serde_json::json!({
                    "id": "chatcmpl-fake",
                    "object": "chat.completion",
                    "created": 0,
                    "model": spec.response_model,
                    "choices": [{
                        "index": 0,
                        "message": {"role": "assistant", "content": "pong"},
                        "finish_reason": "stop"
                    }]
                })
                .to_string();
                http_response(200, "OK", &payload)
            } else if path.ends_with("/api/v0/models") {
                match &spec.models {
                    Some(value) => http_response(200, "OK", &value.to_string()),
                    None => http_response(404, "Not Found", "{\"error\":\"no such route\"}"),
                }
            } else {
                http_response(404, "Not Found", "{\"error\":\"no such route\"}")
            };
            let _ = stream.write_all(response.as_bytes());
            let _ = stream.flush();
        }
    });

    (port, receiver)
}

fn http_response(status: u16, reason: &str, body: &str) -> String {
    format!(
        "HTTP/1.1 {status} {reason}\r\nContent-Type: application/json\r\n\
         Content-Length: {}\r\nConnection: close\r\n\r\n{body}",
        body.len()
    )
}

/// Run `f` with the given environment variables set, restoring the previous
/// values afterwards.  All env-mutating tests share one lock.
fn with_env<T>(vars: &[(&str, Option<&str>)], f: impl FnOnce() -> T) -> T {
    let guard = ENV_LOCK
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    let saved: Vec<(String, Option<String>)> = vars
        .iter()
        .map(|(name, _)| (name.to_string(), std::env::var(name).ok()))
        .collect();
    for (name, value) in vars {
        match value {
            Some(value) => std::env::set_var(name, value),
            None => std::env::remove_var(name),
        }
    }
    let result = f();
    for (name, value) in &saved {
        match value {
            Some(value) => std::env::set_var(name, value),
            None => std::env::remove_var(name),
        }
    }
    drop(guard);
    result
}

/// `doctor_checks` is async; run it on a private current-thread runtime so the
/// env lock can be held for the whole probe.
fn probe(config_overrides: &[String]) -> Vec<DoctorItem> {
    let specs: Vec<String> = std::iter::once("config/hoh.yaml".to_string())
        .chain(config_overrides.iter().cloned())
        .chain(std::iter::once(
            // Keep the MCP check offline and instantaneous.
            "tools.endpoint=http://127.0.0.1:1/mcp".to_string(),
        ))
        .chain(std::iter::once("tools.max_retries=0".to_string()))
        .collect();
    let config = load_config(&specs).expect("config");
    let adapter = TestAdapter::new();
    let workspace = config.runtime.workspace.clone();
    tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .expect("runtime")
        .block_on(async { doctor_checks(&config, &adapter, &workspace).await })
        .expect("doctor checks")
}

fn item<'a>(items: &'a [DoctorItem], name: &str) -> &'a DoctorItem {
    items
        .iter()
        .find(|item| item.name == name)
        .unwrap_or_else(|| panic!("missing doctor item `{name}`: {items:?}"))
}

fn wire_model_name() -> String {
    load_config(&[])
        .expect("config")
        .wire_model_name()
        .to_string()
}

fn base_url(port: u16) -> String {
    format!("model.base_url=http://127.0.0.1:{port}/v1")
}

#[test]
fn chat_probe_sends_the_bearer_token_and_accepts_the_configured_wire_model() {
    let wire = wire_model_name();
    let (port, received) = spawn_fake_endpoint(FakeEndpoint {
        response_model: wire.clone(),
        models: None,
    });

    let items = with_env(&[("HOH_MODEL_API_KEY", Some(FAKE_KEY))], || {
        probe(&[base_url(port)])
    });

    let chat = item(&items, "model.chat");
    assert!(chat.ok, "chat probe must pass: {chat:?}");
    assert!(chat.detail.contains(&wire), "detail: {}", chat.detail);

    let request = received
        .recv_timeout(std::time::Duration::from_secs(30))
        .expect("the fake endpoint must receive the chat request");
    assert_eq!(request.body["model"], serde_json::json!(wire));
    assert!(
        request.path.ends_with("/v1/chat/completions"),
        "unexpected probe path: {}",
        request.path
    );
    let authorization = request
        .headers
        .lines()
        .find(|line| line.to_ascii_lowercase().starts_with("authorization:"))
        .map(|line| line[line.find(':').unwrap() + 1..].trim().to_string())
        .unwrap_or_default();
    assert_eq!(
        authorization,
        format!("Bearer {FAKE_KEY}"),
        "the probe must authenticate with the env-resolved key (DR-15/DR-16):\n{}",
        request.headers
    );
}

#[test]
fn chat_probe_fails_when_the_endpoint_reports_a_different_model() {
    let wire = wire_model_name();
    let (port, _received) = spawn_fake_endpoint(FakeEndpoint {
        response_model: format!("{wire}-mismatch"),
        models: None,
    });

    let items = with_env(&[("HOH_MODEL_API_KEY", Some(FAKE_KEY))], || {
        probe(&[base_url(port)])
    });

    let chat = item(&items, "model.chat");
    assert!(
        !chat.ok,
        "a wrong response model must fail the probe: {chat:?}"
    );
    assert!(
        chat.detail.contains("instead of"),
        "detail must name the mismatch: {}",
        chat.detail
    );
    assert!(
        chat.detail.contains(&format!("{wire}-mismatch")) && chat.detail.contains(&wire),
        "detail: {}",
        chat.detail
    );
}

#[test]
fn chat_probe_without_a_resolvable_key_is_not_ok() {
    let wire = wire_model_name();
    let (port, _received) = spawn_fake_endpoint(FakeEndpoint {
        response_model: wire,
        models: None,
    });

    let items = with_env(
        &[("HOH_MODEL_API_KEY", None), ("OPENAI_API_KEY", None)],
        || probe(&[base_url(port)]),
    );

    let chat = item(&items, "model.chat");
    assert!(
        !chat.ok,
        "no key must not be reported as a healthy probe: {chat:?}"
    );
    assert!(
        chat.detail.contains("no api key resolved"),
        "detail must say `no api key resolved`: {}",
        chat.detail
    );
}

#[test]
fn resident_probe_is_skipped_off_loopback_without_blocking_a_run() {
    let items = with_env(&[("HOH_MODEL_API_KEY", Some(FAKE_KEY))], || {
        probe(&["model.base_url=http://remote.invalid:1/v1".to_string()])
    });

    let resident = item(&items, "model.resident");
    assert!(
        resident.ok,
        "a skipped resident probe must never block a run (C12): {resident:?}"
    );
    assert!(
        resident.detail.starts_with("skipped:"),
        "detail must be explicit about skipping: {}",
        resident.detail
    );
}

#[test]
fn resident_probe_is_skipped_when_the_endpoint_has_no_models_api() {
    let wire = wire_model_name();
    let (port, _received) = spawn_fake_endpoint(FakeEndpoint {
        response_model: wire,
        models: None,
    });

    let items = with_env(&[("HOH_MODEL_API_KEY", Some(FAKE_KEY))], || {
        probe(&[base_url(port)])
    });

    let resident = item(&items, "model.resident");
    assert!(
        resident.ok,
        "a missing LM Studio API is a skip, not a failure (C12): {resident:?}"
    );
    assert!(
        resident.detail.starts_with("skipped:"),
        "detail: {}",
        resident.detail
    );
}

#[test]
fn resident_probe_flags_a_bare_duplicate_of_a_prefixed_wire_name() {
    let (port, _received) = spawn_fake_endpoint(FakeEndpoint {
        response_model: "vendor/some-model".to_string(),
        models: Some(serde_json::json!({
            "data": [
                {"id": "vendor/some-model", "state": "loaded"},
                {"id": "some-model", "state": "loaded"}
            ]
        })),
    });

    let items = with_env(&[("HOH_MODEL_API_KEY", Some(FAKE_KEY))], || {
        probe(&[
            base_url(port),
            "model.wire_model_name=vendor/some-model".to_string(),
        ])
    });

    let resident = item(&items, "model.resident");
    assert!(
        !resident.ok,
        "a bare duplicate instance must still be reported (D6, generalised): {resident:?}"
    );
    assert!(
        resident.detail.contains("some-model") && !resident.detail.contains("qwen"),
        "detail must name the generic stripped id: {}",
        resident.detail
    );
}

#[test]
fn resident_probe_does_not_invent_a_duplicate_for_an_unprefixed_wire_name() {
    let wire = wire_model_name();
    let (port, _received) = spawn_fake_endpoint(FakeEndpoint {
        response_model: wire.clone(),
        models: Some(serde_json::json!({
            "data": [{"id": wire, "state": "loaded"}]
        })),
    });

    let items = with_env(&[("HOH_MODEL_API_KEY", Some(FAKE_KEY))], || {
        probe(&[base_url(port)])
    });

    let resident = item(&items, "model.resident");
    assert!(
        resident.ok,
        "the single loaded instance of an unprefixed wire id is not a duplicate: {resident:?}"
    );
}

/// A guard against the probe accidentally reading a stale constant: the model
/// section itself must be the only source of the expected wire id.
#[test]
fn doctor_reads_the_wire_name_from_a_values_not_from_a_constant() {
    let (port, _received) = spawn_fake_endpoint(FakeEndpoint {
        response_model: "operator-chosen-model".to_string(),
        models: None,
    });
    let items = with_env(&[("HOH_MODEL_API_KEY", Some(FAKE_KEY))], || {
        probe(&[
            base_url(port),
            "model.wire_model_name=operator-chosen-model".to_string(),
        ])
    });
    let chat = item(&items, "model.chat");
    assert!(
        chat.ok,
        "config-provided wire name must be accepted: {chat:?}"
    );
}
