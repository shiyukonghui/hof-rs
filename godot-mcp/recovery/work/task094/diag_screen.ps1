param(
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp',
  [string]$Game = 'snake',
  [string]$Tag = 'screen-bg',
  [int]$Port = 9889,
  [int]$WaitSeconds = 6
)
# diag_screen.ps1 -- TASK-094, defect D-1: is the *window* stale too, or only the
# readback?
#
# It starts the game, sets `Background.color` to blue / red / green with the MCP
# tool, and after each change takes BOTH:
#   * a Win32 screen grab of the window rectangle (what the desktop shows), and
#   * the tool's own screenshot (what `get_viewport().get_texture().get_image()`
#     returns).
# If the screen grab changes and the tool's picture does not, the rendering is
# fine and the module's readback path is the defect.
#
# Iron rule 1: no shell redirection -- Start-Process owns stdout/stderr.
# Iron rule 2: nothing is removed outside $Out.
# Iron rule 3: the engine is started through a generated .cmd.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;public static class Win32b {
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint flags);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  public static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);
  public static readonly IntPtr HWND_NOTOPMOST = new IntPtr(-2);
  public static bool Raise(IntPtr h) {
    ShowWindow(h, 9);
    SetWindowPos(h, HWND_TOPMOST, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040);
    SetWindowPos(h, HWND_NOTOPMOST, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040);
    BringWindowToTop(h);
    return SetForegroundWindow(h);
  }
  public struct RECT { public int Left, Top, Right, Bottom; }
  public static int L, T, R, B;
  public static bool RectOf(IntPtr h) {
    RECT r; if (!GetWindowRect(h, out r)) return false;
    L = r.Left; T = r.Top; R = r.Right; B = r.Bottom; return true;
  }
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr l);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern int GetWindowTextLength(IntPtr h);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, System.Text.StringBuilder s, int n);
  public static IntPtr FindGame(uint[] pids) {
    var want = new System.Collections.Generic.HashSet<uint>(pids);
    IntPtr best = IntPtr.Zero;
    long bestArea = 0;
    EnumWindows((h, l) => {
      uint p; GetWindowThreadProcessId(h, out p);
      if (!want.Contains(p)) return true;
      RECT r; if (!GetWindowRect(h, out r)) return true;
      long area = (long)(r.Right - r.Left) * (long)(r.Bottom - r.Top);
      // The Godot window is the biggest one owned by the process tree; the IME
      // windows the process also owns are 0x0 or a few pixels wide.
      if (area > bestArea) { bestArea = area; best = h; }
      return true;
    }, IntPtr.Zero);
    return best;
  }
}
'@
# The first run of this script grabbed the wrong window: without a DPI-aware
# process, GetWindowRect answers in virtualised pixels while CopyFromScreen reads
# physical ones, so the rectangle landed on an unrelated window.
[void][Win32b]::SetProcessDPIAware()

$Out = Join-Path $Root ("recovery\work\task094\screen\{0}-{1}" -f $Game, $Tag)
New-Item -ItemType Directory -Force -Path $Out | Out-Null
function Say([string]$t) { Write-Host $t }

$engine  = Join-Path $Root 'godot\bin\godot.windows.editor.x86_64.mono.console.exe'
$project = Join-Path $Root ("projects\{0}" -f $Game)
$trace   = Join-Path $Out 'trace.jsonl'
$switches = @(
  ('--path "' + $project + '"'),
  ('--mcp-port=' + $Port),
  ('--mcp-trace="' + $trace + '"'),
  '--mcp-capture=off'
)
$launcher = Join-Path $Out 'launch.cmd'
Set-Content -LiteralPath $launcher -Encoding ASCII -Value @(
  '@echo off',
  ('cd /d "{0}"' -f (Join-Path $Root 'godot')),
  ('"{0}" {1}' -f $engine, ($switches -join ' '))
)
$proc = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $launcher -WorkingDirectory (Join-Path $Root 'godot') `
  -RedirectStandardOutput (Join-Path $Out 'engine.stdout.txt') -RedirectStandardError (Join-Path $Out 'engine.stderr.txt') -NoNewWindow -PassThru

$deadline = (Get-Date).AddSeconds(120)
$up = $false
while ((Get-Date) -lt $deadline -and -not $up) {
  $c = New-Object System.Net.Sockets.TcpClient
  try { $t = $c.ConnectAsync('127.0.0.1', $Port); if ($t.Wait(700) -and $c.Connected) { $up = $true } }
  catch { } finally { try { $c.Close() } catch { } }
  if (-not $up) { Start-Sleep -Milliseconds 500 }
}
if (-not $up) { throw "the game endpoint on $Port never came up" }

function Call-Tool([string]$TagName, [string]$Tool, $Arguments) {
  $body = (@{ jsonrpc = '2.0'; id = 1; method = 'tools/call'; params = @{ name = $Tool; arguments = $Arguments } } | ConvertTo-Json -Compress -Depth 24)
  $bf = Join-Path $Out ($TagName + '.request.json')
  Set-Content -LiteralPath $bf -Value $body -Encoding UTF8 -NoNewline
  $res = & curl.exe -s -X POST -H 'Content-Type: application/json' --data-binary ('@' + $bf) ("http://127.0.0.1:{0}/mcp" -f $Port)
  $text = ($res -join '')
  Set-Content -LiteralPath (Join-Path $Out ($TagName + '.json')) -Value $text -Encoding UTF8
}

function Game-Pids() {
  $kids = @()
  try { $kids = @(Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $proc.Id } | Select-Object -ExpandProperty ProcessId) } catch { }
  $gd = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'godot*' } | Select-Object -ExpandProperty Id)
  return @(@($proc.Id) + @($kids) + @($gd) | Sort-Object -Unique)
}

function Grab-Screen([string]$name) {
  $h = [Win32b]::FindGame([uint32[]](Game-Pids))
  if ($h -eq [IntPtr]::Zero) { Say "  screen $name : no window found"; return }
  if (-not [Win32b]::RectOf($h)) { Say "  screen $name : no rect"; return }
  [void][Win32b]::Raise($h)
  Start-Sleep -Milliseconds 400
  if (-not [Win32b]::RectOf($h)) { Say "  screen $name : no rect"; return }
  $w = [Win32b]::R - [Win32b]::L; $ht = [Win32b]::B - [Win32b]::T
  if ($w -le 0 -or $ht -le 0) { Say ("  screen {0}: empty rect {1}x{2} (iconic={3})" -f $name, $w, $ht, [Win32b]::IsIconic($h)); return }
  $bmp = New-Object System.Drawing.Bitmap($w, $ht)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen([Win32b]::L, [Win32b]::T, 0, 0, (New-Object System.Drawing.Size($w, $ht)))
  $g.Dispose()
  $p = Join-Path $Out ("screen-{0}.png" -f $name)
  $bmp.Save($p, [System.Drawing.Imaging.ImageFormat]::Png)
  $bmp.Dispose()
  Say ("  screen {0}: {1}x{2} sha={3}" -f $name, $w, $ht, (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.Substring(0, 16))
}

Start-Sleep -Seconds $WaitSeconds
Grab-Screen 't0'

foreach ($step in @(@('blue', 0.0, 0.0, 1.0), @('red', 1.0, 0.0, 0.0), @('green', 0.0, 1.0, 0.0))) {
  $name = $step[0]
  Call-Tool ("c-" + $name) 'running_game_set_node_property' @{ node_path = 'Background'; property = 'color'; value = @{ r = $step[1]; g = $step[2]; b = $step[3]; a = 1.0 } }
  Start-Sleep -Milliseconds 600
  Grab-Screen $name
  $r = Call-Tool ("s-" + $name) 'running_game_capture_screenshot' @{ save_path = ('user://screen-{0}.png' -f $name) }
}

$userDir = Join-Path $env:APPDATA ("Godot\app_userdata\{0}" -f $Game)
Say '--- the tool''s own screenshots (user://) ---'
foreach ($n in @('t0','blue','red','green')) {
  if ($n -eq 't0') { continue }
  $p = Join-Path $userDir ("screen-{0}.png" -f $n)
  if (Test-Path -LiteralPath $p) { Say ('  screen-{0}.png sha={1}' -f $n, (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.Substring(0, 16)) }
}
Say '--- screen grabs ---'
$grabs = @{}
foreach ($n in @('t0','blue','red','green')) {
  $p = Join-Path $Out ("screen-{0}.png" -f $n)
  if (Test-Path -LiteralPath $p) { $grabs[$n] = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
}
Say ("SCREEN t0_vs_blue  DIFFERENT = {0}" -f ($grabs['t0'] -ne $grabs['blue']))
Say ("SCREEN blue_vs_red DIFFERENT = {0}" -f ($grabs['blue'] -ne $grabs['red']))
Say ("SCREEN red_vs_green DIFFERENT = {0}" -f ($grabs['red'] -ne $grabs['green']))

Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', ('taskkill /PID ' + $proc.Id + ' /T /F') -NoNewWindow -Wait -PassThru | Out-Null
Say ("out={0}" -f $Out)
