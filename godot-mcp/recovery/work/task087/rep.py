# -*- coding: utf-8 -*-
"""All reporting goes through this module so the Windows console code page
cannot corrupt UTF-8 (this repo's documents are Chinese)."""
from __future__ import print_function
import io, os, sys

_LINES = []
_PATH = None


def set_report(path):
    global _PATH
    _PATH = path


def log(msg):
    _LINES.append(msg)


def flush():
    txt = "\n".join(_LINES) + "\n"
    try:
        sys.stdout.buffer.write(txt.encode("utf-8"))
        sys.stdout.buffer.flush()
    except Exception:
        pass
    if _PATH:
        with io.open(_PATH, "w", encoding="utf-8", newline="\n") as f:
            f.write(txt)
