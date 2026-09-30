param([string]$RoundId = 'smoke-t10')
$ErrorActionPreference = 'Continue'
Set-Location 'F:\moonbit-hof-rs'
$raw = [System.IO.File]::ReadAllText('F:\moonbit-hof-rs\config\model.secret.env')
$m = [regex]::Match($raw, 'HOH_MODEL_API_KEY\s*=\s*(.+)')
$env:HOH_MODEL_API_KEY = $m.Groups[1].Value.Trim()
"KEYLEN=$($env:HOH_MODEL_API_KEY.Length)"
$log = "C:\Users\wyl\AppData\Local\Temp\smoke-t10\console.txt"
$start = Get-Date
"START=$($start.ToString('yyyy-MM-dd HH:mm:ss'))"
& 'F:\moonbit-hof-rs\target\release\hoh.exe' run --iterations 1 --run-id $RoundId *> $log
$ec = $LASTEXITCODE
$end = Get-Date
"ROUND_EXIT=$ec"
"END=$($end.ToString('yyyy-MM-dd HH:mm:ss'))"
"ELAPSED=$([int]($end - $start).TotalSeconds)s"
