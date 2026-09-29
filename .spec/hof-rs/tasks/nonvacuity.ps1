# Non-vacuity (plant-and-revert) harness for the DR-54..DR-56 batch.
#
# Each experiment plants exactly one behaviour change, runs exactly one test,
# records the real failure output, and reverts with `git checkout --`.  The
# script refuses to run if the tree is dirty so a failure can never be confused
# with a pre-existing one, and it verifies the revert by blob comparison.

param(
  [string]$OutDir = ".spec\hof-rs\tasks\nonvacuity"
)

$ErrorActionPreference = 'Continue'
$repo = (Get-Location).Path
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Assert-Clean {
  # Only *tracked* modifications matter: the plant-and-revert proof is a blob
  # comparison against HEAD, so an untracked artifact (a log, this script) is
  # irrelevant.  A stale modification, however, would make a red result
  # unattributable — hence the check.
  $dirty = git status --porcelain --untracked-files=no 2>$null
  if ($dirty) {
    throw "the working tree has uncommitted tracked changes; commit before planting: $dirty"
  }
}

function Blob([string]$path) { (git hash-object $path 2>$null).Trim() }

function Read-Text([string]$path) {
  # The checkout has files in both CRLF and LF form (git's autocrlf on Windows).
  # Normalise to LF for matching, and remember the original so the write-back is
  # byte-identical apart from the plant.
  $bytes = [IO.File]::ReadAllBytes((Join-Path $repo $path))
  $crlf = $false
  for ($i = 0; $i -lt $bytes.Length - 1; $i++) {
    if ($bytes[$i] -eq 13 -and $bytes[$i + 1] -eq 10) { $crlf = $true; break }
  }
  $text = [Text.Encoding]::UTF8.GetString($bytes).Replace("`r`n", "`n")
  return @{ text = $text; crlf = $crlf }
}

function Write-Text([string]$path, [string]$text, [bool]$crlf) {
  $out = $text
  if ($crlf) { $out = $text.Replace("`n", "`r`n") }
  [IO.File]::WriteAllText((Join-Path $repo $path), $out, (New-Object Text.UTF8Encoding($false)))
}

function Run-Experiment {
  param(
    [string]$Id,
    [string]$File,
    [string]$Find,
    [string]$Replace,
    [string]$TestTarget,
    [string]$TestName,
    [string]$Expect
  )

  Assert-Clean
  $before = Blob $File
  $source = Read-Text $File
  $text = $source.text
  $findN = $Find.Replace("`r`n", "`n")
  $replaceN = $Replace.Replace("`r`n", "`n")
  if (-not $text.Contains($findN)) {
    throw "[$Id] the plant anchor was not found in $File"
  }
  $planted = $text.Replace($findN, $replaceN)
  Write-Text $File $planted $source.crlf

  # Planted *now* starts the experiment; the buffer has no BOM by construction.
  $plantedHash = Blob $File
  $log = Join-Path $OutDir "$Id.txt"
  try {
    $output = & cargo test --offline --test $TestTarget $TestName 2>&1 | Out-String
    $exit = $LASTEXITCODE
  } finally {
    # The revert must happen even if the test run itself blew up, or the next
    # experiment would start from a planted file.
    git checkout -- $File
  }
  "EXIT=$exit" | Out-File -Append -Encoding utf8 $log
  $output | Out-File -Append -Encoding utf8 $log

  # Prove the revert by blob identity.
  $after = Blob $File
  if ($after -ne $before) { throw "[$Id] the revert did not restore $File" }
  if ($plantedHash -eq $before) { throw "[$Id] the plant changed nothing" }

  $verdict = if ($exit -ne 0) { "RED (as required)" } else { "GREEN (VACUOUS — the test has no teeth)" }
  [pscustomobject]@{
    id = $Id
    file = $File
    test = "$TestTarget::$TestName"
    planted_blob = $plantedHash
    restored_blob = $after
    exit = $exit
    expect = $Expect
    verdict = $verdict
    log = $log
  }
}

$results = @()

# --- DR-56 -----------------------------------------------------------------
# ① business errors: make them retryable (the smoke-t6 defect itself).
$results += Run-Experiment -Id 'nv1-business-error-retryable' `
  -File 'src/tools/reliable.rs' `
  -Find '        // A JSON-RPC business error is a verdict: never retryable.
        return McpFailure::new(tool, Some(mcp.code), mcp.message.clone(), attempt);' `
  -Replace '        // PLANT: the smoke-t6 defect — retry a business error too.
        let mut planted = McpFailure::new(tool, Some(mcp.code), mcp.message.clone(), attempt);
        planted.retryable = true;
        return planted;' `
  -TestTarget 'mcp_reliability' -TestName 'retries_are_class_aware_business_errors_are_never_retried' `
  -Expect 'the business error must be attempted once, not three times'

# ② transport failures: make them non-retryable.
$results += Run-Experiment -Id 'nv2-transport-not-retryable' `
  -File 'src/tools/reliable.rs' `
  -Find '        let mut failure = McpFailure::new(tool, None, transport.to_string(), attempt);
        failure.retryable = true;' `
  -Replace '        let mut failure = McpFailure::new(tool, None, transport.to_string(), attempt);
        // PLANT: transport failures are no longer retryable.
        failure.retryable = false;' `
  -TestTarget 'mcp_reliability' -TestName 'the_retry_classifier_is_the_single_decider' `
  -Expect 'a transport failure must still be retried (call_count == 4)'

# ③ two consecutive transport failures: make the threshold unreachable.
$results += Run-Experiment -Id 'nv3-endpoint-immortal' `
  -File 'src/tools/endpoint.rs' `
  -Find 'pub const ENDPOINT_DEATH_THRESHOLD: u32 = 2;' `
  -Replace 'pub const ENDPOINT_DEATH_THRESHOLD: u32 = u32::MAX; // PLANT: the endpoint can never die' `
  -TestTarget 'endpoint_liveness' -TestName 'two_transport_failures_kill_the_endpoint_and_later_calls_do_not_retry' `
  -Expect 'the endpoint must be marked unavailable after two failures'

# ④ one failure must NOT kill the endpoint: make the threshold one.
$results += Run-Experiment -Id 'nv4-first-failure-kills' `
  -File 'src/tools/endpoint.rs' `
  -Find 'pub const ENDPOINT_DEATH_THRESHOLD: u32 = 2;' `
  -Replace 'pub const ENDPOINT_DEATH_THRESHOLD: u32 = 1; // PLANT: first failure is a verdict' `
  -TestTarget 'endpoint_liveness' -TestName 'a_single_transport_failure_does_not_kill_the_endpoint' `
  -Expect 'one failure must not mark the endpoint unavailable'

# ⑤ business errors must not count toward the streak.
$results += Run-Experiment -Id 'nv5-business-error-counts' `
  -File 'src/tools/mod.rs' `
  -Find '                } else {
                    // A business error is an answer: the endpoint is alive.
                    self.observe_liveness(&endpoint, Ok(()));
                }' `
  -Replace '                } else {
                    // PLANT: count a business error as a transport failure too.
                    self.observe_liveness(&endpoint, Err(()));
                }' `
  -TestTarget 'endpoint_liveness' -TestName 'business_errors_never_count_toward_the_streak' `
  -Expect 'the business errors must not add to the streak'

# ⑥ "the last real failure is returned", not the first.
$results += Run-Experiment -Id 'nv6-first-failure-returned' `
  -File 'src/tools/reliable.rs' `
  -Find '                last = Some(failure);' `
  -Replace '                // PLANT: keep only the first failure, not the last real one.
                if last.is_none() {
                    last = Some(failure);
                }' `
  -TestTarget 'mcp_reliability' -TestName 'retries_are_bounded_and_preserve_the_real_error' `
  -Expect 'the failure must carry the LAST attempt count (3), not the first (1)'

# ⑦ execute_gdscript code-shape guard: send a bare expression (the DR-50 defect).
$results += Run-Experiment -Id 'nv7-gdscript-bare-expression' `
  -File 'src/adapter/godot.rs' `
  -Find '    pub fn player_position() -> String {
        "return str(get_tree().current_scene.get_node_or_null(\"Player\").position.x) + \",\" + \
         str(get_tree().current_scene.get_node_or_null(\"Player\").position.y)"
            .to_string()
    }' `
  -Replace '    pub fn player_position() -> String {
        // PLANT: the DR-50 defect — a bare expression with no `return`.
        "str(get_tree().current_scene.get_node_or_null(\"Player\").position.x) + \",\" + \
         str(get_tree().current_scene.get_node_or_null(\"Player\").position.y)"
            .to_string()
    }' `
  -TestTarget 'evidence_battery' -TestName 'every_surviving_execute_gdscript_call_is_a_gdscript_body' `
  -Expect 'a value-reading body must return its reading'

$results | ConvertTo-Json | Out-File -Encoding utf8 (Join-Path $OutDir 'results.json')
$results | Format-Table id, exit, verdict -AutoSize
