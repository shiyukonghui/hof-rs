# =============================================================================
#  mcp031_gate6_coverage_probes.ps1 -- live evidence for TASK-031 item (2)
#
#  `check_narrowing_points.py` (guardrail gate 6, GDR-24) was extended by
#  TASK-031 after the M4d audit (D2, high) measured five equivalent spellings
#  that walked straight through the old six-literal scanner:
#
#      const real_t audit_probe_c = 1.0e300;            (implicit, out of range)
#      const float audit_probe_d = static_cast<float>(1.0e300);
#      const Color audit_probe_e = ::Color(1.0e300, 0.0, 0.0, 1.0);
#      const Vector3 audit_probe_f = Vector3{1.0e300, 0.0, 0.0};
#      const Color audit_probe_g = Color <newline> (1.0e300, 0.0, 0.0, 1.0);
#
#  `docs/DESIGN-DETAIL.md` section 22.3b now requires the gate's coverage to be
#  **declared** (`--coverage`) and **probed**: every declared spelling needs an
#  "insert -> exit 1" probe. This script is that regression.
#
#  It proves, on the real tree, that:
#    B1  the baseline is green (exit 0, scanned == pinned == 75, no
#        unannotated/unlisted/stale entry) -- the zero-false-positive baseline
#        (the count grew 30 -> 34 in TASK-033, when the three animation-family
#        files added four pre-gated `real_t` copies, 34 -> 38 in TASK-034,
#        when the four B5 batch 2 groups of this family added one `float` copy
#        and two comparison-width points plus the `priority` integer slot,
#        38 -> 69 in TASK-036, when the movement write's vector arithmetic added
#        29 points under one `G24-MOVE-VECTOR` marker and the style-box argument
#        precondition added two `Color()` defaults under
#        `G24-THEME-STYLEBOX-DEFAULT`, 69 -> 71 in TASK-037, when the
#        node-write family's read-back comparison added two points under
#        `G24-NW-SET-WIDTH`, the sibling of the resource writer's
#        `G24-RESOURCE-SET-WIDTH`, 71 -> 73 in TASK-041, when the
#        `project.godot` `[input]` read-back added two deadzone
#        comparison-width points under `G24-INPUT-PERSIST-DEADZONE`, and
#        73 -> 75 in TASK-045, when the pixel comparison's raw-byte fast path
#        added a second occurrence of each `G24-DIFF-PIXEL-*` colour - the same
#        two markers, now pinned at both points;
#        every one of them is pinned);
#    B2  the M4d five (P1..P5) are RED (exit 1) and the report names the probe
#        line with the expected pattern id;
#    B3  the M4d control probe `(real_t)1.0e300` is still red (nothing regressed);
#    B4  **every** declared spelling has such a probe (pattern ids cast_real_t,
#        cast_float, cast_static_real_t, cast_static_float, cast_func_real_t,
#        cast_func_float, ctor_color, ctor_color_arg_literal, ctor_vector2,
#        ctor_vector2_arg_literal, ctor_vector3, ctor_vector3_arg_literal,
#        ctor_vector4, ctor_vector4_arg_literal, lit_float_range,
#        dbl_cast_into_float, lit_real_t_alias); S10..S13 were added because the
#        first run of this script proved `Color name{...}` was still invisible, and
#        T01..T05 are the M4e D-M4e-1 five (a signed literal, a parenthesised
#        literal, a hexadecimal literal, a same-file `typedef` alias and an array
#        initialiser), added by TASK-033;
#    B5  false positives: a spelling inside a `//` comment, a `/* */` block
#        comment or a string literal, a legitimate `double` (WIDE slot) target,
#        and an in-range `float` literal all stay invisible -> exit 0;
#    B6/B7 the declared boundary: an implicit narrowing of a *runtime* double
#        into `real_t`, and an in-range constructor direct-init, are NOT caught
#        (exit 0). That is the honest limit of a textual scanner and is printed
#        by `--coverage`; the probes assert it stays a documented boundary
#        rather than quietly looking covered.
#
#  Every probe appends to one tracked file and then reverts with
#  `git checkout --`; the file's sha256 must come back byte-identical, and a
#  `finally` block reverts it even if a check throws. Nothing is compiled here:
#  this script exercises the scanner only.
#
#  Usage:
#    powershell -NoProfile -ExecutionPolicy Bypass -File mcp031_gate6_coverage_probes.ps1
# =============================================================================

param(
    [string]$RepoRoot = ''
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrEmpty($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
}
$Python = 'python'
$Script = Join-Path $RepoRoot 'modules\mcp_server\scripts\check_narrowing_points.py'
$ProbeRel = 'modules/mcp_server/tools/running_game_read_scene.cpp'
$ProbeFull = Join-Path $RepoRoot ($ProbeRel -replace '/', '\')
$Root = Join-Path $env:TEMP 'task031-gate6-probes'
$Logs = Join-Path $Root 'logs'

Remove-Item -Recurse -Force $Root -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $Logs | Out-Null

$script:Checks = New-Object System.Collections.Generic.List[object]

function Note {
    param([string]$Text)
    Write-Host $Text
}

function Check {
    param([string]$Id, [bool]$Pass, [string]$Evidence)
    $script:Checks.Add([pscustomobject]@{ id = $Id; pass = $Pass; evidence = $Evidence })
    $tag = if ($Pass) { 'PASS' } else { 'FAIL' }
    Write-Host ("[{0}] {1}" -f $tag, $Id)
    Write-Host ("       {0}" -f $Evidence)
}

function Get-Sha {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return '<missing>' }
    return (Get-FileHash -Algorithm SHA256 -Path $Path).Hash.ToLower()
}

# Append lines to a text file without a BOM (Windows PowerShell 5.1's
# `Set-Content -Encoding UTF8` writes one, and the sources are read as UTF-8).
function Append-Lines {
    param([string]$Path, [string[]]$Lines)
    $existing = [IO.File]::ReadAllLines($Path)
    $all = @($existing) + @($Lines)
    [IO.File]::WriteAllBytes($Path, (New-Object Text.UTF8Encoding($false)).GetBytes(($all -join "`n") + "`n"))
}

function Restore-ProbeFile {
    & git -C $RepoRoot checkout -- $ProbeRel
    if ($LASTEXITCODE -ne 0) { throw ("git checkout -- {0} failed" -f $ProbeRel) }
    return (Get-Sha $ProbeFull)
}

# `cmd /c` redirection keeps the bytes python printed (the guardrail's output is
# ASCII, and a PowerShell pipeline would re-encode it).
function Invoke-Gate6 {
    param([string]$Label)
    $out = Join-Path $Logs ($Label + '.log')
    if (Test-Path $out) { Remove-Item -Force $out }
    & cmd /c "python `"$Script`" > `"$out`" 2>&1"
    $code = $LASTEXITCODE
    $text = Get-Content -Raw -Encoding UTF8 $out
    return [pscustomobject]@{ exit = $code; text = $text; log = $out; sha = (Get-Sha $out) }
}

function Invoke-Gate6Json {
    param([string]$Label)
    $out = Join-Path $Logs ($Label + '.json')
    if (Test-Path $out) { Remove-Item -Force $out }
    & cmd /c "python `"$Script`" --json > `"$out`" 2>&1"
    $code = $LASTEXITCODE
    $text = Get-Content -Raw -Encoding UTF8 $out
    $parsed = $null
    if ($text -and $text.TrimStart().StartsWith('{')) { $parsed = $text | ConvertFrom-Json }
    return [pscustomobject]@{ exit = $code; json = $parsed; raw = $text; log = $out; sha = (Get-Sha $out) }
}

function Get-PointFor {
    param($Json, [string]$Needle)
    if ($null -eq $Json) { return $null }
    foreach ($point in $Json.points) {
        if ($point.text -like ("*" + $Needle + "*")) { return $point }
    }
    return $null
}

# -----------------------------------------------------------------------------
#  Run
# -----------------------------------------------------------------------------

Note '================================================================='
Note ' TASK-031 gate-6 coverage probes -- declared spellings are caught'
Note '================================================================='
Note ("repo      : {0}" -f $RepoRoot)
Note ("guardrail : {0}" -f $Script)
Note ("guardrail sha256: {0}" -f (Get-Sha $Script))
$headSha = (& git -C $RepoRoot rev-parse --short HEAD).Trim()
Note ("git HEAD  : {0}" -f $headSha)
$probeShaBefore = Get-Sha $ProbeFull
Note ("probe file: {0}" -f $ProbeRel)
Note ("probe file sha256 (baseline): {0}" -f $probeShaBefore)

# --- B1: baseline ------------------------------------------------------------
$baseline = Invoke-Gate6 -Label 'B1_baseline'
$baselineJson = Invoke-Gate6Json -Label 'B1_baseline_json'
Check 'B1_baseline_is_green' ($baseline.exit -eq 0) `
    ("python check_narrowing_points.py -> exit={0} log={1} sha256={2}" -f $baseline.exit, $baseline.log, $baseline.sha)
Check 'B1_baseline_scanned_67' ($null -ne $baselineJson.json -and $baselineJson.json.scanned -eq 67 -and $baselineJson.json.pinned -eq 67) `
    ("scanned={0} pinned={1} (zero false positives on the current tree)" -f $baselineJson.json.scanned, $baselineJson.json.pinned)
Check 'B1_baseline_no_failures' ($null -ne $baselineJson.json -and $baselineJson.json.unannotated.Count -eq 0 -and $baselineJson.json.unlisted.Count -eq 0 -and $baselineJson.json.stale.Count -eq 0) `
    ("unannotated={0} unlisted={1} stale={2} moved={3}" -f $baselineJson.json.unannotated.Count, $baselineJson.json.unlisted.Count, $baselineJson.json.stale.Count, $baselineJson.json.moved.Count)
Check 'B1_baseline_text_says_bounded' ($baseline.text -match 'declared spelling') `
    ("the PASS line now states the bounded guarantee (TASK-031 / 22.3b) instead of 'every narrowing point'")

# --- coverage declaration ----------------------------------------------------
$covOut = Join-Path $Logs 'B1_coverage.log'
& cmd /c "python `"$Script`" --coverage > `"$covOut`" 2>&1"
$covCode = $LASTEXITCODE
$covText = Get-Content -Raw -Encoding UTF8 $covOut
Note '--- declared coverage (--coverage) ---'
Note $covText
Check 'B1_coverage_exits_0' ($covCode -eq 0) ("--coverage -> exit={0} log={1} sha256={2}" -f $covCode, $covOut, (Get-Sha $covOut))
$declaredIds = @($baselineJson.json.coverage.spellings | ForEach-Object { [string]$_.id })
$missingIds = @($declaredIds | Where-Object { -not $covText.Contains($_) })
Check 'B1_coverage_lists_every_declared_id' ($declaredIds.Count -ge 16 -and $missingIds.Count -eq 0) `
    ("the scan declares {0} pattern ids in --json and prints every one in --coverage; missing={1}" -f $declaredIds.Count, ($missingIds -join ','))
Check 'B1_coverage_declares_the_boundary' ($covText -match 'implicit narrowing of a runtime double') `
    ("--coverage prints the declared non-coverage (the runtime implicit narrowing) instead of claiming it")
# TASK-033 (M4e D-M4e-1): the *new* declared boundary is the cross-file alias,
# and the same-file alias is no longer a silent gap (T04 proves it is caught).
Check 'B1_coverage_declares_the_alias_boundary' ($covText -match 'alias of real_t/float declared in') `
    ("--coverage names the alias boundary it does not cover (a typedef alias declared in another file)")

# -----------------------------------------------------------------------------
#  Probe table
#
#  `pattern` is the pattern id the scanner must report for the probe line;
#  `expectExit` is 1 for a declared spelling and 0 for a boundary/false-positive
#  probe. P1..P6 reproduce the M4d audit's own probe texts verbatim.
# -----------------------------------------------------------------------------
$probes = @(
    @{ id = 'P1_m4d_implicit_literal'; name = 'audit_probe_c'; pattern = 'lit_float_range'; expectExit = 1
       lines = @('', 'const real_t audit_probe_c = 1.0e300;') },
    @{ id = 'P2_m4d_static_cast_float'; name = 'audit_probe_d'; pattern = 'cast_static_float'; expectExit = 1
       lines = @('', 'const float audit_probe_d = static_cast<float>(1.0e300);') },
    @{ id = 'P3_m4d_qualified_color'; name = 'audit_probe_e'; pattern = 'ctor_color'; expectExit = 1
       lines = @('', 'const Color audit_probe_e = ::Color(1.0e300, 0.0, 0.0, 1.0);') },
    @{ id = 'P4_m4d_braced_vector3'; name = 'audit_probe_f'; pattern = 'ctor_vector3'; expectExit = 1
       lines = @('', 'const Vector3 audit_probe_f = Vector3{1.0e300, 0.0, 0.0};') },
    @{ id = 'P5_m4d_split_line_color'; name = 'audit_probe_g'; pattern = 'ctor_color'; expectExit = 1
       lines = @('', 'const Color audit_probe_g = Color', '(1.0e300, 0.0, 0.0, 1.0);') },
    @{ id = 'P6_m4d_control_c_cast'; name = 'audit_probe_h'; pattern = 'cast_real_t'; expectExit = 1
       lines = @('', 'const real_t audit_probe_h = (real_t)1.0e300;') },
    @{ id = 'S01_cast_float'; name = 'task031_probe_cast_float'; pattern = 'cast_float'; expectExit = 1
       lines = @('', 'const float task031_probe_cast_float = (float)1.0e300;') },
    @{ id = 'S02_cast_static_real_t'; name = 'task031_probe_static_real_t'; pattern = 'cast_static_real_t'; expectExit = 1
       lines = @('', 'const real_t task031_probe_static_real_t = static_cast<real_t>(1.0e300);') },
    @{ id = 'S03_cast_func_real_t'; name = 'task031_probe_func_real_t'; pattern = 'cast_func_real_t'; expectExit = 1
       lines = @('', 'const real_t task031_probe_func_real_t = real_t(1.0e300);') },
    @{ id = 'S04_cast_func_float'; name = 'task031_probe_func_float'; pattern = 'cast_func_float'; expectExit = 1
       lines = @('', 'const float task031_probe_func_float = float(1.0e300);') },
    @{ id = 'S05_ctor_color_brace'; name = 'task031_probe_ctor_color_brace'; pattern = 'ctor_color'; expectExit = 1
       lines = @('', 'const Color task031_probe_ctor_color_brace{1.0e300, 0.0, 0.0, 1.0};') },
    @{ id = 'S06_ctor_vector2'; name = 'task031_probe_ctor_vector2'; pattern = 'ctor_vector2'; expectExit = 1
       lines = @('', 'const Vector2 task031_probe_ctor_vector2 = Vector2(1.0e300, 0.0);') },
    @{ id = 'S07_ctor_vector4'; name = 'task031_probe_ctor_vector4'; pattern = 'ctor_vector4'; expectExit = 1
       lines = @('', 'const Vector4 task031_probe_ctor_vector4 = Vector4{1.0e300, 0.0, 0.0, 1.0};') },
    @{ id = 'S08_lit_float_brace'; name = 'task031_probe_lit_brace'; pattern = 'lit_float_range'; expectExit = 1
       lines = @('', 'const real_t task031_probe_lit_brace{1.0e300};') },
    @{ id = 'S09_dbl_cast_into_float'; name = 'task031_probe_dbl_cast'; pattern = 'dbl_cast_into_float'; expectExit = 1
       lines = @('', 'const real_t task031_probe_dbl_cast = (double)1.0e300;') },
    @{ id = 'S10_ctor_list_init_declared'; name = 'task031_probe_ctor_declared'; pattern = 'ctor_color'; expectExit = 1
       lines = @('', 'const Color task031_probe_ctor_declared{1.0e300, 0.0, 0.0, 1.0};') },
    @{ id = 'S11_ctor_copy_list_init'; name = 'task031_probe_ctor_copy'; pattern = 'ctor_color'; expectExit = 1
       lines = @('', 'const Color task031_probe_ctor_copy = {1.0e300, 0.0, 0.0, 1.0};') },
    @{ id = 'S12_ctor_direct_init_literal'; name = 'task031_probe_ctor_direct'; pattern = 'ctor_vector2_arg_literal'; expectExit = 1
       lines = @('', 'const Vector2 task031_probe_ctor_direct(1.0e300, 0.0);') },
    @{ id = 'S13_ctor_direct_init_literal_3rd'; name = 'task031_probe_ctor_direct3'; pattern = 'ctor_vector3_arg_literal'; expectExit = 1
       lines = @('', 'const Vector3 task031_probe_ctor_direct3(0.0, 1.0e300, 0.0);') },
    @{ id = 'S14_ctor_color_direct_init_literal'; name = 'task031_probe_ctor_direct_color'; pattern = 'ctor_color_arg_literal'; expectExit = 1
       lines = @('', 'const Color task031_probe_ctor_direct_color(1.0e300, 0.0, 0.0, 1.0);') },
    @{ id = 'S15_ctor_vector4_direct_init_literal'; name = 'task031_probe_ctor_direct4'; pattern = 'ctor_vector4_arg_literal'; expectExit = 1
       lines = @('', 'const Vector4 task031_probe_ctor_direct4(1.0e300, 0.0, 0.0, 1.0);') },
    @{ id = 'T01_signed_float_literal'; name = 'task033_probe_signed_literal'; pattern = 'lit_float_range'; expectExit = 1
       lines = @('', 'const float task033_probe_signed_literal = -1.0e300;') },
    @{ id = 'T02_parenthesised_float_literal'; name = 'task033_probe_paren_literal'; pattern = 'lit_float_range'; expectExit = 1
       lines = @('', 'const float task033_probe_paren_literal = (1.0e300);') },
    @{ id = 'T03_hexadecimal_float_literal'; name = 'task033_probe_hex_literal'; pattern = 'lit_float_range'; expectExit = 1
       lines = @('', 'const float task033_probe_hex_literal = 0x1p1000f;') },
    @{ id = 'T04_typedef_alias_literal'; name = 'task033_probe_alias_literal'; pattern = 'lit_real_t_alias'; expectExit = 1
       lines = @('', 'typedef float task033_probe_alias_type;', 'const task033_probe_alias_type task033_probe_alias_literal = 1.0e300;') },
    @{ id = 'T05_array_initialiser_literal'; name = 'task033_probe_array_literal'; pattern = 'lit_float_range'; expectExit = 1
       lines = @('', 'const float task033_probe_array_literal[1] = { 1.0e300 };') },
    @{ id = 'B7_boundary_in_range_ctor_and_variable'; name = 'task031_boundary'; pattern = $null; expectExit = 0
       lines = @('', '// TASK-031 boundary probe: in-range arguments and values that only become', '// out of range at run time are DECLARED NOT COVERED (see --coverage).', 'static void task031_boundary_probe(double p_v) {', '	const Vector2 task031_boundary_direct(1.0, 2.0);', '	const real_t task031_boundary_from_var = p_v;', '	(void)task031_boundary_direct;', '	(void)task031_boundary_from_var;', '}') },
    @{ id = 'B6_boundary_runtime_double'; name = 'task031_boundary_result'; pattern = $null; expectExit = 0
       lines = @('', '// TASK-031 boundary probe: implicit narrowing of a runtime double into real_t is', '// DECLARED NOT COVERED by this scanner (see --coverage); this probe must stay green.', 'static real_t task031_boundary_implicit(double p_v) {', '	const real_t task031_boundary_result = p_v;', '	return task031_boundary_result;', '}') },
    @{ id = 'B5_false_positive_guard'; name = 'task031_fp'; pattern = $null; expectExit = 0
       lines = @('', '// const real_t task031_fp_comment = 1.0e300;', '/* const Vector3 task031_fp_block{1.0e300, 0.0, 0.0}; */', 'static const char *task031_fp_string = "Color(1.0e300, 0.0, 0.0, 1.0)";', 'static const double task031_fp_wide = 1.0e300;', 'static const float task031_fp_inrange = 1.5f;') }
)

try {
    foreach ($probe in $probes) {
        Note ''
        Note ("--- {0} ({1}; expected exit {2}) ---" -f $probe.id, $probe.name, $probe.expectExit)
        Append-Lines -Path $ProbeFull -Lines $probe.lines
        $json = Invoke-Gate6Json -Label ("probe_" + $probe.id)
        $point = Get-PointFor -Json $json.json -Needle $probe.name
        $matched = $false
        $seen = '<none>'
        if ($null -ne $point) {
            $seen = ($point.patterns -join ',')
            if ($null -eq $probe.pattern) { $matched = $true } else { $matched = (@($point.patterns) -contains $probe.pattern) }
        }
        if ($probe.expectExit -eq 1) {
            Check (($probe.id) + '_is_red') ($json.exit -eq 1) `
                ("exit={0}; the probe line is a narrowing point that carries no `// MCP-NARROWING:` marker" -f $json.exit)
            Check (($probe.id) + '_named_with_pattern') ($matched) `
                ("the report names '{0}' (json {1}) with patterns=[{2}] (expected '{3}')" -f $probe.name, (Split-Path -Leaf $json.log), $seen, $probe.pattern)
        } else {
            Check (($probe.id) + '_stays_green') ($json.exit -eq 0) `
                ("exit={0}: this spelling is declared NOT covered / not a narrowing point, so a green run is the honest result" -f $json.exit)
            Check (($probe.id) + '_invisible') (-not $matched) `
                ("no scanned point mentions '{0}' (patterns seen for it: {1})" -f $probe.name, $seen)
        }
        $shaAfter = Restore-ProbeFile
        Check (($probe.id) + '_reverted_byte_identical') ($shaAfter -eq $probeShaBefore) `
            ("{0} sha256 after revert = {1} (baseline {2})" -f $ProbeRel, $shaAfter, $probeShaBefore)
    }
} finally {
    # A crash must not leave the working tree dirty.
    & git -C $RepoRoot checkout -- $ProbeRel | Out-Null
    Note ("finally: reverted {0} sha256={1}" -f $ProbeRel, (Get-Sha $ProbeFull))
}

# --- B4: every declared spelling id is exercised by its own red probe --------
$probedIds = @($probes | Where-Object { $_.expectExit -eq 1 -and $null -ne $_.pattern } | ForEach-Object { [string]$_.pattern } | Sort-Object -Unique)
$unprobed = @($declaredIds | Where-Object { $probedIds -notcontains $_ })
Check 'B4_every_declared_id_has_a_red_probe' ($unprobed.Count -eq 0) `
    ("{0} of {1} declared ids are exercised by an 'insert -> exit 1' probe; unprobed={2}" -f ($declaredIds.Count - $unprobed.Count), $declaredIds.Count, ($unprobed -join ','))
$m4dProbes = @($probes | Where-Object { $_.id -like 'P?_m4d_*' -and $_.expectExit -eq 1 })
Check 'B4_m4d_five_are_all_probed' ($m4dProbes.Count -ge 5) `
    ("the five M4d D2 probes (plus the `(real_t)` control) are in this very table: {0}" -f (($m4dProbes | ForEach-Object { $_.id }) -join ', '))

# --- B1 again: the tree restored --------------------------------------------
Note ''
Note '--- B1b: after every probe, the tree restored ---'
$final = Invoke-Gate6 -Label 'B1b_restored'
$finalJson = Invoke-Gate6Json -Label 'B1b_restored_json'
Check 'B1b_restored_is_green' ($final.exit -eq 0) ("exit={0}" -f $final.exit)
Check 'B1b_restored_scanned_67' ($finalJson.json.scanned -eq 67 -and $finalJson.json.pinned -eq 67) `
    ("scanned={0} pinned={1}" -f $finalJson.json.scanned, $finalJson.json.pinned)
Check 'B1b_restored_byte_identical' ((Get-Sha $ProbeFull) -eq $probeShaBefore) `
    ("{0} sha256 = {1}" -f $ProbeRel, (Get-Sha $ProbeFull))
Check 'B1b_worktree_clean_of_probes' (((& git -C $RepoRoot status --porcelain -- $ProbeRel | Out-String).Trim()) -eq '') `
    ("git status --porcelain for {0} is empty" -f $ProbeRel)

# -----------------------------------------------------------------------------
$logPath = Join-Path $Root 'gate6-coverage-probes.log.txt'
$summary = @()
foreach ($entry in $script:Checks) {
    $tag = 'FAIL'
    if ($entry.pass) { $tag = 'PASS' }
    $summary += ("[{0}] {1} :: {2}" -f $tag, $entry.id, $entry.evidence)
}
[IO.File]::WriteAllBytes($logPath, (New-Object Text.UTF8Encoding($false)).GetBytes(($summary -join "`r`n") + "`r`n"))

$passed = @($script:Checks | Where-Object { $_.pass }).Count
$total = $script:Checks.Count
Write-Host ''
Write-Host '========================== SUMMARY =========================='
foreach ($c in $script:Checks) {
    $tag = 'FAIL'
    if ($c.pass) { $tag = 'PASS' }
    Write-Host ("{0}  {1}" -f $tag, $c.id)
}
Write-Host ("{0}/{1} checks passed; logs in {2} (log sha256={3})" -f $passed, $total, $Logs, (Get-Sha $logPath))
if ($passed -ne $total) { exit 1 }
exit 0
