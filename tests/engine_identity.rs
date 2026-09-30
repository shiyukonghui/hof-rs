//! DR-44 — engine identity: which binary are we actually driving?
//!
//! The engine switch is only worth anything if "which engine produced this
//! evidence" becomes a checkable fact.  Three artifacts carry it:
//!
//! * `meta.json.engine` — a **fixed** block (every field present; an unknown
//!   value is `null` *plus* a reason, never an omission and never a guess);
//! * the `godot.engine_binary` / `godot.engine_version` doctor items;
//! * the `engine_identity` **launch-gate step**: evidence collected through a
//!   different binary than the configured one is worthless, so the round must
//!   fail its gate.
//!
//! Everything runs through the existing [`mini_swe_agent::Environment`]
//! abstraction, so the whole probe is offline-testable and no crate dependency
//! had to be added.

use std::collections::VecDeque;
use std::path::{Path, PathBuf};
use std::sync::Mutex;

use hof_rs::adapter::engine::{
    binary_matches, doctor_items, gate_record, netstat_command, normalize_windows_path,
    probe_identity, probe_listener, process_path_command, version_command, EngineIdentity,
    ENGINE_IDENTITY_STEP_ID, ENGINE_KIND_GODOT,
};
use hof_rs::adapter::BatteryRecord;
use hof_rs::model::{Ablation, ExecKind, ExecRecord, Spec};
use hof_rs::runtime::record::{write_run_meta, RunMeta};
use mini_swe_agent::{Action, Environment, Output};
use serde_json::{json, Value};

/// A scripted `Environment`: the first reply whose needle is a substring of the
/// command wins, and every command is recorded.
#[derive(Default)]
struct FakeEnv {
    replies: Mutex<VecDeque<(String, String, i32)>>,
    commands: Mutex<Vec<String>>,
}

impl FakeEnv {
    fn with(replies: &[(&str, &str, i32)]) -> Self {
        Self {
            replies: Mutex::new(
                replies
                    .iter()
                    .map(|(needle, out, code)| (needle.to_string(), out.to_string(), *code))
                    .collect(),
            ),
            commands: Mutex::new(Vec::new()),
        }
    }

    fn commands(&self) -> Vec<String> {
        self.commands.lock().unwrap().clone()
    }
}

#[async_trait::async_trait]
impl Environment for FakeEnv {
    async fn execute(
        &self,
        action: &Action,
        _cwd: Option<&str>,
        _timeout: Option<u64>,
    ) -> mini_swe_agent::Result<Output> {
        let command = action.command.clone();
        self.commands.lock().unwrap().push(command.clone());
        let mut replies = self.replies.lock().unwrap();
        if let Some(index) = replies
            .iter()
            .position(|(needle, _, _)| command.contains(needle.as_str()))
        {
            let (_, output, code) = replies.remove(index).expect("just found");
            return Ok(Output::success(output, code));
        }
        Ok(Output::success("", 1))
    }

    fn get_template_vars(&self) -> Value {
        json!({})
    }

    fn serialize(&self) -> Value {
        json!({})
    }
}

const CONFIGURED: &str =
    "F:/moonbit-hof-rs/godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe";

fn configured_binary() -> PathBuf {
    PathBuf::from(CONFIGURED)
}

/// What `netstat -ano -p tcp` prints for a listener on 9877 plus an unrelated
/// one (the shape Windows produces).
fn netstat_output() -> String {
    "  TCP    127.0.0.1:9877         0.0.0.0:0              LISTENING       12345\r\n\
     \r\n  TCP    127.0.0.1:52000        0.0.0.0:0              LISTENING       999\r\n"
        .to_string()
}

fn listener_env(pid: u32, path: &str) -> FakeEnv {
    FakeEnv::with(&[
        (netstat_command().as_str(), netstat_output().as_str(), 0),
        (format!("-Id {pid}").as_str(), path, 0),
    ])
}

// ---------------------------------------------------------------------------
// ① the listener probe
// ---------------------------------------------------------------------------

#[tokio::test]
async fn a_listener_that_is_the_configured_binary_matches() {
    // The same file, spelled with different separators and case — the probe
    // must compare identities, not strings.
    let env = listener_env(
        12345,
        "F:\\Moonbit-HoF-RS\\godot-mcp\\godot\\bin\\GODOT.windows.editor.x86_64.MONO.exe",
    );

    let listener = probe_listener(&env, 9877, &configured_binary()).await;
    assert_eq!(listener.pid, Some(12345));
    assert_eq!(
        listener.matches_binary,
        Some(true),
        "listener: {listener:?}"
    );
    assert!(listener.reason.is_none(), "{listener:?}");
    assert!(
        env.commands()
            .iter()
            .any(|command| command == &netstat_command()),
        "the probe must use netstat: {:?}",
        env.commands()
    );
    assert!(
        env.commands()
            .iter()
            .any(|command| command == &process_path_command(12345)),
        "the probe must resolve the pid to an executable path: {:?}",
        env.commands()
    );
}

#[tokio::test]
async fn a_listener_that_is_another_binary_is_a_mismatch() {
    let env = listener_env(
        12345,
        "C:\\Other\\Godot_v4.7.1-stable_mono_win64\\godot.exe",
    );

    let listener = probe_listener(&env, 9877, &configured_binary()).await;
    assert_eq!(listener.matches_binary, Some(false), "{listener:?}");
    assert_eq!(
        listener.path.as_deref(),
        Some("C:\\Other\\Godot_v4.7.1-stable_mono_win64\\godot.exe")
    );
    // The reason must name all three facts the operator needs.
    let reason = listener.reason.unwrap_or_default();
    assert!(reason.contains(CONFIGURED), "{reason}");
    assert!(reason.contains("Godot_v4.7.1"), "{reason}");
    assert!(reason.contains("12345"), "{reason}");
}

#[tokio::test]
async fn a_probe_that_cannot_read_the_listener_is_unknown_never_a_match() {
    let env = FakeEnv::with(&[(netstat_command().as_str(), "", 0)]);

    let listener = probe_listener(&env, 9877, &configured_binary()).await;
    assert_eq!(
        listener.matches_binary, None,
        "an unreadable listener must never be reported as a match: {listener:?}"
    );
    assert!(listener.pid.is_none());
    let reason = listener.reason.unwrap_or_default();
    assert!(
        reason.contains("9877"),
        "the reason must name the port: {reason}"
    );
}

#[test]
fn path_comparison_is_separator_and_case_insensitive() {
    assert_eq!(
        normalize_windows_path("F:\\A\\B\\c.EXE"),
        normalize_windows_path("f:/a/b/C.exe")
    );
    assert!(binary_matches(Path::new("F:/A/B/c.exe"), "f:\\a\\b\\C.EXE"));
    assert!(!binary_matches(Path::new("F:/A/B/c.exe"), "F:/A/B/d.exe"));
    // `//?/` long-path prefixes and `.`/`..` components are the same file.
    assert!(binary_matches(
        Path::new("F:/A/B/../B/c.exe"),
        "\\\\?\\F:\\A\\B\\c.exe"
    ));
}

// ---------------------------------------------------------------------------
// ② the fixed `engine` block
// ---------------------------------------------------------------------------

/// The contract's keys, exactly.  A missing field is a contract violation, so
/// the assertion is on the key set rather than on individual lookups.
const ENGINE_KEYS: &[&str] = &[
    "kind",
    "binary",
    "version_string",
    "version_reason",
    "mcp",
    "listener",
    "checked_at",
];

fn keys_of(value: &Value) -> Vec<String> {
    let mut keys: Vec<String> = value
        .as_object()
        .expect("an object")
        .keys()
        .cloned()
        .collect();
    keys.sort();
    keys
}

#[tokio::test]
async fn the_engine_block_has_the_fixed_shape() {
    let temp = tempfile::tempdir().unwrap();
    let binary = temp.path().join("godot.windows.editor.x86_64.mono.exe");
    std::fs::write(&binary, b"an engine binary stand-in\n").unwrap();

    let env = FakeEnv::with(&[
        (netstat_command().as_str(), netstat_output().as_str(), 0),
        ("-Id 12345", &binary.to_string_lossy(), 0),
        (
            &version_command(&binary),
            "4.8.dev.mono.custom_build.ba1587c71\n",
            0,
        ),
    ]);

    let identity = probe_identity(
        &env,
        Some(&binary),
        Some("http://127.0.0.1:9877/mcp"),
        None,
        Value::Null,
    )
    .await;

    assert_eq!(identity.kind, ENGINE_KIND_GODOT);
    assert_eq!(keys_of(&serde_json::to_value(&identity).unwrap()), {
        let mut keys: Vec<String> = ENGINE_KEYS.iter().map(|key| key.to_string()).collect();
        keys.sort();
        keys
    });

    let block = serde_json::to_value(&identity).unwrap();
    assert_eq!(block["binary"]["path"], json!(binary.to_string_lossy()));
    assert_eq!(block["binary"]["size_bytes"], json!(26));
    assert_eq!(
        block["binary"]["sha256"],
        json!(hof_rs::runtime::policy::sha256_hex(
            b"an engine binary stand-in\n"
        ))
    );
    assert!(block["binary"]["mtime_unix"].is_u64());
    assert_eq!(block["binary"]["reason"], json!(null));
    // DR-44/C12: the version string is *recorded verbatim*, never asserted.
    assert_eq!(
        block["version_string"],
        json!("4.8.dev.mono.custom_build.ba1587c71")
    );
    assert_eq!(block["version_reason"], json!(null));
    assert_eq!(
        block["mcp"]["editor_endpoint"],
        json!("http://127.0.0.1:9877/mcp")
    );
    assert_eq!(block["mcp"]["game_endpoint"], json!(null));
    assert!(
        block["mcp"]["game_endpoint_reason"].is_string(),
        "a null game endpoint must carry a reason: {block}"
    );
    assert_eq!(block["listener"]["matches_binary"], json!(true));
    assert_eq!(block["listener"]["pid"], json!(12345));
    assert!(block["checked_at"].is_u64());
}

#[tokio::test]
async fn a_missing_binary_is_null_plus_a_reason_never_a_guess() {
    let temp = tempfile::tempdir().unwrap();
    let binary = temp.path().join("not-there.exe");
    let env = FakeEnv::default();

    let identity = probe_identity(&env, Some(&binary), None, None, Value::Null).await;
    let block = serde_json::to_value(&identity).unwrap();
    assert_eq!(block["binary"]["size_bytes"], json!(null));
    assert_eq!(block["binary"]["sha256"], json!(null));
    assert_eq!(block["binary"]["mtime_unix"], json!(null));
    let reason = block["binary"]["reason"].as_str().unwrap_or("");
    assert!(reason.contains("not-there.exe"), "{block}");
    assert_eq!(
        block["version_string"],
        json!(null),
        "no binary, no version: {block}"
    );
    assert!(block["version_reason"].is_string(), "{block}");
    assert!(
        !env.commands()
            .iter()
            .any(|command| command.contains("--version")),
        "an absent binary must not be executed: {:?}",
        env.commands()
    );
}

#[tokio::test]
async fn an_unavailable_engine_is_still_a_complete_block() {
    let identity = EngineIdentity::unavailable("this adapter reports no engine binary");
    let block = serde_json::to_value(&identity).unwrap();
    assert_eq!(keys_of(&block), {
        let mut keys: Vec<String> = ENGINE_KEYS.iter().map(|key| key.to_string()).collect();
        keys.sort();
        keys
    });
    assert_eq!(block["binary"]["path"], json!(null));
    assert!(block["binary"]["reason"].is_string());
    assert!(block["listener"]["reason"].is_string());
    assert_eq!(block["listener"]["matches_binary"], json!(null));
    // No engine binary means no gate step at all: an adapter without one has no
    // identity to check (and pretending it did would fail every run).
    assert!(gate_record(&identity).is_none());
}

// ---------------------------------------------------------------------------
// ③ the `engine_identity` launch-gate step
// ---------------------------------------------------------------------------

fn gate_support() -> Vec<BatteryRecord> {
    let record = |step_id: &str, ok: bool| BatteryRecord {
        step_id: step_id.to_string(),
        supports: vec!["N1".to_string()],
        record: ExecRecord {
            kind: ExecKind::Build,
            path: None,
            observation: "supporting step".to_string(),
            candidate_id: String::new(),
        },
        ok,
        raw_path: None,
    };
    vec![
        record("editor_errors_baseline", true),
        record("play_scene_ready", true),
    ]
}

/// A hermetic configured binary: a small temp file, never the real engine (the
/// probe reads the file, so a 194 MB image would only slow the suite down).
fn temp_binary(dir: &Path) -> PathBuf {
    let binary = dir.join("godot.windows.editor.x86_64.mono.exe");
    std::fs::write(&binary, b"engine stand-in\n").unwrap();
    binary
}

async fn mismatching_identity(expected: &Path) -> EngineIdentity {
    let env = listener_env(12345, "C:\\Other\\godot.exe");
    probe_identity(
        &env,
        Some(expected),
        Some("http://127.0.0.1:9877/mcp"),
        None,
        Value::Null,
    )
    .await
}

#[tokio::test]
async fn the_gate_closes_when_the_listener_is_another_binary() {
    let temp = tempfile::tempdir().unwrap();
    let expected = temp_binary(temp.path());
    let identity = mismatching_identity(&expected).await;
    let mut battery = gate_support();
    let step = gate_record(&identity).expect("a configured binary yields a gate step");
    assert_eq!(step.step_id, ENGINE_IDENTITY_STEP_ID);
    assert!(!step.ok, "a mismatch must fail the step: {step:?}");
    battery.push(step);

    let gate = hof_rs::adapter::evaluate_launchable(&battery);
    assert!(!gate.launchable, "the gate must close: {gate:?}");
    let reasons = gate.reasons.join("\n");
    assert!(reasons.contains(ENGINE_IDENTITY_STEP_ID), "{reasons}");
    assert!(
        reasons.contains(&expected.to_string_lossy().to_string()),
        "the reason must name the configured binary: {reasons}"
    );
    assert!(
        reasons.contains("godot.exe"),
        "the reason must name the actual listener: {reasons}"
    );
    assert!(
        reasons.contains("12345"),
        "the reason must name the pid: {reasons}"
    );
}

#[tokio::test]
async fn the_gate_stays_open_when_the_listener_is_the_configured_binary() {
    let temp = tempfile::tempdir().unwrap();
    let expected = temp_binary(temp.path());
    let env = listener_env(12345, &expected.to_string_lossy());
    let identity = probe_identity(
        &env,
        Some(&expected),
        Some("http://127.0.0.1:9877/mcp"),
        None,
        Value::Null,
    )
    .await;
    let mut battery = gate_support();
    battery.push(gate_record(&identity).expect("a gate step"));
    let gate = hof_rs::adapter::evaluate_launchable(&battery);
    assert!(gate.launchable, "{gate:?}");
}

/// DR-53 (DEF-3): the **third** gate case — the listener could not be read
/// (`matches_binary == None`).  "Silence is failure" (§0.2): an unverifiable
/// identity must close the gate, and its observation must be distinguishable
/// from a mismatch so the reader is never misled.
#[tokio::test]
async fn the_gate_closes_when_the_listener_cannot_be_read() {
    let temp = tempfile::tempdir().unwrap();
    let expected = temp_binary(temp.path());

    // `netstat` answers, but no listener on the editor port.
    let env = FakeEnv::with(&[(netstat_command().as_str(), "", 0)]);
    let identity = probe_identity(
        &env,
        Some(&expected),
        Some("http://127.0.0.1:9877/mcp"),
        None,
        Value::Null,
    )
    .await;
    assert_eq!(
        identity.listener.matches_binary, None,
        "an unreadable listener is never a match: {identity:?}"
    );

    let step = gate_record(&identity).expect("a configured binary yields a gate step");
    assert!(
        !step.ok,
        "an unverifiable identity must close the gate: {step:?}"
    );
    let observation = step.record.observation.clone();
    assert!(
        observation.contains("no TCP listener"),
        "the observation must name why it could not verify: {observation}"
    );
    assert!(
        observation.contains("UNAVAILABLE"),
        "the observation must be explicit about the gap: {observation}"
    );
    // Distinguishable from a mismatch: a mismatch names the actual listener.
    let mismatch = mismatching_identity(&expected).await;
    let mismatch_step = gate_record(&mismatch).expect("a gate step");
    assert!(
        mismatch_step
            .record
            .observation
            .contains("engine identity mismatch"),
        "{:?}",
        mismatch_step.record.observation
    );
    assert_ne!(
        observation, mismatch_step.record.observation,
        "the two failures must not read alike"
    );

    // And the gate really closes.
    let mut battery = gate_support();
    battery.push(step);
    let gate = hof_rs::adapter::evaluate_launchable(&battery);
    assert!(
        !gate.launchable,
        "an unreadable listener must not freeze as launchable: {gate:?}"
    );
    assert!(
        gate.reasons.join(" ").contains(ENGINE_IDENTITY_STEP_ID),
        "{:?}",
        gate.reasons
    );
}

/// The step id must be part of the gate's vocabulary (DR-44 ⑤).
#[test]
fn the_engine_identity_step_is_a_gate_step() {
    assert!(
        hof_rs::adapter::GATE_STEP_IDS.contains(&ENGINE_IDENTITY_STEP_ID),
        "GATE_STEP_IDS: {:?}",
        hof_rs::adapter::GATE_STEP_IDS
    );
}

// ---------------------------------------------------------------------------
// ④ the two `hof doctor` items (DR-44 ②)
// ---------------------------------------------------------------------------

#[tokio::test]
async fn the_two_engine_doctor_items_report_the_binary_and_its_version() {
    let temp = tempfile::tempdir().unwrap();
    let binary = temp.path().join("godot.exe");
    std::fs::write(&binary, b"x").unwrap();
    let env = FakeEnv::with(&[(
        version_command(&binary).as_str(),
        "4.8.dev.mono.custom_build.ba1587c71\n",
        0,
    )]);

    let items = doctor_items(&env, &binary).await;
    let binary_item = items
        .iter()
        .find(|item| item.name == "godot.engine_binary")
        .expect("godot.engine_binary must be reported");
    assert!(binary_item.ok, "{binary_item:?}");
    assert!(
        binary_item
            .detail
            .contains(&binary.to_string_lossy().to_string()),
        "{binary_item:?}"
    );
    assert!(binary_item.detail.contains("size"), "{binary_item:?}");
    assert!(binary_item.detail.contains("mtime"), "{binary_item:?}");

    let version_item = items
        .iter()
        .find(|item| item.name == "godot.engine_version")
        .expect("godot.engine_version must be reported");
    assert!(version_item.ok, "{version_item:?}");
    // The version string is recorded **verbatim** — it is never a judgement.
    assert_eq!(version_item.detail, "4.8.dev.mono.custom_build.ba1587c71");
}

#[tokio::test]
async fn a_missing_binary_fails_the_items_without_executing_anything() {
    let temp = tempfile::tempdir().unwrap();
    let binary = temp.path().join("absent.exe");
    let env = FakeEnv::default();

    let items = doctor_items(&env, &binary).await;
    let binary_item = items
        .iter()
        .find(|item| item.name == "godot.engine_binary")
        .expect("godot.engine_binary must be reported");
    assert!(!binary_item.ok, "{binary_item:?}");
    let version_item = items
        .iter()
        .find(|item| item.name == "godot.engine_version")
        .expect("godot.engine_version must be reported");
    assert!(!version_item.ok, "{version_item:?}");
    assert!(
        version_item.detail.contains("does not exist"),
        "{version_item:?}"
    );
    assert!(
        env.commands().is_empty(),
        "an absent binary must never be executed: {:?}",
        env.commands()
    );
}

// ---------------------------------------------------------------------------
// ⑥ DR-51 — the MCP endpoint facts must be real, recorded values
// ---------------------------------------------------------------------------

/// The `GET /mcp` status document the engine answers (the `smoke-t6` live shape,
/// abbreviated).
const STATUS_BODY: &str = "{\"connections\":1,\"is_editor\":true,\"port\":9877,\"tools\":154}";

/// A one-shot loopback double that answers `GET /mcp` with `body`.
fn status_double(body: &'static str) -> (String, std::thread::JoinHandle<()>) {
    use std::io::{Read, Write};
    let listener = std::net::TcpListener::bind("127.0.0.1:0").expect("loopback listener");
    let addr = listener.local_addr().expect("bound address");
    let handle = std::thread::spawn(move || {
        let (mut stream, _) = listener.accept().expect("a status request");
        let mut buffer = [0u8; 2048];
        let _ = stream.read(&mut buffer);
        let response = format!(
            "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\
             Connection: close\r\n\r\n{body}",
            body.len()
        );
        let _ = stream.write_all(response.as_bytes());
        let _ = stream.flush();
    });
    (format!("http://{addr}/mcp"), handle)
}

/// DR-51: a real `GET /mcp` is performed and its **verbatim** body is what the
/// identity records.
#[tokio::test]
async fn the_editor_status_is_the_verbatim_get_mcp_body() {
    let (url, handle) = status_double(STATUS_BODY);
    let body = hof_rs::tools::mcp::fetch_editor_status(&url, 5).expect("the status body");
    handle.join().expect("the double must finish");

    assert_eq!(body["is_editor"], json!(true));
    assert_eq!(body["tools"], json!(154));
    assert_eq!(body["port"], json!(9877));
    assert_eq!(
        body.to_string(),
        serde_json::from_str::<Value>(STATUS_BODY)
            .unwrap()
            .to_string(),
        "the body must be recorded verbatim"
    );
}

/// DR-51: an unreachable endpoint yields `null` + a reason and never fails the
/// run (`smoke-t6`'s reason text was wrong precisely where the value was not).
#[tokio::test]
async fn an_unreachable_endpoint_yields_no_status_and_no_failure() {
    let error = hof_rs::tools::mcp::fetch_editor_status("http://127.0.0.1:1/mcp", 1)
        .expect_err("a closed port has no status body");
    assert!(error.contains("127.0.0.1:1"), "{error}");

    let mut identity = probe_identity(
        &FakeEnv::default(),
        Some(Path::new(CONFIGURED)),
        Some("http://127.0.0.1:1/mcp"),
        None,
        Value::Null,
    )
    .await;
    // The block still carries the fixed shape with a reason for the null.
    let block = serde_json::to_value(&identity).unwrap();
    assert_eq!(block["mcp"]["editor_status"], json!(null));
    assert!(block["mcp"]["editor_status_reason"].is_string());
    // And a status that *is* known fills the field and clears the reason.
    identity.mcp.editor_status = serde_json::from_str(STATUS_BODY).unwrap();
    identity.mcp.editor_status_reason = None;
    let block = serde_json::to_value(&identity).unwrap();
    assert_eq!(block["mcp"]["editor_status"]["tools"], json!(154));
    assert_eq!(block["mcp"]["editor_status_reason"], json!(null));
}

/// DR-51: the status is only fetched for an adapter that drives an engine — an
/// adapter without a binary must not touch the network, and a failed fetch must
/// degrade to `null`, never to an error.
#[test]
fn the_status_fetch_is_gated_on_the_adapter_driving_an_engine() {
    let fetch = |endpoint: &str| -> Result<Value, String> {
        Ok(json!({"endpoint": endpoint, "tools": 154}))
    };
    assert_eq!(
        hof_rs::runtime::engine_identity::editor_status_for(false, "http://x/mcp", |_| panic!(
            "an adapter without an engine binary must not fetch"
        )),
        Value::Null
    );
    assert_eq!(
        hof_rs::runtime::engine_identity::editor_status_for(true, "http://x/mcp", fetch),
        json!({"endpoint": "http://x/mcp", "tools": 154})
    );
    assert_eq!(
        hof_rs::runtime::engine_identity::editor_status_for(true, "http://x/mcp", |_| Err(
            "closed".to_string()
        )),
        Value::Null,
        "a failed fetch is a reason, never a run failure"
    );
}

/// DR-51: folding a registered game endpoint into the block fills the field and
/// removes the reason (and is idempotent).
#[tokio::test]
async fn recording_a_game_endpoint_fills_the_identity_block() {
    let record = hof_rs::tools::endpoint::GameEndpointRecord {
        endpoint: "http://127.0.0.1:63698/mcp".to_string(),
        port: Some(63698),
        source: hof_rs::tools::endpoint::SOURCE_AUTO_FREE_PORT.to_string(),
        pid: Some(101872),
    };
    let mut identity = EngineIdentity::unavailable("nothing was probed");
    assert!(identity.mcp.game_endpoint.is_none());
    assert!(identity.mcp.game_endpoint_reason.is_some());

    assert!(
        hof_rs::adapter::engine::record_game_endpoint(&mut identity, &record),
        "the first record changes the block"
    );
    let block = serde_json::to_value(&identity).unwrap();
    assert_eq!(block["mcp"]["game_endpoint"]["port"], json!(63698));
    assert_eq!(
        block["mcp"]["game_endpoint"]["source"],
        json!("auto_free_port")
    );
    assert_eq!(block["mcp"]["game_endpoint_reason"], json!(null));
    assert!(
        !hof_rs::adapter::engine::record_game_endpoint(&mut identity, &record),
        "recording the same endpoint twice is a no-op"
    );
}

// ---------------------------------------------------------------------------
// ⑤ `meta.json` carries the block (DR-44 ③, C11 hygiene)
// ---------------------------------------------------------------------------

fn meta_with(engine: EngineIdentity, config: Value) -> RunMeta {
    RunMeta {
        run_id: "run-1".to_string(),
        spec: Spec {
            path: "spec.md".into(),
            sha256: "0".repeat(64),
        },
        ablation: Ablation::default(),
        iterations: 1,
        model_identity: "model|openai_compatible|model".to_string(),
        started_at: 0,
        hoh_version: "test".to_string(),
        warnings: vec![],
        config,
        start_state: hof_rs::runtime::start_state::StartState::as_is(),
        engine,
    }
}

#[tokio::test]
async fn meta_json_carries_the_engine_block_and_no_secret() {
    const FAKE_KEY: &str = "test-key-not-a-secret";
    let dir = tempfile::tempdir().unwrap();
    let expected = temp_binary(dir.path());
    let env = listener_env(12345, "C:\\Other\\godot.exe");
    let identity = probe_identity(
        &env,
        Some(&expected),
        Some("http://127.0.0.1:9877/mcp"),
        None,
        Value::Null,
    )
    .await;

    let temp = tempfile::tempdir().unwrap();
    let run_dir = temp.path().join("runs/run-1");
    write_run_meta(
        &run_dir,
        &meta_with(identity, json!({"model_name": "m", "api_key": FAKE_KEY})),
    )
    .expect("write meta");

    let raw = std::fs::read_to_string(run_dir.join("meta.json")).expect("read meta");
    assert!(
        !raw.contains(FAKE_KEY),
        "no secret may reach meta.json, including through the engine block (C11/DR-44):\n{raw}"
    );
    let value: Value = serde_json::from_str(&raw).expect("json");
    assert_eq!(keys_of(&value["engine"]), {
        let mut keys: Vec<String> = ENGINE_KEYS.iter().map(|key| key.to_string()).collect();
        keys.sort();
        keys
    });
    assert_eq!(value["engine"]["listener"]["matches_binary"], json!(false));
    assert!(value["engine"]["checked_at"].is_u64());
}
