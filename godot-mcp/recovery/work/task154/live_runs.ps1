$ErrorActionPreference = 'Continue'
$scripts = 'F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\scripts'
$log = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task154\live_runs.txt'
function Say($t) { Write-Output $t }

Say '##############################################################'
Say '# TASK-154 live runs of the two edited evidence scripts'
Say '# ports 9888/9889 only; the decision maker port is refused at launch'
Say '##############################################################'

foreach ($row in @(@{ f = 'mcp029_clear_default_evidence.ps1'; out = 'task154-live-029' },
                   @{ f = 'mcp032_d3_d4_d6_evidence.ps1'; out = 'task154-live-032' })) {
    Say ''
    Say ('===================== ' + $row.f + ' =====================')
    $outRoot = Join-Path $env:TEMP $row.out
    Say ('OutRoot = ' + $outRoot)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $scripts $row.f) -OutRoot $outRoot 2>&1
    $code = $LASTEXITCODE
    $sw.Stop()
    Say ('EXITCODE = ' + $code + '   wall = ' + [math]::Round($sw.Elapsed.TotalSeconds, 1) + 's')
    foreach ($line in $out) { Say ([string]$line) }
    Say ('--- listeners on 9888/9889 right after: ' + (@(netstat -ano -p TCP | Where-Object { $_ -match 'LISTENING' -and $_ -match ':(988[89])\s' }).Count) + ' (0 = released)')
}

Say ''
Say '===================== final port state ====================='
$hits = @(netstat -ano -p TCP | Where-Object { $_ -match 'LISTENING' -and $_ -match ':(98[7-8][0-9])\s' })
Say ('LISTENING rows in 9870..9889 = ' + $hits.Count)
$hits | ForEach-Object { Say ('   ' + $_.Trim()) }
Say 'DONE'
