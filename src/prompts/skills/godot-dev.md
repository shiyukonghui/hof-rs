# Skill: Godot 4 development (GDScript)

## Project shape
- `project.godot` at the project root; `res://` is the root of the opened
  project. Main scene: `res://scenes/main.tscn`.
- Scripts under `scripts/*.gd` with `extends` on the first line.
- Never commit or edit `.godot/` or `.import/`; they are generated caches.

## GDScript 4.7 essentials
- `func _ready() -> void:` / `func _physics_process(delta: float) -> void:`
- Typed vars: `@export var speed: float = 220.0`
- Input: `Input.is_action_pressed("move_right")`, `Input.is_action_just_pressed("jump")`
- Signals: `signal died`, `died.emit()`, `body_entered.connect(_on_body_entered)`
- `move_and_slide()` for `CharacterBody2D`; set `velocity` first.
- `@onready var sprite: Sprite2D = $Sprite2D`

## InputMap (must exist in project.godot)
Named actions only — the tester drives them through the editor:
- `move_left`, `move_right`, `jump`
- Prefer `Input.is_action_*` over raw key codes.

## Node naming convention (stable, observable)
- `Player`, `Enemy1`, `Enemy2`, `Coin1`…, `HUD`, `Goal`, `Ground`, `Camera2D`
- Keep names unique and semantic: `assert_node_state` and
  `get_game_node_properties` locate nodes by path.

## Common tool calls
```
hoh tools call get_editor_errors --args-file args.json
hoh tools call play_scene --args-file args.json
hoh tools call get_game_scene_tree --args-file args.json
hoh tools call add_node --args-file args.json
hoh tools call get_game_node_properties --args-file args.json
```
`args.json` holds the tool arguments, e.g. `{"node_path": "/root/Main/Player"}`.
Writing arguments to a file avoids Windows shell quoting problems.
