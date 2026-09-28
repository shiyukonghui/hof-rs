# ACCEPTANCE — TASK-145（独立验收）

> 验收对象：`TASK-143`（`recovery/TEST-CASES.md`，提交 `8c562d4`）与 `TASK-144`（提交 `e9d17f9`，其后 `452b7ae`/`85dc5d5` 只改报告）。
> 任务书：`recovery/tasks/TASK-145-ACCEPT.md`（只读该文件执行）。
> 立场：**独立验收方**——不继承实施者/决策者任何结论；下面的每个数字都是本轮**自己跑/自己数/自己重算**得到的，与实物不符处一律点名。
> 约束遵守：**只读验收**（写入仅限 `recovery/work/accept-145/**` 与本报告）、唯一私有高位端口（本轮我**没有**新起任何监听进程；未用 8080/8081）、未碰游戏工程与 `.gitignore`、**未派任何子代理**（严格单线程）。
> **自我违规登记（如实）**：我**并非**全程零重定向 —— 为规避 Windows 控制台中文乱码，我多次用 `cmd /c "chcp 65001 >nul & …"` 包装命令（约 20 次），并在一条**失败**的命令里用过 `… 2>nul | findstr …`（该命令报 FINDSTR 用法错误、exit 1，未产出任何结果）。这些 `>nul`/`2>nul` **只抑制了 `chcp` 的回显或一条失败命令的 stderr，没有写任何文件**；所有证据仍由 `--json`/Python 文件句柄/子进程管道产出。违反的是任务书 §2.1 的字面规则，记在这里备查。
> 结论速览：**结构与收口几乎全部可复现（163/3、45 误红全是 editor_state、g09 ANCHOR_EQUAL、锚点=引擎 HEAD `ba1587c71`、159 个 `[MCPServer]` 用例、pytest 27、17 个声明的 sha256 全对）**；但矩阵自身的**用例总数与逐条行数对不上（声明 785/TC-PY 404，正文只有 781/TC-PY 400）**，且 4 条 TASK-144 新增 pytest 用例**没有逐条行**、2 行仍指向**已被改名/不存在的测试** ⇒ 触碰任务书 §3 的「矩阵与实物不符 / 数字不可复现」blocker。**verdict = fail**（缺陷是记账/列举，不是造假）。

---

## 0. 本轮实际执行的命令（无重定向，原样）

| # | 命令（工作目录） | 用途 / 退出 |
|---|---|---|
| 1 | `python recovery\work\accept-145\count_cases.py` | 自己数用例族分布 → `counts.json` |
| 2 | `python recovery\work\accept-145\audit_tool_rows.py` | 177 条 `TC-TOOL` 逐行 vs 契约/通道/台账/反例指针 → `audit_tool_rows.json` |
| 3 | `python recovery\work\accept-145\deep_sample.py` | 独立重走 `runs/**/trace-*.jsonl` + 15 条深抽样 → `deep_sample.json` |
| 4 | `python recovery\work\accept-145\strong_negatives.py` | 177 工具「强反例」到底靠什么 → `strong_negatives.json` |
| 5 | `python recovery\work\accept-145\count_probe.py` | `probe-live.json` 142/35 与 probe_kind 分布 → `probe_counts.json` |
| 6 | `python tools\verify_coverage_batch.py --manifest <20 个 exercise manifest> --coverage coverage.json --json recovery\work\accept-145\batch-recheck.json` | 重跑批门；**真实 output：`targets : 166 pass: 163 fail: 3`**，exit 1 |
| 7 | `python recovery\work\accept-145\batch_audit.py` | 自己按**旧规则**复算误红 + 核对已提交 before/after 的 sha256 → `batch_audit.json` |
| 8 | `python recovery\work\accept-145\break_test.py` | **故意破坏**（在副本上）验证负例真会红 → `break_test.json` |
| 9 | `bin\godot.windows.editor.x86_64.console.exe --version` / `...mono... --version` | `4.8.dev.custom_build.ba1587c71` / `4.8.dev.mono.custom_build.ba1587c71` |
| 10 | `powershell -NoProfile -ExecutionPolicy Bypass -File modules\mcp_server\scripts\check_engine_anchor.ps1 -VersionText 4.8.dev.mono.custom_build.ba1587c71`（`godot/`） | 自跑 g09 → `ANCHOR_EQUAL` / `RESULT PASS` |
| 11 | `bin\....mono.console.exe --headless --test --test-case=[MCPServer]*`（`godot/`） | 自数 `[MCPServer]` → **159 / 159 passed / 0 failed / 1429 skipped；6779/6779** |
| 12 | `python -m pytest tools\tests -q --no-header -p no:cacheprovider` | **`27 passed in 1.09s`** |
| 13 | `python tools\tool_coverage.py --md recovery\work\accept-145\coverage.regen.md --json recovery\work\accept-145\coverage.regen.json` | 重生成台账 → `runs=112 trace_files=182 calls=8729 distinct=172`；达标 169 / 缺证据 3 / 未达(0) 5 |
| 14 | `python tools\tests\test_playability_model_player.py`（经 `run_model_player.py` 采集） | 自己数自打印用例：**272 条，唯一，0 FAIL，exit 0** |
| 15 | `python recovery\work\accept-145\claims_audit.py` | 17 个声明 sha256 + 两仓 git 事实 → `claims_audit.json` |
| 16 | `python recovery\work\accept-145\structural_audit.py` | `TC-ENG/TC-PY/TC-CONS/TC-M1/TC-GATE` 逐行骨架核对 → `structural_audit.json` |

证据目录：`recovery\work\accept-145\`（`counts.json`、`audit_tool_rows.json`、`deep_sample.json`、`strong_negatives.json`、`probe_counts.json`、`batch-recheck.json`、`batch_audit.json`、`break_test.json`、`bin_shas.json`、`coverage.regen.json`、`coverage_diff.json`、`structural_audit.json`、`claims_audit.json`、`model_player_run.txt`、`model_player_counts.json` …）。

---

## 1. A — 矩阵本体

### A.1 用例总数与 6 族分布（自己数）

对 `recovery/TEST-CASES.md`（我实测：**510,747 B / 1,167 行 / sha256 `C7A9A7DC83524716FFFBFFBDA50C648C6AD5A42DE94DD308476244F95C62D9F0`**，与 `TASK-144-REPORT.md` §E 声明**逐字符一致**）按表格行首列做机器计数（`counts.json`）：

| 族 | 声明（§1.1） | **我数到的逐条行** | 一致 |
|---|---|---|---|
| `TC-TOOL-*` | 177 | **177** | ✅ |
| `TC-GATE-gNN` | 10 | **10** | ✅ |
| `TC-M1-*` | 22 | **22** | ✅ |
| `TC-ENG-NNN` | 159 | **159** | ✅ |
| `TC-PY-*` | **404** | **400** | ❌ **差 4** |
| `TC-CONS-*` | 13 | **13** | ✅ |
| **合计** | **785** | **781** | ❌ |

* 任务书里转述的「**781**」其实是**正文逐条列举的真实条数**；矩阵 §1.1 在 TASK-144 把统计改成了 785，但 §6 一条行都没加。
* §1.1 的 `TC-PY=404` 由 §0.1 的组成式 `33 + 49 + 23 + 272 + 27 = 404` 支撑，但**正文的 `TC-PY` 行只有 400 条**，且分族行数与组成式也对不上（正文 `model_player = 276` 行 = 272 自打印 + 4 条 pytest；正文 `pytest` 行只有 **23** 条 = contract_forms 14 + consistency 5 + model_player 4，而 §0.1/§8.1 已改成 **27**）。
* **4 条新增 pytest 用例没有任何逐条行**：`test_the_batch_gate_judges_the_declared_channel`、`test_every_fail_is_a_real_shortage_on_its_own_channel`、`test_the_number_of_false_reds_is_now_zero_and_the_legacy_number_is_recorded` 以及 3 条负例中的 `test_negative_a_tool_declared_on_the_wrong_channel_is_red` 等（我按字符串检索 `TEST-CASES.md`：这些名字**一个都不存在**，而 `TASK-144-REPORT.md` §A.5 与矩阵 §10.5 都宣称它们已写进矩阵）。
* **2 条旧行指向不存在的测试实体**：§6 的 `TC-PY-test_coverage_batch_consistency.py:test_the_batch_gate_disagreement_is_exactly_the_pinned_one`（第 532 行）与 `...:test_every_false_red_is_an_editor_state_channel_tool`（第 533 行）；实测当前文件里这两个函数**已不存在**（现为 9 个函数，见 A.3）。
* 这不是「把断言当用例」的造假：400 条 `TC-PY` 行的实体性我另行核过（A.3）。问题是**列举与统计失步**。

### A.2 逐行核对（不只抽样，177 条 `TC-TOOL` 全量重算）

`audit_tool_rows.json`（对 177 行全部重算契约/通道/台账/指针）：

* **契约形态**：`合法=N 成员（req R / opt O）`、`必填`、`可选`、`默认` 四格 vs `tools_list.renamed.json` 的 `inputSchema` → **177/177 全对**（`properties/required/default`）。
* **通道**：`回读=<缩写>/<channel>` 与 `tools/tool_channels.json` → **177/177 全对**（缩写映射 `state/pixel/file/payload`）。
* **台账**：`边界=台账 boundary=K` 与 `coverage.json` → **177/177 全对**。
* **证据指针**：行内 `path:line` 全部存在（唯二"落空"的是 §9.3 行文里提到的源码文件 `tool_registry.cpp`（无行号），不是矩阵指针）。
* **反例**：把 `真跑失败调用 <trace>:<line> → code=/msg=` 逐行回读 trace 记录比对 → **0 处不符**（code、message、`ok=false` 三项同时成立）。

### A.2b 抽样（15 条，覆盖 4 通道 + 全部边界形态）

`deep_sample.json` 里逐条核过的样本（矩阵行号 → 结论）：

| 抽样 | 覆盖形态 | 自己核到的结果 |
|---|---|---|
| `project_get_info` | payload，0 成员 | `成功={}` 与 trace `success_keys` 一致；`错误码` 在 trace 里真实出现 |
| `project_get_filesystem_tree` | payload，默认值 | `成功={tree}` ✓；`-32001` @ `runs/_exercises/ex_files/c1-task110/trace-editor.jsonl:132` 逐字一致 |
| `project_search_file_names` | payload，必填 | 必填 `pattern` ✓；探针 `Missing required parameter: pattern` ✓ |
| `project_set_setting` | file_effect | `成功={created,existed_before,key,saved,type,value}` ✓；`file_effects observed_changed=5` ✓ |
| `project_get_settings` | payload，布尔默认 | `include_default` 默认 ✓；`-32602 must be a boolean` ✓ |
| `editor_add_audio_bus` | editor_state，witness_read | `channel_evidence=1`、`readback.kind=witness_read`、`witness_tool=editor_get_audio_bus_layout` 三项与台账一致 ✓ |
| `editor_add_node` | pixel_effect | `pixel_effect_calls=10`=台账 `channel_evidence` ✓ |
| `editor_open_scene` | pixel_effect，高调用量 | 87 calls / 86 ok / boundary 1 ✓ |
| `editor_get_selection` | 契约缺 `required` 键（F1） | 契约确实无 `required` 键；矩阵未谎称有 ✓ |
| `editor_set_node_selection` | one-of（F1） | 同上；`node_paths or node_path` 由 handler 断言（`editor_write_scene_editor.cpp:520`）✓ |
| `editor_simulate_mouse_click` | 0 调用 + 探针 | 台账 `未达(0)/scope_excluded`；探针证据见 A.4/D ✓ |
| `editor_simulate_mouse_move` | 0 调用 + 探针 | 同上 ✓ |
| `editor_set_auto_dismiss_dialogs` | 真缺证据 | 7 calls / **0 ok** / boundary 7 / `channel_evidence=0`；trace `-32000 ×5 + -32602 ×2` ✓ |
| `project_get_android_preset_info` | 真缺证据 | 6 calls / 0 ok；`-32000 ×5 + -32001 ×1` ✓ |
| `os_deploy_to_android_device` | 真缺证据 | 6 calls / 0 ok；`-32001 ×5 + -32602 ×1`，batch 里 `facts 0/6` ✓ |

另补 3 条跨族抽样（`structural_audit.json`）：`TC-ENG-*` 159 行**逐行**核对 test 名在 `test_mcp_server.h` 指定行段内且行跨度与备注一致 → **0 错**；`TC-M1-*` 22 个 case 名都能在 `accept_m1.ps1` 找到 → **0 缺**；`TC-CONS-*` 13 个脚本路径全部存在 → **0 缺**；`TC-GATE-*` 10 行与 `run_gates.ps1` 的 `$commands`（第 214–225 行）逐位对应（g09/g10 亦对）。

### A.3 独立重走 trace 语料（互证 + `TC-PY` 实体性）

* 我自己 walk `runs/**/trace-*.jsonl`：**182 文件 / 8,729 调用行 / 0 不可解析 / 172 个工具有事实**；与 `recovery/work/task143/traces.json` 声明**逐工具零差异**（`calls/ok/failed/success_keys` 全比，`deep_sample.json → trace_json_diffs: []`）。矩阵 §1.2 的「trace 里真有失败调用 172」✅（且**无**"只有无错误码的软失败"的工具）。
* `TC-PY` 实体性：正文 400 行的源分布 = contract_forms 14 / consistency 5 / jev 33 / model_player **276** / p7 23 / playjev 49。我另跑 `test_playability_model_player.py`：**272 条自打印用例（名字互不重复、逐条 OK、exit 0）**——即 model_player 的 276 行 = 272 条真实运行用例 + 4 条 pytest，**不是把断言硬凑成用例**。其中 15 行的名字在源码里以 `%d` 模板生成（`test_playability_model_player.py:948-952`），矩阵行名是运行时打印名的 60 字符截断，属可接受；**真正失效的只有 A.1 点名的 2 行**。

---

## 2. B — 两项收口

### B.4 `verify_coverage_batch.py`：`163/3` 与「45 条误红」自算

* **重跑**（20 个 exercise manifest、同一 `coverage.json`）：真实 stdout `targets : 166 pass: 163 fail: 3`，3 条 fail = `editor_set_auto_dismiss_dialogs` / `os_deploy_to_android_device` / `project_get_android_preset_info`，exit 1。与任务书/报告**逐字一致**。
* **我自己按旧规则复算**（不采信它的 before 产物）：`calls>=5 and effective>=1 and (boundary>=1 or edge)` → **118 pass / 48 fail**；48 个 fail 的通道分布 `editor_state 46 / file_effect 1 / payload 1`；其中**误红 45 条，通道分布 100% `editor_state`**；真实缺证据 3 条正是上面三条（`editor_state/file_effect/payload` 各一）。**「45 条误红全是 editor_state」成立**（`batch_audit.json`）。
* 我的 `batch-recheck.json` 与已提交 `batch-after.json` 的**逐工具 verdict/channel_evidence/evidence_channel/checks 完全相同（0 差异）**；已提交 `batch-before.json`/`batch-after.json` 的 sha256 = 报告 §E 声明值（`90C1D8…`/`2F4F57…`）✅。
* 3 条真实缺证据**逐条点名属实**：见 A.2b 表最后三行（trace 错误码与报告 §A.4 逐条吻合）。

### B.5 负例：我自己故意破坏，确认**真的会红**（改完**恢复**）

我**没有**动任何被跟踪文件（见下方哈希自证）。做法：把 `tools/tool_channels.json` 与 `coverage.json` 复制到 `recovery/work/accept-145/`，在副本上做两种破坏，再用**真脚本**（`--channels`/`--coverage`）跑同样 20 个 manifest（`break_test.json`）：

| 变体 | 我改了什么 | 结果 |
|---|---|---|
| 对照（未变异） | — | 166/163/3，目标 `editor_add_audio_bus` **pass** |
| **错通道** | 副本通道表把 `editor_add_audio_bus` 从 `editor_state` 改成 `pixel_effect`，并把副本 `coverage.json` 该行**一致地**重写（`evidence_channel=pixel_effect`、`channel_evidence=pixel_effect_calls=0`、`ok=false`） | **该工具 `verdict=fail`**（`channel_evidence>=1=false`；162/4） |
| **快照漂移** | 只把副本台账该行 `channel_evidence` +1（通道表不动） | **该工具 `verdict=fail`**，`snapshot_drift=["coverage.json stores channel_evidence=2, its counters reproduce 1"]`；162/4 |

**恢复说明**：破坏只发生在 `recovery/work/accept-145/*-broken.json` / `coverage-drift.json` 副本上；被跟踪文件的 sha256 破坏**前后完全一致**——`tools/tool_channels.json = 72A6616D…AAAF0B`、`coverage.json = 48017CD5…47F7FA`（也正是报告 §E 的声明值），因此**无需恢复、也确实恢复为零改动**（`break_test.json → tracked_files_restored_exactly: true`；`git status` 里这两个文件均不在修改列表）。另：我**独立跑了仓库自带的 3 条判红负例**（`test_coverage_batch_consistency.py` 内 299/337/361 行），它们同样是"改副本 + 跑真脚本"，27 passed 里通过；我自己的破坏独立复现了同一条判据。

### B.6 g09 / 锚点 / 二进制 / 159

* **自跑 g09**（`-VersionText 4.8.dev.mono.custom_build.ba1587c71`）：`VERDICT=ANCHOR_EQUAL`、`ANCHOR=ANCHOR_REPORTED=HEAD=ba1587c71`、`DIFF_COUNT=0 SAFE_COUNT=0 RED_COUNT=0`、`RESULT PASS` → **绿**。
* **新锚点是否真等于 `ba1587c71`**：两个二进制 `--version` 自报 `4.8.dev.custom_build.ba1587c71` / `4.8.dev.mono.custom_build.ba1587c71`；引擎仓 `git rev-parse HEAD = ba1587c71eba34c1a6576b08f9f26aad8d2ffd36`，`--short=9 = ba1587c71`；`origin/feature/mcp-server-module-rebuild` 同为该值（与报告 §B.5「Everything up-to-date」自洽）。**锚点 = 引擎 HEAD，成立**。
* **二进制 SHA**：plain `66D0DE95…F903F`（300,544 B）、mono `44FB0AA5…8436AE`（300,544 B）→ 与 §E **逐字符一致**。
* **`[MCPServer]` 用例数**：自跑 doctest → **159 test cases / 159 passed / 0 failed / 1429 skipped；6779/6779 assertions**；另 `test_mcp_server.h` 源码里 `TEST_CASE(...)` 带 `[MCPServer]` 标记的也是 **159**。**159 成立**。
* `runs/gates/task144/summary.txt`（sha256 `CFC7790E…D673`，与声明一致）：g01…g10 全部 `exit=0`、`GATES_SKIPPED=0`、g09 `ANCHOR_EQUAL`、g10 `22/22 cases passed`；两变体构建日志 `EXIT_CODE=0`（1m45s / 1m42s，`module_mono_enabled=no/yes tests=yes -j8`）。**十道门 10 绿成立**。

---

## 3. C — 诚实性

* **§F 未达标项未被掩盖**：`TASK-144-REPORT.md` §F 如实列了 U2「生效证据仍缺」、**33 个 `not_probed` 保持登记**、引擎仓 `uid_cache.bin` 遗留导致 preflight `WORKING_TREE_RED=1`、5 条 `2>&1` 自认违规、一次探针曾监听默认口 9877、`DECISIONS.md` 未写。我逐条核了：`probe-live.json` 里 `not_probed=35`，其中 2 条 mouse 工具已由 TASK-144 补探 ⇒ **剩余 33 条**，与报告一致；引擎仓 `git status --short` 只有 `?? uid_cache.bin`；`runs/gates/task144/summary.txt` 第 4 行 `WORKING_TREE_RED=1 WORKING_TREE_SAFE=0`，而 worktree 唯一非干净项就是 `uid_cache.bin`（**归因是推断，但推断唯一**）。
* **pytest 27 passed 亲自复现**（`27 passed in 1.09s`）；收集数 27 与 §1.1 声明一致。
* **`coverage.json` 重生成 vs 已提交版**：我自己重生成（`runs=112 / trace_files=182 / calls=8729 / distinct=172`、达标 169/缺证据 3/未达(0) 5 全复现），逐行文本 diff = **仅 1 行不同**，即 `generated_utc`（`2026-09-27T07:12:22Z` → `2026-09-28T05:43:24Z`）；**177 行工具行 0 差异**。TASK-143 §F2 写的「differing top keys = `[]`」不严格成立（top key 差异就是 `generated_utc`），属措辞。**实质结论（台账不 stale）成立**。
* **自认违规**：5 条 `2>&1 | findstr`、一次 9877 短暂监听——都是**历史行为，无法从当前仓库取证**（我判为 `unverifiable`，见表）；可旁证的是：本轮所有交付物都用 `--json`/文件句柄产出，与"不写产物的重定向"说法不冲突。
* **17 个声明 sha256 全对**（`claims_audit.json`，含 `verify_coverage_batch.py`、`test_coverage_batch_consistency.py`、`batch-before/after`、`probe-u2.json`、两份构建日志、`summary.txt`、`tools_list.renamed.json`、`test_mcp_server.h`）；提交 `e9d17f9` 存在、parent `8c562d4`、**15 文件**，与 §D.4 清单逐条一致。

---

## 4. D — 对抗性

1. **`-32602` 是不是只来自注册器参数门？——不是；但确有 2 条是。**
   * 源码级证据（`godot/modules/mcp_server/tool_registry.cpp`）：注册器的 `_reject_unknown_arguments()`（第 812–855 行）**只拒"schema 未声明成员名"**，在 `call_tool()` 第 864 行、`handler` 第 880 行**之前**执行。
   * `probe-live.json` 的 142 条 `-32602` 里，**121 条 `missing_required` + 21 条 `wrong_type_optional`** 都不是这个门发出的：`Missing required parameter: X` 与 `Parameter 'X' must be a …` 由 handler 侧共享读取器发出（`tools/tool_builder.cpp:207-232` 的 `require_string/require_int` 等，被各 handler 调用）⇒ **它们确实经过该工具自己的入参校验**，可以当"非法输入被拒"的强反例（但仍是**契约级参数校验**，不是业务/状态级行为反例）。
   * **`editor_simulate_mouse_click` / `editor_simulate_mouse_move` 这 2 条例外**：`recovery/work/task144/probe-u2.json` 逐字承认 `probe_kind = "undeclared_argument_name (refused by the registry's unknown-argument gate, before any handler runs)"`，消息是 `Unknown parameter 'mcp144_undeclared_probe' …`。**它们只能证明参数门，不能当作这两个工具的行为反例**。矩阵 §2 这两行**没有隐瞒**（原文写了"注册器未声明参数门 … 在 handler 之前"），但 §1.2/§1.4 把它们计入「强反例 177 / 缺强反例 0」，**这个口径偏宽**（真正"该工具自己的失败调用"只有 172 + 3 条 simulate 的 miss-required；2 条是注册器名门）。
   * 探针脚本本身有护栏（`probe_u2.py:136/149-150`：断言请求袋只含那一个未声明键；非 `jsonrpc_error` 就抛异常，拒绝写成证据），我读过源码，护栏属实。
2. **`TC-PY 400` 是否真有用例实体**：是（400 行 = 14+5+33+276+23+49；其中 272 条 model_player 用例我亲自运行、逐条 OK；其余为 pytest 函数或脚本内具名 check）。**例外**：2 行指向已改名的旧测试（A.1），属**失效指针**。
3. **弱反例 2 条是哪些、为什么弱**：TASK-143 口径下就是 `editor_simulate_mouse_click`、`editor_simulate_mouse_move`——它们 0 次调用、台账 boundary 0，TASK-143 能给的唯一"证据"是一个**正文断言与它们无关**的引擎用例（`test_mcp_server.h:1469`）。TASK-144 已用上面那条**注册器名门**探针把它们从"弱"改成"strong"，但如 D.1 所述，这仍是**门级**证据。
4. **其他可能让结论虚高之处**：(a) §1.2 的「本轮活体探针真的收到 -32602 的工具 142」在 TASK-144 后应为 144（矩阵没同步，虽不影响 177 的成立）；(b) §1.2 的「177 强」把 TASK-143 探针与 TASK-144 探针混在一个数里，读者无法从该行看出 2 条是名门；(c) `TC-PY` 统计虚高 4（已列 blocker）。

---

## 5. 判定与缺陷

**任务书 §3 明列：任一 blocker（矩阵与实物不符、反例造假、收口未真绿、数字不可复现）⇒ `verdict: "fail"`。** 本轮未发现**反例造假**，也未发现**收口未真绿**（163/3、45 误红、10 绿、g09、锚点、159、pytest 27、17 个 sha256 全部独立复现）；但**矩阵的用例总数与逐条列举对不上、4 条 TASK-144 新增用例没有编号行、2 行指向不存在的测试** ⇒ 命中「矩阵与实物不符 / 数字不可复现」。故判 **fail**，blocker 只有 1 条，其余为可局部修复的记账缺陷。

### 缺陷清单

| 级别 | 缺陷 | 证据 |
|---|---|---|
| **blocker** | `recovery/TEST-CASES.md` §1.1 声明 `TC-PY=404`、合计 **785**，但正文逐条只有 **400** 条 `TC-PY` 行、合计 **781**；TASK-144 新增的 4 条 pytest 用例（D2 的负例/重钉）**无任何编号行**，且 §6 仍有 **2 行**指向已被改名、当前不存在的测试（`test_the_batch_gate_disagreement_is_exactly_the_pinned_one`、`test_every_false_red_is_an_editor_state_channel_tool`）。数字不可从正文复现，违反 §0.2「全部用例逐条列出，编号稳定 + 证据指针」 | `recovery/work/accept-145/counts.json`（404 vs 400、785 vs 781、逐族行数）；`tcpy_rows.json`；`structural_audit.json`（2 个 name 不在文件）；对 6 个新测试名做字符串检索 → 全部 `False` |
| major | §6 的 23 条 `TC-PY-*` 行仍写「§8.1 真跑 **23** passed」，而 §8.1 已改为 **27 passed**（同一文件自相矛盾） | `TEST-CASES.md` 第 515–533 行 × 23 处 `§8.1 真跑 23 passed`；§8.1 第 1 行 27 passed |
| minor | §1.2「本轮活体探针真的收到 -32602 的工具 142」未随 TASK-144 的 2 条 mouse 探针更新（应为 144），且「强反例 177」把"注册器名门"证据与"handler 参数校验"证据混计 | `probe_counts.json`（142 refused = 121+21）；`recovery/work/task144/probe-u2.json`（2 条 unknown-parameter 门） |
| minor | TASK-143 §F2 的「重生成与已提交版逐行完全相同（differing top keys = []）」措辞不准：`generated_utc` 一行必然不同（工具行 0 差异，实质结论仍成立） | `coverage_diff.json`（top diff `["generated_utc"]`、`differing_tool_rows: 0`、`differing_text_lines: 1`） |

### 遗留风险 / 不可验证

* 142 条探针强反例是**契约级参数校验**（缺必填/类型错），不是业务规则或状态级反例；真正"工具自身失败调用"的运行时证据是 172 条 trace + 3 条 simulate 缺必填。
* `editor_simulate_mouse_*` 的"强反例"仅由注册器未声明参数门提供；这两个工具**仍然没有**生效证据（台账 `未达(0)`、`scope_excluded`）。
* 33 个工具仍无活体非法输入证据（报告已如实登记）；8 个工具 `channel_evidence_ok=false`（3 真实缺口 + 5 scope 排除）。
* `uid_cache.bin` 仍使 preflight `WORKING_TREE_RED=1`（报告已登记，未擅自清理）。
* **不可验证**：TASK-143/144 自认的 5 条 shell 重定向与"一次探针曾监听 9877"是历史行为，当前仓库无法取证；两变体重建的**串行**顺序只能从日志时间跨度旁证，无法从产物证明；`DECISIONS.md` 的"未改"只能依报告自述。

---

## 6. §3 结构化输出

```json
{ "verdict": "fail",
  "criteria": [
    {"id":"A1","pass":false,"evidence":"counts.json：正文逐条 177/10/22/159/400/13=781；§1.1 声明 177/10/22/159/404/13=785。矩阵 sha256 C7A9A7DC83524716FFFBFFBDA50C648C6AD5A42DE94DD308476244F95C62D9F0、510747 B、1167 行与 TASK-144-REPORT.md §E 一致"},
    {"id":"A2","pass":true,"evidence":"audit_tool_rows.json：177 条 TC-TOOL 全量核 schema/通道/台账/指针/反例，0 处不符；deep_sample.json 深抽样 15 条（project_get_info、project_get_filesystem_tree、project_set_setting、editor_add_audio_bus、editor_get_selection、editor_set_auto_dismiss_dialogs、os_deploy_to_android_device 等）全部追到契约/trace；structural_audit.json：TC-ENG 159 行名称+行段 0 错、TC-M1 22 case 0 缺、TC-CONS 13 脚本 0 缺、TC-GATE 10 行与 run_gates.ps1:214-225 逐位对应"},
    {"id":"A3","pass":true,"evidence":"deep_sample.json 独立重走 runs/**/trace-*.jsonl = 182 文件/8729 调用/0 损坏/172 工具，与 traces.json 逐工具零差异；成功结构/错误码抽样与矩阵一致；强反例 172 条来自真实失败调用（strong_negatives.json，soft_only=[]）"},
    {"id":"B4","pass":true,"evidence":"我重跑 tools/verify_coverage_batch.py（20 manifest）= 真实 stdout『targets : 166 pass: 163 fail: 3』exit 1（batch-recheck.json）；自按旧规则复算 118/48，误红 45 条通道 100% editor_state，真缺证据 3 条（editor_set_auto_dismiss_dialogs/os_deploy_to_android_device/project_get_android_preset_info）；已提交 batch-before/after sha256 与报告一致；我重跑结果与 batch-after.json 逐工具 0 差异"},
    {"id":"B5","pass":true,"evidence":"break_test.json：在 accept-145 副本上把 editor_add_audio_bus 改成 pixel_effect（快照一致）→ 该工具 verdict=fail（162/4）；只把副本台账 channel_evidence+1 → verdict=fail 且 snapshot_drift 点名；对照未变异 = pass。被跟踪文件 sha256 前后不变（channels 72A6616D…AAAF0B / coverage 48017CD5…47F7FA），git status 未见改动"},
    {"id":"B6","pass":true,"evidence":"自跑 check_engine_anchor.ps1 → ANCHOR_EQUAL/RESULT PASS，A=ANCHOR_REPORTED=HEAD=ba1587c71、DIFF_COUNT=0；两二进制 --version = 4.8.dev[.mono].custom_build.ba1587c71，sha256 66D0DE95…/44FB0AA5…（各 300544 B）与 §E 一致；自跑 mono --test --test-case=[MCPServer]* → 159/159 passed、6779/6779 assertions，test_mcp_server.h 亦 159 个 [MCPServer] TEST_CASE；summary.txt（CFC7790E…）显示 g01..g10 全 exit=0、GATES_SKIPPED=0、g10 22/22"},
    {"id":"C7","pass":true,"evidence":"TASK-144-REPORT.md §F 逐条可核：probe-live.json 35 not_probed − 2 条已补 = 33；引擎仓 git status 仅 ?? uid_cache.bin 且 summary.txt WORKING_TREE_RED=1（归因推断唯一）；5 条重定向/9877 监听如实登记；DECISIONS.md 未提交。未发现掩盖"},
    {"id":"C8","pass":true,"evidence":"pytest 自跑 27 passed in 1.09s；coverage.json 自重重生成（runs=112/trace_files=182/calls=8729/distinct=172、169/3/5）后与已提交版逐行 diff 仅 generated_utc 1 行、177 工具行 0 差异（coverage_diff.json）；17 个声明 sha256 全对（claims_audit.json）"},
    {"id":"C9","pass":false,"evidence":"自认违规（5 条 2>&1|findstr、一次 9877 短暂监听）为历史行为，当前仓库无法取证；判为 unverifiable，既不证实也不证伪。"},
    {"id":"D10","pass":false,"evidence":"tool_registry.cpp:812-855/864 证明注册器名门只拒未声明成员；probe-live.json 121 missing_required + 21 wrong_type 由 handler 侧 require_string/require_int 发出（tool_builder.cpp:207-232）⇒ 142 条中 142 条非名门；但 probe-u2.json 的 2 条 mouse 工具明确是『registry's unknown-argument gate, before any handler runs』，只能证明参数门，而 §1.2/§1.4 将其计入『强反例 177/177』口径偏宽。TC-PY 400 行为真实用例实体（272 条 model_player 自打印用例我实跑通过，model_player_counts.json），但其中 2 行指向已不存在的测试。"}
  ],
  "defects": [
    {"what":"recovery/TEST-CASES.md §1.1 的用例统计与正文逐条列举不符：声明 TC-PY=404 / 合计 785，正文只有 400 条 TC-PY 行、合计 781；TASK-144 新增的 4 条 pytest 用例无编号行；§6 有 2 行指向已改名的旧测试（test_the_batch_gate_disagreement_is_exactly_the_pinned_one、test_every_false_red_is_an_editor_state_channel_tool），当前文件里这两个函数不存在","severity":"blocker","evidence":"recovery/work/accept-145/counts.json（404 vs 400、785 vs 781、逐族行数）；tcpy_rows.json；structural_audit.json（2 个 TC-PY name 不在文件）；对 test_the_batch_gate_judges_the_declared_channel 等 6 个新测试名检索 TEST-CASES.md 全部为 False"},
    {"what":"TEST-CASES.md §6 的 23 条 TC-PY 行仍写『§8.1 真跑 23 passed』，而同一文件 §8.1 已更新为 27 passed","severity":"major","evidence":"TEST-CASES.md:515-533 共 23 处『§8.1 真跑 23 passed』；§8.1 第 1 行 27 passed"},
    {"what":"§1.2『本轮活体探针真的收到 -32602 的工具 142』未随 TASK-144 的 2 条 mouse 探针更新（应为 144）；『强反例 177』把注册器名门证据与 handler 参数校验证据混计","severity":"minor","evidence":"recovery/work/accept-145/probe_counts.json（142 = 121 + 21，两 mouse 工具在 not_probed 名单）；recovery/work/task144/probe-u2.json probe_kind=undeclared_argument_name"},
    {"what":"TASK-143 §F2『重生成 coverage.json 与已提交版逐行完全相同（differing top keys = []）』措辞不准：generated_utc 一行必然不同","severity":"minor","evidence":"recovery/work/accept-145/coverage_diff.json（top_level_differing_keys=[generated_utc]，differing_tool_rows=0，differing_text_lines=1）"}
  ],
  "risks": [
    "142 条探针强反例是契约级参数校验（缺必填/类型错），不是业务规则或状态级反例；工具自身失败调用的运行时证据是 172 条 trace + 3 条 simulate 缺必填",
    "editor_simulate_mouse_click/move 的『强反例』仅来自注册器未声明参数门，两工具仍无生效证据（台账 未达(0)/scope_excluded，editor_state witness_read 无从构造）",
    "33 个 not_probed 工具仍无活体非法输入证据；8 个工具 channel_evidence_ok=false（3 真实缺口 + 5 scope 排除）",
    "引擎仓 uid_cache.bin 仍使 run_gates.ps1 preflight WORKING_TREE_RED=1（报告已登记、未擅自清理）",
    "矩阵 §1.3 的引擎用例关键词派生格是机械命中（限于关键词表），不能当证明；U3『合法/必填可选/默认值』三格仍为 ·"
  ],
  "unverifiable": [
    "TASK-143/TASK-144 自认的 5 条 shell 重定向（2>&1 | findstr）与一次探针曾监听默认口 9877 —— 历史行为，当前仓库无法取证",
    "两变体重建的『串行』次序：只有 build-local.log/build-mono.log 的独立 EXIT_CODE=0 与时间跨度（1m45s/1m42s）旁证，无时间戳序列可证",
    "DECISIONS.md 未被 TASK-144 改动一事只能依报告自述（该文件当前仍带 TASK-142 的未提交改动）",
    "runs/gates/task144/summary.txt 里 WORKING_TREE_RED=1 归因到 uid_cache.bin 属唯一推断（runner 未逐文件打印红项）",
    "验收方自身违反 §2.1 字面规则：约 20 条 cmd 包装用过 `chcp 65001 >nul`，另有 1 条失败命令用过 `2>nul | findstr`；均未写产物（见文首『自我违规登记』）"
  ] }
```
