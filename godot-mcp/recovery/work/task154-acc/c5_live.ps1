# TASK-154 acceptance: C5-live - reproduce the two content-level reds.
# Uses only ports 9888/9889. Never touches 9877.
$eng = 'F:\moonbit-hof-rs\godot-mcp\godot'
$acc = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task154-acc'
$ps  = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

function Show-Ports([string]$when) {
    $rows = @(netstat -ano -p TCP | Select-String 'LISTENING' | Where-Object { $_.Line -match ':98(7\d|8\d)\s' })
    Write-Host ("=== LISTENING on 9870..9889 {0}: {1} row(s) ===" -f $when, $rows.Count)
    foreach ($r in $rows) { Write-Host ("   {0}" -f $r.Line.Trim()) }
}

Show-Ports 'BEFORE'

Write-Host ''
Write-Host '################ 1. mcp029 UNMODIFIED, live ################'
$sw = [Diagnostics.Stopwatch]::StartNew()
$out = & $ps -NoProfile -ExecutionPolicy Bypass -File "$eng\modules\mcp_server\scripts\mcp029_clear_default_evidence.ps1" -OutRoot "$acc\live-029" 2>&1
$code = $LASTEXITCODE
$sw.Stop()
Write-Host ("EXITCODE = {0}  wall = {1:N1}s" -f $code, $sw.Elapsed.TotalSeconds)
$out | ForEach-Object { Write-Host "  $_" }
$out | Set-Content -Encoding UTF8 "$acc\c5_live_029.out.txt"
Show-Ports 'AFTER mcp029'

Write-Host ''
Write-Host '################ 2. mcp032 with ONLY the 6 brace pairs doubled (temporary copy) ################'
$orig = Join-Path $eng 'modules\mcp_server\scripts\mcp032_d3_d4_d6_evidence.ps1'
$probe = Join-Path $eng 'modules\mcp_server\scripts\zz_acc_probe_mcp032_tmp.ps1'
if (Test-Path $probe) { Remove-Item -Force $probe }
$txt = [IO.File]::ReadAllText($orig)
$pairs = @(
    @("hand-built {'Material','material'}", "hand-built {{'Material','material'}}"),
    @("{prefix:'application/config/name'}", "{{prefix:'application/config/name'}}"),
    @("{filter:...}", "{{filter:...}}"),
    @("{prefix, filter}", "{{prefix, filter}}"),
    @("{bogus:1}", "{{bogus:1}}"),
    @("{include_default:true}", "{{include_default:true}}")
)
foreach ($p in $pairs) {
    if ($txt -notmatch [regex]::Escape($p[0])) { Write-Host ("  PATTERN NOT FOUND: {0}" -f $p[0]) }
    $txt = $txt.Replace($p[0], $p[1])
}
[IO.File]::WriteAllText($probe, $txt, (New-Object Text.UTF8Encoding($false)))
Write-Host ("probe copy = {0}" -f $probe)
$d = @(& git -C $eng diff --no-index --stat -- $orig $probe)
Write-Host '--- diff --no-index --stat (probe vs committed) ---'
$d | ForEach-Object { Write-Host "  $_" }
# show that the ONLY textual difference is the six brace pairs
$ob = [IO.File]::ReadAllLines($orig); $pb = [IO.File]::ReadAllLines($probe)
Write-Host ("line counts: orig={0} probe={1}" -f $ob.Count, $pb.Count)
$diffLines = 0
for ($i = 0; $i -lt [Math]::Max($ob.Count, $pb.Count); $i++) {
    if ($ob[$i] -cne $pb[$i]) { $diffLines++; Write-Host ("  L{0} differs:" -f ($i+1)); Write-Host ("    orig : {0}" -f $ob[$i]); Write-Host ("    probe: {0}" -f $pb[$i]) }
}
Write-Host ("differing lines = {0}" -f $diffLines)

$sw = [Diagnostics.Stopwatch]::StartNew()
$out2 = & $ps -NoProfile -ExecutionPolicy Bypass -File $probe -OutRoot "$acc\live-032-probe" 2>&1
$code2 = $LASTEXITCODE
$sw.Stop()
Write-Host ("EXITCODE = {0}  wall = {1:N1}s" -f $code2, $sw.Elapsed.TotalSeconds)
$out2 | ForEach-Object { Write-Host "  $_" }
$out2 | Set-Content -Encoding UTF8 "$acc\c5_live_032probe.out.txt"

Write-Host ''
Write-Host '################ 3. cleanup + cleanliness proof ################'
Remove-Item -Force $probe
Write-Host ("probe removed = {0}" -f (-not (Test-Path $probe)))
Write-Host ("git status --porcelain lines in engine repo = {0}" -f @(& git -C $eng status --porcelain).Count)
& git -C $eng status --porcelain
Write-Host '--- git diff --stat (whole repo) ---'
& git -C $eng diff --stat
Show-Ports 'FINAL'
Write-Host '--- listeners on 9888/9889 specifically ---'
@(netstat -ano -p TCP | Select-String 'LISTENING' | Where-Object { $_.Line -match ':9888\s|:9889\s' }).Count
