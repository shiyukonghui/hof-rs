param(
  [Parameter(Mandatory=$true)][string]$Session,
  [string]$Label = ''
)
# TASK-103 iron rule 5, the PowerShell half: the same file read by PowerShell 5.1's
# own JSON parser, because that is the parser `run_game_session.ps1` uses. Python
# and PS 5.1 disagree about enough corner cases (surrogate pairs, duplicate keys,
# numbers out of range) that one parser is not evidence for the other.
$ErrorActionPreference = 'Stop'
$path = (Resolve-Path -LiteralPath $Session).Path
$doc = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
$calls = @($doc.calls)
$editor = @($calls | Where-Object { "$($_.port)" -eq 'editor' }).Count
$game = @($calls | Where-Object { "$($_.port)" -eq 'game' }).Count
$tags = @($calls | ForEach-Object { "$($_.tag)" })
$unique = @($tags | Sort-Object -Unique).Count
Write-Output ("PS_PARSE OK {0} calls={1} editor={2} game={3} unique_tags={4}" -f $Label, $calls.Count, $editor, $game, $unique)
if ($unique -ne $calls.Count) { Write-Output "PS_PARSE FAIL: duplicate tags"; exit 1 }
exit 0
