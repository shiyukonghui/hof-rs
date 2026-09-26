"""Inventory recorded events for a set of repo-relative paths.

Reads the payload index once and reports, per path: how many whole-file writes,
how many edits (with result!=Error), total new-text lines, and the newest
write/edit timestamps.  No network, no shell.
"""
import io, json, os, sys, collections

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
W = os.path.join(IDX, "events-write.jsonl")
E = os.path.join(IDX, "events-edit.jsonl")
R = os.path.join(IDX, "events-read.jsonl")


def norm(p):
    return p.replace("\\", "/").lower()


def tail_after_marker(p):
    """Map an absolute recorded path to its repo-relative form.

    The tree keeps `modules/mcp_server` as a path component, so the prefix is
    retained (TASK-086's helpers stripped it only because their inputs were
    already module-relative).
    """
    n = p.replace("\\", "/")
    for marker in ("/modules/mcp_server/", "/godot/"):
        i = n.find(marker)
        if i >= 0:
            return n[i + 1:]
    return os.path.basename(n)


def load(path, want):
    rows = []
    seen = 0
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            seen += 1
            raw = None
            for k in ("path", "file", "uri", "resource", "rel", "target"):
                if isinstance(o.get(k), str) and o[k]:
                    raw = o[k]
                    break
            if raw is None:
                continue
            rel = tail_after_marker(raw)
            if norm(rel) in want:
                rows.append((o.get("seq"), o.get("time") or o.get("t") or 0, o, rel))
    print("  [load %s] rows=%d matched=%d" % (os.path.basename(path), seen, len(rows)))
    return rows


def main():
    targets = [a.strip() for a in sys.argv[1:] if a.strip()]
    want = set(norm(t) for t in targets)
    print("targets:", targets)

    wr = load(W, want)
    ed = load(E, want)
    rd = load(R, want)

    byp = collections.defaultdict(lambda: {"w": [], "e": [], "r": []})
    for seq, t, o, rel in wr:
        byp[rel]["w"].append((t, seq, o))
    for seq, t, o, rel in ed:
        byp[rel]["e"].append((t, seq, o))
    for seq, t, o, rel in rd:
        byp[rel]["r"].append((t, seq, o))

    for rel, d in sorted(byp.items()):
        print("\n=== %s ===" % rel)
        print("  writes=%d edits=%d reads=%d" % (len(d["w"]), len(d["e"]), len(d["r"])))
        for label, key in (("WRITE", "w"), ("EDIT", "e")):
            items = sorted(d[key], key=lambda x: x[0])
            print("  -- %s (%d, time order) --" % (label, len(items)))
            for t, seq, o in items[-40:]:
                newt = o.get("new") or o.get("text") or ""
                oldt = o.get("old") or ""
                res = (o.get("result") or "")[:28]
                nlines = newt.count("\n") + 1 if newt else 0
                olines = oldt.count("\n") + 1 if oldt else 0
                print("     seq=%-5s t=%-14s old=%4d new=%4d ok=%s res=%s"
                      % (seq, t, olines, nlines, o.get("ok"), res))
        items = sorted(d["r"], key=lambda x: x[0])
        if items:
            print("  -- READ (last 6 of %d) --" % len(items))
            for t, seq, o in items[-6:]:
                print("     seq=%-5s t=%-14s totalLines=%s lines=%s"
                      % (seq, t, o.get("totalLines"), len(o.get("lines") or [])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
