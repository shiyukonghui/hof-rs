param(
  [Parameter(Mandatory=$true)][string]$Script,
  [string]$Args = '',
  [Parameter(Mandatory=$true)][string]$Out,
  [string]$Err = '',
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp'
)
# TASK-103: run one PowerShell helper with its stdout/stderr OWNED by Start-Process,
# started from cmd.exe (iron rules 1 and 3).
$ErrorActionPreference = 'Stop'
if (-not $Err) { $Err = $Out + '.err.txt' }
$argList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"{0}\{1}"' -f $Root, $Script))
if ($Args) { $argList += $Args.Split(' ') }
$p = Start-Process -FilePath 'powershell' -ArgumentList $argList -WorkingDirectory $Root `
      -RedirectStandardOutput $Out -RedirectStandardError $Err -NoNewWindow -Wait -PassThru
Write-Output ("{0}: exit {1} -> {2}" -f $Script, $p.ExitCode, $Out)
if (Test-Path -LiteralPath $Err) {
  $n = (Get-Item -LiteralPath $Err).Length
  if ($n -gt 0) { Write-Output ("  stderr bytes: {0}" -f $n) }
}
