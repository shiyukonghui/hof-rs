//! BATCH-B1 cross-module pins: the frozen contract, the frozen tool list, the
//! legacy adapter's alignment, and the round-evidence layout.
//!
//! These are integration-level because they are the properties that hold the
//! *system* together: the contract hash, the tool-list hash and the eight
//! semantic names must not drift silently, and the Godot path must keep
//! compiling and answering honestly through the new trait.

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
use hof_rs::adapter::GodotAdapter;
use hof_rs::adapter::{AdapterError, EngineId, GameAdapter, Intent, Project, SemanticKind};
use hof_rs::config::GodotConfig;

fn godot_adapter() -> GodotAdapter {
    GodotAdapter::new(
        GodotConfig {
            editor_binary: PathBuf::new(),
            cache_excludes: Vec::new(),
            main_scene: "res://scenes/main.tscn".to_string(),
        },
        false,
    )
}

#[test]
fn the_frozen_contract_hash_and_crate_name_are_pinned() {
    assert_eq!(contract_sha256(), CONTRACT_SHA256, "the contract drifted");
    assert_eq!(CONTRACT_SHA256.len(), 64);
    assert_eq!(CONTRACT.len(), 6);
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
fn the_legacy_godot_adapter_implements_the_capability_surface_without_panicking() {
    let mut adapter = godot_adapter();
    assert_eq!(adapter.engine(), EngineId::Godot48Legacy);
    assert_eq!(adapter.engine().as_str(), "godot-4.8-legacy");

    let project = Project::at(PathBuf::from("."));

    // Task-level failures, typed rather than strings.
    for (what, result) in [
        ("prepare", adapter.prepare(&project).err()),
        ("wait_frames", adapter.wait_frames(5).err()),
        ("health", adapter.health().err()),
    ] {
        match result {
            Some(error) => match error.downcast_ref::<AdapterError>() {
                Some(AdapterError::Unsupported { capability, .. }) => assert_eq!(*capability, what),
                other => panic!("`{what}` should be Unsupported, got {other:?}"),
            },
            None => panic!("`{what}` must be a task-level failure on the Godot surface"),
        }
    }

    // Evidence-level failures: the adapter answers, and the answer is "not
    // observed" / "refused" — which is what lets the battery record a gap.
    for kind in SemanticKind::ALL {
        let reading = adapter.read(*kind).expect("read answers");
        assert!(reading.failed, "the Godot path cannot observe {kind:?}");
        assert!(reading.reason.is_some());
        assert_eq!(reading.value, serde_json::Value::Null);
    }
    let injection = adapter
        .inject(&Intent::Move { dir: 1 }, true)
        .expect("inject answers");
    assert!(!injection.accepted);
    assert!(injection.reason.is_some());

    // And the one real capability: the existing artifact verdict.
    let temporary = tempfile::tempdir().unwrap();
    let verdict = adapter
        .validate_artifact(&Project::at(temporary.path()))
        .unwrap();
    assert!(verdict.applicable);
    assert!(!verdict.launchable, "an empty workspace is not launchable");
    assert!(!verdict.reasons.is_empty(), "a verdict carries its reasons");

    // Object safe, so a future engine can be selected at runtime.
    let mut boxed: Box<dyn GameAdapter> = Box::new(godot_adapter());
    assert_eq!(boxed.engine(), EngineId::Godot48Legacy);
    let _ = boxed.wait_frames(1);
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
