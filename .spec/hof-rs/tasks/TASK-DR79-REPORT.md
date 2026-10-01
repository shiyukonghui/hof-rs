# TASK-DR79-REPORT — **不重跑**：以追加式勘误更正 T13 报告的三处机制论断与计数，并修四项管线卫生缺陷

- 任务书：`.spec/hof-rs/tasks/TASK-DR79.md`（本批唯一任务来源）
- 规格即验收报告：`.spec/hof-rs/tasks/TASK-SMOKE-T13-ACCEPTANCE.md`（`verdict=fail`，`T13A-1..9`；我逐条按其 `reproduction` 自行复现）
- 报告人：实现子代理（无上游对话上下文）；落点：`F:\moonbit-hof-rs`
- HEAD（开工 = 收工）= `4c8e76a88f3ec0612d9b50300d6521dab8402fa7`；`origin/master` = `8ddbad3f4db43c28be158c17ad0678fe4d77857c`；**未 push**（闸门已武装，推送会被拒是设计）
- **本批边界（两条铁律均守住）**：**不重跑真机轮、不起引擎、不联网**；`runs/**` **零写入**（含 `runs/smoke-t13/**` 与其分析产物）
- 临时材料全在**仓外** `C:\Users\wyl\AppData\Local\Temp\dr79\**`；仓内无新增临时物（`git status` 只有 8 个被改文件 + 2 个既有未跟踪 `.spec` 件 + 3 个 **本批之前就有**的 `.tmp_*.json`）
- 未使用 `rm -rf`；未从未展开变量构造路径；未用 PowerShell 的 `Get-Content -Raw`+`Set-Content`；未整文件重写行尾（见 §5）

---

## 0. 结论摘要

| 项 | 判定 | 一句话依据 |
|---|---|---|
| 勘误（T13A-1/2/3/4/5/6/7/8/9） | **全部登记，追加式** | 9 条缺陷我逐条从 `runs/smoke-t13/**` 原始件复现；更正写入 `TASK-SMOKE-T13-REPORT.md` 的**新增节**「附：DR-79 勘误」，**原文一字未动、机器可读块未曾改动**（318 增 / 0 删；前 107,703 字节与 HEAD **逐字节相同**，其后新增 26,376 B） |
| T13A-4 的一个子项 | **未复现（如实登记）** | "记录类型表漏 `screenshot:2`"在本报告正文**不存在**：§2.4 第 296 行逐字含 5 类且和为 31，与 `round_facts.txt:161` 一致；机器块 `count_scopes` 根本没有 record-type 条目。故**未更正**该子项 |
| ① 越界写入 | **已修（先红→绿）** | 新增 `hygiene::is_root_temporary` / `clean_round_temporaries` / `OutOfTreeWatch::observed`；轮末清理**轮内自己观察到的**根级临时文件并在 `warnings.log` 留痕；接线与规则各有测试，反向保住"非临时越界写入一律保留" |
| ② usage 双计 | **已修（先红→绿）** | `usage_from_attempts` 过滤排除 `.redacted.`；回归钉：有旁路副本时 planner ratio 必为 **1.0**，同时反向钉住"真 attempt2 仍合并"（ratio 2.0） |
| ③ `artifact_valid` 恒真 | **已修（先红→绿）** | 修复块 `run_loop.rs:1378` 由 `workspace.is_dir()` 改为 `orchestrator.adapter.developer_artifact_valid(&workspace)`；**双向**测试钉（修复后仍坏 → false；修复后可用 → true） |
| ④ 命令行走漏 | **已修（先红→绿）** | `DSH_TERM_CMD` 入 `HARNESS_ENV_VARS`，新增 `COMMAND_LINE_VARS` + 专用终止规则（整条命令行是一个值）；纯文本与真实 JSON 两种形状各一条测试 |
| 门 | **`cargo test --offline` exit 0** | 基线 **546 / 0 / 7 ignored**（59 suites / `--list` 553）→ 终值 **554 / 0 / 7 ignored**（561）；**REMOVED 测试名 = 0**；`cargo fmt --check` exit 0 |
| 植入 | **4 处，各自红，逐字节回退** | P1/P2/P3/P4 各自使"对应"测试红（exit 101 且输出点名该测试），回退后与植入前 sha256 **相同** |
| 禁区 | **未动** | `runs/**` 与 `.workspace/**` 在批内零写入（mtime 时间窗为空）；`PRD-mario.md` / `DECISIONS.md` / `godot-mcp/**` / `Cargo.{toml,lock}` 无改动；未 push |

---

## 1. 勘误清单（逐条：被更正的原句 → 正确读数 → 证据与复现 → 原文是否保留）

> 完整正文（含逐字原句、每条复现命令、`superseded` 标注）在 `TASK-SMOKE-T13-REPORT.md` 新增节
> 「**附：DR-79 勘误（追加式，2026-10-02）**」§E-1..E-9。本表是它的索引与判定。

| 缺陷 | 原句落点 | 原文读数（**保留**，标 `superseded`/`incorrect`） | 正确读数 | 证据 / 复现 | 原文保留 |
|---|---|---|---|---|---|
| **T13A-1** major | §0.1:35、§3.3(d):449–452、§7:610、§10:691、§5.3:546 | 轮内**最初**起游戏失败（`:55361`、04:17:44），"到电池 pass 2 之前任何角色都没有路由"；§3.3(d) 拒绝时间 `04:31:28` | **最初起游戏成功**，发布 `http://127.0.0.1:53068/mcp`（作者 04:19:22 亲自探过两次；Developer 04:44:02 读到 `configured_port=53068`）；DR-70 那条 **~04:41** 追加，属**修复期重启**（`run_loop.rs:1348`，应答 `:55361`）；拒绝时间 **04:51:28**；"逐轮翻转"收窄为"同一轮两次起游戏命运不同"，"承诺与行为不一致"收窄到**修复窗口（~04:41→04:54:51）** | `evidence/round/game_endpoint_{tools_list,scene_tree}_round_author.json`（首行逐字 `POST http://127.0.0.1:53068/mcp`，回包 25908/816 B）；`developer.attempt2.json` msg 77（04:44:02）、msg 135（04:50:46 的 `dir` 显示 `warnings.log 1,110 B @04:41`）、msg 137/138/139（`extra.timestamp=1790887888.17` → 04:51:28）；`epochs.txt` 锚点 1790888078=04:54:38；`run_loop.rs:832`（首次）/`:1348`（修复期） | 是 |
| **T13A-2** major | §7:608、§10:695、机器块 `mechanisms.truncation_64kib` | "64 KiB 上限 **未被触发**：四条未脱敏轨迹里 `hoh_output_truncated` **0** 次" | **触发过一次**：`tester.attempt1.json` **msg 98**（04:56:37）`hoh_output_truncated=true`、`limit=65536`、`original=81139`，运行时标记 `[hoh: 65536 of 81139 bytes were carried; the remaining 15603 bytes were dropped …]`；**登记为该路径的首次真机证据（新获得的正面事实）** | 逐条轨迹解析 `extra` 字段：`python -c "import json,io,glob;print([(p,i) for p in sorted(glob.glob('runs/smoke-t13/iter-1/traj/*.json')) if not p.endswith('.redacted.json') for i,m in enumerate(json.load(io.open(p,encoding='utf-8'))['messages']) if (m.get('extra') or {}).get('hoh_output_truncated')])"` → 恰一行 tester msg 98 | 是 |
| **T13A-3** medium | §5.1:498、§10:698 | attempt2 的 `artifact_valid` 复用了 attempt1 的值（`1137` 计算 / `1185` 复用） | 真实落点是**启动门修复块** `run_loop.rs:1378` 的 `artifact_valid: workspace.is_dir()`（**恒真**）；被引用的 `1137/1185` 属于**未触发**的 wrap-up 块（门槛 `developer_limits && !developer_artifact_valid`，本轮 `wrap_up_retry_used=false`）。"标志太松"结论仍成立，**理由不同且更强**：那条尝试压根没有判定 | `grep -n artifact_valid src/runtime/run_loop.rs`；`sed -n '1150,1188p'` vs `sed -n '1340,1398p'`；`result.json` 的 `repair_retry_used=true` / `wrap_up_retry_used=false` | 是 |
| **T13A-4** minor | §0:23、§2.4:295、机器块 `count_scopes` | verified-only **10** / gap-only **13** | verified-only **21** / gap-only **10**（总数 **31** 不变） | `evidence.json` 复算：`sum(len(r['execution_records']) for r in d['verified_records'])` = 21；`gap_records` = 10 | 是 |
| **T13A-6** minor | §11.4:707、§12:724–725、证据索引:1485、机器块 | "**106** 文件 = round 23 / analysis 28 / gatecheck 5 / scripts 50"；`scripts/**` 37 个；`analysis/**` 14 个；`cite_check.txt` 18189 B；`round_dir_files` 264；`before_evidence` 147 | **110** = round **23** / analysis **31** / gatecheck **5** / scripts **51**；**51**；**31**；**18401** B；**268**；**158**（=268−110；原文 147+110=257≠264 自身也不自洽） | 复算：`find runs/smoke-t13 -type f` 计数 = 268；`.../evidence` = 110；各子目录 23/31/5/51；cite_check 字节数 18401。**机器块 `evidence_files_copied_in_after_close` 本来就是 110/23/31/5/51** ⇒ 正文与机器块矛盾，**错的是正文** | 是 |
| **T13A-7** info | §7:606 | `warnings.log` **8 行** | **7** 个以换行结尾的行（1,849 B；按 LF 切得 8 段是尾换行） | `python -c "import io;b=io.open('runs/smoke-t13/warnings.log','rb').read();print(len(b), b.count(b'\n'), len(b.split(b'\n')))"` → `1849 7 8` | 是 |
| **T13A-8** info | §5.3:544、§10:685 | 角色拒绝时"路由文件不存在"是**强推断 ≈0.85** | **直接观测**：`developer.attempt2.json` **msg 134**（04:50:45）的命令内含 `if exist "%HOH_GAME_ROUTE%" (…) else (echo no route file)`，**msg 135**（04:50:46）输出尾部逐字 `===ROUTE=== \nno route file`。**保留边界**：这是拒绝前 **42 s** 的读数，不是同一瞬 | `python -c "import json,io;d=json.load(io.open('runs/smoke-t13/iter-1/traj/developer.attempt2.json',encoding='utf-8'));print(repr(d['messages'][135]['content'][-160:]))"` | 是 |
| **T13A-5** minor | §10:680、§11:710 | "没有密钥泄漏"（更强的读法：没有**环境值**泄漏） | **密钥值 0 泄漏成立**（51 B 值扫 `runs/smoke-t13/**` 268 文件 = **0 命中**）；但 **`DSH_TERM_CMD`** 这条**非密钥**环境值泄漏进 4 个文件（`planner.attempt1{,.redacted}.json`、`developer.attempt1{,.redacted}.json`，各 2 处），含仓外暂存路径与**密钥文件名** `config/model.secret.env` | `grep -rl DSH_TERM_CMD runs/smoke-t13/`；`grep -rl model.secret.env runs/smoke-t13/`；密钥值扫描（只打印长度与命中数） | 是 |
| **T13A-9** minor | §7:617、§10:679、§10 F-T13-5:696 | `out_of_tree_writes` 记了 3 个仓根 `.tmp_*.json`，"检出但未阻止/未清理" | 三文件**实测仍在**仓根、未跟踪（108/68/46 B，mtime 04:52:28–29）；**本批 ①** 让**未来轮**做**有界清理 + `warnings.log` 留痕**，同时保留 `out_of_tree_writes` 里的事实；**本批不删这三个**（它们是 T13 的取证对象、且非本批轮内产物，清理器按定义只碰轮内新增/变更） | `git status --porcelain`（筛 `.tmp_`）；`stat`；`result.json.out_of_tree_writes` | 是 |

**另**：任务书要求读 `DECISIONS.md` **D289 / D293**。**D289 存在**（追加式更正纪律的依据，本批遵守）；**D293 不存在** —— 冻结的 `DECISIONS.md` 共 11,117 行，**最后一条是 D292**，全文无 `D293`；`DECISIONS.md` 本批**未改**。

**勘误的追加性证据**（可复算）：

```
git diff --numstat -- .spec/hof-rs/tasks/TASK-SMOKE-T13-REPORT.md   ->  318  0
python: HEAD 版字节 = 107,703；工作区前 107,703 字节与 HEAD 逐字节相同（prefix_identical=True）；其后新增 **26,376 B**
```

⇒ 机器可读块（第 741–1408 行）与全部证据字符串**未动**；勘误节 §E-9 逐字段列出被取代的机器块条目。

---

## 2. 四项管线卫生修复（**各自 TDD：先红 → 绿**）

### 2.1 ② usage 双计（`src/runtime/usage.rs`）

- **先红**：新增集成测试 `tests/usage_extraction.rs::a_redacted_sidecar_is_not_a_second_attempt`；改前运行
  `cargo test --offline --test usage_extraction` → `FAILED`，断言 `left: 2  right: 1`
  （"the redacted sidecar must not be counted as a second attempt"）。
- **改动**：`usage_from_attempts` 的名字过滤加 `&& !name.contains(".redacted.")`（DR-79 ②）。
- **绿**：同测试 5 passed / 0 failed。
- **回归钉（双向）**：sidecar 存在时 `merged.calls == single.calls`、`ratio == 1.0`；再加一个真 `planner.attempt2.json`
  后 `merged.calls == single.calls * 2`（防止"把文件全忽略"也能通过）。
- **冻结件非空洞性**：用**修复后的**过滤器对 `runs/smoke-t13/iter-1/traj/` 选文件 → planner 只选 `planner.attempt1.json`
  （改前会选 2 个）；developer 选 `attempt1`+`attempt2`；tester 选 `attempt1`。
  冻结读数佐证：`planner.attempt1.json` 27 calls / 272,378 vs `usage.json` summary planner **54 / 544,756**。

### 2.2 ③ `artifact_valid` 恒真（`src/runtime/run_loop.rs`）

- **先红**：新增 `tests/launchable_gate.rs::the_repair_attempt_artifact_validity_is_measured_not_assumed`；改前运行
  → `FAILED`，输出显示 `developer attempt1 artifact_valid=false` 而 `attempt2 artifact_valid=true`
  （`left: Some(true)  right: Some(false)`）——真实适配器已判定"坏"，而修复块仍记 `true`。
- **改动**：启动门修复块在 push `AttemptOutcome` 前重新问适配器
  `let repair_artifact_valid = orchestrator.adapter.developer_artifact_valid(&workspace);`（`:1378` 附近）。
- **绿**：同测试 passed。
- **回归钉（双向）**：修复后场景仍坏（`SCENE_WITHOUT_ROOT`）→ `false`；修复后可用（`SCENE_WITH_ENTRY_SCRIPT` + 非空
  `scripts/player.gd`）→ `true`。防"硬编码 false"也能通过。

### 2.3 ④ 命令行走漏（`src/runtime/secrets.rs`）

- **先红**：新增两条单元测试；改前运行 `cargo test --offline --lib secrets` → 两条均 `FAILED`
  （`RedactionReport{ spans: [], redacted == original }`，即整条 `DSH_TERM_CMD=` 原样保留）。
- **改动**：
  1. `"DSH_TERM_CMD"` 加入 `HARNESS_ENV_VARS`；
  2. 新增 `COMMAND_LINE_VARS = &["DSH_TERM_CMD"]` 与 `command_line_value_ends_at`：命令行只在**逻辑行末**结束
     （物理 `\n`/`\r`、JSON 的 `\n`/`\r` 转义、JSON 字符串的未转义收尾引号），而 `;` / `&&` / `>>` / `\"` / `\\`
     **都不是**终止符 —— 因为实测 `config/model.secret.env` 恰在第一个 `;` 与第一个 `\"` **之后**；
  3. `assignment_value_end` 增加 `command_line` 参数并在最前面处理。
- **绿**：secrets 单元测试 19 passed / 0 failed。
- **回归钉（真实形状）**：用 `serde_json::to_string` 合成**真实编码**（`\"`、双反斜杠、`\n` 转义）的
  `{"content":"<output>\nDSH_TERM_CMD=…config/model.secret.env…\n</output>"}` ⇒ 脱敏后仍 `json.loads` 通过、
  `span` 外 0 字节变化、`</output>` 存活、`model.secret.env` 与 `run_cmd.py` 均不存活。

### 2.4 ① 越界写入（`src/runtime/hygiene.rs` + `src/runtime/run_loop.rs`）

- **先红**：新增 3 条 `hygiene` 单元测试 + 1 条 `tests/role_paths.rs` 集成测试；
  - 单元测试改前**编译失败**（`is_root_temporary` / `clean_round_temporaries` / `OutOfTreeWatch::observed` 不存在）——
    这是 TDD 里较弱的"红"，如实登记；
  - 集成测试改前是**真断言红**：`the round's own root temporary must be cleaned at close: …\.tmp_probe.json`。这是本次行为改变的**真先红**。
- **改动**：
  - `is_root_temporary(relative)`：**单一路径分量**且为 `.tmp_*` / `tmp_*` / `*.tmp` / `*.bak`（项目文件、带分隔符、
    `.`/`..`、`_probe.gd` 全部不合格）；
  - `clean_round_temporaries(root, observed)`：只删 `is_file()` 的直接子路径，返回被删列表；join 后再校验 `parent()==root`；
  - `OutOfTreeWatch` 记录**轮内观察并集** `observed()`（per-iteration 返回值被迭代记录消费，无法回答轮末问题）；
  - `run_loop.rs` 轮末调用，并把 `out_of_tree_cleanup: removed N round-temporary file(s) from <root>: …` 写进
    `warnings.log`（`sweep_warnings` 通道），`out_of_tree_writes` 的记录**保留**。
- **绿**：hygiene 19 passed；`role_paths` 12 passed。
- **回归钉（反向，保住 DR-25 语义）**：既有的 `a_role_writing_outside_the_project_is_reported` 仍要求
  `stray_dir/probe.txt` **留在盘上**（非临时、带子目录 ⇒ 不清理）；新单元测试同向断言 `keep.txt` / `scenes/main.tscn` /
  `stray_dir/.tmp_nested.json` 一律不动。
- **工具纪律**：只删**具名文件**（`std::fs::remove_file`），无通配符、无目录删除、**无 `rm -rf`**、路径来自 `root.join(单分量)`。

### 2.5 受控植入（**4 处，各自红，逐字节回退**）

| 植入 | 落点（改法） | 目标测试 | 读数 | 回退 |
|---|---|---|---|---|
| **P1** usage sidecar 过滤 | 删去 `&& !name.contains(".redacted.")` | `a_redacted_sidecar_is_not_a_second_attempt` | exit 101，输出点名该测试，`FAILED` ⇒ 红 | sha256 前后相同（`usage.rs` = `0014353268346efb…9499`） |
| **P2** 修复尝试的 `artifact_valid` | `artifact_valid: repair_artifact_valid` → `workspace.is_dir()` | `the_repair_attempt_artifact_validity_is_measured_not_assumed` | exit 101，点名，`FAILED` ⇒ 红 | sha256 前后相同（`run_loop.rs` = `97ba688529ccfeb2…0760`） |
| **P3** 命令行走漏 | 删去 `HARNESS_ENV_VARS` 里的 `"DSH_TERM_CMD",` | `runtime::secrets::tests::a_harness_command_line_does_not_leak_the_secret_file_it_names` | exit 101，点名，`FAILED` ⇒ 红 | sha256 前后相同（`secrets.rs` = `6e9adf2f2162ba64…aed7`） |
| **P4** 轮末清理**接线** | 把 `clean_round_temporaries(...)` 调用替换为 `let cleaned: Vec<String> = Vec::new();` | `a_round_removes_its_own_root_temporary_and_records_it` | exit 101，点名，`FAILED` ⇒ 红 | sha256 前后相同（`run_loop.rs` 同上） |

- 回退方式是**仓外字节备份 + `shutil.copyfile`**（不是编辑器重写），每处都在同一脚本里比较植入前后 sha256。
- 植入日志与原始输出留在仓外 `C:\Users\wyl\AppData\Local\Temp\dr79\plants\{P1..P4}*.txt`（`P3` 为 `P3_harness_command_line_var.txt`）。
- **区分"哪些红是真先红"**：2.1（断言红）、2.2（断言红）、2.3（断言红）、2.4 的**集成**测试（断言红）是**真先红**；
  2.4 的 3 条单元测试首红是**编译失败**（函数尚不存在），属 TDD 的弱红，**不计入**"真先红"。

---

## 3. 门读数与禁区自查

### 3.1 门

| 项 | 开工基线 | 收工终值 | 判定 |
|---|---|---|---|
| `cargo test --offline` | **exit 0** | **exit 0** | 通过 |
| passed / failed | **546 / 0** | **554 / 0** | 净增 8（恰为本批新增的 8 条测试） |
| ignored | **7** | **7** | **未增长** |
| suites | 59 | 59 | — |
| `--list` 测试名 | **553** | **561** | **REMOVED = 0**，ADDED = 8（名称见 §3.3） |
| `cargo fmt --check` | — | **exit 0** | 通过 |
| 强制重编 | — | **逐文件 `touch` `git ls-files '*.rs'` 的 96 个文件**（Python 迭代，**无 shell 通配符**）后重跑 | 通过 |

- **基线算术**：`546 passed + 7 ignored = 553` = `--list` 的 553 条；改后 `554 + 7 = 561`。逐条核对 `--list` 名称得
  **REMOVED = 0 / ADDED = 8**。
- **先清陈旧指纹**：用 Python `glob` 枚举 `target/debug/.fingerprint/hof-rs-*` 并**逐个** `shutil.rmtree`
  （非 `rm -rf`、无 shell 通配符）后，才跑基线；**披露**：删除日志只保留了尾部（最后 4 个目录），**目录总数未留存**。
- 8 条新增测试名：`a_redacted_sidecar_is_not_a_second_attempt`、
  `the_repair_attempt_artifact_validity_is_measured_not_assumed`、
  `runtime::secrets::tests::a_harness_command_line_does_not_leak_the_secret_file_it_names`、
  `runtime::secrets::tests::the_real_json_command_line_shape_redacts_the_whole_value`、
  `runtime::hygiene::tests::only_root_level_temporary_shapes_are_round_litter`、
  `runtime::hygiene::tests::the_cleanup_removes_only_the_root_temporaries_the_watch_observed`、
  `runtime::hygiene::tests::the_watch_remembers_what_it_observed_across_the_round`、
  `a_round_removes_its_own_root_temporary_and_records_it`。

### 3.2 禁区自查

| 检查 | 命令 | 结果 |
|---|---|---|
| `runs/**` 零写入 | `git status --porcelain -- runs/`；`find runs -type f -newermt "2026-10-02 05:52:00"` | 均**空** ⇒ 无改动、无新文件（含 `--ignored`） |
| `.workspace/**` 未动 | `find .workspace -type f -newermt "2026-10-02 05:52:00"` | **空** |
| 冻结规范 / 引擎 / 依赖 | `git status --porcelain -- PRD-mario.md DECISIONS.md godot-mcp Cargo.toml Cargo.lock .spec/hof-rs/REQUIREMENTS.md` | **空** |
| 未 push | `git rev-parse origin/master` | 仍 `8ddbad3f4db43c28be158c17ad0678fe4d77857c`（与开工相同）；本批**未执行 push** |
| 仓内无新增临时物 | `git status --porcelain` | 仅 8 个被改文件 + 2 个既有未跟踪 `.spec` 件 + 3 个 mtime 04:52 的既有 `.tmp_*.json` |
| 无文件被删 | `git status --porcelain` | **无 `D`、无 `R`**；未动游戏文件、未手工写游戏 |
| 行尾未整文件重写 | 逐文件统计 CRLF/LF | 96 个跟踪 `.rs` 里 88 纯 LF、**8 纯 CRLF**（`cli_impl.rs`、`errors.rs`、`main.rs`、`prompts/mod.rs`、`runtime/secrets.rs`、`tools/bridge.rs`、`tests/interaction_contract.rs`、`tests/round_artifacts.rs`）；**无 MIXED**，被我改过的 `secrets.rs` 仍是纯 CRLF ⇒ 未破坏既有行尾 |
| 本批改动面 | `git status --porcelain` | 8 个文件：`src/runtime/{hygiene,run_loop,secrets,usage}.rs`、`tests/{launchable_gate,role_paths,usage_extraction}.rs`、`.spec/hof-rs/tasks/TASK-SMOKE-T13-REPORT.md`（纯追加） |
| 提交 | `git status` / `git log` | 本批变更**未提交**（任务书未要求提交，`DECISIONS.md` 亦禁改；提交信息应由上游决策者按决策日志下发）。`HEAD` 仍是 `4c8e76a`，本地对 `origin/master`(=`8ddbad3f`) 的既有领先**原样保留**，本批**未创建任何提交**、未 stage |

---

## 4. 遗留风险与未验证项（严格区分实测 / 推断 / 未验证）

**实测（本批真跑过）**

1. 四项卫生修复各有先红与绿，且各有双向回归钉；4 处植入各自使对应测试红并逐字节回退。
2. 勘误 9 条逐条从原始件复现；T13A-4 的"漏 `screenshot:2`"子项**未复现**（§1 表与勘误 §E-7）。
3. 门：先清指纹 → 基线 546/0/7 → 逐文件 touch 96 个 `.rs` 强制重编 → 554/0/7、exit 0、`fmt --check` exit 0、REMOVED=0。
4. `runs/**` 与 `.workspace/**` 批内零写入；冻结件/引擎/Cargo 无改动；未 push。

**推断（不得当作已测）**

1. `warnings.log` 的 DR-70 属**修复期重启**（`run_loop.rs:1348`）这条归因，依据是：`warnings.log` 在 04:41 只有 1,110 B
   （msg 135 的 `dir` 输出）、轮次 04:17:42 开跑、电池 pass 1 在 04:41:30/37 失败、代码顺序（首次 832 → 修复 1348）。
   **我没有对游戏进程做仪器化**（不重跑、不起引擎），也没有逐次起游戏的时间戳日志 ⇒ **强推断，非直接观测**。
2. 04:19:22 这个时刻来自被验收报告的 `epochs.txt` 锚点换算；我核到的是**两个探针文件确实 POST 到 `:53068` 且有合法回包**，
   以及 Developer 04:44:02 读到 `configured_port=53068`。04:19:22 本身我**未独立重算**（`epochs.txt` 里没有该行）。

**未验证 / 未知**

1. 我**没有重算** `cite_check.txt` 的 sha256（只核了字节数 18401）；证据索引其余 58 行的字节数与 sha 前缀**未逐条核对**。
2. 我**没有**把 `DSH_TERM_CMD` 从角色 shell 的环境里剥离（本批只做**脱敏**，任务书 ④ 的范围）；角色仍会继承该变量，
   只是它出现在 **`NAME=<value>`** 形状时会被脱敏。若它以**裸值**（无 `DSH_TERM_CMD=` 前缀）出现在别处，本批的规则不覆盖（`HOH_MODEL_API_KEY` 值走的是 DR-19 值规则，本批未扩展）。
3. `clean_round_temporaries` 只处理**直接位于 `out_of_tree_root`** 的单分量路径；子目录里的同类临时文件**仍然只报不治**（有意的边界）。
4. `artifact_valid` 修复让**修复尝试**重新判定，但 `AttemptOutcome.artifact_valid` 仍不区分"模型停手的工程"与"可用工程"
   （DR-76 老风险），本批未触碰该语义。
5. 我**没有**验证 `usage` 修复对 `runs/smoke-t12` 的轮级 token 数会产生什么（旧值 90/901,668 → 新规则下的读数未重算；
   冻结件不可改）。
6. 3 个仓根 `.tmp_*.json` **仍在**（本批有意不删）；清理器对它们无效（它们早于任何未来轮的基线）。

---

## 5. 诚实披露

1. **2.4 的单元测试首红是编译失败**，不是断言红；只有 `role_paths` 那条集成测试是真断言红。我不把前者算作"真先红"。
2. **2.2 的新测试第一次改后仍有红**：我的 (b) 分支一开始用 `SCENE_WITH_ROOT`，但 `developer_artifact_valid` 还要求
   **引用一个非空脚本文件**，`SCENE_WITH_ROOT` 不满足 ⇒ 第一次"绿"运行时是 **test 夹具写错**，我改用带
   `ext_resource` + 非空 `scripts/player.gd` 的场景后绿。**这不是代码缺陷，是测试夹具缺陷，如实登记。**
3. **P3 `anchors` 第一次未命中**：`secrets.rs` 是纯 CRLF 文件，我的植入锚点用了 LF ⇒ 夹具不匹配、植入未发生；
   我改为按文件实际 EOL 选锚点后重跑，红与回退均成立（`P3.bak` 与 `P3_harness_command_line_var.bak` 两份相同备份留着）。
4. **清指纹日志的总数未留存**（只 tail 到最后 4 个目录）；过程本身用 Python 枚举逐个删除，无 shell 通配符、无 `rm -rf`。
5. **勘误的 E-2/E-5 复现命令我一度写错**（heredoc/多行 python 在本 harness 下换行会被折叠），已改成**单行、且我实测过输出**的命令；
   勘误文件里现在给出的是**已验证**的那版。
6. **机器可读块**（本报告 §附录）由 `json.dumps(..., ensure_ascii=False, indent=2)` 序列化后落盘，并由脚本**栅栏感知地回读**
   `json.loads` 并与序列化字节比对（见 §附录注），不是手写 JSON。
7. **未 push**：`origin/master` 与开工相同；**未尝试**推送（闸门已武装、T13 前置无通过验收，推送会被拒是设计）。
8. **本报告的所有数字来自我自己跑的脚本或直接读取的原始件**；被验收报告只用于**定位**。全程离线，未起引擎、未跑轮、
   **未写 `runs/**`**；临时材料全在仓外，**未使用 `rm -rf`**、未从未展开变量构造路径、未用 PowerShell 的 raw 读写对、未整文件重写行尾。

---

## 附：机器可读结论

（本块由 `json.dumps(..., ensure_ascii=False, indent=2)` 序列化后落盘；落盘后由脚本按**行锚定的栅栏**回读、`json.loads`，
并与序列化字节**逐字节**比对。完整脚本在仓外 `C:\Users\wyl\AppData\Local\Temp\dr79\assemble.py` 与 `\check_block.py`。）

```json
{
  "task": "TASK-DR79",
  "kind": "additive erratum of TASK-SMOKE-T13-REPORT.md plus four pipeline hygiene fixes (no round re-run, offline, runs/** read-only)",
  "head": "4c8e76a88f3ec0612d9b50300d6521dab8402fa7",
  "origin_master_at_close": "8ddbad3f4db43c28be158c17ad0678fe4d77857c",
  "pushed": false,
  "erratum": {
    "file": ".spec/hof-rs/tasks/TASK-SMOKE-T13-REPORT.md",
    "section": "附：DR-79 勘误（追加式，2026-10-02）",
    "mode": "append-only",
    "git_numstat": {
      "insertions": 318,
      "deletions": 0
    },
    "prefix_bytes_identical_to_head": true,
    "head_file_bytes": 107703,
    "appended_bytes": 26376,
    "machine_block_untouched": true,
    "evidence_strings_untouched": true
  },
  "corrections": [
    {
      "id": "T13A-1",
      "severity": "major",
      "original_marked": "incorrect/superseded",
      "corrected": "the round's initial start_round_game succeeded and published http://127.0.0.1:53068/mcp (author probed it; developer read configured_port=53068 at 04:44:02); the DR-70 warning at :55361 was appended ~04:41 and belongs to the repair-time restart (run_loop.rs:1348); the refusal time in 3.3(d) is 04:51:28, not 04:31:28; the flipped-invariant and whole-window risk statements are narrowed to the repair window"
    },
    {
      "id": "T13A-2",
      "severity": "major",
      "original_marked": "incorrect",
      "corrected": "the 64 KiB truncation fired exactly once: tester.attempt1.json message 98 at 04:56:37, limit 65536, original 81139; recorded as the first real-machine exercise of that path"
    },
    {
      "id": "T13A-3",
      "severity": "medium",
      "original_marked": "incorrect",
      "corrected": "the loose artifact_valid comes from the DR-70 launch-gate repair block at run_loop.rs:1378 (workspace.is_dir(), always true), not from reuse at 1137/1185 (that is the wrap-up block, which did not fire)"
    },
    {
      "id": "T13A-4",
      "severity": "minor",
      "original_marked": "incorrect",
      "corrected": "execution_records verified-only 21 and gap-only 10 (total 31 unchanged)"
    },
    {
      "id": "T13A-5",
      "severity": "minor",
      "original_marked": "incomplete",
      "corrected": "the 51-byte key value did not leak (0 hits in 268 files), but the non-secret DSH_TERM_CMD command line did, in planner.attempt1{,.redacted}.json and developer.attempt1{,.redacted}.json, naming config/model.secret.env"
    },
    {
      "id": "T13A-6",
      "severity": "minor",
      "original_marked": "incorrect",
      "corrected": "evidence files 110 (round 23 / analysis 31 / gatecheck 5 / scripts 51); scripts 51; analysis 31; cite_check.txt 18401 B; round_dir_files 268; before_evidence 158"
    },
    {
      "id": "T13A-7",
      "severity": "info",
      "original_marked": "incorrect",
      "corrected": "warnings.log has 7 newline-terminated lines (splitting on LF gives 8 because of the trailing newline)"
    },
    {
      "id": "T13A-8",
      "severity": "info",
      "original_marked": "over-conservative",
      "corrected": "the absent route file was directly observed by the developer itself (message 134/135, 04:50:46 printed 'no route file'), 42 s before the 04:51:28 refusal, so it is an observation rather than a 0.85 inference"
    },
    {
      "id": "T13A-9",
      "severity": "minor",
      "original_marked": "incomplete",
      "corrected": "the three .tmp_*.json files in the repository root were detected but never prevented or cleaned; DR-79 fix (1) makes future rounds clean the root temporaries they themselves observed and record it in warnings.log"
    }
  ],
  "not_reproduced": [
    "T13A-4's sub-claim that the record-type table omits screenshot:2 does not reproduce: TASK-SMOKE-T13-REPORT.md line 296 literally lists {replay:11, runtime_trace:10, build:5, assert:3, screenshot:2} (5 families, sum 31), identical to runs/smoke-t13/evidence/analysis/round_facts.txt:161, and the machine block's count_scopes has no record-type entry at all. Not corrected; registered as not reproduced."
  ],
  "decisions_note": "DECISIONS.md D289 exists and is the additive-erratum rule; D293 does not exist (the frozen file ends at D292, 11117 lines). DECISIONS.md was not modified.",
  "fixes": [
    {
      "id": "out_of_tree_writes",
      "defect": "detected but neither prevented nor cleaned",
      "site": "src/runtime/hygiene.rs (is_root_temporary, clean_round_temporaries, OutOfTreeWatch::observed) + src/runtime/run_loop.rs (round-close call + warnings.log trace)",
      "test_first_red": "hygiene unit tests compiled-red (functions absent); role_paths integration test assert-red ('.tmp_probe.json' survived the round)",
      "new_tests": 4,
      "plant": "P4",
      "plant_red": true,
      "restored_byte_exact": true,
      "regression_pins": [
        "only single-component known temp shapes are eligible",
        "a nested/file/non-temp path is never touched",
        "stray_dir/probe.txt stays on disk (DR-25 report-only semantics preserved)"
      ]
    },
    {
      "id": "usage_double_count",
      "defect": "the DR-72 redacted sidecar counted as a second attempt",
      "site": "src/runtime/usage.rs::usage_from_attempts",
      "test_first_red": "tests/usage_extraction.rs::a_redacted_sidecar_is_not_a_second_attempt (left 2, right 1)",
      "new_tests": 1,
      "plant": "P1",
      "plant_red": true,
      "restored_byte_exact": true,
      "regression_pins": [
        "planner ratio 1.0 with a sidecar",
        "a genuine second attempt still merges (ratio 2.0)"
      ]
    },
    {
      "id": "artifact_valid_always_true",
      "defect": "the repair attempt recorded workspace.is_dir()",
      "site": "src/runtime/run_loop.rs launch-gate repair block",
      "test_first_red": "tests/launchable_gate.rs::the_repair_attempt_artifact_validity_is_measured_not_assumed (attempt2 true while attempt1 false)",
      "new_tests": 1,
      "plant": "P2",
      "plant_red": true,
      "restored_byte_exact": true,
      "regression_pins": [
        "repair left broken -> false",
        "repair produced a usable scene -> true"
      ]
    },
    {
      "id": "harness_command_line_redaction",
      "defect": "DSH_TERM_CMD reached frozen evidence",
      "site": "src/runtime/secrets.rs (HARNESS_ENV_VARS + COMMAND_LINE_VARS + command_line_value_ends_at)",
      "test_first_red": "two secrets unit tests (spans empty, redacted == original)",
      "new_tests": 2,
      "plant": "P3",
      "plant_red": true,
      "restored_byte_exact": true,
      "regression_pins": [
        "a plain-text command line is one value, bounded by the physical newline",
        "the real JSON encoding stays valid JSON with zero bytes changed outside the span",
        "a dotted path under the same variable ends at the shell logical line, so ; / && / >> / \\\" / \\\\ are not boundaries"
      ]
    }
  ],
  "gate": {
    "baseline": {
      "passed": 546,
      "failed": 0,
      "ignored": 7,
      "suites": 59,
      "listed": 553,
      "exit_code": 0
    },
    "final": {
      "passed": 554,
      "failed": 0,
      "ignored": 7,
      "suites": 59,
      "listed": 561,
      "exit_code": 0
    },
    "test_names_removed": 0,
    "test_names_added": 8,
    "fmt_check_exit_code": 0,
    "rebuild_forced_by": "per-file touch of the 96 files returned by git ls-files '*.rs' (Python iteration, no shell wildcard)",
    "stale_fingerprints_cleared": "python glob over target/debug/.fingerprint/hof-rs-* + shutil.rmtree (not rm -rf, no wildcard); the total count of removed directories was not retained (only the tail of the log)"
  },
  "banned_zones": {
    "runs_new_files_after_batch_start": 0,
    "runs_git_status_entries": 0,
    "workspace_new_files": 0,
    "frozen_spec_diff_entries": 0,
    "engine_diff_entries": 0,
    "cargo_diff_entries": 0,
    "pushed": false,
    "new_temp_artifacts_in_repo": 0,
    "tracked_files_deleted": 0,
    "line_endings": {
      "tracked_rs": 96,
      "pure_lf": 88,
      "pure_crlf": 8,
      "mixed": 0
    }
  },
  "residual_risks": [
    "The attribution of the DR-70 window failure to the repair-time restart (run_loop.rs:1348) is a strong inference from warnings.log's 04:41 size/listing, the code order and the battery pass 1 timings; no per-start instrumentation exists and no round was re-run.",
    "The 04:19:22 probe time comes from the acceptance report's epochs.txt anchors; I verified the :53068 POSTs and the 04:44:02 configured_port line, not that exact second.",
    "Roles still inherit DSH_TERM_CMD; DR-79 only redacts the NAME=value shape, it does not remove the variable from role shells.",
    "clean_round_temporaries is deliberately root-only and single-component: nested temporary files remain report-only.",
    "AttemptOutcome.artifact_valid still does not distinguish 'a usable project' from 'a project the model stopped improving'.",
    "The cite_check.txt sha256 and the other 58 evidence-index rows were not re-verified beyond byte counts.",
    "The usage fix's effect on runs/smoke-t12's round-level token count was not recomputed (frozen artifacts, read-only).",
    "The three pre-existing .tmp_*.json files are still in the repository root; the cleaner ignores them by design (they pre-date any future round's baseline)."
  ],
  "honest_disclosure": [
    "The hygiene unit tests' first red was a compile error (functions did not exist), not an assertion failure; only the role_paths integration test was a true assertion-red.",
    "The artifact_valid test's (b) branch first used SCENE_WITH_ROOT, which does not satisfy developer_artifact_valid (it needs a non-empty referenced script); the first green run exposed a test-fixture defect, fixed by SCENE_WITH_ENTRY_SCRIPT plus a non-empty scripts/player.gd. The code needed no further change.",
    "Plant P3's first anchor missed because src/runtime/secrets.rs is pure CRLF and my anchor used LF; re-run with the file's actual EOL, the plant reddened and restored byte-exactly.",
    "The fingerprint-clearing log retained only its tail, so the total number of removed directories is not recorded.",
    "Two reproduction commands in the erratum were first written as heredocs/multi-line python that this harness's newline folding breaks; they were replaced with single-line commands whose output I verified.",
    "No push was attempted; origin/master is unchanged."
  ]
}
```
