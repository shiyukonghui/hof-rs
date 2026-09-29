# DR-60 characterisation: run a target serially, one raw log file per run.
# Usage: powershell -File run_raw.ps1 -Runs 40 -Dir <dir> -Args "--test endpoint_liveness"
param(
  [int]$Runs = 40,
  [string]$Dir = "F:\moonbit-hof-rs\.dr60\raw_alone",
  [string]$Args = "--test endpoint_liveness"
)
New-Item -ItemType Directory -Force -Path $Dir | Out-Null
$summaryPath = Join-Path $Dir "summary.txt"
Remove-Item -Force $summaryPath -ErrorAction SilentlyContinue
for ($i = 1; $i -le $Runs; $i++) {
  $stamp = (Get-Date).ToString("HH:mm:ss")
  $log = Join-Path $Dir ("run{0:D3}.log" -f $i)
  $cmdline = "cargo test --offline $Args > `"$log`" 2>&1"
  cmd /c $cmdline
  $code = $LASTEXITCODE
  $text = Get-Content -Raw -Path $log -ErrorAction SilentlyContinue
  $m = [regex]::Matches($text, "test result:[^\r\n]*")
  $summary = if ($m.Count -gt 0) { ($m | ForEach-Object { $_.Value }) -join " | " } else { "(no test result line)" }
  $line = "run={0:D3} start={1} exit={2} :: {3}" -f $i, $stamp, $code, $summary
  Add-Content -Path $summaryPath -Value $line
  Write-Host $line
}
Write-Host "DONE runs=$Runs dir=$Dir"
