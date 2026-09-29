# TASK-DR61-REPORT — 让上一轮证据**结构上不可达**（移出角色 cwd + 覆盖 `.hoh/evidence/**` + 阻断候选视图复制）

> 实现子代理报告。任务书：`.spec/hof-rs/tasks/TASK-DR61.md`（本文件是其 §4 要求的八节报告）。
> 上游输入（只当线索，判定以我自己的实测为准）：`.spec/hof-rs/tasks/TASK-DR59-ACCEPTANCE.md`（DEF-1/DEF-2）、
> `.spec/hof-rs/tasks/TASK-DR59-REPORT.md`（R-1/R-3）、`DECISIONS.md` D240/D247/D248。
> **离线**：未启动 Godot、未触碰任何外部/MCP 端口、未联网、未调模型端点、未 push。
> 基线（批次起点）：`5abddbd`（= `origin/master`）。本批 5 个提交，全部未 push。
> **不声称 E1..E6 中任何一条 met（尤其不声称 E3）** —— 那只能由真机轮次判定。

---

## 1. 结论 + 套件真实尾部/退出码

**结论：任务书 §1 的三件事全部落地，并留下一条红-绿回归不变量 + 两处受控植入。** 三条的落点见 §2，
同族路径的逐条实测判定见 §3。

门（真实输出，`F:\moonbit-hof-rs`，树 = `be8d115`）：

```
$ cargo test --offline
...
   Doc-tests hof_rs
running 0 tests
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
EXIT=0                       # bash PIPESTATUS[0]
```

聚合口径 = `grep -E '^test result:' | awk`（与 DR-59 验收同口径）：

| 口径 | 基线（DR-59 交付） | 本批（`be8d115`） |
|---|---|---|
| targets | 38 | **39**（+`tests/evidence_unreachable.rs`） |
| passed | 359 | **366** |
| failed | 0 | **0** |
| ignored | 7 | **7**（未增） |
| `^warning` 行 | 0 | **0** |
| exit | 0 | **0** |

+7 的来源：新集成目标 3 条（`tests/evidence_unreachable.rs`）+ lib 净 +4（`src/runtime/hygiene.rs` 净 +2、
`src/runtime/view.rs` +2）。`#[ignore` 在树中出现 **8** 次 = 7 个属性 + 1 个文档注释（与 DR-59 记录一致），
即真机目标 `godot_smoke` 的 E0–E6 仍为 ignored，**未跑真机**。

提交（起点 `5abddbd`，未 push）：

| 提交 | 角色 |
|---|---|
| `c139194` | **红**：通配 walk 仍可达上一轮证据；`copy_evidence` 仍复制 `.stale-` 件 |
| `ab869e5` | 实现 v1（curated 5 区 + 移出 cwd + 跳过 `.stale-`），全量绿 |
| `0d0f391` | **红**：把 seed 加宽到真实工作区里**每一个** `.hoh` 同族路径后，`.hoh/SCAFFOLD.md` 仍可达 |
| `92e4aff` | 实现 v2：隔离**整个 `.hoh`**（curated 列表实测不完备，见 §3） |
| `be8d115` | 把不变量加宽到"整个角色 cwd"，任意位置的隔离物都必须红 |

---

## 2. 三件事各自的落点（文件:行）与理由；隔离物移到哪里

### 2.1 把隔离物移出角色 cwd

- `src/runtime/hygiene.rs:457-533` `pub fn quarantine_previous_evidence(workspace: &Path, run_dir: &Path) -> anyhow::Result<Vec<QuarantinedArea>>`
  - 目标 `src/runtime/hygiene.rs:470` `let root = run_dir.join(QUARANTINE_DIR)`（`QUARANTINE_DIR = "quarantine"`，`:350`），
    每个被移动的条目 → `root/<name>.stale-<stamp>[-attempt]`（`stale_name`，`:391`）。
  - 移动只用 `std::fs::rename`（`:527`），**绝不删除**；名字窗口（64 次）耗尽则 `anyhow::bail!`（`:516-521`），
    不回退删除（保留 DR-59 取向）。
- 调用点 `src/runtime/run_loop.rs:356`，位于 `adapter.initialize`（`:337`）**之后**、`A_0` 快照（`:421`）与
  所有角色（Planner `:520` / Developer `:717` / Tester `:1063`）**之前**，每轮一次。
- 隔离物相对角色 cwd 的位置（这是本批的核心）：
  - Developer 的 cwd = `workspace`（`run_loop.rs:717`）；Planner/Tester 的 cwd = `runs/<run_id>/iter-<n>/{planner-view,candidate}`（`:520`/`:1063`）。
  - 隔离物 = `runs/<run_id>/quarantine/**`，是 `workspace` 的**兄弟**、是 `iter-<n>` 的**兄弟**。
    即 `target.starts_with(workspace) == false`，且不在任何 `iter-<n>/*` 之内 ⇒ **任何角色 cwd 的递归遍历都到不了它**。
    测试直接断言这两点（`tests/evidence_unreachable.rs` 的 `!quarantine.starts_with(&workspace)`；`src/runtime/hygiene.rs` 的单测断言 target 在 run 的 `quarantine/` 下且不在 workspace 下）。
- **结构前提会被强制检查，而不是靠约定**：`src/runtime/hygiene.rs:422-431` `destination_is_inside_workspace()`
  （先按 `absolute_path` 词法判定，再在两端都存在时 `canonicalize` 判定，防止 symlink/junction 把目标送回 cwd），
  两处 guard 在 `:474-492`：目标在 workspace 内 ⇒ `bail!`（且回滚刚创建的空目录）。单测
  `quarantine_refuses_a_destination_inside_the_workspace`（`hygiene.rs:893`）固化这条。
  ⇒ 任务书 §3「不得用加白名单/加约定代替结构隔离；做不到就停下上报」在这里变成：**做不到就大声失败**。
- 为什么放在 `runs/<run_id>/quarantine`（而不是 `runs/<run_id>.quarantine` 或仓外）：`cli_impl.rs:823`
  的 `latest_run_id` 把 `runs/` 下的**目录**当 run 候选排序取最后一个 ⇒ 一个 `runs/<id>.quarantine` 兄弟目录
  会被当成"最新的 run"。放在 run 目录内既避开这一点，又让隔离物落在 DR-19 的保密扫描 `runs/<id>/**`
  覆盖范围内（`secrets::redact_tree`）。代价是它也在本轮 run 目录里（DR-59 验收 §8.2 已提示的权衡），
  已列入 §7 的遗留项。

### 2.2 把 `.hoh/evidence/**` 纳入隔离（最终：纳入**整个 `.hoh`**）

- `src/runtime/hygiene.rs:371` `pub const QUARANTINE_AREAS: &[&str] = &[ARTIFACT_DIR]`，`ARTIFACT_DIR = ".hoh"`（`:324`）。
- 也就是说：**一次开轮隔离动作**把上一轮留在工作区里的**整个 `.hoh` 树**移到
  `runs/<run_id>/quarantine/.hoh.stale-<stamp>[-attempt]/`。`.hoh/evidence/**`、`.hoh/deterministic/**`、
  `.hoh/args/**`、`.hoh/scratch/**`、`.hoh/evidence.json`、`.hoh/skills/**` 全部随之移出。
- **为什么从 curated 5 区改成整树（这是本批最重要的一次自我推翻，有实测反例）**：我先按
  `.hoh/{deterministic,evidence,evidence.json,args,scratch}` 做了 curated 隔离并全量绿（`ab869e5`）；
  随后把回归测试的 seed 加宽到"真实工作区里存在的每一个 `.hoh` 同族路径"（`tests/evidence_unreachable.rs:42`，15 个 seed，
  来源见 §3），立刻实测出反例：**`.hoh/SCAFFOLD.md` 在关掉隔离时仍可被 walk 读到**，因为运行时只把它注入
  **角色视图**（`run_loop.rs:498`），从不写进 workspace，`developer_inputs`（`:681-697`）也不含它。
  ⇒ 任何 curated 列表都无法让"对 `.hoh` 的遍历拿不到上一轮字节"这句话成立（角色可在 `.hoh/<任意名>` 落文件）；
  只有移动整树才行。而 `.hoh` 本就是运行时的 artifact 目录，且在 artifact 身份哈希里被整体排除
  （`src/runtime/policy.rs:37-45`，`merged()` 恒含 `.hoh`），移动它不扰动 `A_0`/`A_t`。
- 整树移出的安全性（离线可证部分）：两个 adapter 的 `initialize` 都不写 `.hoh`
  （`GodotAdapter::initialize` `src/adapter/godot.rs:3292-3336`；`FakeAdapter::initialize` `tests/common/mod.rs:400`），
  且每一条生产者路径都自带 `create_dir_all`（`run_battery_pass` 的 `deterministic_dir`、`FakeAdapter::build_check`、
  截图 materialize 路径），`write_inputs`（`src/runtime/view.rs:50-58`）也会建父目录 ⇒ 一个没有 `.hoh` 的工作区是正常起点
  （既有 "fresh workspace" 与 `screenshot_materializes_an_inline_base64_png` 等测试即为此形态）。

### 2.3 阻断候选视图复制

- `src/runtime/view.rs:131`：`if rel.split('/').any(crate::runtime::hygiene::is_expired_name) { continue; }`
  —— `copy_evidence` 跳过任何路径分量带 DR-49 `.stale-` 标记的文件；谓词唯一落点
  `src/runtime/hygiene.rs:383` `pub fn is_expired_name(name) -> bool { name.contains(".stale-") }`。
- 两种"过期/被隔离"情形分别由两件事覆盖：
  1. **被隔离者**（上一轮遗留）：开轮时整树已移出 `.hoh`（§2.2），`copy_evidence` 的源目录 `workspace/.hoh/evidence`
     里根本不存在它们 ⇒ 不可能进入候选视图；
  2. **过期件**（轮内 DR-49 `invalidate_artifact` 把旧截图就地改名成 `frame-00.png.stale-<ts>`，`src/adapter/godot.rs:1088` 一带）：
     由 `view.rs:131` 跳过。为什么不做成"只复制本轮产出"：`copy_evidence` 只面对文件系统，没有"本轮"的时间概念，
     而 `.stale-` 正是仓内既有的"已作废、不可信"标记（DR-49 造、DR-59/DR-61 移），跳过它既最小又语义一致。
- 跳过 ≠ 删除：源文件原地保留（单测 `src/runtime/view.rs:320` 断言源文件仍在、目标里没有）。
- **冻结候选的哈希/清单不受影响**：`.hoh` 在 `HashExcludes::merged()` 里被整体排除
  （`src/runtime/policy.rs:37-45`），因此"复制了哪些 `.hoh/evidence/*`"与候选身份无关。实测固化：
  `src/runtime/view.rs:359` `the_candidate_identity_is_unaffected_by_evidence_copying` 断言
  在候选视图里放入证据文件前后 `hash_tree(&candidate, &excludes)` **完全相等**。

---

## 3. 同族路径的逐条实测判定

**测量方法（两条独立实测 + 一条代码核实，不是列举猜测）**

- **M1 真实残留清单（只读）**：`runs/smoke-t7-experiment/pre_run_workspace_inventory.txt`（smoke-t6 留给 smoke-t7 的开工前清单）
  与 `.workspace/mario/.hoh` 的真实目录内容。这是在读两条真机基线的工件，未修改它们。
- **M2 我自己的双轮复现 + 逐字节 seed**：`tests/evidence_unreachable.rs:42` `SEEDS` 用 15 个**唯一字符串**分别落在
  15 条 `.hoh` 路径上，跑一整轮，然后 (a) 对 `<workspace>/.hoh` 与整个 `<workspace>` 做 **walkdir 递归遍历**，
  (b) 对 Planner/Developer/Tester **被调用那一刻**的整 cwd 快照逐字节比对。"能读到"的定义 = walk/快照里出现
  **与 seed 逐字节相同**的内容。
- **M3 关掉隔离（植入 P1）后的 walk keys**（下面"P1 下仍可见"一列直接来自
  `plant-p1-int.txt` 的真实 reached keys）。

判定表（`.hoh` 下全部同族路径）：

| 路径 | M1 真实存在? | 关掉隔离时是否仍被 walk 读到 | 运行期是否被当轮重写 | 判定 |
|---|---|---|---|---|
| `.hoh/deterministic/**` | 存在（inventory：`battery.json` 等；mario 12 个文件） | **读到**（修前红：`deterministic.stale-1790685590/battery.json`；DR-59 验收 probe A 同形） | 否（DR-24 轮内二次 pass 会 `remove_dir_all(.hoh/deterministic)`，`run_loop.rs:274,814`） | **纳入隔离**（原 DR-59 已处理；整树覆盖） |
| `.hoh/evidence/**` | 存在（inventory：`frame-00.png` = 4246 B；mario 另有 `.stale-` 件） | **读到**（P1：`evidence/frame-00.png`、`evidence/replay/round-one.json`） | 否 | **纳入隔离**（本批目标 DEF-2） |
| `.hoh/evidence.json` | **不存在**（inventory 实测没有） | P1 下读到我的 seed（说明一旦存在就会被读到） | Developer 会重写（`run_loop.rs:968` 附近注入 `.hoh/evidence.json`） | **纳入隔离**（真实轮次通常是 no-op；角色可写，故结构性闭合） |
| `.hoh/args/**` | 存在（inventory 多个；mario `args/` 共 34 文件） | **读到**（P1：`args/probe.json`） | 否 | **纳入隔离**（内容 = 上一轮 MCP 调用载荷，如 `{"max_lines":50}`） |
| `.hoh/scratch/**` | 存在（inventory 大量 scratch/*，含 `engine_written.godot`、`project.godot.bak`） | **读到**（P1：`scratch/gtools.txt`） | 否 | **纳入隔离**（DR-28 probe scratch） |
| `.hoh/SCAFFOLD.md` | 未在 M1 清单出现（运行时只写进**视图**，`run_loop.rs:498`） | **读到**（P1 的 reached keys 明确含 `SCAFFOLD.md`） | **否** | 归整树隔离 —— 这正是 curated 列表不完备的实测反例 |
| `.hoh/TASK.md`、`.hoh/plan.md`、`.hoh/TOOLS.md`、`.hoh/EVIDENCE_HISTORY.md`、`.hoh/PROJECT_MAP.md`、`.hoh/skills/**` | 存在（inventory 全部有） | 路径存在但**内容不是 seed**（M2 按字节比对，首命中落在 `evidence/frame-00.png`） | **是**：`write_inputs(&workspace, developer_inputs)`（`run_loop.rs:681-697`，含 `skill_inputs()` `:151-156`）在 Developer 调用前整体覆盖 | 判定为"当轮被重写、非上一轮残留"；仍随整树一起移出（无副作用，当轮会重写） |

**边界（必须一起说清）**：

- 判定基于"遍历 `.hoh` / 遍历角色 cwd"这一定义。**`.hoh` 之外**的工作区上一轮残留**不在**本批不变量内，
  本批未做任何相关测量（不在任务书 §2 的不变量范围）——列为 §7 未验证项。
- 关掉隔离时，`deterministic` 家族的"轮末 walk"未必命中：DR-24 的轮内二次 pass 会把 `.hoh/deterministic`
  整个删掉重建（`run_loop.rs:274`），所以旧字节在**轮末**可能已不在盘上。该家族真正的泄漏时点是
  **Developer 调用之前**（DR-59 验收 probe A / DR-59 自身 P1 在 `:113` 报出
  `[".hoh/deterministic/battery.json", ".hoh/deterministic/raw/input_channel_probe.json"]`）。
  我的测试在该时点用 Planner/Developer 快照逐字节比对覆盖它（§4/§5）。

---

## 4. 不变量的 TDD 证据（红 → 绿 → 两处植入）

### 4.1 红（生产代码未动；提交 `c139194`）

不变量（任务书 §2 原文）：**对 `.hoh` 做通配/遍历读取，不得命中上一轮的证据字节。**

`tests/evidence_unreachable.rs`（新目标，3 条）+ `src/runtime/view.rs`（新增 1 条单测）先落盘，
真实失败输出（`red-unreachable.txt`）：

```
running 3 tests
test a_clean_round_start_creates_no_quarantine_directory ... ok
test a_wildcard_walk_of_hoh_cannot_reach_the_previous_rounds_evidence ... FAILED
test the_tester_candidate_view_never_carries_the_previous_rounds_evidence ... FAILED

---- a_wildcard_walk_of_hoh_cannot_reach_the_previous_rounds_evidence stdout ----
panicked at tests\evidence_unreachable.rs:180:9:
DR-61: the wildcard walk of `.hoh` still reaches the previous round's .hoh/deterministic/battery.json
  at ["deterministic.stale-1790685590/battery.json"];
  reached keys: [..., "deterministic.stale-1790685590/battery.json",
  "deterministic.stale-1790685590/raw/input_channel_probe.json", "evidence.json",
  "evidence/frame-00.png", "evidence/replay/round-one.json", "args/probe.json",
  "scratch/gtools.txt", ...]

---- the_tester_candidate_view_never_carries_the_previous_rounds_evidence stdout ----
panicked at tests\evidence_unreachable.rs:258:5:
DR-61/DEF-2: the previous round's frame-00.png is still in the frozen candidate view:
  [".hoh/evidence/frame-00.png", ".hoh/evidence/replay/round-one.json"]

test result: FAILED. 1 passed; 2 failed; 0 ignored; ... finished in 41.77s
EXIT=101
```

`red-view.txt`（同一提交）：

```
test runtime::view::tests::copy_evidence_skips_superseded_files_and_keeps_them ... FAILED
panicked at src\runtime\view.rs:325:9:
DR-61: a superseded evidence file must not reach the frozen candidate
test result: FAILED. 6 passed; 1 failed; ... EXIT=101
```

⇒ 三条新行为各自"因当前行为而红"，且第一条红的 reached keys **就是**验收者 probe A 的反例路径同形
（`.hoh/deterministic.stale-<ts>/…`），并额外实测出 `evidence.json`/`args`/`scratch` 同族可达。

### 4.2 绿（`ab869e5`，随后加强：`0d0f391`/`92e4aff`/`be8d115`）

`cargo test --offline --test evidence_unreachable --test evidence_isolation`（最终树）：

```
test result: ok. 3 passed; 0 failed; 0 ignored; ... (evidence_isolation)
test result: ok. 3 passed; 0 failed; 0 ignored; ... (evidence_unreachable)   EXIT=0
```

全量：`39 / 366 passed / 0 failed / 7 ignored / EXIT=0`（§1）。

### 4.3 植入 P1 —— 把隔离**关掉**（只改生产代码）

植入：`src/runtime/hygiene.rs` 的 `should_quarantine` 体 → `let _ = live; false`（一行，测试未动）。

- 集成（`plant-p1-int.txt`，最终树）：

```
test a_wildcard_walk_of_hoh_cannot_reach_the_previous_rounds_evidence ... FAILED
panicked at tests\evidence_unreachable.rs:204:9:
DR-61: the wildcard walk of `.hoh` still reaches the previous round's .hoh/evidence/frame-00.png
  at ["evidence/frame-00.png"];
  reached keys: [..., "SCAFFOLD.md", ..., "args/probe.json", "deterministic/battery.json", ...,
  "evidence.json", "evidence/frame-00.png", "evidence/replay/round-one.json", ...,
  "scratch/gtools.txt", ...]
---- the_tester_candidate_view_never_carries_the_previous_rounds_evidence ... FAILED
panicked at tests\evidence_unreachable.rs:311:5:
DR-61/DEF-2: the previous round's frame-00.png is still in the frozen candidate view:
  [".hoh/evidence/frame-00.png", ".hoh/evidence/replay/round-one.json"]
test result: FAILED. 1 passed; 2 failed; ... EXIT=101
```

- 单元层（`plant-p1-lib.txt`）：`--lib runtime::hygiene` → `test result: FAILED. 10 passed; 3 failed`，
  红在 `quarantine_moves_the_whole_artifact_tree_out_of_the_workspace`（`left: [] / right: [".hoh"]`）、
  `a_second_quarantine_in_the_same_second_does_not_collide`、`quarantine_refuses_a_destination_inside_the_workspace`。
- 回退（三法证明）：`cp` 回保存副本 → `cmp` identical；`git status --porcelain` 空（此时唯一 dirty 文件是我
  随后提交的测试加宽）；`git diff --stat` 对 `src/runtime/hygiene.rs` 空；`git hash-object src/runtime/hygiene.rs`
  = `git rev-parse HEAD:src/runtime/hygiene.rs` = `9de24a82981bc73de7f63de4631366db8140aaeb`。
  （本批最终 HEAD `be8d115` 上同样复核：`git status --porcelain` 空、`git diff --stat` 空、hash 相等。）

### 4.4 植入 P2 —— 把隔离物**放回 cwd 内**（只改生产代码）

植入（两行，测试未动）：`let root = run_dir.join(QUARANTINE_DIR)` → 目标改到 cwd 内，并同时把两处
`is_inside` guard 改成不生效（`if false && …`）。**必须同时关掉 guard 才能做到"放回 cwd 内"** ——
这正是 guard 的设计目的（§2.1），如实披露为"一次植入两处"。

- **变体 (a)：`<workspace>/quarantine`**（`plant-p2a-int.txt`）→ 不变量**红**：

```
panicked at tests\evidence_unreachable.rs:227:9:
DR-61: a walk of the role's cwd still reaches the previous round's .hoh/deterministic/battery.json
  at ["quarantine/.hoh.stale-1790687373/deterministic/battery.json"]
---- the_tester_candidate_view_never_carries_the_previous_rounds_evidence ... FAILED
DR-61/DEF-2: the frozen candidate view still carries the previous round's evidence bytes
EXIT=101
```

  附带实测（同一植入、加宽断言之前的日志 `plant-p2a-hole.txt`）：Planner 视图断言先红 ——
  `DR-61: the Planner's view still carries the previous round's .hoh/deterministic/battery.json`。
  原因是**视图拷贝只排除 `.hoh`/`.git`**（`policy.rs:37-45`），cwd 内任何别的目录都会被原样复制进角色视图，
  即"隔离物留在 cwd 内"不仅可被遍历读到，还会被主动搬进 Planner/Tester 的视图。

- **变体 (b)：`<workspace>/.hoh/quarantine`**（即 DR-59 的位置对应的嵌套写法，`plant-p2b-int.txt`）→ 轮次直接失败：

```
panicked at tests\evidence_unreachable.rs:179:10:
the round itself must still run: 拒绝访问。 (os error 5)
```

  即把一个目录 rename 进它自己的子孙在操作系统层就不可能（access denied）⇒ 该形态在本实现里是"响亮失败"，
  而不是静默降级。

- 回退（三法证明）：`cp` + `cmp` identical；`git hash-object` = `git rev-parse HEAD:src/runtime/hygiene.rs`
  = `9de24a82…`；回退后复跑 `--test evidence_unreachable` → `3 passed; 0 failed; EXIT=0`（`restore-green.txt`）。

---

## 5. DEF-2 的测试证据（候选视图里不再出现上一轮的 evidence）

- **集成测试** `tests/evidence_unreachable.rs:288`
  `the_tester_candidate_view_never_carries_the_previous_rounds_evidence`：
  第 1 轮真跑（断言它确实留下 `.hoh/deterministic/build.json`）→ 把"上一轮的 evidence harvest"
  `.hoh/evidence/frame-00.png` 与 `.hoh/evidence/replay/round-one.json` 落到工作区 → 第 2 轮开轮 → 取 **Tester 被调用那一刻**的
  候选视图快照，断言：
  1. 候选视图**不含** `.hoh/evidence/frame-00.png`，且**无**任何文件字节等于两个 marker；
  2. 正向对照：**本轮**的 `.hoh/deterministic/**` 仍在候选视图里（DR-36 的拷贝机制没被弄坏）；
  3. 两个 marker 在 `runs/run-2/quarantine/**` 下**逐字节存在**（移开、不是删除）；
  4. 再 walk 一次 `<workspace>/.hoh`，marker 不可达。
  修前真实红（§4.1）给出的正是 DEF-2 的形态
  `[".hoh/evidence/frame-00.png", ".hoh/evidence/replay/round-one.json"]`，与验收者 probe A 的
  `tester sees previous-round PNG verbatim = true` 同形；修后绿。
- **单元测试（跳过机制本身）** `src/runtime/view.rs:320`
  `copy_evidence_skips_superseded_files_and_keeps_them`：`frame-00.png` 与 `frame-00.png.stale-<ts>`、
  `replay/round.json` 与 `replay/round.json.stale-<ts>` 同时在源目录 → 目标里只有非 `.stale-` 件；
  **源目录里的 `.stale-` 件仍在**；且 `oversized` 报告里不出现被跳过者（不会把"没复制"谎报成"复制了且过大"）。
- **哈希不受影响** `src/runtime/view.rs:359`（§2.3 已述）。
- **未覆盖路径（如实列出）**：`run_loop.rs:991-997` 把 `.hoh/deterministic/**` 复制进候选用的是
  `view::copy_tree`（`src/runtime/view.rs:62`），它**没有** `.stale-` 过滤。本批未改（避免扰动 DR-59/DR-24 的既有语义）：
  开轮隔离之后，轮内 `.hoh/deterministic` 只会出现本轮产物，除非角色自己写了 `.stale-` 名。列为 §7 R-3。

---

## 6. 禁区自查（真实输出）

引擎树未改（**用嵌套仓 + mtime/摘要**，因为外层不跟踪它，D242）：

```
$ git ls-files godot-mcp | wc -l          => 6484     # pathspec 真命中（>0）
$ git ls-files godot-mcp/godot | wc -l    => 0        # 外层对引擎树是空判 => 外层 diff 无意义
$ git -C godot-mcp/godot status --porcelain | wc -l   => 0
$ git -C godot-mcp/godot rev-parse HEAD   => fc63af77c33368c4a1bb839c95d19750554f63a3
$ git diff --stat 5abddbd..HEAD -- godot-mcp          => (空)
$ sha256 godot-mcp/godot/modules/mcp_server/tools/running_game_test_execution.cpp
    => ece4ae63d445719b662a6e9ad99ba80bebba3ea3c94468094c7e9cb820ddff3f   # 与 DR-59 记录逐字一致
$ find godot-mcp/godot -type f -newermt '2026-09-29 19:00' | wc -l   => 0   # 我的首个提交 20:40
$ find godot-mcp/godot -type f -newermt '2026-09-29 11:00' | wc -l   => 0
```

引擎树最新 mtime 实测 = `2026-09-29 10:58:15`，落在
`godot-mcp/godot/.git/refs/remotes/origin/feature/mcp-server-module-rebuild`（远端跟踪 ref，非源码）；
源码侧最新 = `tests/data/translations.*.translation` 10:49:37。（与 DR-59 验收记录的 10:37:38 不同，见 §8.7。）

`runs/**` 未动、`.workspace/mario/**` 未改（**两者都不被外层跟踪**：`git ls-files runs` = 0、
`git ls-files .workspace` = 0 ⇒ 外层 `git diff` 对它们是空判，故改用"摘要 + mtime"，口径 = DR-59 验收 §2 附注
的 PowerShell `Sort-Object` 口径，脚本 `digest.ps1` 在 scratch 目录）：

```
基线（批次开始时，我自测与他方记录一致）：
  .workspace/mario  files=259  digest=4e494547416b2e87ba025d686afef9447d4f92c027917d1790e6fc9deaeaa84a newest=2026-09-29 14:32:28
  runs              files=5147 digest=01ff775e36935d3d92dab6919fe030389a8ff53483c52e87288ad711ec840dc3 newest=2026-09-29 14:44:16
最终（全部写操作结束、全量套件之后，逐字相同）：
  .workspace/mario  files=259  digest=4e494547416b2e87ba025d686afef9447d4f92c027917d1790e6fc9deaeaa84a newest=2026-09-29 14:32:28
  runs              files=5147 digest=01ff775e36935d3d92dab6919fe030389a8ff53483c52e87288ad711ec840dc3 newest=2026-09-29 14:44:16
```

其余禁区（真实输出）：

```
$ sha256sum .spec/hof-rs/PRD-mario.md
4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a   # 与 DR-59 记录一致
$ git diff --stat 5abddbd..HEAD -- Cargo.toml Cargo.lock DECISIONS.md .spec/hof-rs/PRD-mario.md
(空)                                    # 无新依赖、未改 DECISIONS.md、未改 PRD
$ git diff --stat 5abddbd..HEAD     # 树 = be8d115（报告提交之前；报告文件本身是其后唯一新增）
 src/runtime/hygiene.rs        | 402 +++++++++++++++++++-------
 src/runtime/run_loop.rs       |  42 +++--
 src/runtime/view.rs           |  73 ++++++++
 tests/evidence_isolation.rs   | 128 +++++++++---
 tests/evidence_unreachable.rs | 370 +++++++++++++++++++++++++++++++
 5 files changed, 910 insertions(+), 105 deletions(-)
$ git status --porcelain        => ?? .spec/hof-rs/tasks/TASK-DR61-REPORT.md   # 只有本报告未跟踪
$ git diff --cached --stat      => (空，未 stage)
$ git rev-parse origin/master   => 5abddbd88ec2f8a3095688ba52d76792f7149f33   # 批次起点
$ git log --oneline origin/master..HEAD | wc -l => 5                            # 未 push
```

**离线**：全程只跑 `cargo test --offline` / `cargo build --offline` 语义的命令；**未执行任何 godot 可执行文件**；
真机目标 7 条（`godot_smoke` 的 E0–E6，`#[ignore]`）保持 ignored 未被运行（ignored 7→7）。
披露：既有套件内含 **loopback-only** 测试（如 `tools::endpoint::tests::the_loopback_endpoint_round_trips_through_its_port`、
`doctor_probe` 系列）会绑定 127.0.0.1 的临时端口——那是套件原有行为，与本批改动无关；我没有连接任何外部服务、
没有触碰 Godot/MCP 端口。

**scratch 工作区**：`C:\Users\wyl\AppData\Local\Temp\dr61-scratch\`（全部原始日志：红/绿/加宽红/三次植入/回退/摘要脚本
`digest.ps1`/基线摘要/两个 `hygiene.rs` 字节备份）。清理记录见文末。

---

## 7. 遗留风险与未验证项（严格区分**实测** / **推断**）

**实测（有原始输出）**

- **R-1 轮内泄漏仍在**：隔离**每轮一次**。迭代 t≥2 的 Developer 仍能读到迭代 t-1 的电池证据（轮内反馈，设计如此；
  与 DR-59 的 R-2 同）。我的不变量测试只覆盖**跨轮**。
- **R-2 不变量范围限于 `.hoh`**：`.hoh` 之外的上一轮工作区残留（角色在项目根写的任意文件）**不在**本批不变量内，
  本轮**未做任何相关测量**。"结构上不可达"这句话在本批里只对 `.hoh`（以及证据类家族）成立。
- **R-3 `copy_tree` 无 `.stale-` 过滤**：`run_loop.rs:991` 用 `view::copy_tree` 复制 `.hoh/deterministic`，
  该函数没有跳过谓词（只有 `copy_evidence` 有）。本批未改（避免扰动 DR-24/DR-59 既有断言意图）；未在真实轮次观测到触发形态。
- **R-4 整树 rename 的句柄依赖（同 DR-59 风险面，范围扩大）**：真机上 `<workspace>/.hoh` 若有进程持有句柄
  （`.hoh/deterministic/mcp-sync.json`、`mcp-errors.jsonl` 是 MCP 通道写过的文件），Windows 下 rename 会失败；
  失败会经 `?` 冒泡成轮次错误（**响亮失败，不静默降级**）——这是有意的取舍。
- **R-5 无 GC**：每轮在 `runs/<id>/quarantine/` 留一个 `.hoh.stale-<ts>`，与 DR-59 的 `.stale-` 累积同族，无清理。
- **R-6 `.stale-` 跳过是按名字的约定**：若角色给**本轮**产物起名含 `.stale-`，该文件不会进候选视图，
  Tester 会把它当缺失/不可见（既有 DR-36 的 oversized 报告也不会出现）。本轮**未见真实触发**；属约定性缺口（推断性后果）。
- **R-7 警告面变化**：命中的 token 仍是 `previous_evidence_quarantined`（`run_loop.rs:55`），但每轮
  `warnings.log` 现在按**被移动的条目**写行（本批 1 条：`.hoh`），文案由 DR-59 改为 DR-61；干净开轮不产生任何新警告，
  也不创建空的 `quarantine/` 目录（测试固化）。

**推断（未证）**

- **I-1**：【推断】真机下一轮里模型不再把上一轮的 `pid 108432` / "the editor is not clean" / `os error 10061`
  带进上下文。离线只证"角色 cwd 的遍历与角色视图都拿不到"，真机行为只能由下一轮真机轮次判定。
- **I-2**：【推断】整树移出对真机的 editor/MCP 工具链无副作用（离线只在 FakeAdapter 与 fixture tool channel 下验证；
  `evidence_battery` 38 条 + `launchable_gate` 12 条等离线真适配器路径全绿）。

**未验证**

- 未跑真机；**未验证 E1..E6 中任何一条**（尤其**不声称 E3**）；未做活体注入；未观察真机下 quarantine 的实际命名与累积。
- 未在 `5abddbd` 上重跑全量套件取得 359 基线（会改动 HEAD/worktree）；359/0/7 沿用 DR-59 交付记录 +
  `ignored` 计数与 `#[ignore` 出现次数（8 = 7 属性 + 1 注释）的交叉核对。
- 未复跑 `c139194` 的历史红（不 checkout、不改写历史）；以保存的真实日志 + 之后的植入重放替代（§4）。
- `.hoh` 之外的工作区残留（R-2）与 `copy_tree` 的 `.stale-` 缺口（R-3）未做测量。

---

## 8. 诚实披露

1. **红-绿次序**：`c139194` 与 `0d0f391` 都是**真红**（提交里只有测试，生产代码未动，输出见 §4.1/§4.3 引文）。
   但 `src/runtime/hygiene.rs` 内**新增/改写**的单测在旧签名上根本无法编译（`quarantine_previous_evidence`
   增加了 `run_dir` 参数、返回值由 `Option<String>` 变 `Vec<QuarantinedArea>`），因此它们**不存在"先红"历史**——
   其非空洞性由 P1/P2 植入实测（§4.3/§4.4）。这与 DR-59 的 H-1 同类，不粉饰。
2. **我自己推翻了自己第一版设计**：`ab869e5` 的 curated 5 区方案全量绿之后，我把 seed 加宽到"真实工作区里每一个
   `.hoh` 同族路径"，实测出 `.hoh/SCAFFOLD.md` 不被当轮重写（P1 的 reached keys 实证），才改成整树隔离（`92e4aff`）。
   不是一次做对；`0d0f391` 就是这次自我推翻的**真红**记录。
3. **一处测试能力自我修正**：P2 变体 (a) 之后我担心"只 walk `.hoh`"会漏判 cwd 内的隔离物，于是加了"walk 整个 cwd"
   （`be8d115`）。事后实测（`plant-p2a-hole.txt`）表明该变体**本来就会红**（Planner 视图先红，因为视图拷贝只排除
   `.hoh`/`.git`）——加宽断言仍保留（更贴近不变量本意），但我不声称"没有它就漏判"。
4. **未被独立打红的断言**：Developer 视图逐字节断言没有被单独打红（同形的 Planner 断言由 P2a 打红；Tester 视图由
   集成测试 B 打红）。如实标注，不把它写成"已证明非空洞"。
5. **改写而非放宽既有测试**：`tests/evidence_isolation.rs` 的两条断言**被改写**（原断言的落点是"`.stale-` 目录出现在
   Developer cwd 内"，与本批目标正相反），改写后更强：从"视图里存在 `.stale-`"变为"视图里**不得**出现 `.stale-`"，
   并把逐字节保留断言从"harness 快照里看到"升级为"从 `runs/<id>/quarantine` **磁盘**读取比较"。我没有删除或加 `#[ignore]`
   任何测试；`ignored` 7→7。但"那两条断言确实被改了"必须明说。
6. **摘要口径**：`.workspace/mario` 与 `runs` 的"未修改"证据是 **mtime + 目录摘要**（因为 `git ls-files` = 0，
   外层 diff 是空判）。摘要依赖 PowerShell `Sort-Object` 的文化排序（DR-59 验收 §2 附注已记录该口径），
   与 DR-57/DR-59 记录逐字一致是我能给出的最强证据。
7. **引擎 mtime 的历史差异**：我实测"最新引擎 mtime = 10:58:15（`.git` 远端 ref）"，与 DR-59 验收记录的 10:37:38 不同。
   我不解释历史差异；我给出的未改动证据是：`git -C godot-mcp/godot status --porcelain` 0 行、嵌套 HEAD 未变、
   关键源码 sha 与 DR-59 记录相同、**0 个引擎文件晚于 19:00（我的批次起点）**。
8. **本报告只写实测**：所有引用的命令输出、退出码、路径、摘要均来自本会话真实运行；未编造输出或日期。
   `.spec/hof-rs/PRD-mario.md` 与 `DECISIONS.md` 未改；本批未 push、未 stage 任何东西。

### scratch 清理记录

- 路径：`C:\Users\wyl\AppData\Local\Temp\dr61-scratch\`（日志 `red-*.txt`、`green-*.txt`、`plant-p*.txt`、
  `restore-green.txt`、`suite-green.txt`、`suite-final.txt`、`baseline-*.txt`、`final-*.txt`、`digest.ps1`、
  两个 `hygiene*.orig` 字节备份、两个 `.head-blob.txt`）。
- 清理：报告定稿后删除该目录，并以 `Test-Path` 复核。**实测（删除后立即运行）**：
  `Test-Path 'C:\Users\wyl\AppData\Local\Temp\dr61-scratch'` → **False**（PowerShell 5.1，`powershell -NoProfile -Command`）。
  删除后 `git status --porcelain` 只剩 `?? .spec/hof-rs/tasks/TASK-DR61-REPORT.md`（本报告）。
- 说明：所有实验都在 `tempfile::tempdir()` 生成的**仓外临时工作区**里跑（测试输出里的
  `%LOCALAPPDATA%\Temp\.tmpXXXX\workspace`），没有任何实验写入 `.workspace/mario/**` 或 `runs/**`。
- 局限（如实）：原始日志已删除，验收者只能核对本报告中的引文；这是与 DR-59 相同的口径选择。
