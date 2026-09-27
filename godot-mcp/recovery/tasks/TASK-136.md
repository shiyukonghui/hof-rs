# TASK-136 — 把「V3 + 严格余量」定为准判据，并对 20 款做游戏侧 + 模型侧扫描

> 子代理**只读本文件**执行；报告写到 `recovery\reports\TASK-136-REPORT.md`，**返回值只给该路径 + 一行状态**。
> **严格单线程**：本任务期间**不得**再派子代理。
> **独占文件**：`tools/playtest_player.py`、`tools/playability_gate.py`、`tools/playability_controls.json`、`tools/tests/**`、
> `runs/model-player/**`、`DECISIONS.md`、`recovery/tasks/TASK-136.md`。
> 若脚本臂在 20 款里发现游戏侧阻塞，**允许**修对应游戏的逻辑（**只修发现的那些**），并在报告里逐款点名。
> **禁止触碰**：`projects/_exercises/neg_*` 与 `prefix_*`、`F:\models\**`、`/opt/jev-venv`、`/opt/playjev-venv`、8080/8081 服务、`.gitignore`、`recovery/tasks/README.md`。

---

## 0. 现状（一手）

* **判据**：用户裁定"**Jev 当模拟真人玩家**"——看图出操作 → 游戏接受 → **画面必须动态变化**；子代理须**读图**判断是否符合游戏逻辑；P1–P7 仅作"代码能跑"。
* **TASK-134**：`--player=scripted` 分测臂；**V3 问法**（"现在做哪个动作能推动游戏"+ 候选写成"这个动作会怎样改变画面/状态"）→ `pong×jev`/`tetris×jev` PASS；PlayJev 无变体救活；`MODEL_NO_PROGRESS`/`MODEL_FIXED_POINT` 与 FAIL 分离（不进判决）。
* **TASK-135**（提交 `6999626`）：修好三个游戏侧硬阻塞——snake `StepSeconds=0.25` + 时间基准归玩家（脚本臂 **1/20 → 8/8**）、puzzlebobble `AutoClock=20`（连发 4 发 + 结算）、game2048 `AutoSpawn=true`（盘面真长大）；3×`dotnet build` 0 错 0 警；P1–P7 三款全绿；
  **V3 两把尺子**：`baseline`（裸 `>`，默认）与 `strict`（观测量 ≥2× 对照窗 + 下限 1.0），每步两读落盘、边缘步点名；
  **`pong×jev×V3`：baseline PASS，strict 掉出 PASS**（边缘步 2≈1.09×、7≈1.195×）——如实报告。
* TASK-135 自曝：只读排查中用了若干次 shell 重定向（`2>&1`、`2>/dev/null`），未参与测量与判决；另有两项未做（playjev 修后模型臂、修前 V1 基线）。

---

## 1. 目标

### A. 判据定标准（机制改动）
1. **`strict` 余量升为 PASS 的默认判据**：`baseline` 保留为对照；**只有 strict 通过才算 PASS**，
   仅 baseline 通过者一律标 **`PASS(baseline only)`** 且**不计入通过数**。在报告与 `gate.json` 里都体现。
2. **重定向自查（机械化）**：把本批**实际执行过的命令**（你的控制台/脚本记录）**逐条扫描** `>`、`>>`、`2>&1`、`*> `、`2>/dev/null`、`> nul`、`1>NUL`，
   报告**命中条数与逐条原文**（若某项无法枚举，写明"无法枚举"与原因）。→ 把"无法保证枚举干净"变成**可核数字**。
3. 把"**必须读图**""**strict 默认**""**重定向自查**"写进 `recovery/tasks/TEMPLATE-logic-feedback.md`。

### B. 20 款扫描（本批主体）
* **脚本臂（游戏侧）全覆盖 20 款**：逐款给对局时长 / 存活步数 / 玩法推进步数 / 是否出现动态变化 / 三态；
  **发现游戏侧阻塞就修**（只修发现者），并给修前→修后证据；修完 `dotnet build` 0 失败 + P1–P7 未被弄坏。
* **模型臂（V3 + strict）尽量覆盖**：按预算逐款跑（`jev` 优先；有余力再加 `playjev`），
  逐款给 `steps.jsonl` + `demo.png` + 三态（PASS / `PASS(baseline only)` / FAIL / INCONCLUSIVE / `MODEL_*`）。
  **预算不足就如实报告覆盖到哪一款**，不要声称全跑。
* **必须 `read_image` 实看关键帧**（含**全尺寸 800×600**），写"看到了什么/变了什么/是否符合游戏逻辑"；
  缩略图不得作为"没变化"的依据。

### C. 补 TASK-135 未做项
* `playjev` 的**修后**模型臂重跑（至少 Task-135 修过的 3 款）；
* **修前 V1 基线**（至少 pong / snake / puzzlebobble / game2048 四款，用 `_exercises/prefix_*` 或 git 还原副本，
  **不得改正式工程**）——使"V3 相对 V1 的提升"有前后对照。

### D. 决策与记录
* `DECISIONS.md` 追加本批条目（编号顺延）：**strict 升为默认**的理由与影响、重定向自查机制、20 款扫描结论、任何新发现的游戏侧缺陷。

---

## 2. 硬性约束（铁律）

1. **禁止一切 shell 重定向**（含 `> nul`、`1>NUL`、`2>&1`、`2>/dev/null`）；用 `-o`/`-OutFile`/Python 句柄。
   **本批必须给出 A.2 的自查数字**。
2. **破坏性命令默认拒绝**；不碰 `_exercises/` 既有变体与其余未发现缺陷的工程。
3. 命令尽量**从 cmd 启动**；中文写盘乱码用 cmd/bash 或 Python UTF-8。
4. **禁止任何第三方端点**；只用 8080/8081；**串行**调用；`429/529` 按 `Retry-After` 退避。
5. **不得**杀服务、不得动两个 venv、不得动 `F:\models\**`。
6. 端口：唯一高位端口（避开 9877/9888/9889/8080/8081）。
7. **不许放宽判据**（strict 就是收紧方向）；任何改动走可开关变体 + 逐字证据 + 与基线并列。
8. 改引擎模块才触发两变体重建 + 十道门 + `accept_m1` + push；未改就写明"未触发"及依据。
9. 提交前 `git status --short` 只暂存自己独占清单里的文件；别人的遗留改动不代提交，点名留给决策者。
10. **事实来源分级**（一手实测 vs 文档摘要）；代码与文档冲突以代码为准并显式纠正。

---

## 3. 验收判据

| 编号 | 判据 |
|---|---|
| V1 | `strict` 已是 PASS 默认；`PASS(baseline only)` 单列且不计入通过数（给机制改动与一处实测示范） |
| V2 | 重定向自查：命中条数 + 逐条原文（或写明无法枚举的原因） |
| V3 | 模板已含"必须读图 / strict 默认 / 重定向自查"三项 |
| V4 | **脚本臂覆盖 20/20**，逐款数字与三态齐；发现的游戏侧阻塞已修（给修前→修后证据）或如实登记未修 |
| V5 | 模型臂（V3+strict）覆盖数如实报告；逐款 `steps.jsonl` + `demo.png` + 三态 |
| V6 | 读图：关键帧实看（含全尺寸），逐帧表 + 逻辑符合性推理 |
| V7 | C 段两项（playjev 修后、修前 V1 基线）完成或如实说明 |
| V8 | `DECISIONS.md` 本批条目已加（编号顺延） |
| V9 | 铁律逐条 + 文件所有权自查 + 两仓 `git log --oneline -5` 与 `git status --short` + 关键产物绝对路径 + sha256 |
| V10 | 未达标项如实报告，不得"应该可以" |

---

## 4. 报告落点与返回值

* 报告：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-136-REPORT.md`
* **返回值只给报告路径 + 一行状态**；跑不完如实报告覆盖到哪一款。