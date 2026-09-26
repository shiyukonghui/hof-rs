# TOOL-NAMING — Godot MCP 工具命名规范与 174 项对照表

> **文档性质**：规范性（normative）。本文件是工具命名的**唯一表述来源**；机器可读的**唯一事实源**是同目录的
> [`tool-rename-map.json`](./tool-rename-map.json)（`67826` 字节，sha256 `9f5a57e9201b5f7b0b4929c7562eca3345cc8fa280d63fe1079d4bfae302b91b`，174 条）。
> 本文第 2 节的完整对照表由脚本**从该 JSON 生成**，不是手工转录；脚本与断言输出见 `%TEMP%\namdoc\gen_table.py`。
>
> **决策依据**：hof-rs `DECISIONS.md` 的 **D34**（命名审计：三类可复现事故源 + 最高严重度的安全发现）、
> **D38**（用户裁决：一次做全 + 通道前缀 + 因此重做授权判定）、**D41**（174 项映射产出 + 授权判定口径纠正 + 四项开放项判定）。
> 引擎侧配套条款见 `DESIGN-DETAIL.md` §10（工具移植批次 B1–B5，GDR-9）与 §14（GDR-12..GDR-15）。
>
> **本文不做的事**：不重新推导 174 项语义（已冻结在 JSON）；不改任何代码；不改变任何工具的实现行为。

---

## 1. 命名规范

### 1.1 通道前缀（channel）——名字的第一段即作用域自证

形态：**`<channel>_<verb>_<object>[_<qualifier>]`**，即**先通道后动词**。第一段永远只有一个职责：
回答「这个工具**作用在哪个进程/介质上**」，不看文档也能判定。

| 通道前缀 | 定义与判据（取自 JSON `convention.channel_prefixes`） | 工具数 |
|---|---|---|
| `editor_` | 编辑器进程 / 编辑场景 / **编辑器进程内的全局单例**（`Input`、`InputMap`、`AudioServer`、`Performance`、`EditorInterface` 等） | @@CNT:editor@@ |
| `running_game_` | **运行中的游戏进程**（经 `user://` 文件 IPC 或独立进程端口到达游戏侧） | @@CNT:running_game@@ |
| `project_` | **项目磁盘**（文件内容、资源、`.tscn`/`.tres`、`ProjectSettings`、导出预设、脚本与着色器文件） | @@CNT:project@@ |
| `os_` | **外部进程 / 设备**（`adb` 等本机可执行程序与外接设备） | @@CNT:os@@ |

判据的三条关键推论（全部有 JSON `reason` 支撑）：

1. **「谁的状态被改」优先于「谁发起了调用」**。`play_scene` 启动的虽然是游戏，但动作发生在
   **编辑器的播放控制**上（`EditorInterface.play_*`），故 `editor_play_scene`，**不是** `running_game_*`。
   反之 `get_game_screenshot` 读的是游戏侧经 `user://mcp_screenshot.png` 文件 IPC 落下的截图，
   故 `running_game_capture_screenshot`。
2. **单例归属决定通道**。`simulate_*`(5) 与 `get_input_actions`/`set_input_action` 注入的是
   **编辑器进程**的 `Input`/`InputMap` 单例，**根本到不了游戏**——这正是 D27 E3 根因的复现。
   因此它们全部是 `editor_`，而不是任何「游戏输入」语义的名字。
3. **`project_` 与 `editor_` 的边界判据 = 是否作用于编辑器实时状态**（D41 开放项 1）：
   `save_scene`→`editor_`；`create_scene`/`delete_scene`/`get_scene_file_content`/`cross_scene_set_property`→`project_`；
   `analyze_scene_complexity` 主契约是磁盘路径（**仅在 `path` 为空时**回退当前编辑场景）→`project_`。
   同理由 `get_android_preset_info` 解析的是 `res://export_presets.cfg`，介质是项目磁盘，
   故是 `project_get_android_preset_info`，**不是** `os_*`。

### 1.2 动词闭集与每个动词的唯一含义

动词**只能**取自下表 @@VERBCOUNT@@ 个（源自 JSON `convention.verb_closed_set`）。每个动词只允许有**一个**含义；
同一动作**不得**用两个动词表达。表中「用对了」的例子全部是真实新名（可在第 2 节逐行核对）。

@@VERBDEFS@@
**最容易选错的三对动词**（用一句判据解决，实现者按此选词）：

| 该选谁 | 判据 |
|---|---|
| `get_` vs `list_` vs `read_` | 返回值是**一个对象的状态** → `get_`；是**一个集合的元素清单** → `list_`；是**文件/资源的内容本身** → `read_` |
| `find_` vs `search_` | 在**已知容器**里按条件**定位对象** → `find_`；在**一批文件**里按模式找**命中**（哪些文件/哪些行） → `search_` |
| `create_` vs `add_` · `remove_` vs `delete_` | 实体**此前不存在** → `create_` / 从容器**摘掉成员**但实体仍在 → `remove_`；实体**已存在**、只是挂进容器 → `add_` / **实体本身被销毁** → `delete_` |

### 1.3 禁止项

| 禁止 | 为什么 | 反例（旧名 → 应有的新名） |
  取消两对有损合并、`disposition` 枚举化 + `merge_target`、`convention` 补值域与口径条款、三处引文修正），
  未改任何引擎源码或行为；本文档头部与 §7 打印的字节数/sha256 即 v1.1 的真实指纹。
- **契约同源**：`docs/tools_list.renamed.json` 由 `scripts/gen_renamed_contract.py` 从同一份映射机械生成
  （v1.1 = **171** 条），是每批对等门的参照物。
- **本文档自身的指纹**：`TOOL-NAMING.md` 每次生成后的真实字节数与 sha256 由脚本打印在执行输出里。
  **本文档不内嵌自身 sha256**——那会造成自指（本文件字节数/摘要依赖写入前后状态），
  任何「内嵌自身摘要」的做法在数学上都无法自证；可验证的做法是**重复运行**：
  脚本每次运行都会重渲染两次并断言两次渲染结果**逐字节相同**（`DETERMINISM` 段，见 §7），
  并以「写入后读回、逐字节相等」收口。
- **未做的事**：没有重新推导任何一项语义（全部读自 JSON 与 D34/D38/D41/D45 原文）；
  没有修改任何引擎源码、测试或 hof-rs 契约源（旧 fixture 只读）；没有安装依赖；没有占用 9877；
  没有触碰运行中的 Godot 进程（PID 36392）；没有 `git push`。
- **本文件的改动方式**：TASK-001 只通过 `docs/scripts/gen_table.py` 重渲染本文件，**没有手工编辑**任何表格或计数
  （模板里已变化的章节——§2 表头口径、§3 易混淆分组、§4 处置清单、§5 迁移清单、§6 授权判定、§7 证据块——
  全部在 `template.md` 内随生成器一并更新）。