# =============================================================================
#  mcp025_e3_writeside_evidence.ps1 -- live evidence for TASK-025 item (2)
#
#  E-3 write half: **every shape the module reads back must be writable back**.
#
#  TASK-024b unified the read side of `serialize_variant` (one shape per kind:
#  a vector/colour/rect names its components in an object, a packed array
#  answers an array of the element's own shape) and reported a residual gap it
#  did not have scope to fix: the write side had no component table for
#  `Vector4i`, `Rect2` or `Rect2i`, so a read-back object for those types was
#  answered with `-32602` by `Variant::can_convert(DICTIONARY, <type>)` being
#  false. That is GDR-25 section 23.1 rule 1 failing inside the module: an
#  identifier the module returned could not be fed back without reshaping it.
#
#  This script measures the whole read-back matrix - the six vector types,
#  `Color`, the two rects and all eleven packed arrays - on **both** endpoints
#  (editor 9888 / game 9889), and for every entry:
#
#    * the read shape is the one the contract implies (object of components /
#      array of elements);
#    * feeding that value **exactly as read** to the endpoint's own write tool
#      answers `code=0` and a `new_value` structurally equal to it;
#    * reading it again answers the same value (read -> write -> re-read).
#
#  Gate-2 classes are given for the two tools of the item (success / missing
#  parameter -32602 / underlying failure -32001 with a suggestion), plus the
#  refusal class that ends the E-3 story: a component that does not fit its slot
#  is refused with the component's own name (`value.x`) and the slot's width -
#  a readable reason, not a bare `-32602`.
#
#  Discipline (PLAYBOOK sections 3 and 7): request bodies are built with
#  `ConvertTo-Json` and posted with `curl.exe --data-binary @file`; response
#  bodies are written by `curl.exe -s -o <file>` (never through a pipe or
#  `Out-File`) and every body gets a sha256. The user's editor on 9877 is never
#  touched - only its listener pid is read as a before/after guard.
#
#  Usage:
#    powershell -NoProfile -ExecutionPolicy Bypass -File mcp025_e3_writeside_evidence.ps1
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
$Root = Join-Path $env:TEMP 'task025-e3-writeside'
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

# The Variant type name a JSON value answers after `ConvertFrom-Json`.
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

# A **structural** comparison of two parsed JSON values - deliberately not a
# string comparison, so the round-trip claim below is about the values and about
# nobody having to normalise a spelling first.
function Test-ValueEqual {
    param($A, $B)
    if ($null -eq $A -and $null -eq $B) { return $true }
    if ($null -eq $A -or $null -eq $B) { return $false }
    $aIsString = $A -is [string]
    $bIsString = $B -is [string]
    if ($aIsString -or $bIsString) { return ($aIsString -and $bIsString -and ([string]$A -ceq [string]$B)) }
    $aIsBool = $A -is [bool]
    $bIsBool = $B -is [bool]
    if ($aIsBool -or $bIsBool) { return ($aIsBool -and $bIsBool -and ($A -eq $B)) }
    if (($A -is [ValueType]) -and ($B -is [ValueType])) { return ([double]$A -eq [double]$B) }
    $aIsList = $A -is [System.Collections.IList]
    $bIsList = $B -is [System.Collections.IList]
    if ($aIsList -or $bIsList) {
        if (-not ($aIsList -and $bIsList)) { return $false }
        $la = @($A); $lb = @($B)
        if ($la.Count -ne $lb.Count) { return $false }
        for ($i = 0; $i -lt $la.Count; $i++) {
            if (-not (Test-ValueEqual $la[$i] $lb[$i])) { return $false }
        }
        return $true
    }
    $pa = @($A.PSObject.Properties.Name)
    $pb = @($B.PSObject.Properties.Name)
    if ($pa.Count -ne $pb.Count) { return $false }
    foreach ($name in $pa) {
        if ($pb -notcontains $name) { return $false }
        if (-not (Test-ValueEqual $A.$name $B.$name)) { return $false }
    }
    return $true
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
# Scratch project: one exported property per entry of the read-back matrix.
# -----------------------------------------------------------------------------

$MainGd = @'
extends Node2D

@export var v2: Vector2 = Vector2(1.5, 2.5)
@export var v2i: Vector2i = Vector2i(1, 2)
@export var v3: Vector3 = Vector3(1.5, 2.5, 3.5)
@export var v3i: Vector3i = Vector3i(1, 2, 3)
@export var v4: Vector4 = Vector4(1.5, 2.5, 3.5, 4.5)
@export var v4i: Vector4i = Vector4i(1, 2, 3, 4)
@export var color: Color = Color(0.25, 0.5, 0.75, 1.0)
@export var rect: Rect2 = Rect2(1.5, 2.5, 30.5, 40.5)
@export var rect_i: Rect2i = Rect2i(1, 2, 30, 40)
@export var pb: PackedByteArray = PackedByteArray([1, 200])
@export var pi32: PackedInt32Array = PackedInt32Array([7, -3])
@export var pi64: PackedInt64Array = PackedInt64Array([7, -3])
@export var pf32: PackedFloat32Array = PackedFloat32Array([0.5, 1.5])
@export var pf64: PackedFloat64Array = PackedFloat64Array([0.25, 1.75])
@export var ps: PackedStringArray = PackedStringArray(["a", "b"])
@export var pv2: PackedVector2Array = PackedVector2Array([Vector2(1, 2), Vector2(3, 4)])
@export var pv3: PackedVector3Array = PackedVector3Array([Vector3(1, 2, 3)])
@export var pv4: PackedVector4Array = PackedVector4Array([Vector4(1, 2, 3, 4), Vector4(5, 6, 7, 8)])
@export var pc: PackedColorArray = PackedColorArray([Color(1, 0, 0, 1), Color(0, 1, 0, 1)])
'@
# ASCII only, written as UTF-8 without a BOM (PLAYBOOK section 3's `--import`
# trap: a `.tscn`/script with a BOM can make the first import fail).

$MainScene = @'
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://main.gd" id="1_main"]

[node name="Main" type="Node2D"]
script = ExtResource("1_main")
'@

function New-ScratchProject {
    $projectGodot = @(
        'config_version=5'
        ''
        '[application]'
        'config/name="MCP025 E-3 write-side evidence"'
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

# -----------------------------------------------------------------------------
# The read-back matrix.
#
# `shape` is what the read side must answer, `seed` is what the write tool is
# given first (so the re-read compares values the module itself accepted rather
# than the GDScript defaults). The node argument is `path` on the editor tool and
# `node_path` on the game tool, and each is passed under its own name - a
# mismatch is a `-32602`, never a silent default.
# -----------------------------------------------------------------------------

$Matrix = [ordered]@{
    v2     = @{ shape = 'object_xy';         seed = @{ x = 1.5; y = 2.5 } }
    v2i    = @{ shape = 'object_xy_int';     seed = @{ x = 1;   y = 2 } }
    v3     = @{ shape = 'object_xyz';        seed = @{ x = 1.5; y = 2.5; z = 3.5 } }
    v3i    = @{ shape = 'object_xyz_int';    seed = @{ x = 1;   y = 2;   z = 3 } }
    v4     = @{ shape = 'object_xyzw';       seed = @{ x = 1.5; y = 2.5; z = 3.5; w = 4.5 } }
    v4i    = @{ shape = 'object_xyzw_int';   seed = @{ x = 1;   y = 2;   z = 3;   w = 4 } }
    color  = @{ shape = 'object_rgba';       seed = @{ r = 0.25; g = 0.5; b = 0.75; a = 1.0 } }
    rect   = @{ shape = 'object_rect';       seed = @{ x = 1.5; y = 2.5; width = 30.5; height = 40.5 } }
    rect_i = @{ shape = 'object_rect_int';   seed = @{ x = 1;   y = 2;   width = 30;   height = 40 } }
    pb     = @{ shape = 'array_integer';     seed = @(1, 200) }
    pi32   = @{ shape = 'array_integer';     seed = @(7, -3) }
    pi64   = @{ shape = 'array_integer';     seed = @(7, -3) }
    pf32   = @{ shape = 'array_number';      seed = @(0.5, 1.5) }
    pf64   = @{ shape = 'array_number';      seed = @(0.25, 1.75) }
    ps     = @{ shape = 'array_string';      seed = @('a', 'b') }
    pv2    = @{ shape = 'array_object_xy';   seed = @(@{ x = 1; y = 2 }, @{ x = 3; y = 4 }) }
    pv3    = @{ shape = 'array_object_xyz';  seed = @(@{ x = 1; y = 2; z = 3 }) }
    pv4    = @{ shape = 'array_object_xyzw'; seed = @(@{ x = 1; y = 2; z = 3; w = 4 }, @{ x = 5; y = 6; z = 7; w = 8 }) }
    pc     = @{ shape = 'array_object_rgba'; seed = @(@{ r = 1; g = 0; b = 0; a = 1 }, @{ r = 0; g = 1; b = 0; a = 1 }) }
}
$MatrixNames = @($Matrix.Keys)

$ShapeFields = @{
    object_xy         = @('x', 'y')
    object_xy_int     = @('x', 'y')
    object_xyz        = @('x', 'y', 'z')
    object_xyz_int    = @('x', 'y', 'z')
    object_xyzw       = @('x', 'y', 'z', 'w')
    object_xyzw_int   = @('x', 'y', 'z', 'w')
    object_rgba       = @('r', 'g', 'b', 'a')
    object_rect       = @('x', 'y', 'width', 'height')
    object_rect_int   = @('x', 'y', 'width', 'height')
    array_object_xy   = @('x', 'y')
    array_object_xyz  = @('x', 'y', 'z')
    array_object_xyzw = @('x', 'y', 'z', 'w')
    array_object_rgba = @('r', 'g', 'b', 'a')
}

# Does one read-back value answer the shape the contract implies?
function Test-Shape {
    param([string]$Shape, $Value)
    $kind = Get-JsonKind $Value
    if ($Shape -like 'array_*') {
        if ($kind -ne 'array') { return $false }
        $elements = @($Value)
        if ($elements.Count -eq 0) { return $false }
        $elementKind = $Shape.Substring(6)
        switch ($elementKind) {
            'integer' { return (($elements[0] -is [int]) -or ($elements[0] -is [long])) }
            'number' { return ((Get-JsonKind $elements[0]) -eq 'number') }
            'string' { return ((Get-JsonKind $elements[0]) -eq 'string') }
            default {
                if ((Get-JsonKind $elements[0]) -ne 'object') { return $false }
                foreach ($field in $ShapeFields[$Shape]) {
                    if ($null -eq $elements[0].PSObject.Properties[$field]) { return $false }
                }
                return $true
            }
        }
    }
    if ($kind -ne 'object') { return $false }
    foreach ($field in $ShapeFields[$Shape]) {
        if ($null -eq $Value.PSObject.Properties[$field]) { return $false }
    }
    # The first component carries the number kind: the `_int` shapes must answer
    # integers, every real-valued one a number. (Not `$Value.x` - a `Color`'s
    # components are `r`/`g`/`b`/`a`.)
    $first = $ShapeFields[$Shape][0]
    if ($Shape -like '*_int') {
        return (($Value.$first -is [int]) -or ($Value.$first -is [long]))
    }
    return ((Get-JsonKind $Value.$first) -eq 'number')
}

# One endpoint's read -> write -> re-read pass over the whole matrix. Returns the
# number of entries that failed; every entry is also reported by `Check`.
function Invoke-Matrix {
    param([string]$Prefix, [string]$ReadTool, [string]$WriteTool, [int]$Port, [string]$PathArgument)
    $readArguments = @{}
    $readArguments[$PathArgument] = 'Main'
    $readArguments['properties'] = $MatrixNames
    $readEnv = Invoke-Tool -Id ($Prefix + '_read_1') -Tool $ReadTool -Arguments $readArguments -Port $Port
    $readPayload = Get-Payload $readEnv
    if ($null -eq $readPayload) {
        Check ($Prefix + '_read_1_answered') $false ("no payload from {0}; envelope: {1}" -f $ReadTool, (ConvertTo-CompactJson $readEnv))
        return $MatrixNames.Count
    }
    $first = $readPayload.properties
    Note ("{0} read-back: {1}" -f $Prefix, (ConvertTo-CompactJson $first))

    $failed = 0
    foreach ($name in $MatrixNames) {
        $value = $first.$name
        $shapeOk = Test-Shape -Shape $Matrix[$name].shape -Value $value
        if (-not $shapeOk) { $failed++ }
        Check ($Prefix + '_' + $name + '_read_shape') $shapeOk `
            ("{0}: kind={1} value={2}" -f $name, (Get-JsonKind $value), (ConvertTo-CompactJson $value))

        # The value goes back **exactly as it was read**: no reshaping step.
        $writeArguments = @{}
        $writeArguments[$PathArgument] = 'Main'
        $writeArguments['property'] = $name
        $writeArguments['value'] = $value
        $writeEnv = Invoke-Tool -Id ($Prefix + '_write_' + $name) -Tool $WriteTool -Arguments $writeArguments -Port $Port
        $writePayload = Get-Payload $writeEnv
        $code = Get-ErrorCode $writeEnv
        $accepted = ($code -eq 0) -and ($null -ne $writePayload)
        $sameValue = $accepted -and (Test-ValueEqual $writePayload.new_value $value)

        # ... and it is read again, from the object, after the write.
        $againArguments = @{}
        $againArguments[$PathArgument] = 'Main'
        $againArguments['properties'] = @($name)
        $againEnv = Invoke-Tool -Id ($Prefix + '_reread_' + $name) -Tool $ReadTool -Arguments $againArguments -Port $Port
        $againPayload = Get-Payload $againEnv
        $againValue = $null
        if ($null -ne $againPayload) { $againValue = $againPayload.properties.$name }
        $readAgain = ($null -ne $againPayload) -and (Test-ValueEqual $againValue $value)

        $roundTripOk = $accepted -and $sameValue -and $readAgain
        if (-not $roundTripOk) { $failed++ }
        Check ($Prefix + '_' + $name + '_round_trip') $roundTripOk `
            ("{0}: write code={1} new_value={2} re-read={3} (written value={4})" -f `
                $name, $code, (ConvertTo-CompactJson $writePayload.new_value), (ConvertTo-CompactJson $againValue), (ConvertTo-CompactJson $value))
    }
    return $failed
}

# =============================================================================
#  Run
# =============================================================================

Note '================================================================='
Note ' TASK-025 gate-2 evidence -- E-3 write side (read -> write -> re-read)'
Note '================================================================='
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

try {
    New-ScratchProject
    $importAttempts = Import-Project
    Note ("scratch project: {0} (imported on attempt {1})" -f $Project, $importAttempts)

    $script:EditorHandle = Start-Engine -Arguments @('--headless', '-e', '--path', $Project, "--mcp-port=$EditorPort") -LogName 'editor'
    Check 'editor_endpoint_ready' (Wait-ForPump -Port $EditorPort) ("editor on {0} answered GET /mcp with +20 frames three times" -f $EditorPort)

    $open = Invoke-Tool -Id 'A1_open_main_scene' -Tool 'editor_open_scene' -Arguments @{ path = 'res://scenes/main.tscn' }
    Check 'A1_main_scene_open' ($null -ne (Get-Payload $open)) ("editor_open_scene -> " + (ConvertTo-CompactJson (Get-Payload $open)))

    # =====================================================================
    # (1) seed every matrix property through the write tool
    # =====================================================================
    Note ''
    Note '--- (1) editor: seed the 19 matrix properties through the write tool ---'
    $seedFailures = New-Object System.Collections.Generic.List[string]
    foreach ($name in $MatrixNames) {
        $env = Invoke-Tool -Id ('A2_seed_' + $name) -Tool 'editor_set_node_property' `
            -Arguments @{ path = 'Main'; property = $name; value = $Matrix[$name].seed }
        if ((Get-ErrorCode $env) -ne 0) {
            $seedFailures.Add(("{0}: code={1} message='{2}'" -f $name, (Get-ErrorCode $env), (Get-ErrorMessage $env)))
        }
    }
    $seedReport = '<none>'
    if ($seedFailures.Count -gt 0) { $seedReport = ($seedFailures -join '; ') }
    Check 'A2_all_19_properties_seeded' ($seedFailures.Count -eq 0) `
        ("{0} of {1} seeded; failures: {2}" -f ($MatrixNames.Count - $seedFailures.Count), $MatrixNames.Count, $seedReport)

    # =====================================================================
    # (2) the editor matrix: read -> write -> re-read
    # =====================================================================
    Note ''
    Note '--- (2) editor 9888: read -> write -> re-read, every entry ---'
    $editorFailed = Invoke-Matrix -Prefix 'B_editor' -ReadTool 'editor_get_node_properties' `
        -WriteTool 'editor_set_node_property' -Port $EditorPort -PathArgument 'path'
    Check 'B_editor_matrix_complete' ($editorFailed -eq 0) `
        ("{0} of {1} matrix entries round-tripped on the editor endpoint" -f ($MatrixNames.Count - $editorFailed), $MatrixNames.Count)

    # The refusal class that ends the E-3 story: a component outside its slot is
    # refused with the component's own name and the slot's width.
    Note ''
    Note '--- (2b) the readable refusal: a rect component outside its slot ---'
    $badRect = Invoke-Tool -Id 'B2_bad_rect_component' -Tool 'editor_set_node_property' `
        -Arguments @{ path = 'Main'; property = 'rect'; value = @{ x = 1.0e300; y = 2.0; width = 3.0; height = 4.0 } }
    Check 'B2_rect_x_1e300_is_-32602_and_names_the_32_bit_component' `
        ((Get-ErrorCode $badRect) -eq -32602 -and (Get-ErrorMessage $badRect).Contains('value.x') -and (Get-ErrorMessage $badRect).Contains('32-bit float')) `
        ("code={0} message='{1}'" -f (Get-ErrorCode $badRect), (Get-ErrorMessage $badRect))
    $badRectI = Invoke-Tool -Id 'B2_bad_rect_i_component' -Tool 'editor_set_node_property' `
        -Arguments @{ path = 'Main'; property = 'rect_i'; value = @{ x = 3.0e9; y = 2; width = 30; height = 40 } }
    Check 'B2_rect_i_x_3e9_is_-32602_and_names_the_32_bit_component' `
        ((Get-ErrorCode $badRectI) -eq -32602 -and (Get-ErrorMessage $badRectI).Contains('value.x') -and (Get-ErrorMessage $badRectI).Contains('32-bit signed integer')) `
        ("code={0} message='{1}' (3e9 fits an int64 and not the int32 member, so the refusal can only come from the component slot)" -f (Get-ErrorCode $badRectI), (Get-ErrorMessage $badRectI))
    $missingComponent = Invoke-Tool -Id 'B2_missing_rect_component' -Tool 'editor_set_node_property' `
        -Arguments @{ path = 'Main'; property = 'rect_i'; value = @{ x = 1; y = 2; width = 30 } }
    Check 'B2_missing_component_is_-32602_with_the_component_list' `
        ((Get-ErrorCode $missingComponent) -eq -32602 -and (Get-ErrorMessage $missingComponent).Contains('height')) `
        ("code={0} message='{1}'" -f (Get-ErrorCode $missingComponent), (Get-ErrorMessage $missingComponent))
    # ... and the object/missing-component case is *not* a silent zero rect: the
    # property still holds what it held before.
    $afterRefusals = Invoke-Tool -Id 'B2_rect_after_refusals' -Tool 'editor_get_node_properties' `
        -Arguments @{ path = 'Main'; properties = @('rect', 'rect_i') }
    $afterPayload = Get-Payload $afterRefusals
    Check 'B2_refusals_left_the_property_untouched' `
        ((Test-ValueEqual $afterPayload.properties.rect ([pscustomobject]@{ x = 1.5; y = 2.5; width = 30.5; height = 40.5 })) `
            -and (Test-ValueEqual $afterPayload.properties.rect_i ([pscustomobject]@{ x = 1; y = 2; width = 30; height = 40 }))) `
        ("after the three refusals: rect={0} rect_i={1}" -f (ConvertTo-CompactJson $afterPayload.properties.rect), (ConvertTo-CompactJson $afterPayload.properties.rect_i))

    # =====================================================================
    # (3) gate-2 classes for the two tools of this item (editor side)
    # =====================================================================
    Note ''
    Note '--- (3) gate-2 classes: success / missing parameter / underlying failure ---'
    $setNoValue = Invoke-Tool -Id 'C1_set_missing_value' -Tool 'editor_set_node_property' -Arguments @{ path = 'Main'; property = 'v4' }
    Check 'C1_set_missing_value_is_-32602' ((Get-ErrorCode $setNoValue) -eq -32602 -and (Get-ErrorMessage $setNoValue).Contains('value')) `
        ("code={0} message='{1}'" -f (Get-ErrorCode $setNoValue), (Get-ErrorMessage $setNoValue))
    $setNoNode = Invoke-Tool -Id 'C1_set_missing_node' -Tool 'editor_set_node_property' -Arguments @{ path = 'NoSuchNode'; property = 'v4'; value = @{ x = 1; y = 2; z = 3; w = 4 } }
    Check 'C1_set_missing_node_is_-32001_with_a_suggestion' ((Get-ErrorCode $setNoNode) -eq -32001 -and (Get-ErrorSuggestion $setNoNode) -ne '') `
        ("code={0} message='{1}' suggestion='{2}'" -f (Get-ErrorCode $setNoNode), (Get-ErrorMessage $setNoNode), (Get-ErrorSuggestion $setNoNode))
    $setNoProperty = Invoke-Tool -Id 'C1_set_missing_property' -Tool 'editor_set_node_property' -Arguments @{ path = 'Main'; property = 'no_such_property'; value = 1 }
    Check 'C1_set_missing_property_is_-32001_with_a_suggestion' ((Get-ErrorCode $setNoProperty) -eq -32001 -and (Get-ErrorSuggestion $setNoProperty) -ne '') `
        ("code={0} message='{1}' suggestion='{2}'" -f (Get-ErrorCode $setNoProperty), (Get-ErrorMessage $setNoProperty), (Get-ErrorSuggestion $setNoProperty))

    $getNoPath = Invoke-Tool -Id 'C2_get_missing_param' -Tool 'editor_get_node_properties' -Arguments @{ properties = @('v4') }
    Check 'C2_get_missing_param_is_-32602' ((Get-ErrorCode $getNoPath) -eq -32602) `
        ("code={0} message='{1}'" -f (Get-ErrorCode $getNoPath), (Get-ErrorMessage $getNoPath))
    $getNoNode = Invoke-Tool -Id 'C2_get_missing_node' -Tool 'editor_get_node_properties' -Arguments @{ path = 'NoSuchNode'; properties = @('v4') }
    Check 'C2_get_missing_node_is_-32001_with_a_suggestion' ((Get-ErrorCode $getNoNode) -eq -32001 -and (Get-ErrorSuggestion $getNoNode) -ne '') `
        ("code={0} message='{1}' suggestion='{2}'" -f (Get-ErrorCode $getNoNode), (Get-ErrorMessage $getNoNode), (Get-ErrorSuggestion $getNoNode))

    # Save *after* the seeding so the game process loads the seeded scene.
    $save = Invoke-Tool -Id 'C3_save_scene' -Tool 'editor_save_scene' -Arguments @{}
    Check 'C3_scene_saved_after_seeding' ($null -ne (Get-Payload $save)) `
        ("editor_save_scene -> {0}; scenes/main.tscn sha256={1}" -f (ConvertTo-CompactJson (Get-Payload $save)), (Get-FileSha (Join-Path $Project 'scenes\main.tscn')))

    # =====================================================================
    # (4) the game endpoint: the same matrix, read -> write -> re-read
    # =====================================================================
    Note ''
    Note '--- (4) game 9889: the same 19 entries ---'
    $script:GameHandle = Start-Engine -Arguments @('--headless', '--path', $Project, "--mcp-port=$GamePort") -LogName 'game'
    Check 'game_endpoint_ready' (Wait-ForPump -Port $GamePort) ("game on {0} answered GET /mcp with +20 frames three times" -f $GamePort)

    $gameFailed = Invoke-Matrix -Prefix 'D_game' -ReadTool 'running_game_get_node_properties' `
        -WriteTool 'running_game_set_node_property' -Port $GamePort -PathArgument 'node_path'
    Check 'D_game_matrix_complete' ($gameFailed -eq 0) `
        ("{0} of {1} matrix entries round-tripped on the game endpoint" -f ($MatrixNames.Count - $gameFailed), $MatrixNames.Count)

    $gameSetNoValue = Invoke-Tool -Id 'D2_game_set_missing_value' -Tool 'running_game_set_node_property' -Arguments @{ node_path = 'Main'; property = 'v4' } -Port $GamePort
    Check 'D2_game_set_missing_value_is_-32602' ((Get-ErrorCode $gameSetNoValue) -eq -32602) `
        ("code={0} message='{1}'" -f (Get-ErrorCode $gameSetNoValue), (Get-ErrorMessage $gameSetNoValue))
    $gameSetNoNode = Invoke-Tool -Id 'D2_game_set_missing_node' -Tool 'running_game_set_node_property' -Arguments @{ node_path = 'NoSuchNode'; property = 'v4'; value = @{ x = 1; y = 2; z = 3; w = 4 } } -Port $GamePort
    Check 'D2_game_set_missing_node_is_-32001' ((Get-ErrorCode $gameSetNoNode) -eq -32001) `
        ("code={0} message='{1}'" -f (Get-ErrorCode $gameSetNoNode), (Get-ErrorMessage $gameSetNoNode))
    $gameGetNoParam = Invoke-Tool -Id 'D2_game_get_missing_param' -Tool 'running_game_get_node_properties' -Arguments @{ properties = @('v4') } -Port $GamePort
    Check 'D2_game_get_missing_param_is_-32602' ((Get-ErrorCode $gameGetNoParam) -eq -32602) `
        ("code={0} message='{1}'" -f (Get-ErrorCode $gameGetNoParam), (Get-ErrorMessage $gameGetNoParam))
    $gameGetNoNode = Invoke-Tool -Id 'D2_game_get_missing_node' -Tool 'running_game_get_node_properties' -Arguments @{ node_path = 'NoSuchNode'; properties = @('v4') } -Port $GamePort
    Check 'D2_game_get_missing_node_is_-32001' ((Get-ErrorCode $gameGetNoNode) -eq -32001) `
        ("code={0} message='{1}'" -f (Get-ErrorCode $gameGetNoNode), (Get-ErrorMessage $gameGetNoNode))

    # =====================================================================
    # (5) the zero-string-surgery chain, read -> write -> re-read, both ends
    #
    # Every step below consumes a *field of the previous answer* directly. No
    # `.Split(`, `.Replace(`, `.Substring(`, `.Trim(`, `-match`, `-replace` or
    # numeric cast appears inside the marked region - which is asserted
    # mechanically against this script's own text below, not just claimed.
    # =====================================================================
    Note ''
    Note '--- (5) chain: read -> write -> re-read, string operations by the caller: 0 ---'
    $chainSteps = New-Object System.Collections.Generic.List[string]

    # CHAIN-BEGIN
    # segment 1 (editor): read the composite properties
    $c1 = Invoke-Tool -Id 'E1_editor_read' -Tool 'editor_get_node_properties' -Arguments @{ path = 'Main'; properties = @('v4', 'v4i', 'rect', 'rect_i', 'pv4', 'pb') }
    $c1p = Get-Payload $c1
    $chainSteps.Add(("1 editor_get_node_properties -> .v4i = {0}, .rect = {1}, .rect_i = {2} (string ops: 0)" -f `
                (ConvertTo-CompactJson $c1p.properties.v4i), (ConvertTo-CompactJson $c1p.properties.rect), (ConvertTo-CompactJson $c1p.properties.rect_i)))

    # segment 2 (editor): the read value goes straight back in
    $c2 = Invoke-Tool -Id 'E2_editor_write' -Tool 'editor_set_node_property' -Arguments @{ path = 'Main'; property = 'rect_i'; value = $c1p.properties.rect_i }
    $c2p = Get-Payload $c2
    $chainSteps.Add(("2 editor_set_node_property(rect_i = step1 .rect_i) -> code={0} .new_value = {1} (string ops: 0)" -f (Get-ErrorCode $c2), (ConvertTo-CompactJson $c2p.new_value)))

    # segment 3 (editor): and it reads back the same
    $c3 = Invoke-Tool -Id 'E3_editor_reread' -Tool 'editor_get_node_properties' -Arguments @{ path = 'Main'; properties = @('rect_i') }
    $c3p = Get-Payload $c3
    $chainSteps.Add(("3 editor_get_node_properties -> .rect_i = {0} (string ops: 0)" -f (ConvertTo-CompactJson $c3p.properties.rect_i)))

    # segment 4 (game): the same read on the other endpoint
    $c4 = Invoke-Tool -Id 'E4_game_read' -Tool 'running_game_get_node_properties' -Arguments @{ node_path = 'Main'; properties = @('v4', 'v4i', 'rect', 'rect_i', 'pv4', 'pb') } -Port $GamePort
    $c4p = Get-Payload $c4
    $chainSteps.Add(("4 running_game_get_node_properties -> .v4i = {0}, .rect = {1} (string ops: 0)" -f `
                (ConvertTo-CompactJson $c4p.properties.v4i), (ConvertTo-CompactJson $c4p.properties.rect)))

    # segment 5 (game): back in
    $c5 = Invoke-Tool -Id 'E5_game_write' -Tool 'running_game_set_node_property' -Arguments @{ node_path = 'Main'; property = 'v4i'; value = $c4p.properties.v4i } -Port $GamePort
    $c5p = Get-Payload $c5
    $chainSteps.Add(("5 running_game_set_node_property(v4i = step4 .v4i) -> code={0} .new_value = {1} (string ops: 0)" -f (Get-ErrorCode $c5), (ConvertTo-CompactJson $c5p.new_value)))

    # segment 6 (game): re-read
    $c6 = Invoke-Tool -Id 'E6_game_reread' -Tool 'running_game_get_node_properties' -Arguments @{ node_path = 'Main'; properties = @('v4i') } -Port $GamePort
    $c6p = Get-Payload $c6
    $chainSteps.Add(("6 running_game_get_node_properties -> .v4i = {0} (string ops: 0)" -f (ConvertTo-CompactJson $c6p.properties.v4i)))
    # CHAIN-END

    $chainOk = ($null -eq $c1.error) -and ($null -eq $c2.error) -and ($null -eq $c3.error) `
        -and ($null -eq $c4.error) -and ($null -eq $c5.error) -and ($null -eq $c6.error) `
        -and ((Get-JsonKind $c1p.properties.v4i) -eq 'object') -and ((Get-JsonKind $c1p.properties.rect) -eq 'object') `
        -and ((Get-JsonKind $c1p.properties.pv4) -eq 'array') -and ((Get-JsonKind $c1p.properties.pb) -eq 'array') `
        -and ((Get-ErrorCode $c2) -eq 0) -and (Test-ValueEqual $c2p.new_value $c1p.properties.rect_i) `
        -and (Test-ValueEqual $c3p.properties.rect_i $c1p.properties.rect_i) `
        -and ((Get-ErrorCode $c5) -eq 0) -and (Test-ValueEqual $c5p.new_value $c4p.properties.v4i) `
        -and (Test-ValueEqual $c6p.properties.v4i $c4p.properties.v4i)
    Check 'E_chain_read_write_reread_six_steps' $chainOk ("{0}" -f ($chainSteps -join ' || '))

    $selfText = [IO.File]::ReadAllText($PSCommandPath)
    $begin = $selfText.IndexOf('# CHAIN-BEGIN')
    $end = $selfText.IndexOf('# CHAIN-END')
    $chainText = $selfText.Substring($begin, $end - $begin)
    $forbidden = @('.Split(', '.Replace(', '.Substring(', '.Trim(', '-match ', '-replace ', '[double]', '[int]', '[regex]', 'ConvertTo-Json')
    $found = @()
    foreach ($token in $forbidden) {
        if ($chainText.Contains($token)) { $found += $token }
    }
    $foundReport = '<none>'
    if ($found.Count -gt 0) { $foundReport = ($found -join ', ') }
    Check 'E_chain_region_has_no_string_surgery_tokens' ($found.Count -eq 0) `
        ("forbidden tokens in the chain region: {0} (checked: {1})" -f $foundReport, ($forbidden -join ' '))

    # =====================================================================
    # (6) the matrix is the whole read-back matrix: 19 names, no engine gap
    # =====================================================================
    Check 'F_matrix_is_the_declared_19_entries' ($MatrixNames.Count -eq 19 -and ($MatrixNames -join ',') -ceq 'v2,v2i,v3,v3i,v4,v4i,color,rect,rect_i,pb,pi32,pi64,pf32,pf64,ps,pv2,pv3,pv4,pc') `
        ("{0} entries: {1}" -f $MatrixNames.Count, ($MatrixNames -join ','))
    Check 'F_every_entry_is_writable' (($editorFailed -eq 0) -and ($gameFailed -eq 0)) `
        ("editor failures={0}, game failures={1}: no entry of the matrix is engine-unwritable (each is a declared setter/data member reached through Object::set)" -f $editorFailed, $gameFailed)

    # =====================================================================
    # (7) contract untouched: the two tools advertise the same schema
    # =====================================================================
    Note ''
    Note '--- (7) the contract of the two tools is unchanged ---'
    $list = Invoke-Curl -Id 'G1_editor_tools_list' -Json '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' -Port $EditorPort
    $listed = $null
    try { $listed = (ConvertFrom-Json $list).result.tools } catch { }
    $schemaOf = @{}
    foreach ($tool in @($listed)) { $schemaOf[[string]$tool.name] = $tool.inputSchema }
    $setSchema = $schemaOf['editor_set_node_property']
    $setNames = @($setSchema.properties.PSObject.Properties.Name)
    Check 'G1_editor_set_schema_unchanged' (($setNames -join ',') -ceq 'path,property,value' -and (@($setSchema.required) -join ',') -ceq 'path,property,value') `
        ("editor_set_node_property.properties = [{0}], required = [{1}]" -f ($setNames -join ','), (@($setSchema.required) -join ','))
    $getSchema = $schemaOf['editor_get_node_properties']
    $getNames = @($getSchema.properties.PSObject.Properties.Name)
    Check 'G1_editor_get_schema_unchanged' (($getNames -join ',') -ceq 'path,properties') `
        ("editor_get_node_properties.properties = [{0}]" -f ($getNames -join ','))

    $gameList = Invoke-Curl -Id 'G2_game_tools_list' -Json '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' -Port $GamePort
    $gameListed = $null
    try { $gameListed = (ConvertFrom-Json $gameList).result.tools } catch { }
    $gameSchemaOf = @{}
    foreach ($tool in @($gameListed)) { $gameSchemaOf[[string]$tool.name] = $tool.inputSchema }
    $gameSetSchema = $gameSchemaOf['running_game_set_node_property']
    $gameSetNames = @($gameSetSchema.properties.PSObject.Properties.Name)
    Check 'G2_game_set_schema_unchanged' (($gameSetNames -join ',') -ceq 'node_path,property,value') `
        ("running_game_set_node_property.properties = [{0}] (read from {1})" -f ($gameSetNames -join ','), $GamePort)
    $gameGetSchema = $gameSchemaOf['running_game_get_node_properties']
    $gameGetNames = @($gameGetSchema.properties.PSObject.Properties.Name)
    Check 'G2_game_get_schema_unchanged' (($gameGetNames -join ',') -ceq 'node_path,properties') `
        ("running_game_get_node_properties.properties = [{0}]" -f ($gameGetNames -join ','))
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
