#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""playjev_serve_wsl.py -- start the deployed PlayJev service DETACHED (TASK-127).

Run this INSIDE WSL2 (it is a WSL-side launcher; on Windows it would have nothing to
start).  It is the same detachment pattern TASK-125 used for Jev:

  * `start_new_session=True` puts the server in its own session (setsid), so it survives
    the end of the agent session that launched it;
  * the server's stdout/stderr go straight to a Python-opened log file -- **no shell
    redirection is used anywhere**, which is one of TASK-127's hard rules;
  * the script prints `PID=...` and `LOGPATH=...` and exits immediately.

It deliberately touches NOTHING that belongs to Jev: `/opt/jev-venv`, the 8080 service
and `F:\\models\\NeoHorse-Jev-4B` are never referenced.

Usage (from WSL):

    python3 /mnt/f/moonbit-hof-rs/godot-mcp/tools/playjev_serve_wsl.py [port] [tag]

Defaults: port 8081, tag "detached".  Log lands in
`runs/playability/playjev-serve-<tag>-<stamp>.log` (runs/ is not tracked by git).
"""

import os
import subprocess
import sys
import time

VENV = "/opt/playjev-venv"
SRC = "/opt/playjev"                      # holds the `playjev/` package
MODEL = "/mnt/f/models/PlayJev-0.8B"      # the weights, OUTSIDE the repo
LOGDIR = "/mnt/f/moonbit-hof-rs/godot-mcp/runs/playability"


def main(argv):
    port = argv[1] if len(argv) > 1 else "8081"
    tag = argv[2] if len(argv) > 2 else "detached"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    logpath = os.path.join(LOGDIR, "playjev-serve-%s-%s.log" % (tag, stamp))
    os.makedirs(LOGDIR, exist_ok=True)

    env = dict(os.environ)
    env["CUDA_VISIBLE_DEVICES"] = "0"
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = SRC + os.pathsep + env.get("PYTHONPATH", "")

    cmd = [VENV + "/bin/python", "-m", "playjev.serve",
           "--ckpt", MODEL,
           "--host", "0.0.0.0",
           "--port", port,
           "--name", "playjev-0.8b",
           "--verbose"]

    logf = open(logpath, "w", encoding="utf-8", buffering=1)
    logf.write("# TASK-127 detached PlayJev server\n")
    logf.write("# started %s\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
    logf.write("# $ %s\n" % " ".join(cmd))
    logf.write("# cwd=%s  PYTHONPATH=%s  CUDA_VISIBLE_DEVICES=0\n" % (SRC, SRC))
    logf.flush()

    proc = subprocess.Popen(cmd, env=env, stdout=logf, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, start_new_session=True,
                            cwd=SRC)
    print("PID=%d" % proc.pid)
    print("LOGPATH=%s" % logpath)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
