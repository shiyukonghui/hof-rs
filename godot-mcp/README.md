# godot-mcp — Godot .NET 引擎克隆 + 经典小游戏试测台

> 本目录由 **TASK-091** 建立：把重建期的 `H:\rebuild` 迁入正式项目根，并把「用 MCP 工具驱动
> Godot 开发游戏」这件事变成**可复用、可溯源**的流水线。
> 决策依据见仓库根 `DECISIONS.md` 的 **D136（事故与恢复）/ D137（迁移与嵌套 git）/ D138（新目标口径）**。

---

## 1. 布局

```
godot-mcp/
├── godot/                        ← 【独立 git 仓库】Godot 4.8-dev fork 克隆（含内核 MCP 模块）
│   ├── .git/                     ←   自己的历史、自己的 remote，主仓不跟踪
│   ├── modules/mcp_server/       ←   MCP 模块本体：C++ / 文档 / 脚本 / 测试
│   ├── bin/                      ←   构建产物（4 个编辑器变体，约 390 MB）
│   └── ...                       ←   21,793 文件 / 约 4.7 GB
├── projects/                     ← 游戏工程（每个子目录一个 Godot 工程）
│   ├── _template/                ←   可复用的 C# 游戏工程模板（dotnet build 可离线成功）
│   ├── pong/                     ←   第 1 个游戏：C# 版 Pong
│   ├── breakout/                 ←   第 2 个游戏：C# 版 Breakout
│   ├── snake/                    ←   第 3 个游戏：C# 版 Snake
│   └── mcpplay/  mcpplay8/       ←   重建期的 GDScript 试测工程（原样迁入，留档）
├── GAME-LOOP-LOG.md              ←   ★ 跨轮进度台账：每个游戏一行（调用数 / facts / 判定 / 缺陷 / 证据路径）
├── tools/                        ← 驱动与报告工具
│   ├── new_game.ps1              ←   从 _template 生成一个新游戏工程
│   ├── reset_game.ps1            ←   把一个游戏工程恢复成刚生成的状态（唯一带删除的工具）
│   ├── run_game_session.ps1      ←   ★ 统一试测驱动：起 9888/9889 + trace + 重放 + 台账 + 每游戏报告
│   ├── game_report.py            ←   每游戏报告：判定分布 + facts_complete + 独立复算像素差 + 缺陷清单
│   ├── run_gates.ps1             ←   九道门 + accept_m1，每门一个 cmd 子进程
│   └── sessions/                 ←   各游戏的调用集（JSON + payload/）
├── runs/                         ← 试测产物：trace / ledger / 截图 / 每游戏报告 / 门日志（不入库）
└── recovery/                     ← 恢复档案：TASK-078..092 的报告 / 脚本 / 实测产物（见 §8）
```

主仓 `.gitignore` 排除 `godot-mcp/godot/`（整棵）、各工程的 `.godot/` `bin/` `obj/` `.mono/`
`export_presets.cfg`、`godot-mcp/runs/`，以及 `recovery/` 里体量大/可再生的那几块（§8 有清单与
分界线）。
**`*.import` 故意不忽略** —— 它是 Godot 的资源 UID 映射，属于工程源码。

---

## 2. 两个仓库的关系

| | 主仓 `F:\moonbit-hof-rs` | 引擎仓 `godot-mcp\godot` |
|---|---|---|
| 跟踪内容 | 模板、游戏 C# 源码、驱动脚本、文档、`DECISIONS.md` | 引擎全树 + MCP 模块 |
| 远程 | 无（本项目内部提交） | `git@github.com:shiyukonghui/godot.git` |
| 分支 | `master` | `feature/mcp-server-module-rebuild` |
| **里程碑纪律** | 每段可提交改动即提交 | **每个里程碑必须 `git push`** |

**为什么引擎仓保持独立、不做 submodule**：它是 4.7 GB / 2.18 万文件的上游 fork 全历史；内核补丁本身是
**引擎的**交付物，应由引擎仓自己的分支承担。主仓只需要「知道它在哪、怎么构建」。
（详见 D137 §嵌套 git 处理。）

> 血的教训（D136）：本地提交 **不等于** 已保存。事故中 `feature/mcp-server-module` 的全部本地提交
> 因为「禁止 push」的旧纪律而永久丢失。**此后每个里程碑都 push。**

---

## 3. 构建（必须从 cmd 启动，铁律 3）

```cmd
:: 两个变体共用 bin\obj，必须串行；-j8 按机器调整
cd /d F:\moonbit-hof-rs\godot-mcp\godot
D:\Anaconda\Scripts\scons.exe platform=windows target=editor module_mono_enabled=yes tests=yes -j8 -k
D:\Anaconda\Scripts\scons.exe platform=windows target=editor module_mono_enabled=no  tests=yes -j8 -k
```

产物（`bin\`）：

| 变体 | 可执行文件 | 用途 |
|---|---|---|
| mono（.NET） | `godot.windows.editor.x86_64.mono.console.exe` | **C# 游戏**、MCP 端点、九门里的 doctest |
| 非 mono | `godot.windows.editor.x86_64.console.exe` | `accept_m1.ps1` 写死跑的就是它 |

> **改了契约描述就要把两个变体都重建** —— `accept_m1` 的 `case12` 会逐字比对 `tools/list` 与
> `modules/mcp_server/docs/tools_list.renamed.json`，只重建一个变体会得到 21/22（TASK-090 §5.2/§5.3）。

---

## 4. 怎么跑试测

### 4.1 手动起一对端点

```cmd
:: 编辑器端 9888
bin\godot.windows.editor.x86_64.mono.console.exe -e --path <工程目录> ^
  --mcp-port=9888 --mcp-trace=<trace-editor.jsonl> --mcp-capture=every_call ^
  --mcp-capture-dir=<shots目录> --mcp-capture-viewport=2d

:: 游戏端 9889
bin\godot.windows.editor.x86_64.mono.console.exe --path <工程目录> ^
  --mcp-port=9889 --mcp-trace=<trace-game.jsonl> --mcp-capture=every_call ^
  --mcp-capture-dir=<shots目录> --mcp-capture-viewport=2d
```

调用走 HTTP JSON-RPC：`POST http://127.0.0.1:<port>/mcp`。

### 4.2 统一驱动（推荐）

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File F:\moonbit-hof-rs\godot-mcp\tools\run_game_session.ps1 `
  -Game pong -Session F:\moonbit-hof-rs\godot-mcp\tools\sessions\pong.json
```

它做四件事：① 起 9888/9889（带全部 `--mcp-*` 开关）；② 重放会话里的调用；③ 跑
`modules\mcp_server\scripts\mcp_trace_ledger.py`；④ 产出**每游戏报告**
（判定分布 + `facts_complete` + 缺陷清单）。

### 4.3 台账

```cmd
python modules\mcp_server\scripts\mcp_trace_ledger.py <trace.jsonl> ^
  --text <ledger.txt> --json <ledger.json>
```

**字段与判定规则的可信来源是引擎仓里的 `modules\mcp_server\docs\reports\MCP-TRACEABILITY.md`**，
不是本 README。TASK-092 之后它多了三件事要读：

* **被裁掉的参数不再无据可查**：超限载荷整份写进 `<trace 名>.sidecar/`，行上给相对/绝对路径 +
  真实字节数 + sha256，台账**重新算一遍**并据此判 `args_complete` 与 `args_evidence`
  （`inline_complete` / `sidecar_verified` / `sidecar_missing` / `sidecar_mismatch` /
  `truncated_no_sidecar` / `sidecar_not_recorded_in_trace`）——见该文档 §2.6 / §3.1；
* **延迟调用的文件侧与画面侧证据都在完成时刻采集**：文件副作用跨延迟窗口累计（`Queue::tick`），
  截图 `before` 在请求帧、`after` 在完成帧之后；只有「一帧都没被观测」才写 `not_tracked_deferred`
  ——见 §2.7；
* **`timeout_ms` 由稳定的帧代价估计造出**（最近 15 帧中位数，截断并夹在 [16, 1000] ms），
  所以两条相同场景的 `timeout_ms` 不同只说明取值时刻不同——见 §6。

---

## 5. 新游戏

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File F:\moonbit-hof-rs\godot-mcp\tools\new_game.ps1 -Name snake
```

以 `_template` 为底座生成 `projects\snake\`（Godot .NET 工程，`dotnet build` 可离线成功：
`Godot.NET.Sdk/4.8.0-dev` + `GodotSharp` 已在 NuGet 全局缓存里）。

**目标口径（D138）**：轮次不设限，**至少 20 个经典小游戏、全部 C#**，每款都要有可复算的
「操作有效性」证据 —— 像素差 / 文件 sha / 断言 / 场景树快照，不接受「应该动了」。
**跨轮进度与缺陷登记看 `GAME-LOOP-LOG.md`**（每个游戏一行；工具缺陷与游戏/驱动缺陷分栏）。

---

## 5.1 已知环境缺陷（TASK-093 记录，未修）

**D-1：视口回读陈旧** —— 引擎进程的 `--mcp-capture=every_call` 截图与
`running_game_capture_screenshot` / `running_game_capture_frames` 都返回**同一帧**：
同一轮里 `shots-editor\` / `shots-game\` 的每个 PNG 逐字节相同（实测 42/68、40/62 个各 1 个 sha），
`user://` 跨越 8 秒的两次截图同 sha。**游戏逻辑本身在动**（逐帧采样的 `position` 与
`execute_gdscript` 都给出变化，`frames_waited` 单调递增），所以这是**画面侧证据链**的问题，
不是游戏的问题；同一批代码在 TASK-092 的 Pong 会话里 10/29 组像素差非零、今天仍能复算出来。

> **TASK-094 的更新（先读这一段再读上面）**：D-1 已定位于**这台机器的画面管线**，不是
> `modules\mcp_server`，本模块也改不动它。最小反例：把 `Background.color` 依次设成蓝→红→绿
> （同一调用内读回确认真的变绿），三次截图得到**三张逐字节相同、且都还是最初深色背景**的 PNG；
> `--mcp-capture=off` 同样复现。同一刻蛇的 `SnakeSeg00.position` 从 `(144,240)` 走到 `(384,240)`；
> 渲染器自己在动（加 100 个 `ColorRect` 后 `RENDER_TOTAL_OBJECTS_IN_FRAME` 57 → 157，
> `get_frames_drawn()` 以 ≈144/s 递增）；窗口未最小化；vulkan / opengl3 / d3d12 三者同样冻结；
> `force_draw` 无效。**A/B 是关键**：同一份二进制字节、同一个 `tools\sessions\pong\session.json`，
> 00:14:47 得 10/29 非零、02:00 重放得 0/29。
> 另外，原复现脚本 `diag_render.ps1` 拍的是**已经撞墙死掉的蛇**（1.5 秒就 `ticks=19`），
> 那条脚本里的「两张同 sha」本来就该出现 —— 新反例不依赖对象是否存活。
> 复现：`powershell -File recovery\work\task094\diag_freshness.ps1 -Game snake -Capture off -Port 9891`
> → `D1_VERDICT=PRESENT`。进程外窗口抓取（`CopyFromScreen` / `PrintWindow`）在本会话**不可信**
> （两个不同引擎给出同一份抓取字节）。

**D-2：`accept_m1.ps1` 的主循环就绪判据曾经对负载敏感（TASK-094 已修）** —— `task093` /
`task093b` 两轮里它是 `5/22`，头部写着 `WARNING: the pump never looked steady`。原判据要求
「相隔 1000 ms 的两次采样之间 `frame_count` 至少 +20，连续 3 次」，也就是**至少 20 fps**：这是
吞吐要求，不是就绪要求，有负载时主循环活着但更慢，判据永远不成立，于是用例在尚未稳定的泵上跑。
现在判据是「`frame_count` 连续 6 次严格递增，采样间隔 250 ms」（≈1.5 秒不间断推进，与帧率无关），
死线仍 180 s。实测：**单独跑 wall=50.8s → `22/22`、`GATE_EXIT=0`**；
**同机 8 个 CPU 烧机进程（16 逻辑核）并跑 wall=55.3s → `22/22`、`GATE_EXIT=0`**。
三轮里 `case12/13/14` 与 `guard_user_port_9877` **都 PASS**（含 `case14` 期望的
`bind failed ... error=22`），绑定与端口逻辑本身一直正常。
**读法：不再需要「跑 `accept_m1` 时不要并行跑会话或构建」这条规矩。**

---

## 6. 九道门

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File F:\moonbit-hof-rs\godot-mcp\tools\run_gates.ps1 -Tag task091
```

每道门一个 `cmd.exe` 子进程、各自的 stdout/stderr，退出码在子进程内部回显后解析
（PowerShell 5.1 对重定向子进程的 `ExitCode` 时好时坏）。日志落在 `runs\gates\<tag>\`。
第 10 条是 `accept_m1.ps1`（22 个 case），它不是「门」但每次都跟着跑。

**改了 `modules/mcp_server` 就要重建两个变体再跑门**（见 §3）。

---

## 7. 铁律（每题任务书都照抄）

1. **禁止一切 shell 重定向**：输出用 `Start-Process -RedirectStandardOutput <绝对路径>` 或 `-OutFile`。
2. **破坏性命令默认拒绝**：非空 / 绝对 / 白名单前缀 / 先打印清单；含通配符或 `..` → `throw`。
   迁移走「先复制 → 逐文件 sha 校验 → 才删源」。
3. **构建与运行从 cmd 启动。**
4. 主仓**不得**把 4.7 GB 的引擎树纳入跟踪。
5. **每个里程碑 push。**

---

## 8. `recovery/` —— 恢复档案（TASK-092 迁入）

`recovery/` 是**重建期（TASK-078..091）的全部档案**：事故（D136）之后从 178 份会话记录里把
MCP 模块重建回来的那批文档、脚本、实测产物与原始料。TASK-092 把它从
`C:\Users\wyl\AppData\Local\Temp\mcp-recovery\` 迁进本项目 —— **先 robocopy 复制、再逐文件
SHA-256 校验（两侧文件数与字节数相等、`mismatched=0`）、校验全过才删源**（铁律 2）。
拷贝脚本、校验脚本与两侧清单留在 `recovery/work/task092/`。

```
recovery/
├── reports/        ← RECOVERY-PLAN / STATE-OF-RECOVERY、TASK-078..092 报告、
│                      EXTRACTION-MANIFEST / REPORT、REBUILD-2A/2B 报告与 manifest（23 个 .md）
├── logs/           ← 重建期的原始日志（436 文件 / 2.4 MB）        【不入库：原始料】
├── work/           ← 逐任务的脚本与**关键实测产物**（trace / ledger / PNG / 分析输出）
│   ├── task078 .. task091、gitapply-probe、patchdry…（脚本 + 证据）
│   ├── events-*.jsonl（106 MB 会话事件 dump）                    【不入库：transcripts 的中间物】
│   └── task092/    ← TASK-092 自己的迁移脚本、校验输出与门日志
├── staging/        ← 重建暂存（10,861 文件 / 344 MB）             【不入库：暂存】
├── transcripts/    ← 178 份会话记录（566 MB）                     【不入库：转录】
├── rebuild/        ← 重建期的引擎补丁 / patch manifest / 低置信清单 / 旧副本
│   ├── patches、work2b、_low-confidence、_refs、_excluded、ENGINE-PATCHES-TO-REAPPLY.md
│   └── godot/      ← 重建期的**引擎树旧副本**（19,238 文件 / 1.18 GB）【不入库：引擎树，铁律 4】
├── backup/         ← 重建前的引擎二进制备份（193 MB）              【不入库：大二进制】
├── scripts/        ← 重建期的抽取 / 校验 / manifest 生成脚本（36 个）
└── tmp/            ← 重建期的临时目录                              【不入库：临时】
```

**忽略策略与它的分界线**（`.gitignore` 的 `TASK-092` 段）：入库的是**小而不可再生的判定依据**
（各 TASK 报告、RECOVERY-PLAN、STATE-OF-RECOVERY、EXTRACTION/REBUILD manifest、`work/` 下的脚本
与实测产物、`rebuild/` 的补丁与清单），入库量 **≈2,456 文件 / 75.9 MB**（其中最大单个是
`rebuild/work2b/gen-hits.txt` 的 21.06 MB 文本证据）；忽略的是**大块原始料与可再生的大二进制**
（transcripts / staging / logs / tmp / backup / `rebuild/godot` / `events-*.jsonl` 等，
26 个忽略入口 / ≈31,020 文件 / ≈2.33 GB）。**忽略不等于丢失**：它们在盘上原样保留，只是不进 git 历史。

> 为什么 `recovery/rebuild/godot/` 也忽略：它是重建期的引擎树旧副本，与 `godot-mcp/godot/`
> 同性质 —— 铁律 4 说的是「引擎树不入主仓」，与它是不是旧版本无关。

---
