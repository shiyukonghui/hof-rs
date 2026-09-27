#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""analyze_calls.py -- per-call intent vs. outcome for one recorded session run.

The session manifest says what each call was *meant* to be (intent=ok means "this
should succeed and change something", probe means "this should be refused"). The
run directory holds one `<tag>.json` per call - the verbatim MCP response. This
script joins the two and prints the mismatches, which is the only honest way to
find the calls that failed for a reason the session did not intend, or the probes
that were silently accepted.

Usage:
    python recovery/work/task111/analyze_calls.py <run-dir> <manifest.json> [--only-mismatch]
"""
import argparse
import io
import json
import os
import re
import sys


def load(path):
    with io.open(path, "r", encoding="utf-8") as h:
        return json.load(h)


def error_code(text):
    m = re.search(r'"code":(-?\d+)', text)
    return int(m.group(1)) if m else None


def error_message(text):
    try:
        doc = json.loads(text)
    except ValueError:
        return ""
    err = doc.get("error")
    if isinstance(err, dict):
        return str(err.get("message", ""))[:120]
    return ""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("manifest")
    ap.add_argument("--only-mismatch", action="store_true")
    args = ap.parse_args(argv)

    manifest = load(args.manifest)
    intents = {c["tag"]: c for c in manifest.get("calls") or [] if c.get("tag")}

    rows = []
    for tag in sorted(intents):
        path = os.path.join(args.run_dir, tag + ".json")
        if not os.path.isfile(path):
            rows.append((tag, intents[tag], None, "NO_RESPONSE"))
            continue
        with io.open(path, "r", encoding="utf-8") as h:
            text = h.read()
        code = error_code(text)
        rows.append((tag, intents[tag], code, error_message(text)))

    mismatch = []
    for tag, call, code, msg in rows:
        intent = call.get("intent")
        if intent == "setup":
            continue
        ok = code is None
        # `probe` / `edge` are meant to be refused.
        wanted_ok = intent == "ok"
        if ok != wanted_ok:
            mismatch.append((tag, call, code, msg))

    print("run      : %s" % args.run_dir)
    print("manifest : %s (%s)" % (args.manifest, manifest.get("batch")))
    print("calls    : %d   mismatches: %d" % (len(rows), len(mismatch)))
    print()
    print("%-46s %-6s %-6s %s" % ("tag", "intent", "code", "message"))
    for tag, call, code, msg in mismatch:
        print("%-46s %-6s %-6s %s" % (tag, call.get("intent"), code if code is not None else "ok", msg))
    if not args.only_mismatch:
        print()
        print("--- all calls ---")
        for tag, call, code, msg in rows:
            print("%-46s %-6s %-6s %s" % (tag, call.get("intent"), code if code is not None else "ok", msg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
