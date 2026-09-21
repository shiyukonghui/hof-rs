# REQUIREMENTS — Godot 内置 MCP 模块（`modules/mcp_server`）

- 子项目代号：`godot-mcp-engine`
- 上游决策：hof-rs 仓库 `DECISIONS.md` 的 **D30**（方向变更）与本目录 `DESIGN-OVERVIEW.md`
- 代码落点：**Godot fork**（`F:\RustProjects\godot-mcp-pro\code\godot`），本地分支 `feature/mcp-server-module`
- 规范工件落点：本目录（hof-rs 仓库内，与决策日志同处），因为「为什么这样做」的记录在这里

---

## 1. 目标（要解决的根本问题）

现有 MCP 是 GDExtension，挂在 `EditorPlugin` 上，**只存在于编辑器进程**。由此产生两个无法在 addon 内绕开的硬限制：

1. `simulate_action` / `get_input_actions` 作用于**编辑器**的 `Input`/`InputMap`，而游戏是**独立子进程**（`editor/run/editor_run.cpp` 用 `--path` 拉起），游戏侧靠 `user://` 文件 IPC 转发 → **编辑器侧输入注入永远打不到游戏进程**。
2. 游戏侧唯一的脚本执行工具 `execute_game_script` 走 `Expression.execute([], base, false)`，**只能解析 base 的成员**，引擎单例与全局类一律不可达（`Input`/`InputMap`/`Engine`/`OS`/`InputEventAction` 全部 `Invalid named index '...' for base type Object`）——D29 裁决 6 已实测确认。

**因此在上游架构下，ho f-rs 的 E3（可玩性证据）不可判定。** 本子项目的目标是把 MCP 工具逻辑**集成进引擎本体**，让同一份实现同时存在于编辑器与游戏两个进程内，从而直接访问 `Input`/`InputMap`/`SceneTree`/`Viewport`。

同时消除一类已确认的缺陷：现有 HTTP 传输用**单一 FIFO 队列** `try_recv` 取响应、**不按 JSON-RPC `id` 关联**（`mcp/transport_http.rs`），在并发/丢包下必然错位——这正是 `smoke-t3`/`smoke-t5` 观测到的「响应慢一拍」根因。新实现必须按 `id` 关联，从构造上杜绝此类缺陷。

## 2. 成功标准

| 编号 | 标准 | 判定方式 |
|---|---|---|
| G1 | 模块在 fork master（`4.8.0.dev`，HEAD `57277407`）上编译通过，产出编辑器二进制 | SCons exit 0 + 二进制 `--version` 含基线短哈希 |
| G2 | 编辑器进程内置 HTTP JSON-RPC 服务（默认 9877），`tools/list` 与既有 174 工具 **分批对等** | 逐批 `tools_list.json` schema 逐字 diff + 显式偏差清单 |
| G3 | **游戏进程**（同二进制 + `--mcp-port=N`）能用 `simulate_action` 真正驱动运行中的场景（`Player.position` 发生变化），并能在游戏进程内读 `InputMap` | 引擎内 E2E 脚本：启动游戏 → 注入 → 采样位置 → 断言变化 |
| G4 | 响应严格按 JSON-RPC `id` 关联，任何并发/乱序下零错位 | 并发 100 请求压测：每个响应 id 与其请求 id 一致 |
| G5 | hof-rs **不改工具契约**即可切到引擎端点（编辑器端 + 游戏端），真实 T=1 冒烟 E1–E6 全 met | hof-rs 真实冒烟 + `ACCEPTANCE.md` |
| G6 | C# 可作为游戏开发语言：mono 构建可用，`.csproj` 由引擎生成，`dotnet build` 零错误可被 Tester 采证 | mono 构建产物 + C# 工程 `dotnet build` + 游戏可启动 |

## 3. 非目标

- 不重写编辑器 UI；不追求在 v1 完成 174 工具全量对等（**分类分批**，见 `DESIGN-DETAIL.md` §6）。
- 不替换 Rust GDExtension（两者**并存**，GDExtension 继续服务其他用户/工具）。
- 不针对 Windows 以外的平台（v1 假设）。
- 不做导出发行版的加固（游戏侧端点默认**不开启**，必须显式 `--mcp-port`）。
- 不改 hof-rs 的既有运行时语义（R1–R13）；本子项目只**新增**端点与「Runtime 拥有游戏进程」的能力。

## 4. 约束（硬性）

- **C1 无 GDExtension 依赖**：模块必须是引擎内置 module，不得依赖 addon 的 DLL 或 GDScript autoload。
- **C2 主线程安全**：所有 Godot API 调用只能发生在主线程；不得在其它线程触碰 `Input`/`SceneTree`/`Object`。
- **C3 按 id 关联**：任何请求-响应配对**不得**依赖 FIFO 顺序或共享队列位置。
- **C4 默认安全**：游戏进程默认不监听端口；编辑器进程默认监听 9877（与现有 addon 一致，保持 hof-rs 零改动）。
- **C5 零源码污染**：除 `modules/mcp_server/**` 外，**不得**修改引擎源码；若确实需要（例如未来要让编辑器 run bar 传端口），必须单独记录为决策并给回滚点。
- **C6 许可**：所有新文件带 Godot 风格 MIT 许可头。
- **C7 不推送**：fork 上只本地提交，除非用户明确要求推送。
- **C8 构建可复现**：构建命令与工具链版本必须记录（见 `DECISIONS.md` M0 条目与 `recompute_plan`）。

## 5. 假设

- A1 客户端只有 hof-rs；`POST /mcp` 足够，**不需要 SSE/WebSocket**。
- A2 游戏进程可以由**同一个编辑器二进制**通过 `--path <project> [scene]` 运行（无需导出发行模板）。
- A3 工具名、描述与 `input_schema` 必须与现有 174 工具**逐字一致**（`tests/fixtures/mcp/tools_list.json` 是权威清单）。
- A4 主线程逐帧泵在模态对话框/长阻塞期间不响应，客户端超时是既有能力（hof-rs `tools.ready_timeout_seconds`）。
- A5 mono 构建需要 .NET SDK；本机已具备（9.0.100 / 9.0.300 + .NET 8 运行时），工程侧目标框架为 `net8.0`。
- A6 hof-rs 侧「游戏进程由 Runtime 自己拉起」是本子项目的配套改动（见 `DESIGN-DETAIL.md` §7）。

## 6. 里程碑（每个里程碑结束派**独立**验收子代理）

| 里程碑 | 内容 | 出口门 |
|---|---|---|
| **M0** ✅ | 装 SCons + 非 mono 基线构建 | 二进制可启动、版本与 HEAD 一致、零源码改动 |
| **M1** | 模块骨架 + HTTP + JSON-RPC + 2 个 B1 工具 | 9877 可探活；`tools/list` 形状正确；并发 100 请求零错位；编辑器与游戏两种进程都能逐帧泵 |
| **M2** | B1 + B2 批次（含游戏侧输入/观测） | **G3/E3 解锁**：游戏进程内注入 → 位置变化 |
| **M3** | mono 构建 + C# 工程可跑 | `.csproj` 生成、`dotnet build` 零错误、游戏可启动 |
| **M4** | B3 + B4 批次 | 逐批对等门通过 |
| **M5** | B5 批次 + hof-rs 切端点 + 真实 T=1 冒烟 | E1–E6 全 met，`ACCEPTANCE.md` 更新 |

## 7. 验收标准（每个里程碑通用）

1. **构建**：`scons` 命令 exit 0，且无新增编译警告（相对基线）。
2. **契约**：涉及工具时，`tools/list` 与权威清单逐字 diff，偏差必须列入显式清单并给理由。
3. **行为**：每个工具至少有 ①成功路径 ②参数缺失/非法路径 ③底层失败路径 三类证据。
4. **反例**：验收方必须自造反例（非法 JSON、超长 body、未知 method、并发乱序、端口占用、游戏进程崩溃重启）。
5. **不回归**：hof-rs 离线测试不回归；既有 Rust addon 不被修改。
6. **证据**：真实命令输出原文，不接受「应该通过了」；区分「证据支持」与「推断」。

## 8. 待确认/开放项

- O1 编辑器侧是否需要一个状态 dock（`EditorPlugin`）？当前设计为**可选**（先不做，M1 只注册单例）。
- O2 是否需要把 `modules/mcp_server/**` 拆成独立仓库以后上游化？当前留在 fork 内。
- O3 C# 化会让 hof-rs 的 `PRD-mario.md` 增加 P7/P8（游戏逻辑用 C#、C# 编译零错误）——**需显式回到阶段一更新**，不在实现里回填。
