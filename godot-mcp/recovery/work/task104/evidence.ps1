param(
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp'
)
# TASK-104: produce every per-game evidence log through the same helper that owns
# its stdout/stderr with Start-Process (iron rule 1: no shell redirection anywhere).
$ErrorActionPreference = 'Stop'
$work = Join-Path $Root 'recovery\work\task104'
$logs = Join-Path $work 'logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$capture = Join-Path $work 'capture.ps1'

$games = @(
  @{ name = 'rtype'; tag = 'rt-task104-r2'; prefix = 'rt' },
  @{ name = 'puzzlebobble'; tag = 'pb-task104-r1'; prefix = 'pb' },
  @{ name = 'lunarlander'; tag = 'll-task104-r1'; prefix = 'll' }
)

foreach ($g in $games) {
  $run = Join-Path $Root ("runs\{0}\{1}" -f $g.name, $g.tag)
  $expect = Join-Path $work ("expectations-{0}.json" -f $g.name)
  & powershell -NoProfile -ExecutionPolicy Bypass -File $capture `
      -Script 'recovery\work\task104\assert_summary.py' -Args ('"' + $run + '"') `
      -Out (Join-Path $logs ("assert-{0}.txt" -f $g.name))
  & powershell -NoProfile -ExecutionPolicy Bypass -File $capture `
      -Script 'recovery\work\task104\recompute_readbacks.py' `
      -Args ('"' + $run + '" "' + $expect + '" ' + $g.name) `
      -Out (Join-Path $logs ("recompute-{0}.txt" -f $g.name))
  & powershell -NoProfile -ExecutionPolicy Bypass -File $capture `
      -Script 'recovery\work\task104\pixel_recompute.py' -Args ('"' + $run + '"') `
      -Out (Join-Path $logs ("pixel-{0}.txt" -f $g.name))
  & powershell -NoProfile -ExecutionPolicy Bypass -File $capture `
      -Script 'recovery\work\task104\game_facts.py' -Args ('"' + $run + '"') `
      -Out (Join-Path $logs ("facts-{0}.txt" -f $g.name))
  & powershell -NoProfile -ExecutionPolicy Bypass -File $capture `
      -Script 'recovery\work\task104\frames_recompute.py' -Args ($g.name + ' ' + $g.prefix + '-t "' + $run + '"') `
      -Out (Join-Path $logs ("frames-{0}.txt" -f $g.name))
  & powershell -NoProfile -ExecutionPolicy Bypass -File $capture `
      -Script 'recovery\work\task104\check_session.py' -Args ('"' + (Join-Path $Root ("tools\sessions\{0}\session.json" -f $g.name)) + '"') `
      -Out (Join-Path $logs ("checksession-py-{0}.txt" -f $g.name))
  & powershell -NoProfile -ExecutionPolicy Bypass -File $capture `
      -Script 'recovery\work\task104\analyze_pixels.py' -Args ('"' + $run + '"') `
      -Out (Join-Path $logs ("pixelpairs-{0}.txt" -f $g.name))
}
Get-ChildItem -LiteralPath $logs -File | Where-Object { $_.Name -match '^(assert|recompute|pixel|facts|frames|checksession|pixelpairs)-' } |
  Sort-Object Name | ForEach-Object { Write-Output ("{0,-34} {1,8} bytes" -f $_.Name, $_.Length) }
