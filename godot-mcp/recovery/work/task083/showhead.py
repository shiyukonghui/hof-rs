# -*- coding: utf-8 -*-
"""TASK-083 helper: dump a file's committed (HEAD) content to the work dir so the
pre-edit shape can be compared.  Uses subprocess WITHOUT any shell redirection."""
import io
import os
import subprocess
import sys

GIT = r"H:\rebuild\godot"
OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"


def main():
    rel = sys.argv[1]
    rev = sys.argv[2] if len(sys.argv) > 2 else "HEAD"
    p = subprocess.run(["git", "show", "%s:modules/mcp_server/%s" % (rev, rel.replace("\\", "/"))],
                       cwd=GIT, capture_output=True)
    if p.returncode != 0:
        raise SystemExit(p.stderr.decode("utf-8", "replace"))
    data = p.stdout
    name = "HEAD_" + os.path.basename(rel.replace("\\", "_"))
    with open(os.path.join(OUT, name), "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (os.path.join(OUT, name), len(data)))


if __name__ == "__main__":
    main()
