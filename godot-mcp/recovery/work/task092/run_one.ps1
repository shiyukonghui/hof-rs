# TASK-092: run one native command from cmd, captured to an absolute log, and
# report the exit code read from a marker cmd echoes at the end of the log.
# Iron rule 1: no shell redirection in the caller - Start-Process owns the
# handles. Iron rule 3: the command always starts from cmd.exe.
#
# `Start-Process -Wait` is not used (it hung on the first build after the child
# had already exited); the exit code is taken from the marker, because
# `-PassThru`'s ExitCode answered empty for a process that really failed.
param(
    [Parameter(Mandatory = $true)][string]$CommandLine,
    [Parameter(Mandatory = $true)][string]$Log,
    [string]$WorkDir = 'F:\moonbit-hof-rs\godot-mcp\godot',
    [int]$TimeoutSeconds = 3600
)
$ErrorActionPreference = 'Stop'
$cmdExe = Join-Path $env:SystemRoot 'System32\cmd.exe'
$logDir = Split-Path -Parent $Log
if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

$args = '/v:on /d /c "{0} & echo TASK092_EXIT=!ERRORLEVEL!"' -f $CommandLine
$p = Start-Process -FilePath $cmdExe -ArgumentList $args -WorkingDirectory $WorkDir -PassThru -NoNewWindow `
    -RedirectStandardOutput $Log -RedirectStandardError ($Log + '.err')
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while (-not $p.HasExited) {
    if ((Get-Date) -gt $deadline) { throw "timeout after $TimeoutSeconds s: $CommandLine" }
    Start-Sleep -Milliseconds 500
}
Start-Sleep -Seconds 1
$marker = Select-String -LiteralPath $Log -Pattern 'TASK092_EXIT=(-?\d+)' | Select-Object -Last 1
if ($null -eq $marker) { throw "no exit marker in $Log" }
$code = [int]$marker.Matches[0].Groups[1].Value
Write-Output ("TASK092_EXIT={0} log={1}" -f $code, $Log)
exit $code
