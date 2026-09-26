# -*- coding: utf-8 -*-
"""TASK-083: show the spans splice.py would insert for one file."""
import io
import os
import sys

sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083")
import splice  # noqa: E402

OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"


def main():
    rel = sys.argv[1]
    rmin = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    r = splice.run(rel, write=False, replace_min=rmin)
    info, merged = r
    print("%s: tree=%d bak=%d merged=%d ins=%d bal %s -> %s" % (
        rel, info["tree_lines"], info["bak_lines"], info["merged_lines"],
        info["inserted_lines"], info["balance_tree"], info["balance_merged"]))
    print("--- inserted spans ---")
    for kind, a, b, n in info["notes"]:
        print("  [%s] backup %d-%d (%d lines)" % (kind, a, b, n))
        for i in range(a, min(b, a + 3) + 1):
            print("       %4d| %s" % (i, splice.read_plain(os.path.join(splice.BAK, rel.replace("/", os.sep)))[i - 1][:100]))
        if b - a > 3:
            print("       ...")
    name = os.path.basename(rel.replace("\\", "_"))
    with io.open(os.path.join(OUT, name + ".spliced-dry.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(merged) + "\n")


if __name__ == "__main__":
    main()
