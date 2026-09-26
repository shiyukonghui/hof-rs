import io, json, os, re, sys

R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
T = os.path.join(R, "transcripts")
TARGET = "gen_renamed_contract.py"

def walk(o, path, acc):
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, path + "/" + k, acc)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, path + "/%d" % i, acc)
    else:
        acc.append((path, o))
    return acc

wins = []
files = sorted(os.listdir(T))
for fi, fn in enumerate(files):
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
            order = obj.get("seq", 0)
            metas = []

            def collect(o):
                if isinstance(o, dict):
                    if isinstance(o.get("path"), str) and isinstance(o.get("lines"), list):
                        metas.append(o)
                    for v in o.values():
                        collect(v)
                elif isinstance(o, list):
                    for v in o:
                        collect(v)

            collect(obj)
            for mp in metas:
                pth = mp.get("path")
                if not isinstance(pth, str) or not pth.endswith(TARGET):
                    continue
                lst = mp.get("lines")
                if not isinstance(lst, list) or not lst:
                    continue
                norm = []
                for it in lst:
                    if isinstance(it, dict) and "number" in it and "text" in it:
                        norm.append((int(it["number"]), it["text"]))
                if not norm:
                    continue
                wins.append({
                    "file": fn, "line": ln, "seq": order,
                    "offset": norm[0][0], "count": len(norm),
                    "total": mp.get("totalLines"), "lines": norm,
                })

print("window records:", len(wins))
slot = {}
for w in sorted(wins, key=lambda x: (x["seq"], x["file"], x["line"])):
    for num, text in w["lines"]:
        slot[num] = (text, "%s:%d seq=%s" % (w["file"][:8], w["line"], w["seq"]))
maxn = max(slot) if slot else 0
missing = [i for i in range(1, maxn + 1) if i not in slot]
runs = []
start = None
prev = None
for m in missing:
    if start is None:
        start = m; prev = m; continue
    if m == prev + 1:
        prev = m; continue
    runs.append((start, prev)); start = m; prev = m
if start is not None:
    runs.append((start, prev))
print("covered lines:", len(slot), "max:", maxn, "missing:", len(missing))
print("missing runs:", runs[:60])
with io.open(os.path.join(R, "rebuild", "work2b", "gen-merged2.txt"), "w", encoding="utf-8", newline="\n") as f:
    for i in range(1, maxn + 1):
        t, src = slot.get(i, ("\t<<<MISSING>>>", "-"))
        f.write("%05d\t%s\t%s\n" % (i, src, t))
print("wrote gen-merged2.txt")
