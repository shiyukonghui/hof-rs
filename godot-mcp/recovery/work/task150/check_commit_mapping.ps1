$ErrorActionPreference = 'Continue'

function Get-Commits($repo, $rev) {
  $lines = & git -C $repo rev-list --reverse $rev
  $out = @()
  foreach ($c in $lines) {
    $t = (& git -C $repo rev-parse "$c^{tree}").Trim()
    $out += [pscustomobject]@{ commit = $c; tree = $t }
  }
  return $out
}

$old = Get-Commits 'F:\moonbit-hof-rs-backup\verify-old' '8f48c938ad9860b292ad9ee59111fb8a77606c37'
$new = Get-Commits 'F:\moonbit-hof-rs-backup\verify-new' '4b9bd44054ccfefdb4b96a342a133a4896769b76'
$newParent = Get-Commits 'F:\moonbit-hof-rs-backup\verify-old' '4b9bd44054ccfefdb4b96a342a133a4896769b76~1'

Write-Output ('OLD_COMMITS=' + $old.Count)
Write-Output ('NEW_COMMITS=' + $new.Count)
Write-Output ('NEW_MINUS_ONE_COMMITS=' + $newParent.Count)

Write-Output '--- per-commit tree comparison: OLD[i] vs NEW[i] (expect DIFFER, i.e. every rewritten commit changed because the purge touched every commit) ---'
$same = 0; $diff = 0
for ($i = 0; $i -lt $old.Count; $i++) {
  if ($old[$i].tree -eq $new[$i].tree) { $same++ } else { $diff++ }
}
Write-Output ('OLD_TREE_EQUALS_NEW_TREE: same=' + $same + ' differ=' + $diff)

Write-Output '--- per-commit tree comparison: OLD[i] vs NEW[i+1] (penultimate lineage; expect identical) ---'
$same2 = 0; $diff2 = 0
$firstDiff = $null
for ($i = 0; $i -lt $old.Count; $i++) {
  if ($old[$i].tree -eq $new[$i + 1].tree) { $same2++ } else { $diff2++; if (-not $firstDiff) { $firstDiff = $i } }
}
Write-Output ('OLD_TREE_EQUALS_NEW_SHIFTED: same=' + $same2 + ' differ=' + $diff2)
if ($firstDiff) { Write-Output ('first differing index=' + $firstDiff) }
