param(
  [Parameter(Mandatory=$true)][string]$Name,
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp',
  [switch]$Confirm
)
# reset_game.ps1 -- put ONE game project back to a freshly-scaffolded state.
#
# This is the only destructive tool in godot-mcp, so it follows iron rule 2 to
# the letter: the name must be a single path component, the target must resolve
# to exactly <Root>\projects\<name>, the whole manifest is printed BEFORE
# anything is removed, no pattern is ever used, and removal needs -Confirm.
# `runs\<name>\**` is NEVER touched: a reset must not destroy evidence.
$ErrorActionPreference = 'Stop'

if ($Name -notmatch '^[a-z][a-z0-9_]{1,31}$') { throw "REFUSED: bad -Name '$Name'" }
$projects = [System.IO.Path]::GetFullPath((Join-Path $Root 'projects')).TrimEnd('\')
$target = [System.IO.Path]::GetFullPath((Join-Path $projects $Name))
if ($target -ne ($projects + '\' + $Name)) { throw "REFUSED: '$target' is not '$projects\$Name'" }
if (-not (Test-Path -LiteralPath $target)) { throw "REFUSED: '$target' does not exist" }

$files = @(Get-ChildItem -LiteralPath $target -Recurse -Force -File -ErrorAction SilentlyContinue)
$bytes = 0
foreach ($f in $files) { $bytes += $f.Length }
Write-Output ('TARGET   : {0}' -f $target)
Write-Output ('FILES    : {0}' -f $files.Count)
Write-Output ('BYTES    : {0}' -f $bytes)
Write-Output ('MB       : {0:N2}' -f ($bytes / 1MB))
Write-Output ('KEEPS    : {0}  (evidence is never touched)' -f (Join-Path $Root ("runs\{0}" -f $Name)))
Write-Output 'TOP LEVEL:'
foreach ($t in (Get-ChildItem -LiteralPath $target -Force)) { Write-Output ('   {0} {1}' -f $t.Mode, $t.Name) }

if (-not $Confirm) {
  Write-Output 'DRY RUN: nothing removed. Re-run with -Confirm to actually reset.'
  exit 0
}

Remove-Item -LiteralPath $target -Recurse -Force
if (Test-Path -LiteralPath $target) { Write-Output 'FAILED: the target still exists'; exit 1 }
Write-Output ('REMOVED  : {0}' -f $target)

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'tools\new_game.ps1') -Name $Name -Root $projects -Template (Join-Path $projects '_template')
if ($LASTEXITCODE -ne 0) { Write-Output 'FAILED: new_game.ps1 did not succeed'; exit 1 }
Write-Output ('RESET    : {0} is back to the template state' -f $Name)
exit 0
