# TASK-SMOKE-T11-ACCEPTANCE — 独立验收（机器可读结论在最前，已用 json.dumps 序列化并由 json.loads 回读）

```json
{
  "verdict": "pass",
  "task": "TASK-SMOKE-T11",
  "object": {
    "report": ".spec/hof-rs/tasks/TASK-SMOKE-T11-REPORT.md",
    "book": ".spec/hof-rs/tasks/TASK-SMOKE-T11.md",
    "round_dir": "runs/smoke-t11",
    "project_dir": ".workspace/fresh-t11",
    "head_at_measurement": "4558ba60ab88b607c36aecb58a3530654344584e",
    "head_now": "f7ef6b3d25f15cef94518730769c92061eb5fd05",
    "origin_master": "47eee038d2c2767821d80e687f6ef14e03c6ab0b"
  },
  "summary": "六条判据判定与四项首次真机读数我全部独立复现，未发现任何被判据覆盖不了的假绿：全新空工程条款成立（start_state=fresh、A₀=3ac25f6c 3 文件/1727 B、A₁=04d8ba5a 11 文件/8830 B，两套 hash 口径都由我自己实现复现）；编辑器确被重新指向新工程（177 工具契约里没有任何切换工程的工具 + project_list_scripts=0 + fresh-t11/.godot 缓存被写而 mario 的没有）；HUD 计数经属性工具读到、短额数值钉在判定行、三处退出码同数且都落盘、以及那处红的端点拒绝（死进程 33536）我逐条复现，并在源码层确认角色 CLI 只 adopt 路由、publish 只在 runtime 电池路径；两条新发现（窗口没驱动、先吃金币造成结构假阴性）我量化证实（180/180 样本同值、3 s 游戏时钟、576 黄像素只在 move_right-before）。六条基线摘要我用自己重写的口径复算到**现在**仍逐字节一致（含 c144ef32…7a9c03 自证），冻结文件/嵌套引擎/依赖/未推送全部合规，报告的机器可读 JSON 块我用 json.loads 亲验通过。缺陷都是报告层而非轮次层：F-T11-2 给的因果判据被同轮 input_channel_probe 反驳（原因仍未定）、两处'0 次'未标口径、两处派生分析工件错（distinct_x=60 / 非 UTF-8 判定行转写）、胜利类与 F14/F15 的措辞把'未观测'说成了'缺失'。重要界限：本 accept 只说明**这一轮的报告可信**，不说明目标完成——E3 仍 not_met（C3 未达成），且 E3 的两类失败是'未观测'而非'产品没有'。",
  "criteria": [
    {
      "id": "A1.fresh-empty-project-clause",
      "pass": true,
      "evidence": "冻结件自证：prerun_state.txt:48-49 RUNS_SMOKE_T11_EXISTS=False / WORKSPACE_FRESH_T11_EXISTS=False（23:48:20，且 43-45 行 9877 无监听、无 godot 进程）；fresh_init.txt:6-13 原始 ls 'total 0' + `find -mindepth 1 | wc -l`=0；init exit 0（fresh_init.txt:16-18），产出的 project.godot sha256=00d02c9c…c0ef4 —— 我用 sha256sum 对 A₀ 快照里的 project.godot 逐字复现同值，且 A₀ = 3 文件/1727 B（project.godot 1346 + scenes/main.tscn 342 + scripts/README.md 39）；init --fresh-workspace exit 0（fresh_init2.txt:3-5），purge 只动配置工作区（MARIO_SCRIPTS_COUNT 仍 15）；meta.json.start_state={'mode':'fresh','version_id':None}（该 mode 在 src/runtime/start_state.rs:24-25 的语义是'workspace 被清空且 initialize 重建 A₀'，且 :74-97 要求目录必须真实存在才允许 purge）。我用自己的两套 hash 口径独立复现：runtime 口径 A₀=3ac25f6c…（3/1727）、A₁=04d8ba5a…（11/8830），目录名与内容 hash 逐字相同；report 口径 ef369f27… / b33cf818… 也逐字复现；iter-1/candidate 与活体 .workspace/fresh-t11 均等于 A₁。差异全部落在工程文件（+8 个 scripts/*.gd[.uid]，scenes/main.tscn 342→4358 B，REMOVED 0），无一落在 .hoh/.git/.godot/.import。对照：.workspace/mario 的 A₀（t8/t10）=1f3d20ed… 17/18397 B ≠ 本轮 A₀ ⇒ 起点不是既有成品。注意（provenance）：fresh_init*/editor_* 等 txt 全部 mtime 00:34:23（postrun 00:29:34 之后），属复盘时落盘的转写；其关键数值由冻结件独立佐证（A₀ 的 project.godot sha、A₀ 快照内容、meta.start_state、退出码、基线摘要），故采信但已如此标注。"
    },
    {
      "id": "A2.engine-scoping-is-not-a-fake-round",
      "pass": true,
      "evidence": "契约面：godot/modules/mcp_server/docs/tools_list.renamed.json 共 177 工具，我扫全部 inputSchema —— 没有任何工具带 project location 类参数，也不存在 project_(open|close|load|switch)；editor_open_scene 只在当前工程内开场景，editor_get_open_scripts 只读。⇒ '没有任何工具能切换编辑器所开工程'成立（唯一理论旁路是 editor_execute_gdscript 这类代码执行，但它不构成受支持的项目切换；我未发现任何工具改 --path）。运行时的 godot.editor_scope 检查项也逐字承认 'the runtime cannot verify it'。事实面：LISTENER_PID 22876 的 cmdline 逐字含 `--path F:\\moonbit-hof-rs\\.workspace\\fresh-t11`，ExecutablePath 等于任务书钉的二进制；MCP project_list_scripts → {\"count\":0,\"scripts\":[]}（对照 .workspace/mario 的 scripts 有 15 条目）；我的独立磁盘检查：fresh-t11/.godot/editor/editor_layout.cfg mtime=2026-10-02 00:29:23，而 mario/.godot/editor/editor_layout.cfg 仍是 2026-09-30 18:23:08，且 mario 整树（178 文件、含 .godot 缓存）摘要与开工前逐字节相同 ⇒ 本轮编辑器从未打开 mario。假轮另一半也被排除：游戏端点里的场景树是 fresh-t11 那个 31 节点场景（Coin1..Coin5 在 400/1200/2500/4200/5600、Goal 6600、HUD 四 Label），与 fresh-t11/scenes/main.tscn 一致，不是 mario 的场景。限制：我离线、不查活体端点，以上依赖冻结件 + 磁盘缓存 mtime。"
    },
    {
      "id": "A3.invivo-1-coin-counter-via-property-tool",
      "pass": true,
      "evidence": "raw/interaction_evidence.json call[0]：tool=running_game_get_node_properties，args={\"node_path\":\"/root/Main/HUD/Coins\",\"properties\":[\"text\"]}，payload={\"node_path\":\"/root/Main/HUD/Coins\",\"properties\":{\"text\":\"Coins: 1\"},\"type\":\"Label\"}（我逐字解出）。'旧不可读路径'确已消失：同一轮的 running_game_get_scene_tree 31 个节点只有 name/path/type(+script)，我实测没有任何节点带 text 字段 —— 正是 DR-76 修的'真引擎只发 name/path/type'形状，而计数仍被读到。COIN_COUNTER_UNREADABLE 在全部 .hoh/deterministic/** 里 0 次。"
    },
    {
      "id": "A4.invivo-2-shortfall-and-verdict-classes",
      "pass": true,
      "evidence": "判定行（record-08.json，合法 UTF-8，含真实 U+2014 em dash）里同时出现：`WIN_BLOCKED_UNDER_MOVE_RIGHT (…player max x=Some(225.000045776367), goal.position=Some(Object {\"x\": Number(6600.0),…}), coverage_shortfall_px=Some(6374.999954223633) — the bound is the level or the game logic…the window only holds `move_right` and never jumps…)`；我自己验算 6600.0 − 225.000045776367 = 6374.999954223633。battery.json/deterministic.json/deterministic.log/record-08.json 里 coverage_shortfall_px 共 8 处（驱动行与判定行同值），旧名 WIN_UNREACHABLE_GEOMETRICALLY 0 处，WIN_UNREACHED_WITHIN_BUDGET 0 处 ⇒ 两类结论本轮只走到'仅 move_right 下被阻'一类。口径限定：'0 次'只对**生产发出的判定 token**成立；旧名与新名作为散文仍出现在 EVIDENCE_PLAYBOOK.md、skills/godot-dev.md 与三条轨迹里（见缺陷 T11A-2）。"
    },
    {
      "id": "A5.invivo-3-three-exit-code-readings",
      "pass": true,
      "evidence": "我亲测字节：runs/smoke-t11/exit_code = 30 0a，runs/smoke-t11/process_exit_code = 30 0a，meta.json.exit_code = 0；mtime 次序 result.json 00:29:22.569 < exit_code .6289 < process_exit_code/meta.json .6305；三处都是落盘工件；另一处（wrapper ROUND_EXIT=0）落在本轮自建 evidence/round/wrapper.txt:3，属非冻结转写，报告已如实区分。报告 M3 的'三处同数且都落盘'成立。"
    },
    {
      "id": "A6.invivo-4-red-endpoint-refusal-reproduced",
      "pass": true,
      "evidence": "我从 tester.attempt1.json 自行配对 command→tool result：9 次 `hoh tools call`（editor_play_scene 3 / editor_get_scene_tree 2 / editor_stop_scene 1 / running_game_get_node_properties 3），3 次 running_game_* 全部被拒，回包逐字含 'the game process the record names is not running (pid 33536), so the route belongs to an earlier round … Falling back to the editor endpoint is not allowed (DR-43)'。死进程事实：同时刻 tasklist 只有 22876 与 4508，没有 33536。路由陈旧的决定性一帧：00:18:09 的 editor_play_scene 回包是 pid 4784/port 57902，**同一条命令随后 `type runs\\smoke-t11\\game_endpoint.json` 仍打印 pid 33536/port 56821**；路由文件 mtime 00:07、92 B。设计面：拒绝是 by design —— RouteRefusal::OwnerGone（src/tools/endpoint.rs:182-185 就是那句文案）+ DR-43 不静默回退（mod.rs:485-506）。缺陷面我读到源码确证：src/cli_impl.rs:54-58 的角色侧 CLI **只 adopt** 发布的路由，publish 只发生在 runtime 的电池路径（src/adapter/godot.rs:984，且必须先过 readiness 轮询）⇒ 角色自己 play_scene 天然不会刷新 runs/<id>/game_endpoint.json。报告 M4 红色判定成立，且归因正确。"
    },
    {
      "id": "A7.new-finding-no-drive-observation",
      "pass": true,
      "evidence": "我逐样本重算：interaction_evidence 三条 batch 各 60 帧，合计 180 样本，x 唯一值数=1（每批 unique_x=1），x=225.000045776367、y=303.925262451172 恒定；同轮 input_replay 四个窗口分别 192.000045776367→408.333038330078（60 个不同 x）、426.666320800781→459.666229248047、jump x 恒 466.999542236328 而 y 283.590729→234.257355→267.479584、455.999542236328→239.666732788086（60 个不同 x）。调用面：interaction 窗口 0 次 editor_simulate_input_action，input_replay 8 次；interaction 每批只有 create/play_input_recording + run_test_scenario + stop_input_recording，录音只有 2 个 pressed=true 事件、时长 39-53 ms、无 release。我的独立反证（很重要）：input_channel_probe.json 同样 0 次 editor_simulate_input_action，却用同一套 recording 注入把 Player 从 67.3333358764648 推了 30 帧（gdscript 只读探针读到 173.666687011719）⇒ 报告给的那个判据不成立（见缺陷 T11A-1）。我又做了停止/暂停排除：replay-interaction-before 的 HUD 是 `Coins: 1/Lives: 3/Time: 3`，after 是 `Time: 6`（其余像素仅 365 个差异、玩家块不动）⇒ 采样期间游戏跑了约 180 帧（3 s），玩家却 0 位移，排除了'冻结/暂停采样'，坐实'没有保持住的输入'。"
    },
    {
      "id": "A8.new-finding-structural-false-negative",
      "pass": true,
      "evidence": "顺序：battery.json 是有序列表，input_replay 在 index 7、interaction_evidence 在 index 8（先回放后交互）。几何：main.tscn Coin1 position=Vector2(400,304)，Player y=303.925，spawn x=60 ⇒ move_right 窗口 x 192→408 必然扫过 Coin1。像素：我用 PIL 独立数黄色像素（ColorRect 24×24=576）—— 只有 replay-move_right-before.png 有 576 个，其余 10 张（含 replay-move_right-after.png 与 interaction before/after）全 0 ⇒ 那枚金币是在 input_replay 的 move_right 窗口内消失的。代码：main.gd:4 `@export var coins: int = 0`、:14-16 _ready 即写 'Coins: 0'，唯一增量点是 coin.gd:17-24 collect()→add_coin(1)+queue_free()。读数：interaction 窗口 before 读数 coin=Some(\"Coins: 1\")，全程 1→1，引擎自己的 text:neq \"Coins: 1\" 断言 passed=false。⇒ 0→1 在这个窗口已不可能被观测。口径细化：电池那一步的断言是'与窗口起始读数不同的动态 neq'（expected 就是当场读到的 \"Coins: 1\"），所以 1→2 仍能满足**该步**；被结构上堵死的是 F10 的 claim 原文（evidence.json F10: 'increments the HUD coin counter by exactly one'，player_impact: 'the 0 -> 1 transition … was never observed'）。"
    },
    {
      "id": "A9.six-verdicts-and-undecidable",
      "pass": true,
      "evidence": "六条判定我都用本轮原始件复核：E1 met（四要件：planner.attempt1.log exit_status=Submitted/artifact_valid=true/28 calls；developer artifact_valid=true 且 A₀≠A₁ 真实增量；tester Submitted + evidence.json 合法；exit 0 四处一致）；E2 met（editor_errors_baseline count=0/errors=[]；play_scene_ready playing=true pid 31528 port 56727；场景树 31 节点；editor_stop_scene stopped=true；artifact_gate 在 meta.json 与 result.json 两处都是 applicable=true/launchable=true/reasons=[]）；E3 not_met（4 类里 2 类：左右/跳跃成立，可交互对象/终点胜负不成立）；E4 met（我自查：7 verified/14 gap、18 条执行记录全部在冻结候选里存在 MISSING=[]、type 五类齐全、candidate_id 全绑 04d8ba5a…、verified∩gap=∅ 无重复、14 条 gap 全带 player_impact、handoff 4/5/6）；E5 met（我用与运行时同口径的 hash 复现三棵树同为 04d8ba5a…/11 文件/8830 B）；E6 met（qa_report.md 明写 partial 7+14 并逐条列未达，且主动拒绝过度声明）。unjudgeable=[] 无误：六条都有本轮原始证据；E3 的两类失败判 not_met 而非 unjudgeable 是合理的（判据要的是**被观测到的**行为，而所需观测在本轮不存在），但报告没有把'未观测到'说成'产品没有'（见 A10/A11）。"
    },
    {
      "id": "A10.gaps-not-glossed-and-no-borrowed-evidence",
      "pass": true,
      "evidence": "可交互对象与胜负两类都被写成 gap/不成立：qa_report.md 'What remains open' 段 + F10 player_impact'0->1 从未观测' + F13/F14/F15 gap；报告 §2.3 还主动给出反向澄清（'Coins: 1 意味着确实吃到过一枚金币'，排除'完全不能拾取'的误读），没有粉饰。借用他人证据：我逐条核对报告引用的数值（31 节点、225.000045776367、6374.999954223633、576 黄像素、31/11 文件数、退出码字节）全部可在 runs/smoke-t11/** 与我本节自算里复现；报告对 t10 的引用只有一处（:200，hash 口径自证 1f3d20ed…/ed98d1b8…），而那两个值我也独立复现（t10/versions 两个目录名）。⇒ 没有把别轮读数当本轮证据。"
    },
    {
      "id": "A11.six-read-only-baselines-byte-identical",
      "pass": true,
      "evidence": "我自己按声明口径重写 PowerShell 摘要（仓根相对小写 POSIX 路径 + TAB + 字节长 + TAB + sha256、LF 行、无尾随换行、行序 Sort-Object 文化序，UTF-8 整块 sha256），**在收工后现在**跑出：.workspace\\mario 178 dee0a36f357c440d078c652d4d4b8990af1a63b88d282c1e36c04a16d006cc94 newest 2026-09-30 18:23:08；runs\\smoke-t6 135 c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03 newest 2026-09-29 02:32:01（任务书要求的自证值命中）；t7 115 6e4c1595…20fb7；t8 358 6d11b2c6…bdf5a7；t9 83 541e2d81…36ca9d；t10 232 31955589…b38b8b —— 六条与 baseline_before/after 完全一致，且 before==after 逐字相同。⇒ 不只轮内未变，**到现在仍未变**。排序口径要紧：同一实现换成 ordinal 序后 mario→f622f5b0…、t8→c347bd63…、t10→9ba72fbd…（t6/t7/t9 不变）⇒ 文化序是承重的，用 Python `sorted()`（码点序）复算会'误判'三条基线（见 §3 的坑 P1）。"
    },
    {
      "id": "A12.frozen-files-engine-deps-and-push",
      "pass": true,
      "evidence": "冻结：PRD-mario.md sha256=4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a（= meta.json.spec.sha256）、DECISIONS.md=5ca40958f6563223c3f1a223670b59478d272ed610e15f3da34f81276e868b2a（开工=收工=现在），git status --porcelain -uall 只有开工前就存在的未跟踪 TASK-DR77-ACCEPTANCE.md，TASK-SMOKE-T11.md / REQUIREMENTS.md 无改动。引擎：嵌套仓 git -C godot-mcp/godot rev-parse HEAD=fc63af77…，status --porcelain -uall = 0 行。依赖：git diff 4558ba6..HEAD -- Cargo.toml Cargo.lock = 0 行 ⇒ 无新依赖；round 的唯一提交 f7ef6b3 只新增本报告 871 行。推送：origin/master=47eee038…，HEAD ahead 10，stash 0、tag 0 ⇒ 未 push（闸门武装且未尝试）。"
    },
    {
      "id": "A13.empty-dir-removal-touched-no-baseline",
      "pass": true,
      "evidence": "披露的三处空目录都建在 runs/smoke-t11/evidence/{scripts,round,analysis} 下，用 rmdir（只能删空目录、不能删文件）回收；runs/smoke-t11 不是六条只读基线之一（基线=mario 与 t6..t10）；prerun_state.txt:48 记录 RUNS_SMOKE_T11_EXISTS=False（run 前确不存在）；六条基线摘要到 00:29:42 与我现在复算都逐字不变；git status 无删除 ⇒ 没有基线被这次误建/误删碰到。我没能验证它当时确实用了 rmdir 而非别的命令（只能验证结果），但结果面无损害，故 pass。"
    },
    {
      "id": "A14.release-binary-rebuilt-from-current-head",
      "pass": true,
      "evidence": "prerun_state.txt:26-29 记录开工时 target/release/hoh.exe SIZE=12572672 SHA256=ada84958…、mtime 2026-09-30 17:28；现在实测 SIZE=12692992 SHA256=d0292a06b19c6dc4ab00bb916ad642ee077161d59882109c44ab986b7a6b4b40、mtime 2026-10-01 23:49:06（= 报告 §1.5 重建值），且 23:49:06 < 轮启动 23:50:37 ⇒ 跑的是新二进制。我进一步用二进制内容钉住'来自含 DR-77 改名的 HEAD 源码'：`grep -c WIN_BLOCKED_UNDER_MOVE_RIGHT target/release/hoh.exe`=5、WIN_UNREACHED_WITHIN_BUDGET=3 ⇒ 不可能来自 09-30 的旧二进制。（没有重新 cargo build，见 §5 未检查项。）"
    },
    {
      "id": "A15.report-json-block-actually-valid",
      "pass": true,
      "evidence": "我写了自己的栅栏感知解析：TASK-SMOKE-T11-REPORT.md 里 info string 为 json 的栅栏恰 1 个（其余 25 个为 ''/text），对该块 json.loads 通过，17 个顶层键（task/round_id/round_dir/project_dir/engine/start_state/fresh_project_evidence/round/product_identity/verdicts/unjudgeable/criteria/mechanism_readings/defects/risks/unverified/honest_disclosure）；块内 criteria 22 条、18 pass / 4 fail（E3.at-least-one-interactive-object、E3.goal-or-win-condition、M2.shortfall-on-verdict-line-and-two-class-split、M4.character-cli-reaches-game-endpoint），与正文表格一致。本轮自带的 analysis/json_block_validation.txt 结论同为 PASS；'最近一次验收声称验过而块非法'的问题没有复发。"
    },
    {
      "id": "A16.report-unverified-list-adjudicated",
      "pass": true,
      "evidence": "报告 5 条 unverified 我逐条评估：①pid 75204 谁关的 —— 只有本轮自述，无法独立证（我保留为未验证）；②WIN_UNREACHED_WITHIN_BUDGET 真机 —— 我实测 deterministic/** 0 次，属实；③64 KiB 真机 —— 我实测四条轨迹 hoh_output_truncated=0、最大 tool content 45,486 B（tester）、最大整条消息 102,475 B，属实；④56821/33536 的发布者 —— 我实测这两个数**只**出现在 tester 轨迹与本轮派生分析里，battery raw、meta.json、result.json 全无 ⇒ 报告说'未确定'是诚实的；⑤Developer RepeatedFormatError 被容忍是否有意 —— 我实测 artifact_valid=true、attempt 只 1 次、schema_failure=0，源码级是否刻意我没读，保留。⇒ 该列表不是敷衍，且我未发现它漏报的、我这边能判定的未验证项。"
    },
    {
      "id": "A17.report-internally-consistent-counts",
      "pass": true,
      "evidence": "我复算文件数：运行时自己的轮记录 = 顶层 5 + versions 15 + iter-1 104 = **124**，本轮自建 evidence/** = 62，合计 **186**，与报告 '124（newest 00:29:22）/ 186（00:37:24 实测）'一致；evidence/** 全部 mtime≥00:34:23 ⇒ 00:29:34 的整树计数 124 就等于运行时记录，报告的时点说明成立。其余数字我也复算：plan.md 2879 B、evidence.json 24822 B、qa_report.md 3769 B、developer/tester 轨迹 1084125/1084030/941987 B、battery 12 步 11 ok、'No tool calls found' planner 2/developer 9/tester 9。"
    }
  ],
  "defects": [
    {
      "id": "T11A-1",
      "severity": "minor",
      "what": "报告 F-T11-2 的**因果判据**站不住：它把'该窗口 0 次 editor_simulate_input_action，而 input_replay 有 8 次'当成'驱动没生效'的解释，但同一轮更早的 input_channel_probe.json 也是 0 次 editor_simulate_input_action，却用同一套 recording 注入把玩家从 x=67.3333358764648 推了 30 帧（只读 gdscript 探针读到 173.666687011719）。'窗口确实没推进'这一观测我完全证实（180 样本逐位相同、时钟走了 3 s、input_replay 同候选上位移 216.33 px），但**原因在本轮冻结证据里不可判定**；按报告给的判据去修，可能白修。（报告自己在 risks 里写了 ≈0.75 的推断，但缺陷段与证据行仍把该判据写成解释。）",
      "reproduction": "python -c \"import json;d=json.load(open(r'runs/smoke-t11/iter-1/candidate/.hoh/deterministic/raw/input_channel_probe.json',encoding='utf-8'));[print(c['tool'],c.get('label'),str(c.get('payload'))[:200]) for c in d['calls']]\"  对照 raw/interaction_evidence.json 的 call 清单与三批 get_node_property_samples。"
    },
    {
      "id": "T11A-2",
      "severity": "minor",
      "what": "报告里两处 '0 次' 的口径未加限定：COIN_COUNTER_UNREADABLE 与 WIN_UNREACHABLE_GEOMETRICALLY 在**生产发出的判定**上确为 0，但全轮 grep 分别命中 6 处 / 11 处（EVIDENCE_PLAYBOOK.md、skills/godot-dev.md 把它们作为历史名明确写出、三条轨迹因嵌入这些文档而带上）。按字面读'全轮 0 次'是错的，按'判定行没有发出旧 token'读才对——报告应把口径写在句子里。",
      "reproduction": "grep -rl COIN_COUNTER_UNREADABLE runs/smoke-t11 ; grep -rl WIN_UNREACHABLE_GEOMETRICALLY runs/smoke-t11 ; grep -rho 'WIN_UNREACHABLE_GEOMETRICALLY' runs/smoke-t11 | wc -l"
    },
    {
      "id": "T11A-3",
      "severity": "minor",
      "what": "两处**派生分析工件**与它们要支撑的结论不符：(1) evidence/analysis/interaction_detail.txt 对三段交互采样写 `distinct_x=60`、`x series head: [None, None, …]`，与报告的（正确的）'3×60 帧逐位相同'直接矛盾——这是我的独立复算否掉的；(2) evidence/analysis/interaction_verdict_line.txt **不是合法 UTF-8**（偏移 1480 处一个裸 0xA1，本应是 U+2014 em dash），因此无法从它做逐字引用；真正的判定行原文在 record-08.json 里是合法 UTF-8 且含真 em dash。两者都不影响判定，但派生工件反过来误导读者，且与 §8「实测」的措辞冲突。",
      "reproduction": "python -c \"d=open(r'runs/smoke-t11/evidence/analysis/interaction_verdict_line.txt','rb').read();d.decode('utf-8')\"（抛 UnicodeDecodeError: byte 0xa1 at 1480）；python -c \"import json;d=json.load(open(r'runs/smoke-t11/iter-1/candidate/.hoh/deterministic/raw/interaction_evidence.json',encoding='utf-8'));[print(c['label'],len(set(s['position']['x'] for s in json.loads(c['payload']['content'][0]['text'])['samples']))) for c in d['calls'] if c['tool']=='running_game_get_node_property_samples']\""
    },
    {
      "id": "T11A-4",
      "severity": "info",
      "what": "两处措辞把'未观测'与'产品缺失'混在一起：(a) 报告 §2.3 用'轨迹树里没有敌人/方块/死亡平面 ⇒ F13/F14/F15 全 gap'把**胜利类 F13** 和缺失物体类并列，而 F13 的 gap 原因是'胜利从未被驱动'（QA 自己写得更准）；(b) 它转述的 QA 判词'these behaviours are absent rather than merely unobserved'对 F14/F15 不准确：player.gd:32-40 确实有 y>1000 的 respawn→lose_life 路径（win 也有 goal.gd:11-18 实现），只是这一关没有坑/边缘可触发。对 E6 判定无影响（gap 判定本身对，且未达成被如实声明），但下一批若按这句去重写会重复造轮子。",
      "reproduction": "read runs/smoke-t11/iter-1/candidate/scripts/player.gd (32-40) 与 goal.gd (11-18)；grep -n 'lose_life\\|func win' runs/smoke-t11/iter-1/candidate/scripts/*.gd"
    },
    {
      "id": "T11A-5",
      "severity": "info",
      "what": "报告未提的一处状态不连续：input_replay 最后一个窗口末样本 x=239.666732788086，而紧随其后的 interaction 窗口首样本是 x=225.000045776367（差 14.666687 ≈ 4 帧左移；y 也从 303.925262451172 变成同一值但前一窗口是 303.925201416016 量级的微小差异）。这不推翻'窗口内 180 帧不动'，但它说明交互窗口的初始状态并非'上一窗口结束时的状态'，F-T11-2 若要追因，必须解释这 4 帧——报告把它当成延续叙述了。",
      "reproduction": "对比 raw/input_replay.json 中最后一枚 running_game_get_node_property_samples 的末样本与 raw/interaction_evidence.json 首批首样本。"
    }
  ],
  "risks": [
    "交互窗口（interaction_evidence）不推进的原因仍未定位，且报告给的解释被同轮证据反驳；若下一轮原样再跑，E3 的'可交互对象/胜负'两类会再次结构性地观测不到。",
    "input_replay 先于 interaction_evidence（battery 第 7 步 vs 第 9 步）会先吃掉最近的一枚金币，使 F10 的 0→1 claim 在任何同类候选上都不可观测；这是**证据形态**的假阴性，与'产品不会拾取'必须分开处理。",
    "F-T11-1（角色自己 play_scene 不刷新发布路由）会让任何'自己开场景再读数'的角色永久拿到 game_endpoint_unavailable；不修则应明确告诉角色不要自己 play_scene。",
    "E3 已知成立的两类（左右、跳跃）依赖 editor_simulate_input_action 的编辑器侧注入 + 游戏侧读数；若该注入通道失效，位移证据会一起消失（报告已列，我重申）。",
    "本轮收工时编辑器 22876 存活（postrun_state.txt:73-77），但**我现在实测已无任何 godot 进程、9877 无监听** ⇒ G3 只是'轮末快照'为真，不是长期不变量；下一真机轮必须重新走 §2.1 引导。",
    "本轮自建 evidence/*.txt 全部是 00:34-00:38 的复盘转写，不是轮内实时落盘；其数值靠冻结件互证（我已对关键值做过），但'原始输出'这一措辞比实际强。"
  ],
  "unverified": [
    "编辑器 pid 75204 在开工前是否真的存在、由谁关闭：只有本轮自述（prerun_state.txt），无外部证据。",
    "路由值 56821/pid 33536 的发布者：该值在 battery raw、meta.json、result.json 中均不存在，只出现在 Tester 的现场读取与派生文件里，故无法从冻结件定位写入路径（与报告第 4 条未验证项一致）。",
    "Tester 第二次 play_scene 起的游戏（pid 4784 / port 57902, 00:18:09）是否在轮末仍存活：Tester 轨迹里唯一的 editor_stop_scene 发生在 00:17:06（停的是 4508），4784 没有配对的 stop；只有 00:29:34 的终态快照显示它已不在。",
    "交互窗口零推进的端到端机制（我无法离线复现），以及 input_channel_probe 与 interaction_evidence 同一注入形状行为不同的原因。",
    "WIN_UNREACHED_WITHIN_BUDGET 与 64 KiB 截断路径的真机行为（本轮都未触发）——与报告一致。",
    "报告 §2.1 的'行读数'（INTERACTION_MAX_BATCHES=130 等常量）我未读 src/runtime 的相应源码，只从判定行文本核到 130 与 127 未花。",
    "密钥卫生：我只做了模式化检查（HOH_MODEL_API_KEY= 后紧跟 \\nHOH_ROLE= 即为空值；全轮无 'sk-' 类命中），未做熵扫描，也未读出密钥真值比对。",
    "本轮 evidence/scripts/*.py 的正确性（我只重实现了我用到的口径：tree hash、两套基线摘要逻辑）。"
  ]
}
```

---

# TASK-SMOKE-T11-ACCEPTANCE — 真机轮（全新空工程）的**独立验收**（全新验收子代理，无实现者/调度者上下文）

> 验收人：**独立验收子代理**（与实现者、调度者不同一批；不继承任何结论；未委派、未使用子代理；工作单独完成）。
> 被验对象：`TASK-SMOKE-T11.md`（任务书，含 §2.1 强制引导）、`TASK-SMOKE-T11-REPORT.md`（**只作线索**）、
> `.spec/hof-rs/REQUIREMENTS.md` E1..E6 原文、`.spec/hof-rs/OBJECTIVE-COMPLETION.md` C1..C5、`DECISIONS.md` **D276/D278/D289/D290**。
> **离线**：未启动引擎、未跑轮、未调用 MCP/模型端点、未联网。**`runs/**` 零写入**（我全部脚本只读 `runs/**`，没有在 `runs/**` 下建过任何文件，
> 含"写过再删"）；临时脚本与产物全在**仓外** `F:\t11-accept\`。**未对任何路径用 `rm -rf`**；**未从未展开变量构造路径**；
> 未改 `.workspace/fresh-t11/**`、`.workspace/mario/**`、冻结规格、`DECISIONS.md`、`godot-mcp/**`；未 push、未 stage。
> 我自己的关键口径实现（runtime/report 两套树 hash、两套基线摘要、栅栏感知 JSON 解析）都是**重写**的，不调用被验方的脚本。

## 1. 我为什么判 `pass`（以及它**不**意味着什么）

判 pass 的依据是"报告的每一条实质声明都能被我从冻结件复现，或已被报告自己正确降级为未验证"，而不是"数字看着对"：

1. **头号条款（全新空工程）真的落实了**，且不是靠转写：`meta.json.start_state.mode="fresh"` 的语义（`src/runtime/start_state.rs:24-25`）
   就是"workspace 被清空 + initialize 重建 A₀"，加上 A₀ 快照本身 = 3 文件/1727 B 的空脚手架、其 `project.godot` sha 与我实测一致。
2. **引擎作用域**不是假轮：契约里确实没有切换工程的工具，而新工程与 mario 的编辑器缓存 mtime 分叉（fresh-t11 被写到 00:29:23，mario 停在 09-30 18:23:08）。
3. **四项首次真机读数**三项绿一项红我全部复现；红的那项（角色 CLI 端点拒绝）我还读到源码确认了缺陷位置。
4. **两条新发现**都量化成立（3×60 逐位相同 vs 同候选 216.33 px；唯一 576 黄像素帧出现在 move_right-before）。
5. **六条基线与全部守卫**现在重算仍逐字节一致；JSON 块"这次真能解析"。
6. 报告的自曝与未验证列表**诚实且可核对**，我没有找到它把"未观测"谎报成"verified"的地方。

**它不意味着**：目标完成。E3 = not_met 依旧（C3 未达成），E3 的两类失败是**未观测**；E1 的空工程条款这次满足，但 C1 的"可运行/可玩到的产出"仍需 E3。（C1 的freshness子条件 = 已闭环。）

## 2. 逐项核验表（对应派单的六项工作）

| # | 工作项 | 我的结论 | 决定性证据（全部我自己产出/复算） |
|---|---|---|---|
| 1 | 全新空工程条款（头条） | **成立**，T10A-1 的限定不再适用 | `WORKSPACE_FRESH_T11_EXISTS=False`（00:48:20 前不存在）+ `ls total 0`/`find=0` + init exit 0 + `start_state={mode:fresh}` + A₀=3ac25f6c(3/1727)、A₁=04d8ba5a(11/8830) 由我自己的 hash 实现复现；+8 脚本 / main.tscn 342→4358 / REMOVED 0，全在工程路径 |
| 2 | 引擎作用域（假轮陷阱） | **claim 成立**；编辑器确开新工程 | 177 工具无工程切换器、无 project location 参数；cmdline `--path …fresh-t11`；`project_list_scripts` count=0（mario 15）；fresh-t11/.godot/editor/editor_layout.cfg 00:29:23 vs mario 09-30 18:23:08 且 mario 整树摘要未变 |
| 3a | 计数经属性工具读到 | **绿** | call[0] `running_game_get_node_properties{node_path:/root/Main/HUD/Coins,properties:[text]}` → `text="Coins: 1"`；31 节点无 `text` 字段；判定件里 COIN_COUNTER_UNREADABLE=0 |
| 3b | 短额在判定行 + 两类只走一类 | **半绿，如报告所述** | record-08.json 判定行含 `coverage_shortfall_px=Some(6374.999954223633)`（我验算 6600−225.000045776367）与新名；旧名/WIN_UNREACHED_WITHIN_BUDGET 在判定件 0 次 |
| 3c | 三处退出码同数且落盘 | **绿** | `exit_code`=30 0a、`process_exit_code`=30 0a、`meta.exit_code`=0；mtime 次序 result<exit_code<process/meta；wrapper.txt ROUND_EXIT=0 属非冻结转写 |
| 3d | 角色 CLI 端点的红 | **复现，且源码级确证** | 3 次拒绝（死 pid 33536）；`type game_endpoint.json` 在 play_scene(4784) 之后仍显示 33536；tasklist 无 33536；`RouteRefusal::OwnerGone`+DR-43；`cli_impl.rs:54-58` 只 adopt、`godot.rs:984` 才 publish |
| 4a | 交互窗口可能没驱动 | **观测成立，报告给的原因不成立** | 180 样本 unique_x=1（x=225.000045776367）；input_replay 四窗口 60/10/30/60 帧位移 +216.33/+33.00/竖直弧/−216.33；我的反例：input_channel_probe 0 次 simulate 仍把玩家推了 30 帧 |
| 4b | 结构假阴性（先吃金币） | **成立** | Coin1(400,304)、player y=303.925 ⇒ move_right(192→408) 扫过；黄像素 576 只在 move_right-before，其余 10 帧 0；interaction 首读数已 `Coins: 1`，而 main.gd 初值 0 且唯一增量点是 coin.gd::collect |
| 5 | 六条判定 / 不可判定 / 借用证据 | **全部与证据一致** | 六条 raw 逐条复核（见 A9）；`unjudgeable=[]` 无误；报告对 t10 的引用只有 hash 口径自证一处，且我独立复现 |
| 6 | 守卫、闸门、卫生 | **全绿（除报告层小瑕）** | 六基线摘要我用自写口径复算到"现在"仍逐字一致（含 c144ef32…）；PRD/DECISIONS sha 不变；嵌套仓 clean；Cargo 零改动；ahead 10 未推；JSON 块 json.loads 通过；三空目录 rmdir 不碰基线；二进制 23:49:06 重建且含 DR-77 token |

## 3. 我自产的植入与反例（用来**打红**报告的说法，而不是复述它）

- **P1 摘要排序坑（我踩到并查清）**：我自己用 Python 默认 `sorted()`（码点序）重算六条基线时，mario→`f622f5b0…`、t8→`c347bd63…`、t10→`9ba72fbd…`，看起来三条"被改过"。
  换回声明口径（PowerShell `Sort-Object` 文化序）后六条**逐字命中**。⇒ 文化序是承重的；报告写的"文化排序属口径"是对的，任何验收若用 Python 原生排序会把三条基线误判为被动过。
- **P2 "0 次"范围坑**：全轮 grep `WIN_UNREACHABLE_GEOMETRICALLY` 命中 11 处、`COIN_COUNTER_UNREADABLE` 命中 6 处（playbook/skill 的历史说明 + 嵌入它们的三条轨迹）。
  但**判定件**（battery/records/deterministic）里确为 0。⇒ 报告结论对，措辞缺限定（T11A-2）。
- **P3 F-T11-2 因果反例**：`input_channel_probe.json`（第 7 步）0 次 `editor_simulate_input_action`，靠 recording 注入把 x 67.333→173.667（30 帧）。
  ⇒ "缺 simulate 调用"不能解释第 9 步的不推进（T11A-1）。
- **P4 暂停/冻结排除**：interaction before→after 的 HUD 从 `Time: 3` 变 `Time: 6`，玩家块与金币计数不动（仅 365 像素差）。
  ⇒ 采样期游戏确实跑了 ~180 帧，"没推进"不是暂停或采样不前进造成的。
- **P5 金币归属**：我按 ColorRect 颜色 (1,0.85,0.1)、24×24 计黄像素 = 576，只出现在 `replay-move_right-before.png`；`replay-move_right-after.png` 与 interaction 前后帧均为 0。
  ⇒ 那枚金币是在**回放**窗口内被吃掉的，报告的 F-T11-3 成立。
- **P6 文件数坑**：用 `find … -not -path "*/evidence/*"` 数"运行时记录"会得到 113（因为它顺带排除了运行时自己的 `candidate/.hoh/evidence/*.png` 11 张）。
  正确分解是 顶层 5 + versions 15 + iter-1 104 = **124**，加本轮自建 evidence 62 = **186** ⇒ 报告的 124/186 对。
- **P7 JSON 块亲验**：我自己写栅栏解析（唯一 json 栅栏，json.loads 通过，17 顶层键，criteria 22 条 18/4），与"最近一次验收声称验过却不可解析"的历史对照。
- **P8 hash 口径自证**：我用自己实现的 runtime 口径把 `runs/smoke-t*/versions/*` **全部 19 个目录**重新哈希，**每一个都等于它自己的目录名**（t10 的 1f3d20ed…/ed98d1b8…、t11 的 3ac25f6c…/04d8ba5a… 在内）⇒ 我的口径与运行时的目录名口径一致，A₀/A₁ 与 E5 的结论不是抄来的。

## 4. 逐问独立判断

**Q1（全新空工程条款是否settle）**：settle。关键点在于该条款现在有**运行时自证**（`start_state.mode=fresh` 的语义是"它自己清空并重建"）+ **产物自证**（A₀ 快照就是一份 3 文件脚手架，且它的 project.godot sha 与 init 转写一致）。T10A-1 的"起点是既有产品"问题在本轮形式上不可能成立：mario 的冻结 A₀ 是 17 文件/18397 B，与本轮 A₀ 不同；`A_1≠A_0` 且差异非琐碎（+8 文件、场景 342→4358 B）。唯一保留的是**转写性质**（fresh_init*.txt 系 00:34:23 复盘落盘），但载荷部分已由冻结件互证。

**Q2（引擎作用域）**：claim 成立，且我给出的证据比报告更强（契约扫描 + 缓存 mtime 分叉 + 场景内容匹配）。**限制**：我没有活体查询编辑器（离线），所以"编辑器当时开的确实是新工程"依赖 cmdline + MCP 回包 + 磁盘缓存三条冻结/磁盘证据，不是我自己发的 tools/list。

**Q3（四项首次真机读数）**：1 绿、2 半绿、3 绿、4 红，与报告一致；红项我复现并读到源码级缺陷位置。半绿的含义要读准：短额**确实**在判定行（数值也自洽），改名**确实**生效，但"预算耗尽未到达"这一类本轮没有被走到 ⇒ 该分支仍无真机读数（F-T11-4）。

**Q4（两条新发现）**：观测都成立、都可量化，但 **F-T11-2 的机制归因不成立**（P3）。E3 的可信度边界因此是：
- 左右/跳跃两类**可信**（游戏进程位置样本 + 引擎 `assert_node_state` 4/4 passed；注入是编辑器侧这件事报告已披露）；
- "≥1 可交互对象"是**证据形态的假阴性**：游戏在本轮确实吃到过金币（计数=1 + 像素消失），判据没看到 0→1；⇒ not_met 作为判据判定正确，但**不能**读成"游戏不会拾取"；
- "终点/胜负"是**未驱动**（窗口没推进；Goal 在 6600、玩家 max x=225），不是"关卡不可通过"；且 win 条件在代码里存在（goal.gd）。
  报告没有把这两类说成产品缺失（它明说"只能证明这一次没动"），这是它最重要的诚实点。

**Q5（判定层面）**：六条判定、`unjudgeable=[]`、gap 声明、无借用证据，四项都通过。我没有发现"可判却标不可判"或反向：E3 的两类判 not_met 而非 unjudgeable 是可辩护的（判据要求"被观测到"），但我在风险里保留"未观测≠不存在"的读法要求。

**Q6（守卫与卫生）**：六基线（**现在**复算）逐字节一致；冻结文件、嵌套引擎、零依赖、未推送全部合规；三空目录清理不碰基线；二进制定位到"23:49:06 重建、含 DR-77 token"；报告 JSON 块真可解析。卫生层面两处小瑕（派生工件错值/非 UTF-8、转写而非轮内实写）已列缺陷与未验证。

## 5. 我没有检查的东西（诚实边界）

1. **没有起引擎、没有发任何 MCP 调用**（离线要求）⇒ 编辑器作用域、`tools/list` 的"154/177"、游戏端点可达性都只由冻结件与磁盘状态推断。
2. **没有重新 `cargo build`/`cargo test`** ⇒ "二进制来自 current HEAD"由 sha/mtime + 嵌入的 DR-77 token 支持，而非由复现构建证明。
3. **没有读 `src/runtime` 的交互窗口实现**（batch 上限、录音注入路径），因此 130 批/127 未花只从判定行文本核对。
4. 除"工程切换"这一主题外，**没有审 177 条契约的语义**（只扫了名称与参数）。
5. 密钥只做模式化检查；未取真值做熵/全等扫描。
6. 未审 `runs/smoke-t11/evidence/scripts/**` 里我未重实现的那批脚本的逻辑正确性。
7. 没有独立复核 Tester 的其余 6 条 verified claim（F3 facing/F4 camera/F5 ground/F16 HUD 我只核到 F16 与场景树），报告与 QA 对我的 E4 抽查是自洽的。

## 6. 给下一批的建议（不要在本轮修，但下一批必须处理）

1. **F-T11-2 追因要换判据**：别用"缺 editor_simulate_input_action"当原因（P3 已反驳）。建议做隔离 spike：在同一 game endpoint 上分别用 recording 注入与 editor 注入，逐帧读 `Input.is_action_pressed`/位置，并解释为什么第 7 步能推、第 9 步不能；顺带解释 T11A-5 的 4 帧漂移。
2. **F-T11-3 证据形态**：让交互窗口从**全新 play_scene** 起（QA 的 recommended_update 也是这个），或在电池顺序上把交互放在回放**之前**，或让 F10 接受"窗口内任意 +1"并要求前后各一次读数；同时把"产品不会拾取"与"证据形态假阴性"分开记。
3. **F-T11-1**：角色自己 play_scene 后要能刷新发布路由（或在角色工具面显式禁止 play_scene 并给出替代），但**不要**放宽 DR-43 的"路由不撒谎、不静默回退"。
4. 保留"124 = 运行时记录 / 186 = 含本轮自建 evidence"这种**时点+范围**写法；别再让 `-not -path "*/evidence/*"` 这类模式数错（P6）。
5. 基线摘要继续用文化序口径，并在文中写明；若要用 Python 复算，必须显式实现文化序，否则三条基线会假红（P1）。
6. 修派生分析工件：`interaction_detail.txt` 的 `distinct_x` 统计与 `interaction_verdict_line.txt` 的 UTF-8（把 em dash 落到盘上不要用控制台转写），让"支撑证据"与"结论"一致（T11A-3）。
7. 下一真机轮**必须重走 §2.1**：编辑器 22876 已不在、9877 空闲；建议同时把"先 doctor/netstat 再启动"的顺序做实（本轮 preflight 1/2 实际在启动之后才取，轮前的无监听证据只在 prerun_state.txt）。
8. 报告措辞上，凡"0 次/全轮没有"务必写清范围（判定件 vs 全轮），凡"absent"务必与"unobserved"分开（T11A-2 / T11A-4）。
