extends SceneTree

# TASK-113: the H5 (audio) family's subjects. `editor_add_audio_player` only
# creates the node; the stream it should play is a project asset, so the same
# script the other families use also writes a Node2D root with a visible HUD and
# the two WAV assets are produced next to it by the generator (real RIFF files,
# imported by `--import`).

func _initialize() -> void:
	var root := Node2D.new()
	root.name = "AudioRoot"

	var hud := Label.new()
	hud.name = "HUD"
	hud.text = "audio"
	hud.position = Vector2(20.0, 20.0)
	root.add_child(hud)
	hud.owner = root

	var packed := PackedScene.new()
	var perr := packed.pack(root)
	var serr := ResourceSaver.save(packed, "res://scenes/main.tscn")
	print("MKAUDIO pack_err=", perr, " save_err=", serr)
	quit()
