# TASK-082 item 2: guarded removal of b2*.tmp.* residue in the rebuild work tree.
# Pure ASCII. Absolute paths. Prints the delete list before doing anything.
$ErrorActionPreference = 'Stop'

$root   = 'H:\rebuild\godot'
$prefix = 'H:\rebuild\godot\'
$allowedCPrefix = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\'

# Literal, explicit target list (no wildcards used for the delete itself).
$targets = @(
  'H:\rebuild\godot\modules\mcp_server\b2contract.tmp.json',
  'H:\rebuild\godot\modules\mcp_server\b2map.tmp.json',
  'H:\rebuild\godot\modules\mcp_server\b2reasons.tmp.txt'
)

Write-Output '=== GUARD CHECK ==='
foreach ($t in $targets) {
  if ([string]::IsNullOrWhiteSpace($t)) { throw 'empty target' }
  if (-not [IO.Path]::IsPathRooted($t)) { throw "not absolute: $t" }
  if ($t.Contains('*') -or $t.Contains('?') -or $t.Contains('..')) { throw "wildcard or dotdot in target: $t" }
  if (-not ($t.StartsWith($prefix) -or $t.StartsWith($allowedCPrefix))) { throw "target outside allowed prefixes: $t" }
  if (-not (Test-Path -LiteralPath $t)) { throw "target does not exist: $t" }
  if ((Get-Item -LiteralPath $t).PSIsContainer) { throw "target is a directory: $t" }
}
Write-Output 'guard: PASS (non-empty, absolute, no wildcard/dotdot, inside H:\rebuild\godot\)'
Write-Output ''
Write-Output '=== WILL DELETE ==='
foreach ($t in $targets) {
  $i = Get-Item -LiteralPath $t
  Write-Output ('{0}  bytes={1}' -f $t, $i.Length)
}

# Cross-check the glob the task named, so the literal list is provably complete.
$glob = Get-ChildItem -Path $root -Recurse -File -Filter 'b2*.tmp.*'
$globPaths = @($glob | ForEach-Object { $_.FullName } | Sort-Object)
$litPaths  = @($targets | Sort-Object)
Write-Output ''
Write-Output ('glob b2*.tmp.* matched: {0}' -f $globPaths.Count)
foreach ($g in $globPaths) { Write-Output ('  glob -> ' + $g) }
$diff = Compare-Object $globPaths $litPaths
if ($diff) { throw 'literal list does not equal glob match set; refusing to delete' }
Write-Output 'literal list == glob match set: OK'

foreach ($t in $targets) { Remove-Item -LiteralPath $t -Force }
Write-Output ''
foreach ($t in $targets) { Write-Output ('deleted={0} exists_now={1}' -f $t, (Test-Path -LiteralPath $t)) }
