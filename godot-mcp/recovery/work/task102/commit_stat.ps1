param(
  [string]$Root = 'F:\moonbit-hof-rs',
  [string]$Rev = 'HEAD',
  [string]$Out = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task102\logs\commit-stat.txt'
)
$ErrorActionPreference = 'Stop'
$err = $Out + '.err.txt'
$bat = $Out + '.cmd'
$batch = @(
  '@echo off',
  ('cd /d "{0}"' -f $Root),
  ('git show --stat --oneline {0} | findstr /C:"files changed"' -f $Rev),
  ('git show --stat --oneline {0} | find /c /v ""' -f $Rev)
)
Set-Content -LiteralPath $bat -Value $batch -Encoding ASCII
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $bat -WorkingDirectory $Root `
      -RedirectStandardOutput $Out -RedirectStandardError $err -NoNewWindow -Wait -PassThru
Get-Content -LiteralPath $Out | ForEach-Object { Write-Output ('  | ' + $_) }
