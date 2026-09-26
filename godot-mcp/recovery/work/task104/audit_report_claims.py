#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-104: re-derive every headline number of the report from the run products
and the ledger, and print them next to each other so the report can be read
against its own evidence one last time.

    python audit_report_claims.py
"""
import glob
import hashlib
import io
import json
import os
import re
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
WORK = os.path.join(ROOT, "recovery", "work", "task104")
GAMES = [("rtype", "rt-task104-r2"), ("puzzlebobble", "pb-task104-r1"), ("lunarlander", "ll-task104-r1")]


def answers(run):
    out = {}
    for path in sorted(glob.glob(os.path.join(run, "*.json"))):
        name = os.path.basename(path)
        if name.startswith(("import", "session", "call-index", "ledger", "report")) or name.endswith(".request.json"):
            continue
        try:
            body = json.load(io.open(path, encoding="utf-8-sig"))
        except Exception:
            continue
        if "result" not in body:
            continue
        content = (body["result"] or {}).get("content") or []
        if not content:
            continue
        try:
            out[name[:-5]] = json.loads(content[0].get("text", ""))
        except ValueError:
            out[name[:-5]] = content[0].get("text", "")
    return out


def ledger(run, name):
    path = os.path.join(run, name)
    if not os.path.isfile(path):
        return None
    text = io.open(path, encoding="utf-8-sig").read()
    row = {"calls": None, "verdicts": None, "facts": None}
    for line in text.splitlines():
        if line.startswith("calls="):
            row["calls"] = line.split("malformed_lines")[0].strip()
        if line.startswith("verdicts:"):
            row["verdicts"] = line.strip()
        if "reconstructible facts are all present" in line:
            row["facts"] = line.strip()
    return row


def main():
    print("=== per-game headline numbers, straight from the run products ===\n")
    total_e = total_g = 0
    for game, tag in GAMES:
        run = os.path.join(ROOT, "runs", game, tag)
        ans = answers(run)
        ed = ledger(run, "ledger-editor.txt")
        gm = ledger(run, "ledger-game.txt")
        rep = json.load(io.open(os.path.join(run, "report.json"), encoding="utf-8"))
        a = assert_summary_counts(run)
        e = int(re.search(r"calls=(\d+)", ed["calls"]).group(1)) if ed else 0
        g = int(re.search(r"calls=(\d+)", gm["calls"]).group(1)) if gm else 0
        total_e += e
        total_g += g
        frames = (rep.get("saved_frames") or {}).get("frames") or []
        print("%s  (%s)" % (game, tag))
        print("  calls            : %d (editor %d / game %d)" % (e + g, e, g))
        print("  editor verdicts  : %s" % (ed["verdicts"] if ed else "-"))
        print("  game verdicts    : %s" % (gm["verdicts"] if gm else "-"))
        print("  facts_complete   : %s | %s" % (ed["facts"], gm["facts"]))
        print("  assertions       : %d PASS / %d FAIL  (node_state=%d, screen_text=%d, scenario=%d)"
              % (a["total"], a["fail"], a["node"], a["screen"], a["scenario"]))
        print("  pixel_evidence   : %s" % json.dumps(rep.get("pixel_evidence"), ensure_ascii=False))
        print("  frames           : %d  diffs=%s  distinct_sha=%d/%d"
              % (len(frames),
                 [ (f.get("diff_vs_prev") or {}).get("changed_pixels") for f in frames[1:] ],
                 len(set(f["sha256"] for f in frames)), len(frames)))
        tree = sum(1 for k, v in ans.items() if isinstance(v, dict) and "tree" in v)
        nodes = []
        for k, v in ans.items():
            if isinstance(v, dict) and "tree" in v:
                c = [0, 0]
                walk(v["tree"], c)
                nodes.append(c[0])
        print("  scene trees      : %d reads, nodes=%s total=%d" % (tree, nodes, sum(nodes)))
        e05 = ans.get("e05-read-1", {})
        e09 = ans.get("e09-read-2", {})
        print("  scene sha        : %s (%s B) == %s ? %s"
              % (str(e05.get("sha256"))[:16], e05.get("size"),
                 str(e09.get("sha256"))[:16], e05.get("sha256") == e09.get("sha256")))
        b = ans.get("e12-build-csharp", {})
        v = ans.get("e13-validate-scripts", {})
        print("  build / validate : exit=%s %sms | invalid=%s not_compiled=%s"
              % (b.get("exit_code"), b.get("duration_ms"), v.get("invalid_count"), v.get("not_compiled_count")))
        print()
    print("=== twenty-game ledger total ===")
    log = io.open(os.path.join(ROOT, "GAME-LOOP-LOG.md"), encoding="utf-8").read().splitlines()
    te = tg = rows = 0
    for line in log:
        if not line.startswith("| "):
            continue
        f = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(f) < 5 or f[2] != "C#":
            continue
        m = re.search(u"\u7f16\u8f91\u5668 (\\d+) / \u6e38\u620f (\\d+)", f[3])
        if m:
            e, g = int(m.group(1)), int(m.group(2))
        else:
            m2 = re.match(u"^(\\d+) / (\\d+)\uff08(\\d+)\uff09", f[3])
            if not m2:
                continue
            e, g = int(m2.group(1)), int(m2.group(2))
        rows += 1
        te += e
        tg += g
    print("  rows=%d editor=%d game=%d TOTAL=%d" % (rows, te, tg, te + tg))
    return 0


def walk(node, counter):
    counter[0] += 1
    if str(node.get("name", "")).startswith("@"):
        counter[1] += 1
    for child in node.get("children") or []:
        walk(child, counter)


def assert_summary_counts(run):
    out = {"total": 0, "fail": 0, "node": 0, "screen": 0, "scenario": 0}
    for path in sorted(glob.glob(os.path.join(run, "*.json"))):
        name = os.path.basename(path)
        if name.startswith(("import", "session", "call-index", "ledger", "report")) or name.endswith(".request.json"):
            continue
        try:
            body = json.load(io.open(path, encoding="utf-8-sig"))
        except Exception:
            continue
        content = (body.get("result") or {}).get("content") or []
        if not content:
            continue
        try:
            a = json.loads(content[0].get("text", ""))
        except ValueError:
            continue
        if not isinstance(a, dict):
            continue
        if "passed" in a:
            if not a["passed"]:
                out["fail"] += 1
                continue
            out["total"] += 1
            if "property" in a and a.get("property"):
                out["node"] += 1
            elif a.get("assertion") == "screen_text" or "found" in a or "expected_text" in a:
                # the screen-text answer carries matched_element / expected_text and no
                # 'property'; the scenario answer carries results[] and an integer 'passed'
                out["screen"] += 1
            else:
                out["scenario"] += 1
    return out


if __name__ == "__main__":
    sys.exit(main())
