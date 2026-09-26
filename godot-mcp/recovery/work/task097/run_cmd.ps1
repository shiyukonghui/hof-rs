param(
  [Parameter(Mandatory=$true)][string]$Command,
  [Parameter(Mandatory=$true)][string]$Tag,
  [string]$WorkDir = 'F:\moonbit-hof-rs\godot-mcp\godot',
  [string]$LogDir = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task097\logs'
)
# TASK-097 generic runner. Iron rule 1: stdout/stderr are owned by
# Start-Process -RedirectStandardOutput/-RedirectStandardError, never by a shell
# redirection. Iron rule 3: the child is cmd.exe, so every command is started
# from cmd. The exit code is echoed INSIDE the child (delayed expansion) so it
# survives PowerShell's handling of a redirected child.
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$out = Join-Path $LogDir ($Tag + '.stdout.txt')
$err = Join-Path $LogDir ($Tag + '.stderr.txt')
$wrapped = ($Command + ' & echo TASK097_EXIT=!ERRORLEVEL!')
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/v:on', '/c', $wrapped -WorkingDirectory $WorkDir `
      -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -PassThru
$p.WaitForExit()
Write-Output ("tag={0} exit={1}" -f $Tag, $p.ExitCode)
Write-Output ("out={0}" -f $out)
Write-Output ("err={0}" -f $err)
Get-Content -LiteralPath $out -Tail 30 | ForEach-Object { Write-Output ('  | ' + $_) }
$e = Get-Content -LiteralPath $err -Tail 20 -ErrorAction SilentlyContinue
if ($e) { Write-Output '  [stderr]'; foreach ($l in $e) { Write-Output ('  | ' + $l) } }
