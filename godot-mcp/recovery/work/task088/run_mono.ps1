param(
    [Parameter(Mandatory = $true)][string]$ArgLine,
    [Parameter(Mandatory = $true)][string]$Tag,
    [string]$Exe = 'bin\godot.windows.editor.x86_64.mono.exe'
)
# TASK-088: same contract as task085/run_godot.ps1 but for the mono binary.
# Iron rule 4: started from cmd.exe is not needed here (the engine is not a
# build), but iron rule 2 stands - Start-Process writes the log, no redirection.
$ErrorActionPreference = 'Continue'
$log = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs'
if (-not (Test-Path $log)) { New-Item -ItemType Directory -Force -Path $log | Out-Null }
$out = Join-Path $log ($Tag + '.stdout.txt')
$err = Join-Path $log ($Tag + '.stderr.txt')
$wd = 'H:\rebuild\godot'
$exe = Join-Path $wd $Exe
$sw = [System.Diagnostics.Stopwatch]::StartNew()
# Iron rule 4: the engine run is started from cmd.exe, one level under the
# launcher; the log is still written by Start-Process (iron rule 2).
# `/v:on` + `!ERRORLEVEL!`: `%ERRORLEVEL%` inside a single `cmd /c` line is
# expanded at PARSE time, so it always printed the value from before the command
# and every gate looked like exit 0. Delayed expansion is what makes the code
# real.
$cmdline = '"' + $exe + '" ' + $ArgLine + ' & echo [exitcode]=!ERRORLEVEL!'
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/v:on', '/c', $cmdline `
    -WorkingDirectory $wd -NoNewWindow -PassThru `
    -RedirectStandardOutput $out -RedirectStandardError $err
$p.WaitForExit()
$p.Refresh()
$sw.Stop()
Write-Output ("tag=$Tag")
Write-Output ("exe=$exe")
Write-Output ("args=$ArgLine")
Write-Output ("exit={0}" -f $p.ExitCode)
Write-Output ("wall_seconds={0:N1}" -f $sw.Elapsed.TotalSeconds)
Write-Output ("stdout=$out")
Write-Output ("stderr=$err")
