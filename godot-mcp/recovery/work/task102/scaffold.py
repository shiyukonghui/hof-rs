# -*- coding: utf-8 -*-
"""TASK-102: scaffold recovery\\work\\task102 from the TASK-101 helper set.

Copies the driver helpers and rewrites their task-specific paths (task101 -> task102,
TASK-101 -> TASK-102). Nothing is deleted; an existing destination is left alone unless
--force is given (destructive commands are refused by default).
"""
import io
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "task101")
NAMES = ["capture.ps1", "run_one.ps1", "reset_game_project.ps1", "commit.ps1",
         "check_session.py", "check_session_ps.ps1", "callread.py", "assertions.py",
         "extra_assertions.py", "samples.py", "run_summary.py", "pixel_recompute.py",
         "frames_recompute.py", "editor_facts.py", "peek.py"]

force = "--force" in sys.argv
os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
os.makedirs(os.path.join(HERE, "archive"), exist_ok=True)
for name in NAMES:
    src = os.path.abspath(os.path.join(SRC, name))
    dst = os.path.join(HERE, name)
    if not os.path.isfile(src):
        print("MISSING %s" % src)
        continue
    if os.path.exists(dst) and not force:
        print("keep    %s (already there)" % name)
        continue
    with io.open(src, "r", encoding="utf-8") as handle:
        text = handle.read()
    text = text.replace("task101", "task102").replace("TASK-101", "TASK-102")
    with io.open(dst, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("wrote   %s (%d bytes)" % (name, len(text)))
