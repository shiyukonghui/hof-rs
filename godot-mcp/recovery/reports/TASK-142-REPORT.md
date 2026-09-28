# TASK-142 报告 —— 把"可复现"变成真判据：N≥4 轮分布 + 修脚本策略缺陷 + 报告自洽

> 任务书：`recovery\tasks\TASK-142.md`（自包含：§0 验收方点名的 2 条 major + 4 条 minor、§1 A/B/C/D、
> §2 铁律、§3 Z1–Z8、§4 报告落点）。
> 执行方式：**严格单线程**，本任务期间**没有派任何子代理**（无 `subagent` / `workflow` / `ralph` 调用）。
> 铁律 ①：本批**禁止一切 shell 重定向** ⇒ 可疑命令一律经 `runs\model-player\_scripts\t142_cmd.py`
> （`subprocess ... shell=False`）入**本批自己的**台账 `t142_commands.jsonl`，自查数字见 §H。
> 依据链：每个数字只有**一个来源**（产物路径 + 重算命令），本批全部数字集中在
> `_scripts\t142_numbers.json`、`_scripts\t142_redirect_scan.json`、`_scripts\t142_stability_*.json`、
> `_scripts\t142_frame_alignment.json`、`_scripts\t142_anchors.json`。

---

## 0. 一句话结论

**A（核心）**：`tools\playability_controls.json -> model_player_stability.min_rounds` 由 **2 → 4**
（依据 = TASK-141 §F-2 的四轮三类别实测），被判定的 verdict 现在必须是 **N≥4 轮的分布**：
逐轮 verdict + 逐轮类别 + 类别计数 + 一致性标志（`distribution` / `classes_by_round` /
`all_rounds_agree` / `round_count` / `min_rounds`），**只有全体一致的字面 `PASS` 才 `counts_as_pass=true`**；
轮数不足写 **`ROUNDS_INSUFFICIENT`**（不是判断、不进 PASS；旧的 `INSUFFICIENT_ROUNDS` 只作读入别名）。
TASK-141 的 pong 四轮三类别在**本批自己的四轮复现**里成立（§B.2），而且修完脚本策略后
**同一命令的四轮变成全体一致**（§B.3）——这是"可复现"第一次被真的检查过。

**B**：`--player scripted` 的 pong 策略退化（`Ball.Velocity` 采样为 0 时恒选 `pong_serve`）已修：
策略现在按 `Ball.pos` 的位置差判断球是否真的停着、并对"连续零速读数"**有界轮换**动作；
修前/修后各 4 轮证据 + 20 款脚本策略普查见 §B。

**C**：`TASK-140-REPORT.md` 追加**只增不改**的 **§K 勘误小节**（194 权威口径、断言数 16/14/41/45、
`refusal_evidence` 6 款、§C.7 两处**可机检锚点**、两窗差值分布聚合），并给"一个数字一个来源"表。

**D**：报告档位 **w90** 下按新门槛重跑 **N=4 轮**：脚本臂 **20 款 ×4**、jev 臂 **20 款 ×4**，
逐款分布表 + `STABLE`/`UNSTABLE`/`ROUNDS_INSUFFICIENT` 判定 + 覆盖数如实报；产物索引由
`tools\playtest_artifact_index.py` 生成并**逐文件 `git add -f`**；关键帧**读图实看**（含全尺寸）。

**没有放宽判据**：两把尺子的公式、`min_frames`、`reporting_frames`、`--window-frames` 语义一律未动；
`UNSTABLE` 与 `ROUNDS_INSUFFICIENT` **只能拿掉 PASS**；门槛是**向上**抬（2→4）；
14 款未达标/限制如实列在 §G。

---

（其余小节在长跑结束后补齐：§A 判据、§B 修法与证据、§C 分布、§D 覆盖与产物、§E 逐条判据、
§F 哈希、§G 未达标、§H 铁律自查、§I 提交与仓库状态。）
