#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-143 trace extractor: per contract tool, the real observed outputs.

Walks every `runs/**/trace-*.jsonl` under the godot-mcp root and records, per tool:

  * the failing calls   (ok=false) with their real `error_code` / `error_message`
    / `args` / trace path + 1-based line number -- this is the NEGATIVE evidence
    the task asks for, quoted from the run that produced it;
  * the first substantive ok call with its `result_json` top-level keys -- the
    success STRUCTURE;
  * file-effect statuses and pixel-effect flags as recorded by the trace writer.

Writes traces.json next to itself (Python file handle; no shell redirect).
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r"F:\moonbit-hof-rs\godot-mcp"
RUNS = os.path.join(ROOT, "runs")


def iter_traces():
    out = []
    for dirpath, dirnames, filenames in os.walk(RUNS):
        names = [f for f in filenames if f.startswith("trace-") and f.endswith(".jsonl")]
        if names:
            out.append((dirpath, sorted(names)))
    out.sort()
    return out


def substantive(raw):
    if not isinstance(raw, str) or raw.strip() == "":
        return False
    try:
        body = json.loads(raw)
    except ValueError:
        return False
    if isinstance(body, dict):
        return len(body) > 0
    if isinstance(body, list):
        return len(body) > 0
    return True


def main():
    facts = {}
    total_calls = 0
    malformed = 0
    files = 0
    for base, names in iter_traces():
        for name in names:
            path = os.path.join(base, name)
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            files += 1
            with io.open(path, "r", encoding="utf-8", errors="replace") as h:
                for lineno, line in enumerate(h, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        malformed += 1
                        continue
                    tool = rec.get("tool")
                    if not tool:
                        continue
                    # A CALL line carries `ok` and `seq`. Capture / event / sidecar
                    # lines carry `tool` too (e.g. `{"event":"capture","tool":...}`)
                    # but no `ok`, so they must NOT be counted as a failed call.
                    if "ok" not in rec:
                        continue
                    total_calls += 1
                    f = facts.setdefault(tool, {
                        "calls": 0, "ok": 0, "failed": 0,
                        "error_codes": {}, "negatives": [], "soft_failures": [],
                        "success_keys": None,
                        "success_pointer": None, "file_effects": {}, "traces": set(),
                    })
                    f["calls"] += 1
                    f["traces"].add(rel)
                    if rec.get("ok") is True:
                        f["ok"] += 1
                        raw = rec.get("result_json")
                        if f["success_keys"] is None and substantive(raw):
                            try:
                                body = json.loads(raw)
                            except ValueError:
                                body = None
                            if isinstance(body, dict):
                                f["success_keys"] = sorted(body.keys())
                                f["success_pointer"] = "%s:%d" % (rel, lineno)
                            elif isinstance(body, list):
                                f["success_keys"] = ["<array len=%d>" % len(body)]
                                f["success_pointer"] = "%s:%d" % (rel, lineno)
                    else:
                        f["failed"] += 1
                        code = rec.get("error_code")
                        if code is not None and code != 0:
                            f["error_codes"][str(code)] = f["error_codes"].get(str(code), 0) + 1
                            if len(f["negatives"]) < 4:
                                f["negatives"].append({
                                    "code": code,
                                    "message": rec.get("error_message") or "",
                                    "args": rec.get("args") or "",
                                    "args_truncated": rec.get("args_truncated"),
                                    "pointer": "%s:%d" % (rel, lineno),
                                    "seq": rec.get("seq"),
                                })
                        elif len(f["soft_failures"]) < 3:
                            f["soft_failures"].append({
                                "pointer": "%s:%d" % (rel, lineno),
                                "seq": rec.get("seq"),
                                "args": rec.get("args") or "",
                                "verdicts": rec.get("verdicts"),
                                "flags": rec.get("flags"),
                            })
                    fe = rec.get("file_effect_status")
                    if fe:
                        f["file_effects"][fe] = f["file_effects"].get(fe, 0) + 1

    for f in facts.values():
        f["traces"] = sorted(f["traces"])[:8]
    out = {"root": ROOT, "trace_files": files, "calls": total_calls,
           "malformed": malformed, "tools": facts}
    path = os.path.join(HERE, "traces.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as h:
        h.write(json.dumps(out, ensure_ascii=False, indent=1))
    print("wrote %s" % path)
    print("trace files : %d" % files)
    print("calls       : %d" % total_calls)
    print("malformed   : %d" % malformed)
    print("tools seen  : %d" % len(facts))
    with_neg = sum(1 for f in facts.values() if f["negatives"])
    print("tools with a REAL error code on a failing call : %d" % with_neg)
    print("tools with a success structure : %d" % sum(1 for f in facts.values() if f["success_keys"]))
    print("tools with only code-less failures : %d"
          % sum(1 for f in facts.values() if not f["negatives"] and f["soft_failures"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
