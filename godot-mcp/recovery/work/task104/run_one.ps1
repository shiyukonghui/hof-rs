param(
  [Parameter(Mandatory=$true)][string]$Game,
  [Parameter(Mandatory=$true)][string]$RunTag,
  [Parameter(Mandatory=$true)][int]$EditorPort,
  [Parameter(Mandatory=$true)][int]$GamePort,
  [string]$Session = '',
  [switch]$SkipReport,
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp'
)
# TASK-104: launch one game session through cmd.exe (iron rule 3) and own its
# stdout/stderr with Start-Process -RedirectStandardOutput (iron rule 1: no shell
# redirection anywhere).
$ErrorActionPreference = 'Stop'
$logs = Join-Path $Root 'recovery\work\task104\logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$out = Join-Path $logs ("run-$Game-$RunTag.out.txt")
$err = Join-Path $logs ("run-$Game-$RunTag.err.txt")
$bat = Join-Path $logs ("run-$Game-$RunTag.cmd")
if (Test-Path -LiteralPath $out) { Remove-Item -LiteralPath $out -Force }
if (Test-Path -LiteralPath $err) { Remove-Item -LiteralPath $err -Force }
$psArgs = '-NoProfile -ExecutionPolicy Bypass -File "{0}\tools\run_game_session.ps1" -Game {1} -RunTag {2} -EditorPort {3} -GamePort {4}' -f $Root, $Game, $RunTag, $EditorPort, $GamePort
if ($Session) { $psArgs += ' -Session "{0}"' -f $Session }
if ($SkipReport) { $psArgs += ' -SkipReport' }
$batch = @(
  '@echo off',
  ('powershell ' + $psArgs),
  'echo RUN_EXIT=%ERRORLEVEL%'
)
Set-Content -LiteralPath $bat -Value $batch -Encoding ASCII
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $bat -WorkingDirectory $Root `
      -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -Wait -PassThru
Write-Output ("RUN {0} {1}: process exit {2} -> {3}" -f $Game, $RunTag, $p.ExitCode, $out)
if (Test-Path -LiteralPath $out) {
  Select-String -LiteralPath $out -Pattern 'RUN_EXIT=|FATAL|import   :|report: exit' |
    ForEach-Object { Write-Output ('  | ' + $_.Line) }
}
if (Test-Path -LiteralPath $err) {
  $e = (Get-Item -LiteralPath $err).Length
  Write-Output ("  stderr bytes: {0}" -f $e)
  if ($e -gt 0) { Get-Content -LiteralPath $err -TotalCount 12 | ForEach-Object { Write-Output ('  ! ' + $_) } }
}
