# TASK-DR48-ACCEPT — 修复包（DR-48..DR-53）独立验收任务书

> 你是**独立验收子代理**。不得继承实现者或调度者的结论。
> 只读：`F:\moonbit-hof-rs`。实现者报告：`.spec/hof-rs/tasks/TASK-DR48-REPORT.md`（**线索，非证据**）。
> **离线批**：**不得**启动 Godot、**不得**碰 9877 或任何端口、不联网、不调模型
> （9877 上有我们的编辑器 PID 108432，**绝不许动**）。
> 你唯一的产物是报告 `.spec/hof-rs/tasks/TASK-DR48-ACCEPTANCE.md`。

---

## 1. 先读

`.spec/hof-rs/DESIGN-DETAIL.md` **§14**（DR-48..DR-53 的规范条款）→ `DECISIONS.md` **D221**、**D222**
（D222 含 DR-50 的定性与裁决）→ `.spec/hof-rs/tasks/TASK-DR48-FIX.md`（实现者的判据）
→ `.spec/hof-rs/tasks/TASK-DR48-REPORT.md`（自述）→ `.spec/hof-rs/tasks/TASK-DR47-ACCEPTANCE.md`（上一批的取证）
→ `godot-mcp/recovery/TEST-CASES.md`（177 条 `TC-TOOL-*`，DR-52 的基准）。

## 2. 核心复核项（逐条自己复现，报告里给命令+原始输出+文件:行）

1. **自己跑** `cargo test --offline`：贴真实尾部与退出码；核对 `passed=328 / failed=0 / ignored=7` 是否属实，
   并确认那 7 条 ignored 仍是**既有**的 `tests/godot_smoke.rs` 真机门控（**未**被新增/扩大）。
2. **更新的既有断言**（报告 §5）：逐条判"是否真的语义等价"。**任何放宽 ⇒ 判 fail。**
3. **DR-48**：①把豁免做成**常量数据 + 具名匹配函数**（不是特例 `if`，更不是 `[MCP]` 前缀）；
   ②**非空洞性（头号目标）**：用受控实验证明反例测试**真的会红**——例如临时令匹配函数恒真
   （或注入一条真实 `ERROR:`）。**若注入真 `ERROR:` 后闸门不再失败 ⇒ 判 fail**；
   ③确认引擎那条**真错误**行（`ERROR: [MCP] SceneTree never became available…`）**不**被豁免。
4. **DR-49**：①调用形态不再传文件系统路径；②**调用前作废既有文件**；
   ③`ok` 基于**新鲜度**而非 `is_file()` —— **构造反例**：在目标路径预置一个旧文件，断言步骤**不**判成功；
   ④旧文件**不再**压制 `capture_frames` 回退。
5. **DR-51**：`editor_status` 由真实 `GET /mcp` 填充（失败→`null`+reason）；`game_endpoint` 在**登记当刻**回写。
   构造"有端点/无端点"两种路径的测试证据。确认 `{}`→`null` 的收紧未破坏任何消费者。
6. **DR-52**：①诊断文本与自己的原始记录一致（InputMap 那处矛盾已消）；
   ②**抽样 ≥12 条**（含 hof-rs 真正调用的每个游戏态工具 + 至少 3 条编辑器态）独立核对参数形状，
   并**自己**在 `TEST-CASES.md` 里找依据（不要只用实现者的表）。
7. **DR-53**：畸形 `enabled=` **不改文件**（受控实验：两种畸形写法各跑一次，断言字节不变）；
   两条回归测试确在且**非空洞**；过期测试名已改且断言已收紧。
8. **DR-50 的定性链条（基于 `runs/smoke-t6` 原始文件独立复算，这是本批最重要的一条）**：
   ①第 5 次调用确实是**第一条编译不过**的 code？②失败确在**传输层**（`10060` 状态行缺失）？
   ③随后监听**消失**（`10061`）？④**编辑器端点**同轮确实全程健康？⑤两轮端口/pid 是否如报告所列？
   ⑥**`godot-mcp/**` 是否真的一个字节未改**（`git log`/`git diff` 对 `4d3ff58..HEAD`）？
   ⇒ 你的结论可以是"支持引擎侧"、"证据不足"或"定性错误"，**必须给出你自己的依据与置信度**。
9. **禁令自查**：`runs/smoke-t6/**` 是否**逐字节未变**（自己算目录摘要）；
   `PRD-mario.md` sha256 是否仍为 `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`；
   `Cargo.toml`/`Cargo.lock` 在 `4d3ff58..HEAD` 是否无 diff；是否未 push（`origin/master` 应仍为 `4b9bd44`）；
   是否未 stage `runs/**`、`.workspace/**`、`config/*.secret*`。

## 3. 纪律

只读；**不** `git commit`/`push`/stage；不改 `src/**`、`tests/**`、`config/**`、`godot-mcp/**`、
`.spec/hof-rs/PRD-mario.md`、`runs/smoke-t6/**`。**唯一**允许的受控改动是 §2.3/§2.4/§2.7 要求的
**植入-回退**实验（改后必须 `git checkout --` 回退，并用 `git status --porcelain` 与 `git diff --stat` 双空
证明已恢复；注意仓内 `core.autocrlf=true`，回退后请核对字节与 HEAD blob 一致）。
不联网、不调模型、不启动任何进程、不碰端口。不打印密钥。

## 4. 结构化结论（写进报告 §1）

```json
{ "verdict": "pass" | "fail",
  "criteria": [ { "id": "DR-48|DR-49|DR-50A|DR-50B.characterisation|DR-51|DR-52|DR-53|GUARDS",
                  "pass": true, "evidence": "命令 + 真实输出 + 文件:行" } ],
  "defects": [ { "id": "DEF-X", "severity": "blocker|major|minor|info", "what": "...", "reproduction": "..." } ],
  "risks": [ "..." ], "unverified": [ "..." ] }
```

`verdict=fail` 门槛：存在 blocker/major、任何既有断言被放宽、任何反例测试**空洞**、
DR-50 定性被推翻、或原始工件被动过。

## 5. 报告必含小节

1. 结构化结论 + 真实命令与退出码；2. 逐项核对表；3. **反例清单**（你构造了什么、观测到什么、是否推翻）；
4. 对 DR-50 定性的独立结论与置信度；5. 未验证项与理由；6. 你没有独立复核的部分；
7. 若发现缺陷，给出**给下一批**的建议（**不要**自己改代码）。

**回报给父代理只有一行：报告文件路径。**
