$ErrorActionPreference = 'Stop'
$repo = 'F:\moonbit-hof-rs\godot-mcp\godot'
$contract = Join-Path $repo 'modules\mcp_server\docs\tools_list.renamed.json'
$baseline = Join-Path $repo 'modules\mcp_server\docs\rename-baseline-tools-list.json'

Write-Host '=== working tree bytes + git blob (must equal HEAD for both) ==='
foreach ($f in @(@{ p = $contract; rel = 'modules/mcp_server/docs/tools_list.renamed.json'; label = 'tools_list.renamed.json' },
                 @{ p = $baseline; rel = 'modules/mcp_server/docs/rename-baseline-tools-list.json'; label = 'rename-baseline-tools-list.json' })) {
    $item = Get-Item $f.p
    $sha = (Get-FileHash -Algorithm SHA256 $f.p).Hash.ToLower()
    $wtBlob = (& git -C $repo hash-object -- $f.rel).Trim()
    $headBlob = (& git -C $repo rev-parse ('HEAD:' + $f.rel)).Trim()
    $headSize = (& git -C $repo cat-file -s $headBlob).Trim()
    Write-Host ("{0}: bytes={1} sha256={2}" -f $f.label, $item.Length, $sha)
    Write-Host ("    worktree blob={0}" -f $wtBlob)
    Write-Host ("    HEAD     blob={0} size={1}" -f $headBlob, $headSize)
    Write-Host ("    BYTE-IDENTICAL TO HEAD = {0}" -f (($wtBlob -ceq $headBlob) -and ([int]$item.Length -eq [int]$headSize)))
}
