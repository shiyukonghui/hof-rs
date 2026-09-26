# TASK-101: append decisions-d149.md to the repository's DECISIONS.md.
#
# A Python writer rather than a shell redirect (iron rule 1: no `>` anywhere).
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
TARGET = os.path.join(ROOT, "DECISIONS.md")
SOURCE = os.path.join(HERE, "decisions-d149.md")

with io.open(TARGET, "r", encoding="utf-8") as handle:
    existing = handle.read()
with io.open(SOURCE, "r", encoding="utf-8") as handle:
    addition = handle.read()

if "## D149 —" in existing:
    print("SKIP: DECISIONS.md already carries D149")
else:
    if not existing.endswith("\n"):
        existing += "\n"
    existing += "\n" + addition
    with io.open(TARGET, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(existing)
    print("appended %d bytes from %s to %s" % (len(addition), SOURCE, TARGET))
