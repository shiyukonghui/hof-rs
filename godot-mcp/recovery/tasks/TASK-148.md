# TASK-148 — 从当前源码重新打包「最新版 20 款游戏 exe」

> 子代理**只读本文件**执行；报告 `recovery\reports\TASK-148-REPORT.md`，**只返回路径 + 一行状态**。
> **严格单线程**：不得再派子代理。**禁止 shell 重定向**（`>`/`>>`/`2>&1`/`2>nul`/`1>NUL`/`2>/dev/null`）。
> **独占**：`dist/**`（新包与清单）、`recovery/work/task148/**`、`projects/<game>/**` **仅限导出产物与构建临时文件**（**不得改游戏逻辑/场景/工程配置**）、`recovery/reports/TASK-148-REPORT.md`、`recovery/tasks/TASK-148.md`。
> **禁触**：`DECISIONS.md`、`recovery/**` 其它文件、`tools/**`、引擎仓 `godot/**`、`F:\models\**`、两个 venv、8080/8081、`.gitignore`、`recovery/tasks/README.md`。

---

## 0. 背景与依据（用户裁定）

* 主线是**好用的 MCP 工具**；本次要的是一次**发布打包**：**只要 20 款游戏的 Windows 发布版导出**（**不要**工具载荷、不要源码包）。
* 既有包在 `godot-mcp/dist/`（**已过期**）：`godot-mcp-20games-exe-20260927-0927-part{1,2}of2.zip`（各 ~632 MB）、
  `godot-mcp-20games-playable-20260927-1424-part{1,2}of2.zip`（各 ~632 MB）+ `MANIFEST.txt` + `sha256.txt`；
  配套脚本 `dist/build_package.py`、`dist/gather.py`、`dist/check_counts.py`；TASK-109 的导出脚本 `recovery/work/task109/export_all.ps1`、`package.py`。
* **过期原因**：其后 TASK-133/135/136/140 改过这些游戏的**源码**（snake / game2048 / pong / puzzlebobble / platformer / asteroids / frogger / bomberman / flappy）
  ⇒ 旧包里的 exe **不是**当前源码的产物，必须重新导出。
* 工程：`projects/` 下 **20 个**带 `export_presets.cfg` 的游戏（另有 2 个 `_` 前缀目录**不算**）。

---

## 1. 目标

### A. 先摸清既有包的结构与打包口径（**沿用，不要另起一套**）
1. 读 `dist/gather.py`、`dist/build_package.py`、`dist/check_counts.py` 与既有 `MANIFEST.txt`，
   **写清**上一版 exe 包的**目录结构**（每款含哪些文件：`.exe`、`.pck`、`data_*`、`lib`、`*.json` 等）、**命名规则**、**分卷规则**（为何 2 卷、每卷上限）。
2. **以既有结构为基准**产出本批包（若你判断既有结构有缺陷，**改**可以，但必须**说明理由**并在报告里给前后对照）。

### B. 重新导出 20 款（当前源码）
3. 用**仓库里现成的方式**导出（优先复用 `recovery/work/task109/export_all.ps1` 或等价流程；Godot 编辑器二进制用既有 mono 版），
   **逐款**导出 Windows 发布版；**不得改任何游戏逻辑/场景/工程配置**（只允许生成导出产物与构建临时文件）。
4. **逐款记录**：命令（原始 argv）、退出码、产物路径与大小、导出耗时；失败的款**逐条列失败原因**，**不得跳过或假装成功**。
5. **导出后做轻量冒烟**（每款一次）：从 **cmd** 启动该 exe、确认**进程存活 ≥3 秒且有主窗口**、然后**结束该进程**；
   逐款给 `pid / 存活秒数 / 窗口标题 / 退出方式`。**不得**残留进程（结束时确认无孤儿 godot 进程）。
   * 需要端口时用**唯一高位端口**（避开 9877/9888/9889/8080/8081），并在启动前查占用。

### C. 打包与清单
6. 产出（命名沿用既有惯例，时间戳用**本次**时点）：
   * `dist/godot-mcp-20games-exe-<YYYYMMDD-HHMM>-partXofY.zip`（分卷规则同既有；若单卷可容下则单卷，并说明）；
   * `dist/godot-mcp-20games-exe-<YYYYMMDD-HHMM>.MANIFEST.txt`（逐文件**相对路径 + 字节数 + sha256**，含分卷归属）；
   * `dist/godot-mcp-20games-exe-<YYYYMMDD-HHMM>.sha256.txt`（各分卷 sha256）。
7. **自检**：`check_counts.py` 或等价核对（**20 款、文件数、总字节数**与清单一致）；把核对**原始输出**贴进报告。

---

## 2. 硬性约束（铁律）

1. **禁止一切 shell 重定向**；用 `-o`/`-OutFile`/Python 句柄；如可用既有台账机制则沿用并给自查数字。
2. **破坏性命令默认拒绝**；**不删既有包**（`dist/` 里旧包保留，新包并存）；不改游戏逻辑；不改 `.gitignore`。
3. 命令尽量**从 cmd 启动**；中文写盘乱码用 cmd/bash 或 Python UTF-8。
4. 唯一高位端口；禁止第三方端点。
5. 不受网络影响：**不得**尝试外部下载；一切用本机既有工具链。
6. **未达标项如实报**（哪款没导出成功、哪款冒烟失败、为什么）；不得"应该可以"。
7. 提交：**逐文件暂存**；只提交 `dist/**` 新包（若体积大不适合入库，**先说明**并给出你的处理，例如提交清单与 sha256、把大包留在工作区）；
   他人未提交改动（`DECISIONS.md`、`playability_*`、`ACCEPTANCE-*`、`TASK-14x.md` 等）**一律不代提交、不 revert**。

---

## 3. 验收判据

| 编号 | 判据 |
|---|---|
| P1 | 已写清上一版 exe 包的目录结构/命名/分卷口径，并说明本批是否偏离及理由 |
| P2 | **20/20 逐款**导出记录（原始命令 + 退出码 + 产物路径与大小），失败款逐条给原因 |
| P3 | **20/20 逐款冒烟**结果（pid/存活秒数/窗口标题/退出方式），且**结束时无孤儿进程** |
| P4 | 新包 + `MANIFEST.txt`（逐文件 sha256）+ `sha256.txt` 齐备，命名含本次时间戳 |
| P5 | 自检通过：款数/文件数/总字节数与清单一致（附原始输出） |
| P6 | 旧包未被删除；游戏逻辑/场景/工程配置**零改动**（给 `git status` 证据证明只动了导出产物/临时文件） |
| P7 | 铁律逐条 + 重定向自查 + 两仓 `git log --oneline -3` / `git status --short` + 关键产物路径与 sha256 |
| P8 | 未达标项如实报 |

---

## 4. 报告落点

* `F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-148-REPORT.md`；**只返回路径 + 一行状态**。