# -*- coding: utf-8 -*-
"""Decompose the byte delta between the current contract and the pinned one."""
from __future__ import print_function
import io, json, sys
sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087")
import rep

P = r"H:\rebuild\godot\modules\mcp_server\docs\tools_list.renamed.json"
PINNED_BYTES = 163520
PINNED_SHA = "a5c59853c1e5a4913d600c663c8e972f058f7144869ec20337ab41b7a7bb17ea"
PINNED_OV = 36


def main():
    b = io.open(P, "rb").read()
    s = b.decode("utf-8")
    o = json.loads(s)
    m = o["_meta"]
    rep.log("current  bytes=%d overrides=%d" % (len(b), len(m["overrides"])))
    rep.log("pinned   bytes=%d overrides=%d" % (PINNED_BYTES, PINNED_OV))
    rep.log("raw byte delta = %d" % (PINNED_BYTES - len(b)))

    # the overrides array as it serialises inside the file
    import re
    txt = json.dumps(m["overrides"], ensure_ascii=False, separators=(",", ":"))
    rep.log("overrides serialised (compact, no indent) = %d bytes" % len(txt.encode("utf-8")))
    n_missing = PINNED_OV - len(m["overrides"])
    avg = sum(len(json.dumps(e, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
              for e in m["overrides"]) / max(1, len(m["overrides"]))
    rep.log("mean override entry = %.0f bytes" % avg)
    rep.log("=> %d missing entries account for roughly %d bytes" % (n_missing, int(avg * n_missing)))
    rep.log("residual after that estimate = %d" % (PINNED_BYTES - len(b) - int(avg * n_missing)))

    # environment-dependent field
    mp = m["map_path"]
    rec = r"F:\RustProjects\godot-mcp-pro\code\godot\modules\mcp_server\docs\tool-rename-map.json"
    rep.log("")
    rep.log("_meta.map_path now  = %s" % mp)
    rep.log("_meta.map_path then = %s (the recorded build root)" % rec)
    rep.log("=> this field alone is environment dependent and differs by %d bytes"
            % (len(rec) - len(mp)))
    rep.log("")
    rep.log("entry kinds present: %s"
            % json.dumps({k: sum(1 for e in m["overrides"] if e.get("kind") == k)
                          for k in sorted(set(e.get("kind") for e in m["overrides"]))}))
    rep.log("names present: %s" % ", ".join(sorted(e["old_name"] for e in m["overrides"])))
    rep.flush()


if __name__ == "__main__":
    main()
