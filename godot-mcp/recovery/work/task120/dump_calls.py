#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump every call of one tool in a run: seq, args, ok, and the result (short).

Usage: python dump_calls.py <trace.jsonl> <tool> [<tool> ...]
"""
import io
import json
import sys


def main():
    path = sys.argv[1]
    wanted = set(sys.argv[2:])
    for line in io.open(path, encoding="utf-8"):
        if '"tools/call"' not in line:
            continue
        rec = json.loads(line)
        if rec.get("tool") not in wanted:
            continue
        text = rec.get("result_json") or ""
        try:
            body = json.loads(text)
            if isinstance(body, dict) and isinstance(body.get("content"), list):
                text = body["content"][0].get("text", text)
        except ValueError:
            pass
        print("seq=%s %s ok=%s args=%s" % (rec["seq"], rec["tool"], rec.get("ok"),
                                           (rec.get("args") or "")[:300]))
        print("   -> %s" % (text[:400].replace("\n", " ")))
        print("-" * 30)


if __name__ == "__main__":
    main()
