param(
  [Parameter(Mandatory=$true)][string]$Command,
  [Parameter(Mandatory=$true)][string]$Tag,
  [string]$WorkDir = 'F:\moonbit-hof-rs\godot-mcp',
  [string]$LogDir = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task098\logs',
  [int]$Tail = 30
)
# TASK-098 generic runner (same shape as TASK-097's, retagged).
#   iron rule 1: stdout/stderr are owned by Start-Process -RedirectStandardOutput /
#                -RedirectStandardError, never by a shell redirection.
#   iron rule 3: the child is cmd.exe, so every command is started from cmd.
# The exit code is echoed INSIDE the child (delayed expansion) so it survives
# PowerShell's handling of a redirected child; TASK098_EXIT is the number to quote.
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$out = Join-Path $LogDir ($Tag + '.stdout.txt')
$err = Join-Path $LogDir ($Tag + '.stderr.txt')
$wrapped = ($Command + ' & echo TASK098_EXIT=!ERRORLEVEL!')
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/v:on', '/c', $wrapped -WorkingDirectory $WorkDir `
      -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -PassThru
$p.WaitForExit()
Write-Output ("tag={0} exit={1}" -f $Tag, $p.ExitCode)
Write-Output ("out={0}" -f $out)
Write-Output ("err={0}" -f $err)
Get-Content -LiteralPath $out -Tail $Tail -ErrorAction SilentlyContinue | ForEach-Object { Write-Output ('  | ' + $_) }
$e = Get-Content -LiteralPath $err -Tail 20 -ErrorAction SilentlyContinue
if ($e) { Write-Output '  [stderr]'; foreach ($l in $e) { Write-Output ('  | ' + $l) } }
