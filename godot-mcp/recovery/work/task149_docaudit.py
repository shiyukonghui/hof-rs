#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-149 documentation audit: mechanical checks over the normative documents.

Checks performed (all read-only; every result is printed, nothing is written):

  C1  -- the documented ``-32602`` provenance split, recomputed from the evidence;
  C2  -- every backticked repo-relative path mentioned in the audited documents:
         does it exist on disk?
  C3  -- the ``tools/tests/**`` file count and per-file ``def test_`` counts;
  C4  -- the family totals of recovery/TEST-CASES.md (delegated to its own recount);
  C5  -- every ``recovery/reports/...`` and ``recovery/tasks/...`` reference resolves.

A path that appears in a document and does not exist is a candidate "dead cross-reference";
the script prints it with the document and line number so the caller can judge it (some
mentions are deliberate, e.g. "that file does not exist").

No shell redirection: output goes to stdout from this process.
"""
from __future__ import print_function

import io
import json
import os
import re
import sys

ROOT = r"F:\moonbit-hof-rs"
MCP = os.path.join(ROOT, "godot-mcp")

AUDITED = [
    "DECISIONS.md",
    "godot-mcp/recovery/tasks/README.md",
    "godot-mcp/recovery/tasks/TEMPLATE-logic-feedback.md",
    "godot-mcp/recovery/TEST-CASES.md",
    "godot-mcp/TOOL-COVERAGE.md",
    "godot-mcp/recovery/reports/PLAYABILITY-REPORT.md",
    "godot-mcp/recovery/reports/PLAYABILITY-DEFECTS.md",
    "godot-mcp/recovery/reports/GAME-LOOP-LOG.md",
    "godot-mcp/recovery/reports/TASK-143-REPORT.md",
    "godot-mcp/recovery/reports/TASK-144-REPORT.md",
    "godot-mcp/recovery/reports/TASK-146-REPORT.md",
    "godot-mcp/recovery/reports/TASK-148-REPORT.md",
    "godot-mcp/recovery/reports/ACCEPTANCE-TASK-137.md",
    "godot-mcp/recovery/reports/ACCEPTANCE-TASK-141.md",
    "godot-mcp/recovery/reports/ACCEPTANCE-TASK-145.md",
    "godot-mcp/recovery/reports/ACCEPTANCE-TASK-147.md",
]

# A backticked token is treated as a candidate repo path when it has a separator and one
# of these extensions (or is one of the known separator-less report names handled below).
PATH_RE = re.compile(r"`([A-Za-z0-9_./\\-]+\.(?:md|json|py|ps1|cpp|h|cmd|txt|jsonl|cfg|gd|cs|exe|pck|zip))`")
KNOWN_ALIASES = {
    "coverage.json": "godot-mcp/coverage.json",
    "tools/tool_channels.json": "godot-mcp/tools/tool_channels.json",
}


def norm(rel):
    return rel.replace("\\", "/").strip()


def exists_in_repo(rel):
    """True when the token resolves from any plausible documentation root.

    A document at `godot-mcp/RECOVERY.md` may write `recovery/work/x.json`,
    `godot-mcp/recovery/work/x.json` or just `x.json` for the same file, so the
    candidate is tried against the repo root, `godot-mcp/` and `godot-mcp/recovery/`.
    """
    cand = norm(rel)
    if cand in KNOWN_ALIASES:
        cand = KNOWN_ALIASES[cand]
    bases = (ROOT,
             os.path.join(ROOT, "godot-mcp"),
             os.path.join(ROOT, "godot-mcp", "recovery"),
             os.path.join(ROOT, "godot-mcp", "recovery", "reports"),
             os.path.join(ROOT, "godot-mcp", "recovery", "tasks"),
             os.path.join(ROOT, "godot-mcp", "recovery", "work"),
             os.path.join(ROOT, "godot-mcp", "godot"),
             os.path.join(ROOT, "godot-mcp", "godot", "modules", "mcp_server"))
    for base in bases:
        if os.path.exists(os.path.join(base, cand.replace("/", os.sep))):
            return True, cand
    # TOOL-COVERAGE.md cites module sources engine-relative but abbreviated as
    # `tools/foo.cpp` for `<engine>/modules/mcp_server/tools/foo.cpp`.
    if cand.startswith("tools/"):
        alt = os.path.join(ROOT, "godot-mcp", "godot", "modules", "mcp_server",
                           cand.replace("/", os.sep))
        if os.path.exists(alt):
            return True, cand
    # DECISIONS.md cites `scripts/x.ps1` / `docs/scripts/x.py` for
    # `<engine>/modules/mcp_server/scripts/x.ps1` and `.../docs/scripts/x.py`.
    for sub in ("scripts", "docs"):
        if cand.startswith(sub + "/"):
            alt = os.path.join(ROOT, "godot-mcp", "godot", "modules", "mcp_server",
                               cand.replace("/", os.sep))
            if os.path.exists(alt):
                return True, cand
    return False, cand


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"

    if which in ("all", "c1"):
        print("=" * 78)
        print("C1  -32602 provenance split (from the evidence, not from prose)")
        path = os.path.join(MCP, "recovery", "work", "task143", "probe-live.json")
        with io.open(path, "r", encoding="utf-8") as handle:
            doc = json.load(handle)
        colon = nocolon = wrong = other = 0
        for name, probe in (doc.get("tools") or {}).items():
            if probe.get("error_code") != -32602:
                continue
            msg = "%s" % (probe.get("error_message") or "")
            if msg.startswith("Missing required parameter: "):
                colon += 1
            elif msg.startswith("Missing required parameter '"):
                nocolon += 1
                print("    no-colon case: %-34s %s" % (name, msg))
            elif re.match(r"^Parameter '[^']*' must be\b", msg):
                wrong += 1
            else:
                other += 1
                print("    UNCLASSIFIED:  %-34s %s" % (name, msg))
        total = colon + nocolon + wrong + other
        print("    MISSING_REQUIRED_COLON   = %d" % colon)
        print("    MISSING_REQUIRED_NO_COLON= %d" % nocolon)
        print("    WRONG_TYPE               = %d" % wrong)
        print("    OTHER                    = %d" % other)
        print("    TOTAL live -32602        = %d" % total)
        print("    prover-handler side      = %d (colon + wrong_type)" % (colon + wrong))
        print("    CLAIM '121 + 21'         = %d" % (121 + 21))

    if which in ("all", "c3"):
        print("=" * 78)
        print("C3  tools/tests/** file and test counts")
        tests = os.path.join(MCP, "tools", "tests")
        files = sorted(f for f in os.listdir(tests) if f.endswith(".py"))
        print("    .py files: %d" % len(files))
        total_defs = 0
        for name in files:
            with io.open(os.path.join(tests, name), "r", encoding="utf-8") as handle:
                src = handle.read()
            n = len(re.findall(r"^def test_[A-Za-z0-9_]*\(", src, re.M))
            total_defs += n
            print("      %-42s def test_* = %d" % (name, n))
        print("    total def test_*: %d" % total_defs)

    if which in ("all", "c2"):
        print("=" * 78)
        print("C2  candidate dead path references (only ones that do NOT resolve)")
        seen = {}
        for rel in AUDITED:
            full = os.path.join(ROOT, rel.replace("/", os.sep))
            if not os.path.exists(full):
                print("  AUDITED FILE MISSING: %s" % rel)
                continue
            with io.open(full, "r", encoding="utf-8") as handle:
                for lineno, line in enumerate(handle, 1):
                    for raw in PATH_RE.findall(line):
                        cand = norm(raw)
                        # Only a token that names a DIRECTORY counts as a cross-reference:
                        # a bare basename is routinely a mention, not a path claim.
                        if "/" not in cand and "\\" not in cand and cand not in KNOWN_ALIASES:
                            continue
                        ok, cand = exists_in_repo(cand)
                        if ok:
                            continue
                        key = (rel, cand)
                        seen.setdefault(key, []).append(lineno)
        for (rel, cand) in sorted(seen):
            lines = seen[(rel, cand)]
            shown = ",".join("%d" % x for x in lines[:6])
            more = "" if len(lines) <= 6 else (" (+%d more)" % (len(lines) - 6))
            print("  DEAD  %-46s %-58s lines %s%s"
                  % (os.path.basename(rel), cand, shown, more))
        print("  dead candidate references: %d" % len(seen))


if __name__ == "__main__":
    main()
