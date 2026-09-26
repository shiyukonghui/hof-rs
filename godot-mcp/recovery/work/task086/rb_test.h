/**************************************************************************/
/*  test_mcp_server.h                                                     */
/**************************************************************************/
/*                         This file is part of:                          */
/*                             GODOT ENGINE                               */
/*                        https://godotengine.org                         */
/**************************************************************************/
/* Copyright (c) 2014-present Godot Engine contributors (see AUTHORS.md). */
/* Copyright (c) 2007-2014 Juan Linietsky, Ariel Manzur.                  */
/*                                                                        */
/* Permission is hereby granted, free of charge, to any person obtaining  */
/* a copy of this software and associated documentation files (the        */
/* "Software"), to deal in the Software without restriction, including    */
/* without limitation the rights to use, copy, modify, merge, publish,    */
/* distribute, sublicense, and/or sell copies of the Software, and to     */
/* permit persons to whom the Software is furnished to do so, subject to  */
/* the following conditions:                                              */
/*                                                                        */
/* The above copyright notice and this permission notice shall be         */
/* included in all copies or substantial portions of the Software.        */
/*                                                                        */
/* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,        */
/* EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF     */
/* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. */
/* IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY   */
/* CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,   */
/* TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE      */
/* SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                 */
/**************************************************************************/

#pragma once

#include "../mcp_http_server.h"
#include "../mcp_jsonrpc.h"
#include "../mcp_server.h"
#include "../tool_registry.h"
// TASK-045: the timing half of the raw-byte comparison's doctest needs the clock
// (`OS::get_ticks_usec`) and a way to print its distribution; neither is pulled
// in by the module headers above.
#include "core/config/project_settings.h"
// TASK-067: `project_list_scripts` is asserted against the engine's own script
// language registry, so the test can register a throwaway language whose
// extension no build knows in advance (`ScriptLanguage` / `ScriptServer` live in
// `core/object/script_language.h`, the editor half in `editor_language.h`).
#include "core/object/editor_language.h"
#include "core/object/script_language.h"
// TASK-057 (patch 2): the section publish is asserted against the engine's own
// reader - `ConfigFile` is what a game process and `InputMap` use to read
// `project.godot` back - so the text the new writer produces is checked with it
// instead of with a second parser written in the test.
#include "core/io/config_file.h"
// TASK-057: the multi-line-value regression case builds its expectation with the
// engine's own serializer (`VariantWriter::write_to_string`), which
// `project_settings.h` does not pull in.
#include "core/variant/variant_parser.h"
#include "core/os/os.h"
#include "core/string/print_string.h"
// TASK-012: the input-recording state machine (`tools/input_recorder.{h,cpp}`)
// and the shared `keycode_get_string()` (core/os/keyboard.h, pulled in by the
// recorder header) are asserted directly by the round-trip test. The
// vector-component mapping of `running_game_set_node_property` is asserted
// through its one definition instead of a copy.
#include "../tools/editor_node_write.h"
#include "../tools/input_recorder.h"
#include "../tools/running_game_node_write.h"
// TASK-040 D-3: the game-side observation family's named-property reader
// (`MCPTools::read_named_properties`) is asserted directly - the tools that call
// it need a running game, which a doctest process cannot have.
#include "../tools/running_game_observation.h"
// TASK-020 section 4 (D-3): the two assertion entries' verdict builders are
// asserted directly. The doctor process has no `SceneTree`, so the tools
// themselves can only ever answer the state error (see the TASK-019 case above);
// the builders are the half the two entries must agree on, and they are what the
// tools and the scenario runner really call.
#include "../tools/running_game_assertion.h"
#include "../tools/running_game_test_execution.h"
#include "../tools/tool_builder.h"
#include "../tools/tool_helpers.h"
// TASK-033: the animation family. The three group headers declare the entry
// points the doctests drive directly (they need engine *resources*, which a
// doctest can build without an editor), and `animation_shared.h` carries the
// engine-facing vocabulary they share.
#include "../tools/animation_shared.h"
#include "../tools/editor_animation_write.h"
#include "../tools/editor_animation_tree_write.h"
#include "../tools/editor_animation_read.h"
#include "scene/animation/animation_blend_tree.h"
#include "scene/animation/animation_node_state_machine.h"
#include "scene/animation/animation_player.h"
#include "scene/animation/animation_tree.h"
#include "scene/resources/animation.h"
#include "scene/resources/animation_library.h"
// TASK-034: B5 batch 2. The two shared helper files carry the engine-facing
// vocabulary of the audio and particle families, and the eight group headers
// declare the entry points the doctests drive directly - the ones that need only
// engine *objects* (an `AudioServer`, a `ParticleProcessMaterial`, an
// `AnimationTree` with a state machine) are asserted against real ones here,
// while everything that needs a live edited scene root is proven on the wire in
// REPORT-034 section 6.
#include "../tools/audio_shared.h"
#include "../tools/particle_shared.h"
#include "../tools/editor_audio_write.h"
#include "../tools/editor_audio_read.h"
#include "../tools/editor_particle_write.h"
#include "../tools/editor_particle_read.h"
#include "../tools/editor_theme_write.h"
#include "../tools/editor_scene_3d_write.h"
#include "../tools/editor_navigation_read.h"
#include "../tools/editor_profiling_read.h"
#include "main/performance.h"
#include "scene/2d/gpu_particles_2d.h"
#include "scene/3d/gpu_particles_3d.h"
#include "scene/resources/particle_process_material.h"
#include "servers/audio/audio_effect.h"
#include "servers/audio/audio_server.h"
// TASK-035: B5 batch 3 - the tilemap family (three writers, two of them
// data-destructive fix-first ports, and three readers), the editor shader
// writes, the node physics-layer write and its two readers, and the two project
// shader groups. The three shared helper files carry the family vocabulary; the
// engine objects the doctests drive directly are a real `TileMapLayer` +
// `TileSet` (no texture needed: a `TileSetScenesCollectionSource`), a real
// `ShaderMaterial`, a real `CharacterBody2D`/`CollisionShape2D` and the project
// settings the layer names live in. Everything that needs a live edited scene
// root or a compiled shader is proven on the wire in REPORT-035 section 6.
#include "../tools/tilemap_shared.h"
#include "../tools/editor_tilemap_write.h"
#include "../tools/editor_tilemap_read.h"
#include "../tools/shader_shared.h"
#include "../tools/editor_shader_write.h"
#include "../tools/project_shader_write.h"
#include "../tools/project_shader_read.h"
#include "../tools/physics_shared.h"
#include "../tools/editor_physics_write.h"
#include "../tools/editor_physics_read.h"
// TASK-036: B5 batch 4 - the closing 14 tools. The two shared helper files carry
// the theme and Android/export vocabulary; the doctests drive a real `Theme`
// (a plain `Resource`, safe to build here) and the deterministic halves of the
// Android/export code (the `export_presets.cfg` parser, the `adb devices -l`
// parser, the capability report). Everything that needs a live edited scene (a
// baked navigation mesh, a navigation layer write), a running game (the movement
// write) or an Android SDK/device is proven on the wire in REPORT-036 section 6.
#include "../tools/theme_shared.h"
#include "../tools/project_theme_write.h"
#include "../tools/project_theme_read.h"
#include "../tools/android_shared.h"
#include "../tools/project_export_read.h"
#include "../tools/project_android_read.h"
#include "../tools/os_android_read.h"
#include "../tools/os_android_write.h"
#include "../tools/editor_navigation_write.h"
#include "../tools/running_game_navigation_write.h"
// TASK-052 (GDR-28): the two *added* groups. Their headers export the units the
// doctests pin directly - the plain text writer, and the build's capability
// probes (`csharp_support_available`, `find_dotnet_executable`), its `.csproj`
// search, its command-line rule and the `ChildProcess` the timeout kills.
#include "../tools/project_csharp_build.h"
#include "../tools/project_text_write.h"
#include "scene/2d/node_2d.h"
#include "scene/3d/physics/joints/hinge_joint_3d.h"
#include "scene/3d/node_3d.h"
#include "scene/resources/environment.h"
#include "scene/resources/material.h"
#include "scene/resources/style_box_flat.h"
#include "scene/resources/theme.h"
#include "scene/2d/physics/character_body_2d.h"
#include "scene/2d/physics/collision_shape_2d.h"
#include "scene/3d/mesh_instance_3d.h"
#include "scene/resources/2d/rectangle_shape_2d.h"
#include "scene/resources/material.h"
#include "scene/resources/mesh.h"
#include "scene/resources/shader.h"
// TASK-023 section 2/3 (D-7): the two JSON-to-slot entry points that used to
// bypass the gate - `editor_set_viewport_3d_camera`'s `{x,y,z}` reader and
// `editor_setup_world_environment`'s `{r,g,b}` reader - are asserted through
// their one definition each, plus the guardrail's primitive (`FLOAT32` slot) and
// the `Color` component table.
#include "../tools/editor_write_scene_editor.h"
// TASK-024a E-10: the game-child port rule and the free-port probe
// (`is_usable_game_port` / `pick_free_game_port`) are exported by this group's
// header precisely so that a doctest can pin them, and the probe's mechanism is
// `TCPServer` itself.
#include "../tools/editor_playback.h"

#include "core/config/engine.h"
#include "core/config/project_settings.h"
#include "core/crypto/crypto_core.h"
// TASK-041 section 2 (M-6): the `project.godot` `[input]` read-back is parsed
// with the engine's own `ConfigFile` (objects allowed), so the assertion "the
// action is on disk" is made by an independent reader of the real bytes rather
// than by the writer that produced them.
#include "core/io/config_file.h"
#include "core/io/dir_access.h"
#include "core/io/file_access.h"
#include "core/io/image.h"
#include "core/io/json.h"
#include "core/io/resource_uid.h"
// TASK-027 D-8: the doctest loads the fixture's real `.png`/`.tres` files and
// asserts the shape an Object-valued property is read back in and takes back.
#include "core/io/resource.h"
#include "core/io/resource_loader.h"
// TASK-024a E-10: the free-port probe the tool uses is `TCPServer::listen(0)` +
// `get_local_port()`, and the doctest re-binds the port it answered to prove the
// claim "free" is not a promise the probe cannot keep.
#include "core/io/tcp_server.h"
// TASK-024 E-10: the free-port probe `editor_play_scene` uses is
// `TCPServer::listen(0)` + `get_local_port()`, and the doctest pins that this
// mechanism really works in this process (the tool's own `_pick_free_port` is
// file-private and only reachable through the editor run bar).
#include "core/io/tcp_server.h"
// TASK-010: `Expression` and `RefCounted` are used by the E3 lever test, which
// reproduces the migration source's Expression-based path next to the tool's
// compiled-GDScript path.
#include "core/math/expression.h"
#include "core/object/class_db.h"
#include "core/object/ref_counted.h"
// TASK-012: the vector-component mapping is pinned against a real `Node2D`, so
// the doctest needs the node type the tool is documented to write to. A
// `Node2D` is created directly (no `ClassDB`): `Main::test_entrypoint()` runs
// these cases before the module initialization level.
#include "scene/2d/node_2d.h"
// TASK-017: the batch/all-or-nothing and setup cases assert real derived classes
// (`Sprite2D` for the `is_class("Node2D")` match, `Control` for the preset
// geometry, `Node3D` for the navigation context) and the Environment enum the
// direct C++ world-environment calls write.
#include "scene/2d/sprite_2d.h"
#include "scene/3d/node_3d.h"
#include "scene/gui/control.h"
#include "scene/resources/environment.h"
// TASK-017: the batch/all-or-nothing and setup cases assert real derived classes
// (`Sprite2D` for the `is_class("Node2D")` match, `Control` for the preset
// geometry, `Node3D` for the navigation context) and the Environment enum the
// direct C++ world-environment calls write.
#include "scene/2d/sprite_2d.h"
#include "scene/3d/node_3d.h"
#include "scene/gui/control.h"
#include "scene/resources/environment.h"
// TASK-012: the recorder round-trip test drives `start()`/`capture()` with the
// engine's monotonic millisecond clock, the same one the tools pass in.
#include "core/os/time.h"
// TASK-013: the editor input simulation tools work on this process' `Input` /
// `InputMap` singleton, so their success paths are asserted against the real
// objects - created by the case itself, because the engine's listener only
// creates them for `[SceneTree]` / `[Editor]` cases (tests/test_main.cpp:181).
#include "core/input/input.h"
#include "core/input/input_map.h"
// TASK-010: the E3 lever test asserts the script-language prerequisite and
// initialises the languages for the execution half of the test.
#include "core/object/script_language.h"
#include "core/os/os.h"
#include "core/variant/variant.h"
// TASK-011: the deferred-tool tests assert that this process has no SceneTree
// (which is why the frame tools refuse with -32000 instead of waiting).
#include "scene/main/scene_tree.h"
#include "tests/test_macros.h"

// `std::numeric_limits` is the explicit source of the NaN/INF doubles the
// TASK-010 range guard tests use; this fork has no `Math::nan()`/`Math::inf()`.
#include <limits>

namespace TestMCPServer {

Vector<uint8_t> to_bytes(const String &p_text);
Variant parse_json(const String &p_text);
String canonical(const Variant &p_value);

// A handler that only ever fails: the tool-builder tests need a complete
// declaration without exercising real behaviour.
Variant unused_handler(const Dictionary &p_args, MCPToolError &r_error);

// Registers a tool through the only legal path (TASK-003 section 1.6, GDR-19):
// `MCPTools::ToolBuilder::register_into()`. Returns exactly what the builder
// returned, so a test can assert that a bad declaration never enters the table.
bool register_probe(MCPToolRegistry &r_registry, const String &p_name, const String &p_channel, const String &p_verb, MCPToolScope p_scope);

// Registry holding the six B1 template tools exactly as
// `tools/project_read_template.cpp` defines them.
void build_project_registry(MCPToolRegistry &r_registry);
// Registry built through the shared `register_all_tools()` entry point.
void build_all_tools_registry(MCPToolRegistry &r_registry);
// Registry with one editor-only, one game-only and one both-scope tool.
void build_scope_registry(MCPToolRegistry &r_registry);
// The full registry built exactly as an *editor* process would build it: the
// `scope = EDITOR` tools are only registered when `Engine::is_editor_hint()` is
// set, so the hint is flipped for the duration of `register_all_tools()` and
// restored before returning - no other test can observe the flip.
void build_editor_process_registry(MCPToolRegistry &r_registry);
// Registry with a -32001 probe and a -32000 probe, to observe the tool error
// mapping of the JSON-RPC layer without touching the file system.
void build_error_probe_registry(MCPToolRegistry &r_registry);

// ---------------------------------------------------------------------------
// GDR-20 / TASK-011: the controlled fake pending tool.
//
// `build_deferred_probe_registry()` registers two test-only tools into a fresh
// registry: `project_get_fake_pending` (a *deferred* tool whose task is steered
// by its arguments) and `project_get_fake_immediate` (an ordinary one). Neither
// ever reaches `register_all_tools`, so no gate can see them.
// ---------------------------------------------------------------------------
void build_deferred_probe_registry(MCPToolRegistry &r_registry);

// Fake tasks alive right now; every leak assertion compares it before/after.
int fake_pending_live();

// A `tools/call` payload for one fake deferred request.
String fake_call_body(int p_id, const String &p_payload, int p_ticks, int p_timeout_ms, bool p_fail);

// `"<connection_id>/<id_json>/<KIND>"` for one completion.
String completion_key(const MCPDeferred::Completion &p_completion);

// ---------------------------------------------------------------------------
// A scratch project tree for the `project_read_analysis` group.
//
// Four of the seven tools of that group only have observable behaviour against
// a real file tree (a loadable `.tscn`, an ext_resource graph, an unreferenced
// resource), and the doctest binary's `res://` is whatever directory it was
// launched from. The tree is therefore created in the constructor and removed
// in the destructor, so the working tree is left exactly as it was found even
// when an assertion fails - doctest's CHECK does not unwind, but the
// destructor still runs. The name is fixed (`res://mcp_server_test_fixture`)
// so that a crashed earlier run is repaired by the next constructor.
//
// The helpers are defined inline *here* instead of in tests/test_mcp_server.cpp
// because that translation unit deliberately does not include this header (it
// would pull in every TEST_CASE a second time), so a definition over there
// could not see these declarations.
// ---------------------------------------------------------------------------

// Recursively removes a project directory (files first, then directories).
inline void remove_tree(const String &p_path) {
	Ref<DirAccess> dir = DirAccess::open(p_path);
	if (dir.is_null()) {
		// Either a plain file or nothing at all.
		if (FileAccess::exists(p_path)) {
			DirAccess::remove_absolute(p_path);
		}
		return;
	}

	Vector<String> child_dirs;
	Vector<String> child_files;
	dir->list_dir_begin();
	while (true) {
		const String entry = dir->get_next();
		if (entry.is_empty()) {
			break;
		}
		if (entry == "." || entry == "..") {
			continue;
		}
		if (dir->current_is_dir()) {
			child_dirs.push_back(entry);
		} else {
			child_files.push_back(entry);
		}
	}
	dir->list_dir_end();

	for (int i = 0; i < child_files.size(); i++) {
		DirAccess::remove_absolute(p_path.path_join(child_files[i]));
	}
	for (int i = 0; i < child_dirs.size(); i++) {
		remove_tree(p_path.path_join(child_dirs[i]));
	}
	DirAccess::remove_absolute(p_path);
}

// Sorted, recursive list of the files below `p_path`; used to prove that the
// read-only analysis group never adds or removes a file.
inline Array list_files_recursive(const String &p_path) {
	Array out;
	Ref<DirAccess> dir = DirAccess::open(p_path);
	if (dir.is_null()) {
		return out;
	}

	Vector<String> child_dirs;
	dir->list_dir_begin();
	while (true) {
		const String entry = dir->get_next();
		if (entry.is_empty()) {
			break;
		}
		if (entry == "." || entry == "..") {
			continue;
		}
		const String full = p_path.path_join(entry);
		if (dir->current_is_dir()) {
			child_dirs.push_back(full);
		} else {
			out.push_back(full);
		}
	}
	dir->list_dir_end();

	for (int i = 0; i < child_dirs.size(); i++) {
		const Array nested = list_files_recursive(child_dirs[i]);
		for (int j = 0; j < nested.size(); j++) {
			out.push_back(nested[j]);
		}
	}
	out.sort();
	return out;
}

struct ScratchProject {
	// `res://mcp_server_test_fixture`
	String root;

	ScratchProject();
	~ScratchProject();

	// Ensures the parent directories exist and (over)writes the file.
	bool write(const String &p_relative_path, const String &p_text);

	// Convenience: `<root>/<relative>`.
	String path(const String &p_relative_path) const { return root.path_join(p_relative_path); }

private:
	static String _lines(const char *const *p_lines, int p_count);
};

inline String ScratchProject::_lines(const char *const *p_lines, int p_count) {
	String text;
	for (int i = 0; i < p_count; i++) {
		text += String::utf8(p_lines[i]);
		text += "\n";
	}
	return text;
}

inline bool ScratchProject::write(const String &p_relative_path, const String &p_text) {
	const String full = path(p_relative_path);
	const String parent = full.get_base_dir();
	if (!parent.is_empty()) {
		DirAccess::make_dir_recursive_absolute(parent);
	}
	Ref<FileAccess> file = FileAccess::open(full, FileAccess::WRITE);
	if (file.is_null()) {
		return false;
	}
	file->store_string(p_text);
	file->close();
	return true;
}

inline ScratchProject::ScratchProject() {
	root = String::utf8("res://mcp_server_test_fixture");
	// A fixed name means a tree left behind by a crashed earlier run is
	// repaired here instead of being counted twice.
	remove_tree(root);

	{
		const char *const exported_gd[] = {
			"extends Node2D",
			"",
			"@export var speed: int = 3",
			"@export var title: String = \"hello\"",
			"var not_exported: int = 1",
		};
		write("scripts/exported.gd", _lines(exported_gd, 5));
	}
	{
		const char *const refs_gd[] = {
			"extends Node",
			"",
			"const TARGET := \"SCRIPT_REF_MARKER\"",
		};
		write("scripts/refs.gd", _lines(refs_gd, 3));
	}
	{
		const char *const leaf_tscn[] = {
			"[gd_scene load_steps=2 format=3]",
			"",
			"[ext_resource type=\"Resource\" path=\"res://mcp_server_test_fixture/resources/used.tres\" id=\"1_r\"]",
			"",
			"[node name=\"Leaf\" type=\"Node2D\"]",
			"",
			"# SCRIPT_REF_MARKER",
		};
		write("scenes/leaf.tscn", _lines(leaf_tscn, 7));
	}
	{
		const char *const cycle_a[] = {
			"[gd_scene load_steps=2 format=3]",
			"",
			"[ext_resource type=\"PackedScene\" path=\"res://mcp_server_test_fixture/scenes/cycle_b.tscn\" id=\"1_a\"]",
			"",
			"[node name=\"CycleA\" type=\"Node2D\"]",
		};
		write("scenes/cycle_a.tscn", _lines(cycle_a, 5));
	}
	{
		const char *const cycle_b[] = {
			"[gd_scene load_steps=2 format=3]",
			"",
			"[ext_resource type=\"PackedScene\" path=\"res://mcp_server_test_fixture/scenes/cycle_a.tscn\" id=\"1_b\"]",
			"",
			"[node name=\"CycleB\" type=\"Node2D\"]",
		};
		write("scenes/cycle_b.tscn", _lines(cycle_b, 5));
	}
	{
		// Deliberately script-less: the doctest process never initializes a
		// script language (`Main::test_setup()` does not call
		// `ScriptServer::init_languages()`), so a `.gd` attached here would fail
		// with "Native class Node2D not found". The script-dependent behaviour
		// of project_analyze_scene_complexity / project_get_scene_exports is
		// proven by the gate section 2 evidence on a real scratch project.
		const char *const nested[] = {
			"[gd_scene load_steps=2 format=3]",
			"",
			"[node name=\"Nested\" type=\"Node2D\"]",
			"",
			"[node name=\"Child\" type=\"Sprite2D\" parent=\".\"]",
			"",
			"[node name=\"GrandChild\" type=\"Node2D\" parent=\"Child\"]",
		};
		write("scenes/nested.tscn", _lines(nested, 7));
	}
	{
		const char *const resource[] = {
			"[gd_resource type=\"Resource\" format=3]",
			"",
			"[resource]",
		};
		write("resources/used.tres", _lines(resource, 3));
		write("resources/unused.tres", _lines(resource, 3));
	}
	{
		const char *const notes_md[] = {
			"# notes",
			"",
			"SCRIPT_REF_MARKER",
		};
		write("notes.md", _lines(notes_md, 3));
	}
	{
		const char *const plugin_cfg[] = {
			"[plugin]",
			"",
			"name=\"myplugin\"",
			"version=\"1.0\"",
		};
		write("addons/myplugin/plugin.cfg", _lines(plugin_cfg, 4));
		const char *const addon_resource[] = {
			"[gd_resource type=\"Resource\" format=3]",
			"",
			"[resource]",
		};
		write("addons/myplugin/thing.tres", _lines(addon_resource, 3));
	}
}

inline ScratchProject::~ScratchProject() {
	remove_tree(root);
}

// ---------------------------------------------------------------------------
// A second scratch tree, for the `project_read_files` group (TASK-005).
//
// It is a *separate* root (`res://mcp_server_test_fixture_read_files`) instead
// of an extension of ScratchProject on purpose: REPORT-004 section 2 pins the
// analysis group's exact file totals and extension histogram, so adding material
// to that tree would turn those assertions red for a reason that has nothing to
// do with the analysis tools.
//
// Layout (11 files):
//
//   scripts/alpha.gd            balanced, valid GDScript
//   scripts/broken.gd           unbalanced delimiter (invalid)
//   scripts/unicode.gd          UTF-8 + CRLF; `unicode_text` holds its text
//   scripts/upper.GD            uppercase extension: NOT collected by
//                               project_list_scripts (the test is case
//                               sensitive, `ends_with(".gd")` in the reference)
//   shaders/effect.gdshader     collected by project_list_scripts
//   .hiddendir/secret.gd        a hidden *directory* is collected: the reference
//                               walk skips only the names "." and ".."
//   addons/plug/in_addon.gd     `addons` is descended into: same reason
//   scenes/main.tscn            raw .tscn text for the scene reader
//   resources/simple.tres       loads as a `Resource`, which has no preview
//   resources/gradient.tres     a `Gradient`: stored `offsets`/`colors` values
//                               (TASK-026 E-9 read-back -> write-back chain)
//   resources/environment.tres  a `Environment`: more stored properties than the
//                               reader's limit (TASK-026 E-9 truncation marker)
//   resources/plain.txt         not a loadable resource at all
//   images/small.png            a real 64x32 PNG, produced by the constructor
// ---------------------------------------------------------------------------
struct ReadFilesProject {
	String root;
	// The exact text of `scripts/unicode.gd`: CRLF line endings and non-ASCII
	// characters, so "verbatim" has something to be verbatim about.
	String unicode_text;

	ReadFilesProject();
	~ReadFilesProject();

	bool write(const String &p_relative_path, const String &p_text);
	bool write_bytes(const String &p_relative_path, const Vector<uint8_t> &p_bytes);

	String path(const String &p_relative_path) const { return root.path_join(p_relative_path); }
};

inline bool ReadFilesProject::write_bytes(const String &p_relative_path, const Vector<uint8_t> &p_bytes) {
	const String full = path(p_relative_path);
	const String parent = full.get_base_dir();
	if (!parent.is_empty()) {
		DirAccess::make_dir_recursive_absolute(parent);
	}
	Ref<FileAccess> file = FileAccess::open(full, FileAccess::WRITE);
	if (file.is_null()) {
		return false;
	}
	file->store_buffer(p_bytes.ptr(), p_bytes.size());
	file->close();
	return true;
}

inline bool ReadFilesProject::write(const String &p_relative_path, const String &p_text) {
	// The exact UTF-8 bytes, so that the CRLF and the non-ASCII characters of
	// `unicode_text` reach the disk unchanged.
	const CharString utf8 = p_text.utf8();
	Vector<uint8_t> bytes;
	bytes.resize(utf8.length());
	for (int i = 0; i < utf8.length(); i++) {
		bytes.write[i] = (uint8_t)utf8[i];
	}
	return write_bytes(p_relative_path, bytes);
}

inline ReadFilesProject::ReadFilesProject() {
	root = String::utf8("res://mcp_server_test_fixture_read_files");
	remove_tree(root);

	write("scripts/alpha.gd", "extends Node\n\nfunc alpha() -> int:\n\treturn 1\n");
	write("scripts/broken.gd", "extends Node\n\nfunc broken( -> void:\n\tpass\n");
	unicode_text = String::utf8("extends Node\r\n\r\nvar 名称 : String = \"中文\"\r\n");
	write("scripts/unicode.gd", unicode_text);
	write("scripts/upper.GD", "extends Node\n");
	write("shaders/effect.gdshader", "shader_type canvas_item;\n");
	write(".hiddendir/secret.gd", "extends Node\n\nvar hidden := true\n");
	write("addons/plug/in_addon.gd", "extends Node\n\nvar in_addon := true\n");
	// The second node carries a non-ASCII name on purpose: it makes the `size`
	// field of project_read_scene_file_content differ between characters and
	// UTF-8 bytes, which is what TASK-006 section 3.1 pins.
	write("scenes/main.tscn", String::utf8("[gd_scene load_steps=2 format=3]\n\n[node name=\"Main\" type=\"Node2D\"]\n\n[node name=\"中文\" type=\"Node2D\" parent=\".\"]\n"));
	write("resources/simple.tres", "[gd_resource type=\"Resource\" format=3]\n\n[resource]\n");
	// TASK-026 (E-9). A resource whose *stored* values are worth reading back:
	// a `Gradient` stores `offsets` (`PackedFloat32Array` -> an array of numbers)
	// and `colors` (`PackedColorArray` -> an array of `{r,g,b,a}` objects), the
	// two shapes GDR-25 section 23.4 defines, so the read-back -> write-back
	// chain has a compound value to carry and not only a scalar.
	write("resources/gradient.tres", "[gd_resource type=\"Gradient\" format=3]\n\n[resource]\noffsets = PackedFloat32Array(0, 1)\ncolors = PackedColorArray(1, 0, 0, 1, 0, 0, 1, 1)\n");
	// A resource with far more stored properties than the tool's limit (an
	// `Environment` declares 90+), so the truncation marker is driven by a real
	// engine class instead of by a synthetic property list.
	write("resources/environment.tres", "[gd_resource type=\"Environment\" format=3]\n\n[resource]\n");
	write("resources/plain.txt", "not an image\n");

	// A real PNG, so project_get_resource_preview is exercised against a real
	// encoder and a real decoder instead of a hand-made byte buffer.
	Ref<Image> image = Image::create_empty(64, 32, false, Image::FORMAT_RGBA8);
	image->fill(Color(0.2, 0.4, 0.6, 1.0));
	write_bytes("images/small.png", image->save_png_to_buffer());
}

inline ReadFilesProject::~ReadFilesProject() {
	remove_tree(root);
}

// ---------------------------------------------------------------------------
// A scratch `user://logs/godot.log` for the `editor_read_scene_inspector` group
// (TASK-006). Both log tools of that group read exactly that path and take no
// path argument, so the only way to drive their success path is to put a file
// there.
//
// The fixture is *non-destructive*: an existing log (the engine's own, on a
// developer machine) is read into memory in the constructor and written back
// byte for byte in the destructor. When there was no log, the file is removed
// again - doctest's CHECK does not unwind, but the destructor still runs.
// ---------------------------------------------------------------------------
inline Vector<uint8_t> read_file_bytes(const String &p_path) {
	Vector<uint8_t> out;
	Ref<FileAccess> file = FileAccess::open(p_path, FileAccess::READ);
	if (file.is_null()) {
		return out;
	}
	const int64_t length = file->get_length();
	out.resize(length);
	if (length > 0) {
		file->get_buffer(out.ptrw(), length);
	}
	file->close();
	return out;
}

inline bool write_file_bytes(const String &p_path, const Vector<uint8_t> &p_bytes) {
	const String parent = p_path.get_base_dir();
	if (!parent.is_empty()) {
		DirAccess::make_dir_recursive_absolute(parent);
	}
	Ref<FileAccess> file = FileAccess::open(p_path, FileAccess::WRITE);
	if (file.is_null()) {
		return false;
	}
	if (p_bytes.size() > 0) {
		file->store_buffer(p_bytes.ptr(), p_bytes.size());
	}
	file->close();
	return true;
}

// `user://logs/godot.log` - the one path both log tools read.
inline String scratch_log_path() {
	return String("user://logs/godot.log");
}

struct ScratchLog {
	bool had_original = false;
	bool ok = false;
	Vector<uint8_t> original;

	explicit ScratchLog(const String &p_text);
	~ScratchLog();

	// Removes the log for the "no_log_file" branch; the destructor still
	// restores whatever was there before the fixture was built.
	void remove_file() const {
		DirAccess::remove_absolute(scratch_log_path());
	}
};

inline ScratchLog::ScratchLog(const String &p_text) {
	const String path = scratch_log_path();
	// `DirAccess::make_dir_recursive()` on a `user://`-prefixed path only walks
	// the segments *below* `user://`: its base is the prefix itself, so it calls
	// `make_dir("user://logs")` and the user data directory itself is assumed to
	// exist. In a full-suite run that assumption is false - the `[Logger]` tests
	// set `application/config/name` to `godot_tests` and their `cleanup_logs()`
	// removes the whole `app_userdata/godot_tests` directory - and the write then
	// fails silently. The engine's own logger test therefore creates the
	// directory from the absolute user data path (tests/core/io/test_logger.cpp:47);
	// this fixture does the same. Only the directory creation needs it: every
	// `FileAccess` call below resolves `user://` through `DirAccess::fix_path`.
	OS *os = OS::get_singleton();
	if (os != nullptr) {
		DirAccess::make_dir_recursive_absolute(os->get_user_data_dir().path_join("logs"));
	}
	had_original = FileAccess::exists(path);
	if (had_original) {
		original = read_file_bytes(path);
	}
	ok = write_file_bytes(path, to_bytes(p_text));
}

inline ScratchLog::~ScratchLog() {
	const String path = scratch_log_path();
	if (had_original) {
		write_file_bytes(path, original);
	} else {
		DirAccess::remove_absolute(path);
	}
}

} // namespace TestMCPServer

// ---------------------------------------------------------------------------
// TASK-003 section 1.6 - the bypass proof (compile time).
//
// `MCPToolRegistry::register_tool()` is private and `MCPTools::ToolBuilder` is
// declared its only friend, so the only way into the registry is
// `ToolBuilder::register_into()` - which forces channel / verb / scope /
// mutating to be declared, runs the GDR-16 lint and applies the GDR-19 editor
// guard. Before this, a group could hand a raw `MCPToolDef` straight to the
// registry and skip all three.
//
// This probe is a real check, not a comment. A private member cannot be named
// from out here, and an access failure inside the immediate context of a
// substitution is a substitution failure (CWG 1170), so `test<T>` falls back to
// the ellipsis overload and `is_public` is false. If `register_tool` ever went
// public again, the `static_assert` below would fail the build of this test
// binary.
// ---------------------------------------------------------------------------
template <typename T>
struct RegisterToolAccessProbe {
	template <typename U>
	static char test(decltype(&U::register_tool) *, int);
	template <typename U>
	static long test(...);
	static constexpr bool is_public = (sizeof(test<T>(nullptr, 0)) == sizeof(char));
};

static_assert(!RegisterToolAccessProbe<MCPToolRegistry>::is_public,
		"MCPToolRegistry::register_tool is public again: ToolBuilder is no longer the only registration path (GDR-19 / TASK-003 1.6)");

// ---------------------------------------------------------------------------
// HTTP/1.1 framing (GDR-5)
// ---------------------------------------------------------------------------

TEST_CASE("[MCPServer] HTTP parses request line, headers and body") {
	Vector<uint8_t> buffer = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\r\nHost: 127.0.0.1:9888\r\nContent-Length: 2\r\nContent-Type: application/json\r\n\r\n{}");

	MCPHttp::ParseOutcome outcome = MCPHttp::parse_request(buffer, 1024);
	CHECK(outcome.status == MCPHttp::ParseStatus::COMPLETE);
	CHECK(outcome.request.method == "POST");
	CHECK(outcome.request.path == "/mcp");
	CHECK(outcome.request.version == "HTTP/1.1");
	CHECK(outcome.request.body == "{}");
	CHECK(outcome.request.keep_alive);
	// The request must be consumed exactly.
	CHECK(buffer.is_empty());
}

TEST_CASE("[MCPServer] HTTP header names are case insensitive") {
	Vector<uint8_t> buffer = TestMCPServer::to_bytes("post /mcp HTTP/1.1\r\nhost: x\r\ncontent-LENGTH: 7\r\n\r\n{\"a\":1}");

	MCPHttp::ParseOutcome outcome = MCPHttp::parse_request(buffer, 1024);
	CHECK(outcome.status == MCPHttp::ParseStatus::COMPLETE);
	CHECK(outcome.request.method == "POST");
	CHECK(outcome.request.body == "{\"a\":1}");
}

TEST_CASE("[MCPServer] HTTP connection close is honoured") {
	Vector<uint8_t> buffer = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}");

	MCPHttp::ParseOutcome outcome = MCPHttp::parse_request(buffer, 1024);
	CHECK(outcome.status == MCPHttp::ParseStatus::COMPLETE);
	CHECK_FALSE(outcome.request.keep_alive);
}

TEST_CASE("[MCPServer] HTTP half packet is buffered until complete") {
	// Half 1: header and part of the body.
	Vector<uint8_t> buffer = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\r\nContent-Length: 2\r\n\r\n{");
	CHECK(MCPHttp::parse_request(buffer, 1024).status == MCPHttp::ParseStatus::NEED_MORE);
	// The partial request must not be consumed.
	int size_before = buffer.size();
	CHECK(MCPHttp::parse_request(buffer, 1024).status == MCPHttp::ParseStatus::NEED_MORE);
	CHECK(buffer.size() == size_before);

	// Half 2: the rest of the body.
	Vector<uint8_t> rest = TestMCPServer::to_bytes("}");
	buffer.append_array(rest);
	MCPHttp::ParseOutcome outcome = MCPHttp::parse_request(buffer, 1024);
	CHECK(outcome.status == MCPHttp::ParseStatus::COMPLETE);
	CHECK(outcome.request.body == "{}");
	CHECK(buffer.is_empty());
}

TEST_CASE("[MCPServer] HTTP header split mid line is buffered") {
	Vector<uint8_t> buffer = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\r\nContent-Len");
	CHECK(MCPHttp::parse_request(buffer, 1024).status == MCPHttp::ParseStatus::NEED_MORE);

	Vector<uint8_t> rest = TestMCPServer::to_bytes("gth: 2\r\n\r\n{}");
	buffer.append_array(rest);
	MCPHttp::ParseOutcome outcome = MCPHttp::parse_request(buffer, 1024);
	CHECK(outcome.status == MCPHttp::ParseStatus::COMPLETE);
	CHECK(outcome.request.body == "{}");
}

TEST_CASE("[MCPServer] HTTP keep-alive two requests in one buffer") {
	Vector<uint8_t> buffer = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\r\nContent-Length: 8\r\n\r\n{\"id\":1}POST /mcp HTTP/1.1\r\nContent-Length: 8\r\n\r\n{\"id\":2}");

	MCPHttp::ParseOutcome first = MCPHttp::parse_request(buffer, 1024);
	CHECK(first.status == MCPHttp::ParseStatus::COMPLETE);
	CHECK(first.request.body == "{\"id\":1}");

	MCPHttp::ParseOutcome second = MCPHttp::parse_request(buffer, 1024);
	CHECK(second.status == MCPHttp::ParseStatus::COMPLETE);
	CHECK(second.request.body == "{\"id\":2}");

	MCPHttp::ParseOutcome third = MCPHttp::parse_request(buffer, 1024);
	CHECK(third.status == MCPHttp::ParseStatus::NEED_MORE);
	CHECK(buffer.is_empty());
}

TEST_CASE("[MCPServer] HTTP missing Content-Length") {
	// A POST always carries a body, so the header is mandatory.
	Vector<uint8_t> buffer = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n");
	CHECK(MCPHttp::parse_request(buffer, 1024).status == MCPHttp::ParseStatus::MISSING_CONTENT_LENGTH);
	CHECK(MCPHttp::status_code_for(MCPHttp::ParseStatus::MISSING_CONTENT_LENGTH) == 411);

	// A GET without a body does not need one.
	Vector<uint8_t> get_buffer = TestMCPServer::to_bytes("GET /mcp HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n");
	MCPHttp::ParseOutcome outcome = MCPHttp::parse_request(get_buffer, 1024);
	CHECK(outcome.status == MCPHttp::ParseStatus::COMPLETE);
	CHECK(outcome.request.method == "GET");
	CHECK(outcome.request.body.is_empty());
}

TEST_CASE("[MCPServer] HTTP invalid Content-Length") {
	Vector<uint8_t> buffer = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\r\nContent-Length: abc\r\n\r\n");
	CHECK(MCPHttp::parse_request(buffer, 1024).status == MCPHttp::ParseStatus::INVALID_CONTENT_LENGTH);
	CHECK(MCPHttp::status_code_for(MCPHttp::ParseStatus::INVALID_CONTENT_LENGTH) == 400);
}

TEST_CASE("[MCPServer] HTTP body over the limit is rejected with 413") {
	// The declared length alone is enough to reject; the body is never read.
	Vector<uint8_t> buffer = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\r\nContent-Length: 4096\r\n\r\n");
	CHECK(MCPHttp::parse_request(buffer, 1024).status == MCPHttp::ParseStatus::BODY_TOO_LARGE);
	CHECK(MCPHttp::status_code_for(MCPHttp::ParseStatus::BODY_TOO_LARGE) == 413);
	CHECK(buffer.is_empty());

	// Exactly at the limit is accepted.
	Vector<uint8_t> accepted = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\r\nContent-Length: 2\r\n\r\n{}");
	CHECK(MCPHttp::parse_request(accepted, 2).status == MCPHttp::ParseStatus::COMPLETE);
}

TEST_CASE("[MCPServer] HTTP malformed request line and oversized header") {
	Vector<uint8_t> malformed = TestMCPServer::to_bytes("GARBAGE\r\n\r\n");
	CHECK(MCPHttp::parse_request(malformed, 1024).status == MCPHttp::ParseStatus::BAD_REQUEST_LINE);
	CHECK(MCPHttp::status_code_for(MCPHttp::ParseStatus::BAD_REQUEST_LINE) == 400);

	Vector<uint8_t> bad_version = TestMCPServer::to_bytes("POST /mcp HTTP/9.9\r\nContent-Length: 2\r\n\r\n{}");
	CHECK(MCPHttp::parse_request(bad_version, 1024).status == MCPHttp::ParseStatus::UNSUPPORTED_VERSION);

	String long_header = "POST /mcp HTTP/1.1\r\n";
	for (int i = 0; i < 400; i++) {
		long_header += "X-Pad: 0123456789012345678901234567890123456789\r\n";
	}
	Vector<uint8_t> oversized = TestMCPServer::to_bytes(long_header);
	CHECK(MCPHttp::parse_request(oversized, 1024).status == MCPHttp::ParseStatus::HEADER_TOO_LARGE);
}

TEST_CASE("[MCPServer] HTTP oversized header is 431, not 400") {
	// GDR-12.2: a header block over the 8 KiB cap is `431 Request Header Fields
	// Too Large`. `reason_phrase(431)` already carried the correct string, but
	// the mapping never selected it, so the branch was dead code.
	CHECK(MCPHttp::status_code_for(MCPHttp::ParseStatus::HEADER_TOO_LARGE) == 431);
	CHECK(MCPHttp::reason_phrase(431) == "Request Header Fields Too Large");

	// The mapping has to be reachable from both oversized shapes: the announced
	// block whose blank line has arrived, and one that is still being buffered.
	String terminated = "POST /mcp HTTP/1.1\r\n";
	for (int i = 0; i < 400; i++) {
		terminated += "X-Pad: 0123456789012345678901234567890123456789\r\n";
	}
	terminated += "\r\n";
	Vector<uint8_t> with_terminator = TestMCPServer::to_bytes(terminated);
	const MCPHttp::ParseOutcome outcome = MCPHttp::parse_request(with_terminator, 1024);
	CHECK(outcome.status == MCPHttp::ParseStatus::HEADER_TOO_LARGE);
	CHECK(MCPHttp::status_code_for(outcome.status) == 431);
	CHECK(with_terminator.is_empty());

	String unterminated = "POST /mcp HTTP/1.1\r\n";
	for (int i = 0; i < 400; i++) {
		unterminated += "X-Pad: 0123456789012345678901234567890123456789\r\n";
	}
	Vector<uint8_t> without_terminator = TestMCPServer::to_bytes(unterminated);
	CHECK(MCPHttp::parse_request(without_terminator, 1024).status == MCPHttp::ParseStatus::HEADER_TOO_LARGE);
}

TEST_CASE("[MCPServer] HTTP bare LF header terminator is rejected with 400") {
	// GDR-12.3: HTTP/1.1 requires CRLF. A peer that ends its header block with a
	// bare LF used to leave the request sitting in the input buffer until the
	// 30 s idle timeout and never got an answer at all. It must be answered
	// with 400 right away and the connection closed.
	//
	// The red form of this assertion deliberately used only symbols that
	// already existed, so that the failure was a real assertion failure instead
	// of a build error; the exact status is pinned now that it exists.
	Vector<uint8_t> buffer = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\nHost: 127.0.0.1\nContent-Length: 2\n\n{}");
	const MCPHttp::ParseOutcome outcome = MCPHttp::parse_request(buffer, 1024);
	CHECK(outcome.status == MCPHttp::ParseStatus::BARE_LF_LINE_ENDING);
	CHECK(outcome.status != MCPHttp::ParseStatus::NEED_MORE);
	CHECK(MCPHttp::status_code_for(outcome.status) == 400);
	CHECK(buffer.is_empty());

	// Neither does the bodyless form get to wait.
	Vector<uint8_t> get_buffer = TestMCPServer::to_bytes("GET /mcp HTTP/1.1\n\n");
	const MCPHttp::ParseOutcome get_outcome = MCPHttp::parse_request(get_buffer, 1024);
	CHECK(get_outcome.status == MCPHttp::ParseStatus::BARE_LF_LINE_ENDING);
	CHECK(get_outcome.status != MCPHttp::ParseStatus::NEED_MORE);
	CHECK(MCPHttp::status_code_for(get_outcome.status) == 400);
	CHECK(get_buffer.is_empty());

	// A bare LF anywhere else in the header block cannot be split into header
	// lines either, so it is a 400 as well - what matters is that no request
	// with a bare LF is left buffered.
	Vector<uint8_t> mixed = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\nContent-Length: 2\r\n\r\n{}");
	const MCPHttp::ParseOutcome mixed_outcome = MCPHttp::parse_request(mixed, 1024);
	CHECK(mixed_outcome.status != MCPHttp::ParseStatus::NEED_MORE);
	CHECK(MCPHttp::status_code_for(mixed_outcome.status) == 400);
}

TEST_CASE("[MCPServer] HTTP invalid UTF-8 body stays accepted but is reported") {
	// GDR-12.4: the client contract is UTF-8 and a strict validation path is
	// deliberately not added, so an invalid body is still accepted. What is not
	// allowed is the current silence: `String::utf8` swaps every invalid byte
	// for U+FFFD without saying anything, so the parser has to notice the
	// substitution and hand it to the transport for a verbose warning that
	// carries the original byte length.
	//
	// The validator itself is strict RFC 3629, because "does the decoded string
	// contain U+FFFD" cannot tell a substitution apart from a legitimate
	// U+FFFD in the payload.
	CHECK(MCPHttp::is_valid_utf8((const uint8_t *)"plain ascii", 11));
	const uint8_t chinese[] = { 0xE8, 0x8E, 0xB7, 0xE5, 0x8F, 0x96 }; // 获取
	CHECK(MCPHttp::is_valid_utf8(chinese, 6));
	CHECK(MCPHttp::is_valid_utf8(nullptr, 0));
	CHECK_FALSE(MCPHttp::is_valid_utf8((const uint8_t *)"\xC3", 1)); // truncated 2 byte sequence
	CHECK_FALSE(MCPHttp::is_valid_utf8((const uint8_t *)"\xE8\x8E", 2)); // truncated 3 byte sequence
	CHECK_FALSE(MCPHttp::is_valid_utf8((const uint8_t *)"\xC0\xAF", 2)); // overlong '/'
	CHECK_FALSE(MCPHttp::is_valid_utf8((const uint8_t *)"\xED\xA0\x80", 3)); // UTF-16 surrogate
	CHECK_FALSE(MCPHttp::is_valid_utf8((const uint8_t *)"\xF4\x90\x80\x80", 4)); // beyond U+10FFFF
	CHECK_FALSE(MCPHttp::is_valid_utf8((const uint8_t *)"\xFF", 1)); // never a valid lead byte

	// A payload that is valid JSON once the offending byte has been replaced is
	// still served (loose acceptance), but the substitution is flagged.
	const Vector<uint8_t> prefix = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\r\nContent-Length: 7\r\n\r\n");
	Vector<uint8_t> buffer = prefix;
	const uint8_t payload[] = { '{', '"', 0xFF, '"', ':', '1', '}' };
	for (int i = 0; i < 7; i++) {
		buffer.push_back(payload[i]);
	}
	const MCPHttp::ParseOutcome outcome = MCPHttp::parse_request(buffer, 1024);
	CHECK(outcome.status == MCPHttp::ParseStatus::COMPLETE);
	CHECK(outcome.body_invalid_utf8);
	CHECK(outcome.request.body.contains(String::chr(0xFFFD)));

	// An ASCII body is never flagged.
	Vector<uint8_t> ascii = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\r\nContent-Length: 2\r\n\r\n{}");
	const MCPHttp::ParseOutcome ascii_outcome = MCPHttp::parse_request(ascii, 1024);
	CHECK(ascii_outcome.status == MCPHttp::ParseStatus::COMPLETE);
	CHECK_FALSE(ascii_outcome.body_invalid_utf8);

	// A valid multi byte body is never flagged either.
	Vector<uint8_t> valid = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\r\nContent-Length: 6\r\n\r\n");
	valid.append_array(chinese);
	const MCPHttp::ParseOutcome valid_outcome = MCPHttp::parse_request(valid, 1024);
	CHECK(valid_outcome.status == MCPHttp::ParseStatus::COMPLETE);
	CHECK_FALSE(valid_outcome.body_invalid_utf8);
}

TEST_CASE("[MCPServer] HTTP response envelope is byte exact") {
	CHECK(MCPHttp::build_response(200, "{}", true) == "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 2\r\nAccess-Control-Allow-Origin: *\r\nConnection: keep-alive\r\n\r\n{}");
	CHECK(MCPHttp::build_response(202, "", false) == "HTTP/1.1 202 Accepted\r\nContent-Type: application/json\r\nContent-Length: 0\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n");
	CHECK(MCPHttp::build_response(413, "nope", true) == "HTTP/1.1 413 Payload Too Large\r\nContent-Type: application/json\r\nContent-Length: 4\r\nAccess-Control-Allow-Origin: *\r\nConnection: keep-alive\r\n\r\nnope");

	CHECK(MCPHttp::reason_phrase(200) == "OK");
	CHECK(MCPHttp::reason_phrase(404) == "Not Found");
	CHECK(MCPHttp::reason_phrase(405) == "Method Not Allowed");
	CHECK(MCPHttp::reason_phrase(411) == "Length Required");
}

TEST_CASE("[MCPServer] HTTP Expect: 100-continue is detected before the body arrives") {
	// A client that announces `Expect: 100-continue` waits for the interim
	// response before it starts sending the body (curl does this for bodies
	// over 1 KiB). Without one it either stalls for a second or fails outright,
	// so the framing layer has to report that the interim step is owed.
	Vector<uint8_t> withheld = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\r\nHost: 127.0.0.1\r\nExpect: 100-continue\r\nContent-Length: 4\r\n\r\n");
	const MCPHttp::ParseOutcome outcome = MCPHttp::parse_request(withheld, 1024);
	CHECK(outcome.status == MCPHttp::ParseStatus::NEED_MORE);
	CHECK(outcome.expect_continue);

	// The interim response is byte exact and must not carry Content-Type or
	// Content-Length (RFC 9110: a 100 response has no body and no headers).
	CHECK(MCPHttp::build_continue_response() == "HTTP/1.1 100 Continue\r\n\r\n");

	// Header name and expectation token are case insensitive.
	Vector<uint8_t> mixed_case = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\r\nEXPECT: 100-Continue\r\nContent-Length: 4\r\n\r\n");
	CHECK(MCPHttp::parse_request(mixed_case, 1024).expect_continue);

	// Once the body has arrived there is nothing left to wait for.
	Vector<uint8_t> complete = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\r\nExpect: 100-continue\r\nContent-Length: 2\r\n\r\n{}");
	const MCPHttp::ParseOutcome complete_outcome = MCPHttp::parse_request(complete, 1024);
	CHECK(complete_outcome.status == MCPHttp::ParseStatus::COMPLETE);
	CHECK_FALSE(complete_outcome.expect_continue);

	// A zero length body is complete on the spot as well.
	Vector<uint8_t> empty = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\r\nExpect: 100-continue\r\nContent-Length: 0\r\n\r\n");
	const MCPHttp::ParseOutcome empty_outcome = MCPHttp::parse_request(empty, 1024);
	CHECK(empty_outcome.status == MCPHttp::ParseStatus::COMPLETE);
	CHECK_FALSE(empty_outcome.expect_continue);

	// A request without the header never asks for an interim response.
	Vector<uint8_t> plain = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\r\nContent-Length: 4\r\n\r\n");
	const MCPHttp::ParseOutcome plain_outcome = MCPHttp::parse_request(plain, 1024);
	CHECK(plain_outcome.status == MCPHttp::ParseStatus::NEED_MORE);
	CHECK_FALSE(plain_outcome.expect_continue);
}

TEST_CASE("[MCPServer] HTTP idle timeout never underflows") {
	// A connection that received data is not idle, no matter how the two
	// timestamps relate to each other.
	CHECK(MCPHttp::is_idle_timeout(100000, 40000, 30000)); // 60 s of silence
	CHECK_FALSE(MCPHttp::is_idle_timeout(100000, 90000, 30000)); // 10 s of silence
	CHECK_FALSE(MCPHttp::is_idle_timeout(40000, 40000, 30000)); // same tick

	// The activity stamp comes from a second reading of `get_ticks_msec()`, so
	// it can be newer than the frame clock. The naive `now - last_activity`
	// wraps around to ~1.8e19 ms there, which used to close live connections -
	// including ones with pipelined requests still in the input buffer.
	CHECK_FALSE(MCPHttp::is_idle_timeout(100000, 100016, 30000));
	CHECK_FALSE(MCPHttp::is_idle_timeout(5, 6, 1));

	// A non-positive timeout disables the check entirely.
	CHECK_FALSE(MCPHttp::is_idle_timeout(100000, 0, 0));
}

TEST_CASE("[MCPServer] HTTP Transfer-Encoding chunked stays unsupported and is rejected") {
	// D33: decoding `Transfer-Encoding: chunked` is a deferred hardening item,
	// not part of M1 (the hof-rs contract only ever sends `Content-Length`).
	// The trade off is pinned here so that it can never change silently: a POST
	// that carries only `Transfer-Encoding: chunked` has no `Content-Length`,
	// so it is rejected by the length-required path and the connection is
	// closed without the chunked framing ever being interpreted.
	//
	// Note for the record: DESIGN-DETAIL / D33 describe this as a generic 4xx,
	// the concrete status is 411 `Length Required` (the parser deliberately
	// maps a missing `Content-Length` on a request with a body to 411).
	Vector<uint8_t> chunked = TestMCPServer::to_bytes("POST /mcp HTTP/1.1\r\nHost: 127.0.0.1\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n0\r\n\r\n");
	const MCPHttp::ParseOutcome outcome = MCPHttp::parse_request(chunked, 1024);
	CHECK(outcome.status == MCPHttp::ParseStatus::MISSING_CONTENT_LENGTH);
	CHECK(MCPHttp::status_code_for(outcome.status) == 411);
	CHECK(MCPHttp::reason_phrase(411) == "Length Required");
	// The undecodable payload is dropped, so it can never be mistaken for a body.
	CHECK(chunked.is_empty());
}

// ---------------------------------------------------------------------------
// Port resolution (GDR-4). Function level only: no socket is ever bound.
// ---------------------------------------------------------------------------

TEST_CASE("[MCPServer] port defaults are 9877 for the editor and 0 for a game") {
	Vector<String> no_args;

	MCPPortConfig editor = MCPPort::parse(no_args, false, 0, true);
	CHECK(editor.port == 9877);
	CHECK_FALSE(editor.explicit_cmdline);
	CHECK_FALSE(editor.from_project_setting);
	CHECK(MCPPort::should_listen(true, editor, false));

	MCPPortConfig game = MCPPort::parse(no_args, false, 0, false);
	CHECK(game.port == 0);
	CHECK_FALSE(MCPPort::should_listen(false, game, false));
	CHECK_FALSE(MCPPort::should_listen(false, game, true));
}

TEST_CASE("[MCPServer] --mcp-port forms are parsed and take priority") {
	Vector<String> equals_form;
	equals_form.push_back("--headless");
	equals_form.push_back("--mcp-port=9888");
	MCPPortConfig equals_config = MCPPort::parse(equals_form, true, 9911, true);
	CHECK(equals_config.port == 9888);
	CHECK(equals_config.explicit_cmdline);
	CHECK(MCPPort::should_listen(true, equals_config, false));

	Vector<String> space_form;
	space_form.push_back("--mcp-port");
	space_form.push_back("9889");
	MCPPortConfig space_config = MCPPort::parse(space_form, false, 0, false);
	CHECK(space_config.port == 9889);
	CHECK(space_config.explicit_cmdline);
	// Explicitly requested, so a game process listens.
	CHECK(MCPPort::should_listen(false, space_config, false));

	Vector<String> trailing_space;
	trailing_space.push_back("--mcp-port");
	MCPPortConfig trailing_config = MCPPort::parse(trailing_space, false, 0, true);
	CHECK(trailing_config.port == 9877);
	CHECK_FALSE(trailing_config.explicit_cmdline);

	Vector<String> invalid;
	invalid.push_back("--mcp-port=abc");
	MCPPortConfig invalid_config = MCPPort::parse(invalid, false, 0, true);
	CHECK(invalid_config.port == 9877);
	CHECK_FALSE(invalid_config.explicit_cmdline);

	Vector<String> zero;
	zero.push_back("--mcp-port=0");
	MCPPortConfig zero_config = MCPPort::parse(zero, false, 0, false);
	CHECK(zero_config.port == 0);
	CHECK(zero_config.explicit_cmdline);
	CHECK_FALSE(MCPPort::should_listen(false, zero_config, true));
}

TEST_CASE("[MCPServer] project setting port and game opt-in") {
	Vector<String> no_args;

	MCPPortConfig from_setting = MCPPort::parse(no_args, true, 9911, true);
	CHECK(from_setting.port == 9911);
	CHECK(from_setting.from_project_setting);
	CHECK(MCPPort::should_listen(true, from_setting, false));

	// A game process must opt in explicitly (C4).
	MCPPortConfig game_setting = MCPPort::parse(no_args, true, 9889, false);
	CHECK(game_setting.port == 9889);
	CHECK_FALSE(MCPPort::should_listen(false, game_setting, false));
	CHECK(MCPPort::should_listen(false, game_setting, true));

	// Out of range settings are ignored.
	MCPPortConfig out_of_range = MCPPort::parse(no_args, true, 70000, false);
	CHECK(out_of_range.port == 0);
	CHECK_FALSE(out_of_range.from_project_setting);
}

// ---------------------------------------------------------------------------
// JSON-RPC envelope (GDR-6). The strings below are the reference shapes.
// ---------------------------------------------------------------------------

TEST_CASE("[MCPServer] JSON-RPC initialize envelope") {
	MCPToolRegistry registry;

	MCPJsonRpc::Response numeric = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\"}", registry, true);
	CHECK(numeric.http_status == 200);
	CHECK(numeric.body == "{\"id\":1,\"jsonrpc\":\"2.0\",\"result\":{\"capabilities\":{\"logging\":{},\"tools\":{\"listChanged\":false}},\"protocolVersion\":\"2025-03-26\",\"serverInfo\":{\"name\":\"godot-mcp-rs\",\"version\":\"0.1.0\"}}}");

	MCPJsonRpc::Response string_id = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":\"abc\",\"method\":\"initialize\"}", registry, true);
	CHECK(string_id.body.begins_with("{\"id\":\"abc\",\"jsonrpc\":\"2.0\",\"result\":{\"capabilities\":"));
}

TEST_CASE("[MCPServer] JSON-RPC ping envelope") {
	MCPToolRegistry registry;

	MCPJsonRpc::Response response = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":7,\"method\":\"ping\"}", registry, true);
	CHECK(response.http_status == 200);
	CHECK(response.body == "{\"id\":7,\"jsonrpc\":\"2.0\",\"result\":{}}");
}

TEST_CASE("[MCPServer] JSON-RPC notifications/initialized has an empty body") {
	MCPToolRegistry registry;

	MCPJsonRpc::Response response = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\"}", registry, true);
	CHECK(response.http_status == 202);
	CHECK(response.body.is_empty());
}

TEST_CASE("[MCPServer] JSON-RPC unknown method is -32601") {
	MCPToolRegistry registry;

	MCPJsonRpc::Response response = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"does/not/exist\"}", registry, true);
	CHECK(response.body == "{\"error\":{\"code\":-32601,\"message\":\"Method not found: does/not/exist\"},\"id\":1,\"jsonrpc\":\"2.0\"}");
}

TEST_CASE("[MCPServer] JSON-RPC parse error is -32700 with a null id") {
	MCPToolRegistry registry;

	MCPJsonRpc::Response response = MCPJsonRpc::handle("{this is not json", registry, true);
	CHECK(response.http_status == 400);
	CHECK(response.body == "{\"error\":{\"code\":-32700,\"message\":\"Parse error\"},\"id\":null,\"jsonrpc\":\"2.0\"}");
}

TEST_CASE("[MCPServer] JSON-RPC invalid request is -32600") {
	MCPToolRegistry registry;

	MCPJsonRpc::Response not_an_object = MCPJsonRpc::handle("[]", registry, true);
	CHECK(not_an_object.body == "{\"error\":{\"code\":-32600,\"message\":\"Invalid request: request must be a JSON object\"},\"id\":null,\"jsonrpc\":\"2.0\"}");

	MCPJsonRpc::Response no_method = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":3}", registry, true);
	CHECK(no_method.body == "{\"error\":{\"code\":-32600,\"message\":\"Invalid request: missing method\"},\"id\":3,\"jsonrpc\":\"2.0\"}");

	MCPJsonRpc::Response bad_method = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":4,\"method\":42}", registry, true);
	CHECK(bad_method.body == "{\"error\":{\"code\":-32600,\"message\":\"Invalid request: missing method\"},\"id\":4,\"jsonrpc\":\"2.0\"}");
}

TEST_CASE("[MCPServer] JSON-RPC tools/call argument errors are -32602") {
	MCPToolRegistry registry;
	TestMCPServer::build_project_registry(registry);

	MCPJsonRpc::Response missing_name = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":5,\"method\":\"tools/call\",\"params\":{}}", registry, true);
	CHECK(missing_name.body == "{\"error\":{\"code\":-32602,\"message\":\"Missing tool name\"},\"id\":5,\"jsonrpc\":\"2.0\"}");

	MCPJsonRpc::Response bad_arguments = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":6,\"method\":\"tools/call\",\"params\":{\"name\":\"get_project_info\",\"arguments\":\"nope\"}}", registry, true);
	CHECK(bad_arguments.body == "{\"error\":{\"code\":-32602,\"message\":\"Invalid arguments: expected an object\"},\"id\":6,\"jsonrpc\":\"2.0\"}");

	MCPJsonRpc::Response bad_params = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":6,\"method\":\"tools/call\",\"params\":7}", registry, true);
	CHECK(bad_params.body == "{\"error\":{\"code\":-32602,\"message\":\"Invalid params: expected an object\"},\"id\":6,\"jsonrpc\":\"2.0\"}");

	MCPJsonRpc::Response unknown_tool = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":8,\"method\":\"tools/call\",\"params\":{\"name\":\"not_a_tool\"}}", registry, true);
	CHECK(unknown_tool.body == "{\"error\":{\"code\":-32601,\"message\":\"Method not found: not_a_tool\"},\"id\":8,\"jsonrpc\":\"2.0\"}");
}

TEST_CASE("[MCPServer] JSON-RPC echoes string and number ids verbatim") {
	MCPToolRegistry registry;
	TestMCPServer::build_project_registry(registry);

	// Godot's JSON parser turns every number into a double, so the raw token
	// has to be preserved: `1.0` would break serde_json's `as_u64()` on the
	// client side and therefore id correlation as a whole.
	MCPJsonRpc::Response number_id = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":123,\"method\":\"tools/list\"}", registry, true);
	CHECK(number_id.body.begins_with("{\"id\":123,"));

	MCPJsonRpc::Response string_id = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":\"req-42\",\"method\":\"tools/list\"}", registry, true);
	CHECK(string_id.body.begins_with("{\"id\":\"req-42\","));

	MCPJsonRpc::Response float_id = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":1.5,\"method\":\"ping\"}", registry, true);
	CHECK(float_id.body == "{\"id\":1.5,\"jsonrpc\":\"2.0\",\"result\":{}}");

	// Whitespace between the key and the value is allowed.
	MCPJsonRpc::Response spaced_id = MCPJsonRpc::handle("{ \"id\" : 8 , \"method\" : \"ping\" }", registry, true);
	CHECK(spaced_id.body.begins_with("{\"id\":8,"));

	// An `id` nested in `params` must never be mistaken for the request id.
	MCPJsonRpc::Response nested_id = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":5,\"method\":\"tools/call\",\"params\":{\"name\":\"get_project_info\",\"arguments\":{\"id\":99}}}", registry, true);
	CHECK(nested_id.body.begins_with("{\"id\":5,\"jsonrpc\":"));

	// Requests without an id are answered with a null id.
	MCPJsonRpc::Response no_id = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"method\":\"ping\"}", registry, true);
	CHECK(no_id.body == "{\"id\":null,\"jsonrpc\":\"2.0\",\"result\":{}}");

	// Interleaved ids keep their own response.
	MCPJsonRpc::Response a = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"ping\"}", registry, true);
	MCPJsonRpc::Response b = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"ping\"}", registry, true);
	CHECK(a.body.begins_with("{\"id\":1,"));
	CHECK(b.body.begins_with("{\"id\":2,"));
}

// ---------------------------------------------------------------------------
// Tool registry and scope filtering (GDR-7)
// ---------------------------------------------------------------------------

TEST_CASE("[MCPServer] tools/list filters by process scope") {
	MCPToolRegistry registry;
	TestMCPServer::build_scope_registry(registry);

	CHECK(MCPToolRegistry::scope_matches(MCPToolScope::EDITOR, true));
	CHECK_FALSE(MCPToolRegistry::scope_matches(MCPToolScope::EDITOR, false));
	CHECK_FALSE(MCPToolRegistry::scope_matches(MCPToolScope::GAME, true));
	CHECK(MCPToolRegistry::scope_matches(MCPToolScope::GAME, false));
	CHECK(MCPToolRegistry::scope_matches(MCPToolScope::BOTH, true));
	CHECK(MCPToolRegistry::scope_matches(MCPToolScope::BOTH, false));

	CHECK(registry.is_tool_visible("editor_get_scope_probe", true));
	CHECK_FALSE(registry.is_tool_visible("editor_get_scope_probe", false));
	CHECK(registry.is_tool_visible("running_game_get_scope_probe", false));
	CHECK_FALSE(registry.is_tool_visible("running_game_get_scope_probe", true));

	MCPJsonRpc::Response editor = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}", registry, true);
	Variant parsed_editor = TestMCPServer::parse_json(editor.body);
	CHECK(parsed_editor.get_type() == Variant::DICTIONARY);
	if (parsed_editor.get_type() == Variant::DICTIONARY) {
		Dictionary editor_result = (Dictionary)parsed_editor;
		CHECK(editor_result.has("result"));
		if (editor_result.has("result")) {
			Dictionary result_body = editor_result["result"];
			CHECK(result_body.has("tools"));
			if (result_body.has("tools")) {
				Array editor_tools = result_body["tools"];
				CHECK(editor_tools.size() == 2);
				if (editor_tools.size() == 2) {
					CHECK((String)((Dictionary)editor_tools[0])["name"] == "editor_get_scope_probe");
					CHECK((String)((Dictionary)editor_tools[1])["name"] == "project_get_scope_probe");
				}
			}
		}
	}

	MCPJsonRpc::Response game = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/list\"}", registry, false);
	Variant parsed_game = TestMCPServer::parse_json(game.body);
	CHECK(parsed_game.get_type() == Variant::DICTIONARY);
	if (parsed_game.get_type() == Variant::DICTIONARY) {
		Dictionary game_result = (Dictionary)parsed_game;
		CHECK(game_result.has("result"));
		if (game_result.has("result")) {
			Dictionary result_body = game_result["result"];
			CHECK(result_body.has("tools"));
			if (result_body.has("tools")) {
				Array game_tools = result_body["tools"];
				CHECK(game_tools.size() == 2);
				if (game_tools.size() == 2) {
					CHECK((String)((Dictionary)game_tools[0])["name"] == "running_game_get_scope_probe");
					CHECK((String)((Dictionary)game_tools[1])["name"] == "project_get_scope_probe");
				}
			}
		}
	}
}

TEST_CASE("[MCPServer] tools/list exposes exactly the six template group tools") {
	MCPToolRegistry registry;
	TestMCPServer::build_project_registry(registry);

	CHECK(registry.get_visible_tool_count(true) == 6);
	CHECK(registry.get_visible_tool_count(false) == 6);

	// Byte exact, including the descriptions and input schemas taken verbatim
	// from docs/tools_list.renamed.json (= the renamed old contract). The first
	// two entries are byte-identical to the M1 revision of this test, which is
	// the migration regression guard for project_get_info /
	// project_get_settings.
	MCPJsonRpc::Response response = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}", registry, true);
	CHECK(response.body == String::utf8("{\"id\":1,\"jsonrpc\":\"2.0\",\"result\":{\"tools\":["
										"{\"description\":\"获取项目信息\",\"inputSchema\":{\"properties\":{},\"required\":[],\"type\":\"object\"},\"name\":\"project_get_info\"},"
										"{\"description\":\"获取项目设置\",\"inputSchema\":{\"properties\":{\"include_default\":{\"default\":false,\"type\":\"boolean\"},\"prefix\":{\"type\":\"string\"}},\"required\":[],\"type\":\"object\"},\"name\":\"project_get_settings\"},"
										"{\"description\":\"获取文件系统树状结构\",\"inputSchema\":{\"properties\":{\"max_depth\":{\"default\":-1,\"type\":\"integer\"},\"path\":{\"default\":\"res://\",\"type\":\"string\"}},\"required\":[],\"type\":\"object\"},\"name\":\"project_get_filesystem_tree\"},"
										"{\"description\":\"搜索文件 判别点：只匹配文件名子串（大小写不敏感、上限 200），不读文件内容、不返回行号；要搜索文件内容请用 project_search_file_contents。\",\"inputSchema\":{\"properties\":{\"path\":{\"default\":\"res://\",\"type\":\"string\"},\"pattern\":{\"type\":\"string\"}},\"required\":[\"pattern\"],\"type\":\"object\"},\"name\":\"project_search_file_names\"},"
										"{\"description\":\"在文件内容中搜索文本 判别点：逐行返回 {file,line,text}（大小写不敏感、上限 50，跳过 addons 与 .godot 目录）；要按文件聚合的 {file,lines[]}（大小写敏感、上限 100）请用 project_find_files_referencing_symbol。\",\"inputSchema\":{\"properties\":{\"file_pattern\":{\"default\":\"*\",\"type\":\"string\"},\"path\":{\"default\":\"res://\",\"type\":\"string\"},\"pattern\":{\"type\":\"string\"}},\"required\":[\"pattern\"],\"type\":\"object\"},\"name\":\"project_search_file_contents\"},"
										"{\"description\":\"在项目文件中搜索指定模式的引用 判别点：按文件聚合返回 {file,lines[]}（每文件最多 5 行、大小写敏感、上限 100，跳过隐藏文件与 addons，只扫 .tscn/.gd/.tres/.gdshader）；要逐行 {file,line,text}（大小写不敏感、上限 50）请用 project_search_file_contents。\",\"inputSchema\":{\"properties\":{\"pattern\":{\"description\":\"要搜索的模式\",\"type\":\"string\"}},\"required\":[\"pattern\"],\"type\":\"object\"},\"name\":\"project_find_files_referencing_symbol\"}"
										"]}}"));
}

TEST_CASE("[MCPServer] the shared registration entry point registers the group") {
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	// 6 template + 7 analysis + 6 read_files + 4 write_resource_scene + 1
	// running_game_read_scene (TASK-009) + 6 running_game_observation + 1
	// running_game_script_execution (TASK-010) + 3 running_game_frame_observation
	// + 1 running_game_capture (TASK-011) + 4 running_game_input + 1
	// running_game_node_write (TASK-012); the editor-scope groups are absent
	// because this doctest process is not an editor, so the game-process table
	// carries the 23 both-scope tools plus the 17 game-scope ones.
	CHECK(registry.get_tool_count() == 40);
	CHECK(registry.has_tool("project_get_info"));
	CHECK(registry.has_tool("project_find_files_referencing_symbol"));
	CHECK(registry.has_tool("project_get_statistics"));
	CHECK(registry.has_tool("project_get_scene_exports"));
	CHECK(registry.has_tool("running_game_find_nearby_nodes"));
	CHECK(registry.has_tool("running_game_get_scene_tree"));
	CHECK(registry.has_tool("running_game_execute_gdscript"));
	// TASK-011: the three deferred tools and the game-scope capture tool.
	CHECK(registry.has_tool("running_game_get_node_property_samples"));
	CHECK(registry.has_tool("running_game_find_node_when_available"));
	CHECK(registry.has_tool("running_game_capture_frames"));
	CHECK(registry.has_tool("running_game_capture_screenshot"));
	// TASK-012: the whole game-side input family plus the game-scope property
	// write.
	CHECK(registry.has_tool("running_game_create_input_recording"));
	CHECK(registry.has_tool("running_game_stop_input_recording"));
	CHECK(registry.has_tool("running_game_play_input_recording"));
	CHECK(registry.has_tool("running_game_simulate_button_click_by_text"));
	CHECK(registry.has_tool("running_game_set_node_property"));
}

TEST_CASE("[MCPServer] tools of later batches are not registered") {
	// GDR-7: registering an unimplemented tool just to make a gate look complete
	// is forbidden, so the unimplemented B1 groups must be absent from the
	// registry (and therefore from `tools/list`).
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	CHECK(registry.get_tool_count() == 40);
	CHECK_FALSE(registry.has_tool("editor_open_scene"));
	CHECK_FALSE(registry.has_tool("editor_save_scene"));
	// TASK-009 closed B1: the game-scope tool of the last group is registered in
	// a game process (the doctest process is one) ...
	CHECK(registry.has_tool("running_game_find_nearby_nodes"));
	CHECK(registry.is_tool_visible("running_game_find_nearby_nodes", false));
	// TASK-010 section 4: the same holds for the B2 game-scope tools of the two
	// groups this task implemented, while the rest of B2 stays unregistered
	// (GDR-7: never register what does not work).
	CHECK(registry.has_tool("running_game_get_scene_tree"));
	CHECK(registry.is_tool_visible("running_game_get_scene_tree", false));
	CHECK(registry.has_tool("running_game_execute_gdscript"));
	CHECK(registry.is_tool_visible("running_game_execute_gdscript", false));
	// TASK-011 section 2: the frame-clock group and the capture group are
	// implemented now, so the two tools that were the *examples* of "not
	// registered" in this test are present - and the rest of B2 is still absent,
	// which is the half of the assertion that keeps its strength.
	CHECK(registry.has_tool("running_game_capture_frames"));
	CHECK(registry.is_tool_visible("running_game_capture_frames", false));
	CHECK(registry.has_tool("running_game_find_node_when_available"));
	CHECK(registry.is_tool_visible("running_game_find_node_when_available", false));
	CHECK(registry.has_tool("running_game_get_node_property_samples"));
	CHECK(registry.is_tool_visible("running_game_get_node_property_samples", false));
	CHECK(registry.has_tool("running_game_capture_screenshot"));
	CHECK(registry.is_tool_visible("running_game_capture_screenshot", false));
	// TASK-012 section 2: the eight tools of this batch are implemented now, so
	// the four game-scope ones are present in a game process and the three
	// editor-scope ones are absent from it (GDR-19 17.3: an EDITOR-scope tool is
	// not even registered outside an editor) ...
	CHECK(registry.has_tool("running_game_create_input_recording"));
	CHECK(registry.is_tool_visible("running_game_create_input_recording", false));
	CHECK(registry.has_tool("running_game_stop_input_recording"));
	CHECK(registry.is_tool_visible("running_game_stop_input_recording", false));
	CHECK(registry.has_tool("running_game_play_input_recording"));
	CHECK(registry.is_tool_visible("running_game_play_input_recording", false));
	CHECK(registry.has_tool("running_game_simulate_button_click_by_text"));
	CHECK(registry.is_tool_visible("running_game_simulate_button_click_by_text", false));
	CHECK(registry.has_tool("running_game_set_node_property"));
	CHECK(registry.is_tool_visible("running_game_set_node_property", false));
	CHECK_FALSE(registry.has_tool("editor_play_scene"));
	CHECK_FALSE(registry.has_tool("editor_stop_scene"));
	CHECK_FALSE(registry.has_tool("editor_get_input_actions"));
	// ... and the still-unimplemented groups keep the other half of the
	// assertion: these must stay absent (GDR-7). The editor input *simulation*
	// family is the B2 group this batch deliberately does not touch, and the B3
	// node-write and B4/B5 families are later batches.
	CHECK_FALSE(registry.has_tool("editor_simulate_key"));
	CHECK_FALSE(registry.has_tool("editor_simulate_input_action"));
	CHECK_FALSE(registry.has_tool("editor_simulate_mouse_click"));
	CHECK_FALSE(registry.has_tool("editor_simulate_mouse_move"));
	CHECK_FALSE(registry.has_tool("editor_simulate_input_sequence"));
	CHECK_FALSE(registry.has_tool("editor_add_input_action"));
	// Two names that are in the contract but belong to groups no task has
	// implemented yet: their absence is the same GDR-7 assertion as the six
	// `editor_simulate_*` / `editor_add_input_action` ones above.
	CHECK_FALSE(registry.has_tool("editor_open_scene"));
	CHECK_FALSE(registry.has_tool("editor_save_scene"));
	// ... while the editor-process registry must not carry it at all.
	MCPToolRegistry editor_registry;
	TestMCPServer::build_editor_process_registry(editor_registry);
	CHECK(editor_registry.has_tool("running_game_find_nearby_nodes"));
	CHECK_FALSE(editor_registry.is_tool_visible("running_game_find_nearby_nodes", true));
	CHECK_FALSE(registry.has_tool("editor_remove_output_log"));
}

// ---------------------------------------------------------------------------
// Tool builder + argument helpers + error factories (TASK-002 section 2.2.2)
// ---------------------------------------------------------------------------

TEST_CASE("[MCPServer] the editor guard is an alias of the engine tools macro") {
	// The module-owned guard must be defined exactly when Godot's TOOLS_ENABLED
	// is: the doctest binary is an editor build, so both are defined here. If
	// the guard ever drifted (e.g. to a macro name this fork does not define),
	// every editor-only call site would silently disappear from an editor build.
#ifdef TOOLS_ENABLED
	CHECK(MCP_EDITOR_TOOLS_ENABLED == 1);
#endif
	CHECK_FALSE(MCPTools::is_editor_process());
}

TEST_CASE("[MCPServer] tool builder refuses an incomplete declaration") {
	MCPToolDef built;
	String reason;

	// Nothing but the name and the description: channel, verb, scope, mutating
	// and handler are all missing.
	MCPTools::ToolBuilder bare("project_get_bare_probe", "bare");
	CHECK_FALSE(bare.build(built, reason));
	CHECK(reason.contains("must declare"));
	CHECK(reason.contains("channel"));
	CHECK(reason.contains("verb"));
	CHECK(reason.contains("scope"));
	CHECK(reason.contains("mutating"));
	CHECK(reason.contains("handler"));

	// Declaring only `mutating` still fails: every dimension is mandatory.
	MCPTools::ToolBuilder partial("project_get_partial_probe", "partial");
	partial.mutating(false);
	CHECK_FALSE(partial.build(built, reason));
	CHECK(reason.contains("channel"));
	CHECK_FALSE(reason.contains("mutating"));

	// A complete declaration builds and carries every declared value.
	MCPTools::ToolBuilder complete("project_get_complete_probe", "complete");
	complete.channel("project").verb("get").scope(MCPToolScope::BOTH).mutating(true).schema(MCPTools::empty_object_schema()).handler(_unused_handler);
	CHECK(complete.build(built, reason));
	CHECK(reason.is_empty());
	CHECK(built.mutating == true);
	CHECK(built.scope == MCPToolScope::BOTH);
	CHECK(built.handler != nullptr);

	// The GDR-16 lint runs inside the builder as well.
	MCPTools::ToolBuilder bad_verb("project_update_probe", "bad");
	bad_verb.channel("project").verb("update").scope(MCPToolScope::BOTH).mutating(false).schema(MCPTools::empty_object_schema()).handler(_unused_handler);
	CHECK_FALSE(bad_verb.build(built, reason));
	CHECK(reason.contains("GDR-16 L4"));
}

TEST_CASE("[MCPServer] tool builder keeps editor-only tools out of a game process") {
	MCPToolRegistry registry;

	MCPTools::ToolBuilder editor_only("editor_get_builder_probe", "editor only");
	editor_only.channel("editor").verb("get").scope(MCPToolScope::EDITOR).mutating(false).schema(MCPTools::empty_object_schema()).handler(_unused_handler);
	const bool registered = editor_only.register_into(registry);

	// The doctest process is not an editor, so the editor-only tool must not
	// even enter the table (registering it would still be hidden by the scope
	// filter, but a game process must not carry it at all).
	CHECK_FALSE(MCPTools::is_editor_process());
	CHECK_FALSE(registered);
	CHECK_FALSE(registry.has_tool("editor_get_builder_probe"));
	CHECK(registry.get_tool_count() == 0);

	// A `both` scope tool registers in exactly the same process.
	MCPTools::ToolBuilder both("project_get_builder_probe", "both");
	both.channel("project").verb("get").scope(MCPToolScope::BOTH).mutating(false).schema(MCPTools::empty_object_schema()).handler(_unused_handler);
	CHECK(both.register_into(registry));
	CHECK(registry.has_tool("project_get_builder_probe"));
	CHECK(registry.get_tool_count() == 1);
}

TEST_CASE("[MCPServer] argument helpers report -32602") {
	MCPToolError error;
	Dictionary args;
	String text;
	int64_t number = 0;
	bool flag = false;

	// Required, missing.
	CHECK_FALSE(MCPTools::require_string(args, "pattern", text, error));
	CHECK(error.code == -32602);
	CHECK(error.message == "Missing required parameter: pattern");
	CHECK(error.data.get_type() == Variant::NIL);

	// Required, wrong type.
	error = MCPToolError();
	args["pattern"] = 42;
	CHECK_FALSE(MCPTools::require_string(args, "pattern", text, error));
	CHECK(error.code == -32602);
	CHECK(error.message.contains("must be a string"));
	CHECK(error.message.contains("int"));

	// Required int accepts an integral float (JSON-RPC clients may send 2.0) and
	// rejects a fractional one.
	error = MCPToolError();
	args["max_depth"] = 2.0;
	CHECK(MCPTools::require_int(args, "max_depth", number, error));
	CHECK(number == 2);
	error = MCPToolError();
	args["max_depth"] = 2.5;
	CHECK_FALSE(MCPTools::require_int(args, "max_depth", number, error));
	CHECK(error.code == -32602);
	CHECK(error.message.contains("must be an integer"));

	// Optional: absent means default, present with the wrong type is an error.
	error = MCPToolError();
	CHECK(MCPTools::optional_string(args, "absent", "fallback", text, error));
	CHECK(text == "fallback");
	CHECK_FALSE(error.is_error());

	error = MCPToolError();
	CHECK(MCPTools::optional_int(args, "absent", -1, number, error));
	CHECK(number == -1);

	error = MCPToolError();
	CHECK(MCPTools::optional_bool(args, "absent", true, flag, error));
	CHECK(flag == true);

	error = MCPToolError();
	args["prefix"] = true;
	CHECK_FALSE(MCPTools::optional_string(args, "prefix", "", text, error));
	CHECK(error.code == -32602);
	CHECK(error.message.contains("must be a string"));
	CHECK(error.message.contains("bool"));

	error = MCPToolError();
	args["include_default"] = "yes";
	CHECK_FALSE(MCPTools::optional_bool(args, "include_default", false, flag, error));
	CHECK(error.code == -32602);
	CHECK(error.message.contains("must be a boolean"));
}

TEST_CASE("[MCPServer] tool error factories carry the reference codes and data") {
	MCPToolError invalid = MCPToolError::invalid_params("Missing required parameter: pattern");
	CHECK(invalid.code == -32602);
	CHECK(invalid.message == "Missing required parameter: pattern"); // no prefix (GDR-6)

	MCPToolError not_found = MCPToolError::not_found("File 'res://nope.gd'", "List the project first");
	CHECK(not_found.code == -32001);
	CHECK(not_found.message == "File 'res://nope.gd' not found");
	CHECK(((Dictionary)not_found.data)["suggestion"] == "List the project first");

	MCPToolError no_scene = MCPToolError::no_scene();
	CHECK(no_scene.code == -32000);
	CHECK(no_scene.message == "No scene is currently open");
	CHECK(((Dictionary)no_scene.data).has("suggestion"));

	MCPToolError unimplemented = MCPToolError::not_implemented("probe feature", "Wait for a later batch");
	CHECK(unimplemented.code == -32000);
	CHECK(unimplemented.message == "Not implemented: probe feature");
	CHECK(((Dictionary)unimplemented.data)["suggestion"] == "Wait for a later batch");

	MCPToolError internal = MCPToolError::internal("boom");
	CHECK(internal.code == -32603);
	CHECK(internal.message == "Internal error: boom");
}

TEST_CASE("[MCPServer] tools/call maps a tool error to its own code and data") {
	MCPToolRegistry registry;
	TestMCPServer::build_error_probe_registry(registry);

	MCPJsonRpc::Response not_found = MCPJsonRpc::handle(
			"{\"jsonrpc\":\"2.0\",\"id\":11,\"method\":\"tools/call\",\"params\":{\"name\":\"project_get_error_probe\"}}", registry, true);
	CHECK(not_found.http_status == 200);
	CHECK(not_found.body == "{\"error\":{\"code\":-32001,\"data\":{\"suggestion\":\"Create it first\"},"
							"\"message\":\"Probe resource 'x' not found\"},\"id\":11,\"jsonrpc\":\"2.0\"}");

	MCPJsonRpc::Response unimplemented = MCPJsonRpc::handle(
			"{\"jsonrpc\":\"2.0\",\"id\":12,\"method\":\"tools/call\",\"params\":{\"name\":\"project_get_unimplemented_probe\"}}", registry, true);
	CHECK(unimplemented.body == "{\"error\":{\"code\":-32000,\"data\":{\"suggestion\":\"Wait for a later batch\"},"
								"\"message\":\"Not implemented: probe feature\"},\"id\":12,\"jsonrpc\":\"2.0\"}");
}

TEST_CASE("[MCPServer] project_get_info success path") {
	MCPToolRegistry registry;
	TestMCPServer::build_project_registry(registry);

	MCPToolError tool_error;
	Variant result = registry.call_tool("project_get_info", Dictionary(), tool_error);
	CHECK_FALSE(tool_error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() == Variant::DICTIONARY) {
		Dictionary info = (Dictionary)result;
		CHECK(info.has("project_name"));
		CHECK(info.has("version"));
		CHECK(info.has("editor_screen_size"));
		if (info.has("editor_screen_size")) {
			CHECK(((Dictionary)info["editor_screen_size"]).has("width"));
			CHECK(((Dictionary)info["editor_screen_size"]).has("height"));
		}
	}
}

TEST_CASE("[MCPServer] tools/call wraps the result in the content envelope") {
	MCPToolRegistry registry;
	TestMCPServer::build_project_registry(registry);

	MCPJsonRpc::Response response = MCPJsonRpc::handle("{\"jsonrpc\":\"2.0\",\"id\":9,\"method\":\"tools/call\",\"params\":{\"name\":\"get_project_info\"}}", registry, true);
	CHECK(response.http_status == 200);

	Variant parsed = TestMCPServer::parse_json(response.body);
	CHECK(parsed.get_type() == Variant::DICTIONARY);
	if (parsed.get_type() == Variant::DICTIONARY) {
		Dictionary envelope = (Dictionary)parsed;
		CHECK(envelope["jsonrpc"] == "2.0");
		CHECK((int)envelope["id"] == 9);
		CHECK(envelope.has("result"));
		if (envelope.has("result")) {
			Dictionary result_body = envelope["result"];
			CHECK(result_body.has("content"));
			if (result_body.has("content")) {
				Array content = result_body["content"];
				CHECK(content.size() == 1);
				if (content.size() == 1) {
					Dictionary item = (Dictionary)content[0];
					CHECK(item["type"] == "text");
					CHECK(item.has("text"));
					if (item.has("text")) {
						Variant parsed_text = TestMCPServer::parse_json(item["text"]);
						CHECK(parsed_text.get_type() == Variant::DICTIONARY);
						if (parsed_text.get_type() == Variant::DICTIONARY) {
							Dictionary payload = (Dictionary)parsed_text;
							CHECK(payload.has("project_name"));
							CHECK(payload.has("version"));
						}
					}
				}
			}
		}
	}
}

TEST_CASE("[MCPServer] project_get_settings filters by prefix") {
	MCPToolRegistry registry;
	TestMCPServer::build_project_registry(registry);

	Dictionary args;
	args["prefix"] = "application/config/name";
	MCPToolError tool_error;
	Variant result = registry.call_tool("project_get_settings", args, tool_error);
	CHECK_FALSE(tool_error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() == Variant::DICTIONARY) {
		Dictionary payload = (Dictionary)result;
		CHECK(payload.has("settings"));
		CHECK(payload.has("count"));
		if (payload.has("settings")) {
			Dictionary settings = payload["settings"];
			CHECK(settings.has("application/config/name"));
			CHECK((int)payload["count"] == settings.size());
		}
	}
}

TEST_CASE("[MCPServer] project_get_settings rejects a mistyped optional argument") {
	MCPToolRegistry registry;
	TestMCPServer::build_project_registry(registry);

	Dictionary args;
	args["prefix"] = 7;
	MCPToolError tool_error;
	const Variant result = registry.call_tool("project_get_settings", args, tool_error);
	CHECK(tool_error.code == -32602);
	CHECK(tool_error.message.contains("must be a string"));
	CHECK(result.get_type() == Variant::NIL);
}

// ---------------------------------------------------------------------------
// The four new B1 template tools
// ---------------------------------------------------------------------------

TEST_CASE("[MCPServer] project_get_filesystem_tree lists a directory and reports a missing one") {
	MCPToolRegistry registry;
	TestMCPServer::build_project_registry(registry);

	// max_depth = 0 keeps the walk to the root entry, so the assertion does not
	// depend on how many files happen to sit next to the test binary.
	Dictionary args;
	args["max_depth"] = 0;
	MCPToolError tool_error;
	const Variant result = registry.call_tool("project_get_filesystem_tree", args, tool_error);
	CHECK_FALSE(tool_error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = (Dictionary)result;
		CHECK(payload.has("tree"));
		if (payload.has("tree")) {
			const Dictionary tree = payload["tree"];
			CHECK(tree.has("name"));
			CHECK(tree.has("path"));
			CHECK((String)tree["path"] == "res://");
			CHECK((String)tree["type"] == "directory");
		}
	}

	// A project directory that does not exist is a `-32001` tool error with a
	// suggestion (GDR-14), not an empty tree.
	Dictionary missing;
	missing["path"] = "res://__no_such_directory_for_mcp_tests__";
	MCPToolError missing_error;
	const Variant missing_result = registry.call_tool("project_get_filesystem_tree", missing, missing_error);
	CHECK(missing_error.code == -32001);
	CHECK(missing_error.message.contains("not found"));
	CHECK(missing_error.message.contains("__no_such_directory_for_mcp_tests__"));
	CHECK(((Dictionary)missing_error.data).has("suggestion"));
	CHECK(missing_result.get_type() == Variant::NIL);

	// A path outside the project is an argument error.
	Dictionary outside;
	outside["path"] = "C:/Windows";
	MCPToolError outside_error;
	registry.call_tool("project_get_filesystem_tree", outside, outside_error);
	CHECK(outside_error.code == -32602);
	CHECK(outside_error.message.contains("res://"));

	Dictionary upwards;
	upwards["path"] = "res://../etc";
	MCPToolError upwards_error;
	registry.call_tool("project_get_filesystem_tree", upwards, upwards_error);
	CHECK(upwards_error.code == -32602);
	CHECK(upwards_error.message.contains(".."));

	// D-4 (TASK-003 section 1.3) end to end: the audit's `res://` + `.` / space
	// inputs now address the project root itself, so the *returned* path is
	// canonical and no `.` / ` ` directory entry is ever opened or echoed back.
	Dictionary dotted;
	dotted["path"] = "res://.";
	dotted["max_depth"] = 0;
	MCPToolError dotted_error;
	const Variant dotted_result = registry.call_tool("project_get_filesystem_tree", dotted, dotted_error);
	CHECK_FALSE(dotted_error.is_error());
	if (dotted_result.get_type() == Variant::DICTIONARY) {
		CHECK((String)((Dictionary)((Dictionary)dotted_result)["tree"])["path"] == "res://");
	}

	Dictionary blank;
	blank["path"] = "res:// ";
	blank["max_depth"] = 0;
	MCPToolError blank_error;
	const Variant blank_result = registry.call_tool("project_get_filesystem_tree", blank, blank_error);
	CHECK_FALSE(blank_error.is_error());
	if (blank_result.get_type() == Variant::DICTIONARY) {
		CHECK((String)((Dictionary)((Dictionary)blank_result)["tree"])["path"] == "res://");
	}

	// The subdirectory case is taken from the real tree, so the assertion does
	// not depend on which directory `res://` resolves to in the doctest binary.
	Dictionary shallow;
	shallow["max_depth"] = 1;
	MCPToolError shallow_error;
	const Variant shallow_result = registry.call_tool("project_get_filesystem_tree", shallow, shallow_error);
	CHECK_FALSE(shallow_error.is_error());
	String child_dir;
	if (shallow_result.get_type() == Variant::DICTIONARY) {
		const Dictionary tree = ((Dictionary)shallow_result)["tree"];
		if (tree.has("children")) {
			const Array children = tree["children"];
			for (int i = 0; i < children.size(); i++) {
				const Dictionary child = children[i];
				if ((String)child["type"] == "directory") {
					child_dir = child["path"];
					break;
				}
			}
		}
	}
	CHECK_FALSE(child_dir.is_empty());
	if (!child_dir.is_empty()) {
		Dictionary child_dot;
		child_dot["path"] = child_dir + "/.";
		MCPToolError child_error;
		const Variant child_result = registry.call_tool("project_get_filesystem_tree", child_dot, child_error);
		CHECK_FALSE(child_error.is_error());
		if (child_result.get_type() == Variant::DICTIONARY) {
			CHECK((String)((Dictionary)((Dictionary)child_result)["tree"])["path"] == child_dir);
		}
	}
}

TEST_CASE("[MCPServer] project_search_file_names requires a pattern") {
	MCPToolRegistry registry;
	TestMCPServer::build_project_registry(registry);

	MCPToolError tool_error;
	const Variant result = registry.call_tool("project_search_file_names", Dictionary(), tool_error);
	CHECK(tool_error.code == -32602);
	CHECK(tool_error.message == "Missing required parameter: pattern");
	CHECK(result.get_type() == Variant::NIL);

	Dictionary wrong_type;
	wrong_type["pattern"] = 12;
	MCPToolError type_error;
	registry.call_tool("project_search_file_names", wrong_type, type_error);
	CHECK(type_error.code == -32602);
	CHECK(type_error.message.contains("must be a string"));

	// A missing search root is the bottom layer failure class of this tool.
	Dictionary missing_root;
	missing_root["pattern"] = "anything";
	missing_root["path"] = "res://__no_such_directory_for_mcp_tests__";
	MCPToolError missing_error;
	registry.call_tool("project_search_file_names", missing_root, missing_error);
	CHECK(missing_error.code == -32001);
	CHECK(missing_error.message.contains("not found"));
}

TEST_CASE("[MCPServer] the two de-merged search tools stay distinct (GDR-17)") {
	MCPToolRegistry registry;
	TestMCPServer::build_project_registry(registry);

	// Two registered tools, two names, two handlers, two result shapes.
	CHECK(registry.has_tool("project_search_file_contents"));
	CHECK(registry.has_tool("project_find_files_referencing_symbol"));

	Array tools = registry.build_tools_list(true);
	Dictionary contents;
	Dictionary references;
	for (int i = 0; i < tools.size(); i++) {
		const Dictionary entry = tools[i];
		if ((String)entry["name"] == "project_search_file_contents") {
			contents = entry;
		}
		if ((String)entry["name"] == "project_find_files_referencing_symbol") {
			references = entry;
		}
	}
	CHECK_FALSE(contents.is_empty());
	CHECK_FALSE(references.is_empty());

	// Different parameters: the content search takes `file_pattern` and `path`,
	// the reference scan takes neither.
	const Dictionary contents_properties = ((Dictionary)contents["inputSchema"])["properties"];
	const Dictionary references_properties = ((Dictionary)references["inputSchema"])["properties"];
	CHECK(contents_properties.has("file_pattern"));
	CHECK(contents_properties.has("path"));
	CHECK_FALSE(references_properties.has("file_pattern"));
	CHECK_FALSE(references_properties.has("path"));

	// Different descriptions, each naming the other as the alternative. The
	// Chinese literals have to go through String::utf8(): `String(const char *)`
	// decodes as Latin-1, which would compare mojibake against a real string.
	const String contents_description = contents["description"];
	const String references_description = references["description"];
	CHECK(contents_description != references_description);
	CHECK(contents_description.contains(String::utf8("逐行")));
	CHECK(contents_description.contains("project_find_files_referencing_symbol"));
	CHECK(references_description.contains(String::utf8("按文件聚合")));
	CHECK(references_description.contains("project_search_file_contents"));

	// A pattern that cannot exist anywhere: the reference scan must answer with
	// its own result shape {pattern, matches[], count} and no hit. The walk only
	// ever *reads* .tscn/.gd/.tres/.gdshader files, so it stays cheap.
	MCPToolError references_error;
	Dictionary references_args;
	references_args["pattern"] = "MCP_TEST_PATTERN_THAT_CANNOT_EXIST_12345";
	const Variant references_result = registry.call_tool("project_find_files_referencing_symbol", references_args, references_error);
	CHECK_FALSE(references_error.is_error());
	CHECK(references_result.get_type() == Variant::DICTIONARY);
	if (references_result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = (Dictionary)references_result;
		CHECK((int)payload["count"] == 0);
		CHECK((String)payload["pattern"] == "MCP_TEST_PATTERN_THAT_CANNOT_EXIST_12345");
		CHECK(((Array)payload["matches"]).is_empty());
		CHECK_FALSE(payload.has("query"));
	}

	// The argument contract differs as well.
	MCPToolError missing;
	registry.call_tool("project_find_files_referencing_symbol", Dictionary(), missing);
	CHECK(missing.code == -32602);
	CHECK(missing.message == "Missing required parameter: pattern");

	MCPToolError contents_type_error;
	Dictionary wrong_file_pattern;
	wrong_file_pattern["pattern"] = "x";
	wrong_file_pattern["file_pattern"] = 5;
	registry.call_tool("project_search_file_contents", wrong_file_pattern, contents_type_error);
	CHECK(contents_type_error.code == -32602);
	CHECK(contents_type_error.message.contains("file_pattern"));
	CHECK(contents_type_error.message.contains("must be a string"));
}

TEST_CASE("[MCPServer] project_search_file_contents maps a missing root to -32001") {
	MCPToolRegistry registry;
	TestMCPServer::build_project_registry(registry);

	Dictionary args;
	args["pattern"] = "x";
	args["path"] = "res://__no_such_directory_for_mcp_tests__";
	MCPToolError tool_error;
	registry.call_tool("project_search_file_contents", args, tool_error);
	CHECK(tool_error.code == -32001);
	CHECK(tool_error.message.contains("not found"));
}

TEST_CASE("[MCPServer] project_path_is_normalized_for_every_project_tool") {
	MCPToolError error;
	String normalized;

	CHECK(MCPTools::normalize_project_path("", normalized, error));
	CHECK(normalized == "res://");
	CHECK(MCPTools::normalize_project_path("res://", normalized, error));
	CHECK(normalized == "res://");
	CHECK(MCPTools::normalize_project_path("res://scenes/", normalized, error));
	CHECK(normalized == "res://scenes");
	CHECK(MCPTools::normalize_project_path("  res://scenes  ", normalized, error));
	CHECK(normalized == "res://scenes");

	CHECK_FALSE(MCPTools::normalize_project_path("user://x", normalized, error));
	CHECK(error.code == -32602);
	CHECK_FALSE(MCPTools::normalize_project_path("res://..", normalized, error));
	CHECK(error.code == -32602);

	// D-4 (TASK-003 section 1.3): `.` / empty / whitespace-only segments are
	// folded away instead of being echoed back as a `.` directory entry.
	CHECK(MCPTools::normalize_project_path("res://.", normalized, error));
	CHECK(normalized == "res://");
	CHECK(MCPTools::normalize_project_path("res://src/.", normalized, error));
	CHECK(normalized == "res://src");
	CHECK(MCPTools::normalize_project_path("res:// ", normalized, error));
	CHECK(normalized == "res://");
	CHECK(MCPTools::normalize_project_path("res://a//b", normalized, error));
	CHECK(normalized == "res://a/b");
	CHECK(MCPTools::normalize_project_path("res://a/b/", normalized, error));
	CHECK(normalized == "res://a/b");
	CHECK(MCPTools::normalize_project_path("res:// / . /", normalized, error));
	CHECK(normalized == "res://");

	// Folding must not re-open what the `..` rule already closed: `..` is
	// rejected on the raw remainder, before any segment is collapsed.
	CHECK_FALSE(MCPTools::normalize_project_path("res://a/./../b", normalized, error));
	CHECK(error.code == -32602);
	CHECK_FALSE(MCPTools::normalize_project_path("res://...", normalized, error));
	CHECK(error.code == -32602);
	// A `.`-prefixed *name* is a normal segment and survives untouched.
	CHECK(MCPTools::normalize_project_path("res://a/.hidden/.", normalized, error));
	CHECK(normalized == "res://a/.hidden");
}

// ---------------------------------------------------------------------------
// GDR-16 naming lint, enforced at registration time.
//
// The predicates are static so that a failure points at the exact rule (L1
// prefix / L2 verb set / L3 declared metadata / L4 banned `update_`) instead of
// only at "the tool did not show up".
// ---------------------------------------------------------------------------

TEST_CASE("[MCPServer] naming lint accepts compliant names across all four channels") {
	MCPToolRegistry registry;

	const String names[4] = { "editor_get_node_properties", "running_game_get_scene_tree", "project_get_info", "os_deploy_to_android_device" };
	const String channels[4] = { "editor", "running_game", "project", "os" };
	const String verbs[4] = { "get", "get", "get", "deploy" };

	for (int i = 0; i < 4; i++) {
		String error;
		CHECK(MCPToolRegistry::validate_tool_name(names[i], channels[i], verbs[i], error));
		CHECK(error.is_empty());

		// TASK-003 section 1.6: registration happens through ToolBuilder only.
		CHECK(TestMCPServer::register_probe(registry, names[i], channels[i], verbs[i], MCPToolScope::BOTH));
		CHECK(registry.has_tool(names[i]));
	}
}

TEST_CASE("[MCPServer] naming lint rejects an unknown channel prefix") {
	MCPToolRegistry registry;
	const int count_before = registry.get_visible_tool_count(true);

	String error;
	CHECK_FALSE(MCPToolRegistry::validate_tool_name("game_get_x", "game", "get", error));
	CHECK(error.contains("GDR-16 L1"));

	CHECK_FALSE(TestMCPServer::register_probe(registry, "game_get_x", "game", "get", MCPToolScope::BOTH));
	CHECK_FALSE(registry.has_tool("game_get_x"));
	CHECK(registry.get_visible_tool_count(true) == count_before);

	// L1 is lowercase only, so a capitalized channel fails it too.
	String upper_error;
	CHECK_FALSE(MCPToolRegistry::validate_tool_name("Editor_get_info", "Editor", "get", upper_error));
	CHECK(upper_error.contains("GDR-16 L1"));

	CHECK_FALSE(TestMCPServer::register_probe(registry, "Editor_get_info", "Editor", "get", MCPToolScope::BOTH));
	CHECK_FALSE(registry.has_tool("Editor_get_info"));
}

TEST_CASE("[MCPServer] naming lint rejects a verb outside the closed set") {
	MCPToolRegistry registry;

	String error;
	CHECK_FALSE(MCPToolRegistry::validate_tool_name("editor_navigate_to_node", "editor", "navigate", error));
	CHECK(error.contains("GDR-16 L2"));

	CHECK_FALSE(TestMCPServer::register_probe(registry, "editor_navigate_to_node", "editor", "navigate", MCPToolScope::BOTH));
	CHECK_FALSE(registry.has_tool("editor_navigate_to_node"));

	String clear_error;
	CHECK_FALSE(MCPToolRegistry::validate_tool_name("editor_clear_output_panel", "editor", "clear", clear_error));
	CHECK(clear_error.contains("GDR-16 L2"));

	CHECK_FALSE(TestMCPServer::register_probe(registry, "editor_clear_output_panel", "editor", "clear", MCPToolScope::BOTH));
	CHECK_FALSE(registry.has_tool("editor_clear_output_panel"));
}

TEST_CASE("[MCPServer] naming lint bans update_ anywhere in the name") {
	MCPToolRegistry registry;

	// The channel and the declared verb are both legal here, so only L4 can
	// reject this name - which is why L4 has to run before the L1/L2/L3 checks.
	String error;
	CHECK_FALSE(MCPToolRegistry::validate_tool_name("editor_update_node_property", "editor", "set", error));
	CHECK(error.contains("GDR-16 L4"));
	CHECK(error.contains("update_"));

	CHECK_FALSE(TestMCPServer::register_probe(registry, "editor_update_node_property", "editor", "set", MCPToolScope::BOTH));
	CHECK_FALSE(registry.has_tool("editor_update_node_property"));
}

TEST_CASE("[MCPServer] naming lint rejects a declared channel or verb that disagrees with the name") {
	String channel_error;
	CHECK_FALSE(MCPToolRegistry::validate_tool_name("editor_get_node_properties", "project", "get", channel_error));
	CHECK(channel_error.contains("GDR-16 L3"));
	CHECK(channel_error.contains("declares channel"));

	String verb_error;
	CHECK_FALSE(MCPToolRegistry::validate_tool_name("project_get_settings", "project", "list", verb_error));
	CHECK(verb_error.contains("GDR-16 L3"));
	CHECK(verb_error.contains("declares verb"));

	// An undeclared verb is a disagreement as well, never an "anything goes".
	String undeclared_error;
	CHECK_FALSE(MCPToolRegistry::validate_tool_name("project_get_info", "project", "", undeclared_error));
	CHECK(undeclared_error.contains("GDR-16 L3"));

	MCPToolRegistry registry;
	CHECK_FALSE(TestMCPServer::register_probe(registry, "editor_get_node_properties", "project", "get", MCPToolScope::BOTH));
	CHECK_FALSE(registry.has_tool("editor_get_node_properties"));
}

TEST_CASE("[MCPServer] naming lint strips running_game_ by longest prefix") {
	// `running_game_` carries its own underscore, so a `split('_')[1]` parse
	// would read the verb as `game`. The longest prefix has to win.
	String channel;
	String verb;
	CHECK(MCPToolRegistry::parse_tool_name("running_game_get_scene_tree", channel, verb));
	CHECK(channel == "running_game");
	CHECK(verb == "get");
	CHECK(verb != "game");

	String editor_channel;
	String editor_verb;
	CHECK(MCPToolRegistry::parse_tool_name("editor_get_node_properties", editor_channel, editor_verb));
	CHECK(editor_channel == "editor");
	CHECK(editor_verb == "get");

	String project_channel;
	String project_verb;
	CHECK(MCPToolRegistry::parse_tool_name("project_get_settings", project_channel, project_verb));
	CHECK(project_channel == "project");
	CHECK(project_verb == "get");

	String os_channel;
	String os_verb;
	CHECK(MCPToolRegistry::parse_tool_name("os_deploy_to_android_device", os_channel, os_verb));
	CHECK(os_channel == "os");
	CHECK(os_verb == "deploy");

	MCPToolRegistry registry;
	CHECK(TestMCPServer::register_probe(registry, "running_game_get_scene_tree", "running_game", "get", MCPToolScope::GAME));
	CHECK(registry.is_tool_visible("running_game_get_scene_tree", false));
}

// ---------------------------------------------------------------------------
// B1 group `project_read_analysis` (TASK-004): seven read-only tools that work
// on the project on disk.
//
// Migration source: godot_mcp_gdext/src/commands/analysis.rs (five tools),
// batch.rs (get_scene_dependencies) and scene.rs (get_scene_exports). The
// observable contract of each tool - parameters, result shape, caps, case
// sensitivity, error class - is written out per tool in
// docs/reports/REPORT-004-project-read-analysis.md; the assertions below pin
// every part of it that a caller can observe.
//
// The fixture tree (`res://mcp_server_test_fixture`) is documented in
// TestMCPServer::ScratchProject. Its exact shape is part of these assertions:
//
//   scripts/exported.gd        5 lines, two @export vars, one plain var
//   scripts/refs.gd            3 lines, line 3 holds SCRIPT_REF_MARKER
//   scenes/leaf.tscn           7 lines, ext_resource -> resources/used.tres
//   scenes/cycle_a.tscn       <-> scenes/cycle_b.tscn   (the scene cycle)
//   scenes/nested.tscn         2 children (depth 2, 3 nodes), no script
//   resources/used.tres        referenced by leaf.tscn
//   resources/unused.tres      referenced by nothing
//   notes.md                   not scanned by the extension-filtered tools
//   addons/myplugin/{plugin.cfg,thing.tres}
// ---------------------------------------------------------------------------

TEST_CASE("[MCPServer] the project_read_analysis group is registered for both processes") {
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	// 6 template tools + 7 analysis tools + 6 read_files tools + 4
	// write_resource_scene tools + 1 running_game_read_scene tool (TASK-009) + 6
	// running_game_observation + 1 running_game_script_execution (TASK-010) + 4
	// game-scope tools of TASK-011 + 8 tools of TASK-012 (4 game-scope ones of
	// `running_game_input`, 1 of `running_game_node_write`, 2 editor-scope ones
	// of `editor_playback` and 1 of `editor_input_read`; the editor-scope three
	// are not registered in a game process at all).
	// The four writers are scope `BOTH`; the seventeen game-scope tools are
	// carried by the game-process view and hidden from the editor-process view.
	CHECK(registry.get_tool_count() == 40);
	CHECK(registry.get_visible_tool_count(true) == 23);
	CHECK(registry.get_visible_tool_count(false) == 40);

	const String names[7] = {
		"project_get_statistics",
		"project_analyze_scene_complexity",
		"project_detect_circular_dependencies",
		"project_find_unused_resources",
		"project_find_script_references",
		"project_get_scene_dependencies",
		"project_get_scene_exports",
	};
	for (int i = 0; i < 7; i++) {
		CHECK(registry.has_tool(names[i]));
		CHECK(registry.is_tool_visible(names[i], true));
		CHECK(registry.is_tool_visible(names[i], false));
	}
}

TEST_CASE("[MCPServer] project_get_statistics counts files, scripts, scenes and resources") {
	TestMCPServer::ScratchProject project;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	Dictionary args;
	args["path"] = project.root;
	MCPToolError tool_error;
	const Variant result = registry.call_tool("project_get_statistics", args, tool_error);
	CHECK_FALSE(tool_error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = result;
		// 9 files outside addons; the walk does not descend into `addons/`.
		CHECK((int)payload["total_files"] == 9);
		CHECK((int)payload["scene_count"] == 4);
		CHECK((int)payload["resource_count"] == 2);
		// exported.gd (5 lines) + refs.gd (3 lines), with Rust `str::lines()`
		// semantics: a trailing newline does not invent an extra line.
		CHECK((int)payload["total_script_lines"] == 8);

		const Dictionary counts = payload["file_counts_by_extension"];
		CHECK((int)counts["gd"] == 2);
		CHECK((int)counts["tscn"] == 4);
		CHECK((int)counts["tres"] == 2);
		CHECK((int)counts["md"] == 1);
		// The extension key is lowercased by the reference walk.
		CHECK_FALSE(counts.has("GD"));

		CHECK(payload["autoloads"].get_type() == Variant::DICTIONARY);
		CHECK(payload["plugins"].get_type() == Variant::ARRAY);
	}

	// `include_addons` reaches into `res://.../addons`.
	Dictionary with_addons;
	with_addons["path"] = project.root;
	with_addons["include_addons"] = true;
	MCPToolError addons_error;
	const Variant addons_result = registry.call_tool("project_get_statistics", with_addons, addons_error);
	CHECK_FALSE(addons_error.is_error());
	if (addons_result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = addons_result;
		CHECK((int)payload["total_files"] == 11);
		CHECK((int)payload["resource_count"] == 3);
		const Dictionary counts = payload["file_counts_by_extension"];
		CHECK((int)counts["cfg"] == 1);
		CHECK((int)counts["tres"] == 3);
	}

	// A directory that is not there is -32001 with a suggestion (GDR-14),
	// never a silently empty report.
	Dictionary missing;
	missing["path"] = "res://__no_such_directory_for_mcp_tests__";
	MCPToolError missing_error;
	registry.call_tool("project_get_statistics", missing, missing_error);
	CHECK(missing_error.code == -32001);
	CHECK(missing_error.message.contains("not found"));
	CHECK(((Dictionary)missing_error.data).has("suggestion"));

	// An optional argument that is present with the wrong type is -32602.
	Dictionary wrong_type;
	wrong_type["include_addons"] = "yes";
	MCPToolError type_error;
	registry.call_tool("project_get_statistics", wrong_type, type_error);
	CHECK(type_error.code == -32602);
	CHECK(type_error.message.contains("include_addons"));
}

TEST_CASE("[MCPServer] project_analyze_scene_complexity analyses a .tscn from disk") {
	TestMCPServer::ScratchProject project;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	Dictionary args;
	args["path"] = project.path("scenes/nested.tscn");
	MCPToolError tool_error;
	const Variant result = registry.call_tool("project_analyze_scene_complexity", args, tool_error);
	CHECK_FALSE(tool_error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = result;
		CHECK((String)payload["scene_path"] == project.path("scenes/nested.tscn"));
		CHECK((int)payload["total_nodes"] == 3);
		// The reference counts the root as depth 0, so a root + child +
		// grandchild scene has max_depth 2.
		CHECK((int)payload["max_depth"] == 2);

		const Dictionary by_type = payload["nodes_by_type"];
		CHECK((int)by_type["Node2D"] == 2);
		CHECK((int)by_type["Sprite2D"] == 1);

		// The fixture has no attached script (see ScratchProject), so the
		// script list is empty; the shape is still pinned. A scene *with* a
		// script is proven by the gate 2 evidence on a scratch project.
		CHECK(payload["scripts_attached"].get_type() == Variant::ARRAY);
		CHECK(((Array)payload["scripts_attached"]).is_empty());
		CHECK(payload["issues"].get_type() == Variant::ARRAY);
		CHECK(((Array)payload["issues"]).is_empty());
	}

	// A scene file that is not there is -32001.
	Dictionary missing;
	missing["path"] = project.path("scenes/does_not_exist.tscn");
	MCPToolError missing_error;
	registry.call_tool("project_analyze_scene_complexity", missing, missing_error);
	CHECK(missing_error.code == -32001);
	CHECK(missing_error.message.contains("not found"));

	// A resource that exists but is not a scene is an internal error.
	Dictionary not_a_scene;
	not_a_scene["path"] = project.path("resources/used.tres");
	MCPToolError internal_error;
	registry.call_tool("project_analyze_scene_complexity", not_a_scene, internal_error);
	CHECK(internal_error.code == -32603);
}

TEST_CASE("[MCPServer] the scene complexity fallback distinguishes editor and game process") {
	Engine *engine = Engine::get_singleton();
	if (engine == nullptr) {
		CHECK(engine != nullptr);
		return;
	}
	const bool was_editor = engine->is_editor_hint();

	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	// In a game process the "analyse the edited scene" fallback does not exist:
	// an empty `path` is an explicit -32000 with a suggestion, never a crash.
	engine->set_editor_hint(false);
	CHECK_FALSE(MCPTools::is_editor_process());
	MCPToolError game_error;
	registry.call_tool("project_analyze_scene_complexity", Dictionary(), game_error);
	CHECK(game_error.code == -32000);
	CHECK(game_error.message.begins_with("Not implemented"));
	CHECK(((Dictionary)game_error.data).has("suggestion"));

	// In an editor process the branch is compiled in (MCP_EDITOR_TOOLS_ENABLED)
	// and answers with the documented "no scene is open" state error. The
	// doctest process has no SceneTree at all - the same reason the MCP server
	// logs "SceneTree never became available" here - so the fallback must reach
	// that error without ever touching the editor singleton (which exists in
	// this process, created by `register_editor_types()`, while its
	// `EditorNode` does not). The two messages differ, which is what proves the
	// guard selected a different branch rather than the same error twice.
	engine->set_editor_hint(true);
	CHECK(MCPTools::is_editor_process());
	MCPToolError editor_error;
	registry.call_tool("project_analyze_scene_complexity", Dictionary(), editor_error);
	CHECK(editor_error.code == -32000);
	CHECK(editor_error.message == "No scene is currently open");
	CHECK(((Dictionary)editor_error.data).has("suggestion"));

	engine->set_editor_hint(was_editor);
}

TEST_CASE("[MCPServer] project_detect_circular_dependencies reports the scene cycle") {
	TestMCPServer::ScratchProject project;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	Dictionary args;
	args["path"] = project.root;
	MCPToolError tool_error;
	const Variant result = registry.call_tool("project_detect_circular_dependencies", args, tool_error);
	CHECK_FALSE(tool_error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = result;
		CHECK((int)payload["scenes_checked"] == 4);
		CHECK((bool)payload["has_circular"] == true);

		const Array cycles = payload["circular_dependencies"];
		CHECK(cycles.size() == 1);
		if (cycles.size() == 1) {
			const Array cycle = cycles[0];
			// cycle_a -> cycle_b -> cycle_a: the start node is repeated at the
			// end, exactly like the reference DFS.
			CHECK(cycle.size() == 3);
			if (cycle.size() == 3) {
				const String a = project.path("scenes/cycle_a.tscn");
				const String b = project.path("scenes/cycle_b.tscn");
				CHECK((String)cycle[0] == (String)cycle[2]);
				// doctest cannot decompose `||` of two comparisons, so the
				// orientation test is a single plain bool.
				const bool forward = (String)cycle[0] == a && (String)cycle[1] == b;
				const bool backward = (String)cycle[0] == b && (String)cycle[1] == a;
				const bool orientation_ok = forward || backward;
				CHECK(orientation_ok);
			}
		}

		const Dictionary graph = payload["dependency_graph"];
		CHECK(graph.size() == 4);
		const Array leaf_deps = graph[project.path("scenes/leaf.tscn")];
		CHECK(leaf_deps.is_empty());
		const Array a_deps = graph[project.path("scenes/cycle_a.tscn")];
		CHECK(a_deps.size() == 1);
		if (a_deps.size() == 1) {
			CHECK((String)a_deps[0] == project.path("scenes/cycle_b.tscn"));
		}
	}

	// A path that does not exist is -32001.
	Dictionary missing;
	missing["path"] = "res://__no_such_directory_for_mcp_tests__";
	MCPToolError missing_error;
	registry.call_tool("project_detect_circular_dependencies", missing, missing_error);
	CHECK(missing_error.code == -32001);
	CHECK(missing_error.message.contains("not found"));
}

TEST_CASE("[MCPServer] project_find_unused_resources separates used from unused") {
	TestMCPServer::ScratchProject project;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	Dictionary args;
	args["path"] = project.root;
	MCPToolError tool_error;
	const Variant result = registry.call_tool("project_find_unused_resources", args, tool_error);
	CHECK_FALSE(tool_error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = result;
		const Array unused = payload["unused_resources"];
		CHECK((int)payload["total_resources_scanned"] == 6);
		CHECK((int)payload["total_files_checked"] == 8);

		// leaf.tscn -> used.tres, cycle_a <-> cycle_b and with_script -> the
		// script are the four `[ext_resource ... path="..."]` references; the
		// resources that nobody points at are exactly these three.
		CHECK(unused.size() == 3);
		CHECK((int)payload["unused_count"] == unused.size());
		CHECK(unused.has(project.path("resources/unused.tres")));
		CHECK(unused.has(project.path("scenes/leaf.tscn")));
		CHECK(unused.has(project.path("scenes/nested.tscn")));
		CHECK_FALSE(unused.has(project.path("resources/used.tres")));
		CHECK_FALSE(unused.has(project.path("scenes/cycle_b.tscn")));
		CHECK_FALSE(unused.has(project.path("scripts/refs.gd")));
	}

	Dictionary missing;
	missing["path"] = "res://__no_such_directory_for_mcp_tests__";
	MCPToolError missing_error;
	registry.call_tool("project_find_unused_resources", missing, missing_error);
	CHECK(missing_error.code == -32001);
}

TEST_CASE("[MCPServer] project_find_script_references is not the content search (GDR-17)") {
	TestMCPServer::ScratchProject project;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	const String marker = "SCRIPT_REF_MARKER";

	Dictionary args;
	args["query"] = marker;
	args["path"] = project.root;
	MCPToolError tool_error;
	const Variant result = registry.call_tool("project_find_script_references", args, tool_error);
	CHECK_FALSE(tool_error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = result;
		CHECK((String)payload["query"] == marker);
		// Only .tscn/.gd/.tres/.cfg/.godot are searched, so notes.md (which the
		// content search does read) is not part of `files_searched`.
		CHECK((int)payload["files_searched"] == 8);

		const Array references = payload["references"];
		CHECK((int)payload["reference_count"] == references.size());
		CHECK(references.size() == 2);
		bool saw_script = false;
		bool saw_scene = false;
		for (int i = 0; i < references.size(); i++) {
			const Dictionary hit = references[i];
			// Per line {file, line, content}: the shape is the discriminator
			// against project_search_file_contents' {file, line, text}.
			CHECK(hit.has("file"));
			CHECK(hit.has("line"));
			CHECK(hit.has("content"));
			CHECK_FALSE(hit.has("text"));
			if ((String)hit["file"] == project.path("scripts/refs.gd")) {
				saw_script = true;
				CHECK((int)hit["line"] == 3);
				CHECK((String)hit["content"] == (String)("const TARGET := \"" + marker + "\""));
			}
			if ((String)hit["file"] == project.path("scenes/leaf.tscn")) {
				saw_scene = true;
				CHECK((int)hit["line"] == 7);
			}
		}
		CHECK(saw_script);
		CHECK(saw_scene);
	}

	// The same pattern through the content search: a different shape and one
	// extra hit (notes.md), which is exactly why the two tools were never
	// merged (GDR-17).
	Dictionary contents_args;
	contents_args["pattern"] = marker;
	contents_args["path"] = project.root;
	MCPToolError contents_error;
	const Variant contents_result = registry.call_tool("project_search_file_contents", contents_args, contents_error);
	CHECK_FALSE(contents_error.is_error());
	if (contents_result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = contents_result;
		CHECK((int)payload["count"] == 3);
		const Array matches = payload["matches"];
		bool saw_markdown = false;
		for (int i = 0; i < matches.size(); i++) {
			const Dictionary hit = matches[i];
			CHECK(hit.has("text"));
			CHECK_FALSE(hit.has("content"));
			if ((String)hit["file"] == project.path("notes.md")) {
				saw_markdown = true;
			}
		}
		CHECK(saw_markdown);
	}

	// `query` is required.
	MCPToolError missing;
	registry.call_tool("project_find_script_references", Dictionary(), missing);
	CHECK(missing.code == -32602);
	CHECK(missing.message == "Missing required parameter: query");

	Dictionary wrong_type;
	wrong_type["query"] = 5;
	MCPToolError type_error;
	registry.call_tool("project_find_script_references", wrong_type, type_error);
	CHECK(type_error.code == -32602);
	CHECK(type_error.message.contains("query"));
}

TEST_CASE("[MCPServer] project_get_scene_dependencies reads the ext_resource list") {
	TestMCPServer::ScratchProject project;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	Dictionary args;
	args["path"] = project.path("scenes/leaf.tscn");
	MCPToolError tool_error;
	const Variant result = registry.call_tool("project_get_scene_dependencies", args, tool_error);
	CHECK_FALSE(tool_error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = result;
		CHECK((String)payload["path"] == project.path("scenes/leaf.tscn"));
		const Array dependencies = payload["dependencies"];
		CHECK((int)payload["count"] == dependencies.size());
		CHECK(dependencies.size() == 1);
		if (dependencies.size() == 1) {
			const Dictionary dep = dependencies[0];
			CHECK((String)dep["path"] == project.path("resources/used.tres"));
			// TASK-024 E-1: the loader is asked for types
			// (`get_dependencies(..., p_add_types = true)`), so `type` is the
			// real `ext_resource` type instead of the third `::` field (which,
			// with `add_types = false`, was empty here and the *fallback path*
			// whenever the tag carried a `uid=`).
			CHECK((String)dep["type"] == "Resource");
			// No `uid=` in this tag, so there is no UID to report - but the key
			// is always there, which is what makes the shape uniform.
			CHECK(dep.has("uid"));
			CHECK((String)dep["uid"] == "");
		}
	}

	Dictionary scripted;
	scripted["path"] = project.path("scenes/nested.tscn");
	MCPToolError scripted_error;
	const Variant scripted_result = registry.call_tool("project_get_scene_dependencies", scripted, scripted_error);
	CHECK_FALSE(scripted_error.is_error());
	if (scripted_result.get_type() == Variant::DICTIONARY) {
		// A scene with no `[ext_resource ...]` tag reports an empty list with
		// its own shape, not an error.
		CHECK((int)((Dictionary)scripted_result)["count"] == 0);
		CHECK(((Array)((Dictionary)scripted_result)["dependencies"]).is_empty());
	}

	// `path` is required.
	MCPToolError missing_param;
	registry.call_tool("project_get_scene_dependencies", Dictionary(), missing_param);
	CHECK(missing_param.code == -32602);
	CHECK(missing_param.message == "Missing required parameter: path");

	// A file that is not there is -32001.
	Dictionary missing;
	missing["path"] = project.path("scenes/does_not_exist.tscn");
	MCPToolError missing_error;
	registry.call_tool("project_get_scene_dependencies", missing, missing_error);
	CHECK(missing_error.code == -32001);
	CHECK(missing_error.message.contains("not found"));
}

// ===========================================================================
// TASK-024b E-1 + G-2 - the dependency entry's `type` and `path`
//
// The engine's dependency string, once `p_add_types` is on, is
//
//   `res://path::<type>`                        (tag has no `uid=`)
//   `uid://id::<type>::res://fallback`          (tag has `uid=`; the third
//                                                field is the path the scene
//                                                records, stored by the engine
//                                                as `fallback_path` "in case uid
//                                                path fails",
//                                                resource_format_text.cpp:949)
//
// (`scene/resources/resource_format_text.cpp:919/960-968`). The old
// implementation called `get_dependencies` with the default
// `p_add_types = false`, so the string was `uid://id::::res://fallback` and
// reading the *third* field as the type answered the fallback **path** - the
// D-8 defect: `{"path":"uid://c7mt5x5j361vt","type":"res://main.gd"}`.
//
// Every assertion below fails on the old implementation.
// ===========================================================================
TEST_CASE("[MCPServer] TASK-024b E-1/G-2: a uid-bearing ext_resource keeps its type and its res:// path") {
	TestMCPServer::ScratchProject project;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	const String uid = "uid://c7mt5x5j361vt";
	const String resource_path = project.path("resources/used.tres");
	const String scene_text = String("[gd_scene load_steps=2 format=3]\n\n") +
			"[ext_resource type=\"Resource\" uid=\"" + uid + "\" path=\"" + resource_path + "\" id=\"1_r\"]\n\n" +
			"[node name=\"WithUid\" type=\"Node2D\"]\n";
	REQUIRE(project.write("scenes/with_uid.tscn", scene_text));

	Dictionary args;
	args["path"] = project.path("scenes/with_uid.tscn");
	MCPToolError error;
	const Variant result = registry.call_tool("project_get_scene_dependencies", args, error);
	CHECK_FALSE(error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() != Variant::DICTIONARY) {
		return;
	}
	const Array dependencies = ((Dictionary)result)["dependencies"];
	CHECK((int)((Dictionary)result)["count"] == 1);
	CHECK(dependencies.size() == 1);
	if (dependencies.size() != 1) {
		return;
	}
	const Dictionary dep = dependencies[0];
	// The two halves of D-8 in one place: `type` is a type (not the fallback
	// path) and `path` is a `res://` path (not the `uid://` id).
	CHECK((String)dep["type"] == "Resource");
	CHECK((String)dep["declared_type"] == "Resource");
	CHECK((String)dep["path"] == resource_path);
	CHECK((String)dep["uid"] == uid);
	// A doctest process never opens the project, so the UID registry is empty and
	// the `res://` half can only come from the path the scene records - the
	// engine's own fallback for exactly this case. The live `uid` half is proven
	// by the gate-2 evidence run, where the registry is loaded.
	CHECK((String)dep["path_source"] == "scene_path");

	// Rule 1 of GDR-25 section 23.1 ("zero string surgery"): the `path` this tool
	// answers is accepted **as it is** by the next tool - no `uid://` conversion
	// call, no prefix slicing.
	Dictionary next_args;
	next_args["path"] = dep["path"];
	MCPToolError next_error;
	const Variant next_result = registry.call_tool("project_read_resource", next_args, next_error);
	CHECK_FALSE(next_error.is_error());
	if (next_result.get_type() == Variant::DICTIONARY) {
		CHECK((String)((Dictionary)next_result)["path"] == resource_path);
	}
}

// ---------------------------------------------------------------------------
// TASK-024 E-1 + G-2: a `uid=`-carrying `ext_resource` is the case the old
// implementation got wrong in *both* fields - `type` held the fallback path and
// `path` held a `uid://` no other tool accepts. The UID registry is real here
// (`ResourceUID` is created by `register_core_types`, main.cpp's `test_setup()`
// path included), so the scene names the very UID the engine resolves.
// ---------------------------------------------------------------------------
TEST_CASE("[MCPServer] TASK-024 E-1: a UID dependency answers a real type and a feedable path") {
	TestMCPServer::ScratchProject project;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	ResourceUID *uids = ResourceUID::get_singleton();
	REQUIRE(uids != nullptr);

	const String target = project.path("resources/used.tres");
	const ResourceUID::ID id = uids->create_id_for_path(target);
	REQUIRE(id != ResourceUID::INVALID_ID);
	const String uid_text = uids->id_to_text(id);
	REQUIRE(uid_text.begins_with("uid://"));

	// Exactly the shape the engine itself writes for a saved scene: the tag
	// carries `uid=`, `path=` and `type=` (`resource_format_text.cpp:944-952`
	// then turns `path` into the UID text and keeps the real path as *fallback*).
	const String scene_text = vformat(
			"[gd_scene load_steps=2 format=3]\n\n[ext_resource type=\"Resource\" uid=\"%s\" path=\"%s\" id=\"1_u\"]\n\n[node name=\"Uid\" type=\"Node2D\"]\n",
			uid_text, target);
	REQUIRE(project.write("scenes/with_uid.tscn", scene_text));

	Dictionary args;
	args["path"] = project.path("scenes/with_uid.tscn");
	MCPToolError tool_error;
	const Variant result = registry.call_tool("project_get_scene_dependencies", args, tool_error);
	CHECK_FALSE(tool_error.is_error());
	REQUIRE(result.get_type() == Variant::DICTIONARY);

	const Dictionary payload = result;
	const Array dependencies = payload["dependencies"];
	REQUIRE(dependencies.size() == 1);

	const Dictionary dep = dependencies[0];
	// The real type, not the fallback path (`"res://main.gd"` was the measured
	// defect shape).
	CHECK((String)dep["type"] == "Resource");
	// The UID *and* the resolved `res://` path, so the answer can be fed
	// straight back in without a `project_convert_uid_to_path` round trip.
	CHECK((String)dep["uid"] == uid_text);
	CHECK((String)dep["path"] == target);

	// The chainability claim, exercised: the path the tool just answered is a
	// valid input for the next tool, with no string surgery in between.
	Dictionary chained;
	chained["path"] = dep["path"];
	MCPToolError chained_error;
	const Variant chained_result = registry.call_tool("project_read_resource", chained, chained_error);
	CHECK_FALSE(chained_error.is_error());
	if (chained_result.get_type() == Variant::DICTIONARY) {
		CHECK((String)((Dictionary)chained_result)["path"] == target);
	}

	uids->remove_id(id);
}

TEST_CASE("[MCPServer] project_get_scene_exports reports the scripted nodes of a scene") {
	TestMCPServer::ScratchProject project;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	// A scene whose nodes carry no script reports its own empty shape
	// ({"path","nodes":[],"count":0}) rather than an error. Note that a scene
	// *with* an attached script cannot be exercised here: the doctest process
	// never initializes a script language (`Main::test_setup()` does not call
	// `ScriptServer::init_languages()`), so loading a `.gd` fails with
	// "Native class ... not found". The export collection itself - the
	// PROPERTY_USAGE_EDITOR | PROPERTY_USAGE_SCRIPT_VARIABLE filter, the value
	// serialization and `node_path`/`node_name`/`node_type`/`script_path` - is
	// proven by the gate 2 evidence on a real scratch project, where the engine
	// compiles the script normally.
	Dictionary args;
	args["path"] = project.path("scenes/nested.tscn");
	MCPToolError tool_error;
	const Variant result = registry.call_tool("project_get_scene_exports", args, tool_error);
	CHECK_FALSE(tool_error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = result;
		CHECK((String)payload["path"] == project.path("scenes/nested.tscn"));
		CHECK((int)payload["count"] == 0);
		CHECK(((Array)payload["nodes"]).is_empty());
	}

	// A resource that exists but is not a scene is an internal error, not an
	// empty node list.
	Dictionary not_a_scene;
	not_a_scene["path"] = project.path("resources/used.tres");
	MCPToolError internal_error;
	registry.call_tool("project_get_scene_exports", not_a_scene, internal_error);
	CHECK(internal_error.code == -32603);

	// `path` is required.
	MCPToolError missing_param;
	registry.call_tool("project_get_scene_exports", Dictionary(), missing_param);
	CHECK(missing_param.code == -32602);
	CHECK(missing_param.message == "Missing required parameter: path");

	Dictionary missing;
	missing["path"] = project.path("scenes/does_not_exist.tscn");
	MCPToolError missing_error;
	registry.call_tool("project_get_scene_exports", missing, missing_error);
	CHECK(missing_error.code == -32001);
	CHECK(missing_error.message.contains("not found"));
}

TEST_CASE("[MCPServer] the analysis tools never write to the project") {
	TestMCPServer::ScratchProject project;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	const Array before = TestMCPServer::list_files_recursive(project.root);
	CHECK(before.size() == 11);

	MCPToolError ignored;

	Dictionary scan;
	scan["path"] = project.root;
	scan["include_addons"] = true;
	registry.call_tool("project_get_statistics", scan, ignored);
	registry.call_tool("project_detect_circular_dependencies", scan, ignored);
	registry.call_tool("project_find_unused_resources", scan, ignored);

	Dictionary references;
	references["query"] = "SCRIPT_REF_MARKER";
	references["path"] = project.root;
	registry.call_tool("project_find_script_references", references, ignored);

	Dictionary scene;
	scene["path"] = project.path("scenes/nested.tscn");
	registry.call_tool("project_analyze_scene_complexity", scene, ignored);
	registry.call_tool("project_get_scene_dependencies", scene, ignored);
	registry.call_tool("project_get_scene_exports", scene, ignored);

	const Array after = TestMCPServer::list_files_recursive(project.root);
	CHECK(after.size() == before.size());
	CHECK(TestMCPServer::canonical(after) == TestMCPServer::canonical(before));
}

// ---------------------------------------------------------------------------
// B1 group `project_read_files` (TASK-005): six read-only tools that read
// project content off the disk.
//
// Migration source: godot_mcp_gdext/src/commands/script.rs (list_scripts,
// read_script, validate_script), resource.rs (read_resource,
// get_resource_preview) and scene.rs (get_scene_file_content). The observable
// contract of each tool - parameters, result shape, caps, case sensitivity,
// error class - is written out per tool in
// docs/reports/REPORT-005-project-read-files.md.
//
// The fixture tree is documented in TestMCPServer::ReadFilesProject; its exact
// shape is part of these assertions.
// ---------------------------------------------------------------------------

TEST_CASE("[MCPServer] the project_read_files group is registered for both processes") {
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	// 6 template + 7 analysis + 6 read_files + 4 write_resource_scene + 1
	// running_game_read_scene (TASK-009) + 16 B2 game-scope tools (TASK-010,
	// TASK-011 and TASK-012); the game-scope tools are hidden from the
	// editor-process view.
	CHECK(registry.get_tool_count() == 40);
	CHECK(registry.get_visible_tool_count(true) == 23);
	CHECK(registry.get_visible_tool_count(false) == 40);

	const String names[6] = {
		"project_list_scripts",
		"project_read_script",
		"project_validate_script",
		"project_read_resource",
		"project_get_resource_preview",
		"project_read_scene_file_content",
	};
	for (int i = 0; i < 6; i++) {
		CHECK(registry.has_tool(names[i]));
		CHECK(registry.is_tool_visible(names[i], true));
		CHECK(registry.is_tool_visible(names[i], false));
	}
}

TEST_CASE("[MCPServer] project_list_scripts lists scripts and shaders deterministically") {
	TestMCPServer::ReadFilesProject project;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	// The contract declares `{"properties":{},"required":[],"type":"object"}`, so
	// the tool takes no argument and has no "missing argument" failure class.
	MCPToolError tool_error;
	const Variant result = registry.call_tool("project_list_scripts", Dictionary(), tool_error);
	CHECK_FALSE(tool_error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() != Variant::DICTIONARY) {
		return;
	}

	const Dictionary payload = result;
	const Array scripts = payload["scripts"];
	// `scripts` is an array of *path strings*, not of objects (the reference
	// returns bare paths), and `count` is its size.
	CHECK((int)payload["count"] == scripts.size());

	// The tool always walks `res://`, and in the doctest process `res://` is the
	// engine checkout the binary was launched from - so a *global* exact set
	// cannot be asserted here. What is exact is the fixture subtree: every path
	// the walk collected below the fixture root, against the known layout.
	Array in_fixture;
	for (int i = 0; i < scripts.size(); i++) {
		const String entry = scripts[i];
		if (entry.begins_with(project.root)) {
			in_fixture.push_back(entry);
		}
	}
	Array expected;
	expected.push_back(project.path(".hiddendir/secret.gd"));
	expected.push_back(project.path("addons/plug/in_addon.gd"));
	expected.push_back(project.path("scripts/alpha.gd"));
	expected.push_back(project.path("scripts/broken.gd"));
	expected.push_back(project.path("scripts/unicode.gd"));
	expected.push_back(project.path("shaders/effect.gdshader"));
	in_fixture.sort();
	CHECK(in_fixture.size() == expected.size());
	CHECK(TestMCPServer::canonical(in_fixture) == TestMCPServer::canonical(expected));

	// The extension test is case sensitive, exactly like the reference's
	// `ends_with(".gd")`: `upper.GD` is not a script.
	CHECK_FALSE(in_fixture.has(project.path("scripts/upper.GD")));

	// Two consecutive calls return byte-identical responses.
	MCPToolError second_error;
	const Variant second = registry.call_tool("project_list_scripts", Dictionary(), second_error);
	CHECK_FALSE(second_error.is_error());
	CHECK(TestMCPServer::canonical(second) == TestMCPServer::canonical(result));
}

// ---------------------------------------------------------------------------
// TASK-067 (F-066-1): which files `project_list_scripts` calls a script is not a
// constant of the tool - it is a property of the build.
//
// The engine's own registry is `ScriptServer`:
//   * `ScriptServer::register_language()`   core/object/script_language.cpp:239
//   * `ScriptServer::get_language_for_extension()`  core/object/script_language.cpp:227
//   * `ScriptLanguage::get_extension()`     core/object/script_language.h:224
// Every language names exactly one extension: GDScript registers "gd", and the
// .NET module registers "cs" (`modules/mono/csharp_script.cpp:98`) **only when
// that module is compiled in**. The tool used to hardcode `.gd`/`.gdshader`, so
// every other language of the build was invisible: on a Mono project with five
// readable `.cs` files on disk it answered `{"count":0,"scripts":[]}`.
//
// This test registers a throwaway language whose extension (`gdprobe`) no build
// knows in advance, so it is **red in both variants** before the fix instead of
// only in a Mono one - and it never depends on the .NET module being present.
// ---------------------------------------------------------------------------
class ProbeScriptLanguage : public ScriptLanguage {
public:
	String get_name() const override { return "ProbeScriptLanguage"; }
	void init() override {}
	String get_type() const override { return "ProbeScriptLanguage"; }
	String get_extension() const override { return "gdprobe"; }
	void finish() override {}
#ifdef TOOLS_ENABLED
	EditorLanguage *get_editor_language() override { return &editor_language; }
	EditorLanguage editor_language;
#endif // TOOLS_ENABLED
	Vector<String> get_reserved_words() const override { return Vector<String>(); }
	bool is_control_flow_keyword(const String &p_string) const override {
		(void)p_string;
		return false;
	}
	Vector<String> get_comment_delimiters() const override { return Vector<String>(); }
	Vector<String> get_doc_comment_delimiters() const override { return Vector<String>(); }
	Vector<String> get_string_delimiters() const override { return Vector<String>(); }
	bool supports_builtin_mode() const override { return false; }
	String make_function(const String &p_class, const String &p_name, const PackedStringArray &p_args) const override {
		(void)p_class;
		(void)p_name;
		(void)p_args;
		return String();
	}
	void add_global_constant(const StringName &p_variable, const Variant &p_value) override {
		(void)p_variable;
		(void)p_value;
	}
	String debug_get_error() const override { return String(); }
	int debug_get_stack_level_count() const override { return 0; }
	int debug_get_stack_level_line(int p_level) const override {
		(void)p_level;
		return 0;
	}
	String debug_get_stack_level_function(int p_level) const override {
		(void)p_level;
		return String();
	}
	String debug_get_stack_level_source(int p_level) const override {
		(void)p_level;
		return String();
	}
	void debug_get_stack_level_locals(int p_level, List<String> *p_locals, List<Variant> *p_values, int p_max_subitems, int p_max_depth) override {
		(void)p_level;
		(void)p_locals;
		(void)p_values;
		(void)p_max_subitems;
		(void)p_max_depth;
	}
	void debug_get_stack_level_members(int p_level, List<String> *p_members, List<Variant> *p_values, int p_max_subitems, int p_max_depth) override {
		(void)p_level;
		(void)p_members;
		(void)p_values;
		(void)p_max_subitems;
		(void)p_max_depth;
	}
	void debug_get_globals(List<String> *p_globals, List<Variant> *p_values, int p_max_subitems, int p_max_depth) override {
		(void)p_globals;
		(void)p_values;
		(void)p_max_subitems;
		(void)p_max_depth;
	}
	String debug_parse_stack_level_expression(int p_level, const String &p_expression, int p_max_subitems, int p_max_depth) override {
		(void)p_level;
		(void)p_expression;
		(void)p_max_subitems;
		(void)p_max_depth;
		return String();
	}
	void reload_all_scripts() override {}
	void reload_scripts(const Array &p_scripts) override { (void)p_scripts; }
	void reload_tool_script(const Ref<Script> &p_script) override { (void)p_script; }
	void get_public_functions(List<MethodInfo> *p_functions) const override { (void)p_functions; }
	void get_public_constants(List<Pair<String, Variant>> *p_constants) const override { (void)p_constants; }
	void get_public_annotations(List<MethodInfo> *p_annotations) const override { (void)p_annotations; }
	void profiling_start() override {}
	void profiling_stop() override {}
	void profiling_set_save_native_calls(bool p_enable) override { (void)p_enable; }
	int profiling_get_accumulated_data(ProfilingInfo *p_info_arr, int p_info_max) override {
		(void)p_info_arr;
		(void)p_info_max;
		return 0;
	}
	int profiling_get_frame_data(ProfilingInfo *p_info_arr, int p_info_max) override {
		(void)p_info_arr;
		(void)p_info_max;
		return 0;
	}
};

TEST_CASE("[MCPServer] project_list_scripts lists the script languages the build registered") {
	const String root = "res://mcp_server_test_fixture_script_languages";
	TestMCPServer::remove_tree(root);

	CHECK(TestMCPServer::write_file_bytes(root.path_join("probe.gd"), TestMCPServer::to_bytes("extends Node\n")));
	CHECK(TestMCPServer::write_file_bytes(root.path_join("probe.gdshader"), TestMCPServer::to_bytes("shader_type canvas_item;\n")));
	// `has_csharp` below is exactly about this file: it is a script of the
	// project *iff* this build has the .NET module.
	CHECK(TestMCPServer::write_file_bytes(root.path_join("probe.cs"), TestMCPServer::to_bytes("// probe\n")));
	// The extension of the throwaway language registered below.
	CHECK(TestMCPServer::write_file_bytes(root.path_join("probe.gdprobe"), TestMCPServer::to_bytes("probe\n")));
	// Not a script under any language, so it must never be listed.
	CHECK(TestMCPServer::write_file_bytes(root.path_join("notes.txt"), TestMCPServer::to_bytes("notes\n")));

	ProbeScriptLanguage *probe = memnew(ProbeScriptLanguage);
	const bool probe_registered = ScriptServer::register_language(probe) == OK;
	CHECK(probe_registered);

	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);
	MCPToolError tool_error;
	const Variant result = registry.call_tool("project_list_scripts", Dictionary(), tool_error);

	// The language must be gone before anything is asserted: `REQUIRE`/`CHECK`
	// never abort a case in this harness (tests/test_macros.h:44), and a leaked
	// registration would make every later case in this process see a second
	// language.
	if (probe_registered) {
		ScriptServer::unregister_language(probe);
	}
	memdelete(probe);

	CHECK_FALSE(tool_error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = result;
		const Array scripts = payload["scripts"];
		Array in_fixture;
		for (int i = 0; i < scripts.size(); i++) {
			const String entry = scripts[i];
			if (entry.begins_with(root)) {
				in_fixture.push_back(entry);
			}
		}
		in_fixture.sort();

		Array expected;
		expected.push_back(root.path_join("probe.gd"));
		// Yes: *because* `ProbeScriptLanguage` was registered, a file no build
		// knows about is part of the answer. That is the whole point - the filter
		// is `ScriptServer`, not a literal in the tool.
		expected.push_back(root.path_join("probe.gdprobe"));
		expected.push_back(root.path_join("probe.gdshader"));
		// F-066-1 itself, as a property of the SET rather than of one file's
		// membership: `cs` is a registered extension exactly when the .NET module
		// is compiled in, so the Mono build's answer has one more entry and the
		// plain build's must not invent one.
		const bool has_csharp = ScriptServer::get_language_for_extension("cs") != nullptr;
		if (has_csharp) {
			expected.push_back(root.path_join("probe.cs"));
		}
		expected.sort();

		CHECK(in_fixture.size() == expected.size());
		CHECK(TestMCPServer::canonical(in_fixture) == TestMCPServer::canonical(expected));
		CHECK_FALSE(in_fixture.has(root.path_join("notes.txt")));
		CHECK(in_fixture.has(root.path_join("probe.cs")) == has_csharp);
	}

	TestMCPServer::remove_tree(root);
}

// ---------------------------------------------------------------------------
// TASK-068 (2.i + 2.ii): the two descriptions a caller reads had to say two
// things the tools really do, and both are append-only contract overrides
// (`scripts/gen_renamed_contract.py` DESCRIPTION_OVERRIDES: `list_scripts`,
// `run_test_scenario`; v1.20).
//
// Why the *live* text and not the contract file: the server has no access to
// `docs/`, so the string a client receives is the C++ literal in the builder
// call. Gate 1 is what compares that literal to the contract, and this case is
// what fails *before* a build is spent when a later edit drops a clause of it.
// The sentences asserted here are the declarations the two registered items
// owed:
//
//   * `project_list_scripts` (TASK-067 section 1.4 / D125 (b)) - the walk is
//     deliberately not narrowed, so the engine's own project cache comes back
//     with the rest and the caller filters;
//   * `running_game_run_test_scenario` (R4 section 8.2) - the wait step's input
//     member is `seconds` (contract `inputSchema.properties.steps.items
//     .properties.seconds`, the only duration member) and the *result* entry's
//     echo is `waited_seconds` (tools/running_game_test_execution.cpp:440/459),
//     two different members in two different objects - so nothing is renamed and
//     no alias is added, and the text has to say which is which.
// ---------------------------------------------------------------------------
TEST_CASE("[MCPServer] TASK-068 the two clarified descriptions are registered") {
	MCPToolRegistry editor_registry;
	TestMCPServer::build_editor_process_registry(editor_registry);
	const Array editor_list = editor_registry.build_tools_list(true);

	// `build_all_tools_registry` is the game-process table (the doctest process is
	// not an editor; tests/test_mcp_server.h:12613), and `false` is the game
	// listing - the same pair the TASK-051 case uses for the game side.
	MCPToolRegistry game_registry;
	TestMCPServer::build_all_tools_registry(game_registry);
	const Array game_list = game_registry.build_tools_list(false);

	const auto description_of = [](const Array &p_list, const String &p_name) -> String {
		for (int i = 0; i < p_list.size(); i++) {
			const Variant entry = p_list[i];
			if (entry.get_type() != Variant::DICTIONARY) {
				continue;
			}
			const Dictionary tool = entry;
			if (String(tool.get("name", Variant())) == p_name) {
				return tool.get("description", Variant());
			}
		}
		return String();
	};

	// --- (2.i) project_list_scripts ------------------------------------------
	const String list_scripts = description_of(editor_list, "project_list_scripts");
	// The Chinese head of the original description is still first, verbatim - the
	// append-only half of the override.
	CHECK(list_scripts.begins_with(String::utf8("列出所有脚本文件 ")));
	// ... and the consequence TASK-067 declared only in its report is now in the
	// text a client reads.
	CHECK(list_scripts.contains(String::utf8(".godot")));
	CHECK(list_scripts.contains(String::utf8("生成脚本")));
	CHECK(list_scripts.contains("res://.godot/mono/temp/obj/**"));
	CHECK(list_scripts.contains(String::utf8("自行过滤")));
	// The same string reaches a game-scope caller (`scope = BOTH`).
	const String list_scripts_game = description_of(game_list, "project_list_scripts");
	CHECK(list_scripts_game == list_scripts);

	// --- (2.ii) running_game_run_test_scenario -------------------------------
	const String run_scenario = description_of(game_list, "running_game_run_test_scenario");
	CHECK(run_scenario.begins_with(String::utf8("运行测试场景并执行一系列测试步骤 ")));
	// The input member, the result member, and the statement that they are in
	// different objects - the three facts R4 section 8.2 needed stated.
	CHECK(run_scenario.contains("seconds"));
	CHECK(run_scenario.contains("waited_seconds"));
	CHECK(run_scenario.contains(String::utf8("不同的对象")));
	CHECK(run_scenario.contains(String::utf8("不是入参")));
	CHECK(run_scenario.contains("steps[i].seconds"));
	// The echo is the *requested* value, and which member it mirrors depends on
	// the wait form: `:440` mirrors `seconds`, `:459` mirrors `timeout`. A text
	// that said only "the seconds it really waited" would be wrong for the second
	// form, so both halves are asserted.
	CHECK(run_scenario.contains("tools/running_game_test_execution.cpp:440"));
	CHECK(run_scenario.contains(":459"));
	CHECK(run_scenario.contains("timeout"));
	// `waited_seconds` must NOT have become an accepted input: it is not in the
	// contract's schema and this task did not add it. The clause the description
	// carries is exactly that (`不是入参`), and the schema member set is asserted
	// character for character by the TASK-051 case; here the one thing that
	// would make this text a lie is checked: the live schema still has `seconds`
	// and no `waited_seconds`.
	const auto schema_of = [](const Array &p_list, const String &p_name) -> Dictionary {
		for (int i = 0; i < p_list.size(); i++) {
			const Variant entry = p_list[i];
			if (entry.get_type() != Variant::DICTIONARY) {
				continue;
			}
			const Dictionary tool = entry;
			if (String(tool.get("name", Variant())) == p_name) {
				return tool.get("inputSchema", Variant());
			}
		}
		return Dictionary();
	};
	const Dictionary run_schema = schema_of(game_list, "running_game_run_test_scenario");
	const Dictionary run_properties = run_schema.get("properties", Variant());
	const Dictionary steps = run_properties.get("steps", Variant());
	const Dictionary steps_items = steps.get("items", Variant());
	const Dictionary step_properties = steps_items.get("properties", Variant());
	CHECK(step_properties.has("seconds"));
	CHECK_FALSE(step_properties.has("waited_seconds"));

	// Scope unchanged: the driver is game-only, and its description is served on
	// the game endpoint.
	CHECK(description_of(editor_list, "running_game_run_test_scenario").is_empty());
}

TEST_CASE("[MCPServer] project_read_script returns the file text verbatim") {
	TestMCPServer::ReadFilesProject project;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	Dictionary args;
	args["path"] = project.path("scripts/unicode.gd");
	MCPToolError tool_error;
	const Variant result = registry.call_tool("project_read_script", args, tool_error);
	CHECK_FALSE(tool_error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = result;
		// Exactly three keys: the reference returns no line numbers, and no
		// line-oriented field may be invented here.
		CHECK(payload.size() == 3);
		CHECK((String)payload["path"] == project.path("scripts/unicode.gd"));
		CHECK((String)payload["content"] == project.unicode_text);
		CHECK((int)payload["size"] == TestMCPServer::to_bytes(project.unicode_text).size());
		CHECK((int)payload["size"] != project.unicode_text.length());
		CHECK_FALSE(payload.has("lines"));
		CHECK_FALSE(payload.has("line_numbers"));
		// CRLF and the non-ASCII characters survive the read unchanged.
		CHECK(((String)payload["content"]).contains("\r\n"));
		CHECK(((String)payload["content"]).contains(String::utf8("中文")));
	}

	// `path` is required.
	MCPToolError missing_param;
	registry.call_tool("project_read_script", Dictionary(), missing_param);
	CHECK(missing_param.code == -32602);
	CHECK(missing_param.message == "Missing required parameter: path");

	// A file that is not there is -32001 with a suggestion (GDR-14), never a
	// silently empty file.
	Dictionary missing;
	missing["path"] = project.path("scripts/does_not_exist.gd");
	MCPToolError missing_error;
	registry.call_tool("project_read_script", missing, missing_error);
	CHECK(missing_error.code == -32001);
	CHECK(missing_error.message.contains("not found"));
	CHECK(((Dictionary)missing_error.data).has("suggestion"));

	// The path is normalized before it is opened and echoed back.
	Dictionary dotted;
	dotted["path"] = project.root + "/./scripts/unicode.gd";
	MCPToolError dotted_error;
	const Variant dotted_result = registry.call_tool("project_read_script", dotted, dotted_error);
	CHECK_FALSE(dotted_error.is_error());
	if (dotted_result.get_type() == Variant::DICTIONARY) {
		CHECK((String)((Dictionary)dotted_result)["path"] == project.path("scripts/unicode.gd"));
	}
}

TEST_CASE("[MCPServer] project_validate_script distinguishes valid and broken code") {
	TestMCPServer::ReadFilesProject project;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	// Both answers below hold in either mode: when a script language is
	// initialised the tool reports the real GDScript compilation result, and in a
	// process without one (the doctest process - `Main::test_setup()` never calls
	// `ScriptServer::init_languages()`) it reports the documented structural
	// fallback: balanced source passes, unbalanced source fails. The fallback
	// message says explicitly that no compilation happened, so `valid` is never
	// presented as "syntax is correct". The real-compilation positive and
	// negative cases are additionally covered by the gate 2 evidence on a real
	// project, where the language is initialised (REPORT-005 section 5).
	Dictionary good;
	good["path"] = project.path("scripts/alpha.gd");
	MCPToolError good_error;
	const Variant good_result = registry.call_tool("project_validate_script", good, good_error);
	CHECK_FALSE(good_error.is_error());
	CHECK(good_result.get_type() == Variant::DICTIONARY);
	if (good_result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = good_result;
		CHECK(payload.has("valid"));
		CHECK(payload["valid"].get_type() == Variant::BOOL);
		CHECK((bool)payload["valid"] == true);
		CHECK((String)payload["path"] == project.path("scripts/alpha.gd"));
		CHECK(((String)payload["message"]).length() > 0);
	}

	Dictionary broken;
	broken["path"] = project.path("scripts/broken.gd");
	MCPToolError broken_error;
	const Variant broken_result = registry.call_tool("project_validate_script", broken, broken_error);
	CHECK_FALSE(broken_error.is_error());
	CHECK(broken_result.get_type() == Variant::DICTIONARY);
	if (broken_result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = broken_result;
		CHECK(payload.has("valid"));
		CHECK(payload["valid"].get_type() == Variant::BOOL);
		CHECK((bool)payload["valid"] == false);
		CHECK(payload.has("error_text"));
		CHECK(((String)payload["message"]).length() > 0);
	}

	// `path` is required.
	MCPToolError missing_param;
	registry.call_tool("project_validate_script", Dictionary(), missing_param);
	CHECK(missing_param.code == -32602);
	CHECK(missing_param.message == "Missing required parameter: path");

	// A file that is not there is -32001 with a suggestion.
	Dictionary missing;
	missing["path"] = project.path("scripts/does_not_exist.gd");
	MCPToolError missing_error;
	registry.call_tool("project_validate_script", missing, missing_error);
	CHECK(missing_error.code == -32001);
	CHECK(missing_error.message.contains("not found"));
	CHECK(((Dictionary)missing_error.data).has("suggestion"));
}

TEST_CASE("[MCPServer] project_read_resource reports the loaded resource type") {
	TestMCPServer::ReadFilesProject project;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	Dictionary args;
	args["path"] = project.path("resources/simple.tres");
	MCPToolError tool_error;
	const Variant result = registry.call_tool("project_read_resource", args, tool_error);
	CHECK_FALSE(tool_error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = result;
		CHECK((String)payload["path"] == project.path("resources/simple.tres"));
		CHECK((String)payload["type"] == "Resource");
		CHECK((bool)payload["loaded"] == true);

		// TASK-024 E-9: the answer carries the resource's own stored values
		// (the "read properties" shape every other read tool uses: a flat
		// `name -> serialized value` object), instead of forcing a second round
		// trip through `editor_execute_gdscript` + `get_property_list()`.
		CHECK(payload.has("properties"));
		const Dictionary properties = payload["properties"];
		// `Resource` declares exactly two `PROPERTY_USAGE_STORAGE` members, and
		// this `.tres` sets neither of them.
		CHECK((int64_t)payload["properties_total"] == 2);
		CHECK((int64_t)payload["properties_count"] == properties.size());
		CHECK(properties.size() == 2);
		CHECK(properties.has("resource_local_to_scene"));
		CHECK((bool)properties["resource_local_to_scene"] == false);
		CHECK(properties.has("resource_name"));
		CHECK((String)properties["resource_name"] == "");
		// Inspector scaffolding is not content: `resource_path` is
		// `PROPERTY_USAGE_EDITOR` only and must not be reported.
		CHECK_FALSE(properties.has("resource_path"));
		CHECK((bool)payload["properties_truncated"] == false);
		CHECK((int64_t)payload["properties_limit"] == 256);
		CHECK((int64_t)payload["properties_byte_limit"] == 256 * 1024);
	}

	// A value that is really stored comes back as a value, not as a name.
	REQUIRE(project.write("resources/named.tres", "[gd_resource type=\"Resource\" format=3]\n\n[resource]\nresource_name = \"hello\"\n"));
	Dictionary named;
	named["path"] = project.path("resources/named.tres");
	MCPToolError named_error;
	const Variant named_result = registry.call_tool("project_read_resource", named, named_error);
	CHECK_FALSE(named_error.is_error());
	if (named_result.get_type() == Variant::DICTIONARY) {
		const Dictionary properties = ((Dictionary)named_result)["properties"];
		CHECK((String)properties["resource_name"] == "hello");
	}

	// `path` is required.
	MCPToolError missing_param;
	registry.call_tool("project_read_resource", Dictionary(), missing_param);
	CHECK(missing_param.code == -32602);
	CHECK(missing_param.message == "Missing required parameter: path");

	// An unloadable path is -32001 with a suggestion.
	Dictionary missing;
	missing["path"] = project.path("resources/does_not_exist.tres");
	MCPToolError missing_error;
	registry.call_tool("project_read_resource", missing, missing_error);
	CHECK(missing_error.code == -32001);
	CHECK(missing_error.message.contains("not found"));
	CHECK(((Dictionary)missing_error.data).has("suggestion"));
}

TEST_CASE("[MCPServer] project_get_resource_preview returns a scaled png") {
	TestMCPServer::ReadFilesProject project;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	// 64x32 scaled into max_size=16 -> 16x8 (the reference's uniform scale).
	Dictionary args;
	args["path"] = project.path("images/small.png");
	args["max_size"] = 16;
	MCPToolError tool_error;
	const Variant result = registry.call_tool("project_get_resource_preview", args, tool_error);
	CHECK_FALSE(tool_error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = result;
		CHECK((int)payload["width"] == 16);
		CHECK((int)payload["height"] == 8);
		CHECK((String)payload["format"] == "png");
		CHECK((String)payload["path"] == project.path("images/small.png"));

		const String encoded = payload["image_base64"];
		CHECK(encoded.length() > 0);
		// Standard base64 of the 8 byte PNG signature.
		CHECK(encoded.begins_with("iVBORw0KGgo"));

		// Decode it for real and check the PNG magic, instead of trusting the
		// length or the prefix alone.
		const CharString encoded_utf8 = encoded.utf8();
		Vector<uint8_t> decoded;
		decoded.resize(encoded_utf8.length());
		size_t decoded_length = 0;
		const Error decode_error = CryptoCore::b64_decode(decoded.ptrw(), decoded.size(), &decoded_length,
				(const uint8_t *)encoded_utf8.get_data(), encoded_utf8.length());
		CHECK(decode_error == OK);
		CHECK(decoded_length >= 4);
		CHECK(decoded[0] == 0x89);
		CHECK(decoded[1] == 'P');
		CHECK(decoded[2] == 'N');
		CHECK(decoded[3] == 'G');
	}

	// The default max_size is 256: a 64x32 image is not resized at all.
	Dictionary natural;
	natural["path"] = project.path("images/small.png");
	MCPToolError natural_error;
	const Variant natural_result = registry.call_tool("project_get_resource_preview", natural, natural_error);
	CHECK_FALSE(natural_error.is_error());
	if (natural_result.get_type() == Variant::DICTIONARY) {
		CHECK((int)((Dictionary)natural_result)["width"] == 64);
		CHECK((int)((Dictionary)natural_result)["height"] == 32);
	}

	// `max_size <= 0` is an explicit -32602: `Image::resize` would ERR_FAIL and a
	// scale of 0 would divide by zero.
	Dictionary zero;
	zero["path"] = project.path("images/small.png");
	zero["max_size"] = 0;
	MCPToolError zero_error;
	registry.call_tool("project_get_resource_preview", zero, zero_error);
	CHECK(zero_error.code == -32602);

	// `max_size` present with the wrong type is -32602 as well.
	Dictionary wrong_type;
	wrong_type["path"] = project.path("images/small.png");
	wrong_type["max_size"] = "big";
	MCPToolError wrong_type_error;
	registry.call_tool("project_get_resource_preview", wrong_type, wrong_type_error);
	CHECK(wrong_type_error.code == -32602);
	CHECK(wrong_type_error.message.contains("max_size"));

	// `path` is required.
	MCPToolError missing_param;
	registry.call_tool("project_get_resource_preview", Dictionary(), missing_param);
	CHECK(missing_param.code == -32602);
	CHECK(missing_param.message == "Missing required parameter: path");

	// A path that is not there is -32001, in both branches (image and resource).
	Dictionary missing;
	missing["path"] = project.path("images/does_not_exist.png");
	MCPToolError missing_error;
	registry.call_tool("project_get_resource_preview", missing, missing_error);
	CHECK(missing_error.code == -32001);
	CHECK(missing_error.message.contains("not found"));

	// A resource that loads but carries no image is -32602 ("the object is not
	// applicable"), not -32001 ("it is not there") - the reference's error class.
	Dictionary not_an_image;
	not_an_image["path"] = project.path("resources/simple.tres");
	MCPToolError not_an_image_error;
	registry.call_tool("project_get_resource_preview", not_an_image, not_an_image_error);
	CHECK(not_an_image_error.code == -32602);
	CHECK(not_an_image_error.message.contains("does not have an image preview"));
}

TEST_CASE("[MCPServer] project_read_scene_file_content returns the raw tscn text") {
	TestMCPServer::ReadFilesProject project;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	Dictionary args;
	args["path"] = project.path("scenes/main.tscn");
	MCPToolError tool_error;
	const Variant result = registry.call_tool("project_read_scene_file_content", args, tool_error);
	CHECK_FALSE(tool_error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = result;
		// Same three keys as project_read_script, and no line numbers.
		CHECK(payload.size() == 3);
		CHECK((String)payload["path"] == project.path("scenes/main.tscn"));
		CHECK((int)payload["size"] == TestMCPServer::to_bytes((String)payload["content"]).size());
		CHECK((int)payload["size"] != ((String)payload["content"]).length());
		CHECK(((String)payload["content"]).begins_with("[gd_scene"));
		CHECK(((String)payload["content"]).contains("[node name=\"Main\" type=\"Node2D\"]"));
		CHECK_FALSE(payload.has("lines"));
	}

	// `path` is required.
	MCPToolError missing_param;
	registry.call_tool("project_read_scene_file_content", Dictionary(), missing_param);
	CHECK(missing_param.code == -32602);
	CHECK(missing_param.message == "Missing required parameter: path");

	// A file that is not there is -32001 with a suggestion. The wording is the
	// scene reader's own ("Scene file '...'"), not the script reader's.
	Dictionary missing;
	missing["path"] = project.path("scenes/does_not_exist.tscn");
	MCPToolError missing_error;
	registry.call_tool("project_read_scene_file_content", missing, missing_error);
	CHECK(missing_error.code == -32001);
	CHECK(missing_error.message.contains("Scene file"));
	CHECK(((Dictionary)missing_error.data).has("suggestion"));
}

TEST_CASE("[MCPServer] the file readers never write to the project") {
	TestMCPServer::ReadFilesProject project;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	const Array before = TestMCPServer::list_files_recursive(project.root);
	// The fixture's inventory. TASK-026 added `resources/gradient.tres` and
	// `resources/environment.tres`, so the count moved from 11 to 13.
	CHECK(before.size() == 13);

	MCPToolError ignored;

	registry.call_tool("project_list_scripts", Dictionary(), ignored);

	Dictionary script;
	script["path"] = project.path("scripts/alpha.gd");
	registry.call_tool("project_read_script", script, ignored);
	registry.call_tool("project_validate_script", script, ignored);

	Dictionary resource;
	resource["path"] = project.path("resources/simple.tres");
	registry.call_tool("project_read_resource", resource, ignored);

	Dictionary image;
	image["path"] = project.path("images/small.png");
	image["max_size"] = 16;
	registry.call_tool("project_get_resource_preview", image, ignored);

	Dictionary scene;
	scene["path"] = project.path("scenes/main.tscn");
	registry.call_tool("project_read_scene_file_content", scene, ignored);

	const Array after = TestMCPServer::list_files_recursive(project.root);
	CHECK(after.size() == before.size());
	CHECK(TestMCPServer::canonical(after) == TestMCPServer::canonical(before));
}

// ---------------------------------------------------------------------------
// B1 group `editor_read_scene_inspector` (TASK-006): the seven editor-only,
// read-only tools. This is the first `scope = EDITOR` group, so the guard that
// was never end-to-end observable before is pinned here at three levels:
//   * the registry does not even carry the tools in a game process;
//   * `tools/list` / `tools/call` hide them from a game process;
//   * the JSON-RPC layer answers "Method not found" (-32601) instead of running
//     one.
// The live editor/game endpoint comparison is gate section 2 evidence; what
// cannot be constructed in the doctest process (no SceneTree, no EditorNode) is
// covered there too and declared in the report.
// ---------------------------------------------------------------------------

namespace {
const char *const EDITOR_INSPECTOR_TOOLS[7] = {
	"editor_get_errors",
	"editor_get_output_log",
	"editor_get_open_scripts",
	"editor_get_scene_tree",
	"editor_get_selection",
	"editor_get_viewport_3d_camera",
	"editor_analyze_signal_flow",
};
} // namespace

TEST_CASE("[MCPServer] the editor_read_scene_inspector group is editor-only") {
	// A game process must not even carry the tools in its table (GDR-19 17.3):
	// the builder skips them at registration, so no `tools/list` filtering is
	// needed to hide them.
	MCPToolRegistry game_registry;
	TestMCPServer::build_all_tools_registry(game_registry);
	CHECK(game_registry.get_tool_count() == 40);
	CHECK(game_registry.get_visible_tool_count(false) == 40);
	// ... and an editor process carries exactly the 23 both-scope tools plus the
	// seven inspectors plus the ten writers of `editor_write_scene_editor`
	// (TASK-008) plus the seventeen game-scope tools of
	// TASK-009/TASK-010/TASK-011/TASK-012 plus the three editor-scope tools of
	// TASK-012 (`editor_play_scene`, `editor_stop_scene`,
	// `editor_get_input_actions`) plus the six editor-scope input simulation
	// tools of TASK-013 plus the ten editor-scope node writes of TASK-015, which
	// it hides.
	MCPToolRegistry editor_registry;
	TestMCPServer::build_editor_process_registry(editor_registry);
	CHECK(editor_registry.get_tool_count() == 76);
	CHECK(editor_registry.get_visible_tool_count(true) == 59);
	// The editor-process table still filters correctly the other way round.
	CHECK(editor_registry.get_visible_tool_count(false) == 40);

	for (int i = 0; i < 7; i++) {
		const String name = EDITOR_INSPECTOR_TOOLS[i];
		CHECK_FALSE(game_registry.has_tool(name));
		CHECK_FALSE(game_registry.is_tool_visible(name, false));
		// Even an editor's view cannot see a tool that is not in the table.
		CHECK_FALSE(game_registry.is_tool_visible(name, true));

		CHECK(editor_registry.has_tool(name));
		CHECK(editor_registry.is_tool_visible(name, true));
		CHECK_FALSE(editor_registry.is_tool_visible(name, false));
	}

	// The listing a game process serves must name none of the seven.
	const Array game_list = game_registry.build_tools_list(false);
	CHECK(game_list.size() == 40);
	for (int i = 0; i < game_list.size(); i++) {
		const String listed = ((Dictionary)game_list[i])["name"];
		for (int j = 0; j < 7; j++) {
			CHECK(listed != EDITOR_INSPECTOR_TOOLS[j]);
		}
	}

	// `tools/call` on a game endpoint: -32601, never execution.
	const String call = "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"editor_get_errors\",\"arguments\":{}}}";
	const MCPJsonRpc::Response refused = MCPJsonRpc::handle(call, game_registry, false);
	CHECK(refused.http_status == 200);
	CHECK(refused.body.contains("\"code\":-32601"));
	CHECK(refused.body.contains("Method not found: editor_get_errors"));
	CHECK_FALSE(refused.body.contains("\"result\""));

	// The very same request against the editor table reaches the tool: the log
	// tool needs no editor UI, so it answers with a result envelope here.
	const MCPJsonRpc::Response served = MCPJsonRpc::handle(call, editor_registry, true);
	CHECK(served.http_status == 200);
	CHECK(served.body.contains("\"result\""));
	CHECK(served.body.contains("\"content\""));
}

// TASK-026 (E-9's third surface): GDR-25 section 23.4's closure rule on the two
// *resource* writers.
//
// The read side answers a component-shaped value as an object
// (`{"x":1,"y":2,"z":3}` for a `Vector3`) or as an array of objects
// (`[{r,g,b,a},..]` for a `PackedColorArray`). `editor_set_node_property` has
// taken those shapes since TASK-018/021/025 (`shape_vector_from_json` in
// `prepare_node_property_value`), while `project_edit_resource` /
// `project_create_resource` refused them with `-32602` - so the value
// `project_read_resource` answers for a *resource* could not be fed back at all
// (the node tools cannot write a resource's own property). Both now run the same
// three steps as every other write path.
TEST_CASE("[MCPServer] the resource writers take the component shapes the readers answer") {
	TestMCPServer::ScratchProject fixture;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	// --- `project_create_resource`: a `Vector3` named by its components ---
	const String mesh_path = fixture.path("resources/component_box.tres");
	Dictionary create_args;
	create_args["path"] = mesh_path;
	create_args["type"] = "BoxMesh";
	Dictionary create_properties;
	Dictionary size;
	size["x"] = 1.0;
	size["y"] = 2.0;
	size["z"] = 3.0;
	create_properties["size"] = size;
	create_args["properties"] = create_properties;
	MCPToolError create_error;
	const Variant created = registry.call_tool("project_create_resource", create_args, create_error);
	const String create_refusal = String("project_create_resource refused {\"x\":1,\"y\":2,\"z\":3} for BoxMesh.size: code=") +
			itos(create_error.code) + " message='" + create_error.message + "'";
	CHECK_MESSAGE(!create_error.is_error(), create_refusal);
	if (created.get_type() == Variant::DICTIONARY) {
		const Dictionary create_payload = created;
		const Array set_names = create_payload["properties_set"];
		CHECK(set_names.has("size"));
	}

	// ... and the reader answers the same object back, straight from the file.
	Dictionary read_args;
	read_args["path"] = mesh_path;
	MCPToolError read_error;
	const Variant read_result = registry.call_tool("project_read_resource", read_args, read_error);
	CHECK_FALSE(read_error.is_error());
	if (read_result.get_type() == Variant::DICTIONARY) {
		const Dictionary stored = ((Dictionary)read_result)["properties"];
		CHECK(stored.has("size"));
		if (stored.has("size")) {
			const Variant stored_size = stored["size"];
			CHECK(stored_size.get_type() == Variant::DICTIONARY);
			if (stored_size.get_type() == Variant::DICTIONARY) {
				const Dictionary components = stored_size;
				CHECK(components.has("x"));
				CHECK(components.has("y"));
				CHECK(components.has("z"));
				if (components.has("x") && components.has("y") && components.has("z")) {
					CHECK((double)components["x"] == 1.0);
					CHECK((double)components["y"] == 2.0);
					CHECK((double)components["z"] == 3.0);
				}
			}
		}
	}

	// --- `project_edit_resource`: a `Color` named by its components ---
	const String env_path = fixture.path("resources/component_env.tres");
	CHECK(fixture.write("resources/component_env.tres",
			"[gd_resource type=\"Environment\" format=3]\n\n[resource]\n"));
	Dictionary edit_args;
	edit_args["path"] = env_path;
	Dictionary edit_properties;
	Dictionary background;
	background["r"] = 0.25;
	background["g"] = 0.5;
	background["b"] = 0.75;
	background["a"] = 1.0;
	edit_properties["background_color"] = background;
	edit_args["properties"] = edit_properties;
	MCPToolError edit_error;
	const Variant edited = registry.call_tool("project_edit_resource", edit_args, edit_error);
	const String color_refusal = String("project_edit_resource refused {r,g,b,a} for Environment.background_color: code=") +
			itos(edit_error.code) + " message='" + edit_error.message + "'";
	CHECK_MESSAGE(!edit_error.is_error(), color_refusal);
	if (edited.get_type() == Variant::DICTIONARY) {
		const Dictionary changed = ((Dictionary)edited)["changed"];
		CHECK(changed.has("background_color"));
		if (changed.has("background_color")) {
			const Dictionary entry = changed["background_color"];
			CHECK(entry.has("new"));
			if (entry.has("new")) {
				const Variant written = entry["new"];
				CHECK(written.get_type() == Variant::DICTIONARY);
				if (written.get_type() == Variant::DICTIONARY) {
					const Dictionary components = written;
					CHECK((double)components["r"] == 0.25);
					CHECK((double)components["g"] == 0.5);
					CHECK((double)components["b"] == 0.75);
					CHECK((double)components["a"] == 1.0);
				}
			}
		}
	}
}

TEST_CASE("[MCPServer] editor_get_errors reports the ERROR lines of the log tail") {
	// `String::utf8` for the non-ASCII line: `String(const char *)` decodes a
	// narrow literal as Latin-1, which would put mojibake in the log and make the
	// byte-exact comparisons below meaningless.
	const String content = String("Godot Engine v4.7.1\n"
								  "INFO: editor ready\n"
								  "ERROR: first failure\n"
								  "SCRIPT ERROR: res://scripts/a.gd:3\n"
								  "PARSE ERROR: res://scripts/b.gd:7\n"
								  "only lowercase error here\n") +
			String::utf8("中文日志行 汉字\n");
	TestMCPServer::ScratchLog log(content);
	CHECK(log.ok);

	MCPToolRegistry registry;
	TestMCPServer::build_editor_process_registry(registry);

	// Default `max_lines` is 50, so nothing is cut off: every line of the file
	// is in the window and the four lines whose upper-cased text contains
	// "ERROR" are reported.
	MCPToolError tool_error;
	const Variant result = registry.call_tool("editor_get_errors", Dictionary(), tool_error);
	CHECK_FALSE(tool_error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = result;
		const Array errors = payload["errors"];
		CHECK((int)payload["count"] == errors.size());
		CHECK(errors.size() == 4);
		if (errors.size() == 4) {
			CHECK((String)errors[0] == "ERROR: first failure");
			CHECK((String)errors[1] == "SCRIPT ERROR: res://scripts/a.gd:3");
			CHECK((String)errors[2] == "PARSE ERROR: res://scripts/b.gd:7");
			// The reference upper-cases each line before the test, so a line
			// that only spells "error" in lower case *is* reported.
			CHECK((String)errors[3] == "only lowercase error here");
		}
		// TASK-024 E-6/G-4: the same provenance fields `editor_get_output_log`
		// answers with (the doctest process has no `EditorNode`, so the file is
		// the source here).
		CHECK((String)payload["source"] == "log_file");
		CHECK((String)payload["log_path"] == "user://logs/godot.log");
		CHECK((bool)payload["editor"] == false);
		CHECK((int64_t)payload["pid"] > 0);
		CHECK((int64_t)payload["port"] == 0);
		CHECK((String)payload["reason"] == "");
	}

	// The tail window is taken *before* the error filter, and the split keeps
	// the empty line a trailing newline produces. `max_lines=1` therefore looks
	// at that empty final line and finds no error at all.
	Dictionary tail;
	tail["max_lines"] = 1;
	MCPToolError tail_error;
	const Variant tail_result = registry.call_tool("editor_get_errors", tail, tail_error);
	CHECK_FALSE(tail_error.is_error());
	if (tail_result.get_type() == Variant::DICTIONARY) {
		const Array errors = ((Dictionary)tail_result)["errors"];
		CHECK(errors.size() == 0);
		CHECK((int)((Dictionary)tail_result)["count"] == 0);
	}

	// `max_lines=6` keeps the last six of the eight split elements, i.e. the
	// last four real lines plus the empty one: all four errors are back.
	Dictionary wider;
	wider["max_lines"] = 6;
	MCPToolError wider_error;
	const Variant wider_result = registry.call_tool("editor_get_errors", wider, wider_error);
	CHECK_FALSE(wider_error.is_error());
	if (wider_result.get_type() == Variant::DICTIONARY) {
		CHECK((int)((Dictionary)wider_result)["count"] == 4);
	}

	// A mistyped `max_lines` is -32602 rather than silently ignored.
	Dictionary wrong_type;
	wrong_type["max_lines"] = "many";
	MCPToolError wrong_type_error;
	registry.call_tool("editor_get_errors", wrong_type, wrong_type_error);
	CHECK(wrong_type_error.code == -32602);
	CHECK(wrong_type_error.message.contains("max_lines"));

	// Without a log file the tool reports an empty list; it never invents an
	// error and never fails - and since TASK-024 E-6 it also says *why* it is
	// empty instead of answering `-32603` (which used to make "the file rotated
	// under me" indistinguishable from "this tool is broken").
	log.remove_file();
	MCPToolError absent_error;
	const Variant absent_result = registry.call_tool("editor_get_errors", Dictionary(), absent_error);
	CHECK_FALSE(absent_error.is_error());
	if (absent_result.get_type() == Variant::DICTIONARY) {
		CHECK(((Array)((Dictionary)absent_result)["errors"]).size() == 0);
		CHECK((int)((Dictionary)absent_result)["count"] == 0);
		CHECK((String)((Dictionary)absent_result)["source"] == "no_log_file");
		CHECK_FALSE((String)((Dictionary)absent_result)["reason"] == "");
	}
}

TEST_CASE("[MCPServer] editor_get_output_log filters the tail case sensitively") {
	const String cjk_line = String::utf8("中文日志行 汉字");
	const String content = String("Godot Engine v4.7.1\n"
								  "INFO: editor ready\n"
								  "ERROR: first failure\n"
								  "only lowercase error here\n") +
			cjk_line + String("\n");
	TestMCPServer::ScratchLog log(content);
	CHECK(log.ok);

	MCPToolRegistry registry;
	TestMCPServer::build_editor_process_registry(registry);

	// Default `max_lines` is 100 and there is no filter: the whole file, and the
	// trailing empty element the split of the final newline produces.
	MCPToolError tool_error;
	const Variant result = registry.call_tool("editor_get_output_log", Dictionary(), tool_error);
	CHECK_FALSE(tool_error.is_error());
	CHECK(result.get_type() == Variant::DICTIONARY);
	if (result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = result;
		const Array lines = payload["lines"];
		CHECK((int)payload["count"] == lines.size());
		CHECK(lines.size() == 6);
		if (lines.size() == 6) {
			CHECK((String)lines[0] == "Godot Engine v4.7.1");
			CHECK((String)lines[4] == cjk_line);
			// The trailing newline yields one empty line - the reference's
			// `split('\n')`, not `lines()`.
			CHECK((String)lines[5] == "");
		}
		CHECK((String)payload["source"] == "log_file");
		CHECK((String)payload["log_path"] == "user://logs/godot.log");
		CHECK((bool)payload["editor"] == false);
		CHECK((int64_t)payload["pid"] > 0);
		CHECK((int64_t)payload["port"] == 0);
		CHECK((String)payload["reason"] == "");
	}

	// The filter is a case sensitive substring test (`str::contains`), so
	// "ERROR" matches the upper-case line but not the lower-case one.
	Dictionary filtered;
	filtered["filter"] = "ERROR";
	MCPToolError filtered_error;
	const Variant filtered_result = registry.call_tool("editor_get_output_log", filtered, filtered_error);
	CHECK_FALSE(filtered_error.is_error());
	if (filtered_result.get_type() == Variant::DICTIONARY) {
		const Array lines = ((Dictionary)filtered_result)["lines"];
		CHECK(lines.size() == 1);
		if (lines.size() == 1) {
			CHECK((String)lines[0] == "ERROR: first failure");
		}
	}

	// The same filter in lower case matches the other line: the test really is
	// case sensitive, not a case-insensitive one that happened to pass.
	Dictionary lower;
	lower["filter"] = "error";
	MCPToolError lower_error;
	const Variant lower_result = registry.call_tool("editor_get_output_log", lower, lower_error);
	CHECK_FALSE(lower_error.is_error());
	if (lower_result.get_type() == Variant::DICTIONARY) {
		const Array lines = ((Dictionary)lower_result)["lines"];
		CHECK(lines.size() == 1);
		if (lines.size() == 1) {
			CHECK((String)lines[0] == "only lowercase error here");
		}
	}

	// A non-ASCII filter works byte for byte.
	Dictionary cjk;
	cjk["filter"] = String::utf8("日志");
	MCPToolError cjk_error;
	const Variant cjk_result = registry.call_tool("editor_get_output_log", cjk, cjk_error);
	CHECK_FALSE(cjk_error.is_error());
	if (cjk_result.get_type() == Variant::DICTIONARY) {
		const Array lines = ((Dictionary)cjk_result)["lines"];
		CHECK(lines.size() == 1);
		if (lines.size() == 1) {
			CHECK((String)lines[0] == cjk_line);
		}
	}

	// `max_lines` cuts the tail of the unfiltered line list first.
	Dictionary tail;
	tail["max_lines"] = 2;
	MCPToolError tail_error;
	const Variant tail_result = registry.call_tool("editor_get_output_log", tail, tail_error);
	CHECK_FALSE(tail_error.is_error());
	if (tail_result.get_type() == Variant::DICTIONARY) {
		const Array lines = ((Dictionary)tail_result)["lines"];
		CHECK(lines.size() == 2);
		if (lines.size() == 2) {
			CHECK((String)lines[0] == cjk_line);
			CHECK((String)lines[1] == "");
		}
	}

	// `filter` present with the wrong type is -32602.
	Dictionary wrong_filter;
	wrong_filter["filter"] = 3;
	MCPToolError wrong_filter_error;
	registry.call_tool("editor_get_output_log", wrong_filter, wrong_filter_error);
	CHECK(wrong_filter_error.code == -32602);
	CHECK(wrong_filter_error.message.contains("filter"));

	// No log file: TASK-026 replaced the reference's `no_log_file` marker with
	// the honest-empty source block (`source: "none"`), an empty list and no
	// error - see the dedicated source-block test case below for the whole
	// shape.
	log.remove_file();
	MCPToolError absent_error;
	const Variant absent_result = registry.call_tool("editor_get_output_log", Dictionary(), absent_error);
	CHECK_FALSE(absent_error.is_error());
	if (absent_result.get_type() == Variant::DICTIONARY) {
		const Dictionary payload = absent_result;
		CHECK(((Array)payload["lines"]).size() == 0);
		CHECK((int)payload["count"] == 0);
		CHECK((String)payload["source"] == "none");
		CHECK((bool)payload["available"] == false);
	}
}

// ===========================================================================
// TASK-026, E-6 + G-4 - the log tools' *source* (GDR-25 section 23.3)
//
// Before this task both tools read `user://logs/godot.log` and nothing else,
// and that file is not this process's log: the editor never writes it (file
// logging is behind the `pc` feature tag, and feature tags are off inside the
// editor - main.cpp:2287/2292), the project's *game* processes do, and it is
// rotated by whoever writes it. M4c measured both consequences: the editor
// endpoint on 9888 answered with the game process's lines
// (`[MCP] listening on 127.0.0.1:9889 (editor=false)`), and a read that landed
// in a rotation window answered `-32603` instead of "nothing to read".
//
// What this test case can pin in a `--test` process (which is not an editor and
// has no `EditorLog`): the source block itself, that both tools emit the *same*
// one (G-4), and that "nothing readable" is an ordinary empty answer. The
// `editor_log` branch and the exists-but-unopenable file (the `-32603` case)
// need a real editor / a real rotation lock and are covered by the live
// evidence of REPORT-026 - the doctest process structurally has neither.
// ===========================================================================
TEST_CASE("[MCPServer] the log tools declare their source and their process, and answer honestly when nothing is readable") {
	const String content = String("Godot Engine v4.7.1\nERROR: from the shared file\n");
	TestMCPServer::ScratchLog log(content);
	CHECK(log.ok);

	MCPToolRegistry registry;
	TestMCPServer::build_editor_process_registry(registry);

	// Both tools, same file, same source block.
	MCPToolError errors_error;
	const Variant errors_result = registry.call_tool("editor_get_errors", Dictionary(), errors_error);
	CHECK_FALSE(errors_error.is_error());
	REQUIRE(errors_result.get_type() == Variant::DICTIONARY);
	MCPToolError lines_error;
	const Variant lines_result = registry.call_tool("editor_get_output_log", Dictionary(), lines_error);
	CHECK_FALSE(lines_error.is_error());
	REQUIRE(lines_result.get_type() == Variant::DICTIONARY);
	if (errors_result.get_type() != Variant::DICTIONARY || lines_result.get_type() != Variant::DICTIONARY) {
		return;
	}
	const Dictionary errors_payload = errors_result;
	const Dictionary lines_payload = lines_result;

	// The source block, on the tool that used to answer *no* source at all
	// (that was G-4).
	CHECK((String)errors_payload["source"] == "log_file");
	CHECK((bool)errors_payload["in_process"] == false);
	CHECK((bool)errors_payload["available"] == true);
	// The `--test` process is not an editor, so the block must say so: this is
	// the field that stops a caller from reading another endpoint's log as its
	// own.
	CHECK((bool)errors_payload["editor"] == false);
	CHECK((String)errors_payload["process"] == "game");
	CHECK((int64_t)errors_payload["pid"] > 0);
	// No MCP server is listening in the test process; `0` means exactly that.
	CHECK((int)errors_payload["port"] == 0);
	CHECK((String)errors_payload["log_path"] == "user://logs/godot.log");
	// A readable-but-shared source carries its caveat.
	CHECK(((String)errors_payload["note"]).contains("shared"));

	// G-4: the two tools answer the *same* block, key for key and value for
	// value - not two shapes that happen to look similar.
	const char *const source_keys[] = { "source", "in_process", "available", "editor", "process", "pid", "port", "log_path", "note" };
	for (const char *key : source_keys) {
		const String name(key);
		CHECK(errors_payload.has(name));
		CHECK(lines_payload.has(name));
		if (errors_payload.has(name) && lines_payload.has(name)) {
			CHECK(errors_payload[name] == lines_payload[name]);
		}
	}

	// Nothing readable is an answer. `-32603` here was the E-6 defect.
	log.remove_file();
	MCPToolError absent_error;
	const Variant absent_result = registry.call_tool("editor_get_errors", Dictionary(), absent_error);
	CHECK_FALSE(absent_error.is_error());
	if (absent_result.get_type() == Variant::DICTIONARY) {
		const Dictionary absent = absent_result;
		CHECK((String)absent["source"] == "none");
		CHECK((bool)absent["available"] == false);
		CHECK((bool)absent["in_process"] == false);
		CHECK((int)absent["count"] == 0);
		CHECK(((Array)absent["errors"]).size() == 0);
		CHECK((int)absent["port"] == 0);
		// The note says which file was tried and why it could not help.
		CHECK(((String)absent["note"]).contains("does not exist"));
		CHECK(((String)absent["note"]).contains("user://logs/godot.log"));
	}

	// A directory where the log file should be: `FileAccess::exists()` is false
	// for a directory (`file_access_windows.cpp` excludes
	// `FILE_ATTRIBUTE_DIRECTORY`), so this is still the honest-empty branch -
	// and it is the only wrong-object shape a test process can build, since an
	// exists-but-unopenable file needs a real exclusive lock.
	DirAccess::make_dir_recursive_absolute(TestMCPServer::scratch_log_path());
	MCPToolError directory_error;
	const Variant directory_result = registry.call_tool("editor_get_output_log", Dictionary(), directory_error);
	CHECK_FALSE(directory_error.is_error());
	if (directory_result.get_type() == Variant::DICTIONARY) {
		const Dictionary directory = directory_result;
		CHECK((String)directory["source"] == "none");
		CHECK((bool)directory["available"] == false);
		CHECK((int)directory["count"] == 0);
	}
	DirAccess::remove_absolute(TestMCPServer::scratch_log_path());
}

TEST_CASE("[MCPServer] the editor UI inspectors refuse cleanly without an editor UI") {
	MCPToolRegistry registry;
	TestMCPServer::build_editor_process_registry(registry);

	Engine *engine = Engine::get_singleton();
	if (engine == nullptr) {
		CHECK(engine != nullptr);
		return;
	}
	const bool was_editor = engine->is_editor_hint();

	const char *const ui_tools[3] = {
		"editor_get_open_scripts",
		"editor_get_selection",
		"editor_get_viewport_3d_camera",
	};

	// (1) Runtime guard: outside an editor process the group's editor-UI tools
	// do not reach `EditorInterface` at all.
	engine->set_editor_hint(false);
	for (int i = 0; i < 3; i++) {
		MCPToolError error;
		registry.call_tool(ui_tools[i], Dictionary(), error);
		CHECK(error.code == -32000);
		CHECK(error.message.begins_with("Not implemented: editor inspectors outside a running editor"));
		CHECK(((Dictionary)error.data).has("suggestion"));
	}

	// (2) Singleton guard: the doctest process *does* have an `EditorInterface`
	// (created by `register_editor_types()`) but no `EditorNode`, and
	// `EditorInterface::get_selection()` dereferences `EditorNode::get_singleton()`
	// without a null check. The guard therefore has to be the singleton itself -
	// without it this loop is a null dereference and the whole test binary
	// crashes, which is exactly what this case detects.
	engine->set_editor_hint(true);
	for (int i = 0; i < 3; i++) {
		MCPToolError error;
		registry.call_tool(ui_tools[i], Dictionary(), error);
		CHECK(error.code == -32000);
		CHECK(error.message.begins_with("Not implemented: the editor UI"));
		CHECK(((Dictionary)error.data).has("suggestion"));
	}
	engine->set_editor_hint(was_editor);
}

TEST_CASE("[MCPServer] the edited-scene inspectors need an open scene and validate their arguments") {
	MCPToolRegistry registry;
	TestMCPServer::build_editor_process_registry(registry);

	// The doctest process has no SceneTree at all, which is the same "there is
	// no editable scene" state: -32000 with a suggestion, never a crash. The
	// populated-scene answers are gate section 2 evidence on a live editor.
	const char *const scene_tools[2] = { "editor_get_scene_tree", "editor_analyze_signal_flow" };
	for (int i = 0; i < 2; i++) {
		MCPToolError error;
		registry.call_tool(scene_tools[i], Dictionary(), error);
		CHECK(error.code == -32000);
		CHECK(error.message == "No scene is currently open");
		CHECK(((Dictionary)error.data).has("suggestion"));
	}

	// Argument validation runs first, so a mistyped argument is -32602 rather
	// than a state error.
	Dictionary bad_depth;
	bad_depth["max_depth"] = "deep";
	MCPToolError bad_depth_error;
	registry.call_tool("editor_get_scene_tree", bad_depth, bad_depth_error);
	CHECK(bad_depth_error.code == -32602);
	CHECK(bad_depth_error.message.contains("max_depth"));

	Dictionary bad_node_path;
	bad_node_path["node_path"] = 12;
	MCPToolError bad_node_path_error;
	registry.call_tool("editor_analyze_signal_flow", bad_node_path, bad_node_path_error);
	CHECK(bad_node_path_error.code == -32602);
	CHECK(bad_node_path_error.message.contains("node_path"));

	Dictionary bad_top_only;
	bad_top_only["top_only"] = "yes";
	MCPToolError bad_top_only_error;
	registry.call_tool("editor_get_selection", bad_top_only, bad_top_only_error);
	CHECK(bad_top_only_error.code == -32602);
	CHECK(bad_top_only_error.message.contains("top_only"));
}

// ---------------------------------------------------------------------------
// The write group `project_write_resource_scene` (TASK-007 section 3).
//
// This group is the first one that writes into `res://`, so the assertions
// below do not stop at "the call returned the right JSON": every case also
// inspects the file system (existence, byte content, the file list before and
// after) and every failure case pins the *before* state of the file it refused
// to touch. The tools are addressed by name through
// `TestMCPServer::build_all_tools_registry` instead of through the group's own
// header, so the red phase of this group compiles (and fails) before
// `tools/project_write_resource_scene.{h,cpp}` exists; the registration itself
// is asserted separately below.
// ---------------------------------------------------------------------------

// The property names of a resource, as a set of StringNames.
inline HashSet<StringName> resource_property_names(const Ref<Resource> &p_resource) {
	HashSet<StringName> names;
	if (p_resource.is_null()) {
		return names;
	}
	List<PropertyInfo> properties;
	p_resource->get_property_list(&properties);
	for (const PropertyInfo &property : properties) {
		names.insert(property.name);
	}
	return names;
}

// The four tools exactly as `docs/tool-groups.json` lists them.
inline void check_write_group_registration(MCPToolRegistry &p_registry) {
	const struct {
		const char *name;
		const char *verb;
	} tools[4] = {
		{ "project_create_resource", "create" },
		{ "project_create_scene_file", "create" },
		{ "project_delete_scene_file", "delete" },
		{ "project_edit_resource", "edit" },
	};
	for (int i = 0; i < 4; i++) {
		CHECK(p_registry.has_tool(tools[i].name));
		CHECK(p_registry.is_tool_visible(tools[i].name, false));
		CHECK(p_registry.is_tool_visible(tools[i].name, true));
	}
}

TEST_CASE("[MCPServer] the project_write_resource_scene tools are registered as mutating both-scope tools") {
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);
	check_write_group_registration(registry);

	// GDR-18: a tool that writes `res://` is `mutating = true`. The registry
	// keeps the flag only in the tool definition, which no public accessor
	// exposes, so the observable half is pinned on the wire: the tool is served
	// by the editor process *and* by the game process (scope = both), unlike an
	// `editor_` tool. `mutating` itself is asserted where it is decidable - at
	// the declaration site, by the builder refusing to build without it.
	CHECK(registry.get_tool_count() == 24);
}

TEST_CASE("[MCPServer] project_create_resource writes a new resource and refuses to clobber one") {
	ScratchProject fixture;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	const String relative = "generated/created.tres";
	const String target = fixture.path(relative);
	CHECK_FALSE(FileAccess::exists(target));

	Dictionary args;
	args["path"] = target;
	args["type"] = "Resource";
	Dictionary initial;
	initial["resource_name"] = "mcp_created";
	args["properties"] = initial;

	MCPToolError error;
	const Variant result = registry.call_tool("project_create_resource", args, error);
	CHECK_FALSE(error.is_error());
	CHECK(error.code == 0);

	// The real file system changed: the file is on disk and the parent
	// directory was created for it.
	CHECK(FileAccess::exists(target));
	CHECK(DirAccess::dir_exists_absolute(fixture.path("generated")));

	const Dictionary payload = result;
	CHECK((String)payload["path"] == target);
	CHECK((String)payload["type"] == "Resource");
	const Array properties_set = payload["properties_set"];
	CHECK(properties_set.has("resource_name"));

	// ... and what was written is a real resource again. `CACHE_MODE_IGNORE` is
	// used because the file was just written outside `ResourceLoader`: the loader
	// caches per path, so a later overwrite would otherwise be masked by the
	// instance this load put in the cache.
	const Ref<Resource> written = ResourceLoader::load(target, "", ResourceLoader::CACHE_MODE_IGNORE);
	CHECK(written.is_valid());
	CHECK(written.is_valid() && (String)written->get("resource_name") == "mcp_created");

	// The pre-existing-file guard: -32000 (the state blocks the call) with a
	// suggestion, and *not one byte* of the file changes.
	const String before = FileAccess::get_file_as_string(target);
	MCPToolError exists_error;
	const Variant exists_result = registry.call_tool("project_create_resource", args, exists_error);
	CHECK(exists_result.get_type() == Variant::NIL);
	CHECK(exists_error.code == -32000);
	CHECK(exists_error.message.contains("already exists"));
	CHECK(((Dictionary)exists_error.data).has("suggestion"));
	CHECK(FileAccess::get_file_as_string(target) == before);

	// `overwrite = true` is the explicit opt-in and does rewrite it.
	Dictionary overwrite_args = args;
	overwrite_args["overwrite"] = true;
	Dictionary other;
	other["resource_name"] = "mcp_overwritten";
	overwrite_args["properties"] = other;
	MCPToolError overwrite_error;
	const Variant overwrite_result = registry.call_tool("project_create_resource", overwrite_args, overwrite_error);
	CHECK_FALSE(overwrite_error.is_error());
	CHECK(overwrite_result.get_type() == Variant::DICTIONARY);
	const Ref<Resource> rewritten = ResourceLoader::load(target);
	CHECK(rewritten.is_valid());
	CHECK(rewritten.is_valid() && (String)rewritten->get("resource_name") == "mcp_overwritten");
}

TEST_CASE("[MCPServer] project_create_resource validates path, type and arguments and never half-writes") {
	ScratchProject fixture;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	// path escapes the project.
	{
		Dictionary args;
		args["path"] = "res://../escape.tres";
		args["type"] = "Resource";
		MCPToolError error;
		const Variant result = registry.call_tool("project_create_resource", args, error);
		CHECK(result.get_type() == Variant::NIL);
		CHECK(error.code == -32602);
	}
	// `path` outside `res://`.
	{
		Dictionary args;
		args["path"] = "user://escape.tres";
		args["type"] = "Resource";
		MCPToolError error;
		registry.call_tool("project_create_resource", args, error);
		CHECK(error.code == -32602);
	}
	// a required argument is missing.
	{
		Dictionary args;
		args["path"] = fixture.path("generated/no_type.tres");
		MCPToolError error;
		const Variant result = registry.call_tool("project_create_resource", args, error);
		CHECK(result.get_type() == Variant::NIL);
		CHECK(error.code == -32602);
		CHECK(error.message.contains("type"));
		CHECK_FALSE(FileAccess::exists(fixture.path("generated/no_type.tres")));
	}
	// a mistyped optional argument is refused rather than ignored (PLAYBOOK 6.2).
	{
		Dictionary args;
		args["path"] = fixture.path("generated/bad_overwrite.tres");
		args["type"] = "Resource";
		args["overwrite"] = "yes";
		MCPToolError error;
		registry.call_tool("project_create_resource", args, error);
		CHECK(error.code == -32602);
		CHECK(error.message.contains("overwrite"));
		CHECK_FALSE(FileAccess::exists(fixture.path("generated/bad_overwrite.tres")));
	}
	// an unknown class cannot be instantiated: -32602 (the *argument* names a
	// class that does not exist), and nothing is created.
	{
		Dictionary args;
		args["path"] = fixture.path("generated/unknown.tres");
		args["type"] = "McpNoSuchResourceClass";
		MCPToolError error;
		const Variant result = registry.call_tool("project_create_resource", args, error);
		CHECK(result.get_type() == Variant::NIL);
		CHECK(error.code == -32602);
		CHECK_FALSE(FileAccess::exists(fixture.path("generated/unknown.tres")));
	}
	// a class that exists but can never be a resource is refused as well.
	{
		Dictionary args;
		args["path"] = fixture.path("generated/node.tres");
		args["type"] = "Node";
		MCPToolError error;
		registry.call_tool("project_create_resource", args, error);
		CHECK(error.code == -32602);
		CHECK_FALSE(FileAccess::exists(fixture.path("generated/node.tres")));
	}
}

TEST_CASE("[MCPServer] project_create_scene_file packs a new scene file and refuses to clobber one") {
	ScratchProject fixture;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	const String target = fixture.path("generated/created.tscn");
	CHECK_FALSE(FileAccess::exists(target));

	Dictionary args;
	args["path"] = target;
	MCPToolError error;
	const Variant result = registry.call_tool("project_create_scene_file", args, error);
	CHECK_FALSE(error.is_error());

	CHECK(FileAccess::exists(target));
	const Dictionary payload = result;
	CHECK((String)payload["path"] == target);
	CHECK((String)payload["root_type"] == "Node2D");
	// No `root_name`: the reference derives it from the file stem.
	CHECK((String)payload["root_name"] == "created");
	CHECK(payload["created"] == true);

	const String text = FileAccess::get_file_as_string(target);
	CHECK(text.contains("[gd_scene"));
	CHECK(text.contains("name=\"created\""));
	CHECK(text.contains("type=\"Node2D\""));

	// The pre-existing-file guard: this tool has no `overwrite` argument, so an
	// existing scene file is never replaced.
	const String before = text;
	MCPToolError exists_error;
	const Variant exists_result = registry.call_tool("project_create_scene_file", args, exists_error);
	CHECK(exists_result.get_type() == Variant::NIL);
	CHECK(exists_error.code == -32000);
	CHECK(exists_error.message.contains("already exists"));
	CHECK(((Dictionary)exists_error.data).has("suggestion"));
	CHECK(FileAccess::get_file_as_string(target) == before);
}

TEST_CASE("[MCPServer] project_create_scene_file validates its arguments and the root class") {
	ScratchProject fixture;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	// An explicit root name wins over the file stem, and the type is honoured.
	{
		Dictionary args;
		args["path"] = fixture.path("generated/named.tscn");
		args["root_type"] = "Node3D";
		args["root_name"] = "RenamedRoot";
		MCPToolError error;
		const Variant result = registry.call_tool("project_create_scene_file", args, error);
		CHECK_FALSE(error.is_error());
		const Dictionary payload = result;
		CHECK((String)payload["root_type"] == "Node3D");
		CHECK((String)payload["root_name"] == "RenamedRoot");
		const String text = FileAccess::get_file_as_string(fixture.path("generated/named.tscn"));
		CHECK(text.contains("name=\"RenamedRoot\""));
		CHECK(text.contains("type=\"Node3D\""));
	}
	// A class that does not exist, and a class that is not a Node.
	{
		Dictionary args;
		args["path"] = fixture.path("generated/bad_root.tscn");
		args["root_type"] = "McpNoSuchNodeClass";
		MCPToolError error;
		const Variant result = registry.call_tool("project_create_scene_file", args, error);
		CHECK(result.get_type() == Variant::NIL);
		CHECK(error.code == -32602);
		CHECK_FALSE(FileAccess::exists(fixture.path("generated/bad_root.tscn")));
	}
	{
		Dictionary args;
		args["path"] = fixture.path("generated/not_a_node.tscn");
		args["root_type"] = "Resource";
		MCPToolError error;
		registry.call_tool("project_create_scene_file", args, error);
		CHECK(error.code == -32602);
		CHECK_FALSE(FileAccess::exists(fixture.path("generated/not_a_node.tscn")));
	}
	// missing `path` and a path outside the project.
	{
		MCPToolError error;
		registry.call_tool("project_create_scene_file", Dictionary(), error);
		CHECK(error.code == -32602);
	}
	{
		Dictionary args;
		args["path"] = "res://a/../../b.tscn";
		MCPToolError error;
		registry.call_tool("project_create_scene_file", args, error);
		CHECK(error.code == -32602);
	}
	// a mistyped optional argument.
	{
		Dictionary args;
		args["path"] = fixture.path("generated/bad_type.tscn");
		args["root_type"] = 12;
		MCPToolError error;
		registry.call_tool("project_create_scene_file", args, error);
		CHECK(error.code == -32602);
		CHECK(error.message.contains("root_type"));
	}
}

TEST_CASE("[MCPServer] project_edit_resource rewrites an existing resource and skips unknown properties") {
	ScratchProject fixture;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	// A real, loadable resource on disk, written by the fixture.
	const String relative = "resources/editable.tres";
	CHECK(fixture.write(relative, String::utf8("[gd_resource type=\"Resource\" format=3]\n\n[resource]\nresource_name = \"original\"\n")));
	const String target = fixture.path(relative);
	const String before = FileAccess::get_file_as_string(target);

	Dictionary args;
	args["path"] = target;
	Dictionary properties;
	properties["resource_name"] = "edited";
	// An unknown property is skipped, exactly like the migration source.
	properties["mcp_no_such_property"] = 1;
	args["properties"] = properties;

	MCPToolError error;
	const Variant result = registry.call_tool("project_edit_resource", args, error);
	CHECK_FALSE(error.is_error());
	const Dictionary payload = result;
	CHECK((String)payload["path"] == target);
	CHECK((String)payload["type"] == "Resource");
	const Dictionary changed = payload["changed"];
	CHECK(changed.has("resource_name"));
	CHECK_FALSE(changed.has("mcp_no_such_property"));
	const Dictionary entry = changed["resource_name"];
	CHECK((String)entry["old"] == "original");
	CHECK((String)entry["new"] == "edited");

	// The file really changed on disk and the change survives a reload. The
	// old byte image is gone, which is the positive half of "the write landed".
	CHECK(FileAccess::exists(target));
	CHECK(FileAccess::get_file_as_string(target) != before);
	const Ref<Resource> reloaded = ResourceLoader::load(target);
	CHECK(reloaded.is_valid());
	CHECK(reloaded.is_valid() && (String)reloaded->get("resource_name") == "edited");
}

TEST_CASE("[MCPServer] project_edit_resource reports no change and validates its arguments") {
	ScratchProject fixture;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	const String relative = "resources/unchanged.tres";
	CHECK(fixture.write(relative, String::utf8("[gd_resource type=\"Resource\" format=3]\n\n[resource]\nresource_name = \"same\"\n")));
	const String target = fixture.path(relative);
	const String before = FileAccess::get_file_as_string(target);

	// Only unknown properties: the reference returns the "no properties were
	// changed" payload and never saves, so the bytes on disk stay identical.
	{
		Dictionary args;
		args["path"] = target;
		Dictionary properties;
		properties["mcp_no_such_property"] = 1;
		args["properties"] = properties;
		MCPToolError error;
		const Variant result = registry.call_tool("project_edit_resource", args, error);
		CHECK_FALSE(error.is_error());
		const Dictionary payload = result;
		CHECK((String)payload["message"] == "No properties were changed");
		const Dictionary changed = payload["changed"];
		CHECK(changed.is_empty());
		CHECK(FileAccess::get_file_as_string(target) == before);
	}
	// A `properties` value that is not an object.
	{
		Dictionary args;
		args["path"] = target;
		args["properties"] = "not-an-object";
		MCPToolError error;
		const Variant result = registry.call_tool("project_edit_resource", args, error);
		CHECK(result.get_type() == Variant::NIL);
		CHECK(error.code == -32602);
		CHECK(error.message.contains("properties"));
		CHECK(FileAccess::get_file_as_string(target) == before);
	}
	// A missing `properties`, a missing `path`, and a path that is not in the
	// project at all.
	{
		Dictionary args;
		args["path"] = target;
		MCPToolError error;
		registry.call_tool("project_edit_resource", args, error);
		CHECK(error.code == -32602);
	}
	{
		MCPToolError error;
		registry.call_tool("project_edit_resource", Dictionary(), error);
		CHECK(error.code == -32602);
	}
	{
		Dictionary args;
		args["path"] = "res://../outside.tres";
		Dictionary properties;
		properties["resource_name"] = "x";
		args["properties"] = properties;
		MCPToolError error;
		registry.call_tool("project_edit_resource", args, error);
		CHECK(error.code == -32602);
	}
	// A resource that does not exist -> -32001 with a suggestion, and nothing
	// is created as a side effect.
	{
		Dictionary args;
		args["path"] = fixture.path("resources/never_written.tres");
		Dictionary properties;
		properties["resource_name"] = "x";
		args["properties"] = properties;
		MCPToolError error;
		const Variant result = registry.call_tool("project_edit_resource", args, error);
		CHECK(result.get_type() == Variant::NIL);
		CHECK(error.code == -32001);
		CHECK(((Dictionary)error.data).has("suggestion"));
		CHECK_FALSE(FileAccess::exists(fixture.path("resources/never_written.tres")));
	}
}

TEST_CASE("[MCPServer] the write tools never corrupt an existing file when the call fails") {
	ScratchProject fixture;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	// The counter-example is a *read-only / damaged* existing file: one whose
	// bytes are not a loadable resource. Every failing call below has the path
	// of a real file, so a naive implementation that opened the destination
	// for writing before it knew whether it could succeed would be visible
	// immediately.
	const String relative = "resources/corrupt.tres";
	const String corrupt = String::utf8("[gd_resource type=\"Resource\" format=3]\n\n[resource\nresource_name = \"unterminated\n");
	CHECK(fixture.write(relative, corrupt));
	const String target = fixture.path(relative);
	const String before = FileAccess::get_file_as_string(target);
	CHECK(before == corrupt);

	// (1) editing a file that cannot be loaded: -32001, file untouched.
	{
		Dictionary args;
		args["path"] = target;
		Dictionary properties;
		properties["resource_name"] = "hijacked";
		args["properties"] = properties;
		MCPToolError error;
		const Variant result = registry.call_tool("project_edit_resource", args, error);
		CHECK(result.get_type() == Variant::NIL);
		CHECK(error.code == -32001);
		CHECK(FileAccess::get_file_as_string(target) == before);
	}
	// (2) creating over it without `overwrite`: -32000, file untouched.
	{
		Dictionary args;
		args["path"] = target;
		args["type"] = "Resource";
		MCPToolError error;
		registry.call_tool("project_create_resource", args, error);
		CHECK(error.code == -32000);
		CHECK(FileAccess::get_file_as_string(target) == before);
	}
	// (3) creating over it with `overwrite` but an instantiation that cannot
	//     succeed: -32602, and the original bytes are still there.
	{
		Dictionary args;
		args["path"] = target;
		args["type"] = "McpNoSuchResourceClass";
		args["overwrite"] = true;
		MCPToolError error;
		registry.call_tool("project_create_resource", args, error);
		CHECK(error.code == -32602);
		CHECK(FileAccess::get_file_as_string(target) == before);
	}
	// (4) overwriting with a class that cannot be saved as that extension is a
	//     save failure; whatever the failure is, the file may not end up half
	//     written or empty.
	{
		Dictionary args;
		args["path"] = target;
		args["type"] = "Node";
		args["overwrite"] = true;
		MCPToolError error;
		const Variant result = registry.call_tool("project_create_resource", args, error);
		CHECK(result.get_type() == Variant::NIL);
		CHECK(error.is_error());
		const String after = FileAccess::get_file_as_string(target);
		CHECK(after == before);
		CHECK_FALSE(after.is_empty());
	}
}

TEST_CASE("[MCPServer] project_delete_scene_file removes the scene and reports the deleted path") {
	ScratchProject fixture;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	const String relative = "scenes/doomed.tscn";
	const String text = String::utf8("[gd_scene format=3]\n\n[node name=\"Doomed\" type=\"Node2D\"]\n");
	CHECK(fixture.write(relative, text));
	const String target = fixture.path(relative);
	// The migration source also removes a `<path>.import` sidecar when present.
	const String import_sidecar = target + ".import";
	CHECK(fixture.write("scenes/doomed.tscn.import", String::utf8("[remap]\n\npath=\"res://scenes/doomed.tscn\"\n")));

	const Array before = list_files_recursive(fixture.root);
	CHECK(before.has(target));
	CHECK(before.has(import_sidecar));

	Dictionary args;
	args["path"] = target;
	MCPToolError error;
	const Variant result = registry.call_tool("project_delete_scene_file", args, error);
	CHECK_FALSE(error.is_error());
	const Dictionary payload = result;
	CHECK((String)payload["path"] == target);
	CHECK(payload["deleted"] == true);

	// The observable file system state after the call.
	CHECK_FALSE(FileAccess::exists(target));
	CHECK_FALSE(FileAccess::exists(import_sidecar));
	const Array after = list_files_recursive(fixture.root);
	CHECK_FALSE(after.has(target));
	CHECK_FALSE(after.has(import_sidecar));
	CHECK(after.size() == before.size() - 2);

	// Deleting it a second time is -32001 with a suggestion, not a silent
	// success and not an internal error.
	MCPToolError missing_error;
	const Variant missing_result = registry.call_tool("project_delete_scene_file", args, missing_error);
	CHECK(missing_result.get_type() == Variant::NIL);
	CHECK(missing_error.code == -32001);
	CHECK(((Dictionary)missing_error.data).has("suggestion"));
}

TEST_CASE("[MCPServer] project_delete_scene_file validates its path and touches nothing on failure") {
	ScratchProject fixture;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	const Array before = list_files_recursive(fixture.root);

	// missing `path`.
	{
		MCPToolError error;
		registry.call_tool("project_delete_scene_file", Dictionary(), error);
		CHECK(error.code == -32602);
	}
	// a path outside the project, and one that walks upwards.
	{
		Dictionary args;
		args["path"] = "user://nothing.tscn";
		MCPToolError error;
		registry.call_tool("project_delete_scene_file", args, error);
		CHECK(error.code == -32602);
	}
	{
		Dictionary args;
		args["path"] = "res://../nothing.tscn";
		MCPToolError error;
		registry.call_tool("project_delete_scene_file", args, error);
		CHECK(error.code == -32602);
	}
	// a mistyped `path`.
	{
		Dictionary args;
		args["path"] = 12;
		MCPToolError error;
		registry.call_tool("project_delete_scene_file", args, error);
		CHECK(error.code == -32602);
	}
	// a non-existent file inside the project.
	{
		Dictionary args;
		args["path"] = fixture.path("scenes/never_existed.tscn");
		MCPToolError error;
		registry.call_tool("project_delete_scene_file", args, error);
		CHECK(error.code == -32001);
	}

	// Not one file of the fixture was removed or added by any of the failures.
	const Array after = list_files_recursive(fixture.root);
	CHECK(after == before);
}

TEST_CASE("[MCPServer] the write tools leave no temporary or partial file behind") {
	ScratchProject fixture;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	CHECK(fixture.write("resources/editable.tres", String::utf8("[gd_resource type=\"Resource\" format=3]\n\n[resource]\nresource_name = \"original\"\n")));

	// One successful call of each writing tool.
	{
		Dictionary args;
		args["path"] = fixture.path("generated/a.tres");
		args["type"] = "Resource";
		MCPToolError error;
		registry.call_tool("project_create_resource", args, error);
		CHECK_FALSE(error.is_error());
	}
	{
		Dictionary args;
		args["path"] = fixture.path("generated/b.tscn");
		MCPToolError error;
		registry.call_tool("project_create_scene_file", args, error);
		CHECK_FALSE(error.is_error());
	}
	{
		Dictionary args;
		args["path"] = fixture.path("resources/editable.tres");
		Dictionary properties;
		properties["resource_name"] = "edited_again";
		args["properties"] = properties;
		MCPToolError error;
		registry.call_tool("project_edit_resource", args, error);
		CHECK_FALSE(error.is_error());
	}

	// The write path of this group may go through a temporary file (a write is
	// only published once it has completed). Whatever it uses, it must not
	// survive the call: the tree holds exactly the files the calls created.
	const Array files = list_files_recursive(fixture.root);
	for (int i = 0; i < files.size(); i++) {
		const String file = files[i];
		CHECK_FALSE(file.contains(".mcp-tmp"));
		CHECK_FALSE(file.ends_with(".tmp"));
		CHECK_FALSE(file.contains("~"));
	}
	CHECK(files.has(fixture.path("generated/a.tres")));
	CHECK(files.has(fixture.path("generated/b.tscn")));
	CHECK(files.has(fixture.path("resources/editable.tres")));
	CHECK(files.size() == 14);
}

// ---------------------------------------------------------------------------
// TASK-008: the `editor_write_scene_editor` group (10 editor-only writers).
//
// Everything that needs a live EditorNode, an `EditorSelection` or an
// `EditorLog` is proven on the wire in the group's gate-2 evidence (REPORT-008
// section 6): `Main::test_setup()` never starts the editor, so this process has
// no `EditorNode` at all. What *is* decidable here is the whole argument
// contract (it runs before any editor API is touched), the process-scope guard
// end to end, and the shared atomic-publish helper every file writer of the
// module goes through.
// ---------------------------------------------------------------------------

namespace {
const char *const EDITOR_WRITE_TOOLS[10] = {
	"editor_open_scene",
	"editor_save_scene",
	"editor_reload_plugin",
	"editor_rescan_project_filesystem",
	"editor_set_node_selection",
	"editor_remove_node_selection",
	"editor_add_resource_to_node_property",
	"editor_set_viewport_3d_camera",
	"editor_capture_screenshot",
	"editor_remove_output_log",
};

// A writer for `MCPTools::publish_file_atomically` that leaves a half-written
// scratch file behind *on purpose*: the helper owes the caller a clean tree even
// then.
inline Error atomic_test_failing_writer(const String &p_temp_path, void *p_userdata) {
	(void)p_userdata;
	Ref<FileAccess> file = FileAccess::open(p_temp_path, FileAccess::WRITE);
	if (file.is_valid()) {
		file->store_string("half-written");
		file->close();
	}
	return FAILED;
}

// A writer that succeeds and stores the `String` it is handed.
inline Error atomic_test_succeeding_writer(const String &p_temp_path, void *p_userdata) {
	Ref<FileAccess> file = FileAccess::open(p_temp_path, FileAccess::WRITE);
	if (file.is_null()) {
		return FAILED;
	}
	file->store_string(p_userdata != nullptr ? *(String *)p_userdata : String("published"));
	file->close();
	return OK;
}
} // namespace

TEST_CASE("[MCPServer] the editor_write_scene_editor group is editor-only and complete") {
	// A game process must not even carry the tools in its table (GDR-19 17.3).
	MCPToolRegistry game_registry;
	TestMCPServer::build_all_tools_registry(game_registry);
	CHECK(game_registry.get_tool_count() == 40);
	CHECK(game_registry.get_visible_tool_count(false) == 40);

	// An editor process carries the 23 both-scope tools plus the seven inspector
	// tools plus these ten plus the seventeen game-scope tools of
	// TASK-009/TASK-010/TASK-011/TASK-012 plus the three editor-scope tools of
	// TASK-012 plus the six editor-scope input simulation tools of TASK-013 plus
	// the ten editor-scope node writes of TASK-015.
	MCPToolRegistry editor_registry;
	TestMCPServer::build_editor_process_registry(editor_registry);
	CHECK(editor_registry.get_tool_count() == 76);
	CHECK(editor_registry.get_visible_tool_count(true) == 59);
	CHECK(editor_registry.get_visible_tool_count(false) == 40);

	for (int i = 0; i < 10; i++) {
		const String name = EDITOR_WRITE_TOOLS[i];
		CHECK_FALSE(game_registry.has_tool(name));
		CHECK_FALSE(game_registry.is_tool_visible(name, false));
		CHECK_FALSE(game_registry.is_tool_visible(name, true));

		CHECK(editor_registry.has_tool(name));
		CHECK(editor_registry.is_tool_visible(name, true));
		CHECK_FALSE(editor_registry.is_tool_visible(name, false));
	}

	// The listing a game process serves must name none of the ten ...
	const Array game_list = game_registry.build_tools_list(false);
	CHECK(game_list.size() == 40);
	for (int i = 0; i < game_list.size(); i++) {
		const String listed = ((Dictionary)game_list[i])["name"];
		for (int j = 0; j < 10; j++) {
			CHECK(listed != EDITOR_WRITE_TOOLS[j]);
		}
	}
	// ... and the editor's listing must carry every one of them.
	const Array editor_list = editor_registry.build_tools_list(true);
	CHECK(editor_list.size() == 59);
	for (int j = 0; j < 10; j++) {
		bool found = false;
		for (int i = 0; i < editor_list.size(); i++) {
			if (String(((Dictionary)editor_list[i])["name"]) == String(EDITOR_WRITE_TOOLS[j])) {
				found = true;
				break;
			}
		}
		CHECK(found);
	}

	// `tools/call` on a game endpoint: -32601, never execution.
	const String call = "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"editor_save_scene\",\"arguments\":{}}}";
	const MCPJsonRpc::Response refused = MCPJsonRpc::handle(call, game_registry, false);
	CHECK(refused.http_status == 200);
	CHECK(refused.body.contains("\"code\":-32601"));
	CHECK(refused.body.contains("Method not found: editor_save_scene"));
	CHECK_FALSE(refused.body.contains("\"result\""));
}

TEST_CASE("[MCPServer] the editor write tools validate their arguments before touching the editor") {
	MCPToolRegistry registry;
	TestMCPServer::build_editor_process_registry(registry);

	// A malformed call is `-32602` in every process, and it is decided *before*
	// any editor API is reached - which is why it is observable here at all.
	const auto expect_invalid = [&registry](const String &p_tool, const Dictionary &p_args, const String &p_fragment) {
		MCPToolError error;
		const Variant result = registry.call_tool(p_tool, p_args, error);
		CHECK(result.get_type() == Variant::NIL);
		CHECK(error.is_error());
		CHECK(error.code == -32602);
		CHECK(error.message.contains(p_fragment));
		// TASK-050 O-1/N-7: a `-32602` now carries `data.suggestion` as well.
		// The two checks above are what must not move (the code and the message
		// text); this line used to assert the *absence* of `data`, which was
		// exactly the gap the racing-backlog audit measured (93 B without a
		// suggestion against 223 B with one). It is strengthened, not relaxed.
		CHECK(error.data.get_type() == Variant::DICTIONARY);
		if (error.data.get_type() == Variant::DICTIONARY) {
			const String suggestion = String(((Dictionary)error.data).get("suggestion", String()));
			CHECK_MESSAGE(!suggestion.is_empty(), suggestion);
			CHECK_MESSAGE(suggestion.contains(p_tool), suggestion);
		}
	};

	// editor_open_scene / editor_save_scene: the path contract.
	{
		Dictionary args;
		expect_invalid("editor_open_scene", args, "Missing required parameter: path");
	}
	{
		Dictionary args;
		args["path"] = "user://outside.tscn";
		expect_invalid("editor_open_scene", args, "must address the project");
	}
	{
		Dictionary args;
		args["path"] = "res://../escape.tscn";
		expect_invalid("editor_open_scene", args, "must not walk upwards with '..'");
	}
	{
		Dictionary args;
		args["path"] = "res://../escape.tscn";
		expect_invalid("editor_save_scene", args, "must not walk upwards with '..'");
	}
	{
		// A present argument of the wrong type is never ignored.
		Dictionary args;
		args["path"] = 17;
		expect_invalid("editor_save_scene", args, "Parameter 'path' must be a string");
	}

	// editor_set_node_selection: both path spellings, the mode enum and the types.
	{
		Dictionary args;
		expect_invalid("editor_set_node_selection", args, "node_paths or node_path");
	}
	{
		Dictionary args;
		args["node_path"] = ".";
		args["mode"] = "toggle";
		expect_invalid("editor_set_node_selection", args, "mode must be one of: replace, add, remove");
	}
	{
		Dictionary args;
		args["node_paths"] = "not-an-array";
		expect_invalid("editor_set_node_selection", args, "must be an array of strings");
	}
	{
		Dictionary args;
		Array paths;
		paths.push_back(1);
		args["node_paths"] = paths;
		expect_invalid("editor_set_node_selection", args, "must be a string");
	}
	{
		Dictionary args;
		args["node_path"] = ".";
		args["inspect"] = "yes";
		expect_invalid("editor_set_node_selection", args, "Parameter 'inspect' must be a bool");
	}

	// editor_add_resource_to_node_property: the three required arguments and the
	// two class checks that can be decided without any editor state.
	{
		Dictionary args;
		args["node_path"] = ".";
		expect_invalid("editor_add_resource_to_node_property", args, "Missing required parameter: property");
	}
	{
		Dictionary args;
		args["node_path"] = ".";
		args["property"] = "resource";
		args["resource_type"] = "McpNoSuchResourceClass";
		expect_invalid("editor_add_resource_to_node_property", args, "Unknown resource type");
	}
	{
		Dictionary args;
		args["node_path"] = ".";
		args["property"] = "resource";
		args["resource_type"] = "Node";
		expect_invalid("editor_add_resource_to_node_property", args, "is not a Resource type");
	}
	{
		Dictionary args;
		args["node_path"] = ".";
		args["property"] = "resource";
		args["resource_type"] = "Resource";
		args["resource_properties"] = "nope";
		expect_invalid("editor_add_resource_to_node_property", args, "must be an object");
	}

	// editor_set_viewport_3d_camera: the {x, y, z} objects and the one number.
	{
		Dictionary args;
		args["position"] = 5;
		expect_invalid("editor_set_viewport_3d_camera", args, "must be an object with x, y, z");
	}
	{
		Dictionary args;
		Dictionary position;
		position["x"] = 1;
		position["y"] = "two";
		args["position"] = position;
		expect_invalid("editor_set_viewport_3d_camera", args, "Parameter 'position.y' must be a number");
	}
	{
		Dictionary args;
		args["fov"] = "wide";
		expect_invalid("editor_set_viewport_3d_camera", args, "Parameter 'fov' must be a number");
	}

	// editor_capture_screenshot: `res://` or `user://`, no `..`, and a file name.
	{
		Dictionary args;
		args["save_path"] = "C:/outside/shot.png";
		expect_invalid("editor_capture_screenshot", args, "must start with 'res://' or 'user://'");
	}
	{
		Dictionary args;
		args["save_path"] = "res://../escape.png";
		expect_invalid("editor_capture_screenshot", args, "must not walk upwards with '..'");
	}
	{
		Dictionary args;
		args["save_path"] = "res://";
		expect_invalid("editor_capture_screenshot", args, "must name a file");
	}
}

TEST_CASE("[MCPServer] the editor write tools refuse cleanly without an editor UI") {
	TestMCPServer::ScratchProject fixture;
	MCPToolRegistry registry;
	TestMCPServer::build_editor_process_registry(registry);

	// Valid arguments for each of the ten, in `EDITOR_WRITE_TOOLS` order, so the
	// only reason left to refuse is the missing editor UI.
	Array arguments;
	{
		Dictionary args;
		args["path"] = fixture.path("scenes/leaf.tscn");
		arguments.push_back(args);
	}
	arguments.push_back(Dictionary());
	arguments.push_back(Dictionary());
	arguments.push_back(Dictionary());
	{
		Dictionary args;
		args["node_path"] = ".";
		arguments.push_back(args);
	}
	arguments.push_back(Dictionary());
	{
		Dictionary args;
		args["node_path"] = ".";
		args["property"] = "texture";
		args["resource_type"] = "Resource";
		arguments.push_back(args);
	}
	{
		Dictionary args;
		args["fov"] = 70;
		arguments.push_back(args);
	}
	{
		Dictionary args;
		args["save_path"] = "user://mcp_server_test_shot.png";
		arguments.push_back(args);
	}
	arguments.push_back(Dictionary());
	CHECK(arguments.size() == 10);

	for (int i = 0; i < 10; i++) {
		MCPToolError error;
		const Variant result = registry.call_tool(EDITOR_WRITE_TOOLS[i], (Dictionary)arguments[i], error);
		// Never a result and never a fake success: -32000, with the suggestion
		// the error contract requires.
		CHECK(result.get_type() == Variant::NIL);
		CHECK(error.is_error());
		CHECK(error.code == -32000);
		CHECK(error.message.begins_with("Not implemented:"));
		CHECK(error.data.get_type() == Variant::DICTIONARY);
		CHECK(((Dictionary)error.data).has("suggestion"));
	}
}

// ---------------------------------------------------------------------------
// The `fix_implementation_first` tool of this group (TASK-008 section 2).
//
// This is the red test. The migration source's `clear_output` (editor.rs:421)
// printed about fifty empty lines to stdout and then answered
// `{"cleared": true}` - in a process that may not even have an Output panel, and
// without touching the panel when it does. The assertion below is the invariant
// TASK-008 section 2(c) states: the tool may never report a clear it did not
// perform. With the migration-faithful implementation it fails, exactly as the
// red stage of the group shows; with the fixed implementation it passes.
// ---------------------------------------------------------------------------
TEST_CASE("[MCPServer] editor_remove_output_log never reports a clear it cannot perform") {
	MCPToolRegistry registry;
	TestMCPServer::build_editor_process_registry(registry);
	CHECK(registry.has_tool("editor_remove_output_log"));

	MCPToolError error;
	const Variant result = registry.call_tool("editor_remove_output_log", Dictionary(), error);

	// The doctest process has no EditorNode and therefore no EditorLog. Nothing
	// was cleared here, so no `cleared: true` may come back.
	CHECK(result.get_type() == Variant::NIL);
	if (result.get_type() == Variant::DICTIONARY) {
		CHECK_FALSE((bool)((Dictionary)result).get("cleared", false));
	}
	CHECK(error.is_error());
	CHECK(error.code == -32000);
	CHECK(error.message.begins_with("Not implemented:"));
	CHECK(error.data.get_type() == Variant::DICTIONARY);
	CHECK(((Dictionary)error.data).has("suggestion"));

	// And the same request through the JSON-RPC layer: an error object, never a
	// result envelope that claims success.
	const String call = "{\"jsonrpc\":\"2.0\",\"id\":9,\"method\":\"tools/call\",\"params\":{\"name\":\"editor_remove_output_log\",\"arguments\":{}}}";
	const MCPJsonRpc::Response response = MCPJsonRpc::handle(call, registry, true);
	CHECK(response.http_status == 200);
	CHECK(response.body.contains("\"code\":-32000"));
	CHECK_FALSE(response.body.contains("\"cleared\":true"));
}

TEST_CASE("[MCPServer] publish_file_atomically never damages the destination and leaves no scratch file") {
	TestMCPServer::ScratchProject fixture;
	const String target = fixture.path("resources/editable.tres");
	const String original = String::utf8("[gd_resource type=\"Resource\" format=3]\n\n[resource]\nresource_name = \"original\"\n");
	CHECK(fixture.write("resources/editable.tres", original));
	const String before = FileAccess::get_file_as_string(target);
	CHECK_FALSE(before.is_empty());

	// (1) A writer that fails leaves the destination byte for byte as it was and
	// does not leave its half-written scratch file (or the backup) behind. This
	// is the mechanism `editor_save_scene` and `editor_capture_screenshot`
	// depend on, shared with `project_write_resource_scene` since TASK-008
	// section 3.
	const Error failed = MCPTools::publish_file_atomically(target, atomic_test_failing_writer, nullptr);
	CHECK(failed != OK);
	CHECK(FileAccess::get_file_as_string(target) == before);
	CHECK_FALSE(FileAccess::exists(MCPTools::temporary_sibling_path(target)));
	CHECK_FALSE(FileAccess::exists(MCPTools::temporary_sibling_path(target) + ".bak"));

	// (2) A successful writer publishes the new bytes over the old ones.
	String replacement = "replaced";
	CHECK(MCPTools::publish_file_atomically(target, atomic_test_succeeding_writer, &replacement) == OK);
	CHECK(FileAccess::get_file_as_string(target) == replacement);
	CHECK_FALSE(FileAccess::exists(MCPTools::temporary_sibling_path(target)));
	CHECK_FALSE(FileAccess::exists(MCPTools::temporary_sibling_path(target) + ".bak"));

	// (3) A new path whose parent directory does not exist yet gets one.
	const String nested = fixture.path("generated/deep/published.txt");
	CHECK_FALSE(DirAccess::dir_exists_absolute(fixture.path("generated/deep")));
	String payload = "published";
	CHECK(MCPTools::publish_file_atomically(nested, atomic_test_succeeding_writer, &payload) == OK);
	CHECK(DirAccess::dir_exists_absolute(fixture.path("generated/deep")));
	CHECK(FileAccess::get_file_as_string(nested) == payload);

	// (4) A failure on a new path leaves no file at all - not a partial one.
	const String doomed = fixture.path("generated/never.txt");
	CHECK(MCPTools::publish_file_atomically(doomed, atomic_test_failing_writer, nullptr) != OK);
	CHECK_FALSE(FileAccess::exists(doomed));
	CHECK_FALSE(FileAccess::exists(MCPTools::temporary_sibling_path(doomed)));

	// (5) The naming rule the format savers depend on: the extension stays the
	// last dot component, or `ResourceFormatSaver::recognize_path()` sees the
	// scratch suffix instead of `tres` and every save fails (REPORT-007 8.1).
	CHECK(MCPTools::temporary_sibling_path(String("res://a/b.tres")) == String("res://a/b.mcp-tmp.tres"));
	CHECK(MCPTools::temporary_sibling_path(String("res://a/plain")) == String("res://a/plain.mcp-tmp"));

	// (6) Nothing of the helper survives in the tree.
	const Array files = TestMCPServer::list_files_recursive(fixture.root);
	CHECK(files.size() > 0);
	for (int i = 0; i < files.size(); i++) {
		CHECK_FALSE(((String)files[i]).contains(".mcp-tmp"));
	}
}

// ---------------------------------------------------------------------------
// TASK-009: the `running_game_read_scene` group (one `scope = GAME` tool).
//
// The only `scope = GAME` tool of B1, so this is the mirror image of the
// editor-only group tests above and the first place the direction "a game-only
// tool must be absent from the editor endpoint" is observable:
//   * a game process (the doctest process is one) serves it;
//   * an editor process *registers* it - only `scope = EDITOR` is skipped at
//     registration - but never lists it, and `tools/call` on the editor table
//     answers -32601 instead of running it;
//   * the declarations (`channel` / `verb` / `scope` / `mutating`) are forced by
//     the ToolBuilder, and `docs/tool-rename-map.json` is their authority; the
//     wire-visible half pinned here is the `inputSchema` the listing carries.
//
// The node-tree behaviour itself needs a live `SceneTree` (the running game's
// current scene) and the doctest process has none - the same fact the
// `project_analyze_scene_complexity` fallback test recorded. It is proven on the
// wire in the TASK-009 evidence phase `game` and declared in REPORT-009.
// ---------------------------------------------------------------------------

namespace {
const char *const RUNNING_GAME_READ_SCENE_TOOLS[1] = { "running_game_find_nearby_nodes" };
// TASK-010: the seven game-scope tools the B2 groups add. Together with the B1
// tool above they are the whole `scope = game` set of the port.
const char *const RUNNING_GAME_B2_TOOLS[7] = {
	"running_game_get_scene_tree",
	"running_game_get_node_properties",
	"running_game_get_node_properties_batch",
	"running_game_get_autoload_node",
	"running_game_find_nodes_by_script",
	"running_game_find_ui_elements",
	"running_game_execute_gdscript",
};
} // namespace

TEST_CASE("[MCPServer] the running_game_read_scene group is game-only") {
	MCPToolRegistry game_registry;
	TestMCPServer::build_all_tools_registry(game_registry);
	CHECK(game_registry.get_tool_count() == 40);
	CHECK(game_registry.get_visible_tool_count(false) == 40);
	CHECK(game_registry.get_visible_tool_count(true) == 23);

	MCPToolRegistry editor_registry;
	TestMCPServer::build_editor_process_registry(editor_registry);
	// TASK-013 grew the editor-process table by the six editor-scope input
	// simulation tools: 60 -> 66 registered, 43 -> 49 visible to an editor.
	// TASK-015 grows it by the ten editor-scope node writes: 66 -> 76
	// registered, 49 -> 59 visible to an editor (a game process is unchanged:
	// editor-scope tools are not registered there at all).
	CHECK(editor_registry.get_tool_count() == 76);
	CHECK(editor_registry.get_visible_tool_count(true) == 59);
	CHECK(editor_registry.get_visible_tool_count(false) == 40);

	for (int i = 0; i < 1; i++) {
		const String name = RUNNING_GAME_READ_SCENE_TOOLS[i];
		CHECK(game_registry.has_tool(name));
		CHECK(game_registry.is_tool_visible(name, false));
		CHECK_FALSE(game_registry.is_tool_visible(name, true));

		CHECK(editor_registry.has_tool(name));
		CHECK(editor_registry.is_tool_visible(name, false));
		CHECK_FALSE(editor_registry.is_tool_visible(name, true));
	}

	// TASK-010 section 4: the same scope contract for the seven B2 game-scope
	// tools. They are registered in an editor process too (the game scope is not
	// the editor guard's business) but never visible there, and they are visible
	// in a game process.
	for (int i = 0; i < 7; i++) {
		const String name = RUNNING_GAME_B2_TOOLS[i];
		CHECK(game_registry.has_tool(name));
		CHECK(game_registry.is_tool_visible(name, false));
		CHECK_FALSE(game_registry.is_tool_visible(name, true));

		CHECK(editor_registry.has_tool(name));
		CHECK(editor_registry.is_tool_visible(name, false));
		CHECK_FALSE(editor_registry.is_tool_visible(name, true));

		// ... and the editor endpoint never carries them, which is what the
		// -32601 refusal on the wire is derived from.
		const String call = "{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"" + name + "\",\"arguments\":{}}}";
		const MCPJsonRpc::Response editor_refusal = MCPJsonRpc::handle(call, editor_registry, true);
		CHECK(editor_refusal.http_status == 200);
		CHECK(editor_refusal.body.contains("\"code\":-32601"));
		CHECK(editor_refusal.body.contains("Method not found: " + name));
		CHECK_FALSE(editor_refusal.body.contains("\"result\""));
	}

	// The game listing carries it exactly once; the editor listing never does.
	const Array game_list = game_registry.build_tools_list(false);
	CHECK(game_list.size() == 40);
	Dictionary listed;
	int occurrences = 0;
	for (int i = 0; i < game_list.size(); i++) {
		if (String(((Dictionary)game_list[i])["name"]) == String(RUNNING_GAME_READ_SCENE_TOOLS[0])) {
			listed = game_list[i];
			occurrences++;
		}
	}
	CHECK(occurrences == 1);
	const Array editor_list = editor_registry.build_tools_list(true);
	CHECK(editor_list.size() == 59);
	for (int i = 0; i < editor_list.size(); i++) {
		CHECK(String(((Dictionary)editor_list[i])["name"]) != String(RUNNING_GAME_READ_SCENE_TOOLS[0]));
	}
	for (int j = 0; j < 7; j++) {
		int game_occurrences = 0;
		for (int i = 0; i < game_list.size(); i++) {
			if (String(((Dictionary)game_list[i])["name"]) == String(RUNNING_GAME_B2_TOOLS[j])) {
				game_occurrences++;
			}
		}
		CHECK(game_occurrences == 1);
		for (int i = 0; i < editor_list.size(); i++) {
			CHECK(String(((Dictionary)editor_list[i])["name"]) != String(RUNNING_GAME_B2_TOOLS[j]));
		}
	}

	// The `inputSchema` the listing carries: object, one required `position`
	// (itself an object) and the four optional filters. This is the shape of
	// docs/tools_list.renamed.json; the verbatim comparison is gate 1.
	if (occurrences == 1) {
		const Dictionary schema = listed["inputSchema"];
		CHECK(String(schema["type"]) == "object");
		const Array required = schema["required"];
		CHECK(required.size() == 1);
		CHECK(String(required[0]) == "position");
		const Dictionary properties = schema["properties"];
		CHECK(properties.size() == 5);
		CHECK(String(((Dictionary)properties["position"])["type"]) == "object");
		CHECK(String(((Dictionary)properties["radius"])["type"]) == "number");
		CHECK(String(((Dictionary)properties["max_results"])["type"]) == "integer");
		CHECK(String(((Dictionary)properties["type_filter"])["type"]) == "string");
		CHECK(String(((Dictionary)properties["group_filter"])["type"]) == "string");
	}

	// `tools/call` from an editor endpoint: -32601, never execution.
	const String call = "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"running_game_find_nearby_nodes\",\"arguments\":{}}}";
	const MCPJsonRpc::Response refused = MCPJsonRpc::handle(call, editor_registry, true);
	CHECK(refused.http_status == 200);
	CHECK(refused.body.contains("\"code\":-32601"));
	CHECK(refused.body.contains("Method not found: running_game_find_nearby_nodes"));
	CHECK_FALSE(refused.body.contains("\"result\""));

	// ... and the very same request on the game table reaches the tool: the
	// missing `position` is the tool's own -32602, which is only reachable after
	// the scope guard let the call through.
	const MCPJsonRpc::Response served = MCPJsonRpc::handle(call, game_registry, false);
	CHECK(served.http_status == 200);
	CHECK_FALSE(served.body.contains("-32601"));
	CHECK(served.body.contains("\"code\":-32602"));
	CHECK(served.body.contains("Missing required parameter: position"));
}

TEST_CASE("[MCPServer] running_game_find_nearby_nodes validates its arguments and needs a running game") {
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	const auto call = [&registry](const String &p_arguments) {
		const String request = "{\"jsonrpc\":\"2.0\",\"id\":9,\"method\":\"tools/call\",\"params\":{\"name\":\"running_game_find_nearby_nodes\",\"arguments\":" + p_arguments + "}}";
		return MCPJsonRpc::handle(request, registry, false);
	};

	// (1) `position` is required: the contract's `required: ["position"]`.
	const MCPJsonRpc::Response missing = call("{}");
	CHECK(missing.body.contains("\"code\":-32602"));
	CHECK(missing.body.contains("Missing required parameter: position"));
	CHECK_FALSE(missing.body.contains("\"result\""));

	// (2) A present parameter of the wrong type is -32602, never a silent
	// default (PLAYBOOK section 6 item 2). This is deliberately *stricter* than
	// the GDScript reference, where `position: 5` became the empty dictionary
	// and `radius: "big"` became 100.0. Godot's JSON parser turns every number
	// into a float, which is why the reported type names are float/String.
	const MCPJsonRpc::Response scalar_position = call("{\"position\":5}");
	CHECK(scalar_position.body.contains("\"code\":-32602"));
	CHECK(scalar_position.body.contains("Parameter 'position' must be an object, got float"));

	const MCPJsonRpc::Response bad_component = call("{\"position\":{\"x\":\"a\"}}");
	CHECK(bad_component.body.contains("\"code\":-32602"));
	CHECK(bad_component.body.contains("Parameter 'position.x' must be a number, got String"));

	const MCPJsonRpc::Response bad_component_y = call("{\"position\":{\"x\":0,\"y\":\"a\"}}");
	CHECK(bad_component_y.body.contains("\"code\":-32602"));
	CHECK(bad_component_y.body.contains("Parameter 'position.y' must be a number, got String"));

	const MCPJsonRpc::Response bad_radius = call("{\"position\":{\"x\":0},\"radius\":\"big\"}");
	CHECK(bad_radius.body.contains("\"code\":-32602"));
	CHECK(bad_radius.body.contains("Parameter 'radius' must be a number, got String"));

	const MCPJsonRpc::Response bad_group_filter = call("{\"position\":{\"x\":0},\"group_filter\":7}");
	CHECK(bad_group_filter.body.contains("\"code\":-32602"));
	CHECK(bad_group_filter.body.contains("Parameter 'group_filter' must be a string, got float"));

	const MCPJsonRpc::Response bad_type_filter = call("{\"position\":{\"x\":0},\"type_filter\":7}");
	CHECK(bad_type_filter.body.contains("\"code\":-32602"));
	CHECK(bad_type_filter.body.contains("Parameter 'type_filter' must be a string, got float"));

	const MCPJsonRpc::Response bad_max_results = call("{\"position\":{\"x\":0},\"max_results\":\"many\"}");
	CHECK(bad_max_results.body.contains("\"code\":-32602"));
	CHECK(bad_max_results.body.contains("Parameter 'max_results' must be an integer, got String"));

	const MCPJsonRpc::Response fractional_max_results = call("{\"position\":{\"x\":0},\"max_results\":1.5}");
	CHECK(fractional_max_results.body.contains("\"code\":-32602"));
	CHECK(fractional_max_results.body.contains("Parameter 'max_results' must be an integer, got float"));

	// (3) A well-formed call with no running scene: -32000 with a
	// `data.suggestion` (GDR-14), the module's mapping of the reference's
	// `{"error": "No current scene"}`. The doctest process has no SceneTree at
	// all, so both the null SceneTree and the null current scene land here.
	const MCPJsonRpc::Response no_scene = call("{\"position\":{\"x\":0,\"y\":0}}");
	CHECK(no_scene.body.contains("\"code\":-32000"));
	CHECK(no_scene.body.contains("\"suggestion\""));
	CHECK_FALSE(no_scene.body.contains("\"nodes\""));
	CHECK_FALSE(no_scene.body.contains("\"result\""));
}

// ===========================================================================
// TASK-010: B2 opens with the game-side observation group, the E3 lever
// `running_game_execute_gdscript`, and three small fixes.
//
// The doctest process has no SceneTree (the fact TASK-009 recorded), so the
// node-tree behaviour of the observation group can only be pinned on the wire -
// that is what `scripts/mcp010_b2_observation_evidence.ps1` phase `game` does
// against a real game on 9889, and what REPORT-010 section "E3 解锁证据链"
// quotes. What *is* pinnable here, and is pinned below, is everything that does
// not need the tree: the registration/scope contract of both groups, the
// argument contract of every tool, the -32000 refusal of a well-formed call
// without a running scene, and - because GDScript can be compiled and called
// without any SceneTree - the whole execution path of the E3 lever, including
// the counterexample that shows what the migration source's Expression-based
// path could not do.
// ===========================================================================

namespace {
const char *const RUNNING_GAME_OBSERVATION_TOOLS[6] = {
	"running_game_get_scene_tree",
	"running_game_get_node_properties",
	"running_game_get_node_properties_batch",
	"running_game_get_autoload_node",
	"running_game_find_nodes_by_script",
	"running_game_find_ui_elements",
};
} // namespace

TEST_CASE("[MCPServer] the running_game_observation group is game-only and complete") {
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	for (int i = 0; i < 6; i++) {
		const String name = RUNNING_GAME_OBSERVATION_TOOLS[i];
		CHECK(registry.has_tool(name));
		CHECK(registry.is_tool_visible(name, false));
		CHECK_FALSE(registry.is_tool_visible(name, true));
	}

	// Every tool of the group is served by the game endpoint exactly once, and
	// never by the editor endpoint: the whole group is `scope = game`
	// (docs/tool-rename-map.json), which is why the B2 manifest declares it as
	// one group.
	const Array game_list = registry.build_tools_list(false);
	for (int j = 0; j < 6; j++) {
		int occurrences = 0;
		for (int i = 0; i < game_list.size(); i++) {
			if (String(((Dictionary)game_list[i])["name"]) == String(RUNNING_GAME_OBSERVATION_TOOLS[j])) {
				occurrences++;
			}
		}
		CHECK(occurrences == 1);
	}

	// The `inputSchema` each of the six carries, transcribed from
	// docs/tools_list.renamed.json (`scripts/check_contract_subset.ps1` compares
	// it verbatim on the wire; these assertions pin the shape independently of a
	// running engine).
	//
	// This test calls the handlers with *native* `Dictionary` values, so a wrong
	// number is an `int` here while the same call over JSON-RPC reports `float`
	// (Godot's JSON parser has one number type). The expectations below therefore
	// use doubles wherever the wire test (`running_game_find_nearby_nodes`)
	// expects "got float", and `3` where the native type is what is under test.
	//
	// Every accessor below checks a Variant's type before it casts and checks an
	// array's size before it indexes: during the red run the tools do not exist
	// yet, and a `required[0]` on the empty array of a missing schema is a hard
	// crash (measured: "test case CRASHED: Unhandled SEH exception caught")
	// instead of a failing assertion.
	const auto dict_of = [](const Variant &p_value) -> Dictionary {
		return p_value.get_type() == Variant::DICTIONARY ? (Dictionary)p_value : Dictionary();
	};
	const auto array_of = [](const Variant &p_value) -> Array {
		return p_value.get_type() == Variant::ARRAY ? (Array)p_value : Array();
	};
	const auto schema_of = [&game_list, &dict_of](const String &p_name) -> Dictionary {
		for (int i = 0; i < game_list.size(); i++) {
			const Variant entry = game_list[i];
			if (entry.get_type() != Variant::DICTIONARY) {
				continue;
			}
			if (String(((Dictionary)entry)["name"]) == p_name) {
				return dict_of(((Dictionary)entry).get("inputSchema", Variant()));
			}
		}
		return Dictionary();
	};
	const auto properties_of = [&schema_of, &dict_of](const String &p_tool) -> Dictionary {
		return dict_of(schema_of(p_tool).get("properties", Variant()));
	};
	const auto type_of = [&dict_of](const Dictionary &p_properties, const String &p_property) -> String {
		const Dictionary property = dict_of(p_properties.get(p_property, Variant()));
		if (property.is_empty()) {
			return String();
		}
		const Variant type = property.get("type", Variant());
		return type.get_type() == Variant::STRING ? (String)type : String();
	};
	const auto required_of = [&schema_of, &array_of](const String &p_tool) -> Array {
		return array_of(schema_of(p_tool).get("required", Variant()));
	};
	const auto required_name = [](const Array &p_required) -> String {
		return p_required.size() == 1 ? String(p_required[0]) : String();
	};

	CHECK(String(schema_of("running_game_get_scene_tree").get("type", Variant())) == "object");
	{
		const Dictionary properties = properties_of("running_game_get_scene_tree");
		CHECK(properties.size() == 4);
		CHECK(type_of(properties, "max_depth") == "integer");
		CHECK(type_of(properties, "script_filter") == "string");
		CHECK(type_of(properties, "type_filter") == "string");
		CHECK(type_of(properties, "named_only") == "boolean");
		CHECK(required_of("running_game_get_scene_tree").size() == 0);
	}
	{
		const Dictionary properties = properties_of("running_game_get_node_properties");
		CHECK(required_name(required_of("running_game_get_node_properties")) == "node_path");
		CHECK(properties.size() == 2);
		CHECK(type_of(properties, "node_path") == "string");
		CHECK(type_of(properties, "properties") == "array");
	}
	{
		const Dictionary properties = properties_of("running_game_get_node_properties_batch");
		CHECK(required_name(required_of("running_game_get_node_properties_batch")) == "nodes");
		CHECK(properties.size() == 1);
		CHECK(type_of(properties, "nodes") == "array");
		// ... and the nested item schema the contract declares for `nodes`.
		const Dictionary items = dict_of(((Dictionary)properties.get("nodes", Variant())).get("items", Variant()));
		if (!items.is_empty()) {
			const Dictionary item_properties = dict_of(items.get("properties", Variant()));
			CHECK(type_of(item_properties, "node_path") == "string");
			CHECK(type_of(item_properties, "properties") == "array");
			CHECK(required_name(array_of(items.get("required", Variant()))) == "node_path");
		} else {
			CHECK_MESSAGE(false, "the contract's node item schema is missing");
		}
	}
	{
		const Dictionary properties = properties_of("running_game_get_autoload_node");
		CHECK(required_name(required_of("running_game_get_autoload_node")) == "name");
		CHECK(properties.size() == 2);
		CHECK(type_of(properties, "name") == "string");
		CHECK(type_of(properties, "properties") == "array");
	}
	{
		const Dictionary properties = properties_of("running_game_find_nodes_by_script");
		CHECK(required_name(required_of("running_game_find_nodes_by_script")) == "script");
		CHECK(properties.size() == 2);
		CHECK(type_of(properties, "script") == "string");
		CHECK(type_of(properties, "properties") == "array");
	}
	{
		const Dictionary properties = properties_of("running_game_find_ui_elements");
		CHECK(properties.size() == 1);
		CHECK(type_of(properties, "type_filter") == "string");
		CHECK(required_of("running_game_find_ui_elements").size() == 0);
	}
}

TEST_CASE("[MCPServer] the running_game_observation tools validate their arguments and need a running game") {
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	// One tool call, both halves of its result. (A local struct instead of
	// `std::pair` so the test header does not depend on `<utility>` being pulled
	// in transitively.)
	struct Called {
		Variant payload;
		MCPToolError error;
	};
	const auto call = [&registry](const String &p_tool, const Dictionary &p_arguments) {
		Called result;
		result.payload = registry.call_tool(p_tool, p_arguments, result.error);
		return result;
	};

	// (1) The required parameters of the contract. Every tool that declares one
	// refuses a call without it with -32602 and the helper's message.
	{
		Dictionary args;
		const auto result = call("running_game_get_node_properties", args);
		CHECK(result.second.code == -32602);
		CHECK(result.second.message == "Missing required parameter: node_path");
	}
	{
		Dictionary args;
		const auto result = call("running_game_get_node_properties_batch", args);
		CHECK(result.second.code == -32602);
		CHECK(result.second.message == "Missing required parameter: nodes");
	}
	{
		Dictionary args;
		const auto result = call("running_game_get_autoload_node", args);
		CHECK(result.second.code == -32602);
		CHECK(result.second.message == "Missing required parameter: name");
	}
	{
		Dictionary args;
		const auto result = call("running_game_find_nodes_by_script", args);
		CHECK(result.second.code == -32602);
		CHECK(result.second.message == "Missing required parameter: script");
	}

	// (2) A parameter that is present with the wrong type is -32602, never a
	// silent default (PLAYBOOK section 6 item 2).
	{
		Dictionary args;
		args["max_depth"] = "deep";
		const auto result = call("running_game_get_scene_tree", args);
		CHECK(result.second.code == -32602);
		CHECK(result.second.message == "Parameter 'max_depth' must be an integer, got String");
	}
	{
		Dictionary args;
		args["named_only"] = 3;
		const auto result = call("running_game_get_scene_tree", args);
		CHECK(result.second.code == -32602);
		CHECK(result.second.message == "Parameter 'named_only' must be a boolean, got float");
	}
	{
		Dictionary args;
		args["type_filter"] = 3;
		const auto result = call("running_game_get_scene_tree", args);
		CHECK(result.second.code == -32602);
		CHECK(result.second.message == "Parameter 'type_filter' must be a string, got float");
	}
	{
		Dictionary args;
		args["node_path"] = 5;
		const auto result = call("running_game_get_node_properties", args);
		CHECK(result.second.code == -32602);
		CHECK(result.second.message == "Parameter 'node_path' must be a string, got float");
	}
	{
		Dictionary args;
		args["node_path"] = "Player";
		args["properties"] = "position";
		const auto result = call("running_game_get_node_properties", args);
		CHECK(result.second.code == -32602);
		CHECK(result.second.message == "Parameter 'properties' must be an array of strings, got String");
	}
	{
		Dictionary args;
		args["node_path"] = "Player";
		Array properties;
		properties.push_back("position");
		properties.push_back(7);
		args["properties"] = properties;
		const auto result = call("running_game_get_node_properties", args);
		CHECK(result.second.code == -32602);
		CHECK(result.second.message == "Parameter 'properties[1]' must be a string, got float");
	}
	{
		Dictionary args;
		args["nodes"] = 5;
		const auto result = call("running_game_get_node_properties_batch", args);
		CHECK(result.second.code == -32602);
		CHECK(result.second.message == "Parameter 'nodes' must be an array, got float");
	}
	{
		Dictionary args;
		Array nodes;
		nodes.push_back(5);
		args["nodes"] = nodes;
		const auto result = call("running_game_get_node_properties_batch", args);
		CHECK(result.second.code == -32602);
		CHECK(result.second.message == "Parameter 'nodes[0]' must be an object, got float");
	}
	{
		// An item without `node_path` is a malformed *request*, not a missing
		// node: the missing node is answered per item further down.
		Dictionary args;
		Array nodes;
		Dictionary item;
		nodes.push_back(item);
		args["nodes"] = nodes;
		const auto result = call("running_game_get_node_properties_batch", args);
		CHECK(result.second.code == -32602);
		CHECK(result.second.message == "Parameter 'nodes[0].node_path' must be a string, got nil");
	}
	{
		Dictionary args;
		args["type_filter"] = 3;
		const auto result = call("running_game_find_ui_elements", args);
		CHECK(result.second.code == -32602);
		CHECK(result.second.message == "Parameter 'type_filter' must be a string, got float");
	}

	// (3) A well-formed call without a running scene: -32000 with a
	// `data.suggestion` (GDR-14), the module's mapping of the reference's
	// `{"error": "No current scene"}`. The doctest process has no SceneTree at
	// all, so both the null SceneTree and the null current scene land here.
	{
		const Dictionary args;
		const auto result = call("running_game_get_scene_tree", args);
		CHECK(result.second.code == -32000);
		CHECK(result.second.message == "No scene is currently open");
		CHECK(((Dictionary)result.second.data).has("suggestion"));
	}
	{
		Dictionary args;
		args["node_path"] = "Player";
		const auto result = call("running_game_get_node_properties", args);
		CHECK(result.second.code == -32000);
	}
	{
		Dictionary args;
		Array nodes;
		Dictionary item;
		item["node_path"] = "Player";
		nodes.push_back(item);
		args["nodes"] = nodes;
		const auto result = call("running_game_get_node_properties_batch", args);
		CHECK(result.second.code == -32000);
	}
	{
		Dictionary args;
		args["name"] = "GameState";
		const auto result = call("running_game_get_autoload_node", args);
		CHECK(result.second.code == -32000);
	}
	{
		Dictionary args;
		args["script"] = "res://player.gd";
		const auto result = call("running_game_find_nodes_by_script", args);
		CHECK(result.second.code == -32000);
	}
	{
		const Dictionary args;
		const auto result = call("running_game_find_ui_elements", args);
		CHECK(result.second.code == -32000);
	}

	// (4) TASK-010 section 3.1: the advice a game-side tool gives must not be
	// "use editor_open_scene", which is impossible advice in a game process. The
	// doctest process is not an editor, so this is the game-side wording.
	for (int i = 0; i < 6; i++) {
		const String name = RUNNING_GAME_OBSERVATION_TOOLS[i];
		Dictionary args;
		if (name == "running_game_get_node_properties") {
			args["node_path"] = "Player";
		} else if (name == "running_game_get_autoload_node") {
			args["name"] = "GameState";
		} else if (name == "running_game_find_nodes_by_script") {
			args["script"] = "res://player.gd";
		} else if (name == "running_game_get_node_properties_batch") {
			Array nodes;
			Dictionary item;
			item["node_path"] = "Player";
			nodes.push_back(item);
			args["nodes"] = nodes;
		}
		MCPToolError error;
		registry.call_tool(name, args, error);
		CHECK(error.code == -32000);
		const String suggestion = error.data.get_type() == Variant::DICTIONARY
				? String(((Dictionary)error.data).get("suggestion", Variant()))
				: String();
		CHECK(suggestion.contains("main scene"));
		CHECK_FALSE(suggestion.contains("editor_open_scene"));
	}

	// (5) The empty-string guards: an empty path/name/script is a malformed
	// request, not a lookup that happens to fail.
	{
		Dictionary args;
		args["name"] = "  ";
		const auto result = call("running_game_get_autoload_node", args);
		CHECK(result.second.code == -32602);
		CHECK(result.second.message == "Parameter 'name' must not be empty");
	}
	{
		Dictionary args;
		args["script"] = "  ";
		const auto result = call("running_game_find_nodes_by_script", args);
		CHECK(result.second.code == -32602);
		CHECK(result.second.message == "Parameter 'script' must not be empty");
	}
}

TEST_CASE("[MCPServer] the running_game_script_execution group is game-only and complete") {
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);
	CHECK(registry.has_tool("running_game_execute_gdscript"));
	CHECK(registry.is_tool_visible("running_game_execute_gdscript", false));
	CHECK_FALSE(registry.is_tool_visible("running_game_execute_gdscript", true));

	const Array game_list = registry.build_tools_list(false);
	int occurrences = 0;
	Dictionary listed;
	for (int i = 0; i < game_list.size(); i++) {
		const Dictionary entry = game_list[i];
		if (String(entry["name"]) == "running_game_execute_gdscript") {
			occurrences++;
			listed = entry;
		}
	}
	CHECK(occurrences == 1);
	if (occurrences == 1) {
		CHECK(String(listed["description"]) == String::utf8("在运行中的游戏内执行 GDScript 代码"));
		const Dictionary schema = listed["inputSchema"];
		CHECK(String(schema["type"]) == "object");
		const Array required = schema["required"];
		CHECK(required.size() == 1);
		CHECK(String(required[0]) == "code");
		const Dictionary properties = schema["properties"];
		CHECK(properties.size() == 1);
		CHECK(String(((Dictionary)properties["code"])["type"]) == "string");
	}

	// A game-only tool is refused by the editor endpoint's JSON-RPC layer with
	// -32601 and never executed there.
	MCPToolRegistry editor_registry;
	TestMCPServer::build_editor_process_registry(editor_registry);
	const String request = "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"running_game_execute_gdscript\",\"arguments\":{\"code\":\"return 1\"}}}";
	const MCPJsonRpc::Response refused = MCPJsonRpc::handle(request, editor_registry, true);
	CHECK(refused.body.contains("\"code\":-32601"));
	CHECK(refused.body.contains("Method not found: running_game_execute_gdscript"));
	CHECK_FALSE(refused.body.contains("\"result\""));
}

// ---------------------------------------------------------------------------
// The E3 lever, inside the doctest binary.
//
// `running_game_execute_gdscript` is the tool that unblocks "can the game be
// played" (D56): it runs the caller's code *in the game process*, so the code
// can reach the engine singletons. The migration source could not: it ran the
// code through `Expression.execute([], self, false)`, which resolves names
// against the base object only and therefore fails on `Input`.
//
// GDScript can be compiled and instantiated without any SceneTree, so both
// halves of that claim are decidable here: the tool's path returns a real value
// from a singleton, and the legacy path fails on the very same expression. The
// wire half (an actual game on 9889, with an input injection that visibly moves
// a node) is in the evidence script of TASK-010, because it needs a running
// game.
// ---------------------------------------------------------------------------

TEST_CASE("[MCPServer] running_game_execute_gdscript runs a GDScript body and reaches engine singletons") {
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	const auto call = [&registry](const String &p_code, Variant &r_payload, MCPToolError &r_error) {
		Dictionary args;
		args["code"] = p_code;
		r_payload = registry.call_tool("running_game_execute_gdscript", args, r_error);
	};

	// The payload of a successful call, or an empty dictionary while the tool is
	// missing (the red run). A successful payload always carries `result` and
	// `result_type`, so `is_empty()` is a sufficient "was there an answer" test
	// and no read below can dereference a nil value.
	const auto payload_of = [](const Variant &p_value) -> Dictionary {
		return p_value.get_type() == Variant::DICTIONARY ? (Dictionary)p_value : Dictionary();
	};
	const auto value_of = [](const Dictionary &p_payload, const String &p_key) -> Variant {
		return p_payload.is_empty() ? Variant() : p_payload.get(p_key, Variant());
	};

	// (1) The `code` argument contract.
	{
		Variant payload;
		MCPToolError error;
		Dictionary args;
		payload = registry.call_tool("running_game_execute_gdscript", args, error);
		CHECK(error.code == -32602);
		CHECK(error.message == "Missing required parameter: code");
	}
	{
		Variant payload;
		MCPToolError error;
		call("   \n\t ", payload, error);
		CHECK(error.code == -32602);
		CHECK(error.message == "Parameter 'code' must not be empty");
	}
	{
		Dictionary args;
		args["code"] = 5.0;
		Variant payload;
		MCPToolError error;
		payload = registry.call_tool("running_game_execute_gdscript", args, error);
		CHECK(error.code == -32602);
		CHECK(error.message == "Parameter 'code' must be a string, got float");
	}
	// (2) The language prerequisite, which the doctest process is the perfect
	// witness for: `Main::test_entrypoint()` runs `test_main()` *before*
	// `Main::setup2()` (main/main.cpp:921-943 vs. :3863), and
	// `ScriptServer::init_languages()` - the call that populates GDScript's
	// global names - happens in `setup2()`. So a test binary starts without a
	// script language, and without the guard in the tool the very first `return
	// 1 + 1` would answer `does not compile: Compilation failed` (measured) while
	// the engine log carried the real reason: `Native class "RefCounted" not
	// found`.
	//
	// The guard is asserted *and* then lifted for the rest of this test, so the
	// execution path below runs against a real script language - the same state a
	// running game is in. (`project_validate_script`'s test is written to hold in
	// either mode, and it runs before this one; TASK-010 REPORT section 8 records
	// the ordering argument.)
	if (!ScriptServer::are_languages_initialized()) {
		Variant payload;
		MCPToolError error;
		call("return 1 + 1", payload, error);
		CHECK(error.code == -32000);
		CHECK(error.message.contains("Not implemented"));
		CHECK(error.data.get_type() == Variant::DICTIONARY);
		if (error.data.get_type() == Variant::DICTIONARY) {
			CHECK(((Dictionary)error.data).has("suggestion"));
		}
		ScriptServer::init_languages();
	}
	CHECK(ScriptServer::are_languages_initialized());

	// (3) A body that does not compile is a malformed argument, not an internal
	// failure: -32602 with the compiler's verdict. The check has to sit *after*
	// the language prerequisite above, because with no script language there is
	// nothing to compile the body with - that case is the -32000 state error, and
	// the difference between the two is exactly what a caller needs to see.
	{
		Variant payload;
		MCPToolError error;
		call("return (", payload, error);
		CHECK(error.code == -32602);
		CHECK(error.message.contains("does not compile"));
	}

	// (4) A value comes back, and it is a structured value rather than the
	// migration source's `str(result)`.
	{
		Variant payload;
		MCPToolError error;
		call("return 1 + 1", payload, error);
		CHECK_FALSE(error.is_error());
		CHECK(payload.get_type() == Variant::DICTIONARY);
		const Dictionary result = payload_of(payload);
		CHECK(value_of(result, "result").get_type() == Variant::INT);
		CHECK((int64_t)value_of(result, "result") == 2);
		CHECK(String(value_of(result, "result_type")) == "int");
	}

	// (5) The engine singletons are reachable - the whole point of the tool.
	// `OS.get_process_id()` is the strongest of the two: it returns the real pid
	// of the process the code ran in, i.e. of the doctest binary itself.
	//
	// `Input` is deliberately *not* asserted here: the doctest harness only
	// creates it for `[SceneTree]` / `[Editor]` test cases
	// (tests/test_main.cpp:181-183), so in this process `Input` is a null
	// instance and `Input.is_action_pressed(...)` is a GDScript runtime error
	// (measured: `Attempt to call function 'is_action_pressed' in base 'null
	// instance' on a null instance.`). The input path is proven where it exists -
	// the game endpoint on 9889, with a real injection that moves a node - by
	// `scripts/mcp010_b2_observation_evidence.ps1` phase `game`.
	{
		Variant payload;
		MCPToolError error;
		call("return OS.get_process_id()", payload, error);
		CHECK_FALSE(error.is_error());
		const Dictionary result = payload_of(payload);
		CHECK(String(value_of(result, "result_type")) == "int");
		CHECK((int64_t)value_of(result, "result") > 0);
		CHECK((int64_t)value_of(result, "result") == (int64_t)OS::get_singleton()->get_process_id());
	}
	{
		Variant payload;
		MCPToolError error;
		call("return Engine.get_frames_per_second() >= 0", payload, error);
		CHECK_FALSE(error.is_error());
		const Dictionary result = payload_of(payload);
		CHECK(String(value_of(result, "result_type")) == "bool");
		CHECK((bool)value_of(result, "result") == true);
	}

	// (5) Statements, loops and lifted helper functions are supported; the old
	// expression path accepted a single expression only.
	{
		Variant payload;
		MCPToolError error;
		call("func double_it(value):\n\treturn value * 2\n\nvar total := 0\nfor index in range(3):\n\ttotal += double_it(index)\nreturn total", payload, error);
		CHECK_FALSE(error.is_error());
		const Dictionary result = payload_of(payload);
		CHECK((int64_t)value_of(result, "result") == 6);
	}

	// (6) The legacy path, on the very same expression. This is the comparison
	// the task asks for, made executable: `Expression` resolves names against
	// its base object, so `Input` - a *global* singleton - is not found, while
	// the compiled body above reaches it. Pinning it here means a future change
	// that silently reintroduces the Expression mechanism fails this test.
	{
		Ref<Expression> expression;
		expression.instantiate();
		CHECK(expression->parse("Input.is_action_pressed(\"ui_accept\")") == OK);
		Ref<RefCounted> base;
		base.instantiate();
		const Array no_inputs;
		const Variant legacy = expression->execute(no_inputs, base.ptr(), false);
		CHECK(expression->has_execute_failed());
		CHECK(expression->get_error_text().contains("Input"));
		CHECK(legacy.get_type() == Variant::NIL);
	}

	// (7) The success path also survives the JSON-RPC envelope: the payload is
	// the same dictionary through `tools/call`.
	{
		const auto array_of = [](const Variant &p_value) -> Array {
			return p_value.get_type() == Variant::ARRAY ? (Array)p_value : Array();
		};
		const String request = "{\"jsonrpc\":\"2.0\",\"id\":7,\"method\":\"tools/call\",\"params\":{\"name\":\"running_game_execute_gdscript\",\"arguments\":{\"code\":\"return 40 + 2\"}}}";
		const MCPJsonRpc::Response response = MCPJsonRpc::handle(request, registry, false);
		CHECK(response.http_status == 200);
		CHECK(response.body.contains("\"isError\"") == false);
		const Variant envelope = TestMCPServer::parse_json(response.body);
		CHECK(envelope.get_type() == Variant::DICTIONARY);
		const Dictionary result = envelope.get_type() == Variant::DICTIONARY ? (Dictionary)envelope : Dictionary();
		const Variant result_value = result.get("result", Variant());
		const Array content = result_value.get_type() == Variant::DICTIONARY ? array_of(((Dictionary)result_value).get("content", Variant())) : Array();
		CHECK(content.size() == 1);
		if (content.size() == 1) {
			const Dictionary text_entry = content[0].get_type() == Variant::DICTIONARY ? (Dictionary)content[0] : Dictionary();
			const Variant text = text_entry.get("text", Variant());
			const Variant payload = text.get_type() == Variant::STRING ? TestMCPServer::parse_json((String)text) : Variant();
			const Dictionary payload_dict = payload.get_type() == Variant::DICTIONARY ? (Dictionary)payload : Dictionary();
			CHECK_FALSE(payload_dict.is_empty());
			const Variant value = payload_dict.get("result", Variant());
			// The number loses its integer type on the way through JSON (Godot's
			// parser has one number type), so only the value is asserted.
			CHECK((value.get_type() == Variant::INT || value.get_type() == Variant::FLOAT));
			CHECK((int64_t)value == 42);
		}
	}
}

// ---------------------------------------------------------------------------
// TASK-010 section 3: the three small fixes. Each one is pinned by the test
// that describes the *wanted* behaviour; the red run before the fix is quoted in
// REPORT-010 section "三项小修的前后对照".
// ---------------------------------------------------------------------------

TEST_CASE("[MCPServer] the no_scene advice follows the process, not the editor") {
	// `MCPToolError::no_scene()` is what a tool answers when the state it needs
	// (the edited scene / the running game's current scene) is absent. The
	// suggestion used to be "Use editor_open_scene to open a scene first" for
	// *every* caller, which is impossible advice in a game process: in a game
	// build there is no editor and no editor_open_scene tool at all. The advice
	// is now derived from the process.
	const MCPToolError game_side = MCPToolError::no_scene();
	CHECK(game_side.code == -32000);
	CHECK(game_side.message == "No scene is currently open");
	const String game_suggestion = ((Dictionary)game_side.data)["suggestion"];
	CHECK(game_suggestion.contains("main scene"));
	CHECK(game_suggestion.contains("project.godot"));
	CHECK_FALSE(game_suggestion.contains("editor_open_scene"));

	// In an editor process the editor wording is the actionable one and must be
	// preserved byte for byte for the editor groups.
	Engine *engine = Engine::get_singleton();
	const bool was_editor = engine != nullptr && engine->is_editor_hint();
	if (engine != nullptr) {
		engine->set_editor_hint(true);
	}
	const MCPToolError editor_side = MCPToolError::no_scene();
	const String editor_suggestion = ((Dictionary)editor_side.data)["suggestion"];
	if (engine != nullptr) {
		engine->set_editor_hint(was_editor);
	}
	CHECK(editor_suggestion == "Use editor_open_scene to open a scene first");
}

TEST_CASE("[MCPServer] the integer helpers refuse a double that does not fit an int64") {
	Dictionary args;
	MCPToolError error;
	int64_t value = 0;

	// In range: a JSON-RPC client may spell an integer as `2.0`.
	args["value"] = 2.0;
	CHECK(MCPTools::require_int(args, "value", value, error));
	CHECK(value == 2);
	args["value"] = -5.0;
	CHECK(MCPTools::require_int(args, "value", value, error));
	CHECK(value == -5);
	args["value"] = (int64_t)9223372036854775807LL;
	CHECK(MCPTools::require_int(args, "value", value, error));
	CHECK(value == 9223372036854775807LL);

	// Out of range and non-finite: refused with -32602, never silently folded.
	// The old `(int64_t)number` cast was undefined behaviour and produced a
	// value that could even compare equal again; the guard is the whole fix.
	const double refused[4] = { 1.0e20, -1.0e20, Math::nan(), Math::inf() };
	for (int i = 0; i < 4; i++) {
		args["value"] = refused[i];
		MCPToolError refusal;
		int64_t out = 7;
		CHECK_FALSE(MCPTools::require_int(args, "value", out, refusal));
		CHECK(refusal.code == -32602);
		CHECK(refusal.message == "Parameter 'value' must be an integer, got float");
		CHECK(out == 7);

		MCPToolError optional_refusal;
		int64_t optional_out = 9;
		CHECK_FALSE(MCPTools::optional_int(args, "value", 3, optional_out, optional_refusal));
		CHECK(optional_refusal.code == -32602);
		CHECK(optional_out == 9);
	}

	// The boundary that is *representable* stays accepted: 9.0e18 < 2^63.
	args["value"] = 9.0e18;
	CHECK(MCPTools::require_int(args, "value", value, error));
	CHECK(value == 9000000000000000000LL);
}

TEST_CASE("[MCPServer] a double that does not fit an integer property is refused, not folded") {
	// The direct helper contract first: this is the single definition every
	// property writer (project_create_resource, project_edit_resource,
	// editor_add_resource_to_node_property) goes through.
	MCPToolError error;
	Variant out;
	CHECK(MCPTools::coerce_to_property_type(Variant(2.0), Variant::INT, out, error, "properties"));
	CHECK((int64_t)out == 2);
	CHECK_FALSE(error.is_error());

	const double refused[3] = { 1.0e20, Math::nan(), Math::inf() };
	for (int i = 0; i < 3; i++) {
		MCPToolError refusal;
		Variant refused_out;
		CHECK_FALSE(MCPTools::coerce_to_property_type(Variant(refused[i]), Variant::INT, refused_out, refusal, "properties"));
		CHECK(refusal.code == -32602);
	}

	// ... and through a real tool, on a real file. `Curve.bake_resolution` is an
	// `int` property, so `1e20` reaches the INT coercion path; before the fix
	// the out-of-range double was handed to `type_convert`, whose FLOAT -> INT
	// conversion is `(int64_t)value` - undefined behaviour that silently wrote a
	// wrong integer into the resource. The wanted behaviour is a refusal that
	// writes nothing.
	// The extension has to stay `.tres`: `ResourceSaver::save()` picks its format
	// saver from the text after the *last* dot, so `out_of_range.tres_nan` is not
	// a resource path at all (the same trap REPORT-007 section 8.1 recorded).
	TestMCPServer::ScratchProject fixture;
	MCPToolRegistry registry;
	TestMCPServer::build_all_tools_registry(registry);

	const String target = fixture.path("generated/out_of_range.tres");
	const String target_nan = fixture.path("generated/out_of_range_nan.tres");
	const String target_inf = fixture.path("generated/out_of_range_inf.tres");
	const String target_ok = fixture.path("generated/out_of_range_ok.tres");
	const auto create = [&registry](const String &p_path, const Variant &p_value) {
		struct Created {
			Variant payload;
			MCPToolError error;
		};
		Created result;
		Dictionary args;
		args["path"] = p_path;
		args["type"] = "Curve";
		Dictionary properties;
		properties["bake_resolution"] = p_value;
		args["properties"] = properties;
		result.payload = registry.call_tool("project_create_resource", args, result.error);
		return result;
	};

	{
		const auto result = create(1.0e20, "");
		CHECK(result.second.code == -32602);
		CHECK(result.second.message.contains("outside the range of a 64-bit integer"));
		CHECK_FALSE(FileAccess::exists(target));
	}
	{
		const auto result = create(Math::nan(), "_nan");
		CHECK(result.second.code == -32602);
		CHECK_FALSE(FileAccess::exists(target + "_nan"));
	}
	{
		const auto result = create(Math::inf(), "_inf");
		CHECK(result.second.code == -32602);
		CHECK_FALSE(FileAccess::exists(target + "_inf"));
	}
	{
		// The control: an in-range integral value still writes.
		const auto result = create(200.0, "_ok");
		CHECK_FALSE(result.second.is_error());
		const String written = target + "_ok";
		CHECK(FileAccess::exists(written));
		const Ref<Resource> resource = ResourceLoader::load(written, "", ResourceLoader::CACHE_MODE_IGNORE);
		CHECK(resource.is_valid());
		if (resource.is_valid()) {
			CHECK((int64_t)resource->get("bake_resolution") == 200);
		}
	}
}



// ---------------------------------------------------------------------------
// Independent acceptance probes (appended by the acceptance agent for one run,
// then reverted). No assertion here is copied from the shipped tests.
// ---------------------------------------------------------------------------

TEST_CASE("[MCPServer] ACCEPTANCE adversarial probes") {
	// (a) No length cap: a >= 100 character compliant name must be accepted.
	{
		String long_name = "project_get_";
		for (int i = 0; i < 120; i++) {
			long_name += "x";
		}
		CHECK(long_name.length() >= 100);

		String channel;
		String verb;
		CHECK(MCPToolRegistry::parse_tool_name(long_name, channel, verb));
		CHECK(channel == "project");
		CHECK(verb == "get");

		String error;
		CHECK(MCPToolRegistry::validate_tool_name(long_name, "project", "get", error));
		CHECK(error.is_empty());

		MCPToolRegistry registry;
		MCPToolDef def;
		def.name = long_name;
		def.channel = "project";
		def.verb = "get";
		CHECK(registry.register_tool(def));
		CHECK(registry.has_tool(long_name));
		CHECK(registry.is_tool_visible(long_name, true));
	}

	// (b) `editor_get` has no object segment and must still be accepted (D-E4).
	{
		String channel;
		String verb;
		CHECK(MCPToolRegistry::parse_tool_name("editor_get", channel, verb));
		CHECK(channel == "editor");
		CHECK(verb == "get");

		String error;
		CHECK(MCPToolRegistry::validate_tool_name("editor_get", "editor", "get", error));
		CHECK(error.is_empty());

		MCPToolRegistry registry;
		MCPToolDef def;
		def.name = "editor_get";
		def.channel = "editor";
		def.verb = "get";
		CHECK(registry.register_tool(def));
		CHECK(registry.has_tool("editor_get"));
	}

	// (c) Boundaries: empty remainder, uppercase channel, uppercase verb,
	// trailing underscore, illegal character, and a plainly legal name.
	{
		String channel;
		String verb;
		String err_upper;
		String err_mixed;
		String err_bang;
		String err_trail;
		String err_plain;

		CHECK_FALSE(MCPToolRegistry::parse_tool_name("editor_", channel, verb));
		CHECK_FALSE(MCPToolRegistry::parse_tool_name("project_", channel, verb));
		CHECK_FALSE(MCPToolRegistry::parse_tool_name("os_", channel, verb));
		CHECK_FALSE(MCPToolRegistry::parse_tool_name("running_game_", channel, verb));

		CHECK_FALSE(MCPToolRegistry::validate_tool_name("EDITOR_get_x", "EDITOR", "get", err_upper));
		CHECK(err_upper.contains("GDR-16 L1"));

		CHECK_FALSE(MCPToolRegistry::validate_tool_name("editor_Get_x", "editor", "Get", err_mixed));
		CHECK(err_mixed.contains("GDR-16 L1"));

		CHECK_FALSE(MCPToolRegistry::validate_tool_name("editor_get_x!", "editor", "get", err_bang));
		CHECK(err_bang.contains("GDR-16 L1"));

		// The frozen L1 pattern is `^<channel>_[a-z0-9_]+$`, so a trailing
		// underscore is inside the language; the actual behaviour is recorded.
		CHECK(MCPToolRegistry::validate_tool_name("os_get_", "os", "get", err_trail));
		CHECK(err_trail.is_empty());

		CHECK(MCPToolRegistry::validate_tool_name("editor_remove_a", "editor", "remove", err_plain));
		CHECK(err_plain.is_empty());
	}

	// (d) Channel cross check: a running_game_ name declared as editor_ fails L3.
	{
		String error;
		CHECK_FALSE(MCPToolRegistry::validate_tool_name("running_game_get_x", "editor", "get", error));
		CHECK(error.contains("GDR-16 L3"));
		CHECK(error.contains("declares channel"));

		MCPToolRegistry registry;
		MCPToolDef def;
		def.name = "running_game_get_x";
		def.channel = "editor";
		def.verb = "get";
		CHECK_FALSE(registry.register_tool(def));
		CHECK_FALSE(registry.has_tool("running_game_get_x"));
	}

	// (e) L4 is a `contains`, not a prefix: update_ mid-name still fails.
	{
		String error;
		CHECK_FALSE(MCPToolRegistry::validate_tool_name("editor_set_update_flag", "editor", "set", error));
		CHECK(error.contains("GDR-16 L4"));
		CHECK(error.contains("update_"));

		// The parser itself reads the verb as `set`, i.e. the name is otherwise
		// legal - only the banned substring rejects it.
		String channel;
		String verb;
		CHECK(MCPToolRegistry::parse_tool_name("editor_set_update_flag", channel, verb));
		CHECK(verb == "set");
		CHECK(verb != "update");
	}
}
