$ErrorActionPreference = 'Continue'
$Engine = 'F:\moonbit-hof-rs\godot-mcp\godot'
# The OUTER repository root is F:\moonbit-hof-rs (its worktree contains `godot-mcp\`),
# so the gate runner's repo-relative path is `godot-mcp/tools/run_gates.ps1`.
# Passing `tools/run_gates.ps1` to `git -C F:\moonbit-hof-rs` silently matches
# nothing - a pathspec that does not exist is not an error for `git diff`.
$Outer = 'F:\moonbit-hof-rs'
$OuterRunnerRel = 'godot-mcp/tools/run_gates.ps1'
$Hof = 'F:\moonbit-hof-rs'

function Say($t) { Write-Output $t }

Say '############################################################'
Say '# TASK-154 final self-checks (real output, no paraphrase)'
Say '############################################################'

Say ''
Say '=== 1. engine repo state ==='
Say ('HEAD   = ' + (& git -C $Engine rev-parse HEAD))
Say ('branch = ' + (& git -C $Engine rev-parse --abbrev-ref HEAD))
$porcelain = @(& git -C $Engine status --porcelain)
Say ('git status --porcelain lines = ' + $porcelain.Count + '  (0 = clean)')
$porcelain | ForEach-Object { Say ('   ' + $_) }
Say 'the three TASK-154 commits:'
foreach ($sha in @('56f93ca180', '627aeacee4', 'bdf654b108')) {
    $full = & git -C $Engine rev-parse $sha
    $when = & git -C $Engine log -1 --format=%cd --date=iso $sha
    $subj = & git -C $Engine log -1 --format=%s $sha
    Say ('   ' + $full + '  ' + $when + '  ' + $subj)
}
$remoteRefs = @(& git -C $Engine for-each-ref --format='%(refname)' refs/remotes)
Say ('remote-tracking refs in the engine repo = ' + $remoteRefs.Count + '  (0 => no remote configured => nothing could have been pushed)')
$remoteRefs | ForEach-Object { Say ('   ' + $_) }

Say ''
Say '=== 2. forbidden literals in the two edited scripts ==='
foreach ($rel in @('modules/mcp_server/scripts/mcp029_clear_default_evidence.ps1', 'modules/mcp_server/scripts/mcp032_d3_d4_d6_evidence.ps1')) {
    $path = Join-Path $Engine ($rel -replace '/', '\')
    Say ('--- ' + $rel)
    $all = [IO.File]::ReadAllLines($path, [Text.Encoding]::UTF8)
    $n = 0
    $hof = 0; $hofCode = 0; $port = 0; $portCode = 0
    foreach ($line in $all) {
        $n++
        $isComment = ([string]$line).TrimStart().StartsWith('#')
        if ($line -like '*moonbit-hof-rs*') {
            $hof++
            if (-not $isComment) { $hofCode++ }
            Say ('    L' + $n + ' moonbit-hof-rs isComment=' + $isComment + ' : ' + $line.Trim())
        }
        if ($line -like '*9877*') {
            $port++
            if (-not $isComment) { $portCode++ }
            Say ('    L' + $n + ' 9877 isComment=' + $isComment + ' : ' + $line.Trim())
        }
    }
    Say ('    totals: moonbit-hof-rs=' + $hof + ' (non-comment ' + $hofCode + ') ; 9877=' + $port + ' (non-comment ' + $portCode + ')')
    $bytes = [IO.File]::ReadAllBytes($path)
    $nonAscii = 0
    foreach ($b in $bytes) { if ($b -gt 0x7F) { $nonAscii++ } }
    Say ('    bytes=' + $bytes.Length + '  BOM=' + ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) + '  non-ASCII bytes=' + $nonAscii)
}

Say ''
Say '=== 3. frozen artifacts: worktree blob vs HEAD blob ==='
foreach ($row in @(
        @{ repo = $Engine; rel = 'modules/mcp_server/docs/tools_list.renamed.json'; label = 'tools_list.renamed.json (engine)' },
        @{ repo = $Engine; rel = 'modules/mcp_server/docs/rename-baseline-tools-list.json'; label = 'rename-baseline-tools-list.json (engine)' },
        @{ repo = $Outer; rel = $OuterRunnerRel; label = 'godot-mcp/tools/run_gates.ps1 (OUTER repo F:\moonbit-hof-rs)' },
        @{ repo = $Engine; rel = 'modules/mcp_server/scripts/check_engine_anchor.ps1'; label = 'check_engine_anchor.ps1 (engine)' },
        @{ repo = $Engine; rel = 'modules/mcp_server/scripts/check_hardcoded_counts.py'; label = 'check_hardcoded_counts.py (engine)' })) {
    $p = Join-Path $row.repo ($row.rel -replace '/', '\')
    $size = (Get-Item $p).Length
    $sha = (Get-FileHash -Algorithm SHA256 $p).Hash.ToLower()
    $wt = & git -C $row.repo hash-object -- $row.rel
    $head = & git -C $row.repo rev-parse ('HEAD:' + $row.rel)
    Say ($row.label)
    Say ('    bytes=' + $size + ' sha256=' + $sha)
    Say ('    worktree blobs=' + $wt + '  HEAD blob=' + $head + '  IDENTICAL=' + ($wt -ceq $head))
}

Say ''
Say '=== 4. hof-rs side untouched (except the sanctioned evidence directory) ==='
$hofHead = & git -C 'F:\moonbit-hof-rs' log -1 --format=%h
Say ('hof-rs HEAD = ' + $hofHead)
$hofStatus = @(& git -C 'F:\moonbit-hof-rs' status --porcelain)
Say ('hof-rs git status --porcelain lines = ' + $hofStatus.Count + '  (0 = clean)')
$hofStatus | ForEach-Object { Say ('   ' + $_) }
Say 'hof-rs last 3 commits:'
foreach ($l in @(& git -C 'F:\moonbit-hof-rs' log -3 --format='%h %cd %s' --date=short)) { Say ('   ' + $l) }
$fx = 'F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json'
Say ('the forbidden fixture path: exists=' + (Test-Path $fx) + ' bytes=' + (Get-Item $fx).Length + ' sha256=' + (Get-FileHash -Algorithm SHA256 $fx).Hash.ToLower())

Say ''
Say '=== 5. guardrail 3 evidence (dot-sources the anchor judge; runs last on purpose) ==='
. (Join-Path $Engine 'modules\mcp_server\scripts\check_engine_anchor.ps1')
$v = Get-McpEngineAnchorVerdict -VersionText '4.8.dev.mono.custom_build.035edfce7' -RepoRoot $Engine
Say ('g09 judgement: verdict=' + $v.Verdict + ' anchor=' + $v.Anchor + ' head=' + $v.Head + ' red_count=' + $v.RedCount + ' ok=' + $v.Ok)
foreach ($rel in @('modules/mcp_server/scripts/check_engine_anchor.ps1', 'modules/mcp_server/scripts/check_hardcoded_counts.py')) {
    $d = @(& git -C $Engine diff --name-only --no-renames ($v.Anchor + '..' + $v.Head) -- $rel)
    Say ('    git -C <engine> diff --name-only ' + $v.Anchor + '..' + $v.Head + ' -- ' + $rel + ' => ' + $d.Count + ' line(s) [' + ($d -join ', ') + ']')
}
$d2 = @(& git -C $Outer diff --name-only -- $OuterRunnerRel)
Say ('    git -C <outer F:\moonbit-hof-rs> diff --name-only -- ' + $OuterRunnerRel + ' => ' + $d2.Count + ' line(s) [' + ($d2 -join ', ') + ']')
$outerHeadBlob = & git -C $Outer rev-parse ('HEAD:' + $OuterRunnerRel)
$outerWtBlob = & git -C $Outer hash-object -- $OuterRunnerRel
Say ('    outer runner blob: worktree=' + $outerWtBlob + ' HEAD=' + $outerHeadBlob + ' IDENTICAL=' + ($outerWtBlob -ceq $outerHeadBlob))

Say ''
Say '=== 6. ports 9870..9889 listener state at the end ==='
$net = @(& netstat -ano -p TCP)
$hits = @($net | Where-Object { $_ -match 'LISTENING' -and $_ -match ':(98[7-8][0-9])\s' })
Say ('LISTENING rows in 9870..9889 = ' + $hits.Count)
$hits | ForEach-Object { Say ('   ' + $_.Trim()) }
Say 'DONE'
