$ErrorActionPreference = 'Continue'
$oldClone = 'F:\moonbit-hof-rs-backup\verify-old'
$newClone = 'F:\moonbit-hof-rs-backup\verify-new'
$oldHead = '8f48c938ad9860b292ad9ee59111fb8a77606c37'
$newHead = '4b9bd44054ccfefdb4b96a342a133a4896769b76'
$paths = @(
  'godot-mcp/recovery/work/task148/exe/',
  'godot-mcp/recovery/work/task148/unzip-test/',
  'godot-mcp/recovery/rebuild/work2b/gen-hits.txt',
  'godot-mcp/recovery/rebuild/work2b/gen-strings.txt',
  'godot-mcp/recovery/rebuild/work2b/gen-biglines.txt'
)

$oldList = & git -C $oldClone rev-list --reverse $oldHead
$newList = & git -C $newClone rev-list --reverse $newHead
Write-Output ('OLD_COUNT=' + $oldList.Count + '  NEW_COUNT=' + $newList.Count)

# 1) commit subject lists must be identical (message preservation)
$oldSubj = & git -C $oldClone log --reverse --format='%s' $oldHead
$newSubj = & git -C $newClone log --reverse --format='%s' $newHead
$match = $true
for ($i = 0; $i -lt $oldSubj.Count; $i++) { if ($oldSubj[$i] -ne $newSubj[$i]) { $match = $false; Write-Output ('SUBJECT_MISMATCH at ' + $i) } }
Write-Output ('SUBJECTS_IDENTICAL_OLD_vs_NEW_same_index=' + $match)
Write-Output ('NEW_EXTRA_SUBJECT[last]=' + $newSubj[$newSubj.Count - 1])

# 2) for unchanged-tree commits, none may have had a purged path
$purgeCheck = 0
$bad = @()
for ($i = 0; $i -lt $oldList.Count; $i++) {
  $oT = (& git -C $oldClone rev-parse "$($oldList[$i])^{tree}").Trim()
  $nT = (& git -C $newClone rev-parse "$($newList[$i])^{tree}").Trim()
  if ($oT -eq $nT) {
    # tree unchanged -> filter must have found nothing to remove here
    $had = & git -C $oldClone ls-tree -r --name-only $oldList[$i] -- $paths
    if (@($had).Count -gt 0) { $bad += ('index ' + $i + ' tree-same but had ' + @($had).Count + ' purged paths') }
  } else {
    $stillThere = & git -C $newClone ls-tree -r --name-only $newList[$i] -- $paths
    if (@($stillThere).Count -gt 0) { $bad += ('index ' + $i + ' tree-diff but still has ' + @($stillThere).Count + ' purged paths') }
    $purgeCheck++
  }
}
Write-Output ('COMMITS_WITH_CHANGED_TREE=' + $purgeCheck)
Write-Output ('COMMITS_WITH_UNCHANGED_TREE=' + ($oldList.Count - $purgeCheck))
Write-Output ('ANOMALIES=' + $bad.Count)
$bad | Select-Object -First 20 | ForEach-Object { $_ }

# 3) d-i: old vs new shifted by one must be tree-identical
$same = 0; $diff = 0
for ($i = 0; $i -lt $oldList.Count; $i++) {
  $oT2 = (& git -C $oldClone rev-parse "$($oldList[$i])^{tree}").Trim()
  $nT2 = (& git -C $newClone rev-parse "$($newList[$i + 1])^{tree}").Trim()
  if ($oT2 -eq $nT2) { $same++ } else { $diff++ }
}
Write-Output ('SHIFTED_TREE_IDENTICAL same=' + $same + ' differ=' + $diff)
