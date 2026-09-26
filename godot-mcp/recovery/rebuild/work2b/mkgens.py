import io, os, shutil
R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
W = os.path.join(R, "rebuild", "work2b", "gen")
os.makedirs(W, exist_ok=True)
src = os.path.join(R, "staging", "modules", "mcp_server", "scripts", "gen_renamed_contract.py")
raw = io.open(src, "rb").read().decode("utf-8")
assert 'GENERATOR_VERSION = "1.3.0"' in raw, "constant not found"
fixed = raw.replace('GENERATOR_VERSION = "1.3.0"', 'GENERATOR_VERSION = "1.22.0"', 1)
out = os.path.join(W, "gen_renamed_contract.py")
io.open(out, "wb").write(fixed.encode("utf-8"))
print("wrote", out, len(fixed.encode("utf-8")), "bytes")
print("occurrences of 1.3.0 left:", fixed.count("1.3.0"))
