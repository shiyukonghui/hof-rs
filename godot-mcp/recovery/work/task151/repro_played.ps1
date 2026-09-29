# =============================================================================
#  repro_played.ps1 -- TASK-151 faithful reproduction.
#
#  The first pass (repro.ps1) started the game by hand, without `--remote-debug`,
#  and the defect did NOT reproduce: both compile-failing bodies answered -32602.
#
#  The real smoke run's game process was created by the editor's
#  `editor_play_scene`, and `EditorRun::run()` (editor/run/editor_run.cpp:64-68)
#  always appends `--remote-debug <EditorDebuggerNode server uri>` to the child's
#  command line. That is the difference this script reproduces: the same
#  compile-failing request, on a game child *spawned by an editor*, i.e. one
#  with a debugger peer attached.
#
#  Port discipline: 9888 (our editor) / 9889 (the played game). 9877 is only
#  observed. Only processes this script caused to exist are stopped.
# =============================================================================
param(
    [switch]$KeepRunning,
    [int]$Heartbeats = 6
)

$ErrorActionPreference = 'Stop'

$Engine = 'F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.console.exe'
$EditorPort = 9888
$GamePort = 9889
$UserPort = 9877
$Root = Join-Path $env:TEMP 'mcp151'
$Proj = Join-Path $Root 'proj'
$LogDir = Join-Path $Root 'logs-played'
$Evid = Join-Path $PSScriptRoot 'evidence-played'
New-Item -ItemType Directory -Force -Path $LogDir, $Evid | Out-Null

$script:StartedPids = New-Object System.Collections.Generic.List[object]
$script:Log = New-Object System.Collections.Generic.List[string]

function Say {
    param([string]$Text)
    $line = ("[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss.fff'), $Text)
    Write-Host $line
    $script:Log.Add($line)
}

function ListenPids {
    param([int]$Port)
    $c = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($c) { return (@($c | Select-Object -ExpandProperty OwningProcess) | Sort-Object -Unique) }
    return @()
}

function Wait-ForTcp {
    param([int]$Port, [int]$TimeoutMs = 180000)
    $deadline = [DateTime]::UtcNow.AddMilliseconds($TimeoutMs)
    while ([DateTime]::UtcNow -lt $deadline) {
        $client = New-Object System.Net.Sockets.TcpClient
        try {
            $task = $client.ConnectAsync('127.0.0.1', $Port)
            if ($task.Wait(700) -and $client.Connected) { return $true }
        } catch { } finally { $client.Close() }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Raw-Exchange {
    param([int]$Port, [string]$RequestText, [int]$TimeoutMs = 20000, [string]$Label = 'call')
    $bodyBytes = [Text.Encoding]::UTF8.GetBytes($RequestText)
    $client = New-Object System.Net.Sockets.TcpClient
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $statusLine = ''
    $responseText = ''
    $errorMessage = ''
    $bytesRead = 0
    $connected = $false
    try {
        $ct = $client.ConnectAsync('127.0.0.1', $Port)
        if (-not $ct.Wait(5000)) { throw 'connect timeout' }
        $connected = $true
        $stream = $client.GetStream()
        $stream.ReadTimeout = $TimeoutMs
        $stream.WriteTimeout = $TimeoutMs
        $stream.Write($bodyBytes, 0, $bodyBytes.Length)
        $stream.Flush()
        $buf = New-Object byte[] 65536
        $acc = New-Object System.IO.MemoryStream
        $headerEnd = -1
        $contentLength = -1
        while ($true) {
            $n = $stream.Read($buf, 0, $buf.Length)
            if ($n -le 0) { break }
            $acc.Write($buf, 0, $n)
            $bytesRead += $n
            $all = [Text.Encoding]::UTF8.GetString($acc.ToArray())
            if ($statusLine -eq '') {
                $idx = $all.IndexOf("`r`n")
                if ($idx -ge 0) { $statusLine = $all.Substring(0, $idx) }
            }
            if ($headerEnd -lt 0) {
                $hIdx = $all.IndexOf("`r`n`r`n")
                if ($hIdx -ge 0) {
                    $headerEnd = $hIdx + 4
                    $head = $all.Substring(0, $hIdx)
                    foreach ($h in ($head -split "`r`n")) {
                        if ($h -match '^(?i)Content-Length:\s*(\d+)') { $contentLength = [int]$Matches[1] }
                    }
                    if ($contentLength -eq 0) { break }
                }
            }
            if ($headerEnd -ge 0 -and $contentLength -ge 0) {
                # byte-accurate body length: re-encode is not safe for multi-byte
                # bodies, so use the raw byte count against the byte header size.
                $headerBytes = [Text.Encoding]::UTF8.GetByteCount($all.Substring(0, $headerEnd))
                if (($bytesRead - $headerBytes) -ge $contentLength) { break }
            }
        }
        $raw = [Text.Encoding]::UTF8.GetString($acc.ToArray())
        if ($headerEnd -ge 0) { $responseText = $raw.Substring($headerEnd) }
        elseif ($raw.Length -gt 0) { $responseText = $raw }
    } catch {
        $errorMessage = $_.Exception.Message
    } finally {
        try { $client.Close() } catch { }
    }
    $sw.Stop()
    $dump = @(
        ("label={0} port={1} connected={2}" -f $Label, $Port, $connected),
        ("elapsed_ms={0} bytes_read={1}" -f [int]$sw.Elapsed.TotalMilliseconds, $bytesRead),
        ("status_line={0}" -f $(if ($statusLine -eq '') { '<NONE>' } else { $statusLine })),
        ("io_error={0}" -f $(if ($errorMessage -eq '') { '<none>' } else { $errorMessage })),
        ("request={0}" -f $RequestText),
        ("response_body={0}" -f $responseText)
    )
    [IO.File]::WriteAllLines((Join-Path $Evid ($Label + '.txt')), $dump, (New-Object Text.UTF8Encoding($false)))
    Say ("{0}: status_line={1} elapsed_ms={2} bytes={3} io_error={4}" -f `
            $Label, $(if ($statusLine -eq '') { '<NONE>' } else { $statusLine }), [int]$sw.Elapsed.TotalMilliseconds, $bytesRead, `
        $(if ($errorMessage -eq '') { '<none>' } else { $errorMessage }))
    if ($responseText -ne '') {
        $shown = if ($responseText.Length -gt 900) { $responseText.Substring(0, 900) + '...<truncated>' } else { $responseText }
        Say ("    body={0}" -f $shown)
    }
    return [pscustomobject]@{
        StatusLine = $statusLine
        Body       = $responseText
        ElapsedMs  = [int]$sw.Elapsed.TotalMilliseconds
        Error      = $errorMessage
        Bytes      = $bytesRead
        Connected  = $connected
    }
}

function Post-Mcp {
    param([int]$Port, [string]$Json, [int]$TimeoutMs = 20000, [string]$Label = 'call')
    $bodyBytes = [Text.Encoding]::UTF8.GetBytes($Json)
    $req = ("POST /mcp HTTP/1.1`r`nHost: 127.0.0.1:{0}`r`nContent-Type: application/json`r`nContent-Length: {1}`r`n`r`n{2}" -f $Port, $bodyBytes.Length, $Json)
    return Raw-Exchange -Port $Port -RequestText $req -TimeoutMs $TimeoutMs -Label $Label
}

function Get-McpStatus {
    param([int]$Port, [string]$Label)
    $req = ("GET /mcp HTTP/1.1`r`nHost: 127.0.0.1:{0}`r`nAccept: application/json`r`n`r`n" -f $Port)
    return Raw-Exchange -Port $Port -RequestText $req -TimeoutMs 8000 -Label $Label
}

function ToolCall {
    param([string]$Name, [hashtable]$Arguments, [int]$Id)
    $argJson = ($Arguments.GetEnumerator() | ForEach-Object {
            if ($_.Value -is [bool]) { '"{0}":{1}' -f $_.Key, $_.Value.ToString().ToLower() }
            elseif ($_.Value -is [int] -or $_.Value -is [long]) { '"{0}":{1}' -f $_.Key, $_.Value }
            else { '"{0}":{1}' -f $_.Key, (ConvertTo-Json $_.Value -Compress) }
        }) -join ','
    $prefix = '{"jsonrpc":"2.0","id":' + $Id + ',"method":"tools/call","params":{"name":"' + $Name + '","arguments":{'
    return ($prefix + $argJson + '}}}')
}

function Start-Engine {
    param([string[]]$Arguments, [string]$LogName)
    $out = Join-Path $LogDir ($LogName + '.out.log')
    $err = Join-Path $LogDir ($LogName + '.err.log')
    Remove-Item -Path $out, $err -ErrorAction SilentlyContinue
    $proc = Start-Process -FilePath $Engine -ArgumentList $Arguments -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden
    $cmdline = (Get-CimInstance Win32_Process -Filter ("ProcessId=" + $proc.Id)).CommandLine
    $script:StartedPids.Add([pscustomobject]@{ Id = $proc.Id; CommandLine = $cmdline; LogName = $LogName })
    Say ("STARTED pid={0} log={1}" -f $proc.Id, $LogName)
    Say ("        cmdline={0}" -f $cmdline)
    return [pscustomobject]@{ Process = $proc; Out = $out; Err = $err; Id = $proc.Id }
}

function Stop-ProcessTree {
    param([int]$TargetPid)
    $kids = @(Get-CimInstance Win32_Process -Filter ("ParentProcessId=" + $TargetPid) -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like 'godot*' })
    foreach ($k in $kids) { Say ("  child of pid={0}: pid={1} {2}" -f $TargetPid, $k.ProcessId, $k.CommandLine) }
    try { Stop-Process -Id $TargetPid -Force -ErrorAction SilentlyContinue; Say ("STOPPED pid={0} (we started it)" -f $TargetPid) } catch { }
}

# -----------------------------------------------------------------------------
Say '=== TASK-151 faithful reproduction: compile-failing GDScript on a PLAYED game ==='
Say ("PORT-GUARD before: 9877 = {0} | 9888 = {1} | 9889 = {2}" -f ((ListenPids 9877) -join ','), ((ListenPids 9888) -join ','), ((ListenPids 9889) -join ','))

$editor = Start-Engine -Arguments @('--headless', '-e', '--path', $Proj, '--mcp-port=9888') -LogName 'editor'
if (-not (Wait-ForTcp -Port $EditorPort -TimeoutMs 180000)) { throw 'editor 9888 never came up' }
Say 'editor 9888 is listening'
Post-Mcp -Port $EditorPort -Label 'editor-tools-list' -TimeoutMs 20000 -Json '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | Out-Null

# --- the editor plays the scene; this is what puts a debugger peer on the game --
$playReq = ToolCall -Name 'editor_play_scene' -Id 2 -Arguments @{ mcp_port = $GamePort; headless = $true }
$play = Post-Mcp -Port $EditorPort -Label 'editor-play-scene' -TimeoutMs 60000 -Json $playReq
$playJson = $null
try { $playJson = $play.Body | ConvertFrom-Json } catch { }
$gamePid = $null
if ($playJson -and $playJson.result -and $playJson.result.content) {
    $payload = $playJson.result.content[0].text | ConvertFrom-Json
    Say ('play_scene answer: ' + ($playJson.result.content[0].text))
    $gamePid = [int]$payload.pid
} else {
    Say 'play_scene did not answer a payload; cannot continue'
    exit 2
}

if (-not (Wait-ForTcp -Port $GamePort -TimeoutMs 120000)) { throw 'game 9889 never came up' }
Start-Sleep -Seconds 2
$gameCmdline = (Get-CimInstance Win32_Process -Filter ("ProcessId=" + $gamePid)).CommandLine
Say ("GAME pid={0}" -f $gamePid)
Say ("GAME cmdline={0}" -f $gameCmdline)
Say ("GAME has --remote-debug: {0}" -f ($gameCmdline -match '--remote-debug'))
[IO.File]::WriteAllText((Join-Path $Evid 'game-cmdline.txt'), [string]$gameCmdline, (New-Object Text.UTF8Encoding($false)))
[IO.File]::WriteAllText((Join-Path $Evid 'game-pid.txt'), [string]$gamePid, (New-Object Text.UTF8Encoding($false)))

# --- control: the endpoint answers a benign call before the trigger -----------
Post-Mcp -Port $GamePort -Label 'game-tools-list-before' -TimeoutMs 20000 -Json '{"jsonrpc":"2.0","id":10,"method":"tools/list","params":{}}' | Out-Null

# --- THE TRIGGER: the first compile-failing body -----------------------------
$trigger = ToolCall -Name 'running_game_execute_gdscript' -Id 11 -Arguments @{ code = 'return str(Input.action_press("move_right"))' }
$call = Post-Mcp -Port $GamePort -Label 'game-call-analyzer-error' -TimeoutMs 20000 -Json $trigger

# --- a second, independent connection after the freeze -----------------------
$call2 = Post-Mcp -Port $GamePort -Label 'game-call-2-after-freeze' -TimeoutMs 20000 `
    -Json (ToolCall -Name 'running_game_execute_gdscript' -Id 12 -Arguments @{ code = 'return 1 + 1' })

# --- is the main thread still pumping frames? --------------------------------
for ($i = 1; $i -le $Heartbeats; $i++) {
    $listen = (ListenPids $GamePort) -join ','
    $alive = $null -ne (Get-Process -Id $gamePid -ErrorAction SilentlyContinue)
    $st = Get-McpStatus -Port $GamePort -Label ("game-status-{0:d2}" -f $i)
    Say ("T+{0}s alive={1} listen={2} listen_pids={3}" -f ($i * 10), $alive, $(if ($listen) { 'yes' } else { 'NONE' }), $listen)
    Start-Sleep -Seconds 10
}

# --- decisive control: disconnect the debugger peer, then ask again ----------
Say '=== CONTROL: stop the editor (the debugger peer) and ask the frozen game again ==='
Stop-ProcessTree -TargetPid $editor.Id
Start-Sleep -Seconds 8
$afterEditorGone = Post-Mcp -Port $GamePort -Label 'game-call-after-editor-gone' -TimeoutMs 20000 `
    -Json (ToolCall -Name 'running_game_execute_gdscript' -Id 13 -Arguments @{ code = 'return str(Input.action_press("move_right"))' })
$aliveEnd = $null -ne (Get-Process -Id $gamePid -ErrorAction SilentlyContinue)
Say ("game alive after editor gone = {0}, 9889 listen = {1}" -f $aliveEnd, ((ListenPids $GamePort) -join ','))

foreach ($l in (Get-Content (Join-Path $LogDir 'editor.out.log') -Tail 25 -ErrorAction SilentlyContinue)) { Say ('  editor.out | ' + $l) }
foreach ($l in (Get-Content (Join-Path $LogDir 'editor.err.log') -Tail 25 -ErrorAction SilentlyContinue)) { Say ('  editor.err | ' + $l) }

if (-not $KeepRunning -and $gamePid) { Stop-ProcessTree -TargetPid $gamePid }
Say ("PORT-GUARD after: 9877 = {0}" -f ((ListenPids 9877) -join ','))

[IO.File]::WriteAllLines((Join-Path $Evid 'timeline.txt'), $script:Log.ToArray(), (New-Object Text.UTF8Encoding($false)))
Say ('timeline written to ' + (Join-Path $Evid 'timeline.txt'))

