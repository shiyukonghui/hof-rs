# -*- coding: utf-8 -*-
"""TASK-099: append the D147 entry to the repository's DECISIONS.md.

Append-only and idempotent: it refuses to append if the heading is already there.
Written by this Python writer rather than by a shell redirect (iron rule 1).
"""
import io
import os
import sys

DECISIONS = r"F:\moonbit-hof-rs\DECISIONS.md"
ENTRY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decisions-d147.md")

with io.open(ENTRY, "r", encoding="utf-8") as handle:
    addition = handle.read()
with io.open(DECISIONS, "r", encoding="utf-8") as handle:
    text = handle.read()

if "## D147 \u2014 TASK-099" in text:
    sys.exit("REFUSED: D147 is already in DECISIONS.md")

text = text.rstrip("\n") + "\n" + addition
with io.open(DECISIONS, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(text)
print("appended %d bytes to %s" % (len(addition), DECISIONS))
print("DECISIONS.md now %d bytes" % os.path.getsize(DECISIONS))
