# ENGINE-PATCHES-TO-REAPPLY

TASK-079 (rebuild stage 2a) — the three engine-fork patches that lived in the deleted tree,
parked as **verbatim `git show` output** plus everything needed to replay them.  No patch was
applied to `rebuild\godot` in this stage: the applicability evidence in §5 comes from isolated
sandboxes under `work\patchdry\` and `work\patchdry2\`.

* generated: `2026-09-25 23:57:36`
* patch artifacts: `rebuild\patches\*.diff` (verbatim copies, sha256 below)
* baseline: `%%TEMP%%\audit002\tree` (09-22 full engine snapshot, no `.git`), copied to `rebuild\godot`
* source of the diff text: `%%TEMP%%\audit-engine\diff-patch{1,2,3}.txt`, written on 2026-09-25 by the
  TASK-069/070 audit of `git show <commit>`; these are the **STDOUT bytes of the real command**,
  not a reconstruction.  The text is also captured in the session transcripts
  (`staging\__payload-index\events-diff.jsonl`).

## 1. Baseline identity (what the patches must be applied to)

`rebuild\godot` inherits the audit002 baseline.  The five patched engine files are **pristine**
there — a symbol scan found **zero** occurrences of any patch symbol, so the baseline is the
pre-patch upstream state and the replay starts from a clean pre-image:

| file | baseline bytes | baseline sha256 | is_source_newer_than_assembly | update_settings_section_text | save_custom_section | save_preserving_text |
|---|---|---|---|---|---|---|
| `core/config/project_settings.cpp` | 75556 | `c76f85acfb214ddadf16cd08742eec5c73a20d6753843bcb33f5e552f745886c` | 0 | 0 | 0 | 0 |
| `core/config/project_settings.h` | 13295 | `1e4e7d6e24b559f6c27e6f6b02f21de68967bea0c226d25f4f6680a660a2d994` | 0 | 0 | 0 | 0 |
| `editor/editor_node.cpp` | 389353 | `8110094827f6d7da6209ad2e1c7f371f96f63307255300630b78803c70cd2321` | 0 | 0 | 0 | 0 |
| `modules/mono/csharp_script.cpp` | 86199 | `842199675aa4775830508b10d209bde494edd66786114776627548d41177d0db` | 0 | 0 | 0 | 0 |
| `modules/mono/csharp_script.h` | 20978 | `41fe4bdf644b6cdf1621d18ffcecb6deaa8447225764909e233630a5553cc5cd` | 0 | 0 | 0 | 0 |

## 2. Order, commands, expected result

Apply **strictly in order 1 -> 2 -> 3**, from the repository root (`rebuild\godot`), with `-p1`:

```powershell
$G = "C:\Users\wyl\AppData\Local\Temp\mcp-recovery\rebuild\godot"
$P = "C:\Users\wyl\AppData\Local\Temp\mcp-recovery\rebuild\patches"
foreach ($n in 1,2,3) {
  $f = Get-ChildItem $P -Filter ("patch" + $n + "-*.diff") | Select-Object -First 1
  git -C $G apply -p1 --whitespace=nowarn $f.FullName
  if ($LASTEXITCODE -ne 0) { throw ("patch " + $n + " failed: " + $f.Name) }
}
```

Dry-run first (`--check`) if you want a no-write rehearsal; the same command with `--check`
was used to produce §5.

## 3. Patch table

| # | commit | subject | artifact | bytes | sha256 | files | hunks | +/- |
|---|---|---|---|---|---|---|---|---|
| 1 | `5f3e7fb441` | mcp_server: TASK-055 - a real C# compile verdict (D112 engine patch + recorded build diagnostics) | `rebuild\patches\patch1-csharp-compile-verdict-5f3e7fb441.diff` | 5303 | `6b0ee95c2abde614a4ec0ed2e6e4b7eb00ee39a75ebddf3906737d43cda02353` | 2 | 3 | +40/-3 |
| 2 | `96f631addb` | mcp_server: TASK-057 three closures and engine patch 2 (ProjectSettings section publish) | `rebuild\patches\patch2-projectsettings-section-publish-96f631addb.diff` | 23683 | `70decff99a232fd5866f37cd8bd952ffa40afee8801d2bfc1eaa4b5be46b4c4c` | 2 | 4 | +483/-0 |
| 3 | `2f85141a74` | mcp_server: TASK-067 list the build's script languages, and publish project.godot by section on editor open | `rebuild\patches\patch3-save-preserving-text-2f85141a74.diff` | 20309 | `41867b2962fce8c764da13fe9812c8c67a2bba22c16be5923c0c53206a5fae7e` | 3 | 9 | +253/-28 |

New symbols, as *occurrences on added lines* of each diff:

* **patch 1**: `is_source_newer_than_assembly` x3
* **patch 2**: `update_settings_section_text` x3, `save_custom_section` x8, `_save_custom_section_bnd` x3
* **patch 3**: `save_preserving_text` x9

## 4. The patches, verbatim

### 4.1 patch 1 — `5f3e7fb441`

**C# compile verdict — CSharpScript::is_source_newer_than_assembly()**

* files touched: `modules/mono/csharp_script.cpp` (2 hunks), `modules/mono/csharp_script.h` (1 hunks)
* hunk headers:
  * `modules/mono/csharp_script.cpp`  @@ -2171,9 +2171,7 @@ bool CSharpScript::_update_exports(PlaceHolderScriptInstance *p_instance_to_upda
  * `modules/mono/csharp_script.cpp`  @@ -2620,6 +2618,25 @@ Error CSharpScript::reload(bool p_keep_state) {
  * `modules/mono/csharp_script.h`  @@ -273,6 +273,26 @@ public:
* dependency: none — applies to the pristine baseline

**Why it exists / contract.**

```text
The engine never had a C# compile verdict: `CSharpScript::reload()` returns OK
unconditionally and only looks the type up in the assembly that was already built, so the
module's validation tools had to answer `unverifiable` for every `.cs` file.  The patch adds
**one public read-only accessor**, `CSharpScript::is_source_newer_than_assembly()`, which lifts
the mtime comparison that `_update_exports()` already performs.  It changes **no** signature and
**no** existing semantics (`reload()` is byte-identical).
```

**Raw `git show` output (contains the commit message and the full hunks with their
pre-image context; this is the applicable text).**

```diff
commit 5f3e7fb441e8f31129ac5c8797bf2642d2884564
Author: starsliving <1620462725@qq.com>
Date:   Thu Sep 24 23:51:38 2026 +0800

    mcp_server: TASK-055 - a real C# compile verdict (D112 engine patch + recorded build diagnostics)
    
    The engine never had a C# compile verdict: `CSharpScript::reload()` returns OK
    unconditionally and only looks the type up in the assembly that was already
    built, so TASK-054 had to answer `unverifiable` for every `.cs` file.
    
    Engine patch (one public read-only accessor, no signature or semantic change):
    `CSharpScript::is_source_newer_than_assembly()` lifts the comparison
    `_update_exports()` already made for the editor's placeholders (source mtime vs
    the loaded project assembly) into a public API, and that call site now uses it.
    
    Module side: the already public `Script::is_script_valid()` plus that accessor
    answer "compiled / not compiled"; the project-level half comes from the per-file
    diagnostics `project_build_csharp` parses out of the `dotnet build` output it
    already captures and records (with the modification time each file had at that
    build, so an edited file expires its old diagnostic). `project_validate_script`
    and `project_validate_scripts` now answer `ok` / `invalid` + the compiler's own
    text / `not_compiled` (never `invalid` for "nothing built it"), with the same
    sentences from both tools; the non-mono answer is unchanged.
    
    Contract: 175 entries, only the two validate descriptions move
    (DESCRIPTION_OVERRIDES / ADDED_TOOLS, GENERATOR_VERSION 1.17.0). The plural
    response gains `not_compiled_count`; `count` stays the sum of its five counters.
    
    Evidence (docs/reports/evidence/task055, scripts/mcp055_*): a real Godot C#
    project built through the tool on a mono build (syntax error -> invalid with
    CS1519/CS1002 text, valid file -> ok, edited file -> not_compiled in the same
    payload), the plain build's -32000 unchanged byte for byte, and a pre/post
    comparison of 35 probes where every label outside the declared set is identical.

diff --git a/modules/mono/csharp_script.cpp b/modules/mono/csharp_script.cpp
index 2024ab2ca3..9a6c5eea91 100644
--- a/modules/mono/csharp_script.cpp
+++ b/modules/mono/csharp_script.cpp
@@ -2171,9 +2171,7 @@ bool CSharpScript::_update_exports(PlaceHolderScriptInstance *p_instance_to_upda
 				p_instance_to_update->update(propnames, values);
 			}
 		} else if (placeholders.size()) {
-			uint64_t script_modified_time = FileAccess::get_modified_time(get_path());
-			uint64_t last_valid_build_time = GDMono::get_singleton()->get_project_assembly_modified_time();
-			if (script_modified_time > last_valid_build_time) {
+			if (is_source_newer_than_assembly()) {
 				for (PlaceHolderScriptInstance *instance : placeholders) {
 					Object *owner = instance->get_owner();
 					if (owner->get_script_instance() == instance) {
@@ -2620,6 +2618,25 @@ Error CSharpScript::reload(bool p_keep_state) {
 	return OK;
 }
 
+bool CSharpScript::is_source_newer_than_assembly() const {
+	const String script_path = get_path();
+	if (script_path.is_empty()) {
+		return false;
+	}
+
+	const uint64_t script_modified_time = FileAccess::get_modified_time(script_path);
+	if (script_modified_time == 0) {
+		// The file cannot be read (it is gone): there is no newer source for
+		// the loaded assembly.
+		return false;
+	}
+
+	// Zero when no project assembly was ever built, which is what makes every
+	// readable source file "newer" than nothing.
+	const uint64_t last_valid_build_time = GDMono::get_singleton()->get_project_assembly_modified_time();
+	return script_modified_time > last_valid_build_time;
+}
+
 ScriptLanguage *CSharpScript::get_language() const {
 	return CSharpLanguage::get_singleton();
 }
diff --git a/modules/mono/csharp_script.h b/modules/mono/csharp_script.h
index a1cca8684d..76fd9a161f 100644
--- a/modules/mono/csharp_script.h
+++ b/modules/mono/csharp_script.h
@@ -273,6 +273,26 @@ public:
 		return type_info.is_abstract;
 	}
 
+	/**
+	 * Returns whether this script's source file has been modified after the
+	 * project assembly currently loaded in this process was built, i.e. whether
+	 * the assembly does not contain a build of the source as it is on disk.
+	 *
+	 * `reload()` cannot answer this: C# has no compiler on this side, `reload()`
+	 * only looks the type up in the assembly that was already built and returns
+	 * `OK` regardless (see its definition), so its return value is not a compile
+	 * verdict. A caller that has to tell "this file was changed after the last
+	 * successful build" apart from "this file does not compile" needs this
+	 * signal, which is why it is a public accessor rather than a local variable:
+	 * the editor already makes this comparison to decide whether a placeholder
+	 * has to be refreshed (see `_update_exports`), and the built-in MCP module
+	 * makes it to answer "has this file been compiled?" honestly.
+	 *
+	 * Returns `false` when the script has no path, or when its file cannot be
+	 * read: nothing can be newer than the loaded assembly then.
+	 */
+	bool is_source_newer_than_assembly() const;
+
 	bool inherits_script(const Ref<Script> &p_script) const override;
 
 	Ref<Script> get_base_script() const override;
```

### 4.2 patch 2 — `96f631addb`

**ProjectSettings section publish — update_settings_section_text() + save_custom_section()**

* files touched: `core/config/project_settings.cpp` (2 hunks), `core/config/project_settings.h` (2 hunks)
* hunk headers:
  * `core/config/project_settings.cpp`  @@ -1340,6 +1340,450 @@ Error ProjectSettings::save_custom(const String &p_path, const CustomMap &p_cust
  * `core/config/project_settings.cpp`  @@ -1655,6 +2099,10 @@ void ProjectSettings::_bind_methods() {
  * `core/config/project_settings.h`  @@ -137,6 +137,7 @@ protected:
  * `core/config/project_settings.h`  @@ -204,6 +205,40 @@ public:
* dependency: none in the strict sense (its context does not need patch 1) — but the historical order is 1 -> 2 -> 3

**Why it exists / contract.**

```text
`ProjectSettings::save_custom()` / `_save_settings_text()` can only rewrite the whole
file, so the module had to do text surgery on `project.godot` (nine recorded risks, R1-R9).  The
patch adds a **section-scoped write path**: `update_settings_section_text()` serialises exactly
one section through the *same* `VariantWriter` the full writer uses, and `save_custom_section()`
writes it back while copying every other byte through — comments, key order, BOM
(re-added `EF BB BF`), and CRLF are preserved verbatim.  Pure addition, `+483/-0`, no existing
behaviour touched; ClassDB binding included.
```

**Raw `git show` output (contains the commit message and the full hunks with their
pre-image context; this is the applicable text).**

```diff
commit 96f631addb193b1c23eee821e9ee18d564b96d54
Author: starsliving <1620462725@qq.com>
Date:   Fri Sep 25 01:50:45 2026 +0800

    mcp_server: TASK-057 three closures and engine patch 2 (ProjectSettings section publish)
    
    D-B1: scripts/mcp057_build_mono.cmd records the mono build this project never wrote down (module_mono_enabled=yes tests=yes, stale test and mcp_trace objects deleted, log in C:\Users\wyl\AppData\Local\Temp).
    
    R-B2: docs/tool-groups-added.json gets a machine readable source.generator_version and check_tool_groups.py asserts it, GENERATOR_VERSION and _meta.generator_version are one string (new --generator-version mode); mcp057_rb2_failure_demo.ps1 drifts each of the three in turn and shows exit != 0 plus a byte exact restore.
    
    R-B3: scripts/mcp_evidence_guard.ps1 snapshots the working tree, and the 15 step battery now writes its own logs to C:\Users\wyl\AppData\Local\Temp, restores every tracked evidence file it overwrote, deletes what it created, prints the manifest and fails if git diff --stat is not empty.
    
    Engine patch 2: ProjectSettings::update_settings_section_text() and save_custom_section() publish one section and copy every other byte through - comments, key order, BOM and CRLF included. The scanner walks characters, not lines, because the engine serializes a non-empty Dictionary over several lines (variant_parser.cpp:2187-2201) and a line based reader leaves the value body behind. Existing writers and all 175 tools keep their declared behaviour; nothing is switched to the new path in this batch.

diff --git a/core/config/project_settings.cpp b/core/config/project_settings.cpp
index 0cc88cba71..4cc40e3ae1 100644
--- a/core/config/project_settings.cpp
+++ b/core/config/project_settings.cpp
@@ -1340,6 +1340,450 @@ Error ProjectSettings::save_custom(const String &p_path, const CustomMap &p_cust
 	}
 }
 
+// ---------------------------------------------------------------------------
+// Section-granular publish (TASK-057 patch 2).
+//
+// The whole-file writer above cannot be used when the caller must keep the rest
+// of the file: `_save_settings_text()` writes seven header comment lines plus
+// every stored setting, so anything a human typed into `project.godot` that the
+// engine did not produce - a comment, a blank line, the key order, a section the
+// engine does not know about - is gone after one call. This is not a theory:
+// TASK-042 / TASK-043 measured it for `project_set_setting` and five tool
+// descriptions in modules/mcp_server now say so.
+//
+// Doing it in the caller instead was tried and rejected: the natural splice
+// ("write the new line right after the `[input]` header") silently puts the key
+// into the WRONG section when `[input]` is not the last section of the file,
+// because the engine's reader (VariantParser -> ConfigFile::_parse) attributes
+// every assignment to the section header that preceded it. The failure is
+// silent: the file parses, the key is simply not where the writer thought.
+//
+// So the text work lives here, next to the serializer it has to agree with.
+// ---------------------------------------------------------------------------
+
+namespace {
+
+// One statement of the file: a blank line, a comment, a section header, or an
+// assignment. Only an assignment carries key and value spans.
+//
+// Why this is not line based (it was, and that was a real defect): the engine's
+// own serializer writes a non-empty `Dictionary` as SEVERAL lines
+//
+//     jump={
+//     "deadzone": 0.5,
+//     "events": []
+//     }
+//
+// (`variant_parser.cpp:2187-2201`, and the input actions of every real
+// project.godot look like this). A line-based scanner reads `jump={` as a
+// complete assignment whose value is `{`; the next call then sees a different
+// value, rewrites that one line and leaves the dictionary's remaining lines
+// behind - the file ends up with the body of the value twice. The scanner below
+// therefore finds the VALUE SPAN by walking the characters: it tracks brace,
+// bracket and parenthesis depth and whether it is inside a string, and the value
+// ends at the first newline seen at depth zero outside a string.
+struct _PSStatement {
+	int begin = 0; // First character of the statement's first line.
+	int end = 0; // One past the statement's last line terminator.
+	int key_begin = -1; // Assignment only; the key's first character.
+	int key_end = -1; // Assignment only; one past the key's last character.
+	int value_begin = -1; // Assignment only; the value's first character.
+	int value_end = -1; // Assignment only; one past the value's last character.
+	String key; // The decoded name of an assignment, empty otherwise.
+	String header; // The section an assignment belongs to the header of.
+	String terminator; // The line ending that closes the statement, or "".
+	bool is_blank = false;
+	bool is_comment = false;
+
+	bool is_assignment() const { return key_begin >= 0; }
+};
+
+String _ps_terminator_at(const String &p_text, int p_newline) {
+	return (p_newline > 0 && p_text[p_newline - 1] == '\r') ? String("\r\n") : String("\n");
+}
+
+// The name a key was written under. `_save_settings_text()` writes names through
+// `String::property_name_encode()`, which quotes anything containing `=`, `"`,
+// `;`, `[`, `]`, a space or a non-ASCII character, so a quoted key has to be
+// unescaped before it can be compared with the setting name.
+String _ps_decode_key(const String &p_key) {
+	if (p_key.length() >= 2 && p_key[0] == '"' && p_key[p_key.length() - 1] == '"') {
+		return p_key.substr(1, p_key.length() - 2).c_unescape();
+	}
+	return p_key;
+}
+
+Vector<_PSStatement> _ps_scan(const String &p_text) {
+	const int length = p_text.length();
+	Vector<_PSStatement> statements;
+
+	int i = 0;
+	while (i < length) {
+		_PSStatement statement;
+		statement.begin = i;
+
+		int first = i;
+		while (first < length && (p_text[first] == ' ' || p_text[first] == '\t')) {
+			first++;
+		}
+
+		int line_end = first;
+		while (line_end < length && p_text[line_end] != '\n') {
+			line_end++;
+		}
+		const bool has_newline = line_end < length;
+		const String line_terminator = has_newline ? _ps_terminator_at(p_text, line_end) : String();
+		const bool line_is_empty = (first >= length) || p_text[first] == '\n' || p_text[first] == '\r';
+
+		if (line_is_empty || p_text[first] == ';' || p_text[first] == '#') {
+			statement.is_blank = line_is_empty;
+			statement.is_comment = !line_is_empty;
+			statement.terminator = line_terminator;
+			statement.end = has_newline ? line_end + 1 : length;
+			statements.push_back(statement);
+			i = statement.end;
+			continue;
+		}
+
+		if (p_text[first] == '[') {
+			const int close = p_text.find_char(']', first);
+			if (close > first && close < line_end) {
+				statement.header = p_text.substr(first + 1, close - first - 1).strip_edges();
+				statement.terminator = line_terminator;
+				statement.end = has_newline ? line_end + 1 : length;
+				statements.push_back(statement);
+				i = statement.end;
+				continue;
+			}
+		}
+
+		int equals = -1;
+		for (int k = first; k < line_end; k++) {
+			if (p_text[k] == '=') {
+				equals = k;
+				break;
+			}
+		}
+		if (equals < first + 1) {
+			// Neither a header nor an assignment: the reader would not see a
+			// setting here either, so the line is carried through untouched.
+			statement.terminator = line_terminator;
+			statement.end = has_newline ? line_end + 1 : length;
+			statements.push_back(statement);
+			i = statement.end;
+			continue;
+		}
+
+		int key_end = equals;
+		while (key_end > first && (p_text[key_end - 1] == ' ' || p_text[key_end - 1] == '\t')) {
+			key_end--;
+		}
+
+		int value_begin = equals + 1;
+		while (value_begin < length && (p_text[value_begin] == ' ' || p_text[value_begin] == '\t')) {
+			value_begin++;
+		}
+
+		int cursor = value_begin;
+		int depth = 0;
+		bool in_string = false;
+		bool escaped = false;
+		while (cursor < length) {
+			const char32_t c = p_text[cursor];
+			if (in_string) {
+				if (escaped) {
+					escaped = false;
+				} else if (c == '\\') {
+					escaped = true;
+				} else if (c == '"') {
+					in_string = false;
+				}
+			} else if (c == '"') {
+				in_string = true;
+			} else if (c == '{' || c == '[' || c == '(') {
+				depth++;
+			} else if (c == '}' || c == ']' || c == ')') {
+				depth--;
+			} else if (c == '\n' && depth <= 0) {
+				break;
+			}
+			cursor++;
+		}
+
+		int value_end = cursor;
+		while (value_end > value_begin && (p_text[value_end - 1] == ' ' || p_text[value_end - 1] == '\t' || p_text[value_end - 1] == '\r')) {
+			value_end--;
+		}
+
+		statement.key_begin = first;
+		statement.key_end = key_end;
+		statement.value_begin = value_begin;
+		statement.value_end = value_end;
+		statement.key = _ps_decode_key(p_text.substr(first, key_end - first));
+		// The statement ends on the line the VALUE ends on, which for a
+		// serialized dictionary is several lines below the key.
+		const bool value_has_newline = cursor < length;
+		statement.terminator = value_has_newline ? _ps_terminator_at(p_text, cursor) : String();
+		statement.end = value_has_newline ? cursor + 1 : length;
+		statements.push_back(statement);
+		i = statement.end;
+	}
+
+	return statements;
+}
+
+} // namespace
+
+Error ProjectSettings::update_settings_section_text(const String &p_text, const String &p_section, const CustomMap &p_custom, String &r_result) {
+	r_result = p_text;
+
+	ERR_FAIL_COND_V_MSG(p_section.is_empty(), ERR_INVALID_PARAMETER,
+			"A section-granular project settings publish needs a non-empty section name.");
+	ERR_FAIL_COND_V_MSG(p_section.contains_char('[') || p_section.contains_char(']') || p_section.contains_char('\n') || p_section.contains_char('\r'), ERR_INVALID_PARAMETER,
+			vformat("'%s' cannot name a project settings section.", p_section));
+
+	// The values are serialized by the same writer `_save_settings_text()` uses,
+	// so what lands in the file is byte for byte what a full save of that one
+	// setting would have written (ConfigFile reads it back the same way).
+	// `RBMap` keeps the requested names in a deterministic order, which is what
+	// makes the appended block reproducible.
+	RBMap<String, String> serialized;
+	for (const KeyValue<String, Variant> &E : p_custom) {
+		const String prefix = p_section + "/";
+		ERR_FAIL_COND_V_MSG(!E.key.begins_with(prefix) || E.key.length() == prefix.length(), ERR_INVALID_PARAMETER,
+				vformat("Setting '%s' does not belong to section '%s': a section publish takes full setting names ('%s<name>').", E.key, p_section, prefix));
+
+		String written;
+		ERR_FAIL_COND_V_MSG(VariantWriter::write_to_string(E.value, written, true) != OK, ERR_INVALID_DATA,
+				vformat("Setting '%s' cannot be written as project settings text.", E.key));
+		serialized[E.key.substr(prefix.length())] = written;
+	}
+
+	if (serialized.is_empty()) {
+		return OK;
+	}
+
+	const Vector<_PSStatement> statements = _ps_scan(p_text);
+
+	// The target section: its header statement, and the first statement after it
+	// that is another header.
+	int header_index = -1;
+	for (int i = 0; i < statements.size(); i++) {
+		if (!statements[i].header.is_empty() && statements[i].header == p_section) {
+			header_index = i;
+			break;
+		}
+	}
+	int section_end = statements.size();
+	if (header_index >= 0) {
+		for (int i = header_index + 1; i < statements.size(); i++) {
+			if (!statements[i].header.is_empty()) {
+				section_end = i;
+				break;
+			}
+		}
+	}
+
+	// Everything the section already has gets its VALUE span replaced (every
+	// occurrence, so a hand-written duplicate cannot leave a later, different
+	// value that wins on read). The key text and the rest of the line are copied
+	// through, so a caller that writes the same value twice gets the same bytes.
+	RBMap<String, String> pending;
+	for (const KeyValue<String, String> &E : serialized) {
+		pending[E.key] = E.value;
+	}
+
+	String out;
+	int cursor = 0;
+	for (int i = 0; i < statements.size(); i++) {
+		const _PSStatement &statement = statements[i];
+		if (statement.begin > cursor) {
+			out += p_text.substr(cursor, statement.begin - cursor);
+		}
+
+		const bool in_section = header_index >= 0 && i > header_index && i < section_end;
+		if (in_section && statement.is_assignment() && serialized.has(statement.key)) {
+			const String &value = serialized[statement.key];
+			pending.erase(statement.key);
+
+			const String existing = p_text.substr(statement.value_begin, statement.value_end - statement.value_begin);
+			if (existing != value) {
+				out += p_text.substr(statement.begin, statement.key_begin - statement.begin);
+				out += statement.key.property_name_encode();
+				out += "=";
+				out += value;
+				out += p_text.substr(statement.value_end, statement.end - statement.value_end);
+				cursor = statement.end;
+				continue;
+			}
+		}
+
+		out += p_text.substr(statement.begin, statement.end - statement.begin);
+		cursor = statement.end;
+	}
+	if (cursor < p_text.length()) {
+		out += p_text.substr(cursor);
+	}
+
+	if (!pending.is_empty()) {
+		// The line ending this file uses, taken from the first statement that has
+		// one, so a CRLF project keeps CRLF endings.
+		String file_terminator = "\n";
+		for (const _PSStatement &statement : statements) {
+			if (!statement.terminator.is_empty()) {
+				file_terminator = statement.terminator;
+				break;
+			}
+		}
+
+		if (header_index >= 0) {
+			// Append after the last real line of the section, so the blank line
+			// that separates the section from the next one stays where it was.
+			// A multi-line serialized value is appended as one block.
+			int anchor = header_index;
+			for (int i = header_index + 1; i < section_end; i++) {
+				if (!statements[i].is_blank && !statements[i].is_comment) {
+					anchor = i;
+				}
+			}
+			const int insert_at = statements[anchor].end;
+			String block;
+			if (insert_at > 0 && p_text[insert_at - 1] != '\n') {
+				// The last line has no terminator yet; give it one so the new
+				// setting starts on its own line.
+				block += file_terminator;
+			}
+			for (const KeyValue<String, String> &E : pending) {
+				block += E.key.property_name_encode() + "=" + E.value + file_terminator;
+			}
+			out = out.substr(0, insert_at) + block + out.substr(insert_at);
+		} else {
+			// The section does not exist: create it at the end of the file in the
+			// shape `_save_settings_text()` writes (a blank line before the
+			// header, a blank line after it, then one assignment per line).
+			if (!out.is_empty() && !out.ends_with("\n")) {
+				out += file_terminator;
+			}
+			if (!out.is_empty()) {
+				out += file_terminator;
+			}
+			out += "[" + p_section + "]" + file_terminator;
+			out += file_terminator;
+			for (const KeyValue<String, String> &E : pending) {
+				out += E.key.property_name_encode() + "=" + E.value + file_terminator;
+			}
+		}
+	}
+
+	r_result = out;
+	return OK;
+}
+
+Error ProjectSettings::save_custom_section(const String &p_path, const String &p_section, const CustomMap &p_custom) {
+	ERR_FAIL_COND_V_MSG(p_path.is_empty(), ERR_INVALID_PARAMETER, "Project settings section save path cannot be empty.");
+
+	if (!FileAccess::exists(p_path)) {
+		// This method publishes *into* a file; it never creates a project from
+		// nothing, exactly like `load_custom()` refuses to invent one.
+		return ERR_FILE_NOT_FOUND;
+	}
+
+	Error err = OK;
+	Ref<FileAccess> reader = FileAccess::open(p_path, FileAccess::READ, &err);
+	ERR_FAIL_COND_V_MSG(err != OK || reader.is_null(), err != OK ? err : ERR_CANT_OPEN, vformat("Couldn't read project settings from '%s'.", p_path));
+
+	const uint64_t length = reader->get_length();
+	// `append_utf8()` takes an `int`, so a file larger than that would be
+	// truncated by the cast. Refusing is the only honest answer here; the
+	// alternative - publishing a prefix of a project.godot - is silent data
+	// loss. (This is a new narrowing site, so it is named and gated rather than
+	// left implicit: TASK-057 report section 5.)
+	ERR_FAIL_COND_V_MSG(length > (uint64_t)INT32_MAX, ERR_OUT_OF_MEMORY,
+			vformat("'%s' is too large to be published section by section (size %d bytes).", p_path, (int64_t)length));
+	Vector<uint8_t> raw;
+	raw.resize(length + 1);
+	const uint64_t read = length > 0 ? reader->get_buffer(raw.ptrw(), length) : 0;
+	raw.write[length] = 0;
+	reader->close();
+	if (read != length) {
+		return ERR_FILE_CANT_READ;
+	}
+
+	// A UTF-8 BOM is not part of the engine's String: `append_utf8()` skips it
+	// and `String::utf8()` writes it back only if the character is really there.
+	// It is therefore put back into the text explicitly - measured, not assumed:
+	// an unqualified read-modify-write through `get_as_text()`/`store_string()`
+	// removes the BOM from a file that had one.
+	String text;
+	if (length >= 3 && raw[0] == 0xEF && raw[1] == 0xBB && raw[2] == 0xBF) {
+		text = String::chr(0xFEFF);
+	}
+	text.append_utf8((const char *)raw.ptr(), (int)length);
+
+	String updated;
+	const Error update_error = update_settings_section_text(text, p_section, p_custom, updated);
+	if (update_error != OK) {
+		return update_error;
+	}
+	if (updated == text) {
+		// Nothing to say that the file does not already say. Returning here is
+		// what keeps a repeat call from touching the file at all (the bytes and
+		// the modification time both stay put).
+		return OK;
+	}
+
+	// The destination is replaced the way the rest of this code base replaces a
+	// file it must not destroy: write a sibling, keep a backup, publish, roll
+	// back if the publish fails.
+	const String temp_path = p_path + ".section_tmp";
+	const String backup_path = p_path + ".section_bak";
+
+	const Error backup_error = DirAccess::copy_absolute(p_path, backup_path);
+	if (backup_error != OK) {
+		return backup_error;
+	}
+
+	Error result = OK;
+	Ref<FileAccess> writer = FileAccess::open(temp_path, FileAccess::WRITE, &err);
+	if (err != OK || writer.is_null()) {
+		result = err != OK ? err : ERR_CANT_CREATE;
+	} else {
+		const CharString bytes = updated.utf8();
+		writer->store_buffer((const uint8_t *)bytes.get_data(), bytes.length());
+		writer->close();
+
+		if (!FileAccess::exists(temp_path)) {
+			result = FAILED;
+		} else if (updated.utf8().length() != FileAccess::get_file_as_bytes(temp_path).size()) {
+			// The writer reported success; the file is the only thing that
+			// proves the bytes really landed (a store_buffer that ran out of
+			// space returns without an error).
+			result = FAILED;
+		} else {
+			DirAccess::remove_absolute(p_path);
+			result = DirAccess::rename_absolute(temp_path, p_path);
+		}
+	}
+
+	if (result != OK) {
+		if (!FileAccess::exists(p_path) && FileAccess::exists(backup_path)) {
+			DirAccess::copy_absolute(backup_path, p_path);
+		}
+	}
+
+	DirAccess::remove_absolute(backup_path);
+	DirAccess::remove_absolute(temp_path);
+	return result;
+}
+
+Error ProjectSettings::_save_custom_section_bnd(const String &p_path, const String &p_section, const Dictionary &p_settings) {
+	CustomMap custom;
+	for (const KeyValue<Variant, Variant> &E : p_settings) {
+		custom[E.key] = E.value;
+	}
+	return save_custom_section(p_path, p_section, custom);
+}
+
 Variant _GLOBAL_DEF(const String &p_var, const Variant &p_default, bool p_restart_if_changed, bool p_ignore_value_in_docs, bool p_basic, bool p_internal) {
 	Variant ret;
 	if (!ProjectSettings::get_singleton()->has_setting(p_var)) {
@@ -1655,6 +2099,10 @@ void ProjectSettings::_bind_methods() {
 
 	ClassDB::bind_method(D_METHOD("save_custom", "file"), &ProjectSettings::_save_custom_bnd);
 
+	// TASK-057 patch 2: the section-granular publish (see the header for why a
+	// caller that must keep the rest of the file cannot use `save_custom()`).
+	ClassDB::bind_method(D_METHOD("save_custom_section", "path", "section", "settings"), &ProjectSettings::_save_custom_section_bnd);
+
 	// Change tracking methods
 	ClassDB::bind_method(D_METHOD("get_changed_settings"), &ProjectSettings::get_changed_settings);
 	ClassDB::bind_method(D_METHOD("check_changed_settings_in_group", "setting_prefix"), &ProjectSettings::check_changed_settings_in_group);
diff --git a/core/config/project_settings.h b/core/config/project_settings.h
index 1e5c6f1138..c4ba285132 100644
--- a/core/config/project_settings.h
+++ b/core/config/project_settings.h
@@ -137,6 +137,7 @@ protected:
 	Error _save_settings_binary(const String &p_file, const RBMap<String, List<String>> &p_props, const CustomMap &p_custom = CustomMap(), const String &p_custom_features = String());
 
 	Error _save_custom_bnd(const String &p_file);
+	Error _save_custom_section_bnd(const String &p_path, const String &p_section, const Dictionary &p_settings);
 
 #ifdef TOOLS_ENABLED
 	const static PackedStringArray _get_supported_features();
@@ -204,6 +205,40 @@ public:
 	Error load_custom(const String &p_path);
 	Error save_custom(const String &p_path = "", const CustomMap &p_custom = CustomMap(), const Vector<String> &p_custom_features = Vector<String>(), bool p_merge_with_current = true);
 	Error save();
+
+	// A section-granular publish, for callers that must not rewrite the rest of
+	// the file. `save_custom()` -> `_save_settings_text()` writes the header
+	// comment plus every stored setting, so a caller that only wants to add one
+	// `input/<action>` entry has to accept that the whole `project.godot` is
+	// regenerated and every hand written comment in it is lost. Editing the text
+	// from the caller side instead is not a way out either: the obvious
+	// "insert the line after the `[input]` header" splice has a silent failure
+	// when that section is not the last one, because the engine's own reader
+	// attributes a key to the section that precedes it.
+	//
+	// `save_custom_section()` moves that text handling into the engine - the
+	// engine serializes the target section with the same `VariantWriter` call
+	// `_save_settings_text()` uses - and rewrites **only that section**. Every
+	// other byte of the file is copied through untouched: comments, blank lines,
+	// key order, a UTF-8 BOM and CRLF line endings included. Keys the section
+	// already has are updated in place, new keys are appended to the section
+	// (never to the wrong one), and a section that does not exist yet is created
+	// at the end of the file in the shape `_save_settings_text()` writes. Keys
+	// that are not named are never touched and never removed.
+	//
+	// Neither method changes the in-memory settings: they publish text into a
+	// file, exactly like `save_custom()` does.
+	//
+	// `p_custom` is keyed by the **full** setting name (`"input/jump"`), and every
+	// key must belong to `p_section` - the part before the first `/`. The name
+	// inside the section may itself contain `/` (`rendering/renderer/...` is
+	// stored under `[rendering]`), which is why only the first separator splits.
+	Error save_custom_section(const String &p_path, const String &p_section, const CustomMap &p_custom);
+	// The text half of `save_custom_section()`, without any I/O, so the exact
+	// byte behaviour can be exercised on a string. `p_text` is the file as the
+	// engine decodes it (a UTF-8 BOM, if the caller put one in, is ordinary
+	// content of the first line and is therefore preserved).
+	static Error update_settings_section_text(const String &p_text, const String &p_section, const CustomMap &p_custom, String &r_result);
 	void set_custom_property_info(const PropertyInfo &p_info);
 	const HashMap<StringName, PropertyInfo> &get_custom_property_info() const;
 	uint64_t get_last_saved_time() { return last_save_time; }
```

### 4.3 patch 3 — `2f85141a74`

**save_preserving_text() + the editor-open call site (project_settings.cpp/.h, editor_node.cpp)**

* files touched: `core/config/project_settings.cpp` (6 hunks), `core/config/project_settings.h` (2 hunks), `editor/editor_node.cpp` (1 hunks)
* hunk headers:
  * `core/config/project_settings.cpp`  @@ -1231,9 +1231,12 @@ bool _csproj_exists(const String &p_root_dir) {
  * `core/config/project_settings.cpp`  @@ -1331,6 +1334,24 @@ Error ProjectSettings::save_custom(const String &p_path, const CustomMap &p_cust
  * `core/config/project_settings.cpp`  @@ -1679,14 +1700,19 @@ Error ProjectSettings::update_settings_section_text(const String &p_text, const
  * `core/config/project_settings.cpp`  @@ -1714,24 +1740,14 @@ Error ProjectSettings::save_custom_section(const String &p_path, const String &p
  * `core/config/project_settings.cpp`  @@ -1743,18 +1759,19 @@ Error ProjectSettings::save_custom_section(const String &p_path, const String &p
  * `core/config/project_settings.cpp`  @@ -1776,6 +1793,153 @@ Error ProjectSettings::save_custom_section(const String &p_path, const String &p
  * `core/config/project_settings.h`  @@ -136,6 +136,19 @@ protected:
  * `core/config/project_settings.h`  @@ -234,11 +247,41 @@ public:
  * `editor/editor_node.cpp`  @@ -1068,7 +1068,25 @@ void EditorNode::_notification(int p_what) {
* dependency: **REQUIRES patch 2** — its `project_settings.cpp` hunk context contains `save_custom_section()`, which patch 2 introduces. Applied to a pristine baseline it fails with `patch does not apply` (see §5).

**Why it exists / contract.**

```text
`editor/editor_node.cpp` calls `ProjectSettings::save()` on editor open (the
`!cmdline_mode` branch that `--import` and `--headless` never reach).  That is the whole-file
writer, which regenerated `project.godot` and deleted every hand-written comment.  The patch adds
`ProjectSettings::save_preserving_text()` (publishing section by section through patch 2's
`update_settings_section_text()`) and repoints that one call site at it.  `save()`,
`save_custom()` and `save_custom_section()` keep their observable behaviour; the collection and
the two I/O halves of `save_custom_section()` are **extracted, not rewritten**.
```

**Raw `git show` output (contains the commit message and the full hunks with their
pre-image context; this is the applicable text).**

```diff
commit 2f85141a74f2ee18cb905168cd99aa886de8b95e
Author: starsliving <1620462725@qq.com>
Date:   Fri Sep 25 12:51:38 2026 +0800

    mcp_server: TASK-067 list the build's script languages, and publish project.godot by section on editor open
    
    F-066-1: project_list_scripts hardcoded .gd/.gdshader, so a Mono project with six readable .cs files answered count=0 while four of the module's own error messages told the caller to use it. The extension set is now derived from ScriptServer (the languages this build registered) plus .gdshader. Contract unchanged (176, d4e53b43840b...); no override needed.
    
    F-066-2: the editor's own save on open (editor/editor_node.cpp, the !cmdline_mode branch that --import and --headless never reach) called ProjectSettings::save(), i.e. the whole-file writer, which regenerated project.godot and deleted every hand-written comment. It now calls the new ProjectSettings::save_preserving_text(), which publishes the same settings section by section through patch 2's update_settings_section_text() and copies every other byte through. save()/save_custom()/save_custom_section() keep their observable behaviour; the collection and the two I/O halves of save_custom_section() are extracted, not rewritten.
    
    Tests: a throwaway ScriptLanguage makes the enumeration defect red in BOTH variants, and 17 assertions pin the multi-section publish (comments verbatim, [input] not last, idempotence, sectionless key).

diff --git a/core/config/project_settings.cpp b/core/config/project_settings.cpp
index 4cc40e3ae1..cac2117573 100644
--- a/core/config/project_settings.cpp
+++ b/core/config/project_settings.cpp
@@ -1231,9 +1231,12 @@ bool _csproj_exists(const String &p_root_dir) {
 }
 #endif // TOOLS_ENABLED
 
-Error ProjectSettings::save_custom(const String &p_path, const CustomMap &p_custom, const Vector<String> &p_custom_features, bool p_merge_with_current) {
-	ERR_FAIL_COND_V_MSG(p_path.is_empty(), ERR_INVALID_PARAMETER, "Project settings save path cannot be empty.");
-
+// TASK-067 (patch 3): the "which settings would a save write, grouped by
+// section" half of the whole-file writer, moved here unchanged so that
+// `save_preserving_text()` publishes **exactly** the set `save()` would publish.
+// Splitting it out is a pure extraction - every line below was already in
+// `save_custom()`, in the same order, with the same `_VCSort` ordering.
+Error ProjectSettings::_collect_settings_for_save(const CustomMap &p_custom, bool p_merge_with_current, const Vector<String> &p_custom_features, RBMap<String, List<String>> &r_props, String &r_features) {
 #ifdef TOOLS_ENABLED
 	PackedStringArray project_features = get_setting("application/config/features");
 	// If there is no feature list currently present, force one to generate.
@@ -1331,6 +1334,24 @@ Error ProjectSettings::save_custom(const String &p_path, const CustomMap &p_cust
 		save_features += f;
 	}
 
+	r_props = save_props;
+	r_features = save_features;
+	return OK;
+}
+
+Error ProjectSettings::save_custom(const String &p_path, const CustomMap &p_custom, const Vector<String> &p_custom_features, bool p_merge_with_current) {
+	ERR_FAIL_COND_V_MSG(p_path.is_empty(), ERR_INVALID_PARAMETER, "Project settings save path cannot be empty.");
+
+	// TASK-067 (patch 3): the collection is shared with `save_preserving_text()`
+	// so the whole-file writer and the per-section publisher cannot publish
+	// different sets.
+	RBMap<String, List<String>> save_props;
+	String save_features;
+	const Error collect_error = _collect_settings_for_save(p_custom, p_merge_with_current, p_custom_features, save_props, save_features);
+	if (collect_error != OK) {
+		return collect_error;
+	}
+
 	if (p_path.ends_with(".godot") || p_path.ends_with("override.cfg")) {
 		return _save_settings_text(p_path, save_props, p_custom, save_features);
 	} else if (p_path.ends_with(".binary")) {
@@ -1679,14 +1700,19 @@ Error ProjectSettings::update_settings_section_text(const String &p_text, const
 	return OK;
 }
 
-Error ProjectSettings::save_custom_section(const String &p_path, const String &p_section, const CustomMap &p_custom) {
-	ERR_FAIL_COND_V_MSG(p_path.is_empty(), ERR_INVALID_PARAMETER, "Project settings section save path cannot be empty.");
+// ---------------------------------------------------------------------------
+// TASK-067 (patch 3): the two I/O halves of the section publish.
+//
+// They are extracted from `save_custom_section()` so a whole-file publish can do
+// ONE read and ONE write instead of one pair per section, and so the read and
+// the write rule exist in exactly one place. The byte behaviour is unchanged:
+// the reader puts back the UTF-8 BOM that `append_utf8()` skips, and the writer
+// replaces the file through a sibling plus a backup and verifies the bytes it
+// claims to have written.
+// ---------------------------------------------------------------------------
 
-	if (!FileAccess::exists(p_path)) {
-		// This method publishes *into* a file; it never creates a project from
-		// nothing, exactly like `load_custom()` refuses to invent one.
-		return ERR_FILE_NOT_FOUND;
-	}
+Error ProjectSettings::_read_settings_text_file(const String &p_path, String &r_text) const {
+	r_text = String();
 
 	Error err = OK;
 	Ref<FileAccess> reader = FileAccess::open(p_path, FileAccess::READ, &err);
@@ -1714,24 +1740,14 @@ Error ProjectSettings::save_custom_section(const String &p_path, const String &p
 	// It is therefore put back into the text explicitly - measured, not assumed:
 	// an unqualified read-modify-write through `get_as_text()`/`store_string()`
 	// removes the BOM from a file that had one.
-	String text;
 	if (length >= 3 && raw[0] == 0xEF && raw[1] == 0xBB && raw[2] == 0xBF) {
-		text = String::chr(0xFEFF);
-	}
-	text.append_utf8((const char *)raw.ptr(), (int)length);
-
-	String updated;
-	const Error update_error = update_settings_section_text(text, p_section, p_custom, updated);
-	if (update_error != OK) {
-		return update_error;
-	}
-	if (updated == text) {
-		// Nothing to say that the file does not already say. Returning here is
-		// what keeps a repeat call from touching the file at all (the bytes and
-		// the modification time both stay put).
-		return OK;
+		r_text = String::chr(0xFEFF);
 	}
+	r_text.append_utf8((const char *)raw.ptr(), (int)length);
+	return OK;
+}
 
+Error ProjectSettings::_publish_settings_text_file(const String &p_path, const String &p_text) const {
 	// The destination is replaced the way the rest of this code base replaces a
 	// file it must not destroy: write a sibling, keep a backup, publish, roll
 	// back if the publish fails.
@@ -1743,18 +1759,19 @@ Error ProjectSettings::save_custom_section(const String &p_path, const String &p
 		return backup_error;
 	}
 
+	Error err = OK;
 	Error result = OK;
 	Ref<FileAccess> writer = FileAccess::open(temp_path, FileAccess::WRITE, &err);
 	if (err != OK || writer.is_null()) {
 		result = err != OK ? err : ERR_CANT_CREATE;
 	} else {
-		const CharString bytes = updated.utf8();
+		const CharString bytes = p_text.utf8();
 		writer->store_buffer((const uint8_t *)bytes.get_data(), bytes.length());
 		writer->close();
 
 		if (!FileAccess::exists(temp_path)) {
 			result = FAILED;
-		} else if (updated.utf8().length() != FileAccess::get_file_as_bytes(temp_path).size()) {
+		} else if (p_text.utf8().length() != FileAccess::get_file_as_bytes(temp_path).size()) {
 			// The writer reported success; the file is the only thing that
 			// proves the bytes really landed (a store_buffer that ran out of
 			// space returns without an error).
@@ -1776,6 +1793,153 @@ Error ProjectSettings::save_custom_section(const String &p_path, const String &p
 	return result;
 }
 
+Error ProjectSettings::publish_settings_sections_text(const String &p_text, const Vector<String> &p_sections, const CustomMap &p_values, String &r_result) {
+	r_result = p_text;
+	for (const String &section : p_sections) {
+		if (section.is_empty()) {
+			// See `save_preserving_text()`: a sectionless key is a top-level
+			// assignment of the file itself and has no section form.
+			continue;
+		}
+		const String prefix = section + "/";
+		CustomMap section_settings;
+		for (const KeyValue<String, Variant> &E : p_values) {
+			if (E.key.begins_with(prefix) && E.key.length() > prefix.length()) {
+				section_settings[E.key] = E.value;
+			}
+		}
+		if (section_settings.is_empty()) {
+			continue;
+		}
+		String next;
+		const Error update_error = update_settings_section_text(r_result, section, section_settings, next);
+		if (update_error != OK) {
+			return update_error;
+		}
+		r_result = next;
+	}
+	return OK;
+}
+
+Error ProjectSettings::save_custom_section(const String &p_path, const String &p_section, const CustomMap &p_custom) {
+	ERR_FAIL_COND_V_MSG(p_path.is_empty(), ERR_INVALID_PARAMETER, "Project settings section save path cannot be empty.");
+
+	if (!FileAccess::exists(p_path)) {
+		// This method publishes *into* a file; it never creates a project from
+		// nothing, exactly like `load_custom()` refuses to invent one.
+		return ERR_FILE_NOT_FOUND;
+	}
+
+	String text;
+	const Error read_error = _read_settings_text_file(p_path, text);
+	if (read_error != OK) {
+		return read_error;
+	}
+
+	String updated;
+	const Error update_error = update_settings_section_text(text, p_section, p_custom, updated);
+	if (update_error != OK) {
+		return update_error;
+	}
+	if (updated == text) {
+		// Nothing to say that the file does not already say. Returning here is
+		// what keeps a repeat call from touching the file at all (the bytes and
+		// the modification time both stay put).
+		return OK;
+	}
+
+	return _publish_settings_text_file(p_path, updated);
+}
+
+// ---------------------------------------------------------------------------
+// TASK-067 (patch 3): the editor's own save on open.
+//
+// Root cause of "opening the project in a windowed editor eats the comments in
+// project.godot" (`editor/editor_node.cpp:1062-1072`, reached only when
+// `cmdline_mode` is false - `editor_node.cpp:8479` sets it from
+// `DisplayServer::get_name() == "headless"`, which is why `--import` and
+// `--headless` never showed it): that call site used `save()`, i.e. the
+// whole-file writer, which regenerates `project.godot` from the engine's own
+// serializer - seven header comment lines plus every stored setting, and nothing
+// a human typed.
+//
+// `save_preserving_text()` keeps the two things the call site actually wants -
+// the settings of the editor's own state, and a fresh modification time (the
+// project manager reads `project.godot`'s mtime as "last edited",
+// `editor/project_manager/project_list.cpp:866-869`) - and publishes them
+// section by section into the file that is there, copying every other byte
+// through. It is the same rule the writing tools follow since TASK-057 patch 2.
+// ---------------------------------------------------------------------------
+
+Error ProjectSettings::save_preserving_text() {
+	const String path = get_resource_path().path_join("project.godot");
+	ERR_FAIL_COND_V_MSG(!FileAccess::exists(path), ERR_FILE_NOT_FOUND,
+			vformat("There is no project settings file at '%s' to publish into.", path));
+
+	// The same set `save()` would write: `save()` calls
+	// `save_custom(path)` with an empty custom map and `p_merge_with_current`
+	// true, so the rendering-API and `C#` feature entries `save_custom()`
+	// recomputes are part of it and opening a project still persists them.
+	RBMap<String, List<String>> save_props;
+	String save_features;
+	const Error collect_error = _collect_settings_for_save(CustomMap(), true, Vector<String>(), save_props, save_features);
+	(void)save_features;
+	if (collect_error != OK) {
+		return collect_error;
+	}
+
+	String text;
+	const Error read_error = _read_settings_text_file(path, text);
+	if (read_error != OK) {
+		return read_error;
+	}
+
+	String updated = text;
+	{
+		// The section order is `save_props`' order (an `RBMap` over section
+		// names, so it is sorted and reproducible), and the values are the live
+		// settings - the same ones `_save_settings_text()` would have serialized.
+		Vector<String> sections;
+		CustomMap values;
+		for (const KeyValue<String, List<String>> &E : save_props) {
+			if (E.key.is_empty()) {
+				// A setting with no section is a top-level assignment of the file
+				// itself: `_load_settings_text()` calls `set(assign, value)` for one
+				// (`project_settings.cpp:1001-1002`). It can only have come from the
+				// file, and this publish copies the file through byte for byte, so
+				// there is nothing to publish for it. Section publishing has no form
+				// for a sectionless key by construction -
+				// `update_settings_section_text()` refuses an empty section name, and
+				// `_save_settings_text()` writes such a key before the first header.
+				continue;
+			}
+			sections.push_back(E.key);
+			for (const String &name : E.value) {
+				const String full = E.key + "/" + name;
+				values[full] = get(full);
+			}
+		}
+		const Error publish_error = publish_settings_sections_text(text, sections, values, updated);
+		if (publish_error != OK) {
+			return publish_error;
+		}
+	}
+
+	// Always write, even when `updated == text`. The call site's stated purpose
+	// is to mark the project as last modified, and the project manager reads that
+	// timestamp as "the date the project was last edited"; the bytes written in
+	// the unchanged case are the file's own bytes, so the comments survive either
+	// way. `last_save_time` is refreshed exactly like `save()` does it, so the
+	// editor's external-change check (`editor/editor_node.cpp:1627`) does not
+	// report the write this call just made as somebody else's.
+	const Error write_error = _publish_settings_text_file(path, updated);
+	if (write_error != OK) {
+		return write_error;
+	}
+	last_save_time = FileAccess::get_modified_time(path);
+	return OK;
+}
+
 Error ProjectSettings::_save_custom_section_bnd(const String &p_path, const String &p_section, const Dictionary &p_settings) {
 	CustomMap custom;
 	for (const KeyValue<Variant, Variant> &E : p_settings) {
diff --git a/core/config/project_settings.h b/core/config/project_settings.h
index c4ba285132..36e447f844 100644
--- a/core/config/project_settings.h
+++ b/core/config/project_settings.h
@@ -136,6 +136,19 @@ protected:
 	Error _save_settings_text(const String &p_file, const RBMap<String, List<String>> &p_props, const CustomMap &p_custom = CustomMap(), const String &p_custom_features = String());
 	Error _save_settings_binary(const String &p_file, const RBMap<String, List<String>> &p_props, const CustomMap &p_custom = CustomMap(), const String &p_custom_features = String());
 
+	// TASK-067 (patch 3). The three pieces `save_custom()` and the section
+	// publish share, so the whole-file writer and the per-section writer cannot
+	// drift apart:
+	//   * `_collect_settings_for_save()` is the "which settings would a save
+	//     write, grouped by section" half of `save_custom()`;
+	//   * `_read_settings_text_file()` reads a settings file as the engine
+	//     decodes it, UTF-8 BOM included;
+	//   * `_publish_settings_text_file()` replaces it atomically (sibling,
+	//     backup, verify-bytes, rename, roll back).
+	Error _collect_settings_for_save(const CustomMap &p_custom, bool p_merge_with_current, const Vector<String> &p_custom_features, RBMap<String, List<String>> &r_props, String &r_features);
+	Error _read_settings_text_file(const String &p_path, String &r_text) const;
+	Error _publish_settings_text_file(const String &p_path, const String &p_text) const;
+
 	Error _save_custom_bnd(const String &p_file);
 	Error _save_custom_section_bnd(const String &p_path, const String &p_section, const Dictionary &p_settings);
 
@@ -234,11 +247,41 @@ public:
 	// inside the section may itself contain `/` (`rendering/renderer/...` is
 	// stored under `[rendering]`), which is why only the first separator splits.
 	Error save_custom_section(const String &p_path, const String &p_section, const CustomMap &p_custom);
+	// TASK-067 (patch 3). The editor's own "save the project on open" call
+	// (`editor/editor_node.cpp:1071`) - it must not be a different writer from the
+	// section publish, or the editor would preserve comments while every tool
+	// that writes one section does, and lose them the moment it opens the project
+	// itself.
+	//
+	// It publishes **the settings `save()` would publish** (the same collection
+	// `save_custom()` builds, section by section) into the file that is already
+	// there, and copies every other byte through: comments, blank lines, key
+	// order, a BOM and CRLF included. Unlike `save_custom_section()` it always
+	// writes the file - the call site's stated purpose is to mark the project as
+	// last modified (`editor/project_manager/project_list.cpp:866-869` reads that
+	// timestamp as "last edited") - and it refreshes `get_last_saved_time()`, so
+	// the editor's own external-change check
+	// (`editor/editor_node.cpp:1627`) does not fire on the write it just made.
+	//
+	// It does not create a project: a missing `project.godot` is
+	// `ERR_FILE_NOT_FOUND`, and the caller keeps `save()` for that (and for
+	// binary projects).
+	Error save_preserving_text();
 	// The text half of `save_custom_section()`, without any I/O, so the exact
 	// byte behaviour can be exercised on a string. `p_text` is the file as the
 	// engine decodes it (a UTF-8 BOM, if the caller put one in, is ordinary
 	// content of the first line and is therefore preserved).
 	static Error update_settings_section_text(const String &p_text, const String &p_section, const CustomMap &p_custom, String &r_result);
+	// TASK-067 (patch 3): the text half of `save_preserving_text()` - the same
+	// per-section publish, applied to every named section in one pass over the
+	// text (one read, one write, one rollback point instead of one per section).
+	// `p_values` is keyed by full setting name; a section takes the keys whose
+	// first `/`-separated part is its name, which is exactly the grouping
+	// `_save_settings_text()` writes. `p_sections` fixes the order, so the result
+	// is reproducible for a given input. It is static and free of I/O for the same
+	// reason `update_settings_section_text()` is: the byte behaviour can be
+	// exercised on a string without touching the running project's own file.
+	static Error publish_settings_sections_text(const String &p_text, const Vector<String> &p_sections, const CustomMap &p_values, String &r_result);
 	void set_custom_property_info(const PropertyInfo &p_info);
 	const HashMap<StringName, PropertyInfo> &get_custom_property_info() const;
 	uint64_t get_last_saved_time() { return last_save_time; }
diff --git a/editor/editor_node.cpp b/editor/editor_node.cpp
index fe1c5648ac..1ee0bda7a7 100644
--- a/editor/editor_node.cpp
+++ b/editor/editor_node.cpp
@@ -1068,7 +1068,25 @@ void EditorNode::_notification(int p_what) {
 						ProjectSettings::get_singleton()->set_setting(initial_setting.key, initial_setting.value);
 					}
 				}
-				ProjectSettings::get_singleton()->save();
+				// TASK-067 (patch 3). This used to be `save()`, which regenerates
+				// `project.godot` from the engine's own serializer - seven header
+				// comment lines plus every stored setting, and nothing a human
+				// typed. The result was that merely OPENING the project in a
+				// windowed editor deleted every hand written comment from it
+				// (`--import` and `--headless` never showed it: the
+				// `!cmdline_mode` guard above, set in the constructor from
+				// `DisplayServer::get_name() == "headless"`).
+				//
+				// `save_preserving_text()` publishes the same settings section by
+				// section and copies every other byte through, which is the rule
+				// the writing tools have followed since TASK-057 patch 2. A
+				// `project.godot` that does not exist yet (or a binary project)
+				// still needs `save()`, which is what creates it.
+				if (project_settings_path.is_empty() || !FileAccess::exists(project_settings_path)) {
+					ProjectSettings::get_singleton()->save();
+				} else {
+					ProjectSettings::get_singleton()->save_preserving_text();
+				}
 			}
 
 			_titlebar_resized();
```

## 5. Applicability evidence (isolated sandbox, `rebuild\godot` NOT modified)

Every run below used a sandbox holding copies of the five engine files taken from
`rebuild\godot`, so the tree itself is untouched.

| # | command | sandbox | exit | meaning |
|---|---|---|---|---|
| 1 | `git apply --check patch1` on pristine | `work\patchdry` | **0** | patch 1 applies to the baseline as-is |
| 2 | `git apply --check patch2` on pristine | `work\patchdry` | **0** | patch 2 applies to the baseline as-is |
| 3 | `git apply --check patch3` on pristine | `work\patchdry` | **1** | *expected*: context needs `save_custom_section()` from patch 2 |
| 4 | `git apply patch2` then `git apply --check patch3` | `work\patchdry` | 0 / **0** | patch 3 applies once patch 2 is in |
| 5 | `git apply patch1; patch2; patch3` in order | `work\patchdry2` | **0 / 0 / 0** | the whole replay is clean end to end |

The only failure text (row 3) is git searching for the patch-2 pre-image:

```text
error: while searching for:
    return OK;
}

Error ProjectSettings::save_custom_section(const String &p_path, const String &p_section, const CustomMap &p_custom) {
...
error: patch failed: core/config/project_settings.cpp:1679
error: core/config/project_settings.cpp: patch does not apply
```

Per-file state across the ordered replay in `work\patchdry2` (bytes / lines / sha256):

| file | pristine | after patch1 | after patch2 | after patch3 |
|---|---|---|---|---|
| `core/config/project_settings.cpp` | 75556 / 1628 / `c76f85acfb214ddadf16cd08742eec5c73a20d6753843bcb33f5e552f745886c` | 75556 / 1628 / `c76f85acfb214ddadf16cd08742eec5c73a20d6753843bcb33f5e552f745886c` | 95158 / 2027 / `daeb00777088b36cacf747bfb8d16b3ce4150bce9840314abef3e4ddfa1a3b04` | 102533 / 2178 / `e9c4f6fb143afcdd63939574e0067a4aff929ff47d2893b996da218415d05f68` |
| `core/config/project_settings.h` | 13295 / 238 / `1e4e7d6e24b559f6c27e6f6b02f21de68967bea0c226d25f4f6680a660a2d994` | 13295 / 238 / `1e4e7d6e24b559f6c27e6f6b02f21de68967bea0c226d25f4f6680a660a2d994` | 16043 / 272 / `9680b051cdb862a8b895bca3cf0228163390e9c32207279a2cfdd4e9c2d1daa1` | 19002 / 314 / `b8491ca81d1a8f8cdb986325812948e74406904614a0503704184452e19b7d79` |
| `editor/editor_node.cpp` | 389353 / 8343 / `8110094827f6d7da6209ad2e1c7f371f96f63307255300630b78803c70cd2321` | 389353 / 8343 / `8110094827f6d7da6209ad2e1c7f371f96f63307255300630b78803c70cd2321` | 389353 / 8343 / `8110094827f6d7da6209ad2e1c7f371f96f63307255300630b78803c70cd2321` | 400247 / 8361 / `699bfc817f99ce25cd45678cb3213dea203b49e1a85c4f4f54f7d1b597647ec8` |
| `modules/mono/csharp_script.cpp` | 86199 / 2228 / `842199675aa4775830508b10d209bde494edd66786114776627548d41177d0db` | 89504 / 2242 / `7fef858f8f51a177390f1a878591a4567943ce2b78965b599e47b04b85975eb8` | 89504 / 2242 / `7fef858f8f51a177390f1a878591a4567943ce2b78965b599e47b04b85975eb8` | 89504 / 2242 / `7fef858f8f51a177390f1a878591a4567943ce2b78965b599e47b04b85975eb8` |
| `modules/mono/csharp_script.h` | 20978 / 451 / `41fe4bdf644b6cdf1621d18ffcecb6deaa8447225764909e233630a5553cc5cd` | 22687 / 470 / `499bdbc4e2e8340125bc88e79065826da5753ee07da7070bf4ba58952ae16f0b` | 22687 / 470 / `499bdbc4e2e8340125bc88e79065826da5753ee07da7070bf4ba58952ae16f0b` | 22687 / 470 / `499bdbc4e2e8340125bc88e79065826da5753ee07da7070bf4ba58952ae16f0b` |

## 6. Post-replay acceptance check

After the three patches are applied, these symbols must be present (checked on the patched
sandbox; the counts are plain substring counts):

| file | is_source_newer_than_assembly | update_settings_section_text | save_custom_section | save_preserving_text |
|---|---|---|---|---|
| `core/config/project_settings.cpp` | 0 | 4 | 6 | 5 |
| `core/config/project_settings.h` | 0 | 2 | 5 | 2 |
| `editor/editor_node.cpp` | 0 | 0 | 0 | 2 |
| `modules/mono/csharp_script.cpp` | 2 | 0 | 0 | 0 |
| `modules/mono/csharp_script.h` | 1 | 0 | 0 | 0 |

And the sha256 of the five files must equal the "after patch3" column of §5.

## 7. What else the next stage needs

* The patches do **not** touch `modules/mcp_server/**`; the module side of patch 1 and patch 3
  (e.g. `tools/csharp_verdict.{h,cpp}`, `tools/project_read_files.cpp`, the doctests in
  `tests/test_mcp_server.h`) is *inside the module tree* and is still a **gap** — see
  `REBUILD-2A-MANIFEST.md` §gap table.
* `editor_node.cpp` in the baseline is 389,353 B / 8,343 lines; `git apply` matched its hunk
  exactly, so the baseline revision is compatible with the patch as recorded.
* Hand-written `project.godot` comment preservation (patch 2/3 behaviour) can only be observed
  with a **windowed** editor run (`-e --path <proj>`, no `--headless`); byte equality alone
  cannot distinguish "wrote but unchanged" from "never wrote" — compare **mtime** as well.
* No compilation (`scons`) was attempted in this stage.

## 8. Provenance summary

| item | value |
|---|---|
| diff text command 1 | `git show 5f3e7fb441 -- modules/mono/csharp_script.cpp modules/mono/csharp_script.h` |
| diff text command 2 | `git show 96f631addb -- core/config/project_settings.cpp core/config/project_settings.h` |
| diff text command 3 | `git show 2f85141a74 -- core/config/project_settings.cpp core/config/project_settings.h editor/editor_node.cpp` |
| captured stdout | `%TEMP%\audit-engine\diff-patch{1,2,3}.txt` (2026-09-25 16:06-16:07) |
| transcript cross-reference | `staging\__payload-index\events-diff.jsonl` rows for the same commands |
| decision log cross-reference | `F:\moonbit-hof-rs\DECISIONS.md` D113 (patch 1), D115 (patch 2), D125 (patch 3) |
| F: writes | none |
