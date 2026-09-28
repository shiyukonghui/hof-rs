# TASK-DR47-ACCEPTANCE — 批次二（真机 T=1 冒烟）独立验收报告

- 验收者：独立验收子代理（**无**上游对话上下文，**不继承**执行者或调度者的任何结论）。
- 权威依据：`.spec/hof-rs/tasks/TASK-DR47-ACCEPT.md` §2/§4/§5；同读 `TASK-DR47-SMOKE.md`、`-ADDENDUM.md`、
  `REQUIREMENTS.md` §3/§6、`DESIGN-DETAIL.md` §13、`DECISIONS.md` D219/D220。
- 落点：`F:\moonbit-hof-rs`（外层仓 `master`）。**未改任何代码/夹具/配置/`godot-mcp/**`/`PRD-mario.md`/`runs/smoke-t6/**`**，
  **未** `git commit`/`push`/stage，**未**联网，**未**调用模型，**未**打印密钥（只打印长度）。
- 我自己生成的证据落在 `%TEMP%\dr47acc\`（仓库外），未写入 `runs/**`。
- 真机前提：编辑器 PID **108432** 全程存活于 9877（**未**杀/重启/抢占）；**未**新建任何游戏进程；
  §2.7 所需的 `G` 用的是执行者 02:33 留下的**原始捕获**（我重算其集合），并用**引擎源码静态推导**独立佐证。
- 收尾自检（我自己跑）：`git status --porcelain` **空**；`PRD-mario.md` sha256 =
  `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`（**未变**）；
  `GET http://127.0.0.1:9877/mcp` → **200**；`runs/smoke-t6` 共 **135** 个文件，`runs/smoke-t1..t5` 目录 mtime 仍为 2026/09/21。

---

## 1. 结构化结论（机器可读）

```json
{
  "verdict": "pass",
  "criteria": [
    { "id": "E1", "pass": false,
      "evidence": "runs/smoke-t6/exit_code=6；versions/index.json 中 iteration0/role=init 与 iteration1/role=developer 的 version_id 同为 fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c（A1 的 parent 自指）；warnings.log:'iteration 1: no_progress'；result.json.warnings 含 no_progress；plan.md 三节齐备（Priority Order/Preservation Gate/Acceptance Gate）、planner attempt artifact_valid=true；iter-1/evidence.json 有 verified_records 8 + gap_records 22 + planner_handoff 三键。=> 执行者 not_met 判定正确（Developer 零工程增量）" },
    { "id": "E2", "pass": false,
      "evidence": "artifact_gate.launchable=false，唯一 reason 是 editor_errors_baseline 把 errors:[\"[MCP] capture=off (default; use --mcp-capture=on_error|every_call ...)\"] 判为 not clean；但同一轮 raw/play_scene_ready.json 显示 editor_play_scene ok=true(pid 101872, port 63698) 且 running_game_get_scene_tree ok=true(50 节点)。我自己的活体验证：POST 9877 tools/call editor_get_errors -> count=1 且恰为该 [MCP] 行；POST project_validate_scripts -> count=7, invalid_count=0, valid_count=7 全部 'Script compiles successfully'。=> 判据 not_met，但根因是假阴性（DEF-A 成立）" },
    { "id": "E3", "pass": false,
      "evidence": "raw/input_channel_probe.json 与 raw/input_replay.json 对 http://127.0.0.1:63698/mcp 的 running_game_* 调用全部失败（os 10060 超时后 os 10061 拒绝）；编辑器侧 editor_simulate_input_action 只到 editor_process；无任何游戏进程内位移/跳跃/交互/胜负证据。=> not_met，执行者判定正确且未粉饰" },
    { "id": "E4", "pass": true,
      "evidence": "8 条 verified 的 execution_records 全部指向真实存在的文件（我逐个实读 project_reload_and_open/play_scene_ready/scene_structure/scene_tree/editor_stop_scene/node_and_collision_assertions 与 frame-00.png）；抽检 V1/V2/V4/V8 的记录内容与原始 payload 一致；22 条 gap 均带 player_impact/recommended_update 且无证据；verified claim-id ∩ gap claim-id = 空集；45 条 execution_records 全部带 candidate_id=fc78d299…（iter-1/evidence.json），而候选原始件 candidate/.hoh/evidence.json 的 45 条记录 0 条带该字段（Runtime 归一化时绑定，执行者此说属实）" },
    { "id": "E5", "pass": true,
      "evidence": "我按 src/runtime/policy.rs:68 的算法自行重实现 hash_tree（sha256 over sorted 'relpath\\n{len}\\n{bytes}\\n'，excludes=.hoh/.git/.godot/.import），对 .workspace/mario、runs/smoke-t6/iter-1/candidate、runs/smoke-t6/versions/fc78d299… 三棵树各得 17 文件、sha256 均为 fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c；三棵树两两逐字节相同（diff=[]）" },
    { "id": "E6", "pass": true,
      "evidence": "qa_report.md 第 7 行自述规则、G18（把 launchable=false 如实记为 gap 并点名 'a harness diagnostic, not a script error'）、G20（ACTION_BINDING_UNKNOWN 明说 'the channel was unreadable, not a missing action'）、G21（明说 PNG 陈旧、step 仅因旧文件存在才 ok=true）均为对自己不利的如实披露；我另构造 3 个反例（R1/R2/R3，见 §3），无一推翻结论；未发现任何把 F1–F17 未观测行为写成 verified 的情形" },
    { "id": "DR44.identity", "pass": true,
      "evidence": "meta.json.engine.binary.path == F:/moonbit-hof-rs/godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe；我自己 stat/sha256sum：size=194207744、mtime_unix=1790572931、sha256=25d29eb4fbaf48c00911bcb18b491d5a7305542e00557e70a05f185b935bb468（与落盘逐字一致）；listener.pid=108432、matches_binary=true，Get-NetTCPConnection -LocalPort 9877 与 Get-Process -Id 108432 独立复核一致；我自己执行 '<binary> --version' → 4.8.dev.mono.custom_build.ba1587c71（exit 0）；battery 的 engine_identity 步 ok=true" },
    { "id": "D219.partition", "pass": false,
      "evidence": "我自己的活体 tools/list（POST 9877，56534 B，sha256 aec1d8deb2de7af32bc252deb9813e895dd679dafd17c754fd41926e3d7f744e，与执行者 00:39 捕获的 %TEMP%\\dr47_toolslist_raw.json 逐字节相同）|E|=154；夹具 |F|=177；解析执行者保留的游戏端点原始响应 /tmp/dr47_game_rpc_tools_list.json 得 |G|=73；E⊆F、|F\\E|=23 且全 running_game_*、|E∩G|=50、|E\\G|=104（全 editor_*）、|G\\E|=23、|E∪G|=F=177。**引擎源码静态独立推导**（tool_registry.cpp:267-277 scope_matches(EDITOR=is_editor, GAME=!is_editor, BOTH=true) + 我扫 177 个 shipped ToolBuilder 注册得 EDITOR 104 / BOTH 50 / GAME 23）给出完全相同的 |E|=154、|G|=73、交 50。=> D219 的 108/46/23（G=69）**是错的**，执行者实测 104/50/23 正确" },
    { "id": "DEF-A", "pass": true,
      "evidence": "已在引擎源码级证实：godot-mcp/godot/modules/mcp_server/tools/editor_read_scene_inspector.cpp:249 的 _tool_get_errors 用 source.lines[i].to_upper().contains(\"ERROR\") 过滤日志行——[MCP] capture=off …on_error… 含 'ERROR' 才是唯一入选项（同批 [MCP] trace=off 行不含故未入选，与 count=1 吻合）。hof-rs 侧规则是 src/adapter/godot.rs:783-796 'errors 数组非空即 not clean'，并无子串匹配。我活体复现：editor_get_errors 现返回 count=1 且恰为该行，而 project_validate_scripts 全绿" },
    { "id": "DEF-B", "pass": true,
      "evidence": "mcp-errors.jsonl 3 条 code=-32602 'Parameter save_path must start with res:// or user://, got .workspace/mario\\.hoh/evidence/frame-00.png'；引擎契约见 running_game_capture.cpp:62-63；hof-rs 侧 src/adapter/godot.rs:1042-1048 传的是 workspace.join() 的**文件系统绝对路径**。假证据确认：evidence/frame-00.png size=4246、mtime=2026-09-21 17:55:00.547 +0800、sha256=bef0936daba1b16a23e7b25bd1fc432d946afaaca6d7b0636fbeafc898b67ea2；godot.rs:1109-1124 的 ok 仅由 absolute.is_file() 决定并写下 'screenshot written to … (4246 byte(s))'" },
    { "id": "DEF-C", "pass": true,
      "evidence": "pass2（63698/101872）：raw/play_scene_ready.json 首个 running_game_get_scene_tree ok=true(50 节点)；raw/input_channel_probe.json 前 4 个 running_game_execute_gdscript ok=true（result_type=Nil），第 5 个（Input.action_press）attempts=1..3 全 os 10060，其后 get_node_property_samples/get_node_properties/execute_gdscript 全部 os 10061。pass1（65333/109964）：developer.attempt2.json 内保留了那次电池的 raw/play_scene_ready.json 原文（editor_play_scene ok=true + get_scene_tree 树）与游戏启动行 '[MCP] role=game configured_port=65333 … (editor=false, tools=73)'，并有 8 次 10060、88 次 10061。两轮端口/PID 不同、轨迹同型" },
    { "id": "DEF-D", "pass": true,
      "evidence": "meta.json.engine.mcp.game_endpoint=null 且 reason='the game endpoint does not exist until editor_play_scene has created it'，而本轮确实创建过 65333/109964 与 63698/101872 并成功调用过。代码级根因（我读源码得出）：src/runtime/run_loop.rs:787-793 的回写在**第一次电池跑完之后**才执行，而电池的 editor_stop_scene 步（src/adapter/godot.rs:1887-1888）已 clear_game_endpoint()，且 pass2 之后无回写；editor_status 则由 src/runtime/engine_identity.rs:44 恒定传入 Value::Null，故该字段**永不**落盘，其 reason 文案（'no GET /mcp body was recorded … in this run'）与 DESIGN-DETAIL §13.4 的字段契约不符" },
    { "id": "DEF-E", "pass": true,
      "evidence": "candidate/.hoh/deterministic/deterministic.json 的 replay observation 逐字含 'EDITOR_SIDE_INJECTION: the editor InputMap does not list [\"move_left\", \"move_right\", \"jump\"]'；同一步 raw/input_replay.json 第 1 个调用 editor_get_input_actions ok=true 且 count=92，actions 前三个恰为 ['jump','move_left','move_right']。矛盾属实" },
    { "id": "DEF-F", "pass": true,
      "evidence": "self-produced：raw/screenshot.json 的 step ok=true 而唯一调用 ok=false(-32602)，battery.json 记 'screenshot written to .hoh/evidence/frame-00.png (4246 byte(s))'；代码处的口径是 godot.rs:1109 'One decision point … about the disk'（absolute.is_file()）。执行者的事实观察成立，但把口径描述为『某种更弱的口径』不准确（见 §4 的 partial 裁定）" }
  ],
  "defects": [
    { "id": "DEF-A", "confirmed": true, "severity": "major",
      "correction": "成立，且已从『未能证实到源码级』升级为**源码级 + 活体双重证实**。需改写之处：①『该串被判错只因为含子串 error』的主体是**引擎**（editor_read_scene_inspector.cpp:249），不是 hof-rs——hof-rs 只是『errors 非空即 not clean』；②原报告未提的**关键反例**：引擎确实会打印 'ERROR: [MCP] SceneTree never became available; MCP server disabled.'（见 godot-mcp/recovery/work/task092/logs/*.log.err），故修复时**不可**用『忽略一切 [MCP] 行』，必须只忽略引擎 INFO banner 行且保证 ERROR:/SCRIPT ERROR/PARSE ERROR 仍能判否。" },
    { "id": "DEF-B", "confirmed": true, "severity": "major",
      "correction": "成立。补充两条执行者未点明的机制：①因为 absolute.is_file() 已为真，godot.rs:1081 的 running_game_capture_frames 兜底路径**根本没被尝试**；②假证据的产出点写得非常明确——godot.rs:1109-1124 的 ok 由磁盘存在性决定、文案由该函数拼出。『hof-rs 调用形态 vs 引擎契约』这一问题：hof-rs 传文件系统路径（错），引擎契约要求 res://|user://（running_game_capture.cpp:62-63：'-32602 (the shared rule of editor_capture_screenshot)'）。" },
    { "id": "DEF-C", "confirmed": true, "severity": "major",
      "correction": "成立（两次独立注册后挂死并消失，端口/PID 不同）。但时间线需改写：pass2 的 execute_gdscript 并非『3 次超时』而是**1 次逻辑调用 × 3 次传输重试**全 10060；并且在该次之前有 **4 个 execute_gdscript 调用传输成功**（返回 result=null/result_type=Nil），执行者的『首个 get_scene_tree 之后再无成功观测』不精确。另：pass1 的证据只保留在 developer.attempt2.json 里（raw/* 已被 pass2 覆盖），『两轮一致』站得住但 pass1 那一半不是一等原始件。挂死的**成因仍未定**（见 §5 未验证项）。" },
    { "id": "DEF-D", "confirmed": true, "severity": "moderate",
      "correction": "成立，建议把严重度从 minor→moderate 提为**moderate**。措辞需改写：reason 文案是**通用占位串**，并非对本轮的断言；真正的缺陷是这两个字段在生产代码里**结构性永远取不到值**（game_endpoint 回写被 editor_stop_scene 清理掉且 pass2 后无回写；editor_status 恒定 Value::Null），与 DR-44/DR-43 第 4 条『端点身份入库』的设计意图不符。" },
    { "id": "DEF-E", "confirmed": true, "severity": "minor",
      "correction": "成立，逐字复现（deterministic.json 的诊断句 vs raw 的 92 动作/前三个恰为 jump,move_left,move_right）。无需改写。" },
    { "id": "DEF-F", "confirmed": "partial", "severity": "minor",
      "correction": "部分成立。成立的部分：step 级 ok 与『路径上已有文件』混同，确实让旧文件冒充本次产物（代码依据 godot.rs:1109-1124）。不成立/需改写：『某种更弱的口径』不准确——口径是**明确且刻意**的『磁盘上存在即算』；且它给的第二个例子（input_channel_probe 步 ok=false 却含 4 条 ok=true 调用）**不是缺陷证据**：步 ok 是电池的判定值，本就不是『所有调用成功』的合取。建议把 DEF-F 合并进 DEF-B 作为同一根因的第二个表现。" }
  ],
  "risks": [
    "DEF-C 的成因未定：游戏端点先 TCP 层无响应（10060）后退化为拒绝（10061），但 mario 工程自身没有留下任何 checkjs/SCRIPT ERROR；HoH Mario 的 user://logs/godot.log 已被冒烟后的那次游戏运行覆盖（现只有 9 行游戏 banner）。不能在仓库内区分『引擎游戏进程 MCP 服务死锁/退出』与『hof-rs 的 execute_gdscript 调用形态掌握主循环』——若属后者，则修复范围在 hof-rs；若属前者，需上报用户（可能触发回阶段二/三）。",
    "N2/F5/F6/F16/N1 这 5 个 PRD 要求**同时**出现在 verified 侧与 gap 侧（claim-id 层面互斥、requirement 层面不互斥）。执行者的『并集 = 30 条、verified ∩ gap = ∅』只在 claim-id 层面成立；requirement 层面并集是 24。此处若被后人误读为『N2 已 verified』，会把旧的 frame-00.png 当成有效画面证据。",
    "候选原始件（candidate/.hoh/evidence.json）与归一化件（iter-1/evidence.json）之间，Runtime 会**丢弃** requirement/type 两个键；下游 E_t 因此失去显式 requirement 链接（本次不影响 E1–E6 判定）。",
    "夹具 vs 活体的 2 处 inputSchema 差异（editor_get_test_report.clear.default 真为 true/夹具 false；editor_simulate_input_sequence.events 活体缺 items）来源未查；若契约文档未同步，后续按夹具生成参数会再次踩到 -32602 类错误。",
    "修复 DEF-A 的窄化过滤存在反向风险：把 [MCP] 行一律忽略会吞掉引擎真实的 'ERROR: [MCP] …' 行（已在引擎回收件中出现过），必须配反例测试。"
  ],
  "unverified": [
    "模型端点可用性与本轮 token 账：报告 §1.5 的 GET http://100.105.152.101:18080/v1/models -> 200 未复核（禁项：不调模型/不联网）；我只从 result.json/usage.json 与 %TEMP%\\dr47_smoke_t6_console.log 的 'total tokens Some(26805473)' 核对到 26,805,473 这个**合计**（planner 2,202,183 + developer 15,407,542 + tester 9,195,748）。",
    "执行者在 §4-E3 给出的 pass1 墙钟时刻 [1:20:56, 1:26:58, 1:33:00] 与 [1:58:41]：pass1 侧证据里没有任何 timestamp 字段，无法核对（pass2 侧的 10060 时刻可从 mcp-errors.jsonl 反算出 01:58:39，与 [1:58:41] 同量级）。",
    "『两轮电池的 -32602 各 3 次』：mcp-errors.jsonl 只含 pass2（63698）的 39 条，pass1 的 -32602 原文**未被保留**；两轮一致只能由 battery_passes 步骤表相同 + pass2 原文推定，不是两轮各有一等原始件。",
    "mcp-errors.jsonl 的行数：报告写『共 43 行』，实测 **39** 行（非空行数=39，且以换行结尾；按工具分 running_game_get_node_property_samples 15 + execute_gdscript 12 + get_node_properties 9 + capture_screenshot 3 = 39）。报告此数字**错**（不影响任何结论）。",
    "引擎把 [MCP] capture=off 放进 errors 是『设计如此』还是过滤过粗：只证实了过滤规则（to_upper().contains(\"ERROR\")）与效果，引擎侧无任何测试/文档声明该行应属错误，故『引擎意图』未验证。",
    "engine.mcp 两字段的实际修复归属（引擎侧改过滤 vs hof-rs 侧窄化过滤）：本批只给证据，不做裁决。",
    "meta.json.engine.binary.mtime_unix 报告的 ⚠『差 1 s』：我用 stat 得 1790572931，与落盘**完全一致**；该 1 s 差异是执行者 PowerShell 取整口径的产物，不是缺陷（也不改变其已判定『非缺陷』的结论）。"
  ]
}
```

**真实命令与退出码（本节证据的来源，节选）**

```text
$ git status --porcelain                       -> (空)
$ git rev-parse --abbrev-ref HEAD              -> master
$ sha256sum .spec/hof-rs/PRD-mario.md          -> 4c81c3a9…5c3a
$ stat -c '%s %Y' <mono binary>                -> 194207744 1790572931
$ sha256sum <mono binary>                      -> 25d29eb4fbaf48c00911bcb18b491d5a7305542e00557e70a05f185b935bb468
$ "<binary>" --version                         -> 4.8.dev.mono.custom_build.ba1587c71   (exit 0)
$ curl.exe -s http://127.0.0.1:9877/mcp        -> 200 {"connections":1,...,"is_editor":true,...,"tools":154,...}
$ curl.exe -s -X POST 9877 tools/list          -> 200, 56534 B, sha256 aec1d8de…f744e
$ curl.exe -s -X POST 9877 tools/call editor_get_errors
                                               -> {"count":1,"errors":["[MCP] capture=off (default; use --mcp-capture=on_error|every_call together with --mcp-trace=<path>)"]}
$ curl.exe -s -X POST 9877 tools/call project_validate_scripts
                                               -> {"count":7,"invalid_count":0,"valid_count":7, ... "Script compiles successfully" ×7}
$ Get-NetTCPConnection -LocalPort 9877 -State Listen -> OwningProcess 108432
$ Get-Process -Id 108432                       -> Path F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe
$ (Get-NetTCPConnection for 65333/63698/56438) -> 全部 not-listening；唯一 godot 进程 = 108432
$ cat runs/smoke-t6/exit_code                  -> 6
```

---

## 2. 逐条核对表（每条：命令 → 原始输出 → 判定）

### 2.1 退出码与规模 —— **与报告一致（除一处行数外）**

| 项 | 我的命令 / 原始输出 | 判定 |
|---|---|---|
| 退出码 | `cat runs/smoke-t6/exit_code` → `6`；console log → `SMOKE_EXIT=6` | ✔ 报告称 6 属实 |
| 三角色 tokens | `result.json.usage`：planner 2,202,183 + developer 15,407,542（8,962,310 + 6,445,232）+ tester 9,195,748 | ✔ 合计 **26,805,473**，≈26.8M 属实 |
| attempts | `result.json.attempts` 4 条（planner#1、developer#1、developer#2、tester#1），`exit_status` **全部** `LimitsExceeded`，`exit_was_limits` 全 true | ✔「四次尝试全部 LimitsExceeded」属实 |
| durations | result.json.durations_ms：184389 / 1852719 / 932027 / 1030982（attempts 内为 184385 / 1852719 / 932027 / 1030969） | ✔ 报告取的是 attempts 值；两者差 4ms/13ms，无关结论 |
| repair_retry_used / hygiene | `repair_retry_used=true`、`secret_redactions=0`、`out_of_tree_writes=[]`、`suspicious_files=[]`、`evidence_diff` 三空 | ✔ 属实 |
| 时长 | 启动 1790613647（=2026-09-29 00:40:45 +0800），result.json mtime 02:32 | ✔ ~1h52m 属实 |
| 唯一数字错误 | `mcp-errors.jsonl` 实测 **39** 行（报告写「共 43 行」） | ✘ 报告数字错，无实质影响 |

### 2.2 引擎身份（DR-44 活体验收）—— **通过**

```text
size=194207744   mtime unix=1790572931   sha256=25d29eb4fbaf48c00911bcb18b491d5a7305542e00557e70a05f185b935bb468
```
- `meta.json.engine.binary` 三字段与上逐字一致；`listener.pid=108432`、`matches_binary=true`、path 逐字一致。
- 我自己的探针（`Get-NetTCPConnection`+`Get-Process`）与 `GET /mcp` 均与落盘一致。
- `version_string` 我自己执行二进制得到 `4.8.dev.mono.custom_build.ba1587c71`，以 `4.8.dev.mono` 开头 ✔。
- **DEF-D 复核**：`game_endpoint=null` + `reason`，但 `raw/play_scene_ready.json`（63698/101872，ok=true）与 `developer.attempt2.json` 内保留的 pass1 raw（65333/109964，ok=true + 场景树）证明本轮**创建并成功调用过**游戏端点 ⇒ 缺陷成立（细节见 §4 DEF-D）。`editor_status=null` 亦不应为空：doctor 与我都读到过 `GET /mcp` 的 200 响应体。

### 2.3 DEF-A —— **成立，并已提升到源码级证据**

- `result.json.artifact_gate.reasons` 原文（唯一 reason）：
  `editor_errors_baseline: editor reported 1 error(s): {"available":true,"count":1,...,"errors":["[MCP] capture=off (default; use --mcp-capture=on_error|every_call together with --mcp-trace=<path>)"],...} (UNAVAILABLE: the editor is not clean)`
- **它是信息行而非脚本错误**：同轮 `raw/play_scene_ready.json` 的 `editor_play_scene` ok=true 且 `running_game_get_scene_tree` ok=true（50 节点）；`battery_passes` 两轮 `play_scene_ready=true`、`scene_tree=true`。
- **根因（我自己读引擎源码得出）**：`godot-mcp/godot/modules/mcp_server/tools/editor_read_scene_inspector.cpp:239-259`
  ```cpp
  for (int i = 0; i < source.lines.size(); i++)
      if (source.lines[i].to_upper().contains("ERROR")) errors.push_back(source.lines[i]);
  ```
  即**按大写子串 "ERROR" 过滤日志行**；`capture=off …on_error…` 命中，而同一 banner 里的 `[MCP] trace=off (default; use --mcp-trace=…)` **不含** 'error' 故未入选 —— 与 `count=1` 精确吻合。**置信度：高（源码 + 计数一致）**。
- hof-rs 侧**没有**子串匹配：`src/adapter/godot.rs:783-796` 的规则是『`errors` 数组为空 → ok；非空 → not clean』。
- **我自己活体复现**：POST 9877 `tools/call editor_get_errors` → 现返回 `count=1` 且恰为该行；同时 POST `project_validate_scripts` → `count=7, invalid_count=0, valid_count=7`（全部 "Script compiles successfully"）⇒ **工程真的没有脚本错误，闸门是假阴性**。
- **修复如何不放过真错误**：`[MCP]` 前缀**不足以**作为白名单——引擎会打印
  `ERROR: [MCP] SceneTree never became available; MCP server disabled.`（`godot-mcp/recovery/work/task092/logs/doctest-full-run1.log.err:1` 等）。故窄化规则必须是「行首为 `[MCP] `（不含 `ERROR:`）且属于已知 INFO banner 文案」才忽略，并**必须**有反例测试证明 `SCRIPT ERROR`/`Parse Error`/`ERROR: …` 仍判否。**我没有改任何代码。**

### 2.4 DEF-B —— **成立（假证据我亲手抓了一遍）**

- 原文（`raw/screenshot.json` + `mcp-errors.jsonl` 前 3 行）：
  `code=-32602 "Parameter 'save_path' must start with 'res://' or 'user://', got '.workspace/mario\\.hoh/evidence/frame-00.png'"，attempts=1,2,3`
- PNG 实测（我 `stat`+`sha256sum`）：`size=4246  mtime=2026-09-21 17:55:00.547 +0800  sha256=bef0936daba1b16a23e7b25bd1fc432d946afaaca6d7b0636fbeafc898b67ea2`
- 而 `battery.json` 该步 `ok=true`，`record.observation = "screenshot written to .hoh/evidence/frame-00.png (4246 byte(s))"` ⇒ **假证据成立**。
- **调用形态 vs 引擎契约**（两侧依据都给）：
  - 引擎契约：`running_game_capture.cpp:56-63`（`save_path` 只收 `res://`/`user://`，否则 `-32602`，与 `editor_capture_screenshot` 同规则）+ 实测响应原文；
  - hof-rs 形态：`src/adapter/godot.rs:1042-1048` `relative=".hoh/evidence/frame-00.png"` → `absolute=self.workspace.join(relative)` → `save_path=absolute`（文件系统绝对路径）。
  ⇒ **hof-rs 传错形态**（不是契约要求的形态）。
- 执行者未提的一点：因为路径上文件已存在，`godot.rs:1081` 的 `running_game_capture_frames` 兜底**没有被尝试**。

### 2.5 DEF-C —— **成立（两轮不同端口/PID，轨迹同型）；时间线需修正**

- 端口/PID：pass1 = `65333 / 109964`，pass2 = `63698 / 101872`（`raw/editor_stop_scene.json` 的 `game_endpoint_invalidated` 亦记 63698/101872）。
- pass2 失败原文（`mcp-errors.jsonl`，端口 63698）：
  `os error 10060`（execute_gdscript，attempts 1/2/3 于 t=1790618321/683/9044）→ 随后 `os error 10061`（get_node_property_samples / execute_gdscript / get_node_properties 共 36 条）。
- **我修正执行者的时间线**：`raw/input_channel_probe.json` 显示该步**前 4 个** `running_game_execute_gdscript` 调用 `ok=true`（payload 中 `result:null, result_type:"Nil"`，即传输成功但无值），第 5 个（`Input.action_press("move_right")`）才 `attempts=3` 全 10060，之后全部 10061。
- **游戏进程是否在两次调用之间退出**：10060 表示 TCP 已连通但无 HTTP 应答 ⇒ 进程**活着但服务卡住**；后续 10061 表示**无监听** ⇒ 进程随后退出。故时序是「挂死 → 死亡」，与报告一致。
- pass1 的同类证据只存在于 `iter-1/traj/developer.attempt2.json`（修复期的执行者读到了 pass1 的 `raw/play_scene_ready.json` 原文与游戏进程 banner `[MCP] role=game configured_port=65333 … tools=73`），并含 8 次 `10060`、88 次 `10061`（65333）。**我未再起任何游戏进程**，未使用 `editor_play_scene`。

### 2.6 E1..E6 逐条

| 判据 | 我的独立核对 | 与执行者 |
|---|---|---|
| **E1** | `versions/index.json`：iter0 `role=init` 与 iter1 `role=developer` 的 `version_id` **同为** `fc78d299…`，iter1 `parent` 自指；`warnings.log` + `result.json.warnings` 含 `no_progress`；`plan.md` 三节齐备；`evidence.json` = 8 verified + 22 gap + handoff 三键；`candidate/.hoh/evidence.json` 45 条记录 0 条带 `candidate_id`，`iter-1/evidence.json` 45 条全带 ⇒ Runtime 归一化绑定的说法**属实** | **一致：not_met** |
| **E2** | `launchable=false`（唯一 reason = DEF-A）；`play_scene` 与首个 `get_scene_tree` 真成功；我另跑 `project_validate_scripts` 全绿（7/7） | **一致：not_met，但根因是假阴性** |
| **E3** | 四项子行为（移动/跳跃/可交互对象/胜负）**无一条**有游戏进程内证据；编辑器侧注入（target=editor）不算；截图 `-32602` | **一致：not_met** |
| **E4** | 8 条 verified 的 45 条 execution_records 全部指向实存文件且观察与原始 payload 相符；22 条 gap 无证据；claim-id 互斥 | **一致：met**（附 §5 风险：requirement 层面不互斥） |
| **E5** | 我自写 hash_tree：三棵树各 17 文件、同值 `fc78d299…`、逐字节相同 | **一致：met** |
| **E6** | QA 的 G18/G20/G21 均为自我不利披露；我另造 3 个反例（§3）无一推翻；未发现把未观测行为写成 verified | **一致：met** |

### 2.7 端点分区（D219 等式已知有错）

我**自己**从 9877 抓的活体 `tools/list`（sha256 与执行者 00:39 的捕获**逐字节相同**）解析：

```text
|F|=177  |E|=154  |G|=73
E subset of F: True            | F\E = 23, all running_game_: True
|E&G|=50  |E\G|=104 (all editor_*)  |G\E|=23 (all running_game_*)  |E∪G|=177 == F: True
name diffs 0 / description diffs 0 / inputSchema diffs 2:
  editor_get_test_report      clear.default   live=true   fixture=false
  editor_simulate_input_sequence  events      live 无 items  fixture 有完整 items 子 schema
fixture-only keys: []   live-only keys: []
```

**引擎源码静态独立推导**（不依赖任何运行）：扫 `godot-mcp/godot/modules/mcp_server/**/*.cpp`（排除 `tests/`）的 177 个 shipped `ToolBuilder` 注册，配 `tool_registry.cpp:267-277` 的 `scope_matches`：

```text
shipped registrations: 177   unique: 177   == fixture name set: True
scope: EDITOR 104 / BOTH 50 / GAME 23
=> |E|=154  |G|=73  |E&G|=50  |E\G|=104(全 editor_)  |G\E|=23(全 running_game_)  |E∪G|=177
```

另有两处旁证：HoH Mario 的 `godot.log` 与 pass1 的游戏 banner 均打印 `tools=73`。

⇒ **D219 的 108 editor-only / 46 共享 / 23 game-only（game 69）是错的**；执行者的 104/50/23（game 73）正确；
**并集恰为 177、准入门两条硬判据（`E⊆F`；`|F\E|=23` 且全 `running_game_*`）通过 ⇒ 不是合约漂移，是 D219 的数字错**（与 D220 的认账一致：新增 6 条实为 **2 editor-only + 4 共享**）。

---

## 3. 反例清单（我构造的 / 我复核的）

| 编号 | 攻击对象 | 我做了什么 | 观测 | 是否推翻 |
|---|---|---|---|---|
| **R1** | V7（旧 PNG）| 复读 V7 的 claim 与其 observation，实 `stat`/`sha256sum` frame-00.png | claim 文字仅限「文件存在」，且 observation 自陈 `cannot confirm it depicts this battery run … mtime 2026-09-21` | **不推翻**（但它是 8 条 verified 里最弱的一环；且其引用的 `battery.json` 记录写了「screenshot written to …」= 假证据，见 R3） |
| **R2** | V8 vs QA 自述规则 | 读 `qa_report.md:7`「Only the battery steps marked ok=true …」并对照 V8 引用 `node_and_collision_assertions`（步 ok=false） | 规则与实践**确实不一致**；但同句 observation 自陈「battery step … ok=false … but the collision_info sub-calls ok=true supply the shape counts」，且 3 条 `editor_get_collision_info` 实读 ok=true、payload 真 | **不推翻** E6（只是自述口径不严） |
| **R3（新增）** | E4 的「verified ∩ gap = ∅ / 并集=30」 | 我自己把每条 claim 文本里的 PRD 编号提取出来做集合运算 | verified 侧 requirement = {N1,N2,P2,P4,F5,F6,F16}；gap 侧 = {F1..F17,N1..N4,P3}；**两者交集 = {N1,N2,F5,F6,F16}**；requirement 并集 = **24**（不是 30） | **不推翻** R7（claim-id 层互斥成立），但**推翻「verified ∩ gap = ∅」在 requirement 层的可推广性**；这是执行者未声明的口径 |
| **R4（新增）** | 「QA 是否一律保守」 | 反向扫描 22 条 gap 是否有「把实测成功说成失败/不可用」 | G16 的 "HUD visible text node(s)=2" 与 raw 一致；G18 的 "11 step(s), 7 ok" 与 battery.json 一致；G21 的「3 条 -32602」与 jsonl 一致；G20 明说 unreadable≠unbound | **不推翻**：无一条 gap 与原始件矛盾 |
| **R5（新增）** | 「E2 是否只是假阴性」的另一可能——工程是否真有脚本错误 | **我自己的活体只读调用** `project_validate_scripts`（9877） | `count=7 / invalid_count=0 / valid_count=7 / not_compiled_count=0`，7 个 `.gd` 全部 "Script compiles successfully" | **排除**该可能 ⇒ 强化 DEF-A/E2 假阴性结论 |
| **R6（我自我驳回的线索）** | 是否存在真实引擎 ERROR 被漏掉 | 在 `traj/*.json` 里全量搜 `ERROR:` 并回溯其来源 | 66 处 `SCRIPT ERROR`/`ERROR:` 全部出自 **`%APPDATA%\Godot\app_userdata\MCP074 Platformer\logs\godot.log`（2026-09-25 的另一工程）**（修复期执行者在满盘找 godot.log）；mario 工程轨迹 0 处 | **线索不成立**（未构成对 E2 的反证） |

---

## 4. 对 6 条缺陷的 confirmed / refuted / partial 与严重度意见

| 缺陷 | 我的裁定 | 严重度 | 关键修正 |
|---|---|---|---|
| **DEF-A** | **confirmed** | **major** | 升级为源码级（`editor_read_scene_inspector.cpp:249` 的大小写不敏感子串 "ERROR"）+ 活体复现。主体是**引擎**的过滤，不是 hof-rs 的子串判断。修复白名单**不能**是「一切 `[MCP]` 行」（引擎会打印 `ERROR: [MCP] …`） |
| **DEF-B** | **confirmed** | **major** | 契约/形态两侧依据齐全；补：旧文件还**抑制了 `capture_frames` 兜底**（`godot.rs:1081`） |
| **DEF-C** | **confirmed** | **major** | 修正时间线：pass2 前 4 个 `execute_gdscript` 传输**成功**（Nil），第 5 个才 10060 ×3 attempts；「3×」是重试不是 3 次不同调用；pass1 证据只在 `developer.attempt2.json` 内 |
| **DEF-D** | **confirmed**（**同意升级**为） | **moderate** | 不只是「reason 与事实矛盾」：`editor_status` 恒为 `Value::Null`（`engine_identity.rs:44`）、`game_endpoint` 回写被 `editor_stop_scene` 的 clear 与「pass2 无回写」双重作废（`run_loop.rs:787-793` + `godot.rs:1887-1888`）⇒ 两字段**结构性永远为空** |
| **DEF-E** | **confirmed** | **minor** | 逐字复现，无需改写 |
| **DEF-F** | **partial** | **minor** | 事实成立、机制描述不准确；第二个例子（`input_channel_probe` 步 ok=false 含 4 条 ok=true）不是缺陷证据；建议并入 DEF-B |

**没有一条缺陷被我判 refuted（无错告）**；DEF-F 的 partial 只涉及机制表述与例证质量。

---

## 5. 未验证项与理由

1. **DEF-C 的成因**：无法在仓库内区分「引擎游戏进程的 MCP 服务死锁/退出」与「hof-rs 的 `execute_gdscript` 调用形态（阻塞主循环）」。mario 工程没有留下任何 `SCRIPT ERROR`，且 `HoH Mario/logs/godot.log` 已被冒烟后的那次游戏运行覆盖（现仅 9 行 banner）。
2. **模型端点与 token 账的独立复核**：按禁项不调模型/不联网，故 `GET /v1/models -> 200`、`finish_reason` 等未复核；我只核对了 `result.json`/`usage.json`/console log 的**合计 26,805,473**。
3. **pass1 的墙钟时刻**（[1:20:56, 1:26:58, 1:33:00]）与 **pass1 的 -32602 原文**：pass1 的 `raw/*` 与 `mcp-errors.jsonl` 已被 pass2 覆盖，未保留一等原始件。
4. **`mcp-errors.jsonl` 行数**：报告写 43，实测 39 —— 报告的**数字错**已确认（不影响结论）。
5. **引擎「意图」**：`[MCP] capture=off` 是否应算错误，引擎无测试/文档声明，只证实了过滤规则与效果。
6. **2 处 `inputSchema` 差异的成因**（文档 vs 实现谁先变）：未查。
7. **`meta.json.engine.binary.mtime_unix` 的 1 s 差**：报告自述的 ⚠ 实为其取整口径产物；我用 `stat -c %Y` 得 1790572931，与落盘**完全一致**（不构成缺陷）。

## 6. 我没有独立复核的部分（诚实列账）

1. **没有重跑 T=1 冒烟**，也没有任何模型调用；本报告全部结论来自：`runs/smoke-t6/**` 原始件、我自己对 9877 的**只读** MCP 调用（`tools/list`、`editor_get_errors`、`project_validate_scripts`）、我自己的文件系统/哈希/进程/端口探针、以及**只读**的引擎与 hof-rs 源码。
2. **没有启动任何游戏进程**；§2.7 的 `G` 用的是执行者 02:33 保留的原始响应（我重算集合）+ 我自己的引擎源码静态推导 + 两处 `tools=73` 旁证，**未**重做 `editor_play_scene`。
3. **冒烟本身的过程**（是否中断、是否重跑、`cargo build --release` 等）只能从工件与 console log 交叉印证，我无法亲历。
4. 执行者的 `%TEMP%` 脚本/输出（`dr47_gate5_out.txt`、`dr47_scope_out.txt` 等）我只当**线索**读过，并对其中可判定的部分（集合、哈希、行数）**自行重算**后才采信。
5. 我**没有**检查 `runs/smoke-t1..t5` 的内容（只核了目录 mtime 未变、未做新旧对比），因为任务书明令不假设二者可比。

## 7. 对修复批的建议（按优先级；我没有改任何代码）

1. **P0 · DEF-A（窄化过滤 + 反例测试）**：`editor_errors_baseline` 应只把引擎自身的 **INFO banner** 行（形如 `[MCP] capture=off (…on_error…)`、`[MCP] trace=off (…)`、`[MCP] role=…`、`[MCP] listening on …`、`[MCP] not listening …`、`[MCP] pending_timeout_ms=…`）排除在 `errors` 之外；**必须**配一组反例测试断言 `ERROR: [MCP] SceneTree never became available; MCP server disabled.`、`SCRIPT ERROR:`、`Parse Error:` 仍使闸门判否。修好后 E2 的闸门才重新有判别力。
2. **P0 · DEF-B/DEF-F（证据路径与"本次写入"判定）**：`save_path` 改用引擎接受的可写虚拟路径（`user://…`）或对返回的内联图像自行落盘（`running_game_capture_screenshot` 契约见 `running_game_capture.cpp:56-63`；`capture_frames` 的 inline base64 路径已在 `godot.rs:1083-1106`），并在写入前**删除/失效化**目标旧文件，使「存在即 ok」不能再被陈旧产物满足（同时保证 `capture_frames` 兜底不会被旧文件短路）。
3. **P0 · DEF-C（先定性再修）**：不要在没有归因的情况下改超时。建议修复批分两步：①用引擎侧同一端口复现一次「注册成功 → 4 次 `execute_gdscript` 返回 Nil → 第 5 次挂死」；②若可复现且指向 `execute_gdscript` 的调用形态（脚本体在游戏主循环上阻塞），再改 hof-rs 调用形态；若指向引擎游戏进程，则**上报用户**（禁止改 `godot-mcp/**`）。
4. **P1 · DEF-D（让端点身份真的落盘）**：把 `game_endpoint` 的回写移到每次电池 pass 之后（或在 `clear_game_endpoint` 时保留最后一个已失效记录），并让 `editor_status` 真正接收 `GET /mcp` 的原样响应体（`engine_identity.rs:44` 现在恒定传 `Value::Null`）；两个 reason 文案随之改为「未取到」的准确表述。
5. **P2 · DEF-E**：修正 `EDITOR_SIDE_INJECTION` 诊断句，使其以 `editor_get_input_actions` 的**实际返回**为准（当前 92 动作含 move_left/move_right/jump，却被写成"不含"）。
6. **P2 · 契约面（D220 裁决 3 的延伸）**：按 `godot-mcp/recovery/TEST-CASES.md` 的 `TC-TOOL-*` 逐工具核对 **参数形状**（本次 `save_path` 就是形状错，不是名字错），并用同一轮 `tools/list` 的 2 处 `inputSchema` 差异（`editor_get_test_report.clear.default`、`editor_simulate_input_sequence.events.items`）决定是同步夹具还是修调用方。
7. **P3 · 文档勘误**：在 `DECISIONS.md`/addendum 里把 D219 的 `108/46/23`（game 69）改为 `104/50/23`（game 73），并注明新增 6 条 = 2 editor-only + 4 BOTH；同时把 `TASK-DR47-SMOKE.md` §2 的过时判据与 `TASK-DR47-SMOKE-REPORT.md` 的 39/43 行、DEF-C 时间线一并勘误。

---

### 报告落点

本文件即 `.spec/hof-rs/tasks/TASK-DR47-ACCEPTANCE.md`。**回报：本报告路径一行。**
