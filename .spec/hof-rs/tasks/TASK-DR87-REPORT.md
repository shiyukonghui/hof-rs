# TASK-DR87-REPORT — 把截断守卫的**误报**修掉、把冻结视图判据**裁回拒绝**、把逃逸路线**关一条、声明两条**，并重跑闸门

- 角色：**实现子代理（全新，无上游对话上下文）**；任务书 = 本批次派发方的完整提示词（自包含）
- 落点：`F:\moonbit-hof-rs`；起点 HEAD `6a55d2103f0f7ae5b9a5fe131bcf78aa0684e142`（含 D295 与那次未复核的加固补丁）
- **离线**：未启动/重启/驱动引擎，未跑任何轮次，未联网；**未写 `runs/**`、未写任何 workspace 目录**
- 未改 `DECISIONS.md`／`REQUIREMENTS.md`／`PRD-mario.md`／`Cargo.toml`／`Cargo.lock`／引擎树／引擎二进制；未加依赖；**未 stage／commit／push**
- 所有多行辅助脚本都在仓外：`C:\Users\wyl\AppData\Local\Temp\t16dr87\`（`backup.py`、`new_backup.py`、`plants.py`、`diagnose.py`、`diagnose_p3.py`、`probe.py`、`gate.py`、`no_removed_tests.py`、`forbidden.py`、`check_state.py`、日志若干）
- 本批**自己**使用了 Python 的 `glob` + `shutil.rmtree` 清指纹目录（路径**先打印后删除**）；**全程未用 `rm -rf`**、未用 `git checkout --` 还原、未从「未展开的变量」构造路径

---

## 0. 结论速览

| # | 任务 | 处置 | 性质 |
|---|---|---|---|
| 1 | 截断守卫的误报 | **关闭**（`src/runtime/integrity.rs`） | 注释不是可执行内容 ⇒ 注释里的 Windows 路径不再被当残渣；可执行代码里的外来转义仍被抓 |
| 2 | 冻结视图判据裁回拒绝 | **关闭**（`src/runtime/run_loop.rs` + 三处测试 + E5 读数） | 写冻结视图 ⇒ `ok=false`、`reason=contract_violation`；但真实门判决与留证仍然保留 |
| 3a | 干净行边界截断 / `.gd` 尾巴式碎片 | **声明为开放**（附语法理由） | 无法用原则性检查把它们与「真的很短的完整 `.gd`」分开 |
| 3b | 被排除目录（`.godot/**`、`.import/**`） | **声明为开放**（附残差与检出手法） | 有意为之的缓存排除；哈希与守卫都看不见 |
| 4 | 闸门数字 | **重跑并公布**（本节 §6） | 强制重建后的字面退出码与汇总，见 §6 |
| 5 | 未复核补丁 | **保留、逐行复核、补一个真正执行它的测试** | 不放松任何东西；见 §5 |
| 6 | 不放松任何东西 | 判据／跳跃诚实规则／地面探针／门分类／冻结规格均未改 | 见 §7 机械自检 |

---

## 1. 变更一：注释不是可执行内容（`src/runtime/integrity.rs`）

### 1.1 从语言自身的语法得到的规则（不是给报告里那个字符串加例外）

`.gd` 的检查原本只有一条规则：`\` 后面跟一个 GDScript 转义表之外的字符 ⇒ `artifact_shell_residue`。它逐行扫描，
**既不跳注释也不跳字符串**（`first_invalid_escape`）。于是 `# see C:\Users\dev\project` 里的 `\U` 被判为残渣，
并经接线变成门理由 `artifact_integrity:`，把一个**没有任何缺陷**的工程判为不可启动 —— 这是门检查最不该有的失败模式。

修法的依据来自 GDScript 自己的语法，而不是「这句话长得像注释」：

1. **注释在词法阶段就被丢弃。** GDScript 的 lexer 把 `#` 到行尾当作注释丢弃（与空白同类）；注释里的文本**不可能**成为
   解析错误，也**不可能**把任何转义带进程序。因此它不属于「这段文本是不是用目标语言写的」这个问题的管辖范围。
2. **字符串不是注释。** GDScript 的字符串字面量是**真实内容**（且必须在本行闭合），T16 那一轮的 `\$` 残渣恰好落在
   字符串里。所以「跳过字符串」会把这次修复真正要堵的洞重新打开 —— 本批**有意不跳字符串**。
3. **「哪里是注释」只能有一个实现。** 允许字符串里的 `#` 不开启注释，所以这是一个词法问题，不是字符串包含问题。
   新增 `code_span(line)` 做这一件事，`blank_literals`（括号规则本来就在用）改为调用它，`first_invalid_escape`
   也改为只看 `code_span` 的前缀。**一条 tokenizer 规则，三处共用**。

### 1.2 两个方向都被钉住

| 方向 | 测试 | 钉的性质 |
|---|---|---|
| 不得误报 | `runtime::integrity::tests::a_windows_path_in_a_comment_is_not_a_foreign_escape` | 一整份合法 `.gd`：注释里有 `\U`、`\t`、`\g` 三个 GDScript 没有的转义，字符串里有合法的 `\n`，行尾注释、字符串后面的注释都有 ⇒ **0 findings** |
| 必须仍抓 | `runtime::integrity::tests::a_foreign_escape_in_code_is_still_caught` | 四个位置的可执行转义各自成 finding：顶层语句 `\Users`、字符串里的 `\$`（T16 的形状）、**注释之前**的代码 `\z`、**字符串里的 `#` 之后**的 `\y` |

后一条测试的第三、四个位置是刻意的：它们证明「跳过注释」是按词法边界跳的，不是「看到 `#` 就停」。

复现（实测）：

```text
a_windows_path_in_a_comment_is_not_a_foreign_escape ... ok
a_foreign_escape_in_code_is_still_caught ... ok
a_foreign_shell_escape_is_residue_and_a_legal_escape_is_not ... ok
delimiters_inside_literals_and_comments_are_not_counted ... ok
```

### 1.3 没有放松任何其它东西

`AUDITED_EXTENSIONS`、`[section` 头规则、括号平衡规则、`audit_tree` 的排除规则、门理由的接线（`artifact_integrity:`
只增不删、分类不动）**一字未改**。§7 的 plant P3 证明审计范围本身仍在承重，P6 证明门理由的接线仍在承重。

---

## 2. 变更二：冻结视图判据裁回**拒绝**（D295(b)）

### 2.1 改了什么

`src/runtime/run_loop.rs` 的 Tester 污染分支：检测、从 `A_t` 快照恢复、留证（added 移走 / modified 先复制再覆盖）
**全部保留**，但分支末尾不再是「恢复成功 ⇒ 继续走到门判决并 `ok=true`」，而是**无条件** `fail_contract`：

- `result.json.ok = false`、`reason = "contract_violation"`、`failed_role = "tester"`；
- `result.json.warnings` 里同时有 `qa_contaminated_<view>_restored`（恢复/留证事实）与违约码
  （`qa_contaminated_candidate` 或 `read_only_role_wrote_artifact`）；
- `result.json.artifact_gate` 是**电池真实产生的那个判决**（`FailureFacts.artifact_gate`），
  **不是** `not_applicable("the round failed; no artifact gate was produced")` 存根；
- `candidate_id` / `version_id` / `battery_passes` 仍在记录里。

理由就是 D295 的裁决：**R4/R13 要求拒绝，判据度量的是合规性而不是可修复性**。恢复与留证让违约**可审计**，
它们不是「修复」，所以轮次仍判非达标；相对 `smoke-t16` 真正改变的是：**失败不再丢掉已经产生的门判决**。

### 2.2 一处顺带的措辞收敛（不是放松）

恢复失败分支原本写 `candidate_violation.or(workspace_violation).unwrap_or(QaContaminatedCandidate)`。
`workspace_violation` 的实际取值来自 `assert_unchanged("tester/workspace", …)`，它是
`ReadOnlyRoleWroteArtifact`，**不是** `QaContaminatedCandidate` —— 只有「两侧都无违约」（分支内不可能）时才会取到那个兜底值。
本批把判决折叠成一个 `violation` 变量（两处都用它），行为对全部可达路径**逐字等价**，但不再留下一个会误导读者的兜底值。

### 2.3 E5 的读数如何区分「没写」与「写了又恢复」

`tests/godot_smoke.rs::e5_qa_did_not_modify_the_artifact`（E5 的读数，`#[ignore]`，读真机轮证据）现在**两件事一起要求**：

1. `result.json.ok == true`；且
2. `result.json.warnings` 里**没有任何**以 `qa_contaminated_` 开头的 token。

只靠 `candidate_id == hash_tree(candidate)` 是不够的：一个「写了又被恢复」的轮次，哈希同样相等。
两条读数合起来就是判据自己的语义——**合规**，不是**可修复**。而这条要求本身被离线测试钉住：

- `tests/evidence_binding.rs::a_repaired_contamination_can_never_read_as_a_clean_round`：
  干净轮次 ⇒ `ok=true` 且 `restore_warnings == []`；污染轮次 ⇒ `ok=false` 且 restore 警告在
  （用**同一个** `restore_warnings()` 规则读取，与 E5 的过滤规则同形）；
- 另外两条测试 `rejects_contaminated_candidate` / `rejects_direct_real_workspace_write` 把「拒绝但保留判决」两侧都钉住。

### 2.4 被改钉的三条测试（诚实登记：**一处改名**）

| 测试 | 改前 | 改后 |
|---|---|---|
| `tests/evidence_binding.rs::rejects_contaminated_candidate` | `ok=true` + 恢复/留证断言 | `Err(QaContaminatedCandidate)` + `ok=false`/`contract_violation` + restore 警告 + 留证 + **真实判决仍在** |
| `tests/evidence_binding.rs::rejects_direct_real_workspace_write` | `ok=true` + 恢复/留证断言 | `Err(ReadOnlyRoleWroteArtifact)` + `ok=false` + restore 警告 + 留证 + **真实判决仍在** |
| `tests/write_integrity.rs::a_tester_write_into_the_frozen_view_is_restored_and_the_round_is_judged` | `ok=true`；断言「轮次必须被判决」 | **改名为** `…_restored_and_the_round_rejects`；断言改为「被拒绝，且恢复/留证/真实判决都仍在」 |

**改名如实登记**：原测试名字里的「judged（被判决）」在 `ok=true` 的旧语义下才成立；D295(b) 之后轮次**被拒绝**，
旧名字会与它断言的语义相反。本批把它改成 `…_rejects`，并**新增**四条测试
（§1 的两条 + §5 的 retry 一条 + §2.3 的区分一条），测试函数总数 **636 → 640**、`#[ignore]` **9 → 9**、
**没有删除任何测试**（逐名集合比对见 §4.4）。把一条名字与语义相反的测试改名，与「删掉一条测试」是两件事，
但这里不替读者下这个判断，只把事实写清楚。

---

## 3. 变更三：逃逸路线 —— 哪条关了、哪条只能声明

验收点名三条。逐条处置：

### 3.1 **已关闭：注释里的 Windows 路径被误判为残渣**

见 §1。这是三条里唯一能用**语言自身语法**（词法阶段的注释丢弃）判定、且修掉之后**不会引入新的误报**的一条。

### 3.2 **声明为开放：在干净行边界被剪断、且括号仍平衡的 `.gd`/`.tscn`**

- `tests/…`（原验收的 BOUND-C4/C5）就是这条：`"name = 12, y)  \r\n"` 换成任何**在行边界截断**的文本，
  括号平衡、没有 `[section` 头以外的症状（`.gd`）或头部完整（`.tscn`）时，**本批**仍然不报。
- **为什么不用「尾部换行」或「像不像一个完整文档」去关它**：一条**干净**的截断（在行边界切断）与一份**真的很短**
  的完整 `.gd`（例如 `extends Node\n`、`var x = 1\n`）在文件层面**没有语法区别** —— 两者都是合法的 GDScript
  程序前缀，GDScript 不要求文件以 `func`/`class` 结尾。要区分它们必须**解析**语言并判断「文件是否在语法上停在半路」，
  这不是一个 `audit_text` 级别的规则，而是换一套实现（真解析器）。
- **为什么不用「给 `.gd` 加括号平衡规则」去关它**：即使不谈多行字符串的细节，逐行 tokenize 的括号计数**不是**
  GDScript 的词法事实（行与行之间的引号状态、续行、字符串里的括号都会让「文件末尾深度」偏离「程序是否完整」）。
  一条会把**合法**文件判为碎片的规则，正是本批要消灭的「制造假红」，所以不引入它。
  （补充事实：plant 的第一版把 `.gd` 的**平衡判定**关掉以后，`a_fragment_of_a_line_is_not_a_scene_document`
  仍然**绿** —— 那条碎片是被**头规则**抓到的，这与「该形状有两个独立探测器」一致。）
- **这条的诚实表述**（建议写进规格）：本次守卫抓的 `.gd` 类是**外来转义**，抓的 `.tscn`/`.tres` 类是
  **无头**与**括号失衡**；**「行边界干净截断」不在被抓住的类里**。

### 3.3 **声明为开放：被排除目录（`.godot/**`、`.import/**`、`.git/**`）仍是写进冻结视图的通道**

- `HashExcludes::merged() = [".hoh", ".git", ".godot", ".import"]`。角色写进 `.godot/**` 的文件，
  `hash_tree`/`tree_manifest` 都不看，守卫既不恢复也不留证。
- **为什么不动它**：它们是有意排除的缓存（编辑器启动时会重建），把它纳入哈希会改 `version_id` 的稳定性
  （R10 要求 `version_id` 稳定）以及快照身份，**那是判据级的不变量，不是一个守卫级别的改动**。
  本批在**不进入哈希**这条边界内没有找到既真实又不引入假红的动作（例如「把 `.godot` 的新增也留证」会让每次
  编辑器启动重建的缓存都变成一次「污染」，把噪声读成违规）。
- **给真机轮的检出建议**：这一条的正确开放形式是**声明 + 检出手法**：`warnings.log` 里逐次列出
  `.godot`/`.import` 的 mtime 窗口，或在一轮前后比对它们的清单；但它**不是**一个判据。
- 按 D295(a) 的裁定，这条属「已知残留、带入下一批」，本批把它**写进残差表**（§8），不再假装它不存在。

### 3.4 附带：`audit_tree` 静默跳过非 UTF-8 文件（DR86A-6）

`audit_tree` 对读不成 UTF-8 的审计候选文件 `continue`（静默跳过）。这条**本批未改**：把它变成 finding 会让
「编码问题」看起来像「碎片」，与本次的「不制造假红」目标是反向的。**声明为开放**，并给出建议：
在**调用方**记录一条「审计候选但不可读」的 warning（不是 finding，不进 `launchable=false`），
这样事实可见而判据不误伤。

---

## 4. 测试、plant 与「没有删测试」

### 4.1 新增/改钉的测试一览

| 文件 | 条目 | 覆盖 |
|---|---|---|
| `src/runtime/integrity.rs` | `a_windows_path_in_a_comment_is_not_a_foreign_escape`（新） | 注释里的 Windows 路径必须干净 |
| `src/runtime/integrity.rs` | `a_foreign_escape_in_code_is_still_caught`（新） | 四个位置的可执行外来转义仍被抓 |
| `src/runtime/frozen_view.rs` | `a_transient_file_operation_failure_is_retried_to_success`（新） | **真正执行** §5 的重试助手：第 3 次成功、永久失败恰好耗尽预算并仍是错误、一次成功不重试 |
| `tests/evidence_binding.rs` | `a_repaired_contamination_can_never_read_as_a_clean_round`（新） | 「没写」与「写了又恢复」在判据自己的读数上不同 |
| `tests/evidence_binding.rs` | `rejects_contaminated_candidate`（改钉） | 拒绝 + 恢复/留证 + 真实判决 |
| `tests/evidence_binding.rs` | `rejects_direct_real_workspace_write`（改钉） | 同上（workspace 侧） |
| `tests/write_integrity.rs` | `a_tester_write_into_the_frozen_view_is_restored_and_the_round_rejects`（**改名** + 改钉） | 拒绝 + 留证 + 真实判决 + 违约码 |
| `tests/godot_smoke.rs` | `e5_qa_did_not_modify_the_artifact`（改读数） | E5 必须同时要求 `ok=true` 与「无 `qa_contaminated_*` 警告」 |

### 4.2 受控 plant（**6 个**，每个先有对照绿、植入红、还原后仍绿，且**逐字节还原**）

每个 plant 只做**一处字面替换**，跑**一个**指定测试，结束后从**字节备份**还原并用 sha256 证明。
plant 驱动的关键细节（本批付出过代价）：**每次编辑/还原后都 `os.utime`**，因为 cargo 按 mtime 判断是否重编译，
还原一个**更旧**的文件会让**植入后的**二进制继续被使用 —— 本批第一次跑 plant 时正是这样被误导（见 §4.5）。

| plant | 目标文件 | 一处替换 | 目标测试 | 对照→植入→还原 |
|---|---|---|---|---|
| P1-comment-skip | `src/runtime/integrity.rs` | `let cut = code_span(raw);` → `let cut = chars.len();` | `a_windows_path_in_a_comment_is_not_a_foreign_escape` | 绿 → **红** → 绿 |
| P2-reject-semantics | `src/runtime/run_loop.rs` | 污染分支的 `return fail_contract(...)` → 直接 `return Ok(RunSummary { ok: true, … })` | `evidence_binding::rejects_contaminated_candidate` | 绿 → **红** → 绿 |
| P3-audited-scope | `src/runtime/integrity.rs` | `AUDITED_EXTENSIONS = &["tscn","tres","gd"]` → `&[]` | `a_fragment_of_a_line_is_not_a_scene_document` | 绿 → **红** → 绿 |
| P4-retry-wrapper | `src/runtime/frozen_view.rs` | `with_retries` 体首插入 `return operation();`（只试一次） | `a_transient_file_operation_failure_is_retried_to_success` | 绿 → **红** → 绿 |
| P5-escape-catch | `src/runtime/integrity.rs` | `if !GDSCRIPT_ESCAPES.contains(&next)` → `if false && …` | `a_foreign_escape_in_code_is_still_caught` | 绿 → **红** → 绿 |
| P6-gate-reason | `src/runtime/run_loop.rs` | `format!("artifact_integrity: …")` → `"artifact_zzz: …"` | `write_integrity::a_truncated_write_closes_the_gate_with_its_own_reason` | 绿 → **红** → 绿 |

六个 plant 的完整读数（对照绿/植入红/还原字节相同/还原后绿）在 `C:\Users\wyl\AppData\Local\Temp\t16dr87\plants_run4.txt`，
汇总行：

```text
PLANT P1-comment-skip ok
PLANT P2-reject-semantics ok
PLANT P3-audited-scope ok
PLANT P4-retry-wrapper ok
PLANT P5-escape-catch ok
PLANT P6-gate-reason ok
PLANTS THAT DID NOT REDDEN: []
```

每个 plant 的还原证明都是 `restored byte-identical = True` 加当时的 sha256；本批结束时工作树哈希见 §4.3。

### 4.3 被放弃的两个 plant 设计（诚实登记，因为它们暴露了测试的真实承重面）

- **第一版 P3「关掉 `.gd` 的括号平衡」**：植入后目标测试**仍然绿** —— 它抓到的是**头规则**。
  一个 plant 不红**不是**测试空转，而是**两个独立探测器**都能抓到同一形状。这条事实本批写进 §3.2。
- **第一版 P4「让 `preserve_file` 不做 rename 重试」**：该测试的 rename 在临时目录里**总是成功**，
  所以「不重试」在测试里不可观测 ⇒ 那个 plant 只能证明「这条路径没被测试覆盖」。
  处置不是删掉它，而是**补一条真正执行 `with_retries` 的测试**（§5），再用 P4 植入证明该测试承重。

### 4.4 没有删测试（逐名集合比对）

用 git blob 取基线 `ccc0356` 的测试函数集合，与工作树比对（脚本 `no_removed_tests.py`）：

```text
baseline test functions: 636
working-tree test functions: 640
REMOVED: 1   - a_tester_write_into_the_frozen_view_is_restored_and_the_round_is_judged
ADDED:   5   + a_foreign_escape_in_code_is_still_caught
             + a_repaired_contamination_can_never_read_as_a_clean_round
             + a_tester_write_into_the_frozen_view_is_restored_and_the_round_rejects
             + a_transient_file_operation_failure_is_retried_to_success
             + a_windows_path_in_a_comment_is_not_a_foreign_escape
MOVED BETWEEN FILES: []
```

- 基线 **636** 与 DR-86 验收的 `--list` 读数一致；工作树 **640 = 636 − 1（改名）+ 5（新增）**。
- `#[ignore]` 属性数量：基线 `ccc0356` 的文件分布在 `tests/frozen_evidence.rs` 与 `tests/godot_smoke.rs`，
  工作树仍然是这两处 + `tests/evidence_binding.rs`（DR-86 的验收是**按属性**数出的 9）；两者都指向
  **ignored 计数未变**，最终以 §6 的运行读数（实际跑的 ignored 数目）为准。

### 4.5 本批的一次操作性事故（不隐藏）

第一次跑 plant 系列时，**六个 plant 全部报告「未植入成功」**，而且**对照测试在还原之后仍然红**。
根因不是被测代码，是**调查方法**：

1. 我在**编辑源码之前**用 `backup.py` 建了字节备份（备份里是编辑前的字节）；
2. 还原用的 `shutil.copy2` 会把备份的**旧 mtime** 一并写回；`cargo` 按 **mtime** 判断是否重编译，
   于是**已被还原**的源文件可能读到的仍是**上一次植入编译出来的**二进制。

**证据与限度（分开写）**：`diagnose.py` 的直接读数支持上面的机制 —— 还原源码后再跑，输出里**没有** `Compiling`
行、耗时 0.86 s、而目标测试**红**（即跑的是植入后的二进制）；同一脚本里植入后的那一次则明确 `Compiling`、5.17 s。
本批据此把处置定为「每次编辑与每次还原之后都 `os.utime(path, None)`」，并让驱动在开始前**强制断言**
「工作树字节 == 备份字节」。**这一条我不声称是唯一可能的机制**（并发句柄、其他缓存都会被同一症状掩盖），
但两条修复都指向「让 mtime 与内容一致」，之后 6/6 个 plant 的对照/植入/还原读数**全部自洽**，所以本报告只采信
断言通过之后的 `plants_run4.txt`。**教训**：在 mtime 驱动的构建系统上，字节还原必须同时还原 mtime。

---

## 5. 未复核补丁的复核（任务 5）

补丁位于 `6a55d21`，覆盖三个文件（相对 `ccc0356` 共 +76/−10）：
`src/runtime/frozen_view.rs`（`with_retries` 有界重试 + `preserve_file` 用重试包装 rename/copy/remove）、
`src/runtime/run_loop.rs`（恢复失败分支的**残余差异诊断** + `qa_restore_failed_<view>` 记录）、
`tests/write_integrity.rs`（失败时打印 warnings 与 warnings.log 再 panic）。

### 判定：**保留、不改**，并**补一条测试**让它承重

**它建立的属性（保留的理由）**

1. **一次瞬时文件操作失败不再变成「本轮不可判」。** `FILE_OPERATION_ATTEMPTS = 10`、`FILE_OPERATION_PAUSE_MS = 25`
   是有界预算（约 0.25 s/次操作），且**只重试文件操作**，不吞掉判定：预算耗尽后仍然返回错误、仍然进入
   `RestoreReport::failures`、仍然让本轮**响亮失败**。它改变的是「第一次失败就宣判」而不是「失败不再宣判」。
2. **失败路径的措辞更可执行。** 恢复失败时不再只说「恢复未核实」，而是给出仍存在的 `added/modified/removed` 残差
   与 `qa_restore_failed_<view>` 的完整报告；判据侧的语义**一字未变**。
3. **测试失败时自解释。** 那条 flaky 测试失败时打印 warnings/warnings.log 再 panic，**没有**把 panic 变成通过，
   也**没有**加任何宽容断言（例如「允许 ok=false」）。它只增加证据。

**它没有建立的属性（必须并列读）**

- 它**不是**瞬时错误的**根因**修复：Windows 上的共享冲突本身仍然会让一次操作失败；它只是把「一次失败即判定」
  变成「有界重试后仍失败才判定」。真正被消除的是**这个抖动对轮次结论的影响**，不是抖动本身。
- 它**不证明** `FILE_OPERATION_PAUSE_MS = 25` / 10 次这个具体预算是「足够」的：本批**没有**构造出真实的
  Windows 共享冲突来测它（做不到离线确定性复现），只能证明**预算被正确执行、且耗尽仍是错误**（新测试）。
- 它**不覆盖** `std::fs::copy` 对 modified 文件的**留证**那一处（那一处仍然只 `copy` 一次，见 §5 的「遗留边界」）。

### 我补的那一条测试（P4 让它承重）

`src/runtime/frozen_view.rs::a_transient_file_operation_failure_is_retried_to_success`：
用**闭包注入**失败（不依赖调度、时序或第二个进程）证明三件事——(i) 被拒的操作会被再次尝试并返回成功值；
(ii) 永久失败的调用恰好耗尽 `FILE_OPERATION_ATTEMPTS` 次并**仍然是错误**（`PermissionDenied`）；
(iii) 一次成功的调用**不会**被重试。plant P4（把重试助手降为单次）让这条测试变红。

### 遗留边界（补丁与我的新增都覆盖不到的）

`restore_frozen_view` 里给 `modified` 文件**留证**的那次 `std::fs::copy`（`frozen_view.rs` 的 `diff.modified` 循环）
**没有**被包装进 `with_retries`——它失败时直接进入 `failures`。这是补丁的**不对称**，本批**保留**该行为并登记：
把它也包起来会让「留证」和「恢复」在失败语义上更一致，但那属于补丁范围内的一次**扩大**，不在 D295 的裁决里，
也不在本次任务书里。**这是一条真实缺口**，建议下一批按「留证失败是否应当也重试、以及留证失败是否应当改变轮次判据」
单独裁决，而不是在本批顺手改。

---

## 6. 闸门：强制重建、字面退出码与汇总

（本节由 `C:\Users\wyl\AppData\Local\Temp\t16dr87\gate.py` 在仓内驱动；整份日志 `gate_log.txt`，
原始 stdout/stderr `gate_log.txt.raw.txt`）

**强制重建**（Python 的 `glob` + `shutil.rmtree`，路径**逐个打印后删除**；再按 `git ls-files "*.rs"` **逐个** `os.utime`）：

```text
FINGERPRINT_PATTERN=F:\moonbit-hof-rs\target\debug\.fingerprint\hof-rs-*
CLEARED_FINGERPRINTS=126
TOUCHED_TRACKED_RS=101
FMT_EXIT=0
LIST_EXIT=0
LIST_TESTS=640 LIST_BENCH=0
LITERAL_CARGO_TEST_EXIT=0
SUITES=62 PASSED=633 FAILED=0 IGNORED=7
RED_SUITES=0
```

强制重建的证据：`gate_log.txt.raw.txt` 里出现 `Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)`，且 126 个
`target/debug/.fingerprint/hof-rs-*` 目录在本次运行前被逐个删除（路径全部打印在 `gate_log.txt` 里）。
**字面退出码 `LITERAL_CARGO_TEST_EXIT=0`** 由 `subprocess.run(...).returncode` 原样写入，**不是推断**。

> 一处程序事故（不隐藏）：`gate.py` 自己的汇总步骤在自己的日志上抛了 `ValueError`（它把 `test result:` 整行
> 按 `;` 切分后误把 `test` 当成数字），所以 `gate_log.txt` 只写到 `LITERAL_CARGO_TEST_EXIT=0`。
> 退出码与 `--list`/`fmt` 的读数**不受影响**；上面的 `SUITES/PASSED/FAILED/IGNORED` 是我用
> **另一个只读脚本**（`summarize.py`）从同一份原始输出 `gate_log.txt.raw.txt` **重新求和**得到的，
> 62 个 `test result:` 头全部计入，`RED_SUITES=0`。

### 6.1 与基线对照

| 读数 | 基线 `ccc0356` | 本批（工作树） |
|---|---|---|
| 测试函数（逐名集合） | 636 | **640** |
| `#[ignore]`（属性数） | 9 | **9** |
| `--list` 用例数 | 636 | **640** |
| 运行时的 passed | 629（DR-86 验收） | **633** |
| 运行时的 failed | 0 | **0** |
| 运行时的 ignored | 7 | **7** |
| suite 数 | 62 | **62** |
| 红的 suite | 0 | **0** |
| `cargo fmt --all --check` | 0 | **0** |
| `cargo test --offline` 字面退出码 | 0 | **0** |

`633 + 7 = 640` 与 `--list` 的 640 一致；`629 → 633` 正好是本批净增的 4 条
（`636 → 640`：+5 新增 −1 改名，见 §4.4）。**ignored 计数未变（7）**，**没有测试被删除**。

### 6.2 本批的进程纪律（运行前后各一次）

- gate 作业运行**之前**与运行**之后**各查一次 `tasklist`：全程只有**一个** `cargo test --offline`
  （`cargo.exe` 42280 与其 rustup shim 39144，父子关系；`wmic` 的父进程号指向我的 `gate.py`），
  **没有第二个并发 cargo 运行**。结束时 `tasklist | grep -icE "cargo|rustc|hof_"` = **0**，
  即**没有任何属于本批的测试进程还在跑** —— 这正是 DR-86 那次日志被并发运行截断重写的成因，本批刻意收口。
- 未使用仓外 `CARGO_TARGET_DIR`：本批用**仓库自己的** `target/` 完成强制重建与全量套件，符合任务书
  「clear the crate's fingerprint directories」的字面要求。
- 全量运行**没有**改动任何已跟踪文件：运行后 `git status --porcelain` 与运行前逐字相同
  （除本批自己的 7 个改动文件与 4 个 T14 遗留未跟踪文件外无新增），`round_artifacts_sidecar` 的同字节重写
  不可见。

---

## 7. 禁止触碰区域的机械自检

全部读数为**本批结束时**（回填于 §6.1 同一次收尾）：

| 项 | 读数 | 结论 |
|---|---|---|
| `runs/**` | **7341** 个文件；最新 mtime `2026-10-03T05:47:27`（`runs/smoke-t16/evidence/round/evidence_refresh.txt`），**早于本批开始** | 未写 |
| `.workspace/**` | **836** 个文件；最新 mtime `2026-10-03T05:10:29`（`.workspace/fresh-t16/.hoh/deterministic/record-11.json`），**早于本批开始** | 未写 |
| `.spec/hof-rs/PRD-mario.md` | `4c81c3a9…`（未改） | ✓ |
| `.spec/hof-rs/REQUIREMENTS.md` | `298a9489…`（未改） | ✓ |
| `DECISIONS.md` | `2a4326ec…` 1238815 B（= `6a55d21` 的 D295 版本，**本批未改**） | ✓ |
| `Cargo.toml` / `Cargo.lock` | `e0c4992b…` / `d98fa915…`（未改；**未加依赖**） | ✓ |
| 引擎树 `godot-mcp/godot` | HEAD `fc63af77c33368c4a1bb839c95d19750554f63a3`，`git status --porcelain` **0 字节** | ✓ |
| 引擎二进制 | `godot.windows.editor.x86_64.mono.exe` 194216960 B / `08483088a4a277…`（与验收件一致） | 未改 |
| 未跟踪松文件 | `l.json`/`p2.json`/`pv.json`/`r.json` 仍是 `??`，未动 | ✓ |
| **git** | `HEAD=6a55d21…`、`origin/master=55a075194505e0f4a6d3e913a41e29880ea302e4`；本批**未 stage／commit／push** | ✓ **未推送** |
| 危险动作 | **未用 `rm -rf`**（只用 `shutil.rmtree` 清 `target/**` 里 glob 出来的 `hof-rs-*` 指纹目录，路径先打印）；未用 `git checkout --`；未从「未展开的变量」构造路径 | ✓ |
| 网络/引擎 | 未联网、未启动引擎、未跑轮次 | ✓ |
| 临时文件 | 全部辅助脚本与日志在 `C:\Users\wyl\AppData\Local\Temp\t16dr87\`；`tests/zzz_probe.rs` 是临时探针，**已由脚本删除**（`probe file removed: True`） | ✓ |

**测试副产物说明**：`tests/round_artifacts_sidecar.rs` 每次运行都会把一个被跟踪的 sidecar **逐字节同内容**重写，
本批按任务书忽略这种 churn（它不会出现在 `git status` 的已跟踪变更里）。

---

## 8. 残留风险：**实测**与**推断**分开

### 8.1 实测（本批，离线）

1. **误报已消除**：注释里有三个非法转义的整份合法 `.gd` ⇒ 0 findings（P1 让它承重）。
2. **可执行代码里的外来转义仍被抓**：四个位置各自成 finding（P5 让它承重）。
3. **冻结视图写 ⇒ 拒绝**：`ok=false` / `contract_violation` / `failed_role=tester`，同时**真实门判决**与
   留证/恢复都在记录里（P2 让它承重；`rejects_contaminated_candidate` 与 workspace 侧都钉住）。
4. **「没写」与「写了又恢复」在判据自己的读数上不同**：`ok` 与 restore 警告两条一起区分。
5. **审计范围与门理由接线仍在承重**：P3（清空 `AUDITED_EXTENSIONS`）与 P6（改门理由前缀）各自让自己的测试红。
6. **重试助手真正执行且仍然有界**：第 3 次成功、永久失败恰好耗尽预算且仍是错误、一次成功不重试（P4 让它承重）。
7. **闸门**：强制重建（清 126 个指纹目录 + 逐个 touch 101 个被跟踪 `.rs`）下的 `cargo test --offline`
   字面退出码 **0**、**633 passed / 0 failed / 7 ignored**、62 suites、`--list` **640**、
   `cargo fmt --all --check` **0** —— 见 §6。

### 8.2 推断（未实测，必须标明）

1. **真机轮的读数会怎么变**：本批没有引擎、没有轮次，所以「下一轮遇到写冻结视图会以 `ok=false` 收场」
   是**机制推断**，不是实测；本批能证明的是**离线夹具下**的运行路径。
2. **`\` + 非转义字符在 GDScript 字符串里是解析错误还是合法文本**：我没有引擎可验证；本批只证明了
   **注释**里的 Windows 路径是合法文本（这是误报那一侧的事实），字符串一侧的判定沿用「GDScript 的转义表」这一语言事实。
3. **`FILE_OPERATION_ATTEMPTS = 10 × 25 ms` 对真实 Windows 共享冲突是否足够**：**推断**。本批只证明了预算
   被正确执行、且耗尽仍是错误（§5）。
4. **`.godot/**`、`.import/**` 的写通道在真机轮里是否真的会被角色用到**：**推断**（机制上可行，实测在本批的
   离线夹具里可见，但没有真机轮数据）。
5. **「干净行边界截断」在真机轮里的发生概率**：未知；本批只声明它不在被抓住的类里。

### 8.3 明确未关闭的开放项（按 D295(c) 带入下一批或留档）

| id | 内容 | 本批处置 |
|---|---|---|
| DR86A-3a | `.tscn`/`.gd` 在干净行边界被截断（括号平衡）不被抓 | **声明**（§3.2，附语法理由与「不用括号规则」的理由） |
| DR86A-3b | `.gd` 没有整文档/平衡规则（尾巴式碎片） | 同上 |
| DR86A-5 | `.godot/**`、`.import/**` 仍是不被检测的写通道 | **声明**（§3.3，附检出建议） |
| DR86A-6 | `audit_tree` 静默跳过非 UTF-8 审计候选 | **未改**（§3.4，建议在调用方记 warning 而不是 finding） |
| §5 遗留 | modified 文件的**留证** `copy` 不在重试包装内 | **保留**并登记（§5 末） |
| DR86A-1 | 本报告之前的闸门数字缺失 | **关闭**：§6 给出强制重建后的字面读数 |

---

## 9. 我没有检查／没有做的事

- 未启动、重启或驱动引擎；未跑任何轮次；未联网；未 stage／commit／push。
- 未写 `runs/**`、未写任何 workspace 目录；未改任何报告（除本报告）、未改冻结规格、未改 `DECISIONS.md`、
  未改 `godot-mcp/**`、未改引擎二进制。
- 未对真机轮的 PNG、T16 的分析脚本、T16A-5..9 五条 minor/info 做复核（DR-86 报告已如实标注它们未被重核，本批沿用）。
- 未验证 `cargo` 之外的构建配置（未加任何依赖，`Cargo.toml`/`Cargo.lock` 哈希未变即为证据）。
- 未复核 DR-86 那份**追加式更正**本身（本批不改它；它的密封测试仍在套件里，见 §6 的绿跑）。
