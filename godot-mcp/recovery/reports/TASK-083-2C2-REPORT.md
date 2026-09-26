# TASK-083 — 2c-2：把重建树推进到可编译（REPORT）

* 生成时间：2026-09-26（TASK-083 会话）
* 工作树：`H:\rebuild\godot`　分支：`feature/mcp-server-module-rebuild`
* 起点：`f4b6b92925`（已 push）　终点：见 §7
* 报告：本文件。证据：`C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083\`、`…\logs\`、树内 `modules\mcp_server\docs\reports\evidence\task083\`

---

## 0. 一句话结论（**必须先读**）

**TASK-082 的根因诊断不完整，本轮把它改对了，但"可编译"这个目标没有达成。**

TASK-082 把三个文件判为"丢失文件头"。真相是：2A/2B 重建**只写入读窗覆盖到的行、把没覆盖到的行整段丢弃**（`read_cov` 恰好等于产出文件的行数），
所以每个受损文件都是**被压掉空档的拼接件**，而且拼接的碎片**可以来自不同 revision**——`mcp_server.cpp` 甚至不是"头丢了"，
而是**碎片顺序都是错的**（第 121 行是无签名的 `pump_frame` 函数体，第 240 行 `build_deferred_body` 签名后面直接接 `_start_service` 的尾巴）。

本轮据此重做了修复：**按行号就位**（而不是按读窗出现顺序拼接）、**优先取重建目标 revision 的整份读窗**、缺口用 TASK-044 备份按锚点回填。
逐文件的结果与仍然无解的部分见 §3 / §4。

**实测结果**（同一个计数器重算，见 §5.3）：修复前 TASK-082 build 3（`-k`）＝**1,357 错误行 / 43 个文件**；
本轮 build ②（`-k`）＝**448 错误行 / 21 个文件**（**−67.0% / −51.2%**）。
TASK-082 那 **227 条挂在引擎头文件上的级联已完全消失**；`core` 静态库正常产出、所有失败目标仍在 `modules/mcp_server/**` 之内。
结构受损文件从 **12 个降到 4 个**。

**没有做到的事**（不得含糊）：整树**仍未编译通过**；`bin\` 为空，`--version` 与 `--test-case="[MCPServer]*"` **无实测输出**。
剩余 448 条里有 4 个文件是"关键代码在任何记录里都不存在"（§4.1），我已定位到**具体行号**，但没有替它们编造实现。

---

## 1. 铁律合规

| 铁律 | 执行证据 |
|---|---|
| **1 绝不动 F:** | 全程对 F: 只有只读调用（`Test-Path`/`Get-Item`/`Get-FileHash`/`Get-PSDrive`/`Get-ChildItem`）。§6 给出与 TASK-082 记录的**逐字段相同**证明。没有任何写、删、改、移动。 |
| **2 禁止 shell 重定向** | 全程 **0 条** `>`/`>>`/`*>`/`2>&1`。两次构建一律 `Start-Process cmd.exe -ArgumentList '/c', <命令> -RedirectStandardOutput/-RedirectStandardError <绝对路径> -Wait`（`work\task083\build.ps1`）。所有落盘由 Python `io.open(...,'w')` / `open(...,'wb')` 完成；日志解码用 Python 读字节再写。 |
| **3 破坏性命令默认拒绝** | 唯一删除在 `work\task083\clean_residue.py`：先断言**非空 / 绝对 / 不含 `*?` 与 `..` / 前缀为 `H:\rebuild\godot\` / 存在 / 非目录**，**先打印清单（路径 + 字节 + sha256 前 16）**，通过后才 `os.remove`（字面路径、无通配符），逐条回读 `Test-Path=False`。全程无其它删除/移动/重命名。 |
| **4 构建必须从 cmd 启动** | 两次构建都是 `Start-Process cmd.exe /c scons …`，工作目录 `H:\rebuild\godot`；未在 Git Bash 下跑 SCons。 |

---

## 2. ★ 本轮对根因的更正（TASK-082 §5.3 / §5.6 的不完整处）

### 2.1 真正的损伤模型：**gap-collapsed splice**，而不是"头/尾截断"

`staging\__payload-index\reconstruction.jsonl` 里每个文件的 `read_cov` 与**树上该文件的实际行数完全相等**：

| 文件 | read_total（目标 revision） | read_cov | 树上行数 | 结论 |
|---|---:|---:|---:|---|
| `mcp_server.cpp` | 760 | 522 | 522 | 只写了被覆盖的 522 行 |
| `tools/editor_node_read.cpp` | 781 | 501 | 500 | 同上 |
| `tools/running_game_read_scene.cpp` | 395 | 164 | 166 | 同上 |
| `tool_registry.cpp` | 839 | 518 | 593 | 同上（另含跨 revision 碎片） |
| `tools/tool_helpers.h` | 1490 | 1110 | 1110 | 同上 |

即：**缺失的行被直接删掉，而不是留空**，于是文件在**每个空档处**结构断裂：花括号失衡、函数无头、`namespace` 开闭错位。
这解释了 TASK-082 §5.3 里那 9 个"可疑 D 类"文件——它们不是"可疑"，是**确定断裂**。

### 2.2 `mcp_server.cpp` 不只是头丢了，**碎片顺序也是错的**

树上 522 行的实际排布（实测）：

| 树行 | 内容 | 真实位置 |
|---|---|---|
| 1 | `static const int DEFAULT_EDITOR_PORT = 9877;` | 文件第 60 行附近（前面 59 行被丢） |
| 1–119 | `MCPPort` + `MCPPendingTimeout` + ctor/dtor + `_bind_methods` + TASK-063 端点状态访问器 | 尚算连续 |
| **121** | **`(void)p_delta;`** | `pump_frame()` 的**函数体**，签名被丢 |
| 155–238 | `_shutdown` / `handle_jsonrpc_request` | 连续 |
| **240** | `String MCPServer::build_deferred_body(...) {` | 其后**直接接上 `_start_service` 的尾巴**（241–298） |
| 299–302 | `register_all_tools` 注释残片 + `}` | 跨文件碎片 |
| 304–522 | `_start_service` 全函数 | 连续 |

**结论**：`mcp_server.cpp` 的 `_notification`、`_retire_unattached`、`bootstrap`、`pump_frame` 签名、`build_deferred_body` 函数体、
`get_status_body`、`_get_int_setting`、`_get_bool_setting`、`_register_tools` **整个函数都不在树上**。
TASK-082 的"补回文件头"（51 行）会留下 12 处断裂，**不足以让它编译**——本轮改为按函数边界重组。

### 2.3 有比 TASK-082 设想的更好的证据源：**整份读窗**

`events-read.jsonl` 里存在 `offset=1 且 行数 == totalLines` 的**整份快照**。模块 123 个源文件里 **79 个**有这种快照（`work\task083\complete-reads.txt`）。
当快照的 revision **恰好等于重建目标 revision** 时，该文件可以**逐字节复原**。本轮据此逐字复原了：

* `tools/running_game_script_execution.cpp`（rev312 == target 312）
* `tools/editor_node_batch_write.cpp`（rev766 == target 766，766/766 行全覆盖）

并把 `tools/editor_testing_read.cpp`（rev533 → target 539）、`tools/project_validate_scripts.cpp`（rev368 → target 374）
用"目标 revision 行优先 + 后续窗口覆盖"重建。

---

## 3. 已完成的修复（逐步提交、逐步 push）

| 提交 | 步骤 | 内容 |
|---|---|---|
| `74b3443a45` | Step 0 | 三个 A 类文件：`mcp_server.cpp` 按函数边界重组（670 行、括号平衡、`mcp_server.h` 声明的每个成员都有定义）；`editor_node_read.cpp`、`running_game_read_scene.cpp` 按锚点回填缺失行（+277 / +231） |
| `2eebcdc495` | Step 1 | 五个 B/C 类尾部截断文件：`project_write_resource_scene.cpp`(+205)、`running_game_frame_observation.cpp`(+181)、`running_game_node_write.cpp`(+165)、`tool_helpers.h`(+350)、`project_validate_scripts.cpp`（第 338 行 raw string 被截断，补回 `)desc"));`，C1903/C3516 根因） |
| `40bd5693a8` | Step 2 | **G13**：`tools/project_read_files.h` 补回 `namespace MCPTools {` **与紧随其后的 26 行 TASK-050 N-2 注释块**。**逐字复原，非猜测**：树上第 53/54/55 行 == rev211 的第 80/81/82 行，故 rev211 的 53–79 行就是被丢掉的那一段；该段在 rev97/135/186/211 四个窗口里**逐字节相同**。192 → 219 行，括号平衡 |
| `c9514fb879` | Step 3 | 其余被压空档的源文件回填；`running_game_script_execution.cpp`、`editor_testing_read.cpp`、`project_validate_scripts.cpp` 改用整份读窗重建；结构受损文件 **12 → 6** |
| `2a8f7777cc` | Step 4 | 测试头提升（减 9506–9626）+ 三个恢复残渣 guarded 删除 |
| `a9208962fb` | 追加 | `editor_animation_tree_write.cpp` 三处 C2660：调用方是旧 revision，被调方是新的 |

### 3.1 Step 4 的两件事

**(a) 测试头提升**（裁决 (a)）：`rebuild\_low-confidence\modules\mcp_server\tests\test_mcp_server.h`
431,976 B / 9,626 行，**减去 9506–9626 行**（121 行，正是 "Independent acceptance probes (appended by the acceptance agent for one run, then reverted)" 那一块，
块内确有 **3 处** `register_tool`：9535/9557/9607）→ **427,827 B / 9,505 行**，括号平衡，`RegisterToolAccessProbe` 与 3 个 `static_assert` 保留。
工具（`work\task083\promote_test_header.py`）在切之前**打印切口上下文并断言两行标记文本**，切错即拒绝执行。

**(b) 残渣删除**（裁决 (c)）：`modules/mcp_server/gen_b2_restore.tmp.py`（1,487 B）、
`modules/mcp_server/tests/_task044_block.txt`（32,581 B）、`modules/mcp_server/tests/__tmp_task052_tests.txt`（17,102 B），guarded、先打印清单后删。

### 3.2 `editor_animation_tree_write.cpp` 的三处 C2660（**证据驱动，非发明**）

`add_state_machine_state_on` / `add_state_machine_transition_on` / `set_blend_tree_node_on` 的**定义**带
`animation` / `xfade_time` / `priority` / `advance_condition` 参数（rev > 1038；rev1038 窗口里它们只有 7 个参数），
而**调用方**取自录 rev1038 的旧 revision，只传旧参数表。
本文件**自己的注册 schema**（第 1207 / 1214 / 1235 行）明确声明了 `animation`、`xfade_time`、`priority`、`advance_condition`，
故**旧的是调用方**。补的是"读取 schema 已经声明的属性并转交"，没有引入任何契约之外的行为。

---

## 4. ★ 仍然无解的部分（**如实报告，不掩盖**）

### 4.1 把"整份读窗"当证据源之后仍然缺失的行

`work\task083\gapcheck.py` 的实测（目标 revision 下**任何读窗都没覆盖到**的行）：

| 文件 | 目标行数 | 未被任何读窗覆盖的行 | 未覆盖的大块 |
|---|---:|---:|---|
| `tool_registry.cpp` | 839 | **130** | 500–589、800–839 |
| `tools\project_write_resource_scene.cpp` | 852 | **143** | 1–28、740–852 |
| `tools\editor_write_scene_editor.cpp` | 1184 | **192** | 424–494、535–559、1089–1184 |
| `tools\running_game_test_execution.cpp` | 949 | 30 | 655–674、940–949 |
| `tools\running_game_node_write.cpp` | 1281 | 31 | 900–929（**本轮已回填：1281 行、括号平衡**） |
| `tools\editor_node_batch_write.cpp` | 766 | **0** | —（**本轮逐字复原**） |

**`tool_registry.cpp` 是本轮唯一"已知关键、且缺关键代码"的文件**：缺的 500–589 行包含
`_lookup_schema_path()` 的整个函数体与 `_parameter_name_in_message()` 的函数头，
而树上第 490–524 行正是 `_parameter_name_in_message()` 的**无头函数体**（用了 `marker` / `p_message` → 13× C2065 + 5× C2737）。
可逐字复原的部分（rev815 的 416–499 行：`_schema_type_phrase` 尾部、`_schema_options_phrase`、`_schema_form`、`_SchemaPathLookup` 结构体、
`_lookup_schema_path` 的前 11 行）已定位，但**函数体本身在 179 份记录里从未出现**。

**我没有替它编造实现。**理由：`_lookup_schema_path` 是"参数路径 → schema 节点"的语义函数，
`_invalid_params_suggestion()` 依赖它的 `resolved` / `node` / `required` / `array_name` 四个字段产生**面向用户的建议文本**；
凭空写一个只求编译的版本会把"建议文本"的功能静默降级，而这正是本项目纪律禁止的"为了跑通而妥协"。
如需继续，请裁决：(i) 授权我按 docstring 重写该函数（标记 LOW-CONFIDENCE + 行为变更），或 (ii) 提供新的证据源。

### 4.2 结构仍受损的 4 个文件

`work\task083\structural-scan.txt`（全模块 172 个 `.cpp`/`.h` 的花括号/圆括号配对扫描）：

| 文件 | 状况 |
|---|---|
| `tool_registry.cpp` | 第 479 行 `_schema_type_phrase` 的 `{` 未闭合（fatal C1075）→ 级联 8×C2601 + 5×C2267 |
| `tools\project_write_resource_scene.cpp` | 479/482/499 未闭合，535/537 多余 `}` |
| `tools\editor_write_scene_editor.cpp` | 729/778/779 未闭合 |
| `tools\running_game_test_execution.cpp` | 876/881 未闭合，651 多余 `}` |

对比：TASK-082 的同类扫描是 **12 个**文件；本轮降到 **4 个**（`editor_node_batch_write`、`running_game_node_write`、
`running_game_script_execution`、`editor_testing_read`、`project_validate_scripts` 已归零）。

---

## 5. 构建（两轮，均从 cmd、`Start-Process` 落绝对路径日志）

### 5.1 build ①　`scons platform=windows target=editor tests=no -j8`

* 命令：`cmd.exe /c scons platform=windows target=editor tests=no -j8`
* 退出码：**2**　墙钟：**927.1 s**（其中 SCons 自报编译时间 00:00:11.85 —— 绝大部分是依赖扫描）
* 日志：`logs\task083_build1_notests.stdout.txt`（792 B）、`…stderr.txt`（5,535 B）
* 解码后：`work\task083\task083_build1_notests.stderr.utf8.txt`（编译器按 cp936 输出，已用 Python 读字节转 UTF-8）
* **错误总数：34**，错误码：`C2065`×13、`C2601`×8、`C2267`×5、`C2737`×4、`C2660`×3、`C1075`×1

| 文件 | 错误数 | 根因 |
|---|---:|---|
| `tool_registry.cpp` | 31 | §4.1：`_schema_type_phrase` 未闭合 → `_parameter_name_in_message` 无头 → 其后所有函数变成"块作用域函数定义"（C2267/C2601），末了 fatal C1075 |
| `tools\editor_animation_tree_write.cpp` | 3 | C2660（**本轮已修，见 §3.2 / 提交 `a9208962fb`**） |

> 这一轮**不是全量清单**：SCons 不带 `-k`，遇到首批错误即终止，只编译到 `a` 开头的 4 个模块文件。

### 5.2 build ②　`scons platform=windows target=editor tests=no -j8 -k`

* 命令：`cmd.exe /c scons platform=windows target=editor tests=no -j8 -k`
* 退出码 / 墙钟 / 错误总数 / Top 清单：**见 §5.3（本轮结束时填入，不预写）**

### 5.3 build ② 实测

* 命令：`cmd.exe /c scons platform=windows target=editor tests=no -j8 -k`
* 退出码：**2**　墙钟：**954.2 s**
* 日志：`logs\task083_build2_keepgoing_notests.stdout.txt`（4,777 B）、`…stderr.txt`（62,738 B）
* 解码后：`work\task083\task083_build2_keepgoing_notests.stderr.utf8.txt`
* **错误总数：448 行 / 21 个文件**（错误码：`C2065`×85、`C4430`×73、`C2143`×58、`C3861`×39、`C2601`×27、`C2267`×20、`C2059`×19、`C2146`×18、`C2196`×12、`C2371`×11…）

**与 TASK-082 build 3 的同类对比**（`work\task083\recount.py` 用**同一个计数器**重算两轮日志，避免口径不同）：

| 轮次 | error-lines | 文件数 |
|---|---:|---:|
| TASK-082 build 3（`-k`） | **1,357** | **43** |
| **TASK-083 build ②（`-k`）** | **448** | **21** |
| 变化 | **−909（−67.0%）** | **−22（−51.2%）** |

> TASK-082 报告里的"1,575 条错误 / 48 文件"用的是更宽的模式（也匹配 MSVC 的 `note:` 行）。上表用同一模式重算两者，故 1,357 → 448 才是可比数字。

**剩余错误 Top 清单（文件:行 + 根因）**

| # | 文件 | 错误数 | 首错行 | 根因 |
|---|---|---:|---:|---|
| 1 | `tools/tool_helpers.h` | 87 | 83 | 文件**自身**在 83 行处把 `MCPTools::String` 当重定义（C2371/C4430/C2146）——即这份头文件的**命名空间/花括号在其头部就已失衡**，与 TASK-082 的 R4/R5 同源；回填 +350 行未触及该处 |
| 2 | `tools/running_game_frame_observation.cpp` | 47 | 204 | `node_id` 未声明（C2065）→ `if` 语法错（C2059/C2143/C2447）：该处仍是一个未闭合的块边界 |
| 3 | `tools/running_game_test_execution.cpp` | 42 | 424 | §4.1：655–674 行不可复原，就位后该区域内容错位（`else`/`next`/`TestScenarioTask` 基类成员） |
| 4 | `tools/tool_helpers.cpp` | 34 | 254 | `case` 值重复（C2196，TASK-082 R 项原样存在）；2842 行 `_ReloadCapture::report` 未声明（C3646/C2039） |
| 5 | `tools/editor_node_batch_write.cpp` | 32 | 162 | **即使是 rev766 的"整份就位"版本仍报 `_later_element_requesting` 块作用域非法 + 281 行 C2870**——说明重建目标 revision 766 本身晚于/早于事故终态，或该 revision 的窗口仍是部分件。这是本轮**最出乎预料**的一条 |
| 6 | `tools/tool_builder.h` | 32 | 71 | 头部 71/78 行本地语法错（C2061/C4430） |
| 7 | `tool_registry.cpp` | 31 | 490 | §4.1：`_lookup_schema_path` 函数体不可复原 |
| 8 | `tools/project_cross_scene_write.h` | 24 | 118 | 118 行 `Node` 未声明 —— 丢的是 **include 行**，非正文 |
| 9 | `tools/running_game_node_write.h` | 22 | 59 | 头部把 `int MCPTools::Variant` 判为重定义（C2086/C4430/C2146） |
| 10 | `tools/editor_write_scene_editor.cpp` | 17 | 749 | §4.1：1089–1184（整个尾部）不可复原 → 749/769/812 级联 |
| 11 | `tools/editor_script_write.cpp` | 16 | 142 | `build_execute_gdscript_source` 被以 4 个参数调用（C2661）——与 §3.2 同类"调用方旧、被调方新"的漂移 |
| 12 | `tools/project_write_resource_scene.cpp` | 15 | 375 | §4.1：`_require_properties` 未声明 + 508 行语法错 |
| 13 | `tools/running_game_node_write.cpp` | 15 | 119 | `vector_from_dictionary` 局部函数非法 + 646 行 `_node_path_for_result` **重复定义**（C2084） |
| 14 | `tools/editor_input_simulation.cpp` | 12 | 375 | `_number_fits_event` 等若干静态助手未声明（C3861） |
| 15 | `tools/editor_node_write.cpp` | 7 | 383 | `_optional_dictionary` 未声明（C3861） |
| 16 | `tools/project.cpp` | 4 | 273 | `register_tool` 回调签名不符 + C2248 private（与 TASK-082 §5.5 的 GDR-19 同源） |
| 17 | `tools/editor_read_scene_inspector.cpp` | 3 | 225 | `_require_editor_ui` 未声明 |
| 18 | `tools/project_validate_scripts.cpp` | 3 | 84 | 84 行 `json` 未声明 + 92 行 `_schema_from_json` 未声明（该文件被整份重建后，**局部**仍有跨 revision 漂移） |
| 19 | `tools/editor_node_setup.h` | 2 | 36 | `Color` 前置声明 class/struct 不一致（C4099） |
| 20 | `tools/editor_node_setup.cpp` | 2 | 796 | `_schema_from_json` 未声明 |
| 21 | `tools/editor_control_layout_write.cpp` | 1 | 123 | `_relative_path` 未声明 |

**引擎侧**：`core` 静态库本轮**正常产出并 ranlib 成功**（`Linking Static Library bin\obj\core\core.windows.editor.x86_64.lib`）；
所有失败目标仍在 `modules/mcp_server/**` 之内。TASK-082 那 227 条"挂在引擎头文件上"的级联**已消失**（`core/object/object.h` 等不再出现在错误里）——
这是 G13（`project_read_files.h` 的 `namespace MCPTools {`）修复的直接效果。

### 5.4 build ③（`tests=yes`）

**未执行**：build ② 仍为红，`tests=yes` 只会重复同样的模块错误而多付一次构建（这个判断与 TASK-082 §5.1 `module_mono_enabled` 的处理一致，非静默跳过）。

---

## 6. 收尾：push、git 状态、F: 未触碰证据

### 6.1 push

| 提交 | push 结果 |
|---|---|
| `74b3443a45` / `2eebcdc495` / `40bd5693a8` / `c9514fb879` / `2a8f7777cc` | `f4b6b92925..2a8f7777cc  feature/mcp-server-module-rebuild -> feature/mcp-server-module-rebuild`（exit 0） |
| `a9208962fb` / `be6aa88c8c` | `2a8f7777cc..be6aa88c8c  feature/mcp-server-module-rebuild -> feature/mcp-server-module-rebuild`（exit 0） |

`git rev-parse HEAD` = `be6aa88c8c2ca586345095c5ce8c112dc9d2a892`，
`git rev-parse origin/feature/mcp-server-module-rebuild` = **同一 sha** → 无未推送提交。

### 6.2 `git log --oneline -6`

```
be6aa88c8c modules/mcp_server: task083 build evidence - 1357 -> 448 error lines, 43 -> 21 files; module still RED
a9208962fb modules/mcp_server: task083 - reconcile the three stale call sites in editor_animation_tree_write.cpp
2a8f7777cc modules/mcp_server: task083 step4 - promote the test header (minus the transient probes) and remove the recovery residue
c9514fb879 modules/mcp_server: task083 step3 - gap-fill the remaining gap-collapsed sources
40bd5693a8 modules/mcp_server: task083 step2 - restore project_read_files.h namespace opener (G13)
2eebcdc495 modules/mcp_server: task083 step1 - restore the tail-truncated sources (class B/C)
74b3443a45 modules/mcp_server: task083 step0 - restore the three head-damaged sources
```

### 6.3 `git status --short`

```
（空）
```

### 6.4 F: 未触碰（只读探测，与 TASK-082 记录逐字段对照）

| 观测项 | TASK-082 记录 | 本轮实测 | 判定 |
|---|---|---|---|
| `F:\moonbit-hof-rs\DECISIONS.md` 字节 | 537,251 | **537,251** | 同 |
| …`LastWriteTimeUtc` | 2026-09-25T15:11:18.8118814Z | **2026-09-25T15:11:18.8118814Z** | 同 |
| …`sha256` | `114B2A82…9CF323` | **`114B2A8218E35DF8E998FA4329D99F97D6037987E19FBA4A324B567C009CF323`** | **同** |
| `Get-PSDrive F` `Used` / `Free` | 922,841,124,864 / 392,138,186,752 | **同** | **同** |
| `F:\RustProjects\godot-mcp-pro\code\godot` 子项数 | 0 | **0** | 同 |
| `F:\…\tests\fixtures\mcp\tools_list.json` | `8F8051C4…313C54` / 48,749 B | **同** | 未变 |

探测脚本：`work\task083\fprobe.ps1`（纯 ASCII、只读）。**零写入。**

---

## 7. 终态记录

* **HEAD**：`be6aa88c8c2ca586345095c5ce8c112dc9d2a892`　**== origin**（已 push）
* **`git status --short`**：空
* **`git log --oneline -6`**：见 §6.2
* **门禁（未达成，不得声称达成）**：
  * 整树**仍不可编译**（build ① / ② 均 exit 2）
  * `bin\` 里**没有任何 `*.exe`**（只有 `D3D12Core.dll`、`d3d12SDKLayers.dll` 与 `obj\`）→ `--version` 与 `--test-case="[MCPServer]*"` **没有实测输出**
* **可提交物**：7 个提交（4 个修复步骤 + 1 个调用方对齐 + 1 个证据 + 1 个 build 证据），21 个证据文件已入树
  `modules\mcp_server\docs\reports\evidence\task083\`
* **置信度标签**：凡"来自 TASK-044 备份的回填跨度"与"按函数边界重组的 `mcp_server.cpp`"均为 **LOW/MID confidence reconstruction**，
  逐文件来源见 `splice-report.json` / `rebuild-report.json` / `place2-report.json` / `shas-before.json`。

---

## 8. 需要决策者裁决的点

1. **`tool_registry.cpp` 的 90 行**（`_lookup_schema_path()` 函数体 + `_parameter_name_in_message()` 函数头）在任何记录里都不存在。
   选项：(i) 授权按 docstring 重写（LOW-CONFIDENCE + 会改变建议文本）；(ii) 提供新证据源；(iii) 接受该文件不可编译。
2. **`project_write_resource_scene.cpp`（143 行）/ `editor_write_scene_editor.cpp`（192 行）** 同样缺关键块，
   其中 `editor_write_scene_editor.cpp` 的 1089–1184 行是**整个文件尾部**（含注册函数）。
3. **G13 的修复改变了包含关系**：`project_read_files.h` 现在真的开了 `namespace MCPTools {`，
   所有 include 它的 TU 的符号查找随之改变——这是**正确**的（`.cpp` 侧本来就有 `using namespace MCPTools;`），但请知悉这是一处契约性变化。
4. **`tools/project_validate_scripts.cpp` 第 338 行**的 raw string 曾被截断，本轮补回 `)desc"));`。补的是**词法闭合**，
   描述正文本身仍取自读窗（990 字节），我没有改动正文一个字符。
5. **是否继续 2c-3**：以"把 §4 剩下的 4 个文件按 docstring 重写"为范围，目标是把 build 推到绿。

---

## 9. 本轮**没有**建立的东西

* **没有**建立"整树可编译"。build ①/② 都是红。
* **没有**产出任何 `bin\*.exe`（`bin\` 只有 `D3D12Core.dll` / `d3d12SDKLayers.dll` / `obj\`），因此 `--version` 与 `--test-case="[MCPServer]*"` **没有实测输出**（§5.4）。
* **没有**逐字复原 `mcp_server.cpp`：它是按函数边界从"备份骨架 + 树上最新正文"重组的，**670 行 ≠ 目标 760 行**，
  差的部分是 640→760 之间未读到的块。置信度：中低。
* **没有**恢复 TASK-044 备份里**晚于备份 revision 的**修改：凡是回填来自备份的跨度，都可能是旧版本正文。
  逐文件来源见 `work\task083\splice-report.json` / `rebuild-report.json` / `place2-report.json`。
* **没有**触碰 F:，也没有恢复 `.git` 历史、契约终值、`bin\`（这三件在 TASK-080 已判定永久丢失）。
