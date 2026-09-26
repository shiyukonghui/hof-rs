extends Node2D
# MCP round-7 mini game.
#
# The picture must only change when a tool changes it: there is no animation in
# `_process`, so a "same call twice" pair is a real no-effect pair and not an
# artefact of a moving target.

var moves := 0

func _ready() -> void:
	print("MCP089_MINIGAME_READY name=", name, " player=", $Player.position)

func move_player(dx: float) -> float:
	moves += 1
	var player: ColorRect = $Player
	player.position.x += dx
	print("MCP089_MOVE moves=", moves, " x=", player.position.x)
	return player.position.x

func set_hud(text: String) -> void:
	$HUD.text = text
