param(
  [Parameter(Mandatory=$true)][string]$Name,
  [string]$Class,
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp\projects',
  [string]$Template = 'F:\moonbit-hof-rs\godot-mcp\projects\_template'
)
# new_game.ps1 -- instantiate the reusable C# Godot .NET template.
#
# Iron rule 2: the only destructive operation is "refuse to overwrite an
# existing project"; nothing is ever removed. Targets are absolute, and the
# name is validated before it reaches the filesystem.
$ErrorActionPreference = 'Stop'

if ($Name -notmatch '^[a-z][a-z0-9_]{1,31}$') {
  throw "REFUSED: -Name must match ^[a-z][a-z0-9_]{1,31}$ (got '$Name')"
}
if (-not $Class) {
  $Class = (($Name -split '_' | ForEach-Object { $_.Substring(0,1).ToUpper() + $_.Substring(1) }) -join '') + 'Game'
}
if ($Class -notmatch '^[A-Z][A-Za-z0-9]{1,63}$') {
  throw "REFUSED: -Class must match ^[A-Z][A-Za-z0-9]{1,63}$ (got '$Class')"
}
if (-not (Test-Path -LiteralPath $Template)) { throw "template not found: $Template" }

$dest = Join-Path $Root $Name
if (Test-Path -LiteralPath $dest) {
  throw "REFUSED: '$dest' already exists (nothing is ever overwritten)"
}

Write-Output ("template : {0}" -f $Template)
Write-Output ("dest     : {0}" -f $dest)
Write-Output ("name     : {0}" -f $Name)
Write-Output ("class    : {0}" -f $Class)

Copy-Item -LiteralPath $Template -Destination $dest -Recurse -Force

# The template's own docs are not part of an instance; the instance's README is
# generated from README.game.md below.
foreach ($doc in @('README.md', 'README.game.md')) {
  $p = Join-Path $dest $doc
  if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force }
}

# Instantiate the placeholders, and rename the placeholder files.
$renames = @()
Get-ChildItem -LiteralPath $dest -Recurse -File -Force | ForEach-Object {
  $f = $_
  $text = [System.IO.File]::ReadAllText($f.FullName)
  $new = $text.Replace('__NAME__', $Name).Replace('__CLASS__', $Class)
  if ($new -ne $text) {
    [System.IO.File]::WriteAllText($f.FullName, $new, (New-Object System.Text.UTF8Encoding($false)))
    $renames += $f.FullName.Substring($dest.Length + 1)
  }
}
foreach ($r in $renames) { Write-Output ("  substituted: {0}" -f $r) }

# The instance's own README.
$gameReadme = Join-Path $Template 'README.game.md'
if (Test-Path -LiteralPath $gameReadme) {
  $text = [System.IO.File]::ReadAllText($gameReadme)
  $text = $text.Replace('__NAME__', $Name).Replace('__CLASS__', $Class)
  [System.IO.File]::WriteAllText((Join-Path $dest 'README.md'), $text, (New-Object System.Text.UTF8Encoding($false)))
  Write-Output '  generated : README.md (from _template\README.game.md)'
}

$csproj = Join-Path $dest '__NAME__.csproj'
if (Test-Path -LiteralPath $csproj) { Move-Item -LiteralPath $csproj -Destination (Join-Path $dest ($Name + '.csproj')) }
$cs = Join-Path $dest 'src\__CLASS__.cs'
if (Test-Path -LiteralPath $cs) { Move-Item -LiteralPath $cs -Destination (Join-Path $dest ('src\' + $Class + '.cs')) }

$left = @(Get-ChildItem -LiteralPath $dest -Recurse -File -Force | Where-Object { $_.Name -like '*__*__*' })
Write-Output ("placeholder files left: {0}" -f $left.Count)
Get-ChildItem -LiteralPath $dest -Recurse -File -Force | ForEach-Object { Write-Output ("  {0}" -f $_.FullName.Substring($dest.Length + 1)) }
Write-Output ("created  : {0}" -f $dest)
