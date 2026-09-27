# TASK-115 item C -- the bounded, SAC-friendly export probe.
#
# Three questions, each answered by a command whose output lands in a file under
# recovery\work\task115\logs (Start-Process -RedirectStandardOutput/-Error, the
# same mechanism tools\run_game_session.ps1 uses: iron rule 1 forbids shell
# redirection, and a .cmd wrapper is what keeps the engine's own quoting honest).
#
#   1. Are the OFFICIAL 4.7.1-stable mono export templates installed, and is the
#      template exe Validly signed?
#   2. Does `binary_format/embed_pck=false` leave the exported game exe BYTE
#      IDENTICAL to the template exe (sha256), i.e. is the template's signature,
#      whatever it is, carried into the export untouched?
#   3. Does that exported exe actually run (headless and windowed, exit code 0)
#      and does it really load the same-directory .pck?
#
# Nothing here downloads anything and nothing here is destructive: every write
# lands under $Work.
param(
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp'
)
$ErrorActionPreference = 'Stop'

$Work     = Join-Path $Root 'recovery\work\task115'
$Probe    = Join-Path $Work 'export_probe'
$Logs     = Join-Path $Work 'logs'
$Editor   = Join-Path $Root 'godot\bin\godot.windows.editor.x86_64.mono.console.exe'
$Project  = Join-Path $Root 'projects\_exercises\ex_editor'
$TplDir   = Join-Path $env:APPDATA 'Godot\export_templates'
$TplDir48 = Join-Path $TplDir '4.8.dev'
$TplDir47 = Join-Path $TplDir '4.7.1.stable.mono'
$Tpl48    = Join-Path $TplDir48 'windows_release_x86_64.exe'
$Official = 'D:\Program Files\Godot_v4.7.1-stable_mono_win64\Godot_v4.7.1-stable_mono_win64\Godot_v4.7.1-stable_mono_win64.exe'

New-Item -ItemType Directory -Force -Path $Probe | Out-Null
New-Item -ItemType Directory -Force -Path $Logs  | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Probe 'alone') | Out-Null

$script:Report = New-Object System.Collections.Generic.List[string]
function Say([string]$text) {
  Write-Host $text
  $script:Report.Add($text)
}

function Run-CmdFile([string]$Name, [string[]]$Batch) {
  # A generated .cmd, not a quoted Start-Process argument list: PowerShell escapes
  # inner quotes as \" for a native command line and cmd.exe does not read that
  # the way PowerShell means it (run_game_session.ps1 run-1 defect P-6).
  $b = Join-Path $Probe ($Name + '.cmd')
  Set-Content -LiteralPath $b -Value (@('@echo off') + $Batch) -Encoding ASCII
  $out = Join-Path $Logs ($Name + '.stdout.txt')
  $err = Join-Path $Logs ($Name + '.stderr.txt')
  $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $b -WorkingDirectory $Probe `
        -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -Wait -PassThru
  return [pscustomobject]@{ Exit = $p.ExitCode; Out = $out; Err = $err }
}

function Run-CmdFileBounded([string]$Name, [string[]]$Batch, [int]$TimeoutSec) {
  # TASK-115 measured why this exists: an exported Windows game that cannot find
  # its .pck raises a MODAL message box and waits for a human, so -Wait never
  # returns. The run is therefore bounded, and a run that outlives the bound is
  # reported as TIMEOUT (and killed) instead of blocking the probe forever.
  $b = Join-Path $Probe ($Name + '.cmd')
  Set-Content -LiteralPath $b -Value (@('@echo off') + $Batch) -Encoding ASCII
  $out = Join-Path $Logs ($Name + '.stdout.txt')
  $err = Join-Path $Logs ($Name + '.stderr.txt')
  $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $b -WorkingDirectory $Probe `
        -RedirectStandardOutput $out -RedirectStandardError $err -NoNewWindow -PassThru
  $finished = $true
  try { Wait-Process -Id $p.Id -Timeout $TimeoutSec -ErrorAction Stop } catch { $finished = $false }
  if ($finished) { $p.WaitForExit(); $exit = $p.ExitCode }
  else {
    Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', ('taskkill /PID ' + $p.Id + ' /T /F') `
      -RedirectStandardOutput (Join-Path $Logs ($Name + '.taskkill.stdout.txt')) `
      -RedirectStandardError (Join-Path $Logs ($Name + '.taskkill.stderr.txt')) -NoNewWindow -Wait | Out-Null
    $exit = 'TIMEOUT(' + $TimeoutSec + 's)'
  }
  return [pscustomobject]@{ Exit = $exit; Out = $out; Err = $err; Finished = $finished }
}

function Sha([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return '<absent>' }
  return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Size([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return -1 }
  return (Get-Item -LiteralPath $Path).Length
}

function Sig([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return 'ABSENT' }
  $s = Get-AuthenticodeSignature -LiteralPath $Path
  $subject = ''
  if ($s.SignerCertificate) { $subject = $s.SignerCertificate.Subject }
  return ("{0} :: {1}" -f $s.Status, $subject)
}

# ---------------------------------------------------------------------------
Say '=== TASK-115 C: the export / signature probe ==='
Say ("time (UTC) : {0}" -f (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))
Say ("editor     : {0}" -f $Editor)
Say ("project    : {0}" -f $Project)
Say ''

# -- Q1 -----------------------------------------------------------------------
Say '--- Q1: are the OFFICIAL 4.7.1-stable mono export templates installed? ---'
Say ("template root                : {0}" -f $TplDir)
Say ("template root exists         : {0}" -f (Test-Path -LiteralPath $TplDir))
if (Test-Path -LiteralPath $TplDir) {
  foreach ($d in (Get-ChildItem -LiteralPath $TplDir -Directory | Sort-Object Name)) {
    Say ("  version dir                : {0}" -f $d.Name)
    foreach ($f in (Get-ChildItem -LiteralPath $d.FullName -File | Sort-Object Name)) {
      Say ("      {0,-46} {1,12} bytes" -f $f.Name, $f.Length)
    }
  }
}
Say ("4.7.1.stable.mono dir        : {0}" -f $TplDir47)
Say ("4.7.1.stable.mono exists     : {0}" -f (Test-Path -LiteralPath $TplDir47))
Say ("4.7.1 template exe path      : {0}" -f (Join-Path $TplDir47 'windows_release_x86_64.exe'))
Say ("4.7.1 template exe exists    : {0}" -f (Test-Path -LiteralPath (Join-Path $TplDir47 'windows_release_x86_64.exe')))
Say ''
Say '--- Q1b: what IS on disk, and how is it signed? ---'
Say ("official 4.7.1 mono editor   : {0}" -f (Sig $Official))
Say ("  path                       : {0}" -f $Official)
Say ("4.8.dev template exe         : {0}" -f (Sig $Tpl48))
Say ("  path                       : {0}" -f $Tpl48)
Say ("  size / sha256              : {0} / {1}" -f (Size $Tpl48), (Sha $Tpl48))
Say ''

# -- Q2 -----------------------------------------------------------------------
Say '--- Q2: embed_pck=false vs the template exe, byte for byte ---'
$exeA = Join-Path $Probe 'ex_editor.exe'
$exeB = Join-Path $Probe 'ex_editor_embedded.exe'
$exeC = Join-Path $Probe 'ex_editor_purecopy.exe'
foreach ($f in @($exeA, $exeB, $exeC, (Join-Path $Probe 'ex_editor.pck'))) {
  if (Test-Path -LiteralPath $f) { Remove-Item -LiteralPath $f -Force }
}

$r = Run-CmdFile 'export-noembed' @(
  ('cd /d "{0}"' -f (Join-Path $Root 'godot')),
  ('"{0}" --headless --path "{1}" --export-release "Windows Desktop" "{2}"' -f $Editor, $Project, $exeA),
  'echo EXPORT_EXIT=%ERRORLEVEL%'
)
Say ("export (Windows Desktop, embed_pck=false) exit : {0}" -f $r.Exit)
Get-Content -LiteralPath $r.Out -Tail 6 | ForEach-Object { Say ('    | ' + $_) }
Get-Content -LiteralPath $r.Err -Tail 6 | ForEach-Object { Say ('    ! ' + $_) }
Say ''

$r2 = Run-CmdFile 'export-embed' @(
  ('cd /d "{0}"' -f (Join-Path $Root 'godot')),
  ('"{0}" --headless --path "{1}" --export-release "Windows Desktop Embedded" "{2}"' -f $Editor, $Project, $exeB),
  'echo EXPORT_EXIT=%ERRORLEVEL%'
)
Say ("export (Windows Desktop Embedded, embed_pck=true) exit : {0}" -f $r2.Exit)
Get-Content -LiteralPath $r2.Out -Tail 6 | ForEach-Object { Say ('    | ' + $_) }
Get-Content -LiteralPath $r2.Err -Tail 6 | ForEach-Object { Say ('    ! ' + $_) }
Say ''

$pck = Join-Path $Probe 'ex_editor.pck'
Say ("template exe                 : {0,12} bytes  sha256 {1}" -f (Size $Tpl48), (Sha $Tpl48))
Say ("exported exe (embed_pck=false): {0,12} bytes  sha256 {1}" -f (Size $exeA), (Sha $exeA))
Say ("exported exe (embed_pck=true) : {0,12} bytes  sha256 {1}" -f (Size $exeB), (Sha $exeB))
Say ("sidecar pck (embed_pck=false) : {0,12} bytes  sha256 {1}" -f (Size $pck), (Sha $pck))
Say ("sha256(template) -eq sha256(export, embed_pck=false) : {0}" -f ((Sha $Tpl48) -eq (Sha $exeA)))
Say ("sha256(template) -eq sha256(export, embed_pck=true)  : {0}" -f ((Sha $Tpl48) -eq (Sha $exeB)))
Say ("byte delta (embed_pck=false)  : {0}" -f ((Size $exeA) - (Size $Tpl48)))
Say ''

# The control that makes the next sentence decidable: the FIRST export above still
# has Godot's default `application/modify_resources=true`, which rewrites the PE's
# version-info/icon resources. Export once more with it turned off, so "the bytes
# survive" can be told apart from "the PCK was appended".
$r2b = Run-CmdFile 'export-purecopy' @(
  ('cd /d "{0}"' -f (Join-Path $Root 'godot')),
  ('"{0}" --headless --path "{1}" --export-release "Windows Desktop Pure Copy" "{2}"' -f $Editor, $Project, $exeC),
  'echo EXPORT_EXIT=%ERRORLEVEL%'
)
Say ("export (embed_pck=false + modify_resources=false) exit : {0}" -f $r2b.Exit)
Get-Content -LiteralPath $r2b.Out -Tail 3 | ForEach-Object { Say ('    | ' + $_) }
Get-Content -LiteralPath $r2b.Err -Tail 3 | ForEach-Object { Say ('    ! ' + $_) }
Say ("exported exe (modify_resources=false): {0,12} bytes  sha256 {1}" -f (Size $exeC), (Sha $exeC))
Say ("sha256(template) -eq sha256(export, embed_pck=false + modify_resources=false) : {0}" -f ((Sha $Tpl48) -eq (Sha $exeC)))
Say ("byte delta (embed_pck=false + modify_resources=false) : {0}" -f ((Size $exeC) - (Size $Tpl48)))
Say ''
Say '--- Q2b: how are the two exported exes signed? ---'
Say ("exported exe (embed_pck=false): {0}" -f (Sig $exeA))
Say ("exported exe (embed_pck=true) : {0}" -f (Sig $exeB))
Say ("exported exe (pure copy)      : {0}" -f (Sig $exeC))
Say ("template exe                  : {0}" -f (Sig $Tpl48))
Say ''

# -- Q3 -----------------------------------------------------------------------
Say '--- Q3: does the exported exe really run, and does it load the sidecar .pck? ---'
$aloneExe = Join-Path $Probe 'alone\ex_editor.exe'
Copy-Item -LiteralPath $exeA -Destination $aloneExe -Force
# The alone/ copy has NO .pck next to it: if the exe really reads the sidecar,
# this must fail rather than silently start an empty project. It is run bounded
# because that failure is a MODAL dialog (measured: it never returns).
$r3 = Run-CmdFileBounded 'run-alone-no-pck' @(
  ('cd /d "{0}"' -f (Join-Path $Probe 'alone')),
  ('ex_editor.exe --headless --quit-after 30'),
  'echo RUN_EXIT=%ERRORLEVEL%'
) 45
Say ("run WITHOUT the sidecar .pck, headless --quit-after 30 : exit {0}" -f $r3.Exit)
Get-Content -LiteralPath $r3.Out -Tail 8 | ForEach-Object { Say ('    | ' + $_) }
Get-Content -LiteralPath $r3.Err -Tail 8 | ForEach-Object { Say ('    ! ' + $_) }
Say ''

$r4 = Run-CmdFileBounded 'run-headless' @(
  ('cd /d "{0}"' -f $Probe),
  ('ex_editor.exe --headless --quit-after 60'),
  'echo RUN_EXIT=%ERRORLEVEL%'
) 90
Say ("run WITH the sidecar .pck, headless --quit-after 60 : exit {0}" -f $r4.Exit)
Get-Content -LiteralPath $r4.Out -Tail 10 | ForEach-Object { Say ('    | ' + $_) }
Get-Content -LiteralPath $r4.Err -Tail 10 | ForEach-Object { Say ('    ! ' + $_) }
Say ''

$r5 = Run-CmdFileBounded 'run-windowed' @(
  ('cd /d "{0}"' -f $Probe),
  ('ex_editor.exe --quit-after 120'),
  'echo RUN_EXIT=%ERRORLEVEL%'
) 90
Say ("run WITH the sidecar .pck, windowed --quit-after 120 : exit {0}" -f $r5.Exit)
Get-Content -LiteralPath $r5.Out -Tail 10 | ForEach-Object { Say ('    | ' + $_) }
Get-Content -LiteralPath $r5.Err -Tail 10 | ForEach-Object { Say ('    ! ' + $_) }
Say ''
Say 'post-run process check (no ex_editor.exe may be left behind):'
$left = @(Get-Process -Name 'ex_editor' -ErrorAction SilentlyContinue)
if ($left.Count -eq 0) { Say '  none' } else { foreach ($p in $left) { Say ('  STILL RUNNING pid={0}' -f $p.Id) } }
Say ''

# -- Q3b ----------------------------------------------------------------------
# The exe that IS byte-identical to the template must also be a working game; if it
# were not, "the copy preserves the signature" would be a useless property. The
# .pck has to carry the exe's own name (that is the rule the failure above proved),
# so the pair is copied into its own folder.
Say '--- Q3b: the byte-identical-to-template exe also runs ---'
$pureDir = Join-Path $Probe 'purecopy'
if (-not (Test-Path -LiteralPath $pureDir)) { New-Item -ItemType Directory -Force -Path $pureDir | Out-Null }
Copy-Item -LiteralPath $exeC -Destination (Join-Path $pureDir 'ex_editor.exe') -Force
Copy-Item -LiteralPath $pck  -Destination (Join-Path $pureDir 'ex_editor.pck') -Force
Say ("purecopy\ex_editor.exe sha256 : {0}   (template {1})" -f (Sha (Join-Path $pureDir 'ex_editor.exe')), (Sha $Tpl48))
Say ("purecopy\ex_editor.pck sha256 : {0}" -f (Sha (Join-Path $pureDir 'ex_editor.pck')))
$r6 = Run-CmdFileBounded 'run-purecopy-headless' @(
  ('cd /d "{0}"' -f $pureDir),
  ('ex_editor.exe --headless --quit-after 60'),
  'echo RUN_EXIT=%ERRORLEVEL%'
) 90
Say ("run byte-identical-to-template exe, headless --quit-after 60 : exit [{0}]" -f $r6.Exit)
Get-Content -LiteralPath $r6.Out -Tail 10 | ForEach-Object { Say ('    | ' + $_) }
Get-Content -LiteralPath $r6.Err -Tail 10 | ForEach-Object { Say ('    ! ' + $_) }
Say ''
$left2 = @(Get-Process -Name 'ex_editor' -ErrorAction SilentlyContinue)
if ($left2.Count -eq 0) { Say 'post-run process check: none' } else { foreach ($p in $left2) { Say ('  STILL RUNNING pid={0}' -f $p.Id) } }
Say ''

Set-Content -LiteralPath (Join-Path $Logs 'probe-report.txt') -Value $script:Report -Encoding UTF8
Write-Host ''
Write-Host ('report: {0}' -f (Join-Path $Logs 'probe-report.txt'))
