param(
    [Parameter(Mandatory = $true)][string]$Tag
)
# TASK-088: run the minimal C# project with the mono editor binary and capture
# the marker the C# script prints. cmd.exe child (iron rule 4), Start-Process
# writes the log (iron rule 2).
$logdir = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs'
$out = Join-Path $logdir ($Tag + '.stdout.txt')
$err = Join-Path $logdir ($Tag + '.stderr.txt')
$exe = 'H:\rebuild\godot\bin\godot.windows.editor.x86_64.mono.console.exe'
$proj = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task088\csharp-proj'
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', ('"' + $exe + '" --headless --path ' + $proj + ' --quit-after 600') `
    -WorkingDirectory 'H:\rebuild\godot' -NoNewWindow -PassThru `
    -RedirectStandardOutput $out -RedirectStandardError $err
$p.WaitForExit()
$sw.Stop()
Write-Output ("tag=$Tag")
Write-Output ("exit=" + $p.ExitCode)
Write-Output ("wall_seconds=" + [math]::Round($sw.Elapsed.TotalSeconds, 1))
Write-Output ("stdout=$out")
Write-Output ("stderr=$err")
