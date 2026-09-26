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
wins=[]
for fn in sorted(os.listdir(T)):
    if not fn.endswith(".jsonl"): continue
    p = os.path.join(T, fn)
    with io.open(p,"r",encoding="utf-8",errors="replace") as f:
        for ln, line in enumerate(f,1):
            if TARGET not in line: continue
            try: obj=json.loads(line)
            except Exception: continue
            acc=[]; walk(obj,"",acc)
            meta={}
            for path,v in acc:
                m=re.search(r"/meta/(path|totalLines|offset|truncated)$", path)
                if m: meta[m.group(1)]=v
            if not isinstance(meta.get("path"),str) or not meta["path"].endswith(TARGET): continue
            lines=None
            for path,v in acc:
                if path.endswith("/meta/lines") and isinstance(v,list): lines=v; break
            if not lines:
                for path,v in acc:
                    if path.endswith("/lines") and isinstance(v,list): lines=v; break
            if not lines: continue
            norm=[]
            for item in lines:
                if isinstance(item,dict) and "number" in item and "text" in item:
                    norm.append((int(item["number"]), item["text"]))
                elif isinstance(item,str):
                    norm.append((None,item))
            if not norm or norm[0][0] is None: continue
            wins.append({"src":"%s:%d"%(fn,ln),"offset":norm[0][0],"n":len(norm),"total":meta.get("totalLines"),"lines":norm})
# latest wins: sort by total lines ascending then file; we pick per-line from the record with the greatest total (most recent)
wins.sort(key=lambda w:(w["total"] or 0, w["src"]))
sources={}
slot={}
for w in wins:
    for num,text in w["lines"]:
        slot[num]=(text,w["src"])
        sources.setdefault(w["src"],0)
        sources[w["src"]]+=1
maxn=max(slot) if slot else 0
missing=[i for i in range(1,maxn+1) if i not in slot]
print("windows",len(wins),"lines covered",len(slot),"max",maxn,"missing",len(missing))
runs=[]
start=None; prev=None
for m in missing:
    if start is None: start=m; prev=m; continue
    if m==prev+1: prev=m; continue
    runs.append((start,prev)); start=m; prev=m
if start is not None: runs.append((start,prev))
print("missing runs (first 40):", runs[:40])
with io.open(os.path.join(R,"rebuild","work2b","gen-merged.txt"),"w",encoding="utf-8",newline="\n") as f:
    for i in range(1,maxn+1):
        t,src=slot.get(i,("<<<MISSING>>>","-"))
        f.write("%06d|%s|%s\n" % (i, t, src))
print("wrote gen-merged.txt")
