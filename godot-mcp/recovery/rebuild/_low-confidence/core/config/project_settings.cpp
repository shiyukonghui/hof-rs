bool ProjectSettings::_set(const StringName &p_name, const Variant &p_value) {
	_THREAD_SAFE_METHOD_

	// Early return if value hasn't changed (unless it's being deleted)
	if (p_value.get_type() != Variant::NIL) {
		if (props.has(p_name) && props[p_name].variant == p_value) {
			return true;
		}
	}

	if (p_value.get_type() == Variant::NIL) {
		props.erase(p_name);
		if (p_name.string().begins_with("autoload/")) {
			String node_name = p_name.string().get_slicec('/', 1);
			if (autoloads.has(node_name)) {
				remove_autoload(node_name);
			}
		} else if (p_name.string().begins_with("global_group/")) {
			String group_name = p_name.string().get_slicec('/', 1);
			if (global_groups.has(group_name)) {
				remove_global_group(group_name);
			}
		}
	} else {
		if (p_name == CoreStringName(_custom_features)) {
			Vector<String> custom_feature_array = String(p_value).split(",");
			for (int i = 0; i < custom_feature_array.size(); i++) {
				custom_features.insert(custom_feature_array[i]);
			}

			_version++;
			_queue_changed(p_name);
			return true;
		}

		{ // Feature overrides.
			int dot = p_name.string().find_char('.');
			if (dot != -1) {
				Vector<String> s = p_name.string().split(".");

				for (int i = 1; i < s.size(); i++) {
					String feature = s[i].strip_edges();
					Pair<StringName, StringName> feature_override(feature, p_name);

					if (!feature_overrides.has(s[0])) {
						feature_overrides[s[0]] = LocalVector<Pair<StringName, StringName>>();
					}

					feature_overrides[s[0]].push_back(feature_override);
				}
			}
		}

		if (props.has(p_name)) {
			props[p_name].variant = p_value;
		} else {
			props[p_name] = VariantContainer(p_value, last_order++);
		}
		if (p_name.string().begins_with("autoload_prepend/")) {
			String node_name = p_name.string().get_slicec('/', 1);
			AutoloadInfo autoload;
			autoload.name = node_name;
			String path = p_value;
			if (path.begins_with("*")) {
				autoload.is_singleton = true;
				autoload.path = path.substr(1).simplify_path();
			} else {
				autoload.path = path.simplify_path();
			}
			add_autoload(autoload, true);
		} else if (p_name.string().begins_with("autoload/")) {
			String node_name = p_name.string().get_slicec('/', 1);
			AutoloadInfo autoload;
			autoload.name = node_name;
			String path = p_value;
			if (path.begins_with("*")) {
				autoload.is_singleton = true;
				autoload.path = path.substr(1).simplify_path();
			} else {
				autoload.path = path.simplify_path();
			}
			add_autoload(autoload);
		} else if (p_name.string().begins_with("global_group/")) {
			String group_name = p_name.string().get_slicec('/', 1);
			add_global_group(group_name, p_value);
		}
	}

	_version++;
	_queue_changed(p_name);
	return true;
}

bool ProjectSettings::_get(const StringName &p_name, Variant &r_ret) const {
	_THREAD_SAFE_METHOD_

	if (!props.has(p_name)) {
		return false;
	}
	r_ret = props[p_name].variant;
	return true;
}

Variant ProjectSettings::get_setting_with_override_and_custom_features(const StringName &p_name, const Vector<String> &p_features) const {
	_THREAD_SAFE_METHOD_

	StringName name = p_name;
	if (feature_overrides.has(name)) {
		const LocalVector<Pair<StringName, StringName>> &overrides = feature_overrides[name];
		for (uint32_t i = 0; i < overrides.size(); i++) {
			if (p_features.has(String(overrides[i].first).to_lower())) {
				if (props.has(overrides[i].second)) {
					name = overrides[i].second;
					break;
				}
};

void ProjectSettings::_get_property_list(List<PropertyInfo> *p_list) const {
	_THREAD_SAFE_METHOD_

	RBSet<_VCSort> vclist;
	HashMap<String, LocalVector<_VCSort>> setting_overrides;

	for (const KeyValue<StringName, VariantContainer> &E : props) {
		const VariantContainer *v = &E.value;

		if (v->hide_from_editor) {
			continue;
		}

		_VCSort vc;
		vc.name = E.key;
		vc.order = v->order;
		vc.type = v->variant.get_type();

		bool internal = v->internal;
		if (!internal) {
			for (const String &F : hidden_prefixes) {
				if (vc.name.begins_with(F)) {
					internal = true;
					break;
				}
			}
		}

		if (internal) {
			vc.flags = PROPERTY_USAGE_STORAGE;
		} else {
			vc.flags = PROPERTY_USAGE_EDITOR | PROPERTY_USAGE_STORAGE;
		}

		if (v->internal) {
			vc.flags |= PROPERTY_USAGE_INTERNAL;
		}

		if (v->basic) {
			vc.flags |= PROPERTY_USAGE_EDITOR_BASIC_SETTING;
		}

		if (v->restart_if_changed) {
			vc.flags |= PROPERTY_USAGE_RESTART_IF_CHANGED;
		}

		int dot = vc.name.rfind_char('.');
		if (dot != -1) {
			StringName n = vc.name.substr(0, dot);
			if (props.has(n)) {
				// Property is an override.
				setting_overrides[n].push_back(vc);
			} else {
				vclist.insert(vc);
			}
		} else {
			vclist.insert(vc);
		}
	}

	for (const _VCSort &base : vclist) {
		if (custom_prop_info.has(base.name)) {
			PropertyInfo pi = custom_prop_info[base.name];
			pi.name = base.name;
			pi.usage = base.flags;
			p_list->push_back(pi);
#ifdef TOOLS_ENABLED
		} else if (base.name.begins_with(EDITOR_SETTING_OVERRIDE_PREFIX)) {

	int lines = 0;
	String error_text;
	String section;
	int config_version = 0;

	while (true) {
		assign = Variant();
		next_tag.fields.clear();
		next_tag.name = String();

		err = VariantParser::parse_tag_assign_eof(&stream, lines, error_text, next_tag, assign, value, nullptr, true);
		if (err == ERR_FILE_EOF) {
			// If we're loading a project.godot from source code, we can operate some
			// ProjectSettings conversions if need be.
			_convert_to_last_version(config_version);
			last_save_time = FileAccess::get_modified_time(get_resource_path().path_join("project.godot"));
			return OK;
		}
		ERR_FAIL_COND_V_MSG(err != OK, err, vformat("Error parsing '%s' at line %d: %s File might be corrupted.", p_path, lines, error_text));

		if (!assign.is_empty()) {
			if (section.is_empty() && assign == "config_version") {
				config_version = value;
				ERR_FAIL_COND_V_MSG(config_version > CONFIG_VERSION, ERR_FILE_CANT_OPEN, vformat("Can't open project at '%s', its `config_version` (%d) is from a more recent and incompatible version of the engine. Expected config version: %d.", p_path, config_version, CONFIG_VERSION));
			} else {
				if (section.is_empty()) {
					set(assign, value);
				} else {
					set(section + "/" + assign, value);
				}
			}
		} else if (!next_tag.name.is_empty()) {
			section = next_tag.name;
		}
	}
}

Error ProjectSettings::_load_settings_text_or_binary(const String &p_text_path, const String &p_bin_path) {
	// Attempt first to load the binary project.godot file.
	Error err = _load_settings_binary(p_bin_path);
	if (err == OK) {
		return OK;
	} else if (err != ERR_FILE_NOT_FOUND) {
		// If the file exists but can't be loaded, we want to know it.
		ERR_PRINT(vformat("Couldn't load file '%s', error code %d.", p_bin_path, err));
	}

	// Fallback to text-based project.godot file if binary was not found.
	err = _load_settings_text(p_text_path);
	if (err == OK) {
#ifndef DISABLE_DEPRECATED
		const PackedStringArray features = get_setting("application/config/features");
		for (const String &feat : features) {
			if (feat.contains_char('.') && feat.get_slice_count(".") == 2) {
				int major_version = feat.get_slicec('.', 0).to_int();
				int minor_version = feat.get_slicec('.', 1).to_int();
				// Major version is irrelevant, but the extra check ensures that the feature is in fact a version string.
				if (major_version == 4 && minor_version < 6) {
					// Enable MeshInstance3D compat for projects created before 4.6.
					set_setting("animation/compatibility/default_parent_skeleton_in_mesh_instance_3d", true);
				}
				break;
			}
		}
#endif
		return OK;
	} else if (err != ERR_FILE_NOT_FOUND) {
		ERR_PRINT(vformat("Couldn't load file '%s', error code %d.", p_text_path, err));
	}
	ERR_FAIL_COND_MSG(!props.has(p_name), vformat("Request for nonexistent project setting: '%s'.", p_name));
	props.erase(p_name);
	_queue_changed(p_name);
}

Error ProjectSettings::save() {
	Error error = save_custom(get_resource_path().path_join("project.godot"));
	if (error == OK) {
		last_save_time = FileAccess::get_modified_time(get_resource_path().path_join("project.godot"));
	}
	return error;
}

Error ProjectSettings::_save_settings_binary(const String &p_file, const RBMap<String, List<String>> &p_props, const CustomMap &p_custom, const String &p_custom_features) {
	Error err;
	Ref<FileAccess> file = FileAccess::open(p_file, FileAccess::WRITE, &err);
	ERR_FAIL_COND_V_MSG(err != OK, err, vformat("Couldn't save project.binary at '%s'.", p_file));

Error ProjectSettings::_save_settings_text(const String &p_file, const RBMap<String, List<String>> &p_props, const CustomMap &p_custom, const String &p_custom_features) {
	Error err;
	Ref<FileAccess> file = FileAccess::open(p_file, FileAccess::WRITE, &err);

	ERR_FAIL_COND_V_MSG(err != OK, err, vformat("Couldn't save project.godot - %s.", p_file));

	file->store_line("; Engine configuration file.");
	file->store_line("; It's best edited using the editor UI and not directly,");
	file->store_line("; since the parameters that go here are not all obvious.");
	file->store_line(";");
	file->store_line("; Format:");
	file->store_line(";   [section] ; section goes between []");
	file->store_line(";   param=value ; assign values to parameters");
	file->store_line("");

	file->store_string("config_version=" + itos(CONFIG_VERSION) + "\n");
	if (!p_custom_features.is_empty()) {
		file->store_string("custom_features=\"" + p_custom_features + "\"\n");
	}
	file->store_string("\n");

	for (const KeyValue<String, List<String>> &E : p_props) {
		if (E.key != p_props.begin()->key) {
			file->store_string("\n");
		}

		if (!E.key.is_empty()) {
			file->store_string("[" + E.key + "]\n\n");
		}
		for (const String &F : E.value) {
			String key = F;
			if (!E.key.is_empty()) {
				key = E.key + "/" + key;
			}
			Variant value;
			if (p_custom.has(key)) {
				value = p_custom[key];
			} else {
				value = get(key);
			}

			String vstr;
			VariantWriter::write_to_string(value, vstr, true);
			file->store_string(F.property_name_encode() + "=" + vstr + "\n");
		}
	}

	return OK;
}

Error ProjectSettings::_save_custom_bnd(const String &p_file) { // add other params as dictionary and array?
	return save_custom(p_file);
}

#ifdef TOOLS_ENABLED
bool _csproj_exists(const String &p_root_dir) {
	Ref<DirAccess> dir = DirAccess::open(p_root_dir);
	ERR_FAIL_COND_V(dir.is_null(), false);

	dir->list_dir_begin();
	String file_name = dir->_get_next();
	while (file_name != "") {
		if (!dir->current_is_dir() && file_name.get_extension() == "csproj") {
			return true;
		}
		file_name = dir->_get_next();
	}

	return false;
}
#endif // TOOLS_ENABLED

Error ProjectSettings::save_custom(const String &p_path, const CustomMap &p_custom, const Vector<String> &p_custom_features, bool p_merge_with_current) {
	ERR_FAIL_COND_V_MSG(p_path.is_empty(), ERR_INVALID_PARAMETER, "Project settings save path cannot be empty.");

Error ProjectSettings::_collect_settings_for_save(const CustomMap &p_custom, bool p_merge_with_current, const Vector<String> &p_custom_features, RBMap<String, List<String>> &r_props, String &r_features) {
#ifdef TOOLS_ENABLED
	PackedStringArray project_features = get_setting("application/config/features");
	// If there is no feature list currently present, force one to generate.
	if (project_features.is_empty()) {
		project_features = ProjectSettings::get_required_features();
	}
	// Check the rendering API.
	const String rendering_api = has_setting("rendering/renderer/rendering_method") ? (String)get_setting("rendering/renderer/rendering_method") : String();
	if (!rendering_api.is_empty()) {
		// Add the rendering API as a project feature if it doesn't already exist.
		if (!project_features.has(rendering_api)) {
			project_features.append(rendering_api);
		}
	}
	// Check for the existence of a csproj file.
	if (_csproj_exists(get_resource_path())) {
		// If there is a csproj file, add the C# feature if it doesn't already exist.
		if (!project_features.has("C#")) {
			project_features.append("C#");
		}
	} else {
		// If there isn't a csproj file, remove the C# feature if it exists.
		if (project_features.has("C#")) {
			project_features.remove_at(project_features.find("C#"));
		}
	}
	project_features = _trim_to_supported_features(project_features);
	set_setting("application/config/features", project_features);
#endif // TOOLS_ENABLED

	RBSet<_VCSort> vclist;

	if (p_merge_with_current) {
		for (const KeyValue<StringName, VariantContainer> &G : props) {
			const VariantContainer *v = &G.value;

			if (v->hide_from_editor) {
				continue;
			}

			if (p_custom.has(G.key)) {
				continue;
			}

			_VCSort vc;
			vc.name = G.key; //*k;
			vc.order = v->order;
			vc.type = v->variant.get_type();
			vc.flags = PROPERTY_USAGE_EDITOR | PROPERTY_USAGE_STORAGE;
			if (v->variant == v->initial) {
				continue;
			}

			vclist.insert(vc);
		}
	}

	for (const KeyValue<String, Variant> &E : p_custom) {
		// Lookup global prop to store in the same order
		RBMap<StringName, VariantContainer>::Iterator global_prop = props.find(E.key);

		_VCSort vc;
		vc.name = E.key;
		vc.order = global_prop ? global_prop->value.order : 0xFFFFFFF;
		vc.type = E.value.get_type();
		vc.flags = PROPERTY_USAGE_STORAGE;
		vclist.insert(vc);
	}

	RBMap<String, List<String>> save_props;

	for (const _VCSort &E : vclist) {
		String category = E.name;
		String name = E.name;

		int div = category.find_char('/');

		if (div < 0) {
			category = "";
		} else {
			category = category.substr(0, div);
			name = name.substr(div + 1);
		}
		save_props[category].push_back(name);
	}

	String save_features;

	for (int i = 0; i < p_custom_features.size(); i++) {
		if (i > 0) {
			save_features += ",";
		}

		String f = p_custom_features[i].strip_edges().remove_char('\"');
		save_features += f;
	}

	r_props = save_props;
	r_features = save_features;
	return OK;
}

Error ProjectSettings::save_custom(const String &p_path, const CustomMap &p_custom, const Vector<String> &p_custom_features, bool p_merge_with_current) {
	ERR_FAIL_COND_V_MSG(p_path.is_empty(), ERR_INVALID_PARAMETER, "Project settings save path cannot be empty.");

	// TASK-067 (patch 3): the collection is shared with `save_preserving_text()`
	// so the whole-file writer and the per-section publisher cannot publish
	// different sets.
	RBMap<String, List<String>> save_props;
	String save_features;
	const Error collect_error = _collect_settings_for_save(p_custom, p_merge_with_current, p_custom_features, save_props, save_features);
	if (collect_error != OK) {
		return collect_error;
	}

	if (p_path.ends_with(".godot") || p_path.ends_with("override.cfg")) {
		return _save_settings_text(p_path, save_props, p_custom, save_features);
	} else if (p_path.ends_with(".binary")) {
		return _save_settings_binary(p_path, save_props, p_custom, save_features);
	} else {
		ERR_FAIL_V_MSG(ERR_FILE_UNRECOGNIZED, vformat("Unknown config file format: '%s'.", p_path));
	}
}

// ---------------------------------------------------------------------------
// Section-granular publish (TASK-057 patch 2).
//
// The whole-file writer above cannot be used when the caller must keep the rest
// of the file: `_save_settings_text()` writes seven header comment lines plus
// every stored setting, so anything a human typed into `project.godot` that the
// engine did not produce - a comment, a blank line, the key order, a section the
// engine does not know about - is gone after one call. This is not a theory:
// TASK-042 / TASK-043 measured it for `project_set_setting` and five tool
// descriptions in modules/mcp_server now say so.
//
// Doing it in the caller instead was tried and rejected: the natural splice
// ("write the new line right after the `[input]` header") silently puts the key
// into the WRONG section when `[input]` is not the last section of the file,
// because the engine's reader (VariantParser -> ConfigFile::_parse) attributes
// every assignment to the section header that preceded it. The failure is
// silent: the file parses, the key is simply not where the writer thought.
//
// So the text work lives here, next to the serializer it has to agree with.
// ---------------------------------------------------------------------------

namespace {

// One statement of the file: a blank line, a comment, a section header, or an
// assignment. Only an assignment carries key and value spans.
	}

	return statements;
}

} // namespace

Error ProjectSettings::update_settings_section_text(const String &p_text, const String &p_section, const CustomMap &p_custom, String &r_result) {
	r_result = p_text;

	ERR_FAIL_COND_V_MSG(p_section.is_empty(), ERR_INVALID_PARAMETER,
			"A section-granular project settings publish needs a non-empty section name.");
	ERR_FAIL_COND_V_MSG(p_section.contains_char('[') || p_section.contains_char(']') || p_section.contains_char('\n') || p_section.contains_char('\r'), ERR_INVALID_PARAMETER,
			vformat("'%s' cannot name a project settings section.", p_section));

	// The values are serialized by the same writer `_save_settings_text()` uses,
	// so what lands in the file is byte for byte what a full save of that one
	// setting would have written (ConfigFile reads it back the same way).
	// `RBMap` keeps the requested names in a deterministic order, which is what
	// makes the appended block reproducible.
	RBMap<String, String> serialized;
	for (const KeyValue<String, Variant> &E : p_custom) {
		const String prefix = p_section + "/";
		ERR_FAIL_COND_V_MSG(!E.key.begins_with(prefix) || E.key.length() == prefix.length(), ERR_INVALID_PARAMETER,
				vformat("Setting '%s' does not belong to section '%s': a section publish takes full setting names ('%s<name>').", E.key, p_section, prefix));

		String written;
		ERR_FAIL_COND_V_MSG(VariantWriter::write_to_string(E.value, written, true) != OK, ERR_INVALID_DATA,
				vformat("Setting '%s' cannot be written as project settings text.", E.key));
		serialized[E.key.substr(prefix.length())] = written;
	}

	if (serialized.is_empty()) {
		return OK;
	}

	const Vector<_PSStatement> statements = _ps_scan(p_text);

	// The target section: its header statement, and the first statement after it
	// that is another header.
	int header_index = -1;
	for (int i = 0; i < statements.size(); i++) {
		if (!statements[i].header.is_empty() && statements[i].header == p_section) {
			header_index = i;
			break;
		}
	}
	int section_end = statements.size();
	if (header_index >= 0) {
		for (int i = header_index + 1; i < statements.size(); i++) {
			if (!statements[i].header.is_empty()) {
				section_end = i;
				break;
			}
		}
	}

	// Everything the section already has gets its VALUE span replaced (every
	// occurrence, so a hand-written duplicate cannot leave a later, different
	// value that wins on read). The key text and the rest of the line are copied
	// through, so a caller that writes the same value twice gets the same bytes.
	RBMap<String, String> pending;
	for (const KeyValue<String, String> &E : serialized) {
		pending[E.key] = E.value;
	}

	String out;
	int cursor = 0;
	for (int i = 0; i < statements.size(); i++) {
		const _PSStatement &statement = statements[i];
		if (statement.begin > cursor) {
			out += p_text.substr(cursor, statement.begin - cursor);
		}

		const bool in_section = header_index >= 0 && i > header_index && i < section_end;
		if (in_section && statement.is_assignment() && serialized.has(statement.key)) {
			const String &value = serialized[statement.key];
			pending.erase(statement.key);

			const String existing = p_text.substr(statement.value_begin, statement.value_end - statement.value_begin);
			if (existing != value) {
				out += p_text.substr(statement.begin, statement.key_begin - statement.begin);
				out += statement.key.property_name_encode();
				out += "=";
				out += value;
				out += p_text.substr(statement.value_end, statement.end - statement.value_end);
				cursor = statement.end;
				continue;
			}
		}

		out += p_text.substr(statement.begin, statement.end - statement.begin);
		cursor = statement.end;
	}
	if (cursor < p_text.length()) {
		out += p_text.substr(cursor);
	}

	if (!pending.is_empty()) {
		// The line ending this file uses, taken from the first statement that has
		// one, so a CRLF project keeps CRLF endings.
		String file_terminator = "\n";
		for (const _PSStatement &statement : statements) {
			if (!statement.terminator.is_empty()) {
				file_terminator = statement.terminator;
				break;
			}
		}

		if (header_index >= 0) {
			// Append after the last real line of the section, so the blank line
			// that separates the section from the next one stays where it was.
			// A multi-line serialized value is appended as one block.
			int anchor = header_index;
			for (int i = header_index + 1; i < section_end; i++) {
				if (!statements[i].is_blank && !statements[i].is_comment) {
					anchor = i;
				}
			}
			const int insert_at = statements[anchor].end;
			String block;
			if (insert_at > 0 && p_text[insert_at - 1] != '\n') {
				// The last line has no terminator yet; give it one so the new
				// setting starts on its own line.
				block += file_terminator;
			}
			for (const KeyValue<String, String> &E : pending) {
				block += E.key.property_name_encode() + "=" + E.value + file_terminator;
			}
			out = out.substr(0, insert_at) + block + out.substr(insert_at);
		} else {
			// The section does not exist: create it at the end of the file in the
			// shape `_save_settings_text()` writes (a blank line before the
			// header, a blank line after it, then one assignment per line).
			if (!out.is_empty() && !out.ends_with("\n")) {
				out += file_terminator;
			}
			if (!out.is_empty()) {
				out += file_terminator;
			}
			out += "[" + p_section + "]" + file_terminator;
			out += file_terminator;
			for (const KeyValue<String, String> &E : pending) {
				out += E.key.property_name_encode() + "=" + E.value + file_terminator;
			}
		}
	}

	r_result = out;
	return OK;
}

Error ProjectSettings::save_custom_section(const String &p_path, const String &p_section, const CustomMap &p_custom) {
	ERR_FAIL_COND_V_MSG(p_path.is_empty(), ERR_INVALID_PARAMETER, "Project settings section save path cannot be empty.");

	if (!FileAccess::exists(p_path)) {
		// This method publishes *into* a file; it never creates a project from
		// nothing, exactly like `load_custom()` refuses to invent one.
		return ERR_FILE_NOT_FOUND;
	}

	Error err = OK;
	Ref<FileAccess> reader = FileAccess::open(p_path, FileAccess::READ, &err);
	ERR_FAIL_COND_V_MSG(err != OK || reader.is_null(), err != OK ? err : ERR_CANT_OPEN, vformat("Couldn't read project settings from '%s'.", p_path));

	const uint64_t length = reader->get_length();
	// `append_utf8()` takes an `int`, so a file larger than that would be
	// truncated by the cast. Refusing is the only honest answer here; the
	// alternative - publishing a prefix of a project.godot - is silent data
			DirAccess::remove_absolute(p_path);
			result = DirAccess::rename_absolute(temp_path, p_path);
		}
	}

	if (result != OK) {
		if (!FileAccess::exists(p_path) && FileAccess::exists(backup_path)) {
			DirAccess::copy_absolute(backup_path, p_path);
		}
	}

	DirAccess::remove_absolute(backup_path);
	DirAccess::remove_absolute(temp_path);
	return result;
}

Error ProjectSettings::publish_settings_sections_text(const String &p_text, const Vector<String> &p_sections, const CustomMap &p_values, String &r_result) {
	r_result = p_text;
	for (const String &section : p_sections) {
		if (section.is_empty()) {
			// See `save_preserving_text()`: a sectionless key is a top-level
			// assignment of the file itself and has no section form.
			continue;
		}
		const String prefix = section + "/";
		CustomMap section_settings;
		for (const KeyValue<String, Variant> &E : p_values) {
			if (E.key.begins_with(prefix) && E.key.length() > prefix.length()) {
				section_settings[E.key] = E.value;
			}
		}
		if (section_settings.is_empty()) {
			continue;
		}
		String next;
		const Error update_error = update_settings_section_text(r_result, section, section_settings, next);
		if (update_error != OK) {
			return update_error;
		}
		r_result = next;
	}
	return OK;
}

Error ProjectSettings::save_custom_section(const String &p_path, const String &p_section, const CustomMap &p_custom) {
	ERR_FAIL_COND_V_MSG(p_path.is_empty(), ERR_INVALID_PARAMETER, "Project settings section save path cannot be empty.");

	if (!FileAccess::exists(p_path)) {
		// This method publishes *into* a file; it never creates a project from
		// nothing, exactly like `load_custom()` refuses to invent one.
		return ERR_FILE_NOT_FOUND;
	}

	String text;
	const Error read_error = _read_settings_text_file(p_path, text);
	if (read_error != OK) {
		return read_error;
	}

	String updated;
	const Error update_error = update_settings_section_text(text, p_section, p_custom, updated);
	if (update_error != OK) {
		return update_error;
	}
	if (updated == text) {
		// Nothing to say that the file does not already say. Returning here is
		// what keeps a repeat call from touching the file at all (the bytes and
		// the modification time both stay put).
		return OK;
	}

	return _publish_settings_text_file(p_path, updated);
}

// ---------------------------------------------------------------------------
// TASK-067 (patch 3): the editor's own save on open.
//
// Root cause of "opening the project in a windowed editor eats the comments in
// project.godot" (`editor/editor_node.cpp:1062-1072`, reached only when
// `cmdline_mode` is false - `editor_node.cpp:8479` sets it from
// `DisplayServer::get_name() == "headless"`, which is why `--import` and
// `--headless` never showed it): that call site used `save()`, i.e. the
// whole-file writer, which regenerates `project.godot` from the engine's own
// serializer - seven header comment lines plus every stored setting, and nothing
// a human typed.
//
// `save_preserving_text()` keeps the two things the call site actually wants -
// the settings of the editor's own state, and a fresh modification time (the
// project manager reads `project.godot`'s mtime as "last edited",
// `editor/project_manager/project_list.cpp:866-869`) - and publishes them
// section by section into the file that is there, copying every other byte
// through. It is the same rule the writing tools follow since TASK-057 patch 2.
// ---------------------------------------------------------------------------

Error ProjectSettings::save_preserving_text() {
	const String path = get_resource_path().path_join("project.godot");
	ERR_FAIL_COND_V_MSG(!FileAccess::exists(path), ERR_FILE_NOT_FOUND,
			vformat("There is no project settings file at '%s' to publish into.", path));

	// The same set `save()` would write: `save()` calls
	// `save_custom(path)` with an empty custom map and `p_merge_with_current`
	// true, so the rendering-API and `C#` feature entries `save_custom()`
	// recomputes are part of it and opening a project still persists them.
	RBMap<String, List<String>> save_props;
	String save_features;
	const Error collect_error = _collect_settings_for_save(CustomMap(), true, Vector<String>(), save_props, save_features);
	(void)save_features;
	if (collect_error != OK) {
		return collect_error;
	}

	String text;
	const Error read_error = _read_settings_text_file(path, text);
	if (read_error != OK) {
		return read_error;
	}

	String updated = text;
	{
		// The section order is `save_props`' order (an `RBMap` over section
		// names, so it is sorted and reproducible), and the values are the live
		// settings - the same ones `_save_settings_text()` would have serialized.
		Vector<String> sections;
		CustomMap values;
		for (const KeyValue<String, List<String>> &E : save_props) {
			if (E.key.is_empty()) {
				// A setting with no section is a top-level assignment of the file
				// itself: `_load_settings_text()` calls `set(assign, value)` for one
				// (`project_settings.cpp:1001-1002`). It can only have come from the
				// file, and this publish copies the file through byte for byte, so
				// there is nothing to publish for it. Section publishing has no form
				// for a sectionless key by construction -
				// `update_settings_section_text()` refuses an empty section name, and
				// `_save_settings_text()` writes such a key before the first header.
				continue;
			}
			sections.push_back(E.key);
			for (const String &name : E.value) {
				const String full = E.key + "/" + name;
				values[full] = get(full);
			}
		}
		const Error publish_error = publish_settings_sections_text(text, sections, values, updated);
		if (publish_error != OK) {
			return publish_error;
		}
	}

	// Always write, even when `updated == text`. The call site's stated purpose
	// is to mark the project as last modified, and the project manager reads that
	// timestamp as "the date the project was last edited"; the bytes written in
	// the unchanged case are the file's own bytes, so the comments survive either
	// way. `last_save_time` is refreshed exactly like `save()` does it, so the
	// editor's external-change check (`editor/editor_node.cpp:1627`) does not
	// report the write this call just made as somebody else's.
	const Error write_error = _publish_settings_text_file(path, updated);
	if (write_error != OK) {
		return write_error;
	}
	last_save_time = FileAccess::get_modified_time(path);