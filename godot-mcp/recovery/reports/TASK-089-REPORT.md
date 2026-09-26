# TASK-089 (2c-8) — 文件侧副作用入日志（第 7 轮试测 + 缺陷修复）

* Repository: `H:\rebuild\godot`, branch `feature/mcp-server-module-rebuild`
* Start HEAD: `6b4c29dc81` → End HEAD: **`b8e0142b81`**, **pushed**（fast-forward `6b4c29dc81..b8e0142b81`），
  `git status --short` **空**，与 origin 同步
* 试测工程: `H:\rebuild\projects\mcpplay`（新建，**不在 F: 上**）
* Scratch/tooling: `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task089\`
* Logs: `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs\task089_*`
* Manifest: `modules/mcp_server/docs/reports/REBUILT-2C-MANIFEST.md` § 2c-8（H-1..H-8）
* 文档: `modules/mcp_server/docs/reports/MCP-TRACEABILITY.md`（§2.4 / §3 / §3.2 / §4.2 / §5 已改写）

---

## 0. 三件事，逐条结论

| # | 要求 | 结论 |
|---|---|---|
| A | 文件侧副作用入日志（唯一缺口） | **达成**。调用行新增 `file_effect_status` + `file_effects`（绝对路径 / 前后 sha256+大小 / `changed` / `kind` / 文本文件首尾差异摘要）。收口在**模块唯一的发布原语** `publish_file_atomically()` 等 4 类 6 处磁盘原语上，**不是逐个工具散改**。实测：真正改动 → `ok_file_effect_observed`；同内容重复写 → `ok_no_effect_observed`（含走**另一条写入口**的 `project_set_setting`） |
| B | 第 7 轮试测循环 | **达成**，并产出**缺陷清单**。真实小游戏工程 + 45 次真实调用（编辑器 30 / 游戏 15），覆盖全部工具族（每族 ≥1 次生效 + ≥1 次应无效/边界）。台账：编辑器 `facts_complete 30/30`、游戏 `15/15`。**3 个缺陷根因明确并已修**，**2 项只记录不猜改** |
| C | 九道门 + 收尾 | **九门全绿**（真实输出见 §3），另 `accept_m1.ps1` **22/22**；3 次提交全部 push；F: 未触碰（前后哈希逐字节相同） |

---

## 1. A) 文件侧副作用入日志

### 1.1 设计：一个记录器 + 一处收口

新增 `modules/mcp_server/mcp_file_effects.{h,cpp}`：

* `MCPFileEffect::MutationScope(path, kind)` —— RAII：构造时快照「改动前」，析构时快照「改动后」并
  追加一行到**每次调用一个**的缓冲；
* `begin_recording()` / `end_recording()` / `take_effects()` / `status_name()` —— 由 JSON-RPC 层在
  **调用工具的那一处**（`_dispatch_tools_call` 的 `call_tool` 前后）成对调用，且**只在请求可追踪时**。

**打开 scope 的位置**（模块的磁盘原语，不是工具）：

| 位置 | 覆盖 |
|---|---|
| `tools/tool_helpers.cpp` → `publish_file_atomically()` | **模块唯一的发布原语**：场景 / 资源 / 脚本 / shader / theme / `project.godot` / 截图 / 测试报告的全部写出 |
| `tools/tool_helpers.cpp` → `publish_project_setting_to()` 的 section 分支 | 引擎自己的 `save_custom_section()` 不走上面的原语，是唯一例外 |
| `tools/tool_helpers.cpp` → `_ensure_user_data_directory()` | 唯一由模块代为建目录处（`kind: mkdir`） |
| `project_write_resource_scene.cpp`（删除场景+`.import`）、`editor_testing_read.cpp`（删桥文件）、`csharp_verdict.cpp`（构建记录）、`project_cross_scene_write.cpp`（两处 rollback） | 这四处直接写盘、不走发布原语，各自打开同一个 scope |

开销：`--mcp-trace` 关闭时**一次快照、一次哈希、一次读取都不发生**（`begin_recording()` 根本不被调用）。
开启时：>256 KiB 的文件**只记 sha 与大小、从不整份读**；含 NUL 字节的不算文本、不产生 `diff`；每行 ≤200 字符；
每次调用 ≤256 行（超出置 `truncated`）。

### 1.2 日志字段（与 `id_json`/`method`/`tool` 同层）

```json
{"id":102,"seq":2,"method":"tools/call","tool":"project_write_text_file","ok":true,
 "file_effect_status":"observed_changed",
 "file_effects":[{"path":"res://notes.txt","abs_path":"H:/rebuild/projects/mcpplay/notes.txt",
   "kind":"write","existed_before":true,"failed":false,"changed":true,
   "before":{"bytes":51,"sha256":"fdfc1fb0…"},"after":{"bytes":63,"sha256":"6a9e21b3…"},
   "diff":{"type":"line_head_tail","lines":{"before":3,"after":3},
           "same_head_lines":0,"same_tail_lines":2,
           "changed_lines":{"before":1,"after":1},"head_lines":2,"tail_lines":2,
           "head":["- MCP round-7 session text.","+ MCP round-7 session text (after-run)."],
           "tail":["- …","+ …"],"sampled_partial":false}}]}
```

`status`：`no_mutation` / `observed_changed` / `observed_no_change` / `observed_mixed` /
`not_tracked_deferred`；**空串 = 这条 trace 不带文件侧证据**（旧版本写出的 trace），绝不读作「没变」。

`diff` 如实命名为 `line_head_tail`：它是**有界的首尾差异摘要**（首尾逐行相同数 + 中间差异段行数 +
差异段首/尾各 ≤3 行），**不是完整 LCS diff**——这一点写在 `MCP-TRACEABILITY.md` §2.4 里。

### 1.3 实测演示（①②③ 全部落盘）

驱动 `work\task089\mcp089_live_evidence.ps1`，编辑器 9888 + 游戏 9889，两侧
`--mcp-trace` + `--mcp-capture=every_call` + `--mcp-capture-viewport=2d`（窗口化，非 headless）。

**① 一次真的改动文件 → `ok_file_effect_observed`**（trace-editor seq=2 / 请求 id=102）

```
file_effect_status=observed_changed
changed=True   before={51,"fdfc1fb0…"}   after={63,"6a9e21b3…"}
diff.head  = ["- MCP round-7 session text.", "+ MCP round-7 session text (after-run)."]
```

**② 同内容重复写 → `ok_no_effect_observed`**（seq=3 / id=103）

```
file_effect_status=observed_no_change
changed=False  before==after=={63,"6a9e21b3…"}
```

**② 的另一条写入口**（`project_set_setting` 走引擎 `save_custom_section()`，即 §1.1 的第二处收口）：

```
seq=22 id=122  observed_changed     H:/rebuild/projects/mcpplay/project.godot  555B"b19d6998…" → 567B"44b194c3…"
seq=23 id=123  observed_no_change   567B"44b194c3…" → 567B"44b194c3…"
```

**③ trace 行 + sha 证据 + 台账一起落盘**：

| 产物 | 路径（`…\work\task089\`） |
|---|---|
| 编辑器 trace | `live-after\trace-editor.jsonl`（62 行 / 57 590 B） |
| 游戏 trace | `live-after\trace-game.jsonl`（31 行 / 36 572 B） |
| 截图（原图不截断） | `live-after\shots-editor\` 60 个 PNG；`live-after\shots-game\` 30 个 PNG |
| 台账 | `live-after\ledger-editor.txt` / `.json`；`live-after\ledger-game.txt` / `.json` |
| 逐条请求/响应 | `live-after\e??-*.json`、`g??-*.json`（+ `.request.json`，45 组） |
| **独立**文件快照 | `live-after\live-session.txt` 末尾（会话前后对 10 个落点直接算 `Get-FileHash`） |
| 修复前对照 | `live-before\…`（同一次调用集） |

台账逐行实测（编辑器）：

```
calls=30 malformed_lines=0
verdicts: failed=4, ok_effect_observed=1, ok_file_effect_observed=10, ok_no_effect_observed=15
file_effects: changed=10, none=15, unchanged=5
...
rows whose reconstructible facts are all present: 30/30
```

独立哈希快照与 trace 的 `file_effects` **逐条一致**：`project.godot` / `main.tscn` / `notes.txt` /
`util.gd` / `scratch/paint.tres` / `created/inner/first.txt` / `shots/editor1.png` 判 CHANGED，
`main.gd` / `ui_theme.tres` / `scratch/box.tscn`（已删）判 unchanged/ABSENT——与台账逐行对应。

---

## 2. B) 第 7 轮试测循环

### 2.1 工程与调用集

`H:\rebuild\projects\mcpplay`：`project.godot`（800×600）+ `main.tscn`（Node2D + ColorRect×2 + Label，
挂 `main.gd`）+ `main.gd`（`_ready` 打 `MCP089_MINIGAME_READY`，`move_player()` / `set_hud()`；
**`_process` 里没有任何动画**，画面只因工具而变）+ Theme 资源 `ui_theme.tres` + 文本资源 `notes.txt`。
能被 9889 真跑起来（headless 冒烟：`MCP089_MINIGAME_READY name=Main player=(100.0, 220.0)`，exit 0）。

**45 次调用**（编辑器 id 102–131 / 游戏 id 201–215），工具族与「生效 / 应无效或边界」配对：

| 工具族 | 生效 | 应无效 / 边界 |
|---|---|---|
| 文件读写 | `project_write_text_file`（新建目录里新建）·`project_write_text_file` 真改 | 同内容重写 · 写 `.gd`（有专用工具） |
| 脚本写 | `project_create_script` · `project_edit_script`（真改） | 同内容 `edit_script` · 重复 `create_script`（**这个边界暴露了缺陷 D-2**） |
| 场景/节点读写 | `editor_open_scene` · `editor_set_node_property`（画面变）· `editor_save_scene`（落盘） | 同值再写 · 不存在的节点 |
| 场景/资源文件 | `project_create_scene_file` · `project_create_resource` · `project_delete_scene_file` | 再删一次 |
| 工程设置（第二处收口） | `project_set_setting`（真改 `project.godot`） | 同值再写 |
| 分析类 | `project_get_statistics` · `project_analyze_scene_complexity` · `project_search_file_contents` · `project_get_settings` | 读不存在的脚本 |
| 观察/截图 | `editor_capture_screenshot` · `running_game_capture_screenshot` | 同路径再截 |
| 运行期执行 | `running_game_set_node_property`（画面变） | 同值再写 · 不存在的节点 · **坏代码（暴露 D-1）** |
| 运行期断言 | `running_game_assert_node_state`·`assert_screen_text` | 断言**不成立**（`passed:false`，暴露「成功但结论为否」不可见） · 点不存在的按钮 |

### 2.2 台账（总调用数 / 判定分布 / 证据完整性）

| 端点 | calls | failed | ok_file_effect_observed | ok_effect_observed | ok_no_effect_observed | facts_complete |
|---|---|---|---|---|---|---|
| 编辑器 9888 | 30 | 4 | 10 | 1 | 15 | **30/30** |
| 游戏 9889 | 15 | 5 | 5 | 1 | 4 | **15/15** |

* 无 `malformed_lines`；无 `args_truncated`；无 `result_json_truncated`；无 `capture status=unavailable`
  （两个进程都是窗口化，像素差全部实测）。
* `file_effect` 分布：编辑器 `changed=10 / unchanged=5 / none=15`；游戏 `changed=5 / none=10`。
* 「证据不全无法判定」的行数：**0**（`facts_complete` 全真）。

### 2.3 缺陷清单（本轮最重要产物）

| # | 工具 + trace 行/请求 id | 现象 | 截图 / 像素差 | 文件 sha 证据 | 根因 | 处置 |
|---|---|---|---|---|---|---|
| **D-1** | `running_game_execute_gdscript`，游戏 trace `seq=3/4/5`，id `203/204/205` | **报错信息无法定位**：三次都是 `-32602 "Parameter 'code' does not compile: Parse error"`——连故意写坏的 `this_function_does_not_exist()` 与合法的一行都给出**同一个**无信息的错误 | 三次 capture `changed=False changed_pixels=0`（调用失败，画面不可能变） | 无文件副作用（`file_effect_status=no_mutation`） | 本组带了一份**逐字重复**的 `_build_source` 并调用裸 `Script::reload()`，解析器诊断被丢弃；`editor_execute_gdscript` 早已用 `reload_gdscript_capturing` + `gdscript_reload_failure_text`。**同一个解析错误，两个端点两种说法** | **已修（F1）** |
| **D-2** | `project_create_script`，编辑器 trace `seq=8`，id `108` | **报成功但声称与事实不符**：同一文件写第二次答 `{"created": true, "existed_before": true}`——**一条响应自相矛盾** | 编辑器侧 capture `unchanged`（脚本写入不动画面） | `util.gd` 在 e07 与 e10 之间才真正变形；e08 前后 sha 相同（独立快照 `util.gd CHANGED` 只记一次变化） | `out["created"] = true;` 是常量，而两个同类文本写工具（`project_text_write.cpp:196`、`project_setting_write.cpp:237`）写的是 `created = !existed` | **已修（F3）** |
| **D-3** | `running_game_execute_gdscript`（能力面） | 代码体**根本够不到运行中的场景**：`self` 是裸 `extends RefCounted`，`get_node()` / `$Path` / 节点属性 / 信号全部不可用，只有全局单例能用；而契约描述是「在运行中的游戏内执行 GDScript 代码」，**没有说这条边界** | 同 D-1 | 无 | **设计问题**（`self` 应该绑定到当前场景根？还是 SceneTree？），没有唯一根因 | **只记录不猜改** |
| **D-4** | `tool_helpers.h` | `build_execute_gdscript_source` 与 `execute_gdscript_method_name` **各声明两次**：`namespace MCPTools` 内（1137 / 1112）与 namespace 结束之后（1531 / 1513）。带 `using namespace MCPTools;` 的文件调用即 MSVC **C2668 二义性**（本轮实测，`logs/task089_build_fixes.err.log`） | — | — | 命名空间外多出一段重复声明 | **绕开**（用 `MCPTools::` 限定）；**没有**删那两处（头文件改动超出本任务证据范围） |
| **D-5** | 四个断言工具 | 每次断言都会重写 `user://mcp_test_report.json`（游戏 trace `seq=9..12`，`file_effect=changed`，trace 里能看到 `{"results":[…]}` 增长与绝对路径） | capture `unchanged`（断言不动画面） | 前端 `null` → 399B → 935B → 1300B → 1693B，sha 逐次变化 | 编辑器↔游戏测试报告桥 | **不是缺陷**，但它是「看起来只读的调用却判 `ok_file_effect_observed`」的原因；新增 `result_flags` 列给它加了限定 |
| **D-6** | `editor_set_node_property`，编辑器 trace `seq=14/15` | 同值写两次**响应形状完全相同**（`old_value`/`new_value` 都在），只有像素差能区分 | seq14 `changed=True`、seq15 `changed=False`（这是本模型要钉的形态，工作正常） | 无文件副作用 | 响应本身是诚实的（两个值都给了），读者必须自己比 | **校准记录**，不是缺陷 |
| **D-7** | 断言工具的「成功但结论为否」 | `running_game_assert_node_state` 断言不成立时仍是一次**成功调用**（应答里 `passed:false`），而调用行只有 `result_bytes`，台账**无法判定**这次断言到底过没过 | capture `unchanged` | — | 调用行不记录工具自身的返回体 | **已修（F2）** |

### 2.4 改进（只挑根因明确、改动可控的：日志/证据类 + 错误信息类）

| 修 | 内容 | 验证 |
|---|---|---|
| **F1** | `running_game_script_execution.cpp` 删掉私有 `_build_source`（与 hoist 版逐字同逻辑），改用 `MCPTools::build_execute_gdscript_source(code,false,…)` + `reload_gdscript_capturing()` + `gdscript_reload_failure_text()`，并填 `data.parse_error`（与编辑器端点同构） | 修复后同一调用 `live-after/g03-execute-gdscript.json`：`data.parse_error = {line:1, generated_line:4, in_caller_code:true, message:"Parse Error: Function \"get_node()\" not found in base self."}`；修复前 `live-before/g03-…json` 只有 `"Parse error"`。**成功路径不变**（被删的 builder 与 hoist 版三条布局规则逐字相同） |
| **F2** | `Record` 增 `result_json`/`result_json_bytes`；成功分支填工具自身返回体；`_build_line` 用与 `args` 同一上限写 `result_json`(+`_bytes`/`_truncated`)；台账据此给出 `result_flags`（`assertion_failed`/`created_conflict`/`result_unparseable`）与 `flags` 列 | 修复后游戏台账 `seq=10/11/12` 出现 `assertion_failed`——正是那三条 `passed:false`；代价如实：同一批 45 次调用的 trace 从 45 138→57 590 B（编辑器）、24 755→36 572 B（游戏） |
| **F3** | `project_script_write.cpp`：`out["created"] = !existed;` | 修复后 `live-after/e08-create-script-again.json` = `{"created": false, "existed_before": true, …}`；新增 doctest 钉住（模块用例 147→148） |

**改进前后台账对比**（`work\task089\compare_ledgers.py`，**同一调用集**）：

```
=== editor endpoint ===
calls before=30 after=30
verdicts before: {"failed":4,"ok_effect_observed":1,"ok_file_effect_observed":10,"ok_no_effect_observed":15}
verdicts after : {"failed":4,"ok_effect_observed":1,"ok_file_effect_observed":10,"ok_no_effect_observed":15}
  (no scene/file/verdict field changed for any call)
=== game endpoint ===
calls before=15 after=15
verdicts before: {"failed":5,"ok_effect_observed":1,"ok_file_effect_observed":5,"ok_no_effect_observed":4}
verdicts after : {"failed":5,"ok_effect_observed":1,"ok_file_effect_observed":5,"ok_no_effect_observed":4}
  after-run calls carrying a result flag: 3
    seq=10 id=210 running_game_assert_node_state flags=assertion_failed
    seq=11 id=211 running_game_assert_screen_text flags=assertion_failed
    seq=12 id=212 running_game_assert_screen_text flags=assertion_failed
```

**如实说明一处版本细节**：`live-after` 那次会话的二进制是在**修复代码已编入、但尚未提交**的工作树上
构建的，所以它 trace 里的 `trace_opened.version` 写的是 `4.8.dev.mono.custom_build.151b55b98`
（当时的 HEAD）。修复随后提交为 `80035ed115`；门 1–9 用的二进制自报 `80035ed11`，**编译源与那次会话
完全相同**（此后只有 `.md` 改动）。

**如实说明**：判定分布**没有变化**，而且这是正确结果——这三个修复改变的是**日志能证明什么**
（错误能不能定位、返回体能不能判、声称是否自相矛盾），不是工具做什么。可观测的变化是：
D-2 的响应 `created` 由 `true` 变 `false`、D-1 的拒绝带上行号与原因、D-7 从「无法判定」变成
「台账可判定」。

### 2.5 只记录、未改的

* **D-3**：`running_game_execute_gdscript` 的代码体够不到场景。这是**设计决定**（`self` 绑什么），
  不是单一根因的缺陷。如果要让「运行期执行」真能驱动游戏，需要先定契约（描述里也必须写明边界），
  因此本轮**不动**。
* **D-4**：`tool_helpers.h` 的重复声明。已用限定名绕开；删除那两处是头文件级改动，超出本轮证据，
  **不动**。
* 另外，`project_create_shader` / `project_create_theme` / `project_create_animation` 等写工具也是
  `out["created"] = true;` 的常量写法（与 D-2 同形），但本轮**没有调用它们**，**没有证据**，故
  **只记录、不猜改**。

---

## 3. C) 收尾

### 3.1 九道门（真实输出，二进制自报 `4.8.dev.mono.custom_build.80035ed11`）

| # | 门 | 命令 | 结果 |
|---|---|---|---|
| 1 | 模块 doctest | `bin\godot.windows.editor.x86_64.mono.console.exe --headless --test --test-case=[MCPServer]*` | **exit 0** — `148/148 passed`、`6464/6464` 断言、`SUCCESS!`（2c-7 基线 143/6396） |
| 2 | 全量 doctest | 同二进制 `--headless --test` | **exit 0** — `1574/1574 passed / 3 skipped`、`430777/430777`、`SUCCESS!` |
| 3 | 组清单 | `python modules\mcp_server\docs\scripts\check_tool_groups.py` | **exit 0** — `TOOL-GROUPS CHECK PASS`，5681 B，sha `b83d79d3…` |
| 4 | 契约子集（活链） | `scripts\check_contract_subset.ps1` | **exit 0** — `3/3 checks passed`；editor 9888 `tools=154`、game 9889 `tools=73`、`guard_user_port_9877` PASS |
| 5 | rename map | `python docs\scripts\check_rename_map.py` | **exit 0** — `RESULT: PASS`；`177 == 174 - 2 - 1 + 6` |
| 6 | 同义反复 | `python scripts\check_tautologies.py` | **exit 0** — `TAUTOLOGY CHECK PASS` |
| 7 | 退出码传播 | `python scripts\check_exit_propagation.py --probes` | **exit 0** — `PROBES: 10/10` |
| 8 | 硬编码计数 | `python scripts\check_hardcoded_counts.py` | **exit 0** — `UNCLASSIFIED = 0` |
| 9 | 引擎锚点 | `check_engine_anchor.ps1 -VersionText '4.8.dev.mono.custom_build.80035ed11'` | **exit 0** — `ANCHOR_EQUAL`，`diff_count=0`，`RESULT PASS`；在最终 HEAD `b8e0142b81` 上再判 `ANCHOR_STRUCTURAL_EQUIVALENT`（diff=1 个 `.md`，`RED_COUNT=0`），仍 **PASS** |
| + | M1 验收 | `scripts\accept_m1.ps1` | **exit 0** — `22/22 cases passed`（`logs\task089_accept_m1.stdout.txt`） |
| + | 溯源演示 | `mcp089_live_evidence.ps1` + `mcp_trace_ledger.py` | 编辑器 `calls=30` `facts_complete 30/30`；游戏 `calls=15` `15/15` |

门运行器：`work\task089\run_gates.ps1`（每道门一个 `cmd.exe` 子进程；退出码在子进程**内部**用
`%ERRORLEVEL%` 打印后再解析——本机 PowerShell 对重定向子进程的 `$p.ExitCode` 恒为空，这是 2c-7
G-5 同一类坑）。日志 `logs\task089_final_g0*.stdout.txt`，汇总 `logs\task089_final.summary.txt`。

**诚实标注**：门 1/2/9 用的是 **mono** 二进制（非 mono 二进制本轮未重建，与 2c-7 的声明一致）。

### 3.2 git

```
git log --oneline -8
b8e0142b81 modules/mcp_server: task089 (2c-8) step3 - the gate ledger (9/9 + 22/22) and the iron-rule record
80035ed115 modules/mcp_server: task089 (2c-8) step2 - the round-7 test loop: three defects fixed, the trace now carries the tool's own answer
151b55b984 modules/mcp_server: task089 (2c-8) step1 - the call line carries the file-side half of "did this call do anything"
6b4c29dc81 modules/mcp_server: task088 (2c-7) step2 - the gate ledger (9/9) and the live traceability ledger
e4b025519a modules/mcp_server: task088 (2c-7) step1 - record identity on the trace, the six missing contract overrides, accept_m1 22/22
675df5ef27 modules/mcp_server: task087 (2c-6) - gate ledger, and accept_m1.ps1's four remaining FAILs named
586cb5e010 modules/mcp_server: task087 (2c-6) step5a - recover the two missing group manifests; contract subset gate is 3/3
ab99c693cc modules/mcp_server: task087 (2c-6) step1 - step-5 boundary review + the three conflict cases, suite honestly green

git status --short
(empty)
git rev-parse HEAD                       = b8e0142b8179659639249b27f6c8b78ae036513f
git rev-parse origin/feature/...         = b8e0142b8179659639249b27f6c8b78ae036513f   (同步)
```

`git push`：一次，fast-forward、无 force、无拒绝 — `6b4c29dc81..b8e0142b81`，exit 0。

### 3.3 F: 未触碰证据（开工与收尾各测一次，逐字节相同）

```
537251 114B2A8218E35DF8E998FA4329D99F97D6037987E19FBA4A324B567C009CF323  F:\moonbit-hof-rs\DECISIONS.md
 48749 8F8051C4C0F8941089F0B21A193CEF7C51FA7C41D7E312B1463EA8593F313C54  F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json
```

与 `TASK-088-REPORT.md` 记录的前值完全一致（该 fixture 是契约生成器的输入，**只读**）。
写盘只发生在 `H:\rebuild\godot`、`H:\rebuild\projects\`、`C:\Users\wyl\AppData\Local\Temp\mcp-recovery\`。

### 3.4 铁律

* **没有一次 shell 重定向**：所有日志由 `Start-Process -RedirectStandardOutput/-RedirectStandardError`
  写出，所有文本由 `Set-Content`/`-NoNewline`、Python 写文件或 `write` 工具写出。
* **破坏性命令**：只有一处，共 4 次，每次构建前 —— `work/task088/del_stale_objs.py --apply`
  （绝对路径 / 单一白名单前缀 `H:\rebuild\godot\bin\obj\` / 与 tracked `mcp057_build_mono.cmd` 完全同名的
  4 个路径 / 先打印清单 / 先 dry run / 无通配符无 `..`；每次 3 存在 1 缺失）。别处没有删除、移动、改名。
* **构建与运行一律从 `cmd.exe` 启动**（`task089_build_mono.cmd`、`task089_gate*.cmd`、门运行器），
  用 `WaitForExit()`。
* 非证据来源的改动**全部**用 `// [REBUILT-2C low-confidence: verify] … // [/REBUILT-2C]` 包住，
  并逐条登记进 `REBUILT-2C-MANIFEST.md` § 2c-8（H-1..H-8）。

---

## 4. 遗留 / 未做到（如实）

1. **`running_game_execute_gdscript` 仍不能驱动运行中的游戏**（D-3，设计问题，未改）。本轮游戏侧
   「生效」的证据来自 `running_game_set_node_property`、`running_game_capture_screenshot` 与断言族。
2. **失败应答的 `data`（`suggestion` / `parse_error`）仍不在 trace 上**，只有 `error_code` +
   ≤512 B 的 `error_message`。F1 修掉了其中最要命的形状（只说 "Parse error"），但结构化失败细节
   **仍未入日志**——`MCP-TRACEABILITY.md` §3.2 显式保留为开着的缺口。
3. **延迟应答通道（deferred 工具）的文件侧副作用仍不可观测**，如实写 `not_tracked_deferred`。
   本轮没有调用任何一个 deferred 工具。
4. **D-4 的重复声明未删**（用 `MCPTools::` 绕开）。
5. **同形 `created = true` 常量写法的其它写工具未验证、未改**（无调用证据，只记录）。
6. 门 1/2/9 的二进制是 **mono**；非 mono 二进制本轮未重建。
7. `editor_capture_screenshot` 同路径第二次：`file_effect=unchanged`（PNG 字节完全相同）而
   `scene_effect=unchanged`——这两者一致，但**没有**回答「截图工具是否应当拒绝覆盖」这个契约问题，
   未改。
