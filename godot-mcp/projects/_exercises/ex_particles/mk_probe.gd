extends SceneTree

# TASK-113: the H6 (particle) family's subject scene.

func _initialize() -> void:
	var root := Node2D.new()
	root.name = "PartRoot"

	var seed_particles := GPUParticles2D.new()
	seed_particles.name = "Seed"
	seed_particles.position = Vector2(300.0, 300.0)
	seed_particles.amount = 8
	root.add_child(seed_particles)
	seed_particles.owner = root

	var hud := Label.new()
	hud.name = "HUD"
	hud.text = "particles"
	hud.position = Vector2(20.0, 20.0)
	root.add_child(hud)
	hud.owner = root

	var packed := PackedScene.new()
	var perr := packed.pack(root)
	var serr := ResourceSaver.save(packed, "res://scenes/main.tscn")
	print("MKPART pack_err=", perr, " save_err=", serr)
	quit()
