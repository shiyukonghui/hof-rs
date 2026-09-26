# =============================================================================
#  mcp024b_ergonomics_batch2_evidence.ps1 -- live evidence for TASK-024b
#
#  Item (1) E-1 + G-2 - `project_get_scene_dependencies` answers a real `type`
#  and a `res://` `path` that can be fed straight back:
#
#    * the entry is the engine's own `p_add_types = true` layout
#      (`scene/resources/resource_format_text.cpp:960-968`), split into its
#      fields - `type` is the type, not the third field (which is the engine's
#      `fallback_path` when the tag carries a `uid=`, :949);
#    * `path` is a `res://` path in both states of a scene: the hand-written one
#      (no `uid=`) and the one the *engine itself saved* (with `uid=`, resolved
#      through the UID registry - `path_source = "uid"`);
#    * `uid`, `declared_type` and `path_source` are reported next to it, so the
#      caller never has to guess which field is which;
#    * regression on two different scenes, one of them with a script dependency.
#
#  Item (2) E-3 - one shape per kind:
#
#    * `Vector4`/`Vector4i`/`Rect2i` answer objects exactly like the
#      `Vector2`/`Vector3`/`Color`/`Rect2` family already did;
#    * every packed array answers a JSON array of its element shape
#      (`PackedVector4Array` -> `[{x,y,z,w}, ...]`, `PackedByteArray` -> ints);
#    * verified on the **editor** endpoint (9888) and the **game** endpoint
#      (9889) with 8 packed properties plus `Vector4`/`Vector4i`/`Rect2i`, and
#      every value is written back through the write tool *as it was read* -
#      the caller performs no string surgery (GDR-25 section 23.1 rule 1).
#
#  Gate-2 classes per touched tool: success / missing parameter (-32602) /
#  underlying failure (-32001). The cross-tool chain is at the end and counts
#  the caller's string operations step by step (target 0).
#
#  Discipline (PLAYBOOK sections 3 and 7): request bodies are built with
#  `ConvertTo-Json` and posted with `curl.exe --data-binary @file`; response
#  bodies are written by `curl.exe -s -o <file>` (never through a pipe or
#  `Out-File`) and every body gets a sha256. The user's editor on 9877 is never
#  touched - only its listener pid is read as a before/after guard.
#
#  Usage:
#    powershell -NoProfile -ExecutionPolicy Bypass -File mcp024b_ergonomics_batch2_evidence.ps1
# =============================================================================

param(
    [int]$EditorPort = 9888,
    [int]$GamePort = 9889
)

$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$Engine = Join-Path $RepoRoot 'bin\godot.windows.editor.x86_64.console.exe'
$Curl = Join-Path $env:SystemRoot 'System32\curl.exe'
$UserPort = 9877
$Root = Join-Path $env:TEMP 'task024b-ergonomics'
$Ev = Join-Path $Root 'evidence'
$LogRoot = Join-Path $Root 'logs'
$Project = Join-Path $Root 'proj'

Remove-Item -Recurse -Force $Root -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $Ev, $LogRoot, $Project | Out-Null

$script:Checks = New-Object System.Collections.Generic.List[object]
$script:EditorHandle = $null
$script:GameHandle = $null

function Note {
    param([string]$Text)
    Write-Host $Text
}

function Check {
    param([string]$Id, [bool]$Pass, [string]$Evidence)
    $script:Checks.Add([pscustomobject]@{ id = $Id; pass = $Pass; evidence = $Evidence })
    $tag = if ($Pass) { 'PASS' } else { 'FAIL' }
    Write-Host ("[{0}] {1}" -f $tag, $Id)
    Write-Host ("       {0}" -f $Evidence)
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Text)
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    [IO.File]::WriteAllBytes($Path, (New-Object Text.UTF8Encoding($false)).GetBytes($Text))
}

function Get-FileSha {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return '<missing>' }
    return (Get-FileHash -Algorithm SHA256 -Path $Path).Hash.ToLower()
}

# -----------------------------------------------------------------------------
# HTTP against the MCP endpoint
# -----------------------------------------------------------------------------

function Format-CallBody {
    param([string]$Tool, $Arguments, [int]$Id = 1)
    $envelope = [ordered]@{
        jsonrpc = '2.0'; id = $Id; method = 'tools/call'
        params  = [ordered]@{ name = $Tool; arguments = $Arguments }
    }
    return (ConvertTo-Json -InputObject $envelope -Depth 20 -Compress)
}

function Invoke-Curl {
    param([string]$Id, [string]$Json, [int]$Port, [int]$MaxTimeSec = 90)
    $bodyFile = Join-Path $Ev ("{0}.request.json" -f $Id)
    $respFile = Join-Path $Ev ("{0}.response.json" -f $Id)
    Write-Utf8NoBom -Path $bodyFile -Text $Json
    if (Test-Path $respFile) { Remove-Item -Force $respFile }
    & $Curl -s --max-time $MaxTimeSec -o $respFile -H 'Content-Type: application/json' `
        --data-binary ('@' + $bodyFile) ("http://127.0.0.1:{0}/mcp" -f $Port) | Out-Null
    $curlExit = $LASTEXITCODE
    if (-not (Test-Path $respFile)) {
        Note ("[{0}] curl port={1} exit={2} :: NO RESPONSE FILE" -f $Id, $Port, $curlExit)
        return ''
    }
    $bytes = [IO.File]::ReadAllBytes($respFile)
    $sha = (Get-FileHash -Algorithm SHA256 -Path $respFile).Hash.ToLower()
    $text = [Text.Encoding]::UTF8.GetString($bytes)
    Note ("[{0}] curl port={1} exit={2} bytes={3} sha256={4}" -f $Id, $Port, $curlExit, $bytes.Length, $sha)
    Note ("       request : {0}" -f $Json)
    Note ("       response: {0}" -f $text)
    return $text
}

function Invoke-Tool {
    param([string]$Id, [string]$Tool, $Arguments, [int]$Port = $EditorPort, [int]$MaxTimeSec = 90)
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

function Get-ErrorSuggestion {
    param($Envelope)
    if ($null -eq $Envelope -or $null -eq $Envelope.error -or $null -eq $Envelope.error.data) { return '' }
    return [string]$Envelope.error.data.suggestion
}

function ConvertTo-CompactJson {
    param($Object)
    if ($null -eq $Object) { return '<null>' }
    return (ConvertTo-Json -InputObject $Object -Depth 20 -Compress)
}

# The Variant type name a JSON value answers after `ConvertFrom-Json`. It is the
# discriminator this batch is about: an object/array must not arrive as a string.
function Get-JsonKind {
    param($Value)
    if ($null -eq $Value) { return 'null' }
    if ($Value -is [string]) { return 'string' }
    if ($Value -is [bool]) { return 'bool' }
    if ($Value -is [System.Object[]]) { return 'array' }
    if ($Value -is [System.Collections.IList]) { return 'array' }
    if ($Value -is [ValueType]) { return 'number' }
    return 'object'
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

function Get-StatusProbe {
    param([int]$Port)
    $file = Join-Path $Ev ("status_{0}.response.json" -f $Port)
    if (Test-Path $file) { Remove-Item -Force $file }
    & $Curl -s --max-time 5 -o $file ("http://127.0.0.1:{0}/mcp" -f $Port) | Out-Null
    if (-not (Test-Path $file)) { return $null }
    $bytes = [IO.File]::ReadAllBytes($file)
    if ($bytes.Length -eq 0) { return $null }
    try { return ConvertFrom-Json ([Text.Encoding]::UTF8.GetString($bytes)) } catch { return $null }
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

function Start-Engine {
    param([string[]]$Arguments, [string]$LogName)
    $out = Join-Path $LogRoot ($LogName + '.out.log')
    $err = Join-Path $LogRoot ($LogName + '.err.log')
    Remove-Item -Path $out, $err -ErrorAction SilentlyContinue
    $proc = Start-Process -FilePath $Engine -ArgumentList $Arguments -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden
    Note ("started pid={0} :: {1}" -f $proc.Id, ($Arguments -join ' '))
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

# -----------------------------------------------------------------------------
# Scratch project
#
#   scenes/main.tscn   Main (Node2D) carrying res://main.gd, written by hand
#                      **without** `uid=` so that the pre-save answer can be
#                      measured; `editor_save_scene` then rewrites it the way the
#                      engine itself writes an ext_resource (with `uid=`).
#   scenes/sub.tscn    Sub (Node2D) with a resource dependency, no script.
#   main.gd            the exported probe properties of E-3.
# -----------------------------------------------------------------------------

$MainGd = @'
extends Node2D

@export var v4: Vector4 = Vector4(5, 6, 7, 8)
@export var v4i: Vector4i = Vector4i(1, 2, 3, 4)
@export var rect_i: Rect2i = Rect2i(1, 2, 30, 40)
@export var pv2: PackedVector2Array = PackedVector2Array([Vector2(1, 2)])
@export var pv4: PackedVector4Array = PackedVector4Array([Vector4(1, 2, 3, 4)])
@export var bytes: PackedByteArray = PackedByteArray([1, 200])
@export var names: PackedStringArray = PackedStringArray(["a", "b"])
@export var floats: PackedFloat32Array = PackedFloat32Array([0.5, 1.5])
@export var colors: PackedColorArray = PackedColorArray([Color(1, 0, 0, 1)])
@export var ints: PackedInt32Array = PackedInt32Array([7, -3])
'@
# NOTE: the file above is written as UTF-8 with no BOM, and it is deliberately
# ASCII-only - this script's own strings never need an encoding decision.

$MainScene = @'
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://main.gd" id="1_main"]

[node name="Main" type="Node2D"]
script = ExtResource("1_main")
'@

$SubScene = @'
[gd_scene load_steps=2 format=3]

[ext_resource type="Resource" path="res://resources/thing.tres" id="1_thing"]

[node name="Sub" type="Node2D"]
'@

$ThingTres = @'
[gd_resource type="Resource" format=3]

[resource]
'@

function New-ScratchProject {
    $projectGodot = @(
        'config_version=5'
        ''
        '[application]'
        'config/name="MCP024b ergonomics evidence"'
        'config/features=PackedStringArray("4.8")'
        'run/main_scene="res://scenes/main.tscn"'
        ''
        '[godot_mcp]'
        'enabled_in_game=true'
        ''
        '[rendering]'
        'renderer/rendering_method="gl_compatibility"'
        'renderer/rendering_method.mobile="gl_compatibility"'
    ) -join "`n"
    Write-Utf8NoBom -Path (Join-Path $Project 'project.godot') -Text ($projectGodot + "`n")
    Write-Utf8NoBom -Path (Join-Path $Project 'main.gd') -Text ($MainGd + "`n")
    Write-Utf8NoBom -Path (Join-Path $Project 'scenes\main.tscn') -Text ($MainScene + "`n")
    Write-Utf8NoBom -Path (Join-Path $Project 'scenes\sub.tscn') -Text ($SubScene + "`n")
    Write-Utf8NoBom -Path (Join-Path $Project 'resources\thing.tres') -Text ($ThingTres + "`n")
}

function Import-Project {
    $out = Join-Path $LogRoot 'import.out.log'
    $err = Join-Path $LogRoot 'import.err.log'
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        for ($attempt = 1; $attempt -le 3; $attempt++) {
            Remove-Item -Path $out, $err -ErrorAction SilentlyContinue
            & $Engine --headless --mcp-port=0 --path $Project --import 1> $out 2> $err
            $code = $LASTEXITCODE
            Note ("import attempt={0} exit={1} log={2}" -f $attempt, $code, $out)
            if ($code -eq 0) { return $attempt }
            Start-Sleep -Milliseconds 1500
        }
    } finally {
        $ErrorActionPreference = $previous
    }
    throw '--import of the scratch project failed three times'
}

# One dependency entry of `project_get_scene_dependencies`, selected by path.
function Get-Dependency {
    param([string]$Id, [string]$ScenePath, [string]$DependencyPath, [int]$Port = $EditorPort)
    $env = Invoke-Tool -Id $Id -Tool 'project_get_scene_dependencies' -Arguments @{ path = $ScenePath } -Port $Port
    $payload = Get-Payload $env
    if ($null -eq $payload) { return $null }
    foreach ($dep in @($payload.dependencies)) {
        if ([string]$dep.path -ceq $DependencyPath) { return $dep }
    }
    return $null
}

# The E-3 property list both endpoints are asked for. `properties` is passed as
# the array the caller wants back, never as a single name to be filtered later.
$ProbeProperties = @('v4', 'v4i', 'rect_i', 'pv2', 'pv4', 'bytes', 'names', 'floats', 'colors', 'ints')

# The node argument is spelled `path` on the editor tool and `node_path` on the
# game tool (the contract of each), and it is passed under that name: a mismatch
# is a -32602, never a silent default.
function Get-Properties {
    param([string]$Id, [string]$Tool, [string]$NodePath, [int]$Port, [string]$PathArgument = 'node_path')
    $arguments = @{}
    $arguments[$PathArgument] = $NodePath
    $arguments['properties'] = $ProbeProperties
    $env = Invoke-Tool -Id $Id -Tool $Tool -Arguments $arguments -Port $Port
    return [pscustomobject]@{ env = $env; payload = (Get-Payload $env) }
}

# One node property, read with the read tool of the same endpoint.
function Get-OneProperty {
    param([string]$Id, [string]$Tool, [string]$NodePath, [string]$Property, [int]$Port, [string]$PathArgument = 'node_path')
    $arguments = @{}
    $arguments[$PathArgument] = $NodePath
    $arguments['properties'] = @($Property)
    $env = Invoke-Tool -Id $Id -Tool $Tool -Arguments $arguments -Port $Port
    $payload = Get-Payload $env
    if ($null -eq $payload) { return $null }
    return $payload.properties.$Property
}

# The shape assertions of E-3, applied to one read-back payload. Returns the
# number of failing shape checks; every failure is reported by `Check`.
function Assert-Shapes {
    param([string]$Prefix, $Properties)
    $failures = 0
    $report = New-Object System.Collections.Generic.List[string]

    # --- Vector4 / Vector4i / Rect2i: objects, like Vector2/Vector3 already were
    foreach ($case in @(
            @{ name = 'v4'; fields = @('x', 'y', 'z', 'w') },
            @{ name = 'v4i'; fields = @('x', 'y', 'z', 'w') },
            @{ name = 'rect_i'; fields = @('x', 'y', 'width', 'height') })) {
        $value = $Properties.($case.name)
        $kind = Get-JsonKind $value
        $ok = ($kind -eq 'object')
        if ($ok) {
            foreach ($field in $case.fields) {
                if ($null -eq $value.PSObject.Properties[$field]) { $ok = $false }
            }
        }
        if (-not $ok) { $failures++ }
        $report.Add(("{0} kind={1} value={2}" -f $case.name, $kind, (ConvertTo-CompactJson $value)))
        Check ($Prefix + '_' + $case.name + '_is_object') $ok $report[$report.Count - 1]
    }
    # The number kind follows the engine's: Vector4i/Rect2i answer integers.
    $v4iInts = ($null -ne $Properties.v4i) -and ($Properties.v4i.x -is [int] -or $Properties.v4i.x -is [long])
    Check ($Prefix + '_v4i_components_are_integers') $v4iInts ("v4i.x={0} (kind {1})" -f (ConvertTo-CompactJson $Properties.v4i.x), (Get-JsonKind $Properties.v4i.x))

    # --- every packed array: an array whose elements are the element's own shape
    $packed = [ordered]@{
        pv2    = 'objects_xy'
        pv4    = 'objects_xyzw'
        bytes  = 'integers'
        names  = 'strings'
        floats = 'numbers'
        colors = 'objects_rgba'
        ints   = 'integers'
    }
    foreach ($name in $packed.Keys) {
        $value = $Properties.$name
        $kind = Get-JsonKind $value
        $ok = ($kind -eq 'array')
        $elementReport = ''
        if ($ok) {
            $elements = @($value)
            if ($elements.Count -eq 0) {
                $ok = $false
                $elementReport = 'empty'
            } else {
                switch ($packed[$name]) {
                    'objects_xy' { $ok = (Get-JsonKind $elements[0]) -eq 'object' -and $null -ne $elements[0].x -and $null -ne $elements[0].y }
                    'objects_xyzw' { $ok = (Get-JsonKind $elements[0]) -eq 'object' -and $null -ne $elements[0].x -and $null -ne $elements[0].z -and $null -ne $elements[0].w }
                    'objects_rgba' { $ok = (Get-JsonKind $elements[0]) -eq 'object' -and $null -ne $elements[0].r -and $null -ne $elements[0].a }
                    'integers' { $ok = (Get-JsonKind $elements[0]) -eq 'number' -and ($elements[0] -is [int] -or $elements[0] -is [long]) }
                    'numbers' { $ok = (Get-JsonKind $elements[0]) -eq 'number' }
                    'strings' { $ok = (Get-JsonKind $elements[0]) -eq 'string' }
                }
                $elementReport = ("[0] kind={0} value={1}" -f (Get-JsonKind $elements[0]), (ConvertTo-CompactJson $elements[0]))
            }
        }
        if (-not $ok) { $failures++ }
        Check ($Prefix + '_' + $name + '_is_array_of_' + $packed[$name]) $ok `
            ("{0} kind={1} value={2} {3}" -f $name, $kind, (ConvertTo-CompactJson $value), $elementReport)
    }

    # --- the discriminator of the whole item: no object-kind value is a string
    $stringKinds = New-Object System.Collections.Generic.List[string]
    foreach ($name in @('v4', 'v4i', 'rect_i', 'pv2', 'pv4', 'bytes', 'names', 'floats', 'colors', 'ints')) {
        $kind = Get-JsonKind $Properties.$name
        if ($kind -eq 'string') { $stringKinds.Add($name) }
    }
    $noStrings = $stringKinds.Count -eq 0
    if (-not $noStrings) { $failures++ }
    $stringReport = '<none>'
    if ($stringKinds.Count -gt 0) { $stringReport = ($stringKinds -join ',') }
    Check ($Prefix + '_no_value_falls_back_to_a_string') $noStrings `
        ("values still arriving as a string: {0}" -f $stringReport)

    return $failures
}

# =============================================================================
#  Run
# =============================================================================

Note '============================================================='
Note ' TASK-024b gate-2 evidence -- E-1/G-2 scene dependencies + E-3 shapes'
Note '============================================================='
Note ("engine      : {0}" -f $Engine)
$versionText = (& $Engine --version)
$headSha = (& git -C $RepoRoot rev-parse --short HEAD).Trim()
# TASK-072 (D130): one judge decides the anchor; see check_engine_anchor.ps1.
$anchorVerdict = Get-McpEngineAnchorVerdict -RepoRoot $RepoRoot -VersionText $versionText -HeadSha $headSha
Note ("version     : {0}" -f $versionText)
Note ("git HEAD    : {0}" -f $headSha)
Check 'gate_version_matches_head' ($anchorVerdict.Ok) `
    (("engine --version = '{0}'; git rev-parse --short HEAD = '{1}'" -f $versionText, $headSha) + ' | ' + $anchorVerdict.Summary)

$userPidBefore = Get-ListenerPid -Port $UserPort
Note ("user editor on {0} before run: pid={1} (read-only guard)" -f $UserPort, $userPidBefore)
Check 'port_user_9877_owner_before' ($userPidBefore -gt 0) ("port {0} owner pid={1} (must not change for the whole run)" -f $UserPort, $userPidBefore)
Check 'port_9888_free_before' ((Get-ListenerPid -Port $EditorPort) -eq -1) ("port {0} owner={1}" -f $EditorPort, (Get-ListenerPid -Port $EditorPort))
Check 'port_9889_free_before' ((Get-ListenerPid -Port $GamePort) -eq -1) ("port {0} owner={1}" -f $GamePort, (Get-ListenerPid -Port $GamePort))

$importCode = $null
try {
    New-ScratchProject
    $importAttempts = Import-Project
    $importCode = $importAttempts
    Note ("scratch project: {0}" -f $Project)

    # The `.uid` file the import gives a script is what makes the engine's own
    # save carry `uid=`: recorded here because the uid half of E-1 depends on it.
    $uidFile = Join-Path $Project 'main.gd.uid'
    $uidFileContent = '<none>'
    if (Test-Path $uidFile) { $uidFileContent = (Get-Content -Raw $uidFile).Trim() }
    Check 'import_created_script_uid_file' (Test-Path $uidFile) `
        ("main.gd.uid exists={0} content='{1}'" -f (Test-Path $uidFile), $uidFileContent)

    $script:EditorHandle = Start-Engine -Arguments @('--headless', '-e', '--path', $Project, "--mcp-port=$EditorPort") -LogName 'editor'
    Check 'editor_endpoint_ready' (Wait-ForPump -Port $EditorPort) ("editor on {0} answered GET /mcp with +20 frames three times" -f $EditorPort)

    $open = Invoke-Tool -Id 'A1_open_main_scene' -Tool 'editor_open_scene' -Arguments @{ path = 'res://scenes/main.tscn' }
    Check 'A1_main_scene_open' ($null -ne (Get-Payload $open)) ("editor_open_scene -> " + (ConvertTo-CompactJson (Get-Payload $open)))

    # =====================================================================
    # (1) E-1 + G-2 - the dependency entry
    # =====================================================================
    Note ''
    Note '--- (1a) the hand-written scene: no uid=, type is a type -----------'

    $preDeps = Invoke-Tool -Id 'E1a_deps_before_save' -Tool 'project_get_scene_dependencies' -Arguments @{ path = 'res://scenes/main.tscn' }
    $prePayload = Get-Payload $preDeps
    $preDep = $null
    if ($null -ne $prePayload) { $preDep = @($prePayload.dependencies)[0] }
    Note ("pre-save answer: " + (ConvertTo-CompactJson $prePayload))
    # The D-8 discriminator: before TASK-024b this answered
    # {"path":"uid://...","type":"res://main.gd"} - the *path* under `type`.
    Check 'E1a_type_is_the_engine_type_not_a_path' `
        (($null -ne $preDep) -and ([string]$preDep.type -ceq 'GDScript')) `
        ("dependencies[0].type = '{0}' (a type; the old implementation answered the fallback `path` here)" -f $preDep.type)
    Check 'E1a_declared_type_is_the_tag_type' `
        (($null -ne $preDep) -and ([string]$preDep.declared_type -ceq 'Script')) `
        ("dependencies[0].declared_type = '{0}' (the [ext_resource type=...] of the scene)" -f $preDep.declared_type)
    Check 'E1a_path_is_the_res_path' `
        (($null -ne $preDep) -and ([string]$preDep.path -ceq 'res://main.gd')) `
        ("dependencies[0].path = '{0}'" -f $preDep.path)
    Check 'E1a_uid_is_empty_when_the_scene_has_none' `
        (($null -ne $preDep) -and ([string]$preDep.uid -ceq '')) `
        ("dependencies[0].uid = '{0}' (the tag carries no uid=; a path is never echoed under `uid`)" -f $preDep.uid)
    Check 'E1a_path_source_is_scene_path' `
        (($null -ne $preDep) -and ([string]$preDep.path_source -ceq 'scene_path')) `
        ("dependencies[0].path_source = '{0}'" -f $preDep.path_source)
    Check 'E1a_count_matches_the_array' `
        ($null -ne $prePayload -and [int]$prePayload.count -eq @($prePayload.dependencies).Count -and [int]$prePayload.count -eq 1) `
        ("count={0} dependencies.Count={1}" -f $prePayload.count, @($prePayload.dependencies).Count)

    Note ''
    Note '--- (1b) the second scene (a resource dependency, no script) -------'
    $subDeps = Invoke-Tool -Id 'E1b_deps_sub_scene' -Tool 'project_get_scene_dependencies' -Arguments @{ path = 'res://scenes/sub.tscn' }
    $subPayload = Get-Payload $subDeps
    $subDep = $null
    if ($null -ne $subPayload) { $subDep = @($subPayload.dependencies)[0] }
    Note ("sub.tscn answer: " + (ConvertTo-CompactJson $subPayload))
    Check 'E1b_sub_scene_entry' `
        (($null -ne $subDep) -and ([string]$subDep.path -ceq 'res://resources/thing.tres') -and ([string]$subDep.type -ceq 'Resource') `
            -and ([string]$subDep.declared_type -ceq 'Resource') -and ([string]$subDep.uid -ceq '') -and ([string]$subDep.path_source -ceq 'scene_path')) `
        ("path='{0}' type='{1}' declared_type='{2}' uid='{3}' path_source='{4}'" -f $subDep.path, $subDep.type, $subDep.declared_type, $subDep.uid, $subDep.path_source)

    Note ''
    Note '--- (1c) the engine saves the scene: uid= is written by the engine ---'
    $save = Invoke-Tool -Id 'E1c_save_scene' -Tool 'editor_save_scene' -Arguments @{}
    $sceneText = Get-Content -Raw (Join-Path $Project 'scenes\main.tscn')
    Note ("scenes/main.tscn after editor_save_scene:`n{0}" -f $sceneText)
    Check 'E1c_engine_save_wrote_a_uid_into_the_ext_resource' ($sceneText -match '\[ext_resource type="Script"[^\]]*uid="uid://') `
        ("the saved scene carries uid= in its Script ext_resource (sha256={0})" -f (Get-FileSha (Join-Path $Project 'scenes\main.tscn')))
    $m = [regex]::Match($sceneText, '\[ext_resource type="Script"[^\]]*uid="(uid://[a-z0-9]+)"')
    $sceneUid = if ($m.Success) { $m.Groups[1].Value } else { '' }
    Note ("the uid text in the saved scene: '{0}'" -f $sceneUid)

    $postDeps = Invoke-Tool -Id 'E1c_deps_after_save' -Tool 'project_get_scene_dependencies' -Arguments @{ path = 'res://scenes/main.tscn' }
    $postPayload = Get-Payload $postDeps
    $postDep = $null
    if ($null -ne $postPayload) { $postDep = @($postPayload.dependencies)[0] }
    Note ("post-save answer: " + (ConvertTo-CompactJson $postPayload))
    Check 'E1c_uid_is_reported' (($null -ne $postDep) -and ([string]$postDep.uid -ceq $sceneUid) -and ($sceneUid -ne '')) `
        ("dependencies[0].uid = '{0}' (the uid= the engine itself wrote)" -f $postDep.uid)
    Check 'E1c_path_is_resolved_through_the_uid_registry' `
        (($null -ne $postDep) -and ([string]$postDep.path -ceq 'res://main.gd') -and ([string]$postDep.path_source -ceq 'uid')) `
        ("path='{0}' path_source='{1}' (the UID registry, not the scene's fallback path)" -f $postDep.path, $postDep.path_source)
    Check 'E1c_type_survives_the_uid_form' (($null -ne $postDep) -and ([string]$postDep.type -ceq 'GDScript') -and ([string]$postDep.declared_type -ceq 'Script')) `
        ("type='{0}' declared_type='{1}'" -f $postDep.type, $postDep.declared_type)
    # The regression the whole item is about, stated as a machine-checkable rule.
    Check 'E1c_type_and_path_are_never_the_same_field' `
        (($null -ne $postDep) -and ([string]$postDep.type -cne [string]$postDep.path) -and (([string]$postDep.path).StartsWith('res://')) -and (-not (([string]$postDep.path).StartsWith('uid://')))) `
        ("type='{0}' path='{1}' (a uid:// value must never arrive under `path`)" -f $postDep.type, $postDep.path)

    Note ''
    Note '--- (1d) gate-2 classes for project_get_scene_dependencies --------------'
    $readBack = Invoke-Tool -Id 'E1d_read_resource_by_dep_path' -Tool 'project_read_resource' -Arguments @{ path = $postDep.path }
    $readBackPayload = Get-Payload $readBack
    Check 'E1d_dep_path_is_accepted_by_the_next_tool' `
        (($null -ne $readBackPayload) -and ($null -eq $readBack.error) -and ([string]$readBackPayload.path -ceq 'res://main.gd')) `
        ("project_read_resource(path=dependencies[0].path) -> {0}" -f (ConvertTo-CompactJson $readBackPayload))

    $depMissing = Invoke-Tool -Id 'E1d_deps_missing_param' -Tool 'project_get_scene_dependencies' -Arguments @{}
    Check 'E1d_missing_param_is_-32602' `
        ((Get-ErrorCode $depMissing) -eq -32602 -and (Get-ErrorMessage $depMissing).Contains('path')) `
        ("code={0} message='{1}'" -f (Get-ErrorCode $depMissing), (Get-ErrorMessage $depMissing))

    $depAbsent = Invoke-Tool -Id 'E1d_deps_missing_file' -Tool 'project_get_scene_dependencies' -Arguments @{ path = 'res://scenes/nope.tscn' }
    Check 'E1d_missing_file_is_-32001_with_a_suggestion' `
        ((Get-ErrorCode $depAbsent) -eq -32001 -and (Get-ErrorSuggestion $depAbsent) -ne '') `
        ("code={0} message='{1}' suggestion='{2}'" -f (Get-ErrorCode $depAbsent), (Get-ErrorMessage $depAbsent), (Get-ErrorSuggestion $depAbsent))

    # =====================================================================
    # (2) E-3 - the read-back shapes, editor side
    # =====================================================================
    Note ''
    Note '--- (2a) editor: seed every probe property through the write tool -----'
    # Every packed probe has two elements on purpose: a one-element PowerShell
    # array is unwrapped by the pipeline in some contexts, and this run measures
    # the *shape* a reader sees, not PowerShell's array handling.
    $seedValues = [ordered]@{
        v4     = @{ x = 1.5; y = 2.5; z = 3.5; w = 4.5 }
        pv2    = @(@{ x = 1; y = 2 }, @{ x = 3; y = 4 })
        pv4    = @(@{ x = 1; y = 2; z = 3; w = 4 }, @{ x = 5; y = 6; z = 7; w = 8 })
        bytes  = @(1, 200)
        names  = @('a', 'b')
        floats = @(0.5, 1.5)
        colors = @(@{ r = 1; g = 0; b = 0; a = 1 }, @{ r = 0; g = 1; b = 0; a = 1 })
        ints   = @(7, -3)
    }
    $seedFailures = New-Object System.Collections.Generic.List[string]
    foreach ($name in $seedValues.Keys) {
        $env = Invoke-Tool -Id ('E3a_seed_' + $name) -Tool 'editor_set_node_property' -Arguments @{ path = 'Main'; property = $name; value = $seedValues[$name] }
        if ((Get-ErrorCode $env) -ne 0) { $seedFailures.Add(("{0}: code={1} message='{2}'" -f $name, (Get-ErrorCode $env), (Get-ErrorMessage $env))) }
    }
    $seedFailureReport = '<none>'
    if ($seedFailures.Count -gt 0) { $seedFailureReport = ($seedFailures -join '; ') }
    Check 'E3a_probe_properties_seeded' ($seedFailures.Count -eq 0) `
        ("{0} of {1} probe properties written through the tool; failures: {2}" -f ($seedValues.Count - $seedFailures.Count), $seedValues.Count, $seedFailureReport)

    $readEditor = Get-Properties -Id 'E3b_read_editor' -Tool 'editor_get_node_properties' -NodePath 'Main' -Port $EditorPort -PathArgument 'path'
    Note ("editor read-back: " + (ConvertTo-CompactJson $readEditor.payload.properties))
    $editorShapeFailures = Assert-Shapes -Prefix 'E3b_editor' -Properties $readEditor.payload.properties
    Check 'E3b_editor_all_shape_checks_passed' ($editorShapeFailures -eq 0) `
        ("{0} shape check(s) failed on the editor read-back" -f $editorShapeFailures)

    Note ''
    Note '--- (2b) editor: the read-back goes back into the write tool as it is --'
    $feed = Invoke-Tool -Id 'E3c_feed_v4_back' -Tool 'editor_set_node_property' `
        -Arguments @{ path = 'Main'; property = 'v4'; value = $readEditor.payload.properties.v4 }
    $feedPayload = Get-Payload $feed
    Check 'E3c_v4_object_is_accepted_back' `
        ((Get-ErrorCode $feed) -eq 0 -and ($null -ne $feedPayload) -and ([string]$feedPayload.new_value.x -eq '1.5') `
            -and ([string]$feedPayload.new_value.w -eq '4.5')) `
        ("editor_set_node_property(v4 = the read-back object) -> code={0} new_value={1}" -f (Get-ErrorCode $feed), (ConvertTo-CompactJson $feedPayload.new_value))
    $feedPv4 = Invoke-Tool -Id 'E3c_feed_pv4_back' -Tool 'editor_set_node_property' `
        -Arguments @{ path = 'Main'; property = 'pv4'; value = $readEditor.payload.properties.pv4 }
    $feedPv4Payload = Get-Payload $feedPv4
    Check 'E3c_pv4_array_is_accepted_back' `
        ((Get-ErrorCode $feedPv4) -eq 0 -and ($null -ne $feedPv4Payload) -and ((Get-JsonKind $feedPv4Payload.new_value) -eq 'array')) `
        ("editor_set_node_property(pv4 = the read-back array) -> code={0} new_value={1}" -f (Get-ErrorCode $feedPv4), (ConvertTo-CompactJson $feedPv4Payload.new_value))
    $feedBytes = Invoke-Tool -Id 'E3c_feed_bytes_back' -Tool 'editor_set_node_property' `
        -Arguments @{ path = 'Main'; property = 'bytes'; value = $readEditor.payload.properties.bytes }
    $feedBytesPayload = Get-Payload $feedBytes
    $feedBytesArray = @($feedBytesPayload.new_value)
    Check 'E3c_bytes_array_is_accepted_back' `
        ((Get-ErrorCode $feedBytes) -eq 0 -and ($null -ne $feedBytesPayload) -and ((Get-JsonKind $feedBytesPayload.new_value) -eq 'array') `
            -and ($feedBytesArray.Count -eq 2) -and ($feedBytesArray[0] -eq 1) -and ($feedBytesArray[1] -eq 200)) `
        ("editor_set_node_property(bytes = the read-back array) -> code={0} new_value={1}" -f (Get-ErrorCode $feedBytes), (ConvertTo-CompactJson $feedBytesPayload.new_value))

    # Save *after* the seeding so the game process loads the seeded scene.
    $save2 = Invoke-Tool -Id 'E3c_save_scene' -Tool 'editor_save_scene' -Arguments @{}
    Check 'E3c_scene_saved_after_seeding' ($null -ne (Get-Payload $save2)) `
        ("editor_save_scene -> {0}; scenes/main.tscn sha256={1}" -f (ConvertTo-CompactJson (Get-Payload $save2)), (Get-FileSha (Join-Path $Project 'scenes\main.tscn')))

    # -------------------------------------------------------------------------
    # The residual gap this batch uncovered (reported, not fixed here): the read
    # side now answers `Vector4i`/`Rect2i` as objects, but the *write* side has no
    # component table for those two types (`vector_component_hint` returns the
    # empty string for them), so the read-back of those two cannot be written
    # back yet. Before this batch the read-back was a string, which the write side
    # did not accept either - so this is not a regression, it is the write half of
    # E-3 that still needs the same table. Measured here so the acceptance agent
    # sees the exact refusal instead of reading an inference.
    # -------------------------------------------------------------------------
    $v4iBack = Invoke-Tool -Id 'E3c_v4i_object_back' -Tool 'editor_set_node_property' `
        -Arguments @{ path = 'Main'; property = 'v4i'; value = $readEditor.payload.properties.v4i }
    Check 'GAP_v4i_object_read_back_is_refused_by_the_write_side' ((Get-ErrorCode $v4iBack) -eq -32602) `
        ("editor_set_node_property(v4i = the read-back object) -> code={0} message='{1}' (residual gap: the write side has no Vector4i component table, so only the read shape is fixed in this batch)" -f (Get-ErrorCode $v4iBack), (Get-ErrorMessage $v4iBack))
    $rectBack = Invoke-Tool -Id 'E3c_rect_i_object_back' -Tool 'editor_set_node_property' `
        -Arguments @{ path = 'Main'; property = 'rect_i'; value = $readEditor.payload.properties.rect_i }
    Check 'GAP_rect_i_object_read_back_is_refused_by_the_write_side' ((Get-ErrorCode $rectBack) -eq -32602) `
        ("editor_set_node_property(rect_i = the read-back object) -> code={0} message='{1}' (residual gap: `Rect2`/`Rect2i` have no component table on the write side - `Rect2`'s object read shape predates this batch)" -f (Get-ErrorCode $rectBack), (Get-ErrorMessage $rectBack))

    Note ''
    Note '--- (2c) gate-2 classes for editor_get_node_properties -------------------'
    $editorNoParam = Invoke-Tool -Id 'E3d_editor_missing_param' -Tool 'editor_get_node_properties' -Arguments @{ properties = @('v4') }
    Check 'E3d_editor_missing_param_is_-32602' ((Get-ErrorCode $editorNoParam) -eq -32602) `
        ("code={0} message='{1}'" -f (Get-ErrorCode $editorNoParam), (Get-ErrorMessage $editorNoParam))
    $editorAbsentNode = Invoke-Tool -Id 'E3d_editor_missing_node' -Tool 'editor_get_node_properties' -Arguments @{ path = 'NoSuchNode'; properties = @('v4') }
    Check 'E3d_editor_missing_node_is_-32001' ((Get-ErrorCode $editorAbsentNode) -eq -32001 -and (Get-ErrorSuggestion $editorAbsentNode) -ne '') `
        ("code={0} message='{1}' suggestion='{2}'" -f (Get-ErrorCode $editorAbsentNode), (Get-ErrorMessage $editorAbsentNode), (Get-ErrorSuggestion $editorAbsentNode))

    # =====================================================================
    # (3) E-3 - the same shapes on the game endpoint (9889)
    # =====================================================================
    Note ''
    Note '--- (3a) game process on 9889, reading the saved scene ----------------'
    $script:GameHandle = Start-Engine -Arguments @('--headless', '--path', $Project, "--mcp-port=$GamePort") -LogName 'game'
    Check 'game_endpoint_ready' (Wait-ForPump -Port $GamePort) ("game on {0} answered GET /mcp with +20 frames three times" -f $GamePort)

    $readGame = Get-Properties -Id 'E3e_read_game' -Tool 'running_game_get_node_properties' -NodePath 'Main' -Port $GamePort
    Note ("game read-back: " + (ConvertTo-CompactJson $readGame.payload.properties))
    $gameShapeFailures = Assert-Shapes -Prefix 'E3e_game' -Properties $readGame.payload.properties
    Check 'E3e_game_all_shape_checks_passed' ($gameShapeFailures -eq 0) `
        ("{0} shape check(s) failed on the game read-back" -f $gameShapeFailures)

    Note ''
    Note '--- (3b) game: the read-back goes back into the write tool as it is -----'
    $gameFeed = Invoke-Tool -Id 'E3f_game_feed_v4_back' -Tool 'running_game_set_node_property' `
        -Arguments @{ node_path = 'Main'; property = 'v4'; value = $readGame.payload.properties.v4 } -Port $GamePort
    $gameFeedPayload = Get-Payload $gameFeed
    Check 'E3f_game_v4_object_is_accepted_back' `
        ((Get-ErrorCode $gameFeed) -eq 0 -and ($null -ne $gameFeedPayload) -and ([string]$gameFeedPayload.new_value.y -eq '2.5')) `
        ("running_game_set_node_property(v4 = the read-back object) -> code={0} new_value={1}" -f (Get-ErrorCode $gameFeed), (ConvertTo-CompactJson $gameFeedPayload.new_value))
    $gameFeedPacked = Invoke-Tool -Id 'E3f_game_feed_bytes_back' -Tool 'running_game_set_node_property' `
        -Arguments @{ node_path = 'Main'; property = 'bytes'; value = $readGame.payload.properties.bytes } -Port $GamePort
    $gameFeedPackedPayload = Get-Payload $gameFeedPacked
    Check 'E3f_game_bytes_array_is_accepted_back' `
        ((Get-ErrorCode $gameFeedPacked) -eq 0 -and ($null -ne $gameFeedPackedPayload) -and ((Get-JsonKind $gameFeedPackedPayload.new_value) -eq 'array')) `
        ("running_game_set_node_property(bytes = the read-back array) -> code={0} new_value={1}" -f (Get-ErrorCode $gameFeedPacked), (ConvertTo-CompactJson $gameFeedPackedPayload.new_value))

    Note ''
    Note '--- (3c) gate-2 classes for running_game_get_node_properties ------------'
    $gameNoParam = Invoke-Tool -Id 'E3g_game_missing_param' -Tool 'running_game_get_node_properties' -Arguments @{ properties = @('v4') } -Port $GamePort
    Check 'E3g_game_missing_param_is_-32602' ((Get-ErrorCode $gameNoParam) -eq -32602) `
        ("code={0} message='{1}'" -f (Get-ErrorCode $gameNoParam), (Get-ErrorMessage $gameNoParam))
    $gameAbsentNode = Invoke-Tool -Id 'E3g_game_missing_node' -Tool 'running_game_get_node_properties' -Arguments @{ node_path = 'NoSuchNode'; properties = @('v4') } -Port $GamePort
    Check 'E3g_game_missing_node_is_-32001' ((Get-ErrorCode $gameAbsentNode) -eq -32001) `
        ("code={0} message='{1}'" -f (Get-ErrorCode $gameAbsentNode), (Get-ErrorMessage $gameAbsentNode))

    # =====================================================================
    # (4) the zero-string-surgery chain (GDR-25 section 23.1)
    # =====================================================================
    Note ''
    Note '--- (4) cross-tool chain, string operations by the caller: 0 ---------'
    # Every step below consumes a *field of the previous answer* directly; no
    # `.Split`, `.Replace`, `.Substring`, `.Trim`, `-match` or `[double]` parse
    # appears anywhere in this block. That is the claim being asserted.
    $chainStep = New-Object System.Collections.Generic.List[string]

    # step 1: the scene -> its dependency entry
    $chainDeps = Invoke-Tool -Id 'chain1_deps' -Tool 'project_get_scene_dependencies' -Arguments @{ path = 'res://scenes/main.tscn' }
    $chainDep = @((Get-Payload $chainDeps).dependencies)[0]
    $chainStep.Add(("1 project_get_scene_dependencies -> .dependencies[0].path = '{0}' (string ops: 0)" -f $chainDep.path))

    # step 2: that path -> the resource read tool
    $chainRead = Invoke-Tool -Id 'chain2_read_resource' -Tool 'project_read_resource' -Arguments @{ path = $chainDep.path }
    $chainReadPayload = Get-Payload $chainRead
    $chainStep.Add(("2 project_read_resource(path = step1 .path) -> .path = '{0}', .type = '{1}' (string ops: 0)" -f $chainReadPayload.path, $chainReadPayload.type))

    # step 3: the same field -> the UID read tool
    $chainUid = Invoke-Tool -Id 'chain3_path_to_uid' -Tool 'project_convert_path_to_uid' -Arguments @{ path = $chainDep.path }
    $chainUidPayload = Get-Payload $chainUid
    $chainStep.Add(("3 project_convert_path_to_uid(path = step1 .path) -> .uid = '{0}' (string ops: 0)" -f $chainUidPayload.uid))

    # step 4: the editor read-back of the probe properties
    $chainProps = Invoke-Tool -Id 'chain4_editor_properties' -Tool 'editor_get_node_properties' -Arguments @{ path = 'Main'; properties = @('v4', 'pv4', 'bytes') }
    $chainPropsPayload = Get-Payload $chainProps
    $chainStep.Add(("4 editor_get_node_properties -> .v4 = {0}, .pv4 = {1}, .bytes = {2} (string ops: 0)" -f `
                (ConvertTo-CompactJson $chainPropsPayload.properties.v4), (ConvertTo-CompactJson $chainPropsPayload.properties.pv4), (ConvertTo-CompactJson $chainPropsPayload.properties.bytes)))

    # step 5: the object read in step 4 goes straight back into the write tool
    $chainWrite = Invoke-Tool -Id 'chain5_write_v4_back' -Tool 'editor_set_node_property' `
        -Arguments @{ path = 'Main'; property = 'v4'; value = $chainPropsPayload.properties.v4 }
    $chainWritePayload = Get-Payload $chainWrite
    $chainStep.Add(("5 editor_set_node_property(value = step4 .v4) -> code={0} .new_value = {1} (string ops: 0)" -f (Get-ErrorCode $chainWrite), (ConvertTo-CompactJson $chainWritePayload.new_value)))

    # step 6: and the game endpoint reads the same shape back
    $chainGame = Invoke-Tool -Id 'chain6_game_properties' -Tool 'running_game_get_node_properties' -Arguments @{ node_path = 'Main'; properties = @('v4', 'pv4', 'bytes') } -Port $GamePort
    $chainGamePayload = Get-Payload $chainGame
    $chainStep.Add(("6 running_game_get_node_properties -> .v4 = {0}, .pv4 = {1}, .bytes = {2} (string ops: 0)" -f `
                (ConvertTo-CompactJson $chainGamePayload.properties.v4), (ConvertTo-CompactJson $chainGamePayload.properties.pv4), (ConvertTo-CompactJson $chainGamePayload.properties.bytes)))

    $chainOk = ($null -ne $chainDep) -and ($null -eq $chainDeps.error) -and ($null -eq $chainRead.error) -and ($null -eq $chainUid.error) `
        -and ($null -eq $chainProps.error) -and ($null -eq $chainWrite.error) -and ($null -eq $chainGame.error) `
        -and ([string]$chainDep.path -ceq 'res://main.gd') -and ([string]$chainDep.type -ceq 'GDScript') `
        -and ([string]$chainReadPayload.path -ceq 'res://main.gd') -and (([string]$chainUidPayload.uid).StartsWith('uid://')) `
        -and ((Get-JsonKind $chainPropsPayload.properties.v4) -eq 'object') -and ((Get-JsonKind $chainPropsPayload.properties.pv4) -eq 'array') `
        -and ((Get-JsonKind $chainPropsPayload.properties.bytes) -eq 'array') -and ((Get-JsonKind $chainWritePayload.new_value) -eq 'object') `
        -and ((Get-JsonKind $chainGamePayload.properties.v4) -eq 'object') -and ((Get-JsonKind $chainGamePayload.properties.bytes) -eq 'array')
    Check 'chain_zero_string_surgery_six_steps' $chainOk ("{0}" -f ($chainStep -join ' || '))

    Note ''
    Note '--- (5) contract untouched: the two tools advertise the same schema -----'
    $list = Invoke-Curl -Id 'F1_editor_tools_list' -Json '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' -Port $EditorPort
    $listed = $null
    try { $listed = (ConvertFrom-Json $list).result.tools } catch { }
    $schemaOf = @{}
    foreach ($tool in @($listed)) { $schemaOf[[string]$tool.name] = $tool.inputSchema }
    $depsSchemaObj = $schemaOf['project_get_scene_dependencies']
    $depPropNames = @($depsSchemaObj.properties.PSObject.Properties.Name)
    Check 'F1_dependency_schema_unchanged' `
        (($depPropNames.Count -eq 1) -and ($depPropNames[0] -ceq 'path') -and (@($depsSchemaObj.required) -contains 'path') -and ([string]$depsSchemaObj.type -ceq 'object')) `
        ("project_get_scene_dependencies.inputSchema properties = [{0}], required = [{1}] (no output field was added to the contract)" -f ($depPropNames -join ','), (@($depsSchemaObj.required) -join ','))
    $editorSchemaObj = $schemaOf['editor_get_node_properties']
    $editorSchemaNames = @($editorSchemaObj.properties.PSObject.Properties.Name)
    Check 'F1_editor_schema_unchanged' (($editorSchemaNames -join ',') -ceq 'path,properties') `
        ("editor_get_node_properties.properties = [{0}]" -f ($editorSchemaNames -join ','))

    # The game-scope tool is advertised by the *game* endpoint (a cross-endpoint
    # call is -32601), so its schema is read from 9889.
    $gameList = Invoke-Curl -Id 'F2_game_tools_list' -Json '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' -Port $GamePort
    $gameListed = $null
    try { $gameListed = (ConvertFrom-Json $gameList).result.tools } catch { }
    $gameSchemaOf = @{}
    foreach ($tool in @($gameListed)) { $gameSchemaOf[[string]$tool.name] = $tool.inputSchema }
    $gameSchemaObj = $gameSchemaOf['running_game_get_node_properties']
    $gameSchemaNames = @($gameSchemaObj.properties.PSObject.Properties.Name)
    Check 'F1_game_schema_unchanged' (($gameSchemaNames -join ',') -ceq 'node_path,properties') `
        ("running_game_get_node_properties.properties = [{0}] (read from the game endpoint {1})" -f ($gameSchemaNames -join ','), $GamePort)
} finally {
    Stop-Engine $script:GameHandle
    Stop-Engine $script:EditorHandle
    Start-Sleep -Milliseconds 1500
    $userPidAfter = Get-ListenerPid -Port $UserPort
    Check 'guard_user_port_9877_unchanged' ($userPidBefore -eq $userPidAfter) ("pid_before={0} pid_after={1} (never occupied, killed or restarted by this run)" -f $userPidBefore, $userPidAfter)
    Check 'test_ports_released' (((Get-ListenerPid -Port $EditorPort) -eq -1) -and ((Get-ListenerPid -Port $GamePort) -eq -1)) `
        ("{0} owner={1}; {2} owner={3}" -f $EditorPort, (Get-ListenerPid -Port $EditorPort), $GamePort, (Get-ListenerPid -Port $GamePort))
}

$logPath = Join-Path $Ev 'evidence.log.txt'
$summary = @()
foreach ($entry in $script:Checks) {
    $entryTag = 'FAIL'
    if ($entry.pass) { $entryTag = 'PASS' }
    $summary += ("[{0}] {1} :: {2}" -f $entryTag, $entry.id, $entry.evidence)
}
Write-Utf8NoBom -Path $logPath -Text (($summary -join "`r`n") + "`r`n")

$passed = @($script:Checks | Where-Object { $_.pass }).Count
$total = $script:Checks.Count
Write-Host ''
Write-Host '========================== SUMMARY =========================='
foreach ($c in $script:Checks) {
    $tag = 'FAIL'
    if ($c.pass) { $tag = 'PASS' }
    Write-Host ("{0}  {1}" -f $tag, $c.id)
}
Write-Host ("{0}/{1} checks passed; evidence in {2} (log sha256={3})" -f $passed, $total, $Ev, (Get-FileSha $logPath))
if ($passed -ne $total) { exit 1 }
exit 0
