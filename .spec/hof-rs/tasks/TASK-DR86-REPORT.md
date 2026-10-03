# TASK-DR86-REPORT — 交付边界上的**碎片写检测**、**每一次可写重试都带诊断**、**运行中游戏端点容忍一次传输抖动**、**冻结视图不再以「契约违规且无门判决」收场**，以及 **TASK-SMOKE-T16-REPORT.md 的追加式更正**

- 角色：**实现子代理（全新，无上游对话上下文）**；任务书 = 本批次派发方的完整提示词（自包含）
- 落点：`F:\moonbit-hof-rs`；**离线**：未启动引擎、未跑轮次、未联网、未 push、我**自己未 commit**
- 起点 HEAD：`98485529617ad5facae5e1ea14d1dcb38e14b6c9`（`origin/master` = `55a075194505e0f4a6d3e913a41e29880ea302e4`，**未推送**）
- **本批的改动由派遣方（不是我）提交为两笔**：`ccc0356`（`fix(dr86): detect a truncated product write, …`，18 文件 +2696/−70）与 `6a55d21`（`docs(d295): …`，含独立验收件、我那份报告的较早修订、我在 08:07 之后的 3 文件加固补丁，以及 `DECISIONS.md` 的 D295——**D295 不是我加的**）。我这一批**从未** stage／commit／push；当前工作树唯一与我有关的改动就是**本报告的最终修订**，因此若要钉住读数，请用 §7.1 的逐文件哈希与 §8 的日志，而不是「工作树 = 某次提交」
- 未写 `runs/**`、未写任何 workspace 目录、未改 `DECISIONS.md`／冻结规格／引擎树／依赖清单（§9 的机械自检）
- 所有多行辅助脚本都写在仓外：`C:\Users\wyl\AppData\Local\Temp\t16facts\`（`facts.py`、`append_correction.py`、`plant.py`、`gate_driver.py`、`selfcheck.py`、`summarize.py`、`newest.py`）

---

## 0. 这一批修了什么（每条给出它建立的**性质**）

| # | 变更 | 建立的**性质** | 关键落点 |
|---|---|---|---|
| 1 | **交付件的「整文档」审计** | 一个角色**不能**交付一个「内容是自己想写的东西的截断碎片」的文件、而流水线仍把它当作已交付：碎片在交付边界被**点名**（warning＋`warnings.log`），并作为**门自己的理由**（`artifact_integrity:`）把 `launchable` 判否；检查由**类**驱动，不硬编码那 20 字节 | 新增 `src/runtime/integrity.rs`；接线在 `src/runtime/run_loop.rs` |
| 2 | **每一次能写产物的重试都拿到诊断** | wrap-up 重试的提示词不再是「立刻写」这一句：Planner／Developer／Tester 的每一次 wrap-up 都携带**逐字**缺陷列表（Developer 用适配器实测的缺陷，Planner/Tester 用上一次被拒的 schema issues）；repair 重试另外拿到完整性审计 | `invoke::wrap_up_context`、`schema::issue_lines`、`Adapter::developer_artifact_defects` + `godot::developer_artifact_defects_in`、`run_loop.rs` 三处 wrap-up 与 repair context |
| 3 | **运行中游戏家族容忍一次传输抖动** | 一个**从未应答**的端点在**就绪窗口**内不再是「两次传输失败即判死」：容忍上界 `COLD_START_DEATH_THRESHOLD = 6`（可导出、有界）；窗口由就绪轮询自己开/关；真的一直不应答仍在第 6 次失败后**诚实**判死（`transport_failures_at_mark=6`，拒绝文本照旧 `game_endpoint_unavailable`） | `src/tools/endpoint.rs`、`src/tools/mod.rs`、`src/tools/reliable.rs` |
| 4 | **冻结视图不再以「契约违规且无门判决」收场** | 一个角色往冻结视图里写之后，运行时会：**检测**（照旧）、从 `A_t` 不可变快照**恢复**冻结字节、把角色写的字节**留证**（added 移走、modified 先复制再覆盖，**从不删除**）、并把轮次推进到**门判决**；恢复无法完成才响亮失败，且此时连**真实门判决**也会随失败一起落盘 | 新增 `src/runtime/frozen_view.rs`；`run_loop.rs` 的 Tester 检测点；`FailureFacts.artifact_gate` |
| 5 | **轮次报告的追加式更正** | 独立验收指出的**四处事实错误**被追加更正，报告**原文的每一个字节与那个 `json` 机器块保持原样**（前缀 77319 B / sha256 `ee9d175d…`），更正本身被新增的 append-only 闸门钉住 | `.spec/hof-rs/tasks/TASK-SMOKE-T16-REPORT.md`、`tests/append_only_guard.rs` |

**没有放松任何东西**：判据 E1..E6、跳跃诚实规则、地面探针行为、门对「真产品缺陷 vs 基础设施」的分类、冻结规格，一律未改。第 1 条只会让门**更**严（它在电池之外**新增**一条真实缺陷理由，从不动 `editor_infrastructure_failures` / `banners` / `pre_existing_lines` 的分类）——但「更严」不是「更准」：独立验收指出它**会误报**一处（`.gd` 注释里的 Windows 路径被当作转义残渣），见 §11.2 DR86A-2，我把它当作**已知真缺陷**登记，而不是辩解。没有手写任何游戏，没有跑任何真机轮次。

---

## 1. 变更一：交付边界上的碎片写检测（`src/runtime/integrity.rs`）

### 1.1 检查是怎么从**可读到的失败**推出来的（而不是从这一个文件）

真机轮里的两个产物形状：

```text
runs/smoke-t16/iter-1/candidate/scenes/main.tscn   20 B   b'visible = false)  \r\n'
runs/smoke-t16/iter-1/candidate/scripts/main.gd    1192 B 5 处字面 \$
```

成因是可复算的：模型把 POSIX 命令交给 `cmd.exe`——一个带括号的命令组里含有 `Vector2(4000, 40)`，**坐标里的 `)` 提前关掉了这个组**，重定向只捕获了那一行的尾巴；而 heredoc 里的 `$` 被写成了 `\$`（GDScript 没有这个转义）。

所以检查问两个**类**的问题，任何「截断式 shell 构造」都会在其中一个上失败，对**任意**同类文件成立：

1. **整文档在不在？**（`.tscn`/`.tres`）
   - 没有 `[section ...]` 头 ⇒ 不可能是作者想交付的文档，只能是尾巴；
   - 括号/方括号/花括号深度不平衡（引号串与 `#` 注释之外）⇒ 文本被截断过，或覆盖它的碎片带着「截断它的那个构造」的收尾符——`visible = false)  ` 里的 `)` 正是 shell 命令组的收尾符。负深度即「多出一个收尾符」，正是这一类。
2. **文本是不是用目标语言写的？**（`.gd`）
   - `\` 后面跟的字符不在 GDScript 的转义字母表里（`n t r a b f v ' " \ / u` 与 8 进制数字）⇒ 这个反斜杠是**另一个 shell 转义的残渣**，不是 GDScript 作者会写下的内容。针是「非法转义」这个类，由语言的转义表算出。

**不是硬编码那些字节**：代码里没有 `visible = false)`、没有 `main.tscn`、没有「20 B」；`AUDITED_EXTENSIONS` 决定审计范围，转义表决定针。新增的 6 个单元测试用的都是**别的**碎片形状（`name = 12, y)  `、`[node name="Main"` 被剪断、`\$` 之外的非法转义），全文档与引号内括号必须被接受。

### 1.2 接线与判定

- **审计点**：Developer 阶段（含 wrap-up）结束后立刻审一次（**交付边界**，并把发现交给随后唯一一次 repair 调用）；repair 之后**再**审一次（最后一次可写重试之后）。
- **记录**：每条发现写进 `result.json.warnings`（逐字行）与 `runs/<id>/warnings.log`（`DR-86 delivered-artifact integrity:`）。
- **判否**：只要发现仍在，就把 `artifact_integrity: <path>:<line>: <token>: <detail>` **追加**进门 reasons，并令 `applicable=true`、`launchable=false`（若原本是 `gate_not_applicable`，那条关于**电池**的说明会被移除，避免「applicable=true 却携带 not-applicable 理由」的自相矛盾）。**只加不删**，分类不动。
- 修好之后（repair 写回整文档）发现消失，门恢复由电池判定——这不是放宽，因为审计是一条真实的项目缺陷检查。

---

## 2. 变更二：每一次能写产物的重试都拿到诊断

| 重试 | 改前携带 | 改后携带 | 证据 |
|---|---|---|---|
| Planner wrap-up | `WRAP_UP_RETRY_CONTEXT` ＋ shape 块（**上一次被拒的 issues 丢失**） | 逐字 issue 行（`[json] the planner artifact is missing …`）＋ shape 块 | `tests/write_integrity.rs::a_role_wrap_up_retry_is_handed_the_schema_issues` |
| Developer wrap-up（**就是写坏 20 B 场景的那一次**） | **只有**「STEP BUDGET EXHAUSTED … write the required artifact NOW」 | ＋ `developer_artifact_defects()` 实测的逐字缺陷（路径、磁盘字节数、缺失的 `[node …]`、`artifact_write_truncated` / `artifact_shell_residue`）＋「重写**整个**文件，不要只补一行」 | `a_developer_wrap_up_retry_is_handed_the_verbatim_defects` |
| Tester wrap-up | 只有指令 ＋ shape 块 | ＋ 上一次被拒的逐字 issues（`the tester artifact is missing` / `evidence is not valid JSON`） | `the_tester_wrap_up_retry_is_handed_the_schema_issues` |
| Developer **repair**（本来就有逐字失败电池列表） | 电池失败项 ＋ 门 reasons | ＋ 完整性审计逐字项 | `the_repair_call_is_handed_the_integrity_audit` |

- `wrap_up_context(&[..])` 在**没有**可引用缺陷时会**明说**「the runtime's own checks recorded no quotable defect」——不编造诊断。
- `developer_artifact_defects_in` 是**生产实现**（`GodotAdapter` 走它），不是测试替身：单元测试用真实现直接在碎片/残渣夹具上验证它点名了路径、磁盘字节数与类别。
- 「同一个诊断」是**同一类**：都是运行时自己量到的、逐字的缺陷列表；不再有「repair 有供词、wrap-up 只有命令」的不对称。

---

## 3. 变更三：运行中游戏端点容忍一次传输抖动

### 3.1 机制

- `EndpointLiveness` 新增两个**可加**字段（都 `serde(default)`，旧记录仍可解析）：`successes`（应答过几次；`0` 就是「从未应答」）与 `cold_start_grace`（当前是否处在就绪窗口）。
- `death_threshold()`：**就绪窗口打开 且 `successes == 0`** ⇒ `COLD_START_DEATH_THRESHOLD = 6`；**其它一切情况** ⇒ `ENDPOINT_DEATH_THRESHOLD = 2`（DR-55 原样）。
- 就绪轮询（`wait_for_ready_matching`）在进入循环前 `set_cold_start_grace(tool, true)`，在**每一条退出路径**上 `set_cold_start_grace(tool, false)`；`McpChannel` 把窗口**武装到该 tool 真正会用的那个端点**（用同一个 `client_for` 解析），所以窗口不可能落在别的地址上。
- **有界**：第 6 次连续传输失败即判死，`transport_failures_at_mark` 记真实次数，拒绝文本仍是 `game_endpoint_unavailable`，仍带 `UNAVAILABLE`／`attempt(s)=0`／`endpoint_state`。

上界的推导不是拍的：文档化的轮询间隔 `READY_POLL_INTERVAL_MS = 500`，6 次即「三秒的半秒轮询」——一个真的在启动的游戏进程打开它 MCP 监听端口的窗口。

### 3.2 本轮证据会变成什么样（**推断**，离线不可实测）

- 真机轮里那两次致命失败发生在 `editor_play_scene` 之后、**任何** `running_game_*` 成功之前，且恰好由就绪轮询发出（报告 §7.3 自己说 `play_scene_ready` 以 `game_endpoint_unavailable` 收场）。改后：轮询会**真的把这几次请求发出去**（而不是第二次失败就判死），`mcp-errors.jsonl` 里会多出**真实尝试**的逐次记录；若游戏只是慢了一瞬，第一个语义调用就会成功，E3 在轮记录里**可判**；若它真的一直不应答，端点在第 6 次后被诚实判死，E3 仍不可判，但**证据形状不同**——它现在能区分「从未应答（0 successes，6 次尝试）」与「还没来得及试就被判死（2 次失败、此后 `attempt(s)=0`）」。这是**推断**：本批离线，未跑轮次。
- **实测**（本批）：就绪窗口内 2 次失败不再判死；上界处判死且 mark 正确；窗口外 DR-55 两次判死不变；轮询确实开/关窗口。

---

## 4. 变更四：冻结视图里的写入被恢复、被留证，轮次仍被判决

### 4.1 机制（`src/runtime/frozen_view.rs`）

对候选视图与真实 workspace 各做一次：

1. 用运行时的排除规则量出差异（`.hoh/**` 是 Tester 的**合法**提交区，永不在范围内）；
2. `added`：**移走**到 `iter-N/tester-writes/<label>/<rel>`（rename，失败则 copy+remove）；
3. `modified`：**先复制**污染字节到 `iter-N/tester-writes/<label>/<rel>`，再从 `A_t` 快照覆盖回去（**留证**）；
4. `removed`：从快照复制回来（原文已不存在，无字节可留）；
5. 恢复后**再量一次**并用 `hash_tree` 确认等于 `candidate_id`；只要还有 `failures` 或哈希不等，就**响亮失败**——和改前一样——但此时 `FailureFacts.artifact_gate` 会把**真实门判决**一起写进 `result.json`。

### 4.2 建立的**性质**

- 一轮不再可能因为「某个角色写到了不该写的地方」而以 `reason=contract_violation` ＋ `artifact_gate.applicable=false` 收场（这正是 round 1 的形态：轮次因此**没有门判决**，而这正是这一轮存在的目的）。
- 写入事实仍然可见：`result.json.warnings` 里的 `qa_contaminated_candidate_restored` / `qa_contaminated_workspace_restored`、`warnings.log` 里的逐字 `added/modified/removed` 差异清单与留证路径，以及留证据本身。
- `FailureFacts.artifact_gate`：任何**电池之后**的失败（Tester 污染（恢复失败分支）、Tester schema 失败、QA 前 workspace drift）都不会再把已经真实产生的门判决替换成 `not_applicable` 存根。

> **尚未关闭（决策层裁决 D295(b)）**：本条把「写入被检测并恢复」与「轮次达标」拆开了——轮次可以 `ok=true`。`REQUIREMENTS.md` R4/R13 要求「QA 修改快照 ⇒ **拒绝**」，D295 因此裁定**裁回 `reject`**，并要求 E5 读 `qa_contaminated_*_restored` 警告来区分「没写」与「写了又恢复」。**下一批必须把这条改回拒绝**；本报告不假装它已经满足 R4/R13（见 §10.3 第③行与 §11.3）。

---

## 5. 变更五：`TASK-SMOKE-T16-REPORT.md` 的追加式更正

**这是追加，不是改写**：报告原文 77319 B、sha256 `ee9d175da22f7cf18c31570e31c4dfd807f3afaed7ccc0faf634e0b31381c6f9` **逐字节未动**（我先把原文件整份备份到仓外，改完再用 `sha256sum`＋`cmp` 证明）；`json` 机器块 25686 B、sha256 `06af46d5dfb05cf3c867b1c52a3828fd48ef5a254e894134c202c485b210b0ad` 同样未动。更正以**一个换行**开始，标题的 `#` 落在第 77320 字节；更正后整份文件 83492 B、sha256 `628c920ee7ebba8cb053d28cdfbd39b3550a7ec0d5178f8ce2fe4741a3e61baf`。

更正的四件事（每件都由我**自己**从原始件复算，而不是转述验收）：

| # | 原文（逐字保留在上面） | 我复算到的读数 | 复算方式 |
|---|---|---|---|
| ① | §7.2 `quarantine/ 不存在`；机器块 `"… no quarantine directory"` | `runs/smoke-t16/quarantine/deterministic-pass-1.stale-1790975400/` **存在**（`mcp-errors.jsonl`、`mcp-sync.json`、`raw/` 12 个 JSON）；`warnings.log` 第 3 行的 DR-69 行点名它 | `ls`；读 `warnings.log` |
| ② | §7.2 `第 1 次判定 project_defects_new=1 …` | 隔离的第一趟窗口是 `anchor_line_count=10`、`banners=1`、`editor_infrastructure_failures=5`、`pre_existing_lines=4`、**`project_defects_new=0`**，锚 `request_id=8`／判定 `12`，**没有** `main.tscn` 行；新的那一行只出现在第二趟（锚 `32 count=0`／判定 `36 count=1`）⇒ §9.2 的「DR-81 ① 基建豁免未在真机触发」**为假** | 读隔离 `raw/editor_errors_baseline.json`（4104 B / `6c065b85…`）与活体同文件 |
| ③ | §3.1／§10.3 `533c417d…` **13 文件/9757 B** | 独立重实现 `hash_tree`（`relpath\n{len}\n{bytes}\n`、`\`→`/`、序数排序、排除 `.hoh`）对归档快照算得 **`533c417d…` / 11 文件 / 7646 B**（逐文件清单见更正正文） | `facts.py` |
| ④ | §3.3①／§9.1① 「归档前逐字面路径删掉了三个游离文件」 | 归档里**仍有** `({type`（0 B）与 `Coins`（6 B，`2288\r\n`），**没有** `-p`；`ARCHIVE_MANIFEST.json` 129 项；`archive_round1.py` docstring 逐字 `No deletion happens here` | `ls`／读清单与脚本 |

更正同时**如实标注**：验收件另列的五条 minor/info（T16A-5..9）**我没有重新核对**，仍以验收件为准。新增两个 append-only 测试把这个密封钉住：`the_t16_report_keeps_its_review_revision_and_carries_the_dr86_correction` 与 `the_t16_seal_reddens_on_an_edit_above_it`（后者证明「密封之上改一个字节」变红、「密封之后继续追加」仍绿）。

---

## 6. 测试：真首红 vs 声明式改钉

### 6.1 新增测试（27 条）

| 文件 | 条数 | 覆盖 |
|---|---|---|
| `src/runtime/integrity.rs`（单元） | 6 | 碎片（另一形状也红）、整文档接受、剪断的整文档变红、非法转义 vs 合法转义、引号/注释内括号不计数、非审计扩展名不看 |
| `src/runtime/frozen_view.rs`（单元） | 3 | 留证＋恢复（含 modified 留证）、`.hoh` 不受影响、无法恢复时如实报 failure |
| `src/tools/endpoint.rs`（单元） | 3 | 有界容忍＋诚实 mark、应答过即回到两次判死、两字段可加且旧记录可解析 |
| `src/runtime/invoke.rs`（单元） | 1 | wrap-up 同时携带指令与逐字缺陷（无缺陷时明说） |
| `tests/write_integrity.rs` | 8 | 生产缺陷列表；门因碎片而关；Developer/Planner/Tester 的 wrap-up 诊断；repair 拿到审计；Tester 写冻结视图被恢复且轮次仍判；晚失败保留门判决 |
| `tests/cold_start_grace.rs` | 4 | 窗口内有界容忍（明确以 DR-55 的 2 次为对照）、窗口外不变、轮询开/关窗口、窗口武装在真实端点 |
| `tests/append_only_guard.rs` | 2 | T16 前缀＋机器块密封；编辑变红／追加仍绿 |

### 6.2 **真首红**（诚实登记）

本批的实现与测试是**同一轮**写下的，所以严格意义上的 TDD 首红只有下面这些，且**全部是测试侧的错误**（我按失败信息改的是测试，不是实现）：

- `tools::endpoint::tests::a_cold_start_grace_tolerates_a_bounded_streak_and_keeps_the_honest_mark`：首跑 FAILED（我把上界写成了「第 6 次仍活」，实际是「第 6 次判死」），按 `>=` 语义改正测试；
- `tests/write_integrity.rs` 首跑 3/8 红：`a_late_failure_keeps_the_gate_verdict_it_produced`（脚本步序漏了 repair 的那一次 Developer）、`the_production_adapter_names_the_fragment_and_the_foreign_escape`（我过度断言「同一路径至多两条缺陷」，实为三条**不同**缺陷）、`the_tester_wrap_up_retry_is_handed_the_schema_issues`（候选里有**空的** `.hoh/evidence.json` 占位，所以先走 DR-68 ①(b) 的环内 shape 重试）。三者都按运行时真实行为改测试。

**因此，这批测试的「不是空转」由 §7 的五个受控 plant 证明**：每个 plant 都让它自己的测试变红。

### 6.3 **声明式改钉**（3 条，全部在 `tests/evidence_binding.rs`，均无删除）

| 测试 | 改前钉的性质 | 改后钉的性质 |
|---|---|---|
| `rejects_contaminated_candidate` | Tester 写候选视图 ⇒ `Err(QaContaminatedCandidate)`，`failed_role=tester` | 写入仍被检出并逐字记录（`qa_contaminated_candidate_restored`＋差异清单），冻结字节恢复、污染字节留证，**轮次被判决** |
| `rejects_direct_real_workspace_write` | Tester 绝对路径写 workspace ⇒ 契约违规 | 同上（workspace 侧），并断言留证文件字节 |
| `contract_violation_reports_a_concrete_diff` | Tester 改深层真实文件 ⇒ 违规＋具体差异 | 改用 **Planner**（唯一仍会失败的只读角色路径）钉 DR-2「违规必须带具体差异」 |

改钉的理由：任务书第 4 条要求的性质与旧钉**不可同时成立**（旧钉要求「以契约违规收场」，新性质要求「不以契约违规收场且仍给出门判决」）。**没有删除任何测试**；`--list` 计数与 ignored 计数见 §8。

---

## 7. 受控 plant（5 个，每个只让它自己的测试变红，且逐字节还原）

每个 plant：`plant.py` 先把目标文件整份备份到 `C:\Users\wyl\AppData\Local\Temp\t16facts\plants\<name>.bak`，做**一处字面替换**，跑**指定测试**，然后 `shutil.copy2` 还原，并用 `cmp`＋`sha256sum` 证明与备份逐字节相同。

| plant | 锚（一处字面替换） | 目标测试 | 观测到的红 | 还原证明 |
|---|---|---|---|---|
| ① `integrity_gate` | `src/runtime/run_loop.rs`：`launch_gate.applicable = true;` → `… = launch_gate.applicable;` | `write_integrity::a_truncated_write_closes_the_gate_with_its_own_reason` | **FAILED**（`tests/write_integrity.rs:195`） | `cmp` 0；`42818ef3b214edc75c9984fcc7049ba860ae6997418ce90b1df2fb70cab2939e`（101427 B） |
| ② `wrap_up_diagnostic` | `src/runtime/run_loop.rs`：Developer wrap-up 的 `wrap_up_context(&adapter.developer_artifact_defects(..))` → 裸 `WRAP_UP_RETRY_CONTEXT` | `write_integrity::a_developer_wrap_up_retry_is_handed_the_verbatim_defects` | **FAILED**（`:252`） | 同上（`cmp` 0，`42818ef3…`） |
| ③ `cold_start_bound` | `src/tools/endpoint.rs`：`COLD_START_DEATH_THRESHOLD: u32 = 6;` → `= 2;` | `cold_start_grace::a_readiness_window_tolerates_a_bounded_cold_start_streak` | **FAILED**（`tests/cold_start_grace.rs:68`，即「上界必须严格宽于 DR-55」这一断言） | `cmp` 0；`cc35b5c928567f6922d2efbec66d1da67d7aac396df86ce080668fce98daa557`（34606 B） |
| ④ `restore_guard` | `src/runtime/frozen_view.rs`：`let after = tree_manifest(root, excludes)?;` → `let after = before.clone();` | `write_integrity::a_tester_write_into_the_frozen_view_is_restored_and_the_round_is_judged` | **FAILED**（`:409`） | `cmp` 0；`5e7965cd6f79ad88389ccea859a5fc575242319ae557e01826ec8e82716bd8de`（13661 B） |
| ⑤ `report_seal` | `TASK-SMOKE-T16-REPORT.md`：密封前缀里的 `quarantine/ 不存在` → `quarantine/ 存在X` | `append_only_guard::the_t16_report_keeps_its_review_revision_and_carries_the_dr86_correction` | **FAILED**（`:313`，密封偏移/哈希不符） | `cmp` 0；`628c920ee7ebba8cb053d28cdfbd39b3550a7ec0d5178f8ce2fe4741a3e61baf`（83492 B） |

plant ⑤ 就是「追加式更正自身」的非空转证明；此外新增的 `the_t16_seal_reddens_on_an_edit_above_it` 在**内存副本**上再证一次「密封之上改一字节变红、密封之后追加仍绿」，并断言真实报告未被该测试改写。

### 7.1 plant 之后的两件事（如实登记）

1. **还原是当时的读数**：上表每一个 `cmp 0`＋sha256 都是 plant **当时**对目标文件的取值。此后我为修掉 §8.1 的那次抖动，又对 3 个文件做了**有意**编辑，所以当前工作树的 sha 与备份不同：
   - `src/runtime/frozen_view.rs` = `fdd9fbc5e92ece8324f190f1769483dc45b9b0c9ad6cf20fc3692f1988d52daf`（plant 时为 `5e7965cd…`）
   - `src/runtime/run_loop.rs` = `ab72e55d59a1260fa7184adb6d854d194e92278fa71a51187f7c9b77d210054e`（plant 时为 `42818ef3…`）
   - `tests/write_integrity.rs` = `e5388370524c754fc8385ffdef0d2890e1f7453b5cf961f7129588d1b9f0e9d7`
   - 未变的：`src/tools/endpoint.rs` = `cc35b5c9…`、`src/runtime/integrity.rs` = `88a61519…`、`tests/cold_start_grace.rs` = `4d2e8355…`、`tests/append_only_guard.rs` = `6dfc2a07…`、`TASK-SMOKE-T16-REPORT.md` = `628c920e…`
2. **提交与我无关，且提交发生了两次**：`ccc0356`（本批改动）与 `6a55d21`（独立验收件＋D295＋我那份报告的较早修订＋3 文件加固补丁）都是派遣方打的。我这一批**没有** stage／commit／push。验收子代理随后在同一 HEAD 上复核，其结论与遗留项见 §11.2，派遣方的裁决见 §11.3（D295）。

---

## 8. 闸门（gate）：数字与**字面退出码**

（本节由 `C:\Users\wyl\AppData\Local\Temp\t16facts\gate_driver.py` 在仓外驱动，整份日志 = `gate_log.txt`，63 行 `test result` 头）

- **强制重建**（清指纹目录用 Python 的 `glob` + `shutil.rmtree`，再按 `git ls-files "*.rs"` **逐个** `os.utime`）：
  - `CLEARED_FINGERPRINTS=126`（`target/debug/.fingerprint/hof-rs-*`）
  - `TOUCHED_TRACKED_RS=101`（= `git ls-files "*.rs" | wc -l` 的 101；清单头 `src/adapter/engine.rs, src/adapter/godot.rs, src/adapter/mod.rs`）
  - 重建证据：同一份日志第 130 行 `Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)`
- **`cargo test --offline` 的字面退出码**：`LITERAL_CARGO_TEST_EXIT=0`（日志末行，由 `echo $?` 原样写入，**不是推断**）
- **汇总**（`summarize.py` 对同一份日志求和 63 个 `test result` 头）：**passed 629 / failed 0 / ignored 7**，`error` 行 0 条
- **`cargo test --offline -- --list` 的计数**：**636**（= 629 + 7，与实际执行的 636 个用例一致；独立再跑一次得同值）
- **`cargo fmt --all --check` 的字面退出码**：**0**
- **与基线对照**：基线是 **602 passed / 0 failed / 7 ignored、listing 609**；本批新增 **27** 条测试（§6.1 的 6+3+3+1+8+4+2），`629 − 27 = 602`、`636 − 27 = 609`，**ignored 仍为 7**，无测试被删。
- **执行器上限的处理（按要求明写）**：前台调用有 10 分钟上限，会切断长跑；我因此把整次运行放在**脱离终端**的进程里完成，**同一份日志、同一个构建**继续，字面退出码与 `Compiling` 行都在其中。本节的数字就是那一次完成后的读数。

### 8.1 抖动登记（第一次全量跑不是绿的，我如实写）

- 第一次强制重建后的全量运行：`LITERAL_CARGO_TEST_EXIT=101`，`passed 628 / failed 1 / ignored 7`，唯一红的是 `write_integrity::a_tester_write_into_the_frozen_view_is_restored_and_the_round_is_judged`（错误为 `contract violation: QaContaminatedCandidate`，即**恢复未验证通过**那条响亮失败分支）。
- 单跑该测试（`--nocapture`）**通过**；把 `write_integrity` 整个二进制连跑 **3** 次，**3 次全绿**（8/8，190.86 s / 192.01 s / 92.97 s）⇒ 判定为 **Windows 文件操作抖动**（刚写完的文件短暂被别的句柄占用，`rename`/`copy` 失败），不是逻辑错误。
- 处置（这正是「环境问题不得改变判定」的落点）：`frozen_view.rs` 对 `rename`/`copy`/`remove` 加**有界重试**（10 次 × 25 ms）＋失败时在 `run_loop.rs` 里输出**残余差异**（`added/modified/removed` 清单）；`tests/write_integrity.rs` 在该测试失败时打印警告与日志以便下次自我解释。加固后**重跑强制重建的全量套件 = 绿**（本节上面的数字）。

---

## 9. 禁止触碰区域的机械自检（全部为**我**这一批的动作，均在离线、只读或仓外写入范围内）

| 项 | 读数 | 结论 |
|---|---|---|
| `runs/**` | `find runs -type f` = **7341** 个文件；最新 mtime `2026-10-03 05:47:27`（`runs/smoke-t16/evidence/round/evidence_refresh.txt` 与 `COPY_MANIFEST.txt`），**全部早于本批开始（约 06:5x）** | 我未写 `runs/**`（walk 覆盖全部 7341 个文件，取最新 5 条） |
| workspace 目录 | 未创建、未写入；测试全部用 `tempfile` 的临时根（`.workspace` 下 836 个文件的 mtime 均早于本批） | ✓ |
| `.spec/hof-rs/PRD-mario.md` | `4c81c3a9…` （未改） | ✓ |
| `DECISIONS.md` | 我未改；派遣方在 `6a55d21` 追加 **D295**，当前 sha256 `2a4326ec7d53df6b2e9c22a31139a2c79d92f765b32125bc9c60dd51e52b7fd5`（我这一批读到的值是 `245befb7…`，那是我未改动的证据） | 我未改 ✓ |
| `.spec/hof-rs/REQUIREMENTS.md` | `298a9489…`（未改） | ✓ |
| `Cargo.toml` / `Cargo.lock` | `e0c4992b…` / `d98fa915…`（未改；**未加依赖**） | ✓ |
| 引擎树 `godot-mcp/godot` | HEAD `fc63af77c33368c4a1bb839c95d19750554f63a3`，`git status --porcelain` **0 字节** | ✓ |
| 引擎二进制 | `08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a` 194216960 B（未改） | ✓ |
| 未跟踪松文件 | `l.json`/`p2.json`/`pv.json`/`r.json` 仍是 T14 遗留的 `??`，未动 | ✓ |
| git | 我这一批**未 stage／未 commit／未 push**；派遣方提交了 `ccc0356`（本批 18 文件）与 `6a55d21`（验收件＋D295＋报告的较早修订＋3 文件加固补丁）；`origin/master=55a075194505e0f4a6d3e913a41e29880ea302e4` **未变**（未推送）；工作树唯一与我有关的改动是**本报告的最终修订** | ✓ |
| 危险动作 | 全程未用 `rm -rf`（只用过 `rm -f` 删仓外临时日志）；未从「未展开的变量」构造路径（全部字面量＋Python `os.path.join`）；未用 `git checkout --` 还原任何文件（还原只从仓外**字节备份**做，并用 `cmp`＋`sha256sum` 证明） | ✓ |
| 网络/引擎 | 未联网、未启动引擎、未跑轮次 | ✓ |
| 本报告自身 | 本节读数取自 `selfcheck.py` 的第二次运行：`runs/**` 7341 个文件最新 `05:47:27`、`.workspace` 836 个文件最新 `05:10:29`，均早于本批（约 06:5x 起） | ✓ |

对报告的追加式改钉做了一处例外说明：`tests/round_artifacts_sidecar.rs` 每次运行都会把一个被跟踪的 sidecar **逐字节同内容**重写（任务书已注明要忽略这种 churn）；`git status` 里它**不出现**，说明确实是同字节重写。

---

## 10. 残留风险：**实测**与**推断**分开，以及三条成因在真机上还剩多少暴露

### 10.1 实测（本批，离线夹具/替身）

1. 碎片/残渣类在交付边界被点名并关掉门（单元＋整轮测试；plant ① 证明该测试非空转）。
2. 三类 wrap-up 重试与 repair 都携带逐字诊断（plant ②）。
3. 就绪窗口内 2 次传输失败不判死、第 6 次判死且 mark=6、窗口外 DR-55 不变、轮询开/关窗口（plant ③）。
4. Tester 往冻结视图写：字节恢复、污染字节留证、轮次仍给出判决；晚失败保留真实门判决（plant ④）。
5. 报告更正为纯追加：前缀 77319 B / `ee9d175d…` 与机器块 25686 B / `06af46d5…` 未动（plant ⑤＋单元证）。

### 10.2 推断（未实测，必须标明）

1. **真机轮的证据形状**：§3.2 说「轮询会真的把请求发出去、E3 可能变成可判」——这是机制推断；本批没有引擎、没有轮次。
2. **游戏进程为何在首个语义调用前死掉**：仍未插桩（T16 报告自己的未定项）。本次改动**不**解释死因，只保证「死之前先真的试过、并且失败计数可读」。
3. **模型会不会不再写出 POSIX 语法**：本次**没有**去拒绝/归一化 POSIX 构造，也**没有**给 Developer 一个一等文件写入工具（那是 T16 验收给下一批的建议①）。因此「模型仍可能写出碎片」是推断中仍然成立的。

### 10.3 三条成因在真机上**仍会暴露**的部分

| 成因 | 现在关闭了什么（实测） | 真机仍可能暴露的部分（推断/边界） |
|---|---|---|
| ① wrap-up 重试**无诊断** ⇒ 写坏产物 | 提示词不再无诊断：三类 wrap-up＋repair 都带逐字缺陷；碎片在交付边界被点名并作为门理由 | 根因（POSIX-in-`cmd.exe` 的写入方式）未消除：模型仍可能写出碎片或转义残渣；运行时只能在**交付边界**检出并判否，不会「阻止写下」。若某次碎片落在**非审计扩展名**的文件上（例如无扩展名或 `.md`），本次检查**不看**它；**另外三处由独立验收指出的缺口**也必须并列读：`.gd` 没有整文档/平衡规则、只在行边界被剪断且括号平衡的文件抓不到（DR86A-3）、**注释里的 Windows 路径会被误报为残渣从而误关门**（DR86A-2，真缺陷，建议下一批立即修）。这些都是有意的保守范围与已知缺陷，不是遗漏 |
| ② 端点在首次成功应答前被判死 ⇒ E3 不可判 | 就绪窗口内、从未应答的端点容忍到 6 次；此后诚实判死；窗口开/关与端点解析都有测试 | 若游戏进程**真的**不应答（或监听端口在就绪**截止之后**才打开），E3 依旧不可判——这是保留的诚实失败，不是修好；死因仍未插桩；另外，**窗口之外**的两次失败仍按 DR-55 判死（有意保留），所以「首次语义调用恰好落在窗口外且连续两次传输失败」仍会丢证据 |
| ③ Tester 写冻结视图 ⇒ 契约违规且无门判决 | 检测＋恢复＋留证＋继续判决；恢复失败时也带上真实门判决 | 守卫是**检测并撤销**，不是文件系统级只读：窗口内角色仍可以真的写下文件（随即被移走/覆盖）。`removed` 路径的污染字节**无法**留证（文件已不存在）；恢复依赖 `A_t` 快照可读，若快照本身损坏/权限不足，轮次会响亮失败（此时门判决会随失败落盘，而不是消失）。**两处由独立验收指出**：被排除路径（`.godot/**`、`.import/**`）仍是写进冻结视图的通道，哈希与守卫都看不见（DR86A-5）；「写了又恢复」之后 E5 的哈希**分不出**「没写」，只有 `qa_contaminated_*_restored` 警告披露（DR86A-4，**D295(b) 已裁回 `reject` 并要求 E5 读该警告**，见 §11.3） |

### 10.4 本批没有做的事（不隐藏）

- 没有给 Developer 一等「整文档写入」工具，也没有在工具通道层拒绝/归一化 `cmd.exe` 下的 POSIX 构造（T16 验收的建议①）——本次只做「交付边界可检出、重试有诊断、门理由更精确」。
- 没有跑真机轮、没有启动引擎、没有对 `runs/smoke-t16` 的 PNG 做像素级复核、没有重跑 T16 的验收脚本。
- 没有对验收件列出的 T16A-5..9 五条 minor/info 做独立复算（更正里已如实标注）。

---

## 11. 本批之后发生的并行事件（对本报告的可信度有直接影响）

### 11.1 全量套件里的那次抖动

见 §8.1：第一次全量跑红一条（`write_integrity` 的冻结视图恢复测试），单跑与连跑 3 次均绿，判定为 Windows 文件操作抖动；已用**有界重试＋残余差异诊断＋测试自解释**加固，加固后的强制重建全量套件为绿。这段历史保留在报告里，因为「第一次不是绿的」本身就是要读的事实。

### 11.2 派遣方并行的独立验收（`TASK-DR86-ACCEPTANCE.md`，`pass_with_defects`）

验收子代理在我收尾时对 **commit `ccc0356`**（= 本批改动，未含 §8.1 的加固补丁）出了 `pass_with_defects`：五条头条性质都独立复现，没有承重判据失败；同时列出 8 条缺陷。我把它们原样登记，并给出我的处置（**派遣方的裁决见 §11.3**）：

| id | 验收指出的问题 | 我的处置 |
|---|---|---|
| DR86A-1 | 本报告 §8 当时没有数字，且本批日志里没有一次跑完的绿跑 | **本版已修**：§8 现在给出 `LITERAL_CARGO_TEST_EXIT=0`、629/0/7、listing 636、fmt 0、强制重建证据；§8.1 登记了那次红 |
| DR86A-2 | `.gd` 的非法转义检查**不看注释/字符串**：注释里写 Windows 路径 `# see C:\Users\dev\project` 会被判 `artifact_shell_residue` 并**误关门** | **确认为真缺陷**（我的检查过严、会拒绝无缺陷工程）。修法是复用 `blank_literals` 的注释/字面量规则。**此处不动**（再改会把工作树推得更远，DR86A-8）；**D295(c) 已把它带入下一批** |
| DR86A-3 | 覆盖类比报告的措辞窄：只在行边界被剪断且括号平衡的 `.gd`/`.tscn` 抓不到；`.gd` 没有整文档/平衡规则 | **确认**；§10.3 只披露了「非审计扩展名」这一条缺口。**D295(c) 带入下一批** |
| DR86A-4 | **判据语义变化**：Tester 写冻结视图后轮次可为 `ok=true`，而 `REQUIREMENTS.md` R4/R13 写「QA 修改快照 ⇒ 拒绝」；且 E5 的 `candidate_id == hash_tree(candidate)` 再也分不清「没写」与「写了又恢复」 | **必须由决策层裁决**——**已裁决（D295(b)）：裁回 `reject`，E5 必须读恢复警告**；本报告 §4 的 `ok=true` 语义因此**尚未关闭**，见 §11.3 |
| DR86A-5 | 被排除路径（`.godot/**`、`.import/**`）仍是写进冻结视图的通道：哈希与守卫都看不见 | **确认**（有意为之的缓存排除），§10.3 已补写。**D295(c) 带入下一批** |
| DR86A-6 | `audit_tree` 静默跳过读不成 UTF-8 的文件（UTF-16／BOM／二进制垃圾）——与碎片同形却无发现 | **确认**：这是「静默跳过」的坏味道。建议下一批把「审计候选但不可读」变成一条**找到**（finding），而不是 `continue` |
| DR86A-7 | 本批没有 `DECISIONS.md` 条目 | **已由派遣方在 `6a55d21` 以 D295 关闭**（任务书禁止我改 `DECISIONS.md`，所以这从来不是我的动作） |
| DR86A-8 | 验收期间工作树移动：3 个文件带未提交改动（`frozen_view.rs`、`run_loop.rs`、`write_integrity.rs`，即 §8.1 的加固） | **确认**：那是**我**在 08:07 之后的加固补丁（不是 plant；plant 全部在仓外副本上跑并逐字节还原），现已被 `6a55d21` 收进提交。因此 **§8 的数字属于「`ccc0356`＋加固补丁」= `6a55d21` 的源码状态**；§7.1 的逐文件哈希可把两者分开 |

### 11.3 派遣方的裁决（`DECISIONS.md` **D295**，由派遣方写入，不是我）

- (a) 本批作为「四条成因的修复」**落地，不否决**（验收独立复现了类驱动而非钉死、四类可写重试都带逐字诊断、冷启动阈值对冻结证据成立、更正是纯追加且 77319 B 前缀 `cmp` 一致而机器块未动）。
- (b) **DR86A-4 被裁回 `reject`**：Tester 写冻结视图**不得**以 `ok=true` 收场；**E5 必须读恢复警告**（`qa_contaminated_*_restored`）来区分「没写」与「写了又恢复」。⇒ **本报告 §4 描述的 `ok=true` 语义将在下一批被改回**，我的实现保留检测＋恢复＋留证，但轮次判定要回到「拒绝」。**这一条是本报告最重要的「尚未关闭」项。**
- (c) **DR86A-2（`.gd` 注释误报）、DR86A-3（干净行边界截断）、DR86A-5（被排除目录）** 带入下一批。
- (d) **缺失的闸门数字（DR86A-1）要重跑并公布** —— **§8 就是这一条的答复**：强制重建后的全量套件 `LITERAL_CARGO_TEST_EXIT=0`、629/0/7、listing 636、fmt 0，抖动与处置见 §8.1。
- 派遣方同时把「在实现者仍在写仓库时提交并派发验收」记为自己的流程错误（D295 末段），并指出并发 cargo 运行曾把本批的闸门日志截断重写——本报告 §8 的数字因此是在**验收结束之后**重新跑出来的。

---

## 12. 一句话交给决策层

本批把三条成因里**能在流水线侧关闭的两条**关到了「性质」层面（交付边界的碎片点名＋门理由；就绪窗口内的有界容忍；冻结视图的恢复＋留证＋门判决），把第三条的**根因**（模型把 POSIX 交给 `cmd.exe`）留在原地并如实标注；同时，独立验收指出我的新检查**过严一处**（DR86A-2 误报，下一批修）、**过窄几处**（DR86A-3/5/6，下一批）、以及一条**已由 D295 裁定的判据语义**（DR86A-4：裁回 `reject`，E5 读恢复警告——**这条本轮尚未关闭**）。闸门数字（D295(d)）已在 §8 补齐：强制重建后 `cargo test --offline` 字面退出码 0、629 passed / 0 failed / 7 ignored、listing 636、`cargo fmt --all --check` 0。这些都不该被报告的一句「已修好」盖掉。
