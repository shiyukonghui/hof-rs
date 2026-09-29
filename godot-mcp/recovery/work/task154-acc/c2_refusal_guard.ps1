# TASK-154 acceptance: independent reproduction of the port refusal guard.
# Read-only w.r.t. the repository: it only *runs* the two scripts with a refused
# port and inspects whether OutRoot was created. No port is bound or probed.
$ErrorActionPreference = 'Continue'
$eng = 'F:\moonbit-hof-rs\godot-mcp\godot'
$acc = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task154-acc'
$log = Join-Path $acc 'c2logs'
New-Item -ItemType Directory -Force -Path $log | Out-Null
$ps  = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

# --- static control-flow facts (line numbers) ---------------------------------
$sites = 'exit 4|&\s*\$Curl|Start-Process|Import-McpProject|Remove-Item -Recurse -Force \$Root|New-Item -ItemType Directory|Invoke-WebRequest|Invoke-RestMethod|TcpClient|HttpClient|WebClient|System\.Net'
foreach ($n in @('mcp029_clear_default_evidence.ps1','mcp032_d3_d4_d6_evidence.ps1')) {
    $p = Join-Path $eng "modules\mcp_server\scripts\$n"
    Write-Host "=== ${n}: every guard exit / process / network / out-root site ==="
    $i = 0
    foreach ($line in [IO.File]::ReadAllLines($p)) {
        $i++
        if ($line -match $sites) { Write-Host ("  L{0,4}: {1}" -f $i, $line.Trim()) }
    }
}

$script:results = New-Object System.Collections.Generic.List[object]

function Invoke-Case {
    param([string]$Script, [string[]]$ExtraArgs, [string]$OutRoot, [string]$Label)
    Write-Host ''
    Write-Host "===== CASE: $Label ====="
    Write-Host "script  = $Script"
    Write-Host "args    = $($ExtraArgs -join ' ')"
    Write-Host "OutRoot = $OutRoot"
    if (Test-Path $OutRoot) { Write-Host "PRE-EXISTING OutRoot! aborting"; return }
    $argList = @('-NoProfile','-ExecutionPolicy','Bypass','-File',$Script) + $ExtraArgs + @('-OutRoot',$OutRoot)
    $so = Join-Path $log ((Split-Path $OutRoot -Leaf) + '.stdout.txt')
    $se = Join-Path $log ((Split-Path $OutRoot -Leaf) + '.stderr.txt')
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $proc = Start-Process -FilePath $ps -ArgumentList $argList -PassThru -NoNewWindow -RedirectStandardOutput $so -RedirectStandardError $se
    $proc.EnableRaisingEvents = $true
    $seen = New-Object System.Collections.Generic.HashSet[string]
    $samples = 0
    while (-not $proc.HasExited) {
        try {
            foreach ($c in (Get-CimInstance Win32_Process -Filter "ParentProcessId=$($proc.Id)" -ErrorAction SilentlyContinue)) {
                [void]$seen.Add($c.Name + ' :: ' + $c.CommandLine)
            }
            $samples++
        } catch { }
    }
    $proc.WaitForExit()
    $sw.Stop()
    Write-Host ("exit code                = {0}" -f $proc.ExitCode)
    Write-Host ("elapsed ms               = {0}  (process-tree samples = {1})" -f $sw.ElapsedMilliseconds, $samples)
    Write-Host ("child processes observed = {0}" -f $seen.Count)
    foreach ($s in $seen) { Write-Host "   child: $s" }
    Write-Host ("OutRoot created          = {0}" -f (Test-Path $OutRoot))
    Write-Host "--- stdout ---"
    Get-Content $so -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "  $_" }
    Write-Host "--- stderr ---"
    Get-Content $se -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "  $_" }
    $script:results.Add([pscustomobject]@{ label = $Label; exit = $proc.ExitCode; out_root_created = (Test-Path $OutRoot); children = $seen.Count; ms = $sw.ElapsedMilliseconds })
}

$s029 = Join-Path $eng 'modules\mcp_server\scripts\mcp029_clear_default_evidence.ps1'
$s032 = Join-Path $eng 'modules\mcp_server\scripts\mcp032_d3_d4_d6_evidence.ps1'

Invoke-Case -Script $s029 -ExtraArgs @('-EditorPort','9877') -OutRoot "$acc\rg-029-editor9877" -Label 'mcp029 -EditorPort 9877'
Invoke-Case -Script $s029 -ExtraArgs @('-GamePort','9877')   -OutRoot "$acc\rg-029-game9877"   -Label 'mcp029 -GamePort 9877'
Invoke-Case -Script $s032 -ExtraArgs @('-EditorPort','9877') -OutRoot "$acc\rg-032-editor9877" -Label 'mcp032 -EditorPort 9877'
Invoke-Case -Script $s032 -ExtraArgs @('-GamePort','9877')   -OutRoot "$acc\rg-032-game9877"   -Label 'mcp032 -GamePort 9877'
Invoke-Case -Script $s029 -ExtraArgs @('-EditorPort','1234') -OutRoot "$acc\rg-029-port1234"   -Label 'mcp029 -EditorPort 1234 (outside the allowed set)'
Invoke-Case -Script $s032 -ExtraArgs @('-GamePort','9887')   -OutRoot "$acc\rg-032-port9887"   -Label 'mcp032 -GamePort 9887 (inside 9870..9889, outside the allowed set)'

# PSScriptRoot literal branch: a copy whose *launch path* contains the refused literal
$copyDir = Join-Path $acc 'path-with-9877-literal'
New-Item -ItemType Directory -Force -Path $copyDir | Out-Null
Copy-Item $s029 (Join-Path $copyDir 'mcp029_clear_default_evidence.ps1') -Force
Copy-Item (Join-Path $eng 'modules\mcp_server\scripts\mcp_import_guard.ps1') $copyDir -Force
Invoke-Case -Script (Join-Path $copyDir 'mcp029_clear_default_evidence.ps1') -ExtraArgs @('-EditorPort','9888') -OutRoot "$acc\rg-029-rootliteral" -Label 'mcp029 copy under a dir whose path contains 9877, with allowed ports'

Write-Host ''
Write-Host '===== SUMMARY ====='
$script:results | Format-Table -AutoSize | Out-String -Width 200 | ForEach-Object { Write-Host $_ }
