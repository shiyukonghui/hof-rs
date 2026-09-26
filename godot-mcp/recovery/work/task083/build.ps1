# TASK-083 build driver (pure ASCII).
# Launches the build through cmd.exe and redirects the child's stdout/stderr to
# absolute paths.  No shell redirection operators are used anywhere.
param(
  [Parameter(Mandatory=$true)][string]$Tag,
  [Parameter(Mandatory=$true)][string]$Args
)
$log = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs'
if (-not (Test-Path $log)) { New-Item -ItemType Directory -Path $log | Out-Null }
$stdout = Join-Path $log ($Tag + '.stdout.txt')
$stderr = Join-Path $log ($Tag + '.stderr.txt')
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $Args -WorkingDirectory 'H:\rebuild\godot' `
       -RedirectStandardOutput $stdout -RedirectStandardError $stderr -Wait -PassThru
$sw.Stop()
Write-Output ('TAG=' + $Tag)
Write-Output ('COMMAND=' + $Args)
Write-Output ('EXITCODE=' + $p.ExitCode)
Write-Output ('SECONDS=' + [math]::Round($sw.Elapsed.TotalSeconds, 1))
Write-Output ('STDOUT=' + $stdout)
Write-Output ('STDERR=' + $stderr)
Write-Output ('STDOUT_BYTES=' + (Get-Item $stdout).Length)
Write-Output ('STDERR_BYTES=' + (Get-Item $stderr).Length)
