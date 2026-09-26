param(
  [Parameter(Mandatory=$true)][string]$Name,
  [Parameter(Mandatory=$true)][string]$Class,
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp'
)
# TASK-103 / iron rule 6: a round restarts from the SAME template, not from the
# project the previous round left behind. The old project is archived, never
# deleted:
#
#   1. a sha256 manifest of every file is written first (name, size, sha256);
#   2. the whole directory is MOVED (not copied, not removed) into
#      recovery\work\task103\archive\<name>-<stamp>;
#   3. only then is the project re-instantiated from projects\_template.
#
# Everything is started from cmd.exe (iron rule 3) with its output owned by
# Start-Process (iron rule 1).
$ErrorActionPreference = 'Stop'
$work = Join-Path $Root 'recovery\work\task103'
$logs = Join-Path $work 'logs'
$python = Join-Path $work 'hash_tree.py'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$project = Join-Path $Root ("projects\{0}" -f $Name)
$stamp = (Get-Date -Format 'yyyyMMdd-HHmmss')
$archive = Join-Path $work ("archive\{0}-{1}" -f $Name, $stamp)
if (-not (Test-Path -LiteralPath $project)) { throw "no project to archive: $project" }
if (Test-Path -LiteralPath $archive) { throw "REFUSED: archive target exists: $archive" }
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $archive) | Out-Null

# 1. the sha256 manifest, written by a Python writer (iron rule 1)
$manifest = "$archive.manifest.json"
$p = Start-Process -FilePath 'python' -ArgumentList ('"{0}" "{1}" "{2}"' -f $python, $project, $manifest) `
      -RedirectStandardOutput (Join-Path $logs "hash-$Name.txt") `
      -RedirectStandardError (Join-Path $logs "hash-$Name.err.txt") -NoNewWindow -Wait -PassThru
if ($p.ExitCode -ne 0) { throw "hash_tree failed for $project (exit $($p.ExitCode))" }
Write-Output ("manifest : {0}" -f $manifest)

# 2. the move (never a delete)
Move-Item -LiteralPath $project -Destination $archive
Write-Output ("archived : {0}" -f $archive)

# 3. the fresh instance
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $work 'new_game_run.ps1') -Name $Name -Class $Class
if (-not (Test-Path -LiteralPath $project)) { throw "new_game did not create $project" }
Write-Output ("fresh    : {0}" -f $project)
