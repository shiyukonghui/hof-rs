/**************************************************************************/
/*  project_write_resource_scene.cpp                                      */
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
#include "project_write_resource_scene.h"

#include "tool_builder.h"
#include "tool_helpers.h"

#include "core/error/error_macros.h"
#include "core/io/dir_access.h"
#include "core/io/file_access.h"
#include "core/io/json.h"
#include "core/io/resource_loader.h"
#include "core/io/resource_saver.h"
#include "core/object/class_db.h"
#include "core/object/object.h"
#include "core/object/ref_counted.h"
#include "core/os/os.h"
#include "core/string/string_name.h"
#include "core/templates/hash_map.h"
#include "core/variant/callable.h"
#include "core/variant/variant.h"
#include "scene/main/node.h"
#include "scene/resources/packed_scene.h"

using namespace MCPTools;

// ---------------------------------------------------------------------------
// Shared helpers
//
// The four tools of this group all follow the same shape: normalise the path,
// build or load an object, apply a caller supplied property bag, and publish the
// result. The helpers below are the three things they must do identically - a
// JSON value becomes a property value, a resource becomes a file, and an object
// becomes a property bag.
// ---------------------------------------------------------------------------

// `properties` is an *optional* argument in three of the four tools, but when it
// is present it must be an object (PLAYBOOK section 6.2: a present argument with
// the wrong type is an error, never silently ignored).
static bool _optional_properties(const Dictionary &p_args, Dictionary &r_out, MCPToolError &r_error) {
	const Variant value = p_args.get("properties", Variant());
	if (value.get_type() == Variant::NIL) {
		r_out = Dictionary();
		return true;
	}
	if (value.get_type() != Variant::DICTIONARY) {
		r_error = MCPToolError::invalid_params(vformat("Parameter 'properties' must be an object, got %s",
				Variant::get_type_name(value.get_type())));
		return false;
	}
	r_out = value;
	return true;
}

// The JSON value of a property as a Godot value.
//
// The migration source reads the *typed* property before it assigns, and parses
// the incoming string with the property's own type (`serialize.rs:268`). Godot's
// JSON parser has one number type, so a plain `int` property would otherwise be
// written as a float - the same reasoning as the `_fold_integral_numbers` note in
// editor_read_scene_inspector.cpp. `r_target_type` is that property's type.
//
// Two conversions mirror the reference's string grammar (`parse_godot_string`,
// serialize.rs:299-317): `#rrggbb` is a Color, and `Vector2(...)` / `Vector3(...)`
// is a Vector. Everything else that is a JSON *object* becomes a Dictionary
// ("retain the structure", serialize.rs:288).
static Variant _property_value_from_json(const Variant &p_value, Variant::Type p_target_type) {
	switch (p_value.get_type()) {
		case Variant::NIL: {
			return Variant();
		}
		case Variant::BOOL: {
			return Variant((bool)p_value);
		}
		case Variant::FLOAT: {
			const double number = (double)p_value;
			if (p_target_type == Variant::INT && number >= -9.0e15 && number <= 9.0e15) {
				const int64_t truncated = (int64_t)number;
				if ((double)truncated == number) {
					return Variant(truncated);
				}
			}
			return Variant(number);
		}
		case Variant::ARRAY: {
			const Array source = p_value;
			Array out;
			for (int i = 0; i < source.size(); i++) {
				out.push_back(_property_value_from_json(source[i], Variant::NIL));
			}
			return out;
		}
		case Variant::DICTIONARY: {
			const Dictionary source = p_value;
			Dictionary out;
			const Array keys = source.keys();
			for (int i = 0; i < keys.size(); i++) {
				out[keys[i]] = _property_value_from_json(source[keys[i]], Variant::NIL);
			}
			return out;
		}
		case Variant::STRING: {
			const String text = ((String)p_value).strip_edges();
			if (text.begins_with("#")) {
				const Color color = Color::from_string(text, Color());
				if (color != Color()) {
					return Variant(color);
				}
			}
			// The reference's three constructors are the Godot 3 spellings; the
			// engine parser accepts both spellings, so it is used here.
			if (text.begins_with("Vector2(") || text.begins_with("Vector2i(") ||
					text.begins_with("Vector3(") || text.begins_with("Vector3i(") ||
					text.begins_with("Vector4(")) {
				Variant from_string;
				Variant::construct_from_string(text, from_string);
				if (from_string.get_type() != Variant::NIL) {
					return from_string;
				}
			}
			return (String)p_value;
		}
		default: {
			return p_value;
		}
	}
}

// The value handed to `Object::set()`, coerced to the property's own type.
//
// `VariantUtilityFunctions::type_convert` is exactly the engine's own
// `@GlobalScope.type_convert` (the conversion the GDScript `Object.set()` path
// ends up in), which is the semantics the migration source observes through its
// own bindings. Non-finite numbers are refused explicitly: converting `inf` to
// an integer is undefined behaviour, not a conversion.
static bool _coerce_to_property_type(const Variant &p_value, Variant::Type p_target_type, Variant &r_out, MCPToolError &r_error) {
	if (p_value.get_type() == Variant::FLOAT) {
		const double number = (double)p_value;
		if (Math::is_nan(number) || Math::is_inf(number)) {
			r_error = MCPToolError::invalid_params("Parameter 'properties' contains a non-finite number");
			return false;
		}
	}
	if (p_target_type == Variant::NIL || p_value.get_type() == p_target_type) {
		r_out = p_value;
		return true;
	}
	r_out = VariantUtilityFunctions::type_convert(p_value, p_target_type);
	return true;
}

// The names of every property the object can be given through `set()`.
//
// TASK-049: the table carries the engine's **own** names, whatever they look
// like. `Environment` registers `glow_levels/1`..`glow_levels/7` with
// `ADD_PROPERTYI` (`scene/resources/environment.cpp:1464-1470`), a
// `ShaderMaterial` one `shader_parameter/<uniform>` per uniform of the shader the
// *instance* holds, and the joint classes `params/bias`,
// `angular_limit/upper`, ... - none of them is an identifier, and all of them
// are exactly what `project_read_resource` / `editor_get_node_properties` answer
// (they enumerate this very list). The map value says whether the entry is an
// inspector *label* (`ADD_GROUP` / `ADD_SUBGROUP` / `ADD_CATEGORY`): the engine
// keeps a label in `get_property_list()` but **not** in `GDType::members()`,
// which is the table `Object::set_native()` resolves a name against
// (`ClassDB::add_property_group` only calls `add_to_ordered_properties`,
// `core/object/class_db.cpp:1300-1311`), so a label names nothing that can be
// written. A name declared twice (never observed in the engine; kept
// deterministic) counts as a label only when every entry for it is one.
static HashMap<StringName, bool> _property_table(const Object *p_object) {
	HashMap<StringName, bool> table;
	List<PropertyInfo> properties;
	p_object->get_property_list(&properties);
	for (const PropertyInfo &property : properties) {
		const bool is_label = property_is_label(property);
		if (table.has(property.name)) {
			table[property.name] = table[property.name] && is_label;
		} else {
			table[property.name] = is_label;
		}
	}
	return table;
}

// The fallback judgement for a name the object's own property table does **not**
// carry (TASK-049). Before TASK-049 this was the *first* gate on every key, and
// that is what refused names the engine accepts and the reader answers:
// `glow_levels/1` was `-32602`.
//
// The engine's answer to "can this name address a property" is the property
// table (`Object::set_native()`, `core/object/object.cpp:349-393`), so this
// predicate only has to answer "is this even shaped like a property name": an
// identifier, which is what every spelling this module's readers answer for a
// table entry is *not* required to be - `glow_levels/1` answers `false` here and
// is accepted anyway, because the table is consulted first.
//
// The two spellings `Object::set()` handles outside the table (`script` and
// `metadata/*`, `object.cpp:227-242`) are `false` too unless they are in the
// table: `script` is listed by every `Resource`, and a `metadata/...` key is not
// a property of the resource the bag addresses (no reader of this module answers
// one), so it stays a `-32602` naming the argument. That is a deliberate,
// documented boundary (REPORT-049 section 4), not an oversight.
//
// Everything this predicate answers `false` for - a `:` sub-property path,
// `a.b`, `a[0]`, a name with spaces, the empty name - can never address a table
// entry, so it is a bad *argument* (`-32602`) rather than an unknown property
// (`-32001`). That is the TASK-037 judgement; TASK-049 only stops applying it to
// names the table really carries.
namespace MCPTools {

bool resource_bag_name_is_addressable(const StringName &p_name) {
	return String(p_name).is_valid_identifier();
}

} // namespace MCPTools

// The declared type of a property, or NIL when the object does not have it.
static Variant::Type _property_type(const Object *p_object, const StringName &p_name) {
	const Variant current = p_object->get(p_name);
	if (current.get_type() == Variant::NIL) {
		return Variant::NIL;
	}
	return current.get_type();
}

// The JSON image of a property, for the old/new pair of a `changed` entry.
static Variant _serialized_property(const Object *p_object, const StringName &p_name) {
	return serialize_variant(p_object->get(p_name));
}

// ---------------------------------------------------------------------------
// TASK-022 D-5: "was it really set?" is a **read-back** question.
//
// `project_create_resource` used to answer `properties_set: ["min_value"]` for
// `Curve.min_value = 5.0` and report nothing else, while the engine's own setter
// had stored `max_value - 0.01` (0.99) - the M4b re-audit measured it and noted
// that the sibling `project_edit_resource` answers the same call with a real
// `changed: {min_value: {old, new}}`. The two entries now have one standard: the
// value is read back after `Object::set()` and compared with what the caller
// asked for, and an attribute the setter did not store as asked is reported as
// `ignored` instead of as "set".
//
// The comparison is made at the width the member really stores. A single
// precision member keeps the nearest `float`, so `(double)(float)0.1` is not
// `0.1`; comparing doubles would report a perfectly good write as "ignored". For
// every other target the serialized images are compared directly (a vector is a
// component object on both sides, so the comparison is a structural one).
//
// MCP-NARROWING: G24-RESOURCE-SET-WIDTH (TASK-023 D-7). The `(real_t)` casts
// below narrow a serialized `double` to the member's width; they are safe
// **because they are the comparison's own width**, and they cannot lose a value
// the write gate has already refused: `properties` is coerced through
// `coerce_to_property_type` (the `REAL_T` slot) *before* `Object::set()`, so the
// requested side is a value the 32-bit slot can hold, and both sides are then
// narrowed to that one width. A caller that could reach this line with `1e300`
// would get the honest answer "the stored value is not the request" - which is
// what the `ignored` entry of the D-5 read-back exists to say.
// ---------------------------------------------------------------------------
static bool _stored_value_matches_request(const Variant &p_requested_serialized,
		const Variant &p_stored_serialized, Variant::Type p_target_type) {
	if (p_target_type == Variant::FLOAT) {
		// MCP-NARROWING: G24-RESOURCE-SET-WIDTH - the two `(real_t)` casts below
		// are the comparison's own width, and the requested side reached this
		// function through the `REAL_T` gate (TASK-023 D-7).
		return (real_t)p_requested_serialized == (real_t)p_stored_serialized;
	}
	return p_requested_serialized == p_stored_serialized;
}

// The one `properties` bag writer both resource tools use. TASK-049: it is
// declared in this group's header (next to `register_...`) because a doctest has
// to be able to pin the name rule against the engine's whole property table
// without a live project file - the same reason `MCPTools::set_project_setting`
// and `MCPTools::write_node_property` are exported. Its rules are written out
// next to its definition, below.

// ---------------------------------------------------------------------------
// Atomic publish (TASK-007 section 3.1)
//
// `ResourceSaver::save()` writes straight into the destination, so a failure in
// the middle of a save (a full disk, a format saver that refuses the value, a
// write error) can leave a truncated - that is, **corrupted** - file where the
// caller's resource used to be. The migration source did exactly that.
//
// TASK-008 section 3 hoisted the mechanism into `tools/tool_helpers.*`
// (`publish_file_atomically`, `temporary_sibling_path`) so that the editor write
// group's `editor_save_scene` shares it instead of growing a second, subtly
// different copy. What is left here is the same private name the four tools of
// this group already call, plus the one-line adapter that lets the shared helper
// drive `ResourceSaver::save()`:
//
//   * the temporary file name keeps its extension last (`created.mcp-tmp.tres`),
//     because `ResourceFormatSaver::recognize_path()` compares the text after the
//     **last** dot against the saver's extension list (a measured bug of an
//     earlier revision, REPORT-007 section 8.1);
//   * the destination is only touched after a *successful* save of a temporary
//     sibling that really exists, the old bytes are copied aside first, and a
//     failed publish puts them back.
//
// On every failure path the temporary file (and the backup) is removed: the
// group may not leave a half-written artefact behind.
// ---------------------------------------------------------------------------

static Error _resource_save_writer(const String &p_temp_path, void *p_userdata) {
	const Ref<Resource> *resource = static_cast<const Ref<Resource> *>(p_userdata);
	return ResourceSaver::save(*resource, p_temp_path);
}

static Error _save_resource_atomically(const Ref<Resource> &p_resource, const String &p_path) {
	// The `Ref` is copied into a local so that the callback has a stable address
	// for the whole call; `publish_file_atomically` never stores it.
	Ref<Resource> held = p_resource;
	return publish_file_atomically(p_path, _resource_save_writer, &held);
}

// ---------------------------------------------------------------------------
// project_create_resource (old `create_resource`, resource.rs:199)
//
// `path` + `type` are required; `properties` (object) and `overwrite` (bool,
// default false) are optional. The type has to be an *instantiable* `Resource`
// subclass; an unknown or non-resource class is -32602, because it is the
// argument that names the class. An existing file is refused with -32000 unless
// `overwrite = true` says otherwise - the migration source had that guard, and
// the write group keeps it.
//
// Returns `{"path","type","properties_set":[...],"changed":{}}`.
// ---------------------------------------------------------------------------

static Variant _tool_create_resource(const Dictionary &p_args, MCPToolError &r_error) {
	String raw_path;
	if (!require_string(p_args, "path", raw_path, r_error)) {
		return Variant();
	}
	String path;
	if (!normalize_project_path(raw_path, path, r_error)) {
		return Variant();
	}
	String type_name;
	if (!require_string(p_args, "type", type_name, r_error)) {
		return Variant();
	}
	Dictionary properties;
	if (!_optional_properties(p_args, properties, r_error)) {
		return Variant();
	}
	bool overwrite = false;
	if (!optional_bool(p_args, "overwrite", false, overwrite, r_error)) {
		return Variant();
	}

	if (path == String("res://")) {
		r_error = MCPToolError::invalid_params(
				"Parameter 'path' must name a file, got the project root 'res://'");
		return Variant();
	}
	if (FileAccess::exists(path) && !overwrite) {
		r_error = MCPToolError::tool_state(vformat("Resource already exists: %s", path),
				"Set overwrite=true to replace the existing file");
		return Variant();
	}

	const StringName class_name(type_name);
	if (!ClassDB::class_exists(class_name) || !ClassDB::can_instantiate(class_name) ||
			!ClassDB::is_parent_class(class_name, "Resource")) {
		r_error = MCPToolError::invalid_params(
				vformat("Parameter 'type' must name a resource class, got '%s'", type_name));
		return Variant();
	}
	Object *created = ClassDB::instantiate(class_name);
	Resource *resource = Object::cast_to<Resource>(created);
	if (resource == nullptr) {
		if (created != nullptr) {
			memdelete(created);
		}
		r_error = MCPToolError::invalid_params(
				vformat("Parameter 'type' must name a resource class, got '%s'", type_name));
		return Variant();
	}
	const Ref<Resource> resource_ref(resource);

	Array properties_set;
	if (!properties.is_empty()) {
		const HashSet<StringName> names = _property_names(resource);
		const Array keys = properties.keys();
		for (int i = 0; i < keys.size(); i++) {
			const StringName key(keys[i]);
			if (!names.has(key) || !key.is_valid_identifier()) {
				// An unknown property is skipped, exactly like the migration
				// source (it skipped what `get()` reported as nil).
				continue;
			}
			Variant value;
			if (!_coerce_to_property_type(_property_value_from_json(properties[keys[i]], _property_type(resource, key)),
						_property_type(resource, key), value, r_error)) {
				return Variant();
			}
			resource->set(key, value);
			properties_set.push_back(String(key));
		}
	}

	const Error save_error = _save_resource_atomically(resource_ref, path);
	if (save_error != OK) {
		r_error = MCPToolError::internal(vformat("Failed to save resource: %s", error_names[(int)save_error]));
		return Variant();
	}

	Dictionary result;
	result["path"] = path;
	result["type"] = resource->get_class();
	result["properties_set"] = properties_set;
	result["changed"] = Dictionary();
	return result;
}

// ---------------------------------------------------------------------------
// project_create_scene_file (old `create_scene`, scene.rs:171)
//
// `path` is required; `root_type` (default "Node2D") and `root_name` (default:
// the file stem) are optional. The root type has to be an instantiable `Node`
// subclass. Unlike the migration source this tool **refuses to replace an
// existing file** (-32000 + suggestion): the contract has no `overwrite`
// argument, and a write tool that silently replaces a scene is not something a
// caller can opt out of. Everything else - the packing, the root name default,
// the "Node" fallback of the reference's `unwrap_or` - is unchanged.
//
// Returns `{"path","root_type","root_name","created":true}`.
// ---------------------------------------------------------------------------

static Variant _tool_create_scene_file(const Dictionary &p_args, MCPToolError &r_error) {
	String raw_path;
	if (!require_string(p_args, "path", raw_path, r_error)) {
		return Variant();
	}
	String path;
	if (!normalize_project_path(raw_path, path, r_error)) {
		return Variant();
	}
	String type_name;
	if (!optional_string(p_args, "root_type", "Node2D", type_name, r_error)) {
		return Variant();
	}
	String requested_name;
	if (!optional_string(p_args, "root_name", String(), requested_name, r_error)) {
		return Variant();
	}

	if (path == String("res://")) {
		r_error = MCPToolError::invalid_params(
				"Parameter 'path' must name a file, got the project root 'res://'");
		return Variant();
	}
	if (FileAccess::exists(path)) {
		r_error = MCPToolError::tool_state(vformat("Scene file already exists: %s", path),
				"Delete it first with project_delete_scene_file, or choose another path");
		return Variant();
	}

	const StringName class_name(type_name);
	if (!ClassDB::class_exists(class_name) || !ClassDB::can_instantiate(class_name) ||
			!ClassDB::is_parent_class(class_name, "Node")) {
		r_error = MCPToolError::invalid_params(
				vformat("Parameter 'root_type' must name a node class, got '%s'", type_name));
		return Variant();
	}
	Object *created = ClassDB::instantiate(class_name);
	Node *root = Object::cast_to<Node>(created);
	if (root == nullptr) {
		if (created != nullptr) {
			memdelete(created);
		}
		r_error = MCPToolError::invalid_params(
				vformat("Parameter 'root_type' must name a node class, got '%s'", type_name));
		return Variant();
	}

	String root_name = requested_name;
	if (root_name.is_empty()) {
		root_name = path.get_file().get_basename();
	}
	if (root_name.is_empty()) {
		root_name = "Node";
	}
	root->set_name(root_name);

	Ref<PackedScene> scene;
	scene.instantiate();
	const Error pack_error = scene->pack(root);
	if (pack_error != OK) {
		memdelete(root);
		r_error = MCPToolError::internal(vformat("Failed to pack the scene: %s", error_names[(int)pack_error]));
		return Variant();
	}
	// The packed scene holds everything it needs; the temporary root node goes
	// away again once packing succeeded (the reference `queue_free()`s it).
	memdelete(root);

	const Error save_error = _save_resource_atomically(scene, path);
	if (save_error != OK) {
		r_error = MCPToolError::internal(vformat("Failed to save the scene: %s", error_names[(int)save_error]));
		return Variant();
	}

	Dictionary result;
	result["path"] = path;
	result["root_type"] = type_name;
	result["root_name"] = root_name;
	result["created"] = true;
	return result;
}

// ---------------------------------------------------------------------------
// project_delete_scene_file (old `delete_scene`, scene.rs:251)
//
// `path` is required and must exist, otherwise -32001 with a suggestion (the
// migration source returned not_found as well). The scene file and, when it is
// there, its `<path>.import` sidecar are removed - the `rescan` the reference
// performed afterwards is an editor-side refresh that the tool does not need.
//
// Returns `{"path","deleted":true}` where `path` is the *normalised* path.
// ---------------------------------------------------------------------------

static Variant _tool_delete_scene_file(const Dictionary &p_args, MCPToolError &r_error) {
	String raw_path;
	if (!require_string(p_args, "path", raw_path, r_error)) {
		return Variant();
	}
	String path;
	if (!normalize_project_path(raw_path, path, r_error)) {
		return Variant();
	}

	if (!FileAccess::exists(path)) {
		r_error = MCPToolError::not_found(vformat("Scene file '%s'", path),
				"Use project_get_filesystem_tree to list the .tscn files of the project");
		return Variant();
	}

	const Error remove_error = DirAccess::remove_absolute(path);
	if (remove_error != OK) {
		r_error = MCPToolError::internal(vformat("Failed to delete the scene file: %s",
				error_names[(int)remove_error]));
		return Variant();
	}
	// A scene that was imported has a sidecar; it is removed with the scene.
	const String import_path = path + ".import";
	if (FileAccess::exists(import_path)) {
		DirAccess::remove_absolute(import_path);
	}

	Dictionary result;
	result["path"] = path;
	result["deleted"] = true;
	return result;
}

// ---------------------------------------------------------------------------
// project_edit_resource (old `edit_resource`, resource.rs:131)
//
// `path` and `properties` are both required. The resource is loaded, every
// property of the bag that the resource actually has is written, and the result
// is saved. Unknown property names are **skipped**, not reported - the migration
// source skipped whatever `get()` answered nil for.
//
// Returns `{"path","type","changed":{<name>:{"old","new"}}}`; when nothing was
// changed the reference's own `{"path","changed":{},"message":"No properties
// were changed"}` shape is returned and nothing is written.
// ---------------------------------------------------------------------------

static bool _require_properties(const Dictionary &p_args, Dictionary &r_out, MCPToolError &r_error) {
	const Variant value = p_args.get("properties", Variant());
	if (value.get_type() == Variant::NIL) {
		r_error = MCPToolError::invalid_params("Missing required parameter: properties");
		return false;
	}
	if (value.get_type() != Variant::DICTIONARY) {
		r_error = MCPToolError::invalid_params(vformat("Parameter 'properties' must be an object, got %s",
				Variant::get_type_name(value.get_type())));
		return false;
	}
	r_out = value;
	return true;
}

static Variant _tool_edit_resource(const Dictionary &p_args, MCPToolError &r_error) {
	String raw_path;
	if (!require_string(p_args, "path", raw_path, r_error)) {
		return Variant();
	}
	String path;
	if (!normalize_project_path(raw_path, path, r_error)) {
		return Variant();
	}
	Dictionary properties;
	if (!_require_properties(p_args, properties, r_error)) {
		return Variant();
	}

	if (!FileAccess::exists(path)) {
		r_error = MCPToolError::not_found(vformat("Resource '%s'", path),
				"Use project_get_filesystem_tree to list the resources of the project");
		return Variant();
	}
	const Ref<Resource> resource = ResourceLoader::load(path);
	if (resource.is_null()) {
		// The file is there but is not (or no longer) a loadable resource. It is
		// deliberately left exactly as it is: a read failure must never turn
		// into a write.
		r_error = MCPToolError::not_found(vformat("Loadable resource '%s'", path),
				"The file exists but could not be loaded as a resource; fix or delete it first");
		return Variant();
	}

	const HashSet<StringName> names = _property_names(resource);
	Dictionary changed;

	const Array keys = properties.keys();
	for (int i = 0; i < keys.size(); i++) {
		const StringName key(keys[i]);
		if (!names.has(key) || !key.is_valid_identifier()) {
			continue;
		}
		const Variant old_value = _serialized_property(resource, key);
		Variant value;
		if (!_coerce_to_property_type(_property_value_from_json(properties[keys[i]], _property_type(resource, key)),
					_property_type(resource, key), value, r_error)) {
			return Variant();
		}
		resource->set(key, value);

		Dictionary entry;
		entry["old"] = old_value;
		entry["new"] = _serialized_property(resource, key);
		changed[String(key)] = entry;
	}

	// The reference's "nothing to do" short circuit: when the bag named no
	// property the resource actually has, nothing is written and no file is
	// touched at all. (A property that is written with its current value *is* a
	// change - the reference reports it the same way - and rewriting identical
	// bytes is harmless.)
	if (changed.is_empty()) {
		Dictionary result;
		result["path"] = path;
		result["changed"] = Dictionary();
		result["message"] = "No properties were changed";
		return result;
	}

	const Error save_error = _save_resource_atomically(resource, path);
	if (save_error != OK) {
		r_error = MCPToolError::internal(vformat("Failed to save resource: %s", error_names[(int)save_error]));
		return Variant();
	}

	Dictionary result;
	result["path"] = path;
	result["type"] = resource->get_class();
	result["changed"] = changed;
	return result;
}

// ---------------------------------------------------------------------------
// Registration
// ---------------------------------------------------------------------------

// The authoritative `description` and `inputSchema` of each tool are the contract
// entries of docs/tools_list.renamed.json, character for character. The schemas
// are parsed from the exact contract JSON instead of being rebuilt as a
// hand-written Dictionary - a hand transcription is where a description byte or
// the type of a `"default": false` drifts, and gate 1 compares all three fields
// verbatim. Godot's JSON has a single number type, so integral numbers are
// folded back to INT (`"default": 256` would otherwise be written `256.0`).
static Variant _fold_integral_numbers(const Variant &p_value) {
	switch (p_value.get_type()) {
		case Variant::FLOAT: {
			const double number = p_value;
			if (number >= -9.0e15 && number <= 9.0e15) {
				const int64_t truncated = (int64_t)number;
				if ((double)truncated == number) {
					return Variant(truncated);
				}
			}
			return p_value;
		}
		case Variant::DICTIONARY: {
			const Dictionary source = p_value;
			Dictionary out;
			const Array keys = source.keys();
			for (int i = 0; i < keys.size(); i++) {
				out[keys[i]] = _fold_integral_numbers(source[keys[i]]);
			}
			return out;
		}
		case Variant::ARRAY: {
			const Array source = p_value;
			Array out;
			for (int i = 0; i < source.size(); i++) {
				out.push_back(_fold_integral_numbers(source[i]));
			}
			return out;
		}
		default:
			return p_value;
	}
}

static Dictionary _schema_from_json(const char *p_json) {
	JSON json;
	if (json.parse(String::utf8(p_json)) != OK) {
		ERR_PRINT("MCPTools: invalid inputSchema literal in project_write_resource_scene.cpp");
		return Dictionary();
	}
	return _fold_integral_numbers(json.get_data());
}

void register_project_write_resource_scene_tools(MCPToolRegistry &r_registry) {
	// Order follows docs/tool-groups.json. The order is not a contract, but it
	// has to be stable and append-only. Every tool is channel `project`,
	// `mutating = true` (the only mutating group of B1) and `scope = BOTH`.
	{
		ToolBuilder builder("project_create_resource", String::utf8(R"desc(创建新资源文件)desc"));
		builder.channel("project").verb("create").scope(MCPToolScope::BOTH).mutating(true);
		builder.schema(_schema_from_json(R"schema({"properties":{"overwrite":{"default":false,"description":"是否覆盖已存在的文件","type":"boolean"},"path":{"description":"保存路径 (res://)","type":"string"},"properties":{"description":"初始属性字典","type":"object"},"type":{"description":"资源类型","type":"string"}},"required":["path","type"],"type":"object"})schema"));
		builder.handler(_tool_create_resource).register_into(r_registry);
	}

	{
		ToolBuilder builder("project_create_scene_file", String::utf8(R"desc(创建新场景文件)desc"));
		builder.channel("project").verb("create").scope(MCPToolScope::BOTH).mutating(true);
		builder.schema(_schema_from_json(R"schema({"properties":{"path":{"description":"保存路径 (res://)","type":"string"},"root_name":{"description":"根节点名称 (可选)","type":"string"},"root_type":{"default":"Node2D","description":"根节点类型","type":"string"}},"required":["path"],"type":"object"})schema"));
		builder.handler(_tool_create_scene_file).register_into(r_registry);
	}

	{
		ToolBuilder builder("project_delete_scene_file", String::utf8(R"desc(删除场景文件)desc"));
		builder.channel("project").verb("delete").scope(MCPToolScope::BOTH).mutating(true);
		builder.schema(_schema_from_json(R"schema({"properties":{"path":{"description":"要删除的场景文件路径 (res://)","type":"string"}},"required":["path"],"type":"object"})schema"));
		builder.handler(_tool_delete_scene_file).register_into(r_registry);
	}

	{
		ToolBuilder builder("project_edit_resource", String::utf8(R"desc(编辑资源文件属性并保存)desc"));
		builder.channel("project").verb("edit").scope(MCPToolScope::BOTH).mutating(true);
		builder.schema(_schema_from_json(R"schema({"properties":{"path":{"description":"资源文件路径 (res://)","type":"string"},"properties":{"description":"要修改的属性字典","type":"object"}},"required":["path","properties"],"type":"object"})schema"));
		builder.handler(_tool_edit_resource).register_into(r_registry);
	}
}
