#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-106 part C: run tools/game_report.py against a copy of a run directory and
show whether the new 未声明失败 column fires.

The old snake run (`runs\\snake\\snake-clean-task097`) is the known-positive case:
its `g19-turn-down` and `g22-self-collision` failed without being declared, and its
own `ledger-game.txt` already said `scenario_assertion_failed`. The report is
generated into a scratch copy so the archived run is not rewritten.

No shell redirection anywhere: the copy is done by this Python file and the report
is invoked through `subprocess` with stdout/stderr captured in memory.
"""
import io
import json
import os
import shutil
import subprocess
import sys

REPO = r"F:\moonbit-hof-rs\godot-mcp"
REPORT = os.path.join(REPO, "tools", "game_report.py")


def copy_top_level(src, dst):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    copied = 0
    for name in os.listdir(src):
        s = os.path.join(src, name)
        if os.path.isdir(s):
            continue  # shots-* stay where they are; the trace carries absolute paths
        shutil.copy2(s, os.path.join(dst, name))
        copied += 1
    return copied


def main():
    run_tag = sys.argv[1] if len(sys.argv) > 1 else "snake-clean-task097"
    game = sys.argv[2] if len(sys.argv) > 2 else "snake"
    src = os.path.join(REPO, "runs", game, run_tag)
    scratch = os.path.join(os.environ.get("TEMP", r"F:\moonbit-hof-rs\godot-mcp\recovery\work\task106\tmp"),
                           "task106-reporttest", run_tag)
    copied = copy_top_level(src, scratch)
    out = subprocess.run([sys.executable, REPORT, scratch, "--game=" + game, "--run-tag=" + run_tag],
                         cwd=REPO, capture_output=True)
    print("scratch   : %s (%d files copied)" % (scratch, copied))
    print("exit      : %d" % out.returncode)
    if out.stderr:
        print("stderr    :")
        print(out.stderr.decode("utf-8", "replace"))
    text = io.open(os.path.join(scratch, "report.md"), encoding="utf-8").read().splitlines()
    inside = False
    for line in text:
        if line.startswith("## 未声明失败"):
            inside = True
        elif inside and line.startswith("## "):
            break
        if inside:
            print(line)
    report = json.load(io.open(os.path.join(scratch, "report.json"), encoding="utf-8"))
    print("assertions summary (report.json):")
    print(json.dumps(report["assertions"], ensure_ascii=False, indent=1)[:2000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
