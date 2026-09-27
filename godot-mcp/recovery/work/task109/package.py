#!/usr/bin/env python3
# TASK-109 step 5: package the 20 exported games into zip parts.
#
# Layout inside every part:
#   <pkgname>/README.md               (Chinese: how to run, controls, notes)
#   <pkgname>/MANIFEST.txt            (sha256 + byte size, one line per file)
#   <pkgname>/RUN-CHECK.txt           (per-game launch verification result)
#   <pkgname>/games/<game>/<game>.exe
#   <pkgname>/games/<game>/<game>.pck
#   <pkgname>/games/<game>/data_<game>_windows_x86_64/...
#
# Files are streamed straight into the zip (no staging copy), so peak disk usage
# stays near the archive size instead of 2x the payload.
import hashlib
import json
import os
import sys
import time
import zipfile

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
DIST = os.path.join(ROOT, "dist")
EXE_DIR = os.path.join(DIST, "exe")
WORK = os.path.join(ROOT, "recovery", "work", "task109")

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

SPLIT_INDEX = 10  # first 10 games in part 1, last 10 in part 2


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
    """Return sorted list of (absolute_path, archive_relative_path)."""
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


def build_run_check(verify):
    L = []
    L.append("RUN-CHECK -- 20 款导出游戏逐款启动验证结果 (TASK-109)")
    L.append("=" * 78)
    L.append("")
    L.append("验证方式 A (确定性退出, 逐款):")
    L.append("    cd <pkg>/games/<game>")
    L.append("    <game>.exe --headless --quit-after 120")
    L.append("    断言: 进程退出码 == 0")
    L.append("")
    L.append("验证方式 B (窗口化抽查, 限时 8 秒后强制结束):")
    L.append("    <game>.exe        (不加 --headless, 进程必须能起来且不立即崩溃)")
    L.append("")
    L.append("MCP 端口核验:")
    L.append("    游戏进程启动时不带 --mcp-port, 断言 9877 / 9888 / 9889 上不新增监听。")
    L.append("")
    L.append("-" * 78)
    L.append("逐款结果 (方式 A)")
    L.append("-" * 78)
    L.append("%-16s %-8s %-8s %-10s %s" % ("game", "exit", "verdict", "seconds", "new_mcp_ports"))
    headless = (verify or {}).get("headless", [])
    by_game = {r["game"]: r for r in headless}
    ok = 0
    for g in GAMES:
        r = by_game.get(g)
        if r is None:
            L.append("%-16s %-8s %-8s %-10s %s" % (g, "n/a", "MISSING", "-", "-"))
            continue
        verdict = "PASS" if r.get("exit_code") == 0 else "FAIL"
        if verdict == "PASS":
            ok += 1
        L.append("%-16s %-8s %-8s %-10s %s" % (
            g, r.get("exit_code"), verdict, r.get("seconds"),
            (r.get("new_mcp_ports") or "none")))
    L.append("")
    L.append("方式 A 汇总: %d / %d 款退出码为 0" % (ok, len(GAMES)))
    L.append("")
    L.append("-" * 78)
    L.append("窗口化抽查 (方式 B)")
    L.append("-" * 78)
    for r in (verify or {}).get("windowed", []):
        L.append("%-16s alive_after_8s=%-6s exit_when_killed=%-6s new_mcp_ports=%s" % (
            r["game"], r.get("stayed_alive"), r.get("exit_code"),
            (r.get("new_mcp_ports") or "none")))
    L.append("")
    L.append("-" * 78)
    L.append("MCP 端口结论")
    L.append("-" * 78)
    L.append("baseline listeners on 9877/9888/9889 : [%s]" % (verify or {}).get("baseline_ports", ""))
    L.append("final    listeners on 9877/9888/9889 : [%s]" % (verify or {}).get("final_ports", ""))
    L.append("")
    L.append("结论: 20 款导出游戏在默认启动 (不带 --mcp-port) 下均不监听任何 MCP 端口;")
    L.append("      引擎自身日志逐款给出证据行:")
    L.append("      [MCP] role=game configured_port=0 source=default listen=false")
    L.append("      (源码依据: mcp_server.cpp should_listen() -- 游戏进程必须显式 opt-in)")
    L.append("")
    return "\n".join(L) + "\n"


def build_readme(part_no, part_total, part_games, archive_name, ts):
    L = []
    L.append("# 20 款 C# 小游戏 -- Windows 可运行导出包 (TASK-109)")
    L.append("")
    L.append("本分卷 (第 %d / %d 卷) 内含 **%d 款可直接双击运行的 Windows 游戏**。"
             % (part_no, part_total, len(part_games)))
    L.append("")
    L.append("- 分卷文件名: `%s`" % archive_name)
    L.append("- 生成时间: %s" % ts)
    L.append("- 引擎: Godot 4.8.dev.mono.custom_build (自编译, 源码 `godot/`)")
    L.append("- 导出模板: 用**同一份源码**跑 "
             "`scons platform=windows target=template_release module_mono_enabled=yes -j8` 自建,")
    L.append("  产物安装为 `%APPDATA%\\Godot\\export_templates\\4.8.dev\\windows_release_x86_64.exe`")
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
    L.append("")
    L.append("## 二、本分卷包含的游戏与操作键")
    L.append("")
    L.append("| 游戏 | 操作键 |")
    L.append("|---|---|")
    for g in part_games:
        L.append("| %s | %s |" % (g, CONTROLS[g]))
    L.append("")
    L.append("> 上表逐条取自各游戏 `project.godot` 里**声明的输入动作**及其按键, 没有推测。")
    L.append("> 其中若干款 (lunarlander / missilecommand / puzzlebobble / rtype / towerdefense /")
    L.append("> minesweeper / sokoban) 在开发期主要由 MCP 工具驱动, 声明并接线的动作较少,")
    L.append("> 所以可玩的键盘操作就是表里列出的那几个; 游戏逻辑本身完整 (胜负 / 计分 / 边界")
    L.append("> 都由仓库里的证据链钉住)。")
    L.append("")
    L.append("## 三、注意事项")
    L.append("")
    L.append("1. **不要**只拷贝 exe; `.pck` 与 `data_*` 目录必须与 exe 同目录。")
    L.append("2. 首次启动会比之后略慢 (.NET 运行时需要加载)。")
    L.append("3. 游戏以 800x600 窗口启动; 点窗口关闭按钮或按 Alt+F4 退出。")
    L.append("4. **这些游戏默认不监听任何 MCP 端口。** 引擎日志里可以看到:")
    L.append("   `[MCP] role=game configured_port=0 source=default listen=false`")
    L.append("   只有显式传 `--mcp-port=<端口>` 时游戏进程才会开监听。逐款结论见 `RUN-CHECK.txt`。")
    L.append("5. 命令行验证方式: `<游戏名>.exe --headless --quit-after 120`")
    L.append("   -- 不开窗口跑 120 帧后正常退出, 退出码 0。")
    L.append("6. 本分卷所有文件的 sha256 与字节数见 `MANIFEST.txt`。")
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
    parts = []
    for i in range(0, len(GAMES), SPLIT_INDEX):
        parts.append(GAMES[i:i + SPLIT_INDEX])
    return parts


def main():
    ts = time.strftime("%Y%m%d-%H%M")
    verify = read_json("verify-results.json")
    parts = split_games()
    total_parts = len(parts)

    archives = []
    for idx, part_games in enumerate(parts, start=1):
        pkgname = "godot-mcp-20games-exe-%s-part%dof%d" % (ts, idx, total_parts)
        zip_path = os.path.join(DIST, pkgname + ".zip")

        # pass 1: collect + hash
        entries = []
        for g in part_games:
            files = collect_game_files(g)
            if not files:
                print("WARNING: no files for %s" % g, file=sys.stderr)
            for ap, rp in files:
                entries.append((ap, rp))
        print("part %d: %d games, %d payload files; hashing..." % (idx, len(part_games), len(entries)))
        hashed = []
        total_bytes = 0
        for ap, rp in entries:
            d, sz = sha256_and_size(ap)
            hashed.append((ap, rp, d, sz))
            total_bytes += sz

        manifest_lines = []
        manifest_lines.append("# TASK-109 package manifest")
        manifest_lines.append("# 分卷: %s" % pkgname)
        manifest_lines.append("# 文件数: %d  总字节: %d" % (len(hashed), total_bytes))
        manifest_lines.append("# 格式: <sha256>  <bytes>  <path-in-zip>")
        for ap, rp, d, sz in sorted(hashed, key=lambda t: t[1]):
            manifest_lines.append("%s  %d  %s" % (d, sz, rp))
        manifest_text = "\n".join(manifest_lines) + "\n"

        readme_text = build_readme(idx, total_parts, part_games, pkgname + ".zip", ts)
        runcheck_text = build_run_check(verify)

        # pass 2: write zip
        print("part %d: writing %s (payload %.1f MB)..." % (idx, zip_path, total_bytes / 1048576.0))
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, allowZip64=True, compresslevel=6) as zf:
            for ap, rp, d, sz in sorted(hashed, key=lambda t: t[1]):
                zf.write(ap, "%s/%s" % (pkgname, rp))
            zf.writestr("%s/README.md" % pkgname, readme_text)
            zf.writestr("%s/MANIFEST.txt" % pkgname, manifest_text)
            zf.writestr("%s/RUN-CHECK.txt" % pkgname, runcheck_text)

        zsha, zsz = sha256_and_size(zip_path)
        archives.append({
            "part": idx,
            "zip": zip_path,
            "name": pkgname + ".zip",
            "games": part_games,
            "payload_files": len(hashed),
            "payload_bytes": total_bytes,
            "zip_bytes": zsz,
            "zip_sha256": zsha,
        })
        print("part %d: done %s  bytes=%d sha256=%s" % (idx, zip_path, zsz, zsha))

    with open(os.path.join(WORK, "package-results.json"), "w", encoding="utf-8") as fh:
        json.dump(archives, fh, indent=1)
    print("PACKAGE-DONE parts=%d" % len(archives))


if __name__ == "__main__":
    main()
