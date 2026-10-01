# TASK-DR76-REPORT — 修 DR-73 验收的三条 major（真机读不到计数 / 预算够不到目标 / "关卡不可通过"是假的）

> 实现子代理（无上游对话上下文）。落点：`F:\moonbit-hof-rs`。**离线**：未启动 Godot、未触端口、未联网、
> 未调用模型端点、未跑真机轮；**未 push**（闸门已武装）；**`runs/**` 零写入**（连临时文件都没有）；
> 分析脚本、备份、日志全部在仓外 `C:\Users\wyl\AppData\Local\Temp\dr76\`；**未用 `rm -rf` 删任何路径**，
> 清 fingerprint 用的是"逐条校验父目录 + `shutil.rmtree`"的守卫脚本；
> **未由未展开变量构造路径**；未改 `PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`；
> **对 `.workspace/mario/**` 零字节写入**。
> 实现提交：`b3d1652`（DR-76 的实现 + 文档 + 夹具）；本报告另作一次提交（SHA 以 `git log` 为准）。

---

## 0. 机器可读结论块（已用栅栏感知脚本 `json.loads` 亲验，见 §9）

```json
{
  "verdict": "pass_with_residual_risk",
  "task": "TASK-DR76",
  "head_implementation_commit": "b3d1652",
  "gate": {"cargo_test_offline": "exit 0", "passed": 533, "failed": 0, "ignored": 7,
           "binaries": 58, "list_entries": 540, "benchmarks": 0, "fmt_check_exit": 0,
           "baseline_before_batch": "523/0/7", "test_names_removed": 0,
           "ignore_attribute_delta": 0, "tracked_rs_touched_individually": 95},
  "criteria": [
    {"id": "A1-real-shape-counter", "pass": true,
     "evidence": "hud_label_candidates() uses only name/path/type from the tree; the window reads each candidate's text through running_game_get_node_properties and keeps the one starting with `Coins:`. Frozen evidence: all 10 scene-tree payloads from runs/smoke-t5|t6|t7|t8|t10 give a Label exactly name/path/type (0 text keys), and the frozen t10 tree declares /root/Main/HUD/Coins. Fixtures derived by scripts/derive_dr76_fixtures.py (scene_tree + hud-labels byte-for-byte). Plant P1 (restore the text requirement) reddens the real-shape test with candidates=[] and COIN_COUNTER_UNREADABLE while the same record says WIN_DRIVEN."},
    {"id": "A2-budget-and-split", "pass": true,
     "evidence": "INTERACTION_MAX_BATCHES = SPEC_MAX_TRAVERSAL_SECONDS(120, PRD F17) + 10 = 130 one-second batches. Pinned by the constant test (P2 red: `the drive budget (1 batches = 60 frames) must cover ... (120 s = 7200 frames)`) and by behaviour (P2 red: green window becomes WIN_UNREACHED_WITHIN_BUDGET with coverage_shortfall_px=Some(6120.0)). VERDICT SPLIT: WIN_UNREACHED_WITHIN_BUDGET (budget exhausted; claims nothing about the level) vs WIN_UNREACHABLE_GEOMETRICALLY (2 consecutive stalled batches with budget left). Plant P3 (emit the geometric token for the budget case) reddens a_level_whose_goal_is_unreachable_fails_only_the_win_half."},
    {"id": "A3-retraction", "pass": true,
     "evidence": "src/prompts/skills/godot-dev.md 3b now says the ground is one 6800x40 RectangleShape2D centred at x=3400, continuous under the goal, that the old sentence was false and must not be acted on, and names coverage as the true cause; the superseded wording is preserved inside a marked block. tests/interaction_contract.rs's comment is corrected and the new test the_godot_dev_skill_retracts_the_impassable_level_claim pins it (P4 red). TASK-DR73-REPORT.md section 2.2(A-3) carries an inline correction plus accumulated section 12. The 4deefc8 commit message is unrewritable and is corrected in the ledger only (section 12)."},
    {"id": "A4-max-x", "pass": true,
     "evidence": "The whole-round maximum is 455.999572753906, computed from the frozen per-frame samples by tests/dr76_payload_shapes.rs::the_frozen_rounds_maximum_player_x_is_derived_from_the_samples (P6 red with left 455.999572753906 right 448.666). The DR-73 report and the T10 acceptance are corrected (additive errata, original evidence strings untouched)."},
    {"id": "A5-wrapper-script", "pass": true,
     "evidence": "The wrapper IS tracked: .spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/scripts/run_round.ps1, added by 15e071f, line 14 is `\"ROUND_EXIT=$ec\"`. TASK-DR73-REPORT.md disclosure 5 is corrected with the superseded wording retained; the correct reason is that the line was never frozen into the round's artifacts."},
    {"id": "A6-sidecar-non-vacuity", "pass": true,
     "evidence": "The (marker, leaked) table is replaced by a check derived from the original's own `HOH_*=` names; every surviving assignment in the sidecar must carry a redaction marker, and `inspected > 0` is asserted. Measured: of the six DR-73 markers only HOH_MODEL_API_KEY= occurs in the sidecar (2 lines), so 5 of 6 pairs never ran at all; the old table's two named absences (HOH_ARTIFACT_DIR=, PATH=) are absent from the original too and are now recorded as facts. Plant P5 (copy instead of replace) reddens both sidecar tests."},
    {"id": "A7-citation-drift", "pass": true,
     "evidence": "secrets.rs:222 -> :223, cli_impl.rs:798 -> :803, and 13 items (9 M + 4 ??) -> 14 paths (9 M + 5 A) are corrected in TASK-DR73-REPORT.md with inline `DR-76 更正` markers and in section 12."},
    {"id": "N1-no-handwriting", "pass": true,
     "evidence": "17 project files of .workspace/mario are sha256-identical to the frozen runs/smoke-t10/iter-1/candidate; `diff -r -x .hoh -x .godot` exits 0; find -newermt 2026-10-01 = 0 under both .workspace/mario and runs/**."},
    {"id": "N2-pipeline-side-only", "pass": true,
     "evidence": "git diff --name-status 4e0b760..HEAD touches only .gitattributes, .spec/hof-rs/tasks/TASK-DR73-REPORT.md, .spec/hof-rs/tasks/TASK-SMOKE-T10-ACCEPTANCE.md, .spec/hof-rs/tasks/TASK-DR76-REPORT.md, scripts/derive_dr76_fixtures.py, src/adapter/godot.rs, src/prompts/skills/godot-dev.md, tests/**; no D, no R, no game file."},
    {"id": "G-gate", "pass": true,
     "evidence": "Fingerprints cleared, then 95 tracked .rs files touched one at a time (no shell glob), then cargo test --offline exit 0 = 533/0/7 over 58 binaries; --list = 540, 0 benchmarks; cargo fmt --check exit 0."},
    {"id": "E3-criterion-3", "pass": false,
     "evidence": "NOT CLAIMED. Only a real round can decide. This batch makes the two behaviours observable on the real payload shape and makes the drive budget sufficient for the specification's longest level, but no round was run (hard constraint)."}
  ],
  "defects_remaining": [],
  "risks": [
    "The interaction window holds move_right for up to 130 s of game time when the win is never observed, and it runs before node_and_collision_assertions; downstream battery steps and the Tester then read a perturbed world. No test covers this ordering effect and I could not run the engine to measure it.",
    "WIN_UNREACHABLE_GEOMETRICALLY is an inference from `the sampled player x did not advance over 2 consecutive driven batches while budget remained`. It is evidence that holding move_right cannot advance the player, not proof about a jump the window never takes; the skill tells the Developer the window's contract is `move_right`.",
    "The candidate scan reads every HUD Label's text, so a project with many HUD labels pays one property call each; the scan order is the scene tree's order, so a project with two labels whose text starts with `Coins:` gets the first in tree order (deterministic, but not a policy).",
    "The geometric verdict requires 2 consecutive stalled batches; a level with a long flat stall the player can escape (a moving platform, an enemy knockback) could take it. The record carries the numbers, so a reader can see the evidence, but the token is a diagnosis, not a proof."
  ],
  "unverified": [
    "Whether a real round now observes the pickup and the win (only real hardware can decide; no Godot was started).",
    "The runtime mechanism behind `swept but not collected` in smoke-t10 - unchanged from DR-73, still unclaimed.",
    "Whether the 130-batch budget is enough on real hardware for a level that is blocked by a wall requiring a jump: the window only holds move_right, so such a level reports WIN_UNREACHABLE_GEOMETRICALLY (measured only on the fixture).",
    "Sampling latency and goal-flag read latency on real hardware.",
    "Whether a real round's scene tree really lists the counter cell among the HUD Labels in every future project (the frozen evidence is smoke-t5|t6|t7|t8|t10 only)."
  ],
  "machine_readable_block_check": "see section 9; 1 json-fenced block, parse OK"
}
```

---

## 1. 结论与门（真实读数）

**结论**：DR-73 验收的 **3 major + 3 minor + 1 info**（A1..A7）全部落地；两条新增的**机制性防线**
（夹具只能从冻结载荷派生、覆盖不足不得冒充几何不可达）都有先红测试钉住。**E3（判据(3)）是否 met
不作声称**——只有真机能定，本批未跑真机。

### 1.1 门（逐字读数）

```
$ python scripts/clear_fingerprint.py                 # 逐条校验父目录后 shutil.rmtree
cleared 3 hof-rs fingerprint entries                  # 本次清前仓库里现存的 hof-rs 条目数
fingerprint_exit=0
$ while IFS= read -r p; do touch -- "$p"; done < <(git ls-files '*.rs')
touched=95                                            # 逐文件，无 shell 通配符
$ cargo test --offline   > gate/test.txt 2>&1; echo "EXIT=$?" >> gate/test.txt
   Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)         # 清 fingerprint 后**确实重编**（不是陈旧产物）
   …（58 个 test binary，逐 binary 求和）…
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
EXIT=0
$ cargo test --offline -- --list | tail
   Doc-tests hof_rs
0 tests, 0 benchmarks
EXIT=0
$ cargo fmt --check ; echo $?
0
```

| 指标 | 本批 HEAD | DR-73 基线 | 判定 |
|---|---|---|---|
| `cargo test --offline` 退出码 | **0** | 0 | ✅ |
| passed / failed / ignored | **533 / 0 / 7** | 523 / 0 / 7 | ✅ 净增 10 |
| test binary 数 | **58** | 57 | ✅ |
| `--list` 条目 | **540** | 530 | ✅ 533+7=540 自洽，0 benchmark |
| 测试名被删 | **0** | — | ✅（`git show` 双修订解析，见 §1.2） |
| `#[ignore]` 属性数 | **7** | 7 | ✅ 不增长 |
| `cargo fmt --check` | **0** | 0 | ✅ |

### 1.2 测试名的双修订核对（自产）

```
$ python scripts/testnames.py           # 从 4e0b760 与 HEAD 的每个跟踪 .rs via `git show` 解析
base tests=523 head tests=533
REMOVED=0 []
added=10
  + a_hand_written_text_member_on_the_tree_cannot_choose_the_counter
  + a_player_that_stops_advancing_with_budget_left_is_a_geometric_verdict
  + every_frozen_scene_tree_label_carries_exactly_the_three_keys_the_engine_sends
  + the_counter_is_found_from_the_frozen_tree_without_any_text_member
  + the_derived_fixtures_match_the_sha256_the_manifest_pins
  + the_drive_budget_covers_the_specifications_longest_traversal
  + the_frozen_hud_label_read_shows_the_property_reader_is_a_real_path
  + the_frozen_rounds_maximum_player_x_is_derived_from_the_samples
  + the_godot_dev_skill_retracts_the_impassable_level_claim
  + the_interaction_window_finds_the_counter_in_the_real_scene_tree_shape
#[ignore] attributes: base=7 head=7
```

### 1.3 行尾与工具口径（自证）

- **未用 PowerShell 的 `Get-Content -Raw`+`Set-Content`**：所有源码改动用编辑器逐处替换 + `cargo fmt`；
  报告分析用 python/bash，全部只读 `runs/**`。
- **未重写行尾**：逐文件比对"工作树 CR/LF vs HEAD blob"——被编辑的 `src/adapter/godot.rs`、
  `tests/evidence_battery.rs`、`tests/round_artifacts_sidecar.rs`、两份 `.md` 报告保持**全 LF**；
  `src/prompts/skills/godot-dev.md`（CR=339=LF=339）与 `tests/interaction_contract.rs`（CR=275=LF=275）
  保持**全 CRLF**（与本机既有的混合现状一致，编辑后仍全行统一，没有出现混合行尾）。
  `tests/fixtures/dr76/hud_labels_smoke_t10.json` 的 CRLF **就是冻结原件的 CRLF**（`cmp` 逐字节相同）。
- **新增 `.gitattributes` 钉** `tests/fixtures/dr76/** -text`：否则 `core.autocrlf=true` 会在提交时把
  该 CRLF 夹具规范化成 LF，使"byte-for-byte 拷贝"在**提交后的 blob** 里不成立。
  实测：`git cat-file -p :tests/fixtures/dr76/hud_labels_smoke_t10.json` = CR 29 / LF 29 / 707 B
  = 冻结源件大小；未加钉时该 blob 是 CR 0 / 678 B（这就是加钉的直接证据）。
- **清 fingerprint**：如上；**未用 `rm -rf`**；`clear_fingerprint.py` 对每个候选路径断言
  `os.path.dirname(resolved) == <fingerprint 目录>` 且 basename 以 `hof-rs-` 开头，否则拒绝执行。

---

## 2. ① 真机读不到计数（夹具编造字段）——真实形状证据与红→绿

### 2.1 事实（自产，读冻结载荷）

```
$ python scripts/scan_labels.py        # walk 每个嵌入式 {"tree": …}，只读
TOTAL payloads 18 labels 40 labels-with-text 0
smoke-t10\…\scene_tree.json        trees= 1 labels= 5 with_text= 0
    ['name','path','type'] Score|Result|Lives|Coins|Time  (/root/Main/HUD/…)
smoke-t5|t6|t7|t8 (+t7-experiment, t8/quarantine)  …… 全部 with_text= 0
```

⇒ 真实的 `running_game_get_scene_tree` 在 Label 上**只发 `name`/`path`/`type`**，且冻结轮次**确实有**
`/root/Main/HUD/Coins` 这一格。DR-73 的窗口要求 `Label.text` ⇒ 真机 `coin_label` 恒 `None`、
恒 `COIN_COUNTER_UNREADABLE`，与游戏对错无关；而测试夹具**自己塞进了那个字段**。

### 2.2 修法（只改流水线侧）

- `src/adapter/godot.rs`：`hud_label_path(tree, prefix) -> Option<String>`（依赖 `node["text"]`）
  换成 **`pub fn hud_label_candidates(tree) -> Vec<String>`**：只用真实存在的 `type`/`path`、
  且只收 `/HUD/` 下的 `Label`。
- `step_interaction_evidence` (a) 段：**逐个候选经 `running_game_get_node_properties{properties:["text"]}`
  读文本**，取第一个 `trim_start().starts_with("Coins:")` 者；`coin_before` 就是这次扫描读到的文本
  （**不重复读**，所以断言的期望值就是"选出该格的那次读数"）。候选清单作为一行进入 observation。
- 真机可读路径同时被冻结证据背书：`.hoh/evidence/hud-labels.json`（Tester 在**活着的轮次进程**里
  只读读到的）就是 `running_game_get_node_properties` 对 HUD Label 的真实回包形状
  （`{"node_path","properties":{"text","visible"},"type":"Label"}`），其中 `Coins: 0` 明明白白。

### 2.3 夹具从冻结载荷派生（本批最重要的防再犯）

**派生命令**（仓库根执行，幂等、可重跑）：

```
python scripts/derive_dr76_fixtures.py
```

产出与来源（`tests/fixtures/dr76/MANIFEST.json` 逐个钉 sha256；脚本被 `tests/dr76_payload_shapes.rs`
的 `the_derived_fixtures_match_the_sha256_the_manifest_pins` 执行核对）：

| 夹具 | 来源（只读） | 方式 | sha256 |
|---|---|---|---|
| `scene_tree_smoke_t10.json` | `runs/smoke-t10/iter-1/candidate/.hoh/deterministic/raw/scene_tree.json` | **逐字节拷贝** | `5fa1b08387184ca05bffb14a51ab509e3a53660c7604437a036161b35cf5e128` |
| `hud_labels_smoke_t10.json` | `runs/smoke-t10/iter-1/candidate/.hoh/evidence/hud-labels.json` | **逐字节拷贝** | `3bf62ba0bf347f7d617b0edd5a3736d64ca0771ef7d5a9f790c4364223dde64e` |
| `interaction_position_samples_smoke_t10.json` | `runs/smoke-t10/…/raw/input_replay.json`（148 KB） | 归约：四个 `position` 窗口的逐帧 x 序列 + 目标几何（每个数都是冻结浮点） | `dbd6c5aa1cca6505f197519400ef3cb30b7b181bae6e3dc8fc687a5a176d199c` |

```
$ cmp runs/smoke-t10/iter-1/candidate/.hoh/deterministic/raw/scene_tree.json tests/fixtures/dr76/scene_tree_smoke_t10.json
$ cmp runs/smoke-t10/iter-1/candidate/.hoh/evidence/hud-labels.json          tests/fixtures/dr76/hud_labels_smoke_t10.json
（两者均无输出 = 逐字节相同）
```

测试侧的对应改动：`tests/evidence_battery.rs::node_tree_payload` **不再手写 HUD 单元格**，
改为把冻结树的 `HUD.children` 原样搬进夹具；Label 的**回包形状**也改为从冻结
`hud-labels.json` 取（`frozen_label_reading()`，只替换 `text` 值）。唯一"合成"的仍是游戏状态本身
（计数、位置、flag），这正是夹具**应该**负责的部分。

### 2.4 先红（P1：把"要求 text 成员"放回去）与转绿

```
# P1 植入（src/adapter/godot.rs，hud_label_candidates 内）：
#     if node.get("text").and_then(Value::as_str).is_none() { return; }
$ cargo test --offline --test evidence_battery the_interaction_window_finds_the_counter_in_the_real_scene_tree_shape
test the_interaction_window_finds_the_counter_in_the_real_scene_tree_shape ... FAILED
thread '…' panicked at tests\evidence_battery.rs:4282:5:
the real tree shape must not make the counter unreadable: FAILED interaction: … HUD counter candidates
(…) = []; … interaction: COIN_COUNTER_UNREADABLE (no `Label` under `HUD` whose text starts with
`Coins:`; F10 cannot be observed); interaction: WIN_DRIVEN (goal.reached false -> true …)
test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 52 filtered out
EXIT=101
```

**这条红就是 A1 的可执行复现**：同一轮里 `WIN_DRIVEN` 成立、金币却"读不到"——正是真机上必然发生的事。
回退后（§6）同名测试**绿**；整测 `the_interaction_window_records_a_real_coin_pickup_and_its_assertion`
与 `the_interaction_window_finds_the_counter_in_the_real_scene_tree_shape` 在 §7 的门里全绿。

### 2.5 防夹具漂移的第二条测试（②）

`a_hand_written_text_member_on_the_tree_cannot_choose_the_counter`：场景树里给 **`Score`** 塞
`text = "Coins: 7"`（正是 DR-73 夹具的谎言），真正被游戏更新的是 `Coins`。选点必须来自**属性读取**
而不是树的 `text`。DR-73 的实现会选中 `Score`（属性读回 `Lives: 3  Coins: 0  Time: 120`），
于是 `COIN_COUNTER_UNREADABLE`；新实现选 `Coins`，记录 `Coins: 0 -> Coins: 1` + `COIN_PICKED_UP`。
该测试当前绿（在 §7 门内），并被 P1 一同打红（同族）。

---

## 3. ② 驱动预算够不到目标 + 可分判定

### 3.1 事实与修法

- 旧预算：`INTERACTION_MAX_BATCHES = 24` × `INTERACTION_BATCH_FRAMES = 60` = **1440 帧 = 24 s ≈ 5280 px**；
  冻结目标触发器距出生点 **6308 px**（`Goal` 40×80 @ x=6400，玩家盒 24 宽 ⇒ `x ≥ 6368`；出生 x=60）。
- 新预算：以**规格自身的上限**为准——`PRD-mario.md` **F17**："单次完整通关路径的预期耗时在 30–120 秒之间"。

```rust
pub const SPEC_MAX_TRAVERSAL_SECONDS: u64 = 120;                 // PRD F17
pub const INTERACTION_BUDGET_MARGIN_BATCHES: usize = 10;         // ≈2200 px 裕量
pub const INTERACTION_MAX_BATCHES: usize = 120 + 10;             // = 130 × 60 frames = 7800 帧
pub const INTERACTION_DRIVE_FRAMES: u64 = 130 * 60;
pub const INTERACTION_MIN_PROGRESS_PX: f64 = 1.0;                // < 1 帧位移 3.6667 px
pub const INTERACTION_STALL_BATCHES: usize = 2;
```

- **可区分判定**（A2 的教训变成代码）：`WIN_NOT_DRIVEN` 拆成
  - **`WIN_UNREACHED_WITHIN_BUDGET`**（130 批全部花完、flag 仍 false）——**覆盖**结论，明确写
    "这是 COVERAGE verdict，不是 geometry verdict：窗口没走到触发器，因此对关卡是否可通**不作任何声称**"；
  - **`WIN_UNREACHABLE_GEOMETRICALLY`**（连续 2 个批次的采样 max x 未前进 **且预算仍有剩余**）——
    唯一允许下几何/逻辑结论的分支，并记录剩余批次数；
  - 走不完的驱动（注入被拒 / 采样缺失 / flag 读不出）单独报，**不**从残缺驱动推结论。
- 两种判定都带 `coverage_shortfall_px = goal.position.x − player max x`（在驱动行与判定行各一次）。
- `INTERACTION_DRIVE_ACTION` 的契约没有改变：仍是"按住 `move_right`"，技能里也把这写成窗口的边界。

### 3.2 先红（P2a 预算常量；P2b 行为）

```
# P2 植入：INTERACTION_MAX_BATCHES = 1
$ cargo test --offline --test evidence_battery the_drive_budget_covers_the_specifications_longest_traversal
test the_drive_budget_covers_the_specifications_longest_traversal ... FAILED
thread '…' panicked at tests\evidence_battery.rs:4515:5:
the drive budget (1 batches = 60 frames) must cover the specification's longest traversal
(120 s = 7200 frames); PRD-mario.md F17 allows a level that takes that long, and a budget below it
records a coverage gap as if it were the game's failure
test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 52 filtered out   EXIT=101

$ cargo test --offline --test evidence_battery the_interaction_window_records_a_real_coin_pickup_and_its_assertion
test the_interaction_window_records_a_real_coin_pickup_and_its_assertion ... FAILED
thread '…' panicked at tests\evidence_battery.rs:4123:5:
the interaction window must be green on a project that delivers the behaviour: FAILED interaction:
… drove `move_right` for 1 of 1 batch(es) (60 frame(s) each, 60 frames budgeted), player max x=Some(280.0),
goal.position=Some(…6400.0…), coverage_shortfall_px=Some(6120.0); … interaction:
WIN_UNREACHED_WITHIN_BUDGET / WIN_NOT_DRIVEN (the window spent all 1 batch(es) = 60 frames of
`move_right` and goal.reached stayed false; … — this is a COVERAGE verdict, not a geometry verdict …)
test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 52 filtered out   EXIT=101
```

⇒ **DR-73 的 P9（24→1 全绿）不再成立**：现在改预算会同时打红一条常量钉与一条行为钉。
绿测本身也升级为"**冻结几何的最难情形**"：`Working` 的目标就放在冻结的 x=6400（触发器 6368），
窗口必须真的驱动 **29 批**才早停，而不是像 DR-73 那样 1 批就够（那正是旧夹具把预算问题掩盖掉的原因之一）。

### 3.3 覆盖 vs 几何：可执行区分（P3）

```
# P3 植入：把 budget_exhausted 分支的 token 改成 WIN_UNREACHABLE_GEOMETRICALLY
$ cargo test --offline --test evidence_battery a_level_whose_goal_is_unreachable_fails_only_the_win_half
test a_level_whose_goal_is_unreachable_fails_only_the_win_half ... FAILED
thread '…' panicked at tests\evidence_battery.rs:4440:5:
a goal beyond the budget must be a coverage verdict: FAILED interaction: … drove `move_right` for
130 of 130 batch(es) …, player max x=Some(28660.0), goal.position=Some(…30000.0…),
coverage_shortfall_px=Some(1340.0); … COIN_PICKED_UP (the counter grew 0 -> 1 …); … interaction:
WIN_UNREACHABLE_GEOMETRICALLY (the window spent all 130 batch(es) = 7800 frames … — this is a COVERAGE
verdict, not a geometry verdict …)
test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 52 filtered out   EXIT=101
```

绿态下（门内）三条测试分别钉住：
`a_level_whose_goal_is_unreachable_fails_only_the_win_half`（预算耗尽 ⇒ `WIN_UNREACHED_WITHIN_BUDGET`，
且 **不含** `WIN_UNREACHABLE_GEOMETRICALLY`，`coverage_shortfall_px=Some(1340` = 30000−28660）；
`a_player_that_stops_advancing_with_budget_left_is_a_geometric_verdict`（`Blocked` 关卡 ⇒
`WIN_UNREACHABLE_GEOMETRICALLY` 且"of the 130-batch budget were still unspent"，且**不含** coverage token）；
`a_project_that_never_picks_a_coin_up_is_recorded_as_a_gap`（t10 自身状态：`COIN_NOT_PICKED_UP` +
`WIN_UNREACHED_WITHIN_BUDGET`，且**不得**几何化）。

### 3.4 与 ③ 的相互作用（按任务书要求先修预算再谈可达性）

预算修好后，冻结几何在夹具上**可以是绿的**：29 批驱动到 x=6440，`WIN_DRIVEN`。
⇒ "胜利从未被驱动"在真机上**不能**再唯一归因于关卡几何；DR-73 的 A-3 诊断因此既错、又被本批的
记录结构永久堵住（覆盖不足只能读成 `WIN_UNREACHED_WITHIN_BUDGET`）。

---

## 4. ③ 撤回"关卡不可通过"（含已交付文本）与"哪里改不了"

### 4.1 被撤回的断言与冻结依据

被撤回的断言（DR-73 报告 §2.2(A-3) 与 `godot-dev.md` 3b）：*"x≈3800 之后没有地面 / 关卡不可通过 /
目标在位置上不可达"*。冻结依据（只读）：

```
runs/smoke-t10/iter-1/candidate/scenes/main.tscn
  :11  [sub_resource type="RectangleShape2D" id="s_ground"]
  :12  size = Vector2(6800, 40)
  :45  position = Vector2(3400, 320)          ⇒ x ∈ [0, 6800]，顶面 y=300
  :48  shape = SubResource("s_ground")
  :241 position = Vector2(6400, 280)          ⇒ Goal 40×80 ⇒ 触发器 x ≥ 6368
引擎自己的碰撞读数 runs/smoke-t10/…/raw/node_and_collision_assertions.json:
  editor_get_collision_info(Ground): Ground/CollisionShape2D has_shape=True disabled=False
                                     shape=RectangleShape2D; layer=1 mask=1
```

⇒ 地面**在目标下方连续**；从观测到的 max x 到目标之间唯一障碍是 x=1700 的 `32×60` 墙（顶面高 28 px，
在报告自己算出的 66 px 顶点内）。**真因是回放覆盖不足。**

### 4.2 更正清单（可改文本）

| 落点 | 处置 | 被取代措辞 |
|---|---|---|
| `src/prompts/skills/godot-dev.md` 3b（**交付给 Developer 的技能源**） | 改写为事实口径（6800×40 @3400、连续、唯一障碍 28 px、真因是覆盖）并新增 `> **Superseded (DR-76 ③)**` 引用块保留旧句、明写 "That was false, and it must not be acted on"；另写出窗口的 130 s 上限与两个判定 token | 旧句逐字保留在引用块内 |
| `tests/interaction_contract.rs`（源码注释，原 :104-105） | 注释改为事实口径并指向新测试 | 旧句以"which was false"标注后保留 |
| `.spec/hof-rs/tasks/TASK-DR73-REPORT.md` §2.2(A-3) | 段落**上方**插入 `⚠ DR-76 更正` 块（事实 + 真因 + 指向 §12），旧段**原样保留**并显式标注 `（superseded）` | 全文保留 |
| `.spec/hof-rs/tasks/TASK-DR73-REPORT.md` | **新增 §12「DR-76 更正台账」**：8 行表逐条列出"被取代的位置 / 原文 / 更正后的事实"，并单列**不可改写落点** | 全文保留 |
| `4deefc8` 的**提交信息** | **不可改写**（重写历史才有解，本批不重写历史）⇒ **只在台账更正**：§12 第 8 行与本节；DR-73 报告 §12 明确写"该错误陈述仍存在于 `git log` 中，权威更正以本节记述为准" | 仍留在 `git log`，已标注 |

### 4.3 先红（P4）与转绿

```
# P4 植入：把 godot-dev.md 的**现行** bullet 改回 "…no ground past `x ≈ 3800` — the flag was correct and the level was not."
$ cargo test --offline --test interaction_contract the_godot_dev_skill_retracts_the_impassable_level_claim
test the_godot_dev_skill_retracts_the_impassable_level_claim ... FAILED
thread '…' panicked at tests\interaction_contract.rs:277:9:
the old wording may only survive marked as superseded and called false; this paragraph still stands
as a claim:
- **The player can walk there.** Design the level against the jump you actually …
test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 4 filtered out   EXIT=101
```

**这里踩到并修掉了一个真陷阱**（诚实披露，见 §9.3）：该测试最初用 `skill.split("\n\n")` 找段落，
而**交付的技能是 CRLF 文档**（本机 checkout），`"\r\n\r\n"` 里根本不含 `"\n\n"` ⇒ 整份文件被当成
**一个**段落，"现行 bullet 的假话"与"标注块里的 superseded 引用"被混在一起，断言**恒真**
（P4 第一次植入没打红）。修法：先 `replace("\r\n","\n").replace('\r',"\n")` 再切段，并把这个原因
写进注释。修好后 P4 立刻打红（上）。

---

## 5. ④⑤⑥⑦ 的落点与红→绿

### ④ max x 引用错（minor）

- 事实：整轮最大值 **`455.999572753906`**（跳跃窗口的恒定 x）；DR-73 报告与 T10 验收写 `448.666`
  （`move_right_release` 的末值），**少报 7.33 px**。
- 该数字**没有进入任何生成式输出**（它只是散文引用），所以处置是"更正引用 + 把它变成**从冻结样本计算**"：
  - 新夹具 `interaction_position_samples_smoke_t10.json`（四个窗口的逐帧 x + 目标几何）由派生命令产出；
  - 新测试 `tests/dr76_payload_shapes.rs::the_frozen_rounds_maximum_player_x_is_derived_from_the_samples`
    **遍历 160 个冻结浮点求 max**，断言 `455.999572753906`，并显式 `assert_ne!` 448.666 不回归；
  - `TASK-DR73-REPORT.md` 与 `TASK-SMOKE-T10-ACCEPTANCE.md` 各加**勘误块**（见 §4.2 与 §5.5）。
- **先红（P6）**：

```
# P6 植入：把期望值改回 448.666
$ cargo test --offline --test dr76_payload_shapes the_frozen_rounds_maximum_player_x_is_derived_from_the_samples
assertion `left == right` failed: the whole-round maximum player x, as the frozen samples carry it …
  left: 455.999572753906
 right: 448.666
test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 4 filtered out   EXIT=101
```

### ⑤ "包装脚本不存在"为假（minor）

- 事实（自产）：`git ls-files | grep run_round` → `.spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/scripts/run_round.ps1`；
  `sed -n 14p` → `"ROUND_EXIT=$ec"`（正是 T10A-4 引用的那一行）。DR-73 只查了**仓根** `scripts/`。
- 更正：`TASK-DR73-REPORT.md` §10 第 5 条后插入 `⚠ DR-76 更正`（原文保留、标注 superseded），
  并把**正确论证**写清：第三处读数无法被源码钉住，不是因为脚本不存在，而是因为**那一行从未随轮次工件
  冻结入库**（`round/console.txt` 只有 13 行 hoh 自己的 stdout，没有 `ROUND_EXIT`，因为包装脚本把它打到
  外层控制台而外层未留证）。携带项 (b) 的必要性不变。
- 该条是**文本更正**，没有对应可执行测试（它是关于树的事实陈述）；本报告给出可重跑的只读命令作为证据。
  为免"又是空的树断言"，DR-76 把它写进 DR-73 报告 §12 的第 3 行，与 A5 的判词一一对应。

### ⑥ sidecar 测试仍空转（minor）

- 实测空转程度（自产，比验收者说的更宽）：**DR-73 的六对 (marker, leaked) 里只有
  `HOH_MODEL_API_KEY=` 出现在 sidecar**（2 行），其余**五对从未执行**：

```
$ for t in HOH_ARTIFACT_DIR= PATH= HOH_GAME_ROUTE= HOH_HOH_BIN= HOH_ITERATION= HOH_MODEL_API_KEY=; \
    do printf "%s -> %s\n" "$t" "$(grep -c -- "$t" <sidecar>)"; done
HOH_ARTIFACT_DIR= -> 0      PATH= -> 0            HOH_GAME_ROUTE= -> 0
HOH_HOH_BIN= -> 0           HOH_ITERATION= -> 0   HOH_MODEL_API_KEY= -> 2
```

- 修法：**判据改为从原件自己的字节派生**——`assignment_names(original)` 抽出原件真正携带的
  `HOH_*= ` 名字（`HOH_GAME_ROUTE` / `HOH_HOH_BIN` / `HOH_ITERATION` / `HOH_MODEL_API_KEY`），
  然后断言 "sidecar 里每一次该赋值的取值都必须以 `<redacted` 开头"，并**断言 `inspected > 0`**
  （绿态下实测 inspected = 2，即检查**真的执行了**）；同时把 A6 点名的两个空转名
  （`HOH_ARTIFACT_DIR=`、`PATH=`）作为"原件里根本没有"的**事实**钉住，防止再写回空转表。
- **先红（P5，把"整值替换"改成"复制"）**：

```
$ cargo test --offline --test round_artifacts_sidecar
test the_sidecar_carries_no_environment_value_and_no_user_name ... FAILED
test the_sidecar_is_generated_and_the_original_is_untouched ... FAILED
thread '…' panicked at tests\round_artifacts_sidecar.rs:257:13:
the recorded value of `HOH_GAME_ROUTE=` survived the sidecar: `F:` in "'it-hof-rs\\…HOH_GAME_ROUTE=F:\\…"
thread '…' panicked at tests\round_artifacts_sidecar.rs:165:5:
assertion `left == right` failed: every recorded occurrence must be replaced by the marker, not copied
  left: 0   right: 2
test result: FAILED. 0 passed; 2 failed; 0 ignored; 0 measured; 0 filtered out   EXIT=101
```

### ⑦ 引用漂移（info）

| 原文 | 更正 | 落点 |
|---|---|---|
| `src/runtime/secrets.rs:222` | **`:223`**（`b'\n' \| b'\r'` 分支所在行，自核） | DR-73 报告 §3 植入表第 1 行 + §12 第 4 行 |
| `src/cli_impl.rs:798` | **`:803`**（`write_process_exit_code(...)` 调用所在行，自核） | 同上（植入表第 4 行） |
| "13 项（9 M + 4 ??）" | **14 条路径（9 M + 5 A）** | DR-73 报告 §3 回退自证块内加两行更正注释 + §12 第 5 行 |

### 5.5 T10 验收的引用更正（**披露：这是一次对历史验收记录的加性编辑**）

`TASK-SMOKE-T10-ACCEPTANCE.md` 的正文**逐字未动**（那是当时的真实读数，改写会破坏历史记录），
只在文件头部（结构化 JSON 块**之外**）追加一个 `⚠ DR-76 勘误` 引用块，写明：
`448.666` 应读作 `455.999572753906`、差 7.33 px、不影响任何裁定，以及该数字现在由哪个测试从冻结样本计算。
==> 如需完全禁止编辑历史验收，可只 revert 该文件的本次改动；本报告其余结论不依赖它
（先红/绿的门与夹具都不读它）。

---

## 6. 非空洞性：7 处受控植入（全部逐字节回退）

方法：仓外备份 `…\Temp\dr76\bak2\` → 最小植入 → **先清 `target/debug/.fingerprint/hof-rs-*`** →
跑**对应**测试取红 → `cp` 回退 → `cmp`（对仓外备份）+ `git hash-object == rev-parse HEAD:<path>` +
`git status --porcelain -uall` 空。

| # | 植入 | 落点 | 红输出（逐字要点） | 回退 |
|---|---|---|---|---|
| P1 | 候选必须带 `text` 成员（= DR-73 行为） | `src/adapter/godot.rs` `hud_label_candidates` | `the real tree shape must not make the counter unreadable … candidates = []; COIN_COUNTER_UNREADABLE … WIN_DRIVEN` `0 passed; 1 failed` exit 101 | `cmp` OK；blob `ff086baf…` == HEAD |
| P2a | `INTERACTION_MAX_BATCHES = 1` | `src/adapter/godot.rs` | `the drive budget (1 batches = 60 frames) must cover the specification's longest traversal (120 s = 7200 frames)` `0 passed; 1 failed` exit 101 | `cmp` OK；blob `ff086baf…` == HEAD |
| P2b | 同上（行为面） | 同上 | 绿测变红：`WIN_UNREACHED_WITHIN_BUDGET … coverage_shortfall_px=Some(6120.0)` `0 passed; 1 failed` exit 101 | 同 P2a 的 `cp` 一并回退 |
| P3 | 预算耗尽分支改发 `WIN_UNREACHABLE_GEOMETRICALLY` | `src/adapter/godot.rs` 判定分支 | `a goal beyond the budget must be a coverage verdict …` `0 passed; 1 failed` exit 101 | `cmp` OK；blob `ff086baf…` == HEAD |
| P4 | 现行 bullet 改回 "no ground past `x ≈ 3800`" | `src/prompts/skills/godot-dev.md` 3b | `the old wording may only survive marked as superseded and called false; this paragraph still stands as a claim:` `0 passed; 1 failed` exit 101 | `cmp` OK；blob `7d862ce6…` == HEAD |
| P5 | `sidecar_line` 整值替换 → 复制 | `tests/round_artifacts_sidecar.rs` | `the recorded value of \`HOH_GAME_ROUTE=\` survived the sidecar: \`F:\`` + `every recorded occurrence must be replaced by the marker, not copied`（left 0 right 2）`0 passed; 2 failed` exit 101 | `cmp` OK；blob `36095f58…` == HEAD（sidecar 与原件同时回退，sidecar blob `6a7b16e5…` == HEAD） |
| P6 | 期望值改回 `448.666` | `tests/dr76_payload_shapes.rs` | `left: 455.999572753906 / right: 448.666` `0 passed; 1 failed` exit 101 | `cmp` OK；blob `11646a7f…` == HEAD |
| P7 | 给冻结夹具的 Coins 格**加回** `"text":"Coins: 3"` | `tests/fixtures/dr76/scene_tree_smoke_t10.json` | 三条红：`scene_tree_smoke_t10.json no longer matches the derivation`（sha 不等）+ `` `/root/Main/HUD/Coins`: the real engine sends exactly name/path/type on a Label `` （left `["name","path","text","type"]`）+ 候选扫描 | `cmp` OK；blob `aff9b960…` == HEAD；且 `cmp` 对冻结源件仍逐字节相同 |

**回退核对的最终一次（全表，真实输出）**：

```
$ python scripts/verify_revert.py
src/adapter/godot.rs: cmp=OK hash-object=ff086baf… HEAD=ff086baf… OK
src/prompts/skills/godot-dev.md: cmp=OK hash-object=7d862ce6… HEAD=7d862ce6… OK
tests/interaction_contract.rs: cmp=OK hash-object=be6e42f9… HEAD=be6e42f9… OK
tests/round_artifacts_sidecar.rs: cmp=OK hash-object=36095f58… HEAD=36095f58… OK
tests/dr76_payload_shapes.rs: cmp=OK hash-object=11646a7f… HEAD=11646a7f… OK
.spec/…/redaction_defect.redacted.txt: cmp=OK hash-object=6a7b16e5… HEAD=6a7b16e5… OK
.spec/…/redaction_defect.txt: cmp=OK hash-object=b304a3d2… HEAD=b304a3d2… OK
tests/fixtures/dr76/scene_tree_smoke_t10.json: cmp=OK hash-object=aff9b960… HEAD=aff9b960… OK
git status --porcelain -uall = ''
VERIFY OK
```

> **顺序诚实说明**：本批的"先红"不是"先写测试再写实现"的时间顺序，而是**实现写完后、用
> "恢复 DR-73 行为"的植入证明测试真的因缺该行为而红**（P1/P3/P4/P6 是"恢复旧行为"，P2 是"改坏常量"，
> P5 是"把替换改成复制"，P7 是"把夹具改回 DR-73 的形状"）。每次都已**先清 fingerprint** 再取值。
> 这一点必须写出来，不能把植入叫成 red-first。**唯一真正的 red-first 是 P4 的第一版**：
> 它当场暴露了本子代理自己写的一条**恒真断言**（CRLF 段落切分，见 §4.3），修好后才红。

---

## 7. 禁区自查（真实输出）

```
$ python scripts/digest_runs.py
smoke-t6:  files=135 digest=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03 HIT
smoke-t7:  files=115 digest=6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7 HIT
smoke-t8:  files=358 digest=c347bd637ab481b1ec357cbb534c1330bad18cfab85c113038fa0878e6b3d3f5 HIT
smoke-t9:  files=83  digest=541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d HIT
smoke-t10: files=232 digest=9ba72fbd83528ec7166b791f8659320ff8b1eba5a913a28bf2ec8d5f2e0963ad HIT
```

口径与 DR-73 验收 §G6 相同（小写、正斜杠、仓相对路径 + TAB + 十进制字节数 + TAB + sha256；条目
**序数**排序；`\n` 连接无尾换行；对 UTF-8 取 sha256）。`smoke-t6` 命中验收给出的**完整** digest，
即本批的自证点。以上在**门跑完之后**重算，仍全部命中。另：

```
$ find runs -newermt '2026-10-01 00:00' | wc -l                    → 0
$ find .workspace/mario -newermt '2026-10-01 00:00' | wc -l        → 0
$ diff -r -x .hoh -x .godot .workspace/mario runs/smoke-t10/iter-1/candidate ; echo $?
（无输出）0
$ # 17 个工程文件逐个 sha256（project.godot / scenes/main.tscn / scripts/*.gd + *.uid / README.md）
SAME ×17   （例：scenes/main.tscn 42c525f39ac05b6ddee040a1e51a450ab5cc362bdc05d1114cfbfcc73bd48553
            scripts/coin.gd  b310d631e54d2e3b2c3bca1c518f391d2ab070303b68816330913d1437801fe6）
$ sha256sum .spec/hof-rs/PRD-mario.md
4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a    （与 DR-73 验收记录一致）
$ git -C godot-mcp/godot rev-parse HEAD        → fc63af77c33368c4a1bb839c95d19750554f63a3
$ git -C godot-mcp/godot status --porcelain -uall | wc -l   → 0
$ git diff --name-only 4e0b760..HEAD -- godot-mcp | wc -l   → 0
$ git diff --stat 4e0b760..HEAD -- Cargo.toml Cargo.lock | wc -l → 0     （无新依赖）
$ git diff --name-only 4e0b760..HEAD | grep -c DECISIONS   → 0           （DECISIONS 零编辑）
$ git rev-list --left-right --count origin/master...master → 0	4        （本地领先 4，**未 push**；
                                                       本报告自身提交后为 5——这是自指数字，以 `git log` 为准）
$ git diff --name-status 4e0b760..HEAD | grep -cE '^[DR]'  → 0           （无删除、无重命名）
$ git diff --name-status 4e0b760..HEAD | wc -l              → 15          （14 + 本报告自身；自指，以 git 为准）
$ git status --porcelain -uall | wc -l                     → 0           （仓内无临时物）
$ git ls-files | grep -E '(\.bak$|\.tmp$|~$|^tmp_)' | wc -l → 0
$ git ls-files '%DST%' → 7 个路径逐个 hash-object == HEAD:<path>（OK ×7，DR-73 事故未复发／未再碰）
```

- **`.workspace/mario/**` 零字节写入**：17 个工程文件 sha256 与冻结候选**全同**，`diff -r`（排除
  运行期角色视图 `.hoh`/缓存 `.godot`）**无差异**；`find -newermt` = 0。
- **`runs/**` 零写入（含临时文件）**：五条摘要 + 文件数全部命中；`find -newermt` = 0；
  派生脚本只以 `rb` 打开冻结件、只写到 `tests/fixtures/dr76/`。
- **`cargo test` 只读 `runs/**`？** 否——测试**不读** `runs/**`（新夹具已入库），所以套件不依赖
  运行轮次目录是否存在。
- **未 push**：闸门未触发（本批不推送）。

---

## 8. 遗留风险与未验证项（严格区分实测 / 推断）

**实测（有原始输出）**

1. 门：`cargo test --offline` exit 0、**533/0/7**、58 binaries、`--list` 540、`cargo fmt --check` 0；
   双修订解析**测试名 REMOVED=0**、`#[ignore]` 7→7；95 个跟踪 `.rs` 逐文件 touch；清 fingerprint 后重编。
2. ① 真机形状：10/40（payload×Label）**零 `text` 键**；新测试在真形状上读到计数；P1 打红。
3. ② 预算钉（常量 + 行为两条）与 **覆盖 vs 几何** 的区分；P2/P3 打红。
4. ③ 交付技能与源码注释已撤回；文档测试钉住；P4 打红（并暴露 CRLF 段落切分的恒真断言）。
5. ④ 由冻结样本计算得 `455.999572753906`；P6 打红。⑤ wrapper 存在于仓内且第 14 行一致；⑥ 派生式
   非空转检查（inspected=2）与 P5 打红；⑦ 三处引用更正。
6. 7 处植入各自打红、逐字节回退（`cmp` + `hash-object == HEAD` + `status` 空）。
7. 五条 `runs/**` 摘要命中；mario 17 文件与冻结件相同；PRD sha 未变；嵌套引擎 `fc63af77…` + porcelain 0；
   无新依赖；未 push；仓内无临时物。
8. `tests/fixtures/dr76/**` 加了 `-text` 行尾钉（提交 blob 与冻结源件同为 CRLF/707 B）。

**推断（不得当作已测）**

1. **（高把握）** 新窗口在真机上能读到 `Coins:` 计数——依据是**冻结的** `running_game_get_node_properties`
   回包形状 + 真机场景树形状；但**没有**跑真机。
2. **（中）** 130 批足以覆盖规格允许的最长关卡——依据是 F17 的 120 s 与实测 3.6667 px/帧；真机上的
   采样/读 flag 延迟未测。
3. **（中）** `WIN_UNREACHABLE_GEOMETRICALLY` 的门槛（2 批无进展）在真机上不会误报——只在夹具上测过。
4. **（中）** 交互窗口对后续电池步骤/Tester 的扰动（130 s 的输入保持）——**未测**（无引擎）。

**未闭合（应回上游/回设计）**

1. **E3 是否 met**：只有真机能定，本批**不声称**。
2. **`smoke-t10` "扫过而不拾取"的运行时机制**：与 DR-73 一样**未指认**（离线、不许启 Godot）。
3. **真机轮**：按 D288 的队列，DR-76 通过后才是真机轮；本批不跑。

---

## 9. 诚实披露

1. **我没有跑真机、没有启 Godot、没有联网、没有调任何模型端点、没有触端口。**
2. **我没有手工写游戏**：`.workspace/mario/**` 零字节写入（17 文件逐字节同）；也**没有**动
   `PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`。`DECISIONS.md` 的对应记录（D288 的更正）**本批未写**，
   因为任务书明令不得修改该文件；更正台账落在 `.spec/hof-rs/tasks/TASK-DR73-REPORT.md` §12。
3. **我修掉了自己写的一条恒真断言**（P4 第一次植入**没有**打红）：`interaction_contract` 的段落检查
   用 `split("\n\n")` 切 **CRLF** 技能文档 ⇒ 整份文件一个段落 ⇒ 假话与 superseded 引用混在一起 ⇒ 恒真。
   这与 A1（夹具比现实更宽导致假绿）**同一族**，我把它写进 §4.3 与本条，因为它是本批最有价值的
   自我反例。修好后 P4 打红。
4. **"先红"的顺序被改写为植入取证**（§6 末尾已说明）：除 P4 第一版外，红都是"恢复旧行为"取得的。
   我不把它叫 red-first。
5. **我对 `TASK-SMOKE-T10-ACCEPTANCE.md` 做了一次加性编辑**（头部勘误块，正文与 JSON 块未动）。
   这是一条**历史验收记录**；若上游认为不应触碰，revert 该文件即可，本批结论不依赖它（见 §5.5）。
6. **我把 `TASK-DR73-REPORT.md` 改了**（它自己写着"本报告写完后不再修改"）。这是任务书 ③/④ 的直接要求
   （"从所有可改文本中撤回/更正该说法，保留被取代的措辞并标注"）；我采用的正是"原文保留 + 逐处
   `⚠ DR-76 更正` 标注 + §12 台账"，并在 §12 开头把"打破一次不再修改的承诺及其范围"写在明处。
7. **`4deefc8` 的提交信息不可改写**：我没有重写历史；该错误陈述**仍在 `git log` 里**，
   权威更正只在 DR-73 报告 §12 与本报告（`git log --format=%B 4deefc8` 可复核原文仍带旧句）。
8. **未使用 `rm -rf` 删任何路径；未由未展开变量构造路径**；清 fingerprint 用带父目录断言的脚本；
   所有分析与备份在仓外 `…\Temp\dr76\`。
9. **本报告在写完后不再修改。** 机器可读块（§0）我用栅栏感知脚本按 D279 的机械规则自检：

```
$ python fences.py .spec/hof-rs/tasks/TASK-DR76-REPORT.md
json-fenced blocks = 1 ; json.loads failures = 0 ; all fenced blocks = 19
keys = criteria, defects_remaining, gate, head_implementation_commit,
       machine_readable_block_check, risks, task, unverified, verdict
verdict = pass_with_residual_risk ; criteria = 11 ; risks = 4 ; unverified = 5
```

10. **我没有声称判据(3)（E3）已 met**：本批只把"可观测"从"看错"修回"能看"，并让"够不到"不再冒充
    "不可达"。是否 met **只有真机能定**。
