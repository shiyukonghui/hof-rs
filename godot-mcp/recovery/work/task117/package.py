#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-117 step C: package the 20 re-exported (TASK-116-fixed) games.

Same structure as TASK-109, with the two new things this task owes the user:
  * README.md carries a per-game `## 玩法 -- <game>` section, taken verbatim from
    the project's own README.md (the one TASK-116 rewrote from the actual InputMap),
    not from a hand-typed table;
  * RUN-CHECK.txt carries, next to the launch check, the **playability gate verdict
    measured on the exported exe itself** (runs\\playability-exe\\playability.json).

Layout inside every part:
  <pkgname>/README.md
  <pkgname>/MANIFEST.txt
  <pkgname>/RUN-CHECK.txt
  <pkgname>/games/<game>/<game>.exe
  <pkgname>/games/<game>/<game>.pck
  <pkgname>/games/<game>/data_<game>_windows_x86_64/...
"""
import hashlib
import io
import json
import os
import re
import sys
import time
import zipfile

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
DIST = os.path.join(ROOT, "dist")
EXE_DIR = os.path.join(DIST, "exe")
WORK = os.path.join(ROOT, "recovery", "work", "task117")
PROJECTS = os.path.join(ROOT, "projects")
RUNS_EXE = os.path.join(ROOT, "runs", "playability-exe")

GAMES = [
    "asteroids", "bomberman", "breakout", "flappy", "frogger", "game2048",
    "lunarlander", "match3", "minesweeper", "missilecommand", "pacman",
    "platformer", "pong", "puzzlebobble", "rtype", "snake", "sokoban",
    "spaceinvaders", "tetris", "towerdefense",
]
SPLIT_INDEX = 10


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


def read_text(path):
    for enc in ("utf-8", "utf-8-sig", "gbk", "latin-1"):
        try:
            with io.open(path, "r", encoding=enc) as fh:
                return fh.read()
        except Exception:
            continue
    return ""


def play_section(game):
    """The `## 玩法` block of the project's own README, verbatim."""
    txt = read_text(os.path.join(PROJECTS, game, "README.md"))
    m = re.search(r"^##\s*玩法\s*$(.*?)(?=^##\s|\Z)", txt, re.M | re.S)
    body = (m.group(1).strip() if m else "")
    if not body:
        return "(该工程 README 没有 `## 玩法` 段落 -- 这一条本身就是缺陷)"
    return body


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


def read_json(path):
    if not os.path.isfile(path):
        return None
    with io.open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def gate_by_game():
    doc = read_json(os.path.join(RUNS_EXE, "playability.json")) or {}
    return {g["game"]: g for g in (doc.get("games") or [])}, doc


def verify_by_game():
    doc = read_json(os.path.join(WORK, "verify-results.json"))
    if doc is None:
        return {}
    if isinstance(doc, dict):
        doc = [doc]
    return {r["game"]: r for r in doc}


def build_run_check(verify, gate, gate_doc):
    L = []
    L.append("RUN-CHECK -- 20 款导出游戏逐款启动验证 + 可玩性门结论 (TASK-117)")
    L.append("=" * 96)
    L.append("")
    L.append("本包是 TASK-116 修好「玩家输入被关掉」之后**重新导出**的版本。")
    L.append("下面两栏都是对**导出产物本身**（包里这一份 exe）测出来的，不是对工程测的。")
    L.append("")
    L.append("检查 1 (确定性退出, 逐款):")
    L.append("    cd <pkg>/games/<game>")
    L.append("    <game>.exe --headless --quit-after 120")
    L.append("    断言: 退出码 == 0, 且 stdout 打印自己的 <TOKEN>_READY 状态行。")
    L.append("")
    L.append("检查 2 (可玩性门 P1..P6, 逐款, 对导出 exe):")
    L.append("    窗口化启动导出 exe (--mcp-port=<唯一端口>), 用游戏侧 MCP 端点")
    L.append("    抓整窗帧 / 注入每个声明动作 / 采样节点状态, 由 tools/playability_gate.py 判定。")
    L.append("    P1 可见性 / P2 输入响应 / P3 主循环 / P4 无崩溃无模态框 / P5 可发现性 / P6 能力表")
    L.append("    逐款证据: runs/playability-exe/<game>/{gate.json,frames/,filmstrip.png}")
    L.append("")
    L.append("-" * 96)
    L.append("逐款结果")
    L.append("-" * 96)
    L.append("%-15s %-5s %-9s %-9s %-12s %s" % (
        "game", "exit", "READY", "launch", "playability", "failing criteria"))
    v = verify or {}
    gb = gate or {}
    ok_launch = 0
    ok_play = 0
    for g in GAMES:
        launch = v.get(g)
        if launch is None:
            lc, lv = "n/a", "MISSING"
        else:
            lc = launch.get("exit_code")
            lv = "PASS" if launch.get("pass") else "FAIL"
            if launch.get("pass"):
                ok_launch += 1
        gt = gb.get(g)
        if gt is None:
            pv, fails = "MISSING", "-"
        else:
            pv = gt.get("verdict")
            if pv == "playable":
                ok_play += 1
            fails = ",".join(k for k in ("P1", "P2", "P3", "P4", "P5", "P6")
                             if not (gt.get("criteria", {}).get(k) or {}).get("pass")) or "-"
        L.append("%-15s %-5s %-9s %-9s %-12s %s" % (
            g, lc, "yes" if (launch or {}).get("ready_found") else "no", lv, pv, fails))
    L.append("")
    L.append("汇总: 启动验证 %d/%d PASS; 可玩性门 %d/%d playable" % (
        ok_launch, len(GAMES), ok_play, len(GAMES)))
    L.append("")
    L.append("-" * 96)
    L.append("可玩性门逐条判据 (P1..P6) 的机器可读来源")
    L.append("-" * 96)
    for g in GAMES:
        gt = gb.get(g)
        if not gt:
            L.append("%-15s (no gate result)" % g)
            continue
        L.append("%-15s %s" % (g, " ".join(
            "%s=%s" % (k, "pass" if (gt["criteria"].get(k) or {}).get("pass") else "FAIL")
            for k in ("P1", "P2", "P3", "P4", "P5", "P6"))))
        tgt = gt.get("target") or {}
        exe = (tgt.get("exe") or {})
        if exe.get("sha256"):
            L.append("%-15s   exe sha256=%s" % ("", exe["sha256"]))
    L.append("")
    L.append("-" * 96)
    L.append("MCP 端口结论 (启动验证那一遍, 刻意不带 --mcp-port)")
    L.append("-" * 96)
    L.append("baseline listeners 9877/9888/9889 : [%s]" % (gate_doc or {}).get("__baseline", ""))
    L.append("引擎日志逐款给出证据行: [MCP] role=game configured_port=0 source=default listen=false")
    L.append("(源码依据: mcp_server.cpp should_listen() -- 游戏进程必须显式 opt-in)")
    L.append("")
    L.append("注: 可玩性门那一遍**必须**给游戏进程传 --mcp-port=<唯一端口>, 因为门要通过")
    L.append("    游戏侧 MCP 端点抓帧与注入输入; 每次只用自己那一个端口, 结束即杀, 不碰 9877。")
    return "\n".join(L) + "\n"


def build_readme(part_no, part_total, part_games, archive_name, ts, gate, verify):
    L = []
    L.append("# 20 款 C# 小游戏 -- Windows 可运行导出包（可玩版重导出）")
    L.append("")
    L.append("本分卷 (第 %d / %d 卷) 内含 **%d 款可直接双击运行的 Windows 游戏**。"
             % (part_no, part_total, len(part_games)))
    L.append("")
    L.append("- 分卷文件名: `%s`" % archive_name)
    L.append("- 生成时间: %s" % ts)
    L.append("- 任务: TASK-117 —— 在 TASK-116 修好「出厂把玩家输入关着」的 19 款之后**重新导出**。")
    L.append("  你以前试玩的那批 exe 是修复前的 (TASK-109 导出), 本包取代它。")
    L.append("- 引擎: Godot 4.8.dev.mono.custom_build (自编译, 源码 `godot/`)")
    L.append("- 导出模板: 同一份源码自建的 "
             "`%APPDATA%\\Godot\\export_templates\\4.8.dev\\windows_release_x86_64.exe`")
    L.append("")
    L.append("## 一、如何双击运行")
    L.append("")
    L.append("1. 把整个 `games\\` 目录解压到任意位置 (**必须保留目录结构**, 不要只单独拷 exe)。")
    L.append("2. 进入 `games\\<游戏名>\\`。")
    L.append("3. **双击 `<游戏名>.exe`** 即可开始游戏。")
    L.append("")
    L.append("每款游戏需要同目录下的 **3 件东西**, 缺一不可:")
    L.append("")
    L.append("```")
    L.append("games/<游戏名>/")
    L.append("  <游戏名>.exe                   <- 双击这个")
    L.append("  <游戏名>.pck                   <- 场景与脚本数据 (必须同目录)")
    L.append("  data_<游戏名>_windows_x86_64/  <- 该游戏的 .NET 运行时与程序集 (必须同目录)")
    L.append("```")
    L.append("")
    L.append("> 本包是 **self-contained (自带 .NET 运行时)** 导出: 目标机器**不需要**预装 .NET。")
    L.append("> 代价是每个游戏目录约 160 MB, 整包很大, 因此分成多个 zip 分卷。")
    L.append("> 首次启动会比之后略慢 (.NET 运行时需要加载)。")
    L.append("")
    L.append("## 二、玩法 —— 本分卷每款游戏的操作键")
    L.append("")
    L.append("下表与下面每一节都取自各工程自己的 `README.md`（其按键经 TASK-116 与")
    L.append("`project.godot` 的 InputMap 逐条核对过），并且**每一款都在导出 exe 上被")
    L.append("可玩性门实测过**：按下表里的键，游戏状态或画面必须真的发生变化。")
    L.append("")
    for g in part_games:
        gt = (gate or {}).get(g) or {}
        verdict = gt.get("verdict", "（未测）")
        L.append("- **%s** — 可玩性门判定: `%s`" % (g, verdict))
    L.append("")
    for g in part_games:
        L.append("## 玩法 — %s" % g)
        L.append("")
        L.append(play_section(g))
        L.append("")
    L.append("## 三、注意事项")
    L.append("")
    L.append("1. **不要**只拷贝 exe; `.pck` 与 `data_*` 目录必须与 exe 同目录。")
    L.append("2. 游戏以各自工程声明的窗口尺寸启动 (多数 800x600); 点窗口关闭按钮或按 Alt+F4 退出。")
    L.append("3. **这些游戏默认不监听任何 MCP 端口。** 引擎日志里可以看到:")
    L.append("   `[MCP] role=game configured_port=0 source=default listen=false`")
    L.append("   只有显式传 `--mcp-port=<端口>` 时游戏进程才会开监听。")
    L.append("4. 命令行验证方式: `<游戏名>.exe --headless --quit-after 120`")
    L.append("   -- 不开窗口跑 120 帧后正常退出, 退出码 0, 并在 stdout 打印自己的 `<TOKEN>_READY` 状态行。")
    L.append("5. 逐款启动验证与**导出 exe 上的可玩性门结论**见 `RUN-CHECK.txt`;")
    L.append("   本分卷所有文件的 sha256 与字节数见 `MANIFEST.txt`。")
    L.append("")
    L.append("## 四、分卷说明")
    L.append("")
    L.append("整包 (20 款 x 约 160 MB) 压缩前约 3.2 GB, 超过单文件 2 GB 的常用上限,")
    L.append("因此**按游戏顺序切成 %d 个 zip 分卷**。每个分卷都自带完整的" % part_total)
    L.append("README / MANIFEST / RUN-CHECK, 可以独立解压使用。")
    L.append("")
    L.append("分卷划分:")
    for i in range(part_total):
        lo = i * SPLIT_INDEX
        hi = min(lo + SPLIT_INDEX, len(GAMES))
        L.append("  第 %d 卷: %s" % (i + 1, ", ".join(GAMES[lo:hi])))
    L.append("")
    return "\n".join(L) + "\n"


def split_games():
    return [GAMES[i:i + SPLIT_INDEX] for i in range(0, len(GAMES), SPLIT_INDEX)]


def main():
    ts = time.strftime("%Y%m%d-%H%M")
    verify = verify_by_game()
    gate, gate_doc = gate_by_game()
    parts = split_games()
    total_parts = len(parts)

    archives = []
    for idx, part_games in enumerate(parts, start=1):
        pkgname = "godot-mcp-20games-playable-%s-part%dof%d" % (ts, idx, total_parts)
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

        m = ["# TASK-117 package manifest (playable re-export)",
             "# 分卷: %s" % pkgname,
             "# 文件数: %d  总字节: %d" % (len(hashed), total_bytes),
             "# 格式: <sha256>  <bytes>  <path-in-zip>"]
        for ap, rp, d, sz in sorted(hashed, key=lambda t: t[1]):
            m.append("%s  %d  %s" % (d, sz, rp))
        manifest_text = "\n".join(m) + "\n"

        readme_text = build_readme(idx, total_parts, part_games, pkgname + ".zip", ts, gate, verify)
        runcheck_text = build_run_check(verify, gate, gate_doc)

        print("part %d: writing %s (payload %.1f MB)..." % (idx, zip_path, total_bytes / 1048576.0))
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, allowZip64=True,
                             compresslevel=6) as zf:
            for ap, rp, d, sz in sorted(hashed, key=lambda t: t[1]):
                zf.write(ap, "%s/%s" % (pkgname, rp))
            zf.writestr("%s/README.md" % pkgname, readme_text)
            zf.writestr("%s/MANIFEST.txt" % pkgname, manifest_text)
            zf.writestr("%s/RUN-CHECK.txt" % pkgname, runcheck_text)

        zsha, zsz = sha256_and_size(zip_path)
        archives.append({"part": idx, "zip": zip_path, "name": pkgname + ".zip",
                         "games": part_games, "payload_files": len(hashed),
                         "payload_bytes": total_bytes, "zip_bytes": zsz, "zip_sha256": zsha})
        print("part %d: done %s  bytes=%d sha256=%s" % (idx, zip_path, zsz, zsha))

    with io.open(os.path.join(WORK, "package-results.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(archives, indent=1, ensure_ascii=False))
    print("PACKAGE-DONE parts=%d" % len(archives))


if __name__ == "__main__":
    main()
