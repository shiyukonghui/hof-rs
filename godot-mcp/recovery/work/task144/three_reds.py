# -*- coding: utf-8 -*-
"""Scratch: the 3 genuine reds of the fixed batch gate, with what each lacks
(TASK-144 A.2)."""
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
cov = json.load(io.open(os.path.join(ROOT, "coverage.json"), encoding="utf-8"))
rows = {r["tool"]: r for r in cov["tools"]}
short = {s["tool"]: s for s in cov["channel_delta"]["still_short"]}
reg = cov["unreachable_registry"]

names = ["editor_set_auto_dismiss_dialogs", "os_deploy_to_android_device",
         "project_get_android_preset_info"]
for n in names:
    r = rows[n]
    print("== %s" % n)
    print("   channel=%s channel_evidence=%d calls=%d ok=%d boundary=%d facts=%d"
          % (r["evidence_channel"], r["channel_evidence"], r["calls"], r["ok"],
             r["boundary"], r["facts_complete"]))
    print("   status=%s legacy=%s ledger_class=%s note=%s"
          % (r["status"], r["status_legacy"], r["ledger_class"], r["ledger_class_note"]))
    print("   still_short=%s" % json.dumps(short.get(n), ensure_ascii=False))
    print("   verdicts=%s" % json.dumps(r["verdicts"], ensure_ascii=False))
    print("   flags=%s" % json.dumps(r["flags"], ensure_ascii=False))
    print("   readback=%s" % json.dumps(r.get("readback"), ensure_ascii=False))
    print("   evidence_runs=%s" % json.dumps(r["evidence"], ensure_ascii=False))
