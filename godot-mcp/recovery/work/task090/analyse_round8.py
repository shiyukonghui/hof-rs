#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-090 item C: analyse one round-8 session directory.

Independent of the trace where it can be: the PNGs the capture wrote are hashed
and (for the pairs it names) compared pixel by pixel with Pillow + numpy, and the
scene-tree snapshots the session took are compared with each other to decide
whether the executor left anything behind.

Usage:
    python analyse_round8.py <live-dir> [--label before|after]
Writes <live-dir>/analysis.json and prints a short text report.
"""
import io
import json
import os
import sys

try:
    import numpy as np
    from PIL import Image
    HAVE_PIL = True
except Exception:  # pragma: no cover - the evidence says which path ran
    HAVE_PIL = False


def load(path):
    # `Set-Content -Encoding UTF8` on Windows PowerShell 5.1 writes a BOM, so the
    # session's own response files are read with `utf-8-sig`.
    with io.open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        return handle.read()


def read_json(path):
    try:
        return json.loads(load(path))
    except Exception:
        return None


def tool_body(path):
    """The tool's own body, unwrapped from the MCP content envelope."""
    doc = read_json(path)
    if not isinstance(doc, dict):
        return None
    try:
        text = doc["result"]["content"][0]["text"]
    except Exception:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return None


def sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def png_diff(a, b, threshold=10):
    """Recompute the pixel difference the capture line reports.

    The engine's own rule (`MCPTools::compare_screenshot_pixels`,
    `tools/tool_helpers.cpp:1223`): a pixel counts as changed when
    `max(|dr|, |dg|, |db|) > threshold` over the RGB channels only, and the
    capture compares with `DEFAULT_DIFF_THRESHOLD = 10`
    (`mcp_capture.cpp:68`). Both the "any difference at all" number and the
    threshold number are reported, so the two can be told apart instead of one
    looking like a disagreement.
    """
    if not HAVE_PIL:
        return None
    try:
        ia = np.asarray(Image.open(a).convert("RGBA"), dtype=np.int16)
        ib = np.asarray(Image.open(b).convert("RGBA"), dtype=np.int16)
    except Exception as exc:
        return {"error": str(exc)}
    if ia.shape != ib.shape:
        return {"shape_a": list(ia.shape), "shape_b": list(ib.shape), "comparable": False}
    rgb = np.abs(ia[:, :, :3] - ib[:, :, :3])
    max_diff = rgb.max(axis=2)
    changed_threshold = int((max_diff > threshold).sum())
    changed_any = int((rgb.sum(axis=2) > 0).sum())
    total = int(ia.shape[0] * ia.shape[1])
    return {"comparable": True, "width": ia.shape[1], "height": ia.shape[0],
            "threshold": threshold,
            "changed_pixels": changed_threshold,
            "changed_pixels_any_difference": changed_any,
            "total_pixels": total,
            "changed_pixel_ratio": (changed_threshold / float(total)) if total else 0.0}


def main():
    live = sys.argv[1]
    label = "run"
    if "--label" in sys.argv:
        label = sys.argv[sys.argv.index("--label") + 1]

    out = {"dir": live, "label": label, "pillow": HAVE_PIL}

    # --- 1. the scene tree before / after the executor batch / at the end -----
    trees = {}
    for tag in ("g01-scene-tree-before", "g13-scene-tree-after-exec", "g30-scene-tree-final"):
        body = tool_body(os.path.join(live, tag + ".json"))
        trees[tag] = body
    def flat(tree):
        if not tree or "tree" not in tree:
            return None
        nodes = []
        def walk(node):
            nodes.append((node.get("path"), node.get("type")))
            for child in node.get("children", []) or []:
                walk(child)
        walk(tree["tree"])
        return nodes
    f1, f2, f3 = flat(trees["g01-scene-tree-before"]), flat(trees["g13-scene-tree-after-exec"]), flat(trees["g30-scene-tree-final"])
    out["scene_tree"] = {
        "before": f1,
        "after_executor": f2,
        "final": f3,
        "node_count_before": len(f1) if f1 else None,
        "node_count_after_executor": len(f2) if f2 else None,
        "node_count_final": len(f3) if f3 else None,
        "identical_before_after": f1 == f2,
        "identical_before_final": f1 == f3,
    }

    # --- 2. the executor's answers -------------------------------------------
    execs = {}
    for tag in sorted(os.listdir(live)):
        if tag.startswith(("g03-", "g04-", "g05-", "g06-", "g07-", "g08-", "g09-", "g10-", "g11-",
                           "g12-", "g14-", "g15-")) and tag.endswith(".json") and "request" not in tag:
            execs[tag[:-5]] = tool_body(os.path.join(live, tag))
    out["executor"] = execs

    # --- 3. the capture pairs the trace names, hashed independently ----------
    # Read the capture lines out of the trace and hash the PNGs the line points
    # at; the pixel comparison is then recomputed here, not taken on trust.
    pairs = []
    trace = os.path.join(live, "trace-game.jsonl")
    if os.path.exists(trace):
        for line in load(trace).splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("event") != "capture" or rec.get("status") != "done":
                continue
            before = (rec.get("before") or {}).get("path")
            after = (rec.get("after") or {}).get("path")
            if not before or not after:
                continue
            entry = {"seq": rec.get("seq"), "tool": rec.get("tool"),
                     "changed": rec.get("changed"),
                     "changed_pixels_reported": rec.get("changed_pixels"),
                     "total_pixels_reported": rec.get("total_pixels")}
            entry["before_sha256"] = sha256(before) if os.path.exists(before) else None
            entry["after_sha256"] = sha256(after) if os.path.exists(after) else None
            entry["before_bytes"] = os.path.getsize(before) if os.path.exists(before) else None
            entry["after_bytes"] = os.path.getsize(after) if os.path.exists(after) else None
            if entry["before_sha256"] and entry["after_sha256"]:
                diff = png_diff(before, after)
                if diff:
                    entry["recomputed"] = diff
                    if "changed_pixels" in diff:
                        entry["recomputed_matches_reported"] = (
                            diff["changed_pixels"] == rec.get("changed_pixels"))
                entry["before"] = before
                entry["after"] = after
            pairs.append(entry)
    out["capture_pairs"] = pairs

    with io.open(os.path.join(live, "analysis.json"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    print("=== %s (%s) ===" % (live, label))
    print("scene tree nodes: before=%s after_executor=%s final=%s" % (
        out["scene_tree"]["node_count_before"], out["scene_tree"]["node_count_after_executor"],
        out["scene_tree"]["node_count_final"]))
    print("  identical before/after-executor: %s" % out["scene_tree"]["identical_before_after"])
    print("  identical before/final:        %s" % out["scene_tree"]["identical_before_final"])
    print("capture pairs with a pair of PNGs: %d" % len(pairs))
    mismatches = [p for p in pairs if p.get("recomputed_matches_reported") is False]
    print("  recomputed pixel diff disagrees with the trace: %d" % len(mismatches))
    for p in pairs:
        r = p.get("recomputed") or {}
        print("  seq=%-3s %-38s trace_changed=%-5s trace_px=%-8s recomputed_px=%-8s sha_equal=%s" % (
            p["seq"], p["tool"], p["changed"], p["changed_pixels_reported"],
            r.get("changed_pixels"), p["before_sha256"] == p["after_sha256"]))
    print("wrote %s" % os.path.join(live, "analysis.json"))


if __name__ == "__main__":
    main()
