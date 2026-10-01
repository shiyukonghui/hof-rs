# TASK-SMOKE-T12-ACCEPTANCE — 独立验收（全新子代理，无上游上下文）

- 被验收对象：`.spec/hof-rs/tasks/TASK-SMOKE-T12-REPORT.md`（**线索，不是证据**）+ `runs/smoke-t12/**` 原始件。
- 验收者：独立子代理（**不是**本轮实现者，未继承其任何结论）。落点：`F:\moonbit-hof-rs`。
- 复核时 HEAD：`d559961e…`（轮内 HEAD = `47680397…`，与本报告所述一致）。
- 约束遵守：**离线**（未启动引擎、未跑任何轮、未联网）；只读 `runs/**`（未写入一个字节）；未改动冻结规范 / `DECISIONS.md` / `godot-mcp/**`；未 push、未 stage；临时材料全部在仓库外的 `%TEMP%\t12acc`；**未使用 `rm -rf`**（唯一删除是 `shutil.rmtree` 作用于我自建的临时目录）。

## 0. 判定摘要

| 项 | 判定 | 一句话依据 |
|---|---|---|
| 六条判据 E1..E6 | **全部 met（我逐条复现）** | E3 的四类读数、金币 `0→2`、`Goal.reached false→true` 全部来自**游戏端点语义工具的原始回包**，且各有一发 `running_game_assert_node_state passed=true` |
| 全新工程条款 + 闸门 | **成立** | 我的独立 `hash_tree` 复算 A0=3ac25f6c…(3 文件/1727 B)→A1=fc50ecd2…(11 文件/7384 B)；A0 的 `project.godot` 与 T11 的 A0 **逐字节同 sha** ⇒ 真来自 `hoh init` |
| 修复 ① 遗留动作释放 | **绿（我复现）** | `release_stale_move_left` 在 call[4]，首批驱动在 call[6]；三批各 **60/60 唯一 x** 推进 |
| 修复 ② 观测早于消耗 | **绿（我复现）** | 电池序 6 < 7 < 8；观测窗口**自己的**前后读数是 `Coins: 0`→`Coins: 2` |
| 修复 ③ 路由重发布 | **未触发 ⇒ 该行为仍不可判定（我同意）** | 我的独立普查：39 次 `tools call`，`running_game_*` **0**、`editor_play_scene` **0**；0 次拒绝**不构成**证据 |
| 只读基线 8 条 | **开工=收工=现在，逐字节相同** | 我自写的 culture-order 口径先自证命中 `smoke-t6 = c144ef32…` |
| 机器可读块 | **合法** | 栅栏感知扫描：26 个栅栏、1 个 `json` 块、`json.loads` 通过、与 `machine_block.json` 逐字相同 |
| 报告诚实性 | **总体诚实，但有 3 处实质瑕疵 + 若干计数瑕疵** | 见 §3；其中「两次启动的原始控制台输出都在证据里」**不成立** |

**总判定：`pass`（六条判据与两处绿修复均由我独立复现）；但环境性 A/B 对照的 A 侧原始件缺失，属未证实项。**

> 口径声明：本报告所有数字都来自我自己跑出来的脚本或直接读取的原始件；被验收报告的正文只用于**定位**。

## 1. 逐项核对表

| # | 任务要求 | 我的独立读数 | 结论 |
|---|---|---|---|
| 1 | **E3 四类行为**各有游戏进程内断言 | 左移 `-216.332458496`（call[43]）、右移 `+216.333312988`（call[7]）、跳跃 x 唯一 1 / y 唯一 30（call[31]）、金币 `Coins: 0`(call[0])→`Coins: 2`(call[24]) 且 `text:neq` `passed=true`(call[26])、`reached false`(call[1,10,16])→`true`(call[22,25]) 且 `reached:neq` `passed=true`(call[27])。四发位置断言 `passed=true` | **成立** |
| 1b | 金币与胜负来自**语义工具原始回包**，非推断 | 读数 tool 名 = `running_game_get_node_properties` / `running_game_assert_node_state`；契约实测 177 = 104 editor + 48 project + 23 running + 2 os，编辑器端点 154 个工具中 `running_game_*` = **0**，游戏端点 73 个中 23 个；引擎源码 `scope_matches` 按 `is_editor_hint()` 过滤 | **成立** |
| 1c | 摘要链：3 文件脚手架 → 11 文件工程，改动落在工程文件 | 我自实现 `relpath\n{len}\n{bytes}\n` 排序流口径：两个 `versions/` id 与其目录名**逐字相同**；三棵树（冻结 A1 / `iter-1/candidate` / 活体工作区）11 文件全部 sha256 相同；新增 8 个 `scripts/*.gd(.uid)`、改 `scenes/main.tscn` 342→3580 B、删除 0 | **成立** |
| 2 | 目录可证为空 → init → **恰好一轮** | 空目录原始 `ls` = `total 0`、`find -mindepth 1` = 0；`init` exit 0，产物 3 文件；`runs/smoke-t12` 恰一个 run、一个 `iter-1`、versions 只有 iteration 0/1；215 个文件最老 mtime = **02:49:33 = 唯一那条 `hoh run` 的 START** | **成立（空目录清单本身是自述件，见 §4）** |
| 2b | 环境 A/B：空目录 → `role=game`/73；有 `project.godot` → `role=editor`/154 | B 侧强证据（`wmic` 原始 cmdline/pid 33556、`meta.json.listener` 同 pid、doctor `154 tools`、`tools_list_editor_live.json` 154、`scope_tree_editor.json` 含 `res://project.godot`+`scenes/main.tscn`+`scripts/README.md`）；A 侧**无原始启动件**，被引用的 `probe_empty_tools.json` **不存在** | **半证实（B 强 / A 未证实）** |
| 2c | 书里的顺序是否真的必须 | 必须：编辑器启动即固定工程（177 个工具无一能切换），而无 `project.godot` 的目录无法被编辑器打开 ⇒ 必须 `init` 在前；本轮 `project_list_scripts` = 0 对 mario 15 也证明编辑器确实开在新工程 | **顺序成立** |
| 3 | 修复 ① 真机读数 | call[4] 释放 → call[6] 首批；batch x 唯一数 60/60/60，首末 67.33→283.67→511.00→738.33；`STALE_ACTION_NOT_RELEASED` 0 次 | **绿** |
| 3b | 修复 ② 真机读数 | 步骤序 `interaction_evidence`=6 < `input_channel_probe`=7 < `input_replay`=8；观测窗口自身 call[0]=`Coins: 0`、call[24]=`Coins: 2`，判定行含 `COIN_PICKED_UP`/`WIN_DRIVEN` | **绿** |
| 3c | 修复 ③ 的裁定 | 4 个未脱敏轨迹 39 次 `tools call`（我的正则已做负控），`running_game_*`=0、`editor_play_scene`=0；路由文件确实有两个值（57989/29776 与 53694/25236），报告**拒绝归因** | **未触发，criterion 应视为 undecided（同意）** |
| 4 | 六条判据诚实性 | E1..E6 met；qa_report `Verdict: partial` 与其 12 verified / 10 gap **逐条一致**；无一条被标 undecidable 而实际可判，也无一条被标 met 而实际不可判（E3 有真读数） | **成立** |
| 4b | 未借用别轮证据 | `evidence.json` 里 34 条记录的 `path` 与全文**均不出现** `smoke-t9/t10/t11` | **成立** |
| 5 | 开发者两次触限 + wrap-up 重试 | 复现：attempt1 150 calls / attempt2 25 calls，两次 `LimitsExceeded` + `artifact_valid=false`，`wrap_up_retry_used=true / reason=artifact_missing` | **复现，但「首次出现」为假（T10 同形，见 §3）** |
| 6 | 八条只读基线 | 我自写的 PowerShell 口径复算：8 条**全部**与 `baseline_before/after/final` 逐字符相同（含 count 与 newest mtime）；自证命中 `smoke-t6 = c144ef32…7a9c03` | **成立** |
| 6b | 排序口径是否要紧 | 要紧：同一棵 `smoke-t8` 在 ordinal 序下 `c347bd63…`、在 culture 序下 `6d11b2c6…`；mario `f622f5b0…` vs `dee0a36f…` | **成立（引用必须写口径）** |
| 6c | 冻结件 / 引擎树 / Cargo / 新依赖 | PRD sha `4c81c3a9…5c3a`；`DECISIONS.md` sha `eb709008…`（= 收工值）；嵌套引擎 `fc63af77…` porcelain 0；DR-78 提交与 `4768039..d559961` 均未改 `Cargo.toml/lock` | **成立（无新依赖）** |
| 6d | release 二进制重建且含新串 | 12,713,984 B / mtime 02:45（晚于 HEAD 02:40:57）/ sha256 `310075fa…7158ca`；`strings` 含 `STALE_ACTION_NOT_RELEASED`(1) 与 `the game the role started with \`editor_play_scene\` did not answer`(1) | **成立** |
| 6e | 暂存目录是否污染基线 | `.workspace/.t12-scratch` 在 `.workspace/` 下（gitignore）、**不属于**任何一条基线子树；收工时已不存在；`fresh-t12` 当前的 `.t12pre`/`.t12-scratch` 均已无 | **不构成污染** |
| 6f | 机器可读块 | 26 栅栏 / 1 个 `json` / `json.loads` 通过 / 与 `machine_block.json` 逐字相同 | **成立** |
| 6g | 零写入窗口 | `find runs -newermt "2026-10-02 02:49:33" | grep -v smoke-t12` = **0**；`mario` = 0；`fresh-t11` = 0 | **成立** |

## 2. 我自己做的植入与反例

1. **口径自证 + 灵敏度植入**：自写 PowerShell 口径（culture-order `Sort-Object`、仓根相对小写 POSIX 路径 + TAB + 字节数 + TAB + sha256，LF、无尾随换行）先复现任务书锚点 `runs/smoke-t6 = 135 文件 / c144ef32…7a9c03 / newest 2026-09-29 02:32:01`；再把 t6 复制到**仓库外**临时目录并植入一个文件 ⇒ 计数 135→136、摘要改变 ⇒ 该方法**灵敏**（并且证明仓根相对前缀是承重的：换路径即换值）。
2. **排序反例**：同一文件集在 ordinal 序与 culture 序下摘要不同（`smoke-t8`、`mario`），所以任何引用都必须写明口径。
3. **探测器负控**：我的 `tools\s+call\s+(\w+)` 对合成的 `tools call running_game_get_scene_tree` / `tools call editor_play_scene` 均能命中，而对「分析命令里仅仅出现 `running_game_` 字样」不命中 ⇒ §1/§3c 的 **0 是真阴性**，不是探测器坏了。
4. **端点归属反例**：编辑器端点 154 个工具里 `running_game_*` = 0 ⇒ 金币/胜负的 `running_game_*` 回包**不可能**来自编辑器端点。
5. **借用证据反例**：`evidence.json` 无任何记录或字符串指向其它轮。
6. **哈希复算植入**：我自实现 `hash_tree`，两个版本 id 与三棵树一致性都能命中；若拿别的 exclude 集合（如不排除 `.hoh`）则全不命中 ⇒ 该结果不是凑出来的。

## 3. 缺陷清单（我不修，只报）

| id | 严重度 | 是什么 | 复现 |
|---|---|---|---|
| **T12A-1** | **major** | 报告 §11.2 断言「两个进程、两次启动的原始控制台输出都在证据里」**不成立**：`evidence/round/` 里没有任何启动控制台捕获，`[MCP] role=game/editor` 与 `role=` 字样只出现在报告自身及其 `report_part*.md` 副本里；§1.2 引用的 `probe_empty_tools.json` **全仓不存在** | `grep -rn \[MCP\] runs/smoke-t12/`；`grep -rn role=game\|role=editor runs/smoke-t12/`；`find . -name probe_empty_tools*`（空）；`ls runs/smoke-t12/evidence/round/` |
| **T12A-2** | **major** | A/B 对照的 **A 侧无原始件**：`tools_list_game_mode.json` 是不带端口/路径/pid/时间的裸 `tools/list` 回包，首次启动（pid 22908）与 9881 探针都没有 `wmic`/控制台捕获 ⇒ 机制归因只剩自述 | `head -c 400 …/tools_list_game_mode.json`；`grep -rn 9881 runs/smoke-t12/evidence/`（只有报告正文） |
| **T12A-3** | medium | `evidence/analysis/{e3_extract.txt, mechanisms2.txt, route_trace.txt}` **不是合法 UTF-8**（GBK 控制台重定向），是 T11A-3 家族的复发；报告 §9(d) 只自证了 JSON 块 | `python utf8scan.py runs/smoke-t12` |
| **T12A-4** | medium | §10 的「`wrap_up_retry_used=true` 本轮**首次出现**」为假：`smoke-t10` 已是同一形态（同 reason、同 150+25 calls） | `python mech_cmp.py` |
| **T12A-5** | medium | 轮总 tokens `17,703,610` 取自被**双计**的 `result.json.usage`：planner 聚合 90 calls/901,668 恰是单次 attempt（45/450,834）的两倍；attempts 之和 = `17,252,776`；planner 轨迹本身只有 40 条 assistant、合计 373,275。T10/T11 无此现象 ⇒ **本轮新异常** | `python usage_cmp2.py`；`python traj_tokens.py` |
| T12A-6 | minor | 计数口径缺失/不一致：§2.4 的 `33` 只数了 verified 身上的记录（verified+gap=34）；§2.6 的「8 组」既不等于 6 条 bullet 也不等于 10 个 gap 家族；§0.1 的「38 次」与它自己 §3.3 的枚举（39）及我的复算（39）不符 | `python e4_check.py`；读 `qa_report.md` Gaps；`python tool_census.py` |
| T12A-7 | minor | §7 的「最大单条消息 50,026 B」只是 **tool-role** 消息；最大**序列化消息记录**是 112,115 B（tester）。64 KiB 上限针对工具输出，实质结论（未触发）成立，但措辞会被误读 | `python max_msg.py` |
| T12A-8 | minor | `evidence/round/scope_project_tree.json` 是**被污染且已作废**的捕获（只有 `res://.t12pre`），却留在证据里且未标 superseded；报告实际依赖的是 `scope_tree_editor.json` | `cat …/scope_project_tree.json` vs `…/scope_tree_editor.json` |
| T12A-9 | info | §1.3 说 doctor 的 `project_file/editor_scope` 逐字指到 `fresh-t12`；这只对**轮内 inline doctor**（`round_console.txt`）成立，独立 `doctor_live_final.txt` 指的是 `.workspace/mario` | 两文件对照 |

## 4. 未证实项（附理由）

- A-side of the A/B control from raw payloads: no console or wmic capture exists for the empty-directory launch or for pid 22908, and the cited probe_empty_tools.json is absent. The 73-tool game endpoint itself is corroborated (preflight_doctor_live.txt, tools_list_game_mode.json) but its launch arguments are not.
- 'The directory did not exist before this round' is prose only; the raw empty listing is a hand-transcribed capture taken after two contaminated attempts, and it cannot be re-derived. What I could verify independently is that A0 is the known deterministic scaffold (same project.godot sha256 and same runtime id as smoke-t11's A0).
- The pre-flight doctor and netstat outputs are self-authored text captures; they are internally consistent (two expected FAILs, no listener, no godot process before launch) but I cannot re-run them offline.
- The attribution of the coin/win readings to the game endpoint rests on tool-name availability (running_game_* absent from the 154-tool editor list, present in the 73-tool game list; engine source filters by is_editor_hint()) rather than on a live re-capture; the editor is gone now (9877 has no listener) so no live cross-check is possible offline.
- Which call rewrote runs/smoke-t12/game_endpoint.json during the round (two values read: 57989/29776 in the developer trajectory, 53694/25236 in the round author's own read) -- the report itself judges this unattributable and I agree; no role invoked editor_play_scene.
- Whether zero refusals of running_game_* says anything about the refusal path -- it does not, because zero such calls were made (my census: 0 running_game_*, 0 editor_play_scene).
- The 64 KiB truncation path remains untriggered in this round (same as T11).
- The source-level semantics of `artifact_valid=false` still producing an A1 snapshot (the report's C-F) -- only the co-occurrence is observed.
- Redaction fidelity of the three *.redacted.json sidecars: they parse as JSON and the originals are present, but I did not diff their contents or audit what was removed.

## 5. 我没有检查的

- I did not start the engine and did not run any round (offline constraint); no network was used.
- I did not rebuild the binary; freshness is inferred from mtime > HEAD, the sha256 match with the report, and the presence of the DR-78 strings.
- I did not pixel-analyse the 11 PNGs beyond magic bytes and sizes; the gold-pixel and victory-banner claims in evidence.json/qa-visual-checks.txt are the Tester's own derivations.
- I did not audit the source of the readiness wait or of the route-publish path line by line.
- I did not verify the contents of the A0 scaffold beyond hashes and sizes, nor the semantics of every PRD claim id.

## 6. 独立判断（结论）

1. **E3 首次成立是真的，而且证据形态正确。** 金币计数与胜负标志都来自 `running_game_*` 语义工具在**游戏端点**上的回包（编辑器端点确实没有这些工具，引擎源码按 `is_editor_hint()` 过滤），四类行为各有一发引擎断言 `passed=true`。这不是「探针说 OK」也不是拼装 GDScript。
2. **摘要链是真的。** 我用自己写的两种口径复算：A0 是三文件确定性脚手架（与 T11 的 A0 同 sha），A1 是十一文件工程，8 新增 + 1 修改，删除 0，改动全落在工程文件；三棵树逐文件同 sha。
3. **两处修复确实首次真机变绿。** ①的释放早于首批驱动且三批 60/60 唯一 x；②的观测窗口在自己的回包里看到 `0→2`，而不是接手被吃过的计数。
4. **第三处修复的裁定是正确的、且应当保持 undecided。** 我独立得到 `running_game_*`=0、`editor_play_scene`=0：「没看到拒绝」不等于「拒绝不可能」，零拒绝是**在没发出调用**的前提下取得的。因此「角色 live CLI 不再被陈旧路由拒绝」这条**本轮与上轮都未被真机证明**，其就绪等待成本也无法测量。
5. **书里的顺序是必须的**，与本轮的错误启动顺序无关：编辑器必须在 `hoh init` **之后**启动，否则它开不到新工程（本轮 `project_list_scripts=0` 对 mario 15 就是这条的实测证明）。
6. **报告总体诚实**：把修复 ③ 写成「未触发（不是绿也不是红）」、把 `artifact_valid=false` 写出来、把「不能拿运行时侧 1 poll 冒充角色侧读数」写明——这些都经我核对属实。但它有 **3 处实质瑕疵**：夸大了启动证据的存在（T12A-1）、A 侧原始件缺失却称有对照（T12A-2）、把 T10 已有的 wrap-up 重试说成「首次出现」（T12A-4）；另有若干计数口径问题（T12A-5/6/7）。
7. **`F-T12-2` 的性质**：这不是「首次」，而是 **T10 形态的复发**；对本轮不构成判据失败（A1 仍产出、exit 0），但它说明开发者在真实轮里**反复**耗尽尝试预算并以 `artifact_valid=false` 收场，下一批应当调查而非登记了事。

## 7. 给下一批（T13 复现轮）的建议

1. **真的要走到修复 ③**：必须让某个角色真的执行一次 `editor_play_scene` 或 `running_game_*`（`hoh tools call`），否则 F-T12-1 会第三次悬空。同时在报告里给出这次调用与其中一侧的原始回包。
2. **启动证据从第一秒就重定向到文件**，并给 `probe_empty_tools.json` 这类被引用文件建立「报告引用 → 存在性」的自检（一条 5 行的脚本即可）。
3. **所有派生物用显式 UTF-8 写文件**（不要走控制台重定向），把 T12A-3 这一家族一次性关掉。
4. **每个计数写明作用域**（verified-only / verified+gap；bullet 数 / 家族数；`tools call` 次数 / 全部 hoh 调用次数）。
5. **调查两件事**：开发者两次触限 + `artifact_valid=false` 仍快照的语义；以及 planner usage 双计（`result.json.usage` = 2 × attempt）。
6. 复现轮若要比较口径，先声明排序口径（culture vs ordinal），否则基线值会比错。

## 附：机器可读结论

（本块由 `json.dumps(..., ensure_ascii=False, indent=2)` 序列化生成，落盘后由栅栏感知脚本 `json.loads` 回读并核对必需顶层键；回读结果见本文件末尾的验收自证行。）
```json
{
  "task": "TASK-SMOKE-T12-ACCEPTANCE",
  "round_id": "smoke-t12",
  "reviewed_report": ".spec/hof-rs/tasks/TASK-SMOKE-T12-REPORT.md",
  "verified_against_head": "d559961e0dcd42affe1b2b2718e34586cdc35e8b",
  "round_head": "47680397fff0a990c92470c271a5a6e583aa8fc9",
  "verdict": "pass",
  "verdict_scope": "pass for the six criteria and for the two real-machine green fixes, each reproduced here from raw payloads by an independent path; the third fix is correctly reported as unexercised, and one load-bearing environmental claim (A/B control) stays unverified in its A-side raw form. See defects and unverified.",
  "criteria": [
    {
      "id": "FRESH-PROJECT-CLAUSE",
      "pass": true,
      "evidence": "Recomputed independently: versions/3ac25f6c... = 3 files/1727 B and versions/fc50ecd2... = 11 files/7384 B under my own re-implementation of policy.rs::hash_tree (relpath\\n{len}\\n{bytes}\\n, ordinal sort); both ids equal their directory names. A0's project.godot sha256 00d02c9c... is byte-equal to smoke-t11's A0 project.godot (deterministic scaffold), so A0 came from `hoh init`, not hand-writing. A0->A1 added exactly scripts/{coin,goal,main,player}.gd + .uid (8 files) and modified scenes/main.tscn 342->3580 B, removed none; changes lie only on engineering files. runs/smoke-t12 existed as exactly one run: 215 files, oldest mtime 02:49:33 == the single `hoh run` command in round_console.txt, single iter-1, versions index holds only iteration 0 (init) and 1 (developer). meta.json start_state = {mode:fresh}, exit_code 0; exit_code and process_exit_code are the bytes 30 0A."
    },
    {
      "id": "AB-CONTROL-ENVIRONMENTAL-CLAIM",
      "pass": false,
      "evidence": "B-side is solid: editor_bootstrap.txt (raw wmic: pid 33556, cmdline -e --path .workspace\\fresh-t12 --mcp-port=9877, CreationDate 20261002024833), meta.json engine.listener pid 33556 matches_binary=true, doctor_live_final.txt '154 tools', tools_list_editor_live.json = 154 tools, scope_tree_editor.json shows res://project.godot + scenes/main.tscn + scripts/README.md. A-side is prose only: the cited probe_empty_tools.json does not exist anywhere (`find . -name 'probe_empty_tools*'` -> empty), no raw console capture of the game-role boot exists (`grep -rn '\\[MCP\\]' runs/smoke-t12/` hits only report copies and one developer tool output), and tools_list_game_mode.json (73 tools) carries no metadata tying it to the empty-dir/9881 probe. Supported instead by preflight_doctor_live.txt ('73 tools available at 9877') plus the engine source filter I read: tool_registry.cpp scope_matches/build_tools_list(p_is_editor) and mcp_server.cpp is_editor = Engine::is_editor_hint(). Contract check I ran myself: tools_list.renamed.json = 177 = 104 editor + 48 project + 23 running + 2 os; editor endpoint 154 (no running_*), game endpoint 73 (no editor_*, i.e. editor_play_scene absent). The ordering in the book is nonetheless genuinely required: the editor must be pointed at the new project, and a Godot editor cannot open a directory with no project.godot, so `hoh init` must precede the editor launch."
    },
    {
      "id": "E1",
      "pass": true,
      "evidence": "Same chain as FRESH-PROJECT-CLAUSE. plan.md 3299 B; attempts[planner] artifact_valid=true/attempt=1/45 calls; attempts[tester] Submitted/artifact_valid=true/135 calls; result.json ok=true, failed_role=null, issues=[]; evidence_diff == my own diff (8 added, scenes/main.tscn modified, 0 removed). Wrinkle I confirm from result.json: both developer attempts ended LimitsExceeded with artifact_valid=false (150 and 25 calls), wrap_up_retry_used=true/artifact_missing; A1 is a disk snapshot. E1's literal requirement (Developer produces a Godot project increment) holds; the flag is disclosed by the report."
    },
    {
      "id": "E2",
      "pass": true,
      "evidence": "Raw editor_errors_baseline.json: {\"count\":0,\"errors\":[],\"editor\":true,\"pid\":33556}. play_scene_ready.json: editor_play_scene -> playing=true, endpoint http://127.0.0.1:53595/mcp, pid 27736, then running_game_get_scene_tree -> 22 typed nodes (battery observation). editor_stop_scene -> stopped=true. artifact_gate {applicable:true,launchable:true,reasons:[]} in both meta.json and result.json. battery 12/12 ok."
    },
    {
      "id": "E3",
      "pass": true,
      "evidence": "All four classes reproduced from raw payload content in runs/smoke-t12/iter-1/candidate/.hoh/deterministic/raw/: interaction_evidence call[4] release_stale_move_left (before first driven batch call[6]); batches call[9]/[15]/[21] each 60 samples with 60/60 unique x, +216.333 per batch, 67.33->738.33; input_replay call[7] move_right 881.334777832031->1097.66809082031 (+216.333312988, 60/60), call[43] move_left 1149.00085449219->932.668395996094 (-216.332458496, 60/60), call[31] jump x unique=1 (1156.33410644531), y unique=30, 269.980834960938->min 214.258605957031->last 242.59196472168; call[26] running_game_assert_node_state text:neq 'Coins: 0' actual 'Coins: 2' passed=true; call[27] reached:neq false actual true passed=true; four position assertions passed=true. Counter readings are semantic tool replies on the game endpoint: call[0] running_game_get_node_properties Coins:0, call[24] Coins:2, calls 1/10/16 Goal.reached=false, calls 22/25 =true. The endpoint attribution is structural and I checked it: running_game_* exist only in the game role's tool list (0 of 154 on the editor endpoint), and engine source filters tools by is_editor_hint(). Counter is 0->2, not 0->1 (both coins), which the report states."
    },
    {
      "id": "E4",
      "pass": true,
      "evidence": "My own walk of iter-1/evidence.json: verified_records=12 [N1,N2,N3,P3,F1,F2,F3,F4,F5,F10,F13,F16], gap_records=10 [F1-stop,F6,F7,F8,F9,F11,F12,F14,F15,F17], overlap empty, no duplicate ids; every record path exists in the frozen candidate; every record type counted {build 3, runtime_trace 5, assert 6, replay 11, log 3, screenshot 6}; every record candidate_id = fc50ecd2...; every gap carries player_impact and recommended_update; planner_handoff 5/5/6; zero records reference smoke-t9/10/11. Note scope: 34 records over verified+gap, 33 over verified only (the number the report prints without saying so)."
    },
    {
      "id": "E5",
      "pass": true,
      "evidence": "File-level comparison I ran myself (excluding .hoh/.git/.godot/.import): versions/fc50ecd2, iter-1/candidate and live .workspace/fresh-t12 each contain the same 11 files, all sha256-equal, no only-in/differing entries, 7384 B each."
    },
    {
      "id": "E6",
      "pass": true,
      "evidence": "qa_report.md line 4 is literally 'Verdict: partial'; its Verified list is exactly the 12 verified ids and its Gaps list is exactly the 10 gap ids; it calls its own GAME_INPUT_CHANNEL_OK axis probe 'not usable as evidence'; input_channel_probe.json itself shows injection accepted=true but axis moved=false. No unmet item is reported as verified."
    },
    {
      "id": "FIX1-STALE-ACTION-RELEASE",
      "pass": true,
      "evidence": "interaction_evidence call[4] = running_game_play_input_recording label 'interaction:release_stale_move_left' {event_count:1,injected:1,replayed:true}; call[6] = first driven batch 'interaction:batch1:play_input_recording'. Batches then advance 60/60 unique x each. STALE_ACTION_NOT_RELEASED occurs 0 times in the four unredacted trajectories and not in any battery observation line. T11's frozen-x failure shape does not reproduce."
    },
    {
      "id": "FIX2-OBSERVE-BEFORE-CONSUME",
      "pass": true,
      "evidence": "battery.json step order index 6 interaction_evidence < 7 input_channel_probe < 8 input_replay (consuming windows). The observing window's own readings, inside its raw payload, are call[0] Coins: 0 (before) and call[24] Coins: 2 (after); its verdict line carries COIN_PICKED_UP and WIN_DRIVEN. No earlier window in the battery drives movement."
    },
    {
      "id": "FIX3-ROLE-ROUTE-REPUBLISH",
      "pass": false,
      "evidence": "NOT a green: UNEXERCISED, so this item cannot be scored as passing. My independent census over the same four unredacted trajectories (git-ignored runs/** read-only) finds 39 `tools call` invocations, all editor_*/project_*; running_game_* = 0 and editor_play_scene = 0 (detector negative-controlled against synthetic commands). So the republish path, its readiness wait and DR-43's refusal semantics were never walked, and zero `game_endpoint_unavailable` is not evidence because zero such calls were made. The criterion it would support must stay undecided. Route file fact: developer trajectory msg 112/116 read the route JSON with endpoint http://127.0.0.1:57989/mcp, port 57989, pid 29776; meta.json.engine.mcp.game_endpoint is 53595/27736 with checked_at == started_at == 1790880575, i.e. a round-start snapshot, not the live route; game_endpoint.json is absent at close."
    },
    {
      "id": "GUARDS-BASELINES",
      "pass": true,
      "evidence": "My own PowerShell implementation (written for this acceptance, culture-order Sort-Object, repo-root-relative lowercase POSIX path + TAB + bytes + TAB + sha256, LF, no trailing newline) reproduces the task book's anchor runs/smoke-t6 = 135 files / c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03 / newest 2026-09-29 02:32:01 exactly. Run over the eight read-only trees now: all eight digests, counts and newest mtimes are byte-identical to baseline_before.txt and baseline_after.txt (and baseline_final.txt == baseline_after.txt). Ordering matters: for the same file set the ordinal-sort scheme yields c347bd63... for smoke-t8 and f622f5b0... for mario, versus the culture-order 6d11b2c6.../dee0a36f..., so the caliber must be stated. Plant: adding one file to a temp copy changed count 135->136 and the digest, so the scheme is sensitive."
    },
    {
      "id": "FROZEN-AND-HYGIENE",
      "pass": true,
      "evidence": "PRD-mario.md sha256 = 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a (unchanged). DECISIONS.md sha256 = eb7090086c454966445518978606f35cf6ee3e1cba61c2d4601a86c5f548a7c2 (equal to the round's closing_state.txt). Nested engine godot-mcp/godot HEAD = fc63af77c33368c4a1bb839c95d19750554f63a3, porcelain 0 lines. No Cargo.toml/Cargo.lock change in the DR-78 commit or from 4768039 to now => no new dependencies. target/release/hoh.exe: 12713984 B, mtime 2026-10-02 02:45 (after HEAD 4768039 at 02:40:57), sha256 310075fae...7158ca == the report's value, and `strings` contains STALE_ACTION_NOT_RELEASED (1) and the exact phrase 'the game the role started with `editor_play_scene` did not answer' (1). Engine binary unchanged: 194216960 B, mtime 1790641862, sha256 08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a. The round's own commit d559961 touches only the report file. Scratch staging lived at .workspace/.t12-scratch (git-ignored, outside all eight baselines, removed after closing_state.txt recorded it), so it could not disturb any baseline; the two contaminated empty-listings were self-disclosed and --fresh-workspace purged the project directory before the round."
    },
    {
      "id": "MACHINE-BLOCK",
      "pass": true,
      "evidence": "Fence-aware scan of the report finds 26 fences, exactly 1 with info string json; json.loads parses it; it is byte-identical to evidence/analysis/machine_block.json; top keys include verdicts, criteria, unjudgeable, fixes; verdicts = E1..E6 all met; unjudgeable = []. json_block_check.txt agrees (FENCE_AWARE_JSON_BLOCKS_FOUND = 1, RESULT = PASS)."
    },
    {
      "id": "MECHANISM-READINGS",
      "pass": true,
      "evidence": "Zero-increment tokens absent from warnings.log (4 lines: qa_scope + 3 redaction bypasses). wrap_up_retry_used=true/reason=artifact_missing, repair_retry_used=false, no launch_gate_repair, no quarantine. 64 KiB: hoh_output_truncated = 0 in all four trajectories; largest tool-role message = 50026 B (tester, measured by me); every 'truncated' occurrence is an MCP field `\"truncated\":false` (developer 4 / tester 8, matching the report). Stale logs: editor_errors_baseline count=0. Endpoint reachability role-side: undecidable (0 game-endpoint calls). Exit codes agree four ways: exit_code bytes 30 0A, process_exit_code 30 0A, meta.json 0, wrapper ROUND_EXIT=0. Battery play_scene_ready readiness = 1 poll; role-side wait not measurable. All battery raw payloads have request_id == response_id and mismatched_ids == [], so the payload chain is internally consistent."
    },
    {
      "id": "DEV-ATTEMPT-LIMIT-MECHANISM",
      "pass": false,
      "evidence": "The flags themselves reproduce (both developer attempts LimitsExceeded/artifact_valid=false, 150 + 25 calls, wrap_up_retry_used=true reason artifact_missing), but the report's F-T12-2 wording 'wrap_up_retry_used=true 本轮首次出现' is false: smoke-t10 has the identical pattern with the identical reason artifact_missing and the same 150+25 calls. So this is a recurrence of the T10 developer-budget failure, not a first appearance. It is not a round-level regression of the product (the round still produced A1 and exit 0) but it is a mechanism worth triaging."
    }
  ],
  "defects": [
    {
      "id": "T12A-1",
      "severity": "major",
      "what": "The report claims raw engine-launch evidence it does not have. TASK-SMOKE-T12-REPORT.md section 11.2 says '两个进程、两次启动的原始控制台输出都在证据里' and section 1.2 quotes [MCP] role=game / [MCP] role=editor boot lines, but no such capture exists: evidence/round/ contains no console file for either launch, and the only occurrences of 'role=game'/'role=editor' or those [MCP] boot lines in runs/smoke-t12 are inside the report and its own report_part*.md copies. Section 1.2's A/B control also cites probe_empty_tools.json, which does not exist anywhere in the repository.",
      "reproduction": "grep -rn '\\[MCP\\]' runs/smoke-t12/ (hits: report copies + one developer tool output only); grep -rn 'role=game\\|role=editor' runs/smoke-t12/ (report copies only); find . -name 'probe_empty_tools*' (empty); ls runs/smoke-t12/evidence/round/ (no console capture)."
    },
    {
      "id": "T12A-2",
      "severity": "major",
      "what": "The load-bearing environmental claim (A/B control: empty --path -> game role with 73 tools; project.godot present -> editor role with 154 tools) is only half evidenced. The A-side raw artifacts have no provenance: tools_list_game_mode.json is a bare JSON-RPC tools/list reply with no port, path, pid or timestamp, and there is no wmic/console capture for pid 22908 or for the 9881 probe. The B-side is strongly evidenced. So the claim's mechanism is unverified from raw payloads, even though the book's ordering (empty dir -> hoh init -> editor launch) is genuinely required and the engine-side filter that produces the 73/154 split is confirmed in source and in the frozen contract.",
      "reproduction": "head -c 400 runs/smoke-t12/evidence/round/tools_list_game_mode.json (no metadata); grep -rn '9881' runs/smoke-t12/evidence/ (only report prose); no file in evidence/round/ records the first launch's cmdline or pid 22908."
    },
    {
      "id": "T12A-3",
      "severity": "medium",
      "what": "Three derived analysis artifacts the report cites are not valid UTF-8 (GBK console-redirect output), which is the T11A-3 family recurring: evidence/analysis/e3_extract.txt, mechanisms2.txt and route_trace.txt each raise UnicodeDecodeError under UTF-8. The report's section 9(d) self-certification covers only the JSON block, not these files.",
      "reproduction": "python utf8scan.py runs/smoke-t12 -> the three .txt files fail with 'invalid start byte' 0xa1/0xa2 and an invalid continuation byte 0xce (plus the expected PNG binaries)."
    },
    {
      "id": "T12A-4",
      "severity": "medium",
      "what": "F-T12-2's 'wrap_up_retry_used=true 本轮首次出现' is factually wrong; smoke-t10 already used the wrap-up retry with reason artifact_missing and the same developer pattern. The report's own text elsewhere compares only to T11, so the statement overstates novelty.",
      "reproduction": "python mech_cmp.py: smoke-t10 wrap_up_retry_used=True reason=artifact_missing, developer attempts 1/2 LimitsExceeded artifact_valid=False, calls 150/25 -- identical to smoke-t12; smoke-t11 was clean (repeated-format error, artifact_valid=true)."
    },
    {
      "id": "T12A-5",
      "severity": "medium",
      "what": "The round total 17,703,610 tokens (report header and machine block) is taken from result.json.usage, which double-counts the planner: usage[planner] = 90 calls / 901,668 tokens while the single planner attempt is 45 calls / 450,834 tokens, exactly half. The sum of attempts is 17,252,776, and the planner trajectory itself contains only 40 assistant messages summing 373,275 tokens. T10 and T11 show no such doubling (planner aggregate == attempt), so this is a new anomaly the report neither flags nor investigates.",
      "reproduction": "python usage_cmp2.py and python traj_tokens.py: T12 usage planner (90, 901668) vs attempts (45, 450834); T10 (21,139523) vs (21,139523); T11 (28,199008) vs (28,199008); planner trajectory 40 assistant messages, sum 373,275."
    },
    {
      "id": "T12A-6",
      "severity": "minor",
      "what": "Count scopes are unstated or inconsistent, contradicting the book's report discipline (a) and (d): section 2.4 prints execution_records=33 without saying it counts records attached to verified claims only (verified+gap = 34); section 2.6 says qa_report enumerates '8 组' gaps although the report has 6 gap bullets covering 10 gap families; section 0.1 says the developer made '38 次 hoh tools call' while its own section 3.3 enumeration sums to 39 and my recount is 39.",
      "reproduction": "python e4_check.py (33 verified-only records, 34 total); read iter-1/qa_report.md Gaps section (6 bullets, ids F1-stop,F6,F7,F8,F9,F11,F12,F14,F15,F17); python tool_census.py (39 `tools call`, breakdown identical to the report's list)."
    },
    {
      "id": "T12A-7",
      "severity": "minor",
      "what": "Section 7's '最大单条消息 = 50,026 B' is a tool-output measurement only; the largest serialized message record in the round is 112,115 B (tester attempt1), and the largest assistant record is 36,373 B. The 64 KiB cap applies to tool output, so the substantive claim (cap never triggered) stands, but the wording invites a wrong reading.",
      "reproduction": "python max_msg.py (max role=tool content 50026 for tester; max serialized message 112115); python mech_checks.py."
    },
    {
      "id": "T12A-8",
      "severity": "minor",
      "what": "evidence/round/scope_project_tree.json is a stale, contaminated capture -- it lists only res://.t12pre, with no project.godot/scenes/scripts -- and it is retained in the evidence set with no superseded label. It is not the file the report relies on (scope_tree_editor.json is), but a reader could take it as the editor-scope proof.",
      "reproduction": "cat runs/smoke-t12/evidence/round/scope_project_tree.json (single child .t12pre); compare with scope_tree_editor.json (project.godot, scenes/main.tscn, scripts/README.md)."
    },
    {
      "id": "T12A-9",
      "severity": "info",
      "what": "Section 1.3 says the doctor's godot.project_file / editor_scope checks point verbatim at fresh-t12; that is true of the inline doctor in the run's own output (round_console.txt) but not of the standalone live doctor (doctor_live_final.txt points at .workspace/mario, which is the configured project). The report discloses this nuance elsewhere, but the sentence overgeneralizes.",
      "reproduction": "doctor_live_final.txt lines 6-9 vs round_console.txt lines 11-14."
    }
  ],
  "risks": [
    "Fix 3 (role-side route republish) has now gone unexercised for two consecutive real rounds; the behaviour it guards (a role's own running_game_* call not being refused by a stale route) remains undecided and unmeasured, including its readiness-wait cost.",
    "The developer again ended both attempts LimitsExceeded with artifact_valid=false and needed the wrap-up retry, exactly as in smoke-t10; the runtime still snapshotted the on-disk tree as A1. Whether that branch should count as a failure is unaudited (the report says so itself).",
    "The A/B environmental claim's A-side has no raw boot capture, so if the next round relies on the same reasoning it inherits an unverified premise; it also still has a dangling citation (probe_empty_tools.json).",
    "The planner's role-level token aggregate is double the attempt's in this round; any downstream cost/ablation comparison built on result.json.usage is inflated for this round.",
    "Clock/timezone: my reproduction of the log window used local time; the round's own windows (02:49:33 -> 03:25:17) are self-consistent with file mtimes (oldest 02:49:33).",
    "The rendered analysis files that are GBK-encoded can silently break automated readers that assume UTF-8."
  ],
  "unverified": [
    "A-side of the A/B control from raw payloads: no console or wmic capture exists for the empty-directory launch or for pid 22908, and the cited probe_empty_tools.json is absent. The 73-tool game endpoint itself is corroborated (preflight_doctor_live.txt, tools_list_game_mode.json) but its launch arguments are not.",
    "'The directory did not exist before this round' is prose only; the raw empty listing is a hand-transcribed capture taken after two contaminated attempts, and it cannot be re-derived. What I could verify independently is that A0 is the known deterministic scaffold (same project.godot sha256 and same runtime id as smoke-t11's A0).",
    "The pre-flight doctor and netstat outputs are self-authored text captures; they are internally consistent (two expected FAILs, no listener, no godot process before launch) but I cannot re-run them offline.",
    "The attribution of the coin/win readings to the game endpoint rests on tool-name availability (running_game_* absent from the 154-tool editor list, present in the 73-tool game list; engine source filters by is_editor_hint()) rather than on a live re-capture; the editor is gone now (9877 has no listener) so no live cross-check is possible offline.",
    "Which call rewrote runs/smoke-t12/game_endpoint.json during the round (two values read: 57989/29776 in the developer trajectory, 53694/25236 in the round author's own read) -- the report itself judges this unattributable and I agree; no role invoked editor_play_scene.",
    "Whether zero refusals of running_game_* says anything about the refusal path -- it does not, because zero such calls were made (my census: 0 running_game_*, 0 editor_play_scene).",
    "The 64 KiB truncation path remains untriggered in this round (same as T11).",
    "The source-level semantics of `artifact_valid=false` still producing an A1 snapshot (the report's C-F) -- only the co-occurrence is observed.",
    "Redaction fidelity of the three *.redacted.json sidecars: they parse as JSON and the originals are present, but I did not diff their contents or audit what was removed."
  ],
  "not_checked": [
    "I did not start the engine and did not run any round (offline constraint); no network was used.",
    "I did not rebuild the binary; freshness is inferred from mtime > HEAD, the sha256 match with the report, and the presence of the DR-78 strings.",
    "I did not pixel-analyse the 11 PNGs beyond magic bytes and sizes; the gold-pixel and victory-banner claims in evidence.json/qa-visual-checks.txt are the Tester's own derivations.",
    "I did not audit the source of the readiness wait or of the route-publish path line by line.",
    "I did not verify the contents of the A0 scaffold beyond hashes and sizes, nor the semantics of every PRD claim id."
  ],
  "plants_and_counterexamples": [
    "Digest scheme self-validation: my own PowerShell digest reproduces the task book's anchor runs/smoke-t6 = 135 files / c144ef32...7a9c03 exactly; sensitivity plant on a temp copy changed count and digest when one file was added.",
    "Ordering counterexample: the same smoke-t8 file set hashes to c347bd63... under ordinal sort and 6d11b2c6... under culture order; mario f622f5b0... vs dee0a36f....",
    "Tool-name detector negative control: my regex flags a synthetic `tools call running_game_get_scene_tree` and `tools call editor_play_scene` and does not flag a mere string mention of running_game_ inside an analysis command, so the observed 0 is a real negative rather than a broken detector.",
    "Digest-chain plant: my hash_tree re-implementation reproduces both version ids and the three-tree equality bit-for-bit, so A0->A1 is a three-file scaffold becoming an eleven-file project with the changes on engineering files.",
    "Endpoint-attribution counterexample: the editor role serves 154 tools with 0 running_game_*, so a running_game_* reply could not have come from the editor endpoint.",
    "Borrowed-evidence counterexample: no execution record and no string in iter-1/evidence.json references smoke-t9/t10/t11."
  ]
}
```

<!-- 验收自证（由生成脚本在回读成功后追加） -->
SELF-CHECK: fences=299 json_fences=1 json.loads=PASS round_trip_equal=True verdict=pass criteria=16 defects=9 risks=6 unverified=9
