# TASK-DR64-REPORT — E1 根因离线诊断：为什么 Developer 没有产生任何工程增量（`A_1 == A_0`）

- 任务书：`.spec/hof-rs/tasks/TASK-DR64.md`（本报告的唯一任务来源）
- 落点：`F:\moonbit-hof-rs`（外层仓，`master`；我开工时 HEAD=`5c83a5f`，D257）
- 性质：**纯离线只读诊断**。未启动 Godot、未联网、未调模型端点、未改任何源码、未重跑真机。
- 被诊断对象：`runs/smoke-t7/**`（真机 T=1，2026-09-29 13:26:16 → 14:41:14，115 文件，**只读**）
- 仓外临时物：`C:\Users\wyl\AppData\Local\Temp\dr64`（cygpath 自 `/tmp/dr64`），**已删除**，证据见 §6。
- 时间：2026-09-30 02:2x–02:4x（+0800）

---

## 1. 结论

**结论形式 = (B)：「E1 的判据本身可达；`A_1 == A_0` 不是测量缺陷，而是 Developer 那一轮的写入足迹 100% 落在哈希排除路径内，其整轮 150 步预算被「提示词↔真实 shell 的契约错配」和「一份指向当时结构性不可通过的证据电池的完成定义」吃光，唯一一次工程写入尝试也没有落地。」**

**置信度：高（约 0.9），但结论的两个分句置信度不同，必须分开看：**

| 命题 | 置信度 | 依据 |
|---|---|---|
| ① `A_0`/`A_1` 的测量**没有**排除 Developer 的写入路径，「测量使 E1 不可达」被**证伪** | **很高（≈0.98）** | 我按 `policy.rs:68-97` 独立重实现 `hash_tree`，在**三棵树**上逐字复现运行时的 `fc78d299…`；并做了离线对照实验：只往 `scripts/` 加 1 个新文件即得 `c541c5bb…` ≠ `A_0`（§2 Q1、§3.1） |
| ② 该轮 Developer **没有**改动任何被哈希文件 | **很高（≈0.99）** | 独立 mtime 普查：Developer 窗口内 `.hoh` 之外全工作区只有 4 个 `.godot/**` 缓存文件被动过（也是排除路径），工程文件 mtime 全部是 09-21/13:21（§2 Q4） |
| ③ 主因排序（shell 契约错配 > 预算 > DoD 指向不可通过的电池） | **中（≈0.6，属推断）** | 三个角色的 150 条 assistant 消息**全部 `content` 为空**，模型**没有留下任何一句自述意图**；排序是我从动作序列推断的，不是实测（§7） |
| ④ 唯一一次工程写入尝试「没落地」 | **高（≈0.9）；但「被哪一层吞掉」是推断** | 备份文件存在（`cp` 跑了）、`project.godot` 与备份逐字节相同且 mtime 早于该轮、两个 `--args-file` 从未生成、整条命令输出为空（§2 Q4） |

**一句话回答头号嫌疑**：`hash_tree` 的排除集只有 `{.hoh, .git, .godot, .import}`，Developer 唯一被指定的临时目录 `HOH_SCRATCH_DIR`（即 `.hoh/scratch`）**正好**在其中；所以「测量排除了 Developer 写的文件」这个描述**对了一半**——排除的是它**被要求**写的地方，而工程写入路径（`project.godot`/`scenes/**`/`scripts/**`）**完全在哈希里**。E1 **不是**不可达。

**不声称 E1 或 E3 已 met。** 本轮只做归因，不做修复。

---

## 2. 五个问题逐条回答

### Q1 — `A_0`/`A_1` 到底测什么？一次成功的轮次**是否可能**产生 `A_1 != A_0`？

**定义位置（唯一的哈希实现）**

- `src/runtime/policy.rs:68-97` `hash_tree(root, excludes)`：`WalkDir` 枚举**所有普通文件**，跳过被排除的相对路径，按 `relpath` 排序后对每条喂
  `relpath \n byte_len \n bytes \n`，取 `sha256` 的 hex。**没有**任何「只算某类文件」或「只算 Git 跟踪文件」的逻辑。
- 排除集来自 `HashExcludes::merged()`（`src/runtime/policy.rs:38-47`）：恒有 `".hoh"`、`".git"`，再并入 adapter 的 `cache_excludes()`。
  - `src/adapter/godot.rs:3354-3358`：`cache_excludes()` = `[".hoh", ".git"]` + `config.cache_excludes`。
  - `config/hoh.yaml:47`：`cache_excludes: [".godot", ".import"]`。
  - 匹配规则 `is_excluded`（`policy.rs:51-55`）：`rel == exclude` 或 `rel` 以 `"{exclude}/"` 开头。
  - ⇒ 实际排除集 = **`{.hoh, .git, .godot, .import}`**，仅此四项。

**`A_0`/`A_1` 的取点**

- `A_0`：`src/runtime/run_loop.rs:421` `store.snapshot_role(&workspace, &excludes, 0, "init", "A0 initial artifact")` — 在第 1 轮任何角色之前。
- 无增量判据：`run_loop.rs:707` `h_dev_before = hash_tree(&workspace, &excludes)`（在 `write_inputs` 之后）→ `run_loop.rs:797` `h_dev_after` → `run_loop.rs:798` `if h_dev_before == h_dev_after { … NoProgress … }`。
- `A_1`：`run_loop.rs:954` `h_det = hash_tree(&workspace, &excludes)` → `:955-961` `snapshot_role(… "A1 after the developer and deterministic stages")`，`debug_assert_eq!(version.candidate_id, h_det)`。

**关键问题：按这个测量，成功轮次能不能得到 `A_1 != A_0`？——能，且我离线证明了。**

我按 `policy.rs:68-97` 在 Python 里**独立重实现**同一算法（同排除集），对三棵树计算：

```
$ python hash_tree.py .workspace/mario runs/smoke-t7/iter-1/candidate \
    runs/smoke-t7/versions/fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c
.workspace/mario        files: 17  hash_tree digest: fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c
runs/smoke-t7/iter-1/candidate  files: 17  hash_tree digest: fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c
…/versions/fc78d299…     files: 17  hash_tree digest: fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c
```

17 个文件的集合（**这就是 `A_0`/`A_1` 的全部内容，也就是 Developer 的合法写入靶子**）：

```
project.godot, scenes/main.tscn, scripts/README.md,
scripts/{brick,coin,enemy,goal,main,player,question_block}.gd 及各自 .gd.uid
```

离线对照实验（把工作区**复制**到仓外，绝不碰真工作区）：

```
ws0（未改动的拷贝）                      files=17  digest=fc78d299…   == A_0
ws1（+scripts/hoh_probe.gd，8 字节新文件） files=18  digest=c541c5bb782496c1936af73235d1468b85017b1713bc565b5c2c51a4a07d4b67  != A_0
ws2（+.hoh/probe.txt）                   files=17  digest=fc78d299…   == A_0（排除路径不可见）
```

**判定**：**Q1 的头号嫌疑被证伪。** ①测量**能**看见 Developer 对任何工程文件的增/改/删；②不可见的**只有**写入 `.hoh/**`（含被指定的 scratch）、`.git/**`、`.godot/**`、`.import/**`。E1 的判据**可达**。

> 附注（诚实）：我的重实现复现了运行时的 digest 逐字相同，这比"两次独立实现互相印证"更强；但它是**重实现**，不是调用 Rust 的 `hash_tree` 本身（本批不编译、不运行 `cargo`）。

---

### Q2 — `LimitsExceeded` 是哪个限制？实际值 vs 上限，在哪一行触发？

**答案：步数上限（`step_limit`）。实际 = 150 次模型调用，上限 = 150，第 151 次调用被拒。**

证据链（全部来自原始记录 + 依赖源码）：

| 环节 | 证据 |
|---|---|
| 上限值 | `config/hoh.yaml:14` `step_limit: 150`；轨迹内部也记下了同一值：`runs/smoke-t7/iter-1/traj/developer.attempt1.json` → `info.config.agent.step_limit = 150` |
| 实际消耗 | 同文件 `info.model_stats.api_calls = 150`；`hoh.usage.calls = 150`；`runs/smoke-t7/iter-1/result.json.usage[1].calls = 150` |
| 触发语义 | mini（`F:\RustProjects\mini-swe-agent-rust-mini\rust`）`src/agent.rs:161-173` `check_limits()`：**第一支** `self.config.step_limit > 0 && self.n_calls >= self.config.step_limit` → `FlowInterrupt::limits_exceeded()`；该函数由 `query()` 在**每次取模型回复前**调用（`agent.rs:175-177`：`self.check_limits()?; self.n_calls += 1;`） |
| 上限值来源 | `src/harness/mini.rs:64-75` 把 `inv.limits` 逐项灌进 `AgentConfig`（`:67` `step_limit`） |
| 排除成本上限 | `agent.rs:163` 成本支要求 `cost_limit > 0.0`；`config/hoh.yaml:17` `cost_limit: 0.0`（`src/harness/mini.rs:68` 原样传入）⇒ 成本支**恒假**，`cost_limit` 被结构性禁用 |
| 排除墙钟上限 | `config/hoh.yaml:18` `wall_time_limit_seconds: 3600`；实测 `duration_ms = 3095229` = **3095.2 s = 3600 的 86.0 %**，未达；且墙钟超限走的是**另一个**中断种类 `FlowInterrupt::time_exceeded()`（`agent.rs:167-171`），其 `exit_status` 是字符串 **`TimeExceeded`**（`lib.rs:204-221` `InterruptKind`），而实测状态是 `LimitsExceeded`（`result.json.attempts[1].exit_status`、轨迹末条 `messages[337] = {"exit_status": "LimitsExceeded"}`） |
| 排除格式错 | `max_consecutive_format_errors = 3`（`config/hoh.yaml:19`）；其终止串是 `RepeatedFormatError`（`agent.rs:407-412`），未出现 |

**三个角色同时命中同一上限**（这条把"巧合"排除掉了）：

| 角色 | `exit_status` | `calls` | `duration_ms` | 上限 |
|---|---|---|---|---|
| planner | `LimitsExceeded` | **150** | 866 202 | step_limit=150, wall=3600 |
| developer | `LimitsExceeded` | **150** | 3 095 229 | 同上 |
| tester | `LimitsExceeded` | **150** | 524 143 | 同上 |

`runs/smoke-t7/iter-1/result.json.attempts[*]`、`durations_ms`、`usage[*]`。

**量化**：Developer 用满 **150/150 步**，还剩 **3600 − 3095 = 505 s 墙钟预算未被使用**；即"预算以步数而非时间的形式被耗尽，且耗尽瞬间剩余步数为 0"。

---

### Q3 — `no_progress` 是谁发出的、判据是什么？是因还是果？

**发出者与判据（唯一发射点）**：`src/runtime/run_loop.rs:797-807`

```
797  let h_dev_after = hash_tree(&workspace, &excludes)?;
798  if h_dev_before == h_dev_after {
799      let warning = ContractViolation::NoProgress.code();      // src/model.rs:345 / :356 => "no_progress"
800      iter_warnings.push(warning.to_string());
801      append_warning(&run_dir, &format!(
804          "iteration {iteration}: {warning} (the developer stage produced no change)"))?;
```

全仓仅此一处触发（`grep NoProgress`：`model.rs:345/356` 是枚举与字符串，`run_loop.rs:799` 是唯一使用者）。

**原始记录**：`runs/smoke-t7/warnings.log` 第 2 行即该文本；`runs/smoke-t7/iter-1/result.json.warnings = ["qa_scope: …", "harness_source_read", "no_progress"]`。

**它是因还是果？——是「果」，而且是"纯粹的比较结果"，与 `LimitsExceeded` 无因果关系：**

1. 判据只是一个**哈希相等比较**，与退出状态无关。两个哈希都在 Developer **进程已经退出之后**才取（`:707` 在 `write_inputs` 之后、`:724` `invoke_once(...).await?` 返回之后、`:797` 才取第二个）。
2. 它**只追加一条 warning**：`result.json.ok = true`、`failed_role = null`、`reason = "ok"`、`exit_code = 0`。⇒ **`no_progress` 不是失败信号，也不是任何东西的原因**；它是"Developer 没改动被哈希文件"这一事实的**描述**。
3. 反过来，`LimitsExceeded` 也**不是** `no_progress` 的充分/必要条件：planner 与 tester 同样是 `LimitsExceeded`，但两者都留下了合法工件（`runs/smoke-t7/iter-1/{plan.md,evidence.json}`），且 `attempts[0].artifact_valid = true`；而 Developer 的 `artifact_valid` 判的是"工程是否可用"（`src/adapter/godot.rs:3363-3365` → `:307-333`），本轮为 `true` 却仍零增量。
4. 附带发现（**这是本轮真正的可观测性缺口**）：round 报 `ok=true / exit_code=0` 而 E1 **not_met**。`no_progress` 只是 warnings 里的一行字符串，`result.json` 的布尔判据（`ok`）与工件闸门（`artifact_gate.launchable=true`）都不会变红 ⇒ **自动化层面的"假绿"**：仅看 `ok`/退出码会漏掉 E1 的失败。

---

### Q4 — Developer 到底做了什么？工具调用序列与分类（提议 / 真写盘 / 写盘被拒）

**A. 基础计数（结构化抽取，全部可复现）**

| 项 | 值 | 证据指针 |
|---|---|---|
| assistant 步数（含 tool_calls 的消息） | **150** | 轨迹 `messages`：`role=='assistant'` 且 `tool_calls` 非空 = 150 |
| 工具调用总数 | **185**，**全部**是 `bash` | 同上；`Counter({'bash': 185})`，非 bash 调用 **0** |
| 模型调用数 | 150 | `info.model_stats.api_calls`、`hoh.usage.calls` |
| 自然语言自述 | **0 条** | 150 条 assistant 消息的 `content` **全为空**；`extra.response.choices[*].message` 只有 `{content, role, tool_calls}`，**无 `reasoning_content`**（三种角色皆然） |
| 退出 | `LimitsExceeded` | `messages[337]` |

**B. 真实调用的 MCP 工具（按命令文本抽取）**

```
editor_get_errors            7
editor_play_scene            6
editor_stop_scene            5
running_game_get_scene_tree  3
project_validate_script      1
project_get_info             1
project_get_settings         1
project_set_setting          1      <-- 整轮唯一一个「写动词」工具
```

**C. 分类（提议 / 真写盘 / 写盘被拒）**

| 类别 | 计数 | 证据 |
|---|---|---|
| **工程写入（真写盘）** | **0** | 185 条参数里 `project_create_script` / `project_edit_script` / `project_write_text_file` / `project_create_scene_file` / `project_edit_scene` / `project_delete_file` / `project_import_file` / `editor_setup_collision_shape` 的出现次数**全部为 0** |
| **提议但未落地的工程写** | **1 步**（含 `project_set_setting` ×2） | `messages[325]`：先 `cp project.godot .hoh/scratch/project.godot.pre_iter1`，再写两个 args 文件，再 `hoh tools call project_set_setting`（`godot_mcp/capture=every_call`、`godot_mcp/trace_file`）。`messages[326]` 的观测是**空输出**、`returncode=0` |
| **写盘被拒（策略拒绝）** | **0** | 185 条输出里 `may not mutate the artifact` / `not in this role's allowlist` / `denied` / `forbidden` 出现次数**均为 0**（且 Developer 在 `src/runtime/policy.rs:280-288` 里 `tool_allowed(Developer, _) == true`，本来就不会被拒） |
| **真写盘（scratch）** | 窗口内 **22** 个文件 | mtime 普查：`.workspace/mario/.hoh/scratch/**` 中 mtime ∈ [2026-09-29 13:40, 14:33) 的文件 = **22**（`mc.py`、`drv.py`、`longrun.py`、`hang_test.py`、`editor_side.py`、`move_test.py`、`batt.py`、`parse.py`…） |

**`project_set_setting` 那次为什么算"未落地"——四条独立测量**

1. 该工具的契约（`godot-mcp/godot/modules/mcp_server/docs/tools_list.renamed.json`，name=`project_set_setting`）明写：调用成功时它用引擎的**整文件写入器重写整个 `project.godot`**，并提示"调用前自己备份"。
2. `.workspace/mario/project.godot` 现在是 **1700 B、mtime `2026-09-29 13:21:03.803`、sha256 `e4855a18cf765e206c6aad87bfd499c76e5a9d4245b6ca88b00e3e68a91b4246`**，且 `grep godot_mcp` **无任何命中** ⇒ `godot_mcp/capture` 从未被写入。mtime **早于**该轮 Developer 会话（≈13:40–14:32）。
3. `diff .hoh/scratch/project.godot.pre_iter1 .workspace/mario/project.godot` ⇒ **IDENTICAL**（备份长得一样，原件一个字节没变）。
4. 同一条命令里的两个 `printf` 目标 `args/set_capture.json`、`args/set_trace.json` **至今不存在**；而 `cp` 的目标 `project.godot.pre_iter1` 存在（14:28:20）⇒ 该 `bash -c "…"` 的**前段执行了、后段没有**。紧接的下一步（`messages[335]/[336]`）同一个形状直接抛出 `bash: -c: line 1: unexpected EOF while looking for matching '"'` —— 同一个失败族。

**D. 写入足迹的独立 mtime 普查（比轨迹更硬）**

Developer 会话窗口取 `[2026-09-29 13:40:00, 14:33:00)`（轨迹文件 mtime 13:40:..；会话结束 14:32:24）：

```
$ find .workspace/mario -path .workspace/mario/.hoh -prune -o -type f \
    -newermt '2026-09-29 13:40:00' ! -newermt '2026-09-29 14:33:00' -print
.workspace/mario/.godot/editor/editor_layout.cfg
.workspace/mario/.godot/editor/filesystem_cache10
.workspace/mario/.godot/editor/script_editor_cache.cfg
.workspace/mario/.godot/editor/shader_editor_cache.cfg
count = 4
$ find .workspace/mario/.hoh/scratch -type f -newermt … ! -newermt … | wc -l
22
$ for f in project.godot scenes/main.tscn scripts/player.gd scripts/main.gd scripts/coin.gd; do ls -la --time-style=full-iso .workspace/mario/$f; done
2026-09-29 13:21:03  project.godot          <-- 早于 Developer
2026-09-21 14:50:55  scenes/main.tscn
2026-09-21 13:38:35  scripts/player.gd
2026-09-21 13:42:32  scripts/main.gd
2026-09-21 13:43:07  scripts/coin.gd
```

⇒ 整个窗口内，`.hoh` **之外**被动过的 4 个文件全在 `.godot/**`（**排除路径**）；22 个 scratch 文件在 `.hoh/**`（**排除路径**）；**工程文件 0 个**。这与 `A_1 == A_0` 完全一致，且是**独立于轨迹**的证据。

**E. 那 150 步到底花在哪（实测计数 + 我做的归类）**

| 量 | 值 |
|---|---|
| **第一个成功的 `hoh tools call` 出现在第 38 步**（0 基索引；即用掉 38/150 = **25.3 %** 预算后才第一次通过文档指定的通道拿到结果） | 轨迹逐条比对 `returncode==0` 且输出非空 |
| 命令里出现**显式** `bash -c` / `bash -lc` 包裹的步数 | **115 / 150**；首次出现在第 29 步，此后 121 步里只有 6 步没包 |
| shell 错配的错误签名计数 | `The system cannot find the path specified` **10** 次；`is not recognized as an internal or external command` **4** 次；`was unexpected at this time`（cmd 的 `for` 方言）**3** 次；`unexpected EOF while looking for matching '"'` 首次出现在第 67 步 |
| 命令/输出提到 `$HOH_…` 的步数 | **17** 步 |
| 我做的粗归类（**推断，见 §7**） | 游戏探针/输入实验 ≈37 步；shell/环境摸索 ≈28 步；harness CLI 管道搭建 ≈24 步；工程侦察(读) ≈13 步；读上一轮证据 ≈10 步；其余 ≈38 步；**工程写入 0 步** |

`result.json` 的两个字段与此互证：`out_of_tree_writes = []`、`artifact_hygiene.suspicious_files = []` ⇒ Developer 既没往树外写，也没在工程里留下探测文件。另有一条 `harness_source_read` warning（探测器 `run_loop.rs:214-233` + `hygiene.rs:273-313`，DR-38）⇒ 它的命令确实越到了 harness 仓根（如 `messages[148]` 的 `cd /f/moonbit-hof-rs; ./target/release/hoh.exe --help`、`messages[237]` 的 `find /f/moonbit-hof-rs …`）。

---

### Q5 — 是否存在 harness 侧缺陷压制了增量？逐条排除或确认

| # | 假设 | 判定 | 证据 |
|---|---|---|---|
| ① | 摘要**排除了** Developer 写入的文件 | **证伪** | 排除集只有 `{.hoh,.git,.godot,.import}`（`policy.rs:38-47`、`godot.rs:3354-3358`、`config/hoh.yaml:47`）；17 个被哈希文件**就是** `project.godot`/`scenes/**`/`scripts/**`（我独立重实现复现 `fc78d299…`）；ws1 实验证明加 1 个 `scripts/*.gd` 即改摘要 |
| ② | 摘要**在写入落盘之前**计算 | **证伪（对本轮而言）** | `h_dev_after`（`run_loop.rs:797`）在 `invoke_once(...).await`（`:724`，真的子进程，`mini.rs:94` await；mini 的 `LocalEnvironment` 每次动作 `spawn` 后 `child.wait()` + 读净 stdout/stderr，`local.rs:89-111`）返回之后；`write_inputs`（`:705`）在 `h_dev_before`（`:707`）**之前**且只写 `.hoh`。**更强的反证**：`A_1` 在 `:954`（整个确定性电池、含 `editor_play_scene` 等编辑器官交互之后）取，它**也**等于 `A_0` ⇒ 任何"延迟落盘"解释都活不下来 |
| ③ | Developer 写到了**被哈希排除**的路径 | **确认（这是本轮经验分布的主因）** | 见 Q4-D/E：22 个 scratch 文件 + 4 个 `.godot/**`，**全部**在排除集内；`developer.md:81-86` 的 `[scratch-discipline]` 还**明确要求**把临时物写到 `$HOH_SCRATCH_DIR`（"inside `.hoh/`, which is excluded from the artifact hash"）⇒ 它对哈希**按设计**不可见 |
| ④ | 写入成功但**副本/视图**没同步 | **证伪** | 我用独立重实现在**工作区 / `iter-1/candidate` / `versions/fc78d299…`** 三棵树上得到同一摘要、同为 17 文件；`run_loop.rs:1016-1054` 的 pre-QA 漂移断言也没有报警（`warnings` 里无 `workspace_drift_before_qa`） |

**额外发现（任务书没列、但比 ①–④ 更贴近根因的一个 harness↔提示词契约缺陷）**

- 提示词让角色用 **POSIX** 语法调工具：`src/prompts/developer.md:23` `Use \`$HOH_HOH_BIN tools call <tool> --args-file <path>\``；`src/prompts/mod.rs:44`（developer 任务）与 `:32`/`:60`（planner/tester 的 submit）同形；`src/tools/index.rs:152,225`（自动生成的 `.hoh/TOOLS.md`）与 `src/adapter/godot.rs:3497-3520`（证据剧本）也全是 `$HOH_…`。
- 但角色的**真实 shell 是 `cmd.exe`**：mini `rust/src/environments/local.rs:66-76` 在 Windows 上 `Command::new("cmd").arg("/C").raw_arg(command)`。
- 实测（`runs/smoke-t7/iter-1/traj/developer.attempt1.json`）：
  - `messages[10]` 的 env dump 里 `COMSPEC=C:\WINDOWS\system32\cmd.exe`，且带 cmd 专有的隐藏变量 `=F:=F:\moonbit-hof-rs\.workspace\mario`（附带证明**cwd 确实是工作区**，不是副本）；
  - `messages[2]`（第 0 步）`pwd; ls -la; …` → `The system cannot find the path specified`；
  - `messages[76]` `"$HOH_HOH_BIN" tools call …` → `'$HOH_HOH_BIN" tools call editor_get_errors --args-file "$HOH_SCRATCH_DIR' is not recognized as an internal or external command`；
  - `messages[39]` `for f in …; do …; done` → `f was unexpected at this time`；
  - `messages[78]` `echo "…"` 把整行当字符串回显 —— cmd 不认 `;`。
  - 反之 `messages[79]/[80]` 用 `%HOH_SCRATCH_DIR%` **成功** ⇒ 环境正常，是语法不匹配。
- **这个错配把测试也骗过去了**（测试级假绿）：`tests/artifact_hygiene.rs:112-115` 只断言提示词**包含**字面量 `$HOH_SCRATCH_DIR`；`tests/developer_contract.rs:57-74`（`godot_dev_skill_is_a_real_recipe_book`）只断言技能文本**包含** `"$HOH_HOH_BIN tools call"`。两条测试**结构上无法**发现"提示词要求的语法在角色真实 shell 里跑不了"，只要字符串还在就永远绿。

---

## 3. 量化约束点（结论 B 的实证部分）

### 3.1 「测量可达」的量化（用于把结论钉在 B 而不是 A）

| 实验 | 结果 |
|---|---|
| 未改动拷贝（== `A_0`） | 17 文件，`fc78d299…` |
| +1 个新工程文件 `scripts/hoh_probe.gd`（8 B） | **18 文件，`c541c5bb782496c1936af73235d1468b85017b1713bc565b5c2c51a4a07d4b67`** ≠ `A_0` |
| +1 个 `.hoh/probe.txt` | 17 文件，`fc78d299…`（不变） |

⇒ 判据对"1 文件 / 8 字节"的工程增量即敏感。**E1 可达。**

### 3.2 约束点 1 — 步数预算（硬上限，实测用满）

- 位置：`config/hoh.yaml:14`（`step_limit: 150`）→ `src/harness/mini.rs:67` → mini `rust/src/agent.rs:162`。
- 实测：Developer `calls = 150 = step_limit`，第 151 次调用被 `check_limits()` 拒绝；用时 3095.2 s / 3600 s（**86.0 %**），**505 s 墙钟预算未用**。
- 三个角色**都**恰好撞 150 —— 上限是主约束，不是偶发。

### 3.3 约束点 2 — 提示词↔真实 shell 的契约错配（实测吃掉的步数）

- 位置：`src/prompts/developer.md:23`、`src/prompts/mod.rs:44`（+`:32`/`:60`）、`src/tools/index.rs:152,225`、`src/adapter/godot.rs:3497-3520` ↔ mini `rust/src/environments/local.rs:66-76`。
- 量化：
  - **25.3 %（38/150）** 的预算在**第一次成功**的 `hoh tools call` 之前就烧掉了（首个成功在第 38 步）；
  - **115/150** 步被迫用显式 `bash -c` 重写命令；首次包裹在第 29 步，此后 121 步里只剩 6 步没包；
  - 4 类 shell 方言错误共 **17 次**（10 + 4 + 3，另加首次出现在第 67 步的 quote-EOF 族）；
  - `$HOH_…` 相关步数 17 步；
  - 三份角色轨迹里的 `$HOH_HOH_BIN` 引用：developer 9、planner 2、tester 4 次；planner 还试过 `%HOH_HOH_BIN%` 1 次（即它也踩了同一个坑）。

### 3.4 约束点 3 — 完成定义指向一份当时结构性不可通过的证据电池

- 位置：`src/prompts/developer.md:35-56` 的 `[definition-of-done]` 第 1 条把"计划承诺的每个可观察行为都能从**你之后跑的那份确定性证据电池**里看到"定为完成条件；`:27-30` 的 `[self-test]` 要求"每次有意义改动后重跑对应路径"。
- 当时的电池真实状态（`runs/smoke-t7/iter-1/result.json.battery_passes[0]`）：11 步里 **`input_channel_probe=false`、`node_and_collision_assertions=false`**，其余 9 步 true。
- 而这两步失败的原因在 **hof-rs 自己**（TASK-SMOKE-T7-REPORT §2.2/§7：`godot.rs:1597-1604` 硬传 `"scene_path":"current"` ⇒ 恒 `-32602`；`godot.rs:1253-1257` 与 `:2051-2055` 读顶层 `name` ⇒ 恒判 `missing`）。
- **重要且诚实**：这两处在**我读的 HEAD（`5c83a5f`）上已经被 DR-58 修好了**（`godot.rs:1253-1257` 现在用 `node_properties_read`，`godot.rs:1596-1606` 注释明确"成员表只有 `steps`"且 `axis_args` 不再含 `scene_path`）。也就是说：**约束点 3 针对的是 smoke-t7 当时那个二进制（构建于 `9ff9cd2`，13:22:54），不是现在的 HEAD。**
- 量化（推断，见 §7）：轨迹显示 Developer 在第 26–31 步读 `.hoh/deterministic/{battery.json,deterministic.log,mcp-errors.jsonl}` 与上一轮证据，此后 ≈37 步用于反复起停游戏 + `execute_gdscript`/`get_node_property_samples` 探针，**没有再回到"实现"**。

### 3.5 约束点 4 — 唯一一次工程写入尝试未落地

见 Q4-C 的四条测量。**净效果 0 字节**：`project.godot` 与备份逐字节相同、mtime 早于会话、目标 args 文件不存在、命令输出为空。

---

## 4. 两条候选修法 + 风险 + 回滚点

> 两条**互不替代**：修法 1 治"通道根本不可用"，修法 2 治"预算与完成定义把角色推向错误目标"。建议**先 1 后 2**，因为 1 是乘数。

### 修法 1（首选）：让"文档里写的调用方式"在角色的**真实** shell 里成立

- 做法（二选一，推荐 (a)+(c) 同时做）：
  - **(a) 平台化提示词与工具索引**：把 `src/prompts/developer.md:23`、`src/prompts/mod.rs:32/44/60`、`src/tools/index.rs:152,225`、`src/adapter/godot.rs:3497-3520` 的调用样例改成**由运行时按平台渲染**（Windows 用 `%HOH_HOH_BIN%` / 引号路径，或统一给一条不含 shell 变量的绝对路径样例），而不是硬编码 `$HOH_…`。
  - **(b) 让角色 shell 变成 POSIX**：在 Windows 上把 `LocalEnvironment` 的 shell 指向 Git Bash/`sh`（`local.rs:66-76`），使提示词不必改。
  - **(c) 加**契约测试**：从提示词文本里**抽出**命令，在真实 `LocalEnvironment`（同 cwd、同 `role_env`）里执行一次，断言它真的跑起来（见 §5(b)）。
- 风险：(a) 使提示词成为平台相关产物，跨平台采样会分叉 —— 用**单一渲染函数**收口可缓解；(b) 引入对外部 `bash.exe` 的部署依赖，且要与 C1「Windows 走 cmd.exe」的既有表述对齐（改的是实现，需同步 `REQUIREMENTS.md` C1 的措辞）；(c) 会在 CI 上起真实 shell，慢但确定性可控。
- 回滚点：三条改动各自独立、无数据迁移；`git revert` 单个 commit 即可回到现状。**不动引擎树**（D242），因此无嵌套仓回滚。

### 修法 2：把 Developer 的预算与完成定义对齐到"先写出增量"

- 做法：
  - **(a) 完成定义降噪**：把 `developer.md:35-56` 第 1 条的"必须能从确定性电池看到"改为"电池的**通过与否由 harness 负责**；你只需保证 N1/N2 与计划优先级的**可观测性契约**"，并把电池已知失败项在 Developer 的输入里显式标为 **harness-side，不是你的修复目标**（避免它去修观测层）。
  - **(b) 预算结构化**：把单一 `step_limit`（`config/hoh.yaml:14`）拆成"前 K 步必须产生至少一次工程写入"的门（例如 K=40），未达成则记一条**独立**违约码（不要只留 warning），并在 `result.json` 里让 E1 类失败**真的变红**（治 §2-Q3 的假绿）。
- 风险：(a) 若措辞放松，可能削弱"不许只写代码不验证"的约束 —— 必须保留"可观测性"要求，只把**电池本身的缺陷**移出角色责任；(b) 新增违约码会改变 `result.json` 的 schema 与既有测试的期望，需要同步 `src/model.rs` 的 `ContractViolation` 与相关测试；步数门若设得太小，会在慢角色（planner 866 s）上误伤。
- 回滚点：配置与提示词改动可单独 revert；(b) 的 schema 变更向后兼容（只新增枚举值 + 新字段）即可安全回滚。

---

## 5. 钉死结论的最小测试设计（先红后绿）

### (a) `tests/e1_reachability.rs` — 钉死"测量能看见 Developer 的写入"

- **绿态断言**：在 `TempDir` 里造 `project.godot` + `scenes/main.tscn` + `scripts/x.gd`；`VersionStore::snapshot_role(..., 0, "init", "A0")` 得 `a0`；写一个新文件 `scripts/hoh_probe.gd`；`snapshot_role(..., 1, "developer", "A1")` 得 `a1`；断言
  `a1.version_id != a0.version_id`，且 `diff_manifests(&tree_manifest(A0), &tree_manifest(A1)).added == ["scripts/hoh_probe.gd"]`。
  **配对反例**：只写 `.hoh/probe.txt` ⇒ 断言 `a1.version_id == a0.version_id`。
- **先红**（必须人工确认它**确实因缺行为而红**，而不是因为它压根没跑）：把 `"scripts"` 临时塞进 `GodotConfig::cache_excludes`（一行植入），上面第一条断言必须失败（`a1 == a0`）。这同时证明"排除集一旦覆盖真实产物路径，R2/R3 的写入检测就被静默关闭"（`policy.rs:3348-3358` 自己写的警告）。
- 为什么它能钉死结论：如果 E1 的测量真有"排除 Developer 写入路径"的缺陷，这个测试在**未植入**的绿态下就会红。它把"可达性"变成可执行断言。

### (b) `tests/role_shell_contract.rs` — 钉死"提示词要求的调用语法在角色真实 shell 里可用"

- 做法：**从提示词/技能文本里抽出那条命令**（不要另写一份，否则又会漂移），把 `HOH_HOH_BIN` 指向一个**桩**（临时目录里的一个可执行脚本/`.cmd`，执行即在自己的 `$HOH_SCRATCH_DIR` 落一个 `marker` 文件）；用 `LocalEnvironment::new(LocalEnvironmentConfig { cwd: <temp ws>, env: role_env(...), timeout })`（**与 `src/harness/mini.rs:53-62` 同形**）执行抽出的命令；断言 `marker` 存在、`returncode == 0`。
- **先红**：在**当前代码**上，Windows 上这条断言必然失败，且失败文本应当是 cmd 的 `'$HOH_HOH_BIN" tools call …' is not recognized as an internal or external command`（或 `The system cannot find the path specified`）——**把期望的失败文本写进测试注释并实测一次**，才算真正的红。
  配套一条**对照**断言：同样的操作改用 `%HOH_HOH_BIN%` 必须成功 ⇒ 证明失败来自"环境/语法不匹配"，而不是测试或桩写错。
- **绿**：修法 1 落地后，两条断言都过（平台化提示词，或角色 shell 改成 POSIX 二选一）。
- 为什么它能钉死结论：它把"提示词要求的字符串"与"角色真实 shell 的能力"绑成一个可执行契约；现有 `tests/artifact_hygiene.rs:112-115` 与 `tests/developer_contract.rs:57-74` 只做字符串包含断言，**结构上永远绿**，是本轮最典型的测试级假绿。

---

## 6. 禁区自查（真实输出）

### 6.1 `runs/**` 未动 + 摘要自证

我自己的清单摘要 = 对每文件取 `sha256`，按 `"<relpath>\0<size>\0<sha256>"` 排序后再取 `sha256`（算法固定，可复算）：

```
== 开工前（同一会话内，动手之前） ==
runs/smoke-t6  files=135  manifest_digest=6bfc3e62d8abe1213d3de1535cf469148281c68f8f6884d273ac697452f97334
runs/smoke-t7  files=115  manifest_digest=e741d61d2cca78b54adb4896b04b9537ff3abc3da8118c89772c903cc9a33337
== 收工前（全部取证做完之后） ==
runs/smoke-t6  files=135  manifest_digest=6bfc3e62d8abe1213d3de1535cf469148281c68f8f6884d273ac697452f97334
runs/smoke-t7  files=115  manifest_digest=e741d61d2cca78b54adb4896b04b9537ff3abc3da8118c89772c903cc9a33337
```

同一会话内前后**逐字相同**；且整个 `runs/**` 的最新 mtime 是 `2026-09-29 14:44:16`（`runs/smoke-t7-experiment/e5_hash_tree.json`），而现在是 `2026-09-30 02:29`，相差约 12 小时 ⇒ 本会话**没有**写入 `runs/**`。任务书要求的"绝不重跑真机"也成立：我没有执行过 `hoh run`。

### 6.2 PRD（冻结的 S）

```
$ sha256sum .spec/hof-rs/PRD-mario.md
4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a  *.spec/hof-rs/PRD-mario.md
$ ls -la --time-style=full-iso .spec/hof-rs/PRD-mario.md
2026-09-20 23:21:21  .spec/hof-rs/PRD-mario.md          <-- 从未变过
```

与 `meta.json.spec.sha256` / D243 的 `4c81c3a9…5c3a` 逐字一致。

### 6.3 引擎树"未变更"——**用嵌套仓**，并证明 pathspec 真能命中

```
$ git -C godot-mcp/godot rev-parse --show-toplevel
F:/moonbit-hof-rs/godot-mcp/godot
$ git -C godot-mcp/godot rev-parse HEAD
fc63af77c33368c4a1bb839c95d19750554f63a3
$ git -C godot-mcp/godot log -1 --format='%H %ci %s'
fc63af77c33368c4a1bb839c95d19750554f63a3 2026-09-29 10:37:49 +0800 evid: fix a comment typo in the mcp029 guard block (TASK-154)
$ git -C godot-mcp/godot status --porcelain | wc -l
0
# ---- 非空洞性：证明这个仓库/这条命令真能看见东西 ----
$ git -C godot-mcp/godot ls-files | wc -l                       -> 15049
$ git -C godot-mcp/godot ls-files modules/mcp_server | wc -l    -> 721
# ---- 反向对照：一个不可能命中的 pathspec 同样静默 exit 0 ----
$ git -C godot-mcp/godot status --porcelain -- definitely/not/here ; echo exit=$?   -> exit=0
```

### 6.4 三个假绿陷阱：逐个实测 + 正确读法

**① `git diff` 对不存在的 pathspec 不报错**（⇒ "diff 为空"**不能**当证据）

```
$ git diff --stat -- definitely/not/a/real/path ; echo exit=$?
exit=0
$ git diff --stat -- src/runtime/run_loop.rs ; echo exit=$?      # 一个真实且干净的文件，形状完全相同
exit=0
```
两条输出都是空、退出码都是 0，**无法区分**。所以本报告的引擎结论一律来自嵌套仓 `status` + mtime/摘要，**不是**外层 `git diff`。

**② `cmd` 的 `^` 会静默改写 revision**（⇒ 所有 `rev^` 查询只在 bash 做）

```
$ git -C godot-mcp/godot rev-parse HEAD^   # bash
bdf654b1086d27999e2a278ad187fadc40ce034c
$ git -C godot-mcp/godot rev-parse HEAD    # bash
fc63af77c33368c4a1bb839c95d19750554f63a3
$ cmd //c "git -C godot-mcp/godot rev-parse HEAD^"     # cmd.exe
fc63af77c33368c4a1bb839c95d19750554f63a3               <-- 和 HEAD 一模一样：caret 被吃掉
$ cmd //c "echo A^B"    -> AB                          # 直接证明 ^ 是转义符
$ cmd //c "echo A^^B"   -> A^B                         # 加倍才还原
```
（`cmd //c` 中的 `//` 是 Git Bash 的路径转换规避；若用 `cmd /C`，MSYS 会把它当路径，cmd 只打印横幅、不执行 —— 这也是我实测到的。）本报告**没有**任何依赖 `rev^` 的结论。

**③ 外层仓不跟踪引擎树**（⇒ 外层 `git status` 干净 ≠ 引擎树没变）

```
$ git ls-files godot-mcp/godot | wc -l          -> 0        # 引擎树：0 个被跟踪文件
$ git ls-files godot-mcp | wc -l                -> 6484     # 但共用的外层仓在 godot-mcp/ 下确实跟踪 6484 个文件
$ git check-ignore -v godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe
.gitignore:33:godot-mcp/godot/	godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe
```
⇒ 任务书 D242 的表述需要精确化：**不是"外层仓不跟踪 `godot-mcp/`"，而是"外层仓不跟踪引擎树 `godot-mcp/godot/`（它被 `.gitignore:33` 忽略）"**。我读的 `godot-mcp/godot/modules/mcp_server/docs/tools_list.renamed.json` 属于**嵌套仓**（721 个被跟踪文件之一），只读访问。

### 6.5 仓内无临时物 + 仓外临时物已删除

```
# 仓内：外层仓工作树完全干净（含未跟踪）
$ git status --porcelain -uall | wc -l          -> 0
# 我的全部写入都落在仓外
$ cygpath -w /tmp/dr64
C:\Users\wyl\AppData\Local\Temp\dr64
$ find /tmp/dr64 -type f | wc -l                -> 802        # 脚本 + ws0/ws1/ws2 实验拷贝
$ rm -rf /tmp/dr64 && echo "rm exit=$?"
rm exit=0
$ if [ -e /tmp/dr64 ]; then echo "YES - FAILED"; else echo "NO - removed"; fi
NO - removed
$ if [ -e "C:/Users/wyl/AppData/Local/Temp/dr64" ]; then echo YES; else echo "NO - removed"; fi
NO - removed
# 删除后再复核
$ git status --porcelain -uall | wc -l          -> 0
$ git -C godot-mcp/godot status --porcelain | wc -l -> 0
$ sha256sum .spec/hof-rs/PRD-mario.md | cut -c1-64
4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a
```

**关于"仓内无临时物"的诚实限定**：这是一个**共享 checkout**，我工作期间父代理/兄弟批次在并发提交（我开工时 HEAD=`5c83a5f`，D257 的记录；`DECISIONS.md` mtime `2026-09-30 02:23:12`；`.spec/hof-rs/tasks/dr60-evidence/**` 62 个文件属另一批次且**已提交**）。所以"`git status` 干净"**不能**单独证明是我没动手；能证明的是：**本会话所有会写盘的调用都指向 `C:\Users\wyl\AppData\Local\Temp\dr64\`（已删），加本报告一个文件**；其余操作（读文件、python 离线分析、只读 git、`find`/`ls`/`sha256sum`、以及 `cmd //c echo`）都不写盘。

### 6.6 其他硬约束

- **未 push、未 commit**（本批只产出报告）。
- **未启动 Godot**、未碰任何端口、未联网、未调用任何模型端点：全部操作是文件读取、离线 Python、只读 git、`find`/`ls`/`sha256sum`/`cmd //c echo`。
- **未修改** `src/**`、`tests/**`、`config/**`、`godot-mcp/**`、`.workspace/mario/**`、`.spec/hof-rs/PRD-mario.md`、`DECISIONS.md`、`runs/**`。

---

## 7. 遗留不确定项（严格区分实测 / 推断）

**实测（有原始输出，可用文中命令重跑）**

1. `hash_tree` 的排除集 = `{.hoh,.git,.godot,.import}`；被哈希的是 17 个工程文件；`A_0 == A_1 == fc78d299…`（我自己重实现复现）。
2. 往 `scripts/` 加 1 个 8 字节新文件 ⇒ 摘要变为 `c541c5bb…`；往 `.hoh/` 加文件 ⇒ 摘要不变。
3. Developer：150 步 / 185 次调用，**全部**是 `bash`；工程写入工具出现 **0** 次；写动词工具 **1** 次（`project_set_setting` ×2，同一步）。
4. `project.godot` 1700 B / mtime `2026-09-29 13:21:03` / sha256 `e4855a18…` / 无 `godot_mcp` 键；与 `project.godot.pre_iter1` 逐字节相同；`set_capture.json`/`set_trace.json` 不存在。
5. mtime 普查：Developer 窗口内 `.hoh` 之外只有 4 个 `.godot/**` 文件；`.hoh/scratch` 22 个；工程文件 0 个。
6. 第一个成功的 `hoh tools call` 在第 38 步；115/150 步显式包 `bash -c`；4 类 shell 错误共 17 次。
7. 上限 = `step_limit: 150`（配置、轨迹内记录、三角色各 150 次调用三处互证）；墙钟 3095.2/3600（86.0 %）；成本上限因 `cost_limit>0.0` 守卫而禁用；墙钟超限的字符串会是 `TimeExceeded`，未出现。
8. `no_progress` 唯一发射点 `run_loop.rs:798-807`；该轮 `ok=true`/`exit_code=0`。
9. 三棵树（工作区/candidate/存储版本）字节同一，17 文件。
10. 引擎嵌套仓 HEAD `fc63af77c333…`、`status` 0 行、15049 个被跟踪文件；`runs/smoke-t6`/`smoke-t7` 前后摘要一致；PRD sha `4c81c3a9…5c3a`。
11. 三个陷阱的实测输出（§6.4）。
12. 三份角色轨迹的 assistant 消息 `content` **全空**、无 `reasoning_content`。

**推断（不得当作已证）**

1. **"Developer 把预算花在观测层而非实现上"的动机**：轨迹里**没有**任何自述文字（150 条 content 全空），所以这是我从"读 `.hoh/deterministic/**` → 反复起停游戏 + `execute_gdscript` 探针 → 全程 0 次工程写入"的**动作序列**推断的。动作序列本身是实测，动机是推断。
2. **`project_set_setting` 被哪一层吞掉**：我实测到"备份 cp 落盘、两个 printf 目标没生成、两次 hoh 调用输出为空、project.godot 未变"。但究竟是 cmd 的引号解析截断了 `bash -c "…"`、还是 `hoh tools call` 自身失败后输出被丢弃、还是引擎侧拒绝，**本批无法判定**（离线且不许碰编辑器）。同族失败在 `messages[336]` 被模型自己撞出（`unexpected EOF while looking for matching '"'`），所以"引号解析"是最可能的机制，但仍是推断。
3. **主因排序（shell 契约 > 预算 > DoD）**：三个约束的作用**没有被实验分离**——分离它们需要真机重跑（代价约 75 分钟且任务书禁止）。我只给出各自的可测分量，排序属判断。
4. **"一次成功的 MCP **编辑器侧**写入是否会被 `no_progress` 窗口漏掉"**（延迟落盘风险）：本轮**没有任何**工程写入成功，所以这个假设**既没被证实也没被证伪**。就本轮而言它不影响结论（`A_1` 在电池之后取，也等于 `A_0`；`run_loop.rs:1016` 的 pre-QA 漂移断言也没报警），但**"编辑器异步落盘"这条风险本身仍是未测项**，应由 §5(a) 的测试在真机侧补一条（写入后立刻 `hash_tree` 与下一帧再 `hash_tree` 对比）。
5. **哪条命令触发了 `harness_source_read`**：warning 确实出现，探测器是 `run_loop.rs:214-233` + `hygiene.rs:273-313`（匹配 `src/**`/`.spec/**`/`tests/**`/`.git/**`、目录枚举、或命中 harness 仓根）；Developer 的命令里有多条符合（`messages[148]`、`[153]`、`[161]`、`[237]`…），我**没有**逐条定位是哪一条先触发。
6. **`exit code 255`（4 次）与 `5`（2 次）的具体来源**：我只数了频次，没有逐条追根因。
7. **planner/tester 是否也被同一 shell 错配吃掉预算**：可见的只有字符串计数（planner `$HOH_HOH_BIN` 2 次 + `%HOH_HOH_BIN%` 1 次、tester 4 次、`submit` 字样 planner 4 / tester 16）与"两者仍产出了合法工件"（`artifact_valid=true`，因为 `src/runtime/schema.rs:121` 的闸门**从磁盘**读工件，不依赖 `submit`）。**未**做同粒度的分步时间线。

---

## 8. 诚实披露

1. **只读纪律**：本批**只**读代码/文档/证据、离线跑 Python 分析、只读 git 查询、mtime/摘要普查。**未**修改任何源码、测试、配置、`runs/**`、`.workspace/mario/**`、`PRD-mario.md`、`DECISIONS.md`；**未**启动 Godot、**未**碰端口、**未**联网、**未**调模型端点、**未**重跑真机、**未** push、**未** commit（本报告是本次唯一新增文件，按任务书由调度者提交）。
2. **我没有"顺手修"任何东西**，包括两处已确认的契约缺陷（提示词 shell 语法、测试级假绿）。它们留给后续实现批。
3. **我没有把推断写成实测**：§7 已逐条分栏；凡属推断处文中都标了"推断"。
4. **我的重实现 vs 运行时的实现**：`hash_tree` 是我按 `policy.rs:68-97` 在 Python 里**重写**的，不是调用 Rust 函数（本批不编译、不跑 cargo）。它逐字复现了 `fc78d299…`，这比"两套实现互相印证"强，但**不等于**我执行了生产代码路径。
5. **一个我差点错的地方**：我第一次读 `src/adapter/godot.rs` 时以为 DR-54 的 `scene_path` / 顶层 `name` 两处缺陷还活着，直到核到 `godot.rs:1253-1257` 与 `:1596-1606` 的注释才确认它们**在 HEAD 上已被 DR-58 修好**。因此我在 §3.4 明确写了"约束点 3 针对的是 smoke-t7 当时那个构建（`9ff9cd2`），不是现在的 HEAD"。若不写明，很容易被读成"现在还有两个 bug 挡着 E1"。
6. **一个我主动纠正的表述**：任务书与 D242 说"外层仓不跟踪引擎树"。实测是**外层仓在 `godot-mcp/` 下跟踪了 6484 个文件，但 `godot-mcp/godot/` 下是 0 个**，并被 `.gitignore:33` 忽略。结论不变（引擎树只能用嵌套仓证），但表述被我用数字收窄了。
7. **共享 checkout 的干扰**：我工作期间 HEAD 从（我记录的）`5c83a5f` 起继续有并发提交（D257；`dr60-evidence/**` 62 文件）。所以我不是在静止的仓库上做取证；凡涉及"仓库状态"的断言都写了时间点或用了摘要（§6.5 已说明这一点如何影响"我没动手"的证明力）。
8. **成本与边界**：真机重跑约 75 分钟且被任务书禁止，所以本报告的一切都建立在**既有冻结证据 + 离线对照实验**上。若要把主因排序从"推断"升为"实测"，唯一办法是设计一个**便宜的离线变体轮**（FakeModel 走一遍 Developer 的前 50 步，或只跑一次修复后的契约测试），而不是再烧一轮真机。
9. **不声称 E1/E3 已 met**：E1 仍 `not_met`，E3 仍 `not_met`，本报告没有改变任何判据的状态。
