# -*- coding: utf-8 -*-
"""TASK-083 fix: a long source line can come back *truncated* from a read window,
which silently opens a raw-string literal that never closes and swallows every
following brace.  This finds a `String::utf8(R"<d>(` whose line does not contain
the matching `)<d>"` and re-attaches the statement tail.

The correct tail of

    ToolBuilder builder("x",
            String::utf8(R"desc(<text>)desc"));

is `)desc"));` - raw close, then `)` closes String::utf8(, then `)` closes the
builder call, then `;`.
"""
import io
import os
import re
import sys

sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083")
import splice  # noqa: E402

OPEN = re.compile(r'R"([A-Za-z0-9_]*)\($|R"([A-Za-z0-9_]*)\(.')


def main():
    write = "--write" in sys.argv
    fixed = []
    for rel in sys.argv[1:]:
        if rel.startswith("--"):
            continue
        p = rel if os.path.isabs(rel) else os.path.join(splice.TREE, rel.replace("/", os.sep))
        L = splice.read_plain(p)
        changed = False
        for i, line in enumerate(L):
            m = re.search(r'R"([A-Za-z0-9_]*)\(', line)
            if not m:
                continue
            delim = m.group(1)
            if (")" + delim + '"') in line[m.end():]:
                continue
            body = line[:-1] if line.endswith(";") else line
            if body.endswith(')' + delim + '"'):
                body = body + ")"
            elif body.endswith(")"):
                body = body + delim + '"))'
            else:
                raise SystemExit("unexpected shape at line %d: %r" % (i + 1, line[-40:]))
            L[i] = body + ";"
            changed = True
            fixed.append((p, i + 1, len(line), len(L[i]), L[i][-25:]))
        if changed and write:
            with io.open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(L) + "\n")
        print("%-58s %s holes=%d" % (rel, "FIXED" if changed else "clean", sum(1 for _ in fixed) if changed else 0))
    for p, ln, a, b, tail in fixed:
        print("   %s:%d %d -> %d bytes, tail=%r" % (os.path.basename(p), ln, a, b, tail))


if __name__ == "__main__":
    main()
