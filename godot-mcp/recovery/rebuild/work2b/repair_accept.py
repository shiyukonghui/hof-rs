import io, os, hashlib, subprocess, json, sys

R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
W = os.path.join(R, "rebuild", "work2b")
P = os.path.join(R, "rebuild", "godot", "modules", "mcp_server", "scripts", "accept_m1.ps1")

raw = io.open(P, "rb").read()
orig_sha = hashlib.sha256(raw).hexdigest()
bk = os.path.join(W, "accept_m1.ps1.before-repair")
io.open(bk, "wb").write(raw)
print("backup ->", bk)
print("before bytes=%d sha256=%s" % (len(raw), orig_sha))

txt = raw.decode("utf-8")
eol = "\r\n" if "\r\n" in txt else "\n"
lines = txt.replace("\r\n", "\n").split("\n")
print("lines=%d eol=%r" % (len(lines), eol))

MODE = sys.argv[1] if len(sys.argv) > 1 else "cut1"

if MODE == "cut1":
    # 1) drop the phantom '}' at line 644 (1-based) that closes an earlier case
    del lines[643]
    # 2) drop the duplicated tail copy (lines 976..1083 of the pre-cut file -> now 975..1082)
    del lines[974:1082]
elif MODE == "cut2":
    del lines[643]
    del lines[974:1082]
    # also drop the displaced guard duplicate at 876..895 (now shifted by 109 -> 767..786)
    del lines[766:786]

new = eol.join(lines)
if eol == "\r\n":
    new = new
io.open(P, "wb").write(new.encode("utf-8"))
after = io.open(P, "rb").read()
print("after bytes=%d sha256=%s lines=%d" % (len(after), hashlib.sha256(after).hexdigest(), len(lines)))

ps = r"""
param([string]$F)
$t=$null; $e=$null
[void][System.Management.Automation.Language.Parser]::ParseFile($F,[ref]$t,[ref]$e)
if ($e) { foreach ($x in $e) { Write-Output ($x.ErrorId + ':' + $x.Message + '@' + $x.Extent.StartLineNumber) } } else { Write-Output 'CLEAN' }
"""
pf = os.path.join(W, "one_parse.ps1")
io.open(pf, "w", encoding="ascii", newline="\r\n").write(ps)
p = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", pf, "-F", P],
                   capture_output=True, text=True)
print("PARSE:", p.stdout.strip())
print(p.stderr.strip()[:500])
