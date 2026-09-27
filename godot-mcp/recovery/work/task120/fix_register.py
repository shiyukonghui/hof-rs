#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-120 item D2/D3: the two register labels.

  D2  `needs_an_external_device` gains a PER-TOOL status (`items`), because
      TASK-119's D8 is right: one row listing three tool names reads as "all three
      are unmeasurable", while `os_list_android_devices` is actually PASSING
      (5 ok + 1 -32602) and only the other two are refusal-branch-only.
  D3  `editor_set_auto_dismiss_dialogs` is registered as its own class,
      `engine_not_implemented`, and is no longer left looking like an
      evidence-collection failure: 5 valid-input calls answer `-32000 Not
      implemented` (the two others are argument-validation refusals), so its
      success branch does not exist in this engine build.

Idempotent. Run:  python recovery/work/task120/fix_register.py
"""
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
PATH = os.path.join(ROOT, "tools", "tool_coverage_unreachable.json")

EXT_COMMENT = (
    "TASK-118 section D: tools whose code path exists but whose subject is outside this "
    "machine (a device, an Android preset). Measured, not inferred. TASK-120 item D2 adds "
    "`items`: the PER-TOOL status, because the three are not in the same state - one of them "
    "is already 达标 and the other two have only their refusal branch."
)
EXT_ITEMS = [
    {
        "tool": "os_list_android_devices",
        "ledger_status": "达标",
        "measured": "5 x ok + 1 x -32602 边界",
        "evidence": "runs/_exercises/ex_grid/c7-task118/trace-editor.jsonl",
        "note": ("runs adb for real (source \"adb devices -l\") and answers an empty device list; "
                 "the tool is PASSING. It is in this bucket only because the DEVICE it would list "
                 "is not on this machine - the measurement itself needs nothing external."),
    },
    {
        "tool": "project_get_android_preset_info",
        "ledger_status": "计数达标缺证据",
        "measured": "6 x ok=false（5 x -32000 no Android preset，1 x -32001 preset not found）",
        "evidence": "runs/_exercises/ex_grid/c7-task118/trace-editor.jsonl",
        "note": ("refusal branch only: no project in this repo has an Android export preset, so no "
                 "ok answer exists to measure. Needs an external preset, not a code change."),
    },
    {
        "tool": "os_deploy_to_android_device",
        "ledger_status": "计数达标缺证据",
        "measured": "6 x ok=false（5 x -32001，1 x -32602）",
        "evidence": "runs/_exercises/ex_grid/c7-task118/trace-editor.jsonl",
        "note": ("refusal branch only: no Android preset and no device. TASK-120 item B moved its "
                 "declared channel from `payload` to `file_effect`, so its evidence gate is at "
                 "least satisfiable once an export/deploy really writes an artifact."),
    },
]

ENGINE_COMMENT = (
    "TASK-120 item D3: tools whose SUCCESS branch does not exist in this engine build. They are "
    "not 'missing evidence' - there is nothing to collect. Kept separate from the count_only / "
    "缺证据 language so a reader cannot read them as an unfinished measurement."
)
ENGINE_ITEMS = [
    {
        "tool": "editor_set_auto_dismiss_dialogs",
        "verdict": "-32000 Not implemented: editor_set_auto_dismiss_dialogs",
        "evidence": "runs/_exercises/ex_editor/h7-task115/trace-editor.jsonl seq=74..80",
        "measured": ("7 calls, 0 ok: 5 calls with valid input all answer -32000 Not implemented "
                     "(seq 74-78); the other 2 (seq 79-80) are argument-validation refusals "
                     "(-32602 missing/mistyped 'enabled'). TASK-119's D5/R5 wrote '7/7 -32000': "
                     "the precise split is 5/5 of the valid-input calls."),
        "ledger_status_unchanged": ("计数达标缺证据 - the numeric rule cannot see WHY a channel has no "
                                    "evidence; this entry is the missing explanation, and the ledger's "
                                    "still-short table prints it as 引擎未实现 instead of the generic reason."),
    },
]


def main():
    raw = io.open(PATH, encoding="utf-8").read()
    doc = json.loads(raw)
    changed = []
    ext = doc.get("needs_an_external_device") or {}
    if ext.get("comment") != EXT_COMMENT:
        ext["comment"] = EXT_COMMENT
        changed.append("needs_an_external_device.comment")
    if ext.get("items") != EXT_ITEMS:
        ext["items"] = EXT_ITEMS
        changed.append("needs_an_external_device.items")
    doc["needs_an_external_device"] = ext
    engine = doc.get("engine_not_implemented")
    want = {"comment": ENGINE_COMMENT, "items": ENGINE_ITEMS, "count": len(ENGINE_ITEMS)}
    if engine != want:
        doc["engine_not_implemented"] = want
        changed.append("engine_not_implemented")
    note = doc.get("_task120_note")
    want_note = ("TASK-120: item D2 gives `needs_an_external_device` a per-tool status (one of the "
                 "three is passing); item D3 adds the `engine_not_implemented` class "
                 "(editor_set_auto_dismiss_dialogs: -32000 Not implemented, nothing to collect). "
                 "Members stay 74; reclassified stays 69; scope-excluded stays 5.")
    if note != want_note:
        doc["_task120_note"] = want_note
        changed.append("_task120_note")
    if not changed:
        print("unchanged")
        return
    out = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(out)
    print("changed: %s" % ", ".join(changed))


if __name__ == "__main__":
    main()
