//! The frozen reflectable contract (DESIGN-DETAIL §3).
//!
//! BRP addresses everything by **fully qualified type path including the crate
//! name** (`bevy_transform::components::transform::Transform`), so the paths a
//! game declares *are* the contract between the game and every tool that reads
//! it: a rename is a silent, total break of the observation surface.  This
//! module therefore freezes them:
//!
//! * [`CONTRACT`] is the constant list — one entry per semantic surface;
//! * [`contract_sha256`] is `sha256(canonical_json(CONTRACT))`, recorded by
//!   every round's evidence (`runs/bevy-<round>/meta.json`), so a contract
//!   change cannot pass unnoticed;
//! * [`check_registered_type_paths`] turns a missing path into an explicit
//!   `ContractViolation` (DESIGN-DETAIL §7: a *project* defect, because the PRD
//!   requires the surface to exist).
//!
//! **Crate-name freeze.** The PRD requires the paths to be frozen, and the
//! paths contain the game's crate name; the contract therefore fixes it
//! ([`GAME_CRATE`], `hof_game`) and [`check_game_crate_name`] refuses a game
//! crate that is named anything else.  Changing either is a contract change and
//! must go through the decision process (the hash in `meta.json` is what makes
//! that visible).

use serde_json::{json, Value};

use crate::adapter::AdapterError;

/// The frozen game crate name: every game-declared contract type lives under it.
pub const GAME_CRATE: &str = "hof_game";
/// The frozen module the game declares its contract types in.
pub const GAME_CONTRACT_MODULE: &str = "hof_game::contract";
/// The engine-side path of the transform component (Bevy's own, registered by Bevy).
pub const ENGINE_TRANSFORM_PATH: &str = "bevy_transform::components::transform::Transform";

/// One frozen semantic surface.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct ContractEntry {
    /// The semantic surface's name in the evidence (`readings/<surface>.json`).
    pub surface: &'static str,
    /// The fully qualified type path (crate included) BRP must be addressed with.
    pub type_path: &'static str,
    /// The reflection registration the PRD requires (`Component`/`Resource`/`Event`).
    pub reflect: &'static str,
    /// The semantic tool(s) bound to this surface, comma separated.
    pub semantic_tool: &'static str,
    /// The readable shape, with the field names the tools rely on.
    pub shape: &'static str,
}

/// DESIGN-DETAIL §3: the frozen contract.  Six surfaces, in the order of the
/// design's table; the eight semantic tools split into six bound to an entry
/// and [`TOOLS_WITHOUT_TYPE_PATH`] (frame advance and process health are not
/// reflectable state at all).
pub const CONTRACT: &[ContractEntry] = &[
    ContractEntry {
        surface: "player_marker",
        type_path: "hof_game::contract::Player",
        reflect: "Component",
        semantic_tool: "bevy_player_transform",
        shape: "zero-sized marker; locates the player entity",
    },
    ContractEntry {
        surface: "player_transform",
        type_path: ENGINE_TRANSFORM_PATH,
        reflect: "Component",
        semantic_tool: "bevy_player_transform",
        shape: "translation.x / translation.y (dot path; never array index)",
    },
    ContractEntry {
        surface: "grounded",
        type_path: "hof_game::contract::Grounded",
        reflect: "Component",
        semantic_tool: "bevy_grounded",
        shape: "bool field `on_ground`",
    },
    ContractEntry {
        surface: "coin_counter",
        type_path: "hof_game::contract::CoinCounter",
        reflect: "Resource",
        semantic_tool: "bevy_coin_counter",
        shape: "integer field `coins`",
    },
    ContractEntry {
        surface: "win_flag",
        type_path: "hof_game::contract::WinFlag",
        reflect: "Resource",
        semantic_tool: "bevy_win_flag",
        shape: "bool field `won` (one-way, never resets)",
    },
    ContractEntry {
        surface: "input_intent",
        type_path: "hof_game::contract::InputIntent",
        reflect: "Resource",
        semantic_tool: "bevy_inject_move,bevy_inject_jump",
        shape: "named fields `move_dir: i32` and `jump_pressed: bool`; level-triggered, \
                the edge is cleared by the game every frame",
    },
];

/// The eight semantic tools, frozen by name and order (DESIGN-DETAIL §2.2).
pub const SEMANTIC_TOOLS: &[&str] = &[
    "bevy_player_transform",
    "bevy_grounded",
    "bevy_coin_counter",
    "bevy_win_flag",
    "bevy_inject_move",
    "bevy_inject_jump",
    "bevy_wait_frames",
    "bevy_health",
];

/// The semantic tools that have no reflectable surface: frame advance is an
/// adapter-local action and process health is read from the process, not the ECS.
pub const TOOLS_WITHOUT_TYPE_PATH: &[&str] = &["bevy_wait_frames", "bevy_health"];

/// BRP error codes that mean "the game did not declare the thing the contract
/// requires" (SPIKE-1 §1.3's code table): they are contract violations, i.e.
/// project defects, not infrastructure failures.
pub const CONTRACT_VIOLATION_CODES: &[i64] = &[-23402, -23403, -23501, -23502];

/// The contract as JSON, one object per entry.
pub fn contract_value_of(entries: &[ContractEntry]) -> Value {
    Value::Array(
        entries
            .iter()
            .map(|entry| {
                json!({
                    "surface": entry.surface,
                    "type_path": entry.type_path,
                    "reflect": entry.reflect,
                    "semantic_tool": entry.semantic_tool,
                    "shape": entry.shape,
                })
            })
            .collect(),
    )
}

/// The live contract as JSON.
pub fn contract_value() -> Value {
    contract_value_of(CONTRACT)
}

/// `sha256(canonical_json(entries))` — the same computation for any list, so a
/// test can mutate one entry and see the hash move.
pub fn contract_sha256_of(entries: &[ContractEntry]) -> String {
    crate::runtime::policy::sha256_hex(canonical_json(&contract_value_of(entries)).as_bytes())
}

/// The frozen contract's hash, recorded in every round's evidence.
pub fn contract_sha256() -> String {
    contract_sha256_of(CONTRACT)
}

/// The pinned contract hash literal (see [`contract_sha256`]).  It is asserted
/// by the test suite, so a change to the contract cannot land silently: the test
/// fails first and the change must be re-pinned — and, per the design, go
/// through the decision process.
pub const CONTRACT_SHA256: &str =
    "4af153e77af87ceddb162c4b782701ee0b6c066a651d4e4b5d1e71f329649c69";
pub fn check_registered_type_paths(registered: &[String]) -> Result<(), AdapterError> {
    let missing: Vec<&str> = CONTRACT
        .iter()
        .map(|entry| entry.type_path)
        .filter(|path| !registered.iter().any(|seen| seen == path))
        .collect();
    if missing.is_empty() {
        return Ok(());
    }
    Err(AdapterError::ContractViolation(format!(
        "the game does not register {} required contract type path(s): {} — every path must be \
         registered with `register_type` (PRD §3-C2) before any tool can read it",
        missing.len(),
        missing.join(", ")
    )))
}

/// The `[package] name` of a `Cargo.toml`, if it declares one.
pub fn game_crate_name_of(cargo_toml: &str) -> Option<String> {
    let mut in_package = false;
    for line in cargo_toml.lines() {
        let line = line.trim();
        if line.starts_with('[') {
            in_package = line == "[package]";
            continue;
        }
        if !in_package {
            continue;
        }
        if let Some(rest) = line.strip_prefix("name") {
            let rest = rest.trim_start();
            let Some(rest) = rest.strip_prefix('=') else {
                continue;
            };
            let value = rest.trim();
            let value = value
                .strip_prefix('"')
                .and_then(|value| value.strip_suffix('"'));
            if let Some(value) = value {
                return Some(value.to_string());
            }
        }
    }
    None
}

/// The game crate must be named exactly [`GAME_CRATE`]: the frozen type paths
/// contain it, so a different name means every tool addresses a type that does
/// not exist.
pub fn check_game_crate_name(cargo_toml: &str) -> Result<(), AdapterError> {
    match game_crate_name_of(cargo_toml) {
        Some(name) if name == GAME_CRATE => Ok(()),
        Some(name) => Err(AdapterError::ContractViolation(format!(
            "the game crate is named `{name}` but the frozen contract addresses `{}::…`: the type \
             paths in `adapter/bevy/contract.rs` are the contract, so the crate must be `{}`",
            GAME_CRATE, GAME_CRATE
        ))),
        None => Err(AdapterError::ContractViolation(
            "the game's Cargo.toml declares no `[package] name`".to_string(),
        )),
    }
}

/// The canonical JSON form the hashes are taken over: no whitespace, object
/// keys sorted lexicographically at every depth, strings escaped by the JSON
/// writer.  Two documents that differ only in key order therefore hash the
/// same, and any content change moves the hash.
pub fn canonical_json(value: &Value) -> String {
    let mut out = String::new();
    write_canonical(value, &mut out);
    out
}

fn write_canonical(value: &Value, out: &mut String) {
    match value {
        Value::Null => out.push_str("null"),
        Value::Bool(flag) => out.push_str(if *flag { "true" } else { "false" }),
        Value::Number(number) => out.push_str(&number.to_string()),
        Value::String(text) => out.push_str(&Value::String(text.clone()).to_string()),
        Value::Array(items) => {
            out.push('[');
            for (index, item) in items.iter().enumerate() {
                if index > 0 {
                    out.push(',');
                }
                write_canonical(item, out);
            }
            out.push(']');
        }
        Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            out.push('{');
            for (index, key) in keys.iter().enumerate() {
                if index > 0 {
                    out.push(',');
                }
                out.push_str(&Value::String((*key).clone()).to_string());
                out.push(':');
                write_canonical(map.get(key.as_str()).unwrap_or(&Value::Null), out);
            }
            out.push('}');
        }
    }
}

/// A `Map` built in reverse key order, used by the tests to prove that the hash
/// does not depend on insertion order.
#[cfg(test)]
fn reversed_object(pairs: &[(&str, Value)]) -> Value {
    let mut map = serde_json::Map::new();
    for (key, value) in pairs.iter().rev() {
        map.insert((*key).to_string(), value.clone());
    }
    Value::Object(map)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_json_is_whitespace_free_and_key_sorted() {
        let value = serde_json::from_str(r#"{"b":1,"a":{"d":true,"c":[1,"x"]}}"#).unwrap();
        assert_eq!(
            canonical_json(&value),
            r#"{"a":{"c":[1,"x"],"d":true},"b":1}"#
        );
    }

    #[test]
    fn canonical_json_is_stable_under_key_reordering() {
        let ordered = serde_json::from_str(r#"{"a":1,"b":2,"c":{"x":1,"y":2}}"#).unwrap();
        let reversed = reversed_object(&[
            ("c", reversed_object(&[("y", json!(2)), ("x", json!(1))])),
            ("b", json!(2)),
            ("a", json!(1)),
        ]);
        assert_eq!(canonical_json(&ordered), canonical_json(&reversed));
        assert_eq!(
            canonical_json(&ordered),
            r#"{"a":1,"b":2,"c":{"x":1,"y":2}}"#
        );
    }

    #[test]
    fn canonical_json_escapes_strings_like_json_does() {
        let value = json!({"quote": "a\"b", "newline": "a\nb"});
        assert_eq!(
            canonical_json(&value),
            "{\"newline\":\"a\\nb\",\"quote\":\"a\\\"b\"}"
        );
    }

    #[test]
    fn the_contract_hash_is_the_pinned_literal() {
        // The pin is the point: a contract change fails here first.
        assert_eq!(contract_sha256(), CONTRACT_SHA256);
    }

    #[test]
    fn the_contract_hash_changes_when_any_entry_changes() {
        let baseline = contract_sha256_of(CONTRACT);
        let mut entries = CONTRACT.to_vec();
        entries[2].type_path = "hof_game::contract::NotGrounded";
        assert_ne!(baseline, contract_sha256_of(&entries));
        let mut shape = CONTRACT.to_vec();
        shape[3].shape = "integer field `count`";
        assert_ne!(baseline, contract_sha256_of(&shape));
    }

    #[test]
    fn the_contract_is_six_surfaces_and_the_semantic_tools_are_fully_accounted_for() {
        assert_eq!(CONTRACT.len(), 6);
        let mut bound: Vec<&str> = CONTRACT
            .iter()
            .flat_map(|entry| entry.semantic_tool.split(','))
            .collect();
        bound.extend_from_slice(TOOLS_WITHOUT_TYPE_PATH);
        bound.sort();
        bound.dedup();
        let mut all = SEMANTIC_TOOLS.to_vec();
        all.sort();
        assert_eq!(
            bound, all,
            "every semantic tool is bound or explicitly path-free"
        );
    }

    #[test]
    fn every_game_declared_path_is_under_the_frozen_crate_and_module() {
        for entry in CONTRACT {
            if entry.type_path == ENGINE_TRANSFORM_PATH {
                continue;
            }
            assert!(
                entry
                    .type_path
                    .starts_with(&format!("{GAME_CONTRACT_MODULE}::")),
                "{} is not under the frozen module",
                entry.type_path
            );
        }
    }

    #[test]
    fn a_missing_type_path_is_a_contract_violation() {
        let all: Vec<String> = CONTRACT.iter().map(|e| e.type_path.to_string()).collect();
        assert!(check_registered_type_paths(&all).is_ok());
        let without_grounded: Vec<String> = all
            .iter()
            .filter(|path| path.as_str() != "hof_game::contract::Grounded")
            .cloned()
            .collect();
        let error = check_registered_type_paths(&without_grounded).unwrap_err();
        match error {
            AdapterError::ContractViolation(message) => {
                assert!(
                    message.contains("hof_game::contract::Grounded"),
                    "{message}"
                );
            }
            other => panic!("expected a contract violation, got {other:?}"),
        }
    }

    #[test]
    fn the_game_crate_name_is_part_of_the_contract() {
        assert!(check_game_crate_name("[package]\nname = \"hof_game\"\n").is_ok());
        assert!(check_game_crate_name("[package]\nname = \"my_game\"\n").is_err());
        assert!(check_game_crate_name("[dependencies]\nname = \"hof_game\"\n").is_err());
        assert_eq!(
            game_crate_name_of("[package]\nname=\"hof_game\"\nversion = \"0.1.0\"\n").as_deref(),
            Some("hof_game")
        );
    }

    #[test]
    fn brp_contract_violation_codes_are_pinned() {
        assert_eq!(CONTRACT_VIOLATION_CODES, &[-23402, -23403, -23501, -23502]);
    }
}
