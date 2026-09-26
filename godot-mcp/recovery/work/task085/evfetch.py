# -*- coding: utf-8 -*-
"""TASK-085 helpers: fetch recorded text + report/repair replay breaks.

Ruling (A): the ONLY authoritative sources are
  events-write.jsonl (whole new text) and events-edit.jsonl (full old/new).
Nothing here invents text: every byte written into the tree is either the
replayed chain or the recorded `new` of an edit event.
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


def writes(sub):
    return sorted(load("events-write.jsonl", sub), key=lambda r: r.get("time", 0))


def edits(sub):
    return sorted(load("events-edit.jsonl", sub), key=lambda r: r.get("time", 0))


def reads(sub):
    return load("events-read.jsonl", sub)


def edit_text(sub, seq, which):
    for e in edits(sub):
        if str(e.get("seq")) == str(seq):
            return e.get(which) or ""
    raise SystemExit("edit seq %s not found in %s" % (seq, sub))


def skeleton(sub, rev=None):
    """no -> text from the newest read windows of the wanted revision."""
    rows = reads(sub)
    if not rows:
        return {}, None
    if rev is None:
        rev = max((r.get("totalLines") or 0) for r in rows)
    best = {}
    for r in rows:
        if (r.get("totalLines") or 0) != rev:
            continue
        t = r.get("time", 0)
        for no, txt in (r.get("lines") or []):
            if no not in best or t > best[no][0]:
                best[no] = (t, txt)
    return {k: v[1] for k, v in best.items()}, rev


def lines_of(path):
    t = io.open(path, encoding="utf-8", errors="replace").read().split("\n")
    if t and t[-1] == "":
        t.pop()
    return t


def write_lines(path, lines):
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def bal(lines):
    d = p = 0
    for l in lines:
        s = l.split("//", 1)[0]
        for ch in s:
            if ch == "{":
                d += 1
            elif ch == "}":
                d -= 1
            elif ch == "(":
                p += 1
            elif ch == ")":
                p -= 1
    return d, p
