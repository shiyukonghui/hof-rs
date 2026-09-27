# TASK-112 — 覆盖驱动循环第三批：三条引擎缺陷全部修在根上（含阻塞级 UID 静默损坏）+ 台账新增「证据档位」梯子

> 本报告的数字来自 `coverage.json`（`python tools/tool_coverage.py` 重算）、`runs/gates/task112/`
> 的十道门输出、以及两变体二进制的真实退出码。**没有从任何报告表格转抄**。
> `projects/` 下 20 款正式工程与它们的历史 `runs/` **只读未动**。
> 本轮**引擎有改动**（三条缺陷），因此**重建了两变体 + 十道门 + accept_m1**（§A4）。

---

## 0. 一句话结论与如实边界

**A 段（三条引擎缺陷）与 B 段（证据档位）做完；C 段（H4/H5/H9/H6 子系统练习）本轮未做。**

1. **D-T111-1（阻塞级静默损坏）**：`publish_file_atomically()` 成功后把「保存回调为临时名登记的 UID」
   重指到真正存在的目标路径。修前 doctest 红、修后绿；`--test-case=[MCPServer]*` **159/159 通过**
   （修前该 159 条里 2 条红/崩）。
2. **D-T111-2**：`editor_add_resource_to_node_property` 的 `resource_properties` 改走**模块唯一**的
   bag 写者 `MCPTools::write_resource_properties`，矢量/颜色组件对象不再是 `-32602`；
   组件填不进槽位时仍是 `-32602`（宽度门没被放宽）。
3. **D-T111-3**：`editor_add_raycast.dimension` 成为**闭集**（判定早于编辑器守卫），并把契约
   `inputSchema` 同步声明为 `enum:["2d","3d"]`（生成器 1.22.0 → 1.23.0，`_meta.overrides` +1）。
4. **B 段**：`tool_coverage.py` / `TOOL-COVERAGE.md` 新增证据档位
   `pixel_effect > file_effect > readback > count_only`（0 次另记 `no_calls`）；
   `readback` 的 `witness_read` **必须写在会话 manifest 里并由台账回 trace 复核**，
   本轮声明 22 条、复核通过 20 条、**被拒 2 条**（拒绝是机制在工作的证据）。
   档位分布：`pixel_effect` 27 / `file_effect` 24 / `readback` 77（57 `own_payload` + 20 `witness_read`）
   / `count_only` 9 / `no_calls` 40，合计 **177**。
5. **C 段没做**：H4 导航 6 / H5 音频 6 / H9 录放 3 / H6 粒子 5 共 20 条**仍是 0 次**，登记表里仍是
   「不可达（未复核）」。本轮预算全部花在 A（三条缺陷 + 两变体重建 + 十门 + accept_m1）与 B 上。
   **这是待办，不是结论**；下一批的方法沿用 TASK-111（先建练习工程证伪整族）。

**必须同时说清的边界**：
* `witness_read` 的复核强度是「**该读调用在同一个 run 里对同一个工具域发生过、`ok=true`、回包有实质载荷**」，
  **不是**「这一次读调用的回包里逐字出现了被写的值」。台账记的是见证调用的 `seq`，
  但**没有**做「载荷内容 ⊆ 写入内容」的内容级比对（见 §B3 的两条限制与下一批建议）。
* 「工具自己响应里说成功了」一律**不算** readback：`editor_set_node_script` 的 `attached:true`、
  `editor_set_control_theme` 的 `applied:true` 这类证据**只在有独立读调用时**才给档位。
* 本轮**没有新增任何一个 run**：`出现 137 / 达标 92 / 0 次 40` 与 TASK-111 相同；本轮变的是
  **证据档位**（45 条「计数达标缺证据」逐条落到档位）。

---

## 1. 交付物与证据路径

| 交付物 | 路径 | 说明 |
|---|---|---|
| D-T111-1 修复 | `godot/modules/mcp_server/tools/tool_helpers.{h,cpp}` | 新增 `MCPTools::retarget_published_uid()`，在 `publish_file_atomically()` 成功后调用 |
| D-T111-2 修复 | `godot/modules/mcp_server/tools/editor_write_scene_editor.cpp` | 手写 bag 循环 → `MCPTools::write_resource_properties`（TASK-049 已导出），回答补 4 个读回字段 |
| D-T111-3 修复 | `godot/modules/mcp_server/tools/editor_node_instantiate.cpp` | 新增 `_resolve_raycast_dimension()`（闭集，早于 `require_editor_ui`）+ 注册 schema 加 `enum` |
| 契约变更 | `godot/modules/mcp_server/scripts/gen_renamed_contract.py` + `docs/tools_list.renamed.json` | `SCHEMA_OVERRIDES["add_raycast"]`（`mode=replace`）、生成器 1.23.0、重生成 |
| doctest | `godot/modules/mcp_server/tests/test_mcp_server.h` | 新增 2 个 TEST_CASE + 1 个既有 case 的 3 组断言（§A4） |
| 台账（档位） | `tools/tool_coverage.py` / `TOOL-COVERAGE.md` / `coverage.json` | 档位梯子 + §0.1 见证表 + §0.2 逐档清单 |
| 见证声明 | `tools/sessions/_exercises/{ex_write/c4,ex_write6/c5,ex_3d/h1,ex_anim/h2,ex_grid/h3}-manifest.json` | 每个 manifest 新增 `readback` 数组（22 条） |
| 派生脚本 | `recovery/work/task112/inject_readback.py`（注入）、`derive_readback.py`（列出可用见证） | 声明是手写的，复核是机器做的 |
| 构建日志 | `recovery/logs/task112-build-local5.log`、`task112-build-mono.log` | 均 `EXIT_CODE=0` |
| 十道门 | `runs/gates/task112/summary.txt` + `g01..g10` 的 stdout/stderr | §A4 |
| 决策 | `DECISIONS.md` **D157** | 选项、否决理由、回滚点 |

---

## A. 三条引擎缺陷

### A1. D-T111-1（阻塞级，静默损坏）—— 临时名上的 UID 必须搬到真正存在的路径

**根因链（逐行可查）**

```
ResourceSaver::save(res, "res://a/b.mcp-tmp.tres")          ← 原子发布的临时兄弟名
  └ ResourceFormatSaverText::save
      └ ResourceSaver::get_resource_id_for_path(local_path = 临时名, true)
          └ EditorFileSystem::_resource_saver_get_resource_id_for_path
              └ ResourceUID::create_id_for_path(临时名)     ← 新铸一个 UID，写进临时文件的头
  └ 成功后 ResourceSaver::save 调 save_callback(res, path = 临时名)
      （core/io/resource_saver.cpp:146-148）
      └ EditorNode::_resource_saved            （editor/editor_node.cpp:7963-7974）
          └ EditorFileSystem::update_file(临时名)
              └ ResourceUID::add_id(uid, 临时名) + update_cache()   ← 落盘 .godot/uid_cache.bin
之后 publish_file_atomically 只做 rename：**文件名的映射从来没有被改回目标路径**。
```

后果（TASK-111 §C2 实测，`projects/_exercises/ex_3d`）：之后保存的场景按 UID 引用该资源时，
`resource_format_text.cpp:481-483` **优先用 UID**（`path=` 属性是对的也救不了），
`ResourceLoader::_load_start` 对不存在的临时文件返回空 token，加载以
`[ext_resource] referenced non-existent resource` 结束 —— 而写工具退出码 0。

**选项与否决**（完整理由见 `DECISIONS.md` D157）：①**发布后重指（采纳）**；
②让临时名不可注册（否决：`recognize_path()` 要求扩展名保持最后一段，见
`tool_helpers.h:139-146` 的既有实测）；③绕开 `ResourceSaver` 直写（否决：等于自己实现
Godot 序列化格式，且破坏「模块唯一发布原语」）。

**修复**：`publish_file_atomically()`（模块**唯一**的发布原语，场景/资源/主题三族
`ResourceSaver` 写者都经它）在 rename 成功后调用新增的
`MCPTools::retarget_published_uid(p_path)`：

1. 读「这个 UID 是什么」——两条来源，因为引擎在两种进程里答案不同：
   `ResourceLoader::get_resource_uid()` 只在 `is_editor_hint()` 下读文件头
   （`resource_loader.cpp:1412-1426`），`ResourceUID::get_path_id()` 只在**非**编辑器进程可用
   （`main.cpp:2255-2257` 才 `enable_reverse_cache()`）。先读文件头（编辑器里的权威），
   失败再读临时名的映射。
2. `set_id(uid, 目标)` 改写**前向映射**（加载器实际查的就是它），于是 `uid_cache.bin` 里
   指向 `*.mcp-tmp.*` 的那条被同一条记录覆盖掉。
3. 落盘：仅当 `is_editor_hint()` **且** 项目数据目录（`res://.godot/`）真的存在时调
   `ResourceUID::update_cache()`。理由写在代码注释里：编辑器把**错的值**落盘过，
   内存修正不足以让**另一个进程**（TASK-111 的复现就是一次新的 `godot --headless` 运行）
   读对；而 doctest 进程没有 `.godot/`，写路径上的辅助函数不应顺手造一个目录。

**落盘这一句为什么不是 `EditorFileSystem::update_file()`（一次真实的失败与改正）**：
最初的实现调用 `EditorFileSystem::get_singleton()->update_file(p_path)`（看起来更「正统」：
那正是引擎保存回调自己走过的函数）。它在 `--headless --test --test-case=[MCPServer]*`
（159 条）里**通过**，但在**全量** `--headless --test` 里 **SIGSEGV**：该单例在测试进程里
**存在**（由 `register_editor_types()` 建出）却**不可用**；`--success` 的逐断言输出把崩溃点钉到
`REQUIRE(engine != nullptr)` 之后的那一行（即 `publish_text_atomically`）。改成
`ResourceUID::update_cache()`（`update_file` 自己最终也会调的原语）后，全量测试
**1585 条 / 431085 断言 / 0 失败 / exit 0**。这个「只在全量里复现」的差异是
「先跑 `[MCPServer]*` 子集就以为绿了」会漏掉的东西，记在这里以便后人不要重犯。

**修前 / 修后（同一次节奏内的前后对比）**

| | 修前 | 修后 |
|---|---|---|
| doctest `[MCPServer] a published resource's UID ends up on the published path…` | **红**：`get_id_path(uid) == res://mcp_server_test_fixture/assets/uid_retarget.mcp-tmp.tres`（且该路径**不存在**） | **绿**：`get_id_path(uid) == …/uid_retarget.tres` 且 `FileAccess::exists()` 为真；引用该 UID 的 `.tscn` 能 `ResourceLoader::load()` 回来 |
| `--test-case=[MCPServer]*` | 159 条中 **2 条红**（其中 1 条 SIGSEGV） | **159/159 通过、6779/6779 断言** |
| `--headless --test`（全量） | 修前的崩溃点见下（第一次实现用 `update_file` 时 **1 条 SIGSEGV**） | **1585/1585 通过、431085/431085 断言、exit 0**（另有 3 条本题集外的 skip） |

### A2. D-T111-2 —— `resource_properties` 少了一步 `shape_vector_from_json`

**实测（TASK-111 `c4-040`，保留在 manifest 里）**：
`{"resource_type":"RectangleShape2D","resource_properties":{"size":{"x":48,"y":48}}}` → `-32602`，
消息逐字是「…**Send the property type's own shape: a JSON object naming its components for a
vector/colour**」——它点名的写法正是它拒绝的写法；同目标的 `{"radius":12.0}` 5/5 成功，
兄弟工具 `editor_setup_collision_shape` 用同一个 `{"size":{"x":32,"y":32}}` 成功。

**修复**：该工具的手写循环（`property_value_from_json` → `coerce_to_property_type`，漏了
`shape_vector_from_json`）改为调用模块**已导出**的 `MCPTools::write_resource_properties`
（TASK-049 导出时写明「是为复用/doctest」）——即 `project_create_resource` /
`project_edit_resource` 跑的同一条规则。回答同时补上兄弟工具已有的
`properties_set` / `ignored` / `ignored_count` / `changed`（**行为面增量，已在 D157 声明**）。

**修前 / 修后**

| 输入 | 修前 | 修后 |
|---|---|---|
| `resource_properties = {"size":{"x":48,"y":48}}`（Vector2 属性） | `-32602`「Send the property type's own shape…」 | 写入成功，读回 `Vector2(48,48)`；回答带 `properties_set`/`ignored` |
| `resource_properties = {"size":{"x":"wide","y":1}}` | `-32602`（碰巧对） | 仍是 `-32602`，消息点名 `properties.x`（宽度门**没有被放宽**） |
| 颜色组件对象 | 同样被拒 | 写入成功（doctest 用 `bg_color` 钉住） |

**doctest 用 `StyleBoxFlat` 而不是 `RectangleShape2D` 的如实理由**：
`Main::test_setup()`（`main/main.cpp:688-834`）初始化了物理服务器**管理器**却**从不**调
`PhysicsServer2DManager::initialize_server()`，而 `Shape2D()` 的构造要
`PhysicsServer2D::get_singleton()->shape_create()` —— 实测 `memnew(RectangleShape2D)` 在本进程
**SIGSEGV**。所以 doctest 用同为 `Resource`、**不需要服务器**的 `StyleBoxFlat`
（`shadow_offset` 是 Vector2、`bg_color` 是 Color）钉住**同一个输入形状**；
`RectangleShape2D.size` 的那个拼写由**线上**覆盖（`c4-040` 是修前的实测拒绝；
线上修后复跑见 §A5 的如实说明）。

### A3. D-T111-3 —— `dimension` 闭集 + 契约 enum

**实测（TASK-111 `c4-033`）**：`{"dimension":"4d","name":"Ray4d"}` → **成功**，
回 `{"added":true,"name":"Ray4d","node_path":"Ray4d","type":"RayCast3D"}`。
根因 `editor_node_instantiate.cpp:274` 的 `dimension == "2d" ? RayCast2D : RayCast3D`
—— 除字面量 `"2d"` 之外的**任何**值（含 `"4d"`、`"2D"`、拼错）都静默变成 3D 射线。

**修复**（两半）：
* 运行时：新增 `_resolve_raycast_dimension()`，`2d`/`3d` 之外是 `-32602`
  （`'dimension' must be one of '2d' or '3d'; got '4d'`），注册层按既有规则附
  `data.suggestion`（TASK-050 N-7）；判定放在 `require_editor_ui` **之前**，
  所以 game 进程与 doctest 都能看到它。
* 契约：`SCHEMA_OVERRIDES["add_raycast"]`（`mode=replace`，`enum:["2d","3d"]`，
  `default`/`type`/`name`/`parent_path` 逐字保留、`required` 仍是 `[]`），
  生成器 1.22.0 → **1.23.0**，`_meta.overrides` +1；重生成后**结构化 diff 只有三处**
  （`dimension.enum` + `generator_version` + 一条 override 记录）。
  理由：同一份契约的其它闭集（`editor_set_node_selection.mode`、
  `run_test_scenario.steps[].type`）都已声明 `enum`，而调用方从 `tools/list` 无法得知
  `"4d"` 非法——**契约是调用方唯一能读到的说明**。

**修前 / 修后**

| 输入 | 修前 | 修后 |
|---|---|---|
| `{"dimension":"4d"}` | `ok` + `type:"RayCast3D"`（静默造错节点） | `-32602` `'dimension' must be one of '2d' or '3d'; got '4d'` + `data.suggestion` |
| `{"dimension":"2D"}` | `ok` + `RayCast3D` | `-32602`（同一闭集） |
| `{"dimension":"2d"}` / `"3d"` | `ok` | 不被 dimension 规则拒绝（正面对照：doctest 断言此时是编辑器守卫的 `-32000`，消息与 dimension 无关） |
| 契约 `tools/list` | `dimension: {default:"2d", type:"string"}` | 增加 `enum:["2d","3d"]`（`check_contract_subset` 逐字核过） |

### A4. 两变体重建 + 十道门 + accept_m1（真实退出码）

重建（模块提交前，串行，cmd 启动）：

| 变体 | 命令 | 真实退出码 | `--version` |
|---|---|---|---|
| 纯引擎 | `modules\mcp_server\scripts\build_local.cmd -Force` | **0** | `4.8.dev.custom_build.3fdabe2d9` |
| mono | `modules\mcp_server\scripts\mcp057_build_mono.cmd` | **0** | `4.8.dev.mono.custom_build.3fdabe2d9` |

`HEAD` = `3fdabe2d9`（**二进制锚点与工作树同源**；`g09` 判 `ANCHOR_EQUAL`，
`ANCHOR=3fdabe2d9 ANCHOR_REPORTED=3fdabe2d9 HEAD=3fdabe2d9`）。
模块改动在**十门全绿之后**才提交为 `ba1587c71e`，并 push 到 fork
（`3fdabe2d9a..ba1587c71e`）；下一次重建后 `--version` 才会变成 `ba1587c71e`，
所以本报告的锚点与二进制是**同一个** `3fdabe2d9`，不是漂移。

十道门（`runs/gates/task112b/summary.txt`，每条都是子进程里的 `!ERRORLEVEL!`；第一次跑的是
`task112` tag，当时 **g02 = exit 1**，见 §A1 那条 `update_file` 的失败与改正）：

| 门 | 命令 | exit | 证据 |
|---|---|---|---|
| g01 | `--headless --test --test-case=[MCPServer]*` | **0** | 159/159 cases、6779/6779 断言 |
| g02 | `--headless --test` | **0** | **1585/1585 cases、431092/431092 断言、3 skipped** |
| g03 | `check_tool_groups.py` | 0 | TOOL-GROUPS CHECK PASS |
| g04 | `check_contract_subset.ps1` | 0 | editor 154 / game 73 契约子集 **3/3 PASS**（含新 enum）、`guard_user_port_9877` pid −1/−1 |
| g05 | `check_rename_map.py` | 0 | 177 == 174 − 2 − 1 + 6，契约 sha `fd00c75e…` |
| g06 | `check_tautologies.py` | 0 | 恒真门 PASS |
| g07 | `check_exit_propagation.py --probes` | 0 | PROBES 10/10 |
| g08 | `check_hardcoded_counts.py` | 0 | UNCLASSIFIED = 0 |
| g09 | `check_engine_anchor.ps1` | 0 | **ANCHOR_EQUAL**（anchor = HEAD = `3fdabe2d9`） |
| g10 | `accept_m1.ps1` | 0 | **22/22 cases passed** |

### A5. 如实说明：哪一条缺陷的「修后」证据是哪一种

* **D-T111-1**：doctest **红 → 绿**（同一台机器、同一批），并额外把引用该 UID 的场景
  `ResourceLoader::load()` 回来看它是否有效 —— 这是本轮最强的证据。
* **D-T111-2 / D-T111-3**：**修后**证据是 **doctest + 契约门（g04）+ 全量门（g02）**。
  我**没有**在修后的二进制上跑一次线上 MCP 会话把那两个工具再调一次（C 段没做，
  会话驱动也就没起）。所以这两条的「线上修后对比」是**缺失**的，不拿 doctest 冒充线上证据。
  下一批应当在同一批里补：`editor_add_resource_to_node_property` 发一次
  `{"size":{"x":48,"y":48}}`、`editor_add_raycast` 发一次 `{"dimension":"4d"}`。

---

## B. 证据档位（readback 证据档）

### B1. 档位定义（写进 `tool_coverage.py` 的 docstring 与 `TOOL-COVERAGE.md` 的表头）

```
pixel_effect  >  file_effect  >  readback  >  count_only          （0 次 → no_calls）
```

* `pixel_effect`：至少一次 `ok` 调用的 ledger verdict 是 `ok_effect_observed`（画面/视口真的变了）。
* `file_effect`：至少一次是 `ok_file_effect_observed`（文件真的变了）。
* `readback`：没有像素/文件效果，但生效由**另一次调用**佐证。两种 kind **互不混同**：
  * `witness_read` —— **写类**工具。配对**写在会话 manifest 的 `readback` 数组里**，
    台账回到该 run 的 trace **再找一次**见证调用：必须在、必须 `ok=true`、
    必须有实质载荷（或已核验 sidecar）。找不到就**不授予**档位，并记进 §0.1 的 rejected 列表。
  * `own_payload` —— **读类动词**（TASK-111 的 `READ_VERBS`）。它的回包**就是**测量结果，
    不存在「可以等的第二次调用」。
* `count_only`：有调用、有计数，但没有生效证据。**「工具自己响应里说成功了」只能落在这里。**

### B2. 档位分布与逐档清单

| 档位 | 工具数 | 说明 |
|---|---|---|
| `pixel_effect` | **27** | `ok_effect_observed` 至少一次 |
| `file_effect` | **24** | `ok_file_effect_observed` 至少一次 |
| `readback` | **77** | 其中 **57** 条 `own_payload`（读类），**20** 条 `witness_read` |
| `count_only` | **9** | 见下方清单 |
| `no_calls` | **40** | 契约里 0 次调用的工具（与 TASK-111 相同） |
| **合计** | **177** | 契约条数 |

`count_only` 9 条（**没有**做独立的读回见证，所以**不给**档位）：

| # | tool | 累计 | 边界 | 为什么还在 `count_only`（如实） |
|---|---|---|---|---|
| 1 | `editor_connect_signal` | 39 | 6 | 本轮声明的见证（`editor_list_signal_connections`）在 `c4-v5` **没有**合格调用，被复核**拒**；`c5` 的那一次读回发生**在断开之后**，只能佐证「断开」而不能佐证「连上」 |
| 2 | `running_game_find_node_when_available` | 8 | 8 | 从未配过独立的读回（历史运行里它的 8 次全是边界） |
| 3 | `editor_add_mesh_instance` | 6 | 1 | H1 运行里唯一的读调用是 `editor_get_viewport_3d_camera`，**不读**被建的 mesh 节点 → 不能用 |
| 4 | `editor_setup_camera_3d` | 6 | 1 | 同上（同一族的证据缺口） |
| 5 | `editor_setup_lighting` | 6 | 1 | 同上 |
| 6 | `editor_set_material_3d` | 6 | 3 | 同上 |
| 7 | `editor_setup_world_environment` | 6 | 1 | 同上 |
| 8 | `editor_add_gridmap` | 6 | 1 | 声明的见证（`editor_get_scene_tree`）在 `h3` **没有**合格调用，被复核**拒** |
| 9 | `editor_set_node_script_batch` | 50 | **0** | 从未配过独立读回；且它连边界调用都是 0（另一个台账口径问题，与档位无关） |

### B3. `witness_read` 20 条：写工具 ← 见证读调用（run / seq 来自 trace）

| 写工具 | 见证读调用 | run | 见证 seq | 读回的是什么 |
|---|---|---|---|---|
| `editor_add_scene_instance` | `editor_get_scene_tree` | `runs/_exercises/ex_write5/c4-v5-task111` | 132 | 实例必须出现在编辑场景树里 |
| `editor_rename_node` | `editor_get_node_properties` | 同上 | 138 | 读回被改名节点的 `name` |
| `editor_set_node_groups` | `editor_get_node_groups` | 同上 | 143 | 读回节点的 groups |
| `editor_set_node_script` | `editor_get_node_properties` | 同上 | 138 | 读回节点的 `script` 属性 |
| `editor_set_physics_layers` | `editor_get_node_properties` | 同上 | 138 | 读回 `collision_layer` / `collision_mask` |
| `editor_setup_physics_body` | `editor_get_scene_tree` | 同上 | 132 | 建出来的物理体在树里 |
| `editor_set_control_theme` | `editor_get_node_properties` | 同上 | 138 | 读回 Control 的 `theme` |
| `editor_disconnect_signal` | `editor_list_signal_connections` | `runs/_exercises/ex_write6/c5-task111` | 13 | 断开后 `count:0` |
| `editor_set_viewport_3d_camera` | `editor_get_viewport_3d_camera` | `runs/_exercises/ex_3d/h1-task111` | 27 | 下一次调用读回上一次写的 fov/position |
| `editor_create_animation` | `editor_list_animations` | `runs/_exercises/ex_anim2/h2b-task111` | 23 | 新建的动画在列表里 |
| `editor_add_animation_track` | `editor_get_animation_info` | 同上 | 29 | 读回轨道表 |
| `editor_set_animation_keyframe` | `editor_get_animation_info` | 同上 | 29 | 读回关键帧 |
| `editor_remove_animation` | `editor_list_animations` | 同上 | 23 | 被删的动画不在列表里 |
| `editor_create_animation_tree` | `editor_get_animation_tree_structure` | 同上 | 88 | 读回 tree 结构 |
| `editor_add_state_machine_state` | `editor_get_animation_tree_structure` | 同上 | 88 | 读回状态列表 |
| `editor_remove_state_machine_state` | `editor_get_animation_tree_structure` | 同上 | 88 | 被删的状态不在列表里 |
| `editor_add_state_machine_transition` | `editor_get_animation_tree_structure` | 同上 | 88 | 读回迁移列表 |
| `editor_remove_state_machine_transition` | `editor_get_animation_tree_structure` | 同上 | 88 | 被删的迁移不在列表里 |
| `editor_set_blend_tree_node` | `editor_get_animation_tree_structure` | 同上 | 88 | 混合树节点真的在树上 |
| `editor_set_animation_tree_parameter` | `editor_get_animation_tree_structure` | 同上 | 88 | 参数出现在参数表里 |

**两条必须声明的限制**（下一批要补的就是它们）：
1. **见证 seq 记的是该读工具在 run 里的第一个 `ok`+实质载荷调用**，不一定逐次对应写调用的目标；
   台账**没有**做「读回载荷里逐字出现被写值」的内容级比对。要做成内容级，需要给声明加一个
   `expect` 字段（例如 `"\"name\":\"Ren1\""`）并让复核在载荷里搜它——这是下一批的**口径升级**，
   本轮没有假装做到。
2. **两条声明被复核拒绝**（`editor_add_gridmap`、`editor_connect_signal`）：这正是
   「声明 → 机器复核 → 不给档位」这条链在工作的证据；`TOOL-COVERAGE.md` §0.1 逐条列出了它们。
   我没有把拒绝藏起来，也没有为了让数字好看而手工放行。

---

## C. 子系统练习（H4/H5/H9/H6）—— **本轮未做**

**如实报告到哪一步：A + B 完成，C 一步未做。**

* H4 导航 6 条、H5 音频 6 条、H9 录放 3 条、H6 粒子 5 条：**仍是 0 次调用**，
  `TOOL-COVERAGE.md` §3 / §4 的登记状态未变（仍是「不可达（未复核）」）。
* 没有新建 `projects/_exercises/` 工程、没有新建会话、没有新增 run。
* 因此 §D1 的「出现 / 达标 / 0 次」三个数与 TASK-111 **完全相同**（137 / 92 / 40）——
  这不是「没变化」，而是**本轮的 C 段没做**。
* 预算去向：三条引擎缺陷的定位与修复、5 次纯引擎重建、1 次 mono 重建、十道门 + accept_m1、
  以及 B 段的档位机制与 22 条见证声明的复核。

---

## D. 收尾

### D1. 全语料口径（all-runs）前后对比

| 指标 | TASK-111（基线） | TASK-112（本轮） | 增量 |
|---|---|---|---|
| run 目录 / trace 文件 / `tools/call` | 97 / 162 / 8286 | **97 / 162 / 8286** | 0（C 段未做） |
| 出现过的工具名 | 137 | **137** | 0 |
| `0` 次 | 40 | **40** | 0 |
| `1-4` 次 | 0 | **0** | 0 |
| `>=5` 次 | 137 | **137** | 0 |
| `达标` | 92 | **92** | 0 |
| `计数达标缺证据` | 45 | 45 | 0 |
| **证据档位** | 无此口径 | `pixel_effect` 27 / `file_effect` 24 / `readback` 77 / `count_only` 9 / `no_calls` 40 | 新口径 |
| 登记表「不可达」（仍登记） | 40 | **40** | 0（C 段未做，未复核） |
| 契约条数 | 177 | **177**（`_meta.overrides` +1、生成器 1.23.0） | 条数不变 |

### D2. 台账与决策

* `TOOL-COVERAGE.md` / `coverage.json` 由 `python tools/tool_coverage.py` 重跑生成
  （本轮最后一次：97 run / 162 trace / 8286 调用 / 137 工具）。
* 不可达登记表**未动**（C 段未做，没有新增可复核的实测证据）。
* 决策记录：`DECISIONS.md` **D157**（选项、否决理由、行为面增量声明、C 段未做、回滚点）。

### D3. 如实声明：本轮**没有**做的事

* **没有做 C 段**（H4/H5/H9/H6）。理由与预算去向见 §C。
* **没有**把 `readback` 做成内容级复核（见 §B3 限制 1）。
* **没有**在修后的二进制上跑线上 MCP 会话，因此 **D-T111-2 / D-T111-3 缺线上修后对比**（§A5）。
* **没有**碰 20 款正式工程与它们的历史 `runs/`：只读。
* **没有**为「非像素生效」放宽 `状态`（`达标` 的判据一字未动）；新增的只是**并行的档位**口径。

---

## E. 剩余 `<5` 清单与下一批建议

**仍登记为不可达的 40 条**（与 TASK-111 §E 相同，本轮未复核）：

| 类 | 条数 | 工具 |
|---|---|---|
| **H4** 导航 | 6 | `editor_bake_navigation_mesh`、`editor_get_navigation_info`、`editor_set_navigation_layers`、`editor_setup_navigation_agent`、`editor_setup_navigation_region`、`running_game_move_player_to_target` |
| **H5** 音频 | 6 | `editor_add_audio_bus`、`editor_add_audio_bus_effect`、`editor_add_audio_player`、`editor_get_audio_bus_layout`、`editor_get_audio_info`、`editor_set_audio_bus_property` |
| **H6** 粒子 | 5 | `editor_create_particles`、`editor_get_particle_info`、`editor_set_particle_color_gradient`、`editor_set_particle_material`、`editor_set_particle_preset` |
| **H7** GUI/播放/输入注入 | 15 | （TASK-111 §E 原表） |
| **H8** 导出 / Android | 5 | （同上） |
| **H9** 录放 | 3 | `running_game_create_input_recording`、`running_game_play_input_recording`、`running_game_stop_input_recording` |

**下一批建议（按价值排序）**

1. **先补 C 段（H4 6 → H5 6 → H9 3 → H6 5）**，方法沿用 TASK-111：工程由引擎自身的 API 生成前置，
   每条 ≥5 次 + ≥1 生效 + ≥1 边界，`--headless --quit-after 5` 退出码 0。
   **优先级最高的收益不是那 20 条本身，而是「每条的新调用天然带一个同 run 的读回见证」**——
   这正是本轮给 H1/H2/H3 补档位的缺口（H1 5 条、H6/H4/H5/H9 全部还在 `count_only`）。
2. **把 `readback` 升级到内容级**：给声明加 `expect` 字段，复核时在见证调用的载荷里搜它
   （本轮的 `witness_read` 只证明「见证调用发生过且有载荷」）。同时给 H1 的 5 条补一条真正的节点级见证读
   （`editor_get_scene_tree` 在 `h1` run 里缺失，值得重跑一次把读调用加进会话）。
3. **补 D-T111-2 / D-T111-3 的线上修后对比**：同一批里各发一次修前失败的请求，留 trace 前后对照。
4. **H8 的 5 条**里 `project_get_export_info` / `project_list_export_presets` 只需
   `export_presets.cfg`（工程里有），很可能可达；`os_list_android_devices` /
   `os_deploy_to_android_device` 需要真机，建议先在登记表里**明确分类**而不是继续笼统写「不可达」。
5. **H7 的 `editor_simulate_*` 5 条**注入的是**编辑器进程**的输入，不能驱动游戏进程
   （D59 / GDR-21 的既有边界）；建议在登记表里把「结构性不可达（设计使然）」与
   「本轮没做」分开写，否则下一批会继续把它们当成可达目标去试。

---

## F. 提交与跑后的进程/端口检查

### F1. 两个仓库的真实提交

```
$ cd F:\moonbit-hof-rs\godot-mcp\godot && git log --oneline -1
ba1587c71e  fix(mcp_server): TASK-112 - the three engine defects TASK-111 registered are fixed at the root
            (one of them blocking and silent), plus one schema override
            7 files changed, 527 insertions(+), 13 deletions(-)

$ cd F:\moonbit-hof-rs\godot-mcp\godot && git push origin feature/mcp-server-module-rebuild
To github.com:shiyukonghui/godot.git
   3fdabe2d9a..ba1587c71e  feature/mcp-server-module-rebuild -> feature/mcp-server-module-rebuild

$ cd F:\moonbit-hof-rs && git log --oneline -1
6029f43  feat(godot-mcp): TASK-112 - the evidence-tier ladder for the coverage ledger, the three engine
         defect fixes it drove, and the third batch's account
         15 files changed, 3526 insertions(+), 383 deletions(-)
```

提交顺序是有意的：**先十门全绿，再提交引擎**，然后提交主仓（报告 / 台账 / 声明 / 决策 /
派生脚本）。引擎提交在十门之后，所以 `g09` 的锚点仍是二进制里那个 `3fdabe2d9`——
这一点在 §A4 里已说明，不是锚点漂移。

### F1b. 提交后仍未纳入工作树的主仓条目（都不是本任务的产物）

```
$ git status --porcelain
 M godot-mcp/recovery/work/task104/logs/git-housekeeping.err.txt   <- TASK-104 收尾时的既有状态
 M godot-mcp/recovery/work/task104/logs/git-housekeeping.out.txt   <- 同上
?? godot-mcp/dist/                                                 <- TASK-107/109 的产物
?? godot-mcp/projects/_exercises/ex_write2/                        <- TASK-111 被主动终止的运行留下的半成品
?? godot-mcp/projects/_exercises/ex_write3/                        <- 同上（会话修好前的尝试）
?? godot-mcp/projects/_exercises/ex_write4/                        <- 同上
?? godot-mcp/recovery/reports/ACCEPTANCE-TASK-107.md               <- TASK-107 的产物
```

与 TASK-111 §F2 逐条相同；**没有删除任何一条**（破坏性命令默认拒绝）。

### F2. 构建与运行的进程/端口检查（铁律 4）

```
pre-gates   netstat LISTENING 9888/9889/9877 -> NONE ;  tasklist godot -> NONE
post-gates  netstat LISTENING 9888/9889/9877 -> NONE ;  tasklist godot -> NONE
```

十道门里 `check_contract_subset.ps1` 与 `accept_m1.ps1` 会**临时**起 9888/9889 端点
（`g04` 的 `guard_user_port_9877` 报 `pid_before=-1 pid_after=-1`、`g10` 的
`guard_user_port_9877` 同样通过），用户端口 **9877** 全程未被占用。

### F3. 铁律执行与一条日志观察

```
$ netstat -ano | findstr "LISTENING" | findstr "9888 9889 9877"   ->  NO_LISTENERS
$ tasklist  | findstr /I godot                                    ->  NO_GODOT_PROC
```

铁律 4 在本轮**每次**构建/测试前都执行（5 次纯引擎构建、2 次 mono 构建、2 次十门、6 次
`--test` 直跑），全部在 `F:\moonbit-hof-rs\godot-mcp\godot` 下、全部由 **cmd** 启动
（铁律 3），**没有一次 shell 重定向**（铁律 1：构建脚本自己写日志文件，
我自己的运行一律用 `Start-Process -RedirectStandardOutput/Error`）。

另记一条**观察**（不是本任务的缺陷）：`build_local.cmd` / `mcp057_build_mono.cmd` 的日志
默认落在 `%TEMP%` 且是**追加**的（`>>`），所以旧机器的历史错误行（路径是
`F:\RustProjects\godot-mcp-pro\...`）会留在同一份日志里，第一次看容易把历史错误当成当次错误。
本轮改用 `set MCP_BUILD_LOG=<task112 专用路径>` 与 `recovery/logs/task112-build-*.log` 隔离，
并在读日志时按**当前文件的真实行号**过滤。
