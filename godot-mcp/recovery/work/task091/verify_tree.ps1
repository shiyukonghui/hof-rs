param(
  [Parameter(Mandatory=$true)][string]$Src,
  [Parameter(Mandatory=$true)][string]$Dst,
  [Parameter(Mandatory=$true)][string]$Label,
  [string]$OutDir = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task091\logs'
)

$ErrorActionPreference = 'Stop'
$srcRoot = (Resolve-Path -LiteralPath $Src).Path.TrimEnd('\')
$dstRoot = (Resolve-Path -LiteralPath $Dst).Path.TrimEnd('\')

Write-Output ("### VERIFY {0}" -f $Label)
Write-Output ("SRC={0}" -f $srcRoot)
Write-Output ("DST={0}" -f $dstRoot)

$sha = [System.Security.Cryptography.SHA256]::Create()

function Get-FileShaHex([string]$full) {
  $fs = [System.IO.File]::Open(('\\?\' + $full), [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
  try { $h = $sha.ComputeHash($fs) } finally { $fs.Dispose() }
  return ([System.BitConverter]::ToString($h)).Replace('-', '')
}

$srcRel = New-Object 'System.Collections.Generic.List[string]'
$srcLen = New-Object 'System.Collections.Generic.Dictionary[string,long]'
$pre = $srcRoot.Length + 1
foreach ($f in [System.IO.Directory]::EnumerateFiles($srcRoot, '*', 'AllDirectories')) {
  $r = $f.Substring($pre)
  $srcRel.Add($r)
  $srcLen[$r] = ([System.IO.FileInfo]::new(('\\?\' + $f))).Length
}
$dstRel = New-Object 'System.Collections.Generic.List[string]'
$dstLen = New-Object 'System.Collections.Generic.Dictionary[string,long]'
$pre2 = $dstRoot.Length + 1
foreach ($f in [System.IO.Directory]::EnumerateFiles($dstRoot, '*', 'AllDirectories')) {
  $r = $f.Substring($pre2)
  $dstRel.Add($r)
  $dstLen[$r] = ([System.IO.FileInfo]::new(('\\?\' + $f))).Length
}

$dstSet = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($r in $dstRel) { [void]$dstSet.Add($r) }
$srcSet = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($r in $srcRel) { [void]$srcSet.Add($r) }

Write-Output ("src_files={0}" -f $srcRel.Count)
Write-Output ("dst_files={0}" -f $dstRel.Count)

$missing = New-Object 'System.Collections.Generic.List[string]'
foreach ($r in $srcRel) { if (-not $dstSet.Contains($r)) { $missing.Add($r) } }
$extra = New-Object 'System.Collections.Generic.List[string]'
foreach ($r in $dstRel) { if (-not $srcSet.Contains($r)) { $extra.Add($r) } }
Write-Output ("missing_in_dst={0}" -f $missing.Count)
Write-Output ("extra_in_dst={0}" -f $extra.Count)

$mismatches = New-Object 'System.Collections.Generic.List[object]'
$compared = 0
$totalSrc = 0L
$totalDst = 0L
$i = 0
foreach ($r in $srcRel) {
  $i++
  $sl = $srcLen[$r]
  $totalSrc += $sl
  if (-not $dstSet.Contains($r)) { continue }
  $dl = $dstLen[$r]
  $compared++
  if ($sl -ne $dl) {
    $mismatches.Add([pscustomobject]@{ rel = $r; reason = 'size'; src_len = $sl; dst_len = $dl; src_sha = ''; dst_sha = '' })
    continue
  }
  $s1 = Get-FileShaHex (Join-Path $srcRoot $r)
  $s2 = Get-FileShaHex (Join-Path $dstRoot $r)
  if ($s1 -ne $s2) {
    $mismatches.Add([pscustomobject]@{ rel = $r; reason = 'sha'; src_len = $sl; dst_len = $dl; src_sha = $s1; dst_sha = $s2 })
  }
  if (($i % 2000) -eq 0) { Write-Output ("  progress {0}/{1} mismatches={2}" -f $i, $srcRel.Count, $mismatches.Count) }
}
$totalDst = $dstLen.Values | Measure-Object -Sum | Select-Object -ExpandProperty Sum

Write-Output ("compared={0}" -f $compared)
Write-Output ("mismatched={0}" -f $mismatches.Count)
if ($mismatches.Count -gt 0) {
  Write-Output '--- MISMATCHES ---'
  $mismatches | ForEach-Object { Write-Output ("{0} | {1} | src={2}/{3} dst={4}/{5}" -f $_.rel, $_.reason, $_.src_len, $_.src_sha, $_.dst_len, $_.dst_sha) }
}
if ($missing.Count -gt 0) { Write-Output '--- MISSING ---'; $missing | ForEach-Object { Write-Output $_ } }
if ($extra.Count -gt 0) { Write-Output '--- EXTRA ---'; $extra | ForEach-Object { Write-Output $_ } }

Write-Output ("src_total_bytes={0}" -f $totalSrc)
Write-Output ("dst_total_bytes={0}" -f $totalDst)

$verdict = if (($mismatches.Count -eq 0) -and ($missing.Count -eq 0) -and ($extra.Count -eq 0) -and ($totalSrc -eq $totalDst)) { 'PASS' } else { 'FAIL' }
Write-Output ("VERIFY_{0}={1}" -f $Label, $verdict)

$summary = [pscustomobject]@{
  label = $Label
  src = $srcRoot
  dst = $dstRoot
  src_files = $srcRel.Count
  dst_files = $dstRel.Count
  missing = $missing.Count
  extra = $extra.Count
  compared = $compared
  mismatched = $mismatches.Count
  src_total_bytes = $totalSrc
  dst_total_bytes = $totalDst
  verdict = $verdict
  mismatches = $mismatches
  missing_list = @($missing)
  extra_list = @($extra)
}
$jsonPath = Join-Path $OutDir ("verify_{0}.json" -f $Label)
[System.IO.File]::WriteAllText($jsonPath, ($summary | ConvertTo-Json -Depth 6), (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("json={0}" -f $jsonPath)
if ($verdict -ne 'PASS') { exit 1 } else { exit 0 }
