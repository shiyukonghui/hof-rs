param(
  [Parameter(Mandatory=$true)][string]$Path,
  [Parameter(Mandatory=$true)][string]$Out
)
# Parse a .ps1 with the PowerShell language parser and dump every error as JSON.
# No shell redirection: Set-Content -Encoding UTF8 writes the file.
$ErrorActionPreference = 'Stop'
$errors = @()
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$parseErrors)
foreach ($e in $parseErrors) {
  $errors += [pscustomobject]@{
    line     = $e.Extent.StartLineNumber
    col      = $e.Extent.StartColumnNumber
    endLine  = $e.Extent.EndLineNumber
    errorId  = $e.ErrorId
    message  = $e.Message
    text     = $e.Extent.Text
  }
}
$payload = [pscustomobject]@{
  path        = $Path
  bytes       = (Get-Item $Path).Length
  lines       = (Get-Content -LiteralPath $Path -Encoding UTF8 | Measure-Object -Line).Lines
  errorCount  = $errors.Count
  errors      = $errors
}
$json = $payload | ConvertTo-Json -Depth 6
Set-Content -LiteralPath $Out -Value $json -Encoding UTF8
Write-Output ("errors=" + $errors.Count + " -> " + $Out)
