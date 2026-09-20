//! `GodotAdapter`: the first project adapter (A3).
//!
//! It knows three things: what a minimal Godot 4 project looks like, which MCP
//! tools constitute a deterministic build/boot check, and what a Tester must
//! collect as evidence.

use std::path::Path;

use crate::adapter::{DoctorItem, ProjectAdapter};
use crate::config::GodotConfig;
use crate::model::{ExecKind, ExecRecord, Role};
use crate::tools::ToolChannel;

#[derive(Clone, Debug)]
pub struct GodotAdapter {
    pub config: GodotConfig,
    pub force_init: bool,
}

const PROJECT_GODOT: &str = r#"; Engine configuration file.
config_version=5

[application]

config/name="HoH Mario"
run/main_scene="res://scenes/main.tscn"
config/features=PackedStringArray("4.7")

[display]

window/size/viewport_width=640
window/size/viewport_height=360

[input]

move_left={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":4194319,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
]
}
move_right={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":4194321,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
]
}
jump={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":32,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
]
}

[rendering]

renderer/rendering_method="gl_compatibility"

[editor_plugins]

enabled=PackedStringArray("res://addons/godot_mcp_rs/plugin.cfg")
"#;

/// The plugin entry `initialize` must guarantee (DR-4).
pub const MCP_PLUGIN_PATH: &str = "res://addons/godot_mcp_rs/plugin.cfg";
const EDITOR_PLUGINS_HEADER: &str = "[editor_plugins]";

const MAIN_SCENE: &str = r#"[gd_scene load_steps=2 format=3]

[node name="Main" type="Node2D"]

[node name="Ground" type="StaticBody2D" parent="."]

[node name="CollisionShape2D" type="CollisionShape2D" parent="Ground"]

[node name="Player" type="CharacterBody2D" parent="."]

[node name="Goal" type="Area2D" parent="."]

[node name="HUD" type="CanvasLayer" parent="."]
"#;

impl GodotAdapter {
    pub fn new(config: GodotConfig, force_init: bool) -> Self {
        Self { config, force_init }
    }
}

/// Write `lines` back as an LF-terminated file.
fn write_lines(path: &Path, lines: &[String]) -> anyhow::Result<()> {
    let mut text = lines.join("\n");
    text.push('\n');
    std::fs::write(path, text)?;
    Ok(())
}

/// Guarantee `[editor_plugins]` + `enabled` contains the MCP plugin (DR-4).
///
/// Idempotent by construction: when the entry is already present the file is
/// left byte-for-byte untouched, and an existing `enabled` list keeps every
/// other plugin it names.
fn ensure_plugin_enabled(project_file: &Path) -> anyhow::Result<()> {
    let raw = std::fs::read_to_string(project_file)?;
    let mut lines: Vec<String> = raw.lines().map(ToOwned::to_owned).collect();

    let Some(header) = lines
        .iter()
        .position(|line| line.trim() == EDITOR_PLUGINS_HEADER)
    else {
        lines.push(String::new());
        lines.push(EDITOR_PLUGINS_HEADER.to_string());
        lines.push(String::new());
        lines.push(format!("enabled=PackedStringArray(\"{MCP_PLUGIN_PATH}\")"));
        return write_lines(project_file, &lines);
    };

    let end = (header + 1..lines.len())
        .find(|&index| lines[index].trim_start().starts_with('['))
        .unwrap_or(lines.len());
    let enabled = (header + 1..end).find(|&index| lines[index].trim_start().starts_with("enabled"));
    let Some(enabled) = enabled else {
        lines.insert(
            header + 1,
            format!("enabled=PackedStringArray(\"{MCP_PLUGIN_PATH}\")"),
        );
        return write_lines(project_file, &lines);
    };

    if lines[enabled].contains(MCP_PLUGIN_PATH) {
        // Already enabled: never touch the file.
        return Ok(());
    }

    let line = lines[enabled].clone();
    match (line.find('('), line.rfind(')')) {
        (Some(open), Some(close)) if close > open => {
            let inner = line[open + 1..close].trim();
            let inner = if inner.is_empty() {
                format!("\"{MCP_PLUGIN_PATH}\"")
            } else {
                format!("{inner}, \"{MCP_PLUGIN_PATH}\"")
            };
            lines[enabled] = format!(
                "{}PackedStringArray({inner}){}",
                &line[..open],
                &line[close + 1..]
            );
        }
        _ => {
            lines[enabled] = format!("enabled=PackedStringArray(\"{MCP_PLUGIN_PATH}\")");
        }
    }
    write_lines(project_file, &lines)
}

#[async_trait::async_trait]
impl ProjectAdapter for GodotAdapter {
    fn initialize(&self, workspace: &Path) -> anyhow::Result<()> {
        std::fs::create_dir_all(workspace)?;
        let project_file = workspace.join("project.godot");
        if project_file.is_file() {
            // Already a Godot project: scaffolding is a no-op, but the MCP
            // plugin enablement is still enforced (DR-4), so an `A₀` that was
            // created earlier can be repaired in place.
            return ensure_plugin_enabled(&project_file);
        }
        let non_empty = std::fs::read_dir(workspace)?.next().is_some();
        if non_empty && !self.force_init {
            anyhow::bail!(
                "workspace {} already exists and is not empty; pass --force-init to scaffold \
                 over it",
                workspace.display()
            );
        }

        std::fs::write(&project_file, PROJECT_GODOT)?;
        std::fs::create_dir_all(workspace.join("scenes"))?;
        std::fs::write(workspace.join("scenes/main.tscn"), MAIN_SCENE)?;
        std::fs::create_dir_all(workspace.join("scripts"))?;
        std::fs::write(
            workspace.join("scripts/README.md"),
            "# Scripts\n\nGDScript sources live here.\n",
        )?;

        let addon_source = &self.config.addon_source;
        if addon_source.is_dir() {
            let destination = workspace.join("addons/godot_mcp_rs");
            crate::runtime::view::copy_tree(addon_source, &destination, &[])?;
        } else {
            std::fs::write(
                workspace.join("ADDON_MISSING.txt"),
                format!(
                    "The Godot MCP addon source {} does not exist on this machine.\n",
                    addon_source.display()
                ),
            )?;
        }
        ensure_plugin_enabled(&project_file)?;
        Ok(())
    }

    /// Cache directories only.
    ///
    /// DR-11: adding a *real* artifact path here silently disables the
    /// `hash_tree` based write-detection of R2/R3 — the runtime excludes these
    /// names from hashing and from snapshots, so an excluded file can no longer
    /// be seen when a read-only role writes it.
    fn cache_excludes(&self) -> Vec<String> {
        let mut excludes = vec![".hoh".to_string(), ".git".to_string()];
        excludes.extend(self.config.cache_excludes.iter().cloned());
        excludes
    }

    async fn build_check(
        &self,
        _workspace: &Path,
        tools: &dyn ToolChannel,
    ) -> anyhow::Result<Vec<ExecRecord>> {
        let mut records = Vec::new();

        // 1. reload_project is executed by the runtime because the Tester is
        //    not allowed to call it; the result is informational only.
        let _ = tools
            .call(Role::Developer, "reload_project", serde_json::json!({}))
            .await;

        // 2. Editor errors.  DR-5: decide on the parsed `errors` array, never
        //    on a substring heuristic — an observation may legally contain the
        //    word "error" while the editor is clean, and vice versa.
        let errors = tools
            .call(Role::Tester, "get_editor_errors", serde_json::json!({}))
            .await;
        let observation = match errors {
            Ok(result) => describe_editor_errors(&result.payload),
            Err(error) => format!("get_editor_errors failed: {error}"),
        };
        records.push(ExecRecord {
            kind: ExecKind::Build,
            path: None,
            observation,
            candidate_id: String::new(),
        });

        // 3. Boot the main scene, snapshot the tree, then stop it.
        let play_args = serde_json::json!({"scene_path": self.config.main_scene});
        let play = tools.call(Role::Tester, "play_scene", play_args).await;
        let boot_observation = match play {
            Ok(_) => {
                let tree = tools
                    .call(Role::Tester, "get_game_scene_tree", serde_json::json!({}))
                    .await;
                let _ = tools
                    .call(Role::Tester, "stop_scene", serde_json::json!({}))
                    .await;
                match tree {
                    Ok(result) => format!("main scene booted; scene tree: {}", result.payload),
                    Err(error) => {
                        format!("main scene booted but get_game_scene_tree failed: {error}")
                    }
                }
            }
            Err(error) => format!("play_scene failed: {error}"),
        };
        records.push(ExecRecord {
            kind: ExecKind::RuntimeTrace,
            path: None,
            observation: boot_observation,
            candidate_id: String::new(),
        });

        Ok(records)
    }

    fn evidence_playbook(&self) -> String {
        r#"# Evidence playbook (Godot)

Collect one public execution record per checkable claim. Every artifact you
reference must be written under `.hoh/evidence/` and referenced by a **relative**
path (`.hoh/evidence/<file>`).

## 1. Movement (F1)
```
hoh tools call simulate_sequence --args-file seq.json
# seq.json: {"actions":[{"action":"move_right","duration_ms":800}]}
hoh tools call monitor_properties --args-file props.json
# props.json: {"node_path":"/root/Main/Player","properties":["position"]}
hoh tools call capture_frames --args-file frames.json
# frames.json: {"count":2,"output_dir":".hoh/evidence/move"}
```
Record: before/after `position:x` from `monitor_properties`, plus the screenshot
paths.

## 2. Jump (F2)
```
hoh tools call simulate_sequence --args-file jump.json
# jump.json: {"actions":[{"action":"jump","duration_ms":150}]}
hoh tools call assert_node_state --args-file assert.json
# assert.json: {"node_path":"/root/Main/Player","property":"position:y","expected":"<0"}
```

## 3. Contact with an enemy / coin (F8, F10)
Drive the player into the object with `simulate_sequence`, then read the HUD
counter with `get_game_node_properties` and screenshot the result.

## 4. Deterministic start
`.hoh/deterministic/*.json` records `get_editor_errors` and the scene tree right
after `play_scene`. They prove the project still starts; they never prove
gameplay behaviour.

## Rules
- One `execution_records` entry per observation, with the verbatim output.
- A claim is `verified` only if the cited record visibly shows the behaviour.
- Anything you could not observe is a `gap` with `player_impact` and
  `recommended_update`.
- Never modify the project: use `simulate_*` inputs only.
"#
        .to_string()
    }

    fn tool_policy(&self, role: Role) -> Vec<String> {
        // The authoritative filter is the role matrix in the tool channel; this
        // list only documents the intent for `TOOLS.md` consumers.
        match role {
            Role::Planner => Vec::new(),
            Role::Developer => vec!["*".to_string()],
            Role::Tester => vec![
                "get_*".to_string(),
                "list_*".to_string(),
                "simulate_*".to_string(),
                "assert_*".to_string(),
                "capture_frames".to_string(),
                "play_scene".to_string(),
                "stop_scene".to_string(),
                "monitor_properties".to_string(),
            ],
        }
    }

    fn doctor(&self, workspace: &Path) -> anyhow::Result<Vec<DoctorItem>> {
        let mut items = Vec::new();
        let project = workspace.join("project.godot");
        items.push(DoctorItem {
            name: "godot.project_file".to_string(),
            ok: project.is_file(),
            detail: project.display().to_string(),
        });
        let addon = workspace.join("addons/godot_mcp_rs");
        items.push(DoctorItem {
            name: "godot.mcp_addon".to_string(),
            ok: addon.is_dir(),
            detail: addon.display().to_string(),
        });
        // DR-6: the editor-scope limitation cannot be verified from the
        // filesystem, so it is published as an explicit human-confirmation item
        // (ok = true: it never blocks a run, but it is never hidden either).
        items.push(DoctorItem {
            name: "godot.editor_scope".to_string(),
            ok: true,
            detail: format!(
                "{} Confirm manually that the project currently open in the editor is exactly \
                 this workspace ({}); the runtime cannot verify it.",
                crate::runtime::run_loop::MCP_SCOPE_WARNING,
                workspace.display()
            ),
        });
        Ok(items)
    }
}

/// DR-5: turn a `get_editor_errors` payload into an observation.
///
/// The editor's answer is the authoritative signal.  A payload that is not an
/// object carrying an `errors` array cannot be interpreted as "clean", so it is
/// conservatively recorded as an error together with its verbatim text.
fn describe_editor_errors(payload: &serde_json::Value) -> String {
    let rendered = payload.to_string();
    match payload.get("errors").and_then(serde_json::Value::as_array) {
        Some(errors) if errors.is_empty() => "editor has no errors".to_string(),
        Some(errors) => format!(
            "editor reported {} error(s):\n{rendered}",
            errors.len()
        ),
        None => format!(
            "the get_editor_errors payload could not be parsed as JSON (treated as errors):\n{rendered}"
        ),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::tools::ToolResult;
    use serde_json::Value;

    fn adapter(addon: &Path) -> GodotAdapter {
        GodotAdapter::new(
            GodotConfig {
                addon_source: addon.to_path_buf(),
                cache_excludes: vec![".godot".to_string(), ".import".to_string()],
                main_scene: "res://scenes/main.tscn".to_string(),
            },
            false,
        )
    }

    /// Minimal MCP stand-in: `get_editor_errors` returns a canned payload.
    struct StubChannel {
        errors: Value,
    }

    #[async_trait::async_trait]
    impl ToolChannel for StubChannel {
        fn allowed(&self, _role: Role, _tool: &str) -> bool {
            true
        }

        fn index_markdown(&self, _role: Role) -> String {
            String::new()
        }

        async fn call(&self, _role: Role, tool: &str, _args: Value) -> anyhow::Result<ToolResult> {
            let payload = match tool {
                "get_editor_errors" => self.errors.clone(),
                "play_scene" => serde_json::json!({"ok": true}),
                "get_game_scene_tree" => serde_json::json!({"tree": []}),
                _ => serde_json::json!({}),
            };
            Ok(ToolResult { ok: true, payload })
        }
    }

    async fn build_record(errors: Value) -> ExecRecord {
        let temp = tempfile::tempdir().unwrap();
        let workspace = temp.path().join("mario");
        std::fs::create_dir_all(&workspace).unwrap();
        let channel = StubChannel { errors };
        adapter(&temp.path().join("addon"))
            .build_check(&workspace, &channel)
            .await
            .unwrap()
            .into_iter()
            .next()
            .expect("the build record is always produced")
    }

    #[test]
    fn initializes_a_minimal_project() {
        let temp = tempfile::tempdir().unwrap();
        let workspace = temp.path().join("mario");
        let addon = temp.path().join("addon");
        std::fs::create_dir_all(&addon).unwrap();
        std::fs::write(addon.join("plugin.cfg"), "[plugin]\n").unwrap();

        adapter(&addon).initialize(&workspace).unwrap();

        let project = std::fs::read_to_string(workspace.join("project.godot")).unwrap();
        for action in ["move_left", "move_right", "jump"] {
            assert!(project.contains(action), "missing input action {action}");
        }
        assert!(workspace.join("scenes/main.tscn").is_file());
        assert!(workspace.join("addons/godot_mcp_rs/plugin.cfg").is_file());
    }

    #[test]
    fn initialization_is_idempotent_but_never_clobbers_a_foreign_directory() {
        let temp = tempfile::tempdir().unwrap();
        let addon = temp.path().join("addon");
        let workspace = temp.path().join("mario");

        adapter(&addon).initialize(&workspace).unwrap();
        std::fs::write(workspace.join("scripts/player.gd"), "extends Node\n").unwrap();
        // A second call on an existing Godot project is a no-op.
        adapter(&addon).initialize(&workspace).unwrap();
        assert!(workspace.join("scripts/player.gd").is_file());

        // A non-empty directory that is not a Godot project is refused.
        let foreign = temp.path().join("foreign");
        std::fs::create_dir_all(&foreign).unwrap();
        std::fs::write(foreign.join("notes.txt"), "hello\n").unwrap();
        assert!(adapter(&addon).initialize(&foreign).is_err());
    }

    /// DR-4: `initialize` enables the MCP plugin exactly once and never
    /// rewrites a project file that already lists it.
    #[test]
    fn initialize_enables_the_mcp_plugin_idempotently() {
        let temp = tempfile::tempdir().unwrap();
        let addon = temp.path().join("addon");
        std::fs::create_dir_all(&addon).unwrap();
        std::fs::write(addon.join("plugin.cfg"), "[plugin]\n").unwrap();
        let workspace = temp.path().join("mario");

        adapter(&addon).initialize(&workspace).unwrap();
        let first = std::fs::read_to_string(workspace.join("project.godot")).unwrap();
        assert!(first.contains("[editor_plugins]"), "project: {first}");
        assert_eq!(
            first.matches(MCP_PLUGIN_PATH).count(),
            1,
            "the plugin entry must appear exactly once: {first}"
        );

        adapter(&addon).initialize(&workspace).unwrap();
        let second = std::fs::read_to_string(workspace.join("project.godot")).unwrap();
        assert_eq!(first, second, "a second initialize must not touch the file");
        assert_eq!(second.matches(MCP_PLUGIN_PATH).count(), 1);
    }

    /// DR-4: a pre-existing `enabled` list keeps its other entries.
    #[test]
    fn initialize_preserves_other_enabled_plugins() {
        let temp = tempfile::tempdir().unwrap();
        let addon = temp.path().join("addon");
        let workspace = temp.path().join("mario");
        std::fs::create_dir_all(&workspace).unwrap();
        std::fs::write(
            workspace.join("project.godot"),
            "config_version=5\n\n[editor_plugins]\n\n\
             enabled=PackedStringArray(\"res://addons/other/plugin.cfg\")\n",
        )
        .unwrap();

        adapter(&addon).initialize(&workspace).unwrap();
        let updated = std::fs::read_to_string(workspace.join("project.godot")).unwrap();
        assert!(
            updated.contains("res://addons/other/plugin.cfg"),
            "{updated}"
        );
        assert_eq!(updated.matches(MCP_PLUGIN_PATH).count(), 1, "{updated}");

        adapter(&addon).initialize(&workspace).unwrap();
        assert_eq!(
            updated,
            std::fs::read_to_string(workspace.join("project.godot")).unwrap()
        );
    }

    /// DR-5: editor errors are decided by the parsed `errors` array length, not
    /// by a substring heuristic.
    #[tokio::test]
    async fn editor_errors_are_parsed_as_json() {
        // No errors — including the whitespace variant and a payload that
        // merely mentions the word "error".
        for payload in [
            serde_json::json!({"errors": []}),
            serde_json::json!({"status": "ok", "errors": []}),
            serde_json::json!({"errors": [], "note": "there is no error here"}),
        ] {
            let record = build_record(payload).await;
            assert_eq!(
                record.observation, "editor has no errors",
                "payload treated as an error: {}",
                record.observation
            );
        }

        // One error.
        let record = build_record(serde_json::json!({"errors": [{"message": "x"}]})).await;
        assert!(
            record.observation.contains("editor reported 1 error"),
            "{}",
            record.observation
        );
        assert!(record.observation.contains('x'));

        // Not the expected JSON shape at all -> conservatively "has errors".
        let record = build_record(serde_json::json!("exploded: not a json object")).await;
        assert!(
            record.observation.contains("treated as errors"),
            "{}",
            record.observation
        );
    }

    /// DR-6: the editor-scope limitation is published as an explicit,
    /// human-confirmation doctor item instead of being silently assumed.
    #[test]
    fn doctor_publishes_the_editor_scope_confirmation() {
        let temp = tempfile::tempdir().unwrap();
        let items = adapter(&temp.path().join("addon"))
            .doctor(temp.path())
            .unwrap();
        let scope = items
            .iter()
            .find(|item| item.name == "godot.editor_scope")
            .expect("godot.editor_scope must be reported");
        assert!(scope.ok, "the confirmation item never blocks a run");
        assert!(
            scope
                .detail
                .contains(crate::runtime::run_loop::MCP_SCOPE_WARNING),
            "detail: {}",
            scope.detail
        );
        assert!(
            scope.detail.to_lowercase().contains("confirm"),
            "detail: {}",
            scope.detail
        );
    }

    #[test]
    fn cache_excludes_always_contain_the_runtime_paths() {
        let temp = tempfile::tempdir().unwrap();
        let excludes = adapter(&temp.path().join("addon")).cache_excludes();
        assert!(excludes.contains(&".hoh".to_string()));
        assert!(excludes.contains(&".git".to_string()));
        assert!(excludes.contains(&".godot".to_string()));
    }

    #[test]
    fn playbook_covers_the_four_evidence_kinds() {
        let temp = tempfile::tempdir().unwrap();
        let playbook = adapter(&temp.path().join("addon")).evidence_playbook();
        for needle in [
            "simulate_sequence",
            "capture_frames",
            "monitor_properties",
            "assert_node_state",
            ".hoh/evidence/",
        ] {
            assert!(playbook.contains(needle), "playbook is missing {needle}");
        }
    }
}
