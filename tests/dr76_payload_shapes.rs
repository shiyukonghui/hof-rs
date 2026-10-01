//! DR-76 ①/④ — the interaction fixtures are the engine's own bytes, and the
//! numbers the reports cite are computed from them.
//!
//! The DR-73 acceptance's A1/O1 was a **fixture** defect: `node_tree_payload`
//! hand-wrote a `text` member onto the HUD `Label` nodes of
//! `running_game_get_scene_tree`.  The real engine never sends one — every one of
//! the 10 frozen scene-tree payloads from five rounds gives a `Label` exactly
//! `name`, `path` and `type` — so the green test was green against a shape that
//! cannot occur, and the window it exercised answered `COIN_COUNTER_UNREADABLE`
//! on real hardware no matter what the game did.
//!
//! These assertions are about the **frozen bytes**, so the shape can never drift
//! back: the fixtures under `tests/fixtures/dr76/` are copies (or reductions)
//! produced by `scripts/derive_dr76_fixtures.py` from `runs/smoke-t10/**`, and
//! their sha256 values are pinned in that directory's `MANIFEST.json`.
//!
//! A4 is the same discipline for a number: the whole-round maximum player x the
//! reports cited was `448.666`; the frozen samples' maximum is
//! `455.999572753906` (the jump window's constant x, which the engine's own
//! assertion payload confirms as `actual.x`).  The number is computed here from
//! the frozen series rather than restated.

use std::fmt::Write as _;
use std::path::PathBuf;

use hof_rs::adapter::godot::hud_label_candidates;
use serde_json::Value;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn fixture_raw(name: &str) -> String {
    let path = repo_root().join("tests/fixtures/dr76").join(name);
    std::fs::read_to_string(&path).unwrap_or_else(|error| panic!("{path:?}: {error}"))
}

fn sha256_hex(bytes: &[u8]) -> String {
    use sha2::{Digest, Sha256};
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    hasher
        .finalize()
        .iter()
        .fold(String::new(), |mut out, byte| {
            let _ = write!(out, "{byte:02x}");
            out
        })
}

/// The MCP `tools/call` envelope wraps the payload in `content[0].text`.
fn text_of(payload: &Value) -> String {
    payload["content"][0]["text"]
        .as_str()
        .unwrap_or_else(|| panic!("no text content in {payload}"))
        .to_string()
}

/// Every embedded `{"tree": …}` envelope inside a frozen `scene_tree.json` record
/// — the exact value `hud_label_candidates` is written against.
fn frozen_trees() -> Vec<Value> {
    let raw: Value = serde_json::from_str(&fixture_raw("scene_tree_smoke_t10.json"))
        .expect("the frozen scene tree is JSON");
    raw["calls"]
        .as_array()
        .expect("the frozen record has calls")
        .iter()
        .filter(|call| call["tool"] == serde_json::json!("running_game_get_scene_tree"))
        .map(|call| {
            serde_json::from_str::<Value>(&text_of(&call["payload"]))
                .expect("the inner payload is JSON")
        })
        .filter(|inner| inner.get("tree").is_some())
        .collect()
}

fn walk_labels(node: &Value, out: &mut Vec<(Vec<String>, String)>) {
    if node.get("type").and_then(Value::as_str) == Some("Label") {
        let mut keys: Vec<String> = node
            .as_object()
            .expect("a node is an object")
            .keys()
            .cloned()
            .collect();
        keys.sort();
        out.push((keys, node["path"].as_str().unwrap_or("").to_string()));
    }
    if let Some(children) = node.get("children").and_then(Value::as_array) {
        for child in children {
            walk_labels(child, out);
        }
    }
}

/// DR-76 ①: the engine's scene-tree shape, asserted on the frozen payload.
///
/// This is the executable form of the A1 finding: a HUD `Label` carries exactly
/// `name`, `path`, `type` — **zero** `text` keys — and the counter cell really is
/// `/root/Main/HUD/Coins`.  The window is corrected against this, not against a
/// hand-written idea of it.
#[test]
fn every_frozen_scene_tree_label_carries_exactly_the_three_keys_the_engine_sends() {
    let trees = frozen_trees();
    assert_eq!(trees.len(), 1, "the frozen record carries one scene tree");

    let mut labels = Vec::new();
    walk_labels(&trees[0]["tree"], &mut labels);
    assert!(
        !labels.is_empty(),
        "the frozen tree must really carry HUD labels, or this test proves nothing"
    );
    for (keys, path) in &labels {
        assert_eq!(
            keys,
            &["name".to_string(), "path".to_string(), "type".to_string()],
            "`{path}`: the real engine sends exactly name/path/type on a Label — a `text` member \
             is the DR-73 fixture's invention, and a window that depends on it can never work on \
             real hardware"
        );
    }
    assert!(
        labels
            .iter()
            .any(|(_, path)| path == "/root/Main/HUD/Coins"),
        "the frozen round really had a `Coins` cell, so the counter is findable by path: {labels:?}"
    );
}

/// DR-76 ①: the corrected lookup finds the counter on that frozen shape.
///
/// `hud_label_candidates` takes only `name`/`path`/`type` from the tree; the text
/// is read through `running_game_get_node_properties` by the window.  A tree that
/// carried a `text` member would not change the answer — which is exactly the
/// property the DR-73 implementation lacked.
#[test]
fn the_counter_is_found_from_the_frozen_tree_without_any_text_member() {
    let trees = frozen_trees();
    let candidates = hud_label_candidates(&trees[0]);
    assert!(
        candidates.contains(&"/root/Main/HUD/Coins".to_string()),
        "the counter must be among the candidates of the frozen tree: {candidates:?}"
    );
    assert!(
        !trees[0].to_string().contains("\"text\""),
        "the frozen tree carries no text member at all"
    );
}

/// DR-76 ①: the engine's `running_game_get_node_properties` reading shape for a
/// HUD `Label`, from the frozen `hud-labels.json` — `node_path`, `properties.text`
/// and `properties.visible`, with `type: Label`.  The property reader is a real
/// path to the counter; the scene tree is not.
#[test]
fn the_frozen_hud_label_read_shows_the_property_reader_is_a_real_path() {
    let raw: Value =
        serde_json::from_str(&fixture_raw("hud_labels_smoke_t10.json")).expect("frozen reads");
    let readings = raw["readings"].as_array().expect("readings");
    let keys: Vec<&str> = readings
        .iter()
        .map(|reading| reading["properties"]["text"].as_str().unwrap_or(""))
        .collect();
    assert!(
        keys.iter().any(|text| text.starts_with("Coins:")),
        "the frozen round's own property read answered the counter text: {keys:?}"
    );
    let coins = readings
        .iter()
        .find(|reading| reading["node_path"] == serde_json::json!("/root/Main/HUD/Coins"))
        .expect("the frozen readings carry the Coins cell");
    assert_eq!(coins["type"], serde_json::json!("Label"));
    assert_eq!(coins["properties"]["visible"], serde_json::json!(true));
}

/// DR-76 ④: the whole-round maximum player x, **computed** from the frozen
/// per-frame samples instead of restated.
///
/// The DR-73 report and the T10 acceptance both cited `448.666`; the frozen
/// samples' maximum is `455.999572753906`, the jump window's constant x.  The
/// error did not change any conclusion, but the number was wrong and the fix is
/// that the number is derived from the frozen bytes.  A plant that edits the
/// expectation — or a fixture regenerated with different bytes — reddens this.
#[test]
fn the_frozen_rounds_maximum_player_x_is_derived_from_the_samples() {
    let raw: Value =
        serde_json::from_str(&fixture_raw("interaction_position_samples_smoke_t10.json"))
            .expect("the derived sample file");
    let windows = raw["windows"].as_array().expect("windows");
    assert_eq!(
        windows.len(),
        4,
        "the frozen replay has the four position windows"
    );
    let frame_counts: Vec<u64> = windows
        .iter()
        .map(|window| window["frame_count"].as_u64().expect("frame_count"))
        .collect();
    assert_eq!(frame_counts, vec![60, 10, 30, 60]);

    let mut max_x: Option<f64> = None;
    for window in windows {
        for x in window["xs"].as_array().expect("xs") {
            let x = x.as_f64().expect("a float");
            max_x = Some(max_x.map_or(x, |current: f64| current.max(x)));
        }
    }
    let max_x = max_x.expect("the frozen samples carry numbers");
    assert_eq!(
        max_x, 455.999_572_753_906,
        "the whole-round maximum player x, as the frozen samples carry it (the jump window's \
         constant x).  Any citation must use this value, not the 448.666 the DR-73 report and the \
         T10 acceptance printed"
    );
    assert_ne!(
        max_x, 448.666,
        "the 7.33 px understatement the acceptance's A4 found must not come back"
    );
    // The goal's own geometry is in the same derived file, so a reader can see
    // that the win trigger is far to the right of the observed maximum.
    assert!(
        raw["goal_geometry"]["Goal"]["path"] == serde_json::json!("/root/Main/Goal"),
        "the derived file must carry the frozen goal node: {}",
        raw["goal_geometry"]
    );
}

/// DR-76 ①/④: the fixtures are what the derivation produced.
///
/// `MANIFEST.json` pins each copy's sha256 against the frozen source; this test
/// recomputes them from the files on disk, so a fixture edited by hand (for
/// example to put the DR-73 `text` member back) is red instead of silently
/// driving the suite.
#[test]
fn the_derived_fixtures_match_the_sha256_the_manifest_pins() {
    let manifest: Value =
        serde_json::from_str(&fixture_raw("MANIFEST.json")).expect("the manifest is JSON");
    assert_eq!(
        manifest["derivation"],
        serde_json::json!("python scripts/derive_dr76_fixtures.py")
    );
    let files = manifest["files"].as_array().expect("files");
    assert!(files.len() >= 3, "the manifest must pin every fixture");
    for entry in files {
        let name = entry["fixture"].as_str().expect("a fixture name");
        let path = repo_root().join("tests/fixtures/dr76").join(name);
        let bytes = std::fs::read(&path).unwrap_or_else(|error| panic!("{path:?}: {error}"));
        assert_eq!(
            sha256_hex(&bytes),
            entry["sha256"].as_str().expect("a pinned digest"),
            "{name} no longer matches the derivation; regenerate with `python \
             scripts/derive_dr76_fixtures.py` instead of editing it"
        );
    }
}
