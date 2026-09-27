# TASK-109 step 3: export all 20 C# games to Windows exe.
# Invoked from cmd:
#   cmd /c powershell -NoProfile -ExecutionPolicy Bypass -File export_all.ps1
# Iron rules honoured here:
#   * no shell redirection - Start-Process -RedirectStandardOutput/-RedirectStandardError
#   * each engine run gets a UNIQUE --mcp-port (19401..19420) so the user's 9877 is never touched
$ErrorActionPreference = 'Continue'

$Godot    = 'F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe'
$Root     = 'F:\moonbit-hof-rs\godot-mcp'
$Projects = Join-Path $Root 'projects'
$Dist     = Join-Path $Root 'dist\exe'
$Logs     = Join-Path $Root 'recovery\work\task109\logs'
$Work     = Join-Path $Root 'recovery\work\task109'

New-Item -ItemType Directory -Force -Path $Dist | Out-Null
New-Item -ItemType Directory -Force -Path $Logs | Out-Null

$Games = @(
  'asteroids','bomberman','breakout','flappy','frogger','game2048','lunarlander',
  'match3','minesweeper','missilecommand','pacman','platformer','pong',
  'puzzlebobble','rtype','snake','sokoban','spaceinvaders','tetris','towerdefense'
)

$results = New-Object System.Collections.ArrayList
$i = 0
foreach ($g in $Games) {
    $i++
    $proj   = Join-Path $Projects $g
    $outDir = Join-Path $Dist $g
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    $exe    = Join-Path $outDir "$g.exe"
    $pck    = Join-Path $outDir "$g.pck"
    $stdout = Join-Path $Logs "export-$g.stdout.txt"
    $stderr = Join-Path $Logs "export-$g.stderr.txt"
    $port   = 19400 + $i

    if (Test-Path $exe) { Remove-Item $exe -Force }
    if (Test-Path $pck) { Remove-Item $pck -Force }
    $dataDir = Join-Path $outDir ("data_{0}_windows_x86_64" -f $g)
    if (Test-Path $dataDir) { Remove-Item $dataDir -Recurse -Force }

    $started = Get-Date
    $proc = Start-Process -FilePath $Godot `
        -ArgumentList @('--headless','--path',$proj,("--mcp-port=" + $port),'--export-release','"Windows Desktop"',$exe) `
        -Wait -PassThru -NoNewWindow -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    $secs = [Math]::Round(((Get-Date) - $started).TotalSeconds, 1)

    $exeOk = Test-Path $exe
    $exeLen = 0
    $exeSha = ''
    if ($exeOk) {
        $exeLen = (Get-Item $exe).Length
        $exeSha = (Get-FileHash $exe -Algorithm SHA256).Hash.ToLower()
    }
    $pckOk = Test-Path $pck
    $pckLen = 0
    $pckSha = ''
    if ($pckOk) {
        $pckLen = (Get-Item $pck).Length
        $pckSha = (Get-FileHash $pck -Algorithm SHA256).Hash.ToLower()
    }

    $rec = [ordered]@{
        game           = $g
        port           = $port
        exit_code      = $proc.ExitCode
        seconds        = $secs
        exe_path       = $exe
        exe_exists     = $exeOk
        exe_bytes      = $exeLen
        exe_sha256     = $exeSha
        pck_path       = $pck
        pck_exists     = $pckOk
        pck_bytes      = $pckLen
        pck_sha256     = $pckSha
        stdout_log     = $stdout
        stderr_log     = $stderr
    }
    [void]$results.Add([pscustomobject]$rec)
    Write-Output ("EXPORT {0,-16} exit={1,-3} exe={2,-9} pck={3,-9} {4}s" -f $g, $proc.ExitCode, $exeLen, $pckLen, $secs)
}

$results | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $Work 'export-results.json') -Encoding utf8
Write-Output ("DONE exports={0} exe_ok={1} exit0={2}" -f $results.Count, ($results | Where-Object { $_.exe_exists }).Count, ($results | Where-Object { $_.exit_code -eq 0 }).Count)
