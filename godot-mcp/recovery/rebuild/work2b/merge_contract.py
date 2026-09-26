import io, json, os

R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
T = os.path.join(R, "transcripts")
TARGET = "tools_list.renamed.json"
WANT = "6f654b64f87f60a5b0296e5a7a6b50f3b1a0af98c9ce8770ffe9f964172afbd6"

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

print("read windows for tools_list.renamed.json:", len(metas))
slot = {}
for t, seq, fn, ln, mp in sorted(metas, key=lambda m: (m[0], m[1])):
    for it in mp["lines"]:
        if isinstance(it, dict) and "number" in it:
            slot[int(it["number"])] = (it["text"], "%s:%d" % (fn[:8], ln))
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
print("covered", len(slot), "max", maxn, "missing", len(missing), "runs", runs[:20])
out = os.path.join(R, "rebuild", "work2b", "contract-merged.json")
io.open(out, "w", encoding="utf-8", newline="\n").write("".join(slot[i][0] + "\n" for i in range(1, maxn + 1) if i in slot))
print("wrote", out)

# search for the sha in the same records to learn which revision it was
hits = []
for fn in sorted(os.listdir(T)):
    if not fn.endswith(".jsonl"):
        continue
    p = os.path.join(T, fn)
    with io.open(p, "r", encoding="utf-8", errors="replace") as f:
        for ln, line in enumerate(f, 1):
            if WANT[:12] in line and "tools_list.renamed.json" in line:
                hits.append((fn, ln))
print("records mentioning both the 6f654b64 sha and the file:", len(hits))
