extends SceneTree

# TASK-113: build the probe scene the H4 (navigation) / H9 (recording) families
# need, using only the engine's own API. See the generator's header.

func _initialize() -> void:
	var script_path := "res://src/move_player.gd"
	var f := FileAccess.open(script_path, FileAccess.WRITE)
	f.store_string("""extends CharacterBody2D
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
""")
	f.close()

	var root := Node2D.new()
	root.name = "NavRoot"

	var poly := NavigationPolygon.new()
	var outline := PackedVector2Array([
		Vector2(40.0, 40.0), Vector2(760.0, 40.0),
		Vector2(760.0, 560.0), Vector2(40.0, 560.0)])
	poly.add_outline(outline)

	var region := NavigationRegion2D.new()
	region.name = "Region"
	region.navigation_polygon = poly
	root.add_child(region)
	region.owner = root

	var player := CharacterBody2D.new()
	player.name = "Player"
	player.position = Vector2(100.0, 300.0)
	var scr := load(script_path)
	if scr != null:
		player.set_script(scr)
	root.add_child(player)
	player.owner = root

	var drawn := Polygon2D.new()
	drawn.name = "Drawn"
	drawn.polygon = PackedVector2Array([
		Vector2(-12.0, -12.0), Vector2(12.0, -12.0),
		Vector2(12.0, 12.0), Vector2(-12.0, 12.0)])
	drawn.color = Color(0.9, 0.2, 0.2, 1.0)
	player.add_child(drawn)
	drawn.owner = root

	var agent := NavigationAgent2D.new()
	agent.name = "Agent"
	agent.radius = 8.0
	agent.max_speed = 240.0
	player.add_child(agent)
	agent.owner = root

	var goal := Node2D.new()
	goal.name = "Goal"
	goal.position = Vector2(700.0, 300.0)
	root.add_child(goal)
	goal.owner = root

	var hud := Label.new()
	hud.name = "HUD"
	hud.text = "ex"
	hud.position = Vector2(20.0, 20.0)
	root.add_child(hud)
	hud.owner = root

	var packed := PackedScene.new()
	var perr := packed.pack(root)
	var serr := ResourceSaver.save(packed, "res://scenes/main.tscn")
	print("MKNAV pack_err=", perr, " save_err=", serr,
		" outlines=", poly.get_outline_count(), " outline_pts=", outline.size())
	quit()
