# =============================================================================
#  repro_peer.ps1 -- TASK-151, the confound-free root-cause control.
#
#  repro_played.ps1 proved the freeze on a game child spawned by
#  `editor_play_scene`, whose command line carries
#  `--remote-debug tcp://127.0.0.1:6007` (the editor's debugger server). Killing
#  the editor there was not a clean control: `EditorRun::run()` also passes
#  `--editor-pid`, and the game exits by itself as soon as that pid disappears.
#
#  This script removes both confounds: the game is started by hand with
#  `--remote-debug tcp://127.0.0.1:6011` and NO `--editor-pid`, and 6011 is a
#  plain TCPServer owned by this script. The peer is therefore under our control:
#
#    1. endpoint healthy (tools/list answers),
#    2. a compile-failing body -> nothing is read before the peer is released,
#    3. the peer is released (the socket is closed) -> the SAME connection is
#       answered, with -32602 and data.parse_error,
#
#  which separates "the main thread waits for the debugger" from "the process
#  died" and from "the socket was lost".
#
#  Port discipline: 9889 is ours; the debugger peer port is 6011 (loopback, our
#  own listener); 9877 is only observed.
# =============================================================================
param(
    [int]$PeerPort = 6011,
    [int]$HoldSeconds = 25
)

$ErrorActionPreference = 'Stop'

$Engine = 'F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.console.exe'
$GamePort = 9889
$Root = Join-Path $env:TEMP 'mcp151'
$Proj = Join-Path $Root 'proj'
$LogDir = Join-Path $Root 'logs-peer'
$Evid = Join-Path $PSScriptRoot 'evidence-peer'
New-Item -ItemType Directory -Force -Path $LogDir, $Evid | Out-Null

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
    param([int]$Port, [int]$TimeoutMs = 60000)
    $deadline = [DateTime]::UtcNow.AddMilliseconds($TimeoutMs)
    while ([DateTime]::UtcNow -lt $deadline) {
        $client = New-Object System.Net.Sockets.TcpClient
        try {
            $task = $client.ConnectAsync('127.0.0.1', $Port)
            if ($task.Wait(500) -and $client.Connected) { return $true }
        } catch { } finally { $client.Close() }
        Start-Sleep -Milliseconds 400
    }
    return $false
}

# A POST with an explicit read timeout; the answer is the HTTP body of the SAME
# connection, so "the peer was released and the main thread came back" shows up
# as a body on this very socket.
function Post-Mcp {
    param([int]$Port, [string]$Json, [int]$TimeoutMs = 20000, [string]$Label = 'call')
    $bodyBytes = [Text.Encoding]::UTF8.GetBytes($Json)
    $head = "POST /mcp HTTP/1.1`r`nHost: 127.0.0.1:$Port`r`nContent-Type: application/json`r`nContent-Length: $($bodyBytes.Length)`r`n`r`n"
    $hb = [Text.Encoding]::ASCII.GetBytes($head)
    $client = New-Object System.Net.Sockets.TcpClient
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $status = ''
    $body = ''
    $err = ''
    $bytes = 0
    try {
        if (-not $client.ConnectAsync('127.0.0.1', $Port).Wait(5000)) { throw 'connect timeout' }
        $s = $client.GetStream()
        $s.ReadTimeout = $TimeoutMs
        $s.WriteTimeout = $TimeoutMs
        $s.Write($hb, 0, $hb.Length)
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
        if ($headerEnd -ge 0) { $body = $raw.Substring($headerEnd) } else { $body = $raw }
    } catch { $err = $_.Exception.Message }
    finally { try { $client.Close() } catch { } }
    $sw.Stop()
    $dump = @(
        ("label={0} port={1}" -f $Label, $Port),
        ("elapsed_ms={0} bytes_read={1}" -f [int]$sw.Elapsed.TotalMilliseconds, $bytes),
        ("status_line={0}" -f $(if ($status -eq '') { '<NONE>' } else { $status })),
        ("io_error={0}" -f $(if ($err -eq '') { '<none>' } else { $err })),
        ("request={0}" -f $Json),
        ("response_body={0}" -f $body)
    )
    [IO.File]::WriteAllLines((Join-Path $Evid ($Label + '.txt')), $dump, (New-Object Text.UTF8Encoding($false)))
    Say ("{0}: status_line={1} elapsed_ms={2} bytes={3} io_error={4}" -f $Label, `
        $(if ($status -eq '') { '<NONE>' } else { $status }), [int]$sw.Elapsed.TotalMilliseconds, $bytes, $(if ($err -eq '') { '<none>' } else { $err }))
    if ($body -ne '') {
        $shown = if ($body.Length -gt 800) { $body.Substring(0, 800) + '...<truncated>' } else { $body }
        Say ("    body={0}" -f $shown)
    }
    return [pscustomobject]@{ Status = $status; Body = $body; ElapsedMs = [int]$sw.Elapsed.TotalMilliseconds }
}

Say '=== TASK-151 root-cause control: --remote-debug peer, no --editor-pid ==='
Say ("PORT-GUARD before: 9877 = {0} | 9889 = {1} | {2} = {3}" -f ((ListenPids 9877) -join ','), ((ListenPids 9889) -join ','), $PeerPort, ((ListenPids $PeerPort) -join ','))

# --- our own debugger peer: accept, hold, then close -------------------------
$peerJob = Start-Job -ScriptBlock {
    param($Port, $HoldMs)
    $l = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $Port)
    $l.Start()
    $c = $l.AcceptTcpClient()
    $acceptedAt = Get-Date
    Start-Sleep -Milliseconds $HoldMs
    $c.Close()
    $l.Stop()
    return @{ accepted_at = $acceptedAt.ToString('o'); held_ms = $HoldMs }
} -ArgumentList $PeerPort, ($HoldSeconds * 1000)
Start-Sleep -Seconds 2
Say ("debugger peer listener up on 127.0.0.1:{0} (job pid {1})" -f $PeerPort, $peerJob.Id)
Say ("peer port listen pids = {0}" -f ((ListenPids $PeerPort) -join ','))

# --- the game: --remote-debug points at our peer, and nothing else -----------
$out = Join-Path $LogDir 'game.out.log'
$err = Join-Path $LogDir 'game.err.log'
$game = Start-Process -FilePath $Engine -PassThru -WindowStyle Hidden `
    -ArgumentList @('--headless', '--path', $Proj, '--remote-debug', ("tcp://127.0.0.1:{0}" -f $PeerPort), '--mcp-port=9889') `
    -RedirectStandardOutput $out -RedirectStandardError $err
$cmdline = (Get-CimInstance Win32_Process -Filter ("ProcessId=" + $game.Id)).CommandLine
Say ("STARTED game pid={0}" -f $game.Id)
Say ("        cmdline={0}" -f $cmdline)
Say ("        has --remote-debug = {0} ; has --editor-pid = {1}" -f ($cmdline -match '--remote-debug'), ($cmdline -match '--editor-pid'))
[IO.File]::WriteAllText((Join-Path $Evid 'game-cmdline.txt'), [string]$cmdline, (New-Object Text.UTF8Encoding($false)))
[IO.File]::WriteAllText((Join-Path $Evid 'game-pid.txt'), [string]$game.Id, (New-Object Text.UTF8Encoding($false)))

if (-not (Wait-ForTcp -Port $GamePort -TimeoutMs 90000)) { Say 'FATAL: 9889 never came up'; exit 2 }
Start-Sleep -Seconds 1
Say '9889 is listening'
Post-Mcp -Port $GamePort -Label 'game-tools-list-before' -TimeoutMs 20000 `
    -Json '{"jsonrpc":"2.0","id":10,"method":"tools/list","params":{}}' | Out-Null

# --- THE TRIGGER, read timeout > the peer's hold -----------------------------
$trigger = '{"jsonrpc":"2.0","id":11,"method":"tools/call","params":{"name":"running_game_execute_gdscript","arguments":{"code":"return str(Input.action_press(\"move_right\"))"}}}'
Say ("sending the compile-failing body; the peer will be released after {0}s" -f $HoldSeconds)
$call = Post-Mcp -Port $GamePort -Label 'game-call-analyzer-error' -TimeoutMs (($HoldSeconds + 30) * 1000) -Json $trigger

$alive = $null -ne (Get-Process -Id $game.Id -ErrorAction SilentlyContinue)
Say ("after the answer: game alive = {0} ; 9889 listen = {1}" -f $alive, ((ListenPids $GamePort) -join ','))
Post-Mcp -Port $GamePort -Label 'game-tools-list-after' -TimeoutMs 20000 `
    -Json '{"jsonrpc":"2.0","id":12,"method":"tools/list","params":{}}' | Out-Null

Say '--- game stdout tail ---'
foreach ($l in (Get-Content $out -Tail 20 -ErrorAction SilentlyContinue)) { Say ('  | ' + $l) }
Say '--- game stderr tail ---'
foreach ($l in (Get-Content $err -Tail 20 -ErrorAction SilentlyContinue)) { Say ('  | ' + $l) }

Receive-Job -Job $peerJob -Wait -AutoRemoveJob | ForEach-Object { Say ('  peer job: ' + $_) }
try { if (-not $game.HasExited) { Stop-Process -Id $game.Id -Force; Say ("STOPPED pid={0} (we started it)" -f $game.Id) } } catch { }
Say ("PORT-GUARD after: 9877 = {0}" -f ((ListenPids 9877) -join ','))

[IO.File]::WriteAllLines((Join-Path $Evid 'timeline.txt'), $script:Log.ToArray(), (New-Object Text.UTF8Encoding($false)))
Say ('timeline written to ' + (Join-Path $Evid 'timeline.txt'))
