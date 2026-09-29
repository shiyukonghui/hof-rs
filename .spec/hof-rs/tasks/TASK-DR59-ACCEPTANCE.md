# TASK-DR59-ACCEPTANCE — DR-59（确定性证据按轮次隔离）独立验收

> **独立验收子代理**。未继承实现者或调度者的任何结论；下列所有证据均由本会话**自己运行**得到。
> 判据：`.spec/hof-rs/tasks/TASK-DR59.md`；`DECISIONS.md` D240/D244/D245/D246；验收任务书
> `.spec/hof-rs/tasks/TASK-DR59-ACCEPT.md`。实现者报告（**只当线索**）：`TASK-DR59-REPORT.md`。
> **离线**：未启动 Godot、未碰任何端口、未联网、未调模型端点；未 push、未 stage、未改写历史。

---

## 0. 复核对象的冻结与一处过程观察（必须先读）

验收期间工作区**不是静止的**，故我把复核对象钉在不可变的代码提交上：

| 提交 | 时间 | 内容 |
|---|---|---|
| `ea1cf07` | 19:27:16 | 批次起点，`origin/master` 仍指向它 |
| `91a28f8` | 19:42:09 | 红测试（只加 `tests/evidence_isolation.rs`，161 行） |
| `db145b5` | 19:42:19 | 实现（`godot.rs`/`hygiene.rs`/`run_loop.rs`） |
| `7fab86b` | 19:56:26 | 两轮复现件（测试文件 +66 行） |
| `6e4a6a2` | 20:10:15 | 报告（**验收期间被 implementer `--amend` 两次**：`1990df9`→`d240e75`→`6e4a6a2`） |
| `944770f` | 20:21:05 | **调度者（父代理）** 的 D247 文档提交（`DECISIONS.md` +34、本任务书 `TASK-DR59-ACCEPT.md` 入库） |

- **代码在 `7fab86b` 之后未再变动**：`git diff --stat 7fab86b..944770f -- src tests` **输出为空**。
  故本报告的代码判据 = `7fab86b` 的代码状态 = 当前 HEAD 的代码状态。
- `git diff ea1cf07..HEAD -- DECISIONS.md` 只命中 `944770f`（**父代理**的 D247），**不是**实现者改的；
  实现者 3 个提交只动 `src/{adapter/godot.rs,runtime/hygiene.rs,runtime/run_loop.rs}` + 新增 `tests/evidence_isolation.rs`。
- 报告文件在验收期间被 amend 两次（reflog 实证）：`1990df9`(20:09:10) → `d240e75`(amend 20:09:58)
  → `6e4a6a2`(amend 20:10:15)。我只以 `6e4a6a2`/工作树最终内容为准。

---

## 1. 结构化结论（本报告 §1）

```json
{
  "verdict": "pass",
  "acceptance_target": {
    "code_commits": ["91a28f8", "db145b5", "7fab86b"],
    "docs_commits_by_dispatcher": ["6e4a6a2", "944770f"],
    "head_at_verdict": "944770fbe6de63518568f5285ba15f52321258d1",
    "code_frozen": true
  },
  "criteria": [
    {
      "id": "SUITE",
      "pass": true,
      "evidence": "`cargo test --offline` run from F:\\moonbit-hof-rs: 38 targets, aggregate `targets=38 passed=359 failed=0 ignored=7`, `EXIT=0` (log /tmp/i1_suite.txt, tail: `running 0 tests / test result: ok. 0 passed... / EXIT=0`). +6 delta derived without a baseline rerun: `git diff ea1cf07..HEAD -- tests/` touches ONLY `A tests/evidence_isolation.rs`; added test attributes: `git diff ea1cf07..HEAD -- tests/ | grep -c '^+#\\[tokio::test\\]'` = 3 and hygiene.rs adds exactly 3 `#[test]` (lines +98,+127,+146) => 353+6=359. `grep -c '^+.*#\\[ignore'` over the whole batch diff = 0; `git diff ea1cf07..HEAD -- tests/godot_smoke.rs` empty and blob unchanged (`ae9093661cf989322cbac4e9832572dddd0174a4` both at ea1cf07 and HEAD); 8 `#[ignore` occurrences in tree = 7 attributes + 1 doc comment = 7 ignored. Zero `^warning` lines in the suite log."
    },
    {
      "id": "ISOLATION_REAL",
      "pass": true,
      "evidence": "Mechanism: `src/runtime/run_loop.rs:353` calls `hygiene::quarantine_previous_evidence(&workspace)` AFTER `adapter.initialize` (:337) and BEFORE the `A_0` snapshot (:413) and any role (Planner :512, Developer :709, Tester :1055); `grep -rn quarantine_previous_evidence src/` shows the only call site is run_loop.rs:353. `hygiene.rs:363-388` renames `<ws>/.hoh/deterministic` to `<ws>/.hoh/deterministic.stale-<unixsecs>[-attempt]`. The prompt-named read paths are all `.hoh/deterministic/**` (`src/prompts/mod.rs:56`, `tester.md:9-10,23-27`, `skills/godot-testing.md:7-12`, `godot.rs:3447-3451`); no prompt globs `.hoh`. MY OWN construction (scratch project outside the repo, `%LOCALAPPDATA%\\Temp\\dr59-accept\\probe`, test `dr59_accept_probe`, binary run from the repo root): `PROBE-A live keys in developer view: []` and `PROBE-B round2 live keys in developer view: []`, `EXIT=0` (probe-run2.txt)."
    },
    {
      "id": "QUARANTINE_NOT_DELETE",
      "pass": true,
      "evidence": "Implementation uses `std::fs::rename(&live, &target)?` (`src/runtime/hygiene.rs:376`) and, when all 64 `.stale-` names are taken, `anyhow::bail!` (`:384`) instead of falling back to deletion. MY OWN disk-level measurement (not the harness snapshot): probe A asserts `std::fs::read_to_string(<quarantine>/battery.json) == seeded bytes` and the same for `raw/input_channel_probe.json`; probe B compares the WHOLE quarantined directory file-by-file with round one's evidence and asserts equality: `PROBE-B quarantined files (5): [battery.json, build.json, deterministic.json, deterministic.log, record-00.json]` == `PROBE-B round1 evidence on disk (5 files)`, `EXIT=0`. Independent disproof that the assertions are not vacuous: plant P2 (below) turns the preservation assertions red."
    },
    {
      "id": "NON_VACUITY",
      "pass": true,
      "evidence": "MY OWN two plants, production code only, tests untouched. P1: `hygiene.rs::should_quarantine` body -> `let _ = live; false`; `cargo test --offline --test evidence_isolation` => `EXIT=101`, `test result: FAILED. 1 passed; 2 failed`, panics at `tests/evidence_isolation.rs:113` (`the previous round's evidence is still on the live read path (.hoh/deterministic/): [\".hoh/deterministic/battery.json\", \".hoh/deterministic/raw/input_channel_probe.json\"]`) and `:214` (5 round-one files). P2: `std::fs::rename(&live,&target)` -> `std::fs::remove_dir_all(&live)`; `--test evidence_isolation` => `EXIT=101`, red at `:121` (`was destroyed instead of being moved aside`) and `:219`; `--lib quarantine` => `EXIT=101`, red at `hygiene.rs:593` and `:631`. Both restored byte-exactly (see §3)."
    },
    {
      "id": "TWO_ROUND_REPLAY",
      "pass": true,
      "evidence": "Implementer's `tests/evidence_isolation.rs::round_two_cannot_read_round_one_evidence` (file:191-226) uses `tempfile::tempdir()` and `FakeAdapter` (no `.workspace/mario`); `run_round` (file:170-189) calls `hof_rs::runtime::run_loop::run(&orch,&spec,run_id)` with `run-1` then `run-2` over one workspace, asserts round one really left `.hoh/deterministic/build.json` before round two. MY OWN independent replay (probe B) reproduces the same shape: `PROBE-B round1 evidence on disk (5 files)` (precondition), then `PROBE-B quarantine dirs: [...deterministic.stale-1790684848]` and byte-equality of all 5 files; `EXIT=0`. `.workspace/mario` was never touched (probe uses `%TEMP%\\.tmpXXXX\\workspace`; paths in probe-run2.txt)."
    },
    {
      "id": "GUARDS",
      "pass": true,
      "evidence": "`.workspace/mario/**`: `git ls-files .workspace`=0 (outer repo does not track it), 259 files, newest mtime `2026-09-29 14:32:28` < batch start `19:42:09`; digest (PS scheme, §2 note) `files=259 digest=4e494547416b2e87ba025d686afef9447d4f92c027917d1790e6fc9deaeaa84a`. `runs/**`: `git ls-files runs`=0, newest mtime `2026-09-29 14:44:16` < batch start, `runs` all = `files=5147 digest=01ff775e36935d3d92dab6919fe030389a8ff53483c52e87288ad711ec840dc3` reproduced with PowerShell `Sort-Object` (exactly the value recorded by DR-57), and `runs/smoke-t6` = `files=135 digest=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03` (exactly the DR-54/DR-57 value); `smoke-t7`=115 files. `PRD-mario.md` sha256 = `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`, untouched in range. Engine (nested repo, D242): `git ls-files godot-mcp`=6484 (>0 => pathspec matches), `git ls-files godot-mcp/godot`=0 (=> outer diff is a null judgment), `godot-mcp/godot` has its own `.git` and is ignored by `.gitignore:33`; `git -C godot-mcp/godot status --porcelain`=0 lines (both -uno and full), nested HEAD `fc63af77c33368c4a1bb839c95d19750554f63a3`, newest engine mtime `2026-09-29 10:37:38` < batch, `running_game_test_execution.cpp` sha256 `ece4ae63d445719b662a6e9ad99ba80bebba3ea3c94468094c7e9cb820ddff3f`. Deps: `git diff --stat ea1cf07..HEAD -- Cargo.toml Cargo.lock` empty. Not staged: `git diff --cached --stat` empty. Not pushed: `git rev-parse origin/master` = `ea1cf07a156ec45bc536ed9b028ac4e4350a3ad7`, `origin/master..master` = 5 commits (all DR-59 batch/docs, none pushed by me)."
    },
    {
      "id": "HONESTY",
      "pass": true,
      "evidence": "Adjudicated item by item in §6. Every measured claim I could check held (red-first structure, sentinel provenance, scope boundaries, guard numbers). Its two labelled inference blocks (I-1..I-3) are correctly labelled as inference. Its self-disclosures (§8.1 late unit tests, §8.3 PowerShell exit-code trap, §8.4 DR-49 refactor) are accurate or conservative; §8.3 I could not reproduce (§6.H-4). No inference was passed off as a measurement that I found."
    }
  ],
  "defects": [
    {
      "id": "DEF-1",
      "severity": "major",
      "what": "Residual reachability of the quarantined bytes: after the move, the previous round's evidence still sits INSIDE the role's cwd as `.hoh/deterministic.stale-<ts>/`, so any `ls .hoh` / wildcard read still reaches it (implementer's R-1). The guarantee delivered is that the prompt-named read path `.hoh/deterministic/**` is empty, not that the model can never reach the old bytes.",
      "reproduction": "My probe A: `PROBE-A stale marker still reachable from the Developer cwd at: [\".hoh/deterministic.stale-1790684826/battery.json\", \".hoh/deterministic.stale-1790684826/raw/input_channel_probe.json\"]` (probe-run2.txt:7). Not a fail per the task's own sanctioned `.stale-` option, but it must be a next-batch decision."
    },
    {
      "id": "DEF-2",
      "severity": "major",
      "what": "`.hoh/evidence/**` — the same class of previous-round leftovers — is NOT isolated: (a) it is on the live read path at round start (smoke-t7 pre-run inventory lists `.workspace/mario/.hoh/evidence/frame-00.png` = 4246 B, the smoke-t6 PNG), and (b) `view::copy_evidence` (`src/runtime/view.rs:103-136`) copies EVERY file under `.hoh/evidence` into the Tester's candidate view (it does not skip `.stale-` files). Task §1.1 explicitly asked for `.hoh/deterministic/**` AND its same-class reachable leftovers, so this is within the stated scope. The report discloses (a) as R-3 but does not measure (b).",
      "reproduce_measurement": "My probe A, with a previous-round PNG seeded, measured at the Tester invocation: `PROBE-A tester .hoh/evidence/frame-00.png present=true stale_bytes=true` and `PROBE-A MEASURED: tester sees previous-round PNG verbatim = true`; the same PNG is present in the Developer view (`PROBE-A .hoh/evidence/frame-00.png live in Developer view: true`). Meanwhile the deterministic area is clean in the Tester view: `PROBE-A tester deterministic keys carrying the stale marker: []`. Reporter's own code refs: `copy_evidence` is called at `run_loop.rs:991-995`; `invalidate_artifact` only invalidates the capture target (`godot.rs:1088`), after the Developer."
    },
    {
      "id": "DEF-3",
      "severity": "info",
      "what": "Behaviour-surface notes, all disclosed by the implementer: (i) a new `previous_evidence_quarantined` token + `warnings.log` line are emitted only when a move really happened, and the log line lands BEFORE the pre-existing `MCP_SCOPE_WARNING` line (`run_loop.rs:364` vs `:397`), so `warnings.log` order differs from `meta.warnings` order; (ii) `.hoh/deterministic.stale-*` directories accumulate one per round with no cleanup; (iii) exhausting the 64-name window aborts the whole round (`hygiene.rs:384` bail) rather than deleting — intentional and documented.",
      "reproduction": "Code inspection; suite is green so no test depends on the order."
    },
    {
      "id": "DEF-4",
      "severity": "info",
      "what": "Process observation, not an artifact defect: the report commit was amended twice during this acceptance (reflog 20:09:58 / 20:10:15) and the dispatcher committed D247 + this task brief at 20:21:05, so HEAD moved while the batch was being judged. The CODE commits `91a28f8/db145b5/7fab86b` were never rewritten, and `git diff --stat 7fab86b..HEAD -- src tests` is empty, so the verdict is unaffected.",
      "reproduction": "`git reflog -8 --date=iso`; `git diff --stat 7fab86b..HEAD -- src tests` => empty."
    }
  ],
  "risks": [
    "I-1 (implementer's, correctly labelled inference): that on the NEXT real round the Developer no longer carries the previous round's pid / 'the editor is not clean' / os error 10061 into context. Offline mechanism verified; real-machine behaviour not verified (no Godot run permitted).",
    "DEF-2's real-machine effect is unmeasured: whether the model actually read the previous round's evidence PNG. What I measured is that it is ON the read path (Developer cwd, Tester candidate view).",
    "The `.stale-` quarantine is only a naming/path isolation inside the same cwd; it relies on roles treating `.stale-` as 'superseded, do not trust'. Not enforced.",
    "Accumulated `.stale-` directories are never garbage-collected (unverified growth over many rounds)."
  ],
  "unverified": [
    "Baseline 353 passed / 0 failed / 7 ignored was NOT re-run on the pre-change tree (that would require rewriting the worktree/HEAD). It is corroborated by (a) D244/DR-57's independent record and (b) the +6 arithmetic from an otherwise byte-unchanged test corpus.",
    "I did not re-run the red history at commit `91a28f8`; I confirmed it structurally (2 `#[tokio::test]` present, 0 references to `quarantine_previous_evidence` in both `run_loop.rs` and `hygiene.rs` at that commit) and reproduced the same red shape myself via plant P1.",
    "I did not reproduce the implementer's §8.3 PowerShell-5.1 piped-exit-code trap: my minimal `powershell 5.1` and `pwsh 7` reproductions both reported the true native exit code (0). It is a self-disclosed tooling caveat about its own logs, and it is conservative (it says it did not trust the piped code).",
    "The implementer's raw scratch logs (claimed `%TEMP%\\dr59-scratch\\`, deleted) cannot be re-read; I verified only that `Test-Path %LOCALAPPDATA%\\Temp\\dr59-scratch` = False and `Test-Path %LOCALAPPDATA%\\Temp\\dr59-baseline.txt` = False.",
    "Real-machine quarantine naming and `.stale-` accumulation were not observed (requires a live round)."
  ]
}
```

**判决：`pass`。** 达标项：套件绿且 ignored 未增（**359/0/7，EXIT=0**）；确定性证据的**命名读取路径**在开轮后、任何角色之前为空（我自己构造复现）；修复是**移动而非删除**（磁盘级逐字节证明）；**自设两处植入**均使目标测试变红、并已逐字节回退（三法证明）；两轮复现件**真的跑了两轮**且不依赖 `.workspace/mario`；全部禁区未被动过。两个 major 级残留（DEF-1/DEF-2）不落在任务书 §3 的 fail 门槛上（确定性证据区的隔离成立、且 `.stale-` 移开正是任务书 §1.2 允许的第二种修法），但必须进下一批。

---

## 1.1 真实命令与退出码（关键几条）

```
$ cargo test --offline                 # 全部在 F:\moonbit-hof-rs 下运行
targets=38 passed=359 failed=0 ignored=7      # awk 聚合 grep -E '^test result:'
EXIT=0
$ cargo test --offline --test evidence_isolation
test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 32.16s
EXIT=0                                 # 植入回退后复跑

# 植入 P1（生产代码，测试未动）
$ cargo test --offline --test evidence_isolation
test result: FAILED. 1 passed; 2 failed; 0 ignored; 0 measured; 0 filtered out; finished in 32.62s
EXIT=101
# 植入 P2
$ cargo test --offline --test evidence_isolation   => EXIT=101 (red at :121, :219)
$ cargo test --offline --lib quarantine            => EXIT=101 (red at hygiene.rs:593, :631)

# 回退三法
$ git status --porcelain        => (空)
$ git diff --stat               => (空)
$ git hash-object src/runtime/hygiene.rs  => 56089ec2b157fe33fe4effa1e67831572c7bed3c
$ git rev-parse HEAD:src/runtime/hygiene.rs => 56089ec2b157fe33fe4effa1e67831572c7bed3c   (相等)
$ git hash-object src/runtime/run_loop.rs => e7678cc77e3abf0d5240514ec384c95eda851a2a
$ git rev-parse HEAD:src/runtime/run_loop.rs => e7678cc77e3abf0d5240514ec384c95eda851a2a   (相等)

# 我自己的构造（仓外 scratch 工程，二进制从仓根运行）
$ cargo test --offline --test dr59_accept_probe --no-run   => BUILD_EXIT=0
$ <probe bin> --nocapture --test-threads=1                 => test result: ok. 2 passed; RUN_EXIT=0
```

---

## 2. 逐项核对表

| # | 判据 | 判定 | 独立证据（自产） |
|---|---|---|---|
| 1 | 套件 `cargo test --offline` exit 0 | **pass** | 38 目标 / 359 passed / 0 failed / 7 ignored / `EXIT=0` |
| 2 | 与基线对照、`ignored` 未增 | **pass** | ignored=7（8 处 `#[ignore` = 7 属性 + 1 注释）；+6 = 新文件 3 个 `#[tokio::test]` + hygiene 3 个 `#[test]` |
| 3 | 无测试被删/放宽/加 `#[ignore]` | **pass** | `git diff ea1cf07..HEAD -- tests/` 只有 `A tests/evidence_isolation.rs`；批量 diff 中 `^+.*#\[ignore` 计数 0；`godot_smoke.rs` blob 前后一致 |
| 4 | 隔离**凭什么**成立 | **pass** | `run_loop.rs:353`（唯一调用点）在 `initialize`(:337) 之后、`A_0`(:413) 与所有角色之前；`hygiene.rs:363-388` 整目录 `rename`；提示词只点名 `.hoh/deterministic/**` |
| 5 | 自建“上一轮残留 + 新开轮”读不到 | **pass** | 自查工程 probe A：`live keys in developer view: []`；probe B round2：`live keys: []` |
| 6 | 是**移开**不是**删除**（硬要求） | **pass** | `std::fs::rename`（hygiene.rs:376），名字耗尽 `bail!` 不回退删除（:384）；磁盘级逐字节：probe A 两个文件、probe B 全 5 文件相等 |
| 7 | 自设植入 ⇒ 目标测试变红 | **pass** | P1（`should_quarantine→false`）EXIT=101、2 failed；P2（`rename→remove_dir_all`）EXIT=101、4 处红（含“destroyed instead of moved aside”） |
| 8 | 逐字节回退 + 三法证明 | **pass** | `cmp` 与保存副本一致；status 空；diff --stat 空；`hash-object` == HEAD blob（两文件） |
| 9 | 两轮复现件真的两轮 | **pass** | 测试文件本身用 `tempdir` + 两个 run_id；我自查 probe B 独立复现：round1 留下 5 文件 → round2 的 `.stale-` 与之一一相等 |
| 10 | 不依赖 `.workspace/mario`，用 scratch | **pass** | 两侧都用 `tempfile::tempdir()`；probe 输出里的 workspace 是 `%TEMP%\.tmpXXXX\workspace` |
| 11 | `.workspace/mario/**` 未改 | **pass** | ls-files=0；259 文件；最新 mtime 14:32:28 < 19:42:09；PS 摘要 `4e494547…aa84a` |
| 12 | `runs/**` 只读未动（摘要口径写清） | **pass** | 最新 mtime 14:44:16 < 批次起点；`runs` 全域 PS 摘要 `01ff775e…40dc3`、`smoke-t6` `c144ef32…7a9c03`，与 DR-54/DR-57 记录**逐字一致** |
| 13 | `PRD-mario.md` sha 未变 | **pass** | `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`；区间 diff 空 |
| 14 | 引擎树未改（嵌套仓/摘要） | **pass** | 外层 `ls-files godot-mcp/godot`=0（空判）且被 `.gitignore:33` 忽略；嵌套 `status --porcelain`=0；HEAD `fc63af77c3`；最新 mtime 10:37:38；关键文件 sha `ece4ae63…ff3f` |
| 15 | 无新依赖 | **pass** | `git diff --stat ea1cf07..HEAD -- Cargo.toml Cargo.lock` 空 |
| 16 | 未 push / 未 stage | **pass** | `origin/master` = `ea1cf07a…`（未变）；`git diff --cached --stat` 空 |
| 17 | 两个假绿陷阱各实测 | **pass** | 陷阱 1：不存在 pathspec 的 `git diff` 输出空、exit 0；陷阱 2：`cmd` 中 `git rev-parse db145b5^:src/runtime/run_loop.rs` 得 `e7678cc`（= 本提交，修正后）而 bash 得 `f13d600`（= 父提交，未修正）——**同一命令、同一 exit 0、不同 blob** |
| 18 | 实现者的诚实声明逐条核实 | **pass** | §6；未发现“假设当实测” |

### §2 附注：目录摘要口径（可复现，写明）

与 DR-54 验收报告 §2 附注同口径，但**必须补一条**：PowerShell `Sort-Object` 的排序是**文化敏感**的，
而 Python `sorted()` 是序数排序；两者对 `runs/smoke-t6` 结果相同，对 `runs` 全域**不同**：

- 口径：递归枚举文件（含隐藏；`os.walk`/`Get-ChildItem -Recurse -Force`），每文件取**相对仓根**路径
  （`\`→`/`、转小写）、**字节长度**、**SHA256（小写 hex）**，三列以 `\t` 连接、行间 `\n`、**不加尾随换行**，
  整体 UTF-8 后取 SHA256；行按路径升序排序。
- 实测：`runs/smoke-t6` = `files=135 digest=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03`
  （Python 与 PowerShell **一致**）；
  `runs` 全域 = PowerShell `files=5147 digest=01ff775e36935d3d92dab6919fe030389a8ff53483c52e87288ad711ec840dc3`（**与 DR-57 记录逐字一致**），
  而 Python 序数排序得 `f3c2a3649a9a49a30185665a482a8b2271f9719073ee0024d729bd896b1b6f45`。
  ⇒ **排序器是口径的一部分**；我以 PowerShell 结果作为与历史基线可比的值，Python 的差异已定位为排序器差异、非内容变更
  （文件数两边都是 5147，且 `smoke-t6` 两种排序同值）。
- `.workspace/mario` PS 摘要（我自算，无历史基线可比）= `files=259 digest=4e494547416b2e87ba025d686afef9447d4f92c027917d1790e6fc9deaeaa84a`。

---

## 3. 反例清单（我的植入 + 观测 + 是否推翻结论）

**实验 P1 —— 把隔离关成恒不触发（生产代码，测试未动）**

| 项 | 内容 |
|---|---|
| 植入 | `src/runtime/hygiene.rs::should_quarantine` → `let _ = live; false` |
| 命令 | `cargo test --offline --test evidence_isolation` |
| 观测 | `EXIT=101`；`test result: FAILED. 1 passed; 2 failed`；`:113` 报 `[".hoh/deterministic/battery.json", ".hoh/deterministic/raw/input_channel_probe.json"]`；`:214` 报 5 个 round-one 文件 |
| 结论 | 目标测试**非空洞**，且失败形态与真机 `.messages[54]` 的泄漏集合同形 |
| 回退 | `cp` 回保存副本；`cmp` 一致；status/diff 空；`hash-object` == HEAD blob |

**实验 P2 —— 把“移开”改成“删除”（生产代码，测试未动）**

| 项 | 内容 |
|---|---|
| 植入 | `std::fs::rename(&live, &target)?` → `std::fs::remove_dir_all(&live)?` |
| 命令/观测 | `--test evidence_isolation`：`EXIT=101`，`:121` = `the previous round's evidence was destroyed instead of being moved aside`，`:219` = `must be moved aside intact, not deleted: []`；`--lib quarantine`：`EXIT=101`，`hygiene.rs:593`（读不到 `battery.json`）、`:631`（同秒两次得同名 ⇒ `left != right` 失败） |
| 结论 | **“不是删除”这条断言也是非空洞的**——若实现等价于删除用户数据，这些断言立刻变红（任务书判 fail 的那条防线确实带电） |
| 回退 | 同上三法证明（`56089ec2…` / `e7678cc7…`） |

**实验 X —— 假绿陷阱 1（不存在 pathspec 不报错）**

```
$ git diff --stat ea1cf07..HEAD -- "godot-mcp/godot/definitely/not/here"
(无输出)
exit=0
```
⇒ 空输出**不能**当“未改动”的证据。对照：`git ls-files godot-mcp` = **6484**（pathspec 真命中）、
`git ls-files godot-mcp/godot` = **0**（外层对引擎树是空判）。

**实验 Y —— 假绿陷阱 2（`cmd` 吃掉 `^`）**

```
cmd>  git rev-parse db145b5^:src/runtime/run_loop.rs
e7678cc77e3abf0d5240514ec384c95eda851a2a      # = db145b5 本身（修正后），^ 被吞
bash$ git rev-parse db145b5^:src/runtime/run_loop.rs
f13d600e2238ffdbf567c2d5f7d0636aa8f5d6ee      # = 父提交 ea1cf07（未修正）
cmd>  git rev-parse db145b5:src/runtime/run_loop.rs
e7678cc77e3abf0d5240514ec384c95eda851a2a
```
⇒ `cmd` 下 `rev^:path` 会**静默**变成 `rev:path`，exit 仍 0。副作用：`cmd` 里末尾的 `^` 还会吃掉换行
（我第一次多行测试被拼成一行）。本报告所有历史对象读取都在 `bash` 下做。

---

## 4. 对“隔离真实且非删除”的独立判定

**隔离真实 —— 成立（限定于确定性证据区）。** 我读代码确认机制后再自建场景复现：

1. 调用点唯一且时机正确：`run_loop.rs:353` 在 `initialize`（:337）之后、`A_0` 快照（:413）与
   Planner（:512）/Developer（:709）/Tester（:1055）之前。`initialize` 不创建也不读 `.hoh/deterministic`
   （`godot.rs:3292-3336`）；`create_dir_all(.hoh/deterministic/raw)` 在 `evidence_battery`（`godot.rs:3372`），
   属轮内、在 Developer 之后。
2. **读取路径**之所以看不到旧证据：旧证据被 `rename` 成兄弟目录，`.hoh/deterministic/**` 在角色运行前为空。
   提示词/工具点名的路径全部形如 `.hoh/deterministic/**`（`prompts/mod.rs:56`、`tester.md:9-10,23-27`、
   `skills/godot-testing.md:7-12`、`godot.rs:3447-3451`）；没有任何提示词让角色 glob `.hoh`；
   `PROJECT_MAP.md` 明确“免得角色去探索文件系统”，且 `PROJECT_MAP` 走 `.hoh` 排除（`policy.rs:39`）。
3. **我的独立构造**（`%LOCALAPPDATA%\Temp\dr59-accept\probe`，只复用仓内既有 `tests/common` 离线替身，
   用我自己的场景与断言）：probe A 单轮预置上一轮证据 ⇒ Developer 视图 `live keys = []`，
   隔离目录逐字节保留；probe B 同工作区真跑两轮 ⇒ 第二轮 Developer 视图 `live keys = []`，
   第二轮隔离目录与第一轮证据**整目录逐文件相等**。

**非删除 —— 成立（并已验证这条断言带电）。** `hygiene.rs:376` 是 `std::fs::rename`；名字窗口耗尽时
`:384` `bail!`，**不**像 DR-49 单文件场景那样回退删除。磁盘级证据不是只看 harness 快照：
probe A 直接 `read_to_string` 隔离目录里的 `battery.json` / `raw/input_channel_probe.json` 与种子比较相等；
probe B 对 5 个文件整体比较相等。反向证明：P2 把 `rename` 换成 `remove_dir_all` 后，
`:121` 立刻报“destroyed instead of being moved aside”。

**边界（必须一起说清）**：这是**命名/路径隔离**，不是把旧字节移出模型可达范围——
`DEF-1`（`.stale-` 仍在角色 cwd 内）与 `DEF-2`（`.hoh/evidence/**` 完全未被隔离，且被
`view::copy_evidence` 原样复制进 Tester 候选视图）都是**实测**。任务书 §1.2 允许 `.stale-` 移开，
故 DEF-1 不构成本批判 fail；但 DEF-2 说明“同类路径”这一半并未随本批闭合。

---

## 5. 两轮复现件的独立判定

- **真的跑了两轮**：`tests/evidence_isolation.rs:170-189` 的 `run_round` 各自 `run_loop::run(..., run_id)`，
  `:200` 跑 `run-1`、`:210` 跑 `run-2`，中间 `:204-208` 断言第一轮**真的**留下了
  `.hoh/deterministic/build.json`（污染前提），否则测试自己失败。⇒ 不是“一轮跑两次断言”。
- **污染形态真实**：关掉隔离（我的 P1）时它报出的泄漏集合
  `[".hoh/deterministic/battery.json", ".hoh/deterministic/build.json", ".hoh/deterministic/deterministic.json", ".hoh/deterministic/deterministic.log", ".hoh/deterministic/record-00.json"]`
  与真机 `.messages[54]` 读到 `battery.json`（含 pid 108432 / “the editor is not clean” / os error 10061）
  的形态一致。真机原始证据我也自己取到：`runs/smoke-t7/iter-1/traj/developer.attempt1.json`
  `.messages[52]` 逐字含 `type "F:\moonbit-hof-rs\.workspace\mario\.hoh\deterministic\battery.json"`，
  `.messages[54]`（tool 结果）里 `108432 / the editor is not clean / 10061 / 4246 byte / ACTION_BINDING_UNKNOWN`
  全部为真；`runs/smoke-t7-experiment/pre_run_workspace_inventory.txt` 里
  `.workspace/mario/.hoh/deterministic/battery.json` = **9314** 字节，而
  `runs/smoke-t7-experiment/smoke-t6-workspace-baseline/deterministic/battery.json` 也是 **9314** 字节且含同样片段。
- **不依赖 `.workspace/mario`**：实现者测试与我自己的 probe 都用 `tempfile::tempdir()` + `FakeAdapter`；
  我实测期间 `.workspace/mario` 的最新 mtime 仍是 14:32:28（未变）。
- **报告是否给了 scratch 路径与清理**：给了——`C:\Users\wyl\AppData\Local\Temp\dr59-scratch\`（其日志目录），
  并称定稿后删除；我实测 `Test-Path` = **False**，`%TEMP%\dr59-baseline.txt` = **False**。测试自身的
  workspace 是 `tempdir` 自动清理（我 probe 输出里的 `%TEMP%\.tmpXXXX\workspace` 即此类）。
  唯一可挑的是：报告没把“测试用的 tempdir 路径”写成一条，只写了日志 scratch 目录——**info 级**。

---

## 6. 对实现者“诚实声明”的逐条裁决（不得让假设混成实测）

| 项 | 它的声明 | 我的核实 | 裁决 |
|---|---|---|---|
| H-1（§8.1） | 3 条 `hygiene.rs` 单测是**实现之后**补写，不存在“先红” | `git diff ea1cf07..HEAD -- src/runtime/hygiene.rs` 只有 3 个 `#[test]`（+98/+127/+146），`db145b5` 同时含实现；**结构上确实不可能先红** | **属实**，且它主动披露、未粉饰 |
| H-2（§8.2） | 第三个测试是后加的，随后重跑全量 | `7fab86b` 只改 `tests/evidence_isolation.rs`（+66/-1）；全量套件我实测 359/0/7 | **属实** |
| H-3（§8.3） | 曾用 `\| Tee-Object` 跑基线，PowerShell 把 stderr 当 ErrorRecord 致管道退出码报 1 | 我用 `powershell 5.1` 与 `pwsh 7` 各做最小复现，`$LASTEXITCODE` 都等于真实值 0，**未复现** | **未核实**；但这是对**它自己日志**的保守自述（它说自己不信任那个 1），不影响产物判据 |
| H-4（§8.4） | 把 DR-49 `invalidate_artifact` 的内联 `.stale-` 构造换成共享 `stale_name()`，生成字符串完全相同 | diff 显示 `{base}.stale-{stamp}` / `{base}.stale-{stamp}-{attempt}` 与旧代码逐字符同形（`godot.rs` diff 5+/7-）；全量套件绿，DR-49 既有单测（`frame-00.png.stale-` 前缀、缺失返回 `None`）通过 | **属实** |
| H-5（§5 尾注） | “真机上模型不再读到”**不**声称，只能由下一轮真机判定 | 正确：我离线只证明了机制与读路径 | **诚实**，I-1 分类正确 |
| H-6（§2.4） | 9314 字节同源 + 三项片段 | 我实测：baseline 9314 B 且 `108432`/`the editor is not clean`/`10061` 均 True；inventory 亦 9314 B | **属实** |
| H-7（§6） | `.workspace/mario` 259 文件、最新 14:32:28；`runs/smoke-t6` 135、`smoke-t7` 115、最新 14:44:16；PRD sha；嵌套仓 HEAD `fc63af77c3`、关键文件 sha `ece4ae63…`、mtime 10:37:38 | 逐项实测一致（见 §2 表 11-14） | **属实** |
| H-8（§7 R-1/R-3） | `.stale-` 仍在 cwd 内（残余可达）；`.hoh/evidence/**` 未纳入本批 | 我用 probe A **实测**了两者；并额外实测 **R-3 的放大版**：`.hoh/evidence` 的旧文件会被 `copy_evidence` 原样复制进 Tester 候选视图 | **R-1/R-3 属实**；其 R-3 只说到“开轮时在生效路径”，未说到“会被复制进 Tester 视图”（我补测，记 DEF-2） |
| H-9（§8.8 清理） | scratch 已删除，仓内未留临时文件 | `Test-Path` False；`git status --porcelain` 空（验收期间父代理的文档提交使其又变空） | **属实** |
| H-10（§1 门） | 359/0/7、EXIT=0、零警告 | 我实测同值、同 exit、日志里 `^warning` 计数 0 | **属实** |
| H-11（§8.5） | 未改 `DECISIONS.md` | 区间内只有 `944770f`（**父代理**）动 `DECISIONS.md`；实现者 3 提交不含它 | **属实** |

**未发现任何“把推断写成实测”的地方**；它对作用域（R-2 轮内 vs 跨轮）、对 E3/A0 的边界、对真机行为的
保留都写得克制。

---

## 7. 我没有独立复核的部分（我的局限）

1. **未跑真机**：不启动 Godot、不碰端口、不联网、不调模型端点（任务书硬约束）。因此 I-1（下一轮模型
   上下文不再含旧证据）与 quarantine 在真机上的实际命名/累积**只能留待真机批次**。
2. **未在 `ea1cf07` 上重跑全量**取得 353 基线（会改动 worktree/HEAD，违反纪律）。改用“+6 算术 + 测试语料
   逐字节未动 + D244/DR-57 的既有 353/0/7 记录”三方交叉，记为 §5 unverified 第一条。
3. **未复跑 `91a28f8` 的历史红**（不 checkout、不改写历史）。以结构证明（该提交有测试、无实现）替代，
   并用自己的 P1 复现同形红。
4. **未读实现者已删除的原始日志**（`%TEMP%\dr59-scratch\`），只验证了它已被删除。
5. **未重跑实现者的 `dr57-plants.ps1` 之类脚本**（与本批无关），也未复现其 §8.3 的 PowerShell 陷阱。

---

## 8. 给下一批的建议（**我没有改任何代码**）

1. **DEF-2 单独立批（我建议 DR-61，优先级高于 DR-60）**：把开轮隔离扩展到“同类残留”——至少覆盖
   `.hoh/evidence/**`。要点：①开轮把旧 `.hoh/evidence/**` 也按 `.stale-` 移开（或让 `copy_evidence`
   跳过 `*.stale-*`，两者取其一并说明为何）；②测试必须**实测**“上一轮的 `.hoh/evidence` 文件不再进入
   Tester 候选视图”（我给出的观测点：`InvocationRecord.files` 里 Tester 记录的 `.hoh/evidence/**`），
   并保留“旧字节仍可寻址”的断言；③`.hoh/evidence.json`、`.hoh/skills/*` 等 R-3 清单逐条给出**实测**
   （在开轮时点 vs Developer 调用时点）而非推断。
2. **DEF-1 需要一个显式决策**：是接受“.stale- 仍在 cwd 内、靠标记表达不可信”，还是把隔离物移出
   workspace（例如 `runs/<run_id>/quarantine/`）。若要移出，注意它会混进本轮 run 目录、可能影响 E5
   三树比对与 run 清单核查——必须在设计阶段把这条权衡写进 DECISIONS。
3. **给隔离加“可判定性”测试**：现在断言的是“路径为空 + 字节在 `.stale-` 下”；建议再加一条
   “`.hoh/deterministic.stale-*` 不出现在 `PROJECT_MAP.md`、不出现在任何角色 prompt”的断言，
   把 R-1 的“残余可达性”从口头风险变成可回归的不变量。
4. **DR-60（flake）先刻画再修因**（D246 已定），本批验收未观察到 flake：我这一次全量
   `endpoint_liveness` 7/7 通过，仅 1 次全量运行，不足以推翻 D246 的 1.8% 量化。
5. **摘要口径入库**：把“PowerShell `Sort-Object` 文化排序”写进验收口径工件（我在 §2 附注已给出可复现
   写法），否则下一批会再次出现“摘要对不上但内容没变”的解释成本（DR-54 验收站已提过同样的建议）。

---

## 9. 报告自证与产物

- 本报告路径：`.spec/hof-rs/tasks/TASK-DR59-ACCEPTANCE.md`（**新建，未提交、未 stage**）。
- 我的全部原始输出在仓外：`C:\Users\wyl\AppData\Local\Temp\dr59-accept\`
  （`digest.py`/`digest.ps1`/`digest_var.py`、`probe\`（独立 scratch 工程 `dr59-probe`）、
  `probe-a.txt`/`probe-run.txt`/`probe-run2.txt`、`plant-p1.txt`/`plant-p2-int.txt`/`plant-p2-lib.txt`、
  `post-restore.txt`、`extract_smoke.py`/`verify_prov.py`、`hygiene.rs.orig`/`run_loop.rs.orig`）。
- 全量套件日志在 `/tmp/i1_suite.txt`（Git Bash 临时目录，本次会话）。
- 验收结束时：`git rev-parse HEAD` = `944770fbe6de63518568f5285ba15f52321258d1`；
  `git status --porcelain` 仅有本报告这**一个**未跟踪文件；
  `git diff --stat` 空；`git diff --cached --stat` 空；`origin/master` 仍 `ea1cf07a156ec45bc536ed9b028ac4e4350a3ad7`。
- 我对仓库的**唯一**临时改动是 §3 的两次受控植入，均已逐字节回退并以三法证明；未修任何我发现的问题。
