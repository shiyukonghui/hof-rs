//! Layer 1: the 23 BRP verbs, passed through **unchanged** (DESIGN-DETAIL §2.1).
//!
//! Three rules, all mechanical:
//!
//! 1. **The MCP tool name is the BRP verb, verbatim** — `world.get_components`,
//!    `world.get_components+watch`, `rpc.discover`.  There is no renaming from
//!    the old Godot vocabulary (`entity_query`, `resource_get`, …) anywhere in
//!    this file, and a test asserts the intersection is empty
//!    (`REQUIREMENTS.md` §2-3, §8).
//! 2. **The parameter table is the schema.**  Each verb declares its parameters
//!    once; [`crate::adapter::mcp::ToolSpec::input_schema`] generates the JSON
//!    Schema from that declaration, so a hand-written schema cannot drift away
//!    from the wire format.
//! 3. **Values pass through.**  The server sends the caller's `arguments`
//!    verbatim as the JSON-RPC `params` (SPIKE-1 §0.4-2: `Transform` reads as an
//!    array, writes as an array, and `translation.x` is only valid as a *field
//!    path* — any re-shaping by the adapter silently breaks both).
//!
//! The authoritative source for every name and parameter below is
//! `bevy_remote-0.19.1/src/builtin_methods.rs` (`add_default_methods`), as
//! measured live in SPIKE-1 §1.2 (`rpc.discover`, `methodCount: 23`).

use crate::adapter::mcp::{Layer, ParamSpec, ParamType, ToolSpec};

/// All 23 methods, in the order SPIKE-1 §1.2 lists them.
pub const BRP_VERBS: &[ToolSpec] = &[
    ToolSpec {
        name: "rpc.discover",
        description: "Returns the OpenRPC document (method names and the server URL). The \
                      readiness probe and the method-count self-check use it.",
        params: &[],
        layer: Layer::Generic,
        method: Some("rpc.discover"),
        streaming: false,
        mutating: false,
    },
    ToolSpec {
        name: "world.get_components",
        description: "Reads the named components of one entity. Component names are full type \
                      paths including the crate name. `strict` makes a missing component an \
                      error instead of an entry in `errors`.",
        params: &[
            ParamSpec {
                name: "entity",
                ty: ParamType::Entity,
                required: true,
                description: "the entity id",
            },
            ParamSpec {
                name: "components",
                ty: ParamType::StringList,
                required: true,
                description: "full type paths of the components to read",
            },
            ParamSpec {
                name: "strict",
                ty: ParamType::Bool,
                required: false,
                description: "fail on an invalid component instead of skipping it (default false)",
            },
        ],
        layer: Layer::Generic,
        method: Some("world.get_components"),
        streaming: false,
        mutating: false,
    },
    ToolSpec {
        name: "world.query",
        description: "Queries entities by component filter and returns an array of rows \
                      (entity + selected components + `has`). There is no pagination, ordering or \
                      value comparison.",
        params: &[
            ParamSpec {
                name: "data",
                ty: ParamType::Object,
                required: true,
                description: "`{components:[...], option:\"all\"|\"any\", has:[...]}`",
            },
            ParamSpec {
                name: "filter",
                ty: ParamType::Object,
                required: false,
                description: "`{with:[...], without:[...]}` full type paths",
            },
            ParamSpec {
                name: "strict",
                ty: ParamType::Bool,
                required: false,
                description: "fail on an invalid component path instead of skipping it",
            },
        ],
        layer: Layer::Generic,
        method: Some("world.query"),
        streaming: false,
        mutating: false,
    },
    ToolSpec {
        name: "world.list_components",
        description: "Without `entity`: every registered component type path. With `entity`: the \
                      component names on that entity.",
        params: &[ParamSpec {
            name: "entity",
            ty: ParamType::Entity,
            required: false,
            description: "the entity to inspect; omit to list all registered components",
        }],
        layer: Layer::Generic,
        method: Some("world.list_components"),
        streaming: false,
        mutating: false,
    },
    ToolSpec {
        name: "world.get_components+watch",
        description:
            "Server-sent event stream of the named components whenever they change or are \
                      removed. Streaming: the connection stays open, and a slow consumer can have \
                      it closed silently (bounded(8) + try_send).",
        params: &[
            ParamSpec {
                name: "entity",
                ty: ParamType::Entity,
                required: true,
                description: "the entity to watch",
            },
            ParamSpec {
                name: "components",
                ty: ParamType::StringList,
                required: true,
                description: "full type paths of the components to watch",
            },
            ParamSpec {
                name: "strict",
                ty: ParamType::Bool,
                required: false,
                description: "fail on an invalid component instead of skipping it",
            },
        ],
        layer: Layer::Generic,
        method: Some("world.get_components+watch"),
        streaming: true,
        mutating: false,
    },
    ToolSpec {
        name: "world.list_components+watch",
        description: "Server-sent event stream of component names added to or removed from one \
                      entity.",
        params: &[ParamSpec {
            name: "entity",
            ty: ParamType::Entity,
            required: true,
            description: "the entity to watch",
        }],
        layer: Layer::Generic,
        method: Some("world.list_components+watch"),
        streaming: true,
        mutating: false,
    },
    ToolSpec {
        name: "world.get_resources",
        description: "Reads one registered reflectable resource by its full type path. An \
                      unregistered resource is an error, not a null.",
        params: &[ParamSpec {
            name: "resource",
            ty: ParamType::String,
            required: true,
            description: "full type path of the resource",
        }],
        layer: Layer::Generic,
        method: Some("world.get_resources"),
        streaming: false,
        mutating: false,
    },
    ToolSpec {
        name: "world.list_resources",
        description: "Every registered reflectable resource type path. Bevy's own resources are \
                      mostly absent here (measured: 44 of them, and `Time` is not among them).",
        params: &[],
        layer: Layer::Generic,
        method: Some("world.list_resources"),
        streaming: false,
        mutating: false,
    },
    ToolSpec {
        name: "world.insert_resources",
        description: "Inserts or replaces one resource with the given value.",
        params: &[
            ParamSpec {
                name: "resource",
                ty: ParamType::String,
                required: true,
                description: "full type path of the resource",
            },
            ParamSpec {
                name: "value",
                ty: ParamType::Any,
                required: true,
                description: "the resource value in the shape its reflect type expects",
            },
        ],
        layer: Layer::Generic,
        method: Some("world.insert_resources"),
        streaming: false,
        mutating: true,
    },
    ToolSpec {
        name: "world.mutate_resources",
        description: "Writes one field of one resource by reflection path (dot path, e.g. \
                      `move_dir`). The injection channel of the semantic layer rides on this.",
        params: &[
            ParamSpec {
                name: "resource",
                ty: ParamType::String,
                required: true,
                description: "full type path of the resource",
            },
            ParamSpec {
                name: "path",
                ty: ParamType::String,
                required: true,
                description: "reflection field path; dot path, never an array index",
            },
            ParamSpec {
                name: "value",
                ty: ParamType::Any,
                required: true,
                description: "the value to write at `path`",
            },
        ],
        layer: Layer::Generic,
        method: Some("world.mutate_resources"),
        streaming: false,
        mutating: true,
    },
    ToolSpec {
        name: "world.remove_resources",
        description: "Removes one resource. Destructive: use it only to reset a measurement, \
                      never between a baseline read and its observation.",
        params: &[ParamSpec {
            name: "resource",
            ty: ParamType::String,
            required: true,
            description: "full type path of the resource",
        }],
        layer: Layer::Generic,
        method: Some("world.remove_resources"),
        streaming: false,
        mutating: true,
    },
    ToolSpec {
        name: "world.insert_components",
        description: "Inserts or replaces components on one entity, keyed by full type path.",
        params: &[
            ParamSpec {
                name: "entity",
                ty: ParamType::Entity,
                required: true,
                description: "the entity to modify",
            },
            ParamSpec {
                name: "components",
                ty: ParamType::Object,
                required: true,
                description: "map of full type path to component value",
            },
        ],
        layer: Layer::Generic,
        method: Some("world.insert_components"),
        streaming: false,
        mutating: true,
    },
    ToolSpec {
        name: "world.remove_components",
        description: "Removes the named components from one entity.",
        params: &[
            ParamSpec {
                name: "entity",
                ty: ParamType::Entity,
                required: true,
                description: "the entity to modify",
            },
            ParamSpec {
                name: "components",
                ty: ParamType::StringList,
                required: true,
                description: "full type paths of the components to remove",
            },
        ],
        layer: Layer::Generic,
        method: Some("world.remove_components"),
        streaming: false,
        mutating: true,
    },
    ToolSpec {
        name: "world.mutate_components",
        description: "Writes one field of one component by reflection path. `translation.x` is \
                      valid; `translation[0]` is not (`Expected index access to access a list`).",
        params: &[
            ParamSpec {
                name: "entity",
                ty: ParamType::Entity,
                required: true,
                description: "the entity to modify",
            },
            ParamSpec {
                name: "component",
                ty: ParamType::String,
                required: true,
                description: "full type path of the component",
            },
            ParamSpec {
                name: "path",
                ty: ParamType::String,
                required: true,
                description: "reflection field path; dot path, never an array index",
            },
            ParamSpec {
                name: "value",
                ty: ParamType::Any,
                required: true,
                description: "the value to write at `path`",
            },
        ],
        layer: Layer::Generic,
        method: Some("world.mutate_components"),
        streaming: false,
        mutating: true,
    },
    ToolSpec {
        name: "world.spawn_entity",
        description: "Creates an entity with initial components and returns its id. Inner math \
                      types must be arrays: `{\"translation\":[x,y,z]}`.",
        params: &[ParamSpec {
            name: "components",
            ty: ParamType::Object,
            required: true,
            description: "map of full type path to component value",
        }],
        layer: Layer::Generic,
        method: Some("world.spawn_entity"),
        streaming: false,
        mutating: true,
    },
    ToolSpec {
        name: "world.despawn_entity",
        description: "Removes one entity.",
        params: &[ParamSpec {
            name: "entity",
            ty: ParamType::Entity,
            required: true,
            description: "the entity to remove",
        }],
        layer: Layer::Generic,
        method: Some("world.despawn_entity"),
        streaming: false,
        mutating: true,
    },
    ToolSpec {
        name: "world.reparent_entities",
        description: "Sets or clears the parent relationship of the given entities. A self-parent \
                      is refused with `-23404`.",
        params: &[
            ParamSpec {
                name: "entities",
                ty: ParamType::EntityList,
                required: true,
                description: "the entities to reparent",
            },
            ParamSpec {
                name: "parent",
                ty: ParamType::Entity,
                required: false,
                description: "the new parent; omit to clear the relationship",
            },
        ],
        layer: Layer::Generic,
        method: Some("world.reparent_entities"),
        streaming: false,
        mutating: true,
    },
    ToolSpec {
        name: "world.trigger_event",
        description: "Triggers an observer event with a JSON payload. The game must declare the \
                      event reflectable; the payload's fields must be named (unit structs \
                      produced no frames through `observe+watch`).",
        params: &[
            ParamSpec {
                name: "event",
                ty: ParamType::String,
                required: true,
                description: "full type path of the event",
            },
            ParamSpec {
                name: "value",
                ty: ParamType::Any,
                required: false,
                description: "the event payload",
            },
        ],
        layer: Layer::Generic,
        method: Some("world.trigger_event"),
        streaming: false,
        mutating: true,
    },
    ToolSpec {
        name: "world.write_message",
        description: "Writes a buffered message. The message type must be reflectable and \
                      registered; an unknown type answers -23501.",
        params: &[
            ParamSpec {
                name: "message",
                ty: ParamType::String,
                required: true,
                description: "full type path of the message",
            },
            ParamSpec {
                name: "value",
                ty: ParamType::Any,
                required: false,
                description: "the message payload",
            },
        ],
        layer: Layer::Generic,
        method: Some("world.write_message"),
        streaming: false,
        mutating: true,
    },
    ToolSpec {
        name: "world.observe+watch",
        description: "Server-sent event stream of a global or entity-scoped observer's event \
                      payloads. Streaming.",
        params: &[
            ParamSpec {
                name: "event",
                ty: ParamType::String,
                required: true,
                description: "full type path of the event to observe",
            },
            ParamSpec {
                name: "entity",
                ty: ParamType::Entity,
                required: false,
                description: "restrict the observer to one entity",
            },
        ],
        layer: Layer::Generic,
        method: Some("world.observe+watch"),
        streaming: true,
        mutating: false,
    },
    ToolSpec {
        name: "registry.schema",
        description: "JSON Schema for the registered types, optionally filtered by crate.",
        params: &[
            ParamSpec {
                name: "without_crates",
                ty: ParamType::StringList,
                required: false,
                description: "crates to exclude",
            },
            ParamSpec {
                name: "with_crates",
                ty: ParamType::StringList,
                required: false,
                description: "crates to include",
            },
            ParamSpec {
                name: "type_limit",
                ty: ParamType::Object,
                required: false,
                description: "`{without:[...], with:[...]}` per-type limits",
            },
        ],
        layer: Layer::Generic,
        method: Some("registry.schema"),
        streaming: false,
        mutating: false,
    },
    ToolSpec {
        name: "schedule.list",
        description: "The schedule labels that exist, plus the ones that are unavailable.",
        params: &[],
        layer: Layer::Generic,
        method: Some("schedule.list"),
        streaming: false,
        mutating: false,
    },
    ToolSpec {
        name: "schedule.graph",
        description: "The system dependency graph of one schedule.",
        params: &[ParamSpec {
            name: "schedule_label",
            ty: ParamType::String,
            required: true,
            description: "a label from `schedule.list`",
        }],
        layer: Layer::Generic,
        method: Some("schedule.graph"),
        streaming: false,
        mutating: false,
    },
];

/// The generic layer, as tool specs.
pub fn generic_tools() -> Vec<ToolSpec> {
    BRP_VERBS.to_vec()
}

/// The 23 verb names, in the frozen order.
pub fn brp_method_names() -> Vec<&'static str> {
    BRP_VERBS.iter().filter_map(|verb| verb.method).collect()
}

/// The streaming (`text/event-stream`) verbs, which need a long-lived connection.
pub fn streaming_methods() -> Vec<&'static str> {
    BRP_VERBS
        .iter()
        .filter(|verb| verb.streaming)
        .filter_map(|verb| verb.method)
        .collect()
}

/// Every mutating verb (the policy hook reads this rather than a hand-written list).
pub fn mutating_methods() -> Vec<&'static str> {
    BRP_VERBS
        .iter()
        .filter(|verb| verb.mutating)
        .filter_map(|verb| verb.method)
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    /// SPIKE-1 §1.2, verbatim and in order: `rpc.discover` reported exactly
    /// these 23 methods on Bevy 0.19.1.
    const SPIKE_VERBS: &[&str] = &[
        "rpc.discover",
        "world.get_components",
        "world.query",
        "world.list_components",
        "world.get_components+watch",
        "world.list_components+watch",
        "world.get_resources",
        "world.list_resources",
        "world.insert_resources",
        "world.mutate_resources",
        "world.remove_resources",
        "world.insert_components",
        "world.remove_components",
        "world.mutate_components",
        "world.spawn_entity",
        "world.despawn_entity",
        "world.reparent_entities",
        "world.trigger_event",
        "world.write_message",
        "world.observe+watch",
        "registry.schema",
        "schedule.list",
        "schedule.graph",
    ];

    #[test]
    fn the_verb_list_is_the_measured_23_in_order() {
        assert_eq!(BRP_VERBS.len(), 23);
        assert_eq!(brp_method_names(), SPIKE_VERBS);
    }

    #[test]
    fn generic_tool_names_are_the_verb_names_verbatim() {
        for verb in BRP_VERBS {
            assert_eq!(
                verb.name,
                verb.method.unwrap(),
                "a generic tool was renamed"
            );
            assert_eq!(verb.layer, Layer::Generic);
        }
    }

    #[test]
    fn no_generic_tool_reuses_an_old_godot_tool_name() {
        // The 177-tool Godot vocabulary is still in the repository (the frozen
        // legacy path), so the "no name mapping" rule can be checked mechanically
        // instead of promised.
        let godot: Vec<String> = crate::tools::index::embedded_tool_schemas()
            .iter()
            .filter_map(|tool| tool.get("name").and_then(|name| name.as_str()))
            .map(ToOwned::to_owned)
            .collect();
        assert!(
            godot.len() > 100,
            "the Godot vocabulary snapshot should be large, found {}",
            godot.len()
        );
        for verb in BRP_VERBS {
            assert!(
                !godot.iter().any(|name| name == verb.name),
                "`{}` is an old Godot tool name",
                verb.name
            );
        }
    }

    #[test]
    fn the_streaming_verbs_are_the_three_plus_watch_methods() {
        assert_eq!(
            streaming_methods(),
            vec![
                "world.get_components+watch",
                "world.list_components+watch",
                "world.observe+watch"
            ]
        );
    }

    #[test]
    fn the_mutating_verbs_are_declared() {
        let mutating = mutating_methods();
        assert!(mutating.contains(&"world.mutate_resources"));
        assert!(mutating.contains(&"world.trigger_event"));
        assert!(mutating.contains(&"world.spawn_entity"));
        assert!(!mutating.contains(&"world.query"));
        assert!(!mutating.contains(&"rpc.discover"));
        assert!(!mutating.contains(&"world.get_resources"));
    }

    #[test]
    fn every_verb_schema_is_mechanical_and_closed() {
        for verb in BRP_VERBS {
            let schema = verb.input_schema();
            assert_eq!(schema["additionalProperties"], serde_json::json!(false));
            assert_eq!(schema["properties"].is_object(), true);
            for param in verb.params {
                assert!(
                    schema["properties"][param.name].is_object(),
                    "{} declares `{}` but the schema has no entry",
                    verb.name,
                    param.name
                );
            }
        }
    }

    #[test]
    fn the_path_parameter_of_the_mutators_is_a_string_not_a_list() {
        // SPIKE-1 §0.4-2: `path` is a reflection field path (`translation.x`).
        for verb in BRP_VERBS.iter().filter(|verb| {
            verb.name == "world.mutate_components" || verb.name == "world.mutate_resources"
        }) {
            let path = verb
                .params
                .iter()
                .find(|param| param.name == "path")
                .expect("a `path` parameter");
            assert_eq!(path.ty, ParamType::String);
        }
    }
}
