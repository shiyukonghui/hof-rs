<#
    sac_diagnose.ps1  --  READ-ONLY Smart App Control (SAC) diagnostics
    TASK-114 / godot-mcp package support tool.

    WHAT IT DOES (all read-only):
      1. Prints the Microsoft Smart App Control policy state
         (HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy -> VerifiedAndReputablePolicyState)
         and explains what 0 / 1 / 2 mean.
      2. Reads the recent Microsoft-Windows-CodeIntegrity/Operational events that
         name files shipped inside YOUR extracted package (match by file name and by
         full path), and prints their event id, time and message.
      3. Samples the .exe / .dll files in your extracted package and reports, per file:
         Authenticode status + signer subject, and the Mark-of-the-Web (Zone.Identifier)
         state if present.
      4. Prints how to read the "blocked process" error text itself.

    WHAT IT DOES **NOT** DO:
      * It never writes to the registry, never changes SAC / Defender / WDAC settings,
        never calls Unblock-File, never deletes or moves anything.
      * Every cmdlet used is a Get-* / Read-* cmdlet or a WMI query.

    USAGE
      powershell -ExecutionPolicy Bypass -File sac_diagnose.ps1 -PackagePath "<extracted folder>"
      powershell -ExecutionPolicy Bypass -File sac_diagnose.ps1 -PackagePath "<dir>" -Json

    PARAMETERS
      -PackagePath   Folder that contains the extracted exe/dll files (for example the
                     folder you unzipped one game into). If omitted, only steps 1, 2 and 4
                     run and step 3 is skipped.
      -MaxEvents     How many recent CodeIntegrity events to pull (default 800).
      -AllEvents     Also print the full text of CI events that do NOT name a file in
                     your package. Without it (and with -PackagePath given) only the
                     package-matching events are printed in full, and the unrelated ones
                     are summarised -- otherwise the Windows-farm noise drowns the answer.
      -Json          Emit a single JSON object instead of the readable report.
      -Sample        Max exe/dll files to signature-check (default 40). Use 0 for all.

    NOTES
      * Reading Microsoft-Windows-CodeIntegrity/Operational normally needs an elevated
        shell. Without elevation this section reports "not readable" and the rest still runs.
      * This file is deliberately ASCII-only so that Windows PowerShell 5.1 parses it
        identically no matter what code page / BOM the file is saved with.
#>

[CmdletBinding()]
param(
    [string]$PackagePath = "",
    [int]$MaxEvents = 800,
    [int]$Sample = 40,
    [switch]$AllEvents,
    [switch]$Json
)

Set-StrictMode -Version 2.0

$script:Report = [ordered]@{
    tool         = "sac_diagnose.ps1"
    task         = "TASK-114"
    mode         = "read-only"
    generated_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    machine      = $env:COMPUTERNAME
    user         = "$env:USERDOMAIN\$env:USERNAME"
    elevated     = $false
    sac          = $null
    events       = @()
    package      = $null
    errors       = @()
}

function Add-Error([string]$Message) {
    $script:Report.errors += $Message
}

function Write-Head([string]$Text) {
    Write-Host ""
    Write-Host ("=" * 78)
    Write-Host $Text
    Write-Host ("=" * 78)
}

# ---------------------------------------------------------------- elevation
$isAdmin = $false
try {
    $identity  = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    $isAdmin   = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
} catch {
    Add-Error ("elevation check failed: " + $_.Exception.Message)
}
$script:Report.elevated = $isAdmin

# ---------------------------------------------------------------- 1. SAC state
$sacPath  = "HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy"
$sacName  = "VerifiedAndReputablePolicyState"
$sacValue = $null
$sacFound = $false
$sacReadError = ""

try {
    $props = Get-ItemProperty -Path $sacPath -ErrorAction Stop
    if ($props.PSObject.Properties.Name -contains $sacName) {
        $sacValue = [int]$props.$sacName
        $sacFound = $true
    }
} catch {
    $sacReadError = $_.Exception.Message
}

$sacMeaning = "value absent: the SAC policy value is not present on this machine"
$sacShort   = "absent"
switch ($sacValue) {
    0 { $sacMeaning = "0 = OFF. Smart App Control is disabled. Unsigned or low-reputation binaries are not blocked by SAC on this machine."; $sacShort = "off" }
    1 { $sacMeaning = "1 = ON (enforcement). Smart App Control is enforcing: unsigned / low-reputation code that was downloaded from the internet is blocked."; $sacShort = "on-enforcement" }
    2 { $sacMeaning = "2 = EVALUATION. Smart App Control is in its automatic evaluation phase; it observes and decides, but does not yet block."; $sacShort = "evaluation" }
    default {
        if ($sacFound) {
            $sacMeaning = "unexpected value $sacValue (only 0, 1 and 2 are defined)"
            $sacShort   = "unknown"
        }
    }
}

# Which of the shipped files were downloaded from the internet is a separate question from
# SAC being on. SAC only sees files that carry a Mark-of-the-Web (Zone.Identifier).
$script:Report.sac = [ordered]@{
    registry_path = $sacPath
    value_name    = $sacName
    value         = $sacValue
    present       = $sacFound
    state         = $sacShort
    meaning       = $sacMeaning
    read_error    = $sacReadError
}

if (-not $Json) {
    Write-Head "1. SMART APP CONTROL STATE (read-only)"
    Write-Host ("registry key : " + $sacPath)
    Write-Host ("value name   : " + $sacName)
    if ($sacFound) {
        Write-Host ("value        : " + $sacValue)
    } else {
        Write-Host  "value        : <absent>"
    }
    Write-Host ("meaning      : " + $sacMeaning)
    if ($sacReadError -ne "") {
        Write-Host ("note         : could not read the key directly: " + $sacReadError)
    }
    Write-Host ""
    Write-Host "How to read this:"
    Write-Host "  0 (off)         -> SAC cannot be the cause of a launch failure on this machine."
    Write-Host "  1 (enforcement) -> SAC can block an unsigned exe/dll that carries a"
    Write-Host "                     Mark-of-the-Web. This is the state that produces the"
    Write-Host "                     'This app has been blocked' / silent DLL load failure."
    Write-Host "  2 (evaluation)  -> SAC is deciding; it does not block yet."
    Write-Host "  If the value is absent, SAC was never turned on (or was turned off and the"
    Write-Host "  value was removed) -- again SAC is not the cause here."
    Write-Host ""
    Write-Host "Turning SAC back on is NOT possible in-place once it has been turned off;"
    Write-Host "see dist\README-SAC.md before you touch anything."
}

# ---------------------------------------------------------------- package scan
$pkgDir = $null
$pkgFiles = @()
if ($PackagePath -ne "") {
    $resolved = $null
    try {
        $resolved = (Resolve-Path -LiteralPath $PackagePath -ErrorAction Stop).ProviderPath
    } catch {
        Add-Error ("PackagePath not found: " + $PackagePath)
    }
    if ($resolved) {
        $pkgDir = $resolved
        $all = @()
        try {
            $all = @(Get-ChildItem -LiteralPath $pkgDir -Recurse -File -ErrorAction SilentlyContinue |
                Where-Object { $_.Extension -ieq ".exe" -or $_.Extension -ieq ".dll" })
        } catch {
            Add-Error ("package enumeration failed: " + $_.Exception.Message)
        }
        $pkgFiles = @($all)
    }
}

function Get-Motw([string]$FullName) {
    # Mark-of-the-Web lives in an NTFS alternate data stream named Zone.Identifier.
    $result = [ordered]@{ present = $false; zone = $null; referrer = $null; host = $null; raw = $null }
    try {
        $stream = Get-Item -LiteralPath $FullName -Stream "Zone.Identifier" -ErrorAction Stop
        $result.present = $true
        $text = (Get-Content -LiteralPath $FullName -Stream "Zone.Identifier" -ErrorAction Stop) -join " ; "
        $result.raw = $text
        foreach ($line in @($text -split " ; ")) {
            $t = $line.Trim()
            if ($t -like "ZoneId=*")      { $result.zone     = $t.Substring(7) }
            if ($t -like "ReferrerUrl=*") { $result.referrer = $t.Substring(12) }
            if ($t -like "HostUrl=*")     { $result.host     = $t.Substring(8) }
        }
    } catch {
        # No stream -> no Mark-of-the-Web. Expected for files copied from a local build.
    }
    return $result
}

$sigList = @()
if ($pkgDir) {
    $total = $pkgFiles.Count
    $toCheck = @($pkgFiles)
    if ($Sample -gt 0 -and $total -gt $Sample) {
        # Always check every exe (the launcher), then fill up with dlls.
        $exes = @($pkgFiles | Where-Object { $_.Extension -ieq ".exe" })
        $dlls = @($pkgFiles | Where-Object { $_.Extension -ieq ".dll" })
        $picked = @()
        $picked += $exes
        $room = $Sample - $picked.Count
        if ($room -gt 0) { $picked += @($dlls | Select-Object -First $room) }
        $toCheck = @($picked)
    }

    $unsigned = 0
    $motwCount = 0
    foreach ($f in $toCheck) {
        $sig = $null
        try {
            $sig = Get-AuthenticodeSignature -LiteralPath $f.FullName -ErrorAction Stop
        } catch {
            Add-Error ("signature check failed for " + $f.FullName + ": " + $_.Exception.Message)
        }
        $motw = Get-Motw $f.FullName
        if ($motw.present) { $motwCount = $motwCount + 1 }
        $status = "unknown"
        $subject = ""
        $sha = ""
        if ($sig) {
            $status = [string]$sig.Status
            if ($sig.SignerCertificate) { $subject = [string]$sig.SignerCertificate.Subject }
        }
        if ($status -eq "NotSigned") { $unsigned = $unsigned + 1 }
        $sha = ""
        try { $sha = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash } catch { }

        $sigList += [ordered]@{
            path          = $f.FullName
            name          = $f.Name
            bytes         = $f.Length
            sha256        = $sha
            signature     = $status
            signer        = $subject
            motw          = $motw
        }
    }

    $script:Report.package = [ordered]@{
        path            = $pkgDir
        exe_dll_total   = $total
        checked         = $sigList.Count
        not_signed      = $unsigned
        with_motw       = $motwCount
        files           = $sigList
    }

    if (-not $Json) {
        Write-Head "3. PACKAGE FILES: SIGNATURE + MARK-OF-THE-WEB (read-only)"
        Write-Host ("folder                : " + $pkgDir)
        Write-Host ("exe/dll found         : " + $total)
        Write-Host ("signature-checked     : " + $sigList.Count)
        Write-Host ("  of which NotSigned  : " + $unsigned)
        Write-Host ("files with MOTW       : " + $motwCount)
        Write-Host ""
        Write-Host "  signature          MOTW  size        file"
        Write-Host "  -----------------  ----  ----------  ----"
        foreach ($row in $sigList) {
            $motwTag = "no"
            $zoneTag = ""
            if ($row.motw.present) {
                $motwTag = "YES"
                if ($row.motw.zone) { $zoneTag = "(ZoneId=" + $row.motw.zone + ")" }
            }
            $pad = [string]$row.signature
            if ($pad.Length -lt 17) { $pad = $pad + (" " * (17 - $pad.Length)) }
            $sizepad = ([string]$row.bytes).PadLeft(10)
            Write-Host ("  " + $pad + "  " + $motwTag.PadRight(4) + "  " + $sizepad + "  " + $row.name + " " + $zoneTag)
        }
        Write-Host ""
        Write-Host "How to read this:"
        Write-Host "  signature = NotSigned  -> the file has no Authenticode signature at all."
        Write-Host "                            On a machine where SAC is ON, an unsigned file that"
        Write-Host "                            also carries a MOTW is exactly what gets blocked."
        Write-Host "  signature = UnknownError / HashMismatch / NotTrusted -> the file does have a"
        Write-Host "                            signature but Windows does not accept it (for SAC the"
        Write-Host "                            only thing that counts is a reputable, CA-issued"
        Write-Host "                            signature; self-signed is NOT enough)."
        Write-Host "  MOTW YES               -> Windows recorded that this file came from the"
        Write-Host "                            internet / a zip download. Removing the MOTW is the"
        Write-Host "                            one local, reversible thing you can do"
        Write-Host "                            (dist\tools\unblock_package.ps1), but with SAC ON it"
        Write-Host "                            will usually still refuse to run unsigned code."
        if ($Sample -gt 0 -and $total -gt $sigList.Count) {
            Write-Host ""
            Write-Host ("  NOTE: only " + $sigList.Count + " of " + $total + " files checked (sampled). Re-run with -Sample 0 to check all.")
        }
    }
}

# ---------------------------------------------------------------- 2. CI events
$eventIdsWanted = @(3004, 3033, 3036, 3077, 3082)
$events = @()
$logName = "Microsoft-Windows-CodeIntegrity/Operational"
$logError = ""
$logSize = $null

try {
    $log = Get-WinEvent -ListLog $logName -ErrorAction Stop
    $logSize = $log.RecordCount
} catch {
    $logError = $_.Exception.Message
}

if ($logError -eq "") {
    $raw = @()
    try {
        $raw = Get-WinEvent -LogName $logName -MaxEvents $MaxEvents -ErrorAction Stop
    } catch {
        $logError = $_.Exception.Message
    }

    # Build the match set: every file name in the extracted package.
    $names = @()
    if ($pkgFiles.Count -gt 0) {
        $names = @($pkgFiles | ForEach-Object { $_.Name } | Sort-Object -Unique)
    }

    foreach ($e in $raw) {
        $isWanted = $false
        if ($eventIdsWanted -contains $e.Id) { $isWanted = $true }
        $msg = ""
        try { $msg = [string]$e.Message } catch { }
        $namesHit = @()
        foreach ($n in $names) {
            if ($n -ne "" -and $msg.IndexOf($n, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
                $namesHit += $n
            }
        }
        if (-not $isWanted -and $namesHit.Count -eq 0) { continue }
        $events += [ordered]@{
            id          = $e.Id
            time        = $e.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss")
            level       = [string]$e.LevelDisplayName
            provider    = [string]$e.ProviderName
            package_hit = $namesHit
            message     = $msg
        }
    }
    # package hits first, then by time
    $events = @($events | Sort-Object @{Expression = { if ($_.package_hit.Count -gt 0) { 0 } else { 1 } }}, @{Expression = { $_.time }; Descending = $true })
    if ($events.Count -eq 0) { $events = @() }
}

$script:Report.events = $events

if (-not $Json) {
    Write-Head "2. CODE INTEGRITY OPERATIONAL EVENTS (read-only)"
    Write-Host ("log          : " + $logName)
    if ($logSize -ne $null) { Write-Host ("records in log : " + $logSize) }
    Write-Host ("events pulled  : " + $MaxEvents)
    if ($logError -ne "") {
        Write-Host ""
        Write-Host ("  NOT READABLE: " + $logError)
        Write-Host "  Re-run this script from an ELEVATED PowerShell to see the full event list."
        Add-Error ("event log not readable: " + $logError)
    } else {
        $hits = @($events | Where-Object { $_.package_hit.Count -gt 0 })
        $others = @($events | Where-Object { $_.package_hit.Count -eq 0 })
        # When a package folder was given, the ONLY events that matter are the ones that name
        # a file inside it. Everything else is unrelated noise from other software on the box,
        # so it is summarised instead of dumped. -AllEvents shows it anyway.
        $show = $others
        if ($pkgDir -and -not $AllEvents) { $show = @() }

        Write-Host ("events matched : " + $events.Count + "  (of " + $MaxEvents + " pulled)")
        Write-Host ("  ids looked for : " + ($eventIdsWanted -join ", "))
        if ($pkgDir) {
            Write-Host ("  naming a file inside your package : " + $hits.Count)
            Write-Host ("  unrelated CI events on this machine : " + $others.Count)
        }
        Write-Host ""
        if ($pkgDir -and $hits.Count -eq 0) {
            Write-Host "  >>> NO Code Integrity event names a file inside your extracted package."
            Write-Host ("      (out of the last " + $MaxEvents + " events of the log)")
            Write-Host "      That is evidence FOR 'the block was not a CodeIntegrity/SAC block',"
            Write-Host "      but it is not conclusive on its own -- see the notes below."
            Write-Host ""
        } elseif ($events.Count -eq 0) {
            Write-Host "  No matching events at all. If SAC is ON and your exe/dll still fails, check"
            Write-Host "  that you are looking at the machine that produced the failure, and that the"
            Write-Host "  failure happened recently enough to still be in the log."
            Write-Host ""
        }

        $i = 0
        foreach ($ev in $hits) {
            $i = $i + 1
            $tag = "  <== NAMES YOUR PACKAGE FILE(S): " + ($ev.package_hit -join ", ")
            Write-Host ("  [hit " + $i + "] id=" + $ev.id + "  " + $ev.time + "  " + $ev.level + $tag)
            $lines = @($ev.message -split "`r?`n")
            $shown = 0
            foreach ($l in $lines) {
                if ($shown -ge 12) { Write-Host "        ... (truncated)"; break }
                Write-Host ("        " + $l.TrimEnd())
                $shown = $shown + 1
            }
            Write-Host ""
        }

        if ($show.Count -gt 0) {
            Write-Host "  -- other (unrelated) CI events on this machine, most recent first --"
            $j = 0
            foreach ($ev in $show) {
                $j = $j + 1
                if ($j -gt 10) {
                    Write-Host ("  ... and " + ($show.Count - 10) + " more (use -AllEvents to see them all)")
                    break
                }
                $first = ""
                $fl = @($ev.message -split "`r?`n")
                if ($fl.Count -gt 0) { $first = $fl[0].Trim() }
                if ($first.Length -gt 110) { $first = $first.Substring(0, 110) + "..." }
                Write-Host ("  [" + $j + "] id=" + $ev.id + "  " + $ev.time + "  " + $first)
            }
            Write-Host ""
            Write-Host "  These do NOT name your package. They are other software on this machine"
            Write-Host "  failing its own signing checks. Do not read them as your failure."
            if ($pkgDir -and -not $AllEvents) {
                Write-Host "  (Use -AllEvents to print their full messages.)"
            }
            Write-Host ""
        }

        Write-Host "How to read this:"
        Write-Host "  3077 = Code Integrity blocked a binary (signing level / reputation policy)."
        Write-Host "  3033 = a file was blocked by the Code Integrity policy."
        Write-Host "  3036 = a process tried to load a binary that did not meet the policy."
        Write-Host "  3004 = a signature failed to validate."
        Write-Host "  3082 = policy/paging related CI record."
        Write-Host "  The useful field is the FILE PATH inside the message. If it names a file in"
        Write-Host ("  your extracted package (" + "<hit" + "> above), SAC / WDAC really did block it.")
        Write-Host "  An empty list is NOT proof that SAC is innocent -- the Operational log only"
        Write-Host "  records what the CI subsystem chose to log, and it needs elevation to read."
    }
}

# ---------------------------------------------------------------- 4. how to read the error
if (-not $Json) {
    Write-Head "4. HOW TO READ THE FAILURE YOU SAW"
    Write-Host "The two failure shapes people report are different, and they point at different"
    Write-Host "causes. Get the exact text before concluding anything:"
    Write-Host ""
    Write-Host "  (a) A dialog 'This app has been blocked' / 'Windows protected your PC'"
    Write-Host "      -> that is SmartScreen or SAC refusing the LAUNCHER."
    Write-Host "      Run the exe from a console window so the text is captured:"
    Write-Host '        cmd /c "<the game folder>\<game>.exe"'
    Write-Host "      Read the error box / console text literally; do not paraphrase it."
    Write-Host ""
    Write-Host "      Windows shows a different dialog for a SAC block (no 'Run anyway'"
    Write-Host "      option) than for SmartScreen (which has 'More info' -> 'Run anyway')."
    Write-Host "      If there is no 'Run anyway', it is SAC, not SmartScreen."
    Write-Host ""
    Write-Host "  (b) The window opens and dies, or you see something like"
    Write-Host "      'Could not load file or assembly ...', 'Failed to load the dll',"
    Write-Host "      'Unable to find the entry point', 0xc000007b / 0xc0000135"
    Write-Host "      -> that is the .NET/CoreCLR host or a native dll failing to load."
    Write-Host "      This package is a self-contained .NET export: the runtime dlls"
    Write-Host "      (coreclr.dll, hostfxr.dll, clrjit.dll, System.*.dll) must sit next to"
    Write-Host "      the exe after extraction. If the archive was extracted with a tool that"
    Write-Host "      mangled the folder layout, or if you only copied the exe out of the folder,"
    Write-Host "      the dlls will not be found. Re-extract the whole archive to a fresh folder"
    Write-Host "      and run the exe in place."
    Write-Host "      -> Section 3 above is the interesting one for this shape: are the dlls"
    Write-Host "         present, and what is their signature state?"
    Write-Host "      -> This shape is NOT what SAC produces. SAC refuses the launch; it does not"
    Write-Host "         let the process start and then fail to load a dll."
    Write-Host ""
    Write-Host "  (c) One-shot commands, all read-only, safe to paste:"
    Write-Host '        powershell -ExecutionPolicy Bypass -File sac_diagnose.ps1 -PackagePath "<dir>"'
    Write-Host '        Get-AuthenticodeSignature "<dir>\<game>.exe"'
    Write-Host "        Get-WinEvent -LogName Microsoft-Windows-CodeIntegrity/Operational -MaxEvents 50"
    Write-Host ""
    Write-Host "  This script changes nothing. It only reads."
}

# ---------------------------------------------------------------- JSON output
if ($Json) {
    $jsonText = ""
    try {
        $jsonText = ($script:Report | ConvertTo-Json -Depth 8)
    } catch {
        $jsonText = "{ `"error`": `"ConvertTo-Json failed`" }"
    }
    Write-Output $jsonText
}
