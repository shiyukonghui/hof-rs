# -*- coding: utf-8 -*-
"""TASK-084 housekeeping, guarded per iron rule 3.

1. delete the two scratch files that were created by an accidental `>` redirect
   before the Start-Process launcher existed (non-empty, absolute, no wildcard,
   no `..`, inside the allowed prefix; print the list first);
2. copy the build evidence into the tree so it is committed with the change.
"""
import hashlib
import io
import os
import shutil
import sys

ALLOWED = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task084" + "\\"
TREE = r"H:\rebuild\godot\modules\mcp_server\docs\reports\evidence\task084"
LOGS = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs"
WORK = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task084"
WRITE = "--write" in sys.argv

TO_DELETE = []
TO_COPY = [
    (LOGS + r"\task084_build3_notests.stdout.txt", TREE + r"\build3_notests.stdout.txt"),
    (LOGS + r"\task084_build3_notests.stderr.txt", TREE + r"\build3_notests.stderr.txt"),
    (LOGS + r"\task084_tu_probe.stderr.txt", TREE + r"\tu_probe.stderr.txt"),
    (WORK + r"\rec.py", TREE + r"\reconstruct-from-recorded-writes-and-edits.py"),
]


def guarded_delete(paths):
    print("guarded delete - candidates:")
    for p in paths:
        assert os.path.isabs(p), p
        assert ".." not in p and "*" not in p and "?" not in p, p
        assert p.startswith(ALLOWED), p
        assert os.path.exists(p), p
        assert os.path.isfile(p), p
        n = os.path.getsize(p)
        assert n > 0, p
        h = hashlib.sha256(io.open(p, "rb").read()).hexdigest()[:16]
        print("   %s  %d bytes  sha256[:16]=%s" % (p, n, h))
    for p in paths:
        if WRITE:
            os.remove(p)
            assert not os.path.exists(p)
            print("   removed (verified Test-Path=False): %s" % p)


def dump_error_lines():
    import re
    pat = re.compile(r"^(.*?)\((\d+)\)\s*:\s*(?:fatal )?error\s+([A-Z]+\d+):")
    src = LOGS + r"\task084_build3_notests.stderr.txt"
    raw = io.open(src, "rb").read()
    for enc in ("utf-8", "cp936", "gbk", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except Exception:  # noqa: BLE001
            continue
    hits = [l.strip() for l in text.split("\n") if pat.match(l.strip())]
    dst = TREE + r"\build3_error_lines.txt"
    print("dump %d error lines -> %s" % (len(hits), dst))
    if WRITE:
        os.makedirs(TREE, exist_ok=True)
        with io.open(dst, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(hits) + "\n")


def main():
    guarded_delete(TO_DELETE)
    if WRITE:
        os.makedirs(TREE, exist_ok=True)
    for src, dst in TO_COPY:
        assert os.path.isfile(src), src
        assert dst.startswith(TREE + "\\"), dst
        print("copy %s -> %s (%d bytes)" % (os.path.basename(src), dst, os.path.getsize(src)))
        if WRITE:
            shutil.copyfile(src, dst)
    dump_error_lines()
    print("mode: %s" % ("WRITE" if WRITE else "dry-run"))


if __name__ == "__main__":
    main()
