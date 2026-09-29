# TASK-DR66-REPORT — E1 修复批：提示词↔真实 shell 契约、完成定义降噪、让 E1 类失败真的变红

- 任务书：`.spec/hof-rs/tasks/TASK-DR66.md`（本报告的唯一任务来源）
- 落点：`F:\moonbit-hof-rs`（外层仓，`master`）。开工时 HEAD = `079cf82`（D259），收工时 HEAD = `cb50575`（本批 4 个提交，**未 push**）
- 性质：**离线实现批**。未启动 Godot、未碰端口、未联网、未调模型端点、未跑真机轮、未 `push`
- 仓外临时物：`C:\Users\wyl\AppData\Local\Temp\dr66`（脚本 + 备份 + 探针工作区，**37 个文件，仍在**，见 §6.7；仓内无本批临时物）
- 上游依据：`.spec/hof-rs/tasks/TASK-DR64-REPORT.md`、`.spec/hof-rs/tasks/TASK-DR64-ACCEPTANCE.md`、`DECISIONS.md` D243/D258、以及调度者转达的独立验收两条设计修正（见 §8.2）
- 报告写完后不再修改

---

## 1. 结论 + 套件真实尾部 / 退出码

**结论：五件事全部落地，且五处"永远绿 / 假绿"都变成了真红。** 最重要的一件——**零工程增量的轮次不再报 `ok=true` / `exit_code=0`**——已由可执行测试钉住（构造一次零增量轮次 ⇒ `ok=false`、`failed_role=developer`、违约码 `no_engineering_write`、退出码非 0 且落盘）。

**真机门（唯一权威）：`cargo test --offline`**

```
$ cargo test --offline
...
test result: ok. 0 passed; 0 failed; 7 ignored; 0 measured; 0 filtered out; finished in 0.00s
EXIT=0

聚合：passed=392  failed=0  ignored=7
```

| 口径 | 基线（开工前，`079cf82`） | 本批收工（`cb50575`） | 判定 |
|---|---|---|---|
| passed | **372** | **392**（+20） | 只增不减 ✔ |
| failed | **0** | **0** | ✔ |
| ignored | **7** | **7** | **未增加** ✔ |
| exit code | 0 | **0** | ✔ |

逐二进制核对（`diff` 基线/收工对照，只有 4 处差异，全部是我新增的测试）：

| 二进制 | 基线 | 收工 | 差异 |
|---|---|---|---|
| 库单元测试（lib） | 115 | **119** | +4（`src/runtime/shell.rs` 3 个 + `src/tools/index.rs` 1 个） |
| `tests/e1_increment.rs` | — | **8** | 新增文件 |
| `tests/prompt_shell_contract.rs` | — | **3** | 新增文件 |
| `tests/role_shell_contract.rs` | — | **5** | 新增文件 |

**无既有测试被删除、放宽或加 `#[ignore]`**：测试总数只增（+20），`ignored` 恒为 7；`tests/artifact_hygiene.rs` 与 `tests/developer_contract.rs` 的两条字符串包含断言是**加强**（逐条对比见 §4），新增断言多于删除断言。

**不声称 E1/E3 已 met**（§7）。

---

## 2. 五件事各自的落点与理由

### 2.1 事一：让"提示词要求的命令语法"在角色真实 shell 里真的可用 → **选 (a) 平台化渲染**

**被否决者 (b)（把角色 shell 改成 POSIX）为什么不行**：角色的真实 shell 由 **mini** 的 `LocalEnvironment` 决定（`F:\RustProjects\mini-swe-agent-rust-mini\rust\src\environments\local.rs:66-76`，Windows 走 `Command::new("cmd").arg("/C").raw_arg(command)`）。该 crate 通过 `Cargo.toml:17` 的 `path = "F:/RustProjects/mini-swe-agent-rust-mini/rust"` 引用，**在本仓之外**（不在 `godot-mcp/godot` 嵌套仓内，也不在外层仓被跟踪的 `godot-mcp/` 6484 个文件内）⇒ 按任务书 §1.1 与 D242 **不越界改引擎树**；且改成 `sh` 会把角色**已经正确**的 cmd 命令（反斜杠路径、`%VAR%`、`copy`/`dir` 等内建）全部改错，影响面不可控。

**落点（全部在平台化渲染的单一收口上）**

| 落点 | 作用 |
|---|---|
| **新增 `src/runtime/shell.rs`**（176 行） | `ShellFlavor{Windows,Posix}`（`:32`）、`ShellFlavor::HOST`（`:41/:46` 按 `cfg(windows)` 编译期选定）、`COMMAND_VARS`（`:64`）、`render_var`（`:73`）、`render_command_vars`（`:83`，把 `{{HOH_*}}` 渲染成目标方言）、`contains_unresolved_command_var`（`:96`）、`rewrite_var_dialect`（`:112`，控制组用） |
| `src/runtime/invoke.rs:132-146` | `render_prompt_with_budget_and_shell(template, iteration, limits, flavor)`：`{{…}}` 全部替换完再渲染 `{{HOH_*}}`；`render_prompt_with_budget`（`:116`）与 `render_prompt` 之外的旧调用保持原签名，内部走 `HOST` |
| `src/prompts/mod.rs:24-51` | `skill_document(name, flavor)`、`skill_documents(flavor)`：技能注入前渲染（**角色真正读到的技能文本**） |
| `src/prompts/mod.rs:63/85/110` | `planner_task_with_shell` / `developer_task_with_shell` / `tester_task_with_shell`：任务提示词按目标 shell 渲染 |
| `src/prompts/{planner,developer,tester}.md`、`src/prompts/skills/{godot-dev,godot-testing}.md` | 所有 `$HOH_*` 字面量改成 `{{HOH_*}}` 模板；**不再有任何硬编码 shell 变量** |
| `src/tools/index.rs:147` `render_tools_markdown_for` + `:174/:266` | `.hoh/TOOLS.md` 在**两个出口**（无权限早退 + 正常出口）统一渲染 |
| `src/adapter/godot.rs:3457-3538`（渲染调用在 `:3535`） | 证据剧本 `evidence_playbook()` 结尾统一渲染 |
| `src/runtime/run_loop.rs:170`（`skill_inputs`） | 注入角色视图的技能走 `skill_documents(HOST)`；6 处系统提示词/3 处任务提示词改为 `*_with_shell(…, HOST)` / `render_prompt_with_budget_and_shell(…, HOST)` |

**为什么这是"改真实执行路径"而不是"改文档字符串"**：渲染函数与执行它的 `LocalEnvironment` 现在由同一个 `ShellFlavor::HOST` 绑定；`tests/role_shell_contract.rs` **从交付文本里抽出命令并在真实 `LocalEnvironment` 里跑**，所以"文档里写的"和"真实能跑的"是同一个字符串（§3.1）。平台化只发生在**交付前**，运行时执行路径一行没动，因此不存在"文档 / 执行"两套。

**契约测试（事二）**：`tests/role_shell_contract.rs`（426 行，5 个测试）

- 抽取规则（显式、写进文件头注释，避免测试自身漂移）：命令源 = **角色实际收到的文本**（渲染后的系统提示词 + 任务提示词 + 两个技能体 + 证据剧本）；只扫 ```` ``` ```` 围栏内的行；候选行首 token 必须是 `%HOH_*`/`$HOH_*` 且含 `tools call`；**带尖括号填充位（`<tool>`、`<name>`）的跳过**（那是语法模板不是命令）；`{{HOH_*}}` 按**目标 shell**解析；`--args-file` 路径物化为 `{}`。
- 平台期望（显式）：**宿主方言必须 exit 0 且留下 marker**（Windows ⇒ `%HOH_*%`；POSIX ⇒ `$HOH_*`）；**外来方言必须失败**，且失败必须是 shell 自己的方言错误（消息里含 `HOH_HOH_BIN`、输出非空），否则说明坏的是夹具不是语法。

### 2.2 事三：完成定义降噪 → **移出电池责任，保留并前置工程增量要求**

**落点：`src/prompts/developer.md`**（`50477e7`）

- `:66` 新增 `## Separation of duties`：`Yours` = 项目本身（每个可观察行为都要真实、可启动、经稳定命名节点可达）；`Not yours` = `.hoh/deterministic/**`（确定性证据电池）、`.hoh/evidence.json`、QA 判定，并明确"**电池在你的调用之后**运行，其 `ok=false` 是 **harness-side** 条件，`never a repair target for you`"；若被 harness 侧限制挡住，**用一句话说明并把步数花在项目上**。
- `:92` `[definition-of-done]` 第 1 条从"必须能从**你之后跑的那份确定性证据电池**看到"改成 **`Candidate increment`**：**至少一个项目内文件因你而改变**（新写的非空脚本或真实编辑），并且**明确写出 `.hoh/scratch` 里的写入不算**（被哈希排除 ⇒ 那正是 smoke-t7 的 22 个 scratch 文件）。
- `:29` `[budget]` 新增 **`Within your first {{write_deadline_steps}} steps you must have produced at least one real engineering write`**，并点名违约码 `no_engineering_write`；`{{write_deadline_steps}}` 由 `run_loop::developer_write_deadline()` 渲染（= 25，见 §2.3）。
- `:80` `[self-test]` 保留并改写："先建立可自测的基线，每次有意义改动后重跑对应路径"；同时指出"自测**不是**验收判定，电池是 harness 自己的记录"。

**没有"通过删掉要求"降噪**：N1（`editor_get_errors` + `editor_play_scene`）、N2（稳定命名节点 + 属性随操作变化，并要求用**实时路径** `editor_simulate_input_action` + `running_game_get_node_property_samples` 自证）、非空脚本回读、碰撞体 `shape_count > 0`、HUD `Label` 非空文本**全部保留**；`tests/e1_increment.rs::the_completion_definition_keeps_the_increment_and_drops_the_battery_ownership` 逐条断言这些仍在，并断言电池责任已移出。

**为什么"电池自身缺陷"确实存在过（引用 DR-64 §3.4，不复制其未被证实的数字）**：`runs/smoke-t7/iter-1/result.json.battery_passes[0]` 的 11 步里 `input_channel_probe=false`、`node_and_collision_assertions=false`，而这两步的根因在 hof-rs 自己（`godot.rs:1597-1604` 硬传 `"scene_path":"current"` ⇒ 恒 `-32602`；`godot.rs:1253-1257`/`:2051-2055` 读顶层 `name` ⇒ 恒判 `missing`），且**在 HEAD 上已被 DR-58 修好** ⇒ 该约束点针对的是 smoke-t7 当时的二进制，不是现在的 HEAD。

### 2.3 事四：前 K 步工程写入 + 独立违约码 + **自动化对 E1 类失败真的变红**（本批最重要）

**① K 的选取与理由（可复算，不是拍的）**：`src/runtime/run_loop.rs:58`

```rust
pub fn developer_write_deadline(limits: &AgentLimits) -> u64 {
    (limits.step_limit / 4).min(limits.wrap_up_steps).max(1)   // 150/4 = 37, cap 25 => 25
}
```

- 依据证据：DR-64 量出"第一个**真实工具结果**迟至第 46 步（30.7 % 预算）"、115/150 步被迫包 `bash -c`、"工程写入 0 步"；而 `wrap_up_steps = 25`（`config/hoh.yaml:15`）是运行时**已经**强加的"停止探索、先写出产物"阈值。
- 于是 K 取 **`min(step_limit/4, wrap_up_steps)` = 25（150 步的 16.7 %）**：它落在"探索带"里、且**早于 wrap-up 带**，是"写出增量后仍有足够步数验证它"的最早合理时点；**cap 到 `wrap_up_steps` 保证这条指令永远不会和 wrap-up 规则互相矛盾**。
- 该值由运行时计算并渲染进提示词 ⇒ 提示词里的 K 与运行时用的 K **是同一个数**（`tests/e1_increment.rs::the_developer_prompt_states_the_write_deadline_the_runtime_computes` 断言渲染文本含 `first 25 steps`）。

**② 独立违约码**：`src/model.rs:333-357`

```rust
/// Warning only: the Developer produced no change.
NoProgress,
/// DR-66 ④: **failure.** …
NoEngineeringWrite,          // code() => "no_engineering_write"
```

`no_progress` **保留**（它仍是同一个测量的"描述"），新增的 `no_engineering_write` 是**判定**。两者语义在代码注释、提示词与 `result.json.warnings` 里都可区分。

**③ 真的变红（不是追加 warning）**：`src/runtime/run_loop.rs:829-895`

```rust
let h_dev_after = hash_tree(&workspace, &excludes)?;          // .hoh/** 被排除
let no_engineering_write_attempt = iter_attempts.iter().rev()
    .find(|a| a.role == Role::Developer).filter(|a| a.exit_was_limits);
if h_dev_before == h_dev_after { /* 保留 no_progress warning */ }
if let (true, Some(attempt)) = (h_dev_before == h_dev_after, no_engineering_write_attempt) {
    let violation = ContractViolation::NoEngineeringWrite;
    append_warning(...);                                      // 人类可读的说明
    let mut warnings = iter_warnings.clone();
    warnings.push(violation.code().to_string());               // 机读的违约码
    finalize_failure(&run_dir, iteration, Role::Developer, "contract_violation",
                     Vec::new(), warnings, …, iter_attempts.clone(), …)?;   // ok=false / failed_role=developer
    return Err(HofError::contract(violation).into());           // 轮次失败
}
```

- `h_dev_before`/`h_dev_after` **夹住整个 Developer 阶段（含 wrap-up 重试）**，且 `.hoh/**` 被哈希排除 ⇒ 相等意味着**项目一个字节都没变**，与 `REQUIREMENTS.md:112` 的 E1 分句直接冲突。
- 轮次层：`src/runtime/run_loop.rs:1371` 的 `ok: true` 现在只出现在**成功出口**（失败路径 `finalize_failure` 写 `ok=false` 并直接返回，走不到这里）。
- 退出码层：`src/cli_impl.rs:654` 新增

```rust
pub fn run_exit_code_for(summary: &RunSummary) -> i32 {
    if !summary.ok {
        HofError::contract(ContractViolation::NoEngineeringWrite).exit_code()   // = 2
    } else {
        run_exit_code(&summary.artifact_gate)   // 0 / 6，语义与调用者完全不变
    }
}
```

  `finalize_run`（`:669`）改用它 ⇒ **`runs/<id>/exit_code` 与 `meta.json.exit_code` 不再是常量 0**。`run_exit_code(gate)` **签名与语义一行未动**（既有调用者与 `tests/result_semantics.rs:97-99/275` 原样通过）。

**④ 回归测试（先红后绿）**：`tests/e1_increment.rs::a_zero_engineering_write_round_fails_instead_of_reporting_ok`

- 夹具**正是 smoke-t7 的形状**：Planner 写计划 → Developer 只写 `.hoh/scratch/experiment.py` 与 `.hoh/scratch/project.godot.pre_iter1` 并以 `LimitsExceeded` 结束 → Tester 照常收尾。Tester 步**故意保留**，这样门一旦被移除，轮次会**跑完**并在这条测试真正关心的断言上失败（`result` 必须是 `Err` / `ok` 必须是 false / 退出码必须非 0），而不是因 harness 脚本缺步而失败。
- 断言链：`result.expect_err` → `as_hof_error` 是 `HofError::Contract{NoEngineeringWrite}` → `result.json.ok=false` → `failed_role="developer"` → `warnings` 同时含 `no_engineering_write` 与 `no_progress` → `finalize_run` 返回**非 0**且等于该违约类退出码 → `runs/<id>/exit_code` 与 `meta.json.exit_code` 逐字一致。
- 对照（防止把"重试规则"混进来）：`FakeAdapter::with_developer_artifact_valid(true)` 关闭 wrap-up 重试；`the_same_harness_script_reports_ok_when_the_developer_writes` 只多写一个 `scripts/player.gd` 就断言 `ok=true`、且 `warnings` 里**两个码都不出现** ⇒ 证明这条门只对"零增量"敏感。
- **真的变红的真实输出**：见 §3.2。

### 2.4 事五：改掉两个永远绿的测试（**加强**，逐条对比见 §4）

薄弱的结论：`tests/artifact_hygiene.rs:112-115` 与 `tests/developer_contract.rs:57-74` 只对**原始模板**做字符串包含断言 ⇒ 结构上永远绿（DR-64 §2-Q5 与 DR-64-ACCEPTANCE §6 均确认）。

| 文件 | 改前 | 改后 |
|---|---|---|
| `tests/common/mod.rs` | — | 新增 `delivered_prompt(template)`（`:518`）与 `delivered_skill(name)`（`:534`）：**角色实际收到的文本**（`render_prompt_with_budget_and_shell(…, HOST)` / `skill_documents(HOST)`） |
| `tests/artifact_hygiene.rs:106-137` | `prompt.contains("$HOH_SCRATCH_DIR")`（3 个原始模板） | 对**渲染后**文本断言 `ShellFlavor::HOST.var("HOH_SCRATCH_DIR")`；Windows 下**额外**断言 `!contains("$HOH_SCRATCH_DIR")`；技能断言改读 `delivered_skill` |
| `tests/developer_contract.rs:53-91` | needle 列表含 `"$HOH_HOH_BIN tools call"`、`"$HOH_ARTIFACT_DIR"` | needle 换成 `ShellFlavor::HOST.var(...)` 的**交付形式**；Windows 下额外断言技能里**不再**出现 `$HOH_HOH_BIN`；其余 12 个 needle 与 ≥6 recipes 断言原样保留 |
| `tests/tool_discovery.rs:18-25/206-236` | `skill()` 读原始嵌入字符串；needle `"$HOH_SCRATCH_DIR"` | `skill()` 改读 `delivered_skill`；needle 换成交付形式（**第三处同类修正**，见 §8.3-(2)） |
| **`tests/prompt_shell_contract.rs`（新增，3 测试）** | — | **可执行契约**：①「提示词写的 scratch 纪律真的能用」——用提示词点名的那个变量把文件写出去，断言它落在 `.hoh/scratch`、**不在项目根**，并断言该位置确实在 `HashExcludes::merged()` 的排除集内；②「技能里那条 scratch recipe 能跑」（从围栏块里取出含该变量的那一行真跑）；③「recipe book 的第一条具体 `tools call` 能在角色 shell 里跑」——在 `HOH_HOH_BIN` 位置放一个**真桩**（Windows `.cmd` / POSIX `.sh`），执行抽出的命令，断言桩被启动且收到完整参数表 |

---

## 3. 证据链（真实输出）

### 3.1 `role_shell_contract` 的红（cmd `not recognized`）与对照绿

**(A) 当前代码、外来（POSIX）方言 ⇒ 真实 cmd 报错（测试自身的断言，`tests/role_shell_contract.rs::the_other_platforms_syntax_fails_in_the_roles_real_shell` 通过是因为它**要求**失败）。同一命令、两种方言的原始输出（仓外探针 `%TEMP%\dr66\cmd_probe.py`，工作目录 = 仓外临时 view，环境变量指向真桩）：

```text
### POSIX form
command: $HOH_HOH_BIN tools call dr66-host-nonce project_create_script --args-file $HOH_ARTIFACT_DIR/args/create_player.json
returncode: 1
output:
'$HOH_HOH_BIN' is not recognized as an internal or external command,
operable program or batch file.

### cmd form
command: %HOH_HOH_BIN% tools call dr66-host-nonce project_create_script --args-file %HOH_ARTIFACT_DIR%/args/create_player.json
returncode: 0
output:
(empty)
```

**(B) 修复前后（真正的 RED→GREEN）**。把 `ShellFlavor::HOST`（Windows 分支）改回 `Posix`——即**精确复现修复前的交付文本**——`the_command_the_prompt_hands_the_developer_runs_in_the_real_shell` 的真实失败输出（原始文件，`%TEMP%\dr66\plant-shell-prompt-flavor.txt`）：

```text
thread 'the_command_the_prompt_hands_the_developer_runs_in_the_real_shell' panicked at tests\role_shell_contract.rs:283:5:
assertion `left == right` failed: the command the prompt gives the developer [godot-dev.md] must run
in the role's real shell ("$HOH_HOH_BIN tools call dr66-host-nonce project_create_script --args-file
$HOH_ARTIFACT_DIR/args/create_player.json"); the shell answered:
'$HOH_HOH_BIN' is not recognized as an internal or external command,
operable program or batch file.
  left: 1
 right: 0
```

⇒ 修复前确实是**红**，且红的原因是 **cmd 方言错**（与 smoke-t7 的 `messages[76]: '$HOH_HOH_BIN" tools call …' is not recognized as an internal or external command` 同族），不是路径/夹具问题。修复后：

```text
test the_command_the_prompt_hands_the_developer_runs_in_the_real_shell ... ok
test the_other_platforms_syntax_fails_in_the_roles_real_shell ... ok
test the_platform_correct_form_succeeds_where_the_foreign_one_is_offered ... ok
test no_delivered_document_carries_an_unrendered_shell_placeholder ... ok
test the_generated_tools_index_uses_the_target_shell_syntax ... ok
test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

**非空洞性**：宿主测试与外来测试是**同一条抽出命令**的两种方言；外来测试只在失败是"方言错误且未被静默吞掉"时才算通过，因此任何夹具损坏（找不到桩/路径错）都会让它红。控制组 `the_platform_correct_form_succeeds_where_the_foreign_one_is_offered` 断言同一命令的**宿主拼法**必须成功 ⇒ 排除"桩坏了"这一解释。

### 3.2 零增量轮次 ⇒ `ok` / 退出码真的变红（真实输出）

**(A) 修复后（绿）**：`a_zero_engineering_write_round_fails_instead_of_reporting_ok ... ok`，其断言的**真实值**可从同场景的 `result.json` 取（测试逐项断言）：`ok=false`、`failed_role="developer"`、`warnings` 含 `no_engineering_write` 与 `no_progress`；`finalize_run` 返回 `2`（= `HofError::contract(NoEngineeringWrite).exit_code()`，`src/errors.rs:86-95` 的 contract 类），`runs/run-1/exit_code` 内容为 `2\n`，`meta.json.exit_code=2`。

**(B) 修复前（红）**：把门改成 `if let (false, …)`（一行植入）后，轮次跑完并在**测试真正关心的断言**上失败 —— 原始输出（`%TEMP%\dr66\plant-e1-increment-gate.txt`）：

```text
thread 'a_zero_engineering_write_round_fails_instead_of_reporting_ok' panicked at tests\e1_increment.rs:221:24:
a zero-increment Developer round must fail the round
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
```

把退出码层改回 `run_exit_code(&summary.artifact_gate)`（一行植入）后，原始输出（`%TEMP%\dr66\plant-round-exit-code.txt`）：

```text
thread 'a_zero_engineering_write_round_fails_instead_of_reporting_ok' panicked at tests\e1_increment.rs:280:5:
assertion `left != right` failed: a failed round must not exit 0
  left: 0
 right: 0
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
```

⇒ **"只看 ok / 退出码会漏报 E1 失败"这条指控，在自动化层面已经不可复现**：现在零增量轮次必然让 `ok=false` 且退出码非 0；反之植入任一层都会让它变红。（这两处植入同时就是 §5 的非空洞性证据 2 与 3。）

### 3.3 事一的量化目标（供真机轮核对，本批不声称达成）

本批**不能**证明"首个成功工具调用会提前到第 25 步以内"——那需要真机轮。本批能证明的是**根因已被移除**：交付文本里已经不存在会被 cmd 拒绝的 POSIX 变量引用（`no_delivered_document_carries_an_unrendered_shell_placeholder` + 两条 `!contains("$HOH_…")` 断言），且抽出的命令在真实 `LocalEnvironment` 里 exit 0。

---

## 4. 两条永远绿的测试：改前 / 改后 + 植入证明

### 4.1 逐条对比（注明每一处是加强还是替换）

**(1) `tests/artifact_hygiene.rs::prompts_and_skills_confine_temporary_files_to_the_scratch_dir`**

| 断言 | 改前 | 改后 | 判定 |
|---|---|---|---|
| scratch 变量 | `prompt.contains("$HOH_SCRATCH_DIR")`，对象是 `prompts::PLANNER_PROMPT` 等**原始模板** | `prompt.contains(&ShellFlavor::HOST.var("HOH_SCRATCH_DIR"))`，对象是 `delivered_prompt(...)` | **加强**：从"模板里有没有这个串"变成"角色收到的文本里这个变量是不是宿主方言"。修复前该断言在 Windows 上**红**（§5 植入 4） |
| 方言反例 | 无 | Windows 下 `!prompt.contains("$HOH_SCRATCH_DIR")` | 新增 |
| litter 模式 | `contains("tmp_") && contains(".bak")` | 同（对象换成交付文本） | 保留 |
| 技能 | `content.contains("HOH_SCRATCH_DIR")`（原始技能体） | 同，对象换成 `delivered_skill(name)` | 保留 + 对象加强 |

**(2) `tests/developer_contract.rs::godot_dev_skill_is_a_real_recipe_book`**

| 断言 | 改前 | 改后 | 判定 |
|---|---|---|---|
| 调用形式 | `"$HOH_HOH_BIN tools call"` | `format!("{} tools call", HOST.var("HOH_HOH_BIN"))` | **加强**（这是最典型的一处：改前的 needle 在 Windows 上匹配到的正是 cmd 拒绝的那一行） |
| 目录变量 | `"$HOH_ARTIFACT_DIR"` | `HOST.var("HOH_ARTIFACT_DIR")` | 加强 |
| 方言反例 | 无 | Windows 下 `!dev.contains("$HOH_HOH_BIN")` | 新增 |
| 其余 12 个 needle + `recipes >= 6` + 4 个参数名断言 | 有 | **原样保留** | 未削弱 |

**(3) `tests/tool_discovery.rs::every_role_prompt_forbids_the_harness_sources`** —— 任务书没点名的**第三处**同类问题（`skill()` 读原始嵌入串、needle 是 `"$HOH_SCRATCH_DIR"`）：同样改成交付文本 + 宿主方言。见 §8.3-(2) 的诚实披露。

### 4.2 植入证明：这两条测试现在**会**红

| 植入 | 位置（生产代码 / 承载不变量的测试） | 目标测试 | 真实失败输出 |
|---|---|---|---|
| `delivered_prompt` 返回未渲染的 `{{HOH_SCRATCH_DIR}} …`（模拟"又变回只读模板"的旧行为） | `tests/common/mod.rs:518`（**承载该不变量的测试侧**，见 §5 说明） | `artifact_hygiene::prompts_and_skills_confine_temporary_files_to_the_scratch_dir` | `panicked at tests\artifact_hygiene.rs:114:9: planner.md must name the scratch directory in its real shell syntax` |
| `ShellFlavor::HOST` 的 Windows 分支改回 `Posix`（模拟修复前的交付） | `src/runtime/shell.rs:41`（**生产代码**） | `role_shell_contract::the_command_the_prompt_hands_the_developer_runs_in_the_real_shell` | `… the shell answered: '$HOH_HOH_BIN' is not recognized as an internal or external command, operable program or batch file.  left: 1  right: 0` |

两条目标测试均在植入后 **exit 101**，回退后绿（§5 的逐字节回退证据）。

**"改前会红吗"**：会。第 2 个植入**就是**改前的交付行为（`HOST = Posix` ⇒ 模板渲染成 `$HOH_…`），而第 1 个植入让交付函数退回"只给模板"。两者都精确对应改前状态 ⇒ 改后的测试对"改前状态"是红的。

---

## 5. 非空洞性证据：4 处植入（3 生产 + 1 测试载体），逐字节回退

### 5.1 植入清单

| # | 记录名 | 文件:行 | 植入内容 | 目标测试（命令） | 植入后真实结果 |
|---|---|---|---|---|---|
| 1 | `shell-prompt-flavor` | `src/runtime/shell.rs:41`（**生产**） | Windows 的 `HOST` 由 `ShellFlavor::Windows` 改为 `Posix`（= 精确复现修复前的交付方言） | `cargo test --offline --test role_shell_contract -- the_command_the_prompt_hands_the_developer` | **exit 101**，红于 `role_shell_contract.rs:283`（cmd `not recognized`，见 §3.1-B） |
| 2 | `e1-increment-gate` | `src/runtime/run_loop.rs:862`（**生产**） | 门条件 `(true, …)` → `(false, …)`（零增量不再失败） | `cargo test --offline --test e1_increment -- a_zero_engineering_write_round` | **exit 101**，红于 `tests/e1_increment.rs:221`（`a zero-increment Developer round must fail the round`） |
| 3 | `round-exit-code` | `src/cli_impl.rs:654`（**生产**） | `run_exit_code_for` 退回 `run_exit_code(&summary.artifact_gate)`（忽略 `ok`） | 同 2 | **exit 101**，红于 `tests/e1_increment.rs:280`（`a failed round must not exit 0`，`left: 0 right: 0`） |
| 4 | `forever-green-contract` | `tests/common/mod.rs:518`（**测试载体**，理由见 5.2） | `delivered_prompt` 返回未渲染模板 | `cargo test --offline --test artifact_hygiene -- prompts_and_skills_confine_temporary_files` | **exit 101**，红于 `tests/artifact_hygiene.rs:114` |

原始输出文件（仓外，逐字保留）：`%TEMP%\dr66\plant-{shell-prompt-flavor,e1-increment-gate,round-exit-code,forever-green-contract}.txt`。

### 5.2 关于植入 4 落在测试侧（参 D253）

"交付给角色的文本必须是**宿主方言**"这条不变量，由 `tests/common/mod.rs::delivered_prompt`（测试载体）与生产函数 `render_prompt_with_budget_and_shell` 共同承载。植入 1 已经证明**生产侧**的那一半会被抓红；植入 4 证明**测试载体侧**的那一半也会被抓红——即"测试自己不再退化成只读模板"。按任务书 §2 的许可（"若某处不变量由测试自身承载而生产代码无对应函数，可落在承载该不变量的测试里，但必须显式说明"），这一处显式说明在此。

### 5.3 逐字节回退证据（四种互相独立的证明）

植入脚本（`%TEMP%\dr66\plants.py`）在每次植入前把原文件复制到仓外备份，植入后立即用备份覆盖回写，然后：

```
PLANT shell-prompt-flavor          src/runtime/shell.rs -> exit 101 ; restored sha256=b88f29b3bde08e1f bytes-equal=True
PLANT e1-increment-gate            src/runtime/run_loop.rs -> exit 101 ; restored sha256=c604cc127f66c754 bytes-equal=True
PLANT round-exit-code              src/cli_impl.rs -> exit 101 ; restored sha256=b57aa4faf02998f6 bytes-equal=True
PLANT forever-green-contract       tests/common/mod.rs -> exit 101 ; restored sha256=abbb795c887d5b35 bytes-equal=True
```

（`bytes-equal=True` 是 `open(path,'rb').read() == open(backup,'rb').read()` 的**字节比较**结果——CRLF 敏感，见下。）

**(a) `git status --porcelain` 与 `git diff --stat` 双空**（唯一剩余项是本批之外/并发的 `DECISIONS.md`，见 §6.6-a）：

```
$ git status --porcelain -uall
 M DECISIONS.md
$ git diff --stat
 DECISIONS.md | 31 +++++++++++++++++++++++++++++++
 1 file changed, 31 insertions(+)
```

⇒ 本批的 21 个受管文件（见 (b)）**没有任何未提交改动**。

**(b) `git hash-object` == HEAD blob**（21/21 全部相等）：

```
OK src/adapter/godot.rs            OK src/prompts/planner.md          OK src/runtime/shell.rs
OK src/cli_impl.rs                 OK src/prompts/skills/godot-dev.md OK src/tools/index.rs
OK src/model.rs                    OK src/prompts/skills/godot-testing.md OK tests/artifact_hygiene.rs
OK src/prompts/developer.md        OK src/prompts/tester.md           OK tests/common/mod.rs
OK src/prompts/mod.rs              OK src/runtime/invoke.rs           OK tests/developer_contract.rs
OK src/runtime/mod.rs              OK src/runtime/run_loop.rs         OK tests/e1_increment.rs
OK tests/prompt_shell_contract.rs  OK tests/role_shell_contract.rs     OK tests/tool_discovery.rs
```

**(c) 对备份的逐字节比较**：`bytes-equal=True`（4/4，见上）。

**(d) 为什么 (b) 单独不够、必须加 (c)**：本仓 CRLF 敏感（`.gitattributes` 存在；`git status` 反复提示 `LF will be replaced by CRLF the next time Git touches it`）。`git hash-object` 走的是**过滤器/规范化后**的内容，纯行尾变化在 (b) 里可能相等却仍改变了字节；`cmp`/字节比较才排除这一类。本批**实测到一次真实的行尾事故**：我用 Python 批量改写 `src/runtime/run_loop.rs` 时把整份文件的 CRLF 变成了 LF（`git diff --stat` 立刻从 ~85 行膨胀到 133 行以上、且出现"LF will be replaced by CRLF"警告）。处置：`git checkout -- src/runtime/run_loop.rs` 回到 HEAD，再用保留原行尾的脚本重做补丁，最终 `git diff --stat` 与该文件的真实改动量一致（133 行 ±，无整份重写）。这也是我此后对所有改写脚本都传入 `newline=''` 并断言 `"\r" not in s`/按原文件行尾重建的原因。

### 5.4 额外：`tests/e1_increment.rs` 的排除集**来自运行时配置**（调度者转达的修正 1）

DR-64 §5(a) 原设计把 `[".hoh",".git",".godot",".import"]` 写死在测试里，其"把 `scripts` 塞进 `cache_excludes` 即变红"的方法论植入**不会**让测试变红（DR-64-ACCEPTANCE DEF-7 已指出）。本批改为：

```rust
fn configured_excludes() -> Vec<String> {
    let config = load_config(&[]).expect("config/hoh.yaml must load");
    HashExcludes::new(config.adapter.godot.cache_excludes).merged()
}
```

并断言 `merged()` 恰含 `{.hoh,.git,.godot,.import}`、`cache_excludes == [".godot",".import"]`、项目路径**不在**排除集里、`.hoh/scratch/**` **在**排除集里（`the_runtime_exclude_set_comes_from_the_configuration`）。配对反例 `a_real_artifact_path_in_the_exclude_set_blinds_the_measurement` 把 `scripts` 加进**同一来源**的排除集，证明该写入随即不可见 ⇒ 只要有人把真实产物路径挪进 `cache_excludes`（DR-11 陷阱），这个文件就会红。

---

## 6. 禁区自查（真实输出）

### 6.1 引擎树（含 `godot-mcp/**`）未改 —— 用**嵌套仓**，并证明 pathspec 真能命中

```
$ git -C godot-mcp/godot rev-parse --show-toplevel
F:/moonbit-hof-rs/godot-mcp/godot
$ git -C godot-mcp/godot rev-parse HEAD
fc63af77c33368c4a1bb839c95d19750554f63a3
$ git -C godot-mcp/godot status --porcelain | wc -l            -> 0
$ git -C godot-mcp/godot status --porcelain -uall | wc -l      -> 0
# ---- 非空洞性：这个仓/这条命令确实能看见东西 ----
$ git -C godot-mcp/godot ls-files | wc -l                       -> 15049
$ git -C godot-mcp/godot ls-files modules/mcp_server | wc -l    -> 721
$ git -C godot-mcp/godot ls-files modules/mcp_server/docs/tools_list.renamed.json | wc -l -> 1
# ---- mtime：本批窗口内（2026-09-30 03:00 之后）无引擎文件被动过 ----
$ find godot-mcp/godot -type f -newermt '2026-09-30 03:00' | wc -l -> 0
```

### 6.2 外层仓不跟踪引擎树（假绿陷阱 ③，D242 表述收窄）

```
$ git ls-files godot-mcp/godot | wc -l     -> 0
$ git ls-files godot-mcp | wc -l           -> 6484
$ git check-ignore -v godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe
.gitignore:33:godot-mcp/godot/	godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe
$ git status --porcelain -- godot-mcp/godot | wc -l   -> 0   # 空 pathspec 同样静默（陷阱 ①）
```

⇒ 引擎"未变更"的结论**只**来自嵌套仓 `status` + mtime，**没有**用外层 `git diff`。

### 6.3 `runs/**` 未动

```
$ find runs -type f -newermt '2026-09-30 03:00' | wc -l -> 0
$ find runs -type f -printf '%T+ %p\n' | sort -r | head -1
2026-09-29+14:44:16.4036646000 runs/smoke-t7-experiment/e5_hash_tree.json
```

`runs/**` 的最新 mtime 是 2026-09-29 14:44:16，比本批开工时刻（2026-09-30 03:33）早约 13 小时 ⇒ 本批没有写入 `runs/**`；本批也**没有**执行 `hoh run`（无真机轮）。

### 6.4 `.workspace/mario/**` 未改

```
$ find .workspace/mario -type f -newermt '2026-09-30 03:00' | wc -l -> 0
$ find .workspace/mario -type f -printf '%T+ %p\n' | sort -r | head -1
2026-09-29+14:32:28.7396764000 .workspace/mario/.godot/editor/editor_layout.cfg
```

### 6.5 PRD 未改

```
$ sha256sum .spec/hof-rs/PRD-mario.md
4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a  *.spec/hof-rs/PRD-mario.md
$ ls -la --time-style=full-iso .spec/hof-rs/PRD-mario.md
-rw-r--r-- 1 wyl 197609 5375 2026-09-20 23:21:21.766695900 +0800 .spec/hof-rs/PRD-mario.md
```

与 D243 / `meta.json.spec.sha256` 的 `4c81c3a9…5c3a` 逐字一致。

### 6.6 `DECISIONS.md`、无新依赖、未 push、无仓内临时物

**(a) `DECISIONS.md` 我一行未改**：它在我开工前/mtime 2026-09-30 02:46 已有一处**并发批次**未提交改动（`+31` 行），我全程**没有 `git add` 它**；本批 4 个提交只含上表 21 个文件（`git show --stat` 已逐一核对）。**诚实限定**：我不能证明那 31 行来自谁；我能证明的是我的 4 个提交不含它，且它的 mtime（02:46）**早于**我本批首次写盘（03:33）。

**(b) 无新依赖**：

```
$ git diff 079cf82..HEAD --stat -- Cargo.toml Cargo.lock
(空)
```

⇒ 未新增任何依赖，也不需要说明理由与备选。

**(c) 未 push**：

```
$ git status -sb
## master...origin/master [ahead 4]
```

**(d) 仓内无本批临时物**：

```
$ git status --porcelain -uall
 M DECISIONS.md            # 并发批次，非本批
```

**诚实限定（必须写清）**：仓根有一个 `%DST%/` 目录（内含 `red/`、`green/` 与 7 个文件），它**不是**本批产物——它是**既有物**：mtime 为 **2026-09-24**（早本批 6 天），且被 `.gitignore:52` 忽略（`git check-ignore -v '%DST%/green' -> .gitignore:52:%DST%/`），因此它不出现在 `git status --porcelain` 里。**我无法核实它的来源**（可能是某次 `cmd` 里 `%DST%` 未被展开留下的目录），但可以核实"不是我建的"：全部 7 个文件的 mtime 都落在 2026-09-24，而本批首次写盘是 2026-09-30 03:33。本批所有临时物均在仓外（§6.7）。

我另发现并**当场修掉**了自己在**开发中间态**造成的一个仓内污染：早期版本的 `tests/prompt_shell_contract.rs` / `role_shell_contract.rs` 会把未解析的 `$HOH_ARTIFACT_DIR` / `%HOH_ARTIFACT_DIR%` 当相对路径，在仓根留下两个目录。修法是把 `--args-file` 路径**先按角色环境解析**，解析不出来的 token 直接跳过（`resolve_path` / 内联解析），并在两个文件里各跑一次确认不再产生仓内目录：

```
$ cargo test --offline --test role_shell_contract --test prompt_shell_contract   # 全绿
$ git status --porcelain -uall | grep -v '^ M'    -> 只有三个 ?? 新文件（本批产出）
```

### 6.7 仓外临时物

```
$ cygpath -w /c/Users/wyl/AppData/Local/Temp/dr66
C:\Users\wyl\AppData\Local\Temp\dr66
$ find /c/Users/wyl/AppData/Local/Temp/dr66 -type f | wc -l -> 37
```

内容：`patch_*.py`、`prefix_red.py`、`plants.py`、`cmd_probe.py`、`probe_stub.py`、`msg1..4.txt`、`redo_commits.py`、`plant-*.txt`（4 份原始植入输出）、`prefix-red.txt`、`plant-backup/**`、`cmd-probe/**`。

**诚实披露**：与 DR-64 不同，这批**我没有删除**仓外临时物——因为报告需要逐字引用 `plant-*.txt` 与探针输出，而"报告写完后不再修改"意味着我无法在引用后再补删除证据。这些文件**全部在 `%TEMP%` 下，不在仓内**（任务书的要求是"临时物一律建在仓外"，已满足）；如需清理，`rm -rf "C:\Users\wyl\AppData\Local\Temp\dr66"` 即可，不影响仓库任何状态。

### 6.8 三个假绿陷阱：各实测 + 正确读法

**① `git diff` 对不存在的 pathspec 静默 exit 0**

```
$ git diff --stat -- definitely/not/a/real/path ; echo exit=$?   -> exit=0（空）
$ git diff --stat -- src/runtime/run_loop.rs ; echo exit=$?      -> exit=0（空，形状无差别，但该文件确实有改动）
```

⇒ "diff 为空"不能当"没改"的证据。本报告凡"未改"的结论一律配 **mtime** 或 **嵌套仓 status**。

**② `cmd` 的 `^` 会静默改写 revision（故凡 `rev^` 只在 bash 做）**

```
$ (bash) git -C godot-mcp/godot rev-parse HEAD^  -> bdf654b1086d27999e2a278ad187fadc40ce034c
$ (bash) git -C godot-mcp/godot rev-parse HEAD   -> fc63af77c33368c4a1bb839c95d19750554f63a3
$ cmd //c "git -C godot-mcp/godot rev-parse HEAD^" -> fc63af77c33368c4a1bb839c95d19750554f63a3  ← caret 被吃掉
```

本报告**没有**依赖 `rev^` 的结论。

**③ 外层仓不跟踪引擎树**（见 §6.2）：`git status` 干净 ≠ 引擎树没变；我用的是 **paths API**（`git status --porcelain`）而非 `git diff`，并同时给出 15049/721/1 三个"能命中"的计数。

---

## 7. 遗留风险与未验证项（严格区分实测 / 推断）

**实测（本批有原始输出，可重跑）**

1. 交付文本里**不再存在**任何 POSIX shell 变量引用：5 个 `role_shell_contract` 测试 + 3 个 `prompt_shell_contract` 测试全绿。
2. 从 `godot-dev.md` 抽出的那条具体命令在真实 `LocalEnvironment`（cmd）里 **exit 0** 并启动真桩；同一命令的 POSIX 拼法 **exit 1**，输出 `'$HOH_HOH_BIN' is not recognized as an internal or external command`。
3. 零工程增量轮次：`ok=false`、`failed_role=developer`、`warnings` 含 `no_engineering_write` 与 `no_progress`、`finalize_run` 返回 2、`exit_code` 文件与 `meta.json.exit_code` 均为 2。
4. 工程写入检测可达：`project.godot/scenes/main.tscn/scripts/player.gd` 都在哈希内；新增 1 个 5 字节 `scripts/hoh_probe.gd` 即改变摘要；写 `.hoh/scratch/probe.txt` 不改变；把 `scripts` 加进排除集则不可见。
5. 全仓 `cargo test --offline`：**exit 0 / 392 passed / 0 failed / 7 ignored**（基线 372/0/7）。
6. 4 处植入全部使对应测试 exit 101，并以 4 种方式证明逐字节回退（§5.3）。
7. 禁区内所有断言（§6）：嵌套仓 HEAD `fc63af77…`、`status` 0、`ls-files` 15049、`runs/**` 与 `.workspace/mario/**` 窗口内 0 个新文件、PRD sha `4c81c3a9…5c3a`、`Cargo.{toml,lock}` 无改动、`ahead 4` 未 push。

**推断 / 未验证（不得当作已证）**

1. **E1 是否真的 met —— 未验证，且本批无法验证。** 只有真机轮能定：本批证明的是"零增量必然让自动化变红"与"根因（方言错配）已从交付文本中移除"，**不能**证明下一轮真机 `A_1 != A_0`。同样不声称 E3。
2. **首个成功工具调用的步点会提前多少 —— 推断。** 交付文本已不含 cmd 会拒绝的语法，但"模型据此就少烧步数"需要真机量化（约 75 分钟/轮，本批禁止）。
3. **"零增量 ⇒ 失败"的触发条件被限定为 Developer 的最后一次 attempt `exit_was_limits=true`。** 这是一个**有意的收窄**：`smoke-t7` 的实测形状正是"用尽步数且零增量"；如果放宽为"任何零增量即失败"，会与既有测试里大量"Developer 只写 `.hoh/**`、Tester 仍走完流程"的离线场景冲突（那批测试断言的是别的性质）。**代价必须写清**：一个正常结束（非 `LimitsExceeded`）却零增量的轮次**仍然**不会变红。这是已知的残余假绿面，我把它显式留在这里而不是掩饰；要关闭它需要同时迁移那几个离线场景的夹具（属于另一个逻辑改动，本批不做）。
4. **编辑器异步落盘风险仍未测。** DR-64 §7-4 的"一次成功的编辑器侧写入是否会被 `no_progress` 窗口漏掉"本轮**依旧**既未证实也未证伪：本批的零增量轮次是**合成**的（FakeHarness），没有经过真实编辑器。应在真机轮里补"写入后立刻 `hash_tree`、下一帧再 `hash_tree`"的对照。
5. **三约束的因果权重仍是推断**（shell 错配 / 步数预算 / DoD 指向当时不可通过的电池）；本批只移除了每一处的可测分量，没有做分离实验。
6. **`project_set_setting` 那次写入被哪一层吞掉**（cmd 引号解析 / hoh CLI / 引擎拒绝）本轮未追。
7. **非 Windows 平台的 `HOST` 分支只在编译期被选择，未在真机 POSIX 上运行过**：`ShellFlavor::Posix` 的渲染有单元测试与交叉断言（`the_generated_tools_index_uses_the_target_shell_syntax`、`a_rendered_command_can_be_rewritten_into_the_other_dialect`），但"在 Linux 上真的能跑"属于未验证项。
8. **构建缓存的一次真实故障（已解释，非代码问题）**：`git reset --mixed` 恢复文件时保留了**旧 mtime**，导致 cargo 的增量指纹一度继续复用旧 rlib，出现"源码已是新版、测试却按旧行为跑"的**假红/假绿**（表现为 `run_exit_code_for` 返回 6/0 而非 2）。我用 `touch src/**/*.rs tests/*.rs` 强制重编后一致复现为绿，并在此后的每次门都先 `touch`。**这是离线工作流的一个真实陷阱**，写在这里供后续批次避坑。

---

## 8. 诚实披露

1. **我没有改任何禁区**：未启动 Godot、未碰端口、未联网、未调模型端点、未跑真机轮、未写 `runs/**`、未改 `.workspace/mario/**`、未改 `.spec/hof-rs/PRD-mario.md`、**未改 `DECISIONS.md`**（它是并发批次的未提交改动，我一个字节没碰、也没 add）、未改 `godot-mcp/godot/**`（嵌套仓 `status` 为 0）、未 push、未改 `Cargo.{toml,lock}`。
2. **对调度者两条修正的落实**（它们来自 DR-64 的独立验收）：
   (1) `e1_increment` 的排除集**从 `config/hoh.yaml` 派生**并断言合并后的集合，配"真实产物路径进 `cache_excludes` 即致盲"的反例（§5.4）——这条正是 DR-64-ACCEPTANCE DEF-7；
   (2) `role_shell_contract` 写明了**占位符抽取规则**与**逐平台期望**、并保留"平台正确形式必须成功"的控制组（§2.1 契约测试段）——正是其 §7 的补强建议。
   另：报告**不沿用**被独立验收纠正过的三个数字/引用（首个真实工具结果应为**第 46 步 / 30.7 %** 而非 38/25.3 %；写动词调用应为 **2** 次而非 1 次；排除集/DR-11 警告的引用是 `src/adapter/godot.rs:3345-3358`，`policy.rs` 全长只有 452 行）。§2.3 中 K 的依据只用到了 46/150、115/150、22 个 scratch 文件这三个**已被独立复现**的量。
3. **我主动扩大了一处范围并说明理由**：任务书点名"两条永远绿的测试"，但同一根因还存在**第三处**同类问题（`tests/tool_discovery.rs::every_role_prompt_forbids_the_harness_sources` 对原始模板断言 `"$HOH_SCRATCH_DIR"`）。若只改两条，那条会在本批改动后**变红**（模板不再含 `$`），所以必须一起改成交付形式——这是**同源加强**，不是顺手改需求。
4. **我没有"顺手放宽"任何东西**：两处被改的断言都是**加强**（§4.1 逐条对比）；新增断言 20 条；`ignored` 未增；无测试被删。
5. **关于"报告写完即冻结"**：本报告之后我不再修改任何文件；`%TEMP%\dr66` 的临时物保留（理由见 §6.7）。
6. **我没有把推断写成实测**：§7 已分栏，凡推断处均标注。
7. **一处我差点错的地方**：我一度以为 `src/prompts/skills/*.md` 里的 `$HUD/Score.text` 这类 GDScript 字符串也被模板化了（那会是真 bug）；核对后确认 `sed` 只替换了 `HOH_*` 变量，GDScript 里的 `$HUD/Score` 原样保留（`godot-dev.md:175`、`:201-205` 未被触碰）。
8. **成本与边界**：真机重跑约 75 分钟且被任务书禁止；本报告的一切结论都建立在离线测试、真实 shell 执行（cmd，非 Godot）、以及冻结的既有证据上。
9. **不声称 E1/E3 已 met。**

---

## 附：本批 4 个提交（英文信息，均带 `(DR-66)`，本地未 push）

```
cb50575 test(DR-66): turn the two always-green prompt tests into executable contracts
973ed3a fix(DR-66): make a zero-engineering-write round fail instead of reporting ok
50477e7 fix(DR-66): de-noise the Developer completion definition and require an early increment
22eee2a fix(DR-66): render the prompt/tool-index/playbook shell syntax for the role's real shell
079cf82 (baseline) docs(spec): D259 ...
```

每个提交的内容与它对应的"事"一一对应（24 个文件：14 个生产文件含 1 个新增模块 + 7 个测试文件含 3 个新增 + `src/runtime/mod.rs` 的模块注册）。`git show --stat` 已逐提交核对，未见无关文件。
