# TASK-082 item 1: promote the 13 low-confidence module sources.
# Pure ASCII. Absolute paths only. Uses Copy-Item (no shell redirection).
$ErrorActionPreference = 'Stop'

$lc  = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\rebuild\_low-confidence\modules\mcp_server'
$dst = 'H:\rebuild\godot\modules\mcp_server'
$out = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\promoted-lowconf.txt'

# relpath | confidence-cov% | tailPresent | failedEdits  (from REBUILD-2A-MANIFEST.md 4 table)
$rows = @(
  @('mcp_capture.h',                        '8.8',   'no',          '1'),
  @('tools\editor_animation_tree_write.cpp','13.7',  'no',          '4'),
  @('tools\editor_control_layout_write.cpp','34.2', 'no',          '1'),
  @('tools\editor_node_read.cpp',           '64.1',  'yes',         '14'),
  @('tools\editor_playback.cpp',            '100.0', 'no',          '20'),
  @('tools\editor_read_scene_inspector.cpp','55.1', 'no',          '7'),
  @('tools\editor_write_scene_editor.cpp',  '61.1',  'yes',         '32'),
  @('tools\project_read_analysis.cpp',      '46.5',  'no',          '1'),
  @('tools\project_write_resource_scene.cpp','62.2','yes',         '26'),
  @('tools\running_game_assertion.cpp',     '40.7',  'no',          '2'),
  @('tools\running_game_node_write.cpp',    '91.6',  'yes',         '12'),
  @('tools\running_game_observation.cpp',   '52.4',  'no',          '1'),
  @('tools\tool_helpers.cpp',               '49.1',  'no',          '3')
)

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('# TASK-082 item 1 - promoted low-confidence module sources')
$lines.Add('# date: ' + (Get-Date -Format o))
$lines.Add('# columns: relpath | source(abs) | bytes | sha256 | confidence(read-cov%) | tail | failed_edits | dest_bytes | sha_match | suspicious')
$lines.Add('')

$n = 0
foreach ($r in $rows) {
  $rel = $r[0]
  $src = Join-Path $lc $rel
  $tgt = Join-Path $dst $rel
  if (-not (Test-Path $src)) { throw "source missing: $src" }
  if (-not ($tgt.StartsWith('H:\rebuild\godot\modules\mcp_server\'))) { throw "dest outside allowed prefix: $tgt" }
  $tgtDir = Split-Path $tgt -Parent
  if (-not (Test-Path $tgtDir)) { [void](New-Item -ItemType Directory -Path $tgtDir -Force) }

  $srcHash = (Get-FileHash $src -Algorithm SHA256).Hash
  $srcLen  = (Get-Item $src).Length
  Copy-Item -LiteralPath $src -Destination $tgt -Force
  $dstHash = (Get-FileHash $tgt -Algorithm SHA256).Hash
  $dstLen  = (Get-Item $tgt).Length

  # suspicious-feature scan on the promoted bytes
  $t = [IO.File]::ReadAllText($tgt)
  $ob = ([regex]::Matches($t, '\{')).Count
  $cb = ([regex]::Matches($t, '\}')).Count
  $sus = New-Object System.Collections.Generic.List[string]
  if ($ob -ne $cb) { $sus.Add(("brace_delta=" + ($ob - $cb))) }
  $tailTxt = $t.Substring([Math]::Max(0, $t.Length - 80)).Replace("`r", '').Replace("`n", ' / ')
  if ($tailTxt -notmatch 'namespace') { $sus.Add('tail_no_namespace_close') }
  if ($t -match '@@REGISTRATION_BLOCK@@') { $sus.Add('registration_placeholder_marker') }
  if ($t -match '(?m)^\s*// BEGIN generated\s*$[\s\S]{0,80}?// END generated') { $sus.Add('empty_generated_block?') }
  if ($t -match '<<<<<<<|>>>>>>>|=======') { $sus.Add('conflict_marker') }
  if ($t -notmatch 'Copyright') { $sus.Add('no_copyright_header') }
  $susTxt = ($sus -join ';')
  if ($susTxt -eq '') { $susTxt = '-' }

  $lines.Add(('{0}|{1}|{2}|{3}|{4}|{5}|{6}|{7}|{8}|{9}' -f $rel, $src, $srcLen, $srcHash, $r[1], $r[2], $r[3], $dstLen, ($srcHash -eq $dstHash), $susTxt))
  $lines.Add(('    tail: ' + $tailTxt))
  $n++
}

$lines.Add('')
$lines.Add('files_promoted=' + $n)
[IO.File]::WriteAllLines($out, $lines, (New-Object System.Text.UTF8Encoding($true)))
Write-Output ('promoted=' + $n + ' manifest=' + $out)
