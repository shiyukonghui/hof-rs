# -*- coding: utf-8 -*-
"""TASK-140 §2.1 / §3.Y10: THIS batch's mechanical redirect self-check.

Same discipline as TASK-136's / TASK-138's / TASK-139's scanners.  What this one does
differently:

1. it cuts the shared (append-only) ledger at the first entry that belongs to TASK-140
   (`source == "t140-wrapper-call"`, or an argv naming a `t140_*` script), so "how many
   commands did THIS batch run" does not depend on later batches;
2. it scans THIS batch's driver scripts (`t140_*.py`), the shipped tools it changed
   (`tools/playtest_player.py`, `tools/playability_gate.py`, `tools/playtest_artifact_index.py`)
   and the four game sources it changed (`projects/{asteroids,frogger,bomberman,flappy}/src/*.cs`)
   for `shell=True` and for literal redirect tokens.  Every token in a `.cs` file is classified
   `csharp-source` (a C# `>` / `=>` is not a shell command) so the python-side `code` number
   keeps meaning what it means.

Usage (cmd, through the ledger wrapper):
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t140_cmd.py -- D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t140_scan_redirects.py
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
OUT = os.path.join(HERE, "t140_redirect_scan.json")

GAME_SOURCES = ["asteroids/src/AsteroidsGame.cs", "frogger/src/FroggerGame.cs",
                "bomberman/src/BombermanGame.cs", "flappy/src/FlappyBirdGame.cs"]

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

    Selector = this batch's own NAMESPACE: `source == "t140-wrapper-call"` or an argv that
    names a `t140_*` script.  TASK-139's selector had to be corrected twice; this one is the
    corrected form (accept the `source` field, not just the argv substring), and
    `t140_cut_probe.py` prints the same index independently.
    """
    for i, e in enumerate(entries):
        src = e.get("source") or ""
        joined = " ".join(str(a) for a in (e.get("argv") or []))
        if src == "t140-wrapper-call" or "t140" in joined:
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
            "first_task140_index": start,
            "first_task140_entry": entries[start] if start < len(entries) else None,
            "previous_entry": entries[start - 1] if start > 0 else None,
            "what": ("the first ledger entry that names a `t140_*` script or carries "
                     "`source == t140-wrapper-call`; this batch's commands are that entry and "
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
    mine_files = sorted(glob.glob(os.path.join(HERE, "t140_*.py")))
    for extra in ("playtest_player.py", "playability_gate.py", "playtest_artifact_index.py"):
        p = os.path.join(ROOT, "tools", extra)
        if os.path.isfile(p):
            mine_files.append(p)
    for rel in GAME_SOURCES:
        p = os.path.join(ROOT, "projects", rel)
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
        is_cs = rel.lower().endswith(".cs")
        rep["script_files"].append({"file": rel, "kind": "csharp" if is_cs else "python"})
        if not is_cs and re.search(r"shell\s*=\s*True", txt):
            rep["shell_true"].append(rel)
        for n, line in enumerate(txt.splitlines(), 1):
            for m in re.finditer(r"(2>&1|2>/dev/null|1>NUL|>\s*nul|>>|>)", line):
                s = line.strip()
                tok = m.group(1)
                after = line[m.end():m.end() + 1]
                before = line[max(0, m.start() - 1):m.start()]
                if is_cs:
                    kind = "csharp-source (a C# `>`/`=>` is not a shell command)"
                elif tok == ">" and (after == "=" or before == "-"):
                    # `>=`, `->`, `<->`: a comparison or an arrow, never a redirection
                    kind = "comparison-or-arrow (not a shell redirection)"
                elif tok == ">" and before in ("(", "[", " ", ","):
                    # `print("%s: %r -> %r")`-style text and dict lookups like `a["x"] > b`
                    kind = "comparison-or-arrow (not a shell redirection)"
                else:
                    kind = ("comment" if s.startswith("#") else
                            ("docstring-or-string" if s[:1] in ('"', "'", ">", "`") or
                             s.startswith("（") else "code"))
                rep["script_hits"].append({"file": rel, "line": n,
                                           "token": tok, "kind": kind, "text": s})
    code_hits = [h for h in rep["script_hits"] if h.get("kind") == "code"]
    cs_hits = [h for h in rep["script_hits"] if str(h.get("kind")).startswith("csharp")]
    rep["code_hits"] = code_hits
    rep["csharp_hits"] = cs_hits
    print("COMMANDS SCANNED (this batch): %d   COMMANDS WITH A REDIRECTION HIT: %d"
          % (rep["this_batch_commands"], rep["hits"]))
    print("REAL HITS: %d   false positives: %d"
          % (rep["hits"] - len(rep["false_positives"]), len(rep["false_positives"])))
    for h in rep["hit_lines"]:
        print("  HIT [%s] ts=%s: %s" % (h.get("verdict"), h.get("ts"), h["command"]))
    print("PYTHON CODE-CLASSIFIED SOURCE HITS (%d, each verbatim):" % len(code_hits))
    for h in code_hits:
        print("  %s:%d  `%s`  <- %s" % (os.path.basename(h["file"]), h["line"],
                                        h["text"], h["kind"]))
    print("DRIVER SCRIPTS SCANNED: %d   shell=True: %d   literal redirect tokens: %d "
          "(python-code:%d csharp-source:%d comment/string:%d)"
          % (len(rep["script_files"]), len(rep["shell_true"]), len(rep["script_hits"]),
             len(code_hits), len(cs_hits),
             len(rep["script_hits"]) - len(code_hits) - len(cs_hits)))
    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(rep, ensure_ascii=False, indent=1))
    print("wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
