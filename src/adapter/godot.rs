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
"#;

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

#[async_trait::async_trait]
impl ProjectAdapter for GodotAdapter {
    fn initialize(&self, workspace: &Path) -> anyhow::Result<()> {
        std::fs::create_dir_all(workspace)?;
        let project_file = workspace.join("project.godot");
        if project_file.is_file() {
            // Already a Godot project: initialization is idempotent.
            return Ok(());
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
        Ok(())
    }

    fn cache_excludes(&self) -> Vec<String> {
        let mut excludes = vec![".hoh".to_string(), ".git".to_string()];
        excludes.extend(self.config.cache_excludes.iter().cloned());
        excludes
    }

    async fn build_check(
        &self,
        _candidate_view: &Path,
        tools: &dyn ToolChannel,
    ) -> anyhow::Result<Vec<ExecRecord>> {
        let mut records = Vec::new();

        // 1. reload_project is executed by the runtime because the Tester is
        //    not allowed to call it; the result is informational only.
        let _ = tools
            .call(Role::Developer, "reload_project", serde_json::json!({}))
            .await;

        // 2. Editor errors.
        let errors = tools
            .call(Role::Tester, "get_editor_errors", serde_json::json!({}))
            .await;
        let observation = match errors {
            Ok(result) => {
                let payload = result.payload.to_string();
                if payload.contains("error") && !payload.contains("\"errors\":[]") {
                    format!("editor reported errors:\n{payload}")
                } else {
                    "editor has no errors".to_string()
                }
            }
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
        // The editor-scope limitation is published as a run warning (D7) rather
        // than as a fake pass: it cannot be verified from the filesystem.
        Ok(items)
    }
}
