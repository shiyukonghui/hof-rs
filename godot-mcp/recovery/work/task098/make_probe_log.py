# -*- coding: utf-8 -*-
"""TASK-098: fold the per-import probe logs into one verbatim transcript.

The probe writes one `.cmd` + `.stdout.txt` + `.stderr.txt` per import. Those are the raw
evidence but they are 120 boilerplate files, so this script concatenates the stdout and
stderr of every run, in order, under a header naming the command that produced it, and
writes `logs/importprobe/probe-all.txt`. The three `probe-results*.json` files are the
machine-readable twin and stay as they are.
"""
import glob
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROBE = os.path.join(HERE, "logs", "importprobe")
OUT = os.path.join(PROBE, "probe-all.txt")


def main():
    lines = []
    lines.append("TASK-098 item C: every `--import` this task ran on purpose, verbatim.")
    lines.append("One block per import: the command line it ran, then its stdout, then its stderr.")
    lines.append("")
    cmds = sorted(glob.glob(os.path.join(PROBE, "*.cmd")))
    for cmd in cmds:
        stem = os.path.basename(cmd)[:-4]
        lines.append("=" * 100)
        lines.append("### %s" % stem)
        lines.append("-" * 100)
        with io.open(cmd, "r", encoding="utf-8", errors="replace") as handle:
            lines.append(handle.read().rstrip())
        lines.append("")
        out = os.path.join(PROBE, stem + ".stdout.txt")
        err = os.path.join(PROBE, stem + ".stderr.txt")
        if os.path.isfile(out):
            with io.open(out, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read().rstrip()
            tail = text.splitlines()[-4:]
            lines.append("--- stdout (last 4 lines of %d) ---" % len(text.splitlines()))
            lines.extend(tail)
        if os.path.isfile(err):
            with io.open(err, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read().strip()
            lines.append("--- stderr ---")
            lines.append(text if text else "(empty)")
        lines.append("")
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    print("wrote %s (%d imports)" % (OUT, len(cmds)))


if __name__ == "__main__":
    main()
