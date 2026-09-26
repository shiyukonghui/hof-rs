# =============================================================================
#  mcp068_live.ps1 -- TASK-068 live evidence (pure ASCII).
#
#  Three questions, measured on a real engine and real MCP ports:
#
#    (1) `tools/list` on the EDITOR endpoint: do the two clarified descriptions
#        arrive as the contract spells them, and is `waited_seconds` still absent
#        from `running_game_run_test_scenario`'s `inputSchema` (i.e. no undeclared
#        input was added)?  (TASK-068 section 2.i + 2.ii.)
#
#    (2) `running_game_run_test_scenario` in a real GAME process: does a `wait`
#        step given `seconds` still work, and what does the result entry echo?
#        The two wait forms are measured separately because the echo mirrors
#        `seconds` in one (`:440`) and `timeout` in the other (`:459`).
#
#    (3) `project_list_scripts` on a real Mono project: are the engine's own
#        generated scripts under `res://.godot/mono/temp/obj/**` really in the
#        answer, and are the hand-written `.cs`/`.gd` files there too?  This is
#        evidence for the sentence added to the description, not for a behaviour
#        change (the walk is untouched by TASK-068).
#
#  Usage:
#    powershell -NoProfile -ExecutionPolicy Bypass -File modules\mcp_server\scripts\mcp068_live.ps1 `
#        -Label mono-head
#
#  Discipline: 9877 is asserted untouched before and after; only 9888/9889 are
#  used; only PIDs this script started are stopped; every request and response
#  body goes through `mcp_evidence_guard.ps1` (unique sha-bearing name).
# =============================================================================
param(
    [Parameter(Mandatory = $true)][string]$Label,
    [string]$EditorExe = 'bin\godot.windows.editor.x86_64.mono.console.exe',
    [string]$GameExe = 'bin\godot.windows.editor.x86_64.mono.console.exe',
    [switch]$SkipImport
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'mcp068_env.ps1')

if (-not [IO.Path]::IsPathRooted($EditorExe)) { $EditorExe = Join-Path $RepoRoot $EditorExe }
if (-not [IO.Path]::IsPathRooted($GameExe)) { $GameExe = Join-Path $RepoRoot $GameExe }

$RunDir = Join-Path $EvidenceRoot ('run-' + $Label)
$CallDir = Join-Path $RunDir 'calls'
$ListDir = Join-Path $RunDir 'tools_list'
Ensure-Dir $CallDir | Out-Null
Ensure-Dir $ListDir | Out-Null
Ensure-Dir $IoRoot | Out-Null

Write-Host ('=== mcp068_live label={0}' -f $Label)
Write-Host ('    editor    : {0}' -f $EditorExe)
Write-Host ('    game      : {0}' -f $GameExe)
Write-Host ('    run dir   : {0}' -f $RunDir)

Assert-Port9877Untouched 'p0_port_9877_free_before'
$editorVersion = Get-EngineVersion -Exe $EditorExe -LogPath (Join-Path $RunDir 'editor_version.txt')
$gameVersion = Get-EngineVersion -Exe $GameExe -LogPath (Join-Path $RunDir 'game_version.txt')
Add-Check 'p0_editor_version_recorded' ([bool]$editorVersion) $editorVersion
Add-Check 'p0_game_version_recorded' ([bool]$gameVersion) $gameVersion

# ---------------------------------------------------------------------------
#  Fixture: the Mono copy (needed by both the editor question and the game).
# ---------------------------------------------------------------------------
Reset-MonoProject | Out-Null
Add-Check 'p0_fixture_root_is_a_project' (Test-Path -LiteralPath (Join-Path $MonoProj 'project.godot')) ('project.godot at ' + $MonoProj)

$handWrittenCs = @(Get-ChildItem -LiteralPath (Join-Path $MonoProj 'scripts') -Filter '*.cs' -File | ForEach-Object { $_.Name })
$handWrittenGd = @(Get-ChildItem -LiteralPath (Join-Path $MonoProj 'scripts') -Filter '*.gd' -File | ForEach-Object { $_.Name })
$generatedOnDisk = @(Get-ChildItem -LiteralPath $MonoProj -Recurse -Filter '*.cs' -File | Where-Object { $_.FullName -like (Join-Path $MonoProj '.godot\*') } | ForEach-Object { $_.FullName })
Add-Check 'p0_fixture_has_hand_written_scripts' (($handWrittenCs.Count -ge 6) -and ($handWrittenGd.Count -ge 2)) ('scripts/ cs=' + $handWrittenCs.Count + ' gd=' + $handWrittenGd.Count)
Add-Check 'p0_fixture_has_generated_cs_on_disk' ($generatedOnDisk.Count -ge 2) ('generated .cs under .godot = ' + $generatedOnDisk.Count + ' [' + (($generatedOnDisk | ForEach-Object { $_.Substring($MonoProj.Length + 1) }) -join ', ') + ']')

if (-not $SkipImport) {
    $import = Import-Project -Engine $EditorExe -Path $MonoProj -Name ('import_' + $Label)
    Add-Check 'p0_import_exit0' ($import.exit_code -eq 0) ('attempts=' + $import.attempts + ' exit=' + $import.exit_code + ' log=' + $import.log)
}

if (Test-Path -LiteralPath $BreakoutDll) {
    $dllBytes = (Get-Item -LiteralPath $BreakoutDll).Length
    $dllSha = (Get-FileHash -LiteralPath $BreakoutDll -Algorithm SHA256).Hash.ToLower()
    $null = Write-McpSummary -RunDir $RunDir -Leaf 'p0_breakout_dll' -Object ([pscustomobject]@{
        path = $BreakoutDll; bytes = $dllBytes; sha256 = $dllSha
    })
    Add-Check 'p0_breakout_dll_measured' ($dllBytes -gt 0) ('bytes=' + $dllBytes + ' sha256=' + $dllSha)
} else {
    Add-Check 'p0_breakout_dll_measured' $false ('not found: ' + $BreakoutDll)
}

# ---------------------------------------------------------------------------
#  (1) editor endpoint: tools/list + project_list_scripts
# ---------------------------------------------------------------------------
Reset-McpCallSeq
$editor = Start-McpEditor -Exe $EditorExe -ProjectPath $MonoProj -Port $EditorPort
$editorPid = $editor.Id
Add-Heartbeat ('editor started pid=' + $editorPid)
$portUp = Wait-Port -Port $EditorPort -TimeoutSec 180
Add-Check 'p1_editor_port_bound' $portUp ('port ' + $EditorPort + ' listening')

$editorList = $null
$listScripts = $null
if ($portUp) {
    Start-Sleep -Seconds 3
    $editorList = Invoke-Raw -Port $EditorPort -Method 'tools/list' -Directory $ListDir -Leaf ($Label + '_editor_tools_list')
    $listScripts = Invoke-Tool -Port $EditorPort -Tool 'project_list_scripts' -Arguments ([ordered]@{}) -Directory $CallDir -Leaf ($Label + '_p3_list_scripts')
}
Stop-OwnProcess -Process $editor -LogPath $EditorOutLog
Start-Sleep -Seconds 2
Add-Heartbeat ('editor stopped pid=' + $editorPid)

$editorTools = @()
if ($null -ne $editorList) { $editorTools = @($editorList.Json.result.tools) }
Add-Check 'p1_editor_tools_list_parsed' ($editorTools.Count -gt 0) ('count=' + $editorTools.Count)

$LIST_SCRIPTS_TAIL = 'res://.godot/mono/temp/obj/**'
$WAITED_CLAUSE = 'waited_seconds'
# U+5217 U+51FA (the original head of `project_list_scripts`'s description) and
# U+8FD0 U+884C (the original head of `running_game_run_test_scenario`'s). A .ps1
# may be read with the ANSI code page when it has no BOM, so the literals are
# built from code points instead of being written into this ASCII file.
$HEAD_LIST_SCRIPTS = [string][char]0x5217 + [string][char]0x51FA
$HEAD_RUN_SCENARIO = [string][char]0x8FD0 + [string][char]0x884C

if ($editorTools.Count -gt 0) {
    $byName = @{}
    foreach ($tool in $editorTools) { $byName[[string]$tool.name] = $tool }

    # --- (2.i) project_list_scripts -----------------------------------------
    $ls = $byName['project_list_scripts']
    Add-Check 'p1_list_scripts_is_registered' ($null -ne $ls) 'name=project_list_scripts'
    if ($null -ne $ls) {
        $lsDesc = [string]$ls.description
        Add-Check 'p1_list_scripts_description_declares_the_godot_cache' ($lsDesc.Contains('.godot') -and $lsDesc.Contains($LIST_SCRIPTS_TAIL)) `
            ('description bytes=' + $lsDesc.Length + ' mentions .godot=' + $lsDesc.Contains('.godot') + ' mentions ' + $LIST_SCRIPTS_TAIL + '=' + $lsDesc.Contains($LIST_SCRIPTS_TAIL))
        Add-Check 'p1_list_scripts_description_keeps_the_original_head' ($lsDesc.StartsWith($HEAD_LIST_SCRIPTS)) ('head preserved=' + $lsDesc.StartsWith($HEAD_LIST_SCRIPTS))
        $lsProps = @($ls.inputSchema.properties.PSObject.Properties | ForEach-Object { $_.Name })
        Add-Check 'p1_list_scripts_schema_still_has_no_argument' ($lsProps.Count -eq 0) ('properties=' + ($lsProps -join ','))
        $null = Write-McpSummary -RunDir $RunDir -Leaf 'p1_editor_contract_entries' -Object ([pscustomobject]@{
            editor_tools = $editorTools.Count
            project_list_scripts_description = $lsDesc
            project_list_scripts_schema_properties = $lsProps
        })
    }

    # --- (2.ii) running_game_run_test_scenario ------------------------------
    # `scope = GAME`: this tool is NOT on the editor endpoint (asserted here),
    # so its live description is read from the GAME endpoint's `tools/list` in
    # the (2) block further down.
    $notOnEditor = $true
    foreach ($tool in $editorTools) { if ([string]$tool.name -eq 'running_game_run_test_scenario') { $notOnEditor = $false } }
    Add-Check 'p1_run_test_scenario_is_absent_from_the_editor_endpoint' $notOnEditor 'game-scope tool must not appear on 9888 (the game half is measured in p2)'
}

# --- (3) project_list_scripts really lists the generated scripts ------------
if ($null -ne $listScripts) {
    Add-Check 'p3_list_scripts_call_is_not_an_error' ((Get-ErrorCode $listScripts) -eq 0) ('code=' + (Get-ErrorCode $listScripts))
    $body = Get-ToolBody $listScripts
    if ($null -ne $body) {
        $scripts = @($body.scripts)
        $cache = Get-GodotCacheScripts $scripts
        $csInScripts = @($scripts | Where-Object { $_ -like 'res://scripts/*.cs' })
        $gdInScripts = @($scripts | Where-Object { $_ -like 'res://scripts/*.gd' })
        Add-Check 'p3_count_is_the_array_size' (([int]$body.count) -eq $scripts.Count) ('count=' + $body.count + ' array=' + $scripts.Count)
        Add-Check 'p3_generated_godot_cache_scripts_are_listed' ($cache.Count -ge 2) ('res://.godot/* = ' + $cache.Count + ' [' + ($cache -join ', ') + ']')
        Add-Check 'p3_generated_entries_are_under_the_mono_obj_path' (@($cache | Where-Object { $_ -like 'res://.godot/mono/temp/obj/*' }).Count -eq $cache.Count) ('cache paths=' + ($cache -join ','))
        Add-Check 'p3_hand_written_cs_listed' ($csInScripts.Count -eq $handWrittenCs.Count) ('res://scripts/*.cs listed=' + $csInScripts.Count + ' on disk=' + $handWrittenCs.Count)
        Add-Check 'p3_hand_written_gd_listed' ($gdInScripts.Count -eq $handWrittenGd.Count) ('res://scripts/*.gd listed=' + $gdInScripts.Count + ' on disk=' + $handWrittenGd.Count)
        $null = Write-McpSummary -RunDir $RunDir -Leaf 'p3_list_scripts_paths' -Object ([pscustomobject]@{
            count = $scripts.Count
            godot_cache = $cache
            scripts_dir_cs = $csInScripts
            scripts_dir_gd = $gdInScripts
            all = $scripts
        })
    }
}

# ---------------------------------------------------------------------------
#  (2) game endpoint: the wait step, both forms, plus the old-call control
# ---------------------------------------------------------------------------
Reset-McpCallSeq
$game = Start-McpGame -Exe $GameExe -ProjectPath $MonoProj -Port $GamePort
$gamePid = $game.Id
Add-Heartbeat ('game started pid=' + $gamePid)
$gameUp = Wait-Port -Port $GamePort -TimeoutSec 120
$roleLine = Wait-LogLine -Path $GameOutLog -Pattern 'role=game' -TimeoutSec 60
Add-Check 'p2_game_port_bound' $gameUp ('port ' + $GamePort + ' listening')
Add-Check 'p2_game_role_line' ([bool]$roleLine) ('role=game in the game stdout')
Start-Sleep -Seconds 3

$gameList = $null
$gameTools = @()
if ($gameUp) {
    $gameList = Invoke-Raw -Port $GamePort -Method 'tools/list' -Directory $ListDir -Leaf ($Label + '_game_tools_list')
    if ($null -ne $gameList) { $gameTools = @($gameList.Json.result.tools) }
}
Add-Check 'p2_game_tools_list_parsed' ($gameTools.Count -gt 0) ('count=' + $gameTools.Count)

# ---------------------------------------------------------------------------
#  (1b) the live descriptions vs the contract, verbatim
#
#  The engine has no access to `docs/`, so gate 1 is the check that the two
#  spellings agree. This is the same comparison for the two tools this task
#  moved, but derived from the contract file (no description text is written
#  into this ASCII script) and read from BOTH endpoints - the game-scope tool's
#  description only exists on 9889.
# ---------------------------------------------------------------------------
function Get-ContractDescriptions {
    $contractPath = Join-Path $McpRoot068 'docs\tools_list.renamed.json'
    $raw = [IO.File]::ReadAllText($contractPath, (New-Object Text.UTF8Encoding($false)))
    $doc = $raw | ConvertFrom-Json
    $map = @{}
    foreach ($tool in @($doc.result.tools)) { $map[[string]$tool.name] = [string]$tool.description }
    return $map
}

function Get-LiveDescription($Tools, [string]$Name) {
    foreach ($tool in @($Tools)) { if ([string]$tool.name -eq $Name) { return [string]$tool.description } }
    return ''
}

$contractDescriptions = Get-ContractDescriptions
Add-Check 'p1b_contract_read' ($contractDescriptions.Count -gt 0) ('contract descriptions=' + $contractDescriptions.Count)

$liveVsContract = @()
$scopeCases = @(
    [pscustomobject]@{ name = 'project_list_scripts'; tools = $editorTools; endpoint = 'editor_9888' },
    [pscustomobject]@{ name = 'project_list_scripts'; tools = $gameTools; endpoint = 'game_9889' },
    [pscustomobject]@{ name = 'running_game_run_test_scenario'; tools = $gameTools; endpoint = 'game_9889' }
)
foreach ($case in $scopeCases) {
    $live = Get-LiveDescription $case.tools $case.name
    $expected = [string]$contractDescriptions[$case.name]
    $equal = (($live.Length -gt 0) -and ($live -ceq $expected))
    Add-Check ('p1b_' + $case.name + '_live_description_equals_contract_' + $case.endpoint) $equal `
        ('live bytes=' + $live.Length + ' contract bytes=' + $expected.Length + ' equal=' + $equal)
    $liveVsContract += [pscustomobject]@{ name = $case.name; endpoint = $case.endpoint; live = $live; contract = $expected; equal = $equal }
}
$null = Write-McpSummary -RunDir $RunDir -Leaf 'p1b_live_vs_contract_descriptions' -Object ([pscustomobject]@{ rows = $liveVsContract })

# --- (2.ii) the game-scope contract entry on its own endpoint ---------------
$gameRs = $null
foreach ($tool in $gameTools) { if ([string]$tool.name -eq 'running_game_run_test_scenario') { $gameRs = $tool } }
Add-Check 'p2_run_test_scenario_is_registered_on_the_game_endpoint' ($null -ne $gameRs) ('game tools=' + $gameTools.Count)
if ($null -ne $gameRs) {
    $rsDesc = [string]$gameRs.description
    $stepProps = @($gameRs.inputSchema.properties.steps.items.properties.PSObject.Properties | ForEach-Object { $_.Name })
    Add-Check 'p2_run_scenario_description_names_both_spellings' ($rsDesc.Contains('seconds') -and $rsDesc.Contains($WAITED_CLAUSE)) `
        ('description bytes=' + $rsDesc.Length + ' seconds=' + $rsDesc.Contains('seconds') + ' ' + $WAITED_CLAUSE + '=' + $rsDesc.Contains($WAITED_CLAUSE))
    Add-Check 'p2_run_scenario_description_keeps_the_original_head' ($rsDesc.StartsWith($HEAD_RUN_SCENARIO)) ('head preserved=' + $rsDesc.StartsWith($HEAD_RUN_SCENARIO))
    Add-Check 'p2_waited_seconds_is_not_an_input' (-not ($stepProps -contains $WAITED_CLAUSE)) ('step properties=' + ($stepProps -join ','))
    Add-Check 'p2_seconds_is_still_the_input_member' ($stepProps -contains 'seconds') ('step properties=' + ($stepProps -join ','))
    $null = Write-McpSummary -RunDir $RunDir -Leaf 'p2_run_scenario_schema' -Object ([pscustomobject]@{
        description = $rsDesc
        step_properties = $stepProps
    })
}

$waitSeconds = $null
$waitNode = $null
$waitNodeTimeout = $null
$legacy = $null
$badSeconds = $null
if ($gameUp) {
    # The "old call" control: this is the shape every existing caller uses, and
    # it is the shape REPORT-066's evidence used (`{"type":"wait","seconds":1.5}`).
    $waitSeconds = Invoke-Tool -Port $GamePort -Tool 'running_game_run_test_scenario' -Arguments ([ordered]@{
        steps = @(@{ type = 'wait'; seconds = 1.5 })
    }) -Directory $CallDir -Leaf ($Label + '_p2_wait_seconds')

    # The `waited_seconds` spelling as a REQUEST member: the clarification says it
    # is not an input. Whatever the argument gate answers, the answer is recorded
    # rather than assumed.
    $legacy = Invoke-Tool -Port $GamePort -Tool 'running_game_run_test_scenario' -Arguments ([ordered]@{
        steps = @(@{ type = 'wait'; waited_seconds = 0.05 })
    }) -Directory $CallDir -Leaf ($Label + '_p2_wait_legacy_name')

    # A `seconds` value that is not a number must still be refused (the member is
    # unchanged, so its validation is unchanged).
    $badSeconds = Invoke-Tool -Port $GamePort -Tool 'running_game_run_test_scenario' -Arguments ([ordered]@{
        steps = @(@{ type = 'wait'; seconds = 'soon' })
    }) -Directory $CallDir -Leaf ($Label + '_p2_wait_seconds_type_error')

    # The node form, two halves. `waited_seconds` mirrors `timeout` (`:459`) but
    # ONLY on the timeout branch: a node that is found answers with
    # `found`/`node_path` and no echo at all (`:461-465`). Both halves are
    # measured, because a description that said "every wait echoes
    # waited_seconds" would be wrong for the found half.
    $waitNode = Invoke-Tool -Port $GamePort -Tool 'running_game_run_test_scenario' -Arguments ([ordered]@{
        steps = @(@{ type = 'wait'; node_path = 'Main'; timeout = 0.25 })
    }) -Directory $CallDir -Leaf ($Label + '_p2_wait_node_found')

    $waitNodeTimeout = Invoke-Tool -Port $GamePort -Tool 'running_game_run_test_scenario' -Arguments ([ordered]@{
        steps = @(@{ type = 'wait'; node_path = '__MCP068_NO_SUCH_NODE__'; timeout = 0.25 })
    }) -Directory $CallDir -Leaf ($Label + '_p2_wait_node_timeout')
}
Stop-OwnProcess -Process $game -LogPath $GameOutLog
Start-Sleep -Seconds 2
Add-Heartbeat ('game stopped pid=' + $gamePid)

function Get-WaitEntry($Call) {
    $body = Get-ToolBody $Call
    if ($null -eq $body) { return $null }
    foreach ($entry in @($body.results)) {
        if ([string]$entry.type -eq 'wait') { return $entry }
    }
    return $null
}

if ($null -ne $waitSeconds) {
    $entry = Get-WaitEntry $waitSeconds
    $secondsEcho = $null
    $hasWaited = $false
    if ($null -ne $entry) {
        $names = @($entry.PSObject.Properties | ForEach-Object { $_.Name })
        $hasWaited = ($names -contains 'waited_seconds')
        if ($hasWaited) { $secondsEcho = [double]$entry.waited_seconds }
    }
    Add-Check 'p2_wait_seconds_call_is_not_an_error' ((Get-ErrorCode $waitSeconds) -eq 0) ('code=' + (Get-ErrorCode $waitSeconds))
    Add-Check 'p2_wait_seconds_step_completed' ($null -ne $entry) ('wait entry=' + (($entry | ConvertTo-Json -Compress -Depth 5)))
    Add-Check 'p2_result_echoes_waited_seconds' $hasWaited ('echo=' + $secondsEcho)
    Add-Check 'p2_echo_is_the_requested_seconds' (($null -ne $secondsEcho) -and ([math]::Abs($secondsEcho - 1.5) -lt 1e-9)) ('requested=1.5 echo=' + $secondsEcho)
}

if ($null -ne $legacy) {
    $entry = Get-WaitEntry $legacy
    $code = Get-ErrorCode $legacy
    $echo = $null
    if ($null -ne $entry) { $echo = $entry.waited_seconds }
    # Two honest outcomes are possible and both are recorded; the check is that
    # the request is NOT silently treated as a real 0.05 s wait while the
    # contract's own member is absent, because that would make the description's
    # "waited_seconds is not an input" false.
    $honest = (($code -ne 0) -or ($null -ne $entry))
    Add-Check 'p2_legacy_name_request_is_recorded' $true ('code=' + $code + ' message=' + (Get-ErrorMessage $legacy) + ' entry=' + (($entry | ConvertTo-Json -Compress -Depth 5)))
    Add-Check 'p2_legacy_name_never_produces_a_silent_short_wait' ($honest -and (($code -ne 0) -or ($null -eq $entry) -or ($null -eq $echo))) ('code=' + $code + ' echo=' + $echo)
    $null = Write-McpSummary -RunDir $RunDir -Leaf 'p2_legacy_name_outcome' -Object ([pscustomobject]@{
        request_arguments = $legacy.ArgumentsJson
        error_code = $code
        error_message = (Get-ErrorMessage $legacy)
        wait_entry = $entry
    })
}

if ($null -ne $badSeconds) {
    Add-Check 'p2_bad_seconds_is_still_refused' ((Get-ErrorCode $badSeconds) -eq -32602) ('code=' + (Get-ErrorCode $badSeconds) + ' message=' + (Get-ErrorMessage $badSeconds))
}

if ($null -ne $waitNode) {
    $entry = Get-WaitEntry $waitNode
    $hasEcho = ($null -ne $entry) -and (@($entry.PSObject.Properties | ForEach-Object { $_.Name }) -contains 'waited_seconds')
    $found = $false
    if ($null -ne $entry) { $found = [bool]$entry.found }
    Add-Check 'p2_wait_node_call_is_not_an_error' ((Get-ErrorCode $waitNode) -eq 0) ('code=' + (Get-ErrorCode $waitNode))
    Add-Check 'p2_found_node_wait_answers_found_without_echo' ($found -and (-not $hasEcho)) ('entry=' + (($entry | ConvertTo-Json -Compress -Depth 5)))
    $null = Write-McpSummary -RunDir $RunDir -Leaf 'p2_wait_node_found_entry' -Object ([pscustomobject]@{ entry = $entry })
}

if ($null -ne $waitNodeTimeout) {
    $entry = Get-WaitEntry $waitNodeTimeout
    $nodeEcho = $null
    $found = $false
    if ($null -ne $entry) {
        if (@($entry.PSObject.Properties | ForEach-Object { $_.Name }) -contains 'waited_seconds') {
            $nodeEcho = [double]$entry.waited_seconds
        }
        $found = [bool]$entry.found
    }
    Add-Check 'p2_wait_node_timeout_call_is_not_an_error' ((Get-ErrorCode $waitNodeTimeout) -eq 0) ('code=' + (Get-ErrorCode $waitNodeTimeout))
    Add-Check 'p2_timeout_branch_echo_mirrors_timeout' ((-not $found) -and ($null -ne $nodeEcho) -and ([math]::Abs($nodeEcho - 0.25) -lt 1e-9)) `
        ('requested timeout=0.25 found=' + $found + ' echo=' + $nodeEcho + ' entry=' + (($entry | ConvertTo-Json -Compress -Depth 5)))
    $null = Write-McpSummary -RunDir $RunDir -Leaf 'p2_wait_node_timeout_entry' -Object ([pscustomobject]@{ entry = $entry })
}

Assert-Port9877Untouched 'p9_port_9877_free_after'

# ---------------------------------------------------------------------------
#  Summary
# ---------------------------------------------------------------------------
$checks = @($script:Checks)
$failed = @($checks | Where-Object { -not $_.pass })
$summary = [ordered]@{
    task           = 'TASK-068'
    label          = $Label
    editor_exe     = $EditorExe
    game_exe       = $GameExe
    editor_version = $editorVersion
    game_version   = $gameVersion
    finished       = (Get-Date).ToString('o')
    checks_total   = $checks.Count
    checks_passed  = @($checks | Where-Object { $_.pass }).Count
    checks_failed  = $failed.Count
    checks         = $checks
}
$summaryPath = Write-McpSummary -RunDir $RunDir -Leaf ($Label + '_run_summary') -Object $summary

Write-Host ('    summary   : {0}' -f $summaryPath)
Write-Host ('checks={0} failures={1}' -f $checks.Count, $failed.Count)
foreach ($f in $failed) { Write-Host ('  FAIL {0} :: {1}' -f $f.id, $f.detail) }
if ($failed.Count -gt 0) {
    Write-Host 'TASK-068 LIVE FAILED'
    exit 1
}
Write-Host 'TASK-068 LIVE PASS'
exit 0
