param(
  [string]$Tag = 'task102-doconly',
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp'
)
# TASK-102: run the gate runner's preflight through cmd.exe (iron rule 3) with its
# stdout/stderr owned by Start-Process (iron rule 1: no shell redirection anywhere).
$ErrorActionPreference = 'Stop'
$logs = Join-Path $Root 'recovery\work\task102\logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$out = Join-Path $logs ("gates-$Tag.txt")
$err = Join-Path $logs ("gates-$Tag.err.txt")
$bat = Join-Path $logs ("gates-$Tag.cmd")
if (Test-Path -LiteralPath $out) { Remove-Item -LiteralPath $out -Force }
if (Test-Path -LiteralPath $err) { Remove-Item -LiteralPath $err -Force }
$batch = @(
  '@echo off',
  ('cd /d "{0}"' -f $Root),
  ('powershell -NoProfile -ExecutionPolicy Bypass -File "{0}\tools\run_gates.ps1" -Tag {1}' -f $Root, $Tag),
  'echo GATES_EXIT=%ERRORLEVEL%'
)
Set-Content -LiteralPath $bat -Value $batch -Encoding ASCII
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $bat -WorkingDirectory $Root `
      -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -Wait -PassThru
Write-Output ("run_gates -Tag {0}: process exit {1} -> {2}" -f $Tag, $p.ExitCode, $out)
if (Test-Path -LiteralPath $out) {
  Get-Content -LiteralPath $out | ForEach-Object { Write-Output ('  | ' + $_) }
}
if ((Test-Path -LiteralPath $err) -and (Get-Item -LiteralPath $err).Length -gt 0) {
  Get-Content -LiteralPath $err | ForEach-Object { Write-Output ('  ! ' + $_) }
}
