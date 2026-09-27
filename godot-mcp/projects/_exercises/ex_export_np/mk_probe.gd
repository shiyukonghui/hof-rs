extends SceneTree

# TASK-111: build the TileMap/GridMap probe assets for the H3 family.
#
# H3 was registered as structurally unreachable because no project carried a
# TileMapLayer / TileSet / MeshLibrary. `editor_set_tilemap_cell`'s own contract
# says a hand-authored (or project-shipped) TileSet with a TileSetAtlasSource is
# what is missing - it names that as the caller's responsibility, not a tool
# defect. This script is that caller: it writes
#   res://assets/tileset.tres  - TileSet + TileSetAtlasSource (2 tiles) + texture
#   res://assets/meshlib.tres  - MeshLibrary with one item
#   res://scenes/grid.tscn     - Node2D root + TileMapLayer carrying the TileSet
#
# Run headless, after `--import`, from cmd.exe.

func _initialize() -> void:
	var tex := load("res://assets/seed1.png") as Texture2D
	print("MKGRID tex=", tex)

	var ts := TileSet.new()
	ts.tile_size = Vector2i(8, 8)
	var src := TileSetAtlasSource.new()
	src.texture = tex
	src.texture_region_size = Vector2i(8, 8)
	src.create_tile(Vector2i(0, 0))
	src.create_tile(Vector2i(1, 0))
	var sid := ts.add_source(src)
	var tsave := ResourceSaver.save(ts, "res://assets/tileset.tres")
	print("MKGRID tileset sources=", ts.get_source_count(), " sid=", sid,
		" tiles=", src.get_tiles_count(), " save_err=", tsave)

	var lib := MeshLibrary.new()
	lib.create_item(0)
	lib.set_item_name(0, "cube")
	lib.set_item_mesh(0, BoxMesh.new())
	var ls := ResourceSaver.save(lib, "res://assets/meshlib.tres")
	print("MKGRID meshlib items=", lib.get_item_list().size(), " save_err=", ls)

	var root := Node2D.new()
	root.name = "GridRoot"
	var layer := TileMapLayer.new()
	layer.name = "Tiles"
	layer.tile_set = ts
	root.add_child(layer)
	layer.owner = root

	var packed := PackedScene.new()
	var perr := packed.pack(root)
	var serr := ResourceSaver.save(packed, "res://scenes/grid.tscn")
	print("MKGRID grid pack_err=", perr, " save_err=", serr)
	quit()
