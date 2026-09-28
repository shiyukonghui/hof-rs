#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the model-player script and count its printed cases; verify the 15
'%d rounds ...' rows exist at runtime."""
import io, json, os, re, subprocess, sys
ROOT = r"F:\moonbit-hof-rs\godot-mcp"
HERE = os.path.dirname(os.path.abspath(__file__))
script = os.path.join(ROOT, "tools", "tests", "test_playability_model_player.py")
p = subprocess.run([sys.executable, script], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
out = p.stdout.decode("utf-8", "replace")
with io.open(os.path.join(HERE, "model_player_run.txt"), "w", encoding="utf-8", newline="\n") as h:
    h.write("EXIT=%d\n" % p.returncode)
    h.write(out)
lines = out.split("\n")
# printed case lines look like "ok  <name>" or "FAIL <name>"? inspect head
head = lines[:15]
ok = sum(1 for l in lines if re.match(r"^\s*ok\b", l, re.I))
fail = sum(1 for l in lines if re.match(r"^\s*FAIL\b", l, re.I))
names = re.findall(r"^\s*(?:ok|FAIL)\s+(.*)$", out, re.M)
wanted = ["stability: 1 rounds is ROUNDS_INSUFFICIENT", "stability: 3 rounds reports how many it got"]
res = {"exit": p.returncode, "ok_lines": ok, "fail_lines": fail, "printed_names": len(names),
       "head": head, "wanted_present": {w: any(w in n for n in names) for w in wanted},
       "tail": lines[-12:]}
with io.open(os.path.join(HERE, "model_player_counts.json"), "w", encoding="utf-8", newline="\n") as h:
    h.write(json.dumps(res, ensure_ascii=False, indent=2))
print(json.dumps(res, ensure_ascii=False, indent=2)[:2500])
