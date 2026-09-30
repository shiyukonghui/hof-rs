//! DR-26: `TOOLS.md` must carry the **real** tool schemas, not a bare name list.
//!
//! `smoke-t2` burned two thirds of the Developer's 150 steps reading the HoH
//! sources and the external `godot-mcp-pro` checkout to *guess* argument names.
//! The discovery document therefore lists, per allowed tool, its parameter
//! names, types and whether they are required — generated from the same
//! `tools/list` payload the server returns (the offline snapshot is embedded at
//! compile time, and a live `tools/list` wins when the editor is reachable).

use serde_json::Value;

use crate::model::Role;
use crate::tools::policy;

/// The captured `tools/list` response (JSON-RPC envelope).  It is the schema
/// snapshot the design names as the generation source; embedding it keeps the
/// document complete even when the editor is offline.
pub const EMBEDDED_TOOLS_SNAPSHOT: &str = include_str!("../../tests/fixtures/mcp/tools_list.json");

/// The tool entries of the snapshot, tolerant of every wrapper shape the MCP
/// server (or a future snapshot) may use.
pub fn embedded_tool_schemas() -> Vec<Value> {
    let raw = EMBEDDED_TOOLS_SNAPSHOT.trim_start_matches('\u{feff}');
    let Ok(value) = serde_json::from_str::<Value>(raw) else {
        return Vec::new();
    };
    for pointer in ["/result/tools", "/tools"] {
        if let Some(tools) = value.pointer(pointer).and_then(Value::as_array) {
            return tools.clone();
        }
    }
    value.as_array().cloned().unwrap_or_default()
}

fn tool_name(tool: &Value) -> &str {
    tool.get("name").and_then(Value::as_str).unwrap_or("")
}

/// The first sentence of a description (the full text is far too long for an
/// index a role reads on every step).
fn first_sentence(description: &str) -> String {
    let trimmed = description.trim();
    if trimmed.is_empty() {
        return "(no description)".to_string();
    }
    let end = trimmed
        .char_indices()
        .find(|(_, character)| matches!(character, '。' | '.' | '\n'))
        .map(|(index, character)| index + character.len_utf8())
        .unwrap_or(trimmed.len());
    trimmed[..end].trim().to_string()
}

/// Deterministic category of a tool, from a fixed hint table.
fn category(tool: &str) -> &'static str {
    const HINTS: &[(&str, &[&str])] = &[
        ("project", &["project", "setting", "uid", "filesystem"]),
        ("script", &["script", "gdscript"]),
        ("scene", &["scene", "tscn"]),
        ("node", &["node"]),
        (
            "input",
            &["simulate", "input", "action", "click", "navigate", "key"],
        ),
        (
            "runtime",
            &[
                "play",
                "stop",
                "game",
                "monitor",
                "record",
                "frame",
                "screenshot",
                "stress",
                "report",
                "wait",
            ],
        ),
        (
            "editor",
            &["editor", "plugin", "output", "selection", "bake"],
        ),
        ("collision", &["collision", "physics"]),
        (
            "search",
            &[
                "search", "find", "list_", "read_", "analyze", "detect", "assert",
            ],
        ),
        ("other", &[]),
    ];
    for (name, hints) in HINTS {
        if hints.iter().any(|hint| tool.contains(hint)) {
            return name;
        }
    }
    "other"
}

/// The three tools whose complete call is spelled out, in preference order.
const EXAMPLE_PREFERENCE: &[&str] = &[
    "project_get_info",
    "editor_get_errors",
    "editor_play_scene",
    "running_game_get_node_property_samples",
    "running_game_get_node_properties",
    "editor_get_collision_info",
    "project_create_script",
    "editor_setup_collision_shape",
    "editor_simulate_input_action",
];

fn property_type(property: &Value) -> String {
    match property.get("type").and_then(Value::as_str) {
        Some("array") => match property.pointer("/items/type").and_then(Value::as_str) {
            Some(item) => format!("array<{item}>"),
            None => "array".to_string(),
        },
        Some(other) => other.to_string(),
        None => "any".to_string(),
    }
}

fn example_value(name: &str, property: &Value) -> Value {
    match property_type(property).as_str() {
        "string" => Value::String(format!("<{name}>")),
        "integer" => Value::from(0),
        "number" => Value::from(0.0),
        "boolean" => Value::Bool(true),
        "array" | "array<string>" => Value::Array(Vec::new()),
        "object" => Value::Object(Default::default()),
        _ => Value::String(format!("<{name}>")),
    }
}

/// Render the role-scoped `TOOLS.md` for the machine this binary runs on.
///
/// DR-66 ①: the document is *executed* by the role, so the variable syntax has
/// to match the role's real shell (mini's `LocalEnvironment` starts `cmd.exe` on
/// Windows and `sh` elsewhere).
pub fn render_tools_markdown(role: Role, schemas: &[Value]) -> String {
    render_tools_markdown_for(role, schemas, crate::runtime::shell::ShellFlavor::HOST)
}

/// DR-66 ①: [`render_tools_markdown`] with an explicit target shell.
pub fn render_tools_markdown_for(
    role: Role,
    schemas: &[Value],
    flavor: crate::runtime::shell::ShellFlavor,
) -> String {
    let mut visible: Vec<&Value> = schemas
        .iter()
        .filter(|tool| !tool_name(tool).is_empty())
        .filter(|tool| policy::tool_allowed(role, tool_name(tool)))
        .collect();
    visible.sort_by_key(|tool| tool_name(tool).to_string());

    let mut markdown = format!(
        "# Tool schemas for `{}`\n\n\
         The runtime generated this from the live `tools/list` schema (or the embedded snapshot \
         when the editor is offline). **Do not read the harness sources to learn the API**: \
         everything you may call is below.\n\n\
         `{}` tool(s) visible. Call one with:\n\n```\n\
         {{{{HOH_HOH_BIN}}}} tools call <tool> --args-file {{{{HOH_ARTIFACT_DIR}}}}/args/<name>.json\n```\n\n\
         The JSON file must use exactly the argument names below. Write temporary files only \
         under `{{{{HOH_SCRATCH_DIR}}}}`.\n\n",
        role.as_str(),
        visible.len()
    );
    if visible.is_empty() {
        markdown
            .push_str("This role may not call any MCP tool. Use read-only shell commands only.\n");
        return crate::runtime::shell::render_command_vars(&markdown, flavor);
    }

    // Group by category, categories in a stable (alphabetical) order.
    let mut categories: std::collections::BTreeMap<&'static str, Vec<&Value>> =
        std::collections::BTreeMap::new();
    for tool in &visible {
        categories
            .entry(category(tool_name(tool)))
            .or_default()
            .push(tool);
    }
    for (name, tools) in categories {
        markdown.push_str(&format!("## {name}\n\n"));
        for tool in tools {
            let name = tool_name(tool);
            let description = tool
                .get("description")
                .and_then(Value::as_str)
                .map(first_sentence)
                .unwrap_or_else(|| "(no description)".to_string());
            markdown.push_str(&format!("### `{name}`\n\n{description}\n\n"));
            let properties = tool
                .pointer("/inputSchema/properties")
                .and_then(Value::as_object);
            let required: Vec<&str> = tool
                .pointer("/inputSchema/required")
                .and_then(Value::as_array)
                .map(|items| items.iter().filter_map(Value::as_str).collect())
                .unwrap_or_default();
            match properties {
                None => markdown.push_str("_No declared arguments._\n\n"),
                Some(properties) if properties.is_empty() => {
                    markdown.push_str("_No arguments._\n\n")
                }
                Some(properties) => {
                    markdown.push_str("| argument | type | required |\n|---|---|---|\n");
                    let mut names: Vec<&String> = properties.keys().collect();
                    names.sort();
                    for property in names {
                        let is_required = required.contains(&property.as_str());
                        markdown.push_str(&format!(
                            "| `{property}` | {} | {} |\n",
                            property_type(&properties[property]),
                            if is_required { "yes" } else { "no" }
                        ));
                    }
                    markdown.push('\n');
                }
            }
        }
    }

    markdown.push_str("## Complete call examples\n\n");
    let mut examples = 0;
    for preferred in EXAMPLE_PREFERENCE {
        if examples == 3 {
            break;
        }
        let Some(tool) = visible.iter().find(|tool| tool_name(tool) == *preferred) else {
            continue;
        };
        examples += 1;
        markdown.push_str(&format!(
            "{examples}. `{{{{HOH_HOH_BIN}}}} tools call {preferred} --args-file \
             {{{{HOH_ARTIFACT_DIR}}}}/args/{preferred}.json`\n\n"
        ));
        let mut arguments = serde_json::Map::new();
        if let Some(properties) = tool
            .pointer("/inputSchema/properties")
            .and_then(Value::as_object)
        {
            let required: Vec<&str> = tool
                .pointer("/inputSchema/required")
                .and_then(Value::as_array)
                .map(|items| items.iter().filter_map(Value::as_str).collect())
                .unwrap_or_default();
            for (name, property) in properties {
                if required.contains(&name.as_str()) {
                    arguments.insert(name.clone(), example_value(name, property));
                }
            }
        }
        markdown.push_str(&format!(
            "   `args/{preferred}.json`: `{}`\n\n",
            serde_json::to_string(&Value::Object(arguments)).unwrap_or_default()
        ));
    }
    if examples == 0 {
        markdown.push_str("_No example is available for this role._\n");
    }
    // DR-66 ①: one delivery point for every shell-variable form in the document.
    crate::runtime::shell::render_command_vars(&markdown, flavor)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// DR-53 (DEF-4): the embedded snapshot is the **177-tool** four-channel
    /// contract — the old name said 174 and its `>= 100` assertion never
    /// noticed when the fixture changed.  Every entry must also be named, so a
    /// tool cannot silently disappear from the index the roles read.
    #[test]
    fn the_snapshot_is_the_real_177_tool_contract() {
        let schemas = embedded_tool_schemas();
        assert_eq!(
            schemas.len(),
            177,
            "the embedded snapshot must be the whole 177-tool contract, got {}",
            schemas.len()
        );
        for tool in &schemas {
            assert!(
                !tool_name(tool).is_empty(),
                "a snapshot entry without a name: {tool}"
            );
        }
        assert!(schemas.iter().any(|tool| tool_name(tool) == "editor_play_scene"));
        assert!(schemas.iter().any(|tool| tool_name(tool) == "running_game_capture_screenshot"));
        assert!(schemas.iter().any(|tool| tool_name(tool) == "project_get_info"));
    }

    #[test]
    fn a_role_only_sees_its_own_tools() {
        let schemas = embedded_tool_schemas();
        let developer = render_tools_markdown(Role::Developer, &schemas);
        let tester = render_tools_markdown(Role::Tester, &schemas);
        let planner = render_tools_markdown(Role::Planner, &schemas);
        assert!(developer.contains("`project_create_script`"));
        assert!(!tester.contains("`project_create_script`"));
        assert!(!planner.contains("`project_get_info`"));
    }
}
