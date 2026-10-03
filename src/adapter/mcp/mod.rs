//! The two-layer MCP tool surface over BRP (DESIGN-DETAIL §2).
//!
//! The design's warning is the reason this module exists at all: the new
//! engine's tool surface must **not** be treated as a renamed version of the old
//! one (`REQUIREMENTS.md` §8: 177 editor-shaped Godot tools vs 23 ECS-shaped BRP
//! verbs).  So there are two layers and no name mapping between them:
//!
//! * [`generic`] — the **23 BRP verbs**, passed through one-to-one.  The MCP
//!   tool name *is* the verb name (`world.get_components+watch` included), the
//!   input schema is generated mechanically from a declared parameter table, and
//!   nothing is added: no renaming, no re-shaping, no defaults.
//! * [`semantic`] — **eight** verbs bound to the frozen reflectable contract in
//!   [`crate::adapter::bevy::contract`].  These are the only tools that know a
//!   game's type paths, and they are the only tools the battery uses.
//!
//! [`server`] binds both layers to a [`crate::adapter::bevy::brp::BrpClient`],
//! validates every call against the generated schema, refuses any name that is
//! not frozen, redacts the evidence, and records one [`evidence::CallEvidence`]
//! per call.  [`mod@evidence`] owns the `runs/bevy-<round>/` layout of
//! DESIGN-DETAIL §6.
//!
//! The whole surface is hashed ([`tool_list_sha256`]) and the hash is pinned in
//! the test suite, because the design freezes the tool list **verbatim**:
//! name, parameters and return shape.  A silent drift is exactly what the pin
//! makes impossible.

pub mod evidence;
pub mod generic;
pub mod semantic;
pub mod server;

use serde_json::{json, Map, Value};

/// Which layer a frozen tool belongs to.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Layer {
    /// One BRP verb, passed through unchanged.
    Generic,
    /// One semantic read/injection bound to the frozen contract.
    Semantic,
}

impl Layer {
    pub fn as_str(self) -> &'static str {
        match self {
            Layer::Generic => "generic",
            Layer::Semantic => "semantic",
        }
    }
}

/// The declared JSON type of one tool parameter.
///
/// This small vocabulary is what "mechanically generated schema" means: a
/// parameter is declared once, in Rust, and its JSON Schema fragment is produced
/// by [`ParamType::schema`] — there is no second, hand-written schema to drift
/// away from the first.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ParamType {
    /// A Bevy `Entity` id: BRP serialises it as an unsigned integer.
    Entity,
    Integer,
    /// An integer restricted to a closed set (the semantic layer's `dir`).
    IntEnum(&'static [i64]),
    Bool,
    /// A boolean that may only be the given value (`bevy_inject_move.level`).
    ConstBool(bool),
    String,
    StringList,
    /// An array of entity ids (`world.reparent_entities.entities`).
    EntityList,
    /// A nested object whose shape BRP defines (`world.query.data`,
    /// `world.insert_components.components`, `registry.schema.type_limit`).
    Object,
    /// Any JSON value (BRP's transparent `value` payloads).
    Any,
}

impl ParamType {
    /// The JSON Schema `type` this parameter produces, for the frozen
    /// description.
    pub fn as_str(self) -> &'static str {
        match self {
            ParamType::Entity | ParamType::Integer | ParamType::IntEnum(_) => "integer",
            ParamType::Bool | ParamType::ConstBool(_) => "boolean",
            ParamType::String => "string",
            ParamType::StringList | ParamType::EntityList => "array",
            ParamType::Object => "object",
            ParamType::Any => "any",
        }
    }

    /// The JSON Schema fragment.
    pub fn schema(self) -> Value {
        match self {
            ParamType::Entity => json!({"type": "integer", "minimum": 0}),
            ParamType::Integer => json!({"type": "integer"}),
            ParamType::IntEnum(values) => json!({"type": "integer", "enum": values}),
            ParamType::Bool => json!({"type": "boolean"}),
            ParamType::ConstBool(value) => json!({"type": "boolean", "const": value}),
            ParamType::String => json!({"type": "string"}),
            ParamType::StringList => json!({"type": "array", "items": {"type": "string"}}),
            ParamType::EntityList => {
                json!({"type": "array", "items": {"type": "integer", "minimum": 0}})
            }
            ParamType::Object => json!({"type": "object", "additionalProperties": true}),
            ParamType::Any => json!({}),
        }
    }
}

/// One declared parameter.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct ParamSpec {
    pub name: &'static str,
    pub ty: ParamType,
    pub required: bool,
    pub description: &'static str,
}

/// A frozen tool.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct ToolSpec {
    /// The MCP tool name.  For the generic layer this **is** the BRP verb.
    pub name: &'static str,
    pub description: &'static str,
    pub params: &'static [ParamSpec],
    pub layer: Layer,
    /// The BRP verb this tool maps one-to-one onto (generic layer only; the
    /// semantic layer plans its calls in [`semantic::plan`]).
    pub method: Option<&'static str>,
    /// Whether BRP answers this method as a `text/event-stream` (`+watch`).
    pub streaming: bool,
    /// Whether the method changes the world (a write — the policy hook's input).
    pub mutating: bool,
}

impl ToolSpec {
    /// The generated input schema: `additionalProperties: false`, so a
    /// misspelled argument is refused instead of silently dropped.
    pub fn input_schema(&self) -> Value {
        let mut properties = Map::new();
        let mut required = Vec::new();
        for param in self.params {
            let mut schema = param.ty.schema();
            if let Some(object) = schema.as_object_mut() {
                object.insert(
                    "description".to_string(),
                    Value::String(param.description.to_string()),
                );
            }
            properties.insert(param.name.to_string(), schema);
            if param.required {
                required.push(Value::String(param.name.to_string()));
            }
        }
        json!({
            "type": "object",
            "properties": Value::Object(properties),
            "required": required,
            "additionalProperties": false,
        })
    }

    /// The MCP `tools/list` entry.
    pub fn to_json(&self) -> Value {
        json!({
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema(),
        })
    }
}

/// Both layers, generic first (the frozen order).
pub fn all_tools() -> Vec<ToolSpec> {
    let mut tools = generic::generic_tools();
    tools.extend(semantic::semantic_tools());
    tools
}

/// The frozen `tools/list` payload.
pub fn tool_list() -> Value {
    json!({"tools": all_tools().iter().map(ToolSpec::to_json).collect::<Vec<_>>()})
}

/// `sha256(canonical_json(tools/list))` — the pinned tool-list hash.
pub fn tool_list_sha256() -> String {
    crate::runtime::policy::sha256_hex(
        crate::adapter::bevy::contract::canonical_json(&tool_list()).as_bytes(),
    )
}

/// The pinned tool-list hash literal.  It is asserted by the test suite, so any
/// change to a name, a parameter or a return shape fails the gate first.
pub const TOOL_LIST_SHA256: &str =
    "e177325fe8b2036c355d37b9373b85b524f4a7f0d999e087711366bca661ae97";

/// The frozen tool count: 23 generic verbs + 8 semantic tools.
pub const TOOL_COUNT: usize = 31;

/// Look up a frozen tool by name; anything else is not callable.
pub fn find_tool(name: &str) -> Option<ToolSpec> {
    all_tools().into_iter().find(|tool| tool.name == name)
}

/// Validate `args` against a generated input schema.
///
/// Deliberately a small, strict subset (type, `required`, `additionalProperties`,
/// `enum`, `const`): it is the same validator for both layers, and its whole job
/// is to refuse a call the server would otherwise have to guess about.
pub fn validate_input(schema: &Value, args: &Value) -> Result<(), String> {
    let Some(args) = args.as_object() else {
        return Err("`arguments` must be a JSON object".to_string());
    };
    if let Some(required) = schema.get("required").and_then(Value::as_array) {
        for name in required.iter().filter_map(Value::as_str) {
            if !args.contains_key(name) {
                return Err(format!("missing required parameter `{name}`"));
            }
        }
    }
    let properties = schema.get("properties").and_then(Value::as_object);
    let additional = schema
        .get("additionalProperties")
        .and_then(Value::as_bool)
        .unwrap_or(true);
    for (name, value) in args {
        let Some(property) = properties.and_then(|properties| properties.get(name)) else {
            if additional {
                continue;
            }
            return Err(format!("unknown parameter `{name}`"));
        };
        validate_type(name, property, value)?;
    }
    Ok(())
}

fn validate_type(name: &str, schema: &Value, value: &Value) -> Result<(), String> {
    match schema.get("type").and_then(Value::as_str) {
        Some("integer") => {
            if value.as_i64().is_none() {
                return Err(format!("`{name}` must be an integer"));
            }
        }
        Some("boolean") => {
            if !value.is_boolean() {
                return Err(format!("`{name}` must be a boolean"));
            }
        }
        Some("string") => {
            if !value.is_string() {
                return Err(format!("`{name}` must be a string"));
            }
        }
        Some("array") => {
            let Some(items) = value.as_array() else {
                return Err(format!("`{name}` must be an array"));
            };
            let item_schema = schema.get("items").cloned().unwrap_or_else(|| json!({}));
            for item in items {
                validate_type(name, &item_schema, item)?;
            }
        }
        Some("object") => {
            if !value.is_object() {
                return Err(format!("`{name}` must be an object"));
            }
        }
        _ => {}
    }
    if let Some(allowed) = schema.get("enum").and_then(Value::as_array) {
        if !allowed.iter().any(|allowed| allowed == value) {
            return Err(format!("`{name}` must be one of {allowed:?}"));
        }
    }
    if let Some(constant) = schema.get("const") {
        if constant != value {
            return Err(format!("`{name}` must be {constant}"));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_generated_schema_marks_required_and_forbids_unknown_parameters() {
        const PARAMS: &[ParamSpec] = &[
            ParamSpec {
                name: "entity",
                ty: ParamType::Entity,
                required: true,
                description: "the entity id",
            },
            ParamSpec {
                name: "strict",
                ty: ParamType::Bool,
                required: false,
                description: "fail instead of skipping",
            },
        ];
        let tool = ToolSpec {
            name: "world.get_components",
            description: "test",
            params: PARAMS,
            layer: Layer::Generic,
            method: Some("world.get_components"),
            streaming: false,
            mutating: false,
        };
        let schema = tool.input_schema();
        assert_eq!(schema["type"], json!("object"));
        assert_eq!(schema["required"], json!(["entity"]));
        assert_eq!(schema["additionalProperties"], json!(false));
        assert_eq!(schema["properties"]["entity"]["type"], json!("integer"));
        assert_eq!(schema["properties"]["strict"]["type"], json!("boolean"));
        assert_eq!(
            schema["properties"]["entity"]["description"],
            json!("the entity id")
        );
        assert_eq!(tool.to_json()["inputSchema"], schema);
    }

    #[test]
    fn the_validator_refuses_what_it_should_and_accepts_what_it_should() {
        const PARAMS: &[ParamSpec] = &[
            ParamSpec {
                name: "resource",
                ty: ParamType::String,
                required: true,
                description: "",
            },
            ParamSpec {
                name: "path",
                ty: ParamType::String,
                required: true,
                description: "",
            },
        ];
        let tool = ToolSpec {
            name: "world.mutate_resources",
            description: "",
            params: PARAMS,
            layer: Layer::Generic,
            method: Some("world.mutate_resources"),
            streaming: false,
            mutating: true,
        };
        let schema = tool.input_schema();
        assert!(validate_input(&schema, &json!({"resource": "r", "path": "p"})).is_ok());
        assert!(validate_input(&schema, &json!({"resource": "r"}))
            .unwrap_err()
            .contains("missing required parameter `path`"));
        assert!(
            validate_input(&schema, &json!({"resource": "r", "path": "p", "typo": 1}))
                .unwrap_err()
                .contains("unknown parameter `typo`")
        );
        assert!(
            validate_input(&schema, &json!({"resource": 1, "path": "p"}))
                .unwrap_err()
                .contains("must be a string")
        );
        assert!(validate_input(&schema, &json!(["not", "an", "object"]))
            .unwrap_err()
            .contains("must be a JSON object"));
    }

    #[test]
    fn the_validator_enforces_enum_and_const() {
        const PARAMS: &[ParamSpec] = &[
            ParamSpec {
                name: "dir",
                ty: ParamType::IntEnum(&[-1, 0, 1]),
                required: true,
                description: "",
            },
            ParamSpec {
                name: "level",
                ty: ParamType::ConstBool(true),
                required: true,
                description: "",
            },
        ];
        let schema = ToolSpec {
            name: "bevy_inject_move",
            description: "",
            params: PARAMS,
            layer: Layer::Semantic,
            method: None,
            streaming: false,
            mutating: true,
        }
        .input_schema();
        assert!(validate_input(&schema, &json!({"dir": 1, "level": true})).is_ok());
        assert!(validate_input(&schema, &json!({"dir": 4, "level": true}))
            .unwrap_err()
            .contains("must be one of"));
        assert!(validate_input(&schema, &json!({"dir": 1, "level": false}))
            .unwrap_err()
            .contains("must be true"));
    }

    #[test]
    fn the_validator_checks_every_element_of_a_list() {
        const PARAMS: &[ParamSpec] = &[ParamSpec {
            name: "components",
            ty: ParamType::StringList,
            required: true,
            description: "",
        }];
        let schema = ToolSpec {
            name: "world.remove_components",
            description: "",
            params: PARAMS,
            layer: Layer::Generic,
            method: Some("world.remove_components"),
            streaming: false,
            mutating: true,
        }
        .input_schema();
        assert!(validate_input(&schema, &json!({"components": ["a", "b"]})).is_ok());
        assert!(validate_input(&schema, &json!({"components": ["a", 2]}))
            .unwrap_err()
            .contains("must be a string"));
        assert!(validate_input(&schema, &json!({"components": "a"}))
            .unwrap_err()
            .contains("must be an array"));
    }

    #[test]
    fn the_tool_list_hash_is_pinned_and_the_list_has_the_frozen_size() {
        assert_eq!(all_tools().len(), TOOL_COUNT);
        assert_eq!(tool_list_sha256(), TOOL_LIST_SHA256);
    }
}
