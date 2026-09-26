param(
    [string]$Engine = 'H:\rebuild\godot\bin\godot.windows.editor.x86_64.mono.console.exe',
    [int]$EditorPort = 9888,
    [int]$GamePort = 9889,
    [string]$Root = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task089\live',
    [string]$Proj = 'H:\rebuild\projects\mcpplay',
    # Run-specific values, so that "the first call really changes something"
    # stays true on a second run over the same project. The CALL SET is
    # identical; only the text/colour/setting values differ per run.
    [string]$RunTag = 'before-run',
    [double]$PlayerColorR = 0.1,
    [double]$PlayerColorG = 0.9,
    [double]$PlayerColorB = 0.1
)
# =============================================================================
#  mcp089_live_evidence.ps1 -- TASK-089 item B: a REAL round-7 session against a
#  real (small) game project, on both endpoints, with the trace and the
#  every-call capture on.
#
#  Coverage: the call table below names, for every tool family, at least one call
#  that really takes effect and at least one that must not (or must be refused),
#  so the file-side and the pixel-side verdicts can both be calibrated.
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

function Note([string]$text) {
    Write-Host $text
    $script:Lines.Add($text)
}

function Start-Engine([string[]]$Extra, [string]$LogName) {
    $out = Join-Path $Logs ('task089_live_' + $LogName + '.stdout.txt')
    $err = Join-Path $Logs ('task089_live_' + $LogName + '.stderr.txt')
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
    if ($short.Length -gt 220) { $short = $short.Substring(0, 220) + '...' }
    Note ("  [{0}] port={1} bytes={2} :: {3}" -f $Tag, $Port, $text.Length, $short)
    $script:IndexOfCalls.Add(('{0}|{1}|{2}|{3}|{4}' -f $Tag, $Port, $Body.Length, $text.Length, $Note0))
    return $text
}

function Mcp-Call([int]$Id, [string]$Tool, $Arguments) {
    $obj = @{ jsonrpc = '2.0'; id = $Id; method = 'tools/call';
              params = @{ name = $Tool; arguments = $Arguments } }
    return ($obj | ConvertTo-Json -Compress -Depth 10)
}

# --- the independent file snapshot (sha256 before/after) ---------------------
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
             'ui_theme.tres', 'scratch/box.tscn', 'scratch/paint.tres',
             'created/inner/first.txt', 'shots/editor1.png')

# A clean slate for the destinations the session creates, taken BEFORE the
# snapshot so "before" describes what the session really found.
foreach ($p in @((Join-Path $Proj 'util.gd'), (Join-Path $Proj 'scratch'),
                 (Join-Path $Proj 'created'), (Join-Path $Proj 'shots'))) {
    if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Recurse -Force }
}
$before = Get-FileSnapshot $Watched

Note '=== TASK-089 round-7 live session (windowed) ==='
Note ('engine  : ' + $Engine)
Note ('project : ' + $Proj)

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
if (-not (Wait-Port -Port $EditorPort -TimeoutMs 240000)) {
    Note 'FATAL: the editor endpoint never came up'
} else {
    Start-Sleep -Seconds 6
    Note '--- editor side (9888) ---'

    Invoke-Mcp $EditorPort '{"jsonrpc":"2.0","id":101,"method":"tools/list","params":{}}' 'editor-tools-list' 'tools/list' | Out-Null

    # family: text file write / read
    $notes = "MCP round-7 session text ($RunTag).`nSecond line.`nThird line.`n"
    Invoke-Mcp $EditorPort (Mcp-Call 102 'project_write_text_file' @{ path = 'res://notes.txt'; content = $notes; overwrite = $true }) 'e02-write-text' 'file write (real change)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 103 'project_write_text_file' @{ path = 'res://notes.txt'; content = $notes; overwrite = $true }) 'e03-write-text-again' 'file write, same bytes (no effect)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 104 'project_read_text_file' @{ path = 'res://notes.txt' }) 'e04-read-text' 'file read' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 105 'project_write_text_file' @{ path = 'res://main.gd'; content = 'x' }) 'e05-write-dedicated-extension' 'boundary: .gd has a dedicated tool' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 106 'project_write_text_file' @{ path = 'res://created/inner/first.txt'; content = "created by MCP`n" }) 'e06-write-new-dirs' 'file write into new directories' | Out-Null

    # family: script write
    $util = "extends RefCounted`n`nfunc tag() -> String:`n`treturn `"round7`"`n"
    Invoke-Mcp $EditorPort (Mcp-Call 107 'project_create_script' @{ path = 'res://util.gd'; content = $util }) 'e07-create-script' 'script create (real change)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 108 'project_create_script' @{ path = 'res://util.gd'; content = $util }) 'e08-create-script-again' 'boundary: script already exists' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 109 'project_edit_script' @{ path = 'res://util.gd'; content = $util }) 'e09-edit-script-same' 'script edit, same bytes (no effect)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 110 'project_edit_script' @{ path = 'res://util.gd'; content = ($util + "`nfunc extra() -> int:`n`treturn 7`n") }) 'e10-edit-script-real' 'script edit (real change)' | Out-Null

    # family: scene / node read + write + save
    Invoke-Mcp $EditorPort (Mcp-Call 111 'editor_open_scene' @{ path = 'res://main.tscn' }) 'e11-open-scene' 'scene open' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp $EditorPort (Mcp-Call 112 'editor_get_scene_tree' @{}) 'e12-scene-tree' 'scene read' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 113 'editor_get_node_properties' @{ path = 'Player' }) 'e13-node-properties' 'node read' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 114 'editor_set_node_property' @{ path = 'Player'; property = 'color'; value = @{ r = $PlayerColorR; g = $PlayerColorG; b = $PlayerColorB; a = 1.0 } }) 'e14-set-color-green' 'node write (screen change)' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp $EditorPort (Mcp-Call 115 'editor_set_node_property' @{ path = 'Player'; property = 'color'; value = @{ r = $PlayerColorR; g = $PlayerColorG; b = $PlayerColorB; a = 1.0 } }) 'e15-set-color-green-again' 'node write, same value (no effect)' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp $EditorPort (Mcp-Call 116 'editor_save_scene' @{}) 'e16-save-scene' 'scene save (file change)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 117 'editor_set_node_property' @{ path = 'NoSuchNode'; property = 'color'; value = @{ r = 0; g = 0; b = 0; a = 1 } }) 'e17-bad-node-path' 'boundary: node does not exist' | Out-Null

    # family: scene/resource file write + delete
    Invoke-Mcp $EditorPort (Mcp-Call 118 'project_create_scene_file' @{ path = 'res://scratch/box.tscn'; root_type = 'Node2D'; root_name = 'Box' }) 'e18-create-scene-file' 'scene file create' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 119 'project_create_resource' @{ path = 'res://scratch/paint.tres'; type = 'Gradient' }) 'e19-create-resource' 'resource create' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 120 'project_delete_scene_file' @{ path = 'res://scratch/box.tscn' }) 'e20-delete-scene-file' 'delete (real change)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 121 'project_delete_scene_file' @{ path = 'res://scratch/box.tscn' }) 'e21-delete-scene-file-again' 'boundary: already deleted' | Out-Null

    # family: project setting (the section-arm writer) + read
    $settingValue = "MCP round-7 mini game ($RunTag)"
    Invoke-Mcp $EditorPort (Mcp-Call 122 'project_set_setting' @{ key = 'application/config/description'; value = $settingValue }) 'e22-set-setting' 'project.godot section write (real change)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 123 'project_set_setting' @{ key = 'application/config/description'; value = $settingValue }) 'e23-set-setting-again' 'project.godot same value (no effect)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 124 'project_get_settings' @{ prefix = 'application' }) 'e24-get-settings' 'settings read' | Out-Null

    # family: analysis
    Invoke-Mcp $EditorPort (Mcp-Call 125 'project_get_statistics' @{}) 'e25-statistics' 'analysis read' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 126 'project_analyze_scene_complexity' @{ path = 'res://main.tscn' }) 'e26-scene-complexity' 'analysis read' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 127 'project_search_file_contents' @{ pattern = 'MCP089' }) 'e27-search-contents' 'analysis read' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 128 'project_read_script' @{ path = 'res://nope.gd' }) 'e28-read-missing-script' 'boundary: missing file' | Out-Null

    # family: observation / screenshot on the editor side
    Invoke-Mcp $EditorPort (Mcp-Call 129 'editor_capture_screenshot' @{ save_path = 'res://shots/editor1.png' }) 'e29-editor-screenshot' 'screenshot (file change)' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 130 'editor_capture_screenshot' @{ save_path = 'res://shots/editor1.png' }) 'e30-editor-screenshot-again' 'screenshot to the same path' | Out-Null
    Invoke-Mcp $EditorPort (Mcp-Call 131 'editor_get_errors' @{}) 'e31-get-errors' 'editor log read' | Out-Null
    Start-Sleep -Seconds 3
}
Stop-Engine -Handle $editor
Start-Sleep -Seconds 2

# --- game -----------------------------------------------------------------
$gameArgs = @('--path', $Proj,
              ('--mcp-port=' + $GamePort),
              ('--mcp-trace=' + $gameTrace),
              '--mcp-capture=every_call',
              ('--mcp-capture-dir=' + (Join-Path $Root 'shots-game')),
              '--mcp-capture-viewport=2d')
$game = Start-Engine -Extra $gameArgs -LogName 'game'
Note ('game    : ' + $game.Cmdline)
if (-not (Wait-Port -Port $GamePort -TimeoutMs 240000)) {
    Note 'FATAL: the game endpoint never came up'
} else {
    Start-Sleep -Seconds 6
    Note '--- game side (9889) ---'

    # family: observation
    Invoke-Mcp $GamePort (Mcp-Call 201 'running_game_get_scene_tree' @{}) 'g01-scene-tree' 'running game read' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 202 'running_game_get_node_properties' @{ node_path = 'Player' }) 'g02-node-properties' 'running game read' | Out-Null

    # family: runtime input / execution
    Invoke-Mcp $GamePort (Mcp-Call 203 'running_game_execute_gdscript' @{ code = 'var m = get_node("/root/Main"); return m.move_player(150.0)' }) 'g03-execute-gdscript' 'runtime code (screen change)' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp $GamePort (Mcp-Call 204 'running_game_execute_gdscript' @{ code = 'var m = get_node("/root/Main"); m.set_hud("HUD from MCP"); return m.moves' }) 'g04-execute-gdscript-2' 'runtime code (screen change)' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp $GamePort (Mcp-Call 205 'running_game_execute_gdscript' @{ code = 'return this_function_does_not_exist()' }) 'g05-execute-gdscript-bad' 'boundary: bad code' | Out-Null

    # family: node write, effective and not. The colour is a rotation of the
    # editor-side one, so it is neither the value the scene was saved with nor
    # the value a previous run left behind.
    $gameColor = @{ r = $PlayerColorB; g = $PlayerColorR; b = $PlayerColorG; a = 1.0 }
    Invoke-Mcp $GamePort (Mcp-Call 206 'running_game_set_node_property' @{ node_path = 'Player'; property = 'color'; value = $gameColor }) 'g06-set-color-blue' 'runtime node write (screen change)' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp $GamePort (Mcp-Call 207 'running_game_set_node_property' @{ node_path = 'Player'; property = 'color'; value = $gameColor }) 'g07-set-color-blue-again' 'runtime node write, same value (no effect)' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp $GamePort (Mcp-Call 208 'running_game_set_node_property' @{ node_path = 'Ghost'; property = 'color'; value = @{ r = 0; g = 0; b = 0; a = 1 } }) 'g08-set-missing-node' 'boundary: node does not exist' | Out-Null

    # family: runtime assertions
    Invoke-Mcp $GamePort (Mcp-Call 209 'running_game_assert_node_state' @{ node_path = 'Player'; property = 'color'; expected = $gameColor }) 'g09-assert-pass' 'assertion that should pass' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 210 'running_game_assert_node_state' @{ node_path = 'Player'; property = 'color'; expected = @{ r = 0.9; g = 0.1; b = 0.1; a = 1.0 } }) 'g10-assert-fail' 'assertion that should fail' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 211 'running_game_assert_screen_text' @{ text = 'HUD from MCP' }) 'g11-assert-screen-text' 'assertion that should pass' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 212 'running_game_assert_screen_text' @{ text = 'TEXT THAT IS NOT ON SCREEN' }) 'g12-assert-screen-text-fail' 'assertion that should fail' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 213 'running_game_simulate_button_click_by_text' @{ text = 'NoSuchButton' }) 'g13-click-missing-button' 'boundary: no such button' | Out-Null

    # family: screenshot on the game side
    Invoke-Mcp $GamePort (Mcp-Call 214 'running_game_capture_screenshot' @{ save_path = 'user://round7-game.png' }) 'g14-game-screenshot' 'screenshot (file change)' | Out-Null
    Invoke-Mcp $GamePort (Mcp-Call 215 'running_game_get_node_properties' @{ node_path = 'HUD' }) 'g15-hud-properties' 'running game read' | Out-Null
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
        foreach ($f in $files) { Note ("  {0}  {1} bytes" -f $f.Name, $f.Length) }
    } else {
        Note ("{0}: ABSENT" -f $dir)
    }
}
foreach ($t in @($editorTrace, $gameTrace)) {
    if (Test-Path $t) { Note ("{0}: {1} bytes, {2} lines" -f $t, (Get-Item $t).Length, (Get-Content $t | Measure-Object -Line).Lines) }
    else { Note ("{0}: ABSENT" -f $t) }
}

# The independent check: what the session did to the watched files, measured by
# hashing them here rather than by believing the trace.
Note '--- independent file snapshot (sha256 before -> after) ---'
$after = Get-FileSnapshot $Watched
foreach ($r in $Watched) {
    $b = $before[$r]
    $a = $after[$r]
    $verdict = if ($b -eq $a) { 'unchanged' } else { 'CHANGED' }
    Note ("  {0,-16} {1}" -f $r, $verdict)
    Note ("      before={0}" -f $b)
    Note ("      after ={0}" -f $a)
}

Set-Content -LiteralPath (Join-Path $Root 'live-session.txt') -Value $script:Lines -Encoding UTF8
Set-Content -LiteralPath (Join-Path $Root 'call-index.txt') -Value $script:IndexOfCalls -Encoding UTF8
Note ('summary: ' + (Join-Path $Root 'live-session.txt'))
