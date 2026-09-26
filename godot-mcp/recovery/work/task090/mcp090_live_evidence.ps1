param(
    [string]$Engine = 'H:\rebuild\godot\bin\godot.windows.editor.x86_64.mono.console.exe',
    [int]$EditorPort = 9888,
    [int]$GamePort = 9889,
    [string]$Root = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task090\live-after',
    [string]$Proj = 'H:\rebuild\projects\mcpplay8',
    # Run-specific values, so "the first call really changes something" stays true
    # on a second run over the same project. The CALL SET is identical; only the
    # text/setting values differ per run.
    [string]$RunTag = 'after-run'
)
# =============================================================================
#  mcp090_live_evidence.ps1 -- TASK-090 item C: the round-8 session.
#
#  A REAL multi-step orchestration against a real (small) game, on both
#  endpoints, with `--mcp-trace` + `--mcp-capture=every_call` on:
#
#    (1) drive the game loop: the executor reads and writes the RUNNING scene
#        tree (position / colour / text), so the picture has to move;
#    (2) batch node writes: several node/property writes in one session, each
#        with its own pixel and/or file evidence;
#    (3) input simulation + assertions: a simulated Button click and a
#        multi-step scenario (injected `mcp_right` action -> wait -> assert);
#    (4) resource/scene file creates and deletes and project-setting writes,
#        including calls that MUST fail, so the failure `data` payload can be
#        read back from the trace.
#
#  The project is RESET to a canonical state before the session, so the same
#  call set can be replayed for a before/after comparison.
#
#  Iron rule 2: no shell redirection - files are written with Set-Content, the
#  engines are started with Start-Process (which owns their stdout/stderr).
#  Iron rule 4: every engine is started through cmd.exe.
#  Iron rule 1: nothing outside H:\rebuild and ...\mcp-recovery\ is written.
# =============================================================================
$ErrorActionPreference = 'Stop'
$Logs = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs'
New-Item -ItemType Directory -Force -Path $Root | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root 'shots-editor') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root 'shots-game') | Out-Null

$script:Handles = @()
$script:Lines = New-Object System.Collections.Generic.List[string]
$script:IndexOfCalls = New-Object System.Collections.Generic.List[string]

$PristineProjectGodot = @'
; Engine configuration file.
; MCP round-8 mini game project (TASK-090 item C).

config_version=5

[application]

config/name="McpRound8Mini"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.8")
config/description="MCP round-8 mini game (initial)"

[display]

window/size/viewport_width=800
window/size/viewport_height=600

[dotnet]

project/assembly_name="McpRound8Mini"
'@

$PristineMainTscn = @'
[gd_scene format=3]

[ext_resource type="Script" path="res://main.gd" id="1_main"]

[node name="Main" type="Node2D"]
script = ExtResource("1_main")

[node name="Sky" type="ColorRect" parent="."]
offset_right = 800.0
offset_bottom = 600.0
color = Color(0.1, 0.12, 0.2, 1)

[node name="Player" type="ColorRect" parent="."]
offset_left = 100.0
offset_top = 220.0
offset_right = 180.0
offset_bottom = 300.0
color = Color(0.9, 0.1, 0.9, 1)

[node name="HUD" type="Label" parent="."]
offset_left = 24.0
offset_top = 20.0
offset_right = 620.0
offset_bottom = 64.0
text = "MCP round-8 mini game"

[node name="MoveButton" type="Button" parent="."]
offset_left = 24.0
offset_top = 500.0
offset_right = 160.0
offset_bottom = 540.0
text = "Move"
'@

$PristineMainGd = @'
extends Node2D
# MCP round-8 mini game (TASK-090 item C).
var moves := 0
var last_input := ""

func _ready() -> void:
	$MoveButton.pressed.connect(_on_move_button_pressed)
	# TASK-090 item C, round-8 finding: the injected `mcp_right` action is
	# delivered to `_input` even when the InputMap does not declare it, but
	# `event.is_action_pressed("mcp_right")` resolves through
	# `InputMap::event_get_action_status`, which answers false for an action the
	# InputMap does not have (core/input/input_map.cpp:291-292). Declaring the
	# action is what makes the scenario's input step observable - and that is the
	# game's job, not the tool's.
	if not InputMap.has_action("mcp_right"):
		InputMap.add_action("mcp_right")
	print("MCP090_MINIGAME_READY name=", name, " player=", $Player.position, " mcp_right_in_map=", InputMap.has_action("mcp_right"))

func move_player(dx: float) -> float:
	moves += 1
	var player: ColorRect = $Player
	player.position.x += dx
	print("MCP090_MOVE moves=", moves, " x=", player.position.x)
	return player.position.x

func set_hud(new_text: String) -> void:
	$HUD.text = new_text

func set_player_color(new_color: Color) -> void:
	$Player.color = new_color

func _input(event: InputEvent) -> void:
	if event.is_action_pressed("mcp_right"):
		last_input = "mcp_right"
		move_player(25.0)

func _on_move_button_pressed() -> void:
	last_input = "button"
	move_player(10.0)
'@

function Note([string]$text) {
    Write-Host $text
    $script:Lines.Add($text)
}

function Reset-Project {
    Set-Content -LiteralPath (Join-Path $Proj 'project.godot') -Value $PristineProjectGodot -Encoding UTF8 -NoNewline
    Set-Content -LiteralPath (Join-Path $Proj 'main.tscn') -Value $PristineMainTscn -Encoding UTF8 -NoNewline
    Set-Content -LiteralPath (Join-Path $Proj 'main.gd') -Value $PristineMainGd -Encoding UTF8 -NoNewline
    foreach ($rel in @('util.gd', 'util.gd.uid', 'notes.txt', 'scratch', 'created', 'shots', 'extra')) {
        $full = Join-Path $Proj $rel
        if (Test-Path -LiteralPath $full) { Remove-Item -LiteralPath $full -Recurse -Force }
    }
    Note 'project reset to its canonical state'
}

function Import-Project {
    for ($attempt = 1; $attempt -le 2; $attempt++) {
        $out = Join-Path $Logs ('task090_import_' + $RunTag + '_' + $attempt + '.stdout.txt')
        $err = Join-Path $Logs ('task090_import_' + $RunTag + '_' + $attempt + '.stderr.txt')
        Remove-Item -Force $out, $err -ErrorAction SilentlyContinue
        $cmdline = '"' + $Engine + '" --headless --path ' + $Proj + ' --import & echo IMPORT_EXIT=%ERRORLEVEL%'
        $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $cmdline -WorkingDirectory 'H:\rebuild\godot' `
            -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -PassThru
        $p.WaitForExit()
        $line = (Select-String -LiteralPath $out -Pattern 'IMPORT_EXIT=(-?\d+)' | Select-Object -Last 1)
        $code = if ($line) { $line.Matches[0].Groups[1].Value } else { 'none' }
        Note ("import attempt {0}: exit {1}" -f $attempt, $code)
        if ($code -eq '0') { return $true }
    }
    return $false
}

function Start-Engine([string[]]$Extra, [string]$LogName) {
    $out = Join-Path $Logs ('task090_live_' + $RunTag + '_' + $LogName + '.stdout.txt')
    $err = Join-Path $Logs ('task090_live_' + $RunTag + '_' + $LogName + '.stderr.txt')
    Remove-Item -Force $out, $err -ErrorAction SilentlyContinue
    $cmdline = '"' + $Engine + '" ' + ($Extra -join ' ')
    $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $cmdline -WorkingDirectory 'H:\rebuild\godot' `
        -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -PassThru
    $script:Handles += $p
    return [pscustomobject]@{ Process = $p; Out = $out; Err = $err; Cmdline = $cmdline }
}

function Stop-Engine($handle) {
    if ($null -eq $handle) { return }
    try {
        $children = Get-CimInstance Win32_Process -Filter ("ParentProcessId=" + $handle.Process.Id) -ErrorAction SilentlyContinue
        foreach ($c in @($children)) { Stop-Process -Id $c.ProcessId -Force -ErrorAction SilentlyContinue }
        if (-not $handle.Process.HasExited) { Stop-Process -Id $handle.Process.Id -Force -ErrorAction SilentlyContinue }
    } catch { }
}

function Wait-Port([int]$Port, [int]$TimeoutMs) {
    $deadline = (Get-Date).AddMilliseconds($TimeoutMs)
    while ((Get-Date) -lt $deadline) {
        $client = New-Object System.Net.Sockets.TcpClient
        try {
            $task = $client.ConnectAsync('127.0.0.1', $Port)
            if ($task.Wait(700) -and $client.Connected) { $client.Close(); return $true }
        } catch { } finally { try { $client.Close() } catch { } }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Invoke-Mcp([int]$Port, [string]$Body, [string]$Tag, [string]$Note0) {
    $bodyFile = Join-Path $Root ($Tag + '.request.json')
    Set-Content -LiteralPath $bodyFile -Value $Body -Encoding UTF8 -NoNewline
    $curlArgs = @('-s', '-X', 'POST', '-H', 'Content-Type: application/json',
                  '--data-binary', ('@' + $bodyFile), ("http://127.0.0.1:{0}/mcp" -f $Port))
    $result = & curl.exe @curlArgs 2>$null
    $text = ($result -join '')
    $file = Join-Path $Root ($Tag + '.json')
    Set-Content -LiteralPath $file -Value $text -Encoding UTF8
    $short = $text
    if ($short.Length -gt 200) { $short = $short.Substring(0, 200) + '...' }
    Note ("  [{0}] port={1} bytes={2} :: {3}" -f $Tag, $Port, $text.Length, $short)
    $script:IndexOfCalls.Add(('{0}|{1}|{2}|{3}|{4}' -f $Tag, $Port, $Body.Length, $text.Length, $Note0))
    return $text
}

function Mcp-Call([int]$Id, [string]$Tool, $Arguments) {
    $obj = @{ jsonrpc = '2.0'; id = $Id; method = 'tools/call';
              params = @{ name = $Tool; arguments = $Arguments } }
    return ($obj | ConvertTo-Json -Compress -Depth 12)
}

function Get-FileSnapshot([string[]]$Rel) {
    $map = @{}
    foreach ($r in $Rel) {
        $full = Join-Path $Proj ($r -replace '/', '\')
        if (Test-Path -LiteralPath $full) {
            $item = Get-Item -LiteralPath $full
            $map[$r] = ('{0}|{1}' -f $item.Length, (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash)
        } else {
            $map[$r] = 'ABSENT'
        }
    }
    return $map
}

$Watched = @('project.godot', 'main.tscn', 'main.gd', 'notes.txt', 'util.gd',
             'scratch/box.tscn', 'scratch/grad.tres', 'created/inner/first.txt',
             'shots/editor1.png')

Note '=== TASK-090 round-8 live session (windowed) ==='
Note ('engine  : ' + $Engine)
Note ('project : ' + $Proj)
Note ('run tag : ' + $RunTag)

Reset-Project
if (-not (Import-Project)) { Note 'FATAL: the project never imported'; }

$before = Get-FileSnapshot $Watched

$editorTrace = Join-Path $Root 'trace-editor.jsonl'
$gameTrace = Join-Path $Root 'trace-game.jsonl'
foreach ($f in @($editorTrace, $gameTrace)) { if (Test-Path $f) { Remove-Item -LiteralPath $f -Force } }

# --- editor ---------------------------------------------------------------
$editorArgs = @('-e', '--path', $Proj,
                ('--mcp-port=' + $EditorPort),
                ('--mcp-trace=' + $editorTrace),
                '--mcp-capture=every_call',
                ('--mcp-capture-dir=' + (Join-Path $Root 'shots-editor')),
                '--mcp-capture-viewport=2d')
$editor = Start-Engine -Extra $editorArgs -LogName 'editor'
Note ('editor  : ' + $editor.Cmdline)
if (-not (Wait-Port -Port $EditorPort -TimeoutMs 300000)) {
    Note 'FATAL: the editor endpoint never came up'
} else {
    Start-Sleep -Seconds 8
    Note '--- editor side (9888) ---'
    $descValue = "MCP round-8 mini game ($RunTag)"
    $notes = "MCP round-8 session text ($RunTag).`nSecond line.`nThird line.`n"

    Invoke-Mcp $EditorPort '{"jsonrpc":"2.0","id":101,"method":"tools/list","params":{}}' 'e01-tools-list' 'tools/list' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 102 'project_write_text_file' @{ path = 'res://notes.txt'; content = $notes; overwrite = $true }) 'e02-write-text' 'file write (real change)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 103 'project_write_text_file' @{ path = 'res://notes.txt'; content = $notes; overwrite = $true }) 'e03-write-text-again' 'file write, same bytes (no effect)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 104 'project_read_text_file' @{ path = 'res://notes.txt' }) 'e04-read-text' 'file read' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 105 'project_write_text_file' @{ path = 'res://created/inner/first.txt'; content = "created by MCP round 8`n" }) 'e05-write-new-dirs' 'file write into new directories' | Out-Null

    $util = "extends RefCounted`n`nfunc tag() -> String:`n`treturn `"round8`"`n"
    Invoke-Mcp $EditorPort (Mcp-Call 106 'project_create_script' @{ path = 'res://util.gd'; content = $util }) 'e06-create-script' 'script create (real change)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 107 'project_create_script' @{ path = 'res://util.gd'; content = $util }) 'e07-create-script-again' 'boundary: script already exists (created must be false)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 108 'project_edit_script' @{ path = 'res://util.gd'; content = $util }) 'e08-edit-script-same' 'script edit, same bytes (no effect)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 109 'project_edit_script' @{ path = 'res://util.gd'; content = ($util + "`nfunc extra() -> int:`n`treturn 8`n") }) 'e09-edit-script-real' 'script edit (real change)' | Out-Null

    Invoke-Mcp $EditorPort (Mcp-Call 110 'project_create_scene_file' @{ path = 'res://scratch/box.tscn'; root_type = 'Node2D'; root_name = 'Box' }) 'e10-create-scene-file' 'scene file create (file change)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 111 'project_create_resource' @{ path = 'res://scratch/grad.tres'; type = 'Gradient' }) 'e11-create-resource' 'resource create (file change)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 112 'project_create_resource' @{ path = 'res://scratch/grad.tres'; type = 'Gradient' }) 'e12-create-resource-again' 'MUST fail: resource already exists (data.suggestion)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 113 'project_create_scene_file' @{ path = 'res://scratch/box.tscn'; root_type = 'Node2D'; root_name = 'Box' }) 'e13-create-scene-file-again' 'MUST fail: scene file already exists (data.suggestion)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 114 'project_delete_scene_file' @{ path = 'res://scratch/box.tscn' }) 'e14-delete-scene-file' 'delete (real change)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 115 'project_delete_scene_file' @{ path = 'res://scratch/box.tscn' }) 'e15-delete-scene-file-again' 'MUST fail: already deleted (data.suggestion)' | Out-Null

    Invoke-Mcp $EditorPort (Mcp-Call 116 'project_set_setting' @{ key = 'application/config/description'; value = $descValue }) 'e16-set-setting' 'project.godot section write (real change)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 117 'project_set_setting' @{ key = 'application/config/description'; value = $descValue }) 'e17-set-setting-again' 'project.godot same value (no effect)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 118 'project_get_settings' @{ prefix = 'application' }) 'e18-get-settings' 'settings read' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 119 'project_read_script' @{ path = 'res://main.gd' }) 'e19-read-script' 'script read' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 120 'project_get_statistics' @{}) 'e20-statistics' 'analysis read' | Out-Null

    Invoke-Mcp $EditorPort (Mcp-Call 121 'editor_open_scene' @{ path = 'res://main.tscn' }) 'e21-open-scene' 'scene open' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp $EditorPort (Mcp-Call 122 'editor_get_scene_tree' @{}) 'e22-editor-scene-tree' 'scene read' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 123 'editor_get_node_properties' @{ path = 'Player' }) 'e23-node-properties' 'node read' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 124 'editor_set_node_property' @{ path = 'Sky'; property = 'color'; value = @{ r = 0.05; g = 0.05; b = 0.1; a = 1.0 } }) 'e24-set-sky-color' 'node write (screen change)' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp $EditorPort (Mcp-Call 125 'editor_set_node_property' @{ path = 'Sky'; property = 'color'; value = @{ r = 0.05; g = 0.05; b = 0.1; a = 1.0 } }) 'e25-set-sky-color-again' 'node write, same value (no effect)' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp $EditorPort (Mcp-Call 126 'editor_save_scene' @{}) 'e26-save-scene' 'scene save (file change)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 127 'editor_capture_screenshot' @{ save_path = 'res://shots/editor1.png' }) 'e27-editor-screenshot' 'screenshot (file change)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 128 'editor_get_errors' @{}) 'e28-get-errors' 'editor log read' | Out-Null
    Start-Sleep -Seconds 3
}
Stop-Engine -Handle $editor
Start-Sleep -Seconds 3

# --- game -----------------------------------------------------------------
$gameArgs = @('--path', $Proj,
              ('--mcp-port=' + $GamePort),
              ('--mcp-trace=' + $gameTrace),
              '--mcp-capture=every_call',
              ('--mcp-capture-dir=' + (Join-Path $Root 'shots-game')),
              '--mcp-capture-viewport=2d')
$game = Start-Engine -Extra $gameArgs -LogName 'game'
Note ('game    : ' + $game.Cmdline)
if (-not (Wait-Port -Port $GamePort -TimeoutMs 300000)) {
    Note 'FATAL: the game endpoint never came up'
} else {
    Start-Sleep -Seconds 8
    Note '--- game side (9889) ---'

    # (0) the scene tree BEFORE any executor call: the pollution baseline.
    Invoke-Mcp $GamePort (Mcp-Call 301 'running_game_get_scene_tree' @{}) 'g01-scene-tree-before' 'the tree before any executor call' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 302 'running_game_get_node_properties' @{ node_path = 'Player' }) 'g02-player-properties' 'running game read' | Out-Null

    # (1) the executor reaches the RUNNING tree: read the root, read a node that
    # was there before the call, move and recolour it, change the HUD text.
    Invoke-Mcp $GamePort (Mcp-Call 303 'running_game_execute_gdscript' @{ code = 'return get_parent().name' }) 'g03-exec-root-name' 'executor: is self inside the scene root?' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 304 'running_game_execute_gdscript' @{ code = 'return get_parent().get_node("Player").position.x' }) 'g04-exec-read-x' 'executor: read a pre-existing node property' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 305 'running_game_execute_gdscript' @{ code = 'var p = get_parent().get_node("Player")' + "`n" + 'p.position.x += 120.0' + "`n" + 'return p.position.x' }) 'g05-exec-move-player' 'executor: drive the game (screen change)' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp $GamePort (Mcp-Call 306 'running_game_execute_gdscript' @{ code = 'var p = get_parent().get_node("Player")' + "`n" + 'p.position.x += 120.0' + "`n" + 'return p.position.x' }) 'g06-exec-move-player-again' 'executor: drive it again (screen change)' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp $GamePort (Mcp-Call 307 'running_game_execute_gdscript' @{ code = 'return get_parent().get_node("Player").get_path()' }) 'g07-exec-player-path' 'executor: absolute path of a real node' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 308 'running_game_execute_gdscript' @{ code = 'get_parent().set_hud("HUD from executor")' + "`n" + 'return get_parent().get_node("HUD").text' }) 'g08-exec-set-hud' 'executor: change the HUD (screen change)' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp $GamePort (Mcp-Call 309 'running_game_execute_gdscript' @{ code = 'return get_path()' }) 'g09-exec-own-path' 'executor: the temporary node is a child of the scene root' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 310 'running_game_execute_gdscript' @{ code = 'return get_tree().current_scene.name' }) 'g10-exec-current-scene' 'executor: get_tree() reaches the running scene' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 311 'running_game_execute_gdscript' @{ code = 'var p = get_parent().get_node("Player")' + "`n" + 'p.color = Color(0.1, 0.9, 0.1, 1.0)' + "`n" + 'return p.color' }) 'g11-exec-set-color' 'executor: recolour (screen change)' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp $GamePort (Mcp-Call 312 'running_game_execute_gdscript' @{ code = 'var p = get_parent().get_node("Player")' + "`n" + 'p.color = Color(0.1, 0.9, 0.1, 1.0)' + "`n" + 'return p.color' }) 'g12-exec-set-color-again' 'executor: same colour again (no effect)' | Out-Null
    Start-Sleep -Seconds 2

    # (0b) the tree right after the executor batch: it must be the same tree.
    Invoke-Mcp $GamePort (Mcp-Call 313 'running_game_get_scene_tree' @{}) 'g13-scene-tree-after-exec' 'the tree after the executor calls' | Out-Null

    # (4) the two failing shapes the trace now has to carry a payload for.
    Invoke-Mcp $GamePort (Mcp-Call 314 'running_game_execute_gdscript' @{ code = 'return (' }) 'g14-exec-parse-error' 'MUST fail: parse error (data.parse_error)' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 315 'running_game_execute_gdscript' @{ code = 'return get_parent().get_node("NoSuchChild").name' }) 'g15-exec-runtime-error' 'runtime error after mounting (must still clean up)' | Out-Null
    Start-Sleep -Seconds 1

    # (2) batch node writes through the dedicated tool.
    Invoke-Mcp $GamePort (Mcp-Call 316 'running_game_set_node_property' @{ node_path = 'Player'; property = 'position'; value = @{ x = 60.0; y = 420.0 } }) 'g16-set-position' 'node write (screen change)' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp $GamePort (Mcp-Call 317 'running_game_set_node_property' @{ node_path = 'Player'; property = 'position'; value = @{ x = 60.0; y = 420.0 } }) 'g17-set-position-again' 'node write, same value (no effect)' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp $GamePort (Mcp-Call 318 'running_game_set_node_property' @{ node_path = 'Ghost'; property = 'color'; value = @{ r = 0; g = 0; b = 0; a = 1 } }) 'g18-set-missing-node' 'MUST fail: node does not exist (data.suggestion)' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 319 'running_game_get_node_properties' @{ node_path = 'Player' }) 'g19-player-readback' 'read back the written state' | Out-Null

    # (3) input simulation + assertions.
    Invoke-Mcp $GamePort (Mcp-Call 320 'running_game_assert_node_state' @{ node_path = 'Player'; property = 'position'; expected = @{ x = 60.0; y = 420.0 } }) 'g20-assert-pass' 'assertion that holds (position)' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 321 'running_game_assert_node_state' @{ node_path = 'Player'; property = 'position'; expected = @{ x = 999.0; y = 999.0 } }) 'g21-assert-fail' 'assertion that does NOT hold (ledger flag)' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 322 'running_game_simulate_button_click_by_text' @{ text = 'Move' }) 'g22-click-move-button' 'input simulation: the Move button (screen change)' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp $GamePort (Mcp-Call 323 'running_game_assert_node_state' @{ node_path = 'Player'; property = 'position'; expected = @{ x = 70.0; y = 420.0 } }) 'g23-assert-after-click' 'assertion that holds after the click' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 324 'running_game_simulate_button_click_by_text' @{ text = 'NoSuchButton' }) 'g24-click-missing-button' 'MUST fail: no such button (data.suggestion)' | Out-Null

    # the multi-step scenario: inject `mcp_right` -> wait -> assert (deferred).
    Invoke-Mcp $GamePort (Mcp-Call 325 'running_game_run_test_scenario' @{ steps = @(
        @{ type = 'input'; action = 'mcp_right'; pressed = $true },
        @{ type = 'wait'; seconds = 0.4 },
        @{ type = 'assert'; node_path = 'Player'; property = 'position'; expected = @{ x = 95.0; y = 420.0 } }
    ) }) 'g25-scenario-pass' 'input -> wait -> assert (should hold)' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp $GamePort (Mcp-Call 326 'running_game_run_test_scenario' @{ steps = @(
        @{ type = 'input'; action = 'mcp_right'; pressed = $true },
        @{ type = 'wait'; seconds = 0.4 },
        @{ type = 'assert'; node_path = 'Player'; property = 'position'; expected = @{ x = 99999.0; y = 420.0 } }
    ) }) 'g26-scenario-fail' 'input -> wait -> assert (must NOT hold)' | Out-Null
    Start-Sleep -Seconds 2

    Invoke-Mcp $GamePort (Mcp-Call 327 'running_game_assert_screen_text' @{ text = 'HUD from executor' }) 'g27-assert-screen-text-pass' 'screen text assertion that holds' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 328 'running_game_assert_screen_text' @{ text = 'TEXT THAT IS NOT ON SCREEN' }) 'g28-assert-screen-text-fail' 'screen text assertion that does NOT hold' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 329 'running_game_capture_screenshot' @{ save_path = 'user://round8-game.png' }) 'g29-game-screenshot' 'screenshot (file change)' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 330 'running_game_get_scene_tree' @{}) 'g30-scene-tree-final' 'the tree at the end of the session' | Out-Null
    Start-Sleep -Seconds 3
}
Stop-Engine -Handle $game
Start-Sleep -Seconds 1
foreach ($h in $script:Handles) { Stop-Engine -Handle $h }

# --- what landed ----------------------------------------------------------
Note '--- artefacts ---'
foreach ($dir in @((Join-Path $Root 'shots-editor'), (Join-Path $Root 'shots-game'))) {
    if (Test-Path $dir) {
        $files = @(Get-ChildItem -LiteralPath $dir -File | Sort-Object Name)
        Note ("{0}: {1} file(s)" -f $dir, $files.Count)
    } else {
        Note ("{0}: ABSENT" -f $dir)
    }
}
foreach ($t in @($editorTrace, $gameTrace)) {
    if (Test-Path $t) { Note ("{0}: {1} bytes, {2} lines" -f $t, (Get-Item $t).Length, (Get-Content $t | Measure-Object -Line).Lines) }
    else { Note ("{0}: ABSENT" -f $t) }
}

Note '--- independent file snapshot (sha256 before -> after) ---'
$after = Get-FileSnapshot $Watched
foreach ($r in $Watched) {
    $b = $before[$r]
    $a = $after[$r]
    $verdict = if ($b -eq $a) { 'unchanged' } else { 'CHANGED' }
    Note ("  {0,-24} {1}" -f $r, $verdict)
    Note ("      before={0}" -f $b)
    Note ("      after ={0}" -f $a)
}

Set-Content -LiteralPath (Join-Path $Root 'live-session.txt') -Value $script:Lines -Encoding UTF8
Set-Content -LiteralPath (Join-Path $Root 'call-index.txt') -Value $script:IndexOfCalls -Encoding UTF8
Note ('summary: ' + (Join-Path $Root 'live-session.txt'))
