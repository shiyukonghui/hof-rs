# copy_payload_index.ps1 - TASK-078: copy the machine-readable spools into staging\__payload-index\
# Read-only on the sources; writes ONLY under C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\.
# Pure ASCII. No shell redirection (Out-File -FilePath / -LiteralPath only).
$ErrorActionPreference = 'Stop'
$ROOT = 'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
$W = Join-Path $ROOT 'work'
$DST = Join-Path $ROOT 'staging\__payload-index'
if (-not (Test-Path -LiteralPath $DST)) { New-Item -ItemType Directory -Path $DST | Out-Null }

$files = @(
  'events-write.jsonl','events-edit.jsonl','events-read.jsonl','events-diff.jsonl',
  'events-termfile.jsonl','events-termdump.jsonl','events-termlog.jsonl','events-misc.jsonl',
  'reconstruction.jsonl','gen-runs.jsonl','ps1-parse.json','swaps.json'
)
foreach ($f in $files) {
    $src = Join-Path $W $f
    if (Test-Path -LiteralPath $src) {
        Copy-Item -LiteralPath $src -Destination (Join-Path $DST $f) -Force
    } else {
        Write-Output ("missing (skipped): " + $f)
    }
}

$lines = @(
 '# TASK-078 payload index (machine-readable spool)',
 '',
 'Extracted from C:\Users\wyl\AppData\Local\Temp\mcp-recovery\transcripts\*.jsonl (178 files, read-only).',
 'One JSON object per line. Nothing here was produced by executing recovered code.',
 '',
 '| file | contents |',
 '|---|---|',
 '| events-write.jsonl | one row per `write` tool call: path, content, seq, time, result |',
 '| events-edit.jsonl | one row per `edit` tool call: path, old_string, new_string, replace_all, seq, time |',
 '| events-read.jsonl | one row per `read` tool call: path, offset, totalLines, the numbered line array |',
 '| events-diff.jsonl | one row per captured git/diff command with its full output |',
 '| events-termfile.jsonl | term commands that look like file writers (Set-Content/Out-File/Copy-Item/python open-w) |',
 '| events-termdump.jsonl | term commands that dump file contents (Get-Content/type/cat) with output |',
 '| events-termlog.jsonl | every term/bash call (command + description + output length only) |',
 '| events-misc.jsonl | read calls whose result carried no line array (errors, directories, images) |',
 '| reconstruction.jsonl | one row per reconstructed path: chosen candidate, confidence, failures, coverage, source |',
 '| gen-runs.jsonl | every captured command touching the contract or the generator, with output |',
 '| ps1-parse.json | PowerShell parser result (errors only) for each staged .ps1 |',
 '| swaps.json | candidate swaps decided by objective evidence (ast.parse) |',
 '',
 'Duplicate read rows (same transcript + seq + callId + offset) were removed once (305 rows).',
 'Companion .diff/.cmd.txt pairs live in staging\__diffs\. See EXTRACTION-MANIFEST.md for the per-file table.'
)
$lines | Out-File -FilePath (Join-Path $DST 'README.md') -Encoding utf8

$dstFiles = Get-ChildItem -LiteralPath $DST -File
Write-Output ("payload-index files: " + $dstFiles.Count)
Write-Output ("payload-index bytes: " + ($dstFiles | Measure-Object Length -Sum).Sum)
foreach ($d in $dstFiles) { Write-Output ("  " + $d.Name + "  " + $d.Length) }
