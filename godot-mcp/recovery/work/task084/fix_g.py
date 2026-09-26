# -*- coding: utf-8 -*-
"""TASK-084 fix G: tool_helpers.h, the TASK-063 (d) block.

Two recorded edits on `tool_helpers.h` were never placed by the 2A/2B splice:

  seq=810 (t=1790298746575) replaced the 7-line `build_execute_gdscript_source`
      comment + 3-argument declaration with the recorded 4-argument declaration
      plus `struct GDScriptReloadReport` and the `reload_gdscript_capturing`
      declaration;
  seq=860 (t=1790298785652) appended the `gdscript_reload_failure_text`
      declaration.

Both are replayed here verbatim, in time order, at the first occurrence of their
recorded OLD text (the tree carries a stale duplicate of that same 26-line block
further down, and the reused copy is the one the second edit anchors on).

Without them the header declares neither `GDScriptReloadReport` nor
`reload_gdscript_capturing` nor `gdscript_reload_failure_text`, and the 3-argument
declaration makes `editor_script_write.cpp:142` a "no overload takes 4
arguments" error (C2661) plus 15 cascading C2065/C3861.

usage: python fix_g.py [--write]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rec  # noqa: E402

P = r"H:\rebuild\godot\modules\mcp_server\tools\tool_helpers.h"
SUB = "modules\\mcp_server\\tools\\tool_helpers.h"
WRITE = "--write" in sys.argv
BACKUP = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task084\backup084"


def main():
    edits = {str(r.get("seq")): r for r in rec.load(SUB)[1]}
    e810, e860 = edits["810"], edits["860"]
    with io.open(P, "r", encoding="utf-8", errors="strict") as f:
        text = f.read()
    assert "GDScriptReloadReport" not in text, "already present"
    assert text.count(e810["old"]) == 2, text.count(e810["old"])
    t1 = text.replace(e810["old"], e810["new"], 1)
    assert t1.count("GDScriptReloadReport") == 2
    assert t1.count(e860["old"]) == 1, t1.count(e860["old"])
    t2 = t1.replace(e860["old"], e860["new"], 1)
    assert t2.count("gdscript_reload_failure_text") == 1
    print("applying seq=810 (%d -> %d lines) then seq=860 (%d -> %d lines)" % (
        len(e810["old"].split("\n")), len(e810["new"].split("\n")),
        len(e860["old"].split("\n")), len(e860["new"].split("\n"))))
    print("tool_helpers.h: %d -> %d bytes" % (len(text.encode()), len(t2.encode())))
    if WRITE:
        os.makedirs(BACKUP, exist_ok=True)
        with io.open(os.path.join(BACKUP, SUB.replace("\\", "__")), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        with io.open(P, "w", encoding="utf-8", newline="\n") as f:
            f.write(t2)
        print("written")


if __name__ == "__main__":
    main()
