# TASK-DR60-ACCEPTANCE — DR-60（既有 flake：先刻画再修因）**独立验收报告**

> 独立验收子代理。**未继承**实现者或调度者的结论；本报告全部证据由本会话自己产生。
> 判据：`.spec/hof-rs/tasks/TASK-DR60.md`（任务书）、`.spec/hof-rs/tasks/TASK-DR60-ACCEPT.md`（验收简报）、
> `DECISIONS.md` **D244/D252/D254**（以及执行期间调度者新增的 **D255**，仅作其决策记录引用）、
> `.spec/hof-rs/tasks/TASK-DR60-REPORT.md`（**仅线索，非证据**）。
> **离线**：未启动 Godot、未触碰任何外部/MCP 端口、未联网、未调用任何模型端点、未 `push`、未 `stage`、未改写历史。
> 未修改 `.workspace/mario/**`、`runs/**`、`.spec/hof-rs/PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`，
> 也**未修改任何被跟踪文件**（唯一新增文件就是本报告）。所有临时物写在**仓外**
> `F:\dr60-acc`（脚本/日志）与 `F:\dr60-prefix`（对照构建）。**发现的问题一律只报告，未修**。

**被测对象**：代码树 = `0f78bb0`（DR-60 修复）及其后的整棵树。
`git diff --stat 26609a8..HEAD -- src tests Cargo.toml Cargo.lock` = **`tests/endpoint_liveness.rs | 12 ++++++++++++`**（仅此一处）。
验收期间 HEAD 由 `5342a7d` 漂到 **`836ad5451fb408f128d7ed7ba7872abacc15c533`**（调度者的**纯文档**提交：
`a2baafb`=D255、`836ad54`=DR-65 任务书等；`src/`/`tests/`/`Cargo.*` 零改动）。
`origin/master` 全程 = **`26609a8a1d57d9e2a14ca59f75aabefbeb284114`**（DR-60 的两个提交**未 push**）。
批量提交：**`0f78bb0`**（修复，`tests/endpoint_liveness.rs` +12/-0）、**`5342a7d`**（报告，506 行）。

**一句话结论**：**pass**。修复是**机制级的修因**（一句 socket 模式声明，不是 sleep/重试/放宽断言），
机制与产品无关（测试替身），十次全量有逐份日志且我复跑 3 次全量全绿；我自己把**修前**二进制重建于仓外并
**独立复现了 1.67% 的 flake**（120 次 2 次失败，panic 同在 `:435:10`）。唯一不合格项是 `.dr60/` 仍留在仓内且未忽略
（DEF-1，非 fail 门槛，D255 已记其处置计划）；另有三条**证据台账/措辞**类小缺陷（DEF-2/3/4）。

---

## 1. 结构化结论（机器可读）

```json
{
  "verdict": "pass",
  "criteria": [
    {
      "id": "CHARACTERISED",
      "pass": true,
      "evidence": "实现者 65 次单跑 2 次失败的**逐次记录确实存在**：`.dr60/raw_alone/summary.txt` 恰 40 行 `run=NNN start=... exit=... :: test result: ...`，其中 `run=022 ... exit=101 :: test result: FAILED. 6 passed; 1 failed`；`.dr60/raw_alone/run022.log:23` 是逐字 panic；`.dr60/alone1.log:17` 是另一驱动的 `run=16 ... exit=101`，`:18-46` 是完整逐字失败块（含 10053）。**我自己复现**：把 `0f78bb0^:tests/endpoint_liveness.rs`（`git rev-parse` = 2e5b95c7663d4786a8c91896aea2212bdcbec344，与放入副本的 `git hash-object` 一致）放回**仓外**副本 `F:\\dr60-prefix`，用与 HEAD 相同的 src/Cargo 构建（`cargo test --offline --test endpoint_liveness --no-run` → `Finished` 35.78s），直接运行该 exe **120 次 → 2 次失败（1.67%）**：run001（`os error 10054`）、run091（`os error 10053`），两次 exit=101，panic 均在 `tests\\endpoint_liveness.rs:435:10`，`test result: FAILED. 6 passed; 1 failed`。⇒ 失败**单跑即出现**（进程内没有别的测试），不是全量并发的资源效应。逐字输出见 §3.2。"
    },
    {
      "id": "CAUSE_IS_TEST_NOT_PRODUCT",
      "pass": true,
      "evidence": "机制落在**测试自己的回环替身**，不在产品。(a) 代码：`tests/endpoint_liveness.rs:63-65` `listener.set_nonblocking(true)`（只为轮询 shutdown），`:74` accept 之后、**修复前**直接把 stream 交给 `serve`（`:132`）；`serve` 的首个 `read` 在 `:135-140`，`:139` 是 `Err(_) => return`（放弃、关连接、从不应答）。(b) **我的独立 socket 探针**（仓外 `F:\\dr60-acc\\probe.rs`，`rustc -O probe.rs`）在 Windows 上以确定性时序证明：从非阻塞 listener accept 出的 socket **就是非阻塞** —— `OLD_SHAPE first_read=Err(Os { code: 10035, kind: WouldBlock, ... }) elapsed_ms=0`（客户端字节 300ms 后才写），而在 accept 处加 `set_nonblocking(false)` 后 `FIXED_SHAPE first_read=Ok(18)`，读到 18 字节请求首部（以 GET / HTTP/1.1 开头），`elapsed_ms=298`（即真的阻塞等待）。(c) 产品代码里没有任何非阻塞 socket：`grep -rn set_nonblocking src/` = **0 命中**。(d) 失败在传输层、状态机之前：`src/tools/mcp.rs:190-209` 的 `post` 每次**新建** `ureq::Agent`（`:194-196`，无连接池），而该测试 `McpChannel::new(..., 5, 0)`（`tests/endpoint_liveness.rs:427`）的 **max_retries=0**，连'把传输失败重试掉'的余地都没有；失败点是 `:444-447` 的 `.expect('the editor endpoint is alive')`。(e) 我的 180 次直跑（60 修后 + 120 修前）里，本 target 另外 6 条测试**从未失败**，只有 `the_editor_endpoint_state_is_separate` 失败（2 次）。"
    },
    {
      "id": "FIXES_CAUSE_NOT_SYMPTOM",
      "pass": true,
      "evidence": "逐行读两处 diff：`git show 0f78bb0 --stat` = **1 file changed, 12 insertions(+)**；`git show 0f78bb0 -- tests/endpoint_liveness.rs` 的 12 行 = `ScriptedMcp` 的 6 行文档注释（`:43-48`）+ accept `Ok` 分支里的 6 行（`:77-79` 三行注释 + `stream` + `.set_nonblocking(false)` + `.expect(...)`，即**只有一句功能性语句**）。**没有**新增或加长任何 sleep、**没有**新增任何重试、**没有**放宽任何断言：2ms 退避在 diff 里是 **context**（修复前既有），测试函数体 `:423-453` 在 diff 里**全是 context**（未改一行），`.expect('the editor endpoint is alive')` 一字未动（修前在 `:435`、修后在 `:447`，blob 2e5b95c7→8ef14d2）。语义上它把'替身首个 read 是否落在客户端字节之前'从**调度器掷骰**变成**代码确定性**（read 阻塞直到请求到达），并且**消除的正是产生全部已知失败的那个分支**；它新增的 `.expect` 只会让异常更响、不会更静。⇒ 是修因，不是掩盖。"
    },
    {
      "id": "REPEAT_EVIDENCE",
      "pass": true,
      "evidence": "十条**逐次**记录确实存在：`.dr60/full_runs/summary.txt` 恰 10 行 `run=00N start=HH:MM:SS exit=0`；`run001..010.log` 每份 39 行 `test result:`，我逐份求和 = **372 passed / 7 ignored / 0 failed**（10/10 一致）；十份日志 md5 **两两不同**（10 个不同值）；每份的 `endpoint_liveness` 行都是 `ok. 7 passed; 0 failed; 0 ignored`（10/10）；每份引用的可执行文件正是我随后直跑的那一个 `target/debug/deps/endpoint_liveness-d8e3fbf20bc74977.exe`，且 `cargo test --offline --test endpoint_liveness --no-run` 报 `Finished ... in 0.46s`（**未重编** ⇒ 该二进制与 HEAD 源码一致）。对十份日志扫 `panicked at` / `test result: FAILED` / `error: test failed` / `os error 1005` / `would_block` = **0 命中**。**我自己另复跑全量 3 次**（`cargo test --offline`，串行、不抑制输出）：run1/2/3 = **exit 0 / 372 passed / 0 failed / 7 ignored**，454/452/452 秒，三份日志 md5 互不相同，`panicked`/`FAILED`/`os error 1005` 全 0。"
    },
    {
      "id": "NON_VACUITY_DISCLOSURE",
      "pass": true,
      "evidence": "确定性触发**确实被构造**，且**被我独立复现**：`.dr60/probe_deterministic.log` 记录旧形状 `Err(Os { code: 10035, kind: WouldBlock })`、新形状收到完整请求；我的仓外 `probe.rs` 用同一机制在两个方向复现（见 CAUSE 段）——这是**机制级**证据，不是'跑几次没复现'。频率证据被**明说**：REPORT §5.3/§8.3 声明探针的 1200 次迭代**未跑完**、§7.5 给出 3.1% 的宽置信区间。**但**：REPORT §1.3 把 `iterations=1200 / iter=37,80,100 FAILED` 的引文归到 `.dr60/probe_editor_double.log`，而该文件实际内容是 `iterations=300` + `summary iterations=300 failures=0`（即**修后**那一次），修前探针的失败记录**没有任何保留的原始件** ⇒ DEF-2。因此'非空洞性'成立（机制+频率都给了），但'可核对程度'应降级为'报告文本 + 我的独立机制复现'。"
    },
    {
      "id": "SUITE",
      "pass": true,
      "evidence": "我的 3 次全量 `cargo test --offline`（仓内、串行、不抑制输出、日志在仓外 `F:\\dr60-acc\\full\\run1..3.log`）：**exit 0 / 372 passed / 0 failed / 7 ignored**，与任务书基线（372/0/7）逐字一致；`panicked at` / `test result: FAILED` / `error: test failed` / `os error 1005` = 全 0。`ignored` 未增长：`git grep -n '#[ignore'` 在 `0f78bb0^` 与 `HEAD` **同为 8 行**（`tests/godot_smoke.rs` 的 7 个真属性 `:108/142/233/254/283/350/370` + `:3` 的一句文档注释），全量输出 ignored=7。无测试被删/放宽：`git diff 26609a8..HEAD -- tests/` 只有 `endpoint_liveness.rs` 的 +12 行（全在替身内部，测试函数体未动）；`git diff 26609a8..HEAD -- src Cargo.toml Cargo.lock` = **空**。"
    },
    {
      "id": "GUARDS",
      "pass": true,
      "evidence": "摘要口径**由我独立重建**（仓外 `F:\\dr60-acc\\digest.ps1`）：递归 `Get-ChildItem -Recurse -Force -File`；每文件 = 相对仓根路径（反斜杠转正斜杠、转小写）+ 字节长度 + SHA256（小写 hex），三列 TAB 连接、行间 LF、无尾随换行，行按路径升序且**排序器 = PowerShell `Sort-Object`（文化敏感）**，整体 UTF-8 后取 SHA256。**口径自证**：`runs/smoke-t6` 复算 = **files=135 digest=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03**，与 DR-54/57/59/61/62 记录逐字一致。其余值：`.workspace/mario` = **files=259 digest=4e494547416b2e87ba025d686afef9447d4f92c027917d1790e6fc9deaeaa84a newest=2026-09-29 14:32:28**；`runs` = **files=5147 digest=01ff775e36935d3d92dab6919fe030389a8ff53483c52e87288ad711ec840dc3 newest=2026-09-29 14:44:16**（批次约 23:20 才开始）⇒ 两项都与历史记录一致、无晚于批次窗口的文件。`PRD-mario.md` sha256 = **4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a**（未变）。`git diff --stat 26609a8..HEAD -- Cargo.toml Cargo.lock` 空 ⇒ 无新依赖。未 stage：`git diff --cached --stat` 空。未 push：`git rev-parse origin/master` = **26609a8a1d57d9e2a14ca59f75aabefbeb284114**，HEAD 领先 9 个提交全部只在本地。引擎树（**外层不跟踪 ⇒ 外层 diff 无证据力**）：`git ls-files godot-mcp` = **6484 > 0**（pathspec 真命中），`git ls-files godot-mcp/godot` = **0**（外层空判）；**嵌套仓** `git -C godot-mcp/godot status --porcelain -uno` = **0 行**、`-uall` = **0 行**，嵌套 `HEAD` = **fc63af77c33368c4a1bb839c95d19750554f63a3**，`ls-files` = **15049**，`.gitignore:33` 即 `godot-mcp/godot/`。**唯一不合格项**：`.dr60/` 既未清理也未入忽略（`git status --porcelain` = `?? .dr60/`；`git check-ignore .dr60` = 未忽略；`.gitignore` 无 dr60 规则；61 个文件 / 618 KB）⇒ DEF-1。"
    },
    {
      "id": "HONESTY",
      "pass": true,
      "evidence": "逐条核实：§1.2 的 65 次/2 次有逐次工件（见 CHARACTERISED）；§2 的 file:line 我逐条对照源码为真（修前 `:57-59`/`:68-69`/`:71`/`:124-128`/`:127`，修后 `:64`/`:77-82`/`:132`/`:136-140`/`:139`；panic 修前 `:435`、修后 `:447`）；§3 的 12 行 diff 属实；§4.1 的十次表**与十份日志逐份吻合**（我独立求和）；§4.2 的'确定性触发'方向被我独立复现；§6 的禁区表我逐条复算（含义属实，但它**没把 `.dr60/` 记为待清理项** ⇒ DEF-1）；§8 的 7 条披露里 §8.1（先写错修复）、§8.3（1200 次未跑完）、§8.4（树在脚下移动）、§8.5（'修前基线未自测，引的是任务书数字'）**均属实或方向正确**；§8.2 与 `.dr60/alone1.log` 实际内容不符 ⇒ DEF-3。**未发现伪造输出或日期**：报告引用的每一个可核对数字（10 次/372/7/65 次/2 次/12 行/blob 哈希/嵌套 HEAD）都与工件或我的复算一致。缺陷 DEF-2/3/4 均属**引文与措辞的精确性**，不是把推断写成实测。"
    }
  ],
  "defects": [
    {
      "id": "DEF-1",
      "severity": "minor",
      "what": "临时工作目录 `.dr60/` 仍留在**仓库内**，且既未清理也未进 `.gitignore`（验收简报 §1.7 明确要求二者必居其一）。它不是禁区（禁区是 .workspace/mario、runs、PRD、DECISIONS、godot-mcp），但它使仓库带着 61 个一次性日志文件 / 618 KB 的未跟踪内容交付；任何宽口径 add（如 `git add -A`）都会把一次性原始日志带进历史——这正是 .gitignore 该防的。调度者在 **D255** 里已记录处置决定（'验收通过后把内容迁入 `.spec/hof-rs/tasks/dr60-evidence/` 再清掉仓根'，并明确'在此之前不动它'），故这是**已知且已认领**的收尾项，不构成 fail 门槛，但按简报要求**必须记为缺陷**。",
      "reproduction": "`cd /f/moonbit-hof-rs && git status --porcelain` → `?? .dr60/`；`git check-ignore -v .dr60` → 无输出（未忽略）；`grep -n dr60 .gitignore` → 无匹配；`find .dr60 -type f | wc -l` = **61**；`du -sh .dr60` = **618K**。"
    },
    {
      "id": "DEF-2",
      "severity": "minor",
      "what": "REPORT §1.3 把修前探针的失败记录（`iterations=1200`、`iter=37/80/100 FAILED`）引作 `.dr60/probe_editor_double.log` 的内容，但该文件的实际内容是**修后**那一次运行：`iterations=300` / `summary iterations=300 failures=0`。修前探针的 `served=1 would_block=1 read_error=0` 签名**没有任何保留的原始日志**（`.dr60` 下只有 probe_deterministic.log 与本文件），只能算报告正文的**转述**；§8.3 只披露了'1200 次未跑完'，未披露该文件是修后运行、引文无原始件。影响：该条证据的可核对程度被高估。我以独立机制复现补上了因果链，故不改变结论。",
      "reproduction": "`cat .dr60/probe_editor_double.log` → `iterations=300` + `summary iterations=300 failures=0`；`ls .dr60/*.log` 仅这两份；REPORT §1.3 却引用 `iterations=1200`。"
    },
    {
      "id": "DEF-3",
      "severity": "info",
      "what": "REPORT §8.2 称 25 次驱动（`run_alone.ps1`）'raw failure block did not survive'，但 `.dr60/alone1.log:18-46` 恰好**保存了** run=16 的完整逐字失败块（含 `panicked at tests\\endpoint_liveness.rs:435:10` 与 `os error 10053`）。这是**低估自有证据**（方向与虚报相反），但报告内部的证据台账因此不自洽：§1.2 说'记录在 alone1.log'，§8.2 说'没有留存'。",
      "reproduction": "`sed -n '17,46p' .dr60/alone1.log` → 含 `----- BEGIN VERBATIM OUTPUT run=16 -----` 与完整 panic 块；对比 REPORT §8.2 第二句。"
    },
    {
      "id": "DEF-4",
      "severity": "info",
      "what": "REPORT §1.1/§2.1 把客户端症状固定描述为'读状态行失败（Error encountered in the status line）'。我独立复现的两次失败都只有 `Network Error: ... (os error 10054/10053)`，**没有** status line 前缀 ⇒ 同一个服务端行为（不应答即关闭连接）在客户端可在**写**或**读**的任一点被观察到（ureq 的 `read_next_line` 只在读分支才加该前缀，`ureq-2.12.1\\src\\response.rs:773-800`，消息在 `:791`）。结论（同一 expect、同一行号、同类 errno、同一根因）不变，但'一定是状态行读失败'这一句**过强**。",
      "reproduction": "我的 `.dr60` 外日志 `F:\\dr60-acc\\prefix_runs\\run001.log` 与 `run091.log` 的 panic 行；对比 `.dr60/raw_alone/run022.log:23`（含 status line 前缀）。"
    }
  ],
  "risks": [
    "修后 60 次直跑 + 3 次全量 + 实现者 10 次全量未再现 ≠ 概率为 0：`serve` 的 `Err(_) => return`（`tests/endpoint_liveness.rs:139`）仍在，真正的 ECONNRESET/读取超时仍会以同一个 `.expect` 暴露（实现者 §7.2 已如实记录）。",
    "同形的另两处替身（`tests/dual_endpoint.rs:51-64` 的 RecordingMcp、`tests/endpoint_request_count.rs:103-131` 的 CountingJsonRpc）我**只核对了代码形状**（listener 非阻塞 + accept 后不复位模式后交给读路径），**未实测**它们是否也 flake；实现者对此已声明是'代码检视 + 共享机制，非实测失败'（其 §7.1），措辞诚实；DR-65 任务书已立。",
    "频率的精确值不可得：我的修前 2/120=1.67%、调度者 2/111=1.8%、实现者 2/65=3.1% 同量级，但单次测量的 95% 区间很宽（1.67% 约为 0.2%-5.9%），任何'精确 3%'都属过度声称。",
    "`.dr60/` 若在被迁移前遇到宽口径 add/commit，会把 618 KB 一次性日志写入历史；D255 的迁移计划尚未执行。",
    "我未在**高负载/CPU 争用**下重复测量；本报告的 60+120 次直跑与 3 次全量都是串行、无外部争用条件下测得的。"
  ],
  "unverified": [
    "REPORT §4.2-2 的'300 次迭代 / 1225.32s / 0 would_block'与 §1.3 的 1200 次探针失败记录：只有报告正文（见 DEF-2），我未复跑其探针（探针源 `tests/dr60_probe.rs` 未入库、已删，`git ls-files | grep dr60` 仅有三份 .md 任务/报告文件）。",
    "实现者最初的两次'坏驱动'（run_alone.ps1 / run_raw.ps1）的失败过程无法核对，只能读其 §8.2 自述。",
    "引擎树'内容未改'的正证依赖**嵌套仓 status/HEAD/ls-files 计数**；我未做全树 mtime 扫描，也未逐文件与历史 sha 基线比对（'改了又把 mtime 改回去'这类反证不在我的证据范围内）。",
    "`runs/**` 与 `.workspace/mario` 的'未动'由**摘要 + 最新 mtime** 支撑（二者都不被外层跟踪）；摘要口径自证通过，但它不能排除'同长度同内容的替换'（摘要为内容哈希，实际等价于内容未变，故此项风险很低）。"
  ]
}
```

---

## 2. 逐项核对表（命令 + 退出码）

| # | 核对项 | 我的命令（要点） | 结果 | 判定 |
|---|---|---|---|---|
| 1 | 先刻画（复现统计真实性） | `git rev-parse '0f78bb0^:tests/endpoint_liveness.rs'`；仓外重建 + 直跑 120 次 | blob = `2e5b95c7…`；**2/120 失败（1.67%）**，逐字见 §3.2 | ✅ |
| 2 | 定因（机制 + file:line） | 读 `tests/endpoint_liveness.rs:63-65/74/77-82/132-140`；`probe.rs` 确定性两向 | 非阻塞 listener 的 accept 继承非阻塞；read 立即 `WouldBlock(10035)` | ✅ |
| 3 | 测试竞态 vs 产品缺陷 | `grep -rn set_nonblocking src/`；`mcp.rs:190-209`；`McpChannel::new(...,5,0)` | 产品 0 命中；每次新建 agent；该测试 retries=0 ⇒ **测试竞态** | ✅ |
| 4 | 修因 vs 修症状（无 sleep/重试/放宽） | `git show 0f78bb0 --stat`；`git show 0f78bb0 -- tests/endpoint_liveness.rs` | `1 file changed, 12 insertions(+)`，仅一句 `set_nonblocking(false)`；2ms 退避是 context；测试体未改 | ✅ |
| 5 | 重复运行证据（≥10 次全量逐次 + 我抽 3 次） | `.dr60/full_runs/summary.txt`（10 行 exit=0）；我 `cargo test --offline` × 3 | 十份日志各 372/0/7、md5 两两不同、0 命中 FAILED；我 3 次 = exit 0/372/0/7 | ✅ |
| 6 | 非空洞性（确定性触发 / 频率披露） | `cat .dr60/probe_deterministic.log`；我 `probe.rs` 两向 | 旧形状 `WouldBlock(10035)`、新形状读到请求；报告明说 1200 次未跑完 | ✅（引文有误见 DEF-2） |
| 7 | 套件 | 我 3 次 `cargo test --offline`，`grep -oE 'test result: ok\. [0-9]+ passed' \| awk` | exit 0；372 passed / 0 failed / 7 ignored | ✅ |
| 8 | `ignored` 未增长、无测试删/弱化 | `git grep -n '#[ignore'` 于 `0f78bb0^` 与 `HEAD`；`git diff ef74c60..HEAD -- tests src Cargo.*` | 8 行 vs 8 行（7 属性 + 1 注释）；唯一改动 = 测试文件 +12 | ✅ |
| 9 | 禁区：`.workspace/mario` / `runs` | 我重建的 `digest.ps1`（PS `Sort-Object` 口径），自证 `smoke-t6` | `4e494547…`（259 文件）/ `01ff775e…`（5147 文件），与历史逐字一致 | ✅ |
| 10 | 禁区：PRD / Cargo / stage / push | `sha256sum`；`git diff … Cargo.*`；`git diff --cached --stat`；`git rev-parse origin/master` | `4c81c3a9…`；空；空；`26609a8…`（未 push） | ✅ |
| 11 | 引擎树（嵌套仓证明，非外层 diff） | `git ls-files godot-mcp`；`git ls-files godot-mcp/godot`；`git -C godot-mcp/godot status --porcelain -uno/-uall`；嵌套 `rev-parse HEAD` | 6484（真命中）/ 0（外层空判）/ 0 行 / 0 行 / `fc63af77c3…` | ✅ |
| 12 | `.dr60/` 清理或忽略 | `git status --porcelain`；`git check-ignore -v .dr60`；`grep -n dr60 .gitignore` | `?? .dr60/`；未忽略；无规则（61 文件 / 618 KB） | ❌ **DEF-1** |
| 13 | 诚实性（逐条声明核实） | 见 §1 的 HONESTY | 无伪造；三条引文/措辞缺陷 | ✅（DEF-2/3/4） |

---

## 3. 我自己的复现统计

**机器状态**：Windows 11 Pro，build 26100，16 逻辑处理器；`rustc 1.98.0 (88d9e12ae 2026-08-18)`、`cargo 1.98.0`。
运行方式：**直接运行已构建的测试可执行文件**（不经 cargo，避免构建噪声）；每次串行；cwd = `F:\moonbit-hof-rs`；输出逐次落盘。

### 3.1 修后（HEAD 源码）直跑 60 次

- 二进制：`target/debug/deps/endpoint_liveness-d8e3fbf20bc74977.exe`（`cargo test --offline --test endpoint_liveness --no-run` 报 `Finished ... in 0.46s` **未重编** ⇒ 与 HEAD 源码一致；也是十条全量日志里引用的那一个）。
- 结果：**60/60 `exit=0`**，每份 `test result: ok. 7 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out`（耗时 4.04-4.21s，总 255 秒）；`grep -lE 'FAILED|panicked'` = **无匹配**。
- 逐次记录：`F:\dr60-acc\summary.txt`（60 行）+ `run01.log … run60.log`。

### 3.2 修前（`0f78bb0^` 的测试文件）直跑 120 次 —— 独立复现 flake

- 构建：仓外 `F:\dr60-prefix`，`cp` 了 HEAD 的 `src tests config python tools Cargo.toml Cargo.lock`，再把 `git show '0f78bb0^:tests/endpoint_liveness.rs'` 写回；`git hash-object` = `2e5b95c7663d4786a8c91896aea2212bdcbec344` = `git rev-parse '0f78bb0^:tests/endpoint_liveness.rs'`（**逐字节等于修前 blob**）。`cargo test --offline --test endpoint_liveness --no-run` → `Finished ... in 35.78s`。
- 结果：**120 次 → 2 次失败（1.67%）**，均 `exit=101`，均为 `test result: FAILED. 6 passed; 1 failed; 0 ignored`；其余 118 次 `ok. 7 passed`。
  - 失败在 run=001、run=091（**单跑即发生**，进程内无其它 target/测试）。
- **逐字输出（run=001，os error 10054）**：

```
---- the_editor_endpoint_state_is_separate stdout ----

thread 'the_editor_endpoint_state_is_separate' (121928) panicked at tests\endpoint_liveness.rs:435:10:
the editor endpoint is alive: MCP transport failure to http://127.0.0.1:63621/mcp: http://127.0.0.1:63621/mcp: Network Error: 远程主机强迫关闭了一个现有的连接。 (os error 10054)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace


failures:
    the_editor_endpoint_state_is_separate

test result: FAILED. 6 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 4.11s
```

- **逐字输出（run=091，os error 10053）**：

```
---- the_editor_endpoint_state_is_separate stdout ----

thread 'the_editor_endpoint_state_is_separate' (109040) panicked at tests\endpoint_liveness.rs:435:10:
the editor endpoint is alive: MCP transport failure to http://127.0.0.1:60093/mcp: http://127.0.0.1:60093/mcp: Network Error: 你的主机中的软件中止了一个已建立的连接。 (os error 10053)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace


failures:
    the_editor_endpoint_state_is_separate

test result: FAILED. 6 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 4.07s
```

- 与基线对照：同 panic 行 `:435:10`，同 errno 家族 10053/10054，同"6 passed; 1 failed"。**两个 errno 都被我独立复现**。注意我这两次的文案**没有** `Error encountered in the status line` 前缀（见 DEF-4）。

### 3.3 独立 socket 探针（确定性两向 + 频率）

源：`F:\dr60-acc\probe.rs`（仅 `std`，`rustc -O probe.rs -o probe.exe`）。输出：

```
OLD_SHAPE first_read=Err(Os { code: 10035, kind: WouldBlock, message: "无法立即完成一个非阻止性套接字操作。" }) elapsed_ms=0 (client bytes were 300ms away)
FIXED_SHAPE first_read=Ok(18) frame="GET / HTTP/1.1\r\n\r\n" elapsed_ms=298
FREQUENCY_OLD iterations=300 would_block=0 ok=300
```

解读：**(1)** 从非阻塞 listener accept 出的 socket 在该 accept 后的首个 read 上立刻 `WouldBlock`（0ms，而客户端字节 300ms 后才写）⇒ 继承非阻塞成立，且这是**确定性**的，与 sleep 无关；**(2)** 加一句 `set_nonblocking(false)` 后 read 阻塞 298ms 并读到完整请求 ⇒ 修复方向在 socket 层有效；**(3)** 当客户端紧接着 connect 就写时，300/300 都读到数据 ⇒ 竞态窗口很窄，真实测试里约 2% 的失败来自 ureq 在 connect 与写之间更大的时间窗（与我的 1.67% 量级自洽）。

### 3.4 全量套件（我自己跑的 3 次）

`cargo test --offline`，串行，日志 `F:\dr60-acc\full\run1..3.log`：

| 我的一次 | exit | passed | failed | ignored | 秒 | panicked/FAILED/os 1005x |
|---|---|---|---|---|---|---|
| run1 | 0 | 372 | 0 | 7 | 454 | 0 |
| run2 | 0 | 372 | 0 | 7 | 452 | 0 |
| run3 | 0 | 372 | 0 | 7 | 452 | 0 |

三份日志 md5 互不相同（真实独立运行）。与基线 372/0/7 逐字一致。

---

## 4. 对"修因非修症状"的独立判定

**判定：修因（不是掩盖）。** 依据三条，互相独立：

1. **diff 本身**：12 行里只有一句功能性语句 `stream.set_nonblocking(false)`（+ 一个更响的 `.expect`），其余是文档注释。**没有**新 sleep、**没有**新重试、**没有**断言放宽；2ms 退避与测试函数体都在 diff 里以 **context** 出现。这条独立于任何运行结果即可排除"加长等待/重试换绿"。
2. **机制层**：我的探针证明修复消除的是**产生全部已知失败的那个分支**（非阻塞 read 立刻 `WouldBlock` → `Err(_) => return`）。修后 read 会阻塞直到请求到达，因此"替身是否应答"从调度器时序变成代码属性。
3. **对照实验**：同一台机器、同一 `src`/`Cargo`，只有**测试文件**一行为**修前** vs **修后**的差异：修前 2/120 失败（`:435:10`，10053/10054），修后 60/60 干净，3 次全量 372/0/7。（我说明这一条的证据强度：0/60 对 2/120 的 Fisher 单侧 p≈0.44，**单靠 A/B 不显著**；决定性的是 (1)+(2)，A/B 是支持性证据。）

实现者没有用 `#[ignore]` 真机门控（`ignored` 保持 7，`#[ignore]` 行数 8 vs 8 未变），它给出的理由（"缺陷来自测试自己选的模式标志，离线可复现可消除"）与我的证据一致。

---

## 5. 对"因果 vs 频率假设"的独立判定

**判定：实现者给出的是可观测的机制，并且我独立复现了该机制；其对'因果'的语言基本站得住，但有两处需要降级。**

- **站得住的部分**：机制有 file:line（修前 `:57-59` 非阻塞 listener → `:68-69` accept 继承 → `:124-128` 首个 read → `:127` 放弃；修后 `:63-65 / :74 / :80-82 / :132 / :136-140 / :139`）；该机制**可被我观测**（`probe.rs` 两向确定性复现，且 `elapsed_ms=0` vs `298` 排除了"只是慢"）；它还把 D246 的旧假设（替身写完即 drop 造成 RST）**正确地证伪**——证据是替身根本没读到请求（`would_block=1 read_error=0`），我的失败复现也显示客户端确实没拿到任何应答。
- **需要降级的（DEF-2）**：修前那条探针记录（`iterations=1200`，`served=1 would_block=1`，iter 37/80/100）**没有保留的原始件**，报告 §1.3 还把它错引到 `.dr60/probe_editor_double.log`（该文件其实是修后 `iterations=300 / failures=0`）。因此该条应表述为"**报告文本叙述的测量 + 我独立复现的机制**"，不能当作可核对的原始日志。
- **需要降级的（DEF-4）**：把客户端症状固定写成"status line 读取失败"过强；我的两次失败没有该前缀，说明同一服务端行为可在写或读的任一点被观察到。
- **频率没有被冒充为因果**：实现者明说'1200 次未跑完'（§8.3）、给出置信区间（§7.5），并**另外**构造了确定性触发（§5）——这正是简报要求的非空洞性做法。我的独立测量（2/120）与其 65 次/2 次、调度者 111 次/2 次同量级，说明其刻画统计**不是伪造**。

---

## 6. 未验证项与理由

1. 实现者探针（`tests/dr60_probe.rs`）本身未入库且已删（`git ls-files | grep dr60` 只有三份 .md），我无法复跑其 300 次/1200 次迭代的原始运行；我只能复现其**机制**（我自己写了等价探针）。理由：原件不在仓内，且简报禁止我改仓内文件做植入。
2. 另两处同形替身（`dual_endpoint.rs`、`endpoint_request_count.rs`）是否真会 flake：我**只核对代码形状**（listener 非阻塞、accept 后不复位、读路径对 `WouldBlock` 的处理与 ScriptedMcp 同类），未实测。理由：属于 DR-65 的范围，且实测需要长时间直跑。
3. 高负载/争用条件下的行为：我的测量全部串行无争用。理由：要与实现者的 3.1% 保持可比，争用会污染频率口径。
4. 引擎树的全树 mtime/逐文件 sha 基线：未做；我用的是嵌套仓 `status`（tracked+untracked 均为 0 行）+ 嵌套 HEAD + 15049 个受跟踪文件的计数 + 外层 pathspec 真命中证明。理由：嵌套 `status --porcelain -uall` = 0 行已是最强的"未改"证据，mtime 扫描在 4.7 GB 树上成本高且信息量低。

## 7. 我没有独立复核的部分

- `.dr60/**` 内部日志是**实现者一次运行留下的工件**，我可以核对它们的内部一致性与可复算性（十份全量日志我逐份求和、md5 去重、逐份引用同一二进制；两次失败记录与 panic 文本齐备），但我无法证明"这些文件确实是当时那台机器上那次运行产生的"——这属于所有日志类证据的固有边界。
- 调度者在 D255 中记录的处置计划（迁移 `.dr60/` 到 `.spec/hof-rs/tasks/dr60-evidence/`）**尚未执行**，我只记录该计划存在，不评价其未来执行。
- 验收期间调度者仍在向 master 追加纯文档提交（`a2baafb`、`836ad54`）。我按"代码树"口径判定：`git diff 26609a8..HEAD -- src tests Cargo.toml Cargo.lock` 只有那 12 行。我未逐字读这两个文档提交的内容（与本验收判据无关）。

## 8. 给下一批的建议（**我没有改任何代码**）

1. **收尾 DEF-1**：按 D255 执行迁移（`.dr60/` → 受控位置）或至少补一条 `.gitignore` 规则；不要用宽口径 `git add -A` 把它带进历史。
2. **修 DEF-2 的证据台账**：在 REPORT 里把 §1.3 的修前探针引文改为"报告文本记录（原始件未留存）"，或补存该次运行的原始日志；REFERENCE 类的引文指针必须指向真正含该内容的文件。
3. **DR-65 落地时顺带实测**：给 `dual_endpoint.rs` / `endpoint_request_count.rs` 的替身加同一句模式声明后，用**同样的直跑口径**（直接跑 target 可执行文件 ≥100 次）验证它们此前是否也会 flake；若测不出，就明确写"机制相同但频率未测"。
4. **可选硬化（不属本批）**：`serve` 的 `Err(_) => return` 可在未来改成把 socket 错误打进 panic/日志，使"真实 reset"不再静默；若做，需同时给出非空洞性证据。
5. **给后续验收者的口径**：`rev^` 类查询一律在 **bash** 做（本报告所有 `0f78bb0^` / `ef74c60..HEAD` 查询都在 bash，避开了 cmd 的 caret 陷阱）；引擎树判定一律用**嵌套仓**，外层 `git diff` 对引擎树是空判。
