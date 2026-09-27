# Windows 11 智能应用控制（SAC）与 godot-mcp 打包产物

> 本文回答一个问题：**为什么打包好的游戏 exe 在 Windows 11 上被智能应用控制（Smart App Control，下称 SAC）拦下、DLL 加载失败，怎么办。**
>
> 结论先说：**在我们的包上用"换个下载源""换个解压工具""换 Godot 官方二进制"都解决不了。**
> 只有三条出路：①关掉 SAC（**不可逆**）、②用有信誉的代码签名证书签名（自签名不够）、
> ③在 SAC 关闭的机器/虚拟机/Windows Sandbox 里运行。
>
> **本目录下的脚本不会、也不允许自动改动你机器的任何安全设置。** 关闭 SAC 必须由你本人
> 在设置界面里手动操作——因为关掉之后**在同一台机器上再也开不回来**，这个决定只能由你来做。

---

## 0. 一分钟自查

先在你的机器上跑只读诊断（**什么都不改**）：

```
powershell -ExecutionPolicy Bypass -File dist\tools\sac_diagnose.ps1 -PackagePath "<你解压出来的游戏目录>"
```

它会打印：

1. SAC 状态（注册表 `HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy` 的
   `VerifiedAndReputablePolicyState`，并解释 0/1/2 的含义）；
2. `Microsoft-Windows-CodeIntegrity/Operational` 里最近的拦截事件（3077 / 3033 / 3036 / 3004 / 3082），
   并且**把事件文本里点到了你包内具体文件**的那些事件标出来；
3. 你解压目录里 exe/dll 的签名状态与「来自互联网」标记（Mark-of-the-Web, MOTW）；
4. 怎么读你实际看到的那个报错。

关键判断（脚本会直接告诉你）：

| `VerifiedAndReputablePolicyState` | 含义 | 对我们的包意味着什么 |
|---|---|---|
| `0` | **关闭**。SAC 未启用 | **SAC 不可能是这次失败的原因**，请去查 DLL/解压布局（见第 2 节 (b) 型） |
| `1` | **开启（强制）**。SAC 正在拦截 | 未签名 + 来自互联网的 exe/dll 会被拦。这就是你遇到的那一型 |
| `2` | **评估**。SAC 在观察，还没开始拦 | 现在能跑，但**它随时可能切到 1**，属于定时炸弹 |
| 无此值 | 从未启用（或关闭后值被移除） | 同 `0` |

> ⚠️ SAC 的强制拦截**只会发生在「来自互联网」的文件上**（带 MOTW）。如果你是从本机
> 自己构建/从局域网拷贝的包，MOTW 可能不存在，那么即使 SAC 开着也可能不拦。

---

## 1. 症状长什么样

SAC 造成的失败和 DLL 找不到的失败**长得不一样**，别混：

**(a) SAC / SmartScreen 型：进程被拒绝启动**

* 弹窗形如「此应用已被阻止」「Windows 已保护你的电脑」；
* 或者双击后毫无反应，事件日志里出现 CodeIntegrity 拦截记录。

**怎么区分 SAC 和 SmartScreen：** SmartScreen 的弹窗里有「更多信息 → 仍要运行」；
**SAC 的弹窗没有「仍要运行」这个选项**。没有「仍要运行」= 是 SAC。

**(b) DLL / .NET 宿主型：进程启动了但起不来**

* `Could not load file or assembly ...`
* `Failed to load the dll`、`Unable to find the entry point`
* 错误码 `0xc000007b` / `0xc0000135`；窗口一闪就没了。

本包是**自包含（self-contained）的 .NET 导出**，目标机器**不需要装 .NET**，代价是
exe 旁边必须有一整套运行时 DLL（`coreclr.dll`、`hostfxr.dll`、`clrjit.dll`、`System.*.dll` 等）。

**这一型不是 SAC 造成的**——SAC 是拒绝启动，不会让进程跑起来再失败。常见原因是：

* 只把 exe 从压缩包里拖了出来，DLL 没跟着出来；
* 用不支持长路径 / 把目录结构压平的工具解压，破坏了相对布局；
* 杀软在解压时把某个 DLL 隔离了（先看杀软隔离区）。

**处理办法：重新解压整个压缩包到一个全新目录，在解压出来的原位置直接运行 exe。**

---

## 2. 三条出路

### 出路 ①：关闭 SAC —— **不可逆，请读完再动**

**操作路径（Windows 11）：**

1. 开始菜单 → 搜索并打开 **Windows 安全中心**（Windows Security）；
2. 左侧 **应用和浏览器控制**（App & browser control）；
3. 找到 **智能应用控制 / Smart App Control**，点 **设置 / Settings**；
4. 选择 **关闭 / Off**，确认。

也可以走「设置 → 隐私和安全性 → Windows 安全中心 → 应用和浏览器控制 → 智能应用控制 → 设置」。

> ### ⛔ 不可逆警告（这是本文最重要的一段）
>
> **SAC 一旦关闭，就无法在同一台机器上重新开启。**
> 微软的设计是：SAC 依靠「这台机器的 Windows 是全新安装、且没有不受信任的记录」这个前提工作。
> 关闭之后，系统失去了这个前提，**唯一的恢复方式是重装（重置）Windows**。
> 也就是说：**关掉 = 这台机器永久放弃 SAC 保护**，除非你把系统重装一遍。
>
> 因此：
> * 如果这台机器是你日常办公/开发的主力机，**不要**为了跑一个游戏包而关掉它；
> * 请优先考虑出路 ② 或 ③；
> * 如果你确实要关，请在关闭前确认这台机器上还有别的防护（Defender 实时保护、浏览器防护等）在跑。

**关掉之后：** 再跑一次 `sac_diagnose.ps1`，确认 `VerifiedAndReputablePolicyState` 变成 `0`，
然后再运行游戏。如果仍然失败，那**你的问题根本不是 SAC**，请回到第 1 节 (b) 型去查 DLL。

### 出路 ②：用有信誉的代码签名证书签名 —— **自签名不够**

SAC 判断的是「这个二进制是否**有信誉**」，它看的是：

* 文件是否有 **Authenticode 签名**；
* 签名是否来自 **受信任的 CA 签发的代码签名证书**（不是自己用 `New-SelfSignedCertificate` 造的那种）；
* 签名主体的**信誉**（微软会根据证书的历史和被使用情况累积信誉，也就是所谓 EV / OV 证书信誉）。

所以：

| 做法 | 对 SAC 有效吗 |
|---|---|
| 不签名 | ❌ |
| 自签名证书（`New-SelfSignedCertificate` + `signtool`） | ❌ **完全无效**。自签名只能让你自己机器上的策略信任它，SAC 不看这个 |
| 普通 OV 代码签名证书（CA 签发、证书在硬件 token/HSM 里） | ⚠️ 通常有效，但**新证书没有信誉**，可能需要一段时间 / 一定下载量才被判定为"有信誉" |
| EV 代码签名证书 | ✅ 最可靠，但成本高、需要企业主体资质 |

**要点：** 签名要用 `signtool sign /fd sha256 /tr <时间戳服务器> /td sha256 <exe>`，
并且**给包内每一个 exe 和 dll 都签**（或者至少给 exe + 所有会被加载的 dll 签）。
只签 exe 不签 dll，DLL 加载仍可能被拦。
**本机目前没有代码签名证书，也没有装 signtool**，所以这条路需要你先去购买/申请证书。

### 出路 ③：在 SAC 关闭的机器 / 虚拟机 / Windows Sandbox 里运行

这是**成本最低、风险最小**的一条，适合「我只是想看看游戏能不能跑」的场景。

* **Windows Sandbox**：Windows 11 专业版/企业版自带。
  开始菜单搜索 **Windows Sandbox**（若没有，需在「启用或关闭 Windows 功能」里勾选，
  这一步需要重启）。它每次启动都是一个全新的、用完即弃的 Windows。
* **全新的虚拟机**（Hyper-V / VMware / VirtualBox 装一个 Windows 11）。

⚠️ **不要假设沙箱/虚拟机里 SAC 一定是关的**——SAC 有可能会在一个满足条件的全新安装里
自动进入评估模式。**先在沙箱/VM 里跑一次 `sac_diagnose.ps1`，确认 `VerifiedAndReputablePolicyState=0`，
再运行游戏。** 如果它显示 `2`（评估）或 `1`（强制），在这个沙箱里你同样可以按出路 ① 关掉它
——反正沙箱用完即弃，「不可逆」在这里没有代价。

---

## 3. 为什么「换 Godot 官方二进制」也无效

这一条要分两个不同的场景说，因为我们实测发现原始说法**不准确**，必须更正：

### 3.1 实测数据（本机，2026-09-27）

| 文件 | Authenticode 状态 | 签名主体 |
|---|---|---|
| `D:\Program Files\Godot_v4.7.1-stable_mono_win64\...\Godot_v4.7.1-stable_mono_win64.exe` | **Valid** | `CN=Prehensile Tales B.V., O=Prehensile Tales B.V., L=Uitgeest, S=Noord Holland, C=NL`，签发者 `CN=Certum Code Signing 2021 CA`，有效期至 2028-06-16 |
| **我们自建**的 `godot\bin\godot.windows.editor.x86_64.mono.exe` 等 6 个 exe | **NotSigned** | — |
| **我们自建**的导出模板 `%APPDATA%\Godot\export_templates\4.8.dev\windows_release_x86_64.exe`（82198528 字节） | **NotSigned** | — |

> **更正：**「Godot 官方 Windows 构建同样未签名」这个前提**不成立**——实测官方编辑器的 exe
> 是**有有效签名**的。原始判断需要修正。

### 3.2 那为什么换官方二进制**仍然**救不了我们的包？

三个互不依赖的原因，任何一个都足够：

1. **被拦的不是编辑器，是导出的游戏 exe。**
   导出的游戏 exe 不是编辑器 exe，而是**导出模板**（`windows_release_x86_64.exe`）
   的一份拷贝 + 追加到文件里的游戏 PCK 数据。**换编辑器不会改变导出模板**，
   也不会给导出的游戏 exe 带来任何签名。
   本包用的模板是**我们自己从源码树构建的**（`windows_release_x86_64.exe`，82198528 字节，
   sha256 `AA883610178DC5322DFFA8111DEB0C2CC610364FDBFB557995B319B39785471E`），实测 **NotSigned**。
   用它导出的游戏 exe 自然也是未签名的。
2. **这是一个自建引擎（custom build）。** 本包基于
   `4.8.dev.mono.custom_build.3fdabe2d9`（带 `modules/mcp_server`），官方根本没有对应的二进制可换。
3. **签名是发布者的动作，不是引擎的动作。** 就算你拿官方编辑器重新导出一遍，导出的 exe
   依旧是未签名的——签名需要你去买证书、用 `signtool` 签（出路 ②）。微软不会因为
   "它是 Godot 导出的"就放行。

### 3.3 补充：换官方编辑器对 **C# 导出到 Web** 的影响是零（实测见第 5 节）

如果你考虑"换官方二进制"是为了**把 C# 游戏导出到 Web**，那条路在 Godot 4 上是**引擎层面直接封死**的，
和签不签名、用哪份官方下载无关。见第 5 节。

---

## 4. 本工具包里有什么

| 文件 | 作用 | 会改你的机器吗 |
|---|---|---|
| `dist\tools\sac_diagnose.ps1` | **只读**诊断：SAC 状态 + CodeIntegrity 拦截事件 + 包内文件签名/MOTW + 报错读法 | ❌ 只读，只用 `Get-*` / WMI 查询 |
| `dist\tools\unblock_package.ps1` | 可选：递归清除解压目录里文件的 MOTW（"来自互联网"标记） | ⚠️ 仅在你显式加 `-Apply` 时调用 `Unblock-File`（只删 `Zone.Identifier` 数据流，**不动注册表、不动 SAC**） |
| `dist\README-SAC.md` | 本文 | ❌ |

**`unblock_package.ps1` 默认是干跑（dry-run）**：不加 `-Apply` 时它只打印"将要处理哪些文件、
一共多少个"，一个字节都不改。它是幂等的——没有 MOTW 的文件是空操作，跑第二遍会说"无事可做"。

```
powershell -ExecutionPolicy Bypass -File dist\tools\unblock_package.ps1 -Path "<解压目录>"          # 干跑，看清单
powershell -ExecutionPolicy Bypass -File dist\tools\unblock_package.ps1 -Path "<解压目录>" -Apply   # 真清
```

> **清 MOTW 不等于解决问题。** 它只去掉"这个文件来自互联网"这个标记。
> 如果 SAC 处于强制模式（`1`），未签名的二进制**仍然可能被拒**。
> 清 MOTW 的价值在于：排除 MOTW 这个变量，从而让你能确定"到底是 SAC 拦的，还是 DLL 布局坏了"。

---

## 5. 附录：实测「C# 游戏能否导出到 Web」（TASK-114 A 段结论）

**结论：在 Godot 4 上，用 .NET/C# 编辑器构建 Web 版本是「不可能」，不是「需要额外配置」。**

理由是引擎源码里写死的一道闸门（`godot/platform/web/export/export_plugin.cpp:424-429`）：

```cpp
bool EditorExportPlatformWeb::has_valid_export_configuration(...) const {
#ifdef MODULE_MONO_ENABLED
	// Don't check for additional errors, as this particular error cannot be resolved.
	r_error += TTR("Exporting to Web is currently not supported in Godot 4 when using C#/.NET. ...");
	return false;
#else
	...
#endif
}
```

注意 `#ifdef MODULE_MONO_ENABLED`：这是**编译期**闸门，**只看编辑器是不是 .NET 构建，
完全不看你项目里有没有 C#**。

**实测三条（逐字输出见 `recovery\reports\TASK-114-REPORT.md`）：**

| # | 编辑器 | 项目 | 结果 |
|---|---|---|---|
| 1 | `.mono.console.exe` | `projects\pong`（真 C# 游戏） | ❌ `Godot 4 中目前尚不支持使用 C#/.NET 导出到 Web。` |
| 2 | `.mono.console.exe` | **纯 GDScript 最小工程**（一行 C# 都没有） | ❌ **同样的报错**——证明卡的是编辑器构建，不是项目 |
| 3 | `.console.exe`（非 .NET 构建） | 同一个 GDScript 工程 | ✅ 通过 .NET 闸门，只报缺 Web 导出模板（`web_nothreads_release.zip` 不存在） |

**而 Web 模板在本机也没法建成：**

* 直接跑 `scons platform=web target=template_release -j8` 时，**连配置都进不去**：
  `ERROR: Invalid target platform "web". The following platforms are available: windows`。
  根因在源码：`godot/platform/web/detect.py:29-30` 的 `can_build()` 要求 `emcc` 在 `PATH` 上
  （`return WhereIs("emcc") is not None`），而本机没有装 emsdk。
* 后来装了 emsdk（`emcc 6.0.10`），**构建进到编译阶段但失败**，12–13 个错误全是
  libc++ / C 标准库头文件查找顺序问题，例如：

  ```
  ...\.emcache\sysroot/include/c++/v1\cstddef:45:5: error: <cstddef> tried including <stddef.h>
  but didn't find libc++'s <stddef.h> header.  This usually means that your header search paths
  are not configured properly. ...
  ```

  逐字输出与两次尝试见 `recovery\reports\TASK-114-REPORT.md` §A。
  **这一步与上面的结论无关**：C# 能不能导出到 Web，由引擎源码里那道编译期闸门决定，
  不需要模板存在（闸门在检查模板**之前**就 `return false`）。

**所以：**
* 想用 C# 做 Web 游戏 → 不行。引擎自己给的建议是 "Use Godot 3 to target Web with C#/Mono instead"，
  也就是说只能退到 Godot **3**（老引擎、老 .NET，不是 Godot 4）。
* 想用 Godot 4 做 Web 游戏 → **项目必须是 GDScript（或 GDExtension）**，并且需要能构建/下载
  匹配的 Web 导出模板（本机自建的 `4.8.dev` 引擎需要自己用 emscripten 编模板）。

---

## 6. 这个工具包**不做**什么（请核对）

* ❌ 不修改注册表（没有 `Set-ItemProperty` / `New-ItemProperty` / `reg add`）；
* ❌ 不关闭、不调整 SAC / SmartScreen / Defender / WDAC；
* ❌ 不需要管理员权限（只有读 CodeIntegrity 事件日志时**建议**用管理员，
  非管理员下该节会显示"读不到"，其余功能照常）；
* ❌ 不删除、不移动、不重命名任何文件；
* ❌ 唯一的一次写入是 `unblock_package.ps1 -Apply` 里的 `Unblock-File`（只删 MOTW 数据流）。

两个 `.ps1` 都是**纯 ASCII** 写的，避免 Windows PowerShell 5.1 因编码/BOM 差异读坏脚本。
两个脚本都已用 PowerShell 5.1 的 `[Parser]::ParseFile` 验证过语法（`PARSE_OK`）。
