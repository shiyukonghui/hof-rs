# TASK-154 acceptance: C3 frozen artifact + C7 g09 guardrail-3 pathspec validity
$eng = 'F:\moonbit-hof-rs\godot-mcp\godot'
$outer = 'F:\moonbit-hof-rs'
$acc = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task154-acc'

Write-Host '=== C3a: frozen contract artifact sha256 / bytes / blob ==='
$art = Join-Path $eng 'modules\mcp_server\docs\tools_list.renamed.json'
$b = [IO.File]::ReadAllBytes($art)
$sha = (Get-FileHash -Algorithm SHA256 -Path $art).Hash.ToLower()
$blobW = (& git -C $eng hash-object -- $art) -join ''
$blobH = (& git -C $eng rev-parse 'HEAD:modules/mcp_server/docs/tools_list.renamed.json') -join ''
$blobB = (& git -C $eng rev-parse '28432f859f:modules/mcp_server/docs/tools_list.renamed.json') -join ''
Write-Host ("bytes        = {0}" -f $b.Length)
Write-Host ("sha256       = {0}" -f $sha)
Write-Host ("worktree blob= {0}" -f $blobW)
Write-Host ("HEAD blob    = {0}" -f $blobH)
Write-Host ("28432f859f   = {0}" -f $blobB)
Write-Host ("all identical= {0}" -f (($blobW -eq $blobH) -and ($blobH -eq $blobB)))

Write-Host ''
Write-Host '=== C3b: is the artifact touched anywhere in 28432f859f..HEAD? ==='
$cnt = @(& git -C $eng diff --name-only 28432f859f..HEAD -- modules/mcp_server/docs/tools_list.renamed.json).Count
Write-Host ("diff --name-only lines = {0}" -f $cnt)
Write-Host '--- the actual batch diffstat ---'
& git -C $eng diff --stat 28432f859f..HEAD

Write-Host ''
Write-Host '=== C7a: pathspec validity proof for the three guardrail-3 files ==='
Write-Host '--- 1) engine-relative pathspecs: name the files back (proves they MATCH) ---'
foreach ($rel in @('modules/mcp_server/scripts/check_engine_anchor.ps1','modules/mcp_server/scripts/check_hardcoded_counts.py')) {
    $lines = @(& git -C $eng ls-files -- $rel)
    Write-Host ("  ls-files '{0}' -> {1} line(s): {2}" -f $rel, $lines.Count, ($lines -join ','))
    $d = @(& git -C $eng diff --name-only 035edfce7..HEAD -- $rel)
    Write-Host ("  diff 035edfce7..HEAD -- {0} -> {1} line(s) [{2}]" -f $rel, $d.Count, ($d -join ','))
}
Write-Host '--- 2) outer-repo runner: the WRONG pathspec (silent no-match) vs the RIGHT one ---'
$wrong = @(& git -C $outer diff --name-only -- tools/run_gates.ps1)
Write-Host ("  git -C {0} diff --name-only -- tools/run_gates.ps1            -> {1} line(s) [{2}]  (exit={3})" -f $outer, $wrong.Count, ($wrong -join ','), $LASTEXITCODE)
$right = @(& git -C $outer diff --name-only -- godot-mcp/tools/run_gates.ps1)
Write-Host ("  git -C {0} diff --name-only -- godot-mcp/tools/run_gates.ps1  -> {1} line(s) [{2}]  (exit={3})" -f $outer, $right.Count, ($right -join ','), $LASTEXITCODE)
$lsf = @(& git -C $outer ls-files -- godot-mcp/tools/run_gates.ps1)
Write-Host ("  git -C {0} ls-files -- godot-mcp/tools/run_gates.ps1          -> {1} line(s): {2}" -f $outer, $lsf.Count, ($lsf -join ','))
$lsfWrong = @(& git -C $outer ls-files -- tools/run_gates.ps1)
Write-Host ("  git -C {0} ls-files -- tools/run_gates.ps1                    -> {1} line(s): {2}" -f $outer, $lsfWrong.Count, ($lsfWrong -join ','))
$blobR = (& git -C $outer hash-object -- godot-mcp/tools/run_gates.ps1) -join ''
$headR = (& git -C $outer rev-parse 'HEAD:godot-mcp/tools/run_gates.ps1') -join ''
Write-Host ("  runner blob worktree={0} HEAD={1} identical={2}" -f $blobR, $headR, ($blobR -eq $headR))

Write-Host ''
Write-Host '=== C7b: guardrail-3 proof with a MATCHING pathspec (four ways) ==='
foreach ($rel in @('modules/mcp_server/scripts/check_engine_anchor.ps1','modules/mcp_server/scripts/check_hardcoded_counts.py')) {
    $w = (& git -C $eng hash-object -- (Join-Path $eng $rel)) -join ''
    $h = (& git -C $eng rev-parse ("HEAD:" + $rel)) -join ''
    $hB = (& git -C $eng rev-parse ("28432f859f:" + $rel)) -join ''
    $d = @(& git -C $eng diff --name-only 035edfce7..HEAD -- $rel).Count
    Write-Host ("  {0}: worktree==HEAD==baseline = {1} (blob {2}); diff 035edfce7..HEAD lines={3}" -f $rel, (($w -eq $h) -and ($h -eq $hB)), $w, $d)
}
Write-Host ("  outer godot-mcp/tools/run_gates.ps1: worktree==HEAD = {0} (blob {1})" -f ($blobR -eq $headR), $blobR)
