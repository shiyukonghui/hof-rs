param(
  [Parameter(Mandatory=$true)][string]$Variant,   # mono | plain
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp'
)
# TASK-103: one variant build, started from cmd.exe (iron rule 3) with its
# stdout/stderr owned by Start-Process (iron rule 1: no shell redirection in this
# task). The .cmd scripts themselves write their own scons log to %TEMP%.
# Build SERIALLY (D62): never run the two variants at the same time.
$ErrorActionPreference = 'Stop'
$logs = Join-Path $Root 'recovery\work\task103\logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$out = Join-Path $logs ("build-$Variant.out.txt")
$err = Join-Path $logs ("build-$Variant.err.txt")
$bat = Join-Path $logs ("build-$Variant.cmd")
if (Test-Path -LiteralPath $out) { Remove-Item -LiteralPath $out -Force }
if (Test-Path -LiteralPath $err) { Remove-Item -LiteralPath $err -Force }
if ($Variant -eq 'mono') {
  $inner = 'modules\mcp_server\scripts\mcp057_build_mono.cmd'
} elseif ($Variant -eq 'plain') {
  $inner = 'modules\mcp_server\scripts\build_local.cmd -Force'
} else {
  throw "unknown variant '$Variant'"
}
$batch = @(
  '@echo off',
  ('cd /d "{0}\godot"' -f $Root),
  $inner,
  'echo BUILD_EXIT=%ERRORLEVEL%'
)
Set-Content -LiteralPath $bat -Value $batch -Encoding ASCII
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $bat -WorkingDirectory (Join-Path $Root 'godot') `
      -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -Wait -PassThru
$sw.Stop()
Write-Output ("BUILD {0}: process exit {1} in {2:n0} s" -f $Variant, $p.ExitCode, $sw.Elapsed.TotalSeconds)
if (Test-Path -LiteralPath $out) {
  Select-String -LiteralPath $out -Pattern 'BUILD_EXIT=|exit code =|log =|scons:' | ForEach-Object { Write-Output ('  | ' + $_.Line) }
}
if (Test-Path -LiteralPath $err) {
  $e = (Get-Item -LiteralPath $err).Length
  Write-Output ("  stderr bytes: {0}" -f $e)
  if ($e -gt 0) { Get-Content -LiteralPath $err -TotalCount 10 | ForEach-Object { Write-Output ('  ! ' + $_) } }
}
