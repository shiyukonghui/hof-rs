#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-120 recon (read-only): the four sets the fix has to reason about.

  1. the `editor_state` (and every other) `readback` declaration re-judged under the
     TASK-120 A rules, with the witness verb / order / expect strength spelled out;
  2. the tools that have channel evidence but no boundary call, with the endpoint
     each of them has been seen on;
  3. channel-vs-verb violations across all 177 declarations;
  4. where the string "171" is claimed.

Run:  python recovery/work/task120/inspect.py [--out PATH]
"""
import argparse
import io
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import tool_coverage as tc  # noqa: E402


def endpoint_map(root):
    """tool -> sorted set of trace file kinds it has been seen on."""
    found = {}
    base = os.path.join(root, "runs")
    for dirpath, _d, filenames in os.walk(base):
        for fname in filenames:
            if not (fname.startswith("trace-") and fname.endswith(".jsonl")):
                continue
            kind = fname[len("trace-"):-len(".jsonl")]
            try:
                with io.open(os.path.join(dirpath, fname), "r", encoding="utf-8",
                             errors="replace") as handle:
                    for line in handle:
                        if '"tools/call"' not in line:
                            continue
                        try:
                            rec = json.loads(line)
                        except ValueError:
                            continue
                        tool = rec.get("tool")
                        if tool:
                            found.setdefault(tool, set()).add(kind)
            except IOError:
                pass
    return {k: sorted(v) for k, v in found.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "recovery", "tmp", "task120", "recon.txt"))
    args = ap.parse_args()
    out = io.open(args.out, "w", encoding="utf-8", newline="\n")

    def w(text=""):
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode("gbk", "replace").decode("gbk"))
        out.write(text + "\n")

    cov = json.load(io.open(os.path.join(ROOT, "coverage.json"), encoding="utf-8"))
    names = [t["name"] for t in json.load(io.open(
        os.path.join(ROOT, tc.CONTRACT), encoding="utf-8"))["result"]["tools"]]
    scopes, verbs = tc.scope_and_verb(ROOT)
    ledger = tc.load_module(os.path.join(ROOT, tc.LEDGER), "mcp_trace_ledger")
    channels = json.load(io.open(os.path.join(ROOT, tc.CHANNELS_FILE), encoding="utf-8"))["channels"]

    w("=== 2. channel evidence but no boundary ===")
    seventeen = [r for r in cov["tools"] if r["calls"] >= 5 and r["channel_evidence"] >= 1
                 and r["boundary"] == 0]
    for r in seventeen:
        w("  %-42s verb=%-10s chan=%-12s calls=%3d ok=%3d" %
          (r["tool"], r["verb"], r["evidence_channel"], r["calls"], r["ok"]))
    w("  count=%d" % len(seventeen))

    w("")
    w("=== channel evidence 0 with >=5 calls ===")
    for r in cov["tools"]:
        if r["calls"] >= 5 and r["channel_evidence"] == 0:
            w("  %-42s verb=%-10s chan=%-12s calls=%3d bnd=%d status=%s" %
              (r["tool"], r["verb"], r["evidence_channel"], r["calls"], r["boundary"], r["status"]))

    w("")
    w("=== 3. channel-vs-verb violations (strict rule) ===")
    bad = []
    for n in names:
        verb = tc.verb_of(n, verbs)
        ch = channels[n]["channel"]
        read = verb in tc.READ_VERBS
        if read and ch != tc.CHANNEL_PAYLOAD:
            bad.append((n, verb, ch, "read-verb not declared payload"))
        if (not read) and ch == tc.CHANNEL_PAYLOAD:
            bad.append((n, verb, ch, "action-verb declared payload"))
    for n, v, c, why in bad:
        w("  %-42s verb=%-10s chan=%-12s %s" % (n, v, c, why))
    w("  count=%d" % len(bad))

    w("")
    w("=== 4. where 171 is claimed ===")
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if any(x in dirpath for x in (os.sep + "runs", os.sep + ".git", os.sep + "tmp",
                                      os.sep + "rebuild", os.sep + "staging", os.sep + "backup",
                                      os.sep + "godot" + os.sep + "bin", os.sep + "GodotSharp",
                                      os.sep + "dist")):
            continue
        if os.sep + "godot" + os.sep in dirpath + os.sep and os.sep + "modules" + os.sep not in dirpath:
            # the engine source tree (CHANGELOG, core/...) is not the ledger's text
            continue
        for fname in filenames:
            if not fname.endswith((".md", ".json", ".txt", ".py", ".ps1", ".cmd")):
                continue
            p = os.path.join(dirpath, fname)
            try:
                if os.path.getsize(p) > 6 << 20:
                    continue
                with io.open(p, "r", encoding="utf-8", errors="replace") as h:
                    for i, line in enumerate(h, 1):
                        if "171" in line:
                            w("  %s:%d: %s" % (os.path.relpath(p, ROOT), i, line.strip()[:160]))
            except (IOError, OSError):
                pass

    # --- 1: re-judge every declaration under the new rules -------------------
    runs = sorted({d["run"] for d in tc.load_readback_declarations(ROOT) if d.get("run")})
    traces = []
    for run in runs:
        base = os.path.join(ROOT, run.replace("/", os.sep))
        if not os.path.isdir(base):
            continue
        for fname in sorted(os.listdir(base)):
            if fname.startswith("trace-") and fname.endswith(".jsonl"):
                traces.append((run, os.path.join(base, fname)))
    _stats, _corpus, run_index = tc.build_rows(ROOT, ledger, traces, verbs, scopes)

    decls = tc.load_readback_declarations(ROOT)
    w("")
    w("=== 1. all %d declarations re-judged under TASK-120 A ===" % len(decls))
    rejected = []
    for d in decls:
        tool = d["tool"]
        w("")
        w("-- %s (channel=%s)" % (tool, channels.get(tool, {}).get("channel")))
        w("   witness=%s run=%s why=%s" % (d.get("witness_tool"), d.get("run"), d.get("why")))
        w("   expect=%s expect_absent=%s" % (tc.expected_literals(d), tc.forbidden_literals(d)))
        first = (d.get("expect") or [None])[0]
        if isinstance(first, str) and tc.literal_is_key_only(first):
            w("   NOTE key-only literal: %r" % first)
        pointer, reason = tc.verify_readback(d, run_index, verbs)
        if pointer is None:
            rejected.append((tool, reason))
            w("   VERDICT=REJECTED")
            w("   reason=%s" % reason)
        else:
            w("   VERDICT=OK witness=%s verb=%s seq=%s" %
              (pointer["witness_tool"], pointer["witness_verb"], pointer["witness_seq"]))
        wst = (run_index.get(d.get("run"), {}) or {}).get(d.get("witness_tool")) or {}
        wtext = ""
        for p in wst.get("payloads", []):
            if p["seq"] == (pointer or {}).get("witness_seq"):
                wtext = tc.witness_payload_text(p) or ""
        if wtext:
            w("   witness payload: %s" % wtext[:1200])
    w("")
    w("=== rejected under the new rules: %d ===" % len(rejected))
    for tool, reason in rejected:
        w("  %-42s %s" % (tool, reason))

    out.close()


if __name__ == "__main__":
    main()
