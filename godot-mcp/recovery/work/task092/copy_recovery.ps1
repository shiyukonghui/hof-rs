# TASK-092 (A): copy C:\...\mcp-recovery -> F:\moonbit-hof-rs\godot-mcp\recovery
# Iron rule 1: no shell redirection. Every native process is started with
#               Start-Process -RedirectStandardOutput <absolute path>.
# Iron rule 3: robocopy is started from cmd.exe.
# ASCII only on purpose: PowerShell 5.1 reads BOM-less .ps1 as ANSI.
param(
    [string]$Src = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery',
    [string]$Dst = 'F:\moonbit-hof-rs\godot-mcp\recovery'
)
$ErrorActionPreference = 'Stop'
$logDir = Join-Path $PSScriptRoot 'logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

function Assert-SafeRoot {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { throw 'empty path' }
    if (-not [System.IO.Path]::IsPathRooted($Path)) { throw "not absolute: $Path" }
    if ($Path -match '[?*]') { throw "wildcard in path: $Path" }
    if ($Path -match '\.\.') { throw "dot-dot in path: $Path" }
}
Assert-SafeRoot $Src
Assert-SafeRoot $Dst

if (-not (Test-Path -LiteralPath $Src)) { throw "source missing: $Src" }
if ((Get-Item -LiteralPath $Src -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'source is a reparse point' }

# destination must not already hold migrated payload
if (Test-Path -LiteralPath (Join-Path $Dst 'reports')) { throw "destination already populated: $Dst\reports" }
New-Item -ItemType Directory -Path $Dst -Force | Out-Null

# ---- mapping -------------------------------------------------------------
# root *.md  -> <Dst>\reports\
# root <dir> -> <Dst>\<dir>\   (structure preserved)
$rootFiles = Get-ChildItem -LiteralPath $Src -File | Sort-Object Name
$rootDirs  = Get-ChildItem -LiteralPath $Src -Directory | Sort-Object Name

"### SOURCE INVENTORY" | Out-File -LiteralPath (Join-Path $logDir 'inventory.txt') -Encoding utf8
foreach ($f in $rootFiles) { "FILE {0,12} {1}" -f $f.Length, $f.Name | Out-File -LiteralPath (Join-Path $logDir 'inventory.txt') -Append -Encoding utf8 }
foreach ($d in $rootDirs) {
    $all = Get-ChildItem -LiteralPath $d.FullName -Recurse -File -ErrorAction SilentlyContinue
    "DIR  {0,12} files={1,-7} {2}" -f (($all | Measure-Object Length -Sum).Sum), $all.Count, $d.Name |
        Out-File -LiteralPath (Join-Path $logDir 'inventory.txt') -Append -Encoding utf8
}

$reportsDir = Join-Path $Dst 'reports'
New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null

# ---- copy root files into reports\ --------------------------------------
foreach ($f in $rootFiles) {
    Copy-Item -LiteralPath $f.FullName -Destination (Join-Path $reportsDir $f.Name) -Force
}

# ---- copy top-level directories with robocopy, started from cmd ---------
$cmdExe = Join-Path $env:SystemRoot 'System32\cmd.exe'
$robocopy = Join-Path $env:SystemRoot 'System32\robocopy.exe'
foreach ($d in $rootDirs) {
    $srcDir = $d.FullName
    $dstDir = Join-Path $Dst $d.Name
    $outLog = Join-Path $logDir ("robocopy-" + $d.Name + ".log")
    $cmdLine = '/d /c ""{0}" "{1}" "{2}" /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /MT:8 /NFL /NDL"' -f $robocopy, $srcDir, $dstDir
    $p = Start-Process -FilePath $cmdExe -ArgumentList $cmdLine -Wait -PassThru -NoNewWindow `
        -RedirectStandardOutput $outLog -RedirectStandardError (Join-Path $logDir ("robocopy-" + $d.Name + ".err.log"))
    "ROBOCOPY {0,-12} exit={1}" -f $d.Name, $p.ExitCode |
        Out-File -LiteralPath (Join-Path $logDir 'copy-summary.txt') -Append -Encoding utf8
    if ($p.ExitCode -ge 8) { throw "robocopy failed for $($d.Name): exit $($p.ExitCode)" }
}

"COPY_DONE {0}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') |
    Out-File -LiteralPath (Join-Path $logDir 'copy-summary.txt') -Append -Encoding utf8
Write-Output "COPY_DONE"
