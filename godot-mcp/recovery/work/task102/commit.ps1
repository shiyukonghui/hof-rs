param(
  [Parameter(Mandatory=$true)][string]$MessageFile,
  [string]$Root = 'F:\moonbit-hof-rs'
)
# TASK-102: commit the main repository with the message read from a file.
# Iron rule 1: no shell redirection -- the operations log is owned by Start-Process.
$ErrorActionPreference = 'Stop'
$out = Join-Path $Root 'godot-mcp\recovery\work\task102\logs\git-commit.txt'
$err = Join-Path $Root 'godot-mcp\recovery\work\task102\logs\git-commit.err.txt'
$bat = Join-Path $Root 'godot-mcp\recovery\work\task102\logs\git-commit.cmd'
$batch = @(
  '@echo off',
  ('cd /d "{0}"' -f $Root),
  'git add -A',
  ('git commit -F "{0}"' -f $MessageFile),
  'echo COMMIT_EXIT=%ERRORLEVEL%'
)
Set-Content -LiteralPath $bat -Value $batch -Encoding ASCII
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $bat -WorkingDirectory $Root `
      -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -Wait -PassThru
Write-Output ("git commit: process exit {0}" -f $p.ExitCode)
Get-Content -LiteralPath $out -Tail 8 | ForEach-Object { Write-Output ('  | ' + $_) }
if ((Get-Item -LiteralPath $err).Length -gt 0) {
  Get-Content -LiteralPath $err | ForEach-Object { Write-Output ('  ! ' + $_) }
}
