# TASK-154 acceptance: C6 - the two false-green traps, reproduced
$hof = 'F:\moonbit-hof-rs'
$acc = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task154-acc'
$rel = 'tests/fixtures/mcp/tools_list.json'
$t = Join-Path $acc 'c6trap'
New-Item -ItemType Directory -Force -Path $t | Out-Null

function Report([string]$label, [string]$file) {
    $b = [IO.File]::ReadAllBytes($file)
    $sha = (Get-FileHash -Algorithm SHA256 -Path $file).Hash.ToLower()
    $txt = [Text.Encoding]::UTF8.GetString($b)
    $tools = ([regex]::Matches($txt, '"name"\s*:')).Count
    Write-Host ("{0}: bytes={1} 'name' occurrences={2} sha256={3}" -f $label, $b.Length, $tools, $sha)
}

Write-Host '================ TRAP 1: cmd eats the ^ in db2eed7^:path ================'
Write-Host '--- rev-parse (PowerShell, ^ is not special here) ---'
$parent = (& git -C $hof rev-parse 'db2eed7^') -join ''
$trueBlob = (& git -C $hof rev-parse 'db2eed7^:tests/fixtures/mcp/tools_list.json') -join ''
$headBlob = (& git -C $hof rev-parse ('HEAD:' + $rel)) -join ''
$ownBlob  = (& git -C $hof rev-parse ('db2eed7:' + $rel)) -join ''
Write-Host ("db2eed7            = {0}" -f ((& git -C $hof rev-parse db2eed7) -join ''))
Write-Host ("db2eed7^ (parent)  = {0}" -f $parent)
Write-Host ("db2eed7^:path blob = {0}  <-- the blob the script INTENDED" -f $trueBlob)
Write-Host ("db2eed7:path  blob = {0}  <-- what cmd's caret-eating turns it into" -f $ownBlob)
Write-Host ("HEAD:path     blob = {0}" -f $headBlob)

Write-Host '--- 1a. the TRAP: cmd /c with the unquoted caret ---'
cmd /c "git -C $hof cat-file blob db2eed7^:$rel > `"$t\trap1_cmd_caret.out`""
Write-Host ("cmd line actually handed to git (echo): ")
cmd /c "echo git -C $hof cat-file blob db2eed7^:$rel"
Report '1a cmd /c db2eed7^:path  ' (Join-Path $t 'trap1_cmd_caret.out')

Write-Host '--- 1b. correct reading A: the known blob id, bytes straight from git ---'
cmd /c "git -C $hof cat-file blob $trueBlob > `"$t\trap1_correct_blob.out`""
Report '1b cat-file blob <db2eed7^:path>' (Join-Path $t 'trap1_correct_blob.out')

Write-Host '--- 1c. correct reading B: db2eed7^:path via .NET Process + BaseStream (never through a shell/PowerShell text pipeline) ---'
$psi = New-Object Diagnostics.ProcessStartInfo
$psi.FileName = 'git'
$psi.Arguments = ('-C "' + $hof + '" cat-file blob "db2eed7^:' + $rel + '"')
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$p = [Diagnostics.Process]::Start($psi)
$fs = [IO.File]::Create((Join-Path $t 'trap1_correct_baseStream.out'))
$p.StandardOutput.BaseStream.CopyTo($fs)
$fs.Close()
$p.WaitForExit()
Report '1c Process+BaseStream     ' (Join-Path $t 'trap1_correct_baseStream.out')

Write-Host '--- 1d. what the worktree file and HEAD:path are (the 177-tool capture) ---'
Report '1d worktree file          ' (Join-Path $hof $rel)

Write-Host '--- 1e. is HEAD:path the same blob as db2eed7:path? ---'
Write-Host ("HEAD:path == db2eed7:path  -> {0}" -f ($headBlob -eq $ownBlob))
Write-Host ("HEAD:path == db2eed7^:path -> {0}" -f ($headBlob -eq $trueBlob))

Write-Host ''
Write-Host '================ TRAP 2: git diff does not error on a nonexistent pathspec ================'
function DiffLines([string]$cwd, [string]$pathspec) {
    $out = @(& git -C $cwd diff --name-only -- $pathspec)
    $code = $LASTEXITCODE
    return [pscustomobject]@{ repo = $cwd; pathspec = $pathspec; lines = @($out).Count; names = ($out -join ','); exit = $code }
}
$rows = @()
$rows += DiffLines $hof 'tools/run_gates.ps1'
$rows += DiffLines $hof 'godot-mcp/tools/run_gates.ps1'
$rows += DiffLines $hof 'definitely-not-a-file.txt'
$rows += DiffLines $hof 'godot-mcp/definitely-not-a-file.txt'
$rows | Format-Table -AutoSize | Out-String -Width 160 | ForEach-Object { Write-Host $_ }
Write-Host '--- the same pathspecs through ls-files (which DOES prove a match) ---'
foreach ($ps_ in @('tools/run_gates.ps1','godot-mcp/tools/run_gates.ps1','definitely-not-a-file.txt')) {
    $l = @(& git -C $hof ls-files -- $ps_)
    Write-Host ("  ls-files -- {0,-32} -> {1} line(s) [{2}]" -f $ps_, $l.Count, ($l -join ','))
}
Write-Host '--- diff without --name-only on the wrong pathspec: still silent? ---'
& git -C $hof diff --stat -- tools/run_gates.ps1
Write-Host ("  exit={0}" -f $LASTEXITCODE)
Write-Host '--- git diff pathspec that matches nothing INSIDE the engine repo, exit code ---'
& git -C (Join-Path $hof 'godot-mcp\godot') diff --name-only -- modules/mcp_server/scripts/does_not_exist.ps1
Write-Host ("  exit={0}  (git only errors when a pathspec matches NOTHING *and* is given with --error-unmatch/--exit-code semantics)" -f $LASTEXITCODE)
Write-Host '--- proof that --exit-code does catch a real diff but not an empty pathspec ---'
& git -C (Join-Path $hof 'godot-mcp\godot') diff --quiet --exit-code 28432f859f..HEAD -- modules/mcp_server/scripts/does_not_exist.ps1
Write-Host ("  nonexistent pathspec with --exit-code -> exit={0}" -f $LASTEXITCODE)
& git -C (Join-Path $hof 'godot-mcp\godot') diff --quiet --exit-code 28432f859f..HEAD -- modules/mcp_server/scripts/mcp029_clear_default_evidence.ps1
Write-Host ("  real changed pathspec with --exit-code -> exit={0}" -f $LASTEXITCODE)
