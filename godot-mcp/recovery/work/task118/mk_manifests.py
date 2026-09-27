#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-118: fill in the c6/c7 manifests and supersede the two rejected declarations.

* c6-manifest.json / c7-manifest.json get the same `calls` array the other
  `_exercises` manifests carry (tag / tool / port / intent / note), derived from
  the session files, so the batch is checkable the same way.
* the two TASK-113-era declarations that the end-to-end reader rejected - 
  `editor_add_gridmap <- editor_get_scene_tree @ h3-task111` and
  `editor_connect_signal <- editor_list_signal_connections @ c4-v5-task111` -
  are MOVED (never deleted) into `readback_superseded` with the reason and the
  declaration that replaced them. TASK-115 set that precedent for the three
  TASK-113 declarations.
"""
import io
import json
import os
import re

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
SESS = os.path.join(ROOT, "tools", "sessions", "_exercises", "ex_close")
SUPERSEDE = {
    "tools/sessions/_exercises/ex_grid/h3-manifest.json": "editor_add_gridmap",
    "tools/sessions/_exercises/ex_write/c4-manifest.json": "editor_connect_signal",
}
SUPERSEDE_BY = {
    "editor_add_gridmap": ("runs/_exercises/ex_grid/c6-task118", "editor_get_scene_tree"),
    "editor_connect_signal": ("runs/_exercises/ex_grid/c6-task118", "editor_list_signal_connections"),
}


def load(path):
    with io.open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def save(path, doc):
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1))
        fh.write("\n")


def intent_of(tag, note):
    m = re.match(r"^[a-z0-9]+-\d+-(.+?)-(ok|probe|witness|setup|before|after)$", tag)
    if m:
        return m.group(2)
    return "ok"


def build_calls(session_path):
    doc = load(session_path)
    calls = []
    for call in doc.get("calls") or []:
        if not call.get("tool"):
            continue
        calls.append({
            "tag": call.get("tag"),
            "tool": call.get("tool"),
            "port": call.get("port"),
            "intent": intent_of(call.get("tag") or "", call.get("note") or ""),
            "note": call.get("note") or "",
        })
    return calls


def main():
    for batch in ("c6", "c7"):
        session_path = os.path.join(SESS, "%s-session.json" % batch)
        manifest_path = os.path.join(SESS, "%s-manifest.json" % batch)
        doc = load(manifest_path)
        doc["batch"] = batch
        doc["project"] = "projects/_exercises/ex_grid"
        doc["session"] = "tools/sessions/_exercises/ex_close/%s-session.json" % batch
        doc["calls"] = build_calls(session_path)
        doc.setdefault("readback", [])
        if batch == "c7":
            doc["readback"] = doc.get("readback") or []
            doc["_run"] = "runs/_exercises/ex_grid/c7-task118"
        save(manifest_path, doc)
        print("manifest %s: %d calls, %d readback declarations"
              % (manifest_path, len(doc["calls"]), len(doc.get("readback") or [])))

    for rel, tool in SUPERSEDE.items():
        path = os.path.join(ROOT, rel)
        doc = load(path)
        kept = []
        moved = []
        for item in doc.get("readback") or []:
            if item.get("tool") == tool:
                run, witness = SUPERSEDE_BY[tool]
                moved.append({
                    "tool": tool,
                    "witness_tool": item.get("witness_tool"),
                    "run": item.get("run"),
                    "why": item.get("why"),
                    "superseded_by": {"run": run, "witness_tool": witness,
                                      "declared_in": "tools/sessions/_exercises/ex_close/c6-manifest.json"},
                    "superseded_reason": "TASK-118: the declared witness could not be found in that run at all "
                                         "(no ok=true substantive call of the reader). The tool was re-exercised in "
                                         "runs/_exercises/ex_grid/c6-task118, where the same writer is paired with a "
                                         "witness that really answers with the written value. Moved, not deleted: the "
                                         "old wording stays here for audit.",
                })
            else:
                kept.append(item)
        if moved:
            doc["readback"] = kept
            bucket = doc.setdefault("readback_superseded", [])
            seen = {json.dumps(x, ensure_ascii=False, sort_keys=True) for x in bucket}
            for item in moved:
                key = json.dumps(item, ensure_ascii=False, sort_keys=True)
                if key not in seen:
                    bucket.append(item)
            save(path, doc)
        print("supersede %s: moved %d, kept %d" % (rel, len(moved), len(kept)))
    print("done")


if __name__ == "__main__":
    main()
