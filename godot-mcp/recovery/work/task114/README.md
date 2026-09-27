# TASK-114 A 段：C#→Web 导出的实测复现说明

这个目录里的东西**不是**交付物，是「A 段结论怎么来的」的可复现材料。

## 目录

| 路径 | 是什么 | 入库吗 |
|---|---|---|
| `web_probe/gd_web_probe/` | **纯 GDScript 最小工程**（`project.godot` + `main.tscn` + 一个 Web 预设）。控制组 | ✅ |
| `web_probe/cs_web_probe/` | **真 C# 游戏**（`projects/pong` 的拷贝，含 `pong.csproj` + `src/*.cs`） | ❌ 一条 robocopy 就能重建（见下） |
| `emcc_smoke.cpp` | 用来证明「emscripten 本身没坏」的 12 行 C++ | ✅ |
| `emsdk/` | 手工展开的 emscripten 6.0.10（**约 1.5 GB**：694 MB 下载包 + upstream + node + python） | ❌ 见 `emsdk/.gitignore` |
| `motw_test/` | 用来测 `unblock_package.ps1` 的临时 fixture（带 `Zone.Identifier` 的假 exe/dll） | ❌ 由 `mk_motw_test.ps1` 重建 |
| `*.py` / `*.ps1` | 派生脚本：策略检查、登记表改判、签名取证、fixture 生成、台账探针 | ✅ |

## 复现 A 段的四条命令（全部从 cmd 启动，**无 shell 重定向**）

```cmd
rem 0) 造 C# 被测工程（真游戏，不是骨架）
robocopy F:\moonbit-hof-rs\godot-mcp\projects\pong F:\moonbit-hof-rs\godot-mcp\recovery\work\task114\web_probe\cs_web_probe /E /XD .godot

rem 1) ② C# 工程 + .NET 编辑器  ->  被 .NET 闸门拒绝
cd /d F:\moonbit-hof-rs\godot-mcp
godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless ^
  --path recovery\work\task114\web_probe\cs_web_probe --export-release "Web" out\cs_web\index.html

rem 2) ③a 同一个 .NET 编辑器 + 纯 GDScript 工程  ->  逐字相同的拒绝（决定性对照）
godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless ^
  --path recovery\work\task114\web_probe\gd_web_probe --export-release "Web" out\gd_mono\index.html

rem 3) ③b 非 .NET 编辑器 + 同一个 GDScript 工程  ->  通过闸门，只报缺模板
godot\bin\godot.windows.editor.x86_64.console.exe --headless ^
  --path recovery\work\task114\web_probe\gd_web_probe --export-release "Web" out\gd_nomono\index.html

rem 4) ① 试建 Web 模板（没装 emsdk 时 / 装了 emsdk 后都试过）
cd /d F:\moonbit-hof-rs\godot-mcp\godot
scons platform=web target=template_release -j8
F:\moonbit-hof-rs\godot-mcp\recovery\work\task114\emsdk\env_task114.cmd scons platform=web target=template_release -j8
```

**逐字输出见 `recovery\reports\TASK-114-REPORT.md` §A。**

## emsdk 怎么来的（官方引导失败后的非破坏性绕过）

1. `git clone --depth 1 https://github.com/emscripten-core/emsdk.git`（成功）；
2. `emsdk install latest` / `python emsdk.py install latest` **连续 3 次失败**：
   `[WinError 5] 拒绝访问。` 出现在
   `unzip_temp\install\emscripten\test\test_other.py -> upstream\emscripten\test\test_other.py`
   这一步（清掉半成品重跑仍逐字相同）。第 1 次还叠加了
   `emsdk requires python 3.10 or above (D:\Anaconda\python.exe 3.9.7)`。
3. **绕过**：用 Python 3.13 的 `zipfile` 把同一个 `downloads\…-wasm-binaries.zip`
   展开到 `upstream_stage`，`robocopy upstream_stage\install upstream /E /MOVE`
   就位成规范布局，再手写 `.emscripten` 与 `env_task114.cmd`。
4. 结果：`emcc --version` → `6.0.10-git (d6c521a7f05449857c76bd99e396895583cf2083)`；
   `em++ emcc_smoke.cpp -o emcc_smoke.js` → **exit 0**。
5. **仍未解决的**：`scons platform=web target=template_release -j8`（带 emcc）在
   `Compiling platform\web\*.cpp` 阶段以 12–13 个 libc++ 头文件搜索顺序错误失败。
   这不是 A 段结论的依赖项（闸门在模板检查**之前**就 `return false`）。

## 清理

`emsdk/`（约 1.5 GB）与 `web_probe/cs_web_probe/`、`motw_test/` 都可以直接删除，
不会影响任何入库内容：

```cmd
rmdir /s /q F:\moonbit-hof-rs\godot-mcp\recovery\work\task114\emsdk
rmdir /s /q F:\moonbit-hof-rs\godot-mcp\recovery\work\task114\motw_test
```
