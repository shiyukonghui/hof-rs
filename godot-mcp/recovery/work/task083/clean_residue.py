# -*- coding: utf-8 -*-
"""TASK-083 step 4b: guarded removal of the three recovery-residue files.

Guards, in this order, all of which must pass before anything is removed:
  * the literal path must be absolute and non-empty
  * it must contain no wildcard and no `..`
  * it must start with H:\\rebuild\\godot\\
  * it must exist and not be a directory
  * the list is printed first
Read-only unless --confirm is passed.
"""
import hashlib
import io
import os
import sys

ROOT = r"H:\rebuild\godot"
TARGETS = [
    r"modules\mcp_server\gen_b2_restore.tmp.py",
    r"modules\mcp_server\tests\_task044_block.txt",
    r"modules\mcp_server\tests\__tmp_task052_tests.txt",
]


def guard(p):
    if not p or not os.path.isabs(p):
        raise SystemExit("REFUSE: not absolute: %r" % p)
    if any(c in p for c in "*?") or ".." in p:
        raise SystemExit("REFUSE: wildcard or .. in %r" % p)
    if not p.startswith(ROOT + os.sep):
        raise SystemExit("REFUSE: outside %s: %r" % (ROOT, p))
    if not os.path.exists(p):
        raise SystemExit("REFUSE: does not exist: %r" % p)
    if os.path.isdir(p):
        raise SystemExit("REFUSE: is a directory: %r" % p)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest().upper()


def main():
    confirm = "--confirm" in sys.argv
    full = [os.path.join(ROOT, t) for t in TARGETS]
    print("=== TASK-083 step 4b - residue removal list ===")
    for p in full:
        guard(p)
    for p in full:
        rel = os.path.relpath(p, ROOT)
        print("  %-58s %9d bytes  sha256=%s" % (rel, os.path.getsize(p), sha(p)[:16]))
    print("guards passed: absolute, no wildcard, no '..', inside %s, exists, not a directory" % ROOT)
    if not confirm:
        print("dry run - nothing removed (pass --confirm to remove)")
        return
    for p in full:
        os.remove(p)
        print("  removed %s -> Test-Path=%s" % (os.path.relpath(p, ROOT), os.path.exists(p)))


if __name__ == "__main__":
    main()
