# TASK-151 — 引擎侧缺陷：游戏进程的 `running_game_execute_gdscript` 在**代码编译不过**后挂死并最终失去 MCP 监听

> 你是**实现子代理**，无上游对话上下文；**本文件是你的唯一任务来源**。
> 落点：引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`，
> 起始 HEAD `15bbf1f50e`，工作树干净）。设计/规范在 `modules/mcp_server/docs/`。
> **本任务由决策者显式授权改动 `modules/mcp_server/**`**（此前对 hof-rs 批次是禁改区，现已解禁，见 D224）。

---

## 0. 一句话目标

**复现并根因修复**：在**游戏进程**里，当 `running_game_execute_gdscript` 的 `code` **编译不过**时，
该端点的 MCP 服务会**不再应答**并最终**失去监听**；按设计它**本应**回 `-32602`（带 `data.parse_error`）
且端点保持可用。修完必须**在游戏进程里**证明"答 `-32602`、端点存活、进程存活"，且**不得**回归既有门。

---

## 1. 缺陷证据（来自 hof-rs 真机冒烟 `runs/smoke-t6`，**两轮可复现**）

- 调用序（游戏端点）：`running_game_execute_gdscript` 共 8 次，前 4 次**成功**（但都回
  `{"result":null,"result_type":"Nil"}`，因为调用方发了裸表达式而非函数体——那是**调用方**的缺陷，已由
  hof-rs 侧另修，与本缺陷无关）；**第 5 次是第一条 `code` 编译不过的请求**，此后**再没收到过应答**。
- 失败在**传输层**：连接建立、请求已发出、**状态行始终不来**（`10060`，ureq 报文
  `Error encountered in the status line`），重试 3 次 × 每次间隔 120 s，全部如此。
- 随后**监听消失**：`10061`（连接被拒）。首次 `10060` → 首次 `10061` 约 **730 s**
  （首次 `10061` 只比最后一次 `10060` 晚约 **7 s**）。
- **编辑器端点同轮全程健康**：同一轮 ids 26..43 的 `editor_*` 调用**全部 `ok`**
  （含 `editor_get_input_actions` / `editor_simulate_input_action` / `editor_get_collision_info` /
  `editor_stop_scene`）⇒ 故障**只局限在游戏进程**。
- **两轮**：pass1 `http://127.0.0.1:65333/mcp`（pid 109964）、pass2 `http://127.0.0.1:63698/mcp`（pid 101872）；
  36 条传输错误全部指向 pass2 的 63698。
- 触发那条 `code` 的字面值是（**关键**）：
  `str(Input.action_press("move_right"))` —— `Input.action_press()` 返回 **void**，
  用其返回值作值在 GDScript 里是**分析期（analyzer）错误**，
  引擎原文：`Cannot get return value of call to "%s()" because it returns "void".`（`modules/gdscript/gdscript_analyzer.cpp:3498`）。
- 端点由**编辑器**的 `editor_play_scene` 创建（它给子进程注入 `--mcp-port`）。

**注意**：本缺陷**不是**"缺功能"——模块**本来就有**编译失败 → `-32602` 的路径（见 §2）。

---

## 2. 已知的实现事实（先读，别重新发现）

`modules/mcp_server/tools/running_game_script_execution.cpp`：

| 行 | 事实 |
|---|---|
| 57-63 | `code` 是 GDScript **函数体**；值只能靠 `return` 传出；代码被编译进 `func _mcp_execute()`，在**服务进程**里执行 |
| 83-85 | **契约原文**：`code` 编译不过是 **`-32602`**（`"does not compile: <verdict>"`） |
| 133-145 | **历史返工**（TASK-063 (d) / TASK-089 (F1)）：曾因**裸 `Script::reload()`** 而只会得到 `Parse error`，故改为**捕获 reload 诊断**；注释里留有当时的真实答案与 stderr |
| 202-232 | 现路径：`set_source_code` → `reload_gdscript_capturing(...)` → 若 `reload.error != OK` ⇒
`MCPToolError::invalid_params(gdscript_reload_failure_text(reload))`，并在能看到诊断时填 `data.parse_error` /
`data.parse_error_line` / `data.parse_error_column` |
| 263-330 | 编译过之后的**运行期**错误 ⇒ `-32000`（TASK-103 X-1），不是 `-32602` |

**与 TASK-089 的关键差别（这是首要假设，须被证实或证伪）**：TASK-089 的捕获是针对 **parse 错误**验证的；
本缺陷的触发是 **analyzer（语义）错误**（void 返回值）。两者在引擎里走的是不同阶段，
且**捕获机制在游戏进程里的安装方式可能与编辑器进程不同**（编辑器会装自己的错误处理/打印钩子）。

---

## 3. 第一步：**最小化复现**（必须先做，且必须落在游戏进程）

> **纪律**：**绝不**使用/占用/探测 **9877**（那是决策者正在用的编辑器，PID 108432）。
> 按引擎惯例只用**测试端口**：编辑器 **9888** / 游戏 **9889**；scratch 放 `%TEMP%`。
> 开局与收尾各做一次端口核对（`scripts\mcp_port_guard.ps1` 或等价物），并登记你自己起的每个 pid 与命令行。

建议步骤（可调整，但必须据实记录真实命令与输出）：

1. 造一个最小 scratch 工程（含场景树，使游戏态脚本可用），`%TEMP%\mcp151\proj`。
2. 起**游戏进程**（注意：游戏侧默认**不监听**，必须显式给端口）：
   `bin\godot.windows.editor.x86_64.console.exe --headless --path %TEMP%\mcp151\proj --mcp-port=9889`
   （若某条路径需要窗口化，改成不带 `--headless`，并记录你用的是哪一种、为什么。）
3. 先确认端点活着：`GET http://127.0.0.1:9889/mcp` 应 200。
4. **第一件事**就发这条**编译不过**的请求（不要先发别的成功调用，以免改变状态）：
   ```json
   {"jsonrpc":"2.0","id":1,"method":"tools/call",
    "params":{"name":"running_game_execute_gdscript",
              "arguments":{"code":"this is not gdscript"}}}
   ```
   以及第二条**analyzer 错误**形态（更接近真实触发）：
   ```json
   {"arguments":{"code":"return str(Input.action_press(\"move_right\"))"}}
   ```
5. 观测：**预期** `-32602` 且带 `data.parse_error`；**实测若挂死**（无状态行）⇒ 缺陷复现。
6. 挂死后按 hof-rs 的时间线继续观测：是否 ~730 s 后**监听消失**、**游戏进程是否退出**（取其退出码）、
   `user://logs/godot.log` 与 stdout/stderr 里有什么（尤其 `SCRIPT ERROR:` / `Parse Error:` / analyzer 原文）。
7. **同时**在**编辑器进程**（`--mcp-port=9888`，编辑器端点）复跑同一请求作为对照：
   编辑器侧**应当**正常回 `-32602`。若编辑器侧也挂，则本缺陷的面比 hof-rs 观察到的更大，**必须记录**。

**产出**：可被判据化的复现件（脚本 + 原始输出 + 时间线），存到 `%TEMP%` 或 `recovery/work/task151/`。

---

## 4. 第二步：根因

围绕下列**假设**取证（允许提出新假设，但每条都要有证据）：

1. **analyzer 错误 vs parse 错误走不同路径**：`reload_gdscript_capturing` 的捕获是否只覆盖 parse 阶段？
   analyzer 报错时的 `reload.error` 是什么？诊断通道是否根本没被触发？
2. **游戏进程 vs 编辑器进程的差异**：编辑器装了错误/打印钩子或 `_err_print_error` 覆写，
   游戏进程没有 ⇒ 某条路径在游戏进程里**没有返回值**（如 `reload()` 内部提前 return / 长跳转），
   或**持有锁**等待一个永不到来的事件。特别检查 `reload_gdscript_capturing` 里是否有
   `Mutex`/`Thread`/`Semaphore`/`print_handler` 安装-卸载配对，以及**错误路径是否会跳过卸载**。
3. **主线程死锁**：MCP 的 HTTP 服务在**主线程**泵帧；主线程若被分析/编译路径卡住，
   就会出现"能连、不应答"。请证明或证伪：用调试器/`--verbose` 日志/心跳（`GET /mcp` 的 `frame_count`
   是否还在增长）判定主线程是否还在泵帧。
4. **进程死亡**：若游戏进程**退出**（而非仅卡住），抓退出码与崩溃证据（Windows 崩溃转储/事件日志）。
   `10061`（连接被拒）更像**监听套接字关闭/进程退出**，而不是单纯死锁——请把这两者区分开。

**禁止**用"看起来像"下结论；每条断言都要能指向文件:行或原始日志。

---

## 5. 第三步：修复与测试（TDD）

1. **先写会失败的测试**（引擎侧 doctest，按模块惯例进 `modules/mcp_server/tests/test_mcp_server.h`，
   或按 `docs/DESIGN-DETAIL.md` §17 的框架落点放）；测试必须在**游戏态**（`is_editor=false`）覆盖
   "编译不过 ⇒ `-32602` 且端点存活"。**确认它现在是红的**，把真实失败输出记进报告。
2. 再做**最小修复**。允许的方向（自行判断，但须写清为什么）：
   - 让诊断捕获覆盖 **analyzer** 阶段；
   - 修正错误路径上的资源/锁/状态处理；
   - 必要时把"分析/编译"移到**不会卡住主线程泵帧**的位置（若确实需要，须在设计文档里写明取舍）。
3. 修完：**在游戏进程里**实测"答 `-32602`、端点存活、进程存活"，并**再测一次运行期错误**
   （能编译但运行失败）仍回 `-32000`（TASK-103 语义**不得**回归）。
4. **回归**：跑引擎既有门 —— 十道门 `g01`..`g10`、`scripts\accept_m1.ps1`（历史记录 **22/22**）、
   以及 `check_contract_subset.ps1`（契约**逐字**不许变）。**任何一条变红都必须先解决或明确上报**。
5. 若修复需要改 `DESIGN-DETAIL.md`（规范），**同时更新文档**并在报告里给出"规范 vs 实现"的对应。

---

## 6. 硬约束

- 不碰 **9877**；自用端口 **9888/9889**（或其它**空闲**测试端口，但必须在报告里登记）。
- **不得**改动 hof-rs 那侧的仓库（`src/**`、`tests/**`、`config/**` 等），也不要动 `.spec/**`。
  本任务只覆盖引擎仓 `godot-mcp/godot/**`（嵌套仓），以及（若确需）本任务书所在仓库的
  `recovery/work/task151/`、`recovery/reports/TASK-151-REPORT.md`。
- 不 `push`（提交留在本地；是否 push 由决策者在独立验收后决定）。**逐条提交**，英文信息带 `(TASK-151)`。
- 不改 `PRD`；不引入新依赖；不删除/放宽既有测试来换绿。
- 不并发运行 scons/构建（引擎惯例：**串行构建**）；不抑制构建输出。
- 不许把"未复现"写成"已修复"；不许把推断写成实测。

---

## 7. 完成后的回报（**只回报报告文件路径**）

报告写到 `recovery/reports/TASK-151-REPORT.md`（若你判断引擎侧惯例另有落点，先在此路径写，
并在报告首行说明真实落点）。必含：

1. **结论**：是否复现（在游戏进程 / 编辑器进程**分别**）、根因、修了什么、是否全绿；
   附**构建与测试命令的真实输出尾部与退出码**；
2. **最小复现件**：真实命令、原始响应/超时输出、时间线（含 `10060`/`10061` 与你观测到的进程状态）；
3. **根因**：文件:行 + 原始日志；明确区分「实测」与「推断」；
4. **修复**：改动清单 + 为什么这么改 + 被改动的既有断言（逐条"原/新/为什么语义等价"）；
5. **门与回归**：`g01`..`g10`、`accept_m1`、`check_contract_subset` 的真实结果；
6. **禁区自查**：真实输出证明未碰 9877、未 push、未改 hof-rs 侧、未改 PRD；
7. **遗留风险与未验证项**；
8. **诚实披露**：返工、猜错、绕过的尝试。

**回报给父代理只有一行：报告文件路径。**
