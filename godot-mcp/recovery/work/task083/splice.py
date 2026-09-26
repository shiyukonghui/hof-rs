# -*- coding: utf-8 -*-
"""TASK-083 tool 1: restore gap-collapsed reconstruction files by splicing the
missing spans back in from the TASK-044 backup.

Rule (strict, conservative):
  * walk difflib opcodes between tree (newer, gap-collapsed) and backup (older, complete)
  * 'equal'   -> tree text
  * 'delete'  -> tree text (content that is newer than the backup)
  * 'insert'  -> BACKUP text (content the reconstruction dropped)
  * 'replace' -> tree text normally; if the backup block is longer by >= REPLACE_MIN,
                 append the backup block as well (it may hold dropped lines)

Read-only unless --write is given; never touches F:.
"""
import difflib
import io
import json
import os
import sys

TREE = r"H:\rebuild\godot\modules\mcp_server"
BAK = r"C:\Users\wyl\AppData\Local\Temp\mcp044-module-backup\mcp_server"
OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"

REPLACE_MIN = 8


def read_plain(path):
    with io.open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        return [ln.rstrip("\r\n") for ln in f]


def balance(lines):
    """brace/paren balance with Godot raw-string awareness."""
    depth_c = depth_p = 0
    state = None
    delim = None
    for src in lines:
        i = 0
        n = len(src)
        while i < n:
            c = src[i]
            nx = src[i + 1] if i + 1 < n else ""
            if state is None:
                if c == "/" and nx == "/":
                    break
                if c == "/" and nx == "*":
                    state = "block"
                    i += 2
                    continue
                if c == "R" and nx == '"':
                    j = src.find("(", i + 2)
                    if j != -1:
                        delim = src[i + 2:j]
                        state = "raw"
                        i = j + 1
                        continue
                if c == '"':
                    state = "str"
                    i += 1
                    continue
                if c == "'":
                    state = "chr"
                    i += 1
                    continue
                if c == "{":
                    depth_c += 1
                elif c == "}":
                    depth_c -= 1
                elif c == "(":
                    depth_p += 1
                elif c == ")":
                    depth_p -= 1
                i += 1
                continue
            if state == "block":
                if c == "*" and nx == "/":
                    state = None
                    i += 2
                    continue
                i += 1
                continue
            if state == "raw":
                if c == ")" and src[i + 1:i + 1 + len(delim)] == delim and src[i + 1 + len(delim):i + 2 + len(delim)] == '"':
                    state = None
                    i += 2 + len(delim)
                    continue
                i += 1
                continue
            if state in ("str", "chr"):
                if c == "\\":
                    i += 2
                    continue
                if (state == "str" and c == '"') or (state == "chr" and c == "'"):
                    state = None
                i += 1
                continue
    return depth_c, depth_p, state


def splice(tree, bak, replace_min=REPLACE_MIN):
    sm = difflib.SequenceMatcher(None, tree, bak, autojunk=False)
    out = []
    notes = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.extend(tree[i1:i2])
        elif tag == "delete":
            out.extend(tree[i1:i2])
        elif tag == "insert":
            out.extend(bak[j1:j2])
            notes.append(("insert", j1 + 1, j2, j2 - j1))
        elif tag == "replace":
            out.extend(tree[i1:i2])
            extra = (j2 - j1) - (i2 - i1)
            if extra >= replace_min:
                out.extend(bak[j1:j2])
                notes.append(("replace+", j1 + 1, j2, extra))
    return out, notes


def run(rel, write=False, replace_min=REPLACE_MIN, quiet=False):
    p = os.path.join(TREE, rel.replace("/", os.sep))
    b = os.path.join(BAK, rel.replace("/", os.sep))
    if not os.path.exists(p) or not os.path.exists(b):
        return None
    tree = read_plain(p)
    bak = read_plain(b)
    if bak and bak[-1] == "":
        bak = bak[:-1]  # keep it clean; drop the trailing empty split
    merged, notes = splice(tree, bak, replace_min)
    bc, bp, bs = balance(tree)
    ac, ap, ast = balance(merged)
    info = {
        "rel": rel,
        "tree_lines": len(tree),
        "bak_lines": len(bak),
        "merged_lines": len(merged),
        "inserted_lines": sum(n[3] for n in notes),
        "notes": notes,
        "balance_tree": [bc, bp, bs],
        "balance_merged": [ac, ap, ast],
    }
    if write:
        dst = p
        with io.open(dst, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(merged) + "\n")
        info["written"] = dst
    return info, merged


if __name__ == "__main__":
    rels = read_plain(sys.argv[1]) if len(sys.argv) > 1 else []
    do_write = "--write" in sys.argv
    rmin = int(os.environ.get("REPLACE_MIN", REPLACE_MIN))
    report = []
    for rel in rels:
        rel = rel.strip()
        if not rel:
            continue
        r = run(rel, write=do_write, replace_min=rmin)
        if r is None:
            print("%-45s SKIP (missing)" % rel)
            continue
        info, _ = r
        print("%-45s tree=%-5d bak=%-5d merged=%-5d ins=%-5d bal %s -> %s" % (
            rel, info["tree_lines"], info["bak_lines"], info["merged_lines"],
            info["inserted_lines"], info["balance_tree"], info["balance_merged"]))
        report.append(info)
    with io.open(os.path.join(OUT, "splice-report.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=1))
