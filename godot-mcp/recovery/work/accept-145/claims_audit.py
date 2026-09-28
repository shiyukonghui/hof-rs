#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E/report-claims hash + git audit."""
import hashlib, io, json, os, subprocess, sys
ROOT = r"F:\moonbit-hof-rs\godot-mcp"
REPOROOT = os.path.dirname(ROOT)
HERE = os.path.dirname(os.path.abspath(__file__))
claims = {
 "tools/verify_coverage_batch.py": "D76FB648ACE991655C75B0025C0102EACED134F13750A841CB65F88034B9804D",
 "tools/tests/test_coverage_batch_consistency.py": "F57AC96DA2F0F3937A4E0ED8A36E092B68B506D773089F4E55B560ABA540A6AE",
 "recovery/TEST-CASES.md": "C7A9A7DC83524716FFFBFFBDA50C648C6AD5A42DE94DD308476244F95C62D9F0",
 "tools/tool_channels.json": "72A6616D98AFB614A88726C8B631947521995E05E42E49048242A664A72AAF0B",
 "coverage.json": "48017CD5FC2339AA4EF14D3B20955B93238CF9EEA7DD78EB18ACF7D44E47F7FA",
 "recovery/work/task144/batch-before.json": "90C1D86E66483848B30B9313D63A208C69AF75296132DED5D48B4752A1FA03C7",
 "recovery/work/task144/batch-after.json": "2F4F57A1DAFD95BD3F161B3EB3DCD57779EE2B2B136F8AB716BAD692C08354CD",
 "recovery/work/task144/check_recompute.py": "FE416CE0E29693DE45D029B9614D52D2E1984FD65E865739DE48CF145024C2DC",
 "recovery/work/task144/three_reds.py": "5A32B207BDD74F5FAF149D261B549C10678026FCBDC53927CDDD77951A2DB3BD",
 "recovery/work/task144/three_reds_trace.py": "321FB472D85FD56F5B4F3028E9190EAA085BB9E025D17AF8BA93899A3ADA0DE9",
 "recovery/work/task144/probe_u2.py": "0E0C420453AC334098543602470D2FA1590EA622060364A0AEC75A11E8803953",
 "recovery/work/task144/probe-u2.json": "6EA28D7C30E9A0285F21A72E3FE84D031B1B08FAA8276E7A369B1359BCEF5D75",
 "recovery/work/task144/build-local.log": "3E1005A4C5BE2163E8856F51F1F9AC20A2F574E8958E27D330E16BF8BC788E05",
 "recovery/work/task144/build-mono.log": "1CAA0823C9DA9CEDDCC43E877FB9E0C2AFA1D5DD56F4C3E6D8692E3858653E59",
 "runs/gates/task144/summary.txt": "CFC7790E4716F998EDE16D20E7D96D68BC6B95A8044F31CA157437751D50D673",
 "godot/modules/mcp_server/docs/tools_list.renamed.json": "FD00C75E5174EC923D5A91C0323AFA0804F523B385EAE3D4F78D8C71E1F895DF",
 "godot/modules/mcp_server/tests/test_mcp_server.h": "CEBCDD33F580953D7D9DB3BE44A3D1B97DBC8E586883993A6A450072643A99EB",
}
res = {}
for rel, want in claims.items():
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    got = hashlib.sha256(io.open(p, "rb").read()).hexdigest().upper() if os.path.exists(p) else None
    res[rel] = {"claimed": want, "actual": got, "ok": got == want, "bytes": os.path.getsize(p) if os.path.exists(p) else None}

def git(*a, cwd=ROOT):
    return subprocess.run(["git"] + list(a), cwd=cwd, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT).stdout.decode("utf-8", "replace")

g = {
 "godot-mcp HEAD": git("rev-parse", "HEAD").strip(),
 "godot-mcp log": git("log", "--oneline", "-6").split("\n"),
 "e9d17f9 parents": git("log", "-1", "--format=%H %P", "e9d17f9").strip(),
 "e9d17f9 files": git("show", "--stat", "--format=%h %s", "e9d17f9").split("\n")[:3],
 "e9d17f9 name_count": len([l for l in git("show", "--name-only", "--format=", "e9d17f9").split("\n") if l.strip()]),
 "e9d17f9 filenames": [l for l in git("show", "--name-only", "--format=", "e9d17f9").split("\n") if l.strip()],
 "engine HEAD": git("rev-parse", "HEAD", cwd=os.path.join(ROOT, "godot")).strip(),
 "engine branch": git("rev-parse", "--abbrev-ref", "HEAD", cwd=os.path.join(ROOT, "godot")).strip(),
 "engine remote": git("rev-parse", "origin/feature/mcp-server-module-rebuild", cwd=os.path.join(ROOT, "godot")).strip(),
 "engine status": git("status", "--short", cwd=os.path.join(ROOT, "godot")).split("\n"),
}
out = {"hashes": res, "git": g,
       "hash_failures": [k for k, v in res.items() if not v["ok"]]}
with io.open(os.path.join(HERE, "claims_audit.json"), "w", encoding="utf-8", newline="\n") as h:
    h.write(json.dumps(out, ensure_ascii=False, indent=2))
print("hash failures:", json.dumps(out["hash_failures"], ensure_ascii=False))
print(json.dumps(g, ensure_ascii=False, indent=1)[:2500])
