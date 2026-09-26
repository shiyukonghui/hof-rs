import io, json, os, re
R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
T = os.path.join(R,"transcripts")
TARGET = "gen_renamed_contract.py"
def walk(o, path, acc):
    if isinstance(o, dict):
        for k,v in o.items(): walk(v, path+"/"+k, acc)
    elif isinstance(o, list):
        for i,v in enumerate(o): walk(v, path+"/%d"%i, acc)
    else:
        acc.append((path,o))
recs=[]
for fn in sorted(os.listdir(T)):
    if not fn.endswith(".jsonl"): continue
    p = os.path.join(T, fn)
    with io.open(p,"r",encoding="utf-8",errors="replace") as f:
        for ln, line in enumerate(f,1):
            if TARGET not in line: continue
            try: obj=json.loads(line)
            except Exception: continue
            acc=[]; walk(obj,"",acc)
            # find meta with path endswith target
            for path,v in acc:
                if path.endswith("/meta/path") and isinstance(v,str) and v.endswith(TARGET):
                    total=None; offset=None; lines=None; trunc=None
                    for path2,v2 in acc:
                        if path2.endswith("/meta/totalLines"): total=v2
                        if path2.endswith("/meta/offset"): offset=v2
                        if path2.endswith("/meta/truncated"): trunc=v2
                        if path2.endswith("/meta/lines") and isinstance(v2,list): lines=len(v2)
                    recs.append((fn,ln,offset,lines,total,trunc))
seen=set(); out=[]
for r in recs:
    k=(r[0],r[1])
    if k in seen: continue
    seen.add(k); out.append(r)
with io.open(os.path.join(R,"rebuild","work2b","gen-reads.txt"),"w",encoding="utf-8",newline="\n") as f:
    for r in out: f.write("%s line=%d offset=%s lines=%s total=%s trunc=%s\n"%r)
print("read-window records:", len(out))
