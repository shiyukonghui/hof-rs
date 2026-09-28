# TASK-148 probe: can we see the exported game's main window at all?
$ErrorActionPreference = 'Continue'
Add-Type @'
using System;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public class WinApi {
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetWindowTextW(IntPtr hWnd, StringBuilder s, int n);
    [DllImport("user32.dll")] static extern int GetWindowTextLengthW(IntPtr hWnd);
    public static List<string> WindowsForPid(uint target) {
        var res = new List<string>();
        EnumWindows((h, l) => {
            uint p; GetWindowThreadProcessId(h, out p);
            if (p == target) {
                int len = GetWindowTextLengthW(h);
                var sb = new StringBuilder(len + 1);
                GetWindowTextW(h, sb, sb.Capacity);
                res.Add(h.ToInt64().ToString() + "\t" + (IsWindowVisible(h) ? "1" : "0") + "\t" + sb.ToString());
            }
            return true;
        }, IntPtr.Zero);
        return res;
    }
}
'@

$g = 'pong'
$dir = "F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\$g"
$exe = Join-Path $dir "$g.exe"
$cmd = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', ('"' + $exe + '"')) -WorkingDirectory $dir -PassThru
$gp = $null
for ($t = 0; $t -lt 100 -and -not $gp; $t++) {
    Start-Sleep -Milliseconds 200
    $child = Get-CimInstance Win32_Process -Filter ("ParentProcessId=" + $cmd.Id) -ErrorAction SilentlyContinue |
             Where-Object { $_.Name -eq "$g.exe" } | Select-Object -First 1
    if ($child) { $gp = Get-Process -Id ([int]$child.ProcessId) -ErrorAction SilentlyContinue }
}
Write-Output ("game pid = " + $(if ($gp) { $gp.Id } else { 'NOT-FOUND' }))
for ($t = 0; $t -lt 25; $t++) {
    Start-Sleep -Milliseconds 400
    if ($gp) {
        $gp.Refresh()
        $w = [WinApi]::WindowsForPid([uint32]$gp.Id)
        Write-Output ("t={0}s MainWindowHandle={1} title='{2}' enum=[{3}]" -f `
            [Math]::Round($t * 0.4, 1), $gp.MainWindowHandle, $gp.MainWindowTitle, ($w -join ' ; '))
        if ($gp.MainWindowTitle -ne '') { break }
    }
}
if ($gp) { try { $gp.Kill() } catch {} }
try { if (-not $cmd.HasExited) { $cmd.Kill() } } catch {}
Start-Sleep -Seconds 2
Get-Process -Name $g -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Output ("after: game procs=" + @(Get-Process -Name $g -ErrorAction SilentlyContinue).Count)
