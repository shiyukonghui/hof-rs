# TASK-DR71-REPORT — 让"路由永不撒谎"：就绪后再发布 + 失败必撤下 + 补失败路径测试 + 统一 `editor_play_scene` + 字节声明由命令计算

- 实施者：本批实现子代理（无上游对话上下文，唯一任务来源 `.spec/hof-rs/tasks/TASK-DR71.md`）。
- 对象仓库：`F:\moonbit-hof-rs`。本批基线 = 任务书提交 `553dec2`（其父 `95b3f9b` = D274）。
- 最终 `HEAD = 77c46fe`。本批 5 个 `(DR-71)` 提交（见 §5.6）。
- 离线：**未启动 Godot、未触碰任何外部端口、未联网、未调用任何模型端点、未跑真机轮次**。
  唯一使用的套接字是交付测试本身的 `127.0.0.1` 回环替身（与本仓既有 DR-70 测试同一做法）。
- 写入范围：`src/**`、`tests/**`、`scripts/byte_claims.py`、
  `.spec/hof-rs/tasks/{TASK-DR70-REPORT.md, TASK-DR71-REPORT.md}`、
  `.spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/REDACTION.md`，以及 §4 的受控植入（逐一逐字节回退）。
  **`runs/**` 零写入**（§5.1）；分析脚本、备份、探针产物全部在仓外
  `C:\Users\wyl\AppData\Local\Temp\dr71\`。

---

## 1. 结论 + 门

**门通过。** `cargo test --offline`（先按任务书要求**逐文件 `touch` 全部已跟踪 `.rs`** 强制重编，
`git ls-files '*.rs' | while IFS= read -r f; do touch "$f"; done`，**未使用任何通配符**，
`TOUCHED=89`）：

```
test result: ok. 10 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 23.16s

   Doc-tests hof_rs

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

CARGO_EXIT=0
```

- 汇总（对 53 条 `test result` 行求和）：**465 passed / 0 failed / 7 ignored**，`CARGO_EXIT=0`。
- 基线 455 / 0 / 7 → **+10 条测试**（`tests/**` 的 `#[test]|#[tokio::test]` 出现次数 330 → 340，
  **被删除的测试属性行 = 0**；`tests/godot_smoke.rs` 的 `#[ignore` 出现次数 8 == 8）。
  `ignored` **未增长**（7 == 7），无既有测试被删。
- `cargo fmt --check` → **`FMT_EXIT=0`**（干净）。
- 源码改写方式：全部用编辑工具/字节干净的 Python 脚本（`scripts/byte_claims.py` 写 UTF-8 + 保留原行尾），
  **未使用 PowerShell 5.1 的 `Get-Content -Raw` + `Set-Content` 改写任何源码**；
  唯一一次整文件写入是"从备份/`git show` 复制回来"的字节级 `cp`（§4）。

四项交付状态一览：

| 项 | 内容 | 状态 |
|---|---|---|
| ① | 路由永不撒谎：**先确认就绪再发布**（两处：轮次游戏 + 电池）+ **任何启动失败必撤下** + **发布失败不再静默** | 已交付（§2、§3.1） |
| ② | **已交付测试**驱动失败的 `start_round_game`：无 route / 轮次继续 / 角色拿到明确拒绝 | 已交付（§3.2） |
| ③ | `editor_play_scene` 三处统一裁决 + 受众感知守卫扩到 `developer.md` | 已交付（§3.3） |
| ④ | 字节声明**由命令计算**（生成块 + 独立复算测试），更正 52/28 与 23/28 | 已交付（§3.4） |

---

## 2. ① 的机制选择：**两条都做**（就绪后再发布 **且** 失败必撤下），外加"发布失败不静默"

三者不是替代关系，各自堵一个洞，因此**全部实现**：

1. **先确认就绪、再发布（消除"发布-未就绪"窗口）**——这是根治项。DR-70 的顺序是先
   `register_game_endpoint`（= 写文件即发布），再 `wait_for_game_ready` 轮询；轮询失败时
   文件已经在盘上。现在把"注册"拆成两个语义分离的步骤（`src/tools/mod.rs`）：
   - `install_game_endpoint`（`:83` 默认实现 / `:428` `McpChannel`）——**只装进进程内路由，不写文件**，
     所以轮询可以打到被宣告的游戏端点，而**其它进程此时看不到任何路由**；
   - `publish_game_endpoint`（`:94` / `:439`）——把当前已安装的记录写进发布文件，**失败是一个返回值**；
   - `register_game_endpoint`（`:73`）现在就是上面两步的**组合**（默认实现即组合），
     因此只覆盖它的既有实现者行为不变（电池/双端点的调用点语义不变）。
   - `src/adapter/godot.rs::start_round_game`（`:3882`）→ `:3898` 只 `install`，
     轮询成功后才 `:3931 publish`；
     **电池的 `step_play_scene`（`:909` install，`:980` publish）同样顺序**——电池里
     "先发布后就绪失败"是同一个洞的另一个入口（DR-71 任务书只点名 `start_round_game`，
     但"路由永不撒谎"要求两处一致）。
2. **任何 Err 路径必撤下（幂等）**——适配器与运行时包装层**两层都做**：
   - 适配器：未就绪分支 `:3919`、发布失败分支 `:3932`、电池未就绪/形状不合法分支
     `:1013`/`:1039` 都 `clear_game_endpoint()`（丢进程内路由 + 撤下文件）；
   - 运行时包装层 `src/runtime/run_loop.rs::start_round_game`（`:535`）：`Err` 分支
     无条件 `clear_game_endpoint()` + `withdraw_game_route(game_route_path(run_dir))`，
     **不依赖适配器是否记得撤**（DR-70 验收的建议 1）。
3. **发布失败不得静默**——DR-70 的 `src/tools/mod.rs:401-403` 是 `let _ = publish_game_route(...)`，
   而 `godot.rs:3850-3852` 的注释却称注册失败是致命的。现在
   `publish_game_endpoint` 把 `std::io::Error` 映射成 `anyhow`（含路径与端点）返回；
   `start_round_game` 把它变成**失败的启动**并撤下（连电池步骤也判 `ok=false`）。
   顺带修掉 `publish_game_route`（`src/tools/endpoint.rs:104`）失败时把
   `*.json.tmp-publish` 临时文件留在原地的问题（失败即清理）。

### 2.1 "失败必无 route"的真实红→绿输出

**红（修复前，先写的测试）**——`tests/round_game_window.rs::a_failed_round_game_start_leaves_no_route_and_the_round_proceeds`
驱动**真实** `run_loop::run`：替身在"发布后失败"这一形状上启动轮次游戏，并在 Developer 步骤内
启动**真实 `hoh` 二进制**（`HOH_GAME_ROUTE`）当作角色 shell：

```
test a_failed_round_game_start_leaves_no_route_and_the_round_proceeds ... FAILED
thread '...' panicked at tests\round_game_window.rs:441:5:
a start that failed after publishing must leave no route for the first role:
RoleProbe { route_exists: true, exit_code: Some(0), stdout: "{\n  \"content\": [\n    {\n
\"text\": \"{\\\"tree\\\":{\\\"name\\\":\\\"Main\\\",\\\"path\\\":\\\"/root/Main\\\"}}\",\n
\"type\": \"text\"\n    }\n  ],\n  \"tools\": []\n}\n", stderr: "" }
test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 3 filtered out; finished in 14.98s
```

读法：`route_exists: true` **且** `exit_code: Some(0)`——角色 shell 不但看得见那条路由，
还**成功采纳**了它（这正是 DR-70 验收 §3 的 case B/C 在交付套件里的复现）。

**绿（修复后，同一 target 全部 4 条）**：

```
running 4 tests
test a_failed_round_game_start_leaves_no_route_and_the_round_proceeds ... ok
test a_failing_round_still_withdraws_the_published_route ... ok
test a_route_left_by_another_round_is_not_inherited ... ok
test the_published_route_covers_the_developer_and_tester_windows ... ok
test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 1 filtered out; finished in 22.26s
```

**适配器层的独立红→绿**（`tests/round_game_start.rs`，驱动**真实 `GodotAdapter::start_round_game`**
与回环 MCP 替身，无 Godot、无外部端口）：

```
# 红（修复前）
---- a_start_that_never_becomes_ready_publishes_no_route stdout ----
thread '...' panicked at tests\round_game_start.rs:226:5:
the record must not be published before readiness is confirmed; found
Ok("{\"endpoint\":\"http://127.0.0.1:64775/mcp\",\"port\":64775,\"source\":\"auto_free_port\",\"pid\":124600}")
---- a_publish_failure_is_reported_instead_of_swallowed stdout ----
thread '...' panicked at tests\round_game_start.rs:302:5:
a route that could not be published must fail the start, not be swallowed:
Ok(Some(GameEndpointRecord { endpoint: "http://127.0.0.1:64781/mcp", port: Some(64781),
source: "auto_free_port", pid: Some(124600) }))
test result: FAILED. 1 passed; 2 failed; 0 ignored; 0 measured; 3 filtered out; finished in 4.62s

# 绿（修复后）
running 4 tests
test a_publish_failure_is_reported_instead_of_swallowed ... ok
test a_ready_game_is_published_with_the_record_the_start_confirmed ... ok
test a_start_that_never_becomes_ready_publishes_no_route ... ok
test an_unconfirmed_battery_play_never_exposes_a_route ... ok
test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 4.68s
```

---

## 3. ②③④ 的落点与红→绿

### 3.1 ② 补上"失败的 `start_round_game`"的已交付测试（Err 臂）

**落点**

- `tests/common/mod.rs:415`（`RoundGameStub`）新增字段 `fail_after_publish` 与
  `:444 RoundGameStub::failing_after_publish()`；`FakeAdapter::start_round_game`
  **先 `register_game_endpoint` 再 `bail!`**——精确复刻 DR-70 真实适配器的形状
  （先发布，后轮询失败，且不撤下）。此前的替身只产生 `Ok(None)`/`Ok(Some)`
  （DR-70 验收 A4：`tests/common/mod.rs:547-566`）。
- `tests/round_game_window.rs:395`：`a_failed_round_game_start_leaves_no_route_and_the_round_proceeds`。

**断言（三件事全覆盖，红→绿见 §2.1）**

| | 断言 | 修复前 | 修复后 |
|---|---|---|---|
| (a) 无 route 残留 | 第一个角色窗口内 `!route_exists`、轮次结束后 `!route.exists()` | **RED**（`route_exists: true`） | ok |
| (b) 轮次优雅降级 | `result.is_ok()`，且 `warnings.log` 含 `could not be started` | ok（该属性本就成立） | ok |
| (c) 明确拒绝而非撒谎路由 | `exit_code != Some(0)` 且输出含 `game_endpoint_unavailable`，且游戏端点 `tools().is_empty()` | **RED**（`exit_code: Some(0)`、游戏端点被调用） | ok |

**另加适配器/电池层的三条**（`tests/round_game_start.rs:243/:284/:322/:377`）：
未确认就绪不发布（红→绿见 §2.1）、已确认就绪发布**且发布的是被确认的那条记录**、
发布失败必须可见（A5 的红→绿见 §2.1）、电池里"未确认的 play 不得暴露 route"。
最后一条特意用**替身在每次请求到达时记录"此刻盘上有没有 route"**，而不是只看函数返回后的终态——
因为电池自己的 `editor_stop_scene` 步骤总会收尾撤下文件，只看终态**无法辨别顺序**
（这一条我实测过：初版测试对植入 P5 仍然全绿，见 §4.2 的说明）。

**测试替身的两处随之更新（断言未改动）**：`tests/dual_endpoint.rs:443`、`tests/launchable_gate.rs:181`
的双端点在 `register_game_endpoint` 里记录注册记录；因为电池改为先 `install` 后 `publish`，
两处补上 `install_game_endpoint` 记录同一记录。**被记录的字段与断言逐条不变**
（endpoint / port / source / pid / DR-51 的 history），这不是放宽，而是 API 拆分后的等价适配：
若不做，DR-51 的 `meta.engine.mcp.game_endpoint` 会回归为 `null`——该回归我在第一次门跑时就实测到了
（`the_run_meta_keeps_the_game_endpoint_the_battery_registered` FAILED，`left: Null`）。

### 3.2 ③ `editor_play_scene` 的统一裁决

**裁决：(i) 由运行时拥有轮次会话**（删掉角色的自起场景指令）。理由（第一性原理，非折中）：
DR-70 的整轮路由只有在"运行时启动、运行时确认、运行时撤下"时才可能不撒谎；
角色再起一个场景会 (1) 与运行时那条会话竞争/顶替，(2) 让"Tester 该到达的那条游戏"消失，
(3) 重新制造"路由指向一个没被确认的会话"。因此 `developer.md` 必须与 skill 一致地说"不要自起"。

**落点**

- `src/prompts/developer.md:113`（`[self-test]`）：实时路径列表移除 `editor_play_scene`，
  改为"运行时拥有轮次会话，**不要自己起游戏**（`editor_play_scene`）：第二次启动会顶替
  Tester 要到达的那条会话，而且它跑的是**你改代码之前**的版本"。
- `src/prompts/developer.md:142`（`[definition-of-done]` #3）：保留 `editor_get_errors` 的编辑器侧检查，
  把"用 `editor_play_scene` 启动场景"改为禁止句。
- `src/prompts/skills/godot-dev.md:88`（§5）：维持原裁决（本轮未改），三处自此一致。
- `tests/delivered_materials.rs:157`：新增
  `the_developer_prompt_and_the_skill_forbid_booting_a_game_the_same_way`——
  在**两份**文档上都要求 (a) 提到该命令、(b) 逐字携带统一裁决
  `do not start a game of your own`、(c) **任何提到该命令的句子必须是否定句**
  （`imperative_play_scene_sentence`，按句子切分 + 否定词表；文档是散文，纯子串匹配分不清禁令与命令）。
- `tests/delivered_materials.rs:190`：受众感知守卫**扩展到同时检查 `developer.md`**
  （原来只查 skill 的 `tools call editor_play_scene`）——这正是 DR-70 允许两处继续分叉的盲区。
- `tests/e1_increment.rs:780` 起：**需求驱动地改期望**。旧断言只要求提示词**含有**
  `editor_play_scene` 这个字符串，钉住了工具名却**钉不住极性**——过期提示词正是用这点自由度
  下了"启动场景"的命令。新断言要求 `[definition-of-done]` 段**逐字携带禁令**
  （`do not start a game of your own`）且**不得出现** `boot the scene with`。
  这不是放宽：旧断言可以被一句"启动场景"命令满足。

**红→绿**

```
# 红（developer.md 未改，先写的测试）
thread 'the_developer_prompt_and_the_skill_forbid_booting_a_game_the_same_way' panicked at
tests\delivered_materials.rs:168:9:
developer.md must carry the unified ruling verbatim (`do not start a game of your own`), so the two
Developer-facing documents cannot drift apart again

# 绿
running 6 tests
test the_developer_prompt_and_the_skill_forbid_booting_a_game_the_same_way ... ok
test the_developer_skill_explains_why_the_game_process_is_not_its_self_test ... ok
...
test result: ok. 6 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 2.06s
```

（`e1_increment` 的 14 条、`developer_contract` 的 5 条同批全绿。）

### 3.3 ④ 字节声明由命令计算

#### 3.3.1 事实更正（旧文字保留 + 标注"已更正"）

- `.spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/REDACTION.md`：顶部新增 **"CORRECTION (DR-71)"** 框，
  声明 DR-70 框里 `54`/`30`、`25`/`30` 两组数字**失实**；DR-70 原文**逐字保留**，
  并在原处插入 `**(DR-71: both figures are wrong …)**` / `**(DR-71: \`25\`/\`30\` are wrong too …)**`
  的就地标注；DR-69 的 "**53 bytes** were removed" 仍在 "Superseded DR-69 text" 小节里**逐字保留**。
- `.spec/hof-rs/tasks/TASK-DR70-REPORT.md` §3.5：两句原文保留，就地插入 `**（DR-71 更正：…）**`；
  新增 §3.5b 说明更正方式。
- 真值（**由命令算出，见 §3.3.2**）：DR-69 的替换跨度 **52 → 28**，DR-70 的替换跨度 **23 → 28**
  （DR-70 验收 A2 的复算值与我这里的独立复算一致）；净差 **−24 / +5** 与全部结构事实
  （184/183/184、LF/CR、`dir /b -p`）本就正确、未改。

#### 3.3.2 生成式机制：脚本计算 + 独立复算测试（禁止手写数字）

**机制**：`scripts/byte_claims.py`
（`--emit` 打印 / `--check` 校验 / `--write` 写入）从**两个 git blob**（`dc9d350` 原版、
`3adab37` DR-69 版）与**工作树文件**计算：字节总数、CR、LF、记录数（非空 LF 段）、
`dir /b -p` 命中数，以及两次替换的 removed/inserted 跨度（最长公共前缀/后缀）。
它把结果写进每份文档里成对的 `DR-71-BYTE-CLAIMS` 注释行之间（**保留原行尾**：
有 CRLF 用 CRLF，否则 LF）。**注释行必须独占一行**：脚本与测试都按"整行等于标记"
定位，因为报告完全可能把标记引用在散文里或引用在 `--emit` 样例里——
这类引用**不得**被当成生成块（本批就因为这点把 §3.3.2 的散文覆盖过一次，见 §7.8）。

脚本的输出（`--emit`，逐字引用；`tests/byte_claims.rs` 会独立复算并逐键比较）：

```
DR-71 generated byte claims - written by `python scripts/byte_claims.py --write`, re-computed by tests/byte_claims.rs.  Do not edit by hand.
path = .spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/experiment/dev1_commands.txt
original_blob = dc9d350
original_bytes = 52200
original_cr = 0
original_lf = 184
original_records = 184
original_dir_b_p = 1
dr69_blob = 3adab37
dr69_bytes = 52176
dr69_delta_bytes = -24
dr69_lf = 183
dr69_cr = 0
dr69_records = 183
dr69_dir_b_p = 0
dr69_replaced_bytes = 52
dr69_marker_bytes = 28
worktree_bytes = 52205
worktree_delta_bytes = 5
worktree_cr = 0
worktree_lf = 184
worktree_records = 184
worktree_dir_b_p = 1
worktree_replaced_bytes = 23
worktree_marker_bytes = 28
```

命令输出与复核：

```
$ python scripts/byte_claims.py --check
ok .spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/REDACTION.md
ok .spec/hof-rs/tasks/TASK-DR70-REPORT.md
ok .spec/hof-rs/tasks/TASK-DR71-REPORT.md
```

**被引用的三份文档**：`REDACTION.md`、`TASK-DR70-REPORT.md`、**本报告**。
每份文档另有一个成对的 `DR-71-CORRECTED` 注释行包围的区域，
区域内的**文字一个字节计数都不写**，只点名生成块的键（`dr69_replaced_bytes`、
`dr69_marker_bytes`、`worktree_replaced_bytes`、`worktree_marker_bytes`）。

<!-- DR-71-CORRECTED-BEGIN -->
本报告自身的字节声明同样不手写：更正后的两处替换跨度、三个版本（原 blob / DR-69 blob /
工作树）的字节总数、行尾、记录数与 `dir /b -p` 计数，全部是下方生成块里的键
（`dr69_replaced_bytes`、`dr69_marker_bytes`、`worktree_replaced_bytes`、
`worktree_marker_bytes`，以及其余键），由 `scripts/byte_claims.py --write` 计算并写入，
`tests/byte_claims.rs` 独立复算并逐键比较；本区域刻意不含任何手写字节计数。
<!-- DR-71-CORRECTED-END -->

<!-- DR-71-BYTE-CLAIMS-BEGIN -->
DR-71 generated byte claims - written by `python scripts/byte_claims.py --write`, re-computed by tests/byte_claims.rs.  Do not edit by hand.
path = .spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/experiment/dev1_commands.txt
original_blob = dc9d350
original_bytes = 52200
original_cr = 0
original_lf = 184
original_records = 184
original_dir_b_p = 1
dr69_blob = 3adab37
dr69_bytes = 52176
dr69_delta_bytes = -24
dr69_lf = 183
dr69_cr = 0
dr69_records = 183
dr69_dir_b_p = 0
dr69_replaced_bytes = 52
dr69_marker_bytes = 28
worktree_bytes = 52205
worktree_delta_bytes = 5
worktree_cr = 0
worktree_lf = 184
worktree_records = 184
worktree_dir_b_p = 1
worktree_replaced_bytes = 23
worktree_marker_bytes = 28
<!-- DR-71-BYTE-CLAIMS-END -->

**测试**（`tests/byte_claims.rs`，4 条）：

| 测试 | 行 | 作用 |
|---|---|---|
| `the_generated_byte_claims_match_the_computed_facts` | `:242` | 用 **Rust 独立复算**（`git show` 两个 blob + 当前文件）逐键**且按序**比对三份文档的生成块；只有一行表头（须含 `scripts/byte_claims.py`） |
| `the_corrected_record_states_no_hand_written_byte_count` | `:262` | 更正区域必须点名四个键，且**不得出现 `<数字> + 字节单位`**（`52 bytes` / `(25 B)` / `28 字节` 都命中） |
| `the_superseded_byte_counts_are_preserved_and_annotated` | `:292` | 旧文字（`replacing 54 bytes with a 30-byte marker`、`(25 bytes) became`、`**53 bytes** were removed`）必须仍在，且必须带 DR-71 更正标注 |
| `the_hand_written_claim_detector_works` | `:365` | 探测器自身的非空洞性（认出 `54`/`30`/`25`/`28`，不误伤 `dr69_replaced_bytes`、`DR-71`、`§3.5`） |

**红→绿**：

```
# 红 1（把两份文档退回 DR-71 之前的字节，即"更正尚未存在"）
thread '...' panicked at tests\byte_claims.rs:205:32:
.spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/REDACTION.md must contain a generated byte-claims block
thread '...' panicked at tests\byte_claims.rs:224:13:
.spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/REDACTION.md must carry a DR-71 corrected region between the markers
thread '...' panicked at tests\byte_claims.rs:264:5:
REDACTION.md must annotate the superseded figures as corrected, in place
test result: FAILED. 1 passed; 3 failed; 0 ignored; 0 measured; 4 filtered out; finished in 0.10s

# 红 2（把生成块里的正确值改成 DR-70 原写的错值 52 → 54）
thread 'the_generated_byte_claims_match_the_computed_facts' panicked at tests\byte_claims.rs:230:9:
assertion `left == right` failed: ... the generated claims must equal the recomputed facts, key by key
and in order.  Regenerate with `python scripts/byte_claims.py --write`; never edit a number by hand
  left:  ... ("dr69_replaced_bytes", "54") ...
  right: ... ("dr69_replaced_bytes", "52") ...
test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 3 filtered out; finished in 0.09s

# 绿
running 4 tests
test the_generated_byte_claims_match_the_computed_facts ... ok
test the_corrected_record_states_no_hand_written_byte_count ... ok
test the_superseded_byte_counts_are_preserved_and_annotated ... ok
test the_hand_written_claim_detector_works ... ok
test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.13s
```

**依赖说明**：`tests/byte_claims.rs` 需要 `git` 在 `PATH` 上（历史 blob 无法从工作树重算），
缺 `git` 或 blob 不可达时它**明确失败**而不是跳过（不允许假绿）。这不新增任何 **Cargo 依赖**；
`scripts/byte_claims.py` 只用标准库 + `git`。故**无新依赖**（§5.4）。

---

## 4. 非空洞性：受控植入与逐字节回退

驱动脚本在**仓外**：`C:\Users\wyl\AppData\Local\Temp\dr71\plants.py`
（`apply|restore|verify <id>`；每次植入前把目标文件逐字节备份到仓外
`C:\Users\wyl\AppData\Local\Temp\dr71\bak\`）。**P1..P5 全部落在生产代码 `src/**`**
（`src/prompts/developer.md` 由 `include_str!` 编进二进制并注入角色视图，属生产交付材料——
DR-70 验收对 `godot-dev.md` 采用同一判定）；P6 落在**被提交证据文档**上，是本批第 ④ 项的补充植入，
**不计入"生产代码植入 ≥4"**，但同样逐字节回退。

### 4.1 五处生产代码植入（各自使对应测试红）

| 植入 | 文件（生产） | 禁用的机制 | 红（真实输出，截断） |
|---|---|---|---|
| **P1-run-loop-no-withdraw** | `src/runtime/run_loop.rs:545` | 包装层 `Err` 分支的 `clear_game_endpoint` + `withdraw_game_route` | `round_game_window`：`a start that failed after publishing must leave no route for the first role: RoleProbe { route_exists: true, exit_code: Some(0), ... }` → `FAILED. 0 passed; 1 failed` |
| **P2-start-publishes-before-ready** | `src/adapter/godot.rs:3898` + `:3919` | 轮次游戏改为"发布早就绪"，且失败不撤下（= DR-70 原形） | `round_game_start`：`the record must not be published before readiness is confirmed; found Ok("{\"endpoint\":\"http://127.0.0.1:63024/mcp\",...}")` → `FAILED. 0 passed; 1 failed` |
| **P3-publish-failure-swallowed** | `src/tools/mod.rs:457` | 把发布错误映射改回 `let _ = ...; Ok(())`（= A5 原形） | `round_game_start`：`a route that could not be published must fail the start, not be swallowed: Ok(Some(GameEndpointRecord {...}))` → `FAILED. 0 passed; 1 failed` |
| **P4-developer-boots-its-own-game** | `src/prompts/developer.md:142` | 把 `[definition-of-done]` #3 改回"boot the scene with `editor_play_scene`" | `delivered_materials`：`developer.md still orders the Developer to boot a game (\`editor_play_scene\`): \`check \`editor_get_errors\` for \`{"errors": []}\`, ... and boot the scene with \`editor_play_scene\` before you end the turn\`` → `FAILED. 0 passed; 1 failed` |
| **P5-battery-publishes-before-ready** | `src/adapter/godot.rs:909` + `:1039` | 电池改为"发布早就绪"，且未就绪分支不撤下 | `round_game_start`：`the battery published the route before it confirmed readiness, so the game endpoint saw it in flight during ["running_game_get_scene_tree"]; the whole sequence was [("running_game_get_scene_tree", true)]` → `FAILED. 0 passed; 1 failed` |

### 4.2 补充植入（非生产代码，同样逐字节回退）

| 植入 | 文件 | 机制 | 红 |
|---|---|---|---|
| **P6-doc-hand-written-byte-count** | `.spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/REDACTION.md` | 生成块里把 `dr69_replaced_bytes = 52` 手改成 `54`（DR-70 的原错值） | `byte_claims`：`assertion left == right failed: ... ("dr69_replaced_bytes", "54") ... ("dr69_replaced_bytes", "52")` → `FAILED` |

### 4.3 逐字节回退证明（四重判据 + `cmp`）

`plants.py verify` 的原始输出（每个文件一行；`byte == backup` 是**逐字节**比较，
强制项是因为本仓 `core.autocrlf=true`，行尾改写对 git 不可见）：

```
P1: src/runtime/run_loop.rs      bytes==backup:True  sha256:5b55bb0dfd7e9cf0  hash-object:d50638e81f1d ==HEAD:True
    porcelain lines=0  diff --stat bytes=0
P2: src/adapter/godot.rs         bytes==backup:True  sha256:556a780e264973df  hash-object:fef2ac7b9299 ==HEAD:True
    porcelain lines=0  diff --stat bytes=0
P3: src/tools/mod.rs             bytes==backup:True  sha256:8ecf110a826f4a45  hash-object:fdf44b92198a ==HEAD:True
    porcelain lines=0  diff --stat bytes=0
P4: src/prompts/developer.md     bytes==backup:True  sha256:f3e41db3eef065d3  hash-object:2126a2e64fdf ==HEAD:True
    porcelain lines=0  diff --stat bytes=0
P5: src/adapter/godot.rs         bytes==backup:True  sha256:556a780e264973df  hash-object:fef2ac7b9299 ==HEAD:True
    porcelain lines=0  diff --stat bytes=0
P6: .../REDACTION.md             bytes==backup:True  sha256:71ea30e024bc6088  hash-object:bc1fc2ca5bf3 ==HEAD:True
    porcelain lines=0  diff --stat bytes=0
```

`cmp` 对**仓外备份**（bash，逐个文件）：

```
cmp OK run_loop.rs
cmp OK godot.rs
cmp OK mod.rs
cmp OK developer.md
cmp OK REDACTION.md (fixed copy)
cmp OK REDACTION.md (plant backup)
```

即：`git status --porcelain -uall` **0 行**、`git diff --stat` **0 字节**、
`git hash-object == HEAD:<path>`、**且与仓外备份逐字节相同**。

### 4.4 植入落在承载不变量的测试里？

**没有**。P1..P5 全部只落在 `src/**`（`developer.md` 是 `include_str!` 生产材料）。
植入期间我**只运行对应的测试 target**，未改动任何测试文件来"配合"植入；
P6 落在被提交证据文档上，且**已在 §4.2 显式标注为非生产植入**。

### 4.5 一处诚实记录：初版电池测试是空洞的（自查发现并修好）

电池路径的初版测试只断言 `evidence_battery` 返回后盘上没有 route。**植入 P5 时它仍然全绿**——
因为电池自己的 `editor_stop_scene` 步骤无论如何都会在收尾撤下文件。我据此把断言改成
"替身在**每次请求到达时**记录此刻盘上有没有 route"（`tests/round_game_start.rs` 的
`RpcDouble::watching`），P5 随即变红（§4.1 末行）。这条记录留在报告里，是因为它正是
"看起来通过了"与"真的被验证了"的差别；对应提交 `9d6a6f8`。

---

## 5. 禁区自查（真实输出）

### 5.1 `runs/**` 四条基线未动 + 摘要口径自证 + 写-删检查

口径与 DR-69/DR-70 完全一致（Windows PowerShell 5.1 `Get-ChildItem -Recurse -Force -File`；
仓根相对**小写 POSIX** 路径 + 字节数 + 小写 SHA256，三列 `\t` 连接、`\n` 分行，
整体 UTF-8 取 SHA256；行序 `Sort-Object` 文化排序）：

```
smoke-t6 files=135 hash=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03 newest=09/29/2026 02:32:01 newer_files=0 newer_dirs=0
smoke-t7 files=115 hash=6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7 newest=09/29/2026 14:41:14 newer_files=0 newer_dirs=0
smoke-t8 files=358 hash=6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7 newest=09/30/2026 07:58:28 newer_files=0 newer_dirs=0
smoke-t9 files=83  hash=541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d newest=09/30/2026 11:27:29 newer_files=0 newer_dirs=0
```

**自证**：这四条 hash 与 DR-70 验收 §4 记录的**逐位相同**（含 `smoke-t6` 的已知锚点
`c144ef32…7a9c03`），且 `newest` mtime 也逐条相同 ⇒ 口径同源、四棵树**字节未变**。
切点 `2026-09-30 11:27:30` 之后，四棵树的**新文件数 = 0、新目录数 = 0** ⇒
本批对 `runs/**` **零写入**，连"写过再删"也没有（mtime 会留下痕迹，实测为 0）。

### 5.2 `.workspace/mario` / `PRD-mario.md`

```
live files = 17
snapshot files = 17
identical = True
sha256 .spec/hof-rs/PRD-mario.md = 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a
```

（按运行时排除集 `{.hoh,.git,.godot,.import}` 逐字节比对活体工程树与
`runs/smoke-t9/versions/1f3d20ed…`；PRD 的 sha256 与 DR-70 验收 §7.3 逐字相同。）

### 5.3 嵌套引擎未改 + pathspec 真命中对照

```
nested: git -C godot-mcp/godot rev-parse HEAD = fc63af77c33368c4a1bb839c95d19750554f63a3
nested porcelain lines = 0
outer pathspec control: ls-files godot-mcp = 6484 ; ls-files godot-mcp/godot = 0
```

### 5.4 无新依赖 / 禁区路径

```
git diff --numstat 95b3f9b..HEAD -- DECISIONS.md .workspace/mario PRD-mario.md godot-mcp Cargo.toml Cargo.lock
(空输出)
```

⇒ `DECISIONS.md`、`.workspace/mario/**`、`.spec/hof-rs/PRD-mario.md`、`godot-mcp/**`、
`Cargo.toml`、`Cargo.lock` **全部未改**；无新依赖。

### 5.5 未 push / 未 stage / 仓内无临时物

```
origin/master = 9aebbe15f13508d1ee5063505b2827ee59cc041a
git rev-list --count origin/master..HEAD = 25
git diff --cached --stat = 0 行
git status --porcelain -uall = 0 行
```

（`origin/master` 与 DR-70 验收记录相同；本批 5 个提交全部本地，未 push；工作树干净，
仓内无我留下的临时物——所有脚本/备份/日志都在 `%TEMP%\dr71\`。）

### 5.6 本批提交

```
77c46fe fix(evidence): compute the frozen record's byte claims with a script instead of by hand, and correct the two wrong run lengths (DR-71)
9d6a6f8 test(runtime): make the battery assertion discriminate the publish ordering, not just its end state (DR-71)
0925806 docs(prompts): unify the editor_play_scene ruling - the runtime owns the round's session, so the Developer prompt forbids a self-boot and the audience-aware guard checks it too (DR-71)
3c8228c test(runtime): drive a failing round-game start in the shipped suite and assert no route survives, the round proceeds, and the role gets DR-43's explicit refusal (DR-71)
e7c5cd6 fix(runtime): publish the round's game route only after readiness is confirmed, withdraw it on every failed start, and stop swallowing publish failures (DR-71)
553dec2 docs(spec): stage DR-71 so the route can never lie about a game that is not ready   # 基线（任务书）
```

说明：提交过程中我曾误用 `git commit --amend` 覆盖了第 5 个提交的信息（HEAD 当时在该提交上），
内容未丢（`git diff --stat 06eec7c f3dd064` 只有 `tests/round_game_start.rs`）。
我用 `git reset --soft` + 分批重提交把它整理成上表这 5 个语义提交，并把电池测试的强化独立成
`9d6a6f8`。这是本批的一次流程失误，记录在此以免"提交历史看起来一步到位"。

### 5.7 三个假绿陷阱：实测与正确读法

1. **不存在的 pathspec 什么都不说。**
   `git diff --stat -- definitely/not/a/real/path` → **空输出、`exit=0`**。
   对照：`ls-files godot-mcp = 6484` vs `ls-files godot-mcp/godot = 0`。
   **读法**：空 diff 在**证明 pathspec 真能命中之前**不构成证据。
2. **cmd 吃 `^`、且 `%errorlevel%` 在解析期展开。**
   `cmd /c "git rev-parse dc9d350^"` → `dc9d350dff7357fec88d532ed5d2661a6ce7de18`（`^` 根本没到 git，
   解析成了 `dc9d350` 自己）；`cmd /c "git cat-file -e dc9d350^:definitely/not/here & echo errorlevel=%errorlevel%"`
   → 命令确实 `fatal:` 了，却打印 **`errorlevel=0`**。bash 侧同题：
   `git cat-file -e dc9d350:<真路径>` → `exit=0`；`:definitely/not/here` → **`exit=128`**。
   **读法**：只有 bash 的结果在这里有证据力。
3. **外层仓不跟踪引擎树、工作区与 runs 目录。**
   `git check-ignore -v` → `.gitignore:12:runs/`、`.gitignore:11:.workspace/`、
   `.gitignore:33:godot-mcp/godot/`。
   **读法**：对**被忽略**路径上的空 diff 什么也证明不了；这正是 §5.1/§5.3 要用
   digest、嵌套仓 HEAD/status 与扁平字节比对的原因。

### 5.8 提交证据脱敏

```
secret values considered = 1 (lengths [51])
tracked files scanned = 6824
files containing a secret value = 0
dump: marker count=1, 'HOH_MODEL_API_KEY="$(cat' count=0, 'HOH_MODEL_API_KEY' count=1
```

（`config/model.secret.env` 的 51 字符值在 6824 个已跟踪文件中出现 **0** 次；
本批对 `REDACTION.md` 的改动只在 DR-71 更正框/生成块内，未恢复任何凭据通道。）

---

## 6. 遗留风险与未验证项（严格区分实测 / 推断）

### 6.1 实测（本批自己产出）

- 交付套件里，"失败的 `start_round_game`"现在有三重断言（无 route / 轮次继续 / 明确拒绝），
  且该测试在修复前**真实变红**、在 DR-70 原形（P1/P2）下**再次变红**。
- 真实 `GodotAdapter::start_round_game` 在"游戏永不就绪"时**不发布任何文件**，
  在"发布失败"时**返回 Err 且不留临时文件**（回环替身，无 Godot）。
- 运行时包装层对任意适配器的 `Err` 都撤下文件（P1 证明它单独承重）。
- 三份文档的字节声明与独立复算逐键一致；单改一个数字即红。

### 6.2 推断（未实测，不得当结论）

- **R1（最高）引擎级行为仍全部是推断**：没有真机轮次，所以"真实 Godot 在空工程上接受
  `editor_play_scene`""轮次级游戏进程能活过 Developer 的脚本写入/重载""引擎拒绝第二次 play"
  一律**未验证**。本轮只把**编排/通道级**的"失败必无 route"证到了可复现的粒度
  （真实 `run_loop`、真实 `hoh` 子进程、真实路由文件），**游戏与适配器启动在交付测试里仍是替身**
  （`tests/round_game_start.rs` 用的是真实 `GodotAdapter`，但 editor/game 是回环替身）。
- **R2 我**不给出真机成功率或概率——离线无法反证，给出任何数字都会是编造。
- **R3 发布/采纳不是"存在原子"**：`publish_game_route` 是"写临时文件 + remove + rename"，
  **内容**原子而**存在**不原子（DR-70 验收 C9 实测 8227 次读中 4759 次看到"没有路由"，0 次撕裂）。
  本批**没有**改这一点，也**没有**为它写测试或加锁；丢失模式仍是显式的
  `game_endpoint_unavailable`（明确拒绝），不是传输错误。⇒ 仍是一个"安全但未同步、未测"的竞态。
- **R4 路由文件仍是角色可写的信任边界**（DR-69 R4 未变）：`validate_published_route`
  不建立"这个端点就是本轮的这条游戏"。任何把角色 CLI 输出当游戏观测的判定都不应依赖该文件。
- **R5 `start_round_game` 仍不是"轮次级游戏进程存活"的证明**：只证明"启动时它答了一次
  `running_game_get_scene_tree`"。Developer 中途把游戏弄死这回事本轮仍未处理。
- **R6 6 小时有效期与 Windows 的 pid 复用**仍是 ② 里最弱的两环（未变）。
- **R7 测试对 `git` 的依赖**：`tests/byte_claims.rs` 要 `git` 与 `dc9d350`/`3adab37`
  两个 blob 可达；若未来重写历史把这两个提交变不可达，该测试会**失败**（设计如此，不静默跳过）。
- **R8 未验证项**：真机任何行为；非 Windows 的 pid 存活分支；多进程发布/采纳的正式竞态分析；
  panic 路径上的撤下（包装层只覆盖 `Err` 与正常返回，panic 会跳过）。

---

## 7. 诚实披露

1. **不声明 E1 / E3 已 met**：本批没有真机轮次，也没有跑 E1（增量）与 E3（交互）的评测；
   交付测试覆盖的是编排与通道语义。DR-70 交付里那句"角色真能到达游戏端点"的强表述在本批
   **不再复用**——本轮的证明范围是"**启动失败时路由不撒谎**"，不是"角色真能玩到游戏"。
2. **`②`/`③`/`④` 的红并不是"同一批同一次运行"留下的**：四次红分别在修复前、doc 回退、
   数字植入三种受控状态下取得，报告里逐段贴了原始输出，未作事后修饰。
3. **有意的范围外**：DR-71 任务书只点名 `start_round_game`；我**额外**把同一顺序修进电池
   （§2 第 1 条），因为它也在"轮次窗口"里发布路由。这是**扩展**，不是任务书要求；
   若评审认为越界，可单独 revert `src/adapter/godot.rs` 的 `step_play_scene` 部分——
   但那样会把"路由永不撒谎"缩小到只剩一个入口。
4. **测试替身改了两处**（`tests/dual_endpoint.rs`、`tests/launchable_gate.rs`），因为
   `ToolChannel` 的注册被拆成 install/publish。**断言逐条未改**；不做这个适配会造成
   DR-51 的 `meta.json` 字段回归（我在门跑里实测到了该回归并已修复）。这是适配，不是放宽。
5. **`e1_increment.rs` 的期望被改了**（§3.2）。它**不是**放宽：旧断言要求提示词含有工具名，
   可以被一句"启动场景"命令满足；新断言要求 `[definition-of-done]` 段逐字携带禁令。
6. **`tests/round_game_start.rs` 依赖 `git`**（§6 R7），且它的"发布-存在原子"缺口**未测**（R3）。
7. **流程失误**：提交历史的整理（§5.6）与电池测试初版的空洞（§4.5）都如实写进本报告，
   没有把"看起来通过"当成"已验证"。
8. **`④` 的第一次 `--write` 覆盖了本报告 §3.3.2 的散文**：因为报告把生成块的注释行
   引用在散文与 `--emit` 样例里，而当时的定位是"第一次出现的标记"。我发现后把定位改成
   **整行锚定**（脚本与测试同步改，§3.3.2），修复了被覆盖的段落，并按字节备份核对了
   其余内容；此后 `--check` 三份文档全绿。这条与 §5.6 是同一类教训：**工具自己的标记
   也是被工具解析的输入**，散文里引用它必须给自己留出安全边界。
