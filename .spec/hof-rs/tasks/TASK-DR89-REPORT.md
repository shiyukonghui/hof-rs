# TASK-DR89-REPORT — 修回完整性审计的碎片回归、更正那句假证成、声明工作区缓存残留、建模回车用例、追加 E5 注解、重跑闸门

- 角色：**实现子代理（全新，无上游对话上下文）**；任务书 = 本批次派发方的完整提示词（自包含）
- 落点：`F:\moonbit-hof-rs`；起点 HEAD `3c0cdf7f670122aad5efdfaf0b4379e45cbcc764`（`origin/master` 仍 `55a075194505e0f4a6d3e913a41e29880ea302e4`，`ahead 12`，**未推送**）
- **离线**：未启动/重启/驱动引擎，未跑任何轮次，未联网；**未写 `runs/**`、未写任何 workspace 目录**
- 未改 `DECISIONS.md`、`.spec/hof-rs/PRD-mario.md`（冻结的 S）、引擎树 `godot-mcp/**`、`src/adapter/godot.rs`、`Cargo.toml`/`Cargo.lock`、`config/hoh.yaml`；**未加依赖**；**未 stage／commit／push**
- 所有多行辅助脚本与日志都在仓外：`C:\Users\wyl\AppData\Local\Temp\t16dr89-impl\`（`summarize.py`、`gate.py`、`backup.py`、`finalize.py`、`probe.py`、`zzz_probe89.rs`、`plants.py`、`forbidden.py`、`testsets.py`、`verify.py`、`checks.py`）
- **全程未用 `rm -rf`**（清指纹只用 Python `glob` + `shutil.rmtree`，路径**逐个先打印**；探测用的旧导出一律 `shutil.rmtree` 于**先打印**的仓外路径）；**未用 `git checkout --`**；未从「未展开的变量」构造路径；**每次编辑/还原后都 `os.utime`**，plant 前后都断言「工作树字节 == 字节快照」

---

## 0. Summary for the dispatcher (English)

| # | Dispatched task | What was done | Property established |
|---|---|---|---|
| 1 | **Fix the regression (highest priority)** | The DR-88 carry is kept (it is what closes `X9`), and a literal **still open at the end of the text** is now reported as `artifact_write_truncated` – not by a second, per-line delimiter scan, because the text-resource reader accepts a newline inside a string, so a per-line scan would need a false premise and keeps a measured false positive. | The five truncation findings the DR-88 acceptance measured as lost (`B2/B3/B3b/B5/B5b`) are back, and the audit's silence on an unterminated literal (`C25/C26/C27`, DR88A-5) is **fixed**: 0 → 1 on each. Measured three-point (parent `ab95c65` / DR-88 `52d73d3` / worktree): `B2 1/0/1`, `B3 1/0/1`, `B5 1/0/1`, `B5b 1/0/1`, `C25 0/0/1`, `C26 0/0/1`, `C27 0/0/1`. The two false positives DR-88 removed stay clean (`L2 1/0/0`, `L3 1/0/0`, `L9 1/0/0`), and the intended tightenings stay strict (`X4/X6/X7/X10 = 1`, `X9 0/1/1`, `X3 0/1/1`). |
| 2 | **Correct the false justification** | The clause "the round of record's `\$` residue landed inside string literals" is **deleted** from the production doc, from `TASK-DR88-REPORT.md` §3, and from the test comment that repeated it. The reason now rests on the escape-processing class. | The corrected comment/report agree with the artifact: `runs/smoke-t16/iter-1/candidate/scripts/main.gd` lines 8–12 are five **unquoted** `@onready var … = \$HUD/…` expressions (verified verbatim by script), so a rule that skipped string literals would still have caught all five. Pinned by a new test that transcribes those five lines and asserts no quote on any of them. |
| 3 | **Declare the workspace-side residual** | Declared in §4, and in the appended E5 annotation: the write watch covers the **frozen candidate view** only (built by the runtime, the Tester's cwd, no other writer), so a write through the **same** configured cache excludes inside the real workspace stays invisible. | The declaration names the reasoning (the workspace caches have a non-role writer – the user's long-running editor, D294) and the consequence: `ok=true` with no `qa_*` warning is still possible for a workspace-cache write, so E5's compliance reading is "over the hashed set and the excluded paths **inside the candidate view**", never "no write at all". |
| 4 | **Model the carriage-return case; report the unterminated-literal silence as fixed or declared** | The CR **character** (`'\r'`) is in the escape alphabet (the tokenizer's `case '\r':` accepts a backslash followed by a lone CR); the unterminated-literal silence is **fixed**, not declared. | `C1` (lone CR after `\` in a string) measured **1/1/0** – the false positive is gone with the rule's own authority. `C25/C26/C27` measured **0/0/1**. |
| 5 | **Append a correction to the criteria document** | A D289-style note is **appended** to `REQUIREMENTS.md`; the sealed prefix (20,910 B / `7b551ca0…`) is byte-identical, and its offset still reads exactly 20,910. | A new test pins the annotation as a whole-line heading, asserts the sealed E5 row survives verbatim above it, and proves the seal non-vacuous in memory; plant `P7` proves it on the real bytes (edit inside the prefix → `append_only_guard` red, exit 101; restore byte-identical; control green). |
| 6 | **Pure summarisers over raw logs** | Every number in §8 comes from `summarize.py`, a **pure function of one raw log file**; the driver's narration goes to a different file, never into the evidence path; re-running it twice on the same bytes returns the same tuple (asserted in-process). | The literal exit codes are published raw (`LITERAL_CARGO_TEST_EXIT=0` for both the baseline and the final run, taken as `subprocess.returncode` with `PROCS_BEFORE=NONE` / `PROCS_AFTER=NONE`), and both raw logs re-derive to the published counts. |
| 7 | **Do not weaken anything** | Only 4 files changed (§10), plus this report; no criterion, jump rule, gate classification, rejecting semantics or frozen specification changed; the legacy adapter and its tree are untouched; no game hand-written; no round run. | The 4 changed files are: `src/runtime/integrity.rs` (audit), `tests/append_only_guard.rs` (one added pin), `.spec/hof-rs/REQUIREMENTS.md` (append only), `.spec/hof-rs/tasks/TASK-DR88-REPORT.md` (the false clause corrected in place). |

Gate: baseline I reproduced myself **literal exit 0 / 644 passed / 0 failed / 7 ignored / 62 suites / `--list` 651 / `fmt` 0**; after this batch **literal exit 0 / 648 / 0 / 7 / 62 suites / `--list` 655 / `fmt` 0**, forced rebuild (63 fingerprint dirs cleared + 101 tracked `.rs` touched), `648 + 7 = 655`, no test removed (`REMOVED=0`, `ADDED=4`), `#[ignore]` attributes still 7. Seven controlled plants, each green-control / exit-101 / byte-exact restore / green-control. `PLANTS THAT DID NOT BEHAVE: []`.

---

## 1. 结论速览

| # | 任务 | 处置 | 落点 |
|---|---|---|---|
| 1 | 修回回归（最高优先） | **修回**：文本末尾仍未闭合的字面量按 `artifact_write_truncated` 报告；**未**退回「逐行分隔符扫描」那条路（该路需要一条假语言规则，且实测保留一条误报） | `src/runtime/integrity.rs` |
| 2 | 更正假证成 | **删掉并改对**：代码 doc、DR-88 报告 §3、测试注释三处都改；并加一条把「那五处残渣在未加引号的代码里」变成可执行事实的 pin | `src/runtime/integrity.rs`、`.spec/hof-rs/tasks/TASK-DR88-REPORT.md` |
| 3 | 工作区缓存残留 | **声明**（附理由与对 E5 读数的后果），**不**靠监视工作区关闭 | 本报告 §4、`REQUIREMENTS.md` 追加注 |
| 4 | 回车用例 / 未闭合字面量 | 回车**建模**（`C1` 1→0）；未闭合字面量的沉默**修好**（`C25/26/27` 0→1） | `src/runtime/integrity.rs` |
| 5 | 判据追加注解 | **追加**（D289 式），封印前缀逐字未动；附非空转 plant | `.spec/hof-rs/REQUIREMENTS.md`、`tests/append_only_guard.rs` |
| 6 | 纯函数汇总 + 字面退出码 | **重做**：`summarize.py` 是单一 raw 日志的纯函数；驱动叙述与证据路径分离 | 仓外脚本、本报告 §8 |
| 7 | 不放松任何东西 | 逐项自检通过（§10） | — |

---

## 2. 任务 1：回归的处置 —— **修回，而不是声明**

### 2.1 三条修订上的同一份探针（实测，不是推断）

探针 `zzz_probe89.rs` 直接调用生产 `audit_text`，同一份 case 表在三个修订上各跑一次：
`ab95c65`（DR-88 之前）、`52d73d3`（DR-88 落点，验收判 fail 的修订）、工作树（本批）。
每个修订用 `git archive` 导出到仓外目录，并各自使用**独立的 `CARGO_TARGET_DIR`**（见 §10.2 的工具事故）。

| case | 形状 | parent `ab95c65` | DR-88 `52d73d3` | DR-89 工作树 | 读数 |
|---|---|---|---|---|---|
| **B2** 未闭合 **raw** 字面量掩盖其后的 `\q` | `.gd`: `var s = r"abc`⏎`var p = \q` | 1（shell@2） | **0** | **1**（trunc@1） | 回归**修回** |
| **B3** `.tscn` 未闭合引号后面的碎片尾巴 | header + `name = "abc` + `visible = false)  ` | 1（trunc@3） | **0** | **1**（trunc@2） | 回归**修回** |
| **B3b** 只写了 `name = "abc` | header + `name = "abc` | 0 | 0 | **1**（trunc@2） | 新增发现（同一类） |
| **B5** `.tres` 未闭合引号后面的碎片尾巴 | `[gd_resource …]` + `name = "abc` + `value = 1)  ` | 1（trunc@3） | **0** | **1**（trunc@2） | 回归**修回** |
| **B5b** `.tres` `name = "x` + `name = 12, y)  ` | 验收的另一个变体 | 1（trunc@3） | **0** | **1**（trunc@2） | 回归**修回** |
| **C25** `.gd` 在字符串里被切断 | `var s = "abc` | 0 | 0 | **1**（trunc@1） | DR88A-5 **修好** |
| **C26** `.gd` 在 raw 字面量里被切断 | `var s = r"abc` | 0 | 0 | **1**（trunc@1） | DR88A-5 **修好** |
| **C27** `.gd` 在三引号字面量里被切断 | `var s = """abc` | 0 | 0 | **1**（trunc@1） | DR88A-5 **修好** |
| **C1** 字符串内 `\` 后孤立 CR | `var s = "a\`＋CR＋`b"` | 1（误报） | 1（误报） | **0** | DR88A-4 **修好** |
| **L2** raw 字符串里的 Windows 路径 | `r"C:\Users\dev\project"` | 1（误报） | 0 | 0 | 不倒退 |
| **L3** 合法 `\U0001F600` | | 1（误报） | 0 | 0 | 不倒退 |
| **L9** raw 三引号含 `\d`/`\U`/`#` | | 1（误报） | 0 | 0 | 不倒退 |
| **N1** `.tscn` **合法**多行字符串里含 `)` | `text = "line1`⏎`line2)"` | 1（误报） | 0 | 0 | **不被 per-line 扫描重新引入** |
| **X3** 位数不足的 `\uZZZZ` | | 0 | 1 | 1 | 不倒退 |
| **X4 / X6 / X7 / X10** 字符串内的外来逃逸 | | 1 | 1 | 1 | 不倒退 |
| **X9** 续行字符串的下一行以 `#` 开头 | `"abc\`⏎`#c\q"` | 0 | 1 | 1 | 不倒退 |
| **B1** 未闭合**非 raw** 字面量 + 其后的 `\q` | | 1（shell@2） | 1（shell@2） | **2**（trunc@1 + shell@2） | 更严（多报一条碎片） |
| **B7 / B8** 注释里的引号 | | 0 | 0 | 0 | 不倒退 |
| **D4** `.tscn` 注释里有撇号 + 不平衡 closer | | 1 | 1 | 1 | 不倒退 |
| **R1** 记录轮那五行的单行形状 | `@onready var coins_label: Label = \$HUD/Coins` | 1 | 1 | 1 | 不倒退 |

**读法**：DR-88 的回归是「跨行携带未闭合字面量」把文件余下部分**整段涂白**，于是碎片守卫在自己存在的类别里丢了发现。本批把「文本结束时字面量仍开着」本身判为**碎片**，因此 `1 → 0 → 1` 恢复，且 `C25/C26/C27` 这类从未被报告的形态也一并关闭。**没有**退回 per-line 扫描，因此 `N1` 那条「合法多行资源字符串含 `)`」的误报（parent 实测 1）没有被重新引入。

### 2.2 为什么**不**用「逐行分隔符扫描」这条路（并给出语言依据）

任务书允许该路，但要求「命名支持它的语言规则」。**没有一条真规则支持它**，证据是引擎源码本身：

- `core/variant/variant_parser.cpp` 的字符串分支（`:277-296`）只在读到流终止符时才报错：
  `if (ch == 0) { r_err_str = "Unterminated string"; … }`，`else if (ch == '"') { break; }`——
  **换行不是终止符**，它被当作字符串内容累计。
- 该分支读的流是**按字节的原始流**：`VariantParser::StreamFile::_read_buffer`（`:74-88`）
  `f->get_buffer(temp, p_num_chars)` 后逐字节装填，`StreamFile::_is_eof` 只看 `f->eof_reached()`——
  没有任何「按行」的切分。

因此「`.tscn`/`.tres` 的字符串必须在本行闭合」是**假**的，逐行扫描会把
`text = "line1`⏎`line2)"` 这种**reader 接受**的文档判成碎片。实测（§2.1 `N1`）：parent `ab95c65`
正是这样一条误报（1），DR-88 与本批为 0。用一条假语言规则去修回归，正是本批被派来清除的缺陷类别，
所以本批选的是「未闭合字面量即碎片」这条路——它的依据是**两个 reader 自己的报错**：

- `GDScriptTokenizer::string()` 在 `_is_at_end()` 时 `return make_error("Unterminated string.")`；
- `variant_parser.cpp` 的 `'"'` 分支在 `ch == 0` 时 `r_err_str = "Unterminated string"`（`:283-286`），
  其 `\u`/`\U` 循环在 `:322-326` 同样报 `Unterminated string`。

两个 reader 都拒绝「文件在字面量里结束」，所以这样的文本**不可能**是「整篇文档」——它只能是长写的前缀。

### 2.3 修复的内容

- 新增 `unterminated_literal(text) -> Option<(usize, OpenString)>`：用**与其它规则同一条**携带式
  `scan_line` 走完全文，返回「仍开着的字面量 + 它的起始行」。
- `LexerState` 增加 `opened_line`，`scan_line` 增加 `line_number` 参数（把开引号的行记在状态里）。
- `audit_text` 对**所有受审扩展名**先问「整篇文档在不在」：未闭合字面量 → `IntegrityKind::TruncatedFragment`
  （token 仍是 `artifact_write_truncated`），detail 引用上述两条 reader 规则。
- 顺带修正了一处**不忠实于 tokenizer** 的越位：DR-88 的 unicode 分支在位数不足时 `index += 2 + digits`，
  会**越过**本该闭合字符串的那个引号（于是同一行里合法的收尾引号被吞掉）。tokenizer 在遇到非十六进制位时是
  `push_error` 后 **`break` 而不前进**，把该字符留给外层循环。现改为 `hex_digit_run()`：只吃掉实际存在的
  十六进制位，遇到第一个非十六进制字符就停下。这是新测试在开发中暴露出来的（`"\U0001F"` 一条畸形转义
  一度同时产生「碎片」与「转义」两条 finding），已按引擎行为改齐：现在仍是**恰好 1 条**。

### 2.4 这次修复**不可以**主张的东西（诚实边界）

- `B3/B5` 的**发现数**与**类别 token** 恢复了，但**检出规则换了**：parent 由「速度行分隔符扫描」报出
  （行 3），本批由「未闭合字面量」报出（**行 2**，即字面量开启的那一行）。这不是逐字复现 parent，是**同类发现**。
- `B2` 的 parent 把 `\q` 报成 `artifact_shell_residue`，本批报成 `artifact_write_truncated`：
  在一份「在 raw 字面量里结束」的文本中，`\q` 按语言根本不是转义，把它叫 shell 残渣才是误判；**碎片**是正确读数。
- `B1`（未闭合**非 raw**）从 1 条变 2 条（多一条碎片）：这是**更严**，不是放松。

---

## 3. 任务 2：更正那句假证成（引用冻结工件）

**冻结工件逐字**（`runs/smoke-t16/iter-1/candidate/scripts/main.gd`，第 8–12 行；脚本 `verify.py` 打印其
`repr` 与「是否含引号」的读数）：

```text
@onready var coins_label: Label = \$HUD/Coins
@onready var lives_label: Label = \$HUD/Lives
@onready var time_label: Label = \$HUD/Time
@onready var victory_label: Label = \$HUD/Victory
@onready var player: CharacterBody2D = \$Player
```

读数：这五行共有 **5** 处 `\$`；**没有任何一行含 `"` 或 `'`**（`quotes on any of them: False`）。
因此：

- **「跳过字符串字面量」会不会仍抓到这五处？——会，全部五处。** 它们是**未加引号的表达式**，落在
  代码分支（`scan_line` 的 `ch == '\\'` 一支），与字符串状态无关；本批新增的 pin
  `runtime::integrity::tests::the_round_of_records_residues_are_unquoted_expressions` 把五行逐字转写
  （脚本已核对转写与工件逐字节相同）并断言每行正好 1 条 `artifact_shell_residue`。
- **不跳过字符串的真正理由**只剩语言本身：GDScript 对**非 raw** 字面量确实处理转义
  （`case 'a'/'b'/…/'U'/'u'` 与 `default:` 的 `Invalid escape in string.`），所以外来逃逸**可以**落在
  字符串里——`X4`（`"#\q"`）、`X5`、`X7`（`'#\q'`）、`X10`（`"a\"\q"`）就是这一类；跳过字符串会让这条
  规则对它们失明。

**三处落点都改了**（原句保留在 DR-88 报告里只作为「被更正的原话」引用）：

1. `src/runtime/integrity.rs` 模块 doc：删掉「landed inside string literals」，改成
   「残渣是**未加引号**的五行；跳过字符串仍会抓到全部五处；必须能进入字面量的那一类才是理由」。
2. `.spec/hof-rs/tasks/TASK-DR88-REPORT.md` §3：原文「而 T16 那一轮的 `\$` 残渣正落在字符串里」→ 明确写成
   **该证据为假、由 DR-89 更正**，并逐字给出五行与「跳过字符串仍会全抓」。
3. `src/runtime/integrity.rs` 测试里那句「the residue is inside a string」的注释：改成「**字面量内部**的残渣
   仍被抓——那才是扫描字符串的理由」，并把它真正改成字符串内的对照（`var label = "\$HUD/Coins"`）。

> `TASK-DR88-REPORT.md` 没有测试 pin 它（`grep` 全仓只有 DR-88 验收引用它），所以是在原位更正而不是追加；
> 本批**声明**了这处编辑（见 §10.3），不隐藏。

---

## 4. 任务 3：工作区缓存 watch 的残留 —— **声明，不关闭**

**残留内容（DR88A-3）**：DR-88 引入的「被排除目录写」观察，只覆盖**冻结候选视图**（`candidate/<cache>/**`）。
同一套配置排除（`config/hoh.yaml` 的 `.godot`、`.import`）落在**真实工作区**（`.workspace/**`）时**不被观察**，
因此 Tester 往工作区缓存目录里的写仍可能读成一轮干净：`ok=true`、无 `qa_*` 警告、字节留在工作区、没有留证。
这一半**不在** DR-88 的残留表里，验收也点名要声明。

**为什么不靠「监视工作区」关闭它**：工作区里有**非角色写者**。D294 记录的机制是：用户的长期运行编辑器在
打开工程时会重建 `.godot/**`。本批期间该机制**再次被观察到**：

- `.workspace/**` 当前 **851** 个文件（DR-88 验收读到 836），最新 mtime `2026-10-03T16:44:24`
  （`.workspace/fresh-t16/.godot/scene_groups_cache.cfg`）；
- 该 mtime **早于本批的第一个写动作 3.5 小时**（本会话第一个仓外脚本 `summarize.py` 的 mtime 是
  `2026-10-03T20:11:56`；`checks.py` 读数 `now 2026-10-03T21:12`），所以**不是本批写的**；
- 本批没有对 `.workspace/**` 执行任何写命令，`runs/**` 最新 mtime 仍是 `2026-10-03T05:47:27`（未动）。

把 watch 扩到工作区，等于把**用户的编辑器**的写当成角色违规 → 会批量制造假红。**故不扩，只声明。**

**对判据（E5）的后果**：E5 的合规读数只能是「就 `hash_tree` 覆盖的集合、以及**候选视图内**被排除目录而言」，
**不能**是「字节级不可能有写」。工作区缓存目录里发生的写仍然能读成 `ok=true` 且无警告。
这一点已写进 `REQUIREMENTS.md` 的 DR-89 追加注（§6），使判据文本与代码读法一致。

---

## 5. 任务 4：回车用例（建模）与未闭合字面量（修好）

- **回车（DR88A-4）——建模，不是声明。** `GDSCRIPT_ESCAPES` 现在含**字符** `'\r'`（此前只有字母 `r`）。
  依据是 tokenizer 的 `case '\r':`：`if (_peek() != '\n') { result += ch; _advance(); break; }`——反斜杠后
  跟一个**孤立 CR** 是合法转义。实测 `C1`：parent 1 / DR-88 1 / 本批 **0**；反方向（`\q` 的 `"a\qb"`）
  仍是 1 finding，规则没被关掉。
- **未闭合字面量（DR88A-5）——修好，不是声明。** `C25/C26/C27` 实测 parent 0 / DR-88 0 / 本批 **1**；
  并且这正是任务 1 回归修复所依赖的机制（§2）。

---

## 6. 任务 5：判据文档的追加注解 + 封印 plant

**追加（D289 式，绝不改封印前缀）**：`.spec/hof-rs/REQUIREMENTS.md` 末尾新增
`# DR-89 注（追加式，2026-10-03）——E5 的读数已强于该行文本；追加不改封印前缀`，内容：
E5 的**实际读数**（`ok==true` 且 `qa_contaminated_*`、`qa_wrote_cache_*` 两族警告皆缺席；哈希相等只是必要条件）、
**为什么**（缓存排除不进 `hash_tree`，R10 要求 `version_id` 稳定 → 用非哈希清单观察 + 拒绝 + 留证）、
**边界与后果**（只覆盖候选视图；工作区不观察的理由 D294；后果 §4）、以及**封印读数**。

**逐字校验（`verify.py`）**：

| 量 | 读数 |
|---|---|
| 文件长度 | 26,491 → **28,690** B（追加 2,199 B） |
| DR-80 note 头部 offset | **20,910**（与 pin 相同，未移动） |
| 封印前缀 sha256 | **`7b551ca08c4c5abf15a95cb8edcc4977ce8d03c649654ab4a5ab01f649cae5ae`**（与 pin 相同） |
| DR-89 note 头部 offset | **26,492**（在封印之后） |
| 封印的 E5 行仍在注解之上逐字存在 | True |
| 全文件 sha256 | `4982bf1c1e6591cd10c44c0af60b934b7fee58ac8b1137cba1f162e5b5a41615` |

**先检查了 pin 再写**：`tests/append_only_guard.rs` 的 `REQ_PRE_DR80_BYTES/…_SHA256` 与
`REQ_DR80_HEADING` 就是这条封印；现有测试 `the_requirements_document_keeps_c3_and_carries_the_dr80_note`
在追加后仍绿（`seal_violations` 只比较 marker 之前的字节）。

**新增 pin**：`tests/append_only_guard.rs::the_requirements_e5_row_carries_its_dr89_annotation_and_the_seal_still_holds`
——断言注以整行头部存在、offset 在封印之后、封印行逐字存活、注里含 `qa_wrote_cache_`/`qa_contaminated_`/
`QaContaminatedCandidate`/`hash_tree`/`候选视图`/`工作区`/`7b551ca0`，并在**内存副本**上证明封印非空转
（改 E5 行首的一个字节 → `seal_violations` 非空；追加 → 仍空；真文件不被该测试写）。

**真实字节上的 plant `P7`**（§9）：把 REQUIREMENTS.md 偏移 100 的一个字节翻转 → 该测试 **exit 101**；
还原后 `byte_identical=True`（sha 回到 `4982bf1c`）且 control 再跑 **exit 0**。

---

## 7. 任务 6：汇总必须是 raw 日志的**纯函数** + 公布字面退出码

`C:\Users\wyl\AppData\Local\Temp\t16dr89-impl\summarize.py` 只做一件事：读**一个** raw 日志文件，用一条正则累加
`test result: …` 行，返回 `SUITES/PASSED/FAILED/IGNORED/RED_SUITES`；它不读驱动状态、不写文件、不查环境，
并在内部断言 `summarize(text) == summarize(text)`（同字节两次调用必须同结果）。
驱动 `gate.py` 的叙述写进 `<tag>.log`，**证据路径**只有 `<tag>.raw.txt`（`cargo test --offline` 的原始
stdout+stderr）与 `<tag>.list.txt`（`--list` 的原始输出）。**字面退出码**由
`subprocess.run(...).returncode` 原样写入，不靠推断。

复核（本轮重跑）：

```text
python summarize.py baseline.raw.txt  -> SUITES=62 PASSED=644 FAILED=0 IGNORED=7 RED_SUITES=0
python summarize.py final.raw.txt     -> SUITES=62 PASSED=648 FAILED=0 IGNORED=7 RED_SUITES=0
python summarize.py final.raw.txt     -> SUITES=62 PASSED=648 FAILED=0 IGNORED=7 RED_SUITES=0   (同字节，同结果)
```

这正是 DR-88 报告 §8 与 DR-88 验收 §9 各自登记过的同一类缺陷（driver 内联解析把 `PASSED` 读成 0）。
本批的汇总函数是**独立可重跑**的纯函数，因此即使驱动出错也不会污染已落盘的原始日志与退出码。

---

## 8. 闸门：基线、本批、字面退出码

两趟都用**仓库自己的 `target/`**、同一份驱动（`gate.py`）：Python `glob` 清
`target/debug/.fingerprint/hof-rs-*`（路径**逐个先打印**后 `shutil.rmtree`），再按 `git ls-files "*.rs"`
**逐个** `os.utime`。

| 读数 | 基线（本批自己复现） | 本批（工作树） |
|---|---|---|
| `FINGERPRINT_PATTERN` 命中 / 清除 | `hof-rs-*` / **63** | 同 / **63** |
| `TOUCHED_TRACKED_RS` | **101** | **101** |
| `cargo fmt --all --check` | `FMT_EXIT=0` | `FMT_EXIT=0` |
| `cargo test --offline -- --list` | `LIST_EXIT=0`，`LIST_TESTS=651`，`LIST_BENCH=0` | `LIST_EXIT=0`，`LIST_TESTS=655`，`LIST_BENCH=0` |
| **`cargo test --offline` 字面退出码** | **`LITERAL_CARGO_TEST_EXIT=0`** | **`LITERAL_CARGO_TEST_EXIT=0`** |
| 汇总（纯函数） | `SUITES=62 PASSED=644 FAILED=0 IGNORED=7`，`RED_SUITES=0` | `SUITES=62 PASSED=648 FAILED=0 IGNORED=7`，`RED_SUITES=0` |
| `passed + ignored == --list` | 651 | 655 |
| 全量 wall | 1157.0 s | 1109.6 s |
| 运行前后并发测试进程 | `PROCS_BEFORE=NONE`，`PROCS_AFTER=NONE` | `PROCS_BEFORE=NONE`，`PROCS_AFTER=NONE` |

- **强制重建的证据**：清指纹后的第一次 cargo 调用（`--list` 那次）第 1 行就是
  `   Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)`（`COMPILING_IN_LIST=1`）；全量运行**复用**该次编译出的
  二进制（`COMPILING_HOF_RS_IN_FULL_RUN=0`）。两趟都是同一形状。
- **没有测试被删除或改名**：用两趟 `--list` 原始日志做名字集合比对（`testsets.py`）：
  `REMOVED=0`、`ADDED=4`——新增恰为
  `runtime::integrity::tests::an_unterminated_literal_is_a_fragment_not_a_whole_document`、
  `…::a_lone_carriage_return_after_a_backslash_is_the_languages_own_escape`、
  `…::the_round_of_records_residues_are_unquoted_expressions`、
  `the_requirements_e5_row_carries_its_dr89_annotation_and_the_seal_still_holds`。
- **`ignored` 未变**：行首 `#[ignore` 属性在 `HEAD` 与工作树都是 **7**（都在 `tests/godot_smoke.rs`），
  与运行报告的 `IGNORED=7` 一致。
- **计数差**：`648 − 644 = 4 = 新增测试数`；`644+7=651`、`648+7=655`。
- 本批结束时 `tasklist | grep -cE "cargo|rustc|hof_"` = **0**：没有任何属于本批的测试进程还在跑。

---

## 9. 受控 plant（**7 个**：对照绿 → 植入红（101）→ 还原逐字节相同 → 对照再绿）

驱动 `plants.py`：每个 plant 只做**一处字面替换**（`P7` 是一个字节的翻转），只跑**一条**测试；开始前
断言工作树字节 == 字节快照（快照由 `finalize.py save` 在本批编辑**之后**取），编辑与还原后都 `os.utime`，
每个 plant 的「还原后」运行同时充当下一个 plant 的「植入前对照」。日志：
`C:\Users\wyl\AppData\Local\Temp\t16dr89-impl\plants_log.txt`。

| plant | 目标文件 | 一处替换 | 目标测试 | 对照 → 植入 → 还原 |
|---|---|---|---|---|
| `P1-raw-string-skip` | `integrity.rs` | `if open.raw {` → `if open.raw && false {` | `a_raw_string_processes_no_escapes` | 0 → **101** → 0 |
| `P2-unicode-digit-check` | `integrity.rs` | `if available < digits {` → `if false && available < digits {` | `the_escape_table_is_the_languages_own` | 0 → **101** → 0 |
| `P3-carried-string-state` | `integrity.rs` | `scan_line(raw, index + 1, &mut state).invalid_escape` → `…&mut LexerState::default())…` | `a_continued_string_keeps_its_hash_inside_the_string` | 0 → **101** → 0 |
| `P4-unterminated-literal` | `integrity.rs` | `unterminated_literal(text)` → `None::<(usize, OpenString)>` | `an_unterminated_literal_is_a_fragment_not_a_whole_document` | 0 → **101** → 0 |
| `P5-carriage-return-escape` | `integrity.rs` | 从字母表删掉 `'\r',` | `a_lone_carriage_return_after_a_backslash_is_the_languages_own_escape` | 0 → **101** → 0 |
| `P6-unquoted-residue-justification` | `integrity.rs` | `if index + 1 < count {` → `… && chars[index + 1] != '$' {` | `the_round_of_records_residues_are_unquoted_expressions` | 0 → **101** → 0 |
| `P7-sealed-prefix-edit` | `.spec/hof-rs/REQUIREMENTS.md` | 偏移 100 的字节翻转 | `the_requirements_e5_row_carries_its_dr89_annotation_and_the_seal_still_holds` | 0 → **101** → 0 |

汇总行：`RESULTS` 里 7 个 plant 全部 `planted_exit=101`、`restored_byte_identical=true`、
`control_green=true`；`PLANTS THAT DID NOT BEHAVE: []`。
每次还原都打印植入前的 sha256（`integrity.rs` 回到 `9b203999…`、`REQUIREMENTS.md` 回到 `4982bf1c…`），
收尾再用 `finalize.py verify` 断言三个文件的工作树 sha256 == 快照（全部 `equal`）。

---

## 10. 禁止区域自检、工具事故与轨迹

### 10.1 禁止区域（收尾读数，`forbidden.py`）

| 项 | 读数 | 结论 |
|---|---|---|
| `runs/**` | **7341** 个文件；最新 mtime `2026-10-03T05:47:27`（`runs/smoke-t16/evidence/round/evidence_refresh.txt`） | **未写**（与 DR-88 验收同值） |
| `.workspace/**` | **851** 个文件；最新 mtime `2026-10-03T16:44:24`（`.workspace/fresh-t16/.godot/scene_groups_cache.cfg`） | **非本批写的**：该 mtime 比本会话第一个写动作（20:11:56）早 3.5 小时；见 §4，它正是「工作区缓存有非角色写者」的证据 |
| `.spec/hof-rs/PRD-mario.md`（冻结的 S） | `4c81c3a9…`（未改） | ✓ |
| `DECISIONS.md` | `9f95f26e…`（未改；DR-88 报告里的 `2a4326ec…` 是 D296 追加前的值，HEAD 已前移到 `3c0cdf7`） | ✓ |
| `Cargo.toml` / `Cargo.lock` | `e0c4992b…` / `d98fa915…`（未改；未加依赖） | ✓ |
| `config/hoh.yaml` | `835b6b0e…`（未改） | ✓ |
| `src/adapter/godot.rs`（legacy 引擎适配器） | `27fda15a…`（未改） | ✓ |
| 引擎树 `godot-mcp/godot` | `git status --porcelain` **空**（0 字节） | ✓ |
| git | `HEAD=3c0cdf7…`、`origin/master=55a0751…`（ahead 12），**未 stage／commit／push** | ✓ 未推送 |
| 工作树 | 恰好 **4** 个 ` M`（本批的 4 个文件）+ 四个既有未跟踪松文件 `l.json`/`p2.json`/`pv.json`/`r.json`（未动）+ 本报告 | ✓ |
| 行尾 | 4 个改动文件全为纯 LF（`CRLF=0`） | ✓ |
| 危险动作 | 未用 `rm -rf`（清指纹/清旧导出只用 Python 打印后 `rmtree`）；未用 `git checkout --`；未从「未展开的变量」构造路径 | ✓ |
| 网络/引擎 | 未联网、未启动引擎、未跑轮次、未手写游戏 | ✓ |

### 10.2 工具事故（如实登记）：共享 `CARGO_TARGET_DIR` 让三点探针**第一次**读回陈旧二进制

第一次三点探针让三个修订共用一个 `CARGO_TARGET_DIR`，结果三份日志**逐字相同**，且都等于 parent 的行为
（`L2=1`、`X9=0`）——即 DR-88/本批的编译产物根本没被用上：cargo 复用了先前根目录编译出的 `hof_rs`。
这正是任务书警告的「陈旧二进制」类别。处置：**每个修订一个独立 `CARGO_TARGET_DIR`**，并加两条判别断言
（`L2` parent 必须 1、DR-88/工作树必须 0）。修正后的读数见 §2.1（`L2 1/0/0`、`B3 1/0/1`）。
**教训**：跨修订比较时，「三条日志一样」本身就是可疑信号，必须用一条已知会变的 case 当判别器。

### 10.3 其它轨迹

- 第一次 `plants.py` 立刻失败（`integrity.rs is not the byte backup`）：那份快照是**编辑前**的字节。
  已改为在编辑**之后**用 `finalize.py save` 取快照（`integrity.rs 9b203999…`、`REQUIREMENTS.md 4982bf1c…`），
  并在每个 plant 前断言相等。**没有**任何还原失败或半途状态。
- 本批就地更正了 `TASK-DR88-REPORT.md` 一句假证据（§3）。该文件**没有**测试 pin 它，所以不涉及封印；
  本报告显式声明这处编辑，不假装「未改任何报告」。
- 未复核 DR-88 验收报告的其它结论；只读它取缺陷清单与判据。

---

## 11. 残留风险：**实测**与**推断**分开

### 11.1 实测（本批，离线）

1. 回归修回且未引入 per-line 假规则：三点探针 §2.1（`B2/B3/B3b/B5/B5b` 恢复；`N1` 仍 0）。
2. 误报不倒退：`L2/L3/L9` 在本批为 0；`C1` 由 1 变 0。
3. 收紧不倒退：`X3/X4/X6/X7/X9/X10` 各 1；`R1` 为 1。
4. 未闭合字面量沉默修好：`C25/C26/C27` 各 1。
5. 判据追加注：封印前缀 offset/sha 逐字未动（20,910 / `7b551ca0…`），新 pin 绿，`P7` 承重。
6. 闸门：强制重建下 `cargo test --offline` 字面退出码 **0**、**648 / 0 / 7**、62 suites、`--list` 655、`fmt` 0；
   `REMOVED=0 / ADDED=4`；`#[ignore]` 7。
7. 7 个 plant 全部自洽（对照绿 / 植入 101 / 还原逐字节相同 / 对照再绿）。
8. `.workspace/**` 的最新写来自**非角色写者**（mtime 早于本会话第一个写动作 3.5 小时）——对 §4 是对证。

### 11.2 推断（未实测，必须标明）

1. **真机轮里的行为**：本批没有引擎、没有真机轮，所以「下一轮某个被切断的 `.tscn` 会被报成碎片」是机制推断，
   实测只在离线探针与仓内测试上。
2. **新增的碎片发现会不会误伤真机产物**：合法文档不会以未闭合字面量结束（两个 reader 都会报错），
   所以推断为不会；但本批**没有**对真机产出的 `.tscn`/`.tres` 语料跑过 audit（离线 corpus 与全量套件均绿）。
3. **`B1` 从 1 条变 2 条**：推断为「更严而非生态噪声」，未在真机验证。
4. **hex-digit-run 的忠实性**：按 `gdscript_tokenizer.cpp` 的 `break`（不前进）改齐，已用 `"\U0001F"`
   与 `"\uZZZZ"` 的用例实测为 1 条；未在真机 tokenizer 上对拍。
5. **工作区缓存写**：机制（watch 只覆盖 candidate）是实测（DR-88 夹具）；「真机轮里是否真会发生」是推断。

### 11.3 明确未关闭的开放项

| id | 内容 | 本批处置 |
|---|---|---|
| DR88A-3 | 工作区侧被排除目录不被观察 | **声明**（§4 + 判据注），**不**监视工作区（D294） |
| DR86A-3a/3b | 干净行边界截断、`.gd` 尾巴式碎片 | **未改**（不在本批任务书内） |
| DR86A-6 | `audit_tree` 静默跳过非 UTF-8 候选 | **未改**（同上） |
| DR87A-6 | 报告里两处数字不吻合（126 vs 63、9 vs 7） | 本批独立复现为 **63** 与 **7 ignored** |
| DR88A-5 | 从不报告未闭合字面量 | **关闭**（§2、§5） |
| DR88A-4 | 字符串内孤立 CR 被误拒 | **关闭**（§5） |
| DR88A-1 | 替换后的理由为假 | **关闭**（§3） |
| DR88A-2 | 跨行携带并非严格更严（碎片类丢发现） | **关闭**（§2，实测三点） |

---

## 12. 我没有做的事

- 未启动/重启/驱动引擎；未跑任何轮次；未联网；未手写任何游戏；未 stage／commit／push。
- 未写 `runs/**`、未写任何 workspace 目录；未改 `DECISIONS.md`、`PRD-mario.md`（冻结规格）、
  `godot-mcp/**`、引擎树、`src/adapter/godot.rs`、`Cargo.toml`/`Cargo.lock`、`config/hoh.yaml`。
- 未新增或删除任何测试（只新增 4 条；逐名集合比对 `REMOVED=0 / ADDED=4`；`ignored` 仍 7）。
- 未改任何判据、跳跃诚实规则、门对真缺陷与基建的分类、冻结视图的拒绝语义；`REQUIREMENTS.md` 只在末尾追加。
- 未做任何 `rm -rf`、未用 `git checkout --` 还原、未从「未展开的变量」构造路径。
- 在仓内只做过：4 个文件的编辑、清 `target/debug/.fingerprint/hof-rs-*`（gitignore 的构建缓存，路径先打印）、
  按 `git ls-files` 逐个 `os.utime` 101 个跟踪的 `.rs`、以及写本报告。
