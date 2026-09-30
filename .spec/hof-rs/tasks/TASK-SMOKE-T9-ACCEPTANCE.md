# TASK-SMOKE-T9-ACCEPTANCE — 真机 T=1 整轮（`runs/smoke-t9`）的独立验收

- 判据来源：`.spec/hof-rs/tasks/TASK-SMOKE-T8.md`（**本轮沿用**的唯一任务书：E1..E6 判据、两条风险旗、三个假绿陷阱、取证要求）
  + 调度者本轮追加的五条（其内容只出现在被验收报告的 §0 表中，我按任务书正文与 `REQUIREMENTS.md` 的 E1..E6 口径验收）。
- 被验收对象：`.spec/hof-rs/tasks/TASK-SMOKE-T9-REPORT.md` + `runs/smoke-t9/**`（冻结的轮内证据）
  + `.spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/**`（受控证据目录，已被调度者 `dc9d350` 入库）。
- 性质：**独立验收、离线、只读为主**。我无上游对话上下文；报告与上轮台账只当**线索**，下列每条结论都是我自己从原始工件重算/重读得到的。
- **硬约束遵守**：未启动 Godot；未碰任何端口（只做 `netstat`/进程表/`Get-NetTCPConnection` **读取**）；未联网；未调任何模型端点；未跑真机轮；
  未修改 `runs/**`（**连一个临时文件都没有写入、更没有写过再删**）；未修改 `.workspace/mario/**`、`.spec/hof-rs/PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`；未 push；未 stage。
  仓外临时物：`C:\Users\wyl\AppData\Local\Temp\t9acc\`（`digest.ps1`、`digest_repo.ps1`、`digest_cmp.ps1`、`hashtree.py`、`peek.py`、`cmds.py`、`devscan.py`、`dev2.py`、`dev3.py`、`dev4.py`、`dev5.py`、`pl.py`、`promptdiff.py`、`keycheck.py`、`rd.py`、`mkl.py`、`mkchk.py`、`traps.sh`、`traps.bat`、`mkdirtest.bat`、`mkdirtest2.bat`、`dev1_commands_mine.txt`）。
  我**没有**创建任何 `runs/smoke-t9-experiment` 之类的目录（与 t8 不同，本轮的实验落点在仓外）。
- **仓库状态与我开工时不同（并发活动，非被验收对象所为）**：我开工时 HEAD `a9e050c`；我验收期间**调度者**依次落了 `78bd4cb`（D269）、`dc9d350`（把 T9 报告 + 证据目录入库）、`5f3fea4`（D270 + `TASK-DR69.md`）。
  `origin/master` 全程 `fe129a163d6ca22e5e4b48b81e7229c4260b1291`（**未 push**，ahead 5）。这些提交改变了 `DECISIONS.md`，但**不是被验收对象所为**。
- 摘要口径：**PowerShell 5.1（culture zh-CN）`Get-ChildItem -Recurse -Force -File`；每文件取 `F:\moonbit-hof-rs` 仓根相对 POSIX **小写**路径 + 字节长度 + 小写 SHA256；三列 `\t` 连接、`\n` 分行、无尾随换行；行序 `Sort-Object`（文化排序）；整体 UTF-8 取 SHA256**。
  **自证**：`runs/smoke-t6` = `c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03`（135 文件，最新 mtime `2026-09-29 02:32:01`）✓ —— 命中任务书 §4 点名要求的自证值。
  **文化排序是口径的一部分，我实测**：把 `Sort-Object` 换成 `StringComparer::Ordinal`，`runs/smoke-t8` 变为 `c347bd637ab481b1ec357cbb534c1330bad18cfab85c113038fa0878e6b3d3f5`（与 T8 验收记录逐字相同）；
  而 `runs/smoke-t6`/`smoke-t7` 两种排序**同值** ⇒ 「序数排序会同数不同摘要」**只在含 `_` 分歧路径的树上成立**（与 T8 验收 §2.3 的诚实补充一致）。
  另据实：**我用「仓根相对」得到 `c144ef32…`；用「子树相对」得到 `ec4d3829…`** ⇒ 口径里「仓根相对」这四个字是结果的一部分，不能省。

---

## 0. 结构化结论

```json
{
  "verdict": "pass",
  "verdict_scope": "pass 只针对**本轮的产品级判定（E1 及 E2..E6 的不可判定）与两个 major 根因（F-T9-1 角色 CLI 到不了游戏端点、F-T9-2 Developer 零工程增量）**：我逐条独立复算/重读，全部成立。闸门首次真机点火**确实因正确的原因**（工程树逐字节未变，非 mtime 推断）；四条不可判定**确有『证据不存在』的硬事实**支撑，不是回避；E3 的拒判（有观测但形态不达标且非轮内）**符合 REQUIREMENTS 的证据形式要求**；三条只读基线与全部禁区自证成立；三个假绿陷阱我全部亲手复现。**判 pass 不等于报告无瑕**：我独立发现 3 条 minor 事实性不准（第四、五、六条）与 5 条 info，**没有任何一条动摇报告的头号结论**，故不构成 fail。",
  "criteria": [
    {"id": "E1", "pass": false, "evidence": "产品级 **not_met**，与报告一致。我自己用 Python 重实现运行时 `hash_tree`（排除集 {.hoh,.git,.godot,.import}；`rel\\n{len}\\n{bytes}\\n` 流；Path 序数序）：`runs/smoke-t9/versions/1f3d20ed…`（A_0，iteration=0/role=init）、`iter-1/planner-view`、活体 `.workspace/mario` **三棵树同为 `1f3d20ed50b472e422832c4fa2c8d7b72ae04ee11fa4c5ace65fb20a43997fd8`**（各 17 文件 / 18397 B）。工程文件 mtime 最晚是 `scripts/player.gd 2026-09-30 07:19:25`（t8 遗留），**本窗口（>11:08 或 >10:49）工程文件写入数 = 0**。⇒ Developer 阶段前后哈希相等是**真实的**，`warnings.log` 的 `no_progress` + `contract violation no_engineering_write`（原文逐字见 §2.2）、`result.json` 的 `ok=false/failed_role=\"developer\"/reason=\"contract_violation\"`、`versions/index.json` **只有 A0**、`iter-1/traj/` **无 tester.*** 全部为真。⇒ **E1 = not_met 且『零工程增量』为真**。"},
    {"id": "E2", "pass": null, "evidence": "**本轮不可判定**，与报告一致，且我确认『证据不存在』：`runs/smoke-t9` 下 `candidate` 目录 **0 个**；`deterministic`/`battery.json`/`input_replay`/`input_channel_probe`/`play_scene_ready` 相关文件 **0 个**。失败点结构上在冻结之前：`src/runtime/run_loop.rs:938-987`（哈希相等 → finalize_failure → `return Err`）位于 `:989 // Deterministic evidence battery` **之前**。⇒ 不判 met 也不判 not_met 是本轮唯一诚实的读法。"},
    {"id": "E3", "pass": null, "evidence": "**本轮不可判定（无轮内证据）**，且我确认：轮内**没有** `input_replay.json`/`input_channel_probe.json`（电池未跑）。报告的独立实验数字我亲自从原始回包抽出并验算（§3）：右移 `+216.333290`（59 个区间 ⇒ 恒 `3.66666 px/帧`，×60 = `220.0 px/s` = `player.gd:3 speed=220.0`）、左移 `−216.333397`（恒 `−3.66666`）、跳跃 `221.091949 → 214.258911@f6 → 283.979340`（自地面 `283.998993` 起升 **69.74 px**；按 `jump_velocity=-430`/`gravity=1400` 的**半隐式欧拉**预测 `430²/2800 + 430/120 = 69.62 px`，差 0.12 px）、金币 `coins 0→1` 且 `Coin1` 离开场景树、`Goal` 后 `Main.state=\"won\"`；来源确为**游戏端点**（`play_scene.json` 的 `mcp_port=61183` 回包 → 脚本直连 `127.0.0.1:61183/mcp` 只调 `running_game_*`）。**但不判 met**：任务书 §5 末句只给出**必要**条件，`REQUIREMENTS.md:114` 的 E3 证据形式含**前后截图**与 `assert_node_state`——我实测实验脚本用的是 `running_game_play_input_recording`/`get_node_property_samples`/`set_node_property`/`get_scene_tree`/`get_node_properties`/`run_test_scenario`，**0 次 `capture_screenshot`、0 个 .png、0 次 `assert_node_state`**；且它不是轮内证据。⇒ 拒判正确。"},
    {"id": "E4", "pass": null, "evidence": "**本轮不可判定（前提缺失）**，与报告一致。轮内 **无** `iter-1/evidence.json`、**无** `tester.*` 轨迹、**无** `qa_report.md`；唯一的 `evidence.json` 是 `iter-1/planner-view/.hoh/evidence.json`，内容 `{\"iteration\":0,\"qa_status\":\"partial\",\"verified_records\":[],\"gap_records\":[],planner_handoff 三数组皆空}` ⇒ 是 **E_0 输入副本**，报告对它的定性正确、未混用。"},
    {"id": "E5", "pass": null, "evidence": "**本轮不可判定（无快照可对）**，与报告一致。`versions/index.json` 恰一条 `iteration:0 / role:\"init\" / note:\"A0 initial artifact\"`（`created_at 1790737726`），**无 A_1**。报告同时给出比 E5 更强的静态事实（运行期工程树零写入），我已独立确认为真（见 E1）。"},
    {"id": "E6", "pass": null, "evidence": "**本轮不可判定（无工件）**，与报告一致：没有 QA 工件，无内容层对象可核。报告未作任何『诚实/不诚实』判定，正确。"},
    {"id": "C1-gate", "pass": true, "evidence": "**闸门首次真机点火，因正确的原因，且三方一致。** (a) 零工程写入：我自算三树同为 `1f3d20ed…` + 工程文件 mtime 普查（>11:08 计数 0；>10:49 计数 0）+ 目录 mtime（`scenes 07:17:58`、`scripts 07:18:18` 未动，根目录仅 `-p` 的 10:51:57 早于本轮正式轮）⇒ **不是靠运行时自报**。(b) 三方：`runs/smoke-t9/exit_code` = 字节 `32 0A`（`\"2\\n\"`）、`meta.json.exit_code = 2`、控制台 `ROUND_EXIT=2`；`result.json.ok=false`、`failed_role=\"developer\"`、`reason=\"contract_violation\"`。(c) 代码链：`run_loop.rs:938-987`（哈希相等即 violation）→ `errors.rs:86-95`（`HofError::Contract ⇒ 2`）→ `cli.rs:189-198`（错误路径 `exit_code_of`）→ `cli_impl.rs:701-715`（`run_exit_code_for` 优先 `failure_exit_code`）。**信任边界**：进程退出码本身我只能由代码链 + 实现者控制台捕获背书，离线不可复现（见 §5 unverified U3）。"},
    {"id": "C2-unjudgeable", "pass": true, "evidence": "四条不可判定**正确、非过度保守、亦非回避**：E2/E4/E5/E6 的工件**确实不存在**（`candidate` 0 个、`deterministic` 0 个、`tester.*` 0 个、`A_1` 0 个），而且报告**明确拒绝**用 t8 的 raw 或自己的实验顶替（§4.1-§4.4）。E2 尤其容易误判成 met（活体工程与 t8 的 11/11 电池同体），报告没有借证据，是对的。"},
    {"id": "C3-budget", "pass": true, "evidence": "**浪费预算为真，且主因不是提示词变更。** Developer 两次 attempt 合计 175 次 LLM 调用 / 216 次 bash 调用，工程写入 **0**。attempt1（150 调用 / 184 条命令）：`.hoh/scratch` 命中 139 条、`%HOH_` 出现 **175** 次、`bash -c` **0** 次、提及工程源文件的 **5 条全部是读**（`dir /s /b`、`type`）；它自造 `call.py`/`mcp.py`/`post.ps1`/`drv.py` 并用**裸 HTTP**打 4 个游戏端口（57529/65009/55087/61245），确实成功读到了游戏进程状态（call#84/#93/#94）。attempt2（25 调用 / 32 条命令，wrap-up）：**仍零写入**，且其 prompt 明写『STEP BUDGET EXHAUSTED … write the required artifact NOW』——它却把 25 步几乎全花在**重复读** `.hoh/TASK.md`/`plan.md`/`TOOLS.md` 与反复试 `editor_get_errors`（cmd/bash 语法来回切换）。**提示词变更的判定见 §4.3**。"},
    {"id": "C4-E3exp", "pass": true, "evidence": "见 §3：逐帧数字我自行抽取并**独立验算**，与游戏自身常量（`speed 220` / `jump_velocity -430` / `gravity 1400`）自洽到 <1 px；来源经脚本与 `play_scene.json` 证实为**游戏进程端点上的 `running_game_*` 语义工具**（不是探针、不是编辑器侧注入、不是拼装 GDScript）。**拒判 met 的三条理由全部成立**：缺截图/`assert_node_state`（真实要求）、非轮内、以及一个我额外发现且报告未提的系统偏差（§3.3 采样滞后 ~14 帧）。"},
    {"id": "C5-newfindings", "pass": true, "evidence": "F-T9-1/F-T9-2 我逐条复核为真（§5、代码行与原始回包见 §2.4）。F-T9-3（planner `RepeatedFormatError`）我独立确认：轨迹内 `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` 原串 **7 次**，最后 2 个 assistant 回合**无工具调用**，harness 连发 3 条 `No tool calls found…` 后 `exit RepeatedFormatError`。F-T9-6（`input_axis` 恒 null）我读原始回包确认。F-T9-4（15,570,803 B 工具输出）**只有实现者的机器摘要**（见 unverified U4）。**污染检查：报告的独立实验没有污染本轮**——`runs/smoke-t9` 摘要 `541e2d81…36ca9d` 与最新 mtime `11:27:29` 均在轮内，实验（11:30 之后）若写入该目录必然抬高新 mtime；实验也未写入工程树（工程树 = A_0 字节同一）。"},
    {"id": "C6-guards", "pass": true, "evidence": "见 §6：`runs/smoke-t6|t7|t8` 三条摘要与记录**逐字相同**，且 10:49 之后**无任何**文件/目录 mtime 变动（写-删检查）；`PRD-mario.md` sha256 `4c81c3a9…5c3a` 未变；`DECISIONS.md` 我核出开工值即 `01b9f157…a18d`（报告所记一致），其后续变化全部来自**调度者**提交 `a9e050c`/`78bd4cb`/`5f3fea4`；`godot-mcp/**` 嵌套仓 `fc63af77…`、`status` 0 行、今日 0 文件；引擎身份 `4.8.dev.mono.custom_build.035edfce7`（sha256 仅记录）；`origin/master` 全程 `fe129a1`（未 push）；三个假绿陷阱我**亲手复现**（bash + cmd 双向）。"},
    {"id": "C7-honesty", "pass": true, "evidence": "见 §7：未声称 E1/E3 met（我全文检索核对）；明确区分轮内证据与自造实验；跑了两次且**两次都留档**；删除重建 `runs/smoke-t9` 与 attempt-A 全量轨迹不可复核**如实披露**；孤儿进程已清（我实测现只余编辑器 75204，无游戏监听）；密钥**明文**零泄漏（我用配置文件里的真值在 `.spec`/`runs`/`src`/`tests`/`config` 全树比对，**0 个文件含该 51 字符串**）。**扣分项**：3 条 minor 事实不准（§8 D1/D2/D3）与 5 条 info，均不动摇头号结论。"}
  ],
  "defects": [
    {
      "id": "D1",
      "severity": "minor",
      "what": "报告 §0/§2.2 称『本轮 **cmd 方言错误 0 次**』⇒『t7 的 shell 方言机制不复现』。**前半不成立**：两条 Developer 轨迹里 `was unexpected at this time` 的工具结果共 **3 条**（attempt1 2 条：cmd 下的 heredoc `<< 'EOF'`/`<< 'PYEOF'`；attempt2 1 条），且我另发现同类方言错误——`mkdir -p \"$HOH_SCRATCH_DIR/args\"`（bash 习语在 cmd 下）与 `mkdir -p %HOH_SCRATCH_DIR%/args`（attempt1 call#18/#20）。**后半（`bash -c` 0 次、%HOH_ 175 次）成立**，故 t7 的主机制确实换位；但『0 次方言错误』这一**具体数字是错的**，且它掩掉了 D3 的 `-p` 产物。",
      "reproduction": "python 读 `runs/smoke-t9/iter-1/traj/developer.attempt1.json` / `developer.attempt2.json`，统计 `was unexpected at this time` 的工具消息（我仓外 `dev2.py`/`dev4.py`）；同脚本打印 call#16 `dir /b -p`、call#18 `mkdir -p \"$HOH_SCRATCH_DIR/args\"`、call#20 `mkdir -p %HOH_SCRATCH_DIR%/args`。",
      "impact": "不改变 E1..E6；会误导下一批认为提示词里的 shell 方言问题已经彻底解决。"
    },
    {
      "id": "D2",
      "severity": "minor",
      "what": "报告 §7 F-T9-2 称 Developer『**175 次调用全部**用于 `.hoh/scratch` 自造 MCP 客户端与裸 HTTP 探游戏』。**过度概括**：`%HOH_*` 引用 175 次不假，但 attempt2 的 32 条命令（25 次调用，wrap-up）中 `.hoh/scratch` 命中为 **0**，几乎全是**重复读** `.hoh/TASK.md`/`plan.md`/`TOOLS.md`/工程源文件 + 反复试 `editor_get_errors`。准确的读法是：attempt1（150 步）把预算投进 scratch MCP 客户端；attempt2（25 步）投进重复阅读与工具试错——**两次都零写入**。",
      "reproduction": "python 读两条轨迹，按 `.hoh/scratch` 出现次数分组（我仓外 `dev4.py`）；attempt2 的命令清单见该脚本逐条打印。"
    },
    {
      "id": "D3",
      "severity": "minor",
      "what": "报告 §13.3 称 attempt-A『**所有写入同样落在** `.workspace/mario/.hoh/scratch/**`』；§9.2 又称『45 个写入全部落在 `.hoh/**` 与 `.godot/**`』。**不准确**：工程根出现一个**空目录 `-p`**，mtime `2026-09-30 10:51:57`（attempt-A 窗口内、`.hoh` 创建于 10:51:28 之后），它在 `runs/smoke-t8` 的任何树里**都不存在** ⇒ 是本轮新产生的、**位于工程树内但不属于 `.hoh/.godot`** 的写入；它同时被 A_0 快照与 `planner-view` 复制（各含空 `-p`）。因其为空目录，**文件级摘要/哈希闸门看不见它**（故 E1 判定不受影响）。机制强推断（非实测）：cmd 下 `mkdir -p` 创建字面 `-p` 目录——我在仓外 `cmd` 复现 `mkdir -p \"$HOH_SCRATCH_DIR/args\"` ⇒ 同时生成 `$HOH_SCRATCH_DIR` 与 `-p`（rc=0）；attempt-B 的 call#18 就是这条命令。**attempt-A 的该条命令未留档，故是强推断。**",
      "reproduction": "`Get-ChildItem F:\\moonbit-hof-rs\\.workspace\\mario -Force` 看 `-p`（10:51:57，空）；对照 `runs/smoke-t8` 无 `-p`；`Get-ChildItem runs\\smoke-t9 -Recurse -Directory | ? Name -eq '-p'` 命中 planner-view 与 versions 各一；仓外 `mkdirtest2.bat` 复现 cmd 行为（临时目录，未碰仓库）。",
      "impact": "工程树里多了一个异物目录，会随 A_0 一直传下去；`artifact_hygiene.suspicious_files` 只看文件 ⇒ 看不见。建议下一批顺手清掉并把 hygiene 检查扩到目录。"
    },
    {
      "id": "D4",
      "severity": "info",
      "what": "报告 §9.3 的密钥卫生读数与**它自己的** `postrun_state.txt` 不一致：报告写『console 两份命中 0』，而 `.../experiment/postrun_state.txt` 第 33 行写 `console hits: 1`。我无法复现它的匹配口径（既未留脚本也未留 pattern），因此只能登记矛盾；**我自己的独立口径（用配置里的真值 51 串全树比对）结果是『0 个文件含明文密钥』**，所以**没有 C11 明文泄漏**。",
      "reproduction": "`Get-Content .spec\\hof-rs\\tasks\\TASK-SMOKE-T9-evidence\\experiment\\postrun_state.txt` 尾部 `=== SECRET HYGIENE ===` 段；对照报告 §9.3 该行。"
    },
    {
      "id": "D5",
      "severity": "info",
      "what": "**被入库的证据里含密钥管道信息（非明文）**：Developer 执行了 `set | findstr /i \"HOH\"`（call#16），harness 的环境变量 `DSH_TERM_CMD` 因此被写进轨迹与 `experiment/dev1_commands.txt`（第 15 行），内容为 `cd /f/moonbit-hof-rs; export HOH_MODEL_API_KEY=\"$(cat /c/Users/wyl/AppData/Local/Temp/smoke-t9/keyval.txt)\"; …`。**不含密钥明文**（我逐字节确认 0 命中），但**暴露了密钥文件路径与注入方式**，而这两份文件已被 `dc9d350` **入库**。报告 §9.3 只说了『唯一含明文副本的是仓外 keyval.txt』，未提这一条。",
      "reproduction": "`python` 以 `errors=\"replace\"` 读 `.spec\\hof-rs\\tasks\\TASK-SMOKE-T9-evidence\\experiment\\dev1_commands.txt` 第 15 行（该文件不是合法 UTF-8，直接从 540 字节处起）；同串亦在 `runs/smoke-t9/iter-1/traj/developer.attempt1.json`。"
    },
    {
      "id": "D6",
      "severity": "info",
      "what": "报告 §15.9 写『**我的提交**只含本报告 + 受控证据目录』，暗示实现者自己提交过。实际上这些工件在我开工时仍是 **untracked**，由**调度者**的 `78bd4cb`（报告）与 `dc9d350`（证据目录）入库；实现者自己的 §9.3 也写『未 stage / 未 push』。措辞不一致，无实质危害，但会让人误判『谁写的、谁签的』。",
      "reproduction": "`git log --oneline --stat 78bd4cb dc9d350`；`git show --stat 78bd4cb`（+报告）与 `dc9d350`（+证据目录）。"
    },
    {
      "id": "D7",
      "severity": "info",
      "what": "F-T9-1 的证据指针偏弱：§2.2/§7 指向 `experiment/game_endpoint_probe.txt`，但该文件**只有 1 行**（失败回包），不含配对成功的 `editor_play_scene` 回包（那在 `play_scene.json`/`play_scene2.json`）。结论成立（轮内原始回包 + `play_scene.json` + 代码行共同支撑），但指针应写成一对文件。",
      "reproduction": "`Get-Content .spec\\hof-rs\\tasks\\TASK-SMOKE-T9-evidence\\experiment\\game_endpoint_probe.txt`（1 行）；`play_scene.json`（`mcp_port 61183 / pid 106368 / playing true`）。"
    },
    {
      "id": "D8",
      "severity": "info",
      "what": "§9.2『本轮窗口内有写入的文件共 45 个，全部落在 `.hoh/**` 与 `.godot/**`』——计数本身与我一致（42 个 `.hoh` + 3 个 `.godot`），但其中 3 个 `.godot/editor/*.cfg` 的 mtime 是 **11:36:30**，**晚于轮结束 11:27:29**，是编辑器进程在实现者做实验期间写的（与 T8 验收 R4 同族），不属于『本轮窗口』。措辞应分开。",
      "reproduction": "`Get-ChildItem .workspace\\mario -Recurse -Force -File | ? LastWriteTime -gt '2026-09-30 10:49'`（42 个 `.hoh` + 3 个 `.godot/editor`）。"
    }
  ],
  "risks": [
    "R1（对下一批最重要）**F-T9-1 是结构性的，不是模型问题**：`hoh tools call running_game_*` 每条命令都是新进程（`cli_impl.rs:53` → `bridge.rs:227-234` 新建 `McpChannel::new`），而游戏路由是**进程内**内存（`tools/mod.rs:138`、`register_game_endpoint` 在 `:312`、`client_for` 在 `:186-205` 硬 bail）。我在**只读代码 + 冻结回包**上复核成立；**未**在真机上重跑（离线约束）。⇒ 只要 Developer/Planner 的 plan 还把可观测性钉在 `running_game_*` 上（t9 的 plan.md 第 3/4/5/12 行正是如此），**零增量就可能重演**——调度者已据此开了 `TASK-DR69.md`（`5f3fea4`），方向与我的结论一致。",
    "R2 报告的『提示词无责』结论我支持（system prompt 逐字节相同、任务 prompt 只是把无法解析的 `{HOH_*}` 修成可用的 `%HOH_*%`、工具矩阵未动），**但反过来说明根因在别处**：模型在**同一个结构障碍 + 同一条 plan**下连续两次（attempt-A/B）选择绕道而非写作。⇒ 下一批若只修提示词，很可能再空转；应同时给出『角色是否允许直连游戏端点』的设计裁决。",
    "R3 `-p` 空目录已进入活体 `.workspace/mario` 与 A_0 身份树之外（哈希不可见），会**永久随轮次传播**；`artifact_hygiene` 只看文件 ⇒ 不会报。建议：清掉它，并把 hygiene 扩展到『目录 / 可疑名（如 `-p`、`%VAR%`、`$VAR`）』。",
    "R4 采样滞后 ~14 帧（§3.3）会**系统性低估**每个注入窗口的位移（右移/左移各少记 ~51.33 px），并让跳跃窗口丢掉起跳前 ~14 帧。当前报告的逐帧**速率**与常量自洽，故结论不受影响；但若下一批要用『位移总量』当断言，必须先接受或校正这个偏移。",
    "R5 `input_axis` 恒 `null`（`axis_caveat.txt` 实测 3 帧全 null，`assert input_axis` 直接报 `does not have the property 'input_axis'`）⇒ DR-68 ③(a) 的『断言轴值改变』在真机**几乎不触发**；真机承重的只能是**按目标轴的位置断言**（DR-68 ⑧）。这与 DR-68 验收的告诫一致。",
    "R6 证据形态链仍**未在真机上被走到**：本轮死在 Developer 违约（冻结之前），DR-68 ①（Tester 证据形状）既未证实自愈也未证伪。`runs/smoke-t8` 的 schema 根因依然是**唯一**观察到的那一次。",
    "R7 钥匙管道（`DSH_TERM_CMD` 里的 `keyval.txt` 路径）已随 `dc9d350` **入库**。虽无明文，但建议下一批把 harness 环境注入改成不把 key 文件路径放进角色可见的 shell 环境（或至少在 `redact_tree` 里覆盖该形态）。",
    "R8 **流程**：调度者在我验收期间已连落 `78bd4cb`/`dc9d350`/`5f3fea4`（含 D269/D270 与 `TASK-DR69.md`），即**在接受独立验收之前**就把被验收报告的结论写进了决策日志并派生了下一批。与 T8 轮的 R5（同一文件被两方改写）同族：报告是单一作者工件，但它被入库、被 D269 引用、又被 D270 超越，而验收结论可能与之相左——**若验收 fail，D269/D270 需要回改**。建议下一批把『验收通过后才写决策日志』作为硬次序。"
  ],
  "unverified": [
    "U1 **attempt-A 的全量轨迹不存在**（实现者删除 `runs/smoke-t9` 后未保留 16.4 MB `developer.attempt1.json`）。因此 F-T9-4 的『单条工具结果 15,570,803 字节(msg 221)』**只有实现者的机器摘要**（`attempt1-aborted/developer_attempt1_summary.txt` 第 2/3 行）可读，**我无法逐帧复核**；摘要内『下一条消息即 `llm-connector chat request failed`』与 console 的退出码 5 自洽，仅此而已。",
    "U2 **进程退出码本身**：我核实的是一致性与代码映射（`exit_code` 文件 `32 0A`、`meta.json 2`、`HofError::Contract ⇒ 2`、`cli.rs` 错误路径），**离线无法复现进程返回值**；`ROUND_EXIT=2/5` 是实现者的控制台捕获。",
    "U3 **F-T9-5 的孤儿进程 pid 77708 / `--mcp-port=51911`**：保留工件里 `attempt1-aborted/meta.json` 的 `game_endpoint` 是 `null`，`stop_orphan.txt` 只有 `{\"stopped\": true}`。我**能**确认的是：quarantine 里 attempt-A 的 scratch 有 `args/jrel.json`、`restart.json`（11:06:10）与 `play.json`，与『11:06:10 起过游戏』吻合；且**现在**全机只有编辑器 75204、无游戏监听（我实测）。⇒ 『曾存在 pid 77708』对我是**间接支持**，不是直接证据。",
    "U4 **报告独立实验的原始数字不能被我重跑**（离线禁止启动 Godot / 碰端口）。我能做且已做的是：原始回包内部一致 + 与游戏常量的算术自洽 + 来源通道可判（`play_scene.json` → `running_game_*`）。⇒ 这些是**冻结工件上的核算**，不是新的观测。",
    "U5 **报告 §3.2 的『左移有效』与我核实一致，但其对照前提仍有限**：每个窗口前都做了 `release_all`（3 个动作 pressed:false，`replayed:true`），这确实排除了 t8 的『右移未释放』混淆；但两次实验仍**共用同一个脚本/同一次会话**（`e3_probe.py` 的顺序窗口 + `e3_interact.py` 的瞬移），不是两条独立通道。",
    "U6 **F-T9-4 的通用性**（『任何角色 `dir /s /b` 到大目录都可能重演退出码 5』）为报告自标的推断，我未测其它命令形状（离线也不该测）。",
    "U7 **两个假绿陷阱的『正确读法』在报告里的表述**（trap②『`git cat-file -e HEAD^:<不存在文件>` 在 cmd 与 bash 都是 128』一句）我未逐字复核其每一步；我只复核了**有证据力的那一步**（两 revision 对同一路径存在性不同：bash 128 / cmd 0）与两个对照（都存在 ⇒ 0/0；都不存在 ⇒ 128）。",
    "U8 `.workspace/mario/.hoh/**` 与 `.godot/**` 的**全部**内容我没有逐文件审计（只做了 mtime 普查与工程树哈希），因此『实验没往 `.hoh` 里写』是基于 `.hoh` 目录 mtime 停在 11:27:26 的推断。"
  ]
}
```

---

## 1. 逐条判据表（我的判定 vs 报告）

| 编号 | 我的判定 | 与报告一致？ | 我的关键证据（自产） |
|---|---|---|---|
| **E1** | **not_met** | 一致 | 三树同 `1f3d20ed…`（我重实现 `hash_tree`）；工程文件 mtime 最新 `player.gd 07:19:25`，>11:08 计数 0；`warnings.log` 两行原文；`result.json` 原文；`versions/index.json` 仅 A0；无 `tester.*` |
| **E2** | **不可判定** | 一致 | `candidate` 目录 0 个、`deterministic` 0 个；`run_loop.rs:938-987` 在 `:989` 电池之前 |
| **E3** | **不可判定**（轮内无证据）；实验数字我复核为真但拒判 met | 一致 | 逐帧数字自抽自算（§3）；0 张截图 / 0 次 `assert_node_state`；来源 = 游戏端点 `running_game_*` |
| **E4** | **不可判定** | 一致 | 无 `iter-1/evidence.json`、无 `tester.*`、无 `qa_report.md`；唯一 `evidence.json` 是 `iteration:0` 空副本 |
| **E5** | **不可判定** | 一致 | `versions/index.json` 仅 `A0(init)`，无 `A_1` |
| **E6** | **不可判定** | 一致 | 无 QA 工件 |
| **C1 闸门** | **通过（首次真机点火，原因正确）** | 一致 | 三方一致 + 零写入的内容级证明 + 代码链（§2） |
| **C2 不可判定** | **正确** | 一致 | 证据缺失是硬事实，报告拒绝借证据 |
| **C3 浪费预算** | **成立；主因不是提示词** | 一致（我加强） | prompt 逐字节比对（§4） |
| **C4 E3 实验** | **数字成立；拒判 met 正确** | 一致 | 我自抽逐帧 + 常量验算 + 通道判定（§3） |
| **C5 新发现** | **F-T9-1/T9-2/T9-3/T9-6 成立；F-T9-4 仅间接；无污染** | 一致 | 代码行 + 原始回包 + 摘要比对（§5） |
| **C6 守卫** | **全部成立** | 一致 | 四棵树摘要 + 写-删检查 + 嵌套仓 + 三个陷阱（§6） |
| **C7 诚实** | **成立（3 minor + 5 info 扣分）** | 一致 | §7 |

---

## 2. 闸门（本轮的核心新事物）

### 2.1 零工程写入 —— 我自己的内容级证明

```
# 我自实现的运行时 hash_tree（排除 {.hoh,.git,.godot,.import}；rel\n{len}\n{bytes}\n；Path 序数序）
.workspace\mario                                                                  17 files 18397 B 1f3d20ed50b472e422832c4fa2c8d7b72ae04ee11fa4c5ace65fb20a43997fd8
runs\smoke-t9\versions\1f3d20ed…（A_0 / role=init）                                17 files 18397 B 1f3d20ed…
runs\smoke-t9\iter-1\planner-view                                                 17 files 18397 B 1f3d20ed…
# 工程文件 mtime 最晚的三个
scripts\player.gd   2026-09-30 07:19:25   ← t8
scenes\main.tscn    2026-09-30 07:17:58   ← t8
scripts\main.gd     2026-09-30 07:16:30   ← t8
# 计数
工程文件晚于 2026-09-30 11:08 的数量 = 0
工程文件晚于 2026-09-30 10:49 的数量 = 0
runs/smoke-t9 内任何目录晚于 10:49 的数量 = 0（t6/t7/t8 亦然）
```

**读法**：不是『mtime 说没写』，而是**活体工程树与 A_0 快照逐字节同一**（我复现运行时算法得到同一个 64 位十六进制摘要），加上 mtime 普查 ⇒ 连『同长度同内容替换』这种哈希盲区都被排除。同时工程目录 mtime（`scenes 07:17:58`、`scripts 07:18:18`、根目录 `10:51:57`）在**正式轮 11:08–11:27 内没有任何变动** ⇒ 也排除了『新建后删除文件』的瞬态写入。

### 2.2 三方一致（原文）

```
runs/smoke-t9/exit_code               字节 32 0A                → "2\n"
runs/smoke-t9/meta.json               "exit_code": 2
.spec/.../round/console_retry.txt     ROUND_EXIT=2   START 11:08:44  END 11:27:29
runs/smoke-t9/iter-1/result.json      "ok": false, "failed_role": "developer", "reason": "contract_violation"
runs/smoke-t9/warnings.log            iteration 1: no_progress (the developer stage produced no change)
                                      iteration 1: contract violation no_engineering_write (the developer stage ended
                                      with no engineering write: no file in the artifact tree outside the hash-excluded
                                      runtime paths changed; every write went to an excluded path such as `.hoh/scratch`,
                                      `.godot/**` or `.import/**`)
runs/smoke-t9/meta.json               artifact_gate {applicable:false, launchable:false,
                                      reasons:["the round failed; no artifact gate was produced"]}
runs/smoke-t9/iter-1/result.json      artifact_gate {applicable:false, launchable:false,
                                      reasons:["no launchable gate was evaluated for this iteration"]}
```

**代码链**：`run_loop.rs:938-948`（哈希相等 → `no_progress` 警告）→ `:949-987`（同一条件 → `no_engineering_write` + `finalize_failure(... Role::Developer, "contract_violation" ...)` + `return Err(HofError::contract(violation))`）
→ `errors.rs:86-95`（`HofError::Contract ⇒ 2`）→ `cli.rs:189-198`（错误路径 `exit_code_of`）→ `cli_impl.rs:604-613`（错误路径 `failed_run_summary` + `finalize_run` 写 `exit_code` 与 `meta.json.exit_code`）→ `cli_impl.rs:701-715`（`failure_exit_code` 优先，与 `errors.rs` 同源，**不可能漂移**）。

### 2.3 判定：闸门**因为正确的原因**点火，**现在可信**

- 触发条件是**测量**（`hash_tree` 前后相等），不是『Developer 为什么停』——`run_loop.rs:925-937` 的注释明确记录了 DR-66→DR-67 的收窄被去掉的过程。
- 我独立确认了『相等』是真的（内容级），所以这不是「闸门误报」。
- **它修好了 t7 的假绿**：t7 在同种零增量下报 `ok=true/exit 0/launchable=true`（T7 台账）；本轮报 `ok=false/exit 2/launchable=false`（两处 gate 都自洽）。这正是 DR-68 ⑦ 想要的行为。
- **信任边界**：闸门只测『artifact 树在哈希排除路径之外是否有变化』。它对**空目录**（如 `-p`）与**哈希排除路径内的写入**（`.hoh/**`、`.godot/**`）是盲的——这是设计意图，但见 D3/R3。
- **首次真机点火的代价认知**：我在离线侧未发现闸门的误报面；不过『零增量』同时也会在『本轮无所需改动』时触发，即它会**合法地**把「本来就没活干」判成失败。本轮 A_0 已是 t8 完成态、plan 的第 1 优先级本就满足，这层语义重叠值得下一批在设计上区分（见 §9 建议 3）。

---

## 3. E3 的逐帧抽取与算术（我从原始回包自算）

原始文件：`.spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/experiment/{e3_probe_output.txt,e3_interact_output.txt,play_scene.json,axis_caveat.txt}`。

### 3.1 每帧数字

| 窗口 | 注入 | 样本数 | 首 → 末 x | dx | 每帧 | 每帧 ×60 | 对照常量 | y |
|---|---|---|---|---|---|---|---|---|
| BASELINE | 仅 release | 30 | 恒定 | **0.000000** | 0 | 0 | 静止 | 恒定 |
| MOVE_RIGHT | `move_right pressed:true` | 60 | 111.333305 → 327.666595 | **+216.333290** | `216.333290/59 = 3.666666` | **220.0000 px/s** | `speed=220.0` ✓ | 283.998993 恒定 |
| MOVE_LEFT | `move_left pressed:true` | 60 | 283.666718 → 67.333321 | **−216.333397** | `3.666667` | **220.0000 px/s** | `speed=220.0` ✓ | 283.998993 恒定 |
| JUMP | `jump pressed:true` | 30 | 63.667 恒定 | 0 | 0 | — | — | 221.091949 → **214.258911@f6** → 283.979340 |

### 3.2 算术核对（我的，不是报告的）

- 位移/帧 = dx / (样本数−1)（**60 个样本只有 59 个区间**）：`216.333290/59 = 3.6666661`；`216.333397/59 = 3.6666677`。逐帧唯一值分别是 `{3.666656,3.666664,3.666672}` 与 `{-3.666672,-3.666664,-3.666656}` ⇒ **恒定速率**。
- `3.666667 px/帧 × 60 帧/s = 220.0000 px/s`，与 `scripts/player.gd:3 @export var speed: float = 220.0` **逐字吻合**；`velocity.x = dir * speed`（`:32`）是唯一写 x 速度的路径。
- 跳跃：地面 `y = 283.998993`，观测最低 `214.258911` ⇒ 起升 **69.740082 px**。
  - 连续解 `v²/2g = 430²/(2·1400) = 66.0357 px`。
  - **半隐式欧拉**（Godot 的 `velocity.y += g*dt; move_and_slide()`）在取整前的高度 ≈ `v²/2g + v·dt/2 = 66.0357 + 430/120 = 69.6191 px`。
  - 观测 69.7401 px，与半隐式欧拉相差 **0.12 px** ⇒ 与游戏自身代码路径 + `gravity=1400` 自洽（远优于与连续解的 3.7 px 差）。
- 到顶时间（连续解）`430/1400 = 0.3071 s = 18.4 帧`；由『峰值在采样窗第 6 帧』反推注入发生在采样窗开始前约 **12–14 帧**（见 §3.3）。
- 金币/终点：`Main` 起始 `{coins:0, lives:3, state:"playing", time_left:118.97}`；`running_game_set_node_property` 把 Player 移到 `Coin1(300,290)` ⇒ `coins 0→1`，且**重新读场景树 `Coin1 present = False`**；再移到 `Goal(6400,280)` ⇒ `Main.state = "won"`（`time_left 117.72`）⇒ 拾取与胜负都是**运行时状态变化**，不是静态字段。

### 3.3 我额外发现、报告未提的系统偏差：采样滞后 ~13–14 帧

每个窗口在注入前先读 `before`（均为 `y=283.999`、`velocity=(0,0)`、`controllable=true`），但**第一个样本**已经在运动中：

```
MOVE_RIGHT  before.x=60.0     first.x=111.333  差 = +51.333 px = 14.0 帧 × 3.6667
MOVE_LEFT   before.x=334.9999 first.x=283.667  差 = −51.333 px = 14.0 帧 × 3.6667
JUMP        before.y=283.999  first.y=221.092  差 = −62.907 px
            按 y(t)=283.999−(430·t−700·t²)（t 以帧计）：t=14 → 221.78（观测 221.09，差 0.7 px）
```

⇒ **每个窗口都丢掉注入后的前 ~14 帧**。后果：报告的 `dx/dy` 是**采样窗内**的位移，不是该动作的**全部**位移（真实约多 51.3 px）；报告的**速率**与常量自洽所以结论不受影响，但若下一批用『位移总量』做断言，必须先接受/校正这个偏移。报告把数字如实标为窗口值（`frames=60`），但**没有点出这个滞后**。

### 3.4 来源确实是**游戏进程端点上的语义工具**

- `play_scene.json`：`{\"endpoint\":\"http://127.0.0.1:61183/mcp\",\"mcp_port\":61183,\"pid\":106368,\"playing\":true,\"mode\":\"main\"}` ⇒ 端口来自 `editor_play_scene` 的回包。
- `e3_probe.py`/`e3_interact.py`：`urllib.request` 直连 `http://127.0.0.1:<PORT>/mcp`，`PORT` 即上面的 61183/62306。
- 调用的工具**全部**是 `running_game_*`（`play_input_recording` / `get_node_property_samples` / `set_node_property` / `get_scene_tree` / `get_node_properties` / `run_test_scenario`），**没有** `editor_simulate_input_action`；`probe_editor_prerun.txt` 实测编辑器端点 154 个工具里 `running_game_* = 0` ⇒ 这些调用只能落在游戏端点。
- **风险旗①的纪律执行**：`raw/input_channel_probe.json` / `GAME_INPUT_CHANNEL_OK` 本轮**根本没出现**（无电池），报告没有任何判定建立在探针上。✓

### 3.5 拒判 met 的判定：**正确**

- `REQUIREMENTS.md:114` 的 E3 证据形式 = **`simulate_sequence` 回放 + 前后截图 + `assert_node_state`**。我实测实验里：`capture_screenshot` **0 次**、`.png` **0 个**、`assert_node_state` **0 次**（`run_test_scenario` 只用过一次，且其 `input_axis` 断言因属性不存在而 `passed:false`）。
- 任务书 §5 末句（『不得声称 E3 已 met，除非你有游戏进程内、语义工具的观测证据』）是**必要条件**，不是充分条件；`REQUIREMENTS` 的形式要求更严。
- 更决定性的是：**E3 是本轮判据，证据必须是轮内的**（任务书 §4 要求把证据留在 `runs/<id>/**`）。轮内连电池都没跑 ⇒ 与实验无关地**不可判定**。
- **不把输入通道探针的成功当行为证据**：报告做到了；我也**没有**采信任何探针输出。

---

## 4. Developer 的浪费预算与「因」

### 4.1 我自己的命令级统计（两条轨迹）

```
developer.attempt1.json : assistant 150 / tool_calls 184 / tool 结果 184
   .hoh/scratch 命中 139 条命令 ； %HOH_ 出现 175 次 ； $HOH_ 1 次 ； bash -c 0 次
   提及工程源文件 5 条，全部为读：
     #11 dir /s /b scenes scripts addons 2>nul; echo "=== project.godot ==="; type project.godot
     #14 type project.godot
     #17 type scenes\main.tscn  |  type scripts\main.gd / type scripts\player.gd
     #20 type coin.gd / enemy.gd / goal.gd / brick.gd / question_block.gd
   提及 running_game 66 条 ；裸 HTTP 打过的游戏端口 {57529, 65009, 55087, 61245}
   game_endpoint_unavailable 原串 4 次（2 条工具消息）；was unexpected at this time 2 条
   -32602 原串 18 处（全部在此文件的模型回包里）
developer.attempt2.json : assistant 25 / tool_calls 32
   .hoh/scratch 命中 0 ； %HOH_ 5 ； $HOH_ 8 ； was unexpected at this time 1
   内容 = 重复读 .hoh/TASK.md / plan.md / TOOLS.md / 工程源文件 + 反复试 editor_get_errors
工程写入：两次 attempt 合计 = 0（见 §2.1）
```

⇒ 报告『它的预算被 scratch MCP 客户端与探游戏吃掉』的**主结论成立**；但『175 次调用**全部**』（F-T9-2）对 attempt2 不成立（D2）。

### 4.2 attempt-A 也做同样的事（我从 quarantine 独立发现）

`runs/smoke-t9/quarantine/.hoh.stale-1790737725/scratch/`（10:52–11:06，这正是 attempt-A 的 Developer 留下的、被 DR-61 机制搬进轮目录的字节）里有：

```
call.bat  target\release\hoh.exe tools call %1 --args-file .workspace\mario\.hoh\scratch\args\%1.json
call.sh   ./target/release/hoh.exe tools call "$tool" --args-file …
post.ps1  Invoke-RestMethod -Uri ("http://127.0.0.1:" + $p + "/mcp") …
tools.txt 4013 B 的 editor_* 工具清单
args/running_game_get_node_property_samples.json、args/play.json{“mode”:“main”}、args/press.json、
args/jrel.json{“action”:“jump”,“pressed”:false}（11:06:10）、args/restart.json（11:06:10）、args/stop.json
```

⇒ attempt-A 的 Developer **同样**自造了 MCP 客户端 / 裸 HTTP 探针（与 attempt-B 同型）⇒ 『零写入』不是单次抖动，而是在**本轮条件**下连续两次复现的行为。这与 D266 记录的 t7（另一个机制）以及 t8（同样撞 `game_endpoint_unavailable` **20** 次却写了代码）共同说明：**结构障碍是放大器，模型反应才是分叉点。**

### 4.3 关键判定：是提示词变更，还是模型方差？——**证据不支持提示词变更**（我做了逐字节比对）

我从 t8 与 t9 的**同一角色、同一 attempt 编号**的轨迹里取出 Developer **实际收到的** system prompt 与 task prompt：

```
sys8  len=6873  sha256[:16]=aea355596d239696
sys9  len=6873  sha256[:16]=aea355596d239696
SYS IDENTICAL: True          ← 逐字节相同
user8 len=791  sha256[:16]=a2cb737c796a36b8
user9 len=791  sha256[:16]=1107f8ca3262b64b
USER 的差异仅两处（diff 全文）：
  -5. Use `{HOH_HOH_BIN} tools call …`      +5. Use `%HOH_HOH_BIN% tools call …`
  -round whose only writes went to `{HOH_SCRATCH_DIR}` …  +round whose only writes went to `%HOH_SCRATCH_DIR%` …
  sys8/{HOH_=0  sys9/{HOH_=0   user8/{HOH_=2  user9/{HOH_=0
```

配套事实：

1. **DR-68 ⑥ 的合法终止符只加在 `planner.md` 与 `tester.md`**（`git show 6b13d32 --stat`：仅这两文件 +8 行；`git log 0f37105..HEAD -- src/prompts/developer.md` **空**）⇒ 对 Developer 无影响；而 Planner 拿到新协议后**依然**判 `RepeatedFormatError`（§5 F-T9-3）⇒ 该提示词改动**连它自己的目标都没达成**，更不可能是 Developer 零写入之因。
2. **DR-68 ⑤ 的占位符修复只让 Developer 的 task prompt 从『无法解析的 `{HOH_*}`』变成『可用的 `%HOH_*%`』**（同一修复把 `TOOLS.md` 里的单花括号 3→0，`%HOH_` 6→9，文件大小 32088 B 不变）⇒ 方向是**更清晰**，不可能诱发绕道。t8 在**更差**的文本下还是写了代码。
3. **角色工具矩阵未变**：`src/tools/policy.rs` 在 `0f37105..HEAD` **零 diff**；`src/tools/` 的变动只有 `index.rs` 的占位符 + rustfmt（我读了完整 diff）。
4. **`src/prompts/mod.rs` 的 diff** 也全部是占位符 `{{{{…}}}}`（+ 一处 rustfmt）。

⇒ **结论**：本轮 Developer 的零写入**不能归于近期提示词改动**（关键提示词要么逐字节未变，要么只朝『更可用』方向变）。**证据支持的**是一个更强的读法：**同一结构障碍（F-T9-1）+ 同一份 plan 下，模型连续两次选择绕道**，而 t8 在同样障碍下选择写代码 ⇒ **模型反应/本轮 plan 框架是必要因子**。**证据不支持的**是把 former 归给某条具体 prompt 文本；也**不足以**把它单称『普通模型方差』——两次 attempts 同向、且 attempt-A 与 attempt-B 的绕道方式同型，说明它是**本轮条件下的稳定行为**，而不是一次性随机。

**报告的推断（§2.4 三条，≈0.8/0.6/0.5）与我的差异**：报告已完成『不是提示词』这一步（它说的是『提示词层缺一条分工约束』，属**新增建议**而非归因）；我把它强化为**可核对的逐字节拒绝**。报告的推断①（plan 把可观测结果钉在游戏内读数、而 A0 已功能完整）我**支持**（`plan.md` 第 3/4/5/12 行 + `A_0 = t8 的 A_1` + t8 电池 11/11 ⇒ 计划项基本已满足）；推断③（缺少『本轮改什么』的抓手）与①是同一证据的两面。**但**我注意到 t8 的 `plan.md`（3986 B）**同样**把可观察结果钉在 `running_game_get_scene_tree` / `running_game_get_node_property_samples` 上，而 t8 写了代码 ⇒ **plan 框架是放大因子，不是充分条件**。

---

## 5. 新发现清单的复核

| 编号 | 级别 | 我的复核 | 证据 |
|---|---|---|---|
| **F-T9-1** | major | **成立**（只读代码 + 冻结回包，未跑真机） | `tools/mod.rs:138`（`game: Arc<Mutex<Option<GameRoute>>>`）、`:186-205`（`client_for` 无路由即 bail，文案逐字）、`:312`（`register_game_endpoint` 只写本进程内存）、`bridge.rs:227-234`（`channel_for` 每次 `McpChannel::new`）、`cli_impl.rs:53`（每条 `tools call` 一个新 channel + 进程退出）；轮内原始回包 `developer.attempt1.json` msg74/msg86 与该文案逐字相同；`experiment/game_endpoint_probe.txt`。**同时**：Developer 用裸 HTTP 在 57529 上**成功**读到了游戏状态（call#59/#84/#91）⇒ 游戏确实在跑、端点确实存在，**堵的是契约通道**。 |
| **F-T9-2** | major（E1 直接因） | **成立**（数字见 §4.1；措辞见 D2） | 同上 + §2.1 的三个内容级事实 |
| **F-T9-3** | minor | **成立** | `planner.attempt1.json`：`COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` 原串 **7** 次；末两个 assistant 回合无工具调用；`msgs[97..99]` 三条 `No tool calls found in the response…`；`msgs[100]` `exit RepeatedFormatError`；`planner.attempt1.log` `artifact_valid:true` |
| **F-T9-4** | minor（可靠性） | **仅间接**（见 U1） | `attempt1-aborted/developer_attempt1_summary.txt` 第 2/3/16-17 行：`n messages 223`、`largest messages: [(221, 15570803), …]`、msg221 是 `dir /s /b /a "%TEMP%" \| findstr …` 的输出、msg222 `content='llm-connector chat request failed'`；console `ROUND_EXIT=5`。**全量轨迹已不存在** |
| **F-T9-5** | info | **间接支持**（见 U3） | quarantine scratch 的 11:06:10 时间戳；`stop_orphan.txt` `{\"message\":\"Playback stopped\",\"stopped\":true}`；**现在**全机只有 75204、无游戏监听（我实测） |
| **F-T9-6** | info | **成立** | `axis_caveat.txt`：3 帧 `input_axis: null`；`run_test_scenario` 的 assert `passed:false, reason=\"node '/root/Main/Player' does not have the property 'input_axis'\"` |

### 污染检查（调度者问的第 5 条的附加项）

- **没有写入 `runs/**`（本轮之外）**：`runs/smoke-t9` 摘要 = `541e2d81…36ca9d`（83 文件）、**最新 mtime `2026-09-30 11:27:29` = 轮结束时刻**；实验发生在 11:27:29 之后（报告 §3.2 用的 `editor_play_scene` pid 106368 在 §1.3 的轮结束之后）⇒ 若实验往轮目录写过任何字节，mtime 必然后移。**没有** `runs/smoke-t9-experiment` 这类新目录（对照 t8 有 `runs/smoke-t8-experiment`）。
- **没有写入工程树**：实验前后工程树 = `1f3d20ed…` == A_0 快照（§2.1）。实验确实改变了**运行中的游戏状态**（瞬移 Player、改 Main 计数），但那是进程内存，不是工件。
- **`.godot/**` 有 3 个编辑器缓存文件被重写（11:36:30）**：属编辑器副作用、哈希排除路径，且**晚于轮结束**；不构成轮内证据污染（但见 D8 的措辞）。
- **`.hoh/**` 未见实验写入**：`.workspace/mario/.hoh` 目录 mtime 停在 `11:27:26`（< 轮结束），其下最新文件也是 11:27:26。

---

## 6. 守卫、基线、陷阱

### 6.1 摘要（开工与收工两次一致）

| 树 | 文件 | 我的摘要（文化排序，仓根相对） | 最新 mtime | 与记录 |
|---|---|---|---|---|
| `runs/smoke-t6` | 135 | `c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03` | `2026-09-29 02:32:01` | **= 任务书自证值** ✓ |
| `runs/smoke-t7` | 115 | `6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7` | `2026-09-29 14:41:14` | = DR-66/67 记录 ✓ |
| `runs/smoke-t8` | 358 | `6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7` | `2026-09-30 07:58:28` | = DR-68 记录 ✓ |
| `runs/smoke-t9` | 83 | `541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d` | `2026-09-30 11:27:29` | = 报告 §9.2 ✓（83 文件亦符） |

**写-删检查**：`runs/smoke-t6|t7|t8` 下**晚于 `2026-09-30 10:49` 的文件数 = 0、目录数 = 0**（三棵皆然）。目录 mtime 是最敏感的『写过再删』痕迹（删除会更新父目录 mtime），三棵在所有层级都没有本轮窗口内的更新。
**已知的历史痕迹（非本轮）**：`runs/smoke-t7/iter-1/traj` 的 mtime 是 `2026-09-30 06:56:47` —— 这是 **T8 轮**曾误写 3 个 `*.analysis.json` 后又删除留下的目录 mtime，已在 T8 报告 §11.1 自曝、并由 T8 验收独立确认『文件确已不存在、摘要复原』；它**早于**本轮窗口 10:49，与本轮无关。

### 6.2 其余禁区

| 断言 | 我的独立证据 |
|---|---|
| `PRD-mario.md` 逐字节冻结 | sha256 `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`（= `meta.json.spec.sha256`），mtime `2026-09-20 23:21:21` |
| `DECISIONS.md` 未由实现者编辑 | 工作树 vs HEAD **零 diff**；`509ec0c:DECISIONS.md` 的 sha256 = **`01b9f157…a18d`**（报告 §9.3 的开工值一致）；`509ec0c..HEAD` 内只有**调度者**的 `a9e050c`（±1 行）、`78bd4cb`（+28 行 D269）、`5f3fea4`（+34 行 D270） |
| `godot-mcp/**` 零改动 | 嵌套仓 `git -C godot-mcp/godot rev-parse HEAD = fc63af77c33368c4a1bb839c95d19750554f63a3`；`status --porcelain -uall` **0 行**；引擎树内晚于 `2026-09-30 00:00` 的非 `.git` 文件 **0** 个；外层 `ls-files godot-mcp` = **6484**（真命中）vs `godot-mcp/godot` = **0**（空判） |
| 引擎身份 | `4.8.dev.mono.custom_build.035edfce7`（判据）；sha256 `08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a`、size `194216960`、mtime `2026-09-29 08:31:02`（**仅记录**，与 `meta.json` 逐字相同） |
| 未 push / 未 stage | `origin/master = fe129a163d6ca22e5e4b48b81e7229c4260b1291` 全程未变；HEAD 在我验收期间由 `a9e050c`→`dc9d350`→`5f3fea4`（**ahead 5**）；`git status --porcelain -uno` 空；`git diff --cached` 空；`Cargo.toml/Cargo.lock` 自 `509ec0c` 零 diff |
| 编辑器存活 / 无孤儿 | 我实测：全机仅 `godot.windows.editor.x86_64.mono` **pid 75204**（StartTime `2026-09-29 13:20:54`），cmdline `… -e --path .workspace/mario --mcp-port=9877`，`127.0.0.1:9877` LISTENING 归 75204；**无任何游戏端口监听** |
| 密钥 | 用配置真值（51 字符）在 `.spec`/`runs`/`src`/`tests`/`config`（排除 `model.secret.env` 本身）全树比对：**含明文密钥的文件 = 0**；`runs/smoke-t9` 内 `sk-…`/`api_key` 命中 0。**但**见 D5（管道路径入了库） |

### 6.3 三个假绿陷阱（我亲手复现，bash 与 cmd 双向）

```
① git diff 对不存在的 pathspec 不报错
   $ git diff --stat -- definitely/not/a/real/path        → 输出空, exit=0
   读法：空 + 0 与『没变化』不可区分 ⇒ 断言某路径未改前必须先证 pathspec 真命中
        （本轮对照：git ls-files godot-mcp = 6484 真命中 / godot-mcp/godot = 0 空判）

② cmd 里 ^ 是转义 ⇒ 所有 rev^ 查询一律在 bash 做
   bash : git cat-file -e 'fe129a1^:.spec/…/TASK-DR68-ACCEPTANCE.md' → exit 128
   bash : git cat-file -e 'fe129a1:.spec/…/TASK-DR68-ACCEPTANCE.md'  → exit 0
   cmd  : git cat-file -e fe129a1^:<同一路径>                        → exit 0   ← 假绿
   cmd  : git cat-file -e fe129a1:<同一路径>                         → exit 0
   对照（两 revision 都有 DECISIONS.md）: bash HEAD^ = 0 / bash HEAD = 0   ⇒ 同号，不是假绿
   对照（两 revision 都没有的路径）      : bash HEAD^ = 128                ⇒ 这个形状也不是假绿
   cmd  : git rev-parse fe129a1^                                       → fe129a1 本身（^ 被吃掉）

③ 外层仓不跟踪引擎树
   outer ls-files godot-mcp        = 6484
   outer ls-files godot-mcp/godot  = 0
   git check-ignore -v godot-mcp/godot → .gitignore:33:godot-mcp/godot/
   git diff --stat -- godot-mcp/godot/bin → 空 + exit 0（什么都没说）
   判据来源只能是嵌套仓（fc63af77…、status 0 行）或 mtime/摘要
③′ 同族（我补充）：git check-ignore -v runs/smoke-t9/meta.json → .gitignore:12:runs/
   ⇒ 外层 git status/diff 对本轮**全部证据**都是空判 ⇒ 未变/已留证只能靠目录摘要
```

---

## 7. 诚实性裁定（逐条）

1. **未声称 E1 / E3 met** —— 成立。E1 全文 not_met；E3 全文『不可判定（轮内无证据）+ 独立实验观测』，并明写『仍不判 met』。
2. **明确区分轮内证据与自己的实验** —— 成立。§3.1 说明轮内无 raw，§3.3 逐条列出实验不能确立什么，§16 把实验与轮记录分开索引。
3. **跑了两轮且都留档** —— 成立。attempt-A（`10:49:20 → 11:07:13`，退出码 **5**）与 attempt-B（`11:08:44 → 11:27:29`，退出码 **2**）各有 console/exit_code/meta 留档；我核 `attempt1-aborted/exit_code` = 字节 `35 0A`、`meta.json.exit_code=5`、console `ROUND_EXIT=5` ⇒ attempt-A 也三方一致。
4. **删除重建 `runs/smoke-t9` 与 attempt-A 全量轨迹丢失** —— 如实披露，且与事实相符（该轨迹确不存在；但 **attempt-A 的 scratch 通过 quarantine 幸存**，报告未提，见 §4.2——这是**对实现者有利**的补充事实）。
5. **孤儿进程清理** —— 我实测现在无游戏监听、只剩编辑器 75204；`stop_orphan/probe/interact` 三份回包都是 `{\"stopped\": true}`。**但** 77708/51911 本身只在报告文字里（U3）。
6. **密钥卫生** —— 明文零泄漏（我独立确认），但见 D5（管道路径入库）与 D4（自报读数矛盾）。
7. **未改 `DECISIONS.md`** —— 成立（工作树零 diff；其后改动全在调度者提交里）。报告 §15.6 还主动请求调度者补记 D269 —— 调度者确已记（`78bd4cb`/`5f3fea4`）。
8. **作者单一性** —— 报告由实现者撰写（`78bd4cb` 只加该文件），调度者的 D269/D270 写在 `DECISIONS.md`，**没有**像 T8 那样改写报告正文 ⇒ 比 t8 干净。
9. **扣分** —— D1/D2/D3 三条事实性不准（都属『量化口径』类，不影响判定）；D4/D6/D7/D8 为 info。

---

## 8. 我没查的与做不到的

- **未启动 Godot、未碰任何端口（只读取监听表）、未联网、未调模型端点、未跑真机轮、未跑 `cargo`（构建/测试）**。
- 未逐条审计两条 Developer 轨迹的全部 337 + 139 条消息（约 0.9 MB），只按需检索命令、工具回包、关键串。
- 未审计 `planner.attempt1.json`（225 KB）除格式终止符之外的内容。
- 未复核报告里与 E1..E6 无关的历史转述（t7 的 `E_1` 细节、`LimitsExceeded` 数字、DR-64/67 旧账）。
- 未重跑报告的任何实验（离线禁止）；未重放 t8/t7 的 raw 以交叉验证 E3。
- 未核 `usage.json` 之外的 token 账目明细（我只核了合计：`561394 + 7532725 = 8094119` 与报告一致；`119603+932145+63321 = 1115072 ms`，墙钟 `11:08:44→11:27:29 = 18:45` 与报告一致）。
- 未检查仓内是否存在除 `%DST%`（t8 验收 D8 登记的 2026-09-24 历史异物）之外的其它历史异物。
- 未验证 `.workspace/mario/.hoh/**` 与 `.godot/**` 的逐文件内容（只做 mtime 普查 + 工程树哈希）。

---

## 9. 对下一批的建议

1. **先做设计裁决，再碰提示词**：`TASK-DR69.md`（`5f3fea4` 已建）方向正确。三条候选（持久化端点记录 / `hoh tools call` 内自动发现游戏端点 / 明确禁止角色直连并同步改提示词）必须**显式选一条并写进文档**；只要 plan 还把可观测性钉在 `running_game_*` 上，F-T9-1 就会继续吞预算（R1/R2）。
2. **给『角色可观测性』一条可执行路径**：既然 `running_game_*` 对角色新进程不可达，而 Developer 的 `[definition-of-done]` #4 又要求它用 `running_game_get_node_property_samples` 自证——**这两条契约当前互相矛盾**。要么给角色一个可用的游戏通道，要么把 #4 改成角色真正能执行的编辑器侧路径。
3. **区分『零增量违约』与『本轮本无需改动』**：本轮 A_0 已是 t8 完成态、plan 首要项本就满足，闸门照样判失败。建议在 plan/闸门层加一个显式的『本轮无必需增量』判据（否则要么空转、要么被强迫做无意义改动）。
4. **修三个量化口径**（D1/D2/D3）：把『cmd 方言错误』改成可定义的模式并列出命中；把 attempt2 单独描述；把 attempt-A 的写入说清（含空目录 `-p`）。
5. **清掉并防御 `-p`**（D3/R3）：删除活体 `.workspace/mario/-p`（它会进 A_0 身份树之外、并随快照传播），把 `artifact_hygiene` 从『文件』扩到『目录 + 可疑名（`-p`、`%VAR%`、`$VAR`）』。
6. **E3 若要继续推进**：接受或校正 ~14 帧采样滞后（R4）；补齐 `REQUIREMENTS` 要求的**截图**与 `assert_node_state`（当前 0 次）；并在**轮内**跑出电池（否则永远不可判定）。
7. **密钥管道**（D5/R7）：`redact_tree` 应覆盖 `HOH_MODEL_API_KEY="$(cat …)"` 这类形态；或不让角色 shell 环境携带 `DSH_TERM_CMD`。
8. **流程次序**（R8）：验收结论应先于 D269/D270 这类『已成定论』的决策日志；本轮调度者在验收落地前就写了 D269/D270 并派生了 DR-69，若验收判 fail 就需要回改决策日志（这正是 D245 想避免的）。
9. **证据形态链仍待首次真机验证**：`runs/smoke-t8` 的 Tester schema 根因到本轮仍未复现。下一批必须让 Developer 先产出增量，否则 DR-68 ① 的真机自愈永远测不到。

---

## 10. 结论一句话

**本轮报告的头号结论全部经我独立复核为真——闸门首次真机点火是因为正确的原因（工程树字节同一、三方退出码一致），E2..E6 的四条『不可判定』有硬事实支撑，E3 的四类行为数字与游戏常量自洽到 <1 px 且来源确为游戏进程语义工具、拒判 met 亦正确，F-T9-1/F-T9-2/F-T9-3/F-T9-6 成立，三条基线与全部禁区自证成立、三个假绿陷阱我亲手复现；而报告的『因』不是提示词——Developer 的 system prompt 与 t8 逐字节相同、task prompt 只朝更可用方向变——真正需要裁决的是 F-T9-1 这个结构性障碍。报告有 3 条 minor 量化不准与 5 条 info（含一个空 `-p` 目录与一处密钥管道入库），均不动摇上述任一结论，故本验收判 `pass`。**
