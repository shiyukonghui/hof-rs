# -*- coding: utf-8 -*-
"""TASK-139 §6.1: the ENUMERABLE backfill of this batch's recon commands.

TASK-136 §6.1 rule 3 requires every command a batch ran to be enumerable, including the ones
run in the interactive terminal before the ledger wrapper was part of the batch's own flow.
Those commands are transcribed VERBATIM (the exact command text, the cwd, and what it was
for) with `"source": "manual-backfill"`, so a reader can subtract them from the count if they
prefer to count only wrapper entries.

This file is itself run through the batch's wrapper, so running the backfill also appears in
the ledger as one command.  It is idempotent: an entry is only appended when its exact
command text is not already present in the ledger.
"""
from __future__ import print_function

import io
import json
import os
import shlex
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
LEDGER = os.path.join(HERE, "t136_commands.jsonl")

PY = r"D:\Anaconda\python.exe"
G = r"F:\moonbit-hof-rs\godot-mcp"
R = r"F:\moonbit-hof-rs"

CMD = [
    (r"cmd /c dir /b godot-mcp\runs\model-player", R,
     "recon: list the model-player run prefixes"),
    (r"cmd /c dir /b godot-mcp\runs\model-player\_scripts\*.jsonl godot-mcp\runs\model-player\_scripts\*.json",
     R, "recon: list the scripts' jsonl/json artifacts"),
    (r"cmd /c dir /b godot-mcp\runs\model-player\_scripts\t138_*.out.txt", R,
     "recon: list TASK-138's sweep stdout files"),
    (r"D:\Anaconda\python.exe runs\model-player\_scripts\t139_inspect_step.py "
     r"runs\model-player\t138-scripted\asteroids\scripted\steps.jsonl 1",
     G, "recon: print the shape of one recorded step record"),
    (r"D:\Anaconda\python.exe runs\model-player\_scripts\t139_refusal_probe.py t138-scripted",
     G, "recon: list the FAIL steps of the 5 refusal games and their refusal counters"),
    (r"D:\Anaconda\python.exe runs\model-player\_scripts\t139_timing.py "
     r"runs\model-player\t136-jev-v3\tetris\model\player.json "
     r"runs\model-player\t136-jev-v3\pong\model\player.json",
     G, "recon: locate a model run's player.json (path probe; both paths MISSING)"),
    (r"D:\Anaconda\python.exe runs\model-player\_scripts\t139_timing2.py "
     r"runs\model-player\_scripts\t136_model_results_jev.json",
     G, "recon: per-game wall clock of TASK-136's model sweep"),
    (r"D:\Anaconda\python.exe runs\model-player\_scripts\t139_timing2.py "
     r"runs\model-player\_scripts\t138_results_scripted.json",
     G, "recon: per-game wall clock of TASK-138's scripted sweep"),
    (r"D:\Anaconda\python.exe runs\model-player\_scripts\t139_health.py",
     G, "recon: read-only health probe of 8080/8081"),
    (r"D:\Anaconda\python.exe runs\model-player\_scripts\t139_decl_probe.py",
     G, "recon: current refusal_evidence/gameplay items of the 5 games"),
    (r"D:\Anaconda\python.exe runs\model-player\_scripts\t139_lines.py "
     r"tools\playability_controls.json 350 356",
     G, "recon: exact bytes of the insertion point"),
    (r"D:\Anaconda\python.exe runs\model-player\_scripts\t139_add_blocks.py",
     G, "§1.A/§1.B: insert model_player_window + model_player_refusal declarations"),
    (r"D:\Anaconda\python.exe runs\model-player\_scripts\t139_add_refusal_fields.py",
     G, "§1.B: add per-game game_side_fields to the 5 refusal games"),
    (r"D:\Anaconda\python.exe tools\tests\test_playability_model_player.py",
     G, "the TASK-139 assertions (pre-sweep run)"),
    (r"D:\Anaconda\python.exe -m pytest tools\tests -q", G,
     "the tools test suite (pre-change baseline, 1 passed)"),
    (r"D:\Anaconda\python.exe tools\playtest_player.py selftest",
     G, "the loop's own selftest after the edits (PASSED)"),
    (r"D:\Anaconda\python.exe runs\model-player\_scripts\t139_debug_mixed.py",
     G, "debug: the mixed refusal run's summary"),
    (r"D:\Anaconda\python.exe runs\model-player\_scripts\t139_cleanup.py",
     G, "check for leftover engine processes on this batch's ports"),
    (r"D:\Anaconda\python.exe tools\playtest_artifact_index.py --roots t138-jev-v3 "
     r"--task TASK-138 --out-json runs\model-player\_index\_smoke139.json "
     r"--out-md runs\model-player\_index\_smoke139.md",
     G, "smoke test of the generalized artifact index"),
    (r"cmd /c dir /b runs\model-player\t136-playjev-v3", G,
     "recon: list the playjev sweep's games"),
    (r"cmd /c dir /b runs\model-player\t136-playjev-v3\pong", G,
     "recon: the playjev backend directory name"),
    (r"cmd /c dir /b /s runs\model-player\t136-jev-v3\tetris\player.json", G,
     "recon: the model backend directory name"),
]


def main(argv):
    existing = set()
    if os.path.isfile(LEDGER):
        for line in io.open(LEDGER, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("source") == "manual-backfill":
                existing.add(e.get("verbatim"))
    appended = 0
    with io.open(LEDGER, "a", encoding="utf-8") as fh:
        for cmd, cwd, why in CMD:
            if cmd in existing:
                continue
            try:
                argv_list = shlex.split(cmd, posix=False)
            except Exception:  # noqa: BLE001
                argv_list = [cmd]
            entry = {"ts": "2026-09-28T05:00:00", "cwd": cwd,
                     "argv": [str(a).strip('"') for a in argv_list],
                     "source": "manual-backfill", "verbatim": cmd, "why": why}
            fh.write(json.dumps(entry, ensure_ascii=False) + u"\n")
            existing.add(cmd)
            appended += 1
    total = sum(1 for l in io.open(LEDGER, encoding="utf-8") if l.strip())
    print("manual-backfill: appended %d entr(ies); ledger now %d lines"
          % (appended, total))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
