# TASK-110 — 覆盖驱动循环第一批：可自动刷新的覆盖台账 + 三族练习批次 + 一个修在根上的契约缺陷

> 本报告的所有数字都是本轮从 trace 原文、契约原文与运行自带的响应文件重算出来的，没有从任何报告表格转抄。
> `runs/` 与 `projects/` 下的 20 款正式工程**零改动**（只读）；练习工程新建在 `projects/_exercises/`。
> 唯一的引擎改动在 §C1，已重建两变体、十道门全绿、push 到 fork，并在本节给出前后对比。

---

## 0. 一句话结论

**做完了三件事，并在做的过程中找到一个必须马上说的缺陷。**

1. **台账**：`tools/tool_coverage.py` 把 TASK-108 的统计方法固化成可重跑的工具，两种口径（全量 `runs/**` 与 `--only-final` 的 20 个最终 tag）各自**逐数复现 TASK-108**（2612 次 / 25 条 ≥5 / 150 条 0 次；6618 次 / 27 条 ≥5 / 148 条 0 次），并新增「有效 / 边界 / 字段齐备」三列与**不可达登记表的联动视图**。
2. **覆盖**：新建 3 个练习工程、4 个专门会话、**4 组批次共 651 次调用**（c1 252 + c1b 49 + c1c 24 + c23 163×2），把**可达但 0 次的 63 条**工具从 0 打到 ≥5，其中**家族①的 40 条 project_* 全部通过「≥5 次 + ≥1 生效 + ≥1 边界」的批次门（40/40）**。全语料达标数 **27 → 89 / 177**。
3. **缺陷**：一个**阻塞级**契约/实现不符被实测抓到并修在根上 —— `editor_list_signal_connections` 的 `scope` 参数**契约声明、handler 实现、注册 schema 却没有**，于是调用方永远拿 -32602。修复后 `scope:user|internal` 从 0/3 accepted 变成 3/3 accepted；另登记 4 条根因明确但需设计决策的缺陷、3 条观察。

**必须同时说清的边界**：§C2 的 4 条只登记未修（理由逐条给出）；`running_game_capture_frames` / `capture_signal_emissions` / `get_node_properties_batch` 这 3 条目标仍是「计数达标缺证据」，台账没有替它们把证据补上（§B4）。

---

## 1. 交付物与证据路径

| 交付物 | 路径 | 说明 |
|---|---|---|
| 覆盖台账工具 | `tools/tool_coverage.py` | 随时可重跑；`--only-final` / 全量两种口径 |
| 台账（人读） | `TOOL-COVERAGE.md` | 177 行总表 + 分桶 + <5 清单 + 不可达联动视图 |
| 台账（机读） | `coverage.json` | 逐工具 calls/effective/boundary/facts/verdict 分布/证据路径 |
| 不可达登记表 | `tools/tool_coverage_unreachable.json` | H1–H9 推断 + 6 条**已改判** |
| 会话生成器 | `tools/gen_coverage_session.py` | 批次 c1/c1b/c1c/c23 的唯一真源，同时产出 manifest |
| 批次校验器 | `tools/verify_coverage_batch.py` | 按 manifest 逐工具判「≥5 + ≥1 生效 + ≥1 边界」 |
| 练习工程构造脚本 | `recovery/work/task110/make_exercise_project.py` | 从 `projects/pong` 复制 + 补种 5 张小 PNG |
| 会话与清单 | `tools/sessions/_exercises/ex_files/{c1,c1b,c1c}-{session,manifest}.json`、`tools/sessions/_exercises/ex_scene/c23-*` | 可原样重放 |
| 运行证据 | `runs/_exercises/ex_files/{c1,c1b,c1c}-task110/`、`runs/_exercises/ex_scene/c23-task110/`、`runs/_exercises/ex_scene2/c23-after-task110/` | trace + ledger + 逐调用请求/响应 + 截图（`runs/` 被 `.gitignore` 按既有政策排除，只留在盘上） |
| 门账 | `runs/gates/task110/summary.txt` | g01…g10 真实退出码 |
| 引擎改动 | 引擎仓 `3fdabe2d9a`（`feature/mcp-server-module-rebuild`，已 push） | 一行 schema 成员 |

---

## A. 可自动刷新的覆盖台账（`tools/tool_coverage.py`）

### A1. 输入契约与两种口径

* 契约：`godot/modules/mcp_server/docs/tools_list.renamed.json`（177 条），scope 由 `tool-rename-map.json` + 6 份 `tool-groups*.json` 按名 join（`editor=104 / both=50 / game=23`）。
* `--only-final`：语料 = `dist/review_data.json` 的 20 个最终 `run_tag`（= TASK-108 §3 口径）。
* 默认（全量）：语料 = `runs/**/trace-*.jsonl`（= TASK-108 §4 口径，现在也含本轮练习轮）。
* 逐调用事实**直接复用** `godot/modules/mcp_server/scripts/mcp_trace_ledger.py`（import 成模块），所以「生效 / 边界」用的是那份 reader 的 verdict 词汇，不另立一套。

### A2. 与 TASK-108 的独立复算对照（这是台账可信的前提）

| 口径 | 指标 | TASK-108 报告 | 本工具重算 | |
|---|---|---|---|---|
| 20 个最终轮 | run 目录 / trace 文件 / `tools/call` | 20 / 40 / 2612 | 20 / 40 / **2612** | ✓ |
| | 出现的工具名 | 27 | **27** | ✓ |
| | 0 次 / 1-4 次 / ≥5 次 | 150 / 2 / 25 | **150 / 2 / 25** | ✓ |
| 全量 `runs/**`（TASK-110 之前） | run 目录 / trace 文件 / `tools/call` | 81 / 140 / 6618 | 81 / 140 / **6618** | ✓ |
| | 出现的工具名 | 29 | **29** | ✓ |
| | 0 次 / 1-4 次 / ≥5 次 | 148 / 2 / 27 | **148 / 2 / 27** | ✓ |

两条口径逐数一致，说明「盘点方法固化」这一步没有在搬运中走样。**「达标」是 TASK-110 新加的严格口径**，用它去量 TASK-108 那批 20 款游戏会得到 `达标 5 / 计数达标缺证据 22`：也就是说，20 款循环里那 25 条 ≥5 的工具，有 22 条**从未有过一次失败调用**（没有负路径证据），另有 3 条（`editor_open_scene`、`editor_set_node_script_batch`、`editor_set_node_property`）连一次「生效」都没有 —— 这是台账第一次把「计数」与「证据」分开看的结果，不是对旧数字的否定。

### A3. 「有效调用」的判定规则（写在台账表头，可复核）

* `边界调用` = 该工具 `ok=false` 的次数。
* `有效调用`：**读类动词**（get/read/search/list/find/analyze/detect/convert/validate/check/assert/execute/evaluate）= `ok=true` 且回包是实质载荷（读类调用本就不动像素/字节，回包就是它的证据）；**其余动词**（create/edit/set/add/remove/write/build/simulate/capture…）= ledger 的 `ok_effect_observed` / `ok_file_effect_observed`，也就是真的改了画面或文件。带 `assertion_failed` / `created_conflict` / `scenario_*` 的 ok 调用不计有效。
* `状态`：`达标` = 调用≥5 且 有效≥1 且 边界≥1；`计数达标缺证据` = 调用≥5 但缺其一；`未达(1-4)` / `未达(0)`。
* 6 条 `_meta.added_tools` 不在 rename map 里，动词由名字第二段推导（否则 `project_read_text_file` 会被当成写类工具而永远判不生效）。

### A4. 不可达登记表的联动视图

登记表 `tools/tool_coverage_unreachable.json` 由 `recovery/work/task110/make_unreachable_registry.py` 从 TASK-108 §5.3 **逐行派生**（74 条 / 9 类，与报告一致），并保留一个 `reclassified` 段。台账把它与实测**对在一起**，实测调用不为 0 的条目会打上「漂移」。

**这条联动视图立刻就抓到了东西**：本轮 c23 把登记表里 **6 条**「结构性不可达」的工具真的调用了 —— H7 的 `editor_get_selection` / `get_open_scripts` / `get_output_log` / `get_performance_monitors`（编辑器端点确实能读自己的 GUI 状态，空选择、无打开脚本都是合法答案），H9 的 `running_game_capture_frames` / `capture_signal_emissions`（不需要任何前置模式：前者 `count/frame_interval` 就够且帧内联回包，后者自己注册监听并报出 `Tick.timeout` 的 1 次与 2 次发射）。它们没有被静默删掉，而是记进 `reclassified`（附「为什么可以删」和证据 run），台账从此把它们当**可达**看。**结论：TASK-108 §5.3 的 74 条推断里有 6 条（8.1%）是错的，且错的是「需要前置运行态」这一类推断。**

---

## B. 第一批覆盖

### B1. 练习工程与专门会话

| 工程 | 来源 | 用途 |
|---|---|---|
| `projects/_exercises/ex_files` | 从 `projects/pong` 复制（不含 `.godot`）+ 补种 5 张小 PNG | 家族①（`project_*` 文件/资源/主题/着色器族），只用编辑器端点 |
| `projects/_exercises/ex_scene` | 同上 | 家族②（编辑器读取族）+ 家族③（运行期查询族），编辑器→游戏两阶段 |
| `projects/_exercises/ex_scene2` | 同上（c23 修复后重跑用的干净副本） | 同批重跑的对照 |

会话不是手写的：`tools/gen_coverage_session.py` 按批次生成 `session.json` + `manifest.json`（后者逐调用记 `intent ∈ {ok, probe, edge, setup}`）。**边界证据能否被审计，全靠这份 manifest** —— trace 本身分不清「这次失败是设计好的边界」还是「这次碰巧失败」。`setup` 类调用（开场景、建节点、建自动加载、build）不进批次判定，否则 setup 工具会被当成没有边界的目标来判。

### B2. 家族① `project_*`：40/40 通过批次门

* 批次 c1（252 次调用，42 个工具 = 40 个目标 + `project_create_script`、`project_read_text_file` 两条顺手补证据）→ 34/42 过门。
* c1b（49 次）修 7 条，c1c（24 次）修 2 条，**最终 42/42**。8 条缺口的根因**全部在会话侧，不是工具缺陷**，逐条写进了生成器头部：

| 缺口 | 根因（实测） | 修法 |
|---|---|---|
| `project_validate_script`（6/6 全 -32000） | 复制出来的工程**没有已构建的程序集**；工具**正确地拒绝**发布 `valid`（「not compiled 不等于 does not compile」） | c1b 先 `project_build_csharp`，c1c 在**新编辑器进程**里验证（程序集在启动时载入）→ 3 条真判词 |
| `project_get_resource_preview`（6/6 全 -32602） | 工程里只有场景/主题/Gradient/Curve，**没有带图像预览的资源类** | 用 Python 现造 5 张 8×8 PNG（不引第三方库）→ 5 条真预览 |
| `search_file_names` / `search_file_contents` / `find_script_references` / `set_node_property_across_scenes` | 探针用了工具**宽容**的输入（空 pattern、只匹配不到、坏 path_filter 只回 ok+说明），所以没造出失败 | 改探针为**目录参数**不存在 → -32001 |
| `find_files_referencing_symbol` | 该工具**没有 path 参数**，只能从类型下探 | 探针 `pattern:123` → -32602 |
| `set_node_property_across_scenes`（生效 0） | c1 末尾把自己建的 5 个场景删了，且 `force=false` 会跳过打开中的场景 → 无改写 | c1c 重建场景 + 写与默认值**不同**的 `visible=false` → 真落盘 |
| `project_create_script`（顺手项） | 两次探针都成功（它会自建目录、且幂等） | 探针改为 `path:123` → -32602 |

### B3. 家族② 编辑器读取族 / 家族③ 运行期查询族

* 批次 c23（163 次 = 编辑器 109 + 游戏 54），25 个目标 → **20/25 通过**（5 条不过门的逐条见 B4）。
* 家族② 14 个目标 **13/14**；家族③ 9 个目标 **6/9**（另含顺手补边界的 `editor_get_scene_tree`、`editor_get_node_properties` 两条，前者无失败调用）。
* 这一批的**真实生效**是可指认的：`editor_get_collision_info` 读回 `StaticBody2D` 的碰撞层/掩码，`editor_find_nodes_in_group` 真的按 `ex_balls/ex_ui` 找到节点，`editor_execute_gdscript` 读回 `Main` / `4` / `pong`，`running_game_find_ui_elements` 在运行中的游戏里枚举到 10 个 Control，`running_game_simulate_button_click_by_text` 点中 `ClickMe`（该按钮挂着 c23 现场编译上去的 C# 处理器，点下去把 `Background` 改红 → 像素差可证），`running_game_capture_signal_emissions` 在 `Tick` 上捕获到 `timeout` 发射。

### B4. 没通过门的 5 条（如实列出，没有替它们补证据）

| 工具 | 过不了哪一条 | 实测事实 | 说明 |
|---|---|---|---|
| `editor_get_output_log` | 边界 | `max_lines:-1` 被接受（返回 9 行） | 顺手项；负数没有报错 |
| `editor_get_scene_tree` | 边界 | `max_depth:-2` 被接受 | 顺手项；契约的下限是 -1 但实现容忍更小 |
| `running_game_capture_frames` | 生效 | 5 次都 ok 且回包带内联 base64 帧；但 `capture` 不在读类动词里、画面/文件又没变化 | 台账**没有**为它放宽规则 |
| `running_game_capture_signal_emissions` | 生效 | 同上，其中 2 次真的捕获到发射（1 次 / 2 次） | 同上；这两条的「生效」只差一条**规则澄清**，不是差证据 |
| `running_game_get_node_properties_batch` | 边界 | 不存在的节点**不报错**，而是 `ok` + 每项 `{"error":"Node not found"}` | 批语义下的设计选择，见 §C2-D7 |

---

## C. 缺陷

### C1. 【已修·阻塞级】`editor_list_signal_connections` 的 `scope`：契约声明、handler 实现、注册 schema 没有

**证据（全部来自本轮 trace 与运行自带响应）**

| 面 | 证据 | 内容 |
|---|---|---|
| 契约 | `docs/tools_list.renamed.json` 该工具 `inputSchema.properties.scope` | `type=string, default="all", enum=[all,user,internal]`，描述里连响应键 `counts` 都写了 |
| 实现 | `editor_node_read.cpp:676-686, 701-710` | `optional_string(p_args,"scope",...)` + `parse_signal_connection_scope` + 过滤 + 回包 `scope` 与 `counts` |
| 调用面 | **修复前** `runs/_exercises/ex_scene/c23-task110`：`c23-059/060/061` | `scope:"user"`、`scope:"internal"`、`scope:"bogus"` **3/3** 得 `-32602 "Unknown parameter 'scope' … Accepted parameters …: node_path, signal_name"` |
| 注册 schema | `editor_node_read.cpp:774`（改前） | 那行 JSON 字面量只声明 `node_path` / `signal_name`，所以**参数校验器在 handler 之前就把参数挡掉** |

也就是说：能力被实现了、被文档化了、却**无法被请求**。本仓既有报告（`BREAKOUT-FINDINGS-R3.md`、`PLATFORMER-DEV-LOG.md` §⑩）曾**实测过** `scope` 生效，说明这是重建期丢掉的一行，不是「从未实现」。

**修法**（引擎仓 `3fdabe2d9a`，一行）：把契约自己的那个成员**逐字**copy 进注册 schema（含 enum/default/描述），让 schema 与契约在这个工具上相等，而不是反过来教契约接受一个更小的答案。

**前后对比（同会话形状、同工程，改前 `ex_scene` / 改后 `ex_scene2`）**

| 调用 | 修复前 | 修复后 |
|---|---|---|
| `{scope:"user"}` | `-32602 Unknown parameter 'scope'` | **ok**，只回用户侧连接（`Tick.timeout → _on_tick_timeout`） |
| `{scope:"internal"}` | `-32602 Unknown parameter 'scope'` | **ok**，回 36 217 B 编辑器内部连接 |
| `{scope:"bogus"}`（边界探针） | `-32602 Unknown parameter 'scope'`（**错误信息不指向真因**） | `-32602 Parameter 'scope' accepts a string, one of: all\|user\|internal, optional (default "all")` |
| 该工具 ledger | 编辑端 `failed=20` | 编辑端 `failed=18`（同为 163 次调用） |

**收尾（真实退出码）**：两变体在模块提交**之后**串行重建（`mcp057_build_mono.cmd` / `build_local.cmd`，均 exit 0，`--version` = `4.8.dev.mono.custom_build.3fdabe2d9` 与 `4.8.dev.custom_build.3fdabe2d9`）；十道门 `g01`…`g10` **全部 exit=0**（`g09` **ANCHOR_EQUAL**、`g10` `accept_m1` **22/22 cases passed**、`g04` 两端点契约子集 3/3 PASS），账在 `runs/gates/task110/summary.txt`；引擎仓 `git push origin feature/mcp-server-module-rebuild` 真实输出 `1f9d0cb1c9..3fdabe2d9a`，HEAD 与远端同为 `3fdabe2d9af5b482dc95ccb00ce63a0943601991`。

### C2. 【只登记·未修】4 条根因明确，但修法需要设计决策

> 「根因明确就修掉」在这里**不适用**：这 4 条的修法各自会在**契约/行为/超时语义**上做选择，属于设计决策而不是机械修补；本轮只做了 C1（一行、语义唯一）。（每条的补丁落点都写出来了，下一批可以按它直接做。）

**D2 ｜ `project_search_file_contents` 静默跳过 `.cs`**
* 证据：`c1` 的 `{"pattern":"class"}` 命中 1 处（`project.godot` 的注释），`c1b` 的 `{"pattern":"class","path":"res://src"}` 与 `{"pattern":"PongGame","path":"res://src"}` 都 **count 0**，而 `project_read_script` 同一目录里的 `PongGame.cs` 明明有 `class PongGame`。
* 根因：`project_read_template.cpp:460-471` 的固定白名单 `gd/tscn/tres/cfg/godot/gdshader/md/txt/json/yaml/yml/xml/csv/ini` —— **没有 `cs`**。契约描述只说「跳过 addons 与 .godot 目录」，没说扩展名（对照：`project_find_files_referencing_symbol` 的描述**明确写了**它只扫 `.tscn/.gd/.tres/.gdshader`）。
* 影响：**整个循环是 C# 工程**，最自然的查询（在源码里找符号）得到静默的 0，且回包没有任何提示。
* 修法选项：①白名单加 `cs`（最小，但要定 `.csproj/.sln/.uid/.import` 算不算文本）；②契约描述里把白名单写出来（不改行为，改期望）；③两者都做。**建议 ①+②**，但这会改变既有行为面，需先定口径。

**D3 ｜ `project_build_csharp.timeout_ms`：契约上限 600000，实现实际封顶 30000**
* 证据：`c1b-001` 请求 `{"timeout_ms":300000}` → 回包 `"timeout_ms":300000,"effective_timeout_ms":30000`（`exit_code:0`）。
* 根因：`project_csharp_build.cpp:507-515` `effective_build_timeout_ms = MIN(requested, MCPPendingTimeout::effective_ms(configured))`，而 `mcp_server.h:79 DEFAULT_MS = 30000`；schema 却在 `:748` 声明 `maximum: 600000`。
* 影响：大工程的 C# 构建会在 **30 s** 被 kill（`killed/timed_out` 如实回报），而调用方按契约以为自己要到了 5 分钟。**这是本轮最接近「契约说谎」的一条**（响应层诚实，契约层不诚实）。
* 修法选项：①把声明的 `maximum` 改成与服务端 pending timeout 一致；②把 pending timeout 与 `timeout_ms` 打通（真正的长构建）；③契约里写明「effective = min(请求, 服务端 pending timeout)」。**这是超时语义的设计决策**，故只登记。

**D4 ｜ `project_get_settings.include_default`：声明了（default=false）但被实现忽略**
* 证据：`{}` 与 `{"include_default":true}` 的回包**逐字相同**（`count:988`，含全部默认项）；带 `prefix` 时也照样含默认项（`application` → 37、`display` → 45）。
* 根因：`project_read_template.cpp:281-287` 显式 `(void)include_default;`，注释写明「为了契约兼容而接受；参考实现也不用它，永远报当前有效值」。
* 影响：参数是 no-op，契约读起来像是可控制默认值。修法：契约去掉该参数，或实现真的启用它 —— 都是口径决策。

**D5 ｜ `editor_get_collision_info` 的 `node_path`：schema 说可选，空值时 -32001**
* 证据：`c23-026` `{"node_path":"Body"}` → ok；`c23-028` `{}` → `-32001 Node '' …`（消息提示「`node_path` 相对编辑场景根（`.` 是根本身）」）；`c23-030` `{"node_path":"BodyShape"}` → ok。schema `required=[]`。
* 影响：「可选」在契约里意味着可以不传，实现却是必填。修法：schema 标 required，或空值时回退到场景根（`.`）—— 语义决策。

### C3. 【观察·未修】3 条设计/一致性问题

* **D6 ｜ 值规则拒绝用 `-32602`（Invalid params）**：`project_get_resource_preview` 对「该资源类没有图像预览」、`editor_get_physics_layers` 对「该节点不是 CollisionObject」都用 `-32602`，且 suggestion 自称「该拒绝来自本工具自己的值规则、不指向 inputSchema 的任何成员」。消息**可定位**（说明了真因），但错误码分类是错的，且 suggestion 是模板噪声。
* **D7 ｜ `running_game_get_node_properties_batch` 把每项错误放进 `ok` 载荷**：不存在的节点得到 `ok=true` + `results:[{"node_path":"NoSuchNode","error":"Node not found"}]`，而单数工具 `running_game_get_node_properties` 对同一情况**硬失败**（-32001）。批语义下可辩护，但「只看 `ok` 的调用方会漏掉失败」，建议契约把这条写清。
* **D8 ｜ `editor_analyze_signal_flow` 不认场景根的名字**：`{"node_path":"Main"}` → `-32001 Node 'Main' not found`，而同一批里 `editor_get_node_properties`、`editor_get_node_groups`、`editor_get_node_signals` 用同一个 `"Main"` 都解析成功（分别回 `.`）。三比一的不一致，且契约里 `analyze_signal_flow` 明写「node_path 精确匹配」，所以是**匹配语义**问题而非路径解析缺陷 —— 建议契约补一句「根节点写成 `.`」。

**已知问题的一次再现（非本轮新发现）**：c23 修复后的重跑里 `--import` 的 ERRORLEVEL 报 `-1073741819`（0xC0000005 访问违例），**同一次导入的进程退出码是 0**，会话与全部 163 次调用照常完成。这与 TASK-098/099 用 40+24 份一次性副本追查的是同一类现象，此处只记「又见到一次」。

---

## D. 收尾：覆盖增量、台账、决策、提交

### D1. 覆盖率前后（全量 `runs/**` 口径；TASK-108 基线 vs 本轮）

| 指标 | TASK-108（基线） | TASK-110（本轮） | 增量 |
|---|---|---|---|
| run 目录 / trace 文件 / `tools/call` | 81 / 140 / 6618 | 87 / 148 / **7280** | +6 / +8 / +662 |
| 出现过的工具名 | 29 | **92** | **+63** |
| `0` 次 | 148 | **85** | **−63** |
| `1-4` 次 | 2 | 3 | +1（全部是 c23 的 setup 工具：`editor_connect_signal` 4、`editor_set_node_groups` 4、`editor_setup_collision_shape` 2） |
| `≥5` 次 | 27 | **89** | **+62** |
| `达标`（≥5 且 有生效 且 有边界） | 5 | **66** | **+61** |
| 登记表「不可达」 | 74 | 74（其中 **6 条已按实测改判**，仍当不可达 68） | −6 |
| 可达但未覆盖（<5 且非不可达） | 76 | **20** | **−56** |

**「累计达标数 / 177」的两种读法**：按**批次门**（≥5 + 生效 + 边界）= **66/177**；按**只数次数**（≥5）= **89/177**。二者都不是「177 条全部可用」——剩下的 88 条里，68 条仍登记为需要本循环不具备的子系统（现在已知道其中至少有 6 条登记错了），20 条是本轮没排到的可达工具（清单见 §E）。

### D2. 台账与决策

* `TOOL-COVERAGE.md` / `coverage.json` 由 `python tools/tool_coverage.py` 重跑生成（本轮最后一次：87 run / 148 trace / 7280 调用 / 92 工具）。
* 决策记录：`DECISIONS.md` D155。
* `.gitignore` 增补一条同类规则：`projects/_exercises/*/.godot|bin|obj|.mono` 不入库（既有 33-40 行只匹配一层，练习工程多一层，否则 8.4 MB 导入缓存会被当源码提交）。

### D3. 提交

* 引擎仓：`3fdabe2d9a`（已 push，见 §C1）。
* 主仓：本报告与全部工具/会话/清单/台账同一个提交（见 §G）。

### B5. 家族① 逐工具结果（批次 c1 + c1b + c1c）

**家族① `project_*` 42 个目标（40 条 0 次工具 + `project_create_script`、`project_read_text_file` 两条顺手补证据）**（判据来自 `tools/verify_coverage_batch.py` 对 `coverage.json` 的实测；`本批` 列只数练习轮的调用，`累计` 列含此前的历史轮）

| # | tool | scope | 本批 | 累计 | 有效 | 边界 | facts | 判定 | 证据（主 run） |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `project_add_autoload` | both | 8 | 8 | 7 | 1 | 8/8 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 2 | `project_analyze_scene_complexity` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 3 | `project_convert_path_to_uid` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 4 | `project_convert_uid_to_path` | both | 8 | 8 | 6 | 2 | 8/8 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 5 | `project_create_resource` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 6 | `project_create_scene_file` | both | 12 | 15 | 13 | 2 | 15/15 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 7 | `project_create_script` | both | 22 | 71 | 38 | 1 | 71/71 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 8 | `project_create_shader` | both | 7 | 7 | 6 | 1 | 7/7 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 9 | `project_create_theme` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 10 | `project_delete_scene_file` | both | 6 | 10 | 8 | 2 | 10/10 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 11 | `project_detect_circular_dependencies` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 12 | `project_edit_resource` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 13 | `project_edit_shader` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 14 | `project_find_files_referencing_symbol` | both | 12 | 12 | 11 | 1 | 12/12 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 15 | `project_find_script_references` | both | 12 | 12 | 11 | 1 | 12/12 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 16 | `project_find_unused_resources` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 17 | `project_get_filesystem_tree` | both | 6 | 6 | 2 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 18 | `project_get_info` | both | 8 | 8 | 6 | 2 | 8/8 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 19 | `project_get_resource_preview` | both | 12 | 12 | 5 | 7 | 12/12 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 20 | `project_get_scene_dependencies` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 21 | `project_get_scene_exports` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 22 | `project_get_settings` | both | 7 | 7 | 4 | 1 | 7/7 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 23 | `project_get_shader_params` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 24 | `project_get_statistics` | both | 7 | 7 | 5 | 2 | 7/7 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 25 | `project_get_theme_info` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 26 | `project_list_scripts` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 27 | `project_read_resource` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 28 | `project_read_scene_file_content` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 29 | `project_read_script` | both | 8 | 8 | 5 | 2 | 8/8 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 30 | `project_read_shader` | both | 7 | 7 | 6 | 1 | 7/7 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 31 | `project_read_text_file` | both | 6 | 86 | 80 | 1 | 86/86 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 32 | `project_remove_autoload` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 33 | `project_search_file_contents` | both | 12 | 12 | 11 | 1 | 12/12 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 34 | `project_search_file_names` | both | 12 | 12 | 11 | 1 | 12/12 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 35 | `project_set_node_property_across_scenes` | both | 18 | 18 | 1 | 1 | 18/18 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 36 | `project_set_setting` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 37 | `project_set_theme_color` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 38 | `project_set_theme_constant` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 39 | `project_set_theme_font_size` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 40 | `project_set_theme_stylebox` | both | 6 | 6 | 5 | 1 | 6/6 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 41 | `project_validate_script` | both | 18 | 18 | 3 | 15 | 18/18 | **pass** | `runs/_exercises/ex_files/c1-task110` |
| 42 | `project_write_text_file` | both | 7 | 7 | 6 | 1 | 7/7 | **pass** | `runs/_exercises/ex_files/c1-task110` |

小计：**42/42** 通过批次门。

### B6. 家族② 逐工具结果（编辑器读取族）

**家族②（16 个目标）**（判据来自 `tools/verify_coverage_batch.py` 对 `coverage.json` 的实测；`本批` 列只数练习轮的调用，`累计` 列含此前的历史轮）

| # | tool | scope | 本批 | 累计 | 有效 | 边界 | facts | 判定 | 证据（主 run） |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `editor_analyze_signal_flow` | editor | 12 | 12 | 8 | 4 | 12/12 | **pass** | `runs/_exercises/ex_scene/c23-task110` |
| 2 | `editor_execute_gdscript` | editor | 12 | 12 | 10 | 2 | 12/12 | **pass** | `runs/_exercises/ex_scene/c23-task110` |
| 3 | `editor_find_nodes_by_type` | editor | 12 | 12 | 10 | 2 | 12/12 | **pass** | `runs/_exercises/ex_scene/c23-task110` |
| 4 | `editor_find_nodes_in_group` | editor | 12 | 12 | 10 | 2 | 12/12 | **pass** | `runs/_exercises/ex_scene/c23-task110` |
| 5 | `editor_get_collision_info` | editor | 12 | 12 | 8 | 4 | 12/12 | **pass** | `runs/_exercises/ex_scene/c23-task110` |
| 6 | `editor_get_input_actions` | editor | 12 | 12 | 10 | 2 | 12/12 | **pass** | `runs/_exercises/ex_scene/c23-task110` |
| 7 | `editor_get_node_groups` | editor | 12 | 12 | 10 | 2 | 12/12 | **pass** | `runs/_exercises/ex_scene/c23-task110` |
| 8 | `editor_get_node_properties` | editor | 12 | 68 | 55 | 11 | 68/68 | **pass** | `runs/_exercises/ex_scene/c23-task110` |
| 9 | `editor_get_node_signals` | editor | 12 | 12 | 10 | 2 | 12/12 | **pass** | `runs/_exercises/ex_scene/c23-task110` |
| 10 | `editor_get_open_scripts` | editor | 12 | 12 | 10 | 2 | 12/12 | **pass** | `runs/_exercises/ex_scene/c23-task110` |
| 11 | `editor_get_output_log` | editor | 12 | 12 | 12 | 0 | 12/12 | FAIL | `runs/_exercises/ex_scene/c23-task110` |
| 12 | `editor_get_performance_monitors` | editor | 12 | 12 | 10 | 2 | 12/12 | **pass** | `runs/_exercises/ex_scene/c23-task110` |
| 13 | `editor_get_physics_layers` | editor | 12 | 12 | 6 | 6 | 12/12 | **pass** | `runs/_exercises/ex_scene/c23-task110` |
| 14 | `editor_get_scene_tree` | editor | 12 | 83 | 50 | 0 | 83/83 | FAIL | `runs/_exercises/ex_scene/c23-task110` |
| 15 | `editor_get_selection` | editor | 12 | 12 | 10 | 2 | 12/12 | **pass** | `runs/_exercises/ex_scene/c23-task110` |
| 16 | `editor_list_signal_connections` | editor | 12 | 12 | 5 | 4 | 12/12 | **pass** | `runs/_exercises/ex_scene/c23-task110` |

小计：**14/16** 通过批次门。

### B7. 家族③ 逐工具结果（运行期查询族）

**家族③（9 个目标）**（判据来自 `tools/verify_coverage_batch.py` 对 `coverage.json` 的实测；`本批` 列只数练习轮的调用，`累计` 列含此前的历史轮）

| # | tool | scope | 本批 | 累计 | 有效 | 边界 | facts | 判定 | 证据（主 run） |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `running_game_capture_frames` | game | 12 | 12 | 0 | 2 | 10/12 | FAIL | `runs/_exercises/ex_scene/c23-task110` |
| 2 | `running_game_capture_signal_emissions` | game | 12 | 12 | 0 | 2 | 10/12 | FAIL | `runs/_exercises/ex_scene/c23-task110` |
| 3 | `running_game_find_nearby_nodes` | game | 12 | 12 | 10 | 2 | 12/12 | **pass** | `runs/_exercises/ex_scene/c23-task110` |
| 4 | `running_game_find_nodes_by_script` | game | 12 | 12 | 10 | 2 | 12/12 | **pass** | `runs/_exercises/ex_scene/c23-task110` |
| 5 | `running_game_find_ui_elements` | game | 12 | 12 | 10 | 2 | 12/12 | **pass** | `runs/_exercises/ex_scene/c23-task110` |
| 6 | `running_game_get_autoload_node` | game | 12 | 12 | 10 | 2 | 12/12 | **pass** | `runs/_exercises/ex_scene/c23-task110` |
| 7 | `running_game_get_node_properties` | game | 12 | 52 | 48 | 2 | 52/52 | **pass** | `runs/_exercises/ex_scene/c23-task110` |
| 8 | `running_game_get_node_properties_batch` | game | 12 | 12 | 10 | 0 | 12/12 | FAIL | `runs/_exercises/ex_scene/c23-task110` |
| 9 | `running_game_simulate_button_click_by_text` | game | 12 | 12 | 2 | 2 | 12/12 | **pass** | `runs/_exercises/ex_scene/c23-task110` |

小计：**6/9** 通过批次门。

三个 setup-only 工具（`editor_connect_signal` 4 次、`editor_set_node_groups` 4 次、`editor_setup_collision_shape` 2 次）在批次里只作前置，**不算目标**；它们顺带从 0 次变成可达证据，下一批补到 ≥5 即可（见 §E）。


---

## E. 剩余 `<5` 清单与下一步批次建议

**登记为不可达的 68 条**：H2 动画/AnimationTree（14）、H7 编辑器 GUI 剩余（15）、H3 TileMap/GridMap（7）、H1 3D（7）、H4 导航（6）、H5 音频（6）、H6 粒子（5）、H8 导出/Android（5）、H9 录放（3）。这份清单**现在有 6 条已被证明是错的**，所以它的其余成员值得按同样办法抽查一遍 —— 尤其 H7/H9（错得最集中的两类）。

**可达但本轮没排到的 20 条**（下一批的直接目标，全部在编辑器端点）：

* 节点生命周期写族（8）：`editor_add_node`、`editor_add_scene_instance`、`editor_add_raycast`、`editor_add_resource_to_node_property`、`editor_duplicate_node`、`editor_rename_node`、`editor_reparent_node`、`editor_disconnect_signal` —— **不需要任何新子系统**，一个开着的场景就够，且 `editor_connect_signal` 已有 4 次（差 1 次）可一并补齐。
* 属性/分组/脚本写族（4）：`editor_set_node_property_batch`、`editor_set_node_property_updates`、`editor_set_node_script`、`editor_set_node_groups`（已有 4 次）。
* 物理/主题/着色器接线（5）：`editor_setup_physics_body`、`editor_setup_collision_shape`（已有 2 次）、`editor_set_physics_layers`、`editor_set_control_theme`、`editor_set_anchor_preset`。
* 着色器（2）：`editor_set_shader_material`、`editor_set_shader_param`。
* 外加 B4 的 3 条待补证据：`running_game_capture_frames` / `capture_signal_emissions`（补一条**规则澄清**：`capture` 动词的生效证据就是它的载荷）与 `running_game_get_node_properties_batch`（补类型探针）、`editor_get_output_log` / `editor_get_scene_tree`（补类型探针）。

**批次 2 建议（按收益/成本排序）**：①节点生命周期写族 9 条（一个会话、约 60 次调用，无需新子系统）；②B4 的 5 条补证据（约 30 次调用）；③属性/物理/主题写族 11 条；④然后才碰 H2/H4/H5/H6 —— 那些真要新建子系统（AnimationPlayer、NavigationRegion+烘焙、AudioBus、GPUParticles），成本量级不同，应先按 D5 的教训**逐个证伪「不可达」推断**再决定。

**方法建议**：把本轮抓 D1 的那类探针**系统化** —— 契约 177 条的 `inputSchema.properties` 与注册 schema 做一次**成员级**对照（本轮只对 25 条目标做了调用侧探测，就抓到 1 条阻塞 + 4 条不符）。这正是 `REPORT-052` §A7 猜过、而 TASK-108 §6.8 明说自己没做的那件事（「没有核对调用参数/schema 是否符合契约」）。

---

## F. 如实声明：本轮**没有**做的事

* **没有**核对全部 177 条的参数/响应是否符合契约：只在 3 个族 25 个目标上做了调用侧探测（这已足够抓到 D1）。成员级全量对照见 §E 的建议。
* **没有**修 D2–D5 与 D6–D8：逐条给了证据、根因与补丁落点，**没有动一行引擎代码**（C1 之外）。
* **没有**碰 20 款正式工程与它们的历史 `runs/`：只读；练习轮一律写在 `runs/_exercises/` 与 `projects/_exercises/`（`projects/pong` 是我复制练习工程时的**源**，其本身零改动）。
* **没有**把 `running_game_capture_*` 的「生效」规则改成对它们有利：台账宁可显示「计数达标缺证据」，也不为了让数字好看而放宽判定。
* **没有**给 `runs/` 入库存档：`.gitignore` 第 43 行把 `godot-mcp/runs/` 按既有政策排除，所以本报告引用的 trace/ledger 只留在盘上（路径如上），入库的是工具、会话、清单与台账。
