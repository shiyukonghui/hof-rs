param(
  [int]$Iterations = 6,
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp',
  [string]$Engine = '',
  [int]$FirstPort = 9950,
  [switch]$OmitMcpPort,
  [string]$Cases = 'csharp,gdscript',
  [string]$TagSuffix = ''
)
# TASK-098 item C: try to reproduce the `--import` access violation on purpose.
#
# Observed twice so far, both times with the same shape:
#     IMPORT_EXIT=-1073741819   (0xC0000005)
#     stderr: ERROR: Parameter "singleton" is null.
#             at: EditorNode::is_cmdline_mode (editor\editor_node.cpp:6750)
# and both times AFTER the import had already finished (the log reaches
# `[ DONE ] loading_editor_layout` before the exit code is echoed), i.e. it is a
# SHUTDOWN crash, not an import failure.
#
# The one static fact that narrows it: `EditorNode::is_cmdline_mode()` has exactly one
# caller in the engine, `EditorFileSystem::_process_update_pending()`, which runs from a
# `call_deferred` queued when a script's class info changes. That points at
# "a deferred script-class update fires while the editor is being torn down".
#
# So the probe varies the two things that hypothesis predicts should matter:
#   * the project language   -- C# (asteroids, whose classes come from the .NET build)
#                              vs GDScript (mcpplay, which has no C# assembly at all);
#   * whether the import actually had work to do -- the first import of a copy with no
#     `.godot/` directory scans and queues script-class updates; the second, warm import
#     of the same directory should not.
#
# It never deletes anything: each iteration gets its own fresh copy. Iron rule 1:
# stdout/stderr belong to Start-Process. Iron rule 3: the child is cmd.exe. Iron rule 4:
# every import gets its own port, and the port is checked free first.
$ErrorActionPreference = 'Stop'
if (-not $Engine) { $Engine = Join-Path $Root 'godot\bin\godot.windows.editor.x86_64.mono.console.exe' }
$ProbeRoot = Join-Path $Root 'recovery\work\task098\importprobe'
$LogRoot = Join-Path $Root 'recovery\work\task098\logs\importprobe'
$GodotDir = Join-Path $Root 'godot'
New-Item -ItemType Directory -Force -Path $ProbeRoot, $LogRoot | Out-Null

function Assert-FreePort([int]$port) {
  $holders = netstat -ano | Select-String -Pattern (":{0}\s" -f $port)
  if ($holders) { throw "REFUSED: port $port is already in use: $holders" }
}

function Copy-Fresh([string]$source, [string]$dest) {
  if (Test-Path -LiteralPath $dest) { throw "REFUSED: '$dest' already exists" }
  New-Item -ItemType Directory -Force -Path $dest | Out-Null
  $skip = '\\(\.godot|bin|obj|\.mono)$'
  foreach ($item in (Get-ChildItem -LiteralPath $source -Force)) {
    if ($item.PSIsContainer -and $item.Name -match '^(\.godot|bin|obj|\.mono)$') { continue }
    Copy-Item -LiteralPath $item.FullName -Destination $dest -Recurse -Force
  }
  return $dest
}

$results = @()
$caseList = @()
foreach ($name in ($Cases -split ',')) {
  switch ($name.Trim()) {
    'csharp'   { $caseList += ,@('csharp', 'projects\asteroids') }
    'gdscript' { $caseList += ,@('gdscript', 'projects\mcpplay') }
    default    { throw "REFUSED: unknown case '$name'" }
  }
}
foreach ($case in $caseList) {
  $lang = $case[0]
  $source = Join-Path $Root $case[1]
  for ($i = 1; $i -le $Iterations; $i++) {
    $tag = "{0}{1}-{2:d2}" -f $lang, $TagSuffix, $i
    $dir = Join-Path $ProbeRoot $tag
    Copy-Fresh $source $dir | Out-Null
    foreach ($round in @('fresh', 'warm')) {
      $portArg = ''
      if ($OmitMcpPort) {
        # exactly what tools\run_game_session.ps1 does: the module's own default port
        Assert-FreePort 9877
      } else {
        $portArg = '--mcp-port={0}' -f $FirstPort
        Assert-FreePort $FirstPort
        $FirstPort++
      }
      $out = Join-Path $LogRoot ("{0}-{1}.stdout.txt" -f $tag, $round)
      $err = Join-Path $LogRoot ("{0}-{1}.stderr.txt" -f $tag, $round)
      $bat = Join-Path $LogRoot ("{0}-{1}.cmd" -f $tag, $round)
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
      if (Test-Path -LiteralPath $err) {
        $errText = ((Get-Content -LiteralPath $err) -join ' / ').Trim()
      }
      $done = $false
      if (Test-Path -LiteralPath $out) {
        $done = [bool](Select-String -LiteralPath $out -Pattern '\[ DONE \]' -Quiet)
      }
      $verdict = if ($code -eq '0') { 'OK' } else { 'CRASH' }
      $portLabel = '9877(default)'
      if (-not $OmitMcpPort) { $portLabel = $portArg }
      $results += [pscustomobject]@{
        tag = $tag; round = $round; port = $portLabel; exit = $code; verdict = $verdict
        engine = $Engine; omit_mcp_port = [bool]$OmitMcpPort
        ms = $elapsed; reached_done = $done; stderr = $errText
      }
      Write-Output ("{0,-16} {1,-6} port={2,-14} exit={3,-12} {4,-6} {5,6} ms  done={6}  {7}" -f `
        $tag, $round, $portLabel, $code, $verdict, `
        $elapsed, $done, $errText)
    }
  }
}

$crashes = @($results | Where-Object { $_.verdict -eq 'CRASH' })
Write-Output ''
Write-Output ("=== {0} import(s): {1} OK, {2} CRASH ===" -f $results.Count, ($results.Count - $crashes.Count), $crashes.Count)
foreach ($g in ($results | Group-Object { $_.tag -replace '-\d+$', '' })) {
  $c = @($g.Group | Where-Object { $_.verdict -eq 'CRASH' }).Count
  Write-Output ("   {0,-10} {1}/{2} crashed" -f $g.Name, $c, $g.Count)
}
foreach ($g in ($results | Group-Object round)) {
  $c = @($g.Group | Where-Object { $_.verdict -eq 'CRASH' }).Count
  Write-Output ("   {0,-10} {1}/{2} crashed" -f $g.Name, $c, $g.Count)
}

$json = Join-Path $LogRoot ('probe-results{0}.json' -f $TagSuffix)
[System.IO.File]::WriteAllText($json, ($results | ConvertTo-Json -Depth 4),
                              (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("results: {0}" -f $json)
