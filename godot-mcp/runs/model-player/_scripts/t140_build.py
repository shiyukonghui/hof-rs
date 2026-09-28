# -*- coding: utf-8 -*-
"""TASK-140 §1.B: build the four fixed games, one at a time, each log through a Python handle.

Iron rule 1: no shell redirection.  The command and its output are written by this process.
Reports per game: exit code, the `Build succeeded`/`Build FAILED` line, error count and
warning count, so "dotnet build 0 failures" is a number, not a claim.

Usage (through the ledger wrapper):
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_build.py [--only asteroids]
"""
from __future__ import print_function

import io
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUTDIR = os.path.join(ROOT, "runs", "model-player", "t140-build")
GAMES = ("asteroids", "frogger", "bomberman", "flappy")


def main(argv):
    games = list(GAMES)
    if "--only" in argv:
        i = argv.index("--only")
        games = argv[i + 1:]
    if not os.path.isdir(OUTDIR):
        os.makedirs(OUTDIR)
    results = []
    for g in games:
        proj = os.path.join(ROOT, "projects", g)
        argv2 = ["dotnet", "build", "-c", "Debug", "--nologo"]
        t0 = time.time()
        p = subprocess.Popen(argv2, cwd=proj, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, shell=False)
        out, _ = p.communicate()
        txt = out.decode("utf-8", "replace")
        secs = round(time.time() - t0, 1)
        log = os.path.join(OUTDIR, "%s.txt" % g)
        with io.open(log, "w", encoding="utf-8") as fh:
            fh.write(u"$ (cwd=%s) %s\n" % (proj, u" ".join(argv2)))
            fh.write(u"----- output (%d bytes) -----\n%s\n" % (len(txt), txt))
            fh.write(u"[t140_build] exit=%s\n" % p.returncode)
        errs = [ln for ln in txt.splitlines() if ": error " in ln]
        warns = [ln for ln in txt.splitlines() if ": warning " in ln]
        ok = [ln for ln in txt.splitlines() if "Build succeeded" in ln or "Build FAILED" in ln]
        rec = {"game": g, "exit": p.returncode, "seconds": secs,
               "errors": len(errs), "warnings": len(warns),
               "build_line": ok[-1].strip() if ok else None,
               "log": log, "error_lines": errs[:10], "warning_lines": warns[:10],
               "cmd": argv2, "cwd": proj}
        results.append(rec)
        print("%-12s exit=%s %5.1fs errors=%d warnings=%d  %s"
              % (g, p.returncode, secs, len(errs), len(warns), rec["build_line"]))
        for e in errs[:10]:
            print("    ERROR %s" % e.strip())
    with io.open(os.path.join(OUTDIR, "summary.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(results, ensure_ascii=False, indent=1))
    bad = [r for r in results if r["exit"] != 0 or r["errors"]]
    print("BUILD %s (%d/%d games with exit 0 and 0 errors)"
          % ("CLEAN" if not bad else "PROBLEMS", len(results) - len(bad), len(results)))
    if not os.path.isfile(os.path.join(OUTDIR, "summary.json")):
        return 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
