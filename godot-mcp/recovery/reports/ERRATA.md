# ERRATA — 老报告勘误索引（TASK-149 建）

> **本文件的定位**：TASK-149 的文档校对范围是「**规范类 + 最新报告**」（见
> `recovery/tasks/TASK-149.md` §E.9）。**老报告一律不改**——它们是被引用的历史证据，
> 改它们等于篡改证据。老报告里已被发现的不自洽，**索引到这里**，逐条给
> 「**文件 / 原说法 / 更正 / 依据**」，让后来者不必重踩。
>
> **口径纪律**（与 `TASK-140-REPORT.md` §K、`TASK-136-REPORT.md` §「勘误（TASK-138）」相同）：
> * 更正**只增不改**，不改老报告里的一个字；
> * 每条更正**只有一个来源**：给出台账/产物路径与**可复算命令**；
> * **代码优先**：与代码冲突时，以代码为准，并写明是哪一行代码；
> * 更正**不改变任何结论的定性**——下面每一条都写清"结论受不受影响"。
>
> 建立者：TASK-149（2026-09-28）。行号一律写**当前仓里的路径**（`godot/modules/mcp_server/...`
> 这类完整前缀，不再用 `tools/...` 这种相对缩写）。

---

## 索引（按严重度）

| # | 文件 | 一句话 | 严重度 |
|---|---|---|---|
| **E-1** | `recovery/reports/TASK-140-REPORT.md` | 同一份报告里命令条数同时写 `194` 与 `186`，**权威口径是 194** | major |
| **E-2** | `recovery/TEST-CASES.md`（TASK-146 版） | "**121** 条 `missing_required`"**不可复现**；实测 **142 = 119 + 21 + 2** | major |
| **E-3** | `recovery/reports/TASK-129-REPORT.md` §9.4 | "本机只有**一个**仓"**与事实不符**；本机有**两个**有效的仓（外层 + 嵌套引擎仓） | minor |
| **E-4** | `recovery/reports/TASK-136-REPORT.md` §7 第 9 行 | platformer 帧的 HUD 写成 `TILE 4,27`，实测 **`TILE 3,27`** | major |
| **E-5** | `recovery/reports/TASK-136-REPORT.md` §4.1 / §1.2 | §4.1 的 platformer **strict 列**与顶层 verdict 不符；§1.2 的 `PASS(baseline only)` **举例不是** platformer | minor ×2 |
| **E-6** | `recovery/reports/TASK-136-REPORT.md` | 逐条勘误里 §3.5 的 `16/95`、§11.2 的三处哈希/条数 —— **原报告自己已经收了口**，此处只做索引 | minor |
| **E-7** | `recovery/reports/ACCEPTANCE-TASK-137.md` | 本报告全篇 `tools/playtest_player.py:NNN` 行号指向**验收当时的冻结版**，TASK-142 插入后**位移不是常数**（+58/+99/+119/+174） | minor |
| **E-8** | `recovery/reports/ACCEPTANCE-TASK-141.md` | 同上：该报告的行号指针同样指向冻结版 | minor |
| **E-9** | `recovery/reports/TASK-142-REPORT.md` | D211 引的 `runs/model-player/_scripts/t142_code_revision.json` 在 `runs/**`（**被 gitignore、不入库**），从 git 历史里**不可复得** | minor（限制登记） |
| **E-10** | `recovery/reports/ACCEPTANCE-TASK-145.md` | 该报告的 `pytest 27 passed`、`TC-PY 404`、`合计 785` 都是它**当时的真实读数**，但已被 TASK-146 的 `03839a5` 取代；**它不是错的，是过期的** | info |
| **E-11** | `recovery/reports/` | TASK-149 任务书 §E.9 点名了 `TASK-147-REPORT.md`，**该文件不存在**（TASK-147 是独立验收，只有 `ACCEPTANCE-TASK-147.md` 与 `TASK-147-ACCEPT.md`） | info |
| **E-12** | `recovery/reports/ACCEPTANCE-TASK-147.md` | 它自己点名的 Y1（`121`）、X5（`model_player 272` 标签）、X6（E4 的"25 处"）**在 TASK-149 之前一直没有被落进 `TEST-CASES.md`** | info（已由 TASK-149 §E 落实 Y1） |

---

## E-1 — `TASK-140-REPORT.md`：命令条数 `194` vs `186`

* **文件**：`recovery/reports/TASK-140-REPORT.md`
* **原说法**：**同一份报告里两个数字**——
  * §I 顶部与 §E.Y10 写「**194** 条命令 / 0 命中」；
  * §I.3 两处（"它们不在 **186** 条台账内"、"所有写盘与所有启动游戏的命令都经
    `t140_cmd.py` 入台账（**186** 条）"）与 §F 表
    （`t140_redirect_scan.json | 186 条命令 / 0 命中`）写 **186**。
* **更正**：**只有一个数字，权威口径是 `194`。** 切法必须写死：
  * 切点 = 共享台账 `runs/model-player/_scripts/t136_commands.jsonl` 里**第一条**
    `source == "t140-wrapper-call"` 的条目（TASK-140 当时的 idx **501**，
    ts `2026-09-28T07:02:21`）；
  * 终点 = **最后一条** `t140_scan_redirects.py` 条目（当时 idx **694**）；
  * `694 − 501 + 1 = **194**`。
  * **`186` 不对应任何切法**：按 argv 切是 190（TASK-140 自己已否决）；按"末次扫描之后不再
    计数"的另一种读法也给不出 186。台账在扫描之后又多了 **15** 条收尾命令，所以"现在"从头到尾
    数是 **209** —— 194 与 209 的差额就是那 15 条。
* **依据（可复算，一手）**：
  * 锚点：`runs/model-player/_scripts/t142_redirect_scan.json -> task140_ledger_erratum`
    （`first_task140_index: 501`、`last_scan_entry_index: 694`、
    `authoritative_count_at_last_scan: 194`、`authoritative_scan_at_last_scan.redirect_hits: 0`、
    `count_now: 209`、`after_scan_count: 15`，且那 15 条逐条列出）。
  * **TASK-149 独立重算**（`python recovery\work\task149_ledger.py`，2026-09-28）：
    台账现有 **710** 行；第一条 `source == "t140-wrapper-call"` 在 idx **502**、
    最后一条 `*_scan_redirects.py` 在 idx **695**；`695 − 502 + 1 = **194**`（**区间宽度稳定**，
    两个下标相对锚点各 +1 是因为台账在锚点记录之后又追加了新条目）；扫描之后的条目 **15** 条。
    即：**194 这个数在锚点记录时与现在都成立**，`186` 在任何时点都不成立。
* **结论受影响吗**：**不受影响**。重定向命中数 `0` 与那两条台账外例外（预台账 ~39 条只读侦察、
  1 条直接正则改写 `Ready→BirdReady`）都不变；变的只是那个总数。
* **原报告自己的处置**：`TASK-142-REPORT.md` §K.1 已经**只增不改**地在本报告**文末**追加了勘误小节
  （正文一字未动）。本条目是它的**索引**，不是重做。

---

## E-2 — `TEST-CASES.md`（TASK-146 版）：`121` 条 `missing_required` 不可复现

* **文件**：`recovery/TEST-CASES.md`（TASK-146 落账时的 §1.2「对抗性结论」段与 §9.3 U2；
  该文件属**规范类**，所以 TASK-149 **就地改掉了**，见 §10.7 F1）
* **原说法**：
  > 活的 `-32602` 里有 **121 条 `missing_required`** + **21 条 `wrong_type`** 不是注册器参数门发出的
* **更正**：**142 条 `refused_-32602` 的正确划分是 `119 + 21 + 2`，`121` 不对应任何实测划分**：

  | 段 | 条数 | 消息逐字（前缀） | 发出点（代码） |
  |---|---|---|---|
  | `missing_required`（带冒号） | **119** | `Missing required parameter: <k>` | `godot/modules/mcp_server/tools/tool_builder.cpp:207-232` 的 `require_string()` / `require_int()`（handler 侧共享读取器） |
  | `wrong_type` | **21** | `Parameter '<k>' must be a …, got …` | 同一批 `tool_builder.cpp` 读取器 |
  | `missing_required`（**无冒号**） | **2** | `Missing required parameter '<k>'` | `godot/modules/mcp_server/tools/editor_node_write.cpp:1040`（`editor_set_auto_dismiss_dialogs`）、`godot/modules/mcp_server/tools/editor_node_property_updates.cpp:435`（`editor_set_node_property_updates`）——**两个工具自己的 handler 内联写的消息，不是 `tool_builder.cpp`** |
  | **合计** | **142** | | `119 + 21 + 2 = 142` |

* **依据（可复算，一手）**：
  * 产物：`recovery/work/task143/probe-live.json`（`counters.refused_-32602 = 142`，
    逐工具的 `error_message` 原文）；
  * 复算：`python recovery\work\task149_docaudit.py c1` →
    `MISSING_REQUIRED_COLON = 119`、`MISSING_REQUIRED_NO_COLON = 2`、`WRONG_TYPE = 21`、
    `TOTAL = 142`，并**逐条打印**那 2 条无冒号的消息与工具名；
  * 代码：`tool_builder.cpp:207-232`（`require_string` / `require_int` 的
    `"Missing required parameter: " + p_key` 与 `_type_error_message(...)`）；
    `editor_node_write.cpp:1040`、`editor_node_property_updates.cpp:435`（`"Missing required parameter '…'"`）。
* **结论受影响吗**：**定性结论不受影响**，两点都不变——
  ① 这 142 条中有 140 条发生在 **handler 执行路径内**（`tool_registry.cpp:880` 的
  `def->handler(p_args, r_error)` 之后）⇒ 属于**行为反例**（准确说：契约级入参校验行为）；
  ② 两条 `editor_simulate_mouse_*` 的探针只到 `tool_registry.cpp:864` 的
  `_reject_unknown_arguments()`（在 handler **之前**）⇒ 只证明**参数门**，是**弱**反例。
  因此承重的 **`175/177` 强反例 + 2 条弱** 不依赖这个子数字。
* **谁先发现的**：`ACCEPTANCE-TASK-147.md` 的 **Y1（major）**（它写"121 不存在"、给的是
  119/21/2 与同样的两个代码发出点）。TASK-146 当时**没有**把 Y1 落进 `TEST-CASES.md`；
  TASK-149 落实（§10.7 F1）。

---

## E-3 — `TASK-129-REPORT.md` §9.4："本机只有一个仓"

* **文件**：`recovery/reports/TASK-129-REPORT.md` §9.4（第 464 行起）
* **原说法**：
  > ### 9.4 仓库与提交（本机只有**一个**仓）
  > `godot-mcp\` 不是独立仓库（无 `.git`），它是 `F:\moonbit-hof-rs` 的子目录（与 TASK-128 §8.3 一致）
* **更正**：
  * 关于**外层**的判断是对的：`godot-mcp\` 自身确实没有 `.git`，它是 `F:\moonbit-hof-rs`
    的子目录。`git -C F:\moonbit-hof-rs rev-parse --show-toplevel` → `F:/moonbit-hof-rs`。**这部分不用改。**
  * **"本机只有一个仓"是错的**。本机在 `F:\moonbit-hof-rs` 这棵树里有**两个**与本项目直接相关、
    各自独立、各自有分支的 git 仓：
    1. **外层仓**，toplevel = `F:/moonbit-hof-rs`，分支 `master`（`godot-mcp/` 的一切都在这里）；
    2. **嵌套引擎仓**，toplevel = `F:/moonbit-hof-rs/godot-mcp/godot`，分支
       `feature/mcp-server-module-rebuild`（Godot 引擎 fork；`godot-mcp/recovery/tasks/README.md`
       第 40 行明确承认"引擎仓（`godot-mcp/godot/`，自带 `.git`）也是共享的"）。
  * 另有 1 个**与交付无关**的第三方源码克隆 `runs/playability/PlayJev-src/.git`（`runs/**` 被 gitignore，
    不属于任一交付分支），以及外层仓的 `.git`。所以严格说本机有 3 个 `.git` 目录，
    其中**属于本项目、需要同时看 git 状态的是 2 个**。
* **依据（可复算，一手）**：
  ```bat
  git -C F:\moonbit-hof-rs                  rev-parse --show-toplevel
  git -C F:\moonbit-hof-rs\godot-mcp\godot  rev-parse --show-toplevel
  git -C F:\moonbit-hof-rs\godot-mcp\godot  branch --show-current
  ```
  实测：`F:/moonbit-hof-rs` / `F:/moonbit-hof-rs/godot-mcp/godot` /
  `feature/mcp-server-module-rebuild`。`git status --short` 在两个仓里**各看各的**：
  例如 TASK-149 期间外层仓有 7 个待提交路径，而引擎仓只有 `.gitignore` 一处改动。
* **结论受影响吗**：**不受影响**——TASK-129 的实质结论（它的提交都落在 `F:\moonbit-hof-rs`
  这一个外层仓、`godot-mcp\` 不是独立仓）成立。**受影响的是"几个仓"这个计数与由它推出的操作纪律**：
  "提交前看 git 状态"必须**两个仓各看一次**（这正是 TASK-149 报告 §9 同时给两仓
  `git log --oneline -5` / `git status --short` 的原因）。

---

## E-4 — `TASK-136-REPORT.md` §7 第 9 行：platformer 帧 HUD `TILE 4,27`

* **文件**：`recovery/reports/TASK-136-REPORT.md` §7 第 9 行（正文第 446 行）
* **原说法**：
  > `runs\model-player\t136-scripted-final\platformer\scripted\frames\004_01_after.png` |
  > 800×600 | 同一关卡，HUD 变成 **`TILE 4,27`**，蓝玩家明显右移两格 | **玩家真的向右移动了两格**
* **更正**：该帧 HUD 实测是 **`TILE 3,27`**（不是 `4,27`）；"右移两格"与图上的 `TILE 3`
  自相矛盾，**删去"两格"这个量词**。
* **依据（可复算，一手）**：
  * 帧：`runs\model-player\t136-scripted-final\platformer\scripted\frames\004_01_after.png`
    （10801 B，800×600，sha256 `54e9873333c3edbb2ac3797778462f7bdc8d7a265a519dbd8d73d822e651ef05`）；
    TASK-138 用 `read_image` 实看，读到的 HUD **逐字**是
    `GEMS 0/14  SCORE 0  LIVES 3  AIR 0  TILE 3,27`。
  * **可机检锚点**（TASK-138 §1.C.2 要求的写法，原报告文末已补）：
    `TILE=3,27`（`PlayerX=226, PlayerY=432` → 列 3 / 行 27，格宽 16 px）、`LIVES=3`、
    `GEMS=0/14`、`SCORE=0`；`step 1` 的 `PlayerX 42→86`（`plat_right`）、
    `step 2` 的 `PlayerX 118→194`（`plat_jump`）、`step 3` 的 `LIVES 3→2`；
    状态：`...\platformer\scripted\steps.jsonl`
    sha256 `004671fe88706f75a95ee06c786927f35338d765f2e37ac4dfaf5b7dd47f2a09`（118767 B）。
  * 该 run 汇总：`...\platformer\scripted\player.json`
    sha256 `a823fd9fab9f214fe6ce262e3cd43a84e37675d0c3768619ce36266b1fd7b3f1`（13312 B）。
* **结论受影响吗**：**不受影响**。该行要证明的结论（**修后玩家确实动起来了**）仍然成立，
  依据是同一 run 的逐步读数 `PlayerX 42→86`、`LIVES 3→2→1`、像素差 `599 → 737 → 1088`。
* **原报告自己的处置**：`TASK-136-REPORT.md` 文末的「勘误（TASK-138）」**①** 已给出完整更正并
  **补上了可机检锚点行**（本节即其索引）。

---

## E-5 — `TASK-136-REPORT.md` §4.1 的 strict 列、§1.2 的 `PASS(baseline only)` 举例

* **文件**：`recovery/reports/TASK-136-REPORT.md` §4.1（正文第 209/212 行一带）、§1.2（正文第 84 行一带）
* **原说法**：
  1. **§4.1 脚本臂表**里 `platformer` 行的 **strict 列填 `FAIL`**，而该 run 的
     `player.json -> verdict` 实为 **`INCONCLUSIVE`**（`strict_verdict=FAIL`、
     `game_side_verdict=FAIL`、`baseline_verdict=PASS`、`counts_as_pass=False`）——**顶层 verdict
     与"strict 列"是两码事**（strict 只是三种情形之一，顶层还有 INCONCLUSIVE 分支）。
  2. **§1.2 「一处实测示范（`PASS(baseline only)` 真的出现了）」** 举的例子，读者容易读成 platformer；
     **真正的示范是 `pong × jev × V3`**（`strict` 边缘步 2 = **1.202×**），
     脚本臂的两个真例是 **`asteroids`**（baseline PASS / strict FAIL ⇒ 顶层 `PASS(baseline only)`）
     与 **`pong`**；platformer 的脚本臂顶层 verdict 是 `INCONCLUSIVE`，**不是** `PASS(baseline only)`。
* **更正**：
  * §4.1 的 platformer 行：**strict 列应为 `FAIL`**（这一格原报告填对了），要改的是**读者对它的解读**——
    **不能**从 "strict=FAIL 且 baseline=PASS" 推出"顶层是 `PASS(baseline only)`"，因为顶层还可能是
    `INCONCLUSIVE`。原报告的 **§4.1 表头**把三态（游戏侧）与 strict/baseline 并列，但没有一句话
    说明"顶层 verdict 不等于 strict 列"，这是**表述缺口**而非数字错误。
  * §1.2 的举例：**真例是 `pong`（模型臂示范）+ `asteroids`（脚本臂）**；platformer **不是**
    `PASS(baseline only)` 的例子。
* **依据（可复算，一手）**：
  * `runs\model-player\t136-scripted-final\platformer\scripted\player.json`
    （`verdict = INCONCLUSIVE`、`strict_verdict = FAIL`、`baseline_verdict = PASS`）——
    这正是 `ACCEPTANCE-TASK-137.md` 的 **D-6** 与 **D-7** 点名的两条 minor；
  * `runs\model-player\t136-scripted-final\asteroids\scripted\player.json`
    （`verdict = PASS(baseline only)`、`counts_as_pass = false`、边缘步 3=1.309×、11=1.442×）；
  * `runs\model-player\t136-jev-v3\pong\jev\player.json`
    （`verdict = PASS(baseline only)`、`counts_as_pass = false`、`strict_fail_steps = [2]`、
    `change_margin_edge_steps` 步骤 2 `margin_ratio = 1.202`）。
* **结论受影响吗**：**不受影响**。`strict` 是 PASS 默认判据、`PASS(baseline only)` 不计入通过数、
  脚本臂分布 **9 PASS / 1 PASS(baseline only) / 4 FAIL / 6 INCONCLUSIVE** 全都成立。
* **原报告自己的处置**：文末「勘误（TASK-138）」**⑥**（§4.1 strict 列）与 **⑦**（§1.2 举例）
  已逐条给出；本节是其索引。

---

## E-6 — `TASK-136-REPORT.md` 的其余已收口勘误（索引）

`TASK-136-REPORT.md` 文末的「勘误（TASK-138）」已经**只增不改**地收口了 7 条。除 E-4/E-5 已单独
索引的 ①⑥⑦ 外，其余 4 条在此**只做索引**（原文、更正、依据俱在该报告文末，不重复搬运）：

| 该报告的勘误号 | 位置 | 一句话 |
|---|---|---|
| ② | §11.2（正文第 632 行） | `t136_redirect_scan.json` 的 sha256 前缀与磁盘不符；磁盘实测 `3ac18ad769996410…`（15994 B） |
| ③ | §3.5（正文第 182 行） | 台账拆分 `16/95` 实为 **`17/94`**（按 `source == "manual-backfill"` 精确计数） |
| ④ | §11.2（正文第 631 行） | "截至 111 条"的台账哈希不可核、截点口径不清；改为给行数 + 截点行逐字内容 + 末行 ts |
| ⑤ | §11.2 / §11.4 | 首版报告哈希自指、不可核（这是哈希的定义，不是失误） |

**另注（TASK-149 复算）**：该报告 §3.5 与 §11.2 引用的
`runs/model-player/_scripts/t136_commands.jsonl`、`t136_redirect_scan.json` 都在
`runs/**` 下，而 `runs/**` **被 `.gitignore` 忽略、不进提交** ⇒ 这些路径**只存在于本机**，
从 git 历史里不可复得（该报告 §11.2 的第 10 条自己也这么声明了）。因此本节的所有依据都只能
**在本机复算**，这是**限制登记**，不是新的缺陷。

---

## E-7 / E-8 — `ACCEPTANCE-TASK-137.md` / `ACCEPTANCE-TASK-141.md`：行号指针指向冻结版

* **文件**：`recovery/reports/ACCEPTANCE-TASK-137.md`、`recovery/reports/ACCEPTANCE-TASK-141.md`
  （两者都属**最新报告**，TASK-149 已在各自**文首追加**了只增不改的位移说明与逐条对应表）
* **原说法**：两份报告正文里的 `tools/playtest_player.py:NNN` 指针，例如
  `ACCEPTANCE-TASK-137.md` 的 `:785-793`、`:722-801`、`:881-1048`、`:2326`，
  `ACCEPTANCE-TASK-141.md` 的 `:2286-2308`（`_pong`）、`:349`、`:1170`、`:3804-3813`。
* **更正**：这些行号**指向两份报告验收当时的冻结版本**，不是现在仓里的版本。冻结版 = 现在仓里的
  `tools/playtest_player_t142_prefix.py`（**4905 行**，277930 B），它**逐字节等于**
  `71f92e8^:godot-mcp/tools/playtest_player.py`（`diff --strip-trailing-cr` 结果 0 行）。
  TASK-142 后来在该文件插了几段新代码，所以**位移不是常数**：实测分段为
  **+58 / +99 / +119 / +174** 行。逐条对应表见 `ACCEPTANCE-TASK-137.md` 文首的 TASK-149 追加段。
* **依据（可复算，一手）**：`python recovery\work\task149_stalepointers.py ACCEPTANCE-TASK-137`
  （或 `ACCEPTANCE-TASK-141`）——打印每个指针**今天**落在哪一行、该行原文、以及前后 60 行内的
  `def`/`class` 符号。`python recovery\work\task149_frozenmap.py` 另打印冻结版的 4905 行与
  一组符号在两个版本里的行号对照。
* **顺带更正（行为变化，不只是行号）**：`ACCEPTANCE-TASK-137.md` 的 **E12-d**
  把 `playtest_player.py:2326` 的 `ack_state_for_verdict = inj.get("ack_result") or pre_ack`
  列为"代码里留有一条窄缝（会退回注入前的读）"。**那条兜底已经不存在**：TASK-138 defect ⑨
  （提交 `648b94c`，其提交信息第一句就是"forbid the pre-injection ack fallback"）把它删掉了；
  现在 `tools/playtest_player.py:3426-3450` 明确**不回退 `pre_ack`**，`:3428` 的注释逐字点名
  旧 `:2326`。冻结版 `tools/playtest_player_t142_prefix.py:3253` 也已经是删掉之后的形态
  （它由 `71f92e8` 入库，而 `71f92e8` 在 TASK-138 之后）。
  **E12-d 的其余结论不受影响**（两臂 409/409 步都没走到那条兜底；`pre_ack_used_as_evidence`
  之类字段现在写的是 `false`）。
* **结论受影响吗**：**不受影响**。两份报告的结论都建立在判据与产物证据上，不建立在行号上。

---

## E-9 — `TASK-142-REPORT.md`：`t142_code_revision.json` 不可从 git 复得

* **文件**：`recovery/reports/TASK-142-REPORT.md`（`DECISIONS.md` D211 也引了同一路径）
* **原说法**：D211 的回滚点写"冻结副本 `tools/playtest_player_t142_prefix.py` 与
  `runs/model-player/_scripts/t142_prefix_code/` 都保留了修前字节，**sha256 见
  `_scripts/t142_code_revision.json`**"。
* **更正**：`runs/**` **被 `.gitignore` 忽略、不入库**，所以
  `runs/model-player/_scripts/t142_code_revision.json` 与 `runs/model-player/_scripts/t142_prefix_code/`
  **只存在于本机**，从 git 历史里**不可复得**；能进历史、且可跨机复算的只有
  `tools/playtest_player_t142_prefix.py`（TASK-149 §B 已入库，`71f92e8`；**277930 B**，
  与 `71f92e8^:godot-mcp/tools/playtest_player.py` 逐字节相同）。
  **建议**：将来引用"修前字节"时，优先引 `tools/playtest_player_t142_prefix.py`（入库、可跨机），
  `runs/**` 下的副本只作本机对照。
* **依据（可复算，一手）**：`.gitignore` 对 `runs/**` 的忽略规则；
  `ls tools/playtest_player_t142_prefix.py`（277930 B）与
  `git show 71f92e8^:godot-mcp/tools/playtest_player.py | wc -c`（277930）相等。
* **结论受影响吗**：**不受影响**——回滚点仍然存在，只是它的**可跨机那一半**是
  `tools/playtest_player_t142_prefix.py`。

---

## E-10 — `ACCEPTANCE-TASK-145.md`：`27 passed` / `404` / `785` 是过期，不是错误

* **文件**：`recovery/reports/ACCEPTANCE-TASK-145.md`
* **原说法**：结论速览与 §0 命令表的 `python -m pytest tools\tests …` → **`27 passed in 1.09s`**；
  §1.1 的 `TC-PY-* = 404`、合计 `785`。
* **更正**：这三个数字是**该验收当时（TASK-144 之后、TASK-146 之前）的真实读数**，
  **没有错**。TASK-146 的 `03839a5` 之后，现行值是 **`30 passed`**、`TC-PY-* = 407`、合计 **788**。
  读者若在本仓复跑，应看到 **30 passed**（TASK-149 复跑：`30 passed in 1.97s`）。
* **依据（可复算，一手）**：`python -m pytest tools\tests -q --no-header -p no:cacheprovider`
  → `30 passed`；`python recovery\work\task146\recount.py` → 六族逐族相等、`SELF_CONSISTENT=YES`。
* **结论受影响吗**：**不受影响**，而且**该报告的 `verdict = fail` 正是触发 TASK-146 的原因**——
  它把 `404/785` 与正文 `400/781` 的不一致判成了 blocker，那个判断是对的。

---

## E-11 — TASK-149 任务书 §E.9 点名的 `TASK-147-REPORT.md` 不存在

* **文件**：`recovery/tasks/TASK-149.md` §E.9（点名校对 `recovery/reports/TASK-{143,144,146,147,148}-REPORT.md`）
* **原说法**：把 `TASK-147-REPORT.md` 列进校对范围。
* **更正**：**`recovery/reports/TASK-147-REPORT.md` 不存在**。TASK-147 是**独立验收**任务，
  它的产物按 `recovery/tasks/README.md` 第 4 条是
  `recovery/tasks/TASK-147-ACCEPT.md`（任务书）+ `recovery/reports/ACCEPTANCE-TASK-147.md`（报告），
  没有"实施报告"。已有的同名文件只有这两个。
* **依据（一手）**：`find . -name "*TASK-147*"` → 只有
  `./recovery/reports/ACCEPTANCE-TASK-147.md`、`./recovery/tasks/TASK-147-ACCEPT.md`；
  `ls recovery/reports/` 里没有 `TASK-147-REPORT.md`。
* **结论受影响吗**：**不受影响**——该"报告"的角色由 `ACCEPTANCE-TASK-147.md` 承担，
  后者已被 TASK-149 §A 入库（`70a7aa9`）并在 §E 里逐条校对过。

---

## E-12 — `ACCEPTANCE-TASK-147.md` 自己点名的 Y1/X5/X6 长期未落进规范文件

* **文件**：`recovery/reports/ACCEPTANCE-TASK-147.md` §Y1 / §X5 / §X6
* **原说法（该报告的发现）**：
  * **Y1（major）**：`TEST-CASES.md` §1.2/§9.3 的 `121` 不可复现，实测 `119+21+2`；
  * **X5（minor）**：§0.1 把 `test_playability_model_player.py` 的贡献写成"model_player **272**"，
    容易被读成"该文件的 pytest 行数"，实为 **276 条 TC-PY 行（4 pytest + 272 printed）**；
  * **X6（minor）**：§10.6 E4 的"**25 处**"与修后实际不符（修后含 `30 passed` 的 TC-PY 行是
    **27** 条 + §9.2 一行 + §10.3 一行 = **29**）；且 L7 与 §1.1 注里"**唯一来源**"的表述
    在字面上不严格（§0.1、§9.2 的 F1/F2 行、§10.3 也各出现一次同值同源的 `30 passed`）。
* **更正状态**：
  * **Y1 已由 TASK-149 落实**：`recovery/TEST-CASES.md` §1.2 / §9.3 U2 / §10.6 增补 E5a / §10.7
    全部改成 `119 + 21 + 2`（就地改，并保留原文意图的说明）；见 E-2。
  * **X5 未改**：`model_player 272` 是 §0.1 组成式里的一项（该式写的是
    `jev 33 + playjev 49 + p7 23 + model_player 272 + pytest 30 = 407`，加数都对，
    合计也对），改成 `276` 会让该式与 §1.1 的 407 **不再自洽**（276 含 4 条 pytest 行，
    而那 4 条已被算进最后的 `pytest 30` 里）。**登记为"标签不精确但算式正确"**，
    留给将来统一改写 §0.1 时处理。
  * **X6 未改**：`§10.6 E4` 是 TASK-146 的**变更清单**（叙述它做了什么），TASK-149 的纪律是
    **只改失效引用/数字，不重写他批的变更清单**。该报告已把 X6 记为 minor，读者可以自行对照。
    "唯一来源"一句同样保留（它想表达的是"§8.1 是 `pytest` 数字的权威出处"，
    不是"全文只出现一次"）。
* **依据**：`recovery/reports/ACCEPTANCE-TASK-147.md` §Y1/§X5/§X6 原文；
  `recovery/TEST-CASES.md` §10.7（TASK-149 的落实清单）。
* **结论受影响吗**：**不受影响**——该报告的 `verdict = pass` 建立在 A1/A4/C6/D8 等
  "统计与正文逐位相符、无失效引用、自洽测试真判红"之上，这三条都是 minor/major 级的**记录项**。

---

## 复算脚本清单（TASK-149，全部只读、全部在 `recovery/work/`）

| 脚本 | 复算什么 |
|---|---|
| `task149_ledger.py` | E-1：从 `runs/model-player/_scripts/t136_commands.jsonl` 重算 194 的切法，并读 `t142_redirect_scan.json -> task140_ledger_erratum` |
| `task149_docaudit.py c1` | E-2：从 `probe-live.json` 把 142 条 `-32602` 分成 119/21/2（并逐条打印那 2 条无冒号的） |
| `task149_docaudit.py c2` | §E.10 的失效路径扫描（只对**含目录**的 token 判定，且对多根解析） |
| `task149_docaudit.py c3` | `tools/tests/**` 的文件数与逐文件 `def test_*` 数（30 的唯一来源） |
| `task149_stalepointers.py <报告名>` | E-7/E-8：把某份报告里的 `path:line` 指针在**今天**的位置与附近符号打印出来 |
| `task149_frozenmap.py` | E-7/E-8：重新构造冻结版（4905 行）并打印符号在两个版本里的行号对照 |
| `task149_pointers.py` | 全矩阵 630 个不同的 `path:line` 指针的存在性 + "行号是否超过文件末行" |
| `task149_negclass.py` | E-2 的另一种独立复算（两个探针文件合起来的 `-32602` 分类） |
| `task149_probeshape.py` | `probe-live.json` / `probe-u2.json` 的真实字段形状 |
