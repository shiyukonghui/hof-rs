param(
  [Parameter(Mandatory=$true)][string]$Repo,
  [Parameter(Mandatory=$true)][string]$MessageFile,
  [Parameter(Mandatory=$true)][string]$Tag,
  [switch]$Push,
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp'
)
# TASK-103: commit (and optionally push) one repository, started from cmd.exe (iron
# rule 3) with its stdout/stderr owned by Start-Process (iron rule 1: the commit
# message never goes through a shell redirect).
$ErrorActionPreference = 'Stop'
$logs = Join-Path $Root 'recovery\work\task103\logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$out = Join-Path $logs ("git-$Tag.out.txt")
$err = Join-Path $logs ("git-$Tag.err.txt")
$bat = Join-Path $logs ("git-$Tag.cmd")
if (Test-Path -LiteralPath $out) { Remove-Item -LiteralPath $out -Force }
if (Test-Path -LiteralPath $err) { Remove-Item -LiteralPath $err -Force }
$lines = @('@echo off', ('cd /d "{0}"' -f $Repo), 'git add -A', ('git commit -F "{0}"' -f $MessageFile))
if ($Push) { $lines += 'git push' }
$lines += 'echo GIT_EXIT=%ERRORLEVEL%'
$lines += 'git log --oneline -3'
$lines += 'git status --short'
Set-Content -LiteralPath $bat -Value $lines -Encoding ASCII
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $bat -WorkingDirectory $Repo `
      -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -Wait -PassThru
Write-Output ("git {0}: process exit {1} -> {2}" -f $Tag, $p.ExitCode, $out)
if (Test-Path -LiteralPath $out) { Get-Content -LiteralPath $out | ForEach-Object { Write-Output ('  | ' + $_) } }
if (Test-Path -LiteralPath $err) {
  $e = (Get-Item -LiteralPath $err).Length
  if ($e -gt 0) { Get-Content -LiteralPath $err -TotalCount 10 | ForEach-Object { Write-Output ('  ! ' + $_) } }
}
