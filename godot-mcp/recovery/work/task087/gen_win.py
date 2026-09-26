#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate docs/tools_list.renamed.json from the old contract + the rename map.

Spec source
-----------
* docs/DESIGN-DETAIL.md section 16 item 2 (the renamed contract is the reference
  artifact of every per-batch equality gate), GDR-16, GDR-17 and GDR-18.
* docs/B0-BRIEF.md section 2 (frozen task book for B0).
* docs/tool-rename-map.json is the single source of truth (174 entries).
* docs/tasks/TASK-001-rename-map-v1.1.md section 2.5.1 (the v1.1 map shape).

The transform is mechanical and idempotent:

  * `name`         <- the map's `new_name`;
  * `description`  <- the old contract object, carried over verbatim;
  * `inputSchema`  <- the old contract object, carried over verbatim;
  * top level `id` / `jsonrpc` are carried over from the old contract;
  * `disposition == "unregister_until_implemented"` entries are dropped (2);
  * `disposition == "merge_into"` entries are dropped (1), where the surviving
    entry is named by the entry's own `merge_target` field (= its `old_name`).
    v1.1 replaced the v1.0 inline `merge_into:<old_name>` form with that field
    (D-4), and GDR-17 cancelled two of the three v1.0 merges because they were
    lossy - the two de-merged tools now each keep their own, distinct name.

Expected output: 174 - 2 unregistered - 1 lossless merge == 171 tools.

`description` / `inputSchema` may only ever change through the explicit
DESCRIPTION_OVERRIDES / SCHEMA_OVERRIDES lists below (SCHEMA_OVERRIDES is still
empty, every entry must carry a `reason` that ends up in `_meta.overrides`).
Without such an entry, not a single character of those fields is allowed to move -
the script asserts that by re-serializing both objects and comparing.

v1.2 (TASK-002 section 2.1, audit risks R-1/R-2/R-3): DESCRIPTION_OVERRIDES is no
longer empty. Seven tools stay ambiguous "by name alone" because each pair shares
channel / verb / scope / mutating and differs only in the result shape, the hit
cap or the case sensitivity, so every one of them gets one inline discriminator
sentence. The discriminators are transcribed from the *migration source* (read,
not guessed): commands/project.rs, commands/batch.rs, commands/analysis.rs.
Each override is append-only (`<old description> + " " + <discriminator>`), which
the script enforces, so no original wording can be silently dropped. A stale
override (an `old_name` that never matches) is a hard failure as well.

v1.3 (TASK-003 section 1.1, decision D49/D-1): `_meta.order_normative = false`.
The *membership* and the *content* of `result.tools` are the contract; their
*order* is explicitly not. The engine still has to be deterministic (two
consecutive `tools/list` calls of one build must be byte-identical, see
DESIGN-DETAIL section 17.4 and the doctest
`[MCPServer] tools/list is byte-identical across consecutive calls`), but it is
free to differ from the order of this file. Nothing else in the transform
changed, so the two artifacts can be compared key by key.

v1.4 (TASK-007 section 1): an override record may carry `"mode": "replace"`.
Every override was append-only until then, which is the right default - but an
append cannot fix a sentence that is *factually wrong*: the reader would keep the
false statement in the field and have to reconcile it with the appended one.
`editor_analyze_signal_flow` is the first such case (its description claimed the
persistent test was `flags & 1`, which is `CONNECT_DEFERRED` in Godot 4 while the
implementation - correctly - tests `CONNECT_PERSIST`). A replacing override is
only accepted when its `reason` quotes the text it replaces verbatim, so the
original wording stays in `_meta.overrides` even though the field is rewritten;
append remains the default and every existing entry is unchanged.

v1.5 (TASK-014 section 1 D-3, decision D59 ruling 1 + the M2 acceptance): the
first `SCHEMA_OVERRIDES` entry, and the two rules that make a schema override
auditable. `running_game_play_input_recording` (old `replay_recording`) had
`inputSchema.required = ["events"]` while its implementation - correctly - lets
`events` be omitted and replays this game process' most recent recording instead
(D59 ruling 1). The contract was the side that lied, and the decision was to fix
the contract, not the behaviour, so the *only* edit is "remove `events` from
`required`" plus the description sentence that documents the fallback:

  * a schema override is always a **replacement** (there is no append for an
    object) and must therefore carry `"mode": "replace"`, like the factual
    correction of v1.4;
  * its `reason` has to quote the removed `required` member verbatim
    (`json.dumps(..., ensure_ascii=False)` of the old list), so the member that
    disappeared from the contract is still reconstructible from
    `_meta.overrides` - a reason that does not name what it deletes is refused.

The declared/fired override bookkeeping is now per `(kind, old_name)` instead of
per `old_name`: until v1.5 a single `old_name` could not carry both a description
and a schema override, because `declared_overrides` was the *union* of the two
tables and the count check compared it against one record per fired override.
Each table is still required to fire exactly once per declared name, and a
declared name that never fires is still a hard failure.

v1.6 (TASK-024a section 1 - the E-10 item, alone after the TASK-024 mid-flight
failure): the second `SCHEMA_OVERRIDES` entry, and a `DESCRIPTION_OVERRIDES`
entry for the *same* tool. `editor_play_scene` (old `play_scene`) now injects
`--mcp-port=<port>` into the game process it spawns
(`EditorRunBar::play_*(..., p_play_args)`; `EditorInterface::play_*` does not
forward run arguments, which is why the module stopped going through it). The
port becomes discoverable only if the schema carries it - hence the optional
`mcp_port` integer - and the fact that the child's port no longer comes from the
test project's `godot_mcp/port` setting has to be readable from the contract,
otherwise the tool would only have traded one undiscoverable rule for another.
That is the description entry, and it stays **append-only** (`运行场景` is still
its prefix). The schema entry is a replacement like v1.5's, with the same
obligation: its reason names the removed `required` member verbatim (here the
empty list - this tool never had a required parameter). Both mechanisms are
unchanged; only the tables grew.

v1.7 (TASK-029 - the follow-up the TASK-028 report asked the decision maker
for): `editor_get_test_report` (old `get_test_report`) declares
`"clear": {"default": true}` while its implementation has been an explicit
opt-in since TASK-028 G-3 - an omitted `clear` reads, and only `clear: true`
deletes anything. The bridge file it deletes is `user://mcp_test_report.json`
and it is **shared**: every client of the same editor process reads the same
one, so a default that deletes means the first reader takes the report away
from the next. The decision was to fix the contract, not the behaviour
("option A"), so the *only* edit is that one member's value - `true` -> `false`
- plus the sentence that names the shared file, and both are the third
`SCHEMA_OVERRIDES` entry and the second entry that is a *pair* with a
description override of the same tool. The mechanism is v1.6's unchanged:

  * the schema entry is a replacement (`"mode": "replace"`), and its `reason`
    quotes the removed `required` member verbatim (`[]`, this schema never had
    a required parameter) as the v1.5 guard demands. On top of that guard it
    quotes the member whose *value* it rewrites, verbatim:
    `"default": true` (the spelling in the emitted JSON). A value change is not
    covered by the machinery - the guard can only see the `required` list - so
    the quotation is what keeps the replaced declaration reconstructible from
    `_meta.overrides`. Every other character of the schema (`clear.description`
    = `是否清除结果`, the two `type`s) is carried over unchanged;
  * the description entry stays **append-only** (`获取测试结果报告` is still its
    prefix): the original wording was never wrong, it was just silent about the
    destructive half of `clear`, and a caller has to be able to see that from
    `tools/list` alone.

Standard library only (Python 3.9). No third party package is used anywhere.

v1.8 (TASK-032 D6, the second half of the M4d defect report): the seventh
`DESCRIPTION_OVERRIDES` entry, for `running_game_get_node_properties` (old
`get_game_node_properties`). Its family returns **SceneTree absolute** paths -
`running_game_get_scene_tree` answers `path = "/root/Main/Actor"` - while the
`node_path` description of the same family reads "relative to the scene root"
("节点路径（相对于场景根节点）"). Measured on 9889, both spellings are accepted on
the way in (an absolute `/root/...` path, a path relative to the current scene's
root, or a by-name walk), so the tool is usable - but a client that only reads
`tools/list` could not know that, and would have to guess whether one tool's
answer can be fed into the next. The entry is **append-only** (the original
`获取运行中游戏指定节点的属性` stays first, verbatim) and declares the shape the
tool really answers with plus both accepted input spellings. Nothing else of the
transform changed, and no other field of that entry moved.

v1.9 (TASK-034 section 0, the four schema gaps TASK-033 reported): the three
`SCHEMA_OVERRIDES` entries of the animation-tree family, all `mode=replace` and
all recorded in `_meta.overrides` with the `required` member they keep quoted
verbatim.

TASK-033 measured the opposite direction of the "declared but not delivered"
defect: `editor_add_state_machine_state` / `editor_set_blend_tree_node` read an
`animation` member (both the GDScript
`addons/godot_mcp_rs/commands/animation_tree_commands.gd:271,504` and the Rust
`godot_mcp_gdext/src/commands/animation_tree.rs`) that the contract never
declared, and `editor_add_state_machine_transition` could not reach
`AnimationNodeStateMachineTransition::set_xfade_time` / `set_priority` /
`set_advance_condition` at all - so a newly created Animation state could not be
pointed at an animation and a transition could not be given a cross-fade, a
priority or an advance condition by any tool. The tools now deliver those four
members; the contract is the side that was missing them, and it is corrected
through the mechanism `DESIGN-DETAIL` section 21.5 / 23.2 point 5 prescribes
(a schema override plus a reason that names what it touches), never by hand.

v1.10 (TASK-035 section 0, the declaration TASK-034 section 7.1 reported): the
fourth `SCHEMA_OVERRIDES` entry, `mode=replace`, for `editor_set_material_3d`
(old `set_material_3d`). The contract declared its `material_slot` as `string`
while the engine's API takes an integer surface index
(`MeshInstance3D::set_surface_override_material(int p_surface, ...)`,
`scene/3d/mesh_instance_3d.cpp:375`); a client that sends `0` was answered
"must be a string". The implementation's own `material_slot` grammar (a decimal
string) was a workaround for that declaration, not a behaviour worth keeping,
so the contract is corrected. It is a *value/type* change inside one property,
which the `required` guard cannot see, so - like v1.7 - the reason quotes the
replaced member verbatim (`"material_slot": {"type": "string"}`) as well as the
removed `required` member (`["node_path", "material_path"]`, kept unchanged).

v1.11 (TASK-043, the rewrite side effect TASK-042 section 3 measured): five
*description* overrides, all **append-only** (the original wording stays first,
verbatim), one sentence each, for the five tools that really do save the whole
`project.godot` through the engine's own writer. TASK-042 measured the effect on
a real, hand-commented `project.godot`: the engine rewrites the **entire** file,
writes its own seven-line header, drops every hand-written comment, re-emits the
other settings verbatim and is idempotent - and there is no partial-publish API
(`ProjectSettings::save_custom()` has one whole-file output; `ConfigFile::save()`
likewise). The side effect was silent, so the ruling is that the text a client
reads before calling has to carry it. The five tools are the ones confirmed from
the source, never guessed:

  * `set_project_setting` (project_set_setting) - `MCPTools::publish_project_settings()`
    (`tools/project_setting_write.cpp:218`);
  * `add_autoload` / `remove_autoload` (project_add_autoload /
    project_remove_autoload) - the same helper
    (`tools/project_autoload_write.cpp:150` / `:181`);
  * `set_input_action` (editor_add_input_action) - `MCPTools::persist_input_action()`
    -> `persist_input_action_to()` -> `publish_project_settings_to()`
    (`tools/editor_input_simulation.cpp:665`, `tools/tool_helpers.cpp:788-815`);
  * `reload_plugin` (editor_reload_plugin) - `EditorNode::set_addon_plugin_enabled(name, false, false)`
    / `(name, true, false)` (`tools/editor_write_scene_editor.cpp:396-397`) ends in
    `EditorNode::_update_addon_config()` (`editor/editor_node.cpp:4548` / `:4627`),
    which is **not** gated on `p_config_changed` and arms
    `ProjectSettingsEditor::queue_save()` (`editor/settings/project_settings_editor.cpp:97-99`,
    1.5 s one-shot timer -> `_save()` -> `ProjectSettings::save()`, `:102-106`).

The sentence is conditional ("when this call saves"), because three of the five
have paths that write nothing (`project_add_autoload` on an already-present
autoload, `editor_add_input_action` in a process without a `project.godot`,
`editor_reload_plugin` with no addon enabled). No `inputSchema` moves, no
parameter is added, and no other description changes: the five entries below are
the only diff of the transformed contract apart from `_meta`.

v1.12 (TASK-050 N-2, the honesty gap the racing-backlog audit recorded as N-2):
one **append-only** description override, for `project_validate_script` (old
`validate_script`). The tool resolved the file's language from its extension and
fell back to GDScript when that language was absent, so a legitimate `.cs` file in
a `module_mono_enabled=no` build was answered `{"error_text":"ERR_PARSE_ERROR",
"valid":false,"message":"Compilation failed. Check the script for errors."}` -
this build's missing C# backend was published as the file's compile failure. The
fallback is gone (a language the build does not contain is now a `-32000` refusal
with `data.suggestion`), and the sentence appended here is what tells a client
that `valid` is only ever a verdict of the file's **own** language. The original
`验证脚本语法` stays first, verbatim, and nothing but that one description and
`_meta` moves.

v1.13 (TASK-051, the B-tier `inputSchema` batch the racing-backlog audit
scheduled as C-3 / O-9 / O-4 / O-5 / M-3): **five `SCHEMA_OVERRIDES` entries,
all `mode=replace`** - the count of contract entries (171) does not move, only
five `inputSchema` objects do, so the whole batch is one contract regeneration
away from the authority. Each entry adds members only (no member that existed is
dropped or re-typed), and every reason quotes the `required` member it keeps
verbatim, as the v1.5 guard demands:

  * `batch_add_nodes` (`editor_add_nodes_batch`) gains the optional boolean
    `resolve_within_batch` (default `false`). The measured defect (audit §4.3,
    `editor_node_batch_write.cpp:251-258`): the parent path was resolved against
    the tree *as it was when the call arrived*, so `nodes[1].parent_path="P1"`
    with `P1` created by `nodes[0]` answered `-32001 nodes[1]: parent 'P1'` and
    rolled the whole request back. The schema is the only place a client can
    learn that the batch *can* build a subtree in one call;
  * `find_signal_connections` (`editor_list_signal_connections`) gains the
    optional enum string `scope` (`all` / `user` / `internal`, default `all`).
    The measured defect (audit §5.9): a 5-node scene with no hand-made
    connection of its own answered 60 of 60 connections and 12 659 B, all of them
    the editor's own `Class::method` wiring, and neither `node_path` nor
    `signal_name` can separate them (the `source` of an internal connection is an
    ordinary scene-node path). `scope` is an enum rather than a boolean so the
    `internal` half is expressible too, and its default is the pre-TASK-051
    answer. The `signal_name` substring filter is deliberately **not** changed -
    it is the frozen discriminator against `editor_analyze_signal_flow`
    (GDR-17 / R-1);
  * `simulate_input_sequence` (`editor_simulate_input_sequence`) gains the
    `events[].items` object schema. The measured defect (audit §5.4, `X11`):
    `{"type":"array"}` with no `items` meant a client could only learn the
    element shape - starting with the required `type` and its `enum` - by
    failing once (`-32602 "Missing required parameter: events[0].type"`);
  * `run_test_scenario` (`running_game_run_test_scenario`) gains
    `steps[].pressed` and `steps[].strength`, both of which the implementation
    has read since TASK-019 (`running_game_test_execution.cpp:141-148`) while the
    declaration named only nine of the eleven members (audit §5.5);
  * `play_scene` (`editor_play_scene`) gains `headless` (boolean, default false)
    and `extra_args` (array of strings, default `[]`). The measured defect
    (audit §3.3): the child's command line was `--path / --remote-debug /
    --editor-pid / --scene` plus this tool's own `--mcp-port=<port>`, so
    `--headless` - a routine CI need, and *not* inherited from the editor (it is
    absent from `Main::get_forwardable_cli_arguments(CLI_SCOPE_PROJECT)`) - could
    not be requested at all. `--mcp-port` inside `extra_args` is refused rather
    than appended, because `MCPPort::parse` takes the last occurrence and the
    answer's `endpoint` would then name a port the child is not listening on.

No `description` field moves in this version: every new meaning is carried by
the property it belongs to, which is also what a client reads in `tools/list`.

v1.8 (TASK-052, `DESIGN-DETAIL.md` section 26 / GDR-28 - "契约扩张：新增工具"):
the generator stops being a pure *rename + override* of the 174 old entries. The
decision maker may now author **new** tool entries, and they live in a third,
separate table:

  * `ADDED_TOOLS` is a list, not a dict keyed by `old_name`: a new entry has no
    old name to be keyed by, which is exactly what makes it a *new* entry rather
    than an override of a migrated one. It is therefore separate from both
    `DESCRIPTION_OVERRIDES` and `SCHEMA_OVERRIDES` (GDR-28 point 1), and the
    append happens **after** the rename + override pass, so an added entry can
    never be mistaken for a carried-over one;
  * the append is **deterministic**: the list's order is the output's order, the
    entry carries only `name` / `description` / `inputSchema` (the three fields
    of the contract), and the two name lists (`ported` vs `added`) are proved
    disjoint - a new name that collided with a ported or a dropped name is a
    hard failure;
  * the naming lint of GDR-16 is applied to an added name exactly as it is to a
    ported one (L1 pattern, L4 no `update_`, L2 verb inside the closed set,
    L3 channel and verb derived from the name itself, because there is no
    `tool-rename-map.json` row for a new tool);
  * `_meta` gains **`added_tools`** (the ordered list of names) and
    **`added_count`** (its length), and `_meta.count` stays `len(result.tools)`,
    so the contract's own `count` is `171 + N` from now on;
  * the transform is still idempotent: two runs of one build write byte-identical
    files (the same property the rename pass has always had).

Note what did **not** change: `result.tools` of the 171 ported entries is still a
byte-exact carry-over unless an override records the deviation, the frozen old
contract sha is still enforced, and `order_normative` is still false. The
machine checks that consume the two numbers are `check_tool_groups.py
--check-completeness` (`171 + N = 66 + 105 + N`, each name exactly once) and its
`--added` mode (which validates `docs/tool-groups-added.json`).

v1.16 (TASK-054, the C# honesty defect the audit's D-053-3 registered and
`DESIGN-DETAIL.md` section 26 / GDR-28 point 13 parked): **no entry is added and
no `inputSchema` moves** - the count stays 175 - but two `description` fields
stop over-promising about C#. `CSharpScript::reload()` returns `OK`
unconditionally (`modules/mono/csharp_script.cpp:2588-2621`) and never compiles
the source it was given, so in a Mono build a `.cs` file with a syntax error used
to be answered `{"valid": true, "message": "Script compiles successfully"}`
(measured: TASK-053 `c03`, and again by this task on the pre-change binary). The
single-file tool now refuses that file with `-32000` and the plural tool
classifies it `unverifiable` (no `valid` value, plus the engine basis in
`reason`), so both tools say the same thing:

  * `validate_script` (`project_validate_script`) gets one more **append-only**
    sentence - the v1.12 override already exists, so its original wording is
    untouched and this is a change to that entry's `value` and `reason`;
  * `project_validate_scripts` is an **added** entry (`ADDED_TOOLS`), which has no
    `old_name` and therefore no `DESCRIPTION_OVERRIDES` key: its description
    lives in the table the decision maker authored, and it is extended there. The
    four categories it publishes become five (`ok` / `invalid` /
    `language_unavailable` / `unverifiable`), which is why the sentence has to be
    in the field a client reads.

v1.17 (TASK-055, decision D112 - the engine patch that gives C# a real verdict):
**no entry is added and no `inputSchema` moves** - the count stays 175 - but the
two C# sentences TASK-054 added describe behaviour that no longer holds, so both
`description` fields are rewritten to what the tools now answer:

  * the engine patch is one public read-only accessor,
    `CSharpScript::is_source_newer_than_assembly()` (`modules/mono/csharp_script.h`,
    the comparison `CSharpScript::_update_exports()` already made for the editor's
    placeholders, exposed); together with the already public
    `Script::is_script_valid()` (`core/object/script_language.h:180`) it separates
    "the loaded assembly holds a build of this source" from "nothing compiled
    this source";
  * the project-level half of the verdict is recorded by this module's own build
    tool: `project_build_csharp` parses the compiler's diagnostics out of the
    output it already captures and writes them, with the modification time each
    file had at that build, to `user://mcp_csharp_build_state.json`. A diagnostic
    therefore expires the moment its file is edited, which is what keeps "it
    failed to compile" apart from "it was changed after that build";
  * `validate_script` (`project_validate_script`) gets one more **append-only**
    sentence - the v1.12 entry already exists, so this changes that entry's
    `value` and `reason`, and the TASK-054 sentence it used to end with (a `.cs`
    file gets no verdict here) is replaced because it is no longer true;
  * `project_validate_scripts` is an **added** entry, so its description is
    rewritten in `ADDED_TOOLS`: `unverifiable` stays for the residual "the engine
    could not load the file at all", `not_compiled` is new, and a sixth counter
    (`not_compiled_count`) joins the response.

Nothing else moves: 173 of the 175 entries are byte-identical, both `inputSchema`
objects are untouched, and the two validate tools publish the same verdict for
the same file.

v1.18 (TASK-059 D-4 - the sentence TASK-057 patch 2 falsified): **no entry is
added and no `inputSchema` moves** - the count stays 175 - but five `description`
fields stop claiming a missing capability. TASK-043 had appended, verbatim to all
five, a sentence containing `(the engine has no partial-publish API)` because at
the time that was true and the whole-file rewrite really did destroy every
hand-written comment. TASK-057 patch 2 added exactly that API -
`ProjectSettings::save_custom_section()` and `update_settings_section_text()`
(`core/config/project_settings.h:209-241`, `project_settings.cpp:1537-1779`) - and
TASK-057 deliberately did not switch any tool, reporting D-4 instead. This batch
switches the behaviour and the text **together**:

  * three of the five are genuinely single-section writes and now say so:
    `set_project_setting`, `set_input_action` (`editor_add_input_action`) and
    `add_autoload` (`project_add_autoload`). Their new text states the section
    rule, that comments and every other byte outside the target section survive,
    the four cases in which the whole file is still rewritten, and that this is a
    behaviour improvement (comments are no longer lost);
  * two are not, and their new text says why rather than claiming the capability:
    `remove_autoload` (`project_remove_autoload`) - the section writer replaces
    the values it is given and never deletes a key
    (`core/config/project_settings.h:226-227`), so a removal cannot be expressed
    as a section publish; and `reload_plugin` (`editor_reload_plugin`) - the save
    is the editor's own `ProjectSettingsEditor` settings-changed timer, not this
    module, so there is no section to name.

All five are `mode: "replace"`: the sentence being removed is factually wrong, and
an append-only discriminator would leave the false statement in the field a caller
reads - which is what `mode: "replace"` exists for (TASK-007). Every new value
still begins with the Chinese head of the old contract description, verbatim, and
every `reason` quotes both that head (the append-only guard's obligation) and the
false sentence it removes. The shared text of the three switched tools is one
module-level literal, so the three cannot drift apart. The four whole-file
fall-backs the new text names are the ones `tools/tool_helpers.h` documents and
`MCPTools::publish_project_setting_to()` implements case for case.

v1.19 (TASK-063 - the second round's four product defects): the count moves
**175 -> 176** (one new added tool) and five `description` fields move, three of
them because the text a caller reads was missing a rule that cost the round-2
developer 39 failed calls (TASK-060 D-5/O-2/O-3):

  * **one added entry**: `editor_set_node_property_updates` (the path-scoped
    batch property write; TASK-060 M-1/D-6 - only a *type*-scoped batch existed,
    so twenty geometry values cost twenty single writes). Its description,
    `inputSchema` and `reason` follow the TASK-052/TASK-053 shape;
  * **`update_property`** (`editor_set_node_property`) and
    **`get_node_properties`** (`editor_get_node_properties`) each get one
    **append-only** sentence built from one shared module-level literal
    (`NODE_PATH_RULE_SENTENCE`), so the two cannot drift apart. The parameter
    *names* do not move: `path` (singular) and `node_paths` (plural) stay, and
    what changes is that the text now states the path basis ("relative to the
    edited scene root", `/root/...` refused) and which of the two spellings takes
    one node and which takes many;
  * **`editor_set_node_script_batch`** (an added entry, so its description lives
    in `ADDED_TOOLS`) gets the plural half of the same sentence appended.

All three sentences are append-only (`mode` stays the default): the original
Chinese head of each ported description is preserved verbatim, which the
append-only guard checks character for character.

v1.20 (TASK-068 - the registered items of REPORT-067 section 7): the count and
every `inputSchema` stay exactly where v1.19 left them (**176 entries**), and
exactly two `description` fields move, both append-only, both because the text a
caller reads was silent about something the tool really does:

  * **`list_scripts`** (`project_list_scripts`) now states the walk's one
    observable consequence: it recurses from `res://` and skips only `.` and
    `..`, so the engine's own project cache comes back with the rest
    (`res://.godot/mono/temp/obj/**` on a Mono project) and filtering is the
    caller's job. TASK-067 made the script set a property of the build and
    deliberately did **not** narrow the walk (narrowing would break the pinned
    `.hiddendir/secret.gd` assertion; listing a generated file is honest), so
    the sentence is the declaration the decision owed (D125 (b), TASK-067
    deviation 5);
  * **`run_test_scenario`** (`running_game_run_test_scenario`) now says which of
    the two wait-related spellings is the input and which is the echo. The facts
# and a non-child bare name refused - but spell it two ways (`path` singular on
# `editor_set_node_property` / `editor_get_node_properties`, `node_paths` plural
# on `editor_set_node_script_batch`) and neither description stated the basis.
# The round-2 trace spent 20 single writes and 39 batch calls discovering a rule
# that belongs in the text a caller reads (`-32602 Unknown parameter 'node_path'`
    different members in two different objects, so nothing is renamed, no alias
    is added (an undeclared input would fail gate 1's verbatim schema
    comparison), and the R4 section 8.2 registration is closed by the text alone.

Neither sentence changes a byte of behaviour, and no `required` member moves, so
no `SCHEMA_OVERRIDES` record is touched by this version.

v1.21 (TASK-075 section 2 - the round-5 findings' M1/D3): the count moves
**176 -> 177** (one new added tool) and nothing else moves:

  * **one added entry**: `project_read_text_file`, the symmetric half of the
    module's own added `project_write_text_file`. The round-5 test's judgement
    table (PLATFORMER-FINDINGS section 0.6 (8)) asked for "write it, read it back
    and verify the sha256 - with a tool", and the loop could only be closed with an
    OS `Get-FileHash` call, because the contract had readers for scripts, scenes,
    resources and shaders but none for a plain project text file. Its description
    is the task's own sentence, verbatim.
"""

import argparse
import hashlib
import json
import os
import re
import sys

GENERATOR_VERSION = "1.21.0"
GENERATED_BY = "modules/mcp_server/scripts/gen_renamed_contract.py"

# ---------------------------------------------------------------------------
# TASK-063 (b): the node-path rule of the `editor_*` node tools, as ONE literal.
#
# The defect (TASK-060 D-5 / O-2 / O-3, measured): three tools of the same family
# require the same kind of path - relative to the edited scene root, `/root/...`
# and a non-child bare name refused - but spell it two ways (`path` singular on
# `editor_set_node_property` / `editor_get_node_properties`, `node_paths` plural
# on `editor_set_node_script_batch`) and neither description stated the basis.
# The round-2 trace spent 20 single writes and 39 batch calls discovering a rule
# that belongs in the text a caller reads (`-32602 Unknown parameter 'node_path'`
# first, then a bare `-32001` that only said "use editor_get_scene_tree").
#
# The parameter names stay: renaming `path` would invalidate the frozen evidence
# and every existing caller. What moves is the description, and the rule sentence
# is one literal so the three descriptions cannot drift apart.
#
# The engine basis for each clause (`tools/tool_helpers.cpp:1407-1424`,
# `MCPTools::find_node`, which is what all three tools resolve a path with):
#
#   * step 1 - `"."` or the edited scene root's own name is the root itself;
#   * step 2 - the path is resolved with `Node::has_node()` **relative to the
#     edited scene root** (`scene/main/node.cpp:2001` -> `get_node_or_null`,
#     which starts at `this` for a non-absolute NodePath);
#   * step 3 - a path prefixed with the root's own name is retried without it, so
#     `Main/Bricks/Car` and `Bricks/Car` name the same node;
#   * an **absolute** scene-tree path is not accepted in practice: the edited
#     scene is not the tree root's child in an editor process (it lives under the
#     editor's own container), which is the measured `-32001` of TASK-060 c4_s1
#     (`/root/Main/Bricks/Brick_r0_c0`).
# ---------------------------------------------------------------------------
NODE_PATH_RULE_SENTENCE = (
    "A node path here is resolved relative to the edited scene root and this parameter names ONE "
    "node (the plural tools spell the same strings as 'node_paths', an array: "
    "editor_set_node_script_batch and editor_set_node_property_updates): 'Bricks/Car' and "
    "'./Bricks/Car' address 'Car' inside 'Bricks', and the edited scene root's own name may be used "
    "as a prefix ('Main/Bricks/Car' == 'Bricks/Car' == './Bricks/Car'). An absolute scene-tree path "
    "('/root/Main/Bricks/Car') is not accepted, and a bare name such as 'Car' only addresses a direct "
    "child of the edited scene root. A refused path names this rule in data.suggestion."
)

# TASK-059 D-4 (v1.18): the sentence the three SWITCHED tools share. It is one
# literal so the three descriptions cannot drift apart, and it carries all three
# things TASK-059 section 1.2 requires: that a section write keeps comments and
# every other byte, when the whole file is still rewritten, and that the old
# comment loss is gone (a behaviour improvement). The argument behind it - the
# engine API, the four fall-backs and their source lines - is in the v1.18 note at
# the top of this file, in the table's TASK-059 block below, and in
# `tools/tool_helpers.h`.
_T059_SECTION_WRITE = (
    " This call publishes exactly one setting, and it does so section by section. When the key "
    "names a section - any name with a slash after its first character: input/jump belongs to "
    "[input], rendering/renderer/rendering_method to [rendering] - the write goes through the "
    "engine's own section-granular writer (ProjectSettings::save_custom_section), which replaces "
    "only that section's text and copies every other byte of project.godot through untouched: "
    "every hand-written comment, blank line, key order, UTF-8 BOM and CRLF line ending outside "
    "the target section is preserved byte for byte, and a repeated identical call changes no "
    "bytes (idempotent). This is a behaviour improvement: before TASK-059 every save rewrote the "
    "whole file with the engine's whole-file writer, which re-emits its own fixed header and "
    "every setting and so destroyed every hand-written comment in project.godot. The whole file "
    "is still rewritten that way, and those comments still lost, in four cases: the key names no "
    "section (no slash, or a leading one - such a key lives in the file's header-less global "
    "block, which has no section name to publish into); project.godot does not exist yet (the "
    "section writer publishes into a file and never creates one, while the whole-file writer "
    "does create it); the engine refuses the section write (it rejects a section name carrying a "
    "bracket or a line break, and a value it cannot serialize); or the file already carries this "
    "setting name in its header-less global block (a section write would leave a second home for "
    "it). Only the one named setting is written: settings the editor holds in memory but has not "
    "saved are no longer flushed as a side effect of this call."
)

# Explicit override hooks. SCHEMA_OVERRIDES was empty for B0/B1: the rename is
# name-only plus, from v1.2 on, the seven description disambiguations below.
# Any entry has to look like {"reason": "...", "value": <object>} and is recorded
# in `_meta.overrides` so that the deviation stays auditable.
#
# v1.5 (TASK-014 D-3): SCHEMA_OVERRIDES takes its first entry. A schema override
# is a whole-object *replacement* (there is nothing to append to), so it must
# carry `"mode": "replace"`, and its reason must quote the `required` member it
# removes verbatim - see the guard in `main`. No other character of the schema
# moves.
#
# v1.2: R-1/R-2/R-3 disambiguation (TASK-002 section 2.1.1). Each discriminator
# below is a *fact read out of the migration source*, never an invention; the
# line references are the ones already audited for tool-rename-map.json v1.1.
DESCRIPTION_OVERRIDES = {
    # R-1: editor_analyze_signal_flow vs editor_list_signal_connections.
    # analysis.rs:387-410 / analysis.rs:96-160 (nested nodes[], flags & 1, exact
    # node_path via had_node, no signal_name filter) against
    # batch.rs:207-263 (flat connections[], all connections, substring matches).
    "analyze_signal_flow": {
        "reason": (
            "R-1 消歧 + 事实纠正（TASK-007 §1）：原文按迁移源 analysis.rs:387 写成“只统计持久连接（flags & 1）”，"
            "但 Godot 4 里 CONNECT_DEFERRED = 1、CONNECT_PERSIST = 2（core/object/object.h:356-360），"
            "照字面实现会让普通 .tscn 场景恒返回 nodes: []。实现（TASK-006 已交付）按意图用了 CONNECT_PERSIST，"
            "契约描述是唯一还在说 flags & 1 的地方，故用 mode=replace 纠正。"
            "被替换的原文（逐字保留以便审计）："
            "分析当前场景的信号连接流 判别点：按节点嵌套返回 nodes[]（每节点含 signals_emitted/signals_connected_to），"
            "只统计持久连接（flags & 1）、node_path 精确匹配、无 signal_name 过滤；"
            "要扁平 connections[] 或子串匹配请用 editor_list_signal_connections。"
        ),
        "mode": "replace",
        "value": "分析当前场景的信号连接流 判别点：按节点嵌套返回 nodes[]（每节点含 signals_emitted/signals_connected_to），只收集持久连接（CONNECT_PERSIST，值为 2；注意 Godot 4 中 flags & 1 是 CONNECT_DEFERRED，不是持久连接）、node_path 精确匹配、无 signal_name 过滤；要扁平 connections[] 或子串匹配请用 editor_list_signal_connections。",
    },
    "find_signal_connections": {
        "reason": (
            "R-1 消歧：与 editor_analyze_signal_flow 形状/过滤/匹配方式不同（batch.rs:207 扁平 "
            "connections[]+count、不过滤非持久连接、node_path 与 signal_name 均子串匹配）。"
        ),
        "value": "递归查找场景中所有信号连接 判别点：扁平返回 connections[]（每项 {source,signal,target,method}）与 count，收全部连接（不过滤非持久连接）、node_path 与 signal_name 均按子串匹配；要按节点嵌套的流向分析请用 editor_analyze_signal_flow。",
    },
    # R-2: project_search_file_names vs project_search_file_contents.
    # project.rs:159-191 (file name substring, case insensitive, cap 200) against
    # project.rs:194-246 (per line, case insensitive, cap 50).
    "search_files": {
        "reason": (
            "R-2 消歧：search_files 只按文件名子串匹配（project.rs:175，大小写不敏感、上限 200，"
            "不读内容不返回行号），与 search_in_files 的逐行内容匹配完全不同。"
        ),
        "value": "搜索文件 判别点：只匹配文件名子串（大小写不敏感、上限 200），不读文件内容、不返回行号；要搜索文件内容请用 project_search_file_contents。",
    },
    "search_in_files": {
        "reason": (
            "R-2 消歧：search_in_files 逐行返回 {file,line,text}（project.rs:221-229，大小写不敏感、"
            "上限 50、跳过 addons 与 .godot），与 find_node_references 的按文件聚合不同。"
        ),
        "value": "在文件内容中搜索文本 判别点：逐行返回 {file,line,text}（大小写不敏感、上限 50，跳过 addons 与 .godot 目录）；要按文件聚合的 {file,lines[]}（大小写敏感、上限 100）请用 project_find_files_referencing_symbol。",
    },
    # R-2/R-3: project_find_files_referencing_symbol (batch.rs:419-512) is the
    # de-merged twin of project_search_file_contents (GDR-17).
    "find_node_references": {
        "reason": (
            "R-2 消歧：find_node_references 按文件聚合 {file,lines[]}（batch.rs:474-489，大小写敏感、"
            "上限 100、每文件最多 5 行），与 search_in_files 的逐行形状互为对照（GDR-17 取消合并）。"
        ),
        "value": "在项目文件中搜索指定模式的引用 判别点：按文件聚合返回 {file,lines[]}（每文件最多 5 行、大小写敏感、上限 100，跳过隐藏文件与 addons，只扫 .tscn/.gd/.tres/.gdshader）；要逐行 {file,line,text}（大小写不敏感、上限 50）请用 project_search_file_contents。",
    },
    # R-3: the two converts are a pure direction pair (project.rs:295-322).
    "uid_to_project_path": {
        "reason": (
            "R-3 消歧：uid_to_project_path 入参是文本 UID、出参 {uid,path}，UID 文本非法即报参数错误"
            "（project.rs:295-305），与反向转换项目路径->UID 是纯方向对。"
        ),
        "value": "将 UID 转换为项目路径 判别点：入参为字符串文本 UID（如 uid://...），返回 {uid,path}，UID 文本格式非法时报参数错误；反向转换请用 project_convert_path_to_uid。",
    },
    "project_path_to_uid": {
        "reason": (
            "R-3 消歧：project_path_to_uid 入参是项目路径、出参 {path,uid}，路径未注册时 uid 为空串且"
            "不报错（project.rs:308-322），与反向转换 UID->路径是纯方向对。"
        ),
        "value": "将项目路径转换为 UID 判别点：入参为项目路径（如 res://...），返回 {path,uid}，路径未注册时 uid 为空串且不报错；反向转换请用 project_convert_uid_to_path。",
    },
            "一个只读 tools/list 的智能体必须能看出这一点，故追加判别句。原文“获取测试结果报告”逐字保留在句首（append 模式）。"
        ),
        "value": "获取测试结果报告 缺省（不给 clear）或 clear:false 是纯读取：不改变、不删除任何东西，cleared 为空数组；只有显式 clear:true 才会清空，并且会删除**共享**的桥接文件 user://mcp_test_report.json —— 该文件由同一编辑器进程的所有客户端共用，删除后其它尚未读取该报告的客户端就读不到了（cleared 会列出真正被清掉的范围：editor_process / game_process_file）。",
    },
    # TASK-032 D6 (M4d): the returned `path` of the scene-tree family is the
    # *SceneTree* absolute path (`/root/Main/Actor`), while the `node_path`
    # description of the same family says "relative to the scene root". Both
    # spellings are accepted on the way in (the node resolver takes an absolute
    # `/root/...` path, a path relative to the current scene's root, or a
    # by-name walk), but a client that only reads the description could not know
    # that, and would have to guess how to feed one tool's answer into the next.
    # Append-only: the original wording stays first, verbatim.
    "get_game_node_properties": {
        "reason": (
            "TASK-032 D6 契约与行为一致（M4d 第四次独立验收）：running_game_get_scene_tree 实测返回 "
            "path=\"/root/Main/Actor\"（Node::get_path()，从 SceneTree 根 /root 起算的绝对路径），"
            "而同族 running_game_get_node_properties 的 node_path 描述写的是“相对于场景根节点”，"
            "只读 tools/list 的调用方看不出「绝对路径」也能喂回来。实测两种写法都能被解析"
            "（MCPTools::resolve_game_node：\"/root/...\" 走 SceneTree 根，其余先相对当前场景根解析、"
            "再退化为按名查找），故追加判别句声明实际返回形态。原文“获取运行中游戏指定节点的属性”逐字保留在句首（append 模式）。"
        ),
        "value": "获取运行中游戏指定节点的属性 返回的 path 是 SceneTree 绝对路径（形如 /root/Main/Actor，从 /root 起算，不是场景根相对路径）；node_path 两种写法都接受：相对场景根节点（如 Actor、A/B）或绝对路径（如 /root/Main/Actor），解析顺序是先绝对路径、再相对当前场景根、最后按节点名查找。",
    },
    # ------------------------------------------------------------------
    # TASK-043 (v1.11) appended the measured rewrite side effect to every tool
    # that really saves `project.godot`. TASK-059 D-4 (v1.18) rewrites the five
    # of them, because the sentence they share contains a claim the TASK-057
    # patch 2 engine API falsified: `(the engine has no partial-publish API)`.
    # The behaviour switch and the text are this batch's two halves, done
    # together: three tools moved to `save_custom_section()` and their text now
    # describes it, two could not move and their text says why.
    #
    # The replaced sentence, verbatim, in all five records:
    #   " When this call saves, it rewrites the entire project.godot with the
    #    engine's own whole-file writer (the engine has no partial-publish API),
    #    so every hand-written comment in that file is lost: the remaining
    #    settings are re-emitted verbatim and a repeated identical call changes
    #    no bytes (idempotent), and because the comments cannot be kept, back the
    #    file up yourself before calling if you need them."
    # (The parenthetical is the false part. The rest was true, and for the two
    # tools that did not move it is still true - which is why their new text keeps
    # the same statements instead of dropping them.)
    # ------------------------------------------------------------------
    "set_project_setting": {
        "reason": (
            "TASK-059 D-4（v1.18，mode=replace）：原文逐字为“设置项目设置”；被替换的整句含"
            "“（the engine has no partial-publish API）”，该断言已被 TASK-057 补丁 2 证伪——"
            "core/config/project_settings.h:209-241 声明、project_settings.cpp:1537-1779 实现的两个方法"
            "（update_settings_section_text / save_custom_section）正是“局部发布 API”。本批同时切换行为与描述："
            "project_set_setting 的写入路径由 tools/project_setting_write.cpp:218 的 publish_project_settings()"
            "改为 publish_project_setting()（tools/tool_helpers.cpp 的 publish_project_setting_to()），"
            "后者在键能唯一归节时走引擎的 save_custom_section()，只在四个明写的情形回退整文件重写"
            "（无节名的键 / project.godot 不存在 / 引擎拒绝节写 / 该名已在文件的无头全局块里，"
            "见 tools/tool_helpers.h 的完整论证）。新描述逐条说明：按节写入保留注释与其余文本；"
            "何时仍整文件重写；以及“现在不再丢注释”这一行为改善。原文“设置项目设置”逐字保留在句首（replace 模式，"
            "被替换文本已在 reason 中逐字引用以便审计）。"
        ),
        "mode": "replace",
        "value": "设置项目设置" + _T059_SECTION_WRITE,
    },
    "add_autoload": {
        "reason": (
            "TASK-059 D-4（v1.18，mode=replace）：原文逐字为“注册自动加载”；被替换的整句含"
            "“（the engine has no partial-publish API）”，已被 TASK-057 补丁 2 证伪（"
            "core/config/project_settings.h:209-241、project_settings.cpp:1537-1779）。本批同时切换行为与描述："
            "project_add_autoload 的写入路径由 tools/project_autoload_write.cpp 的 publish_project_settings()"
            "改为 publish_project_setting_to(target, key, ...)，键 autoload/<name> 唯一归节 [autoload]，"
            "走引擎的 save_custom_section()；四个整文件回退条件与 project_set_setting 相同（tools/tool_helpers.h）。"
            "新描述说明按节写入保留注释与其余文本、何时仍整文件重写、以及不再丢注释的行为改善；"
            "并保留原文已有的“同路径已存在则不写文件”的条件句义务（:121-135 的既存早退分支不变）。"
            "原文“注册自动加载”逐字保留在句首（replace 模式）。"
        ),
        "mode": "replace",
        "value": "注册自动加载" + _T059_SECTION_WRITE +
                 " A name that already declares the same path is answered without any save at all.",
    },
    "remove_autoload": {
        "reason": (
            "TASK-059 D-4（v1.18，mode=replace）：原文逐字为“移除自动加载”；被替换的整句含"
            "“（the engine has no partial-publish API）”，已被 TASK-057 补丁 2 证伪。但本工具的判定是"
            "**不切换**：新 API 是“按给出名字替换值”，从不删除键（core/config/project_settings.h:226-227 的契约注释，"
            "update_settings_section_text() 只替换已存在键的值跨度、只追加不存在的键），而本工具的全部工作就是删键"
            "（tools/project_autoload_write.cpp 的 settings->clear(key) -> publish_project_settings_to()）。"
            "把它改成按节写需要从内存重建整节 [autoload] 并重排其余条目的序列化形状、丢失节内手写注释、"
            "并新增“枚举命名空间构造 CustomMap”的辅助函数——对一个工具而言是真实且高风险的行为变更，不划算。"
            "因此它保留整文件重写，新描述**诚实**说明：为什么删除无法按节做、注释仍然会丢、"
            "以及它与已切换的 project_add_autoload 的差别。原文“移除自动加载”逐字保留在句首（replace 模式）。"
        ),
        "mode": "replace",
        "value": (
            "移除自动加载 This call removes one autoload setting, and this one cannot be done section by "
            "section. The engine's section-granular writer (ProjectSettings::save_custom_section) replaces the "
            "values of the names it is given and never deletes a key, so this tool deliberately keeps the "
            "engine's whole-file writer (ProjectSettings::save_custom). Every save therefore rewrites the "
            "entire project.godot: the file is regenerated out of the settings held in memory, the engine's "
            "own fixed header is written, and every hand-written comment in that file is lost - the remaining "
            "settings are re-emitted verbatim and a repeated identical call changes no bytes (idempotent), so "
            "back the file up yourself before calling if you need those comments. Together with "
            "editor_reload_plugin this is one of the two saves in this module that TASK-059 left on the "
            "whole-file writer; project_add_autoload did move to the section-granular path, and the pair "
            "differs for exactly this reason. A name the project does not declare is refused with an error "
            "and nothing is written."
        ),
    },
    "set_input_action": {
        "reason": (
            "TASK-059 D-4（v1.18，mode=replace）：原文逐字为“创建 Input Action”；被替换的整句含"
            "“（the engine has no partial-publish API）”，已被 TASK-057 补丁 2 证伪（"
            "core/config/project_settings.h:209-241、project_settings.cpp:1537-1779）。本批同时切换行为与描述："
            "editor_add_input_action 的持久化路径 tools/editor_input_simulation.cpp:665 persist_input_action() "
            "-> tools/tool_helpers.cpp persist_input_action() -> persist_input_action_to() 的发布一步"
            "由 publish_project_settings_to() 改为 publish_project_setting_to()，键 input/<action> 唯一归节 [input]，"
            "走引擎的 save_custom_section()；四个整文件回退条件见 tools/tool_helpers.h。"
            "新描述说明按节写入保留注释与其余文本、何时仍整文件重写、以及不再丢注释的行为改善；"
            "并保留“进程没有 project.godot 时只写内存、不写文件、游戏看不到”的既存条件句义务"
            "（persist_input_action() 的 :857-861 守卫不变）。原文“创建 Input Action”逐字保留在句首（replace 模式）。"
        ),
        "mode": "replace",
        "value": "创建 Input Action" + _T059_SECTION_WRITE +
                 " In a process with no project.godot the action is written to this process's InputMap only: "
                 "nothing is saved and no game can see it.",
    },
    "reload_plugin": {
        "reason": (
            "TASK-059 D-4（v1.18，mode=replace）：原文逐字为“重新加载 MCP 插件”；被替换的整句含"
            "“（the engine has no partial-publish API）”，已被 TASK-057 补丁 2 证伪。但本工具的判定是**不切换**："
            "它的保存不是本模块发出的——tools/editor_write_scene_editor.cpp 只调 "
            "EditorNode::set_addon_plugin_enabled(name, false/true, false)（p_config_changed=false），"
            "而 editor/editor_node.cpp 的 _update_addon_config() 不受该参数约束、无条件 queue_save()，"
            "由编辑器自己的 ProjectSettingsEditor 定时器 _save() -> ProjectSettings::save() -> save_custom() 整文件写。"
            "本模块既决定不了“要不要写”，也拿不到“写哪一节”，因此无节可命名（TASK-043 的 reason 已记录这条源码链与"
            "实测探针 scripts/mcp043_reload_plugin_rewrite_probe.ps1 的 14/14）。新描述改为点明“本工具自己不写文件、"
            "保存是编辑器的副作用”，并诚实保留注释会丢的陈述。原文“重新加载 MCP 插件”逐字保留在句首（replace 模式）。"
        ),
        "mode": "replace",
        "value": (
            "重新加载 MCP 插件 This tool does not write project.godot itself - the save is a side effect of "
            "the editor. Disabling and re-enabling an addon goes through "
            "EditorNode::set_addon_plugin_enabled, which refreshes editor_plugins/enabled in memory, and the "
            "editor's own ProjectSettingsEditor then flushes the whole project with ProjectSettings::save(), "
            "the engine's whole-file writer. When that save happens the entire project.godot is regenerated "
            "with the engine's own fixed header and every hand-written comment in that file is lost: the "
            "remaining settings are re-emitted verbatim and a repeated identical call changes no bytes "
            "(idempotent), so back the file up yourself before calling if you need those comments. This is "
            "one of the two saves in this module that TASK-059 left on the whole-file writer (with "
            "project_remove_autoload): the decision to write belongs to the editor's own settings-changed "
            "timer, not to this module, and that writer names no section. When no addon is enabled the tool "
            "refuses before touching anything and nothing is saved."
        ),
    },
    # v1.12 (TASK-050 N-2): `project_validate_script` resolved the file's language
    # from its extension and, when that language was absent, **fell back to
    # GDScript** - so a legitimate `.cs` in a `module_mono_enabled=no` build was
    # answered `{"error_text":"ERR_PARSE_ERROR","valid":false,"message":
    # "Compilation failed..."}`. "This build has no C# backend" was being
    # published as "your script does not compile", which is the honesty gap the
    # racing-backlog audit recorded as N-2 and TASK-050 removes: the fallback is
    # gone, a language this build does not contain is a `-32000` refusal carrying
    # `data.suggestion`, and `valid` is only ever a verdict produced by the file's
    # **own** language. The one place a caller can learn that is this description,
    # so the sentence is appended (the original `验证脚本语法` stays first,
    # verbatim - the append-only guard checks exactly that).
    "validate_script": {
        "reason": (
            "TASK-050 N-2 诚实性（决策者裁决；依据 racing-backlog 审计的 N-2 与我在 9888 上的独立复现）："
            "project_validate_script 原实现（project_read_files.cpp 旧 302-305 行）在 "
            "ScriptServer::get_language_for_extension(ext) 返回 null 时回退 GDScript，"
            "于是 module_mono_enabled=no 构建里的合法 .cs 得到 {\"error_text\":\"ERR_PARSE_ERROR\",\"valid\":false,"
            "\"message\":\"Compilation failed. Check the script for errors.\"} —— 把「本构建没有该语言的脚本后端」"
            "冒充成「编译失败」。改为能力感知：语言不可用 → -32000 + data.suggestion（说明用哪个构建/文件），"
            "valid 只在真的用该文件自身语言编译过时才是结论；进程没有任何脚本语言时仍走原有的结构检查降级分支（其 message 明说没有编译）。"
            "原文“验证脚本语法”逐字保留在句首（append 模式）。"
            "TASK-054（D-053-3）在同一句后追加一句：语言**存在**但该 API 不能编译其脚本的（C#，mono 构建）同样不给 valid —— "
            "CSharpScript::reload() 无条件返回 OK（modules/mono/csharp_script.cpp:2588-2621，函数体里唯一的 return 在 2620 行）"
            "且从不解析 set_source_code() 传入的源码；唯一真信号是私有字段 CSharpScript::valid（csharp_script.h:137，"
            "由 ScriptManagerBridge_AddScriptBridge 依「该脚本路径是否已在已加载的 .NET 程序集里」写入，"
            "csharp_script.cpp:2599 与 ScriptManagerBridge.cs:436-463），既无公开读取口、语义也是「这个类之前建过吗」"
            "而不是「这段源码能编译吗」。实测（TASK-053 c03/c05，本任务在改动前的 mono 二进制上再次复现）："
            "语法错误的 broken.cs 得到 category=ok、valid=true、message=\"Script compiles successfully\"。"
            "因此单数工具对该文件 -32000 + data.suggestion，批量工具分类 unverifiable（valid 为 null + reason），两边口径一致。"
            "TASK-055（D112，引擎补丁）**取代**上面那句「C# 没有结论」的措辞：用户已授权给引擎源码打补丁，"
            "补丁只有一处只读 API —— CSharpScript::is_source_newer_than_assembly()（modules/mono/csharp_script.h，"
            "把 CSharpScript::_update_exports() 里既有的「源文件 mtime > 已加载程序集 mtime」比较提升为公开访问器，"
            "并让该处复用它以保持单一事实源）；与**本来就公开**的 Script::is_script_valid()"
            "（core/object/script_language.h:180，CSharpScript 用同一个 valid 字段实现）合起来可把「已加载程序集里有这段源码的构建」"
            "与「没有任何构建编译过这段源码」分开。项目级那一半由本模块自己的构建工具记录："
            "project_build_csharp 从其已捕获的 stdout/stderr 里解析编译器诊断（tools/csharp_verdict.cpp 的 "
            "parse_csharp_build_errors），连**每个文件在构建那一刻的 mtime** 一起写入 user://mcp_csharp_build_state.json；"
            "于是「该文件已被改过」会让旧诊断自动失效 —— 这正是「编译失败」与「改过但未编译」的区分机制。"
            "判定表（纯函数 MCPTools::classify_csharp_verdict，可在非 mono 的 --test 进程 doctest）："
            "class_loaded && !source_newer → ok；否则有适用诊断 → invalid（error_text 为编译器原文，"
            "message 明说这是 project_build_csharp 的项目级构建）；否则 → not_compiled（valid=null + reason 引用两个引擎信号，"
            "单数工具 -32000 拒绝）。旧句里的 `unverifiable` 保留给唯一残余情形：引擎**根本没能把该文件当 Script 载入**。"
            "实测（本任务 mono 构建，pre/post 对照）：语法错误 .cs → invalid + CS1002 原文；合法 .cs → ok/valid=true；"
            "改过未编译 → not_compiled（与 invalid 区分）；非 mono 构建的 .cs 口径逐字节未动。"
        ),
        "value": "验证脚本语法 判别点：valid 只在真的用该文件自身的脚本语言编译过时才是结论（true=编译通过；false=编译失败，error_text 给 ERR_* 标识符）；本构建不含该语言的脚本后端时（例如 module_mono_enabled=no 的构建里的 .cs）不借用别的语言解析、也不给出 valid，而是以 -32000 拒绝并在 data.suggestion 里说明该用哪个构建或文件；进程根本没有初始化任何脚本语言时（--test 进程）只做括号平衡的结构检查，message 会明说没有编译。 A '.cs' file now gets a real verdict (TASK-055): `valid: true` means the loaded .NET assembly contains a build of this exact source (Script::is_script_valid() found a class for the script's path and CSharpScript::is_source_newer_than_assembly() says the file has not changed since that assembly was built); `valid: false` with `error_text` carrying the compiler's own diagnostic text means a project-level build of its .csproj that project_build_csharp ran and recorded rejected the file as it is now; and a file nothing has compiled - edited after the last build, or with no class in the loaded assembly - is refused with -32000 saying 'not compiled', never answered `valid: false`, because the engine itself has no C# compiler (CSharpScript::reload() returns OK unconditionally).",
    },
    # TASK-063 (b): the node-path parameter surface. Both tools take ONE node
    # path under the name `path`, and every path is relative to the edited scene
    # root - two facts the two-character original never stated. Measured
    # (TASK-060 c3/c4, reported as D-5/O-2/O-3): a caller guessed the name
    # `node_path`, the unknown-argument gate answered `-32602 Unknown parameter
    # 'node_path'`, the same request spelled `/root/Main/Ball` answered `-32001`
    # whose suggestion only said "use editor_get_scene_tree", and a bare name
    # that was not a direct child answered `-32001` as well. Twenty single writes
    # and thirty-nine batch calls were spent on that.
    #
    # What moves is only the text: the parameter *name* stays (`path`), because
    # renaming it would invalidate the frozen evidence and every existing caller.
    # Both values carry the one shared `NODE_PATH_RULE_SENTENCE`, so the two
    # cannot drift apart.
    "update_property": {
        "reason": (
            "TASK-063 (b) 参数面（TASK-060 第 2 轮 D-5 + O-2/O-3；实测 c3_a5_setpos_Ball 得 "
            "-32602 Unknown parameter 'node_path'、c4_s1_root_absolute 得 -32001、c4_s5_bare_name 得 -32001）："
            "原描述只有“修改属性”，既没说这个参数叫 path（单数、一个节点），也没说它是**被编辑场景根相对**的路径，"
            "更没提同族的批处理工具用的是 node_paths（复数、字符串数组）。参数名按决策保留（改名会破坏既有证据与调用方），"
            "只把路径基准与单/复数差别追加进描述。原文“修改属性”逐字保留在句首（append 模式）。"
            "判定依据是引擎源码：三个工具都用 MCPTools::find_node（tools/tool_helpers.cpp:1407-1424）解析路径，"
            "它按 Node::has_node() 从被编辑场景根相对解析（scene/main/node.cpp:2001），根自己的名字可作前缀，"
            "而 /root/... 这类绝对场景树路径在编辑器进程里指不到被编辑场景。"
        ),
        "value": "修改属性 " + NODE_PATH_RULE_SENTENCE,
    },
    "get_node_properties": {
        "reason": (
            "TASK-063 (b) 参数面：与 editor_set_node_property 同一条规则（同一个 MCPTools::find_node，"
            "同一个参数名 path、同一个场景根相对基准），只是读取而不是写入；原描述只有“获取节点属性”。"
            "两者共用同一个 NODE_PATH_RULE_SENTENCE 字面量，所以不会漂移。原文“获取节点属性”逐字保留在句首（append 模式）。"
        ),
        "value": "获取节点属性 " + NODE_PATH_RULE_SENTENCE,
    },
}
# v1.5: a schema override replaces the whole `inputSchema` object (there is
# nothing to append to), so it must carry `"mode": "replace"` and a `reason` that
# quotes the `required` member it removes verbatim - see the guard in `main`.
# `"required": []` (rather than a dropped key) is the shape every
# no-required-parameter tool of this contract already has
# (`running_game_get_scene_tree`), and `scripts/gen_b2_game_schema.py`
# reproduces it in the C++ literal.
SCHEMA_OVERRIDES = {
    # TASK-053 section 2.3 (M-5): the sampling stride. This is the first override
    # of a **ported** entry in the C tier, and it is the reason the entry count
    # does not move: adding a member to an existing tool is a schema override, not
    # an added tool (GDR-28 point 1 appends new tools; it does not silently
    # rewrite an existing one, so the rewrite has to be recorded here with its
    # reason - which is what `_meta.overrides` is for).
    #
    # The three members that were already there are copied verbatim (`frame_count`
                    "description": "该转移的 advance 布尔条件名；引擎注册为 AnimationTree 的 parameters/<状态机路径>/conditions/<名字> 参数（可用 editor_set_animation_tree_parameter 直接写入）",
                    "type": "string",
                },
                "advance_mode": {"default": "enabled", "type": "string"},
                "from_state": {"type": "string"},
                "node_path": {"type": "string"},
                "priority": {"default": 1, "type": "integer"},
                "state_machine_path": {"default": "", "type": "string"},
                "switch_mode": {"default": "immediate", "type": "string"},
                "to_state": {"type": "string"},
                "xfade_time": {"default": 0.0, "type": "number"},
            },
            "required": ["node_path", "from_state", "to_state"],
            "type": "object",
        },
    },
    # -----------------------------------------------------------------------
    # TASK-051 (v1.13): the four remaining entries of the B-tier `inputSchema`
    # batch. Each one *adds* members only; every pre-existing member keeps its
    # type, its default and its description character for character, and the
        "value": "获取节点属性 " + NODE_PATH_RULE_SENTENCE,
    },
    # ------------------------------------------------------------------
    # TASK-068 (2.i): `project_list_scripts` and the engine's own project cache.
    #
    # TASK-067 made the tool's script set a property of the *build* (it reads
    # `ScriptServer`), and its walk was left exactly as the reference declared it:
    # only `.` and `..` are skipped, so `.godot` / `.hiddendir` / `addons` all go
    # in. The doctest that pins `.hiddendir/secret.gd` is what makes narrowing the
    # walk a contract change rather than a cleanup, and the decision (D125 (b))
    # was therefore **not** to narrow it: listing a generated file is honest,
    # silently hiding it is a judgement the tool has no machine-checkable rule
    # for. The consequence is visible to a caller, though - a Mono project's
    # `res://.godot/mono/temp/obj/**` scripts come back in the answer - and until
    # this entry the only place that was written down was REPORT-067 section 1.4,
    # which a client reading `tools/list` never sees (TASK-067 deviation 5).
    #
    # The original `列出所有脚本文件` stays first, verbatim (append mode).
    # ------------------------------------------------------------------
    "list_scripts": {
        "reason": (
            "TASK-068 (2.i) 契约与行为一致（TASK-067 §1.4 的显式后果 + D125 裁决 (b)）：原文只有“列出所有脚本文件”，"
            "没说它会走进引擎自己的项目缓存目录。实现从 res:// 起递归收集、只跳过 . 与 .."
            "（tools/project_read_files.cpp 的 _collect_scripts_recursive；.hiddendir/secret.gd 这条已发布断言正是"
            "「不得按点前缀目录收窄」的理由），因此引擎生成的文件也会被列出：真实 mono 工程实测 2 条 "
            "res://.godot/mono/temp/obj/Debug/**.cs（REPORT-067 §1.4）。裁决是不收窄 walk（收窄会撞那条断言，"
            "且列出生成文件是诚实的），故把这一后果写进调用方唯一会读到的描述里，并说明过滤责任在调用方。"
            "原文“列出所有脚本文件”逐字保留在句首（append 模式）。"
        ),
        "value": (
            "列出所有脚本文件 会包含 .godot 下的生成脚本：本工具的 walk 从 res:// 起递归，只跳过 . 与 ..，"
            "因此引擎自己生成的文件也在答案里（真实 mono 工程会出现 res://.godot/mono/temp/obj/** 下的 .cs，"
            "例如 res://.godot/mono/temp/obj/Debug/*.AssemblyInfo.cs），调用方若要只看手写脚本请自行过滤这些路径。"
        ),
    },
    # ------------------------------------------------------------------
    # TASK-068 (2.ii): the `wait` step's input/output naming.
    #
    # R4 section 8.2 registered this as a "回显名陷阱" and TASK-068 was asked to
    # establish the facts before clarifying. The facts (measured, section 3 of
    # REPORT-068):
    #   * the contract's `inputSchema` has exactly one member for a wait step's
    #     duration, and it is `seconds`
    #     (docs/tools_list.renamed.json running_game_run_test_scenario
    #     .inputSchema.properties.steps.items.properties.seconds);
    #   * the implementation reads ONLY `seconds`
    #     (tools/running_game_test_execution.cpp:316 `_step_has_key(step,
    #     "seconds")`, :317 `optional_float(step, "seconds", ...)`) and knows no
    #     `waited_seconds` on the way in;
    #   * every step's answer echoes `waited_seconds`
    #     (tools/running_game_test_execution.cpp:440 and :459 `entry["waited_seconds"] = ...`),
    #     in a different object from the request member.
    # So this is **not** "one name used as both an input and an output": the input
    # member is `seconds`, the result member is `waited_seconds`, and they sit in
    # different objects. Nothing is renamed - renaming would break every existing
    # caller and the frozen evidence - and no alias is added, because adding an
    # input the contract does not declare would itself be an undeclared surface
    # expansion (gate 1 compares the live schema to the contract verbatim).
    # The clarification is therefore the description only: one sentence that names
    # both members and says which is which.
    #
    # The original `运行测试场景并执行一系列测试步骤` stays first, verbatim.
    # ------------------------------------------------------------------
    "run_test_scenario": {
        "reason": (
            "TASK-068 (2.ii) 契约与行为一致（R4 §8.2 登记；本条只改描述，不改行为）：核实结果是**不是同名异义** —— "
            "wait 步骤的等待时长入参在契约里叫 seconds（tools_list.renamed.json 的 "
            "inputSchema.properties.steps.items.properties.seconds，且是唯一一个），实现只读 seconds"
            "（tools/running_game_test_execution.cpp:316-317），而 steps[].type=wait 的**结果**条目回显 waited_seconds"
            "（同文件:440 与:459），两者在**不同的对象**里（请求的 step 对象 vs 结果的 result 条目）。"
            "因此按任务书②的情形只改描述：点名两个成员及其归属，说明入参是 seconds、结果里是 waited_seconds（回显的是真正等到的秒数），"
            "并明说 waited_seconds 不是入参（传它不算），入参名一字未改、也没有加别名（加一个契约未声明的入参会把线上 schema "
            "扩出契约，门①逐字比对会失败）。原文“运行测试场景并执行一系列测试步骤”逐字保留在句首（append 模式）。"
        ),
        "value": (
            "运行测试场景并执行一系列测试步骤 wait 步骤的入参名是 seconds（steps[i].seconds，契约 schema 里唯一的等待时长成员），"
            "结果里每个 wait 条目的回显字段叫 waited_seconds（按时间等待的步骤回显的就是 seconds；按 node_path 等待的步骤回显 timeout，"
            "见 tools/running_game_test_execution.cpp:440 与:459）；两者在**不同的对象**里，waited_seconds 不是入参"
            "（把它写进请求的 step 不生效，seconds 才是入参），入参名与结果字段名都未改动、既有调用不受影响。"
        ),
    },
}
# v1.5: a schema override replaces the whole `inputSchema` object (there is
# nothing to append to), so it must carry `"mode": "replace"` and a `reason` that
# quotes the `required` member it removes verbatim - see the guard in `main`.
# `"required": []` (rather than a dropped key) is the shape every
# no-required-parameter tool of this contract already has
# (`running_game_get_scene_tree`), and `scripts/gen_b2_game_schema.py`
# reproduces it in the C++ literal.
SCHEMA_OVERRIDES = {
    # TASK-053 section 2.3 (M-5): the sampling stride. This is the first override
    # of a **ported** entry in the C tier, and it is the reason the entry count
    # does not move: adding a member to an existing tool is a schema override, not
    # an added tool (GDR-28 point 1 appends new tools; it does not silently
    # rewrite an existing one, so the rewrite has to be recorded here with its
    # reason - which is what `_meta.overrides` is for).
    #
    # The three members that were already there are copied verbatim (`frame_count`
    # 60/采集帧数, `frame_interval` 1/采集间隔帧数, `node_path`/节点路径,
    # `properties`/要监控的属性列表) and `sample_stride` is the only addition.
    # The removed `required` member is quoted below exactly as the guard asks:
    # ["node_path", "properties"] - it is *not* removed, it stays, and the
    # quotation is the guard's way of proving the override did not drop it.
    "monitor_properties": {
        "reason": (
            "TASK-053 第 2.3 节 M-5（决策者裁决）新增可选整数参数 sample_stride（默认 1，最小 1）："
            "保留采样读取工具 running_game_get_node_property_samples 的“观察网格”（frame_interval 决定每隔几帧观察一次）"
            "并把“回传网格”交给 sample_stride（每隔 N 个观察点回传一个，第一个恒回传）。"
            "依据：RACING-TEST-PLAN 的 AC-4/AC-5 连续性断言必须用 frame_interval=1（每帧观察），"
            "而该调用在 3 属性×180 帧下回 23 020 B（REPORT-AUDIT-RACING-BACKLOG §3.5 已记录该体积风险）。"
            "缺省（或显式 1）时响应逐字节与改动前相同：只有 stride>1 时才追加 sample_stride 与 observed_count 两个键；"
            "frame_count 的含义不变成“回传样本数”。被移除的 required 成员逐字为 [\"node_path\", \"properties\"]"
            "（它并未被移除，仍逐字保留在 required 里）；原有四个属性（frame_count/frame_interval/node_path/properties "
            "的 type/default/description）一字未动，只是新增一个属性。"
        ),
        "mode": "replace",
        "value": {
            "properties": {
                "frame_count": {
                    "default": 60,
                                "type": "integer",
                            },
                            "button_mask": {
                                "default": 0,
                                "description": "按住的鼠标键位掩码（type=mouse_move 用，默认 0）",
                                "type": "integer",
                            },
                            "ctrl": {
                                "default": False,
                                "description": "Ctrl 修饰键（type=key 用，默认 false）",
                                "type": "boolean",
                            },
                            "keycode": {
                                "description": "按键名（type=key 必填，引擎的按键名，如 \"W\"/\"Space\"/\"Escape\"）",
                                "type": "string",
                            },
                            "position": {
                                "description": "{x,y} 坐标（type=mouse_click/mouse_move 用；与 x/y 等价，两者都给时以 position 为准）",
                                "type": "object",
                            },
                            "pressed": {
                                "default": True,
                                "description": "按下(true，默认)还是松开(false)（type=key/mouse_click/action 用）",
                                "type": "boolean",
                            },
                            "relative": {
                                "description": "{x,y} 相对位移（type=mouse_move 用）",
                                "type": "object",
                            },
                            "relative_x": {
                                "default": 0.0,
                                "description": "相对位移 x（type=mouse_move 用，默认 0）",
                                "type": "number",
                            },
                            "relative_y": {
                                "default": 0.0,
                                "description": "相对位移 y（type=mouse_move 用，默认 0）",
                                "type": "number",
                            },
                            "shift": {
                                "default": False,
                                "description": "Shift 修饰键（type=key 用，默认 false）",
                                "type": "boolean",
                            },
                            "strength": {
                                "default": 1.0,
                                "description": "动作强度（type=action 用，默认 1.0；引擎会夹到 0..1）",
                                "type": "number",
                            },
                            "time_ms": {
                                "description": "被忽略：本工具按 frame_delay 逐帧注入，不按时间戳（给了它只会在响应的 time_ms_ignored 里体现）"
                            },
                            "type": {
                                "description": "事件类型（必填）",
                                "enum": ["key", "mouse_click", "mouse_button", "mouse_move", "mouse_motion", "action"],
                                "type": "string",
                            },
                            "x": {
                                "default": 0.0,
                                "description": "x 坐标（type=mouse_click/mouse_move 用，默认 0）",
                                "type": "number",
                            },
                            "y": {
                                "default": 0.0,
                                "description": "y 坐标（type=mouse_click/mouse_move 用，默认 0）",
                                "type": "number",
                            },
                        },
                        "required": ["type"],
                        "type": "object",
                    },
                    "type": "array",
                },
                "frame_delay": {
                    "default": 1,
                    "type": "integer",
                },
            },
            "required": ["events"],
            "type": "object",
        },
    },
    "run_test_scenario": {
        "reason": (
            "TASK-051 O-5 契约与行为一致（racing-backlog 审计 §5.5 confirmed；D86 复测见 REPORT-051 §2.4）："
            "为 steps[].properties 补上实现一直在读、契约却没写的 pressed 与 strength"
            "（tools/running_game_test_execution.cpp:141-148 optional_bool(p_step,\"pressed\",true,…) 与 "
            "optional_float(p_step,\"strength\",1.0,…)）。两者只对 type=input 的步骤有效：pressed 决定按下还是松开，"
            "strength 是作用在 action 上的强度（引擎夹到 0..1）。这一步只是把既有能力写进声明，行为一字未改"
            "（G03 实测带 pressed:true 的调用本来就成功）。被移除的 required 成员逐字为 [\"steps\"]（原样保留，未删任何成员）；"
            "steps 的 items 里原有九个属性（action/expected/keycode/node_path/operator/property/seconds/text/type，"
            "含 type 的 enum 与 items.required=[\"type\"]）一字未动，只新增两个属性。"
        ),
        "mode": "replace",
        "value": {
            "properties": {
                "scene_path": {
                    "description": "场景路径，可选 'main', 'current' 或 res:// 路径",
                    "type": "string",
                },
                "steps": {
                    "description": "测试步骤数组，每个步骤包含 type(input/wait/assert) 和相关参数",
                    "items": {
                        "properties": {
                            "action": {
                                "description": "操作名称（input 类型使用）",
                                "type": "string",
                            },
                            "expected": {
                                "description": "期望值（assert 类型使用）"
                            },
                            "keycode": {
                                "description": "按键代码（input 类型使用）",
                                "type": "string",
                            },
                            "node_path": {
                                "description": "节点路径（wait/assert 类型使用）",
                                "type": "string",
                            },
                            "operator": {
                                "default": "eq",
                                "description": "比较操作符: eq/neq/gt/lt/gte/lte/contains/type_is",
                                "type": "string",
                            },
                            "pressed": {
                                "default": True,
                                "description": "input 步骤：注入的事件是按下(true，默认)还是松开(false)",
                                "type": "boolean",
                            },
                            "property": {
                                "description": "属性名（assert 类型使用）",
                                "type": "string",
                            },
                            "seconds": {
                                "description": "等待秒数（wait 类型使用）",
                                "type": "number",
                            },
                            "strength": {
                                "default": 1.0,
                                "description": "input 步骤作用于 action 时的强度（默认 1.0；引擎会夹到 0..1）",
                                "type": "number",
                            },
                            "text": {
                                "description": "期望文本（assert 类型使用）",
                                "type": "string",
                            },
                            "type": {
                                "description": "步骤类型",
                                "enum": ["input", "wait", "assert"],
                                "type": "string",
                            },
                        },
                        "required": ["type"],
                        "type": "object",
                    },
                    "type": "array",
                },
            },
            "required": ["steps"],
            "type": "object",
        },
    },
}

# ---------------------------------------------------------------------------
# v1.8 (TASK-052 section 0, DESIGN-DETAIL.md section 26 / GDR-28): the added
# tools.
#
# Each entry is authored by the decision maker (TASK-052 section 1 gives the
# wording of both entries verbatim) and carries exactly the three contract fields
# plus a `reason` that records *why* the tool exists. The reason is not emitted
# into the contract - `_meta.added_tools` is the ordered list of names that
# GDR-28 point 1 asks for - it is printed by the generator and quoted in
# `docs/reports/REPORT-052-added-tools.md`, which is where the audit trail for
# an added entry lives.
#
# The entries are separate from the two override tables on purpose: those two are
# keyed by an `old_name` of the frozen 174 entry map, an added tool has no such
# row, and mixing the two would make "this description was corrected" and "this
# tool did not exist before" indistinguishable in `_meta.overrides`.
# ---------------------------------------------------------------------------
ADDED_TOOLS = [
    {
        "name": "project_build_csharp",
        "channel": "project",
        "verb": "build",
        "description": (
            "Build the project's C# solution by running the .NET SDK on its .csproj files, and answer the "
            "exit code with the captured output. Requires a Godot build with C# support and a .NET SDK on "
            "PATH; when either is missing the call is refused with the reason and what to install."
        ),
        "inputSchema": {
            "properties": {
                "configuration": {
                    "default": "Debug",
                    "enum": ["Debug", "Release"],
                    "type": "string",
                },
                "extra_args": {
                    "default": [],
                    "items": {"type": "string"},
                    "type": "array",
                },
                "rescan": {
                    "default": True,
                    "type": "boolean",
                },
                "timeout_ms": {
                    "default": 120000,
                    "maximum": 600000,
                    "minimum": 1000,
                    "type": "integer",
                },
            },
            "required": [],
            "type": "object",
        },
        "reason": (
            "M-2 (REPORT-AUDIT-RACING-BACKLOG): the module could create C# projects "
            "(`project_set_setting`, `project_write_text_file`, `project_create_script`) but had no way to "
            "compile one, so the closed loop 'write a C# project from nothing and see it build' stopped one "
            "step short. The engine-side basis is the .NET SDK on PATH (the same tool `dotnet build` runs "
            "through, and the toolchain the engine's own C# exporter expects); the tool is capability-aware "
            "(GDR-28 point 6) because neither the C# module nor the SDK is guaranteed to be present."
        ),
    },
    {
        "name": "project_write_text_file",
        "channel": "project",
        "verb": "write",
                                "description": "y 坐标（type=mouse_click/mouse_move 用，默认 0）",
                                "type": "number",
                            },
                        },
                        "required": ["type"],
                        "type": "object",
                    },
                    "type": "array",
                },
                "frame_delay": {
                    "default": 1,
                    "type": "integer",
                },
            },
            "required": ["events"],
            "type": "object",
        },
    },
    "run_test_scenario": {
        "reason": (
            "TASK-051 O-5 契约与行为一致（racing-backlog 审计 §5.5 confirmed；D86 复测见 REPORT-051 §2.4）："
            "为 steps[].properties 补上实现一直在读、契约却没写的 pressed 与 strength"
            "（tools/running_game_test_execution.cpp:141-148 optional_bool(p_step,\"pressed\",true,…) 与 "
            "optional_float(p_step,\"strength\",1.0,…)）。两者只对 type=input 的步骤有效：pressed 决定按下还是松开，"
            "strength 是作用在 action 上的强度（引擎夹到 0..1）。这一步只是把既有能力写进声明，行为一字未改"
            "（G03 实测带 pressed:true 的调用本来就成功）。被移除的 required 成员逐字为 [\"steps\"]（原样保留，未删任何成员）；"
            "steps 的 items 里原有九个属性（action/expected/keycode/node_path/operator/property/seconds/text/type，"
            "含 type 的 enum 与 items.required=[\"type\"]）一字未动，只新增两个属性。"
        ),
        "mode": "replace",
        "value": {
            "properties": {
                "scene_path": {
                    "description": "场景路径，可选 'main', 'current' 或 res:// 路径",
                    "type": "string",
                },
                "steps": {
                    "description": "测试步骤数组，每个步骤包含 type(input/wait/assert) 和相关参数",
                    "items": {
                        "properties": {
                            "action": {
                                "description": "操作名称（input 类型使用）",
                                "type": "string",
                            },
                            "expected": {
                                "description": "期望值（assert 类型使用）"
                            },
                            "keycode": {
                                "description": "按键代码（input 类型使用）",
                                "type": "string",
                            },
                            "node_path": {
                                "description": "节点路径（wait/assert 类型使用）",
                                "type": "string",
                            },
                            "operator": {
                                "default": "eq",
                                "description": "比较操作符: eq/neq/gt/lt/gte/lte/contains/type_is",
                                "type": "string",
                            },
                            "pressed": {
                                "default": True,
                                "description": "input 步骤：注入的事件是按下(true，默认)还是松开(false)",
                                "type": "boolean",
                            },
                            "property": {
                                "description": "属性名（assert 类型使用）",
                                "type": "string",
                            },
                            "seconds": {
                                "description": "等待秒数（wait 类型使用）",
                                "type": "number",
                            },
                            "strength": {
                                "default": 1.0,
                                "description": "input 步骤作用于 action 时的强度（默认 1.0；引擎会夹到 0..1）",
                                "type": "number",
                            },
                            "text": {
                                "description": "期望文本（assert 类型使用）",
                "keep_existing": {
                    "default": False,
                    "type": "boolean",
                },
                "node_paths": {
                    "items": {"type": "string"},
                    "type": "array",
                },
                "script_path": {"type": "string"},
            },
                    },
                    "type": "array",
                },
            },
            "required": ["steps"],
            "type": "object",
        },
    },
}

# ---------------------------------------------------------------------------
# v1.8 (TASK-052 section 0, DESIGN-DETAIL.md section 26 / GDR-28): the added
# tools.
#
# Each entry is authored by the decision maker (TASK-052 section 1 gives the
# wording of both entries verbatim) and carries exactly the three contract fields
# plus a `reason` that records *why* the tool exists. The reason is not emitted
# into the contract - `_meta.added_tools` is the ordered list of names that
# GDR-28 point 1 asks for - it is printed by the generator and quoted in
# `docs/reports/REPORT-052-added-tools.md`, which is where the audit trail for
                    "type": "integer",
                },
            },
            "required": ["events"],
            "type": "object",
        },
    },
    "run_test_scenario": {
        "reason": (
            "TASK-051 O-5 契约与行为一致（racing-backlog 审计 §5.5 confirmed；D86 复测见 REPORT-051 §2.4）："
            "为 steps[].properties 补上实现一直在读、契约却没写的 pressed 与 strength"
            "（tools/running_game_test_execution.cpp:141-148 optional_bool(p_step,\"pressed\",true,…) 与 "
            "optional_float(p_step,\"strength\",1.0,…)）。两者只对 type=input 的步骤有效：pressed 决定按下还是松开，"
            "strength 是作用在 action 上的强度（引擎夹到 0..1）。这一步只是把既有能力写进声明，行为一字未改"
            "（G03 实测带 pressed:true 的调用本来就成功）。被移除的 required 成员逐字为 [\"steps\"]（原样保留，未删任何成员）；"
            "steps 的 items 里原有九个属性（action/expected/keycode/node_path/operator/property/seconds/text/type，"
            "含 type 的 enum 与 items.required=[\"type\"]）一字未动，只新增两个属性。"
        ),
        "mode": "replace",
        "value": {
            "properties": {
                "scene_path": {
                    "description": "场景路径，可选 'main', 'current' 或 res:// 路径",
                    "type": "string",
                },
                "steps": {
                    "description": "测试步骤数组，每个步骤包含 type(input/wait/assert) 和相关参数",
                    "items": {
                        "properties": {
                            "action": {
                                "description": "操作名称（input 类型使用）",
                                "type": "string",
                            },
                            "expected": {
                                "description": "期望值（assert 类型使用）"
                            },
                            "keycode": {
                                "description": "按键代码（input 类型使用）",
                                "type": "string",
                            },
                            "node_path": {
                                "description": "节点路径（wait/assert 类型使用）",
                                "type": "string",
                            },
                            "operator": {
                                "default": "eq",
                                "description": "比较操作符: eq/neq/gt/lt/gte/lte/contains/type_is",
                                "type": "string",
                            },
                            "pressed": {
                                "default": True,
                                "description": "input 步骤：注入的事件是按下(true，默认)还是松开(false)",
                                "type": "boolean",
                            },
                            "property": {
                                "description": "属性名（assert 类型使用）",
                                "type": "string",
                            },
                            "seconds": {
                                "description": "等待秒数（wait 类型使用）",
                                "type": "number",
                            },
                            "strength": {
                                "default": 1.0,
                                "description": "input 步骤作用于 action 时的强度（默认 1.0；引擎会夹到 0..1）",
                                "type": "number",
                            },
                            "text": {
                                "description": "期望文本（assert 类型使用）",
                                "type": "string",
            continue
        rest = name[len(prefix):]
        if not rest:
            return None
        if not all((("a" <= c <= "z") or ("0" <= c <= "9") or c == "_") for c in rest):
            return None
        # `editor_get` is legal: the object segment is not required (D-E4).
        verb = rest.split("_", 1)[0]
        return channel, verb
    return None


def validate_renamed(entry, closed_set):
    """GDR-16 L1..L4 checks for one map entry. Returns None or a reason."""
    name = entry["new_name"]
    if "update_" in name:
        return "L4 banned 'update_': %s" % name
    if not L1_PATTERN.match(name):
        return "L1 pattern mismatch: %s" % name
    parsed = parse_tool_name(name)
    if parsed is None:
        return "L1 parse failure: %s" % name
    channel, verb = parsed
    if verb not in closed_set:
        return "L2 verb '%s' outside the closed set: %s" % (verb, name)
    if verb != entry.get("verb"):
        return "L3 declared verb '%s' != parsed '%s': %s" % (entry.get("verb"), verb, name)
    if channel != entry.get("channel"):
        return "L3 declared channel '%s' != parsed '%s': %s" % (entry.get("channel"), channel, name)
    return None


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def validate_added(entry, closed_set):
    """GDR-28 point 4 naming lint for one `ADDED_TOOLS` record.

    There is no `tool-rename-map.json` row for a new tool, so the two facts a
    ported entry is cross-checked against the map (`channel`, `verb`) are
    cross-checked against the record's own declaration here: the name is parsed
    with the isomorphic `parse_tool_name`, and the channel and the verb the name
    spells out have to be the ones the record declares. A verb outside the map's
    closed set is accepted only when `ADDED_VERB_EXTENSIONS` carries a record for
    it (see the table's comment). Returns None or a reason."""
    for field in ("name", "channel", "verb", "description", "inputSchema", "reason"):
        if field not in entry:
            return "missing field '%s'" % field
    if not str(entry["name"]).strip():
        return "empty name"
    if not str(entry["reason"]).strip():
        return "empty reason (an added entry has to say why it exists)"
    name = entry["name"]
    if "update_" in name:
        return "L4 banned 'update_': %s" % name
    if not L1_PATTERN.match(name):
        return "L1 pattern mismatch: %s" % name
    parsed = parse_tool_name(name)
    if parsed is None:
        return "L1 parse failure: %s" % name
    channel, verb = parsed
    if channel != entry["channel"]:
        return "declared channel '%s' != parsed '%s': %s" % (entry["channel"], channel, name)
    if verb != entry["verb"]:
        return "declared verb '%s' != parsed '%s': %s" % (entry["verb"], verb, name)
    if verb not in closed_set and verb not in ADDED_VERB_EXTENSIONS:
        return "L2 verb '%s' is outside the closed set and has no ADDED_VERB_EXTENSIONS record: %s" % (verb, name)
    if not isinstance(entry["description"], str) or not entry["description"].strip():
        return "description must be a non-empty string"
    if not isinstance(entry["inputSchema"], dict):
        return "inputSchema must be a JSON object"
    return None


def apply_override(table, old_name, fallback, used, kind):
    """Returns (value, overridden). `overridden` is what makes the carry-over
    assertion below precise: the promise is "nothing moves *without* an explicit
    override", so a fired override has to be exempt from it (in B0 the table was
    empty, so the distinction was not observable and the blanket assertion made
    every override impossible).

    An entry is either

      * append-only (the default, v1.2): `value` is `<old value> + " " +
        <discriminator>`, so not a byte of the original wording can be lost; or
      * `"mode": "replace"` (v1.4): `value` is the corrected text and the
        *reason* has to carry the old text verbatim, so the correction stays
        auditable in `_meta.overrides` even though the field itself is rewritten.
        This mode exists for a value that is factually **wrong**, where an
        append-only discriminator would leave the false statement in the field a
        caller reads (`TASK-007` section 1).
    """
    record = table.get(old_name)
    if record is None:
        return fallback, False
    if "reason" not in record or "value" not in record:
        raise SystemExit("override for %s must carry 'reason' and 'value'" % old_name)
    if not str(record["reason"]).strip():
        raise SystemExit("override for %s carries an empty 'reason'" % old_name)
    mode = record.get("mode", "append")
    if mode not in ("append", "replace"):
        raise SystemExit("override for %s carries an unknown mode %r" % (old_name, mode))
    used.append({"kind": kind, "old_name": old_name, "mode": mode, "reason": record["reason"]})
    return record["value"], True


def main():
    parser = argparse.ArgumentParser(description="Generate the renamed tools/list contract.")
    parser.add_argument("--old-contract", default=DEFAULT_OLD_CONTRACT)
    parser.add_argument("--map", default=DEFAULT_MAP)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    old_path = os.path.abspath(args.old_contract)
    map_path = os.path.abspath(args.map)
    out_path = os.path.abspath(args.out)

    for path, label in ((old_path, "old contract"), (map_path, "rename map")):
        if not os.path.isfile(path):
            sys.exit("FATAL: %s not found: %s" % (label, path))

    old_sha = sha256_file(old_path)
    map_sha = sha256_file(map_path)

    with open(old_path, "r", encoding="utf-8") as handle:
        old_contract = json.load(handle)
# v1.8 (TASK-052 section 0, DESIGN-DETAIL.md section 26 / GDR-28): the added
# tools.
#
# Each entry is authored by the decision maker (TASK-052 section 1 gives the
# wording of both entries verbatim) and carries exactly the three contract fields
# plus a `reason` that records *why* the tool exists. The reason is not emitted
# into the contract - `_meta.added_tools` is the ordered list of names that
# GDR-28 point 1 asks for - it is printed by the generator and quoted in
# `docs/reports/REPORT-052-added-tools.md`, which is where the audit trail for
# an added entry lives.
#
# The entries are separate from the two override tables on purpose: those two are
# keyed by an `old_name` of the frozen 174 entry map, an added tool has no such
# row, and mixing the two would make "this description was corrected" and "this
# tool did not exist before" indistinguishable in `_meta.overrides`.
# ---------------------------------------------------------------------------
ADDED_TOOLS = [
    {
        "name": "project_build_csharp",
        "channel": "project",
        "verb": "build",
        "description": (
            "Build the project's C# solution by running the .NET SDK on its .csproj files, and answer the "
            "exit code with the captured output. Requires a Godot build with C# support and a .NET SDK on "
            "PATH; when either is missing the call is refused with the reason and what to install."
        ),
        "inputSchema": {
            "properties": {
                "configuration": {
                    "default": "Debug",
                    "enum": ["Debug", "Release"],
                    "type": "string",
                },
                "extra_args": {
                    "default": [],
                    "items": {"type": "string"},
                    "type": "array",
                },
                "rescan": {
                    "default": True,
                    "type": "boolean",
                },
                "timeout_ms": {
                    "default": 120000,
                    "maximum": 600000,
                    "minimum": 1000,
                    "type": "integer",
                },
            },
            "required": [],
            "type": "object",
        },
        "reason": (
            "M-2 (REPORT-AUDIT-RACING-BACKLOG): the module could create C# projects "
            "(`project_set_setting`, `project_write_text_file`, `project_create_script`) but had no way to "
            "compile one, so the closed loop 'write a C# project from nothing and see it build' stopped one "
            "step short. The engine-side basis is the .NET SDK on PATH (the same tool `dotnet build` runs "
            "through, and the toolchain the engine's own C# exporter expects); the tool is capability-aware "
            "(GDR-28 point 6) because neither the C# module nor the SDK is guaranteed to be present."
        ),
    },
    {
        "name": "project_write_text_file",
        "channel": "project",
        "verb": "write",
        "description": (
            "Write a project text file such as a .csproj, .sln, NuGet.config or .cfg, and answer the "
            "resulting size and sha256. Refuses scene, resource and script paths (use the dedicated tools "
            "for those) and refuses project.godot (use project_set_setting)."
        ),
        "inputSchema": {
            "properties": {
                "content": {"type": "string"},
                "overwrite": {"default": False, "type": "boolean"},
                "path": {"type": "string"},
            },
            "required": ["path", "content"],
            "type": "object",
        },
        "reason": (
            "N-3 (REPORT-AUDIT-RACING-BACKLOG): the 171 ported writers cover scenes, resources, scripts, "
            "shaders, themes and `project.godot`, but not the plain project text file a C# project or a "
            "config needs (.csproj / .sln / NuGet.config / .cfg), so building a C# project from scratch "
            "still required a hand-written file. The tool is deliberately narrow: it refuses the four "
            "dedicated families and `project.godot`, it has no delete path, and it reads the file back "
            "after the publish (size + sha256) instead of reporting the bytes it meant to write."
        ),
    },
    {
        "name": "project_validate_scripts",
        "channel": "project",
        "verb": "validate",
        "description": (
            "Validate every script of the project in one call and answer a per-file verdict, so a batch "
            "of edited scripts can be checked without one call per file. The categories are `ok` (the "
            "file's own language compiled it), `invalid` (it did not compile - for a `.cs` file that is a "
            "project-level build of its .csproj that project_build_csharp ran and recorded, and the item "
            "carries the compiler's own diagnostic text), `not_compiled` (no build of this source is "
            "loaded: the file was modified after the loaded .NET assembly was built, or that assembly has "
            "no class for the script's path - deliberately not `invalid`, because the engine has no C# "
            "compiler and CSharpScript::reload() returns OK unconditionally), `language_unavailable` (this "
            "build has no script backend for the extension) and `unverifiable` (the engine could not load "
            "the file as a Script resource); `valid` is published only for `ok` and `invalid`, and `count` "
            "is always the sum of the per-category counters."
        ),
        "inputSchema": {
            "properties": {
                "include_errors_only": {
                    "default": False,
                    "type": "boolean",
                },
                "paths": {
                    "items": {"type": "string"},
                    "type": "array",
                },
            },
            "required": [],
            "type": "object",
        },
        "reason": (
            "C-4 (3) of REPORT-AUDIT-RACING-BACKLOG: the racing trace calls `project_validate_script` "
            "seventeen times, six of them back to back (seq 127-132 and 274-279), because one call answers "
            "one file - and the ported contract has only the singular tool. The engine-side basis is "
            "already there: `ScriptServer::get_language_for_extension()` plus `Script::set_source_code()` "
            "+ `Script::reload()` is one loop, and TASK-050 N-2's three-way decision (a language this "
            "build does not contain is a refusal, never a borrowed verdict) is the same per file. The tool "
            "answers a category per file (`ok` / `invalid` / `language_unavailable`) whose counters account "
            "for every file it classified, and it is bounded (an explicit truncation marker) because a "
            "response must not be a function of how many scripts the caller's project has. "
            "TASK-054 (D-053-3) adds the fifth category `unverifiable`: a language this build contains whose "
            "scripts the engine API cannot compile. `CSharpScript::reload()` returns OK unconditionally "
            "(modules/mono/csharp_script.cpp:2588-2621) and never parses the source, so the plural tool used "
            "to answer a syntax-error `.cs` with `ok` / `valid: true` (measured: TASK-053 c03). The item now "
            "carries `valid: null`, a `reason` quoting the engine basis (the private `CSharpScript::valid` "
            "field, csharp_script.h:137, set at csharp_script.cpp:2599 from ScriptManagerBridge.cs:436-463) "
            "and a `suggestion`; `unverifiable_count` joins the counters so `count` stays the sum of the "
            "categories. The singular tool refuses the same file with -32000, so the two tools agree. "
            "TASK-055 (D112) replaces the TASK-054 half of this description: C# now has a real verdict "
            "(the engine accessor `CSharpScript::is_source_newer_than_assembly()` plus the public "
            "`Script::is_script_valid()`), the project-level half comes from the per-file diagnostics "
            "`project_build_csharp` records, `not_compiled` joins the categories for 'nothing compiled "
            "this source' (never published as `invalid`), `unverifiable` stays for the residual 'the "
            "engine could not load the file as a Script', and `not_compiled_count` joins the counters so "
            "`count` remains the sum of the five."
        ),
    },
    {
        "name": "editor_set_node_script_batch",
        "channel": "editor",
        "verb": "set",
        "description": (
            "Attach one script to many nodes in the edited scene in a single call, and answer per node "
            "whether the attachment landed and the script was readable. 'node_paths' is an array of node "
            "paths resolved relative to the edited scene root - the same strings the singular tools take "
            "under the name 'path' (editor_set_node_property, editor_get_node_properties): 'Bricks/Car' "
            "and './Bricks/Car' address 'Car' inside 'Bricks', and the edited scene root's own name may "
            "be used as a prefix ('Main/Bricks/Car' == 'Bricks/Car' == './Bricks/Car'). An absolute "
            "scene-tree path ('/root/Main/Bricks/Car') is not accepted, and a bare name such as 'Car' "
            "only addresses a direct child of the edited scene root. A refused path names this rule in "
            "data.suggestion."
        ),
        "inputSchema": {
            "properties": {
                "keep_existing": {
                    "default": False,
                    "type": "boolean",
                },
                "node_paths": {
                    "items": {"type": "string"},
                    "type": "array",
                },
                "script_path": {"type": "string"},
            },
            "required": ["node_paths", "script_path"],
            "type": "object",
        },
        "reason": (
            "C-4 (4) of REPORT-AUDIT-RACING-BACKLOG: `editor_set_node_script` is called eight times in a "
            "row (racing trace seq 133-140) to give the nodes of one edited scene their scripts, and the "
            "ported contract has no batch form. The engine-side basis is `Object::set_script()` plus the "
            "read-back `editor_set_node_script` already performs (`node->get_script()`): `set_script()` is "
            "a void method whose early return for an abstract script is exactly why a batch must answer "
            "what each node really carries. The tool is all-or-nothing like `editor_add_nodes_batch`, "
            "`keep_existing` skips a node that already has a script instead of silently replacing it, and "
            "one `script_path` for the batch is the whole reason the take-back exists."
        ),
    },
    {
        "name": "editor_set_node_property_updates",
        "channel": "editor",
        "verb": "set",
        "description": (
            "Set a different value on each of many nodes in the edited scene in one call, and answer per "
            "entry whether the value landed."
        ),
        "inputSchema": {
            "properties": {
                "updates": {
                    "items": {
                        "properties": {
                            "path": {"type": "string"},
                            "property": {"type": "string"},
                            "value": {},
                        },
                        "required": ["path", "property", "value"],
                        "type": "object",
                    },
                    "minItems": 1,
                    "type": "array",
                },
                "stop_on_error": {
                    "default": False,
                    "type": "boolean",
                },
            },
            "required": ["updates"],
            "type": "object",
        },
        "reason": (
            "TASK-060 M-1 / D-6 (the second round's capability gap): the ported contract's only batch "
            "property write is `editor_set_node_property_batch`, whose grammar is "
            "`{node_type, property, value}` - one **type-scoped** value for every node of a class. Laying "
            "out a level therefore costs one `editor_set_node_property` per node: the round-2 trace called "
            "it 60 times (57 of them the same tool back to back, `fragments`/bigrams of "
            "REPORT-062's TRACE-FRICTION-ANALYSIS), and the request that asked for the missing shape "
            "(`updates:[...]`) was answered `-32602 Unknown parameter 'updates'` (c3_a5_batch_positions). "
            "The engine-side basis is that the write itself is already per node and already gated: "
            "`MCPTools::write_node_property` is one property write on one `Object` (declared type, "
            "component mapping, `ValueSlot` narrowing gate, read-back), so a *path*-scoped list is one loop "
            "over it and needs no new narrowing rule. The engine has no batch setter, so the tool must be "
            "an added name rather than a ported one (GDR-28). `updates[].path` is the same string the "
            "singular tools take under the name `path` (see `NODE_PATH_RULE_SENTENCE`); `stop_on_error` "
            "exists because the useful answer depends on the caller's intent - `false` (the default) "
            "reports every entry and leaves the ones that landed in place, `true` is all-or-nothing like "
            "the rest of this module's batches: the first refusal stops the call and every entry that "
            "already landed is put back to the value it had. The per-entry `changed`/`old_value`/"
            "`new_value` triple is the read-back the sibling tools publish, so 'the value landed' is "
            "never asserted from the request."
        ),
    },
]

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(HERE)

# ---------------------------------------------------------------------------
# The verbs an *added* tool may introduce.
#
# `tool-rename-map.json`'s `convention.verb_closed_set` is the map's own closed
# set for the 174 ported entries, and it stays the authority for those - this
# generator must never widen it (the map's sha256 travels into
# `_meta.map_sha256` and every ported name is validated against it). GDR-28 point
# 4 requires an added entry to be named by the same rule as a ported one, and it
# spells out the channel restriction and the `update_` ban; it does not say
# whether the closed set binds added names too. The decision taken here (recorded
# in `docs/reports/REPORT-052-added-tools.md`, and reported as a gap in the spec
# wording) is: **the closed set keeps its meaning, and a new verb may only enter
# through an explicit record below**, so `--added` can print the exact set of
# verbs the contract ever invented. Two records exist because the decision maker
# fixed the two names of TASK-052 section 1:
#
#   * `build` - `project_build_csharp`. No existing verb says "compile the
#     project with an external toolchain": `run`/`execute` name a script or a
#     scenario, `export` names a Godot export preset;
#   * `write` - `project_write_text_file`. `create` would claim the file is new
#     (it may overwrite), `edit` names a change to an existing file, `set` names
#     a *setting* (`project_set_setting` is the sibling this tool points callers
#     to for `project.godot`), and `save` names the engine's save_* writers.
#     `write` is the verb the contract wording itself uses ("Write a project text
#     file").
#
# The same two records live in `docs/tool-groups-added.json` as
# `verb_extensions`, where `check_tool_groups.py --added` requires each one to be
# actually used by a group, so neither side can accumulate a stale entry.
# ---------------------------------------------------------------------------
ADDED_VERB_EXTENSIONS = {
    "build": "project_build_csharp - no existing verb names 'compile the project with an external toolchain'",
    "write": "project_write_text_file - the file may or may not exist, so create/edit/set/save all overclaim",
}

DEFAULT_OLD_CONTRACT = r"F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json"
DEFAULT_MAP = os.path.join(MODULE_ROOT, "docs", "tool-rename-map.json")
DEFAULT_OUT = os.path.join(MODULE_ROOT, "docs", "tools_list.renamed.json")

OLD_CONTRACT_SHA256 = "8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54"

# GDR-16 L1: channels tried longest prefix first. `running_game_` carries its own
# underscore, so a `split('_')[1]` parse would read the verb as `game`.
CHANNELS = ("running_game", "project", "editor", "os")
L1_PATTERN = re.compile(r"^(editor|running_game|project|os)_[a-z0-9_]+$")

# D-4: the disposition field is an enum, and a merge names its survivor through
# the separate `merge_target` field instead of the v1.0 `merge_into:<old_name>`
# string form.
DISPOSITION_ENUM = (
    "rename",
    "keep",
    "merge_into",
    "unregister_until_implemented",
    "fix_implementation_first",
)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_tool_name(name):
    """Isomorphic to MCPToolRegistry::parse_tool_name (tool_registry.cpp)."""
    for channel in CHANNELS:
        prefix = channel + "_"
        if not name.startswith(prefix):
            continue
        rest = name[len(prefix):]
        if not rest:
            return None
        if not all((("a" <= c <= "z") or ("0" <= c <= "9") or c == "_") for c in rest):
            return None
        # `editor_get` is legal: the object segment is not required (D-E4).
        verb = rest.split("_", 1)[0]
        return channel, verb
    return None


def validate_renamed(entry, closed_set):
    """GDR-16 L1..L4 checks for one map entry. Returns None or a reason."""
    name = entry["new_name"]
    if "update_" in name:
        return "L4 banned 'update_': %s" % name
    if not L1_PATTERN.match(name):
        return "L1 pattern mismatch: %s" % name
    parsed = parse_tool_name(name)
    if parsed is None:
        return "L1 parse failure: %s" % name
    channel, verb = parsed
    if verb not in closed_set:
        return "L2 verb '%s' outside the closed set: %s" % (verb, name)
    if verb != entry.get("verb"):
        return "L3 declared verb '%s' != parsed '%s': %s" % (entry.get("verb"), verb, name)
    if channel != entry.get("channel"):
        return "L3 declared channel '%s' != parsed '%s': %s" % (entry.get("channel"), channel, name)
    return None


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def validate_added(entry, closed_set):
    """GDR-28 point 4 naming lint for one `ADDED_TOOLS` record.

    There is no `tool-rename-map.json` row for a new tool, so the two facts a
    ported entry is cross-checked against the map (`channel`, `verb`) are
    cross-checked against the record's own declaration here: the name is parsed
    with the isomorphic `parse_tool_name`, and the channel and the verb the name
    spells out have to be the ones the record declares. A verb outside the map's
    closed set is accepted only when `ADDED_VERB_EXTENSIONS` carries a record for
    it (see the table's comment). Returns None or a reason."""
    for field in ("name", "channel", "verb", "description", "inputSchema", "reason"):
        if field not in entry:
            return "missing field '%s'" % field
    if not str(entry["name"]).strip():
        return "empty name"
    if not str(entry["reason"]).strip():
        return "empty reason (an added entry has to say why it exists)"
    name = entry["name"]
    if "update_" in name:
        return "L4 banned 'update_': %s" % name
    if not L1_PATTERN.match(name):
        return "L1 pattern mismatch: %s" % name
    parsed = parse_tool_name(name)
    if parsed is None:
        return "L1 parse failure: %s" % name
    channel, verb = parsed
    if channel != entry["channel"]:
        return "declared channel '%s' != parsed '%s': %s" % (entry["channel"], channel, name)
    if verb != entry["verb"]:
        return "declared verb '%s' != parsed '%s': %s" % (entry["verb"], verb, name)
    if verb not in closed_set and verb not in ADDED_VERB_EXTENSIONS:
        return "L2 verb '%s' is outside the closed set and has no ADDED_VERB_EXTENSIONS record: %s" % (verb, name)
    if not isinstance(entry["description"], str) or not entry["description"].strip():
        return "description must be a non-empty string"
    if not isinstance(entry["inputSchema"], dict):
        return "inputSchema must be a JSON object"
    return None

    if len(merged) != 1:
        sys.exit("FATAL: expected 1 merge_into entry (GDR-17), got %d" % len(merged))

    keep_names = set(entry["old_name"] for entry in entries)
    for item in merged:
        keep = item["merged_into"]
        if keep not in keep_names:
            sys.exit("FATAL: merge keep '%s' is not an old_name in the map" % keep)
        if keep in excluded:
            sys.exit("FATAL: merge keep '%s' is itself excluded" % keep)
        # self check 4: the merged entry and its keeper share one new name, so
        # deduplication cannot create a duplicate.
        if by_old_name[keep]["new_name"] != item["new_name"]:
            sys.exit("FATAL: merge %s -> %s but keeper %s -> %s"
                     % (item["old_name"], item["new_name"], keep, by_old_name[keep]["new_name"]))

    excluded_set = set(excluded)
    merged_set = set(item["old_name"] for item in merged)
    dropped = excluded_set | merged_set

    # --- self check 2: every emitted new name passes the isomorphic lint -----
    for entry in entries:
        if entry["old_name"] in dropped:
            continue
        reason = validate_renamed(entry, closed_set)
        if reason is not None:
            sys.exit("FATAL: %s" % reason)

    # --- transform: name only, description / inputSchema verbatim ------------
    overrides_used = []
    new_tools = []
    name_sources = []
    for tool in old_contract["result"]["tools"]:
def main():
    parser = argparse.ArgumentParser(description="Generate the renamed tools/list contract.")
    parser.add_argument("--old-contract", default=DEFAULT_OLD_CONTRACT)
    parser.add_argument("--map", default=DEFAULT_MAP)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    old_path = os.path.abspath(args.old_contract)
    map_path = os.path.abspath(args.map)
    out_path = os.path.abspath(args.out)

    for path, label in ((old_path, "old contract"), (map_path, "rename map")):
        if not os.path.isfile(path):
            sys.exit("FATAL: %s not found: %s" % (label, path))

    old_sha = sha256_file(old_path)
    map_sha = sha256_file(map_path)

    with open(old_path, "r", encoding="utf-8") as handle:
        old_contract = json.load(handle)
    with open(map_path, "r", encoding="utf-8") as handle:
        rename_map = json.load(handle)

    if old_sha != OLD_CONTRACT_SHA256:
        sys.exit("FATAL: old contract sha256 %s != the frozen %s" % (old_sha, OLD_CONTRACT_SHA256))

    # --- self check 1: map vs old contract are the same 174 tool names -------
    entries = rename_map["tools"]
    total = rename_map.get("total")
    if not (len(entries) == total == 174):
        sys.exit("FATAL: map total=%s but %d entries" % (total, len(entries)))

    old_names = [tool["name"] for tool in old_contract["result"]["tools"]]
    entry_names = [entry["old_name"] for entry in entries]
    if len(set(old_names)) != len(old_names):
    record = table.get(old_name)
    if record is None:
        return fallback, False
    if "reason" not in record or "value" not in record:
        raise SystemExit("override for %s must carry 'reason' and 'value'" % old_name)
    if not str(record["reason"]).strip():
        raise SystemExit("override for %s carries an empty 'reason'" % old_name)
    mode = record.get("mode", "append")
    if mode not in ("append", "replace"):
        raise SystemExit("override for %s carries an unknown mode %r" % (old_name, mode))
    used.append({"kind": kind, "old_name": old_name, "mode": mode, "reason": record["reason"]})
    return record["value"], True


def main():
    parser = argparse.ArgumentParser(description="Generate the renamed tools/list contract.")
    parser.add_argument("--old-contract", default=DEFAULT_OLD_CONTRACT)
    parser.add_argument("--map", default=DEFAULT_MAP)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    old_path = os.path.abspath(args.old_contract)
    map_path = os.path.abspath(args.map)
    out_path = os.path.abspath(args.out)

    for path, label in ((old_path, "old contract"), (map_path, "rename map")):
        if not os.path.isfile(path):
            sys.exit("FATAL: %s not found: %s" % (label, path))

    old_sha = sha256_file(old_path)
    map_sha = sha256_file(map_path)

    with open(old_path, "r", encoding="utf-8") as handle:
        old_contract = json.load(handle)
    with open(map_path, "r", encoding="utf-8") as handle:
        rename_map = json.load(handle)

    if old_sha != OLD_CONTRACT_SHA256:
        sys.exit("FATAL: old contract sha256 %s != the frozen %s" % (old_sha, OLD_CONTRACT_SHA256))

    # --- self check 1: map vs old contract are the same 174 tool names -------
    entries = rename_map["tools"]
    total = rename_map.get("total")
    if not (len(entries) == total == 174):
        sys.exit("FATAL: map total=%s but %d entries" % (total, len(entries)))

    old_names = [tool["name"] for tool in old_contract["result"]["tools"]]
    entry_names = [entry["old_name"] for entry in entries]
    if len(set(old_names)) != len(old_names):
        sys.exit("FATAL: the old contract has duplicate tool names")
    if set(old_names) != set(entry_names):
        missing = sorted(set(old_names) - set(entry_names))
        extra = sorted(set(entry_names) - set(old_names))
        sys.exit("FATAL: map does not cover the old contract: missing=%s extra=%s" % (missing, extra))

    by_old_name = {entry["old_name"]: entry for entry in entries}
    closed_set = set(rename_map["convention"]["verb_closed_set"])

    # --- D-4: disposition is an enum, and a merge is named by merge_target ----
    bad_enum = sorted({entry.get("disposition") for entry in entries} - set(DISPOSITION_ENUM))
    if bad_enum:
        sys.exit("FATAL: disposition value(s) outside the enum: %s" % bad_enum)
    legacy = [entry["old_name"] for entry in entries
              if str(entry.get("disposition", "")).startswith("merge_into:")]
    if legacy:
        sys.exit("FATAL: the v1.0 inline 'merge_into:<old_name>' form survives on %s" % legacy)

    # --- disposition split ---------------------------------------------------
    excluded = [entry["old_name"] for entry in entries
                if entry.get("disposition") == "unregister_until_implemented"]
    merged = []
    for entry in entries:
        if entry.get("disposition") != "merge_into":
            continue
        target = entry.get("merge_target")
        if not target:
            sys.exit("FATAL: merge_into entry %s carries no merge_target" % entry["old_name"])
        merged.append({
            "old_name": entry["old_name"],
            "new_name": entry["new_name"],
            "merged_into": target,
        })
    for entry in entries:
        if entry.get("disposition") != "merge_into" and "merge_target" in entry:
            sys.exit("FATAL: merge_target on a non-merge entry: %s" % entry["old_name"])

    if len(excluded) != 2:
        sys.exit("FATAL: expected 2 unregister_until_implemented entries, got %d" % len(excluded))
    if len(merged) != 1:
        sys.exit("FATAL: expected 1 merge_into entry (GDR-17), got %d" % len(merged))

    keep_names = set(entry["old_name"] for entry in entries)
    for item in merged:
        keep = item["merged_into"]
        if keep not in keep_names:
            sys.exit("FATAL: merge keep '%s' is not an old_name in the map" % keep)
        if keep in excluded:
            sys.exit("FATAL: merge keep '%s' is itself excluded" % keep)
        # self check 4: the merged entry and its keeper share one new name, so
        # deduplication cannot create a duplicate.
        if by_old_name[keep]["new_name"] != item["new_name"]:
            sys.exit("FATAL: merge %s -> %s but keeper %s -> %s"
                     % (item["old_name"], item["new_name"], keep, by_old_name[keep]["new_name"]))

    excluded_set = set(excluded)
    merged_set = set(item["old_name"] for item in merged)
    dropped = excluded_set | merged_set

    # --- self check 2: every emitted new name passes the isomorphic lint -----
    for entry in entries:
        if entry["old_name"] in dropped:
            continue
        reason = validate_renamed(entry, closed_set)
        if reason is not None:
            sys.exit("FATAL: %s" % reason)

    # --- transform: name only, description / inputSchema verbatim ------------
    overrides_used = []
    new_tools = []
    name_sources = []
    for tool in old_contract["result"]["tools"]:
        entry = by_old_name[tool["name"]]
        if entry["old_name"] in dropped:
            continue

        new_tool = dict(tool)  # keeps the old key order
        new_tool["name"] = entry["new_name"]

        description, desc_overridden = apply_override(DESCRIPTION_OVERRIDES, entry["old_name"],
                                                     tool["description"], overrides_used, "description")
        schema, schema_overridden = apply_override(SCHEMA_OVERRIDES, entry["old_name"],
                                                  tool["inputSchema"], overrides_used, "inputSchema")

        # The no-override case must be a byte-exact carry over at the object
        # level; the assertion is what keeps the promise from section 2 honest.
        if not desc_overridden and canonical(description) != canonical(tool["description"]):
            sys.exit("FATAL: description of %s changed without an explicit override" % entry["old_name"])
        if not schema_overridden and canonical(schema) != canonical(tool["inputSchema"]):
            sys.exit("FATAL: inputSchema of %s changed without an explicit override" % entry["old_name"])
        # v1.2: an *append* override may only add one discriminator sentence, so
        # the original wording can never be silently dropped. v1.4 adds the
        # explicit `mode: "replace"` escape hatch for text that is factually
        # wrong; it is refused unless the record's reason quotes the text it
        # replaces, so a replacement cannot be a silent edit either.
        mode = DESCRIPTION_OVERRIDES.get(entry["old_name"], {}).get("mode", "append") if desc_overridden else "append"
        if desc_overridden and mode == "append" and not str(description).startswith(str(tool["description"]) + " "):
            sys.exit("FATAL: description override of %s is not append-only (original wording lost)"
                     % entry["old_name"])
        if desc_overridden and mode == "replace":
            original = str(tool["description"])
            reason = str(DESCRIPTION_OVERRIDES[entry["old_name"]]["reason"])
            if original not in reason:
                sys.exit("FATAL: replacing description override of %s must quote the text it replaces in "
                         "'reason' (original wording would be lost from the record)"
                         % entry["old_name"])
        # v1.5: a schema override is a whole-object replacement, and the one thing
        # it can silently drop is a `required` member. The record must therefore
        # name what it removes, verbatim, or the contract's old obligation is gone
        # with no trace beyond "a schema override fired".
        if schema_overridden:
            record = SCHEMA_OVERRIDES[entry["old_name"]]
            if record.get("mode") != "replace":
                sys.exit("FATAL: schema override of %s must carry \"mode\": \"replace\" (a schema is "
                         "replaced, there is nothing to append to)" % entry["old_name"])
            removed_required = canonical(tool["inputSchema"].get("required", []))
            if removed_required not in str(record["reason"]):
                sys.exit("FATAL: schema override of %s must quote the 'required' member it removes "
                         "verbatim in 'reason' (expected %s)"
                         % (entry["old_name"], removed_required))

        new_tool["description"] = description
        new_tool["inputSchema"] = schema
        new_tools.append(new_tool)
        name_sources.append(entry["new_name"])

    # --- v1.8 (GDR-28 point 1): deterministic append of the new tools ---------
    # After the rename + override pass, never before: an added entry is not a
    # carried-over entry with a changed field, and the two name lists are proved
    # disjoint in both directions below. The output key order is the ported
    # entries' key order (`description`, `inputSchema`, `name`, which is the old
    # contract's own order with `name` replaced), so the file stays diffable.
    ported_names = set(name_sources)
    map_new_names = set(entry["new_name"] for entry in entries)
    added_names = []
    added_verbs_used = set()
    for record in ADDED_TOOLS:
        reason = validate_added(record, closed_set)
        if reason is not None:
            sys.exit("FATAL: added tool: %s" % reason)
        name = record["name"]
        if name in ported_names:
            sys.exit("FATAL: added tool %s has the same name as a ported tool" % name)
        if name in map_new_names:
            sys.exit("FATAL: added tool %s collides with a rename-map new_name" % name)
        if name in added_names:
            sys.exit("FATAL: added tool %s is declared twice" % name)
        if record["verb"] not in closed_set:
            added_verbs_used.add(record["verb"])
        added_names.append(name)
        new_tools.append({
            "description": record["description"],
            "inputSchema": record["inputSchema"],
            "name": name,
        })
        name_sources.append(name)






























        sys.exit("FATAL: duplicate new names in the output: %s" % duplicates)

    meta = {
        "generated_from": old_path,
        "generated_from_sha256": old_sha,
        "map_path": map_path,
        "map_sha256": map_sha,
        "tool_count_in": len(old_names),
        "count": len(new_tools),
        # v1.8 (GDR-28 point 1): the entries that did not come from the map. The
        # list is ordered exactly like the append, so `result.tools[-N:]` are
        # these names in this order; `added_count` is redundant with the list's
        # length on purpose (a consumer that only needs the arithmetic does not
        # have to trust a length).
        "added_count": len(added_names),
        "added_tools": added_names,
        # D-1 (TASK-003 section 1.1, D49): `result.tools` is a *set* for the
        # consumers; the order is explicitly outside the contract. The engine is
        # only required to be deterministic within one build (a second
        # `tools/list` on the same registry is byte-identical), not to reproduce
        # the order below - so no implementation may ever be "fixed" to match it.
        "order_normative": False,
        "excluded": excluded,
        "merged": merged,
        "generator_version": GENERATOR_VERSION,
        "generated_by": GENERATED_BY,
    }
    if overrides_used:
        meta["overrides"] = overrides_used

    output = {
        "id": old_contract["id"],
        "jsonrpc": old_contract["jsonrpc"],
        "result": {"tools": new_tools},
        "_meta": meta,
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    out_sha = sha256_file(out_path)

    print("gen_renamed_contract: input tools = %d" % len(old_names))
    print("gen_renamed_contract: output tools = %d" % len(new_tools))
    print("gen_renamed_contract: order_normative = %s (order is not part of the contract)"
          % json.dumps(output["_meta"]["order_normative"]))
    print("gen_renamed_contract: merged = %d (%s)" % (
        len(merged), ", ".join("%s -> %s" % (m["old_name"], m["merged_into"]) for m in merged)))
    print("gen_renamed_contract: unregister = %d (%s)" % (len(excluded), ", ".join(excluded)))
    print("gen_renamed_contract: added = %d (%s)" % (len(added_names), ", ".join(added_names)))
    for record in ADDED_TOOLS:
        print("gen_renamed_contract: added[%s] verb=%s reason=%s"
              % (record["name"], record["verb"], record["reason"]))
    print("gen_renamed_contract: added verb extensions used = %s"
          % (", ".join(sorted(added_verbs_used)) if added_verbs_used else "(none)"))
    print("gen_renamed_contract: overrides = %d (%s)"
          % (len(overrides_used), ", ".join("%s/%s:%s" % (record["kind"], record["old_name"], record["mode"]) for record in overrides_used)))
    print("gen_renamed_contract: old contract sha256 = %s" % old_sha)
    print("gen_renamed_contract: rename map sha256 = %s" % map_sha)
    print("gen_renamed_contract: output sha256 = %s" % out_sha)
    print("gen_renamed_contract: self-checks = OK (lint %d/%d, unique %d/%d, disposition enum OK)"
          % (len(new_tools), len(new_tools), len(new_tools), len(new_tools)))
    print("gen_renamed_contract: wrote %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
