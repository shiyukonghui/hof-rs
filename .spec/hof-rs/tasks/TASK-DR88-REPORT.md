# TASK-DR88-REPORT — 让完整性审计按 GDScript 自己的词法规则判定、更正那句假证成、观察被排除目录的写、并重跑闸门

- 角色：**实现子代理（全新，无上游对话上下文）**；任务书 = 本批次派发方的完整提示词（自包含）
- 落点：`F:\moonbit-hof-rs`；起点 HEAD `ab95c6521febf7969ce8ae06568ec0ddf501e59a`（`origin/master` 仍 `55a0751`）
- **离线**：未启动/重启/驱动引擎，未跑任何轮次，未联网；**未写 `runs/**`、未写任何 workspace 目录**
- 未改 `DECISIONS.md`／`REQUIREMENTS.md`／`PRD-mario.md`／`Cargo.toml`／`Cargo.lock`／引擎树／引擎二进制；**未加依赖**；**未 stage／commit／push**
- 所有多行辅助脚本与日志都在仓外：`C:\Users\wyl\AppData\Local\Temp\t16dr88\`（`gate.py`、`summarize.py`、`backup.py`、`install.py`、`plants.py`、`no_removed_tests.py`、`forbidden.py`、`lineendings.py`）
- 清指纹目录用 Python `glob` + `shutil.rmtree`（**路径逐个先打印后删除**）；**全程未用 `rm -rf`**、未用 `git checkout --`、未从「未展开的变量」构造路径；**每次编辑/还原后都 `os.utime`**，并在 plant 开始前**断言「工作树字节 == 字节备份」**

---

## 0. Summary for the dispatcher (English)

| # | Dispatched task | What was done | Property established |
|---|---|---|---|
| 1 | Stop refusing legitimate GDScript | The `.gd` escape rule is now a lexer with carried state: **raw** literals (`r"…"`, `r'''…'''`) are not scanned for escapes, **`\UXXXXXX`** is in the alphabet, and `\u`/`\U` must be followed by exactly 4/6 hex digits. `/` and the octal digits `0..7` were removed from the alphabet (the tokenizer's `default:` rejects them). | The two false positives the acceptance reproduced (`L2` raw Windows path, `L3` `"\U0001F600"`) return **0 findings**; the converse (a foreign escape in code) is still caught, pinned by the acceptance's own `X4/X5/X6/X7/X10` and by new cases. |
| 2 | Fix the false statement | The claim "a GDScript string must close on its own line" was **deleted** and replaced by the true reason (a non-raw string *does* process escapes, so it is content), **and** the rule was changed to carry the open literal across lines. | "String is content" now rests on the language's escape processing, not on a false lexicon fact; a `#` on a continued string's next line opens no comment. |
| 3 | Escape positions | **Closed:** `X1` backslash immediately before the comment marker, `X3` incomplete `\u`/`\U`, `X9` escape in a string continued onto a `#` line. **Declared:** `X8` escapes in a `.tscn`/`.tres` string (the resource parser accepts `\` + *any* character — no foreign-escape class exists there), and `X2` a trailing backslash in code (the tokenizer's own line continuation). | Each decision cites the engine source; declared positions are pinned by a test that states the declaration. |
| 4 | Excluded-path write | **Detected and required.** The adapter's configured cache excludes are observed by a separate, non-hashed manifest taken on both sides of the QA window; a difference is preserved as evidence, recorded as `qa_wrote_cache_candidate`, and **rejects** the round. `E5` now requires `ok == true` *and* the absence of both write-token families. | A clean-looking round with live Tester bytes in `.godot/**` can no longer be read as compliant; `hash_tree`/`version_id` are untouched (R10). |

Baseline I reproduced myself: `cargo test --offline` literal exit **0**, **633 passed / 0 failed / 7 ignored**, 62 suites, `--list` **640**, `cargo fmt --all --check` exit **0**, forced rebuild (63 fingerprint dirs cleared, 101 tracked `.rs` touched). After this batch: literal exit **0**, **644 / 0 / 7**, `--list` **651** (11 added, 0 removed, 0 renamed). Six controlled plants, each reddening its own test and restored byte-exactly (`restored byte-identical=True` + sha256).

---

## 1. 结论速览

| # | 任务 | 处置 | 落点 |
|---|---|---|---|
| 1 | 不再拒绝合法 GDScript | **关闭**：raw 字符串不处理转义；`\UXXXXXX` 加入；`\u`/`\U` 位数必须齐；`/` 与 `0..7` 移出字母表 | `src/runtime/integrity.rs` |
| 2 | 那句假证成 | **删掉并改对**（同时改了规则本身：字符串状态跨行携带） | `src/runtime/integrity.rs` 模块 doc |
| 3 | 四个看不见的逃逸位置 | **关三个**（X1/X3/X9）、**声明两个**（X8/X2，各附语言依据与一条 pin 测试） | `src/runtime/integrity.rs` |
| 4 | 被排除目录的写 | **检出并让判据要求它缺席**（独立非哈希观察 + 留证 + 拒绝 + E5 读数 + 文档口径更正） | `src/runtime/policy.rs`、`src/runtime/run_loop.rs`、`src/runtime/frozen_view.rs`、`tests/godot_smoke.rs`、`tests/evidence_binding.rs` |
| 5 | 不放松任何东西 | 判据文本／跳跃诚实规则／地面探针／门对真缺陷与基建的分类／冻结视图的拒绝语义／冻结规格**均未改**；见 §6 | — |
| 6 | 闸门 | **重跑并公布**（强制重建后的字面退出码与汇总，见 §5） | — |

---

## 2. 变更一：审计现在按 GDScript 自己的词法规则判定

`src/runtime/integrity.rs` 原先逐行扫描、**每行独立**、只有一个 20 字符的转义表。现在它是一台**跨行携带状态的按行词法器**：`scan_line(line, &mut LexerState) -> LineScan { code, invalid_escape }`，其中 `code` 是把字符串字面量与注释一起涂白的同一长度掩码（括号规则与转义规则共用它），`LexerState` 携带「上一行结束时仍未闭合的字面量」。

每一条规则都用本仓引擎源码作依据（`godot-mcp/godot/…`，即我们自己那支构建），不是「像不像」：

| 规则 | 语言依据（逐字） | 建立的性质 |
|---|---|---|
| **raw 字面量不处理任何转义** | `modules/gdscript/gdscript_tokenizer.cpp` `GDScriptTokenizer::string()`：`if (_peek(-1) == 'r') { is_raw = true; … }`，随后 `if (is_raw) { … result += '\\'; }` —— 反斜杠是普通字符 | `L2`（`r"C:\Users\dev\project"`）与自造的 raw 三引号（含 `\d`、`\U0001F600`、`#`）都返回 0 findings |
| **`\UXXXXXX` 是语言定义的转义**（旧表漏了 `U`） | 同文件 `case 'U': case 'u': { int hex_len = (code == 'U') ? 6 : 4; … }` | `L3`（`"\U0001F600"`）返回 0 findings |
| **unicode 转义必须带满 4/6 位十六进制** | 同处逐位读 `hex_len` 个字符，遇非十六进制就报 `Invalid hexadecimal digit in unicode escape sequence` | `X3`（`"\uZZZZ"`）、`"\U0001F"` 各自成 finding |
| **代码里的 `\` 只能是行继续** | 同文件 `scan()`：`if (c == '\\') { … if (_peek() != '\n') { return make_error("Expected new line after \"\\\"."); } … }` | `X1`（`\` 紧跟注释标记 `#`）被抓；`\` 在行尾仍然合法（`X2` 声明） |
| **字符串可以跨行**：`\`+换行是显式续行，三引号按定义跨行，且 tokenizer 对普通字面量也不会在换行处收尾 | 同文件 `string()`：`case '\n': newline(false); valid_escape = false;`（继续读）与 `is_multiline` 的三引号分支 | `X9` 关闭；三引号里的「像注释的行」是字符串内容 |
| **`/` 与 `0..=7` 不是 GDScript 转义** | 同文件 `default: … make_error("Invalid escape in string.")`——旧表把它们当合法，是错的 | 收紧（不是放松）：`"a\/b"`、`"\0"` 现在各成 finding |
| **`.tscn`/`.tres` 不套用这张表** | `core/variant/variant_parser.cpp` 字符串分支的 `default: { res = next; }`——反斜杠后**任何**字符都被原样接受 | `X8` 声明为非缺陷类（见 §2.3） |

**误报关闭（实测，即验收用的那两条 + 我自己的一条）**

| 用例 | 规则前 | 现在 |
|---|---|---|
| `L2` `extends Node\n\nvar p = r"C:\Users\dev\project"\n` | 1 finding（误报） | **0** |
| `L3` `var e = "\U0001F600"\n` | 1 finding（误报） | **0** |
| 自造 `var re = r'''\d \U0001F600 # x\nmore'''\n`（raw 三引号 + 反斜杠 + 注释标记） | 误报 | **0** |

**反方向（converse）仍然成立**：`\Users`、`\$`（T16 形状）、`\z`、`"#x" + \y`、`X4`（`"#\q"`）、`X5`、`X6`、`X7`、`X10`、`"C:\Users\dev"`（**非** raw）各自**恰好 1 条** `artifact_shell_residue`。其中「非 raw 的 Windows 路径」是故意加的对照：它与 `L2` 只差一个 `r`，证明跳过的是 **raw 字面量**这个语言构造，不是「长得像路径的字符串」。

---

## 3. 变更二：那句假证成——**我两者都做了**

原 `integrity.rs` 模块 doc 第 39–42 行写着：

```text
A quoted *string* is deliberately not skipped: it is real executable
content (a GDScript string must close on its own line), and the round of
record's `\$` residue landed inside string literals, …
```

- 「a GDScript string must close on its own line」与 `code_span` doc 里「a parse error in its own right」**被删除**：引擎 tokenizer 的 `string()` 循环在普通字面量里遇到换行只是 `newline(false)` 后**继续读**，`\`+换行是显式续行，三引号按定义跨行。
- **改后的证成**：字符串是**真实可执行内容**，因为 GDScript 对**非 raw** 字面量确实处理转义（`case 'a'/'b'/…/'U'/'u'`，以及 `default:` 的 `Invalid escape in string.`），所以外来转义**可以**落在字符串里（X4/X5/X7/X10 这一类），跳过字符串就会让这条规则对那种残渣失明——**这才是**「跳过字符串」不可取的理由。**本报告原先在此处写的证据是假的：** 「T16 那一轮的 `\$` 残渣正落在字符串里」**不成立**（已由 DR-89 更正，DR88A-1）：那五处残渣**不在**字符串里，而是 `scripts/main.gd` 第 8–12 行五个**未加引号**的 `@onready var … = \$HUD/…` 表达式（冻结副本 `runs/smoke-t16/iter-1/candidate/scripts/main.gd`，逐行无引号字符），所以「跳过字符串字面量」仍然会抓到全部五处。
- **同时改了规则本身**：`LexerState` 把未闭合字面量带到下一行（不是「只改措辞」）。这正是 `X9` 关闭、以及三引号里 `#` 不再被当成注释的实现基础。

所以答案是：**证成被改对，且规则被改；二者都做，不是二选一。**

---

## 4. 变更三：逃逸位置——哪条关、哪条声明

| 位置（验收编号） | 处置 | 依据 |
|---|---|---|
| **X1** 反斜杠紧跟开启注释的 `#`（`var a = 1 + \#c`） | **关闭**（1 finding） | 代码里的 `\` 只有 `\`+换行合法；`\#` 触发 `Expected new line after "\"` |
| **X3** 不完整的 unicode 转义（`"\uZZZZ"`） | **关闭**（1 finding） | 需满 4/6 位十六进制 |
| **X9** 被续行的字符串里、下一行以 `#` 开头时的转义（`"abc\`↵`#c\q"`） | **关闭**（1 finding，第 2 行） | 续行后仍在字符串里，`#` 不开启注释 |
| **X8** `.tscn`/`.tres` 字符串里的转义（`note = "C:\Users\dev"`） | **声明为非缺陷类** | `variant_parser.cpp` 的 `default: res = next;`：反斜杠 + 任意字符都被接受，所以「外来转义」这一类在文本资源里**不存在**；把 `.gd` 的字母表套上去只会制造假红。pin：`a_scene_string_may_hold_a_backslash` |
| **X2** 代码里行尾的反斜杠（`var path = C:\`） | **声明为合法** | tokenizer 的 `\`+换行 = 语句续行；把它当残渣才是假红。它在验收表里被登记为「看不见」，但语言说它合法，所以本批**有意**不抓，并在表测试里写明 |

`X8` 的诚实成本（写进 §8）：一个 **malformed** 的 `\u` 落在 `.tscn` 字符串里（VariantParser 会报 `Malformed hex constant in string`）本审计仍然看不见，因为转义规则只对 `.gd` 生效；本批**声明**它，不修它。

---

## 5. 变更四：被排除目录的写——**必须被检出，读数必须要求它缺席**

**决策与理由。** 验收构造过一轮「看起来干净」的轮次：Tester 的字节活在 `.godot/`、`.import/`、`.hoh/`，`result.json` 却 `ok=true`、无 `qa_contaminated_*`，E5 读 MET。`HashExcludes::merged()` 里那两个目录是**有意的缓存排除**（R10 要求 `version_id` 稳定，所以它们**不能**进 `hash_tree`，本批也没让它们进）。因此本批把它判为**必须检出**：

1. **观察而不是哈希**（`src/runtime/policy.rs`）：新增 `cache_prefixes()`（规范化、去重、滤掉运行时的 `.hoh`/`.git`）与 `cache_manifest()`（把 `candidate/<prefix>/**` 逐文件投影成 `<prefix>/<rel> -> sha256`）。它**不**进入 `hash_tree`，`version_id` 与冻结快照身份一字未动。
2. **QA 窗口两侧各取一次**（`src/runtime/run_loop.rs`）：与哈希同一时刻取 `cache_before`/`cache_after`。候选视图是从快照按同一套排除复制出来的，**本来不含**这些缓存目录，所以窗口内出现的任何路径都是角色的写。
3. **留证**（`src/runtime/frozen_view.rs::preserve_excluded_writes`）：新增的路径**移出**视图到 `iter-N/tester-writes/cache-candidate/<rel>`；被改写的路径**复制**留证（排除路径没有快照字节可还原，这一点写在函数 doc 里，不假装能恢复）。失败**不吞**，逐条写进警告。
4. **拒绝**：与哈希可见的写**同一条契约**——`fail_contract(..., ContractViolation::QaContaminatedCandidate, ...)`，`ok=false`、`reason=contract_violation`、`failed_role=tester`，并保留**真实门判决**（`FailureFacts.artifact_gate = Some(launch_gate)`），与既有污染分支完全一致。
5. **判据读数**（`tests/godot_smoke.rs::e5_qa_did_not_modify_the_artifact`）：现在要求 `ok == true` **且**没有 `qa_contaminated_*` **且**没有 `qa_wrote_cache_*`。离线同形读数在 `tests/evidence_binding.rs::qa_write_warnings`（与 E5 用**同一条过滤规则**），由新测试 `a_write_through_the_configured_cache_excludes_can_never_read_as_a_clean_round` 钉住。
6. **口径更正**：`src/runtime/frozen_view.rs` 模块 doc 里原先那句「so a reader can never mistake … the two cases differ in `ok` and in that warning」被改成**只主张它建立的**：哈希只覆盖非排除路径，所以「没有角色写过」只能由**整条读数**（`ok` + 两族警告 + 缓存观察）读出，不能由哈希相等单独读出。`run_loop.rs` 里「the reading that can never be confused…」同样更正。

**这条判据可以主张 / 不可以主张**

- **可以**：在 QA 窗口内，被哈希覆盖的产物集合逐字节未变（`candidate_id == hash_tree(candidate, excludes)`），**并且**适配器配置的缓存目录也没有任何路径出现/改变/消失（独立观察），**并且**该轮 `ok=true`。
- **不可以**：不能说「字节级上不可能有写」。缓存目录是**被观察**而不是被哈希；观察本身也承认排除集是**配置**决定的（`config/hoh.yaml` 的 `[.godot, .import]`；运行时恒定排除的是 `[.hoh, .git]`，其中 `.hoh` 是 Tester 的合法提交区，**不**进观察）。若观察无法完成，轮次是**响亮失败**（警告里带残差），不是静默通过。
- **`REQUIREMENTS.md` 的 E5 行**（“QA 未修改 A_1（快照 hash 前后一致）”）位于 `tests/append_only_guard.rs` 封印的前缀（20,910 B）之内，按 D289 只能追加、本批**未改**它；它本身只主张 hash 相等（没有过度主张），过度主张在代码 doc 里，已按上条更正。更正后的读数以 `E5` 的 doc、`frozen_view.rs` doc、`evidence_binding.rs` 的离线同形读数与本报告为准。

---

## 6. 测试与 pin（新增 11 条，无删除、无改名）

| 文件 | 新增条目 | 覆盖的性质 |
|---|---|---|
| `src/runtime/integrity.rs` | `a_raw_string_processes_no_escapes` | raw 字面量不处理转义（含 raw 三引号）+ converse（非 raw 的同一字节仍是残渣；标识符尾部的 `r` 不是 raw 标记） |
| `src/runtime/integrity.rs` | `the_escape_table_is_the_languages_own` | `\UXXXXXX`/`\uXXXX` 合法；位数不足成 finding；`/` 与 `0..7` 不是转义 |
| `src/runtime/integrity.rs` | `a_backslash_before_a_comment_marker_is_still_code` | X1 关闭 |
| `src/runtime/integrity.rs` | `a_continued_string_keeps_its_hash_inside_the_string` | X9 关闭 + 该续行上的合法转义仍干净 |
| `src/runtime/integrity.rs` | `a_triple_quoted_literal_spans_lines_and_keeps_its_escapes` | 三引号跨行；其内合法转义干净、外来转义被抓 |
| `src/runtime/integrity.rs` | `a_scene_string_may_hold_a_backslash` | X8 声明的 pin |
| `src/runtime/integrity.rs` | `the_acceptance_counterexamples_are_all_judged` | **验收用过的全部 L1–L8 / X1–X10（含我自己的 L9）逐条判决表**（声明项在名字里写明） |
| `src/runtime/policy.rs` | `the_cache_watch_names_only_the_adapter_cache_directories` | 观察集合 = 适配器缓存目录，规范化去重，不含 `.hoh`/`.git` |
| `src/runtime/policy.rs` | `the_cache_manifest_names_the_cache_paths_and_leaves_the_hash_alone` | 观察能看见缓存变化，而 `hash_tree` 完全不变（R10） |
| `src/runtime/frozen_view.rs` | `excluded_cache_writes_are_preserved_never_swallowed` | 新增路径被移出、改写路径被复制留证；失败被返回而非吞掉 |
| `tests/evidence_binding.rs` | `a_write_through_the_configured_cache_excludes_can_never_read_as_a_clean_round` | 端到端：`.godot/cheat.bin` → 拒绝 + `qa_wrote_cache_candidate` + 留证 + 视图不含该字节 + 真实门判决仍在 |

逐名集合比对（`no_removed_tests.py`，HEAD 的 git blob vs 工作树）：**REMOVED 0、MOVED BETWEEN FILES 0、ADDED 11**。

---

## 7. 受控 plant（**6 个**，每个「对照绿 → 植入红 → 还原字节相同 → 还原后仍绿」）

驱动：每个 plant 只做**一处字面替换**，只跑**一条**测试，编辑与还原后都 `os.utime`，开始前**断言工作树字节 == 字节备份**。日志：`C:\Users\wyl\AppData\Local\Temp\t16dr88\plants_log.txt`。

| plant | 目标文件 | 一处替换 | 目标测试 | 对照 → 植入 → 还原 |
|---|---|---|---|---|
| P1-raw-string-skip | `integrity.rs` | `if open.raw {` → `if open.raw && false {` | `a_raw_string_processes_no_escapes` | 0 → **101** → 0 |
| P2-unicode-digit-check | `integrity.rs` | `if !has_hex_digits(…) {` → `if false && !…` | `the_escape_table_is_the_languages_own` | 0 → **101** → 0 |
| P3-carried-string-state | `integrity.rs` | `scan_line(raw, &mut state)` → `scan_line(raw, &mut LexerState::default())` | `a_continued_string_keeps_its_hash_inside_the_string` | 0 → **101** → 0 |
| P4-cache-write-rejection | `run_loop.rs` | `if !candidate_cache_diff.is_empty() {`（拒绝那处）→ 加 `false &&` | `a_write_through_the_configured_cache_excludes_can_never_read_as_a_clean_round` | 0 → **101** → 0 |
| P5-escape-before-comment | `integrity.rs` | 代码分支的 `if index + 1 < count {` → `… && chars[index + 1] != '#' {` | `a_backslash_before_a_comment_marker_is_still_code` | 0 → **101** → 0 |
| P6-cache-watch-names | `policy.rs` | `items.push(normalized.to_string());` → `let _ = normalized;` | `the_cache_watch_names_only_the_adapter_cache_directories` | 0 → **101** → 0 |

汇总行：`PLANTS THAT DID NOT REDDEN: []`。六个 plant 的每一次还原都是 `restored byte-identical=True` 加植入前 sha256（`fb00d440…`（integrity）、`62575ede…`（run_loop）、`411e2204…`（policy）），收尾再用 `backup.py verify` 断言六个文件的**工作树 sha256 == 字节备份 sha256**（全部 `equal=True`）。

---

## 8. 闸门：基线、本批、字面退出码

两趟都用**仓库自己的 `target/`**、同一份驱动（`gate.py`）：Python `glob` 清 `target/debug/.fingerprint/hof-rs-*`（路径逐个打印后 `shutil.rmtree`），再按 `git ls-files "*.rs"` **逐个** `os.utime`。

| 读数 | 基线（我复现） | 本批（工作树） |
|---|---|---|
| `FINGERPRINT_PATTERN` 命中 / 清除 | `hof-rs-*` / **63** | 同 / **63** |
| `TOUCHED_TRACKED_RS` | **101** | **101** |
| `cargo fmt --all --check` | `FMT_EXIT=0` | `FMT_EXIT=0` |
| `cargo test --offline -- --list` | `LIST_EXIT=0`，`LIST_TESTS=640`，`LIST_BENCH=0` | `LIST_EXIT=0`，`LIST_TESTS=651`，`LIST_BENCH=0` |
| **`cargo test --offline` 字面退出码** | **`LITERAL_CARGO_TEST_EXIT=0`** | **`LITERAL_CARGO_TEST_EXIT=0`** |
| 汇总 | `SUITES=62 PASSED=633 FAILED=0 IGNORED=7`，`RED_SUITES=0` | `SUITES=62 PASSED=644 FAILED=0 IGNORED=7`，`RED_SUITES=0` |
| `passed + ignored == --list` | 640 | 651 |
| 全量 wall | 1488.6 s | 1426.8 s |
| 运行前后并发测试进程 | `PROCS_BEFORE=NONE`，`PROCS_AFTER=NONE` | `PROCS_BEFORE=NONE`，`PROCS_AFTER=NONE` |

- 退出码由 `subprocess.run(...).returncode` **原样写入**，不是推断。
- **强制重建的证据**：`gate_log.txt.raw.txt` 第 1 行就是 `Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)`；与 DR-87 验收提醒的一样，这行落在 **`--list` 那次调用**里（清指纹后的第一次 cargo 调用），随后全量运行复用它编译出的二进制。
- 计数与基线的差：`644 − 633 = 11 = 新增测试数`；`ignored` 未变（7）；`--list` 640→651；**没有测试被删除或改名**（§6 的逐名集合比对）。
- 本批结束时 `tasklist | grep -icE "cargo|rustc|hof_"` = **0**：没有任何属于本批的测试进程还在跑（DR-86 那次日志被并发运行截断的教训）。
- **一次工具事故（如实登记）**：`gate.py` 的第一版汇总把 `test result:` 行按 `;` 切开后误判字段数，基线那份日志里打印出 `PASSED=0`。修正汇总函数后，用**另一个纯函数脚本** `summarize.py` 从**同一份 raw 日志**重新求和得到 `633/0/7`（本批那份同样复核为 `644/0/7`）。字面退出码、`--list`、`fmt` 与原始输出不受影响。

---

## 9. 禁止区域自检（收尾读数）

| 项 | 读数 | 结论 |
|---|---|---|
| `runs/**` | **7341** 个文件；最新 mtime `2026-10-03T05:47:27`（`runs/smoke-t16/evidence/round/evidence_refresh.txt`），**早于本批开始（10:39）** | 未写 |
| `.workspace/**` | **836** 个文件；最新 mtime `2026-10-03T05:10:29` | 未写 |
| `.spec/hof-rs/PRD-mario.md`（冻结的 S） | `4c81c3a9…5c3a`（未改） | ✓ |
| `.spec/hof-rs/REQUIREMENTS.md` | `298a948929…e54`（未改） | ✓ |
| `DECISIONS.md` | `2a4326ec…7fd5`，1238815 B（未改，**未补 D 条目**——按任务书不改它） | ✓ |
| `Cargo.toml` / `Cargo.lock` | `e0c4992b…` / `d98fa915…`（未改；未加依赖） | ✓ |
| 引擎树 `godot-mcp/godot` | HEAD `fc63af77c33368c4a1bb839c95d19750554f63a3`，`git status --porcelain` 空 | ✓ |
| git | `HEAD=ab95c65…`、`origin/master=55a0751…`（`ahead 8`），**未 stage／commit／push** | ✓ 未推送 |
| 工作树 | 只有本批 **6** 个源文件 ` M`，加四个既有未跟踪松文件 `l.json`/`p2.json`/`pv.json`/`r.json`（未动），加本报告 | ✓ |
| 危险动作 | 未用 `rm -rf`（清指纹只用 Python `glob`+`shutil.rmtree`，路径先打印）；未用 `git checkout --`；未从「未展开的变量」构造路径；每次编辑/还原后 `os.utime`；工作树 == 字节备份已断言 | ✓ |
| 网络/引擎 | 未联网、未启动引擎、未跑轮次、未手写游戏 | ✓ |

本批改动的 6 个文件（收尾 sha256）：`integrity.rs` `fb00d440…`、`policy.rs` `411e2204…`、`run_loop.rs` `62575ede…`、`frozen_view.rs` `ad43b75e…`、`godot_smoke.rs` `1616013e…`、`evidence_binding.rs` `1447714a…`。行尾与 git blob 一致（工作树与 blob 都是纯 LF；`core.autocrlf=true` 只产生 git 的提示，不产生漂移）。

---

## 10. 残留风险：**实测**与**推断**分开

### 10.1 实测（本批，离线）

1. 两条误报关闭：raw 字符串 Windows 路径、`\U0001F600` 各 **0 findings**（P1/P2 让对应测试承重）。
2. 反方向仍成立：可执行代码里的外来转义在两个方向都被抓（P5 承重；验收的 X4/X5/X6/X7/X10 与自造对照全在表测试里）。
3. 逃逸位置：X1/X3/X9 关闭；X8/X2 声明并在测试里写明理由。
4. 被排除目录的写：端到端夹具里 `.godot/cheat.bin` 现在**拒绝**、留证、并在 `result.json.warnings` 里以 `qa_wrote_cache_candidate` 具名（P4 承重）。
5. 观察不改变哈希：`the_cache_manifest_…_leaves_the_hash_alone` 实测「缓存变化可见、`hash_tree` 不变」。
6. 闸门：强制重建（清 63 指纹 + touch 101 个 `.rs`）下 `cargo test --offline` 字面退出码 **0**、**644 / 0 / 7**、62 suites、`--list` 651、`fmt` 0。
7. 6 个 plant 全部自洽（对照绿/植入红/还原字节相同）。

### 10.2 推断（未实测，必须标明）

1. **真机轮里的行为**：本轮没有引擎、没有真机轮，所以「下一轮 Tester 写 `.godot` 会以 `ok=false` 收场」是机制推断；实测只在离线夹具上。
2. **合法重建候选缓存算不算违规**：若未来某轮里 Tester 在**自己的 cwd（候选视图）**里跑编辑器并把 `.godot` 重建出来，本批会把它判为违规并拒绝。本批的理由是：候选视图按同一套排除从快照复制，**本来没有**这些目录，所以出现即角色的写；且 R4/R13 说冻结视图的写要拒绝。**这是判断，不是实测**，若真机轮出现噪声，应在下一批按「缓存重建是否属于 Tester 的合法动作」单独裁决。
3. **`.tscn` 里 malformed `\u`**：VariantParser 会报错，但本审计的转义规则只对 `.gd`；声明为开放（理由见 §4）。
4. **`\.` 之外的代码反斜杠**：本批按 tokenizer 判定「代码里 `\` 只能是行继续」，比旧的字母表更严；我没有在真机上验证某支旧脚本是否被误伤（离线 corpus 与全量套件均绿）。
5. **行尾 CR 的极端形态**（`\`+`\r` 而不跟 `\n`）：`str::lines()` 会剥掉行尾 `\r`，所以这种形态被当作行尾续行；tokenizer 对这种形态另有 `Unexpected carriage return character.` 的报错路径，本批未单独建模。

### 10.3 明确未关闭的开放项

| id | 内容 | 本批处置 |
|---|---|---|
| DR86A-3a/3b | 干净行边界截断、`.gd` 尾巴式碎片 | **未改**（不在本批任务书内；DR-87 已声明） |
| DR86A-6 | `audit_tree` 静默跳过非 UTF-8 候选 | **未改**（同上） |
| §4 的 X8 | `.tscn`/`.tres` 字符串里的转义与 malformed unicode | **声明**（附 VariantParser 依据与成本） |
| §4 的 X2 | 代码行尾反斜杠 | **声明为合法**（tokenizer 续行） |
| DR87A-5 | 「批次的提交改了 DR-86 报告」 | 不属本批（本批未提交；也未改任何既有报告） |
| DR87A-6 | 报告里两处数字不吻合（126 vs 63、9 vs 7） | 本批独立复现为 **63** 与 **7 ignored**，与 DR-87 验收一致 |

---

## 11. 我没有做的事

- 未启动/重启/驱动引擎；未跑任何轮次；未联网；未手写任何游戏；未 stage／commit／push。
- 未写 `runs/**`、未写任何 workspace 目录；未改 `DECISIONS.md`、`REQUIREMENTS.md`、`PRD-mario.md`（冻结规格）、`godot-mcp/**`、引擎二进制、`Cargo.toml`/`Cargo.lock`。
- 未新增或删除任何测试（只新增 11 条；逐名集合比对 REMOVED 0 / MOVED 0 / ADDED 11）。
- 未做任何 `rm -rf`、未用 `git checkout --` 还原、未从「未展开的变量」构造路径。
- 未复核 DR-87 验收报告自身的其它结论（只读它取缺陷清单）。
