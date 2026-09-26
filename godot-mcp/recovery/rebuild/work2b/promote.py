import io, os, hashlib, shutil, subprocess, json

R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
W = os.path.join(R, "rebuild", "work2b")
G = os.path.join(R, "rebuild", "godot")

# --- promote registration.cpp from _low-confidence into the tree (fossil preserved) ---
src = os.path.join(R, "rebuild", "_low-confidence", "modules", "mcp_server", "tools", "registration.cpp")
dst = os.path.join(G, "modules", "mcp_server", "tools", "registration.cpp")
fossil = os.path.join(W, "registration.cpp.fossil-2a")
raw = io.open(dst, "rb").read()
io.open(fossil, "wb").write(raw)
print("fossil  bytes=%d sha256=%s" % (len(raw), hashlib.sha256(raw).hexdigest()))
new = io.open(src, "rb").read()
io.open(dst, "wb").write(new)
after = io.open(dst, "rb").read()
print("promoted bytes=%d lines=%d sha256=%s" % (len(after), after.decode("utf-8").count("\n") + 1, hashlib.sha256(after).hexdigest()))

# --- promote the version-fixed generator into the tree (fossil preserved) ---
gsrc = os.path.join(W, "gen", "gen_renamed_contract.py")
gdst = os.path.join(G, "modules", "mcp_server", "scripts", "gen_renamed_contract.py")
gfos = os.path.join(W, "gen_renamed_contract.py.fossil-2a")
graw = io.open(gdst, "rb").read()
io.open(gfos, "wb").write(graw)
print("gen fossil bytes=%d sha256=%s" % (len(graw), hashlib.sha256(graw).hexdigest()))
gnew = io.open(gsrc, "rb").read()
io.open(gdst, "wb").write(gnew)
gafter = io.open(gdst, "rb").read()
print("gen promoted bytes=%d lines=%d sha256=%s" % (len(gafter), gafter.decode("utf-8").count("\n") + 1, hashlib.sha256(gafter).hexdigest()))
