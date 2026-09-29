$ErrorActionPreference = 'Stop'
$repo = 'F:\moonbit-hof-rs'
$spec = 'db2eed7^:tests/fixtures/mcp/tools_list.json'
$out = "$env:TEMP\task154-oldfixture.json"
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = 'git'
$psi.Arguments = '-C "' + $repo + '" cat-file blob "' + $spec + '"'
$psi.RedirectStandardOutput = $true
$psi.UseShellExecute = $false
$p = [System.Diagnostics.Process]::Start($psi)
$stream = $p.StandardOutput.BaseStream
$fs = [IO.File]::Create($out)
$stream.CopyTo($fs)
$fs.Close()
$p.WaitForExit()
Write-Host ('git exit = ' + $p.ExitCode)
$bytes = [IO.File]::ReadAllBytes($out)
Write-Host ('bytes = ' + $bytes.Length)
Write-Host ('sha256 = ' + (Get-FileHash -Algorithm SHA256 $out).Hash.ToLower())
