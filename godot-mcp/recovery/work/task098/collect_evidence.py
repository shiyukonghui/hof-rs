# -*- coding: utf-8 -*-
"""TASK-098: run every evidence reader once and save its output as a log.

Iron rule 1 note: this uses Python's own `subprocess` with `stdout=<file handle>`,
which is a process API, not a shell redirection -- no `>`, `>>` or `|` is involved
anywhere. The saved logs are what TASK-098-REPORT.md quotes.
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
LOGS = os.path.join(HERE, "logs")
os.makedirs(LOGS, exist_ok=True)

PY = sys.executable

JOBS = [
    ("assertions-asteroids-r2.txt",
     [PY, os.path.join(HERE, "assertions.py"), os.path.join(ROOT, "runs", "asteroids", "ast-task098-r2")]),
    ("assertions-pacman-r2.txt",
     [PY, os.path.join(HERE, "assertions.py"), os.path.join(ROOT, "runs", "pacman", "pac-task098-r2")]),
    ("assertions-asteroids-r1.txt",
     [PY, os.path.join(HERE, "assertions.py"), os.path.join(ROOT, "runs", "asteroids", "ast-task098-r1")]),
    ("assertions-pacman-r1.txt",
     [PY, os.path.join(HERE, "assertions.py"), os.path.join(ROOT, "runs", "pacman", "pac-task098-r1")]),
    ("summary-asteroids-r2.txt",
     [PY, os.path.join(HERE, "run_summary.py"), os.path.join(ROOT, "runs", "asteroids", "ast-task098-r2")]),
    ("summary-pacman-r2.txt",
     [PY, os.path.join(HERE, "run_summary.py"), os.path.join(ROOT, "runs", "pacman", "pac-task098-r2")]),
    ("summary-asteroids-r1.txt",
     [PY, os.path.join(HERE, "run_summary.py"), os.path.join(ROOT, "runs", "asteroids", "ast-task098-r1")]),
    ("summary-pacman-r1.txt",
     [PY, os.path.join(HERE, "run_summary.py"), os.path.join(ROOT, "runs", "pacman", "pac-task098-r1")]),
    ("samples-asteroids-r2.txt",
     [PY, os.path.join(HERE, "samples.py"), os.path.join(ROOT, "runs", "asteroids", "ast-task098-r2"),
      "g08-samples-frozen", "g10-samples-drift", "g15-samples-flight"]),
    ("samples-pacman-r2.txt",
     [PY, os.path.join(HERE, "samples.py"), os.path.join(ROOT, "runs", "pacman", "pac-task098-r2"),
      "g10-samples-frozen", "g12-samples-patrol"]),
    ("pixel-recompute-asteroids-r2.txt",
     [PY, os.path.join(HERE, "pixel_recompute.py"), os.path.join(ROOT, "runs", "asteroids", "ast-task098-r2")]),
    ("pixel-recompute-pacman-r2.txt",
     [PY, os.path.join(HERE, "pixel_recompute.py"), os.path.join(ROOT, "runs", "pacman", "pac-task098-r2")]),
    ("frames-recompute-asteroids.txt",
     [PY, os.path.join(HERE, "frames_recompute.py"), "asteroids", "ast-",
      os.path.join(ROOT, "runs", "asteroids", "ast-task098-r2")]),
    ("frames-recompute-pacman.txt",
     [PY, os.path.join(HERE, "frames_recompute.py"), "pacman", "pac-",
      os.path.join(ROOT, "runs", "pacman", "pac-task098-r2")]),
    ("frames-recompute-pong.txt",
     [PY, os.path.join(HERE, "frames_recompute.py"), "pong", "pong-",
      os.path.join(ROOT, "runs", "pong", "pong-clean-task097")]),
    ("frames-recompute-breakout.txt",
     [PY, os.path.join(HERE, "frames_recompute.py"), "breakout", "breakout-",
      os.path.join(ROOT, "runs", "breakout", "breakout-clean-task097")]),
    ("frames-recompute-snake.txt",
     [PY, os.path.join(HERE, "frames_recompute.py"), "snake", "snake-",
      os.path.join(ROOT, "runs", "snake", "snake-clean-task097")]),
    ("copy-count-evidence.txt",
     [PY, os.path.join(HERE, "copy_count_evidence.py"),
      os.path.join(ROOT, "runs", "pong", "pong-clean-task097"), "c03-read-before"]),
    ("log-consistency.txt",
     [PY, os.path.join(HERE, "log_consistency.py"), ROOT]),
]


def main():
    for name, argv in JOBS:
        path = os.path.join(LOGS, name)
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            proc = subprocess.run(argv, stdout=handle, stderr=subprocess.STDOUT, cwd=ROOT)
        print("%-42s exit=%d -> %s" % (name, proc.returncode, path))
        if name == "copy-count-evidence.txt":
            # the other two games were counted into separate files by callers; do them here too
            for game in ("breakout", "snake"):
                sub = os.path.join(LOGS, "copy-count-evidence-%s.txt" % game)
                with io.open(sub, "w", encoding="utf-8", newline="\n") as handle:
                    p2 = subprocess.run(
                        [PY, os.path.join(HERE, "copy_count_evidence.py"),
                         os.path.join(ROOT, "runs", game, "%s-clean-task097" % game),
                         "c03-read-before"],
                        stdout=handle, stderr=subprocess.STDOUT, cwd=ROOT)
                print("%-42s exit=%d -> %s" % (os.path.basename(sub), p2.returncode, sub))


if __name__ == "__main__":
    main()
