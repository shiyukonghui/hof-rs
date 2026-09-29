# =============================================================================
#  repro.ps1 -- TASK-151 minimal reproduction, driven against the *game* process.
#
#  Hypothesis to test: `running_game_execute_gdscript` with a `code` that fails
#  to COMPILE (analyzer error) never answers in the game process, while the same
#  request on the editor endpoint answers -32602.
#
#  Port discipline: 9888 (editor) / 9889 (game). Port 9877 (the dispatcher's
#  running editor) is only OBSERVED, never touched.
# =============================================================================
param(
    [ValidateSet('guard', 'game', 'editor', 'all')]
    [string]$Phase = 'all',
    [switch]$KeepScratch
)

$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\godot')).Path
$Engine = Join-Path $RepoRoot 'bin\godot.windows.editor.x86_64.console.exe'
$EditorPort = 9888
$GamePort = 9889
$UserPort = 9877
$Root = Join-Path $env:TEMP 'mcp151'
$Proj = Join-Path $Root 'proj'
$LogDir = Join-Path $Root 'logs'
$Evid = Join-Path $PSScriptRoot 'evidence'

$script:StartedPids = New-Object System.Collections.Generic.List[object]
$script:Log = New-Object System.Collections.Generic.List[string]

function Say {
    param([string]$Text)
    $line = ("[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss.fff'), $Text)
    Write-Host $line
    $script:Log.Add($line)
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Text)
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    [IO.File]::WriteAllText($Path, $Text, (New-Object Text.UTF8Encoding($false)))
}

function Get-ListenerPid {
    param([int]$Port)
    $c = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($c) { return @($c | Select-Object -ExpandProperty OwningProcess) }
    return @()
}

function Assert-UserPortUntouched {
    param([string]$When)
    $pids = @(Get-ListenerPid -Port $UserPort)
    $text = if ($pids.Count -eq 0) { '<none>' } else { ($pids -join ',') }
    Say ("PORT-GUARD {0}: 9877 listen pids = {1}" -f $When, $text)
    return $text
}

function Wait-ForTcp {
    param([int]$Port, [int]$TimeoutMs = 120000)
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

function Stop-Engine {
    param($Handle)
    if ($null -eq $Handle) { return }
    try {
        if (-not $Handle.Process.HasExited) {
            Stop-Process -Id $Handle.Process.Id -Force -ErrorAction SilentlyContinue
            Say ("STOPPED pid={0} (we started it)" -f $Handle.Process.Id)
        }
    } catch { }
}

# Raw HTTP/1.1 exchange with an explicit per-read timeout, so that "no status
# line arrived" is a measurement rather than a curl error string.
function Send-Raw {
    param([int]$Port, [string]$Json, [int]$TimeoutMs = 15000, [string]$Label = 'call')
    $bodyBytes = [Text.Encoding]::UTF8.GetBytes($Json)
    $header = ("POST /mcp HTTP/1.1`r`nHost: 127.0.0.1:{0}`r`nContent-Type: application/json`r`nContent-Length: {1}`r`n`r`n" -f $Port, $bodyBytes.Length)
    $hb = [Text.Encoding]::ASCII.GetBytes($header)

    $client = New-Object System.Net.Sockets.TcpClient
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $statusLine = ''
    $responseText = ''
    $errorMessage = ''
    $bytesRead = 0
    $connected = $false
    $connectError = ''
    try {
        $ct = $client.ConnectAsync('127.0.0.1', $Port)
        if (-not $ct.Wait(5000)) { throw 'connect timeout' }
        $connected = $true
        $stream = $client.GetStream()
        $stream.ReadTimeout = $TimeoutMs
        $stream.WriteTimeout = $TimeoutMs
        $stream.Write($hb, 0, $hb.Length)
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
                $bodyGot = $bytesRead - $headerEnd
                if ($bodyGot -ge $contentLength) { break }
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

    $outFile = Join-Path $Evid ($Label + '.txt')
    $dump = @(
        ("label={0} port={1} connected={2} connect_error={3}" -f $Label, $Port, $connected, $connectError),
        ("elapsed_ms={0} bytes_read={1}" -f [int]$sw.Elapsed.TotalMilliseconds, $bytesRead),
        ("status_line={0}" -f $(if ($statusLine -eq '') { '<NONE>' } else { $statusLine })),
        ("io_error={0}" -f $(if ($errorMessage -eq '') { '<none>' } else { $errorMessage })),
        ("request={0}" -f $Json),
        ("response_body={0}" -f $responseText)
    )
    [IO.File]::WriteAllLines($outFile, $dump, (New-Object Text.UTF8Encoding($false)))

    Say ("{0}: status_line={1} elapsed_ms={2} bytes={3} io_error={4}" -f `
            $Label, $(if ($statusLine -eq '') { '<NONE>' } else { $statusLine }), [int]$sw.Elapsed.TotalMilliseconds, $bytesRead, `
        $(if ($errorMessage -eq '') { '<none>' } else { $errorMessage }))
    if ($responseText -ne '') { Say ("    body={0}" -f $responseText) }
    return [pscustomobject]@{
        StatusLine = $statusLine
        Body       = $responseText
        ElapsedMs  = [int]$sw.Elapsed.TotalMilliseconds
        Error      = $errorMessage
        Bytes      = $bytesRead
        Connected  = $connected
    }
}

function Get-Health {
    param([int]$Port, [string]$Label)
    return Send-Raw -Port $Port -Json '{"jsonrpc":"2.0","id":9001,"method":"tools/list","params":{}}' -TimeoutMs 8000 -Label $Label
}

function Initialize-Scratch {
    if (Test-Path $Root) { Remove-Item -Recurse -Force $Root }
    New-Item -ItemType Directory -Force -Path $Proj, (Join-Path $Proj 'scenes'), $LogDir, $Evid | Out-Null
    $project = @(
        'config_version=5',
        '',
        '[application]',
        'config/name="mcp151 repro"',
        'config/features=PackedStringArray("4.8")',
        'run/main_scene="res://scenes/main.tscn"',
        '',
        '[input]',
        'move_right={',
        '"deadzone": 0.5,',
        '"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":4194321,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)',
        ']',
        '}',
        '',
        '[rendering]',
        'renderer/rendering_method="gl_compatibility"',
        'renderer/rendering_method.mobile="gl_compatibility"'
    ) -join "`n"
    Write-Utf8NoBom (Join-Path $Proj 'project.godot') ($project + "`n")
    $scene = @(
        '[gd_scene format=3]',
        '',
        '[node name="Main" type="Node2D"]',
        '',
        '[node name="Player" type="Node2D" parent="."]',
        'position = Vector2(0, 0)'
    ) -join "`n"
    Write-Utf8NoBom (Join-Path $Proj 'scenes\main.tscn') ($scene + "`n")
    Say ("scratch project = {0}" -f $Proj)
}

function Import-Scratch {
    $out = Join-Path $LogDir 'import.out.log'
    $err = Join-Path $LogDir 'import.err.log'
    $p = Start-Process -FilePath $Engine -ArgumentList @('--headless', '--mcp-port=0', '--path', $Proj, '--import') `
        -PassThru -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden
    $p.WaitForExit(300000) | Out-Null
    Say ("IMPORT exit={0}" -f $p.ExitCode)
}

# --- Phase: game -------------------------------------------------------------
function Invoke-GamePhase {
    Say '=== PHASE game (port 9889) ==='
    Assert-UserPortUntouched -When 'before'
    $game = Start-Engine -Arguments @('--headless', '--path', $Proj, '--mcp-port=9889') -LogName 'game'
    if (-not (Wait-ForTcp -Port $GamePort -TimeoutMs 120000)) {
        Say 'FATAL: game port 9889 never came up'
        return
    }
    Say '9889 is listening'
    $h0 = Get-Health -Port $GamePort -Label 'game-health-before'
    Save-Marker -Name 'game-pid' -Text ([string]$game.Id)

    # THE TRIGGER: the very first tool call on this endpoint is the one whose
    # `code` does not compile. Two spellings of the failure, in this order.
    $c1 = Send-Raw -Port $GamePort -TimeoutMs 15000 -Label 'game-call-1-parse-error' `
        -Json '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"running_game_execute_gdscript","arguments":{"code":"this is not gdscript"}}}'
    $c2 = Send-Raw -Port $GamePort -TimeoutMs 15000 -Label 'game-call-2-analyzer-error' `
        -Json '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"running_game_execute_gdscript","arguments":{"code":"return str(Input.action_press(\"move_right\"))"}}}'

    # Timeline: does the main thread still pump frames? Is the listener still there?
    for ($i = 1; $i -le 12; $i++) {
        Start-Sleep -Seconds 10
        $alive = -not $game.Process.HasExited
        $pids = @(Get-ListenerPid -Port $GamePort) -join ','
        $h = Send-Raw -Port $GamePort -TimeoutMs 5000 -Label ("game-heartbeat-{0:d2}" -f $i)
        Say ("T+{0}s alive={1} listen={2} status={3}" -f ($i * 10), $alive, $(if ($pids) { $pids } else { 'NONE' }), $(if ($h.StatusLine) { $h.StatusLine } else { '<NONE>' }))
        if (-not $alive) {
            $code = try { $game.Process.ExitCode } catch { '<unreadable>' }
            Say ("GAME PROCESS EXITED after ~{0}s exit_code={1}" -f ($i * 10), $code)
            break
        }
    }
    Save-Marker -Name 'game-alive-at-end' -Text ([string](-not $game.Process.HasExited))
    $gameLog = Join-Path $LogDir 'game.out.log'
    if (Test-Path $gameLog) {
        Say '--- game stdout tail ---'
        foreach ($l in (Get-Content $gameLog -Tail 40)) { Say ('  | ' + $l) }
    }
    $gameErr = Join-Path $LogDir 'game.err.log'
    if (Test-Path $gameErr) {
        Say '--- game stderr tail ---'
        foreach ($l in (Get-Content $gameErr -Tail 40)) { Say ('  | ' + $l) }
    }
    if (-not $KeepScratch) { Stop-Engine -Handle $game }
    Assert-UserPortUntouched -When 'after'
}

# --- Phase: editor -----------------------------------------------------------
function Invoke-EditorPhase {
    Say '=== PHASE editor (port 9888) ==='
    Assert-UserPortUntouched -When 'before'
    $editor = Start-Engine -Arguments @('--headless', '-e', '--path', $Proj, '--mcp-port=9888') -LogName 'editor'
    if (-not (Wait-ForTcp -Port $EditorPort -TimeoutMs 180000)) {
        Say 'FATAL: editor port 9888 never came up'
        return
    }
    Say '9888 is listening'
    Get-Health -Port $EditorPort -Label 'editor-health-before' | Out-Null
    Send-Raw -Port $EditorPort -TimeoutMs 15000 -Label 'editor-call-1-parse-error' `
        -Json '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"editor_execute_gdscript","arguments":{"code":"this is not gdscript"}}}' | Out-Null
    Send-Raw -Port $EditorPort -TimeoutMs 15000 -Label 'editor-call-2-analyzer-error' `
        -Json '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"editor_execute_gdscript","arguments":{"code":"return str(Input.action_press(\"move_right\"))"}}}' | Out-Null
    if (-not $KeepScratch) { Stop-Engine -Handle $editor }
    Assert-UserPortUntouched -When 'after'
}

function Save-Marker {
    param([string]$Name, [string]$Text)
    [IO.File]::WriteAllText((Join-Path $Evid ($Name + '.txt')), $Text, (New-Object Text.UTF8Encoding($false)))
}

# -----------------------------------------------------------------------------
switch ($Phase) {
    'guard' {
        Say 'guard: no engine started'
        Assert-UserPortUntouched -When 'now'
        Say ("9888 listen pids = {0}" -f ((Get-ListenerPid -Port 9888) -join ','))
        Say ("9889 listen pids = {0}" -f ((Get-ListenerPid -Port 9889) -join ','))
    }
    'game' {
        Initialize-Scratch; Import-Scratch; Invoke-GamePhase
    }
    'editor' {
        Initialize-Scratch; Import-Scratch; Invoke-EditorPhase
    }
    'all' {
        Initialize-Scratch; Import-Scratch
        Invoke-GamePhase
        Invoke-EditorPhase
    }
}

[IO.File]::WriteAllLines((Join-Path $Evid 'repro-timeline.txt'), $script:Log.ToArray(), (New-Object Text.UTF8Encoding($false)))
Say ('timeline written to ' + (Join-Path $Evid 'repro-timeline.txt'))
Say 'started pids:'
foreach ($p in $script:StartedPids) { Say ("  pid={0} {1}" -f $p.Id, $p.CommandLine) }

