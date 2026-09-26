
param([string]$F)
$t=$null; $e=$null
[void][System.Management.Automation.Language.Parser]::ParseFile($F,[ref]$t,[ref]$e)
if ($e) { foreach ($x in $e) { Write-Output ($x.ErrorId + ':' + $x.Message + '@' + $x.Extent.StartLineNumber) } } else { Write-Output 'CLEAN' }
