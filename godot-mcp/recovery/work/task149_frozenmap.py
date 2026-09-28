#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-149: rebuild the frozen pre-TASK-142 `tools/playtest_player.py` and locate symbols.

Why a rebuild is needed: the frozen copy was built by un-applying TASK-142's hunk from a
revision that already carried TASK-140, so naively stripping every earlier block from the
current file removes blocks that were present back then too. The reliable definition is
topological:

    frozen  :=  current MINUS lines(1 .. start_of_the_contiguous_block_containing
                                      load_stability_declaration)

i.e. the inserted TASK-142 block begins at the first line of the comment paragraph that
introduces `STABILITY_STATE_INSUFFICIENT`, and ends at the last line before the next
pre-existing top-level construct. This script prints the candidate splice point, the
resulting line count, and the line number of every symbol of interest in BOTH files, so a
human can confirm the offset is constant.

Read-only; writes nothing; stdout only.
"""
from __future__ import print_function

import hashlib
import io
import os
import re
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"

SYMBOLS = [
    "PASS_BASELINE_ONLY",
    "CHANGE_MARGIN_DEFAULT_FALLBACK",
    "load_stability_declaration",
    "load_change_margins",
    "load_window_declaration",
    "load_refusal_boundary",
    "_margin_reading",
    "step_refusal_record",
    "ack_verdict",
    "step_verdict",
    "changed_of",
    "change_margin_edge_steps",
    "model_fixed_point",
    "step_made_progress",
    "model_no_progress",
    "summarise",
    "_summarise_core",
    "verdict_class",
    "stability_summary",
    "ScriptedPlayerAgent",
    "_pong",
    "ack_after_inject",
    "reporting_counts_as_pass",
    "win_steps",
]


def read(rel):
    with io.open(os.path.join(ROOT, rel.replace("/", os.sep)), "r",
                 encoding="utf-8", errors="replace") as handle:
        return handle.readlines()


def line_of(lines, token, regex=False):
    for i, line in enumerate(lines, 1):
        if regex:
            if re.search(token, line):
                return i
        elif token in line:
            return i
    return None


def main():
    cur = read("tools/playtest_player.py")
    prefix = read("tools/playtest_player_t142_prefix.py")
    print("current lines : %d" % len(cur))
    print("prefix  lines : %d" % len(prefix))

    # locate the TASK-142 inserted block in the current file
    start = None
    for i, line in enumerate(cur, 1):
        if "TASK-140 §1.A.2: the cross-round judgement.  TASK-142 §1.A raised the minimum" in line:
            start = i
            break
    if start is None:
        for i, line in enumerate(cur, 1):
            if "TASK-142" in line and i < 400:
                start = i
                break
    print("first TASK-142-affected comment line in current: %s" % start)
    print("  %r" % cur[start - 1].rstrip() if start else "")

    # the splice: everything from `start` to the line before the pre-existing
    # `load_change_margins` definition is the inserted block.
    end = None
    for i in range(start, min(len(cur), start + 400)):
        if cur[i - 1].startswith("def load_change_margins("):
            end = i - 1
            break
    print("splice end (line before load_change_margins): %s" % end)
    print("removed span: %d lines" % (end - start + 1))
    rebuilt = cur[:start - 1] + cur[end:]
    print("rebuilt lines : %d  (prefix: %d, delta %d)"
          % (len(rebuilt), len(prefix), len(rebuilt) - len(prefix)))

    print("=" * 78)
    print("%-34s %10s %10s" % ("symbol", "rebuilt", "prefix"))
    for sym in SYMBOLS:
        pat = (r"^\s*(?:def|class)\s+%s\b" % re.escape(sym)) if sym[0].isalpha() else None
        rb = line_of(rebuilt, pat, regex=True) if pat else line_of(rebuilt, '"%s":' % sym)
        pf = line_of(prefix, pat, regex=True) if pat else line_of(prefix, '"%s":' % sym)
        if pat is None:
            rb = line_of(rebuilt, sym)
            pf = line_of(prefix, sym)
        mark = "" if rb == pf else "   <-- MISMATCH"
        print("%-34s %10s %10s%s" % (sym, rb, pf, mark))

    digest = hashlib.sha256("".join(rebuilt).encode("utf-8")).hexdigest()
    print("rebuilt sha256 (utf-8 text): %s" % digest)


if __name__ == "__main__":
    main()
