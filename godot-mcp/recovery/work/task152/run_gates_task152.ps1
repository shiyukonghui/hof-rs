# =============================================================================
#  run_gates_task152.ps1 -- TASK-152: the ten gates, CANONICAL spelling.
#
#  The command set and order are `F:\moonbit-hof-rs\godot-mcp\tools\run_gates.ps1`
#  (lines 214-225), unchanged, with no substitution of any kind:
#
#    g01  bin\godot.windows.editor.x86_64.mono.console.exe --headless --test --test-case=[MCPServer]*
#    g02  bin\godot.windows.editor.x86_64.mono.console.exe --headless --test
#    g03  python modules\mcp_server\docs\scripts\check_tool_groups.py
#    g04  powershell ... modules\mcp_server\scripts\check_contract_subset.ps1
#    g05  python modules\mcp_server\docs\scripts\check_rename_map.py
#    g06  python modules\mcp_server\scripts\check_tautologies.py
#    g07  python modules\mcp_server\scripts\check_exit_propagation.py --probes
#    g08  python modules\mcp_server\scripts\check_hardcoded_counts.py
#    g09  powershell ... modules\mcp_server\scripts\check_engine_anchor.ps1 -VersionText <mono --version>
#    g10  powershell ... modules\mcp_server\scripts\accept_m1.ps1
#
#  No engine rebuild is performed or needed: TASK-152 changes no compile input
#  (two docs/*.json and one docs/scripts/*.py), so the mono binary already on
#  disk is the one HEAD builds. The binary's own `--version` is read anyway and
#  printed, because the previous batch's lesson is that a binary sha256 is NOT a
#  freshness criterion - `--version` plus the test counts are what is checkable.
#
#  Port discipline: nothing here ever binds or probes 9877. g04 and g10 do their
#  own guarded check of 9877 from inside; this runner only *reads* who is
#  listening, via Get-NetTCPConnection, before and after.
# =============================================================================
param(
    [string]$Tag = 'task152',
    [string]$EngineRoot = 'F:\moonbit-hof-rs\godot-mcp\godot',
    [string]$OutRoot = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task152\gates'
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

$mono = Join-Path $EngineRoot 'bin\godot.windows.editor.x86_64.mono.console.exe'
$out = Join-Path $OutDir 'version-probe.txt'
& $mono --version 2>&1 | Set-Content $out -Encoding UTF8
$versionText = (Get-Content $out -TotalCount 1)
Write-Host ("canonical gates: mono --version = {0}" -f $versionText)

$commands = @(
    'bin\godot.windows.editor.x86_64.mono.console.exe --headless --test --test-case=[MCPServer]*',
    'bin\godot.windows.editor.x86_64.mono.console.exe --headless --test',
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
$summary.Add(('GATES_CANONICAL tag={0}' -f $Tag))
$summary.Add(('GATES_CANONICAL ENGINE_HEAD={0}' -f (& git -C $EngineRoot rev-parse HEAD)))
$summary.Add(('GATES_CANONICAL MONO_VERSION_TEXT={0}' -f $versionText))
$summary.Add(('GATES_CANONICAL PORT_9877_BEFORE={0}' -f (((ListenPids 9877) -join ','))))
$summary.Add(('GATES_CANONICAL PORTS_9888_9889_BEFORE={0}/{1}' -f (((ListenPids 9888) -join ',')), (((ListenPids 9889) -join ','))))
$summary.Add('')

$i = 0
foreach ($cmd in $commands) {
    $i++
    $name = ('g{0:d2}' -f $i)
    $o = Join-Path $OutDir ($name + '.stdout.txt')
    $e = Join-Path $OutDir ($name + '.stderr.txt')
    $wrapped = ($cmd + ' & echo GATE_EXIT=!ERRORLEVEL!')
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/v:on', '/c', $wrapped -WorkingDirectory $EngineRoot `
        -RedirectStandardOutput $o -RedirectStandardError $e -NoNewWindow -PassThru
    $deadline = (Get-Date).AddMinutes(30)
    while (-not $p.HasExited) {
        if ((Get-Date) -gt $deadline) { throw "gate $name timed out: $cmd" }
        Start-Sleep -Milliseconds 500
    }
    Start-Sleep -Seconds 1
    $sw.Stop()
    $code = '<none>'
    if (Test-Path $o) {
        $m = Select-String -LiteralPath $o -Pattern 'GATE_EXIT=(-?\d+)' | Select-Object -Last 1
        if ($m) { $code = $m.Matches[0].Groups[1].Value }
    }
    $line = ('{0} exit={1} wall={2:N1}s cmd= {3}' -f $name, $code, $sw.Elapsed.TotalSeconds, $cmd)
    Write-Host $line
    $summary.Add($line)
    $tail = @()
    if (Test-Path $o) { $tail += (Get-Content -LiteralPath $o -Tail 20) }
    if (Test-Path $e) { $ee = Get-Content -LiteralPath $e -Tail 6; if ($ee) { $tail += '  [stderr]'; $tail += $ee } }
    foreach ($t in $tail) { Write-Host ('    | ' + $t); $summary.Add('    | ' + $t) }
}

$summary.Add('')
$summary.Add(('GATES_CANONICAL PORT_9877_AFTER={0}' -f (((ListenPids 9877) -join ','))))
$summary.Add(('GATES_CANONICAL PORTS_9888_9889_AFTER={0}/{1}' -f (((ListenPids 9888) -join ',')), (((ListenPids 9889) -join ','))))
Write-Host ('port9877_after=' + (((ListenPids 9877) -join ',')))
Write-Host ('ports9888_9889_after=' + (((ListenPids 9888) -join ',')) + '/' + (((ListenPids 9889) -join ',')))

foreach ($bin in @('bin\godot.windows.editor.x86_64.mono.console.exe', 'bin\godot.windows.editor.x86_64.mono.exe',
        'bin\godot.windows.editor.x86_64.console.exe', 'bin\godot.windows.editor.x86_64.exe')) {
    $path = Join-Path $EngineRoot $bin
    if (Test-Path $path) {
        $fi = Get-Item $path
        $sha = (Get-FileHash -Algorithm SHA256 $path).Hash.ToLower()
        $ver = (& $path --version 2>&1 | Select-Object -First 1)
        $line = ('BINARY {0} bytes={1} sha256={2} mtime={3} version={4}' -f $bin, $fi.Length, $sha, $fi.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'), $ver)
        Write-Host $line
        $summary.Add($line)
    }
}

$summaryPath = Join-Path $OutDir 'summary.txt'
[IO.File]::WriteAllLines($summaryPath, $summary.ToArray())
Write-Host ('summary=' + $summaryPath)
