# -*- coding: utf-8 -*-
"""TASK-083: copy the evidence for this task into the tree so the report can be
re-derived from the repository (H: only)."""
import io
import os
import shutil

WORK = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"
LOGS = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs"
DST = r"H:\rebuild\godot\modules\mcp_server\docs\reports\evidence\task083"

FILES = [
    "splice-report.json",
    "rebuild-report.json",
    "place2-report.json",
    "structural-scan.txt",
    "gapcheck.txt",
    "complete-reads.txt",
    "complete-reads.json",
    "damaged-list.txt",
    "target-vs-complete.txt",
    "splice-targets.txt",
    "shas-before.json",
    "survey.jsonl",
    "coverage.json",
    "build-summary.txt",
]
LOG_FILES = [
    "task083_build1_notests.stdout.txt",
    "task083_build1_notests.stderr.txt",
    "task083_build2_keepgoing_notests.stdout.txt",
    "task083_build2_keepgoing_notests.stderr.txt",
    "task082_build3_keepgoing.err.txt",
]


def main():
    if not os.path.isdir(DST):
        os.makedirs(DST)
    n = 0
    for fn in FILES:
        p = os.path.join(WORK, fn)
        if os.path.exists(p):
            shutil.copyfile(p, os.path.join(DST, fn))
            n += 1
    for fn in LOG_FILES:
        p = os.path.join(LOGS, fn)
        if os.path.exists(p):
            out = "raw-" + fn
            shutil.copyfile(p, os.path.join(DST, out))
            n += 1
    for fn in ["task083_build1_notests.stderr.utf8.txt", "task083_build2_keepgoing_notests.stderr.utf8.txt"]:
        p = os.path.join(WORK, fn)
        if os.path.exists(p):
            shutil.copyfile(p, os.path.join(DST, fn))
            n += 1
    print("copied %d files -> %s" % (n, DST))
    for fn in sorted(os.listdir(DST)):
        print("   %-52s %d" % (fn, os.path.getsize(os.path.join(DST, fn))))


if __name__ == "__main__":
    main()
