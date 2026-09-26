# TASK-091 — 迁移入仓 + 嵌套 git 处理 + 决策欠账 + C# 游戏脚手架与第 1 个游戏 Pong

* 执行者：迁移/游戏工程师（本会话，**有写权限，未再委派**）
* 主仓：`F:\moonbit-hof-rs`（分支 `master`，**无远程**，提交 = 本仓内部）
* 引擎仓：`F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`，
  remote `git@github.com:shiyukonghui/godot.git`）
* Scratch / 脚本 / 日志：`C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task091\`
* 时间：2026-09-26

---

## 0. 逐条结论

| 段 | 要求 | 结论 |
|---|---|---|
| **A** | 引擎树与试测工程迁入 `godot-mcp\`，先复制→逐文件 sha→才删源 | **达成**。4.708 GB / 21,793 文件，`mismatched=0`；`H:\rebuild` 已清空 |
| **A③** | `HEAD == 382549f63e == origin`、`fsck` 同结论、`status` 空、抽查 sha | **达成**（下表） |
| **B** | 引擎保留自己的 `.git`；主仓忽略；README；提交 | **达成**。主仓 `git status --short` **空** |
| **C** | `DECISIONS.md` 追加 D136 / D137 / D138 | **达成**（另追加了 D139，见 D 段） |
| **D①** | 可复用 C# 工程模板（离线 `dotnet build`）+ 试测驱动脚本 | **达成**。`DOTNET_BUILD_EXIT=0`；离线包源只有引擎自带的 nupkgs |
| **D②** | Pong 用 C# 实现，全程 MCP 工具驱动开发 | **达成**。整份工程由 MCP 调用写成（脚本 / 节点 / 属性 / 构建 / 运行 / 输入 / 断言 / 截图） |
| **D③** | 像素差证明球与板真的动了、断言证明比分变化、台账逐次判定 | **达成**（§D3） |
| **D④** | 缺陷清单 + 修复 + 重跑对比 | **达成**。6 条根因明确的缺陷，4 轮运行逐项对比（§D4） |
| **E** | 九道门全绿（真实输出）、提交与 push、报告 | **达成**。10/10 条 **exit 0** |

---

## A. 迁移（先复制 → 逐文件校验 → 才删源）

| 源 | 目标 |
|---|---|
| `H:\rebuild\godot` | `F:\moonbit-hof-rs\godot-mcp\godot` |
| `H:\rebuild\projects` | `F:\moonbit-hof-rs\godot-mcp\projects` |

**复制**：`robocopy /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /MT:8`（从 **cmd** 启动，
输出用 `Start-Process -RedirectStandardOutput` 收集 —— 铁律 1 与 3）：

```
引擎：  Dirs 2322/2322   Files 21793/21793   Bytes 4.708 g   FAILED 0   Mismatch 0
工程：  Files 303/303    Bytes 6,029,718     FAILED 0
```

**校验**：`verify_tree.ps1` 逐文件 SHA-256。树上最长路径 277（源）/ 294（目标）字符，
`>260` 的源 13 个、目标 80 个 —— `Get-ChildItem` 递归会静默漏掉，所以改用
`Directory::EnumerateFiles` + `\\?\` 长路径前缀 + .NET 直读：

```
### VERIFY godot
src_files=21793 dst_files=21793 missing_in_dst=0 extra_in_dst=0
compared=21793  mismatched=0
src_total_bytes=5055873699  dst_total_bytes=5055873699
VERIFY_godot=PASS
### VERIFY projects
src_files=303 dst_files=303 missing_in_dst=0 extra_in_dst=0  mismatched=0
6,029,718 == 6,029,718   VERIFY_projects=PASS
```

**删除源**：`safe_remove.ps1` —— 白名单前缀 `H:\rebuild`、先打印清单
（`FILES 21793 / BYTES 5055873699`，**与校验值一致**）、无通配符、`-LiteralPath`、
必须 `-Confirm`。`H:\rebuild` 现为空。

### A③ 迁移后的校验

| 项 | 结果 |
|---|---|
| `git rev-parse HEAD` | `382549f63ead3d511c429b3e213d6ecb74986208` |
| 分支 / origin | `feature/mcp-server-module-rebuild`；`refs/remotes/origin/...` **同一 sha** |
| `git status --short` | **空（0 行）** |
| `git fsck --no-progress` | 源与目标两侧 **exit 0**，stdout 与 stderr **逐字节全等**（都是 0 字节，sha `E3B0C442…`） |
| `modules\mcp_server\docs\tools_list.renamed.json` | 148,141 B / `4BE4285CD221A877712370E6A4C73426E0CC7B94C2B6E32D59B3AED69760ED3A`，迁移前后一致 |
| `bin\*.exe` 四变体 | 300,544 / 193,465,344 / 300,544 / 194,050,560 B，sha **逐个相同**（`ED2C3F9C…` / `2542CE1D…` / `6B510923…` / `DDAD7FF8…`） |

---

## B. git 处理（两个仓库的关系）

1. **引擎树保留自己的 `.git`**（独立克隆，**不并入主仓、不做 submodule**）。它是 4.7 GB /
   2.18 万文件的上游 fork 全历史；内核补丁本来就是**引擎的**交付物，应由引擎仓自己的分支承担。
2. **主仓 `.gitignore`** 新增：
   `godot-mcp/godot/`（整棵）、`godot-mcp/projects/*/{.godot,bin,obj,.mono}/`、
   `godot-mcp/projects/*/export_presets.cfg`、`godot-mcp/runs/`。
   **`*.import` 故意不忽略** —— 它是 Godot 的资源 UID 映射，属于工程源码（任务书说「视情况」，这里是「不忽略」）。
   TASK-085/086 的重定向残留 `$null` / `$l` / `%DST%/` **留档不删**（铁律 2），点名忽略。
3. **`godot-mcp/README.md`**：布局、两个仓库的关系（引擎仓以 fork 分支为准、**每个里程碑 push**）、
   构建（两个变体、为什么改了契约就要都重建）、手动与统一驱动的试测方式、九道门、铁律。
4. **主仓提交**：§E 的 `git log`。

---

## C. 决策记录

`F:\moonbit-hof-rs\DECISIONS.md` 追加：

* **D136** 事故与恢复：cmd 下 `*>` 被当字面参数污染脚本参数（PowerShell `-File` 按位置绑定）+
  脚本未校验目标根即 `Remove-Item -Recurse -Force` → 引擎工作树被清空；四次反删除
  （第三方工具、`winfr /regular`、`/extensive` ×2）只救回 MFT 驻留小文件（<1 KB 内容可用、≥1 KB 全 0），
  关键文件与 `.git` 对象库不可用；最终以 `57277407` 基线 + 178 份会话记录重放重建；
  **三条防复发纪律**（禁止一切 shell 重定向 / 破坏性命令默认拒绝 / 每个里程碑 push）。
* **D137** 迁移与嵌套 git 处理：A/B 两节的实际做法与全部校验数字。
* **D138** 新目标口径：轮次不设限、**至少 20 个经典小游戏、全部 C#**，以「可完整溯源操作有效性」为改进基础。
* （追加）**D139** D 段交付：脚手架、驱动、Pong、6 条缺陷与四轮重跑对比、九道门真实输出。

文件从 537,251 B → 555,321 B。

---

## D. C# 游戏脚手架 + 第 1 个游戏 Pong

### D1 可复用模板 `godot-mcp\projects\_template\`

`Godot.NET.Sdk/4.8.0-dev` + `net8.0`，`NuGet.config` **清空包源**、只指向引擎克隆自带的
`..\..\godot\bin\GodotSharp\Tools\nupkgs`，所以完全离线：

```
--- effective package sources ---
  1.  godot-local [已启用]
      F:\moonbit-hof-rs\godot-mcp\godot\bin\GodotSharp\Tools\nupkgs
--- build ---
  pong -> F:\moonbit-hof-rs\godot-mcp\projects\pong\.godot\mono\temp\bin\Debug\pong.dll
    0 个警告  0 个错误
DOTNET_BUILD_EXIT=0
运行库输出：pong.dll / pong.pdb / pong.deps.json / pong.runtimeconfig.json / GodotSharp.dll / GodotSharpEditor.dll
```

占位符 `__NAME__` / `__CLASS__` 由 `tools\new_game.ps1` 实例化（**smoke test 通过**：
`snake` → `SnakeGame`，`placeholder files left: 0`，README 由 `_template\README.game.md` 生成）。
`tools\reset_game.ps1` 把某个工程复位（唯一带删除的工具：单段名字 / 目标必须恰好是
`<root>\projects\<name>` / 先打印清单 / 需 `-Confirm` / **永不动 `runs\` 里的证据**）。

### D2 统一试测驱动 `tools\run_game_session.ps1` + `tools\game_report.py`

* 起**编辑器 9888**（`-e --path`）与**游戏 9889**（`--path`），两者都带
  `--mcp-trace=<jsonl>`、`--mcp-capture=every_call`、`--mcp-capture-dir=<dir>`、`--mcp-capture-viewport=2d`；
* 重放 `tools\sessions\<game>\session.json`（编辑器相 → 关掉 → 游戏相），
  调用体可内联 `content` 或引用 `content_file`；
* 跑 `modules\mcp_server\scripts\mcp_trace_ledger.py`（文本 + JSON）；
* 跑 `game_report.py` → `runs\<game>\<run-tag>\report.md` + `report.json`：
  **判定分布 + `facts_complete` + 独立复算的像素差 + 带根因的缺陷清单**；
* 铁律：引擎一律经 cmd 启动；所有删除都先过 `Assert-InOutRoot`（只允许 `runs\<game>\<run-tag>` 之内）。

### D3 Pong（`godot-mcp\projects\pong\`）与「操作有效性」证据

工程**整份由 MCP 调用写成**（`godot-mcp\tools\sessions\pong\session.json`，编辑器 24 条 + 游戏 29 条）：
`project_create_script`(×2) / `project_edit_script` / `project_build_csharp` / `project_validate_scripts`(×2) /
`editor_open_scene` / `editor_add_nodes_batch`(8 节点) / `editor_set_node_script_batch`(×2) /
`editor_set_node_property`(×3) / `editor_add_input_action`(×5) / `editor_save_scene` /
`editor_get_scene_tree` / `editor_get_node_properties` / `editor_capture_screenshot` / `editor_get_errors`。

| 主张 | 证据（`runs\pong\pong-run4\`） |
|---|---|
| **球真的动了** | `PONG_TICK` 球 (392,268) → (482.1,325.9) → (666.6,444.5)；同批 `running_game_set_node_property` / `capture_screenshot` 各行的截图**独立复算**出 **62 / 92 / 120 / 512 / 512 / 96 px** 像素差，且与 trace 自报的数**逐对相等** |
| **板真的动了** | 注入 `pong_left_up` ×2 再 `pong_left_down` ×1：`PONG_NUDGE y=96 → 8 → 138`（= `Speed 520 × InjectedStepSeconds 0.25`；被 `MinY=8` 夹住的那次也如实反映） |
| **比分真的变了** | `assert_node_state{ScoreRight.text == "1"}` → `"2"`，同刻 `PONG_SCORE scored_by=RIGHT … right=1 / right=2` |
| **胜负真的判了** | `WinLabel.text == "GAME OVER - RIGHT WINS 0:2"`（**逐字断言**通过），同刻 `PONG_OVER winner=RIGHT` |
| **断言不是橡皮图章** | 同一批里 **2 条注定失败**的断言都被台账抓住：`seq=12` 板位置 `eq` → `scenario_assertion_failed`、`seq=27` 屏幕文本不存在 → `assertion_failed`（另有 `seq=11/13/6` 三条场景断言 `scenario_passed` 作正对照） |
| **空转看得见** | 停球后 `PONG_TICK` 连续 6 次 `v=(0,0)` 比分 0-0；`running_game_get_node_property_samples` 的 30 帧同样不动 |
| **画面真的变了** | `user://` 四帧按同名同尺寸逐帧复算：`t0→t1 = 512 px`、`t1→t2 = 512 px`、`t2→final = 7191 px` |

台账（run-4）：

```
编辑器  calls=23  facts_complete 21/23
  verdicts: ok_effect_observed=3, ok_effect_unavailable=1, ok_file_effect_observed=9, ok_no_effect_observed=10
游戏    calls=29  facts_complete 23/29
  verdicts: ok_effect_observed=6, ok_effect_unavailable=6, ok_file_effect_observed=9, ok_no_effect_observed=8
```

不完整的 6 条事实全部是引擎自己写明的**声明边界**（`not_tracked_deferred`：deferred 场景、
压力测试、逐帧采样；`project_edit_script` 的 `args_truncated=true` 是 trace 自己的字节上限），
**没有一条是丢失的证据**。

### D4 缺陷清单 + 修复 + 重跑对比

| # | 层 | 现象（证据） | 根因 | 处置 → 重跑结果 |
|---|---|---|---|---|
| **P-1** | 游戏设计 | run-1：驱动还没发第一条调用，比赛已自己打完 5 分（`PONG_SCORE` ×5）；`g17` 断言 `"1"` 实得 `"3"`，`g20` 期望 `"2"` 实得 `"3"` | `_Ready` 直接发球，而驱动在端口就绪后固定等 6 s，这段无人值守时间把比分推走了 | **改**：开局把球停在中央 `Velocity=Zero`，只有显式发球才开球（会话用注入的 `pong_serve`，顺带走了输入路径）。run-4：启动窗口 6 次 `v=(0,0)`、`0-0`，之后每条比分断言都成立 |
| **P-2** | 游戏逻辑 | run-1：`PONG_OVER winner=LEFT` 而同刻标签是 `GAME OVER - LEFT WINS 3:3` —— 刚得分的是 RIGHT | 胜负用 `_leftScore >= WinScore ? LEFT : RIGHT`，即「谁在目标之上」而非「谁刚越线」 | **改**：只看**刚得分那方**。run-4：`winner=RIGHT`、`GAME OVER - RIGHT WINS 0:2` |
| **P-3** | 驱动（阻塞报告） | run-1：`game_report.py` 退出 2，argparse 报 `unrecognized arguments: (cmd); Out=…; Cmdline=…` | **PowerShell 变量名大小写不敏感**：句柄 `$script:game` 与参数 `$Game` 是同一变量，启动游戏相时把 `-Game` 覆盖成句柄对象 | **改**：句柄改名 `$script:GameProc` / `$script:EditorProc` 并加注释 |
| **P-4** | 驱动生命周期 | `reset_game.ps1` 删 `projects\pong` 报 `being used by another process`；`Get-Process` 里还留着引擎 | `Stop-Engine` 只杀 `cmd` 的直接子进程（`.console.exe` 启动器），真正引擎是孙进程 | **改**：`taskkill /PID … /T /F`。run-3/4 的重置全部成功，收尾无残留引擎 |
| **P-5** | 驱动（P-3 同类复发） | run-3：`report.cmd` 是 `--game= --run-tag=…`，报告的 Saved frames 指向 `…\app_userdata\`（少了 `pong`） | P-3 只改了函数内句柄名，**开头 `$editor = $null` / `$game = $null` 没删** | **改**：删掉那两行并写明原因。run-4：`--game=pong`，user 目录正确 |
| **P-6** | 驱动引号 | run-3：`import: exit 1`，cmd 报 `The filename, directory name, or volume label syntax is incorrect.`（三个路径都对） | `Start-Process` 把内层 `"` 转义为 `\"` 交给原生命令行，cmd 不按 PowerShell 的意思读 | **改**：ledger / report / import 一律**先生成 `.cmd` 文件再跑**。run-4：`import exit 0`、`ledger exit 0`、`report exit 0` |

**四轮重跑对比**（同一批调用、同一开关；每轮前先 `reset_game.ps1` 复位工程）：

| 轮 | 编辑器台账 | 游戏台账 | 关键差异 |
|---|---|---|---|
| run-1（修前） | 23 调用；`ok_effect=3, ok_unavail=1, ok_file=10, ok_no_effect=9`；`changed=10/unchanged=0` | 28 调用；`ok_effect=8, ok_unavail=5, ok_file=10, ok_no_effect=5` | 比分被启动窗口推走；`winner=LEFT 3:3`；报告工具 exit 2 |
| run-2（P-1/2/3） | **与 run-1 逐项相同** | 29 调用；`ok_effect=5, ok_unavail=6, ok_file=10, ok_no_effect=8` | 比分 0:2 确定；`winner=RIGHT`；报告仍空 `--game`（P-5） |
| run-3（+P-4/6） | 与 run-1 逐项相同 | 29 调用；`changed=6, **unchanged=4**` | 4 个截图与 run-2 **逐字节相同** → 会话可复现；`import` 已修好 |
| **run-4（+P-5）** | `changed=9, unchanged=1` | 29 调用；`ok_effect=6, ok_unavail=6, ok_file=9, ok_no_effect=8`；`changed=9, unchanged=1` | `import/ledger/report` **全部 exit 0**；`report.cmd` 里 `--game=pong` |

**编辑器端 run-1 / run-2 / run-3 的判定分布逐项相同**（run-4 只多一条 `unchanged`：`user://pong-editor.png`
与上一轮逐字节相同）——这说明这一批修复**没有改变模块行为**。
`unchanged` 不是「没写盘」，而是**写下去的字节与上一轮完全相同**，本身就是确定性会话的正面证据。

**模块侧零缺陷**：本任务**未改动 `modules/mcp_server` 的任何字节**，因此无需重建引擎。

---

## E. 收尾

### 九道门（`godot-mcp\runs\gates\task091\`，真实输出）

| # | gate | 结论 |
|---|---|---|
| 1 | 模块 doctest `--test-case=[MCPServer]*` | **exit 0** — `150/150 passed`、`6510/6510 assertions`、`SUCCESS!` |
| 2 | 全量 doctest `--headless --test` | **exit 0** — `1576/1576 passed / 3 skipped`、`430823/430823 assertions`、`SUCCESS!` |
| 3 | 组清单 | **exit 0** — `TOOL-GROUPS CHECK PASS`（`41 == 42 - 1: PASS`） |
| 4 | 契约子集（活链） | **exit 0** — `3/3 checks passed`（编辑器 9888、游戏 9889、`guard_user_port_9877`） |
| 5 | 改名映射 | **exit 0** — `RESULT: PASS`（`177 == 174 - 2 - 1 + 6`） |
| 6 | 同义反复 | **exit 0** — `TAUTOLOGY CHECK PASS`（scanned 2 root(s)） |
| 7 | 退出码传播 | **exit 0** — `PROBES: 10/10` |
| 8 | 硬编码计数 | **exit 0** — `RESULT: PASS`（无 UNCLASSIFIED） |
| 9 | 引擎锚点 | **exit 0** — `ANCHOR_JUDGE RESULT PASS`；`verdict=ANCHOR_STRUCTURAL_EQUIVALENT`，`anchor=8604fcf9e`、`head=382549f63`、`diff_count=2 safe_count=2 red_count=0`（2 个 `.md`） |
| + | `accept_m1` | **exit 0** — **`22/22 cases passed`** |

### 提交与 push

主仓 `F:\moonbit-hof-rs`（4 次提交；本仓无远程，提交即落到本项目）：

```
f523904 docs(godot-mcp): 更正 Pong 缺陷记录里的一个数字 —— run-4 里「注定失败的断言」是 2 条不是 3 条
9f87061 docs(decisions): D139 TASK-091 D 段交付 —— 脚手架 + 试测驱动 + Pong + 6 条缺陷的重跑对比
df02ccb feat(godot-mcp): 可复用 C# 游戏模板 + 统一试测驱动 + 第 1 个游戏 Pong
355eefc chore(godot-mcp): 迁移入主仓 + 嵌套 git 忽略策略 + D136/D137/D138
fef32a3 docs(decisions): D135 **独立验收 fail** —— ...
96249df docs(decisions): D134 TASK-075 交付 ...
6f0e1ea docs(decisions): D133 **试测第 5 轮** ...
36cf1ea docs(decisions): D132 TASK-073 交付 ...
```

> 第 4 次提交是一次**自我更正**：初稿把 run-1（P-1 未修时）两条**偶然失败**的比分断言
> 算进了「刻意构造的失败断言」。run-4 里刻意构造的失败断言只有 2 条。记录留着更正本身，
> 不重写历史。

主仓 `git status --short`：**空**（干净）。被忽略的三类东西：引擎树、各工程构建产物、
`runs\`，以及 TASK-085/086 的重定向残留 `$null` / `$l` / `%DST%/`（留档不删）。

引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（本任务未改动，故无新提交）：

```
382549f63e modules/mcp_server: task090 (2c-9) step6 - the round-8 record: the traceability section and the gate ledger
8604fcf9e2 modules/mcp_server: task090 (2c-9) step5 - the description change is declared in the generator, so the contract stays reproducible
eee58538a1 modules/mcp_server: task090 (2c-9) step4 - a deferred call's own body reaches its trace line too
cac01b5f9f modules/mcp_server: task090 (2c-9) step3 - the round-8 fixes: the InputMap fact, the scenario flags, the frame-based deadline
a455a87bea modules/mcp_server: task090 (2c-9) step2 - D-3: the game executor reaches the running scene tree
4b8625bedc modules/mcp_server: task090 (2c-9) step1 - the failure answer's data payload reaches the call line
b8e0142b81 modules/mcp_server: task089 (2c-8) step3 - the gate ledger (9/9 + 22/22) and the iron-rule record
80035ed115 modules/mcp_server: task089 (2c-8) step2 - the round-7 test loop: three defects fixed, the trace now carries the tool's own answer
```

`git status --short`：**空**；`git rev-parse HEAD` == `refs/remotes/origin/feature/mcp-server-module-rebuild`
== `382549f63e`；**里程碑 push**：`git push origin feature/mcp-server-module-rebuild` → **exit 0**，
`Everything up-to-date`（本任务无新提交，纪律照跑）。

---

## F. 遗留与如实声明

1. **Pong 只是一局、一次会话**。D138 的「≥20 个游戏」刚起步；脚手架与驱动已经可复用，
   下一个游戏一条命令即可生成（`new_game.ps1`）并跑（`run_game_session.ps1`）。
2. **`user://` 跨轮留存**：同名截图会被下一轮覆盖，run-3 因此出现 4 条 `unchanged`。
   报告里已注明，且每轮的报告都按当时的文件重新算 sha 与像素差。
3. **`PONG_TICK` 是 1 Hz**：启动窗口只留下 6 条采样。这足够证明「球没动」，
   但更细的运动曲线要用 `running_game_get_node_property_samples`（已用，30 帧）。
4. **`facts_complete` 的缺口全部是声明边界**（`not_tracked_deferred` 等），不是丢失的证据；
   报告现在会把缺口归因写清楚（`args_truncated=…`、`file_effect_status=…`、`capture_reason=…`）。
5. **本节所有数字均取自本任务实际产物**（`verify_*.json`、`fsck_*.txt`、`runs\pong\pong-run{1..4}\`、
   `runs\gates\task091\` 与两份 `git log`），没有凭印象编排。
6. **未做**：`projects\mcpplay` / `mcpplay8` 只是**原样迁入留档**，没有重跑（它们属于 GDScript 时代）。
