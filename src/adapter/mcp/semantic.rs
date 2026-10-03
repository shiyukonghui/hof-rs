//! Layer 2: the eight semantic tools, bound to the **frozen contract**
//! (DESIGN-DETAIL §2.2, §3).
//!
//! This is the layer the deterministic battery uses, and it is deliberately
//! small.  Each read maps onto exactly **one** BRP call (never a batch —
//! SPIKE-2 C4 measured that a batch is not frame-atomic: one batch of 24
//! identical `world.get_resources` calls came back with both `coins:1` and
//! `coins:2`), and each injection maps onto exactly one field write of the
//! contract's `InputIntent` resource.
//!
//! Two properties are worth stating because they are what makes the layer
//! honest:
//!
//! * **Type paths come from [`crate::adapter::bevy::contract`], never from a
//!   literal here.**  A path change is a contract change, with the hash to make
//!   it visible.
//! * **A missing path is a contract violation, not a zero.**  BRP reports an
//!   unregistered type with `-23402/-23502`, and an empty query result means the
//!   player does not exist: both become [`AdapterError::ContractViolation`], so
//!   the battery cannot "observe" 0 coins on a game that never registered a
//!   counter (SPIKE-1 §6.3: an unregistered observable must fail explicitly,
//!   never be silently treated as a value).

use serde_json::{json, Value};

use crate::adapter::bevy::brp::BrpError;
use crate::adapter::bevy::contract::{
    self, ContractEntry, CONTRACT, ENGINE_TRANSFORM_PATH, GAME_CONTRACT_MODULE,
};
use crate::adapter::mcp::{Layer, ParamSpec, ParamType, ToolSpec};
use crate::adapter::AdapterError;

/// The contract's transform path (the engine's own component).
pub const TRANSFORM_PATH: &str = ENGINE_TRANSFORM_PATH;
/// The contract's player marker path.
pub const PLAYER_PATH: &str = "hof_game::contract::Player";
/// The contract's grounded component path.
pub const GROUNDED_PATH: &str = "hof_game::contract::Grounded";
/// The contract's coin-counter resource path.
pub const COIN_COUNTER_PATH: &str = "hof_game::contract::CoinCounter";
/// The contract's win-flag resource path.
pub const WIN_FLAG_PATH: &str = "hof_game::contract::WinFlag";
/// The contract's input-intent resource path.
pub const INPUT_INTENT_PATH: &str = "hof_game::contract::InputIntent";

/// The eight semantic tools, in the frozen order of the contract module.
pub const SEMANTIC_TOOL_SPECS: &[ToolSpec] = &[
    ToolSpec {
        name: "bevy_player_transform",
        description: "The player entity's `translation.x`/`.y`, read through the frozen player \
                      marker and the engine's `Transform`.",
        params: &[],
        layer: Layer::Semantic,
        method: None,
        streaming: false,
        mutating: false,
    },
    ToolSpec {
        name: "bevy_grounded",
        description: "The player's ground state: `Grounded.on_ground` off the frozen contract. \
                      This is the semantic basis for a jump, not a y-coordinate guess.",
        params: &[],
        layer: Layer::Semantic,
        method: None,
        streaming: false,
        mutating: false,
    },
    ToolSpec {
        name: "bevy_coin_counter",
        description: "The `CoinCounter.coins` resource: the count the game increments on pickup.",
        params: &[],
        layer: Layer::Semantic,
        method: None,
        streaming: false,
        mutating: false,
    },
    ToolSpec {
        name: "bevy_win_flag",
        description: "The `WinFlag.won` resource: one-way, false until the goal is reached.",
        params: &[],
        layer: Layer::Semantic,
        method: None,
        streaming: false,
        mutating: false,
    },
    ToolSpec {
        name: "bevy_inject_move",
        description: "Writes the movement intent (`InputIntent.move_dir`, level-triggered). The \
                      game clears the edge itself.",
        params: &[
            ParamSpec {
                name: "dir",
                ty: ParamType::IntEnum(&[-1, 0, 1]),
                required: true,
                description: "-1 left, 0 stop, 1 right",
            },
            ParamSpec {
                name: "level",
                ty: ParamType::ConstBool(true),
                required: true,
                description: "level-triggered: the value stays until it is overwritten",
            },
        ],
        layer: Layer::Semantic,
        method: None,
        streaming: false,
        mutating: true,
    },
    ToolSpec {
        name: "bevy_inject_jump",
        description: "Writes the jump intent (`InputIntent.jump_pressed`); the game clears the \
                      edge every frame.",
        params: &[ParamSpec {
            name: "press",
            ty: ParamType::Bool,
            required: true,
            description: "true presses, false releases",
        }],
        layer: Layer::Semantic,
        method: None,
        streaming: false,
        mutating: true,
    },
    ToolSpec {
        name: "bevy_wait_frames",
        description: "Advances the observation point by `n` game frames before the next read, so \
                      a read never lands in the middle of a transition.",
        params: &[ParamSpec {
            name: "n",
            ty: ParamType::Integer,
            required: true,
            description: "how many game frames to wait for",
        }],
        layer: Layer::Semantic,
        method: None,
        streaming: false,
        mutating: false,
    },
    ToolSpec {
        name: "bevy_health",
        description: "The game process: alive, plus the tail of its stderr. BRP has no log verb, \
                      so a panic is only visible here.",
        params: &[],
        layer: Layer::Semantic,
        method: None,
        streaming: false,
        mutating: false,
    },
];

/// The semantic layer, as tool specs.
pub fn semantic_tools() -> Vec<ToolSpec> {
    SEMANTIC_TOOL_SPECS.to_vec()
}

/// The semantic tool names, in the frozen order.
pub fn semantic_tool_names() -> Vec<&'static str> {
    SEMANTIC_TOOL_SPECS.iter().map(|tool| tool.name).collect()
}

/// The contract entry a semantic tool is bound to, if any.
pub fn contract_entry_for(tool: &str) -> Option<&'static ContractEntry> {
    CONTRACT
        .iter()
        .find(|entry| entry.semantic_tool.split(',').any(|bound| bound == tool))
}

/// One BRP request of a semantic call.  A plan is a **sequence** of single
/// calls; there is no batch representation here either.
#[derive(Clone, Debug, PartialEq)]
pub struct BrpStep {
    pub method: &'static str,
    pub params: Value,
}

impl BrpStep {
    fn new(method: &'static str, params: Value) -> Self {
        Self { method, params }
    }
}

/// Query one component of the player entity.  `strict` is on: a component path
/// the game never registered must fail loudly (`-23402`), not be skipped.
fn player_query(component: &str) -> BrpStep {
    BrpStep::new(
        "world.query",
        json!({
            "data": {"components": [component], "option": "all"},
            "filter": {"with": [PLAYER_PATH]},
            "strict": true,
        }),
    )
}

/// The BRP calls one semantic tool issues, in order (DESIGN-DETAIL §4: read is
/// per-call, `wait_frames`/`health` need no call at all).
pub fn plan(tool: &str, args: &Value) -> Result<Vec<BrpStep>, AdapterError> {
    match tool {
        "bevy_player_transform" => Ok(vec![player_query(TRANSFORM_PATH)]),
        "bevy_grounded" => Ok(vec![player_query(GROUNDED_PATH)]),
        "bevy_coin_counter" => Ok(vec![BrpStep::new(
            "world.get_resources",
            json!({"resource": COIN_COUNTER_PATH}),
        )]),
        "bevy_win_flag" => Ok(vec![BrpStep::new(
            "world.get_resources",
            json!({"resource": WIN_FLAG_PATH}),
        )]),
        "bevy_inject_move" => {
            let dir = args.get("dir").and_then(Value::as_i64).ok_or_else(|| {
                AdapterError::Malformed("`dir` is required and must be an integer".to_string())
            })?;
            if !(-1..=1).contains(&dir) {
                return Err(AdapterError::Malformed(format!(
                    "`dir` must be -1, 0 or 1 (got {dir})"
                )));
            }
            Ok(vec![BrpStep::new(
                "world.mutate_resources",
                json!({"resource": INPUT_INTENT_PATH, "path": "move_dir", "value": dir}),
            )])
        }
        "bevy_inject_jump" => {
            let press = args.get("press").and_then(Value::as_bool).ok_or_else(|| {
                AdapterError::Malformed("`press` is required and must be a boolean".to_string())
            })?;
            Ok(vec![BrpStep::new(
                "world.mutate_resources",
                json!({"resource": INPUT_INTENT_PATH, "path": "jump_pressed", "value": press}),
            )])
        }
        // Frame advance is an adapter-local action (SPIKE-1 §6.3: it is not a BRP
        // verb), and process health comes from the process, not the ECS.
        "bevy_wait_frames" | "bevy_health" => Ok(Vec::new()),
        other => Err(AdapterError::Malformed(format!(
            "`{other}` is not a semantic tool"
        ))),
    }
}

/// The tools whose answer needs no BRP call.
pub fn is_plan_free(tool: &str) -> bool {
    matches!(tool, "bevy_wait_frames" | "bevy_health")
}

/// Turn the responses of [`plan`] into the tool's frozen return shape.
///
/// `frame` is the adapter's monotone observation ordinal (BRP has no frame verb
/// and Bevy's `Time` is not reflectable — SPIKE-1 §0.4-3 — so the contract's
/// frame field is the *adapter's* observation counter; see the batch report).
pub fn project(tool: &str, responses: &[Value], frame: u64) -> Result<Value, AdapterError> {
    match tool {
        "bevy_player_transform" => {
            let row = first_row(responses, tool)?;
            let transform = component_of(row, TRANSFORM_PATH, tool)?;
            let translation = transform.get("translation").and_then(Value::as_array);
            let Some(translation) = translation else {
                return Err(AdapterError::Malformed(format!(
                    "`{tool}`: `{TRANSFORM_PATH}.translation` is not an array"
                )));
            };
            let x = number_at(translation, 0, tool, "translation.x")?;
            let y = number_at(translation, 1, tool, "translation.y")?;
            Ok(json!({"x": x, "y": y, "frame": frame}))
        }
        "bevy_grounded" => {
            let row = first_row(responses, tool)?;
            let grounded = component_of(row, GROUNDED_PATH, tool)?;
            let on_ground = grounded.get("on_ground").and_then(Value::as_bool);
            let Some(on_ground) = on_ground else {
                return Err(AdapterError::Malformed(format!(
                    "`{tool}`: `{GROUNDED_PATH}.on_ground` is not a boolean"
                )));
            };
            Ok(json!({"grounded": on_ground, "frame": frame}))
        }
        "bevy_coin_counter" => {
            let value = resource_value(responses, tool)?;
            let coins = value.get("coins").and_then(Value::as_i64);
            let Some(coins) = coins else {
                return Err(AdapterError::Malformed(format!(
                    "`{tool}`: `{COIN_COUNTER_PATH}.coins` is not an integer"
                )));
            };
            Ok(json!({"coins": coins, "frame": frame}))
        }
        "bevy_win_flag" => {
            let value = resource_value(responses, tool)?;
            let won = value.get("won").and_then(Value::as_bool);
            let Some(won) = won else {
                return Err(AdapterError::Malformed(format!(
                    "`{tool}`: `{WIN_FLAG_PATH}.won` is not a boolean"
                )));
            };
            Ok(json!({"won": won, "frame": frame}))
        }
        "bevy_inject_move" | "bevy_inject_jump" => Ok(json!({"accepted": true})),
        other => Err(AdapterError::Malformed(format!(
            "`{other}` has no projection"
        ))),
    }
}

/// The read tool that reports one [`crate::adapter::SemanticKind`], if any.
pub fn semantic_tool_of_kind(kind: crate::adapter::SemanticKind) -> &'static str {
    kind.tool()
}

fn first_row<'a>(responses: &'a [Value], tool: &str) -> Result<&'a Value, AdapterError> {
    let response = responses.first().ok_or_else(|| {
        AdapterError::Malformed(format!("`{tool}`: no BRP response was recorded"))
    })?;
    // A `world.query` result is a bare array (SPIKE-1 §4.1).
    let rows = response.as_array().ok_or_else(|| {
        AdapterError::Malformed(format!(
            "`{tool}`: the query result is not an array (got {response})"
        ))
    })?;
    rows.first().ok_or_else(|| {
        AdapterError::ContractViolation(format!(
            "`{tool}`: no entity carries the frozen player marker `{PLAYER_PATH}` — the game must \
             register and spawn it (PRD §3-C2)"
        ))
    })
}

fn component_of<'a>(row: &'a Value, path: &str, tool: &str) -> Result<&'a Value, AdapterError> {
    if let Some(errors) = row.get("errors").and_then(Value::as_object) {
        if !errors.is_empty() {
            return Err(AdapterError::ContractViolation(format!(
                "`{tool}`: BRP reported {} error(s) for the frozen paths: {}",
                errors.len(),
                Value::Object(errors.clone())
            )));
        }
    }
    row.get("components")
        .and_then(|components| components.get(path))
        .ok_or_else(|| {
            AdapterError::ContractViolation(format!(
                "`{tool}`: the player entity does not carry `{path}` — it is part of the frozen \
                 contract and must be registered with `register_type` (PRD §3-C2)"
            ))
        })
}

fn resource_value<'a>(responses: &'a [Value], tool: &str) -> Result<&'a Value, AdapterError> {
    let response = responses.first().ok_or_else(|| {
        AdapterError::Malformed(format!("`{tool}`: no BRP response was recorded"))
    })?;
    response.get("value").ok_or_else(|| {
        AdapterError::Malformed(format!(
            "`{tool}`: the resource reply has no `value` field (got {response})"
        ))
    })
}

fn number_at(values: &[Value], index: usize, tool: &str, field: &str) -> Result<f64, AdapterError> {
    values
        .get(index)
        .and_then(Value::as_f64)
        .ok_or_else(|| AdapterError::Malformed(format!("`{tool}`: `{field}` is not a number")))
}

/// A BRP error classified for the semantic layer: an unregistered type is a
/// **contract violation** (a project defect per DESIGN-DETAIL §7), while a
/// method-name error is an adapter bug and everything else stays a BRP failure.
pub fn classify_brp_error(error: &BrpError) -> AdapterError {
    match error {
        BrpError::Rpc { code, message } if contract::CONTRACT_VIOLATION_CODES.contains(code) => {
            AdapterError::ContractViolation(format!(
                "the game does not expose a frozen contract type (BRP {code}: {message}); the \
                 contract paths live in `adapter/bevy/contract.rs`"
            ))
        }
        BrpError::Rpc { code, message } => AdapterError::Rpc {
            code: *code,
            message: message.clone(),
        },
        BrpError::Transport { endpoint, message } => AdapterError::Transport {
            endpoint: endpoint.clone(),
            message: message.clone(),
        },
        BrpError::Timeout { endpoint, millis } => AdapterError::Transport {
            endpoint: endpoint.clone(),
            message: format!("timed out after {millis} ms"),
        },
        BrpError::EndpointTimeout {
            endpoint,
            budget_millis,
        } => AdapterError::EndpointTimeout {
            endpoint: endpoint.clone(),
            budget_millis: *budget_millis,
        },
        BrpError::Malformed { endpoint, message } => {
            AdapterError::Malformed(format!("{endpoint}: {message}"))
        }
        BrpError::HttpStatus {
            endpoint,
            status,
            body,
        } => AdapterError::Malformed(format!("HTTP {status} from {endpoint}: {body}")),
        BrpError::InvalidRequest(message) => AdapterError::Malformed(message.clone()),
    }
}

/// The frozen module prefix, re-exported so callers assert against one constant.
pub const CONTRACT_MODULE: &str = GAME_CONTRACT_MODULE;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_eight_semantic_tools_are_the_frozen_names_in_order() {
        assert_eq!(semantic_tool_names(), contract::SEMANTIC_TOOLS.to_vec());
        for tool in SEMANTIC_TOOL_SPECS {
            assert_eq!(tool.layer, Layer::Semantic);
            assert_eq!(tool.method, None, "semantic tools plan their calls");
        }
    }

    #[test]
    fn every_semantic_tool_is_bound_to_a_contract_entry_or_explicitly_path_free() {
        for tool in semantic_tool_names() {
            let bound = contract_entry_for(tool).is_some();
            let path_free = contract::TOOLS_WITHOUT_TYPE_PATH.contains(&tool);
            assert!(
                bound ^ path_free,
                "`{tool}` must be either contract-bound or declared path-free (bound={bound}, \
                 path_free={path_free})"
            );
        }
        assert!(contract_entry_for("bevy_grounded").is_some());
        assert!(contract_entry_for("bevy_wait_frames").is_none());
        assert!(
            contract_entry_for("entity_query").is_none(),
            "no Godot name here"
        );
    }

    #[test]
    fn the_type_paths_used_by_the_layer_are_the_contracts_paths() {
        // `bevy_player_transform` is bound to two surfaces: the marker that
        // locates the player and the engine `Transform` that carries the
        // coordinates.  Both must come from the contract.
        let bound: Vec<&str> = contract::CONTRACT
            .iter()
            .filter(|entry| {
                entry
                    .semantic_tool
                    .split(',')
                    .any(|t| t == "bevy_player_transform")
            })
            .map(|entry| entry.type_path)
            .collect();
        assert_eq!(bound, vec![PLAYER_PATH, TRANSFORM_PATH]);
        assert_eq!(
            contract_entry_for("bevy_grounded").unwrap().type_path,
            GROUNDED_PATH
        );
        assert_eq!(
            contract_entry_for("bevy_coin_counter").unwrap().type_path,
            COIN_COUNTER_PATH
        );
        assert_eq!(
            contract_entry_for("bevy_win_flag").unwrap().type_path,
            WIN_FLAG_PATH
        );
        assert_eq!(
            contract_entry_for("bevy_inject_move").unwrap().type_path,
            INPUT_INTENT_PATH
        );
        assert_eq!(
            contract_entry_for("bevy_inject_jump").unwrap().type_path,
            INPUT_INTENT_PATH
        );
        for path in [
            PLAYER_PATH,
            GROUNDED_PATH,
            COIN_COUNTER_PATH,
            WIN_FLAG_PATH,
            INPUT_INTENT_PATH,
        ] {
            assert!(path.starts_with(&format!("{CONTRACT_MODULE}::")), "{path}");
        }
    }

    #[test]
    fn each_read_is_one_call_and_never_a_batch() {
        for tool in [
            "bevy_player_transform",
            "bevy_grounded",
            "bevy_coin_counter",
            "bevy_win_flag",
        ] {
            let steps = plan(tool, &json!({})).unwrap();
            assert_eq!(steps.len(), 1, "`{tool}` must be exactly one BRP call");
        }
    }

    #[test]
    fn a_player_read_filters_on_the_frozen_marker_and_is_strict() {
        let steps = plan("bevy_player_transform", &json!({})).unwrap();
        assert_eq!(steps[0].method, "world.query");
        assert_eq!(steps[0].params["filter"]["with"], json!([PLAYER_PATH]));
        assert_eq!(
            steps[0].params["data"]["components"],
            json!([TRANSFORM_PATH])
        );
        assert_eq!(steps[0].params["strict"], json!(true));
    }

    #[test]
    fn the_injection_tools_write_named_fields_of_the_intent_resource() {
        let move_steps = plan("bevy_inject_move", &json!({"dir": -1, "level": true})).unwrap();
        assert_eq!(move_steps.len(), 1);
        assert_eq!(move_steps[0].method, "world.mutate_resources");
        assert_eq!(move_steps[0].params["resource"], json!(INPUT_INTENT_PATH));
        assert_eq!(move_steps[0].params["path"], json!("move_dir"));
        assert_eq!(move_steps[0].params["value"], json!(-1));

        let jump_steps = plan("bevy_inject_jump", &json!({"press": true})).unwrap();
        assert_eq!(jump_steps[0].params["path"], json!("jump_pressed"));
        assert_eq!(jump_steps[0].params["value"], json!(true));
    }

    #[test]
    fn an_out_of_range_direction_is_refused() {
        assert!(plan("bevy_inject_move", &json!({"dir": 2})).is_err());
        assert!(plan("bevy_inject_move", &json!({"dir": -3})).is_err());
        assert!(plan("bevy_inject_move", &json!({})).is_err());
        assert!(plan("bevy_inject_jump", &json!({})).is_err());
    }

    #[test]
    fn frame_advance_and_health_need_no_brp_call() {
        assert!(plan("bevy_wait_frames", &json!({"n": 30}))
            .unwrap()
            .is_empty());
        assert!(plan("bevy_health", &json!({})).unwrap().is_empty());
        assert!(is_plan_free("bevy_wait_frames"));
        assert!(is_plan_free("bevy_health"));
        assert!(!is_plan_free("bevy_grounded"));
    }

    #[test]
    fn a_player_transform_projects_to_x_y_and_frame() {
        let response = json!([{
            "entity": 4294966889u64,
            "components": {
                TRANSFORM_PATH: {"translation": [1.5, -200.0, 0.0], "rotation": [0, 0, 0, 1], "scale": [1, 1, 1]},
                PLAYER_PATH: {}
            }
        }]);
        let value = project("bevy_player_transform", &[response], 42).unwrap();
        assert_eq!(value, json!({"x": 1.5, "y": -200.0, "frame": 42}));
    }

    #[test]
    fn the_resource_reads_project_to_their_named_fields() {
        let coins = json!({"value": {"coins": 3, "target": 5}});
        assert_eq!(
            project("bevy_coin_counter", &[coins], 7).unwrap(),
            json!({"coins": 3, "frame": 7})
        );
        let won = json!({"value": {"won": true}});
        assert_eq!(
            project("bevy_win_flag", &[won], 8).unwrap(),
            json!({"won": true, "frame": 8})
        );
        let grounded = json!([{"entity": 1, "components": {GROUNDED_PATH: {"on_ground": true}}}]);
        assert_eq!(
            project("bevy_grounded", &[grounded], 9).unwrap(),
            json!({"grounded": true, "frame": 9})
        );
    }

    #[test]
    fn an_absent_player_is_a_contract_violation_not_a_zero() {
        let error = project("bevy_grounded", &[json!([])], 1).unwrap_err();
        match error {
            AdapterError::ContractViolation(message) => {
                assert!(message.contains(PLAYER_PATH), "{message}");
            }
            other => panic!("expected a contract violation, got {other:?}"),
        }
    }

    #[test]
    fn a_row_without_the_frozen_component_is_a_contract_violation() {
        let response = json!([{"entity": 1, "components": {PLAYER_PATH: {}}}]);
        let error = project("bevy_grounded", &[response], 1).unwrap_err();
        assert!(
            matches!(error, AdapterError::ContractViolation(_)),
            "{error:?}"
        );
    }

    #[test]
    fn a_per_component_brp_error_is_a_contract_violation() {
        let response = json!([{
            "entity": 1,
            "components": {PLAYER_PATH: {}},
            "errors": {GROUNDED_PATH: "Unknown component type"}
        }]);
        let error = project("bevy_grounded", &[response], 1).unwrap_err();
        assert!(
            matches!(error, AdapterError::ContractViolation(_)),
            "{error:?}"
        );
    }

    #[test]
    fn a_wrong_typed_field_is_malformed_not_silently_ignored() {
        let response = json!([{"entity": 1, "components": {GROUNDED_PATH: {"on_ground": 1}}}]);
        assert!(matches!(
            project("bevy_grounded", &[response], 1),
            Err(AdapterError::Malformed(_))
        ));
    }

    #[test]
    fn an_unregistered_resource_becomes_a_contract_violation() {
        let error = classify_brp_error(&BrpError::Rpc {
            code: -23502,
            message: "Unknown resource type: hof_game::contract::CoinCounter".to_string(),
        });
        assert!(
            matches!(error, AdapterError::ContractViolation(_)),
            "{error:?}"
        );
        let method = classify_brp_error(&BrpError::Rpc {
            code: -32601,
            message: "Method `world.nope` not found".to_string(),
        });
        assert!(
            matches!(method, AdapterError::Rpc { code: -32601, .. }),
            "{method:?}"
        );
    }
}
