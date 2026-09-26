param(
  [Parameter(Mandatory=$true)][string]$Script,
  [string]$Args = '',
  [Parameter(Mandatory=$true)][string]$Out,
  [string]$Err = '',
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp'
)
# TASK-102: run one python helper with its stdout/stderr OWNED by Start-Process.
# Iron rule 1: no `>` and no `|`-into-a-file anywhere in this task.
$ErrorActionPreference = 'Stop'
if (-not $Err) { $Err = $Out + '.err.txt' }
$argList = @(('"{0}\{1}"' -f $Root, $Script))
if ($Args) { $argList += $Args.Split(' ') }
$p = Start-Process -FilePath 'python' -ArgumentList $argList -WorkingDirectory $Root `
      -RedirectStandardOutput $Out -RedirectStandardError $Err -NoNewWindow -Wait -PassThru
Write-Output ("{0}: exit {1} -> {2}" -f $Script, $p.ExitCode, $Out)
if (Test-Path -LiteralPath $Err) {
  $n = (Get-Item -LiteralPath $Err).Length
  if ($n -gt 0) { Write-Output ("  stderr bytes: {0}" -f $n) }
}
