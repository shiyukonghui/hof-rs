# -*- coding: utf-8 -*-
"""TASK-099: append the 2c-11 section to the engine repo's REBUILT-2C-MANIFEST.md.

Append-only, and it refuses to append twice. Written by this Python writer rather
than by a shell redirect (iron rule 1).
"""
import io
import os
import sys

MANIFEST = r"F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\docs\reports\REBUILT-2C-MANIFEST.md"
SECTION = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest-2c11.md")

with io.open(SECTION, "r", encoding="utf-8") as handle:
    addition = handle.read()
with io.open(MANIFEST, "r", encoding="utf-8") as handle:
    text = handle.read()

if "REBUILT-2C MANIFEST \u2014 2c-11" in text:
    sys.exit("REFUSED: the 2c-11 section is already in the manifest")

if not text.endswith("\n"):
    text += "\n"
text = text + addition
with io.open(MANIFEST, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(text)
print("appended %d bytes to %s" % (len(addition), MANIFEST))
print("manifest now %d bytes" % os.path.getsize(MANIFEST))
