# TASK-081 parse sweep for .ps1 (parse only, never executed). Pure ASCII.
param(
  [Parameter(Mandatory=$true)][string]$Root,
  [Parameter(Mandatory=$true)][string]$Out
)
$files = Get-ChildItem -Path $Root -Recurse -File -Filter *.ps1
$results = @()
$total = 0
$bad = 0
foreach ($f in $files) {
  $total++
  $tokens = $null
  $errors = $null
  [void][System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$tokens, [ref]$errors)
  if ($errors.Count -gt 0) {
    $bad++
    $first = $errors[0]
    $results += [pscustomobject]@{
      path  = $f.FullName.Substring($Root.Length).TrimStart('\')
      count = $errors.Count
      line  = $first.Extent.StartLineNumber
      msg   = $first.Message
    }
  }
}
$summary = [pscustomobject]@{ root = $Root; total = $total; ok = ($total - $bad); failed = $bad; details = $results }
$json = $summary | ConvertTo-Json -Depth 5
[IO.File]::WriteAllText($Out, $json, (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("ps1 total=" + $total + " ok=" + ($total - $bad) + " failed=" + $bad)
foreach ($r in $results) { Write-Output ("FAIL " + $r.path + " @" + $r.line + " (" + $r.count + ") " + $r.msg) }
