import io, os, re, hashlib

R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
p = os.path.join(R, "rebuild", "godot", "modules", "mcp_server", "scripts", "accept_m1.ps1")
lines = io.open(p, encoding="utf-8", errors="replace").read().replace("\r\n", "\n").split("\n")

cases = [(i + 1, m.group(1)) for i, l in enumerate(lines) for m in [re.search(r"Invoke-Case '([^']+)'", l)] if m]
recs = [(i + 1, m.group(1)) for i, l in enumerate(lines) for m in [re.search(r"Record-Result '([^']+)'", l)] if m]
print("Invoke-Case sites: %d" % len(cases))
for n, c in cases:
    print("   %4d  %s" % (n, c))
print("Record-Result sites: %d" % len(recs))
for n, c in recs:
    print("   %4d  %s" % (n, c))

# duplicate block comparison
def sig(a, b):
    x = "\n".join(lines[a - 1:b])
    return len(x), hashlib.sha256(x.encode("utf-8")).hexdigest()

pairs = [(976, 1083), (1028, 1083), (876, 895), (886, 895)]
for a, b in pairs:
    print("block[%d:%d] len/sha = %s" % (a, b, sig(a, b)))
# find where an identical block to 976..1083 occurs earlier
target = lines[975:1083]
for start in range(0, len(lines) - len(target)):
    if lines[start:start + len(target)] == target:
        print("identical tail block also at lines %d..%d" % (start + 1, start + len(target)))
        break
t2 = lines[875:895]
for start in range(0, len(lines) - len(t2)):
    if lines[start:start + len(t2)] == t2:
        print("identical guard block also at lines %d..%d" % (start + 1, start + len(t2)))
