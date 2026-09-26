# -*- coding: utf-8 -*-
"""TASK-083 step 2 (G13): tools/project_read_files.h lost the `namespace MCPTools {`
opener *and* the 26-line TASK-050 N-2 comment block that follows it.

The loss is recoverable verbatim from the read windows, not guessed:

  tree line 53 == revision-211 line 80 (`//   * a server that has `ext` ...`)
  tree line 54 == revision-211 line 81 (`// --------`)
  tree line 55 == revision-211 line 82 (`enum class MCPValidateScriptMode {`)

so revision-211 lines 53-79 are exactly the dropped span, and lines 53-55 are

  53: <blank>
  54: namespace MCPTools {
  55: <blank>

with 56-79 being the TASK-050 N-2 block.  Those 27 lines are identical in the
revision-186, revision-135 and revision-97 windows, so the text below is the
recorded text, not a reconstruction.

Placement is also structurally right: `register_project_read_files_tools` stays
at global scope, exactly as in tools/editor_node_read.h (namespace closes at 193,
the register declaration follows at 195).
"""
import io
import json
import os
import sys

sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083")
import splice  # noqa: E402

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
P = r"H:\rebuild\godot\modules\mcp_server\tools\project_read_files.h"
SUB = "modules\\mcp_server\\tools\\project_read_files.h"


def window(rev_total, a, b):
    """Lines a..b of the newest window whose totalLines == rev_total."""
    best = None
    with io.open(os.path.join(IDX, "events-read.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if SUB.lower() not in r.get("path", "").replace("/", "\\").lower():
                continue
            if r.get("totalLines") != rev_total:
                continue
            lns = {no: txt for no, txt in (r.get("lines") or [])}
            have = [no for no in range(a, b + 1) if no in lns]
            if len(have) == b - a + 1:
                if best is None or r.get("time", 0) > best[0]:
                    best = (r.get("time", 0), [lns[no] for no in range(a, b + 1)], r.get("f"))
    if best is None:
        raise SystemExit("no single window covers rev%d %d-%d" % (rev_total, a, b))
    return best[1], best[2]


def main():
    write = "--write" in sys.argv
    L = splice.read_plain(P)
    print("before: lines=%d balance=%s" % (len(L), splice.balance(L)))
    assert L[51] == "void register_project_read_files_tools(MCPToolRegistry &r_registry);", repr(L[51])
    assert L[52] == "//   * a server that has `ext`        -> COMPILE: the real `reload()`.", repr(L[52])
    assert "namespace MCPTools {" not in "\n".join(L[:120]), "opener already present"
    span, src = window(186, 56, 81)
    print("recovered lines 56-81 from transcript %s (revisions 97/135/186/211 agree)" % src)
    assert span[-2:] == [L[52], L[53]], "alignment broken: %r / %r" % (span[-2:], L[52:54])
    head = ["", "namespace MCPTools {", ""]
    new = L[:52] + head + span[:-2] + L[52:]
    print("after : lines=%d balance=%s" % (len(new), splice.balance(new)))
    if write:
        with io.open(P, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(new) + "\n")
        print("written")


if __name__ == "__main__":
    main()
