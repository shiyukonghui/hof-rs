# TASK-DR66-ACCEPT — E1 修复批的独立验收

> 你是**独立验收子代理**。不得继承实现者或调度者的结论。
> 判据：`.spec/hof-rs/tasks/TASK-DR66.md`、`.spec/hof-rs/tasks/TASK-DR64-REPORT.md`（根因）与 `TASK-DR64-ACCEPTANCE.md`。
> 实现者报告（**线索，非证据**）：`.spec/hof-rs/tasks/TASK-DR66-REPORT.md`。
> 批次：4 个 `(DR-66)` 提交，**未 push**。**离线批次**。产物：`.spec/hof-rs/tasks/TASK-DR66-ACCEPTANCE.md`。

## 1. 核心复核（自己复现，给命令 + 原始输出 + 文件:行）

1. **套件**：`cargo test --offline` 应 **exit 0 / 392 passed / 0 failed / 7 ignored**（基线 372/0/7）；
   `ignored` **未增**；**无既有测试被删/放宽**——**两条"永远绿"测试被改**（`artifact_hygiene.rs`、`developer_contract.rs`）
   与任何**替换**都必须**逐条**判定是**加强**还是**削弱**（它自报"加强"，**你要独立核**）。
2. **头号目标：假绿是否真的变红（这是本批的全部意义）**
   - 自己构造（或复用其夹具）**一次零工程增量的轮次**，断言 **`ok=false`、`failed_role=developer`、
     `warnings` 含 `no_engineering_write`、退出码非 0（=2）、`runs/<id>/exit_code` 与 `meta.json.exit_code` 一致**；
   - **自设植入**：①把门条件关掉；②把退出码层退回 `run_exit_code(gate)`。**两者都必须让目标测试红**；
     逐字节回退（**必须含 `cmp`**——该文件 CRLF 敏感，`hash-object` 单独不足以排除纯行尾变化）。
   - **若"只看 `ok`/退出码仍能漏报 E1"⇒ 判 fail。**
3. **它自报的收窄（诚实项，必须核）**：门只在**最后一次 Developer attempt `exit_was_limits=true`** 时触发
   ⇒ **正常结束但零增量的轮次仍不会红**（残余假绿面）。请**核实这一收窄是否真的存在**、
   并判断它**是否与既有离线夹具冲突**（它说拓宽会冲突）。**若收窄被说得比实际小（即实际更宽/更窄）⇒ 记缺陷。**
4. **shell 契约是否真打通**：`src/runtime/shell.rs` 的 `HOST` 平台判定；**从交付文本抽出命令、在真实
   `LocalEnvironment` 里执行**的测试；**宿主方言必须成功、外来方言必须（以 shell 自身方言错误）失败**；
   **控制组**是否真能排除"夹具坏了"这一解释。**自设**把 `HOST` 改回 `Posix` ⇒ 目标测试必须红。
   并核**非 Windows 分支只在编译期选择**这一未验证项是否被如实标注。
5. **完成定义降噪是否"未放宽"**：它声称 N1/N2、非空脚本规则、碰撞形状规则、实况自检路径**仍全在**，
   且增量要求**被保留并前置**。**逐条核**（含"`.hoh/**` 不算工程增量"是否与哈希排除集一致）。
6. **`e1_increment` 的排除集是否真来自运行时配置**（我在 DR-64 验收后转向的修正 1）——
   若它把排除集写死在测试里 ⇒ 记缺陷。
7. **历史改写的披露（我注意到的事）**：本批**尾提交哈希在实现期间多次变化**（我先后读到
   `e8a3d93`→`18bf417`→`cb50575`），说明它**改写了自己的本地（未推送）提交**。
   ⇒ 请核实：**报告是否披露了这一点**；`git reflog` 是否留下旧条目；
   **旧哈希是否已作废**；**当前 HEAD 的树是否就是报告描述的那棵树**。
   （未推送的改写不违规，但**必须披露**——若报告未提，记为缺陷。）
8. **构建缓存陷阱**：它报告 `git reset --mixed` 保留旧 mtime 导致 cargo 复用旧 rlib ⇒ **假红/假绿**，
   处置是 `touch` 后重编。请判断这**是否影响过它的任何一条结论**（尤其门与植入），并给结论。
9. **禁区**：`.workspace/mario`、`runs/**` 未动（**摘要口径须写明**并自证 `runs/smoke-t6` = `c144ef32…`）；
   `PRD-mario.md` sha 未变；Cargo 零 diff（**若它加了依赖，必须核实理由**）；**未 push**（`origin/master` 应仍 `079cf82`）、未 stage；
   **引擎树用嵌套仓**（D242）并证明 pathspec 真能命中；**仓内无临时物**。三个假绿陷阱各实测。

## 2. 纪律
只读为主；**唯一**允许的改动是 §1.2/§1.4 的受控植入（逐字节恢复 + **`cmp` 证明**）。
**离线**：不启动 Godot、不碰外部端口、不联网、不调模型。
不改 `.workspace/mario/**`、`runs/**`、`PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`；临时物**仓外**。
**不 push、不 stage、不改写历史**；**报告写完后不要再改**（我在你的完成消息之后才提交）。**不要修任何你发现的问题。**

## 3. 结构化结论（写进报告 §1）
```json
{ "verdict": "pass" | "fail",
  "criteria": [ { "id": "SUITE|FALSE_GREEN_NOW_RED|NARROWING_HONEST|SHELL_CONTRACT_REAL|DOD_NOT_RELAXED|EXCLUDES_FROM_CONFIG|HISTORY_REWRITE_DISCLOSED|BUILD_CACHE_IMPACT|GUARDS", "pass": true, "evidence": "命令 + 真实输出 + 文件:行" } ],
  "defects": [ { "id": "DEF-x", "severity": "blocker|major|minor|info", "what": "...", "reproduction": "..." } ],
  "risks": [ "..." ], "unverified": [ "..." ] }
```
`verdict=fail` 门槛：套件不绿/ignored 增、**"只看 ok/退出码仍能漏报 E1"**、两处植入不红、
shell 契约未真打通、完成定义被放宽、排除集写死、历史改写未披露、或禁区被动过。

## 4. 报告必含小节
1. 结构化结论 + 命令与输出；2. 逐项核对表；3. **你自己的植入与反例**（含 `cmp` 回退证据）；
4. 对"假绿已变红"的独立判定；5. 对"收窄披露是否诚实"的独立判定；6. 对"两条测试是加强"的逐条判定；
7. 未验证项与理由；8. 你没有独立复核的部分；9. 给下一批的建议（**不要**自己改代码）。

**回报给父代理只有一行：报告文件路径。**