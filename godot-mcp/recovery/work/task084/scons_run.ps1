param(
  [Parameter(Mandatory=$true)][string]$Command,
  [Parameter(Mandatory=$true)][string]$Tag
)
# TASK-084 build launcher: SCons must start from cmd.exe (iron rule 4) and no
# shell redirection may be used (iron rule 2) - Start-Process writes the log.
$logdir = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs'
if (-not (Test-Path $logdir)) { New-Item -ItemType Directory -Force -Path $logdir | Out-Null }
$out = Join-Path $logdir ($Tag + '.stdout.txt')
$err = Join-Path $logdir ($Tag + '.stderr.txt')
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $Command -WorkingDirectory 'H:\rebuild\godot' `
      -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -Wait -PassThru
$sw.Stop()
Write-Output ("tag=" + $Tag)
Write-Output ("command=" + $Command)
Write-Output ("exit=" + $p.ExitCode)
Write-Output ("wall_seconds=" + [math]::Round($sw.Elapsed.TotalSeconds, 1))
Write-Output ("stdout=" + $out)
Write-Output ("stderr=" + $err)
