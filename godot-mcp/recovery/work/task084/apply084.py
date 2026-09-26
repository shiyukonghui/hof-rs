# -*- coding: utf-8 -*-
"""TASK-084 fix A+B (evidence-verified, no invented code).

A. tools/project_cross_scene_write.h
   The file's own newest recorded revision (rev156) has, right after the
   `core/variant/variant.h` include and before the TASK-018 comment:

       (blank)
       // Only ever used through a pointer by the declaration below, so the class name is
       // forward declared instead of dragging `scene/` into this header.
       class Node;

   i.e. exactly the 4 lines the tree lost.  Without them `Node` is undeclared at
   line 118 and MSVC then invents `int MCPTools::Node`, which cascades into
   `int MCPTools::String` / `int MCPTools::Variant` -> 87 errors in
   tool_helpers.h, 22 in running_game_node_write.h and 12 here, all in the
   translation units that include this header before those.

B. tools/editor_node_batch_write.cpp
   Reconstructed from the recorded whole-file write seq=274 plus every later
   recorded edit (`events-edit.jsonl`), assembled on the rev766 read-window
   skeleton.  Every difference from the tree must fall inside an *uncovered* run
   of rev766, which is asserted before anything is written.

usage: python apply084.py [--write]
"""
import difflib
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rec  # noqa: E402

ROOT = r"H:\rebuild\godot"
WRITE = "--write" in sys.argv
BACKUP = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task084\backup084"


def read(sub):
    with io.open(os.path.join(ROOT, sub), "r", encoding="utf-8", errors="strict") as f:
        s = f.read()
    assert "\ufffd" not in s, "replacement char in %s" % sub
    return s


def write(sub, text):
    os.makedirs(BACKUP, exist_ok=True)
    orig = read(sub)
    bpath = os.path.join(BACKUP, sub.replace("\\", "__"))
    with io.open(bpath, "w", encoding="utf-8", newline="\n") as f:
        f.write(orig)
    with io.open(os.path.join(ROOT, sub), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("   wrote %s (backup %s, %d -> %d bytes)" % (sub, bpath, len(orig.encode()), len(text.encode())))


# ---------------------------------------------------------------- A
CROSS = "modules\\mcp_server\\tools\\project_cross_scene_write.h"


def fix_cross():
    print("A. %s" % CROSS)
    L = read(CROSS).split("\n")
    if L and L[-1] == "":
        L = L[:-1]
    L = L[:-1]
    assert L[35] == "", repr(L[35])
    assert L[36].startswith("// TASK-018 section 3"), repr(L[36])
    assert "class Node;" not in "\n".join(L[:120]), "already present"
    ins = [
        "// Only ever used through a pointer by the declaration below, so the class name is",
        "// forward declared instead of dragging `scene/` into this header.",
        "class Node;",
        "",
    ]
    new = L[:36] + ins + L[36:]
    assert new[36].startswith("// Only ever used")
    assert new[38] == "class Node;"
    assert new[39] == ""
    assert new[40].startswith("// TASK-018 section 3")
    print("   inserting 4 lines after line 36 (%d -> %d)" % (len(L), len(new)))
    if WRITE:
        write(CROSS, "\n".join(new) + "\n")


# ---------------------------------------------------------------- B
BATCH = "modules\\mcp_server\\tools\\editor_node_batch_write.cpp"


def fix_batch():
    print("B. %s" % BATCH)
    t = read(BATCH).split("\n")
    if t and t[-1] == "":
        t = t[:-1]
    got, info = rec.assemble_best(BATCH, verbose=True)
    assert len(got) == info["rev"] == 766, len(got)
    d, p, _ = rec._bal(got)
    assert (d, p) == (0, 0), (d, p)
    gaps = info["gaps"]
    hunks = [h for h in difflib.SequenceMatcher(None, t, got, autojunk=False).get_opcodes() if h[0] != "equal"]
    for tag, i1, i2, j1, j2 in hunks:
        inside = any(g[0] <= i1 + 1 <= g[1] for g in gaps)
        print("   hunk %-7s tree[%d:%d] -> rec[%d:%d]  inside-uncovered=%s" % (tag, i1 + 1, i2, j1 + 1, j2, inside))
        assert inside, "hunk at tree line %d is outside the uncovered runs -> refuse" % (i1 + 1)
    budget = sum(g[1] - g[0] + 1 for g in gaps) + 8
    changed = sum(max(i2 - i1, j2 - j1) for _t, i1, i2, j1, j2 in hunks)
    print("   %d hunks, %d changed lines, uncovered-line budget %d" % (len(hunks), changed, budget))
    assert changed <= budget
    if WRITE:
        write(BATCH, "\n".join(got) + "\n")


if __name__ == "__main__":
    print("mode: %s" % ("WRITE" if WRITE else "dry-run"))
    fix_cross()
    fix_batch()
