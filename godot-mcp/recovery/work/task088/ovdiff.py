# -*- coding: utf-8 -*-
"""task088 (4): identify the missing DESCRIPTION_/SCHEMA_OVERRIDES by comparing
the contract against what the server actually publishes.

Evidence: the live `tools/list` bodies accept_m1.ps1 captured (the case3 editor
body and the case12 game body) live in its stdout log. This extracts them, diffs
each tool against `docs/tools_list.renamed.json`, and reports, per tool:

  * whether the contract text is a PREFIX of the live text (the append-only
    override shape the generator documents), and
  * the appended sentence, which is exactly the override `value`.

usage: python ovdiff.py <accept_log> <outfile>
"""
from __future__ import print_function
import io, json, os, re, sys

REPO = r"H:\rebuild\godot"
CONTRACT = os.path.join(REPO, "modules", "mcp_server", "docs", "tools_list.renamed.json")


def extract_bodies(text):
    """Every `tools/list={...}` JSON object in the log, by brace matching."""
    bodies = []
    for m in re.finditer(r"tools/list=", text):
        start = text.find("{", m.end())
        if start < 0:
            continue
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(text)):
            c = text[i]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
                continue
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    chunk = text[start:i + 1]
                    try:
                        bodies.append(json.loads(chunk))
                    except ValueError:
                        pass
                    break
    return bodies


def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def main():
    log = sys.argv[1]
    out = sys.argv[2]
    text = io.open(log, encoding="utf-8", errors="replace").read()
    contract = json.load(io.open(CONTRACT, encoding="utf-8"))
    contract_tools = dict((t["name"], t) for t in contract["result"]["tools"])

    lines = []
    seen = {}
    bodies = extract_bodies(text)
    lines.append("live tools/list bodies extracted from the log: %d" % len(bodies))
    for body in bodies:
        tools = (body.get("result") or {}).get("tools")
        if not tools:
            continue
        for tool in tools:
            seen[tool["name"]] = tool
    lines.append("distinct live tools observed: %d (contract: %d)" % (len(seen), len(contract_tools)))
    lines.append("")

    by_name = {}
    for name, live in sorted(seen.items()):
        fixed = contract_tools.get(name)
        if fixed is None:
            lines.append("%s: NOT IN CONTRACT" % name)
            continue
        d_live = live.get("description") or ""
        d_fix = fixed.get("description") or ""
        s_live = canon(live.get("inputSchema"))
        s_fix = canon(fixed.get("inputSchema"))
        if d_live == d_fix and s_live == s_fix:
            continue
        entry = {"name": name, "desc_differs": d_live != d_fix, "schema_differs": s_live != s_fix}
        if d_live != d_fix:
            entry["contract_is_prefix"] = d_live.startswith(d_fix)
            entry["appended"] = d_live[len(d_fix):] if d_live.startswith(d_fix) else None
            entry["contract_desc"] = d_fix
            entry["live_desc"] = d_live
        if s_live != s_fix:
            entry["contract_schema"] = fixed.get("inputSchema")
            entry["live_schema"] = live.get("inputSchema")
        by_name[name] = entry

    lines.append("tools where the contract and the live server disagree: %d" % len(by_name))
    lines.append("=" * 100)
    for name, entry in sorted(by_name.items()):
        lines.append("")
        lines.append("### %s" % name)
        lines.append("  description differs : %s" % entry["desc_differs"])
        lines.append("  inputSchema differs : %s" % entry["schema_differs"])
        if entry.get("desc_differs"):
            lines.append("  contract text is a prefix of the live text (append-only shape): %s"
                         % entry.get("contract_is_prefix"))
            if entry.get("appended") is not None:
                lines.append("  --- appended sentence (the override value) ---")
                lines.append(entry["appended"])
        if entry.get("schema_differs"):
            lines.append("  --- contract inputSchema ---")
            lines.append("  " + canon(entry["contract_schema"]))
            lines.append("  --- live inputSchema ---")
            lines.append("  " + canon(entry["live_schema"]))
    data = "\n".join(lines) + "\n"
    io.open(out, "w", encoding="utf-8", newline="\n").write(data)
    print("wrote %s (%d bytes)" % (out, len(data.encode("utf-8"))))
    print("tools disagreeing: %d" % len(by_name))
    for name in sorted(by_name):
        e = by_name[name]
        print("  %-45s desc=%-5s schema=%-5s prefix=%s" % (
            name, e["desc_differs"], e["schema_differs"], e.get("contract_is_prefix", "-")))


if __name__ == "__main__":
    main()
