param(
    [Parameter(Mandatory = $true)][string]$Command,
    [Parameter(Mandatory = $true)][string]$Tag,
    [string]$WorkDir = 'H:\rebuild\godot'
)
# TASK-088 generic launcher: cmd.exe child (iron rule 4), Start-Process writes the
# log (iron rule 2, no shell redirection anywhere).
$logdir = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs'
if (-not (Test-Path $logdir)) { New-Item -ItemType Directory -Force -Path $logdir | Out-Null }
$out = Join-Path $logdir ($Tag + '.stdout.txt')
$err = Join-Path $logdir ($Tag + '.stderr.txt')
$sw = [System.Diagnostics.Stopwatch]::StartNew()
# `-Wait` waits for the whole DESCENDANT tree, and MSBuild keeps reuse nodes
# alive for 15 minutes after a successful build, so a finished build looked like
# a hung one. WaitForExit() waits for cmd.exe only.
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/v:on', '/c', ($Command + ' & echo [exitcode]=!ERRORLEVEL!') -WorkingDirectory $WorkDir `
      -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -PassThru
$p.WaitForExit()
$p.Refresh()
$sw.Stop()
Write-Output ("tag=" + $Tag)
Write-Output ("workdir=" + $WorkDir)
Write-Output ("command=" + $Command)
Write-Output ("exit=" + $p.ExitCode)
Write-Output ("wall_seconds=" + [math]::Round($sw.Elapsed.TotalSeconds, 1))
Write-Output ("stdout=" + $out)
Write-Output ("stderr=" + $err)
