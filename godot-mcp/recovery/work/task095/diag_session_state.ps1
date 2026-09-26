# diag_session_state.ps1 -- TASK-095 A: session / display forensics (READ-ONLY).
#
# It only reads: session tables, process lists, WMI classes, system metrics,
# the event log and powercfg. It writes one text file inside $Out.
#
# Iron rule 1: no shell redirection -- this script uses Set-Content/-OutFile only.
# Iron rule 2: nothing destructive.
param(
  [string]$Root = 'F:\moonbit-hof-rs\godot-mcp',
  [string]$Out  = ''
)
$ErrorActionPreference = 'Continue'
if (-not $Out) {
  $Out = Join-Path $Root ('recovery\work\task095\forensics\session-state-{0}.txt' -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
}
$lines = New-Object System.Collections.Generic.List[string]
function S([string]$t) { $lines.Add($t); Write-Host $t }
function Run([string]$title, [string]$cmd) {
  S ''
  S ('=== ' + $title + ' ===')
  try {
    $o = Invoke-Expression $cmd 2>&1 | Out-String -Width 200
    foreach ($l in ($o -split "`r?`n")) { if ($l.TrimEnd().Length -gt 0) { S $l.TrimEnd() } }
  } catch { S ('  (failed: ' + $_.Exception.Message + ')') }
}

S ('TASK-095 A -- session / display forensics -- ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
S ('host=' + $env:COMPUTERNAME + ' user=' + $env:USERNAME)

Run 'our own process session' 'Get-Process -Id $PID | Select-Object Id,SessionId,ProcessName | Format-Table -AutoSize'
Run 'query session' 'query session'
Run 'qwinsta' 'qwinsta'
Run 'query user' 'query user'
Run 'dwm / logonui / winlogon / explorer' 'Get-Process dwm,LogonUI,winlogon,explorer -ErrorAction SilentlyContinue | Select-Object Id,SessionId,ProcessName,StartTime | Format-Table -AutoSize'
Run 'win32 desktop monitor' 'Get-CimInstance Win32_DesktopMonitor | Select-Object Name,DeviceID,Availability,ScreenWidth,ScreenHeight,PNPDeviceID | Format-List'
Run 'wmi monitor basic params' 'Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorBasicDisplayParams -ErrorAction SilentlyContinue | Select-Object InstanceName,Active,MaxHorizontalImageSize,MaxVerticalImageSize | Format-List'
Run 'wmi monitor id' 'Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorID -ErrorAction SilentlyContinue | Select-Object InstanceName,YearOfManufacture,UserFriendlyName | Format-List'
Run 'video controllers' 'Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion,Availability,CurrentHorizontalResolution,CurrentVerticalResolution,CurrentRefreshRate,VideoModeDescription,Status | Format-List'
Run 'pnp display devices' 'Get-PnpDevice -Class Display -ErrorAction SilentlyContinue | Select-Object Status,FriendlyName,InstanceId | Format-List'
Run 'pnp monitor devices' 'Get-PnpDevice -Class Monitor -ErrorAction SilentlyContinue | Select-Object Status,FriendlyName,InstanceId | Format-List'
Run 'screens' 'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::AllScreens | Select-Object DeviceName,Bounds,Primary,WorkingArea | Format-List'
Run 'system metrics' @'
Add-Type -TypeDefinition "using System;using System.Runtime.InteropServices;public class T095U{[DllImport(\"user32.dll\")]public static extern int GetSystemMetrics(int i);[DllImport(\"user32.dll\")]public static extern IntPtr GetForegroundWindow();[DllImport(\"user32.dll\")]public static extern IntPtr OpenInputDesktop(int f,bool b,int a);[DllImport(\"user32.dll\")]public static extern bool SwitchDesktop(IntPtr h);[DllImport(\"dwmapi.dll\")]public static extern int DwmIsCompositionEnabled(out bool e);[DllImport(\"user32.dll\")]public static extern int GetWindowTextW(IntPtr h,System.Text.StringBuilder s,int n);[DllImport(\"user32.dll\")]public static extern int GetClassNameW(IntPtr h,System.Text.StringBuilder s,int n);}"
$b=New-Object System.Text.StringBuilder 512
$c=New-Object System.Text.StringBuilder 512
[T095U]::GetClassNameW([T095U]::GetForegroundWindow(),$c,512)|Out-Null
[T095U]::GetWindowTextW([T095U]::GetForegroundWindow(),$b,512)|Out-Null
$comp=$false;[T095U]::DwmIsCompositionEnabled([ref]$comp)|Out-Null
$d=[T095U]::OpenInputDesktop(0,$false,0x0100)
"SM_CMONITORS=" + [T095U]::GetSystemMetrics(80)
"SM_CXSCREEN=" + [T095U]::GetSystemMetrics(0) + " SM_CYSCREEN=" + [T095U]::GetSystemMetrics(1)
"SM_REMOTESESSION=" + [T095U]::GetSystemMetrics(4096)
"SM_CXVIRTUALSCREEN=" + [T095U]::GetSystemMetrics(78) + " SM_CYVIRTUALSCREEN=" + [T095U]::GetSystemMetrics(79) + " SM_CMONITORS_ALL=" + [T095U]::GetSystemMetrics(80)
"DwmIsCompositionEnabled=" + $comp
"OpenInputDesktop_handle=" + $d
"foreground_hwnd=" + [T095U]::GetForegroundWindow() + " class='" + $c.ToString() + "' title='" + $b.ToString() + "'"
'@
Run 'remote / streaming tools present' 'Get-Process | Where-Object { $_.ProcessName -match "GameViewer|ToDesk|Sunlogin|AnyDesk|Parsec|TeamViewer|mstsc|RustDesk|vnc|NetEase|UU" } | Select-Object Id,SessionId,ProcessName,Path | Format-Table -AutoSize'
Run 'rdp/vnc listeners' 'Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in 3389,5900,5901,5938,8000,5800 } | Select-Object LocalAddress,LocalPort,OwningProcess | Format-Table -AutoSize'
Run 'GameViewer tcp' 'Get-NetTCPConnection -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -in (Get-Process GameViewer,GameViewerServer,GameViewerService,GameViewerHealthd -ErrorAction SilentlyContinue).Id } | Select-Object LocalAddress,LocalPort,RemoteAddress,RemotePort,State | Format-Table -AutoSize'
Run 'powercfg requests' 'powercfg /requests'
Run 'powercfg lastwake' 'powercfg /lastwake'
Run 'dwm composition registry' 'Get-ItemProperty "HKCU:\Software\Microsoft\Windows\DWM" -ErrorAction SilentlyContinue | Select-Object Composition,CompositionPolicy,EnableWindowColorization | Format-List'
Run 'display-related events (last 8h)' @'
$since = (Get-Date).AddHours(-8)
Get-WinEvent -FilterHashtable @{LogName="System"; StartTime=$since} -ErrorAction SilentlyContinue |
  Where-Object { $_.ProviderName -match "Display|Dwm|nvlddmkm|Kernel-Power|Win32k|Video" -or $_.Message -match "display|monitor|DWM" } |
  Select-Object -First 60 TimeCreated,ProviderName,Id,LevelDisplayName,@{n="Msg";e={($_.Message -split "`r?`n")[0]}} | Format-Table -AutoSize -Wrap
'@
Run 'session change / logon events (last 8h)' @'
$since = (Get-Date).AddHours(-8)
Get-WinEvent -FilterHashtable @{LogName="System"; ProviderName="Microsoft-Windows-TerminalServices-LocalSessionManager"; StartTime=$since} -ErrorAction SilentlyContinue |
  Select-Object -First 30 TimeCreated,Id,@{n="Msg";e={($_.Message -split "`r?`n")[0]}} | Format-Table -AutoSize -Wrap
'@
Run 'nvidia-smi' '& nvidia-smi --query-gpu=name,driver_version,utilization.gpu,memory.used,temperature.gpu,pstate --format=csv 2>&1'

Set-Content -LiteralPath $Out -Value $lines -Encoding UTF8
Write-Host ('out=' + $Out)
