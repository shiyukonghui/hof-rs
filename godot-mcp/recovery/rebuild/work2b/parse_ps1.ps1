
param([string]$Root, [string]$OutFile)
$ErrorActionPreference = 'Stop'
$rows = @()
$files = Get-ChildItem -Path $Root -Recurse -File -Include *.ps1 -ErrorAction SilentlyContinue
foreach ($f in $files) {
    $errs = @()
    $tokens = $null
    $parseErrors = $null
    try {
        [void][System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$tokens, [ref]$parseErrors)
        if ($parseErrors) { foreach ($e in $parseErrors) { $errs += ($e.ErrorId + ':' + $e.Message + '@' + $e.Extent.StartLineNumber) } }
    } catch {
        $errs += ('EXCEPTION:' + $_.Exception.Message)
    }
    $rel = $f.FullName.Substring($Root.Length).TrimStart('\')
    $rows += [pscustomobject]@{ rel = $rel; bytes = $f.Length; parseErrors = $errs.Count; errors = $errs }
}
[IO.File]::WriteAllText($OutFile, ($rows | ConvertTo-Json -Depth 6), (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("ps1 scanned=" + $rows.Count + " withErrors=" + (@($rows | Where-Object { $_.parseErrors -gt 0 })).Count)
