# reset_staging.ps1 - TASK-078 guarded reset of the staging output tree.
# SAFETY (TASK-078 section 0.3): target must be non-empty, absolute, start with the
# allowed C: prefix, contain no wildcard and no '..'; the full delete list is printed
# BEFORE any removal; anything unexpected aborts with throw.
# Pure ASCII.
$ErrorActionPreference = 'Stop'

$Allowed = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\'
$Target  = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging'

if ([string]::IsNullOrWhiteSpace($Target)) { throw 'REFUSE: empty target' }
if (-not $Target.StartsWith($Allowed)) { throw "REFUSE: target not under allowed prefix: $Target" }
if ($Target.Contains('*') -or $Target.Contains('?') -or $Target.Contains('..')) { throw "REFUSE: wildcard or dotdot in target: $Target" }
if (-not [System.IO.Path]::IsPathRooted($Target)) { throw "REFUSE: not absolute: $Target" }
if ($Target -eq $Allowed.TrimEnd('\') -or $Target -eq 'C:\' -or $Target -eq 'C:\Users') { throw "REFUSE: target too broad: $Target" }
if (-not (Test-Path -LiteralPath $Target)) { Write-Output "nothing to do: $Target does not exist"; exit 0 }

$items = Get-ChildItem -LiteralPath $Target -Force
Write-Output ("WILL DELETE: " + $Target)
Write-Output ("top-level entries: " + $items.Count)
Write-Output ("total files: " + (Get-ChildItem -LiteralPath $Target -Recurse -Force -File | Measure-Object).Count)
Write-Output ("total bytes: " + (Get-ChildItem -LiteralPath $Target -Recurse -Force -File | Measure-Object Length -Sum).Sum)
foreach ($i in $items) { Write-Output ("  " + $i.FullName) }

Remove-Item -LiteralPath $Target -Recurse -Force
Write-Output ("DELETED: " + $Target)
