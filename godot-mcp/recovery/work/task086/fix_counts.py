# -*- coding: utf-8 -*-
"""TASK-086: bring the stale registry-size assertions of the reconstructed test
header to the number the *contract-complete* registration produces.

Why this is a restoration and not "changing an assertion to make it pass":

  * the recorded edit stream of `tests/test_mcp_server.h` contains, over and over,
    edits whose whole purpose is to move exactly these numbers up as each batch
    lands (`get_tool_count() == 40` -> ... -> `== 175` -> `== 176`,
    `get_visible_tool_count(true) == 152` -> `== 153`, times 7/8 occurrences at
    once). The tree still carries the TASK-015/TASK-017 generation of them
    (48 / 76 / 59 / 35 / 31 / 24);
  * the contract (`docs/tools_list.renamed.json`, 177 entries) plus the scope
    authority (`docs/tool-rename-map.json`) *predict* exactly 177 registered in an
    editor process, 154 visible to an editor and 73 in a game process
    (46 `both` + 102 `editor` + 23 `game` from the map, plus the 6 `ADDED_TOOLS`:
    4 `both` + 2 `editor`);
  * after the registration recovery of this task the registry *measures* exactly
    those numbers (73 / 177 / 154 / 50), so the two sides agree.

Each substitution is pinned to a line number and its expected old text.
"""
import io
import sys

PATH = r"H:\rebuild\godot\modules\mcp_server\tests\test_mcp_server.h"
NOTE = "\t// TASK-086: %s\n"

SITES = {
    1422: ("CHECK(registry.get_tool_count() == 48);", "CHECK(registry.get_tool_count() == 73);"),
    1451: ("CHECK(registry.get_tool_count() == 48);", "CHECK(registry.get_tool_count() == 73);"),
    1648: ("CHECK(registry.build_tools_list(true).size() == 31);", "CHECK(registry.build_tools_list(true).size() == 50);"),
    2290: ("CHECK(registry.get_tool_count() == 48);", "CHECK(registry.get_tool_count() == 73);"),
    2291: ("CHECK(registry.get_visible_tool_count(true) == 35);", "CHECK(registry.get_visible_tool_count(true) == 50);"),
    2292: ("CHECK(registry.get_visible_tool_count(false) == 48);", "CHECK(registry.get_visible_tool_count(false) == 73);"),
    2959: ("CHECK(game_registry.get_tool_count() == 48);", "CHECK(game_registry.get_tool_count() == 73);"),
    2960: ("CHECK(game_registry.get_visible_tool_count(false) == 48);", "CHECK(game_registry.get_visible_tool_count(false) == 73);"),
    2970: ("CHECK(editor_registry.get_tool_count() == 76);", "CHECK(editor_registry.get_tool_count() == 177);"),
    2971: ("CHECK(editor_registry.get_visible_tool_count(true) == 59);", "CHECK(editor_registry.get_visible_tool_count(true) == 154);"),
    2973: ("CHECK(editor_registry.get_visible_tool_count(false) == 48);", "CHECK(editor_registry.get_visible_tool_count(false) == 73);"),
    2989: ("CHECK(game_list.size() == 48);", "CHECK(game_list.size() == 73);"),
    3581: ("CHECK(registry.get_tool_count() == 24);", "CHECK(registry.get_tool_count() == 73);"),
    4215: ("CHECK(game_registry.get_tool_count() == 48);", "CHECK(game_registry.get_tool_count() == 73);"),
    4216: ("CHECK(game_registry.get_visible_tool_count(false) == 48);", "CHECK(game_registry.get_visible_tool_count(false) == 73);"),
    4225: ("CHECK(editor_registry.get_tool_count() == 76);", "CHECK(editor_registry.get_tool_count() == 177);"),
    4226: ("CHECK(editor_registry.get_visible_tool_count(true) == 59);", "CHECK(editor_registry.get_visible_tool_count(true) == 154);"),
    4227: ("CHECK(editor_registry.get_visible_tool_count(false) == 48);", "CHECK(editor_registry.get_visible_tool_count(false) == 73);"),
    4242: ("CHECK(game_list.size() == 48);", "CHECK(game_list.size() == 73);"),
    4251: ("CHECK(editor_list.size() == 59);", "CHECK(editor_list.size() == 154);"),
    4611: ("CHECK(game_registry.get_tool_count() == 48);", "CHECK(game_registry.get_tool_count() == 73);"),
    4612: ("CHECK(game_registry.get_visible_tool_count(false) == 48);", "CHECK(game_registry.get_visible_tool_count(false) == 73);"),
    4613: ("CHECK(game_registry.get_visible_tool_count(true) == 35);", "CHECK(game_registry.get_visible_tool_count(true) == 50);"),
    4622: ("CHECK(editor_registry.get_tool_count() == 76);", "CHECK(editor_registry.get_tool_count() == 177);"),
    4623: ("CHECK(editor_registry.get_visible_tool_count(true) == 59);", "CHECK(editor_registry.get_visible_tool_count(true) == 154);"),
    4624: ("CHECK(editor_registry.get_visible_tool_count(false) == 48);", "CHECK(editor_registry.get_visible_tool_count(false) == 73);"),
    4663: ("CHECK(game_list.size() == 48);", "CHECK(game_list.size() == 73);"),
    4674: ("CHECK(editor_list.size() == 59);", "CHECK(editor_list.size() == 154);"),
    7711: ("CHECK(game_registry.get_tool_count() == 48);", "CHECK(game_registry.get_tool_count() == 73);"),
    7712: ("CHECK(game_registry.get_visible_tool_count(false) == 48);", "CHECK(game_registry.get_visible_tool_count(false) == 73);"),
    7717: ("CHECK(editor_registry.get_tool_count() == 76);", "CHECK(editor_registry.get_tool_count() == 177);"),
    7718: ("CHECK(editor_registry.get_visible_tool_count(true) == 59);", "CHECK(editor_registry.get_visible_tool_count(true) == 154);"),
    7719: ("CHECK(editor_registry.get_visible_tool_count(false) == 48);", "CHECK(editor_registry.get_visible_tool_count(false) == 73);"),
    7734: ("CHECK(game_list.size() == 48);", "CHECK(game_list.size() == 73);"),
    7743: ("CHECK(editor_list.size() == 59);", "CHECK(editor_list.size() == 154);"),
    8412: ("CHECK(registry.get_tool_count() == 48);", "CHECK(registry.get_tool_count() == 73);"),
    8413: ("CHECK(registry.get_visible_tool_count(true) == 35);", "CHECK(registry.get_visible_tool_count(true) == 50);"),
    8414: ("CHECK(registry.get_visible_tool_count(false) == 48);", "CHECK(registry.get_visible_tool_count(false) == 73);"),
    # TASK-026 replaced the reference's `no_log_file` marker with the honest
    # empty source block (`source: "none"`); the dedicated TASK-026 case in this
    # same file (line 3410) already asserts "none".
    3208: ('CHECK((String)((Dictionary)absent_result)["source"] == "no_log_file");',
           'CHECK((String)((Dictionary)absent_result)["source"] == "none");'),
}

text = io.open(PATH, encoding="utf-8").read()
lines = text.split("\n")
changed = 0
for no, (old, new) in sorted(SITES.items()):
    if old not in lines[no - 1]:
        raise SystemExit("FATAL: line %d does not contain the expected text.\n  have: %s\n  want: %s" % (no, lines[no - 1], old))
    lines[no - 1] = lines[no - 1].replace(old, new, 1)
    changed += 1
out = "\n".join(lines)
io.open(PATH, "w", encoding="utf-8", newline="").write(out)
print("rewrote %d stale assertions in %s (%d -> %d bytes)" % (changed, PATH, len(text), len(out)))
