# Skill: Godot 4 development — verified recipes

Every recipe below is copy-pasteable. Replace the angle-bracket placeholders and
run the commands from the project root. `$HOH_ARTIFACT_DIR` expands to the
absolute path of the role's `.hoh` directory, so `--args-file` always receives an
absolute path (a relative one is resolved against the *current* directory and
will fail from a different one).

## 0. How to call any editor tool
```
$HOH_HOH_BIN tools call <tool_name> --args-file $HOH_ARTIFACT_DIR/args/<name>.json
```
Write the JSON arguments first (a file avoids Windows quoting problems), then
call. A failed call exits non-zero and prints the JSON-RPC error verbatim — read
it instead of retrying blindly.

## 1. Write a script and prove it is not empty
Scripts are the usual cause of "the feature exists but nothing happens": a
0-byte `player.gd` still counts as an existing file.
```
# args/create_player.json
{"path":"res://scripts/player.gd","content":"extends CharacterBody2D\n\n@export var speed: float = 220.0\nvar gravity: float = 980.0\n\nfunc _physics_process(delta: float) -> void:\n\tvar dir := Input.get_axis(\"move_left\", \"move_right\")\n\tvelocity.x = dir * speed\n\tvelocity.y += gravity * delta\n\tmove_and_slide()\n"}
```
```
$HOH_HOH_BIN tools call project_create_script --args-file $HOH_ARTIFACT_DIR/args/create_player.json
$HOH_HOH_BIN tools call project_read_script --args-file $HOH_ARTIFACT_DIR/args/read_player.json
# args/read_player.json: {"path":"res://scripts/player.gd"}
```
`project_read_script` must return a non-zero `size` and the content you wrote. Use
`project_edit_script` (`{"path":..., "content":...}` to replace everything, or
`{"path":..., "search":..., "replace":...}`) to change it, then read it back
again.

## 2. Give every physics body a collision shape
A `CharacterBody2D`/`StaticBody2D` without a shape falls through the world.
```
$HOH_HOH_BIN tools call editor_setup_collision_shape --args-file $HOH_ARTIFACT_DIR/args/player_shape.json
# args/player_shape.json: {"node_path":"Player","shape_type":"RectangleShape2D","shape_params":{"size":{"x":24,"y":32}}}
$HOH_HOH_BIN tools call editor_setup_collision_shape --args-file $HOH_ARTIFACT_DIR/args/ground_shape.json
# args/ground_shape.json: {"node_path":"Ground","shape_type":"RectangleShape2D","shape_params":{"size":{"x":640,"y":32}}}
```
Verify with `editor_get_collision_info` (`{"node_path":"Player"}`) and require
`shape_count > 0`.

## 3. Never leave an Area2D without a body
`Goal` (and any coin/trigger) is an `Area2D`: without a collision shape its
`shape_count` is `0` and the win condition can never fire.
```
$HOH_HOH_BIN tools call editor_setup_collision_shape --args-file $HOH_ARTIFACT_DIR/args/goal_shape.json
# args/goal_shape.json: {"node_path":"Goal","shape_type":"RectangleShape2D","shape_params":{"size":{"x":32,"y":32}}}
```
Create the shape *and* the `CollisionShape2D` node in the same step; a body with
an empty child shape still reports `has_shape: false`.

## 4. HUD text needs a Label
A `CanvasLayer` alone shows nothing. Add a `Label` under `HUD` and give it a
non-empty `text`.
```
$HOH_HOH_BIN tools call editor_add_node --args-file $HOH_ARTIFACT_DIR/args/hud_label.json
# args/hud_label.json: {"type":"Label","name":"Score","parent_path":"HUD","properties":{"text":"Score: 0","position":{"x":8,"y":8}}}
```
Keep the counter updating from GDScript (`$Score.text = "Score: %d" % coins`), and
keep the node named and stable so QA can find it.

## 5. Self-test the behaviour before you finish
Simulate the input, then monitor the property the requirement talks about. A
constant `position` means the behaviour is not implemented, whatever the source
looks like.
```
$HOH_HOH_BIN tools call editor_simulate_input_action --args-file $HOH_ARTIFACT_DIR/args/press_right.json
# args/press_right.json: {"action":"move_right","pressed":true}
$HOH_HOH_BIN tools call running_game_get_node_property_samples --args-file $HOH_ARTIFACT_DIR/args/monitor.json
# args/monitor.json: {"node_path":"Player","properties":["position"],"frame_count":60,"frame_interval":1}
$HOH_HOH_BIN tools call editor_simulate_input_action --args-file $HOH_ARTIFACT_DIR/args/release_right.json
# args/release_right.json: {"action":"move_right","pressed":false}
```
The returned `samples[*].position.x` must change while the key is held. Repeat
for `jump` (`position.y` must go negative) and `move_left`.

## 6. Keep the project launchable at all times
```
$HOH_HOH_BIN tools call editor_get_errors --args-file $HOH_ARTIFACT_DIR/args/errors.json
# args/errors.json: {"max_lines": 50}
$HOH_HOH_BIN tools call editor_play_scene --args-file $HOH_ARTIFACT_DIR/args/play.json
# args/play.json: {"mode":"main"}
$HOH_HOH_BIN tools call running_game_get_scene_tree --args-file $HOH_ARTIFACT_DIR/args/tree.json
# args/tree.json: {"max_depth":-1}
$HOH_HOH_BIN tools call editor_stop_scene --args-file $HOH_ARTIFACT_DIR/args/stop.json
# args/stop.json: {}
```
`{"errors": []}` and a running scene tree are the minimum bar (N1). Never end a
turn with a script that does not compile.

## 7. Known-good minimal platform game skeleton (copy this whole file)
This is a **complete, already-valid** main scene. The runtime validates it with
exactly this rule (DR-24): the **first** `[node ...]` line is the only root and
must have **no** `parent=` attribute; every other node must declare `parent=`
and that path must resolve. Getting this wrong is what made `smoke-t2`
unlaunchable (`Invalid scene: root node Ground cannot specify a parent node`).

```
[gd_scene load_steps=5 format=3]

[ext_resource type="Script" path="res://scripts/player.gd" id="1_player"]

[sub_resource type="RectangleShape2D" id="RectangleShape2D_ground"]
size = Vector2(640, 32)

[sub_resource type="RectangleShape2D" id="RectangleShape2D_player"]
size = Vector2(24, 32)

[sub_resource type="RectangleShape2D" id="RectangleShape2D_goal"]
size = Vector2(32, 32)

[node name="Main" type="Node2D"]

[node name="Ground" type="StaticBody2D" parent="."]

[node name="CollisionShape2D" type="CollisionShape2D" parent="Ground"]
shape = SubResource("RectangleShape2D_ground")

[node name="Player" type="CharacterBody2D" parent="."]
script = ExtResource("1_player")

[node name="CollisionShape2D" type="CollisionShape2D" parent="Player"]
shape = SubResource("RectangleShape2D_player")

[node name="Goal" type="Area2D" parent="."]

[node name="CollisionShape2D" type="CollisionShape2D" parent="Goal"]
shape = SubResource("RectangleShape2D_goal")

[node name="HUD" type="CanvasLayer" parent="."]

[node name="Score" type="Label" parent="HUD"]
offset_left = 8.0
offset_top = 8.0
text = "Score: 0"
```

Notes that make the difference between "looks right" and "runs":

- The root is `[node name="Main" type="Node2D"]` — no `parent=`. Children of the
  root use `parent="."`; the `CollisionShape2D` under `Player` uses
  `parent="Player"`.
- `sub_resource` blocks are declared before the nodes that reference them, and
  are referenced by id: `shape = SubResource("RectangleShape2D_player")`.
- The script is referenced by id: `script = ExtResource("1_player")`, and the
  matching `[ext_resource ... path="res://scripts/player.gd"]` must point at a
  file that exists (write it first).

The matching `scripts/player.gd` must be **non-empty**:

```gdscript
extends CharacterBody2D

@export var speed: float = 220.0
@export var jump_velocity: float = -420.0
var gravity: float = 980.0

func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y += gravity * delta
	if Input.is_action_pressed("jump") and is_on_floor():
		velocity.y = jump_velocity
	var direction := Input.get_axis("move_left", "move_right")
	if direction:
		velocity.x = direction * speed
	else:
		velocity.x = move_toward(velocity.x, 0.0, speed)
	move_and_slide()
```

The HUD `Label` is the `Score` node above (`text = "Score: 0"`); keep it named
and update it from GDScript (`$HUD/Score.text = "Score: %d" % coins`).

## 8. Temporary files: `$HOH_SCRATCH_DIR` only
`$HOH_SCRATCH_DIR` is `<view>/.hoh/scratch` and is excluded from the artifact
hash (DR-28). Write every probe, argument file you do not need again, log and
scratch script there:

```
# good
echo '{"max_lines":50}' > "$HOH_SCRATCH_DIR/errors.json"
# bad: leaves garbage inside the candidate identity
echo '{}' > probe_tmp.json
```

Never leave `_*`, `tmp_*`, `*.bak`, `*.tmp` or a helper `*.py` in the project
root: the runtime reports them in `artifact_hygiene.suspicious_files` and the
Tester records a gap.

## GDScript 4 essentials
- `func _ready() -> void:` / `func _physics_process(delta: float) -> void:`
- Typed vars: `@export var speed: float = 220.0`
- Input: `Input.is_action_pressed("move_right")`, `Input.get_axis("move_left", "move_right")`
- Signals: `signal died`, `died.emit()`, `body_entered.connect(_on_body_entered)`
- `move_and_slide()` for `CharacterBody2D`; set `velocity` first.
- `@onready var score_label: Label = $HUD/Score`

## Naming and InputMap
- Named actions only: `move_left`, `move_right`, `jump` must exist in
  `project.godot` so `editor_simulate_input_action` can drive them.
- Stable node names: `Player`, `Enemy1`, `Coin1`, `HUD`, `Goal`, `Ground`.
  QA locates nodes by path, so a rename breaks the evidence.
