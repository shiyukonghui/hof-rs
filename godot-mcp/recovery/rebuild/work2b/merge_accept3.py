import io, json, os

R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
T = os.path.join(R, "transcripts")
TARGET = "accept_m1.ps1"

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
            seq = obj.get("seq", 0); t = obj.get("time", 0)
            found = []

            def collect(o):
                if isinstance(o, dict):
                    if isinstance(o.get("path"), str) and o["path"].endswith(TARGET) and isinstance(o.get("lines"), list):
                        found.append(o)
                    for v in o.values():
                        collect(v)
                elif isinstance(o, list):
                    for v in o:
                        collect(v)

            collect(obj)
            for mp in found:
                nums = [it["number"] for it in mp["lines"] if isinstance(it, dict)]
                if nums:
                    metas.append({"fn": fn, "ln": ln, "seq": seq, "time": t, "total": mp.get("totalLines"),
                                  "off": min(nums), "end": max(nums), "lines": mp["lines"]})

last = max(m["time"] for m in metas)
print("latest read time:", last)
lastrecs = [m for m in metas if m["time"] == last]
for m in lastrecs:
    print("  latest:", m["fn"][:8], m["ln"], "total=", m["total"], "off=", m["off"], "end=", m["end"])

# what total does the last read belong to
lt = lastrecs[0]["total"]
grp = [m for m in metas if m["total"] == lt]
grp.sort(key=lambda m: (m["time"], m["seq"]))
print("records for total=%s : %d" % (lt, len(grp)))
for m in grp:
    print("   %s:%d t=%d seq=%d off=%d end=%d n=%d" % (m["fn"][:8], m["ln"], m["time"], m["seq"], m["off"], m["end"], len(m["lines"])))

slot = {}
for m in grp:
    for it in m["lines"]:
        if isinstance(it, dict) and "number" in it:
            slot[int(it["number"])] = (it["text"], "%s:%d" % (m["fn"][:8], m["ln"]))
maxn = max(slot) if slot else 0
missing = [i for i in range(1, maxn + 1) if i not in slot]
runs = []
st = pv = None
for x in missing:
    if st is None:
        st = pv = x; continue
    if x == pv + 1:
        pv = x; continue
    runs.append((st, pv)); st = pv = x
if st is not None:
    runs.append((st, pv))
print("group covered:", len(slot), "max:", maxn, "missing:", len(missing), "runs:", runs[:40])
io.open(os.path.join(R, "rebuild", "work2b", "accept-group-%s.txt" % lt), "w", encoding="utf-8", newline="\n").write(
    "".join("%05d\t%s\t%s\n" % (i, slot.get(i, ("<<<MISSING>>>", "-"))[1], slot.get(i, ("<<<MISSING>>>", "-"))[0]) for i in range(1, maxn + 1)))
