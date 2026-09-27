# -*- coding: utf-8 -*-
"""TASK-139: check (and optionally clean) for leftover engine processes on this batch's ports.

Read-only by default.  `--kill` kills only processes whose command line carries one of THIS
batch's own ports (9961..9968), using the same selector `playability_gate.tree_pids_for_port`
already uses -- never a broad name match.

Usage (cmd):
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_cleanup.py
    D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t139_cleanup.py --kill
"""
from __future__ import print_function

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import psutil  # noqa: E402

PORTS = (9961, 9962, 9963, 9964, 9965, 9966, 9967, 9968, 9969, 9970)


def holders():
    out = []
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cl = " ".join(p.info.get("cmdline") or [])
        except Exception:  # noqa: BLE001
            continue
        for port in PORTS:
            if "--mcp-port=%d" % port in cl:
                out.append({"pid": p.info["pid"], "name": p.info.get("name"),
                            "port": port, "cmdline": cl})
                break
    return out


def main(argv):
    h = holders()
    print("processes holding one of this batch's ports %s: %d" % (list(PORTS), len(h)))
    for x in h:
        print("  pid=%s name=%s port=%s %s" % (x["pid"], x["name"], x["port"],
                                              x["cmdline"][:160]))
    if "--kill" in argv:
        for x in h:
            try:
                psutil.Process(x["pid"]).kill()
                print("  killed pid=%s" % x["pid"])
            except Exception as e:  # noqa: BLE001
                print("  could not kill pid=%s: %s" % (x["pid"], e))
        print("after: %d" % len(holders()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
