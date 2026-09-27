#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-120: the per-declaration dossier the A3/A1 repairs are crafted from.

For every declaration the TASK-120 A rules reject, print:
  * the declaration as authored (why / expect / expect_absent);
  * the arguments the writer was actually called with (from the batch session file);
  * every call seq of the witnessed tool in that run;
  * for the witness payloads: a window around the declared literal when there is one
    (that is the JSON member the repair has to name), else the head of the payload.

Run:  python recovery/work/task120/dossier.py [tool ...]
"""
import io
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import tool_coverage as tc  # noqa: E402


def windows(text, needles, radius=260):
    out = []
    for needle in needles:
        start = 0
        while True:
            at = text.find(needle, start)
            if at < 0:
                break
            out.append((at, text[max(0, at - radius):at + radius]))
            start = at + len(needle)
            if len(out) >= 4:
                return out
    return out


def main():
    wanted = sys.argv[1:]
    out = io.open(os.path.join(ROOT, "recovery", "tmp", "task120", "dossier.txt"),
                  "w", encoding="utf-8", newline="\n")
    channels = json.load(io.open(os.path.join(ROOT, tc.CHANNELS_FILE), encoding="utf-8"))["channels"]
    scopes, verbs = tc.scope_and_verb(ROOT)
    ledger = tc.load_module(os.path.join(ROOT, tc.LEDGER), "mcp_trace_ledger")
    decls = tc.load_readback_declarations(ROOT)
    runs = sorted({d["run"] for d in decls if d.get("run")})
    traces = []
    for run in runs:
        base = os.path.join(ROOT, run.replace("/", os.sep))
        for fname in sorted(os.listdir(base)):
            if fname.startswith("trace-") and fname.endswith(".jsonl"):
                traces.append((run, os.path.join(base, fname)))
    _s, _c, run_index = tc.build_rows(ROOT, ledger, traces, verbs, scopes)

    for d in decls:
        tool = d["tool"]
        if wanted and tool not in wanted:
            continue
        pointer, reason = tc.verify_readback(d, run_index, verbs)
        if pointer is not None and not wanted:
            continue
        out.write("=" * 96 + "\n")
        out.write("TOOL %s (channel=%s verb=%s) -> %s\n" %
                  (tool, channels[tool]["channel"], tc.verb_of(tool, verbs),
                   "OK" if pointer else "REJECTED"))
        if reason:
            out.write("REASON %s\n" % reason[:400])
        out.write("DECL   %s\n" % json.dumps({k: v for k, v in d.items() if k != "declared_in"},
                                             ensure_ascii=False))
        manifest_path = os.path.join(ROOT, d["declared_in"].replace("/", os.sep))
        batch = os.path.basename(manifest_path).replace("-manifest.json", "")
        session_path = os.path.join(os.path.dirname(manifest_path), "%s-session.json" % batch)
        if os.path.isfile(session_path):
            sess = json.load(io.open(session_path, encoding="utf-8"))
            for call in sess.get("calls") or []:
                if call.get("tool") == tool:
                    out.write("CALL   %s %s\n" % (call.get("tag"),
                                                  json.dumps(call.get("arguments"), ensure_ascii=False)))
        st_t = run_index.get(d["run"], {}).get(tool) or {}
        out.write("WRITER seqs in run = %s\n" % st_t.get("seqs"))
        st_w = run_index.get(d["run"], {}).get(d.get("witness_tool")) or {}
        needles = tc.expected_literals(d) or [""]
        for p in st_w.get("payloads", []):
            text = tc.witness_payload_text(p) or ""
            out.write("WITNESS %s seq=%s len=%d\n" % (d.get("witness_tool"), p["seq"], len(text)))
            shown = windows(text, needles)
            if shown:
                for at, chunk in shown:
                    out.write("   @%d ...%s...\n" % (at, chunk))
            else:
                out.write("   HEAD %s\n" % text[:900])
    out.close()
    print("wrote recovery/tmp/task120/dossier.txt")


if __name__ == "__main__":
    main()
