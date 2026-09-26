param(
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp',
  [string]$Out  = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task093\diag-snake'
)
# diag_snake.ps1 -- the narrow probe for session defect S-3: after ForceTestState
# writes dir=1,0, what is the direction by the time the next call reads it?
# It writes the three scripts through the MCP tools (iron rule: the module is the
# only writer), builds, starts the game endpoint and dumps the board twice.
$ErrorActionPreference = 'Stop'
$engine = Join-Path $Root 'godot\bin\godot.windows.editor.x86_64.mono.console.exe'
$project = Join-Path $Root 'projects\snake'
$session = Join-Path $Root 'tools\sessions\snake\payload'
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
  Write-Output ("[{0}] {1}" -f $Tag, $text.Substring(0, [Math]::Min(500, $text.Length)))
}
function Tool($name, $arguments) {
  return (@{ jsonrpc = '2.0'; id = 1; method = 'tools/call'; params = @{ name = $name; arguments = $arguments } } | ConvertTo-Json -Compress -Depth 24)
}
function Script($path, $file) {
  return (Tool 'project_edit_script' @{ path = $path; content = [System.IO.File]::ReadAllText((Join-Path $session $file)) })
}

$editor = Start-Engine @('-e', '--path', $project, '--mcp-port=9888') 'editor'
if (-not (Wait-Port 9888 300000)) { throw 'the editor endpoint never came up' }
Start-Sleep -Seconds 5
Mcp 9888 'd01-segment' (Script 'res://src/SnakeSegment.cs' 'SnakeSegment.cs')
Mcp 9888 'd02-food'    (Script 'res://src/Food.cs' 'Food.cs')
Mcp 9888 'd03-game'    (Script 'res://src/SnakeGame.cs' 'SnakeGame.cs')
Mcp 9888 'd04-build'   (Tool 'project_build_csharp' @{ configuration = 'Debug'; timeout_ms = 300000; rescan = $true })
Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', ('taskkill /PID ' + $editor.Id + ' /T /F') -NoNewWindow -Wait -PassThru | Out-Null
Start-Sleep -Seconds 3

$game = Start-Engine @('--path', $project, '--mcp-port=9889') 'game'
if (-not (Wait-Port 9889 300000)) { throw 'the game endpoint never came up' }
Start-Sleep -Seconds 4
Mcp 9889 'd05-aim'  (Tool 'running_game_execute_gdscript' @{ code = "var m = get_parent()`nreturn m.ForceTestState(`"23,5|22,5|21,5;dir=1,0;food=0,0`")" })
Mcp 9889 'd06-dump-a' (Tool 'running_game_execute_gdscript' @{ code = 'return get_parent().Dump()' })
Start-Sleep -Milliseconds 700
Mcp 9889 'd07-dump-b' (Tool 'running_game_execute_gdscript' @{ code = 'return get_parent().Dump()' })
Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', ('taskkill /PID ' + $game.Id + ' /T /F') -NoNewWindow -Wait -PassThru | Out-Null
Write-Output 'done'
