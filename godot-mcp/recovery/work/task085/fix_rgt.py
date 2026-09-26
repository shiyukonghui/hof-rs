# -*- coding: utf-8 -*-
"""TASK-085 fix for tools/running_game_test_execution.cpp.

Base: the strict replay from the recorded whole-file write seq=770 plus every
later edit whose recorded result was not an error (events-write + events-edit,
ruling A).  It reproduces the target revision at offset 0 from line 1 to ~634
(see align.py) and contains coherent tick()/TestScenarioTask code, which the tree
copy has lost to a splice.

Two recorded pieces the replay does not carry are added from recorded text:
  * the `scene_path` refusal block - the read windows of rev949 record lines
    627-638 verbatim (they are ABSENT from the replay);
  * the registration span - `scripts/gen_b2_game_schema.py --group
    running_game_test_execution` regenerates it from the authoritative
    `docs/tools_list.renamed.json`, which is what the block itself says it is.

usage: python fix_rgt.py [--apply]
"""
import io
import subprocess
import sys

sys.path.insert(0, ".")
import evfetch as E  # noqa: E402

SUB = r"modules\mcp_server\tools\running_game_test_execution.cpp"
TREE = r"H:\rebuild\godot\modules\mcp_server\tools\running_game_test_execution.cpp"
SRC = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task085\rep_rgt.cpp"


def main():
    skel, rev = E.skeleton(SUB)
    lines = E.lines_of(SRC)
    print("replay %d lines, skeleton rev=%s" % (len(lines), rev))

    # The replay's scene_path block is the TASK-032 D4 variant ("the branch is
    # gone").  The later revision put the tailored refusal back, and the read
    # window of rev939 t=1790142615420 records it verbatim at lines 627-647.
    win = None
    for r in E.reads(SUB):
        if r.get("totalLines") == 939 and r.get("time") == 1790142615420:
            win = {no: txt.rstrip("\r") for no, txt in r.get("lines") or []}
    assert win, "rev939 t=1790142615420 window not found"
    block = [win[n] for n in range(627, 648)]
    assert block[0].strip().startswith("// `scene_path` belongs to the editor-side"), block[0]
    assert block[-1].strip() == "", repr(block[-1])
    assert 'not supported by the game-scope runner' in "\n".join(block)

    anchor = block[0]
    idx = [i for i, l in enumerate(lines) if l == anchor]
    assert len(idx) == 1, "anchor occurs %d times in the replay" % len(idx)
    start = idx[0]
    assert lines[start + 13].strip() == "", lines[start + 13]
    assert lines[start + 14].strip() == "Vector<ScenarioStep> steps;", lines[start + 14]
    print("replacing replay lines %d-%d (TASK-032 D4 comment) with the recorded %d-line refusal block"
          % (start + 1, start + 14, len(block)))
    lines = lines[:start] + block + lines[start + 14:]

    text = "\n".join(lines) + "\n"
    if "--apply" not in sys.argv:
        print("(dry run; pass --apply to write)")
        return
    with io.open(TREE, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote %s (%d lines), running the schema generator in place" % (TREE, len(lines)))
    r = subprocess.run(
        [sys.executable, "-X", "utf8",
         r"H:\rebuild\godot\modules\mcp_server\scripts\gen_b2_game_schema.py",
         "--group", "running_game_test_execution", "--in-place", TREE],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("generator exit=%d" % r.returncode)
    print((r.stdout or "").strip()[:400])
    if r.returncode != 0:
        raise SystemExit("generator failed: %s" % (r.stderr or "")[:400])
    out = E.lines_of(TREE)
    print("final: %d lines (target %s)" % (len(out), rev))


if __name__ == "__main__":
    main()
