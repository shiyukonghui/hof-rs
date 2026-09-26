param(
    [Parameter(Mandatory = $true)][string]$Tag,
    [Parameter(Mandatory = $true)][string]$Commands
)
# TASK-088 gate runner: each gate is a separate cmd.exe child (iron rule 4), each
# writes its own stdout/stderr pair (iron rule 2 - Start-Process, no redirection).
# The combined summary goes to <Tag>.summary.txt so the ledger has one artefact.
# `$Commands` is ONE string split on `;;` - an array does not survive
# `powershell -File` (it arrives comma-joined as a single element).
$logdir = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs'
if (-not (Test-Path $logdir)) { New-Item -ItemType Directory -Force -Path $logdir | Out-Null }
$summary = New-Object System.Collections.Generic.List[string]
$i = 0
foreach ($cmd in ($Commands -split ';;' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })) {
    $i++
    $name = ('{0}_g{1:d2}' -f $Tag, $i)
    $out = Join-Path $logdir ($name + '.stdout.txt')
    $err = Join-Path $logdir ($name + '.stderr.txt')
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $cmd -WorkingDirectory 'H:\rebuild\godot' `
        -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -PassThru
    $p.WaitForExit()
    $sw.Stop()
    $line = ('g{0:d2} exit={1} wall={2:N1}s cmd= {3}' -f $i, $p.ExitCode, $sw.Elapsed.TotalSeconds, $cmd)
    Write-Output $line
    $summary.Add($line)
    $summary.Add(('    stdout=' + $out))
    $summary.Add(('    stderr=' + $err))
    $tail = @()
    if (Test-Path $out) { $tail += (Get-Content $out -Tail 12) }
    if (Test-Path $err) { $e = Get-Content $err -Tail 6; if ($e) { $tail += '  [stderr]'; $tail += $e } }
    foreach ($t in $tail) { Write-Output ('    | ' + $t); $summary.Add('    | ' + $t) }
}
$summaryPath = Join-Path $logdir ($Tag + '.summary.txt')
Set-Content -Path $summaryPath -Value $summary -Encoding UTF8
Write-Output ('summary=' + $summaryPath)
