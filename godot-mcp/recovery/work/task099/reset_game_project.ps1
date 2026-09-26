param(
  [Parameter(Mandatory=$true)][string]$Name,
  [Parameter(Mandatory=$true)][string]$Class,
  [Parameter(Mandatory=$true)][string]$Tag,
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp'
)
# TASK-099: archive a game project before re-instantiating it, so a re-run starts from
# the same fresh template the first run started from.
#
# Iron rule 2 (destructive commands are refused by default): this never deletes
# anything. It writes the sha256 manifest of every file FIRST, then MOVES the directory
# into the task's own archive folder. The move target is an absolute path under
# recovery\work\task099\archive\ and is refused if it already exists.
$ErrorActionPreference = 'Stop'
if ($Name -notmatch '^[a-z][a-z0-9_]{1,31}$') { throw "REFUSED: bad -Name '$Name'" }
if ($Class -notmatch '^[A-Z][A-Za-z0-9]{1,63}$') { throw "REFUSED: bad -Class '$Class'" }
if ($Tag -notmatch '^[a-z0-9][a-z0-9\-]{1,31}$') { throw "REFUSED: bad -Tag '$Tag'" }

$project = Join-Path $Root ('projects\' + $Name)
$archiveRoot = Join-Path $Root 'recovery\work\task099\archive'
$dest = Join-Path $archiveRoot ($Name + '-' + $Tag)
$manifest = Join-Path $archiveRoot ($Name + '-' + $Tag + '.manifest.json')

if (-not (Test-Path -LiteralPath $project)) { throw "REFUSED: project not found: $project" }
if (Test-Path -LiteralPath $dest) { throw "REFUSED: archive destination already exists: $dest" }
New-Item -ItemType Directory -Force -Path $archiveRoot | Out-Null

# 1. evidence first: sha256 + byte count of every file under the project.
$files = @()
Get-ChildItem -LiteralPath $project -Recurse -File -Force | ForEach-Object {
  $files += [pscustomobject]@{
    path = $_.FullName.Substring($project.Length + 1)
    bytes = $_.Length
    sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
  }
}
$doc = [pscustomobject]@{
  task = 'TASK-099'; game = $Name; class = $Class; tag = $Tag
  project = $project; archived_to = $dest
  file_count = $files.Count
  total_bytes = ($files | Measure-Object -Property bytes -Sum).Sum
  files = $files
}
[System.IO.File]::WriteAllText($manifest, ($doc | ConvertTo-Json -Depth 5),
                               (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("manifest : {0} ({1} files, {2} bytes)" -f $manifest, $files.Count, $doc.total_bytes)

# 2. the move itself (no delete anywhere).
Move-Item -LiteralPath $project -Destination $dest
Write-Output ("moved    : {0} -> {1}" -f $project, $dest)

# 3. re-instantiate from the template.
$out = Join-Path $archiveRoot ($Name + '-' + $Tag + '.newgame.txt')
$err = Join-Path $archiveRoot ($Name + '-' + $Tag + '.newgame.err.txt')
$bat = Join-Path $archiveRoot ('newgame-' + $Name + '.cmd')
$batch = @(
  '@echo off',
  ('powershell -NoProfile -ExecutionPolicy Bypass -File "{0}\tools\new_game.ps1" -Name {1} -Class {2}' -f $Root, $Name, $Class),
  'echo NEWGAME_EXIT=%ERRORLEVEL%'
)
Set-Content -LiteralPath $bat -Value $batch -Encoding ASCII
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $bat -WorkingDirectory $Root `
      -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -Wait -PassThru
Write-Output ("new_game : process exit {0}" -f $p.ExitCode)
Get-Content -LiteralPath $out | ForEach-Object { Write-Output ('  | ' + $_) }
if (Test-Path -LiteralPath $err) { Get-Content -LiteralPath $err | ForEach-Object { Write-Output ('  ! ' + $_) } }
$expected = Join-Path $project ('src\' + $Class + '.cs')
if (-not (Test-Path -LiteralPath $expected)) {
  throw "REFUSED: re-instantiation did not produce $expected"
}
Write-Output ("ready    : {0}" -f $project)
