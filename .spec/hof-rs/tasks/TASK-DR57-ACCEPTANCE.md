# TASK-DR57-ACCEPTANCE — DR-57（零请求计数测试 + 报告更正 + DEF-2）独立验收报告

- 验收者：**独立验收子代理**（无上游对话上下文；本报告每一条证据都由我自己复现，实现者报告与 `%TEMP%\dr57-plant\*.txt` 只作**线索**）
- 权威判据：`.spec/hof-rs/tasks/TASK-DR57-ACCEPT.md`；任务书 `.spec/hof-rs/tasks/TASK-DR57.md`；首发现缺陷的验收报告 `.spec/hof-rs/tasks/TASK-DR54-ACCEPTANCE.md`（DEF-1/DEF-2）；规范 `DESIGN-DETAIL.md` §15（DR-55）；决策 `DECISIONS.md` D238/D239/D242/D244
- 被验收批次（起点 `ba32de6`）：`440fc89`、`05efd7f`、`580b86c`、`ae7a45e`、`23304a1`、`c1586e1`、`f4f18cb`、`29fc265`；编排者文档提交 `afb649a`、`77408ed` 夹在期间，**不属于本批产物**（我未把它们当成实现者改动）
- 验收开始 HEAD：`77408edb18efe5b8d960692b1ece7c8319239538`；验收过程中编排者又追加了 `b35b782`、`54e00d1`（纯 `docs(spec)`），验收结束时 HEAD = `54e00d1433adc18cccdd0039532486abfea25896`。**`git diff --name-status ba32de6..HEAD -- src tests` 在头尾两次检查逐字相同**（`M src/adapter/godot.rs`、`A tests/endpoint_request_count.rs`），故 HEAD 移动不影响本次结论
- `origin/master` = `afb649a0afb6a422f8b0d6f3ff8ea1417e382957`（与验收书 §1.7 所述一致）；本地领先 **4** 个提交（`29fc265`/`77408ed`/`b35b782`/`54e00d1`），我**未 push、未 stage、未改写历史**
- 验收日期：2026-09-29（本机时钟与已入库提交）
- 验收者改动（全部受控，逐字节回退）：`src/tools/mod.rs` 上的**两处自设计植入**（§3），日志写在仓外 `%TEMP%\dr57acc\`；唯一仓内写入是本报告文件本身（未跟踪、未 stage）

---

## 1. 结构化结论（机器可读）+ 真实命令与退出码

```json
{
  "verdict": "pass",
  "criteria": [
    {
      "id": "SUITE",
      "pass": true,
      "evidence": "我自跑 `cargo test --offline` 共 **4 次**（背景串行，2026-09-29 18:46–19:2x），四次均 `EXIT=0`；自算聚合四次均 `targets=37 passed=353 failed=0 ignored=7`、大写 `FAILED` 行=0、`panicked`=0。每次唯一的 ignored target 是 `tests/godot_smoke.rs`（`test result: ok. 0 passed; 0 failed; 7 ignored`）。ignored 未增加：`#[ignore]` 出现数在 `ba32de6` 与 HEAD 都是 8，套件两次口径都是 7，且 `git diff --stat ba32de6..HEAD -- tests/godot_smoke.rs` 为空。无测试被删/放宽：`git diff --name-status ba32de6..HEAD -- tests` 只有 `A tests/endpoint_request_count.rs`；`git diff -U0 ba32de6..HEAD -- tests` 的全部删除行只有 `--- /dev/null`。353 = 基线 352 + 新增 1 条（新 target `endpoint_request_count` = 1 passed，见 run1.txt:220/230-232）。"
    },
    {
      "id": "COUNTER_LAYER",
      "pass": true,
      "evidence": "计数器在**测试侧活替身的 TCP accept 路径**上自增：`tests/endpoint_request_count.rs:112-117`（`listener.accept()` 成功后第一件事 `thread_accepted.fetch_add(1)`，:117），它位于 `McpChannel::call_with_meta`（`src/tools/mod.rs:265-306`）**之下**、DR-55 早退（`src/tools/mod.rs:279-285`，在任何 `spawn_blocking` 之前 `return`）**之下**、`McpClient::post`（`src/tools/mcp.rs:190-210`，每次 attempt 新建 `ureq` agent，:194）**之下**。因此没有任何生产代码路径能"跳过"这个计数：连接只可能由一次真实 HTTP 尝试产生。测试的自证三段齐全：判死时 `accepted_at_death == 2`（:313-318）、判死后 3 次调用 accept 计数不动（:345-351）、重注册后恰好 +1（:363-375）。我在 4 次全量 + 1 次单跑中均见该测试 `ok`。"
    },
    {
      "id": "NON_VACUITY",
      "pass": true,
      "evidence": "我**自设计并自跑**两处植入（都只改生产代码 `src/tools/mod.rs`，**未触碰任何测试**）：①在判死早退 `return` 之前用已解析的 `client` 真发一次请求 ⇒ 目标测试 `FAILED`，`tests/endpoint_request_count.rs:345:5`，`left: 5 right: 2`（= 三次调用各多 1 个连接），`EXIT=101`；②整段删除判死守卫 ⇒ 目标测试 `FAILED`，`:330:14`（死端点被健康替身应答），`EXIT=101`。两次植入后 blob 均 ≠ HEAD blob，随后均 `git checkout --` 逐字节回退并以三法证明（见 §3）。⇒ 新测试对"零重试但发一次"与"什么都发"两类反例**都有牙**。"
    },
    {
      "id": "REPORT_CORRECTION",
      "pass": true,
      "evidence": "`TASK-DR54-REPORT.md` §3.2 的更正块（`<a id=\"dr57-correction\">`，文件 146-152 行）①**逐字引述**了旧文（我以 `git show ba32de6:.spec/hof-rs/tasks/TASK-DR54-REPORT.md` 独立证实该句在批次起点确实存在，内容逐字一致，仅引文里补了 Markdown 粗体）；②明确写出原推理为何无效（判死后 `EndpointLiveness::observe` 第一行 `return`——`src/tools/endpoint.rs:153-156`；且 `call_with_meta` 判死时在 `spawn_blocking` 之前就 `return`，`observe` 根本不被调用 ⇒ `consecutive_transport_failures` 是**结构性恒等**，非观测）；③指名新测试 `tests/endpoint_request_count.rs::a_dead_endpoint_sends_zero_requests_to_the_transport_layer`。`git diff ba32de6..HEAD -- .spec/hof-rs/tasks/TASK-DR54-REPORT.md` 显示**只有这一处**和 §4.3 表内一条"DR-57 补记"，其余结论未动，**不是**把报告粉饰成"原本就对"。**唯一缺陷**：更正/报告里"（实测 5 == 5）"是错的——见 DEF-6。"
    },
    {
      "id": "DEF2",
      "pass": true,
      "evidence": "`InputChannelProbe.has_action` 字段**已删除**（`src/adapter/godot.rs` 的 diff：删 `pub has_action: Option<bool>` 与唯一写入点 `has_action: None`，:1384-1391 的构造块），并加结构体文档注释解释"自语义迁移起恒 None、无读者、却序列化进已发布原始证据，null 会被读成'动作不存在'、不要再加回来"。**无读者**：全仓 `src/**/*.rs`+`tests/*.rs` 中不再存在字段读取点（剩余 `has_action` 全是 `probe_scripts::has_action` 这个 GDScript 生成器 `godot.rs:2689-2690`、注释、以及 `tests/evidence_battery.rs:583/1856` 的**替身识别字符串**）。**有读者的字段一律未改**：diff 只删字段+加注释，`capability`/`game_process_reachable`/`is_pressed_before`/`axis_*`/`pressed`/`moved_while_pressed`/`declared_in_project_godot`/`detail` 原样。它自报的同形残留 `is_pressed_before` **确实存在**：声明 `godot.rs:2841`、唯一写入 `godot.rs:1387`（恒 `None`）、全仓无任何读取点（仅冻结 fixture `tests/fixtures/dr58/smoke_t7_input_channel_probe.json:211` 的历史字节）。"
    },
    {
      "id": "FLAKE",
      "pass": true,
      "evidence": "**复现了，且与本批无关（既有测试脆弱性）**。我自己跑 4 次全量 `cargo test --offline` 全部 exit 0（0 次 flake）；但我**单独**直接运行已构建的 `target\\debug\\deps\\endpoint_liveness-d8e3fbf20bc74977.exe`（不启动 cargo、不运行本批新增的 `endpoint_request_count` target）：第 1 轮 20 次中第 12 次 `exit=101 / 6 passed; 1 failed`；第 2 轮 40 次全绿；第 3 轮 100 次中第 51 次失败并**抓到逐字输出**：`thread 'the_editor_endpoint_state_is_separate' panicked at tests\\endpoint_liveness.rs:435:10: … Error encountered in the status line: 远程主机强迫关闭了一个现有的连接。 (os error 10054)`，`6 passed; 1 failed`。合计单跑 **111 次、2 次失败（≈1.8%）**，失败点与实现者报告的 `:435:10`/os error 10053 **同一行、同一"status line"传输层形态**（10053/10054 都是 abort/reset）。归因：`tests/endpoint_liveness.rs` 的内容在 `ba32de6` 与 HEAD **blob 逐字节相同**（两边 `2e5b95c7…`，区间零提交零 diff），且 flake 在**新 target 完全未运行**时即复现 ⇒ **不是本批引入**。"
    },
    {
      "id": "GUARDS",
      "pass": true,
      "evidence": "**引擎树（嵌套仓，按 D242）**：`git -C godot-mcp/godot status --porcelain -uno`=**0** 行、`--untracked-files=all`=**0** 行；嵌套 HEAD 仍 `fc63af77c3`（`evid: fix a comment typo in the mcp029 guard block (TASK-154)`）；`godot-mcp/godot/modules/mcp_server/tools/running_game_test_execution.cpp` mtime **2026-09-27 00:00:14**、sha256 `ece4ae63d445719b662a6e9ad99ba80bebba3ea3c94468094c7e9cb820ddff3f`（远早于本批 17:56:51）。我同时证明 pathspec 能命中：`git ls-files godot-mcp`=**6484** 行、`git ls-files godot-mcp/godot`=**0** 行（这正是"外层 `git diff` 对引擎树是空判"的原因）。**`runs/**`**：`runs/smoke-t6`=135 文件、最新 mtime **2026-09-29 02:32:01**；我按 DR-54 验收报告 §2 附注的同一算法自算摘要 = `files=135 digest=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03`，与实现者/前验收逐字一致；`runs` 全域最新 mtime = **2026-09-29 14:44:16**，`mtime > 2026-09-29 17:00` 的文件数 = **0**；全域自算 `files=5147 digest=01ff775e36935d3d92dab6919fe030389a8ff53483c52e87288ad711ec840dc3`（与实现者一致）；`frame-00.png`=4246 B、sha256 `bef0936d…7ea2`。**`.workspace/mario/**`** 外层不跟踪（ls-files=0），其下最新 mtime **14:32:28**、`>17:00` 文件数 **0**。**PRD** sha256 = `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`。**Cargo**：`git diff --stat ba32de6..HEAD -- Cargo.toml Cargo.lock` 与 `53f6f9d..HEAD` 均空。**未 stage**：`git diff --cached --stat` 空。**未 push**：`origin/master=afb649a…`，ahead=4（我未执行任何 git 写操作，除 §3 的植入-回退）。"
    },
    {
      "id": "TRAPS",
      "pass": true,
      "evidence": "①不存在的 pathspec 不报错：`git diff --stat ba32de6..HEAD -- path/that/does/not/exist` **无输出且 exit=0**，而同一命令形式对真路径 `-- src/adapter/godot.rs` 得 `12 ++++++++++--`；⇒ 空 diff 只有在先证明 pathspec 命中后才可信（我对 godot-mcp 用 `git ls-files`=6484、对 `src/tools/mod.rs` 用 `git ls-files`=1 证明）。②cmd 的 `^`：`cmd` 下 `echo 440fc89^:tests/endpoint_request_count.rs` 输出 `440fc89:tests/endpoint_request_count.rs`（`^` 被吃），`cmd /c` 里 `git cat-file -e 440fc89^:tests/endpoint_request_count.rs` = **exit 0**；而 pwsh 直传 `git cat-file -e \"440fc89^:…\"` = **exit 128**（父提交 `ba32de6` 没有该文件，`fatal: path … exists on disk, but not in '440fc89^'`）。⇒ 用 cmd 会把"本批新增的文件"伪造成"父提交早就有"；正确读法是用 pwsh 直传整个 rev 或先 `git rev-parse <rev>^`。"
    }
  ],
  "defects": [
    {
      "id": "DEF-6",
      "severity": "major",
      "what": "本批的\"更正后的证据陈述\"里写了一个**未经该测试产生的\"实测\"数字**：\"随后三次调用断言 accept 计数纹丝不动（**实测 5 == 5**）\"。新测试在原始树上的真实观测是 **2 == 2**（判死时 `accepted_at_death==2` 由 `tests/endpoint_request_count.rs:313-318` 硬断言；随后 `:345-351` 断言 `double.accepted() == accepted_at_death`；重注册对照 `:371-375` 是 `+1` ⇒ 上限 3）。`5` 只出现在**我/实现者植入\"判死后仍发一次\"时的失败输出**（`left: 5 right: 2`）。这是把**植入态的数字**写成了**pristine 的实测**——恰好是本批要根除的\"以观测充因果\"的同类失误（只是这次错在更正文本自身）。它不改变\"判死后零请求\"的结论（结论由测试断言与我的两处植入独立支撑），但会误导复核者。",
      "reproduction": "读 `TASK-DR57-REPORT.md:114`（§2）与 `:263`（§4 的更正新文）、`TASK-DR54-REPORT.md` 的 DR-57 更正块（`（实测 5 == 5）`）、`DECISIONS.md:9558`（D244 亦引用）；对照 `tests/endpoint_request_count.rs:313-318`（`assert_eq!(accepted_at_death, 2, …)`，原始树通过）与 `:345-351`、`:371-375`。`5` 的来源见任一植入日志（我的 `%TEMP%\\dr57acc\\myA.txt` 或实现者的 `%TEMP%\\dr57-plant\\A.txt`）：`left: 5 right: 2` 是**失败**输出，不是通过时的观测。",
      "impact": "文档级、非语义级；建议由决策者在下一批把 3 处（两份报告 + D244 不可由我这批改）改为\"实测 2 == 2（重注册后 3）\"或直接删除该括注。"
    },
    {
      "id": "DEF-7",
      "severity": "info",
      "what": "更正块自称\"**逐字引述**\"旧文，但引文把原句的 `（计数不再增长 ⇒ 确实没再发请求）` 加了 `**` 粗体，严格说不是逐字节。文字内容与 `git show ba32de6:` 的原句一致，属排版差异，不构成粉饰。",
      "reproduction": "`git show ba32de6:.spec/hof-rs/tasks/TASK-DR54-REPORT.md | Select-String '计数不再增长'` 与原句对照（无粗体）。"
    }
  ],
  "risks": [
    "新计数替身 `CountingJsonRpc` 与既有 `ScriptedMcp` 同形：都是\"写完响应立刻 drop 连接\"。既然旧替身在 111 次单跑里 2 次给出 status-line 级的 reset/abort（10053/10054），新测试理论上也可能以同样机制偶发（我 4 次全量 + 1 次单跑未见）。建议 DR-60 修因时把两个替身的关闭时序一起处理，或至少记录该形态。",
    "计数口径是\"连接数\"而不是\"HTTP 请求数\"：`McpClient::post` 每次 attempt 新建 agent（`src/tools/mcp.rs:194`）且替身回 `Connection: close`，所以当前 1 连接 = 1 尝试；一旦将来客户端改为连接复用，该测试会变松（实现者已在报告 §8.3 自曝，我确认属实）。",
    "DEF-6 的\"5 == 5\"已被写进 `DECISIONS.md` D244（决策者工件，本批与我都不应改）与两份报告；若不在下批修正，错误数字会随\"已验收\"标签长期留存。",
    "判死**之前**的重试乘法（传输层 3 次 × 上层 2 次 ≈ 6 次 HTTP、按 timeout=120s 推算仍可能烧约 12 分钟）不在本批范围，仍待 §16 裁（D239/D244 已登记）。",
    "flake 的真实机制未被钉死：我给出的\"替身写完立即关闭 → 客户端读到 RST（status line 失败）\"只是**假设**；我未构造确定性触发（本批不允许改测试、也没必要）。DR-60 应先刻画再修因。"
  ],
  "unverified": [
    "基线 `352 passed / 36 targets`（`ba32de6` 上的全量）我没有 checkout 去重跑：本批要求不碰历史与工作树，故只验证了 HEAD 的 353/37 与\"353−352=新增 1 条 target\"的结构一致性。",
    "实现者 `dr57-plants.ps1` 的两处植入我没有重跑其脚本：我读到了真实日志（`%TEMP%\\dr57-plant\\A.txt`/`B.txt`/`*.restore.txt`，EXIT=101、blob 前后比对齐全），并**自己另做了两处设计不同**的植入（§3）——即\"非空洞性\"这件事由我独立复现，而那两个具体脚本未逐条复跑。",
    "flake 在 `cargo test --offline` **全量**下的复现率：我只跑 4 次全量（0 次失败），实现者 6 次中 1 次；合计样本太小，无法给稳定的全量频率。我用**单跑 111 次**（2 次失败）来量化该测试自身的脆弱性。",
    "`.workspace/mario/**` 只由 mtime 证明未动（外层不跟踪、无嵌套仓可比）。",
    "新测试在真机/长时压力下的行为未验（离线批次）。"
  ]
}
```

**真实命令与退出码（我自己跑的）**

| # | 命令 | 真实结果 |
|---|---|---|
| 1 | `cargo test --offline`（背景串行 ×4，日志 `%TEMP%\dr57acc\run1..4.txt`） | 四次 `EXIT=0`；每次 `targets=37 passed=353 failed=0 ignored=7`；`FAILED`=0、`panicked`=0 |
| 2 | `cargo test --offline --test endpoint_request_count`（植入回退后 pristine 复验） | `test result: ok. 1 passed; 0 failed`，`EXIT=0` |
| 3 | 同上（我的植入 A：判死前仍发一次） | `FAILED`，`endpoint_request_count.rs:345:5`，`left: 5 right: 2`，`EXIT=101` |
| 4 | 同上（我的植入 B：删除整段判死守卫） | `FAILED`，`endpoint_request_count.rs:330:14`，`EXIT=101` |
| 5 | `target\debug\deps\endpoint_liveness-d8e3fbf20bc74977.exe` 直接跑 **111** 次 | 109 次 `exit=0`（7 passed），2 次 `exit=101`（6 passed; 1 failed，`:435:10`，os error 10054） |
| 6 | `git diff --name-status ba32de6..HEAD -- tests` | 仅 `A tests/endpoint_request_count.rs` |
| 7 | `git diff ba32de6..HEAD -- .spec/hof-rs/tasks/TASK-DR54-REPORT.md` | 仅更正块 + 一处 DR-57 补记 |
| 8 | `git -C godot-mcp/godot status --porcelain -uno` | **0 行**（`--untracked-files=all` 亦 0 行） |

---

## 2. 逐项核对表（对应验收书 §1）

| # | 复核项 | 结论 | 我的证据 |
|---|---|---|---|
| 1 | 套件 exit 0 / 353 / 0 / 7（37 targets）；ignored 未增；无测试被删/放宽/`#[ignore]` | **pass** | 4 次全量自跑，逐次 353/0/7；`tests` 区间只有新增文件、零删除行；`#[ignore]` 出现数 8↔8、套件 ignored 7↔7 |
| 2 | 新测试真"数在不会循环的那一层"（call_with_meta 之下、早退之下、post 之下） | **pass** | `endpoint_request_count.rs:112-117` 的 accept 计数；对照 `mod.rs:265-306`/`279-285`/`287-289`、`mcp.rs:190-210`（§4） |
| 3 | 非空洞性（我自设 ≥2 处植入，改生产代码，必红，逐字节回退三法证明） | **pass** | §3：myA/myB 均 `EXIT=101`；回退后 `porcelain_lines=0`、`diffstat_lines=0`、`hash-object == HEAD blob` |
| 4 | 报告更真：引原文 + 写清原推理为何无效 + 指向新测试 + 不改其它结论 + 不粉饰 | **pass（附 DEF-6/DEF-7）** | `git show ba32de6:` 证实原文；更正块三要素齐备；diff 显示仅一处更正；DEF-6 = 更正文本内嵌错误"实测 5 == 5" |
| 5 | DEF-2：字段已删、有读者的字段未动、文档解释清楚；同形残留 `is_pressed_before` 属实 | **pass** | godot.rs diff；全仓无字段读者；`is_pressed_before` 声明 :2841 / 唯一写 :1387 / 无读者 |
| 6 | flake 多次复现、归因既有/本批 | **pass（判为既有）** | 单跑 111 次 2 次失败（抓到我自己的 10054 逐字输出）；文件 blob 与 `ba32de6` 逐字节相同；新 target 未运行时仍复现 |
| 7 | 禁区：引擎树（嵌套仓）、runs、PRD、Cargo、未 push/未 stage | **pass** | §1 GUARDS；嵌套仓 0 行、runs 摘要逐字一致、PRD sha 一致、Cargo 零 diff、staged 空、origin=afb649a |
| 8 | 两个假绿陷阱各实测一次并给正确读法 | **pass** | §1 TRAPS：不存在 pathspec exit 0 空 diff；cmd `^` 把 `440fc89^:…` 吃成 `440fc89:…`（128 → 0） |

---

## 3. 反例清单（我的自设计植入 + 观测 + 是否推翻）

**植入位置**：`src/tools/mod.rs` 的 `McpChannel::call_with_meta`。**两次都只改生产代码，未动任何测试。** 日志：`%TEMP%\dr57acc\myA.txt`/`myB.txt`/`myA.restore.txt`/`myB.restore.txt`；脚本 `%TEMP%\dr57acc\my-plants.ps1`（仓外）。

**植入 A —— "零重试但仍发一次"（与实现者的写法不同：不用诊断性 clone，直接用已解析的 `client` 同步发）**

```text
        if let Some(liveness) = self.endpoint_state(&endpoint) {
            if liveness.unavailable {
                let _ = client.call_traced(tool, serde_json::json!({}));   // <-- 我的植入
                return Err(
                    endpoint::McpEndpointUnavailableError::new(liveness, tool).into(),
                );
            }
        }
```

| 项 | 内容 |
|---|---|
| 植入前 blob | `ddf6f4e4de1080e02863e84295febf821772af1b`（= HEAD:src/tools/mod.rs） |
| 植入后 blob | `33598a9e415d45bc77135d53d136c8b92e6ee990`（≠ 植入前 ⇒ 植入确实落盘） |
| 观测 | `FAILED`；`tests\endpoint_request_count.rs:345:5: assertion left == right failed: ZERO requests may reach the transport layer after the endpoint is declared dead, but the live double accepted 3 new connection(s) / left: 5 right: 2`；`test result: FAILED. 0 passed; 1 failed`；`EXIT=101` |
| 读法 | `left` 是三次调用后的总 accept 数 5，`right` 是判死时冻结值 2 ⇒ 三次调用各多开 **1** 个连接（每次都真到达了端点），而 `failure.attempts == 1` 仍成立 ⇒ 正是 DEF-1 的反例被抓住 |
| 是否推翻 | **不推翻**（反而证明新测试有效） |

**植入 B —— 删除整段判死守卫（"判死后什么都发"）**

| 项 | 内容 |
|---|---|
| 植入前 blob | `ddf6f4e4de1080e02863e84295febf821772af1b` |
| 植入后 blob | `ccaa2c057f2717d3a4ac3ad5f288acaa6d7d5bf9`（≠ 植入前） |
| 观测 | `FAILED`；`tests\endpoint_request_count.rs:330:14: a dead endpoint stays dead, even with a healthy peer: Object {"tree": Object {"name": String("Main")}}`；`EXIT=101` |
| 读法 | 健康替身**应答了死端点** ⇒ "死端点必须定型拒绝"先响；与 A 的红色语义不同（A 是计数响，B 是"发出去并成功了"响） |
| 是否推翻 | **不推翻** |

**回退的三法证明（逐字来自我脚本的输出；两次植入各一份）**

```text
PLANT myA
planted_blob=33598a9e415d45bc77135d53d136c8b92e6ee990
planted_differs_from_head=True
porcelain_lines=0
diffstat_lines=0
hash_object=ddf6f4e4de1080e02863e84295febf821772af1b
head_blob=ddf6f4e4de1080e02863e84295febf821772af1b
blob_equal=True
pathspec_tracked_lines=1
PLANT myB
planted_blob=ccaa2c057f2717d3a4ac3ad5f288acaa6d7d5bf9
planted_differs_from_head=True
porcelain_lines=0
diffstat_lines=0
hash_object=ddf6f4e4de1080e02863e84295febf821772af1b
head_blob=ddf6f4e4de1080e02863e84295febf821772af1b
blob_equal=True
pathspec_tracked_lines=1
```

即 `git status --porcelain` **空**、`git diff --stat` **空**、`git hash-object src/tools/mod.rs` **逐字节等于** `git rev-parse HEAD:src/tools/mod.rs`；`pathspec_tracked_lines=1` 证明该 pathspec 真能命中（不是假绿陷阱）。回退后我另跑一次 pristine 新测试 = `1 passed`、`EXIT=0`；收尾 `git status --porcelain`（**含 untracked**）为 **0 行**（本报告文件写入前）。

**对实现者两处植入日志的核对（线索级，非重跑）**：`%TEMP%\dr57-plant\A.txt` 与 `B.txt` 内容与其报告 §3.1/§3.2 逐字一致（A：`:345`、`left 5/right 2`、EXIT=101；B：`:330`、EXIT=101），`A.restore.txt`/`B.restore.txt` 的 `hash_object/head_blob` 均为 `ddf6f4e4…`（与当前 HEAD blob 一致）。

---

## 4. 对"计数器层不可循环"的独立判定

**结论：成立（不循环）。**

- **计数点**：`tests/endpoint_request_count.rs:112-117` —— 循环体 `listener.accept()` 返回后第一件事就是 `thread_accepted.fetch_add(1, SeqCst)`（:117），**在替身自己的 TCP accept 路径上**，与生产代码的任何判断无关。停止替身用的是 flag（:113/:161-166），**不靠自连接唤醒**，所以计数只会被 caller 打开的连接推动。
- **层位**（从下到上）：TCP accept（:117） → `McpClient::post`（`src/tools/mcp.rs:190-210`；每次 attempt 新建 agent，:194） → `McpChannel::call_with_meta`（`src/tools/mod.rs:265-306`） → DR-55 判死早退（`mod.rs:279-285`，在 `spawn_blocking`/`call_traced`（:287-289）**之前** `return`）。
- **与旧证据的区别**：旧测试用**已关闭端口**（连不上、无法在服务侧计数），只能读 `consecutive_transport_failures`；而该量被 `EndpointLiveness::observe` 的 `if self.unavailable { return; }`（`endpoint.rs:153-156`）在判死后**结构性冻结**，且判死后 `call_with_meta` 根本不调用 `observe`（`mod.rs:281-284` 直接 return）⇒ 旧推理确实是恒等式。
- **非空洞控制**：新测试先断言 `accepted_at_death == 2`（:313-318）——计到 2 才说明计数器会动；判死后 3 次调用断言计数不变（:345-351）；重注册后断言 `+1`（:371-375）——计数器能再动。
- **我的两个植入**从两个方向证实：A（早退前发一次）使计数 +3，B（删守卫）使死端点被应答。⇒ 计数器**不可能被门冻住**，也不会漏计。

---

## 5. flake 的独立判定与复现次数统计

| 项 | 我的实测 |
|---|---|
| 全量 `cargo test --offline` | **4 次**（18:46–19:2x），全部 `EXIT=0 / 353 passed / 0 failed / 7 ignored`；**0 次 flake** |
| 单跑 `endpoint_liveness` 可执行文件 | **111 次**：轮1 20 次 → 第 12 次失败（`exit=101`，仅摘要，未留逐字）；轮2 40 次 → 全绿；轮3 100 次 → 第 51 次失败并**抓到逐字输出**；合计 **2/111 ≈ 1.8%** |
| 我抓到的逐字失败 | `thread 'the_editor_endpoint_state_is_separate' panicked at tests\endpoint_liveness.rs:435:10: the editor endpoint is alive: MCP transport failure to http://127.0.0.1:59094/mcp: … Error encountered in the status line: 远程主机强迫关闭了一个现有的连接。 (os error 10054)`；`6 passed; 1 failed` |
| 与实现者报告的对照 | 同一测试、同一行 `:435:10`、同一"status line"形态；实现者是 6 次全量中 1 次、os error **10053**，我是单跑 111 次中 2 次、os error **10054**（10053/10054 都是连接被 abort/reset 的 WSA 码） |
| 文件是否本批所改 | **否**：`git rev-parse ba32de6:tests/endpoint_liveness.rs` = `git rev-parse HEAD:tests/endpoint_liveness.rs` = `2e5b95c7663d4786a8c91896aea2212bdcbec344`；`git log --oneline ba32de6..HEAD -- tests/endpoint_liveness.rs` 为空；`git diff --stat` 空 |
| 是否依赖本批新增 target | **否**：我的 111 次是**直接运行** `endpoint_liveness` 的可执行文件，`endpoint_request_count` 完全没有参与；cargo 的 target 是**串行**执行的（进程树观测到同一时刻只有一个测试 exe） |
| **归因** | **既有测试脆弱性，非本批引入**。失败发生在编辑器端点调用（`endpoint_liveness.rs:432-435`）上，对端是同文件内的 `ScriptedMcp`：它 `write_all` 响应后**立即 `return`**（:154-161），socket 随即 drop；在 Windows 环回上客户端可能在读到状态行前就收到 RST/abort ⇒ `Error encountered in the status line`。这是**机制假设**（未构造确定性触发），但"与本批无关"由 blob 恒等 + 新 target 缺席时仍复现两点**独立支撑**。 |

---

## 6. 未验证项与理由

见 §1 JSON 的 `unverified`。要点：基线 352/36 targets 未在 `ba32de6` 上重跑（不得 checkout 历史）；实现者两处植入脚本未逐条重跑（我改用两处自设计植入复现"非空洞性"）；flake 的全量频率样本仍小（4 次全是绿）；`.workspace/mario/**` 仅 mtime 证据；新测试的真机/长时行为离线不可验。

**"不碰端口/不联网"的诚实披露**：我全程离线。所有网络活动都是测试与替身在**进程内** `TcpListener::bind("127.0.0.1:0")` 绑定的内核临时环回端口；我从未 connect/探测 9877 或任何引擎端口，未启动 Godot，未联网，未调用模型端点。

---

## 7. 我没有独立复核的部分

1. `ba32de6` 上的基线套件（352/0/7、36 targets）没有重跑——为遵守"不 checkout、不动历史/工作树"的约束，只用 HEAD 的 353/37 与"新增恰 1 条 target"的结构对照。
2. 实现者 `dr57-plants.ps1` 的两处植入与 `nonvacuity` 历史脚本未逐条重跑；我核对了其真实日志与 blob 记录，并**自己另做**两处设计不同的植入。
3. flake 的真实机制未钉死（给出的是假设 + 频率证据），也未构造确定性触发；DR-60 应按任务书 `TASK-DR60.md` 先刻画再修因。
4. 新测试以外的既有测试未逐条审计（只验证了"批次区间内 tests 仅新增一个文件、无删除行、ignored 未增"）。
5. 引擎侧/真机语义（E3、ACTION_NOT_BOUND 文面等）不在本批范围，离线不可验。

---

## 8. 给下一批的建议（**我没有修改任何代码/文档，除本报告与 §3 的受控植入-回退**）

1. **（建议最高优先，记账）** 修正 DEF-6：把 `TASK-DR57-REPORT.md:114`、`:263`、`TASK-DR54-REPORT.md` 更正块、以及 `DECISIONS.md:9558` 里的"实测 5 == 5"改为实测的 `2 == 2`（重注册后 3），或直接删除该括注；`5` 只属于植入态失败输出。这正是本批的主题（证据陈述必须可复现），不能让它以"已验收"名义留存。
2. **（DR-60）** 把既有 `ScriptedMcp` 与新增 `CountingJsonRpc` 的"写完立刻 drop"关闭时序一起纳入定因：先刻画（≥20 次单跑/全量、记录逐次输出），再给因果解释；若指向产品则停下上报，否则让替身确定性收尾（如半关闭/等待对端 FIN），并给出"至少 10 次全量全绿"的重复证据。
3. **（口径）** 在报告里把"另一工程师复核时可复现的量"写清：新测试在 pristine 上的可打印观测是 `accepted_at_death=2`、post-death `2`、re-arm `3`；不要让植入态数字混入证据段。
4. **（形态假设）** 把"1 连接 = 1 HTTP 尝试"的前提（`mcp.rs:194` 每次 attempt 新建 agent + 替身 `Connection: close`）写成测试注释里的显式不变量；若客户端引入连接复用，该测试需改为在服务侧解析请求而非数连接。
5. **（残留）** 继续把"判死前重试乘法"留在 §16 处理；`is_pressed_before`（恒 None、无读者、仍进原始证据）应与 DEF-2 同判据一并处置。

---

### 附：验收者行为自证

- 写操作仅有：①`src/tools/mod.rs` 两处受控植入并各自 `git checkout --` 逐字节回退（三法证明见 §3）；②本报告文件（`未跟踪`、未 stage）。脚本与日志全部在仓外 `%TEMP%\dr57acc\`。
- 收尾状态（写本报告前）：`git status --porcelain`（含 untracked）= **0 行**；`git diff --stat` 空；`git diff --cached --stat` 空；`git hash-object src/tools/mod.rs` == `git rev-parse HEAD:src/tools/mod.rs` = `ddf6f4e4…`；`git rev-parse HEAD` = `54e00d1433adc18cccdd0039532486abfea25896`（我未改写历史、未 rebase/force、未 push、未 stage）。
- 验收期间编排者自行推进了文档提交（`b35b782`、`54e00d1`）；我在头尾两次确认 `src`/`tests` 的批次 diff 不变，并让回退证明对齐**当时**的 HEAD blob。
