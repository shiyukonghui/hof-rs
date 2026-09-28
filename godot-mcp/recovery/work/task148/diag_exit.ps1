# TASK-148 diagnosis: why does the export process sometimes not exit?
$ErrorActionPreference = 'Continue'
$Godot = 'F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe'
$D     = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task148'
$Root  = 'F:\moonbit-hof-rs\godot-mcp'

function Run-Export {
    param([string]$Game, [int]$Port, [bool]$NoShared, [int]$BudgetSec)
    $proj = Join-Path $Root ("projects\" + $Game)
    $out  = Join-Path $D ("exe\" + $Game)
    New-Item -ItemType Directory -Force -Path $out | Out-Null
    Remove-Item (Join-Path $out ($Game + '.exe')) -Force -ErrorAction SilentlyContinue
    Remove-Item (Join-Path $out ($Game + '.pck')) -Force -ErrorAction SilentlyContinue
    $argl = @('--headless','--path',$proj,"--mcp-port=$Port",'--export-release','"Windows Desktop"',(Join-Path $out ($Game + '.exe')))

    if ($NoShared) { $env:UseSharedCompilation = 'false' } else { Remove-Item Env:\UseSharedCompilation -ErrorAction SilentlyContinue }
    $env:MSBUILDDISABLENODEREUSE = '1'
    $env:DOTNET_CLI_USE_MSBUILD_SERVER = '0'

    $p = Start-Process -FilePath $Godot -ArgumentList $argl -PassThru -NoNewWindow `
         -RedirectStandardOutput (Join-Path $D ("logs\diag-$Game.out.txt")) `
         -RedirectStandardError  (Join-Path $D ("logs\diag-$Game.err.txt"))
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while ((-not $p.HasExited) -and $sw.Elapsed.TotalSeconds -lt $BudgetSec) { Start-Sleep -Milliseconds 500 }
    $sw.Stop()
    $code = 'n/a'
    $exited = $p.HasExited
    if ($exited) { $p.Refresh(); $code = $p.ExitCode; if ($null -eq $code) { $code = 'EMPTY' } }
    $vb = @(Get-Process VBCSCompiler -ErrorAction SilentlyContinue).Count
    Write-Output ("DIAG {0,-12} NoShared={1,-5} exited={2,-5} code=[{3}] seconds={4,-7} VBCSCompiler_alive={5}" -f `
        $Game, $NoShared, $exited, $code, [Math]::Round($sw.Elapsed.TotalSeconds,1), $vb)
    if (-not $exited) { try { $p.Kill() } catch {} }
    # leave no engine behind
    Start-Sleep -Milliseconds 500
    Get-Process -Name ($Game) -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}

# step 0: kill any lingering compiler server first
Get-Process VBCSCompiler -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Run-Export -Game 'pong'     -Port 19408 -NoShared $false -BudgetSec 120
Run-Export -Game 'tetris'   -Port 19409 -NoShared $false -BudgetSec 120
Run-Export -Game 'match3'   -Port 19410 -NoShared $true  -BudgetSec 120

Write-Output ("DIAG-DONE VBCSCompiler_alive=" + @(Get-Process VBCSCompiler -ErrorAction SilentlyContinue).Count)
Get-Process godot* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
