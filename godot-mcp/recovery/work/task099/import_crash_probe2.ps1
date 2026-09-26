param(
  [int]$Iterations = 8,
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp',
  [string]$Engine = '',
  [string]$Source = 'projects\frogger',
  [string]$Tag = 'frogger',
  [int]$FirstPort = 9970,
  [switch]$OmitMcpPort,
  [int]$Load = 0,
  [switch]$WarmOnly,
  [switch]$FreshOnly
)
# TASK-099 item C: the `--import` access violation happened AGAIN, live, on the
# very first import of the brand-new `projects\frogger` project:
#
#     import   : exit -1073741819 (echoed)
#     stderr: ERROR: Parameter "singleton" is null.
#             at: EditorNode::is_cmdline_mode (editor\editor_node.cpp:6750)
#
# exactly after `[ DONE ] loading_editor_layout` -- i.e. the shutdown crash the
# ledger describes (third live occurrence, first one of TASK-099).
#
# The ledger's own rule is "no speculative engine edits": what a claim needs is a
# recipe, so this probe tries to turn the live hit into a reproducible one. It
# varies only things the observed hit could plausibly depend on, and it never
# deletes anything:
#
#   * `fresh` vs `warm` -- a copy with no `.godot/`, `bin/` or `obj/` (the first
#     import of a never-imported C# project, which is what the live hit was) against
#     the second import of exactly that directory;
#   * the port         -- the real driver passes NO `--mcp-port`, so the module's
#     default 9877 is what the live hit used (`-OmitMcpPort`); a unique port is the
#     control;
#   * `-Load N`        -- N CPU burners, to widen every shutdown race window.
#
# Iron rule 1: stdout/stderr belong to Start-Process, never to a shell redirect.
# Iron rule 3: every child is cmd.exe. Iron rule 4: every import gets its own
# checked-free port when a port is passed at all.
$ErrorActionPreference = 'Stop'
if (-not $Engine) { $Engine = Join-Path $Root 'godot\bin\godot.windows.editor.x86_64.mono.console.exe' }
$ProbeRoot = Join-Path $Root 'recovery\work\task099\importprobe'
$LogRoot = Join-Path $Root 'recovery\work\task099\logs\importprobe'
$GodotDir = Join-Path $Root 'godot'
$SrcFull = Join-Path $Root $Source
if (-not (Test-Path -LiteralPath $SrcFull)) { throw "REFUSED: source project not found: $SrcFull" }
New-Item -ItemType Directory -Force -Path $ProbeRoot, $LogRoot | Out-Null

function Assert-FreePort([int]$port) {
  $holders = netstat -ano | Select-String -Pattern (":{0}\s" -f $port)
  if ($holders) { throw "REFUSED: port $port is already in use: $holders" }
}

function Copy-Fresh([string]$source, [string]$dest) {
  if (Test-Path -LiteralPath $dest) { throw "REFUSED: '$dest' already exists" }
  New-Item -ItemType Directory -Force -Path $dest | Out-Null
  foreach ($item in (Get-ChildItem -LiteralPath $source -Force)) {
    if ($item.PSIsContainer -and $item.Name -match '^(\.godot|bin|obj|\.mono)$') { continue }
    Copy-Item -LiteralPath $item.FullName -Destination $dest -Recurse -Force
  }
  return $dest
}

$burners = @()
if ($Load -gt 0) {
  for ($b = 0; $b -lt $Load; $b++) {
    $burners += Start-Process -FilePath 'cmd.exe' `
      -ArgumentList '/c', 'for /l %i in (1,0,2) do @set /a x=%i*%i>nul' `
      -RedirectStandardOutput (Join-Path $LogRoot ("burner-{0}.stdout.txt" -f $b)) `
      -RedirectStandardError (Join-Path $LogRoot ("burner-{0}.stderr.txt" -f $b)) -NoNewWindow -PassThru
  }
  Write-Output ("load: {0} burner(s) started" -f $burners.Count)
}

$results = @()
try {
  for ($i = 1; $i -le $Iterations; $i++) {
    $caseTag = "{0}-{1:d2}" -f $Tag, $i
    $dir = Join-Path $ProbeRoot $caseTag
    Copy-Fresh $SrcFull $dir | Out-Null
    $rounds = @('fresh', 'warm')
    if ($WarmOnly) { $rounds = @('warm') }
    if ($FreshOnly) { $rounds = @('fresh') }
    foreach ($round in $rounds) {
      if ($round -eq 'warm') {
        # `warm` means "import this very directory a second time", so the first
        # import has to happen even when only the warm round is reported.
        $preOut = Join-Path $LogRoot ("{0}-pre.stdout.txt" -f $caseTag)
        $preErr = Join-Path $LogRoot ("{0}-pre.stderr.txt" -f $caseTag)
        $preBat = Join-Path $LogRoot ("{0}-pre.cmd" -f $caseTag)
        $prePort = if ($OmitMcpPort) { '' } else { '--mcp-port={0}' -f $FirstPort }
        if (-not $OmitMcpPort) { Assert-FreePort $FirstPort; $FirstPort++ } else { Assert-FreePort 9877 }
        $preBatch = @('@echo off', ('cd /d "{0}"' -f $GodotDir),
                      ('"{0}" --headless --path "{1}" {2} --import' -f $Engine, $dir, $prePort),
                      'echo IMPORT_EXIT=%ERRORLEVEL%')
        Set-Content -LiteralPath $preBat -Value $preBatch -Encoding ASCII
        Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $preBat -WorkingDirectory $GodotDir `
          -RedirectStandardOutput $preOut -RedirectStandardError $preErr -NoNewWindow -Wait -PassThru | Out-Null
      }
      $portArg = ''
      if ($OmitMcpPort) {
        Assert-FreePort 9877
      } else {
        $portArg = '--mcp-port={0}' -f $FirstPort
        Assert-FreePort $FirstPort
        $FirstPort++
      }
      $out = Join-Path $LogRoot ("{0}-{1}.stdout.txt" -f $caseTag, $round)
      $err = Join-Path $LogRoot ("{0}-{1}.stderr.txt" -f $caseTag, $round)
      $bat = Join-Path $LogRoot ("{0}-{1}.cmd" -f $caseTag, $round)
      $batch = @(
        '@echo off',
        ('cd /d "{0}"' -f $GodotDir),
        ('"{0}" --headless --path "{1}" {2} --import' -f $Engine, $dir, $portArg),
        'echo IMPORT_EXIT=%ERRORLEVEL%'
      )
      Set-Content -LiteralPath $bat -Value $batch -Encoding ASCII
      $started = Get-Date
      $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $bat -WorkingDirectory $GodotDir `
            -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -Wait -PassThru
      $elapsed = [int]((Get-Date) - $started).TotalMilliseconds
      $code = '?'
      if (Test-Path -LiteralPath $out) {
        $m = Select-String -LiteralPath $out -Pattern 'IMPORT_EXIT=(-?\d+)' | Select-Object -Last 1
        if ($m) { $code = $m.Matches[0].Groups[1].Value }
      }
      $errText = ''
      if (Test-Path -LiteralPath $err) { $errText = ((Get-Content -LiteralPath $err) -join ' / ').Trim() }
      $done = $false
      $lastLog = ''
      if (Test-Path -LiteralPath $out) {
        $done = [bool](Select-String -LiteralPath $out -Pattern '\[ DONE \]' -Quiet)
        $lines = @(Get-Content -LiteralPath $out)
        if ($lines.Count -gt 0) { $lastLog = ($lines | Where-Object { $_ -match '\S' } | Select-Object -Last 2) -join ' || ' }
      }
      $verdict = if ($code -eq '0') { 'OK' } else { 'CRASH' }
      $portLabel = if ($OmitMcpPort) { '9877(default)' } else { $portArg }
      $results += [pscustomobject]@{
        tag = $caseTag; round = $round; port = $portLabel; exit = $code; verdict = $verdict
        load = $Load; ms = $elapsed; reached_done = $done; last_log = $lastLog; stderr = $errText
      }
      Write-Output ("{0,-14} {1,-6} port={2,-14} exit={3,-12} {4,-6} {5,6} ms done={6} {7}" -f `
        $caseTag, $round, $portLabel, $code, $verdict, $elapsed, $done, $errText)
    }
  }
} finally {
  foreach ($b in $burners) {
    try {
      Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', ('taskkill /PID ' + $b.Id + ' /T /F') `
        -RedirectStandardOutput (Join-Path $LogRoot 'burner-kill.txt') `
        -RedirectStandardError (Join-Path $LogRoot 'burner-kill.err.txt') -NoNewWindow -Wait | Out-Null
    } catch { }
  }
}

$crashes = @($results | Where-Object { $_.verdict -eq 'CRASH' })
Write-Output ''
Write-Output ("=== {0} import(s): {1} OK, {2} CRASH ===" -f $results.Count, ($results.Count - $crashes.Count), $crashes.Count)
foreach ($g in ($results | Group-Object round)) {
  $c = @($g.Group | Where-Object { $_.verdict -eq 'CRASH' }).Count
  Write-Output ("   round {0,-6} {1}/{2} crashed" -f $g.Name, $c, $g.Count)
}
foreach ($g in ($results | Group-Object port)) {
  $c = @($g.Group | Where-Object { $_.verdict -eq 'CRASH' }).Count
  Write-Output ("   port  {0,-14} {1}/{2} crashed" -f $g.Name, $c, $g.Count)
}
$json = Join-Path $LogRoot ('probe2-{0}-load{1}.json' -f $Tag, $Load)
[System.IO.File]::WriteAllText($json, ($results | ConvertTo-Json -Depth 4), (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("results: {0}" -f $json)
