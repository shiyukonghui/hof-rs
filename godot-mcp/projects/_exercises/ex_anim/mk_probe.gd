extends SceneTree

# TASK-111: build the animation probe scene for the H2 family
# (AnimationPlayer / AnimationTree / StateMachine).
#
# H2 was registered unreachable because none of the 20 games uses AnimationPlayer
# or AnimationTree. The family's actual precondition is one AnimationPlayer plus
# one node for a track to address; this script writes exactly that.
#
#   res://scenes/anim.tscn  ->  Node2D "AnimRoot"
#                                 Node2D         "Target"
#                                 AnimationPlayer "Player"   (default library)
#
# `Player.root_node` is left at its engine default (".."), i.e. "AnimRoot", so a
# track path of "Target:position" addresses AnimRoot/Target.
#
# Run headless, after `--import`, from cmd.exe.

func _initialize() -> void:
	var root := Node2D.new()
	root.name = "AnimRoot"

	var target := Node2D.new()
	target.name = "Target"
	target.position = Vector2(0, 0)
	root.add_child(target)
	target.owner = root

	var player := AnimationPlayer.new()
	player.name = "Player"
	# A default library must exist for every animation tool: `animation_named`
	# reads the player's default library, and a player created bare has none.
	var library := AnimationLibrary.new()
	player.add_animation_library("", library)
	root.add_child(player)
	player.owner = root

	var packed := PackedScene.new()
	var perr := packed.pack(root)
	var serr := ResourceSaver.save(packed, "res://scenes/anim.tscn")
	print("MKANIM pack_err=", perr, " save_err=", serr)
	print("MKANIM root_node=", player.root_node, " libraries=", player.get_animation_library_list())
	quit()
