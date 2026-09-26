# -*- coding: utf-8 -*-
"""TASK-083 recon 7: map the tree file onto the placed reconstruction so the
real gaps (as opposed to reordering) become visible."""
import io
import os

OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"
TREE = r"H:\rebuild\godot\modules\mcp_server\mcp_server.cpp"


def rd(p, strip_no):
    out = []
    with io.open(p, "r", encoding="utf-8", errors="replace", newline="") as f:
        for line in f:
            line = line.rstrip("\r\n")
            out.append(line)
    return out


def main():
    tree = rd(TREE, False)
    placed = []
    for line in rd(os.path.join(OUT, "mcp_server.placed.txt"), False):
        placed.append(line.split("| ", 1)[1] if "| " in line else line)
    # sequential greedy alignment
    cur = 0
    mapping = []
    unmatched = []
    for ti, t in enumerate(tree, 1):
        if t.strip() == "":
            mapping.append((ti, None, t))
            continue
        found = None
        for pi in range(cur, len(placed)):
            if placed[pi] == t:
                found = pi
                break
        if found is None:
            # search backwards for a re-order
            back = None
            for pi in range(0, cur):
                if placed[pi] == t:
                    back = pi
                    break
            unmatched.append((ti, t, "reorder->%d" % (back + 1) if back is not None else "ABSENT"))
            mapping.append((ti, None, t))
        else:
            mapping.append((ti, found + 1, t))
            cur = found + 1
    covered = set(m[1] for m in mapping if m[1] is not None)
    gaps = [i for i in range(1, len(placed) + 1) if i not in covered]
    rng = []
    for g in gaps:
        if rng and g == rng[-1][1] + 1:
            rng[-1][1] = g
        else:
            rng.append([g, g])
    print("tree lines=%d placed lines=%d" % (len(tree), len(placed)))
    print("reordered/absent tree lines: %d" % len(unmatched))
    for ti, t, why in unmatched[:40]:
        print("   tree:%-4d %-12s %s" % (ti, why, t[:90]))
    print("placed line ranges NOT covered by tree: %s" % rng)
    with io.open(os.path.join(OUT, "map_tree_to_placed.txt"), "w", encoding="utf-8", newline="\n") as f:
        for ti, pi, t in mapping:
            f.write("tree%-4d -> placed%-4s | %s\n" % (ti, pi if pi else "-", t))


if __name__ == "__main__":
    main()
