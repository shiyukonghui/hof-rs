# TASK-092 (B5): rebuild both editor variants, serially, from cmd (iron rule 3).
# Iron rule 1: no shell redirection anywhere - every native child is started with
# Start-Process -RedirectStandardOutput <absolute path>.
# ASCII only on purpose (PowerShell 5.1 reads BOM-less .ps1 as ANSI).
param(
    [string]$Root = 'F:\moonbit-hof-rs\godot-mcp\godot',
    [string]$LogDir = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task092\logs'
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
    $out = Join-Path $LogDir ("build-" + $v.Name + ".log")
    $err = Join-Path $LogDir ("build-" + $v.Name + ".err.log")
    $args = '/d /c ""{0}" platform=windows target=editor {1} tests=yes -j8 -k"' -f $scons, $v.Flag
    "START {0} {1}" -f $v.Name, (Get-Date -Format 'HH:mm:ss') | Out-File -LiteralPath (Join-Path $LogDir 'build-summary.txt') -Append -Encoding utf8
    $p = Start-Process -FilePath $cmdExe -ArgumentList $args -WorkingDirectory $Root -Wait -PassThru -NoNewWindow `
        -RedirectStandardOutput $out -RedirectStandardError $err
    "END   {0} exit={1} {2}" -f $v.Name, $p.ExitCode, (Get-Date -Format 'HH:mm:ss') |
        Out-File -LiteralPath (Join-Path $LogDir 'build-summary.txt') -Append -Encoding utf8
    if ($p.ExitCode -ne 0) { throw "build failed for $($v.Name): exit $($p.ExitCode) (see $out)" }
}
Write-Output "BUILD_BOTH_DONE"
