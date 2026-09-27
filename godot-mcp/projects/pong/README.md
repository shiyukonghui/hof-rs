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

**TASK-133 修的两条规则 + 一个对手**（原实现让比赛在无人操作时自己 5:0 结束）：

1. **`AutoServe` 默认改为 `false`**。原实现每得一分自动重发球，而右板没有任何
   输入会让它跟球，于是球径直飞出右侧；stdout 实测 `pong/jev` 在 **23 s** 内
   `PONG_SCORE scored_by=LEFT`×5 → `PONG_OVER winner=LEFT left=5 right=0`
   （真实键臂 12 s），TASK-132 的模型玩家回路因此只有 1–5 步落在「还活着的比赛」里。
   改成 `false` 后，每一分都把球**停在中央**（stdout `PONG_PARKED`），
   下一球由一次显式 `pong_serve`（SPACE）发出 —— 这正是本 README 第 18 行一直
   写的规则，比赛不再能在没有人操作的情况下自己打完。
2. **球在飞时发球被拒绝**（旧实现会把球瞬移回中央、`Velocity` 直接重置，
   于是「按了 SPACE」看起来等于没按；TASK-132 记了 10 步里 9 步如此）。
   现在 `Ball.Velocity != 0` 时 `Serve()` 只说「不行」：
   `LastRejectedAction="serve: the ball is already in flight"` +
   stdout `PONG_SERVE_REFUSED`，球的位置与速度一个字节都不动。
3. **右板对手**（`RightPaddleAutoFollow` 默认 `true`，`OpponentSpeed=340`、
   `OpponentSkill=0.78`）：球**正在朝右飞**时，右板以有限速度追球中心；球停在中央时
   两块板都不动。这是**单人** pong 缺的那一半——没有它，右板永远漏球，
   玩家做什么都改变不了 5:0。**设 `false` 即回到全手动双人**（右板只由
   `pong_right_up`/`pong_right_down` 驱动，那两个键仍然有效）。
   **它做到了**：回合能来回打（实测 `pong/playjev` 一次 46 s 未结束、只丢 1 分）。
   **它没做到**：在模型只会连按 SPACE、从不操作左板的那次跑里，比赛仍在 18 s 内
   以 `RIGHT 5:0` 结束（模型自己那一侧漏球）——可玩窗口没有因此变长，这是本轮
   如实登记的未达标项，见 `recovery/reports/TASK-133-REPORT.md` §4.2。


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
| 断言不是橡皮图章 | 同一批里有 2 条**注定失败**的断言（板位置 `eq` → `scenario_assertion_failed`、屏幕文本不存在 → `assertion_failed`），另有 3 条场景断言作正对照 |
| 空转也看得见 | 球停住后 `PONG_TICK` 连续 6 次 `v=(0,0)`、位置不动；`running_game_get_node_property_samples` 的 30 帧同样不动 |

## 设计约定（每个游戏都要遵守）

1. **可观测状态必须是 Godot 属性**：`[Export]` 字段或节点属性。私有字段里的状态在 trace 上
   不可见，也就无法判定一次调用到底有没有效果（`Ball.Velocity`、`Paddle.Speed`、`WinScore` 都是 `[Export]`）。
2. **确定性优先**：新进程不要自己动起来。run-1 的缺陷 P-1 就是「驱动还没发第一条调用，游戏已经
   自己打完几分」——修复是开局把球停住、等一条显式发球。
3. **每条断言都要有反例**：同一批调用里必须有一条**注定失败**的断言。
