$ErrorActionPreference = 'Stop'
$files = @(
    'F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\scripts\mcp029_clear_default_evidence.ps1',
    'F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\scripts\mcp032_d3_d4_d6_evidence.ps1'
)
Write-Host '=== PowerShell 5.1 file encoding probes ==='
Write-Host ('[Console]::OutputEncoding     = ' + [Console]::OutputEncoding.WebName)
Write-Host ('[Text.Encoding]::Default      = ' + [Text.Encoding]::Default.WebName)
Write-Host ('Default ANSI code page        = ' + (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Nls\CodePage').ACP)
Write-Host ''
foreach ($f in $files) {
    $bytes = [IO.File]::ReadAllBytes($f)
    $bom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
    $nonAscii = @($bytes | Where-Object { $_ -gt 0x7F }).Count
    Write-Host ('--- ' + (Split-Path $f -Leaf))
    Write-Host ('    bytes={0}  BOM={1}  non-ASCII bytes={2}' -f $bytes.Length, $bom, $nonAscii)
    # decode the way PS 5.1 parses a BOM-less file, then look for the integer
    # escapes the header comment block uses
    $ansiText = [Text.Encoding]::Default.GetString($bytes)
    foreach ($needle in @('0x5171', '0x4EAB')) {
        $idx = $ansiText.IndexOf($needle)
        $context = ''
        if ($idx -ge 0) { $context = $ansiText.Substring($idx, 24) }
        Write-Host ('    ANSI-decoded contains "{0}": {1}   [{2}]' -f $needle, ($idx -ge 0), $context)
    }
    # are the escapes still inside a comment line under the ANSI decode?
    $badLine = -1
    $lineNo = 0
    foreach ($line in ($ansiText -split "`n")) {
        $lineNo++
        if (($line.IndexOf('0x5171') -ge 0 -or $line.IndexOf('0x4EAB') -ge 0) -and ($line.TrimStart() -notlike '#*')) {
            $badLine = $lineNo
            Write-Host ('    WARNING: integer escape outside a comment at line {0}: {1}' -f $lineNo, $line.Trim())
        }
    }
    if ($badLine -lt 0) { Write-Host '    OK: both escapes still sit inside `#` comment lines under an ANSI decode' }
}
