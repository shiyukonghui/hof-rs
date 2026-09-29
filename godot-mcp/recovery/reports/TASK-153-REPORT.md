# TASK-153 — 契约生成器去跨仓耦合：`gen_renamed_contract.py` 改用引擎内基准

* 执行者：实现子代理（无上游对话上下文；唯一任务来源 `godot-mcp\recovery\tasks\TASK-153.md`）
* 引擎仓：`F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`），起点 HEAD
  `bef4be0407`（工作树干净），最终 HEAD `28432f859f`
* 一个本地提交（**未 push**）：`28432f859f` **生成器改用引擎内基准 + 溯源注释**：1 文件 / 33 增 3 删
* 脚本 / 原始证据：`godot-mcp\recovery\work\task153\`（`exp1_plant_baseline.py`、`exp2_plant_map.py`、
  `ast_scan_gen.py`、`inspect_baseline.py`、`exp1-plant.txt`、`exp1-gen.out.txt`、`exp1-restore.txt`、
  `exp2-plant.txt`、`exp2-gen.out.txt`、`exp2-restore.txt`、`ast_scan.out.txt`、`defaults.txt`、`gen-run.txt`、
  `gen-help.txt`、`g09-conditions.txt`、`deps-check.txt`、`hofrs-script-refs.txt`、`push-check.txt`、
  `ports-before.txt`、`gates\task153-final\`）
* 报告：本文件。

---

## 1. 结论

**已把生成器也指到引擎内基准**，且**没有削弱它的失败能力**。

| 项 | 结果 |
|---|---|
| 目标达成 | `DEFAULT_OLD_CONTRACT` 由 `r"F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json"` 改为 `os.path.join(DOCS, "rename-baseline-tools-list.json")`；三个默认路径同源于 `DOCS`；生成器与 `g05` **共用同一个引擎内基准** |
| 行为保持 | 生成器（改动后，全默认）与**改动前的生成器 + 显式同一基准**输出**逐字节相同**：154311 B / `8461b6eee63fc17b6547a2640b40e3383f5618f22658611aa8c2e17b704e5373`，`GEN_EXIT=0` |
| 失败能力（非空洞性） | 两次受控植入**都非零退出**：①引擎内基准里同长度改一个 `name` ⇒ `exit 1`，`FATAL: old contract sha256 … != the frozen …`；②映射里改错一条 `new_name` ⇒ `exit 1`，`FATAL: L1 pattern mismatch: add_animation_track`。两次均**逐字节复原**（`git status --porcelain` 与 `git diff --stat` 双空 + `git hash-object` == HEAD blob） |
| 门 | **十道门 10/10 exit 0**；`g05` = **exit 0 / 30 PASS / 0 FAIL**（含 `B0`/`B1`/`B2`）；`g09` = `ANCHOR_STRUCTURAL_EQUIVALENT`，`RED_COUNT=0`，`RESULT PASS` |
| 禁区 | 9877 全程无监听；9888/9889 收尾无监听；未 push；hof-rs 侧仅新增授权证据目录；无新依赖 |

### 1.1 真实命令与退出码（本报告所有结论的命令级依据）

| # | 命令（工作目录 = 引擎仓根，另有注明的除外） | 退出码 |
|---|---|---|
| 1 | `git status --porcelain` / `git rev-parse HEAD`（开工前） | 0（<空> / `bef4be0407`） |
| 2 | `python -m py_compile modules/mcp_server/scripts/gen_renamed_contract.py` | 0 |
| 3 | `python modules/mcp_server/scripts/gen_renamed_contract.py --out …\tools_list.renamed.out.json` | 0 |
| 4 | `python …\gen_HEAD.py --old-contract <基准> --map <映射> --out …\out_HEAD_explicit.json`（改动前脚本 + 显式同一基准） | 0 |
| 5 | `python …\exp1_plant_baseline.py`（植入） | 0 |
| 6 | `python modules/mcp_server/scripts/gen_renamed_contract.py --out …\exp1-should-not-exist.json`（植入态） | **1** |
| 7 | `python …\exp2_plant_map.py`（植入） | 0 |
| 8 | `python modules/mcp_server/scripts/gen_renamed_contract.py --out …\exp2-should-not-exist.json`（植入态） | **1** |
| 9 | `powershell -NoProfile -File tools\run_gates.ps1 -Root F:\moonbit-hof-rs\godot-mcp -Tag task153-final -RunGates -OutDir …\gates\task153-final`（工作目录 `F:\moonbit-hof-rs\godot-mcp`） | 0（十门子进程 `GATE_EXIT` 全 0） |
| 10 | `python …\ast_scan_gen.py` | 0 |
| 11 | `python modules/mcp_server/scripts/gen_renamed_contract.py --help` | 0 |

> 门是用**规范运行器**跑的：`F:\moonbit-hof-rs\godot-mcp\tools\run_gates.ps1`（**注意它不在引擎仓内**，
> 见 §7 第 3 条），命令集与顺序是该文件 `:214-225` 的原文，**未做任何替换**；因为本次改动全是非编译输入，
> 预检本身会判定 `SKIP_REBUILD`（不跑门），所以显式传 `-RunGates` 强制十门真正执行：预检原文为
> `GATES_PREFLIGHT VERDICT=RUN_GATES`、`REASON="-RunGates was given: the caller asked for the ten gates unconditionally"`。
> 没有重建引擎。

---

## 2. 改动清单与溯源

### 2.1 文件改动（`git diff --stat bef4be0407..HEAD` 只有 1 个文件）

| 文件:行 | 改动 |
|---|---|
| `modules/mcp_server/scripts/gen_renamed_contract.py:1764` | 新增 `DOCS = os.path.join(MODULE_ROOT, "docs")`（与 `docs/scripts/check_rename_map.py:71-73` 的 `DOCS` 根写法一致） |
| `gen_renamed_contract.py:1801-1829` | 新增 **29 行溯源注释块**（含 TASK-153 动机、路径 / 字节数 / 条数 / sha256 / 来源 blob / 采集命令 / 日期） |
| `gen_renamed_contract.py:1830` | `DEFAULT_OLD_CONTRACT` 由 hof-rs 绝对路径改为 `os.path.join(DOCS, "rename-baseline-tools-list.json")` |
| `gen_renamed_contract.py:1831-1832` | `DEFAULT_MAP` / `DEFAULT_OUT` 改由同一个 `DOCS` 派生（**字符串值与改动前逐字相同**，仅为统一来源） |
| `gen_renamed_contract.py:1834` | `OLD_CONTRACT_SHA256` **一个字节未改**（`8f8051c4…`） |

**未改**：`OLD_CONTRACT_SHA256` 的值、任何断言表达式、任何其它默认值语义、`docs/rename-baseline-tools-list.json`、
`docstool-rename-map.json`、`docs/tools_list.renamed.json`、任何门脚本、`tools\run_gates.ps1`、
`check_engine_anchor.ps1`、`check_hardcoded_counts.py`。**没有新增/删除/修改任何 `import`**（§5.4）。

改动后的默认值（实测，`recovery\work\task153\defaults.txt`）：

```
DEFAULT_OLD_CONTRACT= F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\docs\rename-baseline-tools-list.json
DEFAULT_MAP= F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\docs\tool-rename-map.json
DEFAULT_OUT= F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\docs\tools_list.renamed.json
```

### 2.2 溯源（记录在常量旁边的同一段注释里，逐字）

```
#   path  : docs/rename-baseline-tools-list.json   (this module's docs dir)
#   bytes : 48749     tools: 174     eol: none (the file carries no newline)
#   sha256: 8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54
#   source: hof-rs `tests/fixtures/mcp/tools_list.json` at the state immediately
#           before its DR-42 re-capture (hof-rs commit db2eed7^, git blob
#           543b49b2583bf06c3aba2a320649a31eda272e3e)
#   taken : 2026-09-29 - the date TASK-152 recorded next to this same artifact
#           (docs/scripts/check_rename_map.py, the TASK-152 comment block);
#           TASK-153 gathered nothing and asserts no date of its own. TASK-152
#           added the file in engine commit 069a2e2ea8 after reading it with
#           git -C F:\moonbit-hof-rs cat-file blob 543b49b2...
#           (a pure read of the hof-rs object store; nothing on the hof-rs side
#            was written), then wrote it verbatim into this repository.
```

**关于日期（任务书 §2.2 的硬要求）**：`2026-09-29` **不是**我新采集的断言，而是 **TASK-152 已经记录在同一
artifact 旁**的日期（`docs/scripts/check_rename_map.py`，已提交在起点 HEAD 里）。我另外独立读了机器时钟
核对：`Get-Date -Format 'yyyy-MM-dd HH:mm:ss K'` → `2026-09-29 09:09:36 +08:00`（同一日）。本任务
**没有重新采集**任何字节，注释里也**明说了这一点**。我没有编造任何日期。

### 2.3 溯源数值的独立复核（实测，非引用）

```
blob(HEAD)      = 543b49b2583bf06c3aba2a320649a31eda272e3e
work blob       = 543b49b2583bf06c3aba2a320649a31eda272e3e   (git hash-object)
bytes           = 48749
sha256          = 8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54
result.tools    = 174
newlines        = 0   crlf = 0        (整文件一行 JSON)
```

### 2.4 「不再有仓外可执行路径」的机器判据

不只靠 grep（注释里必然还会提到 hof-rs，那是溯源，不是代码路径）。`recovery\work\task153\ast_scan_gen.py`
用 AST **排除模块/函数/类 docstring** 后逐个检查 `ast.Constant` 字符串与每个 `open()` 的实参（原文
`ast_scan.out.txt`）：

```
script                     : F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\scripts\gen_renamed_contract.py
docstrings excluded        : 5
executable string-literal hits naming hof-rs : 0
open() calls               :
   line 1855  path
   line 1991  old_path
   line 1993  map_path
   line 2242  out_path
SCAN_EXIT=0 (no executable hof-rs path)
```

即：`hof-rs` 只出现在**注释**里（`gen_renamed_contract.py` 共 6 行，全为 `#` 行），**没有**任何可执行字符串
指向仓外；四个 `open()` 的实参全部是默认值/`--old-contract`/`--map`/`--out` 派生出来的变量。

### 2.5 `--help` / docstring（任务书 §2.4）

生成器的模块 docstring **从未**提到那个 hof-rs 路径（grep 全文件只有注释块 6 行命中），`--help` 也**不含**
任何路径（`--old-contract`/`--map`/`--out` 三个参数都没有 help 文本）：

```
usage: gen_renamed_contract.py [-h] [--old-contract OLD_CONTRACT] [--map MAP]
                               [--out OUT]
...
HELP_EXIT=0
help mentions hof-rs: False
```

⇒ §2.4「若 docstring/--help 提到就更新」在本文件上**无内容可改**，**未改动任何文档字符串或帮助文本**。

---

## 3. 非空洞性受控实验（三步原始输出）

**为什么做两次**：基准是**冻结字节件**，`OLD_CONTRACT_SHA256` 就是为它设的门，所以「植入基准 ⇒ 任何漂移
都必须失败」这条路径天然由 sha 闸把住。为了不让结论停在这个「必然成立」上，我加做了实验 2：它**完全不碰
基准**，而是改**映射**（映射的 sha 在生成器里**没有**冻结，只有 `map_sha` 进了产物 `_meta`），因此红的
**只能**是生成器的**语义自检**。两次都逐字节复原。

### 3.1 实验 1（任务书强制项）— 在**基准**里植入改名 ⇒ `exit 1`

植入方式：**纯字节替换**，且**同长度**：`"name":"add_animation_track"` → `"name":"add_animation_tracx"`。
文件 JSON 仍合法、**字节数一个不变**（48749 → 48749），所以生成器不可能靠「大小变了」这种启发式发现问题。
原始输出（`exp1-plant.txt`）：

```
PLANT baseline bytes        : 48749
PLANT baseline sha256       : 8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54
PLANT frozen sha256         : 8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54
PLANT tool names in baseline: 174
PLANT all names are map old_names: True
PLANT victim name           : 'add_animation_track'
PLANT needle occurrences    : 1
PLANT injected name         : 'add_animation_tracx'
PLANT baseline bytes 48749 -> 48749
PLANT planted sha256        : 6a2ffe6800d43450f77ba211808f3f181cf9c252dc9fe3463d9e6e4482f5dd4c
PLANT JSON still parses     : True
PLANT byte count unchanged  : True
PLANT reversal restores the original bytes: True
```

植入态下 `git status --porcelain`：` M modules/mcp_server/docs/rename-baseline-tools-list.json`。
生成器在该状态下的**真实输出**（`exp1-gen.out.txt`，stderr 原文）：

```
FATAL: old contract sha256 6a2ffe6800d43450f77ba211808f3f181cf9c252dc9fe3463d9e6e4482f5dd4c != the frozen 8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54
GEN_EXIT=1
OUTPUT_WRITTEN=False
```

**读法**：`exit 1`、明确的 `FATAL`（不是警告）、**产物文件不存在**（生成器在写出前就中止）。
**若植入后仍成功 ⇒ 判 fail；这里不是。**

### 3.2 恢复证明 1（逐字节，`exp1-restore.txt` 原文）

```
=== git status --porcelain (must be empty) ===
<empty>
=== git diff --stat (must be empty) ===
<empty>
=== git hash-object vs HEAD blob ===
work_blob=543b49b2583bf06c3aba2a320649a31eda272e3e
head_blob=543b49b2583bf06c3aba2a320649a31eda272e3e
EQUAL=True
work_sha256=8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54
```

恢复手段是 `git checkout -- modules/mcp_server/docs/rename-baseline-tools-list.json`；**双空** +
`git hash-object` == HEAD blob（仓库对 CRLF 敏感 ⇒ 用 blob id，不用文本比较），且 sha256 回到冻结值。

### 3.3 实验 2（深度）— 在**映射**里植入错映射 ⇒ `exit 1`（红在语义自检，非哈希闸）

植入方式：`"new_name": "editor_add_animation_track"` → `"new_name": "add_animation_track"`（丢掉通道前缀，
即 L1 违规）。映射的 sha 在生成器里**没有**冻结，所以这一条**绕开了**实验 1 的哈希闸。原始输出
（`exp2-plant.txt`）：

```
PLANT2 map bytes           : 70917
PLANT2 map sha256          : 2f552719f6a23fe328df0a2944c6048824c1b2a750aebc0fe2cabbcd3529c2bd
PLANT2 map entries         : 174
PLANT2 victim new_name     : 'editor_add_animation_track'
PLANT2 needle occurrences  : 1
PLANT2 injected new_name   : 'add_animation_track'
PLANT2 map bytes 70917 -> 70910
PLANT2 planted sha256      : e17a2df08b27e030300fa4688640c24ae473a06308d406b8a7a089f649f4fe49
PLANT2 JSON still parses   : True
```

生成器在该状态下的**真实输出**（`exp2-gen.out.txt`，stderr 原文）：

```
FATAL: L1 pattern mismatch: add_animation_track
GEN_EXIT=1
OUTPUT_WRITTEN=False
```

**读法**：`exit 1`，且失败信息**点名**了被改坏的那个名字。这证明生成器的语义自检（不是只有那条冻结 sha）
仍然工作；任务书 §2.3「不得把它改成永绿或降级为警告」在本实验下**实测未被违反**。

### 3.4 恢复证明 2（逐字节，`exp2-restore.txt` 原文）

```
=== git status --porcelain (must be empty) ===
<empty>
=== git diff --stat (must be empty) ===
<empty>
=== git hash-object vs HEAD blob ===
EQUAL=True  modules/mcp_server/docs/tool-rename-map.json
  work_blob=743bc79c585cc013a6bd3e900e79d4dc5e042eb4
  head_blob=743bc79c585cc013a6bd3e900e79d4dc5e042eb4
EQUAL=True  modules/mcp_server/docs/rename-baseline-tools-list.json
  work_blob=543b49b2583bf06c3aba2a320649a31eda272e3e
  head_blob=543b49b2583bf06c3aba2a320649a31eda272e3e
```

两次实验后、且在**任何后续提交之前**，工作树完全干净。此后没有再改这两个文件。

### 3.5 行为保持的正向对照（不是「没红就算过」）

把**改动前**的生成器（`git show HEAD~1:…` 导出为 `gen_HEAD.py`）用 `--old-contract` **显式指向**引擎内基准，
与**改动后**生成器的**全默认**运行对比产物：

```
HEAD-explicit (154311, '8461b6eee63fc17b6547a2640b40e3383f5618f22658611aa8c2e17b704e5373')
TASK-153-gen  (154311, '8461b6eee63fc17b6547a2640b40e3383f5618f22658611aa8c2e17b704e5373')
IDENTICAL True
committed     (154272, 'fd00c75e5174ec923d5a91c0323afa0804f523b385eae3d4f78d8c71e1f895df')
```

⇒ 本次改动**只**换了「默认从哪里取基准」，产物字节**完全相同**（`IDENTICAL True`）。

**顺带实测到的一件事（非本任务引入，见 §6.2）**：仓库里已提交的 `docs/tools_list.renamed.json`
（154272 B）与生成器**现在**的产物（154311 B）**不是**逐字节相同，但**语义差异只有一处** ——
`_meta.generated_from`（提交版仍是 hof-rs 路径；生成器现在会写引擎路径，长度差 39 B 正好解释字节差）。
**改动前的生成器配同一个基准也产出 154311 B**，所以这是**改动前就存在**的状态，与 TASK-153 无关。
**我没有重新生成那个已提交产物**（理由见 §6.2）。

---

## 4. 门结果（真实输出）

* 运行器：`F:\moonbit-hof-rs\godot-mcp\tools\run_gates.ps1`（**逐字使用**，只加 `-RunGates` 与 `-OutDir`）
* 证据目录：`recovery\work\task153\gates\task153-final\`（`summary.txt` + `g01..g10.{stdout,stderr}.txt`）
* **未做任何引擎重建**：本次改动不碰任何编译输入（§4.4）。

### 4.1 逐门退出码与关键行（HEAD=`28432f859f`，mono `4.8.dev.mono.custom_build.035edfce7`）

| 门 | exit | 关键输出（原文节选） |
|---|---|---|
| g01 | **0** | `test cases: 160 \| 160 passed \| 0 failed \| 1429 skipped` / `assertions: 6801 \| 6801 passed` / `Status: SUCCESS!` |
| g02 | **0** | `test cases: 1586 \| 1586 passed \| 0 failed \| 3 skipped` / `assertions: 431114 \| 431114 passed` / `Status: SUCCESS!` |
| g03 | **0** | `TOOL-GROUPS CHECK PASS  BYTES 5681  SHA256 b83d79d3e3d080ce460b61ca99a46a126d6a6c45eb3d51d7977a52a991b7fbc7` |
| g04 | **0** | `3/3 checks passed`；`editor port=9888 tools=154` / `game port=9889 tools=73` / `contract=177`；逐字抽样 `name=True description=True inputSchema=True`；`guard_user_port_9877 pid_before=-1 pid_after=-1` |
| **g05** | **0** | **`RESULT: PASS (all checks green)`；PASS 行 30、FAIL 行 0**（见 §4.2） |
| g06 | **0** | `TAUTOLOGY CHECK PASS (every hit is pinned; scanned=2 file kind(s) under 2 root(s))` |
| g07 | **0** | `PROBES: 10/10` |
| g08 | **0** | `BUCKET UNCLASSIFIED = 0`，`BUCKET total = 126`（FROZEN 70）/ `RESULT: PASS (every occurrence of 171/173/175/176/152/72/153 is classified; none is UNCLASSIFIED)` |
| **g09** | **0** | `ANCHOR_JUDGE RESULT PASS`，`VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT`，`RED_COUNT=0`（完整判定见 §4.3） |
| g10 | **0** | `22/22 cases passed`，含 `guard_user_port_9877` PASS |

**合计 10/10 exit 0**（`summary.txt` 的 `g01..g10 exit=0` 十行；每个 `GATE_EXIT` 由子进程内 `!ERRORLEVEL!`
延迟展开写出，不是我手写的）。

### 4.2 `g05` 完整判定：exit 0，30/30 PASS

`g05.stdout.txt` 的机器可数事实：`PASS` 行 = **30**，`FAIL` 行 = **0**，末行 `RESULT: PASS (all checks green)`。
顺序为 `A1 A2 B0 B1 B2 B3 E1 E2 E3 E4 C1 C2 D1 D2 D3 F1 F2 F3 F4 F5 F6 F7 F8 F9 G1 G2 G3 G4 G5 G6`。
与任务书 §4 的重点逐条对上（原文）：

```
[PASS] A1 total == 174                                            total=174
[PASS] A2 len(tools) == 174                                       len=174
[PASS] B0 old contract sha256 frozen                              8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54
[PASS] B1 old contract tools == 174                               len=174
[PASS] B2 bidirectional diff empty                                contract-only=[] map-only=[]
[PASS] B3 old_name unique                                         distinct=174
[PASS] E1 disposition values inside the enum                      outside=[]
[PASS] E2 no inline 'merge_into:<old_name>' form                  leftover=[]
[PASS] E3 every merge_into has a resolvable merge_target          targets=['get_performance_monitors']
[PASS] E4 merge_target only on merge_into entries                 stray=[]
[PASS] C1 non-merged new_name globally unique                     duplicates=[]
[PASS] C2 only merge pairs share a new_name                       shared=['editor_get_performance_monitors']
[PASS] D1 L1..L4 over all 174 new_name                            violations=[]
[PASS] D2 naive split('_')[1] demonstrably fails                  24/24 running_game_* misparsed
[PASS] D3 closed set has 37 verbs                                 distinct=37 listed=37
[PASS] F1 disposition counts 164/7/1/2                            {'rename': 164, 'fix_implementation_first': 7, 'unregister_until_implemented': 2, 'merge_into': 1}
[PASS] F2 channel counts 103/45/24/2                              {'project': 45, 'editor': 103, 'running_game': 24, 'os': 2}
[PASS] F3 mutating true == 103                                    true=103 false=71
[PASS] F4 sum(channel) == 174                                     sum=174
[PASS] F5 'evaluate' kept and annotated unused_in_v1              usage=0
[PASS] F6 convention carries the D-4/D-5 clauses                  missing=[]
[PASS] F7 convention.disposition_enum == the enum in force        [5 values]
[PASS] F8 mutating_semantics states 103 and the policy.rs predicate warning len=177
[PASS] F9 both screenshot tools: mutating=true + conditional-write reason (GDR-18) [2 pairs]
[PASS] G1 ported half is still 171                                ported=171
[PASS] G2 contract names unique                                   distinct=177
[PASS] G3 no unregistered/merged-source name leaks into the contract leaked=[]
[PASS] G4 both de-merged pairs present under 4 distinct names     present=[4 names]
[PASS] G5 every _meta.added_tool is in the contract               absent=[]
[PASS] G6 contract count == map total - 2 unregister - 1 merge + _meta.added_count 177 == 174 - 2 - 1 + 6 = 177
RESULT: PASS (all checks green)
```

（为节省篇幅，`F5/F7/F9/G4` 的长值我用了 `usage=0` / `[5 values]` / `[2 pairs]` / `[4 names]` 概括；
完整原文在 `g05.stdout.txt` 里，`PASS`/`FAIL` 的**条数**是机器统计的 30/0。**没有**任何一条被删或放宽。）

`CONTRACT bytes=154272 sha256=fd00c75e5174ec923d5a91c0323afa0804f523b385eae3d4f78d8c71e1f895df` ——
即 `g05` 读的仍是**仓库里那份**已提交契约（我没动它，§6.2）。`B0` 报的 sha 与改动前**逐字相同**（`8f8051c4…`）。

### 4.3 `g09` 完整判定（任务书 §4 现行判据逐条）

`g09.stdout.txt` 原文：

```
ANCHOR_JUDGE VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT
ANCHOR_JUDGE ANCHOR=035edfce7 ANCHOR_REPORTED=035edfce7 HEAD=28432f859
ANCHOR_JUDGE ANCESTOR=yes
ANCHOR_JUDGE CRITERION=A is an ancestor of H (A == H counts) and git diff --name-only A..H contains no compile input (safe = declared non-compiling whitelist, everything else red)
ANCHOR_JUDGE DIFF_COUNT=4 SAFE_COUNT=4 RED_COUNT=0
ANCHOR_JUDGE SAFE modules/mcp_server/docs/MCP-SERVER-HANDOVER.md
ANCHOR_JUDGE SAFE modules/mcp_server/docs/rename-baseline-tools-list.json
ANCHOR_JUDGE SAFE modules/mcp_server/docs/scripts/check_rename_map.py
ANCHOR_JUDGE SAFE modules/mcp_server/scripts/gen_renamed_contract.py
ANCHOR_JUDGE REASON=035edfce7 is an ancestor of 28432f859 and all 4 file(s) in the diff are non-compiling; the binary is NOT equal to HEAD, it is structurally equivalent to it
ANCHOR_JUDGE RESULT PASS
GATE_EXIT=0
```

现行判据要求 `ANCHOR_EQUAL` **或**（`ANCHOR_STRUCTURAL_EQUIVALENT` 且 `RED_COUNT=0`）——实测是后者，
`RED_COUNT=0`、`RESULT PASS`。三条附加条件（`g09-conditions.txt` 原文）：

```
=== condition 1/2: every file in bef4be0407..HEAD (TASK-153 range) ===
  modules/mcp_server/scripts/gen_renamed_contract.py -> SAFE
=== every file in 035edfce7..HEAD (binary anchor range) ===
  modules/mcp_server/docs/MCP-SERVER-HANDOVER.md -> SAFE
  modules/mcp_server/docs/rename-baseline-tools-list.json -> SAFE
  modules/mcp_server/docs/scripts/check_rename_map.py -> SAFE
  modules/mcp_server/scripts/gen_renamed_contract.py -> SAFE
=== git diff bef4be0407..HEAD (raw) ===
 modules/mcp_server/scripts/gen_renamed_contract.py | 36 ++++++++++++++++++++-- 1 file changed, 33 insertions(+), 3 deletions(-)
```

* **①** TASK-153 的提交区间（`bef4be0407..HEAD`）只有 **1 个 diff**（`gen_renamed_contract.py`），
  用 `check_engine_anchor.ps1` **自己的**分类器判为 `SAFE`（`.py` 在它的非编译白名单里）——
  **全是 docs/scripts、无编译输入**。
* **②** `git diff bef4be0407..HEAD` 的全部内容见上（1 文件 / 33 增 3 删），**没有**任何编译输入。
* **③** 三个被点名的文件**零 diff**：`modules/mcp_server/scripts/check_engine_anchor.ps1` → `ZERO DIFF`、
  `modules/mcp_server/scripts/check_hardcoded_counts.py` → `ZERO DIFF`、`run_gates.ps1` → 见
  §7 第 3 条（它在**引擎仓外**，在它自己的仓里同样是干净未改）。

**为什么不是 `ANCHOR_EQUAL`**：二进制锚点仍是 `035edfce7`（TASK-151 构建，mtime `2026-09-29 08:31:03`），
而我在它之后提交了 TASK-152 的 3 个 commit 与本任务的 1 个 commit，HEAD 必然前进到 `28432f859f`。
本任务是门/脚本类改动，不可能在不重建的前提下让「二进制自报锚点 == HEAD」；重建只会改二进制字节
（上一批的教训：构建**不位级可复现**）而不会多一行新代码 —— 那是制造假绿。我**没有**碰这个判据、
**没有**加白名单、**没有**传 `-Anchor`/伪造 `-VersionText`（命令里传的是二进制**自报**的 `--version`）。

### 4.4 二进制信息（**不作为新鲜度/一致判据**，仅登记）

```
binary exists = True
binary --version = 4.8.dev.mono.custom_build.035edfce7
binary bytes=300544 mtime=2026-09-29 08:31:03
```

按任务书 §4 的教训：**二进制 sha256 不作为判据**（本报告连它都没登记，避免任何人拿它当身份）。
新鲜度的三段证据是 ①`--version` = `4.8.dev.mono.custom_build.035edfce7`（与 TASK-152 验收时一致）；
②`g01` 仍 `160/160`、`g02` 仍 `1586/1586`（与 TASK-152 报告逐字相同，**没有**少一条，也没有多出 TASK-153
的用例 —— 本任务确实没加测试）；③`g10` 把活体端点跑过一遍（`22/22`）。**全程未构建**。

---

## 5. 禁区自查（真实输出）

### 5.1 端口：9877 未碰，9888/9889 已释放

`ports-before.txt` 与门后的**同一条只读命令**（`Get-NetTCPConnection -State Listen`，**只读，不连不绑**）：

```
=== listening ports BEFORE gates (read-only Get-NetTCPConnection) ===
port 9877 : <none listening>
port 9888 : <none listening>
port 9889 : <none listening>

--- port state AFTER gates ---
port 9877 : <none listening>
port 9888 : <none listening>
port 9889 : <none listening>
```

* 我**没有**起过任何 MCP 服务器：端口全部来自既有门脚本（`g04`/`g10` 内部只用 9888/9889；
  `g10` 的 `guard_user_port_9877` 报 `pid_before=-1 pid_after=-1` = 9877 上本来就没有进程，脚本按设计
  不去创建）。收尾复核：三端口**均无监听**。
* 我**没有**运行 `mcp032_d3_d4_d6_evidence.ps1`（它内部 `$UserPort = 9877`）；见 §6.2。

### 5.2 未 push

`push-check.txt` 原文要点：

```
upstream = bef4be04077e855918013355b03ce7a6795a910a
origin contains bef4be0407 =  origin/feature/mcp-server-module-rebuild
origin contains 28432f859f =
* feature/mcp-server-module-rebuild 28432f859f [origin/feature/mcp-server-module-rebuild: ahead 1] …
--- reflog last 6 ---
28432f859f HEAD@{0}: commit: gates: point gen_renamed_contract.py at the engine-internal contract baseline (TASK-153)
bef4be0407 HEAD@{1}: commit: gates: correct the baseline provenance date in check_rename_map.py (TASK-152)
…
```

* `git rev-list --left-right --count HEAD...@{u}` = `1  0`；`git branch -r --contains 28432f859f` **空** ⇒
  **我的提交不在 origin 上**；reflog 最近 6 条**全是 `commit:`**，没有任何 `push`/`fetch` 改写本地分支。
* **一个必须说清的事实**：TASK-152 的 3 个提交（`069a2e2ea8` / `e1fbc8ec7f` / `bef4be0407`）**已经在
  origin 上**，所以 `bef4be0407` 是当前的 upstream。这不是我 push 的——外仓的提交
  `6a003bd docs(engine): D228 - TASK-152 independently accepted … engine branch pushed; open TASK-153`
  记录了「TASK-152 通过验收后由决策侧推送」。本任务**只**新增 `28432f859f`，它在本地。

### 5.3 hof-rs 侧零改动

`hofrs-check.txt` 原文：

```
fixture path  = F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json
fixture bytes = 71481
fixture sha256= 50c5fb4204ee5b957b017eb994e7f7bd73f9b299e6aa9471d5cf11683e067da0
fixture mtime = 2026-09-28 22:37:34
--- hof-rs git status --porcelain ---
?? godot-mcp/recovery/work/task153/
```

* 夹具 mtime **早于我开工**（`2026-09-29 09:0x`），sha 仍是 hof-rs 自己 DR-42 重采后的
  `50c5fb42…`/71481 B ⇒ **一个字节未写**。我全程**没有**读写过 hof-rs 的工作副本；本任务连
  `git -C F:\moonbit-hof-rs cat-file blob …` 都**没有**执行（不需要重新采集）。
* hof-rs 工作树里唯一的新东西是本任务的授权证据目录 `godot-mcp/recovery/work/task153/`（**任务书授权的
  落点**，未跟踪）与稍后新增的 `godot-mcp/recovery/reports/TASK-153-REPORT.md`。
  据我在收尾前的复查，`src/**`、`tests/**`、`config/**`、`.spec/**` **零改动**。

### 5.4 无新依赖

`deps-check.txt` 原文：

```
=== imports in the changed generator (HEAD) ===
import argparse
import hashlib
import json
import os
import re
import sys
=== import lines changed by TASK-153? (git diff filtered) ===
<no import line added, removed or changed>
=== requirements/pyproject touched? ===
```

六个 import 全是 Python 标准库，**改动前后完全一致**；未安装任何包，未改 `requirements`/`pyproject`/`setup.py`。

### 5.5 未放宽/删除任何既有检查

* `g05` 的 **30 条断言一条没删**（§4.2，`PASS=30 / FAIL=0`）；`OLD_CONTRACT_SHA256` 的值一个字没改。
* `check_hardcoded_counts.py`（g08）的**任何模式都没改**（`ZERO DIFF`）；我的注释全部写成**连续 `#` 行**，
  走的是它**既有的** `^\s*#` → `FROZEN` 规则，**不是**加白名单或放宽扫描。g08 实测 `UNCLASSIFIED = 0`
  （counted 总数由 TASK-152 的 119 升到 126，全部落进 FROZEN）。
* `check_engine_anchor.ps1`（g09）**一个字节未改**。
* 生成器的失败路径**没有**被改成警告或永久绿（§3 两次植入都 `exit 1`）。
* 没有任何 `--no-verify`、`|| true`、`try/catch` 吞错；**没有**抑制门/构建/测试输出（门的 stdout/stderr
  各自落盘，`GATE_EXIT` 在子进程内延迟展开）。

---

## 6. 遗留风险与未验证项（区分实测与推断）

### 6.1 实测

1. **生成器默认输入已是引擎内件**：`DEFAULT_OLD_CONTRACT` = `…\modules\mcp_server\docs\rename-baseline-tools-list.json`
   （打印实测），三个默认值同源于 `DOCS`。**实测**。
2. **改动未改变产物字节**：改动前脚本 + 显式同一基准 vs 改动后脚本 + 默认，产物同为 154311 B /
   `8461b6ee…`，`IDENTICAL True`。**实测**。
3. **失败能力仍在，且不只有哈希闸**：基准同长度改名 ⇒ `exit 1` + `FATAL: old contract sha256 …`；
   映射错映射 ⇒ `exit 1` + `FATAL: L1 pattern mismatch: add_animation_track`；两次都逐字节复原
   （双空 + blob 相等 + sha 回冻结值）。**实测**。
4. **十道门 10/10 exit 0**，`g05` 30/30 PASS，`g09` RESULT PASS / RED_COUNT=0。**实测**。
5. **脚本无仓外可执行路径**：AST 扫描字符串常量命中 0、四个 `open()` 实参全是变量。**实测**。
6. **禁区**：9877 无监听、9888/9889 收尾无监听、未 push、hof-rs 夹具字节与 mtime 未动、无新依赖。**实测**。

### 6.2 实测到的范围边界（**本任务没有假装清掉的东西**）

1. **已提交产物里的 `_meta.generated_from` 仍写着 hof-rs 路径**（`tools_list.renamed.json:3939`），
   且它是**本次改动之前就存在**的：改动前的生成器用同一基准重跑，同样产出
   `_meta.generated_from = …\godot\modules\mcp_server\docs\rename-baseline-tools-list.json`（154311 B）。
   **这是实测。**
   * **我的选择：不重新生成**。理由：①任务书 §2 只要求**生成器**的默认输入自包含，没有要求重生成产物；
     ②产物是被 `g04`/`g05`/`g10` 与大量历史探针引用的**大工件**，其唯一差异会落在 `_meta` 的溯源字段上
     （+39 B），改动它属于**扩大改动半径**；③它是一条**惰性的历史溯源字符串**，不是任何读取路径 ——
     生成器不会去读它。**是否把该字段也刷新为引擎路径，留给决策者**（见 §6.3 第 1 条）。
2. **同类可执行跨仓引用仍有 2 处，不在十道门的路径上**（`git grep` 原文，`hofrs-script-refs.txt`）：

```
modules/mcp_server/scripts/mcp029_clear_default_evidence.ps1:62:$OldFixture = 'F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json'
modules/mcp_server/scripts/mcp032_d3_d4_d6_evidence.ps1:63:$OldFixture = 'F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json'
```

   两者都是**一次性历史取证脚本**（`mcp029` 用 `Test-Path` 兜底、`mcp032` 内部还用 `$UserPort = 9877`），
   **既不是门、也不是生成器、也不是契约自检**，`tools\run_gates.ps1:214-225` 里没有它们。
   我没有改它们（超出「生成器 + 门」这条线的范围，且 `mcp032` 涉端口 9877，擅自运行会踩禁区）。
   此外还有**注释/文档级**的 hof-rs 提及（`accept_m1.ps1:19-32`、`gen_table.py:471`、
   `check_rename_map.py:80-99`、`gen_renamed_contract.py:1803-1827`）——那些是**溯源**，按 TASK-152 的
   先例保留。**这是实测到的边界。**
3. **`mcp032`/`mcp029` 若将来被运行**，它们读的是 hof-rs 现在的夹具（71481 B / 177 条，与它们当年
   取证时的 48749 B / 174 条不同）。**这是推断**（我未运行它们，只读了代码与文件元数据）。

### 6.3 建议给决策者（不在本任务范围内，我**没有**擅自扩大改动）

1. **是否重生成 `docs/tools_list.renamed.json`**：若希望「引擎仓里不再有任何东西声称契约来自 hof-rs」，
   重生成一次即可 —— 唯一差异是 `_meta.generated_from`（+39 B）。但我**建议不要**为了这一行去动那个大工件：
   现有 `_meta.generated_from_sha256`（`8f8051c4…`）与冻结值一致、`g05` 全绿，而历史溯源链
   （`reports/evidence/task060/PROVENANCE.json`、`B0-BRIEF.md:199`）本来就把那份 hof-rs 夹具记为来源，
   刷新字段会与那些记录产生一次无声的、只影响文档一致性的差异。**若要做，请单开一个任务**，让它带着
   `mcp052/mcp053_contract_diff.py` 一起验证。
2. **`mcp029`/`mcp032` 的 `$OldFixture` 可以顺手指向引擎内基准**（一行改动各一处），但那两个脚本是历史
   取证件，改它们会改变「历史证据脚本」的语义（它们**故意**读当年的夹具）。建议**不改**，或单开任务
   并在注释里说明为什么读旧件。**我没有动它们。**
3. **门运行器的位置值得写进任务书模板**：`tools\run_gates.ps1` 在**外仓**（`F:\moonbit-hof-rs\godot-mcp\tools\`），
   不在引擎仓内（引擎仓里没有 `tools\` 目录）。任务书 §4 的写法「`tools/run_gates.ps1`」容易让执行者
   按引擎仓相对路径去找。**这是实测**（`Get-ChildItem -Recurse -Filter run_gates.ps1` 在引擎仓内返回空，
   在外仓找到 `F:\moonbit-hof-rs\godot-mcp\tools\run_gates.ps1`）。

### 6.4 未验证（**不是**本任务的失败，是明确的「没做」）

1. **「整个模块不再有任何跨仓可执行输入」** —— **没有**达成，也**没有**被本任务声明达成：§6.2 第 2 条
   实测到 2 处仍存在。任务书 §0 的目标是「生成器改用引擎内基准、与契约自检共用同一基准」，这一条**已达成**。
2. **重建后 `g09` 是否为 `ANCHOR_EQUAL`** —— 未做，理由见 §4.3（会制造假绿）。属**推断**：按该判据的
   `A == H` 分支，重建后应当得到 `ANCHOR_EQUAL`。
3. **本次改动对 `mcp029`/`mcp032` 的行为影响** —— 未运行那两个脚本，无实测数据（推断见 §6.2 第 3 条）。
4. **`tools_list.renamed.json` 重生成后的门表现** —— 未做（§6.2 第 1 条的决定），所以「重生成后十门仍全绿」
   属**推断**（依据是唯一差异在 `_meta.generated_from`，而没有任何门读该字段 —— `git grep` 实测
   `check_rename_map.py` / `accept_m1.ps1` / `check_tool_groups.py` 只读 `_meta.added_count`/`_meta.added_tools`/
   `_meta.overrides`/`_meta.map_sha256` 一类）。

---

## 7. 诚实披露（返工、猜错、绕过的尝试）

1. **非空洞性实验第一次做错了，我废弃并重做。** 第一版脚本用 `'"name": "%s"'`（**带空格**）作锚点，
   而引擎内基准是**紧凑 JSON**（`"name":"…"`，无空格），于是 `needle occurrences = 0`，脚本按设计
   `sys.exit` **拒绝植入**（未写文件）。**两个后果我都说清**：
   * 该次 aborted 的植入**没有**修改任何字节（脚本在 `open(...,"wb")` 之前就退出）；
   * 但同一条命令串里我**紧接着**跑了生成器（当时用的是 `--out …exp1-should-not-exist.json`），它在
     **未被植入的原始基准**上正常输出（`GEN_EXIT=0`）并生成了那个「不该存在」的产物文件。
     我发现后**删除了该文件**，并在第二次（正确锚点）实验里把 `OUTPUT_WRITTEN=False` 一并记录，
     用来证明植入态下生成器**确实没有**写出产物。这个 abort 的痕迹留在 `exp1-plant.txt` 的历史里
     （我**没有**删除那次输出），本文 §3.1 引用的是**第二次**的版本。
   * 教训（与 TASK-152 §7.1 同类）：**「改一个字段」必须先量出那个文件真正的字节形状**，我用
     `inspect_baseline.py` 补量了（紧凑 JSON、`newlines=0`、`b'"name":"'` 出现 174 次）。
2. **我把 `DEFAULT_MAP` / `DEFAULT_OUT` 也一并改成了 `DOCS` 派生**（任务书只点名基准那一行）。
   这**不改变行为**（字符串值与改动前逐字相同，§2.1 已给出实测默认值），理由是：只把基准换成 `DOCS`
   而让另两个继续写 `os.path.join(MODULE_ROOT, "docs", …)`，会让「模块 docs 根」有两个写法，
   正是 D225 那类「同一件事多个来源」的种子。**我愿意接受它带来的更大 diff**（3 行 vs 1 行），
   并在此声明，避免被读成偷偷扩大改动。
3. **`run_gates.ps1` 不在引擎仓里，所以 §4.3 的条件 ③ 无法用引擎仓的 `git diff` 验证它。**
   引擎仓里 `git diff bef4be0407..HEAD -- tools/run_gates.ps1` 会**空**，但那是「路径不存在」的空，
   不是「文件未改」的空。我改用**它所在的仓**（`git -C F:\moonbit-hof-rs status --porcelain --
   godot-mcp/tools/run_gates.ps1` → **空**）来验证。这条差别如果不写，条件 ③ 就是一个**空洞的绿**。
4. **我一开始误判了「推送」基线。** 看到 `git rev-list --left-right --count HEAD@{u}` = `1 0` 时我按
   TASK-152 报告的记忆以为「相对起点应当领先 4」，去查才发现 TASK-152 的三个提交**已经在 origin 上**
   （外仓 `6a003bd` 记录了决策侧在验收后推送）。结论仍是「本任务未 push」，但**过程里我先猜后查**，
   这里记下来。
5. **溯源日期我没有编。** 任务书 §2.2 明确警告上一批有人写了编造日期（`2026-02-15`）。
   我写进注释的 `2026-09-29` 有两个可核对的出处：①它是**已提交**在起点 HEAD 的
   `docs/scripts/check_rename_map.py` 的 TASK-152 注释块里记录的日期；②我另外读了机器时钟
   （`2026-09-29 09:09:36 +08:00`）。注释里也**明说**「TASK-153 没有采集、不主张自己的日期」。
   我**没有**执行任何 hof-rs 的对象库读取，因为本任务不需要重新采集。
6. **我没有做的（以免被读成遗漏）**：
   * **没有**重建引擎（§4.4：不含编译输入，重建只让二进制 sha 变、锚点自报变成 HEAD，是新代码之外的噪音）。
   * **没有**为了让 `g09` 显示 `ANCHOR_EQUAL` 而传 `-Anchor`/伪造 `-VersionText`。
   * **没有**重新生成 `docs/tools_list.renamed.json`（§6.2 第 1 条，含理由与留痕）。
   * **没有**改 `mcp029`/`mcp032`（§6.2 第 2 条、§6.3 第 2 条）。
   * **没有**改 `.gitignore`、`.gitattributes`、`tools\run_gates.ps1`、任何 `tests/**`、任何门脚本的断言。
   * **没有**改 hof-rs 侧任何文件（§5.3）；**没有** push（§5.2）。
7. **「未复现」与「已修复」的用词**：本报告**没有**把任何未复现的东西写成已修复。两次植入的**红**、
   门退出码、`git hash-object`、端口状态都是原始输出；`IDENTICAL True` 是两条命令产物的哈希对比结果；
   `PASS=30 / FAIL=0` 是对 `g05.stdout.txt` 的机器计数。所有引用都在 `recovery\work\task153\` 里可复核。
