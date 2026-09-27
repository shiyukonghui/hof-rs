extends SceneTree

# TASK-111: build the 3D probe scene for the H1 family (3D content pipeline).
#
# The 20-game corpus is entirely 2D, which is why H1 was registered as
# structurally unreachable. That inference is about the *corpus*, not about the
# tools: a project that ships a Node3D scene makes the whole family reachable.
# This script writes exactly that scene, with one MeshInstance3D that already has
# a BoxMesh, so `editor_set_material_3d` (which refuses a mesh-less instance) has
# a real surface to write.
#
# Run headless, after `--import`, from cmd.exe:
#   godot.windows.editor.x86_64.console.exe --headless --path <project> --script res://mk_probe.gd

func _initialize() -> void:
	var root := Node3D.new()
	root.name = "Probe3D"

	var body := MeshInstance3D.new()
	body.name = "Body"
	body.mesh = BoxMesh.new()
	root.add_child(body)
	body.owner = root

	var packed := PackedScene.new()
	var perr := packed.pack(root)
	var serr := ResourceSaver.save(packed, "res://scenes/probe3d.tscn")
	print("MK3D pack_err=", perr, " save_err=", serr)
	print("MK3D saved=res://scenes/probe3d.tscn surfaces=", body.mesh.get_surface_count())
	quit()
