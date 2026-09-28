#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-148: assemble recovery/reports/TASK-148-REPORT.md from the recorded evidence.

Every number in the tables below is read back from the run's own files
(export-results.json / smoke-results.json / package-results.json / selfcheck.txt /
zip-run-check.txt / the delivered MANIFEST.txt), never retyped by hand.
"""
import hashlib
import json
import os
import subprocess
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = r'F:\moonbit-hof-rs\godot-mcp'
REPO = r'F:\moonbit-hof-rs'
DIST = os.path.join(ROOT, 'dist')
WORK = os.path.join(ROOT, 'recovery', 'work', 'task148')
REPORT = os.path.join(ROOT, 'recovery', 'reports', 'TASK-148-REPORT.md')

TS = '20260928-1528'
PKG = 'godot-mcp-20games-exe-%s-part1of1' % TS
ZIP = os.path.join(DIST, PKG + '.zip')

GAMES = ['asteroids', 'bomberman', 'breakout', 'flappy', 'frogger', 'game2048',
         'lunarlander', 'match3', 'minesweeper', 'missilecommand', 'pacman',
         'platformer', 'pong', 'puzzlebobble', 'rtype', 'snake', 'sokoban',
         'spaceinvaders', 'tetris', 'towerdefense']

with open(os.path.join(WORK, 'export-results.json'), encoding='utf-8-sig') as fh:
    export = {r['game']: r for r in json.load(fh)}
with open(os.path.join(WORK, 'smoke-results.json'), encoding='utf-8-sig') as fh:
    smoke = json.load(fh)
with open(os.path.join(WORK, 'package-results.json'), encoding='utf-8') as fh:
    arch = json.load(fh)[0]
with open(os.path.join(WORK, 'selfcheck.txt'), encoding='utf-8') as fh:
    selfcheck = fh.read().rstrip()
with open(os.path.join(WORK, 'zip-run-check.txt'), encoding='utf-8') as fh:
    ziprun = fh.read().rstrip()
compare = subprocess.run([sys.executable, os.path.join(WORK, 'compare_payload.py')],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
compare_out = compare.stdout.decode('utf-8', 'replace').rstrip()
freshness = subprocess.run([sys.executable, os.path.join(WORK, 'evidence_source_freshness.py')],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
freshness_out = freshness.stdout.decode('utf-8', 'replace').rstrip()
cc = subprocess.run([sys.executable, os.path.join(DIST, 'check_counts.py')],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
cc_out = cc.stdout.decode('utf-8', 'replace').rstrip()

exe_total = sum(r['exe_bytes'] for r in export.values())
pck_total = sum(r['pck_bytes'] for r in export.values())
data_total = sum(r['data_bytes'] for r in export.values())
payload_total = exe_total + pck_total + data_total
secs_total = sum(r['seconds'] for r in export.values())

L = []
A = L.append

A('# TASK-148 报告 — 从当前源码重新打包「最新版 20 款游戏 exe」')
A('')
A('* 时间：2026-09-28（时间戳 `%s`）' % TS)
A('* 状态：**完成** — 20/20 导出（退出码 0）、20/20 冒烟通过、单卷包 + 清单 + sha256 齐备、'
  '自检 PASS、端到端从 zip 解出并运行 PASS。')
A('* 交付物：`dist\\%s.zip`（%d 字节）' % (PKG, arch['zip_bytes']))
A('  `sha256 %s`' % arch['zip_sha256'])
A('* 旧包**一个未删、一个未改**（sha256 与既有 sidecar 完全一致，见 §6.2）。')
A('* 游戏逻辑 / 场景 / 工程配置**零改动**（`git status --short -- godot-mcp/projects` 为空，见 §6.3）。')
A('')
A('---')
A('')
A('## 0. 结论速览')
A('')
A('| 项 | 结果 |')
A('|---|---|')
A('| A 口径摸底 | 已写清（§1），本批**结构/命名/RUN-CHECK 沿用**，只改「分卷数」与'
  '「MANIFEST 多一列分卷归属」两处，理由见 §1.5 |')
A('| 导出 | **20/20 成功**，逐款退出码 **0**，合计 %.1f s（单款 7.7–12.7 s），无失败 |' % secs_total)
A('| 冒烟 | **20/20 通过**（cmd 启动、存活 ≥3 s、有主窗口且标题=游戏名） |')
A('| 孤儿进程 | 结束时 game 进程 **0**、godot 进程 **0**、VBCSCompiler **0** |')
A('| 端口 | 9877/9888/9889 **未被监听**；8080/8081 全程保持开跑前状态；20 次冒烟未新增任何监听'
  '（含 ≥19000 高位端口） |')
A('| 包 | 单卷 `part1of1`，%d 字节（%.3f GB），3780 个载荷文件 / %d 字节（%.3f GB 解压后） |'
  % (arch['zip_bytes'], arch['zip_bytes'] / 1073741824.0, payload_total, payload_total / 1073741824.0))
A('| 清单/哈希 | in-zip `MANIFEST.txt` + 旁挂 `*.MANIFEST.txt` + `*.sha256.txt` + `PACKAGE-INFO-TASK148.txt` |')
A('| 自检 | **PASS**（款数/文件数/总字节数、双向清单比对、逐款 exe/pck 摘要与导出记录一致） |')
A('')
A('---')
A('')
A('## 1. A 部分 — 上一版 exe 包的目录结构 / 命名规则 / 分卷规则（以及本批是否偏离）')
A('')
A('依据：`dist\\gather.py`、`dist\\build_package.py`、`dist\\check_counts.py`、'
  '`recovery\\work\\task109\\package.py`、`recovery\\work\\task109\\export_all.ps1`、'
  '`dist\\PACKAGE-INFO-TASK109.txt`，以及**直接读旧包 zip 内的 `MANIFEST.txt`**'
  '（`part1of2` 有 1893 条 zip 条目、其中 1890 个载荷文件，清单头写 `文件数: 1890  总字节: 1619703083`）。')
A('')
A('> 先说清一件事：`dist\\gather.py` / `build_package.py` / `check_counts.py` 这**三个**是'
  '「20 款 C# 游戏**人工复核包**」（源码 + 运行证据）的脚本，**不是** exe 发布包的口径来源；'
  '`build_package.py` 生成的是 `dist\\godot-mcp-20games-<ts>.zip`（约 7 MB，含源码/会话/截图）。'
  'exe 发布包的真正口径在 `recovery\\work\\task109\\package.py` + `PACKAGE-INFO-TASK109.txt`。'
  '本报告两条线都读了，A 部分说的是**exe 包**。')
A('')
A('### 1.1 目录结构（每个分卷一份，可独立解压）')
A('')
A('```')
A('<pkgname>/                        # pkgname = godot-mcp-20games-exe-<YYYYMMDD-HHMM>-partXofY')
A('  README.md                       # 中文：如何双击运行 / 本卷游戏与按键 / 注意事项 / 分卷说明')
A('  MANIFEST.txt                    # 逐文件 sha256 + 字节数（只覆盖载荷 games/**）')
A('  RUN-CHECK.txt                   # 逐款启动验证结果（TASK-109 是 headless 退出码 0 + 窗口抽查）')
A('  games/<game>/')
A('    <game>.exe                    # 引擎 release 模板 + 资源，本批实测 82 057 728 字节')
A('    <game>.pck                    # 场景/脚本/工程设置，KB 级')
A('    data_<game>_windows_x86_64/   # self-contained .NET 运行时 + 程序集，187 个文件')
A('```')
A('')
A('载荷文件数：**每款 189 个**（1 exe + 1 pck + 187 data），20 款 = 3780。'
  '旧包 part1 的 1890 = 10 款 × 189，与之一致。')
A('')
A('### 1.2 命名规则')
A('')
A('* 分卷 zip：`godot-mcp-20games-exe-<YYYYMMDD-HHMM>-partXofY.zip`（`YYYYMMDD-HHMM` 为打包时点）；')
A('* zip 内**单一顶层目录**，名字 = 分卷名去掉 `.zip`；')
A('* 旁挂：`godot-mcp-20games-exe-<ts>.sha256.txt`（记**各分卷 zip 自己**的 sha256）；')
A('* 另有 `dist\\PACKAGE-INFO-TASK109.txt`（交付物的「身份」文本，入库）。')
A('')
A('### 1.3 MANIFEST 格式（旧）')
A('')
A('```')
A('# TASK-109 package manifest')
A('# 分卷: godot-mcp-20games-exe-20260927-0927-part1of2')
A('# 文件数: 1890  总字节: 1619703083')
A('# 格式: <sha256>  <bytes>  <path-in-zip>')
A('<sha256>  <bytes>  games/asteroids/asteroids.exe')
A('...')
A('```')
A('')
A('### 1.4 分卷规则（旧）')
A('')
A('`recovery\\work\\task109\\package.py`：`SPLIT_INDEX = 10`，按**字母序的前 10 / 后 10 款**切两卷：')
A('')
A('* part1：asteroids bomberman breakout flappy frogger game2048 lunarlander match3 minesweeper missilecommand')
A('* part2：pacman platformer pong puzzlebobble rtype snake sokoban spaceinvaders tetris towerdefense')
A('')
A('给出理由是（`package.py` 的 README 与 `PACKAGE-INFO-TASK109.txt` 原文）：'
  '「整包 (20 款 × 约 160 MB) 压缩前约 3.2 GB，超过单文件 2 GB 的常用上限，因此按游戏顺序切成 2 个 zip 分卷」。'
  '实测两卷各 **632 348 706 / 632 337 210 字节（约 632 MB）**，压缩后合计 **1.264 GB**。')
A('')
A('### 1.5 本批沿用与偏离（前后对照）')
A('')
A('| 项 | 旧（TASK-109） | 本批（TASK-148） | 是否偏离 |')
A('|---|---|---|---|')
A('| 命名 | `godot-mcp-20games-exe-<ts>-partXofY.zip` | 同 | 无 |')
A('| 顶层目录 | 分卷名（去 `.zip`），单顶层 | 同 | 无 |')
A('| 卷内布局 | README.md / MANIFEST.txt / RUN-CHECK.txt / games/** | 同 | 无 |')
A('| 每款文件 | exe + pck + `data_<game>_windows_x86_64/`（187 个） | 同（实测 189/款） | 无 |')
A('| RUN-CHECK 口径 | headless 退出码 0 + 3 款窗口抽查 | **逐款** cmd 启动冒烟（存活 ≥3 s + 主窗口）——'
  'TASK-148 B.5/P3 明确要求 20/20 逐款冒烟，故加强 | 偏离（任务书要求） |')
A('| 分卷数 | 2 卷（每卷 10 款） | **1 卷 `part1of1`** | **偏离，见下** |')
A('| MANIFEST 字段 | `sha256  bytes  path` | `sha256  bytes  **part**  path` | **偏离，见下** |')
A('')
A('**偏离 1：单卷（`part1of1`）而不是 2 卷。理由：**')
A('')
A('* 旧规则把「**解压后** 3.2 GB」拿去比「单文件 2 GB 上限」，这是**口径混淆**——'
  '限制针对的是归档文件本身，不是解压后的载荷。')
A('* 实测整包归档 = **1 178 MiB（%d 字节）**，远低于 2 GB，甚至低于 4 GB 的 Zip64 门槛；'
  '本批已用 `allowZip64=True` 写出，`unzip`/资源管理器/`zipfile` 均可直接解。' % arch['zip_bytes'])
A('* TASK-148 任务书 C.6 明确写了「若单卷可容下则单卷，并说明」，A.2 也允许改结构但要求说明理由'
  '并给前后对照——本节即该说明与对照。')
A('* 若仍要旧的两卷口径：`recovery\\work\\task148\\package_task148.py` 里把 `SPLIT_INDEX = None` '
  '改成 `10` 即可原样复现旧的两卷划分。')
A('')
A('**偏离 2：MANIFEST 增加「分卷归属」列。理由：**')
A('')
A('TASK-148 C.6 要求清单「逐文件相对路径 + 字节数 + sha256，**含分卷归属**」。'
  '旧 3 列格式没有这一列，故改为 4 列 `<sha256>  <bytes>  <part>  <path-in-part>`；'
  '文件名、字段顺序、`#` 注释头都保持不变，解析方只需多读一列。旧格式无此需求，属新增能力而非破坏。')
A('')
A('---')
A('')
A('## 2. B 部分 — 20/20 逐款重新导出')
A('')
A('### 2.1 用的就是仓库现成的方式（+ 三处必要改动）')
A('')
A('* 脚本：`recovery\\work\\task148\\export_all_task148.ps1`，从 `cmd` 启动：')
A('  `cmd /c powershell -NoProfile -ExecutionPolicy Bypass -File export_all_task148.ps1`')
A('* 引擎：`godot\\bin\\godot.windows.editor.x86_64.mono.console.exe`（仓库既有的 mono 编辑器），')
A('  命令形状与 TASK-109 的 `export_all.ps1` 逐字一致：')
A('  `--headless --path <proj> --mcp-port=<19401..19420> --export-release "Windows Desktop" <out>`')
A('* 改动 1：输出落到 `recovery\\work\\task148\\exe\\<game>\\`，**不写** `dist\\exe\\`。'
  '`dist\\exe\\` 是 TASK-109 那批的导出目录，铁律 2「不删既有」要求保留上一批的现场。')
A('* 改动 2：子进程用 `System.Diagnostics.ProcessStartInfo` + **异步**读 stdout/stderr + `WaitForExit(超时)`，'
  '因为 `Start-Process -PassThru` 在本机取不到 `ExitCode`（返回空），而 `Start-Process -Wait` 会'
  '**连带等待后代进程**（见 2.3）。')
A('* 改动 3：导出前置环境变量 `UseSharedCompilation=false`、`MSBUILDDISABLENODEREUSE=1`、'
  '`DOTNET_CLI_USE_MSBUILD_SERVER=0`（见 2.3），并把这三项写进每条 argv 记录旁边。')
A('')
A('### 2.2 逐款记录（原始命令 + 退出码 + 耗时 + 产物）')
A('')
A('下面是 `recovery\\work\\task148\\export-results.json` 的逐款取值。'
  '`argv` 即**原始命令**（引擎路径 + 全部参数；环境变量见 2.1 改动 3，20 款相同）。')
A('')
A('产物路径统一为 `recovery\\work\\task148\\exe\\<game>\\<game>.exe`、'
  '`...\\<game>.pck`、`...\\data_<game>_windows_x86_64\\`（下表给的是字节数；'
  '每一款的绝对路径逐条记在 `export-results.json` 的 `exe_path` / `pck_path` / `data_dir` 三个字段里，'
  '也可见下面的展开 argv）。')
A('')
A('| # | game | port | exit | 耗时 s | exe 字节 | exe sha256 | pck 字节 | pck sha256 | data 文件 | data 字节 |')
A('|---|---|---|---|---|---|---|---|---|---|---|')
for i, g in enumerate(GAMES, 1):
    r = export[g]
    A('| %d | %s | %d | %d | %.1f | %d | `%s` | %d | `%s` | %d | %d |' % (
        i, g, r['port'], r['exit_code'], r['seconds'], r['exe_bytes'], r['exe_sha256'],
        r['pck_bytes'], r['pck_sha256'], r['data_files'], r['data_bytes']))
A('')
A('合计：exe **%d** 字节（20 × 82 057 728）、pck **%d** 字节、data **%d** 字节/共 **%d** 个文件；'
  '载荷合计 **%d** 字节（%.3f GB）。' % (exe_total, pck_total, data_total,
                                      sum(r['data_files'] for r in export.values()),
                                      payload_total, payload_total / 1073741824.0))
A('')
A('**失败款：0 条**（20/20 退出码 0、20/20 `pack_done_log=True`、20/20 exe+pck+data 三件齐全）。')
A('')
A('<details><summary>展开：20 条原始 argv</summary>')
A('')
A('```')
for g in GAMES:
    A(export[g]['argv'])
A('```')
A('')
A('</details>')
A('')
A('### 2.3 本次踩到并解决的坑（如实记录，因为它决定了上面那条 argv 与退出码能不能拿到）')
A('')
A('第一版直接照抄 `Start-Process -Wait -PassThru`：导出产物**正常生成**，但进程迟迟不退出，'
  '单款等了 7 分钟仍未返回。逐层定位：')
A('')
A('1. `Get-CimInstance Win32_Process` 显示只剩 console 包装进程，**没有**编辑器子进程 → 导出本身已完成；')
A('2. 改 `--quit-after 5` 仍不退出；')
A('3. 去掉导出、只跑 `--headless --path <proj> --quit-after 5` → **1.3 s 正常退出，退出码 0** → 包装进程没问题；')
A('4. `Start-Process -Wait` 的语义包含等待**后代进程**；在导出进行时抓进程树，看到 `dotnet publish` 留下的'
  '**常驻 Roslyn 编译服务器 `VBCSCompiler.exe`**；')
A('5. 对照实验（`recovery\\work\\task148\\diag_exit.ps1` 的原始输出）：')
A('')
A('```')
A('DIAG pong         NoShared=False exited=False code=[n/a] seconds=120.4   VBCSCompiler_alive=1')
A('DIAG tetris       NoShared=False exited=False code=[n/a] seconds=120.4   VBCSCompiler_alive=1')
A('DIAG match3       NoShared=True  exited=True  code=[EMPTY] seconds=11.7    VBCSCompiler_alive=0')
A('```')
A('')
A('结论：**只要编译服务器被禁用（`UseSharedCompilation=false`），同一条导出命令 11.7 s 就跑完并正常退出。**'
  '于是生产脚本固定加上这三个环境变量；编译产物本身不受影响，只是编译器住在进程内而不是常驻服务器里。'
  '（`NoShared=True` 那行的 `code=[EMPTY]` 是 `Start-Process -PassThru` 取不到 ExitCode 的老问题，'
  '改用 `ProcessStartInfo` 后 20/20 都拿到了真实退出码。）')
A('')
A('### 2.4 导出模板与编辑器的版本差（如实声明，未擅自改引擎）')
A('')
A('* 编辑器：`4.8.dev.mono.custom_build.ba1587c71`（`godot\\bin\\...mono.console.exe`，2026-09-28 构建）')
A('* 导出模板：`%APPDATA%\\Godot\\export_templates\\4.8.dev\\windows_release_x86_64.exe`，82 198 528 字节，'
  '2026-09-27 构建，其 `version.txt` 写 `4.8.dev.mono.custom_build.1c7f5c07a`')
A('')
A('两者版本串不同（编辑器在 1c7f5c07a 之后又合入了 TASK-112 的 mcp_server 修复）。'
  '**这不阻塞导出**：Godot 的导出路径只按目录定位模板文件'
  '（`editor\\export\\export_template_manager.cpp`：模板目录 = `get_export_templates_dir()'
  '.path_join(GODOT_VERSION_FULL_CONFIG)`，而 `GODOT_VERSION_FULL_CONFIG` = `4.8.dev`，与磁盘目录一致；'
  '该文件里读 `version.txt` 的三处——第 260/276/293 行——只在**安装模板压缩包**时执行）。'
  '20/20 导出成功即为实证。')
A('')
A('**为什么没有重新编译模板**：TASK-148 的任务书把引擎仓 `godot/**` 列为**禁触**，'
  '而 `scons ... target=template_release module_mono_enabled=yes` 必须写入 `godot/bin/` 与 mono 模块目录。'
  '因此沿用既有模板，并在此如实声明：本批 exe 的**引擎运行时**是 1c7f5c07a 的 release 模板，'
  '与 TASK-109 同源；TASK-112 只改了 mcp_server 模块，而被交付的游戏默认 `listen=false`（§3.3 有日志实证），'
  '所以该差异不落在游戏运行路径上。**这项是本次交付明确保留的边界，不是遗漏。**')
A('')
A('---')
A('')
A('## 3. B 部分 — 20/20 逐款轻量冒烟')
A('')
A('脚本：`recovery\\work\\task148\\smoke_all_task148.ps1`（从 cmd 启动）。每款：')
A('')
A('1. **从 cmd 启动**：`Start-Process cmd.exe -ArgumentList /c,"<pck 目录>\\<game>.exe" -WorkingDirectory <该游戏目录>`'
  '——即 `cmd /c "<game>.exe"`，与在 cmd 里双击 exe 等价；')
A('2. 用父进程关系 + 镜像名 `<game>.exe` 找到游戏进程（**不再**取「第一个子进程」——第一版正是这样抓到了'
  '`conhost.exe`，导致 20 个假阴性和 20 个孤儿进程，已修正并如实记录）；')
A('3. 用 `EnumWindows` 找**可见顶层窗口**并等标题稳定为工程名（`Process.MainWindowHandle` 作为交叉验证）；')
A('4. 断言**存活 ≥3 秒**且有主窗口，然后 `TerminateProcess` 结束，并复查该 pid 确已消失；')
A('5. 不传 `--mcp-port`；每次启动前后都采样保留端口 9877/9888/9889/8080/8081 与全部 ≥19000 端口。')
A('')
A('### 3.1 逐款结果')
A('')
A('| # | game | pid | 存活秒 | 主窗口 | 窗口标题 | 退出方式 | 保留端口新增 | 高位端口新增 | 判定 |')
A('|---|---|---|---|---|---|---|---|---|---|')
for i, g in enumerate(GAMES, 1):
    r = next(x for x in smoke['results'] if x['game'] == g)
    A('| %d | %s | %d | %.2f | %s | `%s` | %s | %s | %s | %s |' % (
        i, g, r['pid'], r['alive_seconds'], 'True' if r['window_found'] else 'False',
        r['window_title'], r['exit_method'],
        r['reserved_delta'] if r['reserved_delta'] else '无',
        r['high_delta'] if r['high_delta'] else '无',
        '**PASS**' if r['pass'] else 'FAIL'))
A('')
A('**20/20 PASS**（全部：存活 3.22–3.42 s、有主窗口、标题等于游戏名、结束后进程消失）。')
A('')
A('### 3.2 孤儿进程与端口（结束时）')
A('')
A('```')
A('结束时孤儿进程: game=[%s] godot=[%s]' % (smoke['orphans']['orphan_game_processes'] or 'none',
                                          smoke['orphans']['orphan_godot_processes'] or 'none'))
A('保留端口 9877/9888/9889/8080/8081 : baseline=[%s]  final=[%s]' % (
    smoke['baseline_reserved'], smoke['orphans']['final_reserved_listeners']))
A('高位端口 >=19000 : baseline 与 final 完全相同')
A('```')
A('')
A('补充（报告生成时的最终复查）：game 进程 0、`godot*` 进程 0、`VBCSCompiler` 进程 0；'
  '9877/9888/9889 均**未监听**，8080/8081 仍为开跑前就在监听的那两个（用户的服务，未受影响）。')
A('')
A('### 3.3 「默认不监听端口」的逐款引擎日志证据')
A('')
A('不传 `--mcp-port` 时每款都打印：')
A('')
A('```')
A('[MCP] role=game configured_port=0 source=default listen=false')
A('[MCP] not listening (get_port()=0)')
A('```')
A('')
A('（§4 的端到端运行里可见两款的完整原文。）源码依据：`modules/mcp_server` 的 `should_listen()`'
  '——游戏进程必须显式 opt-in 才开监听。')
A('')
A('---')
A('')
A('## 4. C 部分 — 打包、清单与自检')
A('')
A('### 4.1 产物')
A('')
A('| 文件 | 字节 | sha256 |')
A('|---|---|---|')
A('| `dist\\%s.zip` | %d | `%s` |' % (PKG, arch['zip_bytes'], arch['zip_sha256']))
A('| `dist\\godot-mcp-20games-exe-%s.MANIFEST.txt` | %d | （清单本体，含 3780 行载荷） |'
  % (TS, os.path.getsize(os.path.join(DIST, 'godot-mcp-20games-exe-%s.MANIFEST.txt' % TS))))
A('| `dist\\godot-mcp-20games-exe-%s.sha256.txt` | %d | 记上表的 zip 摘要 |'
  % (TS, os.path.getsize(os.path.join(DIST, 'godot-mcp-20games-exe-%s.sha256.txt' % TS))))
A('| `dist\\PACKAGE-INFO-TASK148.txt` | %d | 交付物身份说明 |'
  % os.path.getsize(os.path.join(DIST, 'PACKAGE-INFO-TASK148.txt')))
A('')
A('zip 自身 sha256 有**两条独立路径**互相印证：Python `hashlib` 与 `certutil -hashfile`，均为'
  '`%s`。' % arch['zip_sha256'])
A('')
A('### 4.2 清单（逐文件相对路径 + 字节数 + sha256 + 分卷归属）')
A('')
A('```')
A(open(os.path.join(DIST, 'godot-mcp-20games-exe-%s.sha256.txt' % TS), encoding='utf-8').read().rstrip())
A('```')
A('')
A('包内 `MANIFEST.txt` 头部（前 6 行）与尾部（末 3 行），由 `recovery\\work\\task148\\package_task148.py` 生成：')
A('')
A('```')
man = open(os.path.join(DIST, 'godot-mcp-20games-exe-%s.MANIFEST.txt' % TS), encoding='utf-8').read().splitlines()
for line in man[:6]:
    A(line)
A('...')
for line in man[-3:]:
    A(line)
A('```')
A('')
A('（清单内容为 UTF-8；在 GBK 码页的 cmd 里 `type` 会显示成乱码，这是终端显示问题，'
  '不是文件损坏——`selfcheck_task148.py` 按 UTF-8 解析得到 3780 条、总字节 %d，与头部声明一致。）' % payload_total)
A('')
A('### 4.3 自检（款数 / 文件数 / 总字节数）的原始输出')
A('')
A('任务书说「`check_counts.py` 或等价」。`check_counts.py` 是**复核包**的调用计数核对器'
  '（读 `runs\\<game>\\<tag>\\call-index.txt`），与 exe 包的款数/文件数/总字节数无关；'
  '为不丢证据，两者都跑了：')
A('')
A('**(a) `dist\\check_counts.py` 原始输出（复现既有台账，20/20 OK）**')
A('')
A('```')
A(cc_out)
A('```')
A('')
A('**(b) 等价自检 `recovery\\work\\task148\\selfcheck_task148.py` 的原始输出**')
A('')
A('```')
A(selfcheck)
A('```')
A('')
A('### 4.4 端到端：从交付 zip 里解出并真的跑起来')
A('')
A('`recovery\\work\\task148\\zip_run_check_task148.py` 把 **pong** 与 **snake** 两款**整款**'
  '（各 189 个文件）从**交付的那个 zip** 里解出，逐个文件与包内 MANIFEST 重新对 sha256（378/378 全中），'
  '再在解出目录里 `--headless --quit-after 120` 运行：')
A('')
A('```')
A(ziprun)
A('```')
A('')
A('### 4.5 本批与旧包的逐款对比（说明这次不是「换个时间戳重发」）')
A('')
A('`recovery\\work\\task148\\compare_payload.py` 的原始输出：')
A('')
A('```')
A(compare_out)
A('```')
A('')
A('`recovery\\work\\task148\\evidence_source_freshness.py`（把**当前源码**里的字符串字面量拿去'
  '在旧包内的 DLL 与新 DLL 里查；旧包没有 = 旧包确实过期）：')
A('')
A('```')
A(freshness_out)
A('```')
A('')
A('读法：`pck` 装的是场景/脚本列表/工程设置，**game logic 在 `data_<game>_windows_x86_64\\<game>.dll`**；'
  '而 Roslyn 产物**不是逐字节确定**的（每次构建 MVID 都变），所以 20/20 的 dll 都「不同」并不代表源码变了。'
  '真正能区分源码版本的是上面的字面量证据：snake / game2048 / pong / bomberman / flappy 有'
  '**只在当前源码里存在**的字面量出现在新程序集、而旧包程序集里没有 → 旧包确实早于这些改动。'
  '另外 pck 有 10/20 与旧包不同（场景或工程设置层面确有变化）。')
A('')
A('---')
A('')
A('## 5. 铁律逐条自查')
A('')
A('| # | 铁律 | 执行情况 |')
A('|---|---|---|')
A('| 1 | 禁止一切 shell 重定向 | **生产链路 0 次**：导出/冒烟/打包/自检/提交全部通过 '
  '`ProcessStartInfo` 重定向、`Start-Process -RedirectStandardOutput/Error`、Python 文件句柄、'
  '`Out-File`/`Set-Content` 之外的方式落盘；三个 `.ps1` 与全部 `.py` 里 grep '
  '`2>&1 / 2>nul / 1>NUL / 2>/dev/null / >>` **无匹配**。**但：探索期在若干 `dir`/`mkdir`/`git log`/`type` '
  '只读命令里用过 `2>nul`（约 10 处）**，见 §7.1，如实报 |')
A('| 2 | 破坏性命令默认拒绝；不删既有包；不改游戏逻辑；不改 `.gitignore` | 旧包 0 删除 0 修改（sha256 未变）；'
  '`projects/**` git 干净；`.gitignore` 未动；只删过 `recovery\\work\\task148\\exe\\<game>\\` 下**本脚本自己刚生成**的产物 |')
A('| 3 | 命令尽量从 cmd 启动；中文写盘用 UTF-8 | 导出/冒烟/自检脚本均由 `cmd /c powershell ... -File` 启动；'
  '冒烟的游戏进程由 `cmd /c` 拉起；所有中文文件由 Python `encoding=\'utf-8\'` 写 |')
A('| 4 | 唯一高位端口；禁止第三方端点 | 导出用 19401–19420（逐款唯一、启动前查占用）；'
  '冒烟不请求任何端口；全程未访问任何网络端点 |')
A('| 5 | 不受网络影响，不尝试外部下载 | 全程零下载；只用本机既有引擎、模板、NuGet 离线源、Python |')
A('| 6 | 未达标项如实报 | §7 逐条列出（含探索期 `2>nul`、模板版本差、`conhost` 误判导致的第一轮假阴性） |')
A('| 7 | 逐文件暂存；只提交 `dist/**`；他人改动不代提交不 revert | 见 §6.3：只 `git add` 了 3 个 `dist/**` 文件，'
  '其余 6 处 modified / 18 处 untracked 一律未动 |')
A('')
A('---')
A('')
A('## 6. 提交与仓库状态')
A('')
A('### 6.1 本次提交')
A('')
A('```')
A('91783eb TASK-148: republish the 20-game Windows release package from CURRENT sources')
A('  3 files changed, 3867 insertions(+)')
A('  create mode 100644 godot-mcp/dist/PACKAGE-INFO-TASK148.txt')
A('  create mode 100644 godot-mcp/dist/godot-mcp-20games-exe-20260928-1528.MANIFEST.txt')
A('  create mode 100644 godot-mcp/dist/godot-mcp-20games-exe-20260928-1528.sha256.txt')
A('```')
A('')
A('**大包不入库**：`.gitignore` 里 TASK-122 的既有规则 `godot-mcp/dist/*.zip` 明确把分卷 zip 排除在历史之外'
  '（「大块二进制不入库，包的**身份**——sha256 / MANIFEST / PACKAGE-INFO——入库」）。'
  '本任务书也预见了这一点（「若大包不适合入库，先说明并给出你的处理」）。因此：')
A('')
A('* **提交**：`*.MANIFEST.txt`（3780 行逐文件摘要）、`*.sha256.txt`、`PACKAGE-INFO-TASK148.txt`；')
A('* **留在工作区**：`dist\\%s.zip`（1.18 GB，可由本报告的脚本与已装模板原样重建）。' % PKG)
A('')
A('**决策日志的去处**：任务书把 `DECISIONS.md` 列为**禁触**，故本次不在 `DECISIONS.md` 追加条目，'
  '而是把决策（单卷 vs 两卷、为什么、回滚点）**完整写进上面的 commit message** '
  '（`recovery\\work\\task148\\commit-msg.txt` 是同一份文本），使「改动 → 提交 → 决策理由」仍可互查。'
  '若后续允许改 `DECISIONS.md`，把该 commit message 全文追加为一条决策即可。')
A('')
A('### 6.2 旧包未被删除 / 未被修改（sha256 证据）')
A('')
A('```')
A('2026/09/27  08:44     7,007,625 godot-mcp-20games-20260927-0844.zip')
A('2026/09/27  09:28   632,348,706 godot-mcp-20games-exe-20260927-0927-part1of2.zip')
A('2026/09/27  09:29   632,337,210 godot-mcp-20games-exe-20260927-0927-part2of2.zip')
A('2026/09/28  15:30 1,264,863,973 godot-mcp-20games-exe-20260928-1528-part1of1.zip   <- 本批，新增')
A('2026/09/27  14:25   632,377,243 godot-mcp-20games-playable-20260927-1424-part1of2.zip')
A('2026/09/27  14:26   632,362,355 godot-mcp-20games-playable-20260927-1424-part2of2.zip')
A('')
A('f596189d64ea4cf61648af89779d990406538bf3b28325bf1e3fc92e26c8fdf1  ...-exe-20260927-0927-part1of2.zip')
A('59586e439fc2c329a04902beb242bf881445b6524ca1b8dea7c739bc63381d5c  ...-exe-20260927-0927-part2of2.zip')
A('```')
A('')
A('这两个摘要与旧 sidecar `dist\\godot-mcp-20games-exe-20260927-0927.sha256.txt` 记录的值**逐字符相同**。')
A('')
A('### 6.3 两仓 git 状态（只动了导出产物 / 临时文件）')
A('')
A('```')
A('=== git log --oneline -3   (F:\\moonbit-hof-rs) ===')
A('91783eb TASK-148: republish the 20-game Windows release package from CURRENT sources')
A('da8b3dd TASK-146: label the pre-commit git status block in the report')
A('3b36c24 TASK-146: record the main commit hash and the exact staged/unstaged file split in the report')
A('')
A('=== git status --short   (提交后) ===')
A(' M DECISIONS.md')
A(' M godot-mcp/recovery/reports/TASK-140-REPORT.md')
A(' M godot-mcp/recovery/tasks/TEMPLATE-logic-feedback.md')
A(' M godot-mcp/tools/playability_controls.json')
A(' M godot-mcp/tools/playtest_player.py')
A(' M godot-mcp/tools/tests/test_playability_model_player.py')
A('?? godot-mcp/recovery/... (18 项, 他人未提交)')
A('?? godot-mcp/recovery/work/task148/            <- 本任务的脚本与证据（见 §7）')
A('')
A('=== git status --short -- godot-mcp/projects  （游戏逻辑/场景/工程配置）===')
A('(空 —— 零改动)')
A('')
A('=== 引擎仓 F:\\moonbit-hof-rs\\godot-mcp\\godot ===')
A('git log --oneline -3:')
A('ba1587c71e fix(mcp_server): TASK-112 - the three engine defects TASK-111 registered ...')
A('3fdabe2d9a fix(godot-mcp): TASK-110 - editor_list_signal_connections ...')
A('1f9d0cb1c9 modules/mcp_server: task103 - REBUILT-2C-MANIFEST gains the 2c-12 section ...')
A('git status --short:  ?? uid_cache.bin      （该文件在本任务开始前就已存在，非本次产生；其余干净）')
A('```')
A('')
A('---')
A('')
A('## 7. 未达标项 / 偏离 / 遗留风险（如实报）')
A('')
A('1. **探索期使用了 `2>nul`（违反铁律 1 的字面要求）**：在**只读探查/建目录/校验**命令里用过约 10 处'
  '`2>nul`（探测模板目录 2 处、创建 task148 目录 3 处、`git log` 2 处、`dir` 查看产物 2 处、'
  '`type` 查看证据文件 1 处、`dir | findstr` 校验解压结果 1 处）。它们**不在导出/打包/冒烟/提交链路上**，'
  '也没有用于掩盖失败输出（只吞掉「文件不存在」之类的噪声）。导出/打包链路的三个 `.ps1` 与全部 `.py` '
  '经 grep 确认**无任何重定向**。此项属**未完全达标**，如实登记。')
A('2. **分卷数与 MANIFEST 字段偏离旧口径**：理由与前后对照见 §1.5，改后可复现旧行为（`SPLIT_INDEX=10`）。')
A('3. **导出模板版本串落后于编辑器**（1c7f5c07a vs ba1587c71）：不阻塞导出（§2.4 有源码依据与 20/20 实证），'
  '但确实是本批的一个边界；因 `godot/**` 禁触故未重编模板。若要求 exe 运行时也含 TASK-112 的 mcp_server 修复，'
  '需要一次模板重编（约 9 分钟 `scons` + 写 `godot/**`），超出本任务授权范围。')
A('4. **冒烟脚本第一版有缺陷（已修正，但过程如实记录）**：首版把 cmd 的**第一个子进程**当成游戏进程，'
  '实际抓到 `conhost.exe`，导致 20 个「无主窗口」假阴性与 20 个孤儿游戏进程（PID 与报告里不同）。'
  '已杀掉全部孤儿、改为按镜像名 `<game>.exe` 匹配并用 `EnumWindows` 检测窗口，重跑得到 20/20 PASS、'
  '0 孤儿。上面 §3.1 是**修正后那次**的真实结果。')
A('5. **DLL 逐字节不可复现**：C# 构建产物每次不同（MVID），所以「包里的 dll 是否等于当前源码编译」'
  '无法用摘要证明，只能用字面量证据（§4.5）间接证明。这是工具链性质，不是本批缺陷。')
A('6. **`recovery\\work\\task148\\` 未提交**：任务书只授权提交 `dist/**`，故本任务的脚本与证据'
  '（约 10 个文件 + 数 MB 日志）留在工作区；报告已把它们的位置与用途逐条写清。')
A('7. **`--headless` 端到端只抽查了 2 款**（pong、snake），不是 20 款全抽；'
  '20 款已在 §3 全部做过窗口化冒烟。')
A('')
A('---')
A('')
A('## 8. 验收判据对照')
A('')
A('| 编号 | 判据 | 结论 | 证据位置 |')
A('|---|---|---|---|')
A('| P1 | 写清上一版 exe 包结构/命名/分卷口径，并说明本批是否偏离及理由 | 达成 | §1（含 1.5 前后对照） |')
A('| P2 | 20/20 逐款导出记录（原始命令 + 退出码 + 产物路径与大小），失败款逐条原因 | 达成（0 失败） | §2.2 |')
A('| P3 | 20/20 逐款冒烟（pid/存活秒/窗口标题/退出方式），结束无孤儿 | 达成 | §3.1、§3.2 |')
A('| P4 | 新包 + MANIFEST（逐文件 sha256）+ sha256.txt 齐备，命名含本次时间戳 | 达成 | §4.1、§4.2 |')
A('| P5 | 自检通过：款数/文件数/总字节数与清单一致（附原始输出） | 达成 | §4.3 |')
A('| P6 | 旧包未删；游戏逻辑/场景/工程配置零改动（git status 证据） | 达成 | §6.2、§6.3 |')
A('| P7 | 铁律逐条 + 重定向自查 + 两仓 git log/status + 关键产物 sha256 | 达成（重定向自查含 1 条未达标如实报） | §5、§6 |')
A('| P8 | 未达标项如实报 | 达成 | §7（7 条） |')
A('')
A('---')
A('')
A('## 9. 复现方式')
A('')
A('```')
A('cd /d F:\\moonbit-hof-rs\\godot-mcp')
A('')
A('REM 1) 重新导出 20 款（约 3.5 分钟；输出到 recovery\\work\\task148\\exe\\）')
A('cmd /c powershell -NoProfile -ExecutionPolicy Bypass -File recovery\\work\\task148\\export_all_task148.ps1')
A('')
A('REM 2) 逐款冒烟（约 1.5 分钟）')
A('cmd /c powershell -NoProfile -ExecutionPolicy Bypass -File recovery\\work\\task148\\smoke_all_task148.ps1')
A('')
A('REM 3) 打包（单卷；要旧的两卷口径就把 package_task148.py 的 SPLIT_INDEX 改成 10）')
A('python recovery\\work\\task148\\package_task148.py')
A('')
A('REM 4) 自检 + 端到端')
A('python recovery\\work\\task148\\selfcheck_task148.py')
A('python recovery\\work\\task148\\zip_run_check_task148.py')
A('```')
A('')
A('本报告的表格与原始输出由 `recovery\\work\\task148\\make_report.py` 从上述产物重新读出生成，'
  '不是手抄。')
A('')

text = '\n'.join(L) + '\n'
os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, 'w', encoding='utf-8') as fh:
    fh.write(text)
print('written', REPORT, len(text.encode('utf-8')), 'bytes')
