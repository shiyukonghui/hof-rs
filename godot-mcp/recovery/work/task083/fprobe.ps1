# TASK-083 F: read-only evidence probe. Nothing here writes to F:.
$ErrorActionPreference = 'Continue'
$out = @()
$p = 'F:\moonbit-hof-rs\DECISIONS.md'
if (Test-Path $p) {
  $f = Get-Item $p
  $h = Get-FileHash $p -Algorithm SHA256
  $out += ('DECISIONS.md bytes=' + $f.Length + ' LastWriteTimeUtc=' + $f.LastWriteTimeUtc.ToString('o') + ' sha256=' + $h.Hash)
} else { $out += 'DECISIONS.md MISSING' }
$d = Get-PSDrive F -ErrorAction SilentlyContinue
if ($d) { $out += ('F: Used=' + $d.Used + ' Free=' + $d.Free) } else { $out += 'F: drive not visible' }
$c = 'F:\RustProjects\godot-mcp-pro\code\godot'
if (Test-Path $c) { $out += ('code\godot children=' + (Get-ChildItem $c -Force | Measure-Object).Count) } else { $out += 'code\godot MISSING' }
$t = 'F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json'
if (Test-Path $t) {
  $g = Get-Item $t
  $hh = Get-FileHash $t -Algorithm SHA256
  $out += ('tools_list.json bytes=' + $g.Length + ' sha256=' + $hh.Hash)
} else { $out += 'tools_list.json MISSING' }
$out | ForEach-Object { Write-Output $_ }
