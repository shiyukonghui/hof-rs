# DR-60: extract the evidence table for the report from the recorded logs.
$d = "F:\moonbit-hof-rs\.dr60\full_runs"
"=== summary.txt ==="
Get-Content "$d\summary.txt"
"=== per-run exit codes ==="
Get-Content "$d\summary.txt" | ForEach-Object { if ($_ -match "run=(\d+).*exit=(\d+)") { "$($matches[1]) -> $($matches[2])" } }
"=== aggregate test result lines ==="
Get-Content "$d\summary.txt" | ForEach-Object { ($_ -split ":: ")[1] } | Group-Object | Sort-Object Count -Descending | Select-Object Count,Name | Format-Table -AutoSize
"=== any failure text? ==="
$bad = Select-String -Path "$d\run*.log" -Pattern "panicked|FAILED|error: test failed|os error" -ErrorAction SilentlyContinue
if ($bad) { $bad | Select-Object -First 20 Path,LineNumber,Line } else { "none in any of the 10 logs" }
"=== endpoint_liveness line from each run ==="
Get-ChildItem "$d\run*.log" | Sort-Object Name | ForEach-Object {
  $m = Select-String -Path $_.FullName -Pattern "Running tests\\endpoint_liveness" | Select-Object -First 1
  $r = Select-String -Path $_.FullName -Pattern "test result: ok\." | Select-Object -First 1
  "$($_.Name): $($m.Line.Trim())"
}
