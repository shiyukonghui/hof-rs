
---

## D139 — TASK-091 D 段交付：**可复用 C# 游戏脚手架 + 统一试测驱动 + 第 1 个游戏 Pong**（6 条根因明确的缺陷，5 条修复 + 1 条同类复发，全部重跑对比）

**交付物**（都在 `F:\moonbit-hof-rs\godot-mcp\` 下，主仓跟踪）：

| 件 | 路径 | 说明 |
|---|---|---|
| 工程模板 | `projects\_template\` | Godot .NET 骨架（`Godot.NET.Sdk/4.8.0-dev`、`net8.0`），`NuGet.config` 清空包源只指向引擎自带的 `bin\GodotSharp\Tools\nupkgs` → **离线 `dotnet build` 成功**（`DOTNET_BUILD_EXIT=0`，输出 `.godot\mono\temp\bin\Debug\pong.dll`）；占位符 `__NAME__` / `__CLASS__` 由 `tools\new_game.ps1` 实例化 |
| 新建/重置 | `tools\new_game.ps1`、`tools\reset_game.ps1` | 前者只生成（目标已存在即拒）；后者是**唯一带删除**的工具：名字必须单段、目标必须恰好是 `<root>\projects\<name>`、先打印清单、需 `-Confirm`、**永不动 `runs\`** |
| 试测驱动 | `tools\run_game_session.ps1` | 起编辑器 9888 + 游戏 9889（`--mcp-trace` + `--mcp-capture=every_call` + `--mcp-capture-viewport=2d`）→ 重放会话（`:9888/:9889` 分相）→ 跑 `mcp_trace_ledger.py` → 跑 `game_report.py` |
| 每游戏报告 | `tools\game_report.py` | 判定分布 + `facts_complete` + **独立复算**的像素差（Pillow 重算每对 PNG，并与 trace 自己报的数逐对比对）+ 缺陷清单（每条给根因） |
| 门运行器 | `tools\run_gates.ps1` | 九道门 + `accept_m1`，每门一个 `cmd` 子进程、退出码在子进程内回显后解析 |
| 第 1 个游戏 | `projects\pong\` | C# Pong：`PongGame.cs` / `Ball.cs` / `Paddle.cs` + `scenes\main.tscn`（9 节点），**整份工程由 MCP 调用写成**（`project_create_script` / `project_edit_script` / `editor_add_nodes_batch` / `editor_set_node_script_batch` / `editor_set_node_property` / `editor_add_input_action` / `editor_save_scene` / `project_build_csharp`） |

会话与调用集：`tools\sessions\pong\session.json`（编辑器 24 条 + 游戏 29 条，C# 载荷在 `payload\`）。
四次运行的产物在 `runs\pong\pong-run{1..4}\`（trace / ledger / 截图 / `report.md` / `report.json`）。

**Pong 的「操作有效性」证据链**（全部可复算，见 `runs\pong\pong-run4\report.md`）：

* 球动了：`PONG_TICK` 球 (392,268) → (666.6,444.5)；`running_game_set_node_property` 各行的截图**独立复算**出 62 / 92 / 120 / 512 / 512 / 96 px 的像素差，且与 trace 自报的数**逐对相等**；
* 板动了：注入 `pong_left_up` ×2 再 `pong_left_down` ×1，`PONG_NUDGE y=96 → 8 → 138`（= `Speed 520 × InjectedStepSeconds 0.25`，两次都被 `MinY=8` 夹住的那次也如实反映）；
* 比分变了：`assert_node_state{ScoreRight.text == "1"} → "2"`，同刻 `PONG_SCORE scored_by=RIGHT … right=1/2`；
* 胜负判了：`WinLabel.text = "GAME OVER - RIGHT WINS 0:2"`，`PONG_OVER winner=RIGHT`，并按该**逐字字符串**断言通过；
* 断言不是橡皮图章：同一批里 3 条**注定失败**的断言（板位置 `eq`、比分、屏幕文本）在台账上都给出 `scenario_assertion_failed` / `assertion_failed`；
* 空转看得见：停球后 `PONG_TICK` 连续 6 次 `v=(0,0)` 位置不动，`running_game_get_node_property_samples` 的 30 帧同样不动。

### 缺陷清单（根因明确的才改）

| # | 层 | 现象与证据 | 根因 | 处置与重跑结果 |
|---|---|---|---|---|
| **P-1** | 游戏设计 | run-1：驱动起完端点还没发第一条调用，比赛已经自己打完 5 分（`PONG_SCORE` ×5）；`g17` 断言 `ScoreRight.text=="1"` 实得 `"3"`，`g20` 期望 `"2"` 实得 `"3"` | `_Ready` 直接发球，而驱动在端口就绪后固定等 6 s，这段无人值守的时间把比分推走了 | **改**：`_Ready` 把球停在中央且 `Velocity=Zero`，只有一条显式发球才开球（会话用注入的 `pong_serve` 发球，顺带把输入路径也走了一遍）。run-4：整个启动窗口 6 次 `PONG_TICK v=(0,0)` 比分 0-0，之后每条比分断言都成立 |
| **P-2** | 游戏逻辑 | run-1：`PONG_OVER winner=LEFT` 而同刻标签是 `GAME OVER - LEFT WINS 3:3` —— 刚得分的是 RIGHT | 胜负用 `_leftScore >= WinScore ? LEFT : RIGHT` 判，即「谁在目标之上」而不是「谁刚越线」；`WinScore` 被中途调小时两者不等价 | **改**：`Score(side)` 只看**刚得分那方**的总分是否达标。run-4：`PONG_OVER winner=RIGHT`、标签 `GAME OVER - RIGHT WINS 0:2`，且按该字符串的断言通过 |
| **P-3** | 驱动（阻塞报告） | run-1：`game_report.py` 退出 2，argparse 报 `unrecognized arguments: (cmd); Out=…; Err=…; Cmdline=…` —— 一个 PSCustomObject 被拼进了命令行 | **PowerShell 变量名大小写不敏感**：引擎句柄 `$script:game` 与参数 `$Game` 是同一个变量，启动游戏相时把 `-Game` 覆盖成了句柄对象 | **改**：句柄改名 `$script:GameProc` / `$script:EditorProc`，并加注释钉住 |
| **P-4** | 驱动生命周期 | `reset_game.ps1` 删 `projects\pong` 失败：`being used by another process`；`Get-Process` 里还留着 `godot.windows.editor.x86_64.mono.exe` | `Stop-Engine` 只杀 `cmd.exe` 的直接子进程（`.console.exe` 启动器），真正的引擎进程是孙进程 | **改**：`taskkill /PID <pid> /T /F` 杀整棵树。run-3/run-4 的重置全部成功，收尾无残留引擎进程 |
| **P-5** | 驱动（P-3 同类复发） | run-3：`report.cmd` 里是 `--game= --run-tag=pong-run3`，报告的「Saved frames」指向 `…\app_userdata\`（少了 `pong`） | P-3 只改了函数内的句柄名，**开头那两行 `$editor = $null` / `$game = $null` 没删**，`$game` 依旧把 `-Game` 清空 | **改**：删掉那两行并写明原因。run-4：`report.cmd` 是 `--game=pong`，user 目录正确 |
| **P-6** | 驱动引号 | run-3：`import: exit 1`，stderr 是 cmd 的 `The filename, directory name, or volume label syntax is incorrect.` —— 而三个路径都是对的 | `Start-Process` 把内层 `"` 转义成 `\"` 交给原生命令行，cmd 不按 PowerShell 的意思读它 | **改**：ledger / report / import 一律**生成 `.cmd` 文件再跑**（文件里没有引号游戏）。run-4：`import: exit 0`、`ledger exit 0`、`report: exit 0` |

**模块侧零缺陷**：编辑器端点在 run-1 / run-2 / run-4 的判定分布**逐项相同**
（`ok_effect_observed=3, ok_effect_unavailable=1, ok_file_effect_observed=10, ok_no_effect_observed=9`；
run-4 因 `user://pong-editor.png` 与上一轮逐字节相同而多一条 `unchanged`，见下），
游戏端的 `facts_complete` 缺口全部是引擎自己写明的 `not_tracked_deferred`（deferred / 压力 / 逐帧采样），
没有一条「丢失的证据」。**TASK-091 未改动 `modules/mcp_server` 的任何字节**，因此不需要重建引擎。

**两次独立的重跑证据**（同一批调用、同一开关、工程每次先 `reset_game.ps1` 复位）：

| 轮 | 二进制锚点 | 编辑器台账 | 游戏台账 | 关键差异 |
|---|---|---|---|---|
| run-1（修前） | 8604fcf9e | 23 调用，判定分布见上 | 28 调用；`ok_effect_observed=8` | 比分被启动窗口推走；`winner=LEFT 3:3`；报告工具退出 2 |
| run-2（P-1/P-2/P-3 修后） | 同上 | **与 run-1 逐项相同** | 29 调用；`ok_effect_observed=5, ok_file_effect_observed=10` | 比分 0:2 确定；`winner=RIGHT`；报告仍因 P-5 失败 |
| run-3（+P-4/P-6） | 同上 | 与 run-1 逐项相同 | 29 调用；`changed=6, **unchanged=4**` | 4 个截图与 run-2 **逐字节相同** → 会话可复现；报告因 P-5 空 `--game` |
| run-4（+P-5） | 同上 | `changed=9, unchanged=1` | 29 调用；`ok_effect_observed=6, ok_file_effect_observed=9` | `import/ledger/report` 全部 exit 0；`report.cmd` 里 `--game=pong` |

`unchanged` 不是「没写盘」，而是**写下去的字节与上一轮完全相同**——这本身是确定性会话的正面证据。

**九道门**（`runs\gates\task091\`，第 10 条为 `accept_m1`）：
g01 `150/150 passed / 6510 assertions`、g02 `1576/1576 passed / 3 skipped / 430823 assertions`、
g03 `TOOL-GROUPS CHECK PASS`、g04 `3/3 checks passed`（9888=154 工具、9889=73 工具、9877 守卫）、
g05 `RESULT: PASS`、g06 `TAUTOLOGY CHECK PASS`、g07 `PROBES: 10/10`、g08 `RESULT: PASS`、
g09 `ANCHOR_JUDGE RESULT PASS`（`ANCHOR_STRUCTURAL_EQUIVALENT`，二进制自报 `8604fcf9e`、HEAD `382549f63e`，
差异 2 个 `.md`、`RED_COUNT=0`）、g10 `accept_m1` **22/22**。**全部 exit 0**。

**遗留（如实）**：①Pong 只有一局、一次会话；20 个游戏的口径（D138）刚起步；
②`running_game_get_node_property_samples` 报 `scene_evidence=unavailable`，这是引擎声明的边界；
③`project_edit_script` 的 trace 行 `args_truncated=true`（9464 B），是 trace 自己的字节上限，不是丢证据；
④报告里的 `recomputed px` 用的是引擎的规则 `max(|dr|,|dg|,|db|) > 10`，与 trace 自报的数逐对相等，但「任意差异」口径会更大（TASK-090 已记录同一现象）。
