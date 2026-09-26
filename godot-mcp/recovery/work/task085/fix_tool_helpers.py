# -*- coding: utf-8 -*-
"""TASK-085 ruling (B) dedup for tools/tool_helpers.cpp.

The tree carries two generations of the `serialize_variant` switch cases.

Evidence (recorded read windows, by absolute line number, of the target file):

  * rev2487 t=1790147427099, lines 125-154: VECTOR3I at 140, then COLOR at 148,
    with NOTHING in between.
  * rev2487 t=1790147836781, lines 184-213: the TASK-024b comment ends at 185,
    then VECTOR4 186, VECTOR4I 195, RECT2I 204, PACKED_BYTE_ARRAY 213.
  * events-edit seq=853 t=1790147840771 (the LAST edit touching this region, four
    seconds after that read) inserts the TASK-033 comment and QUATERNION directly
    after the VECTOR4I case.

So the kept generation is: the block that follows the TASK-024b comment
(VECTOR4, VECTOR4I, + QUATERNION, RECT2I, PACKED_*).  Two stale blocks are
dropped: the VECTOR4/VECTOR4I copy that sits between VECTOR3I and COLOR, and the
second, earlier `TASK-024 E-3` PACKED_* copy that sits between ARRAY and OBJECT.

Nothing is invented: every kept line is already in the file.

usage: python fix_tool_helpers.py [--apply]
"""
import io
import sys

TREE = r"H:\rebuild\godot\modules\mcp_server\tools\tool_helpers.cpp"

# (first, last) inclusive line numbers of the blocks to drop / move, 1-based.
DROP_HEAD = (171, 193)
MOVE = (194, 215)
DROP_TAIL = (390, 515)
AFTER = 271  # the VECTOR4I case that the move lands behind


def main():
    t = io.open(TREE, encoding="utf-8", errors="replace").read().split("\n")
    if t and t[-1] == "":
        t.pop()
    n = len(t)
    print("tree lines: %d" % n)

    head = t[DROP_HEAD[0] - 1:DROP_HEAD[1]]
    tail = t[DROP_TAIL[0] - 1:DROP_TAIL[1]]
    moved = t[MOVE[0] - 1:MOVE[1]]
    anchor = t[AFTER - 1]

    # assertions: the blocks are what we think they are
    assert head[0].strip() == "case Variant::VECTOR4: {", head[0]
    assert head[-1].strip() == "}", head[-1]
    assert "TASK-024 E-3: `Vector4` had no branch" in "\n".join(head)
    assert moved[0].strip().startswith("// ---")
    assert "TASK-033 (B5 batch 1" in "\n".join(moved)
    assert moved[-1].strip() == "}", moved[-1]
    assert moved[-2].strip() == "return out;", moved[-2]
    assert "case Variant::QUATERNION: {" in "\n".join(moved)
    assert "TASK-024 E-3: the packed containers" in "\n".join(tail), "tail marker missing"
    assert tail[0].strip().startswith("// ---"), tail[0]
    assert tail[-1].strip() == "}", tail[-1]
    assert t[DROP_TAIL[1]].strip() == "case Variant::OBJECT: {", t[DROP_TAIL[1]]
    assert anchor.strip() == "}", "anchor line %d is not a closing brace: %r" % (AFTER, anchor)
    assert t[AFTER - 2].strip() == "return out;", t[AFTER - 2]
    assert t[AFTER - 1 - 8].strip() == "case Variant::VECTOR4I: {", t[AFTER - 9]

    out = []
    for i, line in enumerate(t, 1):
        if DROP_HEAD[0] <= i <= DROP_HEAD[1]:
            continue
        if MOVE[0] <= i <= MOVE[1]:
            continue
        if DROP_TAIL[0] <= i <= DROP_TAIL[1]:
            continue
        out.append(line)
        if i == AFTER:
            out.extend(moved)

    print("dropped head %d lines, dropped tail %d lines, kept %d moved lines"
          % (len(head), len(tail), len(moved)))
    print("new line count: %d" % len(out))
    if "--apply" not in sys.argv:
        print("(dry run; pass --apply to write)")
        return
    text = "\n".join(out) + "\n"
    with io.open(TREE, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    back = io.open(TREE, encoding="utf-8", errors="replace").read()
    assert back == text, "read-back mismatch"
    print("wrote %s, read-back OK" % TREE)


if __name__ == "__main__":
    main()
