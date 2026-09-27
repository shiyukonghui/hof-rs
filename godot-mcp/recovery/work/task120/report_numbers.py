#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-120 evidence: the before/after numbers, computed from the real files.

`before` = `git show HEAD:godot-mcp/coverage.json` (the ledger as TASK-118 left it,
the exact object TASK-119 accepted against); `after` = the refreshed
`coverage.json`. Everything printed here is derived, nothing is transcribed.

Run:  python recovery/work/task120/report_numbers.py
"""
import io
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REPO = os.path.abspath(os.path.join(ROOT, ".."))
OUT = os.path.join(ROOT, "recovery", "tmp", "task120", "numbers.txt")
LINES = []


def w(text=""):
    print(text)
    LINES.append(text)


def before_doc():
    raw = subprocess.check_output(["git", "-C", REPO, "show", "HEAD:godot-mcp/coverage.json"])
    return json.loads(raw.decode("utf-8"))


def main():
    before = before_doc()
    after = json.load(io.open(os.path.join(ROOT, "coverage.json"), encoding="utf-8"))
    b = {r["tool"]: r for r in before["tools"]}
    a = {r["tool"]: r for r in after["tools"]}

    w("=== corpus ===")
    for key in ("run_dirs", "trace_files", "calls", "ok", "failed", "distinct_tools"):
        w("  %-14s before=%-8s after=%-8s" % (key, before["corpus"][key], after["corpus"][key]))
    w("")
    w("=== status_counts ===")
    for key in ("达标", "计数达标缺证据", "未达(1-4)", "未达(0)"):
        w("  %-18s before=%-5s after=%-5s delta=%+d"
          % (key, before["status_counts"].get(key, 0), after["status_counts"].get(key, 0),
             after["status_counts"].get(key, 0) - before["status_counts"].get(key, 0)))
    w("")
    w("=== evidence_channel_counts (declared) ===")
    for key in ("file_effect", "pixel_effect", "editor_state", "payload"):
        w("  %-14s before=%-5s after=%-5s" % (key, before["evidence_channel_counts"].get(key, 0),
                                             after["evidence_channel_counts"].get(key, 0)))
    w("")
    w("=== evidence_tier_counts ===")
    for key in ("pixel_effect", "file_effect", "readback", "count_only", "no_calls"):
        w("  %-14s before=%-5s after=%-5s delta=%+d"
          % (key, before["evidence_tier_counts"].get(key, 0), after["evidence_tier_counts"].get(key, 0),
             after["evidence_tier_counts"].get(key, 0) - before["evidence_tier_counts"].get(key, 0)))
    w("")
    w("=== readback declarations ===")
    for key in ("declared", "verified", "content_checked", "declared_with_expect"):
        w("  %-20s before=%-5s after=%-5s" % (key, before["readback_declarations"][key],
                                             after["readback_declarations"][key]))
    w("  rejected             before=%-5s after=%-5s"
      % (len(before["readback_declarations"]["rejected"]), len(after["readback_declarations"]["rejected"])))
    w("")

    w("=== the 17 boundary-less tools: before -> after (item C) ===")
    w("%-42s %-12s %6s %6s %6s %-16s %6s %-16s"
      % ("tool", "channel", "chev_b", "bnd_b", "chev_a", "status_before", "bnd_a", "status_after"))
    seventeen = []
    for tool in sorted(a):
        rb, ra = b[tool], a[tool]
        if rb["calls"] >= 5 and rb["channel_evidence"] >= 1 and rb["boundary"] == 0:
            seventeen.append(tool)
            w("%-42s %-12s %6d %6d %6d %-16s %6d %-16s"
              % (tool, ra["evidence_channel"], rb["channel_evidence"], rb["boundary"],
                 ra["channel_evidence"], rb["status"], ra["boundary"], ra["status"]))
    w("  count=%d  (all promoted to 达标: %s)"
      % (len(seventeen), all(a[t]["status"] == "达标" for t in seventeen)))
    w("")

    w("=== still short after the fix (the 3 + the 5) ===")
    for tool in sorted(a):
        if a[tool]["status"] != "达标":
            w("  %-42s calls=%-4d bnd=%-3d chev=%-3d chan=%-12s class=%-24s status=%s"
              % (tool, a[tool]["calls"], a[tool]["boundary"], a[tool]["channel_evidence"],
                 a[tool]["evidence_channel"], a[tool]["ledger_class"] or "-", a[tool]["status"]))
    w("")

    w("=== the repaired declarations: expect before -> after ===")
    bv = before["readback_declarations"]["verified_by_tool"]
    av = after["readback_declarations"]["verified_by_tool"]
    for tool in sorted(av):
        be = (bv.get(tool) or {}).get("expect")
        ae = av[tool]["expect"]
        if be != ae:
            w("  %-42s %s\n      -> %s\n      witness=%s@%s verb=%s"
              % (tool, be, ae, av[tool]["witness_tool"], av[tool]["witness_seq"],
                 av[tool].get("witness_verb")))
    w("")

    w("=== channel declarations that changed ===")
    for tool in sorted(a):
        if b[tool]["evidence_channel"] != a[tool]["evidence_channel"]:
            w("  %-42s %s -> %s" % (tool, b[tool]["evidence_channel"], a[tool]["evidence_channel"]))
    w("")

    w("=== the two tools whose channel CHANGED: effect on their judgement ===")
    for tool in ("os_deploy_to_android_device", "editor_capture_screenshot"):
        w("  %-42s before: chan=%-12s chev=%-3d status=%s"
          % (tool, b[tool]["evidence_channel"], b[tool]["channel_evidence"], b[tool]["status"]))
        w("  %-42s after : chan=%-12s chev=%-3d status=%s bnd=%d"
          % ("", a[tool]["evidence_channel"], a[tool]["channel_evidence"], a[tool]["status"],
             a[tool]["boundary"]))
    w("")

    w("=== still_short reasons (verbatim from coverage.json) ===")
    for item in after["channel_delta"]["still_short"]:
        w("  %-42s %s" % (item["tool"], item["reason"]))
    w("")
    w("=== registry buckets ===")
    reg = after["unreachable_registry"]
    w("  members=%d drift=%d reclassified=%d scope_excluded=%d needs_an_external_device=%d"
      % (reg["members_total"], len(reg["drift"]), len(reg["reclassified"]),
         (reg["scope_excluded"] or {}).get("count", 0),
         (reg["needs_an_external_device"] or {}).get("count", 0)))
    w("  engine_not_implemented=%s"
      % json.dumps([i["tool"] for i in (reg["engine_not_implemented"] or {}).get("items") or []],
                   ensure_ascii=False))
    w("")

    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(LINES) + "\n")
    print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
