# TASK-117 step A: re-export the 20 C# games to dist\exe\<game>\<game>.exe with the
# 4.8.dev template that is already installed (TASK-109 built it; no template download,
# no template policy change -- the user closed the SAC question).
#
# Invoked from cmd (iron rule 3):
#   cmd /c powershell -NoProfile -ExecutionPolicy Bypass -File export_all.ps1
# Iron rule 1: no shell redirection -- Start-Process -RedirectStandardOutput/Error.
# Iron rule 4: each engine run gets a UNIQUE --mcp-port (19401..19420); 9877 untouched.
# Nothing is deleted: the previous (pre-fix) exports were moved aside beforehand by
# preflight.ps1, so this writes into a clean directory.
$ErrorActionPreference = 'Continue'

# ---------------------------------------------------------------------------
# TASK-117 fix for a hang measured on the first attempt (see the report, defect
# D1): the Godot *console wrapper* (`*.console.exe`) exits when its job object
# reports JOB_OBJECT_MSG_ACTIVE_PROCESS_ZERO -- i.e. when the editor AND every
# process it spawned are gone
# (`godot\platform\windows\console_wrapper_windows.cpp:104-172`).  `dotnet publish`
# starts a persistent Roslyn server (`VBCSCompiler.exe`); that child inherits the
# job, outlives the editor, and the wrapper then waits forever (one export measured
# at 113.9 s and still running, with the export itself already finished).
# Disabling the build servers removes the long-lived child, so the wrapper's own
# exit condition is met naturally.  No engine/source change is involved.
$env:UseSharedCompilation = 'false'
$env:DOTNET_CLI_USE_MSBUILD_SERVER = '0'
$env:MSBUILDDISABLENODEREUSE = '1'
Write-Output ("build servers disabled: UseSharedCompilation={0} DOTNET_CLI_USE_MSBUILD_SERVER={1} MSBUILDDISABLENODEREUSE={2}" -f `
    $env:UseSharedCompilation, $env:DOTNET_CLI_USE_MSBUILD_SERVER, $env:MSBUILDDISABLENODEREUSE)

$Godot    = 'F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe'
$Root     = 'F:\moonbit-hof-rs\godot-mcp'
$Projects = Join-Path $Root 'projects'
$Dist     = Join-Path $Root 'dist\exe'
$Work     = Join-Path $Root 'recovery\work\task117'
$Logs     = Join-Path $Work 'logs'

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

    $started = Get-Date
    # Start from a clean destination for THIS game only (guarded: it must live under
    # dist\exe), so a re-export can never leave a stale file from the previous run.
    if (Test-Path $outDir) {
        $full = (Resolve-Path $outDir).Path
        if ($full.StartsWith($Dist, [System.StringComparison]::OrdinalIgnoreCase)) {
            Remove-Item -Path $full -Recurse -Force
            New-Item -ItemType Directory -Force -Path $outDir | Out-Null
        } else {
            Write-Output ("REFUSED to clean outside dist: {0}" -f $full)
            continue
        }
    }
    $proc = Start-Process -FilePath $Godot `
        -ArgumentList @('--headless','--path',$proj,("--mcp-port=" + $port),'--export-release','"Windows Desktop"',$exe) `
        -Wait -PassThru -NoNewWindow -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    $exit = $proc.ExitCode
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
    $dataDir = Join-Path $outDir ("data_{0}_windows_x86_64" -f $g)
    $dataOk = Test-Path $dataDir
    $dataFiles = 0
    $dataBytes = 0
    if ($dataOk) {
        $items = Get-ChildItem -Path $dataDir -Recurse -File
        $dataFiles = $items.Count
        $dataBytes = ($items | Measure-Object -Property Length -Sum).Sum
    }
    $dllOk = Test-Path (Join-Path $dataDir ("{0}.dll" -f $g))
    $coreclrOk = Test-Path (Join-Path $dataDir 'coreclr.dll')

    # the export must not have produced a debug/console wrapper or an embedded pck
    $preset = Get-Content (Join-Path $proj 'export_presets.cfg') -Raw

    $rec = [ordered]@{
        game            = $g
        port            = $port
        exit_code       = $exit
        seconds         = $secs
        exe_path        = $exe
        exe_exists      = $exeOk
        exe_bytes       = $exeLen
        exe_sha256      = $exeSha
        pck_path        = $pck
        pck_exists      = $pckOk
        pck_bytes       = $pckLen
        pck_sha256      = $pckSha
        data_dir        = $dataDir
        data_dir_exists = $dataOk
        data_files      = $dataFiles
        data_bytes      = $dataBytes
        data_has_game_dll = $dllOk
        data_has_coreclr  = $coreclrOk
        stdout_log      = $stdout
        stderr_log      = $stderr
    }
    [void]$results.Add([pscustomobject]$rec)
    Write-Output ("EXPORT {0,-16} exit={1,-3} exe={2,-9} pck={3,-7} data={4}f/{5}B {6}s" -f `
        $g, $exit, $exeLen, $pckLen, $dataFiles, $dataBytes, $secs)
}

$results | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $Work 'export-results.json') -Encoding utf8
Write-Output ("DONE exports={0} exe_ok={1} exit0={2} data_ok={3}" -f `
    $results.Count, ($results | Where-Object { $_.exe_exists }).Count, `
    ($results | Where-Object { $_.exit_code -eq 0 }).Count, `
    ($results | Where-Object { $_.data_dir_exists }).Count)
