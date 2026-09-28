#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-147 D9: re-verify a sample of TC-TOOL rows against the real artefacts.

For each sampled tool the matrix row is parsed and re-checked against:
  * the contract  godot/modules/mcp_server/docs/tools_list.renamed.json
  * the channel declaration tools/tool_channels.json
  * the runtime ledger coverage.json
  * the counterexample pointer's trace file:line (code + message text)
"""
import io, json, re, sys

MATRIX = "recovery/TEST-CASES.md"
CONTRACT = "godot/modules/mcp_server/docs/tools_list.renamed.json"
CHANNELS = "tools/tool_channels.json"
COVERAGE = "coverage.json"

contract = json.load(io.open(CONTRACT, encoding="utf-8"))
if isinstance(contract, dict) and "result" in contract:
    contract_tools = contract["result"]["tools"]
elif isinstance(contract, dict) and "tools" in contract:
    contract_tools = contract["tools"]
else:
    contract_tools = contract
cby = {}
for t in contract_tools:
    cby[t.get("name")] = t

channels = json.load(io.open(CHANNELS, encoding="utf-8"))["channels"]
cov = json.load(io.open(COVERAGE, encoding="utf-8"))["tools"]
covy = {t["tool"]: t for t in cov}

SAMPLE = sys.argv[1:] or [
    "project_get_info", "project_get_filesystem_tree", "editor_open_scene",
    "editor_rename_node", "editor_set_node_property", "editor_stop_scene",
    "editor_add_scene_instance", "editor_simulate_mouse_click",
    "project_set_setting", "editor_execute_gdscript",
]

lines = io.open(MATRIX, encoding="utf-8").read().splitlines()
rows = {}
for ln, raw in enumerate(lines, 1):
    m = re.match(r"^\| TC-TOOL-([^ |]+) \|", raw)
    if m:
        rows[m.group(1)] = (ln, raw)

print("TC-TOOL rows found: %d" % len(rows))
problems = []
for name in SAMPLE:
    if name not in rows:
        problems.append("%s: NO MATRIX ROW" % name)
        continue
    ln, raw = rows[name]
    cells = [c.strip() for c in raw.split("|")]
    ptr, inform, outform, counter, status = cells[4], cells[5], cells[6], cells[7], cells[8]
    print("\n=== %s (matrix line %d) ===" % (name, ln))
    print("  status  : %s" % status)

    # ---- 1. contract schema ----
    spec = cby.get(name)
    if spec is None:
        problems.append("%s: not in the contract" % name)
        continue
    props = (spec.get("inputSchema") or {}).get("properties") or {}
    req = (spec.get("inputSchema") or {}).get("required")
    req = req if isinstance(req, list) else []
    opt = [k for k in props if k not in req]
    withdefault = [k for k, v in props.items() if isinstance(v, dict) and "default" in v]
    m_members = re.search(r"合法=(\d+) 成员", inform)
    m_req = re.search(r"req (\d+)", inform)
    m_opt = re.search(r"opt (\d+)", inform)
    mv, mr, mo = (int(x.group(1)) if x else None for x in (m_members, m_req, m_opt))
    ok1 = (mv == len(props)) and (mr == len(req)) and (mo == len(opt))
    print("  schema  : members %s(=%d) req %s(=%d) opt %s(=%d) -> %s"
          % (mv, len(props), mr, len(req), mo, len(opt), "OK" if ok1 else "MISMATCH"))
    if not ok1:
        problems.append("%s: schema counts matrix=%s/%s/%s real=%d/%d/%d"
                        % (name, mv, mr, mo, len(props), len(req), len(opt)))
    if ("必填=%s" % ", ".join(req)) not in inform and req:
        print("     note: matrix 必填 cell does not literally list %s" % req)
    if ("可选=%s" % ", ".join(opt)) not in inform and opt:
        print("     note: matrix 可选 cell does not literally list %s" % opt)
    for k in withdefault:
        if ("%s=" % k) not in inform:
            problems.append("%s: default of %s missing from the matrix 默认 cell" % (name, k))
    print("  defaults declared in schema: %s" % (withdefault or "none"))

    # ---- 2. channel declaration pointer ----
    tget = covy.get(name)
    m = re.search(r"`%s:(\d+)`" % re.escape(CHANNELS), ptr)
    if m:
        idx = int(m.group(1))
        real_ch = channels.get(name, {}).get("channel")
        line_at = lines[idx - 1] if idx - 1 < len(lines) else ""
        print("  channel : pointer %s:%d -> real channel %r" % (CHANNELS, idx, real_ch))
        if ("回读=%s/" % real_ch) not in outform and ("/readback" not in outform):
            pass
        mch = re.search(r"回读=([a-z_]+)(?:/([a-z_]+))?", outform)
        # observed cell format: "<declared channel>/<ledger tier>", with the short
        # spellings pixel/state/file used for pixel_effect/editor_state/file_effect.
        def norm(x):
            return {"state": "editor_state", "file": "file_effect",
                    "pixel": "pixel_effect"}.get(x, x)
        matrix_channel = mch.group(1) if mch else None
        matrix_tier = mch.group(2) if mch else None
        real_tier = (tget or {}).get("evidence_tier")
        okch = (norm(matrix_channel) == real_ch)
        oktier = (norm(matrix_tier) == norm(real_tier))
        print("     matrix 回读 '%s/%s' (declared/tier) vs declared '%s' + ledger tier '%s' -> %s / %s"
              % (matrix_channel, matrix_tier, real_ch, real_tier,
                 "OK" if okch else "MISMATCH", "OK" if oktier else "MISMATCH"))
        if not okch:
            problems.append("%s: matrix declared-channel cell %s != %s"
                            % (name, matrix_channel, real_ch))
        if not oktier:
            problems.append("%s: matrix tier cell %s != ledger tier %s"
                            % (name, matrix_tier, real_tier))
    else:
        print("  channel : no pointer cell matched (row lists no channels entry)")

    # ---- 3. ledger ----
    t = covy.get(name)
    if t:
        m = re.search(r"边界=台账 boundary=(\d+)", inform)
        if m and int(m.group(1)) != t["boundary"]:
            problems.append("%s: matrix boundary=%s but ledger=%d"
                            % (name, m.group(1), t["boundary"]))
            print("  ledger  : boundary MISMATCH matrix %s vs %d" % (m.group(1), t["boundary"]))
        else:
            print("  ledger  : boundary=%s calls=%s channel_evidence_ok=%s tier=%s"
                  % (t["boundary"], t["calls"], t["channel_evidence_ok"], t["evidence_tier"]))
        if t["evidence_channel"] != channels.get(name, {}).get("channel"):
            problems.append("%s: ledger channel %s != declaration %s"
                            % (name, t["evidence_channel"], channels.get(name, {}).get("channel")))
    else:
        problems.append("%s: not in coverage.json" % name)

    # ---- 4. counterexample pointer: trace file:line, code, message ----
    m = re.search(r"`(runs/[^`]+\.jsonl):(\d+)`", counter)
    if m:
        path, lineno = m.group(1), int(m.group(2))
        try:
            tl = io.open(path, encoding="utf-8").read().splitlines()
        except Exception as e:
            problems.append("%s: trace %s unreadable (%s)" % (name, path, e))
            continue
        if lineno > len(tl):
            problems.append("%s: trace %s:%d beyond EOF (%d)" % (name, path, lineno, len(tl)))
            continue
        rec = json.loads(tl[lineno - 1])
        code = rec.get("error_code")
        msg = rec.get("error_message")
        if code is None and isinstance(rec.get("error"), dict):
            code = rec["error"].get("code")
            msg = rec["error"].get("message")
        if code is None:
            code = rec.get("response", {}).get("error", {}).get("code")
            msg = rec.get("response", {}).get("error", {}).get("message")
        mc = re.search(r"code=(-?\d+)", counter)
        expected = int(mc.group(1)) if mc else None
        ok4 = (code == expected)
        print("  trace   : %s:%d -> code=%s message=%r  (matrix expects %s) %s"
              % (path, lineno, code, (msg or "")[:60], expected, "OK" if ok4 else "MISMATCH"))
        if not ok4:
            problems.append("%s: trace code %s != matrix %s" % (name, code, expected))
        if msg and 'msg="' in counter:
            frag = counter.split('msg="', 1)[1]
            # keep the leading ASCII run only (the cell continues with prose)
            frag = re.match(r"[^\u2014\u4e00-\u9fff\u201c\u201d\u3001\u3002\uff08\uff09\u2192\uff1b]*",
                            frag).group(0)
            frag = frag.split("\u2026", 1)[0].split("...", 1)[0]
            frag = frag.rstrip('"').rstrip()
            if frag and frag not in msg:
                problems.append("%s: matrix message fragment %r not in trace message %r"
                                % (name, frag[:40], msg[:80]))
                print("     message fragment MISMATCH: %r" % frag[:60])
            else:
                print("     message fragment present")
    else:
        print("  trace   : no runs/...jsonl:NNN pointer in the counterexample cell")

print("\n==== problems: %d ====" % len(problems))
for p in problems:
    print("  * " + p)
