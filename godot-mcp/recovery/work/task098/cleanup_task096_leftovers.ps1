param(
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp',
  [switch]$Execute
)
# TASK-098 item B1: resolve the 136 untracked leftovers of TASK-096.
#
# The classification is not invented here -- TASK-096-REPORT.md section D4 already
# decided it ("reporttest-pong 的其余部分 ... 与 tmp_*.tscn ... 不入库"). This script
# makes that decision enforceable and executes the one destructive part of it.
#
# Iron rule 2 (destructive commands are refused by default). The deletion below:
#   * names every target as an absolute path (no wildcards, no `..`);
#   * refuses anything outside the one whitelisted prefix;
#   * refuses any file that is not zero bytes (the four slips are empty by construction);
#   * prints the full manifest before it deletes anything;
#   * refuses to run at all in -WhatIf mode, which is the default.
$ErrorActionPreference = 'Stop'

$Whitelist = [System.IO.Path]::GetFullPath((Join-Path $Root 'recovery\work\task096')).TrimEnd('\') + '\'
$Targets = @(
  (Join-Path $Root 'recovery\work\task096\tmp_pong_df02ccb.tscn'),
  (Join-Path $Root 'recovery\work\task096\tmp_pong_97167e4.tscn'),
  (Join-Path $Root 'recovery\work\task096\tmp_breakout_97167e4.tscn'),
  (Join-Path $Root 'recovery\work\task096\tmp_snake_97167e4.tscn')
)

Write-Output '=== MANIFEST: files this script would delete ==='
$full = @()
foreach ($t in $Targets) {
  if ([string]::IsNullOrWhiteSpace($t)) { throw 'REFUSED: empty path' }
  if ($t -match '[\*\?]' -or $t -match '\.\.') { throw "REFUSED: wildcard or .. in '$t'" }
  $f = [System.IO.Path]::GetFullPath($t)
  if (-not $f.StartsWith($Whitelist, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "REFUSED: '$f' is not under '$Whitelist'"
  }
  if (-not (Test-Path -LiteralPath $f)) { Write-Output ("  ABSENT  {0}" -f $f); continue }
  $len = (Get-Item -LiteralPath $f).Length
  if ($len -ne 0) { throw "REFUSED: '$f' is $len bytes, not one of the empty redirect slips" }
  Write-Output ("  DELETE  {0}  ({1} bytes)" -f $f, $len)
  $full += $f
}
Write-Output ("=== plan: {0} file(s), all 0 bytes, all under the TASK-096 whitelist ===" -f $full.Count)

if (-not $Execute) {
  Write-Output 'DRY RUN (pass -Execute to delete). Nothing was deleted.'
  return
}
foreach ($f in $full) {
  Remove-Item -LiteralPath $f -Force
  Write-Output ("  deleted {0}" -f $f)
}
Write-Output ("done: deleted {0} file(s)" -f $full.Count)
