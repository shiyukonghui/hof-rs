$ErrorActionPreference = 'Continue'
$scripts = 'F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\scripts'
$src = Join-Path $scripts 'mcp032_d3_d4_d6_evidence.ps1'
$probe = Join-Path $scripts 'task154_probe_mcp032.ps1'
$log = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task154\probe_mcp032.txt'
function Say($t) { Write-Output $t }

try {
    # A throwaway copy that differs from the committed file only in the braces of
    # PRE-EXISTING `-f` evidence strings (a `{` that is not a format placeholder
    # makes `-f` throw). The committed file is not modified; this is only so the
    # changed code paths can be exercised live to the D6 section.
    $text = [IO.File]::ReadAllText($src, [Text.Encoding]::UTF8)
    $pairs = @(
        @("hand-built {'Material','material'} JSON:", "hand-built {{'Material','material'}} JSON:"),
        @("{prefix:'application/config/name'}", "{{prefix:'application/config/name'}}"),
        @("{filter:...}", "{{filter:...}}"),
        @("{prefix, filter}", "{{prefix, filter}}"),
        @("project_get_info {bogus:1}", "project_get_info {{bogus:1}}"),
        @("{include_default:true}", "{{include_default:true}}")
    )
    $patched = $text
    foreach ($pair in $pairs) {
        if ($patched -notlike ('*' + $pair[0] + '*')) { throw ('needle not found - refusing to probe: ' + $pair[0]) }
        $patched = $patched.Replace($pair[0], $pair[1])
    }
    if ($patched -ceq $text) { throw 'replacement did nothing' }
    [IO.File]::WriteAllText($probe, $patched, (New-Object Text.UTF8Encoding($false)))
    Say ('probe file written: ' + $probe)
    $diff = @(& git -C (Join-Path $scripts '..\..\..') diff --no-index --stat -- $src $probe 2>$null)
    Say ('diff --no-index --stat (probe vs committed):')
    $diff | ForEach-Object { Say ('   ' + $_) }

    $outRoot = Join-Path $env:TEMP 'task154-probe-032'
    Say ('OutRoot = ' + $outRoot)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $probe -OutRoot $outRoot 2>&1
    $code = $LASTEXITCODE
    $sw.Stop()
    Say ('EXITCODE = ' + $code + '   wall = ' + [math]::Round($sw.Elapsed.TotalSeconds, 1) + 's')
    foreach ($line in $out) { Say ([string]$line) }
} finally {
    if (Test-Path $probe) { Remove-Item -Force $probe }
    Say ''
    Say ('probe file removed = ' + (-not (Test-Path $probe)))
    $st = @(& git -C (Join-Path $scripts '..\..\..') status --porcelain)
    Say ('engine repo git status --porcelain lines after cleanup = ' + $st.Count + ' (0 = clean)')
    $st | ForEach-Object { Say ('   ' + $_) }
}
Say ''
Say 'final port state:'
$hits = @(netstat -ano -p TCP | Where-Object { $_ -match 'LISTENING' -and $_ -match ':(98[7-8][0-9])\s' })
Say ('LISTENING rows in 9870..9889 = ' + $hits.Count)
$hits | ForEach-Object { Say ('   ' + $_.Trim()) }
Say 'DONE'
