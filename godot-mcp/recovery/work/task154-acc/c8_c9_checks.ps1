# TASK-154 acceptance: C8 encoding + C9 prohibited-zone self-check
$eng = 'F:\moonbit-hof-rs\godot-mcp\godot'
$outer = 'F:\moonbit-hof-rs'
$acc = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task154-acc'

Write-Host '=== C8a: encoding of the two edited scripts (bytes / BOM / non-ASCII) ==='
foreach ($n in @('mcp029_clear_default_evidence.ps1','mcp032_d3_d4_d6_evidence.ps1')) {
    $p = Join-Path $eng "modules\mcp_server\scripts\$n"
    $b = [IO.File]::ReadAllBytes($p)
    $bom = ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF)
    $nonAscii = 0
    foreach ($x in $b) { if ($x -gt 127) { $nonAscii++ } }
    $crlf = 0; for ($i=0; $i -lt $b.Length-1; $i++) { if ($b[$i] -eq 13) { $crlf++ } }
    Write-Host ("  {0}: bytes={1} BOM={2} non-ASCII bytes={3} CR count={4}" -f $n, $b.Length, $bom, $nonAscii, $crlf)
    $i = 0
    foreach ($line in [IO.File]::ReadAllLines($p)) {
        $i++
        if ($line -match '\[char\]0x') { Write-Host ("     L{0}: isComment={1} : {2}" -f $i, ($line.TrimStart().StartsWith('#')), $line.Trim()) }
    }
}

Write-Host ''
Write-Host '=== C9a: engine origin / push state ==='
& git -C $eng rev-parse HEAD
& git -C $eng rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild
& git -C $eng rev-list --left-right --count refs/remotes/origin/feature/mcp-server-module-rebuild...HEAD
& git -C $eng status --porcelain
Write-Host ("engine status lines = {0}" -f @(& git -C $eng status --porcelain).Count)
Write-Host ("outer status lines  = {0}" -f @(& git -C $outer status --porcelain).Count)
& git -C $outer status --porcelain | Select-Object -First 20

Write-Host ''
Write-Host '=== C9b: engine commits (author/commit dates) ==='
& git -C $eng log -4 --format='%h %ad %cd %s' --date=iso
Write-Host ("machine now = {0}  tz = {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'), (Get-TimeZone).Id)

Write-Host ''
Write-Host '=== C9c: hof-rs side: HEAD, tracked changes, fixture ==='
& git -C $outer rev-parse --short HEAD
Write-Host '--- porcelain (all) ---'
& git -C $outer status --porcelain
Write-Host '--- tracked-file diff names (excludes untracked) ---'
& git -C $outer diff --name-only
& git -C $outer diff --cached --name-only
$fx = Join-Path $outer 'tests\fixtures\mcp\tools_list.json'
$fb = [IO.File]::ReadAllBytes($fx)
$fsha = (Get-FileHash -Algorithm SHA256 -Path $fx).Hash.ToLower()
Write-Host ("fixture exists={0} bytes={1} sha256={2}" -f (Test-Path $fx), $fb.Length, $fsha)
Write-Host ("fixture blob = {0}" -f ((& git -C $outer hash-object -- $fx) -join ''))
Write-Host ("fixture HEAD blob = {0}" -f ((& git -C $outer rev-parse 'HEAD:tests/fixtures/mcp/tools_list.json') -join ''))

Write-Host ''
Write-Host '=== C9d: provenance of the historical _meta field / commit 54200f0d77 ==='
Write-Host '--- which repo has 54200f0d77 ? ---'
Write-Host ("engine: {0}" -f ((& git -C $eng cat-file -t 54200f0d77 2>&1) -join ''))
Write-Host ("outer : {0}" -f ((& git -C $outer cat-file -t 54200f0d77 2>&1) -join ''))
& git -C $outer log -1 --format='%h %ad %cd %s' --date=iso 54200f0d77
Write-Host '--- does the frozen artifact really carry the hof-rs path in _meta.generated_from ? ---'
$art = Join-Path $eng 'modules\mcp_server\docs\tools_list.renamed.json'
$txt = [IO.File]::ReadAllText($art)
$idx = $txt.IndexOf('generated_from')
Write-Host ("_meta.generated_from excerpt: {0}" -f $txt.Substring([Math]::Max(0,$idx-40), [Math]::Min(220, $txt.Length-[Math]::Max(0,$idx-40))))
Write-Host '--- git log -S for that string in the artifact ---'
& git -C $eng log --oneline -S 'tests/fixtures/mcp/tools_list.json' -- modules/mcp_server/docs/tools_list.renamed.json
Write-Host '--- blob of the artifact at 54200f0d77 (if present) and at HEAD~4..HEAD ---'
foreach ($rev in @('HEAD~4','HEAD~3','HEAD~2','HEAD~1','HEAD')) {
    $bl = (& git -C $eng rev-parse ("{0}:modules/mcp_server/docs/tools_list.renamed.json" -f $rev) 2>&1) -join ''
    Write-Host ("  {0} -> {1}" -f $rev, $bl)
}

Write-Host ''
Write-Host '=== C9e: dependencies / new files in the batch ==='
& git -C $eng diff --name-status 28432f859f..HEAD
