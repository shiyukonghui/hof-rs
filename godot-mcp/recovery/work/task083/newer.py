# -*- coding: utf-8 -*-
"""TASK-083: for one file, show the tree-only ('newer') blocks - the content the
backup does not have - so the splice can be judged instead of trusted."""
import io
import os
import sys

sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083")
import splice  # noqa: E402


def main():
    rel = sys.argv[1]
    p = os.path.join(splice.TREE, rel.replace("/", os.sep))
    b = os.path.join(splice.BAK, rel.replace("/", os.sep))
    tree = splice.read_plain(p)
    bak = splice.read_plain(b)
    import difflib
    sm = difflib.SequenceMatcher(None, tree, bak, autojunk=False)
    print("tree=%d bak=%d" % (len(tree), len(bak)))
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("delete", "replace") and i2 > i1:
            print("  tree %d-%d (%s, %d lines):" % (i1 + 1, i2, tag, i2 - i1))
            for k in range(i1, min(i2, i1 + 6)):
                print("      %5d| %s" % (k + 1, tree[k][:110]))
            if i2 - i1 > 6:
                print("      ... (%d more)" % (i2 - i1 - 6))


if __name__ == "__main__":
    main()
