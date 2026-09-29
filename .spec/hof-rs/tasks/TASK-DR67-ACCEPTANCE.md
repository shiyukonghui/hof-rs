# TASK-DR67-ACCEPTANCE — DR-66 收口批的独立验收

- 判据来源：`TASK-DR67.md`（本批任务书 §0 的五件事与 §1/§2 的门与硬约束）；被验收对象：DR-67 的 6 个 `(DR-67)` 提交 + `.spec/hof-rs/tasks/TASK-DR67-REPORT.md`；上游：`TASK-DR66-ACCEPTANCE.md`（判 fail 的验收）、`TASK-DR66-REPORT.md`（含 DR-67 追加的 §9）、`DECISIONS.md` D261/D262。
- 性质：**独立验收、离线、以只读为主**。我没有上游对话上下文，下列每一条证据都是**我自己跑出来/读出来**的；实现者报告只当线索，**未继承其结论**。实现者的植入日志我只核其存在性，**关键植入我全部自己重做**（§3）。
- 落点：`F:\moonbit-hof-rs`（外层仓，`master`）。我开工时 HEAD = `91f1b9c`（本批 6 个提交的 tip）；验收期间**调度者**又落了两个**只含文档**的提交（`12e9052` 把报告入库、`8838b0a` 更正报告 §6.4/§6.5 的受控路径清单），我收工时 HEAD = `8838b0a98ead38a92f345f269370e9446f8aa946`，`origin/master` 全程为 `079cf828658ec269e51824f5c643ba548ed0a08a`（**ahead 16**）。`git diff 91f1b9c..8838b0a -- src tests Cargo.toml Cargo.lock` **为空** ⇒ 代码树未因这两个提交而变，我的套件结论适用于该树。
- 未启动 Godot、未碰端口、未联网、未调模型端点、未跑真机轮、未 push、未 stage、未改写任何历史、未修改任何既有文件（§10 的 7 处受控植入全部逐字节回退）。
- 仓外临时物：`C:\Users\wyl\AppData\Local\Temp\dr67acc`（`plant.py`、7 份植入日志 `my-plant-*.txt`、`suite-inrepo.txt`、`suite-clean.txt`、`bak/**`；4.6 GB 的仓外 `clean-target` 用完已删）。仓内唯一新增文件是本报告。

---

## 1. 结构化结论

```json
{
  "verdict": "pass",
  "criteria": [
    {
      "id": "DISCLOSURE",
      "pass": true,
      "evidence": "披露确实落到了 `TASK-DR66-REPORT.md` 的**新增 §9**（`:571` 起，`## 9. 【DR-67 新增】本地历史改写披露`）：§9.1（`:578-604`）表格列出**全部 6 个**被丢弃/被 amend 的哈希（`81ec7c1`/`f0183fd`/`c5bb814`/`3944a14`/`e8a3d93`/`18bf417`，外加最终态 `cb50575`）并贴了 reflog 原文；§9.2（`:610-619`）如实给出原因（提交信息被未加引号的 shell 通配符污染——我用 reflog 里 `c5bb814` 的正文 `%DST% 2609.01481v1.pdf … Cargo.lock Cargo.toml DECISIONS.md config godot-mcp python runs src target tests tools` 独立佐证）；§9.3（`:621-627`）写明「未 push、`origin/master` 全程 `079cf82`、被丢弃提交不在任何 ref」故可接受；§9.4（`:629-634`）记录 `dr66-wip` 处置。**错误机制描述的更正方式合格**：旧句仍在 `TASK-DR66-REPORT.md:541` 一字未改（我逐字比对：`reset --mixed` 所在行与 `a54424b` 版本`lo[0]==lc[0]` 为 **True**，长度均 260），其下 `:543-546` 是 `>` 引用块**【DR-67 更正：§7-8 的机制描述错了，原文保留在上】**，明说 `--mixed` 不移动工作树。另两处夸大表述（`:145`→`:147`、`:228`→`:230`）与 §4 标题的收窄块（`:263`→`:265`）同法处理，旧文字全部保留并标注。**但**：`git diff a54424b..e3f3cc8 -- TASK-DR66-REPORT.md` 的唯一一行删除是 `-## 附：本批 4 个提交（英文信息，均带 (DR-66)`，本地未 push）`——即**附录标题被静默删掉**（附录代码块现在无标题地挂在 §9 之后），而且 `TASK-DR67-REPORT.md:96-99` 与 `:467` 把这一行描述成「旧 §7-8 第 8 条被搬进更正块上方、1 删 1 增的同一段」，与 diff 事实**不符**（第 8 条从未被删，仍在 `:541`）。这不影响三处被点名文字「原文保留 + 标注」的成立，故本条判 pass，差额记 DEF-B。"
    },
    {
      "id": "BRANCH_HYGIENE",
      "pass": true,
      "evidence": "①**遗留分支已删**：`git branch -a` 只有 `* master` 与 `remotes/origin/master`；`git rev-parse dr66-wip` → `fatal: ambiguous argument 'dr66-wip': unknown revision…`，exit 128；`.git/logs/refs/heads/` **只剩 `master`**（dr66-wip 的 per-ref reflog 随 `git branch -D` 消失，这是该命令固有行为，其两条事实 `branch: Created from HEAD` 03:39:03 / `branch: Reset to HEAD` 03:39:26 已在删除前摘录进 `TASK-DR66-REPORT.md:606-608`）。②**对象未销毁**：`git cat-file -t` 对 `81ec7c1`/`f0183fd`/`c5bb814`/`3944a14`/`e8a3d93`/`18bf417` **全部返回 `commit`**；`git fsck --no-reflogs` 列出 `dangling commit 3944a1462cdf…`、`e8a3d933…`、`c5bb814ddc…`、`18bf417111…`（另两个是其祖先，reachable from the dangling tip，故不单列）；主 reflog 仍保留 `3944a14 HEAD@{2026-09-30 03:39:04}: commit: …` 与两次 `079cf82 HEAD@{…}: reset: moving to 079cf82`。③**未 force-push**：`git rev-parse origin/master` = `079cf828658ec269e51824f5c643ba548ed0a08a`（自 `079cf82` 起 `refs/remotes/origin/master@{0}` 之外无新条目）。④**本批没有再改写历史**：`git reflog --date=iso` 在 05:00–06:30 窗口内只有 6 条 `commit:` 记录，**无** `reset`/`commit (amend)`/`branch:` 记录（最近一次 amend/reset 分别是 04:18:24 / 03:39:26，属 DR-66）。"
    },
    {
      "id": "PERSISTED_EXIT_CODE_REAL_PATH",
      "pass": true,
      "evidence": "①**生产失败路径现在真的写两个位置**（读码 + 每个环节的独立证据）：`run_loop::run` 在**:404** `create_dir_all(run_dir)`、**:475** `write_run_meta`（即 meta.json 先于任何角色落盘），门命中后 `:957` `return Err(HofError::contract(violation).into())`；`cli_impl::run:604-614` 的 `match run_round_in(…) { Ok=>…, Err(error) => { let failed = run_loop::failed_run_summary(&run_id,&error); let _ = finalize_run(&run_dir,&failed); return Err(error); } }`；`run_dir` = `config.runtime.runs_dir.join(&run_id)`（`cli_impl.rs:516`）与 run_loop 的 `cfg.runtime.runs_dir.join(run_id)`（`:403`）**同一个目录**；`finalize_run`（`:720-722`）写 `runs/<id>/exit_code`，并在 meta.json 已存在时插入 `exit_code`。②**测试不再用手工 summary**：`tests/e1_increment.rs:333-335` 用生产 `hof_rs::runtime::run_loop::failed_run_summary(\"run-1\",&error)`（真实轮次产出的真实 `anyhow::Error`）再调生产 `hof_rs::cli_impl::finalize_run`；`:410-425` 的 `failed_summary()` 已降级为 gate 层对照（只在 `:468-479` 使用），不再是端到端断言的支撑。③**测试先证明缺口**：`:312-321` 断言失败轮次此刻**尚不存在** `runs/run-1/exit_code`、meta.json **没有** `exit_code`——这正是 DEF-2 的缺口。④**我的反例植入**：`persist-off`（把 `finalize_run` 的 `std::fs::write(run_dir.join(\"exit_code\"),…)` 删掉）⇒ `a_zero_engineering_write_round_fails_instead_of_reporting_ok` 与 `a_failed_round_persists_the_real_errors_class` **双双 exit 101**（`tests/common/mod.rs:663` 的 `read` panic）；`code-constant`（`Some(exit_code_of(error))`→`Some(2)`）⇒ `:390 left: 2 right: 4`。⇒ 两个落盘位置的断言是**承重**的。**边界（DEF-A）**：真正调用这两个函数的**调用点** `cli_impl.rs:604-614` 没有任何测试执行（全仓 `cli_impl::run(` 的调用者只有生产 `src/cli.rs:208`）；我的 `caller-glue-off` 植入把它退回 DR-66 的 `?` 形态后，`--test e1_increment` **13 passed / 0 failed**——即「调用点是否调用 finalise」只能靠读源码，不能靠测试。故本条判 pass（落盘确实恢复、测试确实走上生产函数），但把「调用点无执行覆盖」显式记为 DEF-A。"
    },
    {
      "id": "GATE_BROADENED",
      "pass": true,
      "evidence": "①**收窄已被删除**：`run_loop.rs:912-923` 现在只有 `let h_dev_after = hash_tree(...)?;` 与 `if h_dev_before == h_dev_after {`，DR-66 的 `no_engineering_write_attempt`（`.filter(|a| a.exit_was_limits)`）与 `if let (true, Some(attempt))` 已不存在（`git diff a54424a..HEAD` 的对应删除行可见）。②**我的反例植入** `narrowing-restored`（把 `exit_was_limits` 过滤加回门）：`a_zero_increment_round_that_finishes_normally_also_fails` **exit 101**，红在 `:542`，真实输出为 `RunSummary{ …, ok: true, …, failure_exit_code: None }`——正是 DR-66 §7-3 承认的残余假绿面被重新打开 ⇒ 拓宽真的承重、该测试非空洞。③该测试先自证夹具形状：`:533-538` 断言 `developer.attempt1.log` 的 `exit_was_limits == false` 且 `exit_status == \"Submitted\"`。④**被拓宽逼红的既有夹具逐条判定（我逐行读，且用 `git diff a54424a..HEAD` 核对删除行）**：本批 `tests/` 的删除行只有 7 行（`e1_increment.rs` 的 `let summary = failed_summary();`、`tool_discovery.rs` 的 `.writing(\"project.godot\", \"config_version=5\\n\")`、`configured_excludes()` 的 1 行实现与 4 行注释），**无任何断言、测试函数或 `#[ignore]` 被删**。三处夹具迁移全是**只增**：`evidence_isolation.rs:277-290` 在第二轮前写 `project.godot` 为 `config_version=5\\n# run-two\\n` 并断言该写入生效（第二轮的 Developer 写回 `happy_script` 的 `config_version=5\\n`，于是**真的产生增量**；原有隔离断言 `:295-309` 一字未动）；`evidence_unreachable.rs:364-378` 同法加 `project.godot` + `scripts/round_two.gd` 两笔真实工程写入（原断言 `:383-398` 未动）；`tool_discovery.rs:348-389` 的共用 helper 改为**调用唯一**的工程写入（static 计数器 nonce，写 `scripts/command_probe.gd` 与 `scripts/developer_write.gd`），而 `a_project_only_command_is_not_a_harness_read`（`:427-442`）在**同一个 temp root** 上调用它 **3 次**，旧夹具的第 2/3 次确实是零增量 ⇒ 迁移是必要的、不是顺手改需求；`result_semantics.rs:38-45` 只是给测试本地 `RunSummary` 补 `failure_exit_code: None`（新字段），非断言改动。⑤**迁移必要性我另做反例**（测试载体植入，D253 显式说明）：把 `evidence_isolation.rs:277-290` 整段删掉 ⇒ `round_two_cannot_read_round_one_evidence` **exit 101**，红在 `:254` `the round must run: contract violation: NoEngineeringWrite` ⇒ 迁移确实是拓宽逼出来的，不是装饰。⑥**台账普查**：`grep -rho 'FakeStep::new(Role::Developer)' tests/ | wc -l` = **34**（本批新增 2 个 e1 夹具后；实现者报 32 = 本批新增前，与 DR-66 验收的 31 口径差在计数单位），唯一「只写 `.hoh/**`」的仍是 `e1_increment.rs` 自己的夹具，与实现者所述一致。"
    },
    {
      "id": "EXIT_CODE_TRACKS_ERROR_CLASS",
      "pass": true,
      "evidence": "`failed_run_summary`（`run_loop.rs:138-150`）的 `failure_exit_code: Some(exit_code_of(error))` 使用与进程入口同一个函数；`run_exit_code_for`（`cli_impl.rs:701-706`）先返回它。测试 `a_failed_round_persists_the_real_errors_class`（`:366-401`）用 **contract 类 → 2** 与 **External 类 → 4** 两个真实错误各驱动一次，并断言 `failure_exit_code == Some(exit_code_of(&error))`、落盘文本为 `2`/`4`、meta.json 为 `2`/`4`——`:386-393` 明确说 `4` 是 `!ok` 分支**不可能**给出的数。**我的反例植入** `code-constant`（把 `Some(exit_code_of(error))` 改成常量 `Some(2)`）：该测试 **exit 101**，红在 `:390` `left: 2 right: 4`，即「码跟着错误类走」真的承重、测试非空洞。"
    },
    {
      "id": "INFO_ITEMS",
      "pass": true,
      "evidence": "①**门的警告文案已不声称检查 K**：`run_loop.rs:930-939` 现在是「the developer stage ended with no engineering write: no file in the artifact tree outside the hash-excluded runtime paths changed; every write went to an excluded path such as `.hoh/scratch`, `.godot/**` or `.import/**`」，全文无 `step budget`/`within the first`；`developer_write_deadline` 的文档（`:47-66`）显式写明它只是发给 Developer 的指令、运行时不与步数比较。我用植入 `warning-k-steps`（文案改回 `spent its whole step budget … inside the first 25 steps`）让 `the_gate_message_describes_the_condition_the_gate_checks` **exit 101**（红在 `:590`）⇒ 文案层有测试兜底、非空洞。②**提示词排除集措辞**：`developer.md:36-42` 与 `:96-104` 现在都点明 `.hoh/**`、`.godot/**`、`.import/**`，与运行时排除集 `{.hoh,.git,.godot,.import}`（`policy.rs:37-47` + `adapter/godot.rs:3354-3358` + `config/hoh.yaml`）**前三个**一致。植入 `prompt-excludes-narrow`（两段一起退回只提 `.hoh/**`）让 `the_prompt_names_every_excluded_path_not_just_the_scratch_dir` **exit 101**（红在 `:614`）；**注意**：只退回 `[budget]` 一段时该测试**仍然绿**（因 `[definition-of-done]` 那段仍含 `.godot/.import`），两段都退回才红。**残余（DEF-C）**：`.git` 同样在排除集里而提示词与测试都没提，测试名 `names_every_excluded_path` 与报告 §4.3 的「现在提示词把它说全了」**言过其实**。③**「两条测试已改成可执行契约」的说法已收窄且准确**：我读了 `TASK-DR66-REPORT.md:265-277` 的收窄块与两个被点名测试的现状——`artifact_hygiene.rs:106-141` 与 `developer_contract.rs:49-99` **确实仍是 `contains` 断言**（对象换成交付文本、needle 换宿主方言、各加一条 Windows 反向断言），真正执行命令的是**新增文件** `tests/prompt_shell_contract.rs`/`tests/role_shell_contract.rs`（二者 `use mini_swe_agent::{Action, Environment, LocalEnvironment}` 并抽取—执行）。收窄块把「(a) 文案层加强」与「(b) 可执行契约」分开陈述，与事实一致。④其余 info 项的处置：报告 §8.2/§8.3 对 DEF-5/DEF-6/DEF-8 的处理与上述事实一致；DEF-4（附录 24 vs 21）与 lib 测试归属在 DR-67 报告里**未再更正**（DR-66 报告里的旧数字保留原样、未被标注，见 DEF-B 同类问题），DEF-7（`configured_excludes()` 直读 config）**已按选 (A) 一并修好**：`e1_increment.rs:60-64` 改为 `GodotAdapter::new(config.adapter.godot.clone(), false).cache_excludes()`，并在 `:84-102` 断言适配器答案与 `HashExcludes::new(adapter.cache_excludes()).merged()` 相等（我只读码，未对其单独植入）。"
    },
    {
      "id": "SUITE",
      "pass": true,
      "evidence": "①**先 `touch` 再跑门**：`find src tests -name '*.rs' -exec touch {} +`（78 个文件被 touch），随后 `cargo test --offline --no-fail-fast`（记录 `…\\dr67acc\\suite-inrepo.txt`，663 行）：`grep '^test result:' | awk '{p+=$4;f+=$6;i+=$8}'` ⇒ **passed=397 failed=0 ignored=7**，`EXIT=0`，`grep -c 'test result: FAILED'` = 0，`Compiling hof-rs` 出现 1 次；逐二进制 `lib=119`、`e1_increment=13`（8→13，+5，全部为本批新增）。②**排除陈旧产物**：`CARGO_TARGET_DIR=%TEMP%\\dr67acc\\clean-target CARGO_INCREMENTAL=0 cargo test --offline --no-fail-fast`（记录 `suite-clean.txt`，827 行）⇒ 同样 **397/0/7、EXIT=0、`Compiling hof-rs` 1 次**；跑完已删除 4.6 GB 的仓外 target。③**无既有测试被删/放宽/加 ignore**：`git diff 079cf82..HEAD -- tests/ | grep -c '^-.*#\\[(tokio::)?test\\]'` = 0、`^-.*fn [a-z_]` = 0、`^+.*#\\[(tokio::)?test\\]` = 21、`src/` 新增 `#[test]` 4 删除 0、`#[ignore` 新增/删除均为 0；`a54424b..HEAD` 的 `tests/` 删除行只有 7 行（§GATE_BROADENED ④ 逐条解释），无断言删除。④**仓内无临时测试残留**：`tests/dr67_probe.rs`/`dr67_probe2.rs`/`dr67_diag.rs` 的 `git log --all --diff-filter=A` 均 **0 命中**，仓内 `find . -name 'dr67*'` 为空。⑤基线对照：实现者自报基线 392/0/7；`git diff 079cf82..HEAD -- tests/` 的 `+21` 与 `src/` 的 `+4` 合计与 DR-66 的 +20/+16 自洽，392+5=397。"
    },
    {
      "id": "GUARDS",
      "pass": true,
      "evidence": "①`runs/**` **跑套件前后各测一次，逐字相同**：规范口径（复用 DR-54/57/59/61/62/64/66 的 `digest2.ps1`：递归 `-Force -File`、仓根相对路径小写、`\\`→`/`、三列 TAB（路径/字节长度/SHA256 小写 hex）、LF、无尾随换行、`Sort-Object`、整体 UTF-8 后 SHA256）——**口径自证** `runs/smoke-t6 files=135 digest=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03`（与任务书要求逐字一致）、`runs/smoke-t7 files=115 digest=6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7`、`runs files=5147 digest=01ff775e36935d3d92dab6919fe030389a8ff53483c52e87288ad711ec840dc3`（历史值），最新 mtime `2026-09-29 14:44:16`。②`.workspace/mario` **未动**：`files=259 digest=4e494547416b2e87ba025d686afef9447d4f92c027917d1790e6fc9deaeaa84a`（同 DR-59/61/62/64/66），最新 mtime `2026-09-29 14:32:28`。③`PRD-mario.md` sha256 = `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`、mtime `2026-09-20 23:21:21` ⇒ 未变。④`git diff --stat 079cf82..HEAD -- Cargo.toml Cargo.lock` = 空 ⇒ **无新依赖**；`git diff --cached --stat` = 空 ⇒ **未 stage**；`git status --porcelain -uall` = 空 ⇒ 仓内无临时物。⑤`git rev-parse origin/master` = `079cf82` ⇒ **未 push**。⑥**引擎树用嵌套仓**（D242）：`toplevel=F:/moonbit-hof-rs/godot-mcp/godot`、`HEAD=fc63af77c33368c4a1bb839c95d19750554f63a3`、`status --porcelain -uall` **0 行**、`ls-files=15049`、`modules/mcp_server=721`、`find godot-mcp/godot -newermt '2026-09-30 05:00'` **0 个**；外层 `ls-files godot-mcp`=**6484**（pathspec 真命中）、`ls-files godot-mcp/godot`=**0**（外层空判）、`git check-ignore -v` → `.gitignore:33:godot-mcp/godot/`。⑦**三个假绿陷阱逐一复现**：空 pathspec `git diff --stat -- definitely/not/a/real/path` 输出空且 **exit 0**；`bash`: `git rev-parse HEAD^` = `12e9052…` 而 `cmd //c \"git rev-parse HEAD^\"` = `8838b0a…`（= HEAD 本身，caret 被吃；`cmd //c \"echo A^B\"`→`AB`、`echo A^^B`→`A^B`）；外层不跟踪引擎树（0/6484）⇒ 外层 `git diff` 对引擎无证据力。⑧`DECISIONS.md` 我在验收期间未写；`git diff 566983f..HEAD -- DECISIONS.md` 为空（调度者在本批前的提交）。"
    }
  ],
  "defects": [
    {
      "id": "DEF-A",
      "severity": "major",
      "what": "**DEF-2 的闭合点（调用的那 6 行）没有任何可执行测试覆盖**。`cli_impl::run:604-614` 的 `Err` 分支才是「真实失败路径写两个落盘文件」的承重处，而全仓只有生产调用者 `src/cli.rs:208`；测试驱动的是同一批生产函数（`failed_run_summary` + `finalize_run`）与同一顺序，但**调用点本身**退化回 DR-66 的 `let summary = run_round_in(…)await?;` 后，套件**全绿**。这与 DEF-2 的原始形态完全同类（当初坏掉的正是「唯一 finalise 调用点不可达」），因此「下一次只需删/改调用点即可静默重开 DEF-2」这一风险是实的。实现者已在 `TASK-DR67-REPORT.md` §7-2 如实标注「`cli_impl::run` 整函数端到端未被执行」，故我不把它判成 fail，但它应被下一批当作首要遗留。",
      "reproduction": "`grep -rn 'cli_impl::run(' src/ tests/` ⇒ 只命中 `src/cli.rs:208`（生产）。我的植入 `caller-glue-off`（`plant.py`，把 `cli_impl.rs:604-614` 的 match 换回 `let summary = run_round_in(orchestrator, &spec, &run_id).await?;`）后：`cargo test --offline --test e1_increment` ⇒ `test result: ok. 13 passed; 0 failed; 0 ignored; …`，`CARGO_EXIT=0`（原始输出 `%TEMP%\\dr67acc\\my-plant-glue.txt`）。"
    },
    {
      "id": "DEF-B",
      "severity": "minor",
      "what": "**披露文件自身对 diff 的描述不准确，且有一行既有文字被静默删除**。`TASK-DR67-REPORT.md:96-99` 与 `:467` 声称 `git diff a54424b..e3f3cc8` 的「删除行只有 1 行，而那一行是把旧 §7-8 第 8 条挪进更正块之前、1 删 1 增的同一段」——**事实上第 8 条从未被删除**（我逐字比对确认 `TASK-DR66-REPORT.md:541` 与 `a54424b` 版相同），真正被删的是 `-## 附：本批 4 个提交（英文信息，均带 (DR-66)`，本地未 push）`（附录标题），**它没有被恢复**，附录代码块现在无标题地挂在 §9 之后；`TASK-DR66-REPORT.md:574` 的「§1–§8 与附录的既有文字**一个字都没有改动**」也因此不成立。这不改变三处被点名文字「原文保留 + 标注已更正」的成立，属自述失准 + 一处结构性标题丢失。同类遗留：DEF-4 里的两处旧误（附录 24 vs 实际、lib 测试归属）在 DR-66 报告里**既未更正也未标注**，DR-67 报告也没提。",
      "reproduction": "`git diff --stat a54424b..e3f3cc8 -- .spec/hof-rs/tasks/TASK-DR66-REPORT.md` ⇒ `1 file changed, 109 insertions(+), 1 deletion(-)`；`git diff a54424b..e3f3cc8 -- … | grep '^-[^-]'` ⇒ 唯一一行是 `-## 附：本批 4 个提交（英文信息，均带 `(DR-66)`，本地未 push）`；`grep -n '^## ' TASK-DR66-REPORT.md` 现在只有 §1–§9，无「附」标题。"
    },
    {
      "id": "DEF-C",
      "severity": "info",
      "what": "**提示词/测试对排除集的表述比事实宽**。运行时排除集是 `{.hoh,.git,.godot,.import}`，`developer.md` 只点名 `.hoh/**`、`.godot/**`、`.import/**`（`.git` 未提），而新测试名 `the_prompt_names_every_excluded_path_not_just_the_scratch_dir` 与报告 §4.3 的「现在提示词把它说全了」都声称覆盖了**全部**排除路径。实际行为正确（写 `.git/**` 也不产生增量），只是说明不完整。`configured_excludes()` 的断言（`:84-102`）也只枚举这 3 个（另加 `.git` 只在适配器答案的**相等断言**里间接出现）。",
      "reproduction": "`grep -n '\\.hoh|godot|import|git' src/prompts/developer.md | head`；`sed -n '60,102p' tests/e1_increment.rs`；排除集来源 `src/runtime/policy.rs:37-47`、`src/adapter/godot.rs:3354-3358`、`config/hoh.yaml`。"
    },
    {
      "id": "DEF-D",
      "severity": "info",
      "what": "**生产代码引入一处格式损坏**：`src/runtime/run_loop.rs:153` 现在是 `fn now_seconds() -> u64 {    SystemTime::now()`（函数体首个表达式被并到签名行），由 `2b6e943` 带进；功能无影响，但任何 `cargo fmt --check` 会报差异，且说明该提交的编辑未过格式化工具。",
      "reproduction": "`git show 2b6e943 -- src/runtime/run_loop.rs | grep -n -A1 'fn now_seconds'`；`sed -n '153p' src/runtime/run_loop.rs`。"
    },
    {
      "id": "DEF-E",
      "severity": "info",
      "what": "**报告 §6.5 的受控路径清单与其自己引用的诊断文件不一致**：`TASK-DR67-REPORT.md` §6.5 说仓外目录有 **23** 个文件并列出 23 个名字，其中**不含** `diag.txt`；但同一次更正（`8838b0a`）在 §6.4 写入「原始控制台输出见 `%TEMP%\\dr67\\diag.txt`」，而 `diag.txt` 现在的 mtime 与那次提交同刻（06:28），于是该目录实际是 **24** 个文件。另：`diag.txt` 是一份**人工整理的摘要**（含 `Raw output:` 小节），不是原始控制台转储本身。这不影响任何判据（其内容与「doctor 前置检查使 `cli_impl::run` 离线不可达」的结论自洽，我读码也确认 `doctor_checks` 项 3/4 是 `chat_probe`/`models_probe`），但属于取证措辞不精确。",
      "reproduction": "`ls -la /c/Users/wyl/AppData/Local/Temp/dr67/`（24 个文件，`diag.txt` size 1094，mtime 09-30 06:28）；`cat /c/Users/wyl/AppData/Local/Temp/dr67/diag.txt`；`sed -n '145,152p' src/cli_impl.rs`（`items.push(chat_probe(config)); items.push(models_probe(config));`）。"
    }
  ],
  "risks": [
    "**DEF-A 可直接重开 DEF-2**：删掉/改写 `cli_impl.rs:604-614` 的 6 行调用点，套件仍全绿（我实测 13/13 绿），而真实失败轮次又会不写 `runs/<id>/exit_code` 与 `meta.json.exit_code`。修复方向应是让 `cli_impl::run` 的失败路径可被执行（例如把 doctor 前置检查注入化），而不是再加一层只读断言。",
    "`run_round_in` 的**失败**传播没有直接测试：`run_round_in_still_runs_the_loop`（`tests/e1_increment.rs:435-463`）只跑 happy round。它是一行转发，风险低，但若有人把它改成吞错/包装错，现有测试只在 happy 路径与 `failed_run_summary` 上覆盖。",
    "失败路径上 `finalize_run` 会把 `meta.json.artifact_gate` **覆盖**为 `not_applicable(\"the round failed; no artifact gate was produced\")`（`cli_impl.rs:729-731`）。这是新增的落盘副作用，没有任何测试断言它；以 `meta.json.artifact_gate` 为判据的消费者若把 `applicable=false` 读成「无门槛」需被提醒（DR-27 契约原本只描述 `exit_code`）。",
    "`cli_impl::run` 在 doctor **之前**的失败（`run_dir` 已存在 `:552-558`、`--fresh/--reset` 互斥 `:517-522`、配置/规格加载失败）**仍不写**两个落盘位置——实现者 §7-4 已如实记录，本批未关闭；以这两个文件为唯一判据的启动器必须把「文件不存在」读作未知。",
    "K 步时限**仍不被运行时检查**（本批选择改文案）。若后续真要点名 K 的语义，必须先有自己的测量与测试，否则又会变成一个无人检查的措辞。",
    "非 Windows 的 `ShellFlavor::Posix` 分支只在编译期被选择（DR-66 遗留），跨平台采样仍可能在 Linux 上暴露新差异；编辑器侧异步落盘风险亦仍未测（DR-66 §7-4）。",
    "`TASK-DR66-REPORT.md` 的 §9 声称「附录既有文字一个字未改」而附录标题实际被删——后续考古该文件时应知道附录标题已不在，勿把 §9 当作 `a54424b` 版的全等副本。",
    "E1/E3 仍未 met 且本批无法验证：批内只证明「任何零工程增量的 Developer 阶段必然使轮次失败」与「两个落盘位置由真实错误类驱动」，下一轮真机 `A_1 != A_0` 仍未知（真机轮被禁止）。"
  ],
  "unverified": [
    "**`cli_impl::run` 的端到端执行**：我没有执行它。理由与实现者相同——`doctor_checks` 是强制前置（`cli_impl.rs:536-548`），项 3 `chat_probe` 会向模型端点发 `/chat/completions`、项 4 `models_probe` 查 LM Studio（`:149-152`），离线环境必然 `Ok(4)`；我读了代码确认这条链，但**没有**复现那次诊断（复现需要在仓内新建测试文件，超出「临时物建在仓外」的纪律）。因此「真实失败路径写两个位置」对我而言是**读码 + 各环节被执行**，不是单次端到端执行。",
    "**实现者自己的植入原始输出**：我只核了 `%TEMP%\\dr67` 里 7 份 `plant-*.txt` 的**存在性与文件名**，未逐份审计其内容，也没有重放它的 5 处植入；我以 §3 的 7 处**自己的**植入替代。",
    "**DEF-7（`configured_excludes()` 改走适配器）的非空洞性**：我只读码确认它现在调用 `GodotAdapter::cache_excludes()`，**没有**为它单独植入（例如让适配器硬编码追加一个排除项看测试是否跟随）。",
    "**非 Windows `ShellFlavor::Posix` 的真机行为**、**编辑器侧异步落盘**：未验证（DR-66 遗留，本批不涉及）。",
    "**E1/E3 是否 met**：未验证且本批无法验证（需真机轮，任务书禁止）。",
    "**397 个测试的逐条内部逻辑**：我核了聚合/逐二进制、`git diff` 的删除与新增计数、本批点名的全部目标测试与三处迁移夹具；其余既有测试只在「未删/未 ignore/未放宽」维度核对。",
    "**调度者两个文档提交（`12e9052`、`8838b0a`）的内容之外的正确性**：我只核了它们只含 `TASK-DR67-REPORT.md`、未改代码树，并读了 `8838b0a` 的完整 diff；报告其余文字的正确性按 §1 的判据项抽核。",
    "**`tests/prompt_shell_contract.rs` / `role_shell_contract.rs` 的真实执行**：我只确认它们 import 并构造 `LocalEnvironment`（DR-66 验收已用 `HOST→Posix` 植入证明过），本批没有重跑该植入。"
  ]
}
```

**总判：`verdict = pass`（8/8 criteria 通过）。**
一句话：**五件事都真的落地了——披露（含被丢弃的 6 个哈希、原因、未 push 即可接受、`--mixed` 错误机制的原文保留式更正）、`dr66-wip` 删除而对象/reflog 仍在、门拓宽到「任何零增量」且用 3 处「只增断言」的夹具迁移（我另做反例证明迁移是必要的而非装饰）、真实失败路径由 `failed_run_summary`+`finalize_run` 写出两个落盘位置、退出码跟着错误类走；套件在我 `touch` 后为 397/0/7 exit 0，并用仓外全新 target + `CARGO_INCREMENTAL=0` 复现；禁区全清。** 但它有两处需要下一批正视：**(1) 承重的 6 行调用点 `cli_impl.rs:604-614` 没有测试覆盖——我把它退回 DR-66 的 `?` 形态后套件仍 13/13 全绿，这是 DEF-2 原形态的一次静默重开路径；(2) 披露文件把唯一一行删除说错了（真正被删的是 DR-66 报告的附录标题，未被恢复），且 DR-66 报告 §9 声称附录一字未改。**

---

## 2. 逐项核对表（判据 §0 的五件事 + §1/§2 的门与约束）

| # | 判据 | 结论 | 我的自产证据 |
|---|---|---|---|
| 1 | **披露**：被丢弃哈希 / 原因 / 未 push 故可接受 / `--mixed` 错误描述「原文保留 + 标注」 | **pass（DEF-B）** | `TASK-DR66-REPORT.md:571-634`（§9）；`lo[0]==lc[0]` 为 True（260 字节逐字）；`:543-546` 更正块；`git diff a54424b..e3f3cc8` = +109/−1，唯一删除行 = 附录标题 |
| 2 | **分支卫生**：`dr66-wip` 已删、对象仍在、无 force-push | **pass** | `git branch -a` 只有 master/origin；`rev-parse dr66-wip` exit 128；6 个哈希 `cat-file -t`=commit；`fsck` dangling；`origin/master=079cf82` |
| 3 | **真实失败路径写两个落盘位置** | **pass（DEF-A）** | `run_loop.rs:404/475/957` + `cli_impl.rs:604-614/720-722`；测试 `e1_increment.rs:312-355` 走生产函数；植入 `persist-off` ⇒ 两测试红；植入 `caller-glue-off` ⇒ 13/13 仍绿（缺口） |
| 4 | **门拓宽 + 迁移夹具逐条判定** | **pass** | `run_loop.rs:912-923`；植入 `narrowing-restored` ⇒ `:542` 红 `ok:true`；三处迁移只增断言（`evidence_isolation.rs:277-290`、`evidence_unreachable.rs:364-378`、`tool_discovery.rs:348-389`）；植入 `isolation-migration-undone` ⇒ `:254` NoEngineeringWrite |
| 5 | **退出码跟错误类** | **pass** | `run_loop.rs:138-150` + `cli_impl.rs:701-706`；`e1_increment.rs:366-401`（2 与 4 两态）；植入 `code-constant` ⇒ `:390 left:2 right:4` |
| 6 | **info 三项**（门文案 / 排除集措辞 / 可执行契约收窄） | **pass（DEF-C）** | `run_loop.rs:930-939`；植入 `warning-k-steps` ⇒ `:590` 红；`developer.md:36-42/96-104`；植入 `prompt-excludes-narrow` ⇒ `:614` 红；`TASK-DR66-REPORT.md:265-277` 与两个 `contains` 测试实读 |
| 7 | **门**：`cargo test --offline` exit 0 / ≥392 / ignored 不增 / 无测试被删或放宽；先 `touch`；仓外 target 复现 | **pass** | `suite-inrepo.txt` 397/0/7 EXIT=0（`Compiling hof-rs`×1）；`suite-clean.txt`（仓外全新 target + `CARGO_INCREMENTAL=0`）397/0/7 EXIT=0；删除 `#[test]`=0、删除 fn=0、`#[ignore` 增减=0 |
| 8 | **禁区**：`runs/**`、mario、PRD、无新依赖、未 stage、`origin/master`、引擎树（嵌套仓）、三个假绿陷阱 | **pass** | 摘要复算 `smoke-t6=c144ef32…7a9c03`（自证）、`runs=5147/01ff775e…`、mario `259/4e494547…`（跑门前后各一次，值相同）；PRD sha `4c81c3a9…`；Cargo 零 diff；`diff --cached` 空；`origin/master=079cf82`；嵌套仓 `fc63af77…`/0 行/`ls-files 15049`；三陷阱输出见 §1 GUARDS ⑦ |

---

## 3. 我自己的植入与反例（全部逐字节回退）

方法：仓外 `C:\Users\wyl\AppData\Local\Temp\dr67acc\plant.py` 做**字节级**替换（`bytes` 读写，不经文本模式）：先断言 `old` 在该文件里**恰好出现 1 次**（多段编辑则每段各 1 次），再校验工作树字节 == `git cat-file blob HEAD:<path>`，把 pristine 字节备份到仓外，写入后才开跑。`restore` 用备份**逐字节回写**并 `cmp`；`verify` 打印 `bytes_now`/`cmp_bytes_equal`/`hash_object==HEAD blob`/`status`/`diffstat`。

**本仓实测为 LF**（`python eol.py`：`src/cli_impl.rs` CRLF 0 / bareLF 1028，`run_loop.rs` 0/1489，`developer.md` 0/131）；回退判据是四重的（`cmp` 字节 + `git status --porcelain` 空 + `git diff --stat` 空 + `git hash-object == HEAD:path`），因为 `core.autocrlf` 会让 `hash-object` 单看漏掉纯行尾差异。

| # | 记录名 | 文件（植入点） | 植入内容 | 目标测试 | CARGO_EXIT | 真实失败输出（原始日志） |
|---|---|---|---|---|---|---|
| 1 | `code-constant` | `src/runtime/run_loop.rs`（`failed_run_summary`） | `Some(exit_code_of(error))` → `Some(2)` | `e1_increment -- a_failed_round_persists_the_real_errors_class` | **101** | `tests\e1_increment.rs:390: assertion left == right failed: an external failure is class 4: the code must follow the error, not a literal  left: 2  right: 4` |
| 2 | `narrowing-restored` | `src/runtime/run_loop.rs`（门条件） | 加回 `exit_was_limits` 过滤（= DR-66 行为） | `e1_increment -- a_zero_increment_round_that_finishes_normally_also_fails` | **101** | `tests\e1_increment.rs:542: a zero-increment Developer round must fail whatever its exit status was: RunSummary { …, ok: true, …, failure_exit_code: None }` |
| 3 | `warning-k-steps` | `src/runtime/run_loop.rs`（门 warning 文案） | 文案改回 `spent its whole step budget … inside the first 25 steps` | `e1_increment -- the_gate_message_describes_the_condition_the_gate_checks` | **101** | `tests\e1_increment.rs:590: the gate message must not claim a step-budget or K-step check that does not exist` |
| 4 | `prompt-excludes-narrow` | `src/prompts/developer.md`（`[budget]` + `[definition-of-done]` 两段） | 两段一起退回只提 `.hoh/**` | `e1_increment -- the_prompt_names_every_excluded_path_not_just_the_scratch_dir` | **101** | `tests\e1_increment.rs:614: the prompt must account for the .godot exclusion it is subject to`。**附注**：只退回 `[budget]` 一段时该测试**仍绿**（另一段仍含 `.godot/.import`），两段都退回才红 |
| 5 | `persist-off` | `src/cli_impl.rs`（`finalize_run`） | 删掉 `std::fs::write(run_dir.join("exit_code"), …)` | `e1_increment -- a_zero_engineering_write_round_fails_instead_of_reporting_ok a_failed_round_persists_the_real_errors_class` | **101** | `tests\common\mod.rs:663` 两处 panic；`2 failed` |
| 6 | `caller-glue-off` | `src/cli_impl.rs`（`run` 的 Err 分支） | `match run_round_in(…)` 整段 → `let summary = run_round_in(…)await?;`（= DR-66 的 `?` 形态） | 整个 `--test e1_increment` | **0** | `test result: ok. 13 passed; 0 failed; 0 ignored; …` ⇒ **没有任何测试变红**（DEF-A 的证据） |
| 7 | `isolation-migration-undone` | `tests/evidence_isolation.rs`（**测试载体**，D253 显式说明） | 删掉 DR-67 新增的 `write(project.godot,"…# run-two")` + 其断言 | `evidence_isolation -- round_two_cannot_read_round_one_evidence` | **101** | `tests\evidence_isolation.rs:254: the round must run: contract violation: NoEngineeringWrite` ⇒ 迁移是必要的 |

**逐字节回退证据（7/7 全部满足四重判据）**

```
RESTORED src/runtime/run_loop.rs      bytes=67142 cmp_bytes_equal=True sha256 8c1fe14da2946899 == 8c1fe14da2946899   (code-constant)
RESTORED src/runtime/run_loop.rs      bytes=67142 cmp_bytes_equal=True sha256 8c1fe14da2946899 == 8c1fe14da2946899   (narrowing-restored)
RESTORED src/runtime/run_loop.rs      bytes=67142 cmp_bytes_equal=True sha256 8c1fe14da2946899 == 8c1fe14da2946899   (warning-k-steps)
RESTORED src/prompts/developer.md     bytes=6961  cmp_bytes_equal=True sha256 91d71d2e0da35efe == 91d71d2e0da35efe   (prompt-excludes-narrow)
RESTORED src/cli_impl.rs              bytes=39903 cmp_bytes_equal=True sha256 78363d8e1122f58f == 78363d8e1122f58f   (persist-off)
RESTORED src/cli_impl.rs              bytes=39903 cmp_bytes_equal=True sha256 78363d8e1122f58f == 78363d8e1122f58f   (caller-glue-off)
RESTORED tests/evidence_isolation.rs  bytes=12343 cmp_bytes_equal=True sha256 d8f2b2a247ec4694 == d8f2b2a247ec4694   (isolation-migration-undone)
VERIFY <each>: hash_object_matches_HEAD_blob=True ; status=<> diffstat=<>

# 全部回退之后
git status --porcelain -uall            -> (空)
git diff --stat                         -> (空)
git diff --cached --stat                -> (空)
src/cli_impl.rs        hash-object 1a232bd8…  == HEAD:src/cli_impl.rs
src/runtime/run_loop.rs hash-object 70399c54… == HEAD:src/runtime/run_loop.rs
src/prompts/developer.md hash-object 2b382619… == HEAD:src/prompts/developer.md
tests/evidence_isolation.rs hash-object == HEAD (MATCH)
```

---

## 4. 我对每个 headline 问题的独立判定

**4.1 历史改写是否已披露、且旧措辞是「保留 + 标注」而非静默替换？**
**是（有一条结构性的例外）。** 6 个哈希、reflog 原文、原因、未 push 的接受理由、`dr66-wip` 处置全部在 `TASK-DR66-REPORT.md` §9；被点名的三处旧文字（§7-8 机制描述、§2.3-③ 的「不再是常量 0」、§3.2-(A) 的落盘断言）与 §4 标题**全部原样保留**，各自下方有 `>` 更正/收窄块，且逐字比对确认 §7-8 那句与 `a54424b` 版相同。**例外**：`git diff` 里那唯一一行删除是 DR-66 报告的**附录标题**，它被删而未恢复，且报告把这一行描述成了另一处（DEF-B）。这不改变「被点名文字未被静默改写」的结论，但说明披露文本自身的取证描述不能全信。

**4.2 分支卫生？**
**全部满足。** 分支已删、`rev-parse` 失败、6 个对象 `cat-file` 仍为 commit、`fsck` 仍报 dangling、主 reflog 两条 reset 记录仍在、`origin/master` 仍是 `079cf82`、本批时间窗内无任何 `amend/reset/branch:`。

**4.3 真实失败路径是否真的写两个落盘位置？**
**是——但闭合点（调用那 6 行）没有执行覆盖。** 代码链完整且每个环节都有独立证据：目录与 meta.json 在任何角色之前创建（`:404/:475`）、门命中返回 `Err`（`:957`）、调用者的 `Err` 分支调用 `failed_run_summary` + `finalize_run`（`cli_impl.rs:604-614`）、`finalize_run` 写两个位置（`:720-722`）；测试用真实错误的 `failed_run_summary`（不再是手工 summary），并先断言缺口存在。我的 `persist-off` 植入让目标测试双红 ⇒ 落盘断言承重。**但**把调用点退回 `?` 形态后套件 13/13 全绿 ⇒ 「调用点是否调用 finalise」只能读码（DEF-A）。按判据「若真实失败路径仍不写两个位置则 fail」——它**写**，故判 pass。

**4.4 门是否真的拓宽、迁移是否削弱夹具？**
**拓宽为真、迁移是加强。** 门条件现在只剩哈希相等；我把收窄加回去后「正常结束 + 零增量」立刻回到 `ok: true`（红在 `:542`）⇒ 拓宽承重。三处迁移全是**只增**（新增真实工程写入 + 对应断言），`tests/` 的删除行只有 7 行且全部是无断言/注释/字段补全；我把 `evidence_isolation` 的迁移整段删掉后该测试立刻因 `NoEngineeringWrite` 变红 ⇒ 迁移是被拓宽逼出来的必要修复，而不是「为了让套件变绿而改测试」。

**4.5 退出码是否跟着错误类走（非空洞）？**
**是。** contract→2、External→4 两态都断言到两个落盘位置；把码改成常量 `2` 后 External 那条立即红在 `:390 left:2 right:4`。

**4.6 套件？**
**397 passed / 0 failed / 7 ignored，exit 0**，`touch` 先行，且用**仓外全新 target + `CARGO_INCREMENTAL=0`** 复现同值（`Compiling hof-rs` 各 1 次）⇒ 不是陈旧 rlib 造的。`ignored` 未增（7），无 `#[test]` 被删、无 `fn` 被删、无 `#[ignore` 新增。

**4.7 禁区？**
`runs/**`（5147/`01ff775e…`）、`.workspace/mario`（259/`4e494547…`）在**我跑套件前后逐字相同**；`smoke-t6=c144ef32…7a9c03` 口径自证通过；PRD sha 未变；Cargo 零 diff；未 stage；`origin/master=079cf82`；引擎树由**嵌套仓**证明未动（`fc63af77…`、0 行、`ls-files 15049`、外层空判 0/6484、pathspec 真命中）；三个假绿陷阱我逐个复现。

---

## 5. 未验证项与理由

1. **`cli_impl::run` 的端到端执行**：未执行。`doctor_checks`（`cli_impl.rs:536`）是强制前置且项 3/4 是 `chat_probe`/`models_probe`（`:149-152`，前者向 `/chat/completions` 发请求），离线必 `Ok(4)`；要独立复现需在仓内新建测试文件，与「临时物建在仓外」冲突。**理由**：任务书的离线硬约束。
2. **实现者的 5 处植入原始输出**：只核了 `%TEMP%\dr67\plant-*.txt`（7 份）的存在与文件名，未逐份审计、未重放；我用 §3 的 7 处自己的植入替代。**理由**：判据只要求我自产证据，不要求审计对方日志。
3. **DEF-7（排除集改走适配器）的非空洞性**：只读码，未植入。
4. **非 Windows 的 `ShellFlavor::Posix` 真机行为、编辑器侧异步落盘**：未验证（DR-66 遗留、本批不涉及）。
5. **E1/E3 是否 met**：未验证且本批不可验证（需真机轮，被禁止）。
6. **@397 个测试的逐条内部逻辑**：只核聚合/逐二进制/增删计数 + 本批点名的目标测试与三处迁移夹具。**理由**：验收判据的范围。
7. **两个新 shell 契约文件的执行**：只确认它们 import/构造 `LocalEnvironment`；未重跑 DR-66 的 `HOST→Posix` 植入。
8. **K 步时限**：确认它不被检查（读码），但**没有**测试覆盖「未来有人真的加计时门」这一情形——本批有意不改。

---

## 6. 我没有独立检查的部分

1. `src/adapter/godot.rs`、`src/prompts/mod.rs`、`src/runtime/policy.rs` 等**未被 DR-67 改动**的文件（`git diff a54424b..91f1b9c` 的 9 个文件之外），我只在需要时读了引用点。
2. `DECISIONS.md` D261/D262 之外的历史条目；D262 我读了全文并与我的 reflog/分支事实核对一致。
3. 调度者两个文档提交（`12e9052`、`8838b0a`）**内容之外**的正确性——我读了 `8838b0a` 的完整 diff 与报告 §6.4/§6.5 的现状。
4. `%TEMP%\dr67\plant-backup/**` 与 `%TEMP%\dr67\target` 的内容（只核目录存在；仓外 `dr67acc/clean-target` 是我自己的，已删）。
5. `TASK-DR67-REPORT.md` 里除 §1/§2/§3/§4/§5/§6/§7/§8/附 之外的逐句主张（我按 §1 的判据项抽核，未逐字通读它的每一句）。
6. 40+ 个测试二进制中我没有点名的那些测试的运行细节（只看聚合与增删）。

---

## 7. 给下一批的建议（**我不修任何东西**）

1. **先关闭 DEF-A**：让「失败定稿是调用者的职责」这件事**可执行地**被钉住。最小方向是把 `cli_impl::run` 的失败定稿路径做成可注入/可观测的（例如把 doctor 前置检查与 run 主体的编排抽成一个可直接调用的函数，或在测试里用一个返回 `Err` 的 harness + 假 doctor），断言「真实 dispatcher 入口的失败分支确实写下两个文件」。当前把它留在「同一批生产函数 + 同一顺序」的手工重放，与 DEF-2 当初的成因同型。
2. **补 `meta.json.artifact_gate` 被覆盖为 `not_applicable` 的断言或文档**：失败轮次的 meta.json 语义现在与成功轮次不同，且无测试。至少写进 DR-27 契约的文档，让消费者知道 `applicable=false` 可以有「轮次根本没走到 gate」这一含义。
3. **修 DEF-B**：恢复（或明确标注移除）DR-66 报告的附录标题；把 `TASK-DR67-REPORT.md:96-99/:467` 对 diff 的描述改成事实；顺手把 DR-66 报告里未更正的 DEF-4 两处数字（附录文件数、lib 测试归属）补标注——DR-66 报告已经成为后续批次的参考资料，它的自述错误会被继承。
4. **修 DEF-C**：`developer.md` 把 `.git` 也纳入说明（或明确写「除 harness 自身状态目录外」），并把测试名 `names_every_excluded_path` 改成与断言一致的措辞；报告 §4.3 的「说全了」应改成「点明了会改变增量的三个」。
5. **修 DEF-D**：跑一次 `cargo fmt`（或至少恢复 `now_seconds` 的换行），并考虑把 `cargo fmt --check` 纳入门，避免这类编辑残留。
6. **SMOKE-T8 的判据**仍应同时报出：`A_0`、`A_1`、Developer 的工程写入计数、`no_progress`/`no_engineering_write` 是否出现、进程退出码、以及 `runs/<id>/exit_code` 与 `meta.json.exit_code` 的**存在性**——不要让 exit 0 单独承载判定（沿用 DR-66 验收的建议 8）。
7. **不要把 DR-67 的绿当作 DEF-2 的端到端闭环**：它是「所有环节分别被测 + 调用点读码正确」；推送前请把 DEF-A 显式记入 DECISIONS 作为已知债务。

---

## 8. 诚实披露

1. **只读纪律**：除 §3 的 **7 处受控植入**（每处 `cmp` 逐字节回退、`git status`/`git diff --stat` 双空、`git hash-object == HEAD:path`）外，我未修改任何文件；未 commit/push/stage、未改写历史；本报告是仓内唯一新增文件（相对我开工时的 HEAD `91f1b9c`，报告在收工后才出现为未跟踪文件）。
2. **一次我自己造成并立即撤销的仓内误操作（如实记录）**：我第一次跑门时执行了 `find src tests -name '*.rs' -exec touch {} + ; touch build.rs 2>/dev/null`——`touch build.rs` 在本仓**创建了一个 0 字节的未跟踪 `build.rs`**，导致 `cargo test` 以 `error[E0601]: main function not found in crate build_script_build` 失败（EXIT=101）。我立即 `rm -f build.rs` 并复核 `git status --porcelain -uall` 只剩（当时的）未跟踪报告、`git ls-files build.rs` 与 `git log -- build.rs` 均无命中，随后重跑门得到 397/0/7。**没有任何被跟踪文件受影响**；这次失败不是实现者的问题，也不改变任何结论。
3. **离线纪律**：未启动 Godot、未碰端口、未联网、未调模型端点、未跑真机轮。全部操作：读文件、`cargo test --offline`（含一次仓外全新 target 的复现）、只读 git（含 reflog/fsck）、`grep`/`find`/`sha256sum`/`cmp`、仓外 Python/pwsh 脚本、pwsh 摘要复算。唯一的网络邻近动作是：我**没有**复现实现者那次会触发 `chat_probe` 的诊断。
4. **并发活动**：验收期间调度者落了 `12e9052`、`8838b0a` 两个**只含文档**的提交，HEAD 从 `91f1b9c` 移到 `8838b0a`（`ahead` 14→16）；我核实 `git diff 91f1b9c..8838b0a -- src tests Cargo.toml Cargo.lock` 为空 ⇒ 代码树未变、我的套件结论仍适用。这一移动**不是我造成的**。
5. **我没有「顺手修」任何东西**：DEF-A..DEF-E、K 不被检查、doctor 之前的失败不落盘、`artifact_gate` 被覆盖、E1/E3 未判，全部只报告。
6. **我的局限性**：本报告的肯定判定建立在「离线套件 + 我自设的 7 处植入 + 对生产调用链的阅读」上；凡属推断处已逐条标注（尤其 §5-1 的 `cli_impl::run` 端到端）。**不声称 E1/E3 已 met。**
7. **仓外临时物**：`C:\Users\wyl\AppData\Local\Temp\dr67acc`（`plant.py`、`eol.py`、`oldline.py`、`bak/**`、7 份 `my-plant-*.txt`、`suite-inrepo.txt`、`suite-clean.txt`）；一次性的仓外 `clean-target`（4.6 GB）**已删**。被本报告引用的原始产物全部保留在上述受控路径。仓内 `git status --porcelain -uall` 为空（相对 HEAD，除本报告）。

**报告写完后不再修改。**
