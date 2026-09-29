# TASK-DR58-ACCEPTANCE — DR-58（引擎应答载荷形状修正）独立验收报告

- 验收子代理：无上游上下文、不继承实现者/调度者结论；本报告所有证据均为**本代理自己复现**。
- 批次起点 `3c10663`，被验收 HEAD `7390b9b3ea3423c81a83a194634ea293555ad89a`（`master`，未 push，`origin/master` 仍为 `3c10663ee3b444b83abd5403ce715359f1bb3dce`）。
- 任务书：`.spec/hof-rs/tasks/TASK-DR58-ACCEPT.md`；实现者报告仅作线索。
- 环境：离线；未启动 Godot、未碰端口、未联网、未调模型端点；`runs/**` 只读；未改 `godot-mcp/**`、未改 `PRD-mario.md`；未 push、未 stage、未改写历史。
- 时间：2026-09-29 15:39 → 16:5x（+0800）。

---

## 1. 结构化结论（机器可读）

```json
{
  "verdict": "pass",
  "criteria": [
    {
      "id": "SUITE",
      "pass": true,
      "evidence": "自己跑 4 次 `cargo test --offline`（exit 0）；后三次逐二进制求和 SUM passed=352 failed=0 ignored=7（/tmp/dr58_run1.txt `SUM passed=352 failed=0 ignored=7`、run2/run3 同；run1 real 6m32s）。`git diff 3c10663..HEAD -- tests/ | grep -c '^+.*#\\[(tokio::\\)\\?test\\]'` = 10（dr58_payload_shapes.rs 5 + evidence_battery.rs 5，`git diff --numstat` 亦为 331/0 与 360/6）；`git grep -c '#\\[ignore' 3c10663 -- tests/` 与 `HEAD` 逐字相同（tests/godot_smoke.rs:8，其中 1 处是注释、7 处是真 ignore），忽略数 7 未增长；evidence_battery 38 passed（基线 33+5）。定向复核：dr58_payload_shapes 5 passed / evidence_battery `node_properties` 4 passed / `the_scenario_request_omits` 1 passed，均 EXIT=0。"
    },
    {
      "id": "SCENE_PATH_PROVEN",
      "pass": true,
      "evidence": "① 冻结载荷 tests/fixtures/dr58/smoke_t7_input_channel_probe.json（字节等于 runs/smoke-t7/iter-1/candidate/.hoh/deterministic/raw/input_channel_probe.json）里 calls[4] args.scene_path=\"current\"、error.code=-32602、error.message 逐字点名 `Parameter 'scene_path' ('current') is not supported by the game-scope runner...`；② 冻结的 scenario_summary.json（= runs/smoke-t7-experiment/scenario/scenario_summary.json）中带 scene_path 的两条（'main'、'res://scenes/main.tscn'）全 -32602，而**省略**该成员的 5 条（C1/C4/C5/C6/C7）全部返回 result，其中 C4 的 args **恰为** `{steps:[hof-rs 自己的三步]}` 且返回 `in_input_map:true,injected:1`；③ 真契约 `tests/fixtures/mcp/tools_list.json` 里 running_game_run_test_scenario 的 properties 只有 `scene_path:string / steps:array`、required 只有 `steps` ⇒ 不存在“换一个参数名”与“缺其它必填项”的候选；④ 引擎源码 `godot-mcp/godot/modules/mcp_server/tools/running_game_test_execution.cpp:711-726`：scene_path 非 NIL 且 strip_edges 非空 ⇒ 无条件 -32602（与捕获同文），仅缺省/空串/纯空白通过；⑤ 版本吻合：`git -C godot-mcp/godot merge-base --is-ancestor 035edfce7 HEAD` 退出 0，且 `git log 035edfce7..HEAD -- .../running_game_test_execution.cpp` 为空 ⇒ 该文件与 smoke-t7 所用引擎 `4.8.dev.mono.custom_build.035edfce7` 同字节。"
    },
    {
      "id": "PREDICATE_NON_VACUOUS",
      "pass": true,
      "evidence": "受控植入：把 src/adapter/godot.rs:2989 `node_properties_read` 的返回改成恒真（植入后 sha256=2bea2c4838f0df46f46b1cfa460e90fce03634f86b1fc1d5cc773d837da98842）⇒ `--test dr58_payload_shapes` 1 failed（`an_unresolved_or_malformed_node_read_is_not_a_resolved_read` panicked at tests/dr58_payload_shapes.rs:319: `empty object` does not prove a resolved node: {}）；`--test evidence_battery a_malformed_node_properties` 2 failed（:1296 `Player=ok, Goal=ok, HUD=ok`；:1384 reachable=true）；我自建临时探针（8 个自造载荷）亦红。恢复后 sha256 回 aa14d764ebf9cb4660c3217edc3b939b8c3411d9b6c4bd457cd327336fa225ab（=植入前）。自造畸形全判假（见 §3）：空 properties 对象、空 node_path、properties 为数组、顶层键大小写变形（Node_Path/Properties）、nodePath 驼峰、properties=null。"
    },
    {
      "id": "G20",
      "pass": true,
      "evidence": "用真机字节直接复算：tests/fixtures/dr58/smoke_t7_node_and_collision_assertions.json 三条 running_game_get_node_properties 均 ok=true、顶层 keys 恰为 [\"node_path\",\"properties\",\"type\"]，旧判据（顶层 name 非空）=false、新判据=true（Player/Goal/HUD 三者一致；node 脚本见 §3 命令）。真机同一步骤的观测确为 `node properties: Player=missing, Goal=missing, HUD=missing`（runs/smoke-t7/iter-1/candidate/.hoh/deterministic/battery.json:137，deterministic.json:53、record-08.json:4 同），QA 自己也记为 N1/N2（.../candidate/.hoh/evidence.json:560）。probe 的同一载荷 ok=true 而 channel.game_process_reachable=false（input_channel_probe.json）。实现侧 `FixtureChannel` 的 running_game_get_node_properties 已改为从冻结字节取载荷（tests/evidence_battery.rs:288-300 real_node_properties + :770-777），不依赖手写形状。"
    },
    {
      "id": "FIXTURES",
      "pass": true,
      "evidence": "7/7 逐字节复核：`cmp -s` 全 IDENTICAL，且 sha256 与 MANIFEST.json 记录逐条相同（ce9ccf95…、f8932726…、9bfc568d…、a379e4cd…、ecbda5b6…、481c7303…、03f86916…）；`git cat-file blob \"HEAD:tests/fixtures/dr58/<f>\" | cmp -` 三个抽样亦 IDENTICAL（提交字节=工作树字节）；`git ls-files --eol` 显示 5 个 CRLF 夹具 `i/crlf w/crlf`、3 个 LF 文件 `i/lf w/lf`，`.gitattributes` 对其 `-text`。runs 未被改动：smoke-t6 135 文件 / latest 2026-09-29 02:32:01（meta.json）、smoke-t7 115 文件 / latest 14:41:14（meta.json），与 T7 报告记录逐字一致；`find runs/smoke-t7 -newermt '2026-09-29 14:42'` 为空。"
    },
    {
      "id": "NO_WEAKENING",
      "pass": true,
      "evidence": "`git diff 3c10663..HEAD --numstat` 只有 2 个既有文件有删除行：src/adapter/godot.rs 68/14、tests/evidence_battery.rs 360/6，其余全为新增。godot.rs 的 14 行删除逐条对上：两处 `.get(\"name\")` 判据块（5+5）、`\"scene_path\": \"current\",`（1）、playbook 示例 3 行；语义均为**收紧**（旧判据在真机载荷上恒 false）。evidence_battery.rs 的 6 行删除是 `running_game_get_node_properties` 的旧夹具分派（player/goal/hud_properties.json），替换为真机字节，仍对未知节点 panic（更严而非更松）。断言删除：`grep -n '=missing|=ok' tests/evidence_battery.rs` 只命中三处**本批新增**测试；既有断言未动。替身变严：新增 scene_path 拒绝（tests/evidence_battery.rs:664-671）。"
    },
    {
      "id": "STOP_NOT_GUESS",
      "pass": true,
      "evidence": "`build_check`（src/adapter/godot.rs:3408）向 editor_play_scene 发 `{\"scene_path\": self.config.main_scene}`，而真契约里 editor_play_scene 的 properties = [extra_args, headless, mcp_port, mode]、required=[]（node 读取 tests/fixtures/mcp/tools_list.json 实测），确认**无** scene_path；`grep -rn 'editor_play_scene' runs/` 的全部捕获里只有 `{\"mode\":\"main\"}` 成功（runs/smoke-t7/.../raw/play_scene_ready.json），**没有任何**捕获证明 scene_path 被拒。它确实不在电池路径上：GodotAdapter 覆写 evidence_battery（src/adapter/godot.rs:3361），trait 默认实现（src/adapter/mod.rs:167-177）调用 build_check，而两个 ProjectAdapter 实现里只有 godot 与 test_adapter，且 test_adapter 自带 build_check；GodotAdapter::build_check 仅被单测（src/adapter/godot.rs:3733，StubChannel 不校验参数）触达。⇒ 按批次纪律“形状不得猜、无捕获先上报”，不修是**正确克制**，不是遗漏（另见 §5 的 minor 裁定）。"
    },
    {
      "id": "GUARD_PRIORITY",
      "pass": true,
      "evidence": "tests/tool_vocabulary.rs 零 diff（不在 `git diff --stat 3c10663..HEAD` 列表内），SCAN_EXCLUDES 仍只列 2 项（:91-94），非空洞自证测试 `the_guard_recognises_both_vocabularies` 仍在（:338-353），4/4 passed。被丢弃的 `runs/smoke-t7-experiment/semantic/semantic_summary.json` 确实无用：`grep -rn 'semantic_summary' tests/ src/` 无引用（仅 MANIFEST note 提到）；理由写进 MANIFEST.json 的 note。⇒ 未为方便而放宽守卫，处置正确。"
    },
    {
      "id": "GUARDS",
      "pass": true,
      "evidence": "PRD sha256 = 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a（与要求一致）；`git diff --stat 3c10663 HEAD -- Cargo.toml Cargo.lock` 空（无新依赖）；`git diff --cached --stat` 空（未 stage）；`git status --porcelain` 空（终态）；`git rev-parse origin/master` = 3c10663ee3b444b83abd5403ce715359f1bb3dce（未 push；`## master...origin/master [ahead 9]`）。`git diff --stat 3c10663 HEAD -- godot-mcp` 空且 `git status --porcelain -uall godot-mcp` 0 项；注意 godot-mcp/godot 被外层 .gitignore:33 忽略且是嵌套仓（`git ls-files godot-mcp/godot` = 0），故实现者那两条命令**看不见**引擎树——我另用独立证据补上：引擎树 mcp_server 最新 mtime 2026-09-29 10:37:38（批次窗口 14:32–15:25 之前）、`git -C godot-mcp/godot status --porcelain -uno` = 0 条修改。"
    }
  ],
  "defects": [
    {
      "id": "DEF-1",
      "severity": "minor",
      "what": "禁区自查（报告 §7）对 `godot-mcp/**` 用的两条命令在**引擎树**上无效：godot-mcp/godot 被 .gitignore:33 忽略且为独立克隆，外层 git 对它零跟踪，`git status --porcelain godot-mcp` / `git diff ... -- godot-mcp` 的空输出对该子树无证明力（属任务书点名的“假绿陷阱”同族：空 diff 不等于无改动）。",
      "reproduction": "`git check-ignore -v godot-mcp/godot` → `.gitignore:33:godot-mcp/godot/`；`git ls-files godot-mcp/godot | wc -l` → 0；`git ls-files godot-mcp | wc -l` → 6484。结论未受影响：`find godot-mcp/godot/modules/mcp_server -type f -printf '%T+ %p\\n' | sort | tail -1` → 2026-09-29 10:37:38；`git -C godot-mcp/godot status --porcelain -uno` → 0 行。"
    },
    {
      "id": "DEF-2",
      "severity": "minor",
      "what": "测试替身里 scene_path 拒绝正文是**手写字面量**（tests/evidence_battery.rs:374-383 `scene_path_refusal`），不是从冻结捕获读取（对比：被接受的 scenario 应答由 :387-392 `real_scenario_payload()` 从 sc-04 字节读）。若将来手写文本漂移，没有任何测试会发现（dr58_payload_shapes 只断言 `contains(\"is not supported by the game-scope runner\")`）。",
      "reproduction": "node 比对：手写字面量拼接结果与 tests/fixtures/dr58/smoke_t7_input_channel_probe.json 的 error.message **当前逐字相等**（`equal to frozen fixture message: true`）⇒ 今日无漂移，属健壮性缺陷而非事实错误。"
    },
    {
      "id": "DEF-3",
      "severity": "minor",
      "what": "测试名/文档 `the_real_game_scope_runner_refuses_every_scene_path_value`（tests/dr58_payload_shapes.rs:107）宣称“every value”，但捕获只覆盖 3 个取值（'current'/'main'/'res://scenes/main.tscn'）；普遍性实际由引擎源码成立（该文件在 035edfce7 与 HEAD 间零改动）。测试本身未把这层源码级判定编码进去。",
      "reproduction": "node 读取冻结 scenario_summary：refused=2（C2/C3）、accepted=5；加上 in-run 的 'current' 共 3 个取值。"
    },
    {
      "id": "DEF-4",
      "severity": "info",
      "what": "`build_check` 向 editor_play_scene 传 scene_path 是**真实存在的潜在缺陷**（真契约无此参数；同一仓库的真机捕获已证明正确形状是 `{\"mode\":\"main\"}`，见 src/adapter/godot.rs:842 与 runs/smoke-t7/.../play_scene_ready.json；引擎对 schema 未声明参数会拒：runs/smoke-t6/iter-1/traj/developer.attempt1.json:4860 有 `Unknown parameter 'node_path' for tool 'editor_get_node_properties'` 的真机捕获）。本批未修可接受（不在关键路径、不在电池路径、缺该次调用的捕获），但应按“上报项”跟进一次活体捕获后修正。",
      "reproduction": "node 读 tools_list.json：editor_play_scene props=[extra_args,headless,mcp_port,mode]；`grep -n 'let play_args' src/adapter/godot.rs` → :842 `{\"mode\":\"main\"}` vs :3408 `{\"scene_path\":…}`。"
    },
    {
      "id": "DEF-5",
      "severity": "info",
      "what": "`node_properties_read` 的边界比描述略宽：`node_path` 为纯空白（\" \"）时判真；`properties` 为**非空但成员全为 null** 的对象时判真。两者都不与任务书要求的判据（非空 node_path + 非空 properties 对象）冲突，真机也不会产生这两种形状，仅作特征记录。",
      "reproduction": "我自建临时探针 tests/zz_dr58_accept_probe.rs（已删除）：`{\"node_path\":\" \",\"properties\":{\"name\":\"Player\"}}` → true；`{\"node_path\":\"/root/Main/Player\",\"properties\":{\"name\":null}}` → true。"
    }
  ],
  "risks": [
    "修好后的探针在真机上的实际能力标签仍是**推断**：判据 `(pressed, axis_after.is_some() || game_process_reachable)`（src/adapter/godot.rs:1359）会把 reachable=true 变成 GAME_INPUT_CHANNEL_OK，而真机 `input_axis` 恒 null（sc-04 明说 `node '/root/Main/Player' does not have the property 'input_axis'`），届时 probe 的 ok 会由 true 的 reachable 支撑、而非由轴移动支撑。这是 DR-35 既有定义、非本批引入，但下一轮真机不得把该 OK 读成“行为已证”。",
    "下一轮真机若 transport 仍好、可达性变真，E3 仍可能因缺少真实行为证据而不 met；不得预设 E3 转 met。",
    "证据只到“scene_path 的当前取值一律被拒”。空串/纯空白仍被引擎接受（源码 :718），该分支未被捕获；对“省略”结论无影响，但若有人日后改成发空串，仍能通过引擎——那将是另一种与引擎语义不合（把已被声明无意义的参数发出去）的形状。",
    "引擎源码级佐证依赖嵌套仓的 035edfce7 是 HEAD 的祖先且该文件零改动；引擎构建非位级可复现（§15.4），未从二进制反证。",
    "DEF-1 所示的方法论弱点可能同样存在于本仓其它“零 diff”自查：凡涉及被 gitignore 的子树（godot-mcp/godot、runs/**、target/**），外层 git 的空 diff 都不能当证据。"
  ],
  "unverified": [
    "修好后的输入通道探针在真引擎上的运行结果（本批离线，不允许启动 Godot；无任何本批输出可支撑）。",
    "实现者报告的首跑 exit 1 / 日志截断 flake 的成因：我自己 4 次全量 `cargo test --offline` 均 exit 0（3 次含完整求和 352/0/7），未复现；全仓只找到一处墙钟断言（tests/endpoint_liveness.rs:498-501，5 s 预算），仅为**假设**、未定性。",
    "editor_play_scene 对未声明参数 scene_path 的**该次调用**是否真被拒：无捕获（仅有另一工具的真机 unknown-parameter 捕获与引擎源码规则）。",
    "`godot-mcp/godot` 未跟踪文件的完整清单（4.7 GB 克隆，只核了 tracked 修改与 mtime）。",
    "实现者 §8 的其它推断项（手册 `position:x` 在 run_test_scenario 下是否被拒）未独立复核，只核对到它**确实未被修**、且 B5 只覆盖 assert_node_state。"
  ]
}
```

---

## 2. 逐项核对表（TASK-DR58-ACCEPT §1 九项）

| # | 项 | 我的命令（节选） | 真实输出 | 判定 |
|---|---|---|---|---|
| 1 | 套件绿 / ignored 未增 / +10 自洽 | `cargo test --offline` ×4；`awk` 求和；`git diff … --numstat`；`git grep -c '#\[ignore'` | EXIT=0 ×4；`SUM passed=352 failed=0 ignored=7`；新增 `#[test]` 恰 10（5+5，见 numstat 331/0 与 360/6）；ignore 计数 3c10663 与 HEAD 相同；evidence_battery 38 | PASS |
| 2 | `scene_path` 结论是否被证据唯一确定 | `cmp` 夹具↔真机；node 读 sc-02/03/04；`git -C godot-mcp/godot merge-base --is-ancestor 035edfce7 HEAD`；读引擎源码 :711-726 | 拒绝正文点名 scene_path；3 个取值全 -32602；省略的 5 条成功（C4=hof-rs 原 steps）；源码对任何非空串无条件拒；035edfce7 是祖先且该文件零改动 | PASS（判定，非猜；见 §4） |
| 3 | 判据非空洞 | 植入恒真（sha 2bea2c48…）后跑定向测试；自建 8 载荷探针 | dr58_payload_shapes 1 failed（:319）；battery 2 failed（:1296 `Player=ok…`、:1384 reachable=true）；探针红；恢复后 sha 回 aa14d764… | PASS |
| 4 | G20 真机成功载荷不再被判 missing（不靠伪造数据） | node 复算冻结字节 + 旧/新判据 | Player/Goal/HUD：ok=true、keys=[node_path,properties,type]、old=false、new=true；真机观测 `Player=missing…`（battery.json:137）；实现侧夹具已改读真机字节 | PASS |
| 5 | 夹具逐字节可信 + runs 未动 | `cmp -s`/`sha256sum` ×7；`git cat-file blob … \| cmp -` | 7/7 IDENTICAL 且 sha 与 MANIFEST 相同；提交 blob=工作树；smoke-t6 135/latest 02:32:01、smoke-t7 115/latest 14:41:14 | PASS |
| 6 | 无既有断言放宽 | `git diff … --numstat`；逐条对删除行；`grep '=missing\|=ok'` | 仅 godot.rs 14 删 / evidence_battery 6 删，语义全部为收紧；断言命中只在本批新测试 | PASS |
| 7 | `build_check` 停手 vs 遗漏 | node 读 tools_list.json；`grep -rn editor_play_scene runs/`；读 3361/3408/3733 与 mod.rs:167 | 真 schema 无 scene_path；无该调用捕获；GodotAdapter 覆写电池 ⇒ 不在电池路径 | PASS（正确克制；DEF-4 跟进） |
| 8 | 守卫优先级 | `git diff --stat` 是否含 tool_vocabulary；读 SCAN_EXCLUDES/自证测试；grep semantic_summary | tool_vocabulary 零 diff、排除表仍 2 条、4/4 passed；被弃夹具无引用 | PASS |
| 9 | 禁区与陷阱 | PRD sha；Cargo diff；`git status -sb`；`git rev-parse origin/master`；两条假绿陷阱实测 | PRD sha 相符；Cargo 零 diff；未 stage；origin/master=3c10663；不存在 pathspec 时 `git diff` 退出 0（演示）；cmd 下裸 `HEAD^` → 7390b9b（=HEAD）而 `"HEAD^"` → f68410d | PASS（DEF-1 记录方法弱点） |

补充（TASK-DR58 任务书约束）：

- **未 push / 未 stage / 未改历史**：`git status -sb` = `## master...origin/master [ahead 9]`；`git diff --cached --stat` 空；`git rev-parse origin/master` = `3c10663…`。
- **未改 godot-mcp**：tracked 零 diff（6484 项）；引擎树（嵌套仓、被忽略）最新 mtime 10:37:38、`-uno` 零修改（见 DEF-1）。
- **未改 PRD**：sha `4c81c3a9…5c3a`。
- **无新依赖**：`Cargo.toml`/`Cargo.lock` 零 diff。
- **runs 只读**：文件数与最新 mtime 与 T7 记录逐字一致，批次窗口后无新 mtime。

---

## 3. 反例清单（我自己的植入 + 观测 + 是否推翻）

### 3.1 受控植入（唯一允许的改动；逐字节恢复并三法证明）

| 步骤 | 内容 | 命令 | 结果 |
|---|---|---|---|
| 前置 | 备份 + 记录 | `cp src/adapter/godot.rs /tmp/godot.rs.bak`；`sha256sum`；`git hash-object` | 植入前 sha256 `aa14d764ebf9cb4660c3217edc3b939b8c3411d9b6c4bd457cd327336fa225ab`，194051 B，`git hash-object` = HEAD blob `9960917a4c460d8d0e457ea3960707470846c138`，`git status --porcelain` 仅 `?? tests/zz_dr58_accept_probe.rs`（我的临时探针） |
| 植入 | `node_properties_read` 返回恒真 | edit：`resolved && properties` → `let _ = (resolved, properties); true` | 植入后 sha256 `2bea2c4838f0df46f46b1cfa460e90fce03634f86b1fc1d5cc773d837da98842` |
| 观测 A | 判据级 | `cargo test --offline --test dr58_payload_shapes` | **FAILED. 4 passed; 1 failed**：`an_unresolved_or_malformed_node_read_is_not_a_resolved_read` panicked at `tests/dr58_payload_shapes.rs:319:9`：`` `empty object` does not prove a resolved node: {} `` |
| 观测 B | 步级（G20/可达性） | `cargo test --offline --test evidence_battery a_malformed_node_properties` | **FAILED. 0 passed; 2 failed**：:1296 `an unresolved payload is not evidence: … "node properties: Player=ok, Goal=ok, HUD=ok; …"`；:1384 `left: Bool(true) right: Bool(false)`（`reachable=true`） |
| 观测 C | 我自造的 8 个载荷 | `cargo test --offline --test zz_dr58_accept_probe` | **FAILED**（恒真后第一个畸形即红） |
| 恢复 | `cp /tmp/godot.rs.bak src/adapter/godot.rs`；`rm tests/zz_dr58_accept_probe.rs` | `sha256sum`、`git status --porcelain`、`git diff --stat`、`git hash-object`、`git ls-files --eol` | sha256 回 `aa14d764…`；`git status --porcelain` **空**；`git diff --stat` **空**；`git hash-object` = `9960917a…` = `git rev-parse HEAD:src/adapter/godot.rs`；eol 仍 `i/lf w/crlf` |

**结论：恒真化必然变红 ⇒ 判据非空洞。** 增补：把判据改成恒假（实现者报告的红①/红③）我未重复植入，但由真机字节直接复算（§3.3）已独立证明真机载荷在新判据下为真、在旧判据下为假。

### 3.2 我自造的畸形载荷（≥4 个不同类别，覆盖任务书点名的四类）

| 载荷 | 类别 | 期望 | 实测 |
|---|---|---|---|
| `{"properties": {}}` | **空 properties 对象** | false | false ✅ |
| `{"node_path":"","properties":{"name":"Player"}}` | **空 node_path** | false | false ✅ |
| `{"node_path":"/root/Main/Player","properties":["name"]}` | **properties 是数组** | false | false ✅ |
| `{"Node_Path":"/root/Main/Player","Properties":{"name":"Player"}}` | **顶层键大小写变形** | false | false ✅ |
| `{"nodePath":"/root/Main/Player","properties":{"name":"Player"}}` | 驼峰键名变形 | false | false ✅ |
| `{"node_path":"/root/Main/Player","properties":null}` | properties 为 null | false | false ✅ |
| `{"node_path":" ","properties":{"name":"Player"}}` | 纯空白 node_path（特征记录） | — | true（DEF-5） |
| `{"node_path":"/root/Main/Player","properties":{"name":null}}` | 非空但成员全 null（特征记录） | — | true（DEF-5） |
| 真机 Player 载荷（冻结字节） | 真实成功载荷 | true | true ✅ |

### 3.3 G20 从真机字节的独立复算（不经过测试替身）

```
$ node "C:/Users/wyl/AppData/Local/Temp/dr58-accept-g20.js"
Player ok=true keys=["node_path","properties","type"] oldPredicate=false newPredicate=true
Goal   ok=true keys=["node_path","properties","type"] oldPredicate=false newPredicate=true
HUD    ok=true keys=["node_path","properties","type"] oldPredicate=false newPredicate=true
probe player keys=["node_path","properties","type"] oldPredicate=false newPredicate=true
probe recorded reachable=false capability=ACTION_BINDING_UNKNOWN
```

⇒ 旧顶层 `name` 判据在真机载荷上**恒假**（G20 与 DR-54 的 `reachable` 恒 false 同因），新判据为真；与真机观测 `Player=missing, Goal=missing, HUD=missing`（battery.json:137）自洽。

### 3.4 假绿陷阱实测（任务书点名两条）

- **不存在的 pathspec**：`git diff --stat HEAD -- godot-mcp/definitely/not/here` → 无输出、`exit=0`。⇒ 空 diff 必须先用 `git ls-files <path> | wc -l`（本例 godot-mcp 6484、godot-mcp/godot **0**）证明命中。
- **cmd 的 `^`**：`cmd` 里 `git rev-parse HEAD^` → `7390b9b…`（=HEAD，`^` 被吞）；`git rev-parse "HEAD^"` → `f68410d…`（真父提交）。⇒ 引号与否会静默改变 `3c10663^:path` 的含义。

### 3.5 是否推翻实现者结论

**没有推翻任何一项主结论。** 五处 minor/info（DEF-1..5）中，只有 DEF-3 涉及“宣称强于证据”，且已由引擎源码在**同版本同文件**上补齐；DEF-4 是实现者自己上报的未关闭项。

---

## 4. 对 `scene_path` 真形状的独立判定

**判定：`running_game_run_test_scenario` 的请求**必须省略** `scene_path`，只发 `steps`。证据足以**确定**，不是猜。**

候选形状逐一排除：

1. **“换一个参数名就能成功”** —— 排除。真契约（`tests/fixtures/mcp/tools_list.json`，真机 `tools/list`）里该工具的 `properties` 只有 `scene_path` 与 `steps`，且引擎自述 “Accepted parameters of running_game_run_test_scenario: scene_path, steps”（冻结在 sc-02/sc-03 的 `error.data.suggestion`）。引擎对 schema 未声明的名字是拒的（真机捕获：`Unknown parameter 'node_path' for tool 'editor_get_node_properties'`，runs/smoke-t6/iter-1/traj/developer.attempt1.json:4860）。
2. **“失败真由 scene_path 引起吗？正文点名它吗？”** —— 是，逐字点名：`Parameter 'scene_path' ('current') is not supported by the game-scope runner: the migration source used it to make the *editor* play a scene before the steps ran…`（冻结 `input_channel_probe.json` calls[4].error.message）。三个不同取值（'current'、'main'、'res://scenes/main.tscn'）同一条正文，说明拒绝是**参数级**而非取值级。
3. **“该成员必填但我们缺别的必填项”** —— 排除。`required` 只有 `["steps"]`；且省略 scene_path 的 C4 请求体**恰好**是 `{steps:[hof-rs 自己的三步]}` 并返回逐步骤结果（`in_input_map:true, injected:1`）。
4. **“合法 res:// 路径是否可行 / 换空串”** —— `res://scenes/main.tscn` 已被 C3 直接拒（-32602）。空串/纯空白**确实未被捕获排除**：引擎源码 `running_game_test_execution.cpp:711-726` 只对 `strip_edges()` 非空的字符串报错，空串会落过。因此“**省略**是否**唯一**可行的形状”严格地说不是；但“**省略**是一种被真机证明可接受的形状”是**直接观测**，且是引擎错误正文自己指出的路径（“Use editor_play_scene (editor endpoint) first, then run the scenario”）。发空串等于把一个引擎已声明无意义的参数留着——与 DR-58 的整改意图相悖，也不是任何证据要求的形状。
5. **“只是一个碰巧能跑的形状”** —— 排除。省略之所以可用，是因为该参数属于编辑器侧迁移来源、在游戏态 runner 里没有对象（源码注释 :707-710 明说“silently ignoring it would let a caller believe…”）。这正是它对该 runner **结构性无意义**的原因。

版本吻合度（这条把“源码级旁证”升级为强证据）：`git -C godot-mcp/godot merge-base --is-ancestor 035edfce7 HEAD` 退出 0，且 `git log 035edfce7..HEAD -- modules/mcp_server/tools/running_game_test_execution.cpp` **为空** ⇒ 我读到的源码与 smoke-t7 所用引擎 `4.8.dev.mono.custom_build.035edfce7` 是**同一份**（该文件未变）。唯一保留：引擎构建非位级可复现，未从二进制反证。

⇒ **TASK-DR58-ACCEPT §3 的 fail 门槛不成立**（“结论未被证据唯一确定”）。该步是**判定**；实现者的写法（请求体只保留 `steps`，并在注释里写下逐字的拒绝正文与“契约声明 ≠ 引擎接受”）正确。

---

## 5. 对 `build_check` “未修”的独立判定

**判定：本批“不修 + 上报”是正确克制，不是遗漏；但 DEF-4 是一个真实存在的潜在缺陷，应在下一批用一次捕获收口。**

支持“正确克制”：

1. 任务书的三处必修不含它；它由“顺便扫描同模式”发现，属超出范围的候选。
2. 不在电池路径上：`GodotAdapter` 覆写 `evidence_battery`（src/adapter/godot.rs:3361）；`build_check` 只被 **trait 默认** `evidence_battery`（src/adapter/mod.rs:167-177，被 `TestAdapter` 使用）和 godot 的单测（:3733，StubChannel 不校验参数）触达、且是 `pub` trait 方法（无生产调用点，`grep -rn build_check src/` 只有这三处）。⇒ 对 E3/smoke 轮次零影响。
3. 该次调用**没有**捕获（`grep -rn 'editor_play_scene' runs/` 只找到 `{"mode":"main"}` 的成功记录）；批次纪律是“无捕获不猜形状”。

支持“其实已有间接证据、应尽快修”：

- 真契约明说 editor_play_scene 无 `scene_path`；
- 同仓的真机捕获已证明正确形状 `{"mode":"main"}`（src/adapter/godot.rs:842 与 play_scene_ready.json）；
- 引擎拒未声明参数有真机捕获（另一工具）+ 其审计报告（M4e）。

⇒ 我的裁定：**不构成 fail**（TASK-DR58-ACCEPT 的 fail 门槛要求“应修而未修**且证据充分**”；这里缺的是**该调用本身**的证据，且修复不在关键路径），但“无捕获证明它会被拒”这句话比它听起来更弱——正确形状其实已在仓内被真机证明过。建议下一批：用 `{"mode": self.config.main_scene}`（或按 `mode` 语义归一）替换 `:3408`，并加一条断言 editor_play_scene 的实参形状的测试（现在**没有**任何测试校验该实参）。

---

## 6. 未验证项与理由（含 flake 结论）

1. **flake（首跑 exit 1 / 日志截断）**：**未复现**。我自己跑了 4 次全量 `cargo test --offline`，全部 exit 0；其中 3 次做了逐二进制求和，均为 `passed=352 failed=0 ignored=7`（/tmp/dr58_run1.txt 的 `real 6m32.200s`）。全仓只有一处墙钟敏感断言：`tests/endpoint_liveness.rs:498-501`（“死端点不得烧完 30 s 预算”，预算 5 s，被断言的操作本身是立即失败）。它在极端负载下理论上会红，但这是**假设、未定性**；我不把它当解释，也不把 flake 当作不存在。（实现者主动披露且未掩盖，态度正确。）
2. **修好后的探针在真机上的结果**：未验证（离线、禁止启动 Godot）。判据链 `(pressed, axis_after.is_some() || game_process_reachable)`（src/adapter/godot.rs:1359）显示它会变成 OK，但这是**源码推断**；且真机 `input_axis` 恒 null（sc-04/C4 与 sc-06 明说 `does not have the property 'input_axis'`），`moved_while_pressed` 仍会是 false。
3. **editor_play_scene 对 scene_path 的该次拒绝**：无捕获（见 §5）。
4. **引擎二进制 vs 源码 commit**：文件级零改动+祖先关系已证；未做二进制级反证（批次规则本身也禁止把二进制 sha 当新鲜度判据）。
5. **`godot-mcp/godot` 的未跟踪文件**：只核了 tracked 修改与 mtime，未枚举 4.7 GB 克隆的未跟踪项。

---

## 7. 我没有独立复核的部分

- 实现者报告里的**逐次 TDD 红输出**（红①/红②/红③ 的原文）我是按“线索”读的，没有逐字复跑它们当时的中间状态；我复跑的是**当前 HEAD 的终态**（全绿）与**我自己的植入反例**（必红）。红①的等价性另由“真机构造下判据为真、旧判据为假”的复算与恒真植入的必红所覆盖。
- `runs/smoke-t7` 与 `runs/smoke-t7-experiment` 的产生过程（真机轮次本身）不在本批范围内，我只核对其字节未被本批改动、并把它当作第三方记录引用。
- §15 设计文本（DR-54..DR-56）与 D240/D241 的**历史决策合理性**未复核，只核对本批实现与它们一致。
- 我未复核实现者 §6 扫描表里“非缺陷”的每一行（如 `scenario_axis`、`observed_after` 的宽容读法），只抽查了与三处修正直接相关者；也未复核 `src/tools/index.rs`/`src/tools/mcp.rs` 的 `name` 读法（那确是真机形状）。

---

## 8. 给下一批的建议（我不改任何代码）

1. **DR-58 可推**：本批三处修正正确、证据充分、无既有断言放宽、禁区未破、离线门全绿。建议按 D241 的排期推送并继续（推送由决策者执行；我未 push、未 stage）。
2. **下一轮真机（E3 判定）前先明确语义**：修好后 `GAME_INPUT_CHANNEL_OK` 会由“节点可读”支撑，而 `axis_after` 仍为 None、`moved_while_pressed` 仍为 false。请在真机报告里显式区分“通道可读”与“行为已证”，不要因为 probe 的 ok 变真而给出 E3 met。
3. **补一次 `editor_play_scene` 的形状捕获并修 `build_check`（DEF-4）**：建议用 `{"mode": …}`，并新增一条断言其**实参形状**的测试（当前无任何测试覆盖该实参；StubChannel 吞掉一切）。
4. **把 DEF-2 收口**：让 `scene_path_refusal` 从冻结字节（input_channel_probe.json 的 error.message / sc-02）派生，避免替身与真机文本漂移而无人发现。
5. **DEF-1 的方法论补强**：凡“零 diff”自查涉及被 gitignore 的子树（`godot-mcp/godot/`、`runs/`、`target/`），必须用“该子树是否被外层 git 跟踪 + mtime/嵌套仓状态”补证；建议把这条写进验收任务书模板。
6. **`semantic_summary.json` 的守卫冲突**：本批以“丢弃未使用的拷贝”解决，方向正确；若将来需要该证据入测试，应改夹具内容为**提取后的形状子集**（不含退役工具名的 label），而不是把文件加入 SCAN_EXCLUDES。
7. **flake 若再现，请保留完整日志**：`cargo test --offline 2>&1 | Tee-Object` 会截断，建议直接重定向到文件；首要怀疑对象是 `tests/endpoint_liveness.rs:498` 的 5 s 墙钟断言。
8. **设计文档**：D240 新增的“引擎应答形状必须来自活体捕获、不得读契约推断”目前只记在 DECISIONS.md，DESIGN-DETAIL §15 未含。建议在下一节（§16）里把它写成硬性设计条款，而不是只留在决策日志。

---

## 附录：本报告的复现命令清单

```bash
# 套件（4 次）
cargo test --offline                                   # EXIT=0；SUM passed=352 failed=0 ignored=7
# +10 自洽
git diff 3c10663..HEAD -- tests/ | grep -c '^+.*#\[\(tokio::\)\?test\]'   # 10
git grep -c '#\[ignore' 3c10663 -- tests/ ; git grep -c '#\[ignore' HEAD -- tests/
# 夹具
for pair in ...(见 §1 FIXTURES)...; do cmp -s "$f" "$s" && sha256sum "$f" "$s"; done
git cat-file blob "HEAD:tests/fixtures/dr58/smoke_t7_sc_04_scene_path_omitted.json" | cmp - tests/fixtures/dr58/smoke_t7_sc_04_scene_path_omitted.json
# scene_path 判定
node -e "...(读 tools_list.json 的 running_game_run_test_scenario/editor_play_scene 形状)..."
git -C godot-mcp/godot merge-base --is-ancestor 035edfce7 HEAD ; echo $?       # 0
git -C godot-mcp/godot log --oneline 035edfce7..HEAD -- modules/mcp_server/tools/running_game_test_execution.cpp  # 空
# 非空洞植入 + 恢复
sha256sum src/adapter/godot.rs; git hash-object src/adapter/godot.rs; git rev-parse HEAD:src/adapter/godot.rs
cargo test --offline --test dr58_payload_shapes         # 植入恒真 → 1 failed (:319)
cargo test --offline --test evidence_battery a_malformed_node_properties   # → 2 failed (:1296,:1384)
# 恢复三法
git status --porcelain ; git diff --stat ; git hash-object src/adapter/godot.rs   # 空/空/9960917a…
# 陷阱实测
git diff --stat HEAD -- godot-mcp/definitely/not/here ; echo $?                # 空、exit 0
git ls-files godot-mcp | wc -l ; git ls-files godot-mcp/godot | wc -l          # 6484 / 0
# cmd 下：git rev-parse HEAD^  vs  git rev-parse "HEAD^"
```
