# TASK-154 报告 —— 引擎侧收尾：两个历史取证脚本去跨仓引用 + `_meta` 历史说明（`g09` 护栏机器化：未做，附证据）

> 执行者：实现子代理（无上游对话上下文，唯一任务来源 `recovery/tasks/TASK-154.md`）
> 落点：引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`，分支 `feature/mcp-server-module-rebuild`
> 起始 HEAD `28432f859f` → 结束 HEAD `fc63af77c33368c4a1bb839c95d19750554f63a3`
> 门运行器：外层仓 `F:\moonbit-hof-rs\godot-mcp\tools\run_gates.ps1`
> 证据脚本与原始输出：`F:\moonbit-hof-rs\godot-mcp\recovery\work\task154\`（`*.ps1` + `*.out.txt`）

---

## 1. 结论 + 真实命令与退出码

**结论（一句话）**：任务书 §2.1 / §2.2 / §2.3 三项**必修项全部完成**，十道门 **10/10 exit 0**，未推、未改 hof-rs、未重生成冻结工件；§2.4（`g09` 护栏机器化）**明确不做**，因为其中两条**本来就是现有判据**、第三条**无法在不削弱判据的前提下机器化**（§5 给全部证据）。

### 1.1 提交（本地，未 push）

```
$ git -C F:\moonbit-hof-rs\godot-mcp\godot log --oneline -4
fc63af77c3 evid: fix a comment typo in the mcp029 guard block (TASK-154)
bdf654b108 docs: record _meta.generated_from as history, not current input (TASK-154)
627aeacee4 evid: drop the cross-repo fixture path and the user port from mcp032 (TASK-154)
56f93ca180 evid: read the pre-override wording from the engine baseline (TASK-154)
```

`$ git -C ... status --porcelain` → **0 行（干净）**
`$ git -C ... rev-list --count refs/remotes/origin/feature/mcp-server-module-rebuild..HEAD` → **4（ahead=4, behind=0）**
`refs/remotes/origin/feature/mcp-server-module-rebuild` tip = `28432f859f`（= 起始 HEAD）⇒ **这 4 个提交只在本地**。

### 1.2 十道门（改动前 / 改动后各跑一次）

```
$ cd F:\moonbit-hof-rs\godot-mcp
$ powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_gates.ps1 -RunGates -Tag task154_before
$ powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_gates.ps1 -RunGates -Tag task154_final
```

| 运行 | tag | tag 内 HEAD | 结果 |
|---|---|---|---|
| 改动前 | `task154_before` | `28432f859f` | 10/10 `exit=0`，`summary=F:\moonbit-hof-rs\godot-mcp\runs\gates\task154_before\summary.txt` |
| 改动后 | `task154_final` | `fc63af77c` | 10/10 `exit=0`，`summary=F:\moonbit-hof-rs\godot-mcp\runs\gates\task154_final\summary.txt` |

跑门脚本整体退出码 = **0**（两次）。

### 1.3 实际运行两个被改脚本（测试端口，9877 由守卫拒绝）

```
$ powershell -NoProfile -ExecutionPolicy Bypass -File modules\mcp_server\scripts\mcp029_clear_default_evidence.ps1 -OutRoot %TEMP%\task154-live-029
EXITCODE = 1   wall = 9.7s      → TASK-029 evidence: 20 checks, 2 failed

$ powershell -NoProfile -ExecutionPolicy Bypass -File modules\mcp_server\scripts\mcp032_d3_d4_d6_evidence.ps1 -OutRoot %TEMP%\task154-live-032
EXITCODE = 1   wall = 1.2s      → 在第 287 行一个**任务书之外、改动之前就存在**的 `-f` 格式化缺陷上崩溃（见 §7.1），未走完

$ powershell ... recovery\work\task154\probe_mcp032.ps1      # 只把那几个既有 `{` 双写的临时副本
EXITCODE = 1   wall = 11.3s     → TASK-032 evidence: 39 checks, 2 failed
```

### 1.4 端口守卫拒绝（不改脚本、不碰 9877）

```
$ ... mcp029_clear_default_evidence.ps1 -EditorPort 9877 -OutRoot ...
TASK-154 PORT GUARD: port 9877 is refused. This script uses the test ports only: 9888/9889.
exit=4
$ ... mcp032_d3_d4_d6_evidence.ps1 -GamePort 9877 -OutRoot ...
TASK-154 PORT GUARD: port 9877 is refused. This script uses the test ports only: 9888/9889.
exit=4
$ ... mcp029_clear_default_evidence.ps1 -EditorPort 1234 -OutRoot ...      # 集合外也拒绝
TASK-154 PORT GUARD: port 1234 is refused. This script uses the test ports only: 9888/9889.
exit=4
```

---

## 2. 改动清单（文件:行）+ 每个脚本的「改前语义 vs 改后语义」对照

### 2.1 `modules/mcp_server/scripts/mcp029_clear_default_evidence.ps1`（26174 B → 无 BOM、非 ASCII 字节 = 0）

| 行 | 改动 |
|---|---|
| L51–58 | 注释：把"read out of the frozen fixture"改为"read out of the frozen baseline" |
| L60–88 | 新增 TASK-154 溯源注释（为什么换源、等价性证据、如何复核） |
| L45–49 | **删除** `$UserPort = 9877`，替换为说明性注释 |
| L90–92 | **新增** `$ModuleRoot`（`$PSScriptRoot\..`）、`$Docs`、`$OldFixture = Join-Path $Docs 'rename-baseline-tools-list.json'` |
| L112–138 | **新增**端口拒绝守卫（测试端口集合检查 + `$PSScriptRoot` 中端口字面量检查，两处 `exit 4`） |
| L288–299 | **删除** `port_9877_owner_before`（含 `Get-ListenerPid -Port_ $UserPort`），**新增** `test_ports_only` |
| L436–441 | **删除** `port_9877_owner_after`，**新增** `test_ports_released` |

改前 → 改后语义（逐条）：

| 语义单元 | 改前 | 改后 | 是否等价 |
|---|---|---|---|
| 旧描述来源 | `F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json`（跨仓工作文件） | `docs/rename-baseline-tools-list.json`（引擎内冻结基准，`$PSScriptRoot\..\docs` 派生） | **等价**：两文件**整文件逐字节相同**（§2.4 表） |
| 取哪两条 | `get_test_report.description`、`get_test_report.inputSchema.properties.clear.description` | 同名同字段（基准 174 条中含该名） | **等价**（字节相同） |
| `old_fixture_readable` 判据 | 两条长度 > 0 | 不变 | 判据不变；**结果改变**：改前恒为 FAIL（hof-rs 现文件已是 177 条四通道、无 `get_test_report`），改后实测 **PASS** |
| `wire_clear_description_kept` | 线上 `clear.description` == 旧契约 `clear.description` | 不变 | 判据不变；改前线上 vs 空串 → FAIL，改后实测 **PASS** |
| 用户端口 | `$UserPort=9877`；`port_9877_owner_before` 断言"9877 有监听且 pid 不变"，`port_9877_owner_after` 复验 | 该端口**完全不再出现于逻辑中**；启动时若请求它则 `exit 4` | **替换**（见 §3）：把"环境前提"换成"本脚本只向引擎请求 9888/9889"的**可判定事实** |
| 其余 16 条检查（线上契约、纯读、字节相同、显式 clear、诚实空） | 不变 | 不变 | **不变**（实测 18 PASS / 2 FAIL，见 §2.4） |

### 2.2 `modules/mcp_server/scripts/mcp032_d3_d4_d6_evidence.ps1`（35879 B → 无 BOM、非 ASCII 字节 = 0）

| 行 | 改动 |
|---|---|
| L39–46 | 头注释：删去"9877 断言 pid 不变"，改为"9877 在启动时被拒绝" |
| L65–88 | **新增** TASK-154 溯源注释 |
| L89–91 | **新增** `$ModuleRoot` / `$Docs` / `$OldFixture`（引擎内基准） |
| L95–97 | **删除** `$UserPort = 9877` |
| L102–103 | **删除** `. mcp_port_guard.ps1` 的点源 |
| L105–136 | **新增**端口拒绝守卫（与 mcp029 同形） |
| L248–258 | `Start-Engine` 内**删除** `Register-McpPortGuardProcess` 记账，改为直接 `return Start-Process ...`（启动参数不变） |
| L353–362 | **删除** `New-McpPortGuard ...`，**新增** `test_ports_only` / `port_9888_free` / `port_9889_free` |
| L364 | **删除** `Register-McpPortGuardCommandLine`（对 `$import.command` 的记账） |
| L580–583 | **删除** `Complete-McpPortGuard` + `port_9877_guard`，**新增** `test_ports_released` |

改前 → 改后语义（逐条）：

| 语义单元 | 改前 | 改后 | 是否等价 |
|---|---|---|---|
| D6 旧描述来源 | 同上 hof-rs 跨仓路径 | 引擎内基准 | **等价**（整文件逐字节相同） |
| 取哪一条 | `get_game_node_properties.description`（及整 `inputSchema`） | 同 | **等价** |
| `d6_old_wording_readable` | 长度 > 0 | 不变 | 判据不变；改前恒 FAIL，改后实测 **PASS**（证据行：`frozen fixture get_game_node_properties.description = '获取运行中游戏指定节点的属性'`） |
| 端口语义 | `New-McpPortGuard -Port 9877 -PidBefore (Get-ListenerPid -Port_ 9877)`，`Start-Engine` 每次都记账，末尾 `Complete-McpPortGuard ... (Get-ListenerPid -Port_ 9877)` | 逻辑中不再出现该端口；请求集合外端口即 `exit 4`；末尾断言 9888/9889 已释放 | **替换且更早**：原判据是"**运行后**从记录里判断我们没占用它"，新判据是"**任何进程启动前**就已拒绝请求它"，并对测试端口加上"已释放" |
| D3/D4/D6 其余 36 条检查 | 不变 | 不变 | **不变**（实测 37 PASS / 2 FAIL，见 §2.4） |

**被删除的 `mcp_port_guard.ps1` 未改动**：它仍被 `mcp027/033/034/035/036/042/043/047/049/050/051/052/053/054/055/056/059/063/070/071/075/077/probe037` 等 30+ 个脚本点源使用，本任务只让 mcp032 不再使用它，模块本身一个字节未改（`git status --porcelain` 干净）。

### 2.3 `modules/mcp_server/docs/MCP-SERVER-HANDOVER.md`（§3.10，仅文档）

| 行 | 改动 |
|---|---|
| L422–429 | **新增** `_meta.generated_from` 说明：记录的是**生成当时**的来源（hof-rs 夹具），自 TASK-153 起生成器已改读引擎内基准；**该字段为历史溯源，不代表当前输入**；引入提交 `54200f0d77`（2026-09-26）；**不得**重生成该工件，并给出 blob/字节/sha 三法证据 |
| L430–437 | **新增**两个历史取证脚本已去跨仓的说明 + 逐字节等价性证据 + 端口拒绝守卫 |

`docs/tools_list.renamed.json` **未被修改**（三条独立证据见 §6.2）。

### 2.4 等价性证明（比任务书要求更强：整文件逐字节）

任务书只要求"用引擎内基准等价替换"。实际做到的是**整文件逐字节相同**：

```
$ git cat-file -s 543b49b2583bf06c3aba2a320649a31eda272e3e      # hof-rs db2eed7^ 的夹具 blob
48749

baseline bytes=48749 tools=174
db2eed7^ bytes=48749 tools=174
--- get_test_report baseline present=True db2eed7^ present=True
    description bytes equal = True ; chars equal = True
    inputSchema equal = True
    clear.description equal = True
--- get_game_node_properties baseline present=True db2eed7^ present=True
    description bytes equal = True ; chars equal = True
    inputSchema equal = True
    node_path.description equal = True
=== full raw byte comparison of the two JSON documents ===
whole-file byte identical = True
```

（脚本 `recovery\work\task154\equivalence_check.ps1`；hof-rs 侧只做 `git cat-file` 只读，未写任何文件。）

因此 §2.1 的替换相对任务书意图是**严格更强**的等价：不只是"被比较的字段相同"，而是"整个输入文件相同"。

---

## 3. §2.2 我选了哪个、以及理由

**选择：(b) 显式拒绝守卫**，并且**两个脚本都做**（不只是 mcp032）。

守卫实现（两脚本同形）：

```powershell
$TestPorts = @(9888, 9889)
foreach ($requestedPort in @($EditorPort, $GamePort)) {
    if (@($TestPorts) -notcontains $requestedPort) { Write-Host ...; exit 4 }
}
$portLiteralPattern = [regex]::Escape('9877')
if ([regex]::IsMatch([string]$PSScriptRoot, $portLiteralPattern)) { Write-Host ...; exit 4 }
```

理由：

1. **题面要求的是"不得存在静默使用 9877 的路径"**。(a) 参数化仍保留 `-EditorPort 9877` 这条**能到达决策者编辑器**的拼写（只是要求显式传），(b) 则把该拼写**变成硬错误**。同样的守约强度下 (b) 面更小、更难被绕过。
2. **拒绝点更早、更可判定**：守卫在**任何进程启动、任何 HTTP 请求、任何 scratch 目录写入之前**执行（实测：mcp029 守卫 ≈ L129 / 首个进程启动或网络语句 L191；mcp032 ≈ L127 / L187）；触发时 `-OutRoot` **不会被创建**，从而可以**不观测 9877 本身**就证明它没有被用。
3. **顺带更强**：`{9888, 9889}` 之外的任何端口都被拒绝，包括打错字的端口，避免误触无关监听者。
4. **mcp029 一并处理**：任务书 §1 清单只列了 mcp032 的 9877，但 mcp029 **同样硬编码** `$UserPort = 9877`（旧 L49、旧 L231、旧 L370）。硬约束"**绝不占用/探测 9877**"的优先级高于任务书的窄清单，故一并修掉（这条清单错误已由调度者确认为其疏漏，见 §8）。

**未选用 (a) 的具体代价**（记录以便复核）：参数化必须同时保留 `$UserPort` 的 `pid_before/pid_after` 断言才有意义，那就仍然要**枚举**（`netstat -ano -p TCP`）决策者端口——即仍要去"探测"它，与硬约束冲突。

---

## 4. 十道门真实结果 + `g09` 三道护栏核验

### 4.1 改动后（`task154_final`，HEAD `fc63af77c`）：10/10 `exit=0`

preflight（真实输出）：

```
GATES_PREFLIGHT VERSION_TEXT=4.8.dev.mono.custom_build.035edfce7
GATES_PREFLIGHT ANCHOR=035edfce7 HEAD=fc63af77c ANCHOR_REPORTED=035edfce7
GATES_PREFLIGHT WORKING_TREE_RED=0 WORKING_TREE_SAFE=0 COMMITTED_DIFF_SAFE=6
GATES_PREFLIGHT RED_COUNT=0 SAFE_COUNT=6
GATES_PREFLIGHT ANCHOR_SUMMARY ... verdict=ANCHOR_STRUCTURAL_EQUIVALENT ancestor=yes diff_count=6 safe_count=6 red_count=0
GATES_SKIPPED=0
```

| 门 | 命令 | exit | 真实计数 |
|---|---|---|---|
| g01 | `bin\godot.windows.editor.x86_64.mono.console.exe --headless --test --test-case=[MCPServer]*` | 0 | **160 / 160 passed, 0 failed**，assertions 6801/6801 |
| g02 | `... --headless --test` | 0 | **1586 / 1586 passed, 0 failed**，assertions 431114/431114 |
| g03 | `python modules\mcp_server\docs\scripts\check_tool_groups.py` | 0 | `TOOL-GROUPS CHECK PASS`（41 工具、`41 == 42 - 1` PASS） |
| g04 | `powershell ... check_contract_subset.ps1` | 0 | **3/3 checks passed**；`editor_9888` tools=**154**、`game_9889` tools=**73**、契约=**177**、`guard_user_port_9877` PASS（`pid_before=-1 pid_after=-1`） |
| g05 | `python ...\docs\scripts\check_rename_map.py` | 0 | **30 `[PASS]` / 0 `[FAIL]`**；`RESULT: PASS (all checks green)` |
| g06 | `python modules\mcp_server\scripts\check_tautologies.py` | 0 | `TAUTOLOGY CHECK PASS`（9 ps1 + 5 py 声明拼写，1 pinned） |
| g07 | `python ...\check_exit_propagation.py --probes` | 0 | **PROBES: 10/10** |
| g08 | `python ...\check_hardcoded_counts.py` | 0 | **UNCLASSIFIED = 0**；DERIVED 41 / CHECKED 6 / PINNED 5 / LIVE 4 / FROZEN 74 / total 130 |
| g09 | `powershell ... check_engine_anchor.ps1 -VersionText 4.8.dev.mono.custom_build.035edfce7` | 0 | `ANCHOR_JUDGE VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT`、`DIFF_COUNT=6 SAFE_COUNT=6 RED_COUNT=0`、`RESULT PASS` |
| g10 | `powershell ... accept_m1.ps1` | 0 | **22/22 cases passed** |

改动前（`task154_before`，HEAD `28432f859f`）同样 **10/10 exit=0**，`g05` 亦为 30 PASS / 0 FAIL、`g08` UNCLASSIFIED=0（FROZEN 70 / total 126）。

**g08 的一处真实变化（不隐藏）**：`FROZEN` 70 → **74**、`total` 126 → **130**。原因是本批新增注释里出现 `TASK-152` / `TASK-153` 字面量（调查数字集合里含 `152`/`153`），这些出现被分类为 `FROZEN`。**`UNCLASSIFIED` 仍为 0**，门仍 PASS；这不是放宽或新增检查，门判据未变。

### 4.2 `g09` 三道人工护栏的核验证据（真实输出）

`g09` 的判据（`ANCHOR_EQUAL` 或 `ANCHOR_STRUCTURAL_EQUIVALENT` 且 `RED_COUNT=0`）**未改动**。三道人工护栏的核验：

**护栏 ① 区间 diff 全为 docs/scripts 且无编译输入** —— 即判据内的 `RED_COUNT=0`，实测 `DIFF_COUNT=6 SAFE_COUNT=6 RED_COUNT=0`，6 个文件全为 `SAFE`：

```
ANCHOR_JUDGE SAFE modules/mcp_server/docs/MCP-SERVER-HANDOVER.md
ANCHOR_JUDGE SAFE modules/mcp_server/docs/rename-baseline-tools-list.json
ANCHOR_JUDGE SAFE modules/mcp_server/docs/scripts/check_rename_map.py
ANCHOR_JUDGE SAFE modules/mcp_server/scripts/gen_renamed_contract.py
ANCHOR_JUDGE SAFE modules/mcp_server/scripts/mcp029_clear_default_evidence.ps1
ANCHOR_JUDGE SAFE modules/mcp_server/scripts/mcp032_d3_d4_d6_evidence.ps1
```

**护栏 ② 编译输入区间 diff 为空** —— 由 `RED_COUNT=0` 直接蕴含（同一分类器 `Get-McpAnchorFileKind` 判定；非空洞性反例见 §5.2）。

**护栏 ③ 三个判据文件零 diff** —— 实测（三法）：

```
git -C <engine> diff --name-only 035edfce7..fc63af77c -- modules/mcp_server/scripts/check_engine_anchor.ps1   => 0 line(s) []
git -C <engine> diff --name-only 035edfce7..fc63af77c -- modules/mcp_server/scripts/check_hardcoded_counts.py => 0 line(s) []
git -C <outer F:\moonbit-hof-rs> diff --name-only -- godot-mcp/tools/run_gates.ps1                             => 0 line(s) []
outer runner blob: worktree=b3c5ea655b949836f7dc640fc54c255bc526cb16 HEAD=b3c5ea655b949836f7dc640fc54c255bc526cb16 IDENTICAL=True
```

外加 engine 内两个文件的 blob 恒等：

```
check_engine_anchor.ps1    worktree=8f048b31ff049bc8ec394a86b0b0d37ac72823d4 HEAD=8f048b31ff049bc8ec394a86b0b0d37ac72823d4 IDENTICAL=True
check_hardcoded_counts.py  worktree=07283d48866a119d4bf9be13843a6c0ec7fd0456 HEAD=07283d48866a119d4bf9be13843a6c0ec7fd0456 IDENTICAL=True
```

**注（重要的路径事实）**：外层仓根是 `F:\moonbit-hof-rs`（不是 `F:\moonbit-hof-rs\godot-mcp`），门运行器的仓相对路径是 **`godot-mcp/tools/run_gates.ps1`**。把 `tools/run_gates.ps1` 交给 `git -C F:\moonbit-hof-rs` **不会报错、只会匹配 0 条**（`git diff` 对不存在的 pathspec 是静默的）——这会产生"看起来通过"的假证据。本报告的所有护栏③结论都用正确路径得出。

---

## 5. §2.4（可选）：**不做**，以及为什么——附全部实测证据

**结论：按任务书 §2.4 的"若做不到或会让判据变弱 ⇒ 不做"分支处理；保持人工护栏。** 理由分三条，每条都有实测支撑。

### 5.1 护栏 ① 与 ② 早已是现有判据本身（不是"人工"项）

`check_engine_anchor.ps1` 的 `ANCHOR_STRUCTURAL_EQUIVALENT` 定义就是：`A` 是 `H` 的祖先**且** `git diff --name-only A..H` 无编译输入；判据字符串与 `RED_COUNT` 一起每次打印。也就是说：

- "区间 diff 全为 docs/scripts 且无编译输入" = `verdict==ANCHOR_STRUCTURAL_EQUIVALENT && RED_COUNT==0`；
- "编译输入区间 diff 为空" = `RED_COUNT==0`。

把它们再"机器化"一遍是**重复劳动**，而且会让判据出现**第二份实现**（与"一个分类器，不是两份白名单"的设计相悖）。

### 5.2 非空洞性：该规则确实会变红（实测）

```
$ powershell ... recovery\work\task154\guardrails_probe2.ps1
  15bbf1f50e..HEAD: diff=10 red=4 judge.Verdict=ANCHOR_STALE_COMPILED judge.Ok=False
      red = modules/mcp_server/tests/test_mcp_server.h
            modules/mcp_server/tools/running_game_script_execution.cpp
            modules/mcp_server/tools/tool_helpers.cpp
            modules/mcp_server/tools/tool_helpers.h
  97fc49df4b..HEAD: diff=6 red=0 judge.Verdict=ANCHOR_STRUCTURAL_EQUIVALENT judge.Ok=True
  035edfce7f..HEAD: diff=6 red=0 judge.Verdict=ANCHOR_STRUCTURAL_EQUIVALENT judge.Ok=True
```

即：护栏 ①② 的规则**能被真实区间触发**（`ANCHOR_STALE_COMPILED`），不是恒真。

### 5.3 护栏 ③ 无法在不削弱判据的前提下机器化（决定性理由）

护栏 ③ 的内容是"`check_engine_anchor.ps1` / `check_hardcoded_counts.py` / `run_gates.ps1` 零 diff"。实测它的可机器化边界：

1. **它跨越两个仓**：`run_gates.ps1` 在外层仓，而锚点判据运行在引擎仓内。`git -C <engine>` 对引擎树之外**天然不可见**——把它写成一个"区间规则"，那一条永远恒真（空洞）。要覆盖它必须再引入一条外层仓的检查，而外层仓的检查脚本不在十门路径上、也不在被本任务允许改动的范围内。
2. **文件本身就是判据的一部分**：三个文件里两个在引擎仓，其中一个（`check_engine_anchor.ps1`）**就是判据实现**。在它里面加"这三个文件零 diff"是**自指**的：判据脚本一改，规则立刻变红，而修规则又要改判据文件——不能自洽。
3. **任何"非空洞"的区间规则都必然弱于"这三个文件被冻结"**：区间规则只能看到 `A..H`，而事实是"这三份文件在**任何**区间都未被改过"。把"全历史冻结"降级成"某个区间内未改"是**严格更弱**。

护栏 ③ 的**非空洞性**也用一次性探针仓库证明过（规则形状本身能红）：

```
$ powershell ... recovery\work\task154\guardrails_probe2.ps1
### 4. A guardrail-3 violation, injected and detected, then removed ###
  probe repo C:\Users\wyl\AppData\Local\Temp\task154-guardrail3-probe: base=4b2cf61ac head=f88b16f4f
  interval diff = [check_engine_anchor.ps1]
  guardrail 3 (criterion files zero diff) = False  hits=[check_engine_anchor.ps1]  << RED means the rule fired
  probe repo removed = True
```

（探针仓是一个只含单文件的**一次性临时仓**，注入"某提交动了 `check_engine_anchor.ps1`"，规则随即变红；用完即删。**两个真实仓库全程未被触碰**。）

### 5.4 我没有新增任何"需要手工运行"的脚本

曾写过一个 `modules/mcp_server/scripts/review_g09_guardrails.ps1`（只读、不在任何门上），随后**删除**：调度者确认"没有一个能自动跑它的位置，加它只会增加一个低信任度工件"。当前 `git status --porcelain` 证实它不存在。故本批在引擎仓内的产物**只有**两个脚本 + 一份文档。

---

## 6. 禁区自查真实输出

（完整输出：`recovery\work\task154\final_selfcheck.out.txt`，由 `final_selfcheck.ps1` 生成，退出码 0。）

### 6.1 `9877` / `moonbit-hof-rs` 字面量自查

```
--- modules/mcp_server/scripts/mcp029_clear_default_evidence.ps1
    totals: moonbit-hof-rs=2 (non-comment 0) ; 9877=5 (non-comment 2)
    bytes=26174  BOM=False  non-ASCII bytes=0
--- modules/mcp_server/scripts/mcp032_d3_d4_d6_evidence.ps1
    totals: moonbit-hof-rs=2 (non-comment 0) ; 9877=5 (non-comment 2)
    bytes=35879  BOM=False  non-ASCII bytes=0
```

逐行（两个脚本）：

| 文件 | 行 | 是注释 | 内容 |
|---|---|---|---|
| mcp029 | L69 / L83 | 是 | 说明"改前是 hof-rs 路径"的**历史注释**（任务书 §2.3 要求写明该历史；TASK-152 的"字符串常量命中 0"口径针对**可执行代码路径**，注释除外） |
| mcp029 | L115 / L288 / L436 | 是 | 端口守卫与两条旧检查的说明注释 |
| mcp029 | **L134** | **否** | `$portLiteralPattern = [regex]::Escape('9877')` —— **守卫本身的字面量**（它存在的目的是"出现这个值就拒绝"） |
| mcp029 | **L296** | **否** | `$userPortLiteralPattern = [regex]::Escape('9877')` —— 同上，供 `test_ports_only` 使用 |
| mcp032 | L70 / L85 / L108 / L353 / L580 | 是 | 同上（历史说明与守卫说明） |
| mcp032 | **L132** / **L359** | **否** | 同 mcp029 的两处守卫字面量 |

**非注释命中 = 2×2，全部是"拒绝该端口"的守卫字面量本身**；除此之外**没有任何执行路径读取、拼装、枚举或连接该端口**。

### 6.2 冻结工件三法证据（字节 / blob / sha256）

```
tools_list.renamed.json
    bytes=154272 sha256=fd00c75e5174ec923d5a91c0323afa0804f523b385eae3d4f78d8c71e1f895df
    worktree blob=3b1b191dc42f1cec8bc7cdd3504247c935b52f5e  HEAD blob=3b1b191dc42f1cec8bc7cdd3504247c935b52f5e  IDENTICAL=True
rename-baseline-tools-list.json
    bytes=48749 sha256=8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54
    worktree blob=543b49b2583bf06c3aba2a320649a31eda272e3e  HEAD blob=543b49b2583bf06c3aba2a320649a31eda272e3e  IDENTICAL=True
```

另：`git -C <engine> rev-parse 28432f859f:modules/mcp_server/docs/tools_list.renamed.json` = `3b1b191d…` = 当前 worktree blob ⇒ 与起始 HEAD 时**完全相同**。

`--import`\`--headless` 的运行把 `_meta.generated_from` 保持原样（`"F:\\moonbit-hof-rs\\tests\\fixtures\\mcp\\tools_list.json"`）——它是**历史字段**，本次只加旁注文档，未触碰工件。

### 6.3 hof-rs 侧

```
hof-rs HEAD = a5038e0
hof-rs git status --porcelain lines = 1
   ?? godot-mcp/recovery/work/task154/          ← 本任务**被授权**的证据目录（任务书 §0 范围）
the forbidden fixture path: exists=True bytes=71481 sha256=50c5fb4204ee5b957b017eb994e7f7bd73f9b299e6aa9471d5cf11683e067da0
```

- `tests/fixtures/mcp/tools_list.json` **存在且未被删改**（71481 B、`50c5fb42…`，即 hof-rs `db2eed7` 之后的状态）；
- 除被授权的 `recovery/work/task154/` 外，hof-rs **没有任何改动**；
- hof-rs 侧**只读**操作：`git cat-file`（读对象库）、`git status`、`git log`、`Get-FileHash`。

### 6.4 端口与进程收尾

```
=== 6. ports 9870..9889 listener state at the end ===
LISTENING rows in 9870..9889 = 0
```

每次实跑之后复核 9888/9889 均已释放（`listeners on 9888/9889 right after: 0 (0 = released)`），`parse` 与 `-f` 检查确认无遗留引擎进程占用测试端口。**9877 全程既未被绑定，也未被主动连接**：唯一涉及其数值的地方是拒绝守卫的字符串，以及 `Get-ListenerPid`（`netstat -ano -p TCP` 本地套接字表**枚举**）——后者在 mcp029/mcp032 中已随 `$UserPort` 一并删除，故两个脚本现在连"枚举"都不做。

**未 push**：`origin/feature/mcp-server-module-rebuild` 仍指向 `28432f859f`，HEAD 领先 4、落后 0；外层仓无任何提交。

---

## 7. 遗留风险与未验证项（区分实测 / 推断）

### 7.1 【实测】`mcp032` 存在多处**改动之前就有**的 `-f` 格式化缺陷，脚本在旧 HEAD 上同样跑不起来

`mcp032` 原样运行在第 287–288 行崩溃：

```
Error formatting a string: Input string was not in a correct format..
At ...\mcp032_d3_d4_d6_evidence.ps1:348 char:1
+ Check 'd3_parser_positive_control' $controlThrew `
```

原因：证据串里的 `{'Material','material'}` 被 `-f` 当成格式项。**这是既有缺陷，不是 TASK-154 引入**，三条独立证据：

1. `git diff -U0 28432f859f..HEAD -- mcp032_d3_d4_d6_evidence.ps1` 的 hunk 头只有 `@@ -41 / -44 / -63 / -69 / -74 / -191 / -194 / -292 / -300 / -515 @@`，**没有任何 hunk 覆盖 287–290 行**；
2. 该行**逐字符来自 HEAD~3**（`git show 28432f859f:...` 取的原文与现状一致）；
3. 把原表达式单独求值即复现同样异常；把 `{` 双写后正常：

```
THREW: Error formatting a string: Input string was not in a correct format..
OK with doubled braces = hand-built {'Material','material'} JSON: ConvertFrom-Json threw = True; message='x'
```

同一类缺陷在 D4/D6 段还有 5 处：`{prefix:'application/config/name'}`、`{filter:...}`、`{prefix, filter}`、`{bogus:1}`、`{include_default:true}`。

**我没有修它们**（不在任务书授权范围，且会改动既有证据文本）。为了仍能实测本任务改动的代码路径，我在**同一目录下放了一份临时副本**（只把这 6 处 `{` 双写、与仓库文件 diff 恰好 6 行），跑完即删：

```
diff --no-index --stat (probe vs committed):
    ...\\modules\\mcp_server\\scripts\\task154_probe_mcp032.ps1" | 12 ++++++------
    1 file changed, 6 insertions(+), 6 deletions(-)
probe file removed = True
engine repo git status --porcelain lines after cleanup = 0 (0 = clean)
```

**建议（交由调度者/后续任务裁决）**：把这 6 处 `{` 双写后再跑一次 `mcp032`；它当前**根本无法产出任何证据**，与它是否去跨仓无关。

### 7.2 【实测】`mcp029` 实跑 20 检查 / **2 失败**；`mcp032`（打补丁的临时副本）39 检查 / **2 失败**——均为**内容级既有红**，与本次去跨仓无关

`mcp029`（改后实跑）：

```
TASK-029 evidence: 20 checks, 2 failed
[FAIL] wire_clear_default_is_false
       live inputSchema.properties.clear.default = true (type Boolean)
[FAIL] wire_description_names_shared_file
       live description = 获取测试结果报告
```

`mcp032`（临时副本实跑）：

```
TASK-032 evidence: 39 checks, 2 failed
[FAIL] d6_live_description_keeps_the_old_wording   live description starts with the pre-override wording + space: False
[FAIL] d6_live_description_declares_the_shape      live description = '获取运行中游戏指定节点的属性'
```

**判据说明**：这 4 条红说的是"线上 `tools/list` **没有携带** TASK-029 / TASK-032 的 `SCHEMA_OVERRIDES` / `DESCRIPTION_OVERRIDES` 文本"，而不是"脚本读错了基准"。三条支撑：

1. `d6_old_wording_readable` 与 mcp029 的 `old_fixture_readable` **改后转 PASS**，且旧文案与基准逐字一致（`'获取运行中游戏指定节点的属性'`）⇒ §2.1 的换源**达到预期效果**；
2. `d6_contract_agrees_with_the_wire` **PASS**（契约 == 线上）⇒ 红的原因在于**契约工件本身**没有这些 override 文本；
3. 冻结契约 `tools_list.renamed.json` 的 blob 在 `HEAD~6`、`HEAD~3`、`HEAD` **都是 `3b1b191d…`**，且 `git log -S` 显示它**从未**包含过 `/root/Main/Actor`、`user://mcp_test_report.json`、`clear:true` 这些 override 文本 ⇒ 这 4 条红**远早于本批存在**。

**判据不变性（推断，但有强证据）**：由于（i）输入数据逐字节相同、（ii）契约 blob 未变、（iii）我没改这 4 条检查的表达式，这 4 条的**判据与结论**在改前改后一致；唯一变化是 mcp029 的 `wire_clear_description_kept` 由"与空串比较而 FAIL"变为"与真实旧文案比较而 PASS"，以及 `d6_old_wording_readable` / `old_fixture_readable` 由恒 FAIL 变为 PASS。

**必须说明的一点**：改前状态下这两个脚本**无法用测试端口安全地证明"红集合完全一致"**——旧 mcp029 会 `Get-ListenerPid -Port_ 9877`（枚举决策者端口），旧 mcp032 会带着 9877 记账；按硬约束我没有运行旧版本，因此"旧版也是这些红"属于**基于上述 (i)(ii)(iii) 的推断**，不是实测。

### 7.3 【实测】g08 的 FROZEN 桶 +4

见 §4.1 末：`FROZEN 70 → 74`、`total 126 → 130`，`UNCLASSIFIED` 仍为 0。原因是新增注释里的 `TASK-152` / `TASK-153` 字面量落入调查数字集合。门判据未变。

### 7.4 【实测】两个实跑脚本对机器的**非仓内**副作用

- 会向 `%APPDATA%\Godot\app_userdata\mcp029_clear_default\logs\` 与 `...\mcp032_d3_d4_d6\logs\` **追加** Godot 日志（这两个目录在本次之前就存在，含 2026-09-23 / 09-25 的旧日志；本次新增 `godot2026-09-29T10.31.21.log`、`godot2026-09-29T10.36.06.log`）。这是这两个脚本一贯行为，未修改；
- 在 `%TEMP%` 下留下 `task154-live-029`、`task154-live-032`、`task154-probe-032` 三个 OutRoot（证据用，未删除）；
- `mcp029` 按其自身设计删除了 scratch 项目的 `mcp_test_report.json`（位于该项目自己的 app_userdata 目录）。**未触碰决策者真实工程**。

### 7.5 【实测】本报告未做的事

- 未 `push`（任何仓）；
- 未改 hof-rs 任何被跟踪文件；
- 未重生成 `docs/tools_list.renamed.json`；
- 未新增依赖；
- 未删除或放宽任何既有检查（改动只是**替换**端口判据与**换源**；`netstat` 枚举在 mcp029/mcp032 中减少，判据强度见 §3）；
- 未修改 `mcp_port_guard.ps1`（其他 30+ 脚本仍在使用它）。

### 7.6 【推断】任务书 §2.1 提到的"两个脚本不在十门路径上"

我确认了 `run_gates.ps1` 的十条命令列表（`$commands`）里**没有**这两个脚本，`accept_m1.ps1` 的命令行里也没有它们；因此本批改动**不经过任何门**，这也是十门结果与改动前逐项相同的原因。这一点是**实测**（读 `run_gates.ps1:214-225` 与门输出），但"任务书说 grep 无命中"我未逐字复现，仅在此声明我的核实方式。

---

## 8. 诚实披露

1. **我从没链接、绑定或主动探测 9877**。唯一与其数值有关的是"发现该值就拒绝"的守卫字符串。旧版脚本里两次 `Get-ListenerPid -Port_ $UserPort`（`netstat` 本地表枚举）随 `$UserPort` 一并删除；**旧版本我一次都没有运行**——按硬约束这是正确的，但也意味着 §7.2 的"红集合一致"是**推断**而非实测。
2. **`cmd /c git cat-file blob db2eed7^:tests/fixtures/mcp/tools_list.json` 是一个会毒化复核的陷阱**：`^` 被 cmd 当转义符吃掉，命令**静默**返回 HEAD 的内容（71481 B / 177 条、sha `50c5fb42…`），而不是父提交的 48749 B / 174 条 / `8f8051c4…`。我自己第一次就踩了这个坑，差点得出"hof-rs 的旧夹具已经不存在"的**错误结论**。正确读法有两种，我都实测过：
   - `git cat-file blob 543b49b2583bf06c3aba2a320649a31eda272e3e > out`（直接用已知 blob id），或
   - 用 `System.Diagnostics.Process` + `psi.RedirectStandardOutput = $true` + `StandardOutput.BaseStream.CopyTo($fs)` 把 `db2eed7^:...` 的**原始字节**取出（**不要**经过 PowerShell 文本管线，也不要经 `cmd` 重定向）。
   两次读取的原始对照：

   | 读法 | 字节 | 条数 | sha256 |
   |---|---|---|---|
   | `cmd /c git cat-file blob db2eed7^:...` | **71481** | **177** | `50c5fb42…`（= HEAD 内容，**错误**） |
   | `git cat-file blob 543b49b2…` / Process+BaseStream 读 `db2eed7^:` | **48749** | **174** | `8f8051c4…`（**正确**） |

   并对 `git rev-parse db2eed7^` → `b6d9282f5a…`、`git rev-parse db2eed7^:tests/fixtures/mcp/tools_list.json` → `543b49b2…` 做了交叉确认。
3. **我做了全文件逐字节比较，而不只是逐字段**（任务书只要求等价替换）。结论：引擎内基准与 hof-rs 历史夹具**整文件逐字节相同**，因此替换是**可证语义中性**的（§2.4）。这比任务书要求的更强。
4. **任务书 §1 的清单漏了 `mcp029` 的 9877**（只列了 mcp032）。我以"绝不占用/探测 9877 是硬约束、优先级高于窄清单"把两处一并修掉。调度者已确认这是**它的清单错误**，我的处理**不是越权**。
5. **我改了任务书未列出的第三类东西：一行注释里的拼写**（`a requests port` → `a requested port`），并因此多了一个**第 4 个提交** `fc63af77c3`。为保持"报告中的门结果对应最终提交状态"，我在该提交之后**重跑了十道门**（`task154_final`，10/10 exit=0）。任务书只说"逐条提交"，这一条是**注释级**的，我照实披露。
6. **§2.4 我明确不做**，并把全部支撑证据（含反例与探针仓）留在 §5。我**没有**为此新增任何需要手工运行的脚本（`review_g09_guardrails.ps1` 曾写、随后删除，`git status` 可证不存在）。
7. **发现但未修**：`mcp032` 的 6 处既有 `-f` 格式化缺陷使它**在当前 HEAD 上完全无法运行**（§7.1）。修它会超出任务书授权并改动既有证据文本，故只报告 + 给出建议。**它的实测覆盖因此只到"打补丁的临时副本"这一层**，临时副本与仓库文件 diff 已给出（6 处 `{` 双写），用完即删、树已复核干净。
8. **`mcp029` / `mcp032` 实跑各有 2 条红**（§7.2）。它们在**本批之前就存在**、成因是契约工件没有携带对应的 override 文本（冻结契约 blob 与 `git log -S` 佐证），**不是**换源失败；换源的正向效果（`old_fixture_readable`、`d6_old_wording_readable` 转 PASS）是可实测的。
9. **日期**：本批**没有编造任何日期**。提交时间戳 2026-09-29 来自本机时钟（实测 `Get-Date` = `2026-09-29 10:19:14 +08:00`，`Get-TimeZone` = `China Standard Time`），由 git 自动生成。文档中出现的唯一历史日期 `2026-09-26`、提交 `54200f0d77` 均**逐字来自任务书 §1**，我未自行推定或复算。
10. **证据可复现**：所有脚本与原始输出在 `F:\moonbit-hof-rs\godot-mcp\recovery\work\task154\`：
   `cmp_descriptions.ps1`、`dump_entries.ps1`、`extract_oldfixture.ps1`、`equivalence_check.ps1`、`verify_frozen.ps1`、`encoding_check.ps1`、`guardrails_check.ps1`、`guardrails_probe2.ps1`、`final_selfcheck.ps1`（+ `.out.txt`）、`live_runs.ps1`（+ `.txt`）、`probe_mcp032.ps1`（+ `.txt`）、`commit.sh`。
11. **门结果的落点**：`runs\gates\task154_before\summary.txt`、`runs\gates\task154_final\summary.txt`。
12. **未验证项（明确列出）**：① 旧版两个脚本的"红集合"未实跑（§7.2，硬约束所致）；② §7.2 那 4 条红的**修复**不在本任务范围，故当前契约/线上描述与 override 的不一致**仍然存在**；③ `mcp032` 未经打补丁的原件**无法端到端运行**（§7.1）；④ 任务书 §1 "十门实际执行文件的可执行跨仓引用扫描 = 0"这条我**没有独立复现**（我只核实了这两条命令不在门命令列表里）。
