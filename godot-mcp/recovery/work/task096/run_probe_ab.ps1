param(
  [Parameter(Mandatory=$true)][string]$Exe,
  [Parameter(Mandatory=$true)][string]$Tag,
  [string]$Project = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task096\probe',
  [string]$Extra = '',
  [int]$TimeoutSeconds = 120
)
# run_probe_ab.ps1 -- TASK-096 A: run the *same* probe project bytes on one engine.
#
# Iron rule 1: no shell redirection -- Start-Process owns stdout/stderr.
# Iron rule 2: the only writes are inside recovery\work\task096\runs\<Tag>.
# Iron rule 3: the engine is started through cmd.exe from a generated .cmd.
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Exe)) { throw "missing engine: $Exe" }
if (-not (Test-Path -LiteralPath $Project)) { throw "missing project: $Project" }

$Out = Join-Path 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task096\runs' $Tag
New-Item -ItemType Directory -Force -Path $Out | Out-Null

function Say([string]$t) { Write-Host $t }

$launcher = Join-Path $Out 'launch.cmd'
$batch = @(
  '@echo off',
  ('cd /d "{0}"' -f (Split-Path -Parent $Exe)),
  ('"{0}" --path "{1}" {2}' -f $Exe, $Project, $Extra),
  'echo PROBE_EXIT=%ERRORLEVEL%'
)
Set-Content -LiteralPath $launcher -Encoding ASCII -Value $batch
$outFile = Join-Path $Out 'stdout.txt'
$errFile = Join-Path $Out 'stderr.txt'
if (Test-Path -LiteralPath $outFile) { Remove-Item -LiteralPath $outFile -Force }
if (Test-Path -LiteralPath $errFile) { Remove-Item -LiteralPath $errFile -Force }

$before = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'Godot*' } | Select-Object -ExpandProperty Id)
Say ("tag      : {0}" -f $Tag)
Say ("engine   : {0}" -f $Exe)
Say ("project  : {0}" -f $Project)
Say ("godot pids before: {0}" -f (@($before) -join ','))

$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $launcher `
      -WorkingDirectory (Split-Path -Parent $Exe) `
      -RedirectStandardOutput $outFile -RedirectStandardError $errFile -NoNewWindow -PassThru

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while (-not $p.HasExited -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 500 }
if (-not $p.HasExited) {
  Say ("TIMEOUT after {0}s -- killing the tree" -f $TimeoutSeconds)
}
Say ("process exit: {0}" -f $p.ExitCode)

# The console launcher spawns the real engine; make sure nothing of ours survives.
Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'Godot*' } | ForEach-Object {
  $id = $_.Id
  try {
    Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', ('taskkill /PID ' + $id + ' /T /F') `
      -RedirectStandardOutput (Join-Path $Out 'taskkill.stdout.txt') `
      -RedirectStandardError (Join-Path $Out 'taskkill.stderr.txt') -NoNewWindow -Wait -PassThru | Out-Null
  } catch { }
}

Say '--- PROBE lines ---'
if (Test-Path -LiteralPath $outFile) {
  Select-String -LiteralPath $outFile -Pattern 'PROBE096' | ForEach-Object { Say $_.Line }
}
Say '--- stderr (first 20) ---'
if (Test-Path -LiteralPath $errFile) {
  Get-Content -LiteralPath $errFile -TotalCount 20 | ForEach-Object { Say $_ }
}
$after = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'Godot*' } | Select-Object -ExpandProperty Id)
Say ("godot pids after: {0}" -f (@($after) -join ','))
Say ("out={0}" -f $Out)
