param(
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp',
  [string]$Out  = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task093\diag-breakout'
)
# diag_breakout.ps1 -- the narrow probe for the Breakout bounce question: aim the
# ball straight down onto the middle of the paddle and ask, one frame at a time,
# what the contact test compares. It writes the scripts through the MCP tools
# (the module stays the only writer), builds, starts the game endpoint and reads
# the test at several points of the fall.
$ErrorActionPreference = 'Stop'
$engine = Join-Path $Root 'godot\bin\godot.windows.editor.x86_64.mono.console.exe'
$project = Join-Path $Root 'projects\breakout'
$payload = Join-Path $Root 'tools\sessions\breakout\payload'
New-Item -ItemType Directory -Force -Path $Out | Out-Null

function Start-Engine([string[]]$Extra, [string]$LogName) {
  $b = Join-Path $Out ("launch-{0}.cmd" -f $LogName)
  $batch = @('@echo off', ('cd /d "{0}"' -f (Join-Path $Root 'godot')), ('"' + $engine + '" ' + ($Extra -join ' ')))
  Set-Content -LiteralPath $b -Value $batch -Encoding ASCII
  return Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $b -WorkingDirectory (Join-Path $Root 'godot') `
    -RedirectStandardOutput (Join-Path $Out ("engine-{0}.stdout.txt" -f $LogName)) `
    -RedirectStandardError (Join-Path $Out ("engine-{0}.stderr.txt" -f $LogName)) -NoNewWindow -PassThru
}
function Wait-Port([int]$Port, [int]$TimeoutMs) {
  $deadline = (Get-Date).AddMilliseconds($TimeoutMs)
  while ((Get-Date) -lt $deadline) {
    $client = New-Object System.Net.Sockets.TcpClient
    try { $task = $client.ConnectAsync('127.0.0.1', $port); if ($task.Wait(700) -and $client.Connected) { $client.Close(); return $true } }
    catch { } finally { try { $client.Close() } catch { } }
    Start-Sleep -Milliseconds 500
  }
  return $false
}
function Mcp([int]$Port, [string]$Tag, [string]$Body) {
  $bf = Join-Path $Out ($Tag + '.request.json')
  Set-Content -LiteralPath $bf -Value $Body -Encoding UTF8 -NoNewline
  $res = & curl.exe -s -X POST -H 'Content-Type: application/json' --data-binary ('@' + $bf) ("http://127.0.0.1:{0}/mcp" -f $Port)
  $text = ($res -join '')
  Set-Content -LiteralPath (Join-Path $Out ($Tag + '.json')) -Value $text -Encoding UTF8
  Write-Output ("[{0}] {1}" -f $Tag, $text.Substring(0, [Math]::Min(420, $text.Length)))
}
function Tool($name, $arguments) {
  return (@{ jsonrpc = '2.0'; id = 1; method = 'tools/call'; params = @{ name = $name; arguments = $arguments } } | ConvertTo-Json -Compress -Depth 24)
}
function WriteScript($path, $file) {
  return (Tool 'project_edit_script' @{ path = $path; content = [System.IO.File]::ReadAllText((Join-Path $payload $file)) })
}

$editor = Start-Engine @('-e', '--path', $project, '--mcp-port=9888') 'editor'
if (-not (Wait-Port 9888 300000)) { throw 'the editor endpoint never came up' }
Start-Sleep -Seconds 5
Mcp 9888 'p01-brick'  (WriteScript 'res://src/Brick.cs' 'Brick.cs')
Mcp 9888 'p02-paddle' (WriteScript 'res://src/Paddle.cs' 'Paddle.cs')
Mcp 9888 'p03-game'   (WriteScript 'res://src/BreakoutGame.cs' 'BreakoutGame.cs')
Mcp 9888 'p04-build'  (Tool 'project_build_csharp' @{ configuration = 'Debug'; timeout_ms = 300000; rescan = $true })
Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', ('taskkill /PID ' + $editor.Id + ' /T /F') -NoNewWindow -Wait -PassThru | Out-Null
Start-Sleep -Seconds 3

$game = Start-Engine @('--path', $project, '--mcp-port=9889') 'game'
if (-not (Wait-Port 9889 300000)) { throw 'the game endpoint never came up' }
Start-Sleep -Seconds 4
Mcp 9889 'p05-shot-a' (Tool 'running_game_capture_screenshot' @{ save_path = 'user://bk-a.png' })
Mcp 9889 'p06-aim'    (Tool 'running_game_execute_gdscript' @{ code = "return get_parent().AimBall(8.0, -30.0, 0.0, 276.0)" })
Mcp 9889 'p07-test-0' (Tool 'running_game_execute_gdscript' @{ code = 'return get_parent().PaddleTest()' })
Mcp 9889 'p08-aim2'   (Tool 'running_game_execute_gdscript' @{ code = "return get_parent().AimBall(8.0, 20.0, 0.0, 276.0)" })
Mcp 9889 'p09-test-1' (Tool 'running_game_execute_gdscript' @{ code = 'return get_parent().PaddleTest()' })
Start-Sleep -Milliseconds 300
Mcp 9889 'p10-test-2' (Tool 'running_game_execute_gdscript' @{ code = 'return get_parent().PaddleTest()' })
Mcp 9889 'p11-shot-b' (Tool 'running_game_capture_screenshot' @{ save_path = 'user://bk-b.png' })
Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', ('taskkill /PID ' + $game.Id + ' /T /F') -NoNewWindow -Wait -PassThru | Out-Null
Write-Output '--- game stdout ---'
Get-Content (Join-Path $Out 'engine-game.stdout.txt') | Select-String -Pattern 'BREAKOUT' | Select-Object -First 30 | ForEach-Object { $_.Line }
Write-Output 'done'
