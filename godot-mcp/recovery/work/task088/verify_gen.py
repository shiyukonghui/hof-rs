# -*- coding: utf-8 -*-
"""task088 (3): prove the repaired `_tmp_gen_b3_b5.py` still runs AND that its
now-derived contract size equals the real one.

It runs the generator against a COPY of `modules/mcp_server/docs` under the
scratch root, so the three real manifests are never touched, and prints the
`source.names` line the generator wrote into the fresh manifests.

usage: python verify_gen.py <outfile>
"""
from __future__ import print_function
import io, json, os, shutil, subprocess, sys

REPO = r"H:\rebuild\godot"
GENDIR = os.path.join(REPO, "modules", "mcp_server", "docs")
SCRATCH = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task088\gen_scratch"


def main():
    out = sys.argv[1]
    if os.path.isdir(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    docs_copy = os.path.join(SCRATCH, "docs")
    shutil.copytree(GENDIR, docs_copy)
    script = os.path.join(docs_copy, "scripts", "_tmp_gen_b3_b5.py")
    if not os.path.isfile(script):
        raise SystemExit("REFUSED: %s not found" % script)
    proc = subprocess.Popen([sys.executable, script, docs_copy],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, _ = proc.communicate()
    rc = proc.returncode
    contract = json.load(io.open(os.path.join(docs_copy, "tools_list.renamed.json"), encoding="utf-8"))
    real = len(contract["result"]["tools"])
    lines = []
    lines.append("generator exit=%d" % rc)
    lines.append("contract entries (read back from the copy) = %d" % real)
    for batch in ("b3", "b4", "b5"):
        p = os.path.join(docs_copy, "tool-groups-%s.json" % batch)
        if not os.path.isfile(p):
            lines.append("tool-groups-%s.json NOT written" % batch)
            continue
        doc = json.load(io.open(p, encoding="utf-8"))
        lines.append("tool-groups-%s.json: total=%s source.names=%s"
                     % (batch, doc.get("total"), doc.get("source", {}).get("names")))
        lines.append("  source.excluded=%s" % doc.get("source", {}).get("excluded"))
    lines.append("--- generator stdout (tail) ---")
    text = stdout.decode("utf-8", "replace")
    for l in text.strip().split("\n")[-10:]:
        lines.append("  " + l)
    data = "\n".join(lines) + "\n"
    io.open(out, "w", encoding="utf-8", newline="\n").write(data)
    print(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
