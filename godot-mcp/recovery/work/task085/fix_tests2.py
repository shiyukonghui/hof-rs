# -*- coding: utf-8 -*-
"""TASK-085: the last three repairs in tests/test_mcp_server.h.

1. `list_files_recursive` (defined inside `namespace TestMCPServer`) is called
   unqualified at five sites that sit outside that namespace.  Qualified with
   the spelling the file's own other sites use
   (`TestMCPServer::list_files_recursive`, e.g. test_mcp_server.h:9128).

2. `CHECK(payload["created"] == true)` / `CHECK(payload["deleted"] == true)`
   do not compile: `Variant` has no `operator==(bool)`, so doctest's
   decomposition fails (C2678).  The recorded rev9381-9411 spelling is
   `CHECK((bool)payload["created"]);`; the same cast is applied to `deleted`.

3. The five `editor_read_scene_inspector` TEST_CASEs appear TWICE.  The copy at
   2941-3583 is the later one (48 game-scope tools, 76 editor-process tools -
   the counts the current registration produces) and the copy at 9133-9487 is
   the earlier one (19 / 26).  Ruling (B): keep the later generation, drop the
   earlier.  The unique TEST_CASE that follows it (9489, "the editor inspectors
   never write to the project") stays: it takes `EDITOR_INSPECTOR_TOOLS` from
   the surviving anonymous namespace at 2942.

usage: python fix_tests2.py [--apply]
"""
import io
import sys

sys.path.insert(0, ".")
import evfetch as E  # noqa: E402

TREE = r"H:\rebuild\godot\modules\mcp_server\tests\test_mcp_server.h"


def main():
    lines = E.lines_of(TREE)
    print("test_mcp_server.h: %d lines" % len(lines))

    # 1. qualify list_files_recursive
    n = 0
    for i, l in enumerate(lines):
        s = l
        for pre in ("\t", "\t\t", "\t\t\t", ""):
            if (pre + "list_files_recursive(") in s and ("TestMCPServer::list_files_recursive(" not in s):
                s = s.replace(pre + "list_files_recursive(", pre + "TestMCPServer::list_files_recursive(")
        if s != l:
            lines[i] = s
            n += 1
    print("1: qualified %d `list_files_recursive` call(s)" % n)
    assert n >= 5, "expected at least 5 sites, found %d" % n

    # 2. the two bool assertions
    m = 0
    for i, l in enumerate(lines):
        if l.strip() == 'CHECK(payload["created"] == true);':
            lines[i] = l.replace('CHECK(payload["created"] == true);', 'CHECK((bool)payload["created"]);')
            m += 1
        elif l.strip() == 'CHECK(payload["deleted"] == true);':
            lines[i] = l.replace('CHECK(payload["deleted"] == true);', 'CHECK((bool)payload["deleted"]);')
            m += 1
    print("2: rewrote %d bool assertion(s)" % m)
    assert m == 2, "expected 2 assertions, found %d" % m

    # 3. drop the earlier duplicate block
    starts = [i for i, l in enumerate(lines)
              if l.strip() == 'TEST_CASE("[MCPServer] the editor_read_scene_inspector group is editor-only") {']
    assert len(starts) == 2, "editor-only TEST_CASE copies: %d" % len(starts)
    later = starts[0]
    earlier = starts[1]
    # the shared anonymous namespace that carries EDITOR_INSPECTOR_TOOLS
    ns = [i for i, l in enumerate(lines) if i < earlier and l.strip() == "namespace {"]
    beg = ns[-1]
    # its comment header
    while beg > 0 and lines[beg - 1].strip().startswith("//"):
        beg -= 1
    # and the TEST_CASE that ends just before it
    end_of_prev = beg - 1
    while end_of_prev > 0 and lines[end_of_prev].strip() == "":
        end_of_prev -= 1
    # the last duplicate TEST_CASE in the earlier block, walked to its close
    others = [i for i, l in enumerate(lines)
              if l.strip().startswith("TEST_CASE(") and earlier < i and l.strip() != lines[earlier].strip()]
    area = [i for i, l in enumerate(lines) if i > earlier and l.strip().startswith("TEST_CASE(")]
    last_tc = [i for i in area if i < beg + 400]
    # walk each TEST_CASE to its close, take the last one's end
    j = area[0]
    ends = []
    k = 0
    while k < len(area):
        st = area[k]
        depth = 0
        for j2 in range(st, len(lines)):
            s = lines[j2].split("//", 1)[0]
            depth += s.count("{") - s.count("}")
            if j2 > st and depth == 0:
                ends.append((st, j2))
                break
        k += 1
    dup_end = None
    for st, en in ends:
        if st > earlier and len([1 for s2, e2 in ends if s2 > earlier and s2 <= en]) == 0:
            dup_end = en
    # simpler: the earlier block ends where the next (unique) TEST_CASE that is
    # NOT in the duplicate-name list begins
    dupnames = {
        'TEST_CASE("[MCPServer] the editor_read_scene_inspector group is editor-only") {',
        'TEST_CASE("[MCPServer] editor_get_errors reports the ERROR lines of the log tail") {',
        'TEST_CASE("[MCPServer] editor_get_output_log filters the tail case sensitively") {',
        'TEST_CASE("[MCPServer] the editor UI inspectors refuse cleanly without an editor UI") {',
        'TEST_CASE("[MCPServer] the edited-scene inspectors need an open scene and validate their arguments") {',
    }
    cut = None
    for st, en in ends:
        if st > earlier and lines[st].strip() in dupnames:
            cut = en
            break
    for st, en in ends:
        if st > earlier and cut is not None and en > cut and lines[st].strip() in dupnames:
            cut = en
    print("3: earlier duplicate block = lines %d-%d (%d lines); later block's editor-only case at %d"
          % (beg + 1, cut + 1, cut - beg + 1, later + 1))
    # everything strictly between the end of the previous TEST_CASE and the next
    # unique TEST_CASE must be part of the earlier copy
    nxt = [i for i, l in enumerate(lines) if i > cut and l.strip().startswith("TEST_CASE(")]
    assert nxt, "no TEST_CASE after the duplicate block"
    assert lines[nxt[0]].strip().startswith('TEST_CASE("[MCPServer] the editor inspectors never write to the project")'), lines[nxt[0]].strip()
    lines = lines[:beg] + lines[cut + 1:]
    print("   dropped; now %d lines" % len(lines))

    if "--apply" not in sys.argv:
        print("(dry run; pass --apply to write)")
        return
    text = "\n".join(lines) + "\n"
    with io.open(TREE, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    assert io.open(TREE, encoding="utf-8", errors="replace").read() == text
    print("wrote %s (%d lines), read-back OK" % (TREE, len(lines)))


if __name__ == "__main__":
    main()
