param(
  [Parameter(Mandatory=$true)][string]$Target
)
# Digest scheme (repo convention, per TASK-SMOKE-T8.md §4):
#   PowerShell 5.1 (culture zh-CN), Get-ChildItem -Recurse -Force -File
#   per file: path relative to the REPO ROOT, '\' -> '/', lowercased, + byte length + lower SHA256
#   three columns joined by TAB, rows joined by LF, NO trailing newline
#   row order = PowerShell Sort-Object (CULTURE ordering) -- ordering is part of the scheme
#   overall = SHA256 of the UTF-8 bytes of that string
$ErrorActionPreference = 'Stop'
$root = 'F:\moonbit-hof-rs'
$full = (Resolve-Path -LiteralPath $Target).Path
$files = Get-ChildItem -LiteralPath $full -Recurse -Force -File
$lines = New-Object System.Collections.Generic.List[string]
foreach ($f in $files) {
  $p = $f.FullName.Substring($root.Length).TrimStart('\')
  $rel = $p.Replace('\','/').ToLowerInvariant()
  $h = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  $lines.Add("$rel`t$($f.Length)`t$h")
}
$sorted = $lines | Sort-Object
$blob = [string]::Join("`n", $sorted)
$bytes = [System.Text.Encoding]::UTF8.GetBytes($blob)
$sha = [System.Security.Cryptography.SHA256]::Create()
$digest = ([System.BitConverter]::ToString($sha.ComputeHash($bytes)) -replace '-','').ToLowerInvariant()
$newest = ($files | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
"FILES=$($files.Count)"
"DIGEST=$digest"
"NEWEST=$($newest.ToString('yyyy-MM-dd HH:mm:ss'))"
"BYTES=$($bytes.Length)"
