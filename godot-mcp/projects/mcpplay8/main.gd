extends Node2D
# MCP round-8 mini game (TASK-090 item C).
var moves := 0
var last_input := ""

func _ready() -> void:
	$MoveButton.pressed.connect(_on_move_button_pressed)
	# TASK-090 item C, round-8 finding: the injected `mcp_right` action is
	# delivered to `_input` even when the InputMap does not declare it, but
	# `event.is_action_pressed("mcp_right")` resolves through
	# `InputMap::event_get_action_status`, which answers false for an action the
	# InputMap does not have (core/input/input_map.cpp:291-292). Declaring the
	# action is what makes the scenario's input step observable - and that is the
	# game's job, not the tool's.
	if not InputMap.has_action("mcp_right"):
		InputMap.add_action("mcp_right")
	print("MCP090_MINIGAME_READY name=", name, " player=", $Player.position, " mcp_right_in_map=", InputMap.has_action("mcp_right"))

func move_player(dx: float) -> float:
	moves += 1
	var player: ColorRect = $Player
	player.position.x += dx
	print("MCP090_MOVE moves=", moves, " x=", player.position.x)
	return player.position.x

func set_hud(new_text: String) -> void:
	$HUD.text = new_text

func set_player_color(new_color: Color) -> void:
	$Player.color = new_color

func _input(event: InputEvent) -> void:
	if event.is_action_pressed("mcp_right"):
		last_input = "mcp_right"
		move_player(25.0)

func _on_move_button_pressed() -> void:
	last_input = "button"
	move_player(10.0)