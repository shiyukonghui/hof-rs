# TASK-DR59 实施报告 — 让确定性证据**按轮次隔离**（新一轮不得读到上一轮的证据）

> 实现子代理报告。落点 `F:\moonbit-hof-rs`（外层仓 `master`）。**离线批次**：未启动 Godot、未碰任何端口、
> 未联网、未调模型端点。本批 4 个本地提交（**未 push**）：`91a28f8`（红测试）→ `db145b5`（实现）→
> `7fab86b`（两轮序贯通测试）→ 本报告所在的最后一个提交（自引用哈希不便固定）。
> **E3 未被声称**：行为判据只能由真机轮次决定，本轮一切结论均为**离线**证据。

---

## 1. 结论 + 套件真实尾部 / 退出码

**结论：缺陷已修好（离线可判定部分）。** 开轮时（`initialize` 之后、`A_0` 快照与任何角色之前），
`<workspace>/.hoh/deterministic/**` 被**整体移开**到同仓既有 `.stale-<ts>` 命名下的兄弟路径
`<workspace>/.hoh/deterministic.stale-<unix 秒>`；因此新一轮的**读取路径**（`.hoh/deterministic/**`）
在该轮任何角色被调用前就为空，而上一轮的字节**逐字节保留**（**不是删除**）。

- 新增落点：`src/runtime/hygiene.rs:363` `pub fn quarantine_previous_evidence()`；
  `.stale-<ts>` 命名统一到 `src/runtime/hygiene.rs:331` `pub fn stale_name()`。
- 调用点：`src/runtime/run_loop.rs:353`（**唯一**调用处）。
- 回滚点：3 个提交各自单独 revert；不改任何既有测试。

**门（真实输出）**：`cargo test --offline` ⇒ **359 passed / 0 failed / 7 ignored，EXIT=0**，构建**零警告**。

基线（本机同法实测，改动前）= **353 passed / 0 failed / 7 ignored**。
逐目标分布对照（`test result:` 行的去重计数，baseline vs final）：

| 目标 | 基线 | 本批后 |
|---|---|---|
| `src\lib.rs`（单测） | 104 passed | **107 passed**（+3） |
| `tests\evidence_isolation.rs`（新目标，3 测试） | 不存在 | **3 passed** |
| 其余 36 个目标（含 7 ignored 的那个） | 与 final **逐项相同** | 与 baseline **逐项相同** |

⇒ **+6 passed，ignored 7 → 7（未增），无任何目标计数下降**。没有删除/放宽任何既有测试
（`git diff --name-status HEAD~3 HEAD` 只动 `src/{adapter/godot.rs,runtime/hygiene.rs,runtime/run_loop.rs}`
+ 新增 `tests/evidence_isolation.rs`）。

真实尾部（原样粘贴，末两段）：

```
     Running tests\wrap_up_budget.rs (target\debug\deps\wrap_up_budget-48d6de538feb9569.exe)

running 10 tests
test limits_detection_is_case_insensitive_and_narrow ... ok
test tester_prompt_requires_the_early_skeleton ... ok
test every_role_prompt_renders_the_budget_and_the_discipline ... ok
test config_carries_the_new_budget_and_readiness_keys ... ok
test the_godot_developer_artifact_validity_needs_a_real_entry_script ... ok
test consecutive_limits_failures_stop_after_one_retry ... ok
test limits_exceeded_then_one_wrap_up_retry_succeeds ... ok
test a_valid_artifact_does_not_trigger_the_wrap_up_retry ... ok
test a_normal_finish_without_an_artifact_keeps_its_existing_retry ... ok
test a_missing_artifact_triggers_the_wrap_up_retry_with_a_reason ... ok

test result: ok. 10 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 18.47s

   Doc-tests hof_rs

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

EXIT=0
```

新目标的自证（同一套件内）：

```
     Running tests\evidence_isolation.rs (target\debug\deps\evidence_isolation-355f49916769fed0.exe)

running 3 tests
test a_clean_round_start_quarantines_nothing ... ok
test a_new_round_cannot_read_the_previous_round_evidence ... ok
test round_two_cannot_read_round_one_evidence ... ok
```

---

## 2. 定位（谁写 / 谁读 / 开轮有无清理；文件:行）

### 2.1 谁写 `.hoh/deterministic/**`

| 写者 | 位置 | 写什么 |
|---|---|---|
| 电池原始载荷 | `src/adapter/godot.rs:554` `let rel = format!(".hoh/deterministic/raw/{}.json", step.id);` | `raw/<step>.json` |
| MCP 会话同步报告 | `src/adapter/godot.rs:2179` `pub const SESSION_SYNC_FILE: &str = ".hoh/deterministic/mcp-sync.json";`（由 `godot.rs:602` 写入） | `mcp-sync.json` |
| MCP 失败原文 | `src/tools/reliable.rs:97` `workspace.join(".hoh/deterministic/mcp-errors.jsonl")` | `mcp-errors.jsonl` |
| 电池汇总与记录 | `src/runtime/run_loop.rs:916` `deterministic_dir.join("battery.json")`，同段还写 `deterministic.json`、`deterministic.log`、`record-NN.json` | 汇总 + 日志 |
| 目录本身 | `src/runtime/run_loop.rs:273/806` `let deterministic_dir = workspace.join(".hoh/deterministic");` | — |

### 2.2 谁读

| 读者 | 位置 | 读什么 |
|---|---|---|
| **Developer（真机污染的实际读者）** | `src/runtime/run_loop.rs:709` `cwd: workspace.clone()` | 角色 cwd **就是真 workspace**，因此可用绝对/相对路径直接读 `.hoh/deterministic/**` |
| Developer 提示词（DR-17 状态表） | `src/adapter/godot.rs:3448-3453`（playbook 正文） | 指示读 `.hoh/deterministic/battery.json`、`raw/<step>.json` |
| Tester 提示词 | `src/prompts/mod.rs:56`；`src/prompts/tester.md:9-10,23-27,45`；`src/prompts/skills/godot-testing.md:7-14,55-57` | `battery.json` / `raw/<step>.json` / `mcp-errors.jsonl` |
| 运行时的候选视图复制 | `src/runtime/run_loop.rs`（`copy_tree(&deterministic_dir, &candidate.join(".hoh/deterministic"))`） | 整个目录 → `candidate/.hoh/deterministic/**` |
| 角色环境变量 | `src/runtime/invoke.rs:41` `let artifact_dir = view.join(".hoh");` | `HOH_ARTIFACT_DIR` 指向 `.hoh` |

### 2.3 开轮时**有没有**清理 / 隔离

**没有。** 仓内唯一一处清除是 `src/runtime/run_loop.rs:273-274`（DR-24 的 `run_battery_pass`）：

```rust
let deterministic_dir = workspace.join(".hoh/deterministic");
let _ = std::fs::remove_dir_all(&deterministic_dir);
```

它有两个问题，正好构成本缺陷：

1. **时机太晚**：它在 **Developer 阶段之后**才执行（Developer 在 `run_loop.rs:639` 起、
   battery 在 `run_loop.rs:801` 起）。⇒ 从开轮到 Developer 读盘之间，上一轮的证据**原样在生效路径上**。
2. **是静默删除**：`remove_dir_all` 直接销毁上一轮的原始载荷，既无留痕也没有 `.stale-` 保留；
   这一条虽不是本缺陷的直接成因，但正是任务书 §1.2「不得静默删除」要禁的行为，
   本批**没有**改它（见 §7 遗留风险 R-3，属 DR-24 语境的**轮内**重建，非跨轮）。

### 2.4 真机污染链（本地实测，非推测）

`smoke-t7` 开工时的 workspace 清单（`runs/smoke-t7-experiment/pre_run_workspace_inventory.txt`，只读引用）
里含：

```
9314 .workspace/mario/.hoh/deterministic/battery.json
11190 .workspace/mario/.hoh/deterministic/mcp-errors.jsonl
4246 .workspace/mario/.hoh/evidence/frame-00.png
```

`9314` 与 `runs/smoke-t7-experiment/smoke-t6-workspace-baseline/deterministic/battery.json`（**9314 字节**）
逐字节同源，且该文件含 `108432` / `the editor is not clean` / `10061`（本批实测的三项 `True`，见 §5）。
⇒ 上一轮的证据确实在开轮时留在生效路径上，并被 Developer 的读命令直接取走。

---

## 3. 修法与其理由（命名空间 vs 移开；为何不删）

### 3.1 选择的修法：**开轮即移开**（复用 DR-49 的 `.stale-<ts>` 处置方式）

```rust
// src/runtime/hygiene.rs:363（新增）
pub fn quarantine_previous_evidence(workspace: &Path) -> anyhow::Result<Option<String>> {
    let live = workspace.join(DETERMINISTIC_EVIDENCE_DIR);   // ".hoh/deterministic"
    if !should_quarantine(&live) {                            // hygiene.rs:344，= live.exists()
        return Ok(None);
    }
    let base = live.file_name()...;                           // "deterministic"
    let stamp = crate::adapter::engine::now_seconds();
    for attempt in 0..STALE_NAME_ATTEMPTS {                   // 64，与 DR-49 同一命名窗口
        let target = live.with_file_name(stale_name(&base, stamp, attempt));
        if !target.exists() {
            std::fs::rename(&live, &target)?;                 // 移动，不删除
            return Ok(Some(relativize(workspace, &target)));
        }
    }
    anyhow::bail!("DR-59: could not move {DETERMINISTIC_EVIDENCE_DIR} aside: all \
                   {STALE_NAME_ATTEMPTS} `.stale-{stamp}` names are taken")
}
```

调用点（`src/runtime/run_loop.rs:337-353`）位于 `adapter.initialize()` 之后、`excludes`/`A_0` 快照
（`run_loop.rs:384-396` 区段）与任何角色调用之前：

```rust
orchestrator.adapter.initialize(&workspace)?;
let _ = orchestrator.force_init;
// DR-59: ...
let quarantined = crate::runtime::hygiene::quarantine_previous_evidence(&workspace)?;
```

真正发生移开时记一次留痕（不静默）：`run_loop.rs:363` 把稳定 token
`previous_evidence_quarantined`（`run_loop.rs:55`）放进本轮 `meta.json.warnings`，并在 `warnings.log`
追加一行写明移到了哪个名字。干净开轮则**不写任何东西、不建任何目录**。

### 3.2 为什么**不**选「按轮次命名空间」，以及为什么不删

1. **命名空间会改动本轮证据的路径契约，命中面极大而收益更小。**
   `.hoh/deterministic/battery.json` 与 `.hoh/deterministic/raw/<step>.json` 是被**三方角色提示词
   逐字点名**的读取路径（`src/prompts/mod.rs:56`、`src/prompts/tester.md:9-10,23-27`、
   `src/prompts/skills/godot-testing.md:7-12`、`src/adapter/godot.rs:3451-3453`），也是**候选视图复制**
   与**约 40 处测试断言**的落点（`tests/evidence_battery.rs` 内 `iter-1/candidate/.hoh/deterministic/...`
   等）。改成 `.hoh/deterministic/<run_id>/...` 等于同时改写「本轮证据在哪」这件事本身，
   与任务书 §1.4「不得改变本轮证据的内容语义（字段名、结构、可判定性）」的**意图**相冲突：
   它虽没改字段，却改了证据的可寻址性，且要把提示词与消费方全部改成 run 相关。
2. **命名空间并不自动消除旧数据，反而更难判定。** 旧轮次的命名空间目录仍会留在 `.hoh/deterministic/`
   下，`ls .hoh/deterministic/` 就能看到 `smoke-t6/`、`smoke-t7/`；仍然需要一次「移开/清掉」的处置。
   两者并用等于同时承担两套复杂度。
3. **移开是仓内既有、已有文档位的约定。** DR-49（`DESIGN-DETAIL.md:1643-1646`）已经确立
   「调用前先作废目标路径上的既有文件（删除或改名到 `*.stale-<ts>`）」，且
   `src/adapter/godot.rs:2413-2447` 的 `invalidate_artifact()` 就是实现；D240 也明确
   「现有 `.stale-` 改名模式可复用」。本批把该命名**收敛到一个函数**
   （`src/runtime/hygiene.rs:331` `stale_name()`），DR-49 的 `invalidate_artifact` 同时改用它
   （`src/adapter/godot.rs:2433`）——命名一处定义、两处使用，`grep '\.stale-'` 即可审。
4. **为什么不删**：`.hoh/deterministic/**` 是上一轮唯一的原始 MCP 载荷（`raw/<step>.json` 里是引擎
   逐字应答），删掉就永久失去可回查的真机证据 —— 这与 DR-49 注释里「旧工件保持可审计」的理由同源。
   因此断言必须证明**是移开**：本批的测试同时断言「生效路径为空」**且**「旧字节可在 `.stale-` 下逐字节找到」
   （§4）。另外：`quarantine_previous_evidence` 在 64 个名字耗尽时**不回退到删除**，而是
   `bail!` 让本轮**响亮失败**——因为对整轮证据而言，「删掉」和「留在生效路径」两种回退都违背本条决策
   （这与 DR-49 单文件场景的回退删除**故意不同**，代码内已注明理由）。
5. **为什么放在 `initialize` 之后**：`initialize` 可能因为「非空且未 `--force-init`」而**合法失败**；
   放在它之后，失败时不会先动用户的证据。而 `initialize` 本身不读 `.hoh/deterministic`
   （`src/adapter/godot.rs:3294-3338`），所以顺序对隔离效果无影响。
6. **为什么不影响 `A_0`/`A_t`**：`.hoh` 在合并排除集里（`src/runtime/policy.rs:39`
   `let mut items = vec![".hoh".to_string(), ".git".to_string()];`，`policy.rs:420` 断言
   `is_excluded(".hoh/plan.md", …)` 为真），所以 `hash_tree`/`tree_manifest`/版本快照都看不到这次移动；
   `PROJECT_MAP`（`src/runtime/project_map.rs:33,68` 走同一个 `is_excluded`）也不会把它列给模型。

### 3.3 作用域边界（本批**有意**不越界）

隔离只在**开轮**发生一次，不在每个迭代重复：迭代 t≥2 的 Developer 仍能看到迭代 t-1 的电池证据，
这是**轮内**设计好的反馈通道（`EVIDENCE_HISTORY.md` 与 DR-24 的 pass 重建），与
`smoke-t6 → smoke-t7` 的**跨轮**污染是两件事。D240 的措辞也是「开轮即清 / 按轮次隔离」。

---

## 4. TDD 证据：红（真实失败输出）→ 绿 → 非空洞反例

### 4.1 红（先写会失败的测试，确认**因缺陷**而红）

新增 `tests/evidence_isolation.rs`。观测点是 `FakeHarness` 在**角色被调用的那一刻**对**整个 cwd**
做的文件快照（`tests/common/mod.rs:253` `files: read_files(&inv.cwd)`）——它正是「模型当时能读到什么」的
离线等价物。测试预置上一轮的证据（含真机文案），跑一轮，然后断言 Developer 调用瞬间生效路径为空、
旧字节在 `.stale-` 下逐字节存在。

改动**之前**的真实输出（`cargo test --offline --test evidence_isolation`）：

```
running 2 tests
test a_new_round_cannot_read_the_previous_round_evidence ... FAILED
test a_clean_round_start_quarantines_nothing ... ok

failures:

---- a_new_round_cannot_read_the_previous_round_evidence stdout ----

thread 'a_new_round_cannot_read_the_previous_round_evidence' (106908) panicked at tests\evidence_isolation.rs:108:5:
DR-59: the previous round's evidence is still on the live read path (.hoh/deterministic/): [".hoh/deterministic/battery.json", ".hoh/deterministic/raw/input_channel_probe.json"]
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace

test result: FAILED. 1 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 17.36s

error: test failed, to rerun pass `--test evidence_isolation`
EXIT=101
```

（`tests/evidence_isolation.rs:108` 是**当时**的行号；后来加了第三个测试，该断言现在位于 `:113`。
其余行逐字保留。）

### 4.2 绿

实现之后（同一命令）：

```
running 2 tests
test a_clean_round_start_quarantines_nothing ... ok
test a_new_round_cannot_read_the_previous_round_evidence ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 17.53s
EXIT=0
```

新增的单测（`src/runtime/hygiene.rs` 内）也在同一批：

```
running 11 tests
...
test runtime::hygiene::tests::quarantine_is_a_no_op_on_a_clean_start ... ok
test runtime::hygiene::tests::quarantine_moves_the_evidence_aside_and_keeps_the_bytes ... ok
test runtime::hygiene::tests::a_second_quarantine_in_the_same_second_does_not_collide ... ok

test result: ok. 11 passed; 0 failed; 0 ignored; 0 measured; 96 filtered out; finished in 0.03s
```

三个集成测试 + 三个单测共 6 条，覆盖：生效路径为空、旧字节逐字节保留（三个断言：目录名以
`.hoh/deterministic.stale-` 开头 / `battery.json` 字节相等 / `raw/input_channel_probe.json` 字节相等）、
干净开轮零副作用、同秒二次移开不覆盖。

### 4.3 非空洞反例（受控植入 → 观测变红 → 逐字节回退）

**(A) 把隔离关掉**（`run_loop.rs` 调用点换成 `let quarantined: Option<String> = None;`）：
两条「旧证据必须不可读」的测试**全部转红**，且报出与真机同形的症状：

```
running 3 tests
test a_new_round_cannot_read_the_previous_round_evidence ... FAILED
test a_clean_round_start_quarantines_nothing ... ok
test round_two_cannot_read_round_one_evidence ... FAILED

failures:

---- a_new_round_cannot_read_the_previous_round_evidence stdout ----

thread 'a_new_round_cannot_read_the_previous_round_evidence' (119720) panicked at tests\evidence_isolation.rs:113:5:
DR-59: the previous round's evidence is still on the live read path (.hoh/deterministic/): [".hoh/deterministic/battery.json", ".hoh/deterministic/raw/input_channel_probe.json"]
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace

---- round_two_cannot_read_round_one_evidence stdout ----

thread 'round_two_cannot_read_round_one_evidence' (119964) panicked at tests\evidence_isolation.rs:214:5:
DR-59: round two's Developer can still read round one's evidence: [".hoh/deterministic/battery.json", ".hoh/deterministic/build.json", ".hoh/deterministic/deterministic.json", ".hoh/deterministic/deterministic.log", ".hoh/deterministic/record-00.json"]

failures:
    a_new_round_cannot_read_the_previous_round_evidence
    round_two_cannot_read_round_one_evidence

test result: FAILED. 1 passed; 2 failed; 0 ignored; 0 measured; 0 filtered out; finished in 33.45s
EXIT=101
```

**(B) 把隔离条件改成恒真**（`should_quarantine` 改成 `true`，去掉 `live.exists()`）：
本应保持恒真的「干净开轮零副作用」性质**立刻可观测地破掉**——两个层级各转红一处：

`--lib`（单测）：

```
---- runtime::hygiene::tests::quarantine_is_a_no_op_on_a_clean_start stdout ----

thread 'runtime::hygiene::tests::quarantine_is_a_no_op_on_a_clean_start' (121352) panicked at src\runtime\hygiene.rs:609:58:
called `Result::unwrap()` on an `Err` value: 系统找不到指定的路径。 (os error 3)

test result: FAILED. 106 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.09s
```

`--test evidence_isolation`（集成）：

```
test a_clean_round_start_quarantines_nothing ... FAILED

thread 'a_clean_round_start_quarantines_nothing' (106916) panicked at tests\evidence_isolation.rs:153:12:
the round itself must still run: 系统找不到指定的路径。 (os error 3)

test result: FAILED. 1 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 14.13s
```

（`os error 3` 是 Windows 本地化的「系统找不到指定的路径」——恒真后被移开的目标本不存在，
于是 `rename` 失败并让本轮响亮中止。保留原文，不翻译。）

**两次植入均已逐字节回退**：回退后三个源文件的 sha256 与植入**完全相同**，`git diff` 为空：

```
86eb993e6d45d684b1c617dc26673b40252bff24f3426414c07c3d31c63a38cf  src/runtime/hygiene.rs
8025521b9b464fadb45e4c040350b62b8896f4757132046c83102aa2a38a9eb5  src/runtime/run_loop.rs
bcc7eb08c5b054842d31f9cbb856394e6f672f5d25a79ce2b65f96b285232644  src/adapter/godot.rs
---- git diff vs HEAD (src)
(空)
```

---

## 5. 真机证据对照：修法**如何**阻断 `smoke-t7` 那条污染路径

### 5.1 原始污染链（逐字引用 `runs/smoke-t7`，只读）

Developer 的**读命令**在 `runs/smoke-t7/iter-1/traj/developer.attempt1.json` 的 `.messages[52]`
（assistant 的 tool call）里，逐字为：

```
type "F:\moonbit-hof-rs\.workspace\mario\.hoh\deterministic\battery.json"
```

它的**工具返回**在 `.messages[54]`（这既是任务书说的 `pid 108432 / "the editor is not clean" /
os error 10061` 的出处）。本批从该文件逐字定位到的片段（`python` 提取，不手抄）：

```
FRAG 'the editor is not clean'    present
     ...\",\"note\":\"\",\"pid\":108432,\"port\":9877,\"process\":\"editor\",\"source\":\"editor_log\"} (UNAVAILABLE: the editor is not clean)...

FRAG 'os error 10061'             present
     .../127.0.0.1:63698/mcp failed: http://127.0.0.1:63698/mcp: Connection Failed: Connect error: ����Ŀ�����������ܾ����޷����ӡ� (os error 10061) (UNAVAILABLE: this evidence could not ...

FRAG '4246 byte(s)'               present
     ..."path": ".hoh/evidence/frame-00.png", |       "observation": "screenshot written to .hoh/evidence/frame-00.png (4246 byte(s))", ...

FRAG 'ACTION_BINDING_UNKNOWN'     present
     ...    "record": { |       "type": "replay", |       "path": null, |       "observation": "FAILED input channel probe: ACTION_BINDING_UNKNOWN (the game-process probe could not be re...
```

并且这些字节确实是**上一轮**的：`runs/smoke-t7-experiment/smoke-t6-workspace-baseline/deterministic/battery.json`
= **9314 字节**，其中 `108432` / `the editor is not clean` / `10061` 三项本批实测均为 `True`；
而 `smoke-t7` 开工清单里 `.workspace/mario/.hoh/deterministic/battery.json` 也正好是 **9314** 字节
（§2.4）。`.messages[54]` 的内容长度 9153 字符（含 JSON 转义）。

### 5.2 修法如何切断它（机制，逐环节）

1. `run()` 一进入就调用 `quarantine_previous_evidence(&workspace)`（`run_loop.rs:353`），
   在 `A_0` 快照（`run_loop.rs:~410`）与 Planner/Developer/Tester 任何一次调用**之前**。
2. 此刻 `.hoh/deterministic` 存在（真机里装着 9314 字节的 `battery.json`）⇒
   `should_quarantine` 为真 ⇒ 整个目录 `rename` 成 `.hoh/deterministic.stale-<ts>`。
3. 于是 Developer 的 cwd（`run_loop.rs:709` 的**真 workspace**）里，路径
   `.workspace/mario/.hoh/deterministic/battery.json` **不再存在**；
   `messages[52]` 那条 `type "...\battery.json"` 会得到「文件不存在」，而不是上一轮的 `pid 108432`
   与「编辑器不干净」。**旧字节仍在 `.hoh/deterministic.stale-<ts>/battery.json`**，可被审计，但不在这条读路径上。
4. 本轮自己的证据不受影响：`run_battery_pass`（`run_loop.rs:273/806`）照旧在冻结前重建
   `.hoh/deterministic/`，`battery.json`/`raw/<step>.json` 的**路径与字段一字未改**
   （既有 38 条 `tests/evidence_battery.rs` 断言与候选视图复制路径全绿即为证）。
5. 离线等价复现：`round_two_cannot_read_round_one_evidence` 就是「第 1 轮真的留下了
   `deterministic/{battery.json,deterministic.json,deterministic.log,record-NN.json}` → 第 2 轮不同 run_id
   再跑」；关掉隔离时它报出的清单（§4.3-A）与真机 `.messages[54]` 的泄漏集合同形。

**注意**：这只证明「离线机制成立」。真机上「模型上下文里不再出现上一轮内容」这一**行为**结论，
只能由下一轮真机判定 —— 本报告**不**声称它已满足。

---

## 6. 禁区自查（真实输出）

| 禁区 | 检查命令与真实结果 | 判定 |
|---|---|---|
| **`.workspace/mario/**` 未改** | `Get-ChildItem .workspace\mario -Recurse -File` → `count = 259`；最新 mtime = `2026/9/29 14:32:28`（smoke-t7 那轮）；`.workspace` 下 mtime `> 2026-09-29 18:00` 的文件数 = **0** | ✅ 未改 |
| **`runs/**` 未动** | `runs/smoke-t6` = **135** 文件、最新 `2026-09-29 02:32:01`（与 D240 记的 135 一致）；`runs/smoke-t7` = **115** 文件、最新 `2026-09-29 14:41:14`（与 D240 记的 115 一致）；`runs` 下 mtime `> 2026-09-29 18:00` 的文件数 = **0** | ✅ 未动（只读引用） |
| **`PRD-mario.md` sha 未变** | `(Get-FileHash .spec\hof-rs\PRD-mario.md -Algorithm SHA256)` = `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a` | ✅ 未变 |
| **`DECISIONS.md` 未改** | 本批 `git diff --name-status HEAD~3 HEAD` 只有 `src/{adapter/godot.rs,runtime/hygiene.rs,runtime/run_loop.rs}` + 新增 `tests/evidence_isolation.rs`；`git status --porcelain` 为空 | ✅ 未改 |
| **引擎树未改（**用嵌套仓**，不用外层 diff）** | ①先证明外层判据是**空判**：`git ls-files godot-mcp/godot` → **0 个文件**（外层仓不跟踪引擎树，D242/DEF-1）；②嵌套仓 `git -C godot-mcp/godot status --porcelain -uno` → **0 行**，`--porcelain`（含未跟踪）→ **0 行**；③`git -C godot-mcp/godot rev-parse HEAD` = `fc63af77c33368c4a1bb839c95d19750554f63a3`，`log -1` 日期 `2026-09-29 10:37:49 +0800`（TASK-154），远早于本批；④mtime：`godot-mcp/godot/modules/mcp_server` 最新文件 = `2026/9/29 10:37:38`，与 D242 记录的参照值一致；⑤`git -C godot-mcp/godot stash list` 为空 | ✅ 未改 |
| **无新依赖** | `git diff --stat HEAD~3 HEAD -- Cargo.toml Cargo.lock` → **空** | ✅ 无 |
| **未 push** | `git rev-parse origin/master` = `ea1cf07a156ec45bc536ed9b028ac4e4350a3ad7`（本批前）；`git log --oneline origin/master..master` = 本批 3 条 | ✅ 仅本地 |
| **无网络 / 无端口 / 无 Godot / 无模型端点** | 全部命令为 `cargo test --offline`、只读 `git`/`Get-*`/`python`（仅读 `runs/**`）；未启动 Godot、未 `TcpListener`、未发任何 HTTP | ✅ 离线 |
| **未用「删除」过关** | 测试显式断言旧字节在 `.stale-` 下**逐字节存在**（§4.2）；`quarantine_previous_evidence` 名字耗尽时 `bail!` 而非删除 | ✅ |
| **临时/scratch 工作区** | `C:\Users\wyl\AppData\Local\Temp\dr59-scratch\`（所有原始日志：红/绿/两次注入/全量套件）；**已在报告定稿后删除**，删除后 `Test-Path` = `False`（见文末「清理记录」） | ✅ 在仓外，且已清 |

---

## 7. 遗留风险与未验证项（严格区分**实测** / **推断**）

**实测（有原始输出）**

- R-1【实测，残余可达性】移开后的目录仍是**角色 cwd 内**的兄弟路径
  （`.hoh/deterministic.stale-<ts>/`）。因此一条 `ls .hoh` / 通配符仍**可能**让模型看到这些旧字节。
  本批保证的是：**被提示词与工具点名的读取路径**（`.hoh/deterministic/**`）为空，且旧数据带着仓内
  既有的「已作废、不可信」`.stale-` 标记。**未**证明「模型绝对读不到」。若验收认为这不够，
  下一批可把隔离物移出 workspace（例如 `runs/<run_id>/…`）——代价是偏离 DR-49 的**原地**改名惯例，
  且会把上一轮的证据混进本轮的 run 目录（可能干扰 E5 三树比对与 run 清单核查），故本批**未擅自**这么做。
- R-2【实测，作用域边界】隔离**只在开轮一次**。迭代 t≥2 的 Developer 仍能读到迭代 t-1 的电池证据
  （轮内反馈，设计如此）。若判定「跨迭代也算污染」，那是设计变更，需回阶段二/三，不在本批。
- R-3【实测，同类路径仍在】`.hoh/deterministic/` 之外的「上一轮残留可被读」路径**未**纳入本批：
  - `.hoh/evidence/**`（截图等）：smoke-t7 开工清单里 `.workspace/mario/.hoh/evidence/frame-00.png`
    = **4246 字节**（正是 `.messages[54]` 里那条 `4246 byte(s)` 的旧 PNG）。DR-49 只在**捕获前**作废
    **目标路径**（`godot.rs:1088`），开轮时旧 PNG 仍在。**实测存在**，本批按任务书范围（确定性证据区）
    **未改**，以免扰动 DR-49 已被独立验收的语义。
  - `run_battery_pass` 的 `remove_dir_all`（`run_loop.rs:274`）仍是**静默删除**，但它是 DR-24 的
    **轮内**「第二次 pass 不得留第一次载荷」重建，不是跨轮；本批**未改**（改它会削弱 DR-24 的既有断言意图）。
  - `.hoh/plan.md`、`.hoh/TOOLS.md`、`.hoh/TASK.md`、`.hoh/EVIDENCE_HISTORY.md`、`.hoh/PROJECT_MAP.md`、
    `.hoh/skills/*`：smoke-t7 开工清单里**都在**（上一轮残留），但 `run_loop.rs:697`
    `write_inputs(&workspace, &developer_inputs)` 在 Developer 调用前用 `std::fs::write` **整体覆盖**
    （`src/runtime/view.rs:50-58`），故按构造即新鲜 —— **实测为「开轮前是旧的、Developer 调用时已被覆盖」**。
  - `.hoh/evidence.json`：smoke-t7 开工清单里**不存在**（实测），故本轮不是可观测泄漏；
    代码上运行时不向 workspace 重写它（Planner 视图写入的是 `planner_evidence(...)` 的空包，
    `run_loop.rs:106-108`），本批**未改**，也**未**观测到它被读。
- R-4【实测，新增表面】新增一个 warning token `previous_evidence_quarantined`
  （`run_loop.rs:55`），只在**真的发生**移开时出现在本轮 `meta.json.warnings` 与 `warnings.log`。
  它是本轮唯一新增的对外行为面（除移开本身）。干净开轮不产生任何新警告（全量套件零警告，且
  `a_clean_round_start_quarantines_nothing` 为绿）。

**推断（未证）**

- I-1【推断】真机下一轮里，Developer 不会再把上一轮的 `pid`/「编辑器不干净」/`os error 10061` 带进上下文。
  **离线机制成立**（§4）且读路径已被清空（§5.2），但「模型真的不再读到」只能由**真机轮次**判定。
- I-2【推断】模型不会主动去 glob `.hoh` 找 `.stale-*`。R-1 讲的残余可达性是否真被触发，**未证**。
- I-3【推断】`.hoh/evidence/**` 的 4246 字节旧 PNG 在真机下一轮里**是否**会被读。本批**只**证明了
  它在开轮时存在于生效路径（实测），未证明它被读。

**未验证项**

- 未跑真机；未验证 E1..E6 中任何一条（尤其**未**声称 E3）；未做活体注入（会污染基线）；
  未验证真机下 quarantine 的实际命名（真机只有一次轮次的 `.stale-` 才能看到），
  也未验证跨轮多次运行后 `.stale-` 目录的累积量（每轮一个目录，与 DR-49 每轮一个文件同族）。

---

## 8. 诚实披露

1. **测序诚实**：我先写集成测试并确认「因缺陷而红」（§4.1），再写实现（§4.2）。
   但 `src/runtime/hygiene.rs` 内的 3 条**单测**是在实现**之后**补写的 —— 它们测的是**新引入的 API**，
   在旧代码上根本编译不过，因此不存在「先红」的可能；它们的非空洞性由**植入 B** 实测（§4.3-B），
   而不是由一次红历史。这一点我不粉饰。
2. **第三个测试也是后加的**：`round_two_cannot_read_round_one_evidence` 在我第一版实现之后才加，
   随后**重跑全量套件**（359/0/7）并单独用**植入 A** 实测它会转红（§4.3-A）。不是「写完就宣称」。
3. **工具坑（会影响退出码读数，故记下）**：我第一次用
   `cargo test --offline 2>&1 | Tee-Object ...` 跑基线，**全部测试都是 ok**、合计 353/0/7，
   但 PowerShell 把原生命令的 stderr 当 ErrorRecord，管道退出码报成 **1**。此后所有退出码都用
   `bash -c '...; echo $?'` 或 `$LASTEXITCODE` 直接取，§1 与 §4 的 `EXIT=` 都是这样得到的。
   我没有把那个被污染的 1 当成测试失败，也没有把后来的 0 当成「因为改对了才 0」——
   基线/最终两次都是「全绿」这一事实本身由 §1 的逐目标分布对照支撑。
4. **我改了一处 DR-49 的代码**：`invalidate_artifact` 里内联的 `.stale-` 后缀构造换成共享的
   `hygiene::stale_name()`（`src/adapter/godot.rs:2431-2439`）。生成的**字符串完全相同**
   （`{base}.stale-{stamp}` / `{base}.stale-{stamp}-{attempt}`），它的既有单测
   （`assert!(stale.starts_with("frame-00.png.stale-"))`、缺失路径返回 `None`）在全量套件里仍绿。
   我**没有**改它的「名字耗尽 → 删除」回退，也没有改任何既有断言的强度。
5. **未改 `DECISIONS.md`**（按任务书由调度方持有）。本批的决策记录（选「移开」而非「命名空间」、
   `.stale-` 命名收敛、作用域边界、R-1/R-2/R-3 残余）全部写在本报告 §3/§7，供调度方转记。
6. **未编造**：本报告所有数字、退出码、路径、字节数、sha256、逐字引文，都来自本会话真实命令输出
   （原始日志见 §6 的 scratch 路径，已按任务书清理）；两次植入的产物已逐字节回退并经 sha256 复核。
7. **未做的事**：没有 push（`origin/master` 仍 `ea1cf07`）；没有启动 Godot / 碰端口 / 联网 / 调模型端点；
   没有写 `runs/**` 与 `.workspace/**`（全部只读引用）；没有写 `PRD-mario.md`；没有新增依赖；
   没有把推断写成实测（§7 已分栏）。
8. **清理记录**：临时工作区 `C:\Users\wyl\AppData\Local\Temp\dr59-scratch\`
   （脚本 `extract.py`、提交信息 `msg-*.txt`、原始日志 `injection-a.txt` / `injection-a-3tests.txt` /
   `injection-b.txt` / `injection-b2.txt` / `final-suite.txt` / `final-suite-2.txt` / `two-round.txt`）
   以及基线日志 `C:\Users\wyl\AppData\Local\Temp\dr59-baseline.txt` 已删除。
   清理命令与**真实输出**：

   ```
   before: True
   extract.py  final-suite-2.txt  final-suite.txt  injection-a-3tests.txt  injection-a.txt
   injection-b.txt  injection-b2.txt  msg-green.txt  msg-red.txt  msg-tworough.txt
   percount.txt  two-round.txt
   after scratch: False
   after baseline log: False
   ```

   **仓内**未留任何本批临时文件；工作树里唯一的**未跟踪**文件
   `.spec/hof-rs/tasks/TASK-DR59-ACCEPT.md` **不是本批产物**（它在本会话进行中由调度方出现，
   我未创建、未读取、未修改、未提交），除此以外 `git status --porcelain` 为空。
9. **提交计数**：本批共 4 个本地提交（3 个代码/测试 + 1 个本报告）。
   门（§1）跑在**纯代码状态** `7fab86b` 上（当时工作树干净）；本报告是纯 Markdown，不参与编译。
