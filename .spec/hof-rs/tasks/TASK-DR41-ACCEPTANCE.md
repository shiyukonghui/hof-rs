# TASK-DR41-ACCEPTANCE — 批次一（离线契约迁移）独立验收报告

> 验收者：独立验收子代理（无上游对话上下文，未继承实现者/调度者任何结论）。
> 验收对象：外层仓 `F:\moonbit-hof-rs`，`master`，HEAD = `9218516`（DR 提交区间 `b6d9282..b2ed193`）。
> 权威依据：`DESIGN-DETAIL.md` §13（DR-41..DR-47）、`REQUIREMENTS.md` §3 C3/C4/C5 + §10、
> `DECISIONS.md` D216/D217、`TASK-DR41-ACCEPT.md`（§3 清单、§3.7 受控实验、§5 结构化结论）、
> `TASK-DR41-ACCEPT-ADDENDUM.md`（**优先**，六条裁定 + D217 历史纪律）。
> 实现者报告仅作线索，未作为任何一条判定的证据；下文所有证据均为本人亲手复现。

**结论：`pass`（无 blocker/major；§3.7 证明守卫非空洞；无导致语义漂移的未声明行为变更）。
附 4 条 minor/info 缺陷，详见 §5。**

---

## 1. 结论与 `cargo test` 真实输出 / 退出码

本人执行（离线，未启动 Godot、未探测端口、未联网、未调模型端点）：

```
$ cargo test --offline
...
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s   (Doc-tests hof_rs)
EXITCODE=0
```

- **34** 个 test target，逐行解析 `test result:` 汇总：**passed=300, failed=0, ignored=7**，
  非 `ok` 结果 **0** 条，进程退出码 **0**。
- 7 个 `ignored` 全部来自 `tests/godot_smoke.rs`（`e0_*..e6_*`，DR-9 的 `#[ignore]` + `HOH_SMOKE=1` 门控，
  本批未运行）。其余 33 个 target 无 `#[ignore]`、无新增跳过。
- 与实现者报告所称「exit 0、0 failed、7 ignored」**一致**；报告未虚报。
- `tests/tool_vocabulary.rs` 的 4 条用例确实被执行（见 §3.7），不是 `#[ignore]`。

---

## 2. 逐条清单对照（我的命令 → 真实输出 → 判定）

### 2.1 §3.6 全局

| 项 | 我的命令 | 真实输出 | 判定 |
|---|---|---|---|
| `cargo test` | `cargo test --offline` | 34 targets / 300 passed / 0 failed / 7 ignored / EXITCODE=0 | **pass** |
| PRD 未改 | `Get-FileHash .spec\hof-rs\PRD-mario.md -Algorithm SHA256` | `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`（5375 B） | **pass** |
| `godot-mcp/**` 未改 | `git diff b6d9282~1..HEAD --stat -- godot-mcp/` | `(empty)` | **pass** |
| 同上（宽区间复核） | `git diff e8461bf..HEAD --stat -- godot-mcp/` | 6 个文件（`recovery/reports/TASK-150-REPORT.md` 等 894 行）——逐条追责：全部由**本批之前**的 `9000518 chore(recovery)…` 引入；`git show --stat 9000518` 与之一一对应。**不属本批违规** | **pass** |
| `runs/**`/`.workspace/**`/`config/*secret*` 未入库 | `git log e8461bf..HEAD --name-only --pretty=format:` 过滤 | `(empty)` | **pass** |
| 未 push | `git rev-parse origin/master` | `4b9bd44054ccfefdb4b96a342a133a4896769b76`（本批前位） | **pass** |
| 提交边界 | 逐条 `git show --stat` | 7 条提交信息均带 DR 编号；DR-41=11 文件、DR-42=29、DR-43=7、DR-44=12、DR-45=1、报告=1、D217=3。各提交含的路径与自身 DR 主题一致 | **pass**（见 §2.6 的小保留） |

### 2.2 §3.1 DR-41

| 项 | 我的证据 | 判定 |
|---|---|---|
| 模板不含 `[editor_plugins]`；`config/features=("4.8")` | `src/adapter/godot.rs:47-82` 通读：第 54 行 `config/features=PackedStringArray("4.8")`，全文无 `[editor_plugins]` 段；配套单测 `the_project_template_drops_the_gdextension_channel` 通过 | **pass** |
| `initialize()` 不再复制 addon / 不再写 `ADDON_MISSING.txt` | `godot.rs:2654-2684` 通读：既有工程分支只做反向清理；新工程分支只写 `PROJECT_GODOT`/`main.tscn`/`README`。`grep ADDON_MISSING src` 仅剩测试断言（要求**不存在**） | **pass** |
| **既有工作区清理（本人自造临时工程，端到端真跑 `initialize`）** | 本人构造 `%TEMP%\dr41ws\mario`：`addons/godot_mcp_rs/`（2 文件）+ `.godot/extension_list.cfg`（**3 行**，含 addon 行）+ `.godot/subdir/other_cache.keep` + `addons/other_plugin/`、`addons/third_plugin/` + `project.godot` 的 `enabled=PackedStringArray("…other_plugin…","…godot_mcp_rs…","…third_plugin…")`，执行两次 `target\debug\hoh.exe init --project <ws>`（真实二进制，非仓库内改动） | **pass** |
| (a) addon 目录被删 | AFTER-1：`addons/godot_mcp_rs/godot_mcp_gdext.dll`、`plugin.cfg` 均消失 | **pass** |
| (b) cache 中 addon 行消失、其它行逐字保留 | `extension_list.cfg` 由 138 B → 87 B（恰好 −51 B = 被删那一行的字节数），内容为 `res://addons/someone_else/other.gdextension` + `res://addons/third_thing/third.gdextension` 两行**原样** | **pass** |
| (c) 其它插件名逐字保留 | `project.godot` 由 `enabled=PackedStringArray("…other_plugin/plugin.cfg", "…godot_mcp_rs/plugin.cfg", "…third_plugin/plugin.cfg")` 变为 `…("res://addons/other_plugin/plugin.cfg", "res://addons/third_plugin/plugin.cfg")`——两个名字与分隔符逐字不变 | **pass** |
| (d) 列表变空 → 整段移除 | 另建 `%TEMP%\dr41ws\empty`（addon 为唯一项）：`[editor_plugins]` 段整体消失、`config/name="x"` 保留、`.godot/extension_list.cfg` **被删除**、`.godot/` 目录保留 | **pass** |
| (e) 幂等（字节 hash 对比） | 第二次运行后各文件 sha256 与第一次**完全相同**（`project.godot` = `75cedadf…`、`extension_list.cfg` = `620ac9a7…`、两个 `keep.txt` 与 `other_cache.keep` 亦不变） | **pass** |
| 反向：不得误删其它 addon / 不得删 `.godot` | `addons/other_plugin/keep.txt`、`addons/third_plugin/keep.txt`、`.godot/subdir/other_cache.keep` 全程 hash 不变；`.godot` 与 `addons` 目录保留 | **pass** |
| `grep -rn addon_source src tests config` → 0 | `Select-String -Recurse src,tests,config -Pattern addon_source` → `COUNT=0` | **pass** |

### 2.3 §3.2 DR-42

| 项 | 我的证据 | 判定 |
|---|---|---|
| 夹具 177 条 + 四通道正则 | 自写 Python 解析：`result.tools` 长度 **177**，正则 `^(editor\|project\|running_game\|os)_[a-z0-9_]+$` 违例 **0**；通道分布 editor 104 / project 48 / running_game 23 / os 2；无重名 | **pass** |
| 形状未被破坏 / `inputSchema` 未截断 | 与 `tools_list.renamed.json` **逐工具、逐字段**比对：字段差异 **0 条**；名字集合相等且**顺序相同**；`cargo test --offline` 中 `McpClient::list_tool_schemas`/`tools::index` 相关用例全部通过 | **pass** |
| 与 renamed.json 名字集合差集为空 | `in fixture not source = []`，`in source not fixture = []` | **pass** |
| 夹具相对源文件的多/少键（**addendum §1.3①**） | 工具对象键集合：`fixture-only tool keys = []`、`source-only tool keys = []`——**无任何夹具专用字段**。唯一差异是源文件的**顶层** `_meta` 键被丢弃（源顶层键 `{_meta,id,jsonrpc,result}`，夹具 `{id,jsonrpc,result}`） | **pass** |
| `PROVENANCE.md` 存在且 sha256 与我算的一致 | 文件 1628 B；其中 `fixture sha256 = 50c5fb42…`，我独立算得 `50c5fb4204ee5b957b017eb994e7f7bd73f9b299e6aa9471d5cf11683e067da0`（71481 B，**无 BOM**，末字节 `}`）；其中 `source sha256 = fd00c75e…`，我算得 `fd00c75e5174ec923d5a91c0323afa0804f523b385eae3d4f78d8c71e1f895df`（154272 B） | **pass** |
| 抽样 ≥10 条映射一致（含 GDR-17、含禁用 `update_`） | 我的抽样 12 条（`旧名 → 新名`，括号内为「b6d9282~1 旧名出现次数 / 当前 新名出现次数」）：`get_project_info→project_get_info`(14/20)、`play_scene→editor_play_scene`(36/57)、`get_editor_errors→editor_get_errors`(42/47)、`capture_frames→running_game_capture_frames`(20/19)、`monitor_properties→running_game_get_node_property_samples`(32/31)、**`update_property→editor_set_node_property`(1/4)**、**`get_editor_performance→editor_get_performance_monitors`(1/1，GDR-17 merge_into)**、`tilemap_get_info→editor_get_tilemap_info`(1/1)、`simulate_action→editor_simulate_input_action`(33/33)、`get_game_scene_tree→running_game_get_scene_tree`(32/42)、`export_project→project_export_game`(3/0，unregister)、`navigate_to→running_game_move_player_to_target_via_navigation`(3/0，unregister)。另做**全量完备性**核对：174 条中「旧名在 b6d9282~1 出现过、但新名在当前树中缺席」的条目 **0 条**；当前树使用到的新名 **172/174**（缺席的 2 条即上面两个 `unregister_until_implemented`）。全部新名均由 `tool-rename-map.json` 逐条读出，非报告转述 | **pass** |
| 旧名集合零命中（`src/**`、`tests/**`、`src/prompts/**`） | 自写扫描：**不依赖**守卫的 `SCANNED_SUFFIXES`，对 `src/`、`tests/`、`config/` 下**所有**可解码文件（99 个）做整词匹配，旧名集合取自 rename map 的 174 条 `old_name`。命中文件**仅 1 个**：`tests/tool_vocabulary.rs`（守卫自身必须写出旧词汇，属设计排除）。**排除理由**：`godot-mcp/**` 是只读嵌套仓（引擎侧事实源，不改不扫）；`.spec/**`、`runs/**` 是历史证据与文档，不属迁移对象 | **pass** |
| 角色作用域：Planner 对任一新契约写工具 `false` | 自跑 `cargo test --offline --test tools_policy` → `12 passed; 0 failed`。读源：`tests/tools_policy.rs:163 planner_is_denied_every_tool_of_the_contract` 遍历 `contract_names()`（全部 177 条）断言 `!tool_allowed(Planner,..)`；`src/runtime/policy.rs:283 Role::Planner => false` | **pass** |
| QA 对任一新契约写工具 `false`；Developer 对代表性写工具 `true` | 同上测试运行通过。读源：`qa_is_denied_every_mutating_tool_of_the_contract` 取契约中所有 `is_mutating` 名字（断言 `>50`）并断言 Tester 全拒，且「可达写动词名字数 == `QA_ALLOW_EXACT` 长度 == 2」；`Role::Developer => true`；`developer_allowed_all` 通过 | **pass** |

### 2.4 §3.3 DR-43

| 项 | 我的证据 | 判定 |
|---|---|---|
| 双端点：`running_game_*` 只出现在游戏端点 | 自跑 `cargo test --offline --test dual_endpoint` → `6 passed; 0 failed`。读源 `tests/dual_endpoint.rs:164-228`：两个 loopback JSON-RPC 假端点；未登记时该调用报 `game_endpoint_unavailable` 且两端点收到数均为 0；登记后 `running_game_get_scene_tree` 只出现在游戏端点 | **pass**（测试为实现者所写，由我执行；见 §6） |
| 编辑器端点从未收到 `running_game_*` | 同上测试第 211-217 行断言 `!editor.tools().iter().any(|t| t.starts_with("running_game_"))`；另有 `editor.tools() == ["editor_get_errors"]`。实现侧 `src/tools/mod.rs:157 client_for` 按 `scope_of` 选端点，`None` 时 `bail!`（**禁止回退**） | **pass** |
| `editor_play_scene` 缺端口信息 → 该步失败（非静默回退） | `tests/dual_endpoint.rs:443-484`：回复为旧形态 `{"mode":"main","playing":true}` 时 `play_scene_ready.ok == false`，observation 含 `mcp_port`/`endpoint` 与 `UNAVAILABLE`，且注册器收到 **0** 次登记；实现 `godot.rs:837-865` 登记失败即 `finish(..., false, ...)` | **pass** |
| `stop_scene` 后 `running_game_*` 报错且不打旧端口 | `tests/dual_endpoint.rs:230-270`：`clear_game_endpoint` 后报 `game_endpoint_unavailable`，游戏端点收到请求数仍为 1（未增加）；实现 `godot.rs:1884-1892` 在 stop 后无条件 `clear_game_endpoint()` | **pass** |
| `mcp_port_source` 被如实记录 | 实现 `godot.rs:1962-1968`；测试 `dual_endpoint.rs:280-302` 断言 `argument` / `auto_free_port` 逐字记录 | **pass** |

### 2.5 §3.4 DR-44

| 项 | 我的证据 | 判定 |
|---|---|---|
| `config/hoh.yaml` 有 `adapter.godot.editor_binary`，绝对路径，文件真实存在 | `config/hoh.yaml:43` = `F:/moonbit-hof-rs/godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe`；`Test-Path` → `True`，size **194207744** B | **pass** |
| `hof doctor` 两项**真实执行**并贴原始输出 | **我不会启动 Godot 二进制**（禁用项）。故用等价的真实可执行体做**真机式**验证：`hoh doctor -c adapter.godot.editor_binary=C:/Users/wyl/.cargo/bin/rustc.exe -c model.base_url=http://127.0.0.1:1/v1 -c tools.endpoint=http://127.0.0.1:1/mcp`（仓库自身离线测试所用的 `127.0.0.1:1` 模式，无外网、无 Godot），真实输出：<br>`[ok] godot.engine_binary: C:/Users/wyl/.cargo/bin/rustc.exe (size 12814336 B, mtime 1774138722)`<br>`[ok] godot.engine_version: rustc 1.98.0 (88d9e12ae 2026-08-18)`<br>⇒ 两项确实执行了 `<binary> --version` 并把版本串**逐字**记录，且**未硬编码** Godot 版本（换成 rustc 得到 rustc 的版本串，C12）；退出码 4（离线外部依赖不可用，符合 §8） | **pass（以替身二进制）**；对**配置的那支 Godot 二进制**的运行按规定**未做**（见 §4） |
| `meta.json.engine` 字段齐全；缺值 `null` + `reason` | `tests/engine_identity.rs:204` `ENGINE_KEYS = [kind,binary,version_string,version_reason,mcp,listener,checked_at]`，三处断言键集合完全一致；`a_missing_binary_is_null_plus_a_reason_never_a_guess` 断言 `binary.path==null`、`binary.reason` 为字符串、`version_reason` 为字符串、`listener.reason` 为字符串；`an_unavailable_engine_is_still_a_complete_block` 同样断言完整键集。自跑 `--test engine_identity` → `13 passed; 0 failed` | **pass** |
| `engine_identity` 闸门：匹配→过 / 不匹配→失败 / 探针读不到→失败，且 observation 可区分后两者（**addendum §1.6**） | **本人另写独立探针**（`%TEMP%` 编译，链接 `target\debug\libhof_rs.rlib`，直调公共 API，零仓库改动）构造四种 `EngineIdentity` 并调 `gate_record`：<br>`MATCH (Some(true))  -> ok=true  observation=the process listening on the editor port is the configured engine binary C:\engine\godot.exe (pid 4242)`<br>`MISMATCH (Some(false)) -> ok=false observation=FAILED engine identity: configured binary C:\engine\godot.exe \| actual listener C:\Other\godot.exe (pid 4242) \| engine identity mismatch: … (UNAVAILABLE: … , DR-44)`<br>`UNREADABLE (None + reason) -> ok=false observation=… \| no TCP listener on port 9877 could be read from \`netstat -ano -p tcp\` (UNAVAILABLE…)`<br>`UNREADABLE (None + 无 reason) -> ok=false observation=… \| the listener could not be compared (UNAVAILABLE…)`<br>⇒ 三情形齐备，后两者 observation **可区分**；错误信息同列「配置的二进制 / 实际监听者路径 / PID」。代码一致：`engine.rs:512 let ok = listener.matches_binary == Some(true);` | **pass**（但仓库内**无**该第三情形的测试，见 DEF-3） |
| 无新增 crate 依赖 | `git diff e8461bf..HEAD --stat -- Cargo.toml Cargo.lock` → `(empty)` | **pass** |
| 密钥卫生覆盖 `engine` 新键 | `tests/secret_hygiene.rs:93` 注入 `EngineIdentity::unavailable("not probed")`；`:109-113` 断言 `kind/binary/version_string/mcp/listener/checked_at` 六键存在；`:116` 断言 `engine` 串不含假密钥。自跑 `--test secret_hygiene` → `2 passed; 0 failed` | **pass** |

### 2.6 §3.5 DR-45 + §3.7 非空洞性

见 §7（受控实验完整原始输出）。摘要：守卫**确实被执行**（`--test tool_vocabulary` 4 用例，非 `#[ignore]`），
且植入旧名后**真实变红**（exit 101，指名 `src/adapter/godot.rs: play_scene`）⇒ **非空洞**。
守卫的 `OLD_VOCABULARY`（174 条）与我从 `tool-rename-map.json` 独立提取的 `old_name` 集合**双向差集皆空**，
不是一份残缺或抄错的名单。

### 2.7 §3.6 提交边界的小保留（不影响判定）

`b6d9282`（DR-41）在 `src/config.rs` 里把 `addon_source` 字段换成 `editor_binary`（该字段属 DR-44）。
这是**同一结构体字段替换**的必要编译期管线：DR-41 要求删除 `addon_source`，若不同时给出替代字段，
该提交无法编译。DR-44 提交只补 `config/hoh.yaml` 的 4 行与实现，字段本身诞生于 DR-41 提交。
判为 **info，不构成内容与 DR 编号不符**（`git show --stat` 内容与 DR-41 主题一致，无内容丢失）。

---

## 3. 反例清单（我构造了什么 → 观测到什么 → 是否推翻实现者说法）

| # | 反例 | 观测 | 结论 |
|---|---|---|---|
| R1 | **守卫非空洞**：把 `godot.rs:823` 的真实调用 `self.call("editor_play_scene", …)` 临时改回 `self.call("play_scene", …)` | `tool_vocabulary` 变红：`the_retired_vocabulary_is_gone` panicked，`the retired GDExtension-era vocabulary still appears in 1 place(s) (DR-45): src/adapter/godot.rs: play_scene`，`test result: FAILED. 3 passed; 1 failed`，退出码 101 | **不推翻**；守卫有效（§7） |
| R2 | **守卫漏检边界**（addendum §1.4）：新建 `src/legacy_probe.sh`，含 `play_scene`（两处） | `cargo test --offline --test tool_vocabulary` → `4 passed; 0 failed`，`MISS_PROBE_EXIT=0`（**绿**） | 证实守卫的已知假阴性边界：`SCANNED_SUFFIXES = [.rs .md .json .yaml .yml .toml .txt]` 之外的后缀、以及 `src/`+`tests/` 之外的目录（如 `config/`）不被扫描。调度者已裁定采纳（宁严勿松），故不算缺陷 |
| R3 | **清理逻辑的畸形输入**：`project.godot` 的 `[editor_plugins]` 段写成 `enabled=true`（无括号） | `hoh init` 后整段被删，文件只剩 `config_version=5\n\n` | **部分推翻**「无该段或本无该项时逐字节不改」的鲁棒性——见 DEF-2（minor，真实 Godot 工程不可达） |
| R4 | **幂等性**（§3.1(e)）：同一临时工程连续 `init` 两次 | 6 个文件 sha256 全部不变 | 实现者说法成立 |
| R5 | **反向误删**：临时工程里放 `addons/other_plugin/`、`addons/third_plugin/`、`.godot/subdir/other_cache.keep` | 全程 hash 不变；`.godot/`、`addons/` 目录保留 | 实现者说法成立 |
| R6 | **端点污染 / 缺端口**（§3.3） | `dual_endpoint` 6/6 绿：编辑器端点从未收到 `running_game_*`；缺端口时步骤 `ok=false` 且零登记 | 实现者说法成立 |
| R7 | **`mcp_port_source` 三取值**（addendum §1.5）：自写探针喂入 5 种输入 | `argument→"argument"`、`auto_free_port→"auto_free_port"`、**字段缺失→"undeclared"**、**未知取值→"undeclared"**、仅有 `endpoint`→`"undeclared"` | 实现者说法成立：只在看不到该字段（或值不可识别）时用 `undeclared`，拒绝编造 |
| R8 | **闸门第三情形**（addendum §1.6）：自写探针构造 `matches_binary=None` | `ok=false`，observation 与 mismatch 明显不同 | 实现者说法成立（**但仓库内无对应测试**，DEF-3） |
| R9 | **C12 版本串自由度**：把 `editor_binary` 指向 `rustc.exe` 跑 `hoh doctor` | `godot.engine_version: rustc 1.98.0 (88d9e12ae 2026-08-18)`；`src/**` 全文搜索 `4.8.dev`/`ba1587c71`/`custom_build` → **0 命中** | 实现者说法成立：版本串只记录、非判据 |
| R10 | **QA 放宽面全量复算**：用 Python 把**旧前缀规则**与**新四通道+动词规则**在 174 条上逐条重演 | 差异**恰好 5 条**，全部「旧拒 → 新放」，动词 `get/get/get/get/capture`，`map.mutating` 均为 `false`；无任何写工具被放宽 | 实现者说法成立（addendum §1.1） |
| R11 | **被放宽的 5 条是否曾被测试断言拒绝**：`git grep -w <5 个旧名> b6d9282~1 -- '*.rs'` | 5 条全为 `NONE` | addendum §1.1 的「无既有断言被削弱」成立 |
| R12 | **Planner 断言是否被削弱**：抽取 pre/cur 的 `planner_denied_all_mcp` 函数体、`runtime_semantics.rs::planner_cannot_write_artifact` | **逐字节相同**；另新增更强的 `planner_is_denied_every_tool_of_the_contract`（遍历全部 177 条） | addendum §1.2 成立 |
| R13 | **`tool_discovery` 断言改法是否属放宽**（报告 §5(j) 自曝项） | 自验：`editor_add_node` 确实出现在**允许工具** `editor_get_scene_tree` 的 description 里（夹具内检索），旧写法（整篇子串）在新契约下必假阳；新写法检查条目标题 `### \`name\``，而 `src/tools/index.rs:182` 正是以 `### \`{name}\`` 生成条目 ⇒ 形式化正确，**非放宽** | 实现者说法成立 |
| R14 | **活体核对**（addendum §1.3④） | **未做**（离线批次；见 §4） | 不推翻，但不得读成已核 |
| R15 | **未声明的标识符改名**：全量对比 `BatteryStep` 的 `id` 字面量 | `stop_scene` → `editor_stop_scene`（唯一变化），并已同步到 `tests/evidence_battery.rs:649`、`tests/mcp_desync.rs:378`、`godot.rs` 的 playbook 表——全仓无遗留 `"stop_scene"` 期望（除守卫自身） | 内部自洽；但报告未逐条点名 ⇒ DEF-1（minor） |

---

## 4. 未验证项与理由（**不得默认成立**）

1. **配置的那支 Godot 二进制上真实跑 `hof doctor` 两项**：未做。`<binary> --version` 会**启动引擎二进制**，
   与本次验收「不启动 Godot」的硬约束冲突。我改用真实可执行体 `rustc.exe` 完成了同一条代码路径的真机执行（§2.5），
   并独立确认配置路径存在（194207607 字节）。**「配置的 mono 构建返回 `4.8.dev.mono.custom_build.ba1587c71`」属推断，未实测。**
2. **活体 `tools/list` 与夹具逐字一致**：未做，属 DR-47 批次二（离线批次无法证明）。
   夹具的权威性来自仓库内 `tools_list.renamed.json`，不是活体事实。
3. **真实 `netstat -ano -p tcp` / `powershell (Get-Process).Path` 输出形态**：未执行任何探针（离线 + 禁端口探测）。
   解析器只被人工构造的表格覆盖。
4. **`meta.json.engine.mcp.editor_status` 的真实 `GET /mcp` 响应体**：未做（离线恒为空对象 + reason）。
5. **游戏端点 23 个 game-only 工具的真实可达性**：本批只证明 hof-rs **不会**把 `running_game_*` 打到编辑器端点。
6. **`.workspace/mario` 的真实工作区清理**：未在该目录执行 `init`（它是活动工作区，且我不改仓）。
   但 `hoh doctor` 已如实报出该目录**仍**带 `addons/godot_mcp_rs/` 与 `.godot/extension_list.cfg`（见 §5 风险）。
   我对**自造临时工程**完成了端到端清理与幂等验证（§2.2）。
7. **`godot-mcp/recovery/TEST-CASES.md` 的 177 条 `TC-TOOL-*` 语义逐条比对**：未做（本批判据不含，且属引擎侧只读文档）。

---

## 5. 缺陷清单（含严重度与复现步骤）

| id | 严重度 | 内容 | 复现 | 影响 |
|---|---|---|---|---|
| **DEF-1** | minor | **确定性证据标识符被守卫的整词匹配牵连改名**：`BatteryStep` 的 id `"stop_scene"` → `"editor_stop_scene"`。它**不是**工具调用，是电池步 id；守卫第 2 条把它当旧词汇。报告 §5(k) 只在位置清单里笼统提过「BatteryStep 表」，未点名这条标识符级改名 | `git show b6d9282~1:src/adapter/godot.rs \| Select-String 'id: "stop_scene"'` 有命中；当前树 `id: "editor_stop_scene"`。全仓 `"stop_scene"` 现仅存在于守卫自身 | 改变 `.hoh/deterministic/battery.json` 的 `step_id` 与 `raw/<step>.json` 文件名。仓库内所有消费点已同步（含 prompt 的 playbook 表），无悬空引用；但**跨批次比较**旧轮次的 battery 证据时要注意。属「守卫对非工具标识符的假阳性压力」，与 §3.7 第 6 条要求上报的「误报」同类 |
| **DEF-2** | minor | **畸形 `enabled=` 行使整段 `[editor_plugins]` 被删**：`packed_string_array_without` 对无括号的行返回 `None`，而 `None` 被 `ensure_bundled_addon_disabled` 解释为「列表变空 ⇒ 删整段」 | `%TEMP%` 临时工程写 `project.godot = "config_version=5\n\n[editor_plugins]\n\nenabled=true\n"`，跑 `hoh init`，文件变为 `config_version=5\n\n`（整个段消失） | 会静默移除一个它无法解析的插件段（可能连带别人的插件项）。标准 Godot 工程的 `[editor_plugins]` 只写 `enabled=PackedStringArray(...)`，实际不可达；但设计书只说「无该段/本无该项则逐字节不改」，此分支未声明。建议：解析失败时**不改动**并写入一条 reason |
| **DEF-3** | minor（覆盖缺口） | **两处 addendum 要求的情形在仓库内没有测试**：①`parse_game_endpoint` 的 `undeclared` 分支（`undeclared` 在 `*.rs` 中仅出现在 `src/`，无测试引用）；②`gate_record` 在 `matches_binary == None` 时关闸且 observation 区别于 mismatch（`gate_record(` 的调用点只有测试里的 match/mismatch 与「无二进制 ⇒ None」）。**行为我已用自写探针独立证实正确**（R7/R8），缺的是仓库内的回归保护 | `Select-String -Recurse src,tests -Pattern undeclared` → 无测试命中；`Select-String -Recurse src,tests -Pattern 'gate_record\('` → 无 None-matches 调用 | 未来重构可能悄悄破坏这两条已裁定的行为而不被测试发现 |
| **DEF-4** | info | **过时测试名**：`src/tools/index.rs:260 fn the_snapshot_is_the_real_174_tool_list`，夹具已是 177；断言本身是新契约安全的（`schemas.len() >= 100` + 存在 `editor_play_scene`），但名字会误导读者，且 `>= 100` 从不校验真实条数 | 读 `src/tools/index.rs:260-267` | 仅可读性/误导；不构成判据失效 |

**无 blocker、无 major。** §3.7 未证明守卫空洞；未发现夹带语义漂移的未声明行为变更
（批量改名处逐条查表，`git log -p` 逐提交阅读未发现非改名语义改动）。

---

## 6. 我没有独立复核的部分（诚实列账）

1. **DR-43 的双端点测试替身**（`tests/dual_endpoint.rs`）是实现者所写，我**执行**了它（6/6 绿）
   并核对了被测代码，但**没有另写一套独立的双端点假 MCP**。因此 DR-43 的判据属「我运行的证据 + 代码通读」，
   而非「我构造的证据」。DR-44 的 `mcp_port_source`/闸门三情形我另写了独立探针（R7/R8），不在此列。
2. **DR-44 的 `FakeEnv` 测试**（`tests/engine_identity.rs`）同理：我执行并通过，未另写 Environment 假体。
   但闸门与端口来源两条关键行为由我的独立探针覆盖。
3. **`hof doctor` 的其余非引擎项**（模型 chat 探测、驻留实例探测等）我只看到离线输出的一部分，未逐项复核。
4. **`godot-mcp/**` 语义**：我只确认本批未改动它，未审阅其内容正确性。
5. **报告 §3 的 174 条映射表逐行正确性**：我用**集合与全量出现次数**做了机器核对（0 例外），
   未对每一条做「输入/输出语义等价」的人工判定；语义变化项（`fix_implementation_first`、`merge_into`、
   `unregister_until_implemented`）我只核对了它们在 hof-rs 里的**使用面**（是否被调用、是否被替代）。
6. **`cargo build` 的 warning 数**：未单独跑（任务书 §3.6 只要求 `cargo test`）。

---

## 7. §3.7 受控实验 —— 完整三步原始输出

### 第 1 步：植入（一处，`src/`，选「守卫想抓的形态」= 真实工具调用）

改动前 `src/adapter/godot.rs:823`：

```rust
let play = self.call("editor_play_scene", play_args.clone()).await;
```

改后：

```rust
let play = self.call("play_scene", play_args.clone()).await;
```

```
$ git --no-pager diff --stat
 src/adapter/godot.rs | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
$ git --no-pager diff -- src/adapter/godot.rs
@@ -820,7 +820,7 @@ impl<'a> BatterySession<'a> {
         let play_args = json!({"mode": "main"});
         let mut calls = Vec::new();
-        let play = self.call("editor_play_scene", play_args.clone()).await;
+        let play = self.call("play_scene", play_args.clone()).await;
         match play {
```

### 第 2 步：只跑守卫 —— **必须红，实测红**

```
$ cargo test --offline --test tool_vocabulary
running 4 tests
test the_fixture_is_the_four_channel_contract ... ok
test the_guard_recognises_both_vocabularies ... ok
test the_retired_vocabulary_is_gone ... FAILED
test every_quoted_tool_name_exists_in_the_contract ... ok

failures:

---- the_retired_vocabulary_is_gone stdout ----
thread 'the_retired_vocabulary_is_gone' (113820) panicked at tests\tool_vocabulary.rs:302:5:
the retired GDExtension-era vocabulary still appears in 1 place(s) (DR-45):
src/adapter/godot.rs: play_scene

failures:
    the_retired_vocabulary_is_gone

test result: FAILED. 3 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.43s
PLANT_EXIT=101
```

⇒ 守卫**非空洞**：它按整词边界定位到具体文件与旧名，且因缺行为而失败（不是编译失败）。

### 第 3 步：回退 —— 恢复证明为**空**

回退采用「写回提交对象的精确字节」而非 `git checkout --`（原因：本仓 `core.autocrlf=true`，
`git checkout --` 会把该文件的工作区行尾从 LF 改成 CRLF；而实验证明 `edit` 工具**保留**原有行尾，
且植入时 git 曾告警 `LF will be replaced by CRLF`，据此判定该文件实验前工作区为 LF。

```
$ python -c "…git cat-file blob HEAD:src/adapter/godot.rs …"
blob sha256 = 2a962b5c8fa067f82a54d590309ef4804e68c30a8b9be4aaf31f0087bc34b2a1 len = 142511
current file sha256 = bab9798235dde97816e5281b1b03e751be79ea55e7a675944495a6be067ebb42 len = 146023
restored file sha256 = 2a962b5c8fa067f82a54d590309ef4804e68c30a8b9be4aaf31f0087bc34b2a1 len = 142511
EXACT RESTORE = True
```

**恢复证明（原始输出，均为空）：**

```
$ git status --porcelain
(empty)
$ git diff --stat
(empty)
$ git status --porcelain -uall
(empty)
$ git ls-files --eol -- src/adapter/godot.rs
i/lf    w/lf    attr/                 	src/adapter/godot.rs
$ (Get-Content src\adapter\godot.rs)[822]
        let play = self.call("editor_play_scene", play_args.clone()).await;
```

工作区行尾分布也回到实验前的形态：`w/lf = 66`、`w/crlf = 3`（实验中途因 `git checkout --` 曾一度为 65/4）。

### 附：addendum §1.4 要求的「漏检反例」（受控、已回退）

```
$ [System.IO.File]::WriteAllText("src\legacy_probe.sh", "#!/bin/sh`n# legacy launcher still calls play_scene`necho play_scene`n")
$ git status --porcelain
?? src/legacy_probe.sh
$ cargo test --offline --test tool_vocabulary
running 4 tests
test the_fixture_is_the_four_channel_contract ... ok
test the_guard_recognises_both_vocabularies ... ok
test the_retired_vocabulary_is_gone ... ok
test every_quoted_tool_name_exists_in_the_contract ... ok
test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.38s
MISS_PROBE_EXIT=0

$ Remove-Item src\legacy_probe.sh -Force
$ git status --porcelain
(empty)
$ git diff --stat
(empty)
```

⇒ 守卫在「未被扫描的后缀」上确实漏检。**被排除的文件**：`tests/tool_vocabulary.rs`（守卫自身）、
`tests/fixtures/mcp/tools_list.json`（契约夹具，`SCAN_EXCLUDES`）。**`SCANNED_SUFFIXES` 实际覆盖面**：
`.rs .md .json .yaml .yml .toml .txt`，且 walk 根只有 `src` 与 `tests`（`src/prompts/**` 因在 `src` 下被覆盖；
`config/` 不被守卫扫描——我已用自己的全后缀扫描补上：`config/` 内旧名 0 命中）。
补充：夹具虽被排除，但我实测其 `description` 散文**并不含**任何整词旧名，故该排除当前无实际损失。

---

## 8. 结构化结论（§5 要求的机器可读对象）

```json
{
  "verdict": "pass",
  "criteria": [
    { "id": "DR-41.1", "pass": true, "evidence": "src/adapter/godot.rs:47-82 通读：第54行 config/features=PackedStringArray(\"4.8\")，全文无 [editor_plugins]；cargo test --offline 的 lib target 中 the_project_template_drops_the_gdextension_channel ... ok" },
    { "id": "DR-41.2", "pass": true, "evidence": "godot.rs:2654-2684 通读：既有工程分支只做反向清理；新工程分支不复制 addon、不写 ADDON_MISSING.txt；lib target 中 initializes_a_minimal_project ... ok 且断言 !ADDON_MISSING.txt exists" },
    { "id": "DR-41.3a-addon-dir-removed", "pass": true, "evidence": "自造 %TEMP%/dr41ws/mario 跑两次 target/debug/hoh.exe init --project；AFTER-1 快照中 addons/godot_mcp_rs/godot_mcp_gdext.dll 与 plugin.cfg 均消失" },
    { "id": "DR-41.3b-cache-line-removed-others-verbatim", "pass": true, "evidence": "extension_list.cfg 138B->87B（恰好少掉那一行 51B），剩余其它两行内容逐字不变（res://addons/someone_else/other.gdextension + res://addons/third_thing/third.gdextension）" },
    { "id": "DR-41.3c-other-plugins-verbatim", "pass": true, "evidence": "project.godot 的 enabled=PackedStringArray 由 (other_plugin, godot_mcp_rs, third_plugin) 变为 (other_plugin, third_plugin)，两个名字与 \", \" 分隔逐字保留" },
    { "id": "DR-41.3d-empty-list-removes-section", "pass": true, "evidence": "自造 %TEMP%/dr41ws/empty（addon 为唯一项）：[editor_plugins] 整段消失、config/name=\"x\" 保留、.godot/extension_list.cfg 被删除、.godot/ 保留" },
    { "id": "DR-41.3e-idempotent-bytes", "pass": true, "evidence": "第二次 init 后同目录 6 个文件 sha256 与第一次完全相同（project.godot=75cedadf.., extension_list.cfg=620ac9a7.., 三个 keep 文件不变）" },
    { "id": "DR-41.4-reverse-no-collateral", "pass": true, "evidence": "同一实验：addons/other_plugin/keep.txt, addons/third_plugin/keep.txt, .godot/subdir/other_cache.keep 全程 sha256 不变；.godot 与 addons 目录保留" },
    { "id": "DR-41.5-addon-source-zero", "pass": true, "evidence": "Select-String -Recurse src,tests,config -Pattern addon_source -> COUNT=0" },
    { "id": "DR-42.1-fixture-177-regex", "pass": true, "evidence": "python 解析 tests/fixtures/mcp/tools_list.json：177 条、正则违例 0、通道 editor 104/project 48/running_game 23/os 2、无重名" },
    { "id": "DR-42.2-shape-intact", "pass": true, "evidence": "夹具与 tools_list.renamed.json 逐工具逐字段比对差异 0；名字集合相等且顺序相同；cargo test --offline --test tools_policy/tool_discovery 全绿证明现有解析路径可用" },
    { "id": "DR-42.3-name-set-equal", "pass": true, "evidence": "in fixture not source=[] ; in source not fixture=[]（python set 比对）" },
    { "id": "DR-42.4-provenance-sha", "pass": true, "evidence": "PROVENANCE.md 记 fixture sha256=50c5fb4204ee5b957b017eb994e7f7bd73f9b299e6aa9471d5cf11683e067da0；Get-FileHash 实测同值，71481B，无 BOM，末字节 0x7d" },
    { "id": "DR-42.5-fixture-vs-source-keys", "pass": true, "evidence": "工具对象键集合 fixture-only=[]、source-only=[]（无夹具专用字段）；唯一差异是源文件顶层 _meta 键被丢弃" },
    { "id": "DR-42.6-sample-10-mappings", "pass": true, "evidence": "12 条抽样含 update_property->editor_set_node_property 与 GDR-17 的 get_editor_performance->editor_get_performance_monitors；全量完备性：旧名在 b6d9282~1 出现而新名在当前树缺席者 0 条；172/174 新名出现在当前树（另 2 条为 unregister）" },
    { "id": "DR-42.7-old-vocab-zero", "pass": true, "evidence": "自写全后缀整词扫描 src/tests/config（99 文件，旧名集合取自 rename map 174 条）：唯一命中文件为 tests/tool_vocabulary.rs（守卫自身，设计排除）" },
    { "id": "DR-42.8-planner-denied", "pass": true, "evidence": "cargo test --offline --test tools_policy -> 12 passed 0 failed；planner_is_denied_every_tool_of_the_contract 遍历 contract_names() 全部 177 条；src/runtime/policy.rs:283 Role::Planner => false" },
    { "id": "DR-42.9-qa-denied-developer-allowed", "pass": true, "evidence": "qa_is_denied_every_mutating_tool_of_the_contract 取契约内全部 is_mutating 名字（>50）断言 Tester 全拒且可达数==QA_ALLOW_EXACT.len()==2；developer_allowed_all ... ok" },
    { "id": "DR-43.1-running-game-only-on-game-endpoint", "pass": true, "evidence": "cargo test --offline --test dual_endpoint -> 6 passed 0 failed；tests/dual_endpoint.rs:164-228 断言编辑器端点从未收到 running_game_*；src/tools/mod.rs:157 client_for 未登记即 bail!，禁止回退" },
    { "id": "DR-43.2-missing-port-fails-step", "pass": true, "evidence": "tests/dual_endpoint.rs:443-484：旧回复形态下 play_scene_ready.ok==false、observation 含 mcp_port/endpoint 与 UNAVAILABLE、注册器登记数 0；godot.rs:837-865 实现" },
    { "id": "DR-43.3-stop-invalidates", "pass": true, "evidence": "tests/dual_endpoint.rs:230-270：clear 后 running_game_* 报 game_endpoint_unavailable 且游戏端点请求数仍为 1；godot.rs:1884-1892 无条件 clear_game_endpoint" },
    { "id": "DR-43.4-port-source-recorded", "pass": true, "evidence": "godot.rs:1962-1968 逐字记录 argument/auto_free_port；tests/dual_endpoint.rs:280-302 断言 source==\"argument\"/\"auto_free_port\"" },
    { "id": "DR-44.1-editor-binary-config", "pass": true, "evidence": "config/hoh.yaml:43 = F:/moonbit-hof-rs/godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe；Test-Path=True，size=194207744" },
    { "id": "DR-44.2-doctor-two-items-real-run", "pass": true, "evidence": "hoh doctor -c adapter.godot.editor_binary=C:/Users/wyl/.cargo/bin/rustc.exe -c model.base_url=http://127.0.0.1:1/v1 -c tools.endpoint=http://127.0.0.1:1/mcp -> [ok] godot.engine_binary: ... (size 12814336 B, mtime 1774138722) / [ok] godot.engine_version: rustc 1.98.0 (88d9e12ae 2026-08-18)，EXIT=4（离线）；配置的那支 Godot 二进制未被执行（禁用项）" },
    { "id": "DR-44.3-engine-block-null-plus-reason", "pass": true, "evidence": "cargo test --offline --test engine_identity -> 13 passed 0 failed；ENGINE_KEYS 键集断言三处；a_missing_binary_is_null_plus_a_reason_never_a_guess 断言 binary.path=null 且 reason/version_reason/listener.reason 均为字符串" },
    { "id": "DR-44.4-env-abstraction-probe", "pass": true, "evidence": "src/adapter/engine.rs:236 probe_listener 经 mini_swe_agent::Environment；:176 binary_matches 规范化+大小写不敏感；git diff e8461bf..HEAD -- Cargo.toml Cargo.lock 为空（无新依赖）" },
    { "id": "DR-44.5-gate-three-cases", "pass": true, "evidence": "自写 %TEMP% 探针链接 target/debug/libhof_rs.rlib 直调 gate_record：Some(true)->ok=true；Some(false)->ok=false 且 observation 含 'engine identity mismatch … (pid 4242)'；None->ok=false 且 observation 含 'no TCP listener on port 9877 could be read from `netstat -ano -p tcp`'（与 mismatch 明显不同）；代码 engine.rs:512 ok = matches_binary == Some(true)" },
    { "id": "DR-44.6-secret-hygiene", "pass": true, "evidence": "tests/secret_hygiene.rs:93/109-113/116 覆盖 engine 六键且断言不含假密钥；cargo test --offline --test secret_hygiene -> 2 passed 0 failed" },
    { "id": "DR-44.7-c12-no-version-constant", "pass": true, "evidence": "src/** 全文搜索 4.8.dev | ba1587c71 | custom_build -> 0 命中；doctor 用 rustc 替身得到 rustc 版本串，证明版本串非硬编码" },
    { "id": "DR-45.1-guard-exists-three-checks-executed", "pass": true, "evidence": "tests/tool_vocabulary.rs 353 行，三条判据齐备（the_fixture_is_the_four_channel_contract / the_retired_vocabulary_is_gone / every_quoted_tool_name_exists_in_the_contract）；cargo test --offline 输出 tool_vocabulary target 'running 4 tests ... 4 passed 0 failed 0 ignored'，非 #[ignore]" },
    { "id": "DR-45.2-old-vocabulary-list-complete", "pass": true, "evidence": "python 从 tool-rename-map.json 提取 old_name 174 条，与守卫 OLD_VOCABULARY 双向差集皆空" },
    { "id": "DR-45.3-non-vacuous-plant", "pass": true, "evidence": "植入 src/adapter/godot.rs:823 真实调用为 play_scene 后 cargo test --offline --test tool_vocabulary -> FAILED. 3 passed; 1 failed，panicked at tests\\tool_vocabulary.rs:302 'still appears in 1 place(s): src/adapter/godot.rs: play_scene'，退出码 101；回退后 git status --porcelain 与 git diff --stat 均空" },
    { "id": "DR-45.4-false-negative-boundary", "pass": true, "evidence": "新建 src/legacy_probe.sh 含 play_scene -> cargo test --offline --test tool_vocabulary -> 4 passed 0 failed（漏检），删除后 status/diff 均空；SCANNED_SUFFIXES=[.rs .md .json .yaml .yml .toml .txt]，walk 根为 src+tests；SCAN_EXCLUDES=[tests/tool_vocabulary.rs, tests/fixtures/mcp/tools_list.json]" },
    { "id": "GLOBAL.1-cargo-test", "pass": true, "evidence": "cargo test --offline：34 test-result 行，passed=300 failed=0 ignored=7，非 ok=0，EXITCODE=0；7 ignored 全为 tests/godot_smoke.rs（既有 #[ignore]+HOH_SMOKE 门控）" },
    { "id": "GLOBAL.2-prd-sha", "pass": true, "evidence": "Get-FileHash .spec/hof-rs/PRD-mario.md -Algorithm SHA256 = 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a（5375B）" },
    { "id": "GLOBAL.3-godot-mcp-untouched", "pass": true, "evidence": "git diff b6d9282~1..HEAD --stat -- godot-mcp/ 为空；git -C godot-mcp status --porcelain 为空；e8461bf..HEAD 范围内的 6 个 godot-mcp 文件全部出自本批之前的 9000518" },
    { "id": "GLOBAL.4-forbidden-paths-not-committed", "pass": true, "evidence": "git log e8461bf..HEAD --name-only 过滤 runs/|\\.workspace/|config/.*secret -> 空；git status --porcelain -uall 为空" },
    { "id": "GLOBAL.5-commit-boundaries", "pass": true, "evidence": "git show --stat：DR-41=11 文件、DR-42=29、DR-43=7、DR-44=12、DR-45=1（仅 tests/tool_vocabulary.rs）、报告=1、D217=3；提交信息均带 DR 编号；b6d9282/db2eed7 提交时间仍为原始 22:36:01/23:10:29" },
    { "id": "D217.1-origin-unchanged", "pass": true, "evidence": "git rev-parse origin/master = 4b9bd44054ccfefdb4b96a342a133a4896769b76；rev-list --count origin/master..HEAD = 8" },
    { "id": "D217.2-history-rewrite-disclosed", "pass": true, "evidence": "git reflog 显示 57eeff0(DR-44,23:51:51)->c92bda7(DR-45,23:51:55)->21f848e(amend 成 DR-44 消息,00:10:14)->83a9b4c->reset --mixed 57eeff0(00:10:33)->60131e5(DR-44)->b2ed193(DR-45)，与报告 §8.6 自述一致；最终 DR-44=12 文件、DR-45=1 文件，无内容丢失" },
    { "id": "ADD.1-qa-five-widenings", "pass": true, "evidence": "python 用旧前缀规则/新四通道+动词规则在 174 条上逐条重演：差异恰好 5 条，全为旧拒->新放，动词 get/get/get/get/capture，map.mutating 均为 false；git grep -w <5 个旧名> b6d9282~1 -- '*.rs' 全部 NONE（无既有断言被削弱）" },
    { "id": "ADD.2-planner-allowset-empty", "pass": true, "evidence": "抽取 pre/cur 的 planner_denied_all_mcp 与 runtime_semantics::planner_cannot_write_artifact 函数体，逐字节相同；新增更强的全契约遍历断言" },
    { "id": "ADD.3-fixture-reserialized", "pass": true, "evidence": "夹具无任何专用键（工具级键集完全等于源）；仅丢弃源顶层 _meta；PROVENANCE.md 明确写「活体逐字核对留给批次二」，本人亦未做活体核对" },
    { "id": "ADD.4-guard-scan-boundary", "pass": true, "evidence": "被排除文件 2 个（守卫自身 + 契约夹具），SCANNED_SUFFIXES 覆盖 .rs/.md/.json/.yaml/.yml/.toml/.txt；漏检反例（src/legacy_probe.sh）实测为绿" },
    { "id": "ADD.5-mcp-port-source-undeclared", "pass": true, "evidence": "自写探针：argument->\"argument\"、auto_free_port->\"auto_free_port\"、字段缺失->\"undeclared\"、未知取值->\"undeclared\"、仅 endpoint->\"undeclared\"；代码 godot.rs:1962-1968" },
    { "id": "ADD.6-gate-none-closes", "pass": true, "evidence": "自写探针四种 EngineIdentity：match->ok=true、mismatch->ok=false、None(有 reason)->ok=false 且文案为 netstat 读不到、None(无 reason)->ok=false 且文案为 'the listener could not be compared'；三者 observation 可区分" },
    { "id": "ADD.7-registered-gaps-navigate-export", "pass": true, "evidence": "fixture 名集合与 map new_name 集合差集：fixture-not-map = 6 条全新工具、map-not-fixture = {project_export_game, running_game_move_player_to_target_via_navigation}（即两个 unregister）；当前树中 navigate_to/export_project 仅存在于守卫自身，未用任何近似工具顶替" }
  ],
  "defects": [
    { "id": "DEF-1", "severity": "minor",
      "what": "确定性电池步 id 被守卫的整词匹配牵连改名：BatteryStep id \"stop_scene\" -> \"editor_stop_scene\"（它不是工具调用）。报告 §5(k) 仅在位置清单里笼统提及 BatteryStep 表，未点名这条标识符级改名。",
      "reproduction": "git show b6d9282~1:src/adapter/godot.rs | Select-String 'id: \"stop_scene\"' 有命中；当前 src/adapter/godot.rs:1866 为 id: \"editor_stop_scene\"；全仓 \"stop_scene\" 现仅存在于 tests/tool_vocabulary.rs。",
      "impact": "改变 .hoh/deterministic/battery.json 的 step_id 与 raw/<step>.json 文件名。仓库内所有消费点（tests/evidence_battery.rs:649、tests/mcp_desync.rs:378、godot.rs playbook 表）已同步，无悬空引用；跨批次比较旧轮次证据时需注意。属「守卫对非工具标识符的假阳性压力」。" },
    { "id": "DEF-2", "severity": "minor",
      "what": "project.godot 的 [editor_plugins] 段若写成畸形 enabled=（无括号、非 PackedStringArray），ensure_bundled_addon_disabled 会把整段删除，而不是「无该项则逐字节不改」。",
      "reproduction": "temp 工程 project.godot = 'config_version=5\\n\\n[editor_plugins]\\n\\nenabled=true\\n'，跑 target/debug/hoh.exe init --project <dir>，文件变为 'config_version=5\\n\\n'（整段消失）。",
      "impact": "会静默移除一个无法解析的插件段（可能连带他人插件项）。标准 Godot 工程只写 enabled=PackedStringArray(...)，实际不可达；但该分支未声明。建议解析失败时不改动并写 reason。" },
    { "id": "DEF-3", "severity": "minor",
      "what": "addendum 裁定的两条行为在仓库内没有回归测试：(1) parse_game_endpoint 的 undeclared 分支；(2) gate_record 在 matches_binary==None 时关闸且 observation 区别于 mismatch。",
      "reproduction": "Select-String -Recurse src,tests -Pattern undeclared -> 仅 src 3 处、无测试；Select-String -Recurse src,tests -Pattern 'gate_record\\(' -> 无 None-matches 调用。",
      "impact": "行为本身我已用自写探针证真（正确），缺的是回归保护：未来重构可能悄悄破坏这两条已裁定行为而不被测试发现。" },
    { "id": "DEF-4", "severity": "info",
      "what": "过时测试名 src/tools/index.rs:260 the_snapshot_is_the_real_174_tool_list（夹具已是 177），且断言仅为 schemas.len() >= 100，从不校验真实条数。",
      "reproduction": "读 src/tools/index.rs:260-267。",
      "impact": "误导读者；不构成判据失效（真实条数由 tests/tool_vocabulary.rs 的第 1 条判据守）。" }
  ],
  "risks": [
    "批次二（DR-47）必须先跑一次 hoh init / 或等价的清理，否则活动工作区 .workspace/mario 仍带旧通道：本人实测该目录仍有 addons/godot_mcp_rs/（含 godot_mcp_gdext.dll 等 8 个文件）与 .godot/extension_list.cfg（内容恰为 res://addons/godot_mcp_rs/godot_mcp_rs.gdextension）；hoh doctor 已如实把它们报成 [FAIL] godot.bundled_addon / godot.extension_list。清理逻辑本身已由我在自造工程上验证可用且幂等。",
    "夹具是离线派生文档产物（非活体）。批次二必须按 D217 §1.3 的准入门做「名字集合严格相等 + name/description/inputSchema 逐字比较」，并注意夹具不含源文件的顶层 _meta 键。",
    "引擎身份闸门在 matches_binary==None（探针读不到）时也关闸。若真实机器上 netstat -ano 的本地化/格式与解析器预期不符，将整轮拦下。这是设计上要的「沉默即失败」，但批次二首次真机运行时应优先确认探针输出形态。",
    "mcp_port_source 存在第三取值 undeclared（引擎未声明时）。批次二拿到活体 editor_play_scene 回复后，若决定收紧为二元，需要另开决策。",
    "批量改名方式为「读 rename map 的脚本 + 人工复核 24 文件」而非逐行手打（报告 §8.1 已披露）。我的全量机器核对（旧名归零、新名完备、策略差异恰好 5 条）未发现语义漂移，但「输入/输出语义等价」未逐条人工判定。",
    "DEF-2 的畸形 enabled= 分支在标准工程不可达，但若有人手改 project.godot，会静默丢段。",
    "tests/tool_vocabulary.rs 的守卫不扫描 config/、runs/、.spec/ 与非 SCANNED_SUFFIXES 后缀；「旧词汇已在全仓归零」的表述应限定为「src/**、tests/**、src/prompts/** 的 7 类后缀文件」。"
  ],
  "unverified": [
    "在配置的那支 Godot 二进制（godot.windows.editor.x86_64.mono.exe）上真实执行 hof doctor 两项，以及其版本串确为 4.8.dev.mono.custom_build.ba1587c71 —— 会启动引擎二进制，与验收禁用项冲突；我只确认了该文件存在（194207744 B，绝对路径）并用 rustc.exe 走通了同一条代码路径。",
    "活体 tools/list 与夹具逐字一致（名集合与条数）—— 属 DR-47 批次二，离线无法证明。",
    "真实 netstat -ano -p tcp 与 powershell (Get-Process -Id N).Path 在本机的输出形态与解析器契合度 —— 未执行任何端口探针。",
    "meta.json.engine.mcp.editor_status 的真实 GET /mcp 响应体 —— 离线恒为空对象 + reason。",
    "游戏端点独有的 23 个 running_game_* 工具在真实游戏端点上的可达性 —— 本批只证明 hof-rs 不会把它们打到编辑器端点。",
    "活动工作区 .workspace/mario 的真实反向清理结果 —— 我未在该目录执行 init（不改仓、不启动引擎）；只在自造临时工程上端到端验证。",
    "godot-mcp/recovery/TEST-CASES.md 中 177 条 TC-TOOL-* 的语义逐条比对 —— 未做（不属本批判据）。",
    "cargo build 的警告数量 —— 未单独执行（任务书只要求 cargo test）。"
  ]
}
```

---

## 9. 报告落点与验收纪律自查

- 本报告路径：`.spec/hof-rs/tasks/TASK-DR41-ACCEPTANCE.md`。
- **只读约束**：除受控实验外未改仓；未 `git commit`、未 `git push`、未 `git add`/stage。
- **未启动 Godot**、未占用/探测 9877 或任何端口、未联网、未调用任何模型端点。
- 未改 `godot-mcp/**`、未改 `.spec/hof-rs/PRD-mario.md`。
- 实验全部回退后的状态（**在写本报告之前**）：`git status --porcelain`（含 `-uall`）为空、`git diff --stat` 为空；
  `src/adapter/godot.rs` 的 sha256 与 HEAD blob 逐字节相等（`2a962b5c…`，142511 B，`w/lf`）。
  本人产生的唯一临时文件（`cargo test` 日志）已从仓库删除，其余脚本/探针均在 `%TEMP%`。
- 写完本报告后的状态：`git diff --stat` 仍为空；`git status --porcelain -uall` 的唯一一条是
  `?? .spec/hof-rs/tasks/TASK-DR41-ACCEPTANCE.md` —— 即本报告自身（任务书 §0 明确授权的产出），
  非对既有文件的改动；工作树中已跟踪文件无任何改动。
- 回报父代理的内容：仅本报告文件路径。
