import io, os, hashlib, subprocess, json

R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
W = os.path.join(R, "rebuild", "work2b")
P = os.path.join(R, "rebuild", "godot", "modules", "mcp_server", "scripts", "accept_m1.ps1")

# restore the payload copy
raw = io.open(os.path.join(W, "accept_m1.ps1.before-repair"), "rb").read()
io.open(P, "wb").write(raw)
print("restored bytes=%d sha=%s" % (len(raw), hashlib.sha256(raw).hexdigest()))

merged = {}
for ln in io.open(os.path.join(W, "accept-final.txt"), encoding="utf-8"):
    parts = ln.rstrip("\n").split("\t", 2)
    if len(parts) == 3:
        merged[int(parts[0])] = None if parts[2] == "<<<MISSING>>>" else parts[2]
maxn = max(merged)
gap_runs = []
st = pv = None
for n in sorted(merged):
    if merged[n] is None:
        if st is None:
            st = pv = n; continue
        if n == pv + 1:
            pv = n; continue
        gap_runs.append((st, pv)); st = pv = n
if st is not None:
    gap_runs.append((st, pv))
print("merged max=%d gaps=%s" % (maxn, gap_runs))

tree = raw.decode("utf-8").replace("\r\n", "\n").split("\n")
print("tree lines=%d" % len(tree))
# direct offset splice: merged line n (in a gap) <- tree line n-272 (valid for n>=770)
out = []
for n in range(1, maxn + 1):
    if merged.get(n) is not None:
        out.append(merged[n])
    else:
        t = n - 272
        out.append(tree[t - 1] if 1 <= t <= len(tree) else ("# <<<UNRECOVERED merged line %d>>>" % n))
txt = "\n".join(out)
io.open(os.path.join(W, "accept_candidate.ps1"), "wb").write(txt.encode("utf-8"))
print("candidate lines=%d bytes=%d" % (len(out), len(txt.encode("utf-8"))))

ps = r"""
param([string]$F)
$t=$null; $e=$null
[void][System.Management.Automation.Language.Parser]::ParseFile($F,[ref]$t,[ref]$e)
if ($e) { foreach ($x in $e) { Write-Output ($x.ErrorId + ':' + $x.Message + '@' + $x.Extent.StartLineNumber) } } else { Write-Output 'CLEAN' }
"""
pf = os.path.join(W, "one_parse.ps1")
io.open(pf, "w", encoding="ascii", newline="\r\n").write(ps)
p = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", pf, "-F",
                    os.path.join(W, "accept_candidate.ps1")], capture_output=True, text=True)
print("PARSE:", p.stdout.strip()[:2000])
