# TASK-092 (B5): rebuild both editor variants, serially, from cmd (iron rule 3).
# Iron rule 1: no shell redirection anywhere - every native child is started with
# Start-Process -RedirectStandardOutput <absolute path>.
# ASCII only on purpose (PowerShell 5.1 reads BOM-less .ps1 as ANSI).
#
# NOTE: `Start-Process -Wait` is deliberately NOT used. The first run of this
# script hung there forever after scons had already printed "done building
# targets" and every compiler/linker process had exited (its documented behaviour
# is to wait for every process sharing the redirected handles, not just the
# child). The exit code is therefore taken by polling `HasExited` on the direct
# child, which is `cmd /c scons` - a process that cannot outlive its build.
param(
    [string]$Root = 'F:\moonbit-hof-rs\godot-mcp\godot',
    [string]$LogDir = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task092\logs',
    [string]$Only = ''
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Root)) { throw "no engine root: $Root" }
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

$cmdExe = Join-Path $env:SystemRoot 'System32\cmd.exe'
$scons = 'D:\Anaconda\Scripts\scons.exe'
if (-not (Test-Path -LiteralPath $scons)) { throw "no scons: $scons" }

# The two variants share bin\obj, so they must run one after the other.
$variants = @(
    @{ Name = 'mono'; Flag = 'module_mono_enabled=yes' },
    @{ Name = 'nomon'; Flag = 'module_mono_enabled=no' }
)

foreach ($v in $variants) {
    if ($Only -ne '' -and $Only -ne $v.Name) { continue }
    $out = Join-Path $LogDir ("build-" + $v.Name + ".log")
    $err = Join-Path $LogDir ("build-" + $v.Name + ".err.log")
    $sconsArgs = '/v:on /d /c ""{0}" platform=windows target=editor {1} tests=yes -j8 -k & echo TASK092_BUILD_EXIT=!ERRORLEVEL!"' -f $scons, $v.Flag
    "START {0} {1}" -f $v.Name, (Get-Date -Format 'HH:mm:ss') | Out-File -LiteralPath (Join-Path $LogDir 'build-summary.txt') -Append -Encoding utf8

    $p = Start-Process -FilePath $cmdExe -ArgumentList $sconsArgs -WorkingDirectory $Root -PassThru -NoNewWindow `
        -RedirectStandardOutput $out -RedirectStandardError $err
    $deadline = (Get-Date).AddHours(5)
    while (-not $p.HasExited) {
        if ((Get-Date) -gt $deadline) { throw "build timeout for $($v.Name)" }
        Start-Sleep -Seconds 5
    }
    # Give the redirected handles a moment to flush before the log is read.
    Start-Sleep -Seconds 3
    # The exit code is read from the marker cmd echoes at the end of the log, not
    # from `$p.ExitCode`: `Start-Process -PassThru` answered an empty ExitCode for
    # a build that really failed (PS 5.1), and a marker line cannot be empty.
    $marker = Select-String -LiteralPath $out -Pattern 'TASK092_BUILD_EXIT=(\d+)' | Select-Object -Last 1
    if ($null -eq $marker) { throw "no exit marker in $out" }
    $code = [int]$marker.Matches[0].Groups[1].Value
    "END   {0} exit={1} {2}" -f $v.Name, $code, (Get-Date -Format 'HH:mm:ss') |
        Out-File -LiteralPath (Join-Path $LogDir 'build-summary.txt') -Append -Encoding utf8
    if ($code -ne 0) {
        Write-Output ("BUILD_FAILED {0} exit={1} log={2}" -f $v.Name, $code, $out)
        exit 1
    }
}
Write-Output "BUILD_BOTH_DONE"
