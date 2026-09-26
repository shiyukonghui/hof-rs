# =============================================================================
#  mcp026_e9_e6_evidence.ps1 -- live evidence for TASK-026
#
#  Item (1) E-9: `project_read_resource` used to answer `{loaded,path,type}` and
#  not one value of the resource, so a caller had to run a second tool
#  (`editor_execute_gdscript`) to see what the file stores. The engine gives the
#  values in one call (`Resource::get_property_list()` + `Object::get()`), and
#  this script measures:
#
#    * the `properties` map the tool now answers, on **both** endpoints
#      (editor 9888 / game 9889), cross-checked key for key against the STORAGE
#      names the engine itself reports for the same `.tres` through GDScript;
#    * the shapes of GDR-25 section 23.4 (`{r,g,b,a}` objects inside a
#      `PackedColorArray`, plain numbers inside a `PackedFloat32Array`);
#    * the count bound and its truncation marker on a resource that stores more
#      properties than the tool returns (an `Environment`);
#    * the read -> write -> re-read chain: the value that came out of
#      `project_read_resource` goes back in through `project_edit_resource`
#      **exactly as it was read** (no reshaping, no string surgery - asserted
#      against this script's own text), and is read again equal.
#
#  Item (2) E-6 + G-4: the two log tools read `user://logs/godot.log` and nothing
#  else, and that file is not the reader's log - the editor process never writes
#  it (`main.cpp:2287/2292`: file logging is behind the `pc` feature tag, and
#  feature tags are off inside the editor), the project's game process does, and
#  it is rotated by whoever writes it. M4c measured the two consequences this
#  script reproduces:
#
#    * the editor endpoint answered with the **game** process's lines;
#    * a read whose `open()` failed answered `-32603` where the honest answer is
#      "there is nothing to read" (here reproduced deterministically: the log
#      file is held with an exclusive lock, which is exactly what the rotation
#      window produces);
#
#  and measures the fixed behaviour: this process's own Output panel first
#  (`source: "editor_log"`), the file only as a fallback, a source block that
#  names the answering process (`editor`/`process`/`pid`/`port`) and whether the
#  lines can belong to another process (`in_process`), the same block from both
#  tools (G-4), and never `-32603` for "nothing to read".
#
#  Discipline (PLAYBOOK sections 3 and 7): request bodies come from
#  `ConvertTo-Json` and go out with `curl.exe --data-binary @file`; response
#  bodies are written with `curl.exe -s -o <file>` (never through a pipe or
#  `Out-File`) and every one gets a sha256; every scratch file is written as
#  UTF-8 **without BOM**. The user's editor on 9877 (pid read before and after)
#  is never occupied, killed or restarted.
#
#  Usage:
#    powershell -NoProfile -ExecutionPolicy Bypass -File mcp026_e9_e6_evidence.ps1
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
$Root = Join-Path $env:TEMP 'task026-e9-e6'
$Ev = Join-Path $Root 'evidence'
$LogRoot = Join-Path $Root 'logs'
$Project = Join-Path $Root 'proj'
$ProjectName = 'mcp026_evidence'
$UserAppDir = Join-Path $env:APPDATA ("Godot\app_userdata\" + $ProjectName)
$ExpectedLogFile = Join-Path $UserAppDir 'logs\godot.log'

Remove-Item -Recurse -Force $Root -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $Ev, $LogRoot, $Project | Out-Null

# The scratch project's *shared* log does not live under `$Root` (it is
# `%APPDATA%\Godot\app_userdata\<config/name>\logs`), and Godot never clears it
# for us: a previous run's game process lines - and its rotated backups - would
# still be there. Removing the whole directory before the run is what makes every
# check below about *this* run and about *this* run's processes.
Remove-Item -Recurse -Force (Join-Path $UserAppDir 'logs') -ErrorAction SilentlyContinue

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

# A structural comparison of two parsed JSON values - deliberately not a string
# comparison, so the round-trip claims below are about the values themselves.
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

function Get-PropertyNames {
    param($Object)
    if ($null -eq $Object) { return @() }
    return @($Object.PSObject.Properties.Name)
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
            Start-Sleep -Milliseconds 1500
        }
    } catch { }
}

# The `user://logs/godot.log` of the scratch project. The expected path is
# `%APPDATA%\Godot\app_userdata\<config/name>\logs\godot.log`; the fallback
# search exists only so that a sanitised project name cannot make this script
# claim "no file" when the engine wrote one.
function Resolve-LogFile {
    if (Test-Path $ExpectedLogFile) { return $ExpectedLogFile }
    $candidate = Get-ChildItem -Path (Join-Path $env:APPDATA 'Godot\app_userdata') -Recurse -Filter 'godot.log' `
        -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($null -ne $candidate) { return $candidate.FullName }
    return $null
}

# -----------------------------------------------------------------------------
# Scratch project
# -----------------------------------------------------------------------------

$MainGd = @'
extends Node2D

func _ready() -> void:
	print("MCP026-GAME-MARKER ready")
	push_error("MCP026-GAME-ERROR marker")
'@

$MainScene = @'
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://main.gd" id="1_main"]

[node name="Main" type="Node2D"]
script = ExtResource("1_main")
'@

$GradientTres = @'
[gd_resource type="Gradient" format=3]

[resource]
offsets = PackedFloat32Array(0, 1)
colors = PackedColorArray(1, 0, 0, 1, 0, 0, 1, 1)
'@

# 93 `ADD_PROPERTY` declarations in `scene/resources/environment.cpp`, nearly all
# of them default-usage (= STORAGE), against the tool's 64 property limit.
$EnvironmentTres = @'
[gd_resource type="Environment" format=3]

[resource]
'@

function New-ScratchProject {
    # ASCII only, and no BOM anywhere (PLAYBOOK section 3: a `.tscn` with a BOM
    # makes the first `--import` fail).
    $projectGodot = @(
        'config_version=5'
        ''
        '[application]'
        ('config/name="' + $ProjectName + '"')
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
    Write-Utf8NoBom -Path (Join-Path $Project 'resources\gradient.tres') -Text ($GradientTres + "`n")
    Write-Utf8NoBom -Path (Join-Path $Project 'resources\environment.tres') -Text ($EnvironmentTres + "`n")
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

# =============================================================================
#  Run
# =============================================================================

Note '================================================================='
Note ' TASK-026 evidence -- E-9 (resource values) + E-6/G-4 (log source)'
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
    $editorPid = $script:EditorHandle.Process.Id
    Check 'editor_endpoint_ready' (Wait-ForPump -Port $EditorPort) ("editor on {0} (pid {1}) answered GET /mcp with +20 frames three times" -f $EditorPort, $editorPid)

    # =====================================================================
    # (1) E-9 on the editor endpoint: the values, cross-checked with the
    #     engine's own STORAGE list, and the count bound.
    # =====================================================================
    Note ''
    Note '--- (1) E-9 on 9888: project_read_resource answers stored values ---'
    $gradientRead = Invoke-Tool -Id 'E9_read_gradient' -Tool 'project_read_resource' -Arguments @{ path = 'res://resources/gradient.tres' }
    $gradientPayload = Get-Payload $gradientRead
    Check 'E9_1_gradient_read_ok' ($null -ne $gradientPayload -and (Get-ErrorCode $gradientRead) -eq 0) `
        ("payload=" + (ConvertTo-CompactJson $gradientPayload))
    $storedNames = @()
    $stored = $null
    if ($null -ne $gradientPayload) {
        $stored = $gradientPayload.properties
        $storedNames = Get-PropertyNames $stored
    }
    Note ("stored property names: {0}" -f ($storedNames -join ', '))
    Check 'E9_2_properties_present' (($storedNames.Count -gt 0)) `
        ("properties keys = [{0}], total_properties={1}, truncated={2}" -f ($storedNames -join ','), $gradientPayload.total_properties, $gradientPayload.truncated)
    Check 'E9_3_both_stored_shapes' (($storedNames -contains 'colors') -and ($storedNames -contains 'offsets')) `
        ("colors kind={0} value={1}; offsets kind={2} value={3}" -f (Get-JsonKind $stored.colors), (ConvertTo-CompactJson $stored.colors), (Get-JsonKind $stored.offsets), (ConvertTo-CompactJson $stored.offsets))
    $colorsOk = ($stored.colors -is [System.Object[]]) -and ($stored.colors.Count -eq 2) `
        -and ((Get-JsonKind $stored.colors[0]) -eq 'object') `
        -and ((@($stored.colors[0].PSObject.Properties.Name | Sort-Object) -join ',') -ceq 'a,b,g,r') `
        -and ([double]$stored.colors[0].r -eq 1.0) -and ([double]$stored.colors[1].b -eq 1.0)
    Check 'E9_4_packed_color_array_is_an_array_of_rgba_objects' $colorsOk `
        ("colors = {0} (section 23.4 shape: array of {{r,g,b,a}} objects)" -f (ConvertTo-CompactJson $stored.colors))
    $offsetsOk = ($stored.offsets -is [System.Object[]]) -and ($stored.offsets.Count -eq 2) -and ([double]$stored.offsets[0] -eq 0.0) -and ([double]$stored.offsets[1] -eq 1.0)
    Check 'E9_5_packed_float_array_is_an_array_of_numbers' $offsetsOk `
        ("offsets = {0}" -f (ConvertTo-CompactJson $stored.offsets))

    # The engine's own answer for the same file: the tool's keys must be exactly
    # the STORAGE names, and nothing else.
    $crossCheck = @'
var res = load("res://resources/gradient.tres")
var names = []
for p in res.get_property_list():
	if p.usage & PROPERTY_USAGE_STORAGE:
		names.append(String(p.name))
return names
'@
    $crossEnv = Invoke-Tool -Id 'E9_engine_storage_names' -Tool 'editor_execute_gdscript' -Arguments @{ code = $crossCheck }
    $crossPayload = Get-Payload $crossEnv
    $engineNames = @()
    if ($null -ne $crossPayload -and $null -ne $crossPayload.result) { $engineNames = @($crossPayload.result | ForEach-Object { [string]$_ }) }
    $toolNames = @($storedNames | Sort-Object)
    $engineSorted = @($engineNames | Sort-Object)
    Check 'E9_6_keys_equal_the_engines_storage_list' (($toolNames -join ',') -ceq ($engineSorted -join ',')) `
        ("tool properties = [{0}] ; engine get_property_list() STORAGE = [{1}]" -f ($toolNames -join ','), ($engineSorted -join ','))

    # The bound: an `Environment` stores far more than the limit.
    $envRead = Invoke-Tool -Id 'E9_read_environment' -Tool 'project_read_resource' -Arguments @{ path = 'res://resources/environment.tres' }
    $envPayload = Get-Payload $envRead
    $envNames = @()
    if ($null -ne $envPayload) { $envNames = Get-PropertyNames $envPayload.properties }
    $envTotal = 0
    if ($null -ne $envPayload) { $envTotal = [int]$envPayload.total_properties }
    Check 'E9_7_environment_answers_a_truncation_marker' `
        (($envTotal -gt 64) -and ($envPayload.truncated -eq $true) -and ([int]$envPayload.dropped -eq ($envTotal - 64)) -and ($envNames.Count -eq 64)) `
        ("total_properties={0} returned={1} dropped={2} truncated={3} limits={4} message='{5}'" -f `
            $envTotal, $envNames.Count, $envPayload.dropped, $envPayload.truncated, (ConvertTo-CompactJson $envPayload.limits), $envPayload.message)

    # Gate-2 classes for the tool: success (above), missing parameter, and an
    # underlying failure with a suggestion.
    $missingParam = Invoke-Tool -Id 'E9_missing_param' -Tool 'project_read_resource' -Arguments @{}
    Check 'E9_8_missing_path_is_-32602' ((Get-ErrorCode $missingParam) -eq -32602) `
        ("code={0} message='{1}'" -f (Get-ErrorCode $missingParam), (Get-ErrorMessage $missingParam))
    $missingFile = Invoke-Tool -Id 'E9_missing_file' -Tool 'project_read_resource' -Arguments @{ path = 'res://resources/does_not_exist.tres' }
    Check 'E9_9_missing_file_is_-32001_with_a_suggestion' `
        (((Get-ErrorCode $missingFile) -eq -32001) -and ((Get-ErrorSuggestion $missingFile) -ne '')) `
        ("code={0} message='{1}' suggestion='{2}'" -f (Get-ErrorCode $missingFile), (Get-ErrorMessage $missingFile), (Get-ErrorSuggestion $missingFile))

    # =====================================================================
    # (2) The editor process's own log (E-6): a real print and a real error,
    #     then the two tools, then the source block.
    # =====================================================================
    Note ''
    Note '--- (2) E-6 on 9888: the editor process answers with its OWN log ---'
    $editorMarker = @'
print("MCP026-EDITOR-MARKER stdout")
push_error("MCP026-EDITOR-ERROR marker")
return "marked"
'@
    $markEnv = Invoke-Tool -Id 'E6_editor_marker' -Tool 'editor_execute_gdscript' -Arguments @{ code = $editorMarker }
    $markPayload = Get-Payload $markEnv
    Check 'E6_1_editor_log_marker_written' ($null -ne $markPayload) `
        ("editor_execute_gdscript -> {0} (the editor's own print handler routes both into EditorLog)" -f (ConvertTo-CompactJson $markPayload))
    Start-Sleep -Milliseconds 800

    # The window that owns the MCP listener on 9888 is the engine process; the
    # console wrapper `Start-Process -PassThru` returns is only its launcher, so
    # the pid the tool reports is compared against the listener, not the
    # launcher.
    $editorEnginePid = Get-ListenerPid -Port $EditorPort
    Note ("editor console wrapper pid={0}; engine pid (the listener on {1})={2}" -f $editorPid, $EditorPort, $editorEnginePid)

    $editorOut = Invoke-Tool -Id 'E6_editor_output_log' -Tool 'editor_get_output_log' -Arguments @{ max_lines = 500 }
    $editorOutPayload = Get-Payload $editorOut
    $editorOutLines = @()
    if ($null -ne $editorOutPayload) { $editorOutLines = @($editorOutPayload.lines | ForEach-Object { [string]$_ }) }
    $editorOutText = $editorOutLines -join "`n"
    Check 'E6_2_editor_endpoint_uses_the_in_process_log' `
        (($null -ne $editorOutPayload) -and ($editorOutPayload.source -eq 'editor_log') -and ($editorOutPayload.in_process -eq $true) -and ($editorOutPayload.available -eq $true)) `
        ("source={0} in_process={1} available={2} note='{3}'" -f $editorOutPayload.source, $editorOutPayload.in_process, $editorOutPayload.available, $editorOutPayload.note)
    Check 'E6_3_editor_endpoint_reports_its_own_process' `
        (($editorOutPayload.editor -eq $true) -and ($editorOutPayload.process -eq 'editor') -and ([int]$editorOutPayload.pid -eq $editorEnginePid) -and ([int]$editorOutPayload.port -eq $EditorPort) -and ($editorOutPayload.log_path -eq 'user://logs/godot.log')) `
        ("editor={0} process={1} pid={2} (engine pid listening on {3} = {4}) port={5} log_path={6}" -f `
            $editorOutPayload.editor, $editorOutPayload.process, $editorOutPayload.pid, $EditorPort, $editorEnginePid, $editorOutPayload.port, $editorOutPayload.log_path)
    Check 'E6_4_editor_marker_is_in_the_editor_answer' ($editorOutText.Contains('MCP026-EDITOR-MARKER stdout')) `
        ("lines containing the marker: {0}" -f (ConvertTo-CompactJson @($editorOutLines | Where-Object { $_ -like '*MCP026-EDITOR*' })))

    $editorErr = Invoke-Tool -Id 'E6_editor_errors' -Tool 'editor_get_errors' -Arguments @{ max_lines = 500 }
    $editorErrPayload = Get-Payload $editorErr
    $editorErrLines = @()
    if ($null -ne $editorErrPayload) { $editorErrLines = @($editorErrPayload.errors | ForEach-Object { [string]$_ }) }
    $editorErrText = $editorErrLines -join "`n"
    $errorSourceOk = ($null -ne $editorErrPayload) -and ($editorErrPayload.source -eq $editorOutPayload.source) -and ($editorErrPayload.in_process -eq $editorOutPayload.in_process) `
        -and ($editorErrPayload.available -eq $editorOutPayload.available) -and ($editorErrPayload.editor -eq $editorOutPayload.editor) `
        -and ($editorErrPayload.process -eq $editorOutPayload.process) -and ([int]$editorErrPayload.pid -eq [int]$editorOutPayload.pid) `
        -and ([int]$editorErrPayload.port -eq [int]$editorOutPayload.port) -and ($editorErrPayload.log_path -eq $editorOutPayload.log_path) `
        -and ($editorErrPayload.note -eq $editorOutPayload.note)
    Check 'E6_5_G-4_both_tools_share_one_source_block' $errorSourceOk `
        ("editor_get_errors block = {0}; editor_get_output_log block = {1}" -f `
            (ConvertTo-CompactJson ([pscustomobject]@{ source = $editorErrPayload.source; in_process = $editorErrPayload.in_process; available = $editorErrPayload.available; editor = $editorErrPayload.editor; process = $editorErrPayload.process; pid = $editorErrPayload.pid; port = $editorErrPayload.port; log_path = $editorErrPayload.log_path; note = $editorErrPayload.note })), `
            (ConvertTo-CompactJson ([pscustomobject]@{ source = $editorOutPayload.source; in_process = $editorOutPayload.in_process; available = $editorOutPayload.available; editor = $editorOutPayload.editor; process = $editorOutPayload.process; pid = $editorOutPayload.pid; port = $editorOutPayload.port; log_path = $editorOutPayload.log_path; note = $editorOutPayload.note })))
    Check 'E6_6_editor_error_marker_is_in_the_editor_answer' ($editorErrText.Contains('MCP026-EDITOR-ERROR marker')) `
        ("errors containing the marker: {0}" -f (ConvertTo-CompactJson @($editorErrLines | Where-Object { $_ -like '*MCP026-EDITOR*' })))

    # =====================================================================
    # (3) The game process: it writes the shared file, and its own endpoint
    #     does not even carry the editor-scope log tools.
    # =====================================================================
    Note ''
    Note '--- (3) the game process on 9889 and the shared log file ---'
    $script:GameHandle = Start-Engine -Arguments @('--headless', '--path', $Project, "--mcp-port=$GamePort") -LogName 'game'
    $gamePid = $script:GameHandle.Process.Id
    Check 'E6_7_game_endpoint_ready' (Wait-ForPump -Port $GamePort) ("game on {0} (pid {1}) answered GET /mcp with +20 frames three times" -f $GamePort, $gamePid)

    $gameList = Invoke-Curl -Id 'E6_game_tools_list' -Json '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' -Port $GamePort
    $gameToolNames = @()
    try { $gameToolNames = @((ConvertFrom-Json $gameList).result.tools | ForEach-Object { [string]$_.name }) } catch { }
    Check 'E6_8_log_tools_are_editor_scope' (($gameToolNames -notcontains 'editor_get_errors') -and ($gameToolNames -notcontains 'editor_get_output_log')) `
        ("game tools/list carries {0} tools; editor_get_errors present={1}, editor_get_output_log present={2} (both are scope=editor, so a game process must not carry them)" -f `
            $gameToolNames.Count, ($gameToolNames -contains 'editor_get_errors'), ($gameToolNames -contains 'editor_get_output_log'))
    $gameLogCall = Invoke-Tool -Id 'E6_game_calls_the_log_tool' -Tool 'editor_get_errors' -Arguments @{} -Port $GamePort
    Check 'E6_9_game_endpoint_refuses_the_log_tool' ((Get-ErrorCode $gameLogCall) -eq -32601) `
        ("game 9889 editor_get_errors -> code={0} message='{1}' (the editor-scope tools are not registered there at all)" -f (Get-ErrorCode $gameLogCall), (Get-ErrorMessage $gameLogCall))

    # A marker produced *later* by the game process through its own endpoint, so
    # the file has something that can only have come from that process.
    $gameLateMarker = @'
print("MCP026-GAME-LATE-MARKER")
return 1
'@
    $gameMarker = Invoke-Tool -Id 'E6_game_late_marker' -Tool 'running_game_execute_gdscript' -Arguments @{ code = $gameLateMarker } -Port $GamePort
    $gameMarkerPayload = Get-Payload $gameMarker
    Check 'E6_10_game_marker_written' ($null -ne $gameMarkerPayload) ("running_game_execute_gdscript -> {0}" -f (ConvertTo-CompactJson $gameMarkerPayload))
    Start-Sleep -Milliseconds 1500

    # While the game process is alive it is the holder of that file, and Godot's
    # own write handle can deny readers (`file_access_windows.cpp` opens with
    # `_SH_DENYW`/`_SH_DENYRW` when backup saves are enabled). That is the
    # *natural* form of the window in which the pre-TASK-026 reader answered
    # `-32603`; it is recorded as an observation here and reproduced
    # deterministically with an explicit exclusive handle in section (6).
    $liveLogFile = Resolve-LogFile
    $writerHoldsIt = $false
    try {
        if ($null -ne $liveLogFile) {
            [IO.File]::ReadAllText($liveLogFile) | Out-Null
        }
    } catch {
        $writerHoldsIt = $true
    }
    Note ("observation: '{0}' readable from outside while the game process is alive = {1}" -f $liveLogFile, (-not $writerHoldsIt))

    # The E-6 cure: the editor endpoint, asked again while the game is writing,
    # still answers with its own lines and the game's lines are NOT in them.
    $editorOut2 = Invoke-Tool -Id 'E6_editor_output_log_after_game' -Tool 'editor_get_output_log' -Arguments @{ max_lines = 500 }
    $editorOut2Payload = Get-Payload $editorOut2
    $editorOut2Lines = @()
    if ($null -ne $editorOut2Payload) { $editorOut2Lines = @($editorOut2Payload.lines | ForEach-Object { [string]$_ }) }
    $editorOut2Text = $editorOut2Lines -join "`n"
    Check 'E6_12_editor_endpoint_does_not_answer_the_game_lines' `
        (($editorOut2Payload.source -eq 'editor_log') -and ($editorOut2Payload.in_process -eq $true) `
            -and ([int]$editorOut2Payload.pid -ne $gamePid) `
            -and (-not $editorOut2Text.Contains('MCP026-GAME-MARKER')) -and (-not $editorOut2Text.Contains('MCP026-GAME-ERROR')) -and (-not $editorOut2Text.Contains('MCP026-GAME-LATE-MARKER'))) `
        ("source={0} in_process={1} pid={2} (game pid {3}); GAME markers in the editor answer: {4}" -f $editorOut2Payload.source, $editorOut2Payload.in_process, $editorOut2Payload.pid, $gamePid, `
            (ConvertTo-CompactJson @($editorOut2Lines | Where-Object { $_ -like '*MCP026-GAME*' })))
    $editorErr2 = Invoke-Tool -Id 'E6_editor_errors_after_game' -Tool 'editor_get_errors' -Arguments @{ max_lines = 500 }
    $editorErr2Payload = Get-Payload $editorErr2
    $editorErr2Lines = @()
    if ($null -ne $editorErr2Payload) { $editorErr2Lines = @($editorErr2Payload.errors | ForEach-Object { [string]$_ }) }
    Check 'E6_13_editor_errors_do_not_answer_the_game_errors' `
        ((-not (($editorErr2Lines -join "`n").Contains('MCP026-GAME-ERROR'))) -and ([int]$editorErr2Payload.pid -eq $editorEnginePid)) `
        ("editor_get_errors pid={0}; GAME errors in the editor answer: {1}" -f $editorErr2Payload.pid, (ConvertTo-CompactJson @($editorErr2Lines | Where-Object { $_ -like '*MCP026-GAME*' })))

    # =====================================================================
    # (4) E-9 on the game endpoint: the same tool, the same engine check.
    # =====================================================================
    Note ''
    Note '--- (4) E-9 on 9889: the same stored values from the game endpoint ---'
    $gameRead = Invoke-Tool -Id 'E9_game_read_gradient' -Tool 'project_read_resource' -Arguments @{ path = 'res://resources/gradient.tres' } -Port $GamePort
    $gamePayload = Get-Payload $gameRead
    $gameNames = @()
    if ($null -ne $gamePayload) { $gameNames = Get-PropertyNames $gamePayload.properties }
    Check 'E9_10_game_endpoint_answers_the_same_stored_values' `
        (($null -ne $gamePayload) -and ((@($gameNames | Sort-Object) -join ',') -ceq ($toolNames -join ',')) -and (Test-ValueEqual $gamePayload.properties.colors $stored.colors)) `
        ("game properties = [{0}] (editor: [{1}]); colors equal={2}" -f (@($gameNames | Sort-Object) -join ','), ($toolNames -join ','), (Test-ValueEqual $gamePayload.properties.colors $stored.colors))
    $gameCross = Invoke-Tool -Id 'E9_game_engine_storage_names' -Tool 'running_game_execute_gdscript' -Arguments @{ code = $crossCheck } -Port $GamePort
    $gameCrossPayload = Get-Payload $gameCross
    $gameEngineNames = @()
    if ($null -ne $gameCrossPayload -and $null -ne $gameCrossPayload.result) { $gameEngineNames = @($gameCrossPayload.result | ForEach-Object { [string]$_ }) }
    Check 'E9_11_game_keys_equal_the_engines_storage_list' ((@($gameEngineNames | Sort-Object) -join ',') -ceq ($toolNames -join ',')) `
        ("game engine STORAGE = [{0}]" -f ((@($gameEngineNames | Sort-Object)) -join ','))

    # =====================================================================
    # (5) The zero-string-surgery chain: read -> write -> re-read, both ends.
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
    # segment 1 (editor): read the resource's stored values
    $c1 = Invoke-Tool -Id 'C1_read_gradient' -Tool 'project_read_resource' -Arguments @{ path = 'res://resources/gradient.tres' }
    $c1p = Get-Payload $c1
    $chainSteps.Add(("1 project_read_resource -> .properties = {0} (string ops: 0)" -f (ConvertTo-CompactJson $c1p.properties)))

    # segment 2 (editor): the whole bag goes straight back in
    $c2 = Invoke-Tool -Id 'C2_edit_gradient' -Tool 'project_edit_resource' -Arguments @{ path = 'res://resources/gradient.tres'; properties = $c1p.properties }
    $c2p = Get-Payload $c2
    $chainSteps.Add(("2 project_edit_resource(properties = step1 .properties) -> code={0} .changed.colors.new = {1} (string ops: 0)" -f (Get-ErrorCode $c2), (ConvertTo-CompactJson $c2p.changed.colors.new)))

    # segment 3 (editor): and it reads back the same
    $c3 = Invoke-Tool -Id 'C3_reread_gradient' -Tool 'project_read_resource' -Arguments @{ path = 'res://resources/gradient.tres' }
    $c3p = Get-Payload $c3
    $chainSteps.Add(("3 project_read_resource -> .properties.colors = {0} (string ops: 0)" -f (ConvertTo-CompactJson $c3p.properties.colors)))

    # segment 4 (game): the same read on the other endpoint
    $c4 = Invoke-Tool -Id 'C4_game_read_gradient' -Tool 'project_read_resource' -Arguments @{ path = 'res://resources/gradient.tres' } -Port $GamePort
    $c4p = Get-Payload $c4
    $chainSteps.Add(("4 running_game endpoint project_read_resource -> .properties.colors = {0} (string ops: 0)" -f (ConvertTo-CompactJson $c4p.properties.colors)))

    # segment 5 (game): back in, in the game process
    $c5 = Invoke-Tool -Id 'C5_game_edit_gradient' -Tool 'project_edit_resource' -Arguments @{ path = 'res://resources/gradient.tres'; properties = @{ colors = $c4p.properties.colors } } -Port $GamePort
    $c5p = Get-Payload $c5
    $chainSteps.Add(("5 game endpoint project_edit_resource(colors = step4 .properties.colors) -> code={0} .changed.colors.new = {1} (string ops: 0)" -f (Get-ErrorCode $c5), (ConvertTo-CompactJson $c5p.changed.colors.new)))

    # segment 6 (game): re-read
    $c6 = Invoke-Tool -Id 'C6_game_reread_gradient' -Tool 'project_read_resource' -Arguments @{ path = 'res://resources/gradient.tres' } -Port $GamePort
    $c6p = Get-Payload $c6
    $chainSteps.Add(("6 game endpoint project_read_resource -> .properties.colors = {0} (string ops: 0)" -f (ConvertTo-CompactJson $c6p.properties.colors)))
    # CHAIN-END

    $chainOk = ($null -ne $c1p) -and ($null -ne $c2p) -and ($null -ne $c3p) -and ($null -ne $c4p) -and ($null -ne $c5p) -and ($null -ne $c6p) `
        -and ((Get-ErrorCode $c2) -eq 0) -and ((Get-ErrorCode $c5) -eq 0) `
        -and (Test-ValueEqual $c2p.changed.colors.new $c1p.properties.colors) `
        -and (Test-ValueEqual $c3p.properties.colors $c1p.properties.colors) `
        -and (Test-ValueEqual $c4p.properties.colors $c1p.properties.colors) `
        -and (Test-ValueEqual $c5p.changed.colors.new $c4p.properties.colors) `
        -and (Test-ValueEqual $c6p.properties.colors $c1p.properties.colors)
    Check 'E9_12_chain_read_write_reread_six_steps' $chainOk ("{0}" -f ($chainSteps -join ' || '))

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
    Check 'E9_13_chain_region_has_no_string_surgery_tokens' ($found.Count -eq 0) `
        ("forbidden tokens in the chain region: {0} (checked: {1})" -f $foundReport, ($forbidden -join ' '))

    # =====================================================================
    # (6) The rotation window, reproduced: the shared file held exclusively.
    #
    # The game is stopped first so that the only holder is this script. In the
    # pre-TASK-026 code the editor endpoint reads that file for its log tools
    # and answers `-32603` here; the fixed code does not depend on the file at
    # all in an editor process.
    # =====================================================================
    Note ''
    Note '--- (6) the rotation window: the shared log file is unreadable ---'
    Stop-Engine $script:GameHandle
    $script:GameHandle = $null
    Start-Sleep -Milliseconds 2500

    # The external half: with both writers stopped, the file itself is read by
    # this script (never through the module) and it holds the game process's
    # lines - the channel the editor endpoint used to answer *from*.
    $logFile = Resolve-LogFile
    $logFileText = ''
    if ($null -ne $logFile -and (Test-Path $logFile)) { $logFileText = [IO.File]::ReadAllText($logFile) }
    Check 'E6_11_the_shared_file_holds_the_game_process_lines' `
        (($null -ne $logFile) -and $logFileText.Contains('MCP026-GAME-MARKER') -and $logFileText.Contains('MCP026-GAME-ERROR') -and $logFileText.Contains('MCP026-GAME-LATE-MARKER') -and $logFileText.Contains("listening on 127.0.0.1:$GamePort")) `
        ("file='{0}' sha256={1}; contains GAME-MARKER={2} GAME-ERROR={3} GAME-LATE-MARKER={4} GAME-listening-line={5}" -f `
            $logFile, (Get-FileSha $logFile), $logFileText.Contains('MCP026-GAME-MARKER'), $logFileText.Contains('MCP026-GAME-ERROR'), $logFileText.Contains('MCP026-GAME-LATE-MARKER'), $logFileText.Contains("listening on 127.0.0.1:$GamePort"))

    $lock = $null
    $lockPath = $logFile
    if ($null -ne $lockPath) { $lock = [IO.File]::Open($lockPath, 'Open', 'ReadWrite', 'None') }
    Check 'E6_14_the_shared_file_is_held_exclusively' ($null -ne $lock) ("exclusive handle on '{0}' (no other process may open it)" -f $lockPath)
    try {
        $lockedOut = Invoke-Tool -Id 'E6_locked_output_log' -Tool 'editor_get_output_log' -Arguments @{ max_lines = 50 }
        $lockedPayload = Get-Payload $lockedOut
        $lockedErr = Invoke-Tool -Id 'E6_locked_errors' -Tool 'editor_get_errors' -Arguments @{ max_lines = 50 }
        $lockedErrPayload = Get-Payload $lockedErr
        Check 'E6_15_a_locked_shared_file_is_not_a_-32603' `
            (((Get-ErrorCode $lockedOut) -eq 0) -and ((Get-ErrorCode $lockedErr) -eq 0)) `
            ("editor_get_output_log code={0} message='{1}'; editor_get_errors code={2} message='{3}'" -f `
                (Get-ErrorCode $lockedOut), (Get-ErrorMessage $lockedOut), (Get-ErrorCode $lockedErr), (Get-ErrorMessage $lockedErr))
        Check 'E6_16_a_locked_shared_file_does_not_change_the_source' `
            (($lockedPayload.source -eq 'editor_log') -and ($lockedPayload.available -eq $true) -and ($lockedPayload.in_process -eq $true) -and ($lockedErrPayload.source -eq 'editor_log')) `
            ("source={0} available={1} in_process={2} (the editor process never reads that file: main.cpp:2287/2292 leaves the editor out of file logging)" -f `
                $lockedPayload.source, $lockedPayload.available, $lockedPayload.in_process)
    } finally {
        if ($null -ne $lock) { $lock.Dispose(); $lock = $null }
    }

    # =====================================================================
    # (7) The honest-empty shape, and the file the fallback would read.
    # =====================================================================
    Note ''
    Note '--- (7) the source block on a process with no editor log ---'
    $statusProbe = Get-StatusProbe -Port $EditorPort
    Check 'E6_17_editor_status_confirms_editor_process' ($statusProbe.is_editor -eq $true) ("GET /mcp -> is_editor={0} port={1}" -f $statusProbe.is_editor, $EditorPort)
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
