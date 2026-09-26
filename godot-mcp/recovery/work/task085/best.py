# -*- coding: utf-8 -*-
"""Try every base mode for a file and report which reconstruction best matches
the recorded read skeleton of the target revision.

usage: python best.py [subpath ...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evfetch as E  # noqa: E402
import rebuild as RB  # noqa: E402

ROOT = r"H:\rebuild\godot"

FILES = [
    r"modules\mcp_server\tools\running_game_test_execution.cpp",
    r"modules\mcp_server\tools\editor_write_scene_editor.cpp",
    r"modules\mcp_server\tools\project_write_resource_scene.cpp",
    r"modules\mcp_server\tools\running_game_node_write.cpp",
    r"modules\mcp_server\tools\tool_helpers.cpp",
    r"modules\mcp_server\tools\editor_node_write.cpp",
    r"modules\mcp_server\tools\project.cpp",
    r"modules\mcp_server\tools\project_validate_scripts.cpp",
]


def score(sub, mode):
    try:
        buf, info = RB.run(sub, mode, verbose=False)
    except SystemExit as e:
        return None, str(e)
    lines = buf.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    skel, rev = E.skeleton(sub)
    # shift-tolerant: how many recorded lines appear nowhere in the buffer, and
    # how many line numbers agree when the best constant shift is applied
    have = {}
    for i, l in enumerate(lines):
        have.setdefault(l.rstrip("\r"), []).append(i + 1)
    absent = sum(1 for no in skel if skel[no].rstrip("\r") not in have)
    best = -1
    for off in range(-140, 141):
        agree = 0
        for no in skel:
            if no + off < 1 or no + off > len(lines):
                continue
            if lines[no + off - 1].rstrip("\r") == skel[no].rstrip("\r"):
                agree += 1
        best = max(best, agree)
    bad = len(skel) - best
    return (len(lines), bad, len(skel), rev, len(info["breaks"]), len(info["refused"]), absent), None


def main():
    files = sys.argv[1:] or FILES
    for sub in files:
        tree = E.lines_of(os.path.join(ROOT, sub))
        skel, rev = E.skeleton(sub)
        badt = 0
        for no in sorted(skel):
            if no < 1 or no > len(tree) or tree[no - 1].rstrip("\r") != skel[no].rstrip("\r"):
                badt += 1
        print("== %s" % os.path.basename(sub))
        print("   %-10s lines=%-6d mismatch=%-5d/%d target=%s" % ("TREE", len(tree), badt, len(skel), rev))
        modes = ["write"]
        fulls = RB.full_reads(sub)
        if fulls:
            modes.append("read")
            modes.append("rev:%d" % fulls[-1][0])
        for m in modes:
            r, err = score(sub, m)
            if err:
                print("   %-10s %s" % (m, err))
                continue
            n, bad, cov, rv, brk, ref = r
            print("   %-10s lines=%-6d mismatch=%-5d/%d target=%s breaks=%d refused=%d" % (
                m, n, bad, cov, rv, brk, ref))


if __name__ == "__main__":
    main()
