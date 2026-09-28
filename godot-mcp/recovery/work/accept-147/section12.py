#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-147: independent recomputation of the section 1.2/1.3/1.4 headline numbers."""
import io, json, re

contract = json.load(io.open("godot/modules/mcp_server/docs/tools_list.renamed.json", encoding="utf-8"))
tools = contract["result"]["tools"]
channels = json.load(io.open("tools/tool_channels.json", encoding="utf-8"))["channels"]
cov = {t["tool"]: t for t in json.load(io.open("coverage.json", encoding="utf-8"))["tools"]}

names = [t["name"] for t in tools]
print("contract tools        :", len(names), "unique:", len(set(names)))
print("channels entries      :", len(channels))
print("coverage tools        :", len(cov))
print("contract vs channels  :", len(set(names) ^ set(channels)))
print("contract vs coverage  :", len(set(names) ^ set(cov)))

props_of = {t["name"]: ((t.get("inputSchema") or {}).get("properties") or {}) for t in tools}
req_of = {t["name"]: ((t.get("inputSchema") or {}).get("required") or []) for t in tools}
has_props = [n for n in names if props_of[n]]
empty_props = [n for n in names if not props_of[n]]
both = [n for n in names if req_of[n] and [k for k in props_of[n] if k not in req_of[n]]]
defaults = [n for n in names if any(isinstance(v, dict) and "default" in v for v in props_of[n].values())]
enums = [n for n in names if any(isinstance(v, dict) and "enum" in v for v in props_of[n].values())]
print()
print("declared properties   : %d   (matrix 159)" % len(has_props))
print("  required+optional   : %d   (matrix 70)" % len(both))
print("empty properties      : %d   (matrix 18)" % len(empty_props))
print("declares a default    : %d   (matrix 75)" % len(defaults))
print("declares an enum      : %d   (matrix 4)" % len(enums))
print()
nodflt = [n for n in names if (props_of[n] and not any(isinstance(v, dict) and "default" in v for v in props_of[n].values()))]
print("has properties but no default: %d -> %s" % (len(nodflt), nodflt))

missing = sorted(n for n in names if not cov[n].get("channel_evidence_ok"))
print()
print("channel_evidence_ok=false : %d" % len(missing))
for n in missing:
    print("   %-40s channel=%-14s calls=%d tier=%s" % (n, cov[n]["evidence_channel"], cov[n]["calls"], cov[n]["evidence_tier"]))

status = {}
for n in names:
    status[cov[n]["status"]] = status.get(cov[n]["status"], 0) + 1
print()
print("ledger status counts:", status)
print("ledger corpus       :", json.load(io.open("coverage.json", encoding="utf-8"))["corpus"])
