# TASK-DR41-ACCEPT — 批次一（离线契约迁移）独立验收任务书

> 你是**独立验收子代理**。你不是实现者，**不得**继承实现者或调度者的任何结论。
> 你只看：需求、设计、代码、以及**你自己亲手复现**的证据。
> 落点：`F:\moonbit-hof-rs`（外层 git 仓，分支 `master`）。
> 实现者的报告在 `.spec/hof-rs/tasks/TASK-DR41-REPORT.md` —— **它可以作为线索，但不是证据**。
> 凡是报告里声称的结论，你都要自己复算一遍；报告与代码冲突时，**以代码与你的实测为准**。

---

## 0. 你的产出

1. 验收报告：`.spec/hof-rs/tasks/TASK-DR41-ACCEPTANCE.md`
2. 结构化结论（`agent(prompt, {schema})` 返回）：见 §5。

**纪律**：除 §3.7 明文授权的一次「植入-回退」受控实验外，**只读**不改仓；
不得 `git commit`、不得 `push`、不得 stage 任何文件；不得启动 Godot / 不得占用或探测任何端口 / 不得联网。

---

## 1. 先读（按顺序）

| 顺序 | 路径 | 读什么 |
|---|---|---|
| 1 | `.spec/hof-rs/DESIGN-DETAIL.md` **§13（文件末尾）** | 被验收的**权威条款** DR-41..DR-47 |
| 2 | `.spec/hof-rs/REQUIREMENTS.md` §3（C3/C4/C5）+ §10 | 需求侧硬约束与断层事实 |
| 3 | `DECISIONS.md` 末尾 **D216** | 决策、两条硬约束、自曝项 |
| 4 | `.spec/hof-rs/tasks/TASK-DR41-IMPL.md` | 实现者收到的任务书（判据原文） |
| 5 | `.spec/hof-rs/tasks/TASK-DR41-REPORT.md` | 实现者的自述（**线索，非证据**） |
| 6 | `godot-mcp/godot/modules/mcp_server/docs/{tool-rename-map.json,tools_list.renamed.json}` | 改名事实源 vs 新契约 |
| 7 | `godot-mcp/recovery/TEST-CASES.md` | 177 条 `TC-TOOL-*`（查语义变化） |

---

## 2. 验收立场（重要）

实现者**自己证明自己**不算通过。你的价值在于找**反例**与**空洞判据**。优先级从高到低：

1. **判据是不是空的**（vacuous）？例如"旧词汇归零"若扫描逻辑写错，恒绿就毫无意义。
   —— 这是本批**第一号反例目标**，见 §3.7。
2. **声称的改动是否真的落地**？（逐条对代码，不看报告措辞）
3. **是否有未声明的行为变更**？（`git log -p` 的两个提交逐条读；批量改名最容易夹带语义漂移）
4. **边界与错误路径**是否被覆盖？（幂等、缺失字段、不匹配、无对应能力）
5. 区分「**证据支持**」与「**推断**」：报告里凡没有原始输出支撑的结论，一律标为推断。

---

## 3. 逐条核对清单（每条都要给出你的**独立**证据）

### 3.1 DR-41（拆 GDExtension 通道）
- [ ] `PROJECT_GODOT` 模板不含 `[editor_plugins]`；`config/features` 为 `("4.8")`。
- [ ] `initialize()` 不再复制 addon、不再写 `ADDON_MISSING.txt`。
- [ ] **既有工作区**清理：自己造一个含 `addons/godot_mcp_rs/`、含 `.godot/extension_list.cfg`
      （**至少两行**，其中一行是 addon）与含**多插件** `enabled=PackedStringArray("res://other/plugin.cfg", "res://addons/godot_mcp_rs/plugin.cfg")`
      的临时工程，跑一遍初始化，断言：
      -(a) addon 目录被删；(b) `extension_list.cfg` 里 addon 行消失而**其它行逐字保留**；
      (c) 列表里**其它插件名逐字保留**；(d) 列表变空时整段移除的行为与设计一致；
      (e) **幂等**：再跑一次，文件**逐字节不变**（自己算 hash 对比，别信"应该没变"）。
- [ ] `grep -rn addon_source src tests config` → 0 命中（你自己跑）。
- [ ] 反向检查：清理逻辑**不得**误删 `addons/` 下的**其它**目录；不得删 `.godot/` 整个目录。

### 3.2 DR-42（契约换代）
- [ ] `tests/fixtures/mcp/tools_list.json` 条数 == **177**，每条 `name` 匹配 `^(editor|project|running_game|os)_[a-z0-9_]+$`。
- [ ] **形状未被破坏**：现有代码能解析它（跑相关测试即可），且 `inputSchema` 未被截断。
- [ ] 与 `tools_list.renamed.json` 做**名字集合**比对：差集必须为空（顺序无关）。
- [ ] 新增 `tests/fixtures/mcp/PROVENANCE.md` 存在，且其中记录的**落盘后 sha256** 与你自己算的一致。
- [ ] 从 rename map 中**抽样至少 10 条**（含 GDR-17 被拆分的工具、含被禁 `update_` 的改名），
      独立核对代码里的新旧名映射**与 map 一致**；抽样要写清你抽了哪 10 条。
- [ ] 全仓搜索**旧名集合**（无前缀名）：`src/**`、`tests/**`、`src/prompts/**` 必须 0 命中。
      **注意**：`godot-mcp/**` 与 `runs/**`、`.spec/**` 里的旧名**不算违规**（前者只读、后者是历史证据），
      报告里要写明你的扫描范围与排除理由。
- [ ] 角色作用域：自己构造断言——Planner 对**任一新契约写工具**必须 `false`；
      QA 对**任一新契约写工具**必须 `false`；Developer 对代表性写工具必须 `true`。
      （不要只看实现者写的用例名，自己跑。）

### 3.3 DR-43（双端点）
- [ ] 构造/使用双端点假 MCP：`running_game_*` 调用**只**出现在游戏端点；编辑器端点**从未**收到。
- [ ] `editor_play_scene` 响应**缺**端口信息时，该步**判定失败**（不是静默回退）。
- [ ] `stop_scene` 后 `running_game_*` **报错**，且**没有**向旧端口发出请求。
- [ ] 端点来源（`mcp_port_source`）被如实记录。

### 3.4 DR-44（引擎身份）
- [ ] `config/hoh.yaml` 有 `adapter.godot.editor_binary`，值为 mono 构建的绝对路径，且**该文件真实存在**。
- [ ] `hof doctor` 两项真实跑一次，贴原始输出（`godot.engine_binary` / `godot.engine_version`）。
- [ ] `meta.json` 的 `engine` 块**字段齐全**；缺失值必须 `null` **且**带 `reason`。
      自己构造一次"取不到"的情形验证（可用假 Environment）。
- [ ] `engine_identity` 闸门：匹配 → 过；不匹配 → **失败**且错误信息同列「配置的二进制 / 实际监听者路径 / PID」。
- [ ] **无新增 crate 依赖**：`git diff e8461bf..HEAD -- Cargo.toml Cargo.lock` 你亲自读。
- [ ] 密钥卫生：`engine` 新键不进任何密钥；相关测试覆盖了它。

### 3.5 DR-45（旧词汇归零的机器判据）
- [ ] `tests/tool_vocabulary.rs` 存在，三条判据都在，且 `cargo test` 里**真的被执行**（不是 `#[ignore]`）。
- [ ] **非空洞性（本批头号反例）**：见 §3.7。

### 3.6 全局
- [ ] 自己跑 `cargo test`，贴**真实输出尾部 + 退出码**；与报告数字不一致就如实指出。
- [ ] `sha256(.spec/hof-rs/PRD-mario.md)` == `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`。
- [ ] `godot-mcp/**` 未被改动：`git diff e8461bf..HEAD --stat -- godot-mcp/` 必须只含
      **本批不应涉及**的内容——若为 0 行最好；若有改动，逐条判定是否违规。
- [ ] `runs/**`、`.workspace/**`、`config/*.secret*` **未进任何提交**：自己查 `git log e8461bf..HEAD --name-only`。
- [ ] 提交边界：每条提交只含其 DR 相关的路径；提交信息带 DR 编号。

### 3.7 受控实验：证明"旧词汇归零"**不是恒绿**（唯一授权改仓的动作）

1. **植入**：在 `src/` 里**一处**植入一个旧名（例如把某个 `editor_*` 调用临时改回 `play_scene`，
   或加一行含旧名的注释/字符串——选最能代表"守卫想抓的形态"的那种）。
2. **只跑该守卫测试**：`cargo test --test tool_vocabulary`，**必须红**。贴真实输出。
3. **回退**：`git checkout -- <被改文件>`。
4. **证明已恢复**：`git status --porcelain` 为空 + `git diff --stat` 为空（贴原始输出）。
5. 若第 2 步**没有红** → 这是**重大缺陷**：守卫是空洞的，必须报 `fail`，并说明它能被什么绕过。
6. 若你发现守卫**会误报**（把非工具名的标识符当真），也报缺陷（误报同样有害）。

> 若这一步你因为任何原因做不了，**必须明说做不了**，并把 `DR-45 非空洞性` 标为「未验证」，
> **不得**默认它成立。

---

## 4. 反例构造的额外建议（至少做 2 条）

- 幂等性：对 §3.1 的临时工程连续初始化两次，第二次**零字节变化**。
- 缺字段：手改一份 `meta.json` 输入使某引擎字段取不到，验证写 `null`+`reason` 而非省略或编造。
- 版本串自由：验证 `godot.engine_version` **没有**把版本串硬编码成判据（C12）——
  例如替换一个假的 `editor_binary`（一个真实存在的、非 Godot 的可执行文件）看行为是否合理、
  是否仍能通过闸门（若它连 `--version` 失败却仍判 ok，是缺陷）。
- 端点污染：断言编辑器端点的**请求计数**不含任何 `running_game_*`。

---

## 5. 结构化结论（必须返回）

```json
{
  "verdict": "pass" | "fail",
  "criteria": [ { "id": "DR-41.1", "pass": true, "evidence": "命令 + 真实输出片段 + 文件:行号" } ],
  "defects": [ { "id": "DEF-1", "severity": "blocker|major|minor|info",
                 "what": "...", "reproduction": "...", "impact": "..." } ],
  "risks":   [ "..." ],
  "unverified": [ "..." ]
}
```

- `criteria` 要覆盖 §3 的每条清单项（含 §3.7）。`evidence` 必须是你**自己跑出来**的，不能抄报告。
- 任何拿不到证据的项，写进 `unverified`，**不要**放进 `criteria` 判 pass。
- `verdict=fail` 的判定门槛：存在 blocker/major，**或** §3.7 证明守卫空洞，**或** 存在未声明的行为变更。

---

## 6. 报告文件必含小节

1. 结论与 `cargo test` 真实输出/退出码；
2. 逐条清单对照（每条：你的命令 → 真实输出 → 判定）；
3. **反例清单**：你构造了什么、观测到什么、是否推翻了实现者的说法；
4. 未验证项与理由；
5. 缺陷清单（含严重度与复现步骤）；
6. 你**没有**独立复核的部分（诚实列账）；
7. §3.7 受控实验的完整三步原始输出。

**回报给父代理的内容只有一行：报告文件路径。**
