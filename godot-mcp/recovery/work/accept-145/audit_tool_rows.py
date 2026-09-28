#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A: matrix <-> artifact audit for the 177 TC-TOOL rows.

Read-only. Recomputes the schema shape (members/required/optional/defaults),
the declared evidence channel, boundary counts and the counterexample pointer
from the artifacts the matrix names, and reports every disagreement.
"""
import io
import json
import os
import re

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
DOCS = os.path.join(ROOT, "godot", "modules", "mcp_server", "docs")
MATRIX = os.path.join(ROOT, "recovery", "TEST-CASES.md")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_tool_rows.json")

tools = json.load(io.open(os.path.join(DOCS, "tools_list.renamed.json"), "r", encoding="utf-8"))["result"]["tools"]
schema = {t["name"]: t.get("inputSchema") or {} for t in tools}
desc = {t["name"]: t.get("description", "") for t in tools}
channels = json.load(io.open(os.path.join(ROOT, "tools", "tool_channels.json"), "r", encoding="utf-8"))["channels"]
cov = json.load(io.open(os.path.join(ROOT, "coverage.json"), "r", encoding="utf-8"))
covrows = {r["tool"]: r for r in cov["tools"]}

lines = io.open(MATRIX, "r", encoding="utf-8").read().split("\n")
rows = {}
col_anomalies = []
for i, l in enumerate(lines, 1):
    if not l.startswith("| TC-TOOL-"):
        continue
    cells = [c.strip() for c in l.strip().strip("|").split("|")]
    if len(cells) != 9:
        col_anomalies.append({"line": i, "ncols": len(cells)})
        continue
    rows[cells[0]] = {"line": i, "tool": cells[1].strip("`"), "purpose": cells[2],
                      "ptr": cells[3], "in": cells[4], "out": cells[5],
                      "neg": cells[6], "state": cells[7], "note": cells[8]}

report = {"n_rows": len(rows), "col_anomalies": col_anomalies, "mismatches": [],
          "checked": 0, "ptr_missing": [], "trace_neg_mismatch": [], "samples": {}}

def num(pattern, text, default=None):
    m = re.search(pattern, text)
    return m.group(1) if m else default

for cid, r in sorted(rows.items()):
    tool = r["tool"]
    s = schema.get(tool)
    entry = {"id": cid, "tool": tool, "line": r["line"]}
    report["checked"] += 1
    if s is None:
        report["mismatches"].append(dict(entry, what="tool not in contract"))
        continue
    props = s.get("properties") or {}
    req = s.get("required") if "required" in s else None
    has_required_key = "required" in s
    defaults = sorted(k for k, v in props.items() if isinstance(v, dict) and "default" in v)
    req_list = list(req) if req else []
    optional = sorted(k for k in props if k not in req_list)

    m = re.search(r"合法=(\d+) 成员（req (\d+) / opt (\d+)）", r["in"])
    if m:
        exp = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        got = (len(props), len(req_list), len(optional))
        if exp != got:
            report["mismatches"].append(dict(entry, what="schema counts", matrix=exp, actual=got))
    else:
        report["mismatches"].append(dict(entry, what="no schema-count text in 输入形式", in_cell=r["in"][:160]))

    # 必填 / 可选 / 默认 as written
    for label, actual, pat in (("必填", req_list, r"必填=([^;]*)"),
                               ("可选", optional, r"可选=([^;]*)")):
        mm = re.search(pat, r["in"])
        if mm:
            txt = mm.group(1).strip()
            if txt.startswith("无"):
                listed = []
            else:
                listed = sorted(x.strip() for x in txt.split(",") if x.strip())
            if listed != sorted(actual):
                report["mismatches"].append(dict(entry, what=label, matrix=listed, actual=sorted(actual)))
        else:
            report["mismatches"].append(dict(entry, what="no %s cell" % label))
    mm = re.search(r"默认=([^;]*)", r["in"])
    if mm:
        txt = mm.group(1).strip()
        listed = [] if txt.startswith("无") else sorted(x.split("=")[0].strip() for x in txt.split(",") if x.strip())
        if listed != defaults:
            report["mismatches"].append(dict(entry, what="默认", matrix=listed, actual=defaults))
    else:
        report["mismatches"].append(dict(entry, what="no 默认 cell"))

    # boundary from the ledger
    crow = covrows.get(tool) or {}
    mb = re.search(r"边界=台账 boundary=(\d+)", r["in"])
    if mb and int(mb.group(1)) != crow.get("boundary"):
        report["mismatches"].append(dict(entry, what="boundary", matrix=int(mb.group(1)),
                                         actual=crow.get("boundary")))
    # readback / channel
    ch = (channels.get(tool) or {}).get("channel")
    if ch and ("回读=%s" % ch) not in r["out"]:
        report["mismatches"].append(dict(entry, what="evidence channel not named in 回读",
                                         actual=ch, out=r["out"][:200]))

    # counterexample pointer: path:line
    ptrs = re.findall(r"`([^`]+?):(\d+)(?:-(\d+))?`", r["neg"] + " " + r["ptr"])
    files = []
    for p, ln, _ in ptrs:
        pp = p.replace("\\", "/")
        full = os.path.join(ROOT, pp)
        if not os.path.exists(full):
            # maybe relative to engine dir
            full2 = os.path.join(ROOT, "godot", pp)
            if os.path.exists(full2):
                full = full2
            else:
                report["ptr_missing"].append(dict(entry, pointer=p))
                continue
        files.append((full, int(ln)))
    entry["pointers_ok"] = len(files)

    # the counterexample itself: code/message from the trace line
    mc = re.search(r"代码|code=(-?\d+)", r["neg"])
    code = num(r"code=(-?\d+)", r["neg"])
    msgm = re.search(r'msg="([^"]*)"', r["neg"])
    if files and code:
        full, ln = files[0]
        with io.open(full, "r", encoding="utf-8", errors="replace") as h:
            tl = h.readlines()
        if ln <= len(tl):
            try:
                rec = json.loads(tl[ln - 1])
            except Exception:
                rec = None
            if rec is not None:
                ok = (rec.get("error_code") == int(code))
                msg_ok = True
                if msgm:
                    msg_ok = msgm.group(1)[:40] in (rec.get("error_message") or "")
                if not (ok and msg_ok and rec.get("ok") is False):
                    report["trace_neg_mismatch"].append(
                        dict(entry, matrix_code=int(code), actual_code=rec.get("error_code"),
                             matrix_msg=msgm.group(1)[:60] if msgm else None,
                             actual_msg=(rec.get("error_message") or "")[:60],
                             actual_ok=rec.get("ok")))
    elif files and not code:
        entry["neg_no_code"] = True
    report["samples"][cid] = entry

with io.open(OUT, "w", encoding="utf-8", newline="\n") as h:
    h.write(json.dumps(report, ensure_ascii=False, indent=2))
print("rows", report["n_rows"], "checked", report["checked"],
      "mismatches", len(report["mismatches"]), "ptr_missing", len(report["ptr_missing"]),
      "trace_neg_mismatch", len(report["trace_neg_mismatch"]))
print("col_anomalies", report["col_anomalies"][:10])
for x in report["mismatches"][:20]:
    print("MISMATCH", json.dumps(x, ensure_ascii=False)[:300])
for x in report["ptr_missing"][:10]:
    print("PTR-MISSING", json.dumps(x, ensure_ascii=False))
for x in report["trace_neg_mismatch"][:10]:
    print("TRACE-NEG", json.dumps(x, ensure_ascii=False)[:300])
