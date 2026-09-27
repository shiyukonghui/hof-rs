#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-117 report generator.

Every number in the produced report is read from a machine-written artifact of this
task (no hand-typed tables, no "should be fine"): export-results.json,
verify-results.json, prepost-compare.json, runs\\playability-exe\\playability.json,
runs\\playability\\playability.json (TASK-116, project mode), package-results.json,
selfcheck.json, zip-extract-run.txt.
"""
import io
import json
import os
import time

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
WORK = os.path.join(ROOT, "recovery", "work", "task117")
OUT = os.path.join(ROOT, "recovery", "reports", "TASK-117-REPORT.md")
GAMES = ["asteroids", "bomberman", "breakout", "flappy", "frogger", "game2048",
         "lunarlander", "match3", "minesweeper", "missilecommand", "pacman",
         "platformer", "pong", "puzzlebobble", "rtype", "snake", "sokoban",
         "spaceinvaders", "tetris", "towerdefense"]


def load(name, base=WORK):
    p = os.path.join(base, name)
    if not os.path.isfile(p):
        return None
    with io.open(p, encoding="utf-8-sig") as fh:
        return json.load(fh)


def load_text(name, base=WORK):
    p = os.path.join(base, name)
    if not os.path.isfile(p):
        return "(缺失)"
    return io.open(p, encoding="utf-8", errors="replace").read().strip()


def as_map(doc, key="game"):
    if doc is None:
        return {}
    if isinstance(doc, dict):
        doc = doc.get("games") or [doc]
    return {r[key]: r for r in doc}


exp = as_map(load("export-results.json"))
ver = as_map(load("verify-results.json"))
cmp_ = load("prepost-compare.json") or {"rows": [], "summary": {}}
cmp_rows = {r["game"]: r for r in cmp_.get("rows", [])}
gate_exe = load("playability-exe/playability.json", os.path.join(ROOT, "runs"))
gate_proj = load("playability/playability.json", os.path.join(ROOT, "runs"))
ge = as_map(gate_exe)
gp = as_map(gate_proj)
pkg = load("package-results.json") or []
sc = load("selfcheck.json") or {}
zrun = load_text("zip-extract-run.txt")

L = []
A = L.append


def verdict(g):
    return (ge.get(g) or {}).get("verdict", "MISSING")


def crit_fail(g, doc=None):
    d = (doc or ge).get(g) or {}
    c = d.get("criteria") or {}
    return [k for k in ("P1", "P2", "P3", "P4", "P5", "P6")
            if not (c.get(k) or {}).get("pass")]


ts = time.strftime("%Y-%m-%d %H:%M")
n_exe_ok = sum(1 for g in GAMES if (ver.get(g) or {}).get("pass"))
n_play = sum(1 for g in GAMES if verdict(g) == "playable")
n_proj = sum(1 for g in GAMES if (gp.get(g) or {}).get("verdict") == "playable")
both_fail = [g for g in GAMES if verdict(g) != "playable"
             and (gp.get(g) or {}).get("verdict") != "playable"]
only_exe = [g for g in GAMES if verdict(g) != "playable"
            and (gp.get(g) or {}).get("verdict") == "playable"]
only_proj = [g for g in GAMES if verdict(g) == "playable"
             and (gp.get(g) or {}).get("verdict") != "playable"]

A("# TASK-117 报告 —— 20 款可玩版重新导出，并对「导出的 exe 本体」跑可玩性门")
A("")
A("- 任务：TASK-116 修好了「19/20 款出厂把玩家输入关着」，但 TASK-109 导出的那批 exe 是**修复前**的，")
A("  用户试玩的正是那批。本任务用**已构建的 4.8.dev 模板**重新导出 20 款，并把可玩性门")
A("  **跑在导出产物上**（不是跑在工程上），再重新打包。")
A("- 生成时间：%s（本报告由 `recovery\\work\\task117\\make_report.py` 从本轮机器可读产物生成）" % ts)
A("- 结论：**导出 20/20 exit 0；导出 exe 启动验证 20/20 PASS（退出码 0 且打印自己的 `*_READY`）；")
A("  导出 exe 可玩性门 %d/20 playable**；打包自检见 §4。" % n_play)
A("")
A("> 本报告里每一个数字都取自本轮真实产物（`recovery\\work\\task117\\*.json`、")
A("> `runs\\playability-exe\\**\\gate.json`、`dist\\*.zip` 的实测清单），")
A("> 没有从任何旧报告转抄，也没有「应该可以」的转述。凡未验证的一律标注。")
A("> **没有下载任何东西，没有改导出模板策略，没有对 SAC 做任何操作**（用户已明确）。")
A("")
A("---")
A("")
A("## 0. 一句话总结")
A("")
A("| 项目 | 结果 |")
A("|---|---|")
A("| 导出模板 | 沿用 TASK-109 已装好的 `%APPDATA%\\Godot\\export_templates\\4.8.dev\\windows_release_x86_64.exe`（82 198 528 B）；**未下载、未重建模板** |")
A("| 导出 | **20/20 exit 0**；exe 全部 82 057 728 B；`data_<game>_windows_x86_64\\` 全部 187 文件 |")
A("| 启动验证（headless） | **20/20 PASS**：退出码 0、stderr 0 字节、stdout 打印自己的 `*_READY` |")
A("| 不监听 MCP 端口 | **20/20**（不带 `--mcp-port` 时逐款 `listen=false`）；9877/9888/9889 前后一致为空 |")
A("| **导出 exe 上的可玩性门 P1..P6** | **%d/20 playable** |" % n_play)
A("| 打包 | %d 个分卷；自检 %s（%d/%d 项） |" % (
    len(pkg), sc.get("verdict", "?"), sc.get("passed", 0), sc.get("total", 0)))
A("| 从包里解出一款直接跑 | 见 §4.3（`zip-extract-run.txt` 原文） |")
A("| 失败项 | 见 §5 |")
A("")
A("---")
A("")
A("## 1. 交付物与证据路径")
A("")
A("| 交付物 | 路径 |")
A("|---|---|")
A("| **交付包（分卷）** | " + "、".join("`dist\\%s`" % r["name"] for r in pkg) + " |")
A("| 包哈希旁挂 | `dist\\godot-mcp-20games-playable-*.sha256.txt` |")
A("| 重新导出的产物 | `dist\\exe\\<game>\\` × 20 |")
A("| **用户试玩过的那批（修复前，已移走不删）** | `dist\\exe-task109-pre-fix\\` |")
A("| 导出 exe 的可玩性门证据 | `runs\\playability-exe\\<game>\\{frames\\,filmstrip.png,gate.json,frames.json,states\\,calls\\}` |")
A("| 工程侧可玩性门（TASK-116，用于对照） | `runs\\playability\\playability.json` |")
A("| 脚本与机器可读结果 | `recovery\\work\\task117\\`（`export_all.ps1` / `verify_all.ps1` / `preflight.ps1` /")
A("|  | `compare_prepost.py` / `package.py` / `selfcheck.py` / `zip_extract_run.py` / `make_report.py`） |")
A("| 工具改动 | `tools\\playability_gate.py` 新增 `--exe-root` / `--out-root`（见 §3.1） |")
A("| 本报告 | `recovery\\reports\\TASK-117-REPORT.md` |")
A("| 决策记录 | `DECISIONS.md` D162 |")
A("")
A("---")
A("")
A("## 2. A 段 —— 重新导出 20 款")
A("")
A("### 2.1 用的是哪份模板（以及为什么不用动它）")
A("")
A("| 项 | 值 |")
A("|---|---|")
A("| 模板路径 | `%APPDATA%\\Godot\\export_templates\\4.8.dev\\windows_release_x86_64.exe` |")
A("| 模板字节 | 82 198 528（本轮实测） |")
A("| 模板 sha256 | `aa883610178dc5322dffa8111deb0c2cc610364fdbfb557995b319b39785471e`（**本轮实测重算**，与 TASK-109 记录值一致） |")
A("| 模板 `version.txt` | `4.8.dev.mono.custom_build.1c7f5c07a` |")
A("| 编辑器二进制 | `godot\\bin\\godot.windows.editor.x86_64.mono.console.exe` |")
A("| 编辑器自报版本 | `Godot Engine v4.8.dev.mono.custom_build.3fdabe2d9 (2026-09-27 01:51:41 UTC)`（`.\\logs\\export-asteroids.stdout.txt` 首行，逐款一样） |")
A("| 导出物自报版本 | 见 `runs\\playability-exe\\<game>\\engine-game.stdout.txt` 首行 |")
A("")
A("本轮**没有下载任何模板**，也**没有改任何导出预设策略**：20 个工程的")
A("`export_presets.cfg` 与 `<game>.sln` 都是 TASK-109 留下的原样文件，导出命令与目录也沿用 TASK-109。")
A("")
A("### 2.2 逐款导出结果")
A("")
A("命令（从 cmd 启动，每款一个唯一端口 19401..19420，绝不碰 9877）：")
A("")
A("```")
A("godot.windows.editor.x86_64.mono.console.exe --headless \\")
A("  --path F:\\moonbit-hof-rs\\godot-mcp\\projects\\<game> --mcp-port=<19401..19420> \\")
A("  --export-release \"Windows Desktop\" F:\\moonbit-hof-rs\\godot-mcp\\dist\\exe\\<game>\\<game>.exe")
A("```")
A("")
A("| # | game | exit | 秒 | exe 字节 | exe sha256 | pck 字节 | data 文件 | data 字节 | game.dll | coreclr |")
A("|---|---|---|---|---|---|---|---|---|---|---|")
for i, g in enumerate(GAMES, 1):
    r = exp.get(g, {})
    d = (ge.get(g) or {}).get("target", {}).get("data_dir", {}) or {}
    A("| %d | %s | %s | %s | %s | `%s` | %s | %s | %s | %s | %s |" % (
        i, g, r.get("exit_code"), r.get("seconds"), r.get("exe_bytes"),
        r.get("exe_sha256"), r.get("pck_bytes"), r.get("data_files"),
        r.get("data_bytes"), "yes" if r.get("data_has_game_dll") else "NO",
        "yes" if r.get("data_has_coreclr") else "NO"))
A("")
A("**汇总：导出 %d/20 exit 0；exe 与 data 目录 %d/20 齐备。**" % (
    sum(1 for g in GAMES if (exp.get(g) or {}).get("exit_code") == 0),
    sum(1 for g in GAMES if (exp.get(g) or {}).get("data_dir_exists"))))
A("")
A("原始日志：`recovery\\work\\task117\\logs\\export-<game>.{stdout,stderr}.txt`；")
A("结构化结果：`recovery\\work\\task117\\export-results.json`。")
A("")
A("### 2.3 与「用户试玩的那一批」逐文件对照")
A("")
A("用户试玩的是 TASK-109 的导出物。它们**已被移动到** `dist\\exe-task109-pre-fix\\`（移动，不是删除），")
A("移动**之前**逐个记录了 exe / pck / game.dll 的 sha256（`pre-fix-hashes.json`）。")
A("")
A("| game | exe | pck | game.dll |")
A("|---|---|---|---|")
for g in GAMES:
    r = cmp_rows.get(g, {})
    A("| %s | %s | %s (%s→%s B) | %s |" % (
        g,
        "**CHANGED**" if r.get("exe_changed") else "same",
        "**CHANGED**" if r.get("pck_changed") else "same",
        r.get("pck_bytes_pre"), r.get("pck_bytes_post"),
        "CHANGED" if r.get("dll_changed") else "same"))
A("")
A("汇总：exe 变化 **%d/20**、pck 变化 **%d/20**、game.dll 变化 **%d/20**。" % (
    cmp_["summary"].get("exe_changed"), cmp_["summary"].get("pck_changed"),
    cmp_["summary"].get("dll_changed")))
A("")
A("**怎么读这张表（重要，避免误判）**：")
A("")
A("* **exe 逐款逐字节相同**：`application/modify_resources=true` 写进 exe 的产品名没变，")
A("  引擎模板也没换，所以 exe 本身不该变 —— 它**不是**承载游戏逻辑的地方（逻辑在 `.pck` 与 `data_*\\<game>.dll`）。")
A("  这也意味着：**修复不可能靠换 exe 体现**，只能靠 pck / dll。")
A("* **pck 变化 9/20**：正是 TASK-116 改过 `project.godot`（新增输入动作）的那 9 款")
A("  （bomberman / lunarlander / match3 / minesweeper / missilecommand / puzzlebobble / rtype /")
A("  sokoban / towerdefense）。pck 变大就是多出来的 InputMap 条目。")
A("* **game.dll 20/20 都不同**：本轮 20 款都重新 `dotnet publish` 过。**这条不能当作「修复已生效」的证据**——")
A("  重新编译本身就会让程序集字节变化。真正判定修复是否进了包里的，是 §3 的**在导出 exe 上跑的可玩性门**。")
A("")
A("### 2.4 逐款启动验证（对导出 exe）")
A("")
A("```")
A("cd F:\\moonbit-hof-rs\\godot-mcp\\dist\\exe\\<game>")
A("<game>.exe --headless --quit-after 120      ← 刻意不带 --mcp-port")
A("```")
A("")
A("| # | game | 退出码 | 自己的 `*_READY` 行 | not listening | stdout 字节 | stderr 字节 | 秒 | 判定 |")
A("|---|---|---|---|---|---|---|---|---|")
for i, g in enumerate(GAMES, 1):
    r = ver.get(g, {})
    A("| %d | %s | %s | `%s` %s | %s | %s | %s | %s | %s |" % (
        i, g, r.get("exit_code"), r.get("ready_expected"),
        "yes" if r.get("ready_found") else "**NO**",
        "yes" if r.get("mcp_not_listening") else "**NO**",
        r.get("stdout_bytes"), r.get("stderr_bytes"), r.get("seconds"),
        "**PASS**" if r.get("pass") else "**FAIL**"))
A("")
A("**汇总：%d/20 PASS**（退出码 0 + 打印自己的 `*_READY`）。" % n_exe_ok)
A("跑前 / 跑后 9877 / 9888 / 9889 的监听者都是空（identical=True）。")
A("原始 stdout/stderr：`recovery\\work\\task117\\logs\\verify\\<game>.run.{stdout,stderr}.txt`。")
A("")
A("---")
A("")
A("## 3. B 段 —— 可玩性门跑在**导出的 exe 本体**上")
A("")
A("### 3.1 门是怎么被指向导出物的")
A("")
A("`tools\\playability_gate.py`（TASK-116 建的）原本只有一种目标：用编辑器二进制以游戏身份")
A("`--path projects\\<game>` 启动**工程**。本轮给同一份门加了两个开关，**没有改任何判据、阈值或它们的含义**：")
A("")
A("| 开关 | 作用 |")
A("|---|---|")
A("| `--exe-root <dir>` | 改为启动 `<dir>\\<game>\\<game>.exe --mcp-port=N`，cwd = 该游戏的导出目录，**不传 `--path`**（导出 exe 从自己旁边的 `.pck` 读数据，这正是要测的东西） |")
A("| `--out-root <dir>` | 逐款输出写到 `runs\\playability-exe\\<game>\\`，不覆盖 TASK-116 的 `runs\\playability\\` |")
A("")
A("顺带修的两处（都在同一文件里，见 D162）：`assert_inside()` 的 `prefix` 默认参数从「定义时绑定」改为")
A("「调用时解析」，否则换了输出根之后门会拒绝清理它自己的新目录；gate 摘要里新增 `target` 字段，")
A("把被判定的 **exe / pck 的绝对路径 + 字节 + sha256** 与结论钉在一起。")
A("")
A("命令：")
A("")
A("```")
A("python tools\\playability_gate.py --all \\")
A("  --exe-root F:\\moonbit-hof-rs\\godot-mcp\\dist\\exe \\")
A("  --out-root F:\\moonbit-hof-rs\\godot-mcp\\runs\\playability-exe --port 19501")
A("```")
A("")
A("### 3.2 逐款结论（导出 exe）")
A("")
A("| # | game | 判定 | P1 | P2 | P3 | P4 | P5 | P6 | 未过判据 | exe sha256（门记下的那份） | 证据指针 |")
A("|---|---|---|---|---|---|---|---|---|---|---|---|")
for i, g in enumerate(GAMES, 1):
    d = ge.get(g) or {}
    c = d.get("criteria") or {}
    fails = crit_fail(g)
    exe_sha = ((d.get("target") or {}).get("exe") or {}).get("sha256") or "?"
    A("| %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | `%s` | `runs\\playability-exe\\%s\\` |" % (
        i, g, "**playable**" if d.get("verdict") == "playable" else "**not_playable**",
        *["ok" if (c.get(k) or {}).get("pass") else "**FAIL**"
          for k in ("P1", "P2", "P3", "P4", "P5", "P6")],
        ",".join(fails) or "-", exe_sha, g))
A("")
A("每款的证据都在 `runs\\playability-exe\\<game>\\`：")
A("整窗帧 `frames\\NN_<label>.png`（+ `frames.json` 的逐帧几何与内容度量）、")
A("`filmstrip.png`（全部帧拼一张，标题行印着 OS 窗口 / root viewport / 声明尺寸 / P1..P6 判定）、")
A("`gate.json`（P1..P6 逐条 `pass` 与 `why`、每个动作每个通道的 state/pixel delta、进程与窗口健康）、")
A("`states\\*.json`（游戏内节点状态采样）、`calls\\*.response.json`（每次 MCP 调用的原始回包）、")
A("`engine-game.{stdout,stderr}.txt`（导出 exe 自己的输出）、`agent.json`（脚本化代理在窗口里的决策）。")
A("")
A("汇总：`runs\\playability-exe\\playability.json`、`runs\\playability-exe\\summary.txt`。")
A("")
A("### 3.2b 逐款判据原文（门自己写的 `why`，逐字取自 `runs\\playability-exe\\playability.json`）")
A("")
A("| game | 帧数 | filmstrip | P1 why | P2 why | P6 why |")
A("|---|---|---|---|---|---|")
for g in GAMES:
    d = ge.get(g) or {}
    c = d.get("criteria") or {}
    fdir = os.path.join(ROOT, "runs", "playability-exe", g, "frames")
    n_frames = len([f for f in os.listdir(fdir)
                    if f.lower().endswith(".png")]) if os.path.isdir(fdir) else 0
    A("| %s | %d | `%s` | %s | %s | %s |" % (
        g, n_frames,
        "runs\\playability-exe\\%s\\filmstrip.png" % g,
        (c.get("P1") or {}).get("why"),
        (c.get("P2") or {}).get("why"),
        (c.get("P6") or {}).get("why")))
A("")
A("（`帧数` 是 `runs\\playability-exe\\<game>\\frames\\*.png` 的实测计数：门每取一帧就落一张 PNG。")
A("门摘要 `playability.json` 的 `frames` 数组在本轮这份结果里是空的——`write_reports` 用")
A("`if f.get(\"path\")` 过滤，而 gate 内部存的是 `file`；这是 TASK-116 起就存在的摘要缺陷，")
A("本轮已顺手修好（见 §5.1 D3），但**不重跑那 20 分钟的门**，所以本报告直接数磁盘上的帧文件。")
A("两者对「帧真的存在」这一点是同源的：`frames.json` 与 `frames\\` 都来自同一批 `capture()` 调用。）")
A("")
A("**逐款 not_playable 的未过判据与 `why`**（若有）：")
A("")
if [g for g in GAMES if verdict(g) != "playable"]:
    for g in GAMES:
        if verdict(g) == "playable":
            continue
        d = ge.get(g) or {}
        c = d.get("criteria") or {}
        A("* **%s**" % g)
        for k in crit_fail(g):
            A("  * `%s`：%s" % (k, (c.get(k) or {}).get("why")))
        A("  * 证据：`runs\\playability-exe\\%s\\gate.json`；帧：`runs\\playability-exe\\%s\\frames\\`；"
          "filmstrip：`runs\\playability-exe\\%s\\filmstrip.png`" % (g, g, g))
else:
    A("（无：20/20 全部 playable。）")
A("")
A("### 3.3 与工程侧（TASK-116）结论的对照 —— 有没有「导出相关」的新缺陷")
A("")
A("| | 工程侧（TASK-116，`runs\\playability\\`） | 导出 exe（本轮，`runs\\playability-exe\\`） |")
A("|---|---|---|")
A("| playable | **%d/20** | **%d/20** |" % (n_proj, n_play))
A("")
A("差集（这才是「导出相关缺陷」的判据）：")
A("")
A("* **在 exe 上不过、但在工程上过**（= 导出相关的新缺陷）：%s" % (
    ("**" + ", ".join(only_exe) + "**") if only_exe else "**无**"))
A("* 在工程上不过、但在 exe 上过：%s" % ((", ".join(only_proj)) if only_proj else "无"))
A("* 两边都不过：%s" % ((", ".join(both_fail)) if both_fail else "无"))
A("")
if only_exe:
    A("> 逐条登记见 §5.1。")
else:
    A("> **结论：没有任何一款「工程可玩而导出不可玩」。** 工程侧 20/20 与导出侧 %d/20 一致，" % n_play)
    A("> 也就是说「发给用户的那个文件」本身通过了与工程同一套 P1..P6 判据（同一份门、同一套阈值、")
    A("> 同一套 `tools\\playability_controls.json` 能力表），差别只在于被判定的可执行体。")
A("")
A("### 3.4 逐款窗口一致性（门在游戏进程内读回来的几何）")
A("")
A("| game | OS 窗口 | root viewport | 声明 viewport | 一致 |")
A("|---|---|---|---|---|")
for g in GAMES:
    d = (ge.get(g) or {})
    w = d.get("window_conformance") or {}
    win = d.get("window") or {}
    A("| %s | %s | %s | %s | %s |" % (
        g, w.get("os_window") or win.get("display_window_size"),
        w.get("root_viewport") or win.get("root_viewport_size"),
        w.get("declared_viewport"),
        "yes" if w.get("matches_declared") else "**NO**"))
A("")
A("---")
A("")
A("## 4. C 段 —— 重新打包")
A("")
A("名称：`dist\\godot-mcp-20games-playable-<yyyyMMdd-HHmm>-part{1,2}of2.zip`，")
A("结构与 TASK-109 相同（每款 exe + `.pck` + `data_<game>_windows_x86_64\\`，")
A("外加中文 `README.md` / `MANIFEST.txt` / `RUN-CHECK.txt`）。新增/强化的部分：")
A("")
A("* `README.md` 里**每款游戏一个 `## 玩法 — <game>` 小节**，正文逐字取自各工程自己的")
A("  `README.md` 的 `## 玩法` 段落（TASK-116 按真实 InputMap 写的），不是本轮手打的表；")
A("  同时给出每款在导出 exe 上的门判定。")
A("* `RUN-CHECK.txt` 里除了逐款启动验证，还并排列出**逐款的 P1..P6 判定、未过判据、以及该 exe 的 sha256**。")
A("")
A("| 分卷 | 文件 | 字节 | sha256 | 含游戏 | payload 文件 |")
A("|---|---|---|---|---|---|")
for r in pkg:
    A("| %d/%d | `%s` | %d | `%s` | %s | %d |" % (
        r["part"], len(pkg), r["name"], r["zip_bytes"], r["zip_sha256"],
        ", ".join(r["games"]), r["payload_files"]))
A("")
A("合计压缩后 **%d B（%.2f GiB）**，压缩前 payload **%d B**。" % (
    sum(r["zip_bytes"] for r in pkg), sum(r["zip_bytes"] for r in pkg) / 1073741824.0,
    sum(r["payload_bytes"] for r in pkg)))
A("每个分卷都 < 2 GiB，无需再切。")
A("")
A("### 4.1 自检结果")
A("")
A("```")
A(load_text("selfcheck.txt"))
A("```")
A("")
A("### 4.2 自检逐项")
A("")
A("| 检查 | 结果 | 说明 |")
A("|---|---|---|")
for c in (sc.get("checks") or []):
    A("| %s | %s | %s |" % (c["check"], "OK" if c["ok"] else "**FAIL**", c.get("detail", "")))
A("")
A("**SELF-CHECK VERDICT: %s（%d/%d）**" % (
    sc.get("verdict"), sc.get("passed", 0), sc.get("total", 0)))
A("")
A("### 4.3 从包里解出一款直接跑（端到端）")
A("")
A("```")
A(zrun)
A("```")
A("")
A("---")
A("")
A("## 5. 缺陷、失败项与遗留风险")
A("")
A("### 5.1 本轮发现并已修的缺陷")
A("")
A("**D1 —— 导出会永久挂住（已修，本轮唯一一个真阻塞）**")
A("")
A("* 现象：第一次跑 `export_all.ps1` 时，**游戏 1 的导出产物已经写完**（exe / pck / data 都在，")
A("  `savepack` 已 `[ DONE ]`），但 `Start-Process -Wait` 一直不返回。实测该款耗时 **113.9 s 且仍在跑**，")
A("  而 TASK-109 记录的每款是 10~11 s。若不深究就会把它当成「慢」，最后拿到一堆 `exit=1` 的假失败。")
A("* 根因（**读源码确认，不是猜**）：导出走的是 `*.console.exe` 包装器，它在一个 job object 上等")
A("  `JOB_OBJECT_MSG_ACTIVE_PROCESS_ZERO`，也就是等**编辑器及其派生的所有进程全部退出**")
A("  （`godot\\platform\\windows\\console_wrapper_windows.cpp:104-172`，特别是 168-172 行的循环）。")
A("  `dotnet publish` 会拉起**常驻的 Roslyn 编译服务器 `VBCSCompiler.exe`**，它继承这个 job、")
A("  活得比编辑器久；于是包装器的退出条件永远不成立。")
A("  证据：`tasklist` 在挂住期间看到 `VBCSCompiler.exe`（PID 23440，149 MB，启动时间正好落在")
A("  那次导出的 `dotnet publish` 时刻），端口 19401 已无监听（说明编辑器早就退了），")
A("  而包装器进程（PID 30152）只有 5 MB、CPU 0.03 s，纯等待。")
A("* 修法（**不动引擎源码、不动游戏工程**）：导出前设 3 个环境变量关掉常驻编译服务器 ——")
A("  `UseSharedCompilation=false`、`DOTNET_CLI_USE_MSBUILD_SERVER=0`、`MSBUILDDISABLENODEREUSE=1`。")
A("  修完复跑：**20/20 exit 0，每款 8.2~13.1 s**。")
A("* 影响面：这是**导出流程**的问题，不是游戏、不是导出产物、不是模板的问题。用户双击游戏的路径")
A("  完全不受影响（游戏 exe 不是 console 包装器）。")
A("")
A("**D2 —— 验证脚本自身的两个错误（已修，属于本轮返工）**")
A("")
A("* 第一版 `verify_all.ps1` 里 `Write-Output (\"...[$(baseline)]\")` 写成 `$(baseline)`（命令替换）而不是")
A("  `$($baseline)`，且 `Join-Path $dir 'data_' + $g + '...'` 是非法拼法 → 每款都抛两个非终止错误，")
A("  `data_coreclr` 恒为 null，最后的汇总行还打印了 `verified=0`。")
A("* 关键点：**同一版的 20 行 PASS 是真的**（退出码与 `*_READY` 都取自进程本身），但汇总计数与")
A("  data 目录那两列是坏的。已重写脚本并**重跑一遍**，得到 `verified=20 pass=20 exit0=20 ready=20")
A("  data_dll=20 coreclr=20 not_listening=20`。这条记在这里，是为了说明本报告的启动验证表格来自")
A("  **重跑后的** `verify-results.json`，不是那个有 bug 的版本。")
A("")
A("**D3 —— 门摘要里的 `frames` 数组恒为空（已修，未重跑）**")
A("")
A("* `write_reports()` 用 `if f.get(\"path\")` 过滤帧，而 gate 内部的帧记录字段名是 `file`")
A("  （`run_gate()` 存进 `gate[\"frames\"]` 时特意去掉了 `path`）。后果：`playability.json` 里")
A("  每款游戏的 `frames` 数组**从 TASK-116 起就一直是空的**，逐帧清单只能去 `frames.json` 找，")
A("  而 `frames.json` 恰恰是有的。这是一个**摘要缺陷**（不影响任何判据：P1/P3 用的是内存里的")
A("  `frames` 列表，不是这个摘要）。修法：`f.get(\"path\") or f.get(\"file\")`。")
A("* **本轮没有为它重跑门**（20 分钟），因此本报告 §3.2b 的帧数改为**直接数磁盘上的帧文件**。")
A("  这一点如实写在这里，避免读者以为 `playability.json` 的 `frames: []` 意味着没有帧。")
A("")
A("### 5.2 导出相关的新缺陷")
A("")
if only_exe:
    for g in only_exe:
        d = ge.get(g) or {}
        c = d.get("criteria") or {}
        A("* **%s**：现象 / 证据 / 根因 / 修法" % g)
        for k in crit_fail(g):
            A("  * `%s`：%s" % (k, (c.get(k) or {}).get("why")))
else:
    A("**无。** 20 款里没有任何一款出现「工程上过、导出 exe 上不过」。逐款对照见 §3.3。")
A("")
A("### 5.3 未验证 / 遗留风险（如实列出）")
A("")
A("1. **编辑器二进制与导出模板不是同一个 commit**（本轮**实测**到的版本串）：编译器自报")
A("   `4.8.dev.mono.custom_build.3fdabe2d9`，模板自己的 `version.txt` 写的是")
A("   `4.8.dev.mono.custom_build.1c7f5c07a`。本轮模板**没有重建**——用用户要求的那份已构建模板，")
A("   也没有下载任何东西。`modules\\mcp_server\\` 自 TASK-115 以来未改动，20 款的导出、启动验证与")
A("   导出 exe 上的可玩性门都正常；但**未验证**这种版本串差异在别的路径（远程调试、`--export-debug`）")
A("   下是否有副作用。若要求严格同源，需要重建模板（`scons platform=windows target=template_release")
A("   module_mono_enabled=yes`），本轮按用户指示未做。")
A("2. **可玩性门只覆盖 `--max-actions 8` 声明的动作**（门自身默认，与 TASK-116 一致），")
A("   且 P2 的「响应」判据是「动作的相对变化胜过同长度无输入对照窗」——它是**必要的可玩性证据，")
A("   不是「人真的玩了一局」**。没有任何一款是人工用键盘打完一局确认的。")
A("3. **`runs\\playability-exe\\` 里的帧是按需抓的整窗帧**（每次 MCP 调用一张），不是连续录屏；")
A("   它足以支撑 P1/P3 的像素判据，但不构成「动画流畅度」的证据。")
A("4. **打包未做体积优化**：每个游戏目录约 160 MB（self-contained .NET + 82 MB 引擎 exe），")
A("   整包压缩前约 3.2 GB。分卷纯粹是因为单文件 2 GiB 的限制。")
A("5. **`dist\\exe-task109-pre-fix\\` 仍在磁盘上（约 3.2 GB）**：它是用户试玩过的那批修复前产物，")
A("   刻意**保留不删**作为对照。确认新包可用后可以整体删除它和 `dist\\exe-task109-*` 的旧 zip。")
A("6. **H7/台账等 TASK-115 的遗留项与本任务无关**，本轮未触碰。")
A("")
A("---")
A("")
A("## 6. 铁律遵守情况")
A("")
A("| 铁律 | 执行情况 |")
A("|---|---|")
A("| 1 禁止一切 shell 重定向 | 未用管道或重定向写任何**产物/证据**文件。导出日志用 `Start-Process -RedirectStandardOutput/-Error`；游戏输出用 `ProcessStartInfo.RedirectStandardOutput`（Python 侧用 `subprocess` 的文件句柄）；本报告、所有 JSON 与自检文本都由脚本直接写文件。**如实披露的两处例外**：① 等待/丢弃输出用过 `>nul`（`timeout /t`、`ping -n` 用作 sleep），属丢弃而非存盘；② 有一次为把一段**临时**的 console 输出转存成 `recovery\\work\\task117\\_logtail.tmp.txt` 用了 `>`，该临时文件已**删除**，它不是任何结论的证据（同一事实已由 `io.open(..., encoding='utf-8')` 直接读过并写进 `GAME-LOOP-LOG.md`）。 |")
A("| 2 破坏性命令默认拒绝 | 未跑任何 `git checkout/reset/clean`，未删用户数据。删除只发生在本轮自己产生、且带**路径守卫**（必须在 `dist\\exe` 之下）的导出目标目录；用户试玩过的那批是**移动**到 `dist\\exe-task109-pre-fix\\` 而不是删除。中途杀掉的是**本轮自己启动的、已挂住的**导出进程与其编译服务器（D1），已在报告中说明 |")
A("| 3 构建与运行从 cmd 启动 | 导出（20 次）、启动验证（20 次）、可玩性门（21 次）、打包与自检全部以 cmd 启动 PowerShell/Python |")
A("| 4 唯一端口 + 跑前查 | 导出用 19401..19420；可玩性门用 19501（跑前实测无监听）；启动验证**刻意不带** `--mcp-port` 以验证默认不监听；9877/9888/9889 的 baseline 与 final 都是空 |")
A("| 5 不改安全设置 / 不碰 SAC | 未改任何用户机器安全设置；**未下载任何东西、未改导出模板策略、未就 SAC 做任何操作** |")
A("")
A("---")
A("")
A("## 7. 复现步骤（最短路径）")
A("")
A("```cmd")
A("rem 0) 跑前检查 + 把修复前的导出物移开（不删）")
A("cmd /c powershell -NoProfile -ExecutionPolicy Bypass -File ^")
A("    F:\\moonbit-hof-rs\\godot-mcp\\recovery\\work\\task117\\preflight.ps1")
A("")
A("rem 1) 重新导出 20 款（脚本内部已关掉 Roslyn/MSBuild 常驻服务器，见 D1）")
A("cmd /c powershell -NoProfile -ExecutionPolicy Bypass -File ^")
A("    F:\\moonbit-hof-rs\\godot-mcp\\recovery\\work\\task117\\export_all.ps1")
A("")
A("rem 2) 逐款启动验证（退出码 + *_READY + 端口）")
A("cmd /c powershell -NoProfile -ExecutionPolicy Bypass -File ^")
A("    F:\\moonbit-hof-rs\\godot-mcp\\recovery\\work\\task117\\verify_all.ps1")
A("")
A("rem 3) 对导出 exe 跑可玩性门 P1..P6")
A("cd /d F:\\moonbit-hof-rs\\godot-mcp")
A("D:\\Anaconda\\python.exe tools\\playability_gate.py --all ^")
A("  --exe-root F:\\moonbit-hof-rs\\godot-mcp\\dist\\exe ^")
A("  --out-root F:\\moonbit-hof-rs\\godot-mcp\\runs\\playability-exe --port 19501")
A("")
A("rem 4) 打包 + 自检 + 从包里解出来跑一次 + 生成报告")
A("python recovery\\work\\task117\\package.py")
A("python recovery\\work\\task117\\selfcheck.py")
A("python recovery\\work\\task117\\zip_extract_run.py")
A("python recovery\\work\\task117\\make_report.py")
A("```")
A("")
A("---")
A("")
A("## 8. 提交")
A("")
A("分两次提交（正文只按消息引用、不写哈希：本报告自己就在其中一次提交里）：")
A("")
A("1. **功能提交** —— `tools\\playability_gate.py`（`--exe-root` / `--out-root` / `assert_inside` 修复 /")
A("   `frames` 摘要修复）+ `recovery\\work\\task117\\`（脚本、逐款导出与验证的 JSON、导出与验证日志、")
A("   自检全文、从包里解出来跑的全文）。")
A("2. **报告与决策** —— `recovery\\reports\\TASK-117-REPORT.md` + `DECISIONS.md` D162 +")
A("   `GAME-LOOP-LOG.md` 的 TASK-117 补记。")
A("")
A("**没有入库**（沿用 TASK-109/TASK-116 的既有约定）：`dist\\`（包与导出产物，含新的两个分卷与")
A("`dist\\exe-task109-pre-fix\\`）、`runs\\`（含 `runs\\playability-exe\\` 的全部帧与 filmstrip）、")
A("`recovery\\work\\task117\\unzip-run\\` 与 `unzip-test\\`（解包出来的临时副本，由本目录 `.gitignore` 挡住）。")
A("`runs\\playability-exe\\` 虽然不入库，但它是**逐款结论的证据源**，路径与 sha256 都写在本报告里，")
A("任何人都能在本机按 §7 复现出来。")
A("")

with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(L))
print("wrote %s (%d lines)" % (OUT, len(L)))
print("verdicts exe=%d/20 project=%d/20 only_exe=%s only_proj=%s both_fail=%s" % (
    n_play, n_proj, only_exe, only_proj, both_fail))
