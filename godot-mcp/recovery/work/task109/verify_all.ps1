# TASK-109 step 4: verify every exported exe really runs.
# Invoked from cmd:
#   cmd /c powershell -NoProfile -ExecutionPolicy Bypass -File verify_all.ps1
#
# For every game:
#   (a) headless deterministic run:  <game>.exe --headless --quit-after 120
#       -> assert exit code 0, keep the stdout tail as evidence
#   (b) NO --mcp-port is passed, so a game role must NOT listen (REQUIREMENTS C4)
#       -> assert 9877 / 9888 / 9889 gain no new listener
# Then a windowed spot check: the process must start and stay alive.
#
# Output redirection uses System.Diagnostics.ProcessStartInfo (the .NET equivalent
# of Start-Process -RedirectStandardOutput: no shell redirection anywhere).
# Exit codes are read from the Process object after ReadToEnd, which is the only
# way that reliably yields ExitCode (Start-Process -PassThru returns $null here).
$ErrorActionPreference = 'Continue'

$Root  = 'F:\moonbit-hof-rs\godot-mcp'
$Dist  = Join-Path $Root 'dist\exe'
$Work  = Join-Path $Root 'recovery\work\task109'
$VLogs = Join-Path $Work 'logs\verify'
New-Item -ItemType Directory -Force -Path $VLogs | Out-Null

$Games = @(
  'asteroids','bomberman','breakout','flappy','frogger','game2048','lunarlander',
  'match3','minesweeper','missilecommand','pacman','platformer','pong',
  'puzzlebobble','rtype','snake','sokoban','spaceinvaders','tetris','towerdefense'
)

$WatchPorts = @(9877, 9888, 9889)

function Get-McpListeners {
    $found = @()
    foreach ($p in $WatchPorts) {
        $c = Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue
        foreach ($x in $c) { $found += ("{0}:{1}" -f $x.LocalAddress, $x.LocalPort) }
    }
    return ($found | Sort-Object -Unique)
}

function Start-Game {
    param([string]$Exe, [string]$Arguments, [string]$WorkingDir)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName               = $Exe
    $psi.Arguments              = $Arguments
    $psi.WorkingDirectory       = $WorkingDir
    $psi.UseShellExecute        = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.CreateNoWindow         = $true
    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi
    [void]$p.Start()
    $outTask = $p.StandardOutput.ReadToEndAsync()
    $errTask = $p.StandardError.ReadToEndAsync()
    return @{ Proc = $p; OutTask = $outTask; ErrTask = $errTask }
}

$baseline = Get-McpListeners
Write-Output ("MCP baseline listeners on 9877/9888/9889: [{0}]" -f ($baseline -join ', '))

$results = New-Object System.Collections.ArrayList
foreach ($g in $Games) {
    $exe    = Join-Path $Dist "$g\$g.exe"
    $wd     = Join-Path $Dist $g
    $stdout = Join-Path $VLogs "$g.run.stdout.txt"
    $stderr = Join-Path $VLogs "$g.run.stderr.txt"

    $exeExists = Test-Path $exe
    $exitCode  = -1
    $timedOut  = $false
    $secs      = 0.0
    $outText   = ''
    $errText   = ''

    if ($exeExists) {
        $started = Get-Date
        $h = Start-Game -Exe $exe -Arguments '--headless --quit-after 120' -WorkingDir $wd
        $exited = $h.Proc.WaitForExit(180000)
        if (-not $exited) {
            $timedOut = $true
            try { $h.Proc.Kill() } catch {}
            [void]$h.Proc.WaitForExit(20000)
            $exitCode = -999
        } else {
            $exitCode = $h.Proc.ExitCode
        }
        $secs = [Math]::Round(((Get-Date) - $started).TotalSeconds, 2)
        $outText = $h.OutTask.Result
        $errText = $h.ErrTask.Result
        [System.IO.File]::WriteAllText($stdout, $outText, (New-Object System.Text.UTF8Encoding($false)))
        [System.IO.File]::WriteAllText($stderr, $errText, (New-Object System.Text.UTF8Encoding($false)))
    }

    $newPorts = @( (Get-McpListeners) | Where-Object { $baseline -notcontains $_ } )

    $tail = @()
    if ($outText -ne '') {
        $tail = @($outText -split "`r?`n" | Where-Object { $_ -ne '' } | Select-Object -Last 15)
    }

    $rec = [ordered]@{
        game          = $g
        exe_path      = $exe
        exe_exists    = $exeExists
        mode          = 'headless --quit-after 120'
        exit_code     = $exitCode
        pass_exit0    = ($exitCode -eq 0)
        timed_out     = $timedOut
        seconds       = $secs
        stdout_bytes  = $outText.Length
        stderr_bytes  = $errText.Length
        new_mcp_ports = ($newPorts -join ',')
        stdout_tail   = ($tail -join "`n")
        stdout_log    = $stdout
        stderr_log    = $stderr
    }
    [void]$results.Add([pscustomobject]$rec)
    Write-Output ("VERIFY {0,-16} exists={1,-5} exit={2,-4} timeout={3,-5} {4,6}s out={5,-5} err={6,-5} newports=[{7}]" -f $g, $exeExists, $exitCode, $timedOut, $secs, $outText.Length, $errText.Length, ($newPorts -join ','))
}

# ---- windowed spot check -------------------------------------------------
$spot = @('pong','snake','tetris')
$spotResults = New-Object System.Collections.ArrayList
foreach ($g in $spot) {
    $exe    = Join-Path $Dist "$g\$g.exe"
    $wd     = Join-Path $Dist $g
    $stdout = Join-Path $VLogs "$g.window.stdout.txt"
    $stderr = Join-Path $VLogs "$g.window.stderr.txt"

    $h = Start-Game -Exe $exe -Arguments '' -WorkingDir $wd
    Start-Sleep -Seconds 8
    $alive = -not $h.Proc.HasExited
    $newPorts = @( (Get-McpListeners) | Where-Object { $baseline -notcontains $_ } )
    $ec = $null
    if ($alive) {
        try { $h.Proc.Kill() } catch {}
        [void]$h.Proc.WaitForExit(20000)
        $ec = 'killed-after-8s'
    } else {
        $ec = $h.Proc.ExitCode
    }
    $outText = $h.OutTask.Result
    $errText = $h.ErrTask.Result
    [System.IO.File]::WriteAllText($stdout, $outText, (New-Object System.Text.UTF8Encoding($false)))
    [System.IO.File]::WriteAllText($stderr, $errText, (New-Object System.Text.UTF8Encoding($false)))

    $rec = [ordered]@{
        game          = $g
        mode          = 'windowed (no --headless), 8s then killed'
        stayed_alive  = $alive
        exit_code     = $ec
        new_mcp_ports = ($newPorts -join ',')
        stdout_bytes  = $outText.Length
        stderr_bytes  = $errText.Length
        stdout_log    = $stdout
        stderr_log    = $stderr
    }
    [void]$spotResults.Add([pscustomobject]$rec)
    Write-Output ("WINDOW {0,-16} alive_after_8s={1,-5} exit={2} newports=[{3}]" -f $g, $alive, $ec, ($newPorts -join ','))
}

$final = Get-McpListeners
Write-Output ("MCP final listeners on 9877/9888/9889: [{0}]" -f ($final -join ', '))

$out = [ordered]@{
    baseline_ports = ($baseline -join ',')
    final_ports    = ($final -join ',')
    headless       = $results
    windowed       = $spotResults
}
$json = $out | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText((Join-Path $Work 'verify-results.json'), $json, (New-Object System.Text.UTF8Encoding($false)))

Write-Output ("DONE verify total={0} pass_exit0={1} window_alive={2}" -f $results.Count, ($results | Where-Object { $_.pass_exit0 }).Count, ($spotResults | Where-Object { $_.stayed_alive }).Count)
Write-Output ("MCP-PORT-CHECK 9877/9888/9889 baseline=[{0}] final=[{1}] identical={2}" -f ($baseline -join ','), ($final -join ','), (($baseline -join ',') -eq ($final -join ',')))
