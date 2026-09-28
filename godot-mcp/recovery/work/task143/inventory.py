#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-143 inventory: collect every test-case source of the MCP tool into one JSON.

Read-only over the repository; writes only `inventory.json` next to itself (via a
Python file handle, never a shell redirect).

Sources collected
  A contract   godot/modules/mcp_server/docs/tools_list.renamed.json  (177 tools)
  A channel    tools/tool_channels.json                               (177 channels)
  A ledger     coverage.json + tools/tool_coverage.py + unreachable json
  B gates      tools/run_gates.ps1  (g01..g10 command definitions)
  B accept     godot/modules/mcp_server/scripts/accept_m1.ps1 (case ids)
  C engine     godot/modules/mcp_server/tests/test_mcp_server.h (TEST_CASE bodies)
  D pytest     tools/tests/*.py
  E scripts    consistency / regression scripts
"""
import io
import json
import os
import re
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
ENGINE = os.path.join(ROOT, "godot")
MODULE = os.path.join(ENGINE, "modules", "mcp_server")
HERE = os.path.dirname(os.path.abspath(__file__))

CONTRACT = os.path.join(MODULE, "docs", "tools_list.renamed.json")
RENAME_MAP = os.path.join(MODULE, "docs", "tool-rename-map.json")
GROUPS_ADDED = os.path.join(MODULE, "docs", "tool-groups-added.json")
CHANNELS = os.path.join(ROOT, "tools", "tool_channels.json")
COVERAGE = os.path.join(ROOT, "coverage.json")
UNREACHABLE = os.path.join(ROOT, "tools", "tool_coverage_unreachable.json")
ENGINE_TESTS = os.path.join(MODULE, "tests", "test_mcp_server.h")
RUN_GATES = os.path.join(ROOT, "tools", "run_gates.ps1")
ACCEPT_M1 = os.path.join(MODULE, "scripts", "accept_m1.ps1")
TESTS_DIR = os.path.join(ROOT, "tools", "tests")


def read_text(path):
    with io.open(path, "r", encoding="utf-8", errors="replace") as h:
        return h.read()


def lines_of(path):
    return read_text(path).split("\n")


def find_line(lines, needle, start=0):
    for i in range(start, len(lines)):
        if needle in lines[i]:
            return i + 1
    return None


def sha256(path):
    import hashlib
    d = hashlib.sha256()
    with open(path, "rb") as h:
        for chunk in iter(lambda: h.read(1 << 20), b""):
            d.update(chunk)
    return d.hexdigest().upper()


# ---------------------------------------------------------------------------
# A. contract + channel + ledger
# ---------------------------------------------------------------------------
def collect_contract():
    doc = json.load(io.open(CONTRACT, "r", encoding="utf-8"))
    raw = read_text(CONTRACT).split("\n")
    tools = []
    cursor = 0
    for t in doc["result"]["tools"]:
        needle = '"name": "%s"' % t["name"]
        ln = None
        for i in range(cursor, len(raw)):
            if raw[i].strip() == needle:
                ln = i + 1
                cursor = i
                break
        schema = t.get("inputSchema") or {}
        props = schema.get("properties") or {}
        required = list(schema.get("required") or [])
        optional = [k for k in props if k not in required]
        defaults = {k: v.get("default") for k, v in props.items() if isinstance(v, dict) and "default" in v}
        enums = {k: v.get("enum") for k, v in props.items() if isinstance(v, dict) and "enum" in v}
        types = {k: (v.get("type") if isinstance(v, dict) else None) for k, v in props.items()}
        tools.append({
            "name": t["name"],
            "description": t.get("description", ""),
            "contract_line": ln,
            "properties": sorted(props.keys()),
            "required": required,
            "optional": optional,
            "types": types,
            "defaults": defaults,
            "enums": enums,
            "additional_properties": schema.get("additionalProperties", None),
        })
    return {
        "path": os.path.relpath(CONTRACT, ROOT).replace("\\", "/"),
        "sha256": sha256(CONTRACT),
        "count": len(tools),
        "meta": {k: doc["_meta"].get(k) for k in ("count", "added_count", "generated_from", "generator_version")},
        "overrides": doc["_meta"].get("overrides") or [],
        "tools": tools,
    }


def collect_channels():
    doc = json.load(io.open(CHANNELS, "r", encoding="utf-8"))
    raw = read_text(CHANNELS).split("\n")
    out = {}
    cursor = 0
    for name, rec in (doc.get("channels") or {}).items():
        needle = '"%s": {' % name
        ln = None
        for i in range(cursor, len(raw)):
            if raw[i].strip() == needle:
                ln = i + 1
                cursor = i
                break
        out[name] = {"channel": rec.get("channel"), "subject": rec.get("subject"),
                     "basis": rec.get("basis"), "line": ln}
    return {"path": os.path.relpath(CHANNELS, ROOT).replace("\\", "/"), "sha256": sha256(CHANNELS),
            "total": doc.get("total"), "declared_at": doc.get("declared_at"), "channels": out}


def collect_coverage():
    doc = json.load(io.open(COVERAGE, "r", encoding="utf-8"))
    rows = {r["tool"]: r for r in doc["tools"]}
    return {
        "path": os.path.relpath(COVERAGE, ROOT).replace("\\", "/"),
        "sha256": sha256(COVERAGE),
        "mode": doc.get("mode"),
        "corpus": doc.get("corpus"),
        "buckets": doc.get("buckets"),
        "status_counts": doc.get("status_counts"),
        "evidence_tier_counts": doc.get("evidence_tier_counts"),
        "evidence_channel_counts": doc.get("evidence_channel_counts"),
        "scope_counts": doc.get("scope_counts"),
        "unreachable_registry": doc.get("unreachable_registry"),
        "readback_declarations": len(doc.get("readback_declarations") or []),
        "rows": rows,
    }


def collect_rename_map():
    doc = json.load(io.open(RENAME_MAP, "r", encoding="utf-8"))
    raw = read_text(RENAME_MAP).split("\n")
    out = {}
    for e in doc["tools"]:
        nn = e.get("new_name")
        if not nn:
            continue
        needle = '"new_name": "%s"' % nn
        ln = find_line(raw, needle)
        prev = out.setdefault(nn, {})
        prev.update({"scope": e.get("scope"), "verb": e.get("verb"),
                     "old_name": e.get("old_name"), "mutating": e.get("mutating"),
                     "line": ln})
    return {"path": os.path.relpath(RENAME_MAP, ROOT).replace("\\", "/"), "sha256": sha256(RENAME_MAP),
            "entries": len(doc["tools"]), "map": out}


# ---------------------------------------------------------------------------
# B. gates
# ---------------------------------------------------------------------------
def collect_gates():
    raw = read_text(RUN_GATES)
    m = re.search(r"\$commands = @\((.*?)\n\)", raw, re.S)
    cmds = re.findall(r"^\s*(?:'|\()?(.+?)(?:'|\))?,?\s*$", m.group(1), re.M) if m else []
    # the array is written as quoted strings (optionally with a leading literal)
    cmds = []
    for line in m.group(1).split("\n"):
        s = line.strip().rstrip(",")
        if not s:
            continue
        if s.startswith("'"):
            s = s[1:]
            if s.endswith("'"):
                s = s[:-1]
        else:
            # `('powershell ... ' + $resolvedVersionText)` form
            s = s.lstrip("(").strip()
            if s.startswith("'"):
                s = s[1:]
            if "'" in s:
                s = s.split("'")[0]
        cmds.append(s)
    lines = raw.split("\n")
    gates = []
    for i, cmd in enumerate(cmds, start=1):
        gates.append({"id": "g%02d" % i, "cmd": cmd, "declared_line": find_line(lines, cmd[:40])})
    return {"path": os.path.relpath(RUN_GATES, ROOT).replace("\\", "/"), "sha256": sha256(RUN_GATES),
            "gates": gates}


def collect_accept_m1():
    raw = read_text(ACCEPT_M1)
    lines = raw.split("\n")
    cases = []
    for i, line in enumerate(lines):
        m = re.match(r"\s*Invoke-Case '([^']+)'", line)
        if m:
            cases.append({"id": m.group(1), "line": i + 1})
        m2 = re.match(r"\s*Record-Result '([^']+)'", line)
        if m2:
            cases.append({"id": m2.group(1), "line": i + 1, "kind": "guard"})
    return {"path": os.path.relpath(ACCEPT_M1, ROOT).replace("\\", "/"), "sha256": sha256(ACCEPT_M1),
            "cases": cases}


# ---------------------------------------------------------------------------
# C. engine test cases
# ---------------------------------------------------------------------------
CASE_RE = re.compile(r'^TEST_CASE\("\[MCPServer\] (.*)"\) \{')


def collect_engine_cases():
    lines = lines_of(ENGINE_TESTS)
    starts = []
    for i, line in enumerate(lines):
        m = CASE_RE.match(line)
        if m:
            starts.append((i, m.group(1)))
    cases = []
    for idx, (i, name) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
        body = "\n".join(lines[i:end])
        cases.append({"n": idx + 1, "name": name, "line": i + 1, "end_line": end,
                      "body_lines": end - i, "body": body})
    return {"path": os.path.relpath(ENGINE_TESTS, ROOT).replace("\\", "/"),
            "sha256": sha256(ENGINE_TESTS),
            "count": len(cases), "cases": cases}


# ---------------------------------------------------------------------------
# D. tools/tests/**
# ---------------------------------------------------------------------------
def collect_pytests():
    out = []
    for fname in sorted(os.listdir(TESTS_DIR)):
        if not fname.endswith(".py"):
            continue
        path = os.path.join(TESTS_DIR, fname)
        raw = read_text(path)
        lines = raw.split("\n")
        entries = []
        seen = set()
        for i, line in enumerate(lines):
            m = re.match(r"def (test_[A-Za-z0-9_]+)\(", line)
            if m:
                key = ("pytest", m.group(1), i + 1)
                if key not in seen:
                    seen.add(key)
                    entries.append({"kind": "pytest", "id": m.group(1), "line": i + 1})
        # script-style check labels, two spellings in this repo:
        #   jev:      results["checks"]["D1_health_ok"] = ...
        #   playjev:  checks["dumb_server_validates_clean"] = ...
        for i, line in enumerate(lines):
            for m in re.finditer(r'checks(?:"\])?\["([^"]+)"\]', line):
                key = ("script_check", m.group(1), i + 1)
                if key not in seen:
                    seen.add(key)
                    entries.append({"kind": "script_check", "id": m.group(1), "line": i + 1})
        # p7 records its cases as case("human readable name", ...)
        for i, line in enumerate(lines):
            for m in re.finditer(r'\bcase\(\s*"([^"]{8,})"', line):
                key = ("case", m.group(1), i + 1)
                if key not in seen:
                    seen.add(key)
                    entries.append({"kind": "case", "id": m.group(1), "line": i + 1})
        # Two files print their own complete case list; for those the PRINTED list
        # is the authoritative enumeration (every inline tuple included), so it is
        # taken by really running the file (no network, no writes).
        if fname in PRINTED_CASE_FILES:
            printed = printed_case_names(path)
            for name in printed:
                key = ("printed", name, 0)
                if key not in seen:
                    seen.add(key)
                    entries.append({"kind": "printed_case", "id": name, "line": 0})
            # the printed list is authoritative for these two files; the
            # source-derived partial list would only add duplicates
            entries = [e for e in entries if e["kind"] != "case"]
        out.append({"file": os.path.relpath(path, ROOT).replace("\\", "/"),
                    "sha256": sha256(path), "lines": len(lines), "entries": entries,
                    "unique_checks": len({e["id"] for e in entries})})
    return out


PRINTED_CASE_FILES = ("test_playability_p7.py", "test_playability_model_player.py")


def printed_case_names(path):
    """Run a no-network / no-write script and take the case names it prints."""
    import subprocess
    try:
        proc = subprocess.run([sys.executable, path], cwd=ROOT,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except OSError:
        return []
    text = proc.stdout.decode("utf-8", "replace")
    names = []
    for line in text.split("\n"):
        s = line.rstrip()
        m = re.match(r"^ok\s{2}(.+)$", s)          # p7: "ok  <name>"
        if m:
            names.append(m.group(1).strip())
            continue
        m = re.match(r"^(.*?)\s+OK$", s)           # model_player: "<name>   OK"
        if m and len(m.group(1).strip()) > 8:
            names.append(m.group(1).strip())
    return names


# ---------------------------------------------------------------------------
# E. consistency / regression scripts
# ---------------------------------------------------------------------------
def collect_scripts():
    names = [
        (MODULE, "docs/scripts/check_tool_groups.py"),
        (MODULE, "docs/scripts/check_rename_map.py"),
        (MODULE, "scripts/check_tautologies.py"),
        (MODULE, "scripts/check_exit_propagation.py"),
        (MODULE, "scripts/check_hardcoded_counts.py"),
        (MODULE, "scripts/check_engine_anchor.ps1"),
        (MODULE, "scripts/check_contract_subset.ps1"),
        (ROOT, "tools/tool_coverage.py"),
        (ROOT, "tools/verify_coverage_batch.py"),
        (ROOT, "tools/gen_coverage_session.py"),
        (ROOT, "tools/playability_gate.py"),
        (ROOT, "tools/playability_rescore.py"),
        (ROOT, "tools/playability_report.py"),
    ]
    out = []
    for base, rel in names:
        path = os.path.join(base, rel)
        if not os.path.isfile(path):
            out.append({"path": rel, "missing": True})
            continue
        out.append({"path": rel, "missing": False, "sha256": sha256(path),
                    "lines": len(lines_of(path))})
    return out


def main():
    inv = {
        "root": ROOT,
        "contract": collect_contract(),
        "channels": collect_channels(),
        "coverage": collect_coverage(),
        "rename_map": collect_rename_map(),
        "gates": collect_gates(),
        "accept_m1": collect_accept_m1(),
        "engine": collect_engine_cases(),
        "pytests": collect_pytests(),
        "scripts": collect_scripts(),
    }
    out = os.path.join(HERE, "inventory.json")
    with io.open(out, "w", encoding="utf-8", newline="\n") as h:
        h.write(json.dumps(inv, ensure_ascii=False, indent=1))
    print("wrote %s" % out)
    print("contract tools  : %d" % inv["contract"]["count"])
    print("channels        : %d" % len(inv["channels"]["channels"]))
    print("coverage rows   : %d" % len(inv["coverage"]["rows"]))
    print("rename entries  : %d" % inv["rename_map"]["entries"])
    print("gates           : %d" % len(inv["gates"]["gates"]))
    print("accept_m1 cases : %d" % len(inv["accept_m1"]["cases"]))
    print("engine cases    : %d" % inv["engine"]["count"])
    print("pytest files    : %d  (entries %d)" % (len(inv["pytests"]),
                                                  sum(len(p["entries"]) for p in inv["pytests"])))
    print("scripts         : %d" % len(inv["scripts"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
