# TASK-149 helper: stage the paths listed in a manifest ONE AT A TIME (`git add -- <path>`),
# then print exactly what is staged. No shell redirection is used anywhere: this script prints
# to stdout and writes its own run log through a Python file handle.
#
# Usage:  python recovery\work\task149_stage.py <manifest.txt> [--commit "<message>" [--file <msgfile>]]
from __future__ import print_function

import io
import os
import subprocess
import sys

ROOT = r"F:\moonbit-hof-rs"


def run(args, check=False):
    proc = subprocess.run(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    if check and proc.returncode != 0:
        raise SystemExit("FAILED (%d): %s\n%s" % (proc.returncode, " ".join(args), out))
    return proc.returncode, out


def manifest_paths(path):
    out = []
    with io.open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            out.append(line)
    return out


def main():
    manifest = sys.argv[1]
    message = None
    message_file = None
    argv = sys.argv[2:]
    i = 0
    while i < len(argv):
        if argv[i] == "--commit":
            message = argv[i + 1]
            i += 2
        elif argv[i] == "--file":
            message_file = argv[i + 1]
            i += 2
        else:
            raise SystemExit("unknown argument %r" % argv[i])

    paths = manifest_paths(manifest)
    print("manifest: %s (%d paths)" % (manifest, len(paths)))
    for rel in paths:
        full = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.exists(full):
            print("  MISSING  %s" % rel)
        code, out = run(["git", "add", "--", rel])
        status = "ok" if code == 0 else ("FAIL(%d)" % code)
        print("  add %-10s %s" % (status, rel))
        if code != 0:
            print("      %s" % out.strip())

    print("-" * 70)
    code, staged = run(["git", "diff", "--cached", "--name-status"])
    print("STAGED (%s):" % ("none" if not staged.strip() else "see below"))
    print(staged.rstrip())
    code, unstaged = run(["git", "status", "--short"])
    print("-" * 70)
    print("WORKING TREE (for the ownership self-check):")
    print(unstaged.rstrip())

    if message is None and message_file is None:
        return
    if message_file:
        with io.open(message_file, "r", encoding="utf-8") as handle:
            message = handle.read()
    print("-" * 70)
    if message_file:
        code, out = run(["git", "commit", "-F", message_file])
    else:
        code, out = run(["git", "commit", "-m", message])
    print("COMMIT exit=%d" % code)
    print(out.rstrip())
    if code != 0:
        raise SystemExit(1)
    code, log = run(["git", "log", "--oneline", "-3"])
    print("-" * 70)
    print("LOG:")
    print(log.rstrip())


if __name__ == "__main__":
    main()
