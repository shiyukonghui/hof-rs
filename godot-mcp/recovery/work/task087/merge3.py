# -*- coding: utf-8 -*-
"""Revision-aware reconstruction.

  merge3.py <abs-path> --epoch <ms> [--out F] [--report F] [--no-edits]

Phase A  windows: keep, for every line number, the text from the NEWEST read row
         at or before `--epoch` that carries that line number.  This is a
         single-revision skeleton: every contributing window belongs to the same
         recorded revision lineage, so line numbers stay comparable, and a
         later revision never overrides an earlier one line by line.
Phase B  edits:   replay every applied edit AFTER the epoch in time order.
         * exact     - `old` occurs exactly once
         * anchored  - `old` is absent whole, but its first and last line are
                       both present in the buffer (first at or before last); the
                       span between them is replaced by `new`.  Both anchors are
                       recorded text, so only the span the two revisions
                       genuinely disagree about is rewritten.
         * missing   - reported, never guessed.
"""
from __future__ import print_function
import io, json, os, sys
sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087")
import rep

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"


def norm(p):
    return (p or "").replace("/", "\\").lower()


def load(fp, target):
    out = []
    t = norm(target)
    with io.open(fp, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            if norm(o.get("path") or "") == t:
                out.append(o)
    return out


def applied(e):
    return not (e.get("result") or "").lstrip().startswith("Error")


def line_text(el):
    if isinstance(el, (list, tuple)):
        if len(el) >= 2:
            return el[1] if isinstance(el[1], str) else str(el[1])
        return str(el[0]) if el else ""
    if isinstance(el, str):
        for sep in ("\t", ": ", "\t "):
            i = el.find(sep)
            if i > 0 and el[:i].strip().isdigit():
                return el[i + len(sep):]
        return el
    return str(el)


def rebuild(target, epoch, no_edits=False):
    reads = load(os.path.join(IDX, "events-read.jsonl"), target)
    edits = load(os.path.join(IDX, "events-edit.jsonl"), target)

    use = [r for r in reads if (r.get("time", 0) or 0) <= epoch and (r.get("lines") or [])]
    chosen, key_of = {}, {}
    for r in sorted(use, key=lambda x: (x.get("time", 0), x.get("seq") or 0)):
        off = r.get("offset") or 1
        k = (r.get("time", 0), r.get("seq") or 0)
        for i, raw in enumerate(r.get("lines") or []):
            n = off + i
            if n not in key_of or k >= key_of[n]:
                chosen[n] = line_text(raw)
                key_of[n] = k
    total = max(chosen) if chosen else 0
    holes = [n for n in range(1, total + 1) if n not in chosen]
    rep.log("phase A: windows used=%d/%d  lines=%d max=%d holes=%d"
            % (len(use), len(reads), len(chosen), total, len(holes)))
    if holes:
        rngs = []
        s = p = holes[0]
        for h in holes[1:]:
            if h == p + 1:
                p = h
                continue
            rngs.append((s, p))
            s = p = h
        rngs.append((s, p))
        rep.log("  holes: %s" % rngs[:30])

    buf = "\n".join(chosen.get(n, "") for n in range(1, total + 1))
    if not buf.endswith("\n"):
        buf += "\n"
    rep.log("phase A result: lines=%d bytes=%d" % (buf.count("\n"), len(buf.encode("utf-8"))))

    if no_edits:
        return buf, {}

    exact, anchored, missing = [], [], []
    for e in sorted(edits, key=lambda x: (x.get("time", 0), x.get("seq") or 0)):
        if not applied(e) or (e.get("time", 0) or 0) <= epoch:
            continue
        old = e.get("old") or ""
        new = e.get("new") or ""
        if not old:
            missing.append((e, "empty-old"))
            continue
        c = buf.count(old)
        if c == 1:
            buf = buf.replace(old, new, 1)
            exact.append(e)
            continue
        if c > 1:
            missing.append((e, "ambiguous:%d" % c))
            continue
        ol = old.split("\n")
        nl = new.split("\n")
        while ol and ol[-1] == "":
            ol.pop()
        while nl and nl[-1] == "":
            nl.pop()
        if not ol:
            missing.append((e, "empty-old-lines"))
            continue
        head = buf.find(ol[0])
        if head < 0:
            missing.append((e, "no-head"))
            continue
        if len(ol) == 1:
            buf = buf[:head] + "\n".join(nl) + buf[head + len(ol[0]):]
            anchored.append(e)
            continue
        tail = buf.find(ol[-1], head + len(ol[0]))
        if tail < 0:
            missing.append((e, "no-tail"))
            continue
        buf = buf[:head] + "\n".join(nl) + buf[tail + len(ol[-1]):]
        anchored.append(e)

    rep.log("phase B: exact=%d anchored=%d missing=%d" % (len(exact), len(anchored), len(missing)))
    for e, why in missing:
        rep.log("  MISS seq=%-6s t=%-14s %-16s old=%d new=%d | %s"
                % (e.get("seq"), e.get("time"), why,
                   (e.get("old") or "").count("\n") + 1, (e.get("new") or "").count("\n") + 1,
                   (e.get("old") or "").split("\n")[0][:110]))
    rep.log("phase B result: lines=%d bytes=%d" % (buf.count("\n"), len(buf.encode("utf-8"))))
    return buf, {"exact": len(exact), "anchored": len(anchored), "missing": len(missing)}


def main():
    target = sys.argv[1]
    argv = sys.argv[2:]
    epoch = int(argv[argv.index("--epoch") + 1]) if "--epoch" in argv else 0
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    if "--report" in argv:
        rep.set_report(argv[argv.index("--report") + 1])
    buf, info = rebuild(target, epoch, no_edits="--no-edits" in argv)
    if out:
        with io.open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(buf)
        rep.log("wrote %s" % out)
    rep.flush()


if __name__ == "__main__":
    main()
