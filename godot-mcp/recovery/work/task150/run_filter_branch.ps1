$ErrorActionPreference = 'Continue'
Push-Location 'F:\moonbit-hof-rs'
$env:FILTER_BRANCH_SQUELCH_WARNING = '1'

$paths = @(
  'godot-mcp/recovery/work/task148/exe/',
  'godot-mcp/recovery/work/task148/unzip-test/',
  'godot-mcp/recovery/rebuild/work2b/gen-hits.txt',
  'godot-mcp/recovery/rebuild/work2b/gen-strings.txt',
  'godot-mcp/recovery/rebuild/work2b/gen-biglines.txt'
)

$cmd = 'git rm -r --cached --ignore-unmatch ' + ($paths -join ' ')

Write-Output '=== INDEX-FILTER COMMAND STRING ==='
Write-Output $cmd
Write-Output '=== DRY PARSE CHECK: equivalent git ls-files with exclude pathspecs ==='
$lsArgs = @('ls-files') + ($paths | ForEach-Object { ':(exclude)' + $_ })
$out = & git @lsArgs
Write-Output ('ls-files-with-excludes returned ' + @($out).Count + ' paths (expect the task148 non-exe keeper files, 73)')

Write-Output '=== RUNNING FILTER-BRANCH ==='
Write-Output 'git filter-branch --force --index-filter "<above>" --prune-empty --tag-name-filter cat -- --all'
& git filter-branch --force --index-filter $cmd --prune-empty --tag-name-filter cat -- --all
Write-Output ('FILTER_BRANCH_EXIT=' + $LASTEXITCODE)
Pop-Location
