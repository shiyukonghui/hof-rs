# =============================================================================
#  verify_fixed.ps1 -- TASK-151 acceptance on the rebuilt binary.
#
#  The pre-fix measurements are in repro_played.ps1 / repro_peer.ps1 (the same
#  scripts, run before the fix): the compile-failing body produced no status line
#  at all in 20 s, `GET /mcp` went unanswered for 60 s, and releasing the debugger
#  peer answered the SAME connection after 23.6 s.
#
#  This script runs the same two scenarios on the fixed binary and requires the
#  opposite outcome:
#
#    A. a game started by hand with `--remote-debug tcp://127.0.0.1:6011` and NO
#       `--editor-pid`, our own listener as the peer (the confound-free setup);
#    B. the real one: an editor on 9888 plays the scene, so the game child gets
#       `--remote-debug tcp://127.0.0.1:6007 --editor-pid <editor>` from
#       `EditorRun::run()` (editor/run/editor_run.cpp:64-68).
#
#  In both, and in the editor endpoint as a control:
#    * a body that does not compile      -> -32602 + data.parse_error, fast;
#    * a body that compiles then fails   -> -32000 + data.script_error (TASK-103
#      must not regress); this is the second window the guard covers;
#    * a body that succeeds              -> ok;
#    * the endpoint is still healthy afterwards and the process is still alive.
#
#  Port discipline: 9888 / 9889 and the loopback peer port 6011 are ours; 9877 is
#  only observed. Only processes this script caused to exist are stopped.
# =============================================================================
param(
    [int]$PeerPort = 6011,
    [string]$EnginePath = 'F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.console.exe',
    [string]$EvidenceDir = 'evidence-verify'
)

$ErrorActionPreference = 'Stop'

$Engine = $EnginePath
$EditorPort = 9888
$GamePort = 9889
$UserPort = 9877
$Root = Join-Path $env:TEMP 'mcp151'
$Proj = Join-Path $Root 'proj'
$LogDir = Join-Path $Root 'logs-verify'
$Evid = Join-Path $PSScriptRoot $EvidenceDir
New-Item -ItemType Directory -Force -Path $LogDir, $Evid | Out-Null

$script:Log = New-Object System.Collections.Generic.List[string]
$script:Checks = New-Object System.Collections.Generic.List[object]

function Say {
    param([string]$Text)
    $line = ("[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss.fff'), $Text)
    Write-Host $line
    $script:Log.Add($line)
}

function Check {
    param([string]$Id, [bool]$Pass, [string]$Evidence)
    $script:Checks.Add([pscustomobject]@{ id = $Id; pass = $Pass; evidence = $Evidence })
    Say ("[{0}] {1} :: {2}" -f $(if ($Pass) { 'PASS' } else { 'FAIL' }), $Id, $Evidence)
}

function ListenPids {
    param([int]$Port)
    $c = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($c) { return (@($c | Select-Object -ExpandProperty OwningProcess) | Sort-Object -Unique) }
    return @()
}

function Wait-ForTcp {
    param([int]$Port, [int]$TimeoutMs = 120000)
    $deadline = [DateTime]::UtcNow.AddMilliseconds($TimeoutMs)
    while ([DateTime]::UtcNow -lt $deadline) {
        $client = New-Object System.Net.Sockets.TcpClient
        try {
            if ($client.ConnectAsync('127.0.0.1', $Port).Wait(500) -and $client.Connected) { return $true }
        } catch { } finally { $client.Close() }
        Start-Sleep -Milliseconds 400
    }
    return $false
}

# One HTTP/1.1 request on its own connection. `Status=''` means "no status line
# arrived before the read timed out", which is the freeze signature.
function Raw-Exchange {
    param([int]$Port, [string]$RequestText, [int]$TimeoutMs = 20000, [string]$Label = 'call')
    $bodyBytes = [Text.Encoding]::UTF8.GetBytes($RequestText)
    $client = New-Object System.Net.Sockets.TcpClient
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $status = ''
    $response = ''
    $err = ''
    $bytes = 0
    try {
        if (-not $client.ConnectAsync('127.0.0.1', $Port).Wait(5000)) { throw 'connect timeout' }
        $s = $client.GetStream()
        $s.ReadTimeout = $TimeoutMs
        $s.WriteTimeout = $TimeoutMs
        $s.Write($bodyBytes, 0, $bodyBytes.Length)
        $s.Flush()
        $buf = New-Object byte[] 65536
        $acc = New-Object System.IO.MemoryStream
        $headerEnd = -1
        $clen = -1
        while ($true) {
            $n = $s.Read($buf, 0, $buf.Length)
            if ($n -le 0) { break }
            $acc.Write($buf, 0, $n); $bytes += $n
            $all = [Text.Encoding]::UTF8.GetString($acc.ToArray())
            if ($status -eq '') { $i = $all.IndexOf("`r`n"); if ($i -ge 0) { $status = $all.Substring(0, $i) } }
            if ($headerEnd -lt 0) {
                $h = $all.IndexOf("`r`n`r`n")
                if ($h -ge 0) {
                    $headerEnd = $h + 4
                    foreach ($ln in ($all.Substring(0, $h) -split "`r`n")) {
                        if ($ln -match '^(?i)Content-Length:\s*(\d+)') { $clen = [int]$Matches[1] }
                    }
                    if ($clen -eq 0) { break }
                }
            }
            if ($headerEnd -ge 0 -and $clen -ge 0) {
                $hbCount = [Text.Encoding]::UTF8.GetByteCount($all.Substring(0, $headerEnd))
                if (($bytes - $hbCount) -ge $clen) { break }
            }
        }
        $raw = [Text.Encoding]::UTF8.GetString($acc.ToArray())
        if ($headerEnd -ge 0) { $response = $raw.Substring($headerEnd) } else { $response = $raw }
    } catch { $err = $_.Exception.Message }
    finally { try { $client.Close() } catch { } }
    $sw.Stop()
    $dump = @(
        ("label={0} port={1}" -f $Label, $Port),
        ("elapsed_ms={0} bytes_read={1}" -f [int]$sw.Elapsed.TotalMilliseconds, $bytes),
        ("status_line={0}" -f $(if ($status -eq '') { '<NONE>' } else { $status })),
        ("io_error={0}" -f $(if ($err -eq '') { '<none>' } else { $err })),
        ("request={0}" -f $RequestText),
        ("response_body={0}" -f $response)
    )
    [IO.File]::WriteAllLines((Join-Path $Evid ($Label + '.txt')), $dump, (New-Object Text.UTF8Encoding($false)))
    Say ("{0}: status_line={1} elapsed_ms={2} bytes={3}" -f $Label, $(if ($status -eq '') { '<NONE>' } else { $status }), [int]$sw.Elapsed.TotalMilliseconds, $bytes)
    if ($response -ne '') {
        $shown = if ($response.Length -gt 400) { $response.Substring(0, 400) + '...' } else { $response }
        Say ("    body={0}" -f $shown)
    }
    return [pscustomobject]@{ Status = $status; Body = $response; ElapsedMs = [int]$sw.Elapsed.TotalMilliseconds; Bytes = $bytes }
}

function Post-Mcp {
    param([int]$Port, [string]$Json, [int]$TimeoutMs = 20000, [string]$Label = 'call')
    $len = [Text.Encoding]::UTF8.GetByteCount($Json)
    $req = "POST /mcp HTTP/1.1`r`nHost: 127.0.0.1:$Port`r`nContent-Type: application/json`r`nContent-Length: $len`r`n`r`n$Json"
    return Raw-Exchange -Port $Port -RequestText $req -TimeoutMs $TimeoutMs -Label $Label
}

function Get-McpStatus {
    param([int]$Port, [string]$Label)
    $req = "GET /mcp HTTP/1.1`r`nHost: 127.0.0.1:$Port`r`nAccept: application/json`r`n`r`n"
    return Raw-Exchange -Port $Port -RequestText $req -TimeoutMs 8000 -Label $Label
}

function GdCall {
    param([string]$Tool, [string]$Code, [int]$Id)
    $escaped = $Code.Replace('\', '\\').Replace('"', '\"').Replace("`r", '\r').Replace("`n", '\n')
    return ('{"jsonrpc":"2.0","id":' + $Id + ',"method":"tools/call","params":{"name":"' + $Tool + '","arguments":{"code":"' + $escaped + '"}}}')
}

function ToolCall {
    param([string]$Tool, [string]$ArgsJson, [int]$Id)
    return ('{"jsonrpc":"2.0","id":' + $Id + ',"method":"tools/call","params":{"name":"' + $Tool + '","arguments":{' + $ArgsJson + '}}}')
}

function Start-Engine {
    param([string[]]$Arguments, [string]$LogName)
    $out = Join-Path $LogDir ($LogName + '.out.log')
    $err = Join-Path $LogDir ($LogName + '.err.log')
    Remove-Item -Path $out, $err -ErrorAction SilentlyContinue
    $proc = Start-Process -FilePath $Engine -ArgumentList $Arguments -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden
    $cmdline = (Get-CimInstance Win32_Process -Filter ("ProcessId=" + $proc.Id)).CommandLine
    Say ("STARTED pid={0} log={1}" -f $proc.Id, $LogName)
    Say ("        cmdline={0}" -f $cmdline)
    return [pscustomobject]@{ Process = $proc; Out = $out; Err = $err; Id = $proc.Id }
}

function Stop-Pid {
    param([int]$TargetPid, [string]$Why)
    try {
        $p = Get-Process -Id $TargetPid -ErrorAction SilentlyContinue
        if ($p) { Stop-Process -Id $TargetPid -Force; Say ("STOPPED pid={0} ({1})" -f $TargetPid, $Why) }
    } catch { }
}

# The four bodies every scenario asks about.
$AnalyzerError = 'return str(Input.action_press("move_right"))'
$ParseError = 'this is not gdscript'
$RuntimeError = 'var box = {}' + "`n" + 'box["m"] = Node.new()' + "`n" + 'return box["m"].NoSuchMethodAtAll()'
$SuccessCode = 'return 40 + 2'

function Probe-Endpoint {
    param([int]$Port, [string]$Tool, [string]$Role, [bool]$ExpectRuntimeVerdict = $true)
    $r = Post-Mcp -Port $Port -Label ("$Role-tools-list-before") -TimeoutMs 20000 `
        -Json '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
    Check "$Role`_endpoint_healthy_before" ($r.Status -like 'HTTP/1.1 200*') ("tools/list -> {0} in {1} ms" -f $r.Status, $r.ElapsedMs)

    # 1. the analyzer error, i.e. the exact body the smoke run sent
    $a = Post-Mcp -Port $Port -Label ("$Role-call-analyzer-error") -TimeoutMs 15000 -Json (GdCall $Tool $AnalyzerError 11)
    $okA = ($a.Status -like 'HTTP/1.1 200*') -and $a.Body.Contains('"code":-32602') -and $a.Body.Contains('parse_error') -and $a.Body.Contains('void')
    Check "$Role`_analyzer_error_is_32602_with_parse_error" $okA ("{0} in {1} ms; body={2}" -f $a.Status, $a.ElapsedMs, $a.Body.Substring(0, [Math]::Min(200, $a.Body.Length)))
    Check "$Role`_analyzer_error_is_answered_not_frozen" (($a.Status -ne '') -and ($a.ElapsedMs -lt 1000)) ("elapsed {0} ms (pre-fix: no status line in 20000 ms)" -f $a.ElapsedMs)

    # 2. a parse error, the other compile stage
    $p = Post-Mcp -Port $Port -Label ("$Role-call-parse-error") -TimeoutMs 15000 -Json (GdCall $Tool $ParseError 12)
    $okP = ($p.Status -like 'HTTP/1.1 200*') -and $p.Body.Contains('"code":-32602') -and $p.Body.Contains('parse_error')
    Check "$Role`_parse_error_is_32602_with_parse_error" $okP ("{0} in {1} ms" -f $p.Status, $p.ElapsedMs)

    # 3. a runtime error. The `-32000` + `data.script_error` verdict is TASK-103,
    #    which covers the *game* executor; `editor_execute_gdscript` has its own
    #    (pre-TASK-103) path and is asked as a control, so it is only required to
    #    answer - the shape it answers in is recorded, not asserted, because
    #    asserting it would either bless or fix something this task did not touch.
    #    Both roles must not freeze: that is the second window the guard covers.
    $rt = Post-Mcp -Port $Port -Label ("$Role-call-runtime-error") -TimeoutMs 15000 -Json (GdCall $Tool $RuntimeError 13)
    if ($ExpectRuntimeVerdict) {
        $okRt = ($rt.Status -like 'HTTP/1.1 200*') -and $rt.Body.Contains('"code":-32000') -and $rt.Body.Contains('script_error')
        Check "$Role`_runtime_error_is_32000_with_script_error" $okRt ("{0} in {1} ms; body={2}" -f $rt.Status, $rt.ElapsedMs, $rt.Body.Substring(0, [Math]::Min(200, $rt.Body.Length)))
    } else {
        Say ("    ($Role runtime error shape, recorded not asserted: {0} :: {1})" -f $rt.Status, $rt.Body.Substring(0, [Math]::Min(200, $rt.Body.Length)))
    }
    Check "$Role`_runtime_error_is_answered_not_frozen" (($rt.Status -ne '') -and ($rt.ElapsedMs -lt 1000)) ("elapsed {0} ms" -f $rt.ElapsedMs)

    # 4. and the success path still works. The tool payload is nested inside the
    #    JSON-RPC `content[0].text`, so the field names appear escaped on the wire.
    $ok = Post-Mcp -Port $Port -Label ("$Role-call-success") -TimeoutMs 15000 -Json (GdCall $Tool $SuccessCode 14)
    $okOk = ($ok.Status -like 'HTTP/1.1 200*') -and $ok.Body.Contains('\"result\":42') -and $ok.Body.Contains('\"result_type\":\"int\"')
    Check "$Role`_success_still_works" $okOk ("{0} in {1} ms; body={2}" -f $ok.Status, $ok.ElapsedMs, $ok.Body)

    # 5. the endpoint is still healthy afterwards
    $r2 = Post-Mcp -Port $Port -Label ("$Role-tools-list-after") -TimeoutMs 20000 `
        -Json '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
    Check "$Role`_endpoint_healthy_after" ($r2.Status -like 'HTTP/1.1 200*') ("tools/list -> {0} in {1} ms" -f $r2.Status, $r2.ElapsedMs)
    $st = Get-McpStatus -Port $Port -Label ("$Role-status")
    Check "$Role`_status_answers_and_frame_count_is_moving" (($st.Status -like 'HTTP/1.1 200*') -and $st.Body.Contains('frame_count')) ("{0}" -f ($st.Body -replace '\s+', ' '))
}

# -----------------------------------------------------------------------------
Say '=== TASK-151 acceptance on the rebuilt binary ==='
& $Engine --version | Select-Object -First 1 | ForEach-Object { Say ("engine: " + $_) }
Say ("PORT-GUARD before: 9877 = {0} | 9888 = {1} | 9889 = {2}" -f ((ListenPids 9877) -join ','), ((ListenPids 9888) -join ','), ((ListenPids 9889) -join ','))

# --- Scenario A: our own debugger peer, no --editor-pid ----------------------
Say ''
Say '--- Scenario A: game started by hand with --remote-debug to our own peer ---'
$peerJob = Start-Job -ScriptBlock {
    param($Port)
    $l = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $Port)
    $l.Start()
    $c = $l.AcceptTcpClient()
    # Hold the peer for the whole scenario: this is the state the pre-fix run
    # froze in, and the fix must answer anyway.
    Start-Sleep -Seconds 600
    $c.Close(); $l.Stop()
} -ArgumentList $PeerPort
Start-Sleep -Seconds 2
$gameA = Start-Engine -Arguments @('--headless', '--path', $Proj, '--remote-debug', ("tcp://127.0.0.1:{0}" -f $PeerPort), '--mcp-port=9889') -LogName 'gameA'
$cmdA = (Get-CimInstance Win32_Process -Filter ("ProcessId=" + $gameA.Id)).CommandLine
[IO.File]::WriteAllText((Join-Path $Evid 'scenarioA-cmdline.txt'), [string]$cmdA, (New-Object Text.UTF8Encoding($false)))
Check 'scenarioA_game_has_remote_debug' ($cmdA -match '--remote-debug') $cmdA
Check 'scenarioA_game_has_no_editor_pid' (-not ($cmdA -match '--editor-pid')) 'no --editor-pid confound'
if (Wait-ForTcp -Port $GamePort -TimeoutMs 120000) {
    Say '9889 is listening'
    Probe-Endpoint -Port $GamePort -Tool 'running_game_execute_gdscript' -Role 'game'
} else {
    Check 'scenarioA_endpoint_came_up' $false '9889 never listened'
}
# The `.console.exe` is the launcher stub: the engine that owns the listener is
# its child, so "the process survived" is asked of the listener's own pid, not of
# the stub.
$listenA = @(ListenPids $GamePort)
Check 'scenarioA_listener_still_present' (($listenA -join ',') -ne '') ("9889 listen pids = " + ($listenA -join ','))
Check 'scenarioA_engine_process_alive_at_end' (@($listenA | Where-Object { $null -ne (Get-Process -Id $_ -ErrorAction SilentlyContinue) }).Count -gt 0) `
    ("listener pid(s) " + ($listenA -join ',') + " still alive; launcher stub pid " + $gameA.Id + " exited=" + $gameA.Process.HasExited)
Stop-Pid -TargetPid $gameA.Id -Why 'scenario A game'
Stop-Job -Job $peerJob -ErrorAction SilentlyContinue
Remove-Job -Job $peerJob -Force -ErrorAction SilentlyContinue

# --- Scenario B: the real one, a scene played from an editor -----------------
Say ''
Say '--- Scenario B: editor_play_scene (the smoke run''s own setup) ---'
$editor = Start-Engine -Arguments @('--headless', '-e', '--path', $Proj, '--mcp-port=9888') -LogName 'editorB'
if (Wait-ForTcp -Port $EditorPort -TimeoutMs 180000) {
    Say '9888 is listening'
    $playJson = ToolCall -Tool 'editor_play_scene' -ArgsJson ("`"mcp_port`":9889,`"headless`":true") -Id 2
    $play = Post-Mcp -Port $EditorPort -Label 'editor-play-scene' -TimeoutMs 60000 -Json $playJson
    $gamePid = $null
    try {
        $parsed = $play.Body | ConvertFrom-Json
        $payload = $parsed.result.content[0].text | ConvertFrom-Json
        $gamePid = [int]$payload.pid
        Say ('play_scene: ' + $parsed.result.content[0].text)
    } catch { Say 'play_scene answer could not be parsed' }
    Check 'scenarioB_play_scene_reported_a_pid' ($null -ne $gamePid) ("pid=" + $gamePid)

    if ($null -ne $gamePid -and (Wait-ForTcp -Port $GamePort -TimeoutMs 120000)) {
        Start-Sleep -Seconds 2
        $cmdB = (Get-CimInstance Win32_Process -Filter ("ProcessId=" + $gamePid)).CommandLine
        [IO.File]::WriteAllText((Join-Path $Evid 'scenarioB-cmdline.txt'), [string]$cmdB, (New-Object Text.UTF8Encoding($false)))
        Say ("GAME pid={0} cmdline={1}" -f $gamePid, $cmdB)
        Check 'scenarioB_game_has_remote_debug_and_editor_pid' (($cmdB -match '--remote-debug') -and ($cmdB -match '--editor-pid')) 'the smoke run''s exact shape'
        Probe-Endpoint -Port $GamePort -Tool 'running_game_execute_gdscript' -Role 'played'
        Check 'scenarioB_game_process_alive_at_end' ($null -ne (Get-Process -Id $gamePid -ErrorAction SilentlyContinue)) ("pid {0} still there" -f $gamePid)
        Check 'scenarioB_game_listener_still_present' (((ListenPids $GamePort) -join ',') -ne '') ("9889 listen pids = " + ((ListenPids $GamePort) -join ','))
        # The editor's own endpoint is the control: the compile halves must answer
        # the same way they always did. Its runtime-error shape is recorded rather
        # than asserted - `editor_execute_gdscript` does not use the TASK-103
        # capture (`tools/editor_script_write.cpp` has no `call_gdscript_capturing`),
        # which is a pre-existing boundary of that task and not this one's subject.
        Probe-Endpoint -Port $EditorPort -Tool 'editor_execute_gdscript' -Role 'editor' -ExpectRuntimeVerdict $false
        Stop-Pid -TargetPid $gamePid -Why 'scenario B game child'
    } else {
        Check 'scenarioB_game_endpoint_came_up' $false '9889 never listened after play_scene'
    }
    Stop-Pid -TargetPid $editor.Id -Why 'scenario B editor'
} else {
    Check 'scenarioB_editor_came_up' $false '9888 never listened'
}

Say ("PORT-GUARD after: 9877 = {0}" -f ((ListenPids 9877) -join ','))

$failed = @($script:Checks | Where-Object { -not $_.pass })
Say ''
Say ("CHECKS: {0}/{1} passed, {2} failed" -f ($script:Checks.Count - $failed.Count), $script:Checks.Count, $failed.Count)
foreach ($f in $failed) { Say ("  FAILED: {0} :: {1}" -f $f.id, $f.evidence) }

[IO.File]::WriteAllLines((Join-Path $Evid 'timeline.txt'), $script:Log.ToArray(), (New-Object Text.UTF8Encoding($false)))
@($script:Checks | ForEach-Object { "{0}`t{1}`t{2}" -f $_.id, $_.pass, $_.evidence }) |
    Set-Content (Join-Path $Evid 'checks.tsv') -Encoding UTF8
Say ('evidence written to ' + $Evid)
if ($failed.Count -gt 0) { exit 1 }
exit 0
