# -*- coding: utf-8 -*-
"""TASK-085 strict replay, per ruling (A).

base = the newest recorded whole-file write (events-write.jsonl)
then = every later edit (events-edit.jsonl), in time order, each with an EXACT
       old-text match that must be unique.

An edit whose recorded `result` is an error ("Error: ...") NEVER touched the
file, so it is not part of the chain: it is reported separately as `refused`.
An edit whose `old` is not found verbatim (or is found more than once) is a
BREAK: recorded with file + seq + reason.

usage:
  python replay2.py <subpath>              -> the report
  python replay2.py <subpath> --out <path> -> write the replayed buffer
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
    r = (e.get("result") or "").lstrip()
    return not r.startswith("Error")


def replay(sub, verbose=True):
    writes = sorted(load("events-write.jsonl", sub), key=lambda r: r.get("time", 0))
    edits = sorted(load("events-edit.jsonl", sub), key=lambda r: r.get("time", 0))
    if not writes:
        raise SystemExit("no recorded whole-file write for %s" % sub)
    base = writes[-1]
    buf = base.get("content") or ""
    t0 = base.get("time", 0)
    applied = []
    refused = []
    breaks = []
    for e in edits:
        if e.get("time", 0) <= t0:
            continue
        if not is_ok(e):
            refused.append(e)
            continue
        old = e.get("old") or ""
        new = e.get("new") or ""
        n = buf.count(old) if old else -1
        if old and n == 1:
            buf = buf.replace(old, new, 1)
            applied.append(e.get("seq"))
            continue
        breaks.append({
            "seq": e.get("seq"), "time": e.get("time"), "occurrences": n,
            "old_lines": len(old.split("\n")), "new_lines": len(new.split("\n")),
            "first_old": (old.split("\n")[0] if old else "")[:110],
            "first_new": (new.split("\n")[0] if new else "")[:110],
        })
    if verbose:
        print("base: write seq=%s t=%s raw-lines=%d" % (
            base.get("seq"), t0, len((base.get("content") or "").split("\n"))))
        print("edits after base: %d  applied=%d  refused(bad result)=%d  breaks=%d" % (
            len(applied) + len(refused) + len(breaks), len(applied), len(refused), len(breaks)))
        for e in refused:
            print("  REFUSED seq=%-6s t=%-14s old=%-4d new=%-4d  %s" % (
                e.get("seq"), e.get("time"), len((e.get("old") or "").split("\n")),
                len((e.get("new") or "").split("\n")), (e.get("result") or "")[:70]))
        for b in breaks:
            print("  BREAK seq=%-6s t=%-14s occ=%-3d old=%-4d new=%-4d" % (
                b["seq"], b["time"], b["occurrences"], b["old_lines"], b["new_lines"]))
            print("        old> %s" % b["first_old"])
            print("        new> %s" % b["first_new"])
    return buf, {"base": base, "applied": applied, "refused": refused, "breaks": breaks}


def main():
    sub = sys.argv[1]
    argv = sys.argv[2:]
    out = None
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    buf, info = replay(sub)
    print("replayed content lines=%d" % len(buf.split("\n")))
    if out:
        with io.open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(buf if buf.endswith("\n") else buf + "\n")
        print("wrote %s" % out)


if __name__ == "__main__":
    main()
