# `pong` — 第 1 个 C# 小游戏（godot-mcp, TASK-091）

由 `godot-mcp\tools\new_game.ps1` 从 `_template` 生成，并在一次 MCP 会话里长成完整的 Pong。
**所有游戏逻辑都是 C#**（DECISIONS.md D138：至少 20 个经典小游戏、全部 C#）。

| | |
|---|---|
| 工程 | `godot-mcp\projects\pong` |
| 程序集 | `pong`（`pong.csproj` = `Godot.NET.Sdk/4.8.0-dev`，`net8.0`） |
| 主场景 | `res://scenes/main.tscn` |
| 根脚本 | `res://src/PongGame.cs`（类 `PongGame`） |
| 球 / 板 | `res://src/Ball.cs`（类 `Ball`）、`res://src/Paddle.cs`（类 `Paddle`） |

## 玩法

800×600。球 16×16，板 16×100，**先到 5 分者胜**。
`W`/`S` 控制左板，`↑`/`↓` 控制右板，`Space` 发球。
一局开始时球停在中央**不动**，等一次发球。

## 构建（离线）

```cmd
cd /d F:\moonbit-hof-rs\godot-mcp\projects\pong
dotnet build
```

`NuGet.config` 清空了包源、只指向引擎克隆自带的 `bin\GodotSharp\Tools\nupkgs`，所以**不需要网络**。
输出落在 `.godot\mono\temp\bin\Debug\`——正是引擎加载程序集的位置。
也可以让 MCP 端点代劳：`project_build_csharp`。

## 跑试测

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File F:\moonbit-hof-rs\godot-mcp\tools\run_game_session.ps1 -Game pong
```

驱动起编辑器 9888 + 游戏 9889（`--mcp-trace` + `--mcp-capture=every_call`）、
重放 `godot-mcp\tools\sessions\pong\session.json` 的 24 + 29 条调用、跑台账，并在
`godot-mcp\runs\pong\<run-tag>\report.md` 产出**每游戏报告**。

要从零重来一遍（会删掉本工程的构建产物，`runs\` 里的证据不动）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File F:\moonbit-hof-rs\godot-mcp\tools\reset_game.ps1 -Name pong -Confirm
```

## 这次会话证明了什么

每次调用都留下一条台账行，判定只有四种「有效/无效」结论，**没有「应该动了」**：

| 主张 | 证据 |
|---|---|
| 球真的动了 | `PONG_TICK` 里球从 (392,268) 到 (670,447)；`running_game_set_node_property` 那几行的截图**独立复算**出 62/92/120/512/512/96 px 的像素差 |
| 板真的动了 | 注入 `pong_left_up` 两次再 `pong_left_down` 一次，`PONG_NUDGE` 给出 y=96 → 8 → 138（= `Speed 520 × InjectedStepSeconds 0.25`） |
| 比分真的变了 | `running_game_assert_node_state{ScoreRight.text == "1"}` → `"2"`，`PONG_SCORE` 同刻打印 |
| 胜负真的判了 | `WinLabel.text = "GAME OVER - RIGHT WINS 0:2"`，`PONG_OVER winner=RIGHT` |
| 断言不是橡皮图章 | 同一批里有 3 条**注定失败**的断言（板位置 eq、比分、屏幕文本），台账都给出 `assertion_failed` |
| 空转也看得见 | 球停住后 `PONG_TICK` 连续 6 次 `v=(0,0)`、位置不动；`running_game_get_node_property_samples` 的 30 帧同样不动 |

## 设计约定（每个游戏都要遵守）

1. **可观测状态必须是 Godot 属性**：`[Export]` 字段或节点属性。私有字段里的状态在 trace 上
   不可见，也就无法判定一次调用到底有没有效果（`Ball.Velocity`、`Paddle.Speed`、`WinScore` 都是 `[Export]`）。
2. **确定性优先**：新进程不要自己动起来。run-1 的缺陷 P-1 就是「驱动还没发第一条调用，游戏已经
   自己打完几分」——修复是开局把球停住、等一条显式发球。
3. **每条断言都要有反例**：同一批调用里必须有一条**注定失败**的断言。
