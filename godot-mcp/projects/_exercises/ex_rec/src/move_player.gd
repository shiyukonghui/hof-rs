extends CharacterBody2D
# TASK-113 exercise: the H9 recording/replay family needs one motion the *game
# process* really performs from input alone. `Input.is_key_pressed` is fed by the
# key events `running_game_play_input_recording` injects through
# `Input::parse_input_event`, so a replay moves this node and the pixel diff and
# `running_game_get_node_properties` both see it.
const SPEED := 180.0

func _physics_process(delta: float) -> void:
	var dx := 0.0
	if Input.is_key_pressed(KEY_RIGHT):
		dx += SPEED * delta
	if Input.is_key_pressed(KEY_LEFT):
		dx -= SPEED * delta
	if dx != 0.0:
		global_position.x += dx
