# TASK-154 acceptance: C5 - independent attribution of the pre-existing reds
$eng = 'F:\moonbit-hof-rs\godot-mcp\godot'
$acc = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task154-acc'
$s032rel = 'modules/mcp_server/scripts/mcp032_d3_d4_d6_evidence.ps1'
$s029rel = 'modules/mcp_server/scripts/mcp029_clear_default_evidence.ps1'

Write-Host '=== C5.1: batch hunks do NOT cover the -f crash region (baseline L287-291) ==='
$base032 = @(git -C $eng show "28432f859f:$s032rel")
$head032 = [IO.File]::ReadAllLines((Join-Path $eng $s032rel))
Write-Host ("baseline lines={0} head lines={1}" -f $base032.Count, $head032.Count)
# hunks of the batch diff, in baseline coordinates
$hunks = @(git -C $eng diff -U0 28432f859f..HEAD -- $s032rel | Select-String '^@@' | ForEach-Object { $_.Line })
foreach ($h in $hunks) { Write-Host "  hunk $h" }
$ranges = @()
foreach ($h in $hunks) {
    if ($h -match '@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@') {
        $start = [int]$Matches[1]; $len = if ($Matches[2]) { [int]$Matches[2] } else { 1 }
        $ranges += ,@($start, ($start + [Math]::Max($len,1) - 1))
    }
}
Write-Host 'crash region in baseline coordinates = 287..291 (the `-f` line is 288)'
foreach ($probe in 287..291) {
    $covered = $false
    foreach ($r in $ranges) { if ($probe -ge $r[0] -and $probe -le $r[1]) { $covered = $true } }
    Write-Host ("  baseline L{0} covered by a batch hunk = {1}" -f $probe, $covered)
}
Write-Host '--- byte-equality of the crash region, baseline vs head (offset +61) ---'
foreach ($pair in @(@(285,346),@(286,347),@(287,348),@(288,349),@(289,350),@(290,351),@(291,352))) {
    $b = $base032[$pair[0]-1]; $h = $head032[$pair[1]-1]
    Write-Host ("  base[{0}] -ceq head[{1}] : {2}" -f $pair[0], $pair[1], ($b -ceq $h))
    if (-not ($b -ceq $h)) { Write-Host ("     base: {0}" -f $b); Write-Host ("     head: {0}" -f $h) }
}
Write-Host '--- git blame of the crash line ---'
& git -C $eng blame -L 349,349 --date=short -- $s032rel

Write-Host ''
Write-Host '=== C5.2: every `-f` format string in mcp032 that makes PowerShell throw ==='
$i = 0
$bad = @()
foreach ($line in $head032) {
    $i++
    if ($line -notmatch '\s-f\s') { continue }
    foreach ($m in [regex]::Matches($line, '"((?:[^"]|"")*)"')) {
        $lit = $m.Groups[1].Value
        if ($lit -notmatch '\{') { continue }
        if ($lit -match '\{[0-9]' -and $lit -notmatch '\{(?!\d)') { }
        $threw = $false; $msg = ''
        try { $null = ($lit -f 1,2,3,4,5,6) } catch { $threw = $true; $msg = $_.Exception.Message }
        if ($threw) {
            $bad += [pscustomobject]@{ line = $i; literal = $lit; error = $msg }
            Write-Host ("  L{0} THROWS : {1}" -f $i, $lit)
            Write-Host ("        -> {0}" -f $msg)
        }
    }
}
Write-Host ("total throwing `-f` format literals in mcp032 (HEAD) = {0}" -f $bad.Count)
Write-Host '--- the same scan on the BASELINE version of mcp032 ---'
$n = 0; $badB = 0
foreach ($line in $base032) {
    $n++
    if ($line -notmatch '\s-f\s') { continue }
    foreach ($m in [regex]::Matches($line, '"((?:[^"]|"")*)"')) {
        $lit = $m.Groups[1].Value
        if ($lit -notmatch '\{') { continue }
        $threw = $false
        try { $null = ($lit -f 1,2,3,4,5,6) } catch { $threw = $true }
        if ($threw) { $badB++; Write-Host ("  baseline L{0} THROWS : {1}" -f $n, $lit) }
    }
}
Write-Host ("total throwing `-f` format literals in mcp032 (BASELINE 28432f859f) = {0}" -f $badB)
Write-Host '--- and in mcp029 (both revisions) ---'
$base029 = @(git -C $eng show "28432f859f:$s029rel")
$head029 = [IO.File]::ReadAllLines((Join-Path $eng $s029rel))
foreach ($set in @(@('head', $head029), @('baseline', $base029))) {
    $k = 0
    foreach ($line in $set[1]) {
        $k++
        if ($line -notmatch '\s-f\s') { continue }
        foreach ($m in [regex]::Matches($line, '"((?:[^"]|"")*)"')) {
            $lit = $m.Groups[1].Value
            if ($lit -notmatch '\{') { continue }
            $threw = $false
            try { $null = ($lit -f 1,2,3,4,5,6) } catch { $threw = $true }
            if ($threw) { Write-Host ("  mcp029 {0} L{1} THROWS : {2}" -f $set[0], $k, $lit) }
        }
    }
}
Write-Host '(no line printed above means mcp029 has no such literal)'

Write-Host ''
Write-Host '=== C5.3: did the batch change the red checks expressions? ==='
$diffTxt = @(git -C $eng diff -U0 28432f859f..HEAD -- $s029rel $s032rel)
foreach ($needle in @('wire_clear_default_is_false','wire_description_names_shared_file','d6_live_description_keeps_the_old_wording','d6_live_description_declares_the_shape','wire_clear_description_kept')) {
    $hits = @($diffTxt | Select-String -SimpleMatch $needle)
    Write-Host ("  '{0}' appears in the batch diff {1} time(s)" -f $needle, $hits.Count)
    foreach ($x in $hits) { Write-Host ("      {0}" -f $x.Line) }
}

Write-Host ''
Write-Host '=== C5.4: what the FROZEN contract itself says (unchanged blob) ==='
$art = Join-Path $eng 'modules\mcp_server\docs\tools_list.renamed.json'
$c = ConvertFrom-Json ([IO.File]::ReadAllText($art, [Text.Encoding]::UTF8))
foreach ($pair in @(@('editor_get_test_report','clear'), @('running_game_get_node_properties',''))) {
    $e = @($c.result.tools) | Where-Object { $_.name -eq $pair[0] }
    if ($null -eq $e) { Write-Host ("  {0}: NOT IN CONTRACT" -f $pair[0]); continue }
    Write-Host ("  {0}:" -f $pair[0])
    Write-Host ("     description = '{0}'  (length {1})" -f $e.description, $e.description.Length)
    if ($pair[1]) { Write-Host ("     inputSchema.properties.clear.default = {0}" -f $e.inputSchema.properties.clear.default) }
    if ($pair[0] -eq 'running_game_get_node_properties') {
        Write-Host ("     inputSchema.properties.node_path.description = '{0}'" -f $e.inputSchema.properties.node_path.description)
    }
}
Write-Host '--- git log -S over the contract for the override texts the reds expect ---'
foreach ($needle in @('/root/Main/Actor','user://mcp_test_report.json','clear:true')) {
    $log = @(git -C $eng log --oneline -S $needle -- modules/mcp_server/docs/tools_list.renamed.json)
    Write-Host ("  -S '{0}' -> {1} commit(s) {2}" -f $needle, $log.Count, ($log -join ' | '))
}
Write-Host '--- the exact same facts at the OTHER revisions of the artifact ---'
foreach ($rev in @('28432f859f','HEAD')) {
    $b = @(& git -C $eng show ("{0}:modules/mcp_server/docs/tools_list.renamed.json" -f $rev) -join "`n") | Out-String
    $j = ConvertFrom-Json $b
    $e = @($j.result.tools) | Where-Object { $_.name -eq 'editor_get_test_report' }
    $g = @($j.result.tools) | Where-Object { $_.name -eq 'running_game_get_node_properties' }
    Write-Host ("  {0}: editor_get_test_report.clear.default={1} desc.len={2} ; node_props desc.len={3}" -f $rev, $e.inputSchema.properties.clear.default, $e.description.Length, $g.description.Length)
}

Write-Host ''
Write-Host '=== C5.5: are the two scripts on any gate path? ==='
foreach ($runner in @('F:\moonbit-hof-rs\godot-mcp\tools\run_gates.ps1','F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\scripts\accept_m1.ps1')) {
    $hits = @(Select-String -Path $runner -SimpleMatch 'mcp029_clear_default_evidence','mcp032_d3_d4_d6_evidence')
    Write-Host ("  {0}: {1} hit(s) for the two script names" -f (Split-Path $runner -Leaf), $hits.Count)
}
