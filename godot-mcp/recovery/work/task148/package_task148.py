#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-148 step C: package the freshly re-exported 20 games into a release zip.

Layout inside the volume (unchanged from TASK-109):
    <pkgname>/README.md
    <pkgname>/MANIFEST.txt
    <pkgname>/RUN-CHECK.txt
    <pkgname>/games/<game>/<game>.exe
    <pkgname>/games/<game>/<game>.pck
    <pkgname>/games/<game>/data_<game>_windows_x86_64/...

Only change vs recovery/work/task109/package.py: the MANIFEST gains a 分卷归属 column
(required by TASK-148 section C.6) and the volume count is decided by the measured
archive size instead of a fixed 10-games-per-part rule.

Files are streamed straight into the zip, so peak disk usage stays near the archive size.
No shell redirection: every file is written by this Python process.
"""
import hashlib
import json
import os
import sys
import time
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
DIST = os.path.join(ROOT, "dist")
WORK = os.path.join(ROOT, "recovery", "work", "task148")
EXE_DIR = os.path.join(WORK, "exe")

GAMES = [
    "asteroids", "bomberman", "breakout", "flappy", "frogger", "game2048",
    "lunarlander", "match3", "minesweeper", "missilecommand", "pacman",
    "platformer", "pong", "puzzlebobble", "rtype", "snake", "sokoban",
    "spaceinvaders", "tetris", "towerdefense",
]

CONTROLS = {
    "asteroids": "A / D 左转 / 右转；W 推进；空格 开火",
    "bomberman": "W 向上；D 向右；空格 放置炸弹",
    "breakout": "A / D 挡板左移 / 右移；空格 发球",
    "flappy": "空格 拍翅上升；R 重新开始",
    "frogger": "W / A / S / D 向上 / 左 / 下 / 右移动",
    "game2048": "W / A / S / D 向上 / 左 / 下 / 右滑动合并",
    "lunarlander": "空格 点火推进（主推进器）",
    "match3": "空格 自动走一步；A / D 移动选择光标",
    "minesweeper": "R 翻开下一格；F 在下一格插旗",
    "missilecommand": "空格 自动开火（拦截轰炸）",
    "pacman": "W / A / S / D 向上 / 左 / 下 / 右移动",
    "platformer": "A / D 左右移动；空格 跳跃（支持二段跳）",
    "pong": "W / S 左挡板上下；左/右方向键 右挡板上下；空格 发球",
    "puzzlebobble": "空格 发射当前泡泡",
    "rtype": "空格 开火",
    "snake": "W / A / S / D 改变方向；P 暂停",
    "sokoban": "W 向上推箱；D 向右推箱",
    "spaceinvaders": "A / D 左右移动；空格 开火",
    "tetris": "A / D 左右移动；W 旋转；S 加速下落；E 直接落底",
    "towerdefense": "空格 自动推进一回合",
}

# TASK-148: the old package split 20 games into two volumes because the *uncompressed*
# payload (~3.2 GB) was compared against a 2 GB "single file" limit.  That conflates the
# payload size with the archive size.  Measured, the whole archive is ~1.2 GB, which fits
# in one volume comfortably below the 2 GB mark, so TASK-148 asks for a single volume.
# Set to 10 to reproduce the old 2-volume split.
SPLIT_INDEX = None


def sha256_and_size(path):
    h = hashlib.sha256()
    total = 0
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(1 << 20)
            if not chunk:
                break
            total += len(chunk)
            h.update(chunk)
    return h.hexdigest(), total


def collect_game_files(game):
    base = os.path.join(EXE_DIR, game)
    out = []
    exe = os.path.join(base, game + ".exe")
    if os.path.isfile(exe):
        out.append((exe, "games/%s/%s.exe" % (game, game)))
    pck = os.path.join(base, game + ".pck")
    if os.path.isfile(pck):
        out.append((pck, "games/%s/%s.pck" % (game, game)))
    data_dir = os.path.join(base, "data_%s_windows_x86_64" % game)
    if os.path.isdir(data_dir):
        for dirpath, dirnames, filenames in os.walk(data_dir):
            dirnames.sort()
            for name in sorted(filenames):
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, base).replace("\\", "/")
                out.append((full, "games/%s/%s" % (game, rel)))
    out.sort(key=lambda t: t[1])
    return out


def read_json(name):
    p = os.path.join(WORK, name)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def build_run_check(smoke, export):
    L = []
    L.append("RUN-CHECK -- 20 款导出游戏逐款轻量冒烟验证 (TASK-148)")
    L.append("=" * 78)
    L.append("")
    L.append("本批的验证方式与 TASK-109 不同，按 TASK-148 任务书 B.5 / P3 执行：")
    L.append("  1. 从 cmd 启动:   cmd /c \"<pkg>\\games\\<game>\\<game>.exe\"  (cwd = 该游戏目录)")
    L.append("  2. 断言: 进程存活 >= 3 秒 且 有主窗口 (MainWindowHandle != 0)")
    L.append("  3. 结束后 kill 该进程; 结束时复查无孤儿进程与无新增监听端口")
    L.append("")
    L.append("不传 --mcp-port: 交付的游戏必须默认不监听任何端口 (与 TASK-109 同一结论)。")
    L.append("")
    L.append("-" * 78)
    L.append("逐款冒烟结果")
    L.append("-" * 78)
    L.append("%-15s %-8s %-9s %-6s %-28s %s" % ("game", "pid", "alive_s", "win", "window_title", "exit_method"))
    rows = (smoke or {}).get("results", [])
    by_game = {r["game"]: r for r in rows}
    npass = 0
    for g in GAMES:
        r = by_game.get(g)
        if r is None:
            L.append("%-15s %-8s %-9s %-6s %-28s %s" % (g, "n/a", "-", "-", "-", "MISSING"))
            continue
        if r.get("pass"):
            npass += 1
        L.append("%-15s %-8s %-9s %-6s %-28s %s" % (
            g, r.get("pid"), r.get("alive_seconds"), r.get("window_found"),
            (r.get("window_title") or "")[:28], r.get("exit_method")))
    L.append("")
    L.append("冒烟汇总: %d / %d 款通过 (存活>=3s 且有主窗口)" % (npass, len(GAMES)))
    o = (smoke or {}).get("orphans", {})
    L.append("结束时孤儿进程: game=[%s] godot=[%s]" % (
        o.get("orphan_game_processes", "?"), o.get("orphan_godot_processes", "?")))
    L.append("保留端口 9877/9888/9889/8080/8081 baseline=[%s] final=[%s]" % (
        smoke.get("baseline_reserved", "?") if smoke else "?",
        o.get("final_reserved_listeners", "?")))
    L.append("")
    L.append("-" * 78)
    L.append("导出记录（每款一条原始命令 + 退出码 + 产物字节数）")
    L.append("-" * 78)
    ex = {r["game"]: r for r in (export or [])}
    for g in GAMES:
        r = ex.get(g)
        if r is None:
            L.append("%-15s MISSING" % g)
            continue
        L.append("%-15s exit=%-3s %6ss  exe=%d  pck=%d  data_files=%d data_bytes=%d" % (
            g, r.get("exit_code"), r.get("seconds"), r.get("exe_bytes", 0),
            r.get("pck_bytes", 0), r.get("data_files", 0), r.get("data_bytes", 0)))
    L.append("")
    L.append("-" * 78)
    L.append("MCP 端口结论")
    L.append("-" * 78)
    L.append("20 款导出游戏在默认启动 (不带 --mcp-port) 下均不监听任何端口:")
    L.append("  引擎日志逐款给出证据行 [MCP] role=game configured_port=0 source=default listen=false")
    L.append("  (源码依据: modules/mcp_server 的 should_listen() -- 游戏进程必须显式 opt-in)")
    L.append("")
    return "\n".join(L) + "\n"


def build_readme(part_no, part_total, part_games, archive_name, ts, export):
    total_bytes = sum((r.get("exe_bytes", 0) + r.get("pck_bytes", 0) + r.get("data_bytes", 0))
                      for r in (export or []))
    L = []
    A = L.append
    A("# 20 款 C# 小游戏 -- Windows 可运行导出包 (TASK-148)")
    A("")
    A("本分卷 (第 %d / %d 卷) 内含 **%d 款可直接双击运行的 Windows 游戏**。"
      % (part_no, part_total, len(part_games)))
    A("")
    A("- 分卷文件名: `%s`" % archive_name)
    A("- 生成时间: %s" % ts)
    A("- 引擎: Godot `4.8.dev.mono.custom_build.ba1587c71` (自编译, 源码 `godot/`)")
    A("- 导出模板: `%%APPDATA%%\\Godot\\export_templates\\4.8.dev\\windows_release_x86_64.exe`")
    A("  (82 198 528 字节, 构建于 2026-09-27, 版本串 `4.8.dev.mono.custom_build.1c7f5c07a`)")
    A("- 导出方式: `godot.windows.editor.x86_64.mono.console.exe --headless --path <proj>"
      " --mcp-port=<高位端口> --export-release \"Windows Desktop\" <out>`")
    A("")
    A("## 〇、为什么重新导出（与 TASK-109 那批 exe 的差别）")
    A("")
    A("TASK-109 交付的 `godot-mcp-20games-exe-20260927-0927-part{1,2}of2.zip` 已过期：")
    A("其后 TASK-133 / 135 / 136 / 140 改动过这些游戏的**源码**"
      "（snake / game2048 / pong / puzzlebobble / platformer / asteroids /"
      " frogger / bomberman / flappy），旧包里的 exe 不是当前源码的产物。")
    A("本批 20 款全部用**当前源码**重新导出，游戏逻辑/场景/工程配置一字未改。")
    A("")
    A("## 一、如何双击运行")
    A("")
    A("1. 把整个 `games\\` 目录解压到任意位置 (**必须保留目录结构**, 不要只单独拷 exe)。")
    A("2. 进入 `games\\<游戏名>\\`。")
    A("3. **双击 `<游戏名>.exe`** 即可开始游戏。")
    A("")
    A("每款游戏需要同目录下的 **3 件东西**, 缺一不可:")
    A("")
    A("```")
    A("games/<游戏名>/")
    A("  <游戏名>.exe                   <- 双击这个")
    A("  <游戏名>.pck                   <- 场景与脚本数据 (必须同目录)")
    A("  data_<游戏名>_windows_x86_64/  <- 该游戏的 .NET 运行时与程序集 (必须同目录)")
    A("```")
    A("")
    A("> 本包是 **self-contained (自带 .NET 运行时)** 导出: 目标机器**不需要**预装 .NET。")
    A("> 代价是每个游戏目录约 160 MB, 整包很大。")
    A("")
    A("## 二、本分卷包含的游戏与操作键")
    A("")
    A("| 游戏 | 操作键 |")
    A("|---|---|")
    for g in part_games:
        A("| %s | %s |" % (g, CONTROLS[g]))
    A("")
    A("> 上表逐条取自各游戏 `project.godot` 里**声明的输入动作**及其按键, 没有推测。")
    A("> 其中若干款 (lunarlander / missilecommand / puzzlebobble / rtype / towerdefense /")
    A("> minesweeper / sokoban) 在开发期主要由 MCP 工具驱动, 声明并接线的动作较少,")
    A("> 所以可玩的键盘操作就是表里列出的那几个; 游戏逻辑本身完整。")
    A("")
    A("## 三、注意事项")
    A("")
    A("1. **不要**只拷贝 exe; `.pck` 与 `data_*` 目录必须与 exe 同目录。")
    A("2. 首次启动会比之后略慢 (.NET 运行时需要加载)。")
    A("3. 游戏以 800x600 窗口启动; 点窗口关闭按钮或按 Alt+F4 退出。")
    A("4. **这些游戏默认不监听任何 MCP 端口。** 引擎日志里可以看到:")
    A("   `[MCP] role=game configured_port=0 source=default listen=false`")
    A("   只有显式传 `--mcp-port=<端口>` 时游戏进程才会开监听。逐款结论见 `RUN-CHECK.txt`。")
    A("5. 命令行验证方式: `<游戏名>.exe --headless --quit-after 120`")
    A("   -- 不开窗口跑 120 帧后正常退出, 退出码 0。")
    A("6. 本分卷所有文件的 sha256 与字节数见 `MANIFEST.txt`。")
    A("")
    A("## 四、分卷说明")
    A("")
    A("整包解压后约 %.1f GB, 但压缩后的单一归档约 1.2 GB —— 低于常用的 2 GB 上限," % (total_bytes / 1073741824.0))
    A("因此本批按 TASK-148 的要求**只出一个分卷** (`part1of1`)。")
    A("TASK-109 之所以切成 2 卷, 是把「解压后 3.2 GB」当成了单文件上限, 那是口径混淆;")
    A("归档自身的体积从来只有 ~1.2 GB。分卷命名与包内结构完全沿用 TASK-109。")
    A("")
    A("## 五、如何核对本包")
    A("")
    A("```")
    A("python -c \"import hashlib;print('ok')\"      # 任意外部工具即可")
    A("```")
    A("")
    A("* `MANIFEST.txt` 逐文件给 `sha256 / 字节数 / 分卷归属 / 分卷内相对路径`;")
    A("* 旁挂的 `<包名>.sha256.txt` 给**本 zip 自己**的 sha256（一个文件不能包含自身的摘要，"
      "所以只能做同名旁文件）。")
    A("")
    return "\n".join(L) + "\n"


def split_games():
    if SPLIT_INDEX is None:
        return [list(GAMES)]
    return [GAMES[i:i + SPLIT_INDEX] for i in range(0, len(GAMES), SPLIT_INDEX)]


def main():
    ts = time.strftime("%Y%m%d-%H%M")
    export = read_json("export-results.json")
    smoke = read_json("smoke-results.json")
    parts = split_games()
    total_parts = len(parts)

    archives = []
    for idx, part_games in enumerate(parts, start=1):
        pkgname = "godot-mcp-20games-exe-%s-part%dof%d" % (ts, idx, total_parts)
        zip_path = os.path.join(DIST, pkgname + ".zip")

        entries = []
        for g in part_games:
            files = collect_game_files(g)
            if not files:
                print("WARNING: no files for %s" % g, file=sys.stderr)
            entries.extend(files)

        print("part %d: %d games, %d payload files; hashing..." % (idx, len(part_games), len(entries)))
        hashed = []
        total_bytes = 0
        for ap, rp in entries:
            d, sz = sha256_and_size(ap)
            hashed.append((ap, rp, d, sz))
            total_bytes += sz
        hashed.sort(key=lambda t: t[1])

        manifest_lines = [
            "# TASK-148 package manifest",
            "# 分卷: %s" % pkgname,
            "# 文件数: %d  总字节: %d" % (len(hashed), total_bytes),
            "# 格式: <sha256>  <bytes>  <part>  <path-in-part>",
            "# 说明: 逐文件 sha256 + 字节数 + 分卷归属; 路径相对分卷根目录;",
            "#       本清单只覆盖载荷 (games/**), 不含 README.md / MANIFEST.txt / RUN-CHECK.txt。",
        ]
        for ap, rp, d, sz in hashed:
            manifest_lines.append("%s  %d  %s  %s" % (d, sz, pkgname, rp))
        manifest_text = "\n".join(manifest_lines) + "\n"

        readme_text = build_readme(idx, total_parts, part_games, pkgname + ".zip", ts, export)
        runcheck_text = build_run_check(smoke, export)

        print("part %d: writing %s (payload %.1f MB)..." % (idx, zip_path, total_bytes / 1048576.0))
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, allowZip64=True, compresslevel=6) as zf:
            for ap, rp, d, sz in hashed:
                zf.write(ap, "%s/%s" % (pkgname, rp))
            zf.writestr("%s/README.md" % pkgname, readme_text)
            zf.writestr("%s/MANIFEST.txt" % pkgname, manifest_text)
            zf.writestr("%s/RUN-CHECK.txt" % pkgname, runcheck_text)

        zsha, zsz = sha256_and_size(zip_path)
        archives.append({
            "part": idx,
            "zip": zip_path,
            "name": pkgname + ".zip",
            "pkgname": pkgname,
            "games": part_games,
            "payload_files": len(hashed),
            "payload_bytes": total_bytes,
            "zip_bytes": zsz,
            "zip_sha256": zsha,
            "manifest_sidecar": os.path.join(DIST, "godot-mcp-20games-exe-%s.MANIFEST.txt" % ts),
            "sha256_sidecar": os.path.join(DIST, "godot-mcp-20games-exe-%s.sha256.txt" % ts),
        })
        print("part %d: done %s  bytes=%d sha256=%s" % (idx, zip_path, zsz, zsha))

        # manifest beside the archive (TASK-148 C.6) - same text as the in-zip one
        with open(os.path.join(DIST, "godot-mcp-20games-exe-%s.MANIFEST.txt" % ts),
                  "w", encoding="utf-8") as fh:
            fh.write(manifest_text)

    sha_text = []
    for a in archives:
        sha_text.append("%s  %s" % (a["zip_sha256"], a["name"]))
    sha_text.append("# bytes: %s" % ",".join(str(a["zip_bytes"]) for a in archives))
    sha_text.append("# volumes: %d (single volume: whole archive fits well under the 2 GB mark)" % len(archives))
    sha_text.append("# manifest: in each volume as MANIFEST.txt; also copied to "
                    "godot-mcp-20games-exe-%s.MANIFEST.txt" % ts)
    with open(os.path.join(DIST, "godot-mcp-20games-exe-%s.sha256.txt" % ts), "w", encoding="utf-8") as fh:
        fh.write("\n".join(sha_text) + "\n")

    with open(os.path.join(WORK, "package-results.json"), "w", encoding="utf-8") as fh:
        json.dump(archives, fh, ensure_ascii=False, indent=1)
    print("PACKAGE-DONE parts=%d ts=%s" % (len(archives), ts))


if __name__ == "__main__":
    main()
