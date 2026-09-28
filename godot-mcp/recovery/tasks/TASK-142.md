# TASK-142 — 把"可复现"变成真判据：N≥4 轮分布 + 修脚本策略缺陷 + 报告自洽

> 子代理**只读本文件**执行；报告 `recovery\reports\TASK-142-REPORT.md`，**返回值只给该路径 + 一行状态**。
> **严格单线程**：不得再派子代理。
> **独占**：`tools/playtest_player.py`、`tools/playability_gate.py`、`tools/playability_controls.json`、`tools/tests/**`、
> `tools/playtest_artifact_index.py`、`runs/model-player/**`、`recovery/reports/TASK-140-REPORT.md`（**仅追加勘误小节**）、
> `recovery/tasks/TEMPLATE-logic-feedback.md`、`DECISIONS.md`、`recovery/tasks/TASK-142.md`。
> **禁触**：20 款游戏逻辑（**只测不改**）、`_exercises/neg_*`/`prefix_*`、TASK-137/139/141 报告历史内容、`F:\models\**`、两个 venv、8080/8081、`.gitignore`、`recovery/tasks/README.md`。

---

## 0. 验收方（TASK-141，`verdict=pass`）点名的两条 major（本任务的依据）

1. **`TASK-140-REPORT.md` 数字不自洽**：同一份报告同时写 **194**（§I 顶 / §E.Y10）与 **186**（§I.3 两处、§F 表）；**权威台账重算 = 194**。
2. **报告档位下"两轮一致"不是可复现性保证**：用**逐字相同**的 `pong scripted @w90` 命令跑 **4 轮**，读到 **`INCONCLUSIVE` / `PASS` / `PASS(baseline only)` 三个类别**。
   机制：脚本策略在 `Ball.Velocity` 采样为 0 时**恒选 `pong_serve`**，令"8 步动作 >1 种"的提前停止不成立 ⇒ 注入步 6 < 8。
   ⇒ 报告 §C.2 把 pong 标成"两轮 PASS/STABLE"**只属于那两次抽样**。

**其余 minor（一并修）**：`task140_cases` 分段断言数错（unstable 实为 **16** 非 22）；`refusal_evidence` 实为 **6 款**非 5 款；
§C.7 两处描述与图不符（青蛙 y≈536 实测 **530–538**；"三组管子"实为 **4 列**）；报告正文未给"两窗相等步数与差值分布"聚合
（验收方给出：**1053 步 matched=564/53.6%、max|Δ|=23**）。

---

## 1. 目标

### A. **N≥4 轮分布**取代"单次 verdict"（核心）
1. 在 `tools/playability_controls.json` 声明 **`model_player_window.min_rounds = 4`**（给依据：TASK-141 的四轮三类别实测）。
2. **被判定的 verdict 必须是 N≥4 轮的分布**：逐轮 verdict + 计数 + **一致性**；
   `UNSTABLE` 的新语义 = **N≥4 轮中不全体一致**（列出每轮的类别与分歧步）；**只有全体一致的 PASS 才 `counts_as_pass=true`**。
3. **每处引用必须带「档位 + 轮数 + 分布」**（工具输出、`player.json`、`gate.json`、模板）。
4. **N 不足或未跑满 ⇒ 标 `ROUNDS_INSUFFICIENT`**，不得计入 PASS。

### B. 修脚本策略缺陷（TASK-141 的机制根因）
5. `--player scripted`：`Ball.Velocity` 采样为 0 时**不得恒选 `pong_serve`**（策略必须对"速度读数不可靠"有明确处理，例如按位置差推断或加冷却），
   并**给证据**：修前 6 步/提前停止不成立 → 修后 ≥8 步且动作 >1 种；对同类"读数退化导致恒选同一动作"的款做一次普查（逐款给是否受影响）。

### C. 报告自洽与补全
6. `TASK-140-REPORT.md` 追加**勘误小节（只增不改）**：194 vs 186 的更正与权威口径、断言数、`refusal_evidence` 6 款、§C.7 两处描述（**附可机检锚点**）、
   并把"两窗相等步数与差值分布"聚合（含验收方给的 `1053 / 564 / 53.6% / max|Δ|=23` 的口径与自己的重算）。
7. 本批自己产出的数字**必须自洽**：报告中相同数字**只允许一个来源**（台账/产物路径 + 重算命令）。

### D. 重跑与记录
8. **报告档位（w90）下跑 N=4 轮**：至少 `pong`（脚本 + 模型）、`asteroids`、`tetris`、`breakout`（这 4 款是已知不稳定/敏感款）；
   预算允许则脚本臂全 20 款 ×4 轮、模型臂 jev 全 20 款 ×4 轮；**给逐款分布表**。
9. 产物清单用 `tools/playtest_artifact_index.py` 生成并 **`git add -f` 入库**（逐文件暂存）。
10. **必须 `read_image` 实看关键帧**（含全尺寸 800×600），**每条描述附可机检锚点**。
11. `DECISIONS.md` 追加本批条目；`TEMPLATE-logic-feedback.md` 同步"N≥4 轮分布 / `ROUNDS_INSUFFICIENT` / `UNSTABLE` 新语义 / 脚本策略退化"。

---

## 2. 铁律

1. **禁止一切 shell 重定向**；沿用命令台账 + 扫描器并给本批自查数字。
2. **只测不改** 20 款游戏逻辑；破坏性命令默认拒绝。
3. 命令尽量从 cmd 启动；`429/529` 退避；只用 8080/8081；**串行**；**不同档位/轮次用不同端口**（TASK-139/141 都踩过端口冲突）。
4. **不许放宽判据**：`UNSTABLE`/`ROUNDS_INSUFFICIENT` 只能**拿掉** PASS；任何翻转如实报。
5. 提交前 `git status --short` **逐文件暂存**；别人未跟踪文件不代提交。
6. **事实来源分级**；未达标项如实报。

---

## 3. 验收判据

| 编号 | 判据 |
|---|---|
| Z1 | `min_rounds=4` 已声明；verdict 以 **N≥4 轮分布**给出；只有**全体一致 PASS** 才 `counts_as_pass=true` |
| Z2 | `UNSTABLE` 新语义（N≥4 不全体一致）实现 + 测试；`ROUNDS_INSUFFICIENT` 不进 PASS |
| Z3 | 脚本策略退化已修（pong 给出修前 6 步 → 修后 ≥8 步、动作 >1 种），并给"同类款普查" |
| Z4 | `TASK-140-REPORT.md` 勘误小节（只增不改）逐条给出原文/更正/依据；§C.7 补可机检锚点 |
| Z5 | 两窗相等步数与差值分布聚合已给（口径 + 自己的重算） |
| Z6 | 报告档位 N=4 轮：pong/asteroids/tetris/breakout 至少这 4 款；逐款分布表；覆盖数如实报 |
| Z7 | 读图实看（含全尺寸）+ 每描述附锚点；产物清单已逐文件 `git add -f` |
| Z8 | `DECISIONS.md` + 模板同步；本批重定向自查数字；两仓 git 状态；未达标项如实报 |

---

## 4. 报告落点

* `F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-142-REPORT.md`；**只返回路径 + 一行状态**。