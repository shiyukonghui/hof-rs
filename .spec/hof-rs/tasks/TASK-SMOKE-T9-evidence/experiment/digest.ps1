param(
  [Parameter(Mandatory=$true)][string]$Root
)
$ErrorActionPreference = 'Stop'
$repo = 'F:\moonbit-hof-rs'
$full = (Resolve-Path -LiteralPath $Root).Path
$fullNorm = $full.TrimEnd('\')
$files = Get-ChildItem -LiteralPath $full -Recurse -Force -File
$rootLines = New-Object System.Collections.Generic.List[string]
$repoLines = New-Object System.Collections.Generic.List[string]
$newest = $null
foreach ($f in $files) {
  $h = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  $len = $f.Length
  $rel = ($f.FullName.Substring($fullNorm.Length + 1) -replace '\\','/').ToLowerInvariant()
  $rootLines.Add("$rel`t$len`t$h")
  $relr = ($f.FullName.Substring($repo.Length + 1) -replace '\\','/').ToLowerInvariant()
  $repoLines.Add("$relr`t$len`t$h")
  if ($newest -eq $null -or $f.LastWriteTime -gt $newest) { $newest = $f.LastWriteTime }
}
function Dig([System.Collections.Generic.List[string]]$ls) {
  $sorted = $ls | Sort-Object
  $text = [string]::Join("`n", $sorted)
  $sha = [System.Security.Cryptography.SHA256]::Create()
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
  return ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }) -join ''
}
Write-Output ("root={0}" -f $fullNorm)
Write-Output ("files={0}" -f $files.Count)
Write-Output ("digest_rootrelative={0}" -f (Dig $rootLines))
Write-Output ("digest_reporootrelative={0}" -f (Dig $repoLines))
Write-Output ("newest={0}" -f ($(if ($newest) { $newest.ToString('yyyy-MM-dd HH:mm:ss') } else { 'none' })))
