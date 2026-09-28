# TASK-141-ACCEPT — 终局独立验收：游戏逻辑反馈机制（判据 / 工具 / 模板 / 20 款结论）

> **你是独立验收方**，不是实施者。**不得继承**实施者或决策者的结论；只看 §0 的判据、**代码**、**可复现证据**。
> **必须自己跑**、**必须自己 `read_image` 读图**。任务书里出现的任何数字都**只是待核对转述**，一律以你自己的重算为准，不符就点名。
> 报告写到 `recovery\reports\ACCEPTANCE-TASK-141.md`，**返回值只给该路径 + 一行 verdict**。
> **只读验收**：不得改游戏代码/工具/既有证据（可写 `runs/accept-141/**` 与报告）。**严格单线程**：不得再派子代理。

---

## 0. 判据（用户口径，验收基准）

1. **Jev 当模拟真人玩家**：模型**看图**出操作 → 注入 → 记录画面变化；
   **FAIL** = 模型出了操作 ∧ 游戏**确实接受**该输入 ∧ **画面没有动态变化**。
2. **PASS** = 连续 ≥8 步里"接受 ∧ 变化"比例 ≥75%，**且**子代理**读前后图**判定变化**符合游戏逻辑**。
3. **`strict` 余量**为 PASS 默认；仅 baseline 通过者 `PASS(baseline only)` 且 **`counts_as_pass=false`**。
4. **`reporting_frames=90`**（TASK-140 声明）：**低于该档的 verdict 一律不得计入 PASS**。
5. **`UNSTABLE`**：同款同档 ≥2 轮 verdict 不一致 ⇒ 标 `UNSTABLE`、**不计入 PASS**、须列分歧点。
6. `MODEL_FIXED_POINT` / `MODEL_NO_PROGRESS` / `WINDOW_TOO_SHORT` 是**测量侧**结论，**与 FAIL 分开**、**不得**用于判游戏 PASS。
7. **合法拒绝**（`refusal_evidence`）可让该步不算 FAIL，但**全拒绝零推进必不得 PASS**（门槛 `min_real_progress_steps=4`）。
8. **子代理必须读图**：每条逐帧描述**必须带可机检锚点**；缩略图不得作为"没变化"的依据。
9. **P1–P7 只用于"代码能跑"**。

---

## 1. 你要独立核验的事项

### A. 判据机制（读代码 + 构造反例）
1. `reporting_frames`、`counts_as_pass`、`UNSTABLE` 是否**真的**在代码里生效（逐处文件:行）；**低于 90 档能否拿到 PASS**（自己试）。
2. `UNSTABLE` 的三条真实触发（模型 `asteroids` PASS↔baseline-only、脚本 `breakout` 第三次读数不一致）能否**从产物复算**？
   分歧点是否真是"step 6 的 `changed_strict` 差 3 像素"与"ack 丢失"？
3. `refusal_evidence` 的 5 款声明是否来自**游戏自己的状态导出**（不是模型自述）；**"全拒绝零推进"是否真的被判非 PASS**（自己构造/复算）。
4. `ack` 缺失是否**真的**判 `INCONCLUSIVE_ack_missing`、**不回退** `pre_ack`（读代码 + 测试）。

### B. 结论可复现（自己跑）
5. 任选 **≥3 款**（建议 `pong`、`snake`、`tetris`），在**报告档位**下**自己跑**脚本臂与模型臂（V3+strict），
   与 TASK-140 报告数字**逐项对照**；**两轮**至少对 1 款做一次（看是否 `UNSTABLE`）。
6. **自己重算** TASK-140 的两条分布：脚本臂 20×2（报告称 `17/1/0/2` 两轮一致）、jev 20×2、playjev 10×2（`4/0/1/5`）。
7. **4 款修复**（asteroids/frogger/bomberman/flappy）：**自己复现**至少 2 款的"修前缺陷 → 修后消失"
   （asteroids 撞击后重生、frogger 单次注入不连丢多命）；`dotnet build` 与 P1–P7 自己抽 1 款复核。

### C. 读图与诚实性
8. 抽 **≥4 张全尺寸 800×600** 自己 `read_image`，与报告逐帧描述+锚点对照。
9. 核对**报告声明的 9 条未达标项**（§G）是否**真的**未被掩盖（例如 flappy 仍是 `PASS(baseline only)`）。
10. 重定向自查：对台账 `t136_commands.jsonl`/本批台账**自己重扫**，核对"194 条 / 0 命中"与"2 处台账外命令"。

### D. 对抗性
11. 找可能让结论虚高之处：对照窗与动作窗是否**同帧数**？`wait`/合法拒绝是否被当有效动作？`ack` 是否可能被先前按键污染？
    两轮一致是否掩盖**窗口长度敏感**（`SENSITIVE`）？——有则点名，无则说明查过。

---

## 2. 硬性约束

1. **禁止一切 shell 重定向**；用 `-o`/`-OutFile`/Python 句柄。
2. **只读验收**；破坏性命令默认拒绝；**不得**改 20 款游戏逻辑。
3. **禁止第三方端点**；只用 8080/8081；**串行**；唯一高位端口（探针**不同档位必须不同端口**）。
4. **不得**动两个 venv、`F:\models\**`、`_exercises/neg_*` 与 `prefix_*`。
5. **区分"证据支持"与"推断"**；不成立的结论**明说**。

---

## 3. 结构化输出（报告末尾必须有）

```json
{ "verdict": "pass | fail",
  "criteria": [{"id":"A1","pass":true,"evidence":"文件:行 / runs/... / 我跑出的数字"}],
  "defects": [{"what":"...","severity":"blocker|major|minor","evidence":"..."}],
  "risks": ["..."], "unverifiable": ["..."] }
```

任一 `blocker`（判据被偷换、结论无法复现、读图造假、数字不可核）⇒ **`verdict: "fail"`**。

---

## 4. 报告落点与返回值

* 报告：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\ACCEPTANCE-TASK-141.md`
* **返回值只给报告路径 + 一行 `verdict`**。