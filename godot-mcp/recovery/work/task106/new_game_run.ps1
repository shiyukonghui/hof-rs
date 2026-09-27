param(
  [Parameter(Mandatory=$true)][string]$Name,
  [Parameter(Mandatory=$true)][string]$Class,
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp'
)
# TASK-106: instantiate one game project from the tracked template, started from
# cmd.exe (iron rule 3) with its stdout/stderr owned by Start-Process (iron rule 1).
#
# Adapted from recovery/work/task103/new_game_run.ps1; the log directory is this
# task's own.
$ErrorActionPreference = 'Stop'
$logs = Join-Path $Root 'recovery\work\task106\logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$out = Join-Path $logs ("new-game-$Name.out.txt")
$err = Join-Path $logs ("new-game-$Name.err.txt")
$bat = Join-Path $logs ("new-game-$Name.cmd")
if (Test-Path -LiteralPath $out) { Remove-Item -LiteralPath $out -Force }
if (Test-Path -LiteralPath $err) { Remove-Item -LiteralPath $err -Force }
$batch = @(
  '@echo off',
  ('powershell -NoProfile -ExecutionPolicy Bypass -File "{0}\tools\new_game.ps1" -Name {1} -Class {2}' -f $Root, $Name, $Class),
  'echo NEWGAME_EXIT=%ERRORLEVEL%'
)
Set-Content -LiteralPath $bat -Value $batch -Encoding ASCII
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $bat -WorkingDirectory $Root `
      -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -Wait -PassThru
Write-Output ("new_game {0}: process exit {1}" -f $Name, $p.ExitCode)
if (Test-Path -LiteralPath $out) {
  Select-String -LiteralPath $out -Pattern 'created|REFUSED|NEWGAME_EXIT|placeholder files left' | ForEach-Object { Write-Output ('  | ' + $_.Line) }
}
if (Test-Path -LiteralPath $err) {
  $e = (Get-Item -LiteralPath $err).Length
  if ($e -gt 0) { Get-Content -LiteralPath $err -TotalCount 10 | ForEach-Object { Write-Output ('  ! ' + $_) } }
}
