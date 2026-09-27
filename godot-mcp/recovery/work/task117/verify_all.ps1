# TASK-117 step A-verify: for every exported exe, run it headless and require
#   * exit code 0
#   * the game's own "<TOKEN>_READY ..." line on stdout  (proves it initialised its
#     own game state, not merely that a process started)
#   * a complete data_<game>_windows_x86_64 directory
# plus the MCP-port assertion (no --mcp-port -> no listener).
#
# Iron rule 1: no shell redirection.  Iron rule 3: cmd launches everything.  Iron
# rule 4: no port is taken by this step at all (we deliberately do NOT pass
# --mcp-port; that is the default path under test).
$ErrorActionPreference = 'Continue'
$Root = 'F:\moonbit-hof-rs\godot-mcp'
$Dist = Join-Path $Root 'dist\exe'
$Work = Join-Path $Root 'recovery\work\task117'
$Logs = Join-Path $Work 'logs\verify'
New-Item -ItemType Directory -Force -Path $Logs | Out-Null

# game -> the READY token its own source prints
$Games = @(
  'asteroids','bomberman','breakout','flappy','frogger','game2048','lunarlander',
  'match3','minesweeper','missilecommand','pacman','platformer','pong',
  'puzzlebobble','rtype','snake','sokoban','spaceinvaders','tetris','towerdefense'
)
$Ready = @{
  asteroids='AST'; bomberman='BOMBERMAN'; breakout='BREAKOUT'; flappy='FLAPPY';
  frogger='FROGGER'; game2048='GAME2048'; lunarlander='LUNARLANDER'; match3='MATCH3';
  minesweeper='MINESWEEPER'; missilecommand='MISSILECOMMAND'; pacman='PAC';
  platformer='PLATFORMER'; pong='PONG'; puzzlebobble='PUZZLEBOBBLE'; rtype='RTYPE';
  snake='SNAKE'; sokoban='SOKOBAN'; spaceinvaders='SI'; tetris='TETRIS';
  towerdefense='TOWERDEFENSE'
}

$PortsOfInterest = @(9877, 9888, 9889)
function Get-Listeners($plist) {
  $out = @()
  foreach ($p in $plist) {
    $h = @(Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue)
    if ($h.Count -gt 0) { $out += "$p" }
  }
  return ($out -join ',')
}
$baseline = Get-Listeners $PortsOfInterest
Write-Output ("baseline listeners 9877/9888/9889 = [{0}]" -f $baseline)

$results = @()
foreach ($g in $Games) {
    $dir  = Join-Path $Dist $g
    $exe  = Join-Path $dir ($g + '.exe')
    $so   = Join-Path $Logs ($g + '.run.stdout.txt')
    $se   = Join-Path $Logs ($g + '.run.stderr.txt')
    if (-not (Test-Path $exe)) {
        Write-Output ("VERIFY {0,-16} MISSING EXE" -f $g)
        $results += [pscustomobject]@{ game=$g; exit_code=$null; exe_exists=$false;
            ready_expected=($Ready[$g] + '_READY'); ready_found=$false; stdout_bytes=0;
            stderr_bytes=0; seconds=0; data_dll=$false; data_coreclr=$false; pass=$false }
        continue
    }

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $exe
    $psi.Arguments = '--headless --quit-after 120'
    $psi.WorkingDirectory = $dir
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi
    $t0 = Get-Date
    [void]$p.Start()
    $outTask = $p.StandardOutput.ReadToEndAsync()
    $errTask = $p.StandardError.ReadToEndAsync()
    if (-not $p.WaitForExit(60000)) {
        try { $p.Kill() } catch {}
        Write-Output ("VERIFY {0,-16} TIMEOUT(60s) killed" -f $g)
    }
    $out = $outTask.Result
    $err = $errTask.Result
    $exit = $null
    try { $exit = $p.ExitCode } catch {}
    $secs = [Math]::Round(((Get-Date) - $t0).TotalSeconds, 2)
    [System.IO.File]::WriteAllText($so, $out, (New-Object System.Text.UTF8Encoding($false)))
    [System.IO.File]::WriteAllText($se, $err, (New-Object System.Text.UTF8Encoding($false)))

    $want = $Ready[$g] + '_READY'
    $found = [bool]($out -match ('(?m)^' + [regex]::Escape($want) + '\b'))
    $notListening = [bool]($out -match '\[MCP\] not listening' -or $out -match 'listen=false')

    $dll = Join-Path $dir ('data_' + $g + '_windows_x86_64\' + $g + '.dll')
    $coreclr = Join-Path $dir ('data_' + $g + '_windows_x86_64\coreclr.dll')
    $pass = (($exit -eq 0) -and $found)
    $results += [pscustomobject]@{
        game=$g; exit_code=$exit; exe_exists=$true; ready_expected=$want; ready_found=$found;
        mcp_not_listening=$notListening; stdout_bytes=$out.Length; stderr_bytes=$err.Length;
        seconds=$secs; data_dll=(Test-Path $dll); data_coreclr=(Test-Path $coreclr);
        pass=[bool]$pass }
    Write-Output ("VERIFY {0,-16} exit={1,-5} {2}={3,-5} notlisten={4,-5} so={5,-6} se={6,-5} {7}s -> {8}" -f `
        $g, $exit, $want, $found, $notListening, $out.Length, $err.Length, $secs, $(if($pass){'PASS'}else{'FAIL'}))
}

$final = Get-Listeners $PortsOfInterest
Write-Output ("final    listeners 9877/9888/9889 = [{0}]  identical={1}" -f $final, ($baseline -eq $final))
$results | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $Work 'verify-results.json') -Encoding utf8
$nPass = @($results | Where-Object { $_.pass }).Count
$nExit = @($results | Where-Object { $_.exit_code -eq 0 }).Count
$nReady = @($results | Where-Object { $_.ready_found }).Count
$nDll = @($results | Where-Object { $_.data_dll }).Count
$nCore = @($results | Where-Object { $_.data_coreclr }).Count
$nNotListen = @($results | Where-Object { $_.mcp_not_listening }).Count
Write-Output ("DONE verified={0} pass={1} exit0={2} ready={3} data_dll={4} coreclr={5} not_listening={6}" -f `
    @($results).Count, $nPass, $nExit, $nReady, $nDll, $nCore, $nNotListen)
