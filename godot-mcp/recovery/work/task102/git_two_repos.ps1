param(
  [string]$Root = 'F:\moonbit-hof-rs',
  [string]$Out = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task102\logs\git-two-repos.txt'
)
# TASK-102: the two repositories' logs and working trees, with the output owned by
# Start-Process (iron rule 1: no shell redirection anywhere).
$ErrorActionPreference = 'Stop'
$err = $Out + '.err.txt'
$bat = $Out + '.cmd'
$batch = @(
  '@echo off',
  ('cd /d "{0}"' -f $Root),
  'echo === MAIN REPO (branch, HEAD) ===',
  'git rev-parse --abbrev-ref HEAD',
  'git rev-parse HEAD',
  'echo === MAIN REPO git log --oneline -8 ===',
  'git log --oneline -8',
  'echo === MAIN REPO git status --short ===',
  'git status --short',
  'echo',
  ('cd /d "{0}\godot-mcp\godot"' -f $Root),
  'echo === ENGINE REPO (branch, HEAD) ===',
  'git rev-parse --abbrev-ref HEAD',
  'git rev-parse HEAD',
  'echo === ENGINE REPO remote ===',
  'git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild',
  'echo === ENGINE REPO git log --oneline -8 ===',
  'git log --oneline -8',
  'echo === ENGINE REPO git status --short ===',
  'git status --short',
  'echo === ENGINE REPO diff vs the build anchor ===',
  'git diff --name-only --no-renames 2385fe2fb..HEAD'
)
Set-Content -LiteralPath $bat -Value $batch -Encoding ASCII
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $bat -WorkingDirectory $Root `
      -RedirectStandardOutput $Out -RedirectStandardError $err -NoNewWindow -Wait -PassThru
Write-Output ("git two-repos: exit {0} -> {1}" -f $p.ExitCode, $Out)
Get-Content -LiteralPath $Out | ForEach-Object { Write-Output $_ }
