param(
    [Parameter(Mandatory = $true)][string]$Tag,
    [Parameter(Mandatory = $true)][string]$Commands
)
# TASK-089 gate runner (copy of the task-088 one, plus an explicit exit echo).
# Each gate is a separate cmd.exe child (iron rule 4), each writes its own
# stdout/stderr pair (iron rule 2 - Start-Process, no shell redirection).
# The exit code is echoed INSIDE the cmd child, so it survives even when
# PowerShell cannot read `$p.ExitCode` for a redirected child.
# `$Commands` is ONE string split on `;;`.
$logdir = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs'
if (-not (Test-Path $logdir)) { New-Item -ItemType Directory -Force -Path $logdir | Out-Null }
$summary = New-Object System.Collections.Generic.List[string]
$i = 0
foreach ($cmd in ($Commands -split ';;' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })) {
    $i++
    $name = ('{0}_g{1:d2}' -f $Tag, $i)
    $out = Join-Path $logdir ($name + '.stdout.txt')
    $err = Join-Path $logdir ($name + '.stderr.txt')
    $wrapped = ($cmd + ' & echo TASK089_GATE_EXIT=%ERRORLEVEL%')
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $wrapped -WorkingDirectory 'H:\rebuild\godot' `
        -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -PassThru
    $p.WaitForExit()
    $p.Refresh()
    $sw.Stop()
    $exitLine = ''
    if (Test-Path $out) {
        $m = Select-String -LiteralPath $out -Pattern 'TASK089_GATE_EXIT=(-?\d+)' | Select-Object -Last 1
        if ($m) { $exitLine = $m.Matches[0].Groups[1].Value }
    }
    $line = ('g{0:d2} exit={1} wall={2:N1}s cmd= {3}' -f $i, $exitLine, $sw.Elapsed.TotalSeconds, $cmd)
    Write-Output $line
    $summary.Add($line)
    $summary.Add(('    stdout=' + $out))
    $summary.Add(('    stderr=' + $err))
    $tail = @()
    if (Test-Path $out) { $tail += (Get-Content $out -Tail 14) }
    if (Test-Path $err) { $e = Get-Content $err -Tail 6; if ($e) { $tail += '  [stderr]'; $tail += $e } }
    foreach ($t in $tail) { Write-Output ('    | ' + $t); $summary.Add('    | ' + $t) }
}
$summaryPath = Join-Path $logdir ($Tag + '.summary.txt')
[IO.File]::WriteAllLines($summaryPath, $summary.ToArray())
Write-Output ('summary=' + $summaryPath)
