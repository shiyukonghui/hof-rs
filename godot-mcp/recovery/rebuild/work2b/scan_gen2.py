import io, json, os, re
R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
T = os.path.join(R,"transcripts")
TARGET = "gen_renamed_contract.py"
rows = []
for fn in sorted(os.listdir(T)):
    if not fn.endswith(".jsonl"): continue
    p = os.path.join(T, fn)
    with io.open(p,"r",encoding="utf-8",errors="replace") as f:
        for ln, line in enumerate(f,1):
            if TARGET not in line: continue
            rows.append((fn,ln,len(line),line))
# report biggest lines
rows.sort(key=lambda r:-r[2])
with io.open(os.path.join(R,"rebuild","work2b","gen-biglines.txt"),"w",encoding="utf-8",newline="\n") as f:
    for fn,ln,sz,line in rows[:12]:
        f.write("===== %s:%d size=%d =====\n" % (fn,ln,sz))
        f.write(line[:400000])
        f.write("\n")
print("rows",len(rows))
for fn,ln,sz,_ in rows[:12]: print(sz,fn,ln)
