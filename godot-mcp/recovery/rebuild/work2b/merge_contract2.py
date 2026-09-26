import io, json, os, re, hashlib

R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
T = os.path.join(R, "transcripts")
TARGET = "tools_list.renamed.json"

metas = []
for fn in sorted(os.listdir(T)):
    if not fn.endswith(".jsonl"):
        continue
    p = os.path.join(T, fn)
    with io.open(p, "r", encoding="utf-8", errors="replace") as f:
        for ln, line in enumerate(f, 1):
            if TARGET not in line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            t = obj.get("time", 0); seq = obj.get("seq", 0)

            def collect(o):
                if isinstance(o, dict):
                    if isinstance(o.get("path"), str) and o["path"].endswith(TARGET) and isinstance(o.get("lines"), list):
                        metas.append((t, seq, fn, ln, o))
                    for v in o.values():
                        collect(v)
                elif isinstance(o, list):
                    for v in o:
                        collect(v)

            collect(obj)

# group windows by totalLines and pick the newest group
groups = {}
for m in metas:
    tl = m[4].get("totalLines")
    if tl:
        groups.setdefault(tl, []).append(m)
for tl in sorted(groups, key=lambda x: -x):
    ws = groups[tl]
    tmax = max(x[0] for x in ws)
    cov = set()
    for x in ws:
        for it in x[4]["lines"]:
            if isinstance(it, dict):
                cov.add(it["number"])
    print("total=%s windows=%d coverage=%d latest=%d" % (tl, len(ws), len(cov), tmax))

# helper: locate a JSON object by tool name across windows of the newest group
newest = max(groups, key=lambda x: max(m[0] for m in groups[x]))
ws = sorted(groups[newest], key=lambda x: (x[0], x[1]))
print("newest group total =", newest)

def find_text(substr):
    out = []
    for t, seq, fn, ln, mp in ws:
        for it in mp["lines"]:
            if isinstance(it, dict) and substr in it["text"]:
                out.append((it["number"], it["text"], fn, ln))
    return out

for probe in ("editor_get_scene_tree", "editor_set_tilemap_cell", "editor_set_tilemap_cells_in_rect"):
    hits = find_text('"name": "%s"' % probe)
    print("---", probe, "->", [(h[0], h[2][:8], h[3]) for h in hits])

# extract description fields for the three names by scanning windows for '"description": "' near the name
for probe in ("editor_get_scene_tree", "editor_set_tilemap_cell", "editor_set_tilemap_cells_in_rect"):
    segs = []
    for t, seq, fn, ln, mp in ws:
        txt = "\n".join(it["text"] for it in mp["lines"] if isinstance(it, dict))
        idx = txt.find('"name": "%s"' % probe)
        if idx >= 0:
            start = max(0, idx - 4000)
            segs.append((ln, fn, txt[start:idx + 200]))
    print("### %s segments=%d" % (probe, len(segs)))
    for ln, fn, s in segs[:3]:
        io.open(os.path.join(R, "rebuild", "work2b", "desc-%s-%d.txt" % (probe, ln)), "w", encoding="utf-8", newline="\n").write(s)
