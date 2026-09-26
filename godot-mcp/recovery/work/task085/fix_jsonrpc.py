# -*- coding: utf-8 -*-
"""TASK-085 mcp_jsonrpc.cpp assembly.

`mcp_jsonrpc.cpp` in the tree is an early revision: it has only
`_handle_tools_call` + a `handle` that inlines dispatch, and none of
`build_result_raw`, `build_error_raw`, `_immediate`, `_tag`,
`_effective_timeout`, `_dispatch_tools_call`, `dispatch`.  The header declares
the later API, so the link fails on `build_result_raw`, `build_error_raw` and
`dispatch`.

Base: the merged reconstruction `fl_jsonrpc.cpp` (rev453 read windows laid on
the tree, fill.py).  Added from recorded text:
  * `_immediate`  - rev388 t=1790142024951 lines 224-230
  * `handle`      - rev388 lines 373-386 (target shape: refuse a deferred tool)
  * `dispatch`    - rev388 lines 311-371 with the header's `p_trace` parameter
                    wired through `_tag` / `_dispatch_tools_call`; the trace
                    plumbing is the only non-recorded part and is marked.

usage: python fix_jsonrpc.py [--apply]
"""
import io
import sys

sys.path.insert(0, ".")
import evfetch as E  # noqa: E402

SUB = r"modules\mcp_server\mcp_jsonrpc.cpp"
TREE = r"H:\rebuild\godot\modules\mcp_server\mcp_jsonrpc.cpp"
SRC = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task085\fl_jsonrpc.cpp"
MARK = "\t// [REBUILT-2C low-confidence: verify]"


def window(rev, t):
    for r in E.reads(SUB):
        if r.get("totalLines") == rev and r.get("time") == t:
            return {no: txt.rstrip("\r") for no, txt in r.get("lines") or []}
    raise SystemExit("window rev%s t=%s not found" % (rev, t))


def main():
    w = window(388, 1790142024951)
    immediate = [w[n] for n in range(224, 231)]
    handle = [w[n] for n in range(372, 387)]      # blank + recorded handle + close
    body = [w[n] for n in range(311, 372)]        # the recorded 4-arg dispatch
    assert immediate[0].strip().startswith("static Dispatch _immediate("), immediate[0]
    assert handle[1].strip().startswith("Response handle("), handle[1]
    assert body[0].strip().startswith("Dispatch dispatch("), body[0]
    assert body[-1] == "}", repr(body[-1])

    # 1. retarget the recorded dispatch onto the header's signature and trace.
    body[0] = "Dispatch dispatch(const String &p_payload, const MCPToolRegistry &p_registry, bool p_is_editor, uint64_t p_default_timeout_ms, bool p_trace) {"
    out = [body[0], "\tMCPTrace::Record trace;", "\ttrace.traceable = p_trace;"]
    for l in body[1:]:
        s = l.strip()
        if s == 'return _immediate(_error_response("null", PARSE_ERROR, "Parse error", 400));':
            out.append('\treturn _tag(_immediate(_error_response("null", PARSE_ERROR, "Parse error", 400)), trace);')
        elif s == 'return _immediate(_error_response("null", INVALID_REQUEST, "Invalid request: request must be a JSON object"));':
            out.append('\treturn _tag(_immediate(_error_response("null", INVALID_REQUEST, "Invalid request: request must be a JSON object")), trace);')
        elif s == 'return _immediate(_error_response(id_json, INVALID_REQUEST, "Invalid request: missing method"));':
            out.append('\treturn _tag(_immediate(_error_response(id_json, INVALID_REQUEST, "Invalid request: missing method")), trace);')
        elif s == 'return _immediate(_result_response(200, _envelope_result(id_json, result)));':
            out.append('\treturn _tag(_immediate(_result_response(200, _envelope_result(id_json, result))), trace);')
        elif s == 'return _immediate(_result_response(202, String()));':
            out.append('\treturn _tag(_immediate(_result_response(202, String())), trace);')
        elif s == 'return _immediate(_result_response(200, _envelope_result(id_json, Dictionary())));':
            out.append('\treturn _tag(_immediate(_result_response(200, _envelope_result(id_json, Dictionary()))), trace);')
        elif s.startswith('return _dispatch_tools_call('):
            out.append('\t\treturn _dispatch_tools_call(id_json, request.get("params", Variant()), p_registry, p_is_editor, p_default_timeout_ms, trace);')
        elif s.startswith('return _immediate(_error_response(id_json, METHOD_NOT_FOUND,'):
            out.append('\treturn _tag(_immediate(_error_response(id_json, METHOD_NOT_FOUND, vformat("Method not found: %s", method))), trace);')
        else:
            out.append(l)
    dispatch = [MARK] + out
    print("dispatch: %d lines (recorded rev388 body + trace plumbing)" % len(dispatch))

    # 2. drop the early `handle` and splice the two recorded pieces in.
    lines = E.lines_of(SRC)
    hs = [i for i, l in enumerate(lines) if l.strip().startswith("Response handle(const String &p_payload")]
    assert len(hs) == 1, "handle: %d" % len(hs)
    he = [i for i, l in enumerate(lines) if l.strip() == "} // namespace MCPJsonRpc"]
    assert len(he) == 1
    lines = lines[:hs[0]] + handle + dispatch + [""] + lines[he[0]:]

    ci = [i for i, l in enumerate(lines) if l.strip() == "// is a pass-through that copies nothing."]
    assert len(ci) == 1, "_tag comment: %d" % len(ci)
    lines = lines[:ci[0]] + immediate + [""] + lines[ci[0]:]
    print("final: %d lines" % len(lines))

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
