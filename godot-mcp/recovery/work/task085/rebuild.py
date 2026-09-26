# -*- coding: utf-8 -*-
"""TASK-085 reconstruction engine (ruling A).

Base selection, in order of preference:
  * `write` - the newest recorded whole-file write (events-write.jsonl);
  * `read`  - the newest revision whose read windows cover EVERY line
              (a complete recorded snapshot), each line taken from its newest
              window;
  * `rev:N` - the complete snapshot of revision N.

Then every usable edit (recorded result is not an error) with a later time is
replayed in time order, each with an exact and unique old-text match.  Edits with
an error result are reported as `refused`; a non-matching edit is a `break`.
Nothing is invented.

usage:
  python rebuild.py <subpath> [--base write|read|rev:N] [--out PATH] [--quiet]
"""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


def load(which, sub):
    out = []
    p = os.path.join(IDX, which)
    if not os.path.exists(p):
        return out
    with io.open(p, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if sub in norm(r.get("path", "")):
                out.append(r)
    return out


def is_ok(e):
    return not (e.get("result") or "").lstrip().startswith("Error")


def full_reads(sub):
    """[(rev, t, lines)] for every revision whose windows cover every line."""
    rows = load("events-read.jsonl", sub)
    byrev = {}
    for r in rows:
        byrev.setdefault(r.get("totalLines") or 0, []).append(r)
    out = []
    for rev, ws in byrev.items():
        best = {}
        for w in ws:
            t = w.get("time", 0)
            for no, txt in (w.get("lines") or []):
                if no not in best or t > best[no][0]:
                    best[no] = (t, txt)
        if rev > 0 and len(best) >= rev:
            out.append((rev, max(best[n][0] for n in best), {n: best[n][1] for n in best}))
    out.sort(key=lambda x: (x[0], x[1]))
    return out


def pick_base(sub, mode):
    if mode == "read" or mode.startswith("rev:"):
        fulls = full_reads(sub)
        if not fulls:
            raise SystemExit("no complete read snapshot for %s" % sub)
        if mode == "read":
            rev, t, skel = fulls[-1]
        else:
            want = int(mode.split(":")[1])
            hit = [f for f in fulls if f[0] == want]
            if not hit:
                raise SystemExit("rev %d is not a complete snapshot" % want)
            rev, t, skel = hit[-1]
        buf = "\n".join(skel[n] for n in range(1, rev + 1))
        return buf, t, "read rev%d t=%s (%d lines)" % (rev, t, rev)
    writes = sorted(load("events-write.jsonl", sub), key=lambda r: r.get("time", 0))
    if not writes:
        raise SystemExit("no recorded whole-file write for %s" % sub)
    w = writes[-1]
    return w.get("content") or "", w.get("time", 0), "write seq=%s t=%s" % (w.get("seq"), w.get("time"))


def run(sub, mode="write", verbose=True):
    buf, t0, src = pick_base(sub, mode)
    edits = sorted(load("events-edit.jsonl", sub), key=lambda r: r.get("time", 0))
    applied, refused, breaks = [], [], []
    for e in edits:
        if e.get("time", 0) <= t0:
            continue
        if not is_ok(e):
            refused.append(e)
            continue
        old, new = e.get("old") or "", e.get("new") or ""
        n = buf.count(old) if old else -1
        if old and n == 1:
            buf = buf.replace(old, new, 1)
            applied.append(e.get("seq"))
            continue
        breaks.append({"seq": e.get("seq"), "time": e.get("time"), "occ": n,
                       "old_lines": len(old.split("\n")), "new_lines": len(new.split("\n")),
                       "old": old, "new": new})
    if verbose:
        print("base: %s" % src)
        print("edits after base: %d  applied=%d  refused=%d  breaks=%d  lines=%d" % (
            len(applied) + len(refused) + len(breaks), len(applied), len(refused),
            len(breaks), len(buf.split("\n"))))
        for e in refused:
            print("  REFUSED seq=%-6s t=%-14s old=%-4d new=%-4d %s" % (
                e.get("seq"), e.get("time"), len((e.get("old") or "").split("\n")),
                len((e.get("new") or "").split("\n")), (e.get("result") or "")[:64]))
        for b in breaks:
            print("  BREAK seq=%-6s t=%-14s occ=%-3d old=%-4d new=%-4d" % (
                b["seq"], b["time"], b["occ"], b["old_lines"], b["new_lines"]))
            print("        old> %s" % (b["old"].split("\n")[0] if b["old"] else "")[:100])
            print("        new> %s" % (b["new"].split("\n")[0] if b["new"] else "")[:100])
    return buf, {"src": src, "applied": applied, "refused": refused, "breaks": breaks}


def main():
    sub = sys.argv[1]
    argv = sys.argv[2:]
    mode = "write"
    if "--base" in argv:
        mode = argv[argv.index("--base") + 1]
    out = None
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    buf, info = run(sub, mode, verbose="--quiet" not in argv)
    if out:
        with io.open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(buf if buf.endswith("\n") else buf + "\n")
        print("wrote %s" % out)


if __name__ == "__main__":
    main()
