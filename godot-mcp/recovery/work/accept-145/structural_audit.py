#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A2: structural audit of the TC-ENG / TC-PY / TC-CONS / TC-M1 / TC-GATE rows."""
import io, json, os, re, collections
ROOT = r"F:\moonbit-hof-rs\godot-mcp"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "structural_audit.json")
MATRIX = os.path.join(ROOT, "recovery", "TEST-CASES.md")
lines = io.open(MATRIX, "r", encoding="utf-8").read().split("\n")

def rows(prefix):
    out = []
    for i, l in enumerate(lines, 1):
        if l.startswith("| " + prefix):
            c = [x.strip() for x in l.strip().strip("|").split("|")]
            out.append((i, c))
    return out

h_path = os.path.join(ROOT, "godot", "modules", "mcp_server", "tests", "test_mcp_server.h")
h = io.open(h_path, "r", encoding="utf-8", errors="replace").read()
h_lines = h.split("\n")

eng = {"rows": 0, "name_missing": [], "range_bad": [], "line_span_diff": []}
for ln, c in rows("TC-ENG-"):
    eng["rows"] += 1
    cid, tname, ptr = c[0], c[1].strip("`"), c[3]
    m = re.search(r"test_mcp_server\.h:(\d+)-(\d+)", ptr)
    if not m:
        eng["range_bad"].append({"id": cid, "ptr": ptr})
        continue
    a, b = int(m.group(1)), int(m.group(2))
    body = "\n".join(h_lines[a - 1:b])
    # the TEST_CASE( name ) should be at/after a-1 and the name present
    if ("TEST_CASE(" not in body) or (tname not in body):
        eng["name_missing"].append({"id": cid, "name": tname, "range": [a, b]})
    span = b - a + 1
    remain = re.search(r"(\d+) 行", c[8])
    if remain and int(remain.group(1)) != span:
        eng["line_span_diff"].append({"id": cid, "matrix": int(remain.group(1)), "actual": span})
# total TEST_CASEs with [MCPServer]
all_tc = re.findall(r"TEST_CASE\(\s*\"([^\"]+)\"\s*\)", h)
tagged = re.findall(r'TEST_CASE\(\s*"[^"]+"\s*\]\s*"[^"]*"[^)]*\)', h)
eng_tag = re.findall(r'TEST_CASE\(\s*("[^"]*\[MCPServer\][^"]*")\s*\)', h)
eng["test_case_total"] = len(all_tc)
eng["test_case_with_mcpserver_tag"] = len(eng_tag)

# TC-PY
py = {"rows": 0, "missing_symbol": [], "by_file": collections.Counter()}
for ln, c in rows("TC-PY-"):
    py["rows"] += 1
    cid, src, sym = c[0], c[1].strip("`"), c[2].strip("`")
    py["by_file"][src] += 1
    path = os.path.join(ROOT, src)
    if not os.path.exists(path):
        py["missing_symbol"].append({"id": cid, "why": "file missing", "src": src})
        continue
    text = io.open(path, "r", encoding="utf-8", errors="replace").read()
    name = cid.split(":", 1)[1] if ":" in cid else ""
    if name and name not in text:
        py["missing_symbol"].append({"id": cid, "why": "name not in file", "src": src, "name": name[:80]})

# TC-CONS
MOD = os.path.join(ROOT, "godot", "modules", "mcp_server")
cons = {"rows": 0, "missing": []}
for ln, c in rows("TC-CONS-"):
    cons["rows"] += 1
    script = c[1].strip("`")
    cands = [os.path.join(ROOT, script), os.path.join(ROOT, "tools", script),
             os.path.join(MOD, script), os.path.join(MOD, "tools", script)]
    if not any(os.path.exists(p) for p in cands):
        cons["missing"].append({"id": c[0], "script": script})

# TC-M1
m1 = {"rows": 0, "missing": []}
acc = io.open(os.path.join(ROOT, "godot", "modules", "mcp_server", "scripts", "accept_m1.ps1"),
              "r", encoding="utf-8", errors="replace").read()
for ln, c in rows("TC-M1-"):
    m1["rows"] += 1
    case = c[1].strip("`")
    if case not in acc:
        m1["missing"].append({"id": c[0], "case": case})

# TC-GATE: gate names are synthesised by the runner loop; compare the command in
# the evidence cell with the corresponding entry of $commands in run_gates.ps1.
gates = {"rows": 0, "mismatch": []}
rg = io.open(os.path.join(ROOT, "tools", "run_gates.ps1"), "r", encoding="utf-8", errors="replace").read()
cmds = re.findall(r"^\s*'([^']+)',?\s*$", rg, re.M)
listed = [c.strip() for c in re.search(r"\$commands = @\((.*?)\)", rg, re.S).group(1).split("\n")]
cmds = [re.sub(r"^[^']*'|',?\s*$", "", l) for l in listed if "'" in l]
for ln, c in rows("TC-GATE-"):
    gates["rows"] += 1
    g = c[1].strip("`")
    idx = int(g[1:]) - 1
    ev = c[3].replace("\\", "/")
    key = ev.split(" -VersionText")[0].replace("`", "").strip().replace("godot/", "")
    # the runner keeps commands relative to the engine dir
    key_engine = key
    actual = (cmds[idx].replace("\\", "/") if 0 <= idx < len(cmds) else "")
    if key_engine not in actual:
        gates["mismatch"].append({"id": c[0], "gate": g, "matrix": key_engine, "runner": actual})

out = {"TC-ENG": eng, "TC-PY": {k: (dict(v) if isinstance(v, collections.Counter) else v) for k, v in py.items()},
       "TC-CONS": cons, "TC-M1": m1, "TC-GATE": gates}
with io.open(OUT, "w", encoding="utf-8", newline="\n") as h2:
    h2.write(json.dumps(out, ensure_ascii=False, indent=2))
print(json.dumps({k: {kk: (len(vv) if isinstance(vv, list) else vv) for kk, vv in v.items()} for k, v in out.items()}, ensure_ascii=False, indent=2))
print("eng name_missing sample:", json.dumps(eng["name_missing"][:5], ensure_ascii=False))
print("eng range_bad sample:", json.dumps(eng["range_bad"][:5], ensure_ascii=False))
print("py missing sample:", json.dumps(py["missing_symbol"][:8], ensure_ascii=False))
