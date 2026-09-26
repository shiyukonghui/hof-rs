# parse_check_rebuild_ps1.ps1 - TASK-079: PowerShell *parser* check over EVERY .ps1 in the
# rebuild tree (+ rebuild\_low-confidence + the TASK-078 staging set, for the comparison with
# the 433/10 number).  Parses only, never executes.  ASCII only.  No shell redirection.
$ErrorActionPreference = 'Stop'
$R = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
$Out = Join-Path $R 'work\parse-ps1-rebuild.json'

$roots = @(
    @{ tag = 'godot';            path = (Join-Path $R 'rebuild\godot') },
    @{ tag = '_low-confidence';  path = (Join-Path $R 'rebuild\_low-confidence') },
    @{ tag = 'staging';          path = (Join-Path $R 'staging') }
)

$report = New-Object System.Collections.ArrayList
foreach ($root in $roots) {
    $rows = New-Object System.Collections.ArrayList
    if (-not (Test-Path -LiteralPath $root.path)) {
        [void]$report.Add([pscustomobject]@{ tag = $root.tag; missing = $true })
        continue
    }
    $files = Get-ChildItem -LiteralPath $root.path -Recurse -File -Filter *.ps1 -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notlike '*\__history\*' -and $_.FullName -notlike '*\__candidates\*' -and $_.FullName -notlike '*\__diffs\*' }
    foreach ($f in $files) {
        $tokens = $null; $errors = $null
        [void][System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$tokens, [ref]$errors)
        $msgs = @()
        $lines = @()
        if ($errors) {
            foreach ($e in $errors) {
                $msgs += ($e.ErrorId + ':' + $e.Message)
                $lines += ($e.Extent.StartLineNumber)
            }
        }
        $rel = $f.FullName.Substring($root.path.Length + 1)
        [void]$rows.Add([pscustomobject]@{
            rel = $rel; bytes = $f.Length; parseErrors = $msgs.Count;
            lines = $lines; first = ($msgs | Select-Object -First 1)
        })
    }
    $bad = @($rows | Where-Object { $_.parseErrors -gt 0 })
    [void]$report.Add([pscustomobject]@{
        tag = $root.tag; root = $root.path; missing = $false;
        total_ps1 = $rows.Count; with_errors = $bad.Count;
        failures = @($bad | Sort-Object rel)
    })
    Write-Output ($root.tag + ': .ps1 checked = ' + $rows.Count + ', with parse errors = ' + $bad.Count)
    foreach ($b in ($bad | Sort-Object rel)) {
        Write-Output ('    line ' + (($b.lines | Select-Object -First 1)) + '  ' + $b.rel + '  [' + $b.parseErrors + '] ' + $b.first)
    }
}

[System.IO.File]::WriteAllText($Out, ($report | ConvertTo-Json -Depth 6), (New-Object System.Text.UTF8Encoding($false)))
Write-Output ('wrote ' + $Out)
