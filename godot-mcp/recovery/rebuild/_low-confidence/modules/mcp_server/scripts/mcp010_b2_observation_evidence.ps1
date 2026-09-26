# =============================================================================
#  mcp010_b2_observation_evidence.ps1 -- TASK-010 gate 2 / section 2
#
#  The evidence for the two B2 groups TASK-010 implements, and - the actual point
#  of the task - the **E3 unlock chain**: proof, taken from the *game* endpoint
#  (9889), that the built-in module can
#
#    A. read the running game's scene tree and node properties,
#    B. run a caller's GDScript inside the game process and reach the engine
#       singletons (OS / Engine / the running SceneTree) - the thing the
#       migration source's `Expression.execute([], self, false)` path could not
#       do, demonstrated *live* by running the legacy path in the same process
#       and capturing its error text,
#    C. inject input in the game process (`Input.parse_input_event`) and observe
#       an observable state change (a node moves), then release it and observe
#       that the change *stops* - causality, not correlation,
#    D. do all of that without the editor process, which is only used as the
#       *negative* side in phase `scope`.
#
#  Phases:
#    -Phase game    the seven tools on a real game: the observation group (tree,
#                   properties, batch, autoload, find-by-script, UI elements),
#                   the E3 chain above, and the three evidence classes per tool
#                   (success / missing-or-mistyped parameter / bottom-layer
#                   failure), plus the live `-32000` wording of a game-side
#                   refusal and the new bind INFO line from the engine log.
#    -Phase scope   9888 (editor) must not serve any of the seven and must refuse
#                   them with -32601; 9889 must serve all seven exactly once, and
#                   must still not serve an editor-only tool. The two full name
#                   lists are printed side by side.
#    -Phase count   `docs/scripts/check_tool_groups.py` (B1) and the same checker
#                   with `--batch B2/B3/B4/B5` plus `--check-completeness`, and a
#                   machine-checked cross-manifest view whose every number is
#                   *derived* (TASK-048 section 1): no implemented name in two
#                   manifests, every implemented name in the 171 entry contract,
#                   every implemented name with a scope the rename map knows, and
#                   the endpoint arithmetic that follows from those scopes.
#
#  TASK-048 section 1 -- why the numbers below are derived, not frozen:
#
#    Until this task the `scope` and `count` phases carried four invariants that
#    were *literals* measured when TASK-010 implemented B1+B2 = 48 tools of which
#    8 were scope=game (48 union / 17+23+8 scope split / 40 editor endpoint /
#    17 editor-only + 8 game-only). The tree has since reached 171/171, so those
#    literals were red on every run - a red that can never fail for a reason
#    connected to this script, which is exactly where a real regression hides.
#
#    They are therefore derived the way `accept_m1.ps1` derives its expected set
#    (TASK-018 section 2): the single source of truth is the union of the `tools`
#    of every group marked `implemented: true` in the five per-batch group
#    manifests listed in `$ManifestFileNames`, and `docs/tool-rename-map.json` is
#    the authority for each tool's `scope`. Every count printed by `-Phase count`
#    is a consequence of those files; `-Phase scope` goes further and compares the
#    *live* `tools/list` name sets of 9888 and 9889 against the derived sets, so
#    the derivation still fails when the registered tree really drifts from the
#    manifests. A missing manifest is fatal on purpose - skipping one would
#    silently shrink the expected set, the failure this derivation exists to
#    prevent.
#
#  Discipline (PLAYBOOK section 3 and section 7.1):
#    * every response body goes to its own file with `curl.exe -s -o <file>`
#      (never through Out-File or a pipeline) and its sha256 is computed from the
#      bytes on disk;
#    * the scratch projects are fresh copies under %TEMP%; nothing is written
#      inside the repository or any user project;
#    * ports 9888 (editor) / 9889 (game) only. Port 9877 belongs to the user's
#      editor: it is never touched, only observed, and every process this script
#      starts is registered with its pid and command line so the shared
#      classification in `mcp_port_guard.ps1` can decide it (TASK-047 section 1);
#    * only engines this script started itself are stopped.
#
#  Usage:
#    powershell -NoProfile -ExecutionPolicy Bypass -File mcp010_b2_observation_evidence.ps1 -Phase game
#    powershell ... -Phase scope
#    powershell ... -Phase count
# =============================================================================

param(
    [ValidateSet('game', 'scope', 'count')]
    [string]$Phase = 'game'
)

$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$Engine = Join-Path $RepoRoot 'bin\godot.windows.editor.x86_64.console.exe'
$Curl = Join-Path $env:SystemRoot 'System32\curl.exe'
$EditorPort = 9888
$GamePort = 9889
$UserPort = 9877
$Scratch = Join-Path $env:TEMP 'mcp010-b2-observation-scratch'
$NoSceneScratch = Join-Path $env:TEMP 'mcp010-b2-observation-noscene'
$LogRoot = Join-Path $env:TEMP 'mcp010-b2-observation-logs'
$Evid = Join-Path $env:TEMP 'mcp010-b2-observation-evidence'

$ObservationTools = @(
    'running_game_get_scene_tree',
    'running_game_get_node_properties',
    'running_game_get_node_properties_batch',
    'running_game_get_autoload_node',
    'running_game_find_nodes_by_script',
    'running_game_find_ui_elements'
)
$ScriptTool = 'running_game_execute_gdscript'
$Executor = 'running_game_execute_gdscript'
$EditorOnlyProbe = 'editor_get_errors'
$InputAction = 'mcp_test_jump'

$script:Results = New-Object System.Collections.Generic.List[object]
$script:StartedPids = New-Object System.Collections.Generic.List[int]

# =============================================================================
#  Derived expectations (TASK-048 section 1) -- see the file header for why.
# =============================================================================

$ManifestFileNames = @(
    'tool-groups.json',
    'tool-groups-b2.json',
    'tool-groups-b3.json',
    'tool-groups-b4.json',
    'tool-groups-b5.json',
    'tool-groups-added.json'
)

# Reads the five per-batch manifests and the rename map, and returns the
# implemented union plus everything the two remaining phases assert against:
#   Union              every implemented tool name, manifest order, de-duplicated
#   ImplementedByManifest  manifest file name -> its own implemented names
#   Duplicates         implemented names carried by more than one manifest
#   Foreign            implemented names that are not in the 171 entry contract
#   UnknownScope       implemented names whose rename map scope is not one of
#                      editor / both / game
#   EditorScope / BothScope / GameScope   the union partitioned by scope
#   EditorEndpoint     what 9888 serves: union minus the game-scope tools
#   GameEndpoint       what 9889 serves: union minus the editor-scope tools
#   EditorOnly / GameOnly  the two only-lists (served by exactly one endpoint)
function Get-DerivedExpectations {
    $implementedByManifest = [ordered]@{}
    $seenIn = @{}
    $union = @()
    foreach ($manifestFileName in $ManifestFileNames) {
        $manifestPath = Join-Path $RepoRoot ('modules\mcp_server\docs\' + $manifestFileName)
        if (-not (Test-Path $manifestPath)) { throw ("group manifest not found: {0}" -f $manifestPath) }
        $manifestJson = ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 $manifestPath)
        $implemented = @()
        foreach ($group in @($manifestJson.groups)) {
            if ($group.implemented -ne $true) { continue }
            foreach ($tool in @($group.tools)) {
                $name = [string]$tool
                if ($implemented -notcontains $name) { $implemented += $name }
                if ($union -notcontains $name) { $union += $name }
                if (-not $seenIn.ContainsKey($name)) { $seenIn[$name] = @() }
                if ($seenIn[$name] -notcontains $manifestFileName) { $seenIn[$name] += $manifestFileName }
            }
        }
        $implementedByManifest[$manifestFileName] = $implemented
    }
    if ($union.Count -eq 0) { throw 'no implemented tool found in any group manifest' }

    $mapPath = Join-Path $RepoRoot 'modules\mcp_server\docs\tool-rename-map.json'
    if (-not (Test-Path $mapPath)) { throw ("rename map not found: {0}" -f $mapPath) }
    $mapJson = ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 $mapPath)
    $scopeOf = @{}
    foreach ($entry in @($mapJson.tools)) { $scopeOf[[string]$entry.new_name] = [string]$entry.scope }
    # TASK-052: an *added* tool has no rename-map row, so its group in
    # `docs/tool-groups-added.json` declares the scope (the same fallback
    # `check_contract_subset.ps1` and `accept_m1.ps1` use). Without it the two
    # added tools would land in `UnknownScope` and the endpoint sets would be
    # derived from an empty scope.
    $addedManifestPath = Join-Path $RepoRoot 'modules\mcp_server\docs\tool-groups-added.json'
    if (Test-Path $addedManifestPath) {
        $addedJson = ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 $addedManifestPath)
        foreach ($addedGroup in @($addedJson.groups)) {
            foreach ($addedTool in @($addedGroup.tools)) { $scopeOf[[string]$addedTool] = [string]$addedGroup.scope }
        }
    }

    $contractPath = Join-Path $RepoRoot 'modules\mcp_server\docs\tools_list.renamed.json'
    if (-not (Test-Path $contractPath)) { throw ("renamed contract not found: {0}" -f $contractPath) }
    $contractJson = ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 $contractPath)
    $contractNames = @($contractJson.result.tools | ForEach-Object { [string]$_.name })

    $duplicates = @()
    foreach ($name in $union) { if (@($seenIn[$name]).Count -gt 1) { $duplicates += $name } }
    $foreign = @($union | Where-Object { $contractNames -notcontains $_ })
    $knownScopes = @('editor', 'both', 'game')
    $unknownScope = @($union | Where-Object { $knownScopes -notcontains $scopeOf[$_] })

    $editorScope = @($union | Where-Object { $scopeOf[$_] -eq 'editor' })
    $gameScope = @($union | Where-Object { $scopeOf[$_] -eq 'game' })
    $bothScope = @($union | Where-Object { $scopeOf[$_] -eq 'both' })
    $editorEndpoint = @($union | Where-Object { $scopeOf[$_] -ne 'game' })
    $gameEndpoint = @($union | Where-Object { $scopeOf[$_] -ne 'editor' })
    $editorOnly = @($editorEndpoint | Where-Object { $gameEndpoint -notcontains $_ })
    $gameOnly = @($gameEndpoint | Where-Object { $editorEndpoint -notcontains $_ })

    return [pscustomobject]@{
        Union                 = $union
        ImplementedByManifest = $implementedByManifest
        Duplicates            = $duplicates
        Foreign               = $foreign
        UnknownScope          = $unknownScope
        EditorScope           = $editorScope
        BothScope             = $bothScope
        GameScope             = $gameScope
        EditorEndpoint        = $editorEndpoint
        GameEndpoint          = $gameEndpoint
        EditorOnly            = $editorOnly
        GameOnly              = $gameOnly
    }
}

# Set equality over two string collections, case sensitive, order independent.
function Test-SameNameSet {
    param([string[]]$Left, [string[]]$Right)
    $leftOnly = @($Left | Where-Object { $Right -cnotcontains $_ })
    $rightOnly = @($Right | Where-Object { $Left -cnotcontains $_ })
    return [pscustomobject]@{
        Equal     = (($leftOnly.Count -eq 0) -and ($rightOnly.Count -eq 0))
        LeftOnly  = $leftOnly
        RightOnly = $rightOnly
    }
}

function Add-Check {
    param([string]$Id, [bool]$Pass, [string]$Evidence)
    $script:Results.Add([pscustomobject]@{ id = $Id; pass = $Pass; evidence = $Evidence })
    $tag = if ($Pass) { 'PASS' } else { 'FAIL' }
    Write-Host ("[{0}] {1} :: {2}" -f $tag, $Id, $Evidence)
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Text)
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    [IO.File]::WriteAllText($Path, $Text, (New-Object Text.UTF8Encoding($false)))
}

function Get-ListenerPid {
    param([int]$Port)
    foreach ($line in (& netstat -ano -p TCP 2>$null)) {
        if ($line -match 'LISTENING' -and $line -match ("[:\]]" + $Port + "\s")) {
            return [int](($line.Trim() -split '\s+')[-1])
        }
    }
    return -1
}

function Wait-ForTcp {
    param([int]$Port, [int]$TimeoutMs = 240000)
    $deadline = [DateTime]::UtcNow.AddMilliseconds($TimeoutMs)
    while ([DateTime]::UtcNow -lt $deadline) {
        $client = New-Object System.Net.Sockets.TcpClient
        try {
            $task = $client.ConnectAsync('127.0.0.1', $Port)
            if ($task.Wait(700) -and $client.Connected) { return $true }
        } catch { } finally { $client.Close() }
        Start-Sleep -Milliseconds 600
    }
    return $false
}

function Start-Engine {
    param([string[]]$Arguments, [string]$LogName)
    $out = Join-Path $LogRoot ($LogName + '.out.log')
    $err = Join-Path $LogRoot ($LogName + '.err.log')
    Remove-Item -Path $out, $err -ErrorAction SilentlyContinue
    $proc = Start-Process -FilePath $Engine -ArgumentList $Arguments -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden
    $script:StartedPids.Add($proc.Id)
    # TASK-047 section 1: record the pid *and* the arguments, so "did this script
    # ever ask for the user's port" is read off the real command line.
    Register-McpPortGuardProcess -Guard $script:McpPortGuard -EnginePid $proc.Id -Arguments $Arguments
    Write-Host ("started pid={0} :: {1}" -f $proc.Id, ($Arguments -join ' '))
    return [pscustomobject]@{ Process = $proc; Out = $out; Err = $err }
}

function Stop-Engine {
    param($Handle)
    if ($null -eq $Handle) { return }
    try {
        if (-not $Handle.Process.HasExited) {
            Stop-Process -Id $Handle.Process.Id -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 1200
        }
    } catch { }
}

function Import-Project {
    param([string]$Path, [string]$LogName)
    $out = Join-Path $LogRoot ($LogName + '.out.log')
    $err = Join-Path $LogRoot ($LogName + '.err.log')
    $proc = Start-Process -FilePath $Engine -ArgumentList @('--headless', '--path', $Path, '--import') `
        -PassThru -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden
    $proc.WaitForExit(300000) | Out-Null
}

# One JSON-RPC request: body to a file, `curl.exe --data-binary @file`, response
# to its own file with `-o` (never through a pipe).
function Invoke-Mcp {
    param([string]$Id, [string]$Json, [int]$Port)
    $bodyFile = Join-Path $Evid ("{0}.request.json" -f $Id)
    $respFile = Join-Path $Evid ("{0}.response.json" -f $Id)
    [IO.File]::WriteAllBytes($bodyFile, [Text.Encoding]::UTF8.GetBytes($Json))
    if (Test-Path $respFile) { Remove-Item -Force $respFile }
    & $Curl -s -o $respFile -H 'Content-Type: application/json' --data-binary ('@' + $bodyFile) `
        ("http://127.0.0.1:{0}/mcp" -f $Port) | Out-Null
    $curlExit = $LASTEXITCODE
    $bytes = [IO.File]::ReadAllBytes($respFile)
    $sha = (Get-FileHash -Algorithm SHA256 -Path $respFile).Hash.ToLower()
    $text = [Text.Encoding]::UTF8.GetString($bytes)
    Write-Host ("[{0}] port={1} curl_exit={2} bytes={3} sha256={4}" -f $Id, $Port, $curlExit, $bytes.Length, $sha)
    Write-Host ("       request : {0}" -f $Json)
    Write-Host ("       response: {0}" -f $text)
    return $text
}

function Get-Payload {
    param([string]$ResponseText)
    $json = $ResponseText | ConvertFrom-Json
    if ($null -ne $json.result -and $null -ne $json.result.content) {
        return ($json.result.content[0].text | ConvertFrom-Json)
    }
    return $null
}

function Get-ErrorObject {
    param([string]$ResponseText)
    return ($ResponseText | ConvertFrom-Json).error
}

function Get-Lists {
    param([string]$ResponseText)
    $json = $ResponseText | ConvertFrom-Json
    if ($null -eq $json.result) { return $null }
    return @($json.result.tools | ForEach-Object { [string]$_.name })
}

# A JSON-RPC tools/call body, built with a here-string template and
# `ConvertTo-Json` for the arguments so a GDScript body full of quotes and
# newlines survives the trip.
function New-CallBody {
    param([int]$Id, [string]$Tool, $Arguments)
    $argsJson = $Arguments | ConvertTo-Json -Depth 8 -Compress
    return ('{"jsonrpc":"2.0","id":' + $Id + ',"method":"tools/call","params":{"name":"' + $Tool + '","arguments":' + $argsJson + '}}')
}

function Assert-Error {
    param([string]$ResponseText, [string]$Label, [int]$Code, [string]$MessageFragment = '')
    $e = Get-ErrorObject $ResponseText
    if ($null -eq $e) {
        Add-Check $Label $false ("expected the error {0}, got a result: {1}" -f $Code, $ResponseText)
        return
    }
    $ok = ($e.code -eq $Code)
    if ($MessageFragment -ne '') { $ok = $ok -and ([string]$e.message).Contains($MessageFragment) }
    Add-Check $Label $ok ("code={0} message='{1}' expected_code={2} message_contains='{3}'" -f $e.code, $e.message, $Code, $MessageFragment)
}

# TASK-047 section 1: the judgement is the shared classification, not "a listener
# must exist". The old body asserted `($Before -eq $after) -and ($Before -ne -1)`,
# whose second half is an *environment precondition* (the user simply running
# Godot) and which therefore fails forever in an environment where 9877 has no
# listener - masking a real regression behind a red that says nothing about this
# script. The shared guard is strictly stronger: it also decides "did this script
# ever ask for 9877" from the real pids and command lines it started.
function Show-PortGuard {
    param([string]$Label)
    $after = Get-ListenerPid -Port $UserPort
    $result = Complete-McpPortGuard -Guard $script:McpPortGuard -PidAfter $after
    Add-Check $Label $result.pass $result.evidence
}

# =============================================================================
#  The scratch project: an autoload, an input action with no events (so only an
#  `InputEventAction` can carry it) and a scene whose Player reacts to that
#  action by moving. `Input.parse_input_event` is buffered and flushed by the
#  headless DisplayServer at the start of the *next* frame
#  (servers/display/display_server_headless.cpp:53-55), so injection and
#  observation are deliberately two different HTTP calls.
# =============================================================================

function Get-ProjectText {
    return ((@(
                'config_version=5',
                '',
                '[application]',
                'config/name="MCP010 B2 observation"',
                'config/features=PackedStringArray("4.8")',
                'run/main_scene="res://scenes/main.tscn"',
                '',
                '[autoload]',
                'GameState="*res://scenes/game_state.gd"',
                '',
                '[input]',
                '',
                ($InputAction + '={'),
                '"deadzone": 0.2,',
                '"events": []',
                '}',
                '',
                '[rendering]',
                'renderer/rendering_method="gl_compatibility"',
                'renderer/rendering_method.mobile="gl_compatibility"'
            ) -join "`n") + "`n")
}

function Get-SceneText {
    return ((@(
                '[gd_scene load_steps=2 format=3]',
                '',
                '[ext_resource type="Script" path="res://scenes/player.gd" id="1_player"]',
                '',
                '[node name="Main" type="Node2D"]',
                '',
                '[node name="Player" type="Node2D" parent="."]',
                'position = Vector2(0, 0)',
                'script = ExtResource("1_player")',
                '',
                '[node name="Hud" type="CanvasLayer" parent="."]',
                '',
                '[node name="Score" type="Label" parent="Hud"]',
                'offset_left = 8.0',
                'offset_top = 8.0',
                'text = "score"',
                '',
                '[node name="Start" type="Button" parent="Hud"]',
                'offset_left = 8.0',
                'offset_top = 40.0',
                'text = "Start Game"'
            ) -join "`n") + "`n")
}

function Get-PlayerScriptText {
    return ((@(
                'extends Node2D',
                '',
                'var injected_events := 0',
                'var moved_frames := 0',
                'var total_move := 0.0',
                '',
                'func _unhandled_input(event: InputEvent) -> void:',
                ('	if event.is_action_pressed("' + $InputAction + '"):'),
                '		injected_events += 1',
                '',
                'func _process(_delta: float) -> void:',
                ('	if Input.is_action_pressed("' + $InputAction + '"):'),
                '		moved_frames += 1',
                '		total_move += 1.0',
                '		position += Vector2(1, 0)'
            ) -join "`n") + "`n")
}

function Get-GameStateScriptText {
    return ((@(
                'extends Node',
                '',
                'var score := 7',
                'var label := "game-state"'
            ) -join "`n") + "`n")
}

# The bottom-layer case for the game-side refusal: a *running* game whose
# `SceneTree::get_current_scene()` is null. Same construction as the TASK-009
# evidence (a main scene whose `_ready` clears `current_scene`), because a
# project without a main scene aborts the process and could not answer at all.
function Get-ClearedProjectText {
    return ((@(
                'config_version=5',
                '',
                '[application]',
                'config/name="MCP010 current scene cleared"',
                'config/features=PackedStringArray("4.8")',
                'run/main_scene="res://scenes/main.tscn"',
                '',
                '[rendering]',
                'renderer/rendering_method="gl_compatibility"',
                'renderer/rendering_method.mobile="gl_compatibility"'
            ) -join "`n") + "`n")
}

function Get-ClearedSceneText {
    return ((@(
                '[gd_scene load_steps=2 format=3]',
                '',
                '[ext_resource type="Script" path="res://scenes/clear_current_scene.gd" id="1_clear"]',
                '',
                '[node name="Main" type="Node2D"]',
                'script = ExtResource("1_clear")'
            ) -join "`n") + "`n")
}

function Get-ClearedScriptText {
    return ((@(
                'extends Node2D',
                '',
                'func _ready() -> void:',
                '	print("MCP010_CURRENT_SCENE_CLEARED")',
                '	get_tree().current_scene = null'
            ) -join "`n") + "`n")
}

function Initialize-Scratch {
    if (Test-Path $Scratch) { Remove-Item -Recurse -Force $Scratch }
    if (Test-Path $NoSceneScratch) { Remove-Item -Recurse -Force $NoSceneScratch }
    New-Item -ItemType Directory -Force -Path (Join-Path $Scratch 'scenes'), `
        (Join-Path $NoSceneScratch 'scenes'), $LogRoot, $Evid | Out-Null
    Write-Utf8NoBom (Join-Path $Scratch 'project.godot') (Get-ProjectText)
    Write-Utf8NoBom (Join-Path $Scratch 'scenes\main.tscn') (Get-SceneText)
    Write-Utf8NoBom (Join-Path $Scratch 'scenes\player.gd') (Get-PlayerScriptText)
    Write-Utf8NoBom (Join-Path $Scratch 'scenes\game_state.gd') (Get-GameStateScriptText)
    Write-Utf8NoBom (Join-Path $NoSceneScratch 'project.godot') (Get-ClearedProjectText)
    Write-Utf8NoBom (Join-Path $NoSceneScratch 'scenes\main.tscn') (Get-ClearedSceneText)
    Write-Utf8NoBom (Join-Path $NoSceneScratch 'scenes\clear_current_scene.gd') (Get-ClearedScriptText)
    Write-Host ("scratch (running game)   : {0}" -f $Scratch)
    Write-Host ("scratch (scene cleared)  : {0}" -f $NoSceneScratch)
}

# =============================================================================
#  Main
# =============================================================================

Write-Host ("=== TASK-010 gate 2 evidence (phase={0}) ===" -f $Phase)

if (Test-Path $Engine) {
    Write-Host ("engine: {0}" -f $Engine)
    Write-Host ("engine sha256: {0}" -f (Get-FileHash -Algorithm SHA256 -Path $Engine).Hash)
} else {
    Write-Host ("FATAL: engine not found: {0}" -f $Engine)
    exit 2
}

$userPidBefore = Get-ListenerPid -Port $UserPort
Write-Host ("user editor on {0} before: pid={1}" -f $UserPort, $userPidBefore)
# TASK-047 section 1: the 9877 judgement is the shared six-way classification,
# not "a listener must exist" - see mcp_port_guard.ps1 for why that was an
# environment precondition rather than a regression.
$script:McpPortGuard = New-McpPortGuard -Port $UserPort -PidBefore $userPidBefore

# -----------------------------------------------------------------------------
# -Phase game
# -----------------------------------------------------------------------------
if ($Phase -eq 'game') {
    Initialize-Scratch
    Write-Host 'importing the scratch projects ...'
    Import-Project -Path $Scratch -LogName 'import-b2-game'
    Import-Project -Path $NoSceneScratch -LogName 'import-b2-noscene'

    $gameHandle = $null
    $noSceneHandle = $null
    try {
        $gameHandle = Start-Engine -Arguments @('--headless', '--path', $Scratch, ("--mcp-port={0}" -f $GamePort)) -LogName 'b2-game'
        if (-not (Wait-ForTcp -Port $GamePort)) { throw "the game endpoint on $GamePort never came up; log=$(Get-Content -Raw $gameHandle.Out -ErrorAction SilentlyContinue)" }
        Start-Sleep -Seconds 8
        Write-Host 'the game endpoint is listening'

        # --- 0. the bind INFO line (TASK-010 section 3.2) --------------------
        $logText = Get-Content -Raw $gameHandle.Out
        $infoLine = @($logText -split "`n" | Where-Object { $_ -match '\[MCP\] INFO:' })
        $infoOk = ($infoLine.Count -ge 1) -and ($infoLine[0].Contains("127.0.0.1:$GamePort")) -and ($infoLine[0].Contains('game process'))
        Add-Check 'game_bind_info_line' $infoOk ("[MCP] INFO line(s) in the engine log: {0}" -f ($infoLine -join ' || '))

        # --- 1. the game endpoint's tool list --------------------------------
        $list = Invoke-Mcp -Id 'g01_tools_list' -Port $GamePort -Json '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
        $gameNames = Get-Lists $list
        Add-Check 'game_tools_list_has_the_seven_b2_tools' `
            ((@($ObservationTools + $ScriptTool | Where-Object { $gameNames -contains $_ })).Count -eq 7) `
            ("game endpoint serves {0} tool(s); the seven B2 tools present" -f $gameNames.Count)

        # --- 2. A: read the running scene tree -------------------------------
        $t = Invoke-Mcp -Id 'g02_get_scene_tree' -Port $GamePort -Json (New-CallBody 2 'running_game_get_scene_tree' @{})
        $p = Get-Payload $t
        if ($null -eq $p) {
            Add-Check 'game_scene_tree_reads_the_running_scene' $false ("no payload: {0}" -f $t)
        } else {
            $tree = $p.tree
            $rootName = [string]$tree.name
            $childNames = @($tree.children | ForEach-Object { [string]$_.name })
            $player = @($tree.children | Where-Object { [string]$_.name -ceq 'Player' })[0]
            $hud = @($tree.children | Where-Object { [string]$_.name -ceq 'Hud' })[0]
            $hudChildren = @($hud.children | ForEach-Object { [string]$_.name })
            $script = [string]$player.script
            $ok = ($rootName -ceq 'Main') -and ($childNames -contains 'Player') -and ($childNames -contains 'Hud') -and
                  ($hudChildren -contains 'Score') -and ($hudChildren -contains 'Start') -and ($script -ceq 'res://scenes/player.gd')
            Add-Check 'game_scene_tree_reads_the_running_scene' $ok `
                ("root={0} children=[{1}] Hud.children=[{2}] Player.script={3}" -f $rootName, ($childNames -join ','), ($hudChildren -join ','), $script)
        }

        $t = Invoke-Mcp -Id 'g03_get_scene_tree_type_filter' -Port $GamePort -Json (New-CallBody 3 'running_game_get_scene_tree' @{ type_filter = 'Node2D' })
        $p = Get-Payload $t
        if ($null -eq $p) {
            Add-Check 'game_scene_tree_type_filter_keeps_the_matching_chain' $false ("no payload: {0}" -f $t)
        } else {
            # The migration source ignored this parameter entirely; here the tree
            # is pruned to Player (a Node2D) plus the root chain that carries it.
            $names = @($p.tree.children | ForEach-Object { [string]$_.name })
            $ok = ([string]$p.tree.name -ceq 'Main') -and ($names.Count -eq 1) -and ($names[0] -ceq 'Player')
            Add-Check 'game_scene_tree_type_filter_keeps_the_matching_chain' $ok ("tree=Main children=[{0}] (Hud pruned, Player kept)" -f ($names -join ','))
        }

        # --- 3. B: the property baseline (before any injection) --------------
        $before = Invoke-Mcp -Id 'g04_properties_before' -Port $GamePort -Json (New-CallBody 4 'running_game_get_node_properties' @{ node_path = 'Player'; properties = @('position', 'moved_frames', 'injected_events', 'total_move') })
        $beforePayload = Get-Payload $before
        $beforeX = $null
        $beforeMoved = $null
        if ($null -ne $beforePayload) {
            $beforeX = [double]$beforePayload.properties.position.x
            $beforeMoved = [int]$beforePayload.properties.moved_frames
        }
        $beforeOk = ($null -ne $beforePayload) -and ([string]$beforePayload.node_path -ceq '/root/Main/Player') -and
                    ([string]$beforePayload.type -ceq 'Node2D') -and ($beforeX -eq 0.0) -and ($beforeMoved -eq 0)
        Add-Check 'game_node_properties_baseline' $beforeOk `
            ("node_path={0} type={1} position.x={2} moved_frames={3} injected_events={4}" -f `
                $beforePayload.node_path, $beforePayload.type, $beforeX, $beforeMoved, $beforePayload.properties.injected_events)

        # Every editor-visible property - and every script variable - when the
        # filter is absent. A game node's interesting state lives in its script's
        # variables, which carry `PROPERTY_USAGE_SCRIPT_VARIABLE` rather than
        # `PROPERTY_USAGE_EDITOR`; the first version of the tool filtered on the
        # latter alone and silently dropped `moved_frames` (measured on this very
        # run, REPORT-010 section 5).
        $all = Invoke-Mcp -Id 'g05_properties_all' -Port $GamePort -Json (New-CallBody 5 'running_game_get_node_properties' @{ node_path = 'Player' })
        $allPayload = Get-Payload $all
        $allKeys = @($allPayload.properties.PSObject.Properties.Name)
        $allOk = ($null -ne $allPayload) -and ($allKeys.Count -gt 3) -and
                 ($allKeys -contains 'position') -and ($allKeys -contains 'moved_frames') -and
                 ($allKeys -contains 'injected_events') -and ($allKeys -notcontains 'script') -and
                 (-not (@($allKeys | Where-Object { $_.StartsWith('_') }).Count -gt 0))
        Add-Check 'game_node_properties_all_editor_and_script' $allOk `
            ("all-properties keys = [{0}]" -f ($allKeys -join ','))

        # --- 4. C: the E3 lever, part 1 - singletons + the legacy comparison --
        $code = @'
var tree := Engine.get_main_loop() as SceneTree
var legacy := Expression.new()
legacy.parse("Input.is_action_pressed(\"ui_accept\")")
var legacy_base := RefCounted.new()
var legacy_value = legacy.execute([], legacy_base, false)
return {
	"pid": OS.get_process_id(),
	"frames": Engine.get_process_frames(),
	"scene_name": tree.current_scene.name,
	"player_x": tree.current_scene.get_node("Player").position.x,
	"legacy_failed": legacy.has_execute_failed(),
	"legacy_error": legacy.get_error_text(),
	"legacy_value_is_null": legacy_value == null,
}
'@
        $t = Invoke-Mcp -Id 'g06_execute_gdscript_singletons' -Port $GamePort -Json (New-CallBody 6 $Executor @{ code = $code })
        $p = Get-Payload $t
        if ($null -eq $p) {
            Add-Check 'game_execute_gdscript_reaches_the_engine' $false ("no payload: {0}" -f $t)
        } else {
            $r = $p.result
            $enginePid = $gameHandle.Process.Id
            $ok = ([string]$p.result_type -ceq 'Dictionary') -and ([int]$r.pid -gt 0) -and ([string]$r.scene_name -ceq 'Main') -and
                  ([double]$r.player_x -eq 0.0)
            Add-Check 'game_execute_gdscript_reaches_the_engine' $ok `
                ("result_type={0} pid={1} (engine pid={2}) frames={3} scene_name={4} player_x={5}" -f `
                    $p.result_type, $r.pid, $enginePid, $r.frames, $r.scene_name, $r.player_x)
            $legacyOk = ($r.legacy_failed -eq $true) -and ([string]$r.legacy_error).Contains('Input') -and ($r.legacy_value_is_null -eq $true)
            Add-Check 'game_legacy_expression_path_fails_on_the_same_process' $legacyOk `
                ("legacy.has_execute_failed()={0} legacy.get_error_text()='{1}' legacy value is null={2}" -f `
                    $r.legacy_failed, $r.legacy_error, $r.legacy_value_is_null)
        }

        # --- 5. C: the E3 lever, part 2 - inject input in the game process ---
        $inject = @"
var event := InputEventAction.new()
event.action = "$InputAction"
event.pressed = true
Input.parse_input_event(event)
return {
	"injected": true,
	"action": event.action,
	"action_known_to_InputMap": InputMap.has_action("$InputAction"),
	"pressed_same_frame": Input.is_action_pressed("$InputAction"),
}
"@
        $t = Invoke-Mcp -Id 'g07_inject_input' -Port $GamePort -Json (New-CallBody 7 $Executor @{ code = $inject })
        $p = Get-Payload $t
        if ($null -eq $p) {
            Add-Check 'game_input_injection_is_delivered' $false ("no payload: {0}" -f $t)
        } else {
            $r = $p.result
            # `pressed_same_frame` is expected to be *false*: `parse_input_event`
            # buffers and the headless DisplayServer flushes the buffer at the
            # start of the next frame, so the action state is not visible yet.
            $ok = ($r.injected -eq $true) -and ([string]$r.action -ceq $InputAction) -and ($r.action_known_to_InputMap -eq $true)
            Add-Check 'game_input_injection_is_delivered' $ok `
                ("injected={0} action={1} action_in_InputMap={2} pressed_same_frame={3} (buffered, flushed next frame)" -f `
                    $r.injected, $r.action, $r.action_known_to_InputMap, $r.pressed_same_frame)
        }

        Start-Sleep -Seconds 3

        $after = Invoke-Mcp -Id 'g08_properties_after' -Port $GamePort -Json (New-CallBody 8 'running_game_get_node_properties' @{ node_path = 'Player'; properties = @('position', 'moved_frames', 'injected_events', 'total_move') })
        $afterPayload = Get-Payload $after
        $afterX = $null
        $afterMoved = $null
        $afterEvents = $null
        if ($null -ne $afterPayload) {
            $afterX = [double]$afterPayload.properties.position.x
            $afterMoved = [int]$afterPayload.properties.moved_frames
            $afterEvents = [int]$afterPayload.properties.injected_events
        }
        $afterOk = ($null -ne $afterPayload) -and ($afterX -gt $beforeX) -and ($afterMoved -gt $beforeMoved) -and ($afterEvents -ge 1)
        Add-Check 'game_injected_input_moved_the_node' $afterOk `
            ("position.x {0} -> {1}; moved_frames {2} -> {3}; injected_events={4} (the action reached _unhandled_input too)" -f `
                $beforeX, $afterX, $beforeMoved, $afterMoved, $afterEvents)

        # --- 6. C: the E3 lever, part 3 - release and prove causality --------
        $release = @"
var event := InputEventAction.new()
event.action = "$InputAction"
event.pressed = false
Input.parse_input_event(event)
return { "released": true, "pressed_same_frame": Input.is_action_pressed("$InputAction") }
"@
        $t = Invoke-Mcp -Id 'g09_release_input' -Port $GamePort -Json (New-CallBody 9 $Executor @{ code = $release })
        $p = Get-Payload $t
        $releaseOk = ($null -ne $p) -and ($p.result.released -eq $true)
        Add-Check 'game_input_release_is_delivered' $releaseOk ("released={0} pressed_same_frame={1}" -f $p.result.released, $p.result.pressed_same_frame)

        Start-Sleep -Seconds 2
        $frozen1 = Invoke-Mcp -Id 'g10_properties_frozen_a' -Port $GamePort -Json (New-CallBody 10 'running_game_get_node_properties' @{ node_path = 'Player'; properties = @('position', 'moved_frames') })
        Start-Sleep -Seconds 2
        $frozen2 = Invoke-Mcp -Id 'g11_properties_frozen_b' -Port $GamePort -Json (New-CallBody 11 'running_game_get_node_properties' @{ node_path = 'Player'; properties = @('position', 'moved_frames') })
        $frozenPayload1 = Get-Payload $frozen1
        $frozenPayload2 = Get-Payload $frozen2
        $frozenOk = ($null -ne $frozenPayload1) -and ($null -ne $frozenPayload2) -and
                    ([double]$frozenPayload1.properties.position.x -eq [double]$frozenPayload2.properties.position.x) -and
                    ([int]$frozenPayload1.properties.moved_frames -eq [int]$frozenPayload2.properties.moved_frames)
        Add-Check 'game_state_stops_changing_after_the_release' $frozenOk `
            ("position.x {0} -> {1}; moved_frames {2} -> {3} across two reads two seconds apart, after the release event" -f `
                $frozenPayload1.properties.position.x, $frozenPayload2.properties.position.x, `
                $frozenPayload1.properties.moved_frames, $frozenPayload2.properties.moved_frames)

        # --- 7. the rest of the observation group ----------------------------
        $batch = New-CallBody 12 'running_game_get_node_properties_batch' @{
            nodes = @(
                @{ node_path = 'Player'; properties = @('position') },
                @{ node_path = 'Hud/Score'; properties = @('text') },
                @{ node_path = 'NoSuchNode'; properties = @('x') }
            )
        }
        $t = Invoke-Mcp -Id 'g12_batch_properties' -Port $GamePort -Json $batch
        $p = Get-Payload $t
        if ($null -eq $p) {
            Add-Check 'game_batch_reads_two_nodes_and_reports_the_missing_one' $false ("no payload: {0}" -f $t)
        } else {
            # NOTE: the local must not be called `$results` - PowerShell variable
            # names are case insensitive, so it would be the very same variable
            # as the `$script:Results` list and the next Add-Check would fail
            # with "Collection was of a fixed size".
            $batchResults = @($p.results)
            $ok = ($p.count -eq 3) -and ($batchResults.Count -eq 3) -and
                  ([string]$batchResults[0].node_path -ceq '/root/Main/Player') -and
                  ([string]$batchResults[1].node_path -ceq '/root/Main/Hud/Score') -and
                  ([string]$batchResults[1].properties.text -ceq 'score') -and
                  ($null -ne $batchResults[2].error) -and ([string]$batchResults[2].node_path -ceq 'NoSuchNode')
            Add-Check 'game_batch_reads_two_nodes_and_reports_the_missing_one' $ok `
                ("count={0} [0]={1} [1]={2} text={3} [2].error={4}" -f $p.count, $batchResults[0].node_path, $batchResults[1].node_path, $batchResults[1].properties.text, $batchResults[2].error)
        }

        $t = Invoke-Mcp -Id 'g13_autoload' -Port $GamePort -Json (New-CallBody 13 'running_game_get_autoload_node' @{ name = 'GameState'; properties = @('score', 'label') })
        $p = Get-Payload $t
        $autoloadOk = ($null -ne $p) -and ([string]$p.path -ceq '/root/GameState') -and ([int]$p.properties.score -eq 7) -and ([string]$p.properties.label -ceq 'game-state')
        Add-Check 'game_autoload_is_read_by_name' $autoloadOk ("name={0} path={1} type={2} score={3} label={4}" -f $p.name, $p.path, $p.type, $p.properties.score, $p.properties.label)

        $t = Invoke-Mcp -Id 'g14_find_nodes_by_script' -Port $GamePort -Json (New-CallBody 14 'running_game_find_nodes_by_script' @{ script = 'res://scenes/player.gd'; properties = @('moved_frames') })
        $p = Get-Payload $t
        if ($null -eq $p) {
            Add-Check 'game_find_nodes_by_script_is_exact' $false ("no payload: {0}" -f $t)
        } else {
            $nodes = @($p.nodes)
            $ok = ($p.count -eq 1) -and ($nodes.Count -eq 1) -and ([string]$nodes[0].path -ceq '/root/Main/Player') -and ($null -ne $nodes[0].properties.moved_frames)
            Add-Check 'game_find_nodes_by_script_is_exact' $ok ("count={0} [0].path={1} moved_frames={2}" -f $p.count, $nodes[0].path, $nodes[0].properties.moved_frames)
        }
        # The exact-match half: a substring of the same path must find nothing.
        $t = Invoke-Mcp -Id 'g15_find_nodes_by_script_substring' -Port $GamePort -Json (New-CallBody 15 'running_game_find_nodes_by_script' @{ script = 'player' })
        $p = Get-Payload $t
        Add-Check 'game_find_nodes_by_script_does_not_match_a_substring' (($null -ne $p) -and ($p.count -eq 0)) `
            ("script='player' (a substring of res://scenes/player.gd) -> count={0}" -f $p.count)

        $t = Invoke-Mcp -Id 'g16_find_ui_elements' -Port $GamePort -Json (New-CallBody 16 'running_game_find_ui_elements' @{})
        $p = Get-Payload $t
        if ($null -eq $p) {
            Add-Check 'game_find_ui_elements_lists_the_controls' $false ("no payload: {0}" -f $t)
        } else {
            $types = @($p.elements | ForEach-Object { [string]$_.type })
            $ok = ($p.count -eq 2) -and ($types -contains 'Label') -and ($types -contains 'Button')
            Add-Check 'game_find_ui_elements_lists_the_controls' $ok ("count={0} types=[{1}]" -f $p.count, ($types -join ','))
        }

        $t = Invoke-Mcp -Id 'g17_find_ui_elements_type_filter' -Port $GamePort -Json (New-CallBody 17 'running_game_find_ui_elements' @{ type_filter = 'Button' })
        $p = Get-Payload $t
        $uiFilterOk = ($null -ne $p) -and ($p.count -eq 1) -and ([string]$p.elements[0].type -ceq 'Button') -and ([string]$p.elements[0].name -ceq 'Start')
        Add-Check 'game_find_ui_elements_type_filter' $uiFilterOk ("count={0} [0]={1}/{2}" -f $p.count, $p.elements[0].name, $p.elements[0].type)

        # --- 8. the three evidence classes -----------------------------------
        # (a) missing required parameter
        $t = Invoke-Mcp -Id 'g18_missing_parameter' -Port $GamePort -Json (New-CallBody 18 'running_game_get_node_properties' @{})
        Assert-Error $t 'game_missing_parameter_is_-32602' -32602 'Missing required parameter: node_path'

        # (b) a parameter of the wrong type
        $t = Invoke-Mcp -Id 'g19_mistyped_parameter' -Port $GamePort -Json (New-CallBody 19 'running_game_get_scene_tree' @{ max_depth = 'deep' })
        Assert-Error $t 'game_mistyped_parameter_is_-32602' -32602 "Parameter 'max_depth' must be an integer, got String"

        # (c) bottom-layer failures: a node that is not there, an autoload that
        #     is not there, and code that does not compile
        $t = Invoke-Mcp -Id 'g20_node_not_found' -Port $GamePort -Json (New-CallBody 20 'running_game_get_node_properties' @{ node_path = 'NoSuchNode' })
        Assert-Error $t 'game_unknown_node_is_-32001' -32001 "Node 'NoSuchNode' not found"
        $e = Get-ErrorObject $t
        if ($null -ne $e) {
            Add-Check 'game_unknown_node_has_a_suggestion' ((($null -ne $e.data) -and ($null -ne $e.data.suggestion) -and ([string]$e.data.suggestion).Length -gt 0)) `
                ("data.suggestion='{0}'" -f $e.data.suggestion)
        }

        $t = Invoke-Mcp -Id 'g21_autoload_not_found' -Port $GamePort -Json (New-CallBody 21 'running_game_get_autoload_node' @{ name = 'NoSuchAutoload' })
        Assert-Error $t 'game_unknown_autoload_is_-32001' -32001 "Autoload 'NoSuchAutoload' not found"

        $t = Invoke-Mcp -Id 'g22_execute_gdscript_parse_error' -Port $GamePort -Json (New-CallBody 22 $Executor @{ code = 'return (' })
        Assert-Error $t 'game_uncompilable_code_is_-32602' -32602 'does not compile'

        $t = Invoke-Mcp -Id 'g23_execute_gdscript_empty' -Port $GamePort -Json (New-CallBody 23 $Executor @{ code = "  `n " })
        Assert-Error $t 'game_empty_code_is_-32602' -32602 "Parameter 'code' must not be empty"

        Stop-Engine -Handle $gameHandle
        $gameHandle = $null

        # --- 9. the live -32000 wording (TASK-010 section 3.1) ---------------
        $noSceneHandle = Start-Engine -Arguments @('--headless', '--path', $NoSceneScratch, ("--mcp-port={0}" -f $GamePort)) -LogName 'b2-noscene'
        if (-not (Wait-ForTcp -Port $GamePort)) { throw "the cleared-scene game endpoint on $GamePort never came up; log=$(Get-Content -Raw $noSceneHandle.Out -ErrorAction SilentlyContinue)" }
        Start-Sleep -Seconds 6
        Add-Check 'game_cleared_scene_endpoint_is_really_a_running_game' (-not $noSceneHandle.Process.HasExited) `
            ("engine pid={0} still running, so the -32000 below is the tool's null-scene refusal and not a dead endpoint" -f $noSceneHandle.Process.Id)

        $t = Invoke-Mcp -Id 'g24_no_current_scene' -Port $GamePort -Json (New-CallBody 24 'running_game_get_scene_tree' @{})
        Assert-Error $t 'game_no_current_scene_is_-32000' -32000 'No scene is currently open'
        $e = Get-ErrorObject $t
        if ($null -ne $e) {
            $suggestion = [string]$e.data.suggestion
            $ok = ($suggestion.Contains('main scene')) -and ($suggestion.Contains('project.godot')) -and (-not $suggestion.Contains('editor_open_scene'))
            Add-Check 'game_no_scene_advice_is_not_editor_advice' $ok ("data.suggestion='{0}'" -f $suggestion)
        }

        Stop-Engine -Handle $noSceneHandle
        $noSceneHandle = $null
    } finally {
        Stop-Engine -Handle $gameHandle
        Stop-Engine -Handle $noSceneHandle
        Show-PortGuard -Label 'guard_user_port_9877'
    }
}

# -----------------------------------------------------------------------------
# -Phase scope
# -----------------------------------------------------------------------------
if ($Phase -eq 'scope') {
    Initialize-Scratch
    Write-Host 'importing the scratch project ...'
    Import-Project -Path $Scratch -LogName 'import-b2-scope'

    $editorHandle = $null
    $gameHandle = $null
    $editorNames = @()
    $gameNames = @()
    try {
        $editorHandle = Start-Engine -Arguments @('--headless', '-e', '--path', $Scratch, ("--mcp-port={0}" -f $EditorPort)) -LogName 'b2-editor-scope'
        if (-not (Wait-ForTcp -Port $EditorPort)) { throw "the editor endpoint on $EditorPort never came up; log=$(Get-Content -Raw $editorHandle.Out -ErrorAction SilentlyContinue)" }
        Start-Sleep -Seconds 8

        $list = Invoke-Mcp -Id 'scope01_editor_tools_list' -Port $EditorPort -Json '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
        $editorNames = Get-Lists $list
        $leaked = @($ObservationTools + $ScriptTool | Where-Object { $editorNames -contains $_ })
        Add-Check 'scope_b2_tools_absent_from_the_editor_list' ($leaked.Count -eq 0) `
            ("editor endpoint (9888) serves {0} tool(s); leaked B2 game-scope tool(s): [{1}]" -f $editorNames.Count, ($leaked -join ','))

        foreach ($tool in ($ObservationTools + $ScriptTool)) {
            $t = Invoke-Mcp -Id ("scope02_editor_calls_" + $tool) -Port $EditorPort -Json (New-CallBody 2 $tool @{ node_path = 'Player'; code = 'return 1'; name = 'GameState'; script = 'res://x.gd' })
            Assert-Error $t ("scope_editor_refuses_" + $tool + "_with_-32601") -32601 ("Method not found: " + $tool)
        }

        Stop-Engine -Handle $editorHandle
        $editorHandle = $null

        $gameHandle = Start-Engine -Arguments @('--headless', '--path', $Scratch, ("--mcp-port={0}" -f $GamePort)) -LogName 'b2-game-scope'
        if (-not (Wait-ForTcp -Port $GamePort)) { throw "the game endpoint on $GamePort never came up; log=$(Get-Content -Raw $gameHandle.Out -ErrorAction SilentlyContinue)" }
        Start-Sleep -Seconds 8

        $list = Invoke-Mcp -Id 'scope03_game_tools_list' -Port $GamePort -Json '{"jsonrpc":"2.0","id":3,"method":"tools/list","params":{}}'
        $gameNames = Get-Lists $list
        $missing = @($ObservationTools + $ScriptTool | Where-Object { $gameNames -notcontains $_ })
        Add-Check 'scope_b2_tools_present_on_the_game_list_exactly_once' ($missing.Count -eq 0) `
            ("game endpoint (9889) serves {0} tool(s); missing: [{1}]" -f $gameNames.Count, ($missing -join ','))

        $editorLeaked = @($gameNames | Where-Object { $_ -ceq $EditorOnlyProbe })
        Add-Check 'scope_editor_only_tool_still_absent_from_the_game_list' ($editorLeaked.Count -eq 0) `
            ("{0}: occurrences on the game endpoint = {1}" -f $EditorOnlyProbe, $editorLeaked.Count)

        $t = Invoke-Mcp -Id 'scope04_game_calls_editor_tool' -Port $GamePort -Json (New-CallBody 4 $EditorOnlyProbe @{})
        Assert-Error $t 'scope_game_refuses_editor_tool_with_-32601' -32601 ("Method not found: " + $EditorOnlyProbe)

        Stop-Engine -Handle $gameHandle
        $gameHandle = $null
    } finally {
        Stop-Engine -Handle $editorHandle
        Stop-Engine -Handle $gameHandle

        Write-Host ''
        Write-Host '================= the two endpoints side by side ================='
        Write-Host ("editor 9888 ({0} tools): {1}" -f $editorNames.Count, ($editorNames -join ' > '))
        Write-Host ("game   9889 ({0} tools): {1}" -f $gameNames.Count, ($gameNames -join ' > '))
        $editorOnly = @($editorNames | Where-Object { $gameNames -notcontains $_ })
        $gameOnly = @($gameNames | Where-Object { $editorNames -notcontains $_ })
        Write-Host ("editor-only tools (present on 9888, absent on 9889): {0}" -f (($editorOnly) -join ', '))
        Write-Host ("game-only tools   (present on 9889, absent on 9888): {0}" -f (($gameOnly) -join ', '))

        # TASK-048 section 1: the expectations are *derived* from the five group
        # manifests and the rename map, never the TASK-010 era literals (17 / 8).
        # The comparison is set equality, so a tool that moved from one endpoint
        # to the other cannot leave a count green.
        $derived = Get-DerivedExpectations
        $editorSet = Test-SameNameSet -Left $editorNames -Right $derived.EditorEndpoint
        Add-Check 'scope_editor_endpoint_serves_exactly_the_derived_set' $editorSet.Equal `
            ("live 9888 = {0} tool(s), derived = {1}; live_only=[{2}] derived_only=[{3}]" -f `
                $editorNames.Count, $derived.EditorEndpoint.Count, ($editorSet.LeftOnly -join ','), ($editorSet.RightOnly -join ','))
        $gameSet = Test-SameNameSet -Left $gameNames -Right $derived.GameEndpoint
        Add-Check 'scope_game_endpoint_serves_exactly_the_derived_set' $gameSet.Equal `
            ("live 9889 = {0} tool(s), derived = {1}; live_only=[{2}] derived_only=[{3}]" -f `
                $gameNames.Count, $derived.GameEndpoint.Count, ($gameSet.LeftOnly -join ','), ($gameSet.RightOnly -join ','))
        $editorOnlySet = Test-SameNameSet -Left $editorOnly -Right $derived.EditorOnly
        $gameOnlySet = Test-SameNameSet -Left $gameOnly -Right $derived.GameOnly
        Add-Check 'scope_the_editor_game_split_is_exactly_the_scopes' ($editorOnlySet.Equal -and $gameOnlySet.Equal) `
            ("editor-only live={0} derived={1} (live_only=[{2}] derived_only=[{3}]); game-only live={4} derived={5} (live_only=[{6}] derived_only=[{7}])" -f `
                $editorOnly.Count, $derived.EditorOnly.Count, ($editorOnlySet.LeftOnly -join ','), ($editorOnlySet.RightOnly -join ','), `
                $gameOnly.Count, $derived.GameOnly.Count, ($gameOnlySet.LeftOnly -join ','), ($gameOnlySet.RightOnly -join ','))

        Show-PortGuard -Label 'guard_user_port_9877'
    }
}

# -----------------------------------------------------------------------------
# -Phase count
# -----------------------------------------------------------------------------
if ($Phase -eq 'count') {
    $checker = Join-Path $RepoRoot 'modules\mcp_server\docs\scripts\check_tool_groups.py'

    Write-Host ''
    Write-Host '========== check_tool_groups.py (B1, frozen) =========='
    & python $checker
    $b1Exit = $LASTEXITCODE
    Add-Check 'count_check_tool_groups_b1_exit_zero' ($b1Exit -eq 0) ("python check_tool_groups.py exit={0}" -f $b1Exit)

    # TASK-048 section 1: the cross-manifest view below is derived from all five
    # per-batch manifests, so every checker whose manifest feeds it is run too -
    # a green derivation over a manifest nobody validated would be worthless.
    foreach ($batch in @('B2', 'B3', 'B4', 'B5')) {
        Write-Host ''
        Write-Host ("========== check_tool_groups.py --batch {0} ==========" -f $batch)
        & python $checker --batch $batch
        $batchExit = $LASTEXITCODE
        Add-Check ("count_check_tool_groups_{0}_exit_zero" -f $batch.ToLower()) ($batchExit -eq 0) `
            ("python check_tool_groups.py --batch {0} exit={1}" -f $batch, $batchExit)
    }

    Write-Host ''
    Write-Host '========== check_tool_groups.py --check-completeness (171/171) =========='
    & python $checker --check-completeness
    $completeExit = $LASTEXITCODE
    Add-Check 'count_check_tool_groups_completeness_exit_zero' ($completeExit -eq 0) `
        ("python check_tool_groups.py --check-completeness exit={0}" -f $completeExit)

    Write-Host ''
    Write-Host '========== derived cross-manifest view (TASK-048 section 1) =========='
    $derived = Get-DerivedExpectations

    $docB2 = ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 (Join-Path $RepoRoot 'modules\mcp_server\docs\tool-groups-b2.json'))
    $b2All = @($docB2.groups | ForEach-Object { $_.tools })

    # The manifest-level overlap the old check looked at, over *every* group and
    # all five manifests (not just B1/B2), independent of `implemented`.
    $manifestAllTools = [ordered]@{}
    foreach ($manifestFileName in $ManifestFileNames) {
        $doc = ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 (Join-Path $RepoRoot ('modules\mcp_server\docs\' + $manifestFileName)))
        $manifestAllTools[$manifestFileName] = @($doc.groups | ForEach-Object { $_.tools })
    }
    $allOverlap = @()
    for ($i = 0; $i -lt $ManifestFileNames.Count; $i++) {
        for ($j = $i + 1; $j -lt $ManifestFileNames.Count; $j++) {
            foreach ($claimed in @($manifestAllTools[$ManifestFileNames[$i]])) {
                if (@($manifestAllTools[$ManifestFileNames[$j]]) -ccontains $claimed) {
                    $allOverlap += ("{0}/{1}:{2}" -f $ManifestFileNames[$i], $ManifestFileNames[$j], $claimed)
                }
            }
        }
    }

    $manifestLines = @()
    foreach ($manifestFileName in $ManifestFileNames) {
        $manifestLines += ('{0}={1}' -f $manifestFileName, @($derived.ImplementedByManifest[$manifestFileName]).Count)
    }
    Write-Host ("manifests implemented: {0}" -f ($manifestLines -join ', '))
    Write-Host ("implemented union    : {0} tool(s)" -f $derived.Union.Count)
    Write-Host ("scope split          : {0} editor-scope + {1} both-scope + {2} game-scope" -f `
        $derived.EditorScope.Count, $derived.BothScope.Count, $derived.GameScope.Count)
    Write-Host ("editor endpoint 9888 : {0} tool(s) (union minus the {1} game-scope tools)" -f `
        $derived.EditorEndpoint.Count, $derived.GameScope.Count)
    Write-Host ("game endpoint   9889 : {0} tool(s) (union minus the {1} editor-scope tools)" -f `
        $derived.GameEndpoint.Count, $derived.EditorScope.Count)
    Write-Host ("only-lists           : editor-only {0}, game-only {1}" -f `
        $derived.EditorOnly.Count, $derived.GameOnly.Count)

    Add-Check 'count_manifests_are_disjoint' (($allOverlap.Count -eq 0) -and ($derived.Duplicates.Count -eq 0)) `
        ("names claimed by two manifests (any group) = {0} [{1}]; implemented names carried by two manifests = {2} [{3}]" -f `
            $allOverlap.Count, ($allOverlap -join ','), $derived.Duplicates.Count, ($derived.Duplicates -join ','))
    Add-Check 'count_b2_manifest_is_25_tools' ($b2All.Count -eq 25) ("B2 manifest tool count = {0}" -f $b2All.Count)
    Add-Check 'count_every_implemented_tool_is_in_the_contract' ($derived.Foreign.Count -eq 0) `
        ("implemented names absent from the 171 entry contract = {0} [{1}]" -f $derived.Foreign.Count, ($derived.Foreign -join ','))
    Add-Check 'count_every_implemented_tool_has_a_known_scope' ($derived.UnknownScope.Count -eq 0) `
        ("implemented names whose rename map scope is not editor/both/game = {0} [{1}]" -f $derived.UnknownScope.Count, ($derived.UnknownScope -join ','))
    # The scope partition has to *cover* the union: a misspelled scope would drop
    # a tool out of both scope lists and silently put it on both endpoints.
    Add-Check 'count_scope_split_matches_the_rename_map' `
        (($derived.EditorScope.Count + $derived.BothScope.Count + $derived.GameScope.Count) -eq $derived.Union.Count) `
        ("{0} editor + {1} both + {2} game = {3} of {4} implemented tool(s)" -f `
            $derived.EditorScope.Count, $derived.BothScope.Count, $derived.GameScope.Count, `
            ($derived.EditorScope.Count + $derived.BothScope.Count + $derived.GameScope.Count), $derived.Union.Count)
    # Both-scope tools are served by *both* endpoints, so the two endpoint sizes
    # add up to the union plus the both-scope tools. The old literal 40 was this
    # arithmetic evaluated once; now it follows from the rename map.
    Add-Check 'count_endpoint_expectations' `
        (($derived.EditorEndpoint.Count + $derived.GameEndpoint.Count) -eq ($derived.Union.Count + $derived.BothScope.Count)) `
        ("editor {0} + game {1} = union {2} + both-scope {3}" -f `
            $derived.EditorEndpoint.Count, $derived.GameEndpoint.Count, $derived.Union.Count, $derived.BothScope.Count)
}

$passed = @($script:Results | Where-Object { $_.pass }).Count
$total = $script:Results.Count
Write-Host ''
Write-Host ("=== phase {0}: {1}/{2} checks passed ===" -f $Phase, $passed, $total)
foreach ($r in $script:Results) {
    if (-not $r.pass) { Write-Host ("  FAILED {0} :: {1}" -f $r.id, $r.evidence) }
}
Write-Host ("evidence directory: {0}" -f $Evid)
if ($passed -ne $total) { exit 1 }
exit 0
