# ACCEPTANCE — Godot 内置 MCP 模块（`modules/mcp_server`）

验收记录按里程碑追加。每条结论必须可追溯到**独立执行**的命令输出，不采信实施者陈述。

---

## M0 — 工具链 + 非 mono 基线构建：**PASS**

- 验收方：全新独立子代理（`d243cc13-f583-4bb1-b467-6c4fded2826d`），未参与实施，未采信实施者结论。
- 实施摘要：装 SCons 4.11.1（`NO_PROXY=*` 绕过注册表代理）、跑官方依赖脚本（D3D12 Agility SDK / AccessKit / Pix / Mesa NIR
  → `%LOCALAPPDATA%\Godot\build_deps`）、`scons platform=windows target=editor module_mono_enabled=no -j8` 13.2 分钟 exit 0。

### 通过项（每条均为验收方独立复现）

| 项 | 方法 | 关键证据 |
|---|---|---|
| HEAD 与工作区干净 | 命令 | `HEAD=57277407e77e61b161f35dbd7aeb510f7a9e26a6`；`status --short` 仅 4 个 `??`（wrapper 脚本 + graphify 产物），**无 ` M`**；`diff --stat`/`diff --cached --stat`/`stash list` 全空 |
| 产物与字节数 | 命令 | `176,900,608` exe / `300,544` console.exe / `4,821,064` D3D12Core.dll / `4,932,640` d3d12SDKLayers.dll，与声称逐一一致 |
| 溯源确实是本源码所出 | 反例探测 | PE `machine=0x8664`、`link_ts=2026-09-21 11:54:42 UTC` 与文件 mtime **逐秒吻合**；版本串内嵌日期 `2026-09-18 15:41:32 UTC` 恰等于 HEAD 提交时间；`bin\D3D12Core.dll` 与依赖源同名文件 **SHA256 完全相同** |
| 非 mono | 反例探测 | 176 MB exe mmap 扫描：`GodotSharp`/`godot_mono`/`ModuleMono`/`hostfxr`/`coreclr` 全 absent；`bin/obj` 2983 个对象中 mono 匹配 **0**；PE 导入表仅系统 DLL |
| 与在用的 4.7.1-mono 不是同一二进制 | 命令 | 路径不同、`176,900,608` vs `179,589,128`、SHA256 `463676D2…` vs `8EC33BA6…` |
| 增量重建可复现 | 命令 | 同命令复跑：`scons: '.' is up to date.`、`done building targets`、`Elapsed 00:00:24.01`、**EXIT_CODE=0**（cmd 重定向 + `$LASTEXITCODE`，无管道污染） |
| 日志完整无错误 | 读文件 | `build-m0.log` 3242 行，以 `done building targets` + `EXIT_CODE=0` + `BUILD END` 收尾；`ERROR|error C|fatal error` **零匹配**；attempt1 失败原因确为 AccessKit + D3D12 依赖缺失（EXIT_CODE=255） |
| 未越界 | 命令 | hof-rs 无被跟踪改动；`godot_mcp_gdext` status 空且 19:00 后修改文件数 0；`runs\**` 最新 mtime 早于构建开始；9877 构建前后均在 `Listen`，编辑器进程 PID 36392 存活未重启 |

### 未阻断的发现（记入已知偏差）

- **ANGLE 渲染驱动被警告级静默跳过**（`angle=no` 事实上生效）：`build-m0.log:4`，bin 内无 `libEGL.dll`/`libGLESv2.dll`。
  不在 M0 验收标准内；若后续需要，补跑 `python misc\scripts\install_angle.py` 并以 `angle=yes` 重建。
- **`msgfmt` 缺失**：仅生成 `.po` 未生成 `.mo`（4 处 WARNING）。不在依赖路径上。
- nit：日志中链接器中文输出乱码（GBK 按 UTF-8 呈现），关键 ASCII 证据完整。
- nit：官方依赖脚本对 ARM64 PIX 库的 MinGW 适配失败（x86_64 不受影响，脚本仍 exit 0）。

### 未验证边界

- **U1** clean 全量重建的位级可复现性未验证（只验证到「同命令判定完全 up-to-date」）。
- U2 未采集运行中 4.7.1 编辑器的 `--version`（刻意为不干扰用户会话；已用路径/大小/SHA256 替代）。
- U3 未验证 4.8 产物的前台 GPU 渲染路径（只跑 headless）。
- U4 设计文档未规定 ANGLE 是否必须启用（本文件据此在 M0 只记为已知偏差）。

### 后续里程碑必须遵守的环境事实

- **用户正在使用的编辑器占用 9877**（4.7.1-mono，PID 36392）。因此 M1 起的端口相关验收**一律使用非默认端口**
  （编辑器侧 9888、游戏侧 9889），默认端口 9877 的**解析逻辑**只做单元测试，不实际占端口。
- 构建工具链固定为：SCons 4.11.1 / Python 3.9.7 / MSVC 14.42.34433 / WinSDK 10.0.26100.0。
- 模块单元测试用引擎自带 doctest：`SCsub` 中 `if env["tests"]: env_mcp.add_source_files(env.modules_sources, "./tests/*.cpp")`，
  以 `tests=yes` 构建后用 `--test` 运行（范式见 `modules/jsonrpc/tests/test_jsonrpc.cpp` 与 `modules/jsonrpc/SCsub:10-11`）。

---

## M1 — 模块骨架 + HTTP/1.1 子集 + JSON-RPC 2.0 + 2 个工具：**实现完成，独立验收待办**

- 状态：**实施者自测通过；本文件此节的数字全部是「实施者声称」，尚未经独立复核**（按阶段五纪律，
  必须由全新子代理重跑 `modules/mcp_server/scripts/accept_m1.ps1` 与全量 `--test` 后才能改写为「已验证」）。
- 代码落点：fork 分支 `feature/mcp-server-module`，HEAD `95dcb24c76`；全部改动在 `modules/mcp_server/**`，工作树干净、未推送。
- 提交：`fa747aed6b` 骨架与生命周期 / `29598d563a` 单测 / `a25f5e3a63` HTTP 传输 / `42657f863f` JSON-RPC+注册表+2 工具 /
  `1b157503d2` 死连接回收 + idle 下溢修复 + Expect:100-continue / `1aa7a3010f` 连接计数 + 未挂载即退场 / `95dcb24c76` 验收脚本。

### 实施者声称的验收结果（**待独立复核**）

| 用例 | 结果 | 关键证据（实施者提供） |
|---|---|---|
| `GET /mcp` 200 | ✅ | 状态 JSON 含 `tools:2 / port:9888 / is_editor:true / frame_count` 递增 |
| `initialize` | ✅ | `protocolVersion:"2025-03-26"`、`serverInfo.name:"godot-mcp-rs"` |
| `tools/list` 契约 | ✅ | name 与 `inputSchema` **逐字相等**；description 见「已知偏差」 |
| `tools/call get_project_info` | ✅ | `content[0].text` 可解析，含 `project_name` |
| 缺参/非法参数 | ✅ | `-32602`（`Missing tool name` / `Invalid arguments: expected an object`） |
| 未知 method | ✅ | `-32601` `Method not found: bogus/method` |
| 非法 JSON | ✅ | `-32700`，`id=null`，HTTP 400 |
| **并发 100 请求** | ✅ | `sent=100 received=100 unique_ids=100 mismatches=`；另加 6 轮×100 = **600/600 id 全匹配** |
| keep-alive 两连请求 | ✅ | `ka-1` / `ka-2` 各自正确 |
| 半包请求 | ✅ | 分两次（间隔 400 ms）写出后正确拼接 |
| body 超限 | ✅ | HTTP 413 + 关闭连接 |
| **游戏进程 9889** | ✅ | 同一份代码在游戏进程返回同一份 2 工具（`is_editor:false`），`inputSchema` 逐字相等 |
| 游戏进程不带 `--mcp-port` | ✅ | `configured_port=0 listen=false`，9889 未监听 |
| 端口占用 | ✅ | `bind failed on 127.0.0.1:9888 (error=22)` → `get_port()=0`，引擎不崩溃 |
| 连接回收（新增） | ✅ | 第 17 条被拒；关闭后 live=1；新请求 28 ms 内被服务 |
| Expect: 100-continue（新增） | ✅ | 22 ms 内回 `HTTP/1.1 100 Continue`，恰好一次，最终 200 |
| **用户端口 9877 守卫** | ✅ | 三次验收运行前后 `PID 36392` 不变、9877 始终在 Listen |

- 测试：模块 doctest **30 passed / 172 assertions**；**全引擎 `--test` 1456 passed / 424453 assertions / 0 failed**（修复前 1454/1455，多出一条 `Stray Node: MCPServer`）。
- 本轮实际修掉的两个真实缺陷（详见 `DECISIONS.md` D35/D36）：①死连接不回收导致连接预算饥饿；
  ②idle 超时的 uint64 下溢把活连接当空闲掐断（`case8` 的失败根因）。

### 已知偏差与限制（实施者登记，独立验收需复核）

1. **契约源 fixture 的描述是双重编码**：`tests/fixtures/mcp/tools_list.json` 的 **174/174** 条非 ASCII 描述
   都是「UTF-8 字节被按 Latin-1 读出」的形态（含 BOM）。因此 description **不可能逐字相等**；
   当前验收按「原始值或还原值任一命中」放行（实测还原值 `获取项目信息` 与实现一致）。
   **影响所有批次的对等门**；建议要么重新采集该 fixture（UTF-8 干净），要么把该兜底写进契约说明。
2. **`Transfer-Encoding: chunked` 不解码**（D33 判定为按需触发）：无 `Content-Length` 时返回 **411**（非 D33 措辞里的 400，
   411 才是语义正确的状态码——**更正 D33 的措辞**），并已用单测把该取舍固定住。
3. `Expect` 取其它值时静默忽略（无 417）。
4. `console_output` 仍未实现（GDR-8，刻意）。
5. `--test` 运行时模块会打印一行 `[MCP] SceneTree never became available; MCP server disabled.`（测试宿主无 SceneTree），
   随后实例被正确退场；属噪声。
6. 未验证边界：`editor_screen_size` 在 headless 下为 2×2（仅要求字段存在）；未做 mono / C# 相关验证（属 M3）。
