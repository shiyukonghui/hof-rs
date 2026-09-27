# -*- coding: utf-8 -*-
"""TASK-139 recon: are the two model services reachable?  Read-only health probes.

Iron rule 4: only 8080/8081, serial, no third-party endpoint.  Nothing here writes state.
"""
from __future__ import print_function

import json
import socket
import sys
import urllib.request


def port_open(p):
    s = socket.socket()
    try:
        s.settimeout(1.5)
        return s.connect_ex(("127.0.0.1", p)) == 0
    finally:
        s.close()


def get(url, timeout=8):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read(400).decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return None, "%s: %s" % (type(e).__name__, e)


def main(argv):
    for p in (8080, 8081):
        op = port_open(p)
        print("port %d open=%s" % (p, op))
        if op:
            for path in ("/health", "/v1/health", "/"):
                st, body = get("http://127.0.0.1:%d%s" % (p, path))
                print("   GET %s -> %s %s" % (path, st, body[:200].replace("\n", " ")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
