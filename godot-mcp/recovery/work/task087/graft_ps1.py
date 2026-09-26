# -*- coding: utf-8 -*-
"""Build the accept_m1.ps1 replacement from recorded text only.

Base  : the 1022-line-lineage read-window union (0 [Parser]::ParseFile errors).
Graft : the two cases the later revisions added, each inserted with the exact
        recorded `new` text of the edit that added it, at the recorded anchor.

  case0  events-edit seq=1030 t=1790321324515 - the new block ends with the line
         `    # --- case 1: GET /mcp ---...`, which is the recorded anchor; the
         new case is inserted immediately in front of it.
  case20 events-edit seq=858 t=1790015088330 - the new block ends with the
         recorded anchor `    # ---...\n    # Game side\n    # ---...`; inserted
         in front of it.

Nothing else is touched.  Output is written and then must be parse-checked.
"""
from __future__ import print_function
import io, json, os, sys
sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087")
import rep

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
BASE = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087\ps1_e1022.ps1"


def norm(p):
    return (p or "").replace("/", "\\").lower()


def edit(seq):
    with io.open(os.path.join(IDX, "events-edit.jsonl"), encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            o = json.loads(ln)
            if str(o.get("seq")) == str(seq):
                return o
    raise SystemExit("seq %s not found" % seq)


def main():
    out = sys.argv[1]
    rep.set_report(sys.argv[2]) if len(sys.argv) > 2 else None
    buf = io.open(BASE, encoding="utf-8", errors="replace").read()

    e20 = edit(858)
    new20 = e20.get("new") or ""
    anchor20 = "\n".join([
        "    # ------------------------------------------------------------------",
        "    # Game side",
        "    # ------------------------------------------------------------------",
    ])
    # In this recorded payload the new text ENDS with the anchor lines, so they
    # must be cut off before the block is inserted in front of them.
    saw20 = 0
    if new20.endswith(anchor20):
        new20 = new20[:-len(anchor20)].rstrip("\n") + "\n"
        saw20 = 1
    n20 = buf.count(anchor20)
    rep.log("case20 anchor len=%d trailing-stripped=%d occurrences=%d (expect 1)" % (len(anchor20), saw20, n20))
    if n20 == 1:
        buf = buf.replace(anchor20, new20 + anchor20, 1)
        rep.log("  case20 inserted (%d bytes)" % len(new20.encode("utf-8")))

    e0 = edit(1030)
    new0 = e0.get("new") or ""
    marker = "    # --- case 1: GET /mcp --------------------------------------------------"
    n0 = buf.count(marker)
    rep.log("case0 anchor occurrences=%d (expect 1)" % n0)
    if n0 == 1:
        buf = buf.replace(marker, new0.rstrip("\n") + "\n" + marker, 1)
        rep.log("  case0 inserted (%d bytes)" % len(new0.encode("utf-8")))

    rep.log("result bytes=%d lines=%d" % (len(buf.encode("utf-8")), buf.count("\n") + 1))
    io.open(out, "w", encoding="utf-8", newline="\n").write(buf)
    rep.log("wrote %s" % out)
    rep.flush()


if __name__ == "__main__":
    main()
