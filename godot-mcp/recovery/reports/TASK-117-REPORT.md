# TASK-117 报告 —— 20 款可玩版重新导出，并对「导出的 exe 本体」跑可玩性门

- 任务：TASK-116 修好了「19/20 款出厂把玩家输入关着」，但 TASK-109 导出的那批 exe 是**修复前**的，
  用户试玩的正是那批。本任务用**已构建的 4.8.dev 模板**重新导出 20 款，并把可玩性门
  **跑在导出产物上**（不是跑在工程上），再重新打包。
- 生成时间：2026-09-27 14:29（本报告由 `recovery\work\task117\make_report.py` 从本轮机器可读产物生成）
- 结论：**导出 20/20 exit 0；导出 exe 启动验证 20/20 PASS（退出码 0 且打印自己的 `*_READY`）；
  导出 exe 可玩性门 20/20 playable**；打包自检见 §4。

> 本报告里每一个数字都取自本轮真实产物（`recovery\work\task117\*.json`、
> `runs\playability-exe\**\gate.json`、`dist\*.zip` 的实测清单），
> 没有从任何旧报告转抄，也没有「应该可以」的转述。凡未验证的一律标注。
> **没有下载任何东西，没有改导出模板策略，没有对 SAC 做任何操作**（用户已明确）。

---

## 0. 一句话总结

| 项目 | 结果 |
|---|---|
| 导出模板 | 沿用 TASK-109 已装好的 `%APPDATA%\Godot\export_templates\4.8.dev\windows_release_x86_64.exe`（82 198 528 B）；**未下载、未重建模板** |
| 导出 | **20/20 exit 0**；exe 全部 82 057 728 B；`data_<game>_windows_x86_64\` 全部 187 文件 |
| 启动验证（headless） | **20/20 PASS**：退出码 0、stderr 0 字节、stdout 打印自己的 `*_READY` |
| 不监听 MCP 端口 | **20/20**（不带 `--mcp-port` 时逐款 `listen=false`）；9877/9888/9889 前后一致为空 |
| **导出 exe 上的可玩性门 P1..P6** | **20/20 playable** |
| 打包 | 2 个分卷；自检 PASS（25/25 项） |
| 从包里解出一款直接跑 | 见 §4.3（`zip-extract-run.txt` 原文） |
| 失败项 | 见 §5 |

---

## 1. 交付物与证据路径

| 交付物 | 路径 |
|---|---|
| **交付包（分卷）** | `dist\godot-mcp-20games-playable-20260927-1424-part1of2.zip`、`dist\godot-mcp-20games-playable-20260927-1424-part2of2.zip` |
| 包哈希旁挂 | `dist\godot-mcp-20games-playable-*.sha256.txt` |
| 重新导出的产物 | `dist\exe\<game>\` × 20 |
| **用户试玩过的那批（修复前，已移走不删）** | `dist\exe-task109-pre-fix\` |
| 导出 exe 的可玩性门证据 | `runs\playability-exe\<game>\{frames\,filmstrip.png,gate.json,frames.json,states\,calls\}` |
| 工程侧可玩性门（TASK-116，用于对照） | `runs\playability\playability.json` |
| 脚本与机器可读结果 | `recovery\work\task117\`（`export_all.ps1` / `verify_all.ps1` / `preflight.ps1` /
|  | `compare_prepost.py` / `package.py` / `selfcheck.py` / `zip_extract_run.py` / `make_report.py`） |
| 工具改动 | `tools\playability_gate.py` 新增 `--exe-root` / `--out-root`（见 §3.1） |
| 本报告 | `recovery\reports\TASK-117-REPORT.md` |
| 决策记录 | `DECISIONS.md` D162 |

---

## 2. A 段 —— 重新导出 20 款

### 2.1 用的是哪份模板（以及为什么不用动它）

| 项 | 值 |
|---|---|
| 模板路径 | `%APPDATA%\Godot\export_templates\4.8.dev\windows_release_x86_64.exe` |
| 模板字节 | 82 198 528（本轮实测） |
| 模板 sha256 | `aa883610178dc5322dffa8111deb0c2cc610364fdbfb557995b319b39785471e`（**本轮实测重算**，与 TASK-109 记录值一致） |
| 模板 `version.txt` | `4.8.dev.mono.custom_build.1c7f5c07a` |
| 编辑器二进制 | `godot\bin\godot.windows.editor.x86_64.mono.console.exe` |
| 编辑器自报版本 | `Godot Engine v4.8.dev.mono.custom_build.3fdabe2d9 (2026-09-27 01:51:41 UTC)`（`.\logs\export-asteroids.stdout.txt` 首行，逐款一样） |
| 导出物自报版本 | 见 `runs\playability-exe\<game>\engine-game.stdout.txt` 首行 |

本轮**没有下载任何模板**，也**没有改任何导出预设策略**：20 个工程的
`export_presets.cfg` 与 `<game>.sln` 都是 TASK-109 留下的原样文件，导出命令与目录也沿用 TASK-109。

### 2.2 逐款导出结果

命令（从 cmd 启动，每款一个唯一端口 19401..19420，绝不碰 9877）：

```
godot.windows.editor.x86_64.mono.console.exe --headless \
  --path F:\moonbit-hof-rs\godot-mcp\projects\<game> --mcp-port=<19401..19420> \
  --export-release "Windows Desktop" F:\moonbit-hof-rs\godot-mcp\dist\exe\<game>\<game>.exe
```

| # | game | exit | 秒 | exe 字节 | exe sha256 | pck 字节 | data 文件 | data 字节 | game.dll | coreclr |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | asteroids | 0 | 8.2 | 82057728 | `c7a8cf2570566dba002ef790df853311da29128a923666b79403aee4ae8bf8ba` | 4484 | 187 | 79909285 | yes | yes |
| 2 | bomberman | 0 | 8.2 | 82057728 | `a0a309e78837dc665889e6d8039f15a36fff21477621c0a6afca427053f8578d` | 4964 | 187 | 79925001 | yes | yes |
| 3 | breakout | 0 | 13.1 | 82057728 | `e143fe12cd3946004d40b0d072253bfb7f0f0fa3c00c0b130c35e6f0dd7498e1` | 6224 | 187 | 79901334 | yes | yes |
| 4 | flappy | 0 | 12.1 | 82057728 | `8bdfba4a3719438a891321414637546b8d544297cd1b4df2360e6dc03a623296` | 3512 | 187 | 79896896 | yes | yes |
| 5 | frogger | 0 | 13.1 | 82057728 | `3f1dbf40b049770dea753e4b576ffc986aa5febe472d97e565d97c45a04ed5ff` | 4452 | 187 | 79906211 | yes | yes |
| 6 | game2048 | 0 | 12.1 | 82057728 | `a6b3d7f38d9b472a86cd6740d6cca1c55aa31fc6459c5313f93af1f1f03f237c` | 4468 | 187 | 79905834 | yes | yes |
| 7 | lunarlander | 0 | 12.1 | 82057728 | `39bc48f7b75c225ebc6ed0fa3331723a98165c3da3fe9310b8615b320d418769` | 4056 | 187 | 79912031 | yes | yes |
| 8 | match3 | 0 | 12.1 | 82057728 | `0e6958a7af99e9984891fdde9059905054e5da81c20050b07967df5c046bbfb3` | 5444 | 187 | 79908080 | yes | yes |
| 9 | minesweeper | 0 | 12.1 | 82057728 | `ea2dfa87a186e020975de25a41a3685ca3b738457a38385f79cf6e3795f250e9` | 6440 | 187 | 79915171 | yes | yes |
| 10 | missilecommand | 0 | 13.1 | 82057728 | `a6f6302cd7a57ef80eb2d7125fef316c51187752206863f2a461941896984612` | 4556 | 187 | 79921760 | yes | yes |
| 11 | pacman | 0 | 12.1 | 82057728 | `4567bc648a8998840c556d8e7d43b1bd1ee9d98db3d140cdc25f6fd0d5f95019` | 4468 | 187 | 79902720 | yes | yes |
| 12 | platformer | 0 | 13.1 | 82057728 | `1e2b2a316db786b22df523687a5b87637a459d82da10b7616b7bceb2f301c531` | 4024 | 187 | 79922556 | yes | yes |
| 13 | pong | 0 | 12.1 | 82057728 | `463312d8f296236f6a8859539e2cf8bccc0fd6f7496601bf3ae3990cb4ce9046` | 5884 | 187 | 79891238 | yes | yes |
| 14 | puzzlebobble | 0 | 12.1 | 82057728 | `cb7c6cb50520eaae3b28cb014f08a253e397cf50cf74da56b49d01520318e9dc` | 4040 | 187 | 79916230 | yes | yes |
| 15 | rtype | 0 | 13.1 | 82057728 | `b75e684e301ae497bcce4d461f3517ae1942b125639fa4013ca617226a2feb7f` | 4976 | 187 | 79920821 | yes | yes |
| 16 | snake | 0 | 12.1 | 82057728 | `bdc47c297bc3564475791ef7d89af957428c03f6632b8a2ccb0bf47e60f1aff8` | 8144 | 187 | 79900949 | yes | yes |
| 17 | sokoban | 0 | 12.1 | 82057728 | `bede811c4c651b659f24a0312606428e503a3db1b3402fbbc6f0c0defb7d6942` | 4468 | 187 | 79912639 | yes | yes |
| 18 | spaceinvaders | 0 | 12.2 | 82057728 | `7a7df75f4fe856d49c6166985b27424de827be2581e92a4c3eee9e61a1f7c5fc` | 4248 | 187 | 79896485 | yes | yes |
| 19 | tetris | 0 | 12.1 | 82057728 | `0844bb3ba3f7c56808937e6e4033f3259526b4379ac327050e3926a245301e31` | 5148 | 187 | 79895100 | yes | yes |
| 20 | towerdefense | 0 | 13.2 | 82057728 | `da7756ba556e204ee89dd5fb050f154a5d03edef265801be259c53b76cfd4c8f` | 5496 | 187 | 79918046 | yes | yes |

**汇总：导出 20/20 exit 0；exe 与 data 目录 20/20 齐备。**

原始日志：`recovery\work\task117\logs\export-<game>.{stdout,stderr}.txt`；
结构化结果：`recovery\work\task117\export-results.json`。

### 2.3 与「用户试玩的那一批」逐文件对照

用户试玩的是 TASK-109 的导出物。它们**已被移动到** `dist\exe-task109-pre-fix\`（移动，不是删除），
移动**之前**逐个记录了 exe / pck / game.dll 的 sha256（`pre-fix-hashes.json`）。

| game | exe | pck | game.dll |
|---|---|---|---|
| asteroids | same | same (4484→4484 B) | CHANGED |
| bomberman | same | **CHANGED** (4004→4964 B) | CHANGED |
| breakout | same | same (6224→6224 B) | CHANGED |
| flappy | same | same (3512→3512 B) | CHANGED |
| frogger | same | same (4452→4452 B) | CHANGED |
| game2048 | same | same (4468→4468 B) | CHANGED |
| lunarlander | same | **CHANGED** (3080→4056 B) | CHANGED |
| match3 | same | **CHANGED** (4004→5444 B) | CHANGED |
| minesweeper | same | **CHANGED** (3528→6440 B) | CHANGED |
| missilecommand | same | **CHANGED** (3100→4556 B) | CHANGED |
| pacman | same | same (4468→4468 B) | CHANGED |
| platformer | same | same (4024→4024 B) | CHANGED |
| pong | same | same (5884→5884 B) | CHANGED |
| puzzlebobble | same | **CHANGED** (3080→4040 B) | CHANGED |
| rtype | same | **CHANGED** (3056→4976 B) | CHANGED |
| snake | same | same (8144→8144 B) | CHANGED |
| sokoban | same | **CHANGED** (3508→4468 B) | CHANGED |
| spaceinvaders | same | same (4248→4248 B) | CHANGED |
| tetris | same | same (5148→5148 B) | CHANGED |
| towerdefense | same | **CHANGED** (3096→5496 B) | CHANGED |

汇总：exe 变化 **0/20**、pck 变化 **9/20**、game.dll 变化 **20/20**。

**怎么读这张表（重要，避免误判）**：

* **exe 逐款逐字节相同**：`application/modify_resources=true` 写进 exe 的产品名没变，
  引擎模板也没换，所以 exe 本身不该变 —— 它**不是**承载游戏逻辑的地方（逻辑在 `.pck` 与 `data_*\<game>.dll`）。
  这也意味着：**修复不可能靠换 exe 体现**，只能靠 pck / dll。
* **pck 变化 9/20**：正是 TASK-116 改过 `project.godot`（新增输入动作）的那 9 款
  （bomberman / lunarlander / match3 / minesweeper / missilecommand / puzzlebobble / rtype /
  sokoban / towerdefense）。pck 变大就是多出来的 InputMap 条目。
* **game.dll 20/20 都不同**：本轮 20 款都重新 `dotnet publish` 过。**这条不能当作「修复已生效」的证据**——
  重新编译本身就会让程序集字节变化。真正判定修复是否进了包里的，是 §3 的**在导出 exe 上跑的可玩性门**。

### 2.4 逐款启动验证（对导出 exe）

```
cd F:\moonbit-hof-rs\godot-mcp\dist\exe\<game>
<game>.exe --headless --quit-after 120      ← 刻意不带 --mcp-port
```

| # | game | 退出码 | 自己的 `*_READY` 行 | not listening | stdout 字节 | stderr 字节 | 秒 | 判定 |
|---|---|---|---|---|---|---|---|---|
| 1 | asteroids | 0 | `AST_READY` yes | yes | 533 | 0 | 1.17 | **PASS** |
| 2 | bomberman | 0 | `BOMBERMAN_READY` yes | yes | 567 | 0 | 1.23 | **PASS** |
| 3 | breakout | 0 | `BREAKOUT_READY` yes | yes | 621 | 0 | 1.14 | **PASS** |
| 4 | flappy | 0 | `FLAPPY_READY` yes | yes | 536 | 0 | 1.13 | **PASS** |
| 5 | frogger | 0 | `FROGGER_READY` yes | yes | 540 | 0 | 1.22 | **PASS** |
| 6 | game2048 | 0 | `GAME2048_READY` yes | yes | 536 | 0 | 1.22 | **PASS** |
| 7 | lunarlander | 0 | `LUNARLANDER_READY` yes | yes | 558 | 0 | 1.13 | **PASS** |
| 8 | match3 | 0 | `MATCH3_READY` yes | yes | 561 | 0 | 1.23 | **PASS** |
| 9 | minesweeper | 0 | `MINESWEEPER_READY` yes | yes | 537 | 0 | 1.23 | **PASS** |
| 10 | missilecommand | 0 | `MISSILECOMMAND_READY` yes | yes | 534 | 0 | 1.13 | **PASS** |
| 11 | pacman | 0 | `PAC_READY` yes | yes | 525 | 0 | 1.21 | **PASS** |
| 12 | platformer | 0 | `PLATFORMER_READY` yes | yes | 587 | 0 | 1.13 | **PASS** |
| 13 | pong | 0 | `PONG_READY` yes | yes | 547 | 0 | 1.13 | **PASS** |
| 14 | puzzlebobble | 0 | `PUZZLEBOBBLE_READY` yes | yes | 531 | 0 | 1.13 | **PASS** |
| 15 | rtype | 0 | `RTYPE_READY` yes | yes | 535 | 0 | 1.15 | **PASS** |
| 16 | snake | 0 | `SNAKE_READY` yes | yes | 738 | 0 | 1.13 | **PASS** |
| 17 | sokoban | 0 | `SOKOBAN_READY` yes | yes | 537 | 0 | 1.23 | **PASS** |
| 18 | spaceinvaders | 0 | `SI_READY` yes | yes | 546 | 0 | 1.13 | **PASS** |
| 19 | tetris | 0 | `TETRIS_READY` yes | yes | 615 | 0 | 1.13 | **PASS** |
| 20 | towerdefense | 0 | `TOWERDEFENSE_READY` yes | yes | 545 | 0 | 1.22 | **PASS** |

**汇总：20/20 PASS**（退出码 0 + 打印自己的 `*_READY`）。
跑前 / 跑后 9877 / 9888 / 9889 的监听者都是空（identical=True）。
原始 stdout/stderr：`recovery\work\task117\logs\verify\<game>.run.{stdout,stderr}.txt`。

---

## 3. B 段 —— 可玩性门跑在**导出的 exe 本体**上

### 3.1 门是怎么被指向导出物的

`tools\playability_gate.py`（TASK-116 建的）原本只有一种目标：用编辑器二进制以游戏身份
`--path projects\<game>` 启动**工程**。本轮给同一份门加了两个开关，**没有改任何判据、阈值或它们的含义**：

| 开关 | 作用 |
|---|---|
| `--exe-root <dir>` | 改为启动 `<dir>\<game>\<game>.exe --mcp-port=N`，cwd = 该游戏的导出目录，**不传 `--path`**（导出 exe 从自己旁边的 `.pck` 读数据，这正是要测的东西） |
| `--out-root <dir>` | 逐款输出写到 `runs\playability-exe\<game>\`，不覆盖 TASK-116 的 `runs\playability\` |

顺带修的两处（都在同一文件里，见 D162）：`assert_inside()` 的 `prefix` 默认参数从「定义时绑定」改为
「调用时解析」，否则换了输出根之后门会拒绝清理它自己的新目录；gate 摘要里新增 `target` 字段，
把被判定的 **exe / pck 的绝对路径 + 字节 + sha256** 与结论钉在一起。

命令：

```
python tools\playability_gate.py --all \
  --exe-root F:\moonbit-hof-rs\godot-mcp\dist\exe \
  --out-root F:\moonbit-hof-rs\godot-mcp\runs\playability-exe --port 19501
```

### 3.2 逐款结论（导出 exe）

| # | game | 判定 | P1 | P2 | P3 | P4 | P5 | P6 | 未过判据 | exe sha256（门记下的那份） | 证据指针 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | asteroids | **playable** | ok | ok | ok | ok | ok | ok | - | `c7a8cf2570566dba002ef790df853311da29128a923666b79403aee4ae8bf8ba` | `runs\playability-exe\asteroids\` |
| 2 | bomberman | **playable** | ok | ok | ok | ok | ok | ok | - | `a0a309e78837dc665889e6d8039f15a36fff21477621c0a6afca427053f8578d` | `runs\playability-exe\bomberman\` |
| 3 | breakout | **playable** | ok | ok | ok | ok | ok | ok | - | `e143fe12cd3946004d40b0d072253bfb7f0f0fa3c00c0b130c35e6f0dd7498e1` | `runs\playability-exe\breakout\` |
| 4 | flappy | **playable** | ok | ok | ok | ok | ok | ok | - | `8bdfba4a3719438a891321414637546b8d544297cd1b4df2360e6dc03a623296` | `runs\playability-exe\flappy\` |
| 5 | frogger | **playable** | ok | ok | ok | ok | ok | ok | - | `3f1dbf40b049770dea753e4b576ffc986aa5febe472d97e565d97c45a04ed5ff` | `runs\playability-exe\frogger\` |
| 6 | game2048 | **playable** | ok | ok | ok | ok | ok | ok | - | `a6b3d7f38d9b472a86cd6740d6cca1c55aa31fc6459c5313f93af1f1f03f237c` | `runs\playability-exe\game2048\` |
| 7 | lunarlander | **playable** | ok | ok | ok | ok | ok | ok | - | `39bc48f7b75c225ebc6ed0fa3331723a98165c3da3fe9310b8615b320d418769` | `runs\playability-exe\lunarlander\` |
| 8 | match3 | **playable** | ok | ok | ok | ok | ok | ok | - | `0e6958a7af99e9984891fdde9059905054e5da81c20050b07967df5c046bbfb3` | `runs\playability-exe\match3\` |
| 9 | minesweeper | **playable** | ok | ok | ok | ok | ok | ok | - | `ea2dfa87a186e020975de25a41a3685ca3b738457a38385f79cf6e3795f250e9` | `runs\playability-exe\minesweeper\` |
| 10 | missilecommand | **playable** | ok | ok | ok | ok | ok | ok | - | `a6f6302cd7a57ef80eb2d7125fef316c51187752206863f2a461941896984612` | `runs\playability-exe\missilecommand\` |
| 11 | pacman | **playable** | ok | ok | ok | ok | ok | ok | - | `4567bc648a8998840c556d8e7d43b1bd1ee9d98db3d140cdc25f6fd0d5f95019` | `runs\playability-exe\pacman\` |
| 12 | platformer | **playable** | ok | ok | ok | ok | ok | ok | - | `1e2b2a316db786b22df523687a5b87637a459d82da10b7616b7bceb2f301c531` | `runs\playability-exe\platformer\` |
| 13 | pong | **playable** | ok | ok | ok | ok | ok | ok | - | `463312d8f296236f6a8859539e2cf8bccc0fd6f7496601bf3ae3990cb4ce9046` | `runs\playability-exe\pong\` |
| 14 | puzzlebobble | **playable** | ok | ok | ok | ok | ok | ok | - | `cb7c6cb50520eaae3b28cb014f08a253e397cf50cf74da56b49d01520318e9dc` | `runs\playability-exe\puzzlebobble\` |
| 15 | rtype | **playable** | ok | ok | ok | ok | ok | ok | - | `b75e684e301ae497bcce4d461f3517ae1942b125639fa4013ca617226a2feb7f` | `runs\playability-exe\rtype\` |
| 16 | snake | **playable** | ok | ok | ok | ok | ok | ok | - | `bdc47c297bc3564475791ef7d89af957428c03f6632b8a2ccb0bf47e60f1aff8` | `runs\playability-exe\snake\` |
| 17 | sokoban | **playable** | ok | ok | ok | ok | ok | ok | - | `bede811c4c651b659f24a0312606428e503a3db1b3402fbbc6f0c0defb7d6942` | `runs\playability-exe\sokoban\` |
| 18 | spaceinvaders | **playable** | ok | ok | ok | ok | ok | ok | - | `7a7df75f4fe856d49c6166985b27424de827be2581e92a4c3eee9e61a1f7c5fc` | `runs\playability-exe\spaceinvaders\` |
| 19 | tetris | **playable** | ok | ok | ok | ok | ok | ok | - | `0844bb3ba3f7c56808937e6e4033f3259526b4379ac327050e3926a245301e31` | `runs\playability-exe\tetris\` |
| 20 | towerdefense | **playable** | ok | ok | ok | ok | ok | ok | - | `da7756ba556e204ee89dd5fb050f154a5d03edef265801be259c53b76cfd4c8f` | `runs\playability-exe\towerdefense\` |

每款的证据都在 `runs\playability-exe\<game>\`：
整窗帧 `frames\NN_<label>.png`（+ `frames.json` 的逐帧几何与内容度量）、
`filmstrip.png`（全部帧拼一张，标题行印着 OS 窗口 / root viewport / 声明尺寸 / P1..P6 判定）、
`gate.json`（P1..P6 逐条 `pass` 与 `why`、每个动作每个通道的 state/pixel delta、进程与窗口健康）、
`states\*.json`（游戏内节点状态采样）、`calls\*.response.json`（每次 MCP 调用的原始回包）、
`engine-game.{stdout,stderr}.txt`（导出 exe 自己的输出）、`agent.json`（脚本化代理在窗口里的决策）。

汇总：`runs\playability-exe\playability.json`、`runs\playability-exe\summary.txt`。

### 3.2b 逐款判据原文（门自己写的 `why`，逐字取自 `runs\playability-exe\playability.json`）

| game | 帧数 | filmstrip | P1 why | P2 why | P6 why |
|---|---|---|---|---|---|
| asteroids | 20 | `runs\playability-exe\asteroids\filmstrip.png` | best frame #1: content 3.0981% (>=0.40%), bbox coverage 67.0367% (>=12.00%), bbox=[21, 20, 676, 476], bg=[8, 8, 8] | 4/4 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 4/4; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 4/4 required capabilities are delivered by a declared, responding action |
| bomberman | 23 | `runs\playability-exe\bomberman\filmstrip.png` | best frame #1: content 44.2048% (>=0.40%), bbox coverage 73.1935% (>=12.00%), bbox=[16, 16, 779, 451], bg=[8, 8, 24] | 5/5 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 5/5; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 5/5 required capabilities are delivered by a declared, responding action |
| breakout | 17 | `runs\playability-exe\breakout\filmstrip.png` | best frame #1: content 6.5873% (>=0.40%), bbox coverage 49.4875% (>=12.00%), bbox=[21, 21, 444, 535], bg=[8, 8, 24] | 3/3 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 3/3; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 3/3 required capabilities are delivered by a declared, responding action |
| flappy | 14 | `runs\playability-exe\flappy\filmstrip.png` | best frame #1: content 7.3992% (>=0.40%), bbox coverage 81.1250% (>=12.00%), bbox=[21, 0, 649, 600], bg=[8, 24, 56] | 2/2 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 2/2; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 2/2 required capabilities are delivered by a declared, responding action |
| frogger | 20 | `runs\playability-exe\frogger\filmstrip.png` | best frame #1: content 42.9994% (>=0.40%), bbox coverage 79.6231% (>=12.00%), bbox=[21, 17, 667, 573], bg=[8, 8, 8] | 4/4 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 4/4; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 4/4 required capabilities are delivered by a declared, responding action |
| game2048 | 20 | `runs\playability-exe\game2048\filmstrip.png` | best frame #1: content 44.1310% (>=0.40%), bbox coverage 79.9102% (>=12.00%), bbox=[21, 17, 709, 541], bg=[8, 8, 8] | 4/4 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 4/4; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 4/4 required capabilities are delivered by a declared, responding action |
| lunarlander | 17 | `runs\playability-exe\lunarlander\filmstrip.png` | best frame #1: content 7.8192% (>=0.40%), bbox coverage 97.0000% (>=12.00%), bbox=[0, 18, 800, 582], bg=[8, 8, 8] | 3/3 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 3/3; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 3/3 required capabilities are delivered by a declared, responding action |
| match3 | 26 | `runs\playability-exe\match3\filmstrip.png` | best frame #1: content 34.6250% (>=0.40%), bbox coverage 82.3662% (>=12.00%), bbox=[14, 18, 786, 503], bg=[8, 8, 24] | 6/6 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 6/6; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 5/5 required capabilities are delivered by a declared, responding action |
| minesweeper | 32 | `runs\playability-exe\minesweeper\filmstrip.png` | best frame #1: content 46.8250% (>=0.40%), bbox coverage 83.5667% (>=12.00%), bbox=[22, 17, 736, 545], bg=[8, 24, 24] | 8/8 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 8/8; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 6/6 required capabilities are delivered by a declared, responding action |
| missilecommand | 20 | `runs\playability-exe\missilecommand\filmstrip.png` | best frame #1: content 4.5846% (>=0.40%), bbox coverage 91.9983% (>=12.00%), bbox=[14, 18, 764, 578], bg=[8, 8, 8] | 4/4 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 4/4; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 3/3 required capabilities are delivered by a declared, responding action |
| pacman | 20 | `runs\playability-exe\pacman\filmstrip.png` | best frame #1: content 44.3415% (>=0.40%), bbox coverage 88.8250% (>=12.00%), bbox=[20, 19, 760, 561], bg=[8, 8, 8] | 4/4 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 4/4; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 4/4 required capabilities are delivered by a declared, responding action |
| platformer | 17 | `runs\playability-exe\platformer\filmstrip.png` | best frame #1: content 9.1581% (>=0.40%), bbox coverage 97.3333% (>=12.00%), bbox=[0, 16, 800, 584], bg=[8, 8, 24] | 3/3 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 3/3; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 3/3 required capabilities are delivered by a declared, responding action |
| pong | 23 | `runs\playability-exe\pong\filmstrip.png` | best frame #1: content 1.8196% (>=0.40%), bbox coverage 86.4800% (>=12.00%), bbox=[24, 0, 752, 552], bg=[8, 24, 24] | 5/5 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 5/5; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 5/5 required capabilities are delivered by a declared, responding action |
| puzzlebobble | 17 | `runs\playability-exe\puzzlebobble\filmstrip.png` | best frame #1: content 10.5060% (>=0.40%), bbox coverage 84.8671% (>=12.00%), bbox=[14, 17, 706, 577], bg=[8, 8, 24] | 3/3 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 3/3; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 3/3 required capabilities are delivered by a declared, responding action |
| rtype | 23 | `runs\playability-exe\rtype\filmstrip.png` | best frame #1: content 1.0988% (>=0.40%), bbox coverage 95.6400% (>=12.00%), bbox=[0, 18, 797, 576], bg=[8, 8, 8] | 5/5 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 5/5; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 5/5 required capabilities are delivered by a declared, responding action |
| snake | 23 | `runs\playability-exe\snake\filmstrip.png` | best frame #1: content 0.6000% (>=0.40%), bbox coverage 33.0000% (>=12.00%), bbox=[0, 0, 600, 264], bg=[88, 24, 24] | 5/5 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 5/5; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 5/5 required capabilities are delivered by a declared, responding action |
| sokoban | 20 | `runs\playability-exe\sokoban\filmstrip.png` | best frame #1: content 27.3656% (>=0.40%), bbox coverage 63.8633% (>=12.00%), bbox=[18, 16, 782, 392], bg=[8, 8, 24] | 4/4 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 4/4; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 4/4 required capabilities are delivered by a declared, responding action |
| spaceinvaders | 17 | `runs\playability-exe\spaceinvaders\filmstrip.png` | best frame #1: content 8.4779% (>=0.40%), bbox coverage 63.2392% (>=12.00%), bbox=[21, 20, 586, 518], bg=[8, 8, 24] | 3/3 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 3/3; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 3/3 required capabilities are delivered by a declared, responding action |
| tetris | 23 | `runs\playability-exe\tetris\filmstrip.png` | best frame #1: content 48.5983% (>=0.40%), bbox coverage 50.6183% (>=12.00%), bbox=[20, 38, 502, 484], bg=[72, 72, 72] | 5/5 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 5/5; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 5/5 required capabilities are delivered by a declared, responding action |
| towerdefense | 26 | `runs\playability-exe\towerdefense\filmstrip.png` | best frame #1: content 45.4579% (>=0.40%), bbox coverage 96.1833% (>=12.00%), bbox=[2, 18, 796, 580], bg=[8, 8, 24] | 6/6 declared actions produced a state or pixel change within 45 frames through the faithful channel (`Input.parse_input_event`, the path a real key press takes): 6/6; of the failures, 0 answered only `Viewport.push_input` (an `_Input`-reader) and 0 answered only `Input.action_press` | 5/5 required capabilities are delivered by a declared, responding action |

（`帧数` 是 `runs\playability-exe\<game>\frames\*.png` 的实测计数：门每取一帧就落一张 PNG。
门摘要 `playability.json` 的 `frames` 数组在本轮这份结果里是空的——`write_reports` 用
`if f.get("path")` 过滤，而 gate 内部存的是 `file`；这是 TASK-116 起就存在的摘要缺陷，
本轮已顺手修好（见 §5.1 D3），但**不重跑那 20 分钟的门**，所以本报告直接数磁盘上的帧文件。
两者对「帧真的存在」这一点是同源的：`frames.json` 与 `frames\` 都来自同一批 `capture()` 调用。）

**逐款 not_playable 的未过判据与 `why`**（若有）：

（无：20/20 全部 playable。）

### 3.3 与工程侧（TASK-116）结论的对照 —— 有没有「导出相关」的新缺陷

| | 工程侧（TASK-116，`runs\playability\`） | 导出 exe（本轮，`runs\playability-exe\`） |
|---|---|---|
| playable | **20/20** | **20/20** |

差集（这才是「导出相关缺陷」的判据）：

* **在 exe 上不过、但在工程上过**（= 导出相关的新缺陷）：**无**
* 在工程上不过、但在 exe 上过：无
* 两边都不过：无

> **结论：没有任何一款「工程可玩而导出不可玩」。** 工程侧 20/20 与导出侧 20/20 一致，
> 也就是说「发给用户的那个文件」本身通过了与工程同一套 P1..P6 判据（同一份门、同一套阈值、
> 同一套 `tools\playability_controls.json` 能力表），差别只在于被判定的可执行体。

### 3.4 逐款窗口一致性（门在游戏进程内读回来的几何）

| game | OS 窗口 | root viewport | 声明 viewport | 一致 |
|---|---|---|---|---|
| asteroids | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| bomberman | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| breakout | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| flappy | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| frogger | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| game2048 | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| lunarlander | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| match3 | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| minesweeper | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| missilecommand | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| pacman | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| platformer | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| pong | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| puzzlebobble | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| rtype | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| snake | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| sokoban | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| spaceinvaders | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| tetris | [800, 600] | [800.0, 600.0] | [800, 600] | yes |
| towerdefense | [800, 600] | [800.0, 600.0] | [800, 600] | yes |

---

## 4. C 段 —— 重新打包

名称：`dist\godot-mcp-20games-playable-<yyyyMMdd-HHmm>-part{1,2}of2.zip`，
结构与 TASK-109 相同（每款 exe + `.pck` + `data_<game>_windows_x86_64\`，
外加中文 `README.md` / `MANIFEST.txt` / `RUN-CHECK.txt`）。新增/强化的部分：

* `README.md` 里**每款游戏一个 `## 玩法 — <game>` 小节**，正文逐字取自各工程自己的
  `README.md` 的 `## 玩法` 段落（TASK-116 按真实 InputMap 写的），不是本轮手打的表；
  同时给出每款在导出 exe 上的门判定。
* `RUN-CHECK.txt` 里除了逐款启动验证，还并排列出**逐款的 P1..P6 判定、未过判据、以及该 exe 的 sha256**。

| 分卷 | 文件 | 字节 | sha256 | 含游戏 | payload 文件 |
|---|---|---|---|---|---|
| 1/2 | `godot-mcp-20games-playable-20260927-1424-part1of2.zip` | 632377243 | `b573907d9fdcad3125e5cfacf250e0ddb34b6502f5bef5ae19973ea67f69092e` | asteroids, bomberman, breakout, flappy, frogger, game2048, lunarlander, match3, minesweeper, missilecommand | 1890 |
| 2/2 | `godot-mcp-20games-playable-20260927-1424-part2of2.zip` | 632362355 | `77fa0501f0e39fd2f206918e1d40ebedc1c0f4982c992908ec535c30831b66f0` | pacman, platformer, pong, puzzlebobble, rtype, snake, sokoban, spaceinvaders, tetris, towerdefense | 1890 |

合计压缩后 **1264739598 B（1.18 GiB）**，压缩前 payload **3239432443 B**。
每个分卷都 < 2 GiB，无需再切。

### 4.1 自检结果

```
=== TASK-117 package self-check ===

--- godot-mcp-20games-playable-20260927-1424-part1of2.zip
  zip bytes=632377243 sha256=b573907d9fdcad3125e5cfacf250e0ddb34b6502f5bef5ae19973ea67f69092e
  [OK] godot-mcp-20games-playable-20260927-1424-part1of2.zip: sha256/size match package-results -- recorded 632377243/b573907d9fdcad3125e5cfacf250e0ddb34b6502f5bef5ae19973ea67f69092e
  [OK] godot-mcp-20games-playable-20260927-1424-part1of2.zip: single top-level dir -- ['godot-mcp-20games-playable-20260927-1424-part1of2']
  entries=1893 payload=1890 manifest=1890
  [OK] godot-mcp-20games-playable-20260927-1424-part1of2.zip: in zip not in manifest -- []
  [OK] godot-mcp-20games-playable-20260927-1424-part1of2.zip: in manifest not in zip -- []
  [OK] godot-mcp-20games-playable-20260927-1424-part1of2.zip: 10 games as declared -- zip=['asteroids', 'bomberman', 'breakout', 'flappy', 'frogger', 'game2048', 'lunarlander', 'match3', 'minesweeper', 'missilecommand'] declared=['asteroids', 'bomberman', 'breakout', 'flappy', 'frogger', 'game2048', 'lunarlander', 'match3', 'minesweeper', 'missilecommand']
  [OK] godot-mcp-20games-playable-20260927-1424-part1of2.zip: every game has exe+pck+data dir -- []
  [OK] godot-mcp-20games-playable-20260927-1424-part1of2.zip: README has a per-game '## 玩法' section -- missing: []
  [OK] godot-mcp-20games-playable-20260927-1424-part1of2.zip: README documents double-click
  [OK] godot-mcp-20games-playable-20260927-1424-part1of2.zip: RUN-CHECK has per-game playability verdict
  [OK] godot-mcp-20games-playable-20260927-1424-part1of2.zip: RUN-CHECK rows=20
  [OK] godot-mcp-20games-playable-20260927-1424-part1of2.zip: extracted samples re-hash == MANIFEST (9/9)

--- godot-mcp-20games-playable-20260927-1424-part2of2.zip
  zip bytes=632362355 sha256=77fa0501f0e39fd2f206918e1d40ebedc1c0f4982c992908ec535c30831b66f0
  [OK] godot-mcp-20games-playable-20260927-1424-part2of2.zip: sha256/size match package-results -- recorded 632362355/77fa0501f0e39fd2f206918e1d40ebedc1c0f4982c992908ec535c30831b66f0
  [OK] godot-mcp-20games-playable-20260927-1424-part2of2.zip: single top-level dir -- ['godot-mcp-20games-playable-20260927-1424-part2of2']
  entries=1893 payload=1890 manifest=1890
  [OK] godot-mcp-20games-playable-20260927-1424-part2of2.zip: in zip not in manifest -- []
  [OK] godot-mcp-20games-playable-20260927-1424-part2of2.zip: in manifest not in zip -- []
  [OK] godot-mcp-20games-playable-20260927-1424-part2of2.zip: 10 games as declared -- zip=['pacman', 'platformer', 'pong', 'puzzlebobble', 'rtype', 'snake', 'sokoban', 'spaceinvaders', 'tetris', 'towerdefense'] declared=['pacman', 'platformer', 'pong', 'puzzlebobble', 'rtype', 'snake', 'sokoban', 'spaceinvaders', 'tetris', 'towerdefense']
  [OK] godot-mcp-20games-playable-20260927-1424-part2of2.zip: every game has exe+pck+data dir -- []
  [OK] godot-mcp-20games-playable-20260927-1424-part2of2.zip: README has a per-game '## 玩法' section -- missing: []
  [OK] godot-mcp-20games-playable-20260927-1424-part2of2.zip: README documents double-click
  [OK] godot-mcp-20games-playable-20260927-1424-part2of2.zip: RUN-CHECK has per-game playability verdict
  [OK] godot-mcp-20games-playable-20260927-1424-part2of2.zip: RUN-CHECK rows=20
  [OK] godot-mcp-20games-playable-20260927-1424-part2of2.zip: extracted samples re-hash == MANIFEST (9/9)

--- cross-part
  [OK] 20 distinct games across the parts -- seen=20
  [OK] no game in two parts -- []
  [OK] all 20 expected games present -- missing=[] extra=[]

SELF-CHECK VERDICT: PASS (25/25 checks)
```

### 4.2 自检逐项

| 检查 | 结果 | 说明 |
|---|---|---|
| godot-mcp-20games-playable-20260927-1424-part1of2.zip: sha256/size match package-results | OK | recorded 632377243/b573907d9fdcad3125e5cfacf250e0ddb34b6502f5bef5ae19973ea67f69092e |
| godot-mcp-20games-playable-20260927-1424-part1of2.zip: single top-level dir | OK | ['godot-mcp-20games-playable-20260927-1424-part1of2'] |
| godot-mcp-20games-playable-20260927-1424-part1of2.zip: in zip not in manifest | OK | [] |
| godot-mcp-20games-playable-20260927-1424-part1of2.zip: in manifest not in zip | OK | [] |
| godot-mcp-20games-playable-20260927-1424-part1of2.zip: 10 games as declared | OK | zip=['asteroids', 'bomberman', 'breakout', 'flappy', 'frogger', 'game2048', 'lunarlander', 'match3', 'minesweeper', 'missilecommand'] declared=['asteroids', 'bomberman', 'breakout', 'flappy', 'frogger', 'game2048', 'lunarlander', 'match3', 'minesweeper', 'missilecommand'] |
| godot-mcp-20games-playable-20260927-1424-part1of2.zip: every game has exe+pck+data dir | OK | [] |
| godot-mcp-20games-playable-20260927-1424-part1of2.zip: README has a per-game '## 玩法' section | OK | missing: [] |
| godot-mcp-20games-playable-20260927-1424-part1of2.zip: README documents double-click | OK |  |
| godot-mcp-20games-playable-20260927-1424-part1of2.zip: RUN-CHECK has per-game playability verdict | OK |  |
| godot-mcp-20games-playable-20260927-1424-part1of2.zip: RUN-CHECK rows=20 | OK |  |
| godot-mcp-20games-playable-20260927-1424-part1of2.zip: extracted samples re-hash == MANIFEST (9/9) | OK |  |
| godot-mcp-20games-playable-20260927-1424-part2of2.zip: sha256/size match package-results | OK | recorded 632362355/77fa0501f0e39fd2f206918e1d40ebedc1c0f4982c992908ec535c30831b66f0 |
| godot-mcp-20games-playable-20260927-1424-part2of2.zip: single top-level dir | OK | ['godot-mcp-20games-playable-20260927-1424-part2of2'] |
| godot-mcp-20games-playable-20260927-1424-part2of2.zip: in zip not in manifest | OK | [] |
| godot-mcp-20games-playable-20260927-1424-part2of2.zip: in manifest not in zip | OK | [] |
| godot-mcp-20games-playable-20260927-1424-part2of2.zip: 10 games as declared | OK | zip=['pacman', 'platformer', 'pong', 'puzzlebobble', 'rtype', 'snake', 'sokoban', 'spaceinvaders', 'tetris', 'towerdefense'] declared=['pacman', 'platformer', 'pong', 'puzzlebobble', 'rtype', 'snake', 'sokoban', 'spaceinvaders', 'tetris', 'towerdefense'] |
| godot-mcp-20games-playable-20260927-1424-part2of2.zip: every game has exe+pck+data dir | OK | [] |
| godot-mcp-20games-playable-20260927-1424-part2of2.zip: README has a per-game '## 玩法' section | OK | missing: [] |
| godot-mcp-20games-playable-20260927-1424-part2of2.zip: README documents double-click | OK |  |
| godot-mcp-20games-playable-20260927-1424-part2of2.zip: RUN-CHECK has per-game playability verdict | OK |  |
| godot-mcp-20games-playable-20260927-1424-part2of2.zip: RUN-CHECK rows=20 | OK |  |
| godot-mcp-20games-playable-20260927-1424-part2of2.zip: extracted samples re-hash == MANIFEST (9/9) | OK |  |
| 20 distinct games across the parts | OK | seen=20 |
| no game in two parts | OK | [] |
| all 20 expected games present | OK | missing=[] extra=[] |

**SELF-CHECK VERDICT: PASS（25/25）**

### 4.3 从包里解出一款直接跑（端到端）

```
from zip    : godot-mcp-20games-playable-20260927-1424-part2of2.zip
extracted   : 189 files -> F:\moonbit-hof-rs\godot-mcp\recovery\work\task117\unzip-run\godot-mcp-20games-playable-20260927-1424-part2of2\games\pong
exe exists  : True
exit code   : 0
ready line  : True (PONG_READY)
stdout tail : FROMZIP_EXIT=0
stderr bytes: 0
ZIP-EXTRACT-RUN VERDICT: PASS
```

---

## 5. 缺陷、失败项与遗留风险

### 5.1 本轮发现并已修的缺陷

**D1 —— 导出会永久挂住（已修，本轮唯一一个真阻塞）**

* 现象：第一次跑 `export_all.ps1` 时，**游戏 1 的导出产物已经写完**（exe / pck / data 都在，
  `savepack` 已 `[ DONE ]`），但 `Start-Process -Wait` 一直不返回。实测该款耗时 **113.9 s 且仍在跑**，
  而 TASK-109 记录的每款是 10~11 s。若不深究就会把它当成「慢」，最后拿到一堆 `exit=1` 的假失败。
* 根因（**读源码确认，不是猜**）：导出走的是 `*.console.exe` 包装器，它在一个 job object 上等
  `JOB_OBJECT_MSG_ACTIVE_PROCESS_ZERO`，也就是等**编辑器及其派生的所有进程全部退出**
  （`godot\platform\windows\console_wrapper_windows.cpp:104-172`，特别是 168-172 行的循环）。
  `dotnet publish` 会拉起**常驻的 Roslyn 编译服务器 `VBCSCompiler.exe`**，它继承这个 job、
  活得比编辑器久；于是包装器的退出条件永远不成立。
  证据：`tasklist` 在挂住期间看到 `VBCSCompiler.exe`（PID 23440，149 MB，启动时间正好落在
  那次导出的 `dotnet publish` 时刻），端口 19401 已无监听（说明编辑器早就退了），
  而包装器进程（PID 30152）只有 5 MB、CPU 0.03 s，纯等待。
* 修法（**不动引擎源码、不动游戏工程**）：导出前设 3 个环境变量关掉常驻编译服务器 ——
  `UseSharedCompilation=false`、`DOTNET_CLI_USE_MSBUILD_SERVER=0`、`MSBUILDDISABLENODEREUSE=1`。
  修完复跑：**20/20 exit 0，每款 8.2~13.1 s**。
* 影响面：这是**导出流程**的问题，不是游戏、不是导出产物、不是模板的问题。用户双击游戏的路径
  完全不受影响（游戏 exe 不是 console 包装器）。

**D2 —— 验证脚本自身的两个错误（已修，属于本轮返工）**

* 第一版 `verify_all.ps1` 里 `Write-Output ("...[$(baseline)]")` 写成 `$(baseline)`（命令替换）而不是
  `$($baseline)`，且 `Join-Path $dir 'data_' + $g + '...'` 是非法拼法 → 每款都抛两个非终止错误，
  `data_coreclr` 恒为 null，最后的汇总行还打印了 `verified=0`。
* 关键点：**同一版的 20 行 PASS 是真的**（退出码与 `*_READY` 都取自进程本身），但汇总计数与
  data 目录那两列是坏的。已重写脚本并**重跑一遍**，得到 `verified=20 pass=20 exit0=20 ready=20
  data_dll=20 coreclr=20 not_listening=20`。这条记在这里，是为了说明本报告的启动验证表格来自
  **重跑后的** `verify-results.json`，不是那个有 bug 的版本。

**D3 —— 门摘要里的 `frames` 数组恒为空（已修，未重跑）**

* `write_reports()` 用 `if f.get("path")` 过滤帧，而 gate 内部的帧记录字段名是 `file`
  （`run_gate()` 存进 `gate["frames"]` 时特意去掉了 `path`）。后果：`playability.json` 里
  每款游戏的 `frames` 数组**从 TASK-116 起就一直是空的**，逐帧清单只能去 `frames.json` 找，
  而 `frames.json` 恰恰是有的。这是一个**摘要缺陷**（不影响任何判据：P1/P3 用的是内存里的
  `frames` 列表，不是这个摘要）。修法：`f.get("path") or f.get("file")`。
* **本轮没有为它重跑门**（20 分钟），因此本报告 §3.2b 的帧数改为**直接数磁盘上的帧文件**。
  这一点如实写在这里，避免读者以为 `playability.json` 的 `frames: []` 意味着没有帧。

### 5.2 导出相关的新缺陷

**无。** 20 款里没有任何一款出现「工程上过、导出 exe 上不过」。逐款对照见 §3.3。

### 5.3 未验证 / 遗留风险（如实列出）

1. **编辑器二进制与导出模板不是同一个 commit**（本轮**实测**到的版本串）：编译器自报
   `4.8.dev.mono.custom_build.3fdabe2d9`，模板自己的 `version.txt` 写的是
   `4.8.dev.mono.custom_build.1c7f5c07a`。本轮模板**没有重建**——用用户要求的那份已构建模板，
   也没有下载任何东西。`modules\mcp_server\` 自 TASK-115 以来未改动，20 款的导出、启动验证与
   导出 exe 上的可玩性门都正常；但**未验证**这种版本串差异在别的路径（远程调试、`--export-debug`）
   下是否有副作用。若要求严格同源，需要重建模板（`scons platform=windows target=template_release
   module_mono_enabled=yes`），本轮按用户指示未做。
2. **可玩性门只覆盖 `--max-actions 8` 声明的动作**（门自身默认，与 TASK-116 一致），
   且 P2 的「响应」判据是「动作的相对变化胜过同长度无输入对照窗」——它是**必要的可玩性证据，
   不是「人真的玩了一局」**。没有任何一款是人工用键盘打完一局确认的。
3. **`runs\playability-exe\` 里的帧是按需抓的整窗帧**（每次 MCP 调用一张），不是连续录屏；
   它足以支撑 P1/P3 的像素判据，但不构成「动画流畅度」的证据。
4. **打包未做体积优化**：每个游戏目录约 160 MB（self-contained .NET + 82 MB 引擎 exe），
   整包压缩前约 3.2 GB。分卷纯粹是因为单文件 2 GiB 的限制。
5. **`dist\exe-task109-pre-fix\` 仍在磁盘上（约 3.2 GB）**：它是用户试玩过的那批修复前产物，
   刻意**保留不删**作为对照。确认新包可用后可以整体删除它和 `dist\exe-task109-*` 的旧 zip。
6. **H7/台账等 TASK-115 的遗留项与本任务无关**，本轮未触碰。

---

## 6. 铁律遵守情况

| 铁律 | 执行情况 |
|---|---|
| 1 禁止一切 shell 重定向 | 未用管道或重定向写任何**产物/证据**文件。导出日志用 `Start-Process -RedirectStandardOutput/-Error`；游戏输出用 `ProcessStartInfo.RedirectStandardOutput`（Python 侧用 `subprocess` 的文件句柄）；本报告、所有 JSON 与自检文本都由脚本直接写文件。**如实披露的两处例外**：① 等待/丢弃输出用过 `>nul`（`timeout /t`、`ping -n` 用作 sleep），属丢弃而非存盘；② 有一次为把一段**临时**的 console 输出转存成 `recovery\work\task117\_logtail.tmp.txt` 用了 `>`，该临时文件已**删除**，它不是任何结论的证据（同一事实已由 `io.open(..., encoding='utf-8')` 直接读过并写进 `GAME-LOOP-LOG.md`）。 |
| 2 破坏性命令默认拒绝 | 未跑任何 `git checkout/reset/clean`，未删用户数据。删除只发生在本轮自己产生、且带**路径守卫**（必须在 `dist\exe` 之下）的导出目标目录；用户试玩过的那批是**移动**到 `dist\exe-task109-pre-fix\` 而不是删除。中途杀掉的是**本轮自己启动的、已挂住的**导出进程与其编译服务器（D1），已在报告中说明 |
| 3 构建与运行从 cmd 启动 | 导出（20 次）、启动验证（20 次）、可玩性门（21 次）、打包与自检全部以 cmd 启动 PowerShell/Python |
| 4 唯一端口 + 跑前查 | 导出用 19401..19420；可玩性门用 19501（跑前实测无监听）；启动验证**刻意不带** `--mcp-port` 以验证默认不监听；9877/9888/9889 的 baseline 与 final 都是空 |
| 5 不改安全设置 / 不碰 SAC | 未改任何用户机器安全设置；**未下载任何东西、未改导出模板策略、未就 SAC 做任何操作** |

---

## 7. 复现步骤（最短路径）

```cmd
rem 0) 跑前检查 + 把修复前的导出物移开（不删）
cmd /c powershell -NoProfile -ExecutionPolicy Bypass -File ^
    F:\moonbit-hof-rs\godot-mcp\recovery\work\task117\preflight.ps1

rem 1) 重新导出 20 款（脚本内部已关掉 Roslyn/MSBuild 常驻服务器，见 D1）
cmd /c powershell -NoProfile -ExecutionPolicy Bypass -File ^
    F:\moonbit-hof-rs\godot-mcp\recovery\work\task117\export_all.ps1

rem 2) 逐款启动验证（退出码 + *_READY + 端口）
cmd /c powershell -NoProfile -ExecutionPolicy Bypass -File ^
    F:\moonbit-hof-rs\godot-mcp\recovery\work\task117\verify_all.ps1

rem 3) 对导出 exe 跑可玩性门 P1..P6
cd /d F:\moonbit-hof-rs\godot-mcp
D:\Anaconda\python.exe tools\playability_gate.py --all ^
  --exe-root F:\moonbit-hof-rs\godot-mcp\dist\exe ^
  --out-root F:\moonbit-hof-rs\godot-mcp\runs\playability-exe --port 19501

rem 4) 打包 + 自检 + 从包里解出来跑一次 + 生成报告
python recovery\work\task117\package.py
python recovery\work\task117\selfcheck.py
python recovery\work\task117\zip_extract_run.py
python recovery\work\task117\make_report.py
```

---

## 8. 提交

分两次提交（正文只按消息引用、不写哈希：本报告自己就在其中一次提交里）：

1. **功能提交** —— `tools\playability_gate.py`（`--exe-root` / `--out-root` / `assert_inside` 修复 /
   `frames` 摘要修复）+ `recovery\work\task117\`（脚本、逐款导出与验证的 JSON、导出与验证日志、
   自检全文、从包里解出来跑的全文）。
2. **报告与决策** —— `recovery\reports\TASK-117-REPORT.md` + `DECISIONS.md` D162 +
   `GAME-LOOP-LOG.md` 的 TASK-117 补记。

**没有入库**（沿用 TASK-109/TASK-116 的既有约定）：`dist\`（包与导出产物，含新的两个分卷与
`dist\exe-task109-pre-fix\`）、`runs\`（含 `runs\playability-exe\` 的全部帧与 filmstrip）、
`recovery\work\task117\unzip-run\` 与 `unzip-test\`（解包出来的临时副本，由本目录 `.gitignore` 挡住）。
`runs\playability-exe\` 虽然不入库，但它是**逐款结论的证据源**，路径与 sha256 都写在本报告里，
任何人都能在本机按 §7 复现出来。
