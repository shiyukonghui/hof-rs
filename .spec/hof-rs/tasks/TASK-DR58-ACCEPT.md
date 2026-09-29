# TASK-DR58-ACCEPT — DR-58（引擎应答载荷形状修正）独立验收任务书

> 你是**独立验收子代理**。不得继承实现者或调度者的结论。
> 规范：`DESIGN-DETAIL.md` **§15**；任务书：`.spec/hof-rs/tasks/TASK-DR58.md`；
> 实现者报告（**线索，非证据**）：`.spec/hof-rs/tasks/TASK-DR58-REPORT.md`；
> 真机证据（**只读**）：`runs/smoke-t7/**`、`runs/smoke-t7-experiment/**`；
> 决策：`DECISIONS.md` **D240/D241**。**离线批次**。
> 产物：`.spec/hof-rs/tasks/TASK-DR58-ACCEPTANCE.md`。

## 1. 九项核心复核（逐条自己复现，给命令 + 原始输出 + 文件:行）

1. **套件**：自己跑 `cargo test --offline`；应 **exit 0 / 352 passed / 0 failed / 7 ignored**，
   且 **ignored 未增加**；核对 342→352 的 **+10** 与新增测试条数自洽（`dr58_payload_shapes.rs` 5 + 电池 5）。
   另注意实现者报告了一次**未定性 flake**（首跑 exit 1、日志截断、重跑正常）——**请多跑几次**并如实报告是否复现。
2. **头号反例目标：`scene_path` 的"省略"结论是否被证据唯一确定？**
   自己去读 `runs/smoke-t7/**`（含 `raw/input_channel_probe.json`、`runs/smoke-t7-experiment/scenario/**` 的 sc-02/sc-03 与 C1/C4/C5）。
   必须回答：**证据是否排除了其它候选形状**（例如换一个**参数名**、传**空串**、传**合法 `res://` 路径**、
   或该成员**必填但我们缺其它必填项**）？**失败是否真的由 `scene_path` 引起**（错误正文是否点名它）？
   **若证据其实不足以唯一确定"省略"，则那一步是猜测 ⇒ 判 fail 或退回补捕获**（不要再猜第二次）。
3. **可见告性判据非空洞**：`node_properties_read()` 要求在**非空 `node_path`** 且**非空 `properties` 对象**。
   请**自设植入**（把判据改成恒真）证明它**会红**；并确认**畸形/缺失载荷仍判假**
   （实现者称 11 个畸形载荷全假——请自造 ≥4 个**不同**畸形，含 `properties` 为**空对象**、
   `node_path` 为**空串**、`properties` 是**数组**、顶层键**大小写变形**）。
4. **G20 那处**：确认 `godot.rs` 现在对 Player/Goal/HUD 的**真实成功载荷**不再判 "missing"，
   且该修正**不依赖**测试里的伪造数据（用 `runs/smoke-t7` 的真实字节复核）。
5. **夹具可信度**：`tests/fixtures/dr58/**` 的 7 个文件是否与 `runs/smoke-t7/**` 中**对应来源逐字节相同**
   （自己按 `MANIFEST.json` 的来源路径比 sha256）；确认 `runs/**` **未被修改**（两轮基线文件数与最新 mtime 不变）。
6. **无既有断言被放宽**：`git diff 3c10663..HEAD --stat/-numstat`；测试文件的删除行逐条判语义等价；
   确认**替身变严而没变松**。
7. **"停下不猜"的判定是否站得住**：`build_check`（`:3408`）给 `editor_play_scene` 发 `scene_path` 未修。
   请核实：①该工具**真实 schema** 是否确无 `scene_path`（从契约/夹具或真机捕获取证）；
   ②是否**确实没有**捕获能证明它被拒；③它是否**确实不在**电池路径上。⇒ 判定"未修"是**正确克制**还是**遗漏**。
8. **守卫优先级**：实现者因 DR-45 词汇守卫而**丢弃了一个未使用的捕获**（而非豁免该文件）。
   请核实守卫**未被削弱**（`tool_vocabulary` 相关测试仍在且非空洞），并判定其处置是否正确。
9. **禁区与陷阱自查**：`godot-mcp/**` 零 diff（**先证明 pathspec 命中**）；`PRD-mario.md` sha256 仍
   `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`；`Cargo.toml`/`lock` 零 diff；
   **未 push**（`origin/master` 应仍为 `3c10663`）；未 stage；`runs/**` 只读。
   两个假绿陷阱（`git diff` 对不存在 pathspec 不报错；`cmd` 里 `^` 是转义符）各实测一次。

## 2. 纪律

只读为主；**唯一**允许的改动是 §1.3 的受控植入（逐字节恢复 + `git status`/`diff --stat` 双空 +
`git hash-object` == HEAD blob 三法证明；仓库 CRLF 敏感）。
**不启动 Godot、不碰任何端口、不联网、不调模型端点。**
不改 `godot-mcp/**`、不改 `PRD-mario.md`、**不写 `runs/**`**。**不 push、不 stage、不改写历史。**
不删/不放宽既有测试换绿。**不要修任何你发现的问题。**

## 3. 结构化结论（写进报告 §1）

```json
{ "verdict": "pass" | "fail",
  "criteria": [ { "id": "SUITE|SCENE_PATH_PROVEN|PREDICATE_NON_VACUOUS|G20|FIXTURES|NO_WEAKENING|STOP_NOT_GUESS|GUARD_PRIORITY|GUARDS",
                  "pass": true, "evidence": "命令 + 真实输出 + 文件:行" } ],
  "defects": [ { "id": "DEF-x", "severity": "blocker|major|minor|info", "what": "...", "reproduction": "..." } ],
  "risks": [ "..." ], "unverified": [ "..." ] }
```

`verdict=fail` 门槛：套件不绿或 ignored 增加、**`scene_path` 的结论未被证据唯一确定**、
判据可被恒真化而不变红、夹具与真机字节不一致、既有断言被放宽、`runs/**` 被动过、
或"停下不猜"其实是**遗漏**（应修而未修且证据充分）。

## 4. 报告必含小节

1. 结构化结论 + 真实命令与退出码；2. 逐项核对表；3. **反例清单**（你自己的植入 + 观测 + 是否推翻）；
4. 对 **`scene_path` 真形状**的独立判定；5. 对 `build_check`"未修"的独立判定；
6. 未验证项与理由（含 flake 复现结论）；7. 你没有独立复核的部分；8. 给下一批的建议（**不要**自己改代码）。

**回报给父代理只有一行：报告文件路径。**