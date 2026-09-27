#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-117 step C end-to-end: take ONE game straight out of the finished zip,
run its exported exe from the extracted directory, and require exit code 0 plus the
game's own READY line.  This is the check that answers "is the thing in the package
runnable", as opposed to "is the thing in dist runnable"."""
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
WORK = os.path.join(ROOT, "recovery", "work", "task117")
TMP = os.path.join(WORK, "unzip-run")
GAME = "pong"
READY = {"pong": "PONG_READY"}

LOG = []


def emit(s=""):
    LOG.append(s)
    print(s, flush=True)


def main():
    results = io.open(os.path.join(WORK, "package-results.json"), encoding="utf-8-sig").read()
    import json
    parts = json.loads(results)
    # find which part carries the game
    part = None
    for rec in parts:
        if GAME in rec["games"]:
            part = rec
            break
    if part is None:
        emit("ZIP-EXTRACT-RUN VERDICT: FAIL -- %s is in no part" % GAME)
        return 1
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)
    with zipfile.ZipFile(part["zip"]) as zf:
        names = zf.namelist()
        top = sorted(set(n.split("/")[0] for n in names))[0]
        prefix = "%s/games/%s/" % (top, GAME)
        members = [n for n in names if n.startswith(prefix)]
        zf.extractall(TMP, members=members)
    game_dir = os.path.join(TMP, top, "games", GAME)
    exe = os.path.join(game_dir, GAME + ".exe")
    emit("from zip    : %s" % part["name"])
    emit("extracted   : %d files -> %s" % (len(members), game_dir))
    emit("exe exists  : %s" % os.path.isfile(exe))
    if not os.path.isfile(exe):
        emit("ZIP-EXTRACT-RUN VERDICT: FAIL -- exe missing after extraction")
        with io.open(os.path.join(WORK, "zip-extract-run.txt"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(LOG) + "\n")
        return 1

    cmd_file = os.path.join(TMP, "run-from-zip.cmd")
    with io.open(cmd_file, "w", encoding="ascii", newline="\r\n") as fh:
        fh.write("@echo off\r\n")
        fh.write('cd /d "%s"\r\n' % game_dir)
        fh.write('"%s" --headless --quit-after 120\r\n' % exe)
        fh.write("echo FROMZIP_EXIT=%ERRORLEVEL%\r\n")
    so = os.path.join(TMP, "run.stdout.txt")
    se = os.path.join(TMP, "run.stderr.txt")
    with open(so, "wb") as fo, open(se, "wb") as fe:
        p = subprocess.run(["cmd.exe", "/c", cmd_file], stdout=fo, stderr=fe,
                           stdin=subprocess.DEVNULL, cwd=TMP)
    out = io.open(so, encoding="utf-8", errors="replace").read()
    err = io.open(se, encoding="utf-8", errors="replace").read()
    m = re.search(r"FROMZIP_EXIT=(\d+)", out)
    code = int(m.group(1)) if m else None
    ready = READY[GAME] in out
    emit("exit code   : %s" % code)
    emit("ready line  : %s (%s)" % (ready, READY[GAME]))
    emit("stdout tail : %s" % (out.strip().splitlines()[-1][:160] if out.strip() else "(empty)"))
    emit("stderr bytes: %d" % len(err))
    ok = code == 0 and ready
    emit("ZIP-EXTRACT-RUN VERDICT: %s" % ("PASS" if ok else "FAIL"))
    with io.open(os.path.join(WORK, "zip-extract-run.txt"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(LOG) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
