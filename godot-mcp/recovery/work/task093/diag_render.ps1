param(
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp',
  [string]$Out  = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task093\diag-render',
  [int]$Port = 9889,
  [int]$WaitSeconds = 6
)
# diag_render.ps1 -- TASK-093 defect D-1: is the game window's root-viewport
# readback fresh? It starts ONE game endpoint with --mcp-trace + --mcp-capture,
# takes a screenshot, injects 20 input actions, waits, takes another screenshot,
# then decodes the PNGs.
#
# The answer is read from the files, not from the trace: two screenshots taken
# several seconds apart, across an input burst, must not be byte-identical.
#
# Iron rule 1: no shell redirection -- Start-Process owns stdout/stderr, and the
# engine is started from a generated .cmd (iron rule 3).
# Iron rule 2: nothing is removed outside $Out.
$ErrorActionPreference = 'Stop'
$engine  = Join-Path $Root 'godot\bin\godot.windows.editor.x86_64.mono.console.exe'
$game    = 'snake'
$project = Join-Path $Root ("projects\{0}" -f $game)
$trace   = Join-Path $Out 'trace-game.jsonl'
$shots   = Join-Path $Out 'shots'

New-Item -ItemType Directory -Force -Path $Out   | Out-Null
New-Item -ItemType Directory -Force -Path $shots | Out-Null

$batch = @(
  '@echo off',
  ('cd /d "{0}"' -f (Join-Path $Root 'godot')),
  ('"{0}" --path "{1}" --mcp-port={2} --mcp-trace="{3}" --mcp-capture=every_call --mcp-capture-dir="{4}" --mcp-capture-viewport=2d' -f $engine, $project, $Port, $trace, $shots)
)
$launcher = Join-Path $Out 'launch.cmd'
Set-Content -LiteralPath $launcher -Value $batch -Encoding ASCII
$proc = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $launcher -WorkingDirectory (Join-Path $Root 'godot') `
  -RedirectStandardOutput (Join-Path $Out 'engine.stdout.txt') -RedirectStandardError (Join-Path $Out 'engine.stderr.txt') -NoNewWindow -PassThru

$deadline = (Get-Date).AddSeconds(120)
$up = $false
while ((Get-Date) -lt $deadline -and -not $up) {
  $client = New-Object System.Net.Sockets.TcpClient
  try { $task = $client.ConnectAsync('127.0.0.1', $Port); if ($task.Wait(700) -and $client.Connected) { $up = $true } }
  catch { } finally { try { $client.Close() } catch { } }
  if (-not $up) { Start-Sleep -Milliseconds 500 }
}
if (-not $up) { throw "the game endpoint on $Port never came up" }

function Call-Tool([string]$Tag, [string]$Tool, $Arguments) {
  $body = (@{ jsonrpc = '2.0'; id = 1; method = 'tools/call'; params = @{ name = $Tool; arguments = $Arguments } } | ConvertTo-Json -Compress -Depth 24)
  $bf = Join-Path $Out ($Tag + '.request.json')
  Set-Content -LiteralPath $bf -Value $body -Encoding UTF8 -NoNewline
  $res = & curl.exe -s -X POST -H 'Content-Type: application/json' --data-binary ('@' + $bf) ("http://127.0.0.1:{0}/mcp" -f $Port)
  $text = ($res -join '')
  Set-Content -LiteralPath (Join-Path $Out ($Tag + '.json')) -Value $text -Encoding UTF8
  Write-Output ("[{0}] {1}" -f $Tag, $text.Substring(0, [Math]::Min(160, $text.Length)))
}

Start-Sleep -Seconds $WaitSeconds
Call-Tool 'r01-shot-a' 'running_game_capture_screenshot' @{ save_path = 'user://diag-render-a.png' }
Call-Tool 'r02-move'   'running_game_run_stress_test'    @{ action = 'snake_right'; count = 20 }
Start-Sleep -Seconds $WaitSeconds
Call-Tool 'r03-shot-b' 'running_game_capture_screenshot' @{ save_path = 'user://diag-render-b.png' }
Call-Tool 'r04-frames' 'running_game_capture_frames'     @{ count = 6; frame_interval = 30 }

Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', ('taskkill /PID ' + $proc.Id + ' /T /F') -NoNewWindow -Wait -PassThru | Out-Null
Start-Sleep -Seconds 1

$userDir = Join-Path $env:APPDATA ("Godot\app_userdata\{0}" -f $game)
$a = Join-Path $userDir 'diag-render-a.png'
$b = Join-Path $userDir 'diag-render-b.png'
Write-Output '--- the two screenshots ---'
foreach ($p in @($a, $b)) {
  if (Test-Path -LiteralPath $p) {
    $h = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash
    $len = (Get-Item -LiteralPath $p).Length
    Write-Output ('{0}  bytes={1}  sha256={2}' -f (Split-Path -Leaf $p), $len, $h.Substring(0, 16))
  } else {
    Write-Output ('{0}  MISSING' -f (Split-Path -Leaf $p))
  }
}
if ((Test-Path -LiteralPath $a) -and (Test-Path -LiteralPath $b)) {
  $same = ((Get-FileHash -LiteralPath $a -Algorithm SHA256).Hash -eq (Get-FileHash -LiteralPath $b -Algorithm SHA256).Hash)
  Write-Output ('IDENTICAL_BYTES={0}' -f $same)
  if ($same) { Write-Output 'DEFECT_D1=PRESENT (the game window readback is stale)' } else { Write-Output 'DEFECT_D1=GONE (the readback is fresh)' }
}
Write-Output '--- the engine capture files ---'
$pngs = @(Get-ChildItem -LiteralPath $shots -Filter *.png -File -ErrorAction SilentlyContinue)
$distinct = @($pngs | ForEach-Object { (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash } | Sort-Object -Unique)
Write-Output ('capture_pngs={0} distinct_sha256={1}' -f $pngs.Count, $distinct.Count)
if ($pngs.Count -gt 0 -and $distinct.Count -eq 1) {
  Write-Output 'DEFECT_D1_IN_CAPTURE=PRESENT (every before/after frame is the same image)'
}
Write-Output ('out={0}' -f $Out)
