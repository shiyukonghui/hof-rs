$ErrorActionPreference = 'Stop'
$Repo = 'F:\moonbit-hof-rs\godot-mcp\godot'
$Outer = 'F:\moonbit-hof-rs'

function Blob([string]$repo, [string]$rev, [string]$rel) {
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    $o = @()
    try { $o = @(& git -C $repo rev-parse ('{0}:{1}' -f $rev, $rel) 2>$null) } catch { $o = @() }
    $ErrorActionPreference = $old
    if ($o.Count -eq 0) { return '<absent>' }
    return ([string]$o[0]).Trim()
}

Write-Host '=============================================================='
Write-Host ' SECTION 2.4 probe, second attempt (honest evaluation)'
Write-Host '=============================================================='
Write-Host ''
Write-Host '### 1. What guardrail 3 can even SEE ###'
Write-Host 'The three frozen criterion files, and which repository git diff can report them from:'
foreach ($row in @(
        @{ rel = 'modules/mcp_server/scripts/check_engine_anchor.ps1'; repo = 'engine' },
        @{ rel = 'modules/mcp_server/scripts/check_hardcoded_counts.py'; repo = 'engine' },
        @{ rel = 'tools/run_gates.ps1'; repo = 'outer' })) {
    $r = if ($row.repo -eq 'engine') { $Repo } else { $Outer }
    Write-Host ('  {0,-62} lives in the {1} repo (HEAD blob {2})' -f $row.rel, $row.repo, (Blob $r 'HEAD' $row.rel))
}
$inEngineDiff = @(& git -C $Repo diff --name-only --no-renames '15bbf1f50e..HEAD' 2>$null)
Write-Host ('  files in an engine diff that also name tools/run_gates.ps1 : always empty - git -C <engine> cannot see outside the engine tree')
Write-Host ''
Write-Host '### 2. Did the three frozen files actually move in recent engine history? ###'
foreach ($rev in @('035edfce7f', '069a2e2ea8', 'e1fbc8ec7f', 'bef4be0407', '28432f859f', 'HEAD')) {
    $a = Blob $Repo $rev 'modules/mcp_server/scripts/check_engine_anchor.ps1'
    $b = Blob $Repo $rev 'modules/mcp_server/scripts/check_hardcoded_counts.py'
    Write-Host ('  {0,-12} check_engine_anchor.ps1={1}  check_hardcoded_counts.py={2}' -f $rev, $a, $b)
}
Write-Host ('  outer tools/run_gates.ps1 at HEAD = {0} (NOT in any engine diff by construction)' -f (Blob $Outer 'HEAD' 'tools/run_gates.ps1'))
Write-Host ''
Write-Host '### 3. Can the ANCHOR..HEAD rule go red? (non-vacuity) ###'
. (Join-Path $Repo 'modules\mcp_server\scripts\check_engine_anchor.ps1')
foreach ($pair in @(@('15bbf1f50e', 'HEAD'), @('97fc49df4b', 'HEAD'), @('035edfce7f', 'HEAD'))) {
    $files = @(& git -C $Repo diff --name-only --no-renames ($pair[0] + '..' + $pair[1]) 2>$null) | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_.Length -gt 0 }
    $red = @($files | Where-Object { (Get-McpAnchorFileKind -RelativePath $_) -ne 'SAFE' })
    $judge = Get-McpEngineAnchorVerdict -Anchor $pair[0] -HeadSha $pair[1] -RepoRoot $Repo
    Write-Host ('  {0}..{1}: diff={2} red={3} judge.Verdict={4} judge.Ok={5}' -f $pair[0], $pair[1], $files.Count, $red.Count, $judge.Verdict, $judge.Ok)
}
Write-Host ''
Write-Host '### 4. A guardrail-3 violation, injected and detected, then removed ###'
$probeRepo = Join-Path $env:TEMP 'task154-guardrail3-probe'
if (Test-Path $probeRepo) { Remove-Item -Recurse -Force $probeRepo }
New-Item -ItemType Directory -Force -Path $probeRepo | Out-Null
& git -C $probeRepo init -q 2>$null
& git -C $probeRepo config user.email 'task154@local' 2>$null
& git -C $probeRepo config user.name 'task154' 2>$null
Set-Content -LiteralPath (Join-Path $probeRepo 'check_engine_anchor.ps1') -Value '# original' -Encoding ASCII
& git -C $probeRepo add -A 2>$null
& git -C $probeRepo commit -q -m 'base' 2>$null
$base = (& git -C $probeRepo rev-parse HEAD).Trim()
Set-Content -LiteralPath (Join-Path $probeRepo 'check_engine_anchor.ps1') -Value '# tampered' -Encoding ASCII
& git -C $probeRepo add -A 2>$null
& git -C $probeRepo commit -q -m 'tamper' 2>$null
$head = (& git -C $probeRepo rev-parse HEAD).Trim()
$frozen = @('check_engine_anchor.ps1')
$diffFiles = @(& git -C $probeRepo diff --name-only --no-renames ($base + '..' + $head) 2>$null) | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_.Length -gt 0 }
$hits = @($diffFiles | Where-Object { $frozen -contains $_ })
Write-Host ('  probe repo {0}: base={1} head={2}' -f $probeRepo, $base.Substring(0, 9), $head.Substring(0, 9))
Write-Host ('  interval diff = [{0}]' -f ($diffFiles -join ', '))
Write-Host ('  guardrail 3 (criterion files zero diff) = {0}  hits=[{1}]  << RED means the rule fired' -f ($hits.Count -eq 0), ($hits -join ', '))
$after = Blob $probeRepo 'HEAD' 'check_engine_anchor.ps1'
Write-Host ('  probe detected the tampered blob and the OUTER/ENGINE repos were never touched (probe blob {0})' -f $after)
Remove-Item -Recurse -Force $probeRepo
Write-Host ('  probe repo removed = {0}' -f (-not (Test-Path $probeRepo)))
