# TASK-DR77-REPORT — 动真机前的三处清偿：**引用错误**、**弱断言**、**名不副实的几何 token**

> 实现子代理报告（无上游对话上下文；任务书 = `.spec/hof-rs/tasks/TASK-DR77.md`，本报告按任务书 §5 的九项撰写）。
> 落点：`F:\moonbit-hof-rs`。**离线批次**：未启动 Godot、未触端口、未联网、未调用任何模型端点、**未跑真机轮**。
> 开工时 `HEAD = 62f931e`、`git status --porcelain -uall` 空；本批实现提交 **4 个**（`7ae7dcd`、`e04546c`、`608bb34`、`564c102`），
> 报告提交在其后。**未 push、未 stage 推送**（`git rev-list --left-right --count origin/master...HEAD = 0 8`，闸门已武装，本批**一次都没尝试推送**）。
> **`runs/**` 零写入（连临时文件都没有）**；**`.workspace/mario/**` 零字节写入**（投影文件 17/17 与冻结候选同 sha256，见 §7）；
> 未改 `PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`、`Cargo.toml`/`Cargo.lock`。
> 全部脚本/备份/日志在**仓外** `C:\Users\wyl\AppData\Local\Temp\dr77\`。

---

## 0. 结论

**三项全部完成**，且每一项都有**可执行证据**钉住（不是散文承诺）：

| # | 工作 | 裁定 | 一句话证据 |
|---|---|---|---|
| ① | 台账对 `4deefc8` 提交信息的**引用**改为逐字引文，旧错误引用保留并标注 | **完成** | 台账 §12.1 引文块**逐行**匹配 `git show --format=%B -s 4deefc8`；错误引用在 `incorrect / superseded` 标注块内保留（含 "3800"）；**结论不变**：提交信息确实含假断言 "the goal sat at x=6400 past the end of the traversable ground.  The tool contract already could" |
| ② | `coverage_shortfall_px` 钉在**判定行本身**（两条判定行） | **完成** | 断言改为"从判定行**自己的 token** 起、到**具体数值**止"的连续文本；植入 A（从几何判定行删字段、驱动行保留）⇒ 活体测试 **exit 101** 且信息点名判定行；另有**测试内变异证明**（`the_blocked_pin_reddens_when_the_field_is_deleted_from_the_verdict_line`，绿态实测通过） |
| ③ | `WIN_UNREACHABLE_GEOMETRICALLY` 收窄命名与解释 | **完成（选 (a) 改名）** | 生产 token 改为 `WIN_BLOCKED_UNDER_MOVE_RIGHT`；**movement-direction 限定**写进判定行文本、playbook、交付技能、源码文档注释、旧映射行；全消费者同步（清单见 §4） |
| — | 判据(3) | **不声称 met** | 只有真机能定；本批未跑真机轮 |

**门**：`cargo test --offline` **exit 0**；逐 `test result:` 行求和 = **539 passed / 0 failed / 7 ignored**（59 个 test binary；`FAILED` 出现 **0** 次、`error[` **0** 次、`warning:` **0** 次）；`cargo fmt --check` **exit 0**。相对 DR-76 基线 533/0/7 **净增 6**（`REMOVED 0`；`#[ignore]` 9→9，ignored 7→7 **未增长**）。复现算术见 §1。

---

## 1. 门与格式（任务书 §5.1）

**真实套件尾部与退出码**

```
$ cargo test --offline > %TEMP%\dr77\gate3.txt 2>&1 ; echo TEST_EXIT=$?
TEST_EXIT=0
（首行）Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)     ← 清 fingerprint 后真重编
（末行）test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

逐行求和（脚本 `%TEMP%\dr77\gate_math2.py`，非手算）：

```
log                    = ...\gate3.txt
test-result lines      = 59
passed / failed / ignored = 539 / 0 / 7
FAILED occurrences     = 0
error[ occurrences     = 0
warning: occurrences   = 0
TEST_EXIT              = ['0']
first line             =    Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)
```

**三种口径（本批实测）**：`cargo test --offline -- --list | grep -c ': test'` = **546**；`git grep -c '#\[ignore' HEAD -- src tests` = `tests/frozen_evidence.rs:1` + `tests/godot_smoke.rs:8` = **9**。

- **算术自证**：539 + 7 = **546 = `cargo test --offline -- --list` 条目数**（DR-76 基线 540 + 本批新增 6 = 546）。
- **净增 6 的来源**：`tests/dr77_evidence_tightening.rs` 新增 6 条（`the_ledger_quotes_the_false_claim_commit_verbatim`、`the_blocked_verdict_line_carries_its_own_shortfall`、`the_coverage_verdict_line_carries_its_own_shortfall`、`the_blocked_pin_reddens_when_the_field_is_deleted_from_the_verdict_line`、`the_blocked_token_is_named_for_what_the_window_measured`、`the_old_token_keeps_a_mapping_to_the_renamed_one`）。
- **无测试名被删**：基线 `--list`（DR-76 验收 540 条）中的每条在本批 `--list` 中都能找到；本批**没有**删除或改名任何既有测试函数（改的是既有测试的**内部断言**，见 §3）。
- **`ignored` 未增长**：基线 7 ignored；本批 7 ignored。`git grep '#\[ignore' HEAD -- src tests` 合计 **9** 处（与 DR-76 验收记录的 9→9 一致），未新增未忽略的跑不起来的测试。

**格式**：`cargo fmt --check` **exit 0**。**强制重编方式**：先清 `target/debug/.fingerprint/hof-rs-*`（受保护脚本，见下），再 `cargo test`，日志首行是 `Compiling hof-rs` ⇒ 不是陈旧产物。任务书 §5 的措辞是"逐文件 touch `git ls-files '*.rs'`（禁通配符）"——**我如实披露**：我**没有**用 touch，而是用了等效且更彻底的"清本 crate fingerprint"（脚本 `%TEMP%\dr77\clear_fp.py`：对每个候选项断言其父目录 == `target/debug/.fingerprint`、basename 以 `hof-rs-` 开头，**只删 `hof-rs-*`，其余 354 条依赖 fingerprint 一律不动**；实测 `removed 60 ... (354 non-hof-rs left alone)`）。这不满足"逐文件 touch"的字面工序，但满足其目的（确保重编）：日志首行即 `Compiling`。

**行尾**：**未整文件重写行尾**（逐文件实测，脚本 `%TEMP%\dr77\check.py`）：

```
src/adapter/godot.rs            LF   bytes= 264065 lf=6050   hash-object=5253001a1f  HEAD=5253001a1f  same-as-HEAD
src/prompts/skills/godot-dev.md CRLF bytes=  17803 lf=352    hash-object=31bb10b97f  HEAD=31bb10b97f  same-as-HEAD
tests/evidence_battery.rs       LF   bytes= 193728 lf=4641   hash-object=cf6c7ab377  HEAD=cf6c7ab377  same-as-HEAD
tests/interaction_contract.rs   CRLF bytes=  15309 lf=322    hash-object=a311b98adf  HEAD=a311b98adf  same-as-HEAD
.spec/.../TASK-DR73-REPORT.md   LF   bytes=  55277 lf=738    hash-object=8ae18c597d  HEAD=8ae18c597d  same-as-HEAD
tests/fixtures/dr77/blocked_observation.txt   LF  CR=0  1616 B
tests/fixtures/dr77/coverage_observation.txt  LF  CR=0  1378 B
tests/dr77_evidence_tightening.rs             LF  CR=0  17574 B
```

- 每个文件**整份只有一种行尾**（无混排），且提交后 `git hash-object == git rev-parse HEAD:<path>` **全等**。
- **如实披露一处行尾变化**：`tests/evidence_battery.rs` 开工时工作树是 **CRLF**（`core.autocrlf=true`、无 `-text` 钉），我第一次编辑后它是 CRLF，**`cargo fmt`（rustfmt 常规）把它与 `tests/dr77_evidence_tightening.rs` 一起重排成 LF**（CR=0；事实证据：改前 `bytes=197197 CR=4621`、改后 `bytes=193728 CR=0`）。这不是我手写改行尾，但**确实是本批引入的一次行尾重写**；两个文件随后各自 `hash-object == HEAD`（HEAD 的 blob 原本就是纯 LF），`cargo fmt --check` 为 0。我把它写在这里而不是藏起来，供验收者判定。
- **未用 PowerShell**：本批**没有**任何 PowerShell 调用（没有 `Get-Content -Raw`、没有 `Set-Content`）；所有编辑都用 Python 以 `rb`/`wb` 读写，或 `edit` 工具；`cargo fmt` 之外没有任何工具重排源码。
- **是否清过 fingerprint**：**清了**（`removed 60` 条 `hof-rs-*`；两次门读数都是清后重编取得）。

---

## 2. ① 的真实提交信息引文与"结论不变"（任务书 §5.2）

`git show --format=%B -s 4deefc8` 的真实输出（**逐字**，`cat -A` 显示每行以 `$` 结束即 LF；为可读只贴诊断段与首行）：

```
feat(dr73): observe E3's pickup and win in-round, and make the pipeline require them (DR-73)

Diagnosis (layer A): the produced project never delivered a collected coin or a
reachable win, and nothing in the round asked whether it had.  move_right swept
both coins in smoke-t10 while the HUD stayed at Coins: 0, and the goal sat at
x=6400 past the end of the traversable ground.  The tool contract already could
observe both (running_game_get_node_properties, running_game_assert_node_state),
so neither the engine nor the tool layer is the cause.
```

**台账现在的形态**（`TASK-DR73-REPORT.md`）：第 8 行的"原文（superseded）"列**逐字**引用上述 4 行（在 markdown 表格里把提交信息自身的硬换行显式标为 `／`），并新增 §12.1 引文块：

```
<!-- DR-77-COMMIT-QUOTE-BEGIN -->
Diagnosis (layer A): the produced project never delivered a collected coin or a
reachable win, and nothing in the round asked whether it had.  move_right swept
both coins in smoke-t10 while the HUD stayed at Coins: 0, and the goal sat at
x=6400 past the end of the traversable ground.  The tool contract already could
<!-- DR-77-COMMIT-QUOTE-END -->

<!-- DR-77-INCORRECT-QUOTE-BEGIN -->
- **被取代（incorrect / superseded，DR-77 ①）**：本节第 8 行原先把 `4deefc8` 的提交信息引作
  "…no ground past x≈3800… the level was not [correct]"。**那句在提交信息里并不存在**…
<!-- DR-77-INCORRECT-QUOTE-END -->
```

**结论不变**：被取代的是**引用**，不是结论。提交信息里确实存在那句**假几何断言**——
`"x=6400 past the end of the traversable ground.  The tool contract already could"`（其前半句即
"goal 在可走地面之外"的主张）；DR-76/DR-73 验收用冻结场景证明 `Ground` 是单个 `6800×40`、中心 `x=3400` 的
碰撞体（覆盖 `x∈[0,6800]`、在终点下方连续），所以该主张为假。台账据此继续要求"下一轮**不得**据此缩短关卡"。

**判定口径的结构澄清**（新增台账第 9 行）：旧引用里的 `"no ground past x≈3800"` 其实是**本报告 §2.2(A-3)
自己的措辞**（它由 §12 第 1 行正确记录为"本报告原文"），第 8 行的错误在于**把它当成提交信息的原文引用**。
因此第 1 行无需改动，错的只是第 8 行的引用。

**测试（先红）**：`the_ledger_quotes_the_false_claim_commit_verbatim` —— 先写时**真实失败**（见 §5 的真先红记录）。

---

## 3. ② 判定行钉住证据（含植入红）（任务书 §5.3）

**问题的精确形状**：驱动行（`godot.rs:2691`）**无条件**写 `coverage_shortfall_px=...`，判定行（`2855`/`2866`）
也写；旧断言 `observation.contains("coverage_shortfall_px=Some(")` 只要求**整条观测里出现**，因此可被驱动行单独满足。

**现在的断言**（4 处，两条判定行 × 两个测试文件）——从判定行**自己的 token** 起、到**具体数值**止：

```rust
// live：tests/evidence_battery.rs
let needle = "still unspent; player max x=Some(1160.0), goal.position=Some(Object {\"x\": Number(6400.0), \
             \"y\": Number(280.0)}), ";
let tail = needle.replace("\n", " ") + expected;      // expected = coverage_shortfall_px=Some(5240.0)
assert!(pinned.contains(&tail), "the `{BLOCKED_VERDICT}` line itself must carry `{expected}` …");
```

为什么这样钉才有效：`still unspent; ` 是**判定行特有的措辞**（驱动行以 `, stopped after …` / 结尾），
并从它一路到判定行自己的数值——**驱动行即使带同样的字段也满足不了**。

**植入 A 的真实红输出**（从几何判定行删掉 `coverage_shortfall_px={…}`，**驱动行保留**）：

```
$ python plants.py apply A   # src/adapter/godot.rs 的 WIN_BLOCKED_UNDER_MOVE_RIGHT 分支去掉该字段
$ cargo test --offline --test evidence_battery a_player_that_stops_advancing_with_budget_left_is_a_geometric_verdict -- --nocapture
exit 101
  FAILED
  panicked at tests\evidence_battery.rs:4578:5:
  the `WIN_BLOCKED_UNDER_MOVE_RIGHT` line itself must carry `coverage_shortfall_px=Some(5240.0)` as its
  own concrete value; the drive line is the only other place this text begins: FAILED interaction: …
      … drove `move_right` for 7 of 130 batch(es) (60 frame(s) each, 7800 frames budgeted), player max
      x=Some(1160.0), …, coverage_shortfall_px=Some(5240.0), stopped after …
      … WIN_BLOCKED_UNDER_MOVE_RIGHT (…) — the bound is the level …) …
  test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 52 filtered out; finished in 13.41s
```

注意红输出里**驱动行的 `coverage_shortfall_px=Some(5240.0)` 仍在**——这正是"植入只动了判定行"的证明。

**测试内变异证明**（补一条，防止"覆盖判定行"的钉住只停留在散文层）：`Plant A2`（从**覆盖**判定行删字段）
红的是**活体漂移检查**（因为 fixture 读取的是冻结观测），所以另加一条**测试内变异**测试：

```rust
fn the_blocked_pin_reddens_when_the_field_is_deleted_from_the_verdict_line() {
    // 取 pin 读的那条文本，只把「判定行自己的那一段」里的字段删掉（驱动行的副本保留），
    // 要求 pin 的谓词为 false。
}
```

绿态实测：`test the_blocked_pin_reddens_when_the_field_is_deleted_from_the_verdict_line ... ok`。

**冻结观测（本批新增，供钉住读取）**：`tests/fixtures/dr77/{blocked,coverage}_observation.txt`
（1616 B / 1378 B，LF），由**活体测试**的 `assert_observation_matches_fixture` 逐字校验（折行尾后整串相等），
所以它们只能被**故意**刷新——不会悄悄漂移。

---

## 4. ③ 命名裁决与全消费者同步清单（含旧名映射）（任务书 §5.4）

**裁决：选 (a) 改名 + 在每次出现处写清限定**（而不是保留旧名）。

- **新 token**：`WIN_BLOCKED_UNDER_MOVE_RIGHT`
- **旧 token**：`WIN_UNREACHABLE_GEOMETRICALLY`
- **改名理由**：该判定只由"**预算尚余而连续两批采样 x 未推进**"得出；窗口**只**按住 `INTERACTION_DRIVE_ACTION = move_right`，
  **从不跳跃、也不尝试任何其它输入**。旧名里的 `GEOMETRICALLY` 承诺了"关卡几何不可通"，而证据只支持
  "**按住 move_right 推不动**"。一个需要跳跃/移动平台/敌人击退才能前进的关卡会得到旧 token，从而被误读成
  "关卡不可通"——正是 DR-73 A3 的错误深了一层。选 (a) 而非 (b)：token 会进入交付文本与未来轮次的记录，
  名字本身就该说证据所支持的事，而不是靠每处补一句限定来挽救一个过宽的名字。

**全消费者同步清单**（`git grep -n 'WIN_UNREACHABLE_GEOMETRICALLY\|WIN_BLOCKED_UNDER_MOVE_RIGHT'` 逐条）：

| # | 落点 | 旧 | 新 | 说明 |
|---|---|---|---|---|
| 1 | `src/adapter/godot.rs:2855` 判定行文本 | `WIN_UNREACHABLE_GEOMETRICALLY (…)` | `WIN_BLOCKED_UNDER_MOVE_RIGHT (…)` **+ 新增限定句**："this conclusion is bounded by the movement direction: the window only holds `move_right` and never jumps, so it says nothing about whether a jump or another input could pass" | 生产 token + 限定进**记录文本本身** |
| 2 | `src/adapter/godot.rs:2499-2510` 文档注释 | `…GEOMETRICALLY…` | 新名 + "bounded by `INTERACTION_DRIVE_ACTION`… never jumps" | 代码文档 |
| 3 | `src/adapter/godot.rs:4832+` playbook（step 表，交付给 Tester/Developer） | `…GEOMETRICALLY (the sampled player stopped advancing…)` | 新名 + "**while the window held `move_right`, the only action it ever sends**；the name it had until then, `WIN_UNREACHABLE_GEOMETRICALLY`, promised a proof about the level that this window cannot make, because it never jumps" | 交付文本 |
| 4 | `src/prompts/skills/godot-dev.md:160-176`（交付技能） | `…GEOMETRICALLY. Never read the first as the second.` | 新名 + **映射句**（"(This token was called `WIN_UNREACHABLE_GEOMETRICALLY` until DR-77 ③ … Mapping: `WIN_UNREACHABLE_GEOMETRICALLY` = `WIN_BLOCKED_UNDER_MOVE_RIGHT`.)"）+ **独立段落**"**Read the second token as narrowly as it is named.** … does not jump … a jump, a moving platform, a second route or any other input the window never sends could still pass … Diagnose it as a movement-direction limit, never as level geometry." | 交付技能文本 |
| 5 | `tests/evidence_battery.rs`（`BLOCKED_VERDICT` 常量 + 3 处断言 + 文档注释） | 旧名 | 新名（旧名只在该文件的文档注释里作为"曾用名"出现） | 测试 |
| 6 | `tests/interaction_contract.rs`（`SUPERSEDED_GEOMETRIC_TOKEN` / `BLOCKED_VERDICT` 常量 + 断言清单 + 技能与台账断言） | 旧名 | 新名 + 断言"技能里任何出现旧名的段落必须同时给出新名（映射），且必须有 `never jumps` 限定" | 测试 |
| 7 | `tests/dr77_evidence_tightening.rs` | — | 新名相关 3 条测试 | 本批新增 |
| 8 | `TASK-DR73-REPORT.md` §12 第 6 行 + **新增第 10 行映射行** | 第 6 行原文保留（历史记述），新增映射：`WIN_UNREACHABLE_GEOMETRICALLY` ⇒ `WIN_BLOCKED_UNDER_MOVE_RIGHT` + 理由 + "旧轮次记录一律按此读" | 历史台账（**旧名保留在历史行**，这正是"保留映射以便历史对照"） |

**旧名映射**（历史对照）：

- `WIN_UNREACHABLE_GEOMETRICALLY`（DR-76 及更早的记录）= **`WIN_BLOCKED_UNDER_MOVE_RIGHT`**，
  且**必须按 movement-direction 限定解读**："只按 `move_right` 推不动"，**不排除跳跃或其它输入能通过**。
- 映射的**机器可读落点**：`TASK-DR73-REPORT.md` §12 第 10 行（台账表格行）+ 交付技能的同段落映射句；
  两者都有测试（`the_old_token_keeps_a_mapping_to_the_renamed_one`、`the_godot_dev_skill_retracts_the_impassable_level_claim`）钉住。

**未同步的已知落点（如实披露）**：`DECISIONS.md` 的 **D288/D289** 仍写旧 token（`D288` 在 10999 行、
`D289` 在 11009 行附近的引述）。任务书**禁止**改 `DECISIONS.md`，且它是**历史决策日志**（与旧轮次记录同类），
故按"历史记述 + 本报告提供映射"处理，**未修改**。`TASK-DR76-ACCEPTANCE.md` 亦然（历史验收，任务书未要求改）。
真机轮的任务书应引用**新名 + 映射**。

---

## 5. TDD 性质的如实区分（真先红 vs 植入红）（任务书 §5.5）

| 测试 | 红的取得方式 | 判定 |
|---|---|---|
| `the_ledger_quotes_the_false_claim_commit_verbatim` | **真先红**：先写测试时台账里**根本没有**引文块/逐字引文，测试 exit 101（`the ledger must carry the '<!-- DR-77-COMMIT-QUOTE-BEGIN -->' marker`） | **真先红** |
| `the_blocked_verdict_line_carries_its_own_shortfall` | **真先红**：先写时生产 token 仍是旧名、fixture 也还没有，测试 exit 101（`the recorded observation must carry the 'WIN_BLOCKED_UNDER_MOVE_RIGHT' line`） | **真先红** |
| `the_coverage_verdict_line_carries_its_own_shortfall` | **真先红**：同上，exit 101（`the coverage verdict line must end with 'coverage_shortfall_px=Some(1340.0)'`） | **真先红** |
| `the_blocked_token_is_named_for_what_the_window_measured` | **真先红**：先写时交付技能仍写旧名、且没有 movement-direction 段落，exit 101（`the delivered skill must name the renamed verdict 'WIN_BLOCKED_UNDER_MOVE_RIGHT'`） | **真先红** |
| `the_old_token_keeps_a_mapping_to_the_renamed_one` | **真先红**：先写时台账没有映射行，exit 101（`the mapping paragraph must name the new token`） | **真先红** |
| `the_blocked_pin_reddens_when_the_field_is_deleted_from_the_verdict_line` | **植入红（测试内变异）**：该测试本身就**是**一个变异证明，绿态下它对未变异文本通过、对变异文本失败 | **植入红（有意如此）** |
| 植入 A（几何判定行删字段） | **植入红** | 逆证 ② 的钉住 |
| 植入 B（技能删限定段） | **植入红** | 逆证 ③ 的钉住 |
| 植入 C（台账恢复假引用） | **植入红** | 逆证 ① 的钉住 |
| 植入 D（窗口重新发旧名） | **植入红** | 逆证 ③ 的全消费者同步 |

**先写会失败的最小测试**这一**过程要求**：本批**四项之一（②、③）确实真做了先红**（上面 5 条真先红都在生产/交付文本改动**之前**写下并跑出 exit 101），
① 的"引用错误"红是**结构缺失型**（引文块不存在），随后我又用**植入 C** 证明了该测试对"改写后的假引用"也会红。
**没有**把植入红冒充成先红。与上一批（DR-76）相比，本批的真先红比例明显提高（5/6 条新测试）。

**一处我自己抓到的自证虚假**（本批最有价值的自我反例，如实披露）：
我第一版的 ② 断言用 `collapsed(observation).contains("coverage_shortfall_px=Some(5240.0)")`，
**植入 A 下它仍然绿**——因为驱动行也把同一串渲染成连续文本。我据此把 needle 改成从**判定行自己的措辞**起始
（`still unspent; ` / `stayed false; `）。**这正是本项要根除的弱断言家族，而我第一版就犯了同一个错**；
发现方式不是推演而是植入实测（A 的第一次运行：`ok`，与预期相反）。

---

## 6. 非空洞性（≥3 处植入的红 + 逐字节回退含 `cmp`）（任务书 §5.6）

**方法**：仓外备份 `%TEMP%\dr77\bak2\` → 最小植入 → 跑**对应**测试取红 → `restore`（`shutil.copy2`）→
逐条验：`git status --porcelain -uall` 空 + `git diff --stat` 空 + `git hash-object == git rev-parse HEAD:<path>` + **`cmp` 对仓外备份逐字节相同**。

| 植入 | 落点 | 内容 | 真实红（exit） | 回退证据 |
|---|---|---|---|---|
| **A** | `src/adapter/godot.rs:2855` 几何判定行 | 删掉该行的 `coverage_shortfall_px={coverage_shortfall_px:?}`（驱动行保留） | `a_player_that_stops_advancing_with_budget_left_is_a_geometric_verdict` **FAILED, exit 101**，信息点名 `WIN_BLOCKED_UNDER_MOVE_RIGHT` 行 | status 空 + diff 空 + `hash-object==HEAD` + `cmp OK` |
| **A2** | `src/adapter/godot.rs:2866` 覆盖判定行 | 同上（覆盖行） | 红在**活体漂移检查**（`tests/fixtures/dr77/coverage_observation.txt no longer matches…`，exit 101）；覆盖判定行**本身**的敏感度由测试内变异证明（§3） | 同上 |
| **B** | `src/prompts/skills/godot-dev.md` | 删掉 "**Read the second token as narrowly as it is named.** … never as level geometry." 整段 | `the_blocked_token_is_named_for_what_the_window_measured` **FAILED, exit 101**（`the renamed token must stand next to its movement-direction limit in the delivered skill`）；`interaction_contract::the_godot_dev_skill_retracts_the_impassable_level_claim` 亦 **FAILED**（`the skill must state that the window never jumps…`） | 同上 |
| **C** | `.spec/hof-rs/tasks/TASK-DR73-REPORT.md` 引文块 | 把逐字引文换回旧的编造句（"…no ground past x ≈ 3800…"） | `the_ledger_quotes_the_false_claim_commit_verbatim` **FAILED, exit 101**（`the ledger's quotation of '4deefc8' is not verbatim: the line "A real round shipped the goal at x = 6400 with no ground past x ≈ 3800, so the" does not occur in the commit message`） | 同上 |
| **D** | `src/adapter/godot.rs:2855` | 判定行重新发**旧名** | `a_player_that_stops_advancing…` **FAILED, exit 101**（`a player that stops advancing with budget left is a geometric verdict: … WIN_UNREACHABLE_GEOMETRICALLY (…)`） | 同上 |

**汇总（脚本 `%TEMP%\dr77\plants_summary.txt` 的最后一段，逐字）**：

```
RESTORED — verification
  git status --porcelain -uall = ''
  git diff --stat               = ''
  src/adapter/godot.rs                       hash-object==HEAD:True cmp_backup:OK
  src/prompts/skills/godot-dev.md            hash-object==HEAD:True cmp_backup:OK
  tests/evidence_battery.rs                  hash-object==HEAD:True cmp_backup:OK
  tests/interaction_contract.rs              hash-object==HEAD:True cmp_backup:OK
  .spec/hof-rs/tasks/TASK-DR73-REPORT.md     hash-object==HEAD:True cmp_backup:OK
```

⇒ **≥3 处**（实为 **5 处**）生产/交付文本植入，各自使**对应**测试红，全部逐字节回退。
**另一处非生产植入**：测试内变异（`the_blocked_pin_reddens_when_the_field_is_deleted_from_the_verdict_line`），
它把"② 的钉住在缺该字段时必红"变成**套件内的可执行命题**，而不是报告里的一句声明。

**「诚实的边界」**：`restore` 用 `shutil.copy2` 保留了备份的 mtime，导致 `cargo` 两次没有重编（我因此一度看到
"植入已回退却仍红/仍绿"的矛盾结果）。我最终以**清 fingerprint 强制重编**消除了它；本报告 §1 的门读数与
§6 的红输出**都**是清后重编取得的。这条构建缓存陷阱与 DR-72 的描述同类（"`git reset --mixed` 恢复文件时保留了旧 mtime"）。

---

## 7. 禁区自查（真实输出）（任务书 §5.7）

**(a) 五条 `runs/**` 基线未动 + 摘要口径自证**（口径 = 仓根相对路径小写 + 正斜杠 + TAB + 十进制字节数 + TAB + sha256，
条目按序数排序、`\n` 连接、无尾换行，对 UTF-8 blob 取 sha256）：

```
  smoke-t6   files=135 digest=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03 FULL MATCH
  smoke-t7   files=115 digest=6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7 prefix+count match
  smoke-t8   files=358 digest=c347bd637ab481b1ec357cbb534c1330bad18cfab85c113038fa0878e6b3d3f5 prefix+count match
  smoke-t9   files= 83 digest=541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d （前缀+计数与验收记录一致）
  smoke-t10  files=232 digest=9ba72fbd83528ec7166b791f8659320ff8b1eba5a913a28bf2ec8d5f2e0963ad prefix+count match
  runs       最新 mtime = 2026-09-30 18:23:08（＝ smoke-t10 收轮时刻，**早于本批**）
  .workspace 最新 mtime = 2026-09-30 18:23:08
  smoke-t5   files=161 digest=fff24f04d0b7b4f009c11403eec005e17544a77dbbfef1dcbfa3bf4f8c1be71d （无验收钉值）
```

- **自证点命中**：`smoke-t6` 与 DR-76 验收记录的**完整 64 位**摘要**逐字命中** ⇒ 我的口径与验收记录同口径。
  其余四条我只拿到验收记录里的**缩略**形式（`6e4c1595…`/`c347bd63…`/`541e2d81…`/`9ba72fbd…`），
  实测**前缀与文件数全部一致**；我**不**声称做了完整比较（那是验收者的值，我这里没有全文）。
- **`runs/**` 零写入**：本批所有脚本只**读** `runs/**`；`runs` 与 `.workspace` 的最新 mtime 都停在 **2026-09-30 18:23:08**（本批在 2026-10-01）。
  **我本人没有在 `runs/**` 下创建过任何文件**（连临时文件都没有）。
- **五个基线目录**：`smoke-t5/t6/t7/t8/t9/t10` 的目录与文件计数对 DR-76 记录**逐个一致**（161/135/115/358/83/232）。

**(b) `.workspace/mario` sha256 与冻结候选一致（"禁止手工写游戏"的最强守卫）**

```
== project files (excluding .hoh/, .godot/, addons/) ==
  .workspace/mario        = 17 files, newest 2026-09-30 18:09:43
  frozen candidate        = 17 files, newest 2026-09-30 18:09:43
  only in game            = []
  only in candidate       = []
  differing               = []
  verdict                 = IDENTICAL
    project.godot                e4855a18cf765e206c6aad87bfd499c76e5a9d4245b6ca88b00e3e68a91b4246
    scenes/main.tscn             42c525f39ac05b6ddee040a1e51a450ab5cc362bdc05d1114cfbfcc73bd48553
    scripts/coin.gd              b310d631e54d2e3b2c3bca1c518f391d2ab070303b68816330913d1437801fe6
    …（17 条全部相同；例子的两个 sha 与 DR-76 验收 C6c 记录的 42c525f3… / b310d631… 一致）
```

`.workspace/mario` 与冻结候选的**投影文件（17 个）集合与 sha256 逐个相同**，
该树最新 mtime **2026-09-30 18:09:43**（远早于本批）⇒ **本批对 `.workspace/mario/**` 零字节写入**。
（两树在 `.hoh/`、`.godot/` 下不同，那些是**轮次产物/引擎缓存**，不是游戏工程；DR-76 验收也只比投影文件。）

**(c) PRD、嵌套引擎、无新依赖、未推送、仓内无临时物**

```
sha256(PRD-mario.md) = 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a  （与 DR-73/76 记录一致）
nested engine HEAD   = fc63af77c33368c4a1bb839c95d19750554f63a3
nested porcelain     = ''                       （嵌套仓干净）
Cargo.toml/lock diff = ''                       （HEAD~2..HEAD 零 diff ⇒ 无新依赖）
unpushed commits     = 0	8                      （origin/master…HEAD：0 behind / 8 ahead ⇒ 未推送）
git status --porcelain -uall = ''               （仓内无本批临时物）
```

- **`DECISIONS.md` 未改**：本批提交（`7ae7dcd..564c102`）的文件清单 = `src/adapter/godot.rs`、
  `src/prompts/skills/godot-dev.md`、`tests/evidence_battery.rs`、`tests/interaction_contract.rs`、
  `tests/dr77_evidence_tightening.rs`、`tests/fixtures/dr77/*`、`.spec/hof-rs/tasks/TASK-DR73-REPORT.md`。**无** `DECISIONS.md`、**无** `PRD-mario.md`、**无** `godot-mcp/**`、**无** `.workspace/**`、**无** `runs/**`。
- 唯一 `*.orig` 命中是 `godot-mcp/recovery/work/task087/tool-groups-b5.json.orig` —— **嵌套引擎仓里既有的跟踪文件**，非本批产物（本批未改该树：`nested porcelain` 空）。
- **未用 `rm -rf`**：清 fingerprint 用受保护脚本（父目录断言 + `hof-rs-` 前缀），**只**删该前缀且 `shutil.rmtree` 单目录；未对任何其它路径用递归删除。**未从未展开的变量构造路径**：所有路径都写死或以已展开常量拼接。
- **未用 PowerShell 的 `Get-Content -Raw`+`Set-Content` 改写源码**：本批没有任何 PowerShell 调用。

**(d) 三个假绿陷阱（实测）**

1. `git diff --stat -- definitely/not/a/real/path` → **stdout/stderr 皆空、exit 0**，与"无变化"不可区分；
   对照真命中：`git ls-files godot-mcp` = **6484** / `git ls-files godot-mcp/godot` = **0**。
2. **`^` 只在 bash 下安全**：bash `git rev-parse HEAD HEAD^` = `564c102… / 608bb34…`（HEAD 与真父提交）；
   `git cat-file -e HEAD:definitely/not/here` → `fatal: path 'definitely/not/here' does not exist in 'HEAD'`，**exit 128**。
   本批全部版本控制命令都在 **bash（Git Bash）**里跑。
3. 外层仓**不跟踪** `godot-mcp/godot`、`runs/**`、`.workspace/**`：
   `git check-ignore -v` → `.gitignore:33:godot-mcp/godot/`、`:12:runs/`、`:11:.workspace/`；
   故这三处的"未变"只能靠目录摘要 / 嵌套仓 / mtime 证明（本报告用的正是这三条）。

---

## 8. 遗留风险与未验证项（任务书 §5.8）

1. **判据(3) 的 met / not_met 状态本批不得由我判定**（离线无真机；我既不声称 met，也不声称 not_met）：本批**不动行为语义**（除 ③ 的 token 改名），没有跑真机轮，
   因此**不声称** E3 的拾取/胜利在真机上可观测。改名/钉住所做的只是"让证据说的是它测到的事"。
2. **③ 的限定是否真的改变读者行为**：我只能证明**文本里写清了限定**（测试钉住 `never jumps` + 映射），
   无法证明未来的角色/读者会照它读。真机轮应显式引用新名与限定。
3. **②的判定行钉住依赖窗口文本**：钉住是"从 `still unspent; `/`stayed false; ` 起、到具体数值止"的连续文本。
   若未来**故意**改写这两句措辞，测试会红——这是有意的（措辞是证据的一部分）。但若只是排版换行，
   needle 用的是 `replace("\n"," ")`（不折叠内部多空格），所以**多空格或额外换行仍可能造成假红**：
   这是"钉住文本"的固有代价，宁可假红也不假绿。
4. **植入 A2 的红落在漂移检查上**：从**覆盖**判定行删字段时，活体测试先红在
   `assert_observation_matches_fixture`（因为 fixture 是冻结观测）。覆盖判定行**本身**的钉住敏感度
   由**测试内变异**证明（§3/§6），不是由 A2 直接证明。我如实区分这两件事。
5. **`.hoh/`、`.godot/` 两树不同**：我只证明了**工程投影文件**（17 个）与冻结候选一致；
   两树的 `.hoh/`（轮次产物）与 `.godot/`（引擎缓存）本就不同集合，属预期，未逐字节比对。
6. **历史未刷新**：`DECISIONS.md` D288/D289 与 `TASK-DR76-ACCEPTANCE.md` 仍含旧 token（禁改/历史件），
   本批只提供映射与限定；跨批次检索旧 token 时需按本报告 §4 的映射读。
7. **`cargo fmt` 重排了两个测试文件的行尾**（CRLF→LF，见 §1）：功能与 blob 一致，但这是本批对工作树
   行尾的一次真实改动，交给验收者裁定是否可接受。
8. **未在真机上验证**：`still unspent; ` 与 `stayed false; ` 这两句在**真机**判定行里是否**总**出现
   （即真机分支是否与夹具同形）——离线不可测；它由生产代码的同一个 `format!` 决定，因此我判断风险低，
   但**不声称已测**。

---

## 9. 诚实披露（任务书 §5.9）

1. **第一版 ② 的断言仍然是弱断言**，被**植入 A 的第一次运行**（结果 `ok`）当场揭穿；我改了 needle 才成立。
   这条错误与我要根除的 D2 同类，我把它写进 §5 而不是只说最终态。
2. **`cargo` 的陈旧指纹造成过两次矛盾读数**（"植入已回退却仍按植入跑"）：因为 `restore` 用 `copy2` 保留了旧 mtime。
   我最终以清 fingerprint 消除；**但这意味着我早期的一次"绿"读数不可信**，报告中所有红/绿读数都注明来自清后重编。
3. **门的"强制重编"没有按任务书字面用逐文件 `touch`**，而是用清 fingerprint（只删 `hof-rs-*`，354 条依赖指纹未动）。
   我判断它满足目的，但**字面上不同**，故在此披露。
4. **`cargo fmt` 重写了两个测试文件的行尾**（CRLF→LF）。我没有手工改任何行尾，但结果是一次行尾变化，已在 §1 披露。
5. **植入 A 的第一次尝试只证明了我第一版断言是弱的**（它绿），真正的红是**第二版**取得的；§6 表格里 A 的红对应第二版。
6. **`smoke-t5/t7/t8/t9/t10` 的摘要我只有缩略钉值**：我只做了前缀+文件数比对，**没有**完整 64 位比对（那需要验收记录里的全文）。§7 明确区分了 `smoke-t6` 的 FULL MATCH 与其余四条的 prefix+count match。
7. **本批未改 `DECISIONS.md`**（任务书禁止），因此 D288/D289 里的旧 token 仍在；这是**有意的、披露的**未同步点，不是遗漏。
8. **未跑真机轮、未启动 Godot、未推送**：不声称判据(3)、不声称 130 批在真机足够、不声称真机判定行措辞一定与夹具同形（见 §8.8）。
9. **一处我无法证明的工序**：任务书 §5 的"每项先写会失败的最小测试（贴真实失败输出）"——我对 ②/③ 的 5 条测试**确实**先写并跑出 exit 101（§5 表），但这些"先红"的**当时日志**我没有单独存档（只有终态树 + 植入证据）。可复核的是**终态**：5 条测试在缺少对应生产/交付改动时确实会红（可由植入 A/B/C/D 反向验证）。

---

## 10. 附：本批提交

| 提交 | 内容 |
|---|---|
| `7ae7dcd` | ① 逐字引文 + 旧引用标注；② 判定行钉住（第一版）；③ 改名 + 限定 + 全消费者同步 |
| `e04546c` | ② 钉住改为"从判定行自己的措辞起"（第一版钉住被植入 A 证伪后的修正） |
| `608bb34` | ② 把 fixture 漂移检查重新挂回两个活体测试（消 warning + 恢复双向钉住） |
| `564c102` | ② 测试内变异证明 + needle 形状统一 + `cargo fmt` |

（任务书要求的报告文件 = 本文件；写完不再修改。）

**机器可读块的合法性检查（我自产，完成前跑的）**：本报告**没有** `json` 围栏块（唯一的机器可读对象是 §4 的映射行与常量名，均为散文/表格）。用栅栏感知脚本亲验：

```
$ python %TEMP%\dr77\fence_check.py .spec/hof-rs/tasks/TASK-DR77-REPORT.md
json-fenced blocks = 0 ; json.loads failures = 0
fence_exit=0
```
