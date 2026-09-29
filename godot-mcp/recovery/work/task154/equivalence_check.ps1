$ErrorActionPreference = 'Stop'
$u = [Text.Encoding]::UTF8

function Load([string]$p) {
    $bytes = [IO.File]::ReadAllBytes($p)
    $text = [Text.Encoding]::UTF8.GetString($bytes)
    if ($text.Length -gt 0 -and $text[0] -eq [char]0xFEFF) { $text = $text.Substring(1) }
    return @{ bytes = $bytes.Length; json = (ConvertFrom-Json $text) }
}

$baselinePath = 'F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\docs\rename-baseline-tools-list.json'
$a = Load $baselinePath
$b = Load "$env:TEMP\task154-oldfixture.json"
Write-Host ("baseline bytes={0} tools={1}" -f $a.bytes, @($a.json.result.tools).Count)
Write-Host ("db2eed7^ bytes={0} tools={1}" -f $b.bytes, @($b.json.result.tools).Count)

function Entry($json, [string]$name) {
    foreach ($t in @($json.result.tools)) { if ([string]$t.name -eq $name) { return $t } }
    return $null
}

foreach ($n in @('get_test_report', 'get_game_node_properties')) {
    $ea = Entry $a.json $n
    $eb = Entry $b.json $n
    Write-Host ('--- ' + $n + ' baseline present=' + ($null -ne $ea) + ' db2eed7^ present=' + ($null -ne $eb))
    if ($null -ne $ea -and $null -ne $eb) {
        $da = [string]$ea.description
        $db = [string]$eb.description
        $sa = ($ea.inputSchema | ConvertTo-Json -Depth 30 -Compress)
        $sb = ($eb.inputSchema | ConvertTo-Json -Depth 30 -Compress)
        Write-Host ('    description bytes equal = ' + ([Text.Encoding]::UTF8.GetByteCount($da) -eq [Text.Encoding]::UTF8.GetByteCount($db)) + ' ; chars equal = ' + ($da -ceq $db))
        Write-Host ('    description = "' + $da + '"')
        Write-Host ('    inputSchema equal = ' + ($sa -ceq $sb))
        Write-Host ('    clear.description equal = ' + (([string]$ea.inputSchema.properties.clear.description) -ceq ([string]$eb.inputSchema.properties.clear.description)))
        Write-Host ('    node_path.description equal = ' + (([string]$ea.inputSchema.properties.node_path.description) -ceq ([string]$eb.inputSchema.properties.node_path.description)))
    }
}

Write-Host ''
Write-Host '=== full raw byte comparison of the two JSON documents ==='
$same = $a.bytes -eq $b.bytes
if ($same) {
    $ba = [IO.File]::ReadAllBytes($baselinePath)
    $bb = [IO.File]::ReadAllBytes("$env:TEMP\task154-oldfixture.json")
    for ($i = 0; $i -lt $ba.Length; $i++) { if ($ba[$i] -ne $bb[$i]) { $same = $false; Write-Host ("first differing byte at offset " + $i); break } }
}
Write-Host ('whole-file byte identical = ' + $same)
