# -*- coding: utf-8 -*-
"""TASK-100: append the D148 entry to the repository's DECISIONS.md.

Append-only and idempotent: it refuses to append if the heading is already there.
Written by this Python writer rather than by a shell redirect (iron rule 1).
"""
import io
import os
import sys

DECISIONS = r"F:\moonbit-hof-rs\DECISIONS.md"
ENTRY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decisions-d148.md")

with io.open(ENTRY, "r", encoding="utf-8") as handle:
    addition = handle.read()
with io.open(DECISIONS, "r", encoding="utf-8") as handle:
    text = handle.read()

if "## D148 \u2014 TASK-100" in text:
    sys.exit("REFUSED: D148 is already in DECISIONS.md")

text = text.rstrip("\n") + "\n" + addition
with io.open(DECISIONS, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(text)
print("appended %d bytes to %s" % (len(addition), DECISIONS))
print("DECISIONS.md now %d bytes" % os.path.getsize(DECISIONS))
