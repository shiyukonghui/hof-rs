# TASK-DR62-ACCEPTANCE — DR-62（三处"靠约定"缺口）**独立验收报告**

> 独立验收子代理。**未继承**实现者或调度者的结论；本报告所有证据均由本会话自己产生。
> 判据：`.spec/hof-rs/tasks/TASK-DR62.md`（任务书）、`.spec/hof-rs/tasks/TASK-DR62-ACCEPT.md`（验收简报）、
> `DECISIONS.md` **D249/D250**、`.spec/hof-rs/tasks/TASK-DR62-REPORT.md`（**仅作线索**）。
> **离线**：未启动 Godot、未触碰外部/MCP 端口、未联网、未调用任何模型端点、未 `push`、未 `stage`、
> 未改写历史。除 §3 的植入外未改动任何被跟踪文件；全部植入已逐字节回退并三法证明。
> 未修改 `.workspace/mario/**`、`runs/**`、`.spec/hof-rs/PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`。

**被测对象**：代码树 = **`49b9417`**（`git diff --name-only 49b9417..HEAD -- src tests Cargo.toml Cargo.lock` = 空）。
验收期间 HEAD 由 `49b9417` 漂到 **`2a36bb8`**（调度者的 5 个**纯文档**提交：`fb572ca`/`9ea6dea`/`2db2515`/`2a36bb8` 等，
含 `TASK-DR62-REPORT.md`、`TASK-DR62-ACCEPT.md`、`DECISIONS.md` **D251**；`src/`/`tests/`/`Cargo.*` 零改动）。
`origin/master` 全程 = **`6a0c9a9`**（未 push，`origin/master..HEAD` = 7 commits）。本报告不改动历史，只记录漂移。

---

## 1. 结构化结论

```json
{
  "verdict": "pass",
  "criteria": [
    {
      "id": "SUITE",
      "pass": true,
      "evidence": "`cargo test --offline`（全量、不抑制输出、落到 /c/Users/wyl/AppData/Local/Temp/dr62-acc/suite-final.txt）：38 `Running` + 1 `Doc-tests` = 39 targets；`grep -o '[0-9]* passed' | awk` 合计 **372 passed / 0 failed / 7 ignored**；`grep -c '^warning'` = **0**；`SUITE_EXIT=0`。与基线 366/0/7 对照：passed +6、ignored 7→7、failed 0。6 个关键新测试在本次全量里逐条 ok（suite-final.txt:66/68/81/114/118/120/339/341/342/343）。`#[ignore` 全树 8 处（7 属性 + 1 注释），与 `git show 6a0c9a9:tests/godot_smoke.rs` 计数 8 **同值**。全仓范围 `git diff 6a0c9a9..HEAD -U0` 的删除项：函数仅 `copy_evidence_skips_superseded_files_and_keeps_them`（被 3 条更强测试取代）、`is_expired_name`（生产谓词，无调用者）、`run_round`（同名重写）；删除的断言行仅 4 条 `is_expired_name(...)`。无 `#[ignore]` 新增、无测试删除。"
    },
    {
      "id": "NOT_NAME_BASED",
      "pass": true,
      "evidence": "判定源 = **显式清单记录**：`src/runtime/hygiene.rs:391` `SUPERSEDED_MANIFEST = \".superseded.json\"`、`:466` `pub fn is_superseded(root, relative)`（逐级读清单，只做集合成员判断，不读文件名）；消费者 `src/runtime/view.rs:86`（copy_tree）与 `:142`（copy_evidence）；生产者 `src/adapter/godot.rs:2444`（唯一生产写入点，在 `rename` 之前）。全仓非测试代码里已无任何以 `.stale-` 名字作判据的消费者（`grep -rn '\\.stale-' src/` 余下全是文档、生产侧审计命名 `stale_name`、与测试断言）。我自己构造（P1，`tests/dr62_acc_probe.rs`，已删除）：Developer 本轮写 `.hoh/evidence/acc-probe-round-one.stale-4711.png`（**从未被记录**）+ 被清单记录的 `acc-probe-recorded.stale-4712.png` ⇒ Tester 冻结候选视图 `tester.get(this_round) == Some(marker)`，被记录者与 `.superseded.json` 都不在；`PROBE_EXIT=0`。反方向（植入①，把两条判据换回 DR-61 的名字谓词）：同一测试红在 `tests/evidence_unreachable.rs:513`，候选里**只剩** `.hoh/evidence/.superseded.json`。"
    },
    {
      "id": "COPY_TREE",
      "pass": true,
      "evidence": "`src/runtime/view.rs:86`（`copy_tree` 内）与 `:142`（`copy_evidence` 内）是**同一条** `hygiene::is_runtime_bookkeeping(&rel) || hygiene::is_superseded(src, &rel)?`；`src/runtime/run_loop.rs:991` 的调用点无需改动（只加注释）。我的独立单元构造 P3（自己的名字/布局：根清单记 `acc-recorded.stale-2.json`、子目录清单记 `acc-nested.stale-3.json`，另有未记录的 `acc-not-recorded.stale-1.json`）⇒ `copy_tree` 后 `list_tree(dst) == [\"acc-not-recorded.stale-1.json\"]`，两个被记录者原地保留；`PROBE_EXIT=0`。植入②（`if false && (…)` 只关 `copy_tree` 的判据）：lib 恰红 1 条 `runtime::view::tests::copy_tree_applies_the_same_supersession_criterion_as_the_evidence_copy`（`8 passed; 1 failed`，view.rs:408），我的 P3 红而 P1 **仍绿** ⇒ 两条拷贝路径各自独立可测。轮次级：P4（上一轮在 `.hoh/deterministic` 留可识别件 + 新开轮）候选不含该件 ⇒ 通过；但机制不是本过滤器（见 DEF-62A-2）。"
    },
    {
      "id": "WALK_SCOPE_PINNED",
      "pass": true,
      "evidence": "自检 `tests/evidence_unreachable.rs:439 the_workspace_walk_reaches_a_marker_seeded_outside_hoh`，标记 `OUTSIDE_HOH_SEEDS`（`:109` `previous-round/out-of-hoh-battery.json`）**埋在 `.hoh` 之外**；另在既有不变量测试 `:267`（1c）内做同一次 `walk(&workspace)` 的正对照。植入③（把 `:252` 与 `:448` 两处 `walk(&workspace)` 收窄为 `walk(&workspace.join(\".hoh\"))`）⇒ `cargo test --offline --test evidence_unreachable` = **`3 passed; 2 failed`**，红的正是自检（`:451`）与既有不变量（`:276`），`INT_EXIT=101`。**收窄后并非仍绿**。"
    },
    {
      "id": "NON_VACUITY",
      "pass": true,
      "evidence": "三处植入均只改一处、测试断言一字未动；每处植入前把目标文件逐字节备份到 `C:/Users/wyl/AppData/Local/Temp/dr62-acc/head/`，回退用 `cp` 回灌，逐字节证明：`cmp` identical、`git status --porcelain -- <file>` 空、`git diff --stat -- <file>` 空、`git hash-object` == `git rev-parse HEAD:<file>`，另加原始 `sha256sum` 与植入前一致。①（`src/runtime/view.rs` 两条判据改回名字）：lib `6 passed; 3 failed`（view.rs:371/413/453）+ 我的 P1/P3 红 + 轮次级红 ⇒ 2 处生产代码植入非空洞。②（只关 `copy_tree` 过滤）：lib 恰红 1 条 + 我的 P3 红/P1 绿 ⇒ 生产代码非空洞。③（收窄 `walk`）：红在**测试文件**里，不是生产代码 —— 见 DEF-62A-1（实现者已在 REPORT §8.2 主动披露）。"
    },
    {
      "id": "ENGINE_MTIME",
      "pass": true,
      "evidence": "嵌套仓：`git -C godot-mcp/godot status --porcelain` = **0 行**；`rev-parse HEAD` = `fc63af77c33368c4a1bb839c95d19750554f63a3`；`sha256sum …/modules/mcp_server/tools/running_game_test_execution.cpp` = `ece4ae63d445719b662a6e9ad99ba80bebba3ea3c94468094c7e9cb820ddff3f`（三者与 DR-59/DR-61 记录逐字一致，本会话两次测得同值）。三个 mtime 口径今天全部复现：整树含 `.git` 最新 `2026-09-29 10:58:15`（`.git/refs/remotes/origin/feature/mcp-server-module-rebuild`）、排除 `.git` 的源码侧最新 `10:49:37`、`modules/mcp_server` 子树最新 `10:37:38`。`find godot-mcp/godot -type f -newermt '2026-09-29 19:00' | wc -l` = **0**。**结论：10:58:15 与 10:37:38 的差异可解释为口径不同，且我找到了 DR-59 侧的一手出处**（`.spec/hof-rs/tasks/TASK-DR59-REPORT.md:411` 与 `TASK-DR59-ACCEPTANCE.md:72/176` 均写明其口径是 `godot-mcp/godot/modules/mcp_server` 子树 = 10:37:38；DR-61 量的是整树含 `.git` = 10:58:15）。**但这不是“确认未改”**：mtime 无法发现“改了又把时间戳改回去”；“引擎内容未改”的正证是嵌套 status 0 行 + HEAD 未变 + 关键 `.cpp` sha 未变 + 无晚于批次窗口的文件，四项都由我今日独立复现（见 §6）。"
    },
    {
      "id": "GUARDS",
      "pass": true,
      "evidence": "摘要口径（我按实现者与 DR-59/61 验收所述口径**独立重建** `digest.ps1`）：递归 `Get-ChildItem -Recurse -Force -File`，每文件取相对仓根路径（`\\`→`/`、转小写）+ 字节长度 + SHA256（小写 hex），三列 `\\t` 连接、行间 `\\n`、无尾随换行，行按路径升序、**排序器 = PowerShell `Sort-Object`（文化敏感）**，整体 UTF-8 后取 SHA256。**口径自证**：`runs/smoke-t6` 复算 = `c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03`，与 DR-54/57/59/61 记录逐字一致。我全部工作**前后各测一次**，值相同：`.workspace/mario` = 259 文件 / `4e494547416b2e87ba025d686afef9447d4f92c027917d1790e6fc9deaeaa84a` / 最新 `2026-09-29 14:32:28`；`runs` = 5147 文件 / `01ff775e36935d3d92dab6919fe030389a8ff53483c52e87288ad711ec840dc3` / 最新 `2026-09-29 14:44:16`。`PRD-mario.md` sha256 = `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`（未变）。依赖：`git diff --stat 6a0c9a9..HEAD -- Cargo.toml Cargo.lock` = 空。未 stage：`git diff --cached --stat` = 空；`git status --porcelain` = 空。未 push：`git rev-parse origin/master` = `6a0c9a9ae7c02a842619690c60693b96151e087b`。外层 pathspec 证明：`git ls-files godot-mcp` = **6484**（真命中），`git ls-files godot-mcp/godot` = **0**（外层对引擎树是空判，故外层 `git diff` 无证据力）。"
    },
    {
      "id": "HONESTY",
      "pass": true,
      "evidence": "REPORT §8 的 10 条披露逐条核实，全部属实或方向正确（§2 表）。关键两条：§8.2 自认“植入③在测试文件、不在生产代码”——**经我独立确认属实**：全仓没有任何生产代码里的“工作区 cwd 遍历”（`grep -rn 'fn walk' src/` 只有 `src/adapter/godot.rs:2309` 的 JSON 树 `walk(node)` 与 `src/runtime/hygiene.rs:811` 的 `walk(root)`，后者位于 `:630` 的 `#[cfg(test)] mod tests` 内）；§8.3 自认“一条既有测试被替换并加强”——我逐字比对旧体与新体，旧体 5 条断言全部保留，另加“清单记录 vs 名字”两处更强断言，属实。另核实：实现者 scratch 目录 `C:/Users/wyl/AppData/Local/Temp/dr62-scratch` 已删（`Test-Path` = False）；`pwsh` 在本机确实不存在（`where pwsh` 失败，仅 PowerShell 5.1）。少数不精确处见 DEF-62A-2/DEF-62A-4（均为遗漏而非虚报）。"
    }
  ],
  "defects": [
    {
      "id": "DEF-62A-1",
      "severity": "minor",
      "what": "任务书 §2 字面要求“三处**仅生产代码**的受控植入”，第 ③ 处（收窄 `walk`）落在**测试文件** `tests/evidence_unreachable.rs` 里。这不是实现者的偷懒，而是任务书前提不成立：DEF-1 所指的 `walk` 就是该测试自己的递归遍历（DR-61 明确要求用真实文件系统遍历验证不变量，而非调用某个运行时函数），生产代码里不存在这样一条可被“收窄回 `.hoh`”的 cwd 遍历。收窄后自检与既有不变量测试**同时红**，作用域的固定是**有效的**。",
      "reproduction": "`git diff -- src/runtime/view.rs` = 空 + `git diff -- tests/evidence_unreachable.rs`：把 `:252`/`:448` 的 `let cwd = walk(&workspace);` 改成 `walk(&workspace.join(\".hoh\"));` ⇒ `cargo test --offline --test evidence_unreachable` → `3 passed; 2 failed`（`:276`、`:451`），`INT_EXIT=101`。`grep -rn 'fn walk' src/` 只命中 `godot.rs:2309`（JSON）与 `hygiene.rs:811`（在 `#[cfg(test)] mod tests` 内）。"
    },
    {
      "id": "DEF-62A-2",
      "severity": "minor",
      "what": "第二件事（给 `run_loop.rs:991` 的 `copy_tree` 补过滤）在**当前生产代码里没有触发路径**，是纯防御纵深：`(a)` `.hoh/deterministic` 在角色之后、候选拷贝之前被 `run_battery_pass`（`src/runtime/run_loop.rs:272-275`，调用点 `:815`）**整体删掉重建**，角色写进去的任何东西（含清单）在拷贝时已不存在；`(b)` 唯一的生产清单写入点 `invalidate_artifact`（`godot.rs:2444`）只由 `step_screenshot`（`godot.rs:1088`）调用，目标固定是 `.hoh/evidence/frame-00.png`，**从不**落在 `.hoh/deterministic`。因此 TASK-DR62 §1.3 设想的“上一轮在 deterministic 留件、被 copy 过滤挡住”并不描述真实机制 —— 真实机制是“整棵 `.hoh` 每轮开轮被隔离” + “battery 重建目录”。过滤器本身确实接上了（P3 与植入②可证），但它的非空洞性**只在单元层**。实现者报告未把这一点说明（§4.2 读起来像有轮次级触发），属**重要遗漏**，不是虚报。",
      "reproduction": "我的 P2：Developer 写 `.hoh/deterministic/acc-probe-keep.stale-4713.json` 等 ⇒ 轮次结束后该文件**在磁盘上已不存在**（battery 重建），候选 deterministic 键只有运行时自产集 `[\".hoh/deterministic/battery.json\", \"build.json\", \"deterministic.json\", \"deterministic.log\", \"record-00.json\"]`。我的 P4/P5：上一轮留在 `.hoh/deterministic` 的可识别件在新一轮**字节不差地躺在** `runs/<id>/quarantine/**`（恰 1 份），且已从工作区消失 ⇒ 挡住它的是隔离，不是 `copy_tree`。`grep -rn 'SupersededSet::record' src/` 仅 `godot.rs:2444`；`grep -rn 'invalidate_artifact' src/` 的生产调用点仅 `godot.rs:1088`。"
    },
    {
      "id": "DEF-62A-3",
      "severity": "info",
      "what": "清单判据是**逐精确路径**的，不是逐子树：把一个**目录**记进清单不会抑制其中的内容（`is_superseded` 对子项返回 false）。当前没有生产路径会记录目录（`invalidate_artifact` 只处理 `is_file()`），故属潜在语义缺口，不是当前缺陷。",
      "reproduction": "我的 P6（直接调 `hof_rs::runtime::view::copy_tree`）：`src/.superseded.json` 记录 `\"sub\"`，`src/sub/child.json` 存在 ⇒ `list_tree(dst)` = `[\"sub/child.json\"]`（子项仍被拷贝）。"
    },
    {
      "id": "DEF-62A-4",
      "severity": "info",
      "what": "两处台账措辞需要订正（都不影响 DR-62 的代码结论）：`(i)` D250 记的 cmd `^` 陷阱方向正确，但最简单的形式并非“cmd 返回 OK”——`git cat-file -e HEAD^:<不存在文件>` 在 cmd 与 bash **都是 128**；真正的假绿要在“两个 revision 对同一路径的存在性不同”时才出现。`(ii)` D250 的 R-F“引擎 mtime 差异未解释”**现在可以关账**：差异是口径不同，且 DR-59 侧有一手出处（TASK-DR59-REPORT.md:411 / TASK-DR59-ACCEPTANCE.md:72,176 写明其口径为 `modules/mcp_server` 子树）——这属于调度者的台账更新，不属于本批实现者的代码缺陷。",
      "reproduction": "`(i)` bash：`git cat-file -e \"fb572ca^:.spec/hof-rs/tasks/TASK-DR62-REPORT.md\"` → **128**（`fatal: path … exists on disk, but not in 'fb572ca^'`）；cmd：`git cat-file -e fb572ca^:.spec/hof-rs/tasks/TASK-DR62-REPORT.md` → **exit 0**（caret 被吃掉，实际查的是 `fb572ca:…`）。`(ii)` 见 §6。"
    }
  ],
  "risks": [
    "清单是**角色可写**的：任何角色都能在某个被拷贝的目录里写 `.superseded.json`，从而让**本轮**（甚至同伴角色的）产物被判为“已取代”而不进候选 —— 判据的权威性未做强制（不是回归：旧的名字判据同样由角色自选名字触发）。我的 P1 中正是 Developer 自己写下的清单触发了跳过。",
    "清单损坏 = 硬错误：`SupersededSet::load` 对不可解析内容返回 `InvalidData`，`copy_tree`/`copy_evidence` 会把错误上抛 ⇒ 视图构建失败；角色因此可以（有意或无意地）让一轮失败。实现者已记为 R-3，我复核属实。",
    "`.hoh/evidence/.superseded.json` 是新增的落盘运行时文件；无 GC，同目录内取代次数线性增长（体量小，但属新增状态）。",
    "`is_superseded` 对每个条目沿路径分量逐级 `exists()`+读取（每级一次探测），`copy_tree` 现在每文件都要走一遍；测试规模无感（全量套件墙钟与基线同量级），大工作区开销未测量。",
    "验收期间 HEAD 由 `49b9417` 漂到 `2a36bb8`（调度者 5 个纯文档提交，含写进 `DECISIONS.md` 的 D251 与 `TASK-DR62-ACCEPT.md`）；`src/tests/Cargo.*` 零改动，故不影响本判定，但意味着 `git diff 6a0c9a9..HEAD -- DECISIONS.md` 现在**非空**（是调度者自己的 D251，不是本批实现者改的）。",
    "R-1（DR-61 遗留）：`.hoh` **之外**的上一轮残留仍不被隔离，本批只用它做作用域锚点，未扩大隔离面；`previous-round/out-of-hoh-battery.json` 在新轮里仍原地可达（这正是自检的**故意**行为）。"
  ],
  "unverified": [
    "真机：未启动 Godot，未跑任何 E0–E6（`tests/godot_smoke.rs` 7 条仍 ignored、ignored 总数 7→7）；不声称任何条目 met。",
    "未在真机观测 `.superseded.json` 的实际写入时序与位置（只在 FakeAdapter/单元/集成层验证了“记录发生在 rename 之前”的代码顺序）。",
    "`record` 写入失败（只读目录/权限拒绝）的分支未打红，也未观测其“大声失败”路径。",
    "未复算 `hash_tree`/A_0 身份哈希（沿用 `.hoh` 被哈希排除 + 既有测试绿的既有结论）。",
    "未构造“纯换行差异”来实测 `git diff` 对 CRLF 归一化的盲区；只确认了 `core.autocrlf=true` 与 `git hash-object` 会归一化（我另用原始 `sha256sum` + `cmp` 兜底）。",
    "`runs`/`mario` 的“未改”证据是**当前值 == DR-54/57/59/61 记录值 + 我前后两次自测一致**；我不能独立证明实现者动手**之前**的字节，只能证明口径自洽且现在与历史记录一致。"
  ]
}
```

**总判定：`pass`。** 简报列出的 fail 门槛（套件不绿 / ignored 增 / 判据仍靠名字 / 带 `.stale-` 的本轮产物仍被隐藏 / `copy_tree` 未覆盖 / 收窄 `walk` 后仍绿 / 禁区被动过）**逐条都不成立**。
四条缺陷中没有 blocker，两条 minor 是"任务书字面要求 vs 结构性事实"的偏离与一处重要遗漏，两条 info 是台账订正与潜在语义缺口。

---

## 2. 逐项核对表（含真实命令与退出码）

| # | 判据 | 结果 | 我的命令 / 真实观测 |
|---|---|---|---|
| 1 | 套件 `cargo test --offline` exit 0 | **pass** | `cargo test --offline > …/suite-final.txt 2>&1` → `SUITE_EXIT=0`；合计 **372 passed / 0 failed / 7 ignored**；38 `Running` + 1 `Doc-tests` = 39 targets；`^warning` = 0 |
| 2 | 与 366/0/7 对照 | **pass** | passed **+6**（=view 净 +2、hygiene +2、evidence_unreachable 3→5）；ignored **7→7**；failed 0 |
| 3 | `ignored` 未增 / 未加 `#[ignore]` | **pass** | `grep -rn '#\[ignore' src tests \| wc -l` = **8**；`git grep -c '#\[ignore' 6a0c9a9 -- src tests` 亦 **8**（7 属性 + 1 文档注释） |
| 4 | 无既有测试被删/放宽 | **pass** | 全仓 `git diff 6a0c9a9..HEAD -U0` 删除的函数行只有 `copy_evidence_skips_superseded_files_and_keeps_them`、`is_expired_name`、`run_round`（同名重写）；删除的 assert 行只有 4 条 `is_expired_name(...)`；新增 3 条 view 测试 + 2 条 hygiene 测试 + 2 条集成测试 |
| 5 | "替换并加强"是否属实 | **pass** | 旧 `view.rs:320` 测试体：this-round 被拷、`.stale-` 名被跳（根+子目录）、不删除、不做 oversized 报告 —— **5 条全部保留**；新增"子目录清单记录"与"`.stale-` 形状但未被记录者必须被拷"（更强）。hygiene 同名测试 4 断言 → 7 断言且换成结构判据 |
| 6 | 判据判定源 = manifest（不靠名字） | **pass** | `hygiene.rs:391/403/413/444/450/466`、`view.rs:86/142`、`godot.rs:2444`；`grep -rn is_expired_name src/ tests/` 只剩注释 |
| 7 | **我自己构造**带 `.stale-` 的**本轮**产物仍可见 | **pass** | P1（本轮 round，Developer 写 `.hoh/evidence/acc-probe-round-one.stale-4711.png`）⇒ Tester 候选含该键且字节相等；`PROBE_EXIT=0` |
| 8 | `copy_tree` 路径应用同一判据 | **pass** | P3 直接调 `copy_tree`：只拷未记录者；植入② 只关 `copy_tree` ⇒ lib 恰红 1 条、我的 P3 红 / P1 绿（两条路径独立可测） |
| 9 | 上一轮 deterministic 留件不进候选 | **pass** | P4：上一轮在 `.hoh/deterministic` 留可识别件、新开轮 ⇒ 候选不含其字节；P5 证明它躺在 `runs/<id>/quarantine/**`（恰 1 份） |
| 10 | 遍历作用域被永久固定（DEF-1） | **pass** | 自检 `evidence_unreachable.rs:439` + 正对照 `:267`；**收窄 `walk` 后两条同时红**（`3 passed; 2 failed`，`:276`/`:451`） |
| 11 | 三处植入非空洞 + 逐字节回退 | **pass** | ①lib 3 红 + P1/P3 红 + 集成本轮测试红；②lib 1 红 + P3 红；③集成 2 红。回退：`cmp` identical、`status` 空、`diff --stat` 空、`hash-object` == HEAD blob、原始 sha256 复原（见 §3 表） |
| 12 | 引擎 mtime 差异可解释 | **pass（有依据，但不升级为"确认未改"）** | 三个口径今日全部复现；DR-59 一手出处写明其口径是 `mcp_server` 子树；另有嵌套 status/HEAD/sha/`-newermt` 四项正证（§6） |
| 13 | 禁区：mario / `runs/**` 未动 | **pass** | 我工作前后两次摘要完全一致：mario 259 / `4e494547…`；runs 5147 / `01ff775e…`；`smoke-t6` = `c144ef32…9a9c03`（口径自证） |
| 14 | `PRD-mario.md` sha 未变 | **pass** | `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a` |
| 15 | Cargo 零 diff（无新依赖） | **pass** | `git diff --stat 6a0c9a9..HEAD -- Cargo.toml Cargo.lock` = 空 |
| 16 | 未 push / 未 stage | **pass** | `origin/master` = `6a0c9a9ae7c02a842619690c60693b96151e087b`；`git diff --cached --stat` = 空；`git status --porcelain` = 空 |
| 17 | 外层 diff 对引擎树是空判 + pathspec 真命中 | **pass** | `git ls-files godot-mcp` = **6484**；`git ls-files godot-mcp/godot` = **0**；`git ls-files runs` = 0；`git ls-files .workspace` = 0 |
| 18 | 假绿陷阱实测 | **pass** | `git diff --stat 6a0c9a9..HEAD -- definitely-not-a-path-xyz` → exit 0、无报错（不存在 pathspec 不报错）；cmd caret 假绿：`fb572ca^:TASK-DR62-REPORT.md` → bash **128** / cmd **0** |
| 19 | 实现者的诚实披露 | **pass** | §8.1（第三件无修前红）与 §8.2（植入③非生产代码）经我独立确认为**真实**；§8.3/§8.4/§8.5/§8.7/§8.9/§8.10 逐条核实；遗漏见 DEF-62A-2/DEF-62A-4 |

---

## 3. 反例清单（我的植入位置、观测与逐字节回退）

统一说明：仓 `core.autocrlf=true`，`.git` 的 `status`/`diff`/`hash-object` 都会做 CRLF→LF 归一化，
因此我**同时**保留植入前的**逐字节备份**（`C:/Users/wyl/AppData/Local/Temp/dr62-acc/head/`）并用
`cmp` 与原始 `sha256sum` 兜底 —— 三法之外的第 4 项证据。三处植入均**只改一处、断言一字未动**。

### 植入 ①：把 `.stale-` 判据改回"按文件名"（生产代码 `src/runtime/view.rs`，两条路径同改）

```
$ git diff -- src/runtime/view.rs
-        if hygiene::is_runtime_bookkeeping(&rel) || hygiene::is_superseded(src, &rel)? {
+        if rel.split('/').any(|component| component.contains(".stale-")) {   (两处)
$ cargo test --offline --lib runtime::view
panicked at src\runtime\view.rs:413:9: DR-62: copy_tree must not skip by name either
panicked at src\runtime\view.rs:453:9: DR-62: a `.stale-`-looking name the runtime never superseded must be copied
panicked at src\runtime\view.rs:371:9: DR-62: a `.stale-` name the runtime never superseded is this round's artifact and must be copied
test result: FAILED. 6 passed; 3 failed; 0 ignored; 0 measured; 106 filtered out   LIB_EXIT=101

$ cargo test --offline --test dr62_acc_probe
P1: candidate evidence keys: [".hoh/evidence/.superseded.json"]   left: None / right: Some(marker)
P3: left: [".superseded.json", "acc-not-recorded.stale-1.json", "acc-recorded.stale-2.json",
           "sub/.superseded.json", "sub/acc-nested.stale-3.json"]  right: ["acc-not-recorded.stale-1.json"]
test result: FAILED. 2 passed; 2 failed   PROBE_EXIT=101

$ cargo test --offline --test evidence_unreachable a_role_named_stale
panicked at tests\evidence_unreachable.rs:513:5: the candidate holds: [".hoh/evidence/.superseded.json"]
test result: FAILED. 0 passed; 1 failed; 4 filtered out   INT_EXIT=101
```
额外收获（我自己观测到、报告 §4.1 也提到）：回到名字判据后，候选里**只剩清单文件本身**
⇒ `is_runtime_bookkeeping` 不是无的放矢。

### 植入 ②：只关掉 `copy_tree` 的过滤（生产代码 `src/runtime/view.rs`）

```
$ git diff -- src/runtime/view.rs
-        if hygiene::is_runtime_bookkeeping(&rel) || hygiene::is_superseded(src, &rel)? {
+        if false && (hygiene::is_runtime_bookkeeping(&rel) || hygiene::is_superseded(src, &rel)?) {
$ cargo test --offline --lib runtime::view
panicked at src\runtime\view.rs:408:9: DR-62: copy_tree must skip a recorded supersession exactly as copy_evidence does
test result: FAILED. 8 passed; 1 failed; 0 ignored; 0 measured; 106 filtered out   LIB_EXIT=101
$ cargo test --offline --test dr62_acc_probe
p3 … FAILED / p1 … ok / p2 … ok / p4 … ok     test result: FAILED. 3 passed; 1 failed   PROBE_EXIT=101
```
**恰好**只红对应那一条 ⇒ 两条拷贝路径各自独立可测，不是同一断言顺带覆盖。

### 植入 ③：把 `walk` 收窄回 `.hoh`（`tests/evidence_unreachable.rs`，`:252` 与 `:448`）

```
$ git diff -- tests/evidence_unreachable.rs
@@ a_wildcard_walk_of_hoh_cannot_reach_the_previous_rounds_evidence
-    let cwd = walk(&workspace);
+    let cwd = walk(&workspace.join(".hoh"));
@@ the_workspace_walk_reaches_a_marker_seeded_outside_hoh
-    let cwd = walk(&workspace);
+    let cwd = walk(&workspace.join(".hoh"));
$ cargo test --offline --test evidence_unreachable
panicked at tests\evidence_unreachable.rs:451:9: a walk of the workspace must reach the marker outside `.hoh`
  at previous-round/out-of-hoh-battery.json: []; walked keys: ["EVIDENCE_HISTORY.md", "PROJECT_MAP.md",
  "TASK.md", "TOOLS.md", "deterministic/battery.json", ...]   left: 0 / right: 1
panicked at tests\evidence_unreachable.rs:276:9: a walk of the role's cwd must reach the marker outside `.hoh` …
test result: FAILED. 3 passed; 2 failed; 0 ignored; 0 measured; 0 filtered out   INT_EXIT=101
```
**自检与既有的 `.hoh` 外种子测试同时红** ⇒ 作用域确实被固定。注意：该植入在**测试文件**内（DEF-62A-1）。

### 逐字节回退证明（每处植入之后，三法 + 原始 sha256）

| 植入 | 回退动作 | `cmp` 对植入前备份 | `git status --porcelain -- <file>` | `git diff --stat -- <file>` | `git hash-object` | `git rev-parse HEAD:<file>` | 原始 sha256（植入前 = 回退后） |
|---|---|---|---|---|---|---|---|
| ① / ② | `cp .../head/view.rs src/runtime/view.rs` | **identical** | 空 | 空 | `f8ff3851d91706d6b179eeb5eea5c5ff5b07ccd6` | `f8ff3851d91706d6b179eeb5eea5c5ff5b07ccd6` | `fc45b9e263244ef6a24ba1fe2b5c17c1b62de86e8fea38f6a5d28f01d091f6f8` |
| ③ | `cp .../head/evidence_unreachable.rs tests/evidence_unreachable.rs` | **identical** | 空 | 空 | `f597d9c4bb06add050aa559c4d21fa2dab1e4e5f` | `f597d9c4bb06add050aa559c4d21fa2dab1e4e5f` | `6cba5ae03f39f4978e40413db2827f06c5d0146c05c178a7a23f2226ef5fca98` |

最终态：`git status --porcelain` = **空**（我的三个临时探针文件 `tests/dr62_acc_probe{,2,3}.rs` 已删除），
`git diff --stat -- src tests` = 空。**我没有修任何发现的问题。**

### 我的独立探针（构造、位置与观测）

| 探针 | 构造 | 观测 | 结果 |
|---|---|---|---|
| P1 | 本轮 Developer 写 `.hoh/evidence/acc-probe-round-one.stale-4711.png`（无记录）+ `acc-probe-recorded.stale-4712.png` + 其清单 | Tester 候选含前者（字节相等）、不含后者与清单；源文件仍在 | ok |
| P2 | Developer 写 `.hoh/deterministic/acc-probe-keep.stale-4713.json` 等 + 其清单 | 该文件在磁盘上**已被删除**（`run_battery_pass` 重建），候选只有运行时自产集 | ok（发现 DEF-62A-2） |
| P3 | 直接 `copy_tree(src,dst,&[])`，根清单记 `acc-recorded.stale-2.json`、子清单记 `acc-nested.stale-3.json` | `list_tree(dst)` = `["acc-not-recorded.stale-1.json"]`；被记录者原地保留 | ok |
| P4 | 第 1 轮后在工作区 `.hoh/deterministic` 埋可识别件 → 第 2 轮 | 候选不含其字节；候选无任何 `.stale-` 路径 | ok |
| P5 | 同上，但检查隔离区 | 该件在 `runs/acc-run-5b/quarantine/**` 中**恰 1 份**、字节相等；工作区已无 | ok |
| P6 | 清单记录**目录** `"sub"`，`sub/child.json` 存在 | `list_tree(dst)` = `["sub/child.json"]`（子项仍被拷） | ok（潜在缺口，DEF-62A-3） |

---

## 4. 对"判据不靠名字"的独立判定

**判定源不是文件名，是显式清单记录。** 我读实现得到的调用链：

- 常量与类型：`src/runtime/hygiene.rs:391` `SUPERSEDED_MANIFEST = ".superseded.json"`；
  `:403` `SupersededSet`（`load` `:413`、`contains` `:444`、`record` `:450`）；
  `:466` `is_superseded(root, relative)` —— 沿 `relative` 的路径分量逐级读清单做**集合成员**判断，
  **代码里没有任何一处读文件名形状**。
- 消费者：`src/runtime/view.rs:86`（`copy_tree`）与 `:142`（`copy_evidence`），
  两处同为 `if hygiene::is_runtime_bookkeeping(&rel) || hygiene::is_superseded(src, &rel)? { continue; }`。
- 生产者：`src/adapter/godot.rs:2444` `SupersededSet::record(directory, &name)?`，位于 `:2446` 的 `rename` **之前**；
  唯一生产调用者 `:1088`（`step_screenshot` → `.hoh/evidence/frame-00.png`）。
- 旧谓词已删：起点 `hygiene.rs:383` 的 `is_expired_name` 不再存在（`grep` 只剩注释）；全仓非测试代码无 `.stale-` 判据。

**不是名字**的最强证据是"两侧都红过"的对照：

1. 交付态：本轮产物命名 `*.stale-*`（P1 的 `acc-probe-round-one.stale-4711.png`，从未被记录）**进**候选；
   被记录的同类名 **不进**候选。
2. 植入①（换回名字匹配）：**同一条测试**的候选里只剩 `.hoh/evidence/.superseded.json`，
   本轮产物消失（`left: None`）。

⇒ "以前会被隐藏"与"现在不再被隐藏"两侧都是我自己跑出来的真实输出，不是推断。**pass。**

---

## 5. 对"作用域被永久固定"的独立判定

- 新自检 `tests/evidence_unreachable.rs:439` 用的标记 `OUTSIDE_HOH_SEEDS`（`:109`
  `previous-round/out-of-hoh-battery.json`）**确实埋在 `.hoh` 之外**（工作区根下的 `previous-round/`），
  而 `QUARANTINE_AREAS`（`src/runtime/hygiene.rs:371`）= `[".hoh"]` 只隔离 `.hoh`，
  `seed_outside_hoh`（`:123`）在开轮前埋下、开轮后断言仍在**原路径**；
- 既有不变量测试 `:267`（1c）用同一次 `walk(&workspace)` 做正对照，并同时断言 `.hoh` 根遍历**看不到**它；
- **我把遍历收窄回 `.hoh`（`:252`/`:448`）后，两条测试同时红**（观测在 §3 植入③）。

⇒ 若将来有人把"工作区遍历"收窄回 `.hoh`，**不会静默绿**，DEF-1 设想的那种退化被抓住。**pass。**

**但必须写清的边界（DEF-62A-1）**：这条 `walk` 是**测试自己的递归遍历**。全仓不存在生产代码里的
"角色 cwd 遍历"可供收窄 —— `grep -rn 'fn walk' src/` 只有 `src/adapter/godot.rs:2309`（对 JSON `Value` 的
树遍历）与 `src/runtime/hygiene.rs:811`（位于 `:630` `#[cfg(test)] mod tests` 内）。
所以任务书 §2"三处**仅生产代码**的植入"对第 ③ 项**在结构上不可满足**；实现者报告 §8.2 已经主动披露这一点，我确认其属实。
本项按"收窄后是否仍绿"判定为 pass，但把任务书字面要求记为 minor 未满足。

---

## 6. 引擎 mtime 差异的独立结论

**测量（本会话两次，值相同）**：

```
$ git -C godot-mcp/godot status --porcelain | wc -l              => 0
$ git -C godot-mcp/godot rev-parse HEAD                          => fc63af77c33368c4a1bb839c95d19750554f63a3
$ sha256sum godot-mcp/godot/modules/mcp_server/tools/running_game_test_execution.cpp
  => ece4ae63d445719b662a6e9ad99ba80bebba3ea3c94468094c7e9cb820ddff3f

$ find godot-mcp/godot -type f -printf '%T+ %p\n' | sort -r | head -1
  => 2026-09-29+10:58:15.4962655000 godot-mcp/godot/.git/refs/remotes/origin/feature/mcp-server-module-rebuild
$ find godot-mcp/godot -type f -not -path '*/.git/*' -printf '%T+ %p\n' | sort -r | head -1
  => 2026-09-29+10:49:37.8110862000 godot-mcp/godot/tests/data/translations.fa.translation
$ find godot-mcp/godot/modules/mcp_server -type f -printf '%T+ %p\n' | sort -r | head -1
  => 2026-09-29+10:37:38.3710244000 godot-mcp/godot/modules/mcp_server/scripts/mcp029_clear_default_evidence.ps1
$ find godot-mcp/godot -type f -newermt '2026-09-29 19:00' | wc -l   => 0
$ git ls-files godot-mcp | wc -l => 6484     # pathspec 真命中
$ git ls-files godot-mcp/godot | wc -l => 0  # 外层对引擎树是空判 ⇒ 外层 git diff 无证据力
```

**结论（明确回答）**：`10:58:15` 与 `10:37:38` 的差异**可以解释为量测口径不同**，而且这次我找到了
DR-59 侧的**一手出处**，不只是"两个口径今天都能复现"：

- `TASK-DR59-REPORT.md:411` ④ 写明："`godot-mcp/godot/modules/mcp_server` 最新文件 = `2026/9/29 10:37:38`"；
- `TASK-DR59-ACCEPTANCE.md:72` 与 `:176` 亦写明其口径是 `godot-mcp/godot/modules/mcp_server` 子树；
- `TASK-DR61-REPORT.md:322` 与 DR-61 独立验收记的是**整棵树（含 `.git`）**最新 = `10:58:15`（远端跟踪 ref）。

⇒ D250 记为"未解释"的 R-F 可以关账为**口径差**（这是调度者台账的更新，不是代码缺陷）。

**但我明确拒绝把它升级成"确认引擎未改"**：
mtime 无法排除"改了内容再把时间戳改回去"。支持"引擎内容未改"的是另外四项**正证**，且都由我今日独立复现：
嵌套 `status --porcelain` = 0 行、嵌套 `HEAD` 未变、关键 `.cpp` sha 未变、无任何文件晚于批次窗口（19:00）。
综合表述：**没有证据表明引擎被改动；差异已由口径解释；但我不能证明"引擎绝对未被改过"。**

---

## 7. 未验证项与理由

1. **真机 E0–E6 全部未验证**：离线约束，未启动 Godot；`godot_smoke.rs` 7 条保持 ignored（ignored 7→7）。不声称任何条目 met。
2. **`.superseded.json` 的真机写入时序/位置**未观测；只在单元（`godot.rs:4294` 加强后的既有测试）与集成层验证了"记录在 rename 之前"的代码顺序。
3. **`record` 失败分支**（只读目录、权限拒绝）未打红、未观测其"大声失败"表现。
4. **`hash_tree` / A_0 身份**未复算；沿用"`.hoh` 被哈希排除 + 既有测试绿"的既有结论（`view.rs` 的
   `the_candidate_identity_is_unaffected_by_evidence_copying` 本次全量绿）。
5. **CRLF 盲区**未实测构造：只确认 `core.autocrlf=true` 且 `git` 会归一化（工具还打了
   `warning: in the working copy of '<file>', LF will be replaced by CRLF`），因此回退证明另用 `cmp` + 原始 `sha256sum`。
6. **`runs`/`mario` 的"未改"**依赖口径自洽（`smoke-t6` 复算命中历史记录）+ 我前后两次自测一致；
   我无法独立证明实现者动手**之前**的字节，只能证明现在与历史记录逐字一致。
7. **性能开销未测量**（`is_superseded` 的逐目录探测在 `copy_tree` 里对每个条目都发生）。
8. 我**没有**对 38 个集成 target 的全部语义做逐条审计，只审计了 DR-62 相关者 + 全量聚合结论。

---

## 8. 我没有独立复核的部分

- 实现者 `TASK-DR62-REPORT.md` 的**逐行**真实性我没有全查（522→545 行的定稿版我读了全文）；我核的是它的
  主要声明与 §8 的 10 条披露，以及所有与我的判定相关的命令与数字。
- 我没有重放实现者的红-绿历史提交（`d338459`/`6dc12b5`/`49b9417` 内部演进），只验了它们之间的
  `numstat`/`name-status` 与最终态的差异内容；历史红态由我的三处植入重放替代。
- 我没有审计 `godot-mcp/**` 的全部内容（只按判据用了嵌套仓 + mtime + sha），也没有审计 `runs/**` 的内部结构。
- 我没有独立复核 DR-61 的验收结论（本批只继承其风险台账，未重跑其 9 条判据）。
- 我没有检查 `.hoh` 之外残留的隔离（R-1）之外的其它 DR-61 遗留项（rename 句柄、无 GC）。

---

## 9. 给下一批的建议（我**没有**改任何代码）

1. **可以推送**：本验收判 `pass`，四条缺陷无 blocker；`origin/master` 仍 `6a0c9a9`，`origin/master..HEAD` = 7 commits 全在本地。
2. **台账订正（调度者，非实现者）**：
   - 把 D250 的 **R-F** 关账为"口径差"，并在 `DECISIONS.md` 写明三个口径与各自的一手出处
     （DR-59 = `modules/mcp_server` 子树；DR-61/本验收 = 整树含 `.git`）。
   - 把 D250 的 cmd `^` 陷阱措辞精确化：`HEAD^:<不存在>` 在两壳都 128；假绿出现在"两 revision 路径存在性不同"的情形
     （`fb572ca^:TASK-DR62-REPORT.md`：bash 128 / cmd 0）。所有 `rev^` 查询继续只在 bash 做。
3. **任务书措辞**：`TASK-DR62.md` §2 的"三处**仅生产代码**的植入"对第 ③ 项不可满足（该 `walk` 只在测试里）。
   下一份任务书应把这条写成"至少两处生产代码植入 + 作用域锚点的测试层植入"，避免再次出现"自认偏离"。
4. **设计决策待办（不是本批缺陷）**：
   - 明确 `is_superseded` 的**逐精确路径**语义（目录记录不抑制子树，DEF-62A-3）；若期望子树语义，
     需要在 `is_superseded` 里做前缀判定并补测试。
   - 若要给第二件事**生产级非空洞性**，需要一条真的能在 `copy_tree` 源目录里留下"已取代件"的路径
     （今天被 `run_battery_pass` 重建与整 `.hoh` 隔离两道机制挡死），否则应在文档里显式标注它是**防御纵深**。
   - 清单是**角色可写**的：若威胁模型含对抗性角色，应考虑把取代记录命名空间化到运行时独占位置
     （例如随运行目录走），或至少把"角色写清单导致其它产物被隐藏"记成已知残余风险；同时给"清单损坏 ⇒ 视图构建失败"一个明确的产品决策。
5. **不要**在验收/实现流程里再用"文件名子串"做任何跳过判据；也不要把本条新增的 `.superseded.json`
   放进 artifact 身份（它现在在 `.hoh` 内、且被 `is_runtime_bookkeeping` 排除，保持即可）。
6. 下一批的真机轮次应顺带记录：真机上 `.hoh/evidence/.superseded.json` 的实际路径/时序，以及
   `step_screenshot` 在目标目录不可写时的 FAILED note 形态（本批离线不可测）。
