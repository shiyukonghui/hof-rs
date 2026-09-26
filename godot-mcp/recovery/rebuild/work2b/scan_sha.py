import io, json, os, re
R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
out = []
pats = re.compile(r"a5c59853|6f654b64|GENERATOR_VERSION = ")
for root, dirs, files in os.walk(os.path.join(R,"transcripts")):
    for fn in files:
        if not fn.endswith(".jsonl"): continue
        p = os.path.join(root, fn)
        try:
            with io.open(p, "r", encoding="utf-8", errors="replace") as f:
                for ln, line in enumerate(f, 1):
                    if pats.search(line):
                        out.append((fn, ln, line))
        except Exception as e:
            out.append((fn, -1, "ERR " + str(e)))
with io.open(os.path.join(R,"rebuild","work2b","sha-context.txt"), "w", encoding="utf-8", newline="\n") as f:
    for fn, ln, line in out:
        for m in pats.finditer(line):
            s = max(0, m.start()-260); e = min(len(line), m.end()+260)
            f.write("== %s:%d ==\n%s\n" % (fn, ln, line[s:e].replace("\\n","\n")))
print("events", len(out))
