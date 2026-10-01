# TASK-DR78-ACCEPTANCE — DR-78 的独立验收（全新验收子代理，无实现者/调度者上下文）

> 验收人：**独立验收子代理**（本批实现者与调度者之外的全新代理；未继承任何结论；工作单独完成，未委派、未使用子代理）。
> 被验对象：`.spec/hof-rs/tasks/TASK-DR78.md`（任务书）、`.spec/hof-rs/tasks/TASK-DR78-REPORT.md`（实现者报告，**只作线索，绝不是证据**）、
> `.spec/hof-rs/tasks/TASK-SMOKE-T11-ACCEPTANCE.md`（T11A-1..5）、`.spec/hof-rs/tasks/TASK-DR77-ACCEPTANCE.md`（D77-A/D77-B）、`DECISIONS.md` D291/D292。
> **HEAD = `244d1ee`**（实现 `bf943d0` + 只动文档的 `244d1ee`）；开工/收工时 `git diff` 与 `git diff --cached` 皆空，工作树只有一处 **untracked** `.spec/hof-rs/tasks/TASK-SMOKE-T12.md`（mtime 02:19:38，调度者新任务书，非本批产物）。
> **离线**：未启动 Godot、未跑真机轮、未联网、未调用任何模型端点；**未 push、未 stage**。
> **`runs/**` 零写入（含临时文件）**——我的全部脚本只**读** `runs/**`；临时脚本/备份/日志全在仓外 `C:\Users\wyl\AppData\Local\Temp\dr78acc\`。
> **未对任何路径用 `rm -rf`**；**未从未展开的变量构造路径**；未改 `.workspace/mario/**`、`.workspace/fresh-t11/**`、`.spec/hof-rs/PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`。
> 我自己的**关键口径全部重写**（冻结载荷解析、六条基线摘要、函数名集合差、栅栏感知 JSON 解析、八处植入驱动），不调用被验方的脚本。
> **8 处植入我全部亲自重做并逐字节回退**（§3），其中 6 处对应实现者的 P1–P6，2 处是我另加的反例。

## 0. 机器可读结论块（由 `json.dumps(..., ensure_ascii=False, indent=2)` 序列化后落盘，并由我自己的栅栏感知脚本 `json.loads` 回读，见 §8）

```json
{
  "verdict": "pass",
  "task": "TASK-DR78-ACCEPTANCE",
  "object": {
    "task_book": ".spec/hof-rs/tasks/TASK-DR78.md",
    "report": ".spec/hof-rs/tasks/TASK-DR78-REPORT.md",
    "implementation_commit": "bf943d0d4d04676fe6dbce4ea4bf71fdccb11775",
    "docs_commit": "244d1ee418e102650fc74d43130e6829a7aca3d9",
    "repo_head_at_acceptance": "244d1ee418e102650fc74d43130e6829a7aca3d9",
    "base_head": "1bed9b11ccb3bbd2eb713ddf47d6c0dbf05eeeab",
    "working_tree_at_acceptance": "git diff/diff --cached empty; one untracked .spec/hof-rs/tasks/TASK-SMOKE-T12.md (created 02:19:38 by the dispatcher, not by this batch)"
  },
  "summary": "四项全部独立复现。①：我用自己写的脚本重解全部冻结载荷，逐条命中作者引用的读数——input_channel_probe 0 次 editor_simulate_input_action 却把玩家从 67.3333358764648 推到 173.666687011719（C1 反例成立，报告中那条因果判据确实被证伪）；input_replay 的 move_left 窗口 455.999542236328→239.666732788086（3.666657787 px/帧），整轮**唯一**一次 move_left pressed=false 带 target=editor；interaction 三批各 60 帧 unique_x=1（225.000045776367）；交接 14.666687011719 px = 4.000015 帧满速左移；第 9 步 facing=-1 / velocity={0,0}；黄像素 576 只在 replay-move_right-before.png。『move_left 在游戏进程里从未被释放』这一机制我从冻结源码路径（godot.rs:2194-2202 在**每个窗口开头** drain，最后一个窗口无后继）独立证实，并亲自植入『删掉 release』——目标测试 exit 101@:4770。②：角色侧发布落点/顺序/拒绝语义我逐行读过，并亲自植入 3 处（关掉发布分支 → exit 101@:368；删掉 readiness 失败时的 clear → exit 101@:471，证明『失败即撤回、不回退编辑器』是真的钉住的）。③：顺序不变量 + 自清动作 + 夹具按 game_axis 判定，两处回归钉我用自己的最小复原各自打红（exit 101@:4733 与 @:4770）。④：常量回到真旧名、两条断言不再恒真（我的『只提旧名』段落 → exit 101@:317；把常量改回新 token → exit 101@:55）；geometric 已从测试名与点名的消息/注释清除，台账映射行保留。⑤：六处植入我全部重做（全部 exit 101，落在同一行号），逐字节回退（bytes_identical / hash-object==HEAD / diff 空 / status 空），P1/P4/P5 的植入片段与 1bed9b1 的原文逐字节相同。⑥：我自己的门（先 `cargo clean -p hof-rs` 真重编，首行 Compiling）`cargo test --offline` exit 0，59 行 test result 求和 546 passed / 0 failed / 7 ignored；`--list` = 553 = 546+7；fmt exit 0；#[ignore] 9→9；唯一被移除的函数名就是任务书点名的改名。六条只读基线我用自己重写的 PowerShell 口径复算并命中（smoke-t6 = c144ef32…7a9c03 自证），排序口径承重（序数序会给 mario/t8/t10 三个假值）；fresh-t11 与冻结 A_1 快照 11 文件/8830 B 逐字节相同；runs/** 我全程零写入。报告机器可读块由序列化器产出、我的栅栏感知解析器 json.loads 通过，正文与派生工件数字一致。发现的是**守卫强度与披露边界**问题，不是行为或证据链断裂：交付技能里那句旧名映射**没有任何测试钉住其存在**（我的 NOMAP 反例 exit 0），这是 DR-77 验收 R1 在技能侧未闭合（任务书 ④ 只要求改常量+加植入，故不判 fail）；另有 3 处 info 级披露/措辞问题，见 defects。",
  "criteria": [
    {
      "id": "1-spike-cause-pinned-by-my-own-readings",
      "pass": true,
      "evidence": "我自己的脚本（C:\\Users\\wyl\\AppData\\Local\\Temp\\dr78acc\\spike_mine.py，只读）重解 runs/smoke-t11/iter-1/candidate/.hoh/deterministic/raw/*.json：(a) input_channel_probe.json calls=8、editor_simulate_input_action=0、move_right:frames n=30 首 67.3333358764648 末 173.666687011719、只读 gdscript 回读 173.666687011719；(b) input_replay.json calls=48、editor_simulate_input_action=8，四个采样窗口 192.000045776367→408.333038330078 / 426.666320800781→459.666229248047 / jump 恒 466.999542236328（y 弧） / 455.999542236328→239.666732788086（3.666657787258 px/帧）；(c) interaction_evidence.json 三批各 60 帧，unique_x=1 且 x=225.000045776367、unique_y=1（303.925262451172），三条 play_input_recording 回包 injected=1/replayed=true；(d) 交接 239.666732788086→225.000045776367 = 14.666687011719 px = 4.000015 帧满速左移；(e) 第 9 步（node_and_collision_assertions.json call 0）facing=-1、velocity={x:0.0,y:0.0}、position x=225.000045776367；(f) 全 raw 目录里 move_left 的 pressed=false 只有一处：input_replay.json call 47 editor_simulate_input_action，回包 target=editor；(g) 冻结 player.gd:23-28 direction=Input.get_axis(move_left,move_right)；direction!=0 才写 velocity.x=direction*speed 与 facing，否则 velocity.x=move_toward(...,0)；矩阵两个方向都按住 ⇒ direction=0 ⇒ 站立；(h) 产生这批载荷的源码路径：godot.rs:2192-2202 在每个窗口**开头** drain held_in_game 做 release，2231 把本窗口动作 push，循环最后一个窗口（move_left）之后没有任何释放 ⇒ 泄漏。⇒ 结论 (b)『送达但被遗留的相反动作抵消』成立；这些数字与作者 spike_output.txt / 报告 §2.2 **逐字一致**，是我自己算出来的。"
    },
    {
      "id": "1-alternatives-excluded-with-a-raw-reading",
      "pass": true,
      "evidence": "(a)『没施加』排除：三批 injected=1/replayed=true，且若完全没施加而 move_left 仍按住，玩家会继续满速左行而不是在窗口首样本就停住；(c)『时基/帧推进不对』排除：交接处玩家以满速前进了 4.000015 帧（位移读数，不是推断），三批帧号 0..59 齐全；(d)『采样点取错』排除：两个窗口的 node_path 都是 /root/Main/Player、工具与形状（frame_count/frame_interval）相同；(e) 未发现第三类：任何其它解释都要假设一个载荷里不存在的释放入口。C1（同轮能力对照）我逐字复现：input_channel_probe 同样是 0 次 editor_simulate_input_action，却用同一套 recording 注入推了 30 帧 ⇒ 报告 F-T11-2 原来那条判据确实不充分（任务书 §0 的要求达成）。C2（几何对照）：同一轮 move_right 窗口自己的逐帧序列穿过 x=225 与 x=400(Coin1) 所在的整个区间 192…408.333，⇒ 交互窗口按住 move_right 却**不动**，不能归因于该处有挡墙（挡墙也该让它朝右动）。"
    },
    {
      "id": "1-counterexample-checks-distinguish-did-not-move-from-could-not-move",
      "pass": true,
      "evidence": "报告 C1-C5 我逐条核过：C1 同轮能力对照（见上，我复现）；C2 几何穿越（我复现）；C4 同一采样对象（我复现）；C5 游戏在步进（我复现 4.000015 帧）。C3（游戏自身 facing/velocity）我做了**独立加固**：从冻结引擎源码 godot-mcp/godot/scene/2d/physics/character_body_2d.cpp 读 move_and_slide 的语义——facing 是在 _physics_process 里由 direction 先写再 move_and_slide（player.gd:24-28），所以『朝右驱动却被挡住』必然读 facing=+1；观测到 facing=-1 与 velocity=0 因此排除『在推但没动』。注意一处精度问题（info，见 defects）：报告说被挡住的角色 `velocity.x` 仍为 ±220——对**贴地**撞墙成立（character_body_2d.cpp:286-288 只 slide 掉竖直分量），但离地贴墙时 :274-283 会把水平分量也抹掉；两种情形 facing 都仍是 +1，所以判据的**结论**不受影响，只是那句话比引擎语义宽。"
    },
    {
      "id": "1-limit-disclosed-and-plant-reddens",
      "pass": true,
      "evidence": "限制的诚实性：报告 risks 第 2 条与 unverified 第 2/3 条明写『真因由冻结读数+冻结游戏代码+生产源码路径夹出，不是真机因果实验』，并把『move_right 生效的确切帧』列为未知——这与我看到的事实相符（1 帧采样的冻结载荷无法分辨生效帧）。结论强度：证据链是演绎的（游戏在步进 + move_left 被按住 + 恰在注入时刻停住 + 该通道在另外两个窗口被证明有效），我判定**足以支撑后续构建**。我自己植入『删掉观测窗口的 stale release』（src/adapter/godot.rs：整段 `for stale in INTERACTION_STALE_ACTIONS` 删除）：tests/evidence_battery.rs::the_observing_window_clears_a_stale_opposing_action_by_itself **exit 101，panic @ tests\\evidence_battery.rs:4770**，红输出显示 player max x=Some(60.0) 且 COIN_PICKED_UP 仍被记录（窗口成了旁观者）；回退后 bytes_identical=True、hash_object==HEAD=True、diff/status 空。"
    },
    {
      "id": "2-role-started-scene-republishes-the-route",
      "pass": true,
      "evidence": "读码：src/cli_impl.rs 在 `bridge::tools_call_with_reply` 返回后、打印回包之前，仅当 `call.tool == bridge::GAME_START_TOOL`（= \"editor_play_scene\"，src/tools/bridge.rs）且 reply.answered() 时调用 `adapter.publish_role_started_game_route`；实现 src/adapter/godot.rs:4838-4890 顺序 = parse_game_endpoint → install_game_endpoint → wait_for_ready_matching(running_game_get_scene_tree, scene_tree_readiness, ready_timeout_seconds) → publish_game_endpoint；trait 默认 Ok(None)（src/adapter/mod.rs:241）。我自己跑通：`cargo test --offline --test game_route_across_processes a_role_started_scene_republishes_the_game_route_for_later_processes -- --exact` 绿（我的门 546/0/7 里包含它）；我自己的植入 P3（把发布分支改成 `if false && ...`）→ **exit 101 @ tests\\game_route_across_processes.rs:368**，回退逐字节干净。"
    },
    {
      "id": "2-refusal-semantics-untouched-no-editor-fallback",
      "pass": true,
      "evidence": "拒绝条件所在的层（src/tools/endpoint.rs 的 RouteRefusal / 端口与 pid 存活判定、tools/mod.rs 的 clear_game_endpoint/withdraw_game_route）在本批 diff 里**一个字节都没动**（bf943d0 只改 src/adapter/{mod,godot}.rs、src/cli_impl.rs、src/tools/bridge.rs、三个测试文件）。既有四条 DR-43 拒绝测试在我的门里全绿（a_route_pointing_at_a_closed_port_is_refused_explicitly、a_route_whose_recorded_game_process_is_gone_is_refused_even_when_the_port_answers、an_expired_route_is_refused_even_when_it_still_answers、without_a_published_route_the_game_call_still_fails_loudly）。三条新测试断言编辑器端点**从不**收到 running_game_*（我这三条都在自己的门里跑过）。最强的非空洞性证据是我自己的反例 X-noclear：删掉 readiness 失败分支里的 `tools.clear_game_endpoint().await;` ⇒ a_role_started_scene_that_never_becomes_ready_is_refused_and_leaves_no_route **exit 101 @ :471**（旧路由得以存活、后续调用成功而不是拿到 game_endpoint_unavailable）——说明『失败即撤回、绝不回退』不是一句注释。"
    },
    {
      "id": "2-disclosed-readiness-side-effect-bounded-and-fail-safe",
      "pass": true,
      "evidence": "副作用真实存在且我确认过路径：`install_game_endpoint` 只做进程内路由，`wait_for_ready_matching` 无论 HOH_GAME_ROUTE 是否配置都会跑，`publish_game_endpoint` 在 HOH_GAME_ROUTE 未设时提前 return Ok(())（src/tools/mod.rs:442-448）⇒ 『未设路由时发布是 no-op 但就绪确认仍跑』如实。有界吗：wait_for_ready_matching 以 Instant::now()+timeout_secs 为 deadline（src/tools/reliable.rs:338-348），默认 `tools.ready_timeout_seconds = 30`（src/config.rs:145-154、config → BatteryConfig 默认 30 at src/adapter/godot.rs:33），轮询间隔 500 ms；且 DR-55 的『端点已判死就不再敲门』会让它在拒绝时提前结束。⇒ 每次角色侧 play_scene 最多多等 ~30 s，**不会挂死**。失败安全吗：就绪失败 ⇒ clear_game_endpoint（撤回文件）+ anyhow::bail ⇒ CLI 映射成 HofError::External ⇒ exit 4，消息里含 running_game_get_scene_tree 与『did not answer』；发布失败 ⇒ 同样撤回 + 消息含 could not be published 与 DR-43。会误导轮次吗：不会静默成功；但**会改变角色侧时延画像**，并在失败时撤回此前对外可用的路由（见 risks 与 defects D4）。"
    },
    {
      "id": "3-observing-window-first-and-self-sufficient",
      "pass": true,
      "evidence": "顺序：src/adapter/godot.rs run() 现在是 step_interaction_evidence(642) → step_input_channel_probe(643) → step_input_replay(644)，常量 COIN_OBSERVING_BATTERY_STEP=\"interaction_evidence\" / COIN_CONSUMING_BATTERY_STEPS=[\"input_channel_probe\",\"input_replay\"]（:3775-3801）；测试读的是电池真产出的 records 顺序。冻结 battery.json 的顺序是 input_channel_probe(6) / input_replay(7) / interaction_evidence(8) —— 我复算过，正是被测缺陷。自给自足：观测窗口在第一批之前对 INTERACTION_STALE_ACTIONS（当前 = [\"move_left\"]，:3974）走 semantic_release_action，被拒时写 STALE_ACTION_NOT_RELEASED 而不吞（:2636-2652）。夹具：交互斜坡的条件是 `self.driving() && moves && self.game_axis() > 0.0`（tests/evidence_battery.rs:1318），而 game_axis() 用 held_in_game 复现『两个都按住 ⇒ 0』（:671-680）⇒ 注入被接受不再等于玩家会动，正是 T11 被掩盖的那一步。两条回归钉我都自己重做：P1（把顺序整段复原成 1bed9b1 的原文）⇒ **exit 101 @ tests\\evidence_battery.rs:4733**；P2（删掉自清动作块）⇒ **exit 101 @ :4770**；两者回退后逐字节干净。补充（我没在报告里看到、但已核实）：interaction_evidence 不读 self.channel（self.channel 只在 step_input_replay 的 :2101/:2162 被读），所以把它提到 probe 之前**不会**破坏 channel 依赖；probe 的判据也不依赖位移（capability 只看 pressed 与 game_process_reachable/axis_after 是否有值，:1475-1479）。"
    },
    {
      "id": "4-D77A-token-real-again-and-guards-redden",
      "pass": true,
      "evidence": "tests/interaction_contract.rs:43 `const SUPERSEDED_GEOMETRIC_TOKEN: &str = \"WIN_UNREACHABLE_GEOMETRICALLY\";`（真旧名），并有 :53-65 的直接钉子 assert_ne!(旧,新) + assert_eq!(旧,字面旧名) + assert_eq!(新,字面新名)。我自己的植入：P4（常量改回 BLOCKED_VERDICT，与 1bed9b1:tests/interaction_contract.rs:35 逐字节相同）⇒ the_superseded_token_is_the_old_name_and_not_a_copy_of_the_new_one **exit 101 @ :55**；P6（在交付技能末尾追加一段只含旧名的判定句）⇒ the_godot_dev_skill_retracts_the_impassable_level_claim **exit 101 @ :317**，红信息逐字为『the old token `WIN_UNREACHABLE_GEOMETRICALLY` may survive only inside a statement that maps it to `WIN_BLOCKED_UNDER_MOVE_RIGHT`』。两处退化我都读了源码并确认根因：技能是 CRLF，测试现在先 normalize 再逐段 split(\"\\n\\n\")（:312-322，原实现切不开段落）；台账查找现在要求同段同时含旧名与新名（:334-345）——我核实 TASK-DR73-REPORT.md:114-127 的 DR-76 更正段确实只提旧名不提新名，所以 DR-77 验收的 FIXONLY（只改常量就打红）被**真正修掉**，而不是靠退化常量绿。"
    },
    {
      "id": "4-D77B-geometric-gone-with-a-mapping-kept",
      "pass": true,
      "evidence": "测试名：HEAD 里只有 a_player_that_stops_advancing_with_budget_left_is_blocked_under_move_right（tests/evidence_battery.rs:4581），`grep -rn is_a_geometric_verdict tests/` = 0；`cargo test -- --list` 我实跑 553 条，含新名、不含旧名。点名的落点我逐处看过：tests/evidence_battery.rs 的 :337/:453/:4428 与 src/adapter/godot.rs 的对应注释现在都是 movement-direction / `WIN_BLOCKED_UNDER_MOVE_RIGHT` 口径；`grep -n geometric src/adapter/godot.rs` = 0（小写形式已无）。残留的小写 geometric 只在三处：tests/evidence_battery.rs:4816 的注释与 :4826/:4827 两个 concat! 片段（那是**钉子自己在讲被撤回的措辞**，且刻意用 concat! 拼出以免自证空洞），以及 tests/dr77_evidence_tightening.rs（DR-77 自己的文件，不在本批范围）。映射保留：TASK-DR73-REPORT.md:706 与 :713 两条映射行都在（含旧名与新名），交付技能 src/prompts/skills/godot-dev.md:163-167 的映射句也在。P5（把测试函数名改回 1bed9b1 的原文）⇒ the_battery_names_the_blocked_verdict_by_its_movement_direction **exit 101 @ :4834**。"
    },
    {
      "id": "5-six-plants-red-restored-byte-exactly-and-three-verbatim",
      "pass": true,
      "evidence": "我自己在仓外脚本驱动下重做全部六处（每次先备份到仓外 C:\\Users\\wyl\\AppData\\Local\\Temp\\dr78acc\\bak，改动源码后跑对应测试，再原字节回写）：P1 exit 101@evidence_battery.rs:4733、P2 exit 101@:4770、P3 exit 101@game_route_across_processes.rs:368、P4 exit 101@interaction_contract.rs:55、P5 exit 101@:4834、P6 exit 101@:317 —— 与实现者 plants 转写**同一行号**。每处回退后四重校验全部 True：对仓外备份逐字节相同、git hash-object == git rev-parse HEAD:<path>、`git diff --stat -- <path>` 空、`git status --porcelain -uall -- <path>` 空。三处逐字重建：我的脚本自证 P1/P4/P5 的植入片段与 `git show 1bed9b1:<path>` 的对应字节相同（我另用 git show 直接从 1bed9b1 取出原文对照）⇒ 它们的红**就是**那三条测试在 DR-77 树上的真实结果，不是发明的破坏。P2/P3/P6 属于『植入红』（树上原本不存在这些片段）。先红日志的披露：报告 unverified 第 1 条明写『没有为每条新测试单独存档先红日志』，并区分了『P1/P4/P5 可复算地重建先红那一态』与『植入红』；我判定该披露**诚实但确实削弱** TDD 的过程性证明——树里能证明的是终态非空洞，不能证明『先写失败测试』这一步真的发生过。"
    },
    {
      "id": "6-gate-reproduced-on-the-code-revision",
      "pass": true,
      "evidence": "我先 `cargo clean -p hof-rs`（Removed 11280 files）再跑自己的门：`cargo test --offline` **exit 0**，首行 `Compiling hof-rs v0.1.0 (F:\\moonbit-hof-rs)`（真重编，非陈旧产物），59 行 `test result:` 求和 = **546 passed / 0 failed / 7 ignored**，FAILED=0、^error=0、panicked=0、^warning=0；`cargo test --offline -- --list` **exit 0**，测试名行 **553 = 546+7**；`cargo fmt --check` **exit 0**。版本归属：代码改动全在 bf943d0，`git diff --name-only bf943d0..HEAD` 的 18 个文件**全部**在 `.spec/hof-rs/tasks/**` 下（报告/spike/gate 工件；无 src/、tests/、Cargo*）⇒ 『门测在代码所在的修订上、后一个提交只动文档』成立。唯一被删的测试名：我不依赖实现的 names.txt，自己用 `git grep -F \"fn \" 1bed9b1|HEAD -- src tests` 做集合差——**REMOVED = 1 条**，正是 a_player_that_stops_advancing_with_budget_left_is_a_geometric_verdict（改名为 _blocked_under_move_right，新名存在且被 --list 收录）；`git grep -h \"#\\[ignore\" 1bed9b1|HEAD -- src tests | wc -l` = **9 → 9**（未增长）。我自己的数（1662→1682 声明、1391→1406 个不同名）与实现的 1627→1646 口径不同（计数方式差异），但**改名集合差 = 1** 这一实质结论一致。"
    },
    {
      "id": "6-forbidden-zones-with-a-state-digest-caliber",
      "pass": true,
      "evidence": "口径（我自己重写 PowerShell 脚本，不调用被验方脚本）：仓根相对、小写 POSIX 路径 + TAB + 十进制字节数 + TAB + sha256；行以 `\\n` 连接、无尾随换行；行序 = PowerShell `Sort-Object` **文化序**（本机 culture=zh-CN）；对整块 UTF-8 取 sha256。自证与六条：smoke-t6 files=135 digest=**c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03**（点名自证值命中）、mario 178 **dee0a36f…6cc94**、t7 115 **6e4c1595…520fb7**、t8 358 **6d11b2c6…bdf5a7**、t9 83 **541e2d81…36ca9d**、t10 232 **31955589…b38b8b**；与 T11 验收记录的全文值逐字相同，且在我的全部工作之后复算仍相同。**排序是否承重**：承重。我用 Python 码点序（ordinal）复算得到 mario=f622f5b0…、t8=c347bd63…、t10=9ba72fbd…、fresh-t11=5d3e219e…（t6/t7/t9 不变）⇒ t6 的自证**不能**证明排序口径（它对两种序都一样），t8/t10 才能；任何用 Python 默认排序复算的人会把三条基线误判为被动过。fresh-t11：冻结投影比较（排除 .godot/.import/.hoh/.git）= 11 文件/8830 B，only-in-live=[] / only-in-snapshot=[] / differing=[] ⇒ IDENTICAL，点名文件 sha 前缀与实现者一致（project.godot 00d02c9c08c3dc4f、scenes/main.tscn 813c145720d665d8、scripts/player.gd ae5d836ba4ba5e9b——player.gd 与冻结玩家代码一致，这也是 spike 结论所依赖的『冻结游戏代码』）。runs/** 零写入：`find runs -newermt \"2026-10-02 01:00\"` = 0，`find runs -newermt \"-30 minutes\"` = 0（我的整个会话窗口内 0）；`find .workspace/mario -newermt ...` = 0；`find .workspace/fresh-t11 -newermt 00:35` = 0。其余守卫：sha256(.spec/hof-rs/PRD-mario.md)=4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a；`git diff 1bed9b1..HEAD -- DECISIONS.md` = 0 行；嵌套引擎 `git -C godot-mcp/godot rev-parse HEAD`=fc63af77…、porcelain 0 行；`git diff 1bed9b1..HEAD -- Cargo.toml Cargo.lock` = 0 行（无新依赖）；`git rev-list --left-right --count origin/master...HEAD` = `0 14`（未推送）；`git diff --cached` 空（未 stage）。"
    },
    {
      "id": "6-report-json-block-parses-and-discipline-met",
      "pass": true,
      "evidence": "我写了自己的栅栏感知解析器（按 ``` 切块，只解析 info string 为 json 的块）：TASK-DR78-REPORT.md 共 12 个围栏、其中 json 块 1 个、**json.loads 通过**，14 个顶层键，criteria 11 条（11 pass true / 0 false），verdict='pass' ⇒ 块确实由序列化器产出（对照 DR-77 手写块的教训）。纪律 1（可复算 + 作用域）：『0 次 / 逐位相同』类断言我都从同一冻结载荷复算过，且报告 §8.1 为每条写明了作用域（哪个文件、哪个子集）；只有一处措辞偏宽（见 defects D3，不影响结论）。纪律 2（机制归因附反例）：报告 §2.3 的 C1-C5 与 ③/② 的植入齐备，我逐条复现。纪律 3（序列化 + 回读）：我独立复验通过（实现者另有 validate_json_block.py + json_block_check.txt，结论一致）。纪律 4（派生物不矛盾）：spike_output.txt / gate/*.txt / names.txt 的数字与正文一致——我用同一批冻结载荷复算到位（handover 14.666687011719、4.000015 帧、576 黄像素、546/0/7、553、59 行、9→9）。"
    }
  ],
  "defects": [
    {
      "id": "D1-skill-mapping-has-no-test-pinning-its-existence",
      "severity": "minor",
      "what": "任务书 ④ 要求『保留旧名映射行』，映射行**确实保留**（技能 :163-167、台账 :706/:713），但**交付技能那一句没有任何测试钉住其存在**：现行检查只要求『任何提到旧名的段落必须同段给出新名』，所以把技能里唯一的旧名映射句整段删掉后，相关测试仍绿。这正是 DR-77 验收 R1 指出的缺口在技能侧**未闭合**（台账侧已由『同段必须同时含两名』钉住）。任务书 ④ 的字面要求（常量回到真旧名 + 用植入证明只提旧名必红 + 清 geometric）都做到了，所以我判 **不 fail**，记为残留守卫缺口。",
      "reproduction": "我的植入 X-nomap：把 src/prompts/skills/godot-dev.md:163-167 的 ` (This … `WIN_BLOCKED_UNDER_MOVE_RIGHT`.)` 段删掉，跑 `cargo test --offline --test interaction_contract the_godot_dev_skill_retracts_the_impassable_level_claim -- --exact` ⇒ **exit 0（绿）**；回退后 bytes_identical=True、hash_object==HEAD=True、diff/status 空。"
    },
    {
      "id": "D2-undisclosed-exit-4-for-a-non-announcing-reply",
      "severity": "minor",
      "what": "角色侧 play_scene 的发布触发比报告披露的宽一格：只要 `editor_play_scene` 被应答（ToolCallReply::Answered）就调用 publish_role_started_game_route，而 `parse_game_endpoint` 对**既无 endpoint 也无 mcp_port** 的成功回包直接返回 Err（godot.rs:3281-3286）⇒ CLI 立刻 exit 4，消息是『started a game whose route could not be published … (DR-43)』。报告披露了『就绪未确认 ⇒ exit 4』与『发布失败 ⇒ exit 4』，但没提这一类『回包成功却不宣告游戏端点』的回包也会变成硬失败（此前它只是被打印出来）。契约里 editor_play_scene 正常都宣告端点，所以实际触发概率低；记为**行为变化披露不全**。",
      "reproduction": "读 src/tools/bridge.rs（GAME_START_TOOL / answered）与 src/adapter/godot.rs:3268-3304（parse_game_endpoint 的 Err 分支）+ src/cli_impl.rs 的 map_err；离线无法构造真机回包，仅在源码路径上确证。"
    },
    {
      "id": "D3-mechanism-sentence-broader-than-the-engine",
      "severity": "info",
      "what": "报告 §2.2(C) 写『被墙挡住的角色 direction 仍是 ±1、velocity.x 仍是 ±220、facing 会被写成 +1』。『facing=+1』对朝右驱动成立（player.gd:26 在 move_and_slide 之前写），但 `velocity.x` 的取值依赖状态：贴地撞墙时水平分量确实保留（character_body_2d.cpp:286-288 只 slide 掉竖直分量），离地贴墙时 :274-283 会把水平分量也抹掉。⇒ 判据的**结论**（观测到 facing=-1 排除『朝右驱动却被挡住』）不受影响，但这句话把引擎语义说得比实际宽。",
      "reproduction": "读 godot-mcp/godot/scene/2d/physics/character_body_2d.cpp:274-288 与 runs/smoke-t11/iter-1/candidate/.hoh/deterministic/raw/node_and_collision_assertions.json call 0（facing=-1 / velocity={0,0} / floor_block_on_wall=true）。"
    },
    {
      "id": "D4-reorder-changes-the-state-the-probe-and-replay-observe",
      "severity": "info",
      "what": "interaction_evidence 现在跑在 input_channel_probe / input_replay **之前**，而它在自己的驱动里把玩家推进并吃掉金币；因此 probe 与 replay 两个窗口在**下一轮**看到的起始状态（玩家 x、金币计数、以及它们自己的原始采样序列）必然与冻结的 smoke-t11 载荷不同。窗口自己的断言仍然可用（probe 的 capability 不看位移，:1475-1479；replay 断言的是『与窗口首样本不同』），所以这不是缺陷，但报告 risks 里没有提『这是下一轮证据形态的一次变化』，读者可能拿新旧 raw 逐值对比而误判。另外：释放后，观测窗口自己残留的 move_right 只能靠 input_replay 的开头 drain 清掉——新的顺序把它变成第一个驱动窗口，自清动作在当前顺序下是**防御性**的而非必需的。",
      "reproduction": "读 src/adapter/godot.rs:642-644 与 :2636-2652、:2194-2202；对照 runs/smoke-t11/.../battery.json 的旧顺序与 raw/input_channel_probe.json 的位移读数。"
    },
    {
      "id": "D5-machine-reader-cannot-tell-head-from-the-implementation-commit",
      "severity": "info",
      "what": "报告 §0 块里 `\"head\": \"bf943d0d4d04676fe6dbce4ea4bf71fdccb11775\"` 与 `implementation_commit: bf943d0` 是同一个值，而验收时的仓库 HEAD 是 `244d1ee`（只加文档的提交）。正文用『工作提交：bf943d0』解释清楚了，但只看机器可读块的读者会以为那是 HEAD。不影响任何读数。",
      "reproduction": "`git rev-parse HEAD` = 244d1ee418e102650fc74d43130e6829a7aca3d9；`git diff --name-only bf943d0..HEAD` 全在 .spec/ 下。"
    },
    {
      "id": "D6-tools_call-left-with-no-caller-and-a-stale-doc",
      "severity": "info",
      "what": "重构后 `bridge::tools_call` 在仓内**没有任何调用者**（唯一入口 src/cli_impl.rs 改用 tools_call_with_reply），而它的文档注释写着『[tools_call] is the printing form and is what most callers want』——与事实相反。它是 pub API，不会触发 dead_code 警告，所以门看不见。属于清理项而非缺陷。",
      "reproduction": "`grep -rn \"tools_call\\b\" --include=*.rs . | grep -v target`（仓内只剩定义与两处文档引用；godot-mcp/recovery/staging 下的副本是旧快照）。"
    }
  ],
  "risks": [
    "无真机轮：②③④ 只在离线（真实 hoh 二进制 + loopback JSON-RPC 双端点、真实电池夹具）上证明；真机上『stale 释放的接受率』『就绪等待的真实时延』『重发布路由后另一进程能否真到达』我同样不声称。",
    "角色侧 editor_play_scene 现在多一次最长 30 s（tools.ready_timeout_seconds）的就绪等待，并且**就绪失败会撤回此前对外可用的路由**（clear_game_endpoint 同时 withdraw 文件）。若角色在轮中反复 play_scene，其它角色可能暂时失去可用路由——这是 DR-71 语义的正当结果，但改变了角色侧的时延/可用性画像。",
    "新顺序使 interaction_evidence 成为第一个驱动窗口：它自己残留的 move_right 依赖 input_replay 开头 drain 清除；若将来再调顺序或去掉那个 drain，泄漏会以新形式回归。",
    "INTERACTION_STALE_ACTIONS 只列 move_left；若关卡语义改成『按住即持续跳跃』之类，需要把 jump 也列入。",
    "技能侧旧名映射句没有测试钉住其存在（D1，我的 NOMAP 反例 exit 0）。",
    "基线摘要口径依赖 PowerShell 文化序（本机 zh-CN）：换一台 culture 不同的机器，mario/t8/t10/fresh-t11 的摘要可能不同；t6/t7/t9 对排序不敏感，所以 t6 的自证值不能单独担保口径。",
    "`cargo fmt --check` 与 git 都对 CRLF/LF 不可见（DR-77 R4 仍在）；本批被编辑的 8 个文件各自保持原有行尾（我逐文件数过 CRLF 计数），但这条不可见性仍可能掩盖将来的改行尾。"
  ],
  "unverified": [
    "真机行为：本批离线，未起引擎、未跑轮、未联网（硬约束）；②③④ 的真机读数不存在。",
    "interaction 窗口的 move_right 生效的确切帧：1 帧采样的冻结载荷只能把区间界定在窗口前 8 次调用内。",
    "先红（red-first）的过程：树里无法证明『先写会失败的测试』真的发生过；我只能证明终态非空洞，且 P1/P4/P5 逐字重建了 DR-77 树上的红。报告如实披露了缺日志。",
    "`.workspace/fresh-t11` 全树（100 文件，含 .godot/.hoh 缓存）除实现者自己的摘要记录外没有独立的冻结基线；我验证的是 11 文件/8830 B 的工程投影与冻结 A_1 快照逐字节相同，另复算 100 文件摘要复现了实现者记录的值（4c07c0b6…）。",
    "夹具（tests/evidence_battery.rs 的双端点/HUD 模型）是否忠实复现真机在新顺序下的语义：我只读了模型与断言，没有真机对照。",
    "键料卫生：本批沿用模式化检查口径，未做熵扫描（与 T11 验收同）。",
    "`.spec/hof-rs/tasks/TASK-SMOKE-T12.md` 在我的会话开始前后被调度者新建（untracked，mtime 02:19:38），因此『开工时 git status 为空』这一条只能按实现者报告当时的状态采信；我确认它不是我写的、也不是实现批次的一部分。"
  ],
  "machine_readable_block_check": "由我自己的栅栏感知脚本 json.loads 复验通过（本文件内 json 围栏块 1 个、失败 0），见正文 §8",
  "my_plants": {
    "count": 8,
    "red": 7,
    "green_by_design": 1,
    "table": "见正文 §3"
  }
}
```

---

## 1. 结论

**`verdict = pass`。四项全部独立复现，且每一项我都有自己的红/绿证据；我发现的缺陷都是「守卫强度 / 披露边界 / 措辞精度」，没有一条是行为或证据链的断裂。**

一句话判断：**这一批把 T11 的三处流水线缺陷真修了，把 D77-A/D77-B 真清了，而且没有靠削弱 DR-43 的拒绝语义来换绿。**

1. **①（隔离 spike）**：报告对 F-T11-2 给出的原判据**确实被证伪**（我用同一份冻结载荷复现：`input_channel_probe` 也是 0 次
   `editor_simulate_input_action`，却把玩家从 `67.3333358764648` 推到 `173.666687011719`）。真因 **(b) 送达但被遗留的相反动作抵消** 我用自己的读数逐条证实：
   整轮唯一一次 `move_left pressed=false` 带 `target=editor`；交接处玩家以满速前进 `4.000015` 帧；
   交互窗口 180 帧 `unique_x=1` 且恰在注入时刻停住；第 9 步 `facing=-1 / velocity={x:0.0,y:0.0}`；
   泄漏点在产生这批载荷的源码里（`godot.rs:2194-2202` 在**每个窗口开头** drain，最后一个窗口无后继）。
   **限制的诚实性**：报告明写「由冻结读数 + 冻结游戏代码 + 生产源码路径夹出，不是真机因果实验」，与事实相符；我判**结论足以支撑构建**。
   **我自己植入「删掉 release」⇒ 目标测试 `exit 101 @ tests\evidence_battery.rs:4770`。**
2. **②（路由发布）**：角色自起的 `editor_play_scene` 现在会重发布路由，顺序是 install → 确认就绪 → publish，落在适配器层（发布者/采纳者边界清楚）。
   **DR-43 的拒绝语义一个字节没动**：`src/tools/endpoint.rs` 与本批 diff 无关，四条既有拒绝测试全绿，「不回退编辑器」由三条新测试断言。
   我另加的 **X-noclear** 反例（删掉就绪失败时的撤回）**`exit 101 @ game_route_across_processes.rs:471`**——说明「失败即撤回」是被真钉住的。
   披露的副作用（未设路由文件时发布是 no-op、但就绪确认仍跑）**有界**（默认 30 s deadline + 500 ms 轮询 + 端点判死后提前结束）且**失败安全**（撤回 + exit 4）。
3. **③（结构性假阴性）**：观测窗口现在跑在**每个**消耗性窗口之前（常量把规则写成数据，测试读电池真产出的记录顺序），
   窗口**自己**清掉它不驱动的动作，夹具的位移斜坡改成以 `game_axis() > 0.0` 为条件。两条回归钉我用自己的最小复原各自打红：
   **挪回去 `exit 101 @ :4733`、去掉自清 `exit 101 @ :4770`**。
4. **④（D77-A / D77-B）**：常量回到真旧名（`assert_ne!` 的直接钉子把它钉住），两条「旧名映射」断言不再恒真——
   我用「只提旧名的段落」植入打红 `exit 101 @ interaction_contract.rs:317`，并把常量改回新 token 打红 `exit 101 @ :55`；
   `geometric` 已从测试名与点名的消息/注释清除（`--list` 553 条里只有 movement-direction 名），台账与技能的映射行保留。
5. **门与守卫（我自己跑的）**：`cargo clean -p hof-rs`（Removed 11280 files）后 `cargo test --offline` **exit 0**、首行 `Compiling hof-rs v0.1.0`、
   59 行 `test result:` 求和 **546 / 0 / 7**、`--list` = **553**、`cargo fmt --check` **exit 0**、`#[ignore]` **9→9**、**唯一被删的函数名就是任务书点名的改名**；
   代码改动全在 `bf943d0`，`bf943d0..HEAD` 只动 `.spec/**`；六条只读基线我用自己重写的文化序口径复算并命中（`smoke-t6 = c144ef32…7a9c03`）；
   `.workspace/fresh-t11` 与冻结 `A_1` 快照 **11 文件 / 8830 B 逐字节相同**；`runs/**` 我全程零写入。

**必须与结论一起读的两点**：

* **D1（minor）**：任务书 ④ 要求「保留旧名映射行」——映射行确实保留，但**交付技能那句映射没有任何测试钉住其存在**
  （我的 NOMAP 反例：删掉整段映射句后相关测试仍 `exit 0`）。这是 DR-77 验收 **R1** 在技能侧**未闭合**；
  任务书 ④ 的字面三项都做到了，所以我**不判 fail**，但下一批应当补钉。
* **先红的过程不可验**：报告如实披露「没有为每条新测试存档先红日志」。可裁决的是：P1/P4/P5 的植入片段与 `1bed9b1` 的原文**逐字节相同**
  （我的脚本与 `git show` 双向自证），因此那三处的红**就是** DR-77 树上的真实结果；P2/P3/P6 属于「植入红」，只能证明终态非空洞。

---

## 2. 逐项裁定表

| # | 要我验的事 | 裁定 | 我自己的关键证据（全部自产） |
|---|---|---|---|
| 1 | spike 真因、替代项逐条排除、判别力、限制的诚实性、植入红 | **成立** | 我重解冻结载荷：`input_channel_probe` 0 次注入却 `67.3333358764648→173.666687011719`；`input_replay` `move_left` 窗口 `455.999542236328→239.666732788086`（`3.666657787258 px/帧`）；全 raw 唯一 `move_left pressed=false` 带 `target=editor`；交接 `14.666687011719 px = 4.000015 帧`；交互 3×60 帧 `unique_x=1`；第 9 步 `facing=-1 / velocity={0,0}`；黄像素 576 只在 `replay-move_right-before.png`；`godot.rs:2194-2202` 的 drain 语义。植入 P2 ⇒ `exit 101 @ evidence_battery.rs:4770` |
| 2 | 角色自起 play_scene 重发布路由 | **成立** | 读码：`cli_impl.rs` 先 `tools_call_with_reply` → 仅当 `editor_play_scene` 且 `answered()` → `publish_role_started_game_route` → 才打印；实现 `godot.rs:4838-4890` 顺序 install→readiness→publish；我的门里该测试绿；植入 P3（`if false && …`）⇒ `exit 101 @ game_route_across_processes.rs:368` |
| 3 | 就绪已确认、拒绝语义未动、不回退编辑器 | **成立** | 三条新测试断言编辑器从不收 `running_game_*`；四条既有 DR-43 拒绝测试全绿；`src/tools/endpoint.rs` 未在本批 diff 中；我的反例 X-noclear（删撤回）⇒ `exit 101 @ :471` |
| 4 | 披露的副作用有界/失败安全/会不会误导轮次 | **成立（有代价，已披露）** | `wait_for_ready_matching` 有 deadline（默认 30 s，`config.rs:145-154`）+ DR-55 提前结束；`publish_game_endpoint` 在无路由文件时 `Ok(())` 但仍先做就绪确认（`tools/mod.rs:442-448`）；失败 ⇒ `clear_game_endpoint` + `bail` ⇒ exit 4。代价：角色侧多一次最长 30 s 等待，且失败会撤回此前可用路由（见 D2/risks） |
| 5 | 观测窗口先于消耗窗口、自清动作、夹具按游戏轴 | **成立** | `run()` 顺序 `interaction(642) → probe(643) → replay(644)`；常量 `COIN_OBSERVING_BATTERY_STEP`/`COIN_CONSUMING_BATTERY_STEPS`；自清 `:2636-2652`（拒绝写 `STALE_ACTION_NOT_RELEASED`）；夹具 `1318` 行 `self.game_axis() > 0.0`，`game_axis()` `:671-680` 复现「两个都按住⇒0」。P1 ⇒ `exit 101 @ :4733`；P2 ⇒ `exit 101 @ :4770`。**另**：`interaction_evidence` 不读 `self.channel`（只在 `:2101/:2162` 被读）⇒ 提到 probe 前不破坏依赖 |
| 6 | D77-A 常量与真空转 | **成立** | `interaction_contract.rs:43` 是真旧名；`:53-65` 的直接钉子；技能 CRLF 归一化后再分段（`:312-322`）；台账要求同段同时含两名（`:334-345`）；我核实 `TASK-DR73-REPORT.md:114-127` 的更正段只提旧名 ⇒ DR-77 的 FIXONLY 被**真修掉**。P4 ⇒ `exit 101 @ :55`；P6 ⇒ `exit 101 @ :317` |
| 7 | D77-B 旧措辞清除 + 映射保留 | **成立（技能映射未钉存在 = R1 残留）** | `grep -rn is_a_geometric_verdict tests/` = 0；`--list` 实跑 553 条含新名；`grep -n geometric src/adapter/godot.rs` = 0；`TASK-DR73-REPORT.md:706/:713` 与技能 `:163-167` 映射在；P5 ⇒ `exit 101 @ :4834`。技能侧映射的存在性无测试（D1） |
| 8 | 六处植入各自红 + 逐字节回退 + 三处逐字重建 | **成立** | 我重做 P1–P6 全部 `exit 101`，落点与实现者转写同一行号；每处回退后 `bytes_identical / hash_object==HEAD / diff 空 / status 空` 全 True；P1/P4/P5 的植入片段与 `1bed9b1` 原文逐字节相同（脚本 + `git show` 双向自证） |
| 9 | 门、`--list` 一致、只删一个测试名、`ignore` 不变、fmt | **成立** | 我先 `cargo clean -p hof-rs` 再跑：exit 0、首行 `Compiling hof-rs v0.1.0`、59 行求和 546/0/7、`--list` 553、fmt exit 0；我自己的集合差（`git grep -F "fn "`）**REMOVED = 1**（点名的改名）、`#[ignore]` **9→9** |
| 10 | 门在代码所在修订上、后一提交只动文档 | **成立** | `git diff --name-only bf943d0..HEAD` 的 18 个文件全在 `.spec/hof-rs/tasks/**`（无 src/tests/Cargo） |
| 11 | 两个工作区、五条 runs、摘要口径自证与排序承重 | **成立** | 我自己重写的文化序口径命中 6 条（`smoke-t6 = c144ef32…7a9c03`）；码点序会给出 `mario=f622f5b0…/t8=c347bd63…/t10=9ba72fbd…` ⇒ 排序承重、t6 不能担保口径；fresh-t11 对冻结 `A_1` 投影 IDENTICAL；`find runs -newermt "-30 minutes"` = 0 |
| 12 | 冻结规格/台账/引擎/Cargo/未推送/未 stage | **成立** | `PRD-mario.md = 4c81c3a9…`；`git diff 1bed9b1..HEAD -- DECISIONS.md` = 0；嵌套引擎 `fc63af77…` + porcelain 0；`Cargo.toml/lock` 0 行；`origin/master...HEAD = 0 14`；`git diff --cached` 空 |
| 13 | 机器可读块真可解析 + 报告纪律 | **成立** | 我的栅栏感知解析器：DR-78 报告 1 个 json 围栏、`json.loads` 通过、14 顶层键、criteria 11 条全 pass；纪律 1/2/3/4 我逐条核过（作用域、反例、序列化、派生物与正文一致） |

---

## 3. 我自产的植入与反例（8 处，全部逐字节回退）

工具：仓外 `C:\Users\wyl\AppData\Local\Temp\dr78acc\plants_mine.py`（备份在仓外 `dr78acc\bak\`）。
每处流程：读原字节 → 最小改动（只改必要字节、**保持文件原有行尾**）→ 跑**对应**测试取红/绿 → 原字节回写 →
`bytes_identical`（对仓外备份）+ `git hash-object == git rev-parse HEAD:<path>` + `git diff --stat` 空 + `git status --porcelain -uall` 空。

| # | 我的植入 | 落点 | 目标测试 | 结果 | 回退 |
|---|---|---|---|---|---|
| P1 | 复原 DR-77 的电池顺序（观测窗口挪回消耗窗口之后） | `src/adapter/godot.rs` `run()` | `the_coin_observing_window_runs_before_every_consuming_window` | `exit 101` @ `tests\evidence_battery.rs:4733` | 四校验全 True；**植入片段 == `1bed9b1` 原文：True** |
| P2 | 删掉观测窗口的 stale release 整段 | `src/adapter/godot.rs` | `the_observing_window_clears_a_stale_opposing_action_by_itself` | `exit 101` @ `:4770`（`player max x=Some(60.0)`，窗口成旁观者） | 同上 |
| P3 | 让 `editor_play_scene` 的发布分支永不匹配（=`if false && …`） | `src/cli_impl.rs` | `a_role_started_scene_republishes_the_game_route_for_later_processes` | `exit 101` @ `tests\game_route_across_processes.rs:368` | 同上 |
| P4 | 常量退回 `BLOCKED_VERDICT`（DR-77 的 D77-A 状态） | `tests/interaction_contract.rs` | `the_superseded_token_is_the_old_name_and_not_a_copy_of_the_new_one` | `exit 101` @ `:55`（`left == right == "WIN_BLOCKED_UNDER_MOVE_RIGHT"`） | 同上；**== `1bed9b1` 原文：True** |
| P5 | 测试函数名退回 `…_is_a_geometric_verdict` | `tests/evidence_battery.rs` | `the_battery_names_the_blocked_verdict_by_its_movement_direction` | `exit 101` @ `:4834` | 同上；**== `1bed9b1` 原文：True** |
| P6 | 交付技能末尾追加一段只含旧名的判定句 | `src/prompts/skills/godot-dev.md` | `the_godot_dev_skill_retracts_the_impassable_level_claim` | `exit 101` @ `interaction_contract.rs:317` | 同上 |
| **X-nomap**（我加的） | 删掉技能里**唯一**的旧名映射句（` (This … WIN_BLOCKED_UNDER_MOVE_RIGHT.)`） | `src/prompts/skills/godot-dev.md:163-167` | 同名测试 | **`exit 0`（绿）⇒ 技能侧映射无钉住**（D1） | 同上 |
| **X-noclear**（我加的） | 删掉就绪失败分支里的 `tools.clear_game_endpoint().await;` | `src/adapter/godot.rs`（`publish_role_started_game_route`） | `a_role_started_scene_that_never_becomes_ready_is_refused_and_leaves_no_route` | **`exit 101` @ `game_route_across_processes.rs:471`** | 同上 |

**结论**：7 处按设计打红、1 处按设计打绿（用来暴露残留缺口）。所有目标测试都「看着对应代码」——没有空洞的守卫。

**行尾**：被编辑的 8 个文件我逐个数过 `\r\n` 计数并保持原样（`godot.rs`/`mod.rs`/`evidence_battery.rs`/`game_route_across_processes.rs` = LF；
`cli_impl.rs`/`bridge.rs`/`interaction_contract.rs`/`godot-dev.md` = CRLF），与报告 §6.6 一致；我全程**没有**用 PowerShell 改写任何源码。

---

## 4. 我对各问的独立判断

### 4.1 ① spike 的真因与限制

* **真因是 (b)，不是 (a)**：三条独立读数锁定它——(i) 交接处 4.000015 帧的**满速左移**证明「游戏在步进」且「`move_left` 当时仍被按住」；
  (ii) 玩家**恰在注入时刻停住**并连续 180 帧不动，而「只有 `move_left` 被按住」不可能让它停；
  (iii) 整轮游戏通道上没有任何 `move_left` 释放（唯一一处 `target=editor`，而编辑器进程推不动游戏——这一点被 (i) 独立印证：
  如果 call 47 的编辑器侧 release 真能作用到游戏，玩家在被采样前就该停下而不是又走了 4 帧）。
* **判别力**：报告 C1（同轮 0 次注入却位移的对照）是最重要的一条，我复现且认同——它把「我们没看到 X」与「X 不可能」分开了。
  C2 的几何对照在**正确方向**上起作用：交互窗口驱动的是 `move_right`，而同一轮 `move_right` 的逐帧序列穿过 `192…408.333`，
  所以「x=225 处有挡墙」不能解释「按住 `move_right` 却不动」。C3 的 `facing` 论据我另用引擎源码加固（见 D3 的精度说明）。
* **限制是否诚实**：诚实。报告把它放进 risks 与 unverified，并只说结论强度，不声称真机因果；我把「move_right 生效的确切帧」同样列为未知。
* **结论够不够扎实**：够。它的每一步都是读数或冻结源码，唯一没做的是在同一游戏进程里逐帧读 `Input` 状态（离线做不到），
  而现有读数已经把可替代解释逐条排除。**可以在此基础上继续建**。

### 4.2 ② 路由发布、拒绝语义与副作用

* **发布点正确**：角色侧 CLI 从「只采纳」变成「先调工具、再在打印前发布」，发布者/采纳者边界清楚，且顺序与运行时启动同构（install → readiness → publish），
  「未确认就绪不得留下路由」由 `clear_game_endpoint` + `bail` 保证。
* **拒绝语义确实没被放宽**：本批未触碰端口/pid 存活与 DR-43 的拒绝层；四条既有拒绝测试在我的门里绿；
  我的 X-noclear 反例证明「失败即撤回」是被测试真钉住的，不是注释承诺。
* **副作用裁定**：**有界**（`ready_timeout_seconds` 默认 30 s 的 deadline，轮询 500 ms，DR-55 让死端点提前结束）；
  **失败安全**（撤回 + exit 4 + DR-43 措辞）；**不会静默误导轮次**。代价是真实的：每次角色侧 `editor_play_scene` 多一次最多 30 s 等待，
  且**就绪失败会把此前对外可用的路由一起撤回**——这是 DR-71 的正当语义（旧记录不得冒充新游戏），但对「角色在轮中自己做实验」的场景是新的可用性风险，已记入 risks。

### 4.3 ③ 结构性假阴性

* **顺序不变量**现在由「电池真产出的 records」判定，而不是读源码文本——这是正确的形态；我把顺序挪回去实测 `exit 101 @:4733`。
* **自给自足**的论证我加了一条报告没写的**依赖检查**：`interaction_evidence` 不读 `self.channel`，把它提到 probe 之前不会破坏
  「先探测通道、后回放」的能力依赖；probe 的 capability 也不依赖位移（只看 `pressed` 与是否有语义读数）。
* **夹具**按 `game_axis()` 判定，正是 T11 被掩盖的那一步；`starting_held` 让「别人留下的动作」可测。两处回归钉我都独立打红。
* **一处谨慎**：新顺序下 `interaction_evidence` 是**第一个**驱动窗口，它自己的 stale release 在当前顺序里是**防御性**的（没有前驱会留下动作）；
  报告把它说成「spike 真因的修复」略有拔高——真因的**结构性**修复其实是顺序改变，release 是纵深防御。这不影响正确性，但读者应这样理解。

### 4.4 ④ D77-A / D77-B

* 常量回到真旧名，**并且**它的正确性被单独钉住（`assert_ne!` + 两个字面量 `assert_eq!`），这是 DR-77 缺陷的正当补法。
* 两处退化的根因（CRLF 使 `split("\n\n")` 失效、台账取「第一个提旧名段落」）都被真正修掉：
  我核实更正段 `TASK-DR73-REPORT.md:114-127` 确实只提旧名，所以现在的查找必须找到**同时含两名**的映射段，FIXONLY 不再假红。
* `geometric` 从测试名与点名的消息/注释清除；保留的小写 `geometric` 只在**钉子自己在讲被撤回的措辞**（并用 `concat!` 拆开以免自证空洞），我判可接受。
* **未闭合项**：技能侧「映射句必须存在」没有钉子（D1/R1）。

### 4.5 非空洞性、报告纪律

* 六处植入我全部重做，落点与实现者的转写**同一行号**——这是我最看重的交叉验证：说明它的 plants 转写不是事后编的。
* 「三处逐字重建」我用两条独立路径确认（我的植入片段 vs `git show 1bed9b1:<path>` 的字节；脚本自证 + 人工读 diff）。
* **先红日志缺失**：报告如实披露，我判定这是**诚实的降低**（可证明终态非空洞，不能证明过程）。按任务书「区分真先红与植入红并如实报告」的要求，它做到了。
* 机器可读块合法（序列化产出 + 我的栅栏感知 `json.loads` 通过），正文与派生工件数字一致（我用同一批冻结载荷复算到位）。

---

## 5. 未验证项（附理由）

见结论块 `unverified`。要点：

1. **真机行为**：离线硬约束 ⇒ ②③④ 的真机读数不存在；「stale 释放的接受率」「就绪等待的真实时延」「重发布路由后另一进程能否真到达」都不声称。
2. **`move_right` 生效的确切帧**：1 帧采样的冻结载荷只能界定在窗口前 8 次调用内。
3. **先红的过程日志**：没有存档；树里不可验，报告已如实披露。
4. **`fresh-t11` 全树（100 文件）**：没有独立的冻结基线；我验的是工程投影（11 文件/8830 B）与冻结 `A_1` 快照逐字节相同，并复算 100 文件摘要复现实现者记录值。
5. **夹具与真机的同形性**：只读模型与断言，无真机对照。
6. **`.spec/hof-rs/tasks/TASK-SMOKE-T12.md`** 是调度者在 02:19:38 新建的 untracked 文件 ⇒ 「开工时 `git status` 为空」我只能按报告当时的状态采信。

## 6. 我没有检查的

* 没有起引擎、没有跑任何真机轮、没有联网（硬约束）⇒ 不声称真机行为。
* 没有审 `godot-mcp/**` 的内部实现（只验其未改：嵌套仓 HEAD 与 porcelain；另**只**为 spike 的 C3 读过 `character_body_2d.cpp` 的 `move_and_slide` 语义）。
* 没有逐条重跑 DR-77 验收的 17 条判据，也没有重审 DR-76/DR-75 的报告全文。
* 没有独立复核 `tests/evidence_battery.rs` 夹具的**全部**语义（HUD 文本模型、goal 触发半径算术、`299/300` 之类的常量），只核了本批改动点（`:1318` 的轴条件、`game_axis()`、`starting_held`/`disarm_drive`）与两条新测试。
* 没有做密钥熵扫描（沿用模式化检查口径）。
* 没有对 `.workspace/fresh-t11` 的 `.godot/.hoh` 缓存做逐文件对照（只做了工程投影比较与整树摘要复算）。

## 7. 给下一批的建议（按优先级）

1. **补 D1 的钉子**：断言交付技能里存在「旧名 → 新名」的映射句（例如：技能中旧名的每一次出现都必须在同一段给出新名，**且**至少存在一段同时含两名），
   并把 DR-77 R1 的 NOMAP 反例做成常驻的植入清单项。
2. **披露电子化**：把「回包成功却不宣告端点 ⇒ exit 4」与「就绪失败会撤回此前可用路由」写进 `ProjectAdapter::publish_role_started_game_route` 的文档与任务书级说明（D2/risks）。
3. **下一真机轮必须复看的四件事**：① 交互窗口现在第一个驱动，其 raw 采样序列会与 frozen 不同（D4），报告/验收不要用逐值比对；
   ② 角色侧 `editor_play_scene` 的时延（最多 +30 s）与失败时其它角色是否短暂失去路由；③ stale 释放是否总被引擎接受（被拒只会记 `STALE_ACTION_NOT_RELEASED`）；
   ④ `HOH_GAME_ROUTE` 未配置时「发布 no-op 但仍等就绪」这条路径（套件里没有覆盖）。
4. **考虑把 `move_right` 也在观测窗口结束时释放**（或把 `INTERACTION_STALE_ACTIONS` 改成「除驱动动作外全部释放」），让窗口自己不留残留，减少对下一个窗口 drain 的隐式依赖。
5. **清理 D6**：`bridge::tools_call` 已无调用者，或修掉它那句与事实相反的文档注释。
6. **基线口径**：继续用文化序并在文中写明；任何用 Python 默认排序复算的人会把 `mario/t8/t10/fresh-t11` 误判为被动过（t6 是**排序不敏感**的，不能作为口径自证）。
7. 报告 §0 块建议把 `head` 改名为 `implementation_commit_at_gate`（或补一个 `repo_head`），让机器读者不会把 `bf943d0` 当成 HEAD（D5）。

## 8. 机器可读块的合法性检查（本报告落盘后跑的）

```
$ python C:\Users\wyl\AppData\Local\Temp\dr78acc\fencecheck.py .spec/hof-rs/tasks/TASK-DR78-ACCEPTANCE.md
```

（脚本按 ``` 栅栏切块，只对 info string 为 `json` 的块做 `json.loads`，并打印顶层键与 criteria 的 pass 统计。
本报告的 §0 块是先用 `json.dumps(..., ensure_ascii=False, indent=2)` 序列化到仓外文件、再逐字节写进本文件的；结果见文末运行记录。）

### 8.1 本次回读的运行记录（我自己的解析器）

```
$ python C:\Users\wyl\AppData\Local\Temp\dr78acc\fencecheck.py .spec/hof-rs/tasks/TASK-DR78-ACCEPTANCE.md
.spec/hof-rs/tasks/TASK-DR78-ACCEPTANCE.md: fenced blocks = 3 ; json blocks = 1
 json.loads OK ; top-level keys = ["criteria", "defects", "machine_readable_block_check", "my_plants", "object", "risks", "summary", "task", "unverified", "verdict"]
 verdict = "pass"
 criteria = 14 (14 pass true / 0 false / 0 other)
 defects = 6
```

（首次回读发生在 §8.1 落盘之前：json 围栏 1 个、`json.loads` 通过、14 条 criteria 全 `pass: true`、6 条 defects；落盘后再次回读仍通过。本文件除 §0 的 json 块外，另有两个非 json 围栏（§3 的表格说明与本节）——它们都在信息串上被排除，不参与 `json.loads`。）
