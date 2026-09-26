# patch_dryrun2.ps1 - ordered dry run: pristine baseline -> patch1 -> patch2 -> patch3,
# inside an isolated sandbox under mcp-recovery\work.  Never touches rebuild\godot or F:.
$ErrorActionPreference = 'Continue'
$R = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
$SB = Join-Path $R 'work\patchdry2'
$G = Join-Path $R 'rebuild\godot'
$AE = Join-Path $env:TEMP 'audit-engine'

if (Test-Path -LiteralPath $SB) {
    $items = @(Get-ChildItem -LiteralPath $SB -Recurse -Force)
    Write-Output ('GUARDED CLEAN: target=' + $SB + ' items=' + $items.Count)
    foreach ($i in ($items | Select-Object -First 20)) { Write-Output ('  WOULD DELETE ' + $i.FullName) }
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

function Snap([string]$label) {
    Write-Output ('--- ' + $label)
    foreach ($f in @('core\config\project_settings.cpp', 'core\config\project_settings.h',
                     'editor\editor_node.cpp', 'modules\mono\csharp_script.cpp',
                     'modules\mono\csharp_script.h')) {
        $p = Join-Path $SB $f
        $i = Get-Item -LiteralPath $p
        $h = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower()
        $lines = (Get-Content -LiteralPath $p | Measure-Object -Line).Lines
        Write-Output ('    ' + $f.PadRight(42) + ' bytes=' + $i.Length.ToString().PadLeft(8) + ' lines=' + $lines.ToString().PadLeft(7) + ' sha256=' + $h)
    }
}

Snap 'PRISTINE (audit002 baseline copy)'
$seq = @(
    @{ id = 'patch1'; f = Join-Path $AE 'diff-patch1.txt' },
    @{ id = 'patch2'; f = Join-Path $AE 'diff-patch2.txt' },
    @{ id = 'patch3'; f = Join-Path $AE 'diff-patch3.txt' }
)
foreach ($s in $seq) {
    $o = & git -C $SB apply -p1 --whitespace=nowarn $s.f
    Write-Output ('APPLY ' + $s.id + ' exit=' + $LASTEXITCODE + '  ' + (($o -join ' ') -replace "`n", ' '))
    Snap ('AFTER ' + $s.id)
}
