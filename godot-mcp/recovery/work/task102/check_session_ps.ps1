param([Parameter(Mandatory=$true)][string]$Session, [Parameter(Mandatory=$true)][string]$Out)
# TASK-099: the second half of the iron-rule-5 double parse -- Windows PowerShell
# 5.1's own ConvertFrom-Json, on the same bytes. Writes with .NET (no shell
# redirection anywhere).
$ErrorActionPreference = 'Stop'
$raw = [System.IO.File]::ReadAllText($Session)
$doc = $raw | ConvertFrom-Json
$calls = @($doc.calls)
$ports = @{}
foreach ($c in $calls) {
  if ($c.PSObject.Properties.Name -contains 'sleep_ms') { continue }
  $p = "$($c.port)"
  if ($ports.ContainsKey($p)) { $ports[$p] = $ports[$p] + 1 } else { $ports[$p] = 1 }
}
$lines = @()
$lines += ('PS_PARSE OK: {0}' -f $Session)
$lines += ('PS_PARSE calls={0} editor={1} game={2} import={3}' -f $calls.Count, $ports['editor'], $ports['game'], $doc.import)
[System.IO.File]::WriteAllLines($Out, $lines)
Write-Host ($lines -join [Environment]::NewLine)
