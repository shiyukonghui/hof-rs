#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B: independently re-derive the legacy-rule 45 false reds and compare the
committed before/after JSONs with my own re-run."""
import io, json, os, collections, hashlib
ROOT = r"F:\moonbit-hof-rs\godot-mcp"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "batch_audit.json")

MANIFESTS = [
 "tools/sessions/_exercises/ex_3d/h1-manifest.json", "tools/sessions/_exercises/ex_3d/h1b-manifest.json",
 "tools/sessions/_exercises/ex_anim/h2-manifest.json", "tools/sessions/_exercises/ex_anim2/h2c-manifest.json",
 "tools/sessions/_exercises/ex_audio/h5-manifest.json", "tools/sessions/_exercises/ex_bound/c8-manifest.json",
 "tools/sessions/_exercises/ex_close/c6-manifest.json", "tools/sessions/_exercises/ex_close/c7-manifest.json",
 "tools/sessions/_exercises/ex_editor/h7-manifest.json", "tools/sessions/_exercises/ex_files/c1-manifest.json",
 "tools/sessions/_exercises/ex_files/c1b-manifest.json", "tools/sessions/_exercises/ex_files/c1c-manifest.json",
 "tools/sessions/_exercises/ex_grid/h3-manifest.json", "tools/sessions/_exercises/ex_nav/h4-manifest.json",
 "tools/sessions/_exercises/ex_particles/h6-manifest.json", "tools/sessions/_exercises/ex_rec/h9-manifest.json",
 "tools/sessions/_exercises/ex_scene/c23-manifest.json", "tools/sessions/_exercises/ex_write/c4-manifest.json",
 "tools/sessions/_exercises/ex_write5/c4b-manifest.json", "tools/sessions/_exercises/ex_write6/c5-manifest.json",
]
cov = {r["tool"]: r for r in json.load(io.open(os.path.join(ROOT, "coverage.json"), "r", encoding="utf-8"))["tools"]}
channels = json.load(io.open(os.path.join(ROOT, "tools", "tool_channels.json"), "r", encoding="utf-8"))["channels"]

intents = {}
for m in MANIFESTS:
    doc = json.load(io.open(os.path.join(ROOT, m.replace("/", os.sep)), "r", encoding="utf-8"))
    for call in (doc.get("calls") or []):
        if "tool" in call:
            intents.setdefault(call["tool"], []).append(call.get("intent"))

legacy_pass, legacy_fail = [], []
for tool, declared in sorted(intents.items()):
    if all(x == "setup" for x in declared):
        continue
    row = cov.get(tool) or {}
    calls = row.get("calls", 0)
    effective = row.get("effective", 0)
    boundary = row.get("boundary", 0)
    edge = declared.count("edge")
    ok = calls >= 5 and effective >= 1 and (boundary >= 1 or edge >= 1)
    (legacy_pass if ok else legacy_fail).append(tool)

ch_of = lambda t: (channels.get(t) or {}).get("channel")
legacy_fail_by_channel = collections.Counter(ch_of(t) for t in legacy_fail)
# false red = failed by legacy rule but passes the current rule
after = json.load(io.open(os.path.join(ROOT, "recovery", "work", "task144", "batch-after.json"), "r", encoding="utf-8"))
after_verdict = {r["tool"]: r["verdict"] for r in after["results"]}
false_reds = [t for t in legacy_fail if after_verdict.get(t) == "pass"]
real_missing = [t for t in legacy_fail if after_verdict.get(t) != "pass"]

# compare my recheck with the committed after JSON
mine = json.load(io.open(os.path.join(HERE, "batch-recheck.json"), "r", encoding="utf-8"))
mine_v = {r["tool"]: (r["verdict"], r["channel_evidence"], r["evidence_channel"], r["checks"]) for r in mine["results"]}
cmted_v = {r["tool"]: (r["verdict"], r["channel_evidence"], r["evidence_channel"], r["checks"]) for r in after["results"]}
diffs = [t for t in set(mine_v) | set(cmted_v) if mine_v.get(t) != cmted_v.get(t)]

before = json.load(io.open(os.path.join(ROOT, "recovery", "work", "task144", "batch-before.json"), "r", encoding="utf-8"))
before_v = {r["tool"]: r["verdict"] for r in before["results"]}

def sha(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest().upper()

out = {
 "legacy_rule_fail": len(legacy_fail), "legacy_rule_pass": len(legacy_pass),
 "legacy_fail_by_channel": dict(legacy_fail_by_channel),
 "false_reds": len(false_reds), "false_reds_by_channel": dict(collections.Counter(ch_of(t) for t in false_reds)),
 "real_missing_from_legacy_rule": real_missing,
 "real_missing_by_channel": {t: ch_of(t) for t in real_missing},
 "false_reds_names": false_reds,
 "committed_before": {"targets": before["targets"], "passed": before["passed"],
                      "failed": before["targets"] - before["passed"],
                      "fail_by_channel": dict(collections.Counter(ch_of(r["tool"]) for r in before["results"] if r["verdict"] == "fail")),
                      "sha256": sha(os.path.join(ROOT, "recovery", "work", "task144", "batch-before.json"))},
 "committed_after": {"targets": after["targets"], "passed": after["passed"], "failed": after["failed"],
                     "sha256": sha(os.path.join(ROOT, "recovery", "work", "task144", "batch-after.json"))},
 "report_claimed_sha": {"batch-before": "90C1D86E66483848B30B9313D63A208C69AF75296132DED5D48B4752A1FA03C7",
                        "batch-after": "2F4F57A1DAFD95BD3F161B3EB3DCD57779EE2B2B136F8AB716BAD692C08354CD"},
 "my_recheck": {"targets": mine["targets"], "passed": mine["passed"], "failed": mine["failed"],
                "sha256": sha(os.path.join(HERE, "batch-recheck.json"))},
 "recheck_vs_committed_after_diffs": diffs,
 "committed_before_legacy_matches_my_legacy": {
     "before_fail_set_equals_my_legacy_fail": sorted(r["tool"] for r in before["results"] if r["verdict"] == "fail") == sorted(legacy_fail)},
}
with io.open(OUT, "w", encoding="utf-8", newline="\n") as h:
    h.write(json.dumps(out, ensure_ascii=False, indent=2))
print(json.dumps(out, ensure_ascii=False, indent=2)[:4000])
