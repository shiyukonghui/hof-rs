param(
  [Parameter(Mandatory=$true)][string]$Path,
  [Parameter(Mandatory=$true)][string]$AllowedPrefix,
  [switch]$Confirm
)
# Iron rule 2: destructive commands are refused by default.
#  - the target must be absolute, non-empty, and under an explicitly allowed prefix
#  - wildcards and '..' are refused outright
#  - the full manifest is printed BEFORE anything is removed
#  - removal needs -Confirm, and uses -LiteralPath (never a pattern)
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($Path)) { throw 'REFUSED: empty path' }
if ($Path -match '[\*\?\[]') { throw "REFUSED: '$Path' contains a wildcard" }
if ($Path -match '\.\.') { throw "REFUSED: '$Path' contains '..'" }
if (-not [System.IO.Path]::IsPathRooted($Path)) { throw "REFUSED: '$Path' is not absolute" }

$full = [System.IO.Path]::GetFullPath($Path).TrimEnd('\')
$prefix = [System.IO.Path]::GetFullPath($AllowedPrefix).TrimEnd('\')
if (-not $full.StartsWith($prefix + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "REFUSED: '$full' is not under the allowed prefix '$prefix'"
}
if (-not (Test-Path -LiteralPath $full)) { throw "REFUSED: '$full' does not exist" }

$files = @(Get-ChildItem -LiteralPath $full -Recurse -Force -File -ErrorAction SilentlyContinue)
$bytes = 0
foreach ($f in $files) { $bytes += $f.Length }
Write-Output ('TARGET   : {0}' -f $full)
Write-Output ('PREFIX   : {0} (allowed)' -f $prefix)
Write-Output ('FILES    : {0}' -f $files.Count)
Write-Output ('BYTES    : {0}' -f $bytes)
Write-Output ('MB       : {0:N1}' -f ($bytes / 1MB))
$top = @(Get-ChildItem -LiteralPath $full -Force)
Write-Output ('TOP LEVEL: {0} entries' -f $top.Count)
foreach ($t in $top | Select-Object -First 25) { Write-Output ('   {0} {1}' -f $t.Mode, $t.Name) }

if (-not $Confirm) {
  Write-Output 'DRY RUN: nothing removed. Re-run with -Confirm to actually delete.'
  exit 0
}

Remove-Item -LiteralPath $full -Recurse -Force
if (Test-Path -LiteralPath $full) { Write-Output 'FAILED: the target still exists'; exit 1 }
Write-Output ('REMOVED  : {0}' -f $full)
exit 0
