param(
  [Parameter(Mandatory=$true)][string]$Name,
  [Parameter(Mandatory=$true)][string]$Class,
  [Parameter(Mandatory=$true)][string]$Tag,
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp',
  [switch]$Execute
)
# TASK-098: give a game project back its "first ever run" state without deleting it.
#
# Why this exists: the session's editor phase adds the scene's static nodes with
# `editor_add_nodes_batch`, and part B of TASK-098 exists precisely because running that
# batch twice used to write a whole duplicate layer. Since TASK-097 the second batch is
# refused, which is correct behaviour -- but it means replaying the same session against
# the project the previous run already wrote is no longer the same test. The honest way
# back to a first run is to put the old project aside and instantiate a new one.
#
# Iron rule 2 (destructive commands are refused by default):
#   * nothing is deleted -- the old project is MOVED (a rename inside one volume) into
#     recovery\work\task098\archive\, which preserves it byte for byte;
#   * the move target is checked against an absolute whitelist prefix on both ends;
#   * the source name is validated before it reaches the filesystem;
#   * a sha256 manifest of the project's meaningful files is written next to the archive
#     BEFORE the move, so the archived bytes can be compared later;
#   * it runs in dry-run mode unless -Execute is passed.
$ErrorActionPreference = 'Stop'

$NamePattern = '^[a-z][a-z0-9_]{1,31}$'
$TagPattern = '^[A-Za-z0-9._-]{1,64}$'
if ($Name -notmatch $NamePattern) { throw "REFUSED: -Name '$Name' does not match $NamePattern" }
if ($Tag -notmatch $TagPattern) { throw "REFUSED: -Tag '$Tag' does not match $TagPattern" }

$Projects = [System.IO.Path]::GetFullPath((Join-Path $Root 'projects')).TrimEnd('\') + '\'
$ArchiveRoot = [System.IO.Path]::GetFullPath((Join-Path $Root 'recovery\work\task098\archive')).TrimEnd('\') + '\'
$Source = [System.IO.Path]::GetFullPath((Join-Path $Root ("projects\{0}" -f $Name)))
$Dest = [System.IO.Path]::GetFullPath((Join-Path $ArchiveRoot ("{0}-{1}" -f $Name, $Tag)))

if (-not $Source.StartsWith($Projects, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "REFUSED: source '$Source' is not under '$Projects'"
}
if (-not $Dest.StartsWith($ArchiveRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "REFUSED: destination '$Dest' is not under '$ArchiveRoot'"
}
if ($Dest -match '[\*\?]') { throw "REFUSED: wildcard in '$Dest'" }
if (-not (Test-Path -LiteralPath $Source)) { throw "REFUSED: '$Source' does not exist" }
if (Test-Path -LiteralPath $Dest) { throw "REFUSED: '$Dest' already exists (an archive is never overwritten)" }

Write-Output ("source   : {0}" -f $Source)
Write-Output ("archive  : {0}" -f $Dest)
Write-Output '--- files that would be moved (build artifacts excluded from the manifest) ---'
$skip = '\\(\.godot|bin|obj|\.mono)\\'
$rows = @()
foreach ($f in (Get-ChildItem -LiteralPath $Source -Recurse -File -Force)) {
  if ($f.FullName -match $skip) { continue }
  $rel = $f.FullName.Substring($Source.Length + 1)
  $sha = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLower()
  $rows += [pscustomobject]@{ rel = $rel; bytes = $f.Length; sha256 = $sha }
  Write-Output ("  {0,-46} {1,8}  {2}" -f $rel, $f.Length, $sha.Substring(0, 16))
}
$total = (Get-ChildItem -LiteralPath $Source -Recurse -File -Force | Measure-Object).Count
Write-Output ("--- {0} manifest file(s); {1} file(s) in the directory altogether ---" -f $rows.Count, $total)

if (-not $Execute) {
  Write-Output 'DRY RUN (pass -Execute). Nothing was moved.'
  return
}

New-Item -ItemType Directory -Force -Path $ArchiveRoot | Out-Null
$manifest = Join-Path $ArchiveRoot ("{0}-{1}.manifest.json" -f $Name, $Tag)
$payload = [pscustomobject]@{
  task = 'TASK-098'
  game = $Name
  archived_from = $Source
  archived_to = $Dest
  archived_at = (Get-Date).ToString('s')
  files = $rows
}
[System.IO.File]::WriteAllText($manifest, ($payload | ConvertTo-Json -Depth 6),
                               (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("manifest : {0}" -f $manifest)

Move-Item -LiteralPath $Source -Destination $Dest
Write-Output ("moved    : {0} -> {1}" -f $Source, $Dest)

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'tools\new_game.ps1') `
  -Name $Name -Class $Class
Write-Output ("reinstanced: {0}" -f $Source)
