# ACCEPTANCE-TASK-119 — 独立验收：`godot-mcp` 工具覆盖里程碑（契约 177 条）

> 验收员身份：**独立验收子代理**。未参与实现，未继承实现者或调度者的任何结论。
> 本文所有数字都来自本机本轮真实命令的逐字输出；凡不能亲跑的，一律标 `unverifiable` / 推断。
> 被验收对象**未被修改**：只写了本文件；反例都在 `recovery/tmp/acceptance119/` 的**副本**上构造，
> 跑完已删除（见 §7）。`coverage.json` / `TOOL-COVERAGE.md` / `tools/*` 的 mtime 仍为验收前的
> `Sep 27 14:43 / 14:37 / 14:40`，`git status` 中无我引入的改动。

## 0. 结论

**verdict = fail（窄口径失败）**

| 声称 | 复核结果 |
|---|---|
| 契约 177 条 | ✅ 契约文件实数 177 |
| 语料 111 run / 180 trace / 8712 次调用 | ✅ 独立复算逐字一致 |
| 达标 152 / 计数达标缺证据 20 / 未达 5 | ✅ 可重算，逐字一致 |
| 档位 pixel 34 / file 24 / readback 111 / count_only 3 / no_calls 5 | ✅ 可重算，逐字一致 |
| scope-excluded 5 | ✅ 证据成立 |
| needs-an-external-device 3 | ✅ 证据成立（本机实测支持） |
| 「出现过 171 条」 | ⚠️ 与现台账不符：`coverage.json.corpus.distinct_tools = 172`（177−5） |

**判定失败的两条**：

1. **①通道声明正当性**：`tools/tool_channels.json` 里存在一条**自我矛盾、且使证据门结构性永不成立**的
   声明 —— `os_deploy_to_android_device` 被声明为 `payload`（查询类），而它的 verb 是 `deploy`，
   契约描述是「将项目导出并部署到 Android 设备」。`payload` 通道的证据计数只对读类动词累加，
   因此这条工具**无论将来真机接上、部署成功多少次，通道证据都恒为 0**。
2. **②「达标 152 逐条成立」不成立（至少一条）**：`running_game_create_input_recording` 的
   `editor_state` 证据来自 `running_game_stop_input_recording`，而后者 verb=`stop`，**不是读调用**；
   台账与文档明写该通道要求「另一次**独立读调用**」、且「写工具自己的回包不算」。

另有两条同族缺陷（见 §3）：`running_game_stop_input_recording` 的「内容级见证」被接受为
**写之前**、且**位置等于起始值**的那一次读；3 条的 `expect` 只是字段名（恒真性偏弱）。

**必须同时说清的正向结论**：台账的**统计口径与可重算性没有问题**；`payload`（计数当证据）与
`expect` 门（缺证据当通过）经反例证明**确实是活的**，不是恒真、也不是静默失效（§5）。

---

## 1. 复核方法

读入口文件：`TOOL-COVERAGE.md`、`coverage.json`、`tools/tool_coverage.py`、
`tools/tool_channels.json`、`tools/tool_coverage_unreachable.json`、
`godot/modules/mcp_server/scripts/mcp_trace_ledger.py`、`tool_registry.cpp`、
`recovery/reports/TASK-110..118-REPORT.md`、`runs/**/trace-*.jsonl`、`tools/sessions/_exercises/**/*-manifest.json`。

独立复算**不经** `tool_coverage.py`：自写解析器直接读 `runs/**/trace-*.jsonl`，按
`mcp_trace_ledger.py` 的规则重算 `(calls, ok, boundary)`、pixel/file 效果与载荷实质；
再与 `coverage.json` 逐条对。`boundary` 独立复核为 `ok=false`；`file_effect` 复核
`file_effect_status` + `file_effects[].changed`；pixel 复核 `event:"capture"` 行的 `changed`。

---

## 2. 六项核验

### ① 通道声明的正当性 —— **fail（窄）**

逐类抽查（file_effect 全 22 条、pixel_effect 全 28 条逐条读，editor_state 51 条、payload 76 条做
「契约描述 vs 声明通道」对照）：

* `file_effect`（22）—— 全部能对着契约解释：`editor_save_scene`（保存当前场景→.tscn）、
  `project_create_scene_file`（新建 .tscn）、`project_set_setting`（project.godot）、
  `project_write_text_file`（写文本文件）等。**未发现「只影响文件的工具被声明成 pixel_effect」。**
* `pixel_effect`（28）—— 抽查 `editor_add_node` / `editor_set_node_property` /
  `running_game_set_node_property` / `editor_bake_navigation_mesh`：契约都改变被渲染的编辑场景或运行帧，
  与 `ok_effect_observed` 对得上。
* `editor_state`（51）—— 抽查 `editor_set_node_selection`（编辑器选中态）、
  `editor_connect_signal`（进程内连接表）、`editor_remove_output_log`（Output 面板内存态）：
  都在进程内、都不落盘，声明可解释。
* `payload`（76）—— 抽查 `project_get_info` / `project_search_file_contents` /
  `running_game_get_scene_tree`：契约是查询，回包即测量结果，可解释。

**误声明（实证）**：

```
$ PYTHONIOENCODING=utf-8 python -c '... 扫描 declared payload 但 verb 非读类 ...'
== declared payload but verb NOT read ==
   os_deploy_to_android_device deploy 计数达标缺证据

$ python -c '... 打印该行 ...'
os_deploy_to_android_device  verb=deploy  chan=payload  calls=6 ok=0 bnd=6 chev=0
   basis: "payload：部署报告……判定依据：契约是查询：回包本身就是测量结果"
   契约描述: "将项目导出并部署到 Android 设备"
```

`channel_evidence_count()`（`tool_coverage.py:319-320`）对 `payload` 取 `st["read_payload"]`，
而 `read_payload` 只在 `verb_of(name) in READ_VERBS` 时累加（`:658-659`）→ `deploy ∉ READ_VERBS`
→ 该工具**永久** `chev=0`。`load_channels()` 只校验「覆盖契约 + 通道名合法」，**不校验通道与 verb 的一致性**，
所以这个错误能一路通过自检。

**次要**：`editor_capture_screenshot` 声明 `file_effect`，但契约写「返回 base64 PNG **或**保存到文件」，
25 次里 10 次没有文件效果（`file=15`，`eff=25`）。内联 base64 也是合法成功路径，
声明 `payload` 更贴合契约；此条属口径争议，不计为误声明。

**注**：`tool_channels.json` 的 `basis` 是**按通道套模板**（同通道 22/28/51/76 条的
「判定依据」句子逐字相同，只有 `subject` 逐条不同）。它可读，但**不是逐工具的推理**，
评审者若只读 `basis` 会以为每条都做过个案论证。

### ② 达标 152 是否逐条成立 —— **fail（至少 1 条不成立）**

抽样**超过 8 条**（含 editor_state 与 payload 通道），全部回原始 trace 手工核：

| tool | 通道 | calls | ok | bnd | 独立复算 | 结论 |
|---|---|---|---|---|---|---|
| `project_get_info` | payload | 8 | 6 | 2 | 8/6/2 ✅ | 达标（5 条实质载荷 + 1 边界） |
| `project_search_file_contents` | payload | 12 | 11 | 1 | 12/11/1 ✅ | 达标 |
| `project_create_scene_file` | file_effect | 20 | 18 | 2 | 20/18/2，file=18 ✅ | 达标 |
| `editor_save_scene` | file_effect | 123 | 123 | 0 | 123/123/0，file=77 ✅ | 计数达标缺证据（如实） |
| `editor_add_node` | pixel_effect | 36 | 31 | 5 | 36/31/5，pixel=10 ✅ | 达标 |
| `running_game_set_node_property` | pixel_effect | 49 | 47 | 2 | 49/47/2，pixel=28 ✅ | 达标 |
| `editor_set_node_selection` | editor_state | 9 | 8 | 1 | 见下 ✅ | 达标（见证可复现） |
| `editor_connect_signal` | editor_state | 45 | 38 | 7 | 见下 ✅ | 达标（见证可复现） |
| `running_game_stop_input_recording` | editor_state | 7 | 7 | 0 | 7/7/0 ✅ | 缺证据（缺边界） |

**全局更强的检查**：把 177 条工具的 `(calls, ok, boundary)` 与我的独立解析器**逐条对拍**：

```
tools compared: 177
MISMATCHES on (calls,ok,boundary): 0
independent totals calls=8712 ok=8057 failed=655
```

`editor_state` 通道另做了**全量**内容级复核（不是抽样）：把 51 条 `verified_by_tool` 的见证
调用按 `run + witness_tool + witness_seq` **回到 trace 再找一次**，核验 `ok=true`、载荷实质、
且 `expect` 字面量逐字命中（载荷被截断时按 ledger 规则读**已核验 sidecar**）：

```
witnesses re-verified at declared seq (sidecar-aware): 51 / 51
problems: 0
```

**但内容级复核暴露了规则违背**（这正是 ② 判 fail 的依据）：

```
$ python -c '... 审计 51 条：见证是否在写之后 / expect 是否只是字段名 / 见证是否读类动词 ...'
 flagged: 7 of 51
  editor_set_node_groups                <- editor_get_node_groups        seq=143 NAME_ONLY:['"ex_host"']
  editor_set_particle_material          <- editor_get_particle_info      seq=34  NAME_ONLY:['"damping_min"']
  editor_setup_navigation_agent         <- editor_get_navigation_info    seq=27  NAME_ONLY:['"max_speed"']
  running_game_create_input_recording   <- running_game_stop_input_recording seq=5 WITNESS_NOT_READ:stop
  running_game_move_player_to_target    <- running_game_get_node_properties seq=7 NAME_ONLY:['"position"']
  running_game_play_input_recording     <- running_game_get_node_properties seq=2 WITNESS_BEFORE_WRITE|NAME_ONLY
  running_game_stop_input_recording     <- running_game_get_node_properties seq=2 WITNESS_BEFORE_WRITE|NAME_ONLY
```

证据细节（原始 trace，`runs/_exercises/ex_rec/h9-task113/trace-game.jsonl`）：

```
gen1 seq=2  running_game_get_node_properties  ok=True  res={"node_path":"/root/NavRoot/Player",
            "properties":{"position":{"x":100.0,"y":300.0}},"type":"CharacterBody2D"}
gen1 seq=3  running_game_create_input_recording
gen1 seq=4  running_game_play_input_recording
gen1 seq=5  running_game_stop_input_recording
gen1 seq=18 running_game_get_node_properties ... "position":{"x":346.0,...}   <- 真正被移动后的读
```

`tools/sessions/_exercises/ex_rec/h9-manifest.json` 对 `running_game_stop_input_recording` 的声明是：
「the position read **after** the stop differs from the position read before the session」，
`expect: ["\"position\""]`。而台账接受的见证是 **seq=2（写之前）**、且值就是**起始值 100.0** ——
声明里的「differs」被它自己接受的证据否定。`expect` 只是字段名，任何 `get_node_properties` 回包都命中，
所以读取器取了**第一个**命中项，而不是能证明主张的那一项；`verify_readback()` **不检查见证调用的时序**，
也不检查见证工具的 verb 是否为读类。同一个见证被同时授予 `running_game_play_input_recording`。

对 `running_game_create_input_recording`：`editor_state` 通道、`calls=7 / bnd=1 / chev=1` → **达标**，
而它的见证是 `running_game_stop_input_recording`（verb `stop`）的**成功回包**
（`expect: ["\"event_count\":2"]`，seq=5）。字面量本身是内容级的，但见证者不是读调用 ——
与 `TOOL-COVERAGE.md` §0.1「另一次独立读调用」「写工具自己的回包不算」的明文规则相抵。

### ③ scope-excluded 5 与 needs-an-external-device 3 —— **pass**

**scope-excluded 5**（`editor_simulate_*`，`未达(0)`）：

* 独立复核这 5 条在本轮语料里**确实 0 次调用**（我的解析器里它们根本不在 `seen` 里）：
  ```
  distinct tools called: 172
  zero-call tools: 5 ['editor_simulate_key','editor_simulate_mouse_click',
                      'editor_simulate_mouse_move','editor_simulate_input_action',
                      'editor_simulate_input_sequence']
  ```
* 源码行依据成立：`godot/modules/mcp_server/tools/editor_input_simulation.cpp:53-112` 头注释逐字写明
  「they inject synthetic events into the **editor process'** own `Input` queue … they therefore
  **cannot drive a running game**」，并把依据指向 DESIGN-DETAIL §19 / GDR-21 与 **D59**
  的 TASK-012 双向线上证据（`recovery/reports/REPORT-013-b2-closure-editor-input-simulation.md` §2
  实测「编辑器变化 vs 游戏无变化」）。这是**范围决定**，不是「本循环没做」。
* 登记表 H7 的 `why_unreachable` 已把「SUPERSEDED BY MEASUREMENT」与原文并存，并新增
  `still_out`，措辞是「scope decision (D59 / GDR-21), not a missing subsystem」——**没有**把它混进
  `unreachable` 计数。**不是偷懒。**

**needs-an-external-device 3**（本机实测支持）：

```
$ which adb; echo ANDROID_HOME=$ANDROID_HOME
which: no adb in (...)
ANDROID_HOME= ANDROID_SDK_ROOT=

$ ls -la "/c/Program Files (x86)/Android/android-sdk/platform-tools/adb.exe"
-rwxr-xr-x 6641760 Apr 23 2025 .../adb.exe
$ ".../adb.exe" version
Android Debug Bridge version 1.0.41 / Version 36.0.0-13206524

$ grep -c "Android" projects/*/export_presets.cfg
（20 个正式工程×1 个预设文件，全部 0 次命中；pong 的预设只有 name="Windows Desktop"）
```

* `project_get_android_preset_info`：6 次调用**全部** `ok=false -32000 No Android export preset is
  configured in this project`（我逐行读了 `runs/_exercises/ex_grid/c7-task118/trace-editor.jsonl`
  seq=7..12），且 20 个工程的预设文件里确无 Android —— 成功路径需要外部预设，成立。
* `os_deploy_to_android_device`：6 次全部拒绝（`-32001 Export preset 'NoSuchAndroidPreset' not found`
  ×5、`-32602 'Windows Desktop' is a Windows Desktop export preset, not an Android one` ×1），
  成立（其**通道声明**另见缺陷 D1）。
* `os_list_android_devices`：**实际达标**（5 次 ok + 1 次 `-32602` 边界），回包自述
  `adb_present:false` / `source:"adb devices -l"` / `count:0`。它属于本桶是因为**设备**不在本机
  （真缺的是设备与预设，SDK 装了只是不在 PATH）—— 与 TASK-118 报告 §0.4 的说法一致。
  轻微问题：把一条**已达标**的工具与两条未达标的放进同一个「需要外部设备」栏，容易被读成「三条都不可测」。

### ④ 20 条计数达标缺证据 / 17 条缺边界 —— **pass（数字如实），但缺陷见 D4**

* 20 条的构成独立核清：**17 条 `chev≥1 且 bnd=0`**、**3 条 `bnd≥1 且 chev=0`**
  （`editor_set_auto_dismiss_dialogs` 7 次全是 `-32000 Not implemented`；
  `project_get_android_preset_info`、`os_deploy_to_android_device` 见 ③）。与声称的「17 条有通道证据但缺边界」一致。
* 17 条在本轮语料里**确实 0 次 `ok=false`**，台账没有虚报 —— 这一栏是测量事实，**不改口径也不放宽**。
* **但「缺边界」不等于「边界不可构造」，而且这一点是普遍成立的**：
  * `tool_registry.cpp:812-855` 的未声明参数门对**任何** `inputSchema.properties` 存在的工具都生效；
    17 条的契约 `inputSchema.properties` **全部是 dict**（逐条核过，`n_props` 0~5 不等）。
  * 语料本身证明**空 properties 的读工具也能拿到这种边界**：
    `editor_stop_scene` / `editor_reload_plugin` / `editor_rescan_project_filesystem` /
    `editor_remove_output_log` / `editor_remove_node_selection` / `os_list_android_devices` /
    `project_get_info` / `editor_get_audio_info` 的 `n_props=0`，却都在语料里留下
    `-32602 Unknown parameter 'bogus'` 的失败调用。
  * 我用**注入一条同形状合成拒绝调用**的反例直接验证了后果：
    ```
    M4 RESULT stop_input_recording: calls=8 bnd=1 chev=1 status=达标 witness_seq=2 expect=['"position"']
    ```
    即：给 17 条中任意一条补**一次**被拒调用，它就会达标 —— 而它骑乘的正是 §② 那条
    **写之前、值等于起始值**的「见证」。TASK-118 报告 §0 已如实披露「本轮只被授权改证据通道、
    没被授权改边界门槛」，所以我不判这一栏是隐瞒；但结论必须写清：**这 17 条的缺证据有一半是可消除的尽力问题，
    不是不可达**。

### ⑤ 作弊门：有 —— **fail（发现 3 处真口子），但主门是活的**

**构造的反例（全部在副本上，原件未动）**：

* **M1｜把计数当证据？否。** 副本 `runs/_exercises/ex_files/c1-task110` 里把 `project_get_info`
  5 条实质载荷改成 `"{}"`：
  ```
  M1 blanked project_get_info payloads: 5
  M1 RESULT project_get_info: calls=6 bnd=1 chev=0 status=计数达标缺证据    （基线是 chev=5 / 达标）
  ```
  → payload 通道的实质载荷门**真的在跑**，不是「有计数就算达标」。
* **M2｜缺证据当通过？否（正向对照）。** 副本 h9 里把见证载荷的 `"position"` 键改名 `"posn"`：
  ```
  M2 RESULT stop_input_recording: calls=7 chev=0 status=计数达标缺证据 readback=None
  rejected: none of the 5 substantive `running_game_get_node_properties` payload(s) satisfies expect '"position"'
  ```
  → `expect` 内容门**是活的**，删掉字面量就拒签、不给档位。
* **M3｜恒真断言？命中（弱）。** 副本 h9 里把**每一次**写后读的位置强改回起始值 `x=100.0`：
  ```
  M3 forced all post-write positions back to the start value: 5
  M3 RESULT stop_input_recording: chev=1 status=计数达标缺证据 witness_seq=2 expect=['"position"']
  ```
  → 与原件**完全一致**。也就是说：把「玩家确实被移动」篡改成「一步没动」，台账**不会报警**。
  配合 §② 的时序事实（被接受的见证在写**之前**、值就是 `100.0`），`expect=["\"position\""]` 是
  一个**近似恒真**的字段名断言。同族的还有 `"damping_min"`、`"max_speed"`。
* **M4｜边界门是活的 / 工具自己的响应当见证？命中。** 注入一次同形状的 `-32602` 拒绝调用：
  ```
  M4 RESULT stop_input_recording: calls=8 bnd=1 chev=1 status=达标 witness_seq=2 expect=['"position"']
  ```
  → 边界门响应真实；同时 `running_game_create_input_recording` 的达标本来就是靠
  **另一个写工具（`stop`）的响应**当见证（§②），与「写工具自己的回包不算」的规则相抵。

**未发现的作弊**：没有 `witness_tool == tool` 的自证（`rb` 里 0 条自环）；
没有「把不可达条目算进覆盖」的迹象（`members` 74 / `reclassified` 69 / `drift` 69 与 §4 分栏一致）；
`expect_absent` 分支**有被使用**（`editor_remove_animation` 等），且 19 个 manifest 里
**没有**「只声明 `expect_absent` 而不声明 `expect`」的条目 —— 代码里 `expect_matches([], text)` 会
`all([])==True` 从而失去「同一主体」锚点，这个口子目前**未被使用**，属潜在风险（R3）而非现实缺陷。

### ⑥ 可重算性 —— **pass**

用真实脚本、真实 `--root`，只把输出重定向到 scratch（不覆盖被验收工件）：

```
$ python tools/tool_coverage.py --md recovery/tmp/acceptance119/recompute.md \
                                --json recovery/tmp/acceptance119/recompute.json
tool_coverage: mode=all-runs runs=111 trace_files=180 calls=8712 distinct=172
  buckets: 0=5 1-4=0 >=5=172 | status: 达标=152 缺证据=20 未达1-4=0 未达0=5
  registry: 74 members, 69 drift

$ python -c '... 与 coverage.json 逐字段对拍 ...'
mode MATCH / corpus MATCH / buckets MATCH / status_counts MATCH
evidence_tier_counts MATCH / evidence_channel_counts MATCH / tool set MATCH
rows differing on any field: 0
readback MATCH / registry MATCH
```

唯一差异是 `generated_utc`（重跑时间）。**汇总数字与 `coverage.json` 完全一致，逐条工具行也完全一致。**

---

## 3. 缺陷

| ID | 严重度 | 内容 |
|---|---|---|
| D1 | medium | `os_deploy_to_android_device` 通道声明错误：`payload`（查询类）配 verb `deploy`（动作）。`read_payload` 只对读类动词累加 → 该工具通道证据**恒为 0**，真机接上也不会变。`load_channels()` 不校验「通道 ↔ verb」一致性，错误可静默通过自检。 |
| D2 | high | `running_game_create_input_recording`（`达标`）的 `editor_state` 见证是 `running_game_stop_input_recording` 的响应，verb=`stop`，**不是独立读调用**；与 `TOOL-COVERAGE.md` §0.1 与 `tool_coverage.py` docstring 的明文规则相抵（「写工具自己的回包不算」）。 |
| D3 | high | `verify_readback()` **不检查见证的时序**：`running_game_stop_input_recording` / `running_game_play_input_recording` 被接受的见证 `seq=2` 出现在对应写调用（seq=4/5）**之前**，且位置正是起始值 `100.0`；manifest 的 `why`（"differs from the position read before"）被自己接受的证据否定。配合 `expect=["\"position\""]`（字段名级），证据机制退化为「见证工具在该 run 里被调用过」。 |
| D4 | medium | 「17 条缺边界」是语料事实，但不是不可达：17 条的契约 schema 全部有 `properties`，未声明参数门对它们全部生效（语料里 8 个 `n_props=0` 的读工具已实证过这种边界）；M4 证明补一次拒绝调用即可达标，且会骑乘 D3 那条伪见证。台账未量化「可构造但未构造」与「结构性不可达」的差别。 |
| D5 | low | `editor_capture_screenshot` 声明 `file_effect`，但契约允许内联 base64 成功路径（25 次中 10 次无文件效果）；`payload` 更贴合契约。同类口径可讨论，未影响其状态。 |
| D6 | low | `tool_channels.json` 的 `basis` 是按通道套模板（同通道 177 条里 22/28/51/76 条逐字相同），只有 `subject` 逐条不同；读起来像逐条论证，实际不是。 |
| D7 | low | 声称「出现过 171 条」与现台账不符：`coverage.json.corpus.distinct_tools = 172`，且 `buckets[">=5"] = 172`。 |
| D8 | low | `needs_an_external_device` 把**已达标**的 `os_list_android_devices` 与两条未达标的工具同栏；台账主表里它仍是「达标」，两处表述易被误读为三条都不可测。 |

## 4. 风险

* R1：`editor_state` 是本轮**最大的一栏（51/177）**，而它的证据全部依赖人工撰写的 manifest `expect`。
  只要 `expect` 选成字段名（`"position"` / `"damping_min"` / `"max_speed"`），内容门就近似恒真。
  建议给 `expect` 加最小强度约束并检查「见证 seq 必须晚于被见证工具的调用」。
* R2：`channel_evidence` 对 `editor_state` 被硬编码为最多 1（`tool_coverage.py:322-326`），
  30 次写的工具与 6 次写的工具在这栏上不可区分；单次见证足以授予 `达标`。
* R3：`expect_absent` 单独声明时（无 `expect`）会失去「同一主体」锚点
  （`expect_matches([], text)` 恒真）。当前 0 条声明走这条路，但生成器没有禁止它。
* R4：`os_deploy_to_android_device` 的 D1 说明「通道 ↔ verb」没有交叉校验；
  今后新增工具若把动作类声明成 `payload`，会静默产生不可达的证据门。
* R5：`editor_set_auto_dismiss_dialogs` 已 7/7 全部 `-32000 Not implemented`，永远只能 `count_only`；
  它被计入「计数达标缺证据」20 条，标签与「引擎未实现」这一事实不同义。

## 5. 独立运行的检查（命令 + 关键输出）

1. 独立全量重算并逐条对拍（不 import `tool_coverage.py`）→ `MISMATCHES: 0`，`8712/8057/655`。
2. 51 条 `editor_state` 见证按 `run+witness_tool+witness_seq` 回 trace 复核（含 sidecar）→ `51/51`。
3. `python tools/tool_coverage.py --md/--json <scratch>` 重跑 → 与 `coverage.json` 逐字段一致，`rows differing: 0`。
4. 反例 M1（载荷置空）→ `project_get_info` 由 `达标` 降为 `计数达标缺证据`。
5. 反例 M2（`expect` 字面量改名）→ 声明被拒、`chev=0`。
6. 反例 M3（写后位置改回起始值）→ `chev` 仍为 1（不敏感）。
7. 反例 M4（注入一次拒绝调用）→ 由 `计数达标缺证据` 升为 `达标`。
8. 51 条见证审计（时序 / 字段名 expect / 见证 verb）→ 命中 7 条。
9. `adb` / SDK / 20 个 `export_presets.cfg` 的 Android 预设核查 → SDK 在、PATH 无、预设 0。
10. `tool_registry.cpp:800-855` 未声明参数门 + 17 条契约 schema 的 `properties` 核查 → 全部可构造边界。

## 6. 不确定项（verifiable 边界）

* 我**没有**启动 Godot 编辑器/游戏去真实调用工具，因此「某些失败是否真能被线上触发」这一步属
  **源码 + 语料推断**（推断依据已逐条给出：注册器门 + 语料中的实际出现 + M4 注入），
  不是本轮线上实测。
* `recovery/reports/TASK-110..118-REPORT.md` 中的过程数字**未被我当作证据采信**，
  本文所有结论都来自 trace / 契约 / 源码 / 我自己的反例。

## 7. 现场清理

反例与重算产物全部位于 `recovery/tmp/acceptance119/`（副本），验收结束后已 `rm -rf` 删除；
被验收对象（`coverage.json`、`TOOL-COVERAGE.md`、`tools/**`、`runs/**`、`projects/**`）未做任何写入。
