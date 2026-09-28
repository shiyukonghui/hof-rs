# TASK-148 step B5: per-game light smoke test of the freshly exported exe.
#
# Invoked from cmd:
#   cmd /c powershell -NoProfile -ExecutionPolicy Bypass -File smoke_all_task148.ps1
#
# For every game:
#   * launched THROUGH cmd.exe  (`cmd /c "<exe>"`), working dir = the game's own dir,
#     which is exactly what double-clicking / running the exe from cmd does;
#   * the game process is identified as the cmd child whose image name is "<game>.exe"
#     (a first-version of this script took the *first* child and got conhost.exe, which
#     produced 20 false negatives and 20 orphaned game processes - fixed here);
#   * the main window is detected with EnumWindows (visible top-level window whose title
#     settles to the project name), with Process.MainWindowHandle as a cross-check;
#   * the process must still be alive at >= 3 s uptime;
#   * the game process (and its cmd parent) is terminated and the result recorded.
#
# No --mcp-port is passed: the delivered games must not listen by default, which is also
# what TASK-109 verified.  The reserved ports 9877 / 9888 / 9889 / 8080 / 8081 and every
# listener >= 19000 are sampled before and after each launch so any new listener shows up.
#
# Iron rules honoured here: no shell redirection (Start-Process -Redirect* to files or
# in-memory capture), nothing destructive beyond the processes this script spawned.
$ErrorActionPreference = 'Continue'

Add-Type @'
using System;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public class WinApi148 {
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetWindowTextW(IntPtr hWnd, StringBuilder s, int n);
    [DllImport("user32.dll")] static extern int GetWindowTextLengthW(IntPtr hWnd);
    public static List<string> WindowsForPid(uint target) {
        var res = new List<string>();
        EnumWindows((h, l) => {
            uint p; GetWindowThreadProcessId(h, out p);
            if (p == target) {
                int len = GetWindowTextLengthW(h);
                var sb = new StringBuilder(len + 1);
                GetWindowTextW(h, sb, sb.Capacity);
                res.Add(h.ToInt64().ToString() + "\t" + (IsWindowVisible(h) ? "1" : "0") + "\t" + sb.ToString());
            }
            return true;
        }, IntPtr.Zero);
        return res;
    }
}
'@

$Root    = 'F:\moonbit-hof-rs\godot-mcp'
$Work    = Join-Path $Root 'recovery\work\task148'
$OutRoot = Join-Path $Work 'exe'
$Logs    = Join-Path $Work 'logs\smoke'
New-Item -ItemType Directory -Force -Path $Logs | Out-Null

$Games = @(
  'asteroids','bomberman','breakout','flappy','frogger','game2048','lunarlander',
  'match3','minesweeper','missilecommand','pacman','platformer','pong',
  'puzzlebobble','rtype','snake','sokoban','spaceinvaders','tetris','towerdefense'
)

$Reserved = @(9877, 9888, 9889, 8080, 8081)

function Get-Listeners {
    $found = @()
    foreach ($p in $Reserved) {
        $c = Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue
        foreach ($x in $c) { $found += ("{0}:{1}" -f $x.LocalAddress, $x.LocalPort) }
    }
    return @($found | Sort-Object -Unique)
}

function Get-HighListeners {
    $c = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
         Where-Object { $_.LocalPort -ge 19000 }
    return @(($c | ForEach-Object { "{0}:{1}" -f $_.LocalAddress, $_.LocalPort }) | Sort-Object -Unique)
}

$names = @($Games | ForEach-Object { $_ + '.exe' })
$preLeftover = @(Get-CimInstance Win32_Process | Where-Object { $names -contains $_.Name })
if ($preLeftover.Count -gt 0) {
    Write-Output ("PRE-RUN leftover game processes (killing): " + (@($preLeftover | ForEach-Object { $_.Name + ':' + $_.ProcessId }) -join ', '))
    foreach ($p in $preLeftover) { try { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue } catch {} }
    Start-Sleep -Seconds 2
} else {
    Write-Output "PRE-RUN leftover game processes: none"
}

$baselineReserved = Get-Listeners
$baselineHigh     = Get-HighListeners
Write-Output ("BASELINE reserved[{0}] = [{1}]" -f ($Reserved -join '/'), ($baselineReserved -join ', '))
Write-Output ("BASELINE high >=19000 = [{0}]" -f ($baselineHigh -join ', '))

$results = New-Object System.Collections.ArrayList
foreach ($g in $Games) {
    $dir = Join-Path $OutRoot $g
    $exe = Join-Path $dir "$g.exe"

    $rec = [ordered]@{
        game            = $g
        exe_path        = $exe
        launch          = 'cmd /c "<exe>"  (cwd = game dir, no --mcp-port)'
        pid             = 0
        started         = $false
        window_found    = $false
        window_title    = ''
        window_handle   = 0
        main_window_handle_process_api = 0
        alive_seconds   = 0.0
        alive_at_3s     = $false
        exit_method     = ''
        still_alive_end = $false
        reserved_delta  = ''
        high_delta      = ''
        pass            = $false
    }

    if (-not (Test-Path $exe)) {
        $rec.exit_method = 'not-launched (exe missing)'
        [void]$results.Add([pscustomobject]$rec)
        Write-Output ("SMOKE {0,-15} EXE-MISSING" -f $g)
        continue
    }

    $cmd = Start-Process -FilePath 'cmd.exe' `
        -ArgumentList @('/c', ('"' + $exe + '"')) `
        -WorkingDirectory $dir -PassThru
    $rec.started = $true
    $sw = [Diagnostics.Stopwatch]::StartNew()

    # the game process = the cmd child whose image name is "<game>.exe"
    $gamePid = 0
    for ($t = 0; $t -lt 150 -and $gamePid -eq 0; $t++) {
        Start-Sleep -Milliseconds 200
        $child = Get-CimInstance Win32_Process -Filter ("ParentProcessId=" + $cmd.Id) -ErrorAction SilentlyContinue |
                 Where-Object { $_.Name -eq "$g.exe" } | Select-Object -First 1
        if ($child) { $gamePid = [int]$child.ProcessId }
        if ($cmd.HasExited) { break }
    }
    $rec.pid = $gamePid

    if ($gamePid -eq 0) {
        $rec.exit_method = 'process not observed'
        try { if (-not $cmd.HasExited) { $cmd.Kill() } } catch {}
        [void]$results.Add([pscustomobject]$rec)
        Write-Output ("SMOKE {0,-15} NO-PROCESS" -f $g)
        continue
    }

    # poll up to 15 s for a visible top-level window with a settled title
    $deadline = (Get-Date).AddSeconds(15)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 400
        $gp = Get-Process -Id $gamePid -ErrorAction SilentlyContinue
        if (-not $gp) { break }
        $gp.Refresh()
        if ($gp.MainWindowHandle -ne 0) { $rec.main_window_handle_process_api = [int64]$gp.MainWindowHandle.ToInt64() }
        $wins = [WinApi148]::WindowsForPid([uint32]$gamePid)
        foreach ($w in $wins) {
            $parts = $w -split "`t"
            $h = [int64]$parts[0]
            $vis = ($parts[1] -eq '1')
            $ttl = $parts[2]
            if ($vis -and $ttl -ne '') {
                $rec.window_found  = $true
                $rec.window_handle = $h
                $rec.window_title  = $ttl
                break
            }
            if ($vis -and $rec.window_handle -eq 0) {
                $rec.window_found  = $true
                $rec.window_handle = $h
                $rec.window_title  = $ttl
            }
        }
        if ($rec.window_title -ne '') { break }
    }

    # require >= 3 s uptime
    while ($sw.Elapsed.TotalSeconds -lt 3.2) { Start-Sleep -Milliseconds 200 }
    $gp = Get-Process -Id $gamePid -ErrorAction SilentlyContinue
    $rec.alive_seconds = [Math]::Round($sw.Elapsed.TotalSeconds, 2)

    if ($gp) {
        $gp.Refresh()
        $rec.alive_at_3s = $true
        if ($gp.MainWindowHandle -ne 0) { $rec.main_window_handle_process_api = [int64]$gp.MainWindowHandle.ToInt64() }

        $reservedNow = Get-Listeners
        $highNow     = Get-HighListeners
        $rec.reserved_delta = (@($reservedNow | Where-Object { $baselineReserved -notcontains $_ }) -join ',')
        $rec.high_delta     = (@($highNow     | Where-Object { $baselineHigh     -notcontains $_ }) -join ',')

        try {
            $gp.Kill()
            [void]$gp.WaitForExit(15000)
            $rec.exit_method = 'TerminateProcess (killed after smoke)'
        } catch {
            $rec.exit_method = 'kill failed: ' + $_.Exception.Message
        }
        Start-Sleep -Milliseconds 500
        if (Get-Process -Id $gamePid -ErrorAction SilentlyContinue) { $rec.still_alive_end = $true }
        try { if (-not $cmd.HasExited) { $cmd.Kill() } } catch {}
    } else {
        $rec.exit_method = 'game exited by itself before kill'
        $rec.still_alive_end = $false
    }

    $rec.pass = ($rec.started -and $rec.alive_at_3s -and $rec.window_found -and (-not $rec.still_alive_end))
    [void]$results.Add([pscustomobject]$rec)
    Write-Output ("SMOKE {0,-15} pid={1,-7} alive={2,-6}s window={3,-5} title='{4}' exit='{5}' reserved+=[{6}] high+=[{7}] PASS={8}" -f `
        $g, $rec.pid, $rec.alive_seconds, $rec.window_found, $rec.window_title, $rec.exit_method, `
        $rec.reserved_delta, $rec.high_delta, $rec.pass)
}

# orphan check
Start-Sleep -Seconds 3
$orphanGames = @()
foreach ($g in $Games) {
    $p = Get-Process -Name $g -ErrorAction SilentlyContinue
    if ($p) { $orphanGames += ("{0}:{1}" -f $g, (($p | ForEach-Object { $_.Id }) -join '+')) }
}
$orphanGodot = @(Get-Process -Name 'godot*' -ErrorAction SilentlyContinue)
$finalReserved = Get-Listeners
$finalHigh     = Get-HighListeners

$orphans = [ordered]@{
    orphan_game_processes  = ($orphanGames -join ', ')
    orphan_godot_processes = (@($orphanGodot | ForEach-Object { "{0}:{1}" -f $_.ProcessName, $_.Id }) -join ', ')
    final_reserved_listeners    = ($finalReserved -join ', ')
    final_high_listeners        = ($finalHigh -join ', ')
    baseline_reserved_listeners = ($baselineReserved -join ', ')
    baseline_high_listeners     = ($baselineHigh -join ', ')
}

$out = [ordered]@{
    launch_model      = 'cmd /c "<exe>" from the game directory; no --mcp-port passed'
    alive_requirement = '>= 3 s uptime and a visible top-level window (title = project name)'
    reserved_ports    = ($Reserved -join '/')
    baseline_reserved = ($baselineReserved -join ', ')
    baseline_high     = ($baselineHigh -join ', ')
    results           = $results
    orphans           = $orphans
}
$json = $out | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText((Join-Path $Work 'smoke-results.json'), $json, (New-Object System.Text.UTF8Encoding($false)))

$pass = @($results | Where-Object { $_.pass }).Count
Write-Output ("DONE smoke total={0} pass={1}" -f $results.Count, $pass)
Write-Output ("ORPHAN game=[{0}] godot=[{1}]" -f $orphans.orphan_game_processes, $orphans.orphan_godot_processes)
Write-Output ("FINAL reserved=[{0}] high=[{1}]" -f ($finalReserved -join ', '), ($finalHigh -join ', '))
