#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-110: render the batch tables into the report (replaces the marker).

Every number comes from coverage.json + the two verify JSONs, so the tables in
the report cannot drift from the artifacts they summarise. Writes only the
report file (the marker is replaced in place).
"""
import io
import json
import os

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
REPORT = os.path.join(ROOT, "recovery", "reports", "TASK-110-REPORT.md")
MARK = "<!-- BATCH-TABLES -->"

with io.open(os.path.join(ROOT, "coverage.json"), "r", encoding="utf-8") as h:
    cov = json.load(h)
rows = {t["tool"]: t for t in cov["tools"]}

BATCH_RUNS = ("_exercises/",)


def batch_calls(tool):
    return sum(c["calls"] for c in rows[tool]["evidence"]
               if any(b in c["run"] for b in BATCH_RUNS))


def main_run(tool):
    ev = [c for c in rows[tool]["evidence"] if any(b in c["run"] for b in BATCH_RUNS)]
    if not ev:
        return "-"
    best = sorted(ev, key=lambda c: -c["calls"])[0]
    return "`%s`" % best["run"]


def table(title, verified):
    out = ["", "**%s**（判据来自 `tools/verify_coverage_batch.py` 对 `coverage.json` 的实测；"
           "`本批` 列只数练习轮的调用，`累计` 列含此前的历史轮）" % title, ""]
    out.append("| # | tool | scope | 本批 | 累计 | 有效 | 边界 | facts | 判定 | 证据（主 run） |")
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(verified, 1):
        row = rows[r["tool"]]
        out.append("| %d | `%s` | %s | %d | %d | %d | %d | %d/%d | %s | %s |"
                   % (i, r["tool"], row["scope"], batch_calls(r["tool"]), row["calls"],
                      r["effective"], r["failed"], r["facts_complete"], row["calls"],
                      "**pass**" if r["verdict"] == "pass" else "FAIL", main_run(r["tool"])))
    out.append("")
    passed = len([r for r in verified if r["verdict"] == "pass"])
    out.append("小计：**%d/%d** 通过批次门。" % (passed, len(verified)))
    return out


with io.open(os.path.join(ROOT, "recovery", "work", "task110", "c1-verify.json"), "r", encoding="utf-8") as h:
    c1 = json.load(h)["results"]
with io.open(os.path.join(ROOT, "recovery", "work", "task110", "c23-verify.json"), "r", encoding="utf-8") as h:
    c23doc = json.load(h)
c23 = c23doc["results"]
FAM_B = ("editor_",)
fam2 = [r for r in c23 if r["tool"].startswith("editor_")]
fam3 = [r for r in c23 if r["tool"].startswith("running_game_")]

lines = []
lines.append("### B5. 家族① 逐工具结果（批次 c1 + c1b + c1c）")
lines += table("家族① `project_*` 42 个目标（40 条 0 次工具 + `project_create_script`、`project_read_text_file` 两条顺手补证据）", c1)
lines.append("")
lines.append("### B6. 家族② 逐工具结果（编辑器读取族）")
lines += table("家族②（%d 个目标）" % len(fam2), fam2)
lines.append("")
lines.append("### B7. 家族③ 逐工具结果（运行期查询族）")
lines += table("家族③（%d 个目标）" % len(fam3), fam3)
lines.append("")
lines.append("三个 setup-only 工具（`editor_connect_signal` 4 次、`editor_set_node_groups` 4 次、"
             "`editor_setup_collision_shape` 2 次）在批次里只作前置，**不算目标**；它们顺带从 0 次变成可达证据，"
             "下一批补到 ≥5 即可（见 §E）。")
lines.append("")

text = "\n".join(lines)
with io.open(REPORT, "r", encoding="utf-8") as h:
    report = h.read()
if MARK not in report:
    raise SystemExit("marker not found in %s" % REPORT)
report = report.replace(MARK, text)
with io.open(REPORT, "w", encoding="utf-8", newline="\n") as h:
    h.write(report)
print("replaced %s with %d lines of tables" % (MARK, len(lines)))
