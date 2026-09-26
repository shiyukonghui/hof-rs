# parse_check_ps1.ps1 - TASK-078 read-only PowerShell *parser* check over staged .ps1 files.
# Uses [System.Management.Automation.Language.Parser]::ParseFile (no execution).
# Writes the result table to C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\ps1-parse.json
# Pure ASCII. No shell redirection.
$ErrorActionPreference = 'Stop'
$ST = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging'
$Out = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\ps1-parse.json'

$files = Get-ChildItem -LiteralPath $ST -Recurse -File -Filter *.ps1 |
    Where-Object { $_.FullName -notlike '*\__history\*' -and $_.FullName -notlike '*\__candidates\*' -and $_.FullName -notlike '*\__diffs\*' }
$rows = New-Object System.Collections.ArrayList
foreach ($f in $files) {
    $tokens = $null; $errors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$tokens, [ref]$errors)
    $msgs = @()
    if ($errors) { foreach ($e in $errors) { $msgs += ($e.ErrorId + ':' + $e.Message) } }
    $rel = $f.FullName.Substring($ST.Length + 1)
    [void]$rows.Add([pscustomobject]@{ rel = $rel; bytes = $f.Length; parseErrors = $msgs.Count; first = ($msgs | Select-Object -First 1) })
}
$bad = $rows | Where-Object { $_.parseErrors -gt 0 }
Write-Output ("ps1 files checked: " + $rows.Count)
Write-Output ("with parse errors: " + $bad.Count)
foreach ($b in ($bad | Sort-Object rel)) { Write-Output ("  " + $b.rel + "  [" + $b.parseErrors + "] " + $b.first) }
[System.IO.File]::WriteAllText($Out, ($rows | ConvertTo-Json -Depth 4), (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("wrote " + $Out)
