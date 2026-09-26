# patch dry-run in an isolated sandbox under mcp-recovery\work (never touches rebuild\godot or F:)
$ErrorActionPreference = 'Continue'
$R = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
$SB = Join-Path $R 'work\patchdry'
$G = Join-Path $R 'rebuild\godot'
$T = $env:TEMP
$AE = Join-Path $T 'audit-engine'

# fresh sandbox: print the delete list before removing (guarded destruction)
if (Test-Path -LiteralPath $SB) {
    $items = @(Get-ChildItem -LiteralPath $SB -Recurse -Force)
    Write-Output ('GUARDED CLEAN: target=' + $SB + ' items=' + $items.Count)
    foreach ($i in ($items | Select-Object -First 20)) { Write-Output ('  WOULD DELETE ' + $i.FullName) }
    if ($items.Count -gt 20) { Write-Output ('  ... and ' + ($items.Count - 20) + ' more') }
    if (-not $SB.StartsWith($R + '\')) { throw 'sandbox outside mcp-recovery' }
    if ($SB -match '[\*\?]' -or $SB.Contains('..')) { throw 'unsafe sandbox path' }
    Remove-Item -LiteralPath $SB -Recurse -Force
}

$files = @(
    'core\config\project_settings.cpp',
    'core\config\project_settings.h',
    'editor\editor_node.cpp',
    'modules\mono\csharp_script.cpp',
    'modules\mono\csharp_script.h'
)
foreach ($f in $files) {
    $dst = Join-Path $SB $f
    $dir = Split-Path $dst -Parent
    if (-not (Test-Path -LiteralPath $dir)) { [void](New-Item -ItemType Directory -Path $dir -Force) }
    Copy-Item -LiteralPath (Join-Path $G $f) -Destination $dst -Force
}
Write-Output ('sandbox populated: ' + $files.Count + ' files under ' + $SB)

$patches = @(
    @{ id = 'patch1'; file = Join-Path $AE 'diff-patch1.txt' },
    @{ id = 'patch2'; file = Join-Path $AE 'diff-patch2.txt' },
    @{ id = 'patch3'; file = Join-Path $AE 'diff-patch3.txt' }
)

function Try-Apply([string]$patch, [string]$mode) {
    $out = & git -C $SB apply $mode -p1 --verbose --whitespace=nowarn $patch
    $code = $LASTEXITCODE
    return [pscustomobject]@{ code = $code; out = ($out -join "`n") }
}

foreach ($p in $patches) {
    $short = $p.file.Substring($AE.Length + 1)
    $r = Try-Apply $p.file '--check'
    Write-Output ('CHECK ' + $p.id + ' (' + $short + ') exit=' + $r.code)
    if ($r.code -ne 0) { Write-Output ('   ' + ($r.out -replace "`n", "`n   ")) }
}

# now really apply patch2 inside the sandbox, then re-check patch3
$r2 = Try-Apply (Join-Path $AE 'diff-patch2.txt') ''
Write-Output ('APPLY patch2 in sandbox exit=' + $r2.code)
if ($r2.code -ne 0) { Write-Output ('   ' + ($r2.out -replace "`n", "`n   ")) }
$r3 = Try-Apply (Join-Path $AE 'diff-patch3.txt') '--check'
Write-Output ('CHECK patch3 after patch2 exit=' + $r3.code)
if ($r3.code -ne 0) { Write-Output ('   ' + ($r3.out -replace "`n", "`n   ")) }
Write-Output ('sandbox hashes after patch2:')
foreach ($f in @('core\config\project_settings.cpp', 'core\config\project_settings.h')) {
    $h = (Get-FileHash -LiteralPath (Join-Path $SB $f) -Algorithm SHA256).Hash.ToLower()
    Write-Output ('   ' + $f + ' sha256=' + $h + ' bytes=' + (Get-Item -LiteralPath (Join-Path $SB $f)).Length)
}
