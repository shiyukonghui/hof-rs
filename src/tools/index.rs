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

/// DR-72 ④: the parameter names a tool's schema declares, sorted, or `None` when
/// the snapshot has no entry for it.
///
/// This is the same source `TOOLS.md` is rendered from, and it is what makes a
/// parameter refusal actionable: the engine's `-32602` names the parameter it
/// rejected but not the ones it accepts, and the model that guessed
/// `node_path` for `editor_get_node_properties` (whose schema names it `path`)
/// otherwise has nothing to correct against.
pub fn accepted_parameters(tool: &str) -> Option<Vec<String>> {
    let schemas = embedded_tool_schemas();
    let entry = schemas.iter().find(|entry| tool_name(entry) == tool)?;
    let mut names: Vec<String> = entry
        .pointer("/inputSchema/properties")
        .and_then(Value::as_object)
        .map(|properties| properties.keys().cloned().collect())
        .unwrap_or_default();
    names.sort();
    Some(names)
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

/// The tools whose complete call is spelled out, in preference order.
///
/// Round-5 repair (AC-11): this list is the **delivered** tool surface's names.
/// It used to hold the previous engine's names (`project_get_info`,
/// `editor_play_scene`, `running_game_get_node_property_samples`, …), which no
/// Bevy round's schema contains: `render_tools_markdown_for` skips a preference
/// whose name is not in `schemas`, so the "Complete call examples" section was
/// **empty** in every real Bevy round — the names cost a section and bought
/// nothing.  The semantic layer is listed in its frozen contract order; the
/// generic BRP verbs come after it, so a role that may use both is shown the
/// observation surface first.
const EXAMPLE_PREFERENCE: &[&str] = &[
    "bevy_player_transform",
    "bevy_grounded",
    "bevy_coin_counter",
    "bevy_win_flag",
    "bevy_wait_frames",
    "bevy_inject_move",
    "bevy_inject_jump",
    "bevy_health",
    "rpc.discover",
    "world.query",
    "world.get_components",
    "world.get_resources",
    "world.list_components",
    "world.list_resources",
    "world.list_entities",
    "registry.schema",
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
        render_example(&mut markdown, tool, examples);
    }
    // AC-11: the preference list names the **delivered** Bevy surface.  A schema
    // source that does not contain those names — the editor-mediated channel's
    // offline snapshot, or a future engine's surface — still gets runnable
    // examples rather than an empty section, by taking the first visible tools
    // (the list is already sorted by name, so this is deterministic).  The old
    // engine's names were neither: they matched nothing on a Bevy round *and*
    // shipped into the binary.
    if examples == 0 {
        for tool in visible.iter().take(3) {
            examples += 1;
            render_example(&mut markdown, tool, examples);
        }
    }
    if examples == 0 {
        markdown.push_str("_No example is available for this role._\n");
    }
    // DR-66 ①: one delivery point for every shell-variable form in the document.
    crate::runtime::shell::render_command_vars(&markdown, flavor)
}

/// One complete-call example: the command line and the arguments file it needs.
fn render_example(markdown: &mut String, tool: &Value, index: usize) {
    let name = tool_name(tool);
    markdown.push_str(&format!(
        "{index}. `{{{{HOH_HOH_BIN}}}} tools call {name} --args-file \
         {{{{HOH_ARTIFACT_DIR}}}}/args/{name}.json`\n\n"
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
        for (property_name, property) in properties {
            if required.contains(&property_name.as_str()) {
                arguments.insert(
                    property_name.clone(),
                    example_value(property_name, property),
                );
            }
        }
    }
    markdown.push_str(&format!(
        "   `args/{name}.json`: `{}`\n\n",
        serde_json::to_string(&Value::Object(arguments)).unwrap_or_default()
    ));
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
        assert!(schemas
            .iter()
            .any(|tool| tool_name(tool) == "editor_play_scene"));
        assert!(schemas
            .iter()
            .any(|tool| tool_name(tool) == "running_game_capture_screenshot"));
        assert!(schemas
            .iter()
            .any(|tool| tool_name(tool) == "project_get_info"));
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

    /// AC-11: the "Complete call examples" section must name tools the round can
    /// actually call.  The production preference list used to hold the previous
    /// engine's names, which no Bevy round's schema contains — so the section was
    /// empty for every real Bevy role while the constant still shipped those
    /// names into the binary.
    #[test]
    fn the_complete_call_examples_are_the_delivered_bevy_tools() {
        let list = crate::adapter::mcp::tool_list();
        let schemas: Vec<Value> = list
            .get("tools")
            .and_then(Value::as_array)
            .cloned()
            .unwrap_or_default();
        assert!(
            !schemas.is_empty(),
            "the Bevy tool list is the surface a Bevy round delivers"
        );
        let developer = render_tools_markdown(Role::Developer, &schemas);
        assert!(
            developer.contains("tools call bevy_player_transform --args-file"),
            "a Bevy role must be shown a complete call it can run:\n{developer}"
        );
        assert!(
            !developer.contains("_No example is available for this role._"),
            "the example section must not be empty for the delivered surface"
        );
        for old in ["project_", "editor_", "running_game_", "godot", "scene"] {
            assert!(
                !EXAMPLE_PREFERENCE.iter().any(|name| name.contains(old)),
                "the production example preference still names the previous engine (`{old}`)"
            );
        }
    }
}
