import io, json, os, hashlib, re
R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
p = os.path.join(R, "rebuild", "_low-confidence", "modules", "mcp_server", "docs", "tools_list.renamed.json")
raw = io.open(p, "rb").read()
print("bytes", len(raw))
print(repr(raw[:400]))
