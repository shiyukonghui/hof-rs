# -*- coding: utf-8 -*-
"""TASK-101: the editor-phase facts of one run, straight out of its own responses.

    python editor_facts.py <run-dir>

Prints, without trusting report.json:
  * `e05` / `e09` -- the scene file's sha256 and byte count, and whether the refused
    duplicate batch left the file byte-for-byte identical;
  * `e06` -- the error code and how many node conflicts the refusal listed;
  * every `running_game_get_scene_tree` response -- how many node names it returned
    and how many of them start with '@' (an engine-renamed duplicate);
  * the build / validate / errors verdicts of the editor phase.
"""
import glob
import io
import json
import os
import re
import sys


def load(run, tag):
    path = os.path.join(run, tag + ".json")
    if not os.path.isfile(path):
        return None
    with io.open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        return json.load(handle)


def body(doc):
    if not doc:
        return None, None
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
    print("== %s" % run)
    shas = {}
    for tag in ("e05-read-1", "e09-read-2"):
        payload, _err = body(load(run, tag))
        if not isinstance(payload, dict):
            print("  %-14s ABSENT" % tag)
            continue
        sha = payload.get("sha256") or payload.get("sha")
        size = payload.get("bytes") or payload.get("size")
        shas[tag] = sha
        print("  %-14s sha256=%s bytes=%s" % (tag, sha, size))
    if len(shas) == 2:
        same = len(set(shas.values())) == 1
        print("  scene file unchanged by the refused batch: %s" % same)
    doc = load(run, "e06-batch-add-static-again")
    if doc and "error" in doc:
        err = doc["error"]
        data = err.get("data") or {}
        conflicts = data.get("conflicts") or []
        print("  e06 refusal code=%s conflicts=%d paths=%s" % (
            err.get("code"), len(conflicts),
            ",".join(c.get("node_path", "?") for c in conflicts[:6])))
    for tag in sorted(os.path.basename(p)[:-5]
                      for p in glob.glob(os.path.join(run, "*.json"))
                      if not os.path.basename(p).endswith(".request.json")):
        payload, _err = body(load(run, tag))
        if not isinstance(payload, dict):
            continue
        names = None
        if isinstance(payload.get("tree"), dict):
            names = collect([payload["tree"]])
        elif isinstance(payload.get("tree"), list):
            names = collect(payload["tree"])
        elif isinstance(payload.get("nodes"), list):
            names = collect(payload["nodes"])
        if names is not None:
            auto = [n for n in names if n.startswith("@")]
            print("  %-24s nodes=%d auto_named=%d %s" % (tag, len(names), len(auto), auto[:4]))
        if tag == "e12-build-csharp":
            print("  %-24s exit_code=%s duration_ms=%s" % (
                tag, payload.get("exit_code"), payload.get("duration_ms")))
        if tag == "e13-validate-scripts":
            print("  %-24s invalid_count=%s" % (tag, payload.get("invalid_count")))
        if tag == "e14-errors":
            print("  %-24s errors=%s" % (tag, payload.get("count")))


def collect(nodes):
    out = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        name = node.get("name")
        if name:
            out.append(name)
        for key in ("children", "nodes"):
            if isinstance(node.get(key), list):
                out.extend(collect(node[key]))
    return out

if __name__ == "__main__":
    main()
