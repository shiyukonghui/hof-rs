# TASK-115 —— 可复现清单

本目录只放**派生脚本**；它们跑出来的东西（导出的 exe/pck、逐字日志、缓存）都在
`.gitignore` 里，需要时整体删除 `export_probe/` 与 `logs/` 即可。

## 1. 台账与登记表（幂等，随时可重跑）

```cmd
cd /d F:\moonbit-hof-rs\godot-mcp
python tools\tool_coverage.py
python recovery\work\task115\reclassify_h7.py        :: 跑两遍验证幂等
python recovery\work\task115\report_numbers.py       :: 报告里引用的逐行数字
```

## 2. 四个批次会话（每次约 1–3 分钟，跑前先查端口与进程）

```cmd
cd /d F:\moonbit-hof-rs\godot-mcp
set RUN=powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_game_session.ps1
%RUN% -Game "_exercises\ex_editor" -RunTag h7-task115  -EditorPort 9890 -GamePort 9891 -Session "tools\sessions\_exercises\ex_editor\h7-session.json"
%RUN% -Game "_exercises\ex_write5" -RunTag c4b-task115 -EditorPort 9892 -GamePort 9894 -Session "tools\sessions\_exercises\ex_write5\c4b-session.json"
%RUN% -Game "_exercises\ex_anim2"  -RunTag h2c-task115 -EditorPort 9893 -GamePort 9895 -Session "tools\sessions\_exercises\ex_anim2\h2c-session.json"
%RUN% -Game "_exercises\ex_3d"     -RunTag h1b2-task115 -EditorPort 9896 -GamePort 9897 -Session "tools\sessions\_exercises\ex_3d\h1b-session.json"
```

H1 的批次跑过两次：第一次（`h1b-task115`）的两条 `editor_execute_gdscript` 见证
用了 `get_child(0)`，而 `CamHost` / `LightHost` 下先被塞进的是 N3 / N5 两个
`MeshInstance3D`，所以读到的是错的类（`C:MeshInstance3D` / `L:MeshInstance3D`）。
会话已改成按名字寻址（`get_node("Camera3D")` / `get_node("DirectionalLight3D")`），
**TASK-115 的权威 H1 运算是 `h1b2-task115`**，登记与声明都指向它。
第一次那个 run 保留在 `runs/` 里（`runs/` 不入库），作为「见证读本身写错也会被抓出来」的留证。

## 3. 会话文件与清单的关系

* `<batch>-session.json`  —— `run_game_session.ps1` 回放的东西（含 `sleep_ms`）。
* `<batch>-manifest.json` —— 由 `mk_manifests.py` 从会话生成 `calls[]`，外加**手写**的
  `readback[]`（工具、见证工具、run、`why`、`expect`、必要时 `expect_absent`）。
  `tools/tool_coverage.py` 只读 `readback`，并且会回到那个 run 的 trace 里把见证调用
  再找一次、在其回包里逐字搜 `expect` —— 搜不到就不给档位。

## 4. 导出与签名探针

```cmd
cd /d F:\moonbit-hof-rs\godot-mcp
powershell -NoProfile -ExecutionPolicy Bypass -File recovery\work\task115\probe_export.ps1
```

* 逐字输出：`logs\probe-report.txt`（每个引擎调用另有 `logs\<name>.stdout/stderr.txt`）。
* 它**不下载任何东西**；官方 4.7.1-stable mono 模板不在本机时，① 只报 `exists=False`。
* 它**有界**：导出的游戏找不到 `.pck` 时引擎会弹**模态对话框**，`Start-Process -Wait`
  永不返回，所以游戏运行一律走 `Run-CmdFileBounded`（超时即 `taskkill /T /F` 并记 `TIMEOUT(ns)`）。
* 预设：`projects\_exercises\ex_editor\export_presets.cfg`
  —— preset.0 `embed_pck=false`（默认改写 PE）、preset.1 `embed_pck=true`、
  preset.2 `embed_pck=false` + `modify_resources=false`（**唯一与模板逐字节相同的那一份**）。

## 5. PNG fixture

```cmd
python recovery\work\task115\mk_png_fixtures.py
```

写 `projects\_exercises\ex_editor\assets\{a.png,b.png,c16.png}`（8×8、8×8、16×16），
手写 PNG 编码器，无第三方依赖。
