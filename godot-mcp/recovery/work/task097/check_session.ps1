param([Parameter(Mandatory=$true)][string]$Session)
# TASK-097: the PowerShell 5.1 half of the double parse (iron rule: a session
# file is only run after BOTH the Python checker and PS 5.1 have read it).
$ErrorActionPreference = 'Stop'
$doc = Get-Content -LiteralPath $Session -Raw -Encoding UTF8 | ConvertFrom-Json
$calls = @($doc.calls)
if ($calls.Count -eq 0) { throw "REFUSED: no calls in $Session" }
$ports = @{}
foreach ($c in $calls) {
  if ($c.sleep_ms) { continue }
  if (-not $c.tag) { throw "REFUSED: a call without a tag" }
  if (-not $c.tool -and -not $c.method) { throw "REFUSED: call '$($c.tag)' has neither tool nor method" }
  foreach ($k in @($c.arguments.PSObject.Properties.Name)) {
    if ($k -eq 'content_file') {
      $target = Join-Path (Split-Path -Parent (Resolve-Path -LiteralPath $Session).Path) $c.arguments.content_file
      if (-not (Test-Path -LiteralPath $target)) { throw "REFUSED: '$($c.tag)'.content_file not found: $target" }
    }
  }
  $p = "$($c.port)"
  if ($p -notin @('editor', 'game')) { throw "REFUSED: call '$($c.tag)' has port '$p'" }
  if ($ports.ContainsKey($p)) { $ports[$p]++ } else { $ports[$p] = 1 }
}
Write-Output ("PS5.1 OK: {0} calls, ports={1}, import={2}" -f $calls.Count, (($ports.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join ','), $doc.import)
