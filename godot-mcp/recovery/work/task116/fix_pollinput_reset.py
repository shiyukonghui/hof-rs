#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TASK-116 fix D1, second half: `Reset*()` was switching polling back off at startup.

Flipping the field initialiser to `true` was not enough.  Every game's `_Ready()`
calls its own `ResetCounters()` / `ResetBoard()`, and those methods contain

    PollInput = false;

so the shipped process switched player input off again a few milliseconds after
startup.  (The first fixed sweep proved it: with the initialiser flipped, P2 still
reported 0/N actions responding.)

This script removes that assignment **only** from the reset methods that `_Ready`
calls, and leaves it in `ForceTestState`, which is the entry point whose entire
job is to pin a deterministic state for a test.  A test that wants polling off
still has `SetPollInput(false)` and `ForceTestState`.

The script prints every file it rewrites and the method it rewrote it in; it
never touches anything outside projects/<game>/src/*.cs.
"""

import io
import os
import re
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
PROJECTS = os.path.join(ROOT, "projects")
STARTUP_RESETS = ("ResetCounters", "ResetCountersKeepLevel", "ResetBoard", "ResetLevel")
METHOD = re.compile(r"^\s*(?:public|private|protected|internal)\s+[\w<>\[\],\s]+\s+(\w+)\s*\(")
ASSIGN = re.compile(r"^(\s*)PollInput\s*=\s*false\s*;(\s*//.*)?$")


def read(path):
    for enc in ("utf-8", "utf-8-sig"):
        try:
            return io.open(path, encoding=enc).read()
        except Exception:
            continue
    return None


def main(apply):
    games = sorted(d for d in os.listdir(PROJECTS)
                   if os.path.isdir(os.path.join(PROJECTS, d))
                   and not d.startswith("_") and not d.startswith("mcp"))
    total = 0
    for g in games:
        for dirpath, _dn, fns in os.walk(os.path.join(PROJECTS, g, "src")):
            for fn in sorted(fns):
                if not fn.endswith(".cs"):
                    continue
                p = os.path.join(dirpath, fn)
                txt = read(p)
                if txt is None:
                    continue
                lines = txt.splitlines(True)
                current = "<file>"
                out = []
                changed = 0
                for line in lines:
                    m = METHOD.match(line)
                    if m and "class " not in line:
                        current = m.group(1)
                    if current in STARTUP_RESETS and ASSIGN.match(line.rstrip("\r\n")):
                        indent = ASSIGN.match(line.rstrip("\r\n")).group(1)
                        out.append(indent + "// TASK-116 D1: was `PollInput = false;` -- that is what\n")
                        out.append(indent + "// switched player input off again right after _Ready() ran.\n")
                        out.append(indent + "// The deterministic entry point is ForceTestState / SetPollInput.\n")
                        changed += 1
                        continue
                    out.append(line)
                if changed:
                    total += changed
                    print("%s/%s: removed %d assignment(s), last method %s"
                          % (g, fn, changed, current))
                    if apply:
                        with io.open(p, "w", encoding="utf-8", newline="") as fh:
                            fh.write("".join(out))
    print("\n%d assignment(s) %s" % (total, "removed" if apply else "would be removed (dry run)"))
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
