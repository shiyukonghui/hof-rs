# -*- coding: utf-8 -*-
"""task088 (4): contract vs a live `tools/list` BODY file.

usage: python cmp_live.py <live-body.json> <outfile>
"""
from __future__ import print_function
import io, json, os, sys

REPO = r"H:\rebuild\godot"
DOCS = os.path.join(REPO, "modules", "mcp_server", "docs")


def canon(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True)


def main():
    body_path = sys.argv[1]
    out = sys.argv[2]
    # Set-Content -Encoding UTF8 writes a BOM on PowerShell 5.1.
    live = json.load(io.open(body_path, encoding="utf-8-sig"))
    tools = (live.get("result") or {}).get("tools")
    contract = json.load(io.open(os.path.join(DOCS, "tools_list.renamed.json"), encoding="utf-8"))
    fixed = dict((t["name"], t) for t in contract["result"]["tools"])
    rename = json.load(io.open(os.path.join(DOCS, "tool-rename-map.json"), encoding="utf-8"))
    scope = dict((t["new_name"], t.get("scope")) for t in rename["tools"])
    added = json.load(io.open(os.path.join(DOCS, "tool-groups-added.json"), encoding="utf-8"))
    for g in added["groups"]:
        for t in g["tools"]:
            scope[t] = g.get("scope")

    lines = ["live tools=%d contract tools=%d" % (len(tools), len(fixed)), ""]
    desc_missing = []
    schema_missing = []
    for tool in tools:
        name = tool["name"]
        ref = fixed.get(name)
        if ref is None:
            lines.append("%s: NOT IN CONTRACT" % name)
            continue
        d_live, d_fix = tool.get("description") or "", ref.get("description") or ""
        s_live, s_fix = canon(tool.get("inputSchema")), canon(ref.get("inputSchema"))
        if d_live != d_fix:
            rec = {"name": name, "scope": scope.get(name), "prefix": d_live.startswith(d_fix),
                   "contract": d_fix, "live": d_live, "appended": d_live[len(d_fix):] if d_live.startswith(d_fix) else None}
            desc_missing.append(rec)
        if s_live != s_fix:
            schema_missing.append({"name": name, "scope": scope.get(name),
                                   "contract": ref.get("inputSchema"), "live": tool.get("inputSchema")})

    lines.append("DESCRIPTION mismatches: %d" % len(desc_missing))
    for rec in desc_missing:
        lines.append("")
        lines.append("### %s (scope=%s) append_only_prefix=%s" % (rec["name"], rec["scope"], rec["prefix"]))
        lines.append("--- contract (current) ---")
        lines.append(rec["contract"])
        lines.append("--- appended text the override must carry ---")
        lines.append(repr(rec["appended"]))
        lines.append("--- live (the override value) ---")
        lines.append(rec["live"])

    lines.append("")
    lines.append("INPUTSCHEMA mismatches: %d" % len(schema_missing))
    for rec in schema_missing:
        lines.append("")
        lines.append("### %s (scope=%s)" % (rec["name"], rec["scope"]))
        lines.append("--- contract ---")
        lines.append("  " + canon(rec["contract"]))
        lines.append("--- live ---")
        lines.append("  " + canon(rec["live"]))

    data = "\n".join(lines) + "\n"
    io.open(out, "w", encoding="utf-8", newline="\n").write(data)
    print("description mismatches: %d" % len(desc_missing))
    for r in desc_missing:
        print("  %-40s scope=%-8s prefix=%s appended_bytes=%s" % (r["name"], r["scope"], r["prefix"],
              len((r["appended"] or "").encode("utf-8"))))
    print("inputSchema mismatches: %d" % len(schema_missing))
    for r in schema_missing:
        print("  %-40s scope=%s" % (r["name"], r["scope"]))
    print("wrote %s" % out)


if __name__ == "__main__":
    main()
