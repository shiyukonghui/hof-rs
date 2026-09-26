param(
  [string]$Root = 'F:\moonbit-hof-rs'
)
# TASK-103: the two-repository closing snapshot, started from cmd.exe (iron rule 3)
# with its output owned by Start-Process (iron rule 1). Prints, for each repository:
# HEAD, git log --oneline -8, git status --short, and (engine) the remote-tracking
# ref, so "the push landed" and "the tree is clean" are both readable from one file.
$ErrorActionPreference = 'Stop'
$logs = Join-Path $Root 'godot-mcp\recovery\work\task103\logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$out = Join-Path $logs 'git-final-main.txt'
$err = Join-Path $logs 'git-final-main.err.txt'
$bat = Join-Path $logs 'git-final-main.cmd'
if (Test-Path -LiteralPath $out) { Remove-Item -LiteralPath $out -Force }
if (Test-Path -LiteralPath $err) { Remove-Item -LiteralPath $err -Force }
$engine = Join-Path $Root 'godot-mcp\godot'
$rows = @(
  '@echo off',
  'setlocal enabledelayedexpansion',
  ('echo ===== MAIN REPO %MAIN%' -replace '%MAIN%', $Root),
  ('cd /d "{0}"' -f $Root),
  'echo --- rev-parse HEAD & git rev-parse HEAD',
  'echo --- log --oneline -8 & git log --oneline -8',
  'echo --- status --short & git status --short',
  ('echo ===== ENGINE REPO {0}' -f $engine),
  ('cd /d "{0}"' -f $engine),
  'echo --- rev-parse HEAD & git rev-parse HEAD',
  'echo --- rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild & git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild',
  'echo --- log --oneline -8 & git log --oneline -8',
  'echo --- status --short & git status --short',
  'echo --- branch & git rev-parse --abbrev-ref HEAD',
  'echo SNAPSHOT_EXIT=%ERRORLEVEL%'
)
Set-Content -LiteralPath $bat -Value $rows -Encoding ASCII
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $bat -WorkingDirectory $Root `
      -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -Wait -PassThru
Write-Output ("snapshot: process exit {0} -> {1}" -f $p.ExitCode, $out)
Get-Content -LiteralPath $out | ForEach-Object { Write-Output ('  | ' + $_) }
