param(
  [string]$Exe,
  [string]$ArgLine,
  [string]$Tag = 'stock',
  [int]$WaitSeconds = 6,
  [int]$GapMs = 700,
  [int]$Grabs = 3
)
# diag_stockwindow.ps1 -- TASK-094: does *any* Godot on this machine deliver new
# frames to its window?  It starts the engine given by -Exe (no MCP, so no tools
# are called), waits, and grabs the window rectangle several times with a gap.
# The window belongs to the process tree, so a game that animates on its own
# (the snake starts moving immediately) shows up as differing grabs.
#
# Iron rule 1: no shell redirection -- Start-Process owns stdout/stderr.
# Iron rule 2: nothing is removed outside $Out.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class W32 {
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr GetWindowDC(IntPtr h);
  [DllImport("user32.dll")] public static extern int ReleaseDC(IntPtr h, IntPtr dc);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint flags);
  public static bool PrintInto(IntPtr h, IntPtr dc) {
    return PrintWindow(h, dc, 0x00000002 /* PW_RENDERFULLCONTENT */);
  }
  public struct RECT { public int Left, Top, Right, Bottom; }
  public static int L, T, R, B;
  public static bool RectOf(IntPtr h) { RECT r; if (!GetWindowRect(h, out r)) return false; L=r.Left; T=r.Top; R=r.Right; B=r.Bottom; return true; }
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr l);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, System.Text.StringBuilder s, int n);
  public static IntPtr Find(uint[] pids) {
    var want = new System.Collections.Generic.HashSet<uint>(pids);
    IntPtr best = IntPtr.Zero; long bestArea = 0;
    EnumWindows((h, l) => {
      uint p; GetWindowThreadProcessId(h, out p);
      if (!want.Contains(p)) return true;
      RECT r; if (!GetWindowRect(h, out r)) return true;
      long a = (long)(r.Right-r.Left)*(r.Bottom-r.Top);
      if (a > bestArea) { bestArea = a; best = h; }
      return true;
    }, IntPtr.Zero);
    return best;
  }
}
'@
[void][W32]::SetProcessDPIAware()

$Out = Join-Path 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task094\stock' $Tag
New-Item -ItemType Directory -Force -Path $Out | Out-Null
function Say([string]$t) { Write-Host $t }

$launcher = Join-Path $Out 'launch.cmd'
Set-Content -LiteralPath $launcher -Encoding ASCII -Value @('@echo off', ('"{0}" {1}' -f $Exe, $ArgLine))
Say ("cmdline: {0} {1}" -f $Exe, $ArgLine)
$proc = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $launcher -WorkingDirectory (Split-Path -Parent $Exe) `
  -RedirectStandardOutput (Join-Path $Out 'stdout.txt') -RedirectStandardError (Join-Path $Out 'stderr.txt') -NoNewWindow -PassThru

function Pids() {
  $kids = @()
  try { $kids = @(Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $proc.Id } | Select-Object -ExpandProperty ProcessId) } catch { }
  $gd = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'Godot*' } | Select-Object -ExpandProperty Id)
  return @(@($proc.Id) + @($kids) + @($gd) | Sort-Object -Unique)
}

Start-Sleep -Milliseconds $WaitSeconds
# Wait for the window and start grabbing AT ONCE: the snake this fixture runs
# steps every 0.08 s and hits the wall after about 1.6 s, so a grab loop that
# starts at t=4 s can only ever see the finished board -- which is exactly the
# mistake the TASK-093 reproducer made.
$pollDeadline = (Get-Date).AddSeconds(40)
while ((Get-Date) -lt $pollDeadline) {
  if ([W32]::Find([uint32[]](Pids)) -ne [IntPtr]::Zero) { break }
  Start-Sleep -Milliseconds 60
}
Say ("window appeared, elapsed since launch: ~{0:N1}s" -f ((Get-Date) - $pollDeadline.AddSeconds(40) + [timespan]::FromSeconds(40)).TotalSeconds)
$hashes = @()
$printHashes = @()
for ($i = 1; $i -le $Grabs; $i++) {
  $h = [W32]::Find([uint32[]](Pids))
  if ($h -eq [IntPtr]::Zero) { Say ("grab {0}: no window" -f $i) }
  else {
    [void][W32]::ShowWindow($h, 9); [void][W32]::BringWindowToTop($h); [void][W32]::SetForegroundWindow($h)
    Start-Sleep -Milliseconds 250
    if ([W32]::RectOf($h)) {
      $w = [W32]::R - [W32]::L; $ht = [W32]::B - [W32]::T
      if ($w -gt 0 -and $ht -gt 0) {
        $bmp = New-Object System.Drawing.Bitmap($w, $ht)
        $g = [System.Drawing.Graphics]::FromImage($bmp)
        $g.CopyFromScreen([W32]::L, [W32]::T, 0, 0, (New-Object System.Drawing.Size($w, $ht)))
        $g.Dispose()
        $p = Join-Path $Out ("grab-{0}.png" -f $i)
        $bmp.Save($p, [System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose()
        $sha = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash
        $hashes += $sha
        # The second reading of the same window: PrintWindow asks DWM for the
        # window's own last presented frame, which does not depend on the
        # desktop being scanned out.
        $bmp2 = New-Object System.Drawing.Bitmap($w, $ht)
        $g2 = [System.Drawing.Graphics]::FromImage($bmp2)
        $dc = $g2.GetHdc()
        $ok = $false
        try { $ok = [W32]::PrintInto($h, $dc) } finally { try { $g2.ReleaseHdc($dc) } catch { } }
        $g2.Dispose()
        $p2 = Join-Path $Out ("print-{0}.png" -f $i)
        $bmp2.Save($p2, [System.Drawing.Imaging.ImageFormat]::Png); $bmp2.Dispose()
        $sha2 = (Get-FileHash -LiteralPath $p2 -Algorithm SHA256).Hash
        $printHashes += $sha2
        Say ("grab {0}: {1}x{2} sha={3} printwindow={4} psha={5} iconic={6}" -f $i, $w, $ht, $sha.Substring(0,16), $ok, $sha2.Substring(0,16), [W32]::IsIconic($h))
      } else { Say ("grab {0}: empty rect" -f $i) }
    }
  }
  Start-Sleep -Milliseconds $GapMs
}
$distinct = @($hashes | Sort-Object -Unique).Count
$distinctPrint = @($printHashes | Sort-Object -Unique).Count
Say ("grabs={0} distinct={1}   printwindow distinct={2}" -f $hashes.Count, $distinct, $distinctPrint)
if ($distinct -gt 1) { Say 'COPYFROMSCREEN_ANIMATES=YES' } else { Say 'COPYFROMSCREEN_ANIMATES=NO' }
if ($distinctPrint -gt 1) { Say 'PRINTWINDOW_ANIMATES=YES (the engine delivers new frames to its window)' } else { Say 'PRINTWINDOW_ANIMATES=NO (the window content never changes)' }

Get-Process | Where-Object { $_.Id -eq $proc.Id -or $_.ProcessName -like 'Godot*' } | ForEach-Object {
  try { Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', ('taskkill /PID ' + $_.Id + ' /T /F') -NoNewWindow -Wait -PassThru | Out-Null } catch { }
}
Say ("out={0}" -f $Out)
