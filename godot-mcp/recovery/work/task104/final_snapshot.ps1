param(
  [string]$Root = 'F:\moonbit-hof-rs'
)
# TASK-104: the two-repository snapshot the report quotes, written through
# Start-Process so the helper owns its stdout/stderr (iron rule 1: no shell
# redirection anywhere).
$ErrorActionPreference = 'Stop'
$work = Join-Path $Root 'godot-mcp\recovery\work\task104'
$logs = Join-Path $work 'logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$out = Join-Path $logs 'final-snapshot.txt'
$err = Join-Path $logs 'final-snapshot.err.txt'
$bat = Join-Path $logs 'final-snapshot.cmd'
$batch = @(
  '@echo off',
  'set MAIN=F:\moonbit-hof-rs',
  'set ENG=F:\moonbit-hof-rs\godot-mcp\godot',
  'echo ===MAIN rev-parse HEAD===',
  'git -C "%MAIN%" rev-parse HEAD',
  'echo ===MAIN log --oneline -8===',
  'git -C "%MAIN%" log --oneline -8',
  'echo ===MAIN status --short===',
  'git -C "%MAIN%" status --short',
  'echo ===ENG rev-parse HEAD===',
  'git -C "%ENG%" rev-parse HEAD',
  'echo ===ENG rev-parse origin ref===',
  'git -C "%ENG%" rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild',
  'echo ===ENG log --oneline -8===',
  'git -C "%ENG%" log --oneline -8',
  'echo ===ENG status --short===',
  'git -C "%ENG%" status --short',
  'echo ===PROCESSES===',
  'tasklist /FI "IMAGENAME eq godot*"',
  'echo ===PORTS 9958-9975===',
  'netstat -ano | findstr /r ":99[5-7][0-9] "',
  'echo ===PORTS_DONE===',
  'echo SNAPSHOT_EXIT=%ERRORLEVEL%'
)
Set-Content -LiteralPath $bat -Value $batch -Encoding ASCII
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $bat -WorkingDirectory $Root `
      -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -Wait -PassThru
Write-Output ("final snapshot: process exit {0} -> {1}" -f $p.ExitCode, $out)
if (Test-Path -LiteralPath $err) { Write-Output ("  stderr bytes: {0}" -f (Get-Item -LiteralPath $err).Length) }
