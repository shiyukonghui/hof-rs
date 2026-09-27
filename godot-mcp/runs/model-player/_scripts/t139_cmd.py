# -*- coding: utf-8 -*-
"""TASK-139 §2.1: the COMMAND LEDGER wrapper (TASK-136's, continued).

Same discipline as `t136_cmd.py`: every command this batch runs goes through here, the
verbatim argv is APPENDED to `t136_commands.jsonl` BEFORE the command runs, and the child
is executed with `shell=False` so a `>`, `2>&1` or `1>NUL` token could not be interpreted as
a redirection even if one appeared.

Why a separate file at all: TASK-136's ledger is append-only and TASK-138's scanner cut it at
line 116 to define "TASK-136's commands".  This batch's scanner (`t139_scan_redirects.py`)
cuts at the last TASK-138 entry instead, so the two batches stay separable without rewriting
anything.

Usage (cmd):
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_cmd.py --cwd <dir> -- <cmd> <args...>

Iron rule 1: no shell redirection.  This file contains none.
"""
from __future__ import print_function

import io
import json
import subprocess
import sys
import time
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
LEDGER = os.path.join(HERE, "t136_commands.jsonl")     # the SHARED append-only ledger


def append(entry, ledger=None):
    with io.open(ledger or LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + u"\n")


def run(argv, cwd=None, ledger=None, env_extra=None):
    """Run one command through the wrapper's discipline, returning (rc, out, err).

    Used both by this file's `__main__` and by the batch's sweep drivers, so a sweep's
    per-game commands land in the ledger exactly like a hand-typed one.
    """
    cwd = cwd or ROOT
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "cwd": cwd, "argv": list(argv),
             "source": "t139-wrapper-call"}
    append(entry, ledger)
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    if env_extra:
        env.update(env_extra)
    t0 = time.time()
    try:
        p = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=False, env=env)
        out, err = p.communicate()
        rc = p.returncode
    except Exception as e:  # noqa: BLE001
        append({"ts": entry["ts"], "cwd": cwd, "argv": list(argv),
                "source": "t139-wrapper-call",
                "spawn_error": "%s: %s" % (type(e).__name__, e)}, ledger)
        return 127, "", "%s: %s" % (type(e).__name__, e)

    def dec(b):
        try:
            return b.decode("utf-8")
        except UnicodeDecodeError:
            return b.decode("cp936" if sys.platform == "win32" else "latin-1", "replace")

    return rc, dec(out), dec(err)


def main(argv):
    cwd = ROOT
    ledger = None
    env_extra = None
    if "--cwd" in argv:
        i = argv.index("--cwd")
        cwd = argv[i + 1]
        del argv[i:i + 2]
    if "--ledger" in argv:
        i = argv.index("--ledger")
        ledger = argv[i + 1]
        del argv[i:i + 2]
    if "--" in argv and argv.index("--") == 0:
        argv = argv[1:]
    if not argv:
        print("usage: t139_cmd.py [--cwd DIR] [--ledger PATH] -- <command> [args...]")
        return 2
    rc, out, err = run(argv, cwd=cwd, ledger=ledger)
    print("$ (cwd=%s) %s" % (cwd, " ".join(argv)))
    if out:
        print("----- stdout (%s) -----" % len(out))
        print(out, end="" if out.endswith("\n") else "\n")
    if err:
        print("----- stderr (%s) -----" % len(err))
        print(err, end="" if err.endswith("\n") else "\n")
    print("[t139_cmd] exit=%s" % rc)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
