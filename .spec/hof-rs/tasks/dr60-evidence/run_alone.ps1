# DR-60 characterisation driver: run the endpoint_liveness target alone, serially.
# Usage: pwsh -File run_alone.ps1 -Runs 25 -Out <file> [-TestThreads N]
param(
  [int]$Runs = 25,
  [string]$Out = "F:\moonbit-hof-rs\.dr60\alone.log",
  [string]$TestThreads = ""
)
$ErrorActionPreference = "Continue"
New-Item -ItemType Directory -Force -Path (Split-Path $Out) | Out-Null
"" | Set-Content -Path $Out -Encoding utf8
for ($i = 1; $i -le $Runs; $i++) {
  $stamp = (Get-Date).ToString("HH:mm:ss")
  if ($TestThreads -ne "") {
    $raw = cargo test --offline --test endpoint_liveness -- --test-threads=$TestThreads 2>&1
  } else {
    $raw = cargo test --offline --test endpoint_liveness 2>&1
  }
  $code = $LASTEXITCODE
  $summary = ($raw | Select-String -Pattern "test result:" | ForEach-Object { $_.Line.Trim() }) -join " | "
  if (-not $summary) { $summary = "(no 'test result:' line)" }
  Add-Content -Path $Out -Value ("run={0} start={1} exit={2} :: {3}" -f $i, $stamp, $code, $summary) -Encoding utf8
  if ($code -ne 0) {
    Add-Content -Path $Out -Value ("----- BEGIN VERBATIM OUTPUT run={0} -----" -f $i) -Encoding utf8
    $raw | Add-Content -Path $Out -Encoding utf8
    Add-Content -Path $Out -Value ("----- END VERBATIM OUTPUT run={0} -----" -f $i) -Encoding utf8
  }
}
Write-Host "DONE runs=$Runs out=$Out"
