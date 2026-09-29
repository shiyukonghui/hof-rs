# TASK-152 — `g05` 自包含化：引擎门不再依赖 hof-rs 的工作文件

* 执行者：实现子代理（无上游对话上下文；唯一任务来源 `godot-mcp\recovery\tasks\TASK-152.md`）
* 引擎仓：`F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`），起点 HEAD `035edfce7f`（工作树干净）
* 三个本地提交（**未 push**）：
  * `069a2e2ea8` **门自包含**：2 文件 / 34 增 3 删
  * `e1fbc8ec7f` **文档 + 保持 g08 绿**：2 文件 / 11 增 4 删
  * `bef4be0407` **溯源日期修正**：1 文件 / 1 增 1 删
  * **最终 HEAD = `bef4be0407`**；工作树 `git status --porcelain` 空
* 脚本 / 原始证据：`godot-mcp\recovery\work\task152\`（`materialise_baseline.py`、`exp1_plant_byte_exact.py`、
  `exp2_plant_map.py`、`ast_scan_g05.py`、`run_gates_task152.ps1`、`selfcheck.out.txt`、
  `exp1-byte-exact.out.txt`、`exp2-map-plant.out.txt`、`g05-checks.out.txt`、`gates\task152-final2\`）
* 报告：本文件。

---

## 1. 结论

**选了 A（改为自包含）**，未选 B。

| 项 | 结果 |
|---|---|
| `g05` | **exit 0，30/30 全 PASS（`RESULT: PASS (all checks green)`）**，含原 `B0`/`B1`/`B2` |
| `g01` | exit 0 — `160/160 passed`，`6801/6801 assertions`，`SUCCESS!` |
| `g02` | exit 0 — `1586/1586 passed`，`431114/431114 assertions`，`SUCCESS!` |
| `g04` | exit 0 — `3/3 checks passed`（editor 154 / game 73 / contract 177，`guard_user_port_9877 pid_before=-1 pid_after=-1`） |
| `g09` | exit 0 — `ANCHOR_JUDGE VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT`，`ANCHOR=035edfce7`，`HEAD=bef4be040`，`RED_COUNT=0`，`RESULT PASS`（**不是我放宽了语义，见 §4.3**） |
| `g10` | exit 0 — `22/22 cases passed` |
| 其余 | `g03`/`g06`/`g07`/`g08` 全 exit 0（`TOOL-GROUPS CHECK PASS` / `TAUTOLOGY CHECK PASS` / `PROBES: 10/10` / `UNCLASSIFIED = 0`） |
| 十道门合计 | **10/10 exit 0**（TASK-151 报告里的「唯一红 g05」在本任务后消失） |
| 非空洞性 | 两次受控植入**都变红**：基准里改一条 `name` ⇒ 红在 **`B2`**；映射里改一条 `new_name` ⇒ 红在 **`D1`**；两次均**逐字节复原** |

### 1.1 为什么选 A 而不是 B

B（把冻结常量更新为 hof-rs 的新值 `50c5fb42…`/177）能让今天的门变绿，但它**保留跨仓耦合**：
门继续把另一个仓的**工作文件**当判据，hof-rs 下一次合法演进（再采夹具、再改文件名、把工作副本删掉）会
**再一次**让引擎门无缘由变红。这与 D225 的诊断是同一个病，只是把今天这一片止疼了。A 把基准搬进被审计的
仓库，让「门的输入」与「门审计的对象」同属一个 git 仓库、同一条提交历史，跨仓漂移这一类故障**不再存在**，
而 `B0/B1/B2` 的**强度一点没降**（同一组字节、同一个 sha256、同一个条数）。

**没有降低门的强度**：新基准是旧基准的**逐字节副本**（`git hash-object`
`543b49b2583bf06c3aba2a320649a31eda272e3e` 与 hof-rs 重采前的那份 blob **完全相同**，见 §2、§3.3），
`OLD_CONTRACT_SHA256` 与 `174` 一个字没改，`B1` 的字面量只是换成命名常量 `OLD_CONTRACT_TOOL_COUNT`。

---

## 2. 改动清单与溯源

### 2.1 文件改动

| 文件:行 | 改动 |
|---|---|
| `modules/mcp_server/docs/rename-baseline-tools-list.json`（新，1 行 48749 B） | **新增**的引擎内冻结基准 = hof-rs 旧夹具的逐字节副本（无换行符，整文件一行 JSON） |
| `modules/mcp_server/docs/scripts/check_rename_map.py:76-111` | `DEFAULT_OLD_CONTRACT` 由 `r"F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json"` 改为 `os.path.join(DOCS, "rename-baseline-tools-list.json")`；新增 26 行溯源注释块（路径 / 字节数 / 条数 / sha256 / 来源 blob / 采集命令 / 日期） |
| `check_rename_map.py:113` | 新增常量 `OLD_CONTRACT_TOOL_COUNT = 174`（紧邻既有的 `OLD_CONTRACT_SHA256`，未改动后者） |
| `check_rename_map.py:192-193` | `B1` 断言里的字面量 `174` 换成 `OLD_CONTRACT_TOOL_COUNT`（**断言表达式与措辞未变**） |
| `modules/mcp_server/docs/MCP-SERVER-HANDOVER.md` §3.10(k) | 原「g05 三条红与本任务无关」段落**保留原文**，其后追加 TASK-152 关闭说明（新基准路径、未变的三个冻结值、两次非空洞性实验、AST 扫描结论） |

**未改**：`tool-rename-map.json`、`tools_list.renamed.json`、`docs/scripts/template.md`、`TOOL-BRIEF.md`、
其余任何门脚本、任何既有检查的断言。`git diff --stat 035edfce7f..HEAD` 只有上表 3 个文件。

### 2.2 新基准的溯源（记录在常量旁边的同一段注释里）

```
path   : modules/mcp_server/docs/rename-baseline-tools-list.json   (与脚本同目录)
bytes  : 48749          tools: 174          eol: 无换行符
sha256 : 8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54
source : hof-rs `tests/fixtures/mcp/tools_list.json` 在其 DR-42 重采**之前**的状态
         (hof-rs commit db2eed7^, git blob 543b49b2583bf06c3aba2a320649a31eda272e3e)
taken  : 2026-09-29，命令
         git -C F:\moonbit-hof-rs cat-file blob 543b49b2583bf06c3aba2a320649a31eda272e3e
         （对 hof-rs 对象库的**纯读**；hof-rs 侧未写入任何字节），随后逐字节写入本仓
```

采集时的原始输出（`recovery\work\task152\materialise_baseline.py`）：

```
blob        543b49b2583bf06c3aba2a320649a31eda272e3e
bytes       48749
crlf=0 lf=0 bare_cr=0
sha256      8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54
tools       174
written     F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\docs\rename-baseline-tools-list.json
written_sha 8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54
equal       True
EXIT=0
```

> **巧合，不是错误**：`543b49b2583b…` 既是 hof-rs 里那份旧夹具的 **blob id**，也是它进了引擎仓之后的
> **blob id** —— 因为它是同一串字节。这正是「逐字节副本」的机器可核对形式。

### 2.3 「不再读仓外路径」的机器判据

不只靠 grep（注释里必然还会提到 hof-rs，那是溯源，不是代码路径）。`recovery\work\task152\ast_scan_g05.py`
用 AST 把**模块与函数 docstring 排除掉**之后，逐个检查 `ast.Constant` 字符串与每个 `open()` 的实参：

```
docstrings excluded: 2
string-literal hits  : 0

open() calls:
  line 143  path          (--map,        默认为 DOCS/tool-rename-map.json)
  line 190  old_path      (--old-contract, 默认为 DOCS/rename-baseline-tools-list.json)
  line 175  map_path      (--map,        默认同上)
  line 302  contract_path (--contract,   默认为 DOCS/tools_list.renamed.json)
SCAN_EXIT=0
```

即：脚本里只剩 `hof-rs` 出现在**注释**中（3 处 `TASK-152` 行），**没有**任何可执行字符串指向仓外。
三个默认路径全部由 `DOCS = os.path.dirname(HERE)` 派生，因此门在**任何** checkout 位置都自洽。

---

## 3. 非空洞性受控实验（三步原始输出）

**判据说明**：任务书要求「必须红在**该条检查**上（不是别的检查顺带红了）」。植入会同时改动**文件字节**，
所以 `B0 old contract sha256 frozen` **必然**跟着红 —— 这正是 `B0` 该有的行为（它就是在钉这份文件的字节）。
为了让「红」精确归因到**改名/映射**这一条，下面的实验 1 用**纯字节替换**注入（只改一个名字 token，其余
字节含空白与键序全不动），实验 2 则注入**映射**侧、完全不碰基准，使红的条数收敛到 1 条。

### 3.1 实验 1 — 在**基准**里植入改名回归 ⇒ 红在 `B2`

注入：`"name":"get_project_info"` → `"name":"project_mcp_get_info"`（该名字**不在**映射的 `old_name` 集合里，
也**不在** `new_name` 集合里，因此 B 段双向差集是唯一能动的检查）。

```
PLANT victim name           : "name":"get_project_info"
PLANT victim occurrences    : 1
PLANT victim in map old_name: True
PLANT injected in map old     : False
PLANT injected in map new     : False
PLANT baseline bytes 48749 -> 48753
PLANT planted baseline sha256: 2b8f2657b39447b861383bc852258c91ad527754533f0771acdb027f4f22d03b
PLANT only-the-name-differs   : True
```

`g05` 在该状态下的真实输出（节选，完整见 `recovery\work\task152\exp1-byte-exact.out.txt`）：

```
[PASS] A1 total == 174                                            total=174
[PASS] A2 len(tools) == 174                                       len=174
[FAIL] B0 old contract sha256 frozen                              2b8f2657b39447b861383bc852258c91ad527754533f0771acdb027f4f22d03b
[PASS] B1 old contract tools == 174                               len=174
[FAIL] B2 bidirectional diff empty                                contract-only=['project_mcp_get_info'] map-only=['get_project_info']
[PASS] B3 old_name unique                                         distinct=174
...
[PASS] D1 L1..L4 over all 174 new_name                            violations=[]
[PASS] G6 contract count == map total - 2 unregister - 1 merge + _meta.added_count 177 == 174 - 2 - 1 + 6 = 177
RESULT: FAIL (2 failing checks): B0 old contract sha256 frozen, B2 bidirectional diff empty
GATE_EXIT=1
FAIL_LINES=2
```

**读法**：`B2` 的 `contract-only` / `map-only` **精确指认了被改的那一个名字**（`['project_mcp_get_info']`
与 `['get_project_info']`），其余 28 条检查（含 `D1`、`C1`、`F*`、`G*`）**全绿** —— 门没有被改瞎，它认出了
「映射与旧契约不再一一对应」。若植入后仍绿，按任务书就是 fail；这里**不是**。

### 3.2 实验 2 — 在**映射**里植入错误映射 ⇒ 红在 `D1`（单条归因）

注入：`"new_name": "editor_capture_screenshot"` → `"new_name": "capture_screenshot"`（旧式名字，通道前缀丢失）。
基准**一个字节没碰**，所以 `B0/B1/B2` 全部应保持绿，只有命名 lint 该动。

```
PLANT map victim name        : "new_name": "editor_capture_screenshot"
PLANT map victim occurrences : 1
PLANT map bytes 70917 -> 70910
PLANT planted map sha256     : 16e58332804ef60d92bd5cbc0beb50621bbdddfada1732209abdc961850e3c71
PLANT baseline untouched sha : 8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54
...
[FAIL] D1 L1..L4 over all 174 new_name                            violations=[('capture_screenshot', 'L1 pattern')]
...
RESULT: FAIL (1 failing checks): D1 L1..L4 over all 174 new_name
GATE_EXIT=1
FAIL_LINES=1
  [FAIL] D1 L1..L4 over all 174 new_name      violations=[('capture_screenshot', 'L1 pattern')]
```

**读法**：红的**恰好一条**，且就是那条命名检查，`violations` 里直接点名 `capture_screenshot`。
两次实验合起来覆盖了任务书 §3 给的两种植入形态（「不在映射里的旧式名」与「错误的 `old→new` 映射」）。

### 3.3 恢复证明（逐字节）

实验完成后、且在**任何后续提交之前**执行（`recovery\work\task152\selfcheck.out.txt` 原文）：

```
=== git status --porcelain (must be empty) ===
<empty>
=== git diff --stat (must be empty) ===
<empty>
=== git hash-object vs HEAD blob ===
EQUAL  modules/mcp_server/docs/tool-rename-map.json
         work_blob=743bc79c585cc013a6bd3e900e79d4dc5e042eb4
         head_blob=743bc79c585cc013a6bd3e900e79d4dc5e042eb4
EQUAL  modules/mcp_server/docs/rename-baseline-tools-list.json
         work_blob=543b49b2583bf06c3aba2a320649a31eda272e3e
         head_blob=543b49b2583bf06c3aba2a320649a31eda272e3e
EQUAL  modules/mcp_server/docs/scripts/check_rename_map.py
         work_blob=24c6bb7d7a6e6ca5ab262bd7efce5a434ebeecde
         head_blob=24c6bb7d7a6e6ca5ab262bd7efce5a434ebeecde
EQUAL  modules/mcp_server/docs/tools_list.renamed.json
         work_blob=3b1b191dc42f1cec8bc7cdd3504247c935b52f5e
         head_blob=3b1b191dc42f1cec8bc7cdd3504247c935b52f5e
```

* 恢复用 `git checkout -- <两个被植入的文件>`，恢复后**双空**（`status --porcelain` 与 `diff --stat`）
  **且** `git hash-object` == 当时 HEAD 的 blob（CRLF 敏感 → 用 blob id 而不是文本比较）。
* 上面 `check_rename_map.py` 的 `24c6bb7d…` 是**当时** HEAD（`e1fbc8ec7f`）的 blob；`bef4be0407` 把溯源
  日期 `2026-02-15` 订正为 `2026-09-29` 后它变成 `HEAD:…` 的新 blob（**只差这一个日期**，见 §7）。
  被植入的两个文件在三个提交里从未被 `add`，`543b49b2…` 至今仍是它们的 blob，所以该证明**不受后续提交影响**。
* 引擎仓对 CRLF 敏感这一点已核对：`.gitattributes` 为 `* text=auto eol=lf`、本机 `core.autocrlf=true`，
  而基准文件**不含任何换行符**（`crlf=0 lf=0 bare_cr=0`），因此 checkout/add 都不会改写它 ——
  这也解释了为什么 174 条 JSON 是「整文件一行」。

---

## 4. 门结果（真实输出）

运行器：`recovery\work\task152\run_gates_task152.ps1`，命令集与顺序是
`godot-mcp\tools\run_gates.ps1:214-225` 的**逐字复制**，无任何替换；每个门在自己的 `cmd.exe` 子进程里跑、
各自的 stdout/stderr 落盘、`GATE_EXIT=!ERRORLEVEL!` 用延迟展开写在子进程内。

* 证据目录：`recovery\work\task152\gates\task152-final2\`（`summary.txt` + `g01..g10.{stdout,stderr}.txt`）
* **未做任何引擎重建**，也不需要：本任务没碰任何编译输入（3 个文件全是 `.json`/`.md`/`.py`）。

### 4.1 逐门退出码与关键行（HEAD=`bef4be0407`，mono `4.8.dev.mono.custom_build.035edfce7`）

| 门 | exit | 关键输出 |
|---|---|---|
| g01 | **0** | `test cases: 160 \| 160 passed \| 0 failed \| 1429 skipped` / `assertions: 6801 \| 6801 passed` / `Status: SUCCESS!` |
| g02 | **0** | `test cases: 1586 \| 1586 passed \| 0 failed \| 3 skipped` / `assertions: 431114 \| 431114 passed` / `Status: SUCCESS!` |
| g03 | **0** | `TOOL-GROUPS CHECK PASS  BYTES 5681  SHA256 b83d79d3e3d080ce460b61ca99a46a126d6a6c45eb3d51d7977a52a991b7fbc7` |
| g04 | **0** | `3/3 checks passed`，`editor port=9888 tools=154` / `game port=9889 tools=73` / `contract=177`，逐字抽样 `name=True description=True inputSchema=True`，`guard_user_port_9877 pid_before=-1 pid_after=-1` |
| **g05** | **0** | **`RESULT: PASS (all checks green)`，30/30 PASS，0 FAIL**（含 `B0`/`B1`/`B2`，见 §4.2） |
| g06 | **0** | `TAUTOLOGY CHECK PASS (every hit is pinned; scanned=2 file kind(s) under 2 root(s))` |
| g07 | **0** | `PROBES: 10/10` |
| g08 | **0** | `BUCKET UNCLASSIFIED = 0` / `RESULT: PASS (every occurrence of 171/173/175/176/152/72/153 is classified; none is UNCLASSIFIED)` |
| g09 | **0** | `ANCHOR_JUDGE VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT` / `ANCHOR=035edfce7 ANCHOR_REPORTED=035edfce7 HEAD=bef4be040` / `DIFF_COUNT=3 SAFE_COUNT=3 RED_COUNT=0` / `RESULT PASS` |
| g10 | **0** | `22/22 cases passed`（含 `guard_user_port_9877` PASS） |

**合计 10/10 exit 0。**

### 4.2 `g05` 的 30 条检查全绿（原任务书说 27 条，实际 30 条）

`recovery\work\task152\g05-checks.out.txt`：`PASS = 30`、`FAIL = 0`、`exit = 0`：

```
[PASS] B0 old contract sha256 frozen                              8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54
[PASS] B1 old contract tools == 174                               len=174
[PASS] B2 bidirectional diff empty                                contract-only=[] map-only=[]
[PASS] B3 old_name unique                                         distinct=174
...
RESULT: PASS (all checks green)
```

顺序为 `A1 A2 B0 B1 B2 B3 E1 E2 E3 E4 C1 C2 D1 D2 D3 F1 F2 F3 F4 F5 F6 F7 F8 F9 G1 G2 G3 G4 G5 G6`。
`B0` 报的 sha 与改动前**逐字相同**（`8f8051c4…`），`B2` 仍是双向空差集。

### 4.3 `g09` 的 `ANCHOR_STRUCTURAL_EQUIVALENT`：**未放宽语义**，请按偏离读

任务书 §4 写「`g09`（ANCHOR_EQUAL 应指向当前 HEAD）」。实测得到的是
`ANCHOR_STRUCTURAL_EQUIVALENT`，**不是** `ANCHOR_EQUAL`。原因链（**我没有任何选择余地，也没有为此改一行代码**）：

1. mono 二进制是在 HEAD=`035edfce7f` 时构建的（mtime `2026-09-29 08:31:03`，`--version` 自报 `035edfce7`）；
2. 我在它之后提交了 3 个 commit，**HEAD 必然前进**到 `bef4be0407`；
3. 本任务属于「门/文档」类改动，**无法**让「二进制自报锚点 == HEAD」在不重建引擎的前提下成立；
4. 重建会**改变二进制字节**（上一批的教训：构建不可位级复现），而且新二进制的 `--version` 仍会自报
   `bef4be0407` —— 那会让「锚点」不再对应它所含的 TASK-151 修复，正是上一批验收者拒绝做的**假绿**；
5. `check_engine_anchor.ps1` 的判据（该文件 `:12-25` 自述）里，`ANCHOR_STRUCTURAL_EQUIVALENT` **是 PASS**：
   A 是 H 的祖先 **且** `git diff --name-only A..H` **不含任何编译输入**。实测 `DIFF_COUNT=3`、`SAFE_COUNT=3`、
   `RED_COUNT=0`，三个文件分别是 `MCP-SERVER-HANDOVER.md`、`rename-baseline-tools-list.json`、
   `check_rename_map.py` —— 三者都在该判据自带的非编译白名单里（`:87` 的 `.md`/`.json`/`.py`）。

**我没有碰这个判据、没有加白名单、没有传 `-Anchor` 绕过**（命令里传的是二进制**自报**的 `--version`）。
`ANCHOR_STRUCTURAL_EQUIVALENT` 的字面意思**不是**「等于 HEAD」，本报告也不这么写它：它说的是
「这两个 commit 之间的差异**不可能**改变被编进二进制的行为」——这恰好是本次改动需要证明的东西。

**若要看到 `ANCHOR_EQUAL`**：在 `bef4be0407` 上重建 mono（`modules\mcp_server\scripts\mcp057_build_mono.cmd`），
新二进制会自报 `bef4be0407`，`g09` 即为 `ANCHOR_EQUAL`。我**没有**这样做，理由如上第 4 条。

### 4.4 二进制信息（**不作为新鲜度判据**，仅登记）

```
BINARY bin\...mono.console.exe  bytes=300544     sha256=8746a34a79aaab5dd3b1d5600d4188bee8f5e8943b18e2c763a419b3476e6dbf mtime=2026-09-29 08:31:03 version=4.8.dev.mono.custom_build.035edfce7
BINARY bin\...mono.exe          bytes=194216960  sha256=08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a mtime=2026-09-29 08:31:02 version=4.8.dev.mono.custom_build.035edfce7
BINARY bin\...console.exe       bytes=300544     sha256=3feeb6958a5ac8f5f8ea53319e1d6ec12385eccadc335ef42a23736c37b9359e mtime=2026-09-29 07:55:58 version=4.8.dev.custom_build.97fc49df4
BINARY bin\...exe               bytes=193631232  sha256=15cbdeca6eae49f8dfc9853e6d1d336a3145767de6eb75725b0e053d59e046c1 mtime=2026-09-29 07:55:57 version=4.8.dev.custom_build.97fc49df4
```

按任务书 §4 的教训：**二进制 sha256 只登记、不作判据**。新鲜度的三段证据是
① `--version` = `4.8.dev.mono.custom_build.035edfce7`（与 TASK-151 验收时一致）
② `g01` 仍是 `160/160`、`g02` 仍是 `1586/1586`（与 TASK-151 报告逐字相同，**没有**少一条，也没有多出
   TASK-152 的用例——本任务确实没加测试）③ `g10` 的探针把活体端点跑过一遍（`22/22`）。
**全程未构建**，因此不存在「构建输出被抑制」的问题。

---

## 5. 禁区自查（真实输出）

原文：`recovery\work\task152\selfcheck.out.txt`。

### 5.1 端口：9877 未碰，9888/9889 已释放

```
port 9877 : <none listening>
port 9888 : <none listening>
port 9889 : <none listening>
```

* 门运行器在**运行前后各读一次**监听状态（`Get-NetTCPConnection -State Listen`，**只读**，不连不绑）：

```
GATES_CANONICAL PORT_9877_BEFORE=          PORTS_9888_9889_BEFORE=/
GATES_CANONICAL PORT_9877_AFTER=           PORTS_9888_9889_AFTER=/
```

* `g04` 与 `g10` **内部**各自带的守卫也报 `guard_user_port_9877 pid_before=-1 pid_after=-1`（`-1` = 该端口上
  本来就没有进程，脚本按设计不去创建）。
* 本任务**没有**起过任何 MCP 服务器；用到的端口全部来自既有门脚本（`accept_m1.ps1:55-56` 的 9888/9889）。
* 收尾复核：三端口**均无监听**（上表即收尾时读的）。

### 5.2 未 push

```
git rev-list --left-right --count HEAD...origin/feature/mcp-server-module-rebuild
5	0            ← 本地领先 origin 5 个提交，origin 侧 0 个新提交（本任务新增的是其中 3 个）
git rev-list --left-right --count 035edfce7f...origin/... 
3	0            ← 相对本任务起点新增 3 个，全部只在本地
reflog 最近 5 条全部是 commit:（没有任何 push/fetch 改写）
```

`git remote -v` 只有 `origin git@github.com:shiyukonghui/godot.git`，`@{u}` =
`origin/feature/mcp-server-module-rebuild`；`git rev-list` 的右列是 **0**，即**没有**任何新对象到达 origin。

### 5.3 hof-rs 侧零改动

```
hof-rs git status --porcelain = ?? godot-mcp/recovery/work/task152/   ← 只有本任务的证据目录（未跟踪）
hof-rs fixture sha256 = 50c5fb4204ee5b957b017eb994e7f7bd73f9b299e6aa9471d5cf11683e067da0
hof-rs fixture bytes  = 71481
hof-rs fixture mtime  = 2026-09-28 22:37:34     ← 早于本任务开工（2026-09-29 08:4x），从未被写
engine baseline sha256 = 8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54
engine baseline bytes  = 48749
```

* `tests/fixtures/mcp/tools_list.json` 的 **mtime 早于我开工**，sha 仍是 hof-rs 重采后的 `50c5fb42…`/177
  ⇒ 我只**读过**（`git cat-file` 从对象库读 blob，连工作副本都没重读）**没有**写。
* hof-rs 工作树里唯一的新东西是本任务的证据目录 `godot-mcp/recovery/work/task152/`（**任务书授权的落点**）。
  `src/**`、`tests/**`、`config/**`、`.spec/**`、`PRD-mario.md` 全部**零改动**。
* **禁改区内没有被改的文件**：hof-rs 的夹具 sha 与 mtime 都证明未动。

### 5.4 无新依赖

`check_rename_map.py`（HEAD 版本）的全部 import：

```
import argparse
import collections
import hashlib
import json
import os
import re
import sys
```

七个全是 Python 标准库，且**改动前后完全一致**（`git diff` 里没有任何 `import` 行被增删）。
未安装任何包，未改 `requirements`/`pyproject`。

### 5.5 未放宽/删除任何既有检查

* `g05` 的 30 条断言**一条没删**；`B0` 的 sha 常量、`B2` 的双向差集表达式、`C1/C2/D1..D3/E*/F*/G1..G6` 全部原样。
* `check_hardcoded_counts.py`（g08）的**任何模式都没改** —— 见 §7 第 2 条：它一开始因为我的注释多出现一个
  未被分类的 `152` 而红，我的修法是**把自己的注释行整成连续注释行**（满足它既有的 `^\s*#` → FROZEN 规则），
  **不是**去加白名单/放宽扫描。
* `check_engine_anchor.ps1`（g09）**一个字节未改**。
* 没有任何 `--no-verify`、`|| true`、`try/catch` 吞错，没有抑制构建/测试输出。

---

## 6. 遗留风险与未验证项（区分实测与推断）

### 6.1 实测

1. **`g05` 在改动后确实全绿且仍能抓改名回归**：§3 两次植入分别红在 `B2`（点名被改的名字）与 `D1`（点名违规
   的 `new_name`），恢复后双空 + blob 相等。**这是实测**。
2. **脚本不再有访问仓外的代码路径**：AST 扫描字符串常量命中 0、`open()` 实参只有三个 `DOCS` 派生默认值。
   **这是实测**。
3. **hof-rs 侧零写入**：夹具 mtime 早于开工 + sha 与 hof-rs 自己重采后的值一致。**这是实测**。
4. **十道门 10/10 exit 0**：§4 的逐门退出码与关键行。**这是实测**。
5. **`g09` = `ANCHOR_STRUCTURAL_EQUIVALENT`**（不是 `ANCHOR_EQUAL`）：§4.3。**这是实测**。

### 6.2 推断（**不是**实测，勿当证据用）

1. **`ANCHOR_EQUAL` 若不重建就可达** —— 不成立，我没试也不需要试；`bef4be0407` 上重建后应当得到
   `ANCHOR_EQUAL` 属于**推断**（依据是该判据的 `A == H counts` 分支），我没有重建来验证（§4.3 第 4 条）。
2. **`g05` 从此不再受 hof-rs 演进影响** —— 这次是的（新基准在引擎仓内，脚本无仓外路径）。但**同一类耦合
   仍在别的脚本里**：`modules/mcp_server/scripts/gen_renamed_contract.py:1800`（`DEFAULT_OLD_CONTRACT`）与
   `:1804`（`OLD_CONTRACT_SHA256`）同样指向 hof-rs 的同一份夹具并冻结同一个 sha256（**已逐行核对**）；
   `accept_m1.ps1:17-24` 的注释、`docs/B0-BRIEF.md:9`（「旧契约（只读输入）」表格行）、
   `docs/DESIGN-DETAIL.md:7`、`docs/REQUIREMENTS.md:1`、`docs/TOOL-NAMING.md:375`、
   `docs/scripts/template.md:451`、`docs/tasks/TASK-001-…md:21` 也仍以文字记载 hof-rs 路径
   （`B0-BRIEF.md:121` 是任务清单条目，**不是**路径，此处更正）。**它们都不在 `g05` 的执行路径上**
   （`g05` 只跑 `check_rename_map.py`，见 `tools\run_gates.ps1:219`），所以任务书 §0 的目标已达成；
   但「整个模块不再依赖跨仓输入」**没有**达成 —— **这是本次实测到的范围边界，也是给决策者的建议**（见 §6.3）。
3. **`B0` 在植入下必然红是对的行为** —— 依据是它钉的就是那份文件的字节；我认为这是设计意图，但**任务书
   没有明确要求**「植入时只能红一条」，我用实验 2 提供了一个单条红的版本（§3.2）。这一点属于**推断**。
4. **`bef4be0407` 的溯源日期订正不影响门语义** —— 只改了注释里一个日期字符串；`g05`/`g08` 事后已复跑为
   exit 0（**实测**），但「不影响任何判据」的完整证明仍然是**推断**（依据：`git diff` 只有 1 行、且在
   `#` 注释里）。

### 6.3 建议给决策者（不在本任务范围内，我**没有**擅自扩大改动）

1. **顺带自包含 `gen_renamed_contract.py`**：它不该在生成契约时再要求 hof-rs 的路径与 sha。现在引擎仓里
   已经有 `docs/rename-baseline-tools-list.json`，把它设成同一默认即可（一行改动 + 同一段溯源），
   这样「契约生成」与「契约自检」用**同一个**引擎内基准，跨仓耦合在这个模块里就彻底清掉。
2. **`g09` 的 `ANCHOR_EQUAL` 期望值在任务书里偏严**：对任何「只改 `.json`/`.md`/`.py`」的门类任务，
   不重建就拿不到 `ANCHOR_EQUAL`。建议任务书把判据写成「`ANCHOR_EQUAL` **或** `ANCHOR_STRUCTURAL_EQUIVALENT`
   且 `RED_COUNT=0`」，否则会诱导执行者去做「重建以对齐锚点」这种**制造假绿**的动作。
3. **给门运行器加一行机器可读的「已知红」**（TASK-151 验收报告 §7.2 也建议过）：本任务后 `g05` 不再是
   已知红，但若将来又出现跨仓漂移，`summary.txt` 里应能与偶发红区分开。

---

## 7. 诚实披露（返工、猜错、绕过的尝试）

1. **实验 1 第一版做错了，我重做了。** 第一版用 Python `json.load` + `json.dumps` 重写基准，结果**整个
   文件的格式都变了**（字节数 48749 → 52496），于是红的是 `B0`+`B2` 两条，而 `B0` 的红**不能**归因于改名
   （它只是「文件被动过」）。这不满足「必须红在该条检查上」的严格要求，所以我**废弃该结果**，改成
   **纯字节替换**（只换一个名字 token，其余字节全不动，48749→48753），并把这条失败也留在
   `exp1.out.txt` 里没有删除。第二次才是 §3.1 引用的版本。
   * 教训：**重序列化不是「改一个字段」**；要证明「某个检查对某个改动敏感」，就必须让那次改动只包含那个改动。
2. **我一开始把 `g08` 弄红了，那是我的锅，不是既有红。** 第一次十道门跑出 `g08 exit=1`，两条
   `UNCLASSIFIED` 都指向我新加的注释行（`check_rename_map.py:15`、`:63` 的 `[152]`）：我把
   `TASK-152` 写在**续行**上，而续行不是以 `#` 开头，于是 `check_hardcoded_counts.py` 既有的
   `^\s*#` → FROZEN 规则匹配不到。我的修法是**改自己的注释**（把那几行写成连续注释行），
   **没有**去改扫描器的任何模式。修完复跑 `g08 exit=0`、`UNCLASSIFIED = 0`。
   * 这条如果不说，就会看起来像「g08 本来就红」，而它本来**不是**。
3. **我把一个制表符级的手误写进了提交：溯源日期。** 注释里我写了 `taken : 2026-02-15`——**是我从
   记忆里编的日期**，不是实测。发现后单独用一个提交（`bef4be0407`）订正为 `2026-09-29`（读了机器时钟）。
   这也意味着：**`selfcheck.out.txt` 里 `check_rename_map.py` 的 blob `24c6bb7d…` 不是最终 HEAD 的 blob**
   （最终是订正日期后的版本）。被植入的两个文件不受影响，所以 §3.3 的恢复证明依然成立；这个差异我在
   §3.3 里也写明了，没有藏。
4. **我最初想在 `check_rename_map.py` 的模块 docstring 里写「这个脚本不读仓外路径」的说明，后来撤掉了。**
   原因：`check_hardcoded_counts.py` 会把 `152` 数成 hardcoded count，而我在 docstring 里写这个数字会
   在 g08 里制造噪音。最终这块说明放进了**独立的 AST 扫描脚本**（`ast_scan_g05.py`）与**本报告 §2.3**，
   让「不读仓外路径」这件事**可执行、可复跑**，而不是靠一句自述。这是一次**主动放弃已写好的改动**，
   不是被谁要求。
5. **我主动多改了一个文件（`MCP-SERVER-HANDOVER.md`）。** 严格按 §2 的「改动清单」它不在必改项里，
   但该文件 `§3.10(k)` 明文写着 g05 的三条红是「已知、与本任务无关、不得为变绿改常量」。本任务把这条
   红消灭了，如果不同步更新，交接文档就会**对下一位读者说谎**（或诱导他去"恢复"一个已经不存在的问题）。
   改动方式是**保留原段落**、只在其后追加 TASK-152 的关闭说明，不含删改既有结论。
6. **我没有做的（以免被读成遗漏）**：
   * **没有**重建引擎。理由见 §4.4 与 §4.3：本任务不含编译输入，重建只会让二进制 sha 变化并让
     `--version` 变成 `bef4be0407`，而那个二进制里同样**不含**任何新代码 —— 纯粹是噪音。
   * **没有**为了让 `g09` 显示 `ANCHOR_EQUAL` 而传 `-Anchor`/`-VersionText` 伪造锚点。
   * **没有**动 `gen_renamed_contract.py`（它是同类耦合，但**不在 g05 的执行路径上**；擅自扩大改动会把
     「生成器」卷进来，而任务书明确只要求 g05 自包含）。已作为建议写进 §6.3。
   * **没有**改 `.gitignore`、`tools\run_gates.ps1`（在主仓，不在我的写范围）、任何 `tests/**`。
   * **没有** push；三个提交全在本地。
7. **「未复现」与「已修复」的用词**：本报告没有把任何未复现的东西写成已修复。两次植入的**红**是原始
   输出；`B2`/`D1` 指认的名字是原始输出里的字面量；十道门的退出码来自子进程内 `!ERRORLEVEL!`，
   不是我手写的。所有引用都在 `recovery\work\task152\` 里可复核。
