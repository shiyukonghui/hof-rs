#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent count of the case-id families in recovery/TEST-CASES.md.

Read-only. Writes a JSON next to this script (no shell redirection).
"""
import hashlib
import io
import json
import os
import re

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
MATRIX = os.path.join(ROOT, "recovery", "TEST-CASES.md")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "counts.json")

with io.open(MATRIX, "r", encoding="utf-8") as h:
    text = h.read()

lines = text.split("\n")
sha = hashlib.sha256(text.encode("utf-8")).hexdigest().upper()
size = os.path.getsize(MATRIX)

# every distinct id-looking token per family, anywhere in the file
pats = {
    "TC-TOOL": re.compile(r"TC-TOOL-[A-Za-z0-9_]+"),
    "TC-GATE": re.compile(r"TC-GATE-g\d+"),
    "TC-M1": re.compile(r"TC-M1-[A-Za-z0-9_.\-]+"),
    "TC-ENG": re.compile(r"TC-ENG-\d+"),
    "TC-PY": re.compile(r"TC-PY-[^\s|`]+"),
    "TC-CONS": re.compile(r"TC-CONS-[A-Za-z0-9_.\-]+"),
}
per = {}
for fam, pat in pats.items():
    all_hits = pat.findall(text)
    per[fam] = {"distinct": len(set(all_hits)), "occurrences": len(all_hits),
                "sample": sorted(set(all_hits))[:5]}

# matrix A table rows: lines that start with "| TC-TOOL-"
row_a = [l for l in lines if l.startswith("| TC-TOOL-")]
# any table row starting with a case id
rows_by_family = {}
for fam, pat in pats.items():
    rows_by_family[fam] = sum(1 for l in lines if l.startswith("| " + fam + "-"))

# TC-M1 per-row ids and §-by-section
m1_rows = [l.split("|")[1].strip() for l in lines if l.startswith("| TC-M1-")]
eng_rows = [l.split("|")[1].strip() for l in lines if l.startswith("| TC-ENG-")]
gate_rows = [l.split("|")[1].strip() for l in lines if l.startswith("| TC-GATE-")]
cons_rows = [l.split("|")[1].strip() for l in lines if l.startswith("| TC-CONS-")]
py_rows = [l.split("|")[1].strip() for l in lines if l.startswith("| TC-PY-")]

# the declared table in 1.1
declared = {}
for l in lines:
    m = re.match(r"^\|\s*`(TC-[A-Z0-9]+)\*?`?\s*\|\s*(\d+)\s*\|", l)
    if m:
        declared[m.group(1)] = int(m.group(2))
    m2 = re.match(r"^\|\s*\*\*合计\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|", l)
    if m2:
        declared["TOTAL"] = int(m2.group(1))

out = {
    "matrix": MATRIX, "bytes": size, "lines": len(lines), "sha256": sha,
    "distinct_ids": per,
    "distinct_sum": sum(v["distinct"] for v in per.values()),
    "table_rows_by_family": rows_by_family,
    "row_id_counts": {"TC-M1": len(set(m1_rows)), "TC-ENG": len(set(eng_rows)),
                      "TC-GATE": len(set(gate_rows)), "TC-CONS": len(set(cons_rows)),
                      "TC-PY": len(set(py_rows)), "TC-TOOL": len(row_a)},
    "declared_in_section_1_1": declared,
    "sections": [l for l in lines if re.match(r"^#{2,3} ", l)],
}
with io.open(OUT, "w", encoding="utf-8", newline="\n") as h:
    h.write(json.dumps(out, ensure_ascii=False, indent=2))
print("wrote", OUT)
print(json.dumps({k: out[k] for k in ("bytes", "lines", "sha256", "distinct_ids",
                                      "table_rows_by_family", "row_id_counts",
                                      "declared_in_section_1_1")},
                 ensure_ascii=False, indent=2))
