
---

## D154 — TASK-109：20 款 C# 游戏导出为可双击运行的 Windows exe 并分卷打包；缺模板→用同一份源码自建；Godot 的 .NET 导出强制 self-contained，遂补齐离线运行时包；导出默认不监听 MCP 端口（20/20 实测）

- 日期：2026-09-27
- 触发问题：交付物长期停留在「源码 + 证据」（旧包 `dist\godot-mcp-20games-20260927-0844.zip` 7 007 625 B / 614 文件，全是 `.cs` / 运行证据 / 截图，**没有一个可运行的 exe**）。用户明确要**可直接双击运行的游戏**。本机 `%APPDATA%\Godot\export_templates\` **为空**，导出无模板可用。
- 核查事实（全部来自本轮实测，不是转述）：
  * 引擎自报 `4.8.dev.mono.custom_build.1c7f5c07a`；导出报错给出引擎真正期待的路径是
    `export_templates\`**`4.8.dev`**`\windows_release_x86_64.exe` —— **不是**完整版本串（`GODOT_VERSION_FULL_CONFIG` 在 dev 构建下就是 `4.8.dev`）。任务书里「version 应等于 4.8.dev.mono.custom_build.1c7f5c07a」与引擎实际要求不符。
  * `editor_export_platform_pc.cpp:104-121`：`valid = dvalid || rvalid` —— **release 模板单独就够**，不必构建 debug。
  * `modules/mono/godotsharp_dirs.cpp:178-231`：模板（非 `TOOLS_ENABLED`）构建下，游戏侧程序集从 **PCK 内**或 **exe 同级 `data_<app>_<platform>_<arch>/`** 读，**模板目录不需要任何额外旁挂文件**。
  * `GodotTools\Build\BuildSystem.cs:239-240`：导出发布路径**硬编码** `--self-contained true`；而各游戏 `NuGet.config` 为离线还原 `<clear/>` 掉了所有源，只留 `godot\bin\GodotSharp\Tools\nupkgs`，该目录**没有** `Microsoft.*.App.Runtime.win-x64` → `NU1101`，导出静默失败（GodotTools 只回一句 "Failed to build project"，真报错在 `%APPDATA%\Godot\mono\build_logs\`）。
  * 游戏工程**只有 `.csproj` 没有 `.sln`**，而 GodotTools 导出走 `GodotSharpDirs.ProjectSlnPath`，硬要求 `<name>.sln`；缺失时 pck 只有 5.8 KB 且每帧刷 `InvalidOperationException: res://src/…cs is a C# file but no solution file exists`。
  * 游戏角色默认端口是 **0**（`mcp_server.cpp:108-117` 的 `should_listen`：只有编辑器默认监听，游戏必须显式 opt-in），20 款 `project.godot` 均未设 `godot_mcp/*`。
- 选项：
  1. **下载官方 export templates** —— 版本必须是自编译的 `4.8.dev.mono.custom_build`，官方没有；且违反「用同一份源码」；
  2. **用同一份源码自建 release 模板**（选中）；
  3. 改走 framework-dependent 以缩小体积（给每个工程加 `Directory.Build.props` 覆盖 `SelfContained`）—— 但 `--self-contained true` 是**命令行全局属性**，且会改到游戏工程文件，同时让游戏依赖目标机的 .NET 8 运行时；
  4. 改游戏工程 `NuGet.config` 加 `nuget.org` 源 —— 破坏 TASK-091 的离线还原设计；
  5. **保持 self-contained，把缺的运行时包补进本地离线源**（同时选中，配合选项 2）。
- 选择：**选项 2 + 选项 5**，外加**只新增不改动**地补 20 个 `export_presets.cfg` 与 20 个 `<game>.sln`。
- 理由：
  * 模板必须来自同一份源码 —— 官方源不可能有 `custom_build` 的模板，选项 1 直接出局。实测 `git diff --stat 1c7f5c07a1 1f9d0cb1c9 -- "*.cpp" "*.h" "*.cs" "*.py" "*.tscn" "*.cfg"` **为空**（HEAD 只是文档提交），所以从 HEAD 构建等价于从编辑器那个提交构建，版本串差一位是可解释偏差而非换源。
  * self-contained 是 Godot 的**设计意图**（源码硬编码），也是「双击就能跑」最强的含义：目标机**不需要装 .NET**。选项 3 要通过 `Directory.Build.props` 去覆盖命令行全局属性，既可能无效、又要动到 20 个游戏工程，还要把运行前提推给用户机器 —— 用降低交付质量的代价换体积，不符合本项目「不为省事牺牲正确性」的口径。
  * 选项 4 会破坏既有的离线还原决策；选项 5 只往既有本地源**增加**包，既不碰游戏工程、又保留（并加强）离线语义，且这些包成为可复用的本地资产，以后导出自足游戏不再需要网络。
- 做法与结果：
  * **模板**：从 cmd 跑 `scons platform=windows target=template_release module_mono_enabled=yes -j8`，**exit 0 / 9m14s**；产物 `godot.windows.template_release.x86_64.mono.exe`（82 198 528 B，sha256 `AA883610…5471E`）安装为 `%APPDATA%\Godot\export_templates\4.8.dev\windows_release_x86_64.exe`。
  * **离线运行时包**：用一份**临时** NuGet 配置（只加 `nuget.org`，不碰工程文件）跑一次 `dotnet publish --self-contained true` 让 NuGet 解析出版本 **8.0.25**，再把 3 个 `.nupkg`（`netcore.app.runtime` / `windowsdesktop.app.runtime` / `aspnetcore.app.runtime`，共 85 256 363 B）拷进 `godot\bin\GodotSharp\Tools\nupkgs`。`netcore.app.host.win-x64` 只有 7.0.20 但**不需要**（自足发布产物 187 文件里没有 apphost）。
  * **构建文件（只新增）**：`export_presets.cfg` × 20（已被各工程 `.gitignore` 忽略）、`<game>.sln` × 20（`dotnet new sln --format sln`，注意 .NET 10 默认生成 `.slnx`，GodotTools 要经典 `.sln`）。`.cs`/`.tscn`/`project.godot`/`.csproj`/`.gitignore` **零改动**。
  * **导出**：20 款串行，逐款唯一端口 **19401…19420**（绝不碰 9877），每款约 10–11 s，**20/20 exit 0**，exe 均 82 057 728 B（sha 各不相同，因 `modify_resources` 写入各自产品名），各带 187 文件 / 约 79.9 MB 的 `data_<game>_windows_x86_64/`。
  * **验证**：`<game>.exe --headless --quit-after 120`（**刻意不带 `--mcp-port`**）→ **20/20 退出码 0、stderr 全 0 字节**，且每款 stdout 首行都打出自己的 `*_READY`（真实游戏状态，如 `PAC_READY pellets=125 ghosts=4 pac=9,9`）；窗口化抽查 pong/snake/tetris **3/3** 8 秒后仍存活。**9877/9888/9889 的监听者在运行前后都是空集**，逐款日志含 `role=game configured_port=0 source=default listen=false` + `not listening (get_port()=0)`。
  * **取证工具自身的一个坑（本轮最有价值的教训）**：第一轮 `Start-Process -PassThru` + `-RedirectStandardOutput` 时 `ExitCode` 返回 **`$null`**，20 款全部打印 `exit=`（空）、汇总 `pass_exit0=0` —— 若不深究就会把「空值」当成「通过」或「全败」。改用 `ProcessStartInfo` + `ReadToEndAsync` 后拿到真值 20/20。**「跑过了」和「拿到可核对的真值」是两回事。**
  * **打包**：压缩前 ~3.2 GB（超 2 GB 上限）→ 按游戏切成 **2 个 zip**（632 348 706 B / 632 337 210 B，各含 1890 payload 文件 + 中文 README.md + MANIFEST.txt + RUN-CHECK.txt）。自检 **PASS**：20/20 一款不少、无重复、MANIFEST 与 zip 双向一致、每卷 6 个抽查文件解压重算哈希逐位相符；再把 **pong 从 part2 解出来直接跑，exit 0**。
- 预期影响与回滚点：
  * 交付口径从此改变：`dist\godot-mcp-20games-exe-20260927-0927-part{1,2}of2.zip` 才是「可运行的游戏」，旧的源码包不再是交付物。
  * 模板与 3 个运行时包成为**可复用的本地资产**：以后任何自足 C# 游戏导出都只需 `export_presets.cfg` + `<game>.sln`，不必再联网、不必再等 9 分钟构建；模板安装在 `%APPDATA%` 下（系统级，不随仓库回滚，属于环境状态，已在报告中记录 sha256 以便核对）。
  * 模板再加一条：**导出类任务先读引擎源码里模板/发布路径的判定逻辑，再动手**——本次四处阻塞（BOM 的 preset、缺 `.sln`、self-contained 的 NU1101、GodotTools 吞掉 MSBuild 真报错）里有三处是「看源码 5 分钟胜过试错半小时」；以及**「失败」必须读到工具真正的错误输出层**（`%APPDATA%\Godot\mono\build_logs\`），不能停在 GodotTools 那句转述上。
  * 回滚点：删掉 `dist\godot-mcp-20games-exe-20260927-0927-part*.zip` 与 `dist\exe\`；模板从 `%APPDATA%\Godot\export_templates\4.8.dev\` 删除；`<game>.sln` 与 `export_presets.cfg` 逐个删除即可（都是纯新增文件，没有任何既有文件被改写）。
  * **遗留（不阻塞，报告中已列）**：编辑器与模板版本串差一位（源码零差异）；只构建了 release 模板故 `--export-debug` 不可用；窗口化只抽了 3 款；键盘可操作性未逐款真按过（README 只如实列出各工程声明的输入动作）。
