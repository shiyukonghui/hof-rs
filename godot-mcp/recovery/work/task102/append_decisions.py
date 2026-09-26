# -*- coding: utf-8 -*-
"""TASK-102: append the D150 block to the repository's DECISIONS.md.

The body lives in `decisions-d150.md` next to this script so it can be reviewed and
re-read by a human; this writer only appends it (with an explicit UTF-8 encoding,
no shell redirection) and refuses to run twice.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
DECISIONS = os.path.join(ROOT, "DECISIONS.md")
BODY = os.path.join(HERE, "decisions-d150.md")

with io.open(BODY, "r", encoding="utf-8") as handle:
    body = handle.read().rstrip("\n")
with io.open(DECISIONS, "r", encoding="utf-8") as handle:
    text = handle.read()

marker = "## D150 — TASK-102"
if marker in text:
    raise SystemExit("REFUSED: %s is already in DECISIONS.md" % marker)

if not text.endswith("\n"):
    text += "\n"
text += "\n" + body + "\n"

with io.open(DECISIONS, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(text)
print("appended D150 to %s (%d bytes)" % (DECISIONS, len(text)))
