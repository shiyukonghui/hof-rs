# =============================================================================
#  mcp018_b3_closure_evidence.ps1 -- TASK-018 gate 2 evidence
#
#  One run covers the four parts of the task book:
#
#    section 1  the **silent wrong value** is gone. The defect is reproduced as
#               it was measured (`{"position": 1e20}` answered `status: ok` and
#               wrote `Vector2(0,0)`), then the fixed behaviour is proven with a
#               read-back on both the live scene and the file on disk, on every
#               write path that shares the coercion (`editor_set_node_property`,
#               `editor_set_node_property_batch`, `editor_add_nodes_batch`,
#               `running_game_set_node_property`, `project_set_setting`), plus a
#               regression row for `Vector2` / `Vector3` / `float` / `int` /
#               `Color` / `String`.
#
#    section 2  the `accept_m1.ps1` `$ToolNames` derivation. The old literal is
#               taken from `git show HEAD:...` (never from a copy pasted into
#               this script), the manifests are taken from `git show HEAD:...`
#               too, the union is re-derived here with the same rule, and the
#               two sets are compared name by name. Then the same rule is
#               applied to the working-tree manifests and the result is compared
#               with the base literal in its **relative** form: nothing lost,
#               all ten B3 tools present, at least ten tools larger.
#
#               TASK-032: the original second half of that comparison asserted
#               the working-tree union equals the base literal *plus exactly ten*
#               (`derivation_new_union_is_old_plus_exactly_ten`, old=96
#               new=113 at the time of the report). That is a fact about
#               TASK-018's batch, not an invariant - every later batch that
#               implements more tools breaks it, and TASK-030 reported it as
#               still red. It is marked **superseded** and replaced by
#               `derivation_new_union_is_base_plus_b3_and_later_batches`; the
#               section's real invariants (base union == base literal, and the
#               B1/B2 path-output sha rows) are unchanged.
#
#    section 3  the ten tools of the six closing B3 groups: success, missing
#               argument and bottom-layer failure for each, plus one cross-tool
#               chain per group family and the two multi-scene transaction
#               counter-examples (broken middle file, value that cannot fit).
#
#    section 4  the **B3 = 40/40** machine check: the manifest's own 40 tools,
#               the group-implemented count, the live `tools/list` on 9888 and
#               9889, and `docs/scripts/check_tool_groups.py --batch B3` /
#               `--check-completeness` exit codes.
#
#  Discipline (PLAYBOOK sections 3 and 7.1):
#    * every response body is written with `curl.exe -s -o <file>` and its
#      sha256 is printed from the bytes on disk (nothing through a pipe);
#    * every request body is built with `ConvertTo-Json` and sent with
#      `curl.exe --data-binary @file`;
#    * ports 9888 (editor) / 9889 (game) only; the user's 9877 is never touched
#      and its listener pid is asserted unchanged at the end;
#    * scratch `.tscn` / `.tres` are written **without a BOM** and every
#      `--import` exit code is checked;
#    * this file is deliberately pure ASCII, so no PowerShell 5.1 code-page
#      guess can change what it asserts.
#
#  Usage:
#    powershell -NoProfile -ExecutionPolicy Bypass -File mcp018_b3_closure_evidence.ps1
# =============================================================================

$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$ModuleRoot = Join-Path $RepoRoot 'modules\mcp_server'
$Engine = Join-Path $RepoRoot 'bin\godot.windows.editor.x86_64.console.exe'
$Curl = Join-Path $env:SystemRoot 'System32\curl.exe'
$EditorPort = 9888
$GamePort = 9889
$UserPort = 9877
# The commit this task started from: the "previous version" of the acceptance
# script and of the group manifests, read through `git show` rather than from a
# copy pasted into this file. Override with MCP018_BASE_REF when re-running the
# proof against another base.
$BaseRef = if ($env:MCP018_BASE_REF) { $env:MCP018_BASE_REF } else { 'ddb585d888' }
$Scratch = Join-Path $env:TEMP 'mcp018-scratch'
$LogRoot = Join-Path $env:TEMP 'mcp018-logs'
$Evid = Join-Path $env:TEMP 'mcp018-evidence'

$script:Results = New-Object System.Collections.Generic.List[object]
$script:EditorHandle = $null
$script:GameHandle = $null

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
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        for ($attempt = 1; $attempt -le 3; $attempt++) {
            Remove-Item -Path $out, $err -ErrorAction SilentlyContinue
            & $Engine --headless --mcp-port=0 --path $Path --import 1> $out 2> $err
            $code = $LASTEXITCODE
            Write-Host ("import {0}: attempt={1} exit={2} log={3}" -f $Path, $attempt, $code, $out)
            if ($code -eq 0) { return $attempt }
            Write-Host ("attempt {0} failed with {1}" -f $attempt, $code)
            Start-Sleep -Milliseconds 1500
        }
    } finally {
        $ErrorActionPreference = $previous
    }
    throw ("--import of {0} failed three times" -f $Path)
}

function ConvertTo-CompactJson {
    param($Value)
    return (ConvertTo-Json -InputObject $Value -Depth 12 -Compress)
}

function Format-CallBody {
    param([string]$Tool, $Arguments, [int]$Id = 1)
    $envelope = @{
        jsonrpc = '2.0'
        id      = $Id
        method  = 'tools/call'
        params  = @{ name = $Tool; arguments = $Arguments }
    }
    return (ConvertTo-CompactJson $envelope)
}

function Invoke-Curl {
    param([string]$Id, [string]$Json, [int]$Port, [int]$MaxTimeSec = 60)
    $bodyFile = Join-Path $Evid ("{0}.request.json" -f $Id)
    $respFile = Join-Path $Evid ("{0}.response.json" -f $Id)
    Write-Utf8NoBom -Path $bodyFile -Text $Json
    if (Test-Path $respFile) { Remove-Item -Force $respFile }
    & $Curl -s --max-time $MaxTimeSec -o $respFile -H 'Content-Type: application/json' `
        --data-binary ('@' + $bodyFile) ("http://127.0.0.1:{0}/mcp" -f $Port) | Out-Null
    $curlExit = $LASTEXITCODE
    if (-not (Test-Path $respFile)) {
        Write-Host ("[{0}] curl port={1} exit={2} :: NO RESPONSE FILE" -f $Id, $Port, $curlExit)
        return ''
    }
    $bytes = [IO.File]::ReadAllBytes($respFile)
    $sha = (Get-FileHash -Algorithm SHA256 -Path $respFile).Hash.ToLower()
    $text = [Text.Encoding]::UTF8.GetString($bytes)
    Write-Host ("[{0}] curl port={1} exit={2} bytes={3} sha256={4}" -f $Id, $Port, $curlExit, $bytes.Length, $sha)
    Write-Host ("       request : {0}" -f $Json)
    Write-Host ("       response: {0}" -f $text)
    return $text
}

function Invoke-Tool {
    param([string]$Id, [string]$Tool, $Arguments, [int]$Port = $EditorPort, [int]$MaxTimeSec = 60)
    $text = Invoke-Curl -Id $Id -Json (Format-CallBody -Tool $Tool -Arguments $Arguments -Id 1) -Port $Port -MaxTimeSec $MaxTimeSec
    if ([string]::IsNullOrWhiteSpace($text)) { return $null }
    try { return ConvertFrom-Json $text } catch { return $null }
}

function Get-Payload {
    param($Envelope)
    if ($null -eq $Envelope -or $null -eq $Envelope.result) { return $null }
    $content = @($Envelope.result.content)
    if ($content.Count -lt 1) { return $null }
    try { return ConvertFrom-Json ([string]$content[0].text) } catch { return $null }
}

function Get-ErrorCode {
    param($Envelope)
    if ($null -eq $Envelope -or $null -eq $Envelope.error) { return 0 }
    return [int]$Envelope.error.code
}

function Get-ErrorMessage {
    param($Envelope)
    if ($null -eq $Envelope -or $null -eq $Envelope.error) { return '' }
    return [string]$Envelope.error.message
}

function Get-StatusProbe {
    param([int]$Port)
    $file = Join-Path $Evid ("status_{0}.response.json" -f $Port)
    if (Test-Path $file) { Remove-Item -Force $file }
    & $Curl -s --max-time 5 -o $file ("http://127.0.0.1:{0}/mcp" -f $Port) | Out-Null
    if (-not (Test-Path $file)) { return $null }
    $bytes = [IO.File]::ReadAllBytes($file)
    if ($bytes.Length -eq 0) { return $null }
    $text = [Text.Encoding]::UTF8.GetString($bytes)
    try { return ConvertFrom-Json $text } catch { return $null }
}

function Wait-ForPump {
    param([int]$Port, [int]$TimeoutMs = 300000)
    $deadline = [DateTime]::UtcNow.AddMilliseconds($TimeoutMs)
    $consecutive = 0
    $previous = $null
    while ([DateTime]::UtcNow -lt $deadline) {
        $probe = Get-StatusProbe -Port $Port
        if ($null -ne $probe) {
            $frames = [int]$probe.frame_count
            if ($null -ne $previous -and ($frames - $previous) -ge 20) { $consecutive++ } else { $consecutive = 0 }
            if ($consecutive -ge 3) { return $true }
            $previous = $frames
        }
        Start-Sleep -Milliseconds 1000
    }
    return $false
}

# The `type`/`value` of a node property as `editor_get_node_properties` reports
# it, or $null when the property is absent from the answer.
function Get-NodeProperty {
    param([string]$Id, [string]$Path, [string]$Property)
    $envelope = Invoke-Tool -Id $Id -Tool 'editor_get_node_properties' -Arguments @{ path = $Path; properties = @($Property) }
    $payload = Get-Payload $envelope
    if ($null -eq $payload -or $null -eq $payload.properties) { return $null }
    return $payload.properties.$Property
}

# =============================================================================
# Scratch projects
# =============================================================================

$EditorScene = @"
[gd_scene format=3]

[node name="Main" type="Node2D"]

[node name="A" type="Node2D" parent="."]

[node name="B" type="Node2D" parent="."]

[node name="World" type="Node3D" parent="."]

[node name="Ui" type="Control" parent="."]

[node name="Plain" type="Node" parent="."]
"@

$GameScene = @"
[gd_scene format=3]

[node name="Main" type="Node2D"]

[node name="A" type="Node2D" parent="."]
"@

$CrossOne = @"
[gd_scene format=3]

[node name="One" type="Node2D"]

[node name="Child" type="Sprite2D" parent="."]
"@

$CrossTwo = @"
[gd_scene format=3]

[node name="Two" type="Node2D"]
"@

$BrokenScene = @"
[gd_scene format=3]

[node name="Broken" type="Node2D"
"@

function New-Project {
    param([string]$Path, [string]$Name, [string]$SceneText, [bool]$WithMainScene)
    Remove-Item -Recurse -Force $Path -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path (Join-Path $Path 'scenes') | Out-Null
    $lines = @(
        'config_version=5',
        '',
        '[application]',
        ('config/name="' + $Name + '"'),
        'config/features=PackedStringArray("4.8")'
    )
    if ($WithMainScene) { $lines += 'run/main_scene="res://scenes/main.tscn"' }
    $lines += @(
        '',
        '[rendering]',
        'renderer/rendering_method="gl_compatibility"',
        'renderer/rendering_method.mobile="gl_compatibility"'
    )
    Write-Utf8NoBom -Path (Join-Path $Path 'project.godot') -Text (($lines -join "`n") + "`n")
    Write-Utf8NoBom -Path (Join-Path $Path 'scenes\main.tscn') -Text ($SceneText + "`n")
}

# =============================================================================
# Main
# =============================================================================

Write-Host '============================================================='
Write-Host ' TASK-018 gate 2 evidence -- B3 closure, silent-value fix, derivation'
Write-Host '============================================================='

if (-not (Test-Path $Engine)) { Write-Host "FATAL: engine binary not found: $Engine"; exit 2 }
New-Item -ItemType Directory -Force -Path $Scratch, $LogRoot, $Evid | Out-Null

$EditorProject = Join-Path $Scratch 'editor'
$GameProject = Join-Path $Scratch 'game'
$userPortPidBefore = Get-ListenerPid -Port $UserPort
Write-Host ("user editor on {0} before run: pid={1}" -f $UserPort, $userPortPidBefore)

$versionText = (& $Engine --version)
$headSha = (& git -C $RepoRoot rev-parse --short HEAD).Trim()
Write-Host ("engine --version: {0}; git HEAD: {1}" -f $versionText, $headSha)
Add-Check 'gate_version_matches_head' ($versionText.contains($headSha.Substring(0, 9))) ("engine='{0}' head='{1}'" -f $versionText, $headSha)

$EditorTools = @('editor_execute_gdscript', 'editor_set_node_script')
$ProjectTools = @(
    'project_create_script', 'project_edit_script',
    'project_add_autoload', 'project_remove_autoload',
    'project_set_setting',
    'project_set_node_property_across_scenes',
    'project_convert_path_to_uid', 'project_convert_uid_to_path'
)
$AllTen = $EditorTools + $ProjectTools

try {
    # ------------------------------------------------------------------
    # Scratch projects (plus the material the ten tools act on)
    # ------------------------------------------------------------------
    New-Project -Path $EditorProject -Name 'MCP018 closure editor' -SceneText $EditorScene -WithMainScene $false
    New-Project -Path $GameProject -Name 'MCP018 closure game' -SceneText $GameScene -WithMainScene $true
    Write-Utf8NoBom -Path (Join-Path $EditorProject 'scripts\one.gd') -Text "extends Node`n`nfunc marker() -> String:`n`treturn \"one\"`n"
    Write-Utf8NoBom -Path (Join-Path $EditorProject 'scripts\two.gd') -Text "extends Node`n"
    Write-Utf8NoBom -Path (Join-Path $EditorProject 'cross\one.tscn') -Text ($CrossOne + "`n")
    Write-Utf8NoBom -Path (Join-Path $EditorProject 'cross\two.tscn') -Text ($CrossTwo + "`n")
    New-Item -ItemType Directory -Force -Path (Join-Path $EditorProject 'addons\mcp018') | Out-Null
    Write-Utf8NoBom -Path (Join-Path $EditorProject 'addons\mcp018\in_addon.tscn') -Text ("[gd_scene format=3]`n`n[node name=`"InAddon`" type=`"Node2D`"]`n")

    Write-Host 'importing scratch projects ...'
    $a1 = Import-Project -Path $EditorProject -LogName 'import-editor'
    $a2 = Import-Project -Path $GameProject -LogName 'import-game'
    Add-Check 'import_exit_codes' $true ("both scratch projects imported with exit code 0 (attempts: {0} / {1})" -f $a1, $a2)

    $script:EditorHandle = Start-Engine -Arguments @('--headless', '-e', '--path', $EditorProject, "--mcp-port=$EditorPort") -LogName 'editor'
    if (-not (Wait-ForPump -Port $EditorPort -TimeoutMs 300000)) { throw 'editor endpoint never became ready' }
    $script:GameHandle = Start-Engine -Arguments @('--headless', '--path', $GameProject, "--mcp-port=$GamePort") -LogName 'game'
    if (-not (Wait-ForPump -Port $GamePort -TimeoutMs 240000)) { throw 'game endpoint never became ready' }

    # ------------------------------------------------------------------
    # 0. scope: served by 9888, filtered by scope on 9889, -32601 on a leak
    # ------------------------------------------------------------------
    $editorListText = Invoke-Curl -Id 'scope_editor_tools_list' -Json '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' -Port $EditorPort
    $gameListText = Invoke-Curl -Id 'scope_game_tools_list' -Json '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' -Port $GamePort
    $missingOnEditor = @($AllTen | Where-Object { $editorListText -notmatch ('"' + $_ + '"') })
    $editorLeakedOnGame = @($EditorTools | Where-Object { $gameListText -match ('"' + $_ + '"') })
    $projectMissingOnGame = @($ProjectTools | Where-Object { $gameListText -notmatch ('"' + $_ + '"') })
    Add-Check 'scope_editor_serves_all_ten' ($missingOnEditor.Count -eq 0) ("missing from 9888: [" + ($missingOnEditor -join ', ') + "] sha256=" + (Get-FileSha (Join-Path $Evid 'scope_editor_tools_list.response.json')))
    Add-Check 'scope_game_hides_the_two_editor_tools' ($editorLeakedOnGame.Count -eq 0) ("editor-scope tools on 9889: [" + ($editorLeakedOnGame -join ', ') + "]")
    Add-Check 'scope_game_serves_the_eight_project_tools' ($projectMissingOnGame.Count -eq 0) ("missing from 9889: [" + ($projectMissingOnGame -join ', ') + "] sha256=" + (Get-FileSha (Join-Path $Evid 'scope_game_tools_list.response.json')))
    $leakCall = Invoke-Tool -Id 'scope_game_editor_tool_call' -Tool 'editor_execute_gdscript' -Arguments @{ code = 'return 1' } -Port $GamePort
    Add-Check 'scope_game_editor_tool_call_is_32601' ((Get-ErrorCode $leakCall) -eq -32601 -and $null -eq $leakCall.result) ("code=" + (Get-ErrorCode $leakCall) + " result_is_null=" + ($null -eq $leakCall.result) + " message='" + (Get-ErrorMessage $leakCall) + "'")

    # ------------------------------------------------------------------
    # 1. section 4 -- B3 = 40/40 machine check
    # ------------------------------------------------------------------
    $b3 = ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 (Join-Path $ModuleRoot 'docs\tool-groups-b3.json'))
    # `scope` is read from the rename map, never invented: a B3 tool is live on
    # 9889 exactly when its scope is not `editor`.
    $renameMap = ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 (Join-Path $ModuleRoot 'docs\tool-rename-map.json'))
    $scopeByTool = @{}
    foreach ($entry in @($renameMap.tools)) { $scopeByTool[[string]$entry.new_name] = [string]$entry.scope }
    $b3Groups = @($b3.groups)
    $b3All = @($b3Groups | ForEach-Object { $_.tools })
    $b3ImplGroups = @($b3Groups | Where-Object { $_.implemented -eq $true })
    $b3Impl = @($b3ImplGroups | ForEach-Object { $_.tools })
    $b3EditorTools = @($b3Impl | Where-Object { $EditorTools -contains $_ })
    $b3GameExpected = @($b3Impl | Where-Object { $scopeByTool[[string]$_] -ne 'editor' })
    $b3OnEditor = @($b3Impl | Where-Object { $editorListText -match ('"' + $_ + '"') })
    $b3OnGame = @($b3GameExpected | Where-Object { $gameListText -match ('"' + $_ + '"') })
    $b3EditorLeaked = @($b3EditorTools | Where-Object { $gameListText -match ('"' + $_ + '"') })
    Add-Check 'b3_is_complete_40_40' (($b3.total -eq 40) -and ($b3All.Count -eq 40) -and ($b3Groups.Count -eq 12) -and ($b3Impl.Count -eq 40) -and ($b3ImplGroups.Count -eq 12)) ("manifest total={0} tools={1} groups={2} implemented_tools={3} implemented_groups={4}" -f $b3.total, $b3All.Count, $b3Groups.Count, $b3Impl.Count, $b3ImplGroups.Count)
    Add-Check 'b3_live_40_40_on_9888' ($b3OnEditor.Count -eq 40) ("B3 tools live on 9888: {0}/40 (editor endpoint serves editor+both)" -f $b3OnEditor.Count)
    Add-Check 'b3_live_on_9889_matches_scope' (($b3OnGame.Count -eq $b3GameExpected.Count) -and ($b3EditorLeaked.Count -eq 0)) ("B3 tools with scope<>editor: {0}, live on 9889: {1}; B3 editor-scope tools: {2} (none of them live on 9889: [{3}])" -f $b3GameExpected.Count, $b3OnGame.Count, $b3EditorTools.Count, ($b3EditorLeaked -join ', '))
    $python = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { 'python3' }
    $checker = Join-Path $ModuleRoot 'docs\scripts\check_tool_groups.py'
    $b3Out = Join-Path $LogRoot 'check_tool_groups_b3.log'
    $b3CompOut = Join-Path $LogRoot 'check_tool_groups_completeness.log'
    & $python $checker --batch B3 1> $b3Out 2>&1
    $b3Exit = $LASTEXITCODE
    & $python $checker --check-completeness 1> $b3CompOut 2>&1
    $b3CompExit = $LASTEXITCODE
    Add-Check 'b3_check_tool_groups_python' (($b3Exit -eq 0) -and ($b3CompExit -eq 0)) ("--batch B3 exit={0} --check-completeness exit={1}; last line: {2}" -f $b3Exit, $b3CompExit, ((Get-Content $b3Out -Tail 1) -join ' '))

    # ------------------------------------------------------------------
    # 2. section 2 -- accept_m1.ps1 derivation proof
    # ------------------------------------------------------------------
    # The old script and the old manifests come out of `git show HEAD:` through
    # a cmd redirection (raw bytes, no PowerShell decoding of Chinese comments).
    $oldScript = Join-Path $Evid 'accept_m1_head.ps1'
    $oldB1 = Join-Path $Evid 'tool-groups_head.json'
    $oldB2 = Join-Path $Evid 'tool-groups-b2_head.json'
    $oldB3 = Join-Path $Evid 'tool-groups-b3_head.json'
    foreach ($spec in @(
        @{ ref = ($BaseRef + ':modules/mcp_server/scripts/accept_m1.ps1'); file = $oldScript },
        @{ ref = ($BaseRef + ':modules/mcp_server/docs/tool-groups.json'); file = $oldB1 },
        @{ ref = ($BaseRef + ':modules/mcp_server/docs/tool-groups-b2.json'); file = $oldB2 },
        @{ ref = ($BaseRef + ':modules/mcp_server/docs/tool-groups-b3.json'); file = $oldB3 }
    )) {
        cmd /c ("git -C `"{0}`" show {1} > `"{2}`"" -f $RepoRoot, $spec.ref, $spec.file) | Out-Null
    }
    $oldText = Get-Content -Raw -Encoding UTF8 $oldScript
    $literalMatch = [regex]::Match($oldText, '\$ToolNames\s*=\s*@\((?<body>[\s\S]*?)\n\)')
    $oldLiteral = @()
    if ($literalMatch.Success) {
        foreach ($m in [regex]::Matches($literalMatch.Groups['body'].Value, "'([a-z0-9_]+)'")) { $oldLiteral += $m.Groups[1].Value }
    }
    $oldLiteral = @($oldLiteral | Select-Object -Unique)
    $oldUnion = @()
    foreach ($oldManifestFile in @($oldB1, $oldB2, $oldB3)) {
        $json = ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 $oldManifestFile)
        foreach ($group in @($json.groups)) {
            if ($group.implemented -ne $true) { continue }
            foreach ($tool in @($group.tools)) { if ($oldUnion -notcontains $tool) { $oldUnion += [string]$tool } }
        }
    }
    $oldDiff = @(Compare-Object -ReferenceObject ($oldLiteral | Sort-Object -Unique) -DifferenceObject ($oldUnion | Sort-Object -Unique))
    Add-Check 'derivation_base_union_equals_base_literal' (($oldLiteral.Count -gt 0) -and ($oldDiff.Count -eq 0)) ("base {0}: literal={1} tools, base-manifest union={2} tools, name-by-name diff=[]" -f $BaseRef, $oldLiteral.Count, $oldUnion.Count)

    # The same rule against the working-tree manifests, plus the *relative*
    # delta: nothing the base literal carried may have disappeared, and all ten
    # tools this task added must still be there.
    #
    # TASK-032: the criterion used to read
    # `newUnion.Count -eq ($oldLiteral.Count + 10)` and Compare-Object the added
    # set against exactly the ten. That is a statement about TASK-018's batch,
    # not an invariant: every later batch that marks a group `implemented: true`
    # adds tools, so the check necessarily goes red on its own (TASK-030 reported
    # old=96 new=113). It is therefore marked **superseded** and replaced by the
    # form that stays true while the tree still passes every later batch's own
    # gates - the base literal is a subset of the working-tree union, the ten B3
    # tools are all present, and the union is at least ten tools larger. The
    # growth is *reported*, never asserted against a frozen number. The real
    # invariants of this section (the base literal == the base manifests'
    # derivation, and the two `B1/B2` path-output sha rows asserted elsewhere in
    # this file) are untouched.
    $newUnion = @()
    foreach ($manifestName in @('tool-groups.json', 'tool-groups-b2.json', 'tool-groups-b3.json', 'tool-groups-b4.json', 'tool-groups-b5.json')) {
        $json = ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 (Join-Path $ModuleRoot ('docs\' + $manifestName)))
        foreach ($group in @($json.groups)) {
            if ($group.implemented -ne $true) { continue }
            foreach ($tool in @($group.tools)) { if ($newUnion -notcontains $tool) { $newUnion += [string]$tool } }
        }
    }
    $addedByThisTask = @(Compare-Object -ReferenceObject ($oldLiteral | Sort-Object -Unique) -DifferenceObject ($newUnion | Sort-Object -Unique) | Where-Object { $_.SideIndicator -eq '=>' } | ForEach-Object { $_.InputObject })
    $removedByThisTask = @(Compare-Object -ReferenceObject ($oldLiteral | Sort-Object -Unique) -DifferenceObject ($newUnion | Sort-Object -Unique) | Where-Object { $_.SideIndicator -eq '<=' } | ForEach-Object { $_.InputObject })
    $addedSorted = @($addedByThisTask | Sort-Object)
    $expectedAdded = @($AllTen | Sort-Object)
    $missingTen = @($expectedAdded | Where-Object { $addedSorted -notcontains $_ })
    Add-Check 'derivation_new_union_is_base_plus_b3_and_later_batches' (($removedByThisTask.Count -eq 0) -and ($missingTen.Count -eq 0) -and ($newUnion.Count -ge ($oldLiteral.Count + 10))) ("old={0} new={1} removed=[{2}] all_ten_present={3}/10 missing=[{4}] added_count={5} added=[{6}] (superseded criterion, see the comment above)" -f $oldLiteral.Count, $newUnion.Count, ($removedByThisTask -join ', '), ($expectedAdded.Count - $missingTen.Count), ($missingTen -join ', '), $addedSorted.Count, ($addedSorted -join ', '))

    # The new script really has no hand-maintained tool list: it contains no
    # quoted tool name at all (the old one contained one per implemented tool).
    $newScriptPath = Join-Path $ModuleRoot 'scripts\accept_m1.ps1'
    $newScriptText = Get-Content -Raw -Encoding UTF8 $newScriptPath
    $toolNameLiteralsNew = ([regex]::Matches($newScriptText, "'(project|editor|running_game|os)_[a-z0-9_]+'")).Count
    $toolNameLiteralsOld = ([regex]::Matches($oldText, "'(project|editor|running_game|os)_[a-z0-9_]+'")).Count
    Add-Check 'derivation_new_script_has_no_tool_literals' (($toolNameLiteralsNew -eq 0) -and ($toolNameLiteralsOld -eq $oldLiteral.Count)) ("new script quoted tool names={0}; old script quoted tool names={1} (old literal size={2}); new sha256={3}" -f $toolNameLiteralsNew, $toolNameLiteralsOld, $oldLiteral.Count, (Get-FileSha $newScriptPath))

    # ------------------------------------------------------------------
    # 3. section 1 -- the silent wrong value
    # ------------------------------------------------------------------
    $open = Invoke-Tool -Id 'silent_00_open_scene' -Tool 'editor_open_scene' -Arguments @{ path = 'res://scenes/main.tscn' }
    $openOk = $null -ne (Get-Payload $open)
    Add-Check 'silent_prepared_scene_open' $openOk ("editor_open_scene -> " + (ConvertTo-CompactJson (Get-Payload $open)))

    # A known value on A, so "unchanged" is a comparison and not a guess.
    $seed = Invoke-Tool -Id 'silent_01_seed' -Tool 'editor_set_node_property' -Arguments @{ path = 'A'; property = 'position'; value = @{ x = 11; y = 12 } }
    Add-Check 'silent_seed_position' ($null -ne (Get-Payload $seed)) ("A.position seeded -> " + (ConvertTo-CompactJson (Get-Payload $seed)))
    $scenePath = Join-Path $EditorProject 'scenes\main.tscn'
    $save0 = Invoke-Tool -Id 'silent_02_save_seeded' -Tool 'editor_save_scene' -Arguments @{}
    Add-Check 'silent_seed_saved' ($null -ne (Get-Payload $save0)) ("editor_save_scene -> " + (ConvertTo-CompactJson (Get-Payload $save0)))
    $sceneShaBefore = Get-FileSha $scenePath

    # (a) the defect itself, through the single-property write
    $defect = Invoke-Tool -Id 'silent_03_single_1e20' -Tool 'editor_set_node_property' -Arguments @{ path = 'A'; property = 'position'; value = 1.0e20 }
    $defectMessage = Get-ErrorMessage $defect
    $defectOk = ((Get-ErrorCode $defect) -eq -32602) -and ($defectMessage -contains 'can_convert') -and ($defectMessage -contains 'Vector2') -and ($defectMessage -contains 'float')
    Add-Check 'silent_single_write_refused' $defectOk ("code=" + (Get-ErrorCode $defect) + " result_is_null=" + ($null -eq $defect.result) + " message='" + $defectMessage + "' sha256=" + (Get-FileSha (Join-Path $Evid 'silent_03_single_1e20.response.json')))
    $readA = Get-NodeProperty -Id 'silent_04_read_back_a' -Path 'A' -Property 'position'
    Add-Check 'silent_single_read_back_unchanged' (($null -ne $readA) -and ([double]$readA.x -eq 11) -and ([double]$readA.y -eq 12)) ("A.position after the refused write = " + (ConvertTo-CompactJson $readA) + " (was {x:11,y:12})")

    # (b) the same value through the batch write
    $batch = Invoke-Tool -Id 'silent_05_batch_1e20' -Tool 'editor_set_node_property_batch' -Arguments @{ node_type = 'Node2D'; property = 'position'; value = 1.0e20 }
    $batchMessage = Get-ErrorMessage $batch
    $batchOk = ((Get-ErrorCode $batch) -eq -32602) -and ($batchMessage -contains 'before any node was written')
    Add-Check 'silent_batch_write_refused_before_any_write' $batchOk ("code=" + (Get-ErrorCode $batch) + " message='" + $batchMessage + "' sha256=" + (Get-FileSha (Join-Path $Evid 'silent_05_batch_1e20.response.json')))
    $readA2 = Get-NodeProperty -Id 'silent_06_read_back_a2' -Path 'A' -Property 'position'
    $readMain = Get-NodeProperty -Id 'silent_07_read_back_main' -Path '.' -Property 'position'
    Add-Check 'silent_batch_read_back_unchanged' (($null -ne $readA2) -and ([double]$readA2.x -eq 11) -and ([double]$readA2.y -eq 12) -and ($null -ne $readMain) -and ([double]$readMain.x -eq 0) -and ([double]$readMain.y -eq 0)) ("A.position=" + (ConvertTo-CompactJson $readA2) + " Main.position=" + (ConvertTo-CompactJson $readMain))
    $save1 = Invoke-Tool -Id 'silent_08_save_after_refusal' -Tool 'editor_save_scene' -Arguments @{}
    $sceneShaAfter = Get-FileSha $scenePath
    Add-Check 'silent_disk_read_back_unchanged' ($sceneShaBefore -eq $sceneShaAfter) ("scenes/main.tscn sha256 before={0} after={1} (saved again after the refused writes)" -f $sceneShaBefore, $sceneShaAfter)

    # (c) the same value through the batch node-add path
    $addBatch = Invoke-Tool -Id 'silent_09_add_nodes_1e20' -Tool 'editor_add_nodes_batch' -Arguments @{ nodes = @(@{ type = 'Node2D'; name = 'MCP018Bad'; properties = @{ position = 1.0e20 } }) }
    $addBatchMessage = Get-ErrorMessage $addBatch
    Add-Check 'silent_add_nodes_batch_refused' (((Get-ErrorCode $addBatch) -eq -32602) -and ($addBatchMessage -contains 'position')) ("code=" + (Get-ErrorCode $addBatch) + " message='" + $addBatchMessage + "'")
    $nodesAfter = Invoke-Tool -Id 'silent_10_read_nodes_after' -Tool 'editor_find_nodes_by_type' -Arguments @{ type = 'Node2D' }
    $nodesPayload = Get-Payload $nodesAfter
    $badLeaked = @(@($nodesPayload.nodes) | Where-Object { [string]$_.path -eq 'MCP018Bad' })
    Add-Check 'silent_add_nodes_batch_created_nothing' ($badLeaked.Count -eq 0) ("Node2D paths after the refused add: " + (@(@($nodesPayload.nodes) | ForEach-Object { [string]$_.path }) -join ', '))

    # (d) the game-side write path (same coercion helper, other process)
    $gameSeed = Invoke-Tool -Id 'silent_11_game_seed' -Tool 'running_game_set_node_property' -Arguments @{ node_path = 'A'; property = 'position'; value = @{ x = 3; y = 4 } } -Port $GamePort
    Add-Check 'silent_game_seed_position' ($null -ne (Get-Payload $gameSeed)) ("running_game_set_node_property seeded -> " + (ConvertTo-CompactJson (Get-Payload $gameSeed)))
    $gameDefect = Invoke-Tool -Id 'silent_12_game_1e20' -Tool 'running_game_set_node_property' -Arguments @{ node_path = 'A'; property = 'position'; value = 1.0e20 } -Port $GamePort
    $gameDefectMessage = Get-ErrorMessage $gameDefect
    Add-Check 'silent_game_write_refused' (((Get-ErrorCode $gameDefect) -eq -32602) -and ($gameDefectMessage -contains 'can_convert')) ("code=" + (Get-ErrorCode $gameDefect) + " message='" + $gameDefectMessage + "' sha256=" + (Get-FileSha (Join-Path $Evid 'silent_12_game_1e20.response.json')))
    $gameRead = Invoke-Tool -Id 'silent_13_game_read_back' -Tool 'running_game_get_node_properties' -Arguments @{ node_path = 'A'; properties = @('position') } -Port $GamePort
    $gameReadPayload = Get-Payload $gameRead
    Add-Check 'silent_game_read_back_unchanged' (($null -ne $gameReadPayload) -and ([double]$gameReadPayload.properties.position.x -eq 3) -and ([double]$gameReadPayload.properties.position.y -eq 4)) ("A.position in the game process = " + (ConvertTo-CompactJson $gameReadPayload.properties.position))

    # (e) regression guard: every legitimate value still writes and reads back
    $legal = @(
        @{ id = 'vector2_object'; path = 'A'; property = 'position'; value = @{ x = 7; y = 8 }; check = { param($p) ([double]$p.x -eq 7) -and ([double]$p.y -eq 8) } },
        @{ id = 'vector3_object'; path = 'World'; property = 'position'; value = @{ x = 1; y = 2; z = 3 }; check = { param($p) ([double]$p.x -eq 1) -and ([double]$p.y -eq 2) -and ([double]$p.z -eq 3) } },
        @{ id = 'float_value'; path = 'A'; property = 'rotation'; value = 1.5; check = { param($p) [Math]::Abs([double]$p - 1.5) -lt 0.0001 } },
        @{ id = 'int_value'; path = 'A'; property = 'z_index'; value = 3; check = { param($p) [int]$p -eq 3 } },
        @{ id = 'color_string'; path = 'A'; property = 'self_modulate'; value = '#ff0000'; check = { param($p) ([double]$p.r -eq 1) -and ([double]$p.g -eq 0) -and ([double]$p.b -eq 0) } },
        @{ id = 'string_value'; path = 'Ui'; property = 'tooltip_text'; value = 'mcp018-tooltip'; check = { param($p) [string]$p -eq 'mcp018-tooltip' } },
        @{ id = 'vector2_object_scale'; path = 'B'; property = 'scale'; value = @{ x = 2; y = 3 }; check = { param($p) ([double]$p.x -eq 2) -and ([double]$p.y -eq 3) } }
    )
    foreach ($case in $legal) {
        $writeResult = Invoke-Tool -Id ('legal_' + $case.id) -Tool 'editor_set_node_property' -Arguments @{ path = $case.path; property = $case.property; value = $case.value }
        $writePayload = Get-Payload $writeResult
        $readBack = Get-NodeProperty -Id ('legal_' + $case.id + '_read') -Path $case.path -Property $case.property
        $ok = ($null -ne $writePayload) -and ($null -ne $readBack) -and (& $case.check $readBack)
        Add-Check ('legal_value_' + $case.id) $ok ("written=" + (ConvertTo-CompactJson $writePayload) + " read_back=" + (ConvertTo-CompactJson $readBack) + " type=" + $readBack.type)
    }
    # The one *incompatible* spelling that used to be a silent zero: a
    # `"Vector2(x, y)"` **string**. `property_value_from_json` calls the engine's
    # `Variant::construct_from_string`, and this fork's implementation is a stub
    # that always answers NIL (`core/variant/variant.cpp:3531-3533`), so the value
    # stayed a String and `type_convert` answered `Vector2(0,0)` next to a
    # success. REPORT-018 D-1 records the stub; the gate now refuses the spelling.
    $stringForm = Invoke-Tool -Id 'silent_15_vector2_string_form' -Tool 'editor_set_node_property' -Arguments @{ path = 'A'; property = 'position'; value = 'Vector2(4, 5)' }
    Add-Check 'silent_vector2_string_form_refused' ((Get-ErrorCode $stringForm) -eq -32602 -and (Get-ErrorMessage $stringForm).Contains('Vector2')) ("code=" + (Get-ErrorCode $stringForm) + " message='" + (Get-ErrorMessage $stringForm) + "'")
    $stringFormRead = Get-NodeProperty -Id 'silent_16_read_after_string_form' -Path 'A' -Property 'position'
    Add-Check 'silent_vector2_string_form_kept_value' (($null -ne $stringFormRead) -and ([double]$stringFormRead.x -eq 7) -and ([double]$stringFormRead.y -eq 8)) ("A.position after the refused string form = " + (ConvertTo-CompactJson $stringFormRead))
    # The same gate on the project-settings write path: `application/config/name`
    # is a String, and a number *into* a String is a conversion the engine
    # declares (and a faithful one: it is the value's own spelling), so the
    # refusal is proven on a setting whose declared type has no such conversion -
    # one created here with an explicit `type`.
    $seedInt = Invoke-Tool -Id 'silent_17_seed_int_setting' -Tool 'project_set_setting' -Arguments @{ key = 'mcp018/probe_int'; type = 'int'; value = 5 }
    $settingsBad = Invoke-Tool -Id 'silent_18_setting_1e20' -Tool 'project_set_setting' -Arguments @{ key = 'mcp018/probe_int'; value = 1.0e20 }
    Add-Check 'silent_project_setting_refused' (((Get-ErrorCode $seedInt) -eq 0) -and ((Get-ErrorCode $settingsBad) -eq -32602)) ("seed code=" + (Get-ErrorCode $seedInt) + "; value 1e20 into an int setting -> code=" + (Get-ErrorCode $settingsBad) + " message='" + (Get-ErrorMessage $settingsBad) + "'")

    # ------------------------------------------------------------------
    # 4. section 3 -- editor_script_write
    # ------------------------------------------------------------------
    $exec = Invoke-Tool -Id 'esw_01_execute' -Tool 'editor_execute_gdscript' -Arguments @{ code = "var total = 0`nfor i in range(4):`n`ttotal += i`nreturn total" }
    $execPayload = Get-Payload $exec
    Add-Check 'editor_execute_gdscript_success' (($null -ne $execPayload) -and ([int]$execPayload.result -eq 6) -and ([string]$execPayload.result_type -eq 'int')) ("payload=" + (ConvertTo-CompactJson $execPayload) + " sha256=" + (Get-FileSha (Join-Path $Evid 'esw_01_execute.response.json')))
    $execBad = Invoke-Tool -Id 'esw_02_execute_syntax' -Tool 'editor_execute_gdscript' -Arguments @{ code = 'return (' }
    Add-Check 'editor_execute_gdscript_compile_error_32602' ((Get-ErrorCode $execBad) -eq -32602 -and (Get-ErrorMessage $execBad) -contains 'does not compile') ("code=" + (Get-ErrorCode $execBad) + " message='" + (Get-ErrorMessage $execBad) + "'")
    $execMissing = Invoke-Tool -Id 'esw_03_execute_missing_arg' -Tool 'editor_execute_gdscript' -Arguments @{}
    Add-Check 'editor_execute_gdscript_missing_code' ((Get-ErrorCode $execMissing) -eq -32602) ("code=" + (Get-ErrorCode $execMissing) + " message='" + (Get-ErrorMessage $execMissing) + "'")
    $execHelper = Invoke-Tool -Id 'esw_04_execute_helper_func' -Tool 'editor_execute_gdscript' -Arguments @{ code = "func triple(v):`n`treturn v * 3`nreturn triple(14)" }
    $execHelperPayload = Get-Payload $execHelper
    Add-Check 'editor_execute_gdscript_lifted_helper_func' (($null -ne $execHelperPayload) -and ([int]$execHelperPayload.result -eq 42)) ("payload=" + (ConvertTo-CompactJson $execHelperPayload))
    $big = ('return 1' + "`n") + ('# padding padding padding padding padding' + "`n") * 6000
    $execBig = Invoke-Tool -Id 'esw_05_execute_oversize' -Tool 'editor_execute_gdscript' -Arguments @{ code = $big }
    Add-Check 'editor_execute_gdscript_resource_bound' ((Get-ErrorCode $execBig) -eq -32602 -and (Get-ErrorMessage $execBig) -contains 'above the') ("code=" + (Get-ErrorCode $execBig) + " message='" + (Get-ErrorMessage $execBig) + "'")

    # The cross-tool chain of the group: attach a created script, then *read the
    # attachment back* with the executor (which is the only tool that can see a
    # node's script).
    $mkScript = Invoke-Tool -Id 'esw_06_create_script_for_chain' -Tool 'project_create_script' -Arguments @{ path = 'res://scripts/attached.gd'; content = "extends Node`n`nfunc marker() -> String:`n`treturn `"attached-ok`"`n" }
    $attach = Invoke-Tool -Id 'esw_07_attach_script' -Tool 'editor_set_node_script' -Arguments @{ node_path = 'Plain'; script_path = 'res://scripts/attached.gd' }
    $attachPayload = Get-Payload $attach
    Add-Check 'editor_set_node_script_success' (($null -ne $attachPayload) -and ([string]$attachPayload.script_path -eq 'res://scripts/attached.gd') -and ([bool]$attachPayload.attached) -and ([string]$attachPayload.node_path -eq 'Plain')) ("payload=" + (ConvertTo-CompactJson $attachPayload) + " sha256=" + (Get-FileSha (Join-Path $Evid 'esw_07_attach_script.response.json')))
    $readBackScript = Invoke-Tool -Id 'esw_08_read_attachment_back' -Tool 'editor_execute_gdscript' -Arguments @{ code = 'var n = EditorInterface.get_edited_scene_root().get_node("Plain")' + "`n" + 'var s = n.get_script()' + "`n" + 'return s.resource_path if s != null else "none"' }
    $readBackPayload = Get-Payload $readBackScript
    Add-Check 'editor_set_node_script_read_back_chain' (($null -ne $readBackPayload) -and ([string]$readBackPayload.result -eq 'res://scripts/attached.gd')) ("chain: project_create_script -> editor_set_node_script -> editor_execute_gdscript reads back '" + (ConvertTo-CompactJson $readBackPayload) + "'")
    $attachMissing = Invoke-Tool -Id 'esw_09_attach_missing_script' -Tool 'editor_set_node_script' -Arguments @{ node_path = 'Plain'; script_path = 'res://scripts/mcp018_absent.gd' }
    Add-Check 'editor_set_node_script_bottom_32001' ((Get-ErrorCode $attachMissing) -eq -32001) ("code=" + (Get-ErrorCode $attachMissing) + " message='" + (Get-ErrorMessage $attachMissing) + "'")
    $attachBadNode = Invoke-Tool -Id 'esw_10_attach_bad_node' -Tool 'editor_set_node_script' -Arguments @{ node_path = 'NoSuchNode018'; script_path = 'res://scripts/attached.gd' }
    Add-Check 'editor_set_node_script_bad_node_32001' ((Get-ErrorCode $attachBadNode) -eq -32001) ("code=" + (Get-ErrorCode $attachBadNode) + " message='" + (Get-ErrorMessage $attachBadNode) + "'")
    $attachMissingArg = Invoke-Tool -Id 'esw_11_attach_missing_arg' -Tool 'editor_set_node_script' -Arguments @{ node_path = 'Plain' }
    Add-Check 'editor_set_node_script_missing_arg_32602' ((Get-ErrorCode $attachMissingArg) -eq -32602) ("code=" + (Get-ErrorCode $attachMissingArg) + " message='" + (Get-ErrorMessage $attachMissingArg) + "'")

    # ------------------------------------------------------------------
    # 5. section 3 -- project_script_write
    # ------------------------------------------------------------------
    $createScript = Invoke-Tool -Id 'psw_01_create_template' -Tool 'project_create_script' -Arguments @{ path = 'res://scripts/templated.gd' }
    $createPayload = Get-Payload $createScript
    Add-Check 'project_create_script_template' (($null -ne $createPayload) -and ([bool]$createPayload.created) -and (-not [bool]$createPayload.existed_before)) ("payload=" + (ConvertTo-CompactJson $createPayload))
    $readTemplate = Invoke-Tool -Id 'psw_02_read_template' -Tool 'project_read_script' -Arguments @{ path = 'res://scripts/templated.gd' }
    $readTemplatePayload = Get-Payload $readTemplate
    $templateText = [string]$readTemplatePayload.content
    Add-Check 'project_create_script_template_read_back' ($templateText -ceq "extends Node`n`n`nfunc _ready() -> void:`n`tpass`n") ("read back (escaped)='" + ($templateText -replace "`n", '\n' -replace "`t", '\t') + "'")
    $createAgain = Invoke-Tool -Id 'psw_03_create_over_existing' -Tool 'project_create_script' -Arguments @{ path = 'res://scripts/templated.gd'; content = "extends Node2D`n" }
    $createAgainPayload = Get-Payload $createAgain
    Add-Check 'project_create_script_overwrite_is_reported' (($null -ne $createAgainPayload) -and ([bool]$createAgainPayload.existed_before)) ("payload=" + (ConvertTo-CompactJson $createAgainPayload))
    $createBad = Invoke-Tool -Id 'psw_04_create_bad_ext' -Tool 'project_create_script' -Arguments @{ path = 'res://scenes/not_a_script.tscn' }
    Add-Check 'project_create_script_extension_guard' ((Get-ErrorCode $createBad) -eq -32602 -and (Get-ErrorMessage $createBad) -contains '.gd or .cs') ("code=" + (Get-ErrorCode $createBad) + " message='" + (Get-ErrorMessage $createBad) + "'")
    $createMissingArg = Invoke-Tool -Id 'psw_05_create_missing_arg' -Tool 'project_create_script' -Arguments @{}
    Add-Check 'project_create_script_missing_arg' ((Get-ErrorCode $createMissingArg) -eq -32602) ("code=" + (Get-ErrorCode $createMissingArg) + " message='" + (Get-ErrorMessage $createMissingArg) + "'")

    $editContent = Invoke-Tool -Id 'psw_06_edit_content' -Tool 'project_edit_script' -Arguments @{ path = 'res://scripts/templated.gd'; content = "extends Node`n`nvar marker := 1`n" }
    $editContentPayload = Get-Payload $editContent
    Add-Check 'project_edit_script_content_mode' (($null -ne $editContentPayload) -and ([string]$editContentPayload.mode -eq 'content')) ("payload=" + (ConvertTo-CompactJson $editContentPayload))
    $editSearch = Invoke-Tool -Id 'psw_07_edit_search' -Tool 'project_edit_script' -Arguments @{ path = 'res://scripts/templated.gd'; search = 'marker'; replace = 'renamed_marker' }
    $editSearchPayload = Get-Payload $editSearch
    Add-Check 'project_edit_script_search_mode' (($null -ne $editSearchPayload) -and ([string]$editSearchPayload.mode -eq 'search_replace') -and ([int]$editSearchPayload.replacements -eq 1)) ("payload=" + (ConvertTo-CompactJson $editSearchPayload))
    $readEdited = Invoke-Tool -Id 'psw_08_read_edited' -Tool 'project_read_script' -Arguments @{ path = 'res://scripts/templated.gd' }
    $editedText = [string](Get-Payload $readEdited).content
    Add-Check 'project_edit_script_read_back_chain' ($editedText -contains 'renamed_marker') ("chain: project_edit_script -> project_read_script -> " + ($editedText -replace "`n", '\n'))
    $fileShaBefore = Get-FileSha (Join-Path $EditorProject 'scripts\templated.gd')
    $editNoMatch = Invoke-Tool -Id 'psw_09_edit_no_match' -Tool 'project_edit_script' -Arguments @{ path = 'res://scripts/templated.gd'; search = 'MCP018_NOT_THERE' }
    $fileShaAfter = Get-FileSha (Join-Path $EditorProject 'scripts\templated.gd')
    Add-Check 'project_edit_script_no_match_is_32001_and_keeps_bytes' (((Get-ErrorCode $editNoMatch) -eq -32001) -and ($fileShaBefore -eq $fileShaAfter)) ("code=" + (Get-ErrorCode $editNoMatch) + " message='" + (Get-ErrorMessage $editNoMatch) + "' sha256 before={0} after={1}" -f $fileShaBefore, $fileShaAfter)
    $editAmbiguous = Invoke-Tool -Id 'psw_10_edit_ambiguous' -Tool 'project_edit_script' -Arguments @{ path = 'res://scripts/templated.gd'; content = 'x'; search = 'y' }
    Add-Check 'project_edit_script_ambiguous_modes' ((Get-ErrorCode $editAmbiguous) -eq -32602 -and (Get-ErrorMessage $editAmbiguous) -contains 'alternatives') ("code=" + (Get-ErrorCode $editAmbiguous) + " message='" + (Get-ErrorMessage $editAmbiguous) + "'")
    $editNoMode = Invoke-Tool -Id 'psw_11_edit_no_mode' -Tool 'project_edit_script' -Arguments @{ path = 'res://scripts/templated.gd' }
    Add-Check 'project_edit_script_missing_mode' ((Get-ErrorCode $editNoMode) -eq -32602) ("code=" + (Get-ErrorCode $editNoMode) + " message='" + (Get-ErrorMessage $editNoMode) + "'")
    $editMissing = Invoke-Tool -Id 'psw_12_edit_missing_file' -Tool 'project_edit_script' -Arguments @{ path = 'res://scripts/mcp018_absent.gd'; content = 'x' }
    Add-Check 'project_edit_script_missing_file_32001' ((Get-ErrorCode $editMissing) -eq -32001) ("code=" + (Get-ErrorCode $editMissing) + " message='" + (Get-ErrorMessage $editMissing) + "'")

    # ------------------------------------------------------------------
    # 6. section 3 -- project_autoload_write
    # ------------------------------------------------------------------
    $pgBefore = Get-FileSha (Join-Path $EditorProject 'project.godot')
    $addAutoload = Invoke-Tool -Id 'al_01_add' -Tool 'project_add_autoload' -Arguments @{ name = 'Mcp018One'; path = 'res://scripts/one.gd' }
    $addPayload = Get-Payload $addAutoload
    Add-Check 'project_add_autoload_success' (($null -ne $addPayload) -and ([bool]$addPayload.added) -and ([string]$addPayload.setting_value -eq '*res://scripts/one.gd')) ("payload=" + (ConvertTo-CompactJson $addPayload) + " sha256=" + (Get-FileSha (Join-Path $Evid 'al_01_add.response.json')))
    $settingsRead = Invoke-Tool -Id 'al_02_read_settings' -Tool 'project_get_settings' -Arguments @{ prefix = 'autoload/' }
    $settingsPayload = Get-Payload $settingsRead
    Add-Check 'project_add_autoload_read_back_chain' ($null -ne $settingsPayload -and [string]$settingsPayload.settings.'autoload/Mcp018One' -eq '*res://scripts/one.gd') ("project_get_settings prefix=autoload/ -> " + (ConvertTo-CompactJson $settingsPayload))
    $pgAfterAdd = Get-FileSha (Join-Path $EditorProject 'project.godot')
    $pgText = Get-Content -Raw -Encoding UTF8 (Join-Path $EditorProject 'project.godot')
    Add-Check 'project_add_autoload_published_to_project_godot' (($pgBefore -ne $pgAfterAdd) -and ($pgText -match 'Mcp018One="\*res://scripts/one\.gd"')) ("project.godot sha256 {0} -> {1}; contains the setting={2}" -f $pgBefore, $pgAfterAdd, ($pgText -match 'Mcp018One'))
    Add-Check 'project_add_autoload_no_scratch_left' ((-not (Test-Path (Join-Path $EditorProject 'project.mcp-tmp.godot'))) -and (-not (Test-Path (Join-Path $EditorProject 'project.mcp-tmp.godot.bak')))) ("project.mcp-tmp.godot exists={0} bak exists={1}" -f (Test-Path (Join-Path $EditorProject 'project.mcp-tmp.godot')), (Test-Path (Join-Path $EditorProject 'project.mcp-tmp.godot.bak')))
    $addAgain = Invoke-Tool -Id 'al_03_add_again' -Tool 'project_add_autoload' -Arguments @{ name = 'Mcp018One'; path = 'res://scripts/one.gd' }
    $addAgainPayload = Get-Payload $addAgain
    Add-Check 'project_add_autoload_idempotent' (($null -ne $addAgainPayload) -and ([bool]$addAgainPayload.already_present)) ("payload=" + (ConvertTo-CompactJson $addAgainPayload))
    $addConflict = Invoke-Tool -Id 'al_04_add_conflict' -Tool 'project_add_autoload' -Arguments @{ name = 'Mcp018One'; path = 'res://scripts/two.gd' }
    Add-Check 'project_add_autoload_conflict_32000' ((Get-ErrorCode $addConflict) -eq -32000 -and $null -ne $addConflict.error.data.current_value) ("code=" + (Get-ErrorCode $addConflict) + " message='" + (Get-ErrorMessage $addConflict) + "' data=" + (ConvertTo-CompactJson $addConflict.error.data))
    $addMissingPath = Invoke-Tool -Id 'al_05_add_missing_path' -Tool 'project_add_autoload' -Arguments @{ name = 'Mcp018Missing'; path = 'res://scripts/mcp018_absent.gd' }
    Add-Check 'project_add_autoload_bottom_32001' ((Get-ErrorCode $addMissingPath) -eq -32001) ("code=" + (Get-ErrorCode $addMissingPath) + " message='" + (Get-ErrorMessage $addMissingPath) + "'")
    $addMissingArg = Invoke-Tool -Id 'al_06_add_missing_arg' -Tool 'project_add_autoload' -Arguments @{ path = 'res://scripts/one.gd' }
    Add-Check 'project_add_autoload_missing_arg' ((Get-ErrorCode $addMissingArg) -eq -32602) ("code=" + (Get-ErrorCode $addMissingArg) + " message='" + (Get-ErrorMessage $addMissingArg) + "'")
    $removeAutoload = Invoke-Tool -Id 'al_07_remove' -Tool 'project_remove_autoload' -Arguments @{ name = 'Mcp018One' }
    $removePayload = Get-Payload $removeAutoload
    Add-Check 'project_remove_autoload_success' (($null -ne $removePayload) -and ([bool]$removePayload.removed) -and ([string]$removePayload.old_path -eq '*res://scripts/one.gd')) ("payload=" + (ConvertTo-CompactJson $removePayload) + " sha256=" + (Get-FileSha (Join-Path $Evid 'al_07_remove.response.json')))
    $settingsAfterRemove = Invoke-Tool -Id 'al_08_read_settings_after_remove' -Tool 'project_get_settings' -Arguments @{ prefix = 'autoload/' }
    $settingsAfterPayload = Get-Payload $settingsAfterRemove
    Add-Check 'project_remove_autoload_read_back_chain' ($null -ne $settingsAfterPayload -and -not ($settingsAfterPayload.settings.PSObject.Properties.Name -contains 'autoload/Mcp018One')) ("project_get_settings prefix=autoload/ -> " + (ConvertTo-CompactJson $settingsAfterPayload))
    $removeMissing = Invoke-Tool -Id 'al_09_remove_missing' -Tool 'project_remove_autoload' -Arguments @{ name = 'Mcp018One' }
    Add-Check 'project_remove_autoload_absent_32001' ((Get-ErrorCode $removeMissing) -eq -32001) ("code=" + (Get-ErrorCode $removeMissing) + " message='" + (Get-ErrorMessage $removeMissing) + "'")
    $removeMissingArg = Invoke-Tool -Id 'al_10_remove_missing_arg' -Tool 'project_remove_autoload' -Arguments @{}
    Add-Check 'project_remove_autoload_missing_arg' ((Get-ErrorCode $removeMissingArg) -eq -32602) ("code=" + (Get-ErrorCode $removeMissingArg) + " message='" + (Get-ErrorMessage $removeMissingArg) + "'")

    # ------------------------------------------------------------------
    # 7. section 3 -- project_setting_write
    # ------------------------------------------------------------------
    $setVec = Invoke-Tool -Id 'ps_01_set_vector2' -Tool 'project_set_setting' -Arguments @{ key = 'mcp018/probe_vec'; type = 'Vector2'; value = @{ x = 10; y = 20 } }
    $setVecPayload = Get-Payload $setVec
    Add-Check 'project_set_setting_vector2_type_fidelity' (($null -ne $setVecPayload) -and ([string]$setVecPayload.type -eq 'Vector2') -and ([double]$setVecPayload.value.x -eq 10) -and ([double]$setVecPayload.value.y -eq 20) -and (-not [bool]$setVecPayload.existed_before) -and ([bool]$setVecPayload.created)) ("payload=" + (ConvertTo-CompactJson $setVecPayload) + " sha256=" + (Get-FileSha (Join-Path $Evid 'ps_01_set_vector2.response.json')))
    $settingsVecRead = Invoke-Tool -Id 'ps_02_read_settings_vec' -Tool 'project_get_settings' -Arguments @{ prefix = 'mcp018/' }
    $settingsVecPayload = Get-Payload $settingsVecRead
    # `project_get_settings` renders the value through the engine's own `str()`,
    # so a `Vector2` setting comes back as the object shape and the *type* is what
    # the read-back proves: the two components are the ones that were set.
    $vecRead = $settingsVecPayload.settings.'mcp018/probe_vec'
    Add-Check 'project_set_setting_read_back_chain' ($null -ne $settingsVecPayload -and $null -ne $vecRead -and ([double]$vecRead.x -eq 10) -and ([double]$vecRead.y -eq 20)) ("project_get_settings prefix=mcp018/ -> " + (ConvertTo-CompactJson $settingsVecPayload))
    $setInt = Invoke-Tool -Id 'ps_03_set_int' -Tool 'project_set_setting' -Arguments @{ key = 'mcp018/probe_int'; type = 'int'; value = 7.0 }
    $setIntPayload = Get-Payload $setInt
    Add-Check 'project_set_setting_int_folds_double' (($null -ne $setIntPayload) -and ([string]$setIntPayload.type -eq 'int') -and ([int]$setIntPayload.value -eq 7)) ("payload=" + (ConvertTo-CompactJson $setIntPayload))
    $setBadType = Invoke-Tool -Id 'ps_04_set_bad_type' -Tool 'project_set_setting' -Arguments @{ key = 'mcp018/probe_vec'; type = 'Nonsense'; value = 1 }
    Add-Check 'project_set_setting_unknown_type_32602' ((Get-ErrorCode $setBadType) -eq -32602 -and (Get-ErrorMessage $setBadType) -contains 'Accepted names are') ("code=" + (Get-ErrorCode $setBadType) + " message='" + (Get-ErrorMessage $setBadType) + "'")
    $setMismatch = Invoke-Tool -Id 'ps_05_set_type_mismatch' -Tool 'project_set_setting' -Arguments @{ key = 'mcp018/probe_vec'; type = 'String'; value = 'x' }
    Add-Check 'project_set_setting_declared_type_mismatch' ((Get-ErrorCode $setMismatch) -eq -32602 -and (Get-ErrorMessage $setMismatch) -contains 'declared as Vector2') ("code=" + (Get-ErrorCode $setMismatch) + " message='" + (Get-ErrorMessage $setMismatch) + "'")
    $setBadValue = Invoke-Tool -Id 'ps_06_set_bad_value' -Tool 'project_set_setting' -Arguments @{ key = 'mcp018/probe_int'; value = 1.0e20 }
    Add-Check 'project_set_setting_value_gate' ((Get-ErrorCode $setBadValue) -eq -32602) ("code=" + (Get-ErrorCode $setBadValue) + " message='" + (Get-ErrorMessage $setBadValue) + "'")
    $setNull = Invoke-Tool -Id 'ps_07_set_null_new_key' -Tool 'project_set_setting' -Arguments @{ key = 'mcp018/probe_null'; value = $null }
    Add-Check 'project_set_setting_null_new_key' ((Get-ErrorCode $setNull) -eq -32602) ("code=" + (Get-ErrorCode $setNull) + " message='" + (Get-ErrorMessage $setNull) + "'")
    $setMissingArg = Invoke-Tool -Id 'ps_08_set_missing_arg' -Tool 'project_set_setting' -Arguments @{ key = 'mcp018/probe_int' }
    Add-Check 'project_set_setting_missing_value' ((Get-ErrorCode $setMissingArg) -eq -32602) ("code=" + (Get-ErrorCode $setMissingArg) + " message='" + (Get-ErrorMessage $setMissingArg) + "'")

    # ------------------------------------------------------------------
    # 8. section 3 -- project_cross_scene_write
    # ------------------------------------------------------------------
    $crossOnePath = Join-Path $EditorProject 'cross\one.tscn'
    $crossTwoPath = Join-Path $EditorProject 'cross\two.tscn'
    $crossOneBefore = Get-FileSha $crossOnePath
    $crossTwoBefore = Get-FileSha $crossTwoPath
    $dryRun = Invoke-Tool -Id 'cs_01_dry_run' -Tool 'project_set_node_property_across_scenes' -Arguments @{ type = 'Node2D'; property = 'rotation'; value = 0.75; path_filter = 'res://cross'; force = $true; dry_run = $true }
    $dryPayload = Get-Payload $dryRun
    Add-Check 'across_scenes_dry_run' (($null -ne $dryPayload) -and ([bool]$dryPayload.dry_run) -and ([int]$dryPayload.total_scenes -eq 2) -and ([int]$dryPayload.total_nodes -eq 3)) ("payload=" + (ConvertTo-CompactJson $dryPayload))
    Add-Check 'across_scenes_dry_run_wrote_nothing' (((Get-FileSha $crossOnePath) -eq $crossOneBefore) -and ((Get-FileSha $crossTwoPath) -eq $crossTwoBefore)) ("one.tscn sha256={0} (before {1}); two.tscn sha256={2} (before {3})" -f (Get-FileSha $crossOnePath), $crossOneBefore, (Get-FileSha $crossTwoPath), $crossTwoBefore)

    # The deliberately broken middle file: two.tscn is the second of the sorted
    # pair, one.tscn would already have been planned and written by a naive
    # implementation.
    Write-Utf8NoBom -Path $crossTwoPath -Text ($BrokenScene + "`n")
    $brokenSha = Get-FileSha $crossTwoPath
    $broken = Invoke-Tool -Id 'cs_02_broken_middle_file' -Tool 'project_set_node_property_across_scenes' -Arguments @{ type = 'Node2D'; property = 'rotation'; value = 0.75; path_filter = 'res://cross'; force = $true; dry_run = $false }
    $brokenMessage = Get-ErrorMessage $broken
    $brokenNamed = @($broken.error.data.scenes.scenes_named)
    Add-Check 'across_scenes_broken_middle_file_refused' (((Get-ErrorCode $broken) -eq -32000) -and ($brokenMessage -contains 'Refusing to write') -and ($brokenNamed.Count -eq 1) -and ([string]$brokenNamed[0] -eq 'res://cross/two.tscn')) ("code=" + (Get-ErrorCode $broken) + " message='" + $brokenMessage + "' named=[" + ($brokenNamed -join ', ') + "] reason='" + [string]$broken.error.data.scenes.errors[0].reason + "' sha256=" + (Get-FileSha (Join-Path $Evid 'cs_02_broken_middle_file.response.json')))
    Add-Check 'across_scenes_broken_refusal_wrote_nothing' (((Get-FileSha $crossOnePath) -eq $crossOneBefore) -and ((Get-FileSha $crossTwoPath) -eq $brokenSha)) ("one.tscn sha256={0} (before {1}); two.tscn sha256={2} (unchanged broken bytes {3})" -f (Get-FileSha $crossOnePath), $crossOneBefore, (Get-FileSha $crossTwoPath), $brokenSha)

    # A matched node that cannot take the value, on a whole-scene level.
    Write-Utf8NoBom -Path $crossTwoPath -Text ($CrossTwo + "`n")
    $badValue = Invoke-Tool -Id 'cs_03_value_cannot_fit' -Tool 'project_set_node_property_across_scenes' -Arguments @{ type = 'Node2D'; property = 'position'; value = 1.0e20; path_filter = 'res://cross'; force = $true; dry_run = $false }
    Add-Check 'across_scenes_value_gate_refuses_whole_call' ((Get-ErrorCode $badValue) -eq -32000 -and @($badValue.error.data.scenes.errors).Count -eq 2) ("code=" + (Get-ErrorCode $badValue) + " errors=" + (@($badValue.error.data.scenes.errors).Count) + " first='" + [string]$badValue.error.data.scenes.errors[0].reason + "'")
    Add-Check 'across_scenes_value_gate_wrote_nothing' (((Get-FileSha $crossOnePath) -eq $crossOneBefore) -and ((Get-FileSha $crossTwoPath) -eq $crossTwoBefore)) ("one.tscn sha256={0} two.tscn sha256={1}" -f (Get-FileSha $crossOnePath), (Get-FileSha $crossTwoPath))

    # The commit, and the read-back through the file on disk.
    $commit = Invoke-Tool -Id 'cs_04_commit' -Tool 'project_set_node_property_across_scenes' -Arguments @{ type = 'Node2D'; property = 'rotation'; value = 0.75; path_filter = 'res://cross'; force = $true; dry_run = $false }
    $commitPayload = Get-Payload $commit
    Add-Check 'across_scenes_commit' (($null -ne $commitPayload) -and ([int]$commitPayload.total_scenes -eq 2) -and ([int]$commitPayload.total_nodes -eq 3) -and ([string]$commitPayload.scenes_affected[0].mode -eq 'offline_saved')) ("payload=" + (ConvertTo-CompactJson $commitPayload) + " sha256=" + (Get-FileSha (Join-Path $Evid 'cs_04_commit.response.json')))
    $oneText = Get-Content -Raw -Encoding UTF8 $crossOnePath
    Add-Check 'across_scenes_commit_written_to_disk' (($oneText -match 'rotation = 0\.75') -and ((Get-FileSha $crossOnePath) -ne $crossOneBefore)) ("one.tscn now: " + ($oneText -replace "`n", '\n'))
    $oneRead = Invoke-Tool -Id 'cs_05_read_scene_content' -Tool 'project_read_scene_file_content' -Arguments @{ path = 'res://cross/one.tscn' }
    $oneReadPayload = Get-Payload $oneRead
    Add-Check 'across_scenes_read_back_chain' (($null -ne $oneReadPayload) -and ([string]$oneReadPayload.content -match 'rotation = 0\.75')) ("chain: across_scenes -> project_read_scene_file_content -> contains rotation 0.75=" + ([string]$oneReadPayload.content -match 'rotation = 0\.75'))
    Add-Check 'across_scenes_no_scratch_left' ((-not (Test-Path (Join-Path $EditorProject 'cross\one.mcp-tmp.tscn'))) -and (-not (Test-Path (Join-Path $EditorProject 'cross\one.mcp-tmp.tscn.bak')))) ("one.mcp-tmp.tscn exists={0}" -f (Test-Path (Join-Path $EditorProject 'cross\one.mcp-tmp.tscn')))
    Add-Check 'across_scenes_excludes_addons' ((ConvertTo-CompactJson $commitPayload) -notmatch 'in_addon') ("the addons scene is not part of scenes_affected: " + (ConvertTo-CompactJson $commitPayload.scenes_affected))
    $badType = Invoke-Tool -Id 'cs_06_bad_type' -Tool 'project_set_node_property_across_scenes' -Arguments @{ type = 'NoSuchThing018'; property = 'rotation'; value = 0.5; dry_run = $true }
    Add-Check 'across_scenes_unknown_type_32602' ((Get-ErrorCode $badType) -eq -32602) ("code=" + (Get-ErrorCode $badType) + " message='" + (Get-ErrorMessage $badType) + "'")
    $csMissingArg = Invoke-Tool -Id 'cs_07_missing_arg' -Tool 'project_set_node_property_across_scenes' -Arguments @{ type = 'Node2D'; property = 'rotation' }
    Add-Check 'across_scenes_missing_value' ((Get-ErrorCode $csMissingArg) -eq -32602) ("code=" + (Get-ErrorCode $csMissingArg) + " message='" + (Get-ErrorMessage $csMissingArg) + "'")

    # ------------------------------------------------------------------
    # 9. section 3 -- project_resource_uid_read (both directions)
    # ------------------------------------------------------------------
    $pathToUid = Invoke-Tool -Id 'uid_01_path_to_uid' -Tool 'project_convert_path_to_uid' -Arguments @{ path = 'res://scripts/one.gd' }
    $pathToUidPayload = Get-Payload $pathToUid
    $pathFieldOk = $null -ne $pathToUidPayload -and ([string]$pathToUidPayload.path -eq 'res://scripts/one.gd')
    $uidField = if ($null -ne $pathToUidPayload) { [string]$pathToUidPayload.uid } else { '<none>' }
    $uidFieldIsUid = ($uidField -eq '') -or $uidField.StartsWith('uid://')
    Add-Check 'uid_path_to_uid_success' ($pathFieldOk -and $uidFieldIsUid) ("payload=" + (ConvertTo-CompactJson $pathToUidPayload) + " direction_rule(uid empty or uid://)=" + $uidFieldIsUid + " sha256=" + (Get-FileSha (Join-Path $Evid 'uid_01_path_to_uid.response.json')))

    if ($uidField -ne '' -and $uidField -ne '<none>') {
        $uidToPath = Invoke-Tool -Id 'uid_02_uid_to_path_roundtrip' -Tool 'project_convert_uid_to_path' -Arguments @{ uid = $uidField }
        $uidToPathPayload = Get-Payload $uidToPath
        Add-Check 'uid_round_trip' ($null -ne $uidToPathPayload -and ([string]$uidToPathPayload.uid -eq $uidField) -and ([string]$uidToPathPayload.path -eq 'res://scripts/one.gd')) ("path->uid gave '" + $uidField + "'; uid->path gave " + (ConvertTo-CompactJson $uidToPathPayload))
    } else {
        # A path with no UID registered is the contract's other documented case:
        # an empty `uid` and no error.
        Add-Check 'uid_unregistered_path_is_empty_uid' ($pathFieldOk -and $uidField -eq '') ("the imported project has no uid for res://scripts/one.gd, so the answer is the contract's empty-uid success: " + (ConvertTo-CompactJson $pathToUidPayload))
    }
    # A registered UID that is not backed by a file: created through the editor
    # executor, then resolved by the tool. This proves `uid -> path` for a real
    # id independently of whatever the import happened to assign.
    $seedUid = Invoke-Tool -Id 'uid_03_seed_uid' -Tool 'editor_execute_gdscript' -Arguments @{ code = 'ResourceUID.add_id(1234567, "res://scenes/main.tscn")' + "`n" + 'return ResourceUID.id_to_text(1234567)' }
    $seedUidPayload = Get-Payload $seedUid
    $seedUidText = if ($null -ne $seedUidPayload) { [string]$seedUidPayload.result } else { '' }
    Add-Check 'uid_seed' ($seedUidText.StartsWith('uid://')) ("seeded uid=" + $seedUidText)
    $uidToPath2 = Invoke-Tool -Id 'uid_04_uid_to_path_seeded' -Tool 'project_convert_uid_to_path' -Arguments @{ uid = $seedUidText }
    $uidToPath2Payload = Get-Payload $uidToPath2
    Add-Check 'uid_uid_to_path_success' ($null -ne $uidToPath2Payload -and ([string]$uidToPath2Payload.uid -eq $seedUidText) -and ([string]$uidToPath2Payload.path -eq 'res://scenes/main.tscn')) ("payload=" + (ConvertTo-CompactJson $uidToPath2Payload) + " sha256=" + (Get-FileSha (Join-Path $Evid 'uid_04_uid_to_path_seeded.response.json')))
    # Bottom-layer failures and the direction contrast.
    $uidFormat = Invoke-Tool -Id 'uid_05_uid_to_path_bad_format' -Tool 'project_convert_uid_to_path' -Arguments @{ uid = 'res://scripts/one.gd' }
    Add-Check 'uid_uid_to_path_rejects_a_path_32602' ((Get-ErrorCode $uidFormat) -eq -32602 -and (Get-ErrorMessage $uidFormat) -contains 'uid://') ("code=" + (Get-ErrorCode $uidFormat) + " message='" + (Get-ErrorMessage $uidFormat) + "'")
    $uidUpper = Invoke-Tool -Id 'uid_06_uid_to_path_upper' -Tool 'project_convert_uid_to_path' -Arguments @{ uid = 'uid://UPPER' }
    Add-Check 'uid_uid_to_path_rejects_upper_32602' ((Get-ErrorCode $uidUpper) -eq -32602) ("code=" + (Get-ErrorCode $uidUpper) + " message='" + (Get-ErrorMessage $uidUpper) + "'")
    $uidUnknown = Invoke-Tool -Id 'uid_07_uid_to_path_unknown' -Tool 'project_convert_uid_to_path' -Arguments @{ uid = 'uid://zzzzzzzzzz' }
    Add-Check 'uid_uid_to_path_unknown_32001' ((Get-ErrorCode $uidUnknown) -eq -32001) ("code=" + (Get-ErrorCode $uidUnknown) + " message='" + (Get-ErrorMessage $uidUnknown) + "'")
    $uidMissingArg = Invoke-Tool -Id 'uid_08_uid_to_path_missing_arg' -Tool 'project_convert_uid_to_path' -Arguments @{}
    Add-Check 'uid_uid_to_path_missing_arg_32602' ((Get-ErrorCode $uidMissingArg) -eq -32602) ("code=" + (Get-ErrorCode $uidMissingArg) + " message='" + (Get-ErrorMessage $uidMissingArg) + "'")
    $pathToUidBad = Invoke-Tool -Id 'uid_09_path_to_uid_rejects_a_uid_32602' -Tool 'project_convert_path_to_uid' -Arguments @{ path = $seedUidText }
    Add-Check 'uid_path_to_uid_rejects_a_uid_32602' ((Get-ErrorCode $pathToUidBad) -eq -32602) ("code=" + (Get-ErrorCode $pathToUidBad) + " message='" + (Get-ErrorMessage $pathToUidBad) + "'")
    $pathToUidMissing = Invoke-Tool -Id 'uid_10_path_to_uid_missing_file' -Tool 'project_convert_path_to_uid' -Arguments @{ path = 'res://scripts/mcp018_absent.gd' }
    Add-Check 'uid_path_to_uid_missing_file_32001' ((Get-ErrorCode $pathToUidMissing) -eq -32001) ("code=" + (Get-ErrorCode $pathToUidMissing) + " message='" + (Get-ErrorMessage $pathToUidMissing) + "'")
    $pathToUidMissingArg = Invoke-Tool -Id 'uid_11_path_to_uid_wrong_arg_name' -Tool 'project_convert_path_to_uid' -Arguments @{ uid = $seedUidText }
    Add-Check 'uid_argument_names_are_the_discriminator' ((Get-ErrorCode $pathToUidMissingArg) -eq -32602) ("project_convert_path_to_uid with {'uid': ...} -> code=" + (Get-ErrorCode $pathToUidMissingArg) + " message='" + (Get-ErrorMessage $pathToUidMissingArg) + "'")
    $pathInUidField = ($uidField -eq '') -or $uidField.StartsWith('uid://')
    $uidAnswerPath = if ($null -ne $uidToPath2Payload) { [string]$uidToPath2Payload.path } else { '<none>' }
    $pathFieldInUidAnswer = $uidAnswerPath.StartsWith('res://')
    Add-Check 'uid_direction_rules_machine_checked' ($pathInUidField -and $pathFieldInUidAnswer) ("path_to_uid: uid field is a uid or empty={0} (value '{1}'); uid_to_path: path field starts with res://={2} (value '{3}')" -f $pathInUidField, $uidField, $pathFieldInUidAnswer, $uidAnswerPath)
} catch {
    Add-Check 'harness_exception' $false ("EXCEPTION: " + $_.Exception.Message + " @ line " + $_.InvocationInfo.ScriptLineNumber + " :: " + $_.InvocationInfo.PositionMessage)
} finally {
    Stop-Engine -Handle $script:GameHandle
    Stop-Engine -Handle $script:EditorHandle
    $userPortPidAfter = Get-ListenerPid -Port $UserPort
    Add-Check 'guard_user_port_9877' ($userPortPidBefore -eq $userPortPidAfter) ("pid_before={0} pid_after={1}" -f $userPortPidBefore, $userPortPidAfter)
}

Write-Host ''
Write-Host '========================== SUMMARY =========================='
$passed = @($script:Results | Where-Object { $_.pass }).Count
$total = $script:Results.Count
foreach ($r in $script:Results) {
    $tag = if ($r.pass) { 'PASS' } else { 'FAIL' }
    Write-Host ("{0}  {1}" -f $tag, $r.id)
}
Write-Host ("{0}/{1} checks passed" -f $passed, $total)
if ($passed -ne $total) { exit 1 }
exit 0
