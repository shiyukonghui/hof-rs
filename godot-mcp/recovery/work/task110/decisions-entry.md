
---

## D155 — TASK-110：覆盖驱动循环第一批：把 TASK-108 的盘点固化成可重跑台账（两种口径逐数复现）；3 个练习工程 / 4 组会话把 63 条 0 次工具打到 ≥5（家族① 42/42 过门，全语料 ≥5 数 27→89）；台账的「不可达联动视图」当场推翻 TASK-108 的 6 条 H7/H9 推断；并实测抓到一个阻塞级契约缺陷 —— `editor_list_signal_connections` 的 `scope` 被契约声明、被 handler 实现、却不在注册 schema 里 —— 一行修在根上、两变体重建、十门全绿、push 到 fork，同批重跑给出前后对比

- 日期：2026-09-27
- 触发问题：TASK-108 的只读测量给出「20 款游戏只覆盖 27/177（≥5 次），150 条 0 次」，并把 74 条判为结构性不可达（H1–H9，**自述是推断不是实测**）。用户要求把这套方法变成**随时可重跑的台账**，并驱动第一批覆盖：优先做不需要新子系统的三族（`project_*`、`editor_*` 读取、`running_game_*` 查询），每条目标工具 ≥5 次调用且含 ≥1 生效 + ≥1 边界；练习中发现缺陷按既有流程修在根上。
- 核查事实（全部来自本轮产物）：
  * **台账可复现**：`tools/tool_coverage.py` 在 `--only-final` 口径下重算 = 20 目录 / 40 trace / **2612** 次 / 27 个工具名 / 0-1-4-≥5 = **150 / 2 / 25**；在全量 `runs/**` 口径下（TASK-110 之前）= 81 / 140 / **6618** / 29 / **148 / 2 / 27**。与 TASK-108 §3/§4 **逐数相同**（这也说明契约 sha `BD68E804…` 与 `dist/review_data.json` 的 20 个 tag 在这两轮之间没有变）。
  * **「计数」与「证据」分开后**：用本轮新加的严格门（≥5 且 有效≥1 且 边界≥1）去量 TASK-108 那批 20 款，只有 **5 条达标**，22 条「计数达标缺证据」—— 也就是说那条循环里 25 条 ≥5 的工具，**22 条从未有过一次失败调用**。这不是否定旧数字，是把旧数字没回答的问题答了。
  * **一种口径不能混用**：`--only-final` 与全量两套数字在本轮全程并列给出，报告里不互相引用。
- 选项（覆盖怎么做）：
  1. 直接在 20 款正式工程上跑更多调用 —— **否决**：铁律 6 要求只读对待 `projects/` 与 `runs/` 原有内容，且正式工程的场景已经被历史会话改过（例如 c1 末尾把自建场景删了），不可重放；
  2. **在 `projects/_exercises/` 建少量练习工程 + 专门会话**（选中）：可原样重放、可重复、失败不污染正式证据；
  3. 只写台账不造覆盖（把 B 段留空）—— **否决**：那样台账永远只有 27 条，无法回答「工具到底能不能用」。
- 选项（练习会话怎么写）：
  1. 手写 session.json —— 否决：651 次调用手工写必然漂移，且「哪次是设计好的边界」会丢失；
  2. **写生成器 `tools/gen_coverage_session.py`，按批次生成 session + manifest**（选中）；manifest 逐调用记 `intent ∈ {ok, probe, edge, setup}`，`tools/verify_coverage_batch.py` 按它判定，**setup 类调用不进判定**（否则开场景/build 这类前置会被当成没有边界的目标来判）。
- 选项（发现缺陷怎么办）：
  1. `scope` 这一条**只登记不修** —— 否决：它的根因是**一行**、语义唯一（把契约自己声明的成员补进注册 schema），且它是**阻塞级**（能力被实现却无法被请求，调用方按契约发参数必得 -32602）；
  2. **修在根上并走完既有的重建/门/push 流程**（选中）；
  3. 其余 4 条（D2 搜索白名单、D3 构建超时上限、D4 只读参数 no-op、D5 可选参数实为必填）**只登记不修**（选中）—— 理由见下。
- 选择：台账固化 + 练习工程路线 + 生成器/manifest + 只修 `scope`。
- 理由：
  * 练习工程路线是**唯一**同时满足「可重放」「不碰正式证据」「边界可造」的路线；成本是两个 14 文件的工程副本 + 5 张现造的 8×8 PNG。
  * **边界必须是被设计出来的、可审计的**：trace 分不清「设计好的失败」与「碰巧失败」，所以判定必须落在一份 manifest 上。本轮 c1 首轮 34/42、c1b 7 条、c1c 2 条的收敛过程本身就证明了这个设计 —— 而且 8 条缺口的根因**全部在会话侧**（没建程序集、没有可预览的资源、探针用了宽容输入、场景被自己删了），**没有一条是工具缺陷**。
  * 只修 `scope` 而不修 D2–D5，是因为后四条的修法各自要在**行为面/超时语义/契约参数**上做选择（白名单要不要收 `.csproj/.sln/.uid`？`timeout_ms` 的上限该改契约还是改服务端？`include_default` 该删还是该实现？`node_path` 该标必填还是回退到根？）——这些是设计决策，不是机械修补；把它们混在一次「修 bug」里做掉，等于悄悄替用户定了口径。
- 做法与结果：
  * **台账**：`tools/tool_coverage.py`（读契约 + `tool-rename-map.json` + 6 份 `tool-groups*.json` join scope；逐调用事实**复用** `mcp_trace_ledger.py`，不另立 verdict 词汇）产出 `TOOL-COVERAGE.md` + `coverage.json`；`有效调用` 按**动词**分两类判定（读类动词的生效证据就是它的回包；其余动词必须是 `ok_effect_*`/`ok_file_effect_*`），带 `assertion_failed`/`created_conflict`/`scenario_*` 的 ok 不计。`tools/tool_coverage_unreachable.json` 由 `recovery/work/task110/make_unreachable_registry.py` 从 TASK-108 §5.3 **逐行派生**（74 条 / 9 类），台账把它与实测**联动**。
  * **联动视图当场抓到东西**：c23 真的调用了登记表里 **6 条**「结构性不可达」—— H7 的 `editor_get_selection`/`get_open_scripts`/`get_output_log`/`get_performance_monitors`（编辑器读自己的 GUI 状态，空/无都是合法答案）、H9 的 `running_game_capture_frames`/`capture_signal_emissions`（不需要任何前置模式，帧内联回包、信号自己注册监听并捕到 `Tick.timeout` 的 1 次与 2 次发射）。这 6 条**没有静默删掉**，而是记进登记表的 `reclassified` 段（附「为什么可以删」+ 证据 run），台账从此当可达看。**H1–H9 这 74 条推断的错例率至少 8.1%，且错误集中在「需要前置运行态」这一类。**
  * **覆盖**：3 个练习工程（`ex_files` / `ex_scene` / `ex_scene2`）、4 组会话（c1 252 次 + c1b 49 + c1c 24 + c23 163×2），**家族① 40 条 `project_*` 全部过门（42/42，含 2 条顺手项）**，家族② 13/14、家族③ 6/9。全语料：工具名 29 → **92**、≥5 数 27 → **89**、0 次数 148 → **85**、达标 5 → **66**；「可达但未覆盖」76 → **20**（下一批清单已写进报告 §E）。
  * **缺陷（已修）**：`editor_list_signal_connections` 的 `scope`。契约（`tools_list.renamed.json`）声明 `enum=[all,user,internal]` + 描述里连响应键 `counts` 都写了；`editor_node_read.cpp:676-686/701-710` 完整实现了解析、过滤与 `counts` 回包（实测回包确实带 `"scope":"all"` 与 `counts`）；但**注册 schema（`editor_node_read.cpp:774`）只声明了 `node_path`/`signal_name`**，于是参数校验器在 handler 之前就把参数挡掉 —— 修复前 `scope:"user"|"internal"|"bogus"` **3/3** 得 `-32602 Unknown parameter 'scope'`。修法：把契约自己那个成员**逐字**补进 schema 字面量。引擎提交 `3fdabe2d9a`。
  * **收尾（真实退出码）**：两变体在模块提交**之后**串行重建（`mcp057_build_mono.cmd` / `build_local.cmd`，均 exit 0，`--version` = `4.8.dev.mono.custom_build.3fdabe2d9` / `4.8.dev.custom_build.3fdabe2d9`）；十道门 `g01`…`g10` **全部 exit=0**（`g09` **ANCHOR_EQUAL**、`g10` `accept_m1` **22/22 cases passed**、`g04` 两端点契约子集 3/3 PASS），账在 `runs/gates/task110/summary.txt`；引擎仓 push 真实输出 `1f9d0cb1c9..3fdabe2d9a`，HEAD 与远端同为 `3fdabe2d9a`。
  * **同批重跑（前后对比）**：用同一个 `c23-session.json` 对**另一份干净工程** `ex_scene2` 重跑（163 次）：`{scope:"user"}` → **ok**（只回用户侧 `Tick.timeout → _on_tick_timeout`）、`{scope:"internal"}` → **ok**（36 217 B 内部连接）、`{scope:"bogus"}` → `-32602 Parameter 'scope' accepts a string, one of: all|user|internal`（**错误信息从「未知参数」变成指向真因**）；该工具在 ledger 里的编辑端失败数 **20 → 18**，两轮都是 163 次调用。
- 预期影响与回滚点：
  * **覆盖从此是过程而不是一次性报告**：`python tools/tool_coverage.py` 随时重算，`tools/verify_coverage_batch.py` 对批次给 pass/fail；下一批只要加一个 `BATCHES` 条目 + 一份练习工程即可。
  * **台账的三条硬口径**要沿用：①两种语料口径不混用；②`有效/边界`必须来自 ledger 的 verdict 与 manifest 的 intent，不许口头认定；③登记表的成员若在实测里被调用，**必须**从「不可达」集合里改判并留证，不许静默删除。
  * **H1–H9 的其余 68 条不代表「不可达」已被证实**：本轮已证明其中 6 条是错的，报告 §E 因此建议下一批先抽查 H7/H9，再决定要不要为 H2/H4/H5/H6 真的去建子系统。
  * **D2–D5 是下一批的入口而不是遗留**：每条都给了证据、根因文件行号与补丁落点（报告 §C2）；另建议把本轮的调用侧探针**系统化**成一次「契约 177 条 `properties` 成员 vs 注册 schema」的**成员级对照**（本轮只在 25 个目标上探测就抓到 1 条阻塞 + 4 条不符，而 `REPORT-052` §A7 猜过、TASK-108 §6.8 自述没做这件事）。
  * 回滚点：引擎侧 `git revert 3fdabe2d9a`（一行 schema 成员，回滚后需按 §C1 的命令重建两变体并重跑十道门）；主仓侧删除本任务的工具/会话/练习工程/报告即可，**20 款正式工程与它们的 `runs/` 一个字节都没动**。
