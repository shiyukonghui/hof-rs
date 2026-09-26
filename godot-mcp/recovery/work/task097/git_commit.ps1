param(
  [Parameter(Mandatory=$true)][string]$Repo,
  [Parameter(Mandatory=$true)][string]$MessageFile
)
# TASK-097: commit through a message FILE (`git commit -F`), so no shell
# redirection and no quoting games are involved.
$ErrorActionPreference = 'Stop'
& git -C $Repo commit -F $MessageFile
Write-Output ("commit exit: {0}" -f $LASTEXITCODE)
& git -C $Repo log --oneline -1
