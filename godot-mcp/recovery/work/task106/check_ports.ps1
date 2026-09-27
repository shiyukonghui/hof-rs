param(
  [string]$PortList = '9888 9889 9930 9931'
)
# TASK-106 iron rule 4: before any engine is started, show what is already running
# and which of the ports this task intends to use is occupied. Read-only.
#
# `-File` hands a comma list to PowerShell as one string, so the ports arrive
# space separated and are split here rather than through a typed [int[]] parameter.
$ErrorActionPreference = 'Continue'
$Ports = @($PortList -split '[ ,;]+' | Where-Object { $_ -ne '' } | ForEach-Object { [int]$_ })
Write-Output '--- processes named Godot* / dotnet ---'
$procs = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'Godot*' -or $_.ProcessName -like 'dotnet*' }
if (-not $procs) { Write-Output '  (none)' } else {
  foreach ($p in $procs) { Write-Output ("  {0,-8} pid={1}" -f $p.ProcessName, $p.Id) }
}
Write-Output '--- listening ports of interest ---'
$lines = netstat -ano -p TCP
$any = $false
foreach ($port in $Ports) {
  $hits = @($lines | Select-String -SimpleMatch (':' + $port))
  $listen = @($hits | Where-Object { "$_".Trim().StartsWith('TCP') -and "$_" -match 'LISTENING\s+\d+$' })
  if ($listen.Count -gt 0) {
    $any = $true
    foreach ($l in $listen) { Write-Output ("  {0} OCCUPIED  {1}" -f $port, "$l".Trim()) }
  } else {
    Write-Output ("  {0} free" -f $port)
  }
}
if ($any) { Write-Output 'PORT_CHECK: at least one wanted port is OCCUPIED' } else { Write-Output 'PORT_CHECK: all wanted ports free' }
