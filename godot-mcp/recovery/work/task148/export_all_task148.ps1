# TASK-148 step B: re-export all 20 C# games to Windows release exe from CURRENT sources.
#
# Invoked from cmd:
#   cmd /c powershell -NoProfile -ExecutionPolicy Bypass -File export_all_task148.ps1
#
# Basis: recovery\work\task109\export_all.ps1 (the TASK-109 recipe).  Three deliberate,
# measured changes, all recorded in TASK-148-REPORT.md:
#
#   (1) output goes to recovery\work\task148\exe\<game>\ instead of dist\exe\<game>\.
#       dist\exe\ still holds the TASK-109 batch; iron rule 2 forbids destroying the
#       previous batch's evidence.
#
#   (2) UseSharedCompilation=false / MSBUILDDISABLENODEREUSE=1 /
#       DOTNET_CLI_USE_MSBUILD_SERVER=0 are exported for every run.
#       Measured on 2026-09-28: with the Roslyn compiler server enabled, `dotnet publish`
#       leaves a persistent VBCSCompiler.exe behind that inherits the engine's console,
#       and the Godot process then NEVER exits after a successful export (observed 120 s
#       and 240 s hangs, and a 7-minute hang).  With the compiler server disabled the same
#       export finishes and exits in ~12 s:
#         DIAG pong     NoShared=False exited=False  seconds=120.4  VBCSCompiler_alive=1
#         DIAG tetris   NoShared=False exited=False  seconds=120.4  VBCSCompiler_alive=1
#         DIAG match3   NoShared=True  exited=True   seconds= 11.7  VBCSCompiler_alive=0
#       The compiler setting does not change what is compiled, only where the compiler
#       process lives.
#
#   (3) the child is driven through System.Diagnostics.ProcessStartInfo with async
#       stdout/stderr reads + WaitForExit(timeout), which yields the real exit code
#       (Start-Process -PassThru returns an empty ExitCode here).
#
# Iron rules honoured here:
#   * no shell redirection - ProcessStartInfo redirects to pipes; the script writes files
#   * unique high port per run (19401..19420); 9877/9888/9889/8080/8081 never touched
#   * game logic / scenes / project configuration are never written to
$ErrorActionPreference = 'Continue'

$Godot    = 'F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe'
$Root     = 'F:\moonbit-hof-rs\godot-mcp'
$Projects = Join-Path $Root 'projects'
$Work     = Join-Path $Root 'recovery\work\task148'
$OutRoot  = Join-Path $Work 'exe'
$Logs     = Join-Path $Work 'logs'

New-Item -ItemType Directory -Force -Path $OutRoot | Out-Null
New-Item -ItemType Directory -Force -Path $Logs | Out-Null

# (2) keep the Roslyn compiler server out of the picture (see header)
$env:UseSharedCompilation          = 'false'
$env:MSBUILDDISABLENODEREUSE       = '1'
$env:DOTNET_CLI_USE_MSBUILD_SERVER = '0'

$Games = @(
  'asteroids','bomberman','breakout','flappy','frogger','game2048','lunarlander',
  'match3','minesweeper','missilecommand','pacman','platformer','pong',
  'puzzlebobble','rtype','snake','sokoban','spaceinvaders','tetris','towerdefense'
)

function Test-PortBusy([int]$Port) {
    $c = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    return ($null -ne $c)
}

function Get-Sha256([string]$Path) {
    if (Test-Path $Path) { return (Get-FileHash $Path -Algorithm SHA256).Hash.ToLower() }
    return ''
}

$results = New-Object System.Collections.ArrayList
$i = 0
foreach ($g in $Games) {
    $i++
    $proj   = Join-Path $Projects $g
    $outDir = Join-Path $OutRoot $g
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    $exe    = Join-Path $outDir "$g.exe"
    $pck    = Join-Path $outDir "$g.pck"
    $stdout = Join-Path $Logs "export-$g.stdout.txt"
    $stderr = Join-Path $Logs "export-$g.stderr.txt"
    $port   = 19400 + $i

    while (Test-PortBusy $port) { $port++ }

    if (Test-Path $exe) { Remove-Item $exe -Force }
    if (Test-Path $pck) { Remove-Item $pck -Force }
    $dataDir = Join-Path $outDir ("data_{0}_windows_x86_64" -f $g)
    if (Test-Path $dataDir) { Remove-Item $dataDir -Recurse -Force }

    $arguments = '--headless --path ' + $proj + ' --mcp-port=' + $port +
                 ' --export-release "Windows Desktop" ' + $exe

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName               = $Godot
    $psi.Arguments              = $arguments
    $psi.WorkingDirectory       = $Root
    $psi.UseShellExecute        = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.CreateNoWindow         = $true

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    $started = Get-Date
    [void]$proc.Start()
    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()
    $exited = $proc.WaitForExit(300000)
    $timedOut = -not $exited
    $exitCode = -999
    if ($exited) { $exitCode = $proc.ExitCode } else { try { $proc.Kill() } catch {}; [void]$proc.WaitForExit(20000) }
    $secs = [Math]::Round(((Get-Date) - $started).TotalSeconds, 1)
    $outText = ''; $errText = ''
    try { $outText = $outTask.Result } catch {}
    try { $errText = $errTask.Result } catch {}
    [System.IO.File]::WriteAllText($stdout, $outText, (New-Object System.Text.UTF8Encoding($false)))
    [System.IO.File]::WriteAllText($stderr, $errText, (New-Object System.Text.UTF8Encoding($false)))

    $exeOk  = Test-Path $exe
    $exeLen = 0; $exeSha = ''
    if ($exeOk) { $exeLen = (Get-Item $exe).Length; $exeSha = Get-Sha256 $exe }
    $pckOk  = Test-Path $pck
    $pckLen = 0; $pckSha = ''
    if ($pckOk) { $pckLen = (Get-Item $pck).Length; $pckSha = Get-Sha256 $pck }
    $dataOk = Test-Path $dataDir
    $dataFiles = 0; $dataBytes = 0
    if ($dataOk) {
        $items = @(Get-ChildItem -Path $dataDir -Recurse -File)
        $dataFiles = $items.Count
        if ($dataFiles -gt 0) { $dataBytes = ($items | Measure-Object -Property Length -Sum).Sum }
        if ($null -eq $dataBytes) { $dataBytes = 0 }
    }

    $packDone = ($outText -match '\[ DONE \]' -and $outText -match 'savepack')
    $errTail  = ''
    if ($errText -ne '') {
        $errTail = (@($errText -split "`r?`n" | Where-Object { $_ -ne '' } | Select-Object -Last 6) -join ' || ')
    }

    $rec = [ordered]@{
        game          = $g
        port          = $port
        argv          = $Godot + ' ' + $arguments
        env_extra     = 'UseSharedCompilation=false MSBUILDDISABLENODEREUSE=1 DOTNET_CLI_USE_MSBUILD_SERVER=0'
        exit_code     = $exitCode
        timed_out     = $timedOut
        seconds       = $secs
        pack_done_log = $packDone
        exe_path      = $exe
        exe_exists    = $exeOk
        exe_bytes     = $exeLen
        exe_sha256    = $exeSha
        pck_path      = $pck
        pck_exists    = $pckOk
        pck_bytes     = $pckLen
        pck_sha256    = $pckSha
        data_dir      = $dataDir
        data_exists   = $dataOk
        data_files    = $dataFiles
        data_bytes    = $dataBytes
        stderr_bytes  = $errText.Length
        stderr_tail   = $errTail
        stdout_log    = $stdout
        stderr_log    = $stderr
        ok            = ($exeOk -and $pckOk -and $dataOk -and ($exitCode -eq 0))
    }
    [void]$results.Add([pscustomobject]$rec)
    Write-Output ("EXPORT {0,-15} port={1} exit={2,-4} timeout={3,-5} {4,6}s exe={5,-9} pck={6,-7} datafiles={7,-4} databytes={8,-11} packdone={9} OK={10}" -f `
        $g, $port, $exitCode, $timedOut, $secs, $exeLen, $pckLen, $dataFiles, $dataBytes, $packDone, $rec.ok)
    if ($errTail -ne '') { Write-Output ("   stderr: " + $errTail) }
}

$json = $results | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText((Join-Path $Work 'export-results.json'), $json, (New-Object System.Text.UTF8Encoding($false)))

Write-Output ("DONE exports={0} exe_ok={1} exit0={2} ok_all_three={3}" -f `
    $results.Count, @($results | Where-Object { $_.exe_exists }).Count, `
    @($results | Where-Object { $_.exit_code -eq 0 }).Count, @($results | Where-Object { $_.ok }).Count)
