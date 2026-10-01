# TASK-DR78-REPORT — 隔离 spike 判定 F-T11-2 真因；② 角色自起 `play_scene` 重发布路由；③ 消除"金币已被吃掉"的结构性假阴性；④ 并入 D77-A/D77-B

> 实现者：**实现子代理**（无上游对话上下文；本文件是唯一任务来源 `.spec/hof-rs/tasks/TASK-DR78.md`）。
> 落点：`F:\moonbit-hof-rs`。**离线批次**：**未启动引擎、未跑真机轮、未调用任何模型端点、未联网、未 push、未 stage**。
> **`runs/**` 零写入**（含"写过再删"；全部只读，见 §6.2）；**`.workspace/mario/**` 与 `.workspace/fresh-t11/**` 零字节写入**（§6.3 摘要 + 逐字节对照自证）。
> **未改** `PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`；**未加依赖**；**未对任何路径用 `rm -rf`**；**未从未展开的变量构造路径**；
> **未用 PowerShell 的 `Get-Content -Raw`+`Set-Content` 改写任何源码**；**未整文件重写行尾**（被编辑的每个文件保留其原有行尾，§6.6）。
> 工作提交：`bf943d0`（实现+测试+spike 工件）。门读数为 `bf943d0` 工作树、**清 60 条指纹 + 逐文件 touch 96 个 `git ls-files '*.rs'`** 后取得。

---

## 0. 机器可读结论块

```json
{
  "task": "TASK-DR78",
  "verdict": "pass",
  "head": "bf943d0d4d04676fe6dbce4ea4bf71fdccb11775",
  "implementation_commit": "bf943d0",
  "base_head": "1bed9b11ccb3bbd2eb713ddf47d6c0dbf05eeeab",
  "deliverables": {
    "report": ".spec/hof-rs/tasks/TASK-DR78-REPORT.md",
    "spike": ".spec/hof-rs/tasks/TASK-DR78-spike/spike.py",
    "spike_readings": ".spec/hof-rs/tasks/TASK-DR78-spike/spike_output.txt",
    "plants": ".spec/hof-rs/tasks/TASK-DR78-spike/plants/",
    "gate": ".spec/hof-rs/tasks/TASK-DR78-spike/gate/"
  },
  "criteria": [
    {
      "id": "1-spike-decides-the-cause-before-any-drive-change",
      "pass": true,
      "evidence": "TASK-DR78-spike/spike_output.txt: the interaction window's batch1 has unique_x=1 at x=225.000045776367 for 60 frames while the three play_input_recording replies say injected=1/replayed=true; the window's own pre-sample span advanced the player at full speed for 14.666687011719 px = 4.000015 frames leftward (239.666732788086 -> 225.000045776367 at 3.666657787 px/frame); step 9 reads Player facing=-1, velocity={x:0.0,y:0.0}, position x=225.000045776367; and the only move_left pressed=false in the whole round carries target=editor. Verdict: (b) delivered but cancelled by a stale held opposite action; (a), (c), (d) each excluded with a raw reading (counterexample checks C1-C5)."
    },
    {
      "id": "1-counterexample-check-distinguishes-did-not-move-from-could-not-move",
      "pass": true,
      "evidence": "C1: the same round's input_channel_probe made 0 editor_simulate_input_action calls and still moved the player 67.3333358764648 -> 173.666687011719, so the round report's discriminator is refuted. C2: the replay move_right series 192.000045776367 -> 408.333038330078 passes straight through 225 and through Coin1 at 400. C3: facing=-1 with velocity.x=0.0 cannot be produced by a driven-but-blocked player (player.gd sets facing=1 and velocity.x=220 for direction>0). C4: identical node_path and sample shape. C5: the 4-frame leftward advance proves the game was stepping."
    },
    {
      "id": "2-role-started-play_scene-republishes-the-game-route",
      "pass": true,
      "evidence": "ProjectAdapter::publish_role_started_game_route (src/adapter/mod.rs, implemented in src/adapter/godot.rs) is called by hoh tools call editor_play_scene (src/cli_impl.rs) after the call and before the reply is printed; order = install_game_endpoint, readiness poll with scene_tree_readiness, publish_game_endpoint. Test a_role_started_scene_republishes_the_game_route_for_later_processes (exit 0) proves the route file is rewritten to the new endpoint/pid and that a later process reaches that game. Plant P3 disables the branch and the same test exits 101 at tests/game_route_across_processes.rs:368."
    },
    {
      "id": "2-dr43-refusal-preserved-never-falls-back-to-the-editor",
      "pass": true,
      "evidence": "Every failure path calls clear_game_endpoint (withdraws the file) and returns an error (exit 4). Test a_role_started_scene_that_never_becomes_ready_is_refused_and_leaves_no_route: exit != 0, the previously published live game is never probed (previous.tools() empty), the route file is gone, the next running_game_get_scene_tree gets game_endpoint_unavailable, and the editor endpoint receives no running_game_* call. Test a_role_started_scene_whose_route_cannot_be_published_fails_loudly: exit != 0 with 'could not be published' and 'DR-43' in the message, and the editor reply is not printed as a success. The four pre-existing DR-43 refusal tests remain green."
    },
    {
      "id": "3-observing-window-runs-before-every-consuming-window",
      "pass": true,
      "evidence": "src/adapter/godot.rs run() now calls step_interaction_evidence before step_input_channel_probe and step_input_replay; COIN_OBSERVING_BATTERY_STEP and COIN_CONSUMING_BATTERY_STEPS encode the rule as data and the_coin_observing_window_runs_before_every_consuming_window reads the order of the records the battery really produced. Plant P1 restores HEAD~1's three lines verbatim (script-verified: planted text equals HEAD~1's own text) and that test exits 101 at tests/evidence_battery.rs:4733."
    },
    {
      "id": "3-observing-window-is-self-sufficient",
      "pass": true,
      "evidence": "The window releases INTERACTION_STALE_ACTIONS (move_left) inside the game process before its first batch, and reports STALE_ACTION_NOT_RELEASED instead of swallowing a refusal. The fixture now gates its interaction ramp on the game's own Input.get_axis result, so a delivered move_right alone no longer means movement. the_observing_window_clears_a_stale_opposing_action_by_itself starts with move_left held (the smoke-t11 state) and asserts the release precedes the first injected batch; plant P2 removes the release and it exits 101 at :4770."
    },
    {
      "id": "4-D77A-the-superseded-token-is-really-the-old-name",
      "pass": true,
      "evidence": "SUPERSEDED_GEOMETRIC_TOKEN is 'WIN_UNREACHABLE_GEOMETRICALLY' again; the_superseded_token_is_the_old_name_and_not_a_copy_of_the_new_one asserts it and asserts it differs from the new token. The two vacuity sources were fixed as well: the delivered skill is CRLF so the paragraph loop is now normalised (was: no paragraph boundary at all), and the ledger lookup now requires a paragraph carrying both names (was: the first paragraph naming the old one, which is the DR-76 correction note). Plant P4 (the DR-77 state, verbatim from HEAD~1) exits 101 at tests/interaction_contract.rs:55; plant P6 (a skill paragraph naming only the old token) exits 101 at :317."
    },
    {
      "id": "4-D77B-geometric-is-gone-from-the-evidence-surfaces",
      "pass": true,
      "evidence": "The battery's test name is a_player_that_stops_advancing_with_budget_left_is_blocked_under_move_right and the assertion messages/comments at tests/evidence_battery.rs:337/:453/:4428 plus src/adapter/godot.rs:2857/:3886 use the movement-direction wording; the old token itself is preserved in the ledger mapping and the skill's mapping sentence. the_battery_names_the_blocked_verdict_by_its_movement_direction pins both directions and plant P5 (the DR-77 name, verbatim from HEAD~1) exits 101 at tests/evidence_battery.rs:4834."
    },
    {
      "id": "gate",
      "pass": true,
      "evidence": "After clearing 60 hof-rs-* fingerprints (354 non-hof-rs left) and touching all 96 tracked .rs files one at a time: cargo test --offline exit 0, first line 'Compiling hof-rs v0.1.0 (F:\\moonbit-hof-rs)', 59 'test result:' lines summing to 546 passed / 0 failed / 7 ignored, FAILED=0, error=0, panicked=0, warning=0; cargo test --offline -- --list = 553 = 546 + 7; cargo fmt --check exit 0; fn declarations 1627 -> 1646 with ADDED 20 / REMOVED 1 (the mandated D77-B rename); #[ignore] 9 -> 9."
    },
    {
      "id": "non-vacuity-six-plants",
      "pass": true,
      "evidence": "TASK-DR78-spike/plants_transcript.txt: P1 exit 101, P2 exit 101, P3 exit 101, P4 exit 101, P5 exit 101, P6 exit 101; each with bytes_identical=True, hash_object==HEAD=True, status_clean=True, diff_clean=True. P1/P4/P5 additionally verify 'the planted text equals HEAD~1's own text: True', i.e. the red is the pre-DR78 state reconstructed verbatim rather than an invented mutation."
    },
    {
      "id": "forbidden-zones",
      "pass": true,
      "evidence": "Six read-only baselines recomputed with a rewritten culture-order digest and byte-identical: mario 178 dee0a36f…6cc94, t6 135 c144ef32…7a9c03 (the self-certifying value), t7 115 6e4c1595…520fb7, t8 358 6d11b2c6…bdf5a7, t9 83 541e2d81…36ca9d, t10 232 31955589…b38b8b; runs newer than 2026-10-02 01:00 = 0; .workspace/fresh-t11 = 11 files/8830 B byte-identical to the frozen A_1 snapshot (only-in-live [], only-in-snapshot [], differing []); sha256(PRD-mario.md) unchanged at 4c81c3a9…; git diff HEAD~1..HEAD -- DECISIONS.md = 0 lines; nested engine HEAD fc63af77… with porcelain 0; no Cargo.toml/Cargo.lock change; origin/master behind by 13 and nothing pushed; no rm -rf and no path built from an unexpanded variable."
    }
  ],
  "spike": {
    "cause": "b-applied-then-cancelled",
    "supported_by": [
      "input_replay call 39 presses move_left in the game process and nothing on the game channel releases it afterwards (the only later move_left pressed=false is target=editor)",
      "the interaction window advanced the player 14.666687011719 px = 4.000015 frames of full-speed leftward travel inside its own call span",
      "step 9 Player facing=-1 and velocity={x:0.0,y:0.0}, which player.gd can only produce with direction==0.0",
      "player.gd moves by Input.get_axis(\"move_left\", \"move_right\"); both held => 0",
      "godot.rs:2194-2202 drains held_in_game at the START of each window, so the loop's last window is never released"
    ],
    "excluded": {
      "a-no-input-at-all": "the three batch injections answered injected=1/replayed=true, and with move_left still held a window that injected nothing would keep travelling left instead of stopping at the first sample",
      "c-timing-or-physics": "60 samples per batch with frame indices 0..59 and a measured 4.000015-frame full-speed advance inside the window",
      "d-wrong-sample-target": "both windows sample node_path /root/Main/Player with frame_count=60, frame_interval=1"
    },
    "still_unknown": [
      "the exact frame at which move_right took effect (resolvable only within the window's first 8 calls)",
      "no real-machine replication was performed (this was an offline batch)"
    ],
    "counterexample_checks": [
      "C1 same-round capability control: input_channel_probe, 0 editor_simulate_input_action calls, 67.3333358764648 -> 173.666687011719",
      "C2 geometry control: the replay move_right series passes through x=225 and x=400",
      "C3 the game's own reading: facing=-1 with velocity.x=0.0 excludes 'blocked while driven'",
      "C4 the sampled object is identical in both windows",
      "C5 the game was stepping: 4.000015 frames of full-speed travel inside the window"
    ]
  },
  "gate": {
    "cargo_test_offline_exit": 0,
    "passed": 546,
    "failed": 0,
    "ignored": 7,
    "test_result_lines": 59,
    "list_count": 553,
    "fmt_check_exit": 0,
    "fingerprints_cleared": 60,
    "fingerprints_left_alone": 354,
    "tracked_rs_touched": 96,
    "rebuild_proved_by": "Compiling hof-rs v0.1.0 (F:\\moonbit-hof-rs) as the first line of the gate log",
    "fn_declarations": {
      "base": 1627,
      "head": 1646,
      "added": 20,
      "removed": 1
    },
    "removed_is": "a_player_that_stops_advancing_with_budget_left_is_a_geometric_verdict (renamed by this batch as TASK-DR78 item 4 requires; the same test exists under its new name)",
    "ignore_attributes": {
      "base": 9,
      "head": 9
    }
  },
  "baseline_digests": {
    "caliber": "repo-root-relative lowercase POSIX path + TAB + byte length + TAB + sha256, LF lines, no trailing newline, PowerShell Sort-Object culture order, sha256 of the whole UTF-8 block",
    ".workspace/mario": {
      "files": 178,
      "digest": "dee0a36f357c440d078c652d4d4b8990af1a63b88d282c1e36c04a16d006cc94",
      "newest": "2026-09-30 18:23:08"
    },
    "runs/smoke-t6": {
      "files": 135,
      "digest": "c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03",
      "newest": "2026-09-29 02:32:01"
    },
    "runs/smoke-t7": {
      "files": 115,
      "digest": "6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7",
      "newest": "2026-09-29 14:41:14"
    },
    "runs/smoke-t8": {
      "files": 358,
      "digest": "6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7",
      "newest": "2026-09-30 07:58:28"
    },
    "runs/smoke-t9": {
      "files": 83,
      "digest": "541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d",
      "newest": "2026-09-30 11:27:29"
    },
    "runs/smoke-t10": {
      "files": 232,
      "digest": "319555896964ce1526f72a33cb239bf389fe29bcde23841764d13c57dfb38b8b",
      "newest": "2026-09-30 18:23:08"
    },
    ".workspace/fresh-t11": {
      "files": 100,
      "digest": "4c07c0b6d4352a5a64e1b49908e3ae1325f62f0a3b4de44d17efc51ebffd13a4",
      "newest": "2026-10-02 00:29:23"
    },
    "paths_relative_to": "the repository root (my first implementation used the scanned directory as the base and all six baselines mismatched; with the repo root as the base all six match, which is why the base is stated here)"
  },
  "changed_files": [
    "src/adapter/mod.rs (ProjectAdapter::publish_role_started_game_route)",
    "src/adapter/godot.rs (the implementation; battery order; stale-action release; D77-B comments)",
    "src/cli_impl.rs (the role-side publish trigger before the reply is printed)",
    "src/tools/bridge.rs (ToolCallReply, tools_call_with_reply, GAME_START_TOOL)",
    "tests/evidence_battery.rs (fixture axis model, 3 new tests, D77-B renames, expected order)",
    "tests/game_route_across_processes.rs (3 new tests, canned per-tool replies)",
    "tests/interaction_contract.rs (D77-A: constant, normalised skill loop, both-name ledger lookup, new guard)"
  ],
  "risks": [
    "No real-machine round was run (offline batch): 2/3/4 are proven offline only, against the real hoh binary plus loopback JSON-RPC doubles.",
    "The spike's cause is pinned by frozen readings + the frozen game code + the producing source path, not by an in-vivo causal experiment.",
    "The role-side publish adds a readiness poll (up to tools.ready_timeout_seconds, default 30 s) to a role's editor_play_scene, and turns a game that never confirms readiness into exit 4 instead of an immediate success.",
    "When no route file is configured (HOH_GAME_ROUTE unset, e.g. a manual bench call) the publish is a no-op but the readiness confirmation still runs; no test covers that path.",
    "INTERACTION_STALE_ACTIONS lists move_left only; a project whose jump is hold-to-fly would need jump added.",
    "A refused stale-action release is recorded but does not fail the window; a later batch may want to treat it as untrustworthy drive evidence.",
    "cargo fmt --check and git are both blind to CRLF/LF differences, so line-ending drift inside a file stays invisible; this batch only ever formatted LF files in write mode and preserved every file's existing endings."
  ],
  "unverified": [
    "True red-first logs: P1/P4/P5 reconstruct HEAD~1's text verbatim so the pre-fix red is reproducible, but no contemporaneous log of the first failure was archived.",
    "Real-machine behaviour of the republished route, of the readiness wait, and of the stale-action release acceptance rate.",
    "The exact frame at which the interaction window's move_right took effect.",
    "Whether any existing consumer depends on a role-side editor_play_scene returning without a readiness wait (no test exercises that shape)."
  ],
  "honest_disclosure": [
    "I did not build a fix on the round report's causal explanation; the spike tests it first and refutes it (C1), and the four items were implemented only after the cause was pinned to the stale held move_left.",
    "One test name is removed and replaced (the D77-B rename the task book demands); it is the only entry in the fn-name set difference and no test was deleted to make the gate green.",
    "This batch modified neither DECISIONS.md nor PRD-mario.md; the decision-log entry is the scheduler's to write.",
    "The six baselines first mismatched because my path base was wrong; the mismatch and the corrected caliber are both reported rather than only the matching result.",
    "No push was attempted (the gate is armed and GitHub is unreachable)."
  ]
}
```

（本块由 `json.dumps(..., ensure_ascii=False, indent=2)` 序列化后落盘，落盘后由独立栅栏感知脚本 `json.loads` 回读，见 §8。）

---

## 1. 结论

**四项全部落地，且每一项都有一个能独立复算的红/绿证据。**

1. **①（前置）隔离 spike 给出可复现的真因（不是报告里的那个）**：交互窗口**确实送达了 `move_right`**，
   但它被 **`input_replay` 最后一个窗口遗留、从未在游戏进程内释放的 `move_left`** 抵消——
   `player.gd` 读 `Input.get_axis("move_left", "move_right")`，两个都按住 ⇒ 轴向 `0` ⇒ 玩家站立不动。
   证据面：窗口自身采样前**以满速向左推进了 4.000015 帧**（`239.666732788086 → 225.000045776367`，`14.666687011719 px`），
   紧随其后的第 9 步读到 **`facing=-1`、`velocity={x:0.0,y:0.0}`**（"被几何挡住"的玩家会读成 `facing=+1`、`velocity.x=±220`），
   而整轮在游戏通道上**没有任何一次** `move_left pressed=false`（唯一一处是 `target="editor"` 的编辑器侧释放）。
   ⇒ **（b）"施加了但被别处的遗留状态抵消"成立**；**（a）"没施加"、（c）"时基没推进"、（d）"采样点取错"逐条排除**（§2，含反例检验）。
2. **② 角色自起 `play_scene` 现在会重发布游戏路由**，落点在**适配器层**（`ProjectAdapter::publish_role_started_game_route`），
   与采纳者 `bridge::adopt_published_game_route` 构成明确的发布/采纳边界；顺序与运行时启动同构（install → 确认就绪 → publish）。
   **DR-43 的拒绝语义一条未放宽**：未确认就绪 ⇒ 不发布且显式失败，失败路径撤回路由，**任何路径都不回退到编辑器端点**（§3）。
3. **③ 结构假阴性消除**：`interaction_evidence` 现在运行在 `input_channel_probe`/`input_replay` **之前**（观测早于消耗），
   并且该窗口**自己清掉它不驱动的动作**（自给自足，不依赖别的步骤的状态）。两条回归钉：**把观测窗口挪回消耗窗口之后即红**、
   **去掉自清动作即红**（§4）。
4. **④ D77-A 与 D77-B 清偿**：`SUPERSEDED_GEOMETRIC_TOKEN` 回到真正的旧名，两条"旧名映射"断言**不再恒真**
   （并修掉了它们各自依赖的 CRLF/整文档退化），`geometric` 从证据面的测试名与消息中清除（§5）。

**门**（`bf943d0`；清指纹后真重编）：

| 项 | 读数 | 证据 |
|---|---|---|
| `cargo test --offline` | **exit 0** | `TASK-DR78-spike/gate/test.txt` 末行 `test_exit=0` |
| 套件尾部 | `59` 个 `test result:` 行求和 = **546 passed / 0 failed / 7 ignored** | 同上；`FAILED`=0、`^error`=0、`error[`=0、`panicked`=0、`^warning:`=0。**口径说明**：`grep "warning"` 另有 6 行命中，逐行看过，全部是**测试函数名**（如 `a_healthy_session_records_no_desync_warning`），不是编译警告 |
| 基线算术 | DR-77 的 **539/0/7** + 本批 **7 条新测试** = **546/0/7** | `TASK-DR78-spike/names.txt` 的 ADDED 表 |
| `cargo test --offline -- --list` | **553** 条 = 546 + 7（自洽） | `TASK-DR78-spike/gate/list.txt`（`list_exit=0`） |
| 强重编 | 首行 `Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)`；`Compiling` 命中 1 次 | `gate/test.txt` 头 2 行 |
| 强重编怎么来的 | 清 **60** 条 `hof-rs-*` 指纹（留 354 条非本 crate 的）；再**逐文件** touch **96** 个 tracked `.rs` | `gate/clear_fp.txt`、`gate/touch.txt` |
| `cargo fmt --check` | **exit 0** | `gate/fmt.txt` |
| 测试名 | fn 声明 1627 → 1646；**ADDED 20 / REMOVED 1** | `names.txt` |
| `#[ignore]` | **9 → 9**（未增长） | `names.txt` |
| 门是否被动过 | **无测试被删**，唯一 REMOVED 是任务书 ④ 点名要求改名的那个测试（§5.3） | `names.txt` |

---

## 2. §1.1 spike 结论：交互窗口为何没推进

**命令**（只读、离线、在仓内任何路径下可复跑；脚本已随报告落盘）：

```
$ python .spec/hof-rs/tasks/TASK-DR78-spike/spike.py .spec/hof-rs/tasks/TASK-DR78-spike/spike_output.txt
```

`spike_output.txt` 是脚本**用 Python 以 UTF-8 写盘**的（不用控制台重定向——T11A-3 的教训：派生物必须自己合法），
我另用 `python -c "open(...,'rb').read().decode('utf-8')"` 亲验 `utf8 OK`（§8）。

### 2.1 判定（逐条"支持 / 排除 / 仍未知"）

| 候选 | 判定 | 依据（原始读数见 §2.2 与 `spike_output.txt`） |
|---|---|---|
| (a) 窗口**根本没施加输入** | **排除** | 三批的 `running_game_play_input_recording` 回包都是 `{"event_count":1,"injected":1,"replayed":true,"speed":1.0}`（call 5/11/17）；且"完全没施加"下 `move_left` 仍被按住（见下），玩家会**继续以满速向左**，而读数显示它在窗口开头就停了。 |
| **(b) 施加了但被别处抢先/覆盖** | **支持（真因）** | `input_replay` 最后一个窗口（call 39）在游戏进程内按下 `move_left` 且**之后没有任何游戏通道的释放**；窗口进入时该动作仍然按住，`move_right` 落上去后 `Input.get_axis` 恒为 `0`。三条独立读数支持（§2.2 B/C/F）。 |
| (c) 施加了但**时基/帧推进不对** | **排除** | 窗口自己那 8 次调用期间玩家**以满速前进了整整 4 帧**（`14.666687011719 / 3.666657787 = 4.000015`）——游戏在步进；每批 `frame_count=60` 且帧号 `0..59` 齐全。另外 T11 验收自己的读数（HUD `Time: 3 → 6`）也说明采样期跑了约 180 帧。 |
| (d) 施加了且推进了，但**采样点取错** | **排除** | 两个窗口采的是**同一个**对象（`node_path="/root/Main/Player"`）、同一个工具、同一形状（`frame_count`/`frame_interval` 相同）。 |
| (e) 其它 | **未发现** | 没有第三类候选能在不假设"未知的释放入口"的前提下解释 4 帧满速左移 + `velocity.x=0.0`。 |

**仍未知（必须写明）**：`move_right` 落下去的**确切帧**无法从 1 帧采样的冻结载荷里分辨（只能界定在窗口前 8 次调用之内）；
以及真机复现仍未做（离线批次，§7）。

### 2.2 原始读数

**(A) 整轮在游戏进程内的输入事件（按到达顺序）**

```
-- input_channel_probe.json
   call  3  GAME      move_right pressed=True   label=move_right:play_input_recording
-- input_replay.json
   call  3  GAME      move_right pressed=True
   call 12  GAME      move_right pressed=False  label=move_right_release:reset
   call 15  GAME      move_right pressed=True
   call 24  GAME      move_right pressed=False  label=jump:reset
   call 27  GAME      jump      pressed=True
   call 36  GAME      jump      pressed=False   label=move_left:reset
   call 39  GAME      move_left pressed=True    label=move_left:play_input_recording
   call 47  EDITOR    move_left pressed=False   label=move_left:EDITOR_SIDE_INJECTION:release  (target=editor)
-- interaction_evidence.json
   call  5  GAME      move_right pressed=True   label=interaction:batch1:play_input_recording
   call 11  GAME      move_right pressed=True   label=interaction:batch2:play_input_recording
   call 17  GAME      move_right pressed=True   label=interaction:batch3:play_input_recording
```

⇒ **`input_replay` 的释放在每个窗口的"开头"发生（把上一个窗口的动作还给游戏）**，所以**最后一个窗口的 `move_left` 没有后继替它释放**；
整个轮次里 `move_left` 只有一次 `pressed=false`，而且回包自己的 `"target":"editor"`——**那是编辑器进程，不能驱动游戏**（DR-35/DR-68 ③(a) 的同一条纪律）。

**(B) 交接处的算术**

```
input_channel_probe  move_right frames: n=30 first=(0, 67.3333358764648, …) last=(29, 173.666687011719, …)
    editor_simulate_input_action calls in that file: 0
input_replay  move_left window: first=455.999542236328 last=239.666732788086  per-frame = 3.666657787
input_replay  move_right window: first=192.000045776367 last=408.333038330078
    contains x=225.000045776367 ? True ; contains x=400 (Coin1) ? True
interaction   batch1: n=60 unique_x=1 x=[225.000045776367]
HANDOVER: 239.666732788086 -> 225.000045776367
    gap = 14.666687011719 px = 4.000015 frames of full-speed leftward travel
```

**(C) 游戏自己怎么说（第 9 步、交互窗口之后的一次 `running_game_get_node_properties Player`）**

```
    facing     = -1
    velocity   = {'x': 0.0, 'y': 0.0}
    position   = {'x': 225.000045776367, 'y': 303.925262451172}
```

冻结候选的 `scripts/player.gd`：

```
    var direction := Input.get_axis("move_left", "move_right")
    velocity.x = direction * speed
    facing = 1 if direction > 0.0 else -1
    else: velocity.x = move_toward(velocity.x, 0.0, speed)
```

**这三行合起来是一条判据，不是推测**：`velocity.x` 被 `move_toward` 归零只在 `direction == 0.0` 时发生；
被墙挡住的角色 `direction` 仍是 `±1`、`velocity.x` 仍是 `±220`、`facing` 会被写成 `+1`。读到 `velocity.x=0.0` 且 `facing=-1`，
即"轴向为 0 且最后一次非零方向是左"。

**(F) 泄漏点在产生这些载荷的源码里**

```
    godot.rs:2194           for previous in held_in_game.drain(..) {          <- 释放在每个窗口的**开头**
    godot.rs:2196               .semantic_release_action(previous, &format!("{label}:reset"), …)
```

`held_in_game` 在循环**开头**被 drain，循环体最后一个窗口（`move_left`）结束后没有任何释放 ⇒ 循环退出时 `move_left` 仍按住。
这与 (A) 的冻结书证逐条对应。

### 2.3 反例检验（**我的判据能区分"没动"与"动不了"**）

| # | 要把什么排除 | 反例/对照 | 读数 |
|---|---|---|---|
| C1 | "**动不了**：该输入通道根本推不动这个游戏" | **同轮、同候选、同一注入形状**的 `input_channel_probe`：**0 次** `editor_simulate_input_action`，只用录制注入，把玩家 `67.3333358764648 → 173.666687011719`（30 帧） | 见 (B) 第 1–2 行；⇒ 通道有能力，且"缺 `editor_simulate_input_action`"**不是**判据（这也正是任务书 §0 要驳的那条） |
| C2 | "**动不了**：关卡在 x=225 附近挡住了玩家" | 同一轮的 `input_replay` `move_right` 窗口自己的逐帧序列 `192.000045776367 → 408.333038330078`，**穿过 225，也穿过 Coin1 的 400** | 见 (B) 第 3–4 行 |
| C3 | "**动不了**：被挡住但确实在推" | `facing=-1` 且 `velocity.x=0.0`（C-节读数 + `player.gd` 两条赋值路径）：被挡住的玩家读不出这两个值 | 见 (C) |
| C4 | "没动是因为**采样取错对象/区间**" | 两个窗口的 `node_path` 都是 `/root/Main/Player`，都是 `frame_count=60/interval=1` 的同名工具 | 见 `spike_output.txt` §D3 |
| C5 | "没动是因为**游戏没步进**" | 窗口自己那 8 次调用期间玩家满速左移了 **4.000015 帧**（位置读数，不是推断） | 见 (B) 末段 |

**C1 是任务书点名要求的那一类反例**：它证明"0 次注入"这个现象在同轮里**既能对应"不动"也能对应"动了"**，因此该判据不充分——
而我的判据（同轮能力对照 + 几何穿越对照 + 游戏自身 `facing`/`velocity` 读数）在 C1 成立的前提下仍然把 (a)(c)(d) 逐条排除。

---

## 3. ② 角色自起的 `play_scene` 重发布游戏路由

### 3.1 缺陷与落点

验收已定位到源码：`cli_impl.rs` 的角色侧 CLI 只 **adopt**（`bridge::adopt_published_game_route`），
而 **publish** 只发生在运行时的电池路径（`GodotAdapter` 的 `play_scene_ready` 步）⇒ 角色自己 `editor_play_scene` 起的游戏，
其路由永远不会写进 `runs/<id>/game_endpoint.json`（T11：`play_scene` 回 pid 4784，紧接着同一条命令仍打印 pid 33536）。

**改动**（发布者/采纳者边界写清了）：

| 层 | 角色 | 文件 |
|---|---|---|
| 采纳者 | `bridge::adopt_published_game_route`（**未改**） | `src/tools/bridge.rs` |
| 发布者 | `ProjectAdapter::publish_role_started_game_route`（新增；`GodotAdapter` 实现，默认 `Ok(None)`） | `src/adapter/mod.rs`、`src/adapter/godot.rs` |
| 触发点 | `hoh tools call editor_play_scene`：先 adopt → 调工具 → **若回包宣告了新路由则发布** → 才打印成功 | `src/cli_impl.rs` |
| 回包载体 | `bridge::ToolCallReply` + `bridge::tools_call_with_reply`（`tools_call` 的输出字节不变） | `src/tools/bridge.rs` |

顺序与运行时启动同构、且不是细节：`install_game_endpoint`（仅进程内路由）→ 用**已安装**的路由轮询 `running_game_get_scene_tree`
（就绪谓词就是电池自己的 `scene_tree_readiness`，DR-72 ⑤）→ `publish_game_endpoint`。任何失败路径都 `clear_game_endpoint()`
（同时撤回文件），并返回错误（`HofError::External` ⇒ **exit 4**），**绝不静默沿用旧路由、绝不回退到编辑器端点**。

### 3.2 三条测试（先红/回归钉）

`tests/game_route_across_processes.rs`（真实 `hoh` 二进制 + loopback JSON-RPC 双端点，离线）：

1. `a_role_started_scene_republishes_the_game_route_for_later_processes` —— 路由文件先指向**死 pid/死端口**（T11 的形状），
   编辑器宣告一个**活的新游戏**；断言 `exit 0`、新游戏端点**先被就绪轮询问过**、路由文件被改写成**新 endpoint + 新 pid**，
   且**另一个新进程**随后能通过该路由到达新游戏（编辑器端点从不收到 `running_game_*`）。
2. `a_role_started_scene_that_never_becomes_ready_is_refused_and_leaves_no_route` —— **回归钉**：宣告的游戏是死端口，
   而路由文件里原本有一个**活的、会应答的**旧游戏；断言 `exit != 0`、**旧游戏一次都没被问过**（`previous.tools()` 为空）、
   失败后路由文件**不存在**（`clear` 已撤回），随后 `running_game_get_scene_tree` 拿到的是 **DR-43 的显式 `game_endpoint_unavailable`**，
   且编辑器端点**没有收到任何 `running_game_*`**。
3. `a_role_started_scene_whose_route_cannot_be_published_fails_loudly` —— 路由路径的父目录是一个**普通文件**，
   `publish_game_route` 无法建目录；断言 `exit != 0`、消息里**明说 "could not be published" 与 "DR-43"**、
   编辑器自己的回包**没有**被当作成功打印、且就绪确认确实发生在发布尝试之前。

既有的"死 pid 路由仍被拒"钉（`a_route_whose_recorded_game_process_is_gone_is_refused_even_when_the_port_answers`、
`a_route_pointing_at_a_closed_port_is_refused_explicitly`、`an_expired_route_is_refused_even_when_it_still_answers`、
`without_a_published_route_the_game_call_still_fails_loudly`）**全部保持绿**（`gate/test.txt`），拒绝条件一条未放宽。

---

## 4. ③ 结构假阴性（F-T11-3）

### 4.1 事实（先复算一遍，不靠转述）

`spike_output.txt` §E：11 张冻结帧里**只有 `replay-move_right-before.png` 有 576 个黄色像素**（其余 10 张全 0）；
`input_replay` 的 `move_right` 窗口把玩家从 `192.000045776367` 带过 `Coin1`（`x=400`），
而 `interaction_evidence` 的首个计数读数已经是 `Coins: 1`；`main.gd` 从 `0` 起、`coin.gd::collect()` 是唯一自增点
⇒ **F10 的 `0 -> 1` 在这个窗口结构上不可达**。这就是"观测窗口排在被观测事件之后"，不是"产品不会拾取"。

### 4.2 改动

1. **顺序**（`src/adapter/godot.rs` 的 `run()`）：`interaction_evidence` 移到 `input_channel_probe` / `input_replay` **之前**。
   步骤 id 常量 `COIN_OBSERVING_BATTERY_STEP` / `COIN_CONSUMING_BATTERY_STEPS` 把这条规则**写成数据**，
   测试读的是**电池真的产出的记录顺序**（不是源码文本）。
2. **自给自足**：观测窗口在第一批驱动之前，用游戏进程通道释放 `INTERACTION_STALE_ACTIONS`（当前 = `move_left`），
   失败时在判定里写 `STALE_ACTION_NOT_RELEASED`（不吞）。这正是 spike 判出的真因的修复：窗口不再依赖别的步骤的状态。

### 4.3 测试与回归钉

`tests/evidence_battery.rs`：

* `the_coin_observing_window_runs_before_every_consuming_window` —— 跑完整电池，读 `records` 的 `step_id` 顺序，
  断言观测窗口的下标 **<** 每个消耗窗口的下标。**把观测窗口挪回消耗窗口之后 ⇒ 红**：植入 P1 复原了 DR-77 HEAD 的三行顺序，
  该测试 `exit 101`，panic 于 `tests\evidence_battery.rs:4733`（`TASK-DR78-spike/plants/P1-order.txt`）。
* `the_observing_window_clears_a_stale_opposing_action_by_itself` —— 双端点**开局就按住 `move_left`**（T11 的真实状态），
  断言窗口仍然 `COIN_PICKED_UP`，**并且**原始调用列表里"释放 `move_left`"发生在"第一批注入之前"。
  **去掉自清动作 ⇒ 红**：植入 P2，`exit 101`，panic 于 `:4770`（`plants/P2-release.txt`）。
* 夹具也按游戏真实语义修了：交互窗口的"驱动 ⇒ 位移"斜坡现在**以 `Input.get_axis` 的结果为条件**
  （`game_axis() > 0.0`），所以"注入被接受"不再等于"玩家会动"——这正是 T11 里被掩盖的那一步；
  并在窗口结束（非 `position` 的断言形状）时解除驱动模型，避免它泄漏给 DR-78 之后排在后面的窗口。

---

## 5. ④ 并入 D77-A / D77-B

### 5.1 D77-A：常量退化成新 token，使两条映射断言恒真

**落点** `tests/interaction_contract.rs`：

* `const SUPERSEDED_GEOMETRIC_TOKEN` 从 `BLOCKED_VERDICT` 改回 `"WIN_UNREACHABLE_GEOMETRICALLY"`；
* 新增 `the_superseded_token_is_the_old_name_and_not_a_copy_of_the_new_one`：`assert_ne!(旧名, 新名)` + `assert_eq!(旧名, 字面旧名)`。
  **植入 P4**（把常量改回 `BLOCKED_VERDICT`，即 DR-77 的原状态，已核对与 `HEAD~1` 原文逐字相同）⇒ 该测试 `exit 101`（`:55`）。
* **修掉两条断言各自的退化**（这是"常量改回旧名就会在未改动的树上打红"的根因）：
  * 交付技能是 **CRLF**，原来 `skill.split("\n\n")` 根本切不开段落 ⇒ 整份文档变成一个"段落"，判据退化成"全文某处提到新名"。
    现在先归一化行尾再逐段检查，**任何提到旧名的段落都必须同段给出新名**。
  * 台账查找原来取"第一个提到旧名的段落"，那是 §2.2 的 DR-76 更正段（早于 DR-77 改名，只提旧名）⇒ 改回旧名必然假红。
    现在要求"**同时**含旧名与新名的段落"（即真正的映射段），这才是"台账必须给出映射"的断言。
* **用植入证明技能里只提旧名时测试必红**：**植入 P6** 往交付技能 `src/prompts/skills/godot-dev.md` 追加一段**只含旧名**的独立判定句
  ⇒ `the_godot_dev_skill_retracts_the_impassable_level_claim` `exit 101`，panic 于 `tests\interaction_contract.rs:317`。

### 5.2 D77-B：`geometric` 残留在测试名与消息/注释

| 原落点 | 现在 |
|---|---|
| `tests/evidence_battery.rs:4535 fn …_is_a_geometric_verdict` | `fn a_player_that_stops_advancing_with_budget_left_is_blocked_under_move_right` |
| 同文件 `:4548` 断言消息 "is a geometric verdict" | "is a `WIN_BLOCKED_UNDER_MOVE_RIGHT` verdict (movement-direction, not geometry)" |
| 同文件 `:337`、`:453`、`:4428` 注释/消息 | 改为 movement-direction / `WIN_BLOCKED_UNDER_MOVE_RIGHT` 口径 |
| `src/adapter/godot.rs:2857`、`:3886` 注释 | 改为"`WIN_BLOCKED_UNDER_MOVE_RIGHT` 那一个" |
| 旧名本身 | **保留**：`BLOCKED_VERDICT` 的文档注释、台账映射表（§12 第 6/10 行）、技能里的映射句，全部照旧 |

**测试名是证据的一部分**（会进 `cargo test` 输出与 `--list`），所以加了钉子
`the_battery_names_the_blocked_verdict_by_its_movement_direction`（`tests/evidence_battery.rs`）：
断言新名在、旧措辞不在（旧措辞用 `concat!` 拼出来，**免得钉子自己成为反例**）。
**植入 P5**（把函数名改回 `…_is_a_geometric_verdict`，与 `HEAD~1` 逐字相同）⇒ 该测试 `exit 101`（`:4834`）。

### 5.3 改名与"无测试名被删"的边界（**必须点名**）

任务书 ④ 要求把 `geometric` 从测试函数名里去掉，而门要求"无测试名被删"。二者在这一次改名上**必然交叉**：
`fn` 声明集合的差集是 **ADDED 20 / REMOVED 1**，**唯一**的 REMOVED 就是被点名改名的那个测试：

```
REMOVED (1):
    a_player_that_stops_advancing_with_budget_left_is_a_geometric_verdict   tests/evidence_battery.rs
ADDED   (20) = 7 条新测试 + 12 个新 helper/方法与 trait 实现 + 1 个改名后的新名
```

`#[ignore]` **9 → 9**，`--list` **553 = 546 + 7**，`git status` 无删除。
我没有用删除测试来让门变绿：这 1 条移除是任务书的显式要求，而且**同一测试以新名存在**（§5.2 的钉子证明两者指向同一个测试）。

---

## 6. 非空洞性与禁区自查

### 6.1 植入红表（6 处；**每处使"对应"测试红**；全部逐字节回退）

工具：`C:\Users\wyl\AppData\Local\Temp\dr78\plants.py`（**在仓外**；备份也在仓外 `dr78\plants\bak\`，报告里只放**转写** `TASK-DR78-spike/plants/*.txt`）。
每处回退后四重校验：`bytes_identical`（对仓外备份 `cmp` 式逐字节）+ `git hash-object == HEAD:<path>` + `git status --porcelain -uall` 空 + `git diff --stat` 空。

| # | 植入 | 落点 | 目标测试 | 红 | 回退 |
|---|---|---|---|---|---|
| P1 | 复原 DR-77 的电池顺序（观测窗口挪到消耗窗口之后） | `src/adapter/godot.rs` `run()` | `the_coin_observing_window_runs_before_every_consuming_window` | `exit 101` @ `evidence_battery.rs:4733` | 四重校验全 True；**且植入文本与 `HEAD~1` 原文逐字相同 = True** |
| P2 | 删掉观测窗口的自清动作块 | `src/adapter/godot.rs` | `the_observing_window_clears_a_stale_opposing_action_by_itself` | `exit 101` @ `:4770` | 同上 |
| P3 | 让 `editor_play_scene` 的发布分支永不匹配（= DR-77 行为） | `src/cli_impl.rs` | `a_role_started_scene_republishes_the_game_route_for_later_processes` | `exit 101` @ `game_route_across_processes.rs:368` | 同上 |
| P4 | 常量退回 `BLOCKED_VERDICT`（= DR-77 的 D77-A 状态） | `tests/interaction_contract.rs` | `the_superseded_token_is_the_old_name_and_not_a_copy_of_the_new_one` | `exit 101` @ `:55` | 同上；与 `HEAD~1` 原文逐字相同 = True |
| P5 | 测试名退回 `…_is_a_geometric_verdict`（= DR-77 的 D77-B 状态） | `tests/evidence_battery.rs` | `the_battery_names_the_blocked_verdict_by_its_movement_direction` | `exit 101` @ `:4834` | 同上；与 `HEAD~1` 原文逐字相同 = True |
| P6 | 交付技能追加一段只含旧名的判定句 | `src/prompts/skills/godot-dev.md` | `the_godot_dev_skill_retracts_the_impassable_level_claim` | `exit 101` @ `interaction_contract.rs:317` | 同上 |

**"真先红"与"植入红"的区分（如实）**：

* **我这一批没有为每条新测试单独存档"写测试时的那次红"日志**。可裁决的是：P1/P4/P5 把对应区域**逐字复原到 `HEAD~1` 的原文**
  （脚本自证 `the planted text equals HEAD~1's own text: True`），因此这三个红**就是**那三条测试在 DR-77 树上的真实结果——
  即"先红"的那一态被可复算地重建了，而不是我用一个虚构的破坏去凑红。
* P2/P3/P6 是**植入红**：它们移除/追加的是 DR-77 树上不存在的东西，只能证明终态非空洞、且"对应测试确实看着对应代码"。
* 另外，本批唯一"在实现之前就先跑过一次并确认红"的是 ③：把夹具改成按 `Input.get_axis` 判定之后、**在改动 `run()` 顺序之前**，
  `evidence_battery` 的交互测试即以真实失败红过一次（那一次的原始日志我没有单独存档，**不声称**；见 §7 未验证项）。

### 6.2 `runs/**` 零写入 + 六条只读基线摘要自证

口径（与 DR-77 / T11 验收同一口径，**仓根相对**小写 POSIX 路径 + TAB + 字节长 + TAB + sha256、LF 行、无尾随换行、
`Sort-Object` **文化序**、UTF-8 整块 sha256）；脚本 `baseline_digest_rootrel.ps1`（口径**重写**，不调用被验方脚本）：

```
.workspace/mario         files=178 digest=dee0a36f357c440d078c652d4d4b8990af1a63b88d282c1e36c04a16d006cc94 newest=2026-09-30 18:23:08
runs/smoke-t6            files=135 digest=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03 newest=2026-09-29 02:32:01
runs/smoke-t7            files=115 digest=6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7 newest=2026-09-29 14:41:14
runs/smoke-t8            files=358 digest=6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7 newest=2026-09-30 07:58:28
runs/smoke-t9            files=83  digest=541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d newest=2026-09-30 11:27:29
runs/smoke-t10           files=232 digest=319555896964ce1526f72a33cb239bf389fe29bcde23841764d13c57dfb38b8b newest=2026-09-30 18:23:08
.workspace/fresh-t11     files=100 digest=4c07c0b6d4352a5a64e1b49908e3ae1325f62f0a3b4de44d17efc51ebffd13a4 newest=2026-10-02 00:29:23
```

六条与 DR-77/T11 验收记录的值**逐字相同**（`smoke-t6` 命中点名自证值 `c144ef32…7a9c03`）。
**口径的两个坑我都实测过**（P1/T11A 的教训）：我第一版把路径算成"相对被扫目录"，六条**全部**对不上；
改成**仓根相对**后六条全部命中。⇒ 路径基准与排序口径都是承重的，报告里显式写明。
另外：

```
runs newer than 2026-10-02 01:00 = 0        （本批开工之后，runs/** 没有任何文件被写）
mario newer than 2026-10-02 01:00 = 0
fresh-t11 newer than 2026-10-02 00:35 = 0
```

⇒ **`runs/**` 零写入（连临时文件都没有）**；`runs/smoke-t11/evidence/**` 里那 6 个 00:34–00:38 的文件是 **T11 验收自己的**复盘转写，早于本批。

### 6.3 两个工作区未变

* `.workspace/mario`：摘要 `dee0a36f…` 与基线逐字相同（178 文件；newest 停在 2026-09-30 18:23:08）。
* `.workspace/fresh-t11`：**与冻结的 `A_1` 快照逐字节对照**
  （`runs/smoke-t11/versions/04d8ba5a12899ed8bfc2c04113932983e5db03e8d471717fc3da8b5db9a585c1`，
  排除 `.godot/.import/.hoh/.git`）：`11 文件 / 8830 B` 对 `11 文件 / 8830 B`，**only-in-live=[]、only-in-snapshot=[]、differing=[]** ⇒ **IDENTICAL**
  （含 `project.godot 1346`、`scenes/main.tscn 4358`、`scripts/*.gd` 与 `.uid` 全部 same）。

### 6.4 冻结件、引擎、依赖、推送

```
sha256(.spec/hof-rs/PRD-mario.md) = 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a   （与 T11 meta 的 spec sha 相同）
git diff --stat HEAD~1..HEAD -- DECISIONS.md   -> 0 行     （本批未动 DECISIONS.md）
git -C godot-mcp/godot rev-parse HEAD          -> fc63af77c33368c4a1bb839c95d19750554f63a3
git -C godot-mcp/godot status --porcelain -uall -> 0 行
git diff --stat HEAD~1..HEAD -- Cargo.toml Cargo.lock -> 0 行      （无新依赖）
git rev-list --left-right --count origin/master...HEAD -> 0  13     （未推送；闸门已武装，见 §6.5）
git diff --cached --stat -> 0 行                                     （未 stage）
git status --porcelain -uall -> 空                                   （仓内无临时物）
```

### 6.5 三个假绿陷阱（实测）

1. `git diff --stat -- definitely/not/a/real/path` ⇒ **stdout 空、exit 0**（不存在的路径看起来"干净"）；对照真命中 `git ls-files godot-mcp` = 6484、`git ls-files godot-mcp/godot` = 0。
2. `git rev-parse HEAD HEAD^` = `bf943d0… / 1bed9b1…`（真 HEAD 与真父）；`git cat-file -e HEAD:definitely/not/here` ⇒ **exit 128** `does not exist`。
3. `git check-ignore -v runs godot-mcp/godot .workspace` ⇒ `.gitignore:12 runs/`、`.gitignore:33 godot-mcp/godot/`、`.gitignore:11 .workspace/`
   ⇒ 这三处的"未变"**只能**靠摘要 / 嵌套仓 / 逐字节对照证明（本报告用的正是这三条）。
   **未推送**：`origin/master` 停在 `1bed9b1`，本地领先 13，我没有执行任何 `git push`（闸门已武装且 GitHub 不可达）。

### 6.6 行尾与 PowerShell

被编辑的 7 个文件**各自保持原有行尾**（`src/adapter/godot.rs`、`src/adapter/mod.rs`、`tests/evidence_battery.rs`、
`tests/game_route_across_processes.rs`、spike 工件 = LF；`src/cli_impl.rs`、`src/tools/bridge.rs`、`tests/interaction_contract.rs` = CRLF）。
`cargo fmt --check` 对两种行尾都 exit 0，而我**只**对两个 LF 文件跑过 `rustfmt … <file>`（写模式），
没有对 CRLF 文件跑过任何整文件写模式格式化。本批**没有**用 PowerShell 的 `Get-Content -Raw`+`Set-Content` 写过任何文件
（PowerShell 只用于 §6.2 的**只读**摘要）。

---

## 7. 遗留风险与未验证项（严格区分实测 / 推断）

**未验证（我做不到的）**

1. **真机复现**：本批是离线批次 ⇒ ②③④ 的修复**没有**在任何一次真机轮上跑过；"角色自起 `play_scene` 后路由被刷新"
   只在离线双端点上被证明（真实 `hoh` 二进制 + loopback JSON-RPC）。
2. **我把 spike 的真因当作 (b) 是"读数 + 冻结游戏代码 + 生产源码路径"三者夹出来的**，不是真机复现的因果实验。
   仍未知：`move_right` 生效的**确切帧**；以及真机上一模一样的遗留动作是否还会以别的形式出现。
3. **真先红的过程日志**：P1/P4/P5 能复原到 `HEAD~1` 原文（可复算地重建了"先红那一态"），但**没有**独立的当时日志。
4. **`cargo fmt` 的行尾不可见性**（DR-77 R4）依旧：fmt 与 git 都对 CRLF/LF 差异不敏感；本批靠"每个文件保持原行尾 + 只对 LF 文件写模式格式化"来规避。
5. **`editor_play_scene` 在"没有配置路由文件"的场景**（`HOH_GAME_ROUTE` 未设，例如手工 bench 调用）：`publish_game_endpoint`
   在这种情况下是 no-op，但**就绪确认仍会跑**——这是本批引入的一处可观察行为变化（已披露；套件里没有这样的调用，所以没有测试覆盖它）。
6. 未跑 `cargo build --release`；门只覆盖 `--offline` 的测试与格式检查。

**风险（给下一批/真机轮）**

1. **③ 的顺序不变量是"电池自己的顺序"**。若将来有人把观测窗口挪到消耗窗口之后，P1 证明测试会红——
   但**真机上"金币在哪一帧被吃掉"仍取决于关卡与驱动**，回归钉保护的是结构，不是某一关的数值。
2. **②的就绪确认会给角色侧 `editor_play_scene` 增加一次最长 `tools.ready_timeout_seconds`（默认 30 s）的等待**。
   真机上若某次 play 永远不就绪，角色 CLI 会以 exit 4 失败而不是立刻返回——这是有意的（宁可显式失败也不留下撒谎的路由），
   但它改变了角色侧的时延画像，下一真机轮应复看。
3. **③ 的自清动作只列了 `move_left`**：在当前 `player.gd` 语义下（水平轴 + `is_action_just_pressed("jump")`）足够；
   若关卡改成"按住即持续跳跃"这类语义，需要把 `jump` 也列进去。
4. `INTERACTION_STALE_ACTIONS` 的释放在**真机**上是否总被接受（`play_input_recording(pressed=false)` 的拒绝率）没有真机读数；
   被拒时窗口会在判定里写 `STALE_ACTION_NOT_RELEASED`，但**不会**因此失败（当前实现），
   下一批可考虑把它升级为"驱动不可信"的失败。

**我没有检查的**

* 未启动 Godot、未调用任何 MCP/模型端点、未联网 ⇒ ②③④ 的真机行为一律不声称。
* 未审 `godot-mcp/**` 内部实现（只验其未改）。
* 未逐条重跑 DR-77 验收的 17 条判据；我重跑的门是 DR-78 自己的门（546/0/7）。
* 未做密钥熵扫描（沿用 T11 的模式化检查口径之外没有新增）。

---

## 8. 报告纪律自证（§2 的四条）

1. **"0 次 / 逐位相同 / 不存在"型断言都可复算，且写明作用域**：
   * "`input_channel_probe` 里 `editor_simulate_input_action` = 0 次" ⇒ `spike.py` §B 打印该计数（作用域 = **那一个文件**）；
   * "window 内 60 帧只有 1 个 x 值" ⇒ `spike.py` §B 打印 `unique_x=1`（作用域 = **那一个 batch 的 `running_game_get_node_property_samples` 载荷**）；
   * "只有 `replay-move_right-before.png` 有 576 个黄像素" ⇒ `spike.py` §E 逐帧列出（作用域 = **冻结的 11 张帧**）；
   * "整轮游戏通道上没有 `move_left pressed=false`" ⇒ `spike.py` §A 逐条列出（作用域 = **`raw/` 下三个输入相关载荷**；编辑器侧那一处已标 `target=editor`）；
   * "`runs/**` 零写入" ⇒ §6.2 的摘要 + `find … -newermt` 计数（作用域 = **六条基线 + 本批时间窗**）。
2. **机制归因都附反例检验**：§2.3 的 C1–C5，把"我们没看到 X"与"X 不可能"分开写；③/② 的每条归因都有对应植入。
3. **机器可读块由序列化器产出并回读**：本块的来源与回读命令见下方 §8.1。
4. **派生物与结论不矛盾**：`TASK-DR78-spike/*` 里所有数字都取自同一次脚本运行（脚本用 Python 直接以 UTF-8 写盘），
   报告正文的数字与之一致；`gate/*.txt` 与正文的门读数一致（由 §0 的 JSON 块记录同一组值）。

### 8.1 机器可读块

```
$ python .spec/hof-rs/tasks/TASK-DR78-spike/validate_json_block.py
```

（校验器是**栅栏感知**的：按 ``` 切块，只对 info string 为 `json` 的块做 `json.loads`，并核对顶层键与 `verdict`。
输出落在 `TASK-DR78-spike/json_block_check.txt`。）
