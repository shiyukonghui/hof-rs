# -*- coding: utf-8 -*-
"""Look for the recorded spelling of the `created` / `deleted` assertions."""
import io
import json
import os

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
needles = ['payload["created"]', 'payload["deleted"]', '["created"] == true', '["deleted"] == true']
seen = {}
with io.open(os.path.join(IDX, "events-read.jsonl"), encoding="utf-8", errors="replace") as f:
    for line in f:
        if "created" not in line and "deleted" not in line:
            continue
        r = json.loads(line)
        if "test_mcp_server" not in (r.get("path") or "").replace("/", "\\").lower():
            continue
        for no, txt in r.get("lines") or []:
            for nd in needles:
                if nd in txt:
                    seen.setdefault(txt.strip(), set()).add(r.get("totalLines"))
for k, v in sorted(seen.items()):
    print("%-70s revs=%s" % (k[:70], sorted(v)[:4]))
