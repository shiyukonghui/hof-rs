# TASK-DR57-REPORT — 补"零请求"的**计数**测试 + 更正 §15 报告的证据陈述 + 处置 DEF-2

- 任务书：`.spec/hof-rs/tasks/TASK-DR57.md`
- 输入：`.spec/hof-rs/tasks/TASK-DR54-ACCEPTANCE.md`（DEF-1/DEF-2 的原始论证）、`DESIGN-DETAIL.md` §15、
  `DECISIONS.md` D238/D239/D242、`.spec/hof-rs/tasks/TASK-DR54-REPORT.md`（被更正者）
- 批次起点：`ba32de65aca8d12cfcc3eac6b31d53b059fe2da1`（`master`，当时 `origin/master` 同点）
- **离线批次**：未启动 Godot、未碰任何引擎端口、未联网、未调模型端点（全部 endpoint 都是进程内
  `TcpListener::bind("127.0.0.1:0")` 的内核临时环回端口）
- 本批**不断言** E3 已 met；E3 只能由真机 T=1 判定（与 D238/D239 一致）

---

## 1. 结论 + 真实门输出

**三件事全部完成，且都带可复现证据：**

| # | 交付 | 状态 |
|---|---|---|
| 1 | 补一条**在传输层真计数**的测试 | **完成**：`tests/endpoint_request_count.rs::a_dead_endpoint_sends_zero_requests_to_the_transport_layer`，原始树绿；两类反例（判死后仍发一次 / 判死短路整段删除）**都转红**，且都逐字节回退 |
| 2 | 更正 `TASK-DR54-REPORT.md` §3.2 的证据陈述 | **完成**：原文引述 + 新文引述 + 原推理为何无效 + 指向新测试（§4） |
| 3 | 处置 DEF-2（`InputChannelProbe.has_action`） | **完成**：**删除**该字段及其产生代码，并加文档注释防复发（§5） |

**门（真实输出）**

基线（改动前，`ba32de6`，`cargo test --offline`）：

```
targets=36  AGGREGATE passed=352 failed=0 ignored=7
大写 FAILED / panicked / error[ 行数 = 0
EXIT=0
```

> 口径说明：352 是 **36 个 `test result:` 行的 passed 之和**（含 lib 单测 104 条、集成测试与
> doc-tests 0 条），ignored 恰为 **7**，全部来自 `tests/godot_smoke.rs`；本批**未新增任何 `#[ignore]`**，
> 该文件也**零改动**。

<!-- SUITE_FINAL -->
**`targets=37  AGGREGATE passed=353 failed=0 ignored=7`，`EXIT=0`。** 这一结果在批次收尾时**连续复跑 3 次
全部一致**（`run1/run2/run3` 均 `EXIT=0 passed=353 failed=0 ignored=7`），另有一次 `EXIT=0 passed=353
failed=0 ignored=7`（DEF-2 改动后）。相对基线：**+1 passed，正是新增的那一条测试**；`failed` 仍为 0、
`ignored` 仍为 **7**（**未增加**）；target 数 36 → 37（新增 `tests/endpoint_request_count.rs` 一个 target）。

**真实尾部**（最后一次全量复跑，逐字）：

```
running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

   Doc-tests hof_rs

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

EXIT=0
```

> 注（诚实项）：批次收尾前的**一次**全量复跑曾出现 1 条 flake 失败（详情与逐字输出见 §8.1）；
> 该 target 单独连跑 3 次与随后 3 次全量复跑均全绿。§8.1 把它作为**既有风险**如实保留，未通过改测试掩盖。

本批结束后（`cargo test --offline`，逐 target 汇总结束）：
**提交（7 个本地提交，英文信息带 `(DR-57)`，未 push）**

| commit | 内容 |
|---|---|
| `440fc89` | 新增计数测试 |
| `05efd7f` | 收敛非空洞性实验脚本 |
| `580b86c` | 修脚本与 CRLF 工作树的针脚匹配 |
| `ae7a45e` | 让反例 B 真正删掉整段短路（保证植入树可编译） |
| `23304a1` | 删除死字段 `InputChannelProbe.has_action`（DEF-2） |
| `c1586e1` | 更正 `TASK-DR54-REPORT.md` 的循环论证证据陈述 |
| `f4f18cb` | 把实验脚本归档到 `.spec/hof-rs/tasks/` |

**本批净改动**（`git diff --stat ba32de6..HEAD` 的口径是"自批次起点以来的全部提交"，其中
`afb649a` 是**上游编排者**在我工作期间提交的 DR-59 文档、**不是**本批产物；除此之外本批 4 个文件）：

```
 afb649a docs(spec): open DR-59 - isolate the deterministic evidence area per round…   (上游提交，非本批)
 .spec/hof-rs/tasks/TASK-DR54-REPORT.md |  11 +-
 .spec/hof-rs/tasks/dr57-plants.ps1     | 116 ++++++++++
 src/adapter/godot.rs                   |  12 +-
 tests/endpoint_request_count.rs        | 376 +++++++++++++++++++++++++++++++++
```

（上表 file 行即 `git diff --stat ba32de6..HEAD` 的 4 个文件；`afb649a` 由编排者在共享分支上产生，
本报告只标记其归属，不改写、不 cherry-pick。）

---

## 2. 新测试：名字、计数在哪一层、为什么**不循环**

**测试**：`tests/endpoint_request_count.rs::a_dead_endpoint_sends_zero_requests_to_the_transport_layer`

**计数挂在哪一层（任务书的核心要求）**：挂在**独立 loopback 替身的 accept 路径**上，即
`TcpListener::accept()` 返回连接后**第一件事**就是 `accepted.fetch_add(1)`（`tests/endpoint_request_count.rs`
的 `CountingJsonRpc` 线程体）。这一层：

- 在 `McpChannel::call_with_meta` **之下**（那是 app 层）；
- 在 DR-55 的 `if liveness.unavailable { return ... }` **之下**（那条 `return` 根本到不了 socket）；
- 在 `McpClient::post` **之下**（`post` 要建立 TCP 连接才可能被 accept 到）。

**为什么这不循环论证**：DR-55 的判死短路发生在 socket **之前**，所以"判死后计次不增"这个量不是由
被短路的那段代码产生的——**连接只可能由一次真实的 HTTP 尝试产生**。旧测试的问题恰恰相反：它用
**已关闭端口**（`a_closed_loopback_endpoint()`）当对偶，而"连接被拒"这件事本身**无法被计数**，
于是它只能退回去读 `consecutive_transport_failures`——而那正是被 `observe` 的早退**在构造上冻结**的量。

**测试的形状（三段）**：

1. **判死**：替身切到 `Mode::DropWithoutAnswering`（收下连接、一个字节不回，复现 `smoke-t6` 的"状态行
   没来"形态），两次 `max_retries = 0` 的调用产生两次**真实传输失败**，端点判死。
2. **测量**：替身切成**完全健康**（`Mode::Answer`，会真的回 `{"result":…}`）。三次 `max_retries = 3` 的
   调用必须仍被定型拒绝，且 **accept 计数纹丝不动**（实测 `5 == 5`）。若判死后仍有请求到达，
   健康替身会**成功应答**（调用不再 `Err`）且连接数 +1 —— 两个断言都会响。
3. **活对照**：`register_game_endpoint` 重新武装同一地址后，下一次调用必须**恰好 +1** 个连接，
   证明"零"来自判死裁决，而不是计数器坏了。

测试还内建了**自非空洞控制**：判死时刻断言 `accepted == 2` —— 计到 2 才说明这个计数器真的会动。

---

## 3. 非空洞性证据：植入 → 红（真实输出）→ 三法回退

脚本：`.spec/hof-rs/tasks/dr57-plants.ps1`（已入库，可复跑；运行前断言工作树完全干净，植入后**只跑
一条测试**，`finally` 式 `git checkout --` 回退，再核 blob）。原始日志在**仓库外**
`C:\Users\wyl\AppData\Local\Temp\dr57-plant\`（`A.txt` / `B.txt` / `run.txt` / `*.restore.txt`），
以免污染"工作树必须干净"的自证。**两处植入都在生产代码 `src/tools/mod.rs`，没有一处改测试。**

### 3.1 反例 A —— "**零重试但仍发一次**"（DEF-1 的正是这个反例）

植入：在判死短路 `return` **之前**插入一次真实的 `call_traced`（先把 game route 的 client clone
出锁再 await，避免持锁跨 await）：

```
        if let Some(liveness) = self.endpoint_state(&endpoint) {
            if liveness.unavailable {
                let _probe_tool = tool.to_string();
                let _probe_client = self
                    .game
                    .lock()
                    .ok()
                    .and_then(|guard| guard.as_ref().map(|route| route.client.clone()));
                if let Some(_probe_client) = _probe_client {
                    let _ = tokio::task::spawn_blocking(move || {
                        _probe_client.call_traced(&_probe_tool, serde_json::json!({}))
                    })
                    .await;
                }
                return Err(
                    endpoint::McpEndpointUnavailableError::new(liveness, tool).into(),
                );
            }
        }
```

植入后 blob `4b6934e1a56dd390195241f38280c745e75c6ba1` ≠ HEAD `ddf6f4e4de1080e02863e84295febf821772af1b`
（证明植入真的落盘）。**真实失败输出**（`A.txt`，逐字）：

```
running 1 test
test a_dead_endpoint_sends_zero_requests_to_the_transport_layer ... FAILED

---- a_dead_endpoint_sends_zero_requests_to_the_transport_layer stdout ----

thread 'a_dead_endpoint_sends_zero_requests_to_the_transport_layer' (120112) panicked at tests\endpoint_request_count.rs:345:5:
assertion `left == right` failed: ZERO requests may reach the transport layer after the endpoint is declared dead, but the live double accepted 3 new connection(s)
  left: 5
 right: 2

test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.02s
error: test failed, to rerun pass `--test endpoint_request_count`
EXIT=101
```

**读法（重要，防止把数字读错）**：`left` 是随后三次调用的**事后**总 accept 数（5），`right` 是
判死时刻的冻结值（2）。所以 A 的结论是"三次调用总共新开了 **3** 个连接"——即每次调用**恰好 1 个**
请求、且**每个请求都被 accept 到**。这与"零重试但发一次"**逐字一致**：`failure.attempts == 1`
（上层环没重试）在本反例下**仍然成立**，只有 accept 计数揭穿了那一发请求。

### 3.2 反例 B —— "判死后**什么都发**"（把短路整段删掉）

植入：把整个 `if let Some(liveness) … { … }` 块替换为 `let tool_name = tool.to_string();`。
植入后 blob `ee3600f4ce17bca9959421880789c9d659417bd1` ≠ HEAD。**真实失败输出**（`B.txt`，逐字）：

```
warning: unused variable: `tool_name`
   --> src\tools\mod.rs:279:13
...
running 1 test
test a_dead_endpoint_sends_zero_requests_to_the_transport_layer ... FAILED

---- a_dead_endpoint_sends_zero_requests_to_the_transport_layer stdout ----

thread 'a_dead_endpoint_sends_zero_requests_to_the_transport_layer' (121188) panicked at tests\endpoint_request_count.rs:330:14:
a dead endpoint stays dead, even with a healthy peer: Object {"tree": Object {"name": String("Main")}}

test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.01s
error: test failed, to rerun pass `--test endpoint_request_count`
EXIT=101
```

**读法**：这次请求真的**发出了并成功**（健康替身回了 `{"tree":{"name":"Main"}}`），于是"死端点必须
定型拒绝"这条断言先响。两类反例因此各有一个**语义不同**的红色：A 是计数响，B 是"死端点竟然答成了"。
两者都 `EXIT=101`。

### 3.3 三法回退证明（两次植入各自一份，逐字来自 `*.restore.txt`）

```
PLANT A
porcelain_empty=True
diffstat_empty=True
hash_object=ddf6f4e4de1080e02863e84295febf821772af1b
head_blob=ddf6f4e4de1080e02863e84295febf821772af1b
blob_equal=True
```

```
PLANT B
porcelain_empty=True
diffstat_empty=True
hash_object=ddf6f4e4de1080e02863e84295febf821772af1b
head_blob=ddf6f4e4de1080e02863e84295febf821772af1b
blob_equal=True
```

即：`git status --porcelain` **空**、`git diff --stat` **空**、`git hash-object src/tools/mod.rs`
**逐字节等于** `git rev-parse HEAD:src/tools/mod.rs`。脚本收尾后我另跑了一次完整 `git status --porcelain`
（**含 untracked**）= **完全空**（§7）。

**另记（诚实项）**：本批的植入与既有测试 `two_transport_failures_kill_the_endpoint_and_later_calls_do_not_retry`
**没有交集**——我没有为了"非空洞"去改那条既有测试，也没有放宽它（§7.5）。

---

## 4. 报告更正：原文 → 新文 → 为何原推理无效

被更正文件：`.spec/hof-rs/tasks/TASK-DR54-REPORT.md` §3.2。**这是更正，不是润色**：原文**逐字保留**在
更正块内（`<a id="dr57-correction">` 锚点），新文紧随其后，且不改动该节其它结论（判死转移、
首次失败不判死、业务错误不计入、重注册重新武装、端点各自独立、ready 轮询等原文一律原样保留）。

**原文（逐字引述，更正前）**：

> - **零重试的证据**：… 测试 `two_transport_failures_kill_the_endpoint_and_later_calls_do_not_retry`
>   用 **`max_retries = 3`** 调用三次，断言 `failure.attempts == 1` 且
>   `endpoint_state.consecutive_transport_failures` 仍为 2（**计数不再增长 ⇒ 确实没再发请求**）。

**新文（逐字引述，已落盘）**：

> - **零重试的证据**：… 用 **`max_retries = 3`** 调用三次，断言 `failure.attempts == 1`。
>   - **DR-57 更正（本条被独立验收 DEF-1 推翻，原文与更正都留在这里，不删改）：**
>     - **原文（本报告 §3.2 在 DR-57 之前的措辞，逐字引述）**：
>       > 断言 `failure.attempts == 1` 且 `endpoint_state.consecutive_transport_failures` 仍为 2
>       > （**计数不再增长 ⇒ 确实没再发请求**）。
>     - **更正后的措辞**：
>       > `failure.attempts == 1` 只证明这条调用**不再重试**。它**不**证明"没有发请求"：要证明零请求，
>       > 必须由**独立计数替身**在**传输层**（`McpClient::post` 真正建立 TCP 连接的那一层、也就是
>       > `EndpointLiveness` 判定**之前**）计次，并断言判死后该计次**不增**。本报告写作时没有这样的计数：
>       > `tests/endpoint_liveness.rs::two_transport_failures_kill_the_endpoint_and_later_calls_do_not_retry`
>       > 用的是**已关闭端口**的对偶，因此它**根本无法**数到请求。DR-57 新增的计数测试是
>       > `tests/endpoint_request_count.rs::a_dead_endpoint_sends_zero_requests_to_the_transport_layer`：
>       > 活的 loopback 替身在自己的 **accept 路径**上计次（先以"收下连接、一个字节不回"的形态制造两次
>       > 真实传输失败把端点判死，再把替身切成**完全健康**），随后三次调用断言 accept 计数**纹丝不动**
>       > （实测 5 == 5），并以"重注册后下一次调用恰好 +1"作为计数器的活对照。同一测试在"判死后仍发一次
>       > 请求"与"判死短路被整段删除"两种受控植入下都转红（`EXIT=101`，DR-57 报告 §3）。
>     - **原推理为何无效**：`EndpointLiveness::observe` 在 `unavailable` 时**第一行就 `return`**
>       （`src/tools/endpoint.rs` 的 `if self.unavailable { return; }`），而 `call_with_meta` 也只在 `Err`
>       分支里调用它。所以只要端点已判死，`consecutive_transport_failures` **在构造上被冻结在
>       `transport_failures_at_mark`**，与"之后是否仍发请求"完全无关——它是一个恒等式，不是一个观测。
>       用它推断因果是**循环论证**。独立验收者（`TASK-DR54-ACCEPTANCE.md` §3 实验 B）把"判死后仍发一次
>       请求"植入后，本条测试**仍然绿**，只有验收者自写的计数测试转红；行为本身是对的，缺的是
>       **证据有效性与覆盖**。

**原推理为何无效（第三遍，用最小代码路径说清）**：`call_with_meta` 在判死时**在 `spawn_blocking` 之前**
`return Err(...)`，因此 `observe_liveness` 在判死后的每次调用里都**根本不被调用**；即便被调用，
`observe` 的第一行 `if self.unavailable { return; }` 也会让它直接返回。两条路径都使
`consecutive_transport_failures` 恒定等于 `endpoint.transport_failures_at_mark`。所以
"计数不再增长"是**由代码结构保证的恒真命题**，它对"是否发了请求"没有任何鉴别力——
这正是独立验收者植入后旧测试仍绿的原因。

另：报告 §4.3 的 `channel.has_action == true` 行补了一句 DR-57 补记（指向 DEF-2 的删除），
**没有改动该行原有的"原断言/新断言/为什么"三列**。

---

## 5. DEF-2 处置：**删除** `InputChannelProbe.has_action`

**选择：删除**（选项②"保留但标注"被否决），改动落在 `src/adapter/godot.rs`：

1. 删掉结构体字段 `pub has_action: Option<bool>`；
2. 删掉唯一写入点 `has_action: None`（`step_input_channel_probe` 里的 `InputChannelProbe { … }`）；
3. 在结构体文档注释里写明**为什么删**与**不要再加回来**：该字段自语义迁移起恒为 `None`、全仓无读者，
   却仍被 `finish_with` 序列化进发布的原始证据 `.hoh/deterministic/raw/input_channel_probe.json` 的
   `channel.has_action`，在那里 `null` 会被证据消费者读成"该动作不存在"——而这个字段**从来不承载**
   这个结论。

**理由（为什么选删除而不是标注）**：

- **它没有任何读者**：`git grep -n "\.has_action" -- src tests` 在改动后只剩 `InputMap.has_action`
  这类**脚本字符串**与注释，没有任何字段读取点（DEF-2 的原始判定也是"全仓已无任何读者"）。
- **它进的是发布出去的证据**：保留一个恒 `null` 的选项字段，等价于让每个证据消费者永久面对一个
  只能靠文档解释的坑；删除后**歧义在源头消失**。
- **删它不会丢任何已采集事实**：已被采集的原始证据（如 `tests/fixtures/dr58/smoke_t7_input_channel_probe.json`、
  `runs/smoke-t7/**`）是**冻结的字节**，本批一个字都没动，因此历史记录仍然完整；
  变的是"**以后再生成的**证据不再带这个空槽"。
- **语义替代物已在场**：`pressed`（以及 `axis_before/axis_after/moved_while_pressed`）才是 DR-54 之后
  承载"注入是否被接受"的语义证据，报告 §4.3 也已记录旧断言 `has_action == true` 被换成 `pressed == true`。
- 有读者字段的语义**一律未动**（`capability`/`game_process_reachable`/`is_pressed_before`/`axis_*`/
  `pressed`/`moved_while_pressed`/`declared_in_project_godot`/`detail` 全部原样）。
  **顺带说明**：`is_pressed_before` 同样是恒 `None`、同样无读者，但任务书只点了 `has_action`，
  我**没有**擅自扩大到其它字段；它作为**未实现/无读者**的第二个实例记在 §8。

---

## 6. 其它"用观测推断因果"的段落清单

任务书要求：只更正 §3.2 那处，其它同类段落**列出**即可。我逐节扫过 `TASK-DR54-REPORT.md`，
按"证据强度"分三类列出（**只有第 1 类是本批已更正的那处**）：

**A. 已被本批更正的（循环/恒等式，1 处）**

1. §3.2 "零重试的证据"：`consecutive_transport_failures` 不再增长 ⇒ 没发请求。**已更正**（§4）。

**B. 由观测推结论，但结论本身另有独立证据支撑（未改，仅登记）**

2. §6 nv3 行：用 `endpoint_liveness` 的判死断言（"计数==2 且 unavailable"）判"阈值=2"被覆盖。这是
   **行为级**断言，且阈值正确性另有 §3.1 的常量与 `a_single_transport_failure_…` 双向覆盖，故**成立**；
   但同一节若被人拿去当"零请求"的证据就会重复 DEF-1 的错误，**注明"不可这样用"**。
3. §7 "未碰 `godot-mcp/**`：`git diff --stat … -- godot-mcp` 无输出"。**外层仓的这条证据对引擎树是空判**
   （`godot-mcp/godot/` 被 gitignore、是嵌套克隆），见 D242/DR-58 DEF-1。本批改用嵌套仓命令与新证据
   （§7.1），并**没有**去改 DR-54 报告里这条历史表述（属"存量降级"范畴，任务书未要求本批改）。
4. §6/§7 "全绿即无植入残留"：由"套件绿"推"树干净"。这条在**同一运行**里其实另有 `git status` 与 blob
   比对兜底，故成立；登记为"不要单独使用"。

**C. 明确只是推断、报告自己已标注（未改，仅登记）**

5. §8 "推断"清单 1–7（E3 未验证、引擎拒绝文面、`input_axis` 采样、`events` 形状、scenario 字段名、
   重试放大、`artifact_is_fresh` 不可达分支）——报告**自己**已写成"推断，不得当作已证"，**不是**把推断
   伪装成实测，无需更正。

**判定**：除 §3.2 外，我**没有**发现第二处"用被结构冻结的量推断因果"的**同类**错误；B 类两处是
"结论另有证据、但表述可被误用"，本批如实登记、未改（避免把一次更正扩大成对报告的整体重写）。

---

## 7. 禁区自查（真实输出）

### 7.1 引擎仓：用**嵌套仓**证明未改（D242 的硬纪律）

外层仓 `git ls-files godot-mcp` = **6484** 行（证明这个 pathspec **真的命中**，不是"不存在的 pathspec
静默返回空"的假绿陷阱）；外层 `git diff --stat 53f6f9d..HEAD -- godot-mcp` = **0 行**。
但**真正的证据是嵌套仓**（`godot-mcp/godot/` 被 `.gitignore:33` 忽略，外层 git 在那里跟踪 **0** 个文件，
所以外层 `git diff` 对引擎树是空判）：

```
nested_HEAD=fc63af77c33368c4a1bb839c95d19750554f63a3
nested_status_porcelain_uno_lines=0
nested_status_porcelain_all_lines=0
nested_log_top:  fc63af77c3 evid: fix a comment typo in the mcp029 guard block (TASK-154)
engine_source_mtime (running_game_test_execution.cpp): 2026-09-27 00:00:14
engine_source_sha256: ece4ae63d445719b662a6e9ad99ba80bebba3ea3c94468094c7e9cb820ddff3f
```

即：嵌套仓**工作树完全干净**（tracked 与 untracked 均为 0 行），HEAD 仍是我的批次起点之前的
`fc63af77c3`，`mcp_server` 关键源码文件 mtime 是 **2026-09-27 00:00:14**（远早于本批，
本批最早提交时间为 2026-09-29 17:56），且其 sha256 被记录以便后续轮次对照。

### 7.2 `runs/**` 未动

- 外层仓跟踪 `runs/**` 的文件数 = **0**（`runs/` 在 `.gitignore:12`）。故不能只靠 diff。
- `git status --porcelain --untracked-files=all -- runs` = **0 行**。
- `runs/smoke-t6`：**135** 文件、最新 mtime **2026-09-29 02:32:01**（与验收报告一致）；
  我按验收报告 §2 附注的**同一口径**重算目录摘要（递归枚举文件，`-Force` 含隐藏；相对路径 `\`→`/`
  转小写 + 字节数 + 小写 sha256，按路径升序、`\t` 连接三列、`\n` 连接、不加尾随换行、UTF-8 后取 SHA256）：
  `files=135 digest=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03`
  —— 与验收报告的 `c144ef32…7a9c03` **逐字一致**。
- `runs/smoke-t6/iter-1/candidate/.hoh/evidence/frame-00.png`：**4246 B**、
  sha256 `bef0936daba1b16a23e7b25bd1fc432d946afaaca6d7b0636fbeafc898b67ea2`（与 D223 记录一致）。
- **时序判据**（最直接）：`runs/**` 全域**最新** mtime = **2026-09-29 14:44:16**
  （`runs/smoke-t7-experiment/e5_hash_tree.json`，DR-58 的真机轮次产物）；
  本批第一个改动文件（`tests/endpoint_request_count.rs`）的 mtime = **2026-09-29 17:50:53**；
  `Get-ChildItem runs -Recurse -File -Force | Where mtime > 我的首个文件` = **0**。
- `runs` 全域摘要（同一算法，仅为记账，**无历史基线可比**）：`files=5147 digest=01ff775e36935d3d92dab6919fe030389a8ff53483c52e87288ad711ec840dc3`
  （验收报告当时是 4970 文件 / `c6d6f4ec…`；差额来自 DR-58 的 `runs/smoke-t7*` 轮次，**不是**本批）。

### 7.3 PRD 未变

```
PRD_sha256=4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a
```

与 D223 与 DR-54 报告记录的值**逐字一致**；本批的 `git diff --stat ba32de6..HEAD` 也不含
`.spec/hof-rs/PRD-mario.md`。

### 7.4 无新依赖

```
cargo_diff_53f6f9d_HEAD_lines=0        (git diff --stat 53f6f9d..HEAD -- Cargo.toml Cargo.lock)
cargo_diff_worktree_lines=0            (git diff --stat HEAD -- Cargo.toml Cargo.lock)
```

新测试只用了 std 与仓内已有依赖（`serde_json`、`tokio`、`hof_rs`），**未加任何依赖**。

### 7.5 未 push、未 stage、未放宽/删除任何既有测试

```
origin_master=ba32de65aca8d12cfcc3eac6b31d53b059fe2da1
HEAD=c1586e1…（推送状态检查时）
ahead_of_origin=6
staged_diff_stat_lines=0
```

- **我从未执行 `git push`**（本子代理全程没有 push 命令）。本地领先 6 个提交（后为 7 个，含脚本归档）。
- `git diff --stat ba32de6..HEAD` 的 4 个文件里**没有** `tests/endpoint_liveness.rs`、`tests/evidence_battery.rs`、
  `tests/godot_smoke.rs`、`tests/mcp_reliability.rs` 的任何改动 ⇒ **没有任何既有测试被改动、放宽或删除**。
  我对 `tests/**` 的**唯一**改动是**新增** `tests/endpoint_request_count.rs`（376 行纯新增）。
- `#[ignore]` 标注数：`tests/godot_smoke.rs` 内 **7** 个 `#[ignore]`（文件零改动），套件实跑 `ignored=7`
  —— **未增加**。

### 7.6 离线与"不碰端口"

- 未启动 Godot（全程没有 `godot.windows.editor*` 进程命令）；未连接 9877 或任何引擎端口；
  `cargo test --offline`（**没有**任何联网）；未调用任何模型端点。
- 本批所有网络活动都是**进程内** `TcpListener::bind("127.0.0.1:0")` 的内核临时环回端口：
  既有 `endpoint_liveness` 的双、我的 `CountingJsonRpc`、以及 `a_closed_loopback_endpoint()` 那种
  "bind 后立刻 drop"的关闭端口。**从未**主动 connect/探测任何固定端口。

### 7.7 工作树最终状态

`git status --porcelain`（**含 untracked**）= **完全空**；`git diff --stat` = 空；
`git diff --cached --stat` = 空。所有实验日志都写在仓库外的 `%TEMP%\dr57-plant\`。

---

## 8. 遗留风险与未验证项

1. **`tests/endpoint_liveness.rs::the_editor_endpoint_state_is_separate` 出现一次真实 flake（未修，据实登记）。**
   本批最终全量复跑中出现过 **1 次**失败：`panicked at tests\endpoint_liveness.rs:435:10: the editor
   endpoint is alive: MCP transport failure to http://127.0.0.1:54952/mcp: … Network Error: 你的主机中的
   软件中止了一个已建立的连接。 (os error 10053)`，该次 `endpoint_liveness` 为 `6 passed; 1 failed`。
   该测试文件我**零改动**；把该 target **单独连跑 3 次全部 `7 passed`**，随后**全量套件连续复跑 3 次
   全部 `EXIT=0 / 353 passed / 0 failed / 7 ignored`**（§1）。出现频率：本批全量套件共跑 **6 次**
   （1 次基线 + 1 次 DEF-2 后 + 1 次收尾 + 3 次复跑），**仅 1 次**命中该 flake。这属于**既有替身
   `ScriptedMcp` 的时序敏感**问题（验收报告 §7 也记过"实现者那次首跑 exit 1 flake 未复现"，
   并指出全仓唯一挂钟敏感断言在 `endpoint_liveness.rs:498`）。
   **本批不修它**：它不在本任务书范围内，且改动既有测试文件与"不得改既有测试"的边界冲突；
   我把它记为**必须由下一批单独处置的 flake**，并给出这次的**逐字**失败文本以便定位。
2. **测试替身仍是"裸 HTTP/1.1"手写实现**：`CountingJsonRpc` 只解析 `Content-Length` 与 `id`，
   不模拟分块编码/keep-alive。对"计数连接"这一目的足够，但若将来要复用为通用替身需补。
3. **计数口径是"连接"而不是"HTTP 请求"**：本设计的客户端每个 attempt 新建一个连接
   （`ureq` agent 每次 attempt 重建，且响应带 `Connection: close`），所以 1 连接 = 1 请求。
   若将来客户端改为连接复用，这个测试会**变得松弛**（计的是连接数，不是请求数）。
   **这是本测试唯一的形态假设**，我在此明写，避免后人误以为它天然等价。
4. **`is_pressed_before` 是同一个 DEF-2 形态的第二个实例**（恒 `None`、无读者、仍进原始证据）。
   任务书只点了 `has_action`，我**未擅自扩大**；建议下一批按同一判据一并处置。
5. **引擎侧三项形态假设仍未验证**（ACTION_NOT_BOUND 的真实文面、`input_axis` 采样、`events` 形状），
   与 DR-54/DR-58 报告一致，**离线不可证**。
6. **E3 的 met/not_met 未被本批断言**（只能由真机 T=1 判定）；本批只补了"零请求"这一条证据的有效性。
7. **本批未重跑 DR-54 的 7 处历史植入**：我只验证了"本批新增的测试对 DEF-1 的两类反例有牙"，
   没有重新审计 DR-54 那批植入；那是验收报告已独立复核过的内容。

---

## 9. 诚实披露

1. **我的实验脚本改过三次才跑通**（第一版针脚没匹配 CRLF；第二版反例 B 删掉了开 `{` 却留着闭 `}`，
   导致植入树编译失败而不是断言失败；第三版才让两类反例都产生**断言级**红色）。
   前两次的失败**没有**被当作非空洞性证据，也不在任何提交的最终状态里；相关修订单独成提交
   （`580b86c`、`ae7a45e`），过程如实留在 `origin` 之外的本批提交历史里。
2. **反例 A 的红色数字要按"两次读数之差"读**（`left: 5` 是事后总数、`right: 2` 是判死时冻结值，
   差 3 = 三次调用各 1 个请求）。我在 §3.1 明写了读法，避免把这个数字误读成"3 次重试"。
3. **我遇到并据实登记了 1 次既有测试 flake**（§8.1），**没有**为了让套件变绿去改那条既有测试——
   那是任务书禁止的"放宽/删除既有测试换绿"。我的处理是：确认自己零改动该文件、单独复跑、记录逐字输出、
   并在多次全量复跑里区分"flake"与"回归"。
4. **`cargo test --offline` 的最终数字以本报告 §1 的 `<!-- SUITE_FINAL -->` 段落为准**（真实输出），
   我**没有**修改任何测试来凑数字：新增的 `+1` 只来自新增的那一条测试。
5. **本批未改 `DECISIONS.md`**（任务书明令属决策者工件）；本报告的结论是否入库由决策者裁决。
6. **本批未改 `.spec/hof-rs/PRD-mario.md`**，也未写 `runs/**`（§7.2/§7.3 有真实输出）。
7. **`godot-mcp` 的"未改"证据我严格按 D242 的口径给**（嵌套仓 `git -C godot-mcp/godot` + mtime/摘要），
   并在 §7.1 明写"外层 `git diff` 对引擎树是空判"这一方法论陷阱——包括对 DR-54 报告里那条历史表述的
   降级登记（§6 第 3 条）。
8. **本批次全程离线**：没有启动引擎、没有触碰引擎端口、没有联网、没有调用模型端点；所有 loopback
   都是内核临时端口（§7.6）。
