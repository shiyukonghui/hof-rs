#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-147 B5b: check whether the matrix's two -32602 families really partition the 142 real probes."""
import io, json, collections

probe = json.load(io.open("recovery/work/task143/probe-live.json", encoding="utf-8"))["tools"]
refused = {n: r for n, r in probe.items() if r.get("verdict") == "refused_-32602"}
print("real refused_-32602 probes:", len(refused))

with_colon = [n for n, r in refused.items() if r["error_message"].startswith("Missing required parameter:")]
no_colon = [n for n, r in refused.items() if r["error_message"].startswith("Missing required parameter '")]
wrong_type = [n for n, r in refused.items()
              if r["error_message"].startswith("Parameter '") and "must be" in r["error_message"]]
unknown = [n for n, r in refused.items() if r["error_message"].startswith("Unknown parameter")]
print("  startswith `Missing required parameter:`  :", len(with_colon))
print("  startswith `Missing required parameter '` :", len(no_colon), no_colon)
print("  `Parameter '..' must be .., got ..`       :", len(wrong_type))
print("  `Unknown parameter ...`                   :", len(unknown))
print("  sum:", len(with_colon) + len(no_colon) + len(wrong_type) + len(unknown))
print()
print("matrix claims: 121 missing_required + 21 wrong_type = 142 (in the probe-live set)")
print("observed     : %d missing_required + %d wrong_type + %d third-family = %d"
      % (len(with_colon), len(wrong_type), len(no_colon),
         len(with_colon) + len(wrong_type) + len(no_colon)))
print()
for n in no_colon:
    print("third family: %-40s %r" % (n, refused[n]["error_message"]))
print()
print("total live -32602 probes for the two simulate tools (task144/u2):",
      len(json.load(io.open("recovery/work/task144/probe-u2.json", encoding="utf-8"))["tools"]))
print("142 + 2 =", 142 + 2, "(= section 1.2's '本轮活体探针真的收到 -32602 的工具 = 144')")
