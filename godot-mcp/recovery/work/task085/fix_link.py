# -*- coding: utf-8 -*-
"""TASK-085: the last two link gaps.

1. tools/project_write_resource_scene.cpp - the header exports
   `MCPTools::write_resource_properties` (project_write_resource_scene.h:92) and
   `_tool_edit_resource` calls it, but the tree only has the private
   `_write_resource_properties`. A one-line adapter inside `namespace MCPTools`
   restores the exported symbol; the recorded body is untouched.

2. tools/tool_helpers.cpp - `MCPTools::schema_with_integer_defaults` is declared
   in tool_helpers.h:1202 and defined at tool_helpers.cpp:3198 of the recorded
   rev3233 t=1790245547163 window, but the tree copy has lost it. Its recorded
   body is re-inserted verbatim.

usage: python fix_link.py [--apply]
"""
import io
import sys

sys.path.insert(0, ".")
import evfetch as E  # noqa: E402

PWRS = r"H:\rebuild\godot\modules\mcp_server\tools\project_write_resource_scene.cpp"
HELP = r"H:\rebuild\godot\modules\mcp_server\tools\tool_helpers.cpp"


def window(sub, rev, t):
    for r in E.reads(sub):
        if r.get("totalLines") == rev and r.get("time") == t:
            return {no: txt.rstrip("\r") for no, txt in r.get("lines") or []}
    raise SystemExit("window rev%s t=%s not found for %s" % (rev, t, sub))


def fun_end(lines, start):
    depth = 0
    for j in range(start, len(lines)):
        s = lines[j].split("//", 1)[0]
        depth += s.count("{") - s.count("}")
        if j > start and depth == 0:
            return j
    raise SystemExit("unbalanced block at line %d" % (start + 1))


def main():
    # ---- 1. the exported resource-bag writer --------------------------------
    lines = E.lines_of(PWRS)
    ds = [i for i, l in enumerate(lines)
          if l.strip().startswith("static bool _write_resource_properties(const Ref<Resource> &p_resource, const Dictionary &p_properties,")
          and not l.strip().endswith(";")]
    assert len(ds) >= 1, "_write_resource_properties: %d" % len(ds)
    ds = [ds[-1]]  # the definition follows the forward declaration
    end = fun_end(lines, ds[0])
    adapter = [
        "",
        "namespace MCPTools {",
        "",
        "// The exported name the header declares (project_write_resource_scene.h).",
        "bool write_resource_properties(const Ref<Resource> &p_resource, const Dictionary &p_properties,",
        "\t\tDictionary &r_changed, Dictionary &r_ignored, Array &r_properties_set, MCPToolError &r_error) {",
        "\treturn _write_resource_properties(p_resource, p_properties, r_changed, r_ignored, r_properties_set, r_error);",
        "}",
        "",
        "} // namespace MCPTools",
    ]
    print("pwrs: adding the exported adapter after line %d" % (end + 1))
    lines = lines[:end + 1] + adapter + lines[end + 1:]

    # ---- 2. schema_with_integer_defaults -----------------------------------
    w = window(r"tools\tool_helpers.cpp", 3233, 1790245547163)
    start = None
    for no in sorted(w):
        if w[no].strip().startswith("Dictionary schema_with_integer_defaults("):
            start = no
            break
    if start is None:
        raise SystemExit("rev3233 window does not carry the definition")
    endno = max(w)
    helper = [w[n] for n in range(start, endno + 1)]
    # The window stops at `schema["properties"] = properties;`; the two lines
    # that close the helper are the only non-recorded ones (the return type and
    # the recorded comment leave no other reading).
    helper += ["\treturn schema;", "}"]
    print("helpers: re-inserting the recorded %d-line definition (rev3233 %d-%d)" % (len(helper), start, endno))
    assert helper[-1] == "}"

    hl = E.lines_of(HELP)
    idx = [i for i, l in enumerate(hl) if l.strip() == "} // namespace MCPTools"]
    assert len(idx) == 1, "namespace close: %d" % len(idx)
    head = idx[0]
    hl = hl[:head] + helper + ["", ""] + hl[head:]
    print("helpers: %d -> %d lines" % (len(hl) - len(helper) - 2, len(hl)))

    if "--apply" not in sys.argv:
        print("(dry run; pass --apply to write)")
        return
    for path, data in ((PWRS, lines), (HELP, hl)):
        text = "\n".join(data) + "\n"
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        assert io.open(path, encoding="utf-8", errors="replace").read() == text
        print("wrote %s (%d lines), read-back OK" % (path, len(data)))


if __name__ == "__main__":
    main()
