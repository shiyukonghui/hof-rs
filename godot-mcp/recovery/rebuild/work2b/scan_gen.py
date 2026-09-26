import io, json, os, re
R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
T = os.path.join(R,"transcripts")
pat_file = "gen_renamed_contract.py"
hits = []
for fn in sorted(os.listdir(T)):
    if not fn.endswith(".jsonl"): continue
    p = os.path.join(T, fn)
    with io.open(p,"r",encoding="utf-8",errors="replace") as f:
        for ln, line in enumerate(f,1):
            if pat_file in line and ("editor_get_scene_tree" in line or "1.22" in line or "ADDED_TOOLS" in line or "DESCRIPTION_OVERRIDES" in line):
                hits.append((fn,ln,line))
with io.open(os.path.join(R,"rebuild","work2b","gen-hits.txt"),"w",encoding="utf-8",newline="\n") as f:
    for fn,ln,line in hits:
        f.write("===== %s : line %d (len=%d) =====\n" % (fn,ln,len(line)))
        f.write(line[:200000])
        f.write("\n")
print("hits",len(hits))
for fn,ln,_ in hits[:60]: print(fn,ln)
