# `puzzlebobble` — a C# Godot game (godot-mcp)

由 `godot-mcp\tools\new_game.ps1` 从 `_template` 生成。**所有游戏逻辑都是 C#**
（DECISIONS.md D138：至少 20 个经典小游戏、全部 C#）。

| | |
|---|---|
| 工程 | `godot-mcp\projects\puzzlebobble` |
| 程序集 | `puzzlebobble`（`puzzlebobble.csproj` = `Godot.NET.Sdk/4.8.0-dev`，`net8.0`） |
| 主场景 | `res://scenes/main.tscn` |
| 根脚本 | `res://src/PuzzleBobbleGame.cs`（类 `PuzzleBobbleGame`） |

## 玩法

800×600。目标：aim and shoot bubbles to clear the board。

**瞄准是可见的**（TASK-133 §1.A.4 的修复）：`pb_left`/`pb_right` 现在会重画
**瞄准点串**（`AimDot0..5`，沿 `Tick()` 走的同一条整数射线，含侧壁反射），
按一次键就在同一帧看到方向改变。旧实现只改 `AngleIndex` 属性、不重画，
瞄准的像素差是 **0**（TASK-131 记 P2 翻红，当时刻意没有放宽判据）。
五个瞄准档位现在是一个**循环**：最左再往左会绕到最右（反之亦然），
两端不再有「按了没反应」的死点。

**射弹会自己落地并结算**（TASK-135 §1.A.2 的修复）：`AutoClock` 默认 **20 步/秒**，
游戏**自己**按时间推进 `Tick()`，一发泡泡从射手飞到盘面约 0.5 s。旧版 `AutoClock=0`，
`Tick()` 的唯一生产者是 MCP 的 `StepFrames()` 钩子，于是**没有人推帧时打出一发就整局冻结**：
弹道停在射手正上方（`Steps=0` 而 `Ticks` 继续涨——渲染在跑、模拟没跑），
而 `Shoot()` 在 `ProjActive` 时拒绝再开火 ⇒ **玩家永远打不出第二发**。
空闲时钟只把 `Steps` 加一、不改像素，所以零输入对照窗仍然干净；
确定性入口（`ForceTestState` / `StepFrames`）不受影响：`ResetCounters` 仍把它置 0。

| 操作 | 动作名 | 键 |
|---|---|---|
| aim left | `pb_left` | `A` |
| aim right | `pb_right` | `D` |
| shoot | `pb_shoot` | `SPACE` |

> 动作名就是 `project.godot` 的 `[input]` 里的名字，可用 `running_game_capture_screenshot` + `Input.action_press` 由 MCP 端点精确复现；
> 可玩性门（`tools/playability_gate.py`）会逐条注入这些键，并要求**确实出现可归因的状态或像素变化**。

## 构建（离线）

```cmd
cd /d F:\moonbit-hof-rs\godot-mcp\projects\puzzlebobble
dotnet build
```

`NuGet.config` 清空了包源、只指向引擎克隆自带的 `bin\GodotSharp\Tools\nupkgs`，所以**不需要网络**。
输出落在 `.godot\mono\temp\bin\Debug\`——正是引擎加载程序集的位置。

也可以让 MCP 端点代劳：`project_build_csharp`。

## 跑试测

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File F:\moonbit-hof-rs\godot-mcp\tools\run_game_session.ps1 -Game puzzlebobble
```

驱动会起编辑器 9888 + 游戏 9889（`--mcp-trace` + `--mcp-capture=every_call`）、
重放 `godot-mcp\tools\sessions\puzzlebobble\session.json` 里的调用、跑台账，并在
`godot-mcp\runs\puzzlebobble\<run-tag>\report.md` 产出**每游戏报告**
（判定分布 + `facts_complete` + 独立复算的像素差 + 缺陷清单）。

## 设计约定（每个游戏都要遵守）

1. **可观测状态必须是 Godot 属性**：`[Export]` 字段或节点属性。私有字段里的状态
   在 trace 上不可见，也就无法判定一次调用到底有没有效果。
2. **确定性优先**：新进程不要自己动起来。Pong 的 run-1 缺陷 P-1 就是「测试驱动还没发第一条
   调用，游戏已经自己打完几分」——修复方式是开局把球停住、等一条显式发球。
3. **每条断言都要有反例**：同一批调用里必须有一条**注定失败**的断言，否则「断言通过」
   证明不了断言机制本身在工作。
