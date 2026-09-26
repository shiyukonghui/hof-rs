# -*- coding: utf-8 -*-
"""TASK-083 recon 3: per-file read-window coverage from the payload index."""
import io
import json
import os
import sys
from collections import defaultdict

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"

TARGET_REL = [
    "mcp_server.cpp",
    "tools/editor_node_read.cpp",
    "tools/running_game_read_scene.cpp",
]


def norm(p):
    return p.replace("/", "\\").lower()


def main():
    reads = defaultdict(list)   # relpath -> rows
    writes = defaultdict(list)
    edits = defaultdict(list)
    with io.open(os.path.join(IDX, "events-read.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            p = norm(r.get("path", ""))
            if "modules\\mcp_server\\" not in p:
                continue
            rel = p.split("modules\\mcp_server\\", 1)[1]
            reads[rel].append(r)
    for fn, store in (("events-write.jsonl", writes), ("events-edit.jsonl", edits)):
        with io.open(os.path.join(IDX, fn), "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                p = norm(r.get("path", ""))
                if "modules\\mcp_server\\" not in p:
                    continue
                rel = p.split("modules\\mcp_server\\", 1)[1]
                store[rel].append(r)

    out = []
    for rel in TARGET_REL:
        rows = reads.get(rel, [])
        by_total = defaultdict(list)
        for r in rows:
            by_total[r.get("totalLines")].append(r)
        summary = []
        for total, rs in sorted(by_total.items(), key=lambda kv: (kv[0] or 0)):
            covered = set()
            offs = []
            for r in rs:
                off = r.get("offset", 1)
                offs.append(off)
                for ln in (r.get("lines") or []):
                    covered.add(ln[0])
            full = set(range(1, (total or 0) + 1))
            miss = sorted(full - covered)
            # compress missing ranges
            ranges = []
            for m in miss:
                if ranges and m == ranges[-1][1] + 1:
                    ranges[-1][1] = m
                else:
                    ranges.append([m, m])
            summary.append({
                "totalLines": total,
                "windows": len(rs),
                "offsets": sorted(offs),
                "covered": len(covered & full),
                "missing": len(miss),
                "missing_ranges": ranges[:60],
                "latest_time": max(r.get("time", 0) for r in rs),
                "transcripts": sorted({r.get("f") for r in rs}),
            })
        out.append({
            "rel": rel,
            "read_rows": len(rows),
            "write_rows": len(writes.get(rel, [])),
            "edit_rows": len(edits.get(rel, [])),
            "revisions": summary,
        })

    with io.open(os.path.join(OUT, "coverage.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=1))

    # Also dump the list of module paths that have ANY read/write coverage.
    allp = sorted(set(list(reads) + list(writes) + list(edits)))
    with io.open(os.path.join(OUT, "module_paths.txt"), "w", encoding="utf-8", newline="\n") as f:
        for p in allp:
            f.write("%-70s reads=%-4d writes=%-3d edits=%d\n" % (
                p, len(reads.get(p, [])), len(writes.get(p, [])), len(edits.get(p, []))))
    print("coverage written; module paths=%d" % len(allp))


if __name__ == "__main__":
    main()
