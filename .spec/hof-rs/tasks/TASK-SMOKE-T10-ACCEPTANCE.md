# TASK-SMOKE-T10-ACCEPTANCE — 独立验收（验收者 = 全新子代理，无上游上下文）

> 被验收对象：`.spec/hof-rs/tasks/TASK-SMOKE-T10-REPORT.md`（revision `eadde3e`，sha256 `57f83784…de239`）
> + 任务书 `TASK-SMOKE-T10.md`（其基准书 `TASK-SMOKE-T8.md` 全效）+ `runs/smoke-t10/**` 原始工件。
> 我自己产出的证据全部来自**只读**操作：`runs/smoke-t10/**` 与冻结基线的重算、原始响应逐帧抽取、轨迹字节级检查、
> 源码阅读、git/进程只读检查。**我没有启动 Godot、没有联网、没有调用任何模型端点、没有写入 `runs/**` 一个字节。**
> 验收时刻：HEAD `0ed69cda56e5ded9744742e697e1450f055a85d9`（验收期间调度者在并发提交：`6f72e16`(D277)、`0ed69cd`(TASK-DR72)）。

## 结构化结论

```json
{
  "verdict": "pass",
  "criteria": [
    {
      "id": "E1.A0-ne-A1",
      "pass": true,
      "evidence": "我用运行时自己的口径（src/runtime/policy.rs:68-97：排除 {.hoh,.git,.godot,.import}，树根相对路径逐字节排序，sha256 over `rel\\n{len}\\n{bytes}\\n`）重算两棵树，**逐位复现了它们的目录名**：versions/1f3d20ed50b4…=1f3d20ed50b472e422832c4fa2c8d7b72ae04ee11fa4c5ace65fb20a43997fd8（17 文件/18397 B），versions/ed98d1b80be9…=ed98d1b80be945c6d8e8a40fc3b5114dd9e1d33b1c29d576d050255a7fa1a1e1（17 文件/21679 B）⇒ 两树确不相同；我另用报告的 hashtree2 口径复现其 5971b484…/c781cf81… 逐字相同。我独立 diff：ADDED=[] REMOVED=[] MODIFIED=7 全部在 scripts/ 下（brick.gd 171→265、coin.gd 430→975、enemy.gd 1419→1748、goal.gd 275→440、main.gd 2344→3368、player.gd 2231→3216、question_block.gd 510→650，+3282 B），无一个落在被排除/易变路径。语义上也不是一句话：player.gd 新增 hurt_from_enemy + 8 个 @export 可观测量、main.gd 新增 6 个 @export 状态量、coin.gd 新增 _process/falling、goal.gd 新增 reached。"
    },
    {
      "id": "E1.legal-E1-accepted",
      "pass": true,
      "evidence": "iter-1/evidence.json 可解析：iteration=1、qa_status=partial、verified_records=9（F1,F2,F4,F5,F14,F15,F16,N1,N2）、gap_records=11（F3,F6-F13,F17,N3）、**交集为空**；14 条 verified execution_records 的 path 逐条存在（MISSING=[]）；每条 execution_record 都有 type（replay/screenshot/assert/build/runtime_trace）与 candidate_id=ed98d1b8…（Tester 原件里是空串 ⇒ 运行时绑定可见）；gap 每条带 player_impact+recommended_update；planner_handoff 三数组 4/6/6。logs/tester.attempt1.log：exit_status=Submitted、artifact_valid=true、attempt=1、exit_was_limits=false，且 traj/ 下**只有 tester.attempt1.json**（无 attempt2）。全轮 schema_failure=0、RepeatedFormatError=0（我逐文件 grep 四条轨迹）。"
    },
    {
      "id": "E1.round-completed-exit0",
      "pass": true,
      "evidence": "原始字节：runs/smoke-t10/exit_code = `30 0A`（即 \"0\\n\"，`xxd` 亲测）；meta.json `\"exit_code\": 0`；result.json `ok=true, failed_role=null, reason=\"ok\", issues=[]`；attempts 四个（planner1 + developer 1+wrap-up + tester1），durations 之和与 17:28:54→18:23:08（54m14s）一致；battery_passes 长度 1、11 步全 true；usage 合计 25,616,513 = console 的 `total tokens Some(25616513)`。**注意**：第三个退出码位置（进程码）见缺陷 T10A-4。"
    },
    {
      "id": "E1.fresh-empty-project-clause",
      "pass": false,
      "evidence": "**本轮起点不是全新空白工程，且未跑 `hoh init`。** meta.json `start_state = {\"mode\":\"as_is\",\"version_id\":null}`，源码 src/runtime/start_state.rs:22-30 明确定义 AsIs = “The workspace was used as it was found”；本轮命令是 `hoh run --iterations 1 --run-id smoke-t10`（无 --fresh-workspace）。prerun_state.txt（17:28:48）实测 `MARIO_TREE=17 files 18397 bytes`，与 `A_0` 的文件数/字节数相同；runs/smoke-t8/versions/index.json 显示 t8 的 A1 = `1f3d20ed…`、t9 的 index.json 只有 A0 = `1f3d20ed…` ⇒ 本轮 A0 正是 **t8 的产物经 t9 原样携带**（报告 §2.2 自己也写“本轮起点正是 t9 的终点”）。该条款**不在** REQUIREMENTS.md 的 E1 原文里（E1 只要求“一轮完整循环真实跑通 + 三个产物”），它出自 OBJECTIVE-COMPLETION.md 的 **C1**（“`hoh init` 一个**全新空白工程**…**不是**既有 `.workspace/mario`”）⇒ **E1 按 REQUIREMENTS 原文成立，判据(1)/C1 的空白工程条款不成立**；D276 第 10623-10624 行如实记录了这一点，**但被验收的报告本身通篇未提**（见缺陷 T10A-1）。"
    },
    {
      "id": "E1.trajectory-JSON-evidence-form",
      "pass": false,
      "evidence": "E1 的证据形式一栏写着“`runs/<run-id>/` 下全部工件 + **轨迹 JSON**”。四条轨迹里 `tester.attempt1.json` **不是合法 JSON**：`json.loads` 报 `Invalid control character at line 2204 col 311 (char 412862)`，`strict=False` 报 `Expecting ',' delimiter: line 2205 column 8 (char 412870)`；另三条均可解析。⇒ 证据形式 **3/4** 完好；实质三要件不受影响（证据包、QA 报告、电池原始件均独立可解析）。机制见 T10A-2。"
    },
    {
      "id": "Q2.endpoint-reachability",
      "pass": true,
      "evidence": "**角色 CLI 在真机上确实到达了游戏端点**：我把 `tester.attempt1.json` 按两处已知损坏点做最小修复后结构化解析（修法：在每个 `HOH_MODEL_API_KEY=<redacted>` 后紧跟物理换行处补回 `\",`）⇒ 30 条 bash 命令调用了 `running_game_*`（40 处字面调用），其中 **27 条的 tool result 携带真实引擎载荷**；用报告口径（`extra.actions[0].command`）我复现出完全相同的 89 条已执行命令 / 23 条 running_game（分布 get_node_properties 11、run_test_scenario 10、get_node_property_samples 4、create/play/stop 各 2）。载荷是活的游戏进程才会有的：动态位置样本、`run_test_scenario` 的 `resolved_node_path=/root/Main/Player`、`GAME OVER - press Jump to restart`、重启后 spawn x=60、`Lives: 3 / Coins: 0`。**整轮 `game_endpoint_unavailable` = 0 次**（四条轨迹逐文件 grep 均为 0，全树 0）。"
    },
    {
      "id": "Q2.route-lifecycle",
      "pass": true,
      "evidence": "**轮末撤下**：`runs/smoke-t10/game_endpoint.json` 现在不存在（我也实测 Test-Path 为假），收工只有编辑器进程 75204。**轮中存在且有原始证据**：开发者 attempt1 在 17:38:12（`extra.timestamp=1790761092.31`）执行 `type \"…\\runs\\smoke-t10\\game_endpoint.json\"`，其 tool result 逐字冻结为 `{\"endpoint\":\"http://127.0.0.1:61826/mcp\",\"port\":61826,\"source\":\"auto_free_port\",\"pid\":109308}`——与报告 §8.1 的轮中读数一致；同一轨迹里还能看到该游戏的日志行 `[MCP] role=game configured_port=61826 … listening on 127.0.0.1:61826 (editor=false, tools=73)`。**“在第一个角色之前发布”**：每个角色的环境里都带 `HOH_GAME_ROUTE=F:\\…\\runs\\smoke-t10\\game_endpoint.json`（planner 轨迹第 1256 字符处就有），且代码上 `src/runtime/run_loop.rs:733 start_round_game(...)` 位于 planner（:763 起）之前、`src/adapter/godot.rs:3882-3938` 是“就绪后才 publish” ⇒ 结构上成立；但该文件 **17:29:01 的 mtime 与 pid 存活**只能由报告 §8.1 的轮中记录支撑，文件已删，**无法再复测**（见 unverified）。"
    },
    {
      "id": "Q2.developer-no-detour",
      "pass": true,
      "evidence": "开发者两条轨迹：命令中 `running_game_` **0** 次、`http://`/`https://`/`127.0.0.1`/`curl`/`socket`/`Incoming…` **0** 次（唯一的 `mcp` 命中是它写进 GDScript 的注释文字：`## … the MCP property tools …`）；`editor_` 135 次（attempt1）。t9 的“自造 MCP 客户端 + 裸探端口”没有重演。"
    },
    {
      "id": "Q2.tester-evidence-shape-first-attempt",
      "pass": true,
      "evidence": "t8 正是被 schema 拒的那一步，本轮 attempt=1 一次通过（Submitted / artifact_valid=true / 0 schema_failure / 0 RepeatedFormatError）；`No tool calls found` 提醒仍在（planner 6、developer.attempt1 23、developer.attempt2 0、tester 5，我逐文件复现这四个数），但没有一次升级为 RepeatedFormatError。"
    },
    {
      "id": "Q3.frames-and-arithmetic",
      "pass": true,
      "evidence": "我从 `…/deterministic/raw/input_replay.json`（48 次调用：**39 running_game_* + 9 editor_***，see T10A-6）逐帧自抽：move_right 60 样本 x 184.666702→400.999725（Δ=+216.333023，59 个间隔 ⇒ 3.6666614 px/帧）；move_right_release 10 样本 415.666351→448.666260（Δ=+32.999908，3.6666565/帧）；move_left 60 样本 448.666260→232.333389（Δ=−216.332870，−3.6666588/帧）；jump 30 样本 y 269.980835→214.258606(f17 峰)→242.591965，逐帧 dy 严格按 **+0.388885/帧** 递增（= gravity 1400 × (1/60)² = 0.388889，与 `.workspace/mario/scripts/player.gd` 的 `gravity=1400.0` 自洽），起升 55.722229、峰后在窗内回落 28.333359、x 恒定。`player.gd` 的 `speed=220.0` ⇒ 220/60 = 3.666667 px/帧，与引擎自己报的 `velocity.x=3.666656`（×60=219.9994 px/s）逐位吻合。来源是**游戏进程通道**：四条位置断言的 quadruple 都标 `channel=game_process`，且 `input_axis` 在真机恒 `null`（4 次 `…\"input_axis\":null`，`run_test_scenario` 的轴断言原始回包写 `does not have the property 'input_axis'`）⇒ 承重的确是位置证据。"
    },
    {
      "id": "Q3.assertions-accepted-and-PNGs",
      "pass": true,
      "evidence": "4 次 `running_game_assert_node_state` 的 `payload.content[0].text` 逐条解出：operator=neq、property=position、**passed=true 4/4**、`resolved_node_path=/root/Main/Player`，且 expectation **逐条等于该窗口第一个采样**（184.666702/415.666351/455.999573/448.666260）；全轮 `POSITION_ASSERTION_UNAVAILABLE`/`POSITION_UNCHANGED`/`REPLAY_FRAME_MISSING` 只出现在**提示词/EVIDENCE_PLAYBOOK 文本**里（tester 轨迹 2 处、playbook 1 处），**没有任何一条是引擎回包**。冻结候选的 `.hoh/evidence/` 有 8 张 `replay-{move_right,move_left,jump,move_right_release}-{before,after}.png` + `frame-00.png`，9 个文件我逐个验了 PNG magic（89504e470d0a1a0a）与体积（9165–9931 B）。"
    },
    {
      "id": "Q3.partial-verdict-correct",
      "pass": true,
      "evidence": "**金币从未被拾取**：全轮所有 `Coins: N` 读数**全部是 0**（91 处，0 个非 0；分布在 trajectories/证据/场景文件），`Goal.reached` 全轮只出现一次且为 **false**。**而且证据比报告更强**：我在同一候选里抽出静态几何——Player 碰撞 = RectangleShape2D 24×32（中心随节点），Coin1 (300,290)、Coin2 (425,290) 为 CircleShape2D r=11 ⇒ 右移窗口 184.7→401.0（y≈284）与释放窗口 415.7→448.7 **都物理扫过金币圆心区域**（如 x=300 时 rect 288–312 / coin 289–311，y 268–300 / 279–301），金币却始终没被拾取 ⇒“≥1 可交互对象”不只是“没试到”，而是**做过了也没反应**（属产品缺陷，与 D277 决定 2 一致）。**胜利从未被驱动**：Goal 在 (6400,280)，玩家全轮可观测 x 最大 448.666（±1 帧），从未接近；`Coins`/`Goal.reached` 两条独立读数一致。⇒ **E3 = not_met（4 类中 2 类：左右移动、跳跃成立）是完全正确的判定，不是过度保守。**"
    },
    {
      "id": "Q4.new-major-defect-F-T10-1",
      "pass": true,
      "evidence": "见 defects T10A-2：我独立复现了机制、定位了两处坏点与字节偏移，并确认了 4 个脱敏点中哪 2 个致死。报告对根因的描述与 `src/runtime/secrets.rs:70-98` 的代码逐字相符。"
    },
    {
      "id": "Q5.cap-64KiB-and-no-oversized-replay",
      "pass": true,
      "evidence": "两次真实截断：developer `65536 of 80800`（读 res://scripts/main.gd）、tester `65536 of 147809`（读 input_replay.json），均在 tool result 里带显式标注（`hoh: tool output truncated`、`the remaining N bytes were dropped and are NOT part of this result`）与 `hoh_output_limit_bytes/hoh_output_original_bytes/hoh_output_truncated`。无 MB 级回放：**按序列化整条消息**最大 = 156,999 B（developer msg181）、139,445 B（tester msg21）；**按 content** 最大 = 65,888 B（developer）/65,889 B（tester msg21，即 65536+标注）。t9 的 15,570,803 B 事故未复现。报告的具体数字有一处错（见 T10A-3），但结论成立。"
    },
    {
      "id": "Q4.no-repair-attempt",
      "pass": true,
      "evidence": "result.json `repair_retry_used=false`；iter-1/traj/ 无 developer.attempt3；warnings.log（全文 2 行）无 `launch_gate_repair`；quarantine/ 只有 `.hoh.stale-1790760534`，无 `deterministic-pass-*.stale-*`；battery_passes 只有 pass=1 一遍 11 步 ⇒ “零写入的修复尝试”这一类缺陷不存在。`wrap_up_retry_used=true, reason=artifact_missing` 是步数用尽的收尾：candidate 的 mtime 显示 attempt#1 写了 6 个脚本（17:44:06–17:51:16），**player.gd 的 18:09:43 落在 wrap-up 窗口**，即 wrap-up 确实写了工程。"
    },
    {
      "id": "Q4.gate-opened-no-stale-log-no-zero-increment",
      "pass": true,
      "evidence": "门被评估且开启：meta.json 与 result.json 两处都是 `artifact_gate={applicable:true, launchable:true, reasons:[]}`；无过期编辑器日志关门：raw/editor_errors_baseline.json `count=1`，唯一内容是信息性 `[MCP] capture=off …`（battery.json 里同一条被 DR-48 豁免）。零增量未发生：warnings.log 只有 DR-61 隔离行与 qa_scope 行，**无** `Zero-increment shape`/`no_progress`/`no_engineering_write`（工程树也确实有 7 文件增量）。"
    },
    {
      "id": "Q6.guards",
      "pass": true,
      "evidence": "见 §3：四条基线摘要逐字命中历史值（含自证 `smoke-t6=c144ef32…7a9c03`）；mario 工程树 = A_0/A_1 与证据链一致；PRD sha 未变；明文密钥全仓 0 命中；嵌套引擎仓干净；无孤儿进程、编辑器 75204 存活；三个假绿陷阱全部亲手复现。"
    }
  ],
  "defects": [
    {
      "id": "T10A-1",
      "severity": "major（判据解读与披露）",
      "what": "被验收报告（§0/§2）把 **E1 判为 met 而不带任何限定**，全篇未出现“空白工程/fresh/判据(1)/C1”，§0 还写“本轮不可判定的判据：无”。事实是：本轮 `start_state.mode=as_is`，起点是 t8 的产物（17 文件/18397 B）经 t9 原样携带，从未在全新空工程上跑 `hoh init`。报告自己在 §2.2 写明“本轮起点正是 t9 的终点”，却没有把它连到 C1。该限定只出现在调度者的 D276（10623-10624 行）。⇒ 结论：“E1 按 REQUIREMENTS 原文 met”成立；“**判据(1) = 全新空白工程上的 E1 met**”**不成立**。",
      "reproduction": "`python -c \"import json;print(json.load(open('runs/smoke-t10/meta.json'))['start_state'])\"` → `{'mode':'as_is','version_id':None}`；`cat runs/smoke-t10/../smoke-t9/versions/index.json` → 只有 1f3d20ed…；`cat .spec/hof-rs/OBJECTIVE-COMPLETION.md` 第 9-19 行；`grep -n 空白 .spec/hof-rs/tasks/TASK-SMOKE-T10-REPORT.md` → 0 命中。"
    },
    {
      "id": "T10A-2",
      "severity": "major（已由本轮自报为 F-T10-1，我独立确认为真）",
      "what": "`redact_secret_assignments` 把 `runs/smoke-t10/iter-1/traj/tester.attempt1.json` 写成非法 JSON。机制与代码逐字相符：`src/runtime/secrets.rs:81-91` 在不带引号的值上用 `find([';','\\n','\\r'])` 找值尾——Rust 的 '\\n' 是**物理换行**，而 JSON 字符串里的换行是 `\\`+`n` 两个字符 ⇒ 赋值位于 JSON 字符串内部且后随 JSON 转义换行时，扫描一路吃到物理行尾，把字符串余部、闭引号与逗号一起删掉，替换成 `HOH_MODEL_API_KEY=<redacted>`。**两处坏点、同一文件**（同一消息的 content 与 extra.raw_output 各一处）：@char 412834（值尾=412862，即那个物理换行；替换后 `<redacted>` 起于 412852）与 @char 413159。开发者 attempt2 的另 2 处脱敏值后跟字面 `;`（`;C:\\Users\\wyl\\node_modules…`）⇒ 扫描正确停止、JSON 完好（F-T10-2 为真）。**影响面判断**：《tester 轨迹》是过程性/可审计证据，`evidence.json`、`qa_report.md`、电池 raw 全部独立且可解析 ⇒ **不影响本轮的 E1/E3 判定**；但 (a) 直接**削掉了 E1 证据形式里的“轨迹 JSON”** 1/4；(b) 被删掉的是 `set | findstr /i hoh` 环境转储在 `HOH_MODEL_API_KEY=` 之后的**整个物理行尾**——本轮 `HOH_GAME_ROUTE=…` 行幸运地在它之前而幸存，只要字母序换个位置，**证明路由交付的那一行就会被吃掉**（脆弱性，见 risks）。",
      "reproduction": "`python -c` 逐文件 `json.loads`（strict 与 strict=False）：tester 报 char 412862/412870，另三条 OK；`grep -o 'HOH_MODEL_API_KEY=<redacted>' tester.attempt1.json` 后跟 `\\n      \"extra\":` / `\\n        \"returncode\":`；`git show HEAD:src/runtime/secrets.rs | sed -n '70,98p'`；`grep -c '<redacted>' developer.attempt2.json` = 2 且后跟 `;`。我的最小修复（补 `\",`）可使该文件重新解析，且修复后 30 条 running_game 调用、27 条真实载荷、0 次 unavailable 全部可复现。"
    },
    {
      "id": "T10A-3",
      "severity": "minor（度量陈述）",
      "what": "报告 §6 写“最大单条消息 = 65,886 B（developer），tester 最大 52,270 B”。实测：**tester 文件里根本不存在 52,270**（52,270 是 developer 的**第二**大 content 长度）。按 content（字符）：tester 最大 = msg21 的 **65,887 字符/65,889 字节**（正是被 64 KiB 截断的那条），developer 最大 = msg181 的 65,886/65,888；按**整条消息序列化**：developer 最大 **156,999 B**、tester 最大 **139,445 B**。报告把“字符”写成“B”，并把 tester 的 52,270 弄错。对结论无影响（都远小于 MB 级，t9 的 15.5 MB 事故确实未复现）。",
      "reproduction": "把 tester 轨迹按 T10A-2 的方法修复后 `len(m['content'])` 排序：`65887(msg21,tool) / 15159 / 9485 …`；`any(len(c)==52270)` → False。"
    },
    {
      "id": "T10A-4",
      "severity": "minor（证据保全）",
      "what": "“退出码三方一致”的第三处 `console.txt → ROUND_EXIT=0` **不在任何冻结工件里**。冻结的 `…-evidence/round/console.txt`（1657 B，13 行）只有 hoh 自己的 stdout（spec/doctor/run finished/prd coverage），**没有 ROUND_EXIT**；`ROUND_EXIT=$ec` 出自报告自己的包装脚本 `scripts/run_round.ps1:14`，它把该行打到**外层控制台**（hoh 的输出被重定向到 %TEMP%\\smoke-t10\\console.txt），外层那段没有被冻结入库。⇒ 我能从原始字节确认的是：exit_code 文件 `30 0A`、meta.json `exit_code:0`、result.json `ok:true/reason:\"ok\"`；进程退出码只能采信报告的转述。",
      "reproduction": "`grep -rn ROUND_EXIT runs/smoke-t10 .spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/round/` → 只在 `scripts/run_round.ps1` 命中；`wc -l` 冻结 console.txt = 13。"
    },
    {
      "id": "T10A-5",
      "severity": "minor（计数口径与解读）",
      "what": "报告 §5.5/§10 称 `-32602` 全轮 **6 次**且“全部是角色自己参数写错”。字符串出现确实是 6 处，但**真实的 -32602 引擎错误回包只有 2 个**（都在 developer.attempt1，各在 content 与 raw_output 里各出现一次，内容为 `Unknown parameter 'node_path' for tool 'editor_get_node_properties'`，returncode 5）；tester 的 2 处在它写的脚本**注释文字**里（`# DR-58: never send scene_path — the game-scope runner answers -32602…`），不是错误回包。",
      "reproduction": "逐文件 `-32602` 上下文见 §2；developer.attempt2 = 0。"
    },
    {
      "id": "T10A-6",
      "severity": "minor（措辞）",
      "what": "报告 §4.5 写“轨迹里 48 次 replay 调用的工具名**全部**是 `running_game_*`”，同一句的括号里又承认注入走 `editor_simulate_input_action`。实测 48 次 = **39 running_game_* + 9 editor_***（1 `editor_get_input_actions` + 8 `editor_simulate_input_action`）。实质主张（读数与断言都在游戏端点）正确。",
      "reproduction": "`Counter(x['tool'] for x in json.load(open('…/raw/input_replay.json'))['calls'])`。"
    },
    {
      "id": "T10A-7",
      "severity": "minor（披露准确性；与 D271 的“证据里的环境泄露”同族复发）",
      "what": "报告 §16.6 称受控证据目录里“**不含**原始 env dump（我删掉了那一段）”。但 `…-evidence/analysis/redaction_defect.txt:1-4` 逐字保留了环境转储片段：`HOH_ARTIFACT_DIR=… / HOH_GAME_ROUTE=… / HOH_HOH_BIN=… / HOH_ITERATION=1 / HOH_MODEL_API_KEY=<redacted>;C:\\Users\\wyl\\node_modules\\…`（含用户名与 PATH 尾段）。**不是密钥泄露**：我用配置文件里的真值（长度 51）扫全仓 6465 个文件（排除 config/model.secret.env），**0 命中**；`simred.py` 里的 `sk-REALSECRET51CHARS` 是假值。但“不含 env dump”这一句不实。",
      "reproduction": "`grep -n 'HOH_MODEL_API_KEY=' .spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/analysis/redaction_defect.txt scripts/redcheck.py scripts/simred.py`；密钥真值扫描 → 0。"
    },
    {
      "id": "T10A-8",
      "severity": "info（角色侧摩擦，非 harness 缺陷）",
      "what": "报告口径的 23 条 `hoh tools call running_game_*` 并非每条都拿到引擎载荷：按我结构化的 30 条 running_game bash 调用统计，**27 条**载荷正常，3 条没有——① 最早一次 `cd .hoh\\scratch & … hoh.exe tools call running_game_get_node_properties` 回 `<returncode>0</returncode>` 但输出 `hoh: could not find config file for config/hoh.yaml`（cwd 不对，不是 `game_endpoint_unavailable`）；② `for %n in (...) do … > hud_%n.json` 那次输出为空；③ 用 `;` 串联两条命令那次 `returncode 2`（`unexpected argument ';'`）。⇒ “通道可达”由其余 27 条载荷充分支撑。",
      "reproduction": "见 §2 的逐条清单（修复后按 tool_call_id 关联 assistant command 与 tool result）。"
    }
  ],
  "risks": [
    "路由生命周期里“17:29:01 发布 / pid 109308 在该刻存活”这一**时点**只能由报告 §8.1 的轮中记录支撑（文件已按设计撤下，我无法再测）；我能独立证明的是：角色环境自 planner 起就带 HOH_GAME_ROUTE、开发者在 17:38:12 读到内容 61826/109308、收工时文件与进程都不在了。",
    "**到底是哪一个游戏进程回答了 Tester 仍是推断**：轮级游戏 61826/pid 109308（开发者 17:38 读到）与电池 play 的 65144/pid 109040（play_scene_ready.json，`editor_stop_scene` 记 `game_endpoint_invalidated` 65144/109040，meta.json 最终 game_endpoint 也是 65144）是两个进程；报告自评 ≈0.6 并标为推断——同意，且我的读数支持“两个进程”的划分，但无法从冻结件判定 Tester 命中哪一个，只能判定“命中了一个活着的游戏端点”。",
    "T10A-2 的证据损失是**碰运气幸存**的：被删段起始于 `HOH_MODEL_API_KEY=`，该点之后同一物理行的所有内容（本轮即环境转储尾部）都没了；若 `HOH_GAME_ROUTE` 排在键名之后，路由交付的唯一轮内原文就会被抹掉。下一次脱敏事故可能同时伤到判定与可审计性。",
    "F-T10-3（`evidence_diff` 全空而真实改了 7 个文件）我确认为真（result.json `evidence_diff={added:[],modified:[],removed:[]}`）⇒ DR-68 的 R7 现在可判“未实现”；本轮无人因此受损，但它意味着“增量检测”的另一条腿是哑的。",
    "预算脆弱（F-T10-4）：Developer 两次 attempt 都 LimitsExceeded，主增量来自 attempt#1，wrap-up 只补了 1 个文件；若 wrap-up 也没写，本轮会落进 NoEngineeringWrite。",
    "E3 的两个缺口现在有更强的证据形态（金币被物理扫过仍未拾取、Goal 在 x=6400 而玩家最多到 x≈449）⇒ 属**产物缺陷**，验收建议只诊断、不许手工替写（与 D277 决定 2 一致）。"
  ],
  "unverified": [
    "游戏路由文件 17:29:01 的 mtime、pid 109308 在该刻的存活：文件已删，仅存报告 §8.1 的轮中记录；代码结构（run_loop.rs:733 在 planner 之前；godot.rs:3882-3938 就绪后 publish）只能支持“结构上在第一个角色之前”，不是当轮测量。",
    "进程退出码 0（ROUND_EXIT）本身：见 T10A-4，冻结件里没有这一处。",
    "D276 第 10618 行“就地改写证据三次出问题”里 DR-69/DR-70 那两次的历史细节：属既往轮次，本轮未复核。",
    "E2/E4/E5/E6 我只做了点检（E2：电池 11/11 ok、两处 gate 一致、53 节点、编辑器错误仅 1 条信息性 banner；E4：14 条 path 存在 + 互斥 + candidate_id 绑定；E5：candidate/versions-ed98d1b8/活体工作区**逐字节同一**（运行时口径与我的口径都给 ed98d1b8…）；E6：qa_report `partial` + 每条 gap 带 player_impact），**不是完整的独立验收**——本任务书的重点是 E1/E3/端点/缺陷。",
    "被删掉的那段环境转储原文（无法恢复）；`set | findstr /i hoh` 的完整输出顺序。",
    "本轮七个脚本的改动**是否导致**了 E3 中成立的两类行为：我做了结构化作 diff（新增函数/@export），但没做行为归因（t8/t9 时代移动就已可用）。"
  ]
}
```

---

## 1. 逐条判据表（我自己的判定，不引用报告结论）

| ID | 判据 | 我的判定 | 决定性证据（我自己产出） |
|---|---|---|---|
| E1-1 | Developer 真的写了工程文件（`A_0≠A_1`） | **成立** | 我用**运行时自己的** hash 复现了两个目录名本身（1f3d20ed…/ed98d1b8…）；7 个 `scripts/*.gd` 被我独立 diff 出来（+3282 B，ADDED/REMOVED 空） |
| E1-2 | QA 产出**合法** `E_1` | **成立** | evidence.json 9 verified + 11 gap、交集空、14 条执行记录路径全部存在、type/claim_id/candidate_id 齐备 |
| E1-3 | 整轮跑完 + 退出码 | **成立（第三处见 T10A-4）** | `exit_code` 字节 `30 0A`；meta `exit_code:0`；result `ok:true/reason:ok`；battery 1 遍 11/11 |
| E1-4 | **全新空白工程**条款 | **不成立** | meta `start_state.mode=as_is`；prerun mario=17 文件/18397 B=A0；A0=t8 的 A1（经 t9 携带） |
| E1-5 | E1 的**证据形式**（轨迹 JSON） | **部分（3/4）** | tester 轨迹非法 JSON（两处坏点），另三条可解析 |
| Q2-1 | 角色 CLI 真机到达游戏端点 | **成立** | 27 条 running_game 调用带真实引擎载荷；0 次 `game_endpoint_unavailable` |
| Q2-2 | 路由“先有、末撤” | **成立（时点见 unverified）** | 开发者 17:38:12 读到 61826/109308（冻结在轨迹里）；收工文件不存在、无游戏进程 |
| Q2-3 | Developer 无裸 HTTP、无游戏通道调用 | **成立** | 命令里 running_game/http/socket/curl 全 0 |
| Q2-4 | Tester 证据形状一次过 | **成立** | 只有 attempt1、Submitted、artifact_valid=true、0 schema_failure/RepeatedFormatError |
| Q3-1 | 每帧数字与游戏常量自洽 | **成立** | 横向 3.6666614 px/帧 = speed220/60；纵向逐帧 +0.388885 = gravity1400/3600 |
| Q3-2 | 8 张 PNG + 4 次断言被引擎接受 | **成立** | 9 个 PNG 的 magic 亲验；4/4 `passed:true`，`resolved_node_path=/root/Main/Player`，无 POSITION_ASSERTION_UNAVAILABLE 回包 |
| Q3-3 | “金币未拾取 / 胜利未驱动”两条缺口 | **成立，且更强** | 全轮 91 处 `Coins: 0`、0 处非 0；`reached` 只有 false；右移/释放窗口物理扫过 Coin1/Coin2 仍不拾取；Goal x=6400 vs 玩家 max 448.67 |
| Q3-4 | 判 E3“部分”是否过度保守 | **否** | 四类里 2 类成立；可交互对象与胜利均有反向证据 |
| Q4-1 | 64 KiB 上限生效 | **成立**（数字见 T10A-3） | `65536 of 80800`、`65536 of 147809` + extra 三字段 |
| Q4-2 | 无超长回放 | **成立** | 全体最大 content 65,889 B / 最大序列化 156,999 B，无 MB 级 |
| Q4-3 | 无修复尝试 | **成立** | repair_retry_used=false、无 attempt3、无 launch_gate_repair、无 stale 电池目录 |
| Q4-4 | 门被评估且打开 | **成立** | meta 与 result 两处 `{applicable:true,launchable:true,reasons:[]}` |
| Q4-5 | 无过期日志关门 | **成立** | `count=1`、内容是信息性 MCP banner |
| Q4-6 | 无零增量信号 | **成立** | warnings.log 全文 2 行，无三形状关键字 |
| Q6-1 | 四条基线逐字节未变 | **成立** | 我自算四条全部命中历史值（含 `c144ef32…7a9c03`）；runs/ 下无晚于 18:23:08 的写入 |
| Q6-2 | PRD / 密钥 / 编辑器 / 引擎 / 孤儿 | **成立** | PRD sha 4c81c3a9…；明文密钥 0 命中；编辑器 75204（未重启）；嵌套仓 HEAD fc63af77/porcelain 0；仅 75204 一个 godot 进程 |
| Q6-3 | 三个假绿陷阱 | **成立** | ①空 pathspec → 空+exit0；②bash `rev^` 128 / `rev` 0，cmd 下 `^` 被吃 → 0 且 rev-parse 返回 fe129a1；③`ls-files godot-mcp`=6484 vs `godot-mcp/godot`=0，check-ignore 命中 `.gitignore:33:godot-mcp/godot/`、`:12:runs/`、`:11:.workspace/` |
| Q7 | D276（验收前写下）有无证据支持不了的句子 | **有一处**（见 §4） | `控制台 ROUND_EXIT=0` 这一处不在冻结件里 |

## 2. 我的独立抽取（原始响应 → 数字）

**E3 逐帧（来源 `iter-1/candidate/.hoh/deterministic/raw/input_replay.json`，48 次调用 = 39 running_game_* + 9 editor_*）**

| 窗口 | 样本 | 首 → 末 | Δ | 每帧 | 与游戏常量对照 |
|---|---|---|---|---|---|
| move_right | 60 | x 184.666702270508 → 400.999725341797 | +216.333023 | 216.333023/59 = 3.6666614 | ×60 = 219.9997 px/s ≈ `speed 220.0` |
| move_right_release | 10 | x 415.666351318359 → 448.666259765625 | +32.999908 | 3.6666565 | 同向复核 |
| jump | 30 | y 269.980834960938 → 214.258605957031(f17) → 242.59196472168 | 起升 55.722229 / 窗内回落 28.333359 | dy 递增 +0.388885/帧 | = `gravity 1400` × (1/60)² = 0.388889 |
| move_left | 60 | x 448.666259765625 → 232.333389282227 | −216.332870 | −3.6666588 | ×60 = −219.9995 px/s |

四条断言的期望值**逐条等于窗口首样本**（184.666702 / 415.666351 / 455.999573 / 448.666260），`passed:true` 4/4。

**树摘要（两套口径，都写明并自证）**
- **运行时口径**（`rel\n{len}\n{bytes}\n` 流，排除 `{.hoh,.git,.godot,.import}`，字节序）：`versions/1f3d20ed…` → `1f3d20ed50b472e422832c4fa2c8d7b72ae04ee11fa4c5ace65fb20a43997fd8`（= 目录名，17/18397）；`versions/ed98d1b8…` → `ed98d1b80be945c6d8e8a40fc3b5114dd9e1d33b1c29d576d050255a7fa1a1e1`（= 目录名，17/21679）；`iter-1/candidate` 与活体 `.workspace/mario` 都 = `ed98d1b8…`。
- **报告口径**（仓/tree 根相对**小写** POSIX 路径 + size + sha256，`\t`/`\n`，行序数排序，整体 sha256）：`5971b484…e463`（A0=planner-view）、`c781cf81…034a`（A1=candidate=活体）——逐字复现报告的四个值。
- **runs 基线口径**（PowerShell 5.1 `Get-ChildItem -Recurse -Force -File`，**仓根相对**小写路径 + 长度 + sha256，`\t` 连接、`\n` 分行、无尾随换行，行序 **`Sort-Object` = 文化排序**，整体 UTF-8 取 sha256）：t6 `135/c144ef32…7a9c03`（**自证命中**）、t7 `115/6e4c1595…20fb7`、t8 `358/6d11b2c6…bdf5a7`、t9 `83/541e2d81…36ca9d`、t10 `232/31955589…b38b8b`（newest 18:23:08）。**文化排序确属口径的一部分**：我把排序器换成 `StringComparer::Ordinal`，t8 变为 `c347bd63…b3d3f5`（与 T8/T9 验收记录的历史序数值逐字一致）；t6 两种排序同值（c144ef32…），所以“换成序数就不同”只在含分歧路径的树上成立。

## 3. 守卫与诚实性（我自己复现）

- 四条只读基线：摘要逐字命中 + `runs/` 全域**没有任何文件晚于 18:23:08**（唯一等于该时刻的 12 个条目就是本轮自己的最终写）。
- `PRD-mario.md` sha256 = `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`（未变）。
- 明文密钥：真值（长度 51）扫全仓 6465 文件（排除 `config/model.secret.env`）= **0 命中**；受控证据目录亦无密钥值。
- 引擎未改（**嵌套仓**，D242）：`git -C godot-mcp/godot rev-parse HEAD = fc63af77c33368c4a1bb839c95d19750554f63a3`、`status --porcelain -uall` **0 行**；外层 `ls-files godot-mcp = 6484`（真命中）对 `godot-mcp/godot = 0`（空判）。
- 进程：`9877` LISTENING 属 pid 75204（StartTime 2026/9/29 13:20:54，开机未重启），全机只有这一个 godot 进程 ⇒ **无孤儿游戏进程**；开工时（prerun_state.txt）也只有 75204。
- 三个假绿陷阱：见判据表 Q6-3（cmd 那次我亲测 `CMD_EXIT=0` 而 `git rev-parse fe129a1^` 返回 `fe129a1`——`^` 被吃掉，0 不携带证据力）。
- `-p` 目录：活体工作区/candidate/A1 均不存在，A0 快照与 planner-view 仍在 —— 与报告 §11.4 一致（清理者是本轮 Developer 的 `rmdir`，不是运行时）。
- `runs/smoke-t10` 是新目录：prerun `RUNS_T10_EXISTS=False`。

## 4. Q7 — D276（验收前写下的条目）逐句核对

- 事实性句子（A0/A1 摘要、7 脚本、9 verified+11 gap、Tester 一次过、`position:neq` 4/4、`Coins: 0`、`Goal.reached=false`、F-T10-1 根因、`-32602` 摩擦、回滚点、232 文件）**全部被我独立复现**。
- **唯一一处冻结证据支持不了的句子**：`D276` 第 10607 行「退出码 0 三方一致（**`exit_code` 字节 `30 0A`、`meta.json.exit_code=0`、控制台 `ROUND_EXIT=0`**）」的第三处。前两处我能从原始字节确认；`ROUND_EXIT=0` 只活在报告包装脚本 `run_round.ps1:14` 打到外层控制台的那一行里，而冻结入库的 `round/console.txt` 只有 hoh 自己的 stdout（13 行、无 `ROUND_EXIT`）⇒ **该句的第三个证据不在任何冻结件中**（成因是包装器的输出没有被一起留证，不是造假）。
- D276 的标题（“E1 首次 met”）**在其自身文本内有免责**：第 10623-10624 行明写本轮工作区不是全新空白工程、判据(1) 的 `hoh init` 一条仍未满足。所以不是“说了证据不支持的话”，而是“标题的语气强于正文的限定”；相比之下**被验收的报告连这句限定都没有**（T10A-1）。
- 另注：调度者在验收期间又落了 **D277**（`6f72e16`），它自我限定为“只记用户决定 + 完成消息事实转述”，并接受了“结论先于验收”的批评。我核对其第 4 条转述时发现 `任一轨迹最大消息 65,886 B` 的口径不精确（同 T10A-3），其余转述与我的读数一致。

## 5. 报告自述“局限”的裁定

1. **“某个文件的测量在调度者并发提交后变了”**：属实且记账正确。报告最后一次测量的 `DECISIONS.md` sha 是 `024fb22d…5ef0`（开工）→ `4db9c006…64b6`（D276 之后）；现在实际是 `ee28d746…7fb2`，因为**验收期间**又多了 `6f72e16`（D277，只改 `DECISIONS.md` +39 行）与 `0ed69cd`（新增 `TASK-DR72.md`）。`git show --pretty=format: --name-only` 证实 `87adbea`/`6f72e16` 只动 `DECISIONS.md`；报告三次修订（`1345a33`/`2638e6d`/`eadde3e`）只动报告与受控证据。**是否影响什么**：不影响任何 E1..E6 判据——`DECISIONS.md` 不是判据证据，且开工/收工两旁证都指向“该文件只由调度者的提交改变，不是本轮真机轮所为”。它只影响“报告中那一格的值是时点值”这一事实，而报告已显式披露。
2. **“`-p` 的清理者是 Developer 而不是运行时”**：我确认（活体/A1/candidate 无、A0 快照与 planner-view 有），且 `artifact_hygiene.suspicious_directories=[]` 的“看不出问题”确实因为候选树已被清 ⇒ 报告 §15 第 7 条的自我限定成立。
3. **“两个游戏进程的时序不强断言（≈0.6）”**：成立，见 risks。
4. **“未做行为归因（≈0.8）”**：成立；我只补了结构化作 diff（新增 `hurt_from_enemy`、`_process`、`reached` 与 8+6 个 `@export`），没有归因。

## 6. 我没有检查的

- Godot 未被启动、未联网、未调用模型（硬约束）⇒ 除冻结工件外，我没有复现任何**活体**行为。
- E2/E4/E5/E6 我只做点检（见 unverified），未做完整独立验收。
- `plan.md` 与 7 个脚本改动之间的“计划-实现”一致性、`prd_coverage` 的 9/17 口径、电池 11 步各自的脚本内部逻辑、`.hoh/scratch` 的残留物，我没有逐项复核。
- `runs/smoke-t6|t7|t8|t9` 的历史“期间未动”只能靠摘要与历史记录比对（`runs/**` 不入 git，没有可回放的历史）。

## 7. 给下一批的建议

1. **F-T10-1 必须按 TDD 修**（反例测试的输入就是一个含 JSON 转义换行的环境转储）：三种候选修法按优先级——(a) 终止符集补 `\`+`n`/`\`+`r`（即同时匹配转义换行），(b) 对 `.json` 走 parse-rewrite-serialize，(c) 改写后**先验证可解析**，不可解析就放弃改写并留旁注。同时把“**禁止就地改写被冻结或被轮次读取的证据**”落成可测规则（D276 已裁决，需要一条测试来兜住）。
2. **把进程退出码写进冻结件**（例如把 `ROUND_EXIT` 一并写进 `runs/<id>/` 或受控证据目录），让“三方一致”第三处不再依赖包装器控制台。
3. **全新空白工程轮**：用同一份冻结 `PRD-mario.md`、以 `fresh` 起点跑 `hoh init + hoh run`，并在验收里**硬性断言 `meta.json.start_state.mode == \"fresh\"`** 与 `A_0` 为“空工程基线”而非 t8 的产物；这条断言是 C1 的唯一可机检形态。
4. **修 `evidence_diff`（F-T10-3）**：现在真实有 7 文件增量而它仍为空 ⇒ DR-68 的 R7 应判 fail 一次并补实现（或明确降级声明为未实现，不再占着“已交付”）。
5. **报告模板加两条精度要求**：(i) “最大消息”必须说明是 content 还是整条序列化、是字符还是字节；(ii) 计数类结论必须说明口径（字符串出现次数 ≠ 引擎错误回包次数，E3 里“48 次调用”要区分下注入与读数）。
6. **E3 的两个缺口按产物缺陷诊断**：先查 coin.gd 的 Area2D `monitoring`/层掩码/`add_coin` 链路（我这份证据显示金币被物理扫过仍未拾取，比“没走到”更硬）、以及 Goal 的可达性（x=6400 vs 关卡实际可走范围）；**不要手工替它写游戏**（D277 决定 2）。
7. **预算**：Developer 两条 attempt 都 `LimitsExceeded`、主增量来自 attempt#1、wrap-up 只兜了 1 个文件 ⇒ 下一轮前值得复核步骤预算或 wrap-up 策略（离 `NoEngineeringWrite` 只差一个文件）。

---

### 验收者自述（诚实披露）

- 我**没有修改** `runs/**`（一个字节都没有，包括临时文件）、没有改 `.workspace/mario/**`、`PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`；未 stage、未 push。
- 我的全部临时脚本与输出都在**仓外** `C:\\Users\\wyl\\AppData\\Local\\Temp\\t10acc\\`。
- 我**没有启动或停止任何 Godot 进程**，没有触碰任何端口，没有联网，没有调用模型端点。
- 我**没有修复任何发现的问题**（含 T10A-2）；报告只做诊断与复现。
- 本文件写完后**不再修改**。
