param(
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp',
  [string]$Tag = '',
  [string]$VersionText = '4.8.dev.mono.custom_build.8604fcf9e',
  [string]$OutDir = ''
)
# run_gates.ps1 -- the nine gates, each in its own cmd.exe child (iron rule 3),
# each with its own stdout/stderr pair (iron rule 1: Start-Process, never a shell
# redirect), and the exit code echoed INSIDE the child so it survives whatever
# PowerShell 5.1 does with a redirected child's ExitCode.
#
# The command set and the order are the TASK-089/TASK-090 ones, unchanged; only
# the working directory moved (H:\rebuild\godot -> godot-mcp\godot, TASK-091 D137).
$ErrorActionPreference = 'Stop'
$engine = Join-Path $Root 'godot'
if (-not (Test-Path -LiteralPath $engine)) { throw "engine root not found: $engine" }
if (-not $Tag) { $Tag = 'task091_' + (Get-Date -Format 'yyyyMMdd-HHmmss') }
if (-not $OutDir) { $OutDir = Join-Path $Root ("runs\gates\{0}" -f $Tag) }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$commands = @(
  'bin\godot.windows.editor.x86_64.mono.console.exe --headless --test --test-case=[MCPServer]*',
  'bin\godot.windows.editor.x86_64.mono.console.exe --headless --test',
  'python modules\mcp_server\docs\scripts\check_tool_groups.py',
  'powershell -NoProfile -ExecutionPolicy Bypass -File modules\mcp_server\scripts\check_contract_subset.ps1',
  'python modules\mcp_server\docs\scripts\check_rename_map.py',
  'python modules\mcp_server\scripts\check_tautologies.py',
  'python modules\mcp_server\scripts\check_exit_propagation.py --probes',
  'python modules\mcp_server\scripts\check_hardcoded_counts.py',
  ('powershell -NoProfile -ExecutionPolicy Bypass -File modules\mcp_server\scripts\check_engine_anchor.ps1 -VersionText ' + $VersionText),
  'powershell -NoProfile -ExecutionPolicy Bypass -File modules\mcp_server\scripts\accept_m1.ps1'
)

$summary = New-Object System.Collections.Generic.List[string]
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
