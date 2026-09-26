param(
  [Parameter(Mandatory=$true)][string]$Tag,
  [Parameter(Mandatory=$true)][string]$EngineArgs,
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp'
)
# TASK-103: run the engine with its stdout/stderr owned by Start-Process (iron
# rule 1: no shell redirection) and started from cmd.exe (iron rule 3).
$ErrorActionPreference = 'Stop'
$logs = Join-Path $Root ("recovery\work\task103\logs\{0}" -f $Tag)
$out = $logs + '.stdout.txt'
$err = $logs + '.stderr.txt'
$bat = $logs + '.cmd'
$engine = Join-Path $Root 'godot\bin\godot.windows.editor.x86_64.mono.console.exe'
$batch = @(
  '@echo off',
  ('cd /d "{0}\godot"' -f $Root),
  ('"{0}" {1}' -f $engine, $EngineArgs),
  'echo ENGINE_EXIT=%ERRORLEVEL%'
)
Set-Content -LiteralPath $bat -Value $batch -Encoding ASCII
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $bat -WorkingDirectory (Join-Path $Root 'godot') `
      -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -Wait -PassThru
$sw.Stop()
$echoed = ''
$m = Select-String -LiteralPath $out -Pattern 'ENGINE_EXIT=(-?\d+)' | Select-Object -Last 1
if ($m) { $echoed = $m.Matches[0].Groups[1].Value }
Write-Output ("{0}: process exit {1} / echoed {2} in {3:n0} s -> {4}" -f $Tag, $p.ExitCode, $echoed, $sw.Elapsed.TotalSeconds, $out)
Select-String -LiteralPath $out -Pattern 'passed|failed|SUCCESS|FAILED|ERROR' | Select-Object -First 25 |
  ForEach-Object { Write-Output ('  | ' + $_.Line) }
$e = (Get-Item -LiteralPath $err).Length
Write-Output ("  stderr bytes: {0}" -f $e)
