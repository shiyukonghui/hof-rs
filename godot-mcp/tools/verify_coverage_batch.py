#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_coverage_batch.py -- check one coverage batch against its own gate.

The batch gate is per target tool:

    calls >= 5   and   channel_evidence >= 1   and
    (failed >= 1 or a declared edge call)

`calls` / `failed` come from `coverage.json` (tools/tool_coverage.py). The
evidence half is the **declared-channel** rule of TASK-118 item A: every
contract tool declares ONE authoritative evidence channel in
`tools/tool_channels.json`, and a tool is judged ON THAT CHANNEL, with
content-level evidence:

    file_effect   `ok_file_effect_observed`   - a file on disk really changed
    pixel_effect  `ok_effect_observed`        - the rendered frame really changed
    editor_state  a verified `witness_read` whose `expect` literal was found
                  verbatim in another, independent read call's payload
    payload       `ok=true` with a substantive payload (the answer IS the
                  measurement; the TASK-111 READ_VERBS rule)

TASK-144 item A -- why this file changed
----------------------------------------
This script used to apply `calls >= 5 and effective >= 1 and (boundary >= 1 or
edge)`, where `effective` is the **PRE-TASK-118** quantity: a call counted only
when a pixel or a file really moved. For every `editor_state`-channel tool
`effective` is 0 by construction - the whole point of TASK-118 was that an
editor write whose effect lives in the editor process' own memory moves neither
pixels (an exercise project's 2D viewport does not repaint for it) nor bytes
(nothing is saved). The stale rule therefore reported red for 45 tools that the
ledger marks 达标. The gate now judges `channel_evidence`, the quantity the
ledger itself judges, and it does not re-implement that quantity: it imports
`tools/tool_coverage.py` and calls that module's own `channel_evidence_count()`
and `load_channels()`, so the gate and the ledger cannot drift apart again.
`effective` is still printed, as information only - it is no longer a gate.

Two further guards keep the verdict honest:

  * the snapshot must AGREE with the declarations. If a row of `coverage.json`
    declares a different channel, or carries a `channel_evidence` (or
    `channel_evidence_ok`) that the counters under it do not reproduce, the tool
    is red with the disagreement spelled out - a ledger generated before a
    channel edit must not be silently judged on the old channel.
  * a tool that is a target but is not in the channel table is red, not
    quietly skipped.

The boundary half is decidable only with the session manifest, because a tool
whose contract has no input at all cannot be made to fail: for those the
generator declares an `edge` call (a documented limit input such as an empty
pattern) instead of a `probe` one, and this script accepts either. It reports
which one applied, so the weaker evidence is printed rather than hidden.

It also reports the trace-fact completeness (`facts_complete`) per tool, i.e.
whether the call's reconstructible fields (request id, tool, args, times,
result, capture, scene evidence, file effect) are all present in the trace -
"the call is in the trace" is not the same as "the call is auditable".

Usage:
    python tools/verify_coverage_batch.py --manifest tools/sessions/_exercises/ex_files/c1-manifest.json
    python tools/verify_coverage_batch.py --manifest ... --coverage coverage.json --json OUT
    python tools/verify_coverage_batch.py --manifest ... --channels tools/tool_channels.json

Exit 0 when every target passes, 1 when any fails, 2 on a usage/IO error.
"""
import argparse
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# The ledger's own rule, imported rather than copied: `channel_evidence_count`,
# `load_channels` and `CHANNEL_ORDER` are the single definition of "which
# evidence counts for which tool" (TASK-118 item A / TASK-144 item A).
import tool_coverage as ledger_rule  # noqa: E402


def channel_table(path, names, verbs):
    """The channel declarations, validated by the ledger's own loader.

    `tool_coverage.load_channels()` reads `<root>/tools/tool_channels.json`, so a
    caller-supplied table (the negative tests use one) is staged under a
    throwaway root; the validation - exact contract coverage, closed channel set,
    channel-agrees-with-verb - is the ledger's, never a second copy.
    """
    default = os.path.abspath(os.path.join(ROOT, ledger_rule.CHANNELS_FILE))
    if os.path.abspath(path) == default:
        return ledger_rule.load_channels(ROOT, names, verbs)
    tmp = tempfile.mkdtemp(prefix="mcp144-channels-")
    try:
        staged = os.path.join(tmp, ledger_rule.CHANNELS_FILE)
        os.makedirs(os.path.dirname(staged))
        shutil.copyfile(path, staged)
        return ledger_rule.load_channels(tmp, names, verbs)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def judge(intents, coverage_rows, channels):
    """One verdict per target tool, on the declared channel."""
    results = []
    skipped_setup = []
    for tool in sorted(intents):
        declared = intents[tool]
        if all(x == "setup" for x in declared):
            skipped_setup.append(tool)
            continue
        row = coverage_rows.get(tool) or {}
        calls = row.get("calls", 0)
        boundary = row.get("boundary", 0)
        facts = row.get("facts_complete", 0)
        edge = declared.count("edge")
        probe = declared.count("probe")
        declaration = channels.get(tool) or {}
        channel = declaration.get("channel")

        # The ledger's own counter, fed the ledger row's own per-channel
        # counters. `readback` is the verified witness pointer (editor_state).
        stats = {"pixel_effect": row.get("pixel_effect_calls", 0),
                 "file_effect": row.get("file_effect_calls", 0),
                 "read_payload": row.get("read_payload_calls", 0)}
        channel_evidence = (ledger_rule.channel_evidence_count(stats, channel, row.get("readback"))
                            if channel in ledger_rule.CHANNEL_ORDER else 0)

        # The snapshot must agree with the declarations it was built from.
        drift = []
        if channel is None:
            drift.append("%s is not in the channel table" % tool)
        elif not row:
            drift.append("%s is a target but has no row in the coverage snapshot" % tool)
        else:
            if row.get("evidence_channel") != channel:
                drift.append("coverage.json declares channel %r, the channel table declares %r"
                             % (row.get("evidence_channel"), channel))
            if row.get("channel_evidence") != channel_evidence:
                drift.append("coverage.json stores channel_evidence=%r, its counters reproduce %r"
                             % (row.get("channel_evidence"), channel_evidence))
            if bool(row.get("channel_evidence_ok")) != (channel_evidence >= 1):
                drift.append("coverage.json stores channel_evidence_ok=%r while the reproduced "
                             "evidence is %r" % (row.get("channel_evidence_ok"), channel_evidence))

        checks = {
            "calls>=5": calls >= 5,
            "channel_evidence>=1": channel_evidence >= 1,
            "boundary>=1": boundary >= 1,
            "boundary_declared": probe >= 1,
            "edge_declared": edge >= 1,
            "snapshot_agrees": not drift,
        }
        boundary_ok = checks["boundary>=1"] or checks["edge_declared"]
        verdict = "pass" if (checks["calls>=5"] and checks["channel_evidence>=1"]
                             and boundary_ok and checks["snapshot_agrees"]) else "fail"
        results.append({
            "tool": tool, "calls": calls, "effective": row.get("effective", 0),
            "boundary": boundary, "facts_complete": facts,
            "evidence_channel": channel,
            "channel_evidence": channel_evidence,
            "declared_ok": declared.count("ok"),
            "declared_probe": probe, "declared_edge": edge,
            "boundary_evidence": ("failed_call" if boundary >= 1
                                  else ("declared_edge_input" if edge >= 1 else "NONE")),
            "facts_all": bool(calls and facts == calls),
            "snapshot_drift": drift,
            "checks": checks, "verdict": verdict,
        })
    return results, skipped_setup


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify one coverage batch.")
    parser.add_argument("--manifest", required=True, action="append",
                        help="repeatable: the batch's own manifest, plus any earlier batch's")
    parser.add_argument("--coverage", default=os.path.join(ROOT, "coverage.json"))
    parser.add_argument("--channels",
                        default=os.path.join(ROOT, ledger_rule.CHANNELS_FILE),
                        help="the declared evidence channel of every contract tool "
                             "(default: tools/tool_channels.json)")
    parser.add_argument("--json", default=None)
    args = parser.parse_args(argv)

    for path in args.manifest:
        if not os.path.isfile(path):
            sys.stderr.write("verify_coverage_batch: missing %s\n" % path)
            return 2
    for path in (args.coverage, args.channels):
        if not os.path.isfile(path):
            sys.stderr.write("verify_coverage_batch: missing %s\n" % path)
            return 2

    raw = []
    for path in args.manifest:
        with io.open(path, "r", encoding="utf-8") as h:
            raw.append(json.load(h))
    with io.open(args.coverage, "r", encoding="utf-8") as h:
        coverage = json.load(h)
    rows = {r["tool"]: r for r in coverage["tools"]}

    names = ledger_rule.contract_tools(ROOT)
    _scopes, verbs = ledger_rule.scope_and_verb(ROOT)
    try:
        channels, channel_doc = channel_table(args.channels, names, verbs)
    except SystemExit as exc:
        sys.stderr.write("verify_coverage_batch: channel table rejected by the ledger rule: %s\n"
                         % exc)
        return 2

    intents = {}
    for manifest in raw:
        for call in manifest.get("calls") or []:
            if "tool" not in call:
                continue
            intents.setdefault(call["tool"], []).append(call["intent"])

    results, skipped_setup = judge(intents, rows, channels)
    passed = [r for r in results if r["verdict"] == "pass"]

    print("batch   : %s (%s)" % ("+".join(m.get("batch", "?") for m in raw),
                                 raw[-1].get("project")))
    print("coverage: %s (mode=%s)" % (args.coverage, coverage.get("mode")))
    print("channels: %s (declared_at=%s)" % (args.channels, channel_doc.get("declared_at")))
    print("gate    : calls>=5 and channel_evidence>=1 and (boundary>=1 or declared edge); "
          "evidence judged on the tool's declared channel (TASK-118 A / TASK-144 A)")
    print("targets : %d   pass: %d   fail: %d" % (len(results), len(passed), len(results) - len(passed)))
    print("setup   : %d tool(s) used only to make the targets measurable, not judged: %s"
          % (len(skipped_setup), ", ".join(skipped_setup) or "-"))
    print()
    print("%-42s %5s %5s %12s %12s %5s %6s %-20s %s"
          % ("tool", "calls", "eff", "channel", "ch-evidence", "fail", "facts",
             "boundary evidence", "verdict"))
    for r in results:
        print("%-42s %5d %5d %12s %12d %5d %6s %-20s %s"
              % (r["tool"], r["calls"], r["effective"], r["evidence_channel"] or "-",
                 r["channel_evidence"], r["boundary"],
                 "%d/%d" % (r["facts_complete"], r["calls"]),
                 r["boundary_evidence"], r["verdict"]))
        for complaint in r["snapshot_drift"]:
            print("%-42s   snapshot: %s" % ("", complaint))
    missing_manifest = [r for r in results if r["calls"] == 0]
    if missing_manifest:
        print()
        print("!! tools with ZERO calls in this coverage snapshot: %s"
              % ", ".join(r["tool"] for r in missing_manifest))
    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as h:
            h.write(json.dumps({"batches": [m.get("batch") for m in raw],
                                "project": raw[-1].get("project"),
                                "manifests": args.manifest,
                                "coverage": args.coverage,
                                "mode": coverage.get("mode"),
                                "channels": args.channels,
                                "channels_declared_at": channel_doc.get("declared_at"),
                                "gate": "calls>=5 and channel_evidence>=1 and "
                                        "(boundary>=1 or declared edge); evidence on the "
                                        "declared channel (TASK-118 A / TASK-144 A)",
                                "legacy_quantity": "effective (pixel/file delta only) - reported, "
                                                   "no longer a gate",
                                "targets": len(results), "passed": len(passed),
                                "failed": len(results) - len(passed),
                                "setup_only": skipped_setup,
                                "results": results}, ensure_ascii=False, indent=2) + "\n")
        print("\nwrote %s" % args.json)
    return 0 if len(passed) == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
