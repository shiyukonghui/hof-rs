# TASK-114 — SAC 拦截的落地（只读诊断工具包）+ C#→Web 导出的实测结论 + H8 两条 export-read 工具上线

> **本报告的每一个数字与每一段报错都来自本机真实命令的逐字输出**，没有从任何报告表格转抄。
> 「已经通过 / 应该可以」这类转述一律不写；没做到的写在 §E。
>
> **引擎侧零改动**（`godot/modules/mcp_server/` 一个字节未动），因此按铁律 7 **未触发**两变体重建
> 与十道门。二进制的 `--version` 仍是 `4.8.dev.mono.custom_build.3fdabe2d9`。
> `projects/` 下 **20 款正式工程**与它们的历史 `runs/` **只读未动**。

---

## 0. 一句话结论与如实边界

**A 段（C#→Web 的三组实测 + 源码闸门）、B 段（SAC 只读工具包三件套）、C④（H8 两条 export-read
工具上线）、D 段（台账重算 / 登记表改判 / 决策 / 提交 / 本报告）全部完成。**

1. **A 段结论（要的就是结论）：在 Godot 4 上，用 .NET/C# 编辑器构建 Web 版本是「不可能」，
   不是「需要什么配置」。** 依据是一道**编译期**闸门
   `godot/platform/web/export/export_plugin.cpp:424-429`：

   ```cpp
   bool EditorExportPlatformWeb::has_valid_export_configuration(...) const {
   #ifdef MODULE_MONO_ENABLED
       // Don't check for additional errors, as this particular error cannot be resolved.
       r_error += TTR("Exporting to Web is currently not supported in Godot 4 when using C#/.NET. ...");
       return false;
   #else
   ```

   `#ifdef MODULE_MONO_ENABLED` 是**编辑器构建**的属性，**与项目里有没有 C# 无关**；
   它在检查导出模板**之前**就 `return false`。三组运行时实验与它一致（§A2）。
2. **B 段**：`dist\tools\sac_diagnose.ps1`（**只读**）、`dist\tools\unblock_package.ps1`
   （**默认干跑**，`-Apply` 才动）、`dist\README-SAC.md`（中文，三条出路 + **不可逆警告**）。
   两个脚本**纯 ASCII**、无 BOM，PS 5.1 `[Parser]::ParseFile` 双解析 **PARSE_OK**，
   Python 侧 16 项策略检查 **全 PASS**，并且在本机**真跑通**（含一个带 MOTW 的 fixture 的
   干跑 / `-Apply` / 幂等三段）。
3. **A 段同时更正当场发现的一个事实错误**：任务书的前提「Godot 官方 Windows 构建同样未签名」
   **不成立**——本机安装的官方 4.7.1-stable mono Windows 编辑器 exe 的 Authenticode 状态是
   **`Valid`**（签名主体 `CN=Prehensile Tales B.V.`，签发者 `CN=Certum Code Signing 2021 CA`，
   有效期至 2028-06-16）。真正的理由是另外三条（§A4），已写进 `README-SAC.md` 与 D159。
4. **C④**：`project_get_export_info` / `project_list_export_presets` 从 **0 次**打到
   **13 / 14 次**（各含 2 次边界），覆盖真成功分支（两端口）、capability-missing 分支与
   空 schema 的未知参数闸门。全语料 `no_calls` **20 → 18**、`readback` **87 → 89**、
   达标 **102 → 104**、出现过的工具 **157 → 159**。

**必须同时说清的边界（没做到的地方）**：

* **A① 的 Web 模板最终没建成**：装好 emsdk（`emcc 6.0.10`）后构建进到编译阶段，仍以
  **12–13 个错误**失败，全部是 libc++/C 头文件查找顺序问题（`<cstddef> tried including
  <stddef.h> but didn't find libc++'s <stddef.h> header`）。**这不影响 A 段结论**
  （闸门在模板检查之前就拒绝），但意味着**本机没有可用的 Web 导出模板**，
  所以「非 .NET 编辑器 + GDScript 项目**导出成功**」这一格**没有拿到**，
  拿到的是「它通过了 .NET 闸门、只报缺模板」（§A2 控制组二）。
* **C 段只做了 H8 的两条**。任务书里排在 C①②③ 的 **H1 5 条 `count_only`**、
  **TASK-113 被降级的 3 条见证**、**H7 15 条**本轮**没做**（§E 写明为什么与下一步）。
* **`dist/` 一直是未跟踪目录**（TASK-107/109 的既有状态）。本轮只把
  `dist\tools\*.ps1` 与 `dist\README-SAC.md` 三个文件显式入库，**没有**把整个 `dist/`（含
  1.26 GB 的 zip 与 3.09 GB 的 exe）拖进 git。
* **一次铁律 1 的失误（如实披露）**：任务早期有两条**只读探查**命令用了 `2>nul` 重定向
  （第一次是在列 `dist` 与 `godot\bin` 目录时）。发现后立即改用无重定向写法。
  本轮所有构建 / 运行 / 会话 / 检查**均无重定向**；会话日志一律由 `run_game_session.ps1`
  自己的 `Start-Process -RedirectStandardOutput/Error` 产生。

---

## 1. 交付物与证据路径

| 交付物 | 路径 | 说明 |
|---|---|---|
| SAC 只读诊断 | `dist\tools\sac_diagnose.ps1` | SAC 状态 + CodeIntegrity 事件（点名包内文件）+ 签名/MOTW + 报错读法 |
| MOTW 清理（可选） | `dist\tools\unblock_package.ps1` | **默认干跑**；`-Apply` 才 `Unblock-File`；幂等 |
| 中文说明 | `dist\README-SAC.md` | 三条出路 + 不可逆警告 + 「换官方二进制」的更正 |
| 策略/双解析检查 | `recovery\work\task114\check_sac_tools.py` | 16 项，Python 半；PS 5.1 半见 §B2 |
| A 段实验工程 | `recovery\work\task114\web_probe\{gd_web_probe,cs_web_probe}` | GDScript 对照组 / C# 真游戏（pong 拷贝） |
| A 段构建环境 | `recovery\work\task114\emsdk\`（含 `env_task114.cmd`、`.emscripten`） | 手工展开的 emscripten 6.0.10 + 环境包装 |
| A 段签名取证 | `recovery\work\task114\probe_signatures.ps1` | 官方 Godot vs 自建二进制的签名对照 |
| H8 练习工程 | `projects\_exercises\{ex_export,ex_export_np}\` | 前者 2 个导出预设、后者**没有** `export_presets.cfg` |
| H8 会话与声明 | `tools\sessions\_exercises\{ex_export\h8-session.json,ex_export_np\h8n-session.json}` | 16 + 10 次调用 |
| 台账（重算） | `TOOL-COVERAGE.md` / `coverage.json` | 104 run / 172 trace / 8471 调用 / 159 出现过 |
| 登记表改判 | `tools\tool_coverage_unreachable.json` | `reclassified` 54 → **56**（只加不删） |
| 派生脚本 | `recovery\work\task114\{check_sac_tools,reclassify_h8,h8_coverage_probe,probe_signatures,mk_motw_test}.py/.ps1` | 全部可重跑 |
| 决策 | `F:\moonbit-hof-rs\DECISIONS.md` **D159** | 选项、否决理由、更正、回滚点 |
| 会话账 | `runs\_exercises\{ex_export\h8-task114,ex_export_np\h8n-task114}\` | trace + ledger + report（`runs/` 不入库） |

---

## A. C# 游戏能不能导出到 Web —— 实测三组 + 源码闸门

### A1. ① 尝试构建 Web 模板

**第一次（没装 emsdk，任务书要求的原命令）**，从 cmd 启动、无重定向：

```
$ cd /d F:\moonbit-hof-rs\godot-mcp\godot && scons platform=web target=template_release -j8
scons: Reading SConscript files ...
ERROR: Invalid target platform "web".
The following platforms are available:
        windows
Please run SCons again and select a valid platform: platform=<string>.
[exit code: 1]
```

**根因（源码，不是猜测）**：`godot\platform\web\detect.py:29-30`

```python
def can_build():
    return WhereIs("emcc") is not None
```

`emcc` 不在 `PATH` 上 → SCons 的平台列表里根本没有 `web`。本机 `where emcc` /
`where emsdk` / `where em++` **全部 "Could not find files"**。

**第二次（手工装好 emscripten 6.0.10 之后）**：

```
$ cd /d F:\moonbit-hof-rs\godot-mcp\godot && <emsdk>\env_task114.cmd scons platform=web target=template_release -j8
scons: Reading SConscript files ...
Building for platform "web", architecture "wasm32", target "template_release".
...
Compiling platform\web\web_main.cpp ...
...
...\.emcache\sysroot/include/c++/v1\cstddef:45:5: error: <cstddef> tried including <stddef.h>
 but didn't find libc++'s <stddef.h> header.  This usually means that your header search paths
 are not configured properly.  The header search paths should contain the C++ Standard Library
 headers before any C Standard Library, and you are probably using compiler flags that make that
 not be the case.
...
247 warnings and 13 errors generated.
scons: *** [bin\obj\platform\web\web_main.web.template_release.wasm32.o] Error 1
250 warnings and 12 errors generated.
scons: *** [bin\obj\platform\web\os_web.web.template_release.wasm32.o] Error 1
scons: *** [bin\obj\platform\web\javascript_bridge_singleton.web.template_release.wasm32.o] Error 1
252 warnings and 13 errors generated.
scons: *** [bin\obj\platform\web\display_server_web.web.template_release.wasm32.o] Error 1
scons: *** [bin\obj\main\main.web.template_release.wasm32.o] Error 1
scons: building terminated because of errors.
INFO: Time elapsed: 00:00:06.92
[exit code: 1]
```

同一命令**跑了两次**（第二次是在 `em++` 已经把 emscripten 的 sysroot/system library 缓存
预热之后），**两次的错误逐字相同**（`247 warnings and 13 errors` 等）。

**同一台机器上 emscripten 本身是好的**（这是为了排除「是我装坏了」而做的对照）：

```
$ <emsdk>\env_task114.cmd em++ emcc_smoke.cpp -o emcc_smoke.js
cache:INFO: generating system library: sysroot\lib\wasm32-emscripten\libc-debug.a... (1074 inputs, 24.52s)
...
cache:INFO:  - ok
[exit code: 0]
```

→ **结论：emscripten 6.0.10 能编普通 C++；是 Godot 4.8.dev 的 web 平台构建在这套
emscripten 下过不了 libc++ 头文件搜索顺序。**
**卡在哪一步：卡在 `Compiling platform\web\*.cpp`，不是卡在「没模板」。**

### A2. ②③ 三组导出实验（全部从 cmd 启动，无重定向）

| # | 编辑器 | 项目 | **逐字结论** |
|---|---|---|---|
| ② | `.mono.console.exe`（.NET 构建） | `cs_web_probe`（**真 C# 游戏**：`pong.csproj` + `src\*.cs`，预设 `Windows Desktop` + `Web`） | ❌ 见下 |
| ③a | **同一个** `.mono.console.exe` | `gd_web_probe`（**纯 GDScript 最小工程，一行 C# 都没有**） | ❌ **逐字相同** |
| ③b | `.console.exe`（**非** .NET 构建） | **同一个** `gd_web_probe` | ⛔ 通过 .NET 闸门，只报缺模板 |

**② 与 ③a 的逐字输出（两者完全一样）：**

```
$ cd /d F:\moonbit-hof-rs\godot-mcp && godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless \
    --path recovery\work\task114\web_probe\cs_web_probe --export-release "Web" out\cs_web\index.html
...
ERROR: Cannot export project with preset "Web" due to configuration errors:
Godot 4 中目前尚不支持使用 C#/.NET 导出到 Web。要在 Web 目标上使用 C#/Mono，请改用 Godot 3。
如果这个项目不使用 C#，请使用非 C# 版本的编辑器来导出项目。

   at: EditorNode::_fs_changed (editor\editor_node.cpp:1458)
ERROR: Project export for preset "Web" failed.
   at: EditorNode::_fs_changed (editor\editor_node.cpp:1474)
[exit code: 1]
```

**③b 的逐字输出（非 .NET 编辑器，同一个 GDScript 工程）：**

```
$ godot\bin\godot.windows.editor.x86_64.console.exe --headless \
    --path recovery\work\task114\web_probe\gd_web_probe --export-release "Web" out\gd_nomono\index.html
...
ERROR: Cannot export project with preset "Web" due to configuration errors:
在预期路径处未找到导出模板：
C:/Users/wyl/AppData/Roaming/Godot/export_templates/4.8.dev/web_nothreads_debug.zip
在预期路径处未找到导出模板：
C:/Users/wyl/AppData/Roaming/Godot/export_templates/4.8.dev/web_nothreads_release.zip

   at: EditorNode::_fs_changed (editor\editor_node.cpp:1458)
ERROR: Project export for preset "Web" failed.
[exit code: 1]
```

**为什么②③a 相同这件事是决定性的**：同一个 .NET 编辑器，对**一个根本没有 C# 的工程**，
报的是「C#/.NET 不能导出到 Web」。这排除掉「是项目里的 C# 触发的」「是 csproj 没编译」
「是某个 cs 文件出错」等一切项目侧假设——**触发条件是编辑器构建本身**。

**为什么③b 是必要的对照**：把编辑器换成非 .NET 构建，**同一份 `export_presets.cfg`、
同一个工程**立刻通过 .NET 闸门，失败点前移到「缺 `web_nothreads_*.zip` 模板」。
即两道门是**串联**的，而 .NET 那道门在**前面**。

### A3. 结论（④）

> **C# 游戏 Web 导出在 Godot 4 上是「不可能」，不是「需要什么条件」。**

* 触发条件是**编辑器构建是不是 .NET 版**（编译期 `#ifdef MODULE_MONO_ENABLED`），
  不是项目内容、不是预设写法、不是签名、不是模板；
* 引擎自己给的出路写在报错里：**"Use Godot 3 to target Web with C#/Mono instead."**
  —— 也就是退到 **Godot 3**（不是 Godot 4 的某个配置）；
* 若坚持 Godot 4 + Web，则**项目必须是 GDScript（或 GDExtension）**，
  并且还需要能构建/下载**匹配版本**的 Web 导出模板（本机自建的 `4.8.dev` 需要自己用
  emscripten 编模板，而 §A1 显示这套 emscripten 编不过去）。
* **对本仓的直接含义**：`projects/` 下 **20 款游戏全部是 C# 工程**，因此**它们不可能有 Web 版本**，
  除非改写成 GDScript 或退回 Godot 3。这条要写进交付说明，避免以后重复投入。

### A4. 附带更正：为什么「换 Godot 官方二进制」也无效

**实测（本机，`recovery\work\task114\probe_signatures.ps1`）：**

| 文件 | Authenticode 状态 | 签名主体 |
|---|---|---|
| `D:\Program Files\Godot_v4.7.1-stable_mono_win64\...\Godot_v4.7.1-stable_mono_win64.exe` | **Valid** | `CN=Prehensile Tales B.V., O=…, C=NL`；签发者 `CN=Certum Code Signing 2021 CA`；`NotAfter 2028-06-16` |
| `godot\bin\godot.windows.editor.x86_64{,.mono}.exe` 等 **6 个自建 exe** | **NotSigned** | — |
| `%APPDATA%\Godot\export_templates\4.8.dev\windows_release_x86_64.exe`（82198528 字节） | **NotSigned** | — |

> **更正**：任务书的前提「官方 Windows 构建同样未签名」**与实测不符**，官方编辑器 exe 是
> **有效签名**的。`README-SAC.md` 与 D159 按实测改写。

**「换官方二进制也无效」仍然成立，但理由是另外三条（任一条都足够）：**

1. **被拦的不是编辑器，是导出的游戏 exe。** 导出的 exe = **导出模板**（
   `windows_release_x86_64.exe`）的拷贝 + 追加进文件里的游戏 PCK。**换编辑器不换模板**，
   也不会给导出的 exe 带来任何签名；本包用的模板是本仓自建的，**实测 NotSigned**。
2. **这是 custom build**（`4.8.dev.mono.custom_build.3fdabe2d9`，带 `modules/mcp_server`），
   官方没有对应二进制可换。
3. **签名是发布者的动作，不是引擎的动作。** 拿官方编辑器重新导出一遍，得到的 exe 依旧未签名；
   要过 SAC 得去买证书用 `signtool` 签（`README-SAC.md` 出路 ②）。

---

## B. SAC 工具包（交给用户在被拦机器上自己跑）

### B1. 三个交付物

| 文件 | 做了/没做什么 |
|---|---|
| `dist\tools\sac_diagnose.ps1` | **只读**：① `HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy` 的 `VerifiedAndReputablePolicyState` 并解释 0/1/2/缺失；② `Microsoft-Windows-CodeIntegrity/Operational` 最近事件（3004/3033/3036/3077/3082），**并把事件文本里点名了包内文件名的那些单独标出**（`<hit>`），无关事件只摘要（`-AllEvents` 才全打印）；③ 包内 exe/dll 的 `Get-AuthenticodeSignature` 状态 + 签名主体 + SHA256 + MOTW（`Zone.Identifier`）；④ 两种失败形态（SAC 拒绝启动 vs DLL/.NET 宿主失败）的判别读法（含「SAC 弹窗没有『仍要运行』」）。支持 `-Json`。 |
| `dist\tools\unblock_package.ps1` | **默认干跑**：先打印「文件夹里有多少文件、其中多少个带 MOTW、逐个全路径清单」，一个字节都不改。加 `-Apply` 才调 `Unblock-File`（只删 `Zone.Identifier` 数据流），并**复核**还剩几个带 MOTW。**幂等**。 |
| `dist\README-SAC.md` | 中文。三条出路（①关 SAC + **不可逆警告**、②有信誉的代码签名证书、③SAC 关闭的机器/VM/Windows Sandbox），「换官方二进制」的更正版，工具说明，以及**明确列出本工具包不做的事**。**不含任何自动改注册表 / 关 SAC 的代码。** |

两个 `.ps1` 用**纯 ASCII** 写（首 4 字节 `b'<#\n '`，**无 BOM**），避免 Windows PowerShell 5.1
因代码页/BOM 差异读坏脚本。

### B2. 铁律 5「双解析」的两半

**PowerShell 5.1 半**（`[Parser]::ParseFile`，逐个脚本）：

```
PARSE_OK sac_diagnose.ps1
PARSE_OK unblock_package.ps1
```

（过程中确实抓到一个真语法错误并改掉：`Write-Host "…\"<dir>\""` 里用了 C 风格反斜杠转义，
PS 5.1 把 `\"` 当字符串结束，`<` 变成保留字 → `The '<' operator is reserved for future use.`
（第 414 / 437 / 438 行）。已改成单引号字符串。）

**Python 半**（`check_sac_tools.py`，16 项全 PASS）：

```
PASS ascii-only / no-BOM（两个脚本）
PASS sac_diagnose.ps1 is read-only            -- 可执行代码里没有任何写/改安全设置的 cmdlet
PASS unblock_package.ps1 touches nothing but Unblock-File
PASS Unblock-File is gated behind -Apply      -- gate offset 2224 < Unblock-File offset 2368
PASS sac_diagnose.ps1 never calls Unblock-File (in executable code)
PASS README-SAC.md has no registry-write command outside a negation list
PASS README documents exit 1 / exit 2 / exit 3 / 不可逆警告
{ "ok": true, "checks": 16, "failed": [] }
```

检查器用了一个小的「去掉注释与字符串」归约器，所以「禁止词只出现在帮助文本里」不会被误报，
而「出现在可执行代码里」一定会被报出（这条是它自己的判定口径，写在脚本注释里）。

### B3. 本机真跑（数值证据）

**只读诊断**（`-PackagePath godot\bin -Sample 3 -MaxEvents 200`）：

```
value        : 0
meaning      : 0 = OFF. Smart App Control is disabled. …
folder                : F:\moonbit-hof-rs\godot-mcp\godot\bin
exe/dll found         : 59
signature-checked     : 7
  of which NotSigned  : 7
files with MOTW       : 0
  NotSigned          no        300544  godot.windows.editor.x86_64.console.exe
  NotSigned          no     193622528  godot.windows.editor.x86_64.exe
  NotSigned          no     194207744  godot.windows.editor.x86_64.mono.exe
  NotSigned          no      82198528  godot.windows.template_release.x86_64.mono.exe
  ...
events matched : 23  (of 200 pulled)
  ids looked for : 3004, 3033, 3036, 3077, 3082
  naming a file inside your package : 0
  unrelated CI events on this machine : 23
  >>> NO Code Integrity event names a file inside your extracted package.
```

**`-Json` 输出可被机器读**：`$j | ConvertFrom-Json` → `tool=sac_diagnose.ps1 mode=read-only
machine=DESKTOP-JJKJAF8 sac_value=0 sac_state=off exe_dll=2 checked=2 not_signed=0 with_motw=2
events=1`。

**MOTW fixture 的三段实测**（`mk_motw_test.ps1` 造两个带 `ZoneId=3` 的文件 + 一个干净文件）：

```
# 干跑
files in folder (recursive, filter '*') : 3
files carrying a Mark-of-the-Web         : 2
Files that WILL be unblocked:
     1. …\motw_test\fake_core.dll  [ZoneId=3]
     2. …\motw_test\fake_game.exe  [ZoneId=3]
DRY RUN -- nothing was changed.

# -Apply
Applying Unblock-File ...
Unblock-File succeeded on : 2 / 2
still carrying a MOTW     : 0

# 第二次干跑（幂等）
files carrying a Mark-of-the-Web : 0
Nothing to do: no file in this folder carries a Mark-of-the-Web.
```

干净的 `clean.txt` **两次都没有被列出** —— 脚本没有越界处理。

---

## C. 覆盖循环尾巴 —— 本轮只吃了 C④（H8 两条）

### C1. 为什么先做 H8 的两条

任务书 C④ 自己点名「先试**只需 `export_presets.cfg` 的两条**」。读源码确认了这个判断：
`godot\modules\mcp_server\tools\project_export_read.cpp` —— 两个工具**只**读
`res://export_presets.cfg`（`ConfigFile`）与 `ProjectSettings`，**不需要真导出**；
输入 schema 是**空对象**（`{"properties":{},"required":[],"type":"object"}`），
`scope` 是 `BOTH`（编辑器与游戏进程都能调）；**缺文件不是错误**
（`presets_file_present:false` + `count:0` + `message`）。

### C2. 两个练习工程与两个真实会话

| 工程 | 内容 | 会话 | 结果 |
|---|---|---|---|
| `projects\_exercises\ex_export` | `export_presets.cfg` 有 **2 个预设**（`Windows Desktop` + `Web`） | `h8-session.json`，16 次 | editor 9 / game 8 条调用，各 2 条边界 |
| `projects\_exercises\ex_export_np` | **删掉了** `export_presets.cfg` | `h8n-session.json`，10 次 | editor 8 / game 2，0 失败 |

**逐字回包（节选）：**

```
[h8-001-…-editor-ok] port=9888 :: {"result":{"content":[{"text":"{\"count\":2,\"presets\":[{…}…"}}]}
[h8-004-…-editor-ok] port=9888 :: {"content":[{"text":"{\"capabilities\":{\"editor_export\":true,
                                 \"editor_process\":true,\"presets_source\":\"editor_export\"},…"}}]}
[h8-007-…-game-ok  ] port=9889 :: {"count":2,…}                       ← 游戏进程同样读得到 2 个预设
[h8-010-…-game-ok  ] port=9889 :: {"capabilities":{"editor_export":false,"editor_process":false,
                                 "presets_source":"export_presets.cfg"},…"}
[h8-013-…-editor-unknown-arg] :: {"error":{"code":-32602,"data":{"suggestion":
                                 "project_list_export_presets accepts no parameters"},
                                 "message":"Unknown parameter 'preset_name' …"}}
[h8-015-…-game-unknown-arg  ] :: {"error":{"code":-32602,"data":{"suggestion":
                                 "project_list_export_presets accepts no parameters"},
                                 "message":"Unknown parameter 'index' …"}}

[h8n-004-…-editor-nofile] :: {"count":0,"message":"'res://export_presets.cfg' does not exist:
                             this project has no export presets",…}
[h8n-001-…-editor-nofile] :: {"presets_file_present":false, "preset_count":0,
                             "unavailable":[{"capability":"export_presets", …}], …}
```

**ledger 退出码**（`run_game_session.ps1` 自报，非转述）：

```
editor: ledger exit 0     calls=9  verdicts: failed=2, ok_no_effect_observed=7
game  : ledger exit 0     calls=8  verdicts: failed=2, ok_no_effect_observed=6
（ex_export_np）editor: ledger exit 0  calls=8  verdicts: ok_no_effect_observed=8
（ex_export_np）game  : ledger exit 0  calls=2  verdicts: ok_no_effect_observed=2
```

### C3. 台账重算后的两条工具（`coverage.json` 逐字段）

| tool | calls | ok | boundary | 档位 | 桶 | 状态 | `gate` |
|---|---|---|---|---|---|---|---|
| `project_get_export_info` | **13** | 11 | 2 | `readback`（own_payload） | `>=5` | **达标** | `true` |
| `project_list_export_presets` | **14** | 12 | 2 | `readback`（own_payload） | `>=5` | **达标** | `true` |

`evidence` 字段逐个 run 记着调用数（`runs/_exercises/ex_export/h8-task114`: 8 / 9；
`…/ex_export_np/h8n-task114`: 5 / 5）。

### C4. 全语料增量（`python tools/tool_coverage.py`，非手算）

```
tool_coverage: mode=all-runs runs=104 trace_files=172 calls=8471 distinct=159
  buckets: 0=18 1-4=0 >=5=159 | status: 达标=104 缺证据=55 未达1-4=0 未达0=18
  registry: 74 members, 56 drift
```

| 指标 | TASK-113（基线） | TASK-114（本轮） | 增量 |
|---|---|---|---|
| run 目录 / trace / `tools/call` | 102 / 168 / 8444 | **104 / 172 / 8471** | +2 / +4 / **+27** |
| 出现过的工具名 | 157 | **159** | **+2** |
| `0` 次 | 20 | **18** | **−2** |
| 达标 | 102 | **104** | **+2** |
| 证据档位 | pixel 34 / file 24 / readback 87 / count_only 12 / no_calls 20 | **pixel 34 / file 24 / readback 89 / count_only 12 / no_calls 18** | readback +2、no_calls −2 |
| 登记表 `reclassified` | 54 | **56** | +2（`project_get_export_info`、`project_list_export_presets`） |

`TOOL-COVERAGE.md` 由脚本重写（不是手工编辑）；登记表用
`recovery\work\task114\reclassify_h8.py` 追加，该脚本**幂等**（跑第二遍输出
`replaced 2 of my own prior entries`，总数仍是 56），且**没有删除任何成员**（`members` 仍 74）。

---

## D. 收尾

### D1. 引擎改动判定 → 未重建、未跑十道门

* `godot/modules/mcp_server/` **一个字节未改**（本轮没有发现需要修的缺陷，也没有为了「顺手」而改）。
* 因此按铁律 7 **未触发**两变体重建、未重跑十道门、未跑 accept_m1、未 push 引擎仓。
* 二进制的 `--version` 仍是 `4.8.dev.mono.custom_build.3fdabe2d9`（含 TASK-112 三条修复的那个锚点），
  本轮两批会话都跑在它上面。

### D2. 依赖与环境问题（按纪律留档）

* **emsdk 官方引导装了 3 次，3 次都失败在同一步**：

  ```
  Unzipping file '…\emsdk\downloads\…-wasm-binaries.zip' failed due to reason:
  [WinError 5] 拒绝访问。: '\\?\…\emsdk\unzip_temp\install\emscripten\test\test_other.py'
   -> '\\?\…\emsdk\upstream\emscripten\test\test_other.py'
  error: installation failed!
  ```

  第 1 次是 `emsdk requires python 3.10 or above (D:\Anaconda\python.exe 3.9.7)`（已用
  Python 3.13 绕过）；第 2、3 次都是上面这条（第 3 次先 `rmdir /s /q upstream` 与 `unzip_temp`
  清掉半成品再跑，仍逐字相同）。**这是我自己的 `recovery\work\task114\emsdk\` 下的暂存目录，
  不涉及用户环境。**
* **绕过方式（非破坏性）**：不改 emsdk，直接用 Python `zipfile` 把同一个 zip 展开到
  `upstream_stage`，再用 `robocopy /MOVE` 就位成 emscripten 的规范布局
  （`upstream\{bin,emscripten,lib}`），并手写 `.emscripten`（`NODE_JS` / `PYTHON` /
  `LLVM_ROOT` / `BINARYEN_ROOT` / `EMSCRIPTEN_ROOT` / `CACHE`）与 `env_task114.cmd`。
  结果：`emcc --version` → `emcc (Emscripten gcc/clang-like replacement + linker emulating GNU ld)
  6.0.10-git (d6c521a7…)`，`em++` 编普通 C++ **exit 0**。
* **没解决的阻塞**：Godot 的 web 平台构建在这套 emscripten 下过不了 libc++ 头文件搜索顺序
  （§A1）。**这不是环境临时故障，而是版本组合问题**，所以按纪律**如实上报**而不是绕过它去改结论。

### D3. 跑前检查（铁律 4）

```
pre-h8   netstat LISTENING 9877/9888/9889 -> NONE ; tasklist godot -> NONE
post-h8  netstat LISTENING 9877/9888/9889 -> NONE ; tasklist godot -> NONE
```

每次会话**之前**都先查进程与端口；用户端口 **9877** 全程未被占用；
两批会话由 **cmd** 启动（`powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_game_session.ps1
-Game "_exercises\ex_export" -RunTag h8-task114 -EditorPort 9888 -GamePort 9889 -Session …`）。

### D4. 提交

见 §F。

---

## E. 本轮**没有**做的事（如实清单 + 下一步）

1. **H1 的 5 条 `count_only` 没补**（`editor_add_mesh_instance`、`editor_setup_camera_3d`、
   `editor_setup_lighting`、`editor_set_material_3d`、`editor_setup_world_environment`）：
   它们的见证读在 `h1` run 里缺失，要补必须重跑一次 h1 并把节点级读调用加进去。
2. **TASK-113 被降级的 3 条见证没补**（`editor_set_node_script`、`editor_set_control_theme`、
   `editor_remove_animation`）：要补必须重跑一次 c4/c5 型会话，在读回阶段加上
   `editor_get_node_properties {"path":"C4Node1","properties":["script"]}`、
   `{"path":"Panel","properties":["theme"]}` 以及**删除之后**的 `editor_list_animations`。
3. **H7 的 15 条没动**：任务书要求先分类「结构性不可达（`editor_simulate_*` 注入编辑器输入，
   依 D59/GDR-21 边界）」与「可达未做」，再练可达的。这一步本轮没做（预算给了 A 段与 B 段）。
4. **H8 剩下的 3 条**（`os_list_android_devices` / `os_deploy_to_android_device` /
   `project_get_android_preset_info`）仍需真机或 Android SDK；口径沿用登记表的
   「需要外部设备」而不是「不可达」。
5. **Web 模板没建成**（§A1）。因此「非 .NET 编辑器 + GDScript 项目**真的导出成功**」这一格
   没有拿到；拿到的是它的前置（通过了 .NET 闸门、只差模板）。
6. **没有消除 A 段遗留的构建产物占用**：`godot\bin\obj\*.web.template_release.wasm32.o` 等
   失败对象的残留、`godot\bin\.web_zip\` 的部分生成文件、以及 `recovery\work\task114\emsdk\`
   （约 1.5 GB，含 694 MB 的下载包）**都留在原地未删**——它们不在 git 跟踪范围内
   （`godot/bin` 与 `recovery/work` 的既有状态），需要时可整体删除
   `recovery\work\task114\emsdk\` 释放空间。

**下一批建议（按价值排序）**

1. 先把 **TASK-113 被降级的 3 条 + H1 的 5 条**补成真的内容级见证（升档一个会话就够）。
2. **H7 先分类再动手**：`editor_simulate_*` 5 条是结构性不可达（设计使然），
   其余 10 条大概率可达；建议建一个 `ex_editor` 练习工程做一次「编辑器 GUI 状态」批次。
3. H8 剩 3 条：测不了就按「需要外部设备」登记，别写「不可达」。
4. A 段的结论请**同步进交付说明与 README**：20 款游戏不可能有 Web 版本。

---

## F. 提交

主仓 `F:\moonbit-hof-rs` 的提交与工作树状态见本报告末尾的提交段（提交信息对应
`DECISIONS.md` D159）。**引擎仓（`F:\moonbit-hof-rs\godot-mcp\godot`）本轮无提交**：
`godot/modules/mcp_server/` 一个字节未改，`bin/` 下的 web 构建半成品不入库。

未纳入工作树的主仓条目（**都不是本任务的产物，一律未删除**）：
`godot-mcp/dist/` 里除本任务三个文件以外的既有产物（TASK-107/109）、
`godot-mcp/projects/_exercises/{ex_write2,ex_write3,ex_write4,ex_audio,ex_nav,ex_particles,ex_rec}/`
（沿用既有未跟踪状态）、`godot-mcp/tools/__pycache__/`、
`godot-mcp/recovery/reports/ACCEPTANCE-TASK-107.md`、
`godot-mcp/recovery/work/task104/logs/git-housekeeping.{out,err}.txt`（TASK-104 的既有改动）。
