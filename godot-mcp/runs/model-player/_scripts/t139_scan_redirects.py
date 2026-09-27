# -*- coding: utf-8 -*-
"""TASK-139 §2.1 / §3.X9: THIS batch's mechanical redirect self-check.

Same discipline as TASK-136's and TASK-138's scanners.  What this one does differently:

1. it cuts the shared (append-only) ledger at the last **TASK-138** entry instead of at a
   hard-coded TASK-136 line, so "how many commands did THIS batch run" is a number that does
   not depend on how many commands a later batch adds;
2. it scans THIS batch's driver scripts (`t139_*.py`) plus the two shipped tools it changed
   (`tools/playtest_player.py`, `tools/playability_gate.py`, `tools/playtest_artifact_index.py`)
   for `shell=True` and for literal redirect tokens, and classifies each hit as `code` vs
   comment/docstring text.

Usage (cmd, through the ledger wrapper):
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_cmd.py -- D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_scan_redirects.py
"""
from __future__ import print_function

import glob
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
LEDGER = os.path.join(HERE, "t136_commands.jsonl")
OUT = os.path.join(HERE, "t139_redirect_scan.json")

# The last entry TASK-138 wrote.  TASK-138's own scanner cut at line 116 (TASK-136's last
# entry, ts 2026-09-28T03:22:58) and reported 70 commands; TASK-138's wrap-up commands came
# after it.  This batch's cut is that batch's LAST entry, found by scanning for the last line
# whose ts is <= TASK-139's first command (the first entry written after this file's sibling
# `t139_cmd.py` appeared).  The fallback is the entry count TASK-138's scanner itself reported.
CUT_MATCH = {"ts_prefix": "2026-09-28T"}

PATTERNS = [
    (r"2>&1", "2>&1"),
    (r"2>/dev/null", "2>/dev/null"),
    (r"1>NUL", "1>NUL"),
    (r">\s*nul\b", "> nul"),
    (r"\*>[ ]", "*> "),
    (r">>", ">>"),
    (r">", ">"),
]


def unified(s):
    out = []
    for pat, label in PATTERNS:
        for m in re.finditer(pat, s, re.IGNORECASE if label.lower().endswith("nul") else 0):
            out.append({"token": label, "at": m.start(),
                        "context": s[max(0, m.start() - 40):m.end() + 40]})
    tokens = set(h["token"] for h in out)
    if any(t in tokens for t in (">>", "2>&1", "2>/dev/null", "1>NUL", "> nul", "*> ")):
        out = [h for h in out if h["token"] != ">"]
    return out


def find_cut(entries):
    """The index of the first entry that belongs to THIS batch.

    The selector is the batch's own NAMESPACE, not a timestamp and not the backfill marker:
    the first entry whose argv names one of this batch's `t139_*` scripts or the `t139_cmd.py`
    wrapper, or whose `source` is `t139-wrapper-call`.  Checked against the ledger with
    `t139_cut_probe.py`, which printed the same index and the entry before it.

    Two earlier drafts were WRONG and are recorded here because a wrong cut silently changes
    the count:
      * "first `manual-backfill` entry" -- TASK-138 wrote 16 backfill rows of its OWN that sit
        BEFORE this batch, and TASK-139's backfill rows are appended AFTER its 21 wrapper
        rows, so that selector claimed 44 rows that belong to TASK-136/138;
      * "first entry with `t139` in its argv" alone is the right idea but must also accept the
        `source` field, because a wrapper call to a tool that does not carry `t139_` in its
        argv (e.g. `tools/playtest_player.py`) is still this batch's.
    """
    for i, e in enumerate(entries):
        src = e.get("source") or ""
        joined = " ".join(str(a) for a in (e.get("argv") or []))
        if src == "t139-wrapper-call" or "t139" in joined:
            return i
    return len(entries)


def main():
    entries = []
    with io.open(LEDGER, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    start = find_cut(entries)
    mine = entries[start:]
    rep = {
        "scanner": os.path.abspath(__file__),
        "ledger": LEDGER,
        "ledger_sha256_at_scan": hashlib.sha256(open(LEDGER, "rb").read()).hexdigest(),
        "ledger_bytes_at_scan": os.path.getsize(LEDGER),
        "ledger_lines_total": len(entries),
        "cut": {
            "first_task139_index": start,
            "first_task139_entry": entries[start] if start < len(entries) else None,
            "previous_entry": entries[start - 1] if start > 0 else None,
            "what": ("the first ledger entry that names a `t139_*` script or carries "
                     "`source == t139-wrapper-call`; this batch's commands are that entry and "
                     "everything after it"),
        },
        "this_batch_commands": len(mine),
        "this_batch_first_ts": (mine[0].get("ts") if mine else None),
        "this_batch_last_ts": (mine[-1].get("ts") if mine else None),
        "hits": 0, "hit_lines": [], "false_positives": [],
        "script_files": [], "script_hits": [], "shell_true": [],
    }
    for e in mine:
        joined = " ".join(str(a) for a in (e.get("argv") or []))
        hits = unified(joined)
        if hits:
            rep["hits"] += 1
            rec = {"ts": e.get("ts"), "source": e.get("source", "wrapper"),
                   "cwd": e.get("cwd"), "command": joined, "hits": hits}
            if all(h["token"] == ">" for h in hits) and "unpack(" in joined:
                rec["verdict"] = "false positive (Python struct big-endian format char)"
                rep["false_positives"].append(rec)
            else:
                rec["verdict"] = "REAL"
            rep["hit_lines"].append(rec)
    mine_files = sorted(glob.glob(os.path.join(HERE, "t139_*.py")))
    for extra in ("playtest_player.py", "playability_gate.py", "playtest_artifact_index.py"):
        p = os.path.join(ROOT, "tools", extra)
        if os.path.isfile(p):
            mine_files.append(p)
    for p in sorted(set(mine_files)):
        rel = os.path.abspath(p)
        if os.path.basename(rel) == os.path.basename(__file__):
            rep["script_files"].append({"file": rel,
                                        "skipped": "this scanner's own pattern table and "
                                                   "shell=True regex"})
            continue
        txt = io.open(p, encoding="utf-8").read()
        rep["script_files"].append({"file": rel})
        if re.search(r"shell\s*=\s*True", txt):
            rep["shell_true"].append(rel)
        for n, line in enumerate(txt.splitlines(), 1):
            for m in re.finditer(r"(2>&1|2>/dev/null|1>NUL|>\s*nul|>>|>)", line):
                s = line.strip()
                kind = ("comment" if s.startswith("#") else
                        ("docstring-or-string" if s[:1] in ('"', "'", ">", "`") or
                         s.startswith("（") else "code"))
                rep["script_hits"].append({"file": rel, "line": n,
                                           "token": m.group(1), "kind": kind, "text": s})
    code_hits = [h for h in rep["script_hits"] if h.get("kind") == "code"]
    rep["code_hits"] = code_hits
    print("COMMANDS SCANNED (this batch): %d   COMMANDS WITH A REDIRECTION HIT: %d"
          % (rep["this_batch_commands"], rep["hits"]))
    print("REAL HITS: %d   false positives: %d"
          % (rep["hits"] - len(rep["false_positives"]), len(rep["false_positives"])))
    for h in rep["hit_lines"]:
        print("  HIT [%s] ts=%s: %s" % (h.get("verdict"), h.get("ts"), h["command"]))
    print("CODE-CLASSIFIED SOURCE HITS (%d, each verbatim):" % len(code_hits))
    for h in code_hits:
        print("  %s:%d  `%s`  <- %s" % (os.path.basename(h["file"]), h["line"],
                                        h["text"], h["kind"]))
    print("DRIVER SCRIPTS SCANNED: %d   shell=True: %d   literal redirect tokens: %d "
          "(code:%d comment/string:%d)"
          % (len(rep["script_files"]), len(rep["shell_true"]), len(rep["script_hits"]),
             len(code_hits), len(rep["script_hits"]) - len(code_hits)))
    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(rep, ensure_ascii=False, indent=1))
    print("wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
