extends Node2D
# TASK-096 A -- the ownership A/B discriminator.
#
# It encodes, in one script, exactly the call batch of
#   recovery\work\task095\sessions\loadednode\session.json  (p01..p07):
#     p01 baseline read -> p02 loaded Background -> magenta -> p03 read
#     p04 runtime-created full-screen ColorRect C9 -> p05 read
#     p06 free C9 + force redraw the loaded item (color/queue_redraw/hide/show/size)
#     p07 read again.
# The reason it is a script and not MCP calls: the stock Godot 4.7.1 build has no
# mcp_server module, so MCP calls cannot run on it at all. Running the identical
# script bytes on both engines is the only way to compare the two engines on the
# same batch of operations.
#
# Every line is prefixed with the step tag so a reader can diff the two engines'
# stdout line by line.

const TAG := "PROBE096"

func _pixels() -> String:
	var img: Image = get_viewport().get_texture().get_image()
	var p1 := img.get_pixel(10, 580)     # covered by Background only
	var p2 := img.get_pixel(400, 580)    # the loaded grid line
	var bg: ColorRect = get_node("Background")
	return "P1(10,580)=%s P2(400,580)=%s bg=%s C9=%s fd=%d objs=%d prims=%d" % [
		str(p1), str(p2), str(bg.color), str(get_node_or_null("C9")),
		Engine.get_frames_drawn(),
		int(Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)),
		int(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)),
	]

func _ready() -> void:
	print("%s|meta|engine=%s display=%s adapter=%s" % [
		TAG, str(Engine.get_version_info().string),
		DisplayServer.get_name(), RenderingServer.get_video_adapter_name()])
	print("%s|p01-baseline|%s" % [TAG, _pixels()])

	var bg: ColorRect = get_node("Background")
	bg.color = Color(1, 0, 1, 1)
	print("%s|p02-loaded-magenta|bg=%s" % [TAG, str(bg.color)])
	await get_tree().create_timer(1.0).timeout
	print("%s|p03-read-loaded|%s" % [TAG, _pixels()])

	var c := ColorRect.new()
	c.name = StringName("C9")
	c.position = Vector2(0, 0)
	c.size = Vector2(800, 600)
	c.color = Color(1, 1, 0, 1)
	add_child(c)
	print("%s|p04-runtime-cover|C9 added %s" % [TAG, str(c.get_path())])
	await get_tree().create_timer(1.0).timeout
	print("%s|p05-read-runtime|%s" % [TAG, _pixels()])

	var c9 := get_node_or_null("C9")
	if c9 != null:
		c9.queue_free()
	bg.color = Color(0, 1, 0, 1)
	bg.queue_redraw()
	bg.hide()
	bg.show()
	bg.size = Vector2(800, 600)
	print("%s|p06-force-redraw-loaded|bg=%s visible=%s size=%s" % [
		TAG, str(bg.color), str(bg.visible), str(bg.size)])
	await get_tree().create_timer(1.2).timeout
	print("%s|p07-read-forced|%s" % [TAG, _pixels()])

	# A pure-runtime control at the very end: if THIS is frozen too, the readback
	# channel itself would be the suspect rather than the loaded item.
	var c10 := ColorRect.new()
	c10.name = StringName("C10")
	c10.position = Vector2(0, 0)
	c10.size = Vector2(800, 600)
	c10.color = Color(1, 0, 0, 1)
	add_child(c10)
	await get_tree().create_timer(0.6).timeout
	print("%s|p08-runtime-red|%s" % [TAG, _pixels()])
	c10.color = Color(0, 0, 1, 1)
	await get_tree().create_timer(0.6).timeout
	print("%s|p09-runtime-blue|%s" % [TAG, _pixels()])
	c10.queue_free()
	await get_tree().create_timer(0.6).timeout
	print("%s|p10-runtime-removed|%s" % [TAG, _pixels()])

	print("%s|PROBE_DONE" % TAG)
	get_tree().quit()
