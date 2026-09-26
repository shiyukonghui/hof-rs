# -*- coding: utf-8 -*-
"""Merge recorded read windows + replayed edits into a candidate file body.

Method (the only one the evidence admits for these paths):
  1. every `events-read` row gives a window of numbered lines of the file at the
     revision that was read; for each line number keep the text from the newest
     row that carries it (time order, ties broken by later seq).
  2. require that the union of line numbers is exactly 1..totalLines with no
     hole.  A hole is a BREAK, reported, never guessed.
  3. replay every applied `events-edit` whose time is newer than the newest
     window that contributed, in time order, asserting `old` occurs exactly once.

usage:
  python merge.py <abs-path> [--out FILE] [--report FILE] [--prefer-read]
"""
from __future__ import print_function
import io, json, os, sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
E = os.path.join(IDX, "events-edit.jsonl")
R = os.path.join(IDX, "events-read.jsonl")

LOG = []


def say(msg):
    LOG.append(msg)


def say_stdout():
    """Emit the log as UTF-8 bytes so the Windows console code page cannot corrupt it."""
    try:
        sys.stdout.buffer.write(("\n".join(LOG) + "\n").encode("utf-8"))
        sys.stdout.buffer.flush()
    except Exception:
        pass


def norm(p):
    return (p or "").replace("/", "\\").lower()


def load(fp, target):
    out = []
    t = norm(target)
    with io.open(fp, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            if norm(o.get("path") or "") == t:
                out.append(o)
    return out


def applied(e):
    return not (e.get("result") or "").lstrip().startswith("Error")


def strip_number(s):
    """A recorded read line is either '  123\\ttext' or [123, 'text']."""
    if isinstance(s, (list, tuple)):
        if len(s) >= 2:
            return s[1] if isinstance(s[1], str) else str(s[1])
        return str(s[0]) if s else ""
    if not isinstance(s, str):
        return str(s)
    for sep in ("\t", ": ", "\t "):
        i = s.find(sep)
        if i > 0 and s[:i].strip().isdigit():
            return s[i + len(sep):]
    return s


def build(target, prefer_read=False):
    reads = load(R, target)
    edits = load(E, target)

    # ---- pass 1: newest text per line number
    best = {}
    best_time = {}
    for r in sorted(reads, key=lambda x: (x.get("time", 0), x.get("seq") or 0)):
        off = r.get("offset") or 1
        tl = r.get("totalLines")
        lines = r.get("lines") or []
        if not lines:
            continue
        t = r.get("time", 0)
        s = r.get("seq") or 0
        for i, raw in enumerate(lines):
            n = off + i
            key = (t, s)
            if n not in best or key >= best_time[n]:
                best[n] = strip_number(raw)
                best_time[n] = key

    total = max(best) if best else 0
    holes = [n for n in range(1, total + 1) if n not in best]
    say("windows: %d rows, lines=%d, max=%d, holes=%d" % (len(reads), len(best), total, len(holes)))
    if holes:
        rng = []
        s = p = holes[0]
        for h in holes[1:]:
            if h == p + 1:
                p = h
                continue
            rng.append((s, p))
            s = p = h
        rng.append((s, p))
        say("  HOLE RANGES: %s" % rng[:40])

    buf = "\n".join(best.get(n, "") for n in range(1, total + 1))
    if not buf.endswith("\n"):
        buf += "\n"
    say("merged: lines=%d bytes=%d" % (buf.count("\n"), len(buf.encode("utf-8"))))

    # ---- pass 2: replay edits newer than the newest contributing window
    if prefer_read:
        say("prefer-read: edit replay skipped by request")
        return buf, {"edits": [], "breaks": []}

    newest = max(best_time.values())[0] if best_time else 0
    say("newest contributing window time = %s" % newest)
    applied_edits = [e for e in edits if applied(e)]
    applied_edits.sort(key=lambda x: (x.get("time", 0), x.get("seq") or 0))
    done, skipped, breaks = [], [], []
    for e in applied_edits:
        if e.get("time", 0) <= newest:
            skipped.append(e)
            continue
        old = e.get("old") or ""
        new = e.get("new") or ""
        c = buf.count(old) if old else 0
        if old and c == 1:
            buf = buf.replace(old, new, 1)
            done.append(e)
        else:
            breaks.append((e, c))
    say("edits after newest window: %d (applied=%d, breaks=%d), before=%d"
        % (len(done) + len(breaks), len(done), len(breaks), len(skipped)))
    for e, c in breaks:
        say("  BREAK seq=%-6s t=%-14s occ=%d old=%d new=%d | %s"
            % (e.get("seq"), e.get("time"), c,
               (e.get("old") or "").count("\n") + 1, (e.get("new") or "").count("\n") + 1,
               (e.get("old") or "").split("\n")[0][:100]))
    say("after edits: lines=%d bytes=%d" % (buf.count("\n"), len(buf.encode("utf-8"))))
    return buf, {"edits": done, "breaks": breaks}


def main():
    target = sys.argv[1]
    argv = sys.argv[2:]
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    rep = argv[argv.index("--report") + 1] if "--report" in argv else None
    buf, info = build(target, prefer_read="--prefer-read" in argv)
    if out:
        with io.open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(buf)
        say("wrote %s" % out)
    if rep:
        with io.open(rep, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(LOG) + "\n")
        say("report %s" % rep)
    say_stdout()


if __name__ == "__main__":
    main()
