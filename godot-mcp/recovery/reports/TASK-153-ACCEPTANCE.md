# TASK-153 独立验收报告 — `gen_renamed_contract.py` 去跨仓耦合

* 验收者：**独立验收子代理**（无上游对话上下文；唯一授权来源 `godot-mcp\recovery\tasks\TASK-153-ACCEPT.md`）。
  未继承实现者（`TASK-153-REPORT.md`）或调度者（`DECISIONS.md` D227–D229）的任何**结论**；下面每一条证据
  都是本验收会话自己跑出来的。
* 被测：引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`）
  * 起点/基线 `bef4be04077e855918013355b03ce7a6795a910a`
  * 被测 HEAD **`28432f859fdbf1a88d15c72bd71b91ffb55db7d3`**（工作树 `git status --porcelain` = 0 行）
* 外层仓：`F:\moonbit-hof-rs`（HEAD `7ed7820fe001664fc77884b1022dd488ef8be74b`）
* 本验收的自产证据目录：`godot-mcp\recovery\work\task153-accept\`（脚本、原始输出、门产物）

---

## 1. 结构化结论

```json
{
  "verdict": "pass",
  "criteria": [
    {
      "id": "DECOUPLED",
      "pass": true,
      "evidence": "grep -ni 'hof-rs|moonbit-hof-rs' modules/mcp_server/scripts/gen_renamed_contract.py -> 6 hits, all at :1803 :1804 :1818 :1819 :1825 :1826 and every one starts with '#'. Own AST scan (recovery/work/task153-accept/my_ast_scan.py, SCAN_EXIT=0): docstrings excluded 5, executable hof-rs string literals 0, f-string fragments 0, open() at :1855/:1991/:1993/:2242 all take Name args (path/old_path/map_path/out_path). Import-time resolution: DEFAULT_OLD_CONTRACT=F:\\moonbit-hof-rs\\godot-mcp\\godot\\modules\\mcp_server\\docs\\rename-baseline-tools-list.json, and DEFAULT_OLD_CONTRACT lives in the ENGINE module docs dir = True. Ran the generator once from C:\\ (CWD=/c): GEN_EXIT_FROM_C=0, 154311 B, sha256 8461b6ee...5373; cmp against the engine-root run = exit 0."
    },
    {
      "id": "BEHAVIOUR_IDENTICAL",
      "pass": true,
      "evidence": "Pre-change script extracted with `git show bef4be0407:modules/mcp_server/scripts/gen_renamed_contract.py` (sha256 35bfd8752abda2b5...; its :1800 is the literal r\"F:\\moonbit-hof-rs\\tests\\fixtures\\mcp\\tools_list.json\"). Ran it with --old-contract/--map pointing at the ENGINE baseline/map (+ explicit --out): PRE_EXIT=0, 154311 B, sha256 8461b6eee63fc17b6547a2640b40e3383f5618f22658611aa8c2e17b704e5373. Ran the post-change generator with ALL DEFAULTS from C:\\: same 154311 B / 8461b6ee...5373. `cmp` = exit 0. => the change moved an input source, it did not change behaviour."
    },
    {
      "id": "NON_VACUITY",
      "pass": true,
      "evidence": "Four acceptor-designed plants (none copied from the implementer or TASK-152), each with byte-exact restore proven by `git status --porcelain` empty + `git diff --stat` empty + `git hash-object` == HEAD blob. A1 (baseline, TWO equal-length names open_scene/stop_scene exchanged: 48749->48749 B, JSON valid, 174 unique names, sha 8f8051c4..->3d2b08ee..): GEN_EXIT=1, 'FATAL: old contract sha256 3d2b08ee... != the frozen 8f8051c4...', OUTPUT_WRITTEN=False. A2 (baseline, whole tool tilemap_get_cell deleted: 48749->48470 B, 173 tools): GEN_EXIT=1, OUTPUT_WRITTEN=False. B1 (map, two entries given ONE new_name while channel+verb stay consistent, so only the duplicate self-check can fire: 70917->70914 B): GEN_EXIT=1, 'FATAL: duplicate new names in the output: [project_search_file_names]', OUTPUT_WRITTEN=False. B2 (map, project_get_info -> project_read_info with declared verb still 'get': 70917->70918 B): GEN_EXIT=1, 'FATAL: L3 declared verb get != parsed read: project_read_info', OUTPUT_WRITTEN=False. All four are reports on stderr with a non-zero exit, never a warning, and no output file was created."
    },
    {
      "id": "GATES.10",
      "pass": true,
      "evidence": "Own run of the OUTER-repo runner: `powershell -NoProfile -File F:\\moonbit-hof-rs\\godot-mcp\\tools\\run_gates.ps1 -Root F:\\moonbit-hof-rs\\godot-mcp -Tag task153-accept -RunGates -OutDir ...\\task153-accept\\gates`, CWD=F:\\moonbit-hof-rs\\godot-mcp, process exit code 0. summary.txt: g01..g10 exit=0 (ten lines). g01 test cases 160|160 passed|0 failed; g02 1586|1586 passed|0 failed; g03 'TOOL-GROUPS CHECK PASS BYTES 5681 SHA256 b83d79d3e3d080ce460b61ca99a46a126d6a6c45eb3d51d7977a52a991b7fbc7'; g04 '3/3 checks passed', editor port=9888 tools=154, game port=9889 tools=73, contract=177, guard_user_port_9877 pid_before=-1 pid_after=-1; g05 PASS lines=30 FAIL lines=0 and 'RESULT: PASS (all checks green)'; g06 'TAUTOLOGY CHECK PASS'; g07 'PROBES: 10/10'; g08 BUCKET UNCLASSIFIED=0, total=126; g09 ANCHOR_STRUCTURAL_EQUIVALENT RED_COUNT=0 'RESULT PASS'; g10 '22/22 cases passed'. No engine rebuild was performed."
    },
    {
      "id": "G09.GUARDRAILS",
      "pass": true,
      "evidence": "Criterion in force in the untouched script: PASS = ANCHOR_EQUAL or ANCHOR_STRUCTURAL_EQUIVALENT (red==0); actual verdict ANCHOR_STRUCTURAL_EQUIVALENT with RED_COUNT=0. (1) `git diff --name-only --no-renames 035edfce7f..HEAD` = 4 files (MCP-SERVER-HANDOVER.md, rename-baseline-tools-list.json, docs/scripts/check_rename_map.py, scripts/gen_renamed_contract.py); each classified by the judge's OWN dot-sourced Get-McpAnchorFileKind -> SAFE/SAFE/SAFE/SAFE, and the TASK-153 range bef4be0407..HEAD -> 1 file -> SAFE. No compile input. (2) `git diff --name-only bef4be0407..HEAD -- <all 37 compile extensions + 6 compile names>` = 0 bytes. (3) `git diff --stat bef4be0407..HEAD -- modules/mcp_server/scripts/check_engine_anchor.ps1 modules/mcp_server/scripts/check_hardcoded_counts.py` = empty; outer repo `git status --porcelain -- godot-mcp/tools/run_gates.ps1` and `git diff --stat --` both empty and its blob b3c5ea655b949836f7dc640fc54c255bc526cb16 == HEAD blob."
    },
    {
      "id": "PROVENANCE",
      "pass": true,
      "evidence": "Every number in the new comment block at gen_renamed_contract.py:1801-1829 is independently checkable and checks out. Baseline: bytes=48749, cr=0, lf=0, sha256=8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54, tools=174, unique=174; blob 543b49b2583bf06c3aba2a320649a31eda272e3e == HEAD blob. `git -C F:\\moonbit-hof-rs cat-file -t 543b49b2...` -> blob, and `git -C F:\\moonbit-hof-rs cat-file blob 543b49b2... | cmp - <engine baseline>` -> exit 0 (CMP_IDENTICAL). `git -C F:\\moonbit-hof-rs rev-parse 'db2eed7^:tests/fixtures/mcp/tools_list.json'` -> 543b49b2... (db2eed7 = 'tools: migrate to the 177-tool four-channel contract ... (DR-42)'). File added in engine commit 069a2e2ea8ca0af76e704bd94b81bc742b171174 at 2026-09-29T08:48:49+08:00. Date: '2026-09-29' is present in check_rename_map.py at bef4be0407 (:95), that file's last commits are bef4be0407 08:55:58 and e1fbc8ec7f 08:52:44, while the TASK-153 commit is 2026-09-29T09:13:33+08:00 and the machine clock read 2026-09-29T09:25:11+08:00. So the recorded date is genuinely TASK-152's, predates this task, and the comment's own claim ('TASK-153 gathered nothing and asserts no date of its own') is consistent with the history. OLD_CONTRACT_SHA256 is byte-unchanged in the diff."
    },
    {
      "id": "ARTIFACT.UNTOUCHED",
      "pass": true,
      "evidence": "modules/mcp_server/docs/tools_list.renamed.json: bytes=154272, sha256=fd00c75e5174ec923d5a91c0323afa0804f523b385eae3d4f78d8c71e1f895df, blob 3b1b191dc42f1cec8bc7cdd3504247c935b52f5e — identical to `git rev-parse bef4be0407:<path>` and `git show bef4be0407:<path> | sha256sum`. It was NOT regenerated (a regeneration would be 154311 B with an engine-local generated_from). `_meta.generated_from` at :3939 still names the hof-rs fixture; `git log -S\"generated_from\"` over that path returns exactly one commit, 54200f0d77aa2f79f4ecb75c6c1ea7826ebae352 (2026-09-26T10:18:48+08:00), and `git show 54200f0d:<path> | grep generated_from` already shows the same hof-rs literal => historical fact predating TASK-153 by three days."
    },
    {
      "id": "SCRIPTS.SCOPE",
      "pass": true,
      "evidence": "modules/mcp_server/scripts/mcp029_clear_default_evidence.ps1:62 and modules/mcp_server/scripts/mcp032_d3_d4_d6_evidence.ps1:63 both hold the executable `$OldFixture = 'F:\\moonbit-hof-rs\\tests\\fixtures\\mcp\\tools_list.json'` (mcp029 uses it with Test-Path at :64). mcp032 also holds `$UserPort = 9877` at :69 (used at :295 and :515). Neither script is on the ten-gate path: `grep -n 'mcp029|mcp032' F:\\moonbit-hof-rs\\godot-mcp\\tools\\run_gates.ps1` exits 1 (nothing) and the same grep over modules/mcp_server/scripts/accept_m1.ps1 (gate g10) exits 1. An acceptor-authored scan of every script the ten banner commands actually run found 0 executable cross-repo references on the whole gate path."
    },
    {
      "id": "GUARDS",
      "pass": true,
      "evidence": "No push: origin/feature/mcp-server-module-rebuild = bef4be04077e855918013355b03ce7a6795a910a, HEAD = 28432f859f, `git merge-base --is-ancestor 28432f859f origin/...` exit 1, `git branch -r --contains 28432f859f` empty, reflog -20 has no push/fetch/pull line, `git rev-list --left-right --count HEAD...@{u}` = 1 0, `git diff --cached --stat` empty. hof-rs side untouched: tests/fixtures/mcp/tools_list.json bytes=71481 sha256=50c5fb4204ee5b957b017eb994e7f7bd73f9b299e6aa9471d5cf11683e067da0 mtime=2026-09-28 22:37:34 (predates the task), and the only hof-rs working-tree entries are my own untracked recovery/work/task153-accept/** files. No new dependency: no import/from line added, removed or changed by the task range, and no requirements/pyproject file is in the diff. No existing check deleted or weakened: `git diff --diff-filter=D --name-only bef4be0407..HEAD` empty, the whole range is one modified file, the three named guard files have zero diff, g05 still reports 30 PASS/0 FAIL, and OLD_CONTRACT_SHA256 is unchanged. Ports: 9877/9888/9889 had 0 listeners before the gates and 0 listeners after (read-only Get-NetTCPConnection -State Listen); port 9877 was never bound, connected to or attacked, and mcp032_d3_d4_d6_evidence.ps1 was never executed."
    }
  ],
  "defects": [
    {
      "id": "DEF-1",
      "severity": "info",
      "what": "Task-book line-cite imprecision only (no code defect): TASK-153-ACCEPT.md section 2.8 groups 'the latter also contains $UserPort=9877' under the citation mcp032...:63, but the cross-repo literal is at :63 and $UserPort = 9877 is at :69. D229 makes the same statement without a line number, so nothing delivered is wrong.",
      "reproduction": "sed -n '63p;69p' modules/mcp_server/scripts/mcp032_d3_d4_d6_evidence.ps1"
    },
    {
      "id": "DEF-2",
      "severity": "info",
      "what": "Disclosed residual coupling, not a TASK-153 defect: modules/mcp_server/docs/tools_list.renamed.json:3939 keeps `_meta.generated_from` pointing at the hof-rs fixture, and two legacy evidence scripts keep executable cross-repo inputs (one on port 9877). D229 already fixed the statement boundary ('the generator/gate line is decoupled; the module as a whole is not') and opened TASK-154; TASK-153's own goal is met.",
      "reproduction": "sed -n '3939p' modules/mcp_server/docs/tools_list.renamed.json; sed -n '62p' modules/mcp_server/scripts/mcp029_clear_default_evidence.ps1; sed -n '63p;69p' modules/mcp_server/scripts/mcp032_d3_d4_d6_evidence.ps1"
    }
  ],
  "risks": [
    "docs/tools_list.renamed.json is a frozen artifact anchored by g04 (contract byte-for-byte 3/3), g05 (B0/B1/B2, CONTRACT bytes=154272 sha256=fd00c75e...) and the TASK-060 provenance chain, while the current generator now emits 154311 B (its _meta.generated_from would become the engine path, +39 B). D229 forbids regenerating it pending a full re-verification; that divergence between 'the artifact on disk' and 'what the generator would write today' remains open.",
    "g09 passes as ANCHOR_STRUCTURAL_EQUIVALENT, not ANCHOR_EQUAL, so its PASS depends entirely on the three reviewer-side guardrails. They hold today (verified above), but nothing in check_engine_anchor.ps1 or run_gates.ps1 encodes guardrails (1) and (2) - they are re-derived by hand each time. A future batch could pass g09 while violating them unless a reviewer keeps checking.",
    "The engine build is not bit-reproducible and no rebuild was done, so binary freshness rests on --version (4.8.dev.mono.custom_build.035edfce7) + unchanged test counts (g01 160/160, g02 1586/1586) + the live-endpoint gates (g04/g10). That is the intended criterion for a non-compile-input change, but it cannot detect a stale binary whose tests happen to still pass.",
    "mcp032_d3_d4_d6_evidence.ps1 hardcodes $UserPort = 9877 and reads the hof-rs fixture at its CURRENT state (71481 B / 177 tools), while its historical evidence was captured against 48749 B / 174 tools. Running it later would silently compare against different bytes. Not exercised here (9877 is forbidden), so this is inferred from code reading, not measured."
  ],
  "unverified": [
    "I did not run mcp029_clear_default_evidence.ps1 or mcp032_d3_d4_d6_evidence.ps1 (the latter would occupy port 9877), so their runtime behaviour is unmeasured.",
    "I did not rebuild the engine, so an ANCHOR_EQUAL verdict after a rebuild is untested - deliberately, since a rebuild without new code would only make the binary claim HEAD.",
    "Whether the implementer actually executed the exact historical command recorded in the comment ('git -C F:\\moonbit-hof-rs cat-file blob 543b49b2...') cannot be proven from the repository. What I could and did prove: the blob exists in the hof-rs object store and its bytes are identical to the engine baseline, so the recorded method is correct and reproducible.",
    "I did not audit the hof-rs/engine documentation corpus for every hof-rs mention; docs-level provenance mentions (README, B0-BRIEF, TOOL-NAMING, reports/**) are outside this task's decoupling goal."
  ]
}
```

### 1.1 真实命令与退出码（本报告全部结论的命令级依据）

工作目录除注明外均为引擎仓根 `F:\moonbit-hof-rs\godot-mcp\godot`。

| # | 命令 | 退出码 |
|---|---|---|
| 1 | `git status --porcelain` / `git rev-parse HEAD` / `git rev-parse '@{u}'` / `git rev-list --left-right --count HEAD...@{u}'` | 0（`<空>` / `28432f859f...` / `bef4be0407...` / `1  0`） |
| 2 | `python recovery/work/task153-accept/my_ast_scan.py` | 0（`SCAN_EXIT=0`） |
| 3 | `cd /c && python F:\...\gen_renamed_contract.py --out ...\out_from_C.json` | 0 |
| 4 | `python ...\gen_pre_bef4be0407.py --old-contract <引擎基准> --map <引擎映射> --out ...\out_pre_explicit.json` | 0 |
| 5 | `cmp out_pre_explicit.json out_from_C.json` | 0 |
| 6 | `bash ...\run_plant.sh A1` / `A2` / `B1` / `B2` | 植入脚本 0，**生成器各 1**，恢复 0 |
| 7 | `powershell -NoProfile -File F:\...\godot-mcp\tools\run_gates.ps1 -Root F:\...\godot-mcp -Tag task153-accept -RunGates -OutDir ...\gates`（CWD 外层仓） | 0（十门子进程 `GATE_EXIT` 全 0） |
| 8 | `git diff --name-only bef4be0407..HEAD -- <37 扩展名 + 6 文件名>` | 0（输出 0 字节） |
| 9 | `git -C F:\moonbit-hof-rs cat-file blob 543b49b2... \| cmp - <基准>` | 0（`CMP_IDENTICAL`） |
| 10 | `python ...\gatepath_scan.py`（十门路径可执行跨仓引用扫描） | 0（`EXECUTABLE ... : 0`） |
| 11 | `Get-NetTCPConnection -State Listen` 过滤 9877/9888/9889（门前后各一次） | 各 0，计数 0/0 |
| 12 | `git hash-object` 四文件 vs `git rev-parse HEAD:<path>`（验收收尾） | 0（四对全 `EQUAL=True`，`status` 0 行，`diff --stat` 0 行） |

---

## 2. 逐项核对表

| 验收项 | 判据 | 结论 | 决定性证据（自产） |
|---|---|---|---|
| 1 去耦 | `DEFAULT_OLD_CONTRACT` 指向引擎内；非注释处无 hof-rs 路径/字面量；无 CWD 依赖 | **PASS** | grep 6 命中全为 `#` 行；AST 可执行字面量 0、`open()` 4 处全变量、导入期解析落在引擎 docs；从 `C:\` 跑 exit 0 且产物与引擎根跑 `cmp` 0 |
| 2 行为保持 | 改前脚本 + 显式同一基准 vs 改后脚本全默认，逐字节相同 | **PASS** | 两者均 154311 B / `8461b6ee…5373`，`cmp` 0（详见 §4） |
| 3 非空洞性 | 基准/映射各植入一个真实差异 ⇒ 非零退出（非警告）；逐字节恢复 | **PASS** | A1/A2/B1/B2 全 `GEN_EXIT=1` + `OUTPUT_WRITTEN=False`；四次恢复 `status`/`diff --stat` 双空 + `hash-object` == HEAD blob |
| 4 十道门 | 10/10 exit 0；g05 30/0；g01 160、g02 1586、g04 3/3(154/73/177)、g07 10/10、g08 UNCLASSIFIED=0、g10 22/22 | **PASS** | 自跑 `run_gates.ps1 -RunGates`，`summary.txt` 十行 exit=0；各门计数见 §1 `GATES.10` |
| 5 g09 三护栏 | ①区间 diff 全 docs/scripts 无编译输入 ②编译输入 diff 空 ③三个判据/门脚本零 diff | **PASS** | 用**判据脚本自己的** `Get-McpAnchorFileKind` 分类 4+1 文件全 SAFE；编译输入 pathspec diff 0 字节；两个引擎文件 `diff --stat` 空 + 外层 `run_gates.ps1` blob `b3c5ea65…` == HEAD |
| 6 溯源真实性 | 路径/字节/条数/sha256/blob/日期可核，无编造 | **PASS** | 数值全中；blob 在 hof-rs 对象库存在且 `cmp` 一致；`db2eed7^` 夹具 blob 正是该 id；日期在 `bef4be0407` 已提交且早于本任务提交 |
| 7 D229-1 | 未重生成冻结工件；`_meta.generated_from` 为历史事实 | **PASS** | 工件 blob/sha/字节与 `bef4be0407` 完全相同；`-S\"generated_from\"` 仅 `54200f0d77`（2026-09-26），该提交里已是 hof-rs 路径 |
| 8 D229-2 | 两个取证脚本确有跨仓可执行引用；后者含 9877；均不在十门路径 | **PASS** | `mcp029:62`、`mcp032:63`（`$UserPort=9877` 在 `:69`）；`run_gates.ps1`/`accept_m1.ps1` grep 均 exit 1 |
| 9 禁区自查 | 9877/9888/9889 前后无监听；未 push；hof-rs 侧零改动；无新依赖；无检查被删/放宽 | **PASS** | 端口计数前后均 0；origin 仍 `bef4be0407` 且不含被测提交、reflog 无网络操作、无 staged；夹具 `50c5fb42…`/71481 B/mtime 未变；无 import 变更；区间无删除 |

---

## 3. 反例清单（我自己设计并执行的对抗性实验）

> 纪律：§2.3 的植入是**唯一**被允许的改动；四次植入全部 `git checkout --` 逐字节恢复，并每次在**植入前**和
> **恢复后**各自打印 `git status --porcelain`、`git diff --stat`、四文件 `git hash-object` vs HEAD blob。
> 移植脚本 `recovery/work/task153-accept/my_plants.py`（自写），每个植入在 needle 出现次数 ≠ 1 时**拒绝写入**。

| 反例 | 植入内容（与实现者/TASK-152 **不同**） | 目标 | 实际结果 | 恢复证明 |
|---|---|---|---|---|
| **A1** | 引擎基准里把两个**等长**名字互换：`"name":"open_scene"` ↔ `"name":"stop_scene"`。JSON 仍合法、174 条仍唯一、**字节数 48749 不变**（大小启发式看不见） | 基准出现真实差异 ⇒ 必须红 | `FATAL: old contract sha256 3d2b08ee671f7ef1… != the frozen 8f8051c4c0f89410…`；`GEN_EXIT=1`；`OUTPUT_WRITTEN=False` | `status` 空、`diff --stat` 空、`hash-object` `543b49b2…` == HEAD blob、sha 回 `8f8051c4…` |
| **A2** | 引擎基准里**整条删除** `tilemap_get_cell`（先证明 `json.dumps(separators=(',',':'))` 与原文件**逐字节无损**，再删）：48749 → 48470 B、174 → **173** 条、JSON 合法 | 结构性真实差异 ⇒ 必须红 | `FATAL: old contract sha256 5ebbad35c8068dcd… != the frozen 8f8051c4…`；`GEN_EXIT=1`；`OUTPUT_WRITTEN=False` | 同上，sha 回 `8f8051c4…` |
| **B1** | 改名表里让 `search_in_files` 与 `search_files` **共用一个 `new_name`**：`project_search_file_contents` → `project_search_file_names`。二者 `channel=project`、`verb=search` **一致**，所以 L1/L2/L3 全部仍通过，红的**只能**是唯一性自检（绕过基准哈希闸） | 错映射 ⇒ 必须红 | `FATAL: duplicate new names in the output: ['project_search_file_names']`；`GEN_EXIT=1`；`OUTPUT_WRITTEN=False`（70917 → 70914 B） | `status` 空、`diff --stat` 空、`hash-object` `743bc79c…` == HEAD blob |
| **B2** | 改名表里把 `project_get_info` → `project_read_info`，条目里 `verb` 仍为 `get`（`read` 在闭集内，故 L2 不拦，专打 **L3**） | 错映射 ⇒ 必须红 | `FATAL: L3 declared verb 'get' != parsed 'read': project_read_info`；`GEN_EXIT=1`；`OUTPUT_WRITTEN=False`（70917 → 70918 B） | 同上，`hash-object` `743bc79c…` == HEAD blob |

**附加反例（正向对照）**：把 `--old-contract` 显式指回 **hof-rs 当前夹具**（只读）⇒ `GEN_EXIT=1`，
`FATAL: old contract sha256 50c5fb4204ee5b95… != the frozen 8f8051c4…`。这同时说明：①CLI 覆盖仍然被尊重；
②新默认值确实是**引擎内**件（否则默认不会产出旧基准的 sha 校验失败/成功对比）。

**我自己的工具踩过的一个坑（如实披露，避免被读成实现缺陷）**：`A2` 与 `B1` 的**第一版**脚本因自身 bug
在写文件前 `REFUSED` 退出，而我的 driver 仍继续跑了生成器 —— 于是生成器在**未被植入**的原始输入上正常
`exit 0` 并写出了 scratch 产物。这是我这一侧的假绿，不是实现的问题。我修好脚本（A2 改为可自证的紧凑
序列化往返、B1 允许与既有 `new_name` 有意冲突）并**完整重跑**，上表记录的是修正后的结果；那次误产出的
scratch 文件已删除，最终 `git status` 四文件全干净。

---

## 4. 对「行为逐字节相同」的独立结论

**结论：成立。改动只是把默认输入来源从仓外换成仓内，产物字节没有变化。**

我自己复算（不看实现者的数字）：

```
改前生成器 git show bef4be0407:modules/mcp_server/scripts/gen_renamed_contract.py
        -> recovery/work/task153-accept/gen_pre_bef4be0407.py
        -> sha256 35bfd8752abda2b574bdc0f675ab3b944c1639f74b2121cad346365d238494a1
        -> 其 :1800 = r"F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json"（无 DOCS 常量）

改前 + 显式引擎基准/映射 --out out_pre_explicit.json  : exit 0, 154311 B, 8461b6eee63fc17b6547a2640b40e3383f5618f22658611aa8c2e17b704e5373
改后 + 全默认      --out out_from_C.json             : exit 0, 154311 B, 8461b6eee63fc17b6547a2640b40e3383f5618f22658611aa8c2e17b704e5373
cmp out_pre_explicit.json out_from_C.json            : exit 0
改后 + 全默认（引擎根）--out out_from_engine_root.json : exit 0, 同上 sha256
cmp out_from_C.json out_from_engine_root.json        : exit 0
```

与实现者报告（154311 B / `8461b6ee…e5373`）**逐字符一致**，但这是我自己跑出来的两条产物之间的比较，
不是转述。另外，`git diff bef4be0407..HEAD` 的全部内容我已逐行读过：只有 `DOCS` 新增、29 行 `#` 注释、
以及三行默认值的**等价重写**（`os.path.join(MODULE_ROOT,"docs",X)` → `os.path.join(DOCS,X)`，
`DOCS = os.path.join(MODULE_ROOT,"docs")`，字符串值因此逐字相同）；`OLD_CONTRACT_SHA256` 一个字节未动，
断言表达式一个未改，无 import 变化。

**注意边界（避免这句结论被过度延伸）**：这里说的是「同一基准字节 ⇒ 同一产物字节」。改动**确实**改变了
「不传 `--old-contract` 时的默认行为」——改前默认指向 hof-rs 现夹具（71481 B / `50c5fb42…`）会被冻结 sha
拦下并 `exit 1`，改后默认指向引擎基准而成功。这正是本任务的目标（换输入来源），不是行为偷改。

---

## 5. 未验证项与理由

1. **未运行 `mcp029` / `mcp032`**：`mcp032` 硬编码 `$UserPort = 9877`，任务书明令绝不占用/探测 9877，
   因此我不能执行它；`mcp029` 与 `mcp032` 属同族历史取证件，随 `mcp032` 一并留白。它们的跨仓引用是
   **读代码**得到的事实，运行期表现未测。
2. **未重建引擎**：本任务范围为非编译输入（已用 pathspec diff 证明），重建只会让二进制自报锚点变成 HEAD
   而不会多一行新代码；因此「重建后 `g09` 是否为 `ANCHOR_EQUAL`」**未测**，且我有意不去制造那种假绿。
3. **未能证明实现者当年确实执行了注释里记的那条命令**：仓库无法证明「某条命令被跑过」。我能证明的更强
   事实是：`543b49b2…` 确在 hof-rs 对象库中，且其字节与引擎基准 `cmp` 完全一致 ⇒ 记录的方法正确且可复现。
4. **未逐文件审计全部 hof-rs 文本提及**：`modules/mcp_server/**` 里有大量 **docs/** 与注释级提及
   （README、B0-BRIEF、TOOL-NAMING、reports/** 等，共 51 个文件命中）。它们是溯源文本，不在本任务
   「生成器/门这一线去耦」的目标内；我只对**十门实际执行的文件**做了可执行/注释分类（结果：可执行 0）。

---

## 6. 我没有独立复核的部分

* **实现者自产证据本身**：`recovery/work/task153/**` 里的脚本与输出，我只把它当作线索；上面每一条结论
  都由我在 `recovery/work/task153-accept/` 下重新生成。我没有逐行审计实现者的 `exp1/exp2/ast_scan_gen.py`。
* **TASK-152 的改动**（`check_rename_map.py`、`MCP-SERVER-HANDOVER.md`、基准件引入）：除它落在
  `035edfce7..HEAD` 锚点区间、被我用判据脚本自己的分类器判为 SAFE 之外，我没有重做 TASK-152 的验收
  （那是 `TASK-152-ACCEPTANCE.md` 的范围，且 D228 已独立验收通过）。
* **决策内容本身**：D227–D229 的三条裁决（尤其「不重生成冻结工件」与「把 `mcp029`/`mcp032` 留到
  TASK-154」）是决策者权限内的取舍，我核验的是**它们的事实前提是否成立**，不是它们是否明智。
* **门脚本内部逻辑**：`run_gates.ps1` / `check_engine_anchor.ps1` / `check_hardcoded_counts.py` 我读了、
  确认零 diff 并按它们自己的判据复算，但没有审计这三个文件在**历次**修改中的强度演化（超出本任务区间）。

---

## 7. 给下一批的建议（我没有改任何代码）

1. **`g09` 的附加护栏应当机器化**：护栏 ①（区间 diff 全是非编译输入）与 ②（编译输入 diff 为空）目前是
   **人工复核项**，判据脚本只实现「STRUCTURAL_EQUIVALENT + RED_COUNT=0」。建议让 `run_gates.ps1`/判据脚本
   在 `-RunGates` 路径下把 `git diff <基线 TASK 起点>..HEAD -- <编译输入>` 的空性一并打印/断言，否则
   下一个验收者仍要靠人记得手算。（**不要**为了这条去改判据本身放宽阈值。）
2. **`docs/tools_list.renamed.json` 与生成器现已产出的字节不一致（154272 vs 154311）**，差异只在
   `_meta.generated_from`。D229 已决定不在无完整重验证时重生成。建议 TASK-154（或其后单独任务）按
   D229 的处置执行：重生成前必须同时跑 `g04` 的契约逐字 3/3、`g05` 的 B0/B1/B2 与 `mcp052/mcp053_contract_diff.py`，
   并把「`generated_from` 已刷新为引擎内路径」写进产物旁的溯源说明，避免后人据该字段误判生成器仍在跨仓。
3. **`mcp029`/`mcp032` 的处置建议保持 D229 的方向但明确语义**：这两个脚本是**历史取证件**，它们
   `$OldFixture` 读的是「当年那次取证的夹具」。若改成引擎内基准，则与它们复核的历史字节（48749/174）不符；
   更安全的做法是**参数化**（默认仍指当年的冻结基准或引擎内基准并显式打印读了哪一份），并把 `mcp032` 的
   `$UserPort = 9877` 改为可传参的测试端口或加显式拒绝运行的守卫 —— 不要在没有替代端口的情况下直接跑它。
4. **任务书模板**：`run_gates.ps1` 在外层仓这一事实已在 D229 记录；建议继续在引擎任务书里写**绝对路径**
   （本任务书 `TASK-153-ACCEPT.md` §2.4 已经这么做了，故本次未踩坑）。
5. **不要为「让 g09 显示 ANCHOR_EQUAL」而重建**：本任务已用三条护栏证明非编译改动下的 STRUCTURAL_EQUIVALENT
   是合规判据；重建只会引入不位级可复现的噪音。

---

## 附：本验收会话的产物清单（可逐条复核）

`godot-mcp/recovery/work/task153-accept/`：
`my_ast_scan.py`、`probe_baseline.py` + `.out.txt`、`pick_targets.py` + `.out.txt`、`my_plants.py`、
`run_plant.sh`、`A1-full.txt`、`A2-full.txt`、`B1-full.txt`、`B2-full.txt`、`gen_pre_bef4be0407.py`、
`pre_explicit.log`、`out_pre_explicit.json`、`out_from_C.json`、`out_from_engine_root.json`、
`guard2.txt`、`gatepath_scan.py` + `.out.txt`、`gates/summary.txt`、`gates/g01..g10.{stdout,stderr}.txt`。
