#include "project_read_template.h"

#include "tool_builder.h"

#include "core/config/project_settings.h"
#include "core/error/error_macros.h"
#include "core/io/dir_access.h"
#include "core/io/file_access.h"
#include "core/variant/variant.h"
#include "scene/main/scene_tree.h"
#include "scene/main/window.h"

// Editor-only engine APIs are compiled in only for a tools build (TASK-002
// section 2.2.3). `MCP_EDITOR_TOOLS_ENABLED` is defined in tools/tool_builder.h.
#ifdef MCP_EDITOR_TOOLS_ENABLED
#include "editor/editor_interface.h"
#include "scene/gui/control.h"
#endif

using namespace MCPTools;

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

static String _get_project_string(const String &p_key) {
	ProjectSettings *settings = ProjectSettings::get_singleton();
	if (settings == nullptr || !settings->has_setting(p_key)) {
		return String();
	}
	return (String)settings->get_setting(p_key);
}

// Mirrors `serialize_variant` of the reference implementation: everything that
// is not directly JSON representable is converted into a plain structure so
// that `JSON::stringify` never has to deal with engine-only types.
static Variant _serialize_variant(const Variant &p_value) {
	switch (p_value.get_type()) {
		case Variant::NIL: {
			return Variant();
		}
		case Variant::BOOL: {
			return (bool)p_value;
		}
		case Variant::INT: {
			return (int64_t)p_value;
		}
		case Variant::FLOAT: {
			return (double)p_value;
		}
#endif
	SceneTree *tree = SceneTree::get_singleton();
	if (tree != nullptr && tree->get_root() != nullptr) {
		const Vector2i size = tree->get_root()->get_visible_rect().size;
		// MCP-NARROWING: G24-VIEWPORT-SIZE - the two `Vector2(...)` calls of this
		// function are the **widening** direction: a `Vector2i` component is an
		// `int` and a `Vector2` component is a `real_t`, so `Vector2(size)` and
		// `Vector2()` cannot lose a value. The source is the engine's own
		// viewport size, not caller input (TASK-023 D-7 scan entry).
		return Vector2(size);
	}
	// MCP-NARROWING: G24-VIEWPORT-SIZE - the zero vector fallback (see above).
	return Vector2();
}

// Rust's `str::trim_matches('*')`.
static String _trim_stars(const String &p_value) {
	int begin = 0;
// project_get_settings
// ---------------------------------------------------------------------------

static Variant _tool_get_project_settings(const Dictionary &p_args, MCPToolError &r_error) {
	ProjectSettings *settings = ProjectSettings::get_singleton();
	if (settings == nullptr) {
		r_error = MCPToolError::not_implemented("ProjectSettings",
				"ProjectSettings is only available inside a running engine");
		return Variant();
	}

	String prefix;
	if (!optional_string(p_args, "prefix", String(), prefix, r_error)) {
		return Variant();
	}
	bool include_default = false;
	if (!optional_bool(p_args, "include_default", false, include_default, r_error)) {
		return Variant();
	}
	// Accepted for contract compatibility; the reference implementation does not
	// use it either (it always reports the current effective values).
	(void)include_default;

	Dictionary out;
	int count = 0;

	List<PropertyInfo> property_list;
	settings->get_property_list(&property_list);
	for (const PropertyInfo &info : property_list) {
		const String name = info.name;
		if (!prefix.is_empty() && !name.begins_with(prefix)) {
			continue;
		}
		const Variant value = settings->has_setting(name) ? settings->get_setting(name) : Variant();
		out[name] = serialize_variant(value);
		count++;
	}

	Dictionary result;
	result["settings"] = out;
	result["count"] = count;
	return result;
}

// ---------------------------------------------------------------------------
// project_get_filesystem_tree
// ---------------------------------------------------------------------------

static Dictionary _scan_directory(const String &p_path, int64_t p_max_depth, int64_t p_depth) {
	Dictionary node;
	node["name"] = (p_path == "res://") ? String("res://") : p_path.get_file();
	node["path"] = p_path;
	node["type"] = "directory";

	if (p_max_depth >= 0 && p_depth > p_max_depth) {
		return node;
	}
	Ref<DirAccess> dir = DirAccess::open(p_path);
	if (dir.is_null()) {
		// A nested directory that cannot be read is skipped silently, exactly
		// like the reference; the *root* is validated by the caller.
		return node;
	}

	Array children;
	dir->list_dir_begin();
	while (true) {
		const String entry = dir->get_next();
		if (entry.is_empty()) {
			break;
		}
		if (entry == "." || entry == "..") {
			continue;
		}
		const bool is_dir = dir->current_is_dir();
		const String full = join_path(p_path, entry);
		if (is_dir) {
			children.push_back(_scan_directory(full, p_max_depth, p_depth + 1));
		} else {
			Dictionary file_node;
			file_node["name"] = entry;
			file_node["path"] = full;
			file_node["type"] = "file";
			children.push_back(file_node);
		}
	}
	dir->list_dir_end();

	if (!children.is_empty()) {
		node["children"] = children;
	}
	return node;
}

static Variant _tool_get_filesystem_tree(const Dictionary &p_args, MCPToolError &r_error) {
	String path;
	int64_t max_depth = -1;
	if (!optional_string(p_args, "path", "res://", path, r_error)) {
		return Variant();
	}
	if (!optional_int(p_args, "max_depth", -1, max_depth, r_error)) {
		return Variant();
	}
	String normalized;
	if (!normalize_project_path(path, normalized, r_error)) {
		return Variant();
	}
	// A root directory that does not exist is a tool error (-32001, GDR-14).
	Ref<DirAccess> probe = open_project_dir(normalized, r_error);
	if (probe.is_null()) {
		return Variant();
	}

	Dictionary result;
	result["tree"] = _scan_directory(normalized, max_depth, 0);
	return result;
}

// ---------------------------------------------------------------------------
// project_search_file_names (old `search_files`)
//
// Only the *file name* is matched, case insensitively, with a cap of 200. Note
// that the reference does not skip `addons` or `.godot` here (unlike the content
// search), which is part of why the two tools are not the same tool.
// ---------------------------------------------------------------------------

static const int SEARCH_FILE_NAMES_MAX = 200;

static void _search_file_names_recursive(const String &p_path, const String &p_query, Array &r_matches, int p_max) {
	if (r_matches.size() >= p_max) {
		return;
	}
	Ref<DirAccess> dir = DirAccess::open(p_path);
	if (dir.is_null()) {
		return;
	}
	dir->list_dir_begin();
	while (true) {
		const String entry = dir->get_next();
		if (entry.is_empty()) {
			break;
		}
		if (entry == "." || entry == "..") {
			continue;
		}
		const String full = join_path(p_path, entry);
		if (dir->current_is_dir()) {
			_search_file_names_recursive(full, p_query, r_matches, p_max);
		} else if (entry.to_lower().contains(p_query.to_lower())) {
			r_matches.push_back(full);
		}
		if (r_matches.size() >= p_max) {
			break;
		}
	}
	dir->list_dir_end();
}

static Variant _tool_search_file_names(const Dictionary &p_args, MCPToolError &r_error) {
	String pattern;
	if (!require_string(p_args, "pattern", pattern, r_error)) {
		return Variant();
	}
	String path;
	if (!optional_string(p_args, "path", "res://", path, r_error)) {
		return Variant();
	}
	String normalized;
	if (!normalize_project_path(path, normalized, r_error)) {
		return Variant();
	}
	Ref<DirAccess> probe = open_project_dir(normalized, r_error);
	if (probe.is_null()) {
		return Variant();
	}

	Array matches;
	_search_file_names_recursive(normalized, pattern, matches, SEARCH_FILE_NAMES_MAX);

	Dictionary result;
	result["matches"] = matches;
	result["count"] = matches.size();
	return result;
}

// ---------------------------------------------------------------------------
// project_search_file_contents (old `search_in_files`)
//
// Per line {file, line, text}, case insensitive, cap 50, skipping the `addons`
// and `.godot` directories and restricted to a fixed text extension whitelist.
// ---------------------------------------------------------------------------

static const int SEARCH_FILE_CONTENTS_MAX = 50;

static const char *SEARCH_CONTENTS_EXTENSIONS[] = {
	"gd", "tscn", "tres", "cfg", "godot", "gdshader", "md", "txt", "json", "yaml", "yml", "xml", "csv", "ini"
};

static bool _is_searchable_text_extension(const String &p_extension) {
	for (const char *extension : SEARCH_CONTENTS_EXTENSIONS) {
		if (p_extension == extension) {
			return true;
		}
	}
	return false;
}

static void _search_file_contents_recursive(const String &p_path, const String &p_query, const String &p_file_pattern, Array &r_matches, int p_max) {
	if (r_matches.size() >= p_max) {
		return;
	}
	Ref<DirAccess> dir = DirAccess::open(p_path);
	if (dir.is_null()) {
		return;
	}
	dir->list_dir_begin();
	while (true) {
		const String entry = dir->get_next();
		if (entry.is_empty()) {
			break;
		}
		if (entry == "." || entry == "..") {
			continue;
		}
		const String full = join_path(p_path, entry);
		if (dir->current_is_dir()) {
			if (entry != "addons" && entry != ".godot") {
				_search_file_contents_recursive(full, p_query, p_file_pattern, r_matches, p_max);
			}
		} else if (p_file_pattern == "*" || entry.contains(_trim_stars(p_file_pattern))) {
			if (_is_searchable_text_extension(file_extension(entry))) {
				String contents;
				MCPToolError ignored;
				if (read_project_text_file(full, contents, ignored)) {
					const Vector<String> lines = split_lines(contents);
					for (int i = 0; i < lines.size(); i++) {
static Variant _tool_search_file_contents(const Dictionary &p_args, MCPToolError &r_error) {
	String pattern;
	if (!require_string(p_args, "pattern", pattern, r_error)) {
		return Variant();
	}
	String file_pattern;
	if (!optional_string(p_args, "file_pattern", "*", file_pattern, r_error)) {
		return Variant();
	}
	String path;
	if (!optional_string(p_args, "path", "res://", path, r_error)) {
		return Variant();
	}
	String normalized;
	if (!normalize_project_path(path, normalized, r_error)) {
		return Variant();
	}
	Ref<DirAccess> probe = open_project_dir(normalized, r_error);
	if (probe.is_null()) {
		return Variant();
	}

	Array matches;
	_search_file_contents_recursive(normalized, pattern, file_pattern, matches, SEARCH_FILE_CONTENTS_MAX);

	Dictionary result;
	result["matches"] = matches;
	result["count"] = matches.size();
	// The reference returns the query back as well; the contract keeps it.
	result["query"] = pattern;
	return result;
}

// ---------------------------------------------------------------------------
// project_find_files_referencing_symbol (old `find_node_references`)
//
// Aggregated per file {file, lines[]}, case SENSITIVE, cap 100, at most 5 line
// numbers per file, hidden entries and `addons` skipped, and only the four
// reference-bearing extensions scanned. This is the de-merged twin of
// project_search_file_contents (GDR-17): the two must never be collapsed back
// numbers per file, hidden entries and `addons` skipped, and only the four
// reference-bearing extensions scanned. This is the de-merged twin of
// project_search_file_contents (GDR-17): the two must never be collapsed back
// into one implementation.
// ---------------------------------------------------------------------------

static const int FIND_REFERENCES_MAX = 100;
static const int FIND_REFERENCES_MAX_LINES_PER_FILE = 5;

static bool _has_reference_extension(const String &p_file_name) {
	// Suffix test, exactly like the reference (case sensitive).
	return p_file_name.ends_with(".tscn") || p_file_name.ends_with(".gd") ||
			p_file_name.ends_with(".tres") || p_file_name.ends_with(".gdshader");
}

static void _scan_for_pattern_recursive(const String &p_path, const String &p_pattern, Array &r_matches, int p_max) {
	if (r_matches.size() >= p_max) {
		return;
	}
	Ref<DirAccess> dir = DirAccess::open(p_path);
	if (dir.is_null()) {
		return;
	}
	dir->list_dir_begin();
	while (true) {
		const String entry = dir->get_next();
		if (entry.is_empty()) {
			break;
		}
		if (r_matches.size() >= p_max) {
			break;
		}
		// Covers "." and ".." as well as any hidden entry.
		if (entry.begins_with(".")) {
			continue;
		}
		const String full = _join_path(p_path, entry);
		if (dir->current_is_dir()) {
			if (entry == "addons") {
				continue;
			}
			_scan_for_pattern_recursive(full, p_pattern, r_matches, p_max);
		} else if (_has_reference_extension(entry)) {
			String contents;
			MCPToolError ignored;
			if (read_project_text_file(full, contents, ignored) && contents.contains(p_pattern)) {
				Array lines;
				const Vector<String> split = _split_lines(contents);
				for (int i = 0; i < split.size(); i++) {
					if (lines.size() >= FIND_REFERENCES_MAX_LINES_PER_FILE) {
						break;
					}
					if (split[i].contains(p_pattern)) {
						lines.push_back(i + 1);
					}
				}
				Dictionary hit;
				hit["file"] = full;
				hit["lines"] = lines;
				r_matches.push_back(hit);