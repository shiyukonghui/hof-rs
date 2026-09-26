param(
    [Parameter(Mandatory = $true)][string]$ArgLine,
    [Parameter(Mandatory = $true)][string]$Tag
)
$ErrorActionPreference = 'Continue'
$log = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs'
$out = Join-Path $log ($Tag + '.stdout.txt')
$err = Join-Path $log ($Tag + '.stderr.txt')
$wd = 'H:\rebuild\godot'
$exe = Join-Path $wd 'bin\godot.windows.editor.x86_64.exe'
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$p = Start-Process -FilePath $exe -ArgumentList $ArgLine -WorkingDirectory $wd -NoNewWindow -Wait -PassThru `
    -RedirectStandardOutput $out -RedirectStandardError $err
$sw.Stop()
Write-Output ("tag=$Tag")
Write-Output ("exe=$exe")
Write-Output ("args=$ArgLine")
Write-Output ("exit={0}" -f $p.ExitCode)
Write-Output ("wall_seconds={0:N1}" -f $sw.Elapsed.TotalSeconds)
Write-Output ("stdout=$out")
Write-Output ("stderr=$err")
