# DR-72 forbidden-zone self-check.
#
# Reproduces the T8/T9/T10 digest convention verbatim: PowerShell 5.1
# (culture zh-CN) Get-ChildItem -Recurse -Force -File, repo-root-relative
# lowercase POSIX path + byte length + lowercase SHA256, tab-joined,
# newline-separated, NO trailing newline, lines sorted with Sort-Object
# (culture sort is part of the convention), whole text UTF-8 -> SHA256.
#
# It only reads.  It writes nothing, anywhere.
[CmdletBinding()]
param(
    [string[]]$Runs = @(
        'runs/smoke-t6',
        'runs/smoke-t7',
        'runs/smoke-t8',
        'runs/smoke-t9',
        'runs/smoke-t10'
    )
)

$repo = (Get-Item -LiteralPath $PSScriptRoot/..).FullName
foreach ($run in $Runs) {
    $root = Join-Path $repo $run
    if (-not (Test-Path -LiteralPath $root)) {
        Write-Output ("{0}  MISSING" -f $run)
        continue
    }
    $lines = New-Object System.Collections.Generic.List[string]
    $files = Get-ChildItem -LiteralPath $root -Recurse -Force -File -ErrorAction SilentlyContinue
    foreach ($file in $files) {
        $relative = $file.FullName.Substring($repo.Length + 1).Replace('\', '/').ToLowerInvariant()
        $bytes = [System.IO.File]::ReadAllBytes($file.FullName)
        $sha = [System.Security.Cryptography.SHA256]::Create()
        try {
            $digest = $sha.ComputeHash($bytes)
        } finally {
            $sha.Dispose()
        }
        $hex = ([System.BitConverter]::ToString($digest)).Replace('-', '').ToLowerInvariant()
        $lines.Add(("{0}`t{1}`t{2}" -f $relative, $bytes.Length, $hex))
    }
    $sorted = $lines | Sort-Object
    $payload = [string]::Join("`n", $sorted)
    $outer = [System.Security.Cryptography.SHA256]::Create()
    try {
        $whole = $outer.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($payload))
    } finally {
        $outer.Dispose()
    }
    $wholeHex = ([System.BitConverter]::ToString($whole)).Replace('-', '').ToLowerInvariant()
    $newest = ($files | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
    Write-Output ("{0}  {1}  {2}  newest {3:yyyy-MM-dd HH:mm:ss}" -f $run, $files.Count, $wholeHex, $newest)
}
