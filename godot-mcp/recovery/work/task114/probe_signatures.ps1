$ErrorActionPreference = "Continue"
Write-Host "=== 1. official Godot 4.7.1 editor folder tree ==="
Get-ChildItem -LiteralPath "D:\Program Files\Godot_v4.7.1-stable_mono_win64" -Recurse -File |
    ForEach-Object { Write-Host ("  " + $_.FullName) }

Write-Host ""
Write-Host "=== 2. installed export templates ==="
$tplRoot = "C:\Users\wyl\AppData\Roaming\Godot\export_templates"
Get-ChildItem -LiteralPath $tplRoot -Recurse -File |
    ForEach-Object {
        $sig = $null
        try { $sig = Get-AuthenticodeSignature -LiteralPath $_.FullName } catch { }
        $st = "-"
        if ($sig) { $st = [string]$sig.Status }
        Write-Host ("  " + $st.PadRight(12) + $_.Length.ToString().PadLeft(10) + "  " + $_.FullName)
    }

Write-Host ""
Write-Host "=== 3. self-check: what this script just proved ==="
Write-Host "  (see the two sections above)"
