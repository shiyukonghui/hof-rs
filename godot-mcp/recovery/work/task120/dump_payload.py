#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump one tool's payloads at given seqs (unescaped envelope), for crafting `expect`.

Usage: python dump_payload.py <trace.jsonl> <tool> <seq,seq,...>
"""
import io
import json
import sys


def main():
    path, tool, seqs = sys.argv[1], sys.argv[2], {int(x) for x in sys.argv[3].split(",")}
    for line in io.open(path, encoding="utf-8"):
        if '"tools/call"' not in line:
            continue
        rec = json.loads(line)
        if rec.get("tool") != tool or rec.get("seq") not in seqs:
            continue
        text = rec.get("result_json") or ""
        try:
            body = json.loads(text)
        except ValueError:
            body = None
        if isinstance(body, dict) and isinstance(body.get("content"), list):
            text = body["content"][0].get("text", text)
        print("seq=%s ok=%s len=%d" % (rec["seq"], rec.get("ok"), len(text)))
        print(text)
        print("-" * 40)


if __name__ == "__main__":
    main()
