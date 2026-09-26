import io, json, os, re

R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
T = os.path.join(R, "transcripts")
TARGET = "accept_m1.ps1"

metas = []
files = sorted(os.listdir(T))
for fn in files:
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
            seq = obj.get("seq", 0)

            def collect(o):
                if isinstance(o, dict):
                    if isinstance(o.get("path"), str) and o["path"].endswith(TARGET) and isinstance(o.get("lines"), list):
                        metas.append((seq, fn, ln, o))
                    for v in o.values():
                        collect(v)
                elif isinstance(o, list):
                    for v in o:
                        collect(v)

            collect(obj)

print("window records:", len(metas))
byfile = {}
for seq, fn, ln, mp in metas:
    key = fn
    byfile.setdefault(key, {"n": 0, "min": 10 ** 9, "max": 0, "totals": set()})
    b = byfile[key]
    b["n"] += 1
    nums = [it["number"] for it in mp["lines"] if isinstance(it, dict) and "number" in it]
    if nums:
        b["min"] = min(b["min"], min(nums))
        b["max"] = max(b["max"], max(nums))
    if mp.get("totalLines"):
        b["totals"].add(mp["totalLines"])

rows = sorted(byfile.items(), key=lambda kv: -kv[1]["max"])
with io.open(os.path.join(R, "rebuild", "work2b", "accept-windows-summary.txt"), "w", encoding="utf-8", newline="\n") as f:
    for fn, b in rows:
        f.write("%-60s n=%-3d min=%-5d max=%-5d totals=%s\n" % (fn[:60], b["n"], b["min"], b["max"], sorted(b["totals"])))

# coverage using latest seq wins
slot = {}
for seq, fn, ln, mp in sorted(metas, key=lambda m: (m[0], m[1], m[2])):
    for it in mp["lines"]:
        if isinstance(it, dict) and "number" in it:
            slot[int(it["number"])] = (it["text"], "%s:%d" % (fn[:8], ln))
maxn = max(slot) if slot else 0
missing = [i for i in range(1, maxn + 1) if i not in slot]
runs = []
start = prev = None
for m in missing:
    if start is None:
        start = prev = m
        continue
    if m == prev + 1:
        prev = m
        continue
    runs.append((start, prev))
    start = prev = m
if start is not None:
    runs.append((start, prev))
print("covered:", len(slot), "max:", maxn, "missing:", len(missing))
print("missing runs:", runs[:80])
io.open(os.path.join(R, "rebuild", "work2b", "accept-merged.txt"), "w", encoding="utf-8", newline="\n").write(
    "".join("%05d\t%s\t%s\n" % (i, slot.get(i, ("<<<MISSING>>>", "-"))[1], slot.get(i, ("<<<MISSING>>>", "-"))[0]) for i in range(1, maxn + 1)))
