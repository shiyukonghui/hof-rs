//! DR-58 — the engine's **real** reply shapes, frozen from the real machine.
//!
//! The batch's hard rule: a payload shape may no longer be inferred from the
//! contract document.  Every assertion here is driven by a byte-for-byte copy of
//! a real payload captured during `smoke-t7` (engine
//! `4.8.dev.mono.custom_build.035edfce7`); `tests/fixtures/dr58/MANIFEST.json`
//! records each source file and its sha256, and the first test checks them.
//!
//! `runs/**` is read-only: these fixtures are copies, never edits, and the
//! manifest test re-checks the original bytes whenever the source is present.

use std::path::PathBuf;

use hof_rs::runtime::policy::sha256_hex;
use serde_json::{json, Value};

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn fixture_dir() -> PathBuf {
    repo_root().join("tests/fixtures/dr58")
}

fn fixture(name: &str) -> Value {
    let path = fixture_dir().join(name);
    let raw = std::fs::read_to_string(&path).unwrap_or_else(|error| panic!("{path:?}: {error}"));
    serde_json::from_str(&raw).unwrap_or_else(|error| panic!("{name}: {error}"))
}

fn manifest() -> Value {
    fixture("MANIFEST.json")
}

/// The MCP `tools/call` envelope's payload text, parsed.
fn inner(payload: &Value) -> Value {
    let text = payload["content"][0]["text"]
        .as_str()
        .unwrap_or_else(|| panic!("no content[0].text in {payload}"));
    serde_json::from_str(text).unwrap_or_else(|error| panic!("{text}: {error}"))
}

fn call_with_tool<'a>(raw: &'a Value, tool: &str) -> &'a Value {
    raw["calls"]
        .as_array()
        .unwrap_or_else(|| panic!("no calls array in {raw}"))
        .iter()
        .find(|call| call["tool"] == json!(tool))
        .unwrap_or_else(|| panic!("no `{tool}` call in {raw}"))
}

// ---------------------------------------------------------------------------
// ① the freeze itself
// ---------------------------------------------------------------------------

/// DR-58 ②: the tests must be driven by the **real** bytes, so the fixtures are
/// frozen copies of the captured payloads and each source and its sha256 is on
/// record.  Where the read-only source still exists, the copy is re-compared to
/// it byte for byte.
#[test]
fn the_dr58_fixtures_are_byte_for_byte_copies_of_the_real_payloads() {
    let manifest = manifest();
    let files = manifest["files"].as_array().expect("a files array");
    assert!(
        files.len() >= 8,
        "the batch's real evidence must be frozen: {files:?}"
    );
    for entry in files {
        let name = entry["fixture"].as_str().expect("fixture name");
        let source = entry["source"].as_str().expect("source path");
        let expected = entry["sha256"].as_str().expect("sha256");
        let bytes = std::fs::read(fixture_dir().join(name))
            .unwrap_or_else(|error| panic!("fixture {name}: {error}"));
        assert_eq!(
            sha256_hex(&bytes),
            expected,
            "the frozen fixture `{name}` no longer hashes to its recorded value"
        );

        let source_path = repo_root().join(source);
        if source_path.is_file() {
            let original = std::fs::read(&source_path).unwrap();
            assert_eq!(
                bytes, original,
                "`{name}` is not a byte-for-byte copy of `{source}`"
            );
            assert_eq!(
                sha256_hex(&original),
                expected,
                "`{source}` itself changed since it was frozen"
            );
        }
    }
}

// ---------------------------------------------------------------------------
// ② `running_game_run_test_scenario`: the real `scene_path` shape
// ---------------------------------------------------------------------------

/// DR-58 ③: **how the true shape was determined.**  The run's own record shows
/// hof-rs sending `scene_path: "current"` and the engine answering `-32602`;
/// the captured experiments show the same refusal for `main` and for
/// `res://scenes/main.tscn`, while every request that **omits** the member
/// succeeds.  The contract document is not the evidence — and this test pins
/// that it would have said the opposite.
#[test]
fn the_real_game_scope_runner_refuses_every_scene_path_value() {
    let summary = fixture("smoke_t7_scenario_summary.json");
    let entries = summary.as_array().expect("a summary array");

    let refused: Vec<&Value> = entries
        .iter()
        .filter(|entry| entry.get("jsonrpc_error_code").is_some())
        .collect();
    assert!(
        refused.len() >= 2,
        "the captured experiment refused at least two scene_path values: {summary}"
    );
    for entry in &refused {
        assert_eq!(entry["jsonrpc_error_code"], json!(-32602), "{entry}");
        let args = &entry["args"];
        assert!(
            args.get("scene_path").is_some(),
            "the refusal is about a request that carried `scene_path`: {entry}"
        );
        let message = entry["jsonrpc_error_message"].as_str().unwrap_or("");
        assert!(
            message.contains("is not supported by the game-scope runner"),
            "the engine's own words must be quoted: {entry}"
        );
    }

    let accepted: Vec<&Value> = entries
        .iter()
        .filter(|entry| entry.get("jsonrpc_error_code").is_none())
        .collect();
    assert!(
        accepted.len() >= 3,
        "the captured experiment accepted requests without scene_path: {summary}"
    );
    for entry in &accepted {
        let args = &entry["args"];
        assert!(
            args.get("scene_path").is_none(),
            "the accepted shape omits `scene_path` entirely: {entry}"
        );
        assert!(
            entry["parsed"]["result"]["content"].is_array(),
            "an accepted scenario answers per-step results: {entry}"
        );
    }

    // The in-run record: hof-rs sent `current`, the engine refused it.
    let probe = fixture("smoke_t7_input_channel_probe.json");
    let scenario = call_with_tool(&probe, "running_game_run_test_scenario");
    assert_eq!(scenario["args"]["scene_path"], json!("current"));
    assert_eq!(scenario["ok"], json!(false));
    assert_eq!(scenario["error"]["code"], json!(-32602));
    assert!(
        scenario["error"]["message"]
            .as_str()
            .unwrap_or("")
            .contains("'current'"),
        "the refusal names the value hof-rs sent: {scenario}"
    );

    // Why the contract document could not settle this: it *declares* the
    // parameter.  Inferring shapes from it is exactly the DR-58 defect.
    let schemas = hof_rs::tools::index::embedded_tool_schemas();
    let schema = schemas
        .iter()
        .find(|tool| tool["name"] == json!("running_game_run_test_scenario"))
        .expect("the contract still lists the scenario runner");
    assert!(
        schema
            .pointer("/inputSchema/properties/scene_path")
            .is_some(),
        "the contract advertises scene_path (optional) while the real runner refuses every value: {schema}"
    );
}

// ---------------------------------------------------------------------------
// ③ `running_game_get_node_properties`: the real reply shape
// ---------------------------------------------------------------------------

/// DR-58 ①: the real `running_game_get_node_properties` reply has exactly the
/// top-level keys `node_path` / `properties` / `type` — there is **no** top-level
/// `name`.  The pre-DR-58 predicate read `name`, so it was a constant `false`.
#[test]
fn the_real_node_properties_reply_has_no_top_level_name() {
    let raw = fixture("smoke_t7_node_and_collision_assertions.json");
    let mut seen = Vec::new();
    for node in ["Player", "Goal", "HUD"] {
        let call = raw["calls"]
            .as_array()
            .unwrap()
            .iter()
            .find(|call| {
                call["tool"] == json!("running_game_get_node_properties")
                    && call["args"]["node_path"] == json!(node)
            })
            .unwrap_or_else(|| panic!("no real payload for {node}"));
        assert_eq!(call["ok"], json!(true), "{call}");
        let payload = inner(&call["payload"]);

        let mut keys: Vec<String> = payload
            .as_object()
            .unwrap_or_else(|| panic!("{node}: the payload is an object"))
            .keys()
            .cloned()
            .collect();
        keys.sort();
        assert_eq!(
            keys,
            vec![
                "node_path".to_string(),
                "properties".to_string(),
                "type".to_string()
            ],
            "{node}: the real top-level shape"
        );
        assert!(
            payload.get("name").is_none(),
            "{node}: there is no top-level `name` to read"
        );
        assert!(
            payload["node_path"]
                .as_str()
                .unwrap_or("")
                .starts_with("/root/"),
            "{node}: the reply names the *resolved* node path"
        );
        assert!(
            payload["properties"].is_object(),
            "{node}: the property dictionary is a real object"
        );
        assert!(
            !payload["properties"].as_object().unwrap().is_empty(),
            "{node}: the dictionary is non-empty"
        );
        // The node's name lives *inside* `properties`, and only for node types
        // that have one — which is why the top-level read was wrong.
        assert_eq!(payload["properties"]["name"], json!(node), "{node}");
        seen.push(node);
    }
    assert_eq!(seen, vec!["Player", "Goal", "HUD"]);
}

/// DR-58 ②: the production predicate must accept every real payload and reject
/// every shape that does not prove a resolved node — including the exact
/// top-level-`name` read the pre-DR-58 code performed.
#[test]
fn a_real_node_properties_reply_is_a_resolved_read() {
    let raw = fixture("smoke_t7_node_and_collision_assertions.json");
    for call in raw["calls"].as_array().unwrap() {
        if call["tool"] != json!("running_game_get_node_properties") {
            continue;
        }
        let payload = inner(&call["payload"]);
        assert!(
            hof_rs::adapter::godot::node_properties_read(&payload),
            "a successful real payload must prove the node: {payload}"
        );
    }
    // The probe's own real reply (`raw/input_channel_probe.json`) is the same
    // shape, so it counts too.
    let probe = fixture("smoke_t7_input_channel_probe.json");
    let player = call_with_tool(&probe, "running_game_get_node_properties");
    let payload = inner(&player["payload"]);
    assert!(
        hof_rs::adapter::godot::node_properties_read(&payload),
        "the probe's real reply must prove the game process is reachable: {payload}"
    );
}

/// DR-58 ④ — the **non-vacuity** counterexample.  Making the predicate constant
/// `true` (to make the round look better) or constant `false` (the DR-54 bug)
/// must both fail here.
#[test]
fn an_unresolved_or_malformed_node_read_is_not_a_resolved_read() {
    use hof_rs::adapter::godot::node_properties_read;

    // The exact payload shape the pre-DR-58 code read: a top-level `name`.
    let old_read = json!({"name": "Player", "node_path": "Player"});
    // The same fixture shape the retired compatibility fixtures used.
    let retired_fixture = json!({
        "name": "Player",
        "node_path": "Player",
        "position": {"x": 60.0, "y": 283.999},
    });
    for (label, payload) in [
        ("empty object", json!({})),
        ("top-level name only", old_read),
        ("retired flattened fixture", retired_fixture),
        ("node_path without properties", json!({"node_path": "/root/Main/Player"})),
        (
            "empty properties dictionary",
            json!({"node_path": "/root/Main/Player", "properties": {}}),
        ),
        (
            "properties without node_path",
            json!({"properties": {"name": "Player"}}),
        ),
        (
            "blank node_path",
            json!({"node_path": "", "properties": {"name": "Player"}}),
        ),
        (
            "node_path is not a string",
            json!({"node_path": 7, "properties": {"name": "Player"}}),
        ),
        (
            "properties is not an object",
            json!({"node_path": "/root/Main/Player", "properties": "Player"}),
        ),
        ("null payload", json!(null)),
        ("array payload", json!([])),
    ] {
        assert!(
            !node_properties_read(&payload),
            "`{label}` does not prove a resolved node: {payload}"
        );
    }

    // …and the real payload does, from the same call site the malformed ones go
    // through, so the counterexample is not a predicate that is simply always
    // false.
    let raw = fixture("smoke_t7_node_and_collision_assertions.json");
    let real = inner(&call_with_tool(&raw, "running_game_get_node_properties")["payload"]);
    assert!(node_properties_read(&real), "{real}");
}
