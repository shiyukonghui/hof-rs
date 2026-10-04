//! BATCH-B1 cross-module pins: the frozen contract, the frozen tool list and the
//! round-evidence layout.
//!
//! **BATCH-B2 re-pinned two of these literals deliberately.**  D297 (b) added the
//! game frame counter as the seventh reflectable surface and D297 (c) put the
//! semantic layer's return shapes into `tools/list`, and both are contract
//! changes, so `CONTRACT_SHA256` moved
//! `4af153e7…` -> `792001e7…` and `TOOL_LIST_SHA256` moved
//! `e177325f…` -> `bcf03c0b…`.  The assertions below still compare against the
//! constants, so they are pins, not restatements.  The tool count is unchanged
//! (no tool was added or removed; the frame counter is read *inside* the calls
//! that already existed).
//!
//! These are integration-level because they are the properties that hold the
//! *system* together: the contract hash, the tool-list hash and the eight
//! semantic names must not drift silently.

use std::path::PathBuf;
use std::time::Duration;

use hof_rs::adapter::bevy::brp::BrpClient;
use hof_rs::adapter::bevy::build::feature_set_sha256;
use hof_rs::adapter::bevy::contract::{
    check_game_crate_name, check_registered_type_paths, contract_sha256, contract_value, CONTRACT,
    CONTRACT_SHA256, GAME_CRATE, SEMANTIC_TOOLS,
};
use hof_rs::adapter::mcp::evidence::{
    meta_json, round_dir, write_round, CallEvidence, RoundEvidence, RoundHashes, LAYOUT,
};
use hof_rs::adapter::mcp::generic::{brp_method_names, BRP_VERBS};
use hof_rs::adapter::mcp::semantic::{semantic_tool_names, SEMANTIC_TOOL_SPECS};

#[test]
fn the_frozen_contract_hash_and_crate_name_are_pinned() {
    assert_eq!(contract_sha256(), CONTRACT_SHA256, "the contract drifted");
    assert_eq!(CONTRACT_SHA256.len(), 64);
    assert_eq!(CONTRACT.len(), 7, "seven surfaces since D297 (b)");
    assert_eq!(GAME_CRATE, "hof_game");
    assert!(contract_value().is_array());
    let paths: Vec<String> = CONTRACT.iter().map(|e| e.type_path.to_string()).collect();
    assert!(check_registered_type_paths(&paths).is_ok());
    let missing: Vec<String> = paths
        .iter()
        .filter(|path| path.as_str() != "hof_game::contract::Grounded")
        .cloned()
        .collect();
    assert!(check_registered_type_paths(&missing).is_err());
    assert!(check_game_crate_name("[package]\nname = \"hof_game\"\n").is_ok());
}

#[test]
fn the_tool_list_hash_and_the_eight_semantic_names_are_pinned() {
    assert_eq!(
        hof_rs::adapter::mcp::tool_list_sha256(),
        hof_rs::adapter::mcp::TOOL_LIST_SHA256,
        "the frozen tool surface drifted"
    );
    assert_eq!(hof_rs::adapter::mcp::TOOL_LIST_SHA256.len(), 64);
    assert_eq!(BRP_VERBS.len(), 23);
    assert_eq!(SEMANTIC_TOOL_SPECS.len(), 8);
    assert_eq!(
        semantic_tool_names(),
        vec![
            "bevy_player_transform",
            "bevy_grounded",
            "bevy_coin_counter",
            "bevy_win_flag",
            "bevy_inject_move",
            "bevy_inject_jump",
            "bevy_wait_frames",
            "bevy_health",
        ]
    );
    assert_eq!(SEMANTIC_TOOLS, semantic_tool_names().as_slice());
    assert_eq!(brp_method_names()[0], "rpc.discover");
    assert_eq!(brp_method_names()[22], "schedule.graph");
}

#[test]
fn the_generic_layer_keeps_the_verb_names_and_the_old_vocabulary_out() {
    let godot: Vec<String> = hof_rs::tools::index::embedded_tool_schemas()
        .iter()
        .filter_map(|tool| tool.get("name").and_then(|name| name.as_str()))
        .map(ToOwned::to_owned)
        .collect();
    assert!(godot.len() > 100);
    for verb in BRP_VERBS {
        assert_eq!(verb.name, verb.method.expect("a generic verb"));
        assert!(
            !godot.iter().any(|name| name == verb.name),
            "`{}` is an old Godot tool name",
            verb.name
        );
    }
}

#[test]
fn the_round_evidence_layout_and_hashes_are_the_designs() {
    let repository_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let lockfile = repository_root.join("Cargo.lock");
    let hashes = RoundHashes::measure(&lockfile).unwrap();
    assert_eq!(hashes.contract_sha256, contract_sha256());
    assert_eq!(hashes.feature_sha256, feature_set_sha256());
    assert_eq!(hashes.lock_sha256.len(), 64);

    let meta = meta_json(
        "b1",
        &hashes,
        Some(0),
        &serde_json::json!({"build_millis": 1}),
    );
    for field in [
        "contract_sha256",
        "feature_sha256",
        "lock_sha256",
        "exit_code",
        "segments",
    ] {
        assert!(!meta[field].is_null(), "meta.json is missing `{field}`");
    }

    let temporary = tempfile::tempdir().unwrap();
    let mut evidence = RoundEvidence::new("b1", hashes);
    evidence.exit_code = Some(0);
    evidence.build_log = "Compiling hof_game v0.1.0\n".to_string();
    evidence.launch = serde_json::json!({"headless": true, "port": 15702});
    evidence.gate = Some(serde_json::json!({"applicable": true, "launchable": true}));
    evidence.calls.push(CallEvidence {
        seq: 1,
        tool: "world.get_components+watch".to_string(),
        layer: "generic",
        brp_methods: vec!["world.get_components+watch".to_string()],
        requests: vec![serde_json::json!({"method": "world.get_components+watch"})],
        responses: vec![serde_json::json!({"components": {}})],
        result: Some(serde_json::json!({"components": {}})),
        error: None,
        timestamp_ms: 1_791_000_000_000,
    });
    evidence.readings.push((
        "grounded".to_string(),
        serde_json::json!({"grounded": true}),
    ));
    let directory = write_round(temporary.path(), &evidence).unwrap();
    assert_eq!(directory, round_dir(temporary.path(), "b1").unwrap());
    for name in LAYOUT {
        let path = if let Some(stem) = name.strip_suffix('/') {
            directory.join(stem)
        } else {
            directory.join(name)
        };
        assert!(
            path.exists(),
            "{} is missing from the layout",
            path.display()
        );
    }
    assert!(directory
        .join("calls/0001-world.get_components+watch.json")
        .exists());
    assert!(directory.join("readings/grounded.json").exists());
}

/// DESIGN-DETAIL §8-5: the integration smoke check that **must exist** and can be
/// run when an engine is available, but never enters the default gate.
///
/// It is the only test in this batch that talks to a real engine.  Everything
/// else is driven by the in-process fake BRP server, so the default gate needs
/// neither an engine nor a network.
///
/// Run it with:
/// `cargo test --offline --test bevy_adapter_b1 -- --ignored --nocapture`
/// while a Bevy 0.19.1 app with `RemotePlugin`/`RemoteHttpPlugin` is listening on
/// 127.0.0.1:15702 (SPIKE-1 §4.1 measured `methodCount: 23`, `version: 0.19.1`).
#[test]
#[ignore = "needs a real Bevy 0.19.1 app listening on 127.0.0.1:15702 (SPIKE-1/2); never in the default gate"]
fn the_pinned_endpoint_answers_discover_with_the_23_methods_of_bevy_0191() {
    let client = BrpClient::local(Duration::from_secs(2));
    let document = client
        .discover()
        .expect("a live BRP endpoint on 127.0.0.1:15702");
    assert_eq!(document["openrpc"], serde_json::json!("1.3.2"));
    assert_eq!(document["info"]["version"], serde_json::json!("0.19.1"));
    assert_eq!(document["methodCount"], serde_json::json!(23));
    let server = document["servers"][0]["url"]
        .as_str()
        .expect("the server URL");
    assert!(
        server.contains("15702"),
        "the main-world endpoint must be 15702, got `{server}`"
    );
}
