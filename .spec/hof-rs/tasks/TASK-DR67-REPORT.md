# TASK-DR67-REPORT — DR-66 收口：披露历史改写、清理 `dr66-wip`、处置 DEF-3（选 A 拓宽门）、让真实失败路径写出退出码

- 任务书：`.spec/hof-rs/tasks/TASK-DR67.md`（本报告的唯一任务来源）
- 落点：`F:\moonbit-hof-rs`（外层仓，`master`）。开工时 HEAD = `a54424b`（调度者刚把 `TASK-DR66-ACCEPTANCE.md`
  提交进来），收工时 HEAD = `91f1b9c`（本批 6 个 `(DR-67)` 提交，**未 push**）
- 性质：**离线收口批**。未启动 Godot、未碰端口、未联网、未调模型端点、未跑真机轮、未 `push`
- 仓外临时物：`C:\Users\wyl\AppData\Local\Temp\dr67`（脚本、备份、5 份植入原始输出、日志；仓内无临时物）
- 先读：`TASK-DR66-ACCEPTANCE.md`（判 fail 的验收）、`TASK-DR66-REPORT.md`、`DECISIONS.md` D261/D262
- 报告写完后不再修改

---

## 1. 结论 + 套件真实尾部 / 退出码

**结论：五件事全部落地。** 唯一判 fail 的披露项已补（含被丢弃的 6 个哈希、改写原因、为何未 push 即可接受、
以及 `--mixed` 机制描述的更正，旧措辞全部原样保留并标注）；`dr66-wip` 已按「先记录后删除、对象留 reflog」
处置；DEF-3 选 **(A) 拓宽门**并要求迁移了 3 个因此变红的既有夹具（逐条说明为何是加强）；DEF-2 让真实失败
路径真的把退出码写进两个位置、测试走真实路径、本报告就地更正 DR-66 的夸大表述；DEF-4..DEF-8 逐条处置。

**门（唯一权威）：`cargo test --offline`，且跑门前先 `touch`**（见 §5.5 的构建缓存陷阱）

```
$ find src tests -name '*.rs' -exec touch {} +          # 每次跑门前强制重编
$ cargo test --offline --no-fail-fast
...
test result: ok. 0 passed; 0 failed; 7 ignored; 0 measured; 0 filtered out; finished in 0.00s

聚合：passed=397  failed=0  ignored=7
EXIT=0
```

原始产物：`C:\Users\wyl\AppData\Local\Temp\dr67\final-suite.txt`（659 行）、
基线对照 `baseline-suite.txt`（822 行）、拓宽门后 `suite-after-fixes.txt`。

| 口径 | 基线（本批开工，`a54424b`） | 收工（`91f1b9c`） | 判定 |
|---|---|---|---|
| passed | **392** | **397**（+5） | 只增不减 ✔ |
| failed | **0** | **0** | ✔ |
| ignored | **7** | **7** | **未增加** ✔ |
| exit code | 0 | **0** | ✔ |

**`touch` 是必须的，而且本批真的需要它**：任务书点名的构建缓存陷阱是「`reset --mixed` 保留旧 mtime ⇒
cargo 复用旧 rlib ⇒ 假红/假绿」。本批的处置是两重的：①每次跑门（含每次植入）前 `find src tests -name
'*.rs' -exec touch {} +`；②把 `CARGO_TARGET_DIR` 指到**仓外**的 `%TEMP%\dr67\target`，从零重编一次
（`Compiling hof-rs v0.1.0` 出现且后续运行只 `Finished`），因此下面的 397/0/7 不是陈旧产物造的。
**我没有在本批做任何 `reset`/`--amend`**（见 §8.1），所以本批再无 mtime 陷阱来源，但纪律照旧执行。

**无既有测试被删/放宽/加 `#[ignore]`**（可复算）：

```
$ git diff 079cf82..HEAD -- tests/ | grep -c '^-.*#\[\(tokio::\)\?test\]'   -> 0
$ git diff 079cf82..HEAD -- tests/ | grep -c '^-.*fn [a-z_]'                -> 0
$ git diff 079cf82..HEAD -- tests/ | grep -c '^+.*#\[\(tokio::\)\?test\]'   -> 21
$ git diff 079cf82..HEAD -- src/   | grep -c '^+.*#\[test\]'                -> 4
$ git diff 079cf82..HEAD -- src/   | grep -c '^-.*#\[test\]'                -> 0
$ git diff 079cf82..HEAD -- src tests | grep -c '^+.*#\[ignore'             -> 0
```

「删除的测试/函数」两行都是 **0**：本批**没有删掉任何测试**，只删过本批自己的**临时诊断测试文件**
（`tests/dr67_probe.rs`、`dr67_probe2.rs`、`dr67_diag.rs`，均为本批新建、未进入任何提交、已在 §6.5 说明）。

逐二进制（最终套件）：lib **119**、`e1_increment` **13**、`result_semantics` **7**、`tool_discovery` **13**、
其余不变；`e1_increment` 由 8 → 13（+5，全部为本批新增）。

**不声称 E1/E3 已 met**（§7）。

---

## 2. 事一：披露本地历史改写 —— 落点与更正方式

**全部落点在 `.spec/hof-rs/tasks/TASK-DR66-REPORT.md`（旧节一字未改，只新增与就地更正）：**

| 内容 | 落点（文件:行） | 方式 |
|---|---|---|
| **新增披露节** | `TASK-DR66-REPORT.md:571`（`## 9. 【DR-67 新增】本地历史改写披露`） | **新增**，插在「附」之前；§1–§8 与附录原文未动 |
| 被丢弃的哈希 + reflog 原文 | `:578`（`### 9.1`） | 表格列 `81ec7c1`/`f0183fd`/`c5bb814`/`3944a14`/`e8a3d93`/`18bf417` + `cb50575`，并贴 reflog 原文 |
| 为什么改写 | `:610`（`### 9.2`） | 如实：提交信息被 shell 通配符污染（贴 `c5bb814` 正文里的 `%DST% …` 串）+ 尾提交两次 `--amend` |
| 为什么可接受 | `:621`（`### 9.3`） | **未 push**：`origin/master` 全程 `079cf82` 未动、无 upstream、被丢弃的 6 个提交不在任何 ref |
| `dr66-wip` 处置 | `:629`（`### 9.4`） | 先记录 `3944a14` 再删分支；未删对象/reflog |
| **更正 §7-8 的错误机制描述** | `:543`（紧接旧 §7-8 第 8 条下方的引用块） | **旧措辞原样保留在上**，引用块标注「§7-8 的机制描述错了，原文保留在上」 |

**更正 §7-8 的具体做法（关键：不静默改写）**：旧句子 `git reset --mixed 恢复文件时保留了旧 mtime`
**留在原处、一字未改**，其下立刻加一个 `>` 引用块：

> **【DR-67 更正：§7-8 的机制描述错了，原文保留在上】**
> `git reset --mixed` **不移动工作树**（不 `git checkout` 任何文件），它把 HEAD 与本仓索引重置到目标提交、
> **丢弃工作树之上的提交**；保留旧 mtime 的是**被丢弃的提交所留下的工作树文件**……正确描述见 §9。

同一原则用在另外两处被验收指为「夸大 / 混淆」的表述上：

| 被更正的旧文字 | 落点 | 处理 |
|---|---|---|
| §2.3-③「`runs/<id>/exit_code` 与 `meta.json.exit_code` **不再是常量 0**」 | `:145` 原文，`:147` 更正块 | 旧句保留；更正块写明 DEF-2 的真实情形（失败路径上 `finalize_run` **不可达**、那两个位置**根本不写**、断言支撑是**手工 `RunSummary`**），并指向本报告 §4 |
| §3.2-(A)「`finalize_run` 返回 2、`exit_code` 文件与 `meta.json.exit_code` 均为 2」 | `:230` 更正块 | 旧句保留；更正块区分「真实轮次写下的 `result.json`（成立）」与「对**手工对象**调用 `finalize_run`（不是真实轮次）」 |
| §4 标题「两条永远绿的测试」被读成「已变成可执行契约」 | `:265` 收窄块 | 旧文字保留；明确 **(a) 文案层加强** = 那两条**仍是 `contains`**、对象换成交付文本；**(b) 可执行契约** = `prompt_shell_contract.rs` / `role_shell_contract.rs` **两个新增文件**（DEF-8） |

**没有任何一处静默改写既有文字**：`git diff a54424b..e3f3cc8 -- .spec/hof-rs/tasks/TASK-DR66-REPORT.md`
的 **删除行只有 1 行**，而那一行是把旧 §7-8 的第 8 条**挪进更正块之前**、内容一字未改地重新出现
（`git diff` 里表现为 1 删 1 增的同一段）。这一点在 §8.3 里也如实说明。

---

## 3. 事二：`dr66-wip` 删除的真实输出

**先记录（删除前）**：`refs/heads/dr66-wip` 指向 `3944a1462cdf109da29280fd512928415ebf9c0c`，
无 upstream、未 push，与 `cb50575` 的差异为 **912 行插入 / 56 行删除（8 个文件）**；
其对象哈希与被丢弃的事实已写入 `TASK-DR66-REPORT.md:578`（§9.1）与 `:629`（§9.4）。
删除前原始输出：

```
$ git branch -avv
  dr66-wip              3944a14 fix(DR-66): render the prompt/tool-index/playbook shell syntax for the role's real shell
* master                566983f [origin/master: ahead 7] docs(spec): D262 and the DR-67 closing brief …
  remotes/origin/master 079cf82 docs(spec): D259 …
$ git rev-parse dr66-wip
3944a1462cdf109da29280fd512928415ebf9c0c
$ git cat-file -t 3944a14
commit
$ git diff --stat dr66-wip cb50575 | tail -1
 8 files changed, 912 insertions(+), 56 deletions(-)
```

**删除**：`git branch -D dr66-wip` → `Deleted branch dr66-wip (was 3944a14).`

**删除后的真实输出（本报告引用）**：

```
$ git branch -a
* master
  remotes/origin/master
$ git rev-parse dr66-wip
dr66-wip
fatal: ambiguous argument 'dr66-wip': unknown revision or path not in the working tree.
[exit code: 128]
$ git cat-file -t 3944a14
commit
$ git cat-file -t 81ec7c1 ; git cat-file -t f0183fd ; git cat-file -t c5bb814
commit
commit
commit
$ git cat-file -t e8a3d93 ; git cat-file -t 18bf417
commit
commit
$ git reflog --date=iso | grep -E "3944a14|dr66-wip|reset: moving"
079cf82 HEAD@{2026-09-30 03:39:26 +0800}: reset: moving to 079cf82
3944a14 HEAD@{2026-09-30 03:39:04 +0800}: commit: fix(DR-66): render the prompt/tool-index/playbook shell syntax for the role's real shell
079cf82 HEAD@{2026-09-30 03:39:03 +0800}: reset: moving to 079cf82
$ git fsck --no-progress --no-reflogs | grep 3944a14
dangling commit 3944a1462cdf109da29280fd512928415ebf9c0c
```

**对象/reflog 一个未删**：`3944a14` 仍可 `cat-file`、仍在主 reflog（`HEAD@{03:39:04}` 与
`HEAD@{03:39:26}: reset: moving to 079cf82` 两条都在）、`fsck` 报 dangling commit ⇒ 证据可完整取回。
`.git/logs/refs/heads/` 里**只剩 `master`**（`dr66-wip` 的 per-ref reflog 随分支删除，这是
`git branch -D` 的固有行为，且它记录的两条事实——`branch: Created from HEAD` / `branch: Reset to HEAD`
——已在删除前被摘录进 `TASK-DR66-REPORT.md:578`）。

---

## 4. 事三：DEF-3 —— **选 (A) 拓宽门**

### 4.1 选择与理由

**选 (A)**：让**任何**「Developer 阶段零工程增量」都失败，删掉 `exit_was_limits` 收窄。
理由不是「我倾向 A」，而是**收窄的理由本身被证伪后，收窄就没有理由了**，且它留着的那条残余假绿面
（正常结束却零增量仍报 `ok=true`/退出 0）正是 E1 关心的失败类。任务书 §0-3 的验收更正说得很清楚：
`tests/**` 全部 32 个（验收说 31 个，我的仓外普查是 **32** 个，见下）`FakeStep::new(Role::Developer)`
块里，唯一「只写 `.hoh/**`」的就是 DR-66 自己新增的 `tests/e1_increment.rs` 夹具。

**我自己重跑了这次普查**（仓外脚本 `%TEMP%\dr67\devsteps2.py`，与验收者的口径一致，但按
`FakeStep::new(Role::Developer)` 起块、取到下一个 `FakeStep::new(` 为止、抽 `.writing("…")` 的第一个参数）：

```
total Developer blocks: 32
EMPTY-WRITE step: tests/evidence_battery.rs:909
EMPTY-WRITE step: tests/result_semantics.rs:153
EMPTY-WRITE step: tests/wrap_up_budget.rs:243
blocks whose every write is under .hoh/ : 1
  tests/e1_increment.rs:188 ['.hoh/scratch/experiment.py', '.hoh/scratch/project.godot.pre_iter1']
```

原始输出：`%TEMP%\dr67\devsteps.txt`。数字与验收者的 31 差 1，因为验收者按「Developer 夹具块」计，
我按 `FakeStep::new(Role::Developer)` 计；**结论相同**（唯一 `.hoh/**`-only 的块是本批自己的夹具）。

**改动（`src/runtime/run_loop.rs:907-931`）**：
删掉 `no_engineering_write_attempt`（`.filter(|a| a.exit_was_limits)`）与 `let _ = attempt;`，
门条件从 `if let (true, Some(attempt)) = (h_dev_before == h_dev_after, …)` 变成
**`if h_dev_before == h_dev_after`**。DR-66 的 `no_progress` warning 保持原位不动。

### 4.2 因拓宽而变红的既有夹具：逐条、以及为什么每一条都是**加强**

拓宽后全量跑（`--no-fail-fast`，留档 `%TEMP%\dr67\suite-def3-nff.txt`）**红 3 条**，均在
「同一次共用 workspace 上跑多轮、且每轮写同一份 `project.godot` 字节」的场景里：

| # | 测试 | 红在哪 | 为什么它本来就是个**零增量**轮次 | 迁移方式 | 为什么这是**加强** |
|---|---|---|---|---|---|
| 1 | `tests/evidence_isolation.rs::round_two_cannot_read_round_one_evidence` | `:254` `the round must run: contract violation: NoEngineeringWrite`（第二轮） | 两轮都用 `happy_script()`，第二轮 Developer 写回**完全相同**的 `project.godot` 字节 ⇒ 工程树**一个字节没变** | 第二轮开始前先 `write(workspace/project.godot, "config_version=5\n# run-two\n")`，并断言这次写入生效 | 原夹具的「第二轮」其实什么也没改，隔离不变量是在一个**退化的轮次**上测的；迁移后第二轮**真的产生了工程增量**，隔离仍然成立 ⇒ 断言的对象更强，不是放宽 |
| 2 | `tests/evidence_unreachable.rs::the_tester_candidate_view_never_carries_the_previous_rounds_evidence` | `:201` 同上（第二轮） | 同上（`happy_script()` 两轮） | 第二轮前写 `project.godot`（第二轮探针内容）**并**新写 `scripts/round_two.gd` | 同上；且这正是**真实场景的形状**（第二轮开在上一轮已经改过的项目上） |
| 3 | `tests/tool_discovery.rs::a_project_only_command_is_not_a_harness_read`（连带 `enumerating_the_harness_root_is_recorded_as_a_warning`、`a_recursive_hoh_search_is_recorded_as_a_warning` 的共用 helper） | helper `warnings_for_developer_command` 的 `result.expect(...)` | helper 在**同一个 temp root** 上被调 3 次，`FakeStep` 每次都写同一份 `project.godot` ⇒ 第 2、3 次是零增量 | helper 每次调用写一个**调用唯一**的工程文件 `scripts/developer_write.gd`（内容含自增 nonce），Developer 步自身不再写 `project.godot` | 原 helper 的重复调用在**第 2 次之后就什么都没改**，而它断言的是「trace 只报告、不改变轮次结果」；迁移后**每一次调用都是一个真轮次**，同一断言在真轮次上成立 ⇒ 加强 |

**这三条都不是被删除、被 `#[ignore]`、也不是被放宽**：断言数只增不减（见 §1 的删除行计数为 0），
且每条的迁移都附加了「该轮次真的有增量」这一前提。**逐条 diff 见 `git show 2b6e943 -- tests/`**。

### 4.3 拓宽的残余面（诚实）

- 门现在只对「Developer 阶段前后工程哈希相等」敏感。**它的定义就是 E1**（「Developer 产出一个工程增量」），
  所以这条门**没有残余假绿面**了：正常结束、`LimitsExceeded`、被 harness 侧限制挡住——只要工程树没变，就失败。
- 新增一个反向夹具 `e1_increment::a_zero_increment_round_that_finishes_normally_also_fails` 钉住这一点，
  且**它先红**（见 §5.1）：修前它的真实输出是
  `a zero-increment Developer round must fail whatever its exit status was: RunSummary { … ok: true, … }`。
- 已知的**非**假绿面：一个「只改了被排除路径（`.hoh/**`、`.godot/**`、`.import/**`）」的轮次仍然算零增量而失败
  ——这是**有意的**，并且现在提示词把它说全了（§5.4 / DEF-6）。

### 4.4 「同名同数」：提示词与运行时的 K 仍是同一个数

任务书要求「无论哪条，都要更新 `developer.md` 的 `[budget]` 措辞与门/提示词保持**同名同数**」。
本批的选择是：**K 是提示词的指令，不是运行时的检查**，因此：

- `src/runtime/run_loop.rs:47-66` 的 `developer_write_deadline()` **签名与算法一行未动**，仍是
  `min(step_limit/4, wrap_up_steps).max(1)` = **25**；提示词 `{{write_deadline_steps}}` 仍由它渲染，
  `[budget]` 仍写 `Within your first {{write_deadline_steps}} steps`；测试
  `the_developer_prompt_states_the_write_deadline_the_runtime_computes` 仍断言渲染文本含 `first 25 steps`
  且 K == 25、K <= `wrap_up_steps`。⇒ **提示词与运行时用同一个数，且是同一个函数算出来的。**
- 改的是**运行时消息的措辞**：门命中时的 warning 不再声称「spent its whole step budget …
  inside the first {K} steps」（那是一个**从未被检查**的条件，DEF-5），改成如实描述
  「ended with no engineering write: no file in the artifact tree outside the hash-excluded runtime paths changed」。
- 函数文档现在**显式写明** `developer_write_deadline` 只是发给 Developer 的指令、运行时不把它与步数比较
  （`src/runtime/run_loop.rs:47-66` 的 DR-67 段），并说明为何**不**选「真的检查 K」：
  一个在第 26 步才合理开始写的 agent 会被字面计数器误杀，要做这件事得先有它自己的测量。

---

## 5. TDD 与非空洞性证据

### 5.1 先红后绿（第 3、4 件）

**(a) DEF-3 拓宽门 —— 先红**。新增 3 个夹具后、改门之前，`cargo test --offline --test e1_increment`
（原始输出 `%TEMP%\dr67\red-def3.txt`）真实失败（`EXIT=101`，`8 passed; 3 failed`）：

```
thread 'a_zero_increment_round_that_finishes_normally_also_fails' panicked at tests\e1_increment.rs:392:10:
a zero-increment Developer round must fail whatever its exit status was: RunSummary { run_id: "run-1", …,
ok: true, artifact_gate: ArtifactGate { applicable: false, launchable: true, … }, … }

thread 'the_gate_message_describes_the_condition_the_gate_checks' panicked at tests\e1_increment.rs:440:5:
the gate message must not claim a step-budget or K-step check that does not exist:
contract violation {} (the developer stage spent its \ whole step budget with no engineering write inside the first \
{first_write_deadline} steps: …

thread 'the_prompt_names_every_excluded_path_not_just_the_scratch_dir' panicked at …
```

`ok: true` 那一条**就是** DR-66 §7-3 承认的残余假绿面在真实路径上的复现。改门后同文件
`11 passed; 0 failed`（`green-def3.txt`）。

**(b) DEF-2 失败路径落盘 —— 先红（这次是"先红"而非"先绿"）**。收口前的 `tests/e1_increment.rs`
对两个落盘位置的断言用的是**手工构造的 `failed_summary()`**；本批改成走真实路径后，新增断言
「失败轮次此刻**还没有** `runs/run-1/exit_code`、`meta.json` 里**没有** `exit_code`」——
这正是 DEF-2 的缺口本身，收口前它必然为真（真），而随后由真实错误驱动的落盘必然使后续断言为真；
修前 `finalize_run` 在 `Err` 路径不可达 ⇒ 若不修 `cli_impl::run`，这两个断言之后就不会有任何文件，
`read(exit_code)` 会 panic。**这条"红"的可复算证据**是 §5.3 的植入 **P1b**：
把 `run_exit_code_for` 里携带码的分支删掉后，`a_failed_round_persists_the_real_errors_class` 红在
`left: 2 right: 4`（即「按真实错误类落盘」这件事真的承重）。

### 5.2 5 处受控植入（**全部落在生产代码**），各自让对应测试红

方法：仓外 `%TEMP%\dr67\plant.py` 做**字节级**替换（先断言 `old` 在该文件里恰好出现 1 次再写），
植入前把 pristine 字节（**取自 `git cat-file blob HEAD:<path>`**，与工作树字节相同，脚本会先校验
`sha256(HEAD blob) == sha256(worktree)`）存到仓外备份，植入后立即用备份**逐字节回写**。
每次植入用 `cargo test --offline --test <bin> -- <name>` 单点跑。5 份原始输出留在仓外受控路径：
`%TEMP%\dr67\plant-<id>.txt`。

| # | 记录名 | 文件:行（植入点） | 植入内容 | 目标测试 | CARGO_EXIT | 真实失败行（原始输出） |
|---|---|---|---|---|---|---|
| P1 | `p1-summary-drops-the-code` | `src/runtime/run_loop.rs`（`failed_run_summary` 的 `failure_exit_code`） | `Some(exit_code_of(error))` → `None` | `e1_increment -- a_failed_round_persists_the_real_errors_class` | **101** | `tests\e1_increment.rs:377: assertion \`left == right\` failed: the summary must carry the code of the error it was built from  left: None  right: Some(2)` |
| P1b | `p1b-exit-code-ignores-the-error` | `src/cli_impl.rs`（`run_exit_code_for` 的携带码分支） | 整段 `if let Some(code) = summary.failure_exit_code { … return code; }` 删除 | 同上 | **101** | `tests\e1_increment.rs:390: assertion \`left == right\` failed: an external failure is class 4: the code must follow the error, not a literal  left: 2  right: 4` |
| P1c | `p1c-run-round-in-stubbed` | `src/cli_impl.rs`（`run_round_in` 体） | `run_loop::run(...).await` → `Err(anyhow!("planted"))` | `e1_increment -- run_round_in_still_runs_the_loop` | **101** | `tests\e1_increment.rs:454: a happy round must complete through the dispatcher's round half: planted` |
| P2 | `p2-narrowing-restored` | `src/runtime/run_loop.rs`（门条件） | 重新加回 `exit_was_limits` 收窄（等价于 DR-66 的行为） | `e1_increment -- a_zero_increment_round_that_finishes_normally_also_fails` | **101** | `tests\e1_increment.rs:540: a zero-increment Developer round must fail whatever its exit status was: RunSummary { …, ok: true, …, failure_exit_code: None }` |
| P3 | `p3-warning-claims-k-steps` | `src/runtime/run_loop.rs`（门 warning 文案） | 文案改回 `spent its whole step budget with no engineering write inside the first 25 steps` | `e1_increment -- the_gate_message_describes_the_condition_the_gate_checks` | **101** | `tests\e1_increment.rs:590: the gate message must not claim a step-budget or K-step check that does not exist: contract violation {} (the developer stage spent its whole step budget \ with no engineering write inside the first 25 steps …` |

**P3 的第一版是编译错（`cannot find value first_write_deadline`），我没有把它当作"红"**：改成
自包含的 `25` 字面量后重跑，才得到上面这条**断言失败**——这一点如实记下，避免把「编译不过」混作证据。

### 5.3 逐字节回退（四种独立证明 ×5）

每处植入回退后的真实输出（同一脚本，逐条贴在 `plant-<id>.txt` 尾部，下面是汇总）：

| # | 文件 | `cmp`/字节比较 vs 备份 | `git status --porcelain -uall -- <file>` | `git diff --stat -- <file>` | `git hash-object` == `HEAD:<file>` |
|---|---|---|---|---|---|
| P1 | `src/runtime/run_loop.rs` | `cmp_bytes_equal=True`（67142 B，sha256 同 `8c1fe14d…`） | 空 | 空 | ✔ `70399c54…` |
| P1b | `src/cli_impl.rs` | `cmp_bytes_equal=True`（39903 B，sha256 同 `78363d8e…`） | 空 | 空 | ✔ `1a232bd8…` |
| P1c | `src/cli_impl.rs` | `cmp_bytes_equal=True`（39903 B，sha256 同 `78363d8e…`） | 空 | 空 | ✔ `1a232bd8…` |
| P2 | `src/runtime/run_loop.rs` | `cmp_bytes_equal=True`（67142 B，sha256 同 `8c1fe14d…`） | 空 | 空 | ✔ `70399c54…` |
| P3 | `src/runtime/run_loop.rs` | `cmp_bytes_equal=True`（67142 B，sha256 同 `8c1fe14d…`） | 空 | 空 | ✔ `70399c54…` |

**(c) 为什么必须加 `cmp`/字节比较（本仓 CRLF 敏感）**：`core.autocrlf=true`，`.gitattributes` 只把
`tests/fixtures/dr58/**` 钉为 `-text`。`git hash-object` 走的是**过滤器规范化后**的内容，纯行尾变化
可能让它在 `hash-object` 下仍然相等。所以回退判据是**四重**的：`cmp`（字节） + `git status` 空 +
`git diff --stat` 空 + `git hash-object == HEAD blob`。DR-66 报告 §5.3-(d) 记过一次真实的整份行尾事故
（Python 批量改写 `run_loop.rs` 把 CRLF 变 LF），本批的处置是：**所有植入/回退脚本都用
`read_bytes`/`write_bytes`（Python `bytes`），不经文本模式、不传 `newline=`，也不做任何 `sed`/`text.replace`
式的重写**；因此不存在把行尾改掉的路径。工作树上这些文件当前都是 **LF**（`grep -c $'\r'` = 0），
回退后字节数与 HEAD blob 完全一致。

**关于"植入落在测试载体"**：本批**没有**测试载体植入。P1/P1b/P1c/P2/P3 **全部**在生产代码里
（D253 要求的显式说明因此是"不适用：无测试侧植入"）。这一点是特意做的——本批的第一版曾把
`persist_failed_round_exit_code()` 这个**测试侧**开关当作 P1 的植入点，我把那次实测到的问题如实记在
§8.4：它在单点跑里**没有变红**，说明那个开关（以及当时在 `cli_impl::run` 里的分支）**不可观测**，
所以我删掉了它并重构（见 §8.4）。

### 5.4 新增/改动的测试（可执行需求文档）

| 测试 | 断言什么 | 为什么不是恒绿 |
|---|---|---|
| `e1_increment::a_zero_increment_round_that_finishes_normally_also_fails` | Developer **正常结束**（`attempt log` 里 `exit_was_limits=false`、`exit_status="Submitted"`）且零增量 ⇒ 轮次必须失败、`result.json.ok=false`、warnings 含 `no_engineering_write` | 修门前它红在 `ok: true`（§5.1a）；P2 也让它红 |
| `e1_increment::the_gate_message_describes_the_condition_the_gate_checks` | 门 warning 文案**不得**出现 `step budget` / `within the first`，**必须**出现 `no file` 与 `excluded` | P3 让它红（§5.2） |
| `e1_increment::the_prompt_names_every_excluded_path_not_just_the_scratch_dir` | 交付提示词必须提到 `.hoh`、`.godot`、`.import`，且这三个**真的**在 `configured_excludes()` 里 | 修文案前它红（§5.1a） |
| `e1_increment::a_failed_round_persists_the_real_errors_class` | 用**真实错误**驱动 `failed_run_summary` + `finalize_run`：contract 类 → 两个位置都是 `2`；**External 类 → 都是 `4`**（`2` 是 `!ok` 回退分支也会给的数，`4` 才是"码跟着错误走"的证据） | P1、P1b 各让它红（§5.2） |
| `e1_increment::a_zero_engineering_write_round_fails_instead_of_reporting_ok`（改） | 先断言失败轮次**尚未**写两个位置（DEF-2 缺口），再走真实路径写下并断言两处一致 | 见 §5.1b 与 P1b |
| `e1_increment::run_round_in_still_runs_the_loop` | `cli_impl::run_round_in` 必须真的跑轮次：返回 `iterations_completed == 1`，且 `runs/run-1/iter-1/result.json` 存在 | P1c 让它红（只返回 `Err` 的桩会被这条抓住） |
| `e1_increment::the_runtime_exclude_set_comes_from_the_configuration`（改，DEF-7） | 排除集改从 **`GodotAdapter::cache_excludes()`** 派生，并断言适配器当前答案是 `[.hoh,.git,.godot,.import]`、且 `configured_excludes() == HashExcludes::new(adapter.cache_excludes()).merged()` | 适配器在配置之外硬编码追加排除项时，从 config 直读的旧写法不会跟随；现在会 |

---

## 6. 禁区自查（真实输出）

### 6.1 引擎树未改 —— 用**嵌套仓**，且证明 pathspec 真能命中

```
$ git -C godot-mcp/godot rev-parse --show-toplevel
F:/moonbit-hof-rs/godot-mcp/godot
$ git -C godot-mcp/godot rev-parse HEAD
fc63af77c33368c4a1bb839c95d19750554f63a3
$ git -C godot-mcp/godot status --porcelain -uall | wc -l    -> 0
# ---- 非空洞性：这个仓/这条命令确实能看见东西 ----
$ git -C godot-mcp/godot ls-files | wc -l                     -> 15049
$ git -C godot-mcp/godot ls-files modules/mcp_server | wc -l  -> 721
$ git ls-files godot-mcp/godot | wc -l                        -> 0      # 外层不跟踪引擎树
$ git ls-files godot-mcp | wc -l                              -> 6484   # 但外层确实跟踪 godot-mcp/
```

⇒ 引擎"未变更"的结论**只**来自嵌套仓 `status` + `ls-files` 计数与 mtime，**没有**用外层 `git diff`。
未启动 Godot（无真机轮），未碰 9877/9878 等端口。

### 6.2 `runs/**` 与 `.workspace/mario/**` 未动

```
$ find runs -type f -newermt '2026-09-30 05:00' | wc -l                       -> 0
$ find runs -type f -printf '%T+ %p\n' | sort -r | head -1
2026-09-29+14:44:16.4036646000 runs/smoke-t7-experiment/e5_hash_tree.json
$ find .workspace/mario -type f -newermt '2026-09-30 05:00' | wc -l           -> 0
$ find .workspace/mario -type f -printf '%T+ %p\n' | sort -r | head -1
2026-09-29+14:32:28.7396764000 .workspace/mario/.godot/editor/editor_layout.cfg
```

`runs/**` 最新 mtime 比本批首次写盘早约 14 小时 ⇒ 本批没有写 `runs/**`（也没有跑 `hoh run`）。

### 6.3 PRD 未改、无新依赖、未 push、仓内无临时物

```
$ sha256sum .spec/hof-rs/PRD-mario.md
4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a  *.spec/hof-rs/PRD-mario.md
$ ls -la --time-style=full-iso .spec/hof-rs/PRD-mario.md
-rw-r--r-- 1 wyl 197609 5375 2026-09-20 23:21:21.766695900 +0800 .spec/hof-rs/PRD-mario.md
$ git diff --stat 079cf82..HEAD -- Cargo.toml Cargo.lock
(空)
$ git status -sb
## master...origin/master [ahead 14]
$ git rev-parse origin/master
079cf828658ec269e51824f5c643ba548ed0a08a
$ git status --porcelain -uall
(空)
$ git diff --stat 566983f..HEAD -- DECISIONS.md
(空)
```

⇒ PRD sha 与 D243/`meta.json.spec.sha256` 一致；`Cargo.{toml,lock}` 自基线零 diff ⇒ **无新依赖**；
`origin/master` 仍是 `079cf82` ⇒ **未 push**（`ahead 14` 是本批 6 个 + 调度者在本批期间落的若干提交，
见 §8.5）；`git status` 空 ⇒ **仓内无本批临时物**；**`DECISIONS.md` 我一个字节没碰**（任务书禁止）。
仓根另有一个既有、被 `.gitignore` 忽略的 `%DST%/` 目录（mtime 2026-09-24，早于本批），**不是**本批产物。

### 6.4 离线纪律

未启动 Godot、未碰端口、未联网、未调模型端点、未跑真机轮、未 `push`（含 `--all`）。
一次**试图**用真实 dispatcher 的离线诊断（一次性测试文件 `tests/dr67_diag.rs`，只存在于诊断期间、
从未提交、随后删除；原始控制台输出见 `%TEMP%\dr67\diag.txt`）证明 `cli_impl::run` 在本环境
**不可达**：它跑完 doctor 后返回 `Ok(4)`（`hoh run: pre-flight checks failed`），因为
`doctor_checks` 的第 3/4 项要求 model/chat 探针——这正是我不能在测试里驱动它的原因（§8.4），
也是本批**没有**把它变成测试夹具的诚实边界。

### 6.5 仓外临时物 + 被报告引用的原始产物

```
$ cygpath -w "$TEMP/dr67"
C:\Users\wyl\AppData\Local\Temp\dr67
$ find /c/Users/wyl/AppData/Local/Temp/dr67 -maxdepth 1 -type f | wc -l
23
$ find /c/Users/wyl/AppData/Local/Temp/dr67 -maxdepth 1 -type f -printf '%f\n' | sort
baseline-suite.txt  commit-msg.txt  devsteps.py  devsteps.txt  devsteps2.py  final-suite.txt
green-def3.txt  head-cli_impl.rs  plant-p1-failed-round-not-persisted.txt
plant-p1-persistence-disabled.txt  plant-p1-summary-drops-the-code.txt
plant-p1b-exit-code-ignores-the-error.txt  plant-p1c-run-round-in-stubbed.txt
plant-p2-narrowing-restored.txt  plant-p3-warning-claims-k-steps.txt  plant.py  red-def3.txt
report-gate.txt  suite-after-def3.txt  suite-after-fixes.txt  suite-def3-fixed.txt
suite-def3-nff.txt  suite-def3.txt
```

内容：`plant.py`、`devsteps.py`/`devsteps2.py`、`baseline-suite.txt`、`suite-def3.txt`、`suite-def3-nff.txt`
（= 报告中提到的 `suite-def3-nofailfast` 留档）、`suite-def3-fixed.txt`、`suite-after-fixes.txt`、
`final-suite.txt`、`report-gate.txt`、`red-def3.txt`、`green-def3.txt`、`devsteps.txt`、
`plant-<id>.txt`（**7 份**植入原始输出，其中 `plant-p1-failed-round-not-persisted.txt` 与
`plant-p1-persistence-disabled.txt` 是 §8.4 里那两次**没有变红**的第一版记录的原始留档）、
`plant-backup/**`、`commit-msg.txt`、`head-cli_impl.rs`（§6.5 之外的一次手工回退所用的 HEAD blob，
见 §6.5 末）。**被本报告引用的原始产物全部保留在上述受控路径**，报告写完后不再修改，故不做清理
（与 DR-66 的做法一致）。仓内 `git status --porcelain -uall` 为空。

**我删掉的仓内文件**（仅限本批自建的临时诊断测试，从未进入任何提交）：
`tests/dr67_probe.rs`、`tests/dr67_probe2.rs`、`tests/dr67_diag.rs`（`git status` 空、`git log` 里无它们，
可用 `git log --all --diff-filter=A -- tests/dr67_probe.rs` 复核为 0 命中）。

---

## 7. 遗留风险与未验证项（严格区分实测 / 推断）

**实测（有原始输出，可重跑）**

1. 套件 **397 passed / 0 failed / 7 ignored、exit 0**；`touch` 先行、仓外 target 全新编译印证（§1）。
2. 拓宽后的门对「正常结束（`Submitted`）+ 零增量」真的失败（§5.1a），且 P2 把它复原成旧行为时同一测试
   立刻变红（§5.2）。
3. 真实失败路径的两个持久化位置由**真实错误**驱动写出：contract→2、External→4，两处一致（§5.4）；
   P1/P1b 各自让它红（§5.2）。
4. 5 处植入全部在生产代码、全部 exit 101、逐字节回退（`cmp` + status + diff + hash-object 四重，§5.3）。
5. 禁区全清（§6）：嵌套仓 `fc63af77…`/0 行、`runs` 与 mario 窗口内 0 新文件、PRD sha `4c81c3a9…`、
   `Cargo` 零 diff、`ahead 14` 未 push、仓内干净、无新依赖。
6. `dr66-wip` 删除后 `rev-parse` 失败、`cat-file -t 3944a14` 仍为 `commit`、reflog 两条仍在（§3）。

**推断 / 未验证（不得当作已证）**

1. **E1/E3 是否 met —— 未验证，且本批无法验证**（需真机轮，任务书禁止）。本批只证明「零增量必然变红、
   且两处落盘反映真实失败类」，**不能**证明下一轮真机 `A_1 != A_0`。
2. **`cli_impl::run` 的完整函数未在测试中执行过**：它的 doctor 前置检查需要 model/chat 探针。
   本批把「失败定稿」抽成 `run_round_in`（轮次部分）+ 调用者的错误分支，测试驱动的是**同样的两个生产函数、
   同样的顺序、同样的真实 `anyhow::Error`**；**但"整函数端到端"属于未验证**。任何声称"测试覆盖了
   `cli_impl::run`"的说法都是推断。
3. **K 步时限不检查**：这是**本批的设计选择**（改文案而非加计时门）。若将来有人要真的检查 K，
   必须先有它自己的测量与测试；`developer_write_deadline` 的文档已写明这一点。
4. **`failure_exit_code` 只覆盖 `run_loop::run` 的失败**：`cli_impl::run` 里 **doctor 之前**的失败
   （配置错误、`--fresh-workspace` 与 `--reset-workspace` 互斥、run 目录已存在）**不会**写那两个位置
   （那时 `run_dir` 可能还不存在）。这是**有意的最小改动**：那些失败的进程退出码仍由 `cli_main_entry`
   给出（2/4），但 `runs/<id>/exit_code` 不存在。**以这两个文件为唯一判据的启动器**应把"文件不存在"
   读作"未知"而不是 0——这一点在 DR-66 验收 §risks 里已提过，本批**没有**关闭它，如实记录。
5. **非 Windows 的 `ShellFlavor::Posix` 分支**（DR-66 遗留）仍未在真机 POSIX 上跑过，本批不涉及。
6. **编辑器侧异步落盘**仍未测（DR-66 §7-4 遗留），本批不涉及。

---

## 8. 诚实披露

1. **我没有改写任何本地历史**：本批**没有** `git reset`、**没有** `git commit --amend`、**没有** rebase、
   没有创建/删除任何分支（唯一的分支操作是任务书要求的 `git branch -D dr66-wip`，见 §3）。
   6 个提交全部是**新增**提交：`e3f3cc8`、`2b6e943`、`2cf44e7`、`0685059`、`aa08855`、`91f1b9c`。
   可用 `git reflog --date=iso` 复核：本批时间窗内没有任何 `reset`/`commit (amend)`/`branch:` 记录。
2. **我没有改任何禁区**：未启动 Godot、未碰端口、未联网、未调模型端点、未跑真机轮、未写 `runs/**`、
   未改 `.workspace/mario/**`、未改 `PRD-mario.md`、**未改 `DECISIONS.md`**、未改 `godot-mcp/godot/**`、
   未 push、未改 `Cargo.{toml,lock}`。
3. **§2 的更正方式有一点必须说清**：DR-66 报告里那三处旧文字**全部原样保留**并各自带一个
   `>` 更正/收窄块；唯一在 `git diff` 里表现为「删除」的一行是旧 §7-8 第 8 条被**搬进**更正块上方
   （内容一字未改）。我没有在任何地方用新文字覆盖旧文字。
4. **我遇到的第一个"植入不红"是真的**，不是包装：第一版把 P1 的植入点放在 `src/cli_impl.rs` 的
   `persists_failed_round_exit_code()`（以及后来放回 `cli_impl::run` 的错误分支）——**两次跑都是
   `CARGO_EXIT=0`（绿）**。诊断后确认 `cli_impl::run` 在本环境**不可达**（doctor 要 model/chat 探针），
   所以那个分支**不可观测**。处置：删掉测试侧开关、把轮次抽成 `run_round_in`、让失败定稿留在调用者的
   错误分支上，并把植入重新指向**可观测的生产函数**（`failed_run_summary` / `run_exit_code_for` /
   `run_round_in`）。**第一版的"绿"原始输出仍在** `plant-p1-failed-round-not-persisted.txt`（旧记录名）
   与本次诊断过的输出里；我把结论写在这里而不是把那次失败藏起来。
5. **并发活动**：本批期间 HEAD 从 `a54424b` 起有**调度者**落的文档提交（例如把
   `TASK-DR66-ACCEPTANCE.md` 提交进来），因此 `ahead` 从 7 涨到 14；那些提交**不是我**落的，
   也不含本批代码。我能证明的是：本批 6 个提交各只含我列出的文件，`DECISIONS.md` 在我的提交里 0 命中。
6. **我没有把推断写成实测**：§7 已分栏；三处"未验证"逐条标注，其中最要紧的是
   **`cli_impl::run` 整函数的端到端未被执行**（§7-2）与 **K 不被检查是有意选择**（§7-3）。
7. **不声称 E1/E3 已 met。**

---

## 附：本批 6 个提交（英文信息，均带 `(DR-67)`，本地未 push）

```
91f1b9c test(DR-67): make the run_round_in wiring test run a real happy round and check its artifacts
aa08855 test(DR-67): pin the persisted code to the error's own class with a non-contract error too
0685059 test(DR-67): drive the failed-round persistence through the production summary and finaliser, with no test-side switch
2cf44e7 fix(DR-67): make the failure finalisation a caller of the round instead of a predicate inside it
2b6e943 fix(DR-67): fail any zero-increment Developer stage, and persist the exit code on the real failure path
e3f3cc8 docs(DR-67): disclose the DR-66 local history rewrite (six discarded or amended hashes, why it happened, why unpushed made it acceptable, and the dr66-wip disposition), and correct the three wrong statements in place with the old wording preserved and marked
a54424b (本批开工时的 HEAD，调度者的文档提交)
```

文件边界：`e3f3cc8` = 只改 `TASK-DR66-REPORT.md`；`2b6e943` = `src/{cli_impl.rs,prompts/developer.md,
runtime/run_loop.rs}` + 5 个测试文件；`2cf44e7` = `src/cli_impl.rs` + `tests/e1_increment.rs`；
`0685059`、`aa08855`、`91f1b9c` = 只改 `tests/e1_increment.rs`。
