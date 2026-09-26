# -*- coding: utf-8 -*-
"""Merge recorded read windows by line number, then replay recorded edits.

Pass 1 (windows): for every line number keep the text carried by the NEWEST
recorded read row that has it.  Records how many distinct texts were seen per
line and which was chosen, so genuine window conflicts are visible instead of
being hidden by the pick.

Pass 2 (edits): replay every applied edit in time order.
  * exact   - `old` occurs exactly once in the buffer -> plain replace
  * anchored- `old` was not found whole, but on a per-line scan the buffer
              shares at least MIN_OVERLAP lines with the head and the tail of
              `old`; the differing middle is replaced by the corresponding
              middle of `new`.  The shared bytes are recorded text on both
              sides, so this only ever rewrites the span the two revisions
              actually disagree about.  Cross-revision boundary alignment.
  * missing - no anchor; reported as a BREAK and left untouched.

usage: python merge2.py <abs-path> [--out F] [--report F] [--windows-only]
"""
from __future__ import print_function
import io, json, os, sys
sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087")
import rep

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
MIN_OVERLAP = 2


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


def build(target, windows_only=False, verbose=True, skeleton=None):
    reads = load(os.path.join(IDX, "events-read.jsonl"), target)
    edits = load(os.path.join(IDX, "events-edit.jsonl"), target)

    if skeleton is not None:
        reads = [r for r in reads if (r.get("totalLines") or 0) <= skeleton]
        rep.log("skeleton filter: totalLines <= %d keeps %d window row(s)" % (skeleton, len(reads)))

    variants = {}
    chosen = {}
    chosen_key = {}
    for r in sorted(reads, key=lambda x: (x.get("time", 0), x.get("seq") or 0)):
        off = r.get("offset") or 1
        lines = r.get("lines") or []
        if not lines:
            continue
        key = (r.get("time", 0), r.get("seq") or 0)
        for i, raw in enumerate(lines):
            n = off + i
            txt = line_text(raw)
            variants.setdefault(n, {})
            variants[n][txt] = variants[n].get(txt, 0) + 1
            if n not in chosen_key or key >= chosen_key[n]:
                chosen[n] = txt
                chosen_key[n] = key

    total = max(chosen) if chosen else 0
    holes = [n for n in range(1, total + 1) if n not in chosen]
    multi = [n for n in chosen if len(variants[n]) > 1]
    rep.log("windows=%d lines=%d max=%d holes=%d conflicting-lines=%d"
            % (len(reads), len(chosen), total, len(holes), len(multi)))

    buf = "\n".join(chosen.get(n, "") for n in range(1, total + 1))
    if not buf.endswith("\n"):
        buf += "\n"
    before = buf
    rep.log("merged: lines=%d bytes=%d" % (buf.count("\n"), len(buf.encode("utf-8"))))

    if windows_only:
        return buf, {"applied": [], "anchored": [], "missing": [], "total_lines": total}

    done = anchored = []
    missing = []
    for e in sorted(edits, key=lambda x: (x.get("time", 0), x.get("seq") or 0)):
        if not applied(e):
            continue
        old = e.get("old") or ""
        new = e.get("new") or ""
        if not old:
            missing.append((e, "empty-old"))
            continue
        c = buf.count(old)
        if c == 1:
            buf = buf.replace(old, new, 1)
            done.append(e)
            continue
        if c > 1:
            missing.append((e, "ambiguous:%d" % c))
            continue
        # --- overlap-based anchor alignment -------------------------------
        ob = old.split("\n")
        nb = new.split("\n")
        while ob and ob[-1] == "":
            ob.pop()
        while nb and nb[-1] == "":
            nb.pop()
        pos = -1
        for start in range(0, len(buf)):
            if buf.startswith(ob[0], start):
                pos = start
                break
        if pos < 0:
            missing.append((e, "no-head"))
            continue
        buf_end = pos + len(ob[0])
        head_share = 1
        tail_share = 0
        # tail: does the buffer end the block with the same last line of old?
        tail_start = buf.find("\n" + ob[-1] + "\n", buf_end)
        if tail_start >= 0:
            tail_share = 1
        if head_share + tail_share < MIN_OVERLAP:
            missing.append((e, "thin-anchor"))
            continue
        if tail_share:
            end = tail_start + 1 + len(ob[-1])
        else:
            end = buf_end
        repl = "\n".join(nb) if tail_share == 0 else None
        if tail_share:
            repl = ob[0] + "\n" + "\n".join(nb[1:]) if len(nb) > 1 else ob[0]
        buf = buf[:pos] + repl + buf[end:]
        anchored.append(e)

    rep.log("edits: exact=%d anchored=%d missing=%d" % (len(done), len(anchored), len(missing)))
    for e, why in missing:
        rep.log("  MISS seq=%-6s t=%-14s %-14s old=%d new=%d | %s"
                % (e.get("seq"), e.get("time"), why,
                   (e.get("old") or "").count("\n") + 1, (e.get("new") or "").count("\n") + 1,
                   (e.get("old") or "").split("\n")[0][:110]))
    rep.log("after edits: lines=%d bytes=%d" % (buf.count("\n"), len(buf.encode("utf-8"))))
    return buf, {"applied": done, "anchored": anchored, "missing": missing,
                 "total_lines": total, "conflicts": multi}


def main():
    target = sys.argv[1]
    argv = sys.argv[2:]
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    repf = argv[argv.index("--report") + 1] if "--report" in argv else None
    if repf:
        rep.set_report(repf)
    sk = int(argv[argv.index("--skeleton") + 1]) if "--skeleton" in argv else None
    buf, info = build(target, windows_only="--windows-only" in argv, skeleton=sk)
    if out:
        with io.open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(buf)
        rep.log("wrote %s" % out)
    rep.flush()


if __name__ == "__main__":
    main()
