# ACCEPTANCE-TASK-147 — 独立复验：`TEST-CASES.md` 自洽性修复（blocker 是否真清）

* 验收方：独立子代理（未继承实施者/决策者结论）
* 对象：TASK-146（主提交 `03839a5`，其后 `3b36c24` / `da8b3dd` 仅改报告）
* 基准：`recovery/tasks/TASK-147-ACCEPT.md` §0（上一轮 TASK-145 的 1 blocker + 1 major + 口径偏宽）
* 时间/工作目录：`F:\moonbit-hof-rs\godot-mcp`；**只读验收**，全部自写脚本落在 `recovery/work/accept-147/**`
* 被跟踪文件 sha256（验收前后均已复算一致）：
  * `recovery/TEST-CASES.md` = `b433b0ffeb84eb3f2e2d0aa5a0da62dae05361648afc8eca57fdbf5be67e6cc0`（522467 B，1210 行）
  * `tools/tests/test_matrix_self_consistency.py` = `e800be60f7e5ef30b1adc1f61668f397a33a76305d782b8faccbdb24c12519c7`（14214 B）
  * 与实施报告 §E 登记值**逐位一致**。

---

## 0. 我做了什么（全部自己跑、自己重算）

| 编号 | 我自己的动作 | 脚本/命令 |
|---|---|---|
| A1 | 自写独立重算器（非 `task146/recount.py`），按"`\| TC-<族>-` 开头的表格行"重数六族 | `recovery/work/accept-147/recount_independent.py` |
| A2/A3 | 逐行解析全部 407 条 `TC-PY` 行，按 note 类型（pytest / script_check / printed）分别解析证据指针 `path:line`，核对 `def <名>(` 落在该行；并对全篇 890 个 `path.ext:NNN` 指针做存在性 + EOF 检查 | `resolve_pointers.py`、`cross_check.py` |
| A3' | 反向：真跑 `p7` / `model_player`，把**实际打印**的 case 名与矩阵行名做集合双向比对 | `printed_reverse.py` |
| A4 | 全篇数字扫描 + 与修前版本 `85dc5d5:…TEST-CASES.md` 对账 | `number_scan2.py`、`prefix_count.py` |
| B5 | 从**原始产物**（`coverage.json`、`probe-live.json`、`probe-u2.json`、`runs/**/trace-*.jsonl`）独立推导强/弱反例；并对 142 条活体 `-32602` 逐条做消息族划分 | `strong_weak.py`、`probe_partition.py` |
| B5' | 从契约 JSON 独立重算 §1.2 全部数字；按 `inventory.py` 的分段规则独立重算 §1.3 | `section12.py`、`section13b.py` |
| C6 | 对矩阵**内存副本**做 8 类破坏，调用被交付的检查器；再用临时 `conftest.py` 让**真 pytest** 判红 | `adversarial.py`、`pytest_red_proof.py` |
| C7 | 绕过探测：整体删一族行、删整文件行、新增外部 pytest 文件、只校合计等 | `adversarial.py`、`bypass_probe.py` |
| D9 | 抽样 12 条 `TC-TOOL` 行（≥6 要求）逐字段复核 | `sample_tctool.py` |
| D11 | `git show --name-status 03839a5` 文件清单 | `git` |

---

## 1. 逐条核验结论

### A. blocker 是否真清

**A1 — 统计 == 正文（我重算）**：**成立**。

```
file            : recovery/TEST-CASES.md   (1210 行)
  TC-TOOL       : 177
  TC-GATE       : 10
  TC-M1         : 22
  TC-ENG        : 159
  TC-PY         : 407
  TC-CONS       : 13
  TOTAL         : 788
  unmatched TC-* family rows: 0
```

与 §1.1 声明（`177/10/22/159/407/13 = 788`）**逐族逐位相等**，且被交付检查器 `declared_statistics()` 独立解析出的声明值也等于该表。TASK-145 的 blocker-1（声明 404/785 vs 正文 400/781）**已消除**。

`TC-PY` 逐文件分解（与 §6 的两级粒度一致，可交叉验证）：

| 文件 | 行数 | 其中 pytest | 其中 script_check | 其中 printed |
|---|---|---|---|---|
| `test_contract_forms.py` | 14 | 14 | – | – |
| `test_coverage_batch_consistency.py` | 9 | 9 | – | – |
| `test_matrix_self_consistency.py` | 3 | 3 | – | – |
| `test_jev_agent.py` | 33 | – | 33 | – |
| `test_playjev_agent.py` | 49 | – | 49 | – |
| `test_playability_p7.py` | 23 | – | – | 23 |
| `test_playability_model_player.py` | 276 | 4 | – | 272 |
| **合计** | **407** | **30** | **82** | **295** |

**A2 — TASK-144 的 4 条新用例有编号行、字段齐全**：**成立**。
指针/字段逐条复核（`TC-PY-*` 行；第 2 列=文件、第 3 列=测试名、第 4 列=`文件:行`、输入形式/输出形式/反例判据/现状齐备）：

| 编号行 | 指向 | 真实存在？ |
|---|---|---|
| L545 `…test_the_number_of_false_reds_is_now_zero_and_the_legacy_number_is_recorded` | `test_coverage_batch_consistency.py:286` | ✅ `def test_…(` 正在 286 |
| L546 `…test_negative_a_tool_declared_on_the_wrong_channel_is_red` | `:299` | ✅ 正在 299 |
| L547 `…test_negative_a_snapshot_that_contradicts_its_own_counters_is_red` | `:337` | ✅ 正在 337 |
| L548 `…test_negative_a_payload_channel_on_an_action_verb_is_rejected` | `:361` | ✅ 正在 361 |

**A3 — 2 条替换后的行名真实存在**：**成立**。
* L543 `test_the_batch_gate_judges_the_declared_channel` → `tools/tests/test_coverage_batch_consistency.py:254`，实测该行就是 `def test_the_batch_gate_judges_the_declared_channel():`。
* L544 `test_every_fail_is_a_real_shortage_on_its_own_channel` → `:272`，实测该行就是 `def test_every_fail_is_a_real_shortage_on_its_own_channel():`。

**全篇引用扫描**：30/30 条 pytest 行的 `path:line` 都指向该文件里真正的 `def <名>(`；82 条 `script_check` 行的名字都在对应源文件的 `checks["…"]` 键里（被交付检查器按 `["<名>"]` 解析）；全篇 **890** 个 `path.ext:NNN` 指针**无一个**指向不存在的文件或越界行；**41** 个"找不到路径"的 token 全部是裸基名/相对片段（如 `tool_registry.cpp`、`scripts/check_tautologies.py`），按"任意深度同名文件"复核**全部存在**。反向检查：`p7` 真打印 23 条 = 矩阵 23 行（双向集合相等、无重复行）；`model_player` 真打印 272 条 = 矩阵 **272 条 printed 行**（双向集合相等、无重复行，HTML 转义差异已归一）。

**A4 — stale 是否清干**：**成立**。
* 现行文件里 **没有任何**"23 passed"作为活引用；仅 2 处出现在**变更记录**（L7 的四项更正、L1197 的 E4 行）里，语境都是 `"23 passed" → 30 passed`，属历史引述，不是声明。
* 与修前 `85dc5d5` 版本对账：修前全文 `23 passed` **25 处** = §6 的 23 个 TC-PY 行 + §9.2 一行 + §10.3 一行 —— 与 §10.6 E4 的表述**逐项吻合**；修前全文 `27 passed` 1 处（§8.1 行）也在 §10.6 中列明。
* 实测值与 §8.1 一致：我跑的 `python -m pytest tools/tests -q --no-header -p no:cacheprovider` → **`30 passed in 2.13s`**（exit 0），与 §8.1 L962 的 `30 passed` 同值；§0.1 L21 "pytest 收集 30 条" 同值。未发现任何活引用仍写着 `27 passed`。

### B. 口径与反例强度

**B5 — 175/177 强 + 2 弱**：**成立（我独立推导）**。
我不是读矩阵，而是从原始产物推导：判"强反例"= ①`runs/**/trace-*.jsonl` 里该工具有 `ok=false` 的真实失败调用（我扫了 **17664** 行 trace，**172** 个工具有失败调用），或 ②TASK-143 活体探针以 handler 侧消息拒了它（`Missing required parameter:` / `Parameter '…' must be`），或 ③台账 `boundary>=1`。三者并集 = **175**；剩余**恰好 2 个**：`editor_simulate_mouse_click`、`editor_simulate_mouse_move`——与 §1.2/§1.4 的"缺强反例 2/177"**完全一致**。这 2 个同时有 u2 参数门探针 + 一条"仅提及"的引擎用例，故属**弱**反例，§1.2 对抗性结论段与 §9.3 U2 的定性正确。

**§2 两条 `editor_simulate_*` 是否标 weak**：**成立**。L199/L200 两行反例判据格里逐字写着 `**强度=weak（参数门反例，不是该工具的行为反例）**`，并注明发出点与 `handler` 的先后关系。

**代码一致性（逐处文件:行，我自己打开文件核过）**：

| 文档主张 | 我的实测 | 结论 |
|---|---|---|
| `require_string()` / `require_int()` 在 `godot/modules/mcp_server/tools/tool_builder.cpp:207-232` | `bool require_string(` 在 **:207**；`:214` 抛 `Parameter '%s' must be %s, got %s`（经 `_type_error_message`，定义 :169）；`bool require_int(` 在 **:221**；`:228` 抛同型消息 | ✅ 区间与语义都对 |
| 2 条 `editor_simulate_*` 的拒绝在 `tool_registry.cpp:864` | `static bool _reject_unknown_arguments(` 定义 **:812**；`call_tool()` 里 `if (!_reject_unknown_arguments(*def, p_args, r_error))` 在 **:864**；`const Variant result = def->handler(p_args, r_error);` 在 **:880** | ✅ 864 在 880 之前，成立 |
| `probe-u2.json` 逐字自述 `undeclared_argument_name … before any handler runs` | 文件里确有该字段；两工具的 `request_arguments` 只含 `mcp144_undeclared_probe`，`verdict=refused_-32602`，消息 `Unknown parameter '…' for tool '…'` | ✅ |

### C. 自洽校验测试的有效性（对抗性）

**C6 — 真判红 + 恢复后逐位未变**：**成立**。
我在**内存副本**上做了 8 类破坏（矩阵文件本身一个字节都没写），被交付的检查器全部真报错：

| 破坏 | 结果 |
|---|---|
| §1.1 合计 788→789 | `check_statistics` 报 `TOTAL: section 1.1 says 789, the body has 788 row(s)` |
| 删 1 条 TC-PY 行 | 统计报 407/406 + 788/787；引用报 `test_contract_forms.py: 14 def test_* but 13 pytest rows` |
| 把一行 pytest 名改成不存在的测试 | 引用报 `line 526: no 'def test_task146_deliberately_missing(' in …` |
| 只把 `TC-ENG-NNN` 159→158 | 统计报 `TC-ENG-*: section 1.1 says 158, the body has 159 numbered row(s)` |
| 改一条 p7 printed 行名 | 引用报 `line 861: 'no such printed case declared items present and on screen' is not printed by …` |
| 合计 +7（不动各族） | 统计报 795/788 |
| 删掉全部 3 条自洽测试行 | 统计报 404/785（**引用检查器不报**，见 C7） |
| 删掉 5 个族的声明行 | 统计报 5 条 `section 1.1 declares no TC-* row` |

**真 pytest 判红**：临时 `tools/tests/conftest.py`（仅把 `read_matrix()` 换成"合计+1 的副本"，**未动被测文件**）→

```
F.F                                                                      [100%]
FAILED tools/tests/test_matrix_self_consistency.py::test_the_matrix_section_1_1_statistics_equal_its_own_rows
FAILED tools/tests/test_matrix_self_consistency.py::test_the_matrix_checker_goes_red_on_a_deliberately_inconsistent_matrix
2 failed, 1 passed in 1.17s        exit code: 1
```

随后**恢复到干净态**：删除临时 `conftest.py`，重跑得到 `3 passed`；被跟踪文件 sha256 **前后逐位相同**：
`recovery/TEST-CASES.md` `b433b0ff…e6cc0` → `b433b0ff…e6cc0`；`tools/tests/test_matrix_self_consistency.py` `e800be60…19c7` → `e800be60…19c7`。工作树 `git status --short` 里本任务只多出 `recovery/work/accept-147/`，无残留。

**C7 — 能否被绕过**：**部分能被绕过，已点名（缺陷 X2/X3）**。
* ✅ **不是**"只比一个家族"：`FAMILIES` 六族全比、逐族比 + 合计比，而且"缺声明行"也会报错。
* ✅ **不是**"只校合计不校逐族"：逐族独立比对，我上面"只改一族"的破坏被点名。
* ✅ **printed 类没被漏掉**：`kind_of()` 认 `自打印的 case 名`，p7/model_player 各自真跑取名字再逐个比对（我的破坏命中）。
* ❌ **可绕过 1（X2）**：引用检查器只遍历**矩阵里已有行的文件**（`rows → by_src`）。把某个 pytest 文件的**全部行**删掉，`check_references` **零抱怨**（我实测：删掉 3 条自洽测试行 → `check_references` 返回 `[]`）。此时只有"统计"侧能发现行数变化。
* ❌ **可绕过 2（X3，更重）**：矩阵里**完全没有行**的 pytest 文件根本不在遍历范围内。我**临时新建** `tools/tests/test_accept147_bypass_probe.py`（含 1 条 `def test_…`）后，`check_statistics` 与 `check_references` **双双返回 `[]`**（全绿），而真实 pytest 会多收集 1 条。即"新增一个没有矩阵行的测试文件"这一类失效**不会被拦**。探测完成后文件已删除，两个被跟踪文件 sha256 仍未变。
* ❌ **可绕过 3（X4）**：反向不成立——矩阵里有行、但**真打印结果里缺该条**是被检查的；反过来"真打印有、矩阵缺行"只在 printed 侧被顺带覆盖（我实测 p7 23=23、model_player 272=272 恰好齐全），但检查器没有"printed 总数 == 文件自报总数"的独立计数锚（它靠 `code != 0 or not names` 兜底）。

### D. 全局回归与诚实性

**D8 — 自己跑 pytest**：**成立**。原始命令与输出：

```
$ python -m pytest tools/tests -q --no-header -p no:cacheprovider
..............................                                           [100%]
30 passed in 2.13s            (exit 0)

$ python -m pytest tools/tests
============================= 30 passed in 2.08s ==============================  (exit 0)
```

通过 **30** / 失败 **0** / 跳过 **0**，与报告称的 30 passed 一致。`test_matrix_self_consistency.py` 单跑 `3 passed`。

**D9 — 抽样 ≥6 条 TC-TOOL 行**：**成立**。我抽了 **12** 条（`project_get_info`、`project_get_filesystem_tree`、`project_search_file_names`、`project_set_setting`、`editor_open_scene`、`editor_add_scene_instance`、`editor_stop_scene`、`editor_rename_node`、`editor_set_node_property`、`editor_capture_screenshot`、`editor_execute_gdscript`、`editor_simulate_mouse_click`/`_move`），逐条重算四件事：契约 `properties/required/optional/default` 计数、`tools/tool_channels.json:<行>` 指向的声明通道、`coverage.json` 的 `boundary` 与 `evidence_tier`、反例指针 `runs/…jsonl:<行>` 的实际 `error_code` 与消息片段。**problems: 0**——12/12 全对（`editor_simulate_mouse_*` 的 `回读=state/no_calls` 与声明通道 `editor_state` + 台账 `no_calls` 亦吻合）。

**D10 — 报告 §F/§H 与自认的 2 条重定向违规**：**属实**。
* §D 表格逐字承认 **2 条** shell 重定向（`… --collect-only -q 2>&1 | findstr`、`dir /s /b … 2>nul`），并说明都不写产物；§F.1 再次登记。这 2 条与 TASK-143/144 的先例口径一致，**不影响任何产物**（我复算的两个 sha256 与 §E 登记值逐位相同）。
* §F 其余项逐条可核：F.2（`DECISIONS.md` 有他人未提交改动 ⇒ 不落盘）、F.3/F.4（解析器 3+1 处口径 bug 及修法，与我读到的实现一致）、F.5（新增 3 条使 27→30，连带 §0.1/§1.1/§6/§8.1 必须同动）、F.6（`TASK-146.md` 按先例未提交——我确认它仍是 `??`）、F.7（明确声明未重审其它族逐行内容，未重算 169/8/94/83 之外的 §1.3）。
* §H 决策条目完整（触发问题/3 选项含否决理由/最终选择/理由/回滚点/未落盘原因），内容与我复核到的事实一致。

**D11 — `03839a5` 文件清单**：**成立**。

```
M godot-mcp/recovery/TEST-CASES.md
A godot-mcp/recovery/reports/TASK-146-REPORT.md
A godot-mcp/recovery/work/task146/hashes.py
A godot-mcp/recovery/work/task146/probe_names.py
A godot-mcp/recovery/work/task146/py_rows.py
A godot-mcp/recovery/work/task146/recount.py
A godot-mcp/recovery/work/task146/red-proof.json
A godot-mcp/recovery/work/task146/red_proof.py
A godot-mcp/tools/tests/test_matrix_self_consistency.py
9 files changed, 1256 insertions(+), 39 deletions(-)
```

**全部属于 TASK-146 自己声明独占的路径**；**没有**替他人提交 `DECISIONS.md`、`recovery/reports/TASK-140-REPORT.md`、`recovery/tasks/TEMPLATE-logic-feedback.md`、`tools/playability_controls.json`、`tools/playtest_player.py`、`tools/tests/test_playability_model_player.py`、`tools/playtest_player_t142_prefix.py`；**无删除项**（没有 revert 任何东西）。上述他人改动在我验收时的 `git status --short` 里仍以 ` M`/`??` 原样存在。

---

## 2. 我额外独立复算到的旁证（不属判据，用于判断"是否修一处坏一处"）

| 数字 | 矩阵 | 我的独立复算 | 结论 |
|---|---|---|---|
| 契约工具 / channels / 台账 名单 | 177 / 177 / 177 | 177 / 177 / 177，两两对称差 **0** | ✅ |
| 声明 properties 的工具 | 159 | **159** | ✅ |
| required+optional 兼有 | 70 | **70** | ✅ |
| properties 为空 | 18 | **18** | ✅ |
| 声明默认值 | 75 | **75** | ✅ |
| 声明 enum | 4 | **4** | ✅ |
| 引擎用例派生覆盖（非法/边界/错误码+消息/副作用/幂等） | 114/114/67/83/34 | 按 `inventory.py` 同规则独立复算 **114/114/67/83/34** | ✅ |
| `channel_evidence_ok=false` 的工具 | 8 | **8**，且名单与 §1.4 逐名相同 | ✅ |
| 台账状态 | 169 达标 / 3 计数达标缺证据 / 5 未达 | **完全相同** | ✅ |
| 语料 | 182 trace / 112 run / 8729 calls / 172 distinct | **完全相同** | ✅ |
| 活体 `-32602` 的工具 | 144 | 142（task143）+ 2（task144 u2）= **144** | ✅ |

---

## 3. 缺陷与判定

**未发现 blocker**：统计与正文六族 + 合计逐位相符；无失效引用；关键数字（407/788/175+2/30 passed/144）**都可复现**；自洽测试**不是形同虚设**（真判红、恢复后逐位未变）。

**major**

* **Y1 — 子计数不可复现**：`TEST-CASES.md` §1.2 对抗性结论段（L86）与 §9.3 U2（L1125）写"活的 `-32602` 里有 **121 条 `missing_required`** + **21 条 `wrong_type`**"。我从 `recovery/work/task143/probe-live.json` 自写脚本逐条划分那 142 条 `refused_-32602`，实测是 **119** 条消息形如 `Missing required parameter: <k>`（来自 `tool_builder.cpp` 的 `require_string/require_int`）+ **21** 条 `Parameter '…' must be …, got …` + **2** 条 `Missing required parameter '<k>'`（**无冒号**）：`editor_set_auto_dismiss_dialogs`（发出点 `tools/editor_node_write.cpp:1040`）与 `editor_set_node_property_updates`（发出点 `tools/editor_node_property_updates.cpp:435`）。119+21+2=142。**报告数字拆不开 142**（121+21=142 但 121 不存在）。该段"这些是 handler 行为反例、2 条 simulate 只到参数门"的**定性结论不受影响**（那 2 条确在 handler 内、确非注册器门），受影响的只是这一处被当作精确证据的子计数；§1.2/§1.4 承重的 `175/177 + 2 弱` 不依赖它。

**minor**

* **X2 — 引用检查器对"整体删行"无感**：删掉某 pytest 文件的**全部** TC-PY 行时，`check_references()` 返回 `[]`（只遍历已有行的文件）。此时靠统计侧兜底。
* **X3 — 新增无矩阵行的 pytest 文件完全逃逸**：临时新建 `tools/tests/test_accept147_bypass_probe.py` 后两个检查器**双双全绿**。这是唯一一类"加了测试不补行"的漏洞，正是该测试声称要防的场景（上述两个探测文件均已删除，被跟踪文件 sha256 未变）。
* **X4 — printed 侧无独立计数锚**：只有"矩阵行 → 真打印集合"方向被检查；"真打印 → 矩阵行"方向未检查（实测恰好齐全：23=23、272=272），故不构成当下错误，只构成再犯风险。
* **X5 — §0.1 的 `model_player 272` 标签不精确**：该文件贡献 **276** 条 TC-PY 行（**4** 条 pytest + **272** 条 printed）；写成"model_player 272"容易被读成"该文件的 pytest 行数"。合计 407 本身正确。
* **X6 — §10.6 E4 的"25 处"与修后实际不符**：E4 写 `§6 的 23 个 TC-PY 行 + §9.2 一行 + §10.3 一行` = 25；修后实际含 "30 passed" 的 TC-PY 行是 **27**（23 条旧行 + 本轮新增的 **4** 条 TC-PY 行），加 §9.2 一行、§10.3 一行共 **29**。行为本身（全部改成 30 passed、且无 `27 passed` 残留）是对的，只是变更清单的计数写成 25（还要注意 E4 自己就落在"非 TC-PY 的 30 passed 行"里）。另：L7 与 §1.1 注里"**唯一来源**"的表述在字面上不严格——全文另有 §0.1 L21、§9.2 L1084/1085、§10.3 L1161 也各出现一次 `30 passed`（同值同源，不冲突）。

**risks**

* 自洽测试只在 **pytest 层**把关，而 pytest 又要靠人主动跑；`tools/tests` 一旦被误删或有新文件未纳入矩阵，X3 的盲区就会静默存在。建议后续给 `check_references()` 增加一个"`tools/tests/test_*.py` 的 `def test_*` 全集"锚（不要只遍历矩阵已有行）。
* §1.2/§1.3 的派生数字本轮已复核一致，但它们的生成器/检查器仍在 `recovery/work/task143/` 之外（`analyze.py` 是 ad-hoc 脚本）；派生格仍是关键词命中，不等于证明（§0.3 已如实声明）。
* Y1 这类"引一手产物时的加法口误"没有机器守卫；建议把 `142 = 119+21+2` 的划分也写进一个可执行断言。

**unverifiable**

* 无法从仓库文件独立复现实施方在 §C.1 里贴的**三次判红**原始输出（那要求跑出 `red-proof.json` 的生成环境）；但我用**自己的**等价破坏（8 类 + 真 pytest 2 failed）独立复现了"真判红 + 恢复后 sha256 逐位未变"这一判据本身。
* `probe-u2.json` / `probe-live.json` 是在**当时**的引擎进程里真跑出来的；我未重启引擎重跑探针（会违反"只读验收/不碰引擎"约束），只对该 JSON 的**内部一致性**与消息族划分做了复核。
* 实施报告 §G.3 声明"引用 TASK-145 已复现为真绿的部分未重做"（163/3、g09、accept_m1 22/22、十道门等）；这些超出本任务书 §1 的核验范围，我**未重跑**，故本报告的 pass 不覆盖它们。

---

## 4. 结构化输出

```json
{
  "verdict": "pass",
  "criteria": [
    {"id": "A1", "pass": true, "evidence": "自写独立重算器 recovery/work/accept-147/recount_independent.py 从正文重数：TC-TOOL 177 / TC-GATE 10 / TC-M1 22 / TC-ENG 159 / TC-PY 407 / TC-CONS 13 = 788，与 §1.1 声明逐族逐位相等；未匹配族行 0"},
    {"id": "A2", "pass": true, "evidence": "TC-PY 行 L545/L546/L547/L548 分别指向 test_coverage_batch_consistency.py:286/299/337/361，均经我核对为真正的 `def test_<名>(` 行；输入形式/输出形式/反例判据/现状字段齐备"},
    {"id": "A3", "pass": true, "evidence": "L543→:254 `def test_the_batch_gate_judges_the_declared_channel(`、L544→:272 `def test_every_fail_is_a_real_shortage_on_its_own_channel(` 实测存在；全篇 890 个 path:line 指针零失效；30/30 pytest 行、82/82 script_check 行均可解析；反向比对 p7 23=23、model_player 272=272 双向集合相等"},
    {"id": "A4", "pass": true, "evidence": "现行文件无活的 '23 passed'（仅 2 处变更记录语境）；我自跑 `python -m pytest tools/tests -q --no-header -p no:cacheprovider` = 30 passed（exit 0），与 §8.1 L962、§0.1 L21 同值；修前 85dc5d5 版本 '23 passed' 25 处 = 23 TC-PY 行 + §9.2 一行 + §10.3 一行，与 §10.6 E4 吻合"},
    {"id": "B5a", "pass": true, "evidence": "从原始产物独立推导（扫 runs/**/trace-*.jsonl 共 17664 行、172 工具有真实失败调用；probe-live.json handler 侧 -32602；coverage.json boundary>=1）三路并集 = 175/177，剩余恰好 2 个 = editor_simulate_mouse_click / editor_simulate_mouse_move，与 §1.2/§1.4 的 2/177 一致；L199/L200 两行逐字标注 `强度=weak`"},
    {"id": "B5b", "pass": true, "evidence": "代码路径逐处核对：tool_builder.cpp:207 `bool require_string(`、:214 抛 `Parameter '..' must be ..`、:221 `bool require_int(`、:228 同型；tool_registry.cpp:812 `_reject_unknown_arguments` 定义、:864 调用、:880 `def->handler(...)`——864 在 880 之前；probe-u2.json 逐字 `undeclared_argument_name … before any handler runs`"},
    {"id": "C6", "pass": true, "evidence": "对内存副本做 8 类破坏全部真判红（合计+1、删行、改指向不存在测试名、只改一族、改 p7 printed 名、合计+7、删 3 条自洽行、删 5 族声明行）；临 conftest.py 让真 pytest 报 `2 failed, 1 passed` + `AssertionError: TOTAL: section 1.1 says 789, the body has 788 row(s)`；恢复后 TEST-CASES.md sha256 b433b0ff…e6cc0 与 test_matrix_self_consistency.py e800be60…19c7 前后逐位相同，临时文件已删"},
    {"id": "C7", "pass": true, "evidence": "六族全比、逐族+合计都校、printed 类纳入检查（破坏命中）⇒ 不存在任务书举例的三种绕过形态；但确实存在另外两类盲区：删掉某文件全部行时 check_references 返回 []，临时新建无矩阵行的 pytest 文件（tools/tests/test_accept147_bypass_probe.py，含 1 个 def test_）时两个检查器双双全绿——已记为 X2/X3 缺陷，探测文件已删除、被跟踪文件 sha256 未变"},
    {"id": "D8", "pass": true, "evidence": "自跑 `python -m pytest tools/tests -q --no-header -p no:cacheprovider` → `30 passed in 2.13s` exit 0；`python -m pytest tools/tests` → `30 passed in 2.08s`；通过 30 / 失败 0 / 跳过 0"},
    {"id": "D9", "pass": true, "evidence": "抽样 12 条 TC-TOOL 行（重算 work/accept-147/sample_tctool.py，problems=0）：契约 properties/required/optional/default 计数、tool_channels.json:<行> 声明通道、coverage.json boundary+tier、runs/…jsonl:<行> 的 error_code 与消息片段全部吻合"},
    {"id": "D10", "pass": true, "evidence": "报告 §D 与 §F.1 逐字自认 2 条 shell 重定向（--collect-only 2>&1 | findstr、dir /s /b … 2>nul），均不写产物；§F.2/F.5/F.6/F.7 逐条可核（DECISIONS.md 仍有他人 ` M`、TASK-146.md 仍为 `??`）；§H 决策条目含选项与回滚点；§E 登记的两个 sha256 与我复算值逐位相同"},
    {"id": "D11", "pass": true, "evidence": "`git show --name-status 03839a5` = 9 个文件（TEST-CASES.md、TASK-146-REPORT.md、work/task146/ 6 个、tools/tests/test_matrix_self_consistency.py），9 files changed / 1256 insertions / 39 deletions；未包含 DECISIONS.md、TASK-140-REPORT.md、playability_*、playtest_player*.py 等他人改动；无删除项"}
  ],
  "defects": [
    {"what": "§1.2 L86 与 §9.3 U2 L1125 写“121 条 missing_required + 21 条 wrong_type”，与一手产物不符", "severity": "major", "evidence": "recovery/work/task143/probe-live.json 的 142 条 refused_-32602 实测划分为 119 条 `Missing required parameter: <k>`（tool_builder.cpp:207-232 的 require_string/require_int）+ 21 条 `Parameter '…' must be …, got …` + 2 条无冒号的 `Missing required parameter '<k>'`（editor_set_auto_dismiss_dialogs 出自 tools/editor_node_write.cpp:1040；editor_set_node_property_updates 出自 tools/editor_node_property_updates.cpp:435）；119+21+2=142，而 121+21=142 中的 121 不存在。复算脚本 recovery/work/accept-147/probe_partition.py 与 strong_weak.py。定性结论（属 handler 行为反例、2 条 simulate 只到参数门）不受影响，§1.2/§1.4 的 175/177 + 2 弱不依赖该数字"},
    {"what": "自洽检查器的引用侧只遍历“矩阵里已有行的文件”，整体删行不会被发现（X2）", "severity": "minor", "evidence": "把 test_matrix_self_consistency.py 的 3 条 TC-PY 行全部删除后，check_references(mut) == []（recovery/work/accept-147/adversarial.py break 7b），只有 check_statistics 报 407/404 与 788/785"},
    {"what": "矩阵里完全没有行的 pytest 文件不在校验范围内，新增测试文件可不补行而全绿（X3）", "severity": "minor", "evidence": "临时创建 tools/tests/test_accept147_bypass_probe.py（含 def test_a_brand_new_suite_nobody_added_to_the_matrix）后，check_statistics 与 check_references 双双返回 []（recovery/work/accept-147/bypass_probe.py）；这正是该文件 docstring 声称要防的“加了测试不补行”。探测文件已删除，两个被跟踪文件 sha256 未变"},
    {"what": "printed 类用例只有“矩阵行→真打印”单向校验，无独立总数锚（X4）", "severity": "minor", "evidence": "check_references 依赖 rows 驱动；printed 的完整性只体现在统计侧行数。实测 p7 23=23、model_player 272=272 且无重复行（recovery/work/accept-147/printed_reverse.py），故当前不构成错误，仅构成再犯风险"},
    {"what": "§0.1 L21 把 test_playability_model_player.py 的贡献写成“model_player 272”，实为 276 条 TC-PY 行（4 pytest + 272 printed）", "severity": "minor", "evidence": "recovery/work/accept-147/cross_check.py 逐文件统计：test_playability_model_player.py = 276，其中 pytest 4 / printed 272；合计 407 正确"},
    {"what": "§10.6 E4 的“25 处”与修后实际不符（应为 29 处：27 条 TC-PY 行 + §9.2 一行 + §10.3 一行）；L7 与 §1.1 注的“唯一来源”表述字面不严格", "severity": "minor", "evidence": "修后含 '30 passed' 的 TC-PY 行 27 条（recovery/work/accept-147/number_scan2.py），非行处另有 §0.1 L21、§9.2 L1084/L1085、§10.3 L1161、§10.6 L1197 共 5 处；修前 85dc5d5 为 23+2=25（prefix_count.py），与 E4 所述一致，即 25 是修前基数、修后写成 25 未加新增的 4 行"}
  ],
  "risks": [
    "把关机制只在 pytest 层，且需要人主动跑；X2/X3 盲区意味着“新增测试文件不补行”仍可静默逃逸，建议给 check_references 增加 tools/tests/test_*.py 的 def test_* 全集锚",
    "§1.2/§1.3 仍是关键词派生数字（§0.3 已如实声明为派生下限），其生成脚本在 recovery/work/task143/ 之外、无 pytest 守卫，Y1 这类口误不会被机器发现",
    "本质检 pass 只覆盖 TASK-147-ACCEPT §1 的 A–D；实施报告 §G.3 声明“未重做”的 TASK-145 已验部分（163/3、g09、accept_m1 22/22、十道门、两变体重建）不在本报告覆盖内"
  ],
  "unverifiable": [
    "实施方 §C.1 的三次判红原始输出（red-proof.json 的生成环境）无法从仓库独立复现；我另行用自己的等价破坏复现了同一判据",
    "probe-live.json / probe-u2.json 是当时引擎进程的真跑产物，我按只读验收约束未重启引擎重跑探针，只核其内部一致性与代码路径对应关系",
    "TASK-145 已复现为真绿的收口项（verify_coverage_batch 163/3、g09 ANCHOR_EQUAL、accept_m1 22/22、十道门 exit=0）本轮未重跑"
  ]
}
```
