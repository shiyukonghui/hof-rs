$ErrorActionPreference = 'Stop'
$u = [Text.Encoding]::UTF8
$c = ConvertFrom-Json ([IO.File]::ReadAllText('F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\docs\tools_list.renamed.json', $u))
$t = @($c.result.tools)
foreach ($n in @('editor_get_test_report', 'running_game_get_node_properties')) {
    foreach ($x in $t) {
        if ([string]$x.name -eq $n) {
            Write-Host ('### ' + $n)
            Write-Host ('description = ' + [string]$x.description)
            Write-Host ('inputSchema = ' + ($x.inputSchema | ConvertTo-Json -Depth 20 -Compress))
            Write-Host ''
            break
        }
    }
}
Write-Host '=== baseline raw entries ==='
$b = ConvertFrom-Json ([IO.File]::ReadAllText('F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\docs\rename-baseline-tools-list.json', $u))
$bt = @($b.result.tools)
foreach ($n in @('get_test_report', 'get_game_node_properties')) {
    foreach ($x in $bt) {
        if ([string]$x.name -eq $n) {
            Write-Host ('### ' + $n)
            Write-Host ('description = ' + [string]$x.description)
            Write-Host ('inputSchema = ' + ($x.inputSchema | ConvertTo-Json -Depth 20 -Compress))
            Write-Host ''
            break
        }
    }
}
