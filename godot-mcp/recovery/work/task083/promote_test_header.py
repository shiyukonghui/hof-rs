# -*- coding: utf-8 -*-
"""TASK-083 step 4a: promote the `_low-confidence` tests/test_mcp_server.h, minus
the transient acceptance-probe block at lines 9506-9626.

The subtraction is a reconstruction judgement signed off by the decision maker
(TASK-083 ruling (a)).  This script prints the exact cut boundaries so the cut is
auditable, refuses to run if those boundaries do not match the expected text, and
writes only with --write.
"""
import hashlib
import io
import os
import sys

SRC = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\rebuild\_low-confidence\modules\mcp_server\tests\test_mcp_server.h"
DST = r"H:\rebuild\godot\modules\mcp_server\tests\test_mcp_server.h"
OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"

HEAD_MARK = "// Independent acceptance probes (appended by the acceptance agent for one run,"
TAIL_MARK = "then reverted). No assertion here is copied from the shipped tests."


def sha_b(b):
    return hashlib.sha256(b).hexdigest().upper()


def main():
    write = "--write" in sys.argv
    raw = open(SRC, "rb").read()
    text = raw.decode("utf-8")
    L = text.split("\n")
    print("source: %s" % SRC)
    print("  bytes=%d lines=%d sha256=%s" % (len(raw), len(L), sha_b(raw)[:24]))
    n = len(L)
    for i in range(9500, 9512):
        print("  %5d| %s" % (i, L[i - 1][:110]))
    print("  ...")
    for i in range(max(1, n - 8), n + 1):
        print("  %5d| %s" % (i, L[i - 1][:110]))
    assert HEAD_MARK in L[9506], "line 9507 is not the probe header: %r" % L[9506]
    assert TAIL_MARK in L[9507], "line 9508 is not the probe second line: %r" % L[9507]
    # find the end of the block: the last line of it, then keep the rest
    end = 9626
    print("cut: dropping lines 9506..%d (%d lines)" % (end, end - 9505))
    kept = L[:9505] + L[end:]
    # the block must contain exactly the transient probes
    dropped = L[9505:end]
    n_bad = sum(1 for x in dropped if "register_tool" in x)
    print("dropped block contains %d references to register_tool" % n_bad)
    out = "\n".join(kept)
    b = out.encode("utf-8")
    print("result: bytes=%d lines=%d sha256=%s" % (len(b), len(kept), sha_b(b)[:24]))
    print("kept static_assert count=%d, RegisterToolAccessProbe=%d" % (
        out.count("static_assert"), out.count("RegisterToolAccessProbe")))
    if write:
        with open(DST, "wb") as f:
            f.write(b)
        print("written -> %s" % DST)
    else:
        with open(os.path.join(OUT, "promoted-test-header.h"), "wb") as f:
            f.write(b)
        print("dry run -> work\\promoted-test-header.h")


if __name__ == "__main__":
    main()
