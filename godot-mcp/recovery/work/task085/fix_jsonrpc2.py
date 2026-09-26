# -*- coding: utf-8 -*-
"""TASK-085: the two recorded envelope builders for mcp_jsonrpc.cpp.

The tree copy of `mcp_jsonrpc.cpp` is the early revision that has neither
`build_result_raw` nor `build_error_raw`, although `mcp_jsonrpc.h` declares both
and `mcp_server.cpp` calls them.  Both bodies are recorded verbatim in the
rev388 t=1790170254765 window (lines 200-206) and are appended to the tree copy.

`MCPJsonRpc::dispatch` is NOT restored here: the header's five-parameter form
(with `bool p_trace`) postdates every recorded definition of it (the only
recorded one, rev388 line 311, takes four parameters), so restoring it would
mean writing the trace plumbing rather than replaying recorded text.

usage: python fix_jsonrpc2.py [--apply]
"""
import io
import sys

sys.path.insert(0, ".")
import evfetch as E  # noqa: E402

SUB = r"modules\mcp_server\mcp_jsonrpc.cpp"
TREE = r"H:\rebuild\godot\modules\mcp_server\mcp_jsonrpc.cpp"


def main():
    w = None
    for r in E.reads(SUB):
        if r.get("totalLines") == 388 and r.get("time") == 1790170254765:
            w = {no: txt.rstrip("\r") for no, txt in r.get("lines") or []}
    assert w, "rev388 window not found"
    block = [w[n] for n in range(199, 207)]
    assert block[1].strip().startswith("String build_result_raw("), block[1]
    assert block[5].strip().startswith("String build_error_raw("), block[5]
    assert block[0].strip() == "" and block[-1].strip() == "}"

    lines = E.lines_of(TREE)
    ci = [i for i, l in enumerate(lines) if l.strip() == "} // namespace MCPJsonRpc"]
    assert len(ci) == 1, "namespace close: %d" % len(ci)
    lines = lines[:ci[0]] + block + [""] + lines[ci[0]:]
    print("mcp_jsonrpc.cpp: appending the recorded build_result_raw / build_error_raw (%d lines)" % len(block))
    print("new line count: %d" % len(lines))
    if "--apply" not in sys.argv:
        print("(dry run; pass --apply to write)")
        return
    text = "\n".join(lines) + "\n"
    with io.open(TREE, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    assert io.open(TREE, encoding="utf-8", errors="replace").read() == text
    print("wrote %s, read-back OK" % TREE)


if __name__ == "__main__":
    main()
