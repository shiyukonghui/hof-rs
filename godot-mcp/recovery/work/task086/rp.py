# -*- coding: utf-8 -*-
"""TASK-086 strict replay.

Ruling: the ONLY authoritative sources are
  events-write.jsonl (whole new text)   and   events-edit.jsonl (full old/new).
Replay = newest recorded whole-file write BY TIME + every later applied edit in
time order, each requiring an EXACT and UNIQUE match of `old`.
An edit whose recorded `result` starts with "Error" never touched the file.
An edit whose `old` is missing/ambiguous is a BREAK (reported, never guessed).

usage:
  python rp.py <exact-path-or-substr> [--out FILE] [--list]
"""
import io
import json
import os
import sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
_C = {}


def norm(p):
    return (p or "").replace("/", "\\").lower()


def index(which):
    if which in _C:
        return _C[which]
    by = {}
    with io.open(os.path.join(IDX, which), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            by.setdefault(norm(r.get("path", "")), []).append(r)
    _C[which] = by
    return by


def rows(which, sub):
    sub = norm(sub)
    out = []
    for path, rs in index(which).items():
        if sub in path:
            out.extend(rs)
    return out


def exact_rows(which, path):
    k = norm(path)
    d = index(which)
    if k in d:
        return d[k]
    hits = [p for p in d if k in p]
    if len(hits) == 1:
        return d[hits[0]]
    if not hits:
        return []
    raise SystemExit("ambiguous path %r -> %s" % (path, hits[:8]))


def applied(e):
    return not (e.get("result") or "").lstrip().startswith("Error")


def replay(path, want_base=None, verbose=True):
    writes = sorted(exact_rows("events-write.jsonl", path), key=lambda r: r.get("time", 0))
    edits = sorted(exact_rows("events-edit.jsonl", path), key=lambda r: r.get("time", 0))
    if not writes:
        raise SystemExit("no recorded whole-file write for %s" % path)
    if want_base is not None:
        base = [w for w in writes if str(w.get("seq")) == str(want_base)]
        if not base:
            raise SystemExit("no write with seq %s" % want_base)
        base = base[0]
    else:
        base = writes[-1]
    buf = base.get("content") or ""
    t0 = base.get("time", 0)
    done, refused, breaks = [], [], []
    for e in edits:
        if e.get("time", 0) <= t0:
            continue
        if not applied(e):
            refused.append(e)
            continue
        old = e.get("old") or ""
        new = e.get("new") or ""
        if old and buf.count(old) == 1:
            buf = buf.replace(old, new, 1)
            done.append(e)
        else:
            breaks.append((e, buf.count(old) if old else -1))
    if verbose:
        print("base: seq=%s t=%s bytes=%d lines=%d" % (
            base.get("seq"), t0, len(base.get("content") or ""),
            len((base.get("content") or "").split("\n"))))
        print("edits after base: %d  applied=%d  refused=%d  breaks=%d" % (
            len(done) + len(refused) + len(breaks), len(done), len(refused), len(breaks)))
        for e, occ in breaks:
            print("  BREAK seq=%-6s t=%-14s occ=%-3d old=%-4d new=%-4d  %s" % (
                e.get("seq"), e.get("time"), occ,
                len((e.get("old") or "").split("\n")), len((e.get("new") or "").split("\n")),
                (e.get("old") or "").split("\n")[0][:100]))
        print("replayed lines=%d bytes=%d" % (len(buf.split("\n")), len(buf)))
    return buf, {"base": base, "applied": done, "refused": refused, "breaks": breaks}


def main():
    sub = sys.argv[1]
    argv = sys.argv[2:]
    out = None
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    buf, info = replay(sub)
    if out:
        with io.open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(buf if buf.endswith("\n") or buf == "" else buf + "\n")
        print("wrote %s" % out)


if __name__ == "__main__":
    main()
