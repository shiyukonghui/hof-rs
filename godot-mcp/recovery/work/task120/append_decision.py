#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-120: append the D164 decision record to the repository DECISIONS.md.

Idempotent: appends only when the D164 heading is not already present.
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
PATH = os.path.join(ROOT, "DECISIONS.md")

ENTRY = """
## D164 — TASK-120：见证规则收紧（读动词 / 时序 / `expect` 带值 / 禁止裸 `expect_absent`）；通道↔verb 交叉校验；17 条补边界；四处标签修正

* 触发问题：TASK-119 独立验收判 **fail**，两条 HIGH：
  ① `running_game_create_input_recording` 的 `editor_state` 见证用的是 `running_game_stop_input_recording`
  （**写**工具）自己的回包；
  ② `verify_readback()` **不检查见证时序** —— `running_game_stop_input_recording` /
  `running_game_play_input_recording` 被接受的见证调用在写**之前**、值就是起始值 `100.0`，而
  `expect: ["\\"position\\""]` 只是裸键名 → 证据机制退化为「那个 run 里这次读调用发生过」。
  MEDIUM：`os_deploy_to_android_device`（动作动词 `deploy`）声明成 `payload`，`read_payload` 只对读类
  动词累加，**证据门结构性恒为 0**；「17 条有通道证据但没有边界调用」的边界**可构造**（不是不可达）；
  LOW：171/172、`needs_an_external_device` 混栏、`editor_set_auto_dismiss_dialogs` 标签、`basis` 模板。
* 考虑的选项（含被否决者及理由）：
  1. **只把 7 条不合规声明降级，规则不动** —— 否决：规则本身弱，降级只掩盖「写在写之前的读也能签」这个
     结构性口子（M3 反例证明旧的键名级 `expect` 对「把写后的读强改回起始值」完全无感）。
  2. **收紧到「见证必须晚于**同一次**写、且值必须等于该次写写入的值」** —— 否决：manifest 表达不了
     「哪一次写」，同一 run 里多次同形写会让规则不可满足；本轮采用「见证必须晚于被见证工具的**至少一次**
     调用」这一条可判、可复核的时序规则，并配「值级 `expect`」。
  3. **要求每条 `expect` 都是「键:值」对** —— 否决：`T:res://themes/c4b.tres`、`C:Camera3D`、
     `L:DirectionalLight3D` 这类 `editor_execute_gdscript` 的结果**本身就是值**，强制键值对会把已经很强的
     声明判死。最终只拒「裸 JSON 键名 / 裸名字」（`^"[A-Za-z_][A-Za-z0-9_]*"$`），并把这个边界写进台账。
  4. **给 17 条补边界时降低门槛（有通道证据即达标）** —— 否决：门槛是测量事实，降门槛等于把「没测失败面」
     谎报成「测过了」。改为**真跑**一次引擎会话，注入同形状的被拒调用。
  5. **不注入边界，只在文档里论证「可构造」** —— 否决：论证不是证据；M4 已证明补一次即可达标。
  6. **通道↔verb 校验只报警不失败** —— 否决：动作动词声明 `payload` 会让证据门**结构性**永不成立，
     报警会被忽略；改为加载期硬失败。
* 最终选择：
  * `verify_readback()` 四条硬规则：**A1** 见证工具必须是读类动词（且不能是被见证工具自己）；
    **A2** 被采用的见证调用必须**晚于**被见证工具的至少一次调用（同 run、`seq` 更大）；
    **A3** `expect` 至少要有一条**带值**的字面量（拒裸键名）；**A4** 不得**只**声明 `expect_absent`。
    违背即**拒签**、记入 rejected 并写明理由。
  * `load_channels()` 新增「通道 ↔ verb」一致性校验，违规**拒绝运行**；`os_deploy_to_android_device`
    由 `payload` 改为 `file_effect`，`editor_capture_screenshot` 由 `file_effect` 改为 `payload`
    （`capture` ∈ READ_VERBS，契约允许内联 base64 或落盘）。
  * 按新规则**重判 51 条声明**：14 条不合格，逐条用**见证回包里真实存在的值**补强 `expect`
    （含 3 条 input recording 改用真读调用 + 写后值），**0 条降级**；37 条原样通过。
  * 新批次 `c8-task120`（`_exercises/ex_grid`，端口 9905/9906）：给 17 条各注入一次
    `-32602 Unknown parameter 'undeclared_probe'`（注册器未声明参数门 `tool_registry.cpp:812-855`，
    先于 handler 执行），**不改任何门槛**。
  * 标签修正：台账表头显式打印 `出现过的工具名（distinct）= 172`（此前一处口述称 171）；
    `needs_an_external_device` **逐条**给当前状态；新增 `engine_not_implemented` 类
    （`editor_set_auto_dismiss_dialogs`：5 次合法输入全部 `-32000 Not implemented`）；
    `tool_channels.json` 顶层写明 `basis` 是**通道级模板**。
* 选择理由：把「证据」从「那次调用发生过」推进到「写进去的值能在写**之后**、从引擎自己的回答里读回来」；
  通道与动词的一致性由读者强制而不是靠人记得；边界用真调用补，而不是论证它可构造。
* 预期影响与回滚点：
  * **口径影响**：达标 **152 → 169**、计数达标缺证据 **20 → 3**、`未达(0)` 5 不变
    （**177 = 169 + 3 + 5**）；档位 pixel 34 / file 24 / readback 111 / count_only 3 / no_calls 5
    **均不变**（档位是另一把尺子）。3 条仍缺证据的是引擎未实现的
    `editor_set_auto_dismiss_dialogs` 与缺设备/预设的两条 Android 工具。
  * **证据影响**：声明 51 条、经 trace 复核 51 条、被拒 0 条；14 条 `expect` 变成带值；
    corpus 112 run / 182 trace / 8729 调用（c8 只加 1 run、2 trace、17 次调用）。
  * **反例自证**：`recovery/work/task120/witness_rules_selftest.py` 20 项全过（A1–A4 + M1/M2/M2b/M3/M4），
    其中 M3 用**同一份被篡改的语料**同时跑旧规则（签）与新规则（拒）；把 c8 run 用
    `--exclude c8-task120` 排除后台账精确退回 152/20。
  * **回滚点**：`git revert` TASK-120 的功能提交即可回到 TASK-118 口径（`tools/tool_coverage.py`、
    `tools/tool_channels.json`、`tools/tool_coverage_unreachable.json`、6 份 manifest、
    `tools/sessions/_exercises/ex_bound/`、台账两件）；新 run
    `runs/_exercises/ex_grid/c8-task120` **不入库**。台账随时可 `python tools/tool_coverage.py` 重算。
  * **引擎未动**：`godot/modules/mcp_server/` 一个字节未改，按铁律 7 **未触发**两变体重建、
    未跑十道门、未跑 accept_m1、未 push 引擎仓。
"""


def main():
    text = io.open(PATH, encoding="utf-8").read()
    if "## D164 —" in text:
        print("D164 already present; unchanged")
        return
    if not text.endswith("\n"):
        text += "\n"
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text + ENTRY)
    print("appended D164 (%d chars)" % len(ENTRY))


if __name__ == "__main__":
    main()
