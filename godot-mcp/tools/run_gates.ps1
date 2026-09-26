param(
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp',
  [string]$Tag = '',
  [string]$VersionText = '',
  [string]$OutDir = '',
  [string]$Anchor = '',
  [string]$VersionBinary = '',
  [switch]$RunGates,
  [switch]$PreflightOnly
)
# run_gates.ps1 -- the ten gates, each in its own cmd.exe child (iron rule 3),
# each with its own stdout/stderr pair (iron rule 1: Start-Process, never a shell
# redirect), and the exit code echoed INSIDE the child so it survives whatever
# PowerShell 5.1 does with a redirected child's ExitCode.
#
# The command set and the order are the TASK-089/TASK-090 ones, unchanged; only
# the working directory moved (H:\rebuild\godot -> godot-mcp\godot, TASK-091 D137).
#
# TASK-099 (B): a PREFLIGHT in front of the ten gates. The gates only ever mean
# "this change did not break anything that was working"; when the engine repo has
# not moved a single compile input since the binary was built, running all ten
# buys no information and costs a full pass. The preflight therefore asks the
# module's own anchor judge (modules\mcp_server\scripts\check_engine_anchor.ps1,
# dot-sourced -- one classifier, not a second copy of the whitelist) what the
# diff between the built binary's self-reported anchor and HEAD contains:
#
#   * nothing to compile (ANCHOR_EQUAL with a clean tree, or
#     ANCHOR_STRUCTURAL_EQUIVALENT) -> print the verdict, the reason and the
#     non-compiling file list, write it to summary.txt, exit 0. No gate is run
#     and nothing is rebuilt, because there is nothing whose compiled behaviour
#     could have changed.
#   * any compile input -> the preflight says so and the ten gates run exactly as
#     they did before (`-RunGates` forces that path unconditionally).
#
# The anchor is the built binary's OWN `--version` unless the caller overrides it
# with `-VersionText` (the old explicit spelling, kept) or `-Anchor`. The old
# hard-coded default (`4.8.dev.mono.custom_build.8604fcf9e`) was the TASK-090
# anchor and went stale on every later commit (ledger G-1); gate 9 now judges the
# binary that is actually on disk.
$ErrorActionPreference = 'Stop'
$engine = Join-Path $Root 'godot'
if (-not (Test-Path -LiteralPath $engine)) { throw "engine root not found: $engine" }
if (-not $Tag) { $Tag = 'task091_' + (Get-Date -Format 'yyyyMMdd-HHmmss') }
if (-not $OutDir) { $OutDir = Join-Path $Root ("runs\gates\{0}" -f $Tag) }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

if (-not $VersionBinary) { $VersionBinary = Join-Path $engine 'bin\godot.windows.editor.x86_64.mono.console.exe' }
$LegacyVersionText = '4.8.dev.mono.custom_build.8604fcf9e'

# --- small helpers ------------------------------------------------------------
function Invoke-GitLines([string]$Repo, [string[]]$GitArgs) {
  $old = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  $lines = @()
  $code = 0
  try {
    $lines = @(& git -C $Repo @GitArgs 2>$null)
    $code = [int]$LASTEXITCODE
  } catch {
    $code = -1
    $lines = @()
  } finally {
    $ErrorActionPreference = $old
  }
  return [pscustomobject]@{ ExitCode = $code; Lines = @($lines) }
}

# The version string the binary on disk reports, read through a generated .cmd
# (iron rule 1: Start-Process owns the handles; iron rule 3: cmd launches it).
function Get-BinaryVersionText([string]$Exe) {
  if (-not (Test-Path -LiteralPath $Exe)) { return '' }
  $out = Join-Path $OutDir 'preflight-version.stdout.txt'
  $err = Join-Path $OutDir 'preflight-version.stderr.txt'
  $bat = Join-Path $OutDir 'preflight-version.cmd'
  $batch = @('@echo off', ('"{0}" --version' -f $Exe), 'echo VERSION_EXIT=%ERRORLEVEL%')
  Set-Content -LiteralPath $bat -Value $batch -Encoding ASCII
  $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $bat -WorkingDirectory $engine `
        -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -Wait -PassThru
  if (-not (Test-Path -LiteralPath $out)) { return '' }
  foreach ($line in (Get-Content -LiteralPath $out)) {
    $t = ([string]$line).Trim()
    if ($t.Length -eq 0) { continue }
    if ($t -match '^VERSION_EXIT=') { continue }
    return $t
  }
  return ''
}

# Working-tree paths (modified / staged / untracked), with `git status --porcelain`
# shapes normalised to plain paths.
function Get-WorkingTreePaths([string]$Repo) {
  $res = Invoke-GitLines -Repo $Repo -GitArgs @('status', '--porcelain', '--untracked-files=all')
  $paths = New-Object System.Collections.Generic.List[string]
  if ($res.ExitCode -ne 0) { return @{ Ok = $false; Paths = @() } }
  foreach ($raw in @($res.Lines)) {
    $line = [string]$raw
    if ($line.Length -lt 4) { continue }
    $path = $line.Substring(3).Trim()
    if ($path -match ' -> ') { $path = ($path -split ' -> ')[-1].Trim() }
    $path = $path.Trim('"')
    if ($path.Length -gt 0) { $paths.Add($path) | Out-Null }
  }
  return @{ Ok = $true; Paths = @($paths.ToArray()) }
}

# --- the anchor judge (single source of truth for the classification) --------
$judge = Join-Path $engine 'modules\mcp_server\scripts\check_engine_anchor.ps1'
$judgeOk = Test-Path -LiteralPath $judge
if ($judgeOk) { . $judge }

# --- resolve the anchor the binary reports -----------------------------------
$resolvedVersionText = $VersionText
if ([string]::IsNullOrWhiteSpace($resolvedVersionText)) {
  if (-not [string]::IsNullOrWhiteSpace($Anchor)) {
    $resolvedVersionText = '4.8.dev.mono.custom_build.' + $Anchor.Trim()
  } else {
    $auto = Get-BinaryVersionText -Exe $VersionBinary
    if ([string]::IsNullOrWhiteSpace($auto)) {
      Write-Host ('GATES_PREFLIGHT WARNING=could not read --version from {0}; falling back to the historical default' -f $VersionBinary)
      $resolvedVersionText = $LegacyVersionText
    } else {
      $resolvedVersionText = $auto
    }
  }
}

# --- classify ----------------------------------------------------------------
$verdict = $null
$skipReason = ''
$runReason = ''
$nonCompiling = New-Object System.Collections.Generic.List[string]
$redWorking = New-Object System.Collections.Generic.List[string]
$treeSafe = New-Object System.Collections.Generic.List[string]
$treeReadable = $true

if (-not $judgeOk) {
  $runReason = ('the anchor judge is missing at {0}; the closure cannot be proven' -f $judge)
} else {
  $verdict = Get-McpEngineAnchorVerdict -VersionText $resolvedVersionText -RepoRoot $engine
  # the non-compiling files of the committed range (safe by the judge's whitelist)
  foreach ($f in @($verdict.SafeFiles)) { $nonCompiling.Add([string]$f) | Out-Null }

  $tree = Get-WorkingTreePaths -Repo $engine
  if (-not $tree.Ok) {
    $treeReadable = $false
  } else {
    foreach ($p in @($tree.Paths)) {
      if ((Get-McpAnchorFileKind -RelativePath $p) -ne 'SAFE') { $redWorking.Add($p) | Out-Null }
      else { $treeSafe.Add($p) | Out-Null; $nonCompiling.Add($p) | Out-Null }
    }
  }

  if ($RunGates) {
    $runReason = '-RunGates was given: the caller asked for the ten gates unconditionally'
  } elseif (-not $treeReadable) {
    $runReason = 'git status could not be read for the engine working tree; the closure cannot be proven'
  } elseif ($redWorking.Count -gt 0) {
    $runReason = ('the engine working tree carries {0} compile input(s) that are not in any built binary' -f $redWorking.Count)
  } elseif (-not $verdict.Ok) {
    $runReason = ('the anchor judge returned {0}: {1}' -f $verdict.Verdict, $verdict.Reason)
  } else {
    $skipReason = $verdict.Reason
  }
}

# --- report the preflight ----------------------------------------------------
function Write-PreflightSummary([string[]]$Lines) {
  $summaryPath = Join-Path $OutDir 'summary.txt'
  [IO.File]::WriteAllLines($summaryPath, $Lines)
  foreach ($l in $Lines) { Write-Host $l }
  Write-Host ('summary=' + $summaryPath)
}

$verdictName = 'ANCHOR_UNKNOWN'
if ($verdict) { $verdictName = $verdict.Verdict }
$headShown = '<unresolved>'
if ($verdict -and -not [string]::IsNullOrWhiteSpace($verdict.Head)) { $headShown = $verdict.Head }
$anchorShown = '<unresolved>'
if ($verdict -and -not [string]::IsNullOrWhiteSpace($verdict.Anchor)) { $anchorShown = $verdict.Anchor }

$pre = New-Object System.Collections.Generic.List[string]
$pre.Add(('GATES_PREFLIGHT RUNNER=tools\run_gates.ps1 tag={0}' -f $Tag))
$pre.Add(('GATES_PREFLIGHT VERSION_TEXT={0}' -f $resolvedVersionText))
$pre.Add(('GATES_PREFLIGHT ANCHOR={0} HEAD={1} ANCHOR_REPORTED={2}' -f $anchorShown, $headShown, $(if ($verdict) { $verdict.AnchorReported } else { '<none>' })))
$pre.Add(('GATES_PREFLIGHT WORKING_TREE_RED={0} WORKING_TREE_SAFE={1} COMMITTED_DIFF_SAFE={2}' -f $redWorking.Count, $treeSafe.Count, $(if ($verdict) { $verdict.SafeCount } else { 0 })))

if ($skipReason -ne '') {
  $pre.Add('GATES_PREFLIGHT VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT')
  $pre.Add(('GATES_PREFLIGHT REASON="{0}"' -f $skipReason))
  $pre.Add(('GATES_PREFLIGHT NONCOMPILING_COUNT={0}' -f $nonCompiling.Count))
  foreach ($f in @($nonCompiling.ToArray())) { $pre.Add(('GATES_PREFLIGHT NONCOMPILING {0}' -f $f)) }
  $pre.Add('GATES_PREFLIGHT RESULT=SKIP_REBUILD')
  $pre.Add('GATES_SKIPPED=1')
  $pre.Add('GATES_PREFLIGHT EXPLAIN=the diff between the built binary anchor and HEAD contains no compile input, so no compiled behaviour can have changed; the ten gates would report on the same binary that already passed')
  Write-PreflightSummary -Lines $pre.ToArray()
  exit 0
}

$pre.Add('GATES_PREFLIGHT VERDICT=RUN_GATES')
$pre.Add(('GATES_PREFLIGHT REASON="{0}"' -f $runReason))
$pre.Add(('GATES_PREFLIGHT RED_COUNT={0}' -f $redWorking.Count))
$pre.Add(('GATES_PREFLIGHT SAFE_COUNT={0}' -f $nonCompiling.Count))
if ($verdict) { $pre.Add('GATES_PREFLIGHT ANCHOR_SUMMARY ' + $verdict.Summary) }
$pre.Add('GATES_SKIPPED=0')

if ($PreflightOnly) {
  $pre.Add('GATES_PREFLIGHT RESULT=PREFLIGHT_ONLY')
  Write-PreflightSummary -Lines $pre.ToArray()
  exit 0
}
foreach ($l in $pre.ToArray()) { Write-Host $l }

# --- the ten gates -----------------------------------------------------------
$commands = @(
  'bin\godot.windows.editor.x86_64.mono.console.exe --headless --test --test-case=[MCPServer]*',
  'bin\godot.windows.editor.x86_64.mono.console.exe --headless --test',
  'python modules\mcp_server\docs\scripts\check_tool_groups.py',
  'powershell -NoProfile -ExecutionPolicy Bypass -File modules\mcp_server\scripts\check_contract_subset.ps1',
  'python modules\mcp_server\docs\scripts\check_rename_map.py',
  'python modules\mcp_server\scripts\check_tautologies.py',
  'python modules\mcp_server\scripts\check_exit_propagation.py --probes',
  'python modules\mcp_server\scripts\check_hardcoded_counts.py',
  ('powershell -NoProfile -ExecutionPolicy Bypass -File modules\mcp_server\scripts\check_engine_anchor.ps1 -VersionText ' + $resolvedVersionText),
  'powershell -NoProfile -ExecutionPolicy Bypass -File modules\mcp_server\scripts\accept_m1.ps1'
)

$summary = New-Object System.Collections.Generic.List[string]
foreach ($l in $pre.ToArray()) { $summary.Add($l) }
$i = 0
foreach ($cmd in $commands) {
  $i++
  $name = ('g{0:d2}' -f $i)
  $out = Join-Path $OutDir ($name + '.stdout.txt')
  $err = Join-Path $OutDir ($name + '.stderr.txt')
  # TASK-092: the exit code marker is expanded with **delayed** expansion
  # (`cmd /v:on` + `!ERRORLEVEL!`). `%ERRORLEVEL%` is expanded when cmd parses the
  # whole line, i.e. *before* the command runs, so the TASK-089..091 spelling
  # echoed whatever the error level had been on entry - a marker that cannot
  # report a failure. The commands, their order and the output layout are
  # unchanged; only the marker is now able to be non-zero.
  $wrapped = ($cmd + ' & echo GATE_EXIT=!ERRORLEVEL!')
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  # TASK-092: `-Wait` is not used either. On this machine it hung forever on a
  # build whose child had already exited (`Start-Process -Wait` waits for every
  # process sharing the redirected handles); the gate runner polls the direct
  # child instead, which `cmd /c` cannot outlive.
  $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/v:on', '/c', $wrapped -WorkingDirectory $engine `
        -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -PassThru
  $deadline = (Get-Date).AddMinutes(10)
  while (-not $p.HasExited) {
    if ((Get-Date) -gt $deadline) { throw "gate $name timed out: $cmd" }
    Start-Sleep -Milliseconds 500
  }
  Start-Sleep -Seconds 1
  $sw.Stop()
  $code = ''
  if (Test-Path -LiteralPath $out) {
    $m = Select-String -LiteralPath $out -Pattern 'GATE_EXIT=(-?\d+)' | Select-Object -Last 1
    if ($m) { $code = $m.Matches[0].Groups[1].Value }
  }
  $line = ('{0} exit={1} wall={2:N1}s cmd= {3}' -f $name, $code, $sw.Elapsed.TotalSeconds, $cmd)
  Write-Host $line
  $summary.Add($line)
  $tail = @()
  if (Test-Path -LiteralPath $out) { $tail += (Get-Content -LiteralPath $out -Tail 16) }
  if (Test-Path -LiteralPath $err) { $e = Get-Content -LiteralPath $err -Tail 6; if ($e) { $tail += '  [stderr]'; $tail += $e } }
  foreach ($t in $tail) { Write-Host ('    | ' + $t); $summary.Add('    | ' + $t) }
}
$summaryPath = Join-Path $OutDir 'summary.txt'
[IO.File]::WriteAllLines($summaryPath, $summary.ToArray())
Write-Host ('summary=' + $summaryPath)
