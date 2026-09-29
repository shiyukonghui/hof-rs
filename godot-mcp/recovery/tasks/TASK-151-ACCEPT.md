# TASK-151-ACCEPT — TASK-151（引擎侧调试器冻结修复）独立验收

> 你是**独立验收子代理**。不得继承实现者或调度者的结论。
> 实现者报告：`godot-mcp/recovery/reports/TASK-151-REPORT.md`（**线索，非证据**）。
> 产物：`godot-mcp/recovery/reports/TASK-151-ACCEPTANCE.md`。
> **落点**：引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`，
> 被测 HEAD **`035edfce7f`**，基线 `15bbf1f50e`）+ 外层仓的 `godot-mcp/recovery/**`。

---

## 1. 先读

`godot-mcp/recovery/tasks/TASK-151.md`（实现者判据）→ `reports/TASK-151-REPORT.md`（自述）
→ `DECISIONS.md` **D224**、**D225**（授权范围与裁决）→ 引擎 `modules/mcp_server/docs/HANDOVER` §3(k)
→ 代码：`modules/mcp_server/tools/running_game_script_execution.cpp`、
`editor/run/editor_run.cpp:64-71`、`core/debugger/remote_debugger.cpp:444` 与 `:626-632`。

## 2. 核心复核项（逐条自己复现，给命令 + 原始输出 + 文件:行）

1. **修法是否承载（头号反例目标——非空洞性）**：**移除/停用守卫**（`GDScriptErrorBreakGuard`）→
   **重建** → 线上判据（`work/task151/verify_fixed.ps1` 或等价）**必须变红**；恢复后**必须转绿**。
   若移除守卫后仍是绿的 ⇒ **判 fail**（说明修复没起作用/判据不是冲它去的）。
   实验后必须用 `git status`/`diff` 双空 + blob 比对证明引擎仓已**逐字节恢复**。
2. **根因链是否成立**：①`editor_run.cpp:64-71` 确实**无条件**追加 `--remote-debug` + `--editor-pid`；
   ②有调试器时 `GDScript::reload()` 失败会走到 `remote_debugger.cpp:444` 的 `while (is_peer_connected())`；
   ③该等待发生在**主线程**（= MCP 端点泵帧的线程）。**用代码+你自己的测量**支持或推翻；
   若你无法复跑"peer 释放后同一连接被应答"的对照实验，**明写未做**，不得默认成立。
3. **线上验收**：在**新鲜 mono** 上自己跑一遍（≥34 检查）：被玩的游戏里 `code` 编译不过 ⇒
   `-32602` + `data.parse_error` 且**端点与进程存活**；运行期错误仍 ⇒ `-32000` + `data.script_error`。
   并**自己核对** mono 二进制的 sha256/mtime/`--version`（实现者称 `c4fb9982…` / 08:09:15 /
   `4.8.dev.mono.custom_build.035edfce7`）。
4. **门**：自己跑 `g01`/`g02`/`g09`/`g10`，并**另抽至少两道**其它门；核对
   `g01` 160/160、`g02` 1586/1586、`g10` 22/22、`g04` 3/3 契约逐字、`g09` ANCHOR_EQUAL。
   **plain-console 的 deviation 结果**必须与 canonical mono 结果**并列**且被标清（不得混成一句"全绿"）。
5. **`g05` 归因（必须独立判定）**：实现者称 `g05` 仍 exit=1 且**与本批无关**——`g05` 的 B0/B1/B2 以
   **hof-rs 的** `tests/fixtures/mcp/tools_list.json` 为基准（hof-rs 在 `db2eed7` 重采为 `50c5fb42…`/177，
   脚本内冻的是 `8f8051c4…`/174）。请自己核实：①脚本里该路径与常量确实是那两个值；
   ②`git diff 15bbf1f50e..HEAD -- <g05 的输入文件>` 为空；③`g05` 其余检查确实全过。
   ⇒ 判定"无关"成立与否。
6. **doctest/wire 分工**：核对报告 §7.1 是否**如实**声明"真游戏不冻结"这半边**未被单测覆盖**、
   以及其理由（`remote_debugger.cpp:626-632` 的空 `DisplayServer` 会 SIGSEGV）。
7. **断言未被削弱**：`git diff 15bbf1f50e..HEAD --stat` 与 `--numstat`；测试文件**不得**有删除行。
8. **禁区自查**：`9877`/`9888`/`9889`/`6011` 全程空闲且**从未被本批占用**（实现者称每次运行前后都记了守卫行，
   请抽查其证据）；未 `push`（两个仓的 `origin` 都未前进）；hof-rs 侧（`src/**`、`tests/**`、`config/**`、`.spec/**`）
   **零改动**；`PRD-mario.md` sha256 仍 `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`。

## 3. 纪律

只读为主；**唯一**允许的改动是 §2.1 的"移除守卫→重建→恢复"受控实验（必须逐字节恢复并证明）。
**绝不占用 9877**（它当前空闲，也**不许**被你占用）；自用测试端口只用 **9888/9889**，收尾复核已释放。
串行构建、不抑制输出；不改 hof-rs 侧；不 `push`、不 stage；不删改既有测试换绿。
不联网（除回环测试端口）。

## 4. 结构化结论（写进报告 §1）

```json
{ "verdict": "pass" | "fail",
  "criteria": [ { "id": "FIX.load_bearing|ROOT_CAUSE|WIRE.34|GATES|G05.attribution|DOCTEST_SPLIT|NO_WEAKENING|GUARDS",
                  "pass": true, "evidence": "命令 + 真实输出 + 文件:行" } ],
  "defects": [ { "id": "DEF-x", "severity": "blocker|major|minor|info", "what": "...", "reproduction": "..." } ],
  "risks": [ "..." ], "unverified": [ "..." ] }
```

`verdict=fail` 门槛：修复**不承载**、根因链被推翻、线上判据未通过、任何既有测试被削弱、
`g05` 归因被判为**与本批有关**、或原始工件被动过。

## 5. 报告必含小节

1. 结构化结论 + 真实命令与退出码；2. 逐项核对表；3. **反例清单**（你构造/移除了什么、观测到什么、是否推翻）；
4. 对"修复是否承载"的独立结论；5. 未验证项与理由；6. 你没有独立复核的部分；
7. 给下一批的建议（**不要**自己改代码）。

**回报给父代理只有一行：报告文件路径。**
