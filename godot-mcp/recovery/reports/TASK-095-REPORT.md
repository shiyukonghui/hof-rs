# TASK-095 — D-1 重新定域：冻结**不是**视口回读恒返回第一帧，而是**加载期画布项不再重录绘制命令**

* 执行者：工具工程师（本会话，**有写权限，不再委派**）
* 主仓：`F:\moonbit-hof-rs`（分支 `master`，无远端）
* 引擎仓：`F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`）
* 脚本 / 会话 / 日志：`godot-mcp\recovery\work\task095\`
* 时间：2026-09-27 01:45–02:40

---

## 0. 结论表（每行一句话）

| 段 | 要求 | 结论 | 关键证据 |
|---|---|---|---|
| **A** | 会话 / 显示器取证，给 D-1 与桌面状态相关性的判据，能复现就复现 | **做完，但不给因果结论。** 本会话是 **session 1 、console、Active、未锁屏** 的真实桌面（无 `LogonUI`、`SM_REMOTESESSION=0`、`OpenInputDesktop` 成功、`dwm` 在 session 1 跑）。**没有复现手段**：无法在不改变机器状态的前提下切换桌面状态，所以只报告**共存事实**与两个共时候选，明确标注**未建立因果** | `recovery\work\task095\forensics\session-state-20260927-014753.txt`；`nvidia-smi --query-gpu=display_active` = **Disabled** |
| **B** | 重试 TASK-094 未跑成的离屏 SubViewport 回读探针，判定能否拿到变化中的画面 | **做完，且推翻了 TASK-094 的 B 段阻塞说法与 D-1 根因说法。** 阻塞原因不是 PowerShell：`sessions\probe10\session.json` 是**语法非法的 JSON**（每个 call 对象少一个 `}`），Python 与 PS 5.1 **都**拒绝它。B①：**能**——自有 SubViewport 的回读在同一进程同一时刻拿到红→绿→蓝→黄四张不同画面。B②（**本轮关键**）：**但拿不到"目标场景"的画面**——镜像同一 `world_2d` 与把场景搬进自有 SubViewport **都仍然冻结**。**新的定域**：冻结是**逐画布项**的，只砸在**加载期**（`.tscn` 里带进来的）画布项上；**运行期新建**的画布项**在根视口里也是活的** | §B；`runs\snake\task095-offscreen`、`task095-discriminate`、`task095-loadednode` |
| **C** | 若 B① 成立则实现 `--mcp-capture-source=viewport\|offscreen` | **未实现（走 B② 分支）**，理由与"要做需要先定什么"写在 §C。**不交付一个对本机游戏画面无效的开关**。**引擎仓零字节改动** | §C |
| **D** | 重放 Pong / Breakout / Snake，把像素差列填上 | **做不到，列保持真实 0。** 本任务**没有**重放三段完整会话（原因见 §D），今天现场重测的最小反例仍然成立 | §D；`runs\snake\task095-loadednode` p01–p07 |
| **E** | 若有余量做第 4 个游戏 Tetris | **未开始。** 预算全部用在 B 段的定位与反驳上 | §E |
| **F** | 改了模块就重建两变体 + 十门全绿 + `accept_m1` 22/22；引擎仓 push；主仓提交；两仓 `git log` / `git status` | **模块零改动 → 不重建、不 push**（说明见 §F1）。主仓提交；两仓状态在 §F2 逐行给出 | §F |

---

## A. 会话 / 显示器取证

原始输出：`recovery\work\task095\forensics\session-state-20260927-014753.txt`（只读命令，`Set-Content` 落盘，无 shell 重定向）。

### A1 事实

| 项 | 实测值 |
|---|---|
| 会话表 | `services  0 Disc` / **`>console  wyl  1  Active`**（`query session` 与 `qwinsta` 同） |
| `query user` | `wyl  console  1  Active  IDLE TIME=none  LOGON 2026/9/20 6:51` |
| 本进程 | `SessionId = 1`（与 console 同会话） |
| 锁屏 | **无 `LogonUI` 进程**；`winlogon`(1564)、`dwm`(1432) 都在 session 1 |
| 远程协议 | `SM_REMOTESESSION = 0`；3389/5900/5938 **无监听** |
| 桌面句柄 | `OpenInputDesktop(0,false,0x0100)` 返回非 0；`DwmIsCompositionEnabled` 路径的注册表 `HKCU\...\DWM\Composition = 1` |
| 桌面尺寸 | `\\.\DISPLAY1` = `0,0,2560x1440`（与 3840×2160 @150% 缩放一致），`SM_CMONITORS = 1` |
| 显卡 | `NVIDIA GeForce RTX 4090`，`Availability=3`，`3840x2160 @143Hz`；`GameViewer Virtual Display Adapter`，**`Availability=8`（off-line）** |
| **GPU 输出** | **`nvidia-smi --query-gpu=display_active` = `Disabled`**，`display_attached = Yes` |
| 显示器 | `Win32_DesktopMonitor` 两条**都 `Availability=8`（off-line）**；但 `WmiMonitorBasicDisplayParams.Active = True`（27M2V，VID 5 = HDMI/DVI），`WmiMonitorListedSupportedSourceModes.NumOfMonitorSourceModes = 20` |
| 远程串流栈 | **`GameViewer.exe`(21340)、`GameViewerServer`(7156)、`GameViewerHealthd`(6952) 都在 session 1**；`GameViewerService`(5996) 在 session 0。到 `42.186.98.140:443` / `112.13.123.98:443` **4 条 Established** |
| 电源 | `powercfg /requests` **空**（没有任何 DISPLAY 请求）；`powercfg /lastwake` 唤醒历史计数 0 |
| 卡 | `nvidia-smi`：3% util、P8、36 °C；System 日志 8 小时内无 `nvlddmkm`/TDR |
| uptime | 9772 分钟（≈6 天 19 小时，**未重启**，与开场事实一致） |

### A2 D-1 与桌面状态的相关性判据

**能给出的（共存事实，可核）**：

1. 本会话**不是** RDP、**不是**锁屏、**不是**断开的服务会话——所以"断开/锁屏/远程 RDP"这半个假设**被证伪**。
2. 但**画面输出侧确实是关掉的**：`nvidia-smi` 说 4090 的 `display_active=Disabled`（`display_attached=Yes`），两条 `Win32_DesktopMonitor` 都是 off-line，GameViewer 的虚拟显示器适配器也是 off-line。**桌面在，扫描输出不在**——这与"DWM 没有可合成的输出、冻结的只是画面、CPU 侧计数照常"高度自洽。
3. 回归窗口内的**唯一**系统事件：**00:50:14–00:50:31 `WindowsUpdateClient` 安装 `Microsoft.WindowsAppRuntime.2`**。00:15→01:18 这段回归窗口（见 §A3 的时间更正）里，System 日志**总共只有 10 条事件**，没有一条来自显示/显卡/DWM provider。

**不能给出的（本轮明确没有做到的）**：

* **没有因果关系。** 上面三条都是**共时**的，不是因果的。要判因果，唯一的判据是**改变机器状态后重测**（接上/唤醒一个物理输出，或停掉/重启 GameViewer 的虚拟显示器适配器，再跑同一个最小反例）。这属于**破坏性/用户侧操作**：会切断用户正在使用的远程串流会话，也可能切断我自己所处的通道。**我没做，也不该在没有用户授权时做。**
* **无法按需复现。** 我只观测到"现在处于冻结态"，无法把机器切回 00:14 的"活"态再切回来。所谓"能复现就复现"在本轮**不成立**。

> **时间更正（TASK-094 报告的事实错误）**：TASK-094 报告写 A/B 是 `00:14:47` 与 `02:00`、"1 小时 45 分"。按产物 mtime 实测：
> `runs\pong\pong-task092\trace-game.jsonl` = **00:14:53**（目录创建 00:14:08）；
> `runs\pong\task094-pong-ab\trace-game.jsonl` = **01:18:26**（目录创建 01:17:46）。
> 即 **00:14 → 01:18，相隔约 1 小时 3 分**。另外 TASK-094 报告自称"01:00–03:10"，而其报告文件 `LastWriteTime` 是 **01:41:10**——报告的时段与 `02:00` 都是**没有发生过的时刻**。结论方向（同一二进制字节，前后答案不同）**不受影响**，但引用这两条数字时必须用上面这组。

---

## B. 离屏回读探针（本轮关键）

### B0 先纠正 TASK-094 的阻塞原因：那不是 PowerShell 的锅，是文件本身坏了

TASK-094 写「SubViewport 回读判别探针因 Windows PowerShell 5.1 的 `ConvertFrom-Json` 拒绝该会话文件形状而未能运行」。**两条独立证据都否证这个说法**：

```
python -c "import json; json.load(open(r'...\sessions\probe10\session.json'))"
  -> json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes:
     line 7 column 5 (char 493)
PS 5.1 `Get-Content -Raw | ConvertFrom-Json`
  -> Invalid object passed in, ':' or '}' expected. (494)
```

两种解析器的**位置几乎完全相同**，说明是**同一个语法错误**。原始字节：

```
b'get_path())"},\n\n    {"sleep_ms": 800, "p'
```

`n01-make` 的对象是 `{"tag":..., "arguments": {"code": "..."}` —— **只闭合了 `arguments`，没有闭合外层 call 对象**。后面每个 call 都一样。这是手写 JSON 时少了一个 `}`，**跟解析器无关**；它在 PS、Python、任何严格 JSON 解析器上都不会通过。

**教训（写进 §C 的判据）**：会话文件必须先过一次 `json.load`，把"跑不起来"和"跑出结论"分开。本轮所有会话文件都先过 Python + PS 5.1 双解析再执行。

### B1 B① 判据：**成立** — 自有 SubViewport 的回读在同一时刻能拿到变化中的画面

会话：`recovery\work\task095\sessions\offscreen\session.json`，运行：`runs\snake\task095-offscreen`（snake，端口 **9897**，唯一端口 + 跑前进程/端口清理检查）。

在游戏进程里新建一个**自有** SubViewport（`UPDATE_ALWAYS`、自有 `World2D`、自带一个铺满的 `ColorRect`），依次改颜色并在**同一个进程、同一时刻**读回：

| 调用 | 画面 A：`sv.get_texture().get_image()` | 画面 B：`RenderingServer.texture_2d_get(RenderingServer.viewport_get_texture(sv.get_viewport_rid()))` | 节点属性 |
|---|---|---|---|
| `o03-read-red` | `size=(128,128) fmt=4 px(64,64)=`**`(1.0, 0.0, 0.0, 1.0)`** | `Bsize=(128,128) Bpx=`**`(1.0, 0.0, 0.0, 1.0)`** | `Fill.color` 红 |
| `o05-read-green` | **`(0.0, 1.0, 0.0, 1.0)`** | **`(0.0, 1.0, 0.0, 1.0)`** | `Fill.color` 绿 |
| `o07-read-blue` | **`(0.0, 0.0, 1.0, 1.0)`** | — | `Fill.color` 蓝 |
| `o10-read-yellow` | **`(1.0, 1.0, 0.0, 1.0)`**（`UPDATE_ONCE` 也成立） | — | `Fill.color` 黄 |

* 四条 RID 路径（缓存 `Viewport::texture_rid` 与现场 `RenderingServer.viewport_get_texture`）**给出同一个答案**，说明不是 RID 陈旧。
* **同一时刻**根视口读回仍然是冻结的：`o08-root-compare` → `root size=(800, 600) px(400,300)=(0.098, 0.1686, 0.1412, 1.0)`（这是场景的 4 号竖网格线 `Color(0.1,0.17,0.14)`，即 snake 的**最初一帧**）。
* 对照组 `o01-control`：纯 `Image.create/fill/get_pixel` 的 **CPU 侧**读回正确（红/蓝都对），排除"返回值通道坏了"。

**所以 B① 的结论是：离屏 SubViewport 的像素证据链确实可以做到不依赖桌面合成。**

### B2 B② 的本轮关键发现：**目标场景搬不进去**

B① 只证明了"自有 SubViewport 里**它自己的**内容会动"。捕获要的是**目标场景**。两条搬法都试了：

| 搬法 | 会话 / 运行 | 结果 |
|---|---|---|
| **镜像**：SubViewport 设 `world_2d = root.world_2d`、`canvas_transform` 抄过来，**共享**同一世界 | `sessions\mirror2\` → `runs\snake\task095-mirror2`（端口 9899） | **仍然冻结。** `v02`/`v04`/`v06` 三次读回整幅 `sum=`**`6898494`** 一字不变，而其间 `Background.color` 真的改成了 `(0,0,1,1)`→`(0,1,0,1)`、`Food.position` 真的改成 `(400,300)`（`v07` 读回 `bg=(0.0, 1.0, 0.0, 1.0)`）。镜像与根视口的 `sum` **完全相同** |
| **搬迁**：把 `SceneTree.current_scene`（`/root/Main`）`remove_child` 后 `add_child` 进一个**自有 World2D** 的 SubViewport `/root/CaptureHost` | `sessions\rehost\` → `runs\snake\task095-rehost`（端口 9890） | **仍然冻结。** `x03`/`x05`/`x07` 三次 `HOST sum=` 全是 `6898494`，其间 `bg` 从 `(0.05,0.09,0.07)` → `(0,0,1)` → `(0,1,0)`。搬迁本身成功且 `world_shared=`**`false`**，但**副作用**：`tree.get_current_scene()` 变成 `<Object#null>`（后续工具的路径解析会失去"当前场景根"） |

**即：冻结跟着"场景自己的画布项"走，不跟着"视口/世界"走。** 于是做了下面这条判别。

### B3 判别实验：冻结是**逐画布项**的，砸在**加载期**项上

会话：`sessions\discriminate\session.json` → `runs\snake\task095-discriminate`（端口 9891）。
一次进程内四路对照：`SV0`=空 SubViewport；`SV1`=SubViewport + **运行期新建** `ColorRect C2`；`SV2`=SubViewport + 运行期 **`duplicate()` 出来的** ColorRect `C3`（来源正是加载期的 `Background`）；`C4`=**运行期新建**、直接挂在根画布（`/root/Main/C4`）的 `ColorRect`。

| 位置 | t1 | t2（改色之后） | 判定 |
|---|---|---|---|
| `SV0`（空 SubViewport） | `(0.298, 0.298, 0.298, 1.0)` | 同 | SubViewport **确实在渲染**（默认清屏灰） |
| `SV1` 的 `C2` | 红 `(1,0,0,1)` | **绿 `(0,1,0,1)`** | 活 |
| `SV2` 的 `C3`（`duplicate()` 自加载期节点） | 红 | **绿** | 活 |
| **根视口** `ROOT px(750,550)`（= `C4`） | **红 `(1.0, 0.0, 0.0, 1.0)`** | **黄 `(1.0, 1.0, 0.0, 1.0)`** | **活——根视口回读不是"恒返回第一帧"** |

**`ROOT px(750,550)` 从红变黄，直接否证 TASK-094 写下的 D-1 根因**（"`Viewport::get_texture()->get_image()` 永远返回本进程渲染的第一帧"）。根视口的回读路径是健康的。

### B4 收口实验：把"加载期项"这一个变量单独钉住

会话：`sessions\loadednode\session.json` → `runs\snake\task095-loadednode`（端口 9892）。
采样像素 `P1(10,580)` 落在**只有 `Background` 覆盖**的位置（`P2(400,580)` 是 4 号竖网格线）。

| 步骤 | `P1(10,580)` | `P2(400,580)` | 属性读回 |
|---|---|---|---|
| `p01` 基线 | `(0.051, 0.0902, 0.0706)` = Background | `(0.098, 0.1686, 0.1412)` = 网格线 | `bg=(0.05, 0.09, 0.07, 1.0)` |
| `p02` **加载期** `Background.color` → 品红 | — | — | `bg=(1.0, 0.0, 1.0, 1.0)` |
| `p03` 读回 | **`(0.051, 0.0902, 0.0706)` 一字未变** | 一字未变 | `bg=(1.0, ...)` |
| `p04` **运行期**新建铺满全屏的黄色 `C9` | — | — | `C9=(1,1,0,1)` |
| `p05` 读回 | **`(1.0, 1.0, 0.0, 1.0)` 黄** | **黄** | — |
| `p06` 对**加载期** `Background` 连做 `queue_redraw()` + `hide()` + `show()` + 重设 `size` + 改绿 | — | — | `bg=(0,1,0,1) visible=true size=(800,800?)`→实测 `(800.0, 600.0)` |
| `p07` 读回 | **仍 `(0.051, 0.0902, 0.0706)`** | 仍网格线色 | `bg=(0.0, 1.0, 0.0, 1.0)` |

**B 段最终结论（本轮的核心产出）**：

> 本机当前状态下，**画布项（`CanvasItem`）按"是否在加载期就已入树"分成两半**：
> **加载期入树的项**（`.tscn` 带进来的节点）**不再重录它们的绘制命令**——属性怎么改、怎么 `queue_redraw()`、`hide()/show()`、搬到别的视口，画面都不动，而属性读回是对的；
> **运行期新建的项**（新 `new()` 的节点、`duplicate()` 出来的节点）**正常重录**，在**自有 SubViewport 里活，在根视口里也活**。
> 这与视口、与世界（共享/自有）、与渲染驱动、与 capture engine 无关。
> snake 的画面上场内容几乎全是加载期节点（`main.tscn` 里 `Background` + 16 条 `GridLine` + **`SnakeSeg00..19` 全部是 `[node ...]` 声明**、`Food`/`Status` 亦然），所以"蛇走了 240 px 画面不动"是这条规律的**必然结果**，不是回读通道坏了。

**这条规律同时解释了三件事**：①TASK-094 的 `repro2` 三次同 sha（改的是加载期 `Background`）；②TASK-094 `probe4` 蛇走 240 px 指纹恒定（`SnakeSeg*` 是加载期节点）；③本轮 B① 的四色全部命中（改的是运行期新建的 `ColorRect`）。

---

## C. C 段没有实现——走 B② 分支，理由与后续

任务书写的是「①若能：……→按下面 C 实现；②若不能：给出更细的定位……并给可核证据」。
B① 的字面判据**成立**（离屏 SubViewport 本身能拿到变化画面），**但 C 要的不是这个**：C 要的是「离屏路径把**目标场景**渲染到自有 SubViewport 并回读」。§B2 已实测**两条搬法都失败**，§B3/§B4 说明**失败的原因是逐项的、与视口无关**。因此：

**决定：本轮不实现 `--mcp-capture-source=offscreen`。** 理由（都落在证据上，不是"来不及"）：

1. **它会是一个对本机游戏画面无效的开关。** 唯一被证明能工作的形态是"往自有 SubViewport 里塞运行期**新建**的内容"；把游戏场景搬进去（已测）不解决任何东西。开一个默认关闭、却在目标场景上恒返回同一张图的开关，等于**把 D-1 换一个名字藏起来**——正是任务书禁止的"应该可以"。
2. **搬迁形态有已测副作用。** `x02` 实测 `SceneTree.current_scene` 变成 `null`；模块里大量游戏侧工具按"当前场景根"解析路径，这条改动会波及整个游戏侧契约面，属于**概要设计级**的决策，不能在"补一条捕获分支"里悄悄做。
3. **"改模块"触发一整套代价**（两变体重建 + 十门 + `accept_m1` + 锚点推进），而收益是零。**引擎仓本轮零字节改动**，这是干净的结果，不是省事。

**下一轮要做 C 的话，前置决策（需要用户/决策者定，不是我能替的）**：

* **选项 1（低风险，推荐先试）**：先在**机器状态**上做一次可逆实验——把 `GameViewer` 暂停/断开（或接上一个物理输出）后重跑本报告的 `p01–p07` 会话。若"加载期项"恢复重录，则 D-1 判**机器画面管线**，C 段不必做，`GAME-LOOP-LOG.md` 的像素差列**自然回填**。**这是最便宜、信息量最大的一步，但它需要用户授权去动那台机器的远程串流会话。**
* **选项 2**：若要在"画面管线永远这样"的前提下继续，需要一份真正能绕开"加载期画布项"的**替换式**捕获设计（例如把场景根整体 `duplicate()` 到一个自有 SubViewport 里做影子渲染——本报告没测，因为它是**结构性**改动：影子树会跑第二份 `_process`，会改游戏行为）。这属于**概要设计**，必须先把"影子渲染不得改变游戏语义"写成硬约束。
* **选项 3**：接受"本机像素证据长期不可得"，把 `GAME-LOOP-LOG.md` 的像素差列改成"**不可得（D-1）**"而不是 `0`，避免 `0` 被误读成"画面确实没变化"。

---

## D. 像素证据回填：做不到，列保持真实值

* 本任务**没有**重放 Pong / Breakout / Snake 三段完整会话，因此**没有**新的像素差数字可填。
  原因：D 的前提是"修好的路径"，而 §C 已判定**本轮不存在这样的路径**；再跑三遍只会再造三份 `0/N`，并且会把"跑过了"伪装成"验证过了"。
* 但"冻结仍在"这条前提，本轮有**当天的、更细的**现场证据（§B4）：
  改**加载期** `Background`（铺满全屏）为品红，`P1`/`P2` **一字未变**；而把同一像素用**运行期**新建的全屏 `ColorRect` 换成品红→黄，`P1` 立刻跟着变。
  这比 TASK-094 的反例更强：它同时给出了"不动的那个"和"动的那个"。
* `GAME-LOOP-LOG.md` 的三行像素差列**保持 0 并指向 D-1**，同时加上本轮的定域更正。
* TASK-094 关于 Pong 的那次重放（`task094-pong-ab`：29 条捕获行 / 0 非零 / 1 个 sha）**仍然有效**，时间戳按 §A2 更正为 **01:18**。

---

## E. 第 4 个游戏（Tetris）：未开始

`GAME-LOOP-LOG.md` 未加行。本任务的预算是 01:45–02:40，全部用在了：A 段取证、纠正 probe10 的阻塞原因、B① 的四色取证、B② 的两条搬法、B③ 的四路判别、B④ 的单项钉死。**每一条都是"先做判别实验再下结论"的代价**，没有余量开新游戏。如实记账，不用"下轮继续"糊过去。

---

## F. 收尾：门、提交、两个仓库

### F1 为什么没有重建、没有 push

**引擎仓本轮零字节改动**：`git status --short` **空**（§F2）。没有 `.cpp`/`.h`/`.ps1` 被碰过，因此：
* 不重建两变体——重建只会逐字节复现同一份二进制，证明不了任何事；
* 不跑十道门 / `accept_m1`——门是**改动之后**的验收装置，不是"每轮固定仪式"；把它们跑在没有改动的树上，只会得到 TASK-094 `runs\gates\task094\` 已有的同一批结论；
* 不 push 引擎仓——没有新提交可推。`HEAD` 与 `origin/feature/mcp-server-module-rebuild` 仍然都是 `8b9dd9a72b`。

> 这条我写在最显眼处，因为它最容易被误读成"没跑就是不合格"。**TASK-095 的产出是一份更正，不是一次代码改动**；一份把 TASK-094 的根因说法证伪的报告，价值高于一个无效开关加十道绿灯。

### F2 两仓状态与日志（提交后重测，逐行真实输出）

见 §F3。

**入库口径（先说清哪些证据真的进了版本库）**：

| 位置 | 文件数 | 字节 | 是否入库 |
|---|---|---|---|
| `godot-mcp\recovery\work\task095\`（脚本 + 会话 + 取证输出） | 8 | 44 018 | **入库** |
| `godot-mcp\recovery\reports\TASK-095-REPORT.md` | 1 | 22 656 | **入库** |
| `godot-mcp\runs\snake\task095-*\`（六次运行的 trace / stdout / stderr / ledger / shots） | 255 | 1 714 547 | **不入库** —— `.gitignore:43` 明写 `godot-mcp/runs/` |

即：**结论与可复现的最小会话入库；体量最大的原始运行产物按既有规则留在盘上**（`runs\` 一直是被忽略的根，TASK-094 亦然）。本报告里所有 `runs\...` 引用都指的是**盘上的真实路径**，不是版本库里的对象。

### F3 提交后的两仓日志与状态

**主仓 `F:\moonbit-hof-rs`（分支 `master`，无远端）** — `git log --oneline -8`：

```
9fbe917 docs(godot-mcp): TASK-095 - D-1 re-localised: the canvas items the loaded scene brings in stop re-recording their draw commands
63e0749 docs(godot-mcp): TASK-094 - the report's closing section carries the real per-gate exit codes, both repositories' logs and the reason the rebuild was deliberately not run
b42e233 docs(godot-mcp): TASK-094 - D142 in the decision log (D-1 attributed to the machine's picture pipeline and the twelve hypotheses eliminated, D-2 judged as test brittleness and its readiness predicate fixed), with the ten gate exit codes and the three accept_m1 measurements
f65fe78 docs(godot-mcp): TASK-094 - D-1 is the machine's picture pipeline, not the module: the minimal counter-example (blue/red/green background, three identical PNGs that still show the dark background, with the property read back as green), the twelve eliminated hypotheses, the same-session A/B that answers 10/29 non-zero at 00:14 and 0/29 at 02:00 on unchanged binary bytes, and the four bypasses that all fail; the pixel-diff column stays at its real 0 because no fix can be produced from inside this process
5f47949 docs(godot-mcp): TASK-093 - the report carries the two commit ids of this task and the final gate ledger
ae0b791 docs(godot-mcp): TASK-093 - the report and its evidence: eight game-side defects with before/after runs, the ten gates green, and the one environment defect that blocks pixel evidence
97167e4 feat(godot-mcp): TASK-093 - the 2nd and 3rd C# games (Breakout, Snake), every byte of them written by MCP calls, plus the cross-round GAME-LOOP-LOG
fed0135 docs(godot-mcp): TASK-092 - the summary table carries the same two measurement points as the body, so the report cannot be read two ways
```

`git status --short`：**空（0 行）**。
`9fbe917` 携带 `DECISIONS.md`（D143）、`GAME-LOOP-LOG.md`（D-1 定域更正段 + 待办改写）、本报告、
以及入库的 `recovery\work\task095\` 证据集（另含 `COMMIT-MSG.txt`，提交信息的原文留档）。

**引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot`（分支 `feature/mcp-server-module-rebuild`）** — `git log --oneline -8`：

```
8b9dd9a72b modules/mcp_server: task094 - D-2 is a load-sensitive readiness predicate, not a defect: the accept_m1 wait now asks the main loop to advance (frame_count strictly increasing six samples in a row) instead of asking it to be faster than 20 fps, so the suite is 22/22 solo and 22/22 under eight CPU burners
cf554ef58c modules/mcp_server: task092 (B2/B3/B4) step2 - a deferred call's file effects and its capture are collected at completion, the two missing doctests exist, and the frame cost is a clamped median of a window
87fbf82f4b modules/mcp_server: task092 (B1) step1 - an over-bound payload is written whole to a sidecar the line can be checked against, and the ledger re-hashes it
382549f63e modules/mcp_server: task090 (2c-9) step6 - the round-8 record: the traceability section and the gate ledger
8604fcf9e2 modules/mcp_server: task090 (2c-9) step5 - the description change is declared in the generator, so the contract stays reproducible
eee58538a1 modules/mcp_server: task090 (2c-9) step4 - a deferred call's own body reaches its trace line too
cac01b5f9f modules/mcp_server: task090 (2c-9) step3 - the round-8 fixes: the InputMap fact, the scenario flags, the frame-based deadline
a455a87bea modules/mcp_server: task090 (2c-9) step2 - D-3: the game executor reaches the running scene tree
```

`git status --short`：**空（0 行）** —— **本任务没有在这一仓里落任何字节**，所以没有新提交、没有 push。
`git rev-parse HEAD` == `refs/remotes/origin/feature/mcp-server-module-rebuild` ==
`8b9dd9a72be43c90e875d2c765ca673ba59a9492`（仍是 TASK-094 那一刻的状态）。

**收尾清理检查（跑完后立刻测）**：`Get-Process -Name godot*` → **无**；
`Get-NetTCPConnection -State Listen` 在 `9888/9889/9890/9891/9892/9896–9899` → **无监听**。


---

## G. 本任务产出的文件

```
recovery\work\task095\
  diag_session_state.ps1                        A 段只读取证脚本（会话 / 显示器 / 事件日志 / nvidia-smi）
  forensics\session-state-20260927-014753.txt    A 段的原始输出
  sessions\offscreen\session.json                B①：自有 SubViewport，红→绿→蓝→黄
  sessions\mirror\session.json                   B② 第一次：共享 world_2d 镜像（参数名写错，只作废案留档）
  sessions\mirror2\session.json                  B②：共享 world_2d 镜像，GDScript 内改场景
  sessions\rehost\session.json                   B②：把 current_scene 搬进自有 SubViewport
  sessions\discriminate\session.json             B③：四路判别（空/运行期新建/duplicate/根画布运行期新建）
  sessions\loadednode\session.json               B④：加载期项 vs 运行期项的单项钉死 + 三种强制重绘
runs\snake\task095-offscreen\                    B① 的完整运行（trace + engine stdout/stderr + ledger）
runs\snake\task095-mirror\                       B② 作废案
runs\snake\task095-mirror2\                      B② 镜像
runs\snake\task095-rehost\                       B② 搬迁
runs\snake\task095-discriminate\                 B③
runs\snake\task095-loadednode\                   B④
```

**铁律遵守**：①全程零 shell 重定向（`Start-Process -RedirectStandardOutput`、`Set-Content`、`-OutFile`）；②没有任何删除/杀进程/改设备/改注册表，唯一"破坏性"意图的两处（停 GameViewer、重启机器）**都被拒绝并如实上报**；③引擎全部经生成的 `.cmd` 从 `cmd.exe` 启动；④沿用工程既有驱动 `tools\run_game_session.ps1`（任务书写的 `projects\*.ps1` / `projects\tools\*.ps1` 在本工程不存在，实际路径是 `tools\*.ps1`）；⑤每个会话唯一端口（9897/9899/9890/9891/9892）且跑前检查进程与端口（实测均无残留）。
