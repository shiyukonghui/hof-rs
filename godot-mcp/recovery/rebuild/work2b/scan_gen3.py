import io, json, os, re
R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
T = os.path.join(R,"transcripts")
TARGET = "gen_renamed_contract.py"
def walk(o, path, acc):
    if isinstance(o, dict):
        for k,v in o.items(): walk(v, path+"/"+k, acc)
    elif isinstance(o, list):
        for i,v in enumerate(o): walk(v, path+"/%d"%i, acc)
    elif isinstance(o, str):
        if TARGET in o or len(o) > 4000:
            acc.append((path, o))
best = []
for fn in sorted(os.listdir(T)):
    if not fn.endswith(".jsonl"): continue
    p = os.path.join(T, fn)
    with io.open(p,"r",encoding="utf-8",errors="replace") as f:
        for ln, line in enumerate(f,1):
            if TARGET not in line: continue
            try: obj = json.loads(line)
            except Exception: continue
            acc=[]; walk(obj,"",acc)
            for path,s in acc:
                if TARGET in s:
                    best.append((len(s), fn, ln, path, s))
best.sort(key=lambda r:-r[0])
seen=set()
with io.open(os.path.join(R,"rebuild","work2b","gen-strings.txt"),"w",encoding="utf-8",newline="\n") as f:
    for sz,fn,ln,path,s in best[:40]:
        f.write("===== size=%d %s:%d path=%s =====\n" % (sz,fn,ln,path))
        f.write(s if isinstance(s,str) else str(s))
        f.write("\n")
print("strings",len(best))
for sz,fn,ln,path,_ in best[:40]: print(sz, fn, ln)
