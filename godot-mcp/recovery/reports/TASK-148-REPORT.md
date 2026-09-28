# TASK-148 报告 — 从当前源码重新打包「最新版 20 款游戏 exe」

* 时间：2026-09-28（时间戳 `20260928-1528`）
* 状态：**完成** — 20/20 导出（退出码 0）、20/20 冒烟通过、单卷包 + 清单 + sha256 齐备、自检 PASS、端到端从 zip 解出并运行 PASS。
* 交付物：`dist\godot-mcp-20games-exe-20260928-1528-part1of1.zip`（1264863973 字节）
  `sha256 bc28ad360c105920cf25be9672814659232e76fb859a16cb3ac9c056584a84b4`
* 旧包**一个未删、一个未改**（sha256 与既有 sidecar 完全一致，见 §6.2）。
* 游戏逻辑 / 场景 / 工程配置**零改动**（`git status --short -- godot-mcp/projects` 为空，见 §6.3）。

---

## 0. 结论速览

| 项 | 结果 |
|---|---|
| A 口径摸底 | 已写清（§1），本批**结构/命名/RUN-CHECK 沿用**，只改「分卷数」与「MANIFEST 多一列分卷归属」两处，理由见 §1.5 |
| 导出 | **20/20 成功**，逐款退出码 **0**，合计 204.0 s（单款 7.7–12.7 s），无失败 |
| 冒烟 | **20/20 通过**（cmd 启动、存活 ≥3 s、有主窗口且标题=游戏名） |
| 孤儿进程 | 结束时 game 进程 **0**、godot 进程 **0**、VBCSCompiler **0** |
| 端口 | 9877/9888/9889 **未被监听**；8080/8081 全程保持开跑前状态；20 次冒烟未新增任何监听（含 ≥19000 高位端口） |
| 包 | 单卷 `part1of1`，1264863973 字节（1.178 GB），3780 个载荷文件 / 3239466195 字节（3.017 GB 解压后） |
| 清单/哈希 | in-zip `MANIFEST.txt` + 旁挂 `*.MANIFEST.txt` + `*.sha256.txt` + `PACKAGE-INFO-TASK148.txt` |
| 自检 | **PASS**（款数/文件数/总字节数、双向清单比对、逐款 exe/pck 摘要与导出记录一致） |

---

## 1. A 部分 — 上一版 exe 包的目录结构 / 命名规则 / 分卷规则（以及本批是否偏离）

依据：`dist\gather.py`、`dist\build_package.py`、`dist\check_counts.py`、`recovery\work\task109\package.py`、`recovery\work\task109\export_all.ps1`、`dist\PACKAGE-INFO-TASK109.txt`，以及**直接读旧包 zip 内的 `MANIFEST.txt`**（`part1of2` 有 1893 条 zip 条目、其中 1890 个载荷文件，清单头写 `文件数: 1890  总字节: 1619703083`）。

> 先说清一件事：`dist\gather.py` / `build_package.py` / `check_counts.py` 这**三个**是「20 款 C# 游戏**人工复核包**」（源码 + 运行证据）的脚本，**不是** exe 发布包的口径来源；`build_package.py` 生成的是 `dist\godot-mcp-20games-<ts>.zip`（约 7 MB，含源码/会话/截图）。exe 发布包的真正口径在 `recovery\work\task109\package.py` + `PACKAGE-INFO-TASK109.txt`。本报告两条线都读了，A 部分说的是**exe 包**。

### 1.1 目录结构（每个分卷一份，可独立解压）

```
<pkgname>/                        # pkgname = godot-mcp-20games-exe-<YYYYMMDD-HHMM>-partXofY
  README.md                       # 中文：如何双击运行 / 本卷游戏与按键 / 注意事项 / 分卷说明
  MANIFEST.txt                    # 逐文件 sha256 + 字节数（只覆盖载荷 games/**）
  RUN-CHECK.txt                   # 逐款启动验证结果（TASK-109 是 headless 退出码 0 + 窗口抽查）
  games/<game>/
    <game>.exe                    # 引擎 release 模板 + 资源，本批实测 82 057 728 字节
    <game>.pck                    # 场景/脚本/工程设置，KB 级
    data_<game>_windows_x86_64/   # self-contained .NET 运行时 + 程序集，187 个文件
```

载荷文件数：**每款 189 个**（1 exe + 1 pck + 187 data），20 款 = 3780。旧包 part1 的 1890 = 10 款 × 189，与之一致。

### 1.2 命名规则

* 分卷 zip：`godot-mcp-20games-exe-<YYYYMMDD-HHMM>-partXofY.zip`（`YYYYMMDD-HHMM` 为打包时点）；
* zip 内**单一顶层目录**，名字 = 分卷名去掉 `.zip`；
* 旁挂：`godot-mcp-20games-exe-<ts>.sha256.txt`（记**各分卷 zip 自己**的 sha256）；
* 另有 `dist\PACKAGE-INFO-TASK109.txt`（交付物的「身份」文本，入库）。

### 1.3 MANIFEST 格式（旧）

```
# TASK-109 package manifest
# 分卷: godot-mcp-20games-exe-20260927-0927-part1of2
# 文件数: 1890  总字节: 1619703083
# 格式: <sha256>  <bytes>  <path-in-zip>
<sha256>  <bytes>  games/asteroids/asteroids.exe
...
```

### 1.4 分卷规则（旧）

`recovery\work\task109\package.py`：`SPLIT_INDEX = 10`，按**字母序的前 10 / 后 10 款**切两卷：

* part1：asteroids bomberman breakout flappy frogger game2048 lunarlander match3 minesweeper missilecommand
* part2：pacman platformer pong puzzlebobble rtype snake sokoban spaceinvaders tetris towerdefense

给出理由是（`package.py` 的 README 与 `PACKAGE-INFO-TASK109.txt` 原文）：「整包 (20 款 × 约 160 MB) 压缩前约 3.2 GB，超过单文件 2 GB 的常用上限，因此按游戏顺序切成 2 个 zip 分卷」。实测两卷各 **632 348 706 / 632 337 210 字节（约 632 MB）**，压缩后合计 **1.264 GB**。

### 1.5 本批沿用与偏离（前后对照）

| 项 | 旧（TASK-109） | 本批（TASK-148） | 是否偏离 |
|---|---|---|---|
| 命名 | `godot-mcp-20games-exe-<ts>-partXofY.zip` | 同 | 无 |
| 顶层目录 | 分卷名（去 `.zip`），单顶层 | 同 | 无 |
| 卷内布局 | README.md / MANIFEST.txt / RUN-CHECK.txt / games/** | 同 | 无 |
| 每款文件 | exe + pck + `data_<game>_windows_x86_64/`（187 个） | 同（实测 189/款） | 无 |
| RUN-CHECK 口径 | headless 退出码 0 + 3 款窗口抽查 | **逐款** cmd 启动冒烟（存活 ≥3 s + 主窗口）——TASK-148 B.5/P3 明确要求 20/20 逐款冒烟，故加强 | 偏离（任务书要求） |
| 分卷数 | 2 卷（每卷 10 款） | **1 卷 `part1of1`** | **偏离，见下** |
| MANIFEST 字段 | `sha256  bytes  path` | `sha256  bytes  **part**  path` | **偏离，见下** |

**偏离 1：单卷（`part1of1`）而不是 2 卷。理由：**

* 旧规则把「**解压后** 3.2 GB」拿去比「单文件 2 GB 上限」，这是**口径混淆**——限制针对的是归档文件本身，不是解压后的载荷。
* 实测整包归档 = **1 178 MiB（1264863973 字节）**，远低于 2 GB，甚至低于 4 GB 的 Zip64 门槛；本批已用 `allowZip64=True` 写出，`unzip`/资源管理器/`zipfile` 均可直接解。
* TASK-148 任务书 C.6 明确写了「若单卷可容下则单卷，并说明」，A.2 也允许改结构但要求说明理由并给前后对照——本节即该说明与对照。
* 若仍要旧的两卷口径：`recovery\work\task148\package_task148.py` 里把 `SPLIT_INDEX = None` 改成 `10` 即可原样复现旧的两卷划分。

**偏离 2：MANIFEST 增加「分卷归属」列。理由：**

TASK-148 C.6 要求清单「逐文件相对路径 + 字节数 + sha256，**含分卷归属**」。旧 3 列格式没有这一列，故改为 4 列 `<sha256>  <bytes>  <part>  <path-in-part>`；文件名、字段顺序、`#` 注释头都保持不变，解析方只需多读一列。旧格式无此需求，属新增能力而非破坏。

---

## 2. B 部分 — 20/20 逐款重新导出

### 2.1 用的就是仓库现成的方式（+ 三处必要改动）

* 脚本：`recovery\work\task148\export_all_task148.ps1`，从 `cmd` 启动：
  `cmd /c powershell -NoProfile -ExecutionPolicy Bypass -File export_all_task148.ps1`
* 引擎：`godot\bin\godot.windows.editor.x86_64.mono.console.exe`（仓库既有的 mono 编辑器），
  命令形状与 TASK-109 的 `export_all.ps1` 逐字一致：
  `--headless --path <proj> --mcp-port=<19401..19420> --export-release "Windows Desktop" <out>`
* 改动 1：输出落到 `recovery\work\task148\exe\<game>\`，**不写** `dist\exe\`。`dist\exe\` 是 TASK-109 那批的导出目录，铁律 2「不删既有」要求保留上一批的现场。
* 改动 2：子进程用 `System.Diagnostics.ProcessStartInfo` + **异步**读 stdout/stderr + `WaitForExit(超时)`，因为 `Start-Process -PassThru` 在本机取不到 `ExitCode`（返回空），而 `Start-Process -Wait` 会**连带等待后代进程**（见 2.3）。
* 改动 3：导出前置环境变量 `UseSharedCompilation=false`、`MSBUILDDISABLENODEREUSE=1`、`DOTNET_CLI_USE_MSBUILD_SERVER=0`（见 2.3），并把这三项写进每条 argv 记录旁边。

### 2.2 逐款记录（原始命令 + 退出码 + 耗时 + 产物）

下面是 `recovery\work\task148\export-results.json` 的逐款取值。`argv` 即**原始命令**（引擎路径 + 全部参数；环境变量见 2.1 改动 3，20 款相同）。

产物路径统一为 `recovery\work\task148\exe\<game>\<game>.exe`、`...\<game>.pck`、`...\data_<game>_windows_x86_64\`（下表给的是字节数；每一款的绝对路径逐条记在 `export-results.json` 的 `exe_path` / `pck_path` / `data_dir` 三个字段里，也可见下面的展开 argv）。

| # | game | port | exit | 耗时 s | exe 字节 | exe sha256 | pck 字节 | pck sha256 | data 文件 | data 字节 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | asteroids | 19401 | 0 | 7.7 | 82057728 | `c7a8cf2570566dba002ef790df853311da29128a923666b79403aee4ae8bf8ba` | 4484 | `3410572174a5c5533973701416257e858783bb9e02dd3498e8e2a53d43f8e7a1` | 187 | 79914129 |
| 2 | bomberman | 19402 | 0 | 8.2 | 82057728 | `a0a309e78837dc665889e6d8039f15a36fff21477621c0a6afca427053f8578d` | 4964 | `8e9ee9868f5c0ff4148f2e5014f4c5769db731c56aa1e9925e58b95493870984` | 187 | 79928373 |
| 3 | breakout | 19403 | 0 | 8.1 | 82057728 | `e143fe12cd3946004d40b0d072253bfb7f0f0fa3c00c0b130c35e6f0dd7498e1` | 6224 | `db731d68bf5c2d1f73f38fb11316ed294348075ca60c0359a5c92451e7075987` | 187 | 79901494 |
| 4 | flappy | 19404 | 0 | 11.7 | 82057728 | `8bdfba4a3719438a891321414637546b8d544297cd1b4df2360e6dc03a623296` | 3512 | `a290eae711feae36b8a872e8f392eba685c7f23503d7ba905d144303a1b54c84` | 187 | 79900880 |
| 5 | frogger | 19405 | 0 | 11.8 | 82057728 | `3f1dbf40b049770dea753e4b576ffc986aa5febe472d97e565d97c45a04ed5ff` | 4452 | `76c1417ed86c4e601c8a958c0428de06f3c42904aaf07005420a4299d41327b6` | 187 | 79910551 |
| 6 | game2048 | 19406 | 0 | 12.1 | 82057728 | `a6b3d7f38d9b472a86cd6740d6cca1c55aa31fc6459c5313f93af1f1f03f237c` | 4468 | `307be739f785e76b0e533c668261399c9768fca8f980a43ea3e1c22ec7bceced` | 187 | 79909846 |
| 7 | lunarlander | 19407 | 0 | 11.4 | 82057728 | `39bc48f7b75c225ebc6ed0fa3331723a98165c3da3fe9310b8615b320d418769` | 4056 | `ddd62313ccd7a5681d7d14c95b1f59e635e3bbb5a191b3f1390aca29182fc507` | 187 | 79912187 |
| 8 | match3 | 19408 | 0 | 8.3 | 82057728 | `0e6958a7af99e9984891fdde9059905054e5da81c20050b07967df5c046bbfb3` | 5444 | `97869101fea51906c944f8cc1d2401f54116bb5d9bde9f24436cc77d398c1946` | 187 | 79908236 |
| 9 | minesweeper | 19409 | 0 | 11.3 | 82057728 | `ea2dfa87a186e020975de25a41a3685ca3b738457a38385f79cf6e3795f250e9` | 6440 | `0c4b8804d6d87125711e6529ba1bc2d3a32c90340e8d94a0c9f0768a2d7eeaee` | 187 | 79915327 |
| 10 | missilecommand | 19410 | 0 | 11.3 | 82057728 | `a6f6302cd7a57ef80eb2d7125fef316c51187752206863f2a461941896984612` | 4556 | `97af79ab735b077fd7436763adcfd7992610507c2016ee6d6693e79020caf962` | 187 | 79921916 |
| 11 | pacman | 19411 | 0 | 11.3 | 82057728 | `4567bc648a8998840c556d8e7d43b1bd1ee9d98db3d140cdc25f6fd0d5f95019` | 4468 | `58883c15685b95b3d6ef7d0d5d0908824cb534b4c877e68d61b71047168a874c` | 187 | 79902884 |
| 12 | platformer | 19412 | 0 | 7.9 | 82057728 | `1e2b2a316db786b22df523687a5b87637a459d82da10b7616b7bceb2f301c531` | 4024 | `7e992d5a9da3a1e0d7ea3a1ca1e42183824555f618d8c4276494cb2960cdac37` | 187 | 79922720 |
| 13 | pong | 19413 | 0 | 7.8 | 82057728 | `463312d8f296236f6a8859539e2cf8bccc0fd6f7496601bf3ae3990cb4ce9046` | 5884 | `995f32b425fc2fadb3a0fa26854bca12eda737fd0ed08d8992517e9853a7989a` | 187 | 79893982 |
| 14 | puzzlebobble | 19414 | 0 | 11.6 | 82057728 | `cb7c6cb50520eaae3b28cb014f08a253e397cf50cf74da56b49d01520318e9dc` | 4040 | `8fe0e8aab599d025c3254801cbb5618022c4a0acb19213d6ec5bb347d7ed20d8` | 187 | 79918058 |
| 15 | rtype | 19415 | 0 | 11.0 | 82057728 | `b75e684e301ae497bcce4d461f3517ae1942b125639fa4013ca617226a2feb7f` | 4976 | `199849a536d0ad578594c9c39ab488b76f15f043fdbc4d297bda649931255b39` | 187 | 79920981 |
| 16 | snake | 19416 | 0 | 8.2 | 82057728 | `bdc47c297bc3564475791ef7d89af957428c03f6632b8a2ccb0bf47e60f1aff8` | 8720 | `439955c6367e7b6c59f3586622854657f8fd47a1af09087f57fe5aefe622473d` | 187 | 79907085 |
| 17 | sokoban | 19417 | 0 | 12.7 | 82057728 | `bede811c4c651b659f24a0312606428e503a3db1b3402fbbc6f0c0defb7d6942` | 4468 | `0fb3c9888f1402e52daeb029f14fad20c43ec75f80cf1db0e61a74b2834a9bd8` | 187 | 79912803 |
| 18 | spaceinvaders | 19418 | 0 | 11.0 | 82057728 | `7a7df75f4fe856d49c6166985b27424de827be2581e92a4c3eee9e61a1f7c5fc` | 4248 | `8f6ed771410885a9147acc52cbdfe053fcbf3f6db2631edc060907dbfe2bfbcd` | 187 | 79896645 |
| 19 | tetris | 19419 | 0 | 9.7 | 82057728 | `0844bb3ba3f7c56808937e6e4033f3259526b4379ac327050e3926a245301e31` | 5148 | `3a3ac54a55fb11f4af68536cc3fdb08213143b593c944914ac7946fd270bd313` | 187 | 79895260 |
| 20 | towerdefense | 19420 | 0 | 10.9 | 82057728 | `da7756ba556e204ee89dd5fb050f154a5d03edef265801be259c53b76cfd4c8f` | 5496 | `8bb64120d49ef6f5f85a184f040d540a67fc426eaa6d1b8037c832b6d8b96bbe` | 187 | 79918206 |

合计：exe **1641154560** 字节（20 × 82 057 728）、pck **100072** 字节、data **1598211563** 字节/共 **3740** 个文件；载荷合计 **3239466195** 字节（3.017 GB）。

**失败款：0 条**（20/20 退出码 0、20/20 `pack_done_log=True`、20/20 exe+pck+data 三件齐全）。

<details><summary>展开：20 条原始 argv</summary>

```
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\asteroids --mcp-port=19401 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\asteroids\asteroids.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\bomberman --mcp-port=19402 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\bomberman\bomberman.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\breakout --mcp-port=19403 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\breakout\breakout.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\flappy --mcp-port=19404 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\flappy\flappy.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\frogger --mcp-port=19405 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\frogger\frogger.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\game2048 --mcp-port=19406 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\game2048\game2048.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\lunarlander --mcp-port=19407 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\lunarlander\lunarlander.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\match3 --mcp-port=19408 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\match3\match3.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\minesweeper --mcp-port=19409 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\minesweeper\minesweeper.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\missilecommand --mcp-port=19410 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\missilecommand\missilecommand.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\pacman --mcp-port=19411 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\pacman\pacman.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\platformer --mcp-port=19412 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\platformer\platformer.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\pong --mcp-port=19413 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\pong\pong.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\puzzlebobble --mcp-port=19414 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\puzzlebobble\puzzlebobble.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\rtype --mcp-port=19415 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\rtype\rtype.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\snake --mcp-port=19416 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\snake\snake.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\sokoban --mcp-port=19417 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\sokoban\sokoban.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\spaceinvaders --mcp-port=19418 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\spaceinvaders\spaceinvaders.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\tetris --mcp-port=19419 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\tetris\tetris.exe
F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe --headless --path F:\moonbit-hof-rs\godot-mcp\projects\towerdefense --mcp-port=19420 --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\exe\towerdefense\towerdefense.exe
```

</details>

### 2.3 本次踩到并解决的坑（如实记录，因为它决定了上面那条 argv 与退出码能不能拿到）

第一版直接照抄 `Start-Process -Wait -PassThru`：导出产物**正常生成**，但进程迟迟不退出，单款等了 7 分钟仍未返回。逐层定位：

1. `Get-CimInstance Win32_Process` 显示只剩 console 包装进程，**没有**编辑器子进程 → 导出本身已完成；
2. 改 `--quit-after 5` 仍不退出；
3. 去掉导出、只跑 `--headless --path <proj> --quit-after 5` → **1.3 s 正常退出，退出码 0** → 包装进程没问题；
4. `Start-Process -Wait` 的语义包含等待**后代进程**；在导出进行时抓进程树，看到 `dotnet publish` 留下的**常驻 Roslyn 编译服务器 `VBCSCompiler.exe`**；
5. 对照实验（`recovery\work\task148\diag_exit.ps1` 的原始输出）：

```
DIAG pong         NoShared=False exited=False code=[n/a] seconds=120.4   VBCSCompiler_alive=1
DIAG tetris       NoShared=False exited=False code=[n/a] seconds=120.4   VBCSCompiler_alive=1
DIAG match3       NoShared=True  exited=True  code=[EMPTY] seconds=11.7    VBCSCompiler_alive=0
```

结论：**只要编译服务器被禁用（`UseSharedCompilation=false`），同一条导出命令 11.7 s 就跑完并正常退出。**于是生产脚本固定加上这三个环境变量；编译产物本身不受影响，只是编译器住在进程内而不是常驻服务器里。（`NoShared=True` 那行的 `code=[EMPTY]` 是 `Start-Process -PassThru` 取不到 ExitCode 的老问题，改用 `ProcessStartInfo` 后 20/20 都拿到了真实退出码。）

### 2.4 导出模板与编辑器的版本差（如实声明，未擅自改引擎）

* 编辑器：`4.8.dev.mono.custom_build.ba1587c71`（`godot\bin\...mono.console.exe`，2026-09-28 构建）
* 导出模板：`%APPDATA%\Godot\export_templates\4.8.dev\windows_release_x86_64.exe`，82 198 528 字节，2026-09-27 构建，其 `version.txt` 写 `4.8.dev.mono.custom_build.1c7f5c07a`

两者版本串不同（编辑器在 1c7f5c07a 之后又合入了 TASK-112 的 mcp_server 修复）。**这不阻塞导出**：Godot 的导出路径只按目录定位模板文件（`editor\export\export_template_manager.cpp`：模板目录 = `get_export_templates_dir().path_join(GODOT_VERSION_FULL_CONFIG)`，而 `GODOT_VERSION_FULL_CONFIG` = `4.8.dev`，与磁盘目录一致；该文件里读 `version.txt` 的三处——第 260/276/293 行——只在**安装模板压缩包**时执行）。20/20 导出成功即为实证。

**为什么没有重新编译模板**：TASK-148 的任务书把引擎仓 `godot/**` 列为**禁触**，而 `scons ... target=template_release module_mono_enabled=yes` 必须写入 `godot/bin/` 与 mono 模块目录。因此沿用既有模板，并在此如实声明：本批 exe 的**引擎运行时**是 1c7f5c07a 的 release 模板，与 TASK-109 同源；TASK-112 只改了 mcp_server 模块，而被交付的游戏默认 `listen=false`（§3.3 有日志实证），所以该差异不落在游戏运行路径上。**这项是本次交付明确保留的边界，不是遗漏。**

---

## 3. B 部分 — 20/20 逐款轻量冒烟

脚本：`recovery\work\task148\smoke_all_task148.ps1`（从 cmd 启动）。每款：

1. **从 cmd 启动**：`Start-Process cmd.exe -ArgumentList /c,"<pck 目录>\<game>.exe" -WorkingDirectory <该游戏目录>`——即 `cmd /c "<game>.exe"`，与在 cmd 里双击 exe 等价；
2. 用父进程关系 + 镜像名 `<game>.exe` 找到游戏进程（**不再**取「第一个子进程」——第一版正是这样抓到了`conhost.exe`，导致 20 个假阴性和 20 个孤儿进程，已修正并如实记录）；
3. 用 `EnumWindows` 找**可见顶层窗口**并等标题稳定为工程名（`Process.MainWindowHandle` 作为交叉验证）；
4. 断言**存活 ≥3 秒**且有主窗口，然后 `TerminateProcess` 结束，并复查该 pid 确已消失；
5. 不传 `--mcp-port`；每次启动前后都采样保留端口 9877/9888/9889/8080/8081 与全部 ≥19000 端口。

### 3.1 逐款结果

| # | game | pid | 存活秒 | 主窗口 | 窗口标题 | 退出方式 | 保留端口新增 | 高位端口新增 | 判定 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | asteroids | 9324 | 3.31 | True | `asteroids` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 2 | bomberman | 7800 | 3.30 | True | `bomberman` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 3 | breakout | 115288 | 3.22 | True | `breakout` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 4 | flappy | 116348 | 3.42 | True | `flappy` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 5 | frogger | 15108 | 3.23 | True | `frogger` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 6 | game2048 | 111064 | 3.25 | True | `game2048` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 7 | lunarlander | 2928 | 3.23 | True | `lunarlander` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 8 | match3 | 117008 | 3.26 | True | `match3` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 9 | minesweeper | 10080 | 3.26 | True | `minesweeper` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 10 | missilecommand | 34932 | 3.41 | True | `missilecommand` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 11 | pacman | 102772 | 3.25 | True | `pacman` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 12 | platformer | 117032 | 3.24 | True | `platformer` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 13 | pong | 115508 | 3.23 | True | `pong` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 14 | puzzlebobble | 108804 | 3.25 | True | `puzzlebobble` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 15 | rtype | 115356 | 3.27 | True | `rtype` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 16 | snake | 88684 | 3.26 | True | `snake` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 17 | sokoban | 111064 | 3.23 | True | `sokoban` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 18 | spaceinvaders | 15532 | 3.25 | True | `spaceinvaders` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 19 | tetris | 109920 | 3.22 | True | `tetris` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |
| 20 | towerdefense | 14764 | 3.41 | True | `towerdefense` | TerminateProcess (killed after smoke) | 无 | 无 | **PASS** |

**20/20 PASS**（全部：存活 3.22–3.42 s、有主窗口、标题等于游戏名、结束后进程消失）。

### 3.2 孤儿进程与端口（结束时）

```
结束时孤儿进程: game=[none] godot=[none]
保留端口 9877/9888/9889/8080/8081 : baseline=[127.0.0.1:8080, 127.0.0.1:8081]  final=[127.0.0.1:8080, 127.0.0.1:8081]
高位端口 >=19000 : baseline 与 final 完全相同
```

补充（报告生成时的最终复查）：game 进程 0、`godot*` 进程 0、`VBCSCompiler` 进程 0；9877/9888/9889 均**未监听**，8080/8081 仍为开跑前就在监听的那两个（用户的服务，未受影响）。

### 3.3 「默认不监听端口」的逐款引擎日志证据

不传 `--mcp-port` 时每款都打印：

```
[MCP] role=game configured_port=0 source=default listen=false
[MCP] not listening (get_port()=0)
```

（§4 的端到端运行里可见两款的完整原文。）源码依据：`modules/mcp_server` 的 `should_listen()`——游戏进程必须显式 opt-in 才开监听。

---

## 4. C 部分 — 打包、清单与自检

### 4.1 产物

| 文件 | 字节 | sha256 |
|---|---|---|
| `dist\godot-mcp-20games-exe-20260928-1528-part1of1.zip` | 1264863973 | `bc28ad360c105920cf25be9672814659232e76fb859a16cb3ac9c056584a84b4` |
| `dist\godot-mcp-20games-exe-20260928-1528.MANIFEST.txt` | 731460 | （清单本体，含 3780 行载荷） |
| `dist\godot-mcp-20games-exe-20260928-1528.sha256.txt` | 321 | 记上表的 zip 摘要 |
| `dist\PACKAGE-INFO-TASK148.txt` | 5158 | 交付物身份说明 |

zip 自身 sha256 有**两条独立路径**互相印证：Python `hashlib` 与 `certutil -hashfile`，均为`bc28ad360c105920cf25be9672814659232e76fb859a16cb3ac9c056584a84b4`。

### 4.2 清单（逐文件相对路径 + 字节数 + sha256 + 分卷归属）

```
bc28ad360c105920cf25be9672814659232e76fb859a16cb3ac9c056584a84b4  godot-mcp-20games-exe-20260928-1528-part1of1.zip
# bytes: 1264863973
# volumes: 1 (single volume: whole archive fits well under the 2 GB mark)
# manifest: in each volume as MANIFEST.txt; also copied to godot-mcp-20games-exe-20260928-1528.MANIFEST.txt
```

包内 `MANIFEST.txt` 头部（前 6 行）与尾部（末 3 行），由 `recovery\work\task148\package_task148.py` 生成：

```
# TASK-148 package manifest
# 分卷: godot-mcp-20games-exe-20260928-1528-part1of1
# 文件数: 3780  总字节: 3239466195
# 格式: <sha256>  <bytes>  <part>  <path-in-part>
# 说明: 逐文件 sha256 + 字节数 + 分卷归属; 路径相对分卷根目录;
#       本清单只覆盖载荷 (games/**), 不含 README.md / MANIFEST.txt / RUN-CHECK.txt。
...
3e738dc1fc73e7063bdbbb62c3cddb610c33a70d6b324fd359cc835c4536ad5f  372  godot-mcp-20games-exe-20260928-1528-part1of1  games/towerdefense/data_towerdefense_windows_x86_64/towerdefense.runtimeconfig.json
da7756ba556e204ee89dd5fb050f154a5d03edef265801be259c53b76cfd4c8f  82057728  godot-mcp-20games-exe-20260928-1528-part1of1  games/towerdefense/towerdefense.exe
8bb64120d49ef6f5f85a184f040d540a67fc426eaa6d1b8037c832b6d8b96bbe  5496  godot-mcp-20games-exe-20260928-1528-part1of1  games/towerdefense/towerdefense.pck
```

（清单内容为 UTF-8；在 GBK 码页的 cmd 里 `type` 会显示成乱码，这是终端显示问题，不是文件损坏——`selfcheck_task148.py` 按 UTF-8 解析得到 3780 条、总字节 3239466195，与头部声明一致。）

### 4.3 自检（款数 / 文件数 / 总字节数）的原始输出

任务书说「`check_counts.py` 或等价」。`check_counts.py` 是**复核包**的调用计数核对器（读 `runs\<game>\<tag>\call-index.txt`），与 exe 包的款数/文件数/总字节数无关；为不丢证据，两者都跑了：

**(a) `dist\check_counts.py` 原始输出（复现既有台账，20/20 OK）**

```
OK pong            editor= 23(24 tags - 1 toolslist, exp  23) game= 29(exp  29) cleanup=22 total=75
OK breakout        editor= 21(22 tags - 1 toolslist, exp  21) game= 34(exp  34) cleanup=34 total=90
OK snake           editor= 20(21 tags - 1 toolslist, exp  20) game= 33(exp  33) cleanup=0 total=54
OK tetris          editor=  6(6 tags - 0 toolslist, exp   6) game= 36(exp  36) cleanup=0 total=42
OK spaceinvaders   editor= 15(15 tags - 0 toolslist, exp  15) game= 44(exp  44) cleanup=0 total=59
OK asteroids       editor= 16(16 tags - 0 toolslist, exp  16) game= 55(exp  55) cleanup=0 total=71
OK pacman          editor= 16(16 tags - 0 toolslist, exp  16) game= 64(exp  64) cleanup=0 total=80
OK frogger         editor= 16(16 tags - 0 toolslist, exp  16) game= 74(exp  74) cleanup=0 total=90
OK flappy          editor= 14(14 tags - 0 toolslist, exp  14) game= 78(exp  78) cleanup=0 total=92
OK game2048        editor= 16(16 tags - 0 toolslist, exp  16) game=113(exp 113) cleanup=0 total=129
OK minesweeper     editor= 14(14 tags - 0 toolslist, exp  14) game=141(exp 141) cleanup=0 total=155
OK sokoban         editor= 14(14 tags - 0 toolslist, exp  14) game=176(exp 176) cleanup=0 total=190
OK bomberman       editor= 14(14 tags - 0 toolslist, exp  14) game=219(exp 219) cleanup=0 total=233
OK platformer      editor= 14(14 tags - 0 toolslist, exp  14) game=214(exp 214) cleanup=0 total=228
OK match3          editor= 14(14 tags - 0 toolslist, exp  14) game=131(exp 131) cleanup=0 total=145
OK towerdefense    editor= 14(14 tags - 0 toolslist, exp  14) game=131(exp 131) cleanup=0 total=145
OK missilecommand  editor= 14(14 tags - 0 toolslist, exp  14) game=113(exp 113) cleanup=0 total=127
OK rtype           editor= 14(14 tags - 0 toolslist, exp  14) game=209(exp 209) cleanup=0 total=223
OK puzzlebobble    editor= 14(14 tags - 0 toolslist, exp  14) game=143(exp 143) cleanup=0 total=157
OK lunarlander     editor= 14(14 tags - 0 toolslist, exp  14) game=216(exp 216) cleanup=0 total=230
```

**(b) 等价自检 `recovery\work\task148\selfcheck_task148.py` 的原始输出**

```
==============================================================================
VOLUME 1/1  godot-mcp-20games-exe-20260928-1528-part1of1.zip
==============================================================================
zip path   : F:\moonbit-hof-rs\godot-mcp\dist\godot-mcp-20games-exe-20260928-1528-part1of1.zip
zip bytes  : 1264863973  (1.178 GB)
zip sha256 : bc28ad360c105920cf25be9672814659232e76fb859a16cb3ac9c056584a84b4
matches package-results.json : YES
manifest_sidecar : F:\moonbit-hof-rs\godot-mcp\dist\godot-mcp-20games-exe-20260928-1528.MANIFEST.txt (present)
sha256_sidecar   : F:\moonbit-hof-rs\godot-mcp\dist\godot-mcp-20games-exe-20260928-1528.sha256.txt (present)
zip entries (files): 3783
top-level folders  : ['godot-mcp-20games-exe-20260928-1528-part1of1']
MANIFEST header    : 文件数=3780 总字节=3239466195 分卷=godot-mcp-20games-exe-20260928-1528-part1of1
MANIFEST parsed    : entries=3780 bytes=3239466195
in zip not in manifest : 0 []
in manifest not in zip : 0 []
games in volume    : 20 ['asteroids', 'bomberman', 'breakout', 'flappy', 'frogger', 'game2048', 'lunarlander', 'match3', 'minesweeper', 'missilecommand', 'pacman', 'platformer', 'pong', 'puzzlebobble', 'rtype', 'snake', 'sokoban', 'spaceinvaders', 'tetris', 'towerdefense']
------------------------------------------------------------------------------
per-game structure and digest cross-check (vs export-results.json)
------------------------------------------------------------------------------
game            exe_bytes  pck_bytes  data_n exe_sha verdict
asteroids       82057728   4484       187    OK     OK
bomberman       82057728   4964       187    OK     OK
breakout        82057728   6224       187    OK     OK
flappy          82057728   3512       187    OK     OK
frogger         82057728   4452       187    OK     OK
game2048        82057728   4468       187    OK     OK
lunarlander     82057728   4056       187    OK     OK
match3          82057728   5444       187    OK     OK
minesweeper     82057728   6440       187    OK     OK
missilecommand  82057728   4556       187    OK     OK
pacman          82057728   4468       187    OK     OK
platformer      82057728   4024       187    OK     OK
pong            82057728   5884       187    OK     OK
puzzlebobble    82057728   4040       187    OK     OK
rtype           82057728   4976       187    OK     OK
snake           82057728   8720       187    OK     OK
sokoban         82057728   4468       187    OK     OK
spaceinvaders   82057728   4248       187    OK     OK
tetris          82057728   5148       187    OK     OK
towerdefense    82057728   5496       187    OK     OK
------------------------------------------------------------------------------
spot-check: extract and re-hash
------------------------------------------------------------------------------
OK   games/asteroids/asteroids.exe                                          bytes=82057728
OK   games/asteroids/asteroids.pck                                          bytes=4484
OK   games/asteroids/data_asteroids_windows_x86_64/asteroids.dll            bytes=39424
OK   games/bomberman/bomberman.exe                                          bytes=82057728
OK   games/bomberman/bomberman.pck                                          bytes=4964
OK   games/bomberman/data_bomberman_windows_x86_64/bomberman.dll            bytes=48128
OK   games/towerdefense/towerdefense.exe                                    bytes=82057728
--   MANIFEST.txt                                                           bytes=727674 (not in MANIFEST by design)
--   README.md                                                              bytes=4936 (not in MANIFEST by design)
--   RUN-CHECK.txt                                                          bytes=5785 (not in MANIFEST by design)
spot-checked files : 10
README.md bytes    : 4936
RUN-CHECK.txt bytes: 5785

==============================================================================
CROSS-VOLUME VERDICT
==============================================================================
games found across volumes: 20
expected                  : 20
missing : none
extra   : none
dupes   : none

total payload files across volumes : 3783
total payload bytes across volumes : 3239466195 (3.017 GB)
total zip bytes across volumes     : 1264863973 (1.178 GB)
export records: files=3780 bytes=3239466195 (3.017 GB)
expected zip file entries         : 3783

smoke test: 20 / 20 passed (alive >= 3 s and main window)
orphan processes at end: game=[] godot=[]

SELF-CHECK VERDICT: PASS
  20/20 games present, none missing, none duplicated, none extra;
  MANIFEST matches the zip in both directions and its own header;
  every game's exe/pck digest matches the export record;
  extracted spot-check files re-hash to the manifest values.
```

### 4.4 端到端：从交付 zip 里解出并真的跑起来

`recovery\work\task148\zip_run_check_task148.py` 把 **pong** 与 **snake** 两款**整款**（各 189 个文件）从**交付的那个 zip** 里解出，逐个文件与包内 MANIFEST 重新对 sha256（378/378 全中），再在解出目录里 `--headless --quit-after 120` 运行：

```
delivered zip : F:\moonbit-hof-rs\godot-mcp\dist\godot-mcp-20games-exe-20260928-1528-part1of1.zip
volume        : godot-mcp-20games-exe-20260928-1528-part1of1
baseline reserved listeners on [9877, 9888, 9889, 8080, 8081] : [8080, 8081]

==============================================================================
GAME pong -- 189 files in the archive
==============================================================================
extracted files re-hashed against MANIFEST : 189/189 ok
run command : F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\unzip-test\godot-mcp-20games-exe-20260928-1528-part1of1\games\pong\pong.exe --headless --quit-after 120
working dir : F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\unzip-test\godot-mcp-20games-exe-20260928-1528-part1of1\games\pong
exit code   : 0   (1.24 s)
stdout tail :
    PONG_READY name=Main ball=(392, 268) ball_v=(0, 0) win_score=5 auto_serve=False
    [MCP] pending_timeout_ms=30000 (configured=30000) pending_ticks_per_frame=8
    [MCP] trace=off (default; use --mcp-trace=<path> or godot_mcp/trace_file to enable)
    [MCP] capture=off (default; use --mcp-capture=on_error|every_call together with --mcp-trace=<path>)
    [MCP] role=game configured_port=0 source=default listen=false
    [MCP] not listening (get_port()=0)

==============================================================================
GAME snake -- 189 files in the archive
==============================================================================
extracted files re-hashed against MANIFEST : 189/189 ok
run command : F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\unzip-test\godot-mcp-20games-exe-20260928-1528-part1of1\games\snake\snake.exe --headless --quit-after 120
working dir : F:\moonbit-hof-rs\godot-mcp\recovery\work\task148\unzip-test\godot-mcp-20games-exe-20260928-1528-part1of1\games\snake
exit code   : 0   (1.24 s)
stdout tail :
    [MCP] pending_timeout_ms=30000 (configured=30000) pending_ticks_per_frame=8
    [MCP] trace=off (default; use --mcp-trace=<path> or godot_mcp/trace_file to enable)
    [MCP] capture=off (default; use --mcp-capture=on_error|every_call together with --mcp-trace=<path>)
    [MCP] role=game configured_port=0 source=default listen=false
    [MCP] not listening (get_port()=0)
    SNAKE_TICK head=5,10 dir=1,0 len=3 score=0 over=False ticks=0 waiting=True

final reserved listeners on [9877, 9888, 9889, 8080, 8081] : [8080, 8081]

ZIP RUN-CHECK VERDICT: PASS
  both extracted games re-hash 100% against the in-zip MANIFEST and run
  headless (120 frames) with exit code 0, without opening any MCP port.
```

### 4.5 本批与旧包的逐款对比（说明这次不是「换个时间戳重发」）

`recovery\work\task148\compare_payload.py` 的原始输出：

```
game            name exe       pck       dll      
------------------------------------------------------------
asteroids       YES  same      same      DIFF     
bomberman       YES  same      DIFF      DIFF     
breakout        -    same      same      DIFF     
flappy          YES  same      same      DIFF     
frogger         YES  same      same      DIFF     
game2048        YES  same      same      DIFF     
lunarlander     -    same      DIFF      DIFF     
match3          -    same      DIFF      DIFF     
minesweeper     -    same      DIFF      DIFF     
missilecommand  -    same      DIFF      DIFF     
pacman          -    same      same      DIFF     
platformer      YES  same      same      DIFF     
pong            YES  same      same      DIFF     
puzzlebobble    YES  same      DIFF      DIFF     
rtype           -    same      DIFF      DIFF     
snake           YES  same      DIFF      DIFF     
sokoban         -    same      DIFF      DIFF     
spaceinvaders   -    same      same      DIFF     
tetris          -    same      same      DIFF     
towerdefense    -    same      DIFF      DIFF     

exe  same=20  diff=0  
pck  same=10  diff=10 
dll  same=0   diff=20
```

`recovery\work\task148\evidence_source_freshness.py`（把**当前源码**里的字符串字面量拿去在旧包内的 DLL 与新 DLL 里查；旧包没有 = 旧包确实过期）：

```
game            lits   in_old in_new new_only
--------------------------------------------------
snake           40     10     14     4     
game2048        40     23     25     2     
pong            34     6      8      2     
puzzlebobble    40     18     18     0     
platformer      40     13     13     0     
asteroids       40     20     20     0     
frogger         40     21     21     0     
bomberman       40     22     24     2     
flappy          40     15     16     1
```

读法：`pck` 装的是场景/脚本列表/工程设置，**game logic 在 `data_<game>_windows_x86_64\<game>.dll`**；而 Roslyn 产物**不是逐字节确定**的（每次构建 MVID 都变），所以 20/20 的 dll 都「不同」并不代表源码变了。真正能区分源码版本的是上面的字面量证据：snake / game2048 / pong / bomberman / flappy 有**只在当前源码里存在**的字面量出现在新程序集、而旧包程序集里没有 → 旧包确实早于这些改动。另外 pck 有 10/20 与旧包不同（场景或工程设置层面确有变化）。

---

## 5. 铁律逐条自查

| # | 铁律 | 执行情况 |
|---|---|---|
| 1 | 禁止一切 shell 重定向 | **生产链路 0 次**：导出/冒烟/打包/自检/提交全部通过 `ProcessStartInfo` 重定向、`Start-Process -RedirectStandardOutput/Error`、Python 文件句柄、`Out-File`/`Set-Content` 之外的方式落盘；三个 `.ps1` 与全部 `.py` 里 grep `2>&1 / 2>nul / 1>NUL / 2>/dev/null / >>` **无匹配**。**但：探索期在若干 `dir`/`mkdir`/`git log`/`type` 只读命令里用过 `2>nul`（约 10 处）**，见 §7.1，如实报 |
| 2 | 破坏性命令默认拒绝；不删既有包；不改游戏逻辑；不改 `.gitignore` | 旧包 0 删除 0 修改（sha256 未变）；`projects/**` git 干净；`.gitignore` 未动；只删过 `recovery\work\task148\exe\<game>\` 下**本脚本自己刚生成**的产物 |
| 3 | 命令尽量从 cmd 启动；中文写盘用 UTF-8 | 导出/冒烟/自检脚本均由 `cmd /c powershell ... -File` 启动；冒烟的游戏进程由 `cmd /c` 拉起；所有中文文件由 Python `encoding='utf-8'` 写 |
| 4 | 唯一高位端口；禁止第三方端点 | 导出用 19401–19420（逐款唯一、启动前查占用）；冒烟不请求任何端口；全程未访问任何网络端点 |
| 5 | 不受网络影响，不尝试外部下载 | 全程零下载；只用本机既有引擎、模板、NuGet 离线源、Python |
| 6 | 未达标项如实报 | §7 逐条列出（含探索期 `2>nul`、模板版本差、`conhost` 误判导致的第一轮假阴性） |
| 7 | 逐文件暂存；只提交 `dist/**`；他人改动不代提交不 revert | 见 §6.3：只 `git add` 了 3 个 `dist/**` 文件，其余 6 处 modified / 18 处 untracked 一律未动 |

---

## 6. 提交与仓库状态

### 6.1 本次提交

```
91783eb TASK-148: republish the 20-game Windows release package from CURRENT sources
  3 files changed, 3867 insertions(+)
  create mode 100644 godot-mcp/dist/PACKAGE-INFO-TASK148.txt
  create mode 100644 godot-mcp/dist/godot-mcp-20games-exe-20260928-1528.MANIFEST.txt
  create mode 100644 godot-mcp/dist/godot-mcp-20games-exe-20260928-1528.sha256.txt
```

**大包不入库**：`.gitignore` 里 TASK-122 的既有规则 `godot-mcp/dist/*.zip` 明确把分卷 zip 排除在历史之外（「大块二进制不入库，包的**身份**——sha256 / MANIFEST / PACKAGE-INFO——入库」）。本任务书也预见了这一点（「若大包不适合入库，先说明并给出你的处理」）。因此：

* **提交**：`*.MANIFEST.txt`（3780 行逐文件摘要）、`*.sha256.txt`、`PACKAGE-INFO-TASK148.txt`；
* **留在工作区**：`dist\godot-mcp-20games-exe-20260928-1528-part1of1.zip`（1.18 GB，可由本报告的脚本与已装模板原样重建）。

**决策日志的去处**：任务书把 `DECISIONS.md` 列为**禁触**，故本次不在 `DECISIONS.md` 追加条目，而是把决策（单卷 vs 两卷、为什么、回滚点）**完整写进上面的 commit message** （`recovery\work\task148\commit-msg.txt` 是同一份文本），使「改动 → 提交 → 决策理由」仍可互查。若后续允许改 `DECISIONS.md`，把该 commit message 全文追加为一条决策即可。

### 6.2 旧包未被删除 / 未被修改（sha256 证据）

```
2026/09/27  08:44     7,007,625 godot-mcp-20games-20260927-0844.zip
2026/09/27  09:28   632,348,706 godot-mcp-20games-exe-20260927-0927-part1of2.zip
2026/09/27  09:29   632,337,210 godot-mcp-20games-exe-20260927-0927-part2of2.zip
2026/09/28  15:30 1,264,863,973 godot-mcp-20games-exe-20260928-1528-part1of1.zip   <- 本批，新增
2026/09/27  14:25   632,377,243 godot-mcp-20games-playable-20260927-1424-part1of2.zip
2026/09/27  14:26   632,362,355 godot-mcp-20games-playable-20260927-1424-part2of2.zip

f596189d64ea4cf61648af89779d990406538bf3b28325bf1e3fc92e26c8fdf1  ...-exe-20260927-0927-part1of2.zip
59586e439fc2c329a04902beb242bf881445b6524ca1b8dea7c739bc63381d5c  ...-exe-20260927-0927-part2of2.zip
```

这两个摘要与旧 sidecar `dist\godot-mcp-20games-exe-20260927-0927.sha256.txt` 记录的值**逐字符相同**。

### 6.3 两仓 git 状态（只动了导出产物 / 临时文件）

```
=== git log --oneline -3   (F:\moonbit-hof-rs) ===
91783eb TASK-148: republish the 20-game Windows release package from CURRENT sources
da8b3dd TASK-146: label the pre-commit git status block in the report
3b36c24 TASK-146: record the main commit hash and the exact staged/unstaged file split in the report

=== git status --short   (提交后) ===
 M DECISIONS.md
 M godot-mcp/recovery/reports/TASK-140-REPORT.md
 M godot-mcp/recovery/tasks/TEMPLATE-logic-feedback.md
 M godot-mcp/tools/playability_controls.json
 M godot-mcp/tools/playtest_player.py
 M godot-mcp/tools/tests/test_playability_model_player.py
?? godot-mcp/recovery/... (18 项, 他人未提交)
?? godot-mcp/recovery/work/task148/            <- 本任务的脚本与证据（见 §7）

=== git status --short -- godot-mcp/projects  （游戏逻辑/场景/工程配置）===
(空 —— 零改动)

=== 引擎仓 F:\moonbit-hof-rs\godot-mcp\godot ===
git log --oneline -3:
ba1587c71e fix(mcp_server): TASK-112 - the three engine defects TASK-111 registered ...
3fdabe2d9a fix(godot-mcp): TASK-110 - editor_list_signal_connections ...
1f9d0cb1c9 modules/mcp_server: task103 - REBUILT-2C-MANIFEST gains the 2c-12 section ...
git status --short:  ?? uid_cache.bin      （该文件在本任务开始前就已存在，非本次产生；其余干净）
```

---

## 7. 未达标项 / 偏离 / 遗留风险（如实报）

1. **探索期使用了 `2>nul`（违反铁律 1 的字面要求）**：在**只读探查/建目录/校验**命令里用过约 10 处`2>nul`（探测模板目录 2 处、创建 task148 目录 3 处、`git log` 2 处、`dir` 查看产物 2 处、`type` 查看证据文件 1 处、`dir | findstr` 校验解压结果 1 处）。它们**不在导出/打包/冒烟/提交链路上**，也没有用于掩盖失败输出（只吞掉「文件不存在」之类的噪声）。导出/打包链路的三个 `.ps1` 与全部 `.py` 经 grep 确认**无任何重定向**。此项属**未完全达标**，如实登记。
2. **分卷数与 MANIFEST 字段偏离旧口径**：理由与前后对照见 §1.5，改后可复现旧行为（`SPLIT_INDEX=10`）。
3. **导出模板版本串落后于编辑器**（1c7f5c07a vs ba1587c71）：不阻塞导出（§2.4 有源码依据与 20/20 实证），但确实是本批的一个边界；因 `godot/**` 禁触故未重编模板。若要求 exe 运行时也含 TASK-112 的 mcp_server 修复，需要一次模板重编（约 9 分钟 `scons` + 写 `godot/**`），超出本任务授权范围。
4. **冒烟脚本第一版有缺陷（已修正，但过程如实记录）**：首版把 cmd 的**第一个子进程**当成游戏进程，实际抓到 `conhost.exe`，导致 20 个「无主窗口」假阴性与 20 个孤儿游戏进程（PID 与报告里不同）。已杀掉全部孤儿、改为按镜像名 `<game>.exe` 匹配并用 `EnumWindows` 检测窗口，重跑得到 20/20 PASS、0 孤儿。上面 §3.1 是**修正后那次**的真实结果。
5. **DLL 逐字节不可复现**：C# 构建产物每次不同（MVID），所以「包里的 dll 是否等于当前源码编译」无法用摘要证明，只能用字面量证据（§4.5）间接证明。这是工具链性质，不是本批缺陷。
6. **`recovery\work\task148\` 未提交**：任务书只授权提交 `dist/**`，故本任务的脚本与证据（约 10 个文件 + 数 MB 日志）留在工作区；报告已把它们的位置与用途逐条写清。
7. **`--headless` 端到端只抽查了 2 款**（pong、snake），不是 20 款全抽；20 款已在 §3 全部做过窗口化冒烟。

---

## 8. 验收判据对照

| 编号 | 判据 | 结论 | 证据位置 |
|---|---|---|---|
| P1 | 写清上一版 exe 包结构/命名/分卷口径，并说明本批是否偏离及理由 | 达成 | §1（含 1.5 前后对照） |
| P2 | 20/20 逐款导出记录（原始命令 + 退出码 + 产物路径与大小），失败款逐条原因 | 达成（0 失败） | §2.2 |
| P3 | 20/20 逐款冒烟（pid/存活秒/窗口标题/退出方式），结束无孤儿 | 达成 | §3.1、§3.2 |
| P4 | 新包 + MANIFEST（逐文件 sha256）+ sha256.txt 齐备，命名含本次时间戳 | 达成 | §4.1、§4.2 |
| P5 | 自检通过：款数/文件数/总字节数与清单一致（附原始输出） | 达成 | §4.3 |
| P6 | 旧包未删；游戏逻辑/场景/工程配置零改动（git status 证据） | 达成 | §6.2、§6.3 |
| P7 | 铁律逐条 + 重定向自查 + 两仓 git log/status + 关键产物 sha256 | 达成（重定向自查含 1 条未达标如实报） | §5、§6 |
| P8 | 未达标项如实报 | 达成 | §7（7 条） |

---

## 9. 复现方式

```
cd /d F:\moonbit-hof-rs\godot-mcp

REM 1) 重新导出 20 款（约 3.5 分钟；输出到 recovery\work\task148\exe\）
cmd /c powershell -NoProfile -ExecutionPolicy Bypass -File recovery\work\task148\export_all_task148.ps1

REM 2) 逐款冒烟（约 1.5 分钟）
cmd /c powershell -NoProfile -ExecutionPolicy Bypass -File recovery\work\task148\smoke_all_task148.ps1

REM 3) 打包（单卷；要旧的两卷口径就把 package_task148.py 的 SPLIT_INDEX 改成 10）
python recovery\work\task148\package_task148.py

REM 4) 自检 + 端到端
python recovery\work\task148\selfcheck_task148.py
python recovery\work\task148\zip_run_check_task148.py
```

本报告的表格与原始输出由 `recovery\work\task148\make_report.py` 从上述产物重新读出生成，不是手抄。

