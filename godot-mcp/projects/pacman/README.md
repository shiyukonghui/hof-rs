# `pacman` — a C# Godot game (godot-mcp)

由 `godot-mcp\tools\new_game.ps1` 从 `_template` 生成。**所有游戏逻辑都是 C#**
（DECISIONS.md D138：至少 20 个经典小游戏、全部 C#）。

| | |
|---|---|
| 工程 | `godot-mcp\projects\pacman` |
| 程序集 | `pacman`（`pacman.csproj` = `Godot.NET.Sdk/4.8.0-dev`，`net8.0`） |
| 主场景 | `res://scenes/main.tscn` |
| 根脚本 | `res://src/PacManGame.cs`（类 `PacManGame`） |

## 构建（离线）

```cmd
cd /d F:\moonbit-hof-rs\godot-mcp\projects\pacman
dotnet build
```

`NuGet.config` 清空了包源、只指向引擎克隆自带的 `bin\GodotSharp\Tools\nupkgs`，所以**不需要网络**。
输出落在 `.godot\mono\temp\bin\Debug\`——正是引擎加载程序集的位置。

也可以让 MCP 端点代劳：`project_build_csharp`。

## 跑试测

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File F:\moonbit-hof-rs\godot-mcp\tools\run_game_session.ps1 -Game pacman
```

驱动会起编辑器 9888 + 游戏 9889（`--mcp-trace` + `--mcp-capture=every_call`）、
重放 `godot-mcp\tools\sessions\pacman\session.json` 里的调用、跑台账，并在
`godot-mcp\runs\pacman\<run-tag>\report.md` 产出**每游戏报告**
（判定分布 + `facts_complete` + 独立复算的像素差 + 缺陷清单）。

## 设计约定（每个游戏都要遵守）

1. **可观测状态必须是 Godot 属性**：`[Export]` 字段或节点属性。私有字段里的状态
   在 trace 上不可见，也就无法判定一次调用到底有没有效果。
2. **确定性优先**：新进程不要自己动起来。Pong 的 run-1 缺陷 P-1 就是「测试驱动还没发第一条
   调用，游戏已经自己打完几分」——修复方式是开局把球停住、等一条显式发球。
3. **每条断言都要有反例**：同一批调用里必须有一条**注定失败**的断言，否则「断言通过」
   证明不了断言机制本身在工作。
