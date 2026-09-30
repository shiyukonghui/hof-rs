# TASK-SMOKE-T8-ACCEPTANCE — 真机 T=1 整轮（`runs/smoke-t8`）的独立验收

- 判据来源：`.spec/hof-rs/tasks/TASK-SMOKE-T8.md`（本轮任务书：E1..E6 判据、两条风险旗、三个假绿陷阱、取证要求）；
  被验收对象：`.spec/hof-rs/tasks/TASK-SMOKE-T8-REPORT.md` + `runs/smoke-t8/**`（冻结的轮内证据）；
  对照基线：`.spec/hof-rs/tasks/TASK-SMOKE-T7-REPORT.md`、`runs/smoke-t6`/`runs/smoke-t7`（只读）、`DECISIONS.md` D258/D263/D264。
- 性质：**独立验收、离线、只读为主**。我无上游对话上下文；报告只当**线索**，下列每一条结论都是**我自己从原始工件重算/重读**得到的。
- **硬约束遵守**：未启动 Godot；未碰任何端口（只做 `netstat`/进程表**读取**）；未联网；未调任何模型端点；未跑真机轮；
  未修改 `runs/**`、`.workspace/mario/**`、`.spec/hof-rs/PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`；未 push；未 stage。
  仓外临时物：`C:\Users\wyl\AppData\Local\Temp\t8acc\`（`digest.ps1`、`digest_variant.ps1`、`digest_py.py`、`hash_tree.py`、
  `diff_trees.py`、`compare3.py`、`e3_frames.py`、`e3_calls.py`、`probe_shape.py`、`evidence_shape.py`、`traj_schema.py`、
  `e4_check.py`、`e4_records.py`、`dump_order.ps1`、`dump_order.py`、`ps_order.txt`、`py_order.txt`）。仓内唯一新增文件是本报告。
- **仓库状态与我开工时不同（并发活动，非实现者所为）**：我开工时 HEAD `0f37105`、工作树仅一个未跟踪文件（本报告的被验收对象）。
  我验收期间**调度者**落了 5 个提交（`0f37105`→`40aa6fe`(D265)→`b926a31`(改报告并入库)→`559d531`→`2c47727`），
  收工时 HEAD `2c47727a74e141fc69a91ed2ffe5ff48f316a67c`、`origin/master` 全程 `ce22e181b1619c8fa5cf6adc670f7de48d2a3198`（**ahead 5，未 push**）。
  我验收的是**真机轮的证据**；报告文本此后被调度者追加了 F9（`b926a31`），下文凡引报告处均已核对到该改动的性质（见 §6.9）。
- 摘要口径（我自定并自证）：PowerShell 5.1 / culture zh-CN，`Get-ChildItem -Recurse -Force -File`，
  **仓根相对**小写 POSIX 路径 + 字节长度 + 小写 sha256，`\t` 连接、`\n` 分行、无尾随换行，行序 **`Sort-Object`（文化排序）**，整体 UTF-8 取 sha256。
  **自证**：`runs/smoke-t6` = `c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03`（135 文件，最新 mtime `2026-09-29 02:32:01`）✓。

---

## 0. 结构化结论

```json
{
  "verdict": "fail",
  "verdict_scope": "fail 只针对**报告的诊断结论与一处电池假绿**，**不是**针对真机轮的六条产品级判定。E1..E6 六条我逐条独立复核，全部与报告一致；F1/F2 两个 major 发现都真实存在；守卫/基线/禁区自证全部成立。判 fail 的三个实质项是：①E3 的头号论断『左移被实测证否』不成立（最可能是**注入时序假象**，不是产品缺陷）；②E1 的根因不完整——被拒证据同时缺 `execution_records[*].type` **和** `claim_id`，只补 `type` 仍会被拒；③确定性电池的 `input_replay` 用**整向量**不等判『有位移』，move_left 因重力改了 y 而被判 ok=true（掩蔽假绿）。**无需重跑真机轮**（证据完好），需要的是更正报告诊断并据此收窄下一批的修复范围。",
  "criteria": [
    {
      "id": "E1",
      "pass": false,
      "evidence": "产品级 not_met，**与报告一致**；原因也**是**报告写的『Tester 证据被 schema 拒』，但该原因**不完整**（见 defects D2）。我自实现 `src/runtime/policy.rs:68-97` 的 `hash_tree`（排除集 `[.hoh,.git,.godot,.import]`，`a.0.cmp` 逐字节排序，`rel\\n{len}\\n{bytes}\\n` 流），三棵树重算：A_0=`fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c`（17 文件/16113 B，**与 smoke-t7 记录逐字相同**）、A_1=候选树=`.workspace/mario`=`1f3d20ed50b472e422832c4fa2c8d7b72ae04ee11fa4c5ace65fb20a43997fd8`（17 文件/18397 B）；A0→A1 差 3 个**工程文件**（`scenes/main.tscn` 7434→9139 B、`scripts/main.gd` 1920→2344 B、`scripts/player.gd` 2076→2231 B），增删各 0。运行时的原始拒绝在 `runs/smoke-t8/iter-1/result.json`（`ok=false`、`failed_role=tester`、`reason=schema_failure`、`issues[0].message=\"evidence does not match the required structure: missing field \\`type\\`\"`），产生它的代码是 `src/model.rs:87-94`（`#[serde(rename=\"type\")] kind: ExecKind`，无默认值）经 `src/runtime/schema.rs:284-288` 的 `serde_json::from_value::<EvidenceBundle>`；被拒工件 `runs/smoke-t8/iter-1/candidate/.hoh/evidence.json` 的每条记录 `exec_keys=['observation','path']`（对照 smoke-t7 被接受的 `['candidate_id','observation','path','type']`）。"
    },
    {
      "id": "E2",
      "pass": true,
      "evidence": "实质 met，**与报告一致**。`runs/smoke-t8/iter-1/candidate/.hoh/deterministic/deterministic.log`：『11 step(s), 11 of them ok; launchable=true (battery pass(es): 2, repair_retry_used=true)』；`editor_errors_baseline` 唯一一行是引擎横幅 `[MCP] capture=off …`（`raw/editor_errors_baseline.json`，`count=1`、`source=editor_log`）；`play_scene_ready` 53 节点；闸门三步（`src/adapter/mod.rs:23-27`：`editor_errors_baseline`/`play_scene_ready`/`engine_identity`）第二遍全 ok。**持久化确实丢了它**：`result.json.battery_passes=[]`、`result.json.artifact_gate={applicable:false,launchable:true,reasons:[\"no launchable gate was evaluated for this iteration\"]}`、`meta.json.artifact_gate.reasons=[\"the round failed; no artifact gate was produced\"]`——但**报告 §3.1 说的『只有 .workspace/mario/.hoh 留证』不准确**：同一份 battery 原文在**冻结的** `runs/smoke-t8/iter-1/candidate/.hoh/deterministic/**` 里也有（见 D6）。"
    },
    {
      "id": "E3",
      "pass": false,
      "evidence": "产品级 not_met（合取判据），**与报告一致**；但报告的**构成**只有一半成立。我从 `raw/input_replay.json` 独立抽出四个 `channel=game_process` 四元组（全部 `tool=running_game_get_node_property_samples`）：右移 60 帧 `188.333374→404.666382`（dx `+216.333008`，`3.666661 px/帧`×60=`219.9997 px/s`，与 A_1 `scripts/player.gd:3 @export var speed: float = 220.0` 逐字吻合）；跳跃 30 帧 y `269.996124→峰值 214.273911@f17→242.607254`（自地面起升 69.7 px；`v²/2g=430²/2800=66.04 px`、到顶 `430/1400=0.307 s≈18.4 帧`，与 `jump_velocity=-430`/`gravity=1400` 自洽）；`move_left` 60 帧 x **恒为 584.363037**、y `270.940613→283.994659`。⇒ 右移与跳跃**成立**；**左移『被证否』不成立**（见 defects D1：move_right 从未在游戏进程内被释放，`Input.get_axis(\"move_left\",\"move_right\")` 返回 0）；可交互对象（F10）与终点/胜负（F13）仍无观测。故 E3 仍 not_met，但报告把它读成『左移=产品缺陷』是错的。"
    },
    {
      "id": "E4",
      "pass": false,
      "evidence": "前提缺失故 not_met，**与报告一致**。轮内**没有** `runs/smoke-t8/iter-1/evidence.json`（只有被拒的 `candidate/.hoh/evidence.json`）。内容层我独立复算：8 条 verified 全带 `execution_records`、**38 条被引路径 38/38 实存**（相对 `iter-1/candidate` 逐条 `os.path.exists`）、17 条 gap 全带 `player_impact`+`recommended_update`、`gap_records_missing_fields=0`。⇒ 对一份被运行时拒绝的工件不能宣布达标，报告的分栏正确。"
    },
    {
      "id": "E5",
      "pass": true,
      "evidence": "met（强），**与报告一致**，并比报告更强。用运行时自己的 `hash_tree`（不是报告自造的脚本）：候选树 = 存储 A_1 = 现 `.workspace/mario` 工程树 = `1f3d20ed…`（各 17 文件/18397 B）；全文件集三路比对只差 **hash 排除路径**（`.godot/**`、`.hoh/**`），工程集**差异 0**。Tester 期间无工程写入：`.workspace/mario` 与候选的 17 个工程文件 mtime 全部 ≤ `2026-09-30 07:19:25`，而 Tester 阶段是 `07:31→07:58`。诚实边界：内容哈希等价于内容未变，不排除同长度同内容的替换（风险极低）。"
    },
    {
      "id": "E6",
      "pass": true,
      "evidence": "内容层 met，**与报告一致**。我逐条读 8 verified + 17 gap：无一条未达成被写成 verified（G1..G17 覆盖左移/释放/二跳/朝向/相机/墙/敌人/金币/问号砖/砖块/终点/失败/重开/时长/长时稳定，与 verified 的 N1/P2/P3/F1右移/F2跳/N2/F16/F5 不重叠）。**保留意见（与报告一致但更重）**：G1 的 `player_impact` 写『The player cannot move left **at all**』，在 D1 的时序解释下是**未经证实的因果断言**；其 observation 文字（60 帧 x 不变）本身精确。另 V3 的 `verified` 由『可达性 + 注入被接受』撑起（见 risks R1），报告已如实标注。"
    }
  ],
  "defects": [
    {
      "id": "D1",
      "severity": "major",
      "what": "报告 §2.1/§2.2 与 §0 的旗舰论断『`move_left` 被实测证否（左移不产生位移）』**不成立**：最可能是**注入时序假象**，而非产品缺陷。理由是三条原始事实的合取：①轮内**所有**游戏通道注入都是 `pressed=true`（`raw/input_replay.json` 的 `running_game_play_input_recording` 调用 #2/#10/#18/#26 与 `run_test_scenario` 的 input 步全部 pressed=true），**游戏进程从未收到过任何 release**——四个 release 全部走 `editor_simulate_input_action`（#8/#16/#24/#32），而报告自己（§2.1）承认编辑器侧『cannot drive the game』；②`jump` 窗口的 x **仍在以 3.6667 px/帧 增加**（470.696→577.030，calls[22]），证明采样时 `move_right` **仍被按住**；③A_1 `scripts/player.gd:28-32` 是 `var dir := Input.get_axis(\"move_left\",\"move_right\")` + `velocity.x = dir * speed`，左右完全对称，`project.godot:28-69` 两侧绑定也对称（physical_keycode 4194319/4194321）。三者合起来唯一自洽的解释：游戏进程内 `move_right` 与 `move_left` **同时按住** ⇒ `get_axis` = 0 ⇒ `velocity.x=0` ⇒ x 恒定——这不是产品缺陷。引擎侧也支持：replay 用 `Input::get_singleton()->parse_input_event(event)`（`godot-mcp/godot/modules/mcp_server/tools/running_game_input.cpp:532`，`pressed` 由事件携带，`:487-505`），**没有自动释放**。报告自己的独立实验 #2（`runs/smoke-t8-experiment/e3_attrib_console.txt`）里还留着反证：D 窗口结束 x=375.333、F 窗口开始 x=371.666，**正好一帧 −3.667 px 的左移**发生在采样窗口边界——与『左移完全无效』矛盾，与『左移有效但被仍按住的右移抵消』一致。⇒ 该缺陷**不改变 E3=not_met**，但会让下一批把根因错误地投向 `project.godot`/`player.gd`。",
      "reproduction": "`python` 读 `runs/smoke-t8/iter-1/candidate/.hoh/deterministic/raw/input_replay.json`：对每个 `running_game_get_node_property_samples` 调出 `quadruple` 与 `samples`，逐帧打印（我用仓外 `e3_frames.py`）；核 `calls[22]` 的 x 单调递增、`calls[30]` 的 x 逐帧相等；`grep -c '\"pressed\": false' ` 在**游戏通道**的工具载荷里为 0；读 `godot-mcp/godot/modules/mcp_server/tools/running_game_input.cpp:487-543` 确认无自动释放；读 `runs/smoke-t8/versions/1f3d20ed…/scripts/player.gd:28-32`。"
    },
    {
      "id": "D2",
      "severity": "major",
      "what": "E1 的根因诊断**不完整**：报告只写『缺 `type`』，但被拒工件**同时缺 `claim_id`**——`src/model.rs:104-108` 的 `ClaimRecord.claim_id: String` **没有** `#[serde(default)]`，而 t8 的每条记录 keys 是 `['claim','execution_records','requirement','status','type']`。serde 在解 `execution_records` 时先撞上嵌套的 `type` 而提前返回，所以运行时报的是 `type`；**只把 `type` 补上，下一次就会被 `missing field \\`claim_id\\`` 拒**。再者 `src/prompts/tester.md:53-68` 的输出契约里**既无 `type` 也无 `claim_id`**（全文只有 `:44` 提到 `path`），所以 F2 的『提示词形状块不完整』比报告写的更宽。",
      "reproduction": "`python` 读 `runs/smoke-t8/iter-1/candidate/.hoh/evidence.json` 打印每条记录的 keys（我仓外 `evidence_shape.py`）；读 `src/model.rs:87-94`/`:104-108`；读 `src/prompts/tester.md:44-68`；`grep -n 'claim_id' src/prompts/tester.md` → 0 命中。serde『报告第一个缺失字段』这一层是**代码阅读推断**（未执行编译）。"
    },
    {
      "id": "D3",
      "severity": "major",
      "what": "确定性电池的 `input_replay` 步骤存在**掩蔽假绿**：`src/adapter/godot.rs:1946` 用 `quadruple[\"before_position\"] != quadruple[\"after_position\"]` 判『有没有移动』，而 `move_left` 的四元组 before/after 的 **y 不同**（270.940613→283.994659，角色在下落），于是 `moved=true`，`expect_movement=true`（`:1835`）也拦不住 ⇒ 一个**水平完全不动**的动作被记为 `ok=true`，整轮 11/11。方向无关的整向量比较 + 重力 ⇒ 假绿。报告未提这一点（它只把 move_left 写成 QA 的 gap）。",
      "reproduction": "`src/adapter/godot.rs:1831-1836`（动作表 `(\"move_left\",\"move_left\",60,true)`）与 `:1945-1972`（moved 判定）；`runs/smoke-t8/iter-1/candidate/.hoh/deterministic/deterministic.log` 里 `input_replay` 的 `record.ok=true`；同一文件的 `move_left` 四元组。"
    },
    {
      "id": "D4",
      "severity": "minor",
      "what": "报告 §5 对照表把 `repair_retry_used` 的 t8 值写成 **true**（引 `deterministic.log` 的 battery 级 `repair_retry_used=true`），而同一轮的 `result.json.repair_retry_used` 是 **false**。两者是不同层（电池内部修一遍 vs 轮级定向修复），报告未区分，容易被下一批当同一指标。",
      "reproduction": "`runs/smoke-t8/iter-1/result.json:222` 与 `runs/smoke-t8/iter-1/candidate/.hoh/deterministic/deterministic.log:1`。"
    },
    {
      "id": "D5",
      "severity": "minor",
      "what": "报告 §6.4 引 `git rev-parse origin/master` = **`079cf82`** 与实际不符：真值 `ce22e18…`（D263 的推送点；`git reflog show origin/master` 显示 `079cf82 → ce22e18 update by push`）。『未 push』的结论仍成立（轮内 HEAD `0f37105` 在 `ce22e18` 之后，本地领先）。疑为把任务书/命令里的 `079cf82..HEAD` 起点误当远端值。",
      "reproduction": "`git rev-parse origin/master`；`git reflog show origin/master`；`git log --oneline ce22e18..HEAD`。"
    },
    {
      "id": "D6",
      "severity": "minor",
      "what": "报告 §3.1/§0 说 E2 的 verdict『只有在 `.workspace/mario/.hoh/deterministic/**`（一个会被下一轮隔离的目录）留证』——**偏绝对**：同一份 `deterministic.log`/`battery.json`/`raw/**` 也在**冻结的** `runs/smoke-t8/iter-1/candidate/.hoh/deterministic/**` 里（我逐字节比过 `raw/input_replay.json` 两侧 md5 相同：`401d575194abf61cb3b98da8f9d710a6`）。报告真正成立的那半（`result.json`/`meta.json` 读不到）我已独立确认。",
      "reproduction": "`md5sum .workspace/mario/.hoh/deterministic/raw/input_replay.json runs/smoke-t8/iter-1/candidate/.hoh/deterministic/raw/input_replay.json`。"
    },
    {
      "id": "D7",
      "severity": "info",
      "what": "报告 §6.4 的『`git status --porcelain -uall` 为空』在它写下报告后就不再成立（报告自身当时是未跟踪文件）；且 `runs/**` 被 `.gitignore` 排除 ⇒ 外层 `git status`/`git diff` 对**本轮全部证据**都是空判（与任务书陷阱③同族）。判据应改用目录摘要（我即如此）。",
      "reproduction": "`.gitignore` 含 `runs/`；我开工时 `git status --porcelain -uall` 只有 `?? .spec/hof-rs/tasks/TASK-SMOKE-T8-REPORT.md`。"
    },
    {
      "id": "D8",
      "severity": "info",
      "what": "仓库根存在一个名为 `%DST%` 的**受跟踪目录**（`green/`、`red/`，7 个文件，mtime `2026-09-24 00:35`），形似某次未展开变量的命令产物。它**早于本轮 6 天**，不是本轮的临时物，故不影响本轮判定；仅登记为工作树内的历史异物。",
      "reproduction": "`git ls-files '%DST%' | wc -l` = 7；`find . -maxdepth 1 -newermt '2026-09-30 06:00'` 不含它。"
    },
    {
      "id": "D9",
      "severity": "info",
      "what": "报告里的『提示词↔shell』计数（`bash -c` 120→0、`$HOH_`/`%HOH_` 33/1→4/162、首个成功 `hoh tools call` 34→15）是**定义相关**的。我用更粗的口径复核方向：`developer.attempt1.json` 中 `bash -c` 出现次数 t7=**360** → t8=**0**；t8 的 `$HOH_`=16、`%HOH_`=567；`runs/smoke-t8/TOOLS.md` 单花括号 `{HOH_*}`=3、`%HOH_*%`=6。**方向一致，数字不可逐一对上**（口径不同），这些不是 E1..E6 的判据。",
      "reproduction": "`grep -o … | wc -l` 于 `runs/smoke-t7/iter-1/traj/developer.attempt1.json`、`runs/smoke-t8/iter-1/traj/developer.attempt1.json`、`runs/smoke-t8/TOOLS.md`。"
    }
  ],
  "risks": [
    "R1 风险旗①的实现被证实：`raw/input_channel_probe.json` 的 `channel.capability=GAME_INPUT_CHANNEL_OK` 而 `axis_before=axis_after=null`、`moved_while_pressed=false`；`src/adapter/godot.rs:1359` 允许 `game_process_reachable` 单独抬到 OK，与同文件 `:1206-1207` 的文档（『with a semantic reading arriving』）矛盾。QA 的 verified#3 正建立在这条可达性记录上（措辞限于『绑定 + 交付』）；行为判据未被污染，但『绿』仍不可信。",
    "R2 失败轮里 `meta.json.artifact_gate.launchable=true` 且 `ArtifactGate::is_open()`（`src/model.rs:301-303`）只看 `launchable`、不看 `applicable`（生产代码零调用）⇒ 任何未来只看 `launchable`/`is_open()` 的读者会误读失败轮。退出码路径本身安全（`cli_impl.rs:701-706` 先看 `failure_exit_code`）。",
    "R3 失败路径的 `result.json` 是存根：`candidate_id/version_id=null`、`evidence_diff` 三段全空、`battery_passes=[]`、`prd_coverage` 全 0、`repair_retry_used=false`——**读 `result.json`/`meta.json` 无法知道本轮真的产生了 3 文件增量与 11/11 电池**（根因：`src/runtime/run_loop.rs:1355-1369` 传 `EvidenceDiff::default()` 且不传 battery 结果）。严重性：对本轮**可复现性/审计**为 major（但轮目录里 `versions/`、`candidate/.hoh/deterministic/**`、`traj/`、`logs/` 仍在，证据可重建）；而 `runs/**` 不入 git ⇒ 这些证据只存在于工作树。",
    "R4 活体工作树 `.workspace/mario` 的目录摘要**不稳定**：我复算 148 文件得 `b2235abc4e4c842f4ef355c34cbf0381b937940de9e4803dba61b098a85d2128`，与报告的收工值 `1e45948f…1986` 不同——差在编辑器自身于 `2026-09-30 08:09:00` 重写 `.godot/editor/*.cfg`（3 个文件）。**工程树不受影响**（仍 `1f3d20ed…`）。⇒ 任何『某树未变』的断言只能用冻结的候选/版本树，或显式排除 `.godot`。",
    "R5 报告文本已不再是单一作者产物：调度者在 `b926a31` 为其追加了 F9（task prompt/TOOLS.md 头部的单花括号 `{HOH_*}` 占位符）并改了若干措辞。F9 的落点我抽查成立（`runs/smoke-t8/TOOLS.md` 有 3 处 `{HOH_*}`、6 处 `%HOH_*%`，`runs/smoke-t8/**` 共 48 处单花括号 HOH 记号），但这部分**不是本轮实现者的自证**，验收时应分开记账。",
    "R6 本轮的 E1/E2/E3 关键证据全部在 `runs/**`（gitignored）；没有入库的不可篡改摘要。任何后续轮次/清理都可能让这些证据消失。"
  ],
  "unverified": [
    "U1 `player.gd` 当时**是否真的短暂处于**调用 `_update_facing_visual` 的中间态：mtime 只能证明 07:19:25 之后未再写，不能证明中间态存在。**现象已实测**（日志读到的错误行指向一个在 A_0/A_1 都不存在的函数名），**机制是推断**。",
    "U2 `move_left` 的『抵消』解释是强推断而非直接观测：游戏侧 `input_axis` 属性读不到（`running_game_get_node_property_samples` 每帧 `null`；`run_test_scenario` 的 assert 直说节点没有该属性），所以我没有『当时 axis=0』的读数，只有『右移在 jump 窗口仍在生效』+『引擎 replay 不自动释放』+『player.gd 对称』的合取。",
    "U3 `running_game_*` 工具在**编辑器端点**上不存在这一条（报告 §6.1 的 live probe）：我只读到路由代码（`src/tools/endpoint.rs:38-44`）与工件内的不对称证据（编辑器 InputMap 无 move_*、游戏 `in_test_map:true`），**未重跑端点探测**（离线约束）。",
    "U4 『首个成功 `hoh tools call` 在第 15 步』与报告 §4.2 的全部计数：未用报告之外的严格口径重算（见 D9）。",
    "U5 D2 中『补上 `type` 后下一个错误会是 `claim_id`』：由 serde 派生语义推断（`claim_id` 无 `#[serde(default)]`），**未执行编译验证**。",
    "U6 引擎二进制自轮次以来未变：嵌套仓 `status` 0 行、无 2026-09-30 之后的文件、sha256 与 meta.json 记录一致（`08483088…e9e6a`）——但这是**现在**的读数，轮内当时的一致性由 meta.json 记录背书。",
    "U7 报告中未经我复核的少数转述（例如 t7 的 `E_1` 结构、DR-64/DR-67 的历史数字）——我只核了与 E1..E6 判定相关的部分。"
  ]
}
```

---

## 1. 逐条判据表

| 编号 | 我的判定 | 与报告一致？ | 我的关键证据（自产） |
|---|---|---|---|
| **E1** | **not_met** | 一致 | A_0/A_1 由我重实现 `policy.rs::hash_tree` 重算（`fc78d299…` / `1f3d20ed…`，差 3 个工程文件）；`result.json` 的原始 schema 拒绝 + `model.rs:87-94` + `schema.rs:284-288`。**原因不完整**（D2） |
| **E2** | **met（实质）** | 一致（但 D6 收窄一处） | `candidate/.hoh/deterministic/deterministic.log` 11/11、`launchable=true`；`editor_errors_baseline` 仅 1 行横幅；`play_scene_ready` 53 节点；`result.json`/`meta.json` 覆写成 `not_applicable` |
| **E3** | **not_met（右移+跳跃成立；左移不成立）** | **判定一致，构成不一致** | 四个 `game_process` 四元组逐帧抽值；`3.666661×60=219.9997 px/s`；跳跃峰值自洽；左移时序假象（D1） |
| **E4** | **not_met（前提缺失）** | 一致 | 无 `iter-1/evidence.json`；被拒工件内容层 38/38 路径实存、8 verified 全带记录、17 gap 全带两字段 |
| **E5** | **met（强）** | 一致（更强） | 运行时 `hash_tree` 三树同 `1f3d20ed…`；全文件集差异仅 `.godot/**`/`.hoh/**`；工程文件 mtime ≤07:19:25（Tester 07:31→07:58） |
| **E6** | **met（内容层）** | 一致（保留更重） | 8 verified 与 17 gap 无重叠；G1 的 `player_impact` 是未证因果（D1） |

---

## 2. 我自己的抽取与算术

### 2.1 E1 的树哈希（重实现 `policy.rs:68-97`）

```
A_0  versions/fc78d299…  files=17 bytes=16113 digest=fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c
A_1  versions/1f3d20ed…  files=17 bytes=18397 digest=1f3d20ed50b472e422832c4fa2c8d7b72ae04ee11fa4c5ace65fb20a43997fd8
候选 iter-1/candidate      files=17 bytes=18397 digest=1f3d20ed…（同 A_1）
活体 .workspace/mario      files=17 bytes=18397 digest=1f3d20ed…（同 A_1）
planner-view              files=17 bytes=16113 digest=fc78d299…（= A_0）
A0→A1: removed=0 added=0 modified=3
   scenes/main.tscn  7434 B (sha 381066c05c1a…) -> 9139 B (sha 42c525f39ac0…)
   scripts/main.gd   1920 B (sha 9d8da90c6d66…) -> 2344 B (sha 26bd5ea69cd7…)
   scripts/player.gd 2076 B (sha b206397c8dff…) -> 2231 B (sha b2936105212e…)
```
排除集 = `[".hoh", ".git", ".godot", ".import"]`（`src/runtime/policy.rs:39-47` + `config/hoh.yaml:47`）；排序 = `a.0.cmp(&b.0)`（字节序）；流 = `relpath\n{len}\n{bytes}\n`。
**A_0 与 smoke-t7 报告记录的 `fc78d299…` 逐字相同**（T7 报告 §0/§1.1/§1.3）⇒ 基线身份未漂移。

### 2.2 E3 的逐帧数值（原始回包，非报告转述）

| 调用 | 动作 | 帧 | x 首→末 | dx | dx/帧 | 合 `speed=220`/60Hz？ | y |
|---|---|---|---|---|---|---|---|
| candidate `raw/input_replay.json` calls[6] | move_right | 60 | 188.333374 → 404.666382 | **+216.333008** | 3.666661 | **219.9997 px/s ✓** | 283.998993 恒定 |
| calls[14]（"release" 窗口） | move_right | 10 | 422.999664 → 455.999573 | +32.999908 | 3.666656 | 219.9994 ✓ | 283.998993 恒定 |
| calls[22] | jump | 30 | 470.696106 → 577.029663 | +106.333557 | 3.666674 | 220.0005 ✓（**右移仍按住**） | 269.996124 → **214.273911 @f17** → 242.607254 |
| calls[30] | move_left | 60 | 584.363037 → 584.363037 | **+0.000000** | 0 | 0 | 270.940613 → 283.994659（落地） |

- 跳跃自洽性：自地面（283.998993）起的峰值高度 `283.998993−214.273911 = 69.72 px`；由 A_1 常量 `jump_velocity=-430`、`gravity=1400` 得 `v²/2g = 66.04 px`、到顶 `0.307 s ≈ 18.4 帧`（观测 f17）⇒ 与游戏自己的代码路径自洽（离散积分/采样对齐的少量偏差）。
- `channel=game_process` 是 `running_game_get_node_property_samples` 的**四元组包装字段**，由 `src/adapter/godot.rs:1708/1916` 依工具名打上；路由由 `src/tools/endpoint.rs:38-44` 的**工具名前缀**决定（`running_game_* ⇒ 游戏端点`）。⇒ 来源是**游戏进程内语义工具**（不是探针、不是静态检查、不是拼装 GDScript）；但**诚实边界**：`channel` 字符串本身是 harness 赋的，不是引擎回的，其正当性来自路由代码 + 同一文件里编辑器侧 `editor_get_input_actions` 报 `in_input_map:false` 而游戏侧 `run_test_scenario` 报 `in_input_map:true` 的**不对称呼应**。
- 风险旗纪律已执行：`raw/input_channel_probe.json` 的 `GAME_INPUT_CHANNEL_OK` **未被**我用作任何行为证据。

### 2.3 摘要口径（自证 + 文化排序实测）

| 树 | 文件 | 我的摘要（culture） | 备注 |
|---|---|---|---|
| `runs/smoke-t6` | 135 | `c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03` | **= 任务书要求的自证值**；最新 mtime `2026-09-29 02:32:01` |
| `runs/smoke-t7` | 115 | `6e4c1595735c3cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7` | 与 DR-66/67 验收记录逐字一致 |
| `runs/smoke-t8` | 358 | `6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7` | 与报告 §6.3 一致 |
| `.workspace/mario` | 148 | `b2235abc4e4c842f4ef355c34cbf0381b937940de9e4803dba61b098a85d2128` | **≠ 报告收工值** `1e45948f…`：编辑器 08:09:00 重写 `.godot/editor/*.cfg`（R4） |

**文化排序是口径的一部分——我实测证实**：对 `runs/smoke-t8`，把 `Sort-Object` 换成序数排序，摘要变为 `c347bd637ab481b1ec357cbb534c1330bad18cfab85c113038fa0878e6b3d3f5`（Python 码点序亦然）；
两者只有 **3 对**相邻项次序不同（`…/evidence0.json` 一族与 `…/scratch/o_actions.txt`、`…/args/mon_player.json` 等 `_` 参与比较处）。
诚实补充：对 **`runs/smoke-t6`** 两种排序结果**相同**（都 `c144ef32…`），所以『Python 序数排序会同数不同摘要』这一说法**只在 t8 这类含分歧路径的树上成立**，不具普遍性。

---

## 3. 对各个头号问题的独立判断

### 3.1 E1 为何 not_met：**是报告写的原因**（但原因不止一个）

- schema 拒绝是真的、可复现的：`result.json.issues[0]`、`tester.attempt1.log.artifact_valid=false`、控制台 `hoh: schema failure for role Tester after 1 attempt(s)`、`runs/smoke-t8/exit_code` = `"3\n"`、`meta.json.exit_code=3`（三方一致）。
- 产生拒绝的**文件:行**：`src/model.rs:87-94`（`ExecRecord.kind` 无默认值）→ `src/runtime/schema.rs:284-288`（serde 反序列化）→ 错误串逐字相同。
- 反馈回路是通的：`traj/tester.attempt1.json` 里同一错误消息在 msg[116]/[215]/[225]/[252]/[254]/[271]/[291]/[293]（≥8 处）反复出现，模型始终没把 `type` 放进 `execution_records`。⇒ 报告『模型把 type 当 claim 层字段』的推断合理。
- **但**：D2 说明还缺 `claim_id`；且 `src/prompts/tester.md` 的输出契约里连 `type` 都没写（`:53-68` 是空数组），`EVIDENCE_SKELETON`（`src/model.rs:436-465`）只在 `schema.rs:241` 作为 **retry context** 下发，而 `schema.rs:243-245` 的 `if limits { break; }` 在 attempt1 `LimitsExceeded` 时直接跳出 ⇒ 骨架一次也没送到模型。报告 1–7 条编号全部复核成立。

### 3.2 E3 的 `move_left`：**不是产品缺陷，是注入时序假象**（决定性反驳见 D1）

报告给的两条支撑（轮内 60 帧 + 自造实验 #2 的 40 帧）**都发生在 `move_right` 仍被按住的上下文里**；它自己的实验 #2 里还留着『D 与 F 窗口之间 −3.667 px』这一条左移**有效**的痕迹。所以：`move_left` 的正确读法是 **not established（未证）**，而不是 **falsified（被证否）**。

### 3.3 E3 的来源确实是游戏进程内语义工具

见 §2.2 的诚实边界。要点：`running_game_get_node_property_samples` 的路径名是运行中的 `/root/Main/Player`，帧序列由引擎按帧产出（不是 harness 拼的），并且整轮里同一份 raw 还并存着**编辑器侧**的 `editor_simulate_input_action`（被明确标 `EDITOR_SIDE_INJECTION`，且 `in_input_map:false`）——两条通道在同一文件里可区分。

### 3.4 E2：**实质 met，但只在概要工件里丢失**

- 成立：第二遍电池三步全 ok（`editor_errors_baseline` count=1 仅横幅、`play_scene_ready` ok、`engine_identity` ok）⇒ `launchable=true`（`src/adapter/mod.rs:41-56`）。
- 丢失：`result.json`/`meta.json` 被失败路径覆写（`run_loop.rs:138-151` 的 `failed_run_summary` + `cli_impl.rs:604-613/720-739` 的 `finalize_run`）。
- 报告『E2 的 evidence 只在 `.workspace/mario/.hoh`』不准确（D6）：`runs/smoke-t8/iter-1/candidate/.hoh/deterministic/**` 是冻结留存。

### 3.5 E5：三树字节级同一（我自己重算，比报告更强）

候选树 = 版本树 = 活体工程树 = `1f3d20ed…`（运行时自己的算法）。全文件集比对差异**只**落在 hash 排除路径（`.godot/**` 85 文件、`.hoh/**` 运行时目录）。装配时间线：planner 06:56:57 结束 → developer 三次 attempt（a1 150 步、a2 25 步 wrap-up、a3 60 步 repair）→ 07:31:05 落盘 → Tester 07:31→07:58。工程写入全部 ≤ 07:19:25。

### 3.6 F1（启动闸门假阴性）**成立**

- 第一遍 07:19:33 读到 `count=2`，其中 `ERROR: res://scripts/player.gd:31 - Parse Error: Function "_update_facing_visual()" not found in base self.`（原文留在 `traj/developer.attempt3.json` msg[1] 的修复上下文里；我另核：`runs/smoke-t8-experiment/first_pass_gate_context.txt`）。
- 该函数名在 **A_0 与 A_1 的 `player.gd` 里都不存在**；07:19:25 的 `player.gd` 第 31 行调 `_apply_facing_visual()`、第 41 行定义它（我 grep 两侧版本与活体文件，`_update_facing_visual` 0 命中）。
- 冻结副本的第二遍（07:31）`count=1`（`raw/editor_errors_baseline.json`，`source="editor_log"`）。`editor_get_errors` 读的是**编辑器日志文件**，所以中间态错误行会留到滚出为止 ⇒ 假阴性成立。代价：`developer.attempt3.log` 的 `notes = "launch_gate_repair: …"`，60 步 / 4,022,698 tokens / 684,335 ms。
- **该修复对工程树零写入**（我独立证明）：17 个工程文件的 mtime 全部 ≤ 07:19:25（repair 窗口 ≈07:19:33→07:30:57 之后没有任何工程写入）；且 A_1 内容与 repair 后第二遍闸门读到的一致。

### 3.7 F2（Tester 证据形状契约缺口）**成立，但比报告写的更宽**

见 D2。三处已复现：`model.rs:436-465` 骨架内容、`schema.rs:241`（仅 retry 上下文）、`schema.rs:243-245`（limits 抑制重试）、`prompts/tester.md:53-68`（形状块只有空数组）。补充：**`claim_id` 也缺**。

### 3.8 证据落点问题（`result.json` 在失败路径不完整）**成立，严重性 major（可审计性）**

`result.json`：`ok=false / failed_role=tester / reason=schema_failure / candidate_id=null / version_id=null / evidence_diff={added:[],modified:[],removed:[]} / battery_passes=[] / prd_coverage 全 0 / repair_retry_used=false`。一个只读 `result.json` 的人会得出『本轮什么都没有』——而事实是本轮**真的**有 3 文件增量、11/11 电池、A_1 快照。根因 `run_loop.rs:1355-1369`（`EvidenceDiff::default()`，且 `finalize_failure` 不接 battery 结果）。**缓解**：`runs/smoke-t8/versions/index.json`、`iter-1/candidate/.hoh/deterministic/**`、`traj/`、`logs/`、`exit_code` 都在，证据可重建；但 `runs/**` 不在 git，且 `meta.json` 的 `launchable=true` 反向误导（F4/R2）。

### 3.9 两个 major 发现的处置与『修复未写入』

- F1 与 F2 我都独立复核为真（§3.6/§3.7），且都指向**运行时/提示词**的缺口，而不是模型单方面的错。
- repair attempt3 **真的没写工程**（mtime 普查 + A_1=候选=活体），所以报告『该修复零写入』成立，代价是纯浪费（4.02M tokens / 11 分 24 秒）。

---

## 4. 三个假绿陷阱（我自己重做）

| 陷阱 | 我的实测 | 正确读法 |
|---|---|---|
| ① `git diff` 对不存在 pathspec 不报错 | `git diff --stat -- definitely/not/a/real/path` → 空输出、`exit=0` | 空 + 0 与『没变化』不可区分；断言某路径未改前必须 `git ls-files <path> | wc -l > 0` |
| ② `cmd` 里 `^` 被吃掉 | bash：`git cat-file -e ef74c60^:.spec/…/TASK-SMOKE-T8.md` → **128**、`ef74c60:…` → **0**；cmd：两者都 → **0**（`git rev-parse ef74c60^` 在 cmd 返回 `ef74c60` 本身） | 真假绿出现在**两 revision 对同一路径存在性不同**时；`rev^` 查询只在 bash 做 |
| ③ 外层仓不跟踪引擎树 | `git ls-files godot-mcp` = **6484**（真命中），`godot-mcp/godot` = **0**，`git check-ignore -v` → `.gitignore:33`，`git diff --stat -- godot-mcp/godot/bin` 空 + `exit=0` | 外层 `git diff` 在引擎树上是**空判**；只有嵌套仓 `git -C godot-mcp/godot …` 或 mtime/摘要算证据 |
| ③′ 同族（我补充） | 外层 `git diff/status` 对 `runs/**` 也是空判（gitignore） | 本轮全部证据的『未变』只能用目录摘要（我用了） |

---

## 5. 守卫与基线

| 断言 | 我的独立证据 |
|---|---|
| `runs/smoke-t6` 未改 | 135 文件、`c144ef32…7a9c03`、最新 mtime `2026-09-29 02:32:01`（= 任务书自证值） |
| `runs/smoke-t7` 未改 | 115 文件、`6e4c1595…20fb7`、最新 mtime `2026-09-29 14:41:14`；`find runs/smoke-t7 -name '*analysis*'` = **0**（报告 §11.1 自曝的 3 个误写文件确已不存在） |
| `runs/smoke-t8` 新目录 | 358 文件、`6d11b2c6…f5a7`、最新 mtime `2026-09-30 07:58:28` |
| `PRD-mario.md` 逐字节冻结 | sha256 `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`，mtime `2026-09-20 23:21:21`；与 `meta.json.spec.sha256` 相同 |
| 引擎树未改（**嵌套仓**） | toplevel `F:/moonbit-hof-rs/godot-mcp/godot`、HEAD `fc63af77c33368c4a1bb839c95d19750554f63a3`、`status --porcelain -uall` **0 行**、`ls-files` **15049**、`modules/mcp_server` **721**、引擎树内 **0** 个文件晚于 `2026-09-30 00:00`（最新非 .git 文件 `2026-09-29 10:49:37`） |
| 引擎身份 = 版本串，sha256 只作记录 | `meta.json.engine.version_string = 4.8.dev.mono.custom_build.035edfce7`；控制台 doctor 同值；我重算二进制 sha256 = `08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a`、size `194216960`、mtime `2026-09-29 08:31:02`——**与 meta.json 记录逐字相同**（仅记录，不当判据） |
| `godot-mcp/**` 零改动 | `git diff 0f37105..HEAD -- src tests Cargo.toml Cargo.lock` = **空**；`src/adapter/tool_vocabulary.rs` 零 diff（风险旗②：守卫未放宽，我也**没有**读/造 `semantic_summary.json`） |
| 未 stage / 未 push | `git diff --cached --stat` 空；`origin/master = ce22e18…`（D263 推送点），本地 `ahead 5`，`behind 0` |
| 无残留临时物 | `build.rs` 不存在且 `git ls-files build.rs` = 0（报告 §11.2 的误操作已清理）；本轮新增只有 `runs/smoke-t8/**`、`runs/smoke-t8-experiment/**` 与报告；`%DST%` 是 2026-09-24 的历史异物（D8） |
| 编辑器存活 / 孤儿清理 | `pid 75204` 存活（`godot.windows.editor.x86_64.mono`，StartTime `2026-09-29 13:20:54`），`127.0.0.1:9877 LISTENING 75204`；报告的孤儿 `118332` **已消失**，`meta.json` 记的游戏端点 `122828` 也已消失，`65442`/`60448` 无监听；全机只剩 75204 一个 godot 进程 |

---

## 6. 诚实性裁定（报告 §10/§11 的自我披露）

1. **『风险旗①的情形本轮真的发生了』——成立**（§2.4 三条我全部复核）。
2. **『没有声称 E3 已 met』——成立**：判定表与 §2.3 都是 not_met（合取），全文无 E3=met 的字样。
3. **『清理了 Tester 遗留的孤儿游戏进程』——成立**：pid 118332 现已不存在，`runs/smoke-t8-experiment/stop_orphan.txt` 有 `{"stopped": true}` 回包；这是我唯一能核的『状态改动』，且未触碰编辑器本体（`75204` 仍活）。
4. **『未把 result.json/meta.json 的失败存根当事实来源』——成立**（报告 §11.7），且这正是它拿到 A_1/电池结论的方式；但它**没有把这条升格为 F3 级缺陷的严重性**（我已单列 R3）。
5. **§11.1 的越界自曝（误写 `runs/smoke-t7/iter-1/traj/*.analysis.json` 后删除）——与我的独立测量自洽**：t7 摘要在收工值上等于历史基线 `6e4c1595…`，且无残留文件。⇒ 『已复原』可核。
6. **§11.2 的 `touch build.rs` 误操作——已复原**：文件不存在、未被跟踪。
7. **报告未声称『E1 已 met』**：一致。
8. **不足之一**：报告的**旗舰诊断**（E3 左移证否）建立在一个没有 release 的注入序列上，且它自造的两个实验都没有把 `move_right` 先**在游戏进程内**释放，因此**两个实验不能互相独立**（同一个混淆因子）；报告却把它当作两个独立佐证（§2.2）。
9. **报告文本的作者问题（R5）**：调度者在 `b926a31` 追加 F9 等改动；F9 的落点抽查成立，但验收报告时应把『实现者自证』与『调度者追加』分开。

---

## 7. 我没查的与做不到的

- 未启动 Godot、未重跑真机轮、未探端点、未联网、未调模型端点、未跑 `cargo`（构建/测试）。
- 未逐条审计 460 次模型调用的轨迹（`traj/**` 共 6 份、约 3.3 MB）；只按需检索 schema 错误、修复上下文、工具名与坐标回包。
- 未复核报告里与 E1..E6 判定无关的历史转述（DR-64/DR-67 的旧数字、t7 的 `E_1` 细节）。
- 未验证 §4.4 的『先 touch 再构建』与二进制新鲜度（只核了 `target/release/hoh.exe` 的 mtime 记录不可信 vs 不可核；round 的 console 里 doctor 行存在）。
- 未核 `usage.json` 的逐角色账目（只核总 tokens = 24,462,425 与 durations 合计 3,902.557 s）。

---

## 8. 对下一批（DR-68 及离线批）的建议

1. **修 Tester 的证据形状关**：①把完整记录形状（`type` **与** `claim_id`）写进 `src/prompts/tester.md:53-68` 的输出契约（不要只靠 retry context）；②让 `schema.rs:241` 的 `EVIDENCE_SKELETON` 在 attempt1 `LimitsExceeded` 时也能送达，或让 `:243-245` 不再因 limits 抑制一次重试；③在 `validate_evidence_shape`（`model.rs:609-655`）里做**记录级**预检，把**所有**缺失字段一次列全（serde 一次只报一个，是 D2 的放大器）。
2. **修 `input_replay` 的观测语义**（D1+D3）：①每次动作前/后通过**游戏通道**注入 release（`running_game_play_input_recording` events 里带 `pressed:false`），否则相反方向的行动互为混淆；②把『有位移』判据从**整向量不等**改成**该动作应有方向的位移**（或在 y 上扣除重力/地面状态），否则重力会继续掩蔽水平无效。
3. **把承诺过的 `move_left` 实验重做**：先 `running_game_play_input_recording(move_left, pressed=false)` 与 `(move_right, pressed=false)` 清场，再用 `run_test_scenario(input move_left)` + 长窗口采样（并接受窗口滞后，至少抽两个连续窗口）。**在该实验之前，不要把 `move_left` 写成产品缺陷**。
4. **启动闸门不要读会被时间污染的证据**：`editor_get_errors` 是 append-only 编辑器日志（`source=editor_log`）。要么在评估前清基线，要么把错误行与**冻结字节**做一致性过滤（F1 的错误行点名了文件里不存在的符号）。
5. **失败路径持久化**：`run_loop.rs:1355-1369` 把真实的 `EvidenceDiff`/candidate_id/version_id/battery 结果传给 `finalize_failure`（或扩展 `failed_run_summary`），并让任何『只看 `launchable`』的读者考虑 `applicable`（F4/R2）。
6. **给出 E1 的『真的变红』证据**：本轮 `ok=false` + 退出码 3 是**另一类失败**（schema），`NoEngineeringWrite` 契约类 2 仍未在真机被走到；下一批若要证明 E1 类失败会红，需要一条**零增量**的真机/夹具路径。
7. **流程**：报告是单一作者工件；若要保留可追责性，实现者报告先原样入库，调度者批注另记（`DECISIONS.md`），避免同一文件被两方改写后无法区分自证与转述。另：给 `runs/**` 的关键证据（版本索引、`deterministic.log`、`raw/input_replay.json`、失败 `result.json`、console、三树摘要）做一份入库的不可篡改摘要或归档，否则真机证据只活在工作树里。

---

## 9. 结论一句话

**六条产品级判定与两个 major 发现都经我独立复核为真，守卫与基线全部成立；但报告的旗舰诊断（E3 左移『被证否』）是注入时序假象、E1 的根因漏了 `claim_id`、电池的 `input_replay` 存在方向无关的掩蔽假绿——因此本报告判 `fail`（范围仅限报告诊断），且不需要重跑真机轮。**
