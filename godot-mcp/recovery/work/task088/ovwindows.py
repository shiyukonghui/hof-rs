# -*- coding: utf-8 -*-
"""task088: which recorded read windows of a file expose the override tables?

For every read row of the path, report if the window contains the
DESCRIPTION_OVERRIDES / SCHEMA_OVERRIDES assignment and count the 4-space keys
inside the window.

usage: python ovwindows.py <abs-path> <outfile>
"""
from __future__ import print_function
import io, json, os, re, sys

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
KEY_RE = re.compile(r'^    "([^"]+)"\s*:')


def norm(p):
    return (p or "").replace("/", "\\").lower()


def line_text(el):
    if isinstance(el, (list, tuple)):
        return el[1] if len(el) >= 2 and isinstance(el[1], str) else ""
    if isinstance(el, str):
        return el
    return ""


def main():
    target = norm(sys.argv[1])
    out = sys.argv[2]
    lines = []
    with io.open(os.path.join(IDX, "events-read.jsonl"), encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            if norm(o.get("path")) != target:
                continue
            body = [line_text(x) for x in (o.get("lines") or [])]
            joined = "\n".join(body)
            marks = []
            if "DESCRIPTION_OVERRIDES = {" in joined:
                marks.append("D")
            if "SCHEMA_OVERRIDES = {" in joined:
                marks.append("S")
            if "GENERATOR_VERSION" in joined:
                marks.append("V")
            keys = [m.group(1) for m in (KEY_RE.match(b) for b in body) if m]
            if not marks and not keys:
                continue
            lines.append("t=%s seq=%s totalLines=%s offset=%s marks=%s keys=%d %s"
                         % (o.get("time"), o.get("seq"), o.get("totalLines"), o.get("offset"),
                            "".join(marks) or "-", len(keys), ",".join(keys)))
    data = "\n".join(lines) + "\n"
    io.open(out, "w", encoding="utf-8", newline="\n").write(data)
    print("rows with marks/keys: %d" % len(lines))
    for l in lines:
        print(l)


if __name__ == "__main__":
    main()
