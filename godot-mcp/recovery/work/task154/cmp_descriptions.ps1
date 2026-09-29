$ErrorActionPreference = 'Stop'
$u = [Text.Encoding]::UTF8
$c = ConvertFrom-Json ([IO.File]::ReadAllText('F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\docs\tools_list.renamed.json', $u))
Write-Host ('top-level keys: ' + ($c.PSObject.Properties.Name -join ','))
$t = @($c.result.tools)
Write-Host ('tools count = ' + $t.Count)
Write-Host ('names like test_report: ' + (($t | ForEach-Object { $_.name } | Where-Object { $_ -like '*test_report*' }) -join ' | '))
Write-Host ('names like node_properties: ' + (($t | ForEach-Object { $_.name } | Where-Object { $_ -like '*node_properties*' }) -join ' | '))
foreach ($n in @('editor_get_test_report', 'running_game_get_node_properties')) {
    $e = $null
    foreach ($x in $t) { if ([string]$x.name -eq $n) { $e = $x; break } }
    if ($null -ne $e) {
        Write-Host ('--- ' + $n + ' desc len=' + ([string]$e.description).Length)
        Write-Host ('    desc = "' + [string]$e.description + '"')
        Write-Host ('    clear.description = "' + [string]$e.inputSchema.properties.clear.description + '"')
        Write-Host ('    node_path.description = "' + [string]$e.inputSchema.properties.node_path.description + '"')
    } else {
        Write-Host ('--- ' + $n + ' NOT FOUND')
    }
}
Write-Host ''
Write-Host '=== baseline ==='
$b = ConvertFrom-Json ([IO.File]::ReadAllText('F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\docs\rename-baseline-tools-list.json', $u))
Write-Host ('baseline top-level keys: ' + ($b.PSObject.Properties.Name -join ','))
$bt = @($b.result.tools)
Write-Host ('baseline tools count = ' + $bt.Count)
foreach ($n in @('get_test_report', 'get_game_node_properties')) {
    $e = $null
    foreach ($x in $bt) { if ([string]$x.name -eq $n) { $e = $x; break } }
    if ($null -ne $e) {
        Write-Host ('--- ' + $n + ' desc len=' + ([string]$e.description).Length)
        Write-Host ('    desc = "' + [string]$e.description + '"')
        Write-Host ('    clear.description = "' + [string]$e.inputSchema.properties.clear.description + '"')
        Write-Host ('    node_path.description = "' + [string]$e.inputSchema.properties.node_path.description + '"')
    } else {
        Write-Host ('--- ' + $n + ' NOT FOUND')
    }
}
