# -*- coding: utf-8 -*-
"""Copy a reconstruction buffer into the working tree.

Guards, in this order:
  * the destination must be an absolute path under H:\\rebuild\\godot\\
  * the source must be an absolute path under
    C:\\Users\\wyl\\AppData\\Local\\Temp\\mcp-recovery\\
  * the file must exist, be non-empty, and contain no CR
  * the brace balance of the new text is printed before the copy

usage: python apply.py <src> <dst> [--expect-lines N]
"""
import io
import os
import sys

ALLOW_DST = r"H:\rebuild\godot\\"
ALLOW_SRC = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\\"


def guard(p, prefix, what):
    if not p:
        raise SystemExit("%s path is empty" % what)
    if not os.path.isabs(p):
        raise SystemExit("%s path is not absolute: %s" % (what, p))
    if "*" in p or "?" in p or ".." in p:
        raise SystemExit("%s path has a wildcard or ..: %s" % (what, p))
    if not os.path.normcase(os.path.normpath(p)).startswith(os.path.normcase(os.path.normpath(prefix))):
        raise SystemExit("%s path is outside %s: %s" % (what, prefix, p))


def main():
    src, dst = sys.argv[1], sys.argv[2]
    guard(src, ALLOW_SRC, "source")
    guard(dst, ALLOW_DST, "destination")
    if not os.path.isfile(src):
        raise SystemExit("source is not a file: %s" % src)
    text = io.open(src, encoding="utf-8", errors="replace").read()
    if not text.strip():
        raise SystemExit("source is empty: %s" % src)
    if "\r" in text:
        raise SystemExit("source contains CR: %s" % src)
    new = text.split("\n")
    if new and new[-1] == "":
        new.pop()
    old = None
    if os.path.isfile(dst):
        old = io.open(dst, encoding="utf-8", errors="replace").read().split("\n")
        if old and old[-1] == "":
            old.pop()
    print("src=%s" % src)
    print("dst=%s" % dst)
    print("old lines=%s  new lines=%d" % (len(old) if old is not None else "n/a", len(new)))
    if "--expect-lines" in sys.argv:
        want = int(sys.argv[sys.argv.index("--expect-lines") + 1])
        if len(new) != want:
            raise SystemExit("expected %d lines, reconstruction has %d" % (want, len(new)))
    with io.open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write(text if text.endswith("\n") else text + "\n")
    back = io.open(dst, encoding="utf-8", errors="replace").read()
    if back != (text if text.endswith("\n") else text + "\n"):
        raise SystemExit("read-back mismatch after write")
    print("wrote %d lines, read-back OK" % len(new))


if __name__ == "__main__":
    main()
