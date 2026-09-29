# TASK-152-ACCEPTANCE — TASK-152（g05 自包含）独立验收

* 验收者：**独立验收子代理**（无上游对话上下文；不继承实现者/调度者任何结论）
* 任务书：`godot-mcp/recovery/tasks/TASK-152-ACCEPT.md`
* 被测引擎仓：`F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`）
  * 被测 HEAD **`bef4be04077e855918013355b03ce7a6795a910a`**（报告写 `bef4be0407`），工作树 `git status --porcelain` 空
  * 区间基线 `035edfce7f`（mono 二进制自报锚点 `4.8.dev.mono.custom_build.035edfce7`）
* 验收者自造证据目录：`godot-mcp/recovery/work/task152-acc/`（`ast_scan_independent.py`、`plant.py`、`gates/`）
* 实验纪律：只读为主；唯一写入是 §3 的两处受控植入（已逐字节恢复，三法证明）。**未占用/未探测 9877**；自用端口只有 9888/9889（门脚本内部使用），收尾复核全部释放。未 push、未 stage、未改 hof-rs 侧任何跟踪文件、未改任何既有检查。**发现的问题一处未修**。

---

## 1. 结构化结论

```json
{
  "verdict": "pass",
  "criteria": [
    {
      "id": "SELF_CONTAINED",
      "pass": true,
      "evidence": "check_rename_map.py:102 `DEFAULT_OLD_CONTRACT = os.path.join(DOCS, \"rename-baseline-tools-list.json\")`，DOCS 由 :71-72 的 __file__ 推导。g05 执行路径 = tools\\run_gates.ps1:219 `python modules\\mcp_server\\docs\\scripts\\check_rename_map.py`（无参数）。非注释行的 hof-rs 路径命中=0（Select-String 'hof-rs|moonbit' 的 8 处全部在 :78-99 的 `#` 注释内）。自写 AST 扫描（排除 2 个 docstring）路径字面量命中=0（唯一命中是 :257 的检查标签 'D1 L1..L4'，被宽松的 '..' 模式误捕，非路径）；全部 open() 实参只有 :140/:172/:187/:299，均由 DOCS 派生。跨 cwd 复跑：`cd C:\\ && python <abs>\\check_rename_map.py` ⇒ `RESULT: PASS (all checks green)` exit 0。"
    },
    {
      "id": "BASELINE.BYTES",
      "pass": true,
      "evidence": "`modules/mcp_server/docs/rename-baseline-tools-list.json`：bytes=48749、sha256=8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54、`git hash-object`=543b49b2583bf06c3aba2a320649a31eda272e3e、`json.load` 得 result.tools 条数=174、LF=0 CR=0。溯源自证：`git -C F:\\moonbit-hof-rs rev-parse 'db2eed7^:tests/fixtures/mcp/tools_list.json'` = 543b49b2583bf06c3aba2a320649a31eda272e3e；`git cat-file blob 543b49b2…` 经 sha256sum = 8f8051c4…；与引擎内基准 `cmp` ⇒ CMP_IDENTICAL（逐字节相同）；`git cat-file -s` = 48749。"
    },
    {
      "id": "GATES.10",
      "pass": true,
      "evidence": "`powershell -NoProfile -ExecutionPolicy Bypass -File tools\\run_gates.ps1 -RunGates -Tag task152acc -OutDir …\\recovery\\work\\task152-acc\\gates`（命令集即 tools\\run_gates.ps1:214-225 原文，未复制未替换；-RunGates 只是强制十门全跑）。十门 `GATE_EXIT=0`：g01 160/160（6801/6801 断言）、g02 1586/1586（431114/431114）、g03 `TOOL-GROUPS CHECK PASS BYTES 5681 SHA256 b83d79d3…`、g04 3/3（editor 154 / game 73 / contract 177；guard_user_port_9877 pid_before=-1 pid_after=-1）、**g05 `PASS=30 FAIL=0` `RESULT: PASS (all checks green)`**（B0 8f8051c4…、B1 len=174、B2 contract-only=[] map-only=[]）、g06 PASS、g07 10/10、g08 `UNCLASSIFIED = 0`（185 文件）、g09 `ANCHOR_STRUCTURAL_EQUIVALENT DIFF_COUNT=3 SAFE_COUNT=3 RED_COUNT=0 RESULT PASS`、g10 22/22。抽验的两道非实现者引用门：g03 与 g06 均由我自跑并读全文输出。"
    },
    {
      "id": "NON_VACUITY",
      "pass": true,
      "evidence": "①在引擎内基准植入改名（`\"name\":\"get_filesystem_tree\"` → `\"name\":\"legacy_get_filesystem_tree\"`，纯字节替换，48749→48756，sha a0603adc…）⇒ g05 exit 1，`[FAIL] B0`（字节钉）+ `[FAIL] B2 contract-only=['legacy_get_filesystem_tree'] map-only=['get_filesystem_tree']`，**点名被植入的名字**，其余检查仍绿。②在改名表植入错映射（`\"new_name\": \"project_get_statistics\"` → `\"get_statistics\"`，70917→70909，sha c3d1b8bf…，基准 sha 仍 8f8051c4…）⇒ g05 exit 1，**恰好一条** `[FAIL] D1 L1..L4 over all 174 new_name violations=[('get_statistics','L1 pattern')]`。两处恢复：`git checkout --` rc=0，`git status --porcelain` 空、`git diff --stat` 空、四文件 `git hash-object`==HEAD blob（map 743bc79c…／baseline 543b49b2…／check_rename_map.py 1503e8d8…／tools_list.renamed.json 3b1b191d…）ALL_FOUR_BYTE_EQUAL=True。"
    },
    {
      "id": "G09.GUARDRAILS",
      "pass": true,
      "evidence": "(a) `git diff --name-only --no-renames 035edfce7f..HEAD` 恰好 3 个：`modules/mcp_server/docs/MCP-SERVER-HANDOVER.md`、`modules/mcp_server/docs/rename-baseline-tools-list.json`、`modules/mcp_server/docs/scripts/check_rename_map.py` ⇒ .md/.json/.py，**全部落在判据自带非编译白名单**，无任何 .cpp/.h。 (b) 用判据同一套编译输入扩展名过滤该区间 ⇒ compile-input count = 0。 (c) `git diff --quiet 035edfce7f..HEAD -- modules/mcp_server/scripts/check_engine_anchor.ps1` exit 0（零 diff）；`check_hardcoded_counts.py` 同区间 exit 0（零 diff）；外层 `tools/run_gates.ps1` 未改（`git status --porcelain` 空、blob b3c5ea655b949836f7dc640fc54c255bc526cb16、mtime 2026-09-27 03:33:00、最后由 TASK-099 的 bf83a9e 提交）。"
    },
    {
      "id": "SCOPE.HONESTY",
      "pass": true,
      "evidence": "`modules/mcp_server/scripts/gen_renamed_contract.py:1800 DEFAULT_OLD_CONTRACT = r\"F:\\moonbit-hof-rs\\tests\\fixtures\\mcp\\tools_list.json\"`、`:1804 OLD_CONTRACT_SHA256 = \"8f8051c4…\"`（逐行读到）。它不在 g05 执行路径上（run_gates.ps1:219 只跑 check_rename_map.py，后者只 import 标准库）。⇒ 实现者自曝的范围边界**真实**；**「模块不再依赖跨仓输入」这句话不成立，不得写成完成态**（赞同立 TASK-153）。"
    },
    {
      "id": "SELF_REPORTED",
      "pass": true,
      "evidence": "`check_hardcoded_counts.py` 在 035edfce7f..HEAD 零 diff（`git diff --quiet` exit 0）；g08 现真为 `UNCLASSIFIED = 0` / `RESULT: PASS`。溯源日期：常量旁 `taken : 2026-09-29` 与新增基准的提交 `069a2e2ea8` committer 时间 `2026-09-29 08:48:49 +0800` 一致，且验收时机器时间 `2026-09-29 09:05` ⇒ 与该事实相容（中间那版编造的 2026-02-15 已不存在于 HEAD）。"
    },
    {
      "id": "GUARDS",
      "pass": true,
      "evidence": "9877：门运行前后 `netstat` 均 \"none listening\"，g04/g10 内部守卫 `pid_before=-1 pid_after=-1`；9888/9889 运行前空闲、收尾复核仍空闲。未 push：引擎 `git rev-list --left-right --count HEAD...origin/feature/mcp-server-module-rebuild` = `6 0`，`origin/...` 仍 `15bbf1f50ea45146bb4a644ffde9898d1b7ca7ee`，reflog 全是 commit。hof-rs 侧：`git status --porcelain` 无跟踪改动、`git diff --stat` 空，夹具仍 bytes 71481 / sha256 50c5fb42… / 177 条 / mtime 2026-09-28 22:37:34。无新依赖：区间内 `check_rename_map.py` 的 import 行零增删（7 个标准库）。无削弱：该文件 diff 仅 1 行路径常量、1 行注释块、1 行新增常量与 B1 字面量→命名常量（值同为 174），B0/B2/C/D/E/F/G 表达式原样。"
    }
  ],
  "defects": [
    { "id": "DEF-1", "severity": "info", "what": "跨仓耦合在本模块内并未清零：`modules/mcp_server/scripts/gen_renamed_contract.py:1800` 仍硬编码 hof-rs 绝对路径、`:1804` 仍冻结同一 sha256（已被实现者自曝，且不在 g05 执行路径上）。", "reproduction": "`git -C godot rev-parse HEAD:modules/mcp_server/scripts/gen_renamed_contract.py` 后 read :1795-1805；或 `Select-String -Path modules\\mcp_server\\scripts\\gen_renamed_contract.py -Pattern 'moonbit-hof-rs'`" },
    { "id": "DEF-2", "severity": "info", "what": "B0 对「基准文件被任何字节改动」必然变红，因此单看 §3 实验 1 是 2 红；这不是缺陷，是 B0 的设计语义（钉字节）。若将来批次的验收脚本按「只能红一条」自动判分，会误判。", "reproduction": "实验 1 输出：`[FAIL] B0 …` + `[FAIL] B2 …`；实验 2（只动 map）为恰好 1 红，可作单条归因的对照。" },
    { "id": "DEF-3", "severity": "info", "what": "实现者报告 §2.3 引用「AST 扫描：commented/docstring 之外字符串常量命中 0」；我独立扫描在宽松模式下会命中 1 处非路径标签 'D1 L1..L4'。结论（无仓外路径字面量）一致，但报告该句的字面表述对扫描器的模式敏感，属表述精度问题。", "reproduction": "`python recovery\\work\\task152-acc\\ast_scan_independent.py`" }
  ],
  "risks": [
    "g05 的绿色现在依赖一份签入的 48 KB 冻结 JSON（`rename-baseline-tools-list.json`）：它是「旧契约」的字节快照，将来若 171 项旧契约本身需要合法换代，必须同时更新该文件与两个冻结常量——这是刻意的强耦合到引擎仓，但需要下一位读者知道「改它就等于重定基线」。",
    "g09 的 `ANCHOR_STRUCTURAL_EQUIVALENT` 只在 `RED_COUNT=0` 时有意义；本批次三护栏均已独立核验成立，但该判据的宽松性依赖 `check_engine_anchor.ps1` 的白名单未被松动——本次零 diff，属可证状态。",
    "TASK-153 未落地前，任何把「模块不再依赖跨仓输入」当作事实的文档/交接说明都会失真。"
  ],
  "unverified": [
    "未重建引擎（本批无编译输入，重建只会改变二进制字节并使 --version 虚假前进）；因此「重建后会得到 ANCHOR_EQUAL」仍是实现者的推断，我没有验证，也不需要验证。",
    "未复现 g08 历史中间态（注释续行导致的两个 UNCLASSIFIED）：最终树上无法再生该中间状态；我只验证了它声称的结果（检查器零 diff、g08 UNCLASSIFIED=0）。",
    "未重跑 plain-console（非 mono）变体；本次仅 mono `035edfce7`。",
    "未核验 hof-rs 的「夹具 mtime 早于开工」这一时间线主张的完整历史（我只能观测当前 mtime/sha，早于 TASK-152 的提交时间，与之相容）。",
    "未逐一复核实现者自造证据目录 `recovery/work/task152/**` 的每个脚本输出（按任务书它们是线索；本报告全部证据由我自产）。"
  ]
}
```

---

## 2. 逐项核对表（TASK-152-ACCEPT §2）

| § | 复核项 | 结论 | 我的关键证据（自跑） |
|---|---|---|---|
| 2.1 | 自包含：默认指向引擎内、执行路径无 hof-rs 路径 | **PASS** | `check_rename_map.py:102`；非注释 hof-rs 命中 0；AST 路径字面量命中 0；`open()` 仅 :140/:172/:187/:299；跨 cwd 复跑仍 PASS |
| 2.2 | 基准字节：sha256 `8f8051c4…` / 174 条 / blob `543b49b2…` | **PASS** | 48749 B；sha256 `8f8051c4…`；`git hash-object` = `543b49b2…`；JSON 174 条；与 hof-rs `db2eed7^` blob `cmp` 逐字节相同 |
| 2.3 | 十道门 10/10 exit 0，g05 30/30，g01/g02/g04/g07/g08/g10 数字 | **PASS** | 十门 `GATE_EXIT=0`；g05 PASS=30 FAIL=0；g01 160/160；g02 1586/1586；g04 3/3（154/73/177）；g07 10/10；g08 UNCLASSIFIED=0；g10 22/22。抽验 g03/g06 全文亦过 |
| 2.4① | 基准植入 ⇒ 红在 B2 且点名 | **PASS** | B2 `contract-only=['legacy_get_filesystem_tree'] map-only=['get_filesystem_tree']`；伴生 B0 红（字节钉，见 DEF-2） |
| 2.4② | 映射植入 ⇒ 恰好一条（D1） | **PASS** | 唯一 FAIL：`D1 … violations=[('get_statistics','L1 pattern')]` |
| 2.4 | 逐字节恢复（status/diff/hash-object 四文件） | **PASS** | status 空、diff --stat 空、四文件 work blob == HEAD blob |
| 2.5 | g09 三护栏 | **PASS** | 见 §4 |
| 2.6 | 诚实范围（生成器仍读 hof-rs） | **PASS**（边界属实；强主张不成立） | `gen_renamed_contract.py:1800/1804` 实读 |
| 2.7 | 自曝两处 | **PASS** | 检查器零 diff；g08 UNCLASSIFIED=0；溯源日期 2026-09-29 与提交时间一致 |
| 2.8 | 禁区自查 | **PASS** | 9877 未碰；9888/9889 前后空闲；origin 仍 `15bbf1f50e`；hof-rs 跟踪区零改动；无新依赖；无检查被删/放宽 |

**验收结论：`verdict = pass`。** 没有任何 §4 的 fail 门槛被触发。

---

## 3. 反例清单（我植入/改动了什么、观测到什么、是否推翻）

| # | 植入 | 位置与字节 | 观测（原始输出） | 是否推翻主结论 |
|---|---|---|---|---|
| 1 | 基准改名 `get_filesystem_tree` → `legacy_get_filesystem_tree` | `docs/rename-baseline-tools-list.json`，纯字节替换 1 处，48749→48756，sha `a0603adc03ecd7cf1de2c6872f6f57bf3ea614b5646a6b9b09e4c8644d0aebce` | g05 exit 1；`[FAIL] B0`（报新 sha）+ `[FAIL] B2 contract-only=['legacy_get_filesystem_tree'] map-only=['get_filesystem_tree']`；其余 28 检查全绿 | 否 —— 门仍能抓改名回归，且点名 |
| 2 | 映射错名 `"new_name": "project_get_statistics"` → `"get_statistics"`（丢通道前缀） | `docs/tool-rename-map.json`，1 处，70917→70909，sha `c3d1b8bf0e831b90e4c5a8bac731d87d434da591c96187cbd3ef594e0c34d283`；基准 sha 未变 `8f8051c4…` | g05 exit 1；**恰好 1 条** `[FAIL] D1 … violations=[('get_statistics','L1 pattern')]` | 否 —— 单条归因成立 |
| 3 | 显式把 `--old-contract` 指向 hof-rs 现夹具 | 只读调用 | g05 exit 1；`[FAIL] B0 50c5fb42…` + `[FAIL] B1 len=177` + `[FAIL] B2`；而**默认**（引擎内基准）同树 PASS | 否 —— 反向证明：绿来自「基准搬进引擎仓」，不是「hof-rs 恰好还匹配」 |
| 4 | 从 `C:\` 跨 cwd 运行 g05（默认参数） | 只读调用 | `MAP F:\…\godot\modules\mcp_server\docs\tool-rename-map.json`；`RESULT: PASS (all checks green)` exit 0 | 否 —— 默认路径由 `__file__` 派生，非 cwd/仓外 |
| 5 | 恢复后三法校验 | `git checkout --` ×2 | status 空 + diff --stat 空 + 四文件 blob 与 HEAD 逐字节相同 | 否 —— 无残留、无 CRLF 漂移 |

另：我自写 AST 扫描（`ast_scan_independent.py`）是一次**反向验证工具**，不修改任何被审计文件；它只驳回了一个宽松模式的误报（检查标签 `L1..L4`），未发现任何仓外路径字面量。

---

## 4. 对 `g09` 判据变更的独立把关结论

**采纳状态：三护栏全部成立 ⇒ 本次允许以 `ANCHOR_STRUCTURAL_EQUIVALENT` + `RED_COUNT=0` 作为 g09 的通过判据。**（这是对调度者放宽判据的事后把关，不是我放宽的——`check_engine_anchor.ps1` 一字未改。）

机器事实（我自跑）：

```
ANCHOR_JUDGE VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT
ANCHOR_JUDGE ANCHOR=035edfce7 ANCHOR_REPORTED=035edfce7 HEAD=bef4be040
ANCHOR_JUDGE ANCESTOR=yes
ANCHOR_JUDGE DIFF_COUNT=3 SAFE_COUNT=3 RED_COUNT=0
ANCHOR_JUDGE SAFE modules/mcp_server/docs/MCP-SERVER-HANDOVER.md
ANCHOR_JUDGE SAFE modules/mcp_server/docs/rename-baseline-tools-list.json
ANCHOR_JUDGE SAFE modules/mcp_server/docs/scripts/check_rename_map.py
ANCHOR_JUDGE RESULT PASS
```

**那 3 个 diff 文件的完整清单与分类：**

| # | 文件 | 类型 | 是否编译输入 |
|---|---|---|---|
| 1 | `modules/mcp_server/docs/MCP-SERVER-HANDOVER.md` | 文档（.md） | 否 |
| 2 | `modules/mcp_server/docs/rename-baseline-tools-list.json` | 数据（.json） | 否 |
| 3 | `modules/mcp_server/docs/scripts/check_rename_map.py` | 门脚本（.py） | 否（判据白名单 `:87` 含 `.py`；非 `config.py`） |

**该 3 个 diff 只是文档/数据/门脚本——不含任何 `*.cpp` / `*.h` / `*.tscn` / `config.py` 等编译输入。** 逐条护栏的独立证据：

* (a) `git diff --name-only --no-renames 035edfce7f..HEAD` 恰好输出上述 3 行，无第四行；扩展名全在判据自带 SAFE 白名单（`.md`/`.json`/`.py`）。
* (b) 用判据自己的编译输入集合（`check_engine_anchor.ps1:75-84` 的扩展名 + `sconstruct/sconscript/scsub/config.py/makefile/gnumakefile`）过筛该区间 ⇒ **compile-input count = 0**；`git diff --stat` 为 `3 files changed, 40 insertions(+), 2 deletions(-)`。
* (c) `git diff --quiet 035edfce7f..HEAD -- modules/mcp_server/scripts/check_engine_anchor.ps1` ⇒ exit 0（**零 diff**）；`check_hardcoded_counts.py` 同区间 ⇒ exit 0；外层 `tools/run_gates.ps1` 亦未被 TASK-152 触碰（工作树干净、blob `b3c5ea65…`、mtime `2026-09-27 03:33:00`、最后提交为 TASK-099 的 `bf83a9e`）。⇒ **判据脚本本身没有被松动。**

补充说明（我认同实现者对该判据语义的读法）：`ANCHOR_STRUCTURAL_EQUIVALENT` 的字面含义**不是**「等于 HEAD」；本次 `ANCHOR=035edfce7`、`HEAD=bef4be040`。它成立的可证内容是「两 commit 之间的差异不可能改变被编进二进制的行为」，而这一点恰由 (a)(b) 独立坐实。若要求 `ANCHOR_EQUAL`，唯一途径是重建一个**不含新代码**的二进制来让 `--version` 前进到 `bef4be0407`——那会把判据推向鼓励伪造，故我同意本次按「结构等价 + RED_COUNT=0」通过。

---

## 5. 未验证项与理由

1. **未重建引擎**：本批 3 个文件无编译输入（(b) 已证），重建只会改变二进制字节并使 `--version` 虚假前进。⇒ 「重建即可得 `ANCHOR_EQUAL`」保持为**推断**，未验证，且不建议做。
2. **未复现 g08 的历史中间态**（裸 `152` 续行导致两个 UNCLASSIFIED）：最终树上该中间状态不可再生。我只验证了其**后果**：`check_hardcoded_counts.py` 零 diff、`g08` UNCLASSIFIED=0。
3. **未跑 plain-console 变体**：本次只看 mono `4.8.dev.mono.custom_build.035edfce7`（任务书未要求另一变体）。
4. **未做超过 3 个 diff 文件的更大规模反例**（如同时改基准与映射、或改 `--contract`）：任务书只要求两处植入。
5. **未核验实现者证据目录内每个输出的真实性**：按任务书它们是线索；本报告的全部证据由我自产，故不依赖它们。
6. **未评估 TASK-153 的实现**（生成器一行级修复尚不存在）；本报告只对「该耦合仍存在」这一事实作证。

---

## 6. 我没有独立复核的部分

* `recovery/work/task152/**` 里实现者自建脚本的内部逻辑（`materialise_baseline.py`、`exp*_plant_*.py`、`run_gates_task152.ps1`）：我只把它当线索，用**我自己的** `plant.py` + `run_gates.ps1` 重做了等价实验。
* hof-rs 侧对象库的写入历史（我只能证明当前无跟踪改动、夹具 sha/mtime 与其自身重采后的值一致）。
* 门脚本内部除 g05/g09 之外的判定逻辑（如 `accept_m1.ps1` 的 22 个 case、`check_hardcoded_counts.py` 的分类器实现）——我只核验它们的**当前行为**（输出与退出码），未逐行审计其判定是否「足够强」。
* 调度者 D227 里对 g09 判据的立法表述（`DECISIONS.md`）我只读了，未参与其立法。

---

## 7. 给下一批的建议（**我没有改任何代码**）

1. **TASK-153 应当做，且措辞要守住**：把 `gen_renamed_contract.py:1800/1804` 指向 `docs/rename-baseline-tools-list.json` 与同一 sha/条数常量之后，才可以写「契约生成与契约自检共用同一个引擎内基准」。**在此之前，任何「模块不再依赖跨仓输入」的完成态表述都必须被驳回**（本报告 §1 SCOPE.HONESTY 已如此判定）。
2. **给 g05 的基准加一句「改它=重定基线」的显式警告**（它现在已经是全门唯一的外部数据输入）：建议在基准文件名或常量注释里写明「此文件是 174 项旧契约的字节快照，修改它等同重定基线，必须同时更新 `OLD_CONTRACT_SHA256`/`OLD_CONTRACT_TOOL_COUNT` 并走一次规范级变更」。
3. **把「非空洞性」固化成可复用脚本**：本次我用 `recovery/work/task152-acc/plant.py` 重做了两处植入 + 三法恢复；建议下一批直接复用（`plant → run g05 → assert 指定检查红 → checkout → 三法校验`），把「必须红、必须点名、必须逐字节复原」变成一条命令的退出码，而不是一次性的手工叙述。
4. **B0 的归因语义建议注明**：任何改基准字节的植入都必然双红（B0 + 目标检查）；验收脚本若做「只能红一条」的自动判分，需按实验 2（只动 map）归因，或把 B0 定义为「字节封印」而非功能检查。
5. **g09 判据的护栏建议写进判据脚本自身**（而不是只写在任务书里）：例如让 `check_engine_anchor.ps1` 在输出 `ANCHOR_STRUCTURAL_EQUIVALENT` 时**同时**打印 `git diff --quiet` 对 `scripts/check_engine_anchor.ps1` 与 `tools/run_gates.ps1` 的结果（等价于「判据自证未被松动」）。这是判定层的强化，不是放宽。

---

## 附：本报告全部证据的自产命令索引

| 用途 | 命令 |
|---|---|
| 十道门 | `powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_gates.ps1 -RunGates -Tag task152acc -OutDir F:\moonbit-hof-rs\godot-mcp\recovery\work\task152-acc\gates` |
| 基准字节 | `git hash-object modules\mcp_server\docs\rename-baseline-tools-list.json`；`Get-FileHash -Algorithm SHA256`；`python -c "…json…"` |
| 溯源 blob | `git -C F:\moonbit-hof-rs rev-parse 'db2eed7^:tests/fixtures/mcp/tools_list.json'`；`git cat-file blob 543b49b2…` + `cmp` |
| 自包含扫描 | `python recovery\work\task152-acc\ast_scan_independent.py` |
| 植入与恢复 | `python recovery\work\task152-acc\plant.py {baseline|map} {plant|restore}`；`python plant.py baseline verify` |
| g09 护栏 | `git diff --name-only --no-renames 035edfce7f..HEAD`；`git diff --quiet 035edfce7f..HEAD -- modules/mcp_server/scripts/check_engine_anchor.ps1` |
| 禁区 | `netstat -ano \| Select-String ":9877\s.*LISTENING"`；`git rev-list --left-right --count HEAD...origin/feature/mcp-server-module-rebuild`；hof-rs `git status --porcelain` / `git diff --stat` |
