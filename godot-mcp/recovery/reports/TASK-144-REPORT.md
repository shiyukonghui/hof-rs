# TASK-144 REPORT — 收口工具测试的两个可修项：U4 陈旧批校验脚本 + U1 g09 锚点漂移（附 U2 补强）

> 任务书：`recovery/tasks/TASK-144.md`（子代理只读该文件执行）。
> 交付物：`tools/verify_coverage_batch.py`、`tools/tests/test_coverage_batch_consistency.py`、`recovery/TEST-CASES.md`（只改相关行）、
> `recovery/work/task144/**`、本报告、两个引擎二进制（重建，无源码改动）。
> **事实来源分级**：本报告里 §A/§B/§C 的每个数字都来自本轮真跑的原始输出（命令与产物路径一并给出）；
> 凡引自 TASK-112/118/143 的，标明出处。**未达标项与自认的违规在 §F 与 §D.1 如实登记。**

---

## 0. 结论摘要

| 项 | 结果 |
|---|---|
| **A（U4）** | `verify_coverage_batch.py` 已对齐现行通道规则（**判据只改误报，未放宽任何缺口判据**）：`166 目标 118 pass / 48 fail` → **`163 pass / 3 fail`（0 条误红）**；3 条真实缺证据逐条点名（§A.4）。新增 **3 条会判红的负例**（§A.5）。`TEST-CASES.md` 相关行已更新（§A.6）。 |
| **B（U1）** | 两变体在 HEAD `ba1587c71e` 上**串行重建**（均 exit 0，`--version` 均变为 `ba1587c71`）→ **十道门 g01…g10 全部 exit=0**（g09 **`ANCHOR_EQUAL`**，g10 `accept_m1` **22/22**）→ push 真实输出 **`Everything up-to-date`**（本地 HEAD 与 origin 同为 `ba1587c71eba34c1a6576b08f9f26aad8d2ffd36`，本次无新提交可推）。新锚点 **`ba1587c71`**。**未发现“非纯记账漂移”的证据**（§B.6）。 |
| **C（U2）** | U2 的两条 simulate 工具**已补上真实失败观察**（活体探针，只触发注册器的未声明参数门、在 handler 之前，安全）：两条都真收到 `-32602`（§C.1）。F1 保持 PIN 不动（§C.2）。 |
| **D** | 铁律、所有权、两仓 git、关键产物 sha256 见 §D/§E。**自认违规：4 条命令用了 `2>&1` 重定向**（§D.1）。 |

---

## A. U4 —— 把陈旧批校验脚本对齐现行规则

### A.1 现行规则（**代码优先**，不采信任何文档/报告）

* `tools/tool_coverage.py`（TASK-118 item A 起）给每个工具在 `tools/tool_channels.json` 里声明**唯一权威证据通道**，并**只在该通道上**判 `达标`：
  `status_of_channel(calls, channel_evidence, boundary)`：`calls>=5 and channel_evidence>=1 and boundary>=1`（`tool_coverage.py:380-393`）；
  通道证据计数函数是 `channel_evidence_count(st, channel, readback)`（`:356-377`）：
  `pixel_effect→pixel_effect`、`file_effect→file_effect`、`payload→read_payload`、`editor_state→readback.expect_matched`。
* `tools/verify_coverage_batch.py` 修前仍用 **TASK-118 之前**的量：`calls>=5 and effective>=1 and (boundary>=1 or edge)`，
  其中 `effective` 只有“像素/文件真的动了”才算 ⇒ **所有 `editor_state` 通道工具 `effective` 恒为 0** ⇒ 系统性误红
  （真跑通道分布：契约 177 = `payload` 76 / `editor_state` **51** / `pixel_effect` 28 / `file_effect` 22；修前 48 个 fail 里 **46 个是 `editor_state`** = 45 误红 + 1 真缺，另 2 个是 `file_effect`/`payload` 的真缺）。
* 复算互证（`recovery/work/task144/check_recompute.py`，真跑）：用 `tool_coverage.py` **自己的** `channel_evidence_count()`，喂 `coverage.json` 每行的
  `pixel_effect_calls`/`file_effect_calls`/`read_payload_calls`/`readback`，对 **177 行全部**复现出该行已存的 `channel_evidence` 与 `evidence_channel`：
  ```
  rows=177 mismatch=0
  ```
  这是“不重写定义、直接复用台账函数”的可行性证据。

### A.2 修法（`tools/verify_coverage_batch.py`）

1. **判据换成现行规则**：`verdict = calls>=5 and channel_evidence>=1 and (boundary>=1 or declared edge)`。
   `effective` 保留为**仅供对照打印的信息列**，**不再是门槛**（脚本 docstring 与 `--json` 的 `legacy_quantity` 字段都写明）。
2. **不复制规则，改为 import**：脚本 `import tool_coverage as ledger_rule`，直接调用台账自己的
   `load_channels()`（通道表校验：契约覆盖恰好、通道闭集、**通道必须与工具动词一致**）与 `channel_evidence_count()`。
   * 新增 `--channels PATH`（默认 `tools/tool_channels.json`）：`tool_coverage.load_channels()` 只从 `<root>/tools/tool_channels.json` 读表，
     故非默认表会被暂存到一个临时 root 下再交给**同一个**校验函数，判据定义仍然只有一份。
3. **新增“快照必须自洽”护栏**（诚实性，不是放宽）：目标工具的 `coverage.json` 行必须与 `tool_channels.json` 声明一致 ——
   通道名、`channel_evidence`、`channel_evidence_ok` 三者都要能被行内计数复现；任何一条不符即判 **fail** 并把分歧逐条打印。
   这挡住“通道表改过、台账没重生成、却被按旧通道静默判定”的失效模式。
4. 退出码语义不变：全部 pass → 0；有 fail → 1；用法/IO 错、或通道表被台账规则拒绝 → 2。

### A.3 前后对照（同一语料、同一 20 个 exercise manifest）

原始命令（本地 AI 分片输出到 `--json`，**未用 shell 重定向**）：

```
python tools\verify_coverage_batch.py --manifest <20 个 tools\sessions\_exercises\*\*-manifest.json> --coverage coverage.json --json <out>
```

| | targets | pass | fail | 其中误红 | 其中真实缺证据 |
|---|---|---|---|---|---|
| **修前（`batch-before.json`）** | 166 | **118** | **48** | **45** | **3** |
| **修后（`batch-after.json`）** | 166 | **163** | **3** | **0** | **3** |

修前 48 个 fail 的通道分布（真跑统计）：`('editor_state', 误红)=45`、`('editor_state', 真缺)=1`、`('file_effect', 真缺)=1`、`('payload', 真缺)=1`。
修后 fail 只剩那 3 条。**数字与任务书给出的 `118/48 → 163/3` 逐字一致。**

### A.4 3 条真实缺证据：逐条点名 + 缺什么

三条都是 `coverage.json` 里 `channel_evidence_ok=false`（台账 `计数达标缺证据`），**不是**误报；修后仍应为红。

| 工具 | 通道 | calls/ok/boundary | 缺什么（原始 trace 证据） |
|---|---|---|---|
| `editor_set_auto_dismiss_dialogs` | `editor_state` | 7 / 0 / 7 | 本引擎**没有进程级 auto-dismiss 开关**（台账 `ledger_class=engine_not_implemented`）。`runs/_exercises/ex_editor/h7-task115/trace-editor.jsonl` seq 74–78 = `-32000 "Not implemented: editor_set_auto_dismiss_dialogs"`（带 435 B `suggestion`），seq 79 = `-32602 "Missing required parameter 'enabled'"`，seq 80 = `-32602 "Parameter 'enabled' must be a boolean, got String"`。**7 次调用没有一次 ok ⇒ 不存在“另一次独立读调用逐字读回被写的值”的机会**，`editor_state` 通道证据恒为 0。缺的是**引擎的成功分支**，不是测试。 |
| `os_deploy_to_android_device` | `file_effect` | 6 / 0 / 6 | `runs/_exercises/ex_grid/c7-task118/trace-editor.jsonl` seq 13–17 = `-32001 "Export preset 'NoSuchAndroidPreset' not found"`，seq 18 = `-32602 "'Windows Desktop' is a Windows Desktop export preset, not an Android preset; this tool only deploys Android presets"`。**缺 Android export preset + 真机/设备**，盘上文件不会真的变；另：**6/6 调用的 `file_effect=not_recorded`、`facts_complete=0/6`**（调用不可完全审计）本身也是台账证据缺口。 |
| `project_get_android_preset_info` | `payload` | 6 / 0 / 6 | 同一 trace seq 7–11 = `-32000 "No Android export preset is configured in this project"`（`error_data` 带 `preset_count/presets_file/presets_file_present` 与 suggestion），seq 12 = `-32001 "Export preset 'NoSuchAndroidPreset' not found"`。**没有一条 `ok=true` 且回包是实质载荷的调用** ⇒ `payload` 通道证据 0。缺的是**带 Android preset 的工程**。 |

### A.5 负例（D2）：会判红的错输入，并已写成测试

`tools/tests/test_coverage_batch_consistency.py`（TASK-143 建、本轮升级）现在有 **9 条 pytest**，其中 3 条是**必须判红的负例**，每条都配**正向对照**：

| 负例（pytest 名） | 故意构造的错输入 | 期望 | 实测 |
|---|---|---|---|
| `test_negative_a_tool_declared_on_the_wrong_channel_is_red` | 取一个**正在 pass** 的 `editor_state` 目标（动态选：`pixel_effect_calls==0`），把它在**通道表**里改声明成 `pixel_effect`，并把 `coverage.json` 副本**一致地**重整（`evidence_channel=pixel_effect`、`channel_evidence=pixel_effect_calls=0`、`ok=False`，于是没有“快照漂移”干扰） | exit **1**，该工具 `verdict=fail`，`channel_evidence==0` | ✅ 通过；未变异的对照运行里同一工具是 `pass` |
| `test_negative_a_snapshot_that_contradicts_its_own_counters_is_red` | 把某个 pass 工具的 `coverage.json` 行 `channel_evidence` **+1**（行内计数复现不出来） | exit **1**、`verdict=fail`、`snapshot_drift` 非空 | ✅ 通过 |
| `test_negative_a_payload_channel_on_an_action_verb_is_rejected` | 把某个 pass 的**动作词**工具声明成 `payload`（台账的动词守卫：`read_payload` 只对读词累计，这个门永远满足不了） | exit **2** 且输出含 `contradicts the tool verb` | ✅ 通过（**通过脚本继承了台账自己的守卫**，而不是第二份实现） |

正向对照另有 `test_the_negative_the_internal_check_is_not_vacuous`（把某行 `channel_evidence` 清零必须让台账自洽检查报怨）。
测试仍**调用真正的 `verify_coverage_batch.py`**（子进程，`--json`），不是复制一份规则。

真跑结果：

```
D:\Anaconda\python.exe -m pytest tools\tests\test_coverage_batch_consistency.py -q --no-header -p no:cacheprovider
.........                                                                [100%]
9 passed

D:\Anaconda\python.exe tools\tests\test_coverage_batch_consistency.py
ok    the ledger is internally consistent
ok    the manifests exist
ok    the gate writes a report
ok    targets/pass match the pin
ok    the gate has no false red
ok    the genuinely-short set matches the pin
ok    every fail is short on its own channel
ok    a control target exists for the negatives
ok    negative: a tool declared on the wrong channel is red

9/9 checks passed
```

全仓 pytest 也从 23 → **27 passed**（本文件 5 → 9 条；`pytest tools\tests --collect-only -q` = 27 tests collected）。

### A.6 `TEST-CASES.md` 的更新（只改相关行 + 统计）

改动清单（明细见该文件新增的 §10.5）：§0.1 `tools/tests/**` 计数行、§1.1 的 `TC-PY-*`（400→**404**）与**合计（781→785）**、
§1.2 强/弱反例两格（175→**177**、2→**0**）、§1.4 缺口两行、§2 里两条 simulate 工具行、
§7 的 `check_engine_anchor.ps1` 与 `verify_coverage_batch.py` 两行、§8.1 的 pytest 与 `verify_coverage_batch.py` 两行、
§8.2 的 g09 行与输出块（新增 TASK-144 B 更新）、§8.3 preflight 段、§9.2 的 F2 段、§9.3 的 U1/U2 两段。
**矩阵其余行、统计与叙述一字未动。**

---

## B. U1 —— g09 锚点漂移：两变体重建 → 十道门 → accept_m1 → push

### B.1 重建前的一手事实（复核 TASK-143 的结论）

```
bin\godot.windows.editor.x86_64.console.exe --version        -> 4.8.dev.custom_build.3fdabe2d9
bin\godot.windows.editor.x86_64.mono.console.exe  --version  -> 4.8.dev.mono.custom_build.3fdabe2d9
git -C godot rev-parse --short=9 HEAD                        -> ba1587c71
bin\...mono.console.exe --headless --test --test-case=[MCPServer]*
    [doctest] test cases:  159 |  159 passed | 0 failed | 1429 skipped
    [doctest] assertions: 6779 | 6779 passed | 0 failed
```

即：二进制自报 `3fdabe2d9`，但其内含 **159** 个 `[MCPServer]` 用例 = **HEAD 的条数**（`3fdabe2d9` 时是 157）。
**二进制包含 TASK-112 的改动，只是 `--version` 里烘的锚点串没换** —— 锚点记账漂移的判据成立。

### B.2 两变体重建（串行、cmd 启动、真实退出码）

| 变体 | 命令 | 墙钟 | exit | 重建后 `--version` | 构建日志 |
|---|---|---|---|---|---|
| plain（非 mono，单精度） | `modules\mcp_server\scripts\build_local.cmd -Force` | **1m45s**（`Time elapsed: 00:01:45.01`） | **0** | `4.8.dev.custom_build.ba1587c71` | `recovery/work/task144/build-local.log` |
| mono | `modules\mcp_server\scripts\mcp057_build_mono.cmd` | **1m42s**（`Time elapsed: 00:01:42.07`） | **0** | `4.8.dev.mono.custom_build.ba1587c71` | `recovery/work/task144/build-mono.log` |

* 两个 `.cmd` 内部就是既有的 scons 命令（`platform=windows target=editor module_mono_enabled={no,yes} tests=yes -j8`），
  并各自执行了 `-Force` 语义（删除 `test_mcp_server.obj`、`test_main.obj`、`mcp_trace*.obj`），日志两行 `EXIT_CODE=0` 可核。
* **串行**：先 plain 后 mono，同一时刻只有一个 scons（D62）；未并发。
* 重建**没有改任何源码**：`git -C godot status --short` 全程只有既有的未跟踪 `uid_cache.bin`。

### B.3 十道门（逐门，真跑）

命令：`powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_gates.ps1 -Tag task144 -RunGates`
（`-RunGates` 是**显式要求无条件跑十门**；否则 preflight 在 `ANCHOR_EQUAL` 下会直接 `SKIP_REBUILD`）。
逐门账：`runs/gates/task144/summary.txt`；每门 stdout/stderr：`runs/gates/task144/gNN.stdout.txt` / `gNN.stderr.txt`。

| 门 | 命令（要点） | exit | 实测摘要 |
|---|---|---|---|
| g01 | mono `--headless --test --test-case=[MCPServer]*` | **0** | `159 / 159 passed, 0 failed, 1429 skipped`；`6779/6779 assertions` |
| g02 | mono `--headless --test` | **0** | `1585 / 1585 passed, 0 failed, 3 skipped`；`431092/431092 assertions` |
| g03 | `python modules\mcp_server\docs\scripts\check_tool_groups.py` | **0** | `TOOL-GROUPS CHECK PASS`（41 工具 / 7 组；`SHA256 b83d79d3…`） |
| g04 | `powershell … check_contract_subset.ps1` | **0** | `3/3 checks passed`（editor 9888 tools=154、game 9889 tools=73、`guard_user_port_9877 pid_before=-1 pid_after=-1`） |
| g05 | `python modules\mcp_server\docs\scripts\check_rename_map.py` | **0** | `RESULT: PASS`（G1..G6 全绿，`177 == 174-2-1+6`） |
| g06 | `python modules\mcp_server\scripts\check_tautologies.py` | **0** | `TAUTOLOGY CHECK PASS`（1 pinned，2 类文件/2 root） |
| g07 | `python modules\mcp_server\scripts\check_exit_propagation.py --probes` | **0** | `PROBES: 10/10` |
| g08 | `python modules\mcp_server\scripts\check_hardcoded_counts.py` | **0** | `RESULT: PASS`（116 处、`UNCLASSIFIED=0`） |
| g09 | `powershell … check_engine_anchor.ps1 -VersionText 4.8.dev.mono.custom_build.ba1587c71` | **0** | **`ANCHOR_EQUAL`**：`ANCHOR=ba1587c71 ANCHOR_REPORTED=ba1587c71 HEAD=ba1587c71`、`DIFF_COUNT=0 SAFE_COUNT=0 RED_COUNT=0`、`RESULT PASS` |
| g10 | `powershell … accept_m1.ps1`（即 `accept_m1`） | **0** | **`22/22 cases passed`** |

十门 **10 绿**（`GATES_SKIPPED=0`）。重建前 TASK-143 的十门是 9 绿 1 红（唯一红即 g09）；重建后没有**任何**门回退。

### B.4 `accept_m1`（单独复核）

十门里的 g10 就是 `accept_m1.ps1`，`22/22 cases passed`（含 `case12_game_process_endpoint`、`case20_tools_list_cross_process_restart`、`guard_user_port_9877`）。
`TEST-CASES.md` §8.4 记录的 TASK-143 结果也是 22/22，**无变化**。

### B.5 push（不 force、只在目标分支）

```
git -C godot push origin feature/mcp-server-module-rebuild
-> Everything up-to-date
git -C godot rev-parse HEAD                              -> ba1587c71eba34c1a6576b08f9f26aad8d2ffd36
git -C godot rev-parse origin/feature/mcp-server-module-rebuild -> ba1587c71eba34c1a6576b08f9f26aad8d2ffd36
git -C godot status -sb                                  -> ## feature/mcp-server-module-rebuild...origin/feature/mcp-server-module-rebuild
```

**如实说明**：TASK-112 的引擎提交 `ba1587c71e` 在它自己的批次里**已经推过**（`recovery/reports/TASK-112-REPORT.md` 的记录与现在的 origin 引用一致），
本任务只做“重建 + 重跑门”，**没有产生新的引擎提交**，因此 push 没有内容可推。命令真实执行、输出逐字为 `Everything up-to-date`；**未 force、未换分支、未改远端任何东西**。

### B.6 新锚点 + “是否纯记账漂移”

* **新锚点：`ba1587c71`**（plain 与 mono 两个变体同锚；`--version` 分别为 `4.8.dev.custom_build.ba1587c71` / `4.8.dev.mono.custom_build.ba1587c71`）。
* **重建没有暴露“确非纯记账漂移”**：重建前后唯一可观察的变化就是两个二进制 `--version` 的锚点串；
  其余九道门与 `accept_m1` 的结果与重建前**逐条一致**（重建前 TASK-143 实测：g01 159/159、g02 1585/1585、g03..g08 绿、g10 22/22），
  且重建前二进制已含 HEAD 的 159 条 `[MCPServer]` 用例。因此**不存在“二进制缺了某个编译输入”的证据**，收口方式是真绿而非伪锚点。
* 二进制 sha256 见 §E。

---

## C. U2 / F1 的处置（D6）

### C.1 U2 —— 从“如实登记”升级为“真的补上失败观察”（本轮新增，真跑）

U2 的两条：`editor_simulate_mouse_click`、`editor_simulate_mouse_move`（TASK-143 时：0 次调用、`scope_excluded`、台账 boundary 0、连弱反例都不是关于它们的）。

**为什么 TASK-143 的“做不到”只对一半成立**：TASK-143 的 `not_probed` 理由是“写类且无必填参数 ⇒ 构造非法输入就可能真的改状态”。
那对**值**探针成立（要让 handler 跑到值规则才拒），但对**名**探针不成立，因为有源码级的次序保证：

```
tool_registry.cpp:857-866   MCPToolRegistry::call_tool()
    :864  if (!_reject_unknown_arguments(*def, p_args, r_error)) { return Variant(); }   // 未声明参数门
    :880  const Variant result = def->handler(p_args, r_error);                          // 才会跑 handler
editor_input_simulation.cpp:1172   ToolBuilder("editor_simulate_mouse_click").…schema(schema).handler(_tool_simulate_mouse_click)
editor_input_simulation.cpp:1201   ToolBuilder("editor_simulate_mouse_move").…schema(schema).handler(_tool_simulate_mouse_move)
        （两者都 mutating(true)；契约里 required=[]，properties 分别是 {button,pressed,x,y} / {x,y}）
```

所以“只带一个**未声明成员名**”的调用会被注册器当场拒为 `-32602 Unknown parameter ...`，**注入编辑器输入事件的 handler 根本不会执行** —— 探的是参数门，不是工具行为，**不会动鼠标**。

真跑（`recovery/work/task144/probe_u2.py`，**只起 editor 端点、只用唯一高位端口 9919**、scratch 在 `%TEMP%\task144-probe`、进程在 `finally` 里终止）：

```
wrote F:\moonbit-hof-rs\godot-mcp\recovery\work\task144\probe-u2.json
harness: {"import": true, "import_listen": ["[MCP] listening on 127.0.0.1:9919 (editor=true, tools=154)"], "port_up": true, "tools_list_count": 154, "both_targets_registered": true}
editor_simulate_mouse_click      refused_-32602 code=-32602 message=Unknown parameter 'mcp144_undeclared_probe' for tool 'editor_simulate_mouse_click'
editor_simulate_mouse_move       refused_-32602 code=-32602 message=Unknown parameter 'mcp144_undeclared_probe' for tool 'editor_simulate_mouse_move'
```

逐字响应（`probe-u2.json`）：

```
{"error":{"code":-32602,"data":{"suggestion":"Accepted parameters of editor_simulate_mouse_click: button, pressed, x, y"},
 "message":"Unknown parameter 'mcp144_undeclared_probe' for tool 'editor_simulate_mouse_click'"},"id":1,"jsonrpc":"2.0"}
{"error":{"code":-32602,"data":{"suggestion":"Accepted parameters of editor_simulate_mouse_move: x, y"},
 "message":"Unknown parameter 'mcp144_undeclared_probe' for tool 'editor_simulate_mouse_move'"},"id":2,"jsonrpc":"2.0"}
```

脚本自带护栏：**断言请求参数袋只含那一个未声明键**；回答若不是 `jsonrpc_error` 就抛异常、**拒绝**把“偷跑成功”写成证据。
跑完后 `netstat`/`tasklist` 复查：9919/9877/9888/9889 都无监听，无残留 godot 进程。

**边界如实说明（不夸大）**：
* 这补的是**非法输入被拒**的**强反例**（`TEST-CASES.md` §1.2 强反例 **175→177**、弱反例 **2→0**；矩阵 A 两行的“非法/错误码/强度/现状”已更新为 `present`）。
* 这**不是**这两个工具的**生效证据**：台账仍是 `未达(0)` / `scope_excluded`；`editor_state` 通道要的 witness_read（读回被注入的输入事件）依旧无从构造，
  登记表的 `still_out.measurable_when` 自己写着“这样的批次买得到计数与边界，**买不到 tier**”（`tools/tool_coverage_unreachable.json:137`）。
* **其余 33 个 `not_probed` 工具没有任何变化**（保持 TASK-143 的如实登记）。
* `editor_simulate_key` / `editor_simulate_input_action` / `editor_simulate_input_sequence` **有**必填参数，本可走“缺必填”探针，但那是 TASK-143 探针范围的既有选择，本任务**不去动它**（U2 只点名两条 mouse 工具）。

### C.2 F1 —— 保持 PIN，不动

F1 = 3 条工具 schema 没有 `required` 键（`editor_get_selection`、`editor_set_node_selection`、`editor_remove_node_selection`，其中 `set_node_selection` 是 one-of，方言表达不出）。
**处置：保持登记（PIN），未改契约、未改 pinned 集合。** 理由（未变）：`tools_list.renamed.json` 就是 `accept_m1` 的逐字比对基准（g10 case3 逐字 154/154），
改它会把“契约形态约定不一致”变成“端到端验收基准漂移”，属于决策者的取舍，不在本任务范围。`tools/tests/test_contract_forms.py` 的 PIN 原样未动。

---

## D. 铁律、所有权、两仓 git（D7）

### D.1 铁律逐条

| 铁律 | 本轮实际 |
|---|---|
| **禁止一切 shell 重定向** | **自认违规 4 条，全部如实登记**：4 条命令用了 `2>&1 \| findstr` —— ①重建前数 `[MCPServer]` 用例数；②看 `three_reds_trace.py` 的输出；③跑全仓 pytest 时只看汇总行；④看 `DECISIONS.md` 的 diff 结构。**4 条都不写任何产物**（只是把 stderr 并到 stdout 再过滤显示），交付物与证据文件一律由 Python 文件句柄、`--json`、`--out`、或工具自带的日志机制写出。另声明：`build_local.cmd` / `mcp057_build_mono.cmd` / `run_gates.ps1` / `accept_m1.ps1` **脚本内部**沿用既有台账机制（`>>` + `Start-Process -RedirectStandardOutput/-RedirectStandardError`），这是任务书 §2.1「如既有台账机制存在则沿用」所指的机制，不是我敲的重定向。 |
| **破坏性命令默认拒绝** | 只有重建（scons 覆写 `bin/`）与两个 `.cmd` 内部的**具名路径** `del /q`（既有的 `-Force` 语义）。未删除、未移动任何用户的工程/文件；未 revert 任何他人改动。 |
| **不碰游戏工程 / `.gitignore`** | 未改 `projects/**`、`projects/_exercises/**`、`.gitignore`。探针 scratch 在 `%TEMP%\task144-probe`。 |
| **命令尽量从 cmd 启动** | 所有构建、门、pytest、探针都由 cmd/pwsh 以既有命令集启动；引擎进程由 Python `subprocess` 在 `godot` 目录下启动。 |
| **唯一高位端口 / 禁第三方端点** | 本任务自己的探针只用 **9919 一个**端口（editor 端点）；门/验收用它们自己的 9888/9889；9877 只被 g04 的 guard 观察。**没有任何出站网络**（唯一网络动作是 `git push` 到项目自己的 origin，输出 `Everything up-to-date`）。**自认一处副作用**：第一次探针尝试（未加 `-e`，失败的那次）借用了 TASK-143 harness 的 `run_import()`，它**没有传 `--mcp-port`**，于是那次 `--import` 临时进程在 `127.0.0.1:9877` 上短暂监听（即编辑器默认口；当时 accept_m1 的 guard 实测 `pid_before=-1 pid_after=-1`，用户的编辑器**没有**在运行）。最终版探针给 `--import` 也传了 `--mcp-port=9919`（日志 `[MCP] listening on 127.0.0.1:9919`），不再碰 9877。 |
| **不许放宽判据** | `verify_coverage_batch.py` 只把**陈旧量**换成**现行量**并**新增**自洽护栏；没有任何通道门槛被放松（3 条真实缺证据仍判红）。引擎侧未改任何测试/断言（重建的是同一份源码）。 |
| **改引擎模块 ⇒ 走两变体重建全流程** | 本任务**未改引擎模块**；但为清 g09 仍按要求执行了完整流程（重建 → 十门 → accept_m1 → push），见 §B。 |
| **事实来源分级** | 代码优先：`tool_coverage.py` + `tool_channels.json` 是通道规则的唯一来源；本报告所有数字附命令与产物路径。 |
| **未达标项如实报** | 见 §F。 |

### D.2 文件所有权自查

| 声明独占的路径 | 本轮动作 |
|---|---|
| `tools/verify_coverage_batch.py` | **改**（判据 + import 复用 + `--channels` + 自洽护栏） |
| `tools/tests/**` | **改** `test_coverage_batch_consistency.py`（5→9 条 pytest）；未碰其余 7 个文件 |
| `recovery/work/task144/**` | **新建**（脚本、日志、中间 JSON） |
| `recovery/TEST-CASES.md` | **只更新相关行与统计**（清单见该文件 §10.5） |
| `recovery/reports/TASK-144-REPORT.md` | **新建**（本文件） |
| `recovery/tasks/TASK-144.md` | 只读，未改（也**未提交**：与 `TASK-143.md` 的既有先例一致，任务书保持未跟踪） |
| 引擎仓 `godot/` | **只重建两个二进制**（源码零改动、无新提交） |
| `DECISIONS.md`（位于仓库根 `F:\moonbit-hof-rs\DECISIONS.md`） | **未改、未 add**（原因见 §G） |

其他本轮写入（工具自身输出位置）：`runs/gates/task144/**`（门运行器的既有输出位置）。

### D.3 两仓 git（原文）

主仓（root = `F:/moonbit-hof-rs`）：

```
==MAIN-STATUS==
 M DECISIONS.md
 M godot-mcp/recovery/TEST-CASES.md
 M godot-mcp/recovery/reports/TASK-140-REPORT.md
 M godot-mcp/recovery/tasks/TEMPLATE-logic-feedback.md
 M godot-mcp/tools/playability_controls.json
 M godot-mcp/tools/playtest_player.py
 M godot-mcp/tools/tests/test_coverage_batch_consistency.py
 M godot-mcp/tools/tests/test_playability_model_player.py
 M godot-mcp/tools/verify_coverage_batch.py
?? godot-mcp/recovery/reports/ACCEPTANCE-TASK-137.md
?? godot-mcp/recovery/reports/ACCEPTANCE-TASK-141.md
?? godot-mcp/recovery/reports/TASK-142-REPORT.md
?? godot-mcp/recovery/tasks/TASK-137-ACCEPT.md
?? godot-mcp/recovery/tasks/TASK-141-ACCEPT.md
?? godot-mcp/recovery/tasks/TASK-142.md
?? godot-mcp/recovery/tasks/TASK-143.md
?? godot-mcp/recovery/tasks/TASK-144.md
?? godot-mcp/recovery/work/task144/
?? godot-mcp/tools/playtest_player_t142_prefix.py

==MAIN-LOG==
8c562d4 test(godot-mcp): TASK-143 - full use-case inventory (781 cases in 6 families) ...
1b0ccb6 TASK-140: report layout - reorder the top-level sections to 0,A..J (content unchanged)
153f73d TASK-140: report finalisation - list the batch's commits explicitly in section J.1
```

引擎仓（root = `F:/moonbit-hof-rs/godot-mcp/godot`）：

```
==ENGINE-STATUS==
?? uid_cache.bin

==ENGINE-LOG==
ba1587c71e fix(mcp_server): TASK-112 - the three engine defects TASK-111 registered are fixed at the root ...
3fdabe2d9a fix(godot-mcp): TASK-110 - editor_list_signal_connections' registered schema regains `scope` ...
1f9d0cb1c9 modules/mcp_server: task103 - REBUILT-2C-MANIFEST gains the 2c-12 section ...

==ENGINE-BRANCH==
## feature/mcp-server-module-rebuild...origin/feature/mcp-server-module-rebuild
?? uid_cache.bin
```

* `uid_cache.bin` 是**既有的**未跟踪文件（本任务开工前就存在，未提交、未删除）。
* `DECISIONS.md`、`TASK-140-REPORT.md`、`TEMPLATE-logic-feedback.md`、`playability_*.json/py`、`test_playability_model_player.py`、
  `playtest_player_t142_prefix.py`、`TASK-142*`、`ACCEPTANCE-TASK-137/141*`、`TASK-143*` **都是 TASK-142/143 的残留，未代提交、未 revert**。

---

## E. 关键产物路径 + sha256（UPPERCASE，sha256 全长）

| 路径 | bytes | sha256 |
|---|---|---|
| `tools/verify_coverage_batch.py` | 13602 | `D76FB648ACE991655C75B0025C0102EACED134F13750A841CB65F88034B9804D` |
| `tools/tests/test_coverage_batch_consistency.py` | 20659 | `F57AC96DA2F0F3937A4E0ED8A36E092B68B506D773089F4E55B560ABA540A6AE` |
| `recovery/TEST-CASES.md` | 510747 | `C7A9A7DC83524716FFFBFFBDA50C648C6AD5A42DE94DD308476244F95C62D9F0` |
| `tools/tool_channels.json`（输入，未改） | 86426 | `72A6616D98AFB614A88726C8B631947521995E05E42E49048242A664A72AAF0B` |
| `coverage.json`（输入，未改） | 582448 | `48017CD5FC2339AA4EF14D3B20955B93238CF9EEA7DD78EB18ACF7D44E47F7FA` |
| `recovery/work/task144/batch-before.json`（修前 118/48） | 83226 | `90C1D86E66483848B30B9313D63A208C69AF75296132DED5D48B4752A1FA03C7` |
| `recovery/work/task144/batch-after.json`（修后 163/3） | 106614 | `2F4F57A1DAFD95BD3F161B3EB3DCD57779EE2B2B136F8AB716BAD692C08354CD` |
| `recovery/work/task144/check_recompute.py`（177 行复算互证） | 1290 | `FE416CE0E29693DE45D029B9614D52D2E1984FD65E865739DE48CF145024C2DC` |
| `recovery/work/task144/three_reds.py` + `three_reds_trace.py`（3 条缺证据的原始 trace 取证） | 1399 / 1697 | `5A32B207BDD74F5FAF149D261B549C10678026FCBDC53927CDDD77951A2DB3BD` / `321FB472D85FD56F5B4F3028E9190EAA085BB9E025D17AF8BA93899A3ADA0DE9` |
| `recovery/work/task144/probe_u2.py`（U2 探针） | 8013 | `0E0C420453AC334098543602470D2FA1590EA622060364A0AEC75A11E8803953` |
| `recovery/work/task144/probe-u2.json`（U2 逐字响应） | 2464 | `6EA28D7C30E9A0285F21A72E3FE84D031B1B08FAA8276E7A369B1359BCEF5D75` |
| `recovery/work/task144/build-local.log` | 10504 | `3E1005A4C5BE2163E8856F51F1F9AC20A2F574E8958E27D330E16BF8BC788E05` |
| `recovery/work/task144/build-mono.log` | 10540 | `1CAA0823C9DA9CEDDCC43E877FB9E0C2AFA1D5DD56F4C3E6D8692E3858653E59` |
| `runs/gates/task144/summary.txt`（十门逐门账） | 18063 | `CFC7790E4716F998EDE16D20E7D96D68BC6B95A8044F31CA157437751D50D673` |
| `godot/bin/godot.windows.editor.x86_64.console.exe`（plain，新锚点 ba1587c71） | 300544 | `66D0DE9577B14D499FB51792C6DFB87FEDD61671FC14358178CF4FC5C6FF903F` |
| `godot/bin/godot.windows.editor.x86_64.mono.console.exe`（mono，新锚点 ba1587c71） | 300544 | `44FB0AA5BE6A8687372133002E31E939D331200CB2AF2AC20229C8916F8436AE` |

复现命令（全部 python 文件句柄/`--json` 写出，无 shell 重定向）：
`recovery/work/task144/check_recompute.py`、`three_reds.py`、`three_reds_trace.py`、`probe_u2.py`、`hashes.py`；
门：`tools\run_gates.ps1 -Tag task144 -RunGates`；批校验：见 §A.3；测试：`python -m pytest tools\tests`。

---

## F. 未达标项与遗留风险（D8，如实）

| 项 | 状态 | 说明 |
|---|---|---|
| U4/D1 前后对照 | **达成** | `118/48 → 163/3`，误红 45→0，数字与任务书一致 |
| U4/D2 负例 | **达成** | 3 条判红负例（错通道 / 快照自相矛盾 / 动词-通道矛盾），各带正向对照；写成 pytest |
| U4/D3 TEST-CASES 行 | **达成** | 只改相关行 + 统计（清单见 §A.6 与该文件 §10.5） |
| U1/D4 重建+十门+accept_m1+push+新锚点 | **达成** | 10 绿、`22/22`、`Everything up-to-date`、新锚点 `ba1587c71` |
| U1/D5 若"确非纯记账漂移"如实报 | **未触发** | 未发现任何非漂移证据；收口是真绿 |
| U2 | **已加强**（原为"如实登记"） | 两条 mouse 工具补上真跑 `-32602` 强反例；**生效证据仍缺**（台账仍 `未达(0)`，`scope_excluded`，witness_read 无从构造） |
| F1 | **保持 PIN** | 未改契约、未改 pinned 集合；留给决策者 |
| **引擎侧 `uid_cache.bin`** | **遗留** | 引擎仓的未跟踪文件（既有）；`run_gates.ps1` 的 preflight 把它算成 `WORKING_TREE_RED=1`。**本任务未删、未提交**（删除属于对他人工作树的破坏性动作，且它是引擎自己生成的缓存）。建议决策者决定：加入 `.gitignore` 或在干净树上做一次提交 —— 但改 `.gitignore` 被本任务禁止。 |
| **`edit` 前 4 条 `2>&1` 重定向** | **自认违规** | 见 §D.1，无产物写入，不影响任何交付物 |
| **probing 时的一次 9877 短暂监听** | **自认副作用** | 第一次失败的探针尝试的 `--import` 用了默认口；最终版已改为 9919。当时用户编辑器未运行（guard `pid_before=-1`） |
| **`DECISIONS.md` 未写** | **遗留（按任务书授权）** | 见 §G |
| 未提交 `recovery/tasks/TASK-144.md` | **有意** | 与 `TASK-143.md` 先例一致（任务书保持未跟踪），见 §D.2 |

**不写"应该可以"**：上面每一项要么本轮真跑出结果，要么明确写"未做/遗留"。

---

## G. 本该写进 `DECISIONS.md` 的条目（**未改它**，留给决策者）

**为什么不改**：`DECISIONS.md`（仓库根 `F:\moonbit-hof-rs\DECISIONS.md`）已被中止批次 TASK-142 改动（`git diff --stat` = **96 insertions，未提交**）。
任务书 §0 明确：**不要整体 add**；无法干净分离 ⇒ **不改它**，把内容写进报告。我判断"干净分离"需要把「别人的未提交 hunk」与「我的新增 hunk」在索引里拆开（只能用 `git apply --cached` 之类的体操），
风险与收益不成比例，且任务书已给出这条授权路径。**我也未 revert 它的任何改动。**

建议追加的条目（可直接粘贴）：

```markdown
## 2026-09-28 — TASK-144：批校验门对齐声明通道；g09 经两变体重建收口；U2 补活体反例
* 触发问题：
  (1) `tools/verify_coverage_batch.py` 仍按 TASK-118 之前的 `effective>=1` 判，对 45 个 `editor_state` 通道工具系统性误红（166 目标 118 pass / 48 fail）；
  (2) g09 红 = 锚点记账漂移（二进制自报 3fdabe2d9、引擎 HEAD ba1587c71，但二进制已含 HEAD 的 159 条 [MCPServer] 用例）；
  (3) U2 的两条 `editor_simulate_mouse_*` 无任何真实失败观察。
* 考虑的选项：
  * U4：(a) 把 `effective` 换成台账的 `channel_evidence`，但**自己重算**（否决：会与 `tool_coverage.py` 形成第二份定义）；
    (b) `--json` 里直接搬 `channel_evidence_ok` 当判据（否决：通道表与快照不一致时无法发现）；
    **(c) 选中**：`import tool_coverage`，直接调 `load_channels()` + `channel_evidence_count()`，并**新增**"快照必须能被行内计数复现"的自洽护栏。
  * U1：(a) 伪造/手改锚点串让 g09 变绿（**否决**：任务书禁止，且是伪造证据）；(b) 只登记不修（否决：任务书要求收口）；
    **(c) 选中**：按既有流程两变体串行重建 → 十门 → accept_m1 → push（实为 `Everything up-to-date`，无新提交）。
  * U2：(a) 保持"如实登记"（任务书允许）；**(b) 选中**：用"未声明参数名"探针（`tool_registry.cpp:864` 在 `handler` 之前）真跑，
    得到两条 `-32602`，且不可能注入输入事件；其余 33 个 `not_probed` 保持登记。
* 最终选择：U4 走 (c)；U1 走 (c)；U2 走 (b)；F1 保持 PIN；`DECISIONS.md` 因 TASK-142 残留**不改**（本条由报告转交）。
* 选择理由：判据定义只能有一份（代码优先、import 复用）；g09 必须真绿而不是伪锚点；
  "名探针 vs 值探针"的差别有源码级次序证据，能在**零副作用**下把 U2 从"无观察"提升为"强反例"。
* 预期影响与回滚点：U4 —— 批校验门从此与台账同源，改通道规则只需改 `tool_channels.json` + 重生成 `coverage.json`（脚本会因自洽护栏报出陈旧快照）；
  回滚点 `git revert <本批提交>`。U1 —— 两个二进制锚点从 `3fdabe2d9` 推到 `ba1587c71`，回滚需重建或 `git checkout` 旧二进制；
  引擎侧无新提交可回滚。U2 —— 新增证据只落在 `recovery/work/task144/probe-u2.json`，回滚即删除该文件与 `TEST-CASES.md` 相应两行。
```

---

_报告生成（本地）：2026-09-28；所有命令的真实输出见正文与 §E 的产物。_
