# TASK-DR62-REPORT — 去掉三处"靠约定"的缺口：`.stale-` 判据去名字化、`copy_tree` 过滤、遍历作用域永久固定

> 实现子代理报告。任务书：`.spec/hof-rs/tasks/TASK-DR62.md`（本文件是其 §4 要求的八节报告）。
> 上游输入（只当线索，判定以我自己的实测为准）：`.spec/hof-rs/tasks/TASK-DR61-ACCEPTANCE.md`（DEF-1 / R-B / R-E、
> 以及 R-F 的未解释 mtime 差异）、`.spec/hof-rs/tasks/TASK-DR61-REPORT.md`、`DECISIONS.md` D249/D250。
> **离线**：未启动 Godot、未触碰任何外部/MCP 端口、未联网、未调模型端点、未 push。
> 批次起点 = `6a0c9a9`（= `origin/master`）；本批 = 3 个代码/测试提交（`d338459`/`6dc12b5`/`49b9417`）
> + 本报告及其定稿小修的纯文档提交（`fb572ca` 及之后一个），**全部未 push**。
> **不声称 E1..E6 中任何一条 met（尤其不声称 E3）** —— 那只能由真机轮次判定。

---

## 1. 结论 + 套件真实尾部/退出码（与 366/0/7 对照）

**结论：任务书 §1 的三件事全部落地。** 三件事的落点见 §2；TDD 与植入证据见 §3/§4；
"`.stale-` 命名的本轮产物不再被误跳过"的实测见 §5；禁区自查见 §6；遗留项见 §7；诚实披露见 §8。

门（`F:\moonbit-hof-rs`，`cargo test --offline`，串行、不抑制输出、每次全量重跑）：

```
$ cargo test --offline
   Doc-tests hof_rs

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
EXIT=0
```

| 口径 | 批次起点 `6a0c9a9`（我自己在动手前重跑） | 交付树 `49b9417` | 与任务书基线 366/0/7 |
|---|---|---|---|
| targets | 39 | **39** | 相同 |
| passed | 366 | **372** | **+6** |
| failed | 0 | **0** | 相同 |
| ignored | 7 | **7** | **未增** |
| `^warning` 行 | 0 | **0** | 相同 |
| exit | 0 | **0** | 相同 |

+6 = lib `111 → 115`（view 净 +2、hygiene 净 +2）**加上** `tests/evidence_unreachable.rs` `3 → 5`（+2）。
即任务书记的 366/0/7 与我在起点重跑的实测**逐字一致**，交付后 passed 只增不减、`ignored` 7→7、
无既有测试被删/放宽/加 `#[ignore]`（`#[ignore` 全树出现 **8** 次 = `tests/godot_smoke.rs` 的 7 个属性 + 1 条文档注释，
起点与交付树同值；真机目标 E0–E6 仍全部 ignored，**本批未跑真机**）。

本批提交（起点 `6a0c9a9`，未 push）：

| 提交 | 角色 |
|---|---|
| `d338459` | **红**：`copy_evidence` 按名字隐藏 `.stale-` 命名的本轮产物；`copy_tree` 完全没有过期过滤 |
| `6dc12b5` | 实现：显式清单 `.superseded.json` + 两条拷贝路径统一判据 + 生产者在改名**之前**写记录 |
| `49b9417` | 遍历作用域自检 + `.hoh` 外常驻种子 + 轮次级"不再被误跳过"实测 |
| 本报告提交 `fb572ca` + 定稿小修 | `TASK-DR62-REPORT.md`（纯文档：`git diff --stat 49b9417..HEAD -- src tests Cargo.toml Cargo.lock` = 空；最终全量套件跑在代码树 `49b9417` 上） |

---

## 2. 三件事各自的落点（文件:行）与理由；`.stale-` 判据的新依据

### 2.1 第一件：`.stale-` 判据**去名字化**（改用显式清单）

**判据的新依据 = 一份显式的"已取代"清单文件**，不是任何名字形状：

- `src/runtime/hygiene.rs:391` `pub const SUPERSEDED_MANIFEST: &str = ".superseded.json"`
  —— 每个目录里的清单，内容是**相对该目录**的路径 JSON 数组。
- `src/runtime/hygiene.rs:403` `pub struct SupersededSet`：`load`（`:413`，缺失=空集；**损坏=报错**）、
  `contains`（`:444`）、`record`（`:450`，写/追加清单）。
- `src/runtime/hygiene.rs:466` `pub fn is_superseded(root, relative) -> io::Result<bool>`
  —— **唯一的消费者判据**：沿 `relative` 的路径分量，逐级查 `root` 及其各祖先目录的清单，命中即"已取代"。
- **生产者**：`src/adapter/godot.rs:2444` `SupersededSet::record(directory, &name)?`，位于
  `std::fs::rename`（`:2446`）**之前** —— 记录写不进去就**大声失败**（调用方 `godot.rs:1093-1097` 记 FAILED note），
  而不是先把字节挪走却没有结构性痕迹。这是 DR-49 `invalidate_artifact` 的唯一生产调用点（`godot.rs:1088`）。
- **消费者**：`src/runtime/view.rs:142`（`copy_evidence`）与 `src/runtime/view.rs:86`（`copy_tree`），
  两处都是 `if hygiene::is_runtime_bookkeeping(&rel) || hygiene::is_superseded(src, &rel)? { continue; }`。
- **删除**了 DR-49/DR-61 的名字谓词 `pub fn is_expired_name(name) -> bool { name.contains(".stale-") }`
  （起点 `src/runtime/hygiene.rs:383`）：它现在没有任何调用者，留着只会招人重新接线。
- `stale_name`（`:494`）**保留**，但文档已改写为"**仅生产者侧的审计名**"：改名仍带 `.stale-<ts>`，
  以便"已取代"在仓库里可 grep、可审计，字节也不被删除。

**为何它不靠名字（三条互相独立的理由，均可核对代码）**：

1. **判据的输入只有清单**：`is_superseded` 不读取文件名，只把"相对路径字符串"拿去和清单条目做集合成员判断。
   一个从未被记录的名字**永远不匹配**——即使它长得就像 `.stale-`（§5 有轮次级实测）。
2. **被记录者无需任何标记名**：清单命中即跳过，与名字无关；DR-62 甚至没有要求被取代者改名为 `.stale-`。
   （改名仍保留，是为了审计与 DR-49 的"目标路径先清空"语义，不是为了判据。）
3. **清单由运行时自己写**：`SupersededSet::record` 是唯一写入路径，所以"被跳过"的集合
   ⊆ "运行时确实取代过"的集合，角色无法靠命名把自己塞进去或挤出去。

**为什么不是别的方案**（被考虑并否决）：

- 继续用名字子串：这就是 DEF-1/R-E 的缺陷本身（角色给**本轮**产物起名 `*.stale-*` 就被隐藏）。
- 用一个"保留目录"（如把过期件搬进 `.hoh/evidence/.stale/`）：仍是命名空间约定，且"取代"是**逐文件**的事实，
  目录只表达了"某次批量移动"，不能表达"哪一个具体路径已被取代"。
- 只在内存里把集合从调用方传进拷贝函数：清单不落盘 ⇒ 崩溃/跨进程就没有审计痕迹，
  验收者也无法核对"到底记了什么"；落盘的清单本身就是可核对工件。

**"旧行为必须仍被拒绝（隔离物仍不得进入视图）"如何仍然成立**：两条互补的结构性事实——

- **被隔离者（上一轮遗留）**：DR-61 把**整棵 `.hoh` 移出工作区**到 `runs/<run_id>/quarantine/`，
  于是 `copy_evidence`/`copy_tree` 的**源目录里根本不存在**它们 ⇒ 靠"不在场"被拒绝，与名字无关。
  该行为由既有测试 `tests/evidence_unreachable.rs::the_tester_candidate_view_never_carries_the_previous_rounds_evidence`
  继续守着（本批未改、仍绿）。
- **被取代者（轮内 DR-49 就地改名，留在 `.hoh` 里）**：靠 §2.1 的清单记录被拒绝。

### 2.2 第二件：补 `copy_tree` 的过滤（`run_loop.rs:991` 那条路径）

- 落点：`src/runtime/view.rs:86`（在 `pub fn copy_tree`（`:69`）内部）。
  **调用点不需要改动**——`src/runtime/run_loop.rs:991` 依旧调用 `copy_tree(&deterministic_dir, &candidate/.hoh/deterministic, &[])`，
  过滤因此在两条拷贝路径**同一处**生效（这正是要的效果：缺口不在调用点，在函数没判据）。
  该调用点只加了一条解释性注释（`src/runtime/run_loop.rs:991-994`）。
- 理由：DR-61 R-3 / 独立验收 R-B 指出 `copy_evidence` 有过期过滤而 `copy_tree` **一个都没有**，
  同一类"过期件进入冻结候选"的形态可以从这条路径进入。本批让两条路径共用同一个
  `is_superseded` 判据（外加"清单文件本身不进入视图"`is_runtime_bookkeeping`，`hygiene.rs:395`）。

### 2.3 第三件：永久固定遍历作用域（DEF-1 的根除）

- `.hoh` **之外**的常驻种子：`tests/evidence_unreachable.rs:109` `OUTSIDE_HOH_SEEDS`
  （`previous-round/out-of-hoh-battery.json`），播种函数 `:123`。
- **自检测试**：`tests/evidence_unreachable.rs:439`
  `the_workspace_walk_reaches_a_marker_seeded_outside_hoh` —— 先跑一整轮真实 round（隔离照常发生），
  然后断言 `walk(&workspace)` **确实命中**该 `.hoh` 外标记（且命中在它自己的路径上、且它确实存活），
  同时断言 `walk(&workspace/.hoh)` **看不到**它。
- **该语义也同时固化进既有不变量测试**：`tests/evidence_unreachable.rs:267`（1c）正对照，
  在 `a_wildcard_walk_of_hoh_cannot_reach_the_previous_rounds_evidence` 内用同一次 `walk(&workspace)`
  做"必须命中 `.hoh` 外标记"的正向断言。
- 理由：把**遍历作用域**（整个角色 cwd）与**隔离作用域**（`.hoh` 家族）解耦。
  若有人把 `walk(&workspace)` 收窄回 `.hoh`，这两处**同时**变红（§4 植入 ③ 的真实输出），
  而不变量文本本身不会因为种子全在 `.hoh` 下而静默失效。任务书要求的"**必须让第 3 项的自检以及
  原有的 `.hoh` 外种子测试都红**"，实测正是这两条（§4.3）。

---

## 3. TDD 证据：红（真实失败输出）→ 绿

### 3.1 红提交 `d338459`（生产代码未动，只加测试）

三个新测试（`src/runtime/view.rs`），真实输出（`dr62-scratch/red-view.txt`）：

```
running 9 tests
test runtime::view::tests::a_real_invalidation_is_what_the_evidence_copy_skips ... FAILED
test runtime::view::tests::copy_tree_applies_the_same_supersession_criterion_as_the_evidence_copy ... FAILED
test runtime::view::tests::copy_evidence_skips_a_recorded_supersession_and_copies_a_role_named_stale_file ... FAILED
test result: FAILED. 6 passed; 3 failed; 0 ignored; 0 measured; 104 filtered out; finished in 0.06s
EXIT=101

---- runtime::view::tests::a_real_invalidation_is_what_the_evidence_copy_skips stdout ----
panicked at src\runtime\view.rs:442:9:
DR-62: a `.stale-`-looking name the runtime never superseded must be copied

---- runtime::view::tests::copy_tree_applies_the_same_supersession_criterion_as_the_evidence_copy stdout ----
panicked at src\runtime\view.rs:397:9:
DR-62: copy_tree must skip a recorded supersession exactly as copy_evidence does

---- runtime::view::tests::copy_evidence_skips_a_recorded_supersession_and_copies_a_role_named_stale_file stdout ----
panicked at src\runtime\view.rs:360:9:
DR-62: a `.stale-` name the runtime never superseded is this round's artifact and must be copied
```

每条都**因当前行为而红**，且红的理由就是任务书点名的两处缺口：按名字隐藏（两条）+ `copy_tree` 没有过滤（一条）。

**第三件事（遍历作用域）没有"修前之红"**：它固定的是一个**已经存在且当前为绿**的能力
（`walk(&workspace)` 本来就覆盖整个工作区）。所以该测试在交付时按构造就是绿的；
它的非空洞性由**植入 ③**证明（§4.3 的真实红输出）。这一条我不粉饰，见 §8.1。

### 3.2 绿（`6dc12b5` / `49b9417`）

```
$ cargo test --offline --lib runtime::view::tests
test result: ok. 9 passed; 0 failed; 0 ignored; 0 measured; 106 filtered out; finished in 0.06s   EXIT=0
$ cargo test --offline --lib runtime::hygiene
test result: ok. 15 passed; 0 failed; 0 ignored; 0 measured; 100 filtered out; finished in 0.05s  EXIT=0
$ cargo test --offline --test evidence_unreachable
test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 29.82s      EXIT=0
```

实现后立即全量复跑（`dr62-scratch/green-suite-1.txt`）：`39 targets / 370 passed / 0 failed / 7 ignored / warning=0 / EXIT=0`；
自检与实测测试加入后最终全量（§1）：`372 / 0 / 7`。

---

## 4. 非空洞性证据：三处植入各自的红 + 逐字节回退

三处植入都**只改一处、测试断言一字未动**；每处植入前都把目标文件**逐字节**备份到
`dr62-scratch/head/`，回退用 `cp` 回灌，并四法证明（外加 `cmp`）。

### 4.1 植入 ① —— 把 `.stale-` 判据改回"按文件名"（**生产代码** `src/runtime/view.rs`）

植入（两条拷贝路径的判据一起换成 DR-61 的名字谓词）：
`if hygiene::is_runtime_bookkeeping(&rel) || hygiene::is_superseded(src, &rel)? {` →
`if rel.split('/').any(|component| component.contains(".stale-")) {`（`copy_tree` 与 `copy_evidence` 各一处）。

真实输出（`dr62-scratch/plant-1.txt`）：

```
test runtime::view::tests::copy_tree_applies_the_same_supersession_criterion_as_the_evidence_copy ... FAILED
test runtime::view::tests::a_real_invalidation_is_what_the_evidence_copy_skips ... FAILED
test runtime::view::tests::copy_evidence_skips_a_recorded_supersession_and_copies_a_role_named_stale_file ... FAILED
test result: FAILED. 6 passed; 3 failed; 0 ignored; 0 measured; 106 filtered out; finished in 0.07s
LIB_EXIT=101

---- a_real_invalidation_is_what_the_evidence_copy_skips stdout ----
panicked at src\runtime\view.rs:453:9:
DR-62: a `.stale-`-looking name the runtime never superseded must be copied
---- copy_tree_... stdout ----
panicked at src\runtime\view.rs:413:9:
DR-62: copy_tree must not skip by name either
---- copy_evidence_skips_a_recorded_... stdout ----
panicked at src\runtime\view.rs:371:9:
DR-62: a `.stale-` name the runtime never superseded is this round's artifact and must be copied

也同时打红轮次级实测：
test a_role_named_stale_artifact_is_not_hidden_from_the_tester ... FAILED
panicked at tests\evidence_unreachable.rs:513:5:
assertion `left == right` failed: DR-62: a `.stale-`-named artifact the runtime never superseded must reach
the frozen candidate; the candidate holds: [".hoh/evidence/.superseded.json"]
  left: None
 right: Some("DR-62 this round's own `.stale-`-named evidence\n")
INT_EXIT=101
```

注意最后一行的额外收获：回到名字判据后，候选视图里**只剩** `.hoh/evidence/.superseded.json`（清单文件本身），
本轮产物被隐藏 —— 这既是缺陷 1 的形态，也说明"清单文件是运行时簿记、不得进入视图"的断言不是无的放矢。

### 4.2 植入 ② —— 把 `copy_tree` 的过滤**关掉**（**生产代码** `src/runtime/view.rs`，只这一条路径）

植入：`copy_tree` 内部的判据改为 `if false && (hygiene::is_runtime_bookkeeping(&rel) || hygiene::is_superseded(src, &rel)?) {`。

真实输出（`dr62-scratch/plant-2.txt`）：

```
test runtime::view::tests::copy_tree_applies_the_same_supersession_criterion_as_the_evidence_copy ... FAILED
panicked at src\runtime\view.rs:408:9:
DR-62: copy_tree must skip a recorded supersession exactly as copy_evidence does
test result: FAILED. 8 passed; 1 failed; 0 ignored; 0 measured; 106 filtered out; finished in 0.07s
LIB_EXIT=101
```

**恰好**打红对应那一条测试：`copy_tree` 的过滤不是摆设；同时 `copy_evidence` 的测试全绿，
说明两处判据是**各自独立可测**的，不是同一断言顺带覆盖。

### 4.3 植入 ③ —— 把 `walk` 收窄回 `.hoh`（`tests/evidence_unreachable.rs`）

植入：把两处 `let cwd = walk(&workspace);`（`:252` 既有不变量测试、`:448` 自检）改成
`let cwd = walk(&workspace.join(".hoh"));`（即 DEF-1 设想的"将来有人把遍历收窄回 `.hoh`"）。

真实输出（`dr62-scratch/plant-3.txt`）——**自检与原有的 `.hoh` 外种子测试同时红**：

```
failures:
---- the_workspace_walk_reaches_a_marker_seeded_outside_hoh stdout ----
panicked at tests\evidence_unreachable.rs:451:9:
assertion `left == right` failed: DR-62: a walk of the workspace must reach the marker outside `.hoh`
at previous-round/out-of-hoh-battery.json: []; walked keys: ["EVIDENCE_HISTORY.md", "PROJECT_MAP.md",
"TASK.md", "TOOLS.md", "deterministic/battery.json", "deterministic/build.json", ...]
  left: 0
 right: 1
---- a_wildcard_walk_of_hoh_cannot_reach_the_previous_rounds_evidence stdout ----
panicked at tests\evidence_unreachable.rs:276:9:
assertion `left == right` failed: DR-62: a walk of the role's cwd must reach the marker outside `.hoh`
at previous-round/out-of-hoh-battery.json: []; walked keys: [ ... 同上 ... ]
  left: 0
 right: 1
failures:
    a_wildcard_walk_of_hoh_cannot_reach_the_previous_rounds_evidence
    the_workspace_walk_reaches_a_marker_seeded_outside_hoh
test result: FAILED. 3 passed; 2 failed; 0 ignored; 0 measured; 0 filtered out; finished in 28.89s
INT_EXIT=101
```

**该植入在测试文件里，不在生产代码里** —— 这是与任务书 §2 字面要求（"三处**仅生产代码**的植入"）的**一处偏离**，
原因与理由见 §8.2：DEF-1 所指的 `walk` 就是这个测试自己的递归遍历（DR-61 §5 明确要求不变量用**真实文件系统遍历**验证，
而不是调用某个运行时函数），生产代码里不存在这样一个"工作区 cwd 遍历"可供收窄。

### 4.4 逐字节回退证明（每处植入之后）

三处植入的回退都做了同一组检查，真实输出：

```
$ cp dr62-scratch/head/view.rs src/runtime/view.rs
$ cmp src/runtime/view.rs dr62-scratch/head/view.rs   => (无输出，identical)
$ git status --porcelain                              => (空)
$ git diff --stat                                     => (空)
$ git hash-object src/runtime/view.rs                 = f8ff3851d91706d6b179eeb5eea5c5ff5b07ccd6
$ git rev-parse HEAD:src/runtime/view.rs              = f8ff3851d91706d6b179eeb5eea5c5ff5b07ccd6

$ cp dr62-scratch/head/evidence_unreachable.rs tests/evidence_unreachable.rs
$ cmp tests/evidence_unreachable.rs dr62-scratch/head/evidence_unreachable.rs => identical
$ git status --porcelain => (空);  git diff --stat => (空)
$ git hash-object tests/evidence_unreachable.rs       = f597d9c4bb06add050aa559c4d21fa2dab1e4e5f
$ git rev-parse HEAD:tests/evidence_unreachable.rs    = f597d9c4bb06add050aa559c4d21fa2dab1e4e5f
```

回退后复跑（`dr62-scratch/restore-green.txt`）：`runtime::view::tests 9/0`、`runtime::hygiene 15/0`、
`evidence_unreachable 5/0`，三者 `EXIT=0`；最终全量 `372/0/7 EXIT=0`（§1）。

**CRLF 说明（口径的一部分，不粉饰）**：本仓 `core.autocrlf=true`（且 `.gitattributes` 只对
`tests/fixtures/dr58/**` 禁转换）。`src/adapter/godot.rs` 的工作树是 CRLF，其余被改文件是 LF。
含义是：`git status` / `git diff` / `git hash-object` 都会先做 CRLF→LF 归一化，
**因此它们看不见"纯换行符差异"**。所以我额外用 `cmp` 对植入前的**逐字节备份**做比较，
它才是"逐字节回退"的最强证据；三法仍然全部成立。受植入影响的文件都验过：`cmp` identical
（`src/runtime/view.rs`、`tests/evidence_unreachable.rs`），`git hash-object` == HEAD blob。

### 4.5 第四处（加固，非任务书要求）：生产者记录顺序

`invalidate_artifact` 的既有单测被**加强**（新增 3 条断言，见 §6 的 assert 计数）：
断改名后 `SupersededSet::load(temp.path())` 确实含该名字、且 `is_superseded(temp.path(), &stale)` 为真。
把它换成"先改名、后记录"不会红（结果态相同），所以它固定的是**顺序契约**而非结果 ——
顺序的必要性（记录失败要大声失败）在 §7 R-2 里按"实测/推断"分别说明。

---

## 5. "`.stale-` 命名的本轮产物不再被误跳过"的实测

三层实测，全部为真跑输出：

1. **单元层**（`src/runtime/view.rs:342`，绿）：源目录里同时有
   `replay.stale-this-round.json`（从未被记录）、被记录的 `frame-00.png.stale-1790663544` 与
   子目录清单记录的 `replay/round.json.stale-1790663544` ⇒ 目标目录里
   **只有**未记录者 + `frame-00.png`；被取代者原地保留；不给被跳过者做 oversized 报告。
2. **生产者—消费者层**（`src/runtime/view.rs:432`，绿）：用**真实生产函数**
   `adapter::godot::invalidate_artifact` 制造一次真实取代（它自己写清单），再跑真实 `copy_evidence`
   ⇒ 被真实取代的 `frame-00.png.stale-<ts>` 不进候选，而 `this-round.stale-keep.png`
   （仅名字像）**进**候选，字节都还在源目录。
3. **轮次层**（`tests/evidence_unreachable.rs:484`，绿）：真实 round 里由 **Developer 自己**
   （Developer 的 cwd 就是 workspace）写下三样东西：`.hoh/evidence/round-one.stale-keep.png`（本轮产物，
   名字带 `.stale-`）、`.hoh/evidence/superseded.stale-1790663544.png`（被清单记录）、
   `.hoh/evidence/.superseded.json`（清单）。Tester 的冻结候选视图实测：
   - `tester[".hoh/evidence/round-one.stale-keep.png"] == "DR-62 this round's own `.stale-`-named evidence\n"`（**不再被误跳过**）；
   - `!tester.contains_key(".hoh/evidence/superseded.stale-1790663544.png")`（结构性跳过仍生效）；
   - `!tester.contains_key(".hoh/evidence/.superseded.json")`（簿记不进视图）；
   - `workspace.join(".hoh/evidence/superseded.stale-1790663544.png").is_file()`（跳过≠删除）。

**"误跳过"的前后对照（同一测试、只换生产判据）**：§4.1 显示，把判据改回名字匹配后，同一测试的
候选视图里**只有** `.hoh/evidence/.superseded.json`，`round-one.stale-keep.png` 消失
（`left: None / right: Some("DR-62 this round's own ...")`）。⇒ "以前会被隐藏"与"现在不再被隐藏"
两侧都是真实输出，不是推断。

---

## 6. 禁区自查（真实输出）

**引擎树未改**（必须用**嵌套仓** + mtime/摘要，因为外层**不跟踪**引擎树，D242）：

```
$ git ls-files godot-mcp | wc -l          => 6484   # pathspec 真命中（>0）
$ git ls-files godot-mcp/godot | wc -l    => 0      # 外层对引擎树是空判 => 外层 diff 无证据力
$ git -C godot-mcp/godot status --porcelain | wc -l  => 0
$ git -C godot-mcp/godot rev-parse HEAD   => fc63af77c33368c4a1bb839c95d19750554f63a3   # 起点==终点
$ sha256sum godot-mcp/godot/modules/mcp_server/tools/running_game_test_execution.cpp
  => ece4ae63d445719b662a6e9ad99ba80bebba3ea3c94468094c7e9cb820ddff3f   # 起点==终点，与 DR-59/DR-61 记录一致
$ find godot-mcp/godot -type f -newermt '2026-09-29 19:00' | wc -l => 0
$ find godot-mcp/godot -type f -newermt '2026-09-29 11:00' | wc -l => 0
```

**引擎 mtime 台账（D250 记为"未解释"的 R-F，本批给出实测解释）**：起点与终点**逐字相同**，

- 整棵树（含 `.git`）最新 = `2026-09-29 10:58:15`，落在
  `godot-mcp/godot/.git/refs/remotes/origin/feature/mcp-server-module-rebuild`（远端跟踪 ref，非源码）；
- 排除 `.git` 的源码侧最新 = `2026-09-29 10:49:37`（`tests/data/translations.fa.translation`）；
- **`modules/mcp_server` 子树最新 = `2026-09-29 10:37:38`**（`scripts/mcp029_clear_default_evidence.ps1`），
  与 DR-59 记录的数字**逐字相同**。

⇒ D250 的"差异"可以解释为**口径不同**：DR-59 记的是 `mcp_server` **子树**最新 mtime（10:37:38），
DR-61 与独立验收记的是**整棵树（含 `.git`）**最新 mtime（10:58:15）。三者今天都复现，且 mtime **没有任何变化**。
（我无法看到 DR-59 当时的脚本，所以这条是"今天两个口径分别复现出两个纪录值"的**解释**，
不是对 DR-59 动作的**实测**；但"引擎内容未改"另由嵌套 status/HEAD/关键 sha/`-newermt` 四项实测支撑。）

**`runs/**` 未动、`.workspace/mario/**` 未改**（两者都不被外层跟踪：`git ls-files runs`=0、`git ls-files .workspace`=0
⇒ 外层 `git diff` 对它们是空判，故用"摘要 + mtime"）。**摘要口径（写明）**：递归枚举文件
（`Get-ChildItem -Recurse -Force -File`），每文件取**相对仓根**路径（`\`→`/`、转小写）、字节长度、
SHA256（小写 hex），三列 `\t` 连接、行间 `\n`、无尾随换行，整体 UTF-8 后取 SHA256；
行按路径升序排序，**排序器用 PowerShell `Sort-Object`（文化敏感排序）**——这是口径的一部分。
脚本 `dr62-scratch/digest.ps1`（我按该口径重建）。**口径自证**：`runs/smoke-t6` 复算 =
`c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03`，与 DR-54/57/59/61 记录**逐字一致**。

```
批次起点（动手前）：
  .workspace/mario  files=259  digest=4e494547416b2e87ba025d686afef9447d4f92c027917d1790e6fc9deaeaa84a newest=2026-09-29 14:32:28
  runs              files=5147 digest=01ff775e36935d3d92dab6919fe030389a8ff53483c52e87288ad711ec840dc3 newest=2026-09-29 14:44:16
  runs/smoke-t6     files=135  digest=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03 newest=2026-09-29 02:32:01
全部写操作结束、最终全量套件之后：
  .workspace/mario  files=259  digest=4e494547416b2e87ba025d686afef9447d4f92c027917d1790e6fc9deaeaa84a newest=2026-09-29 14:32:28
  runs              files=5147 digest=01ff775e36935d3d92dab6919fe030389a8ff53483c52e87288ad711ec840dc3 newest=2026-09-29 14:44:16
  runs/smoke-t6     files=135  digest=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03 newest=2026-09-29 02:32:01
```

其余禁区与纪律（真实输出）：

```
$ sha256sum .spec/hof-rs/PRD-mario.md
4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a   # 未变
$ git diff --stat 6a0c9a9..HEAD -- Cargo.toml Cargo.lock          => (空)   # 无新依赖
$ git diff --stat 6a0c9a9..HEAD -- DECISIONS.md                   => (空)   # 未改 DECISIONS.md
$ git diff --stat 6a0c9a9..HEAD -- .spec/hof-rs/PRD-mario.md      => (空)   # 未改 PRD
$ git diff --stat 6a0c9a9..HEAD
 src/adapter/godot.rs          |  24 +++++-
 src/runtime/hygiene.rs        | 191 ++++++++++++++++++++++++++++++++++++++----
 src/runtime/run_loop.rs       |   3 +
 src/runtime/view.rs           | 147 +++++++++++++++++++++++++-----
 tests/evidence_unreachable.rs | 180 +++++++++++++++++++++++++++++++++++++--
 5 files changed, 502 insertions(+), 43 deletions(-)
$ git status --porcelain                                          => (空)
    # 该输出取自"报告尚未落盘"的那一刻；报告提交后状态里会出现两个未跟踪文件，
    # 其一是本报告、其二是调度者在批次尾声新建的 TASK-DR62-ACCEPT.md（不是我的产物，见 §8.11）
$ git diff --cached --stat                                        => (空，未 stage)
$ git rev-parse origin/master  => 6a0c9a9ae7c02a842619690c60693b96151e087b   # 批次起点，未 push
$ git rev-parse HEAD           => 49b9417c1ae6a2b635c9a820eaf7cf9989b8c488   # 代码树 HEAD（本报告提交后为 fb572ca…，纯文档）
$ git log --oneline origin/master..HEAD | wc -l                   => 3      # 未 push（报告提交后 4）
$ grep -rn '#\[ignore' src tests | wc -l                          => 8      # 起点同为 8（7 属性 + 1 注释）
```

**"无既有测试被删/放宽"** 的函数清单与断言计数核对（`git show 6a0c9a9:<file>` vs 工作树）：

```
== src/runtime/view.rs ==
removed (baseline-only): fn copy_evidence_skips_superseded_files_and_keeps_them   # 见 §8.3：被"替换并加强"，非删除
added:  fn record_supersession / fn copy_evidence_skips_a_recorded_supersession_and_copies_a_role_named_stale_file
        / fn copy_tree_applies_the_same_supersession_criterion_as_the_evidence_copy
        / fn a_real_invalidation_is_what_the_evidence_copy_skips
== src/runtime/hygiene.rs ==
removed (baseline-only): fn is_expired_name            # 生产谓词本身被移除（判据去名字化）
added:  SupersededSet::{load,contains,record,len,is_empty} / is_runtime_bookkeeping / is_superseded
        / fn a_supersession_recorded_in_a_subdirectory_manifest_is_found_from_the_root
        / fn the_manifest_is_bookkeeping_and_a_malformed_one_is_an_error
        # `the_superseded_marker_is_recognized_by_one_predicate` 保留原测试名，函数体被替换为更强的结构判据断言
== src/adapter/godot.rs ==
removed: (无)    added: (无)      # 只加强既有的 invalidating_an_artifact_moves_it_aside
== tests/evidence_unreachable.rs / tests/evidence_isolation.rs / src/runtime/run_loop.rs ==
removed: (无)                      # 只有新增（+ 一处把 run_round 拆出 run_round_with 的内部重构）
assert 计数（起点 -> 交付）：view 18 -> 29；hygiene 51 -> 62；godot 114 -> 116；evidence_unreachable 16 -> 30
```

**离线**：全程只跑 `cargo test --offline` / `cargo build --offline` 语义的命令；**未执行任何 godot 可执行文件**；
真机目标 7 条（`godot_smoke` 的 E0–E6，`#[ignore]`）保持 ignored 未被运行（ignored 7→7）。
披露：既有套件内含 **loopback-only** 测试（如 `tools::endpoint::*`、`doctor_probe` 系列）会绑定 127.0.0.1 的临时端口 ——
那是套件原有行为，与本批改动无关；我没有连接任何外部服务、没有触碰 Godot/MCP 端口。

**scratch 工作区**：`C:\Users\wyl\AppData\Local\Temp\dr62-scratch\`（日志 `red-view.txt`、`green-lib.txt`、
`green-suite-1.txt`、`green-unreachable.txt`、`plant-1/2/3.txt`、`restore-green.txt`、`suite-baseline.txt`、
`suite-final.txt`、`guards.txt`、`fn-inventory.txt`、`engine-baseline.txt`、`engine-final.txt`、
`digests-final.txt`；脚本 `digest.ps1`、`engine-check.sh`；逐字节备份 `head/`、`backup/`）。清理见 §8.9。

---

## 7. 遗留风险与未验证项（严格区分**实测** / **推断**）

**实测（有原始输出）**

- **R-1 `.hoh` 之外的残留仍不被隔离**（DR-61 R-A 的延续，本批**已改为可测**）：`OUTSIDE_HOH_SEEDS`
  的标记在开轮后仍在原地、仍可被 `walk(&workspace)` 命中（§2.3 的正对照就是它的实测）。
  DR-62 的不变量范围同样**只以 `.hoh` 家族为界**，本批没有把隔离面扩大到 `.hoh` 之外（也不在任务书范围）。
- **R-2 判据依赖"生产者先记录"**：`is_superseded` 只认清单；若将来有人新增一条"取代"路径却忘记调用
  `SupersededSet::record`，该路径取代的字节会**进入视图**（判据是"记录在案"）。实测：全仓生产调用点唯一
  （`git grep` 只有 `godot.rs:1088`），且既有单测已断言 `invalidate_artifact` 会记录；但这是一条**结构性依赖**。
  另外：记录失败会**大声失败**（`record` 在 rename 之前，`godot.rs:2441-2447`）——`record` 的失败分支没有单测打红
  （见 R-6/R-7）。
- **R-3 清单损坏 = 报错**：`SupersededSet::load` 对不可解析内容返回 `InvalidData`（`hygiene.rs:413-427`），
  `copy_tree`/`copy_evidence` 会把错误向上冒泡（视图构建失败）。这是刻意的"不静默再放行"，
  代价是**角色可写的目录里出现坏清单会让视图构建失败**。单测 `the_manifest_is_bookkeeping_and_a_malformed_one_is_an_error` 固化。
- **R-4 `copy_tree` 增加逐目录清单查询**：`is_superseded` 沿路径分量逐级 `load`（每级一次 `exists()` 探测）。
  我没有测量大工作区上的开销；测试树规模下无感（全量套件墙钟与基线同量级，见 §1 各 target 耗时）。
- **R-5 无 GC**：`runs/<id>/quarantine/**` 每轮留一份，与 DR-59/DR-61 同族，本批未处理。
- **R-6 候选身份不受影响**（沿用 DR-61 的结构性理由 + 既有测试）：`.hoh` 在 `HashExcludes::merged()` 里整体排除，
  `the_candidate_identity_is_unaffected_by_evidence_copying`（`view.rs`）继续绿；本批未重新独立复算 `hash_tree`。
- **R-7 真机 rename 句柄风险**（DR-61 R-4）：Windows 下若 `.hoh` 有活句柄，整树 `rename` 会失败并冒泡成轮次错误。
  离线不可测，本批未触碰该路径。

**推断（未证）**

- **I-1**：【推断】真机上 DR-49 的截图取代现在会先写 `.hoh/evidence/.superseded.json`；若该目录不可写，
  取代会失败并让 `step_screenshot` 记一条 FAILED note（而不是"静默挪走、候选里仍出现旧图"）。
  离线只在 FakeAdapter/单测下验证了"记录在 rename 前"的代码顺序，未在真机观测。
- **I-2**：【推断】真机下一轮不会因为本批改动而多出/少出候选视图内容，除"角色自己用 `.stale-` 命名本轮产物"
  这一种情况（那是本批**有意**改变的行为）。
- **I-3**：【推断】§6 的 R-F 解释（DR-59 的 10:37:38 是 `mcp_server` 子树口径、DR-61 的 10:58:15 是整树含 `.git` 口径）
  是对"两个数字分别复现"的解释，不是对 DR-59 当时动作的实测。

**未验证**

- 未跑真机；**未验证 E1..E6 中任何一条**（尤其**不声称 E3**）；未做活体注入；未观察真机下
  `.superseded.json` 的实际写入位置/时序与 quarantine 的实际命名。
- 未在批次起点 `6a0c9a9` 之外重跑历史提交（不改写历史/不 checkout）；红-绿历史以本会话的真实提交 + 植入重放为准。
- `record` 写入失败（磁盘只读/权限拒绝）那条分支没有专门打红。
- `.hoh` 之外残留的隔离（R-1）与真机可用性（R-7）不在本批范围，也未测量。

---

## 8. 诚实披露

1. **第三件事没有"修前之红"**：任务书 §2 要求"每件事先写会失败的最小测试"。第 1、2 件有真实红（§3.1）；
   第 3 件固定的是一个**当前已为绿**的能力，任何"修前必红"的写法都是伪造。它的非空洞性由植入 ③ 的真实红给出
   （§4.3），我在 §3.1 已明确标注。
2. **植入 ③ 在测试文件里，不在生产代码里** —— 这是对任务书 §2"三处**仅生产代码**的植入"的**明确偏离**。
   理由：DEF-1 所指的 `walk` 就是 `tests/evidence_unreachable.rs` 自己的递归遍历；DR-61 §5 之所以这样写，
   是因为不变量必须由**真实文件系统遍历**来验证，而不能调用运行时函数（那会把"运行时认为该看到什么"
   当成"磁盘上有什么"）。生产代码里不存在"遍历整个工作区 cwd"这样一个函数可供收窄 ——
   `view::list_tree`/`policy::tree_manifest`/`hygiene::scan` 都不是这条不变量使用的遍历，
   收窄它们既不代表 DEF-1 的回归，也不能让自检变红。植入 ①② 是**纯生产代码**的（`src/runtime/view.rs`）。
   若验收者要求 ③ 也必须落在生产代码里，请把它判为**未满足**并退回：我据实报告，不伪造。
3. **一条既有测试被"替换并加强"，不是删除**：`copy_evidence_skips_superseded_files_and_keeps_them`
   （起点 `view.rs:320`）被 `copy_evidence_skips_a_recorded_supersession_and_copies_a_role_named_stale_file`
   取代。它的旧期望（裸 `.stale-` 名必须被跳过）与任务书要求的"`.stale-` 命名的本轮产物不再被误跳过"
   **正面冲突**，无法同时成立。替代测试保留了原有全部要点（记录在案者被跳过、字节保留、被跳过者不做 oversized 报告），
   并**新增**两处：子目录清单记录 vs 名字（更强）。view 模块的测试数 7 → 9
   （红提交那一次运行的真实计数：`running 9 tests` / `6 passed; 3 failed; 104 filtered out` = 替换 1 条为 3 条）。
4. **生产谓词 `is_expired_name` 被删除**（它已无调用者）。同名测试
   `the_superseded_marker_is_recognized_by_one_predicate` 保留原名、函数体换成更强的结构判据断言
   （断言计数 view 18→29、hygiene 51→62）；`hygiene.rs` 里 `quarantine_moves_...` 中原本调用它的那一句，
   改成字面量 `path.contains(".stale-")` —— 语义与旧谓词完全相同（旧谓词就是这一个子串判断）。
5. **CRLF 口径**：本仓 `core.autocrlf=true`，`git status`/`git diff`/`git hash-object` 都会做 CRLF→LF 归一化，
   看不见纯换行差异。因此"逐字节回退"的最强证据是我对**植入前逐字节备份**做的 `cmp`（identical），
   三法仍然全部成立（§4.4）。我没有让任何被改文件的工作树换行风格发生变化（交付时 `godot.rs` 仍为
   4546 行 CRLF / 0 行裸 LF，`git diff` 里没有任何"整文件重写"）。
6. **本批在工作区里引入了一个新的运行时文件**：`.hoh/evidence/.superseded.json`（取代清单；巢状时出现在被取代文件所在目录）。
   它在 `.hoh` 内 ⇒ 不参与 artifact 身份哈希；它被 `is_runtime_bookkeeping` 排除 ⇒ 不会进入任何视图；
   它随整树隔离一起被移走。但"多了一个文件"是事实，不能不说。
7. **摘要口径**：`runs`/`.workspace/mario` 的"未修改"证据是 **mtime + 目录摘要**（外层 `git ls-files` = 0 ⇒ 外层 diff 空判），
   脚本是我按 DR-59/DR-61 验收 §2 附注的 PowerShell `Sort-Object` 文化排序口径**重建**的；它把
   `runs/smoke-t6` 复算成与 DR-54/57/59/61 记录**逐字一致**的值，因此口径同源。
8. **本报告只写实测**：所有引用的命令输出、退出码、路径、摘要、mtime 均来自本会话真实运行；未编造输出或日期。
   `DECISIONS.md` 未改（任务书禁止）；`.spec/hof-rs/PRD-mario.md` 未改；`.workspace/mario/**` 与 `runs/**` 未写；
   未 push、未 stage；未新增依赖。
9. **scratch 清理**：报告定稿后删除 `C:\Users\wyl\AppData\Local\Temp\dr62-scratch\`，并以 `Test-Path` 复核（结果见文末补记）。
   与 DR-61 相同的口径选择：原始日志不再留存，但 §3/§4 给出了**逐字引文**与**可一键重放的植入编辑**
   （每处都是一行替换），验收者可自行重放并核对。
10. **一处工具面事实**：本会话没有 `pwsh`（只有 Windows PowerShell 5.1），摘要与 `Test-Path` 复核均用
    `powershell -NoProfile` 完成；`rev^` 类查询一律在 bash 做（D250 记录的 cmd `^` 转义陷阱，本批未遇到问题）。
11. **一处分属文件**：本批运行期间调度者新建了 `.spec/hof-rs/tasks/TASK-DR62-ACCEPT.md`（独立验收任务书）。
    它**不是我的产物**、不在我任何提交里，我未 touch / 未 stage / 未 commit 它。
    因此现在跑 `git status --porcelain` 会看到**两个**未跟踪文件（本报告 + 该任务书）；
    §6 里"status 为空"的引文是清理 scratch 之前那一刻的真实输出（当时两者都尚未落盘）。

### scratch 清理记录

- 路径：`C:\Users\wyl\AppData\Local\Temp\dr62-scratch\`（853 KB：日志 `red-view.txt`、`green-lib.txt`、
  `green-suite-1.txt`、`green-unreachable.txt`、`plant-1.txt`、`plant-2.txt`、`plant-3.txt`、`restore-green.txt`、
  `suite-baseline.txt`、`suite-final.txt`、`guards.txt`、`fn-inventory.txt`、`fn-base.txt`、`fn-head.txt`、
  `base-res.txt`、`fin-res.txt`、`engine-baseline.txt`、`engine-final.txt`、`digests-final.txt`；
  脚本 `digest.ps1`、`engine-check.sh`；逐字节备份 `head/`（回退用）与 `backup/`（起点用））。
- 清理（真实输出）：`rm -rf C:/Users/wyl/AppData/Local/Temp/dr62-scratch` 后
  `powershell -NoProfile -Command "Test-Path 'C:\Users\wyl\AppData\Local\Temp\dr62-scratch'"` → **False**。
- 说明：所有实验都在 `tempfile::tempdir()` 生成的**仓外临时工作区**里跑
  （测试输出里的 `%LOCALAPPDATA%\Temp\.tmpXXXX\workspace`），没有任何实验写入 `.workspace/mario/**` 或 `runs/**`
  （§6 摘要前后逐字一致即其证据）。
- 局限（如实）：与 DR-61 相同的口径选择——原始日志已删除，验收者只能核对本报告中的逐字引文；
  但三处植入都是**一行替换**（§4.1/§4.2/§4.3 写明了确切编辑），可原样重放复核，
  且交付树的状态由 `git hash-object` / `git status` / 本报告 §1 的门输出共同固定。
