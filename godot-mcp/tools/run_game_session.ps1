param(
  [Parameter(Mandatory=$true)][string]$Game,
  [string]$Session = '',
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp',
  [string]$RunTag = '',
  [string]$Engine = '',
  [int]$EditorPort = 9888,
  [int]$GamePort = 9889,
  [switch]$SkipReport
)
# =============================================================================
#  run_game_session.ps1 -- the reusable game test driver (TASK-091, D137/D138).
#
#  It starts BOTH endpoints of one game project with the trace/capture switches
#  the evidence model needs, replays a session of MCP calls against them, and
#  then turns the traces into a ledger and a per-game report.
#
#    editor endpoint  : 9888   (-e --path <project>)
#    game   endpoint  : 9889   (--path <project>)
#    both             : --mcp-trace=<jsonl> --mcp-capture=every_call
#                       --mcp-capture-dir=<dir> --mcp-capture-viewport=2d
#
#  Iron rule 1: no shell redirection anywhere -- engine stdout/stderr are owned
#               by Start-Process -RedirectStandardOutput/-RedirectStandardError.
#  Iron rule 2: the only writes/deletes are inside <Root>\runs\<Game>\<RunTag>;
#               every destructive path is checked against that prefix first.
#  Iron rule 3: both engines are started through cmd.exe.
#
#  Session file format (JSON):
#    {
#      "import": true,
#      "calls": [
#        {"tag":"e01-tools-list","port":"editor","method":"tools/list"},
#        {"tag":"e02-ball","port":"editor","tool":"project_create_script",
#         "arguments":{"path":"res://src/Ball.cs","content_file":"payload/Ball.cs"}},
#        {"sleep_ms":2000,"port":"game","note":"let the ball travel"}
#      ]
#    }
#  `content_file` is resolved relative to the session file's directory.
# =============================================================================
$ErrorActionPreference = 'Stop'

if (-not $Session) { $Session = Join-Path $Root ("tools\sessions\{0}\session.json" -f $Game) }
if (-not $Engine)  { $Engine  = Join-Path $Root 'godot\bin\godot.windows.editor.x86_64.mono.console.exe' }
$Project = Join-Path $Root ("projects\{0}" -f $Game)
if (-not $RunTag) { $RunTag = (Get-Date -Format 'yyyyMMdd-HHmmss') }
$OutRoot = Join-Path $Root ("runs\{0}\{1}" -f $Game, $RunTag)
$SessionDir = Split-Path -Parent (Resolve-Path -LiteralPath $Session).Path
$LedgerTool = Join-Path $Root 'godot\modules\mcp_server\scripts\mcp_trace_ledger.py'
$ReportTool = Join-Path $Root 'tools\game_report.py'

foreach ($p in @($Session, $Engine, $LedgerTool)) {
  if (-not (Test-Path -LiteralPath $p)) { throw "missing: $p" }
}
if (-not (Test-Path -LiteralPath $Project)) { throw "missing project: $Project" }

New-Item -ItemType Directory -Force -Path $OutRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $OutRoot 'shots-editor') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $OutRoot 'shots-game') | Out-Null

$script:Handles = New-Object System.Collections.Generic.List[object]
$script:Lines = New-Object System.Collections.Generic.List[string]
$script:Index = New-Object System.Collections.Generic.List[string]
$script:NextId = 100

function Note([string]$text) {
  Write-Host $text
  $script:Lines.Add($text)
}

# --- iron rule 2: every destructive path goes through this --------------------
function Assert-InOutRoot([string]$path) {
  $full = [System.IO.Path]::GetFullPath($path)
  $prefix = [System.IO.Path]::GetFullPath($OutRoot).TrimEnd('\') + '\'
  if (-not $full.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "REFUSED: '$full' is not inside '$OutRoot'"
  }
  return $full
}

function Remove-InOutRoot([string]$path) {
  $full = Assert-InOutRoot $path
  if (Test-Path -LiteralPath $full) { Remove-Item -LiteralPath $full -Force }
}

# --- engines ------------------------------------------------------------------
function Start-Engine([string[]]$Extra, [string]$LogName) {
  $out = Join-Path $OutRoot ("engine-$LogName.stdout.txt")
  $err = Join-Path $OutRoot ("engine-$LogName.stderr.txt")
  Remove-InOutRoot $out
  Remove-InOutRoot $err
  $cmdline = '"' + $Engine + '" ' + ($Extra -join ' ')
  $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $cmdline -WorkingDirectory (Join-Path $Root 'godot') `
        -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -PassThru
  $script:Handles.Add($p)
  return [pscustomobject]@{ Process = $p; Out = $out; Err = $err; Cmdline = $cmdline }
}

function Stop-Engine($handle) {
  if ($null -eq $handle) { return }
  try { if ($handle.Process.HasExited) { return } } catch { }
  # `taskkill /T` kills the WHOLE tree: cmd -> the .console.exe launcher -> the real
  # engine. Killing only the direct child leaves the engine alive and holding the
  # project directory (run-1 defect P-4: reset_game.ps1 then could not remove it).
  try {
    $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', ('taskkill /PID ' + $handle.Process.Id + ' /T /F') `
          -RedirectStandardOutput (Join-Path $OutRoot 'taskkill.stdout.txt') `
          -RedirectStandardError (Join-Path $OutRoot 'taskkill.stderr.txt') -NoNewWindow -Wait -PassThru
    if ($p.ExitCode -ne 0) { Write-Host ("  taskkill exit {0} (the tree may already be gone)" -f $p.ExitCode) }
  } catch {
    try { if (-not $handle.Process.HasExited) { Stop-Process -Id $handle.Process.Id -Force -ErrorAction SilentlyContinue } } catch { }
  }
}

function Wait-Port([int]$Port, [int]$TimeoutMs) {
  $deadline = (Get-Date).AddMilliseconds($TimeoutMs)
  while ((Get-Date) -lt $deadline) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
      $task = $client.ConnectAsync('127.0.0.1', $Port)
      if ($task.Wait(700) -and $client.Connected) { $client.Close(); return $true }
    } catch { } finally { try { $client.Close() } catch { } }
    Start-Sleep -Milliseconds 500
  }
  return $false
}

function Import-Project {
  # A generated .cmd rather than a quoted Start-Process argument: PowerShell
  # escapes inner quotes as \" for a native command line and cmd.exe reads it
  # differently, which is what made `--import` fail with "The filename,
  # directory name, or volume label syntax is incorrect" (run-3 defect P-6).
  $out = Join-Path $OutRoot 'import.stdout.txt'
  $err = Join-Path $OutRoot 'import.stderr.txt'
  Remove-InOutRoot $out
  Remove-InOutRoot $err
  $b = Join-Path $OutRoot 'import.cmd'
  $batch = @(
    '@echo off',
    ('cd /d "{0}"' -f (Join-Path $Root 'godot')),
    ('"{0}" --headless --path "{1}" --import' -f $Engine, $Project),
    'echo IMPORT_EXIT=%ERRORLEVEL%'
  )
  Set-Content -LiteralPath $b -Value $batch -Encoding ASCII
  $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $b -WorkingDirectory (Join-Path $Root 'godot') `
        -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -Wait -PassThru
  $code = ''
  if (Test-Path -LiteralPath $out) {
    $m = Select-String -LiteralPath $out -Pattern 'IMPORT_EXIT=(-?\d+)' | Select-Object -Last 1
    if ($m) { $code = $m.Matches[0].Groups[1].Value }
  }
  Note ("import   : exit {0} (echoed) / {1} (process)  ({2})" -f $code, $p.ExitCode, $out)
}

# --- the MCP transport --------------------------------------------------------
function Invoke-Mcp([int]$Port, [string]$Body, [string]$Tag, [string]$NoteText) {
  $bodyFile = Join-Path $OutRoot ($Tag + '.request.json')
  Set-Content -LiteralPath $bodyFile -Value $Body -Encoding UTF8 -NoNewline
  $curlArgs = @('-s', '-X', 'POST', '-H', 'Content-Type: application/json',
                '--data-binary', ('@' + $bodyFile), ("http://127.0.0.1:{0}/mcp" -f $Port))
  $result = & curl.exe @curlArgs
  $text = ($result -join '')
  Set-Content -LiteralPath (Join-Path $OutRoot ($Tag + '.json')) -Value $text -Encoding UTF8
  $short = $text
  if ($short.Length -gt 160) { $short = $short.Substring(0, 160) + '...' }
  Note ("  [{0}] port={1} bytes={2} :: {3}" -f $Tag, $Port, $text.Length, $short)
  $script:Index.Add(('{0}|{1}|{2}|{3}|{4}' -f $Tag, $Port, $Body.Length, $text.Length, $NoteText))
}

function Resolve-Arguments($arguments, [string]$dir) {
  if ($null -eq $arguments) { return $null }
  if ($arguments.PSObject.Properties.Name -contains 'content_file') {
    $rel = $arguments.content_file
    $full = Join-Path $dir $rel
    if (-not (Test-Path -LiteralPath $full)) { throw "content_file not found: $full" }
    $arguments.PSObject.Properties.Remove('content_file')
    $arguments | Add-Member -NotePropertyName content -NotePropertyValue ([System.IO.File]::ReadAllText($full))
  }
  return $arguments
}

# =============================================================================
Note '=== godot-mcp game session ==='
Note ("game     : {0}" -f $Game)
Note ("project  : {0}" -f $Project)
Note ("session  : {0}" -f $Session)
Note ("run      : {0}" -f $OutRoot)
Note ("engine   : {0}" -f $Engine)

$doc = Get-Content -LiteralPath $Session -Raw -Encoding UTF8 | ConvertFrom-Json
$calls = @($doc.calls)

if ($doc.import -ne $false) { Import-Project }

$editorTrace = Join-Path $OutRoot 'trace-editor.jsonl'
$gameTrace = Join-Path $OutRoot 'trace-game.jsonl'
foreach ($t in @($editorTrace, $gameTrace)) { Remove-InOutRoot $t }

# NOTE (run-3 defect P-5): do NOT declare `$game` / `$editor` here either --
# PowerShell variable names are case-insensitive, so `$game = $null` silently
# blanks the `-Game` parameter, and the per-game report then runs with
# `--game=` (empty) and cannot find the game's user:// directory.
$phase = $null

function Enter-Phase([string]$name) {
  if ($name -eq 'editor') {
    $args = @('-e', '--path', $Project,
              ('--mcp-port=' + $EditorPort),
              ('--mcp-trace=' + $editorTrace),
              '--mcp-capture=every_call',
              ('--mcp-capture-dir=' + (Join-Path $OutRoot 'shots-editor')),
              '--mcp-capture-viewport=2d')
    # NOTE: the handle must NOT be called `$game` / `$editor` -- PowerShell variable
    # names are case-insensitive, so `$script:game` would silently overwrite the
    # `-Game` parameter (run-1 defect P-3).
    $script:EditorProc = Start-Engine -Extra $args -LogName 'editor'
    Note ('editor   : ' + $script:EditorProc.Cmdline)
    if (-not (Wait-Port -Port $EditorPort -TimeoutMs 300000)) { Note 'FATAL: the editor endpoint never came up' }
    else { Start-Sleep -Seconds 6; Note '--- editor side (9888) ---' }
  } else {
    $args = @('--path', $Project,
              ('--mcp-port=' + $GamePort),
              ('--mcp-trace=' + $gameTrace),
              '--mcp-capture=every_call',
              ('--mcp-capture-dir=' + (Join-Path $OutRoot 'shots-game')),
              '--mcp-capture-viewport=2d')
    $script:GameProc = Start-Engine -Extra $args -LogName 'game'
    Note ('game     : ' + $script:GameProc.Cmdline)
    if (-not (Wait-Port -Port $GamePort -TimeoutMs 300000)) { Note 'FATAL: the game endpoint never came up' }
    else { Start-Sleep -Seconds 6; Note '--- game side (9889) ---' }
  }
}

function Leave-Phase([string]$name) {
  if ($name -eq 'editor') { Stop-Engine -Handle $script:EditorProc; Start-Sleep -Seconds 3 }
  else { Stop-Engine -Handle $script:GameProc; Start-Sleep -Seconds 1 }
}

$order = @()
foreach ($c in $calls) { $p = "$($c.port)"; if ($order -notcontains $p) { $order += $p } }

foreach ($p in $order) {
  if ($p -notin @('editor', 'game')) { throw "unknown port '$p' in the session file" }
  Enter-Phase $p
  $port = if ($p -eq 'editor') { $EditorPort } else { $GamePort }
  foreach ($c in ($calls | Where-Object { "$($_.port)" -eq $p })) {
    if ($c.sleep_ms) {
      $secs = [double]$c.sleep_ms / 1000.0
      Note ("  [sleep {0}s] {1}" -f $secs, $c.note)
      Start-Sleep -Milliseconds ([int]$c.sleep_ms)
      continue
    }
    if ($c.method -eq 'tools/list' -or (-not $c.tool -and $c.method)) {
      $body = (@{ jsonrpc = '2.0'; id = $script:NextId; method = $c.method; params = @{} } | ConvertTo-Json -Compress -Depth 8)
    } else {
      $arguments = Resolve-Arguments $c.arguments $SessionDir
      $body = (@{ jsonrpc = '2.0'; id = $script:NextId; method = 'tools/call';
                  params = @{ name = $c.tool; arguments = $arguments } } | ConvertTo-Json -Compress -Depth 24)
    }
    $script:NextId++
    Invoke-Mcp $port $body $c.tag $c.note
  }
  Leave-Phase $p
}

foreach ($h in $script:Handles) { Stop-Engine -Handle $h }

# --- ledgers ------------------------------------------------------------------
# The python invocations go through a generated .cmd file rather than through
# Start-Process' argument quoting: PowerShell escapes inner double quotes as \"
# for a native command line, and cmd.exe does not read \" the way PowerShell
# means it (run-1 defect P-3's sibling). A .cmd file has no quoting games at all.
Note '--- ledger ---'
foreach ($pair in @(@('editor', $editorTrace, $EditorPort), @('game', $gameTrace, $GamePort))) {
  $name = $pair[0]; $trace = $pair[1]
  if (-not (Test-Path -LiteralPath $trace)) { Note ("{0}: trace ABSENT" -f $name); continue }
  $txt = Join-Path $OutRoot ("ledger-{0}.txt" -f $name)
  $jsn = Join-Path $OutRoot ("ledger-{0}.json" -f $name)
  $b = Join-Path $OutRoot ("ledger-{0}.cmd" -f $name)
  $batch = @(
    '@echo off',
    ('python "{0}" "{1}" --text "{2}" --json "{3}"' -f $LedgerTool, $trace, $txt, $jsn),
    'echo LEDGER_EXIT=%ERRORLEVEL%'
  )
  Set-Content -LiteralPath $b -Value $batch -Encoding ASCII
  $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $b `
        -WorkingDirectory (Join-Path $Root 'godot') -RedirectStandardOutput (Join-Path $OutRoot ("ledger-{0}.stdout.txt" -f $name)) `
        -RedirectStandardError (Join-Path $OutRoot ("ledger-{0}.stderr.txt" -f $name)) -NoNewWindow -Wait -PassThru
  Note ("{0}: ledger exit {1} -> {2}" -f $name, $p.ExitCode, $txt)
  if (Test-Path -LiteralPath $txt) { Get-Content -LiteralPath $txt -TotalCount 6 | ForEach-Object { Note ('    | ' + $_) } }
}

Set-Content -LiteralPath (Join-Path $OutRoot 'session-log.txt') -Value $script:Lines -Encoding UTF8
Set-Content -LiteralPath (Join-Path $OutRoot 'call-index.txt') -Value $script:Index -Encoding UTF8

# --- the per-game report ------------------------------------------------------
if (-not $SkipReport -and (Test-Path -LiteralPath $ReportTool)) {
  Note '--- per-game report ---'
  $b = Join-Path $OutRoot 'report.cmd'
  $batch = @(
    '@echo off',
    ('python "{0}" "{1}" --game={2} --run-tag={3}' -f $ReportTool, $OutRoot, $Game, $RunTag),
    'echo REPORT_EXIT=%ERRORLEVEL%'
  )
  Set-Content -LiteralPath $b -Value $batch -Encoding ASCII
  $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $b `
        -WorkingDirectory (Join-Path $Root 'godot') -RedirectStandardOutput (Join-Path $OutRoot 'report.stdout.txt') `
        -RedirectStandardError (Join-Path $OutRoot 'report.stderr.txt') -NoNewWindow -Wait -PassThru
  Note ("report: exit {0}" -f $p.ExitCode)
  $rep = Join-Path $OutRoot 'report.md'
  if (Test-Path -LiteralPath $rep) {
    Get-Content -LiteralPath $rep | ForEach-Object { Note ('    | ' + $_) }
  }
}

Note ("run root : {0}" -f $OutRoot)
