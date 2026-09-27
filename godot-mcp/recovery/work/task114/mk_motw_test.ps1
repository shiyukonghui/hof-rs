# TASK-114 -- create a THROWAWAY fixture that has a Mark-of-the-Web, so that the
# toolkit's MOTW detection and its -Apply path can be tested for real.
# Everything it touches lives under recovery\work\task114\motw_test\ (scratch).
$ErrorActionPreference = "Stop"
$dir = Join-Path $PSScriptRoot "motw_test"
if (Test-Path -LiteralPath $dir) { Remove-Item -LiteralPath $dir -Recurse -Force }
New-Item -ItemType Directory -Path $dir | Out-Null

# two "package" files
Set-Content -LiteralPath (Join-Path $dir "fake_game.exe")  -Value "not a real exe" -Encoding ASCII
Set-Content -LiteralPath (Join-Path $dir "fake_core.dll") -Value "not a real dll" -Encoding ASCII
# one file that we will leave clean, to prove the script does not over-reach
Set-Content -LiteralPath (Join-Path $dir "clean.txt")      -Value "no motw here"    -Encoding ASCII

# give the two package files a Zone.Identifier stream (this IS the Mark-of-the-Web)
foreach ($n in @("fake_game.exe", "fake_core.dll")) {
    $p = Join-Path $dir $n
    $zone = "[ZoneTransfer]`r`nZoneId=3`r`nReferrerUrl=https://example.invalid/pkg.zip`r`nHostUrl=https://example.invalid/pkg.zip`r`n"
    Set-Content -LiteralPath $p -Stream "Zone.Identifier" -Value $zone -Encoding ASCII
}

Write-Host ("fixture created: " + $dir)
Get-ChildItem -LiteralPath $dir -File | ForEach-Object {
    $has = $false
    try { $null = Get-Item -LiteralPath $_.FullName -Stream "Zone.Identifier" -ErrorAction Stop; $has = $true } catch { }
    Write-Host ("  " + $_.Name.PadRight(16) + " MOTW=" + $has)
}
