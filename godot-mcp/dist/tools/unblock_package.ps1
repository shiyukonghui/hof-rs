<#
    unblock_package.ps1  --  remove the Mark-of-the-Web (Zone.Identifier) from an
    extracted package folder. TASK-114 / godot-mcp package support tool.

    THIS IS THE ONLY WRITE THIS TOOL DOES, AND IT IS REVERSIBLE:
      * It calls Unblock-File on the files you point it at.
      * Unblock-File deletes the NTFS alternate data stream named "Zone.Identifier"
        (the "Mark-of-the-Web") and nothing else.
      * It does NOT touch the registry, SAC, SmartScreen, Defender, WDAC, file
        permissions, file contents or file names.

    DRY RUN BY DEFAULT. Without -Apply the script only PRINTS what it would do:
    the full list of files that currently carry a Mark-of-the-Web, and the count.
    Add -Apply to actually unblock them.

    IDEMPOTENT: a file with no Mark-of-the-Web is a no-op. Running it twice is safe;
    the second run reports that there is nothing left to do.

    USAGE
      powershell -ExecutionPolicy Bypass -File unblock_package.ps1 -Path "<extracted folder>"
      powershell -ExecutionPolicy Bypass -File unblock_package.ps1 -Path "<extracted folder>" -Apply

    PARAMETERS
      -Path        The extracted package folder (recursed).
      -Apply       Actually perform the unblock. Without it: dry run.
      -Filter      Optional file filter, default "*" (all files).
      -Json        Emit a single JSON summary instead of the readable report.

    NOTE
      Removing the Mark-of-the-Web does NOT make the package trusted. It only removes
      the "this came from the internet" flag. With Smart App Control in enforcement
      mode, an unsigned binary can still be refused even after unblocking. Read
      dist\README-SAC.md for the three real options before you rely on this script.

      This file is deliberately ASCII-only so that Windows PowerShell 5.1 parses it
      identically no matter what code page / BOM the file is saved with.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Path,
    [switch]$Apply,
    [string]$Filter = "*",
    [switch]$Json
)

Set-StrictMode -Version 2.0

$errors = @()
$root = $null
try {
    $root = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).ProviderPath
} catch {
    $errors += ("path not found: " + $Path)
}

if (-not $Json) {
    Write-Host ""
    Write-Host ("=" * 78)
    Write-Host "unblock_package.ps1 -- Mark-of-the-Web (MOTW) cleanup, TASK-114"
    Write-Host ("=" * 78)
    Write-Host ("mode  : " + $(if ($Apply) { "APPLY (will call Unblock-File)" } else { "DRY RUN (nothing will be changed)" }))
    Write-Host ("folder: " + $Path)
    Write-Host ("filter: " + $Filter)
    Write-Host ""
}

if ($root -eq $null) {
    foreach ($e in $errors) { Write-Host ("ERROR: " + $e) }
    if ($Json) {
        Write-Output (@{ ok = $false; errors = $errors } | ConvertTo-Json -Depth 4)
    }
    exit 1
}

function Test-Motw([string]$FullName) {
    $present = $false
    $zone = $null
    try {
        $null = Get-Item -LiteralPath $FullName -Stream "Zone.Identifier" -ErrorAction Stop
        $present = $true
        try {
            $text = (Get-Content -LiteralPath $FullName -Stream "Zone.Identifier" -ErrorAction Stop) -join " ; "
            foreach ($line in @($text -split " ; ")) {
                $t = $line.Trim()
                if ($t -like "ZoneId=*") { $zone = $t.Substring(7) }
            }
        } catch { }
    } catch {
        $present = $false
    }
    return @{ present = $present; zone = $zone }
}

# ---- 1. enumerate -----------------------------------------------------------
$all = @()
try {
    $all = @(Get-ChildItem -LiteralPath $root -Recurse -File -Filter $Filter -ErrorAction SilentlyContinue)
} catch {
    $errors += ("enumeration failed: " + $_.Exception.Message)
}

# ---- 2. which carry a MOTW --------------------------------------------------
$withMotw = @()
foreach ($f in $all) {
    $m = Test-Motw $f.FullName
    if ($m.present) {
        $withMotw += [pscustomobject]@{ File = $f; Zone = $m.zone }
    }
}

$totalFiles = $all.Count
$motwCount  = $withMotw.Count

if (-not $Json) {
    Write-Host ("files in folder (recursive, filter '" + $Filter + "') : " + $totalFiles)
    Write-Host ("files carrying a Mark-of-the-Web              : " + $motwCount)
    Write-Host ""
    if ($motwCount -eq 0) {
        Write-Host "Nothing to do: no file in this folder carries a Mark-of-the-Web."
        Write-Host "(This is the same result you get on a second run -- the script is idempotent.)"
    } else {
        Write-Host "Files that WILL be unblocked (this is the exact list, by full path):"
        $i = 0
        foreach ($row in $withMotw) {
            $i = $i + 1
            $z = ""
            if ($row.Zone) { $z = "  [ZoneId=" + $row.Zone + "]" }
            Write-Host ("  " + $i.ToString().PadLeft(4) + ". " + $row.File.FullName + $z)
        }
        Write-Host ""
    }
}

# ---- 3. apply (only with -Apply) -------------------------------------------
$unblocked = 0
$failed = @()
if ($Apply -and $motwCount -gt 0) {
    if (-not $Json) {
        Write-Host "Applying Unblock-File ..."
    }
    foreach ($row in $withMotw) {
        try {
            Unblock-File -LiteralPath $row.File.FullName -ErrorAction Stop
            $unblocked = $unblocked + 1
        } catch {
            $failed += ($row.File.FullName + " : " + $_.Exception.Message)
        }
    }
    # verify
    $still = @()
    foreach ($row in $withMotw) {
        $m = Test-Motw $row.File.FullName
        if ($m.present) { $still += $row.File.FullName }
    }
    if (-not $Json) {
        Write-Host ("Unblock-File succeeded on : " + $unblocked + " / " + $motwCount)
        Write-Host ("still carrying a MOTW     : " + $still.Count)
        if ($failed.Count -gt 0) {
            Write-Host "Failures:"
            foreach ($f in $failed) { Write-Host ("  " + $f) }
        }
    }
    $errors += $failed
} elseif (-not $Apply -and $motwCount -gt 0 -and -not $Json) {
    Write-Host "DRY RUN -- nothing was changed."
    Write-Host "To actually remove the Mark-of-the-Web from the files listed above, re-run with:"
    Write-Host ("  powershell -ExecutionPolicy Bypass -File unblock_package.ps1 -Path `"" + $root + "`" -Apply")
    Write-Host ""
    Write-Host "Reminder: this only removes the 'came from the internet' flag. It does not"
    Write-Host "sign anything and it does not turn Smart App Control off. See README-SAC.md."
}

if ($Json) {
    $out = [ordered]@{
        ok            = ($errors.Count -eq 0)
        mode          = $(if ($Apply) { "apply" } else { "dry-run" })
        folder        = $root
        filter        = $Filter
        files_total   = $totalFiles
        with_motw     = $motwCount
        unblocked     = $unblocked
        targets       = @($withMotw | ForEach-Object { $_.File.FullName })
        errors        = $errors
    }
    Write-Output ($out | ConvertTo-Json -Depth 4)
}
