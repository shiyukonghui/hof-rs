# -*- coding: utf-8 -*-
"""TASK-083 fix: project_validate_scripts.cpp line 338 lost the tail of its raw
string literal.  The correct end of the statement is

    String::utf8(R"desc(<text>)desc"));

i.e. raw-close `)desc"`, then `)` closes String::utf8(, then `)` closes the
ToolBuilder builder( opened on line 337, then `;`.  The reconstruction kept only
the last `);`.  This restores the missing `)desc"))` and is idempotent.
"""
import io
import os
import sys

sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083")
import splice  # noqa: E402

P = r"H:\rebuild\godot\modules\mcp_server\tools\project_validate_scripts.cpp"


def main():
    write = "--write" in sys.argv
    L = splice.read_plain(P)
    line = L[337]
    print("before: balance=%s len=%d tail=%r" % (splice.balance(L), len(line), line[-30:]))
    assert line.startswith('\t\t\t\tString::utf8(R"desc('), "unexpected shape"
    body = line[:-1] if line.endswith(";") else line
    if body.endswith(')desc")'):
        body = body + ")"
    elif body.endswith(")"):
        body = body + 'desc"))'
    else:
        raise SystemExit("cannot repair: %r" % line[-30:])
    L[337] = body + ";"
    print("after : balance=%s len=%d tail=%r" % (splice.balance(L), len(L[337]), L[337][-30:]))
    if write:
        with io.open(P, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(L) + "\n")
        print("written")
    print("L[337][-30:] len after =", len(L[337]))


if __name__ == "__main__":
    main()
