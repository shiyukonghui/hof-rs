# -*- coding: utf-8 -*-
"""TASK-084 fix 1: editor_node_batch_write.cpp.

The tree's lines 75-190 were filled from a pre-TASK-051 revision (rev598's
`_batch_error_entry` / `_rollback_envelope` / `_attach_batch_envelope` /
headless `_transaction_fail`), which is exactly why the file reported

  C2267/C2601 `_later_element_requesting` ... line 133: `{` has no match
  C3861 `_pending_path_for` / `_pending_path_matches`
  C2039 `_PendingNode` has no member `parent_from_batch`

The recorded edit `seq=267` (time 1790239120501) replaced the 9-line
`struct _PendingNode` with a 116-line block that is the *whole* head the final
revision has: the struct with `parent_from_batch`, `_pending_path_for`,
`_pending_path_matches`, `_resolve_batch_parent` and `_later_element_requesting`.

Tree 75-190 is 116 lines and its tail (151-190) is byte-identical to the tail of
that recorded block, so the block lands at 75-190 exactly and no text is guessed:
this is recorded text, replayed at its recorded position.

usage: python fix_batch_head.py [--write]
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ev import load  # noqa: E402

P = r"H:\rebuild\godot\modules\mcp_server\tools\editor_node_batch_write.cpp"
SUB = "modules\\mcp_server\\tools\\editor_node_batch_write.cpp"


def read_lines(path):
    with io.open(path, "r", encoding="utf-8", errors="strict") as f:
        return f.read().split("\n")


def main():
    write = "--write" in sys.argv
    L = read_lines(P)
    if L and L[-1] == "":
        L = L[:-1]
    assert L[74] == "struct _PendingNode {", repr(L[74])
    assert L[83] == "};", repr(L[83])
    assert L[189] == "}", repr(L[189])
    assert L[190] == "", repr(L[190])
    assert L[191].startswith('// `{"index":N'), repr(L[191])

    blk = None
    for r in load(SUB):
        if str(r.get("seq")) == "267":
            blk = r["new"].split("\n")
    assert blk is not None, "seq=267 not found"
    if blk and blk[-1] == "":
        blk = blk[:-1]
    assert len(blk) == 116, len(blk)
    # the head of the recorded block must be the struct, its tail the function we
    # already have verbatim at 151-190 -> the splice point is proven, not assumed.
    assert blk[0] == "struct _PendingNode {"
    assert blk[-1] == "}"
    assert blk[-29:] == L[161:190], "tail misalignment"
    print("replacing tree lines 75-190 (116) with recorded seq=267 NEW (116)")
    new = L[:74] + blk + L[190:]
    print("lines %d -> %d" % (len(L), len(new)))
    if write:
        with io.open(P, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(new) + "\n")
        print("written")


if __name__ == "__main__":
    main()
