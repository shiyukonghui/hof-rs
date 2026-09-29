# =============================================================================
#  run_gates_task151.ps1 -- TASK-151: the module's ten gates (g01..g10).
#
#  This mirrors `F:\moonbit-hof-rs\godot-mcp\tools\run_gates.ps1` exactly - same
#  ten commands, same order, same per-gate stdout/stderr pair, same
#  `GATE_EXIT=!ERRORLEVEL!` marker expanded with delayed expansion - with ONE
#  recorded deviation:
#
#    * g01 and g02 (and the `--version` the anchor judge is given for g09) ran on
#      `bin\godot.windows.editor.x86_64.console.exe` instead of the mono variant.
#      The canonical runner uses `godot.windows.editor.x86_64.mono.console.exe`,
#      but `bin\godot.windows.editor.x86_64.mono.exe` is HELD OPEN by the
#      dispatcher's own running editor (PID 108432 on port 9877), so the mono
#      variant cannot be relinked while that process lives - scons fails with
#      `bin\godot.windows.editor.x86_64.mono.exe: Access is denied` after every
#      object has compiled. Running g01/g02 on the stale mono binary would be a
#      **false green** (it does not contain this task's new case at all), so the
#      plain variant - which is also the binary `accept_m1` (g10) and
#      `check_contract_subset` (g04) already use - is the one judged. The doctest
#      source is the same file for both variants.
#
#  Everything else is byte for byte the canonical command.
#
#  Port discipline: g04/g10 start engines on 9888/9889 and observe 9877; g01/g02
#  run `--test`, which returns from `Main::setup()` before any listener exists.
#  The guard is checked before and after.
# =============================================================================
param(
    [string]$Tag = 'task151',
    [string]$EngineRoot = 'F:\moonbit-hof-rs\godot-mcp\godot',
    [string]$OutRoot = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task151\gates'
)

$ErrorActionPreference = 'Stop'

$OutDir = Join-Path $OutRoot $Tag
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function ListenPids {
    param([int]$Port)
    $c = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($c) { return (@($c | Select-Object -ExpandProperty OwningProcess) | Sort-Object -Unique) }
    return @()
}

function Get-BinaryVersionText {
    param([string]$Exe)
    $out = Join-Path $OutDir 'version-probe.txt'
    & $Exe --version 2>&1 | Set-Content $out -Encoding UTF8
    return (Get-Content $out -TotalCount 1)
}

$plain = Join-Path $EngineRoot 'bin\godot.windows.editor.x86_64.console.exe'
$versionText = Get-BinaryVersionText -Exe $plain
Write-Host ("gates: engine = {0}" -f $plain)
Write-Host ("gates: --version = {0}" -f $versionText)
Write-Host ("gates: 9877 listen pids BEFORE = {0}" -f ((ListenPids 9877) -join ','))

# The canonical ten commands, with the two mono spellings replaced (see the header).
$commands = @(
    'bin\godot.windows.editor.x86_64.console.exe --headless --test --test-case=[MCPServer]*',
    'bin\godot.windows.editor.x86_64.console.exe --headless --test',
    'python modules\mcp_server\docs\scripts\check_tool_groups.py',
    'powershell -NoProfile -ExecutionPolicy Bypass -File modules\mcp_server\scripts\check_contract_subset.ps1',
    'python modules\mcp_server\docs\scripts\check_rename_map.py',
    'python modules\mcp_server\scripts\check_tautologies.py',
    'python modules\mcp_server\scripts\check_exit_propagation.py --probes',
    'python modules\mcp_server\scripts\check_hardcoded_counts.py',
    ('powershell -NoProfile -ExecutionPolicy Bypass -File modules\mcp_server\scripts\check_engine_anchor.ps1 -VersionText ' + $versionText),
    'powershell -NoProfile -ExecutionPolicy Bypass -File modules\mcp_server\scripts\accept_m1.ps1'
)

$summary = New-Object System.Collections.Generic.List[string]
$summary.Add(('GATES_TASK151 RUNNER=recovery\work\task151\run_gates_task151.ps1 tag={0}' -f $Tag))
$summary.Add(('GATES_TASK151 ENGINE={0}' -f $plain))
$summary.Add(('GATES_TASK151 VERSION_TEXT={0}' -f $versionText))
$summary.Add(('GATES_TASK151 DEVIATION=g01/g02/version-probe ran on the plain console binary because the mono binary is held open by the dispatcher editor (PID 108432, port 9877)'))
$summary.Add(('GATES_TASK151 PORT_9877_BEFORE={0}' -f (((ListenPids 9877) -join ','))))
$summary.Add('')

$i = 0
foreach ($cmd in $commands) {
    $i++
    $name = ('g{0:d2}' -f $i)
    $out = Join-Path $OutDir ($name + '.stdout.txt')
    $err = Join-Path $OutDir ($name + '.stderr.txt')
    $wrapped = ($cmd + ' & echo GATE_EXIT=!ERRORLEVEL!')
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/v:on', '/c', $wrapped -WorkingDirectory $EngineRoot `
        -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -PassThru
    $deadline = (Get-Date).AddMinutes(30)
    while (-not $p.HasExited) {
        if ((Get-Date) -gt $deadline) { throw "gate $name timed out: $cmd" }
        Start-Sleep -Milliseconds 500
    }
    Start-Sleep -Seconds 1
    $sw.Stop()
    $code = '<none>'
    if (Test-Path $out) {
        $m = Select-String -LiteralPath $out -Pattern 'GATE_EXIT=(-?\d+)' | Select-Object -Last 1
        if ($m) { $code = $m.Matches[0].Groups[1].Value }
    }
    $line = ('{0} exit={1} wall={2:N1}s cmd= {3}' -f $name, $code, $sw.Elapsed.TotalSeconds, $cmd)
    Write-Host $line
    $summary.Add($line)
    $tail = @()
    if (Test-Path $out) { $tail += (Get-Content -LiteralPath $out -Tail 18) }
    if (Test-Path $err) { $e = Get-Content -LiteralPath $err -Tail 6; if ($e) { $tail += '  [stderr]'; $tail += $e } }
    foreach ($t in $tail) { Write-Host ('    | ' + $t); $summary.Add('    | ' + $t) }
}

$summary.Add('')
$summary.Add(('GATES_TASK151 PORT_9877_AFTER={0}' -f (((ListenPids 9877) -join ','))))
$summary.Add(('GATES_TASK151 PORTS_9888_9889_AFTER={0}/{1}' -f (((ListenPids 9888) -join ',')), (((ListenPids 9889) -join ','))))

$summaryPath = Join-Path $OutDir 'summary.txt'
[IO.File]::WriteAllLines($summaryPath, $summary.ToArray())
Write-Host ('summary=' + $summaryPath)
