#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-106: the byte-identity chain of the re-run's script payloads.

For every `project_create_script` / `project_edit_script` call in the run's editor
trace, the sha256 of the payload the call actually carried (inline `content`, or the
sidecar file when the payload was over the 4096-byte arg limit) must equal the
sha256 of the session's own payload file. The project's copy on disk is compared
against the same payload file, so "the session wrote this byte for byte" is a
three-way identity rather than a claim.

    python payload_bytes_t106.py <run-dir> <payload-dir>
"""
import hashlib
import io
import json
import os
import sys


def sha256(data):
    return hashlib.sha256(data).hexdigest().upper()


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def main():
    run = os.path.abspath(sys.argv[1])
    payload_dir = os.path.abspath(sys.argv[2])
    out_path = sys.argv[3] if len(sys.argv) > 3 else None
    lines = []

    def say(text):
        print(text)
        lines.append(text)

    repo = os.path.abspath(os.path.join(os.path.dirname(payload_dir), "..", "..", ".."))
    trace = os.path.join(run, "trace-editor.jsonl")
    checked = 0
    problems = []
    with io.open(trace, encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("event"):
                continue  # `trace_opened` / the matching `capture` line: not a call
            if rec.get("tool") not in ("project_create_script", "project_edit_script"):
                continue
            # A truncated `args` string is not valid JSON (it is cut at the arg
            # limit on purpose), so the sidecar is the source when it exists.
            args = None
            source = "inline"
            if rec.get("args_truncated"):
                side = (rec.get("args_sidecar_detail") or {}).get("path")
                if not side:
                    seq = rec.get("seq")
                    candidate = os.path.join(run, "trace-editor.sidecar", "%04d-args.json" % seq)
                    side = candidate if os.path.isfile(candidate) else None
                if not side:
                    problems.append("seq=%s: truncated without a sidecar" % rec.get("seq"))
                    continue
                args = json.loads(io.open(side, encoding="utf-8-sig").read())
                source = "sidecar"
            else:
                args = json.loads(rec.get("args") or "{}")
            rel = args.get("path", "")
            name = os.path.basename(rel)
            content = args.get("content")
            if content is None:
                problems.append("%s: no content in args or sidecar" % name)
                continue
            payload = read_bytes(os.path.join(payload_dir, name))
            call_sha = sha256(content.encode("utf-8"))
            payload_sha = sha256(payload)
            project_path = os.path.join(repo, "projects", "snake", "src", name)
            project_sha = sha256(read_bytes(project_path)) if os.path.isfile(project_path) else "<absent>"
            ok = (call_sha == payload_sha == project_sha)
            checked += 1
            say("%-18s %-8s call=%s payload=%s project=%s %s" % (
                name, source, call_sha[:16], payload_sha[:16], project_sha[:16],
                "OK" if ok else "MISMATCH"))
            if not ok:
                problems.append("%s: %s" % (name, (call_sha, payload_sha, project_sha)))
    say("checked: %d ; problems: %d" % (checked, len(problems)))
    for p in problems:
        say("  PROBLEM %s" % p)
    say("PAYLOAD_CHAIN %s" % ("OK" if not problems and checked else "FAIL"))
    if out_path:
        with io.open(out_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(lines) + "\n")
    return 0 if not problems and checked else 1


if __name__ == "__main__":
    sys.exit(main())
