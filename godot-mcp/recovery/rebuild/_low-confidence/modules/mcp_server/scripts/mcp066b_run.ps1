# =============================================================================
#  mcp066b_run.ps1 -- TASK-066 ROLE B: rerun the whole live chain + criteria 5/6
#  + the eight round-3 blanks, on the C# breakout project role A built.
#
#  Pure ASCII. Products go to absolute paths under
#  F:\RustProjects\godot-mcp-pro\code\godot\modules\mcp_server\docs\reports\
#  evidence\task066b\ ; %TEMP%\mcp066b is scratch only and is copied in by
#  mcp066b_finalize.ps1. NOTHING under modules/mcp_server/tools|tests, the
#  contract, the map or the group lists is ever written.
#
#  Phases
#    P0 preflight: ports free, contract sha, A's ten fixture hashes re-checked,
#       project copied byte for byte, --import with checked exit code, watcher
#       started (mcp_watch_run.ps1, stop_reason must come out as `marker`).
#    P1 editor session A (windowed, --mcp-capture=every_call scale=2):
#       criterion 5 (scope, 3 calls per scope, set algebra), B4 (scope x
#       node_path), B5 (scene [connection] vs run-time connect()), B6 (the diff
#       tool's four refusal paths), criterion 6 (changed:true / changed:false,
#       three routes), the evidence-guard snapshot pair.
#    P2 editor session B: scale=1 + --mcp-capture-diff-image=on (B3 + B2 half).
#    P3 editor session C: scale=4 (B3).
#    P4 editor session D: --mcp-capture=on_error (B2 half).
#    P5 game session (windowed, no --headless): the live chain on the C# project
#       (input -> paddle/ball per-frame samples, bricks really decrease, score
#       really changes with an in-process assert), criterion 6 game side, B1
#       windowed capture family.
#    P6: marker, watcher summary, independent pixel recomputation, uniqueness
#       audit, manifest, closing git/port checks. (mcp066b_finalize.ps1 can be
#       re-run standalone; it only reads scratch and writes evidence.)
# =============================================================================

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'mcp066b_env.ps1')

$DirPre = Join-Path $EvidenceRoot 'preflight'
$DirScope = Join-Path $EvidenceRoot 'scope'
$DirCap = Join-Path $EvidenceRoot 'capture'
$DirGame = Join-Path $EvidenceRoot 'game'
$DirShots = Join-Path $EvidenceRoot 'shots'
$DirProbe = Join-Path $EvidenceRoot 'probes'
$DirLogs = Join-Path $EvidenceRoot 'process-logs'
$DirWatch = Join-Path $EvidenceRoot 'watch'
$DirTraces = Join-Path $EvidenceRoot 'traces'

$script:PixelPairs = New-Object System.Collections.ArrayList
$script:Findings = New-Object System.Collections.ArrayList
$script:StartedAt = Get-Date
$script:EditorProcess = $null
$script:GameProcess = $null
$script:WatcherProcess = $null

function Note-Finding([string]$Id, [string]$Text) {
    [void]$script:Findings.Add([pscustomobject]@{ id = $Id; text = $Text })
    Add-Heartbeat ('FINDING ' + $Id + ' ' + $Text)
}

# A terminating error must not leave an engine process (or the watcher) behind:
# stop only PIDs this run started, write the marker so the watcher records its
# own verdict, and exit non-zero.
trap {
    $message = $_.Exception.Message
    Write-Host ('B066 TRAP ' + $message)
    try { Add-Heartbeat ('TRAP ' + $message) } catch { }
    try { Stop-OwnProcess -Process $script:EditorProcess -LogPath '' } catch { }
    try { Stop-OwnProcess -Process $script:GameProcess -LogPath '' } catch { }
    try {
        if (-not (Test-Path -LiteralPath $MarkerFile)) {
            [IO.File]::WriteAllText($MarkerFile, ('task=066 role=B aborted=' + $message + "`n"), (New-Object Text.UTF8Encoding($false)))
        }
    } catch { }
    try {
        if ($null -ne $script:WatcherProcess -and -not $script:WatcherProcess.HasExited) {
            $null = $script:WatcherProcess.WaitForExit(120000)
        }
    } catch { }
    exit 1
}

function Write-JsonEvidence([string]$Directory, [string]$Leaf, $Object, [string]$Id = '') {
    $json = ($Object | ConvertTo-Json -Depth 30)
    return (Write-McpEvidenceText -Directory $Directory -Leaf $Leaf -Text $json -Extension '.json' -Id $Id)
}

function Get-BodySha($Call) {
    if ($null -eq $Call.Json -or $null -eq $Call.Json.result -or $null -eq $Call.Json.result.content) { return '' }
    return (Get-McpEvidenceContentSha256 -Text ([string]$Call.Json.result.content[0].text))
}

function Get-Wall([string]$Stamp) { return $Stamp }

# ---------------------------------------------------------------------------
#  Watcher (mcp_watch_run.ps1). Launched through -EncodedCommand because the
#  natural `-File ... -TracePath a -TracePath b` form cannot bind twice and
#  a single comma string is silently read as ONE path (BREAKOUT-FINDINGS-R3 F2).
# ---------------------------------------------------------------------------
function Start-Watcher {
    Ensure-Dir $WatchOutDir | Out-Null
    Remove-Item -LiteralPath $MarkerFile -Force -ErrorAction SilentlyContinue
    $cmd = "& '$WatcherPath' -Marker '$MarkerFile' -TracePath '$TraceGlob','$ProgressTrace' -TimeoutSec 2700 -StaleSec 0 -IntervalSec 5 -OutDir '$WatchOutDir'"
    $enc = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))
    $out = Join-Path $ScratchRoot 'watch-stdout.txt'
    $err = Join-Path $ScratchRoot 'watch-stderr.txt'
    $p = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-EncodedCommand', $enc) -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
    Add-Heartbeat ('watcher started pid=' + $p.Id + ' command=' + $cmd)
    return $p
}

# ===========================================================================
#  P0 -- preflight
# ===========================================================================
Ensure-Dir $ScratchRoot | Out-Null
Ensure-Dir $IoRoot | Out-Null
Ensure-Dir $DirPre | Out-Null
Add-Heartbeat 'P0 preflight start'
Ensure-Dir $DirScope | Out-Null
Ensure-Dir $DirCap | Out-Null
Ensure-Dir $DirGame | Out-Null
Ensure-Dir $DirShots | Out-Null
Ensure-Dir $DirProbe | Out-Null
Ensure-Dir $DirLogs | Out-Null
Ensure-Dir $DirTraces | Out-Null

$portsBefore = Get-ListeningPorts
Add-Check 'p0_port_9877_free_before' (-not ($portsBefore -contains 9877)) ('listening_ports=' + ($portsBefore -join ','))
Add-Check 'p0_ports_9888_9889_free_before' ((-not ($portsBefore -contains 9888)) -and (-not ($portsBefore -contains 9889))) ('listening_ports=' + ($portsBefore -join ','))

$contractPath = Join-Path $McpRoot 'docs\tools_list.renamed.json'
$contractSha = Get-Sha256OfFile $contractPath
$contractShaExpected = 'd4e53b43840b6537af9dfbefdc77e7fb4ed6202ee23f3016503a7a53953e7ecd'
Add-Check 'p0_contract_sha_is_the_recorded_one' ($contractSha -eq $contractShaExpected) ('sha256=' + $contractSha)

$head = (& git -C $RepoRoot rev-parse HEAD).Trim()
$branch = (& git -C $RepoRoot branch --show-current).Trim()
Add-Heartbeat ('P0 head=' + $head + ' branch=' + $branch + ' contract=' + $contractSha)

$diffTools = @(& git -C $RepoRoot diff --stat HEAD -- modules/mcp_server/tools modules/mcp_server/tests modules/mcp_server/docs/tools_list.renamed.json modules/mcp_server/docs/tool-rename-map.json modules/mcp_server/docs/tool-groups.json)
Add-Check 'p0_module_tree_not_modified_before' (@($diffTools | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count -eq 0) ('git diff --stat lines=' + @($diffTools).Count)
# `scripts/**` is allowed to differ (this run's own harness scripts are new).
$diffScripts = @(& git -C $RepoRoot status --porcelain modules/mcp_server/scripts)
Add-Heartbeat ('scripts dir status entries=' + @($diffScripts).Count + ' : ' + (@($diffScripts) -join ' ; '))

# --- A's reported fixture hashes, re-checked on disk -----------------------
$aExpect = [ordered]@{
    'project.godot'      = '4973072b5a7432cb00f65e5c2099e346c9d30c3760d4f1c9317a15a514627f2b'
    'scenes\main.tscn'   = 'd33b89311f018f41861e9a2add9b8afa2fb707c32ae470cd83925570bdb67b35'
    'McpBreakoutCs.csproj' = '2d35333d19e4557de7337020ad656bf724622dee9560cf84cb3b18feed231751'
    'NuGet.config'       = 'b1654e727e4ed844e47bee54ffb3304afcc38fc406fec761265d719c47b83d28'
    'scripts\Main.cs'    = '14c4aaa24dd1b43fdc16368f87b8aa3539a2c97d10d91fc70d087ecc50105aae'
    'scripts\Paddle.cs'  = '14934efb2b3a076db8133f7915fc7c1a3c3e3ef2ef20a181cb4f32562c107cd2'
    'scripts\Ball.cs'    = '77385665f98001d60e00d728f98e9ebe9223f216cea12139c28b36ca00645c5a'
    'scripts\Brick.cs'   = '817c1924f55056e31bb7fa2c1b2208c00c67b4fe32895aa8790e9d4581ede48a'
    'scripts\CsVerdict.cs' = '427219c58a2bd2b38f59e147d170beece388c852f30a8e5531b22b303f3fa05f'
    'scripts\CsVerdict2.cs' = 'f5c6744908a4545f9b20b98a25836a1e1063a23afb0962792737ce67a3e9c57a'
}
$aRows = New-Object System.Collections.ArrayList
$aMatch = 0
foreach ($key in $aExpect.Keys) {
    $full = Join-Path $ProjSrc $key
    $actual = ''
    $ok = $false
    if (Test-Path -LiteralPath $full) {
        $actual = Get-Sha256OfFile $full
        $ok = ($actual -eq $aExpect[$key])
    }
    if ($ok) { $aMatch++ }
    [void]$aRows.Add([pscustomobject]@{ file = $key; expected = $aExpect[$key]; actual = $actual; match = $ok })
}
Add-Check 'p0_a_reported_hashes_match_on_disk' ($aMatch -eq $aExpect.Count) ('matched=' + $aMatch + '/' + $aExpect.Count)
$null = Write-JsonEvidence $DirPre 'p0_a_reported_hashes' ([pscustomobject]@{ rows = $aRows; matched = $aMatch; total = $aExpect.Count }) 

# --- copy the project byte for byte ---------------------------------------
if (Test-Path -LiteralPath $Proj) { Remove-Item -LiteralPath $Proj -Recurse -Force }
Copy-Item -LiteralPath $ProjSrc -Destination $Proj -Recurse -Force
Ensure-Dir $Proj | Out-Null

$srcFiles = @(Get-ChildItem -LiteralPath $ProjSrc -Recurse -File | Where-Object { $_.FullName -notmatch '\\\.godot\\' })
$copyMismatch = New-Object System.Collections.ArrayList
foreach ($f in $srcFiles) {
    $rel = $f.FullName.Substring($ProjSrc.Length)
    $dst = $Proj + $rel
    if (-not (Test-Path -LiteralPath $dst)) { [void]$copyMismatch.Add('missing:' + $rel); continue }
    if ((Get-Sha256OfFile $f.FullName) -ne (Get-Sha256OfFile $dst)) { [void]$copyMismatch.Add('differs:' + $rel) }
}
Add-Check 'p0_project_copy_is_byte_identical' ($copyMismatch.Count -eq 0) ('files=' + $srcFiles.Count + ' mismatch=' + $copyMismatch.Count + ' ' + (@($copyMismatch) -join ';'))

# --- import the copy with a checked exit code ------------------------------
$importOk = $false
$importDetail = ''
try {
    $imp = Import-McpProject -Engine $MonoExe -Path $Proj -LogDirectory $DirLogs -Name 'b066_import' -NoPort
    $importOk = ($imp.exit_code -eq 0)
    $importDetail = 'exit=' + $imp.exit_code + ' attempts=' + $imp.attempts + ' log=' + $imp.log
} catch {
    $importDetail = 'import threw: ' + $_.Exception.Message
}
Add-Check 'p0_import_exit_zero' $importOk $importDetail

# --- watcher ---------------------------------------------------------------
$script:WatcherProcess = Start-Watcher
Start-Sleep -Seconds 3
$watchAlive = ($null -ne $script:WatcherProcess) -and (-not $script:WatcherProcess.HasExited)
Add-Check 'p0_watcher_started' $watchAlive ('pid=' + $(if ($null -ne $script:WatcherProcess) { $script:WatcherProcess.Id } else { 'none' }))
Add-Heartbeat 'P0 preflight done'

# ===========================================================================
#  Helpers shared by the editor sessions
# ===========================================================================
function Start-EditorSession {
    param(
        [Parameter(Mandatory = $true)][string]$Tag,
        [Parameter(Mandatory = $true)][string]$TraceFile,
        [Parameter(Mandatory = $true)][string]$CaptureDir,
        [Parameter(Mandatory = $true)][string[]]$CaptureArgs
    )
    $outLog = Join-Path $DirLogs ('editor-' + $Tag + '.out.log.txt')
    $errLog = Join-Path $DirLogs ('editor-' + $Tag + '.err.log.txt')
    $engineArgs = @('-e', '--path', $Proj, ('--mcp-port=' + $EditorPort), ('--mcp-trace=' + (To-Fwd $TraceFile)), ('--mcp-capture-dir=' + $CaptureDir)) + $CaptureArgs
    Reset-McpCallSeq
    $p = Start-OwnProcess -Exe $MonoExe -EngineArgs $engineArgs -OutLog $outLog -ErrLog $errLog
    $script:EditorProcess = $p
    Add-Heartbeat ('editor[' + $Tag + '] started pid=' + $p.Id + ' args=' + ($engineArgs -join ' '))
    $ready = Wait-Port -Port $EditorPort -TimeoutSec 90
    $capEnabled = Wait-LogLine -Path $outLog -Pattern '\[MCP\] capture enabled' -TimeoutSec 60
    Start-Sleep -Seconds 2
    return [pscustomobject]@{ Process = $p; OutLog = $outLog; ErrLog = $errLog; Args = $engineArgs; PortReady = $ready; CaptureLine = $capEnabled }
}

function Stop-EditorSession($Session) {
    if ($null -ne $Session) { Stop-OwnProcess -Process $Session.Process -LogPath $Session.OutLog }
    $script:EditorProcess = $null
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline) {
        if (-not ((Get-ListeningPorts) -contains $EditorPort)) { break }
        Start-Sleep -Milliseconds 500
    }
    Start-Sleep -Seconds 1
}

function Open-Scene2D {
    param([int]$Port, [string]$Dir, [string]$Prefix)
    $open = Invoke-Tool -Port $Port -Tool 'editor_open_scene' -Arguments @{ path = 'res://scenes/main.tscn' } -Directory $Dir -Leaf ($Prefix + '_open_scene')
    $two = Invoke-Tool -Port $Port -Tool 'editor_execute_gdscript' -Arguments @{ code = "EditorInterface.set_main_screen_editor(`"2D`")`nreturn `"ok`"" } -Directory $Dir -Leaf ($Prefix + '_main_screen_2d')
    $tree = Invoke-Tool -Port $Port -Tool 'editor_get_scene_tree' -Arguments @{ max_depth = -1 } -Directory $Dir -Leaf ($Prefix + '_scene_tree')
    return [pscustomobject]@{ Open = $open; TwoD = $two; Tree = $tree }
}

function Invoke-ScopeCall {
    param([int]$Port, [string]$Dir, [string]$Leaf, [string]$Scope, [string]$NodePath, [string]$SignalName)
    $callArgs = [ordered]@{}
    if (-not [string]::IsNullOrEmpty($Scope)) { $callArgs['scope'] = $Scope }
    if (-not [string]::IsNullOrEmpty($NodePath)) { $callArgs['node_path'] = $NodePath }
    if (-not [string]::IsNullOrEmpty($SignalName)) { $callArgs['signal_name'] = $SignalName }
    return (Invoke-Tool -Port $Port -Tool 'editor_list_signal_connections' -Arguments $callArgs -Directory $Dir -Leaf $Leaf)
}

function Get-ConnSet($Call) {
    $body = Get-ToolBody $Call
    $out = @()
    if ($null -eq $body) { return @() }
    foreach ($c in @($body.connections)) {
        $out += ('{0}|{1}|{2}|{3}' -f [string]$c.source, [string]$c.signal, [string]$c.target, [string]$c.method)
    }
    return @($out)
}

function Get-ScopeCounts($Call) {
    $body = Get-ToolBody $Call
    if ($null -eq $body) { return $null }
    return $body.counts
}

# `running_game_get_node_properties` answers {"node_path","properties":{...},"type"}:
# the values live under `properties`, not at the top level of the body.
function Get-PropsOf($Call) {
    $body = Get-ToolBody $Call
    if ($null -eq $body) { return $null }
    return $body.properties
}

function Get-CaptureForCall($TraceLines, $Call) {
    return (Resolve-Capture -TraceLines $TraceLines -Tool $Call.Tool -Ordinal $Call.ToolOrdinal)
}

# Pair "my k-th call of tool T in this process" with "the k-th tools/call request
# of tool T in the trace", then read that request's own seq and find the capture
# line that repeats it. No text matching is involved anywhere.
function Resolve-Capture {
    param([Parameter(Mandatory = $true)]$TraceLines, [Parameter(Mandatory = $true)][string]$Tool, [int]$Ordinal = 1)
    $reqs = @(Get-ToolRequests $TraceLines | Where-Object { $_.tool -eq $Tool })
    if ($reqs.Count -lt $Ordinal) { return $null }
    return (Get-CaptureBySeq $TraceLines ([int]$reqs[$Ordinal - 1].seq))
}

function Add-PixelPair {
    param(
        [string]$Label,
        [string]$BeforeRes,
        [string]$AfterRes,
        $CaptureLine,
        $ToolBody,
        [int]$Threshold = 10
    )
    $beforeAbs = Globalize-ResPath $BeforeRes
    $afterAbs = Globalize-ResPath $AfterRes
    if ($null -eq $CaptureLine) { return $null }
    if ((-not (Test-Path -LiteralPath $beforeAbs)) -or (-not (Test-Path -LiteralPath $afterAbs))) {
        Add-Heartbeat ('pixel pair skipped (missing png) label=' + $Label + ' before=' + $beforeAbs + ' after=' + $afterAbs)
        return $null
    }
    $entry = [pscustomobject]@{
        label               = $Label
        before              = $beforeAbs
        after               = $afterAbs
        before_res          = $BeforeRes
        after_res           = $AfterRes
        threshold           = $Threshold
        before_sha256       = (Get-Sha256OfFile $beforeAbs)
        after_sha256        = (Get-Sha256OfFile $afterAbs)
        log_changed_pixels  = [int]$CaptureLine.changed_pixels
        log_total_pixels    = [int]$CaptureLine.total_pixels
        log_changed         = [bool]$CaptureLine.changed
        tool_changed_pixels = $null
        tool_total_pixels   = $null
        tool_identical      = $null
    }
    if ($null -ne $ToolBody) {
        $entry.tool_changed_pixels = [int]$ToolBody.changed_pixels
        $entry.tool_total_pixels = [int]$ToolBody.total_pixels
        $entry.tool_identical = [bool]$ToolBody.identical
    }
    [void]$script:PixelPairs.Add($entry)
    return $entry
}

# ===========================================================================
#  P1 -- editor session A
# ===========================================================================
Add-Heartbeat 'P1 editor session A start'
$traceA = Join-Path $ScratchRoot 'trace-editor-a.jsonl'
$sessA = Start-EditorSession -Tag 'a' -TraceFile $traceA -CaptureDir 'res://mcp066b_shots' -CaptureArgs @('--mcp-capture=every_call', '--mcp-capture-viewport=2d', '--mcp-capture-scale=2')
Add-Check 'p1_editor_boot_port_ready' $sessA.PortReady ('args=' + ($sessA.Args -join ' '))
Add-Check 'p1_editor_boot_capture_enabled' $sessA.CaptureLine (First-LineMatching -Path $sessA.OutLog -Pattern 'capture enabled')

$listA = Invoke-Raw -Port $EditorPort -Method 'tools/list' -Directory $DirPre -Leaf 'p1_editor_tools_list'
$listACount = @($listA.Json.result.tools).Count
Add-Check 'p1_editor_tools_list_is_153' ($listACount -eq 153) ('count=' + $listACount)

$openA = Open-Scene2D -Port $EditorPort -Dir $DirCap -Prefix 'p1'
$openBody = Get-ToolBody $openA.Open
Add-Check 'p1_scene_opened' ([bool]$openBody.opened) ('body=' + ($openBody | ConvertTo-Json -Compress -Depth 5))
$treeBody = Get-ToolBody $openA.Tree
$treeJson = ($treeBody | ConvertTo-Json -Compress -Depth 30)
$nodesSeen = @()
foreach ($n in @('Main', 'Paddle', 'Ball', 'WallTop', 'Bricks', 'Brick0', 'HUD', 'ScoreLabel', 'ProbeTimer')) {
    if ($treeJson -like ('*"' + $n + '"*')) { $nodesSeen += $n }
}
Add-Check 'p1_scene_tree_has_expected_nodes' ($nodesSeen.Count -ge 8) ('found=' + ($nodesSeen -join ',') + ' body_bytes=' + $treeJson.Length)

# --- evidence guard snapshot pair: main.tscn before -> between -> after -----
$sceneAbs = Join-Path $Proj 'scenes\main.tscn'
$pairA = Write-McpEvidenceSnapshotPair -Directory $DirCap -Leaf 'p1_main_tscn' -Extension '.tscn' `
    -Before { [IO.File]::ReadAllBytes($sceneAbs) } `
    -Between {
        $null = Invoke-Tool -Port $EditorPort -Tool 'editor_set_node_property' -Arguments @{ path = 'WallTop'; property = 'position'; value = @{ x = 0; y = 40 } } -Directory $DirCap -Leaf 'p1_pair_set_position'
        $null = Invoke-Tool -Port $EditorPort -Tool 'editor_save_scene' -Arguments @{ path = 'res://scenes/main.tscn' } -Directory $DirCap -Leaf 'p1_pair_save_scene'
    } `
    -After { [IO.File]::ReadAllBytes($sceneAbs) }
Add-Check 'p1_snapshot_pair_before_after_differ' (-not $pairA.Identical) ('before=' + (Sha8 $pairA.BeforeSha256) + ' after=' + (Sha8 $pairA.AfterSha256) + ' before_bytes=' + (Get-Item $pairA.Before).Length + ' after_bytes=' + (Get-Item $pairA.After).Length)

# --- criterion 6, editor side ---------------------------------------------
$readA1 = Invoke-Tool -Port $EditorPort -Tool 'editor_get_scene_tree' -Arguments @{ max_depth = -1 } -Directory $DirCap -Leaf 'p1_c6_read_only_a'
$readA2 = Invoke-Tool -Port $EditorPort -Tool 'editor_get_scene_tree' -Arguments @{ max_depth = -1 } -Directory $DirCap -Leaf 'p1_c6_read_only_b_replay'
$argReal6 = [ordered]@{ path = 'WallTop'; property = 'position'; value = [ordered]@{ x = 0; y = 60 } }
$real6 = Invoke-Tool -Port $EditorPort -Tool 'editor_set_node_property' -Arguments $argReal6 -Directory $DirCap -Leaf 'p1_c6_real_change'
$replay6 = Invoke-Tool -Port $EditorPort -Tool 'editor_set_node_property' -Arguments $argReal6 -Directory $DirCap -Leaf 'p1_c6_same_args_same_value_replay'
Add-Check 'p1_c6_replay_arguments_byte_identical' ($real6.ArgumentsSha256 -eq $replay6.ArgumentsSha256) ('arguments_sha256=' + $real6.ArgumentsSha256 + ' replay=' + $replay6.ArgumentsSha256)

Start-Sleep -Seconds 3
$traceLinesA = Get-TraceObjects $traceA
$capRead1 = Get-CaptureForCall $traceLinesA $readA1
$capRead2 = Get-CaptureForCall $traceLinesA $readA2
$capReal = Get-CaptureForCall $traceLinesA $real6
$capReplay = Get-CaptureForCall $traceLinesA $replay6
Add-Check 'p1_c6_capture_lines_resolved_by_seq' (($null -ne $capRead1) -and ($null -ne $capReal) -and ($null -ne $capReplay)) ('read1_seq=' + $readA1.Seq + ' real_seq=' + $real6.Seq + ' replay_seq=' + $replay6.Seq + ' resolved=' + @($capRead1, $capRead2, $capReal, $capReplay | Where-Object { $null -ne $_ }).Count + '/4')
Add-Check 'p1_c6_read_only_replays_are_changed_false' ((-not [bool]$capRead1.changed) -and (-not [bool]$capRead2.changed)) ('a=' + $capRead1.changed + ' b=' + $capRead2.changed + ' pixels=' + $capRead1.changed_pixels + '/' + $capRead2.changed_pixels)
Add-Check 'p1_c6_real_change_is_changed_true' ([bool]$capReal.changed) ('changed=' + $capReal.changed + ' pixels=' + $capReal.changed_pixels + '/' + $capReal.total_pixels + ' ratio=' + $capReal.changed_pixel_ratio)
Add-Check 'p1_c6_same_args_same_value_replay_is_changed_false' (-not [bool]$capReplay.changed) ('changed=' + $capReplay.changed + ' pixels=' + $capReplay.changed_pixels + ' replay_before_sha=' + (Sha8 ([string]$capReplay.before.sha256)) + ' replay_after_sha=' + (Sha8 ([string]$capReplay.after.sha256)))
Add-Check 'p1_c6_capture_is_windowed_done_not_unavailable' (([string]$capReal.status -eq 'done') -and ([string]$capReal.viewport -eq '2d') -and ([int]$capReal.scale -eq 2)) ('status=' + $capReal.status + ' viewport=' + $capReal.viewport + ' scale=' + $capReal.scale + ' frames_waited=' + $capReal.frames_waited)

# capture lines map one to one with the calls of this session
$reqCountA = @(Get-ToolRequests $traceLinesA).Count
$capCountA = @($traceLinesA | Where-Object { $_.event -eq 'capture' }).Count
Add-Check 'p1_capture_lines_match_call_count' ($reqCountA -eq $capCountA) ('requests=' + $reqCountA + ' captures=' + $capCountA)

# three routes: log (above), tool, independent python (later)
$beforeRes = ''
$afterRes = ''
$beforeResR = ''
$afterResR = ''
$toolBodyReal = $null
$toolBodyReplay = $null
if ($null -ne $capReal) {
    $beforeRes = [string]$capReal.before.path
    $afterRes = [string]$capReal.after.path
    $toolDiffReal = Invoke-Tool -Port $EditorPort -Tool 'editor_analyze_screenshot_diff' -Arguments @{ image_a = $beforeRes; image_b = $afterRes } -Directory $DirCap -Leaf 'p1_c6_tool_diff_real_change'
    $toolBodyReal = Get-ToolBody $toolDiffReal
}
if ($null -ne $capReplay) {
    $beforeResR = [string]$capReplay.before.path
    $afterResR = [string]$capReplay.after.path
    $toolDiffReplay = Invoke-Tool -Port $EditorPort -Tool 'editor_analyze_screenshot_diff' -Arguments @{ image_a = $beforeResR; image_b = $afterResR } -Directory $DirCap -Leaf 'p1_c6_tool_diff_replay'
    $toolBodyReplay = Get-ToolBody $toolDiffReplay
}
$toolRouteOk = ($null -ne $toolBodyReal) -and ($null -ne $capReal) -and ([int]$toolBodyReal.changed_pixels -eq [int]$capReal.changed_pixels) -and ([int]$toolBodyReal.total_pixels -eq [int]$capReal.total_pixels)
Add-Check 'p1_c6_tool_route_matches_capture_line' $toolRouteOk ('tool=' + $toolBodyReal.changed_pixels + '/' + $toolBodyReal.total_pixels + ' log=' + $capReal.changed_pixels + '/' + $capReal.total_pixels)
Add-Check 'p1_c6_tool_route_replay_is_identical' (($null -ne $toolBodyReplay) -and ([bool]$toolBodyReplay.identical) -and ([int]$toolBodyReplay.changed_pixels -eq 0)) ('identical=' + $toolBodyReplay.identical + ' pixels=' + $toolBodyReplay.changed_pixels)

if (($null -ne $capReal) -and ($null -ne $toolBodyReal)) { $null = Add-PixelPair -Label 'editor_real_change' -BeforeRes $beforeRes -AfterRes $afterRes -CaptureLine $capReal -ToolBody $toolBodyReal }
if (($null -ne $capReplay) -and ($null -ne $toolBodyReplay)) { $null = Add-PixelPair -Label 'editor_replay' -BeforeRes $beforeResR -AfterRes $afterResR -CaptureLine $capReplay -ToolBody $toolBodyReplay }

# copy the four PNGs into the evidence tree (unique names + content digest)
foreach ($item in @(
        @{ leaf = 'p1_real_change.before'; res = $beforeRes }, @{ leaf = 'p1_real_change.after'; res = $afterRes },
        @{ leaf = 'p1_replay.before'; res = $beforeResR }, @{ leaf = 'p1_replay.after'; res = $afterResR })) {
    $abs = Globalize-ResPath $item.res
    if (Test-Path -LiteralPath $abs) {
        $w = Write-McpEvidenceBytes -Directory $DirShots -Leaf $item.leaf -Bytes ([IO.File]::ReadAllBytes($abs)) -Extension '.png'
        Add-Heartbeat ('png copied ' + $item.leaf + ' sha8=' + $w.Sha8 + ' bytes=' + $w.Bytes)
    }
}
Add-Heartbeat 'P1 criterion 6 done'

# --- criterion 5: scope ----------------------------------------------------
$scopeBaseAll = @()
$scopeBaseUser = @()
$scopeBaseInt = @()
$bodyShaAll = @()
$bodyShaUser = @()
$bodyShaInt = @()
for ($i = 1; $i -le 3; $i++) {
    $cDef = Invoke-ScopeCall -Port $EditorPort -Dir $DirScope -Leaf ('p1_scope_default_' + $i) -Scope $null -NodePath $null -SignalName $null
    $cUsr = Invoke-ScopeCall -Port $EditorPort -Dir $DirScope -Leaf ('p1_scope_user_' + $i) -Scope 'user' -NodePath $null -SignalName $null
    $cInt = Invoke-ScopeCall -Port $EditorPort -Dir $DirScope -Leaf ('p1_scope_internal_' + $i) -Scope 'internal' -NodePath $null -SignalName $null
    $scopeBaseAll += , (Get-ConnSet $cDef)
    $scopeBaseUser += , (Get-ConnSet $cUsr)
    $scopeBaseInt += , (Get-ConnSet $cInt)
    $bodyShaAll += (Get-BodySha $cDef)
    $bodyShaUser += (Get-BodySha $cUsr)
    $bodyShaInt += (Get-BodySha $cInt)
}
$defSet = @($scopeBaseAll[0])
$userSet = @($scopeBaseUser[0])
$intSet = @($scopeBaseInt[0])
Add-Check 'p1_scope_default_is_three_times_byte_stable' (@($bodyShaAll | Sort-Object -Unique).Count -eq 1) ('default count=' + $defSet.Count + ' distinct body sha=' + @($bodyShaAll | Sort-Object -Unique).Count + ' sha8=' + (Sha8 ([string]$bodyShaAll[0])))
Add-Check 'p1_scope_user_is_three_times_byte_stable' (@($bodyShaUser | Sort-Object -Unique).Count -eq 1) ('user count=' + $userSet.Count + ' distinct body sha=' + @($bodyShaUser | Sort-Object -Unique).Count + ' sha8=' + (Sha8 ([string]$bodyShaUser[0])))
Add-Check 'p1_scope_internal_is_three_times_byte_stable' (@($bodyShaInt | Sort-Object -Unique).Count -eq 1) ('internal count=' + $intSet.Count + ' distinct body sha=' + @($bodyShaInt | Sort-Object -Unique).Count + ' sha8=' + (Sha8 ([string]$bodyShaInt[0])))

$union = @(@(@($userSet) + @($intSet)) | Sort-Object -Unique)
$inter = @($userSet | Where-Object { $intSet -contains $_ })
$defSorted = @($defSet | Sort-Object -Unique)
$unionSorted = @($union | Sort-Object -Unique)
Add-Check 'p1_scope_user_union_internal_equals_default' (@(Compare-Object $defSorted $unionSorted).Count -eq 0) ('default=' + $defSorted.Count + ' user=' + @($userSet | Sort-Object -Unique).Count + ' internal=' + @($intSet | Sort-Object -Unique).Count + ' union=' + $unionSorted.Count + ' user-minus-default=' + @($userSet | Where-Object { $defSet -notcontains $_ }).Count + ' internal-minus-default=' + @($intSet | Where-Object { $defSet -notcontains $_ }).Count)
Add-Check 'p1_scope_user_intersection_internal_is_empty' ($inter.Count -eq 0) ('intersection=' + $inter.Count)
$userNoClass = @($userSet | Where-Object { $_ -notmatch '::' }).Count
$intWithClass = @($intSet | Where-Object { $_ -match '::' }).Count
Add-Check 'p1_scope_user_methods_have_no_class_prefix' ($userNoClass -eq @($userSet | Sort-Object -Unique).Count) ('user=' + @($userSet | Sort-Object -Unique).Count + ' without ::=' + $userNoClass)
Add-Check 'p1_scope_internal_methods_all_have_class_prefix' ($intWithClass -eq @($intSet | Sort-Object -Unique).Count) ('internal=' + @($intSet | Sort-Object -Unique).Count + ' with ::=' + $intWithClass)

# counts self consistency across the 3x3 calls
$countsOk = $true
$countsDetail = New-Object System.Collections.ArrayList
foreach ($pair in @(
        @{ c = $defSet; k = 'all' }, @{ c = $userSet; k = 'user' }, @{ c = $intSet; k = 'internal' })) {
    $probe = Invoke-ScopeCall -Port $EditorPort -Dir $DirScope -Leaf ('p1_scope_counts_' + $pair.k) -Scope $pair.k -NodePath $null -SignalName $null
    $cnt = Get-ScopeCounts $probe
    $b = Get-ToolBody $probe
    if ($null -eq $cnt) { $countsOk = $false; [void]$countsDetail.Add($pair.k + ':no_counts'); continue }
    $selfOk = ([int]$cnt.user + [int]$cnt.internal -eq [int]$cnt.all) -and ([int]$b.count -eq @($b.connections).Count) -and ([int]$b.count -eq [int]$cnt.($pair.k))
    if (-not $selfOk) { $countsOk = $false }
    [void]$countsDetail.Add(('{0}:count={1} counts={2}-{3}-{4} expected={5}' -f $pair.k, $b.count, $cnt.all, $cnt.user, $cnt.internal, @($pair.c).Count))
}
Add-Check 'p1_scope_counts_are_self_consistent' $countsOk (($countsDetail -join ' | '))

$explicitAll = Invoke-ScopeCall -Port $EditorPort -Dir $DirScope -Leaf 'p1_scope_all_explicit' -Scope 'all' -NodePath $null -SignalName $null
Add-Check 'p1_scope_explicit_all_equals_default' ((Get-BodySha $explicitAll) -eq $bodyShaAll[0]) ('explicit_sha8=' + (Sha8 (Get-BodySha $explicitAll)) + ' default_sha8=' + (Sha8 ([string]$bodyShaAll[0])))
$bogus = Invoke-ScopeCall -Port $EditorPort -Dir $DirScope -Leaf 'p1_scope_bogus' -Scope 'bogus' -NodePath $null -SignalName $null
Add-Check 'p1_scope_unknown_is_refused_with_32602' ((Get-ErrorCode $bogus) -eq -32602) ('code=' + (Get-ErrorCode $bogus) + ' message=' + (Get-ErrorMessage $bogus))

# --- B4: scope x node_path -------------------------------------------------
$b4 = [ordered]@{}
foreach ($sc in @('all', 'user', 'internal')) {
    $call = Invoke-ScopeCall -Port $EditorPort -Dir $DirScope -Leaf ('p1_b4_node_path_' + $sc) -Scope $sc -NodePath 'ProbeTimer' -SignalName $null
    $set = Get-ConnSet $call
    $cnt = Get-ScopeCounts $call
    $b4[$sc] = [pscustomobject]@{ set = $set; counts = $cnt; body = (Get-ToolBody $call) }
}
$b4Ok = (([int]$b4['all'].counts.all -eq [int]$b4['all'].set.Count) -and ([int]$b4['user'].counts.user -eq [int]$b4['user'].set.Count) -and ([int]$b4['internal'].counts.internal -eq [int]$b4['internal'].set.Count))
Add-Check 'p1_b4_scope_composes_with_node_path' $b4Ok ('node_path=ProbeTimer all=' + $b4['all'].set.Count + '/counts.all=' + $b4['all'].counts.all + ' user=' + $b4['user'].set.Count + ' internal=' + $b4['internal'].set.Count + ' counts=' + $b4['all'].counts.all + '-' + $b4['all'].counts.user + '-' + $b4['all'].counts.internal)
$b4Partition = (([int]$b4['user'].set.Count + [int]$b4['internal'].set.Count) -eq [int]$b4['all'].set.Count)
Add-Check 'p1_b4_node_path_set_still_partitions' $b4Partition ('user+internal=' + ([int]$b4['user'].set.Count + [int]$b4['internal'].set.Count) + ' all=' + $b4['all'].set.Count)

# --- B5: scene [connection] vs run-time connect() --------------------------
$userBefore = @($userSet | Sort-Object -Unique)
$sceneTextBefore = [IO.File]::ReadAllText($sceneAbs)
$connectCode = "var root = EditorInterface.get_edited_scene_root()`nvar t = root.get_node(`"ProbeTimer`")`nvar b = root.get_node(`"Ball`")`nvar cb = Callable(b, `"queue_free`")`nif not t.timeout.is_connected(cb):`n`tt.timeout.connect(cb)`nreturn `"runtime-connect-done`""
$b5connect = Invoke-Tool -Port $EditorPort -Tool 'editor_execute_gdscript' -Arguments @{ code = $connectCode } -Directory $DirScope -Leaf 'p1_b5_runtime_connect'
$b5body = Get-ToolBody $b5connect
Add-Heartbeat ('B5 runtime connect result=' + ($b5body | ConvertTo-Json -Compress -Depth 5))

$b5user1 = Invoke-ScopeCall -Port $EditorPort -Dir $DirScope -Leaf 'p1_b5_user_after_connect_1' -Scope 'user' -NodePath $null -SignalName $null
$b5user2 = Invoke-ScopeCall -Port $EditorPort -Dir $DirScope -Leaf 'p1_b5_user_after_connect_2' -Scope 'user' -NodePath $null -SignalName $null
$b5user3 = Invoke-ScopeCall -Port $EditorPort -Dir $DirScope -Leaf 'p1_b5_user_after_connect_3' -Scope 'user' -NodePath $null -SignalName $null
$userAfter = @(Get-ConnSet $b5user1 | Sort-Object -Unique)
$sceneTextAfter = [IO.File]::ReadAllText($sceneAbs)
$runtimeEntries = @($userAfter | Where-Object { $_ -match 'queue_free' })
$sceneEntries = @($userAfter | Where-Object { $_ -notmatch 'queue_free' })
Add-Check 'p1_b5_runtime_connection_lands_in_user_scope' ($runtimeEntries.Count -eq 1) ('user_before=' + $userBefore.Count + ' user_after=' + $userAfter.Count + ' runtime_entries=' + ($runtimeEntries -join ',') + ' scene_entries=' + ($sceneEntries -join ','))
Add-Check 'p1_b5_runtime_connection_is_not_in_the_scene_file' ((-not ($sceneTextBefore -like '*queue_free*')) -and (-not ($sceneTextAfter -like '*queue_free*'))) ('scene file bytes=' + $sceneTextAfter.Length + ' mentions queue_free=' + ($sceneTextAfter -like '*queue_free*'))
Add-Check 'p1_b5_user_scope_repeats_are_stable' (((Get-BodySha $b5user1) -eq (Get-BodySha $b5user2)) -and ((Get-BodySha $b5user2) -eq (Get-BodySha $b5user3))) ('sha8=' + (Sha8 (Get-BodySha $b5user1)))

# Are the two sources distinguishable in the answer? The answer's connection
# entries are inspected field by field: if both have exactly the same key set,
# the tool exposes no provenance.
$b5bodyJson = Get-ToolBody $b5user1
$keySets = @()
foreach ($c in @($b5bodyJson.connections)) {
    $keySets += (@($c.PSObject.Properties.Name | Sort-Object) -join ',')
}
$distinctKeySets = @($keySets | Sort-Object -Unique)
Add-Check 'p1_b5_no_provenance_field_is_exposed' ($distinctKeySets.Count -eq 1) ('distinct connection key sets=' + $distinctKeySets.Count + ' keys=' + ($distinctKeySets -join ' || '))

# scope after the runtime connection: default / internal / user sets
$afterDef = @(Get-ConnSet (Invoke-ScopeCall -Port $EditorPort -Dir $DirScope -Leaf 'p1_scope_after_default' -Scope $null -NodePath $null -SignalName $null))
$afterInt = @(Get-ConnSet (Invoke-ScopeCall -Port $EditorPort -Dir $DirScope -Leaf 'p1_scope_after_internal' -Scope 'internal' -NodePath $null -SignalName $null))
$afterUnion = @(@($userAfter) + @($afterInt) | Sort-Object -Unique)
Add-Check 'p1_scope_partition_holds_after_the_runtime_connection' (@(Compare-Object @($afterDef | Sort-Object -Unique) $afterUnion).Count -eq 0) ('default=' + @($afterDef | Sort-Object -Unique).Count + ' union=' + $afterUnion.Count + ' internal=' + @($afterInt | Sort-Object -Unique).Count)

# --- B6: editor_analyze_screenshot_diff refusal paths ----------------------
$pngJsonPath = Join-Path $IoRoot 'probe-pngs.json'
$pngExit = 0
if (-not (Test-Path -LiteralPath $pngJsonPath)) {
    $previousEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { $null = & python (Join-Path $ScriptRoot 'mcp066b_make_pngs.py') $IoRoot 2>&1 | Out-String } catch { $null = $_.Exception.Message }
    $pngExit = $LASTEXITCODE
    $ErrorActionPreference = $previousEap
}
$pngs = (Get-Content -LiteralPath $pngJsonPath -Raw | ConvertFrom-Json)
$b64 = @{}
foreach ($img in $pngs.images) { $b64[$img.name] = [string]$img.base64 }
Add-Check 'p1_b6_probe_images_built' ($b64.Count -eq 3) ('exit=' + $pngExit + ' images=' + ($b64.Keys -join ','))

$b6a = Invoke-Tool -Port $EditorPort -Tool 'editor_analyze_screenshot_diff' -Arguments @{ image_a = 'this-is-not-base64!!'; image_b = $b64['sm_64x64'] } -Directory $DirProbe -Leaf 'p1_b6_invalid_base64'
Add-Check 'p1_b6_invalid_base64_is_refused' ((Get-ErrorCode $b6a) -eq -32001) ('code=' + (Get-ErrorCode $b6a) + ' message=' + (Get-ErrorMessage $b6a))
$b6b = Invoke-Tool -Port $EditorPort -Tool 'editor_analyze_screenshot_diff' -Arguments @{ image_a = $b64['sm_64x64']; image_b = $b64['sm_64x32'] } -Directory $DirProbe -Leaf 'p1_b6_size_mismatch'
Add-Check 'p1_b6_size_mismatch_is_refused' ((Get-ErrorCode $b6b) -eq -32602) ('code=' + (Get-ErrorCode $b6b) + ' message=' + (Get-ErrorMessage $b6b))
$b6c = Invoke-Tool -Port $EditorPort -Tool 'editor_analyze_screenshot_diff' -Arguments @{ image_a = $b64['big_4097x1']; image_b = $b64['big_4097x1'] } -Directory $DirProbe -Leaf 'p1_b6_over_max_dimension'
Add-Check 'p1_b6_over_max_dimension_is_refused' ((Get-ErrorCode $b6c) -eq -32602) ('code=' + (Get-ErrorCode $b6c) + ' message=' + (Get-ErrorMessage $b6c))
$b6d = Invoke-Tool -Port $EditorPort -Tool 'editor_analyze_screenshot_diff' -Arguments @{ image_a = $b64['sm_64x64']; image_b = $b64['sm_64x64']; threshold = 999 } -Directory $DirProbe -Leaf 'p1_b6_threshold_out_of_range'
Add-Check 'p1_b6_threshold_out_of_range_is_refused' ((Get-ErrorCode $b6d) -eq -32602) ('code=' + (Get-ErrorCode $b6d) + ' message=' + (Get-ErrorMessage $b6d))

$traceLinesA = Get-TraceObjects $traceA
$scopeSummaryA = [pscustomobject]@{
    default_count = @($defSet | Sort-Object -Unique).Count
    user_count_before_connect = @($userSet | Sort-Object -Unique).Count
    internal_count = @($intSet | Sort-Object -Unique).Count
    default_body_sha256 = $bodyShaAll[0]
    user_body_sha256 = $bodyShaUser[0]
    internal_body_sha256 = $bodyShaInt[0]
    user_after_runtime_connect = $userAfter
    default_after_runtime_connect_count = @($afterDef | Sort-Object -Unique).Count
    internal_after_runtime_connect_count = @($afterInt | Sort-Object -Unique).Count
    b4_node_path_ProbeTimer = [pscustomobject]@{ all = $b4['all'].set; user = $b4['user'].set; internal = $b4['internal'].set; counts = $b4['all'].counts }
    default_set_minus_user = @($defSet | Where-Object { $userSet -notcontains $_ })
    user_minus_default = @($userSet | Where-Object { $defSet -notcontains $_ })
    internal_minus_default = @($intSet | Where-Object { $defSet -notcontains $_ })
    user_internal_intersection = $inter
    trace_requests = @(Get-ToolRequests $traceLinesA).Count
    trace_captures = @($traceLinesA | Where-Object { $_.event -eq 'capture' }).Count
}
$null = Write-JsonEvidence $DirScope 'p1_scope_summary' $scopeSummaryA

Add-Heartbeat 'P1 done; stopping editor session A'
Stop-EditorSession $sessA

# ===========================================================================
#  P2 -- editor session B: scale=1 + diff image
# ===========================================================================
Add-Heartbeat 'P2 editor session B (scale=1, diff_image=on) start'
$traceB = Join-Path $ScratchRoot 'trace-editor-b.jsonl'
$sessB = Start-EditorSession -Tag 'b' -TraceFile $traceB -CaptureDir 'res://mcp066b_shots_b' -CaptureArgs @('--mcp-capture=every_call', '--mcp-capture-viewport=2d', '--mcp-capture-scale=1', '--mcp-capture-diff-image=on')
Add-Check 'p2_editor_boot_scale1' ($sessB.PortReady -and $sessB.CaptureLine) (First-LineMatching -Path $sessB.OutLog -Pattern 'capture enabled')
$openB = Open-Scene2D -Port $EditorPort -Dir $DirCap -Prefix 'p2'
$scopeB = Invoke-ScopeCall -Port $EditorPort -Dir $DirScope -Leaf 'p2_scope_default' -Scope $null -NodePath $null -SignalName $null
$scopeBSet = @(Get-ConnSet $scopeB | Sort-Object -Unique)

$argRealP2 = [ordered]@{ path = 'WallTop'; property = 'position'; value = [ordered]@{ x = 0; y = 80 } }
$realB = Invoke-Tool -Port $EditorPort -Tool 'editor_set_node_property' -Arguments $argRealP2 -Directory $DirCap -Leaf 'p2_real_change'
$replayB = Invoke-Tool -Port $EditorPort -Tool 'editor_set_node_property' -Arguments $argRealP2 -Directory $DirCap -Leaf 'p2_same_args_same_value_replay'
Start-Sleep -Seconds 3
$traceLinesB = Get-TraceObjects $traceB
$capRealB = Get-CaptureForCall $traceLinesB $realB
$capReplayB = Get-CaptureForCall $traceLinesB $replayB
Add-Check 'p2_real_change_is_changed_true' ([bool]$capRealB.changed) ('changed=' + $capRealB.changed + ' pixels=' + $capRealB.changed_pixels + '/' + $capRealB.total_pixels + ' scale=' + $capRealB.scale)
Add-Check 'p2_replay_is_changed_false' (-not [bool]$capReplayB.changed) ('changed=' + $capReplayB.changed + ' pixels=' + $capReplayB.changed_pixels)
Add-Check 'p2_diff_image_field_is_populated' ((-not [string]::IsNullOrEmpty([string]$capRealB.diff.path)) -and ([int]$capRealB.diff.bytes -gt 0) -and ([string]$capRealB.diff.sha256.Length -eq 64)) ('diff.path=' + $capRealB.diff.path + ' bytes=' + $capRealB.diff.bytes + ' sha256=' + $capRealB.diff.sha256)
$diffAbs = Globalize-ResPath ([string]$capRealB.diff.path)
Add-Check 'p2_diff_png_exists_on_disk' ((Test-Path -LiteralPath $diffAbs) -and ((Get-Item -LiteralPath $diffAbs).Length -gt 0)) ('path=' + $diffAbs + ' bytes=' + $(if (Test-Path -LiteralPath $diffAbs) { (Get-Item -LiteralPath $diffAbs).Length } else { 0 }))
if (Test-Path -LiteralPath $diffAbs) {
    $null = Write-McpEvidenceBytes -Directory $DirShots -Leaf 'p2_diff_image' -Bytes ([IO.File]::ReadAllBytes($diffAbs)) -Extension '.png'
}
# B3: the raster is the frame with each axis divided by the scale and floored -
# the scale-1 frame here is 2978x1793, so 1793/2 and 1793/4 cannot be exact. The
# invariant asserted is therefore per axis, not "four times the pixel count".
$realATotal = [int]$capReal.total_pixels
$w1 = [int]$capRealB.before.width
$h1 = [int]$capRealB.before.height
$w2 = [int]$capReal.before.width
$h2 = [int]$capReal.before.height
Add-Check 'p2_b3_scale1_frame_is_the_unscaled_frame' ((([int]$capRealB.before.width) * ([int]$capRealB.before.height)) -eq ([int]$capRealB.total_pixels)) ('scale=1 raster=' + $w1 + 'x' + $h1 + ' total=' + $capRealB.total_pixels + ' bytes=' + $capRealB.before.bytes)
Add-Check 'p2_b3_scale2_is_the_scale1_frame_halved_per_axis' (($w2 -eq [int][math]::Floor([double]$w1 / 2.0)) -and ($h2 -eq [int][math]::Floor([double]$h1 / 2.0)) -and (($w2 * $h2) -eq ([int]$capReal.total_pixels))) ('scale1=' + $w1 + 'x' + $h1 + ' scale2=' + $w2 + 'x' + $h2 + ' expected=' + [int][math]::Floor([double]$w1 / 2.0) + 'x' + [int][math]::Floor([double]$h1 / 2.0) + ' total=' + $capReal.total_pixels)

$null = Write-JsonEvidence $DirCap 'p2_session_b' ([pscustomobject]@{
    scope_default_count = $scopeBSet.Count
    scope_default_equals_session_a = (@(Compare-Object $scopeBSet @($defSet | Sort-Object -Unique)).Count -eq 0)
    real_capture = $capRealB
    replay_capture = $capReplayB
    scale1_total_pixels = [int]$capRealB.total_pixels
    scale2_total_pixels = $realATotal
})
Add-Heartbeat 'P2 done; stopping editor session B'
Stop-EditorSession $sessB

# ===========================================================================
#  P3 -- editor session C: scale=4
# ===========================================================================
Add-Heartbeat 'P3 editor session C (scale=4) start'
$traceC = Join-Path $ScratchRoot 'trace-editor-c.jsonl'
$sessC = Start-EditorSession -Tag 'c' -TraceFile $traceC -CaptureDir 'res://mcp066b_shots_c' -CaptureArgs @('--mcp-capture=every_call', '--mcp-capture-viewport=2d', '--mcp-capture-scale=4')
Add-Check 'p3_editor_boot_scale4' ($sessC.PortReady -and $sessC.CaptureLine) (First-LineMatching -Path $sessC.OutLog -Pattern 'capture enabled')
$openC = Open-Scene2D -Port $EditorPort -Dir $DirCap -Prefix 'p3'
$scopeC = Invoke-ScopeCall -Port $EditorPort -Dir $DirScope -Leaf 'p3_scope_default' -Scope $null -NodePath $null -SignalName $null
$scopeCSet = @(Get-ConnSet $scopeC | Sort-Object -Unique)
$argRealP3 = [ordered]@{ path = 'WallTop'; property = 'position'; value = [ordered]@{ x = 0; y = 100 } }
$realC = Invoke-Tool -Port $EditorPort -Tool 'editor_set_node_property' -Arguments $argRealP3 -Directory $DirCap -Leaf 'p3_real_change'
Start-Sleep -Seconds 3
$traceLinesC = Get-TraceObjects $traceC
$capRealC = Get-CaptureForCall $traceLinesC $realC
Add-Check 'p3_real_change_is_changed_true' ([bool]$capRealC.changed) ('changed=' + $capRealC.changed + ' pixels=' + $capRealC.changed_pixels + '/' + $capRealC.total_pixels + ' scale=' + $capRealC.scale)
Add-Check 'p3_b3_scale4_is_the_scale1_frame_quartered_per_axis' ((([int]$capRealC.before.width) -eq [int][math]::Floor([double]$w1 / 4.0)) -and (([int]$capRealC.before.height) -eq [int][math]::Floor([double]$h1 / 4.0)) -and ((([int]$capRealC.before.width) * ([int]$capRealC.before.height)) -eq ([int]$capRealC.total_pixels))) ('scale1=' + $w1 + 'x' + $h1 + ' scale4=' + [int]$capRealC.before.width + 'x' + [int]$capRealC.before.height + ' expected=' + [int][math]::Floor([double]$w1 / 4.0) + 'x' + [int][math]::Floor([double]$h1 / 4.0) + ' total=' + $capRealC.total_pixels + ' scale2_total=' + $realATotal)
$null = Write-JsonEvidence $DirCap 'p3_session_c' ([pscustomobject]@{
    scope_default_count = $scopeCSet.Count
    scope_default_equals_session_a = (@(Compare-Object $scopeCSet @($defSet | Sort-Object -Unique)).Count -eq 0)
    capture = $capRealC
    scale4_total_pixels = [int]$capRealC.total_pixels
    scale2_total_pixels = $realATotal
})
Add-Heartbeat 'P3 done; stopping editor session C'
Stop-EditorSession $sessC

# ===========================================================================
#  P4 -- editor session D: --mcp-capture=on_error
# ===========================================================================
Add-Heartbeat 'P4 editor session D (on_error) start'
$traceD = Join-Path $ScratchRoot 'trace-editor-d.jsonl'
$sessD = Start-EditorSession -Tag 'd' -TraceFile $traceD -CaptureDir 'res://mcp066b_shots_d' -CaptureArgs @('--mcp-capture=on_error', '--mcp-capture-viewport=2d', '--mcp-capture-scale=2')
Add-Check 'p4_editor_boot_on_error' ($sessD.PortReady -and $sessD.CaptureLine) (First-LineMatching -Path $sessD.OutLog -Pattern 'capture enabled')
$openD = Open-Scene2D -Port $EditorPort -Dir $DirCap -Prefix 'p4'
$scopeD = Invoke-ScopeCall -Port $EditorPort -Dir $DirScope -Leaf 'p4_scope_default' -Scope $null -NodePath $null -SignalName $null
$scopeDSet = @(Get-ConnSet $scopeD | Sort-Object -Unique)
$okD = Invoke-Tool -Port $EditorPort -Tool 'editor_get_scene_tree' -Arguments @{ max_depth = -1 } -Directory $DirProbe -Leaf 'p4_successful_call'
$errD = Invoke-Tool -Port $EditorPort -Tool 'editor_set_node_property' -Arguments @{ path = 'NoSuchNode'; property = 'position'; value = @{ x = 0; y = 0 } } -Directory $DirProbe -Leaf 'p4_failing_call'
Start-Sleep -Seconds 3
$traceLinesD = Get-TraceObjects $traceD
$capsD = @($traceLinesD | Where-Object { $_.event -eq 'capture' })
$capForOkD = Get-CaptureForCall $traceLinesD $okD
$capForErrD = Get-CaptureForCall $traceLinesD $errD
Add-Check 'p4_error_call_really_failed' ((Get-ErrorCode $errD) -ne 0) ('code=' + (Get-ErrorCode $errD) + ' message=' + (Get-ErrorMessage $errD))
Add-Check 'p4_success_produces_no_capture_line' ($null -eq $capForOkD) ('seq=' + $okD.Seq + ' tool=editor_get_scene_tree capture=' + $(if ($null -eq $capForOkD) { 'absent' } else { 'present' }))
Add-Check 'p4_error_produces_a_capture_line' ($null -ne $capForErrD) ('seq=' + $errD.Seq + ' tool=editor_set_node_property status=' + $(if ($null -ne $capForErrD) { $capForErrD.status } else { 'absent' }))
Add-Check 'p4_capture_count_equals_error_count' ($capsD.Count -eq 1) ('captures=' + $capsD.Count + ' (the only failing call in this session)')
$null = Write-JsonEvidence $DirCap 'p4_session_d' ([pscustomobject]@{
    scope_default_count = $scopeDSet.Count
    scope_default_equals_session_a = (@(Compare-Object $scopeDSet @($defSet | Sort-Object -Unique)).Count -eq 0)
    success_call_error_code = (Get-ErrorCode $okD)
    failing_call_error_code = (Get-ErrorCode $errD)
    capture_line_for_success = $capForOkD
    capture_line_for_error = $capForErrD
    capture_lines_total = $capsD.Count
})
Add-Heartbeat 'P4 done; stopping editor session D'
Stop-EditorSession $sessD

# B8: the internal count across the four editor processes
$internalAcross = @(
    [pscustomobject]@{ session = 'A'; internal = @($intSet | Sort-Object -Unique).Count; user = @($userSet | Sort-Object -Unique).Count; all = @($defSet | Sort-Object -Unique).Count },
    [pscustomobject]@{ session = 'B'; internal = (Get-ScopeCounts $scopeB).internal; user = (Get-ScopeCounts $scopeB).user; all = (Get-ScopeCounts $scopeB).all },
    [pscustomobject]@{ session = 'C'; internal = (Get-ScopeCounts $scopeC).internal; user = (Get-ScopeCounts $scopeC).user; all = (Get-ScopeCounts $scopeC).all },
    [pscustomobject]@{ session = 'D'; internal = (Get-ScopeCounts $scopeD).internal; user = (Get-ScopeCounts $scopeD).user; all = (Get-ScopeCounts $scopeD).all }
)
$internalValues = @($internalAcross | ForEach-Object { [int]$_.internal } | Sort-Object -Unique)
Add-Check 'p4_b8_scope_counts_are_stable_across_processes' ($internalValues.Count -eq 1) ('internal across sessions=' + (($internalAcross | ForEach-Object { $_.session + '=' + $_.internal }) -join ' ') + ' user=' + (($internalAcross | ForEach-Object { $_.session + '=' + $_.user }) -join ' '))
$null = Write-JsonEvidence $DirScope 'p4_b8_scope_across_processes' ([pscustomobject]@{ rows = $internalAcross; distinct_internal='' + $internalValues.Count; a_reported_internal_count = 206; a_reported_all_with_one_connection = 207; a_reported_user_with_one_connection = 1 })

# ===========================================================================
#  P5 -- game session (windowed)
# ===========================================================================
Add-Heartbeat 'P5 game session (windowed) start'
$gameOut = Join-Path $DirLogs 'game.out.log.txt'
$gameErr = Join-Path $DirLogs 'game.err.log.txt'
$gameArgs = @('--path', $Proj, ('--mcp-port=' + $GamePort), ('--mcp-trace=' + (To-Fwd $GameTrace)), '--mcp-capture=every_call', '--mcp-capture-dir=res://mcp066b_game_shots', '--mcp-capture-viewport=2d', '--mcp-capture-scale=2')
Reset-McpCallSeq
$script:GameProcess = Start-OwnProcess -Exe $MonoExe -EngineArgs $gameArgs -OutLog $gameOut -ErrLog $gameErr
Add-Heartbeat ('game started pid=' + $script:GameProcess.Id + ' args=' + ($gameArgs -join ' '))
$gameReady = Wait-Port -Port $GamePort -TimeoutSec 90
$roleGame = Wait-LogLine -Path $gameOut -Pattern 'role=game' -TimeoutSec 60
Start-Sleep -Seconds 3
$gameLogText = Read-TextShared -Path $gameOut
$bindFailed = ($gameLogText -like '*bind failed*')
Add-Check 'p5_game_role_and_no_bind_failure' ($gameReady -and $roleGame -and (-not $bindFailed)) ('port_ready=' + $gameReady + ' role_game_line=' + $roleGame + ' bind_failed=' + $bindFailed)

$listG = Invoke-Raw -Port $GamePort -Method 'tools/list' -Directory $DirGame -Leaf 'p5_game_tools_list'
$listGCount = @($listG.Json.result.tools).Count
$gameNames = @($listG.Json.result.tools | ForEach-Object { [string]$_.name })
$editorNamesOnGame = @($gameNames | Where-Object { $_ -like 'editor_*' })
$runningGameNames = @($gameNames | Where-Object { $_ -like 'running_game_*' })
Add-Check 'p5_game_tools_list_is_72_with_no_editor_tools' (($listGCount -eq 72) -and ($editorNamesOnGame.Count -eq 0)) ('count=' + $listGCount + ' editor_*=' + $editorNamesOnGame.Count + ' running_game_*=' + $runningGameNames.Count)

# --- before state ----------------------------------------------------------
$gMainBefore = Invoke-Tool -Port $GamePort -Tool 'running_game_get_node_properties' -Arguments @{ node_path = 'Main'; properties = @('Score', 'BricksHit', 'State', 'Lives') } -Directory $DirGame -Leaf 'p5_main_before'
$gBricksBefore = Invoke-Tool -Port $GamePort -Tool 'running_game_find_nodes_by_script' -Arguments @{ script = 'res://scripts/Brick.cs' } -Directory $DirGame -Leaf 'p5_bricks_before'
$gScoreBefore = Invoke-Tool -Port $GamePort -Tool 'running_game_get_node_properties' -Arguments @{ node_path = 'HUD/ScoreLabel'; properties = @('text') } -Directory $DirGame -Leaf 'p5_score_text_before'
$gTreeBefore = Invoke-Tool -Port $GamePort -Tool 'running_game_get_scene_tree' -Arguments @{ max_depth = -1 } -Directory $DirGame -Leaf 'p5_scene_tree_before'
$gBricksBeforeBody = Get-ToolBody $gBricksBefore
$gScoreBeforeBody = Get-PropsOf $gScoreBefore
$gMainBeforeBody = Get-PropsOf $gMainBefore
$gTreeBeforeJson = (Get-ToolBody $gTreeBefore) | ConvertTo-Json -Compress -Depth 30
Add-Heartbeat ('game before: bricks=' + $gBricksBeforeBody.count + ' score_text=' + $gScoreBeforeBody.text + ' state=' + $gMainBeforeBody.State)

# make the first hit deterministic (test pre-condition, declared in the report)
$null = Invoke-Tool -Port $GamePort -Tool 'running_game_set_node_property' -Arguments @{ node_path = 'Ball'; property = 'position'; value = @{ x = 300; y = 320 } } -Directory $DirGame -Leaf 'p5_prepare_ball_position'
$null = Invoke-Tool -Port $GamePort -Tool 'running_game_set_node_property' -Arguments @{ node_path = 'Ball'; property = 'Vel'; value = @{ x = 0; y = -260 } } -Directory $DirGame -Leaf 'p5_prepare_ball_velocity'

# --- paddle: inject input, read back with ANOTHER tool ----------------------
$gPaddleBefore = Invoke-Tool -Port $GamePort -Tool 'running_game_get_node_properties' -Arguments @{ node_path = 'Paddle'; properties = @('position', 'Moves', 'LastDir') } -Directory $DirGame -Leaf 'p5_paddle_before'
$gInjectRight = Invoke-Tool -Port $GamePort -Tool 'running_game_run_test_scenario' -Arguments @{ steps = @(@{ type = 'input'; action = 'paddle_right'; pressed = $true }) } -Directory $DirGame -Leaf 'p5_inject_paddle_right'
$gPaddleSamples = Invoke-Tool -Port $GamePort -Tool 'running_game_get_node_property_samples' -Arguments @{ node_path = 'Paddle'; properties = @('position'); frame_count = 24; frame_interval = 1 } -Directory $DirGame -Leaf 'p5_paddle_position_samples'
$gPaddleAfter = Invoke-Tool -Port $GamePort -Tool 'running_game_get_node_properties' -Arguments @{ node_path = 'Paddle'; properties = @('position', 'Moves', 'LastDir') } -Directory $DirGame -Leaf 'p5_paddle_after'
$gReleaseAndAssert = Invoke-Tool -Port $GamePort -Tool 'running_game_run_test_scenario' -Arguments @{ steps = @(@{ type = 'input'; action = 'paddle_right'; pressed = $false }, @{ type = 'assert'; node_path = 'Paddle'; property = 'Moves'; operator = 'gt'; expected = 0 }) } -Directory $DirGame -Leaf 'p5_release_and_assert_moves'

$gPaddleSamplesBody = Get-ToolBody $gPaddleSamples
$xs = @()
foreach ($s in @($gPaddleSamplesBody.samples)) { $xs += [double]$s.position.x }
$distinctX = @($xs | Sort-Object -Unique).Count
$monotonic = $true
for ($i = 1; $i -lt $xs.Count; $i++) { if ($xs[$i] -lt $xs[$i - 1]) { $monotonic = $false } }
Add-Check 'p5_paddle_samples_are_per_frame_monotonic' (($xs.Count -ge 20) -and ($distinctX -eq $xs.Count) -and $monotonic) ('frames=' + $xs.Count + ' distinct=' + $distinctX + ' monotonic=' + $monotonic + ' first=' + $xs[0] + ' last=' + $xs[$xs.Count - 1] + ' samples=' + (($xs | ForEach-Object { [math]::Round($_, 2) }) -join ','))
$gPaddleBeforeBody = Get-PropsOf $gPaddleBefore
$gPaddleAfterBody = Get-PropsOf $gPaddleAfter
$gReleaseBody = Get-ToolBody $gReleaseAndAssert
Add-Check 'p5_paddle_really_moved_between_two_calls' (([double]$gPaddleAfterBody.position.x) -gt ([double]$gPaddleBeforeBody.position.x)) ('x ' + $gPaddleBeforeBody.position.x + ' -> ' + $gPaddleAfterBody.position.x + ' moves=' + $gPaddleAfterBody.Moves + ' dir=' + $gPaddleAfterBody.LastDir)
Add-Check 'p5_paddle_in_process_assert_passed' ([bool]$gReleaseBody.all_passed) ('all_passed=' + $gReleaseBody.all_passed + ' passed=' + $gReleaseBody.passed + ' failed=' + $gReleaseBody.failed + ' results=' + ($gReleaseBody.results | ConvertTo-Json -Compress -Depth 5))

# --- ball + bricks + score --------------------------------------------------
$gInjectLaunch = Invoke-Tool -Port $GamePort -Tool 'running_game_run_test_scenario' -Arguments @{ steps = @(@{ type = 'input'; action = 'launch'; pressed = $true }) } -Directory $DirGame -Leaf 'p5_inject_launch'
$gBallSamples = Invoke-Tool -Port $GamePort -Tool 'running_game_get_node_property_samples' -Arguments @{ node_path = 'Ball'; properties = @('position'); frame_count = 18; frame_interval = 1 } -Directory $DirGame -Leaf 'p5_ball_position_samples'
$gWaitAssertScore = Invoke-Tool -Port $GamePort -Tool 'running_game_run_test_scenario' -Arguments @{ steps = @(@{ type = 'wait'; seconds = 1.5 }, @{ type = 'assert'; node_path = 'Main'; property = 'Score'; operator = 'gt'; expected = 0 }) } -Directory $DirGame -Leaf 'p5_wait_and_assert_score'
$gBricksAfter = Invoke-Tool -Port $GamePort -Tool 'running_game_find_nodes_by_script' -Arguments @{ script = 'res://scripts/Brick.cs' } -Directory $DirGame -Leaf 'p5_bricks_after'
$gScoreAfter = Invoke-Tool -Port $GamePort -Tool 'running_game_get_node_properties' -Arguments @{ node_path = 'HUD/ScoreLabel'; properties = @('text') } -Directory $DirGame -Leaf 'p5_score_text_after'
$gMainAfter = Invoke-Tool -Port $GamePort -Tool 'running_game_get_node_properties' -Arguments @{ node_path = 'Main'; properties = @('Score', 'BricksHit', 'State', 'Lives', 'Launched') } -Directory $DirGame -Leaf 'p5_main_after'
$gTreeAfter = Invoke-Tool -Port $GamePort -Tool 'running_game_get_scene_tree' -Arguments @{ max_depth = -1 } -Directory $DirGame -Leaf 'p5_scene_tree_after'

$gBallSamplesBody = Get-ToolBody $gBallSamples
$ys = @()
foreach ($s in @($gBallSamplesBody.samples)) { $ys += [double]$s.position.y }
$ballDistinct = @($ys | Sort-Object -Unique).Count
$ballMono = $true
for ($i = 1; $i -lt $ys.Count; $i++) { if ($ys[$i] -gt $ys[$i - 1]) { $ballMono = $false } }
$gBricksAfterBody = Get-ToolBody $gBricksAfter
$gScoreAfterBody = Get-PropsOf $gScoreAfter
$gMainAfterBody = Get-PropsOf $gMainAfter
$gWaitBody = Get-ToolBody $gWaitAssertScore
$gTreeAfterJson = (Get-ToolBody $gTreeAfter) | ConvertTo-Json -Compress -Depth 30
Add-Check 'p5_ball_samples_are_per_frame_monotonic' (($ys.Count -ge 15) -and ($ballDistinct -ge 15) -and $ballMono) ('frames=' + $ys.Count + ' distinct=' + $ballDistinct + ' monotonic_decreasing=' + $ballMono + ' samples=' + (($ys | ForEach-Object { [math]::Round($_, 2) }) -join ','))
Add-Check 'p5_brick_node_set_really_decreased' (([int]$gBricksAfterBody.count) -lt ([int]$gBricksBeforeBody.count)) ('before=' + $gBricksBeforeBody.count + ' after=' + $gBricksAfterBody.count + ' surviving=' + (($gBricksAfterBody.nodes | ForEach-Object { $_.name }) -join ','))
$brick0Before = ($gTreeBeforeJson -like '*"Brick0"*')
$brick0After = ($gTreeAfterJson -like '*"Brick0"*')
Add-Check 'p5_brick0_left_the_whole_scene_tree' ($brick0Before -and (-not $brick0After)) ('Brick0 before=' + $brick0Before + ' after=' + $brick0After)
Add-Check 'p5_score_label_text_really_changed' (([string]$gScoreAfterBody.text) -ne ([string]$gScoreBeforeBody.text)) ('text ' + $gScoreBeforeBody.text + ' -> ' + $gScoreAfterBody.text + ' Main.Score=' + $gMainAfterBody.Score + ' BricksHit=' + $gMainAfterBody.BricksHit)
$scoreAssertActual = ''
$scoreAssertRows = @($gWaitBody.results | Where-Object { $_.property -eq 'Score' })
if ($scoreAssertRows.Count -gt 0) { $scoreAssertActual = [string]$scoreAssertRows[0].actual }
Add-Check 'p5_score_in_process_assert_passed' ([bool]$gWaitBody.all_passed) ('all_passed=' + $gWaitBody.all_passed + ' passed=' + $gWaitBody.passed + ' actual=' + $scoreAssertActual + ' results=' + ($gWaitBody.results | ConvertTo-Json -Compress -Depth 5))
$null = Write-JsonEvidence $DirGame 'p5_live_chain' ([pscustomobject]@{
    paddle = [pscustomobject]@{ before = $gPaddleBeforeBody; after = $gPaddleAfterBody; samples_x = $xs; distinct_x = $distinctX; monotonic = $monotonic; assert = $gReleaseBody }
    ball = [pscustomobject]@{ samples_y = $ys; distinct_y = $ballDistinct; monotonic_decreasing = $ballMono }
    bricks = [pscustomobject]@{ before_count = [int]$gBricksBeforeBody.count; after_count = [int]$gBricksAfterBody.count; before_nodes = @($gBricksBeforeBody.nodes | ForEach-Object { $_.name }); after_nodes = @($gBricksAfterBody.nodes | ForEach-Object { $_.name }) }
    score = [pscustomobject]@{ text_before = [string]$gScoreBeforeBody.text; text_after = [string]$gScoreAfterBody.text; main_after = $gMainAfterBody; assert = $gWaitBody }
    two_step_sha256 = [pscustomobject]@{
        paddle_before = $gPaddleBefore.ResponseSha256; paddle_after = $gPaddleAfter.ResponseSha256
        bricks_before = $gBricksBefore.ResponseSha256; bricks_after = $gBricksAfter.ResponseSha256
        score_before = $gScoreBefore.ResponseSha256; score_after = $gScoreAfter.ResponseSha256
    }
})
$twoStepPairs = @(
    @{ n = 'paddle'; a = $gPaddleBefore.ResponseSha256; b = $gPaddleAfter.ResponseSha256 },
    @{ n = 'bricks'; a = $gBricksBefore.ResponseSha256; b = $gBricksAfter.ResponseSha256 },
    @{ n = 'score'; a = $gScoreBefore.ResponseSha256; b = $gScoreAfter.ResponseSha256 })
$allDiffer = $true
foreach ($p in $twoStepPairs) { if ($p.a -eq $p.b) { $allDiffer = $false } }
Add-Check 'p5_every_two_step_pair_has_a_different_sha256' $allDiffer (($twoStepPairs | ForEach-Object { $_.n + ':' + (Sha8 $_.a) + '->' + (Sha8 $_.b) }) -join ' ')

# --- criterion 6, game side -------------------------------------------------
$gRead1 = Invoke-Tool -Port $GamePort -Tool 'running_game_get_scene_tree' -Arguments @{ max_depth = -1 } -Directory $DirGame -Leaf 'p5_c6_read_only_a'
$gRead2 = Invoke-Tool -Port $GamePort -Tool 'running_game_get_scene_tree' -Arguments @{ max_depth = -1 } -Directory $DirGame -Leaf 'p5_c6_read_only_b_replay'
$argGameReal = [ordered]@{ node_path = 'WallTop'; property = 'position'; value = [ordered]@{ x = 0; y = 160 } }
$gReal = Invoke-Tool -Port $GamePort -Tool 'running_game_set_node_property' -Arguments $argGameReal -Directory $DirGame -Leaf 'p5_c6_real_change'
$gReplay = Invoke-Tool -Port $GamePort -Tool 'running_game_set_node_property' -Arguments $argGameReal -Directory $DirGame -Leaf 'p5_c6_same_args_same_value_replay'
Add-Check 'p5_c6_game_replay_arguments_byte_identical' ($gReal.ArgumentsSha256 -eq $gReplay.ArgumentsSha256) ('arguments_sha256=' + $gReal.ArgumentsSha256 + ' replay=' + $gReplay.ArgumentsSha256)
Start-Sleep -Seconds 3
$traceLinesG = Get-TraceObjects $GameTrace
$gRead1Cap = Get-CaptureForCall $traceLinesG $gRead1
$gRead2Cap = Get-CaptureForCall $traceLinesG $gRead2
$gRealCap = Get-CaptureForCall $traceLinesG $gReal
$gReplayCap = Get-CaptureForCall $traceLinesG $gReplay
Add-Check 'p5_c6_game_read_replays_changed_false' ((-not [bool]$gRead1Cap.changed) -and (-not [bool]$gRead2Cap.changed)) ('a=' + $gRead1Cap.changed + ' b=' + $gRead2Cap.changed)
Add-Check 'p5_c6_game_real_change_changed_true' ([bool]$gRealCap.changed) ('changed=' + $gRealCap.changed + ' pixels=' + $gRealCap.changed_pixels + '/' + $gRealCap.total_pixels + ' viewport=' + $gRealCap.viewport + ' scale=' + $gRealCap.scale + ' status=' + $gRealCap.status)
Add-Check 'p5_c6_game_replay_changed_false' (-not [bool]$gReplayCap.changed) ('changed=' + $gReplayCap.changed + ' pixels=' + $gReplayCap.changed_pixels + ' before_sha=' + (Sha8 ([string]$gReplayCap.before.sha256)) + ' after_sha=' + (Sha8 ([string]$gReplayCap.after.sha256)))
$null = Add-PixelPair -Label 'game_real_change' -BeforeRes ([string]$gRealCap.before.path) -AfterRes ([string]$gRealCap.after.path) -CaptureLine $gRealCap -ToolBody $null
$null = Add-PixelPair -Label 'game_replay' -BeforeRes ([string]$gReplayCap.before.path) -AfterRes ([string]$gReplayCap.after.path) -CaptureLine $gReplayCap -ToolBody $null
$null = Write-JsonEvidence $DirGame 'p5_game_capture' ([pscustomobject]@{ read_a = $gRead1Cap; read_b = $gRead2Cap; real_change = $gRealCap; replay = $gReplayCap; args_sha256 = $gReal.ArgumentsSha256; replay_args_sha256 = $gReplay.ArgumentsSha256 })

# --- B1: windowed game capture family --------------------------------------
$capShot = Invoke-Tool -Port $GamePort -Tool 'running_game_capture_screenshot' -Arguments @{} -Directory $DirGame -Leaf 'p5_b1_capture_screenshot_memory'
$capShotBody = Get-ToolBody $capShot
$shotOk = $false
$shotDetail = ''
if ($null -ne $capShotBody) {
    $bytes = [Convert]::FromBase64String([string]$capShotBody.image_base64)
    $magic = ($bytes.Length -gt 8) -and ($bytes[0] -eq 0x89) -and ($bytes[1] -eq 0x50) -and ($bytes[2] -eq 0x4E) -and ($bytes[3] -eq 0x47)
    $shotOk = $magic -and ([int]$capShotBody.width -gt 0) -and ([int]$capShotBody.height -gt 0)
    $shotDetail = 'width=' + $capShotBody.width + ' height=' + $capShotBody.height + ' format=' + $capShotBody.format + ' png_bytes=' + $bytes.Length + ' png_magic=' + $magic
    $null = Write-McpEvidenceBytes -Directory $DirShots -Leaf 'p5_b1_capture_screenshot' -Bytes $bytes -Extension '.png'
}
Add-Check 'p5_b1_windowed_capture_screenshot_returns_a_real_png' $shotOk $shotDetail

$capShotSaved = Invoke-Tool -Port $GamePort -Tool 'running_game_capture_screenshot' -Arguments @{ save_path = 'user://b066_shot.png' } -Directory $DirGame -Leaf 'p5_b1_capture_screenshot_save_path'
$capShotSavedBody = Get-ToolBody $capShotSaved
Add-Check 'p5_b1_capture_screenshot_save_path_writes_a_file' (($null -ne $capShotSavedBody) -and (-not [string]::IsNullOrEmpty([string]$capShotSavedBody.saved_path))) ('saved_path=' + $capShotSavedBody.saved_path + ' width=' + $capShotSavedBody.width + ' height=' + $capShotSavedBody.height)

$capFrames = Invoke-Tool -Port $GamePort -Tool 'running_game_capture_frames' -Arguments @{ count = 3; frame_interval = 10; half_resolution = $true } -Directory $DirGame -Leaf 'p5_b1_capture_frames_half'
$capFramesBody = Get-ToolBody $capFrames
$frameShas = @()
$frameEngines = @()
$frameOk = $false
$frameDetail = ''
if ($null -ne $capFramesBody) {
    foreach ($fr in @($capFramesBody.frames)) {
        $fb = [Convert]::FromBase64String([string]$fr.image_base64)
        $frameShas += (Get-McpEvidenceContentSha256 -Bytes $fb)
        $frameEngines += [int]$fr.frame
    }
    # The three frames come from three different engine frames, `frame_interval`
    # apart, each a real PNG of the windowed game. Pixel distinctness is NOT
    # asserted here: this fixture's Ball and Paddle are plain Node2D nodes with no
    # visual child, so a moving ball changes no pixel - the criterion below moves
    # a visible node between two captures instead.
    $stepsOk = $true
    for ($i = 1; $i -lt $frameEngines.Count; $i++) { if (($frameEngines[$i] - $frameEngines[$i - 1]) -ne 10) { $stepsOk = $false } }
    $frameOk = (@($capFramesBody.frames).Count -eq 3) -and $stepsOk -and (@($capFramesBody.frames | Where-Object { [string]$_.image_base64 -like 'iVBOR*' }).Count -eq 3)
    $frameDetail = 'count=' + $capFramesBody.count + ' widths=' + (($capFramesBody.frames | ForEach-Object { $_.width }) -join ',') + ' heights=' + (($capFramesBody.frames | ForEach-Object { $_.height }) -join ',') + ' engine_frames=' + ($frameEngines -join ',') + ' interval_ok=' + $stepsOk
}
Add-Check 'p5_b1_windowed_capture_frames_are_real_frames' $frameOk $frameDetail
# The capture really reflects the screen: move a VISIBLE node, then take one
# frame and compare it with the first frame taken before the move.
$moveArgs = @{ node_path = 'WallTop'; property = 'position'; value = @{ x = 0; y = 200 } }
$null = Invoke-Tool -Port $GamePort -Tool 'running_game_set_node_property' -Arguments $moveArgs -Directory $DirGame -Leaf 'p5_b1_move_visible_node'
Start-Sleep -Seconds 1
$capFramesAfterMove = Invoke-Tool -Port $GamePort -Tool 'running_game_capture_frames' -Arguments @{ count = 1; frame_interval = 1; half_resolution = $true } -Directory $DirGame -Leaf 'p5_b1_capture_frames_after_move'
$capFramesAfterMoveBody = Get-ToolBody $capFramesAfterMove
$afterMoveSha = ''
if (($null -ne $capFramesAfterMoveBody) -and (@($capFramesAfterMoveBody.frames).Count -ge 1)) {
    $afterMoveSha = Get-McpEvidenceContentSha256 -Bytes ([Convert]::FromBase64String([string]$capFramesAfterMoveBody.frames[0].image_base64))
}
Add-Check 'p5_b1_windowed_capture_reflects_a_visible_change' (($afterMoveSha -ne '') -and (@($frameShas).Count -ge 1) -and ($afterMoveSha -ne $frameShas[0])) ('frame_before_move_sha8=' + (Sha8 $frameShas[0]) + ' frame_after_move_sha8=' + (Sha8 $afterMoveSha))
$capFramesFull = Invoke-Tool -Port $GamePort -Tool 'running_game_capture_frames' -Arguments @{ count = 2; frame_interval = 10; half_resolution = $false } -Directory $DirGame -Leaf 'p5_b1_capture_frames_full'
$capFramesFullBody = Get-ToolBody $capFramesFull
$fullDetail = 'count=' + $capFramesFullBody.count + ' widths=' + (($capFramesFullBody.frames | ForEach-Object { $_.width }) -join ',') + ' heights=' + (($capFramesFullBody.frames | ForEach-Object { $_.height }) -join ',')
$fullOkHalf = $false
if ((@($capFramesFullBody.frames).Count -ge 1) -and (@($capFramesBody.frames).Count -ge 1)) {
    $fullOkHalf = ([int]$capFramesFullBody.frames[0].width -eq 2 * [int]$capFramesBody.frames[0].width)
}
Add-Check 'p5_b1_full_resolution_frames_are_twice_the_half_resolution_ones' $fullOkHalf $fullDetail

$null = Write-JsonEvidence $DirGame 'p5_b1_windowed_capture_family' ([pscustomobject]@{
    screenshot_memory = [pscustomobject]@{ width = $capShotBody.width; height = $capShotBody.height; format = $capShotBody.format; response_sha256 = $capShot.ResponseSha256 }
    screenshot_saved = $capShotSavedBody
    frames_half = [pscustomobject]@{ count = $capFramesBody.count; widths = @($capFramesBody.frames | ForEach-Object { $_.width }); engine_frames = $frameEngines; pixel_sha256 = $frameShas }
    frames_full = [pscustomobject]@{ count = $capFramesFullBody.count; widths = @($capFramesFullBody.frames | ForEach-Object { $_.width }) }
    frame_after_visible_move_sha256 = $afterMoveSha
    note = 'Ball and Paddle are plain Node2D nodes with no visual child in this fixture, so the three 10-frame-apart capture_frames PNGs are pixel-identical; the screen-dependent claim is made by moving a visible ColorRect (WallTop) between two captures'
})

Add-Heartbeat 'P5 done; stopping the game process'
Stop-OwnProcess -Process $script:GameProcess -LogPath $gameOut
$script:GameProcess = $null
$deadline = (Get-Date).AddSeconds(30)
while ((Get-Date) -lt $deadline) {
    if (-not ((Get-ListeningPorts) -contains $GamePort)) { break }
    Start-Sleep -Milliseconds 500
}
Start-Sleep -Seconds 1

# ===========================================================================
#  P6 -- stop, independent recomputation, summary
# ===========================================================================
Add-Heartbeat 'P6 finalize start'
$portsAfter = Get-ListeningPorts
Add-Check 'p6_ports_9888_9889_released' ((-not ($portsAfter -contains 9888)) -and (-not ($portsAfter -contains 9889))) ('listening_ports=' + ($portsAfter -join ','))
Add-Check 'p6_port_9877_still_untouched' (-not ($portsAfter -contains 9877)) ('listening_ports=' + ($portsAfter -join ','))

# independent recomputation (route 3)
$pairsPath = Join-Path $IoRoot 'pixel-pairs.json'
$recomputePath = Join-Path $IoRoot 'pixel_recompute.json'
$pairsJson = ($script:PixelPairs | ConvertTo-Json -Depth 10)
[IO.File]::WriteAllBytes($pairsPath, (New-Object Text.UTF8Encoding($false)).GetBytes($pairsJson))
$recOut = ''
if (Test-Path -LiteralPath $pairsPath) {
    $previousEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { $recOut = (& python (Join-Path $ScriptRoot 'mcp065b_pixel_recompute.py') $pairsPath $recomputePath 2>&1 | Out-String) } catch { $recOut = $_.Exception.Message }
    $ErrorActionPreference = $previousEap
}
Add-Heartbeat ('pixel recompute: ' + ($recOut -replace "`r?`n", ' | '))
$recOk = $false
$recDetail = ''
if (Test-Path -LiteralPath $recomputePath) {
    $rec = Get-Content -LiteralPath $recomputePath -Raw | ConvertFrom-Json
    $recOk = [bool]$rec.all_three_routes_agree
    $recDetail = 'pairs=' + @($rec.pairs).Count + ' all_three_routes_agree=' + $rec.all_three_routes_agree + ' ' + (@($rec.pairs | ForEach-Object { $_.label + ':' + $_.independent.changed_pixels + '/' + $_.independent.total_pixels + ' log_match=' + $_.log_matches_independent }) -join ' | ')
    Copy-Item -LiteralPath $recomputePath -Destination (Join-Path $DirCap 'pixel_recompute.json') -Force
}
Add-Check 'p6_independent_pixel_recomputation_agrees' $recOk $recDetail

# traces into the evidence tree
foreach ($t in @($traceA, $traceB, $traceC, $traceD, $GameTrace)) {
    if (Test-Path -LiteralPath $t) {
        Copy-Item -LiteralPath $t -Destination (Join-Path $DirTraces (Split-Path -Leaf $t)) -Force
    }
}
if (Test-Path -LiteralPath $ProgressFile) {
    Copy-Item -LiteralPath $ProgressFile -Destination (Join-Path $DirTraces 'PROGRESS.md.txt') -Force
}

# marker: this is the ONLY thing that stops the watcher with stop_reason=marker,
# and it is written after every call of this run is done. The watcher is then
# awaited (never killed) and its own summary is read back as evidence.
[IO.File]::WriteAllText($MarkerFile, ('task=066 role=B finished=' + (Get-Date).ToString('o', $InvariantCulture) + "`n"), (New-Object Text.UTF8Encoding($false)))
Add-Heartbeat 'B066-DONE.marker written; waiting for the watcher'
if ($null -ne $script:WatcherProcess) {
    $exited = $script:WatcherProcess.WaitForExit(240000)
    Add-Heartbeat ('watcher wait done exited=' + $exited + ' has_exited=' + $script:WatcherProcess.HasExited)
}
Start-Sleep -Seconds 2
$watchSummaryPath = Join-Path $WatchOutDir 'watch-summary.json'
$watchTxtPath = Join-Path $WatchOutDir 'watch-summary.txt'
$watchReason = ''
$watchActivity = $false
$watchFiles = 0
$watchMissing = 0
$watchLines = 0
$watchBeforeEnd = $true
if (Test-Path -LiteralPath $watchSummaryPath) {
    $ws = Get-Content -LiteralPath $watchSummaryPath -Raw | ConvertFrom-Json
    $watchReason = [string]$ws.stop_reason
    $watchActivity = [bool]$ws.activity_seen
    $watchFiles = [int]$ws.trace_files
    $watchLines = [int]$ws.trace_lines
    $watchBeforeEnd = [bool]$ws.observation_stopped_before_development_ended
    foreach ($row in @($ws.traces)) { if ([bool]$row.missing) { $watchMissing++ } }
}
Add-Check 'p6_watch_stop_reason_is_marker' ($watchReason -eq 'marker') ('stop_reason=' + $watchReason)
Add-Check 'p6_watch_had_activity' $watchActivity ('activity_seen=' + $watchActivity + ' trace_lines=' + $watchLines)
Add-Check 'p6_watch_saw_the_trace_lines' ($watchLines -gt 0) ('trace_lines=' + $watchLines + ' files=' + $watchFiles + ' missing=' + $watchMissing)
Add-Check 'p6_watch_stopped_after_the_development_ended' (-not $watchBeforeEnd) ('observation_stopped_before_development_ended=' + $watchBeforeEnd)
Ensure-Dir $DirWatch | Out-Null
foreach ($wf in @($watchSummaryPath, $watchTxtPath, (Join-Path $WatchOutDir 'watch.log'), (Join-Path $ScratchRoot 'watch-stdout.txt'), (Join-Path $ScratchRoot 'watch-stderr.txt'))) {
    if (Test-Path -LiteralPath $wf) {
        $dest = Join-Path $DirWatch ((Split-Path -Leaf $wf) + '.txt')
        Copy-Item -LiteralPath $wf -Destination $dest -Force
    }
}
$null = Write-JsonEvidence $DirWatch 'p6_watch_summary' ([pscustomobject]@{
    stop_reason = $watchReason; activity_seen = $watchActivity; trace_files = $watchFiles
    trace_lines = $watchLines; missing = $watchMissing
    observation_stopped_before_development_ended = $watchBeforeEnd
    marker = $MarkerFile; watcher = $WatcherPath
    invocation = 'powershell -EncodedCommand with -TracePath ''<glob>'',''<progress>'' (BREAKOUT-FINDINGS-R3 F2)'
    trace_paths = @($TraceGlob, $ProgressTrace)
})

$summary = [pscustomobject]@{
    task = 'TASK-066'
    role = 'B'
    started = $script:StartedAt.ToString('o', $InvariantCulture)
    finished = (Get-Date).ToString('o', $InvariantCulture)
    head = $head
    branch = $branch
    contract_sha256 = $contractSha
    editor_port = $EditorPort
    game_port = $GamePort
    editor_tools_list_count = $listACount
    game_tools_list_count = $listGCount
    checks_passed = @($script:Checks | Where-Object { $_.pass }).Count
    checks_failed = @($script:Checks | Where-Object { -not $_.pass }).Count
    checks = $script:Checks
    findings = $script:Findings
    pixel_pairs = $script:PixelPairs
    scale2_total_pixels = $realATotal
    scale1_total_pixels = [int]$capRealB.total_pixels
    scale4_total_pixels = [int]$capRealC.total_pixels
    scope_default_count = @($defSet | Sort-Object -Unique).Count
    scope_user_count = @($userSet | Sort-Object -Unique).Count
    scope_internal_count = @($intSet | Sort-Object -Unique).Count
    a_reported_scope_counts = 'all=207 user=1 internal=206 with one persisted connection'
    watch = [pscustomobject]@{ stop_reason = $watchReason; activity_seen = $watchActivity; trace_lines = $watchLines; trace_files = $watchFiles; missing = $watchMissing }
    evidence_root = $EvidenceRoot
}
$summaryPath = Join-Path $DirPre 'run-summary.json'
[IO.File]::WriteAllText($summaryPath, (($summary | ConvertTo-Json -Depth 30).Replace("`r`n", "`n")), (New-Object Text.UTF8Encoding($false)))
Add-Heartbeat ('summary written ' + $summaryPath)

Write-Host ''
Write-Host ('B066 RESULT checks_passed=' + $summary.checks_passed + ' checks_failed=' + $summary.checks_failed)
Write-Host ('B066 FAILED_IDS ' + (@($script:Checks | Where-Object { -not $_.pass } | ForEach-Object { $_.id }) -join ','))
Write-Host ('B066 WATCH stop_reason=' + $watchReason + ' activity_seen=' + $watchActivity + ' trace_lines=' + $watchLines)
Write-Host ('B066 SUMMARY ' + $summaryPath)
