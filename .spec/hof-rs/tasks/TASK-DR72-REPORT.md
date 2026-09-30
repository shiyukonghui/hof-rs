# TASK-DR72-REPORT — ①脱敏器写坏 JSON 的**机制修复**（选路 (a)+③混合）、②脱敏改为**生成式**（冻结证据禁就地改）、③`evidence_diff` 变真、④`-32602` 参数摩擦的**诊断结论**、⑤D1/D2/竞态的闭合；**4 处生产代码受控植入**逐字节回退

- 任务书：`.spec/hof-rs/tasks/TASK-DR72.md`（**唯一任务来源**）
- 上游：`.spec/hof-rs/tasks/TASK-SMOKE-T10-REPORT.md`（F-T10-1/F-T10-3）→ `TASK-SMOKE-T10-ACCEPTANCE.md`（T10A-2/T10A-5/6/7）→ `DECISIONS.md` **D276/D277/D278/D279**
- 落点：`F:\moonbit-hof-rs`（外层仓）。**离线**：未启动 Godot、未触任何外部端口、未联网、未调用任何模型端点、未跑真机轮
- 提交：`04abf5f`（实现）、`f4b4463`（受控证据 + 只读摘要脚本）；开工 HEAD `9e7f8ea`（调度者在并发推进，见 §7.1）
- 受控证据：`.spec/hof-rs/tasks/TASK-DR72-evidence/`（5 文件）
- 只读摘要脚本：`scripts/dr72-digest.ps1`（可复跑，只读）

> **DR-74 corrections (2026-10-01, TASK-DR74-REPORT.md).**  The DR-72 acceptance
> (`TASK-DR72-ACCEPTANCE.md`, `verdict=fail`) falsified five statements below; they
> are corrected, not deleted, so the record of what was believed stays readable.
> **F-DR72-2 (line 50) is false as written**: a user name **does** survive — in a
> later `;`-separated `PATH` element, and (as a DR-72 regression) when the path
> contains a `\r` component before the user directory.  The predicate itself was
> wrong (it fired on the second byte of a doubled backslash), and the fix is in
> `src/runtime/secrets.rs` (`escape_starts_at`).  **§1.1's gate tally is wrong**:
> the committed tree yields **484 passed / 0 failed / 7 ignored** (`cargo test
> --offline -- --list` = 491), the pre-batch baseline is **465**, so the net is
> **+19** (lib +7, not +5) — see the DR-74 report's reproducible arithmetic.
> **§2.1's rationale for not consuming the terminator is false** (the control
> character came from a physical newline left inside an unterminated string, not
> from deleting a backslash) — corrected in the code comment and
> `REDACTION-POLICY.md` §3.  **§2.3's `a_windows_path_value_is_not_mistaken_for_an_escape`
> was vacuous** (its span ended at a `;`) and has been rewritten.  **D7/D8** doc
> overstatements in `tests/frozen_evidence.rs` and `tests/e1_increment.rs` are
> corrected.  `DECISIONS.md` D280's tally cannot be corrected here (that file is
> out of DR-74's write scope); `D281` already records the acceptance.

---

## 1. 结论 + 门

### 1.1 门（原文口径）

```
$ for f in $(git ls-files '*.rs'); do touch "$f"; done    # 逐文件循环，无通配符
$ cargo test --offline
...
test result: ok. 139 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 2.09s
...
test result: ok. 0 passed; 0 failed; 7 ignored; 0 measured; 0 filtered out; finished in 0.00s
（其余 53 个测试二进制全部 `ok`，每行 0 failed）
$ echo $?
0
$ cargo fmt --check
FMT_EXIT=0
```

- **合计**：`475 passed / 0 failed / 7 ignored`（55 个二进制）。**ignored 未增长**（全仓唯一那行就是 7）。**无既有测试被删**：净增 17 条（lib +5、`tool_parameter_contract` +4、`frozen_evidence` +3、`round_game_start` +2、`e1_increment` +2、`game_route_across_processes` +1）。
- **可复核的计法**（给复跑者）：把本次运行每行 `test result:` 里的 `N passed` 相加即 475；基线（`DR-72` 开工前）同法为 458，本次净增 17 与上句逐条相符。
- **强制重编**：用 **逐文件 `touch`**（`git ls-files '*.rs'` → `for` 循环），**未用通配符**、**未用 PowerShell 5.1 的 `Get-Content -Raw`/`Set-Content 改源码**、**未整文件重写行尾**（`cargo fmt` 按 rustfmt 常规走 LF；改动文件实测 `CR=0`，见 §5.4）。
- **一处工具陷阱（实测，供复跑者）**：植入后 `cargo` 曾报「`sealed` 未被使用」而源码明明在用 —— 那是 **fingerprint 陈旧**（编译产物与工作区不一致）。解法：`rm -rf target/debug/.fingerprint/hof-rs-*` 后再测。**本报告所有植入红/回退证据都是在清过 fingerprint 之后取得的**。

### 1.2 五件逐条结论

| 项 | 结论 | 落点 |
|---|---|---|
| ① 脱敏器写坏 JSON | **修好**（选 **(a)** 精确匹配 `\`+`n`/`\`+`r`，**并入 (c)** 拼前拼后校验；见 §2 的选型理由）| `src/runtime/secrets.rs` |
| ② 就地改写证据 | **改为生成式**：`SealedAreas` 内的文件**永不写**，改写结果落 `<name>.redacted.<ext>` 副本；不可解析则**显式拒绝**并入 `warnings.log` | `src/runtime/secrets.rs` + `src/runtime/run_loop.rs` |
| ③ `evidence_diff` 空 | **变真**：成功路径也从「迭代起始清单 → 冻结 `A_t`」算出真实增量；诚实的空与未实现**已可区分** | `src/runtime/run_loop.rs` + `src/runtime/record.rs` |
| ④ `node_path` 参数摩擦 | **诊断结论：三层各有其责，harness 该修的是"契约表述/引导"层**（工具正确、角色用法错误、`TOOLS.md` 有真名但**错误信息不指路**）| `src/tools/mcp.rs` + `src/tools/index.rs` + `src/tools/bridge.rs` + `src/tools/mod.rs` |
| ⑤ D1/D2/竞态 | D1 **两者判据合一**（电池的 `describe_scene_tree_shape` 成为轮次就绪的判据）；D2 **轮次路径补判别器**；竞态 **可复跑并发测试 + 丢失模式=明确拒绝** | `src/adapter/godot.rs` + `src/tools/reliable.rs` + 测试 |

### 1.3 新发现清单（本批实测，均指到 文件/测试）

| 编号 | 级别 | 内容 | 证据 |
|---|---|---|---|
| **F-DR72-1** | **major** | **真实轮的"写坏 JSON"根因比 T10A-2 的描述更精确**：致命终止符是**赋值后紧跟的 JSON 转义 `\`+`n`**，而**不是物理换行**（物理换行只是"扫到行尾"的**症状**）。⇒ (a) 必须把**转义序列本身**纳入值尾判定，且**必须不消费它**（消费掉反斜杠才会留下裸控制字符）| §2.2 逐字节；`secrets.rs::an_assignment_inside_a_json_string_survives_an_escaped_newline` |
| **F-DR72-2** | minor（**新，实测**） | **Windows 路径里的 `\r` 会被误判为转义换行**：`F:\runs\...` 的 `\r` 让赋值扫描提前收尾 ⇒ 多行环境转储的**后续行会残留**（用户名/凭据值不残留，但目录结构残留）。这是 (a) 的**代价**，已在 §6 显式披露，未假装修掉 | `secrets.rs::a_windows_path_value_is_not_mistaken_for_an_escape` |
| **F-DR72-3** | minor | `analysis/redaction_defect.txt` **仍保留环境值**（`HOH_ARTIFACT_DIR=`/`HOH_HOH_BIN=`/用户名 PATH 尾段）—— 确认 T10A-7。**明文密钥全仓 0 命中**（不是密钥泄露）。**未就地改写它**（它是"缺陷本身的冻结证据"），按 D279 把**同一次扫描**用于**本批产物**并落成测试 | §5.2；`frozen_evidence.rs::the_batch_evidence_products_carry_no_environment_values` |
| **F-DR72-4** | info | **退出码"三方一致"只有两处在冻结件里**（`exit_code` 字节 `30 0A`、`meta.json.exit_code=0`）；第三处 `ROUND_EXIT=0` 在包装脚本打到外层控制台，**不在 `runs/**`**。本报告**不把三方一致当落盘证据** | §5.1 |
| **F-DR72-5** | info（口径） | 上游报告三处计数不精确（最大消息、`-32602` 真实回包数、48 次调用里 9 次是 editor 侧）—— 本报告**全部自己从工件重算**，不转抄 | §6.2 |

---

## 2. ① 机制选择 + 「转义 `\n`」形态的对抗性证据

### 2.1 三选一：选 **(a) 修匹配**，并把 **(c)** 作为强制后置门

| 方案 | 采纳 | 理由 / 否决理由 |
|---|---|---|
| **(a) 修匹配** | **采纳（主体）** | 根因是**终止符集合不完整**（只认物理 `\n`，不认 JSON 转义）。补上 `\`+`n`/`\`+`r` 是**最小且精确**的修改，触发条件与被观测损坏**同形**。**关键实现细节**：终止符**不消费**（返回其首字节的下标）—— 若照旧消费，删掉反斜杠会把合法字符串变成裸控制字符，"修好"仍是坏 JSON |
| (b) `parse → 改写 → serialize` | **否决** | 对"**先按值替换、再按赋值扫**"这条现有管线**不解决问题**：值替换本身仍是文本扫，序列化之前的搜索仍在同一个字节空间里；要么把扫描搬到 `serde_json::Value` 树上（大改且要处理数组/嵌套/键名），要么只是把同一缺陷延迟到 serialize 之后。**投入大、风险面大、收益与 (a) 等价** |
| (c) 改写前先验证 | **采纳（作为强制门，不单独用）** | 只做 (c) 会让**合法文件里的赋值规则整体失灵**：本轮实测——**去掉 (a) 后，对抗性形状下拼接触发 `refused`，整个脱敏变成空操作**（§4 植入 1 的红输出）。`refused` 只应作**最后防线**，不能当主要修复 |

⇒ **最终形态 = (a) 修匹配（主体） + (c) 校验（门）**：`redact_secret_assignments_traced` 先做精确拼接，再**只在输入是 JSON 时**要求输出仍可解析；不可解析则**整体不改写**并把 `refused` 报告给调用方（`redact_tree_traced` 把它写进 `warnings.log`，不静默）。

### 2.2 修前 / 修后（真实字节）

**修前（冻结的真机损坏，只读测量，未写一个字节）**：

```
runs/smoke-t10/iter-1/traj/tester.attempt1.json   834125 B
  json.JSONDecoder.raw_decode → "Invalid control character at: line 2204 column 311 (char 412862)"
  char 419374 起（两处坏点之一，另一处 @419699）：
    ...HOH_ITERATION=1\nHOH_MODEL_API_KEY=<redacted>\n      "extra": {\n        "returncode": 0,...
                                            ^^^^ 物理换行落在 JSON 字符串内部
  同轮另 3 条轨迹可解析；developer.attempt2.json 的 2 处脱敏值后跟字面 `;` 而幸免
```

**修后（同形输入，走生产函数）**：

```
$ cargo test --offline --lib runtime::secrets::tests::an_assignment_inside_a_json_string_survives_an_escaped_newline -- --exact
running 1 test
test runtime::secrets::tests::an_assignment_inside_a_json_string_survives_an_escaped_newline ... ok
test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 138 filtered out
```

该测试断言四件事（**可复核**）：

1. **仍是合法 JSON**：`serde_json::from_str::<Value>(&report.redacted)` 成功；
2. **除被替换区间外逐字节相同**：`bytes_changed_outside_spans(&report) == Some(0)`，而该函数**先从 `original` + `spans` 逐字节重建输出**、再与 `redacted` 比较——所以它同时证明"输出是输入的一个纯拼接"与"跨度外零差异"；
3. **跨度可重组**：测试内 `reassemble(&report) == report.redacted`；
4. **旧代码毁掉的东西还在**：`report.redacted` 里 `"extra":{"returncode":0}` 与 `content` 以 `</output>` 收尾 —— 闭引号与逗号未被吞。

**逐字节的差分方式（交给复跑者）**：`RedactionReport { original, redacted, spans: Vec<RedactionSpan{name,start,end,replacement}> }` 是公开类型；把 `original` 按 `spans` 拼接即必须等于 `redacted`。受控证据里的**真实样例**：

- 输入 `.spec/hof-rs/tasks/TASK-DR72-evidence/samples/env.original.txt`
- 输出 `.../env.redacted.txt`（**由生产函数生成**，非手改；见 `REDACTION-POLICY.md`）
- 跨度 `.../env.spans.txt`：

```
HOH_ARTIFACT_DIR [53..83) -> HOH_ARTIFACT_DIR=<redacted>
PATH [129..153) -> PATH=<redacted>
```

- **非空洞性**：`frozen_evidence.rs::the_redacted_sample_is_regenerable_from_the_production_pass` 每次都在真实运行里用生产函数重算这两个文件并与之逐字节比较；不一致即红（并且它会把生产结果写到 `target/dr72-redaction-sample/`，让修正只需一次 `cp`，**不手改转义**）。

### 2.3 抗"误报"的补充测试（防止修一个形态造出另一个）

- `a_windows_path_value_is_not_mistaken_for_an_escape`：JSON 字符串里**双反斜杠**的 Windows 路径（`C:\\Users\\u`），断言赋值被替换、**值消失**、且转义后的 `next` **存活**。
- `what_followed_the_assignment_in_the_same_string_survives`：值是无反斜杠的普通 token，断言**转义之后的字节全部存活**且仍是纯拼接。
- `a_splice_that_would_break_json_is_refused_and_reported`：(c) 门——**已经非法**的文档不改写、`refused` 显式。

---

## 3. ②③④⑤ 的落点与红→绿

### ② 脱敏改为"旁注/生成式"

**落点**：`src/runtime/secrets.rs`（`SealedAreas`/`TreeRedactionReport`/`redacted_copy_path`/`redact_tree_traced`）、`src/runtime/run_loop.rs`（`frozen_evidence_roots` + `redaction_sweep`，替换 5 处调用点 + 轮末 1 处）。

**冻结区域（运行时定义）**：`versions/**`、`quarantine/**`、`iter-*/candidate/**`、`iter-*/traj/**`。命中即写 `<name>.redacted.<ext>` 副本，原件逐字节不动。
**刻意不冻结**：`iter-*/planner-view/**` —— DR-19 仍要求"凭据位置不得在 `runs/<id>` 下存活"，而角色会把自己的环境转储写进自己的视图，**且没有任何消费者解析 planner-view**（`secret_isolation.rs::a_leaked_secret_is_erased_and_counted` 正是这条的既有测试）。这条区分写进了 `frozen_evidence_roots` 的文档注释。

**测试（先红）**：`frozen_evidence.rs::a_redaction_pass_leaves_frozen_evidence_byte_identical` —— 5 个冻结区文件各放一份**合法 JSON + 转义换行 + 环境值**，跑一次 `redact_tree_traced`，断言：**5 个原件逐字节不变**、5 个副本存在且干净（`scrub_is_clean`）、副本计入 `report.copies` 而**不**出现在 `report.rewritten`、`hits() == 5+1`、唯一非冻结文件仍被就地改写。

**红→绿**（植入 2 见 §4）：把 `if sealed.contains(&path)` 换成 `if false`，同一测试 **FAILED**：

```
assertion `left == right` failed: versions/aaaa/env.json is frozen evidence and must be byte-identical after the pass
  left: "{\"dump\": \"HOH_MODEL_API_KEY=<redacted>\\nHOH_ARTIFACT_DIR=<redacted>\\runs\\\\run-1\"}\n"
 right: "{\"dump\": \"HOH_MODEL_API_KEY=test-key-not-a-secret\\nHOH_ARTIFACT_DIR=F:\\\\stand-in\\\\runs\\\\run-1\"}\n"
```

**顺带闭合 D279/T10A-7（调度者补充 1）**：`HARNESS_ENV_VARS` 扩到 11 个 `HOH_*` + `PATH`/`Path`；`scrub_text` 把"赋值"与"值"两规则合成一次带跨度拼接。新增测试 `the_batch_evidence_products_carry_no_environment_values` **只扫本批受控证据目录**，并且**把"含用户名的路径"独立于"凭据形状"单独判**（这正是上游漏掉的那一类）。**未修**的 `TASK-SMOKE-T10-evidence/analysis/redaction_defect.txt` 作为**发现**列在 §5.2，未就地改写。

### ③ `evidence_diff` 变真

**落点**：`run_loop.rs::iteration_evidence_diff`（新）+ 迭代内 `iteration_start_manifest` 采集（在 Developer 之前、rollback 之后）+ 成功路径赋值；`record.rs::iteration_directories`（供红扫封区用）。

**语义**：`evidence_diff = diff(迭代起始的工程清单, 冻结的 versions/<version_id> 清单)`，两侧都用**运行时自己的 walk 与排除集**（`HashExcludes`），所以**可复算**。

**测试（先红）**：`e1_increment.rs::a_round_that_changes_files_records_the_real_evidence_diff` —— 一轮改 1 个脚本、加 2 个脚本，断言 `evidence_diff` 非空、`added == ["scripts/coin.gd","scripts/goal.gd"]`、`modified == ["scripts/player.gd"]`、`removed` 空，并**独立核对**冻结快照确实带 Developer 的字节、`versions/` 下确有 A0 与 A1 两个快照。
**非空洞性同伴**：`a_zero_increment_round_records_an_evidence_diff_that_is_honestly_empty` —— 只有 `.hoh/scratch` 写的一轮，三个数组**必须都为空**（防止"永远写一个固定非空 diff"也能过）。

**红→绿 + 直接复现 F-T10-3**（植入 3）：把成功路径的赋值 `if true` 短路，测试 **FAILED**，输出**逐字复现**上游那条缺陷证据：

```
the round changed `scripts/player.gd` and added two scripts, so `evidence_diff` cannot be empty —
that is exactly the F-T10-3 defect: {"added":[],"modified":[],"removed":[]}
```

⇒ **"诚实的空"与"未实现"现在是两种可区分的事实**：前者由同伴测试（零增量轮）钉住，后者由本测试钉住。

### ④ `node_path` 参数契约摩擦 —— **诊断结论**

**诊断（逐层）**：

| 层 | 判定 | 证据 |
|---|---|---|
| **引擎工具实现** | **不是问题** | 捕获的 `tools/list`（`tests/fixtures/mcp/tools_list.json`）里 `editor_get_node_properties` 的 `inputSchema` 就是 `{"path": string, "properties": array<string>}`，`required=["path"]`；**同族的 `editor_get_collision_info` 用的才是 `node_path`** ⇒ 命名不统一是真的，但该工具**没有错** |
| **角色侧用法** | **是问题（错的一侧）** | 模型给 `editor_get_node_properties` 发了 `node_path`（游戏通道的拼法）；这是**可理解但错误**的用法 |
| **契约表述 / 引导** | **是问题（harness 该修的一层）** | `.hoh/TOOLS.md` 由**真 schema** 渲染、**本来就写着 `path`**，但**引擎的拒绝只点名"被拒的"参数，不点"可用的"**；`-32602` 的原文（真机 `returncode 5`）就是 `Unknown parameter 'node_path' for tool 'editor_get_node_properties'` —— **下一步只能再猜**。playbook 的示例区也**只示范了游戏通道的 `node_path`**（`editor_get_node_properties` 未在示例里出现） |

**修的那一层 = 契约表述/引导（harness 侧，非引擎树）**：

- `src/tools/index.rs::accepted_parameters(tool)`：从**同一份** `tools/list` 快照取该工具声明的参数名（`.hoh/TOOLS.md` 的同一个来源）。
- `src/tools/mcp.rs`：`is_unknown_parameter_error`（`-32602` **且** message 含 `unknown parameter`，所以 DR-54 的 `ACTION_NOT_BOUND` 不受影响）、`parameter_guidance`、`unknown_parameter_message`、`augment_parameter_error`、线程本地 hint。
- `src/tools/bridge.rs::tools_call`：调用前装载 hint、调用后清除（**只有 CLI bridge 这一条进程路径**装，因此 harness 内部的 `-32602` 绝不被改写）。
- `src/tools/mod.rs`：`McpChannel::call_with_meta` 的 `Err` 分支调用 `augment_parameter_error` —— **必须在调用者线程**做，因为 `call_traced` 跑在 `spawn_blocking` 工作线程上（本批实测踩到过这一点，注释已写明）。
- **错误类不变**：仍是 `McpError{code:-32602}`，只是 message 更长。

**测试（先红）**：`tests/tool_parameter_contract.rs`（4 条，走**真实 CLI 派发** `hof_rs::cli::dispatch` → `hoh tools call`，对 loopback JSON-RPC double；无 Godot、无外部端口、不写 `runs/**`）

1. `the_captured_contract_declares_path_for_the_property_tool`：**从夹具**推导"正确名 = `path`"，并断言 `node_path` **不在**该工具声明里、而在 `editor_get_collision_info` 里 —— "正确参数名"不是硬编码。
2. `the_correct_parameter_name_succeeds`：用**声明里的名字**发调用 ⇒ 退出码 0。
3. `the_wrong_parameter_name_is_refused_with_the_accepted_names`：发 `node_path` ⇒ 错误里**保留引擎原句**且**点名可用参数 `path`**。
4. `the_hint_turns_a_terse_refusal_into_an_actionable_one`：机制单测 + hint 生命周期 + 未知名工具**诚实降级**（"harness has no schema"）+ 非空洞性（换一个参数列表得到不同消息）。

**红→绿**（植入 4）：删掉 `augment_parameter_error`，测试 3 **FAILED**：

```
the refusal must name the accepted parameter `path`:
JSON-RPC error -32602: Unknown parameter 'node_path' for tool 'editor_get_node_properties'
```

⇒ 这就是真机那句**一字不差**的形态。

### ⑤ D1 / D2 / 竞态

**(D1) 就绪判据合一。** 落点：`src/tools/reliable.rs::wait_for_ready_matching`（带 `shape` 谓词的就绪轮询）、`src/adapter/godot.rs::scene_tree_readiness`（唯一谓词：`describe_scene_tree_shape(unwrap_mcp_payload(payload))`），**电池的 `ready()` 与轮次的 `start_round_game` 都走它**。语义：形状不对 **不算就绪**，但**继续轮询**（刚启动的游戏可能先给 stub），到 deadline 时**失败信息就是形状拒绝**（不是笼统超时）。
**测试**：`round_game_start.rs::the_round_readiness_poll_requires_a_scene_tree_not_merely_an_answer` —— double 先给 **3 次非场景树**再给真树；断言 `polls >= 4`（旧判据会停在第 1 次）且记录被发布。
**同时修正既有测试的**假绿**：`a_ready_game_is_published_with_the_record_the_start_confirmed` 与 `a_publish_failure_is_reported_instead_of_swallowed` 原来喂的是**电池会拒的**形状（`{"tree":{"name","path"}}`，节点缺 `type`）⇒ 已换成真场景树。这是"两个判据不一致"被测试**认同**了的表现。

**(D2) 轮询期间的判别器。** `round_game_start.rs::the_round_readiness_poll_never_exposes_the_route_while_it_runs` —— 复用电池已有机制（`RpcDouble::watching`，每个请求到达时记录路由文件是否存在），对**轮次**路径断言：就绪轮询期间路由**从未**可见、失败后文件与进程内路由都不留。
**先红**：该测试在"安装即发布、失败才清"的旧形态下必然红（这正是 DR-71 验收者说"能让 8 条轮次测试全绿"的盲区）；本批未单独逆转旧形态（那需要改写历史实现），但判别器本身已与 D1 一起被植入证明为有效（植入 2/4 均能变红；D2 的判据与电池测试**同构**，电池侧同类断言 `an_unconfirmed_battery_play_never_exposes_a_route` 在改动前后均绿）。

**(竞态) 可复跑的并发测试 + 丢失模式。** `game_route_across_processes.rs::concurrent_publish_and_read_never_yields_a_torn_record` —— 1 写（每 3 轮插一次 `withdraw`）+ 4 读，400 ms，payload 4 KiB 级；断言：**读到过**（`hits>0`）、**torn == 0**（每次观测要么是**完整合法**且 `pid == 本进程` 的记录，要么 `None`）、并且**丢失模式的退路是明确拒绝**（`withdraw` 后 `use_game_route_file` 与 `load_game_route` 都返回 `None`，绝不猜端口）。
**读数**：本机 `reads≈9.6k / hits≈7.0k / misses≈2.6k / torn=0`，与 DR-71 验收在真机测到的 **9658 读 / 7074 未命中 / 0 撕裂**同形（**数量级相同**，不是同一次运行）。

---

## 4. 非空洞性：4 处**仅生产代码**的受控植入

规则：每处只改**生产代码**（`src/**`，不碰测试）；改后先 `rm -rf target/debug/.fingerprint/hof-rs-*` 再测；记录**对应**测试的真实红输出；随后 `cp -p` 回退，并以 **`cmp` 对仓外备份** + `sha256sum` 双证。全部回退后：`diff -r src /f/dr72-backup/src` → **SRC_TREE_IDENTICAL**；`diff -r tests ...` → **TESTS_TREE_IDENTICAL**；`grep -r PLANT src tests` → **0**。

| # | 植入（生产代码） | 对应测试（变红） | 红输出要点 | 回退证明（cmp + sha256） |
|---|---|---|---|---|
| **1** | `secrets.rs:167` `b'\\' => matches!(...n/r)` → `b'\\' => false`（转义不再终止） | `runtime::secrets::tests::an_assignment_inside_a_json_string_survives_an_escaped_newline`（**另带红 2 条同族**） | `the splice must be accepted for this shape: Some("… control character … invalid JSON …")` | `CMP_EQUAL_secrets.rs`；`ef76206d…7ad6` == 备份 |
| **2** | `secrets.rs:578` `if sealed.contains(&path)` → `if false`（冻结文件被就地改） | `a_redaction_pass_leaves_frozen_evidence_byte_identical` | `versions/aaaa/env.json is frozen evidence and must be byte-identical after the pass` + 左右字节对照 | `CMP_EQUAL_plant2_restore`；`ef76206d…7ad6` |
| **3** | `run_loop.rs:1794` 成功路径的 `evidence_diff` 赋值短路（`if true` 跳过） | `a_round_that_changes_files_records_the_real_evidence_diff` | `… that is exactly the F-T10-3 defect: {"added":[],"modified":[],"removed":[]}` | `CMP_EQUAL_plant3_restore`；`c24bf53d…6dd9` |
| **4** | `tools/mod.rs:413` `Err(mcp::augment_parameter_error(tool, error))` → `Err(error)` | `the_wrong_parameter_name_is_refused_with_the_accepted_names` | `the refusal must name the accepted parameter `path`: JSON-RPC error -32602: Unknown parameter 'node_path' …` | `CMP_EQUAL_plant4_restore`；`b6953b3b…7f44` |

**为什么必须 `cmp`**：本仓 `core.autocrlf=true`（§5.4 实测），git 层的 `git status --porcelain` / `git diff` 对行尾差异**是盲的**（`git hash-object` 归一化后也可能相同）。所以回退证明以**仓外备份的字节比较**为准，`git` 的三项只是**附加**证据：

```
$ git status --porcelain -uall          # 植入已回退、只剩本批应提交的改动（§5.4 列表）
$ git diff --stat                       # 同上，无植入残留
$ git hash-object src/runtime/secrets.rs    # 与备份 sha 对照一致
```

**没有把植入落在承载不变量的测试里**：4 处**全部**在 `src/**`，`tests/**` 一个字节未参与植入（参 D253 的口径）。

---

## 5. 禁区自查（真实输出）

### 5.1 `runs/**` 五条基线未动 + 摘要口径自证

`scripts/dr72-digest.ps1`（PowerShell 5.1，**只读**；口径逐字沿用 T8/T9/T10：仓根相对小写 POSIX 路径 + 字节长度 + 小写 SHA256，`\t` 连接、`\n` 分行、无尾随换行，行序 **`Sort-Object` 文化排序**，整体 UTF-8 取 SHA256）：

```
runs/smoke-t6  135  c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03  newest 2026-09-29 02:32:01
runs/smoke-t7  115  6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7  newest 2026-09-29 14:41:14
runs/smoke-t8  358  6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7  newest 2026-09-30 07:58:28
runs/smoke-t9   83  541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d  newest 2026-09-30 11:27:29
runs/smoke-t10 232  319555896964ce1526f72a33cb239bf389fe29bcde23841764d13c57dfb38b8b  newest 2026-09-30 18:23:08
```

- **五条逐字命中**任务书/上游报告记录的值（含 **`smoke-t6 = c144ef32…7a9c03` 自证**），文件数与 `newest` 也逐字一致。
- **本批对 `runs/**` 零写入**：`find runs -newermt "2026-10-02" -type f` → **空**（本会话日期晚于全部五轮，故"零写入"可机检）；分析脚本与中间产物只在**仓外**（`/f/dr72-backup` 与 `target/`）。
- **口径是口径的一部分**：文化排序不是可选项（换成 ordinal 会给出不同摘要，T9 验收已实测并记录）；本报告因此**不跨口径引用**数字。

### 5.2 其余禁区

| 断言 | 实测 |
|---|---|
| `PRD-mario.md` 冻结 | `sha256 = 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`（与 `meta.json.spec.sha256` 同） |
| `DECISIONS.md` 未由我编辑 | `git status` 全程无 `DECISIONS.md`；本会话中它的每次变化都来自**调度者提交**（`262d887`→`5603f32`→`9211a0d`→`9e7f8ea`） |
| `godot-mcp/**` 零改动（**嵌套仓**） | `git -C godot-mcp/godot rev-parse HEAD = fc63af77…f63a3`（与上游记录同）；`status --porcelain -uall` = **0 行**；外层 `git ls-files godot-mcp` = **6484**（**pathspec 真命中**）对 `git ls-files godot-mcp/godot` = **0**（空判对照） |
| 无新依赖 | `git diff --stat HEAD -- Cargo.toml Cargo.lock` **空** |
| 未 push | `git rev-parse HEAD origin/master` 两值相同（开工 `9e7f8ea`；本批提交未推） |
| 仓内无临时物 | `git status --porcelain -uall` 仅本批的 20 个条目（13 改 + 5 证据 + 1 测试 + 1 脚本），**无 `*.tmp-submit`/`*.tmp-publish`/调试残file**；`scripts/` 下新增的只有只读摘要脚本 |
| `.workspace/mario/**` | 我只读；本批未启动任何游戏/编辑器，未写工程 |
| 未启动 Godot / 未触端口 / 未联网 / 未调模型 | 全程只跑 `cargo`、只读文件与 git；loopback double 只绑 `127.0.0.1:0` |

### 5.3 环境值（调度者补充 1）—— 发现与处置

```
$ grep -n 'HOH_MODEL_API_KEY=\|HOH_ARTIFACT_DIR=' .spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/analysis/redaction_defect.txt
1:'it-hof-rs\\\\.workspace/mario\\\\.hoh\\nHOH_GAME_ROUTE=…\\nHOH_HOH_BIN=…\\nHOH_ITERATION=1\\nHOH_MODEL_API_KEY=<redacted>;C:\\Users\\wyl\\…'
```

- **确认 T10A-7**：该分析件确实保留 `HOH_*` 值、用户名 PATH 尾段（**不是密钥泄露**：明文密钥全仓 **0 命中**）。
- **处置**：**不就地改写它** —— 它是"脱敏器写坏证据"这一缺陷的**冻结证据本身**（且 `HOH_MODEL_API_KEY=<redacted>` 正是被分析的对象）。改为：**(i)** 把同一次扫描用于**本批产物**并落成测试（`the_batch_evidence_products_carry_no_environment_values`，含"含用户名的路径"独立判据）；**(ii)** 在 §6 作为**遗留项**明确上报给调度者决定是否生成 `<name>.redacted.txt` 旁注副本。
- **自证**：本批受控证据**不含**真实环境值 —— `samples/env.original.txt` 是 `<stand-in>` 合成值，用户名用 `<user>`；测试每次运行都会扫描 `TASK-DR72-evidence/**`（唯一豁免是 `samples/`，且豁免理由写在该目录 `README.md` 里）。

### 5.4 行尾与编辑工具（硬约束）

- **未用** PowerShell 5.1 的 `Get-Content -Raw` + `Set-Content` 改写任何源码；所有源码编辑走文件工具的**字面替换**；`cargo fmt` 是唯一的批量格式化，用于让 `cargo fmt --check` 归零。
- **未整文件重写行尾**：改动文件实测 `CR=0`（LF）。本仓 `core.autocrlf=true`，git 的 `LF will be replaced by CRLF` 是**检出期归一化提示**（入库 blob 仍是 LF），不是本批引入的改动；因此回退证明按 §4 用 **`cmp` 对仓外备份**。

---

## 6. 遗留风险与未验证项（严格区分**实测** / **推断**）

### 6.1 实测（有本轮证据）

1. ①的机制选择与对抗性证据：修前真机损坏字节（char 412862，只读测得）+ 修后合法 JSON + 跨度外零差异。**(a)+(c) 组合；去掉 (a) 时整个脱敏退化为空操作（植入 1 实测）。**
2. ②：5 类冻结区逐字节不变、5 份生成副本、唯一非冻结文件仍就地改；`planner-view` **刻意不冻结**并有 DR-19 的既有测试兜底。
3. ③：成功路径 `evidence_diff` 非空且与独立重算一致；零增量轮**诚实的空**；短路即复现 `{"added":[],"modified":[],"removed":[]}`。
4. ④：诊断三层结论；真机那句错误形态在测试里被复现并已被"点名可用参数"取代。
5. ⑤：D1 两个判据合一（含两处既有测试的假绿被改正）；D2 判别器在轮次路径就位；竞态并发测试 torn=0、丢失模式=明确拒绝。
6. 4 处生产代码植入各自红 + 逐字节回退（`cmp` + sha256 + 全树 `diff -r` 同一）。
7. 门：`cargo test --offline` exit 0，`475 passed / 0 failed / 7 ignored`，`cargo fmt --check` exit 0，逐文件 `touch` 强编。
8. 五条 `runs/**` 基线逐字命中；`PRD` 未变；嵌套引擎未改（pathspec 真命中对照）；无新依赖；未 push；仓内无临时物；本会话对 `runs/**` 零写入。

### 6.2 实测的**口径更正**（对上游报告，调度者补充 3）

| 上游说法 | 本批实测 | 依据 |
|---|---|---|
| "任一轨迹最大消息 65,886 B" | 按 **content 字符数**：developer 最大 **65,886**、tester 最大 **65,887**；按**整条消息序列化**：developer **156,999 B**、tester **139,445 B**（验收 T10A-3 同结论） | 本报告不转抄，结论（无 MB 级回放）不受影响 |
| "`-32602` 全轮 6 次，全是角色参数写错" | 字符串出现 6 处，但**真实引擎错误回包只有 2 个**（都在 developer.attempt1，各在 content 与 raw_output）；tester 那 2 处在它写的**注释文字**里 | 同上 |
| "48 次 replay 调用全是 `running_game_*`" | **39 `running_game_*` + 9 `editor_*`**（1 get_input_actions + 8 simulate_input_action） | 同上 |
| "退出码 0 三方一致" | **只有两处在落盘件里**（`exit_code` 字节 `30 0A`、`meta.json.exit_code=0`）；`ROUND_EXIT=0` 出自包装脚本打到外层控制台，**不在 `runs/**`** | 本报告 §5.1 只声明两处；**不把三方一致当落盘证据** |

### 6.3 推断（**不得当已测**）

1. **（≈0.7）** `F-DR72-2`（Windows 路径里的 `\r` 让赋值扫描提前收尾）在**真机多行转储**上的影响面：我用构造用例证明了该行为，**没有**在真机转储上端到端复现。
2. **（≈0.6）** 本轮"选 (a)+(c)"能覆盖**未来**所有形态：我覆盖了逃逸换行、双反斜杠路径、普通 token、已非法文档四类；**没有**对任意 JSON 转义族（`\t`、`\uXXXX`、`\"`）做穷举。
3. **（≈0.8）** D2 的判别器"能让旧形态变红"：我论证了它与电池同构、且判别机制本身经植入验证有效；**没有**真的把 `godot.rs` 回退到 DR-70 的"安装即发布"形态去实测那条历史实现。

### 6.4 未闭合 / 建议

1. **`analysis/redaction_defect.txt` 的环境值**（§5.3）：建议由调度者决定是否生成旁注副本；**不宜就地改写**（它是缺陷证据）。
2. **冻结文件的 `.redacted` 副本会落进下一轮的 `runs/` 扫描面**（本批 citato 的路径在 `versions/` / `traj/` 下，而 `versions/` 会进内容哈希）。本批**未**在 `versions/**` 里观察到副本（该目录只由 `snapshot_role` 写、红扫在其后），但**未验证**它在多迭代轮次下的行为 —— 建议下一批实测一次。
3. **`ROUND_EXIT` 未入冻结件**（F-DR72-4）：建议把进程退出码一并写进 `runs/<id>/`，让"三方一致"不再依赖包装脚本。这属于**范围外**，本批未做。
4. **`planner-view` 未被封区**是**有意**的（DR-19 优先）；若将来有消费者解析 planner-view，这条必须重开。

---

## 7. 诚实披露

1. **我改了什么**：`src/**` 9 文件、`tests/**` 5 文件、`.spec/hof-rs/tasks/TASK-DR72-evidence/**` 5 文件、`scripts/dr72-digest.ps1` 1 文件。**两笔提交**：`04abf5f`、`f4b4463`（均带 `(DR-72)`，英文信息）。**未推**。
2. **调度者在并发推进**：开工 HEAD `9e7f8ea` 在我工作期间由调度者产生（`262d887`→`5603f32`→`9211a0d`→`9e7f8ea`）。**我没有提交过 `DECISIONS.md`**，也没有 amend 过任何既有提交。
3. **我用过的一次"非只读"动作**：`cargo test`/`cargo fmt`/`cargo build`（编译与格式化）、`cp -r src tests /f/dr72-backup`（**仓外**备份）、`cargo fmt` 对**我改动的文件**做了常规格式化（LF）。**没有**启动 Godot、**没有**触任何端口、**没有**联网、**没有**调用模型端点、**没有**跑真机轮、**没有**写 `runs/**` 一个字节（含临时文件）。
4. **植入过程中的一次工具陷阱如实记录**（§1.1）：fingerprint 陈旧导致有一轮"红"其实是**旧二进制**跑出来的，我识别并清除后重取；§4 表里的红输出**全部**是清 fingerprint 之后的。
5. **一处自我更正**：②的设计初稿把 `planner-view` 也封了，导致既有测试 `secret_isolation.rs::a_leaked_secret_is_erased_and_counted` 变红。我**没有**改那条测试去迁就实现，而是**判断 DR-19 优先**、把 `planner-view` 移出封区并在代码注释与报告中写明理由。**这条取舍是我的判断，不是任务书直接规定**。
6. **我没有声称 E1/E3 已 met**；本批不含任何真机行为证据，也不给真机概率（§6.3 的推断均带前提）。
7. **我没有把推断写成实测**：§6.1/§6.2 与 §6.3 严格分开；`F-DR72-1/2` 均已给出可复核的字节或测试名。
8. **受控证据里没有真实环境值**（合成 `<stand-in>`/`<user>`），且每次测试运行都会扫描该目录自证；**唯一**已知残留是 §5.3 的既有分析件，已作为**发现**上报而非偷偷修掉。

---

## 附：本报告的机器可读结论块

```json
{
  "task": "TASK-DR72",
  "head_at_start": "9e7f8ea27a4fb928acb34b0a117246c81d1f8def",
  "commits": ["04abf5f", "f4b4463"],
  "gate": {
    "cargo_test_offline_exit": 0,
    "passed": 475,
    "failed": 0,
    "ignored": 7,
    "ignored_grew": false,
    "cargo_fmt_check_exit": 0,
    "forced_rebuild": "per-file touch over git ls-files '*.rs'"
  },
  "items": {
    "1_redactor_escape": {"done": true, "mechanism": "a_plus_c", "chosen": "escape-aware exact terminator, terminator not consumed, JSON post-validate gate"},
    "2_generated_redaction": {"done": true, "sealed": ["versions", "quarantine", "iter-*/candidate", "iter-*/traj"], "not_sealed_on_purpose": ["iter-*/planner-view"], "copy_suffix": ".redacted"},
    "3_evidence_diff": {"done": true, "measured_from": "iteration start manifest -> frozen A_t snapshot"},
    "4_parameter_contract": {"done": true, "diagnosis": "engine tool correct; role usage wrong; contract guidance is the harness-side defect", "fixed_layer": "tools/index.rs + tools/mcp.rs + tools/bridge.rs + tools/mod.rs"},
    "5_readiness_and_race": {"done": true, "one_predicate": "scene_tree_readiness", "d2_discriminator": "round path watches the route during the poll", "race": "concurrent publish/read, torn=0, loss mode = explicit refusal"}
  },
  "plants": 4,
  "plant_restores": {"cmp_vs_out_of_repo_backup": "equal", "diff_r_src": "identical", "diff_r_tests": "identical", "plant_markers_left": 0},
  "runs_baseline": {
    "smoke-t6": [135, "c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03"],
    "smoke-t7": [115, "6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7"],
    "smoke-t8": [358, "6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7"],
    "smoke-t9": [83, "541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d"],
    "smoke-t10": [232, "319555896964ce1526f72a33cb239bf389fe29bcde23841764d13c57dfb38b8b"]
  },
  "forbidden": {"prd_sha256": "4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a", "nested_engine_head": "fc63af77c33368c4a1bb839c95d19750554f63a3", "nested_engine_porcelain_lines": 0, "new_dependencies": false, "pushed": false, "runs_writes": 0},
  "not_claimed": ["E1 met", "E3 met", "real-machine probability"],
  "unverified": ["Windows-path backslash-r impact on a real multi-line dump", "exhaustive JSON escape families", "D2 against the historical publish-on-install code"]
}
```
