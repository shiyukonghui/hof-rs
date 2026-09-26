#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""game_report.py -- the per-game report of a godot-mcp test session.

TASK-091 item D (DECISIONS.md D137/D138).

Input : one run directory produced by tools/run_game_session.ps1
        (trace-*.jsonl, ledger-*.{txt,json}, shots-*/, engine-*.stdout.txt)
Output: <run>/report.md and <run>/report.json

The report answers, for one game, exactly the four questions the goal口径 asks:

  1. what did the ledger判定 for every call          -> verdict distribution
  2. is every call's evidence complete               -> facts_complete (n/m)
  3. did the operations actually change pixels       -> recomputed pixel diffs
  4. which defect is left, with its root cause       -> the defect list

Nothing here trusts the trace's own summary: the PNG pairs the capture lines name
are hashed and re-diffed with Pillow, and the ledger flags are read back from the
ledger's own JSON.
"""
import argparse
import hashlib
import io
import json
import os
import re
import sys

try:
    import numpy as np
    from PIL import Image
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False


def read_text(path):
    if not os.path.exists(path):
        return None
    with io.open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        return handle.read()


def read_json(path):
    text = read_text(path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def png_diff(a, b, threshold=10):
    """The engine's own rule (`mcp_capture.cpp:68` + `tool_helpers.cpp:1223`)."""
    if not HAVE_PIL:
        return None
    try:
        ia = np.asarray(Image.open(a).convert("RGBA"), dtype=np.int16)
        ib = np.asarray(Image.open(b).convert("RGBA"), dtype=np.int16)
    except Exception as exc:
        return {"error": str(exc)}
    if ia.shape != ib.shape:
        return {"comparable": False, "shape_a": list(ia.shape), "shape_b": list(ib.shape)}
    rgb = np.abs(ia[:, :, :3] - ib[:, :, :3])
    max_diff = rgb.max(axis=2)
    total = int(ia.shape[0] * ia.shape[1])
    changed = int((max_diff > threshold).sum())
    return {
        "comparable": True,
        "width": int(ia.shape[1]),
        "height": int(ia.shape[0]),
        "threshold": threshold,
        "changed_pixels": changed,
        "changed_pixels_any_difference": int((rgb.sum(axis=2) > 0).sum()),
        "total_pixels": total,
        "changed_pixel_ratio": (changed / float(total)) if total else 0.0,
    }


def capture_pairs(trace_path):
    """Every capture line in a trace, with the PNGs it names re-diffed here."""
    text = read_text(trace_path)
    pairs = []
    if not text:
        return pairs
    for line in text.splitlines():
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
        entry = {
            "seq": rec.get("seq"),
            "tool": rec.get("tool"),
            "changed": rec.get("changed"),
            "changed_pixels_reported": rec.get("changed_pixels"),
            "total_pixels_reported": rec.get("total_pixels"),
            "note": rec.get("note") or rec.get("reason"),
        }
        if before and after and os.path.exists(before) and os.path.exists(after):
            entry["before"] = before
            entry["after"] = after
            entry["before_sha256"] = sha256(before)
            entry["after_sha256"] = sha256(after)
            entry["before_bytes"] = os.path.getsize(before)
            entry["after_bytes"] = os.path.getsize(after)
            diff = png_diff(before, after)
            if diff:
                entry["recomputed"] = diff
                if diff.get("comparable") and rec.get("changed_pixels") is not None:
                    entry["recomputed_matches_reported"] = (
                        diff["changed_pixels"] == rec.get("changed_pixels"))
        pairs.append(entry)
    return pairs


def ledger_summary(ledger_json):
    if not ledger_json:
        return None
    rows = ledger_json.get("rows") or []
    verdicts = {}
    facts_complete = 0
    args_evidence = {}
    for row in rows:
        verdicts[row["verdict"]] = verdicts.get(row["verdict"], 0) + 1
        if row.get("facts_complete"):
            facts_complete += 1
        # TASK-092 (item B1): how the parameters' completeness was established.
        key = row.get("args_evidence") or "not_recorded_in_trace"
        args_evidence[key] = args_evidence.get(key, 0) + 1
    ineffective = [r for r in rows
                   if r["verdict"] in ("ok_no_effect_observed", "ok_effect_unavailable")]
    failed = [r for r in rows if r["verdict"] == "failed"]
    incomplete = [r for r in rows if not r.get("facts_complete")]
    return {
        "calls": ledger_json.get("calls"),
        "malformed_lines": ledger_json.get("malformed_lines"),
        "verdicts": verdicts,
        "facts_complete": facts_complete,
        "args_evidence": args_evidence,
        "rows": rows,
        "failed": failed,
        "ineffective": ineffective,
        "facts_incomplete": incomplete,
    }


def observable_lines(stdout_path, patterns):
    text = read_text(stdout_path) or ""
    out = []
    for line in text.splitlines():
        for pat in patterns:
            if pat in line:
                out.append(line.rstrip())
                break
    return out


def main():
    parser = argparse.ArgumentParser(description="Per-game report for one run directory.")
    parser.add_argument("run")
    parser.add_argument("--game", default="?")
    parser.add_argument("--run-tag", default="?")
    parser.add_argument("--stdout-pattern", action="append", default=None)
    parser.add_argument("--user-dir", default=None,
                        help="the game's user:// directory; its PNGs are diffed against each other")
    args = parser.parse_args()

    run = os.path.abspath(args.run)
    patterns = args.stdout_pattern or ["PONG_", "/root/", "SCRIPT ERROR", "ERROR", "WARNING"]

    report = {
        "game": args.game,
        "run_tag": args.run_tag,
        "run": run,
        "pillow": HAVE_PIL,
        "endpoints": {},
        "defects": [],
    }

    for name in ("editor", "game"):
        summary = ledger_summary(read_json(os.path.join(run, "ledger-%s.json" % name)))
        pairs = capture_pairs(os.path.join(run, "trace-%s.jsonl" % name))
        report["endpoints"][name] = {"ledger": summary, "captures": pairs}

    report["observable"] = {
        "editor": observable_lines(os.path.join(run, "engine-editor.stdout.txt"), patterns),
        "game": observable_lines(os.path.join(run, "engine-game.stdout.txt"), patterns),
    }

    # --- the frames the session saved by name (running_game_capture_screenshot)
    user_dir = args.user_dir
    if user_dir is None:
        user_dir = os.path.join(os.environ.get("APPDATA", ""), "Godot", "app_userdata", args.game)
    frames = []
    if os.path.isdir(user_dir):
        names = [n for n in os.listdir(user_dir) if n.lower().endswith(".png")]
        # oldest first: that is the order the session wrote them in.
        names.sort(key=lambda n: os.path.getmtime(os.path.join(user_dir, n)))
        for name in names:
            path = os.path.join(user_dir, name)
            frames.append({"name": name, "path": path, "bytes": os.path.getsize(path),
                           "sha256": sha256(path), "mtime": os.path.getmtime(path)})
    if frames:
        for frame in frames:
            try:
                with Image.open(frame["path"]) as im:
                    frame["size"] = [im.width, im.height]
            except Exception:
                frame["size"] = None
        # A diff is only meaningful between two frames of the same size: the editor's
        # screenshot is the whole editor window and the game's is the 800x600 viewport.
        # Each frame is therefore compared with the previous frame OF THE SAME SIZE.
        last_by_size = {}
        for frame in frames:
            key = tuple(frame["size"]) if frame["size"] else None
            prev = last_by_size.get(key)
            if prev is not None:
                frame["diff_vs_prev"] = png_diff(prev["path"], frame["path"])
                frame["diff_prev_name"] = prev["name"]
            last_by_size[key] = frame
    report["saved_frames"] = {"dir": user_dir, "frames": frames}

    # --- the defect list ------------------------------------------------------
    # A defect is claimed only where a fact supports it; every entry names the
    # evidence it came from, so a reader can disagree with the entry rather than
    # with the whole report.
    def why_incomplete(row):
        """Turn `facts_complete == False` into the reason the trace itself gives."""
        facts = row.get("facts") or {}
        reasons = []
        if not facts.get("args"):
            # TASK-092 (item B1): "cropped" is no longer the same as "lost". The
            # reason names which side of the sidecar rule failed, because the two
            # have different fixes (write the evidence vs. find the file).
            reasons.append("args_evidence=%s (args_bytes=%s; sidecar=%s)"
                           % (row.get("args_evidence") or "args_truncated=%s" % row.get("args_truncated"),
                              row.get("args_bytes"),
                              json.dumps(row.get("args_sidecar_detail") or {}, sort_keys=True)[:200]))
        if not facts.get("file_effect"):
            reasons.append("file_effect_status=%s (%s)" % (
                row.get("file_effect_status"), row.get("file_effect_evidence")))
        if not facts.get("scene_evidence"):
            reasons.append("scene_effect=%s, capture_status=%s, capture_reason=%s" % (
                row.get("scene_effect"), row.get("capture_status"), row.get("capture_reason")))
        if not facts.get("capture"):
            reasons.append("capture_status=%s, capture_reason=%s" % (
                row.get("capture_status"), row.get("capture_reason")))
        if not facts.get("times"):
            reasons.append("duration_ms/ts_ms missing")
        return "; ".join(reasons) or "unclassified"

    defects = []
    for name in ("editor", "game"):
        summary = report["endpoints"][name]["ledger"]
        if summary is None:
            defects.append({
                "id": "%s-0" % name,
                "severity": "blocking",
                "claim": "no ledger was produced for the %s endpoint" % name,
                "evidence": "ledger-%s.json is absent" % name,
                "root_cause": "the endpoint never answered (see engine-%s.stderr.txt)" % name,
            })
            continue
        for row in summary["facts_incomplete"]:
            defects.append({
                "id": "%s-facts-%s" % (name, row.get("call_id")),
                "severity": "low",
                "claim": "call %s (%s) has incomplete reconstructible facts" % (
                    row.get("call_id"), row.get("tool")),
                "evidence": "facts=%s" % json.dumps(row.get("facts"), sort_keys=True),
                "root_cause": why_incomplete(row),
            })
        for row in summary["failed"]:
            defects.append({
                "id": "%s-failed-%s" % (name, row.get("call_id")),
                "severity": "medium",
                "claim": "call %s (%s) failed with error %s" % (
                    row.get("call_id"), row.get("tool"), row.get("error_code")),
                "evidence": (row.get("error_data_json") or "")[:400],
                "root_cause": "declared failure" if (row.get("error_data_json") or "")
                              else "unexplained failure",
            })
    # pixels that did NOT move where a call claimed to move something
    for name in ("editor", "game"):
        for pair in report["endpoints"][name]["captures"]:
            diff = pair.get("recomputed") or {}
            if pair.get("changed") is True and diff.get("changed_pixels") == 0:
                defects.append({
                    "id": "%s-capture-%s" % (name, pair.get("seq")),
                    "severity": "high",
                    "claim": "the trace reports a screenshot change but the recomputed diff is 0",
                    "evidence": "%s -> %s" % (pair.get("before"), pair.get("after")),
                    "root_cause": "capture or diff rule mismatch",
                })
            if pair.get("recomputed_matches_reported") is False:
                defects.append({
                    "id": "%s-capture-mismatch-%s" % (name, pair.get("seq")),
                    "severity": "medium",
                    "claim": "recomputed pixel diff disagrees with the trace's own number",
                    "evidence": "trace=%s recomputed=%s" % (
                        pair.get("changed_pixels_reported"), diff.get("changed_pixels")),
                    "root_cause": "different diff rule or different PNG pair",
                })
    manual = read_text(os.path.join(run, "defects.md"))
    report["defects"] = defects
    report["defects_manual"] = manual

    # --- render ---------------------------------------------------------------
    lines = []
    lines.append("# Per-game report — `%s`" % args.game)
    lines.append("")
    lines.append("* run tag: `%s`" % args.run_tag)
    lines.append("* run dir: `%s`" % run)
    lines.append("* Pillow/numpy available for the independent pixel recomputation: **%s**" % HAVE_PIL)
    lines.append("")

    for name in ("editor", "game"):
        summary = report["endpoints"][name]["ledger"]
        lines.append("## %s endpoint (%s)" % (name, 9888 if name == "editor" else 9889))
        lines.append("")
        if summary is None:
            lines.append("**no ledger** — see `engine-%s.stderr.txt`." % name)
            lines.append("")
            continue
        lines.append("* calls: **%d** (malformed trace lines: %d)" % (
            summary["calls"] or 0, summary["malformed_lines"] or 0))
        lines.append("* verdicts: " + (", ".join(
            "%s=%d" % (k, summary["verdicts"][k]) for k in sorted(summary["verdicts"])) or "<none>"))
        lines.append("* `facts_complete`: **%d/%d**" % (summary["facts_complete"], summary["calls"] or 0))
        lines.append("* `args_evidence`: " + (", ".join(
            "%s=%d" % (k, summary["args_evidence"][k]) for k in sorted(summary["args_evidence"])) or "<none>"))
        lines.append("* failed: %d, no-effect observed: %d" % (
            len(summary["failed"]), len(summary["ineffective"])))
        lines.append("")

    # the pixel proof
    lines.append("## Pixel proof (recomputed, not taken on trust)")
    lines.append("")
    total_pairs = 0
    moved = 0
    for name in ("editor", "game"):
        pairs = report["endpoints"][name]["captures"]
        lines.append("### %s" % name)
        lines.append("")
        if not pairs:
            lines.append("*no capture pairs in the trace.*")
            lines.append("")
            continue
        lines.append("| seq | tool | trace changed | trace px | **recomputed px** | PNG sha equal |")
        lines.append("|---|---|---|---|---|---|")
        for pair in pairs:
            recomputed = (pair.get("recomputed") or {}).get("changed_pixels")
            total_pairs += 1
            if recomputed:
                moved += 1
            lines.append("| %s | `%s` | %s | %s | **%s** | %s |" % (
                pair.get("seq"), pair.get("tool"), pair.get("changed"),
                pair.get("changed_pixels_reported"), recomputed,
                pair.get("before_sha256") == pair.get("after_sha256")))
        lines.append("")
    lines.append("**capture pairs with a recomputed non-zero pixel diff: %d/%d**" % (moved, total_pairs))
    lines.append("")

    # the frames the session saved by name
    sf = report["saved_frames"]
    lines.append("### Saved frames (`user://`, `running_game_capture_screenshot`)")
    lines.append("")
    lines.append("Directory: `%s`" % sf["dir"])
    lines.append("")
    if not sf["frames"]:
        lines.append("*no saved frame found.*")
        lines.append("")
    else:
        lines.append("| frame | size | bytes | sha256 (first 12) | previous same-size frame | **recomputed px vs it** |")
        lines.append("|---|---|---|---|---|---|")
        for frame in sf["frames"]:
            diff = frame.get("diff_vs_prev") or {}
            size = "x".join(str(v) for v in frame["size"]) if frame.get("size") else "?"
            lines.append("| `%s` | %s | %d | `%s` | %s | **%s** |" % (
                frame["name"], size, frame["bytes"], frame["sha256"][:12],
                ("`%s`" % frame["diff_prev_name"]) if frame.get("diff_prev_name") else "-",
                diff.get("changed_pixels", "-")))
        lines.append("")
        lines.append("> `user://` survives between runs, so the same names are rewritten by each run; "
                     "the byte count, the sha256 and the diff above are recomputed from the files on "
                     "disk at report time.")
        lines.append("")

    # the causal chain from the game's own stdout
    lines.append("## The game's own stdout (causal chain)")
    lines.append("")
    for name in ("editor", "game"):
        obs = report["observable"][name]
        lines.append("### %s (%d line(s))" % (name, len(obs)))
        lines.append("")
        lines.append("```")
        for line in obs[:60]:
            lines.append(line)
        if len(obs) > 60:
            lines.append("... (%d more)" % (len(obs) - 60))
        lines.append("```")
        lines.append("")

    # defects
    lines.append("## Defect list")
    lines.append("")
    if not defects:
        lines.append("**no defect supported by the evidence of this run.**")
        lines.append("")
    else:
        lines.append("| id | severity | claim | evidence | root cause |")
        lines.append("|---|---|---|---|---|")
        for d in defects:
            lines.append("| `%s` | %s | %s | `%s` | %s |" % (
                d["id"], d["severity"], d["claim"],
                (d["evidence"] or "").replace("|", "\\|")[:200], d["root_cause"]))
        lines.append("")

    if manual:
        lines.append("## Defect list (curated)")
        lines.append("")
        lines.append(manual)
        lines.append("")

    md = "\n".join(lines) + "\n"
    with io.open(os.path.join(run, "report.md"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(md)
    slim = dict(report)
    for name in ("editor", "game"):
        summary = slim["endpoints"][name]["ledger"]
        if summary:
            summary["rows"] = [
                {k: row.get(k) for k in ("call_id", "request_id", "tool", "ok", "verdict",
                                         "facts", "facts_complete", "scene_effect", "scene_evidence",
                                         "capture_status", "capture_reason",
                                         "file_effect", "file_effect_status", "file_effect_evidence",
                                         "args_bytes", "args_truncated",
                                         "args_complete", "args_evidence", "args_sidecar_detail",
                                         "error_code", "result_flags", "error_flags")}
                for row in summary["rows"]]
    with io.open(os.path.join(run, "report.json"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(slim, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
