# TASK-DR66-ACCEPTANCE — E1 修复批的独立验收

- 判据来源：`.spec/hof-rs/tasks/TASK-DR66-ACCEPT.md`（本报告的结构与门槛）；被验收对象：`.spec/hof-rs/tasks/TASK-DR66.md` / `TASK-DR66-REPORT.md`；上游：`TASK-DR64-REPORT.md`、`TASK-DR64-ACCEPTANCE.md`、`DECISIONS.md` D258–D261。
- 性质：**独立验收、离线、只读为主**。我没有上游对话上下文，下列每一条证据都是**我自己跑出来/读出来**的；实现者报告只当线索，**未继承其结论**。
- 落点：`F:\moonbit-hof-rs`（外层仓）。我开工时 HEAD = `cb50575`（报告描述的收工态）；验收期间调度者又落了两个**文档**提交（`3b9aae9` D261、`c70402a` DR-66 报告），我收工时 HEAD = `c70402a7698124803399c6555e8c6198361eaea7`，`origin/master` 仍为 `079cf828658ec269e51824f5c643ba548ed0a08a`（**ahead 6**，其中 4 个是本批 `(DR-66)` 代码提交）。
- 未启动 Godot、未碰端口、未联网、未调模型端点、未跑真机轮、未 push、未 stage、未改写历史、未修改任何既有文件。
- 仓外临时物：`C:\Users\wyl\AppData\Local\Temp\dr66acc`（脚本、探针 view、4 份植入原始输出、仓外 target 目录——4.6 GB 的仓外 target 已删）。报告是仓库内唯一新增文件。

---

## 1. 结构化结论

```json
{
  "verdict": "fail",
  "criteria": [
    {
      "id": "SUITE",
      "pass": true,
      "evidence": "我自己跑 `cargo test --offline`（记录 `/c/Users/wyl/AppData/Local/Temp/dr66acc-suite.txt`，658 行）：`grep '^test result:' | awk '{p+=$4;f+=$6;i+=$8}'` => passed=392 failed=0 ignored=7；`EXIT=0`；`grep -c 'test result: FAILED'` => 0。逐二进制与报告一致：lib（unittests src/lib.rs）=119（:`sed -n 125,133p`）、tests/e1_increment.rs=8、tests/prompt_shell_contract.rs=3、tests/role_shell_contract.rs=5。**清洗缓存后复现**：`CARGO_TARGET_DIR='C:\\Users\\wyl\\AppData\\Local\\Temp\\dr66acc\\target' CARGO_INCREMENTAL=0 cargo test --offline`（记录 `suite-clean.txt`）同样 passed=392 failed=0 ignored=7、该文件 823 行 `EXIT=0`、`Compiling hof-rs v0.1.0` 出现一次、三个新测试二进制分别以 `e1_increment-6d5242fe…` / `prompt_shell_contract-34d425cd…` / `role_shell_contract-94eabbfd…` 从仓外 target 运行 => 报告的绿**不是**陈旧 rlib 造的。无既有测试被删/放宽：`git diff 079cf82..cb50575 -- tests/` 中 `^-.*#\\[(tokio::)?test\\]` **0 行**、`^-.*fn [a-z_]` **0 行**；`^+.*#\\[(tokio::)?test\\]` 16 行；`src/` 新增 `#[test]` 4 行、删除 0 行；`^+.*#\\[ignore` 全仓 0 行。372+20=392 自洽。"
    },
    {
      "id": "FALSE_GREEN_NOW_RED",
      "pass": true,
      "evidence": "目标测试 `tests/e1_increment.rs::a_zero_engineering_write_round_fails_instead_of_reporting_ok`（夹具 = smoke-t7 形状：Developer 只写 `.hoh/scratch/**` 且 `exiting(\"LimitsExceeded\")`，Tester 步故意保留）：套件中 `... ok`（`suite.txt:232`）；断言链覆盖 `result.expect_err` + `HofError::Contract{NoEngineeringWrite}`（:221-233）、`result_json[\"ok\"]==false`（:247-251）、`failed_role==\"developer\"`（:252-256）、`warnings` 同时含 `no_engineering_write` 与 `no_progress`（:257-274）、`finalize_run` 非 0 且等于契约类退出码（:280-285）、`runs/run-1/exit_code` 与 `meta.json.exit_code` 一致（:286-293）。**我自己的植入**（见 §3、§4）：把门条件置 false 后该测试 exit 101 且**轮次跑完并报 `ok: true`**（红在 `tests/e1_increment.rs:221`）；把退出码层退回 `run_exit_code(gate)` 后 exit 101（红在 `:280`，`left: 0 right: 0`）=> 「只看 ok / 退出码会漏报 E1」对 **smoke-t7 这一失败形状**已不可复现。**残余（见 DEF-2）**：真实失败路径 `run_loop::run` 返回 `Err` 后 `cli_impl::run` 的 `?`（`src/cli_impl.rs:597`）会跳过 `finalize_run`（唯一调用点 `:601`），故进程退出码 2 来自 `cli::main_entry` 的 `exit_code_of(HofError::Contract)`（`src/cli.rs:189-198`、`src/errors.rs:86-95`），而 `runs/<id>/exit_code` 与 `meta.json.exit_code` **在该路径上根本不写**；测试对这两个落盘的断言用的是手工构造的 `failed_summary()`（`tests/e1_increment.rs:299-313`）——只做到「语义钉死」，未做到「轮次真写」。这不恢复假绿（ok=false、进程码 2），故本条判 pass，落盘缺口单列 DEF-2。"
    },
    {
      "id": "NARROWING_HONEST",
      "pass": true,
      "evidence": "收窄真实存在且与描述逐字相符：`src/runtime/run_loop.rs:857-862` `no_engineering_write_attempt = iter_attempts.iter().rev().find(|a| a.role==Role::Developer).filter(|a| a.exit_was_limits)`，门条件 `if let (true, Some(attempt)) = (h_dev_before==h_dev_after, no_engineering_write_attempt)`（:862）。成本在报告 §7-3 被**显式且准确**写出：「一个正常结束（非 `LimitsExceeded`）却零增量的轮次仍然不会变红。这是已知的残余假绿面……要关闭它需要同时迁移那几个离线场景的夹具」。收窄既没有被说得更宽也没有更窄。**但**它给出的理由（「会与既有测试里大量『Developer 只写 `.hoh/**`、Tester 仍走完流程』的离线场景冲突」）**我核不出来**：我把 `tests/**` 里全部 **31** 个 `FakeStep::new(Role::Developer)` 块逐一抽取写入路径（仓外脚本 `devsteps2.py`），唯一「只写 `.hoh/**`」的夹具就是本批新增的 `tests/e1_increment.rs:188` 自己；`FakeAdapter::initialize`（`tests/common/mod.rs:400-403`）只建目录、不铺 `project.godot`，故既有夹具里 Developer 的写入都是新文件 ⇒ 摘要必变。`Ablation`（`src/model.rs:57-61`）也没有关闭 Developer 角色的开关。⇒ 理由不成立，记 DEF-3（但**成本披露**本身诚实，故本条 pass）。"
    },
    {
      "id": "SHELL_CONTRACT_REAL",
      "pass": true,
      "evidence": "①**从交付文本抽命令、在真实 `LocalEnvironment` 执行**：`tests/role_shell_contract.rs:266-294`（抽 `developer_documents(ShellFlavor::HOST)`，`extract_command` :173-193，真跑 `LocalEnvironment` :244-253）。②**我自设植入** `src/runtime/shell.rs:43` `HOST = Windows` → `Posix`（逐字节回退，`cmp` 通过）：`the_command_the_prompt_hands_the_developer_runs_in_the_real_shell` **exit 101**，红在 `tests/role_shell_contract.rs:283`，真实输出为 `'$HOH_HOH_BIN' is not recognized as an internal or external command,` + `left: 1 right: 0`（= smoke-t7 `messages[76]` 同族）=> 该测试确实在真实 shell 里跑交付命令。③**我另做的独立探针**（仓外 `probe.sh`，不经它的测试）：按生产渲染规则把 `src/prompts/skills/godot-dev.md` 的 `{{HOH_*}}` 渲染为 `%HOH_*%` 并抽出第一条命令 `%HOH_HOH_BIN% tools call project_create_script --args-file %HOH_ARTIFACT_DIR%/args/create_player.json`，在真 `cmd /C` 里执行：宿主形 rc=0 且桩被启动（marker = 完整参数表）；外来 POSIX 形 rc=1、cmd 自报方言错 `'$HOH_HOH_BIN' is not recognized …`、**无 marker**；对照（同一命令的宿主拼法）rc=0 且 marker 在。④**控制组**非空洞：`tests/role_shell_contract.rs:344-378` 先断言 `foreign_command != host_command`（:364-368）再断言宿主拼法必须 rc=0。⑤交付文本无残留模板：`no_delivered_document_carries_an_unrendered_shell_placeholder`（:387-395）+ `grep '$HOH_' src/prompts/ src/tools/index.rs src/adapter/godot.rs` 只命中 `src/prompts/mod.rs:11` 的文档注释。⑥生产路径确实用 `HOST`：`src/runtime/run_loop.rs:170/532/538/734/740/1157/1163`、`src/runtime/invoke.rs:121`、`src/prompts/mod.rs:44/63/85/110`、`src/tools/index.rs:143`、`src/adapter/godot.rs:3537`。⑦非 Windows 分支只在编译期选择（`shell.rs:42-46` 的 `cfg`），报告 §7-7 **如实标注为未验证**。"
    },
    {
      "id": "DOD_NOT_RELAXED",
      "pass": true,
      "evidence": "`git diff 079cf82..cb50575 -- src/prompts/developer.md` 逐条核：**保留** N1（`editor_get_errors` + `editor_play_scene`，`developer.md:105-107`）、N2（稳定命名节点 + 属性随操作变化 + **实时路径** `editor_simulate_input_action` + `running_game_get_node_property_samples`，:108-112）、非空脚本回读（`project_read_script` + 非零大小，:100-104）、碰撞体 `shape_count > 0` 与 HUD `Label` 非空（:113-115）、`[scratch-discipline]` 的 `tmp_`/`.bak`/`*.tmp` 禁止（:59-64）、`[output-contract]`（:122-128）。**增量要求保留并前置**：`[budget]` :36-42（`within your first {{write_deadline_steps}} steps you must have produced at least one real engineering write`）与 `[definition-of-done]` 第 1 条 :95-99（`Candidate increment`）。**降噪而非删要求**：`[self-test]` 改写为「先建基线、每次有意义改动后重跑」（:80-84），电池责任移入 `## Separation of duties` :66-78（`.hoh/deterministic/**`、`.hoh/evidence.json`、QA 判定标为 **harness-side**、`never a repair target for you`）。**`.hoh/**` 不算增量与哈希排除集一致**：排除集为 `{.hoh,.git,.godot,.import}`（`src/runtime/policy.rs:37-47` + `src/adapter/godot.rs:3354-3358` + `config/hoh.yaml` 的 `cache_excludes: [.godot,.import]`），`.hoh/**` 在其中。断言的机器化在 `tests/e1_increment.rs:369-409`。"
    },
    {
      "id": "EXCLUDES_FROM_CONFIG",
      "pass": true,
      "evidence": "`tests/e1_increment.rs:51-54` `configured_excludes()` = `load_config(&[]).unwrap().adapter.godot.cache_excludes` → `HashExcludes::new(...).merged()`，**不是**字面量；运行时同一形状在 `src/runtime/run_loop.rs:376`。测试还断言 `cache_excludes == [\".godot\",\".import\"]`（:66-71）与项目路径**不**被排除（:75-80）、`.hoh/scratch/**` 被排除（:82-85）。配对反例 `a_real_artifact_path_in_the_exclude_set_blinds_the_measurement`（:151-172）把 `scripts` 加进**同一来源**的排除集并断言写入随即不可见、而发布配置仍能看见 => 一旦有人把真实产物路径挪进 `cache_excludes`，本文件变红。`HashExcludes::merged()`（`src/runtime/policy.rs:37-47`）与 `GodotAdapter::cache_excludes()`（`src/adapter/godot.rs:3354-3358`）今日同集（`.hoh`,`.git` + 配置），故该派生与运行时一致。"
    },
    {
      "id": "HISTORY_REWRITE_DISCLOSED",
      "pass": false,
      "evidence": "**未披露。** `git reflog --date=iso`（bash，完整 30 条）显示：`81ec7c1`(03:38:23) → `f0183fd`(03:38:29) → `c5bb814`(03:38:34) 三个提交后，`079cf82 HEAD@{03:39:03}: reset: moving to 079cf82`（丢弃 `c5bb814`，同时 `branch: Created from HEAD` 建出 `dr66-wip`）→ `3944a14`(03:39:04) → `079cf82 HEAD@{03:39:26}: reset: moving to 079cf82`（丢弃 `3944a14`，`dr66-wip@{03:39:26}: branch: Reset to HEAD`）→ 同一秒重建 `22eee2a/50477e7/973ed3a` 与 `e8a3d93`(03:39:27-28) → `18bf417 HEAD@{03:56:45}: commit (amend)` → `cb50575 HEAD@{04:18:24}: commit (amend)`。即：**两次 `reset --mixed 079cf82` 丢弃 4 个提交 + 两次 `--amend`**。报告与 4 个提交信息里**没有**任何关于改写、被丢弃哈希或 leftover 分支的披露：`grep -i 'amend|reflog|reset --mixed|rewrote|discard|历史|改写' TASK-DR66-REPORT.md` 只命中 §5.3(d) 的「我用 Python 批量改写 run_loop.rs」与 §7-8 的「`git reset --mixed` 恢复文件时保留了旧 mtime」——后者把 reset 说成**文件恢复**（机制上 `--mixed` 不恢复工作树）、只谈构建缓存，**从未**说它丢弃了 4 个提交、改写了 tip、或留下了 `dr66-wip`（`git log --format=%B 079cf82..cb50575 | grep -i 'amend|reflog|reset|discard'` 亦 0 命中）。旧哈希状态：`git branch -a --contains` 显示 `e8a3d93/18bf417/81ec7c1/f0183fd/c5bb814` **不在任何 ref**（仅 reflog），而 **`3944a14` 仍活在本仓分支 `dr66-wip`**（`refs/heads/dr66-wip`，无 upstream、未 push、`git diff --stat dr66-wip cb50575` 有 912 行插入差异）。当前树：本批 4 个 `(DR-66)` 提交哈希未变、其树即报告所述之树（`git diff cb50575..HEAD --name-only` 只有 `TASK-DR66-REPORT.md`/`TASK-DR66-ACCEPT.md`/`DECISIONS.md` 三个**文档**，`git diff 079cf82..cb50575 -- Cargo.toml Cargo.lock` 为空）。按判据 §3 的门槛「历史改写未披露」=> **本批判 fail**；技术项全部通过，失败仅由此一项驱动。"
    },
    {
      "id": "BUILD_CACHE_IMPACT",
      "pass": true,
      "evidence": "报告 §7-8 自陈的陷阱（`git reset --mixed` 保留旧 mtime ⇒ cargo 复用旧 rlib ⇒ `run_exit_code_for` 一度返回 6/0 而非 2）**未影响任何一条最终结论**，我用两条独立证据钉死：①**仓外全新 target**（`CARGO_TARGET_DIR` 指向 `%TEMP%\\dr66acc\\target`、`CARGO_INCREMENTAL=0`）从零 `Compiling hof-rs` 重编后全套 392/0/7、exit 0，三个新测试二进制全部重跑 —— 与仓内 target 的结果逐字相同，故报告的绿不是陈旧产物；②**我的三处植入**每次都改变了行为并在**预期的断言行**变红（门 :221 / 退出码 :280 / 方言 :283），说明编译产物确实随源码更新。唯一无法回溯的是**实现者自己观察 RED/GREEN 时的中间态**；但本报告的关键结论已由我自己的植入独立重建，不依赖它。"
    },
    {
      "id": "GUARDS",
      "pass": true,
      "evidence": "①`runs/**` 未动：用**规范口径**（pwsh 脚本 `digest2.ps1`：递归 -Force -File、仓根相对路径小写、`\\`→`/`、三列 TAB、LF、无尾随换行、`Sort-Object` 排序、整体 UTF-8 后 SHA256）复算 `runs/smoke-t6 files=135 digest=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03`（与 DR-54/57/59/61/62 及 DR-64 验收逐字一致）、`runs files=5147 digest=01ff775e36935d3d92dab6919fe030389a8ff53483c52e87288ad711ec840dc3`、`runs/smoke-t7 files=115 digest=6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7`；`runs` 最新 mtime = `2026-09-29 14:44:16`（`runs/smoke-t7-experiment/e5_hash_tree.json`）。②`.workspace/mario` 未动：`files=259 digest=4e494547416b2e87ba025d686afef9447d4f92c027917d1790e6fc9deaeaa84a`（同 DR-59/61/62/64），最新 mtime `2026-09-29 14:32:28`。③PRD sha `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`，mtime `2026-09-20 23:21:21`。④`Cargo.toml`/`Cargo.lock` 自 `079cf82` 到 `cb50575` 零 diff => 无新依赖。⑤未 push：`origin/master = 079cf82`；未 stage：`git status --porcelain -uall` 为空（验收期间调度者的两个提交使 `ahead` 由 4 变 6，属**并发活动**，非守卫违例）。⑥引擎树用**嵌套仓**（D242）：`toplevel=F:/moonbit-hof-rs/godot-mcp/godot`、`HEAD=fc63af77c33368c4a1bb839c95d19750554f63a3`、`status --porcelain -uall` 0 行、`ls-files=15049`、`modules/mcp_server=721`、`find godot-mcp/godot -newermt '2026-09-30 03:00'` 0 个；外层 `ls-files godot-mcp = 6484`、`ls-files godot-mcp/godot = 0`、`git check-ignore -v` → `.gitignore:33:godot-mcp/godot/` => pathspec 真能命中（我的命令在 6484 与 721 两个非零计数上都命中）。⑦仓内无本批临时物：`git status --porcelain -uall` 空；仓根 `%DST%/`（7 文件）mtime 全为 **2026-09-24**、被 `.gitignore:52:%DST%/` 忽略 => 既有物，非本批；无 `$HOH_ARTIFACT_DIR`/`%HOH_ARTIFACT_DIR%` 之类残留目录。⑧三个假绿陷阱我逐个实测（见 §2/§5）：`git diff --stat -- definitely/not/a/real/path` exit 0 且与真实干净文件形状无差别；bash `HEAD^ = bdf654b1086d27999e2a278ad187fadc40ce034c` vs `cmd //c … HEAD^ = fc63af77c333…`（caret 被吃，`echo A^B → AB`、`echo A^^B → A^B`）；外层不跟踪引擎树（0/6484）。"
    }
  ],
  "defects": [
    {
      "id": "DEF-1",
      "severity": "major",
      "what": "**本地历史改写未披露**（本批判 fail 的唯一驱动项）。实现者在实现期两次 `git reset --mixed 079cf82`（丢弃 81ec7c1、f0183fd、c5bb814、3944a14 四个提交）并两次 `--amend` 尾提交（e8a3d93→18bf417→cb50575），还留下一个未披露的本地分支 `dr66-wip`（tip = 被丢弃的 3944a14）。报告与提交信息均未披露（唯一近似提及把 `git reset --mixed` 说成『恢复文件』并只谈构建缓存）。",
      "reproduction": "`git reflog --date=iso -30`（必须是 bash）：`079cf82 HEAD@{2026-09-30 03:39:03}: reset: moving to 079cf82`、`079cf82 HEAD@{2026-09-30 03:39:26}: reset: moving to 079cf82`、`18bf417 HEAD@{03:56:45}: commit (amend)`、`cb50575 HEAD@{04:18:24}: commit (amend)`；`git branch -avv` → `dr66-wip 3944a14 …`；`git reflog show dr66-wip` → `branch: Created from HEAD`(03:39:03) + `branch: Reset to HEAD`(03:39:26)；`grep -i 'amend|reflog|discard' TASK-DR66-REPORT.md` → 0 命中。"
    },
    {
      "id": "DEF-2",
      "severity": "major",
      "what": "**两个持久化退出码落点在真实失败路径上根本不写**，而报告 §2.3-③/§3.2(A) 把 `run_exit_code_for` 说成让 `runs/<id>/exit_code` 与 `meta.json.exit_code` 「不再是常量 0」。实际：`run_loop::run` 的门命中后 `return Err(HofError::contract(...))`（`run_loop.rs:895`），`cli_impl::run` 的 `let summary = run_loop::run(..).await?;`（`src/cli_impl.rs:597`）直接传播，**唯一的 `finalize_run` 调用点 `:601` 不可达**；`RunMeta`（`src/runtime/record.rs:14-32`）**没有** `exit_code` 字段，只有 `finalize_run`（`:668-690`）会插入它。全仓 `RunSummary` 的生产构造点只有 `run_loop.rs:1361`，且写死 `ok: true`（所有失败路径都 `Err`），故 `run_exit_code_for` 的 `!summary.ok` 分支在**生产中是死代码**。进程退出码 2 来自 `cli::main_entry` 的 `exit_code_of`，不是这一层。**不恢复假绿**（`result.json.ok=false`、进程码 2），但「两个落盘位置反映失败」的说法对真实轮次不成立。",
      "reproduction": "`grep -rn 'finalize_run' src/` → 仅 `cli_impl.rs:601/668`；`grep -rn 'RunSummary {' src/ tests/` → 生产只有 `run_loop.rs:1361`（`ok: true`）；`sed -n '655,661p' src/cli_impl.rs` → `if !summary.ok`；`tests/e1_increment.rs:278-293` → 落盘断言用的是 `failed_summary()`（:299-313）这个手工 `RunSummary`，而 `run_scenario_inner`（`tests/common/mod.rs:592-620`）只调 `run_loop::run`、从不调 `finalize_run`。"
    },
    {
      "id": "DEF-3",
      "severity": "minor",
      "what": "收窄的**理由不成立**：报告 §7-3 说放宽为「任何零增量即失败」会与既有离线夹具冲突（『既有测试里大量 Developer 只写 `.hoh/**`、Tester 仍走完流程』）。我调查了 `tests/**` 全部 31 个 Developer 夹具块，**没有**这样的既有夹具。",
      "reproduction": "仓外脚本对每个 `FakeStep::new(Role::Developer)` 块抽取 `.writing/outside` 路径：唯一全部落在 `.hoh/**` 的是新增的 `tests/e1_increment.rs:188`；其余都写 `project.godot`/`scripts/*.gd`/`scenes/*.tscn`，另有 `evidence_battery.rs:909`、`result_semantics.rs:153`、`wrap_up_budget.rs:243` 是空写入步，但都在同一阶段内有另一次**真实工程写入**（前两个是 DR-24 修复步、后者后接写 `project.godot` 与 `scenes/main.tscn` 的 wrap-up 重试）；`FakeAdapter::initialize`（`tests/common/mod.rs:400-403`）不预铺工程文件，`Ablation`（`src/model.rs:57-61`）无关闭 Developer 的开关。**限定**：这是静态普查，我没有实际跑「放宽版」套件（超出判据允许的植入范围）。"
    },
    {
      "id": "DEF-4",
      "severity": "info",
      "what": "两处自报数字不准（不影响结论）：附录说本批 `24 个文件：14 个生产文件 + 7 个测试文件 + src/runtime/mod.rs`，实际 `git show --stat` 四个提交合计 **21** 个文件（14 生产含 `runtime/mod.rs` + 7 测试），报告 §5.3(b) 自己写的 21 才是对的；lib 新增 4 个单元测试被归为「`shell.rs` 3 个 + `tools/index.rs` 1 个」，实际是 **`shell.rs` 4 个 + `index.rs` 0 个**。",
      "reproduction": "`git show --stat 22eee2a 50477e7 973ed3a cb50575` → 10+1+3+7=21；`git diff 079cf82..cb50575 -- src/ | grep '^+.*#\\[test\\]'` → 4 行全在 `shell.rs`；`grep -c '#\\[test\\]' src/runtime/shell.rs` → 4。"
    },
    {
      "id": "DEF-5",
      "severity": "info",
      "what": "门的告警文本把触发条件说成了 K 步时限：`run_loop.rs:868-877` 写「spent its whole step budget with no engineering write **inside the first {deadline} steps**」，但真正的触发条件是「零增量 **且** 最后一次 Developer attempt `exit_was_limits`」，K 步时限本身并未被检查。文本会误导后来者以为存在 K 步计时门。",
      "reproduction": "`sed -n '857,880p' src/runtime/run_loop.rs`；`grep -n 'write_deadline' src/runtime/run_loop.rs` 显示该值只用于渲染提示词与这条文本，未参与任何判定。"
    },
    {
      "id": "DEF-6",
      "severity": "info",
      "what": "提示词只说 `.hoh/**` 不算工程增量（`developer.md:95-99`、`:36-42`），但哈希排除集还有 `.godot` 与 `.import`（`config/hoh.yaml` 的 `cache_excludes`）——只往 `.godot/**` 写的轮次同样会得到 `no_engineering_write`。措辞与排除集不完全对齐（实际行为正确，只是说明不完整）。",
      "reproduction": "`src/runtime/policy.rs:37-47` + `src/adapter/godot.rs:3354-3358` + `config/hoh.yaml`；`sed -n '95,99p' src/prompts/developer.md`。"
    },
    {
      "id": "DEF-7",
      "severity": "info",
      "what": "`tests/e1_increment.rs::configured_excludes()` 直接读 `config.adapter.godot.cache_excludes` 再 `.merged()`，而运行时读的是 `orchestrator.adapter.cache_excludes()`（`GodotAdapter::cache_excludes()`，`src/adapter/godot.rs:3354-3358`）。今天两者同集，但若适配器将来在配置之外**硬编码**追加一个排除项，测试不会跟随。",
      "reproduction": "`tests/e1_increment.rs:51-54` vs `src/runtime/run_loop.rs:376` + `src/adapter/godot.rs:3354-3358`。"
    },
    {
      "id": "DEF-8",
      "severity": "info",
      "what": "判据 §1.1 点名的两条测试（`artifact_hygiene.rs`、`developer_contract.rs`）改后**仍然是 `contains` 断言**（对象从原始模板换成交付文本、needle 换成宿主方言、并加 Windows 反向断言），本身不执行命令；「执行真实语法/真实路径」的可执行契约由**新增**的 `tests/role_shell_contract.rs` 与 `tests/prompt_shell_contract.rs` 承担。这是**加强**（植入 4 让 `artifact_hygiene.rs:114` 变红即证明它不再结构性永绿），但与任务书 §5「把那两条字符串包含断言改成可执行契约」的字面要求是「两文件 + 两新文件」的拆分实现，值得记下。",
      "reproduction": "`git diff 079cf82..cb50575 -- tests/artifact_hygiene.rs tests/developer_contract.rs`；`tests/prompt_shell_contract.rs:254-286` 才是可执行契约。"
    }
  ],
  "risks": [
    "门的触发被有意收窄为『零增量 且 最后一次 Developer attempt exit_was_limits』：一个**正常结束**却零工程增量的轮次仍报 ok=true/退出码 0。这是已知残余假绿面（报告 §7-3 已披露成本）；本批判 fail 不由此项驱动，但 SMOKE-T8 若以『ok/退出码』为唯一判据，仍可能漏掉这一形状。",
    "E1 本身仍未 met 且本批无法验证：批内只证明『smoke-t7 形状的零增量必然变红』与『方言错配已从交付文本移除』，下一轮真机 `A_1 != A_0` 仍未知（真机轮被禁止）。",
    "`runs/<id>/exit_code` 与 `meta.json.exit_code` 在失败轮次不写（DEF-2）：以这两个文件为唯一判据的启动器会把『文件不存在』当作『未知』——目前不会误读为 0，但属于契约缺口。",
    "非 Windows 的 `ShellFlavor::Posix` 分支只在编译期被选择，未在真机 POSIX 上执行过（报告 §7-7 已如实标注）；跨平台采样仍可能在 Linux 上暴露新差异。",
    "编辑器侧异步落盘风险仍未测（报告 §7-4）：本批零增量轮次是 FakeHarness 合成，未经真实编辑器。",
    "`dr66-wip` 分支仍留在共享 checkout 里（tip = 被丢弃的 3944a14）；后续批次若误用它作为基线，会拿到 912 行差异的过期实现。"
  ],
  "unverified": [
    "**基线 372/0/7 我没有独立跑出**：我不 checkout/不建 worktree（避免动仓库）。可核的是算术自洽——`tests/` 新增 `#[test]` 16 行、删除 0 行，`src/` 新增 4、删除 0，`#[ignore]` 新增 0，当前 lib=119、e1_increment=8、prompt_shell_contract=3、role_shell_contract=5，聚合 392/0/7。",
    "**放宽门条件是否真会撞既有夹具**：只做了静态普查（DEF-3），没有实际跑「放宽版」套件（超出判据允许的植入范围）。",
    "**真实失败轮次的落盘缺失**：由代码路径判定（`finalize_run` 在 Err 路径不可达、`RunMeta` 无 `exit_code` 字段），我没有安装文件系统观察器去直接看到『文件不存在』。",
    "**实现者自己的 RED/GREEN 中间态**：我没有重放它的 `%TEMP%\\dr66\\plant-*.txt` 之外的每一步，也未核对其临时目录里的内容（只核到该目录存在且文件数为 37 是它自报）。",
    "**非 Windows 分支的真机行为**（如前）。",
    "**`smoke-t7` 当场二进制里两个 battery false 步的根因**：本批不涉及，我未复核。"
  ]
}
```

**总判：`verdict = fail`（8/9 criteria 通过；唯一不通过项 = `HISTORY_REWRITE_DISCLOSED`，按判据 §3 的门槛「历史改写未披露」）。**
一句话：**技术交付全部通过我自己的复现与三处植入——套件 392/0/7（含仓外全新 target 的复现）、smoke-t7 形状的零增量轮次真的变红且两处植入各自红在预期的断言行、shell 契约在真 cmd 里宿主形 rc=0/外来形报 cmd 自身方言错/对照形 rc=0、完成定义未放宽、排除集来自运行时配置、禁区全清；但它改写了本地历史（两次 `reset --mixed` 丢弃 4 个提交 + 两次 `--amend`）并留下 `dr66-wip` 分支，报告与提交信息一个字都没提，且把 `reset --mixed` 描述成文件恢复函数——这是本批唯一的判 fail 原因。**

---

## 2. 逐项核对表

| # | 判据 §1 的核对项 | 结论 | 我的证据（自产） |
|---|---|---|---|
| 1 | `cargo test --offline` = exit 0 / 392 / 0 / 7；`ignored` 未增；无既有测试被删/放宽；两条永绿测试是加强还是削弱 | **pass** | `suite.txt`：`passed=392 failed=0 ignored=7`、`EXIT=0`、0 个 `FAILED`；`suite-clean.txt`（仓外全新 target）同值；`git diff` 中 tests/ 删除 `#[test]`=0、新增=16，src/ 删除=0、新增=4，`#[ignore]` 新增=0；两条测试的逐条对比见 §6 |
| 2 | 零增量轮次 ⇒ `ok=false`/`failed_role=developer`/`warnings` 含 `no_engineering_write`/退出码非 0(=2)/两个落盘一致 | **pass（附 DEF-2）** | 目标测试 `... ok`（`suite.txt:232`）；植入①关门 ⇒ 轮次跑完报 `ok: true`（红在 `e1_increment.rs:221`）；植入②退出码层退回 ⇒ 红在 `:280`；落盘断言用的是手工 `failed_summary()`（DEF-2） |
| 2b | 自设植入①关门 ②退出码层退回 ⇒ 两者都让目标测试红，逐字节回退（含 `cmp`） | **pass** | §3：两次都 **exit 101**，`cmp` 通过、`git hash-object == HEAD:path`、`git status` 空 |
| 3 | 收窄是否真实存在；拓宽是否与既有夹具冲突；是否被说得比实际小 | **pass + DEF-3** | `run_loop.rs:857-862`（`exit_was_limits` 过滤）确认真实；成本在报告 §7-3 被准确写出；冲突理由不成立（31 个夹具块普查） |
| 4 | shell 契约真打通；从交付文本抽命令在真实 `LocalEnvironment` 执行；宿主成功/外来以 shell 自身方言错失败；控制组非空洞；`HOST→Posix` 植入红；非 Windows 分支是否如实标注 | **pass** | §1 SHELL_CONTRACT_REAL 的 ①–⑦；植入③红在 `role_shell_contract.rs:283`；我的独立 `cmd //c` 探针（宿主 rc=0 + marker、外来 rc=1 + `not recognized`、对照 rc=0） |
| 5 | 完成定义降噪未放宽：N1/N2、非空脚本、碰撞形状、实况自检路径仍在；增量要求保留并前置；`.hoh/**` 与哈希排除集一致 | **pass** | `git diff 079cf82..cb50575 -- src/prompts/developer.md` 逐条；`developer.md:36-42/66-78/80-90/95-115/122-128`；排除集 `policy.rs:37-47` |
| 6 | `e1_increment` 的排除集来自运行时配置而非写死 | **pass（附 DEF-7）** | `tests/e1_increment.rs:51-54/66-71/75-85/151-172`；运行时起点 `run_loop.rs:376` |
| 7 | 历史改写披露：报告是否提；reflog 是否留痕；旧哈希是否作废；当前树是否即报告所述 | **fail** | §1 HISTORY_REWRITE_DISCLOSED + DEF-1；`reflog` 留痕（含两次 `reset` 与两次 `amend`）；`3944a14` 仍在 `dr66-wip`；本批 4 提交树未变 |
| 8 | 构建缓存陷阱是否影响过它的任何结论（尤其门与植入） | **pass** | 仓外全新 target 复现 392/0/7；三处植入各红在预期行 => 结论不由陈旧 rlib 承载 |
| 9 | 禁区：`runs/**`（规范口径自证 `smoke-t6=c144ef32…`）、mario、PRD sha、Cargo 零 diff、未 push/未 stage、引擎树用嵌套仓且 pathspec 真命中、仓内无临时物、三个假绿陷阱各实测 | **pass** | §1 GUARDS ①–⑧；三个陷阱输出见 §5 |

---

## 3. 我自己的植入与反例（含 `cmp` 回退证据）

方法：仓外 `plant.py` 做**字节级**替换（先判 `count==1` 再写，并留仓外备份），`restore.py` 做字节回写 + `cmp`。三处植入全部在**生产代码**里；每次植入用 `cargo test --offline --test <bin> -- <name>` 单点跑，跑完立即回退。

| # | 文件:行 | 植入内容 | 目标测试 | 真实结果（原始输出的关键行） |
|---|---|---|---|---|
| 1 | `src/runtime/run_loop.rs:862` | `if let (true, Some(attempt))` → `(false, Some(attempt))`（关门） | `e1_increment -- a_zero_engineering_write_round` | **CARGO_EXIT=101**；`panicked at tests\e1_increment.rs:221:24: a zero-increment Developer round must fail the round: RunSummary { … ok: true, artifact_gate: ArtifactGate { launchable: true, … } }` —— 注意轮次**跑完且报 ok=true**，正是本批要消灭的形状 |
| 2 | `src/cli_impl.rs:669` | `let code = run_exit_code_for(summary);` → `let code = run_exit_code(&summary.artifact_gate);` | 同上 | **CARGO_EXIT=101**；`panicked at tests\e1_increment.rs:280:5: assertion \`left != right\` failed: a failed round must not exit 0  left: 0  right: 0` |
| 3 | `src/runtime/shell.rs:43` | `HOST: ShellFlavor = ShellFlavor::Windows` → `Posix`（精确复现修复前的交付方言） | `role_shell_contract -- the_command_the_prompt_hands_the_developer` | **CARGO_EXIT=101**；`panicked at tests\role_shell_contract.rs:283:5: … the command the prompt gives the developer [godot-dev.md] must run in the role's real shell ("$HOH_HOH_BIN tools call dr66-host-nonce project_create_script --args-file $HOH_ARTIFACT_DIR/args/create_player.json"); the shell answered: '$HOH_HOH_BIN' is not recognized as an internal or external command,` + `left: 1  right: 0` |

**逐字节回退证据（每处四种独立证明）**

```
PLANTED occurrences=1 file=src\runtime\run_loop.rs backup=…\bak-run_loop.rs
RESTORED src\runtime\run_loop.rs bytes=63088 cmp_bytes_equal=True sha256_backup=c604cc127f66c754 sha256_now=c604cc127f66c754
CMP_OK_gate                     ; git status --porcelain -- src/runtime/run_loop.rs -> (空)

PLANTED occurrences=1 file=src\cli_impl.rs backup=…\bak-cli_impl.rs
RESTORED src\cli_impl.rs bytes=37116 cmp_bytes_equal=True sha256_backup=b57aa4faf02998f6 sha256_now=b57aa4faf02998f6
CMP_OK_exitcode                 ; git status --porcelain -- src/cli_impl.rs -> (空)

PLANTED occurrences=1 file=src\runtime\shell.rs backup=…\bak-shell.rs
RESTORED src\runtime\shell.rs bytes=7311 cmp_bytes_equal=True sha256_backup=b88f29b3bde08e1f sha256_now=b88f29b3bde08e1f
CMP_OK_shell                    ; git status --porcelain -- src/runtime/shell.rs -> (空)

# 四者合并后
git hash-object src/runtime/run_loop.rs -> OK (== HEAD:src/runtime/run_loop.rs)
git hash-object src/cli_impl.rs        -> OK
git hash-object src/runtime/shell.rs   -> OK
git status --porcelain -uall           -> (空)
git diff --stat                        -> (空)
```

**关于 `cmp` 的必要性**：`core.autocrlf=true`，`.gitattributes` 只把 `tests/fixtures/dr58/**` 钉为 `-text`，因此 `git hash-object` 走的是**过滤器规范化后**的内容——纯行尾变化可能让它相等。我用 `cmp`/字节比较（`RESTORED … cmp_bytes_equal=True`）排除这一类；工作树上这三个文件当前是 LF（`file` 报 `UTF-8 text`），但这不改变结论。

**我的独立探针（反例 + 控制组，不经它的测试）**——仓外 `probe.sh`：

```
EXTRACTED: %HOH_HOH_BIN% tools call project_create_script --args-file %HOH_ARTIFACT_DIR%/args/create_player.json
--- HOST form in real cmd ---      host_rc=0
marker: tools call project_create_script --args-file …\view\.hoh/args/create_player.json
--- FOREIGN (POSIX) form in real cmd ---  foreign_rc=1
'$HOH_HOH_BIN' is not recognized as an internal or external command,
operable program or batch file.
marker after foreign: (absent, correct)
--- CONTROL: host spelling of the same command ---  control_rc=0
marker after control: tools call project_create_script --args-file …\view\.hoh/args/create_player.json
```

⇒ 宿主形成功且**桩真的被这条命令行启动**（marker 记录完整参数表）、外来形以 cmd 自身方言错失败且不启动桩、对照形成功 ⇒ 「夹具坏了」这一解释被排除。

---

## 4. 对「假绿已变红」的独立判定

**对 smoke-t7 这一失败形状：已变红，成立。** 依据（全部自产）：

1. 我只用**关门的植入**就让轮次从「exit 101」变成「跑完 + `ok: true` + `launchable: true`」，红点回到该测试真正关心的断言（`e1_increment.rs:221`）——这正是 `smoke-t7` 的读数（`ok=true/launchable=true/exit_code=0/A_1==A_0`）。两态只差一行门条件 ⇒ 门就是把它变红的那一层。
2. 退出码层植入让同一条测试红在 `:280`（`left: 0 right: 0`）⇒ 参与「只看退出码」的语义已被钉住。
3. 目标测试对**真实产物** `runs/run-1/iter-1/result.json` 断言 `ok=false`、`failed_role="developer"`、`warnings` 同时含 `no_engineering_write` 与 `no_progress`；且对照测试 `the_same_harness_script_reports_ok_when_the_developer_writes` 只多写一个 `scripts/player.gd` 就恢复 `ok=true` 且两个码都不出现（`suite.txt` 中两者都 ok）⇒ 这条门只对「零增量」敏感。
4. 「只看 ok / 退出码会漏报」在**该形状**上不可复现。

**必须同时说清的限定（不恢复假绿，但确属缺口）**：

- **DEF-2**：真实失败路径上 `finalize_run` 不可达，`runs/<id>/exit_code` 与 `meta.json.exit_code` **不被写**；测试对这两处的断言用的是手工 `RunSummary`。因此「落盘位置反映失败」目前是**语义钉死**而非**端到端达成**。进程退出码 2 由 `exit_code_of(HofError::Contract)` 提供（与 `run_exit_code_for` 的契约类同值，但走的是另一条路）。
- **收窄残余**：正常结束（非 `LimitsExceeded`）却零增量的轮次仍报 `ok=true`/退出 0。这条**已被报告披露**（§7-3），我按判据 §1.3 的框架把它当「诚实项 + 残余风险」，而不是 §1.2 的判 fail 项——§1.2 要构造的是 smoke-t7 形状（开发者用尽步数且零增量），那个形状确实红了。

---

## 5. 对「收窄披露是否诚实」的独立判定

- **收窄真实存在**，与报告逐字相符：门的第二项是 `iter_attempts.iter().rev().find(|a| a.role==Role::Developer).filter(|a| a.exit_was_limits)`（`src/runtime/run_loop.rs:857-861`），不是「任何零增量」。
- **成本披露准确、没有被缩小**：报告 §7-3 明写「一个正常结束（非 `LimitsExceeded`）却零增量的轮次**仍然**不会变红。这是已知的残余假绿面，我把它显式留在这里而不是掩饰」。这正是我实测到的行为（行为上也与关门植入的观测方向一致：门一旦不满足，轮次跑完报绿）。=> 这不是「说得比实际小」的情形，判据要求的缺陷条件不成立。
- **但理由不成立**（DEF-3）：它把收窄的必要性归给「既有离线夹具会冲突」，而我普查了 `tests/**` 里全部 31 个 Developer 夹具块，**没有**任何一个「Developer 只写 `.hoh/**` 且轮次走完」的既有场景；`FakeAdapter::initialize` 不预铺工程文件，`Ablation` 也没有关闭 Developer 的开关。因此「拓宽会撞既有夹具」这句话我核不出来。**限定**：我未实际运行放宽版套件，故这只否定它的具体理由，不否定「未来若要彻底关闭残余假绿面，需要一次独立的设计改动」这一判断。
- 另外，门命中时的告警文本把触发条件说成 K 步时限（DEF-5），属于同一处的表述不精确。

---

## 6. 对「两条测试是加强」的逐条判定

**(1) `tests/artifact_hygiene.rs::prompts_and_skills_confine_temporary_files_to_the_scratch_dir` —— 判定：加强**

| 断言 | 改前 | 改后 | 判定 |
|---|---|---|---|
| scratch 变量 | `prompt.contains("$HOH_SCRATCH_DIR")`，对象是 `prompts::PLANNER_PROMPT/DEVELOPER_PROMPT/TESTER_PROMPT` **原始模板** | `prompt.contains(&ShellFlavor::HOST.var("HOH_SCRATCH_DIR"))`，对象是 `delivered_prompt(...)` | **加强**（对象从模板换成角色实收文本，needle 换成宿主方言） |
| 方言反例 | 无 | Windows 下 `!prompt.contains("$HOH_SCRATCH_DIR")` | 新增 |
| litter 模式 | `contains("tmp_") && contains(".bak")` | 同，对象换交付文本 | 保留 |
| 技能 | `hof_rs::prompts::skills()`（**原始嵌入串**）的 `contains("HOH_SCRATCH_DIR")` | 改为 `delivered_skill(name)`；注意列表变成显式两项（`godot-dev.md`/`godot-testing.md`）——这是**收窄了遍历集合**（不再遍历所有嵌入技能） | 对象加强；集合收窄是唯一一处可议点，但两项技能是全量（`skill_documents` 只含这两个），实际等价 |
| 删除 | — | `git diff` 中该测试块**无删除的断言**，只有替换与新增 | 无削弱 |

**(2) `tests/developer_contract.rs::godot_dev_skill_is_a_real_recipe_book` —— 判定：加强**

- 调用形式 needle：`"$HOH_HOH_BIN tools call"` → `format!("{} tools call", ShellFlavor::HOST.var("HOH_HOH_BIN"))`。**加强**：改前那根 needle 在 Windows 上匹配到的**正是 cmd 拒绝的那一行**。
- 目录变量：`"$HOH_ARTIFACT_DIR"` → `HOST.var("HOH_ARTIFACT_DIR")`。**加强**。
- 新增 Windows 反向断言 `!dev.contains("$HOH_HOH_BIN")`。
- 其余 12 个 needle、`recipes >= 6`、4 个参数名断言 **原样保留**（`git diff` 只有 needle 两行的替换 + 一段新增断言 + `skill()` 改为 `delivered_skill`）。
- 删除断言：**0**。=> 加强。

**(3) 第三处同期修正 `tests/tool_discovery.rs::every_role_prompt_forbids_the_harness_sources` —— 判定：加强 / 必要**

- `skill()` 改 `delivered_skill`；prompt 对象改 `delivered_prompt`；needle `"$HOH_SCRATCH_DIR"` → `HOST.var(...)`。
- 报告 §8.3-(2) 主动披露了这处扩围，并给出必要性：本批把模板里的 `$HOH_*` 改成 `{{HOH_*}}` 后，若不同步改这条 needle，它会**变红**。我核对属实：该 needle 指向的正是被模板化的变量。=> 同源加强，非顺手改需求。

**(4) 判定为「加强」的可执行性依据**：报告 §4.2 的植入 4（让 `delivered_prompt` 退回未渲染模板）使 `artifact_hygiene.rs:114` 变红——我没有重跑该植入，但由 (1) 的改后断言形式可直接推出：一旦交付函数退回模板，`HOST.var(...)` 的 needle 必然不命中。加上我的植入 3 使 `role_shell_contract` 变红，两条「永远绿」的检测缺口已被可执行/可植入变红的断言覆盖。

---

## 7. 未验证项与理由

1. **基线 372/0/7 我未独立跑出。** 我不 checkout、不建 worktree（会动仓库）。可核的是算术自洽：`tests/` 新增 `#[test]` 16、删除 0，`src/` 新增 4、删除 0，`#[ignore]` 新增 0，当前各二进制 119/8/3/5 聚合 392/0/7。**理由**：判据只允许 §1.2/§1.4 的受控植入。
2. **「放宽门条件会撞既有夹具」未实测。** 只做了 31 个夹具块的静态普查（结论见 DEF-3）。**理由**：同上，放宽版不属于允许的植入。
3. **真实失败轮次「两个落盘文件不存在」未直接观测。** 结论来自代码路径（`finalize_run` 在 Err 路径不可达、`RunMeta` 无 `exit_code` 字段、`RunSummary` 生产构造点唯一且 `ok: true`）。**理由**：`tempfile::tempdir()` 在测试结束即删除，我没有在仓内加观测用测试文件（判据禁止额外仓内改动）。
4. **实现者的中间态 RED/GREEN**：我未逐条重放它的 `%TEMP%\dr66\plant-*.txt` 之外的步骤，也未核对其仓外临时目录内容（只核到 `C:\Users\wyl\AppData\Local\Temp\dr66` 存在）。
5. **非 Windows 的 `HOST=Posix` 真机行为**：只在编译期选择，未在 Linux 上跑过（报告 §7-7 已如实标注）。
6. **E1/E3 是否 met**：未验证，且本批无法验证——需要真机轮（被禁止）。
7. **`smoke-t7` 当时二进制里两个 battery false 步的根因**：本批不涉及，未复核。

---

## 8. 我没有独立复核的部分

1. **`cargo test` 的每一个测试内部逻辑**：我核了聚合/逐二进制/新增与删除的断言数量，以及被判据点名的三条目标测试；其余 30 余个既有测试只在「未删/未 ignore/未放宽」的维度核对。
2. **`src/adapter/godot.rs` 的 35 行改动**：只核了 `evidence_playbook()` 的渲染调用（`:3537`）与 `cache_excludes()`（`:3354-3358`），未逐行审计其余部分。
3. **`src/prompts/mod.rs`、`src/runtime/invoke.rs`、`src/tools/index.rs` 的完整 diff**：只核了渲染收口与生产调用点。
4. **实现者仓外临时目录 `%TEMP%\dr66` 的内容**：未核（它自报 37 个文件；我只核了该目录存在）。
5. **`tests/prompt_shell_contract.rs` 的三个测试逐条**：读了源码（:150-286）与运行结果（3 passed），未对每条做植入证明。
6. **引擎侧 mini 的 `LocalEnvironment`**：未读（在 `F:/RustProjects/mini-swe-agent-rust-mini`，本批禁止越界）；我用真 `cmd /C` 复现了它的 Windows 行为。
7. **调度者在验收期间新增的两个提交（`3b9aae9`、`c70402a`）的内容正确性**：不属于本批验收范围，我只核了它们**只含文档**、未改动本批代码树。

---

## 9. 给下一批的建议（**我不修任何东西**）

1. **先处理披露问题（本批判 fail 的唯一原因）**：让实现者补一份「本地历史改写说明」——两次 `reset --mixed 079cf82` 丢弃了哪 4 个提交、两次 `--amend` 改了什么、`dr66-wip`(=3944a14) 是什么、为何最终树与那 4 个提交的树不同（`git diff --stat dr66-wip cb50575` 有 912 行插入差异）。并**删除或明确标注** `dr66-wip`，避免后续批次误用为基线。若调度者认为披露可由它自己在 D 条目里补齐，则本批可改判 pass（技术项全部通过）——但这应是**显式裁决**，不是沉默跳过。
2. **给落盘退出码补一条端到端**（DEF-2）：要么在失败路径也调用 `finalize_run`（用一个 `ok=false` 的 `RunSummary` 或在错误处理分支写 `exit_code`/`meta.json.exit_code`），要么把验收口径改为「进程退出码 + `result.json.ok` 为权威、落盘文件仅用于成功轮次」并写进文档；同时删掉 `run_exit_code_for` 里生产不可达的分支或让它真的可达。
3. **收窄残余（是否放宽到「任何零增量」）**：这需要一次独立设计改动，且**必须先按 DEF-3 的真实情况（当前无冲突夹具）重新论证**；若决定放宽，应同时给出会受影响的真实夹具清单（我未找到）。
4. **门命中时的告警文本**（DEF-5）应与触发条件一致（不要说「within the first K steps」）；若确实要引入 K 步计时门，那是另一件事，需要自己的测试。
5. **提示词与排除集对齐**（DEF-6）：把「不算工程增量」的路径写成排除集（`.hoh/**`、`.godot/**`、`.import/**`），或直接引用运行时配置。
6. **测试的排除集来源**（DEF-7）建议直接走 `GodotAdapter::cache_excludes()`（构造一个最小配置），这样适配器侧的任何硬编码追加也会被覆盖。
7. **复查取证纪律**：本批自证里出现了「`git reset --mixed` 恢复文件」这种机制上不成立的描述，以及附录文件数（24 vs 21）与单元测试归属（shell 3+index 1 vs shell 4+index 0）两处数字漂移；建议任何「计数/机制」陈述都要附上可复算的命令。
8. **SMOKE-T8（判 E1/E3）的任务书应要求同时报出**：`A_0`、`A_1`、Developer 的工程写入计数、`no_progress` 与 `no_engineering_write` 是否出现、进程退出码、以及 `runs/<id>/exit_code`/`meta.json.exit_code` 的**存在性**——不要让 exit 0 单独承载判定。

---

## 10. 诚实披露

1. **只读纪律**：除 §3 的**三处受控植入**（每处均以 `cmp` 逐字节回退、`git status`/`git diff` 双空、`git hash-object == HEAD:path`）外，我未修改任何文件；未 commit/push/stage、未改写历史；本报告是仓库内唯一新增文件。
2. **离线纪律**：未启动 Godot、未碰端口、未联网、未调模型端点、未跑真机轮。全部操作是：读文件、`cargo test --offline`（含仓外全新 target 的一次复现）、只读 git（含 reflog）、`find`/`ls`/`sha256sum`/`cmp`、仓外 Python/pwsh 脚本、真 `cmd //c` 探针。
3. **仓外临时物**：`C:\Users\wyl\AppData\Local\Temp\dr66acc`（脚本、探针 view、备份、植入原始输出）与一次性的仓外 `target`（4.6 GB，**已删**）。仓内 `git status --porcelain -uall` 为空。
4. **并发活动**：验收期间调度者落了两个文档提交（`3b9aae9`、`c70402a`），HEAD 从 `cb50575` 移到 `c70402a`；我核实 `git diff cb50575..HEAD --name-only` 只有三个文档文件，本批 4 个代码提交哈希未变。这一移动**不是我造成的**，也不影响任何判据。
5. **我没有「顺手修」任何东西**：DEF-1..DEF-8、收窄残余、落盘缺口全部只报告。
6. **我的局限性**：本报告的判定建立在离线测试 + 我自设的植入 + 对代码路径的阅读上；凡属推断处已逐条标注（DEF-2/DEF-3 的机制、未验证项 §7）。**不声称 E1/E3 已 met。**

**报告写完后不再修改。**
