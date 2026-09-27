# TASK-117 step A0: iron rule 4 (check processes and ports before touching anything)
# and the non-destructive archiving of the pre-fix TASK-109 exports.
#
# The TASK-109 exports are the artifacts the user actually played (made before the
# TASK-116 input fix).  They are MOVED aside, never deleted, so the report can cite
# the before/after hashes of the same path.
$ErrorActionPreference = 'Continue'
$Root = 'F:\moonbit-hof-rs\godot-mcp'
$Dist = Join-Path $Root 'dist'

Write-Output '=== PORTS (must all be free) ==='
foreach ($p in 9877, 9888, 9889, 19401, 19420, 19501) {
    $hits = @(Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue)
    Write-Output ("port {0,-6} listeners={1}" -f $p, $hits.Count)
}
Write-Output '=== PROCESSES (no godot may be running) ==='
$gp = @(Get-Process -Name 'godot*' -ErrorAction SilentlyContinue)
Write-Output ("godot processes={0}" -f $gp.Count)
foreach ($x in $gp) { Write-Output ("  pid={0} name={1}" -f $x.Id, $x.ProcessName) }

Write-Output '=== ARCHIVE the pre-fix exports (move, not delete) ==='
$old = Join-Path $Dist 'exe'
$arch = Join-Path $Dist 'exe-task109-pre-fix'

# Record what the user actually played, before it moves: same path, before/after.
$pre = New-Object System.Collections.ArrayList
if (Test-Path $old) {
    foreach ($d in (Get-ChildItem $old -Directory)) {
        $g = $d.Name
        $exe = Join-Path $d.FullName ("$g.exe")
        $pck = Join-Path $d.FullName ("$g.pck")
        $dll = Join-Path $d.FullName ("data_{0}_windows_x86_64\{0}.dll" -f $g)
        $rec = [ordered]@{ game = $g; dir = $d.FullName }
        foreach ($pair in @(@('exe', $exe), @('pck', $pck), @('dll', $dll))) {
            $k = $pair[0]; $f = $pair[1]
            if (Test-Path $f) {
                $rec[$k + '_bytes'] = (Get-Item $f).Length
                $rec[$k + '_sha256'] = (Get-FileHash $f -Algorithm SHA256).Hash.ToLower()
            } else {
                $rec[$k + '_bytes'] = $null
                $rec[$k + '_sha256'] = $null
            }
        }
        [void]$pre.Add([pscustomobject]$rec)
        Write-Output ("PRE-FIX {0,-16} exe={1} pck={2} dll={3}" -f $g, $rec.exe_sha256, $rec.pck_sha256, $rec.dll_sha256)
    }
    $pre | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $Root 'recovery\work\task117\pre-fix-hashes.json') -Encoding utf8
    Write-Output ("pre-fix hashes recorded for {0} games" -f $pre.Count)
}

if (Test-Path $old) {
    if (Test-Path $arch) {
        Write-Output ("archive already exists, leaving it alone: {0}" -f $arch)
    } else {
        Move-Item -Path $old -Destination $arch
        Write-Output ("MOVED {0} -> {1}" -f $old, $arch)
    }
} else {
    Write-Output ("nothing to archive at {0}" -f $old)
}
$n = 0
if (Test-Path $arch) { $n = @(Get-ChildItem $arch -Directory).Count }
Write-Output ("archived game dirs={0}" -f $n)
Write-Output ("dist\exe exists now={0}" -f (Test-Path $old))
