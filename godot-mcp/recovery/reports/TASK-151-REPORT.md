# TASK-151 — 引擎侧缺陷：游戏进程的 `running_game_execute_gdscript` 在 code **编译不过**后挂死并最终失去 MCP 监听

* 执行者：实现子代理（无上游对话上下文，任务书即 `godot-mcp\recovery\tasks\TASK-151.md`）
* 引擎仓：`F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`），起点 `15bbf1f50e`（工作树干净）
  * `c0f2dfba31` **测试（红）**：1 文件 / 151 增 0 删
  * `97fc49df4b` **修复**：3 文件 / 150 增 6 删
  * `035edfce7f` **文档**：`MCP-SERVER-HANDOVER.md` §3 新增 (k) / 31 增 0 删
  * **未 push**（是否 push 由决策者在独立验收后决定）
* 主仓（`F:\moonbit-hof-rs`）：本报告与 `godot-mcp\recovery\work\task151\`（脚本 + 原始证据 + 门日志）**同一提交**
  `chore(recovery): record the TASK-151 debugger-freeze batch …`，**未 push**；提交后主仓工作树干净。
* 脚本 / 原始证据：`godot-mcp\recovery\work\task151\`（`repro.ps1`、`repro_played.ps1`、`repro_peer.ps1`、
  `verify_fixed.ps1`、`run_gates_task151.ps1`、`run_gates_canonical.ps1`、`evidence\`、`evidence-played\`、
  `evidence-peer\`、`evidence-verify\`、`evidence-verify-mono\`、`gates\`、`logs\`）
* 报告：本文件。

---

## 0. 结论表（每行一句话）

| 段 | 问题 | 结论 | 关键证据 |
|---|---|---|---|
| 复现 · 游戏（**无调试器**） | 手起游戏 `--headless --path … --mcp-port=9889`，第一条编译不过的请求 | **未复现**。解析错误 `-32602` **16 ms**、analyzer 错误（`str(Input.action_press("move_right"))`）`-32602` **12 ms**，`data.parse_error` 齐全 | `work\task151\evidence\game-call-1-parse-error.txt`、`game-call-2-analyzer-error.txt` |
| 复现 · 游戏（**编辑器播放**，= 冒烟场景） | `editor_play_scene` 起的孩子（cmdline 带 `--remote-debug tcp://127.0.0.1:6007 --editor-pid 118496`） | **复现**。同一条 body **20 s 内没有任何状态行**；第二条独立连接同样无状态行；`GET /mcp` 连续 **60 s**（6 次采样）无应答；**进程仍活、9889 仍在监听** | `evidence-played\timeline.txt` |
| 复现 · 编辑器（对照） | 9888 上的 `editor_execute_gdscript` | **未复现**。两条 body 都回 `-32602`（9–14 ms），全程健康 | `evidence-verify\editor-*.txt` |
| 根因 | 为什么只有「带调试器的游戏」不应答 | **主线程被引擎的调试器等待停住**：`GDScript::reload()` 的失败路径调 `debug_break_parse()` → `RemoteDebugger::debug()` 的 `while (is_peer_connected())`（`core/debugger/remote_debugger.cpp:444`）。抓到它的判据：把调试器对端释放后，**同一条连接** 23.6 s 后收到 `-32602` | `evidence-peer\timeline.txt` |
| 修复 | 最小改法 | `MCPTools::GDScriptErrorBreakGuard`：在本模块执行调用方代码的窗口内抬起引擎的 `ScriptDebugger::ignore_error_breaks`，退出时还原读到的值；两处 capture（编译窗口 + 执行窗口）各一个作用域 | `tools\tool_helpers.h/.cpp`、`tools\running_game_script_execution.cpp` |
| 修复后（线上） | 真游戏进程 | **34/34 项通过**：播放的游戏 3 ms 回 `-32602`（解析 3 ms、analyzer 3 ms）、运行期错误 4 ms 回 `-32000` + `data.script_error`、成功 2 ms、端点存活、进程存活；编辑器对照不变 | `evidence-verify\checks.tsv` |
| 门与回归 | 十道门 + `accept_m1` + `check_contract_subset` | **canonical（新鲜 mono）9/10 绿**：g01 `exit=0` 160/160、g02 `exit=0` 1586/1586、g03/g04/g06/g07/g08/g09/g10 全 `exit=0`（g10 `22/22`、g04 `3/3`、g09 `ANCHOR_EQUAL 035edfce7`）；**g05 `exit=1`，三条失败全是 hof-rs fixture 造成的既有红，与本任务无关**（§5.3） | `gates\task151-canonical\summary.txt`、`gates\task151\summary.txt`（plain 偏离一次） |

---

## 1. 结论

### 1.1 是否复现（分别）

* **游戏进程，不带调试器：未复现。** 这是第一轮（按任务书 §3 的原样步骤）的结果——两条 body 都正确回了
  `-32602`（见 §2.1）。**因此任务书 §2「analyzer 错误走不同阶段、捕获机制在游戏进程里安装方式不同」这条首要假设被证伪**：
  捕获机制在游戏进程里工作正常，`data.parse_error` 连 `messages[]` 与 `generated_line` 都齐全。
* **游戏进程，编辑器播放（真冒烟场景）：复现。** 端点是 `editor_play_scene` 起的子进程，它的命令行**必然**带
  `--remote-debug tcp://127.0.0.1:6007 --editor-pid <editor>`（`editor/run/editor_run.cpp:64-71`），于是
  `EngineDebugger::is_active()` 在该进程里为真。**这一条命令行是唯一的差别**，本任务用自建对端把它单独隔出来做了对照（§2.3）。
* **编辑器进程：未复现。** 同一轮 9888 上两条 body 都回 `-32602`（历史 11–14 ms，复测 9–14 ms）。

### 1.2 根因（一句话）

`GDScript::reload()` 在失败路径上会调用 `GDScriptLanguage::debug_break_parse()`
（`modules/gdscript/gdscript.cpp:825/845/867`），而**只要进程里有活跃调试器**，它就会进
`EngineDebugger::debug()` → `RemoteDebugger::debug()`，后者在
`while (is_peer_connected())`（`core/debugger/remote_debugger.cpp:444`）里**阻塞主线程**直到编辑器恢复它或对端消失。
两个 executor 都跑在**主线程**、就在框架泵里，所以整条端点（以及游戏本身）一起停住。运行期错误路径
（`modules/gdscript/gdscript_vm.cpp:525/3989` → `debug_break()`）**形状完全相同**。

### 1.3 修了什么

`modules/mcp_server/tools/tool_helpers.h/.cpp` 新增 `MCPTools::GDScriptErrorBreakGuard`，在
`reload_gdscript_capturing`（编译窗口）与 `call_gdscript_capturing`（执行窗口）里各开一个作用域：
进入时把 `ScriptDebugger::ignore_error_breaks` 抬起，退出时**还原它读到的值**。无调试器时**零写入**
（编辑器、普通游戏、`--test` 进程逐字节不变）。**契约、描述、schema、错误码一律未动。**

### 1.4 是否全绿

* **canonical 门（新鲜 mono，`4.8.dev.mono.custom_build.035edfce7`）**：**9/10**，`g01..g04、g06..g10` 全部 `exit=0`。
  唯一红是 **g05 `exit=1`**，三条失败（`B0/B1/B2`）比的是 **hof-rs 侧的冻结 fixture**，该文件已被 hof-rs 自己重采
  （§5.3 有完整证据链）；**本任务没有触碰 g05 的任何一个输入**，也没有为了变绿去改那个冻结常量。
* **deviation 门（plain console，`4.8.dev.custom_build.97fc49df4`）**：同样 **9/10**，每个门的输出与 canonical 逐项一致
  （g01 160/160、g02 1586/1586、g09 `ANCHOR_EQUAL 97fc49df4`、g10 22/22）。
* **线上验收（修复后）**：plain 与 mono 变体各 **34/34**（§1.5）。

### 1.5 构建与测试命令的真实尾部与退出码

```
# 串行构建（引擎惯例 -j8 是同一份脚本的既有写法，全程没有并发 scons）
cmd> modules\mcp_server\scripts\build_local.cmd -Force          → build_local: exit code = 0
cmd> modules\mcp_server\scripts\mcp057_build_mono.cmd           → mcp057_build_mono: exit code = 0
      （mono 第一次失败：bin\godot.windows.editor.x86_64.mono.exe: 拒绝访问 / Access is denied
        —— 决策者随后释放了持锁进程，重跑即 exit code = 0；详见 §8）

# 红相位（只有测试、没有修复）
.\modules/mcp_server/tests/test_mcp_server.h(10340): error C2065: "GDScriptErrorBreakGuard": undeclared identifier
.\modules/mcp_server/tests/test_mcp_server.h(10340): error C2146: syntax error: missing ';' before identifier 'guard'
.\modules/mcp_server/tests/test_mcp_server.h(10340): error C3861: 'guard': identifier not found
scons: *** [bin\obj\tests\test_main.windows.editor.x86_64.obj] Error 2
EXIT_CODE=2

# canonical 门（真实尾部，逐门原样）
g01 exit=0 wall=13.3s cmd= bin\godot.windows.editor.x86_64.mono.console.exe --headless --test --test-case=[MCPServer]*
    | [doctest] test cases:  160 |  160 passed | 0 failed | 1429 skipped
    | [doctest] assertions: 6801 | 6801 passed | 0 failed |
    | [doctest] Status: SUCCESS!
g02 exit=0 wall=32.8s cmd= bin\godot.windows.editor.x86_64.mono.console.exe --headless --test
    | [doctest] test cases:   1586 |   1586 passed | 0 failed | 3 skipped
    | [doctest] assertions: 431114 | 431114 passed | 0 failed |
    | [doctest] Status: SUCCESS!
g03 exit=0  TOOL-GROUPS CHECK PASS      BYTES 5681  SHA256 b83d79d3e3d080ce460b61ca99a46a126d6a6c45eb3d51d7977a52a991b7fbc7
g04 exit=0  3/3 checks passed           editor 154 / game 73 / contract 177 / guard_user_port_9877 pid_before=-1 pid_after=-1
g05 exit=1  RESULT: FAIL (3 failing checks): B0 old contract sha256 frozen, B1 old contract tools == 174, B2 bidirectional diff empty
g06 exit=0  TAUTOLOGY CHECK PASS
g07 exit=0  PROBES: 10/10
g08 exit=0  RESULT: PASS (… none is UNCLASSIFIED)   UNCLASSIFIED = 0
g09 exit=0  ANCHOR_JUDGE VERDICT=ANCHOR_EQUAL … RESULT PASS
g10 exit=0  22/22 cases passed

# 单一用例（红相位单据的可执行证明：修复后它跑出 22 条断言）
cmd> "…console.exe" --headless --mcp-port=0 --test --test-case="*error breaks armed*" --success
[MCPServer] running_game_execute_gdscript does not run caller code with engine error breaks armed
[doctest] test cases:  1 |  1 passed | 0 failed | 1588 skipped
[doctest] assertions: 22 | 22 passed | 0 failed
[doctest] Status: SUCCESS!     DOCTEST_EXIT=0

# 线上验收（修复后，两个变体）
plain: CHECKS: 34/34 passed, 0 failed     （evidence-verify\checks.tsv）
mono : CHECKS: 34/34 passed, 0 failed     （evidence-verify-mono\checks.tsv）
```

---

## 2. 最小复现件

端口纪律：只用 **9888（编辑器）/ 9889（游戏）**，另加自建的调试器对端端口 **6011**（loopback，本脚本自己的监听）；
**9877 只观察、从不使用**，每次运行的开头与结尾各做一次监听者核对。scratch 工程在 `%TEMP%\mcp151\proj`。

### 2.1 第一轮：手起游戏进程（**未复现**，且证伪了首要假设）

```
cd F:\moonbit-hof-rs\godot-mcp\recovery\work\task151
powershell -NoProfile -ExecutionPolicy Bypass -File .\repro.ps1 -Phase all
  [PORT-GUARD before] 9877 LISTEN pid=108432 | 9888 free | 9889 free
  STARTED pid=108640  cmdline="…\godot.windows.editor.x86_64.console.exe" --headless --path C:\Users\wyl\AppData\Local\Temp\mcp151\proj --mcp-port=9889
  [MCP] role=game configured_port=9889 source=cmdline listen=true     ← 游戏侧确已监听
  game-health-before:      status_line=HTTP/1.1 200 OK  elapsed_ms=37
  game-call-1-parse-error:    status_line=HTTP/1.1 200 OK  elapsed_ms=16   → -32602 + data.parse_error
  game-call-2-analyzer-error: status_line=HTTP/1.1 200 OK  elapsed_ms=12   → -32602 + data.parse_error
  （12 次心跳 120 s：进程 alive=True、9889 一直在监听）
  [PORT-GUARD after] 9877 listen pids = 108432
```

原始响应（`evidence\game-call-2-analyzer-error.txt`，逐字）：

```
status_line=HTTP/1.1 200 OK
response_body={"error":{"code":-32602,"data":{"parse_error":{"generated_line":4,"in_caller_code":true,
"line":1,"message":"Parse Error: Cannot get return value of call to \"action_press()\" because it returns \"void\".",
"messages":["Parse Error: Cannot get return value of call to \"action_press()\" because it returns \"void\"."]},
"parse_error_column":null,"suggestion":"Parameter 'code' accepts a string (required); …"},
"message":"Parameter 'code' does not compile at line 1 of 'code': Parse Error: Cannot get return value of call to
\"action_press()\" because it returns \"void\"."},"id":2,"jsonrpc":"2.0"}
```

**结论**：裸游戏进程**没有缺陷**——analyzer 阶段与 parse 阶段**都被正确捕获**并回 `-32602`。

### 2.2 第二轮：编辑器播放的场景（**复现**，就是冒烟场景本身）

```
powershell -NoProfile -ExecutionPolicy Bypass -File .\repro_played.ps1
  [PORT-GUARD before] 9877 = 108432 | 9888 = (空) | 9889 = (空)
  editor 9888 is listening                   ← 工具列表 200（154 工具）
  editor-play-scene:  HTTP/1.1 200 OK  {"mcp_port":9889,"pid":118348,"mcp_port_source":"argument", …}
  GAME cmdline=F:\…\bin\godot.windows.editor.x86_64.exe --path C:/Users/wyl/AppData/Local/Temp/mcp151/proj \
        --remote-debug tcp://127.0.0.1:6007 --editor-pid 118496 --scene res://scenes/main.tscn "--mcp-port=9889" --headless
  GAME has --remote-debug: True
  game-tools-list-before:  HTTP/1.1 200 OK  7 ms          ← 触发前端点健康
  game-call-analyzer-error: status_line=<NONE> elapsed_ms=20016 bytes=0
      io_error=Exception calling "Read" … "Unable to read data from the transport connection:
                A connection attempt failed because the connected party did not properly respond
                after a period of time, or established connection failed because connected host has failed to respond."
  game-call-2-after-freeze: status_line=<NONE> elapsed_ms=20010 bytes=0      ← 第二条独立连接同样无状态行
  T+10s alive=True listen=yes listen_pids=118348
  T+20s alive=True listen=yes listen_pids=118348
  T+30s alive=True listen=yes listen_pids=118348
  T+40s alive=True listen=yes listen_pids=118348
  T+50s alive=True listen=yes listen_pids=118348
  T+60s alive=True listen=yes listen_pids=118348      ← 60 s 里「连接能建立、进程活着、监听还在、就是没有状态行」
  （随后停掉编辑器 = 同时拆掉调试器对端与 --editor-pid 的看守）
  game-call-after-editor-gone: status_line=<NONE> elapsed_ms=2049
      io_error=Exception calling "Wait" …"One or more errors occurred."     ← 连接直接被拒（没有监听者了）
  game alive after editor gone = False, 9889 listen = (空)
  [PORT-GUARD after] 9877 = 108432
```

时间线（`evidence-played\timeline.txt`）：触发在 `07:33:56.822` → 首次 20 s 无状态行；60 s 心跳
`07:34:25.282 … 07:35:57.846` 全部 `alive=True listen=yes`；末次观测 `07:35:57.846`，其后 `07:36:18.653`
进程已退出、监听已空。

**与 hof-rs 观测的对应**：本任务用的是裸 socket，所以没有 ureq 的 `10060` / `10061` **字符串**；
对应的**形状**是——`10060`（"Error encountered in the status line"）= **连接建立、请求已发出、状态行不来**，本处实测
`status_line=<NONE>` + 读超时；`10061`（连接被拒）= **监听者不存在**，本处实测为「连接直接失败」，只在
**子进程被拆除之后**出现（§3.4）。

### 2.3 第三轮：把 `--editor-pid` 混淆去掉（**根因判据**）

`repro_played.ps1` 的收尾控制不干净：`EditorRun::run()` 同时给了 `--editor-pid`，编辑器一消失，游戏**自己退出**
（实测 2 s 内），所以那次「释放对端」同时发生了两件事。`repro_peer.ps1` 把两者分开：游戏**手起**、
`--remote-debug` 指向本脚本自己的监听套接字、**不带 `--editor-pid`**，对端**持有 25 s 后关闭**。

```
powershell -NoProfile -ExecutionPolicy Bypass -File .\repro_peer.ps1
  cmdline="…console.exe" --headless --path C:\Users\wyl\AppData\Local\Temp\mcp151\proj \
          --remote-debug tcp://127.0.0.1:6011 --mcp-port=9889
  has --remote-debug = True ; has --editor-pid = False
  game-tools-list-before:    HTTP/1.1 200 OK  37 ms
  game-call-analyzer-error:  HTTP/1.1 200 OK  elapsed_ms=23580   ← 与对端持有时间（25 s）吻合
      body={"error":{"code":-32602,"data":{"parse_error":{"generated_line":4,"in_caller_code":true,"line":1,
            "message":"Parse Error: Cannot get return value of call to \"action_press()\" because it returns \"void\"."…}}}}
  after the answer: game alive = True ; 9889 listen = 21816
  game-tools-list-after:     HTTP/1.1 200 OK  5 ms
```

**这一条是根因判据**：**同一条 TCP 连接**在调试器对端关闭的那一刻被应答了。所以不是套接字坏了、不是进程死了，
而是**主线程在等调试器**；`elapsed_ms` 由对端的存活时间决定，而与 body 的内容无关。

---

## 3. 根因

### 3.1 实测链条（每一步都有文件:行或原始输出）

1. `editor_play_scene` 起的子进程命令行带 `--remote-debug tcp://127.0.0.1:6007`（实测原文见 §2.2）。
   **源头**：`editor/run/editor_run.cpp:64-68`（`const String debug_uri = EditorDebuggerNode::get_singleton()->get_server_uri(); if (debug_uri.size()) { args.push_back("--remote-debug"); … }`）
   与 `:70-71`（`--editor-pid`）。
2. 有调试器 ⇒ `EngineDebugger::is_active()` 为真
   （`core/debugger/engine_debugger.h:106`：`singleton != nullptr && script_debugger != nullptr`；
   `core/debugger/engine_debugger.cpp:136-149` 用 `tcp://` 建 `RemoteDebugger` + `ScriptDebugger`）。
3. `GDScript::reload()` 的三条失败路径各调一次 `GDScriptLanguage::debug_break_parse(...)`
   （`modules/gdscript/gdscript.cpp:825` 解析、`:845` analyzer、`:867` 编译器）。
4. `debug_break_parse` 只在有调试器且在主线程时才动手
   （`modules/gdscript/gdscript_editor.cpp:300-304`：`if (EngineDebugger::is_active() && Thread::get_caller_id() == Thread::get_main_id())` → `debug(this, false, true)`），
   随后进 `ScriptDebugger::debug` → `EngineDebugger::debug` → `RemoteDebugger::debug`
   （`core/debugger/remote_debugger.cpp:396`）。
5. `RemoteDebugger::debug` 只在「对端不在」或「忽略错误断点」时提前返回（`:411`、`:407-409`），否则
   **`while (is_peer_connected()) { flush_output(); _poll_messages(); if (_has_messages()) {…} else { delay_usec(10000); … } }`**
   （`:444`、`:626-632`）——**只要对端还在，它就一直在那里**。
6. 运行期错误走同一条路：`modules/gdscript/gdscript_vm.cpp:3988-3989`
   （`_err_print_error(..., ERR_HANDLER_SCRIPT)` + `debug_break(err_text, false)`），栈溢出 `:525` 同。
7. 两个 executor 都在主线程（`tools/running_game_script_execution.cpp` 的 handler 由框架泵调用），
   而 MCP 的 HTTP 应答也在同一个泵里写 —— 于是「连接能建立、请求已发出、状态行不来」（§2.2/§2.3）。

### 3.2 任务书 §4 的四条假设，逐条判

| # | 假设 | 判定 | 依据 |
|---|---|---|---|
| 1 | analyzer 错误与 parse 错误走不同路径，捕获只覆盖 parse | **证伪（实测）** | 裸游戏进程里 analyzer 错误同样回 `-32602` + `data.parse_error`（含 `messages[]`）；捕获钩子在 `reload()` 内部对三段都同样生效（§2.1） |
| 2 | 游戏进程与编辑器进程的差异在于错误钩子/打印钩子缺失 | **证伪（实测）**：差异是**调试器对端**，不是捕获机制 | 裸游戏进程（没有钩子差异，也没有调试器）正常；`editor_play_scene` 的孩子（有调试器）挂；把对端单独隔离后挂点跟着对端走（§2.3）。引擎 stderr 仍然打印 `SCRIPT ERROR: Parse Error: …` + `at: GDScript::reload` —— 说明诊断**产生过**，缺的是**应答** |
| 3 | 主线程死锁 | **确认（实测）** | 60 s 内 `GET /mcp` 无应答（帧泵停住）而进程活、监听在；释放对端后同一条连接立刻被应答（§2.2/§2.3） |
| 4 | 进程死亡 vs 单纯死锁 | **两者分开**：故障期是**死锁**；`10061` 是**下游** | 观测 60 s 内进程与监听都在（§2.2）；进程消失发生在**编辑器/对端被拆掉之后**，且 `--editor-pid` 让子进程自行退出（实测 2 s 内） |

### 3.3 「进程没死」这件事的直接证据

```
T+10s alive=True listen=yes listen_pids=118348
…
T+60s alive=True listen=yes listen_pids=118348
```
（`evidence-played\timeline.txt`；`alive` 由 `Get-Process` 判，`listen` 由 `Get-NetTCPConnection -State Listen` 判。）

### 3.4 一处必须更正的解读（决策者已确认）

hof-rs 把 730 s 之后的 `10061` 记成「**监听消失 / 进程死亡**」。**这个读法是错的**：按本任务的实测，故障期
**进程与监听都还在**，只是**主线程被调试器的等待卡住**，因此端点「能连、不应答」。`10061` **不是**故障本体，
而是**子进程最终被拆除之后的下游症状**——本任务复现了它的触发条件：`--editor-pid` 让子进程在编辑器消失后
~2 s 内自行退出，随后 9889 无监听、连接被拒（`game alive after editor gone = False, 9889 listen = (空)`）。
这同时解释了为什么 `GET /mcp`（与任何请求）在 60 s 内都不应答、而监听仍在：

* 「不应答」来自 **`RemoteDebugger::debug()` 的循环**（同一线程同时负责写响应）；
* 「监听仍在」是因为**监听套接字由别的代码持有**，它没有参与那个等待。

**未复现的部分（如实声明）**：我没有跑满 730 s 去重现冒烟运行里「首次 `10061` 比末次 `10060` 晚约 7 s」的那一段，
也没有取证到底是谁在那 730 s 里拆掉了子进程（harness、编辑器停播、还是别的）。我复现的是等价机制
（对端/`--editor-pid` 消失 ⇒ 监听消失），以及完整的前半段（无状态行 + 监听仍在 + 进程仍活）。

---

## 4. 修复

### 4.1 改动清单（`git diff --numstat 15bbf1f50e..035edfce7f`）

```
151   0   modules/mcp_server/tests/test_mcp_server.h          （c0f2dfba31：红相位测试）
 83   0   modules/mcp_server/tools/tool_helpers.h             （97fc49df4b：GDScriptErrorBreakGuard 的声明与引擎依据）
 54   6   modules/mcp_server/tools/tool_helpers.cpp           （97fc49df4b：实现 + 两处调用点）
 13   0   modules/mcp_server/tools/running_game_script_execution.cpp（97fc49df4b：契约注释新增一条）
 31   0   modules/mcp_server/docs/MCP-SERVER-HANDOVER.md      （035edfce7f：§3 (k) 边界登记）
```

### 4.2 为什么这么改

* **修在模块、不修在引擎**：「脚本出错就停进调试器」是编辑器对**用户代码**的契约。本模块编译的**不是**用户代码，
  而是 MCP 调用方送来的一段合成 body；模块对它的全部回答就是**从捕获到的诊断里构造的结构化拒绝**
  （`-32602` + `data.parse_error`，TASK-063/089；`-32000` + `data.script_error`，TASK-103）。
  一次调试器暂停是这些诊断**唯一**还能变成「完全没有回答」的途径，所以在**本模块运行调用方代码的那个窗口**里
  把引擎自己那面开关抬起来，退出时还原，是与既有捕获同一思路的最小补丁。
* **用的是引擎自己的开关，不是私有的**：`ScriptDebugger::ignore_error_breaks` 就是调试器协议里
  `set_ignore_error_breaks` 暴露的那个（`core/debugger/remote_debugger.cpp:740-742`），而且**两种调试器都在阻塞之前先读它**
  （`RemoteDebugger::debug()` `:407-409`；`LocalDebugger::debug()` `core/debugger/local_debugger.cpp:120-122`）。
* **两处窗口都覆盖**：编译窗口（`reload_gdscript_capturing`）与被调 body 的执行窗口（`call_gdscript_capturing`）。
  后者是必要的，因为运行期错误走 `debug_break()`（`gdscript_vm.cpp:3988-3989`），**形状完全一样**；
  否则 §5.3 的「运行期错误仍回 `-32000`」在播放的游戏里会变成「又一次挂死」，等于只修了一半。
* **还原读到的值**：不是固定写回 `false`——编辑器自己关掉的设置，不能被一次工具调用改写。
* **无调试器零写入**：`changed() == false`，编辑器进程/普通游戏/`--test` 进程的行为逐字节不变（有 doctest 钉）。

### 4.3 被改动的既有断言

**没有。** `git diff --numstat` 对 `test_mcp_server.h` 是 **151 增 / 0 删**；对全部改动是
**332 增 / 6 删**，其中 6 行删除全部是 `tool_helpers.cpp` 两处 capture 里被作用域包起来的**同一段语句的缩进与
`add_error_handler` / `callp` / `remove_error_handler` 三行**（原样保留，只是放进 `{}` 并加了一行 guard 构造）。
逐条对照：

| 位置 | 原 | 新 | 为什么语义等价 |
|---|---|---|---|
| `reload_gdscript_capturing` | `add_error_handler(&handler); report.error = p_script->reload(); remove_error_handler(&handler);` | 同一段外面套 `{ GDScriptErrorBreakGuard break_guard(EngineDebugger::get_script_debugger()); … }` | 三行一句未改；guard 只写调试器开关，且无调试器时零写入；`report` / `messages` / 行映射的构造都在作用域之外，一字未动 |
| `call_gdscript_capturing` | `add_error_handler(&handler); p_entry_point.callp(nullptr, 0, r_result, r_call_error); remove_error_handler(&handler);` | 同一段外面套同样的 `{}` | 同上；TASK-103 的 `-32000` / `data.script_error` 与 `note` 的构造完全没碰 |

### 4.4 规范 vs 实现

* **没有改 `DESIGN-DETAIL.md`**：该文档不描述 executor 的内部引擎依据（`grep execute_gdscript` 在
  `DESIGN-DETAIL.md` 里无命中），本模块关于 executor 的可观察契约写在 `tools/running_game_script_execution.cpp`
  的头部注释（implemented contract）与 `tools/tool_helpers.h` 的引擎依据注释里，两者**都已同步更新**；
  线上契约（`docs/tools_list.renamed.json` 的 name/description/inputSchema）**一字未改**（g04 逐字通过）。
* 另外在 `docs/MCP-SERVER-HANDOVER.md` §3 增 (k) 节，登记「保证 / 不保证 / 实测 / 为什么 doctest 只钉一半 / 门⑤ 三条红的出处」。

---

## 5. 门与回归

### 5.1 canonical（新鲜 mono 变体，命令与 `tools\run_gates.ps1` 逐字相同）

| # | 命令 | 真实结果 |
|---|---|---|
| g01 | `bin\godot.windows.editor.x86_64.mono.console.exe --headless --test --test-case=[MCPServer]*` | **exit=0** `160/160 passed`、`6801/6801 assertions`、`SUCCESS!`（13.3 s） |
| g02 | `bin\godot.windows.editor.x86_64.mono.console.exe --headless --test` | **exit=0** `1586/1586 passed / 3 skipped`、`431114/431114 assertions`、`SUCCESS!`（32.8 s） |
| g03 | `python modules\mcp_server\docs\scripts\check_tool_groups.py` | **exit=0** `TOOL-GROUPS CHECK PASS`，`BYTES 5681`，`SHA256 b83d79d3…` |
| g04 | `powershell … check_contract_subset.ps1` | **exit=0** `3/3 checks passed`；编辑器 **154** / 游戏 **73** / `contract=177`；逐字抽样 `name=True description=True inputSchema=True`；`guard_user_port_9877 pid_before=-1 pid_after=-1`（9877 本轮空闲） |
| g05 | `python modules\mcp_server\docs\scripts\check_rename_map.py` | **exit=1** `RESULT: FAIL (3 failing checks): B0 old contract sha256 frozen, B1 old contract tools == 174, B2 bidirectional diff empty`（**既有红，非本任务，见 §5.3**） |
| g06 | `python modules\mcp_server\scripts\check_tautologies.py` | **exit=0** `TAUTOLOGY CHECK PASS` |
| g07 | `python modules\mcp_server\scripts\check_exit_propagation.py --probes` | **exit=0** `PROBES: 10/10` |
| g08 | `python modules\mcp_server\scripts\check_hardcoded_counts.py` | **exit=0** `UNCLASSIFIED = 0`（扫描 185 文件；新增代码没有引入未分类常数） |
| g09 | `powershell … check_engine_anchor.ps1 -VersionText 4.8.dev.mono.custom_build.035edfce7` | **exit=0** `VERDICT=ANCHOR_EQUAL`、`ANCHOR=035edfce7 ANCHOR_REPORTED=035edfce7 HEAD=035edfce7`、`DIFF_COUNT=0`、`RESULT PASS` |
| g10 | `powershell … accept_m1.ps1` | **exit=0** **`22/22 cases passed`**（47.0 s），含 `guard_user_port_9877` |

日志：`recovery\work\task151\gates\task151-canonical\g01..g10.{stdout,stderr}.txt` + `summary.txt`。
运行器：`recovery\work\task151\run_gates_canonical.ps1`（十道命令与主仓 `tools\run_gates.ps1` 相同，**无任何替换**）。

### 5.2 deviation 一次（plain console 变体）—— 保留并明确区分

在决策者释放 mono 二进制**之前**，`bin\godot.windows.editor.x86_64.mono.exe` 被 9877 上的编辑器进程
（PID 108432）**持有**，scons 重链接必然失败（`…mono.exe: 拒绝访问 / Access is denied`），因此当时无法产出新鲜 mono。
**我没有**用陈旧 mono 冒充（那会是假绿：陈旧 mono 里根本没有本任务的新用例），而是把 g01/g02/版本探针换成
plain console 跑了一遍作 `deviation`：

| # | deviation 结果（plain，`4.8.dev.custom_build.97fc49df4`） |
|---|---|
| g01 | **exit=0** `160/160`、`6801/6801`（用例数与 canonical 相同 ⇒ 新用例确实在里面） |
| g02 | **exit=0** `1586/1586 / 3 skipped`、`431107/431107` |
| g09 | **exit=0** `ANCHOR_EQUAL 97fc49df4` |
| g10 | **exit=0** `22/22` |
| 其余 | 与 canonical 逐项一致（g05 同样红，同因） |

日志：`recovery\work\task151\gates\task151\summary.txt`；运行器 `run_gates_task151.ps1`（头部写明替换与理由）。
`g02` 的断言数在两种变体下相差 7 条（431107 / 431114）**不是本任务造成的**，与 TASK-073 记录的「变体固有差异」同族
（mono 变体多出的断言来自 C# 相关用例）；**用例数两边都是 1586**。

### 5.3 g05 的三条红：出处已查明，**不在本任务**

```
$ python -c "…"      →  F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json  sha256=50c5fb4204ee5b957b017eb994e7f7bd73f9b299e6aa9471d5cf11683e067da0  tools=177
$ check_rename_map.py 的冻结常量 →  OLD_CONTRACT_SHA256 = 8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54（174 工具）
$ git -C F:\moonbit-hof-rs log --oneline -1 -- tests/fixtures/mcp/tools_list.json
  db2eed7 tools: migrate to the 177-tool four-channel contract and rewrite the role scopes (DR-42)
$ git -C …\godot diff --name-only 15bbf1f50e..HEAD -- modules/mcp_server/docs/tool-rename-map.json docs/tools_list.renamed.json
  （空）
```

即：**hof-rs 侧自己把那个冻结 fixture 从 174 工具 / `8f8051c4…` 换成了 177 工具 / `50c5fb42…`**，
而 g05 的 `B0/B1/B2` 正是拿它当基准；g05 的**其余全部检查（A1/A2/B3/C…/F8/F9/G1..G6）都是 PASS**，
契约侧的推导（`171 + 6 = 177`、唯一性、去合并对、`_meta` 一致）也全 PASS。
**本任务对 g05 的任何输入零改动**（上面 `git diff` 为空），所以这三条红**在 TASK-151 之前就存在**。

**我没有"修"它，这是有意的**：把 `OLD_CONTRACT_SHA256` 与新计数改成新 fixture 等于**重定这条门线的基线**
（那正是「为了让门变绿而放宽门」）；把 fixture 改回去则落在**明确禁止改动的 hof-rs 侧**。
因此按任务书 §5.4「任何一条变红都必须先解决或**明确上报**」，此处**上报**，并把判断留给决策者。
（该判断与出处也写进了 `MCP-SERVER-HANDOVER.md` §3 (k)，以免后来者顺手"修"绿。）

### 5.4 二进制身份（"新鲜"可核对）

```
BINARY bin\godot.windows.editor.x86_64.mono.console.exe bytes=300544      sha256=bf47c8f0af17e738a18db2f6fa79e62efa89bcf9ab34bcea9c83ff2001c8bfb7 mtime=2026-09-29 08:09:16 version=4.8.dev.mono.custom_build.035edfce7
BINARY bin\godot.windows.editor.x86_64.mono.exe         bytes=194216960   sha256=c4fb99826ccf0bad05acb3a1bbf100d0ef394f3907568116281bcd7b03e06c75 mtime=2026-09-29 08:09:15 version=4.8.dev.mono.custom_build.035edfce7
BINARY bin\godot.windows.editor.x86_64.console.exe      bytes=300544      sha256=3feeb6958a5ac8f5f8ea53319e1d6ec12385eccadc335ef42a23736c37b9359e mtime=2026-09-29 07:55:58 version=4.8.dev.custom_build.97fc49df4
BINARY bin\godot.windows.editor.x86_64.exe              bytes=193631232   sha256=15cbdeca6eae49f8dfc9853e6d1d336a3145767de6eb75725b0e053d59e046c1 mtime=2026-09-29 07:55:57 version=4.8.dev.custom_build.97fc49df4
```

两个变体都带着本任务的修复：mono 报 `035edfce7` = 当前 HEAD；plain 报 `97fc49df4`，
`git diff 97fc49df4..HEAD` 只含 `MCP-SERVER-HANDOVER.md`（非编译输入），故 g09 判 PASS（canonical 那次是 `ANCHOR_EQUAL`）。

### 5.5 线上验收（修复后，两个变体都跑了）

* **plain**：`34/34`（`evidence-verify\checks.tsv`，运行器 `verify_fixed.ps1`）
* **mono**：`34/34`（`evidence-verify-mono\checks.tsv`，`-EnginePath …mono.console.exe`，引擎自报
  `4.8.dev.mono.custom_build.035edfce7`）

两个场景各自的结果：

| 场景 | 编译不过（analyzer） | 编译不过（parse） | 运行期错误 | 成功 | 端点存活 | 进程存活 |
|---|---|---|---|---|---|---|
| **A** 手起游戏 + 自建 `--remote-debug` 对端（**不带** `--editor-pid`） | `-32602` + `data.parse_error`，**13 ms**（mono 25 ms） | `-32602`，18 ms（mono 17 ms） | `-32000` + `data.script_error`，12 ms（mono 12 ms） | `ok`，3 ms | `tools/list` 5 ms 后仍 200，`GET /mcp` 回 `frame_count` | 监听 pid 113108（mono 91984）仍活 |
| **B** `editor_play_scene` 播放（= 冒烟场景，`--remote-debug tcp://127.0.0.1:6007 --editor-pid 90292`；mono 那次是 `…mono.exe … --editor-pid 9964`） | `-32602` + `data.parse_error`，**3 ms**（mono 16 ms） | `-32602`，3 ms（mono 4 ms） | `-32000` + `data.script_error`，4 ms（mono 3 ms） | `ok`，2 ms | `tools/list` 5 ms 后仍 200 | pid 118748（mono 117936）仍活、9889 仍在监听 |
| **C** 编辑器对照（`editor_execute_gdscript`，9888） | `-32602`，9 ms（mono 25 ms） | `-32602`，14 ms（mono 15 ms） | 形状**如实记录、不作断言**（见 §7） | `ok`，5 ms | `tools/list` 6 ms 后仍 200 | — |

（括号内为 mono 变体同项实测；两个变体的 `checks.tsv` 都是 34 行全 `True`。mono 那次 A 场景比第一次多 12 ms 属正常抖动，
关键判据是 **`< 1000 ms` 与"必须有状态行"**，而修复前是 **20 s 无状态行**。）

对照（修复前，同一份脚本）：场景 B 的 analyzer body **20 s 内无状态行**、`GET /mcp` 60 s 无应答；
场景 A（对端释放前）**23.58 s** 才回同一条 body。

---

## 6. 禁区自查

| 项 | 结论 | 真实输出 |
|---|---|---|
| **不碰 9877** | **做到**。全程只用 9888/9889（+ 自建 6011），每次运行首尾核对监听者 | `PORT-GUARD before/after: 9877 listen pids = 108432`（修复前各轮）、`pid_before=108432 pid_after=108432`（g04 的 `guard_user_port_9877`）；canonical 那轮 9877 已空闲，g04 打印 `pid_before=-1 pid_after=-1`（无监听者），canonical 摘要 `PORT_9877_BEFORE=`/`AFTER=`（空） |
| **不 push** | **做到**：三个提交都在本地 | 引擎仓 `git log --oneline -3`：`035edfce7f` / `97fc49df4b` / `c0f2dfba31`；未执行任何 `git push`（本会话没有 push 类命令） |
| **不改 hof-rs 侧**（`src/**`、`tests/**`、`config/**`、`.spec/**`） | **做到**。主仓只新增 `godot-mcp\recovery\` 下的两个路径（本任务授权的落点），提交后工作树干净 | 提交前 `git status --porcelain` = `?? godot-mcp/recovery/reports/TASK-151-REPORT.md` + `?? godot-mcp/recovery/work/task151/`（**没有别的路径**）；提交后 `git status --porcelain` 为空；`tests/fixtures/mcp/tools_list.json` 保持 hof-rs 提交 `db2eed7` 的字节（sha `50c5fb42…`），**未触碰** |
| **不改 PRD** | **做到**：引擎仓改动只有 5 个文件，无 PRD | `git diff --numstat 15bbf1f50e..035edfce7f`（§4.1） |
| **串行构建、不抑制构建输出** | **做到**：三次 scons 严格串行；输出进日志文件（不用管道），脚本同时回显 | 构建日志 `%TEMP%\mcp_server_build_local.log`、`%TEMP%\mcp057\mono_build.log`；本报告 §1.5 给出 `EXIT_CODE=` 原文 |
| **不删/放宽既有测试** | **做到** | `test_mcp_server.h` 的 numstat = **151 增 / 0 删**；`git diff` 无 `^-` 行 |
| **收尾端口** | **9888/9889/6011 均已释放；9877 由决策者清空、我没有占用** | 各轮脚本收尾都打印 `STOPPED`（只停自己起的 pid）+ `PORT-GUARD after`；canonical 门摘要 `PORTS_9888_9889_AFTER=/`（两者皆空）、`PORT_9877_AFTER=`（空）；报告写完后的最终核对见 §7.4 |

---

## 7. 遗留风险与未验证项

### 7.1 **"真游戏里不冻结"这半边只由线上证据支持，不经单测覆盖**（决策者已确认的分工）

* **doctest 只钉模块自身的决策**：`[MCPServer] running_game_execute_gdscript does not run caller code with engine
  error breaks armed`（22 条断言，`--test-case="*error breaks armed*" --success` 可复现）钉三件事——
  有调试器时开关被抬起并**还原读到的值**；**无调试器时零写入**（`changed()==false`）；游戏路径
  （`is_editor=false` / `p_tool_script=false`）编译不过仍回 `-32602` + `data.parse_error` 且其后仍可用。
* **该机制无法在 doctest 内驻留，这是实测结论，不是设计偏好**：`RemoteDebugger::debug()` 的空闲分支要求
  `DisplayServer::get_singleton()->force_process_and_drop_events()`
  （`core/debugger/remote_debugger.cpp:626-632`），而 `Main::test_setup()`（`main/main.cpp:688-835`）
  **不创建任何显示服务器**。实测：一个**挂上真 `--remote-debug` 对端、再让 body 失败**的用例
  `FATAL ERROR: test case CRASHED: SIGSEGV`（`logs\red2-marker.stdout.txt`），崩点在进入该循环之后
  （用例已打印到「线程已启动」、尚未拿到回答）。
* 因此**"真游戏进程里不冻结"由 `verify_fixed.ps1` 的 34 项线上检查量出**（§5.5），**不得**被读成"已由单测覆盖"。

### 7.2 修复的语义边界（已写进 `MCP-SERVER-HANDOVER.md` §3 (k)）

* 只覆盖**本模块自己的窗口**：同一进程里**游戏自身脚本**的编译/运行期错误仍然照编辑器规则停住调试器。
* **救不回**已经进入等待的进程（开关在等待开始时读）。
* 执行窗口也覆盖（`call_gdscript_capturing`）是一个**有意的语义决定**：调用方 body 自己触发的引擎错误从此
  以 `-32000` + `data.script_error` 结构化地报出来，而不再暂停编辑器。若决策者认为"调用方触发的错误也应停调试器"，
  这是需要回退的一点（回退只需删掉 `call_gdscript_capturing` 里的那一个作用域，doctest 与线上脚本都要相应调整）。
* 不保证其他进程配置：**release 模板**（无 `DEBUG_ENABLED`）里 `debug_break_parse` 的调用点本身不编译，
  本修复在那里是空操作（与 TASK-103 记录的边界同族）。

### 7.3 未验证 / 未做

1. **没有跑满 730 s 复现冒烟运行的后半段**（`10060`→`10061` 的 7 s 间隔），也没有取证是谁拆掉了子进程；
   我复现的是等价机制 + `--editor-pid` 自退出的实测（§3.4）。
2. **没有分析 Windows 崩溃转储/事件日志**：本缺陷是**阻塞**而不是崩溃（真崩溃只出现在 **doctest 里那个不可行的用例**，
   已定位到 `remote_debugger.cpp:630` 的空 `DisplayServer`，与产品路径无关）。
3. **`editor_execute_gdscript` 的运行期错误形状只是记录、没有断言**：它回 `ok` + `{"result":null,"result_type":"Nil"}`
   （**没有** `note`）。`tools/editor_script_write.cpp` 里没有 `call_gdscript_capturing` —— 也就是
   **TASK-103 的运行期结构化解拒绝只覆盖游戏 executor**，编辑侧是**既有边界**、本任务**没有动**（契约/门都没要求）。
   我在脚本里把这一形状**打印出来但不判为通过**，以免把既有缺陷当成正确行为固定下来。
4. **g02 的断言数在 mono/plain 相差 7（431114 / 431107）**未逐一归因（同用例数 1586）；与 TASK-073 记录的变体固有差异同族。
5. **本任务的 doctest 不覆盖并发**：窗口是同步的、主线程的，与 TASK-103 捕获窗口同一假设；若将来 executor 变成
   可重入/多线程，`ignore_error_breaks` 的保存-还原需要重新论证（当前无并发调用者）。
6. **`check_hardcoded_counts.py` 的既有 2 行 `UNCLASSIFIED` 债务**（如 TASK-073 §8.1.7 所记）本轮为 0，未受影响。

### 7.4 最终端口/进程核对（报告落盘时所测）

```
9877 free   9888 free   9889 free   6011 free
Get-CimInstance Win32_Process -Filter "Name LIKE 'godot%'"  →  (无)
```

（canonical 之后 9877 一直是空闲的；本任务**从未**启动占用 9877 的进程——见 §6 的逐轮 `PORT-GUARD` 记录。
mono 那次线上验收的出现/收尾分别是 `9877 = (空)` / `PORT-GUARD after: 9877 = (空)`。）

---

## 8. 诚实披露（返工、猜错、绕过的尝试）

1. **任务书 §2 的首要假设是错的（已实测证伪）**：我按它出发，第一轮手起游戏进程跑两条 body —— 都正常回 `-32602`。
   真正的差别是 `--remote-debug`（`editor_play_scene` 必带，手起不带）。这一步花了两次运行，但它把
   "捕获机制"整条岔路**用实测关掉**了，后面的定位才收敛到调试器。
2. **第一版 doctest 用真 `RemoteDebugger` 对端 + 释放线程 —— 崩了。** 我把它当"红"接受了一次，
   但崩溃点不是缺陷本体；于是加了一个临时 `TASK151PROBE` 用例 + `print_line` 标记重建定位，
   测出崩点是 `RemoteDebugger::debug()` 空闲分支的空 `DisplayServer`（`remote_debugger.cpp:630`），
   随即**推翻自己的测试设计**，改成"模块自身的决定由 doctest 钉 + 真实冻结由线上量"的分工。
   代价：3 次额外构建、1 次回滚。**没有**把这次 SIGSEGV 说成"红相位"。
3. **红相位是编译错误，不是断言失败。** 只有测试、没有修复时 `error C2065: "GDScriptErrorBreakGuard":
   undeclared identifier`（§1.5 原文）。我不把它说成"行为红"；**真正的行为红**是线上那一份：
   修复前播放的游戏 20 s 无状态行、`GET /mcp` 60 s 无应答（§2.2）。两半都如实写在这里。
4. **`repro_played.ps1` 的收尾控制一开始不干净**：我停掉编辑器后游戏**自己退出了**（`--editor-pid`），
   于是"释放对端 ⇒ 应该立刻被应答"这条判据被污染。我**没有**拿那次观测下结论，而是另写
   `repro_peer.ps1`（手起游戏、自建对端、**不带** `--editor-pid`）重做，才拿到 23.58 s 的关键判据。
5. **脚本自身的 4 个 bug（都已修，且都不影响结论的原始证据）**：
   `$Log` 变量名与 `$script:Log` 撞名（PowerShell 作用域）、`ToolKey` 的 `-f` 格式化被 JSON 花括号吃掉、
   心跳请求漏传 `-Json`（第一轮 12 次心跳其实发的是空 body，服务器回 `400 -32700`；这不影响"端点活着"的结论，
   但 §2.2 用的是**带正确心跳**的第二轮）、成功断言没考虑工具载荷在 `content[0].text` 里被转义
   （`\"result\":42`），以及最初把编辑侧运行期错误也断言成 `-32000`（那是我读错既有边界，已改成只记录）。
6. **mono 变体第一次构建失败**：`bin\godot.windows.editor.x86_64.mono.exe: 拒绝访问`——被 9877 上决策者的编辑器
   （PID 108432）持有。我**没有**绕过（不改名/不替换/不用陈旧二进制冒充），改用 plain 变体跑 deviation 并
   把偏离写进门摘要；决策者释放该文件后，我**重新构建 mono 并跑了 canonical 全十道门**（`exit code = 0`），
   两者结果都在 §5 并列保留，且给出了四个二进制的 sha256 + mtime（§5.4）。
7. **g05 我没有"顺手修绿"**：三条红是 hof-rs fixture 被重采造成的（§5.3），改成新常量=重定基线，改回 fixture=闯禁改区；
   我选择**上报**并写进模块文档，而不是让门变绿。
8. **`editor_play_scene` 起的子进程在编辑器消失后 ~2 s 自退**这件事，是我在做对照时才发现的；
   它同时解释了 `10061` 为什么"晚 7 s 才出现"（§3.4），也解释了我上一版控制的漏洞（第 4 条）。
9. **没有使用任何别的引擎/工具进程去探测 9877**；收尾时它由决策者清空，我全程只观察。

---

## 9. 复现清单（从零到本报告的最小步骤）

```
# 1) 红相位（会失败）
cd F:\moonbit-hof-rs\godot-mcp\godot
modules\mcp_server\scripts\build_local.cmd -Force          # → exit 2, error C2065 GDScriptErrorBreakGuard
# 2) 修复后（绿）
modules\mcp_server\scripts\build_local.cmd -Force          # → exit code = 0
modules\mcp_server\scripts\mcp057_build_mono.cmd           # → exit code = 0（需要 mono.exe 未被占用）
# 3) 十道门
cd F:\moonbit-hof-rs\godot-mcp\recovery\work\task151
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_gates_canonical.ps1
# 4) 线上验收（两个变体）
powershell -NoProfile -ExecutionPolicy Bypass -File .\verify_fixed.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\verify_fixed.ps1 `
    -EnginePath F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe `
    -EvidenceDir evidence-verify-mono
# 5) 修复前的对照（行为红）
powershell -NoProfile -ExecutionPolicy Bypass -File .\repro.ps1 -Phase all      # 裸游戏：不复现
powershell -NoProfile -ExecutionPolicy Bypass -File .\repro_played.ps1          # 播放的游戏：复现（20 s 无状态行）
powershell -NoProfile -ExecutionPolicy Bypass -File .\repro_peer.ps1            # 根因判据（同连接 23.58 s 后被应答）
```
