#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B: deliberate-break negative test, done on COPIES (no tracked file touched).

1. wrong channel declared (consistent snapshot) -> the gate must go red for that tool
2. snapshot drift (channel_evidence bumped, table untouched) -> must go red
3. unmutated control -> the same tool passes
"""
import hashlib
import io
import json
import os
import subprocess
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "break_test.json")
TARGET = "editor_add_audio_bus"

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

def sha(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest().upper()

orig_ch = os.path.join(ROOT, "tools", "tool_channels.json")
orig_cov = os.path.join(ROOT, "coverage.json")
before = {"channels": sha(orig_ch), "coverage": sha(orig_cov)}

ch = json.load(io.open(orig_ch, "r", encoding="utf-8"))
cov = json.load(io.open(orig_cov, "r", encoding="utf-8"))
ch_broken = json.loads(json.dumps(ch))
cov_broken = json.loads(json.dumps(cov))
ch_broken["channels"][TARGET]["channel"] = "pixel_effect"
row = next(r for r in cov_broken["tools"] if r["tool"] == TARGET)
orig_row = {k: row.get(k) for k in ("evidence_channel", "channel_evidence", "channel_evidence_ok",
                                    "pixel_effect_calls", "file_effect_calls", "read_payload_calls", "readback")}
row["evidence_channel"] = "pixel_effect"
row["channel_evidence"] = row.get("pixel_effect_calls", 0)
row["channel_evidence_ok"] = bool(row["channel_evidence"] >= 1)
ch_path = os.path.join(HERE, "channels-broken.json")
cov_path = os.path.join(HERE, "coverage-broken.json")
json.dump(ch_broken, io.open(ch_path, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
json.dump(cov_broken, io.open(cov_path, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)

# variant 2: drift only
cov_drift = json.loads(json.dumps(cov))
row2 = next(r for r in cov_drift["tools"] if r["tool"] == TARGET)
row2["channel_evidence"] = (row2.get("channel_evidence") or 0) + 1
row2["channel_evidence_ok"] = True
cov_drift_path = os.path.join(HERE, "coverage-drift.json")
json.dump(cov_drift, io.open(cov_drift_path, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)

def run(tag, coverage, channels):
    out = os.path.join(HERE, "break-%s.json" % tag)
    cmd = [sys.executable, os.path.join(ROOT, "tools", "verify_coverage_batch.py")]
    for m in MANIFESTS:
        cmd += ["--manifest", m]
    cmd += ["--coverage", coverage, "--channels", channels, "--json", out]
    p = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = p.stdout.decode("utf-8", "replace")
    stderr = p.stderr.decode("utf-8", "replace")
    res = {"exit": p.returncode, "json": out}
    if os.path.exists(out):
        j = json.load(io.open(out, "r", encoding="utf-8"))
        rec = next((r for r in j["results"] if r["tool"] == TARGET), None)
        res.update({"targets": j["targets"], "passed": j["passed"], "failed": j["failed"],
                    "target": {k: rec.get(k) for k in ("verdict", "evidence_channel", "channel_evidence",
                                                       "channel_evidence_ok", "snapshot_drift", "checks")} if rec else None})
    else:
        res["stderr_tail"] = stderr[-500:]
    if tag == "wrong-channel":
        res["stdout_has_contradicts_verb"] = "contradicts the tool verb" in stdout + stderr
    return res

result = {
  "target": TARGET, "original_row": orig_row,
  "control": run("control", orig_cov, orig_ch),
  "wrong_channel_declared_consistent_snapshot": run("wrong-channel", cov_path, ch_path),
  "snapshot_drift_only": run("drift", cov_drift_path, orig_ch),
  "file_hashes_before": before,
  "file_hashes_after": {"channels": sha(orig_ch), "coverage": sha(orig_cov)},
  "tracked_files_restored_exactly": before == {"channels": sha(orig_ch), "coverage": sha(orig_cov)},
}
with io.open(OUT, "w", encoding="utf-8", newline="\n") as h:
    h.write(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps(result, ensure_ascii=False, indent=2)[:5000])
