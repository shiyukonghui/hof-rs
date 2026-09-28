# ACCEPTANCE — hof-rs（引擎换代后的验收记录）

- 版本：**v2（2026-09-29）**，取代 v1（2026-09-21，已过期：其"E1–E6 未执行"的结论已被
  `runs/smoke-t1..t6` 与 DR-29..DR-53 取代；v1 原文存于 git 历史 `4fe077d`）。
- 需求基线 `.spec/hof-rs/REQUIREMENTS.md` **v0.3**；设计基线 `DESIGN-DETAIL.md` **v0.9**（§13/§14）；
  决策基线 `DECISIONS.md` **D216..D223**。
- **硬约束**：`PRD-mario.md` 逐字节未改（sha256 `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`）；
  `godot-mcp/**` 未被本线修改。

## 1. 验收方法

三类证据缺一不可：**离线确定性**（`cargo test --offline` 全绿 + 反例测试**非空洞**，用受控植入-回退证明）、
**真机端到端**（真实 T=1 跑在我们的引擎构建上并留证）、**独立验收**（另一批全新子代理只看需求/设计/代码/原始工件，
自己复现并给结构化 verdict）。三批（批次一、批次二、修复包）**各经一次独立验收，三次 verdict 均为 `pass`**。

## 2. 引擎换代（DR-41..DR-47）——已验收

| ID | 判据 | 结果 | 关键证据 |
|---|---|---|---|
| DR-41 | 拆 GDExtension 通道与 `extension_list.cfg` 缓存；`addon_source` 归零 | pass | 自造多插件工程端到端 `hoh init`：addon 目录删除、缓存**恰好**少掉那一行（138→87 B）、其它插件名逐字保留、列表空才整段移除、**连跑两次零字节变化**；`addon_source` 0 命中 |
| DR-42 | 夹具 174→**177** 四通道前缀；24 文件迁移；角色作用域重写 | pass | 177 条、正则违规 0、**集合与顺序**与 `tools_list.renamed.json` 一致、逐工具字段 diff 0、**无夹具专用键** |
| DR-43 | 双端点路由 | **pass（真机）** | `editor_play_scene` 真回 `endpoint`/`mcp_port`/`pid`/`mcp_port_source=auto_free_port`；首个 `running_game_get_scene_tree` **成功（50 节点）** |
| DR-44 | 引擎身份入库 + `engine_identity` 闸门 | **pass（真机）** | `meta.json.engine`：sha256 `25d29eb4…`、`4.8.dev.mono.custom_build.ba1587c71`、**`listener.pid=108432` 且 `matches_binary=true`**；匹配/不匹配/读不到三情形各有测试 |
| DR-45 | 旧词汇归零 | pass（**非空洞已证**） | 植入 `play_scene` ⇒ `tool_vocabulary` **转红**；回退后与 HEAD blob 逐字节一致；旧名集合与 rename map 174 条**双向差集为空** |
| DR-46/47 | 禁项与真机前置 | pass | 未启动引擎/未碰端口/未联网；PRD 未改；无新依赖 |

**端点集合恒等式（实测，取代 D219 的错值）**：契约 **177 = 104 editor-only + 50 共享 + 23 game-only**；
编辑器端点 **154**、游戏端点 **73**、并集 177。两条独立路径确证：活体 `tools/list` 逐字节捕获；
**静态**从 `tool_registry.cpp:267-277` 的 `scope_matches` + 177 条注册推导。

## 3. 真机 T=1 冒烟（批次二）——已执行，结论诚实

`target/release/hoh.exe run --iterations 1 --run-id smoke-t6`；**退出码 6**；**26,805,473 tokens / 约 112 分钟**；
四次 attempt 全部 `LimitsExceeded`。

| ID | 判定 | 依据 |
|---|---|---|
| E1 | **not_met** | 三角色真跑、`D_1`/`E_1` 合法（8 verified + 22 gap，绑定 candidate），但 **Developer 零工程增量**（`A0 == A1 == fc78d299…`） |
| E2 | **not_met（根因是假阴性）** | `artifact_gate.launchable=false`（exit 6），唯一"错误"是引擎信息行；同轮 **`play_scene` 与 `running_game_get_scene_tree` 确实成功**，`project_validate_scripts` 回 **7/7 编译成功** |
| E3 | **not_met** | 游戏端点**注册成功**（DR-43 由此获真机验证），随后**挂死并消失**（两轮可复现 65333/109964、63698/101872）；输入注入只到编辑器侧 ⇒ 核心行为无一被证实 |
| E4 | **met** | 8 条 verified 均指向真实存在的可复现公共记录并绑定 `candidate_id`；22 条未证者全落 gap |
| E5 | **met（强）** | 验收者**自己重实现 `hash_tree`**，workspace / candidate / 版本库三棵树 **17 文件逐字节同、同 hash `fc78d299…`** |
| E6 | **met** | QA 把未达成全部如实落 gap；验收者另构造反例（V7 依赖**旧 PNG**、V8 建立在 `ok=false` 步骤上）**均未推翻**——偏差方向一律保守 |

> **E2/E3 的 not_met 不是"模型没写代码"**：E2 是集成假阴性，E3 是引擎侧可用性缺陷（见 §5）。

## 4. 修复包（DR-48..DR-53）——已实现、已独立验收

| ID | 内容 | 离线判据 |
|---|---|---|
| DR-48 | 闸门只豁免**引擎信息横幅的确切形态**（常量数据 + 具名匹配） | **非空洞已证**：匹配函数恒真 ⇒ 3 条 ERROR 反例全红；常量加一尾空格 ⇒ 正向测试失败；引擎**真错误**行不被豁免 |
| DR-49 | 截图证据**本轮真实**：契约形态、调用前作废既有文件、`ok` 基于**新鲜度**、修回退压制 | 反例：预置旧文件**不再**伪造成功；旧文件**不再**压制 `capture_frames` |
| DR-50A | `execute_gdscript` 的 `code` 必须是 **GDScript 函数体**（值只能靠 `return` 传出） | 已修（原发裸表达式 ⇒ 4 次调用全回 `result_type:"Nil"`） |
| DR-51 | 端点身份**真正持久化**（`editor_status` 取真实 `GET /mcp`；`game_endpoint` 在**登记当刻**回写） | 有/无端点两条路径各有测试 |
| DR-52 | 诊断自洽 + **参数形状**逐工具核对 | 验收者独立解析 **177/177** `inputSchema.required` 与 `TC-TOOL-*` **0 处不符**；15 个真实调用点全合规 |
| DR-53 | 畸形 `enabled=` **不改文件**；补两条回归测试；过期测试名与断言 | 受控实验 + 测试 |

`cargo test --offline`：**EXIT 0，328 passed / 0 failed / 7 ignored**（7 条为既有真机门控）。

## 5. 上游缺陷（**未关闭**）：游戏端点挂死 = 引擎侧可用性缺陷（DR-50B）

- **依据（两轮可复现）**：hof-rs 的 JSON-RPC **合规**且前 4 次被正常应答；失败在**传输层**
  （连接建立、请求已发、**状态行始终不来**，`10060`，重试 3×120 s）；随后**监听消失**（`10061`）；
  **编辑器端点全程健康**（同轮 ids 26..43 全 ok，`editor_stop_scene` 还回了 `game_endpoint_invalidated`）；
  两轮（65333/109964、63698/101872）均如此；唯一与挂死同时出现的差别是"第 5 条是**首条编译不过**的 `code`"，
  而引擎对编译不过的**书面答案**本应是 `-32602`（带 `data.parse_error_line`）。
- **机制未定**（推断）："编译错误捕获路径卡住主线程"是假设，离线不可证。
- **最小复现（待执行）**：`editor_play_scene` 后第一件事发
  `running_game_execute_gdscript{code:"this is not gdscript"}` ⇒ 预期 `-32602`；若挂死 ⇒ 缺陷**孤立确认**。
- **纪律**：`godot-mcp/**` **未改、不改**；作为**上游项**单独立项。

## 6. 未关闭项（**不假装已完成**）

1. **DR-50B 最小复现 spike** 未执行；上游缺陷单未提交。
2. **绕行 2/3/4 未实现**（需先出设计 §15 / DR-54..DR-56）：①把 **E3 关键路径移出 `execute_gdscript`**，
   改用契约语义工具（`running_game_get_node_property_samples` / `running_game_create_input_recording` +
   `running_game_play_input_recording` / `running_game_run_test_scenario` / `running_game_assert_node_state` /
   `running_game_move_player_to_target`）；②同一端点**连续两次传输失败即快速失败**（本轮白烧约 12 分钟）；
   ③**业务错误（如 `-32602`）不重试**。
3. **E2/E3 能否真正 met 未验证**：修复包**全部修复都没有真机验证**，必须再跑一轮真机 T=1 + 独立验收。
4. **minor 缺陷**：`artifact_is_fresh` 的不可达分支；DR-49④ 单独不可证伪；DR-53 受控实验用了别的畸形写法；
   报告 §4.1 对 730 s 的措辞（首次 `10061` 只比最后一次 `10060` 晚 7 s）。
5. **`runs/smoke-t6` 目录摘要算法未文档化**（实现者 `3ce19752…` 不可复现，验收者得 `20aca752…`）。
6. **未验证的形态假设**：内联 `image_base64` 截图应答、`user://` 备选路径、`editor_status` 真机应答形态、
   引擎对"编译不过"是否**始终**回 `-32602`。

## 7. 残留风险

- **游戏端点的持续可用性是最大风险**：它决定 E3 乃至阶段二能否推进；在绕行 2/3 落地前，任何依赖游戏端点的观测
  都可能以 730 s 挂死 + 端点消失收场。
- **E1 零增量成因未定**：Developer 两次 attempt 都 `LimitsExceeded`（150 + 60 步），可能是步数预算不足，
  也可能是产物门槛过严；本轮未定性。
- **离线验收覆盖不到真机形态**：参数形状/应答形态的结论都建立在仓库内契约文档与夹具上，活体逐字复核只能由真机轮次提供。
- `runs/smoke-t1..t5` 属**旧契约时代**证据，**不得**与换代后轮次混用比较。

## 8. 工件索引

| 类别 | 路径 |
|---|---|
| 需求/设计 | `REQUIREMENTS.md` v0.3、`DESIGN-DETAIL.md` v0.9（§13/§14）、`DESIGN-OVERVIEW.md`、`PRD-mario.md`（冻结） |
| 任务书 | `tasks/TASK-DR41-IMPL.md`、`TASK-DR41-ACCEPT.md`(+`-ADDENDUM`)、`TASK-DR47-SMOKE.md`(+`-ADDENDUM`)、`TASK-DR47-ACCEPT.md`、`TASK-DR48-FIX.md`、`TASK-DR48-ACCEPT.md` |
| 实现/执行报告 | `tasks/TASK-DR41-REPORT.md`、`TASK-DR47-SMOKE-REPORT.md`、`TASK-DR48-REPORT.md` |
| 独立验收报告 | `tasks/TASK-DR41-ACCEPTANCE.md`、`TASK-DR47-ACCEPTANCE.md`、`TASK-DR48-ACCEPTANCE.md` |
| 真机证据 | `runs/smoke-t6/**`（换代后基线，**不得覆盖**） |
| 决策 | `DECISIONS.md` D216..D223 |
