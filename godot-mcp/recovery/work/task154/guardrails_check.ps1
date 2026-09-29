$ErrorActionPreference = 'Stop'
$Repo = 'F:\moonbit-hof-rs\godot-mcp\godot'
$env:RUN_GATES_ENGINE_REPO = $Repo

# TASK-154 helper (NOT a deliverable of the engine repo, NOT on any gate path):
# it evaluates the three g09 guardrails as machine-checkable rules over a
# committed interval, so the report can carry reproducible evidence instead of a
# human's word. The anchor judge itself is dot-sourced, never copied.
. (Join-Path $Repo 'modules\mcp_server\scripts\check_engine_anchor.ps1')

$FrozenCriterionFiles = @(
    'modules/mcp_server/scripts/check_engine_anchor.ps1',
    'modules/mcp_server/scripts/check_hardcoded_counts.py',
    'tools/run_gates.ps1'
)

function Get-IntervalDiff([string]$A, [string]$B) {
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $lines = @()
    try { $lines = @(& git -C $Repo diff --name-only --no-renames ($A + '..' + $B) 2>$null) } catch { $lines = @() }
    $ErrorActionPreference = $old
    return @($lines | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_.Length -gt 0 })
}
function Get-IntervalBlobs([string]$A, [string]$B) {
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $lines = @()
    try { $lines = @(& git -C $Repo diff --name-only --no-renames --diff-filter=AM ($A + '..' + $B) 2>$null) } catch { $lines = @() }
    $ErrorActionPreference = $old
    return @($lines | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_.Length -gt 0 })
}

function Test-Guardrails([string]$Anchor, [string]$Head) {
    $files = Get-IntervalDiff -A $Anchor -B $Head
    $g1Red = New-Object System.Collections.Generic.List[string]
    $g1Safe = New-Object System.Collections.Generic.List[string]
    foreach ($f in $files) {
        if ((Get-McpAnchorFileKind -RelativePath $f) -eq 'SAFE') { $g1Safe.Add($f) | Out-Null } else { $g1Red.Add($f) | Out-Null }
    }
    # guardrail 1/2: the interval's diff contains no compile input.
    $g1 = ($g1Red.Count -eq 0)
    # guardrail 3: the three criterion files have ZERO diff in the interval.
    $g3Hits = @($files | Where-Object { $FrozenCriterionFiles -contains $_ })
    $g3 = ($g3Hits.Count -eq 0)
    return [pscustomobject]@{
        anchor = $Anchor; head = $Head
        diff_count = $files.Count
        safe = @($g1Safe.ToArray()); red = @($g1Red.ToArray())
        guardrail1_2_no_compile_input = $g1
        guardrail3_criterion_files_zero_diff = $g3
        guardrail3_hits = $g3Hits
        pass = ($g1 -and $g3)
    }
}

Write-Host '=============================================================='
Write-Host ' TASK-154 section 2.4 probe: the three g09 guardrails as RULES'
Write-Host '=============================================================='

Write-Host ''
Write-Host '### A. the live interval (the real binary anchor .. HEAD) ###'
$engine = Join-Path $Repo 'bin\godot.windows.editor.x86_64.mono.console.exe'
$ver = (& $engine --version) -join ''
$ver = $ver.Trim()
Write-Host ('binary --version = ' + $ver)
$v = Get-McpEngineAnchorVerdict -VersionText $ver -RepoRoot $Repo
Write-Host ('anchor judge: verdict={0} anchor={1} head={2} red_count={3}' -f $v.Verdict, $v.Anchor, $v.Head, $v.RedCount)
$live = Test-Guardrails -Anchor $v.Anchor -Head $v.Head
Write-Host ('  guardrail 1+2 (interval diff contains no compile input) = {0}' -f $live.guardrail1_2_no_compile_input)
Write-Host ('      diff_count={0} safe={1} red=[{2}]' -f $live.diff_count, $live.safe.Count, ($live.red -join ', '))
foreach ($f in $live.safe) { Write-Host ('      SAFE ' + $f) }
Write-Host ('  guardrail 3 (criterion files zero diff) = {0}  hits=[{1}]' -f $live.guardrail3_criterion_files_zero_diff, ($live.guardrail3_hits -join ', '))
foreach ($fc in $FrozenCriterionFiles) { Write-Host ('      frozen ' + $fc + ' in interval diff = ' + ($live.guardrail3_hits -contains $fc)) }
Write-Host ('  LIVE OVERALL = {0}' -f $(if ($live.pass) { 'PASS' } else { 'FAIL' }))

Write-Host ''
Write-Host '### B. non-vacuity: a synthetic interval that MUST go red ###'
$fakeAnchor = '035edfce7f'
Write-Host ('fake anchor = {0} (a real ancestor of HEAD); its interval touches engine sources' -f $fakeAnchor)
$fake = Test-Guardrails -Anchor $fakeAnchor -Head $v.Head
Write-Host ('  guardrail 1+2 = {0}  diff_count={1} red_count={2}' -f $fake.guardrail1_2_no_compile_input, $fake.diff_count, $fake.red.Count)
foreach ($f in $fake.red) { Write-Host ('      RED ' + $f) }
Write-Host ('  guardrail 3 = {0} hits=[{1}]' -f $fake.guardrail3_criterion_files_zero_diff, ($fake.guardrail3_hits -join ', '))
Write-Host ('  SYNTHETIC OVERALL = {0}   << the rule CAN go red' -f $(if ($fake.pass) { 'PASS' } else { 'FAIL' }))

Write-Host ''
Write-Host '### C. non-vacuity for guardrail 3 alone: a range that touches a compile input ###'
$c = Test-Guardrails -Anchor '97fc49df4b' -Head 'bdf654b108'
Write-Host ('97fc49df4b..HEAD: guardrail 1+2 = {0} red=[{1}]' -f $c.guardrail1_2_no_compile_input, ($c.red -join ', '))
Write-Host ('                   guardrail 3 = {0} hits=[{1}]' -f $c.guardrail3_criterion_files_zero_diff, ($c.guardrail3_hits -join ', '))

Write-Host ''
Write-Host '### D. was guardrail 3 ever violated in the recent past? ###'
foreach ($pair in @(@('035edfce7f', '28432f859f'), @('15bbf1f50e', '28432f859f'))) {
    $d = Test-Guardrails -Anchor $pair[0] -Head $pair[1]
    Write-Host ('{0}..{1}: guardrail 1+2 = {2} (red=[{3}]) ; guardrail 3 = {4} (hits=[{5}])' -f `
            $pair[0], $pair[1], $d.guardrail1_2_no_compile_input, ($d.red -join ', '), $d.guardrail3_criterion_files_zero_diff, ($d.guardrail3_hits -join ', '))
}
