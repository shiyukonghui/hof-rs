# TASK-092 (A): per-file sha256 verification of the recovery migration.
# Both sides are enumerated with the \\?\ long-path prefix and .NET APIs, because
# Get-ChildItem is documented to silently skip paths over 260 characters.
# ASCII only on purpose.
param(
    [string]$Src = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery',
    [string]$Dst = 'F:\moonbit-hof-rs\godot-mcp\recovery'
)
$ErrorActionPreference = 'Stop'
$logDir = Join-Path $PSScriptRoot 'logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$report = Join-Path $logDir 'verify.txt'

function Long([string]$p) {
    if ($p.StartsWith('\\?\')) { return $p }
    if ($p.StartsWith('\\')) { return '\\?\UNC\' + $p.Substring(2) }
    return '\\?\' + $p
}
function Sha256([string]$p) {
    $fs = New-Object System.IO.FileStream((Long $p), [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite, 1048576, [System.IO.FileOptions]::SequentialScan)
    try {
        $sha = [System.Security.Cryptography.SHA256]::Create()
        try { return [System.BitConverter]::ToString($sha.ComputeHash($fs)).Replace('-', '') }
        finally { $sha.Dispose() }
    } finally { $fs.Dispose() }
}

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("### VERIFY recovery migration")
$lines.Add(("src={0}" -f $Src))
$lines.Add(("dst={0}" -f $Dst))

# ---- build the expected (src -> dst) map --------------------------------
$srcFiles = New-Object System.Collections.Generic.List[object]
foreach ($f in [System.IO.Directory]::EnumerateFiles((Long $Src), '*', [System.IO.SearchOption]::TopDirectoryOnly)) {
    $srcFiles.Add([pscustomobject]@{ Src = $f; Rel = 'reports\' + [System.IO.Path]::GetFileName($f) })
}
foreach ($d in [System.IO.Directory]::EnumerateDirectories((Long $Src), '*', [System.IO.SearchOption]::TopDirectoryOnly)) {
    $name = [System.IO.Path]::GetFileName($d)
    if ($name -eq '_migration-task092') { continue }
    foreach ($f in [System.IO.Directory]::EnumerateFiles((Long $d), '*', [System.IO.SearchOption]::AllDirectories)) {
        $inner = $f.Substring($d.Length).TrimStart('\')
        $srcFiles.Add([pscustomobject]@{ Src = $f; Rel = $name + '\' + $inner })
    }
}

$expectedDst = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($r in $srcFiles) { [void]$expectedDst.Add(((Long $Dst) + '\' + $r.Rel)) }

# ---- enumerate destination ----------------------------------------------
$dstFiles = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
$scratchPrefix = (Long $Dst) + '\_migration-task092'
foreach ($f in [System.IO.Directory]::EnumerateFiles((Long $Dst), '*', [System.IO.SearchOption]::AllDirectories)) {
    # The migration's own scratch tree (scripts + robocopy logs) is not part of the
    # migrated payload; it is declared and moved under work\task092 afterwards.
    if ($f.StartsWith($scratchPrefix, [System.StringComparison]::OrdinalIgnoreCase)) { continue }
    [void]$dstFiles.Add($f)
}

$missing = 0; $extra = 0; $compared = 0; $mismatch = 0; $sizeMismatch = 0
$srcTotal = [long]0; $dstTotal = [long]0
$mismatchLines = New-Object System.Collections.Generic.List[string]

foreach ($r in $srcFiles) {
    $srcPath = $r.Src
    $dstPath = ((Long $Dst) + '\' + $r.Rel)
    $srcLen = (New-Object System.IO.FileInfo((Long $srcPath))).Length
    $srcTotal += $srcLen
    if (-not $dstFiles.Contains($dstPath)) { $missing++; $mismatchLines.Add("MISSING $dstPath"); continue }
    $dstLen = (New-Object System.IO.FileInfo($dstPath)).Length
    $dstTotal += $dstLen
    if ($dstLen -ne $srcLen) { $sizeMismatch++; $mismatchLines.Add("SIZE $srcLen != $dstLen  $dstPath"); continue }
    $hs = Sha256 $srcPath
    $hd = Sha256 $dstPath
    $compared++
    if ($hs -ne $hd) { $mismatch++; $mismatchLines.Add("SHA $hs != $hd  $dstPath") }
}
foreach ($f in $dstFiles) { if (-not $expectedDst.Contains($f)) { $extra++; $mismatchLines.Add("EXTRA $f") } }

$lines.Add(("src_files={0} expected_dst_files={1} dst_files={2}" -f $srcFiles.Count, $expectedDst.Count, $dstFiles.Count))
$lines.Add(("compared={0} mismatched={1} size_mismatch={2} missing_in_dst={3} extra_in_dst={4}" -f $compared, $mismatch, $sizeMismatch, $missing, $extra))
$lines.Add(("src_total_bytes={0} dst_matched_total_bytes={1}" -f $srcTotal, $dstTotal))
foreach ($m in $mismatchLines) { $lines.Add($m) }
$ok = ($missing -eq 0 -and $extra -eq 0 -and $mismatch -eq 0 -and $sizeMismatch -eq 0 -and $compared -eq $srcFiles.Count)
$lines.Add(("VERIFY_RECOVERY=" + $(if ($ok) { 'PASS' } else { 'FAIL' })))
$lines | Out-File -LiteralPath $report -Encoding utf8
$lines | ForEach-Object { Write-Output $_ }
if (-not $ok) { exit 1 }
