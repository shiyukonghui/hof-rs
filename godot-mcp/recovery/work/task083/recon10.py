# -*- coding: utf-8 -*-
"""TASK-083 recon 10: every module file whose reconstruction dropped lines."""
import io
import json
import os

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
BAK = r"C:\Users\wyl\AppData\Local\Temp\mcp044-module-backup\mcp_server"
TREE = r"H:\rebuild\godot\modules\mcp_server"
OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"


def main():
    rows = []
    with io.open(os.path.join(IDX, "reconstruction.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    mod = [r for r in rows if r.get("rel", "").startswith("modules\\mcp_server\\")]
    print("module reconstruction entries: %d" % len(mod))
    missing = [r for r in mod if (r.get("read_missing_n") or 0) > 0]
    print("with dropped lines: %d" % len(missing))
    lines = []
    nbak = 0
    for r in sorted(missing, key=lambda x: -x.get("read_missing_n", 0)):
        rel = r["rel"].replace("modules\\mcp_server\\", "")
        tp = os.path.join(TREE, rel.replace("/", os.sep))
        bp = os.path.join(BAK, rel.replace("/", os.sep))
        tag = []
        if os.path.exists(bp):
            tag.append("BAK")
            nbak += 1
        if not os.path.exists(tp):
            tag.append("TREE-MISSING")
        lines.append("%-60s miss=%-5d cov=%-6s pct=%-6s conf=%-4s tail=%-14s %s" % (
            rel, r.get("read_missing_n"), r.get("read_cov"), r.get("read_cov_pct"),
            r.get("conf"), r.get("miss_tail"), ",".join(tag)))
    with io.open(os.path.join(OUT, "damaged-list.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    # the splice target list = damaged and present in both
    tgt = []
    for r in sorted(missing, key=lambda x: x["rel"]):
        rel = r["rel"].replace("modules\\mcp_server\\", "")
        if os.path.exists(os.path.join(BAK, rel.replace("/", os.sep))) and os.path.exists(os.path.join(TREE, rel.replace("/", os.sep))):
            tgt.append(rel)
    with io.open(os.path.join(OUT, "splice-targets.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(tgt) + "\n")
    print("with a backup donor: %d -> splice-targets.txt" % len(tgt))
    for l in lines[:60]:
        print("  " + l)


if __name__ == "__main__":
    main()
