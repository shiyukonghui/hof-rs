param(
  [string]$Root = 'F:\moonbit-hof-rs'
)
# TASK-102: a read-only look at the main repository's working tree, with the output
# owned by Start-Process (iron rule 1: no shell redirection).
$ErrorActionPreference = 'Stop'
$logs = Join-Path $Root 'godot-mcp\recovery\work\task102\logs'
$out = Join-Path $logs 'git-status.txt'
$err = Join-Path $logs 'git-status.err.txt'
$bat = Join-Path $logs 'git-status.cmd'
$batch = @(
  '@echo off',
  ('cd /d "{0}"' -f $Root),
  'git status --porcelain=v1',
  'echo STATUS_EXIT=%ERRORLEVEL%',
  'echo ---COUNT---',
  'git status --porcelain=v1 | find /c /v ""'
)
Set-Content -LiteralPath $bat -Value $batch -Encoding ASCII
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $bat -WorkingDirectory $Root `
      -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -Wait -PassThru
Get-Content -LiteralPath $out | ForEach-Object { Write-Output ('  | ' + $_) }
