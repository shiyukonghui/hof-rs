param(
    [string]$Engine = 'H:\rebuild\godot\bin\godot.windows.editor.x86_64.mono.console.exe',
    [int]$GamePort = 9889,
    [string]$Root = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task090\probe-action',
    [string]$Proj = 'H:\rebuild\projects\mcpplay8'
)
# TASK-090 item C: the focused probe for the round-8 finding "the scenario's
# injected `mcp_right` action did not move the player".
#
# It separates the three possible causes with three independent reads:
#   1. does the node's `_input` fire at all for an injected InputEventAction?
#   2. is the action in the running InputMap (i.e. is the name known)?
#   3. does `Input.is_action_pressed` see it (the polling route rather than `_input`)?
# plus the executor's own view of the tree before/after.
$ErrorActionPreference = 'Stop'
$Logs = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs'
New-Item -ItemType Directory -Force -Path $Root | Out-Null
$script:Handles = @()
$script:Lines = New-Object System.Collections.Generic.List[string]

function Note([string]$t) { Write-Host $t; $script:Lines.Add($t) }

function Start-Engine([string[]]$Extra, [string]$LogName) {
    $out = Join-Path $Logs ('task090_probe_' + $LogName + '.stdout.txt')
    $err = Join-Path $Logs ('task090_probe_' + $LogName + '.stderr.txt')
    Remove-Item -Force $out, $err -ErrorAction SilentlyContinue
    $cmdline = '"' + $Engine + '" ' + ($Extra -join ' ')
    $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $cmdline -WorkingDirectory 'H:\rebuild\godot' `
        -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -PassThru
    $script:Handles += $p
    return $p
}
function Stop-Engine($p) {
    if ($null -eq $p) { return }
    try {
        $kids = Get-CimInstance Win32_Process -Filter ("ParentProcessId=" + $p.Id) -ErrorAction SilentlyContinue
        foreach ($k in @($kids)) { Stop-Process -Id $k.ProcessId -Force -ErrorAction SilentlyContinue }
        if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
    } catch { }
}
function Wait-Port([int]$Port, [int]$TimeoutMs) {
    $deadline = (Get-Date).AddMilliseconds($TimeoutMs)
    while ((Get-Date) -lt $deadline) {
        $c = New-Object System.Net.Sockets.TcpClient
        try { $t = $c.ConnectAsync('127.0.0.1', $Port); if ($t.Wait(700) -and $c.Connected) { $c.Close(); return $true } }
        catch { } finally { try { $c.Close() } catch { } }
        Start-Sleep -Milliseconds 500
    }
    return $false
}
function Invoke-Mcp([int]$Port, [string]$Body, [string]$Tag) {
    $f = Join-Path $Root ($Tag + '.request.json')
    Set-Content -LiteralPath $f -Value $Body -Encoding UTF8 -NoNewline
    $r = & curl.exe -s -X POST -H 'Content-Type: application/json' --data-binary ('@' + $f) ("http://127.0.0.1:{0}/mcp" -f $Port) 2>$null
    $text = ($r -join '')
    Set-Content -LiteralPath (Join-Path $Root ($Tag + '.json')) -Value $text -Encoding UTF8
    Note ("  [{0}] {1}" -f $Tag, $text)
    return $text
}
function Mcp-Call([int]$Id, [string]$Tool, $Arguments) {
    return (@{ jsonrpc = '2.0'; id = $Id; method = 'tools/call'; params = @{ name = $Tool; arguments = $Arguments } } |
        ConvertTo-Json -Compress -Depth 12)
}

$game = Start-Engine -Extra @('--path', $Proj, ('--mcp-port=' + $GamePort)) -LogName 'game'
if (-not (Wait-Port -Port $GamePort -TimeoutMs 300000)) { Note 'FATAL: game endpoint never came up'; }
else {
    Start-Sleep -Seconds 6
    # 1. baseline: last_input is empty, moves is 0
    Invoke-Mcp $GamePort (Mcp-Call 401 'running_game_execute_gdscript' @{ code = 'var m = get_parent()
return [m.last_input, m.moves]' }) 'p01-baseline' | Out-Null
    # 2. the InputMap knows the action?
    Invoke-Mcp $GamePort (Mcp-Call 402 'running_game_execute_gdscript' @{ code = 'return InputMap.has_action("mcp_right")' }) 'p02-inputmap-has-action' | Out-Null
    # 3. inject the very same event the scenario injects, from inside the game
    Invoke-Mcp $GamePort (Mcp-Call 403 'running_game_execute_gdscript' @{ code = 'var e = InputEventAction.new()
e.action = "mcp_right"
e.pressed = true
e.strength = 1.0
Input.parse_input_event(e)
return "injected"' }) 'p03-inject-direct' | Out-Null
    Start-Sleep -Seconds 1
    Invoke-Mcp $GamePort (Mcp-Call 404 'running_game_execute_gdscript' @{ code = 'var m = get_parent()
return [m.last_input, m.moves, m.get_node("Player").position.x]' }) 'p04-after-direct' | Out-Null
    # 4. the scenario's own tool, one input step only
    Invoke-Mcp $GamePort (Mcp-Call 405 'running_game_run_test_scenario' @{ steps = @(@{ type = 'input'; action = 'mcp_right'; pressed = $true }, @{ type = 'wait'; seconds = 0.3 }) }) 'p05-scenario-input' | Out-Null
    Start-Sleep -Seconds 1
    Invoke-Mcp $GamePort (Mcp-Call 406 'running_game_execute_gdscript' @{ code = 'var m = get_parent()
return [m.last_input, m.moves, m.get_node("Player").position.x]' }) 'p06-after-scenario' | Out-Null
    # 5. the polling route: is_action_pressed inside the tree
    Invoke-Mcp $GamePort (Mcp-Call 407 'running_game_execute_gdscript' @{ code = 'return Input.is_action_pressed("mcp_right")' }) 'p07-poll' | Out-Null
    Start-Sleep -Seconds 2
}
Stop-Engine $game
Start-Sleep -Seconds 1
foreach ($h in $script:Handles) { Stop-Engine $h }
Set-Content -LiteralPath (Join-Path $Root 'probe.txt') -Value $script:Lines -Encoding UTF8
Note ('summary: ' + (Join-Path $Root 'probe.txt'))
