# -*- coding: utf-8 -*-
"""TASK-099: fold the per-iteration `--import` probe artefacts into one transcript.

The probe writes, for every iteration and round, a three-file sample (`.cmd`,
`.stdout.txt`, `.stderr.txt`). Those samples are byproducts; their verbatim contents
are what matters, so this writer folds them into one text file (the same shape
TASK-098 used for its probe) and the three-file samples themselves stay out of git.

Written by this Python writer rather than by a shell redirect (iron rule 1).
"""
import glob
import io
import os

ROOT = r"F:\moonbit-hof-rs\godot-mcp\recovery\work\task099"
LOG = os.path.join(ROOT, "logs", "importprobe")
OUT = os.path.join(LOG, "probe2-all.txt")

lines = []
cmds = sorted(glob.glob(os.path.join(LOG, "*.cmd")))
lines.append("TASK-099 --import crash probe -- verbatim transcript of %d sample(s)" % len(cmds))
lines.append("")
for cmd in cmds:
    base = cmd[:-4]
    lines.append("=" * 78)
    lines.append("SAMPLE %s" % os.path.basename(base))
    lines.append("-- cmd --")
    with io.open(cmd, "r", encoding="utf-8", errors="replace") as handle:
        lines.append(handle.read().rstrip("\n"))
    out = base + ".stdout.txt"
    if os.path.isfile(out):
        with io.open(out, "r", encoding="utf-8", errors="replace") as handle:
            body = handle.read().rstrip("\n").split("\n")
        lines.append("-- stdout (last 8 of %d line(s)) --" % len(body))
        lines.extend(body[-8:])
    err = base + ".stderr.txt"
    if os.path.isfile(err):
        with io.open(err, "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read().rstrip("\n")
        lines.append("-- stderr --")
        lines.append(text if text else "(empty)")
    lines.append("")

for name in ("probe2-frog-load0.json", "probe2-frogload-load8.json"):
    path = os.path.join(LOG, name)
    if os.path.isfile(path):
        with io.open(path, "r", encoding="utf-8") as handle:
            lines.append("RESULTS %s:" % name)
            lines.append(handle.read().rstrip("\n"))
        lines.append("")

with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
    handle.write("\n".join(lines) + "\n")
print("wrote %s (%d lines, %d bytes)" % (OUT, len(lines), os.path.getsize(OUT)))
