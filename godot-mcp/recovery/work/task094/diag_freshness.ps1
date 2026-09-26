param(
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp',
  [string]$Game = 'snake',
  [string]$Driver = '',
  [string]$ExtraEngineArgs = '',
  [string]$Tag = '',
  [string]$Session = '',
  [string]$Capture = 'every_call',
  [int]$Port = 9889,
  [int]$WaitSeconds = 6
)
# diag_freshness.ps1 -- TASK-094, defect D-1: the minimal reproducer.
#
# It starts ONE game process with capture on, replays
# `recovery\work\task094\sessions\repro\session.json` (three `set_node_property`
# calls that move SnakeSeg00 by 552 px and then to another row, with a 500 ms
# settle and a screenshot after each), and then answers one question from the
# files: are the three pictures different?
#
# `-Driver` and `-ExtraEngineArgs` exist so the same session can be replayed
# under a different rendering driver or render-thread mode.
#
# Iron rule 1: no shell redirection -- Start-Process owns stdout/stderr.
# Iron rule 2: nothing is removed outside $Out.
# Iron rule 3: the engine is started through a generated .cmd.
$ErrorActionPreference = 'Stop'

if (-not $Tag) {
  $Tag = 'run'
  if ($Driver) { $Tag = "driver-$Driver" }
  if ($ExtraEngineArgs) { $Tag = $Tag + '-' + ($ExtraEngineArgs -replace '[^A-Za-z0-9]', '') }
}
$Out = Join-Path $Root ("recovery\work\task094\freshness\{0}-{1}" -f $Game, $Tag)
$shots = Join-Path $Out 'shots'
New-Item -ItemType Directory -Force -Path $Out   | Out-Null
New-Item -ItemType Directory -Force -Path $shots | Out-Null

function Say([string]$t) { Write-Host $t }

$engine  = Join-Path $Root 'godot\bin\godot.windows.editor.x86_64.mono.console.exe'
$project = Join-Path $Root ("projects\{0}" -f $Game)
$trace   = Join-Path $Out 'trace.jsonl'
if (-not $Session) { $Session = Join-Path $Root 'recovery\work\task094\sessions\repro\session.json' }

$extra = @()
if ($Driver) { $extra += ('--rendering-driver ' + $Driver) }
if ($ExtraEngineArgs) { $extra += $ExtraEngineArgs }

$switches = @(
  ('--path "' + $project + '"'),
  ('--mcp-port=' + $Port),
  ('--mcp-trace="' + $trace + '"'),
  ('--mcp-capture=' + $Capture),
  ('--mcp-capture-dir="' + $shots + '"'),
  '--mcp-capture-viewport=2d'
) + $extra

$launcher = Join-Path $Out 'launch.cmd'
Set-Content -LiteralPath $launcher -Encoding ASCII -Value @(
  '@echo off',
  ('cd /d "{0}"' -f (Join-Path $Root 'godot')),
  ('"{0}" {1}' -f $engine, ($switches -join ' '))
)
Say ("cmdline: {0}" -f ($switches -join ' '))
$proc = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $launcher -WorkingDirectory (Join-Path $Root 'godot') `
  -RedirectStandardOutput (Join-Path $Out 'engine.stdout.txt') -RedirectStandardError (Join-Path $Out 'engine.stderr.txt') -NoNewWindow -PassThru

$deadline = (Get-Date).AddSeconds(120)
$up = $false
while ((Get-Date) -lt $deadline -and -not $up) {
  $c = New-Object System.Net.Sockets.TcpClient
  try { $t = $c.ConnectAsync('127.0.0.1', $Port); if ($t.Wait(700) -and $c.Connected) { $up = $true } }
  catch { } finally { try { $c.Close() } catch { } }
  if (-not $up) { Start-Sleep -Milliseconds 500 }
}
if (-not $up) { throw "the game endpoint on $Port never came up" }

function Call-Tool([string]$TagName, [string]$Tool, $Arguments) {
  $body = (@{ jsonrpc = '2.0'; id = 1; method = 'tools/call'; params = @{ name = $Tool; arguments = $Arguments } } | ConvertTo-Json -Compress -Depth 24)
  $bf = Join-Path $Out ($TagName + '.request.json')
  Set-Content -LiteralPath $bf -Value $body -Encoding UTF8 -NoNewline
  $res = & curl.exe -s -X POST -H 'Content-Type: application/json' --data-binary ('@' + $bf) ("http://127.0.0.1:{0}/mcp" -f $Port)
  $text = ($res -join '')
  Set-Content -LiteralPath (Join-Path $Out ($TagName + '.json')) -Value $text -Encoding UTF8
  Say ("  [{0}] {1}" -f $TagName, $text.Substring(0, [Math]::Min(120, $text.Length)))
}

Start-Sleep -Seconds $WaitSeconds

$doc = Get-Content -LiteralPath $Session -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($c in $doc.calls) {
  if ($c.sleep_ms) { Start-Sleep -Milliseconds ([int]$c.sleep_ms); continue }
  Call-Tool $c.tag $c.tool $c.arguments
}

Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', ('taskkill /PID ' + $proc.Id + ' /T /F') -NoNewWindow -Wait -PassThru | Out-Null
Start-Sleep -Seconds 1

$userDir = Join-Path $env:APPDATA ("Godot\app_userdata\{0}" -f $Game)
$hashes = @{}
Say '--- the three pictures (user://) ---'
foreach ($n in @('a','b','c')) {
  $p = Join-Path $userDir ("repro-{0}.png" -f $n)
  if (Test-Path -LiteralPath $p) {
    $h = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash
    $hashes[$n] = $h
    Say ('  repro-{0}.png  bytes={1}  sha256={2}' -f $n, (Get-Item -LiteralPath $p).Length, $h.Substring(0, 16))
  } else { Say ('  repro-{0}.png  MISSING' -f $n) }
}
$ab = ($null -ne $hashes['a']) -and ($hashes['a'] -ne $hashes['b'])
$ac = ($null -ne $hashes['a']) -and ($hashes['a'] -ne $hashes['c'])
$bc = ($null -ne $hashes['b']) -and ($hashes['b'] -ne $hashes['c'])
Say ("A_vs_B_DIFFERENT = {0}" -f $ab)
Say ("A_vs_C_DIFFERENT = {0}" -f $ac)
Say ("B_vs_C_DIFFERENT = {0}" -f $bc)
if ($ab -and $ac -and $bc) { Say 'D1_VERDICT=GONE (the readback follows the scene)' } else { Say 'D1_VERDICT=PRESENT (the readback is stale)' }

$pngs = @(Get-ChildItem -LiteralPath $shots -Filter *.png -File -ErrorAction SilentlyContinue)
$distinct = @($pngs | ForEach-Object { (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash } | Sort-Object -Unique)
Say ("capture_pngs={0} distinct_sha256={1}" -f $pngs.Count, $distinct.Count)
Say ("out={0}" -f $Out)
