# TASK-082 — 2c-1：把重建树推进到**可构建**（REPORT）

* 生成时间：2026-09-26T12:1x+08:00
* 工作树：`H:\rebuild\godot`　分支：`feature/mcp-server-module-rebuild`
* 起点：`54200f0d77`　终点：`f4b6b92925`（**已 push，HEAD == origin**）
* 报告：本文件。原始证据：`C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\`、`…\logs\`、以及**树内** `modules\mcp_server\docs\reports\evidence\task082\`

---

## 0. 一句话结论

**四件事全部执行完毕并各自提交、各自 push。** ①13 个低置信源文件已提升（含逐份证据，其中 3 份经独立证明**确为截断**）；②3 个 `b2*.tmp.*` 残留已 guarded 删除；③生成器修复 + 契约重生成，**全部要求数字通过**（177 / 6 / 1.22.0 / 154 / 73 / 幂等），但 sha 与原值 `a5c59853…` **仍不相同，如实报告**；④**构建为红**：三次构建，权威清单 = **1,575 条错误 / 48 文件 / 38 个失败目标，全部 38 个都在 `modules/mcp_server` 之内**（引擎 `core`/`thirdparty` 静态库正常链接）。**根因已定位到 file:line，其中一条（`tools/project_read_files.h` 丢失 `namespace MCPTools {`）不在 TASK-081 的 G1–G12 清单里，是本轮新证据。**

---

## 1. 铁律合规（§0）

| 铁律 | 执行证据 |
|---|---|
| **1 绝不动 F:** | 开工 `2026-09-26T11:46:50`：`DECISIONS.md` 537,251 B / `114B2A8218E35DF8E998FA4329D99F97D6037987E19FBA4A324B567C009CF323` / `LastWriteTimeUtc=2026/9/25 15:11:18`；`Get-PSDrive F` `Used=922,841,124,864 / Free=392,138,186,752`；`code\godot` children=0。收尾 `12:12:06`：**四项逐字段相同**（§6）。对 F: 的全部操作只有 `Get-Item`/`Get-FileHash`/`Get-ChildItem`/`Get-PSDrive`，以及生成器对 `F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json` 的 `open(...,'r')` 只读读取——该文件两次生成前后 sha 均为 `8F8051C4C0F8941089F0B21A193CEF7C51FA7C41D7E312B1463EA8593F313C54`（= 生成器内冻结常量，未变）。 |
| **2 禁止一切 shell 重定向** | 全程 **0 条** `>` / `>>` / `*>` / `2>&1`。三次构建一律 `Start-Process cmd.exe -RedirectStandardOutput/-RedirectStandardError <绝对路径>`。落盘一律 `[IO.File]::WriteAllLines` / `[IO.File]::WriteAllText` / Python `open(...,'w')` / `Copy-Item`。日志解码（cp936→UTF-8）用 Python 读字节再写，不经 shell。 |
| **3 破坏性命令默认拒绝** | 唯一删除在 `work\task082\clean_residue.ps1` 内：先断言非空 / 绝对 / 不含 `*?..` / 位于 `H:\rebuild\godot\` 前缀 / 存在 / 非目录，**打印待删清单**，再以 glob `b2*.tmp.*` 的匹配集**交叉校验**字面清单（`Compare-Object` 不等则 `throw` 且不删），通过后才 `Remove-Item -LiteralPath`（无通配符）。全程无其它删除/移动/重命名。 |
| **4 绝对路径 / .ps1 纯 ASCII / 构建从 cmd 启动** | 所有路径绝对；新建的 3 个 `.ps1` 为纯 ASCII；三次构建均由 `Start-Process cmd.exe /c …` 在 `H:\rebuild\godot` 下启动（未在 Git Bash 下跑 SCons）。 |

---

## 2. ① 提升 13 个低置信源文件

**提交**：`b0fcceb381`（13 files changed, 12,116 insertions）→ push `54200f0d77..b0fcceb381` exit 0。

来源：`C:\Users\wyl\AppData\Local\Temp\mcp-recovery\rebuild\_low-confidence\modules\mcp_server\`。
逐份记录（路径 | 来源 | 字节 | 置信度=2A 读取覆盖率 | 已知可疑处）完整版在 `work\task082\promoted-lowconf.txt` 与树内 `evidence\task082\item1-promoted-lowconf.txt`；下表为摘要（sha 源=目标，13/13 全部相等）：

| 路径 | 字节 | sha256(前16) | 置信度 | 已知可疑处 |
|---|---:|---|---:|---|
| `mcp_capture.h` | 13,549 | `1CFD5D172DFCE901` | 8.8% | — |
| `tools\editor_animation_tree_write.cpp` | 58,985 | `5FB726B8AB5A7401` | 13.7% | 尾部无 namespace 闭合 |
| `tools\editor_control_layout_write.cpp` | 10,401 | `D2766133B32A1D22` | 34.2% | 尾部无 namespace 闭合 |
| `tools\editor_node_read.cpp` | 21,233 | `0477C57193AB5038` | 64.1% | **头部截断**（无 licence/include）、花括号 +2、无 copyright |
| `tools\editor_playback.cpp` | 29,222 | `DA8CA8930AC78C17` | 100.0% | 尾部无 namespace 闭合 |
| `tools\editor_read_scene_inspector.cpp` | 24,190 | `4E02EDBF1C3D9C02` | 55.1% | 尾部含 `@@REGISTRATION_BLOCK@@` 占位符 |
| `tools\editor_write_scene_editor.cpp` | 31,738 | `9FE085A9DAC665D7` | 61.1% | **尾部在 raw string 中间截断**、花括号 +5 |
| `tools\project_read_analysis.cpp` | 40,722 | `B286661BBEF7123D` | 46.5% | 尾部无 namespace 闭合 |
| `tools\project_write_resource_scene.cpp` | 24,324 | `006E0DBA6F82189F` | 62.2% | **尾部在注释中间截断**（`// two apart.`） |
| `tools\running_game_assertion.cpp` | 32,801 | `F61EDCB1E3991CB9` | 40.7% | 尾部无 namespace 闭合 |
| `tools\running_game_node_write.cpp` | 55,362 | `6F238776018139AB` | 91.6% | **尾部 `// END generated` 截断**、花括号 +4 |
| `tools\running_game_observation.cpp` | 36,895 | `DDC5B5DC12696F03` | 52.4% | registration 为**空** BEGIN/END generated 块 |
| `tools\tool_helpers.cpp` | 155,309 | `B90691597BEEC70C` | 49.1% | — |

**未被掩盖**：报告点名"看似完整"的 4 份里，`registration.cpp` 早已在树内（17,014 B，与 LC 同尺寸）；`editor_playback.cpp` 在本批内；另两份（`docs\DESIGN-DETAIL.md`、`docs\tool-groups-b5.json`）是文档/关卡输入，**不在**"12 个 `.cpp` + `mcp_capture.h`"的 13 份范围内，故本轮未提升——如需请裁决。
**交叉发现**：这 13 份里有 3 份（`editor_node_read.cpp`、`project_write_resource_scene.cpp`、`running_game_node_write.cpp`）在 §4 的结构扫描中被**独立证明为截断文件**，即提升它们只恢复"路径存在"，不恢复"可编译"。

---

## 3. ② 清理 `b2*.tmp.*` 残留

**提交**：`8af1aa6968`（3 files changed, 471 deletions）→ push `b0fcceb381..8af1aa6968` exit 0。

guarded 清单（先打印后删，逐条 `path bytes`）：

| 文件 | 字节 | git blob |
|---|---:|---|
| `modules/mcp_server/b2contract.tmp.json` | 4,756 | `9a6acc19794dbf28` |
| `modules/mcp_server/b2map.tmp.json` | 4,605 | `41b365b82cd5d7bf` |
| `modules/mcp_server/b2reasons.tmp.txt` | 1,017 | `335b2b6e527d6265` |

删除后逐一 `Test-Path=False`；树内 `b2*.tmp.*` 命中数 3→0；`git status --short` 无其它变更。guard 日志：`work\task082\clean_residue.ps1`（+ 运行输出见 `logs\`）。
**如实说明（未做）**：`modules/mcp_server/gen_b2_restore.tmp.py` 属 TASK-081 报告 §6.1/§9.3 点名的同一批恢复残渣，但**不匹配** `b2*.tmp.*` 通配式，故按任务书字面范围**未删**，已在提交信息与本报告中标出，建议下一轮一并清理（连同 §4 发现的 `tests\_task044_block.txt` 32,581 B、`tests\__tmp_task052_tests.txt` 17,102 B）。

---

## 4. ③ 契约重生成

**提交**：`b965865a64`（2 files changed, 86 insertions, 30 deletions）→ push `8af1aa6968..b965865a64` exit 0。

### 4.1 三项要求逐条

| 要求 | 事实 | 处理 |
|---|---|---|
| `GENERATOR_VERSION` → `1.22.0` | 树内**本就是** `1.22.0`（line 500）。原始 `_low-confidence` 副本是**旧的** `1.3.0`，两者**只差这一个字符串**（118,450 vs 118,449 B，byte-diff 从 32,455 起、其余为位移） | **无需修改，已验证并如实记录**（不假装修过） |
| **去掉重复块** | **真实存在**：`SCHEMA_OVERRIDES` 的字面 key 有 **13 个但只有 12 个不同**——`"play_scene"` 重复（line 701 与 line 728）。`ast.literal_eval` 会**静默吞掉**重复 key，故此前 2B 报告的"重复"是**真**的，但被复述得含糊：真正重复的只有 `play_scene` 一个 key，不是 `play_scene` + `find_signal_connections` 两处（后者是 desc/schema 各一条的**合法配对**） | 删掉**第一个**（line 698–723，死代码：Python dict 后者胜出）→ **行为不变**的纯清理。修前 raw=13/distinct=12，修后 **12/12，dups=NONE** |
| **能补的 override 补上** | TASK-076A 的 **3 条 append-only 记录**（`get_scene_tree`、`tilemap_set_cell`、`tilemap_fill_rect`，docstring 有描述、表里全缺）**可逐字节恢复**：`REPORT-076 §1.2` 记录 42→**898**、27→**717**、30→**720** B；两个 tilemap 文本**在 `tools/editor_tilemap_write.cpp:532/:538` 的 C++ 字面量里逐字存在**（727−10=**717**、730−10=**720**），`get_scene_tree` 全文在 `REPORT-076` line 55（**898** ✓）。并恢复 `SCENE_TREE_ADDRESSABILITY_SENTENCE`(855 B) / `TILEMAP_ATLAS_GAP_SENTENCE`(689 B) 两个模块级字面量与 `_T076_TILEMAP_GAP_REASON` | **已补 3 条**，`_meta.overrides` 21 → **24**。`reason` 的**措辞**是依 `REPORT-076 §1.3`（REPORT-075 §5 D4 / §6 D5 的实测事实）转写，**不是**逐字节恢复的原件——此点必须视为重建判断 |

> **其余 12 条缺失记录未补**：记录口径要求 `overrides = 36`，现为 24。差额（12）对应 v1.19/v1.20/v1.21 各版本的记录，其 `reason`/`value` 文本在可信证据中**没有逐字来源**，编造即伪造，故**不补**。

### 4.2 验证（全部实测，两次连跑）

| 判据 | 要求 | 实测 | 判定 |
|---|---|---|---|
| `_meta.count` | 177 | **177** | PASS |
| `_meta.added_count` | 6 | **6** | PASS |
| `_meta.generator_version` | 1.22.0 | **1.22.0** | PASS |
| 编辑器端点 | 154 | **154**（104 `editor_*` + 48 `project_*` + 2 `os_*`：`os_list_android_devices`、`os_deploy_to_android_device`） | PASS |
| 游戏端点 | 73 | **73**（23 `running_game_*` + 48 `project_*` + 2 `os_*`） | PASS |
| 幂等（连跑两次同 sha） | 相同 | run1 = run2 = `f07a62fcf2612efb3b6585e3a3fd64a8b2b447f7fe995d29f1ea5069372c8bc3`，**134,720 B** | PASS |
| 三处描述字节 | 898/717/720 | **898 / 717 / 720**，且原文逐字在句首 | PASS |
| `inputSchema` 稳定性 | 不得移动 | 177/177 条与修前**逐字节相同**；仅 3 条 description 移动 | PASS |
| 生成器自检 | — | `self-checks = OK (lint 177/177, unique 177/177, disposition enum OK)` | PASS |

### 4.3 sha 差异（**不得伪造等价**）

```
修前（TASK-081 叠加件）: 078433de71db6a6da9190e4e9434dbed0376139c88fe19638b4251aff55d8b5c  129,016 B
本轮修后              : f07a62fcf2612efb3b6585e3a3fd64a8b2b447f7fe995d29f1ea5069372c8bc3  134,720 B
事故前终值（记录）     : a5c59853c1e5a4913d600c663c8e972f058f7144869ec20337ab41b7a7bb17ea  163,520 B
```

**仍不相等。** 差值 **−28,800 B**。原因可量化：`_meta.overrides` **24 vs 记录的 36**（差 12 条记录 ≈ 差额的主体），其余为描述文本措辞差异。**本轮把 21→24，使产物更接近终值，但没有、也不声称达到终值。**

---

## 5. ④ 构建到红/绿

### 5.1 构建矩阵（全部从 **cmd** 启动，`Start-Process -RedirectStandardOutput`，无重定向）

| # | 命令 | 退出 | 耗时 | 结果 |
|---|---|---|---|---|
| 1 | `scons platform=windows target=editor tests=yes -j8` | 非 0 | **22 s** | 在 `tests/test_main.cpp` 处停：**8 × C2248**，全在 09-22 化石 `modules/mcp_server/tests/test_mcp_server.h`（行 1253/1270/1283/1298/1309/1327/1352/1390） |
| 2 | `scons platform=windows target=editor tests=no -j8` | 非 0 | **188 s** | 在 `modules/mcp_server/mcp_server.cpp` 处停：**109 条错误自 line 4 起**。模块源是**第一个**失败的；`bin\obj\core\core.windows.editor.x86_64.lib` 正常产出 |
| 3 | `scons platform=windows target=editor tests=no -j8 -k` | 非 0 | **635 s** | **权威清单：1,575 条错误 / 48 文件 / 38 个失败目标——38 个全部在 `modules/mcp_server` 内** |

**日志路径（绝对）**

* `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs\task082_build1.txt` / `.err.txt`（原 cp936）
* `…\logs\task082_build2_notests.txt` / `.err.txt`
* `…\logs\task082_build3_keepgoing.txt` / `.err.txt`
* 解码后 UTF-8 + 汇总：**树内** `modules\mcp_server\docs\reports\evidence\task082\`（`build1/2/3.*`, `item4-build3-errors-summary.txt`, `item4-truncation-classes.txt`, `README.md` 含完整修复计划）

**`module_mono_enabled=yes` 未试**（任务书写"再按需"）：模块在不带 Mono 时都不编译，Mono 只会**重复同样的错误**而多付一整次构建；该判断记录在 `evidence\task082\README.md`，非静默跳过。

### 5.2 前 N 条编译错误（file:line + 根因 + 归属）

错误码分布：`C2065` 316、`C4430` 198、`C3861` 167、`C2143` 161、`C2059` 111、`C2653` 73、`C2146` 63、`C3646` 58、`C2447` 55、`C2825` 32、`C2510` 32、`C2601` 30 …… 其中 `C2267`/`C2601`（"块作用域函数定义非法"/"局部函数定义非法"）与 `C2870`（"命名空间定义必须出现在文件作用域"）**只在同一 TU 前面有 `{` 或 `namespace` 未闭合时出现**。

| # | file:line | 首错 | 根因 | 归属 |
|---|---|---|---|---|
| 1 | `modules/mcp_server/mcp_server.cpp:4` | `C2143` / `C4430` | **文件头丢失**：首行即 `static const int DEFAULT_EDITOR_PORT = 9877;`，无 licence、无 include、无 `namespace`。`MCPPortConfig`/`MCPServer` 等全部未声明 → line 82 起 `C2653 'MCPServer': 不是类或命名空间名` | `mcp_server.cpp` 全文件（109 条，末了 `fatal C1003`） |
| 2 | `modules/mcp_server/tools/running_game_read_scene.cpp:1` | `C2059` `if` | **文件内部碎片**：首行 `if (p_a.distance != p_b.distance) {`（在某比较器函数体中间），末行 `for (int i = 0; i < keep; i++) {`（在函数中间）。它既没有头也没有尾 | `running_game_read_scene.cpp` 全文件（106 条） |
| 3 | `modules/mcp_server/tools/editor_node_read.cpp:9` | `C2143`/`C4430` | **文件头丢失**：首行是分隔注释，无 licence/include；`require_string` / `MCPToolError::invalid_params` 全未声明 | `editor_node_read.cpp`（101 条） |
| 4 | `modules/mcp_server/tools/tool_helpers.cpp:254` 起 | `C2196` `case 值 "12" 已使用` | **块级重复**：`case` 标签成组重复（12/13/29/30/31/32/33/34/35/36/37/38…），说明写入时同一段被拼接了两次 | `tool_helpers.cpp`（106 条，末了 `fatal C1003`） |
| 5 | `modules/mcp_server/tools/running_game_node_write.cpp:85` | `C2601` 非法局部函数定义 | 前面有 `}` 缺失；line 200 直接给 `C2870 'MCPTools': 命名空间定义必须出现在文件作用域`。尾部又是 `// END generated`（截断） | `running_game_node_write.cpp`（103 条） |
| 6 | `modules/mcp_server/tools/tool_helpers.h:83` | `C2371 'MCPTools::String': 重定义，不同的基类型` | 该 TU 在到达 `tool_helpers.h:83` 前，命名空间/花括号已失衡（见 R4/R5），于是 Godot 的 `String`/`Variant` 被解析为 `MCPTools::` 成员；**并由此级联出 227 条挂在引擎头文件上的错误** | `tool_helpers.h`（87 条）+ `tool_builder.h`（32 条）+ 级联 |
| 7 | `modules/mcp_server/tools/editor_input_simulation.cpp:189` | `C2672 vformat 找不到匹配的重载` | `C2267`/`C2601` 成串出现——同样的未闭合 `{` 机制 | `editor_input_simulation.cpp`（90 条） |
| 8 | `modules/mcp_server/tools/editor_node_batch_write.cpp:153` | `C2267`/`C2601` `_later_element_requesting` | 块作用域函数非法 + `C3861` 找不到 `_pending_path_for`/`_pending_path_matches` → 前面丢了块边界 | `editor_node_batch_write.cpp`（73 条） |
| 9 | `modules/mcp_server/tools/editor_node_setup.cpp:100` | `C2059` `)` / `++` / `<` / `for` | 同一 TU 前面未闭合 | `editor_node_setup.cpp`（69 条） |
| 10 | `core/object/object.h`（132）、`core/io/resource.h`（40）、`core/object/method_info.h`（20）、`core/object/property_info.h`（16）、`scene/main/node.h`（15） | `C2039`/`C2059`/`C2143`/`C3646` | **级联，不是引擎缺陷**：仅出现在包含破损模块头的 TU 里；`core`/`thirdparty` 静态库已成功链接 | 归属模块头（见 R4/R5） |

模块内错误数前 15 名：`mcp_server.cpp` 109、`running_game_read_scene.cpp` 106、`tool_helpers.cpp` 106、`running_game_node_write.cpp` 103、`editor_node_read.cpp` 101、`editor_input_simulation.cpp` 90、`tool_helpers.h` 87、`editor_node_batch_write.cpp` 73、`editor_node_setup.cpp` 69、`running_game_script_execution.cpp` 59、`project_write_resource_scene.cpp` 47、`running_game_frame_observation.cpp` 44、`editor_testing_read.cpp` 37、`tool_registry.cpp` 35、`tool_builder.h` 32。

### 5.3 结构扫描：全模块 172 个 `.cpp`/`.h` 的确定性与可疑清单

完整表：`work\task082\truncation-classes.txt`（树内同件 `item4-truncation-classes.txt`）。

* **A 类（头截断，确定）3 个**：`mcp_server.cpp`、`tools/editor_node_read.cpp`、`tools/running_game_read_scene.cpp` —— 其余 169 个源文件都以下载 licence 块开头。
* **B 类（尾截断，确定）5 个**：`tools/project_write_resource_scene.cpp`（`// two apart.`）、`tools/running_game_frame_observation.cpp`（`if (!game_framebuffer_available()) {`）、`tools/running_game_node_write.cpp`（`// END generated`）、`tools/running_game_read_scene.cpp`（`for` 头）、`tools/tool_helpers.h`（孤立 `//`）。
* **C 类（字符串/注释未闭合，确定）1 个**：`tools/project_validate_scripts.cpp`（MSVC 报 `C1903`/`C3516`）。
* **D 类（尾部正常但花括号/圆括号失衡，可疑）9 个**：`tool_registry.cpp`(+3)、`editor_input_simulation.cpp`(+2/+2)、`editor_node_batch_write.cpp`(+1)、`editor_node_setup.cpp`(−1)、`editor_node_write.cpp`(+6)、`editor_write_scene_editor.cpp`(+5)、`project_read_files.h`(−1)、`running_game_script_execution.cpp`(−1)、`running_game_test_execution.cpp`(+8)。
* **确定损伤合计 8 个文件**（A∪B∪C）；加可疑共 17 / 172 带结构红旗。

### 5.4 ★ 本轮新发现（**不在 TASK-081 的 G1–G12 里**）

**G13 — `tools/project_read_files.h` 丢失了 `namespace MCPTools {` 开头**

```
 52: void register_project_read_files_tools(MCPToolRegistry &r_registry);
 53: //   * a server that has `ext`        -> COMPILE: the real `reload()`.
 54: // ---------------------------------------------------------------------------
 55: enum class MCPValidateScriptMode {
 …
190: MCPToolError validate_script_verdict_refusal(const String &p_path, const MCPValidateScriptVerdict &p_verdict);
191:
192: } // namespace MCPTools
```

全文件**没有任何 `namespace MCPTools {`**，却有一个**闭合**。line 53–54 是从**别的文件**串进来的注释块 → 丢的是**块边界**，不只是 `namespace` 一行。line 192 那个孤立的 `}` **在每一个包含它的 TU 里关掉了外层命名空间**，这正是 `C2870` / `C2601` 以及 227 条引擎头级联的机制。该文件同时是 D 类（bd=−1）且在 build 3 中有 6 条自身错误（首错 line 192）。

**其它新发现**：`tools/running_game_read_scene.cpp`（7,665 B，内部碎片）与 `tool_helpers.h` 尾截断（67,121 B）都不在 G1–G12 清单中。

### 5.5 测试阻塞的第二层（R6）

树内 `tests/test_mcp_server.h` 是 **66,392 B / 1,392 行**的 09-22 化石，在 8 处**直接调用** `registry.register_tool(...)`；而 `tool_registry.h:141` 明确把它设为 **private**，唯一 friend 是 `MCPTools::ToolBuilder`（GDR-19 / TASK-003 §1.6）。`_low-confidence` 的 431,976 B / 9,626 行版本才是符合该规则的修订，它含 `RegisterToolAccessProbe` + `static_assert`。
**但它不能整份提升**：其 line 9506–9626 是一段自述为**临时**的块——

```
// Independent acceptance probes (appended by the acceptance agent for one run,
// then reverted). No assertion here is copied from the shipped tests.
```

——并在此调用 private 的 `register_tool` 三次（9535/9557/9607）。整份提升会**原样复制 C2248**。故正确件 =「`_low-confidence` 载荷 **减去 line 9506–9626**」；**这一减法属重建判断，须决策者签字后才可提交**。

### 5.6 修复计划（有序，每步是下一步的门）

| 步 | 动作 | 依据 / 判据 |
|---|---|---|
| **0** | 修复 3 个头截断文件（`mcp_server.cpp`、`tools/editor_node_read.cpp`、`tools/running_game_read_scene.cpp`）。这三份贡献 316 条错误且**从第 1–9 行就失败**，不定它们，后面所有错误都无意义 | 头/尾的**稳定部分**（licence、include 块、namespace 开闭）可从 `C:\Users\wyl\AppData\Local\Temp\mcp044-module-backup\mcp_server\` 取——该目录存有完整旧修订（`mcp_server.cpp` 25,234 B、`editor_node_read.cpp` 30,008 B、`running_game_read_scene.cpp` 18,213 B）。**严禁整份替换**（会把模块静默回退约 30 个任务）；函数体必须从 transcript 读窗口合并 |
| **1** | 修复 5 个尾截断文件（B 类） | 同上规则：优先 transcript 读窗口，TASK-044 备份仅作最后手段 |
| **2** | 修复 `tools/project_read_files.h` 的 `namespace MCPTools {`（G13） | 这是 Step 0 之后**单点收益最高**的修复：它解释了 `C2870`/`C2601` 与 227 条引擎头级联。形状可由其自身 docstring 与 9 个同族 `tools/project_*_read.h` 推定——但**必须是重放而非猜测** |
| **3** | Step 0–2 止血后，**重新核验 9 个 D 类可疑** | 其中若干可能本来就是健康的（D 类明示为"可疑"而非"确定"） |
| **4** | 测试头：提升 `_low-confidence` 载荷 **减去 9506–9626**，再跑 `tests=yes` | 判据：化石那 8 条 `C2248` 消失、且 `static_assert` 仍成立 |
| **5** | 清 `tests\_task044_block.txt`(32,581 B)、`tests\__tmp_task052_tests.txt`(17,102 B)、`gen_b2_restore.tmp.py`(1,487 B) | 同一批恢复残渣，与代码无关 |
| **6** | 重跑 `scons platform=windows target=editor tests=yes -j8`，通过后再试 `module_mono_enabled=yes` | 只有到这一步才允许谈 Mono |

**门禁（本轮未达成，不得声称达成）**：`--version` 与 `--test-case="[MCPServer]*"` **无实测输出**——构建为红，二进制未产出，故**无法**给出。`bin\` 目录不存在。

---

## 6. 收尾：push、git 状态、F: 未触碰证据

### 6.1 push（四次，逐条如实）

| # | 提交 | push 结果 |
|---|---|---|
| ① | `b0fcceb381` | exit **0**：`54200f0d77..b0fcceb381  feature/mcp-server-module-rebuild -> feature/mcp-server-module-rebuild` |
| ② | `8af1aa6968` | exit **0**：`b0fcceb381..8af1aa6968  …` |
| ③ | `b965865a64` | exit **0**：`8af1aa6968..b965865a64  …` |
| ④ | `f4b6b92925` | exit **0**：`b965865a64..f4b6b92925  …` |

`git rev-parse HEAD` = `f4b6b929251e6f954cb0e7ed6c6e7fa8ab7d9142`，`git rev-parse origin/feature/mcp-server-module-rebuild` = **同一 sha** → 无未推送提交。

### 6.2 `git log --oneline -5`

```
f4b6b92925 modules/mcp_server: task082 build evidence - first build is RED, 38 module targets fail
b965865a64 modules/mcp_server: repair gen_renamed_contract.py and regenerate tools_list.renamed.json (1.22.0)
8af1aa6968 modules/mcp_server: remove recovery residue b2*.tmp.* (guarded delete, 3 files)
b0fcceb381 modules/mcp_server: promote 13 low-confidence reconstruction sources (low-confidence reconstruction: must be verified)
54200f0d77 modules/mcp_server: rebuild from session transcripts (fidelity noted in report)
```

### 6.3 `git status --short`

```
（空）
```

（构建产物全部落在被 `.gitignore` 命中的 `bin\`；`git status --short --ignored` 未显示新异常。）

### 6.4 F: 未触碰（前/后逐字段对照）

| 观测项 | 开工 11:46:50 | 收尾 12:12:06 | 判定 |
|---|---|---|---|
| `F:\moonbit-hof-rs\DECISIONS.md` 字节 | 537,251 | 537,251 | 同 |
| …`LastWriteTimeUtc` | 2026/9/25 15:11:18 | 2026/9/25 15:11:18 | 同 |
| …`sha256` | `114B2A8218E35DF8E998FA4329D99F97D6037987E19FBA4A324B567C009CF323` | 同 | **同** |
| `Get-PSDrive F` `Used` / `Free` | 922,841,124,864 / 392,138,186,752 | 同 | **同** |
| `F:\RustProjects\godot-mcp-pro\code\godot` 子项数 | 0 | 0 | 同 |
| `F:\…\tests\fixtures\mcp\tools_list.json`（生成器只读输入） | — | `8F8051C4…8F313C54` / 48,749 B（＝生成器内冻结常量，两次生成后不变） | 只读，未变 |

对 F: 的全部调用均为只读（`Get-Item` / `Get-FileHash` / `Get-ChildItem` / `Get-PSDrive` / Python `open(...,'r')`）。**零写入。**

---

## 7. 需要决策者裁决的点

1. **`_low-confidence` 载荷 minus line 9506–9626 才可提升**（§5.5）——这是一个重建判断，请签字或另指证据。
2. **TASK-044 备份仅作"稳定部分"供体**（§5.6 Step 0/1）——我拒绝整份替换（会静默回退约 30 个任务），但"只取 licence/include/namespace 开闭"这一策略边界需要确认。
3. **`overrides` 24 vs 36**：差的 12 条无逐字证据，我选择**不补**（编造即伪造）。若要求补齐，需要新的证据来源。
4. **`gen_b2_restore.tmp.py` / `tests\_task044_block.txt` / `tests\__tmp_task052_tests.txt`** 是否按残渣一并清理（②只授权了 `b2*.tmp.*`）。
5. **`docs\DESIGN-DETAIL.md`（G3，31,531 B vs 84,486 B）与 `docs\tool-groups-b5.json`（G4）** 未提升，因为不在 ① 的 13 份源文件范围内；如需请指示。

**未被掩盖的事实**：模块**仍不可编译**（38/38 失败目标在模块内）；契约 sha **仍不等于** `a5c59853…`；测试头**仍是化石**；`--version` 与 doctest 的**实测输出不存在**（二进制未产出）。本轮交付的是**可复现的红**与**定位到行**的根因，不是"完成"。
