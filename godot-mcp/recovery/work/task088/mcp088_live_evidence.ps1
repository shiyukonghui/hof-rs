param(
    [string]$Engine = 'H:\rebuild\godot\bin\godot.windows.editor.x86_64.console.exe',
    [int]$EditorPort = 9888,
    [int]$GamePort = 9889,
    [switch]$Headless
)
# =============================================================================
#  mcp088_live_evidence.ps1 -- TASK-088 item 5: a REAL session whose trace,
#  screenshots and pixel verdicts are kept as the evidence that the traceability
#  capability exists.
#
#  Editor side (9888):  tools/list (the published contract), a mutating call, and
#                       the SAME call again (the "reported success, picture did
#                       not move" case).
#  Game side   (9889):  a read, a mutating call on the visible ColorRect, and the
#                       same call again.
#
#  Both processes are WINDOWED unless -Headless: a headless process has no
#  framebuffer, so every capture is `unavailable` and the pixel verdict cannot be
#  demonstrated (the module says so at `--mcp-capture` startup).
#
#  Iron rule 2: no shell redirection anywhere - every file is written with
#  Set-Content/-OutFile or passed to a Python writer; the engines are started
#  with Start-Process, which owns their stdout/stderr files.
#  Iron rule 4: the engines are started through cmd.exe.
# =============================================================================
$ErrorActionPreference = 'Stop'
$Root = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task088\live'
$Proj = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task088\live-proj'
$Logs = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs'
New-Item -ItemType Directory -Force -Path $Root | Out-Null

$script:Handles = @()
$script:Lines = New-Object System.Collections.Generic.List[string]

function Note([string]$text) {
    Write-Host $text
    $script:Lines.Add($text)
}

function Start-Engine([string[]]$Extra, [string]$LogName) {
    $out = Join-Path $Logs ('task088_live_' + $LogName + '.stdout.txt')
    $err = Join-Path $Logs ('task088_live_' + $LogName + '.stderr.txt')
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

function Invoke-Mcp([int]$Port, [string]$Body, [string]$Tag) {
    # The body goes through a FILE and `--data-binary @file`: PowerShell 5.1
    # mangles embedded double quotes when it passes a JSON string as a native
    # argument (the server received garbage and answered -32700), and a file also
    # avoids any shell redirection (iron rule 2).
    $bodyFile = Join-Path $Root ($Tag + '.request.json')
    Set-Content -LiteralPath $bodyFile -Value $Body -Encoding UTF8 -NoNewline
    $curlArgs = @('-s', '-X', 'POST', '-H', 'Content-Type: application/json',
                  '--data-binary', ('@' + $bodyFile), ("http://127.0.0.1:{0}/mcp" -f $Port))
    $result = & curl.exe @curlArgs 2>$null
    $text = ($result -join '')
    $file = Join-Path $Root ($Tag + '.json')
    Set-Content -LiteralPath $file -Value $text -Encoding UTF8
    Note ("  [{0}] port={1} bytes={2} -> {3}" -f $Tag, $Port, $text.Length, $file)
    return $text
}

# ---------------------------------------------------------------------------
$mode = if ($Headless) { 'headless' } else { 'windowed' }
Note ('=== TASK-088 live traceability session (' + $mode + ') ===')
Note ('engine  : ' + $Engine)
Note ('project : ' + $Proj)

$editorTrace = Join-Path $Root 'trace-editor.jsonl'
$gameTrace = Join-Path $Root 'trace-game.jsonl'
foreach ($f in @($editorTrace, $gameTrace)) { if (Test-Path $f) { Remove-Item -LiteralPath $f -Force } }

$common = @('--path', $Proj, '--mcp-capture=every_call')
if (-not $Headless) { $common = @('--path', $Proj) }
Write-Output ('unused hint: ' + ($common -join ' ')) | Out-Null

# --- editor ---------------------------------------------------------------
$editorArgs = @('-e', '--path', $Proj,
                ('--mcp-port=' + $EditorPort),
                ('--mcp-trace=' + $editorTrace),
                '--mcp-capture=every_call',
                ('--mcp-capture-dir=' + (Join-Path $Root 'shots-editor')),
                '--mcp-capture-viewport=2d')
if ($Headless) { $editorArgs = @('--headless') + $editorArgs }
$editor = Start-Engine -Extra $editorArgs -LogName 'editor'
Note ('editor  : ' + $editor.Cmdline)
if (-not (Wait-Port -Port $EditorPort -TimeoutMs 240000)) {
    Note 'FATAL: the editor endpoint never came up'
} else {
    Start-Sleep -Seconds 4
    Note '--- editor side ---'
    Invoke-Mcp -Port $EditorPort -Tag 'editor-tools-list' `
        -Body '{"jsonrpc":"2.0","id":101,"method":"tools/list","params":{}}' | Out-Null
    Invoke-Mcp -Port $EditorPort -Tag 'editor-open-scene-1' `
        -Body '{"jsonrpc":"2.0","id":102,"method":"tools/call","params":{"name":"editor_open_scene","arguments":{"path":"res://main.tscn"}}}' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp -Port $EditorPort -Tag 'editor-read-tree-1' `
        -Body '{"jsonrpc":"2.0","id":103,"method":"tools/call","params":{"name":"editor_get_scene_tree","arguments":{}}}' | Out-Null
    Invoke-Mcp -Port $EditorPort -Tag 'editor-set-color-green' `
        -Body '{"jsonrpc":"2.0","id":104,"method":"tools/call","params":{"name":"editor_set_node_property","arguments":{"path":"ColorRect","property":"color","value":{"r":0.1,"g":0.9,"b":0.1,"a":1.0}}}}' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp -Port $EditorPort -Tag 'editor-set-color-green-again' `
        -Body '{"jsonrpc":"2.0","id":105,"method":"tools/call","params":{"name":"editor_set_node_property","arguments":{"path":"ColorRect","property":"color","value":{"r":0.1,"g":0.9,"b":0.1,"a":1.0}}}}' | Out-Null
    Start-Sleep -Seconds 3
}
Stop-Engine -Handle $editor
Start-Sleep -Seconds 2

# --- game -----------------------------------------------------------------
$gameArgs = @('--path', $Proj,
              ('--mcp-port=' + $GamePort),
              ('--mcp-trace=' + $gameTrace),
              '--mcp-capture=every_call',
              ('--mcp-capture-dir=' + (Join-Path $Root 'shots-game')))
if ($Headless) { $gameArgs = @('--headless') + $gameArgs }
$game = Start-Engine -Extra $gameArgs -LogName 'game'
Note ('game    : ' + $game.Cmdline)
if (-not (Wait-Port -Port $GamePort -TimeoutMs 240000)) {
    Note 'FATAL: the game endpoint never came up'
} else {
    Start-Sleep -Seconds 4
    Note '--- game side ---'
    Invoke-Mcp -Port $GamePort -Tag 'game-read-tree-1' `
        -Body '{"jsonrpc":"2.0","id":201,"method":"tools/call","params":{"name":"running_game_get_scene_tree","arguments":{}}}' | Out-Null
    Invoke-Mcp -Port $GamePort -Tag 'game-set-color-blue' `
        -Body '{"jsonrpc":"2.0","id":202,"method":"tools/call","params":{"name":"running_game_set_node_property","arguments":{"node_path":"ColorRect","property":"color","value":{"r":0.1,"g":0.1,"b":0.9,"a":1.0}}}}' | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Mcp -Port $GamePort -Tag 'game-set-color-blue-again' `
        -Body '{"jsonrpc":"2.0","id":203,"method":"tools/call","params":{"name":"running_game_set_node_property","arguments":{"node_path":"ColorRect","property":"color","value":{"r":0.1,"g":0.1,"b":0.9,"a":1.0}}}}' | Out-Null
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
Set-Content -LiteralPath (Join-Path $Root 'live-session.txt') -Value $script:Lines -Encoding UTF8
Note ('summary: ' + (Join-Path $Root 'live-session.txt'))
