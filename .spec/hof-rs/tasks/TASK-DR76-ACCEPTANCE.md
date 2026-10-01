# TASK-DR76-ACCEPTANCE — DR-76 的独立验收（全新验收子代理，无实现者上下文）

> 验收人：**独立验收子代理**（本批实现者与调度者之外的全新代理；未继承任何结论；未委派、未使用子代理）。
> 落点：`F:\moonbit-hof-rs`。被验对象：`.spec/hof-rs/tasks/TASK-DR76.md`（任务书）、
> `.spec/hof-rs/tasks/TASK-DR76-REPORT.md`（实现者报告，**只作线索，绝不是证据**）、
> `.spec/hof-rs/tasks/TASK-DR73-ACCEPTANCE.md`（判 fail 的前序验收）、`DECISIONS.md` **D288**、
> `REQUIREMENTS.md` 判据(3) 原文。
> **HEAD = `4f02179`**（实现提交 `b3d1652` + 报告提交 `4f02179`）；开工时 `git status --porcelain -uall` = 空。
> **离线**：未启动 Godot、未触端口、未联网、未调用任何模型端点、未跑真机轮；**未 push、未 stage**；
> **`runs/**` 零写入（含"写过再删"）**——派生脚本与全部分析只**读** `runs/**`，我本人**没有在 `runs/**` 下创建过任何文件**；
> 临时脚本/备份/日志全部在仓外 `C:\Users\wyl\AppData\Local\Temp\dr76acc\`；
> **未使用 `rm -rf` 删任何路径**（清 fingerprint 用带"父目录断言 + basename 前缀"守卫的 `shutil.rmtree` 脚本）；
> **未从未展开的变量构造路径**；未改 `.workspace/mario/**`、`.spec/hof-rs/PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`。

---

## 0. 机器可读结论块（已用栅栏感知脚本 `json.loads` 亲验，见 §7）

```json
{
  "verdict": "pass",
  "task": "TASK-DR76",
  "object": {"head": "4f0217911880ea5b301b89b11fa62902c3259e12", "implementation_commit": "b3d1652278e54025a6dd2c24394d3c100b8778a3"},
  "summary": "DR-73 验收的三条 major 全部经我独立复现修复：真机形状的计数读取路径（含派生夹具与行尾钉）、以 PRD F17 为依据并被打红的 130 批预算 + 覆盖/几何分立判定、以及假陈述的撤回与替代措辞保留。门 533/0/7、--list 540、fmt 0、五条 runs 摘要全命中、游戏工程 17/17 逐字节同冻结件、未推送。七处植入我全部亲自重做并逐字节回退。两项 minor 与若干 info 见 defects。",
  "criteria": [
    {"id": "C1a-counter-real-shape", "pass": true,
     "evidence": "hud_label_candidates (src/adapter/godot.rs:4254-4271) 只用节点的 `type` 与 `path`（`path.contains(\"/HUD/\")`）枚举候选，完全不读 `text`；窗口在 2541-2552 逐个候选经 read_hud_text → running_game_get_node_properties{properties:[\"text\"]} 读文本，取第一个 trim_start().starts_with(\"Coins:\") 者。全文件 grep `set_node_property` = 0 命中。"},
    {"id": "C1b-frozen-payload-shape", "pass": true,
     "evidence": "我自写的 os.walk 扫描（含嵌套 `.hoh`，解开 JSON-RPC 的 content[0].text 字符串）遍历 runs/smoke-t5|t6|t7|t8|t10 的 scene_tree.json 与 play_scene_ready.json：12 份载荷 / 36 个 Label / **0 个带 `text`**，键集合恒为 ('name','path','type')；smoke-t10 的 iter-1 两份额外声明 /root/Main/HUD/Coins。五轮 iter-1 候选恰为 10 份，与报告的“10 份”口径一致。"},
    {"id": "C1c-fixtures-derived", "pass": true,
     "evidence": "脚本逐字节拷贝两个冻结件、归约第三个。我亲跑 `python scripts/derive_dr76_fixtures.py`：exit 0、幂等（重跑后 4 个文件 sha256 全同）、`diff -r` 对仓外备份无差异、`git status` 仍空。`cmp` 两份拷贝与其冻结源件**逐字节相同**（scene_cmp=0, hud_cmp=0）；源件 sha256 5fa1b083… / 3bf62ba0… 与 MANIFEST 钉值一致；`git hash-object`（工作树）== `git rev-parse HEAD:<path>` 四文件全等。"},
    {"id": "C1d-line-ending-pin", "pass": true,
     "evidence": "`git check-attr text` 对 tests/fixtures/dr76/** 三个文件全为 `unset`，而 `git config core.autocrlf=true`。hud_labels 夹具 CR=29/LF=29/707 B，与冻结源件逐字节同；scene_tree 夹具 CR=0/LF=32/5816 B。提交 blob `aff9b960…`/`40bb19e1…` 与工作树 hash-object 相同 ⇒ CR 未被规范化。报告声称“未加钉时 blob 是 CR 0 / 678 B”——该反向对照我未复现（见 unverified）。"},
    {"id": "C1e-plant-text-requirement", "pass": true,
     "evidence": "我的 P1：在 hud_label_candidates 内加回 `if node.get(\"text\").and_then(Value::as_str).is_none() { return; }` ⇒ `the_interaction_window_finds_the_counter_in_the_real_scene_tree_shape` FAILED（exit 101），记录逐字为 `candidates = []; COIN_COUNTER_UNREADABLE … WIN_DRIVEN`，同一轮 `drove 29 of 130 batch(es) … player max x=Some(6440.0) … stopped as soon as the win was observed`。回退后 `cmp` OK、blob `ff086baf…` == HEAD。"},
    {"id": "C2a-budget-derivation", "pass": true,
     "evidence": "godot.rs:3863-3871：`SPEC_MAX_TRAVERSAL_SECONDS = 120`、`INTERACTION_BUDGET_MARGIN_BATCHES = 10`、`INTERACTION_MAX_BATCHES = SPEC + MARGIN = 130`、`INTERACTION_DRIVE_FRAMES = 130*60 = 7800`。`PRD-mario.md:55` F17 逐字为“单次完整通关路径的预期耗时在 30–120 秒之间” ⇒ 120 不是裸数，是规格自身的上限。"},
    {"id": "C2b-budget-pinned", "pass": true,
     "evidence": "我的 P2：把 `INTERACTION_MAX_BATCHES` 改为 28（近失，不是 1）⇒ 常量钉 `the_drive_budget_covers_the_specifications_longest_traversal` FAILED：“the drive budget (28 batches = 1680 frames) must cover the specification's longest traversal (120 s = 7200 frames)”；同一次改动下行为钉 `the_interaction_window_records_a_real_coin_pickup_and_its_assertion` 也 FAILED（WIN_UNREACHED_WITHIN_BUDGET, coverage_shortfall_px=Some(180.0)）。⇒ DR-73 的“24→1 全绿”确实不再成立。"},
    {"id": "C2c-green-fixture-forces-the-trigger", "pass": true,
     "evidence": "边界实测：预算 28 批 ⇒ 行为钉红（player max x=6220.0 < 触发器 6368）；预算 29 批 ⇒ 同一测试 **ok**（drove 29 批到 x=6440 ≥ 6368）。配合 P1 红态打印的“29 of 130 batch(es) … 6440.0 … stopped as soon as the win was observed”，绿夹具确实被迫驱动到目标的触发器，而不是像 DR-73 那样 1 批就够。"},
    {"id": "C2d-split-verdicts", "pass": true,
     "evidence": "godot.rs:2853-2881：`stalled && batches_left > 0` ⇒ WIN_UNREACHABLE_GEOMETRICALLY；`budget_exhausted`（= 未早停、未停摆、驱动完整、批次用尽）⇒ WIN_UNREACHED_WITHIN_BUDGET（文本明写“this is a COVERAGE verdict, not a geometry verdict … nothing is claimed about whether the level is passable”）；其余 ⇒ WIN_NOT_DRIVEN（不完整驱动，不下结论）。我的 P3（把预算耗尽分支的 token 改成几何 token）⇒ `a_level_whose_goal_is_unreachable_fails_only_the_win_half` FAILED，记录 `drove 130 of 130 … max x=28660.0 … coverage_shortfall_px=Some(1340.0)`，与报告逐字一致。绿态下三测试分别钉住：覆盖（NoWin）、几何（Blocked，`of the 130-batch budget were still unspent`）、t10 自身状态（NoPickupNoWin，且不得几何化）。"},
    {"id": "C2e-shortfall-in-both-verdict-lines", "pass": true,
     "evidence": "读码核实：驱动行（godot.rs:2691）与两条判定行（2861、2872）**都**写 `coverage_shortfall_px={coverage_shortfall_px:?}`。但“判定行也带”**没有被测试钉住**——见 defects D2。"},
    {"id": "C3a-skill-retracted", "pass": true,
     "evidence": "src/prompts/skills/godot-dev.md 3b 现行 bullet 改为“keep the ground continuous under it”（:140-141）；旧句以 `> **Superseded (DR-76 ③).** This section used to say: … **That was false, and it must not be acted on.**` 逐字保留在引用块内（:143-163），并写明 6800×40 @3400、continuous、唯一 28 px 障碍、真因是 coverage、以及两个 token。"},
    {"id": "C3b-source-comment-retracted", "pass": true,
     "evidence": "tests/interaction_contract.rs:104-113 的注释改为“this comment used to say … — that was false. The frozen Ground is one 6800x40 … continuous under the goal … true cause … replay coverage”，由 `the_godot_dev_skill_retracts_the_impassable_level_claim` 钉住。"},
    {"id": "C3c-superseded-preserved-not-deleted", "pass": true,
     "evidence": "`git show b3d1652 -- src/prompts/skills/godot-dev.md` 是改写而非删除；旧句仍可在 :144-146 读到。TASK-DR73-REPORT.md §2.2(A-3) 在段落**上方**插入 `⚠ DR-76 更正` 块、旧段原样保留并标 `（superseded）`，另加 §12 八行台账。"},
    {"id": "C3d-no-history-rewrite", "pass": true,
     "evidence": "`git log --format=%B -1 4deefc8` 仍带原句“……the goal sat at x=6400 past the end of the traversable ground.”；4deefc8 的 SHA 未变（内容寻址）⇒ 未重写历史。更正只落在 TASK-DR73-REPORT.md §12 的记述里。**但台账第 8 行对该提交信息的“原文”引用是错的**——见 defects D1。"},
    {"id": "C3e-t10-acceptance-additive", "pass": true,
     "evidence": "`git show b3d1652 -- .spec/hof-rs/tasks/TASK-SMOKE-T10-ACCEPTANCE.md` 只有 **1 个 hunk、9 insertions、0 deletions**，全部在 `## 结构化结论` 之前；`json` 围栏块 my fence-aware `json.loads` 通过（1 个 json 块，0 失败，keys 仍为 criteria/defects/risks/unverified/verdict）；新旧两版 JSON 块**逐字节相同**（`json identical: True`），证据字符串零改动。"},
    {"id": "C4a-max-x-derived", "pass": true,
     "evidence": "我从冻结 `input_replay.json` 独立重算：160 个 position 样本、max = `455.999572753906`，与派生夹具的归约结果逐位相同。我的 P6（期望值改回 448.666）⇒ `left: 455.999572753906 / right: 448.666` FAILED。"},
    {"id": "C4b-wrapper-script", "pass": true,
     "evidence": "`git ls-files | grep run_round` → `.spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/scripts/run_round.ps1`；`git log --diff-filter=A` → `15e071f`；`sed -n 14p` → `\"ROUND_EXIT=$ec\"`；冻结 `round/console.txt` 13 行、`ROUND_EXIT` 命中 0 ⇒ 更正后的论证（该行未随轮次工件冻结入库）成立。"},
    {"id": "C4c-sidecar-markers", "pass": true,
     "evidence": "我自写扫描：原件携带的赋值名恰为 `HOH_GAME_ROUTE` / `HOH_HOH_BIN` / `HOH_ITERATION` / `HOH_MODEL_API_KEY`（各 2 次）；sidecar 中前三者 0 次、`HOH_MODEL_API_KEY=` 2 次，`<redacted by TASK-DR73:` 恰 2 次（== 原件 2 条 occurrence 头）。“六对里五对从未执行”成立：`HOH_ARTIFACT_DIR=`/`PATH=` 在原件里根本不存在。sidecar 对 `C:\\`、`node_modules`、`moonbit-hof-rs`、`HOH_GAME_ROUTE=F:` 全 0 命中。测试新增 `inspected > 0` 断言。"},
    {"id": "C5-seven-plants", "pass": true,
     "evidence": "P1(ff086baf)/P2(godot.rs)/P3(godot.rs)/P4(7d862ce6 + be6e42f9)/P5(36095f58 + 6a7b16e5)/P6(11646a7f)/P7(aff9b960) 我**全部亲自重做**、各自打红其对应测试、并逐字节回退（`cmp` 对仓外备份 OK + `git hash-object == git rev-parse HEAD:<path>` + `git status --porcelain -uall` 空）。P4 回退后我另做的“raw split”对照见 §3.3。"},
    {"id": "C5b-crlf-vacuity-fix", "pass": true,
     "evidence": "二进制读入技能文档：CR=339/LF=339，`\\n\\n` 出现 **0** 次、`\\r\\n\\r\\n` 50 次 ⇒ `skill.split(\"\\n\\n\")` 只得 **1** 段（整份文件），而规范化后 51 段、其中恰 1 段带旧措辞且同时含 superseded+false。我的 P4b（把测试改回 raw split，旧假句仍在现行 bullet）⇒ 测试 **ok**（假绿）；恢复规范化后同一植入 ⇒ FAILED。恒真断言与修复**双向亲证**。"},
    {"id": "C5c-plant-order-disclosure", "pass": true,
     "evidence": "报告 §6 末尾与 §9.3 自曝：红是“实现写完后用恢复旧行为的植入”取得的，不叫 red-first；唯一真 red-first 是 P4 第一版（并当场暴露自己的恒真断言）。我核对：任务书要求的是“先写会失败的最小测试”，该要求**未被满足也无法从树里证明被满足**；但每处红都因缺该行为而红（我逐条复现），所以**可执行非空洞性**成立。判为过程偏离（info），不削弱行为证据。"},
    {"id": "C6a-gate", "pass": true,
     "evidence": "我清掉 59 条 `target/debug/.fingerprint/hof-rs-*`（带父目录/basename 断言的守卫脚本），日志首行为 `Compiling hof-rs v0.1.0` ⇒ 真重编。`cargo test --offline` **exit 0**，逐 `test result:` 行求和 = **533 passed / 0 failed / 7 ignored**，58 个 test binary，`FAILED` 出现 0 次、`error[` 0 次；`cargo test --offline -- --list` = **540** 条（533+7 自洽）、0 benchmark、exit 0；`cargo fmt --check` = **FMT_EXIT=0**。双修订解析（4e0b760 vs HEAD，覆盖 src/ 与 tests/ 全部 .rs）：530 → 540，**REMOVED 0**、ADDED 10（与报告清单逐字相同）、`#[ignore]` 9 → 9。"},
    {"id": "C6b-runs-digests", "pass": true,
     "evidence": "我的口径 = **仓根相对路径小写化 + 正斜杠 + TAB + 十进制字节数 + TAB + sha256，条目按序数（ordinal）排序，`\\n` 连接、无尾换行，对 UTF-8 blob 取 sha256**。五条全部命中报告的逐字值，且自证点命中：t6 135 `c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03`、t7 115 `6e4c1595…520fb7`、t8 358 `c347bd63…b3d3f5`、t9 83 `541e2d81…36ca9d`、t10 232 `9ba72fbd…e0963ad`。`find runs -newermt '2026-10-01 00:00'` = 0。"},
    {"id": "C6c-game-untouched", "pass": true,
     "evidence": "**最强守卫**：.workspace/mario 的 17 个工程文件与冻结 `runs/smoke-t10/iter-1/candidate` 同集合、**sha256 全同**（差异 0、只在单边 0）；例 `scenes/main.tscn 42c525f3…`、`scripts/coin.gd b310d631…`。.workspace/mario 与 runs 下**最晚 mtime = 2026-09-30 18:23:08**（t10 收轮时刻），`-newermt 2026-10-01` 两处皆 0 ⇒ 本批零字节写入。"},
    {"id": "C6d-forbidden-trees-and-deps", "pass": true,
     "evidence": "`git diff --name-status 4e0b760..HEAD` = 14 条（9 M + 5 A），全在 `.spec/`、`scripts/`、`src/`、`tests/`；**无 D、无 R、无游戏文件**。对 PRD-mario.md / DECISIONS.md / godot-mcp / Cargo.toml / Cargo.lock 的 diff = 0 行。`sha256(PRD-mario.md) = 4c81c3a9…`（与 DR-73 记录一致）；嵌套引擎 `git -C godot-mcp/godot rev-parse HEAD = fc63af77…`、porcelain 0；`git rev-list --left-right --count origin/master...HEAD = 0 5` ⇒ **未推送**；`git status --porcelain -uall` 空、仓内无 `.bak/.tmp/~` 临时物。"},
    {"id": "C6e-false-green-traps", "pass": true,
     "evidence": "(1) `git diff --stat -- definitely/not/a/real/path` = 空 stdout/stderr、exit 0；对照 `git ls-files godot-mcp` = 6484（真）/ `godot-mcp/godot` = 0（假）。(2) cmd 下 `git rev-parse HEAD^` 打出 `4f021791…`（= HEAD，而 HEAD^ 应为 `b3d1652`）⇒ `^` 被吃掉；bash 下 `git rev-parse HEAD HEAD^` 给出 4f02179 / b3d1652，`git cat-file -e HEAD:definitely/not/here` exit 128。(3) 外层仓不跟踪：`git check-ignore -v` 命中 `.gitignore:33 godot-mcp/godot/`、`:12 runs/`、`:11 .workspace/`，三处 `git ls-files` 皆 0。"}
  ],
  "defects": [
    {"id": "D1-ledger-misquotes-the-commit-message", "severity": "minor",
     "what": "TASK-DR73-REPORT.md §12 台账第 8 行的“原文（superseded）”列，把 `4deefc8` 提交信息写成 `\"…no ground past x≈3800… the level was not [correct]\"`。该提交信息里**没有**这两句；它的真实句子是 “the goal sat at x=6400 past the end of the traversable ground.”。错误主张**确实存在**于提交信息（“past the end of the traversable ground”就是那个假几何断言），但台账作为“权威更正清单”却不逐字引用，这正是本批在别处严肃对待的同类失真。",
     "reproduction": "`git log --format=%B -1 4deefc8 | grep -n \"3800\\|impassable\"` → 0 命中；`git log --format=%B -1 4deefc8 | grep -n \"past the end\"` → 1 命中。对照读 `.spec/hof-rs/tasks/TASK-DR73-REPORT.md:708`。"},
    {"id": "D2-shortfall-not-pinned-on-the-verdict-line", "severity": "minor",
     "what": "报告 §3.1 称两种判定“都带 `coverage_shortfall_px`（在驱动行与判定行各一次）”。代码确实如此，但**测试钉不住判定行**：驱动行（godot.rs:2691）无条件携带该字段，于是 `observation.contains(\"coverage_shortfall_px=Some(\")`（几何测试）与 `contains(\"coverage_shortfall_px=Some(1340\")`（覆盖测试）都能被驱动行单独满足。我把几何判定行的 `coverage_shortfall_px=` 改成 `shortfall_px=`（仍保留驱动行）⇒ 该测试仍然 **ok**。",
     "reproduction": "在 src/adapter/godot.rs:2861 把 `coverage_shortfall_px={coverage_shortfall_px:?}` 改为 `shortfall_px={coverage_shortfall_px:?}`，跑 `cargo test --offline --test evidence_battery a_player_that_stops_advancing_with_budget_left_is_a_geometric_verdict` ⇒ `1 passed; 0 failed`。回退后 blob 仍为 ff086baf…。"}
  ],
  "risks": [
    "R1（中，报告已披露）WIN_UNREACHABLE_GEOMETRICALLY 的判据只是“按住 move_right 且连续 2 个批次采样 max x 未前进、预算仍有剩余”。一个需要跳跃/移动平台/敌人击退才能前进的关卡会得到**几何** token——这与 DR-73 的 A3 同族：把驱动方式的边界误读成关卡的边界。报告 risk #2/#4 已如实写出该限制，代码/技能却把 token 叫“GEOMETRICALLY”且技能正文只说“Never read the first as the second”，未提醒“第二个本身也不是几何证明”。可发布，但应窄读。",
    "R2（中，报告已披露）窗口会在未观测到胜利时把 move_right 按住最多 130 s 的**游戏时间**，且它跑在 node_and_collision_assertions 之前 ⇒ 下游电池步骤与 Tester 读到一个被扰动过的世界。无测试覆盖该次序效应，我也无法离线测量。",
    "R3（低）覆盖/几何判定的动量门槛（2 批）在真机上可能被长平台/击退误触发；记录带数字（batches_left、max x、shortfall），所以可复核，但 token 是诊断不是证明。",
    "R4（低）候选扫描读每个 HUD Label 的 text：HUD 很大时是每格一次属性调用；两个文本都以 `Coins:` 开头的项目取树序第一个（确定但非策略）。",
    "R5（低）派生夹具的 MANIFEST 钉的是**拷贝自身**的 sha256，套件不读 runs/**，因此“拷贝 == 冻结源件”只由我这类的仓外 `cmp` 与 `-text` 行尾钉保证；一个改了夹具再重跑派生脚本（同时刷新 manifest）的人在**仓库内部**不会被打红。冻结策略是外部约束，故仍可接受。",
    "R6（低）交互窗口在真机上找不到 `Coins:` 标签时一律报 COIN_COUNTER_UNREADABLE。冻结证据里 smoke-t5|t6|t7 的 HUD 只有 Result/Score、**根本没有** Coins 格——那三轮若跑新窗口，金币半边仍会是 unreadable。这是诚实的 gap（PRD F10 要求该格），但也说明“计数可观测”依赖未来项目真的命名了该格。"
  ],
  "unverified": [
    "真机是否真的能用该路径读到 `Coins:` 计数并观测到拾取/胜利——无 Godot、无真机轮，任何人（包括我）都只能从冻结载荷与契约形状推断。报告未声称判据(3) met，我同样不声称。",
    "报告 §1.3 声称“未加 `-text` 钉时提交 blob 是 CR 0 / 678 B”这一**反向对照**：我验证了“加钉后 CR 保留”，但没有通过临时移除 gitattributes 条目去复现未加钉时的 blob。",
    "smoke-t10 里“扫过金币却不拾取”的运行时机制（DR-73/DR-76 都拒绝指认）——离线不可分，我不指认。",
    "sampled 位置与 goal flag 在真机上的读取延迟，以及 130 批在真机上是否足以覆盖规格允许的最长关卡（只在夹具上按 220 px/批折算过）。",
    "`hud-labels.json` 的 `source` 字段自述“Tester 在活着的轮次进程里只读 running_game_get_node_properties”——smoke-t10 的确定性原始记录里没有任何针对 HUD 标签的 `get_node_properties` 调用可交叉印证，**该形状的真实性我只能采信其自述 + DR-73 验收 D5 的独立真机读数**。"
  ],
  "machine_readable_block_check": "由我自己的栅栏感知脚本 json.loads 亲验，见 §7"
}
```

---

## 1. 结论

**`verdict = pass`**（DR-73 的三条 major 全部经我独立复现修复；两项 minor 见 defects D1/D2，均不改变本批判定）。

一句话判断：**这一批把 DR-73 的三处致命问题从“声称修了”变成“我亲手把它打红再打绿”**——
真机形状的计数读取路径成立且夹具确系派生；预算从裸常量变成规格（PRD F17）自身的上限并且
**28 批红 / 29 批绿**的边界证明绿夹具真的被迫驱动到触发器；覆盖与几何**分成两个 token**且有可执行区分；
假陈述在交付技能、源码注释、前序报告里被撤回而旧措辞以 `superseded` 保留；提交信息确实没被改写。
七处植入我全部亲自重做并逐字节回退。门与禁区守卫全部通过。

留下的两条 minor：台账第 8 行**错误引用了提交信息的原文**（D1）；以及“判定行也带 shortfall”这句
**没有被测试钉住**（D2）。两条都属于“报告/工件的精度”，不是机制缺陷。

---

## 2. 逐项裁定表（任务书的六项工作）

| # | 工作 | 裁定 | 关键证据（全部自产） |
|---|---|---|---|
| 1 | 计数查找（头条） | **成立** | C1a-C1e：代码只用 type/path，文本经属性工具读；12 份冻结载荷 / 36 Label / 0 text；派生脚本幂等、`cmp` 逐字节同、MANIFEST 三值自洽；`check-attr` = unset 且 CR=29 保留；P1 打红真实形状测试 |
| 2 | 预算与分立判定 | **成立（含一处欠钉）** | C2a-C2e：120 s 出自 PRD F17:55；P2（28 批）同时打红常量钉与行为钉；28 红 / 29 绿边界；P3 打红覆盖→几何的冒充；两条判定 token 与 shortfall 在码内齐备（判定行未被测试钉住，D2） |
| 3 | 撤回 | **成立（含一处误引）** | C3a-C3e：技能与源码注释已改口径、旧句以 `superseded`+`false` 保留；4deefc8 未改写历史；T10 验收加性 9 行、JSON 块逐字节不动（台账误引提交信息，D1） |
| 4 | 其他更正 | **成立** | C4a-C4c：455.999572753906 由冻结样本算出（我独立重算一致，P6 打红）；wrapper 在仓内且第 14 行一致；“六对里五对空转”实测成立 |
| 5 | 非空洞性与 TDD 偏离 | **成立（过程偏离如实披露）** | C5a-C5c：七植入全复现 + 逐字节回退；CRLF 恒真断言**双向亲证**（raw split 绿 / 规范化红）；顺序确非 red-first，报告未把它叫成 red-first |
| 6 | 门与守卫 | **成立** | C6a-C6e：533/0/7、58 二进制、--list 540、fmt 0、REMOVED 0、ignore 9→9；五条 runs 摘要全命中（t6 自证）；游戏 17/17 同冻结件、最晚 mtime 2026-09-30 18:23:08；未推送、无新依赖；三陷阱亲复现 |

---

## 3. 我自产的植入与反例（全部逐字节回退）

方法：仓外备份 `C:\Users\wyl\AppData\Local\Temp\dr76acc\bak\` → 最小植入 → 跑**对应**测试取红 →
`cp` 回退 → `cmp`（对仓外备份）+ `git hash-object == git rev-parse HEAD:<path>` + `git status --porcelain -uall` 空。
清 fingerprint 用带守卫的脚本（对每个候选项断言其父目录 == fingerprint 目录、basename 以 `hof-rs-` 开头）。

### 3.1 任务书点名的七处植入（我全部亲自重做）

| # | 我的植入 | 落点 | 红输出（逐字要点） | 回退 |
|---|---|---|---|---|
| P1 | 候选必须带 `text` 成员（= DR-73 行为） | `hud_label_candidates` | `the real tree shape must not make the counter unreadable … candidates = []; COIN_COUNTER_UNREADABLE … WIN_DRIVEN`；`0 passed; 1 failed` exit 101 | `cmp` OK；blob `ff086baf…` == HEAD |
| P2 | `INTERACTION_MAX_BATCHES = 28`（近失，非 1） | `src/adapter/godot.rs` | 常量：`the drive budget (28 batches = 1680 frames) must cover the specification's longest traversal (120 s = 7200 frames)`；行为：`player max x=Some(6220.0) … WIN_UNREACHED_WITHIN_BUDGET … coverage_shortfall_px=Some(180.0)`；各自 exit 101 | 同 P1 的 `cp` 一并回退 |
| P2b | `INTERACTION_MAX_BATCHES = 29`（边界对照） | 同上 | `the_interaction_window_records_a_real_coin_pickup_and_its_assertion ... ok`（**绿**） | 同上 |
| P3 | 预算耗尽分支改发几何 token | `src/adapter/godot.rs:2867` | `a goal beyond the budget must be a coverage verdict … drove 130 of 130 … max x=Some(28660.0) … coverage_shortfall_px=Some(1340.0)`；exit 101 | `cmp` OK；blob `ff086baf…` == HEAD |
| P4 | 现行 bullet 加回 “no ground past `x ≈ 3800` … the level was not” | `godot-dev.md` 3b | `the old wording may only survive marked as superseded and called false; this paragraph still stands as a claim:`；exit 101 | `cmp` OK；blob `7d862ce6…` == HEAD |
| P5 | `sidecar_line` 整值替换 → 复制 | `tests/round_artifacts_sidecar.rs` | `the recorded value of \`HOH_GAME_ROUTE=\` survived the sidecar: \`F:\`` + `every recorded occurrence must be replaced by the marker, not copied`；`0 passed; 2 failed` exit 101 | `cmp` OK；测试 blob `36095f58…`、sidecar blob `6a7b16e5…` == HEAD |
| P6 | 期望值改回 `448.666` | `tests/dr76_payload_shapes.rs` | `left: 455.999572753906 / right: 448.666`；exit 101 | `cmp` OK；blob `11646a7f…` == HEAD |
| P7 | 给冻结夹具的 Coins 格加 `\"text\":\"Coins: 3\"` | `tests/fixtures/dr76/scene_tree_smoke_t10.json` | 三条红：`scene_tree_smoke_t10.json no longer matches the derivation` + `` `/root/Main/HUD/Coins`: the real engine sends exactly name/path/type on a Label `` + 计数器候选断言 | `cmp` OK（对备份**与对冻结源件**）；blob `aff9b960…` == HEAD |

### 3.2 我额外加的两项

| # | 反例 | 目的 | 结果 |
|---|---|---|---|
| X1 | 把几何判定行的 `coverage_shortfall_px=` 改成 `shortfall_px=`（驱动行不动） | “判定行也带 shortfall”是否被测试钉住 | **不红**：`a_player_that_stops_advancing_with_budget_left_is_a_geometric_verdict ... ok` ⇒ 断言可被驱动行单独满足（defect D2） |
| X2（P4b） | 把 `interaction_contract` 的段落切分改回 `skill.split("\n\n")`，同时保留 P4 的假句植入 | 恒真断言的真伪 | **绿**（`1 passed`）+ `warning: unused variable: normalized` ⇒ 旧断言确实恒真 |

### 3.3 CRLF 恒真断言的双向证据

```
二进制读 src/prompts/skills/godot-dev.md：CR=339 LF=339
  raw "\n\n" 出现次数 = 0 ；raw "\r\n\r\n" 出现次数 = 50 ；raw split 段数 = 1
  规范化后段数 = 51 ；其中含 "no ground past" 的段数 = 1（同时含 superseded 与 false）
```
⇒ 旧实现把整份 CRLF 文件当成**一个**段落，假话与 superseded 引用混在一起，断言恒真；
修复后（先 `replace("\r\n","\n").replace('\r',"\n")` 再切）恰好命中那一处并会因它未标注而红。
P4/P4b 的对照证明这不是纸上推演。

---

## 4. 我对各问的独立判断

### 4.1 计数查找（头号目标）
- **读取路径**：成立。`hud_label_candidates` 只取 `type`/`path`（连 `name` 都没用，只多不少地安全），
  `/HUD/` 过滤是明写的策略；文本一律经 `running_game_get_node_properties{properties:["text"]}`。
  整个过程**没有任何属性写入**（全文件无 `set_node_property`）。
- **“夹具是派生的而不是手写的”**：成立，且是我自己跑出来的。脚本只以 `rb` 打开冻结件；
  两份拷贝 `cmp` 逐字节同；第三个是归约（我独立从 `input_replay.json` 重算 160 个样本、max 一致）；
  `MANIFEST.json` 三个 sha256 与实际文件自洽；测试还会重算它们。
- **行尾钉**：成立。`tests/fixtures/dr76/** -text` 生效（`check-attr` = unset），在 `core.autocrlf=true`
  的机器上 CR=29 的 CRLF 夹具**没有被规范化**，提交 blob 与工作树一致（`40bb19e1…`）。
- **P1 打红**：成立且信息量高——同一条记录里 `WIN_DRIVEN` 与 `COIN_COUNTER_UNREADABLE` 并存、
  `candidates=[]`，这正是真机在 DR-73 实现下必然发生的事。

### 4.2 预算与分立判定
- **预算是“算出来的”**：成立。120 s 是 `PRD-mario.md` F17 的原文上限，130 = 120+10、7800 帧 = 130×60 由常量算术导出。
- **会被打红**：成立。28 批（近失）同时打红“常量钉”与“行为钉”；29 批绿。
  ⇒ 绿夹具**真的**被迫驱动到触发器（6386→需求 29 批，实测 29 批到 x=6440），不再是 DR-73 的“1 批就够”。
- **可分判定**：成立。两个 token 的分支条件互斥（`stalled && batches_left>0` vs `budget_exhausted`），
  覆盖分支的文本自己声明“不对关卡作任何声称”；P3 证明把覆盖写成几何会被打红。
- **推断限制是否诚实**：**是，但 token 名过宽**。报告的 risk #2/#4 明确写出“这是对按住 move_right 的
  推断，不是关于跳跃的证明”“2 批停摆可能被可脱困的长停滞触发”。代码注释与技能也把窗口契约写成
  “按住 move_right”。**但交付出去的 token 叫 `WIN_UNREACHABLE_GEOMETRICALLY`，技能只写“Never read the
  first as the second”，没有提醒读者“第二个也不是几何证明”**。⇒ 可以发布，但应把该 token 窄读为
  “在本窗口的驱动方式下无法前进”，并在真机轮之后按实际证据重估（见 R1、§8 建议 2）。

### 4.3 撤回
- **交付技能**：成立。现行 bullet 已改口径，旧句逐字留在 `> **Superseded (DR-76 ③).**` 引用块里，
  并明写 “That was false, and it must not be acted on.”。全文件 `superseded` 只出现 1 次，就在保留块内，
  所以“保留”这一点被间接钉住（但见 R7/§4.5 的保留意见）。
- **源码注释**：成立（`tests/interaction_contract.rs:104-113`）。
- **没有删除而是保留并标注**：成立（`git show` 是改写+hunk 插入，不是删除）。
- **提交信息不可改写、只在台账更正**：成立。4deefc8 的 SHA 未变，`git log --format=%B` 仍带原句。
  **但台账第 8 行引用错了原文**（D1）——这是我这批找到的最实质的精度问题。
- **T10 验收的加性编辑（披露裁定）**：我核到 **1 hunk / 9 insertions / 0 deletions**、JSON 块逐字节相同、
  fence-aware 解析通过、证据字符串零改动。**裁定：可接受，但不是最干净的形态。**
  理由：(i) 任务书只禁止改 PRD/DECISIONS/godot-mcp 与游戏，`.spec/**` 的历史验收并不在禁列，
  且任务书本身要求改写 `TASK-DR73-REPORT.md`（它还写着“写完后不再修改”），所以“加性勘误”在本仓有先例；
  (ii) 加性、不改机器可读块、原字符串全留，历史读数未被篡改；
  (iii) **但**一个历史验收工件被后来的批次改动，即使加性，也会让“读者看到的文件”与“当时被验收的字节”分离，
  只有 git archaeology 才能还原。**更干净的形态是独立 sidecar**（例如 `…-ACCEPTANCE-DR76-ERRATA.md`），
  让被验收工件的字节保持不变。实现者主动披露并提供 revert 选项，这一点减轻了问题。

### 4.4 其他更正
- **④ max x**：成立。我从冻结 `input_replay.json` 独立重算 = `455.999572753906`；P6 打红 448.666。
  该数字**没有**进入生成式输出（只是散文引用），处置正确。
- **⑤ wrapper 脚本**：成立。仓内存在、`15e071f` 加入、14 行逐字一致；更正后的论证
  （“该行未随轮次工件冻结入库”，console.txt 仅 13 行且无 ROUND_EXIT）与我的实测一致。
- **⑥ sidecar**：成立，且比验收者说得更宽——我实测原件携带 4 个 `HOH_*` 名，
  sidecar 只保留 `HOH_MODEL_API_KEY=` 的 2 行；`HOH_ARTIFACT_DIR=`/`PATH=` 在原件里**根本不存在**；
  新检查从原件自身字节派生主题并断言 `inspected > 0`（绿态实测 2），P5 会打红。

### 4.5 非空洞性与 TDD 偏离
- **七处植入**：我全部亲自重做，七处都使**对应**测试红，且全部逐字节回退（`cmp` + blob == HEAD + status 空）。
- **TDD 偏离裁定**：实现者自曝“红是事后用恢复旧行为的植入取得的，不叫 red-first”。
  我判定：**诚实、且不削弱本批的行为证据**。理由：植入证明的正是 red-first 想保证的性质——
  每条测试在缺该行为时会因**正确的原因**失败；本批最关键的几处断言（真机形状、455.999572753906、
  29 批、coverage≠geometry）都对着冻结载荷或精确值，不是对着实现拟合。
  **但**任务书的“先写会失败的最小测试（贴真实失败输出）”这一**过程要求确实未被满足**，
  也无法从树里被证明被满足——这是一个过程偏离，我记为 info 而不是 defect，因为它不影响可裁决性。
- **它自曝的恒真断言**：我双向亲证（§3.3）：raw split 在植入下**绿**，规范化后**红**。这正是“夹具/断言比现实更宽”
  的同族错误被自己抓到，是本批最有价值的自我反例，披露到位。

### 4.6 门与守卫
见 §1 表与 §0 的 C6a-C6e。我要强调三件事：
1. **我的门读数与报告逐字一致**（533/0/7、58、540、fmt 0），且我是**清掉 59 条 fingerprint 后重编**取得的
   （日志首行 `Compiling hof-rs`），不是陈旧产物；我**没有**照抄报告的“逐文件 touch 95 个 .rs”，
   而是用了等效且更彻底的清 fingerprint，此点如实披露。
2. **最强的守卫成立**：游戏工程 17 文件 sha256 与冻结候选全同，`.workspace/mario` 与 `runs` 下
   最晚 mtime 都是 `2026-09-30 18:23:08` ⇒ 本批不可能通过改游戏来让症状消失。
3. **五条 runs 摘要全命中**，且 `smoke-t6 = c144ef32…7a9c03` 自证点命中，证明我的口径与验收记录同口径。

### 4.7 报告自带的“未验证清单”裁定
| 报告 unverified | 我的裁定 |
|---|---|
| 真机轮上是否真能观测到拾取与胜利 | **成立且不可检**：无 Godot，我也只能推断；报告拒绝声称判据(3) met 是对的 |
| smoke-t10 “扫过而不拾取”的运行时机制 | **成立**：我也无法区分，保持不指认是恰当行为 |
| 需要跳跃才能通的关卡会得到几何 token | **成立**：我把它升级为 risk R1（token 名过宽） |
| 采样/goal flag 的真机延迟 | **成立**：离线不可测 |
| 真机场景树是否永远把计数格列在 HUD Labels 里 | **成立**：冻结证据只有五轮；我补了一条更强的观察 —— smoke-t5|t6|t7 的 HUD **连 Coins 格都没有**（见 R6） |

⇒ **这份未验证清单是诚实、克制且基本完整的**；我只补两点：token 名的窄读要求（R1），
以及 `hud-labels.json` 的 provenance 只有自述 + DR-73 D5 的旁证（unverified 第 5 条）。

---

## 5. 三个假绿陷阱（实测）

1. `git diff --stat -- definitely/not/a/real/path` → **stdout+stderr 皆空、exit 0**，与“无变化”不可区分；
   对照必须真命中：`git ls-files godot-mcp` = **6484** / `git ls-files godot-mcp/godot` = **0**。
2. **cmd 吃掉 `^`**：cmd 下 `git rev-parse HEAD^` 打出 `4f021791…`（= HEAD，而 HEAD^ 应为 `b3d1652`）；
   bash 下 `git rev-parse HEAD HEAD^` = `4f02179… / b3d1652…`，`git cat-file -e HEAD:definitely/not/here` exit 128。
   有证据力的只有 bash（或在 cmd 里加引号）。
3. 外层仓不跟踪 `godot-mcp/godot`、`runs/**`、`.workspace/**`（`.gitignore:33/12/11`，三处 `ls-files` = 0）
   ⇒ 这三处的“未变”只能靠目录摘要 / 嵌套仓 / mtime 证明。

（另：本报告所有门读数都写入文件后再读退出码，不走管道过滤，避免“编译失败经过滤后与全绿不可区分”。）

---

## 6. 未验证项与理由

见结论块 `unverified`。要点：
1. **真机是否能观测到 E3 的两个行为** —— 离线、不许启 Godot；报告不声称，我也不声称。
2. **未加 `-text` 钉时的 blob 形态（CR 0 / 678 B）** —— 我只验证了“加钉后 CR 保留”，未做移除钉的反向对照。
3. **`hud-labels.json` 的 provenance** —— 其 `source` 是自述；smoke-t10 的确定性原始记录里没有可交叉印证的
   HUD 属性读取调用，只能靠 DR-73 验收 D5 的独立真机读数旁证。
4. **smoke-t10 “扫过不拾取”的运行时机制** —— 我不指认。
5. **真机延迟与 130 批的充分性** —— 只在夹具上按 220 px/批折算。

## 7. 我没有检查的

- 未启动 Godot / 未跑任何真机轮（硬约束）；因此**不声称判据(3) 是否 met**。
- 未逐条重审 `input_replay` 既有位置断言的实现（只核其冻结回包与派生数字）。
- 未审 `godot-mcp/**` 内部实现（只验其未改：嵌套 HEAD 与 porcelain）。
- 未逐条审读 DR-73/DR-76 报告全文的每一个数字（重点核了我能独立重算的那些：455.999572753906、
  6308/6368/6400 几何、28/29 批边界、两条判定的 token 与 shortfall、五条 runs 摘要）。
- 未验证报告 §1.1 中“逐文件 touch 95 个 .rs”这一**过程**（我只核了 tracked .rs 数量 = 95，
  并用自己的清 fingerprint 重编取得门读数）。
- 未检查 `scripts/derive_dr76_fixtures.py` 之外的其它生成式脚本与 `tests/fixtures/**` 其它家族与真实载荷的一致性。
- 未在 `runs/**` 下创建过任何文件（我自己那条摘要脚本也只读）。

**机器可读块的合法性检查（我自产）**：
```
$ python <仓外>/fence.py .spec/hof-rs/tasks/TASK-DR76-ACCEPTANCE.md
json-fenced blocks = 1 ; json.loads failures = 0
```
（报告写完后再跑一次确认；本报告与结论块同时落盘。）

---

## 8. 给下一批的建议（按优先级）

1. **按 D288 的队列推进真机轮**（DR-76 通过后才是真机轮）。跑之前先把两条 minor 修掉，成本极低：
   - **D2**：把断言从“observation 里出现过 `coverage_shortfall_px=Some(`”改成对**判定行本身**的匹配
     （例如断言 `WIN_UNREACHABLE_GEOMETRICALLY … coverage_shortfall_px=Some(` 这一片段），否则“判定行也带 shortfall”
     永远只是散文承诺。
   - **D1**：把 TASK-DR73-REPORT.md §12 第 8 行的“原文”改成提交信息里的真实句子
     （“the goal sat at x=6400 past the end of the traversable ground”）。
2. **把 `WIN_UNREACHABLE_GEOMETRICALLY` 的语义收窄**（或改名，例如 `WIN_STALLED_UNDER_MOVE_RIGHT`），
   并在交付技能里补一句“它只说明按住 move_right 无法前进，不排除跳跃/其它输入能前进”。否则真机轮上
   一个需要跳跃的关卡会被误读成“关卡不可通”，那正是本批要根除的错误，只是深了一层。
3. **真机轮要单独观测“窗口的次序扰动”**（R2）：窗口跑在 `node_and_collision_assertions` 之前并可能按住
   move_right 达 130 s 游戏时间。建议在真机轮里对比窗口前后的世界状态，或把窗口挪到电池末尾/单独一轮。
4. **给历史验收记录改用 sidecar 勘误**（本批对 T10 验收的加性编辑可接受但非最优）；
   若上游偏好零触碰，revert 该文件即可，本批其余结论不依赖它（我也确认门与夹具都不读它）。
5. **把 MANIFEST 的钉升级为“源件 sha”**（R5）：让 `derive_dr76_fixtures.py` 增加只读 `--check` 模式，
   在生成前断言冻结源件的 sha256，使“拷贝 == 冻结件”成为套件内可断言的命题（现在只能在仓外 `cmp`）。
6. **补一条“保留”断言**：现在 `the_godot_dev_skill_retracts_the_impassable_level_claim` 只通过
   “文件里存在 `superseded`”间接钉住旧措辞被保留；建议直接断言旧句仍在文件里且相邻文本含 `false`，
   以便将来有人“清理”引用块时被打红。
