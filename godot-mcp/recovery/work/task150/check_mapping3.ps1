$ErrorActionPreference = 'Continue'
$repo = 'F:\moonbit-hof-rs-backup\verify-old'
$oldHead = '8f48c938ad9860b292ad9ee59111fb8a77606c37'
$newHead = '4b9bd44054ccfefdb4b96a342a133a4896769b76'
$paths = @(
  'godot-mcp/recovery/work/task148/exe/',
  'godot-mcp/recovery/work/task148/unzip-test/',
  'godot-mcp/recovery/rebuild/work2b/gen-hits.txt',
  'godot-mcp/recovery/rebuild/work2b/gen-strings.txt',
  'godot-mcp/recovery/rebuild/work2b/gen-biglines.txt'
)

$oldList = @(& git -C $repo rev-list --reverse $oldHead)
$newList = @(& git -C $repo rev-list --reverse $newHead)
Write-Output ("OLD_COUNT=$($oldList.Count) NEW_COUNT=$($newList.Count)")
Write-Output "FIRST3_OLD=$($oldList[0..2] -join ',')"
Write-Output "FIRST3_NEW=$($newList[0..2] -join ',')"
Write-Output "LAST2_OLD=$($oldList[-2..-1] -join ',')"
Write-Output "LAST2_NEW=$($newList[-2..-1] -join ',')"

$sameIdx = 0; $differIdx = 0
$iShiftSame = 0; $iShiftDiffer = 0
$anom = 0
for ($i = 0; $i -lt $oldList.Count; $i++) {
  $oT = (git -C $repo rev-parse "$($oldList[$i])^{tree}").Trim()
  $nT = (git -C $repo rev-parse "$($newList[$i])^{tree}").Trim()
  if ($oT -eq $nT) { $sameIdx++ } else { $differIdx++ }
  if ($i -ge 1) {
    $nPrev = (git -C $repo rev-parse "$($newList[$i-1])^{tree}").Trim()
    if ($oT -eq $nPrev) { $iShiftSame++ } else { $iShiftDiffer++ }
  }
}
Write-Output "SAME_INDEX same=$sameIdx differ=$differIdx"
Write-Output "SHIFTED_OLD_i_vs_NEW_i_minus_1 same=$iShiftSame differ=$iShiftDiffer"

# Which commits carry purged paths, in the OLD history?
$carriers = 0
for ($i = 0; $i -lt $oldList.Count; $i++) {
  $had = @(git -C $repo ls-tree -r --name-only $oldList[$i] -- $paths)
  if ($had.Count -gt 0) { $carriers++ }
}
Write-Output "OLD_COMMITS_CARRYING_PURGED_PATHS=$carriers"

# Same in the NEW history
$carriersNew = 0
for ($i = 0; $i -lt $newList.Count; $i++) {
  $had = @(git -C $repo ls-tree -r --name-only $newList[$i] -- $paths)
  if ($had.Count -gt 0) { $carriersNew++ }
}
Write-Output "NEW_COMMITS_CARRYING_PURGED_PATHS=$carriersNew"
