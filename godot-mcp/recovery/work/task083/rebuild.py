# -*- coding: utf-8 -*-
"""TASK-083 tool 5: faithful per-file reconstruction.

The 2A/2B reconstruction emitted only the lines its read windows covered and
dropped every uncovered line, so the tree copy of a file is a *gap-collapsed*
splice whose fragments can even belong to different revisions.  This tool
rebuilds one file properly:

  1. base := the complete read window (offset 1, contiguous 1..totalLines) at the
     highest revision that has one.  A complete window is a coherent snapshot of
     the whole file at that moment - everything the gap-collapsed tree is not.
     If a complete window exists at the reconstruction's target revision, that is
     the file, verbatim.
  2. then every read window whose revision is *higher* than the base's is applied
     in ascending revision order, anchored by content (not by line number):
     the window replaces the base span it covers, because it is newer.
  3. finally the TASK-044 backup fills any span that is still absent from the
     result (difflib 'insert' spans only - never overwriting newer text).

Read-only unless --write.  Nothing outside H:\\rebuild\\godot\\modules\\mcp_server
and this work directory is touched.
"""
import difflib
import io
import json
import os
import sys
from collections import defaultdict

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
TREE = r"H:\rebuild\godot\modules\mcp_server"
BAK = r"C:\Users\wyl\AppData\Local\Temp\mcp044-module-backup\mcp_server"
OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"


def norm(p):
    return p.replace("/", "\\").lower()


def read_plain(path):
    with io.open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        return [ln.rstrip("\r\n") for ln in f]


def load_reads():
    per = defaultdict(list)
    with io.open(os.path.join(IDX, "events-read.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            p = norm(r.get("path", ""))
            if "modules\\mcp_server\\" not in p:
                continue
            per[p.split("modules\\mcp_server\\", 1)[1]].append(r)
    return per


def load_targets():
    recs = {}
    with io.open(os.path.join(IDX, "reconstruction.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                r = json.loads(line)
                if r.get("rel", "").startswith("modules\\mcp_server\\"):
                    recs[r["rel"].split("modules\\mcp_server\\", 1)[1]] = r
    return recs


def complete_windows(rows):
    out = []
    for r in rows:
        rev = r.get("totalLines") or 0
        lns = r.get("lines") or []
        nos = sorted(x[0] for x in lns)
        if rev and nos and nos[0] == 1 and nos[-1] == rev and len(nos) == rev:
            out.append((rev, r.get("time", 0), [t for _, t in sorted(lns)]))
    return out


def partial_windows(rows):
    out = []
    for r in rows:
        rev = r.get("totalLines") or 0
        lns = r.get("lines") or []
        nos = sorted(x[0] for x in lns)
        if rev and lns and not (nos[0] == 1 and nos[-1] == rev and len(nos) == rev):
            out.append((rev, r.get("time", 0), [t for _, t in sorted(lns)]))
    return out


def apply_window(base, win, search=400):
    """Replace the base span that `win` covers with `win` (win is newer)."""
    if not win:
        return base, "empty"
    if not base:
        return list(win), "seeded"
    # locate win[0] in base
    first, last = win[0], win[-1]
    # candidate anchors for the head
    cands = [i for i in range(len(base)) if base[i] == first]
    if not cands:
        sm = difflib.SequenceMatcher(None, [first], base, autojunk=False)
        m = sm.find_longest_match(0, 1, 0, len(base))
        if m.size == 0:
            return base, "no-anchor"
        cands = [m.b]
    anchor = cands[0]
    # locate win[-1] at or after the anchor
    end = None
    span = max(1, len(win) * 3 + search)
    for i in range(anchor, min(len(base), anchor + span)):
        if base[i] == last:
            end = i + 1
            break
    if end is None:
        sm = difflib.SequenceMatcher(None, [last], base[anchor:anchor + span], autojunk=False)
        m = sm.find_longest_match(0, 1, 0, min(len(base) - anchor, span))
        if m.size == 0:
            end = min(len(base), anchor + len(win))
        else:
            end = anchor + m.b + 1
    return base[:anchor] + list(win) + base[end:], "replaced %d..%d" % (anchor, end)


def backup_fill(out, bak):
    sm = difflib.SequenceMatcher(None, out, bak, autojunk=False)
    res = []
    ins = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("equal", "delete", "replace"):
            res.extend(out[i1:i2])
        if tag == "insert":
            res.extend(bak[j1:j2])
            ins += j2 - j1
    return res, ins


def rebuild(rel, reads, recs, do_backup=True, complete_only=False, verbose=False):
    rows = reads.get(norm(rel).replace("modules\\mcp_server\\", ""), [])
    target = (recs.get(rel, {}) or {}).get("read_total") or 0
    comp = sorted(complete_windows(rows))
    notes = []
    base = []
    base_rev = 0
    for rev, t, lines in comp:
        if rev == target:
            base, base_rev = list(lines), rev
            notes.append("complete read at target revision %d" % rev)
            break
    if not base and comp:
        rev, t, lines = comp[-1]
        base, base_rev = list(lines), rev
        notes.append("complete read at revision %d (target %d)" % (rev, target))
    # newer partial windows, ascending
    if not complete_only:
        later = sorted([w for w in partial_windows(rows) if w[0] > base_rev])
        for rev, t, lines in later:
            if len(lines) < 8:
                continue
            base, how = apply_window(base, lines)
            notes.append("window rev%d (%d lines): %s" % (rev, len(lines), how))
    bak_path = os.path.join(BAK, rel.replace("/", os.sep))
    ins = 0
    if do_backup and os.path.exists(bak_path):
        bak = read_plain(bak_path)
        if bak and bak[-1] == "":
            bak = bak[:-1]
        base, ins = backup_fill(base, bak)
        if ins:
            notes.append("backup filled %d lines" % ins)
    return base, notes, target, base_rev


def main():
    rels = [l.strip() for l in read_plain(sys.argv[1]) if l.strip()]
    write = "--write" in sys.argv
    complete_only = "--complete-only" in sys.argv
    do_backup = "--no-backup" not in sys.argv
    reads = load_reads()
    recs = load_targets()
    report = []
    for rel in rels:
        base, notes, target, base_rev = rebuild(rel, reads, recs, do_backup=do_backup,
                                                complete_only=complete_only)
        p = os.path.join(TREE, rel.replace("/", os.sep))
        cur = read_plain(p) if os.path.exists(p) else []
        print("%-52s cur=%-5d -> new=%-5d (base rev%d, target %d)" % (rel, len(cur), len(base), base_rev, target))
        for n in notes:
            print("      %s" % n)
        report.append({"rel": rel, "cur": len(cur), "new": len(base), "target": target,
                       "base_rev": base_rev, "notes": notes})
        if write:
            with io.open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(base) + "\n")
    with io.open(os.path.join(OUT, "rebuild-report.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
