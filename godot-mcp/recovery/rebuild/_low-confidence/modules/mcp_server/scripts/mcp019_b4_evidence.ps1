#    section F  `running_game_capture_signal_emissions` over a real window, and
#               `editor_analyze_screenshot_diff` against two real PNGs.
#
#  Discipline (PLAYBOOK sections 3 and 7.1):
#    * every response body lands on disk through `curl.exe -s -o <file>` and its
#      sha256 is printed from those bytes (never through a pipe);
#    * every request body is built with `ConvertTo-Json` and sent with
#      `curl.exe --data-binary @file`;
#    * ports 9888 (editor) / 9889 (game) only; the user's 9877 is judged by the
#      shared classification in `mcp_port_guard.ps1` (TASK-047 section 1);
#    * scratch `.tscn` / `.godot` files are written **without a BOM** and the
#      `--import` exit code is checked;
#    * this file is deliberately pure ASCII.
#
#  Usage:
#    powershell -NoProfile -ExecutionPolicy Bypass -File mcp019_b4_evidence.ps1
# =============================================================================

$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$ModuleRoot = Join-Path $RepoRoot 'modules\mcp_server'
$Engine = Join-Path $RepoRoot 'bin\godot.windows.editor.x86_64.console.exe'
$Curl = Join-Path $env:SystemRoot 'System32\curl.exe'
$EditorPort = 9888
$GamePort = 9889
$UserPort = 9877
$Scratch = Join-Path $env:TEMP 'mcp019-scratch'
$LogRoot = Join-Path $env:TEMP 'mcp019-logs'

# TASK-028 D-1: the shared scratch-project writer and `--import` runner.
. (Join-Path $PSScriptRoot 'mcp_import_guard.ps1')
# TASK-047 section 1: the shared 9877 classification (see mcp_port_guard.ps1).
. (Join-Path $PSScriptRoot 'mcp_port_guard.ps1')
$Evid = Join-Path $env:TEMP 'mcp019-evidence'

$script:Results = New-Object System.Collections.Generic.List[object]
$script:EditorHandle = $null
$script:GameHandle = $null
$script:Checks = 0

function Add-Check {
    param([string]$Id, [bool]$Pass, [string]$Evidence)
    $script:Checks++
    $script:Results.Add([pscustomobject]@{ id = $Id; pass = $Pass; evidence = $Evidence })
    $tag = if ($Pass) { 'PASS' } else { 'FAIL' }
    Write-Host ("[{0}] {1} :: {2}" -f $tag, $Id, $Evidence)
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Text)
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    [IO.File]::WriteAllBytes($Path, [Text.Encoding]::UTF8.GetBytes($Text))
}

function Get-FileSha {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return '<missing>' }
    return (Get-FileHash -Algorithm SHA256 -Path $Path).Hash.ToLower()
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

function Start-Engine {
    param([string[]]$Arguments, [string]$LogName)
    $out = Join-Path $LogRoot ($LogName + '.out.log')
    $err = Join-Path $LogRoot ($LogName + '.err.log')
    Remove-Item -Path $out, $err -ErrorAction SilentlyContinue
    $proc = Start-Process -FilePath $Engine -ArgumentList $Arguments -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden
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
    # TASK-028 D-1: the shared, hardened `--import` runner
    # (`scripts\mcp_import_guard.ps1`): exit code checked, bounded retry,
    # and every failure prints the command, the exit code, the project path
    # and the log tail. The bespoke loop this replaces did the first two and
    # only this file knew how to report the third.
    $result = Import-McpProject -Engine $Engine -Path $Path -LogDirectory $LogRoot -Name $LogName
    # TASK-047 section 1: `Import-McpProject` returns the exact command line it
    # ran, so an `--import` process that asked for 9877 would be caught too.
    Register-McpPortGuardCommandLine -Guard $script:McpPortGuard -CommandLine $result.command
    $script:LastImportAttempts = $result.attempts
    Write-Host ('import {0}: exit 0 on attempt {1}' -f $Path, $result.attempts)
    return $result.attempts
}

function Format-CallBody {
    param([string]$Tool, $Arguments, [int]$Id = 1)
    $envelope = @{
        jsonrpc = '2.0'
        id      = $Id
        method  = 'tools/call'
        params  = @{ name = $Tool; arguments = $Arguments }
    }
    return (ConvertTo-Json -InputObject $envelope -Depth 20 -Compress)
}

function Invoke-Curl {
    param([string]$Id, [string]$Json, [int]$Port, [int]$MaxTimeSec = 90)
    $bodyFile = Join-Path $Evid ("{0}.request.json" -f $Id)
    $respFile = Join-Path $Evid ("{0}.response.json" -f $Id)
    if ($null -eq $Envelope -or $null -eq $Envelope.error) { return 0 }
    return [int]$Envelope.error.code
}

function Get-ErrorMessage {
    param($Envelope)
    if ($null -eq $Envelope -or $null -eq $Envelope.error) { return '' }
    return [string]$Envelope.error.message
}


# The tool names of a `tools/list` body that are really present, by literal
# containment on the JSON text. Deliberately not `-match`: a pattern built from a
# name would be a *regex*, and `Where-Object { $text -match ('"' + $n + '"') }`
# matched nothing at all in PowerShell 5.1 (the operator is not `-like`), which
# silently turned every "is it live?" question into "yes". `IndexOf` with
# `Ordinal` on the exact quoted name has no such failure mode.
function Get-LiveToolNames {
    param([string]$JsonText, [string[]]$Candidates)
    $found = @()
    foreach ($name in $Candidates) {
        if ($JsonText.IndexOf('"' + [string]$name + '"', [StringComparison]::Ordinal) -ge 0) {
            $found += [string]$name
        }
    }
    return $found
}

function Get-MissingToolNames {
    param([string]$JsonText, [string[]]$Candidates)
    $missing = @()
    foreach ($name in $Candidates) {
        if ($JsonText.IndexOf('"' + [string]$name + '"', [StringComparison]::Ordinal) -lt 0) {
            $missing += [string]$name
        }
    }
    return $missing
}

# The `scope` of one tool, straight out of the parsed rename map, with `'?'` for
# "the map does not declare it" - deliberately distinct from an empty string, so
# a missing entry cannot be mistaken for a scope. (`$hashtable[$key] -notlike
# 'game'` is `$true` for a missing key, which is how a "not the game endpoint's
# tool" filter can silently swallow a typo; this script was measured doing
# exactly that.)
function Get-ToolScope {
    param($JsonMap, [string]$Name)
    foreach ($entry in @($JsonMap.tools)) {
        if ([string]$entry.new_name -ceq $Name) { return [string]$entry.scope }
    }
    return '?'
}

function Get-StatusProbe {
    param([int]$Port)
Write-Host '============================================================='
Write-Host ' TASK-019 gate 2 evidence -- B4 (7 tools) and M4 closure'
Write-Host '============================================================='

if (-not (Test-Path $Engine)) { Write-Host "FATAL: engine binary not found: $Engine"; exit 2 }
Remove-Item -Recurse -Force $Scratch, $LogRoot, $Evid -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $Scratch, $LogRoot, $Evid | Out-Null

$GameProject = Join-Path $Scratch 'game'
$userPortPidBefore = Get-ListenerPid -Port $UserPort
Write-Host ("user editor on {0} before run: pid={1}" -f $UserPort, $userPortPidBefore)
# TASK-047 section 1: the 9877 judgement is the shared six-way classification,
# not "a listener must exist" - see mcp_port_guard.ps1 for why that was an
# environment precondition rather than a regression.
$script:McpPortGuard = New-McpPortGuard -Port $UserPort -PidBefore $userPortPidBefore

$versionText = (& $Engine --version)
$headSha = (& git -C $RepoRoot rev-parse --short HEAD).Trim()
Write-Host ("engine --version: {0}; git HEAD: {1}" -f $versionText, $headSha)
Add-Check 'gate_version_matches_head' ($versionText.contains($headSha.Substring(0, 9))) ("engine='{0}' head='{1}'" -f $versionText, $headSha)

$EditorTools = @('editor_get_test_report', 'editor_analyze_screenshot_diff')
$GameTools = @(
    'running_game_assert_node_state',
    'running_game_assert_screen_text',
    'running_game_capture_signal_emissions',
    'running_game_run_test_scenario',
    'running_game_run_stress_test'
)
$AllB4 = $EditorTools + $GameTools

try {
    New-ScratchProject -Path $GameProject
    Write-Host 'importing the scratch project ...'
    $importAttempts = Import-Project -Path $GameProject -LogName 'import-game'
    Add-Check 'scratch_import_exit_code_is_zero' ($importAttempts -ge 1) ("imported with exit code 0 on attempt {0} (BOM-free .tscn/.gd/.godot)" -f $importAttempts)

    $script:EditorHandle = Start-Engine -Arguments @('--headless', '-e', '--path', $GameProject, "--mcp-port=$EditorPort") -LogName 'editor'
    if (-not (Wait-ForPump -Port $EditorPort -TimeoutMs 300000)) { throw 'editor endpoint never became ready' }
    $script:GameHandle = Start-Engine -Arguments @('--headless', '--path', $GameProject, "--mcp-port=$GamePort") -LogName 'game'
    if (-not (Wait-ForPump -Port $GamePort -TimeoutMs 240000)) { throw 'game endpoint never became ready' }

    $editorListText = Invoke-Curl -Id 'A1_editor_tools_list' -Json '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' -Port $EditorPort
    $gameListText = Invoke-Curl -Id 'A2_game_tools_list' -Json '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' -Port $GamePort
    # The advertised names, read from the `name` fields (see `Get-LiveToolNameSet`).
    # Every liveness question below is answered against these two sets.
    $editorNames = @(Get-LiveToolNameSet -JsonText $editorListText)
    $gameNames = @(Get-LiveToolNameSet -JsonText $gameListText)
    Add-Check 'A1_editor_tools_list_is_parseable' (($editorNames.Count -gt 0) -and ($editorNames.Count -eq ($editorNames | Sort-Object -Unique).Count)) ("9888 advertises {0} uniquely named tool(s)" -f $editorNames.Count)
    Add-Check 'A2_game_tools_list_is_parseable' (($gameNames.Count -gt 0) -and ($gameNames.Count -eq ($gameNames | Sort-Object -Unique).Count)) ("9889 advertises {0} uniquely named tool(s)" -f $gameNames.Count)

    # ------------------------------------------------------------------
    # A. process scope, both directions
    # ------------------------------------------------------------------
    $editorMissing = @(Get-MissingToolNames -LiveNames $editorNames -Candidates $EditorTools)
    $gameLeakedEditor = @(Get-LiveToolNames -LiveNames $gameNames -Candidates $EditorTools)
    $gameMissing = @(Get-MissingToolNames -LiveNames $gameNames -Candidates $GameTools)
    $editorLeakedGame = @(Get-LiveToolNames -LiveNames $editorNames -Candidates $GameTools)
    Add-Check 'A3_editor_endpoint_serves_the_two_editor_tools' ($editorMissing.Count -eq 0) ("missing on 9888: [" + ($editorMissing -join ', ') + "] sha256=" + (Get-FileSha (Join-Path $Evid 'A1_editor_tools_list.response.json')))
    Add-Check 'A4_game_endpoint_serves_the_five_game_tools' ($gameMissing.Count -eq 0) ("missing on 9889: [" + ($gameMissing -join ', ') + "] sha256=" + (Get-FileSha (Join-Path $Evid 'A2_game_tools_list.response.json')))
    Add-Check 'A5_editor_tools_absent_from_the_game_endpoint' ($gameLeakedEditor.Count -eq 0) ("editor-scope tools found on 9889: [" + ($gameLeakedEditor -join ', ') + "]")
    Add-Check 'A6_game_tools_absent_from_the_editor_endpoint' ($editorLeakedGame.Count -eq 0) ("game-scope tools found on 9888: [" + ($editorLeakedGame -join ', ') + "]")

    $leak1 = Invoke-Tool -Id 'A7_game_calls_editor_tool' -Tool 'editor_get_test_report' -Arguments @{ clear = $false } -Port $GamePort
    Add-Check 'A7_cross_endpoint_call_game_to_editor_is_32601' ((Get-ErrorCode $leak1) -eq -32601 -and $null -eq $leak1.result) ("code=" + (Get-ErrorCode $leak1) + " result_is_null=" + ($null -eq $leak1.result) + " message='" + (Get-ErrorMessage $leak1) + "'")
    $leak2 = Invoke-Tool -Id 'A8_editor_calls_game_tool' -Tool 'running_game_run_stress_test' -Arguments @{ count = 1 } -Port $EditorPort
    Add-Check 'A8_cross_endpoint_call_editor_to_game_is_32601' ((Get-ErrorCode $leak2) -eq -32601 -and $null -eq $leak2.result) ("code=" + (Get-ErrorCode $leak2) + " result_is_null=" + ($null -eq $leak2.result) + " message='" + (Get-ErrorMessage $leak2) + "'")

    # ------------------------------------------------------------------
    # B. B4 = 7/7 and M4 = 47/47 machine checks
    # ------------------------------------------------------------------
    $b4 = ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 (Join-Path $ModuleRoot 'docs\tool-groups-b4.json'))
    $b3 = ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 (Join-Path $ModuleRoot 'docs\tool-groups-b3.json'))
    $renameMap = ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 (Join-Path $ModuleRoot 'docs\tool-rename-map.json'))
    # field is the authority, TASK-006 section 2). B4 is split 2 editor-scope /
    # 5 game-scope with no both-scope member, so the editor endpoint - which
    # serves editor + both - carries all seven. The two sets are therefore simply
    # the two halves of the manifest union, and neither is a hand-written list.
    #
    # (The scopes are read per tool below rather than through a `-notlike` filter
    # over the map lookup: a hashtable lookup that misses answers `$null`, and
    # `$null -notlike 'game'` is `$true`, so such a filter silently counts a
    # missing map entry as an editor tool. `Get-ToolScope` reports the three
    # spellings explicitly and a check below fails loudly on a `?`.)
    $b4EditorExpected = @($b4Impl | Where-Object { (Get-ToolScope -JsonMap $renameMap -Name ([string]$_)) -in @('editor', 'both') })
    $b4EditorMissing = @(Get-MissingToolNames -LiveNames $editorNames -Candidates $b4EditorExpected)
    $b4GameMissing = @(Get-MissingToolNames -LiveNames $gameNames -Candidates $b4Game)
    $b4UnknownScope = @($b4Impl | Where-Object { (Get-ToolScope -JsonMap $renameMap -Name ([string]$_)) -eq '?' })
    Add-Check 'B0_every_b4_tool_has_a_scope_in_the_rename_map' ($b4UnknownScope.Count -eq 0) ("B4 tools whose scope the rename map does not declare: [{0}]" -f ($b4UnknownScope -join ', '))
    Add-Check 'B1_b4_is_complete_7_of_7' (($b4.total -eq 7) -and ($b4All.Count -eq 7) -and ($b4Groups.Count -eq 3) -and ($b4Impl.Count -eq 7) -and ($b4ImplGroups.Count -eq 3)) ("manifest total={0} tools={1} groups={2} implemented_tools={3} implemented_groups={4}" -f $b4.total, $b4All.Count, $b4Groups.Count, $b4Impl.Count, $b4ImplGroups.Count)
    Add-Check 'B2_b4_live_all_7_on_9888' (($b4EditorMissing.Count -eq 0) -and ($b4EditorExpected.Count -eq 7)) ("B4 tools live on 9888: {0}/7 (the endpoint serves editor + both, and B4 has no both-scope member, so every B4 tool is live there); missing: [{1}]" -f $b4EditorExpected.Count, ($b4EditorMissing -join ', '))
    Add-Check 'B3_b4_live_on_9889_matches_scope' (($b4GameMissing.Count -eq 0) -and ($b4GameLeaked.Count -eq 0)) ("B4 tools with scope<>editor: {0}, missing on 9889: [{1}]; B4 editor-scope tools: {2} (none on 9889: [{3}])" -f $b4Game.Count, ($b4GameMissing -join ', '), $b4Editor.Count, ($b4GameLeaked -join ', '))

    $b3Groups = @($b3.groups)
    $b3Impl = @($b3Groups | Where-Object { $_.implemented -eq $true } | ForEach-Object { $_.tools })
    $m4 = @($b3Impl + $b4Impl | Sort-Object -Unique)
    Add-Check 'B4_m4_is_47_of_47' (($b3Impl.Count -eq 40) -and ($b4Impl.Count -eq 7) -and ($m4.Count -eq 47)) ("B3 implemented={0} B4 implemented={1} M4 union={2}/47" -f $b3Impl.Count, $b4Impl.Count, $m4.Count)
    $m4OnEditor = @(Get-LiveToolNames -LiveNames $editorNames -Candidates $m4)
    $m4EditorExpected = @($m4 | Where-Object { (Get-ToolScope -JsonMap $renameMap -Name ([string]$_)) -in @('editor', 'both') })
    $m4OnGame = @(Get-LiveToolNames -LiveNames $gameNames -Candidates $m4)
    $m4GameExpected = @($m4 | Where-Object { (Get-ToolScope -JsonMap $renameMap -Name ([string]$_)) -in @('game', 'both') })
    $m4MissingEditor = @(Get-MissingToolNames -LiveNames $editorNames -Candidates $m4EditorExpected)
    $m4MissingGame = @(Get-MissingToolNames -LiveNames $gameNames -Candidates $m4GameExpected)
    $m4UnknownScope = @($m4 | Where-Object { (Get-ToolScope -JsonMap $renameMap -Name ([string]$_)) -eq '?' })
    # --- C4 editor_analyze_screenshot_diff --------------------------------
    # Two real PNGs, produced by the engine itself: the module's
    # `editor_capture_screenshot` cannot run headless (no framebuffer - exactly
    # the capability gate GDR-20 section 10 describes), so the bytes come from
    # `project_get_resource_preview`, which encodes whatever image the project
    # holds with the engine's own PNG writer. The two files are written from that
    # base64 by PowerShell, so the diff input is engine-produced and
    # engine-decodable.
    $pngA = Join-Path $GameProject 'a.png'
    $pngB = Join-Path $GameProject 'b.png'
    $preview = Invoke-Tool -Id 'C4a_engine_png_probe' -Tool 'project_get_resource_preview' -Arguments @{ path = 'res://source.png'; max_size = 8 } -Port $EditorPort
    $previewPayload = Get-Payload $preview
    $previewPrefix = ''
    if ($null -ne $previewPayload -and $null -ne $previewPayload.image_base64) {
        $previewBase64 = [string]$previewPayload.image_base64
        if ($previewBase64.Length -ge 12) { $previewPrefix = $previewBase64.Substring(0, 12) }
    }
    Add-Check 'C4a_the_engine_produced_a_png_to_diff' (($null -ne $previewPayload) -and ([string]$previewPayload.format -eq 'png') -and ($previewPrefix.StartsWith('iVBORw0KGgo'))) ("width={0} height={1} format={2} base64_prefix={3}" -f $previewPayload.width, $previewPayload.height, $previewPayload.format, $previewPrefix)
    if ($null -eq $previewPayload -or $null -eq $previewPayload.image_base64) { throw 'the PNG probe failed; the diff evidence cannot be produced on a corrupt image' }
    [IO.File]::WriteAllBytes($pngA, [Convert]::FromBase64String([string]$previewPayload.image_base64))
    [IO.File]::WriteAllBytes($pngB, [Convert]::FromBase64String([string]$previewPayload.image_base64))
    # The project needs to see the two new files before `res://a.png` resolves.
    $null = Import-Project -Path $GameProject -LogName 'import-game-after-pngs'
    $diffIdentical = Invoke-Tool -Id 'C4_screenshot_diff_identical' -Tool 'editor_analyze_screenshot_diff' -Arguments @{ image_a = 'res://a.png'; image_b = 'res://b.png' } -Port $EditorPort
    $diffIdenticalPayload = Get-Payload $diffIdentical
    Add-Check 'C4_screenshot_diff_success_identical' (($null -ne $diffIdenticalPayload) -and ($diffIdenticalPayload.identical -eq $true) -and ($diffIdenticalPayload.changed_pixels -eq 0) -and ($diffIdenticalPayload.width -ge 1) -and ($diffIdenticalPayload.height -ge 1)) ("payload=" + (ConvertTo-Json -InputObject $diffIdenticalPayload -Depth 8 -Compress))
    Add-Check 'C5_screenshot_diff_returns_a_diff_png' ($null -ne $diffIdenticalPayload -and -not [string]::IsNullOrEmpty([string]$diffIdenticalPayload.diff_image_base64)) ("diff_image_base64 length=" + ([string]$diffIdenticalPayload.diff_image_base64).Length)
    $diffMissing = Invoke-Tool -Id 'C6_screenshot_diff_missing_arg' -Tool 'editor_analyze_screenshot_diff' -Arguments @{ image_b = 'res://b.png' } -Port $EditorPort
    Add-Check 'C6_screenshot_diff_missing_image_a_is_32602' ((Get-ErrorCode $diffMissing) -eq -32602 -and (Get-ErrorMessage $diffMissing) -match 'image_a') ("code=" + (Get-ErrorCode $diffMissing) + " message='" + (Get-ErrorMessage $diffMissing) + "'")
    $diffBadPath = Invoke-Tool -Id 'C7_screenshot_diff_bad_path' -Tool 'editor_analyze_screenshot_diff' -Arguments @{ image_a = 'res://does_not_exist.png'; image_b = 'res://b.png' } -Port $EditorPort
    Add-Check 'C7_screenshot_diff_missing_file_is_32001' ((Get-ErrorCode $diffBadPath) -eq -32001) ("code=" + (Get-ErrorCode $diffBadPath) + " message='" + (Get-ErrorMessage $diffBadPath) + "'")
    $diffBadThreshold = Invoke-Tool -Id 'C8_screenshot_diff_bad_threshold' -Tool 'editor_analyze_screenshot_diff' -Arguments @{ image_a = 'res://a.png'; image_b = 'res://b.png'; threshold = 300 } -Port $EditorPort
    Add-Check 'C8_screenshot_diff_threshold_out_of_range_is_32602' ((Get-ErrorCode $diffBadThreshold) -eq -32602) ("code=" + (Get-ErrorCode $diffBadThreshold) + " message='" + (Get-ErrorMessage $diffBadThreshold) + "'")
    # P-1: the deleted string grammar. A `Vector2(...)` string can no longer be
    # silently written, and the *live* form of that is the write tool refusing it.
    $p1 = Invoke-Tool -Id 'C9_p1_vector2_string_is_refused' -Tool 'editor_set_node_property' -Arguments @{ path = 'Main'; property = 'position'; value = 'Vector2(1,2)' } -Port $EditorPort
    Add-Check 'C9_p1_vector2_string_refused_on_the_wire' ((Get-ErrorCode $p1) -eq -32602) ("code=" + (Get-ErrorCode $p1) + " message='" + (Get-ErrorMessage $p1) + "'")

    # --- C10 running_game_assert_node_state: pass and structured failure ---
    $nodePass = Invoke-Tool -Id 'C10_assert_node_state_pass' -Tool 'running_game_assert_node_state' -Arguments @{ node_path = 'Actor'; property = 'position'; expected = @{ x = 3; y = 4 }; operator = 'eq' } -Port $GamePort
    $nodePassPayload = Get-Payload $nodePass
    Add-Check 'C10_assert_node_state_passes_a_true_assertion' (($null -ne $nodePassPayload) -and ($nodePassPayload.passed -eq $true) -and ($nodePassPayload.assertion -eq 'node_state')) ("payload=" + (ConvertTo-Json -InputObject $nodePassPayload -Depth 8 -Compress))

    $nodeFail = Invoke-Tool -Id 'C11_assert_node_state_failure' -Tool 'running_game_assert_node_state' -Arguments @{ node_path = 'Actor'; property = 'position'; expected = @{ x = 9; y = 9 }; operator = 'eq' } -Port $GamePort
    $nodeFailPayload = Get-Payload $nodeFail
    Add-Check 'C11_assert_node_state_failure_is_structured' (($null -ne $nodeFailPayload) -and ($nodeFailPayload.passed -eq $false) -and ($null -ne $nodeFailPayload.expected) -and ($null -ne $nodeFailPayload.actual) -and ($nodeFailPayload.expected.x -eq 9) -and ($nodeFailPayload.actual.x -eq 3)) ("payload=" + (ConvertTo-Json -InputObject $nodeFailPayload -Depth 8 -Compress))

    $nodeMissing = Invoke-Tool -Id 'C12_assert_node_state_missing_arg' -Tool 'running_game_assert_node_state' -Arguments @{ node_path = 'Actor'; property = 'position' } -Port $GamePort
    Add-Check 'C12_assert_node_state_missing_expected_is_32602' ((Get-ErrorCode $nodeMissing) -eq -32602 -and (Get-ErrorMessage $nodeMissing) -match 'expected') ("code=" + (Get-ErrorCode $nodeMissing) + " message='" + (Get-ErrorMessage $nodeMissing) + "'")
    $nodeBadOp = Invoke-Tool -Id 'C13_assert_node_state_bad_operator' -Tool 'running_game_assert_node_state' -Arguments @{ node_path = 'Actor'; property = 'position'; expected = 1; operator = 'approximately' } -Port $GamePort
    Add-Check 'C13_assert_node_state_bad_operator_is_32602' ((Get-ErrorCode $nodeBadOp) -eq -32602 -and (Get-ErrorMessage $nodeBadOp) -match 'type_is') ("code=" + (Get-ErrorCode $nodeBadOp) + " message='" + (Get-ErrorMessage $nodeBadOp) + "'")
    $nodeNotFound = Invoke-Tool -Id 'C14_assert_node_state_bad_node' -Tool 'running_game_assert_node_state' -Arguments @{ node_path = 'Nope'; property = 'position'; expected = 1 } -Port $GamePort
    Add-Check 'C14_assert_node_state_unknown_node_is_32001' ((Get-ErrorCode $nodeNotFound) -eq -32001) ("code=" + (Get-ErrorCode $nodeNotFound) + " message='" + (Get-ErrorMessage $nodeNotFound) + "' suggestion='" + ([string]$nodeNotFound.error.data.suggestion) + "'")
    $nodeBadProperty = Invoke-Tool -Id 'C15_assert_node_state_bad_property' -Tool 'running_game_assert_node_state' -Arguments @{ node_path = 'Actor'; property = 'not_a_property'; expected = 1 } -Port $GamePort
    Add-Check 'C15_assert_node_state_unknown_property_is_32001' ((Get-ErrorCode $nodeBadProperty) -eq -32001) ("code=" + (Get-ErrorCode $nodeBadProperty) + " message='" + (Get-ErrorMessage $nodeBadProperty) + "'")

    # --- C16 running_game_assert_screen_text: pass and structured failure --
    $textPass = Invoke-Tool -Id 'C16_assert_screen_text_pass' -Tool 'running_game_assert_screen_text' -Arguments @{ text = 'Hello'; partial = $true } -Port $GamePort
    $textPassPayload = Get-Payload $textPass
    Add-Check 'C16_assert_screen_text_finds_real_control_text' (($null -ne $textPassPayload) -and ($textPassPayload.passed -eq $true) -and ($textPassPayload.source -eq 'control_tree') -and ($textPassPayload.matched_element.text -eq 'Hello MCP')) ("payload=" + (ConvertTo-Json -InputObject $textPassPayload -Depth 8 -Compress))
    $textFail = Invoke-Tool -Id 'C17_assert_screen_text_failure' -Tool 'running_game_assert_screen_text' -Arguments @{ text = 'Goodbye'; partial = $true } -Port $GamePort
    $textFailPayload = Get-Payload $textFail
    $visibleTexts = @($textFailPayload.visible_texts)
    Add-Check 'C17_assert_screen_text_failure_lists_the_search_space' (($null -ne $textFailPayload) -and ($textFailPayload.passed -eq $false) -and ($visibleTexts -contains 'Hello MCP') -and ($visibleTexts -contains 'Go')) ("passed={0} visible_texts=[{1}]" -f $textFailPayload.passed, ($visibleTexts -join ' | '))
    Add-Check 'C18_assert_screen_text_skips_invisible_text' ($visibleTexts -notcontains 'Secret') ("'Secret' (a hidden Label) in visible_texts: {0}" -f ($visibleTexts -contains 'Secret'))
    $textCase = Invoke-Tool -Id 'C19_assert_screen_text_case' -Tool 'running_game_assert_screen_text' -Arguments @{ text = 'hello mcp'; partial = $false; case_sensitive = $false } -Port $GamePort
    $textCasePayload = Get-Payload $textCase
    Add-Check 'C19_assert_screen_text_honours_case_sensitive_false' (($null -ne $textCasePayload) -and ($textCasePayload.passed -eq $true)) ("passed={0} case_sensitive={1} partial={2}" -f $textCasePayload.passed, $textCasePayload.case_sensitive, $textCasePayload.partial)
    $textMissing = Invoke-Tool -Id 'C20_assert_screen_text_missing_arg' -Tool 'running_game_assert_screen_text' -Arguments @{ partial = $true } -Port $GamePort
    Add-Check 'C20_assert_screen_text_missing_text_is_32602' ((Get-ErrorCode $textMissing) -eq -32602 -and (Get-ErrorMessage $textMissing) -match 'text') ("code=" + (Get-ErrorCode $textMissing) + " message='" + (Get-ErrorMessage $textMissing) + "'")

    # ------------------------------------------------------------------
    # D. the accumulator: per-process state, and the chain inside one process
    # ------------------------------------------------------------------
    # `editor_get_test_report` reads an accumulator that lives in the **module**,
    # inside one process. The editor endpoint therefore has its own, and the
    # game-scope assertions of section C ran in the game process: they must NOT
    # appear here. That is asserted rather than described, because a report that
    # silently mixed the two would be worse than an empty one.
    $chainClear = Invoke-Tool -Id 'D1_chain_report_cleared' -Tool 'editor_get_test_report' -Arguments @{ clear = $true } -Port $EditorPort
    $chainClearPayload = Get-Payload $chainClear
    Add-Check 'D1_editor_report_clears_to_nothing' (($null -ne $chainClearPayload) -and ($null -ne $chainClearPayload.total) -and ($null -ne $chainClearPayload.source)) ("after clear: total={0} no_results={1} source={2}" -f $chainClearPayload.total, $chainClearPayload.no_results, $chainClearPayload.source)
    $chainAfter = Invoke-Tool -Id 'D2_chain_report_still_empty' -Tool 'editor_get_test_report' -Arguments @{ clear = $false } -Port $EditorPort
    $chainAfterPayload = Get-Payload $chainAfter
    Add-Check 'D2_editor_report_is_empty_without_editor_assertions' (($null -ne $chainAfterPayload) -and ($chainAfterPayload.total -eq 0) -and ($chainAfterPayload.no_results -eq $true)) ("total={0} no_results={1} all_passed={2} pass_rate='{3}'" -f $chainAfterPayload.total, $chainAfterPayload.no_results, $chainAfterPayload.all_passed, $chainAfterPayload.pass_rate)
    $afterCalls = Invoke-Tool -Id 'D3_editor_report_unaffected_by_game_assertions' -Tool 'editor_get_test_report' -Arguments @{ clear = $false } -Port $EditorPort
    $afterCallsPayload = Get-Payload $afterCalls
    Add-Check 'D3_game_assertions_do_not_leak_into_the_editor_report' (($null -ne $afterCallsPayload) -and ($afterCallsPayload.total -eq 0)) ("total={0} after four game-scope assertions (C10/C11/C16/C17) ran in the game process" -f $afterCallsPayload.total)
    # The editor-side chain inside one process: `editor_execute_gdscript` runs
    # there, and its own answer is what proves the two tools share a process.
    $editorEval = Invoke-Tool -Id 'D4_editor_process_probe' -Tool 'editor_execute_gdscript' -Arguments @{ code = 'return Engine.get_main_loop() != null' } -Port $EditorPort
    Add-Check 'D4_the_editor_tools_share_the_process_with_the_editor_executor' ($null -ne (Get-Payload $editorEval)) ("editor_execute_gdscript answered: " + (ConvertTo-Json -InputObject (Get-Payload $editorEval) -Compress))

    # ------------------------------------------------------------------
    # E. the scenario runner: structured conclusion, pass and deliberate fail
    # ------------------------------------------------------------------
    $passScenario = @{
        steps = @(
            @{ type = 'wait'; seconds = 0.1 },
            @{ type = 'assert'; node_path = 'Actor'; property = 'position'; expected = @{ x = 3; y = 4 }; operator = 'eq' },
            @{ type = 'assert'; text = 'Hello MCP'; partial = $true },
            @{ type = 'wait'; seconds = 0.1 }
        )
    }
    $passScenarioResult = Invoke-Tool -Id 'E1_run_test_scenario_pass' -Tool 'running_game_run_test_scenario' -Arguments $passScenario -Port $GamePort -MaxTimeSec 120
    $passScenarioPayload = Get-Payload $passScenarioResult
    Add-Check 'E1_run_test_scenario_structured_pass' (($null -ne $passScenarioPayload) -and ($passScenarioPayload.all_passed -eq $true) -and ($passScenarioPayload.passed -eq 2) -and ($passScenarioPayload.failed -eq 0) -and ($passScenarioPayload.total_steps -eq 4) -and ($passScenarioPayload.completed_steps -eq 4) -and ($null -ne $passScenarioPayload.duration_ms)) ("payload=" + (ConvertTo-Json -InputObject $passScenarioPayload -Depth 10 -Compress))

    $failScenario = @{
        steps = @(
            @{ type = 'wait'; seconds = 0.05 },
            @{ type = 'assert'; node_path = 'Actor'; property = 'position'; expected = @{ x = 999; y = 999 }; operator = 'eq' },
            @{ type = 'assert'; text = 'ThisTextIsNotOnScreen'; partial = $true }
        )
    }
    $failScenarioResult = Invoke-Tool -Id 'E2_run_test_scenario_deliberate_failure' -Tool 'running_game_run_test_scenario' -Arguments $failScenario -Port $GamePort -MaxTimeSec 120
    $failScenarioPayload = Get-Payload $failScenarioResult
    $failSteps = @($failScenarioPayload.results)
    $failVerdicts = @($failSteps | Where-Object { $null -ne $_.passed -and $_.passed -eq $false })
    Add-Check 'E2_run_test_scenario_reports_a_deliberate_failure' (($null -ne $failScenarioPayload) -and ($failScenarioPayload.all_passed -eq $false) -and ($failScenarioPayload.failed -eq 2) -and ($failScenarioPayload.passed -eq 0) -and ($failVerdicts.Count -eq 2)) ("all_passed={0} passed={1} failed={2} failed_verdict_steps={3}" -f $failScenarioPayload.all_passed, $failScenarioPayload.passed, $failScenarioPayload.failed, $failVerdicts.Count)
    Add-Check 'E3_the_failing_assertion_carries_expected_and_actual' (($null -ne $failScenarioPayload) -and ($failVerdicts[0].expected.x -eq 999) -and ($failVerdicts[0].actual.x -eq 3) -and ($null -ne $failVerdicts[0].reason)) ("step={0} expected={1} actual={2} reason='{3}'" -f $failVerdicts[0].step, (ConvertTo-Json -InputObject $failVerdicts[0].expected -Compress), (ConvertTo-Json -InputObject $failVerdicts[0].actual -Compress), $failVerdicts[0].reason)
    Add-Check 'E4_the_failing_scenario_is_not_all_passed_with_zero_assertions' (($null -ne $failScenarioPayload) -and ($failScenarioPayload.all_passed -eq $false)) ("all_passed={0} (a scenario that asserts nothing must not be 'all passed' either)" -f $failScenarioPayload.all_passed)

    $scenarioMissing = Invoke-Tool -Id 'E5_run_test_scenario_missing_arg' -Tool 'running_game_run_test_scenario' -Arguments @{ steps = @() } -Port $GamePort
    Add-Check 'E5_run_test_scenario_empty_steps_is_32602' ((Get-ErrorCode $scenarioMissing) -eq -32602) ("code=" + (Get-ErrorCode $scenarioMissing) + " message='" + (Get-ErrorMessage $scenarioMissing) + "'")
    $scenarioBadStep = Invoke-Tool -Id 'E6_run_test_scenario_bad_step' -Tool 'running_game_run_test_scenario' -Arguments @{ steps = @(@{ type = 'jump' }) } -Port $GamePort
    Add-Check 'E6_run_test_scenario_unknown_step_type_is_32602' ((Get-ErrorCode $scenarioBadStep) -eq -32602) ("code=" + (Get-ErrorCode $scenarioBadStep) + " message='" + (Get-ErrorMessage $scenarioBadStep) + "'")
    $scenarioScenePath = Invoke-Tool -Id 'E7_run_test_scenario_scene_path_refused' -Tool 'running_game_run_test_scenario' -Arguments @{ steps = @(@{ type = 'wait'; seconds = 0 }); scene_path = 'main' } -Port $GamePort
    Add-Check 'E7_run_test_scenario_scene_path_is_refused' ((Get-ErrorCode $scenarioScenePath) -eq -32602 -and (Get-ErrorMessage $scenarioScenePath) -match 'scene_path') ("code=" + (Get-ErrorCode $scenarioScenePath) + " message='" + (Get-ErrorMessage $scenarioScenePath) + "'")

    Add-Check 'F3_capture_signal_emissions_missing_node_paths_is_32602' ((Get-ErrorCode $signalMissing) -eq -32602 -and (Get-ErrorMessage $signalMissing) -match 'node_paths') ("code=" + (Get-ErrorCode $signalMissing) + " message='" + (Get-ErrorMessage $signalMissing) + "'")
    $signalBadNode = Invoke-Tool -Id 'F4_capture_signal_emissions_bad_node' -Tool 'running_game_capture_signal_emissions' -Arguments @{ node_paths = @('Nope'); duration_ms = 200 } -Port $GamePort
    Add-Check 'F4_capture_signal_emissions_unknown_node_is_32001' ((Get-ErrorCode $signalBadNode) -eq -32001) ("code=" + (Get-ErrorCode $signalBadNode) + " message='" + (Get-ErrorMessage $signalBadNode) + "'")
    $signalBadDuration = Invoke-Tool -Id 'F5_capture_signal_emissions_bad_duration' -Tool 'running_game_capture_signal_emissions' -Arguments @{ node_paths = @('Main'); duration_ms = 600001 } -Port $GamePort
    Add-Check 'F5_capture_signal_emissions_over_long_window_is_32602' ((Get-ErrorCode $signalBadDuration) -eq -32602) ("code=" + (Get-ErrorCode $signalBadDuration) + " message='" + (Get-ErrorMessage $signalBadDuration) + "'")

    # The window really ends: a second call with an empty filter watches every
    # signal of the node and still terminates.
    $signalsAll = Invoke-Tool -Id 'F6_capture_signal_emissions_all_signals' -Tool 'running_game_capture_signal_emissions' -Arguments @{ node_paths = @('Main'); duration_ms = 400 } -Port $GamePort -MaxTimeSec 120
    $signalsAllPayload = Get-Payload $signalsAll
    Add-Check 'F6_capture_signal_emissions_without_a_filter_still_terminates' (($null -ne $signalsAllPayload) -and ($signalsAllPayload.watch_ended -eq 'duration')) ("watched={0} count={1} watch_ended={2}" -f @($signalsAllPayload.watched).Count, $signalsAllPayload.count, $signalsAllPayload.watch_ended)

    # ------------------------------------------------------------------
    # G. liveness: the game survived the whole battery (no crash, no leak)
    # ------------------------------------------------------------------
    $stillAlive = Get-StatusProbe -Port $GamePort
    Add-Check 'G1_the_game_process_survived_the_whole_battery' (($null -ne $stillAlive) -and ($null -ne $stillAlive.frame_count)) ("frame_count=" + $stillAlive.frame_count + " pending=" + $stillAlive.pending + " pending_connections=" + $stillAlive.pending_connections)
    $editorAlive = Get-StatusProbe -Port $EditorPort
    Add-Check 'G2_the_editor_process_survived_the_whole_battery' (($null -ne $editorAlive) -and ($null -ne $editorAlive.frame_count)) ("frame_count=" + $editorAlive.frame_count + " pending=" + $editorAlive.pending + " pending_connections=" + $editorAlive.pending_connections)

} finally {
    Stop-Engine -Handle $script:GameHandle
    Stop-Engine -Handle $script:EditorHandle
}

$userPortPidAfter = Get-ListenerPid -Port $UserPort
$portGuardResult = Complete-McpPortGuard -Guard $script:McpPortGuard -PidAfter $userPortPidAfter
Add-Check 'H1_user_editor_port_9877_guard' $portGuardResult.pass $portGuardResult.evidence

# =============================================================================
# Summary
# =============================================================================
$failed = @($script:Results | Where-Object { $_.pass -eq $false })
Write-Host ''
Write-Host '============================================================='
Write-Host (" TASK-019 evidence summary: {0} checks, {1} passed, {2} failed" -f $script:Checks, ($script:Checks - $failed.Count), $failed.Count)
Write-Host '============================================================='
foreach ($result in $script:Results) {
    Write-Host (" {0}  {1}" -f $(if ($result.pass) { 'PASS' } else { 'FAIL' }), $result.id)
}
if ($failed.Count -gt 0) {
    Write-Host ''
    Write-Host 'FAILED CHECKS:'
    foreach ($result in $failed) { Write-Host (" - {0} :: {1}" -f $result.id, $result.evidence) }
    exit 1
}
Write-Host ''
Write-Host ("evidence directory: {0}" -f $Evid)
exit 0