import io, json, os, re, sys, subprocess

R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
G = os.path.join(R, "rebuild", "godot")
OUT = os.path.join(R, "rebuild", "work2b")

PS = r"""
param([string]$Root, [string]$OutFile)
$ErrorActionPreference = 'Stop'
$rows = @()
$files = Get-ChildItem -Path $Root -Recurse -File -Include *.ps1 -ErrorAction SilentlyContinue
foreach ($f in $files) {
    $errs = @()
    $tokens = $null
    $parseErrors = $null
    try {
        [void][System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$tokens, [ref]$parseErrors)
        if ($parseErrors) { foreach ($e in $parseErrors) { $errs += ($e.ErrorId + ':' + $e.Message + '@' + $e.Extent.StartLineNumber) } }
    } catch {
        $errs += ('EXCEPTION:' + $_.Exception.Message)
    }
    $rel = $f.FullName.Substring($Root.Length).TrimStart('\')
    $rows += [pscustomobject]@{ rel = $rel; bytes = $f.Length; parseErrors = $errs.Count; errors = $errs }
}
[IO.File]::WriteAllText($OutFile, ($rows | ConvertTo-Json -Depth 6), (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("ps1 scanned=" + $rows.Count + " withErrors=" + (@($rows | Where-Object { $_.parseErrors -gt 0 })).Count)
"""

def run_ps1():
    pf = os.path.join(OUT, "parse_ps1.ps1")
    io.open(pf, "w", encoding="ascii", newline="\r\n").write(PS)
    out = os.path.join(OUT, "parse-ps1-2b.json")
    p = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", pf,
                        "-Root", G, "-OutFile", out], capture_output=True, text=True)
    print(p.stdout.strip(), p.stderr.strip()[:2000])
    return out

PY = r"""
import io, os, sys, json, ast
R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
G = os.path.join(R, "rebuild", "godot")
rows = []
for root, dirs, files in os.walk(G):
    for fn in files:
        if not fn.endswith(".py"):
            continue
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, G)
        try:
            src = io.open(p, "rb").read()
            ast.parse(src.decode("utf-8", "replace"), filename=rel)
            rows.append({"rel": rel, "errors": 0, "first": ""})
        except SyntaxError as e:
            rows.append({"rel": rel, "errors": 1, "first": "%s:%s" % (e.lineno, e.msg)})
        except Exception as e:
            rows.append({"rel": rel, "errors": 1, "first": "EXC:" + str(e)})
io.open(os.path.join(R, "rebuild", "work2b", "parse-py-2b.json"), "w", encoding="utf-8", newline="\n").write(
    json.dumps(rows, ensure_ascii=False, indent=1))
bad = [r for r in rows if r["errors"]]
print("py scanned=%d withErrors=%d" % (len(rows), len(bad)))
for r in bad:
    print(" ", r["rel"], r["first"])
"""

if __name__ == "__main__":
    out = run_ps1()
    d = json.load(io.open(out, encoding="utf-8"))
    bad = [x for x in d if x["parseErrors"] > 0]
    print("PS1 files with errors:", len(bad))
    for x in bad:
        print(" ", x["parseErrors"], x["bytes"], x["rel"], "|", x["errors"][0] if x["errors"] else "")
    io.open(os.path.join(OUT, "parse_py_run.py"), "w", encoding="utf-8", newline="\n").write(PY)
    os.system('python "%s"' % os.path.join(OUT, "parse_py_run.py"))
