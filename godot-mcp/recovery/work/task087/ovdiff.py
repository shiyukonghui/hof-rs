# -*- coding: utf-8 -*-
"""Compare the current contract's override keys with every recorded override key.

The recorded `_meta.overrides` entries surface in:
  * `contract_fingerprint.txt` (task076 evidence) - the pinned final contract
  * recorded read windows / terminal dumps of tools_list.renamed.json
  * the generator source itself (DESCRIPTION_OVERRIDES / SCHEMA_OVERRIDES)

usage: python ovdiff.py
"""
from __future__ import print_function
import io, json, os, re, sys
sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087")
import rep

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
TREE = r"H:\rebuild\godot\modules\mcp_server"


def main():
    p = os.path.join(TREE, "docs", "tools_list.renamed.json")
    o = json.loads(io.open(p, encoding="utf-8-sig").read())
    ov = o["_meta"]["overrides"]
    rep.log("current overrides=%d" % len(ov))
    keys = []
    for e in ov:
        if isinstance(e, dict):
            keys.append(e.get("tool") or e.get("name") or e.get("old_name") or "?")
        else:
            keys.append(str(e))
    rep.log("current keys: %s" % ", ".join(sorted(keys)))

    # generator source: every override key declared there
    src = io.open(os.path.join(TREE, "scripts", "gen_renamed_contract.py"), encoding="utf-8").read()
    rep.log("")
    rep.log("--- generator declared tables ---")
    for tbl in ("DESCRIPTION_OVERRIDES", "SCHEMA_OVERRIDES"):
        m = re.search(r"^%s\s*=\s*\{(.*?)^\}" % tbl, src, re.S | re.M)
        if not m:
            rep.log("  %s: not found" % tbl)
            continue
        names = re.findall(r'^\s{4}"([a-z0-9_]+)"\s*:', m.group(1), re.M)
        rep.log("  %s: %d keys" % (tbl, len(names)))
        rep.log("    %s" % ", ".join(names))

    # recorded fingerprint
    fp = os.path.join(TREE, "docs", "reports", "evidence", "task076", "contract_fingerprint.txt")
    if os.path.exists(fp):
        rep.log("")
        rep.log("--- contract_fingerprint.txt ---")
        rep.log(io.open(fp, encoding="utf-8", errors="replace").read())
    else:
        rep.log("")
        rep.log("contract_fingerprint.txt NOT PRESENT at %s" % fp)
    rep.flush()


if __name__ == "__main__":
    main()
