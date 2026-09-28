# TASK-149 报告 — 仓库清理（含已中止支线入库）+ 规范类文档校对

> 任务书：`recovery/tasks/TASK-149.md`（只读该文件执行）。
> **一行状态**：**A/B/C/D/E 全部完成；Q1–Q10 逐条自证；3 个提交（外层仓 2 个 + 引擎仓 1 个）+ 1 个报告提交；改完复跑 `pytest tools\tests` = 30 passed、矩阵 `SELF_CONSISTENT=YES`、preflight `WORKING_TREE_RED=0`；未达标项 3 条（全部如实登记，均不阻塞）。**
> **严格单线程**：本任务**没有**派任何子代理、没有 workflow、没有 ralph。
> **禁止 shell 重定向**：本报告引用的每一条证据都由 Python 文件句柄 / 工具的
> `-OutFile`/`--json`/`--md` 产生；**本轮我自己没有用过 `>`/`>>`/`2>&1`/`2>nul`/`1>NUL`**。
> 台账机制说明：`run_gates.ps1` **脚本内部**沿用既有 `Start-Process` + 子进程管道（这是它本来的
> 设计，见 §7.1），不是我引入的重定向。

---

## 0. 结论速览（对应任务书 §3 的 Q1–Q10）

| 编号 | 判据 | 结论 | 证据落点 |
|---|---|---|---|
| **Q1** | §A 审计轨迹已入库，提交信息写明对应交付提交 | **达标** | 提交 `70a7aa9`（307 文件 / +101249）；提交信息逐条列出 `8c562d4`/`e9d17f9`/`03839a5`/`91783eb` |
| **Q2** | TASK-142 残留作为**一个独立提交**，注明"已中止支线/仅作参考/不属于主线交付/被测状态" | **达标** | 提交 `71f92e8`（7 文件 / +5692 −85）；四项声明逐字在提交信息里 |
| **Q3** | 无任何丢弃/revert；`git log` 可追；被跟踪文件内容与提交前一致 | **达标** | 全程**未用** `git checkout --`/`restore`/`revert`/`rm`；`git reflog` 可追；§7.2 逐文件比对 |
| **Q4** | 引擎仓 `.gitignore` 加 `uid_cache.bin` 并提交；preflight 复跑给结果 | **达标** | 引擎仓提交 `15bbf1f50e`；preflight **`WORKING_TREE_RED=0`**、`ANCHOR_STRUCTURAL_EQUIVALENT`、`SKIP_REBUILD`（§3） |
| **Q5** | `DECISIONS.md` 加本批条目（主线校正/143/144/146/148 偏离），注明 TASK-142 条目来源 | **达标** | D212（主线校正 + **点名 D210/D211 来自已中止支线**）、D213、D214、D215；提交 `c53201e` |
| **Q6** | 校对范围内文档逐份过一遍，列出**逐文件**发现与修改（含"无问题"的文件） | **达标** | §5 的 15 份逐文件表 |
| **Q7** | `recovery/reports/ERRATA.md` 已建，至少收录 §E.12 点名的 5 类，逐条「文件/原说法/更正/依据」 | **达标** | `ERRATA.md`（348 行）；**E-1…E-5 正是点名的 5 类**，另加 E-6…E-12 |
| **Q8** | 改完复跑：`pytest tools\tests` 数字 + `TEST-CASES.md` 自洽校验 | **达标** | **`30 passed in 1.97s`**；`recount.py` → **`SELF_CONSISTENT=YES`**（177/10/22/159/407/13 = 788）；自洽脚本 **6/6** |
| **Q9** | 铁律逐条 + 文件所有权自查 + 两仓 `git log`/`git status` + 关键产物路径与 sha256 | **达标** | §7、§8、§9 |
| **Q10** | 未达标项如实报 | **达标** | §10 的 U1–U3（3 条） |

**一句话**：本批把一个被中断的支线**保留**进了历史（`71f92e8`，带完整的来源与状态声明），
把散落的审计轨迹一次性收进仓（`70a7aa9`），修掉了引擎仓那个让 preflight 一直报红的
未跟踪文件（`15bbf1f50e`），补了 4 条决策日志（`c53201e`），并把规范类+最新报告校了一遍
——其中**只有 3 处真正失效的数字/说明**被就地改掉，其余老报告的不自洽集中进新建的
`ERRATA.md`。

---

## 1. 依据与范围（任务书 §0 的实测校正）

任务书 §0 列的「当前残留（实测）」有 **2 处与实测不符**，如实登记（**代码/仓库优先于任务书**，
这正是 `tasks/README.md` 第 7 条鼓励的行为）：

| 任务书说 | 实测 | 我的处置 |
|---|---|---|
| 「**批次产出未入库**：`recovery/work/task144/`、`recovery/work/task148/`」 | **`task144/` 已入库**（`git ls-files recovery/work/task144/` = 11 个文件；它在 TASK-144 的 `e9d17f9` 里就提交了）。**只有 `task148/` 未入库** | 两个都写进 §A 清单（`git add` 对已跟踪文件是幂等的），并在提交信息里说明 `task144` 是补记 |
| 「已修改：`DECISIONS.md`、`TASK-140-REPORT.md`、`TEMPLATE-logic-feedback.md`、`tools/playability_controls.json`、`tools/playtest_player.py`、`tools/tests/test_playability_model_player.py`」 | 一致（6 个） | §B 全收，另加 `tools/playtest_player_t142_prefix.py`（任务书 §0 也列了它） |
| 「未跟踪：`recovery/reports/{ACCEPTANCE-TASK-137,141,145,147,TASK-142-REPORT}.md`」 | 一致，**另有 `recovery/reports/TASK-148-REPORT.md` 也未跟踪** | 一并收进 §A（它属于本批审计轨迹） |
| 「任务书点名校对 `TASK-147-REPORT.md`」 | **该文件不存在** | 登记为 `ERRATA.md` **E-11**；改为校对 `ACCEPTANCE-TASK-147.md` |

**交付提交对照**（提交信息里也写了）：

| 提交 | 内容 |
|---|---|
| `8c562d4` | TASK-143：781 用例 6 族矩阵 + contract-form / coverage-batch 测试 |
| `e9d17f9` | TASK-144：批量门改判声明通道（118/48→163/3）、两变体重建 `ba1587c71`、`accept_m1` 22/22 |
| `03839a5` | TASK-146：`TEST-CASES.md` 统计 == 正文（407/788）+ 自洽守护测试 |
| `91783eb` | TASK-148：从当前源码重发 20 款 Windows exe 包 |

---

## 2. §A — 审计轨迹入库（提交 `70a7aa9`）

**方式**：**逐文件暂存**。清单落在 `recovery/work/task149_stage_a.txt`（带注释说明为什么
每条在清单里、以及哪些**故意不在**），由一个只做 `git add -- <path>` 的脚本
（`recovery/work/task149_stage.py`）逐条执行，随后**打印 `git diff --cached --name-status`
与 `git status --short`** 供所有权自查。**没有用 `git add -A`/`git add .`**。

**提交 `70a7aa9`**：`307 files changed, 101249 insertions(+)`。清单与归属：

| 组 | 路径 | 归属 |
|---|---|---|
| A1 独立验收报告 | `recovery/reports/ACCEPTANCE-TASK-{137,141,145,147}.md` | 137 → 验收 TASK-136 那批；141 → 验收 TASK-140 那批；145 → 验收 143+144；147 → 复验 146 |
| A2 支线报告 + 最新报告 | `recovery/reports/TASK-142-REPORT.md`、`TASK-148-REPORT.md` | 142 的报告（保留）；148 的报告（对应 `91783eb`） |
| A3 任务书 | `recovery/tasks/TASK-{137-ACCEPT,141-ACCEPT,142,143,144,145-ACCEPT,146,147-ACCEPT,148,149}.md` | 决策 → 执行 → 判定三件套（`tasks/README.md` 第 4/5 条要求入库） |
| A4 work 目录 | `recovery/work/accept-145/`、`accept-147/`、`task144/`、`task148/` | 各自的探针/脚本/中间产物；`task144/` 是**补记**（本已入库）、`task148/` 是**首次入库** |

**注意（情境说明）**：`recovery/work/task148/unzip-test/...` 里有 `pong.exe` / `pong.pck` 等
**包的解出副本**（`unzip-test` 是 TASK-148 的端到端验证产物）。任务书的"`dist/**` 大包不动"
约束的是 `dist/**`；`recovery/work/task148/` 是任务书 §A.1 **明确要求提交**的 work 目录，
故按任务书入库。**没有触碰 `dist/**`**（`git status` 里 `dist/**` 全程零改动）。

---

## 3. §B — 已中止支线（TASK-142）独立提交（`71f92e8`）

**提交 `71f92e8`**：`7 files changed, 5692 insertions(+), 85 deletions(-)`。

| 文件 | 属于 |
|---|---|
| `DECISIONS.md` | D210（`min_rounds` 2→4、N≥4 分布、`ROUNDS_INSUFFICIENT`）+ D211（`_pong` 策略退化与修法）。**整份一处提交，未拆两半**（任务书 §B.3 的要求） |
| `recovery/reports/TASK-140-REPORT.md` | 该支线追加的「只增不改」勘误小节 §K |
| `recovery/tasks/TEMPLATE-logic-feedback.md` | 该支线的 §1.2e 与反例 33–36 |
| `tools/playability_controls.json` | `model_player_stability`：`min_rounds` 4、`ROUNDS_INSUFFICIENT`、分布要求、`why_4_not_2` |
| `tools/playtest_player.py` | `load_stability_declaration()`、`STABILITY_STATE_INSUFFICIENT*`、声明驱动的 `STABILITY_MIN_ROUNDS` |
| `tools/tests/test_playability_model_player.py` | 配套断言（+264 −26） |
| `tools/playtest_player_t142_prefix.py` | **修前冻结副本**（4906 行 / 277930 B；与 `71f92e8^:godot-mcp/tools/playtest_player.py` **逐字节相同**，`diff --strip-trailing-cr` 输出 0 行） |

**提交信息逐字包含**（任务书 §B.3 的四项要求）：`ABORTED BRANCH`、`REFERENCE ONLY`、
`NOT PART OF THIS LINE'S DELIVERY`、以及**被测状态**——TASK-143 记录的
`task142_cases` **52 断言 PASSED、未让任何测试变红**。

**与主线冲突的登记（任务书 §B.4「只报告不处置」）**：
`tools/playability_controls.json`、`tools/playtest_player.py`、
`tools/tests/test_playability_model_player.py` 是**产品/测试代码**，它们**真的改变了
可玩性测量的行为**（例如声明的最低轮数 2→4）。任务书 §2.3 说 `tools/**` 只读，
§B.3 又说把这三个文件作为该独立提交的成员——**两者冲突**。我按 §B.3 执行（用户的
"保留、不丢弃"是明确裁定），并**在提交信息里显式登记这一冲突**：
它们对 MCP 工具线**是惰性的**（TASK-149 全程 `pytest tools\tests` = 30 passed，
改动前后都在 README 与 §B 的测点跑过），**没有 revert、没有扩展**。

**没有撤销任何东西**：全程未执行 `git checkout --` / `git restore` / `git revert` / `git rm` /
`Remove-Item` / `del`。`tools/playtest_player_t142_prefix.py` 是**新增**，不是覆盖。

---

## 4. §C — 引擎仓 `uid_cache.bin`（提交 `15bbf1f50e`）

**改动**：`godot-mcp/godot/.gitignore` 在「Generated by Godot binary」段追加
（**3 行**：1 行注释 + 2 行注释 + 1 行规则，见 diff）：

```diff
 logs/
+# TASK-149: the project-scoped UID cache Godot writes next to project.godot.
+# It is machine-local state (it caches res:// UID lookups), not a source file.
+uid_cache.bin
 
 # Generated by unit tests
```

**非破坏性证据**：文件**仍在磁盘上**（70 B，mtime 仍为 `Sep 28 13:42`，未被触碰）；
`git check-ignore -v uid_cache.bin` → `.gitignore:50:uid_cache.bin`（之前 exit 1、现在 exit 0）。
引擎仓提交 `15bbf1f50e`（分支 `feature/mcp-server-module-rebuild`，**未 force、未切分支、
未 push**）。这是 TASK-149 对引擎仓的**唯一**改动。

**为什么必须这样修**：锚点判据 `check_engine_anchor.ps1` 对未识别 basename/扩展名是
**fail-closed**（`UNCLASSIFIED` 也算 RED），而 `.bin` 不可能进扩展名白名单，所以
"忽略"是唯一声明式解法（不能删文件——任务书禁止破坏性操作）。

### preflight 复跑（**修前 / 修后**，原始输出要点）

**修前**（`powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_gates.ps1 -PreflightOnly -Tag task149_preflight_before`，exit 0）：

```
GATES_PREFLIGHT ANCHOR=ba1587c71 HEAD=ba1587c71 ANCHOR_REPORTED=ba1587c71
GATES_PREFLIGHT WORKING_TREE_RED=1 WORKING_TREE_SAFE=0 COMMITTED_DIFF_SAFE=0
GATES_PREFLIGHT VERDICT=RUN_GATES
GATES_PREFLIGHT REASON="the engine working tree carries 1 compile input(s) that are not in any built binary"
GATES_PREFLIGHT RED_COUNT=1
GATES_PREFLIGHT RESULT=PREFLIGHT_ONLY
```

⇒ **确认 `WORKING_TREE_RED` 正是由 `uid_cache.bin` 引起的**（那 1 条 RED 就是它）。

**修后**（`... -Tag task149_preflight_after`，exit 0）：

```
GATES_PREFLIGHT ANCHOR=ba1587c71 HEAD=15bbf1f50 ANCHOR_REPORTED=ba1587c71
GATES_PREFLIGHT WORKING_TREE_RED=0 WORKING_TREE_SAFE=0 COMMITTED_DIFF_SAFE=1
GATES_PREFLIGHT VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT
GATES_PREFLIGHT REASON="ba1587c71 is an ancestor of 15bbf1f50 and all 1 file(s) in the diff are non-compiling; the binary is NOT equal to HEAD, it is structurally equivalent to it"
GATES_PREFLIGHT NONCOMPILING_COUNT=1
GATES_PREFLIGHT NONCOMPILING .gitignore
GATES_PREFLIGHT RESULT=SKIP_REBUILD
GATES_SKIPPED=1
```

**逐条说明剩余项**（任务书 §C.6 要求）：**没有剩余 RED**。`WORKING_TREE_RED=0`；
`COMMITTED_DIFF_SAFE=1` 是**锚点与 HEAD 之间的那 1 个文件**（`.gitignore`），它被判为
`SAFE`（非编译白名单成员）⇒ 判据从 `ANCHOR_EQUAL` 变成 `ANCHOR_STRUCTURAL_EQUIVALENT`，
这是**预期且正确**的结果（`.gitignore` 不改变任何已编译行为）。
`GATES_SKIPPED=1` 表示**十道门没有重跑**（preflight 的 SKIP_REBUILD 分支），
**这与任务书 §C.6 的要求一致**（"确认 `WORKING_TREE_RED` 不再由该文件引起"）。

**工具环境说明**：本机**没有 `pwsh`**（`where pwsh` 找不到），只有
`C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`；因此用 `powershell -NoProfile
-ExecutionPolicy Bypass -File ...` 调用，**语义与既有台账一致**（TASK-144 的
`TEST-CASES.md` §8.2 里 g09/g10 也是这么调的）。

---

## 5. §D — `DECISIONS.md` 追加（提交 `c53201e`）

编号顺延：既有到 **D211**，本批加 **D212–D215**（沿用文件既有格式：日期 / 触发问题 /
核查事实 / 选项（含否决理由）/ 最终选择 / 理由 / 预期影响与回滚点）。

| 编号 | 标题 | 要点 |
|---|---|---|
| **D212** | 主线校正（2026-09-28）：交付物是 **MCP 工具**，不是小游戏；中止 TASK-142 支线 | 用户三条裁定的原文；**明确点名 D210/D211 来自已中止支线**（任务书 §D.8）；给出 `71f92e8` 与"52 断言 PASSED / 未变红 / 30 passed 复跑"的被测状态 |
| **D213** | TASK-143：用例矩阵**口径**（781 条、6 族、编号稳定）+"派生"必须声明 | 六族数字、活体探针 142/`not_probed` 35、产品代码改动 0；写明 **781 是交付当时口径、788 是现行口径** |
| **D214** | TASK-144/146：**判据只收紧**（通道口径对齐 + 矩阵自洽守护 + 反例 175/177） | ①批量门 `163/3`、误红 45→0；②两变体重建至 `ba1587c71`、十门全绿、`accept_m1` 22/22、push `Everything up-to-date`；③自洽**先证红再恢复**；④口径收紧；⑤**TASK-149 的子计数更正 119+21+2** |
| **D215** | TASK-148：打包**偏离**（单卷 / MANIFEST 增列 / `UseSharedCompilation=false` 根因） | 旧"两卷"的理由（>2 GB）在实测下不成立（1.178 GB）；`SPLIT_INDEX = 10` 可复现旧口径；编译服务器挂住 → 三个环境变量 → 11.7 s 正常退出 |

**任务书 §D.8 的"注明来源"**：D212 的「最终选择」段落里**逐字**写：
> **重要：本文件里以下两条条目来自已中止支线，不是本主线的决策** —— **D210**、**D211** …
> 全部由 **`71f92e8`** 入库。**在主线里引用它们时必须同时写明"来自已中止支线 TASK-142"**。

另外在 §E 给 `TEMPLATE-logic-feedback.md` 的 §1.2e / 反例 33–36 加了一条**同样的来源横幅**
（它是那份规范类文档里唯一会被误读成活口径的地方）。

---

## 6. §E — 文档校对（逐文件）

**范围**（任务书 §E.9 为准）：规范类 `DECISIONS.md`、`recovery/tasks/README.md`、
`recovery/tasks/TEMPLATE-logic-feedback.md`、`recovery/TEST-CASES.md`、`TOOL-COVERAGE.md`
及同目录 `PLAYABILITY-*`、`GAME-LOOP-LOG.md`；最新报告
`TASK-{143,144,146,148}-REPORT.md` + `ACCEPTANCE-TASK-{137,141,145,147}.md`。
**老报告不改**，只进 `ERRATA.md`。

### 6.1 逐文件发现与修改

| # | 文件 | 发现 | 动作 |
|---|---|---|---|
| 1 | `DECISIONS.md` | 无失效引用（C2 扫描的命中项全部是有意为之的历史/外部坐标：`.hoh/**`、`.spec/**`、被重构掉的旧路径）；**TASK-142 条目（D210/D211）没有来源标注** | **改**：追加 D212–D215（§5）；D212 点名 D210/D211 的来源 |
| 2 | `recovery/tasks/README.md` | **无问题**。逐条核过：§6 的 TASK-127/128 并行事故记录、§8 的"严格单线程"（2026-09-27 最终指示、推翻同日 worktree 方案）、§40 行"引擎仓自带 `.git` 也是共享的"——都**与现状一致**（实测本机两个仓，见 `ERRATA.md` E-3）。无失效引用、无数字 | **不改**（列入 Q6 的"无问题"项） |
| 3 | `recovery/tasks/TEMPLATE-logic-feedback.md` | §1.2e 与反例 33–36 是 TASK-142 的产物，**没有来源标注**（读者会当成主线硬要求） | **改**：加来源横幅（只增不改） |
| 4 | `recovery/TEST-CASES.md` | ①§1.2 与 §9.3 U2 的 **`121` 不可复现**（实测 `119+21+2`，ACCEPTANCE-147 的 Y1 已点名）；②§9.3 U2 末句「其余 **33** 个 `not_probed`」与同段自己的「35 个」矛盾；③§8.3 的「`WORKING_TREE_RED=1` 指的是 `uid_cache.bin`」已因 §C 失效；④多处 `tools/tool_builder.cpp` 这类**相对缩写**（引擎文件其实在 `godot/modules/mcp_server/tools/`） | **改**：①②③④ 就地更正（保留原读数、写明"TASK-149 更新"），并新增 **§10.7 TASK-149 更新**段。**增删编号行 0 条** ⇒ §1.1 的 177/10/22/159/407/13 = 788 **逐位未变** |
| 5 | `TOOL-COVERAGE.md` | **是 `tools/tool_coverage.py` 的生成物**（改了也会被下次生成覆盖）；逐项复核：177 工具、`>=5` 桶 172（= 177 − 0 次 5）、**`tools/*.cpp` 那 10 个引用全部存在**（真身 `godot/modules/mcp_server/tools/*.cpp`）、生成命令可跑 | **只加校对注**（说明为什么不动它的数字 + 复核结论） |
| 6 | `recovery/reports/PLAYABILITY-REPORT.md` | 游戏侧规范类文档；引用路径**本机全部存在**；每个数字的依据都在 `runs/playability/**`（**被 gitignore，只在本机**） | **只加来源/范围注**：主线已校正（D212），不做逐条数字校对，老报告勘误进 ERRATA |
| 7 | `recovery/reports/PLAYABILITY-DEFECTS.md` | 同上（D1/D11/D2/D3/D5 汇总"总计 84 条，已修 84"内部自洽） | **只加同款注** |
| 8 | `GAME-LOOP-LOG.md` | **路径不在 `recovery/reports/` 下，而在 `godot-mcp/`**（任务书 §E.9 的并列写法容易误读）；游戏侧台账，依据都在 `runs/**` | **改**：加来源/范围注 + **就地写明真实路径** |
| 9 | `recovery/reports/TASK-143-REPORT.md` | 它的 `781`/`400`/`23 passed` 是**交付当时的真实值**，已被 TASK-146 取代；`TEST-CASES.md` 顶部已注明"TASK-144/146 更新" | **不改**（它是历史实施报告；口径演进由 `TEST-CASES.md` 头部 + `DECISIONS.md` D213/D214 记录） |
| 10 | `recovery/reports/TASK-144-REPORT.md` | 同上（`404`/`785` 是它当时的真实值，TASK-146 已更正） | **不改**（同上） |
| 11 | `recovery/reports/TASK-146-REPORT.md` | 它自己就是更正报告，`788/407/30 passed` 与现状一致；无失效引用 | **不改**（无问题） |
| 12 | `recovery/reports/TASK-148-REPORT.md` | 逐条复核通过：`1264863973` B 单卷、`3780` 载荷 / `3239466195` B、`part1of1`、四列清单、`UseSharedCompilation=false` 根因、20/20 导出与冒烟、`dist/*.MANIFEST.txt`/`*.sha256.txt`/`PACKAGE-INFO-TASK148.txt` **都在盘上** | **不改**（无问题） |
| 13 | `recovery/reports/ACCEPTANCE-TASK-137.md` | 全篇 `tools/playtest_player.py:NNN` 指针属于**验收当时的冻结版**（TASK-142 之后位移**不是常数**：+58/+99/+119/+174）；其中 `:2326` 的 `pre_ack` 兜底**已被 TASK-138 移除**（行为变化，不只是行号）；另有两处指针指向的东西与描述不符（`:950-981`、`:2476-2478`） | **改**：文首追加**只增不改**的 TASK-149 段，含**逐指针实算表**（覆盖它引用过的**每一个**行号）；不改正文别的字 |
| 14 | `recovery/reports/ACCEPTANCE-TASK-141.md` | 同类行号漂移（`:2286-2308` `_pong` → `:2405` 等 8 处） | **改**：同款文首追加段 + 逐指针表 |
| 15 | `recovery/reports/ACCEPTANCE-TASK-145.md` | `27 passed` / `404` / `785` 是它当时的真实读数，已被 `03839a5` 取代；**它的 `verdict=fail` 正是 TASK-146 的起因，判断是对的** | **改**：加"过期说明"（不改任何数字、不改结论） |
| 16 | `recovery/reports/ACCEPTANCE-TASK-147.md` | 它点名的 **Y1**（`121`）当时**没有被落进** `TEST-CASES.md`；**X5/X6** 也还在 | **改**：加注说明 **Y1 已由 TASK-149 落实**、**X5/X6 经复核后保留**及理由 |

### 6.2 校对用的机械检查（全部只读，脚本在 `recovery/work/`）

| 检查 | 脚本 | 结果 |
|---|---|---|
| `-32602` 来源划分 | `task149_docaudit.py c1` | **119 / 21 / 2 = 142**（逐条打印 2 条无冒号的消息与工具名） |
| 失效路径引用（含目录的 token，多根解析） | `task149_docaudit.py c2` | 扫描后剩 27 条候选；**逐条判读后 0 条需要改**（详见 §6.3） |
| `tools/tests/**` 计数 | `task149_docaudit.py c3` | 9 个 .py，`def test_*` 共 **30**（唯一来源） |
| 矩阵 `path:line` 指针 | `task149_pointers.py` | 631 个不同指针，连到 627 个文件，**0 条行号超过文件末行**；4 条"missing"是裸 basename（`test_mcp_server.h:4342` 等），真身存在 |
| 冻结点位图 | `task149_frozenmap.py` | 冻结版 **4905 行**；符号两版行号对照，证实位移分段 |
| 报告内某指针"今天"落点 | `task149_stalepointers.py <报告>` | 打印行内容 + 前后 60 行内的 `def`/`class` |
| TASK-140 194 复算 | `task149_ledger.py` | 台账 710 行；首个 `t140-wrapper-call` idx 502、末次 `*_scan_redirects.py` idx 695 ⇒ `695−502+1 = **194**`（区间宽度稳定；扫描后 15 条） |

### 6.3 c2 扫描剩下的 27 条候选为什么"不用改"（逐类说明）

| 类 | 例 | 判读 |
|---|---|---|
| 其他系统/外部坐标 | `.hoh/evidence.json`、`.spec/godot-mcp-engine/tool-rename-map.json`、`install/emscripten/test/test_other.py`、`skills/godot-dev.md` | 不在本仓，是当时的**真坐标**（`.hoh` 在用户 home，`.spec` 已随重构移除），改了反而假 |
| 部署/构建落在别处 | `4.8.dev/windows_release_x86_64.exe`、`/windows_release_x86_64.exe`、`godot/bin/...mono.console.exe`（含 `...` 省略号） | 是命令行片段/带省略号的示意，不是路径声明 |
| 被重构掉的旧路径（历史叙述） | `docs/DESIGN-DETAIL.md`、`docs/TOOL-NAMING.md`、`scripts/accept_m1.ps1`、`tools/tool_builder.h` | 历史决策记录里的旧坐标；DECISIONS 的纪律是"只增不改"，且它们描述的是**当时**的树 |
| 明确不存在的文件（已登记） | `tools/tests/conftest.py`、`tools/tests/test_accept147_bypass_probe.py`（ACCEPTANCE-147 说"临时文件已删"）、`task146/recount.py`（相对 `recovery/work/` 解析得到，真身存在） | 已在原文里声明临时/已删，或可解析 |
| `runs/**`（gitignore） | `runs/accept-141/indep_cmp_pong.txt`、`t140-gate-4/playability.json` | 本机存在（`runs/**` 被忽略），不可能进 git，但**不是"失效引用"**——它们是本机可复算的产物指针 |

---

## 7. §F — 验证与自查

### 7.1 改完复跑（Q8，原始输出）

```
python -m pytest tools\tests -q --no-header -p no:cacheprovider
..............................                                           [100%]
30 passed in 1.97s
```

```
python recovery\work\task146\recount.py
family       declared     body status
TC-CONS-           13       13 OK
TC-ENG-           159      159 OK
TC-GATE-           10       10 OK
TC-M1-             22       22 OK
TC-PY-            407      407 OK
TC-TOOL-          177      177 OK
TOTAL             788      788 OK
per-family body counts: {'TC-TOOL-': 177, 'TC-GATE-': 10, 'TC-M1-': 22, 'TC-ENG-': 159, 'TC-PY-': 407, 'TC-CONS-': 13}
SELF_CONSISTENT=YES
```

```
python tools\tests\test_matrix_self_consistency.py
ok    section 1.1 statistics == the body's numbered rows
ok    section 1.1 is present and complete
ok    every TC-PY row names a test that exists
ok    the statistics checker goes red on a bad TOTAL
ok    the statistics checker goes red on a dropped row
ok    the reference checker goes red on a renamed row
6/6 checks passed
```

**基线对照**：改动**前**同样命令 = **30 passed in 1.97s**（同一结果）。
**`TEST-CASES.md` 的改动没有让任何守护测试变红**（这正是任务书 §E.11 的要求；
我只改文字与两个失效数字，**一条编号行都没增删**，所以 `check_statistics` 不受影响）。

**TASK-142 残余的测点**（§B 的"被测状态"宣称）：

```
（§B 入库前、树里已带该残余时）
python -m pytest tools\tests -q --no-header -p no:cacheprovider
..............................                                           [100%]
30 passed in 1.98s
```

⇒ 与 TASK-143 记录的"未让任何测试变红"**一致**。

### 7.2 Q3 — 无丢弃 / 可追（逐项）

| 检查 | 结果 |
|---|---|
| `git checkout --` / `restore` / `revert` / `reset --hard` | **一次都没有执行**（本报告全篇可查） |
| 删除文件（`rm`/`del`/`Remove-Item`） | **一次都没有执行** |
| `uid_cache.bin` 是否还在 | **在**（70 B，mtime 未变） |
| 旧包 `dist/**` | **未被删、未被改**（`git status --short` 里 `dist/**` 零改动；`dist/` 里的 4 个文件 mtime 未变） |
| `71f92e8` 的 7 个文件是否"与提交前一致" | `git show HEAD~2:godot-mcp/tools/playtest_player.py` 与 `tools/playtest_player_t142_prefix.py` **逐字节相同**（`diff --strip-trailing-cr` = 0 行）；`DECISIONS.md` 的 D210/D211 段落**原文保留**（`c53201e` 只在**其后**追加） |
| 可追性 | `git log --oneline`（外层 5 条 + 引擎 3 条）与 `git reflog` 都完整；本批 3 个提交的父链是 `91783eb → 70a7aa9 → 71f92e8 → c53201e` |

**被跟踪文件内容与提交前一致的核对**（除有意修改的文档）：`70a7aa9` 是**纯新增**
（表中路径在 `91783eb` 都不存在）；`71f92e8` 的 6 个 `M` 是**任务书 §0 点名要保留的既存改动**，
我**未在其上再改一个字节**（对 `tools/playability_controls.json`/`playtest_player.py` 的
`git diff` 与我接手时逐字节相同）；`c53201e` 的 12 个 `M` **全部是我的文档校对改动**（逐条见 §6.1）。

### 7.3 Q9 — 铁律逐条

| 铁律 | 本轮实际 |
|---|---|
| 禁止一切 shell 重定向 | **零违反**。所有产物由 `edit`/`write` 工具、Python `io.open`、`git -F <file>`、`-OutFile`/`--json`/`--md` 产生。`run_gates.ps1` 内部的 `Start-Process -RedirectStandardOutput` 是**该脚本既有设计**（任务书 §2.1"如可用台账机制则给自查数字"），不是我引入的 |
| 破坏性命令默认拒绝 | 未用任何破坏性命令；`uid_cache.bin` 只忽略不删 |
| 不改产品/测试代码（`tools/**` 只读）、不改游戏工程 | `tools/**` 里我**没有做过任何编辑**；`projects/**` 零改动。**唯一涉及 `tools/**` 的写操作是 §B 的 `git add`**（提交的是**既存**改动，非我所作；冲突已在 §3 与提交信息里登记） |
| 命令尽量从 cmd 启动 | preflight 用 `cmd` 终端 + `powershell -NoProfile ... -File`；其余为只读脚本 |
| 唯一高位端口 / 禁第三方端点 | **本轮没有启动任何监听进程**（preflight 不建端口；无网络出站） |
| 不改 `.gitignore`（除 §C 的引擎仓一行） | 外层仓 `.gitignore` **未动**；引擎仓 `.gitignore` **只加 §C 那 3 行** |
| 代码优先于文档 | 文档更正全部以代码与产物为准（最典型：`121` → 代码里的 `require_string`/`require_int` 与两处内联消息） |
| 未达标项如实报 | §10 的 U1–U3 |

### 7.4 文件所有权自查（任务书 §F.14）

**我独占并被修改/新建的路径**（全部在任务书 §0 的独占清单内）：

| 路径 | 动作 | 提交 |
|---|---|---|
| `DECISIONS.md` | 改（+D212–D215） | `71f92e8`（既存 D210/D211）+ `c53201e`（我追加的） |
| `recovery/tasks/**.md` | 入库（`TASK-13x/14x*.md`、`TASK-149.md`） | `70a7aa9` |
| `recovery/reports/*.md` | 入库 5 份 + 改 6 份 + **新建 `ERRATA.md`** | `70a7aa9` + `c53201e` |
| `recovery/work/**` | 入库 4 个目录 + **新建 `task149_*.py`/`task149_*.txt`** | `70a7aa9` + `c53201e` + 报告提交 |
| `recovery/TEST-CASES.md` | 改 | `c53201e` |
| `TOOL-COVERAGE.md` | 改（只加注） | `c53201e` |
| `PLAYABILITY-REPORT.md` / `PLAYABILITY-DEFECTS.md` | 改（只加注） | `c53201e` |
| `GAME-LOOP-LOG.md` | 改（只加注） | `c53201e` |
| `recovery/reports/ERRATA.md` | **新建** | `c53201e` |
| 引擎仓 `godot/.gitignore` | 改（唯一例外） | `15bbf1f50e` |

**没有代提交别人的产物**：每次提交前都打印 `git status --short`；`dist/**`、`F:\models\**`、
两个 venv、8080/8081、`projects/**` 全程零触碰；`runs/**`（含 TASK-148 的 `runs/gates/**`）
按既有 `.gitignore` 规则不入库，**我也没有强行 add 它们**。

---

## 8. Q9 — 两仓 git 状态

### 8.1 外层仓（`F:/moonbit-hof-rs`，分支 `master`）

```
$ git log --oneline -5
c53201e docs(godot-mcp): TASK-149 D+E - decision-log entries for the corrected mainline, and the normative-document proofread
71f92e8 docs(godot-mcp): TASK-142 residue - ABORTED BRANCH, REFERENCE ONLY, NOT PART OF THIS LINE'S DELIVERY
70a7aa9 docs(godot-mcp): TASK-149 A - commit the MCP-tool audit trail (137/141/142/143/144/145/146/147/148/149)
91783eb TASK-148: republish the 20-game Windows release package from CURRENT sources
da8b3dd TASK-146: label the pre-commit git status block in the report

$ git status --short
（本报告写入前的状态：只有 recovery/work/task149_* 的报告辅助文件未跟踪；见 §8.3）
```

提交规模：

| 提交 | 规模 |
|---|---|
| `70a7aa9` | 307 files changed, **101249 insertions(+)**, 0 deletions |
| `71f92e8` | 7 files changed, **5692 insertions(+), 85 deletions(-)** |
| `c53201e` | 21 files changed, **1514 insertions(+), 3 deletions(-)** |

### 8.2 引擎仓（`F:/moonbit-hof-rs/godot-mcp/godot`，分支 `feature/mcp-server-module-rebuild`）

```
$ git log --oneline -3
15bbf1f50e chore(gitignore): TASK-149 - ignore the machine-local `uid_cache.bin`
ba1587c71e fix(mcp_server): TASK-112 - the three engine defects TASK-111 registered are fixed at the root (one of them blocking and silent), plus one schema override
3fdabe2d9a fix(godot-mcp): TASK-110 - editor_list_signal_connections' registered schema regains `scope`, the one member that made the TASK-051 narrowing unreachable

$ git status --short
（空 —— 引擎工作树干净）
```

**未 push**（任务书只要求提交；且既有流程里 push 需要显式许可）。

### 8.3 关键产物路径 + 身份（任务书 §F.13/Q9）

`sha256` 是**工作区文件**的值（写报告时会变的那几个除外，见下）；
`git blob @HEAD` 是**跨机可复算的身份**（`git rev-parse HEAD:<path>`）：

| 路径 | git blob @HEAD | sha256（工作区） | 字节 | 行 |
|---|---|---|---|---|
| `godot-mcp/recovery/reports/ERRATA.md` | `2121b92329dc91cb56775719a3335342129c3dcb` | `4d49ed89ac873c42ec66d223dfc60a4ffcad0818dbe0836849babf0d296712a9` | 27295 | 348 |
| `godot-mcp/recovery/TEST-CASES.md` | `2b6660d0d56a637bc39b1deb007cd4893db8f78d` | `b6f0164a719500a022891d5c361e3a7964b0f822be92a4f67238287f33dfa7a1` | 528837 | 1252 |
| `godot-mcp/recovery/tasks/TASK-149.md` | `07e6045382e5aa6b8b069bef7757260980c9a09c` | `8c2ed434c199d502a992af6ba0e6319f5dee8bb871bd1ca9dc74dba5340c450f` | 8654 | 104 |
| `DECISIONS.md` | `aa891b8631bbf96abe90f6d022d9f324e5d20061` | `064881f0158cddf0b0122a66685029120700e606fee39c88a28fd3a39bf75379` | 909108 | 8324 |
| `godot-mcp/TOOL-COVERAGE.md` | `3768de1735aa01f995a274455db4f40199f42f0c` | `b7f7f83e8f165efa7f027bfaff693c2b74df1834d39afbb68da132f0e45aa04e` | 266282 | 1057 |
| `godot-mcp/GAME-LOOP-LOG.md` | `23b43089576b3611ff3c1bb32b3a8eefdd2b029a` | `00802aef7a018f239b20ae1912e0a1cb110611a34fce80918691478c44f1d194` | 157464 | 672 |
| `godot-mcp/recovery/reports/PLAYABILITY-REPORT.md` | `4fff93bf7a91036a882d1ce5f4239867510eebfa` | `1f736b13f467184b53a3c7e5154bb4a2b0d0e12202366703e523a335f26c7c62` | 74324 | 871 |
| `godot-mcp/recovery/reports/PLAYABILITY-DEFECTS.md` | `a5c7f992070986a9ffbc16797de8f326b034430e` | `3d04f68e0fe2a150e6739b7261eb1c47030996a02e12803682a0d8cadd25e0d6` | 69739 | 1050 |
| `godot-mcp/recovery/tasks/README.md` | `2540d5989c5df6afce4789e3614e3987bc331927` | `c00e65f64b1baf928830f8d4679716494d1f59eadab205c414f2f9a395831f94` | 4632 | 49 |
| `godot-mcp/recovery/tasks/TEMPLATE-logic-feedback.md` | `2e6df76df53e66feb211dcd429e0f695972469d9` | `10b1851ed1b9bf778816d108ab788dbde6e85dc20ce1785731c974eb29307f72` | 48274 | 593 |
| `godot-mcp/recovery/reports/ACCEPTANCE-TASK-137.md` | `42cb985949d3c2c43c65a1d23d898a754a58ba41` | `6a9bce4428ee76d417e42c07424e670a57c0cc3474893634b2ecd5d25ec87dc5` | 38717 | 219 |
| `godot-mcp/recovery/reports/ACCEPTANCE-TASK-141.md` | `f2a2846eabac9fc269b67a6cb867615e316314d2` | `1404549d8b2e9645bd815cfd2fb1a52dcdd9ce41ece5e5526d7994df0d05b6d7` | 60543 | 501 |
| `godot-mcp/recovery/reports/ACCEPTANCE-TASK-145.md` | `9a974ee71290ac45514b0775a0e54987fdf3224b` | `b233ebb6b58e12acfbceb8380a467fc5768a3682c1023ede2ddd0b2618f434ee` | 32440 | 220 |
| `godot-mcp/recovery/reports/ACCEPTANCE-TASK-147.md` | `559d7838d4776690130a5d79616e696c9609699a` | `f798afc7baa3164472fe7a15ac472f9785d9cb3c8d5d7c6819f398cbbbd8f298` | 30939 | 273 |
| `godot-mcp/tools/playtest_player_t142_prefix.py` | `a1a16830cfabdb54e5a1efaad91355af66979195` | `04354f537c9f0e25b418c1d95a2b3b08950ade6f8d0d387a5744aaddda37485d` | 277930 | 4906 |
| `godot-mcp/recovery/work/task149_docaudit.py` | `df18038d057917da0808af3d6779b6fc4f8389f2` | `ce73dbdcd73e100fd8b880e8f979f4657317e1d61c9f52f1c6db431ade2fb4c5` | 8105 | 183 |
| `godot-mcp/recovery/work/task149_ledger.py` | `0c86bcc31ec2fdd3e159713860fd39324ca70f6e` | `f513f5034b596ec0393e27dea20ade2eb5a9b0936ec81fb5ef97454789348cc5` | 3110 | 78 |
| `godot-mcp/recovery/work/task149_stalepointers.py` | `a3239b633b1125286854bcc179dedbfd9500c38e` | `2a3c4db9872070be7678ee9524540d1f18d171711da8e789390b23416cdb52cc` | 4266 | 102 |
| `godot-mcp/recovery/work/task149_frozenmap.py` | `9b70f2f89fc485c970008da3a8b8bf9e31ce7831` | `4291813c64d62cce07f6d723963fff48a9973b97ec3044d70a980024907c3391` | 4285 | 126 |
| `godot-mcp/recovery/work/task149_pointers.py` | `05af5b8b5a92b5a4b04d09038fde638f772b3106` | `add0616bc68e2d3efddb1e4779d6efe9b6026eb6322bb03e660fc8eb74650cea` | 2182 | 65 |
| `godot-mcp/recovery/work/task149_negclass.py` | `ad19a1796836fabfb1539aca7cd7c8dbf7900630` | `9bad16fbd5f193db53cd41ba3ced1787fbae90cf4560f31102023a975ee972fd` | 4036 | 110 |
| `godot-mcp/recovery/work/task149_probeshape.py` | `dc27a881cd12d19e69ac6f0cd5bc5e90a12e2e64` | `e5fc70f7f43bfd823d45dc0791048bb721c6f17bf57d1b5fb792eaa3fcb0f75d` | 1591 | 42 |
| `godot-mcp/recovery/work/task149_stage.py` | `314fc6cefea2a2d66074e73d7cce64299f21fe40` | `945315a11939541068e0c61ce0ba2ad27d16e035a8dbfd0e4a94cac219740e68` | 2951 | 94 |
| **`godot-mcp/recovery/reports/TASK-149-REPORT.md`（本文件）** | 见提交 `TASK-149 report` 的 blob | `python recovery\work\task149_hashes.py` 可复算 | — | — |

> 用 `python godot-mcp\recovery\work\task149_hashes.py` 可一次性复算上表全部
> `git blob @HEAD` + `sha256` + 字节 + 行数（只读、无重定向）。
> **本文件自己**的 sha256 与 git blob 在写入报告时还不可得（自指），故由提交
> `TASK-149 report` 与上面的脚本给出。

---

## 9. `ERRATA.md` 收录了什么（Q7 明细）

新建 `recovery/reports/ERRATA.md`（348 行），**逐条「文件 / 原说法 / 更正 / 依据」**，
并给出**可复算命令**与「结论受不受影响」。点名的 5 类全部在：

| 编号 | 点名的勘误 | 对应任务书 §E.12 |
|---|---|---|
| **E-1** | `TASK-140-REPORT.md` 同一报告 `194` vs `186`（权威 = **194**，TASK-149 独立复算区间宽度仍为 194） | ✅ 第 1 条 |
| **E-2** | `TEST-CASES.md` 的 `121` 不可复现 ⇒ **142 = 119 + 21 + 2**（给代码发出点） | ✅ 第 2 条 |
| **E-3** | `TASK-129` §9.4「只有一个仓」⇒ 本机**两个**（外层 + 嵌套引擎仓）+ 1 个无关克隆 | ✅ 第 3 条 |
| **E-4** | `TASK-136` §7 第 9 行 platformer `TILE 4,27` ⇒ **`TILE 3,27`**，**附可机检锚点** | ✅ 第 4 条 |
| **E-5** | `TASK-136` §4.1 strict 列、§1.2 `PASS(baseline only)` 举例（真例 pong/asteroids） | ✅ 第 5 条 |
| E-6 | `TASK-136` 其余已收口勘误（②③④⑤）的索引 | 我自行补充 |
| E-7 / E-8 | `ACCEPTANCE-TASK-137/141` 的行号指针指向冻结版（位移分段 +58/+99/+119/+174） | 我自行补充 |
| E-9 | `TASK-142-REPORT.md` 引的 `runs/**` 产物从 git 不可复得（限制登记） | 我自行补充 |
| E-10 | `ACCEPTANCE-TASK-145` 的 `27/404/785` 是过期不是错误 | 我自行补充 |
| E-11 | 任务书点名的 `TASK-147-REPORT.md` **不存在** | 我自行补充 |
| E-12 | `ACCEPTANCE-TASK-147` 的 Y1/X5/X6 的落实状态 | 我自行补充 |

---

## 10. 未达标项（Q10，如实登记）

**U1 — §B 的 `tools/**` 与任务书 §2.3「`tools/**` 只读」冲突，我按 §B 执行**

- 任务书 §B.3 要求把 3 个 `tools/**` 文件作为该独立提交的成员，§2.3 又规定 `tools/**` 只读。
  两者**不可能同时满足**。我选择**按 §B.3 提交**（用户的"保留、不丢弃"是明确裁定，
  且 §B.4 只要求"发现与主线冲突**只报告不处置**"——不处置 ≠ 不提交）。
- **我没有在自己的工作里改过 `tools/**` 的任何字节**；提交的是**接手时就有的**既存改动。
- 该冲突已写进 `71f92e8` 的提交信息与 §3。**如果用户的意图是"连既存改动也不能提交"，
  这个提交需要被 revert**——但那样就与"保留、不得丢弃"矛盾，故我判断 §B.3 优先。

**U2 — `recovery/work/task148/unzip-test/` 里的 `.exe`/`.pck` 二进制进了历史**

- 任务书 §A.1 明确要求提交 `recovery/work/task148/`，而该目录里有 TASK-148 端到端验证
  **从交付 zip 解出**的 pong/snake 整款副本（含 `.exe`/`.pck`/`.pdb`）。
- 我按任务书执行（`70a7aa9`，`+101249` 行的大头就是这些）。**如果决策者认为 work 目录
  应当只留脚本与 JSON**，这是一个**需要修正的"过宽提交"**（可以后续
  `git rm --cached` 那些二进制并加忽略规则，但那是**新的决策**，不在本批授权内）。

**U3 — `GAME-LOOP-LOG.md` 与 `PLAYABILITY-*` 只做了"范围/来源注"，没有逐条数字校对**

- 任务书 §E.9 把它们列进"规范类"校对范围，但它们的**每一个数字**的依据都在 `runs/**`
  （**被 `.gitignore` 忽略、只存在于本机**）。逐条校对意味着：
  ①核对本机 `runs/**`（大工程、且与主线交付无关）；②改一份**其依据不可跨机复算**的文档。
- 我只做了：引用路径存在性检查（通过）、来源/范围注（主线已校正 D212）、
  以及把它们的不自洽登记进 `ERRATA.md` 的机制。
- **如果决策者要求逐条校对**，需要明确：(a) 以本机 `runs/**` 为准吗？
  (b) 主线的**什么交付**依赖这些数字？（按 D212，答案是"没有"。）

**其他如实声明**

* **`pwsh` 不存在**：preflight 用 Windows PowerShell 5.1 跑（§4），
  与既有台账（TASK-144 §8.2 的 g09/g10）一致。
* **`ERRATA.md` 的 E-1 有两个下标 +1**：TASK-142 §K.1 记的 501/694 与我现在算的 502/695
  相差 1（台账在锚点记录之后又追加了新条目）——**区间宽度 194 两边一样**，
  已在 E-1 里逐字解释，不是不一致。
* **未 push**：两个仓都只提交、未推送（任务书没要求；既有流程里 push 要显式许可）。

---

## 11. 交付物清单

| 类型 | 路径 | 状态 |
|---|---|---|
| 报告（本文件） | `recovery/reports/TASK-149-REPORT.md` | 新建 |
| 勘误索引 | `recovery/reports/ERRATA.md` | 新建（`c53201e`） |
| 决策日志 | `DECISIONS.md`（+D212–D215） | 改（`c53201e`） |
| 规范类文档 | `recovery/TEST-CASES.md`、`recovery/tasks/TEMPLATE-logic-feedback.md`、`TOOL-COVERAGE.md`、`GAME-LOOP-LOG.md`、`recovery/reports/PLAYABILITY-{REPORT,DEFECTS}.md` | 改（`71f92e8` + `c53201e`） |
| 最新报告校对注 | `recovery/reports/ACCEPTANCE-TASK-{137,141,145,147}.md` | 改（`c53201e`） |
| 审计轨迹 | 5 份报告 + 10 份任务书 + 4 个 work 目录 | 入库（`70a7aa9`） |
| 已中止支线 | 6 个既存改动 + 冻结副本 | 入库（`71f92e8`） |
| 引擎仓 | `godot/.gitignore` | 提交（`15bbf1f50e`） |
| 复算脚本 | `recovery/work/task149_{check,negclass,stage,docaudit,probeshape,pointers,stalepointers,frozenmap,ledger,hashes}.py` | 入库（`c53201e` + 报告提交） |
| 暂存清单/提交信息 | `recovery/work/task149_{stage_a,stage_b}.txt`、`task149_msg_{a,b,c,de}.txt` | 入库（报告提交） |

**只返回路径 + 一行状态**（任务书 §4）：
`F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-149-REPORT.md`
—— A/B/C/D/E 全部完成；3 个提交（外层 `70a7aa9`/`71f92e8`/`c53201e` + 引擎 `15bbf1f50e`）；
复跑 `pytest tools\tests` = 30 passed、矩阵自洽 `YES`、preflight `WORKING_TREE_RED=0`；
未达标 3 条（U1 `tools/**` 冲突按 §B 执行、U2 work 目录二进制偏宽、U3 游戏侧文档未逐条校对）。
