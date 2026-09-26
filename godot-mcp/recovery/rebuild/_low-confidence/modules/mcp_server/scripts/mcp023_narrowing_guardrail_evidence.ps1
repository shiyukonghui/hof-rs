        '[godot_mcp]',
        'enabled_in_game=true',
        '',
        '[rendering]',
        'renderer/rendering_method="gl_compatibility"',
        'renderer/rendering_method.mobile="gl_compatibility"'
    )
    Write-Utf8NoBom -Path (Join-Path $Path 'project.godot') -Text (($project -join "`n") + "`n")
    Write-Utf8NoBom -Path (Join-Path $Path 'scenes\main.tscn') -Text $MainScene
    Write-Utf8NoBom -Path (Join-Path $Path 'xscenes\good.tscn') -Text $XScene
    Write-Utf8NoBom -Path (Join-Path $Path 'main.gd') -Text $Script
}

$Script:MainScenePath = $null
$Script:XScenePath = $null

# Put the edited scene back into the known state **and** make that state the disk
# state, so every case starts from the same bytes.
function Reset-Baseline {
    param([string]$Tag)
    $null = Invoke-Tool -Id ($Tag + '_b0_pos') -Tool 'editor_set_node_property' -Arguments @{ path = 'Actor'; property = 'position'; value = @{ x = 3; y = 4 } }
    $null = Invoke-Tool -Id ($Tag + '_b1_rot') -Tool 'editor_set_node_property' -Arguments @{ path = 'Actor'; property = 'rotation'; value = 0.5 }
    $null = Invoke-Tool -Id ($Tag + '_b2_save') -Tool 'editor_save_scene' -Arguments @{}
    $null = Invoke-Tool -Id ($Tag + '_b3_save') -Tool 'editor_save_scene' -Arguments @{}
    return (Get-FileSha $Script:MainScenePath)
}

# ---------------------------------------------------------------------------
# The D-4 counterexample matrix for `editor_set_node_property` (path 1).
#
# `values` are the two controls and the six counterexamples the M4b audit
# measured. Every counterexample gets all four evidence forms; the controls prove
# the gate is a refusal of the unfittable and not of large numbers as such.
# ---------------------------------------------------------------------------
$CounterExamples = @(
function Test-Path1Scalar {
    $results = @()
    foreach ($case in $CounterExamples) {
        $tag = 'P1_' + $case.name
        $before = Reset-Baseline -Tag $tag
        $env = Invoke-Tool -Id $tag -Tool 'editor_set_node_property' -Arguments @{ path = 'Actor'; property = 'rotation'; value = $case.value }
        $code = Get-ErrorCode $env
        $payload = Get-Payload $env
        $respFile = Join-Path $Evid ($tag + '.response.json')
        $respText = Get-FileText $respFile
        $saveEnv = Invoke-Tool -Id ($tag + '_save') -Tool 'editor_save_scene' -Arguments @{}
        $after = Get-FileSha $Script:MainScenePath
        $propsRead = Get-EditorNodeProperty -Id ($tag + '_read_props') -Path 'Actor' -Property 'rotation'
        $gdRead = Get-EditorGdscript -Id ($tag + '_read_gd') -Code $EditorReadActorRotation

        $formEcho = Test-NoValueEcho $env
        $formFile = Test-FileHasNoNonFinite -Path $Script:MainScenePath
        $formRead = (Test-FiniteValue $propsRead) -and ($gdRead -eq '0.5')
        if ($case.refused) {
            $formCode = ($code -eq -32602)
            $newValue = ''
            if ($null -ne $payload) { $newValue = ConvertTo-CompactJson $payload.new_value }
            Add-Check ($tag + '_code') $formCode ("code=" + $code + " new_value_echo=" + $newValue + " message=" + (Get-ErrorMessage $env))
            Add-Check ($tag + '_no_value_echo') $formEcho ("no result payload / no value echo in error.data; message names the engine's value: " + (Get-EngineWouldWriteSpelling -Text $respText))
            Add-Check ($tag + '_file_clean') $formFile ("scenes/main.tscn sha256 " + $before + " -> " + $after + "; no inf/nan in bytes")
            Add-Check ($tag + '_read_old') $formRead ("editor_get_node_properties rotation=" + (ConvertTo-CompactJson $propsRead) + " ; editor_execute_gdscript str(rotation)=" + $gdRead)
        } else {
            $formCode = ($code -eq 0) -and (Test-FiniteValue $payload.new_value)
            Add-Check ($tag + '_code') $formCode ("code=" + $code + " new_value=" + (ConvertTo-CompactJson $payload.new_value) + " (finite control)")
            Add-Check ($tag + '_echo_finite') (($null -ne $env.result) -and (Test-FiniteValue $payload.new_value) -and (-not $respText.Contains('1e99999'))) ("success payload with a finite new_value=" + (ConvertTo-CompactJson $payload.new_value))
            Add-Check ($tag + '_file_clean') $formFile ("scene file clean after save; sha256 " + $after)
            $formRead = ($gdRead -ne '0.5') -and ($gdRead -ne 'inf') -and ($gdRead -ne 'nan')
            Add-Check ($tag + '_read_new') $formRead ("the written value is finite and readable: gd=" + $gdRead + " props=" + (ConvertTo-CompactJson $propsRead))
        }
        $results += [pscustomobject]@{ case = $case.name; code = $code; before = $before; after = $after; props = (ConvertTo-CompactJson $propsRead); gd = $gdRead }
    }
    return $results
}

function Test-Path2Batch {
    $results = @()
            [pscustomobject]@{ name = '1e300'; value = 1.0e300 },
            [pscustomobject]@{ name = '3.5e38'; value = 3.5e38 },
            [pscustomobject]@{ name = 'neg_3.5e38'; value = -3.5e38 },
            [pscustomobject]@{ name = 'string_1e300'; value = '1e300' },
    Add-Check 'D6_bridge_file_written' (Test-Path $bridgeAbs) ("user://mcp_test_report.json exists=" + (Test-Path $bridgeAbs) + " sha256=" + (Get-FileSha $bridgeAbs) + " bytes=" + (Get-Item $bridgeAbs -ErrorAction SilentlyContinue).Length)

    # (2) The editor endpoint reads it (the cross-endpoint call is the whole
    # point: `running_game_*` is not registered on 9888).
    $report = Invoke-Tool -Id 'D6_editor_read' -Tool 'editor_get_test_report' -Arguments @{ clear = $false }
    $reportPayload = Get-Payload $report
    $reportText = ConvertTo-CompactJson $reportPayload
    Add-Check 'D6_editor_sees_game_report' (([int]$reportPayload.total -ge 2) -and ([int]$reportPayload.failed -ge 1) -and ((@($reportPayload.details)).Count -ge 2) -and ($reportPayload.source -eq 'game_process_file')) ("total=" + $reportPayload.total + " passed=" + $reportPayload.passed + " failed=" + $reportPayload.failed + " source=" + $reportPayload.source + " report_path=" + $reportPayload.report_path + " written_at_unix=" + $reportPayload.report_written_at_unix)

    # (3) `clear` (the default) empties the bridge as well, so the next call is
    # honestly empty instead of replaying a stale report.
    $cleared = Invoke-Tool -Id 'D6_editor_clear' -Tool 'editor_get_test_report' -Arguments @{}
    $clearedPayload = Get-Payload $cleared
    $empty = Invoke-Tool -Id 'D6_editor_empty' -Tool 'editor_get_test_report' -Arguments @{}
    $emptyPayload = Get-Payload $empty
    Add-Check 'D6_clear_is_cross_process' (([int]$clearedPayload.total -ge 2) -and (Test-Path $bridgeAbs) -eq $false -and ([int]$emptyPayload.total -eq 0) -and ($emptyPayload.no_results -eq $true) -and ($emptyPayload.report_file_present -eq $false)) ("first total=" + $clearedPayload.total + " cleared=" + (ConvertTo-CompactJson $clearedPayload.cleared) + " file left=" + (Test-Path $bridgeAbs) + " second total=" + $emptyPayload.total + " no_results=" + $emptyPayload.no_results + " report_file_present=" + $emptyPayload.report_file_present)

    return $reportText
}


$EditorReadEnvironment = @'
var tree = Engine.get_main_loop()
var root = tree.get_edited_scene_root()
var env = null
for child in root.get_children():
	if child is WorldEnvironment:
		env = child.environment
var bg = str(env.background_color) if env != null else "<no-env>"
return "background_color=" + bg
'@

# A structured "is this tool registered" probe: parse `tools/list` and look at
# the `name` fields (PLAYBOOK section 7.4 - never a text match, because one
# description may name another tool).
function Get-ToolNames {
    param([int]$Port = $EditorPort)
    $text = Invoke-Curl -Id ("toolslist_$Port") -Json (ConvertTo-Json -InputObject @{ jsonrpc = '2.0'; id = 2; method = 'tools/list'; params = @{} } -Depth 8 -Compress) -Port $Port
    if ([string]::IsNullOrWhiteSpace($text)) { return @() }
    try { $envelope = ConvertFrom-Json $text } catch { return @() }
    return @($envelope.result.tools | ForEach-Object { [string]$_.name })
}

function Test-Preconditions {
    $names = @(Get-ToolNames -Port $EditorPort)
    Add-Check 'T0_tools_list_parsed' ($names.Count -gt 0) ("editor tools/list parsed: " + $names.Count + " tool(s)")
    foreach ($tool in @('editor_set_viewport_3d_camera', 'editor_setup_world_environment', 'editor_simulate_mouse_click', 'editor_simulate_mouse_move', 'editor_simulate_input_action', 'editor_simulate_input_sequence')) {
        Add-Check ('T0_registered_' + $tool) ($names -contains $tool) ("parsed name set contains " + $tool)
    }
    # The `3D` viewport singleton is what the camera tool needs; prove it exists
    )
    foreach ($case in $cases) {
        # --- the refusal, with all four evidence forms -----------------------
        $tag = 'C_' + $case.key
        $beforeGd = Get-EditorGdscript -Id ($tag + '_before') -Code $EditorReadCameraPosition
        $saveBefore = Invoke-Tool -Id ($tag + '_save_before') -Tool 'editor_save_scene' -Arguments @{}
        $before = Get-FileSha $Script:MainScenePath
        $component = @{ x = 0.0; y = 0.0; z = 0.0 }
        $component[$case.key -eq 'position' ? 'x' : 'x'] = $case.bad
        $env = Invoke-Tool -Id $tag -Tool 'editor_set_viewport_3d_camera' -Arguments @{ $case.key = $component }
        $code = Get-ErrorCode $env
        $payload = Get-Payload $env
        $respText = Get-FileText (Join-Path $Evid ($tag + '.response.json'))
        $saveAfter = Invoke-Tool -Id ($tag + '_save_after') -Tool 'editor_save_scene' -Arguments @{}
        $after = Get-FileSha $Script:MainScenePath
        $afterGd = Get-EditorGdscript -Id ($tag + '_after') -Code $EditorReadCameraPosition
        Add-Check ($tag + '_code') ($code -eq -32602) ("code=" + $code + " message=" + (Get-ErrorMessage $env))
        Add-Check ($tag + '_no_value_echo') (Test-NoValueEcho $env) ("no result payload / no value echo; message names: " + (Get-EngineWouldWriteSpelling -Text $respText))
# D-7 (b): `editor_setup_world_environment` - bg_color / ambient_color
# ---------------------------------------------------------------------------
function Test-D7WorldEnvironment {
    $results = @()
        $tag = 'W_' + $which
        # `editor_save_scene` is not byte-idempotent while the editor keeps
        # normalizing a freshly created `WorldEnvironment` (measured: the sha of
        # the *file* changes on the next save with no write in between), so the
        # sha comparison below is taken between two **settled** states. The
        # substantive forms - no `inf`/`nan`/`Color(inf` in the bytes, and an
        # independent GDScript read - do not depend on this settling.
        $beforeSha = Get-StabilizedSceneSha -Tag ($tag + '_pre')
        $env = Invoke-Tool -Id $tag -Tool 'editor_setup_world_environment' -Arguments @{ $which = @{ r = 1.0e300; g = 0.0; b = 0.0 } }
        $code = Get-ErrorCode $env
    return $results
}

# ---------------------------------------------------------------------------
# D-7 (c): the editor input-injection tools
# ---------------------------------------------------------------------------
function Test-D7EditorInput {
    $results = @()
    # `editor_simulate_input_action` needs an action; `editor_add_input_action`
    # is the gated writer that makes one.
    $addAction = Invoke-Tool -Id 'I_action_add' -Tool 'editor_add_input_action' -Arguments @{ action = 'mcp_evidence_action'; events = @(@{ type = 'key'; keycode = 'F9' }) }
    Add-Check 'I_action_added' ((Get-ErrorCode $addAction) -eq 0) ("editor_add_input_action code=" + (Get-ErrorCode $addAction) + " message=" + (Get-ErrorMessage $addAction))

    $mouseCases = @(
        [pscustomobject]@{ tool = 'editor_simulate_mouse_click'; args = @{ x = 1.0e300; y = 0.0 }; tag = 'I_click_x' },
        [pscustomobject]@{ tool = 'editor_simulate_mouse_move'; args = @{ x = 0.0; y = -1.0e300 }; tag = 'I_move_y' },
        [pscustomobject]@{ tool = 'editor_simulate_mouse_move'; args = @{ x = 1.0e-300; y = 0.0 }; tag = 'I_move_underflow' }
    )
    foreach ($case in $mouseCases) {
        $env = Invoke-Tool -Id $case.tag -Tool $case.tool -Arguments $case.args
        $code = Get-ErrorCode $env
        $respText = Get-FileText (Join-Path $Evid ($case.tag + '.response.json'))
        Add-Check ($case.tag + '_code') ($code -eq -32602) ("code=" + $code + " message=" + (Get-ErrorMessage $env))
        Add-Check ($case.tag + '_no_value_echo') (Test-NoValueEcho $env) ("no result payload / no finite position echo; message names: " + (Get-EngineWouldWriteSpelling -Text $respText))
        $results += [pscustomobject]@{ case = $case.tag; code = $code }
    }
    # The legal coordinates still inject, and the answer echoes what the event
    # really carries.
    $ok = Invoke-Tool -Id 'I_click_ok' -Tool 'editor_simulate_mouse_click' -Arguments @{ x = 10.0; y = 20.0 }
    $okPayload = Get-Payload $ok
    $gate6 = Test-Gate6NarrowingPoints

    Write-Host '=== port discipline (after) ==='
    $pid9877b = Get-ListenerPid -Port $UserPort
    Add-Check 'P0_user_port_untouched_after' ($pid9877b -eq $pid9877) ("9877 owner before=" + $pid9877 + " after=" + $pid9877b)

    $summary = [pscustomobject]@{
        version    = $version
        head       = $head
        checks     = $script:Checks
        failed     = @($script:Results | Where-Object { -not $_.pass }).Count
        path1      = $path1
        path2      = $path2
        path3      = $path3
        path4      = $path4
        path5      = $path5
        d5         = $d5
        d6         = $d6
        regression = $reg
        d7_camera  = $d7camera
        d7_env     = $d7env
        d7_input   = $d7input
        d7_game    = $d7game
        gate6      = $gate6
        results    = $script:Results
    }
    [IO.File]::WriteAllText($ResultFile, (ConvertTo-Json -InputObject $summary -Depth 32))
    Write-Host ("results -> {0}" -f $ResultFile)
    Write-Host ("checks={0} failed={1}" -f $script:Checks, @($script:Results | Where-Object { -not $_.pass }).Count)
} finally {
    Stop-Engine -Handle $script:GameHandle
    Stop-Engine -Handle $script:EditorHandle
    Start-Sleep -Milliseconds 1500
    Write-Host '=== port discipline (settled) ==='
    Write-Host ("9888 owner = " + (Get-ListenerPid -Port $EditorPort))
    Write-Host ("9889 owner = " + (Get-ListenerPid -Port $GamePort))
    Write-Host ("9877 owner = " + (Get-ListenerPid -Port $UserPort))
}

# TASK-069 section 2.3 (census): this evidence script wrote its `failed` count
# into the summary JSON and printed it, then fell off the end of the file - which
# PowerShell reports as exit 0, so a red check was unreadable to any caller.
# `$script:Results` is the shared check list filled by Add-Check.
$failed = @($script:Results | Where-Object { -not $_.pass })
if ($failed.Count -gt 0) {
    Write-Host ''
    Write-Host ("EVIDENCE FAILED: {0} check(s)" -f $failed.Count)
    foreach ($entry in $failed) { Write-Host ('    ' + $entry.id + ': ' + $entry.evidence) }
    exit 1
}
exit 0