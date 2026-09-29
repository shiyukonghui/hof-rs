# DR-57 non-vacuity: controlled plants against the new request-counting test.
#
# Two counterexamples are planted in turn, in src/tools/mod.rs (PRODUCTION code,
# never a test), and the new test must go RED for each:
#
#   A  "zero retries but one request still sent"  -> one extra call before the
#      dead-endpoint return (the DEF-1 counterexample).
#   B  "send everything"                          -> the dead-endpoint guard is
#      removed entirely.
#
# After each plant the file is reverted byte-exactly with `git checkout --`, and
# the revert is proven three ways: `git status --porcelain` empty,
# `git diff --stat` empty, and `git hash-object` == `git rev-parse HEAD:<path>`.
$ErrorActionPreference = 'Continue'
$root = 'F:\moonbit-hof-rs'
Set-Location $root
$file = 'src/tools/mod.rs'
# Raw logs go OUTSIDE the repository on purpose: the task requires the final
# `git status --porcelain` to be completely empty, untracked files included, and
# the report quotes the real output from these logs.
$logDir = Join-Path $env:TEMP 'dr57-plant'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$path = Join-Path $root $file
$headBlob = (git rev-parse "HEAD:$file").Trim()
$original = [System.IO.File]::ReadAllText($path)
# The working tree is CRLF; the here-strings below are LF.  Normalising the file
# text to LF lets the needles be written as ordinary LF blocks.  The revert is
# never string surgery: it is `git checkout --`, proven by blob identity.
$originalLf = $original.Replace("`r`n", "`n")

function Assert-Clean {
    $porcelain = git status --porcelain
    if ($porcelain) { throw "the tree is not clean before a plant: $porcelain" }
}

function Run-Test([string]$name) {
    $log = Join-Path $logDir "$name.txt"
    & cargo test --offline --test endpoint_request_count 2>&1 | Tee-Object -FilePath $log
    $code = $LASTEXITCODE
    "EXIT=$code" | Tee-Object -FilePath $log -Append
    return $code
}

function Restore([string]$name) {
    git checkout -- $file
    $porcelain = git status --porcelain
    $diffstat = git diff --stat -- $file
    $blob = (git hash-object $file).Trim()
    $lines = @()
    $lines += "PLANT $name"
    $lines += "porcelain_empty=$(($porcelain -eq $null -or @($porcelain).Count -eq 0))"
    $lines += "diffstat_empty=$(($diffstat -eq $null -or @($diffstat).Count -eq 0))"
    $lines += "hash_object=$blob"
    $lines += "head_blob=$headBlob"
    $lines += "blob_equal=$($blob -eq $headBlob)"
    $lines | Tee-Object -FilePath (Join-Path $logDir "$name.restore.txt")
}

Assert-Clean

# ---------------------------------------------------------------- plant A
# The needle is the whole guard block, closing brace included, so each plant can
# replace or delete it without leaving an unbalanced brace behind.
$guard = @"
        if let Some(liveness) = self.endpoint_state(&endpoint) {
            if liveness.unavailable {
                return Err(
                    endpoint::McpEndpointUnavailableError::new(liveness, tool).into(),
                );
            }
        }
"@ -replace "`r`n", "`n"
$plantA = @"
        if let Some(liveness) = self.endpoint_state(&endpoint) {
            if liveness.unavailable {
                let _probe_tool = tool.to_string();
                let _probe_client = self
                    .game
                    .lock()
                    .ok()
                    .and_then(|guard| guard.as_ref().map(|route| route.client.clone()));
                if let Some(_probe_client) = _probe_client {
                    let _ = tokio::task::spawn_blocking(move || {
                        _probe_client.call_traced(&_probe_tool, serde_json::json!({}))
                    })
                    .await;
                }
                return Err(
                    endpoint::McpEndpointUnavailableError::new(liveness, tool).into(),
                );
            }
        }
"@ -replace "`r`n", "`n"
if (-not $originalLf.Contains($guard)) { throw "plant A: the dead-endpoint guard was not found verbatim" }
$planted = $originalLf.Replace($guard, $plantA)
if ($planted -eq $original) { throw "plant A: the plant did not change the file" }
[System.IO.File]::WriteAllText($path, $planted)
$plantedBlob = (git hash-object $file).Trim()
"plant A blob=$plantedBlob (must differ from HEAD=$headBlob)" | Tee-Object -FilePath (Join-Path $logDir 'A.planted.txt')
$codeA = Run-Test 'A'
Restore 'A'

# ---------------------------------------------------------------- plant B
$plantB = @"
        let tool_name = tool.to_string();
"@ -replace "`r`n", "`n"
if (-not $originalLf.Contains($guard)) { throw "plant B: the dead-endpoint guard was not found verbatim" }
$plantedB = $originalLf.Replace($guard, $plantB)
if ($plantedB -eq $original) { throw "plant B: the plant did not change the file" }
[System.IO.File]::WriteAllText($path, $plantedB)
$plantedBlobB = (git hash-object $file).Trim()
"plant B blob=$plantedBlobB (must differ from HEAD=$headBlob)" | Tee-Object -FilePath (Join-Path $logDir 'B.planted.txt')
$codeB = Run-Test 'B'
Restore 'B'

"SUMMARY codeA=$codeA codeB=$codeB"
