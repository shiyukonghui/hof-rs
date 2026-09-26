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
            seq = obj.get("seq", 0)
            t = obj.get("time", 0)
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

# when did the file first reach 1355 lines (or its maximum)?
mx = max(m["total"] or 0 for m in metas)
print("max total seen:", mx)
final = [m for m in metas if (m["total"] or 0) >= 1350]
final.sort(key=lambda m: (m["time"], m["seq"]))
print("records at total>=1350:", len(final))
for m in final[:12]:
    print("  %s:%d time=%d seq=%d total=%s off=%d end=%d" % (m["fn"][:8], m["ln"], m["time"], m["seq"], m["total"], m["off"], m["end"]))

t0 = final[0]["time"] if final else 0
print("t0 =", t0)
sel = [m for m in metas if m["time"] >= t0]
sel.sort(key=lambda m: (m["time"], m["seq"]))
slot = {}
for m in sel:
    for it in m["lines"]:
        if isinstance(it, dict) and "number" in it:
            slot[int(it["number"])] = (it["text"], "%s:%d" % (m["fn"][:8], m["ln"]))
maxn = max(slot) if slot else 0
missing = [i for i in range(1, maxn + 1) if i not in slot]
runs = []
st = pv = None
for x in missing:
    if st is None:
        st = pv = x
        continue
    if x == pv + 1:
        pv = x
        continue
    runs.append((st, pv)); st = pv = x
if st is not None:
    runs.append((st, pv))
print("selected windows:", len(sel), "covered:", len(slot), "max:", maxn, "missing:", len(missing))
print("missing runs:", runs[:60])
outp = os.path.join(R, "rebuild", "work2b", "accept-final.txt")
io.open(outp, "w", encoding="utf-8", newline="\n").write(
    "".join("%05d\t%s\t%s\n" % (i, slot.get(i, ("<<<MISSING>>>", "-"))[1], slot.get(i, ("<<<MISSING>>>", "-"))[0]) for i in range(1, maxn + 1)))
print("wrote", outp)
