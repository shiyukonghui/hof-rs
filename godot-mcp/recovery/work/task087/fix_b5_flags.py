# -*- coding: utf-8 -*-
"""Report which not-implemented groups declare the 14 undeclared contract tools,
then (with --apply) set `implemented: true` on exactly those groups.

Conservative: only a group that declares at least one of the 14 names is touched,
and the file is rewritten with the same 2-space indent + trailing newline the
existing manifest uses.  A backup of the original bytes is written next to the
work dir first.
"""
from __future__ import print_function
import io, json, os, sys, shutil
sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087")
import rep

ROOT = r"H:\rebuild\godot\modules\mcp_server"
DOCS = os.path.join(ROOT, "docs")
B5 = os.path.join(DOCS, "tool-groups-b5.json")
BACKUP = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087\tool-groups-b5.json.orig"


def main():
    apply = "--apply" in sys.argv
    if "--report" in sys.argv:
        rep.set_report(sys.argv[sys.argv.index("--report") + 1])
    mapping = json.loads(io.open(os.path.join(DOCS, "tool-rename-map.json"),
                                 encoding="utf-8-sig").read())
    old2new = {e["old_name"]: e["new_name"] for e in mapping["tools"]}
    contract = json.loads(io.open(os.path.join(DOCS, "tools_list.renamed.json"),
                                  encoding="utf-8-sig").read())
    new_names = set(t["name"] for t in contract["result"]["tools"])
    # names not declared by any *implemented* group of the other five manifests
    declared = set()
    for mf in ("tool-groups.json", "tool-groups-b2.json", "tool-groups-b3.json",
               "tool-groups-b4.json", "tool-groups-added.json"):
        j = json.loads(io.open(os.path.join(DOCS, mf), encoding="utf-8-sig").read())
        for g in j.get("groups") or []:
            if g.get("implemented"):
                for t in g.get("tools") or []:
                    declared.add(old2new.get(t, t))
    missing = sorted(n for n in new_names if n not in declared)

    j = json.loads(io.open(B5, encoding="utf-8-sig").read())
    hits = []
    for g in j["groups"]:
        names = [old2new.get(t, t) for t in (g.get("tools") or [])]
        inter = sorted(set(names) & set(missing))
        if inter and not g.get("implemented"):
            hits.append((g, inter))
    rep.log("groups to flip: %d" % len(hits))
    for g, inter in hits:
        rep.log("  %-42s tools=%d  covers=%s" % (g.get("name"), len(g.get("tools") or []), inter))
    if apply:
        shutil.copyfile(B5, BACKUP)
        for g, _ in hits:
            g["implemented"] = True
        txt = json.dumps(j, ensure_ascii=False, indent=2) + "\n"
        with io.open(B5, "w", encoding="utf-8", newline="\n") as f:
            f.write(txt)
        rep.log("applied; backup at %s" % BACKUP)
        rep.log("bytes now = %d" % len(txt.encode("utf-8")))
    rep.flush()


if __name__ == "__main__":
    main()
