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
│   ├── mcpplay/  mcpplay8/       ←   重建期的 GDScript 试测工程（原样迁入，留档）
├── tools/                        ← 驱动与报告工具
│   ├── new_game.ps1              ←   从 _template 生成一个新游戏工程
│   ├── reset_game.ps1            ←   把一个游戏工程恢复成刚生成的状态（唯一带删除的工具）
│   ├── run_game_session.ps1      ←   ★ 统一试测驱动：起 9888/9889 + trace + 重放 + 台账 + 每游戏报告
│   ├── game_report.py            ←   每游戏报告：判定分布 + facts_complete + 独立复算像素差 + 缺陷清单
│   ├── run_gates.ps1             ←   九道门 + accept_m1，每门一个 cmd 子进程
│   └── sessions/                 ←   各游戏的调用集（JSON + payload/）
└── runs/                         ← 试测产物：trace / ledger / 截图 / 每游戏报告 / 门日志（不入库）
```

主仓 `.gitignore` 排除 `godot-mcp/godot/`（整棵）、各工程的 `.godot/` `bin/` `obj/` `.mono/`
`export_presets.cfg`，以及 `godot-mcp/runs/`。
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

---

## 5. 新游戏

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File F:\moonbit-hof-rs\godot-mcp\tools\new_game.ps1 -Name snake
```

以 `_template` 为底座生成 `projects\snake\`（Godot .NET 工程，`dotnet build` 可离线成功：
`Godot.NET.Sdk/4.8.0-dev` + `GodotSharp` 已在 NuGet 全局缓存里）。

**目标口径（D138）**：轮次不设限，**至少 20 个经典小游戏、全部 C#**，每款都要有可复算的
「操作有效性」证据 —— 像素差 / 文件 sha / 断言 / 场景树快照，不接受「应该动了」。

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
