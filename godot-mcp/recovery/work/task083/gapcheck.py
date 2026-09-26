# -*- coding: utf-8 -*-
"""TASK-083: for the still-damaged files, report the reconstruction target
revision and which line ranges of it were never captured by any read window -
i.e. exactly what cannot be recovered."""
import io
import json
import os
from collections import defaultdict

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"

FILES = [
    "tool_registry.cpp",
    "tools\\project_write_resource_scene.cpp",
    "tools\\editor_write_scene_editor.cpp",
    "tools\\running_game_node_write.cpp",
    "tools\\running_game_test_execution.cpp",
    "tools\\editor_node_batch_write.cpp",
]


def main():
    per = defaultdict(list)
    with io.open(os.path.join(IDX, "events-read.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            p = r.get("path", "").replace("/", "\\").lower()
            if "modules\\mcp_server\\" in p:
                per[p.split("modules\\mcp_server\\", 1)[1]].append(r)
    recs = {}
    with io.open(os.path.join(IDX, "reconstruction.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                r = json.loads(line)
                if r.get("rel", "").startswith("modules\\mcp_server\\"):
                    recs[r["rel"].split("modules\\mcp_server\\", 1)[1]] = r
    out = []
    for rel in FILES:
        rec = recs.get(rel.lower(), {})
        total = rec.get("read_total") or 0
        cov = set()
        for r in per.get(rel.lower(), []):
            for no, _ in (r.get("lines") or []):
                cov.add(no)
        miss = [i for i in range(1, total + 1) if i not in cov]
        rng = []
        for m in miss:
            if rng and m == rng[-1][1] + 1:
                rng[-1][1] = m
            else:
                rng.append([m, m])
        big = [r for r in rng if r[1] - r[0] + 1 >= 5]
        out.append("%-48s target=%-5d uncaptured=%-5d big-ranges=%s" % (rel, total, len(miss), big))
    with io.open(os.path.join(OUT, "gapcheck.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    for l in out:
        print(l)


if __name__ == "__main__":
    main()
