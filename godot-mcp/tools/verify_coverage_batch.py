#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_coverage_batch.py -- check one TASK-110 coverage batch against its own gate.

The batch gate (task book item B) is per target tool:

    calls >= 5   and   effective >= 1   and   (failed >= 1 or a declared edge call)

`calls` / `effective` / `failed` come from `coverage.json` (tools/tool_coverage.py).
The boundary half is decidable only with the session manifest, because a tool whose
contract has no input at all cannot be made to fail: for those the generator declares
an `edge` call (a documented limit input such as an empty pattern) instead of a `probe`
one, and this script accepts either. It reports which one applied, so the weaker
evidence is printed rather than hidden.

It also reports the trace-fact completeness (`facts_complete`) per tool, i.e. whether
the call's reconstructible fields (request id, tool, args, times, result, capture,
scene evidence, file effect) are all present in the trace - "the call is in the trace"
is not the same as "the call is auditable".

Usage:
    python tools/verify_coverage_batch.py --manifest tools/sessions/_exercises/ex_files/c1-manifest.json
    python tools/verify_coverage_batch.py --manifest ... --coverage coverage.json --json OUT
Exit 0 when every target passes, 1 when any fails, 2 on a usage/IO error.
"""
import argparse
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify one coverage batch.")
    parser.add_argument("--manifest", required=True, action="append",
                        help="repeatable: the batch's own manifest, plus any earlier batch's")
    parser.add_argument("--coverage", default=os.path.join(ROOT, "coverage.json"))
    parser.add_argument("--json", default=None)
    args = parser.parse_args(argv)

    for path in args.manifest:
        if not os.path.isfile(path):
            sys.stderr.write("verify_coverage_batch: missing %s\n" % path)
            return 2
    if not os.path.isfile(args.coverage):
        sys.stderr.write("verify_coverage_batch: missing %s\n" % args.coverage)
        return 2

    raw = []
    for path in args.manifest:
        with io.open(path, "r", encoding="utf-8") as h:
            raw.append(json.load(h))
    with io.open(args.coverage, "r", encoding="utf-8") as h:
        coverage = json.load(h)
    rows = {r["tool"]: r for r in coverage["tools"]}

    intents = {}
    for manifest in raw:
        for call in manifest.get("calls") or []:
            if "tool" not in call:
                continue
            intents.setdefault(call["tool"], []).append(call["intent"])

    results = []
    skipped_setup = []
    for tool in sorted(intents):
        declared = intents[tool]
        if all(x == "setup" for x in declared):
            skipped_setup.append(tool)
            continue
        row = rows.get(tool)
        calls = row["calls"] if row else 0
        eff = row["effective"] if row else 0
        failed = row["boundary"] if row else 0
        facts = row.get("facts_complete", 0) if row else 0
        edge = declared.count("edge")
        probe = declared.count("probe")
        checks = {
            "calls>=5": calls >= 5,
            "effective>=1": eff >= 1,
            "boundary>=1": failed >= 1,
            "boundary_declared": probe >= 1,
            "edge_declared": edge >= 1,
        }
        boundary_ok = checks["boundary>=1"] or checks["edge_declared"]
        verdict = "pass" if (checks["calls>=5"] and checks["effective>=1"] and boundary_ok) else "fail"
        results.append({
            "tool": tool, "calls": calls, "effective": eff, "failed": failed,
            "facts_complete": facts, "declared_ok": declared.count("ok"),
            "declared_probe": probe, "declared_edge": edge,
            "boundary_evidence": ("failed_call" if failed >= 1
                                  else ("declared_edge_input" if edge >= 1 else "NONE")),
            "facts_all": bool(calls and facts == calls),
            "checks": checks, "verdict": verdict,
        })

    passed = [r for r in results if r["verdict"] == "pass"]
    print("batch   : %s (%s)" % ("+".join(m.get("batch", "?") for m in raw),
                                 raw[-1].get("project")))
    print("coverage: %s (mode=%s)" % (args.coverage, coverage.get("mode")))
    print("targets : %d   pass: %d   fail: %d" % (len(results), len(passed), len(results) - len(passed)))
    print("setup   : %d tool(s) used only to make the targets measurable, not judged: %s"
          % (len(skipped_setup), ", ".join(skipped_setup) or "-"))
    print()
    print("%-42s %5s %5s %5s %6s %-20s %s"
          % ("tool", "calls", "eff", "fail", "facts", "boundary evidence", "verdict"))
    for r in results:
        print("%-42s %5d %5d %5d %6s %-20s %s"
              % (r["tool"], r["calls"], r["effective"], r["failed"],
                 "%d/%d" % (r["facts_complete"], r["calls"]),
                 r["boundary_evidence"], r["verdict"]))
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
                                "coverage": args.coverage, "mode": coverage.get("mode"),
                                "targets": len(results), "passed": len(passed),
                                "setup_only": skipped_setup,
                                "results": results}, ensure_ascii=False, indent=2) + "\n")
        print("\nwrote %s" % args.json)
    return 0 if len(passed) == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
