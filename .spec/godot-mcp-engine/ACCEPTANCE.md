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
