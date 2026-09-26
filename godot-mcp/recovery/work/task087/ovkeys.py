# -*- coding: utf-8 -*-
"""Harvest override key names of tools_list.renamed.json from recorded dumps.

Every recorded output that mentions `overrides` is scanned for tool-name-shaped
tokens in the neighbourhood, so the set of override keys the terminal revision
carried can be compared with what the reconstructed generator declares.

usage: python ovkeys.py [--report F]
"""
from __future__ import print_function
import io, json, os, re, sys, collections
sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087")
import rep

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
FILES = ["events-termdump.jsonl", "gen-runs.jsonl", "events-diff.jsonl",
         "events-termfile.jsonl", "events-termlog.jsonl"]
NAME = re.compile(r"(?:editor|running_game|project|os)_[a-z0-9_]+")

names = collections.Counter()
where = {}
sources = collections.Counter()
for fn in FILES:
    p = os.path.join(IDX, fn)
    if not os.path.exists(p):
        continue
    with io.open(p, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            out = o.get("out") or ""
            if "overrides" not in out:
                continue
            sources[fn] += 1
            i = out.find("overrides")
            seg = out[max(0, i - 400):i + 6000]
            for m in NAME.finditer(seg):
                n = m.group(0)
                names[n] += 1
                where.setdefault(n, (fn, o.get("seq"), o.get("time")))

rep.log("sources mentioning overrides: %s" % dict(sources))
rep.log("distinct tool-name tokens near an overrides mention: %d" % len(names))
for n, c in names.most_common(200):
    rep.log("  %-52s %5d  %s" % (n, c, where[n]))
rep.flush()
