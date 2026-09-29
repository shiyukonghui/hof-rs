# DR-60 characterisation: run a target serially, capture output reliably via
# PowerShell pipeline (no cmd redirection), one verbatim log per run.
# Usage: powershell -File run_seq.ps1 -Runs 40 -Dir <dir> -Target endpoint_liveness
param(
  [int]$Runs = 40,
  [string]$Dir = "F:\moonbit-hof-rs\.dr60\raw_alone",
  [string]$Target = "endpoint_liveness",
  [int]$Full = 0
)
New-Item -ItemType Directory -Force -Path $Dir | Out-Null
$summaryPath = Join-Path $Dir "summary.txt"
Remove-Item -Force $summaryPath -ErrorAction SilentlyContinue
Set-Location "F:\moonbit-hof-rs"
for ($i = 1; $i -le $Runs; $i++) {
  $stamp = (Get-Date).ToString("HH:mm:ss")
  if ($Full -eq 1) {
    $out = & cargo test --offline 2>&1
  } else {
    $out = & cargo test --offline --test $Target 2>&1
  }
  $code = $LASTEXITCODE
  $log = Join-Path $Dir ("run{0:D3}.log" -f $i)
  $out | Out-File -FilePath $log -Encoding utf8
  $text = $out -join "`n"
  $m = [regex]::Matches($text, "test result:[^\r\n]*")
  $summary = if ($m.Count -gt 0) { ($m | ForEach-Object { $_.Value }) -join " | " } else { "(no test result line)" }
  $line = "run={0:D3} start={1} exit={2} :: {3}" -f $i, $stamp, $code, $summary
  Add-Content -Path $summaryPath -Value $line
  Write-Output $line
}
Write-Output "DONE runs=$Runs dir=$Dir"
