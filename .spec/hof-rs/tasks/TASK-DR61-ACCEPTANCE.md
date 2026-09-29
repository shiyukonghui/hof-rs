# TASK-DR61-ACCEPTANCE — DR-61「上一轮证据结构上不可达」独立验收报告

> 独立验收子代理产出。**未继承**实现者或调度者的任何结论；下列每条 evidence 都是我在本会话亲自跑出、
> 亲自复制的输出。任务书：`.spec/hof-rs/tasks/TASK-DR61-ACCEPT.md`；判据：`.spec/hof-rs/tasks/TASK-DR61.md`
> 与 `DECISIONS.md` D247/D248。
> 实现者报告（仅当线索）：`.spec/hof-rs/tasks/TASK-DR61-REPORT.md`。
> 批次起点 `5abddbd`（= `origin/master`）；被验收的代码树 = `be8d115`（= 当前 HEAD 的 `src`/`tests`，见附录 A）。
> **离线**：未启动 Godot、未触碰任何外部/MCP 端口、未联网、未调模型端点。未 push、未 stage、未改历史。
> 唯一改动：§4 的 4 处受控植入（3 处生产代码 + 1 处测试 fixture），**全部逐字节回退并三法证明**；
> 另有 1 个临时 scratch 集成测试文件（`tests/dr61_acceptance_scratch.rs`），跑完即删，最终 `git status --porcelain` 为空。

---

## 1. 结构化结论（机器可读）

```json
{
  "verdict": "pass",
  "criteria": [
    {
      "id": "SUITE",
      "pass": true,
      "evidence": "`cargo test --offline`（bash，真实退出码）：`EXIT=0`；逐 target 聚合 39 targets / passed=366 / failed=0 / ignored=7 / `^warning`=0；与基线 359/0/7 对照 +7 = 新集成目标 3 + lib 净 +4。`#[ignore` 出现次数 HEAD 与 `5abddbd` 均为 8（7 属性 + 1 文档注释，全在 tests/godot_smoke.rs），ignored 7→7 未增。逐条核对见 §3/§5。产物：C:\\Users\\wyl\\AppData\\Local\\Temp\\dr61-accept\\FINAL-suite.txt、FINAL-exit.txt。"
    },
    {
      "id": "UNREACHABLE_STRUCTURAL",
      "pass": true,
      "evidence": "两处自设植入、两条独立运行，均红：(1) 在 cwd 内、`.hoh` 之外植入 `.hoh2/previous-round-battery.json` → `--test evidence_unreachable` 红在 `tests/evidence_unreachable.rs:233`，报文点名 `.hoh2/previous-round-battery.json`（E1，EXIT=101）；(2) 关掉隔离（生产代码 `should_quarantine`→false）后在 `.hoh` 下的上一轮证据存活 → 同测试红在 `:204`，reached keys 含 `evidence/frame-00.png` 与 `SCAFFOLD.md`（E2，EXIT=101）。⇒ 不变量确为「遍历整个角色 cwd」，不是只针对 `.hoh` 的位置约定。"
    },
    {
      "id": "QUARANTINE_LOCATION",
      "pass": true,
      "evidence": "隔离物 = `runs/<run_id>/quarantine/`（`src/runtime/hygiene.rs:470` `run_dir.join(QUARANTINE_DIR)`，`QUARANTINE_DIR=\".hoh\"` 见 `:350`）。我的 scratch 探针 `accept_location_and_full_cwd_walk`：断言 `q.is_dir()`、`!q.starts_with(workspace)`、且 **canonicalize 后**仍不在 workspace 内；随后对 `<workspace>` 全树 walkdir 递归，`reaches(cwd, BATTERY).is_empty()` 与 `reaches(cwd, FRAME).is_empty()` 均成立、且 cwd 内无任何含 `.stale-` 的键（绿，见 §4 E5）。结构前提还有 `hygiene.rs:422-431` 的词法+canonical 双重 guard 与 `:474-492` 的两处 `bail!`。"
    },
    {
      "id": "NOT_DELETE",
      "pass": true,
      "evidence": "移动用 `std::fs::rename`（`src/runtime/hygiene.rs:522`），无任何删除分支。旧字节可寻址：E5 探针断言两个 marker 在 quarantine 下各出现**恰好 1 次**（`reaches(kept, BATTERY).len()==1`、`FRAME` 同）。名字窗口耗尽**失败而非删除**：E5 探针 `accept_exhaustion_fails_and_deletes_nothing` 预占 stamp±窗口内全部 64 个 `.hoh.stale-<stamp>[-n]` 名后调用 `quarantine_previous_evidence`，返回 `Err(\"DR-61: could not move .hoh aside: all 64 … names … are taken\")`（`hygiene.rs:515-521`），且 `.hoh/deterministic/battery.json` 逐字节仍在原位（绿）。"
    },
    {
      "id": "NON_VACUITY",
      "pass": true,
      "evidence": "两处只改生产代码的反例均红：P1 隔离关掉（`hygiene.rs::should_quarantine`→`let _ = live; false`）→ E2 红；P2 隔离物放回 cwd 内（`let root = workspace.join(QUARANTINE_DIR)` + 同时短路两处 guard）→ E3 红在 `:227`，路径 `quarantine/.hoh.stale-1790689294/deterministic/battery.json`。另加 P3（`view.rs:131` 的 `.stale-` 跳过关掉）→ `src/runtime/view.rs:335` 红。三次回退均：`cmp` identical + `git status --porcelain` 空 + `git diff --stat` 空 + `git hash-object` == HEAD blob（hygiene `9de24a82…`、view `f3a85495…`）。"
    },
    {
      "id": "COPY_EVIDENCE",
      "pass": true,
      "evidence": "`src/runtime/view.rs:131` `if rel.split('/').any(hygiene::is_expired_name) { continue; }`（谓词 `hygiene.rs:383`）。我自设场景（E5 `accept_candidate_view_excludes_previous_evidence`）：run-1 真跑 → 在 `.hoh/evidence/ACCEPT-recognisable.png` 落可识别文件 → run-2 开轮 → 取 **Tester 被调用那一刻**的候选视图快照：键 `.hoh/evidence/ACCEPT-recognisable.png` 不存在、无任何 value 等于该 marker；同一 marker 在 `runs/run-2/quarantine/**` 下**恰好 1 份**（移开非删除）。非空洞性由 P3 保证（`view.rs:335` 红）。"
    },
    {
      "id": "NO_OVER_QUARANTINE",
      "pass": true,
      "evidence": "轮内反馈**未**被整树隔离破坏：E5 探针 `accept_intra_round_feedback_survives` 跑一个 2 轮次迭代的完整 round（`run_scenario(root, 2, …)`），断言 iteration 1 的 Developer cwd 快照**不含** `.hoh/deterministic/build.json`（对照），而 iteration 2 的 Developer 快照**含**该键且内容含 `fake adapter: build check ok`（= t-1 电池产物）⇒ DR-59 R-2 的刻意见 t-1 轮内反馈仍在。代码侧同证：`quarantine_previous_evidence` 全仓唯一调用点 `src/runtime/run_loop.rs:356`，位于 `for iteration in 1..=cfg.runtime.iterations`（`:448`）**之前**，轮内再无第二次隔离；每轮迭代末尾的 `run_battery_pass`（`:815`/`:890`）重建 `.hoh/deterministic` 不受影响。（绿）"
    },
    {
      "id": "GUARDS",
      "pass": true,
      "evidence": "`runs/**`：`git ls-files runs`=0（外层空判）、我自算 PS 摘要（口径见 §2，含 `Sort-Object` 文化排序）批次前后均 `files=5147 digest=01ff775e36935d3d92dab6919fe030389a8ff53483c52e87288ad711ec840dc3 newest=2026-09-29 14:44:16`；`runs/smoke-t6` 复算 = `files=135 digest=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03`，与 DR-54/DR-57/DR-59 记录**逐字一致**。`.workspace/mario`：`ls-files`=0、`files=259 digest=4e494547416b2e87ba025d686afef9447d4f92c027917d1790e6fc9deaeaa84a newest=2026-09-29 14:32:28`（前后一致）。`PRD-mario.md` sha256=`4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`（未变）。引擎（嵌套仓，D242）：`git -C godot-mcp/godot status --porcelain`=0 行、嵌套 HEAD=`fc63af77c33368c4a1bb839c95d19750554f63a3`、关键源码 sha=`ece4ae63d445719b662a6e9ad99ba80bebba3ea3c94468094c7e9cb820ddff3f`、`find godot-mcp/godot -type f -newermt '2026-09-29 19:00'`=0；pathspec 真命中证明 `git ls-files godot-mcp`=6484（>0）而 `git ls-files godot-mcp/godot`=0（外层空判）。依赖：`git diff --stat 5abddbd..HEAD -- Cargo.toml Cargo.lock` 空。未 push：`git rev-parse origin/master`=`5abddbd88ec2f8a3095688ba52d76792f7149f33`，未 stage：`git diff --cached --stat` 空。"
    },
    {
      "id": "HONESTY",
      "pass": true,
      "evidence": "报告 §8 的 9 条自曝基本为实测或有据：H-1（新 hygiene 单测无「先红」历史）与我的函数清单 diff 一致（旧 API 签名变更使其无法先行编译）；H-2 的 curated→整树自我推翻由我的 E2 reached keys 含 `SCAFFOLD.md` 独立复现；H-5 的 evidence_isolation 断言改写经 diff 核对为**加强**（由「存在 `.stale-`」改为「不得存在」并把保留断言升级为磁盘读取）。未发现把推断写成实测的条目；报告 §7 明确分列「实测/推断/未验证」，且反复声明不声称 E3。仅一处措辞可更精确：§8.5 只说 `evidence_isolation.rs` 被改写，未点名 `hygiene.rs` 内 `quarantine_moves_the_evidence_aside_and_keeps_the_bytes` 被**改名+加强**为 `quarantine_moves_the_whole_artifact_tree_out_of_the_workspace`（覆盖未削弱，见 §5）。"
    }
  ],
  "defects": [
    {
      "id": "DEF-1",
      "severity": "minor",
      "what": "交付的回归测试 `tests/evidence_unreachable.rs` 的 `SEEDS`（:42-95）**全部落在 `.hoh` 下**。它确实遍历整个 cwd（:224 `walk(&workspace)`），我在 E1 证明该遍历对 `.hoh` 之外的字节也会红；但由于没有任何常驻 seed 位于 `.hoh` 之外，「cwd 全遍历」这一能力**不会被交付套件永久守住**——若将来有人把 :224 的 cwd 遍历窄化回只 walk `.hoh`，只要 seed 仍全在 `.hoh`，套件依旧全绿（唯一残留保护是 :233 的「cwd 内不得有任何 `.stale-` 键」）。这正是本批要根除的「位置约定」风险在**测试可持续性**层面的残影。",
      "reproduction": "E1：在 `SEEDS` 末尾加 `(\".hoh2/previous-round-battery.json\", \"DR-61 ACCEPT probe A: …\\n\")`，`cargo test --offline --test evidence_unreachable a_wildcard_walk_of_hoh_cannot_reach_the_previous_rounds_evidence -- --exact` → EXIT=101、`tests/evidence_unreachable.rs:233` 点名 `.hoh2/previous-round-battery.json`；而用**未修改**的交付 seed 跑同一测试 → 绿。⇒ 当前能力真实，但无常驻反例。"
    }
  ],
  "risks": [
    "R-A（范围边界，报告 R-2 已披露，我实测确认）：隔离目标是整个 `.hoh`（`hygiene.rs:371 QUARANTINE_AREAS=[\".hoh\"]`）。**`.hoh` 之外**的上一轮工作区残留不会被移走，仍可被 cwd 遍历读到。E1 正是该形态的实测：`.hoh2/previous-round-battery.json` 在开轮后仍在原处。「结构上不可达」在本批只对 `.hoh` 家族成立，不是对任意工作区残留。",
    "R-B（报告 R-3，我未测）：`run_loop.rs:991` 用 `view::copy_tree` 把 `.hoh/deterministic/**` 复制进候选，该函数**没有** `.stale-` 过滤（只有 `copy_evidence` 有）。开轮隔离后轮内该目录只应含本轮产物，但若角色自己写 `.stale-` 名，行为未测。",
    "R-C（报告 R-4，离线不可测）：真机上 `<workspace>/.hoh` 内若有进程持有句柄（MCP 通道写过 `mcp-sync.json`/`mcp-errors.jsonl`），Windows 下整树 `rename` 会失败并经 `?` 冒泡成轮次错误。这是「响亮失败」的有意取舍，但真机可用性未验证。",
    "R-D（报告 R-5）：`runs/<id>/quarantine/` 每轮留一个 `.hoh.stale-<ts>`，无 GC，累积风险与 DR-59 同族。",
    "R-E（报告 R-6）：`.stale-` 跳过是按名字的字符串约定（`name.contains(\".stale-\")`）。若本轮产物名含该子串，它不会进候选视图；我未在真机/测试中观测到触发。",
    "R-F（报告 §8.7，我实测复现）：引擎树最新 mtime 我测得「源码侧 2026-09-29 10:49:37 / 含 `.git` 则 10:58:15（远端跟踪 ref）」，与 DR-59 验收记录的 10:37:38 不同。我确认「0 个引擎文件晚于 19:00 批次起点 + 嵌套 status 干净 + HEAD/sha 未变」，但**历史差异的原因无人解释**，属遗留台账缺口。",
    "R-G（本次验收新观察到）：验收期间 HEAD 由 `be8d115` 推进到 `6bf654a`（4 个提交：报告 3 次 + D249/ACCEPT 1 次，全部为 docs）。我用 `git diff be8d115..HEAD -- src tests Cargo.toml Cargo.lock` 证明**代码树零差异**，故结论不受影响；但「验收期间有人仍在写历史」说明本分支不是冻结态。"
  ],
  "unverified": [
    "真机：未跑 E0–E6（`godot_smoke` 的 7 条 `#[ignore]` 保持 ignored，7→7），未做活体注入，未观察真机 quarantine 命名/累积。报告不声称 E3，我也未验证 E1–E6。",
    "实现者已删除的 scratch 原始日志（`C:\\Users\\wyl\\AppData\\Local\\Temp\\dr61-scratch\\`，我实测 `Test-Path`=False）：其报告中的红/植入引文无法直接核验，只能靠我自己的复现（§4）间接印证；其 P2a「Planner 断言先红」的说法我未能从任何现存工件核验。",
    "`5abddbd` 上的全量套件基线 359/0/7 我**未 checkout 重跑**（不修改 worktree/历史）；我以「39 targets 聚合 + 逐文件函数清单 diff + `#[ignore` 计数 8==8 + 改动面只有 5 个文件」交叉核对，未增 ignored、未删测试名、未放宽既有断言。",
    "报告 R-7 的 `warnings.log` 文案变化、以及「`runs/<id>.quarantine` 会被 `latest_run_id` 误当 run」的设计论据：未做行为级验证。",
    "`copy_tree` 的 `.stale-` 缺口（R-B）：未测量。"
  ]
}
```

---

## 2. 真实命令与退出码（关键面）

| # | 命令（`F:\moonbit-hof-rs`，离线） | 退出码 | 结果 |
|---|---|---|---|
| S | `cargo test --offline` | **0** | 39 targets；`passed=366 failed=0 ignored=7`；`^warning`=0 |
| E1 | `cargo test --offline --test evidence_unreachable a_wildcard_walk_of_hoh_cannot_reach_the_previous_rounds_evidence -- --exact`（`.hoh` 外植入在 `SEEDS`） | **101** | 红在 `tests\evidence_unreachable.rs:233`，点名 `.hoh2/previous-round-battery.json` |
| E2 | 同上（生产代码隔离关掉，交付 seed 原样） | **101** | 红在 `:204`；reached keys 含 `SCAFFOLD.md`、`evidence/frame-00.png` 等 |
| E3 | 同上（生产代码把隔离物放回 cwd） | **101** | 红在 `:227`，`quarantine/.hoh.stale-1790689294/deterministic/battery.json` |
| P3 | `cargo test --offline --lib runtime::view::tests::copy_evidence_skips_superseded_files_and_keeps_them -- --exact`（`view.rs:131` 跳过关掉） | **101** | 红在 `src\runtime\view.rs:335` |
| E5 | `cargo test --offline --test dr61_acceptance_scratch -- --test-threads=1`（我的 4 个 scratch 探针） | **0** | `4 passed; 0 failed; … finished in 59.86s` |

**摘要口径（写明，可复现）**：递归枚举文件（`Get-ChildItem -Recurse -Force -File`），每文件取**相对仓根**路径
（`\`→`/`、转小写）、字节长度、SHA256（小写 hex），三列 `\t` 连接、行间 `\n`、无尾随换行，整体 UTF-8 后取 SHA256；
行按路径升序排序，**排序器用 PowerShell `Sort-Object`（文化敏感排序）**——这是口径的一部分（DR-59 验收 §2 附注）。
脚本 `C:\Users\wyl\AppData\Local\Temp\dr61-accept-digest.ps1`。自校验：`runs/smoke-t6` 复算 =
`c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03`，与 DR-54/DR-57/DR-59 记录逐字一致 ⇒ 我的口径与历史基线同源。

**两个假绿陷阱（均实测）**：

- **`git diff` 对不存在的 pathspec 不报错**：`git diff --stat 5abddbd..HEAD -- no/such/path` → 无输出、`exit=0`。
  因此引擎「未改」不能靠外层 `git diff` 判断：我另行证明 pathspec 是否真命中 —— `git ls-files godot-mcp`=**6484**
  （>0，命中），`git ls-files godot-mcp/godot`=**0**（外层对引擎树是**空判**）⇒ 外层 `git diff -- godot-mcp/godot` 恒为空、
  无证据力，必须用嵌套仓（D242）。
- **cmd 的 `^` 是转义符**：cmd 中 `git rev-parse HEAD^` 与 `git rev-parse HEAD` **输出相同**（都是 `6bf654a…`，caret 被吞），
  而 `git cat-file -e HEAD^:.spec/hof-rs/tasks/TASK-DR61-ACCEPT.md` 在 cmd 返回 **OK**、在 bash 返回 **128**
  （该文件确由 HEAD `6bf654a` 新增、HEAD^ 内不存在）。⇒ 我所有 `<rev>^:<path>` 查询一律在 **bash** 执行。

---

## 3. 逐项核对表（任务书 §1）

| # | 判据 | 结论 | 我的实测要点 |
|---|---|---|---|
| 1 | 套件 `--offline` exit 0；对照 359/0/7；ignored 未增；无测试被删/放宽/加 `#[ignore]` | **pass** | EXIT=0；366/0/7；`#[ignore` 8==8；函数清单 diff：仅 hygiene.rs 1 条旧测试被**改名加强**，其余全是新增 helper/测试；`evidence_isolation.rs` 28 行删除全部是断言**加强**式改写 |
| 2 | 不变量遍历整个角色 cwd；`.hoh` 内与 `.hoh` 外两处植入都能红 | **pass** | E1（cwd 内 `.hoh2/`）红在 `:233`；E2（`.hoh` 内 seed + 关隔离）红在 `:204` |
| 3 | 隔离物在角色 cwd 之外；走一遍 cwd 全树无上一轮字节 | **pass** | `hygiene.rs:470`；E5 探针（词法+canonical+全树 walk）绿 |
| 4 | 是移开不是删除；旧字节可寻址；名字耗尽不删除（应失败） | **pass** | `:522` rename；E5 两个 marker 各恰好 1 份；E5 耗尽探针 `Err` 且原地字节完好 |
| 5 | 两处生产代码植入（关隔离 / 放回 cwd）都红；逐字节回退三法 | **pass** | E2、E3 均 EXIT=101；三次 `cmp`+status 空+diff 空+`hash-object`==HEAD blob |
| 6 | `copy_evidence`：上一轮 `.hoh/evidence` 件不进 Tester 候选视图 | **pass** | E5 探针绿；P3 使单测红 ⇒ 非空洞；marker 仍在 quarantine |
| 7 | 不得过度隔离：整树隔离后轮内 t≥2 仍见 t-1 反馈 | **pass** | E5 `accept_intra_round_feedback_survives` 绿；调用点唯一且在迭代循环前 |
| 8 | 禁区：mario / runs / PRD / 依赖 / 未 push / 未 stage / 引擎嵌套仓 | **pass** | 见 §1 GUARDS 与 §2 摘要口径 |
| 9 | 诚实声明逐条核实，不得把假设混成实测 | **pass** | 见 §1 HONESTY 与 §7 |

---

## 4. 反例清单（我自设植入的位置、观测、结论）

**E1 —— 在 cwd 内、`.hoh` 之外植入上一轮证据（只改测试 fixture）**

| 项 | 内容 |
|---|---|
| 植入 | `tests/evidence_unreachable.rs` 的 `SEEDS` 追加 `(".hoh2/previous-round-battery.json", "DR-61 ACCEPT probe A: pid 108432 (UNAVAILABLE: the editor is not clean)\n")` |
| 命令 | `cargo test --offline --test evidence_unreachable a_wildcard_walk_of_hoh_cannot_reach_the_previous_rounds_evidence -- --exact` |
| 观测（真实） | `EXIT=101`；`panicked at tests\evidence_unreachable.rs:233:9: DR-61: a walk of the role's cwd still reaches the previous round's .hoh2/previous-round-battery.json at [".hoh2/previous-round-battery.json"]`；`test result: FAILED. 0 passed; 1 failed; 2 filtered out; finished in 12.80s` |
| 结论 | 不变量对 `.hoh` 之外的 cwd 字节**确实敏感** ⇒ 不是「只针对已知位置」的约定。同一次观测也确认：实现**不**隔离 `.hoh` 之外的残留（R-A，任务范围外，非缺陷）。 |
| 回退 | `cp` 回备份；`cmp` identical；`git status --porcelain` 空；`git diff --stat` 空；`git hash-object tests/evidence_unreachable.rs` = `git rev-parse HEAD:…` = `4c407b94e6472066f6149ab444d67df62dbf5f26` |

**E2 —— 关掉隔离（生产代码，`src/runtime/hygiene.rs`）**

| 项 | 内容 |
|---|---|
| 植入 | `fn should_quarantine(live: &Path) -> bool { let _ = live; false }`（交付 seed 原样） |
| 观测（真实） | `EXIT=101`；红在 `:204`；`reached keys: ["EVIDENCE_HISTORY.md", "PROJECT_MAP.md", "SCAFFOLD.md", "TASK.md", "TOOLS.md", "args/probe.json", "deterministic/battery.json", "deterministic/build.json", "deterministic/deterministic.json", "deterministic/deterministic.log", "deterministic/record-00.json", "evidence.json", "evidence/frame-00.png", "evidence/replay/round-one.json", "plan.md", "scratch/gtools.txt", "skills/godot-dev.md", "skills/godot-testing.md"]` |
| 结论 | `.hoh` 内植入的上一轮证据让不变量红；同时**独立复现**了实现者 §3 的关键行：`SCAFFOLD.md` 不被当轮重写（`TASK.md/plan.md/TOOLS.md/EVIDENCE_HISTORY.md/PROJECT_MAP.md/skills` 未出现在 reached keys 中，即确被 `write_inputs` 覆盖）⇒ curated 列表不完备、整树隔离是必要的。 |
| 回退 | 同上四法；`git hash-object src/runtime/hygiene.rs` = `9de24a82981bc73de7f63de4631366db8140aaeb` == HEAD blob |

**E3 —— 把隔离物放回 cwd 内（生产代码，两处 guard 同时短路 + 改落点）**

| 项 | 内容 |
|---|---|
| 植入 | `let root = run_dir.join(QUARANTINE_DIR)` → `workspace.join(QUARANTINE_DIR)`；两处 guard 改 `if false && …`（`:474`、`:485`）。**必须同时短路 guard**，如实披露为「一次植入三处」。 |
| 观测（真实） | `EXIT=101`；`warning: unused variable: run_dir`；`panicked at tests\evidence_unreachable.rs:227:9: DR-61: a walk of the role's cwd still reaches the previous round's .hoh/deterministic/battery.json at ["quarantine/.hoh.stale-1790689294/deterministic/battery.json"]` |
| 结论 | 「隔离物落在 cwd 内」这一原始缺陷形态**必然红**，且红的是**全 cwd walk** 断言 ⇒ 不变量与目标同构。 |
| 回退 | 同上四法；hash 恢复 `9de24a82…` |

**P3 —— 关掉 `copy_evidence` 的 `.stale-` 跳过（生产代码，`src/runtime/view.rs`）**

| 项 | 内容 |
|---|---|
| 植入 | `if rel.split('/').any(is_expired_name)` → `if false && …` |
| 观测（真实） | `EXIT=101`；`panicked at src\runtime\view.rs:335:9: DR-61: a superseded evidence file must not reach the frozen candidate` |
| 结论 | DEF-2 的修复**非空洞**（单测在跳过被关掉时必红）。 |
| 回退 | 同上四法；`git hash-object src/runtime/view.rs` = `f3a854958e8570acf0b0d8eb9ec1e8df1dd87d5f` == HEAD blob |

**E5 —— 4 个独立 scratch 探针（`tests/dr61_acceptance_scratch.rs`，跑完即删）**

```
running 4 tests
test accept_candidate_view_excludes_previous_evidence ... ok
test accept_exhaustion_fails_and_deletes_nothing ... ok
test accept_intra_round_feedback_survives ... ok
test accept_location_and_full_cwd_walk ... ok
test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 59.86s
```
源码见附录 B（便于下一批复现）。删除后 `git status --porcelain` 为空。

---

## 5. 对「结构不可达」的独立判定

**判定：成立（在 `.hoh` 家族范围内），且不变量本身确为 cwd 级遍历检查。**

- 交付不变量测试的检查范围：`tests/evidence_unreachable.rs:201` walk `<workspace>/.hoh`；`:224` walk **整个 `<workspace>`**；
  `:233` 另查 cwd 内不得有任何 `.stale-` 键。E1 证明 `:224` 对 `.hoh` 之外的字节同样命中并断言失败。
- 隔离落点结构上在角色 cwd 之外：Developer cwd = `workspace`（`run_loop.rs:717`），Planner/Tester cwd = `runs/<id>/iter-<n>/{planner-view,candidate}`（`:520`/`:1063`），
  隔离物 = `runs/<id>/quarantine/**`（`hygiene.rs:470`）——workspace 的兄弟、`iter-<n>` 的兄弟。我的探针用**词法 + canonicalize** 双判定确认。
- 另有结构性 guard：目标若在 workspace 内则 `bail!`（`hygiene.rs:474-492`，含 canonical 防 symlink/junction），
  单测 `quarantine_refuses_a_destination_inside_the_workspace`（`:893`）固化；E3 证明「放回 cwd」必然红。
- **边界（不粉饰）**：不变量只保证「上一轮留在 `.hoh` 下的字节不可达」。`.hoh` 之外的 cwd 残留不在保证范围（R-A），
  且交付套件无常驻的 `.hoh` 外 seed 去永久守住 cwd 遍历能力（DEF-1，minor）。

---

## 6. 对「未过度隔离」的独立判定

**判定：未过度。整树隔离没有清掉轮内状态。**

- 机制层：`quarantine_previous_evidence` 全仓唯一定义（`hygiene.rs:457`）与唯一调用点（`run_loop.rs:356`），
  调用发生在 `for iteration in 1..=cfg.runtime.iterations`（`:448`）**之前**、`adapter.initialize`（`:337`）之后、
  `A_0` 快照（`:421`）与所有角色之前；轮内没有任何第二次隔离调用。
- 行为层：E5 `accept_intra_round_feedback_survives` 在真实 2 迭代 round 上证明 iteration 2 的 Developer cwd 快照
  含 iteration 1 的 `.hoh/deterministic/build.json`（内容 `fake adapter: build check ok`），而 iteration 1 的快照不含
  ⇒ t≥2 仍见 t-1 的电池证据，DR-59 R-2 的刻意语义**保留**。
- 反向保护：`a_clean_round_start_creates_no_quarantine_directory`（`tests/evidence_unreachable.rs:360`）与
  `quarantine_is_a_no_op_on_a_clean_start`（`hygiene.rs:834`）证明干净开轮不建空 `quarantine/`。
- ⇒ 任务书 §1.7 担心的回归**不存在**；若整树隔离误伤轮内反馈，E5 该探针会红，实测绿。

---

## 7. 实现者诚实声明的逐条裁决

| 报告条目 | 我的裁决 |
|---|---|
| §1 门 366/0/7、exit 0、39 targets、`#[ignore` 8=7+1 | **实测一致**（S；`#[ignore` 清单我逐行核对，全在 `tests/godot_smoke.rs`） |
| §2.1 隔离物在 `runs/<id>/quarantine` 且不在任何角色 cwd | **实测一致**（E5 探针，含 canonicalize） |
| §2.2 curated→整树，理由是 `SCAFFOLD.md` 不被重写 | **实测一致**（E2 reached keys 含 `SCAFFOLD.md`；`TASK.md/plan.md/…` 不在其中） |
| §2.3 `copy_evidence` 跳过 `.stale-`；跳过≠删除；哈希不受影响 | **跳过与保留实测一致**（E5/P3）；「哈希不受影响」我只做了代码级核对（`.hoh` 在 `HashExcludes::merged()`，`policy.rs:37-45`），未独立复算候选身份 |
| §4.3 P1（关隔离）红 | **我独立复现且更强**（E2，含 reached keys） |
| §4.4 P2（放回 cwd）红；变体 (b) OS 层拒绝 | **变体 (a) 我复现为红**（E3）；变体 (b)「把目录 rename 进自身子孙」我未复跑（删除的日志不可核验），但 E3 已足够证明非空洞 |
| §7 R-1 轮内 t≥2 仍见 t-1 | **实测一致且未回归**（E5 探针） |
| §7 R-2 `.hoh` 外残留不在范围 | **实测一致**（E1；且这是本次唯一看到范围边界的地方） |
| §7 R-3 `copy_tree` 无 `.stale-` 过滤 | **代码级核对一致**（`view.rs:62` 起无谓词）；**未做行为测量** |
| §7 R-4/R-5/R-6/R-7 | 未验证（见 §8 未验证项），但都如实标注为风险/推断，未见「推断冒充实测」 |
| §8.1 新 hygiene 单测无法「先红」 | **一致**：`quarantine_previous_evidence` 签名与返回类型都变了，旧测试文本在新 API 下无法编译；我的函数清单 diff 只看到 1 条旧测试被替换 |
| §8.3 「事后实测表明 P2a 本来就会红」 | **无法核验**（`plant-p2a-hole.txt` 已删）；结论本身是无害的自我克制，我未采信也未否决 |
| §8.5 「改写而非放宽」证据只有 evidence_isolation.rs | 我核对 diff：**改写确为加强**（存在→不存在；快照→磁盘读取）；但 `hygiene.rs` 旧的 `quarantine_moves_the_evidence_aside_and_keeps_the_bytes` 被**改名加强**为 `quarantine_moves_the_whole_artifact_tree_out_of_the_workspace`，报告未点名（info 级措辞不精确，不影响结论） |
| §8.6 摘要口径含 PS `Sort-Object` 文化排序 | **实测一致**：我的脚本按该口径复算，`runs` 全域与 `smoke-t6` 均与历史记录逐字一致 |
| §8.8/§6 引擎未改（嵌套仓 + mtime + sha） | **实测一致**：嵌套 status 0、HEAD `fc63af77…`、关键 sha `ece4ae63…`、0 个文件晚于 19:00；外层 `godot-mcp/godot` pathspec 空判（我已证明） |

---

## 8. 未验证项与理由（我未做，或做不了）

1. **真机轮次**：未启动 Godot、未触碰任何端口、未联网 ⇒ E0–E6 全部未验证；7 条 `#[ignore]` 保持 ignored（7→7）。
2. **`5abddbd` 基线 359/0/7 未 checkout 重跑**（会动 worktree/历史）。替代：`39 targets` 聚合、逐文件函数清单 diff、
   `#[ignore` 8==8、改动面仅 `src/runtime/{hygiene,view,run_loop}.rs` + `tests/{evidence_isolation,evidence_unreachable}.rs` + 文档。
3. **实现者 scratch 原始日志已删**（实测 `Test-Path`=False）⇒ 其报告内的引文（红/植入/变体 b）不可直接核验；
   我用自设的 E1/E2/E3/P3/E5 重建了同形证据。
4. **`copy_tree` 的 `.stale-` 缺口、`warnings.log` 文案、`latest_run_id` 与 `runs/<id>.quarantine` 的交互**：未做行为测量。
5. **候选身份哈希不受证据复制影响**：仅代码级核对（`.hoh` 在合并排除项），未独立复算 `hash_tree`。
6. **真机 rename 句柄风险（R-4）、quarantine 无 GC（R-5）**：离线不可测。

## 9. 给下一批的建议（我不改任何代码）

1. **把 cwd 遍历能力做成常驻反例（对应 DEF-1）**：在 `tests/evidence_unreachable.rs` 内加一个**自检型**用例，
   在临时工作区把一份 marker 放到 `.hoh` 之外的 cwd 目录，直接断言 `walk(&workspace)` 能命中它——
   这样把「walk 覆盖整个 cwd」与「实现只隔离 `.hoh`」解耦，任何把 walk 窄化回 `.hoh` 的回归都会立刻红。
2. **显式记录 `.hoh` 之外残留的范围边界**：R-A 已是既知边界，建议在任务书/决策里写明「DR-61 的不可达性以
   `.hoh` 家族为界」，避免下一批把它当成「任意工作区残留都不可达」。
3. **补 `copy_tree` 的 `.stale-` 判定**（R-B）：要么证明它不可能触发，要么打一个会失败的最小测试再决定是否修。
4. **引擎 mtime 台账口径统一**（R-F）：把「源码侧最新 mtime」与「含 `.git` 的最新 mtime」分开记录，
   并解释与 DR-59 记录 10:37:38 的差异，避免每批重复付出核验成本。
5. **验收期间不要继续写历史**（R-G）：本次 HEAD 从 `be8d115` 漂到 `6bf654a`；虽有 `git diff` 证明代码零差异，
   但冻结分支会让证据链更干净。

---

## 附录 A：验收期间仓库状态（我未做任何提交）

- 我的会话开始时：`HEAD=be8d115`，`git status --porcelain` 显示 `?? TASK-DR61-ACCEPT.md`、`?? TASK-DR61-REPORT.md`。
- 结束时：`HEAD=6bf654a7934d77a39401ca98404e4feafb614123`；`git status --porcelain` **空**；`git diff --stat` **空**。
- `git diff --stat be8d115..HEAD` = `.spec/hof-rs/tasks/TASK-DR61-ACCEPT.md`、`.spec/hof-rs/tasks/TASK-DR61-REPORT.md`、`DECISIONS.md`（D249）；
  `git diff --stat be8d115..HEAD -- src tests Cargo.toml Cargo.lock` = **空** ⇒ **被验收代码树 = `be8d115`，与当前 HEAD 的代码零差异**。
- `origin/master = 5abddbd88ec2f8a3095688ba52d76792f7149f33`（未 push；`origin/master..HEAD` = 9 commits）。
- 验收前后禁区摘要一致：`.workspace/mario` `259 / 4e494547…aa84a / 14:32:28`；`runs` `5147 / 01ff775e…40dc3 / 14:44:16`。

## 附录 B：我的 scratch 探针源码（已删除，供复现）

`F:\moonbit-hof-rs\tests\dr61_acceptance_scratch.rs`（删除前内容）：

```rust
//! DR-61 independent acceptance probes (scratch; deleted after the run).
mod common;

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
use std::sync::Arc;

use common::{
    happy_script, test_config, write, write_spec, FakeAdapter, FakeHarness, FakeStep,
    FakeToolChannel, InvocationRecord,
};
use hof_rs::model::{Ablation, Role};
use hof_rs::runtime::hygiene::{quarantine_previous_evidence, QUARANTINE_DIR};

const BATTERY: &str = "ACCEPT previous-round battery: pid 108432 (UNAVAILABLE: the editor is not clean)\n";
const FRAME: &str = "ACCEPT previous-round frame-00.png: 4246 bytes of smoke-t6\n";
const ACCEPT_EVIDENCE: &str = "ACCEPT previous-round evidence at .hoh/evidence/ACCEPT-recognisable.png\n";

fn walk(root: &Path) -> BTreeMap<String, Vec<u8>> { /* walkdir, follow_links(false), rel path -> bytes */ }
fn reaches<'a>(walked: &'a BTreeMap<String, Vec<u8>>, seed: &str) -> Vec<&'a String> { /* byte-equality hits */ }

async fn run_round(root: &Path, run_id: &str) -> Vec<InvocationRecord> {
    // test_config + write_spec + FakeHarness::new(happy_script()) + FakeAdapter + FakeToolChannel
    // + hof_rs::runtime::run_loop::run(&orchestrator, &spec, run_id)
}

fn quarantine_dir(root: &Path, run_id: &str) -> PathBuf { root.join("runs").join(run_id).join(QUARANTINE_DIR) }

#[tokio::test]
async fn accept_location_and_full_cwd_walk() {
    // seed .hoh/deterministic/battery.json + .hoh/evidence/frame-00.png; run_round("run-1")
    // assert: full cwd walk reaches neither marker; no ".stale-" key in cwd
    // assert: quarantine dir exists, !starts_with(workspace), canonicalize also outside
    // assert: each marker preserved exactly once under the quarantine
}

#[test]
fn accept_exhaustion_fails_and_deletes_nothing() {
    // pre-create 64 ".hoh.stale-<stamp>[-n]" names for stamp in now-4 ..= now+40
    // quarantine_previous_evidence -> expect Err containing "could not move"
    // assert .hoh/deterministic/battery.json still present, byte-identical, addressable
}

#[tokio::test]
async fn accept_candidate_view_excludes_previous_evidence() {
    // run_round("run-1"); write .hoh/evidence/ACCEPT-recognisable.png; run_round("run-2")
    // Tester record.files: key absent, no value == marker; marker once under runs/run-2/quarantine
}

#[tokio::test]
async fn accept_intra_round_feedback_survives() {
    // 2-iteration script (Planner/Developer/Tester x2) via common::run_scenario
    // dev(1).files has no .hoh/deterministic/build.json; dev(2).files does, content contains
    // "fake adapter: build check ok"
}
```
（正文完整、可直接重键入；上面省略的仅为四个 `walk`/`run_round` 辅助函数的标准实现与重复的断言细节，
与 `tests/evidence_unreachable.rs` 中同名辅助函数同形。）
