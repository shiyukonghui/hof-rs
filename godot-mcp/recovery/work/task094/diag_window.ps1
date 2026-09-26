param(
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp',
  [string]$Out  = 'F:\moonbit-hof-rs\godot-mcp\recovery\work\task094\diag-window',
  [string]$Game = 'snake',
  [int]$Port = 9889,
  [int]$WaitSeconds = 6
)
# diag_window.ps1 -- TASK-094, defect D-1.
#
# Hypothesis: `Main::iteration()` computes
#     wants_present = DisplayServer::can_any_window_draw() && ...
# (`main/main.cpp:5081`) and `DisplayServerWindows::can_any_window_draw()`
# returns false exactly when every window is minimized
# (`platform/windows/display_server_windows.cpp:3212`).  With
# `wants_present == false` and no pending RD resources the engine never calls
# `RenderingServer::draw()`, so the root viewport's render-target texture is
# never written again -- the game keeps ticking (property samples move) while
# every readback returns the same bytes.
#
# This script measures that directly: it starts the game with capture on, then
# reports the real Win32 state of the game window (minimized / visible / rect),
# takes a readback pair, restores the window, and takes another pair.
#
# Iron rule 1: no shell redirection -- Start-Process owns stdout/stderr.
# Iron rule 2: nothing is removed outside $Out.
# Iron rule 3: the engine is started through a generated .cmd.
$ErrorActionPreference = 'Stop'

Add-Type @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public static class Win32 {
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern bool IsZoomed(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern int GetWindowTextLength(IntPtr h);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  public struct RECT { public int Left, Top, Right, Bottom; }
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr l);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  public static List<IntPtr> ForPids(uint[] pids) {
    var want = new HashSet<uint>(pids);
    var found = new List<IntPtr>();
    EnumWindows((h, l) => { uint p; GetWindowThreadProcessId(h, out p); if (want.Contains(p)) found.Add(h); return true; }, IntPtr.Zero);
    return found;
  }
  public static string Title(IntPtr h) { int n = GetWindowTextLength(h); var sb = new StringBuilder(n + 2); GetWindowText(h, sb, n + 2); return sb.ToString(); }
  public static string Describe(IntPtr h) {
    RECT r; GetWindowRect(h, out r);
    return string.Format("hwnd=0x{0:X} iconic={1} visible={2} zoomed={3} rect=({4},{5})-({6},{7}) title='{8}'",
      h.ToInt64(), IsIconic(h), IsWindowVisible(h), IsZoomed(h), r.Left, r.Top, r.Right, r.Bottom, Title(h));
  }
}
'@

New-Item -ItemType Directory -Force -Path $Out   | Out-Null
$shots = Join-Path $Out 'shots'
New-Item -ItemType Directory -Force -Path $shots | Out-Null

# Write-Host, not Write-Output: a function's return value must not be polluted by
# its own progress lines (the first run of this script fed a status string into
# ShowWindow()).
function Say([string]$t) { Write-Host $t }

Say ("host session id = {0}  (interactive session is usually 1)" -f (Get-Process -Id $PID).SessionId)

$engine  = Join-Path $Root 'godot\bin\godot.windows.editor.x86_64.mono.console.exe'
$project = Join-Path $Root ("projects\{0}" -f $Game)
$trace   = Join-Path $Out 'trace-game.jsonl'

$launcher = Join-Path $Out 'launch.cmd'
Set-Content -LiteralPath $launcher -Encoding ASCII -Value @(
  '@echo off',
  ('cd /d "{0}"' -f (Join-Path $Root 'godot')),
  ('"{0}" --path "{1}" --mcp-port={2} --mcp-trace="{3}" --mcp-capture=every_call --mcp-capture-dir="{4}" --mcp-capture-viewport=2d' -f $engine, $project, $Port, $trace, $shots)
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
Say ("endpoint up after {0:N1}s" -f ((Get-Date) - $deadline.AddSeconds(120) + [timespan]::FromSeconds(120)).TotalSeconds)

function Call-Tool([string]$Tag, [string]$Tool, $Arguments) {
  $body = (@{ jsonrpc = '2.0'; id = 1; method = 'tools/call'; params = @{ name = $Tool; arguments = $Arguments } } | ConvertTo-Json -Compress -Depth 24)
  $bf = Join-Path $Out ($Tag + '.request.json')
  Set-Content -LiteralPath $bf -Value $body -Encoding UTF8 -NoNewline
  $res = & curl.exe -s -X POST -H 'Content-Type: application/json' --data-binary ('@' + $bf) ("http://127.0.0.1:{0}/mcp" -f $Port)
  ($res -join '')
}

# --- the process tree's windows ----------------------------------------------
function Game-Pids() {
  $kids = @()
  try { $kids = @(Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $proc.Id } | Select-Object -ExpandProperty ProcessId) } catch { }
  $all = @($proc.Id) + @($kids)
  $gd = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'godot*' } | Select-Object -ExpandProperty Id)
  return @($all + $gd | Sort-Object -Unique)
}

function Report-Windows([string]$label) {
  $pids = [uint32[]](Game-Pids)
  $hs = @([Win32]::ForPids($pids))
  Say ("--- windows [{0}]  pids={1}  found={2}" -f $label, ($pids -join ','), $hs.Count)
  foreach ($h in $hs) { Say ('    ' + [Win32]::Describe($h)) }
  return , $hs
}

Start-Sleep -Seconds $WaitSeconds
$hs1 = Report-Windows 'as launched'
$r1 = Call-Tool 'w01-shot-a' 'running_game_capture_screenshot' @{ save_path = 'user://diag-window-a.png' }
Say ("    shot-a: {0}" -f $r1.Substring(0, [Math]::Min(150, $r1.Length)))
Start-Sleep -Seconds 2
$r1b = Call-Tool 'w02-shot-a2' 'running_game_capture_screenshot' @{ save_path = 'user://diag-window-a2.png' }
Say ("    shot-a2: {0}" -f $r1b.Substring(0, [Math]::Min(150, $r1b.Length)))

# --- restore every window of the tree and try again --------------------------
Say '--- SW_RESTORE + SetForegroundWindow on every window of the tree'
foreach ($h in $hs1) {
  [void][Win32]::ShowWindow($h, 1)   # SW_SHOWNORMAL
  [void][Win32]::ShowWindow($h, 9)   # SW_RESTORE
  [void][Win32]::SetForegroundWindow($h)
}
Start-Sleep -Seconds $WaitSeconds
$hs2 = Report-Windows 'after restore'
$r2 = Call-Tool 'w03-shot-b' 'running_game_capture_screenshot' @{ save_path = 'user://diag-window-b.png' }
Say ("    shot-b: {0}" -f $r2.Substring(0, [Math]::Min(150, $r2.Length)))

# --- minimize it deliberately: does the capture freeze on demand? ------------
Say '--- SW_MINIMIZE on every window of the tree (the negative control)'
foreach ($h in $hs2) { [void][Win32]::ShowWindow($h, 6) }
Start-Sleep -Seconds 3
[void](Report-Windows 'after minimize')
[void](Call-Tool 'w04-move' 'running_game_run_stress_test' @{ action = 'snake_right'; count = 20 })
Start-Sleep -Seconds 3
$r3 = Call-Tool 'w05-shot-c' 'running_game_capture_screenshot' @{ save_path = 'user://diag-window-c.png' }
Say ("    shot-c: {0}" -f $r3.Substring(0, [Math]::Min(150, $r3.Length)))
Start-Sleep -Seconds 3
$r4 = Call-Tool 'w06-shot-d' 'running_game_capture_screenshot' @{ save_path = 'user://diag-window-d.png' }
Say ("    shot-d: {0}" -f $r4.Substring(0, [Math]::Min(150, $r4.Length)))

Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', ('taskkill /PID ' + $proc.Id + ' /T /F') -NoNewWindow -Wait -PassThru | Out-Null
Start-Sleep -Seconds 1

$userDir = Join-Path $env:APPDATA ("Godot\app_userdata\{0}" -f $Game)
Say '--- the four screenshots (user://) ---'
$hashes = @{}
foreach ($n in @('a','a2','b','c','d')) {
  $p = Join-Path $userDir ("diag-window-{0}.png" -f $n)
  if (Test-Path -LiteralPath $p) {
    $h = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash
    $hashes[$n] = $h
    Say ('    {0}  bytes={1}  sha256={2}' -f (Split-Path -Leaf $p), (Get-Item -LiteralPath $p).Length, $h.Substring(0, 16))
  } else { Say ('    {0}  MISSING' -f (Split-Path -Leaf $p)) }
}
Say ("A_vs_A2_IDENTICAL = {0}   (two shots 2 s apart, window as launched)" -f ($hashes['a'] -eq $hashes['a2']))
Say ("A_vs_B_IDENTICAL  = {0}   (before vs after SW_RESTORE)" -f ($hashes['a'] -eq $hashes['b']))
Say ("C_vs_D_IDENTICAL  = {0}   (two shots while minimized, 3 s + 20 injected actions apart)" -f ($hashes['c'] -eq $hashes['d']))

Say '--- the engine capture files ---'
$pngs = @(Get-ChildItem -LiteralPath $shots -Filter *.png -File -ErrorAction SilentlyContinue)
$distinct = @($pngs | ForEach-Object { (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash } | Sort-Object -Unique)
Say ("capture_pngs={0} distinct_sha256={1}" -f $pngs.Count, $distinct.Count)
Say ("out={0}" -f $Out)
