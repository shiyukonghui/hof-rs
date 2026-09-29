# TASK-151-ACCEPTANCE — TASK-151（引擎侧调试器冻结修复）独立验收

> 验收者：**全新独立子代理**（无实现者/调度者上下文，不继承任何结论）。
> 权威任务书：`godot-mcp/recovery/tasks/TASK-151-ACCEPT.md`。
> 被测引擎仓：`F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`，HEAD **`035edfce7f`**，基线 `15bbf1f50e`）。
> 本报告里**每一条证据都是验收者自己跑出来的**；凡引自他处的证据都显式标注为「他证/未独立复核」。

---

## 1. 结构化结论

```json
{
  "verdict": "pass",
  "criteria": [
    {
      "id": "FIX.load_bearing",
      "pass": true,
      "evidence": "受控实验（本验收者自己做的唯一改动）：tool_helpers.cpp 两处 `GDScriptErrorBreakGuard break_guard(EngineDebugger::get_script_debugger());` → `break_guard(nullptr)`（2 处，git diff --numstat = 2 ins / 2 del），串行重建 mono（modules\\mcp_server\\scripts\\mcp057_build_mono.cmd，EXIT_CODE=0，产物 sha256=9bb511f7…console / 0678ce27….mono，mtime 08:26:46/45）→ verify_fixed.ps1 判据 **18/34 通过、16 条全红**（CHECKS: 18/34 passed, 16 failed，OUTER_EXIT=1）：scenario A(game) 8 条红、scenario B(played, editor_play_scene 的真实场景) 8 条红，每一条都是 `status_line=<NONE>` + 15–20 s 读超时，而 `scenarioA_listener_still_present` / `scenarioA_engine_process_alive_at_end` / `scenarioB_game_process_alive_at_end` / `scenarioB_game_listener_still_present` 与 **editor 对照 9 条全绿**（判据文件 `recovery/work/task151-accept/wire-guard-off.console.txt`，逐条原始证据 `recovery/work/task151/evidence-acc-guard-off/`）。恢复源码（sha 8dd73421… = 备份 = 原始）重建后 **34/34 CHECKS: 34/34 passed, 0 failed, OUTER_EXIT=0**（`wire-restored-mono.console.txt` + `evidence-acc-restored-mono/`）。⇒ 移走守卫判据**转红**、放回**转绿**，修复承载且是承重件。",
      "files": "godot-mcp/godot/modules/mcp_server/tools/tool_helpers.cpp:2910, :3046"
    },
    {
      "id": "ROOT_CAUSE",
      "pass": true,
      "evidence": "①`editor/run/editor_run.cpp:64-68` 读源确认：`const String debug_uri = EditorDebuggerNode::get_singleton()->get_server_uri(); if (debug_uri.size()) { args.push_back(\"--remote-debug\"); args.push_back(debug_uri); }`，`:70-71` `args.push_back(\"--editor-pid\")` 无条件追加；实测两次 `editor_play_scene` 的子进程命令行逐字含 `--remote-debug tcp://127.0.0.1:6007 --editor-pid <editor>`（`evidence-acc-baseline-mono/scenarioB-cmdline.txt` 与 `timeline.txt` 08:24:29.394）。②`core/debugger/engine_debugger.h:106` `is_active() = singleton != nullptr && script_debugger != nullptr`；`modules/gdscript/gdscript.cpp:823-826`（parse）、`843-846`（analyzer）、`862-868`（compiler）三条失败路径都在 `EngineDebugger::is_active()` 下调 `debug_break_parse`；`modules/gdscript/gdscript_editor.cpp:297-312` 只在 `is_active() && Thread::get_caller_id() == Thread::get_main_id()` 时调 `debug(this,false,true)`；`core/debugger/remote_debugger.cpp:396-418` 先读 `is_ignoring_error_breaks()`（`:407-409`）再进入 `while (is_peer_connected())`（`:444`），空闲分支 `OS::delay_usec(10000)` + `DisplayServer::get_singleton()->force_process_and_drop_events()`（`:626-632`）。③主线程=泵帧线程：`modules/mcp_server/mcp_server.cpp:242` `set_process(true)`，`:174-175` `NOTIFICATION_PROCESS → pump_frame`，`:276-281` 注释与代码「socket polling, parsing, tool execution, advancing the deferred tasks and writing the responses back — all on the main thread, once per frame」。**独立行为测量**：守卫停用后同一条编辑器播放的游戏连接 15 s 无状态行，而进程与 9889 监听全程存活（`scenarioB_game_process_alive_at_end` PASS / `scenarioB_game_listener_still_present` PASS），同轮 editor 端点 11–32 ms 正常——与「主线程被停、写入响应的同一线程被占」一致。**未做**：我没有抓栈（无 procdump/调试器）去直接证明「线程正停在 remote_debugger.cpp:444」；此处是「源码 + 你自己的行为测量」支持，不是栈证据。",
      "files": "godot-mcp/godot/editor/run/editor_run.cpp:64-71, core/debugger/engine_debugger.h:106, modules/gdscript/gdscript.cpp:823-826/843-846/862-868, modules/gdscript/gdscript_editor.cpp:297-312, core/debugger/remote_debugger.cpp:396-418/444/626-632, modules/mcp_server/mcp_server.cpp:174-175/242/276-281"
    },
    {
      "id": "WIRE.34",
      "pass": true,
      "evidence": "两次独立执行 `verify_fixed.ps1`（实现者的脚本，验收者自己跑）在**新鲜 mono** 上：`-EnginePath …mono.console.exe`，`engine: 4.8.dev.mono.custom_build.035edfce7`（脚本自身 `--version` 行）。第一次（复原后未重建的既有新鲜 mono，sha256=bf47c8f0…）：**34/34，exit 0**（`wire-baseline-mono.console.txt`）。第二次（我恢复源码后自己重建的 mono，sha256=8746a34a…）：**34/34，exit 0**（`wire-restored-mono.console.txt`）。逐项：被玩的游戏里 analyzer 错误 `str(Input.action_press(\"move_right\"))` ⇒ `HTTP/1.1 200` + `\"code\":-32602` + `data.parse_error`（16 ms）、parse 错误 ⇒ `-32602` + `data.parse_error`（4 ms）、运行期错误 `box[\"m\"].NoSuchMethodAtAll()` ⇒ `\"code\":-32000` + `data.script_error`（4 ms）、成功 `return 40 + 2` ⇒ `\"result\":42`（2 ms）、`tools/list` 前后各 200（5 ms）、`GET /mcp` 200 且 body 含 `frame_count`（`{\"frame_count\":186,...}`）、`scenarioB_game_process_alive_at_end` PASS、`scenarioB_game_listener_still_present` PASS；scenario A（自建 6011 对端、无 `--editor-pid`）同项 25/15/13/3 ms；编辑器对照 9888 两条编译不过也都 `-32602`（20/14 ms）。**二进制身份自己核对**：`bin\\godot.windows.editor.x86_64.mono.exe` sha256=`c4fb99826ccf0bad05acb3a1bbf100d0ef394f3907568116281bcd7b03e06c75` bytes=194216960 mtime=2026-09-29 08:09:15 `--version`=4.8.dev.mono.custom_build.035edfce7；`mono.console.exe` sha256=`bf47c8f0af17e738a18db2f6fa79e62efa89bcf9ab34bcea9c83ff2001c8bfb7` bytes=300544 **mtime=08:09:16（报告 §5.4 写的是 08:09:15，差 1 秒，属记账瑕疵）** `--version`=4.8.dev.mono.custom_build.035edfce7。",
      "files": "recovery/work/task151-accept/wire-baseline-mono.console.txt, recovery/work/task151-accept/wire-restored-mono.console.txt, recovery/work/task151/evidence-acc-baseline-mono/, recovery/work/task151/evidence-acc-restored-mono/"
    },
    {
      "id": "GATES",
      "pass": true,
      "evidence": "验收者自己运行 `recovery/work/task151/run_gates_canonical.ps1 -Tag acc-mono -OutRoot …\\task151-accept\\gates`（该脚本是主仓 `tools/run_gates.ps1` 命令集的逐字复制，验收者读源核对过第 47-58 行的十条命令）在**我自己重建的 mono**（`--version`=4.8.dev.mono.custom_build.035edfce7，调用时 sha256=8746a34a…）上跑**全部十道**：g01 exit=0 `160/160 passed | 6801/6801 assertions | SUCCESS!`（13.7 s）；g02 exit=0 `1586/1586 passed | 3 skipped | 431114/431114 assertions | SUCCESS!`（33.3 s）；g03 exit=0 `TOOL-GROUPS CHECK PASS  BYTES 5681  SHA256 b83d79d3e3d080ce460b61ca99a46a126d6a6c45eb3d51d7977a52a991b7fbc7`；g04 exit=0 `3/3 checks passed`，逐字抽样 `name=True description=True inputSchema=True`（editor 154 / game 73 工具，contract=177），`guard_user_port_9877 pid_before=-1 pid_after=-1`；**g05 exit=1（唯一红，见 G05.attribution）**；g06 exit=0 `TAUTOLOGY CHECK PASS`；g07 exit=0 `PROBES: 10/10`；g08 exit=0 `UNCLASSIFIED = 0`；g09 exit=0 `ANCHOR_JUDGE VERDICT=ANCHOR_EQUAL  ANCHOR=035edfce7 ANCHOR_REPORTED=035edfce7 HEAD=035edfce7  DIFF_COUNT=0  RESULT PASS`；g10 exit=0 `22/22 cases passed`（46.4 s，含 `guard_user_port_9877` PASS）。**plain-console deviation 的并列问题**：本验收者**没有**重跑 plain 变体（理由见 §5.1：会把 HEAD 的修复编译进 `4.8.dev.custom_build.97fc49df4` 版本串，破坏 g09 锚点语义，且 plain mono 变体切换会改动引擎 bin 产物）；我复述的 plain 结果只能来自实现者日志（`gates\\task151\\summary.txt`，`4.8.dev.custom_build.97fc49df4`，g01 160/160、g02 1586/1586、g09 `ANCHOR_EQUAL 97fc49df4`）——**这是他证，不是我独立复核**；任务书 §2.4 要求两个变体「并列且标清」，本报告在 §5.1 里明确把二者分开列出并标注来源。",
      "files": "recovery/work/task151-accept/gates/acc-mono/summary.txt, g01..g10.{stdout,stderr}.txt, recovery/work/task151-accept/gates-acc-mono.console.txt"
    },
    {
      "id": "G05.attribution",
      "pass": true,
      "evidence": "三条红**确与 TASK-151 无关**，我自己复现并核对了归因链的三个事实：①脚本内常量与路径逐字核对：`modules/mcp_server/docs/scripts/check_rename_map.py:77` `DEFAULT_OLD_CONTRACT = r\"F:\\moonbit-hof-rs\\tests\\fixtures\\mcp\\tools_list.json\"`、`:79` `OLD_CONTRACT_SHA256 = \"8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54\"`、`:160` `check(\"B0 …\", old_sha == OLD_CONTRACT_SHA256, old_sha)`、`:166` `check(\"B1 …\", len(old_names) == 174, …)`、`:167-168` B2 双向集合差；实测 hof-rs 侧该文件 sha256=`50c5fb4204ee5b957b017eb994e7f7bd73f9b299e6aa9471d5cf11683e067da0`、`len(tools)=177`（`Get-FileHash` + `python -c json`），`git log --oneline -1 -- tests/fixtures/mcp/tools_list.json` = `db2eed7`。②该文件**不在引擎仓内**（`F:\\moonbit-hof-rs\\tests\\…`），因此 `git -C godot-mcp/godot diff 15bbf1f50e..HEAD` 无从触及它；同时 g05 的**全部引擎侧输入**零 diff：`git -C godot diff --name-only 15bbf1f50e..HEAD -- modules/mcp_server/docs/tool-rename-map.json modules/mcp_server/docs/tools_list.renamed.json modules/mcp_server/docs/scripts/check_rename_map.py` 输出为空。③自己跑 `python modules\\mcp_server\\docs\\scripts\\check_rename_map.py`（exit=1）：**恰好三条红** `[FAIL] B0 old contract sha256 frozen / B1 old contract tools == 174 (len=177) / B2 bidirectional diff empty (contract-only=[177 条新名] map-only=[174 条旧名])`，**其余 25 条全 PASS**（A1/A2、B3、C1/C2、D1/D2/D3、E1..E4、F1..F9、G1..G6），`RESULT: FAIL (3 failing checks)`。⇒ 失败面正是「旧 174 条契约 vs 新 177 条契约」，即 D225 所述跨仓耦合（引擎门拿 hof-rs 的工作文件当基准），不涉本批任何改动。",
      "files": "godot-mcp/godot/modules/mcp_server/docs/scripts/check_rename_map.py:77/79/160/166/167, recovery/work/task151-accept/g05.stdout.txt, recovery/work/task151-accept/gates/acc-mono/g05.stdout.txt"
    },
    {
      "id": "DOCTEST_SPLIT",
      "pass": true,
      "evidence": "报告 §7.1 的声明**如实**。读码核对：`test_mcp_server.h:10325-10409` 的用例 `[MCPServer] running_game_execute_gdscript does not run caller code with engine error breaks armed` 只钉三件事——(1) 用**自己 new 的 `ScriptDebugger owned`**（`:10337`）验证抬起与「还原读到的值」（`:10348-10354`），(2) **无调试器零写入** `CHECK(EngineDebugger::get_script_debugger() == nullptr)` + `CHECK_FALSE(guard.changed())`（`:10359-10361`），(3) game 路径 `is_editor=false`/`p_tool_script=false` 下编译不过仍 `-32602`+`data.parse_error` 且其后仍可用（`:10364-10408`）；用例头部注释 `:10320-10323` 明确写「引擎可见的那一半由 verify_fixed.ps1 在线上量」。实测：`--test-case=\"*error breaks armed*\" --success` ⇒ `1 passed | 0 failed | 1588 skipped`、`assertions: 22 | 22 passed | 0 failed`、`DOCTEST_EXIT=0`（我自己跑；且该用例的编译错误正是实现者 §1.5 的「红相位」，性质是**编译失败**不是断言失败，实现者已如实标注）。其理由是**实测**不是偏好：`:10294-10303` 指出 `RemoteDebugger::debug()` 空闲分支要 `DisplayServer::get_singleton()->force_process_and_drop_events()`（`remote_debugger.cpp:626-632`），而 `Main::test_setup()` 不建 display server ⇒ 我在源里核对到 `remote_debugger.cpp:626-632` 确为 `OS::delay_usec(10000); if (Thread::is_main_thread()) { DisplayServer::get_singleton()->force_process_and_drop_events(); }`（`:630` 对 `nullptr` 解引用会崩，与实现者记录一致）；**该 SIGSEGV 本身我没有独立复跑**（要重建一个带真调试器对端的 doctest，会再动一次引擎树），仅源码支持 + 实现者日志（`logs\\red2-marker.stdout.txt`）。",
      "files": "godot-mcp/godot/modules/mcp_server/tests/test_mcp_server.h:10270-10409, godot-mcp/godot/core/debugger/remote_debugger.cpp:626-632, recovery/work/task151/logs/red2-marker.stdout.txt（他证）"
    },
    {
      "id": "NO_WEAKENING",
      "pass": true,
      "evidence": "`git -C godot-mcp/godot diff --numstat 15bbf1f50e..035edfce7f` = `31/0 MCP-SERVER-HANDOVER.md`、`151/0 tests/test_mcp_server.h`、`13/0 tools/running_game_script_execution.cpp`、`54/6 tools/tool_helpers.cpp`、`83/0 tools/tool_helpers.h`（合计 332 增 / 6 删，与报告 §4.1 一致）。**测试文件 0 删除**：`git diff 15bbf1f50e..HEAD -- modules/mcp_server/tests/` numstat = `151 0`；对 test_mcp_server.h 全量 diff 里以 `-` 开头（排除 `---`）的行数 = **0**。**6 条删除全部在 tool_helpers.cpp 的既有捕获语句上**，逐字列出：`-add_error_handler(&handler);` `-report.error = p_script->reload();` `-remove_error_handler(&handler);` `-add_error_handler(&handler);` `-p_entry_point.callp(nullptr, 0, r_result, r_call_error);` `-remove_error_handler(&handler);` ⇒ 与报告 §4.3 的「原样保留、只是外包一层作用域」逐条吻合；对应新增行是同段三行 + `GDScriptErrorBreakGuard break_guard(…);`（本验收者实验中把它改成 `nullptr` 即为 2 ins/2 del）。另：契约侧**逐字未动**——`git diff 15bbf1f50e..HEAD --numstat` 不含 `tools_list.renamed.json`/`tool-rename-map.json`；g04 的逐字抽样 `name=True description=True inputSchema=True` 通过；g03 的 `BYTES 5681 / SHA256 b83d79d3…` 与实现者所报一致。",
      "files": "recovery/work/task151-accept/gates/acc-mono/g03.stdout.txt, g04.stdout.txt"
    },
    {
      "id": "GUARDS",
      "pass": true,
      "evidence": "**9877 未被本批占用**：验收者自己的三次 wire 运行 `timeline.txt` 都是 `PORT-GUARD before: 9877 =  | 9888 =  | 9889 =  ` 与 `after: 9877 = `（空 = 无监听者）；canonical 摘要 `PORT_9877_BEFORE=/PORT_9877_AFTER=`（空）且 g04 `guard_user_port_9877 pid_before=-1 pid_after=-1`；收尾实测 `9877:  | 9888:  | 9889:  | 6011: ` 全空、无任何 `godot*` 进程。**脚本从不绑定 9877**：`Select-String -Pattern 'mcp-port=9877|--mcp-port 9877'` 在 `modules\\mcp_server\\scripts\\**` 的唯一命中是 `mcp042_port_guard_probes.ps1:37/39/40/76/116`，这些是**对字符串解析器与 guard 库的单元探针**（喂一个命令行字符串/注册 guard 记录），不启动引擎。**未 push**：引擎仓 `git rev-list --count origin/feature/mcp-server-module-rebuild..HEAD = 3`（即 `c0f2dfba31`/`97fc49df4b`/`035edfce7f` 领先远端共 3 条，origin 仍 `15bbf1f50e`）；主仓 `origin/master = 14fd0c7 = HEAD`（本批的主仓提交已在 origin，是 D224/D225/记录提交，非引擎修复；本验收者未 push 任何东西）。**hof-rs 侧零改动**：`git log --oneline -5 -- src tests config .spec` 最新为 `c2822de`（D223 文档，早于本批），本批三条主仓提交 `8442fc3`/`9da47de`/`14fd0c7` 落点在 `recovery/**` 与 `DECISIONS.md`；`git status --porcelain` 仅 `?? godot-mcp/recovery/work/task151/` 与 `?? godot-mcp/recovery/work/task151-accept/`（均为 `recovery/**` 授权落点）。`PRD-mario.md` sha256 = `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`（与任务书要求逐字相同）。**不 stage / 不删测试**：本验收者只用了 `copy` 备份 + `IO.File.WriteAllText` 恢复 + `git status/diff/hash-object` 只读核对，从未 `git add`/`checkout`/`restore`。",
      "files": "recovery/work/task151/evidence-acc-*/timeline.txt, recovery/work/task151-accept/gates/acc-mono/summary.txt, recovery/work/task151-accept/gates/acc-mono/g04.stdout.txt"
    }
  ],
  "defects": [
    {
      "id": "DEF-1",
      "severity": "info",
      "what": "引擎构建**不是可复现的（bit-for-bit）**：同一份源码（blob 逐字节相同）在同一轮里重建三次，产物 sha256 各不相同——守卫停用版 `mono.console.exe=9bb511f7…`/`mono.exe=0678ce27…`；恢复后版 `8746a34a…`/`08483088…`；而 HEAD 上的原版是 `bf47c8f0…`/`c4fb9982…`。因此「用它自己的 sha256 复述二进制身份」只能证明**当时那个文件**是什么，不能证明它由哪份源码构建；能证明「新鲜且带修复」的只有 `--version`（=035edfce7）、mtime、以及我这次 `--test-case=\"*error breaks armed*\"` 重建后的 22/22。",
      "reproduction": "比对 `recovery/work/task151-accept/build-1-guard-off.console.txt` / `build-2-restored.console.txt` 里的 sha 与 `gates/acc-mono/summary.txt` 的 BINARY 行，再看 §3 的 blob 相等证明。"
    },
    {
      "id": "DEF-2",
      "severity": "info",
      "what": "报告 §5.4 的 mtime 记账差 1 秒：`bin\\godot.windows.editor.x86_64.mono.console.exe` 实际 mtime 是 `2026-09-29 08:09:16`，报告写 `08:09:15`（`mono.exe` 的 08:09:15 是对的）。不影响任何结论。",
      "reproduction": "`Get-ChildItem bin\\godot.windows.editor.x86_64.mono*.exe | % { $_.Name, $_.LastWriteTime }`"
    },
    {
      "id": "DEF-3",
      "severity": "info",
      "what": "报告 §3.4 / D225 把「`--editor-pid` 让子进程在编辑器消失后约 2 s 自行退出」写成机制。我在引擎源码里只找到 `main/main.cpp:218/1904-1906`（解析该参数）与 `:2274-2275`（`DisplayServer::get_singleton()->enable_for_stealing_focus(editor_pid)`），**没有任何向该 pid 轮询/等死的代码**；`--editor-pid` 因此更像「把子进程挂在编辑器的作业对象/焦点语义上」，而不是被显式监视。该 2 s 自退在实现者的 `evidence-played/timeline.txt`（07:35:57.846 进程在，07:36:18.653 已退出）里是**原始观测**，但我**没有**独立复跑「只拆编辑器、看游戏是否自退」的对照。结论方向不受影响（本批的 wire 判据不依赖它），但机制描述应降级为「未定」。",
      "reproduction": "`Select-String -Path main\\main.cpp,core\\**\\*.cpp -Pattern editor_pid` 只出上述 4 行；对照 `recovery/work/task151/evidence-played/timeline.txt` 末段。"
    },
    {
      "id": "DEF-4",
      "severity": "info",
      "what": "报告 §1.5/§4 把 §2.3 的 `repro_peer.ps1`（23.58 s 后同一连接被应答）当作**根因判据**。它是全套证据里最关键的判别性对照，但我**未独立复跑**（只读了 `evidence-peer/timeline.txt` 的原始日志与脚本）。我独立拿到的是同族的、更直接的一对：守卫停用 ⇒ 同一条连接 15 s 无状态行；守卫在 ⇒ 25 ms 应答。",
      "reproduction": "对照 §3 的实验一/实验二与 `recovery/work/task151/evidence-peer/timeline.txt:9-16`（他证）。"
    }
  ],
  "risks": [
    "**构建不可复现（DEF-1）** ⇒ 任何「用 sha256 指认二进制」的跨批次基线都不可靠；后续批次的证据应改用「`--version` + 本批用例数 + 只读探针」三件套，或把构建做成可复现（固定时间戳/路径）后再谈二进制哈希。",
    "**g05 是跨仓耦合门**（引擎门拿 hof-rs 的 `tests/fixtures/mcp/tools_list.json` 当基准）。它现在恒红且与引擎仓内的一切改动无关（我已证明），这正是「训练人忽略红色」的典型；D225 已决定另立 TASK-152 让 g05 自包含于引擎仓，**在该项关闭前，十道门的全绿是不可达的**——验收与门禁脚本都应显式把 g05 记为「已知基线红」而不是「偶发」。",
    "**doctest 只覆盖模块自己的决定**（守卫抬起/还原/无调试器零写入），「真游戏不冻结」永远只能由线上脚本量。这是一条**结构性的覆盖空洞**，不会因为后续补测消除（`Main::test_setup()` 无 DisplayServer）；任何「TASK-151 已被单测覆盖」的说法都是误读。",
    "**执行窗口守卫的语义决定**（`call_gdscript_capturing` 也被覆盖 ⇒ 调用方 body 自己触发的引擎错误不再暂停编辑器）已被 D225 明确**保留**。它不是本缺陷的最小充分条件（编译窗口那一个 scope 就足够让 §2.1 的判据转绿），取消它只需删一个作用域；但它同时被「运行期错误必须仍回 -32000」这条线需要着。若将来要回退，wire 脚本第 3 项与 doctest 都要同步改。",
    "**`editor_execute_gdscript` 的运行期错误无结构化拒绝**（我读源确认 `tools/editor_script_write.cpp:190-204` 直接 `entry_point.callp`，没有 `call_gdscript_capturing`，也没有守卫）——实测它回 `ok` + `{\"result\":null,\"result_type\":\"Nil\"}`。这是既有边界，本批没动，脚本也**只记录不断言**（我在两次运行里都看到该行被标为 `recorded not asserted`，处理是诚实的）。"
  ],
  "unverified": [
    "**未独立复跑 730 s 时间线**（`10060` × 3 → 首次 `10061`）本身，以及「首次 10061 比末次 10060 晚约 7 s」是否成立；我只证明到「故障期进程/监听存活、端点不应答」与「对端消失后进程确实会退」的下游形状。",
    "**未对守卫停用态抓线程栈**，因此「主线程确实停在 `RemoteDebugger::debug()` 的 `while (is_peer_connected())`」这一条严格说是**源码推断 + 行为吻合**，不是栈证据。",
    "**未独立复跑 plain-console（`4.8.dev.custom_build.97fc49df4`）变体的十道门**——报告 §5.2 的 deviation 表我只能作为他证转述（并列在 §5.1），见 §5.1 的理由。",
    "**未独立复跑 doctest 里那个会 SIGSEGV 的「真调试器对端」用例**；`remote_debugger.cpp:630` 的空 `DisplayServer` 解引用是读源得到的支持，崩溃复现来自实现者日志。",
    "**未独立复跑 `repro_played.ps1` / `repro_peer.ps1` 的修复前观测**（20 s 无状态行 / 23.58 s 后被应答）。我用**同一个判据、同一条 `--remote-debug` 结构、同一台机器**做出了等价的「守卫停用 ⇒ 红」，但那是守卫停用态，不是 `15bbf1f50e` 基线二进制。",
    "**未逐一归因 g02 断言数在 mono/plain 相差 7**（431114 vs 431107，用例数都是 1586）——我只在 mono 侧独立测到 431114/431114。",
    "**未独立审计实现者的全部端口守卫记录**，只抽查了 `PORT-GUARD` 与 `guard_user_port_9877` 两类行（全部一致：修复前各轮 9877=pids 108432，canonical/本验收各轮为空）；未审计每个中间脚本的每一次 bind。"
  ]
}
```

**判定**：`verdict = pass`。门限检查逐条对照任务书 §4：修复**承载**（§2.1 受控实验转红且可复原）、根因链**未被推翻**、线上判据**通过**（34/34 ×2）、**无既有测试被削弱**、`g05` 归因**判为与本批无关**、原始工件**完好**。无 blocker / major。

---

## 2. 逐项核对表（任务书 §2 的 8 条）

| # | 核对项 | 判定 | 我做的命令 / 我看到的原始输出（节选） |
|---|---|---|---|
| 1 | 修复是否承载（移除守卫 → 红；恢复 → 绿；逐字节复原） | **通过** | `$t=[IO.File]::ReadAllText($p)`；`occurrences=2`；替换成 `break_guard(nullptr)` ⇒ `git diff --numstat` = `2 2 tools/tool_helpers.cpp`。`cmd /c modules\mcp_server\scripts\mcp057_build_mono.cmd` ⇒ `mcp057_build_mono: exit code = 0`。`verify_fixed.ps1` ⇒ **`CHECKS: 18/34 passed, 16 failed`**、`OUTER_EXIT=1`。恢复：`copy /Y %TEMP%\t151-accept-tool_helpers.cpp.bak` ⇒ sha `8dd73421…` 与备份相同 ⇒ `git status --porcelain` **空**、`git diff --stat` **空**、`git hash-object` = `2bfd041c95bb0e027573272ca296bd9b07b00aa6` = `git rev-parse HEAD:…/tool_helpers.cpp`（`.h` 也同）。重建后 `CHECKS: 34/34 passed, 0 failed`、`OUTER_EXIT=0`。 |
| 2 | 根因链 ①②③ | **通过（③为源码+行为支持，未抓栈）** | ① `editor_run.cpp:64-68` + `:70-71`；实测 cmdline `--remote-debug tcp://127.0.0.1:6007 --editor-pid 110092`。② `gdscript.cpp:823-826/843-846/862-868` + `gdscript_editor.cpp:300-304` + `remote_debugger.cpp:407-409/444`。③ `mcp_server.cpp:174-175/242/276-281`「all on the main thread, once per frame」+ 守卫停用时 15 s 无状态行而进程与监听在。 |
| 3 | 线上验收（≥34 项）+ 二进制身份 | **通过**（mtime 差 1 秒见 DEF-2） | 两次 34/34；`--version` = `4.8.dev.mono.custom_build.035edfce7`；sha256 `c4fb9982…`（`mono.exe`）/`bf47c8f0…`（`mono.console.exe`）与报告一致；mtime `08:09:15`/`08:09:16`。 |
| 4 | 门（g01/g02/g09/g10 + 另抽） | **通过**（唯一红 g05，见下条） | 我实跑**十道**：g01 `160/160`、g02 `1586/1586`、g03 PASS `SHA256 b83d79d3…`、g04 `3/3`、g06 PASS、g07 `10/10`、g08 `UNCLASSIFIED = 0`、g09 `ANCHOR_EQUAL`、g10 `22/22`；g05 见 §2.5。plain 变体并列见 §5.1（他证）。 |
| 5 | `g05` 归因 | **判「无关」成立** | 脚本 `:77/:79/:160/:166/:167` 与 fixture `50c5fb42…`/177 逐字核对；`git diff 15bbf1f50e..HEAD` 对 g05 三个引擎侧输入为空；自跑 exit=1 恰三条红 B0/B1/B2，其余 25 条全 PASS。 |
| 6 | doctest/wire 分工如实 | **通过** | `test_mcp_server.h:10320-10323`+`:10294-10303` 明写「只钉模块决定 / 真游戏半边由 wire 量 / 原因是 `remote_debugger.cpp:626-632` 空 DisplayServer SIGSEGV」；我读源与自跑 `22/22` 支持。 |
| 7 | 断言未被削弱 | **通过** | test_mcp_server.h `151 增 / 0 删`，`-` 行 0；6 条删除逐字列出，全在 `tool_helpers.cpp` 既有捕获语句。 |
| 8 | 禁区自查 | **通过** | 9877 三次 wire 运行前后皆空、收尾四端口全空、无 godot 进程；脚本从不 bind 9877；引擎 `origin…HEAD` 领先 3 且 origin 未动、主仓 `origin/master=HEAD`；`src/tests/config/.spec` 本批零提交；`PRD` sha `4c81c3a9…5c3a`。 |

---

## 3. 反例清单（我构造/移除了什么、观测到什么、是否推翻）

**实验一（唯一的源码改动：停用守卫）**

* 改了什么：`modules/mcp_server/tools/tool_helpers.cpp` 的**两处**调用点
  `GDScriptErrorBreakGuard break_guard(EngineDebugger::get_script_debugger());`
  → `GDScriptErrorBreakGuard break_guard(nullptr); // TASK-151-ACCEPT falsification: guard disabled`
  （`:2910` 编译窗口、`:3046` 执行窗口；`git diff --numstat` = `2 2`，只此一个文件）。
  这样守卫类的 `changed()` 变 false、构造/析构都不写 `ignore_error_breaks`，**且现有 doctest 仍应通过**（它用的是自己 new 的 `ScriptDebugger owned`，不经过这两处）——这一点让「红」只能来自线上行为而不是单测。
* 构建：`cd godot-mcp/godot; cmd /c modules\mcp_server\scripts\mcp057_build_mono.cmd` ⇒
  `mcp057_build_mono: exit code = 0`；日志尾部含 `Compiling modules\mcp_server\tools\tool_helpers.cpp` / `Linking Program …mono.console.exe` / `INFO: Time elapsed: 00:00:34.19` / `EXIT_CODE=0`（串行，输出未抑制，落 `%TEMP%\mcp057\mono_build.log` 与 `build-1-guard-off.console.txt`）。产物 `mono.console.exe sha256=9bb511f788559290af30030e2643c290e8992eacec2cf0096e4356d960d1414b mtime=08:26:46`、`mono.exe sha256=0678ce27b873396bf45c2f26f4fba0fffe7ef2eb4a3c78c9b8235800a0382ffd mtime=08:26:45`，`--version` 仍 `4.8.dev.mono.custom_build.035edfce7`。
* 观测（`verify_fixed.ps1`，原始输出 `wire-guard-off.console.txt`，逐条证据 `evidence-acc-guard-off/`）：
  * `CHECKS: 18/34 passed, 16 failed`，`OUTER_EXIT=1`。
  * Scenario A（自建 6011 对端、无 `--editor-pid`）：`game-call-analyzer-error: status_line=<NONE> elapsed_ms=15011 bytes=0`、parse `15005`、runtime `15015`、success `15002`、tools/list-after `20015`、`GET /mcp` `8002` —— **8 条全红**，而 `scenarioA_listener_still_present :: 9889 listen pids = 112768` 与 `scenarioA_engine_process_alive_at_end` **PASS**。
  * Scenario B（`editor_play_scene`，真冒烟场景，cmdline 实测 `--remote-debug tcp://127.0.0.1:6007 --editor-pid 106448`）：同样的 `status_line=<NONE>`、`15004 / 15014 / 15009 / 15012 / 20008 / 8006 ms` —— **8 条全红**；`scenarioB_game_process_alive_at_end :: pid 15364 still there` 与 `scenarioB_game_listener_still_present :: 9889 listen pids = 15364` **PASS**。
  * 编辑器对照（9888，`editor_execute_gdscript`）：analyzer `20 ms`、parse `14 ms`、runtime `13 ms`、success `5 ms`、tools/list 前后 200、`GET /mcp` `frame_count=5560` —— **9 条全绿**。
* 结论：**判据随守卫一起转红，且红的形状正是缺陷形状（连接建立、请求发出、无状态行；进程与监听仍在；同轮编辑器健康）。未推翻修复，反而证明它承重。**

**实验二（恢复）**

* `copy /Y %TEMP%\t151-accept-tool_helpers.cpp.bak <tool_helpers.cpp>`；实测恢复后
  sha256 `8dd7342162d4b194afd326d65b2702024f4b1fca3585fbfb8fd544d5fb7bc0b9` = 实验前备份 = 实验前工作树值；
  `git hash-object tool_helpers.cpp tool_helpers.h` = `2bfd041c95bb0e027573272ca296bd9b07b00aa6` / `f77a0f9fd8de3358f7797c6143777733dd12d695` = `git rev-parse HEAD:…` 的两个 blob；`git status --porcelain` 与 `git diff --stat` **双空**。
* 重建（`build-2-restored.console.txt`，`exit code = 0`）后 `verify_fixed.ps1` ⇒ `CHECKS: 34/34 passed, 0 failed`、`OUTER_EXIT=0`；同一二进制上 `--test-case="*error breaks armed*" --success` ⇒ `1 passed | 22/22 assertions`。**逐字节复原被三重证明（sha256 / blob / git 双空）。**

**我没有构造但需要说明的「等价反例」**：`scenarioB` 里 `played_runtime_error_is_32000_with_script_error` 也在守卫停用时转红（`-32000` 也被冻住），说明执行窗口那一个 scope 同样是承重的，不只是编译窗口。这支持 D225「保留执行窗口」的判断。

---

## 4. 对「修复是否承载」的独立结论

**承载，且是承重件，不是装饰。**

理由不是「实现者说它承载」，而是我在自己的机器上、用同一个判据、对**同一份源码的两种状态**做了 A/B：`get_script_debugger()` → `nullptr` 使 16 条线上检查全部转红（且红的形状与 hof-rs 冒烟里那条缺陷逐条对应），改回源码后重建即 34/34 转绿，且源码复原可在 sha256 / git blob / `git status`+`diff` 三个层面逐字节证明。同时我独立确认了它**修的是正确的层**：守卫只写引擎自己的 `ScriptDebugger::ignore_error_breaks`（`remote_debugger.cpp:407-409` 在阻塞前读它），在无调试器时零写入（我自己跑的第 (2) 组 doctest 断言），并且**没有**通过改契约、放宽门、改测试来换绿（契约侧零 diff、g04 逐字通过、测试文件 0 删除）。

**唯一需要提醒决策者的语义点**（不是缺陷，是取舍）：编译窗口那一个 scope 就足以让本任务的头号判据转绿；执行窗口那个 scope 是为「运行期错误必须仍回 `-32000`」服务的（我的停用实验里它同样红了）。D225 已决定两个都留——我核对到该决定与代码一致，且 `call_gdscript_capturing` 的守卫在无调试器时同样零写入，因此对编辑器/普通游戏/`--test` 的既有行为无可观察影响。

---

## 5. 未验证项与理由

### 5.1 plain-console（`4.8.dev.custom_build.97fc49df4`）变体——**未独立复核，只作他证并列**

任务书 §2.4 要求 plain-console 的 deviation 与 canonical **并列且标清**。我的处置：

| | canonical（mono） | plain-console deviation |
|---|---|---|
| 来源 | **我独立跑**（`run_gates_canonical.ps1`，全部十道） | **他证**：实现者 `recovery/work/task151/gates/task151/summary.txt` / `run_gates_task151.ps1` |
| 版本串 | `4.8.dev.mono.custom_build.035edfce7` | `4.8.dev.custom_build.97fc49df4` |
| g01 | exit=0 `160/160`、`6801/6801` | 他证 exit=0 `160/160`、`6801/6801` |
| g02 | exit=0 `1586/1586`（3 skipped）、`431114/431114` | 他证 exit=0 `1586/1586`、`431107/431107` |
| g09 | exit=0 `ANCHOR_EQUAL 035edfce7`（我自己跑到 `DIFF_COUNT=0`） | 他证 exit=0 `ANCHOR_EQUAL 97fc49df4` |
| g10 | exit=0 `22/22` | 他证 exit=0 `22/22` |
| g05 | exit=1（三条红，我独立复现） | 他证同样 exit=1、同因 |

**我不重跑它的理由（写清以免被读成偷懒）**：`97fc49df4` 的版本串之所以能被 g09 判 `ANCHOR_EQUAL`，是因为 plain 二进制是在「修复已提交、文档未提交」的那一刻构建的；我现在若 `build_local.cmd` 重建 plain，得到的会是**含修复**却仍只报 `97fc49df4` 的二进制——那才是真正的假绿（它的自报锚点不再对应它所含的源码）。要忠实地重跑 deviation，得先把引擎树 checkout 到 `97fc49df4` 再构建，那会动到「不得改动引擎树」的验收纪律边界（虽然可复原），且对 verdict 无增量：本批与判据无关的结论我已用 canonical 全十道独立覆盖，唯一红 g05 我已独立复现并归因。

### 5.2 其它未验证项

见 §1 结构化结论的 `unverified` 列表（730 s 时间线、线程栈、SIGSEGV 用例、修复前基线二进制复跑、plain 变体、g02 的 7 条断言差、逐个中间脚本的 bind 审计）。

---

## 6. 我没有独立复核的部分（明确列举）

1. `repro.ps1` / `repro_played.ps1` / `repro_peer.ps1` 的**修复前**运行——我只读了它们的脚本与产物（`evidence/`、`evidence-played/`、`evidence-peer/`），没有重跑。
2. 实现者 `evidence-verify/`、`evidence-verify-mono/` 两次 34/34（我用自己的 `evidence-acc-*` 三次运行替代，结论一致，但**没有**去比对 `checks.tsv` 逐行是否与实现者版本相同）。
3. `gates/task151/`（plain deviation）与 `gates/task151-canonical/` 的历史日志——只抽查了 `summary.txt`、`g04/g10` 的 `guard_user_port_9877` 行与 `PORT-GUARD` 行。
4. `logs/red2-marker.stdout.txt`（doctest SIGSEGV）——只读，未复现。
5. 实现者报告 §8 里自述的「4 个脚本 bug」「3 次额外构建」「mono 首次构建失败」等过程事实——无法从产物反查，一律按「未复核」对待。
6. `MCP-SERVER-HANDOVER.md §3 (k)` 的**文字**与实现/实测是否逐句对应：我核对了其中可核对的关键断言（守卫范围、还原原值、无调试器零写入、20 s/60 s/23.6 s/13 ms/3 ms、g05 三条红的出处、`remote_debugger.cpp:626-632` 的理由），未逐句审计整份 §3。

---

## 7. 给下一批的建议（**我没有改任何代码**）

1. **不要回退、不要改写本批的 `035edfce7f`**；`verdict=pass`，且我已证明守卫是承重件。
2. **优先做 TASK-152（g05 自包含化）**：在那之前，任何「十道门全绿」都是不可达的；建议同时给验收/门运行器加一行显式的「已知基线红：g05 B0/B1/B2（跨仓 fixture 漂移，见 HANDOVER §3(k)）」，把偶发红与已知红在**机器可读**层面分开（现在的处理只是人写的一段话）。
3. **门的「新鲜」判据应从 sha256 改成三元组**（`--version` + 本批新增用例是否在 + 只读探针），因为同一份源码的 scons 产物哈希不稳定（DEF-1）；否则下一批仍会有人用「sha 不同」误判「二进制不对」。
4. **给 §2 那类「修复是否承载」的受控实验写成一个可复用的脚本**（形如 `mcp073_gate3_double_red_phase.ps1`：前置「与 HEAD 逐字节一致」断言 + `try/finally` 恢复 + 恢复后 sha256/blob/porcelain 三重校验），把这次我手工做的四步（备份 → 改 → 重建 → 恢复）固化；本次实例已证明它值这个成本，但也已暴露出「手工做没有自动前置/后置校验」的风险。
5. **给 `repro_peer.ps1` 那条 23.58 s 判据补一次独立复跑**（分离 `--remote-debug` 与 `--editor-pid`），它是全套证据里唯一能区分「等调试器」与「死套接字/死进程」的直接对照；本轮我未能覆盖，建议下一批把它作为必做项并落原始日志。
6. **`--editor-pid` 使子进程在编辑器消失后自退的机制**（DEF-3）建议单独查清（作业对象？控制台组？），否则 HANDOVER §3(k) 与 D225 里那句话是「观测对、解释未定」。
7. **不要把「执行窗口也在守卫内」当成本缺陷的最小修复**：取消它只需删一个 scope，但会同时让「运行期错误不再暂停编辑器」这条消失；若要改，必须同时改 `verify_fixed.ps1` 第 3 项与 doctest（报告 §7.2 已给出回退点，我核对到该描述准确）。

---

## 附：本验收者产生的工件（均在授权落点 `recovery/**`）

```
recovery/reports/TASK-151-ACCEPTANCE.md                                   ← 本报告
recovery/work/task151-accept/wire-baseline-mono.console.txt               ← 基线 34/34（既有新鲜 mono）
recovery/work/task151-accept/wire-guard-off.console.txt                   ← 实验一：18/34（红）
recovery/work/task151-accept/wire-restored-mono.console.txt               ← 实验二：34/34（绿）
recovery/work/task151-accept/build-1-guard-off.console.txt                ← 串行重建（守卫停用），exit 0
recovery/work/task151-accept/build-2-restored.console.txt                 ← 串行重建（恢复后），exit 0
recovery/work/task151-accept/gates-acc-mono.console.txt                   ← 十道门全量控制台输出
recovery/work/task151-accept/gates/acc-mono/{g01..g10}.{stdout,stderr}.txt+summary.txt
recovery/work/task151-accept/g05.stdout.txt                               ← g05 单独复现
recovery/work/task151/evidence-acc-baseline-mono/                          ← 逐检查原始响应 + timeline
recovery/work/task151/evidence-acc-guard-off/                              ← 同上（红态）
recovery/work/task151/evidence-acc-restored-mono/                          ← 同上（绿态）
```

引擎仓（`godot-mcp/godot`）**零 diff、零提交、零 stage**；`git status --porcelain` 在验收结束时空。四端口（9877/9888/9889/6011）**全部空闲**，无遗留 `godot*` 进程。
