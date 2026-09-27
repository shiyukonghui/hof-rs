# `snake` — a C# Godot game (godot-mcp)

由 `godot-mcp\tools\new_game.ps1` 从 `_template` 生成。**所有游戏逻辑都是 C#**
（DECISIONS.md D138：至少 20 个经典小游戏、全部 C#）。

| | |
|---|---|
| 工程 | `godot-mcp\projects\snake` |
| 程序集 | `snake`（`snake.csproj` = `Godot.NET.Sdk/4.8.0-dev`，`net8.0`） |
| 主场景 | `res://scenes/main.tscn` |
| 根脚本 | `res://src/SnakeGame.cs`（类 `SnakeGame`） |

## 玩法

800×600。目标：eat the food and grow without hitting the wall or yourself。

**开局是「等待开始」**：新进程把蛇画在场上但**不动**（`WaitingForStart=true`，
`Ticks` 保持 0），按一次方向键才开始走。这是 TASK-133 的修复：旧版开局自带
`dir=(1,0)` 且立刻步进，1.52 s（19 步 × 0.08 s）就自己撞右墙，第一帧就是失败画面。

| 操作 | 动作名 | 键 |
|---|---|---|
| turn up | `snake_up` | `W` |
| turn down | `snake_down` | `S` |
| turn left | `snake_left` | `A` |
| turn right | `snake_right` | `D` |
| pause | `snake_pause` | `P` |
| restart | `snake_restart` | `R` |

`snake_restart` 的规则（TASK-133）：**正在进行的这一局拒绝重开**（记
`LastRejectedAction="restart: the run is still live"`，不悄悄清掉玩家的进度）；
已结束 / 已暂停 / 还在等待开始时，重开把比分、蛇身、方向、计时器都归零，
并回到同样的「等待开始」状态。

> 动作名就是 `project.godot` 的 `[input]` 里的名字，可用 `running_game_capture_screenshot` + `Input.action_press` 由 MCP 端点精确复现；
> 可玩性门（`tools/playability_gate.py`）会逐条注入这些键，并要求**确实出现可归因的状态或像素变化**。
> 上表与 `project.godot` 的 `[input]` 段、`tools/playability_controls.json ->
> games.snake.required_ui` 三处必须一致（Z1 的核对口径）。

## 构建（离线）

```cmd
cd /d F:\moonbit-hof-rs\godot-mcp\projects\snake
dotnet build
```

`NuGet.config` 清空了包源、只指向引擎克隆自带的 `bin\GodotSharp\Tools\nupkgs`，所以**不需要网络**。
输出落在 `.godot\mono\temp\bin\Debug\`——正是引擎加载程序集的位置。

也可以让 MCP 端点代劳：`project_build_csharp`。

## 跑试测

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File F:\moonbit-hof-rs\godot-mcp\tools\run_game_session.ps1 -Game snake
```

驱动会起编辑器 9888 + 游戏 9889（`--mcp-trace` + `--mcp-capture=every_call`）、
重放 `godot-mcp\tools\sessions\snake\session.json` 里的调用、跑台账，并在
`godot-mcp\runs\snake\<run-tag>\report.md` 产出**每游戏报告**
（判定分布 + `facts_complete` + 独立复算的像素差 + 缺陷清单）。

## 设计约定（每个游戏都要遵守）

1. **可观测状态必须是 Godot 属性**：`[Export]` 字段或节点属性。私有字段里的状态
   在 trace 上不可见，也就无法判定一次调用到底有没有效果。
2. **确定性优先**：新进程不要自己动起来。Pong 的 run-1 缺陷 P-1 就是「测试驱动还没发第一条
   调用，游戏已经自己打完几分」——修复方式是开局把球停住、等一条显式发球。
3. **每条断言都要有反例**：同一批调用里必须有一条**注定失败**的断言，否则「断言通过」
   证明不了断言机制本身在工作。
