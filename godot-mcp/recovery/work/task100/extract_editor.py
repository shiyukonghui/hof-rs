# -*- coding: utf-8 -*-
"""TASK-100: pull the editor-phase and tree facts out of a finished run directory.

    python extract_editor.py <run-dir>

Everything is read from the per-call response files the driver wrote, so the numbers
below and the ledger cannot disagree. The `@`-name count is the D-3 check: a scene
that went through the TASK-097 fix must never come back carrying engine-renamed
duplicates.
"""
import glob
import io
import json
import os
import sys


def body_of(path):
    with io.open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        doc = json.load(handle)
    if "error" in doc:
        return None, doc["error"]
    content = (doc.get("result") or {}).get("content") or []
    if not content:
        return None, None
    try:
        return json.loads(content[0].get("text", "")), None
    except ValueError:
        return None, None


def main():
    run = sys.argv[1]
    print("run: %s" % run)
    for path in sorted(glob.glob(os.path.join(run, "e*.json"))):
        tag = os.path.basename(path)[:-5]
        if tag.endswith(".request"):
            continue
        body, error = body_of(path)
        if error is not None:
            conflicts = (error.get("data") or {}).get("conflicts")
            print("%-30s ERROR code=%s conflicts=%s" % (
                tag, error.get("code"), len(conflicts) if conflicts else None))
            for item in (conflicts or []):
                print("      conflict name=%s existing=%s node_path=%s" % (
                    item.get("requested_name"), item.get("existing_node_path"),
                    item.get("node_path")))
            continue
        if not isinstance(body, dict):
            continue
        if "sha256" in body and "size" in body:
            print("%-30s path=%s sha256=%s size=%s" % (tag, body.get("path"),
                                                       body["sha256"], body["size"]))
        elif "exit_code" in body:
            print("%-30s exit_code=%s duration_ms=%s" % (tag, body["exit_code"],
                                                         body.get("duration_ms")))
        elif "invalid_count" in body:
            print("%-30s invalid_count=%s count=%s not_compiled=%s" % (
                tag, body["invalid_count"], body.get("count"), body.get("not_compiled_count")))
        elif "errors" in body and "count" in body:
            print("%-30s count=%s available=%s" % (tag, body["count"], body.get("available")))

    names = []

    def walk(node):
        if not isinstance(node, dict):
            return
        name = node.get("name")
        if name:
            names.append(name)
        for child in (node.get("children") or []):
            walk(child)

    last_tree = None
    for path in sorted(glob.glob(os.path.join(run, "g*-tree.json"))):
        tag = os.path.basename(path)[:-5]
        if tag.endswith(".request"):
            continue
        body, error = body_of(path)
        if isinstance(body, dict) and isinstance(body.get("tree"), dict):
            walk(body["tree"])
            last_tree = tag
    at = [n for n in names if n.startswith("@")]
    print("tree node names seen : %d (across every scene-tree call)" % len(names))
    print("engine-renamed @names: %d %s" % (len(at), at[:10]))
    print("last tree call: %s" % last_tree)


if __name__ == "__main__":
    main()
