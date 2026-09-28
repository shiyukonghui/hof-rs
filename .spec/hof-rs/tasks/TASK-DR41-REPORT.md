# TASK-DR41（批次一）实现报告 — hof-rs 引擎换代：拆除 GDExtension 通道 + 工具契约迁移 + 双端点 + 引擎身份入库

- 范围：DR-41..DR-46（纯离线；DR-47 真机批次不在本次范围）
- 结论级别：`cargo test` **全绿**（exit 0，0 failed，7 ignored）
- 提交（外层仓 `master`，均带 DR 编号，未 `push`）：

```
b2ed193 tests: guard the repository against the retired tool vocabulary (DR-45)
60131e5 adapter: record the engine identity and gate on it before freezing (DR-44)
1d52b24 tools: route running_game_* to the game endpoint the engine announces (DR-43)
db2eed7 tools: migrate to the 177-tool four-channel contract and rewrite the role scopes (DR-42)
b6d9282 adapter: drop the bundled GDExtension addon and its stale extension cache (DR-41)
```
（第 6 个提交是本报告 `docs: TASK-DR41 implementation report for the engine-switch batch (DR-41..DR-46)`，紧随其后；
它自己的 hash 不便自引用，用 `git log` 查看。）

---

## 1. 结论

**做完了什么**

| 块 | 内容 | 状态 |
|---|---|---|
| DR-41 | `PROJECT_GODOT` 去掉 `[editor_plugins]`、`config/features` 改 `"4.8"`；新工作区不再复制 addon、不再写 `ADDON_MISSING.txt`；既有工作区**反向清理**（addons 目录 / `.godot/extension_list.cfg` / `[editor_plugins]`）且幂等；`adapter.godot.addon_source` 从结构体与 `config/hoh.yaml` 删除 | 完成 |
| DR-42 | 夹具重采为 177 条四通道契约（UTF-8 无 BOM）+ `PROVENANCE.md`；24 个文件的旧名按改名表逐条迁移；角色工具作用域按「四通道 + 只读动词集」重写 | 完成 |
| DR-43 | 按作用域路由端点（`running_game_*` 只去游戏端点）；`editor_play_scene` 响应解析并登记游戏端点，登记失败即使该步失败；`editor_stop_scene` 之后游戏端点失效、后续调用报错 | 完成 |
| DR-44 | `adapter.godot.editor_binary`；`hof doctor` 两项（`godot.engine_binary` / `godot.engine_version`）；`meta.json.engine` 固定字段块（缺值 `null` + `reason`）；经既有 `Environment` 抽象跑端口→PID→可执行体路径探针；可启动闸门新增 `engine_identity` 步；密钥卫生覆盖 `engine` 新键 | 完成 |
| DR-45 | 新增 `tests/tool_vocabulary.rs` 三条同时绿（177/四通道正则；旧词汇 0；反向：被引用的名字都必须在夹具里） | 完成 |
| DR-46 | 禁项自查（见 §6） | 完成 |

**未做什么**

- 批次二（DR-47 真机冒烟）**未做**：没有启动过引擎二进制，没有对活体 `tools/list` 逐字核对，没有真实端口 9877 的监听者探针，没有 `GET /mcp` 的 `editor_status` 实测。
- `meta.json.engine.mcp.editor_status` 在批次一恒为空对象 + `editor_status_reason`（离线不发起 `GET /mcp`）。
- 没有恢复任何旧名兼容层，也没有引入任何新依赖（`Cargo.toml` / `Cargo.lock` 在本批 5 个提交里 `git diff --stat` 为空）。

**`cargo test` 的真实输出尾部与退出码**

```
$ cargo test --offline > final.txt 2>&1 ; echo "EXIT=$LASTEXITCODE"
EXIT=0

   Doc-tests hof_rs

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

34 个 test target 全部 `test result: ok`，合计 **0 failed**。逐 target 计数：

```
test result: ok. 94 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.05s   (lib)
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s    (main)
test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 43.11s
test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 12.05s
test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 8.80s
test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.08s
test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 9.32s
test result: ok. 8 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 16.33s
test result: ok. 6 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.04s
test result: ok. 13 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.01s   (engine_identity)
test result: ok. 23 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 43.52s  (evidence_battery)
test result: ok. 12 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 14.25s
test result: ok. 0 passed; 0 failed; 7 ignored; 0 measured; 0 filtered out; finished in 0.00s    (godot_smoke)
test result: ok. 7 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 15.10s
test result: ok. 9 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 12.00s
test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.04s
test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.06s
test result: ok. 7 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 9.33s
test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 15.02s
test result: ok. 7 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 11.73s
test result: ok. 11 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 9.22s
test result: ok. 8 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 23.18s
test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.02s
test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 9.15s
test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 21.29s
test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.06s
test result: ok. 7 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 11.86s
test result: ok. 13 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 34.91s
test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.40s   (tool_vocabulary)
test result: ok. 12 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.13s
test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 10 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 14.10s
```

**`#[ignore]` / 环境门控（如实列出，未偷偷删除）**

- `tests/godot_smoke.rs`：**7 个用例全部 `#[ignore]`**（E1–E6 需要真机）。门控方式：`#[ignore]` + 运行时要求 `HOH_SMOKE=1` 环境变量，缺失即 panic（DR-9）；本批未运行（未安装/未启动任何引擎）。
- 其余 33 个 target 无 `#[ignore]`、无环境变量门控；`cargo test --offline` 即可全绿（无需网络、Godot、LM Studio）。
- `cargo build --offline`：0 warning（`Select-String -Pattern "warning|error"` 命中数为 0）。

---

## 2. 逐条判据对照（命令 + 真实输出片段 + 文件:行号）

### 2.1 DR-41

**① 新工程模板不含 `[editor_plugins]`**

```
$ cargo test --offline --lib adapter::godot::tests::the_project_template_drops_the_gdextension_channel
test result: ok. 1 passed; 0 failed
```

- 证据：`src/adapter/godot.rs:47`（`PROJECT_GODOT`，通读可见 `config/features=PackedStringArray("4.8")` 且无 `[editor_plugins]` 段）
- 测试断言：`src/adapter/godot.rs:3079` `the_project_template_drops_the_gdextension_channel`

**② 既有工程的清理幂等（字节比较）**

```
$ cargo test --offline --lib adapter::godot::tests::initialize_removes_a_legacy_bundled_addon_idempotently
test result: ok. 1 passed; 0 failed
$ cargo test --offline --lib adapter::godot::tests::initialize_removes_empty_remains_of_the_retired_channel
test result: ok. 1 passed; 0 failed
$ cargo test --offline --lib adapter::godot::tests::initialize_never_touches_a_project_without_the_retired_channel
test result: ok. 1 passed; 0 failed
```

- 实现：`src/adapter/godot.rs:2604`（`ensure_bundled_addon_disabled`）、`:2555`（`remove_bundled_addon_dir`）、`:2533`（`remove_stale_extension_cache`）、`:2654`（`initialize`）
- 红→绿的真实证据（TDD 红）：

```
thread 'adapter::godot::tests::the_project_template_drops_the_gdextension_channel' panicked at src\adapter\godot.rs:2871:9:
the template must not enable an editor plugin (DR-41)
thread 'adapter::godot::tests::initialize_removes_a_legacy_bundled_addon_idempotently' panicked at src\adapter\godot.rs:2921:9:
the exact addon directory must be removed (DR-41)
test result: FAILED. 11 passed; 5 failed; 0 ignored; 0 measured; 67 filtered out
```

**③ `addon_source` 0 命中**

```
$ (Select-String -Path (Get-ChildItem -Recurse src,tests,config -File).FullName -Pattern "addon_source" | Measure-Object).Count
0
```

**④ `cargo test` 中与 `PROJECT_GODOT`/`initialize` 相关的既有测试按新语义更新并绿** — 见 §5 (a)–(e)。

### 2.2 DR-42

**① 夹具 177 条且每条匹配 `^(editor|project|running_game|os)_[a-z0-9_]+$`**

```
$ cargo test --offline --test tool_vocabulary the_fixture_is_the_four_channel_contract
test the_fixture_is_the_four_channel_contract ... ok
test result: ok. 4 passed; 0 failed
```

- 断言：`tests/tool_vocabulary.rs:268`（条数 == 177、正则、四通道都非空）
- 夹具：`tests/fixtures/mcp/tools_list.json`（71481 B，sha256 `50c5fb4204ee5b957b017eb994e7f7bd73f9b299e6aa9471d5cf11683e067da0`）
- 来源与落盘形态：`tests/fixtures/mcp/PROVENANCE.md`
- TDD 红（真实失败输出）：

```
---- the_fixture_is_the_four_channel_contract stdout ----
thread 'the_fixture_is_the_four_channel_contract' panicked at tests\tool_vocabulary.rs:269:5:
the fixture must carry the 177-tool contract (DR-42)
test result: FAILED. 2 passed; 2 failed; 0 ignored; 0 measured; 0 filtered out
```

**② `tool_allowed(Planner, <任何写工具>) == false` 有测试**

- `tests/tools_policy.rs:163` `planner_is_denied_every_tool_of_the_contract`：遍历**整个 177 条契约**，断言 Planner 对每一条都是 false（比"任何写工具"更强）
- 另：`src/runtime/policy.rs:325` `a_write_verb_is_never_granted_to_a_read_only_role`（库内单测，覆盖 12 个写动词）

**③ `tool_allowed(QA, <任何写工具>) == false` 有测试**

- `tests/tools_policy.rs:117` `qa_is_denied_every_mutating_tool_of_the_contract`：遍历整个契约里所有 `is_mutating` 的名字（>50 条），断言 Tester 全 false，并断言"可达的写动词名字恰好等于两条已登记例外"
- 例外由生产常量导出（单一真源）：`src/runtime/policy.rs:233` `pub const QA_ALLOW_EXACT`，`tests/tools_policy.rs:17` 直接引用它

```
$ cargo test --offline --test tools_policy
test qa_is_denied_every_mutating_tool_of_the_contract ... ok
test planner_is_denied_every_tool_of_the_contract ... ok
test the_role_lists_only_name_contract_tools ... ok
test result: ok. 12 passed; 0 failed
```

**角色作用域重写**：`src/runtime/policy.rs:185`（`tool_matrix`）、`:209`（`QA_READ_VERBS`）、`:217`（`MUTATING_VERBS`）、`:242`（`verb_of`）、`:257`（`is_mutating`）、`:280`（`tool_allowed`）；`src/tools/policy.rs:8` re-export。

### 2.3 DR-43

**双端点假 MCP 断言（判据 ①）**

```
$ cargo test --offline --test dual_endpoint
test running_game_tools_never_reach_the_editor_endpoint ... ok
test stop_scene_invalidates_the_game_endpoint ... ok
test the_scope_of_a_tool_is_decided_by_its_channel_prefix ... ok
test the_play_scene_reply_is_parsed_into_the_game_endpoint ... ok
test the_play_scene_step_registers_the_announced_endpoint ... ok
test the_play_scene_step_fails_when_no_endpoint_is_announced ... ok
test result: ok. 6 passed; 0 failed
```

- 断言①：`tests/dual_endpoint.rs:164` —— 两个 loopback JSON-RPC 假端点；`running_game_get_scene_tree` 只出现在游戏端点的到达记录里，编辑器端点**从未**收到任何 `running_game_*`（`!editor.tools().iter().any(|t| t.starts_with("running_game_"))`）；未登记时该调用报 `game_endpoint_unavailable` 且两个端点都没收到请求。
- 断言②：`tests/dual_endpoint.rs:443` —— `editor_play_scene` 未回端口时 `play_scene_ready.ok == false`，observation 含 `neither an `endpoint` nor an `mcp_port`` 与 `UNAVAILABLE`，且 channel 未收到任何登记调用。
- 断言③：`tests/dual_endpoint.rs:230` —— `clear_game_endpoint` 后 `running_game_*` 报错，且游戏端点收到的请求数仍为 1（没有打到旧端口）。
- 实现：`src/tools/endpoint.rs`（scope/记录/URL 解析）、`src/tools/mod.rs:157`（`client_for` 按作用域选端点，未登记即报错，**禁止**回退）、`:229/:240/:246`（登记/失效/查询）、`src/adapter/godot.rs:1943`（`parse_game_endpoint`）、`:814`（`step_play_scene` 登记）、`:1864`（`step_stop_scene` 失效）。
- 端点信息进 `meta.json`：见 DR-44 的 `engine.mcp.game_endpoint`（`src/runtime/run_loop.rs` 在第一轮电池后写回）。

### 2.4 DR-44

**① `adapter.godot.editor_binary`**

- 结构体：`src/config.rs:109` `pub editor_binary: PathBuf`（`#[serde(default)]`：缺省即"未知"，记 `null` + `reason`，不编造）
- 配置：`config/hoh.yaml:41` 指向 mono 构建的绝对路径

**② `hof doctor` 两项**

```
$ cargo test --offline --test engine_identity the_two_engine_doctor_items_report_the_binary_and_its_version
test the_two_engine_doctor_items_report_the_binary_and_its_version ... ok
$ cargo test --offline --test engine_identity a_missing_binary_fails_the_items_without_executing_anything
test a_missing_binary_fails_the_items_without_executing_anything ... ok
```

- 实现：`src/adapter/engine.rs:503`（`doctor_items`），接入点 `src/cli_impl.rs:164`
- `godot.engine_binary`：ok = 路径是文件；detail = 路径 + `size` + `mtime`
- `godot.engine_version`：ok = `<binary> --version` 退出码 0；detail = 版本串**逐字**（`assert_eq!(version_item.detail, "4.8.dev.mono.custom_build.ba1587c71")`，测试 `tests/engine_identity.rs:423`）
- 代码里没有任何版本常量：`src/adapter/engine.rs:706` 用 `include_str!` 扫描自身并断言不含 `custom`+`_build`（C12）
- 二进制不存在时**不执行**：`tests/engine_identity.rs:458` 断言 `env.commands().is_empty()`

**③ `meta.json.engine` 固定字段块（缺值 `null` + `reason`）**

```
$ cargo test --offline --test engine_identity the_engine_block_has_the_fixed_shape
test the_engine_block_has_the_fixed_shape ... ok
$ cargo test --offline --test engine_identity a_missing_binary_is_null_plus_a_reason_never_a_guess
test a_missing_binary_is_null_plus_a_reason_never_a_guess ... ok
$ cargo test --offline --test engine_identity meta_json_carries_the_engine_block_and_no_secret
test meta_json_carries_the_engine_block_and_no_secret ... ok
```

- 契约键集合断言：`tests/engine_identity.rs:204` `ENGINE_KEYS = [kind, binary, version_string, version_reason, mcp, listener, checked_at]`（三个测试都断言"键集合完全一致"，缺一个键即失败）
- 结构体与默认值：`src/adapter/engine.rs:78`（`EngineIdentity`）、`:102`（`Default`）、`:111`（`unavailable`）
- 落盘：`src/runtime/record.rs:31` `pub engine: crate::adapter::EngineIdentity`（`#[serde(default)]`）
- 组装：`src/runtime/engine_identity.rs:23`（`probe`），调用点 `src/runtime/run_loop.rs:347`
- C11 扩展（`engine` 新键不得含密钥明文）：`tests/secret_hygiene.rs:100`（键存在性）+ `:107`（`engine` 串里不得出现假密钥）

**④ `listener.matches_binary` 经既有 `Environment` 抽象**

```
$ cargo test --offline --test engine_identity
test a_listener_that_is_the_configured_binary_matches ... ok
test a_listener_that_is_another_binary_is_a_mismatch ... ok
test a_probe_that_cannot_read_the_listener_is_unknown_never_a_match ... ok
test path_comparison_is_separator_and_case_insensitive ... ok
test result: ok. 13 passed; 0 failed
```

- 探针：`src/adapter/engine.rs:176`（`probe_listener`，`netstat -ano -p tcp` → PID → `powershell -NoProfile -Command "(Get-Process -Id <pid>).Path"`）、`:236`（`binary_matches`，规范化绝对路径、大小写不敏感、容忍 `//?/` 与 `..`）
- 无新增 crate 依赖（Cargo.toml / Cargo.lock 本批 diff 为空）
- 测试用 `FakeEnv`（实现 `mini_swe_agent::Environment`，`tests/engine_identity.rs:58`）离线覆盖匹配/不匹配/不可判定三种情形

**⑤ `engine_identity` 闸门步**

```
$ cargo test --offline --test engine_identity the_gate_closes_when_the_listener_is_another_binary
test the_gate_closes_when_the_listener_is_another_binary ... ok
$ cargo test --offline --test engine_identity the_gate_stays_open_when_the_listener_is_the_configured_binary
test the_gate_stays_open_when_the_listener_is_the_configured_binary ... ok
$ cargo test --offline --test engine_identity the_engine_identity_step_is_a_gate_step
test the_engine_identity_step_is_a_gate_step ... ok
```

- 步 id：`src/adapter/engine.rs:33` `ENGINE_IDENTITY_STEP_ID = "engine_identity"`
- 闸门词汇：`src/adapter/mod.rs:23`（`GATE_STEP_IDS` 三元素）、`src/adapter/mod.rs:38`（`evaluate_launchable`：所有**已声明**的闸门步都必须 ok；未声明的步跳过而不是臆造）
- 步的生成：`src/adapter/engine.rs:424`（`gate_record`），注入点 `src/runtime/run_loop.rs:263`（`run_battery_pass`，两轮电池都注入）
- 失败信息同列三件事（实机证据字符串，取自测试断言）：

```
FAILED engine identity: configured binary <配置的二进制> | actual listener C:\Other\godot.exe (pid 12345) |
engine identity mismatch: the configured binary is <配置的二进制> while the process listening on port 9877 is
C:\Other\godot.exe (pid 12345) (UNAVAILABLE: evidence produced by another engine is worthless, DR-44)
```

### 2.5 DR-45

```
$ cargo test --offline --test tool_vocabulary
test the_fixture_is_the_four_channel_contract ... ok
test the_retired_vocabulary_is_gone ... ok
test every_quoted_tool_name_exists_in_the_contract ... ok
test the_guard_recognises_both_vocabularies ... ok
test result: ok. 4 passed; 0 failed
```

- ① `tests/tool_vocabulary.rs:268`：177 条 + 四通道正则 + 四个通道都非空
- ② `tests/tool_vocabulary.rs:291`：**精确 174 条旧名**逐字整词扫描 `src/**`、`tests/**`（含 `src/prompts/**`），命中即失败
- ③ `tests/tool_vocabulary.rs:312`：反向——被引号引用（或紧接 `tools call `）的四通道名字必须都在夹具里
- 防误报写法（按要求写明）：
  1. 第 2 条查的是**冻结的 174 条旧名**，不是"凡不在夹具里的名字"。测试里合法地存在**臆造**名字（`totally_unknown_mcp_tool` / `brand_new_tool` / `frobnicate_world` / `x`）用于证明 default-deny，若按"不在夹具即命中"写就会误报。
  2. 第 3 条只看**引号内**（`` `name` `` / `"name"`）或 `tools call ` 之后的名字，因此 `project_declared_actions`（函数名，形状恰好像 channel 名）不会被当成工具名。
  3. 第 3 条再叠加"第二段必须是夹具里出现过的动词"（`contract_verbs()`，`tests/tool_vocabulary.rs:140`），于是 `editor_status` / `editor_endpoint` / `editor_errors_baseline` / `editor_process` / `os_error` 这类 JSON 字段名与步 id 全部自动排除。
  4. 剩余手工排除只有 **1 条**：`NON_TOOL_PREFIXED_TOKENS = ["project_reload_and_open"]`（`tests/tool_vocabulary.rs:88`），它是 DR-24 的电池步 id，动词 `reload` 恰好是契约里真实存在的动词，无法用规则排除。
  5. 第 2 条的扫描集合里排除了两个文件（`SCAN_EXCLUDES`，`tests/tool_vocabulary.rs:91`）：本守卫自身（它必须逐字写出旧词汇）与契约夹具 `tools_list.json`（其 `description`/`reason` 散文里可能提到旧名，已实测确实提到）。
- 已知假阴性边界：运行期拼接出来的名字、以及不在 `SCANNED_SUFFIXES` 里的文件类型不会被看到（在文件头注释里写明）。

### 2.6 DR-46

见 §6。

---

## 3. 旧名 → 新名映射表（完整 174 条）

说明：
- **作用域（端点）**由通道前缀决定（`src/tools/endpoint.rs:47` `scope_of`）：`editor_*` / `project_*` / `os_*` → 编辑器端点；`running_game_*` → 游戏端点（DR-43）。
- **作用域（角色）**列取自 rename map 的 `scope` 字段（`editor` / `game` / `both`→通用）。
- **语义是否变化**：绝大多数是纯改名（同一能力、同一输入输出形式）；非纯改名的 10 条按 rename map 的 `disposition` 标出并给出 reason 摘要。
- **依据** = `godot-mcp/godot/modules/mcp_server/docs/tool-rename-map.json` 的**行号**（该文件 sha256 `2f552719f6a23fe328df0a2944c6048824c1b2a750aebc0fe2cabbcd3529c2bd`）。
- 迁移方式：**逐条查表**（脚本读取 rename map，按整词边界、长名优先替换 24 个文件），随后人工复核全部改动行；两个策略文件（`src/runtime/policy.rs`、`tests/tools_policy.rs`）完全不使用脚本替换，由人按新契约重写。**没有**对载体做无差别正则替换。

| # | 旧名 | 新名 | 端点 | 角色作用域 | 语义变化 | 依据(map 行号) |
|---|---|---|---|---|---|---|
| 1 | `get_project_info` | `project_get_info` | editor endpoint | 通用 | 否（同一能力，仅改名） | 79 |
| 2 | `get_filesystem_tree` | `project_get_filesystem_tree` | editor endpoint | 通用 | 否（同一能力，仅改名） | 90 |
| 3 | `search_files` | `project_search_file_names` | editor endpoint | 通用 | 否（同一能力，仅改名） | 101 |
| 4 | `search_in_files` | `project_search_file_contents` | editor endpoint | 通用 | 否（同一能力，仅改名） | 112 |
| 5 | `get_project_settings` | `project_get_settings` | editor endpoint | 通用 | 否（同一能力，仅改名） | 123 |
| 6 | `set_project_setting` | `project_set_setting` | editor endpoint | 通用 | 否（同一能力，仅改名） | 134 |
| 7 | `uid_to_project_path` | `project_convert_uid_to_path` | editor endpoint | 通用 | 否（同一能力，仅改名） | 145 |
| 8 | `project_path_to_uid` | `project_convert_path_to_uid` | editor endpoint | 通用 | 否（同一能力，仅改名） | 156 |
| 9 | `get_scene_tree` | `editor_get_scene_tree` | editor endpoint | editor | 否（同一能力，仅改名） | 167 |
| 10 | `get_scene_file_content` | `project_read_scene_file_content` | editor endpoint | 通用 | 否（同一能力，仅改名） | 178 |
| 11 | `open_scene` | `editor_open_scene` | editor endpoint | editor | 否（同一能力，仅改名） | 189 |
| 12 | `delete_scene` | `project_delete_scene_file` | editor endpoint | 通用 | 否（同一能力，仅改名） | 200 |
| 13 | `add_scene_instance` | `editor_add_scene_instance` | editor endpoint | editor | 否（同一能力，仅改名） | 211 |
| 14 | `get_scene_exports` | `project_get_scene_exports` | editor endpoint | 通用 | 否（同一能力，仅改名） | 222 |
| 15 | `play_scene` | `editor_play_scene` | editor endpoint | editor | 否（同一能力，仅改名） | 233 |
| 16 | `stop_scene` | `editor_stop_scene` | editor endpoint | editor | 否（同一能力，仅改名） | 244 |
| 17 | `save_scene` | `editor_save_scene` | editor endpoint | editor | 否（同一能力，仅改名） | 255 |
| 18 | `create_scene` | `project_create_scene_file` | editor endpoint | 通用 | 否（同一能力，仅改名） | 266 |
| 19 | `add_node` | `editor_add_node` | editor endpoint | editor | 否（同一能力，仅改名） | 277 |
| 20 | `delete_node` | `editor_delete_node` | editor endpoint | editor | 否（同一能力，仅改名） | 288 |
| 21 | `rename_node` | `editor_rename_node` | editor endpoint | editor | 否（同一能力，仅改名） | 299 |
| 22 | `update_property` | `editor_set_node_property` | editor endpoint | editor | 否（同一能力，仅改名） | 310 |
| 23 | `get_node_properties` | `editor_get_node_properties` | editor endpoint | editor | 否（同一能力，仅改名） | 321 |
| 24 | `duplicate_node` | `editor_duplicate_node` | editor endpoint | editor | 否（同一能力，仅改名） | 332 |
| 25 | `connect_signal` | `editor_connect_signal` | editor endpoint | editor | 否（同一能力，仅改名） | 343 |
| 26 | `disconnect_signal` | `editor_disconnect_signal` | editor endpoint | editor | 否（能力不变；该工具实现先修，输入/输出形式见 reason）：作用于编辑场景信号连接，故 editor_；但实现忽略 target_path、固定用场景根作 Callable（node.rs:355），先修实现 | 354 |
| 27 | `move_node` | `editor_reparent_node` | editor endpoint | editor | 否（同一能力，仅改名） | 365 |
| 28 | `add_resource` | `editor_add_resource_to_node_property` | editor endpoint | editor | 否（同一能力，仅改名） | 376 |
| 29 | `set_anchor_preset` | `editor_set_anchor_preset` | editor endpoint | editor | 否（同一能力，仅改名） | 387 |
| 30 | `get_node_groups` | `editor_get_node_groups` | editor endpoint | editor | 否（同一能力，仅改名） | 398 |
| 31 | `set_node_groups` | `editor_set_node_groups` | editor endpoint | editor | 否（同一能力，仅改名） | 409 |
| 32 | `find_nodes_in_group` | `editor_find_nodes_in_group` | editor endpoint | editor | 否（同一能力，仅改名） | 420 |
| 33 | `get_editor_selection` | `editor_get_selection` | editor endpoint | editor | 否（同一能力，仅改名） | 431 |
| 34 | `select_nodes` | `editor_set_node_selection` | editor endpoint | editor | 否（同一能力，仅改名） | 442 |
| 35 | `clear_editor_selection` | `editor_remove_node_selection` | editor endpoint | editor | 否（同一能力，仅改名） | 453 |
| 36 | `execute_editor_script` | `editor_execute_gdscript` | editor endpoint | editor | 否（同一能力，仅改名） | 464 |
| 37 | `get_editor_errors` | `editor_get_errors` | editor endpoint | editor | 否（同一能力，仅改名） | 475 |
| 38 | `get_output_log` | `editor_get_output_log` | editor endpoint | editor | 否（同一能力，仅改名） | 486 |
| 39 | `get_editor_screenshot` | `editor_capture_screenshot` | editor endpoint | editor | 否（同一能力，仅改名） | 497 |
| 40 | `get_game_screenshot` | `running_game_capture_screenshot` | **game endpoint** | game | 否（同一能力，仅改名） | 508 |
| 41 | `clear_output` | `editor_remove_output_log` | editor endpoint | editor | 否（能力不变；该工具实现先修，输入/输出形式见 reason）：意图清空编辑器 Output 面板，故 editor_；但实现只向 stdout 打印空行（editor.rs:421），未清除面板，先修实现 | 519 |
| 42 | `reload_plugin` | `editor_reload_plugin` | editor endpoint | editor | 否（同一能力，仅改名） | 530 |
| 43 | `reload_project` | `editor_rescan_project_filesystem` | editor endpoint | editor | 否（同一能力，仅改名） | 541 |
| 44 | `get_signals` | `editor_get_node_signals` | editor endpoint | editor | 否（同一能力，仅改名） | 552 |
| 45 | `compare_screenshots` | `editor_analyze_screenshot_diff` | editor endpoint | editor | 否（同一能力，仅改名） | 563 |
| 46 | `set_auto_dismiss` | `editor_set_auto_dismiss_dialogs` | editor endpoint | editor | 否（能力不变；该工具实现先修，输入/输出形式见 reason）：设置编辑器对话框自动关闭行为，故 editor_；但实现只写无人读取的 static（editor.rs:618，全仓仅此一处引用），先修实现 | 574 |
| 47 | `get_editor_camera` | `editor_get_viewport_3d_camera` | editor endpoint | editor | 否（同一能力，仅改名） | 585 |
| 48 | `set_editor_camera` | `editor_set_viewport_3d_camera` | editor endpoint | editor | 否（同一能力，仅改名） | 596 |
| 49 | `get_game_scene_tree` | `running_game_get_scene_tree` | **game endpoint** | game | 否（同一能力，仅改名） | 607 |
| 50 | `get_game_node_properties` | `running_game_get_node_properties` | **game endpoint** | game | 否（同一能力，仅改名） | 618 |
| 51 | `set_game_node_property` | `running_game_set_node_property` | **game endpoint** | game | 否（同一能力，仅改名） | 629 |
| 52 | `capture_frames` | `running_game_capture_frames` | **game endpoint** | game | 否（同一能力，仅改名） | 640 |
| 53 | `monitor_properties` | `running_game_get_node_property_samples` | **game endpoint** | game | 否（同一能力，仅改名） | 651 |
| 54 | `execute_game_script` | `running_game_execute_gdscript` | **game endpoint** | game | 否（同一能力，仅改名） | 662 |
| 55 | `start_recording` | `running_game_create_input_recording` | **game endpoint** | game | 否（同一能力，仅改名） | 673 |
| 56 | `stop_recording` | `running_game_stop_input_recording` | **game endpoint** | game | 否（同一能力，仅改名） | 684 |
| 57 | `replay_recording` | `running_game_play_input_recording` | **game endpoint** | game | 否（同一能力，仅改名） | 695 |
| 58 | `find_nodes_by_script` | `running_game_find_nodes_by_script` | **game endpoint** | game | 否（同一能力，仅改名） | 706 |
| 59 | `get_autoload` | `running_game_get_autoload_node` | **game endpoint** | game | 否（同一能力，仅改名） | 717 |
| 60 | `batch_get_properties` | `running_game_get_node_properties_batch` | **game endpoint** | game | 否（同一能力，仅改名） | 728 |
| 61 | `find_ui_elements` | `running_game_find_ui_elements` | **game endpoint** | game | 否（同一能力，仅改名） | 739 |
| 62 | `click_button_by_text` | `running_game_simulate_button_click_by_text` | **game endpoint** | game | 否（同一能力，仅改名） | 750 |
| 63 | `wait_for_node` | `running_game_find_node_when_available` | **game endpoint** | game | 否（同一能力，仅改名） | 761 |
| 64 | `find_nearby_nodes` | `running_game_find_nearby_nodes` | **game endpoint** | game | 否（同一能力，仅改名） | 772 |
| 65 | `navigate_to` | `running_game_move_player_to_target_via_navigation` | **game endpoint** | game | **是**（新契约里不存在；`unregister_until_implemented`） | 783 |
| 66 | `move_to` | `running_game_move_player_to_target` | **game endpoint** | game | 否（同一能力，仅改名） | 794 |
| 67 | `watch_signals` | `running_game_capture_signal_emissions` | **game endpoint** | game | 否（同一能力，仅改名） | 805 |
| 68 | `get_performance_monitors` | `editor_get_performance_monitors` | editor endpoint | editor | 否（同一能力，仅改名） | 816 |
| 69 | `get_editor_performance` | `editor_get_performance_monitors` | editor endpoint | editor | **是**（并入保留方 `get_performance_monitors`）：同属编辑器进程 Performance 单例，返回值经逐字段核验是 get_performance_monitors 的真子集（profiling.rs:63 vs :32），故按 GDR-17 维持合并；代价：返回值由平铺改嵌套，消费者须按 get_performance_monitors 的嵌套形状取值 | 827 |
| 70 | `list_scripts` | `project_list_scripts` | editor endpoint | 通用 | 否（同一能力，仅改名） | 839 |
| 71 | `read_script` | `project_read_script` | editor endpoint | 通用 | 否（同一能力，仅改名） | 850 |
| 72 | `create_script` | `project_create_script` | editor endpoint | 通用 | 否（同一能力，仅改名） | 861 |
| 73 | `edit_script` | `project_edit_script` | editor endpoint | 通用 | 否（同一能力，仅改名） | 872 |
| 74 | `attach_script` | `editor_set_node_script` | editor endpoint | editor | 否（同一能力，仅改名） | 883 |
| 75 | `get_open_scripts` | `editor_get_open_scripts` | editor endpoint | editor | 否（同一能力，仅改名） | 894 |
| 76 | `validate_script` | `project_validate_script` | editor endpoint | 通用 | 否（同一能力，仅改名） | 905 |
| 77 | `simulate_key` | `editor_simulate_key` | editor endpoint | editor | 否（同一能力，仅改名） | 916 |
| 78 | `simulate_mouse_click` | `editor_simulate_mouse_click` | editor endpoint | editor | 否（同一能力，仅改名） | 927 |
| 79 | `simulate_mouse_move` | `editor_simulate_mouse_move` | editor endpoint | editor | 否（同一能力，仅改名） | 938 |
| 80 | `simulate_action` | `editor_simulate_input_action` | editor endpoint | editor | 否（同一能力，仅改名） | 949 |
| 81 | `get_input_actions` | `editor_get_input_actions` | editor endpoint | editor | 否（同一能力，仅改名） | 960 |
| 82 | `set_input_action` | `editor_add_input_action` | editor endpoint | editor | 否（同一能力，仅改名） | 971 |
| 83 | `simulate_sequence` | `editor_simulate_input_sequence` | editor endpoint | editor | 否（同一能力，仅改名） | 982 |
| 84 | `find_nodes_by_type` | `editor_find_nodes_by_type` | editor endpoint | editor | 否（同一能力，仅改名） | 993 |
| 85 | `batch_set_property` | `editor_set_node_property_batch` | editor endpoint | editor | 否（同一能力，仅改名） | 1004 |
| 86 | `find_signal_connections` | `editor_list_signal_connections` | editor endpoint | editor | 否（同一能力，仅改名） | 1015 |
| 87 | `batch_add_nodes` | `editor_add_nodes_batch` | editor endpoint | editor | 否（同一能力，仅改名） | 1026 |
| 88 | `find_node_references` | `project_find_files_referencing_symbol` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1037 |
| 89 | `get_scene_dependencies` | `project_get_scene_dependencies` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1048 |
| 90 | `cross_scene_set_property` | `project_set_node_property_across_scenes` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1059 |
| 91 | `list_animations` | `editor_list_animations` | editor endpoint | editor | 否（同一能力，仅改名） | 1070 |
| 92 | `create_animation` | `editor_create_animation` | editor endpoint | editor | 否（同一能力，仅改名） | 1081 |
| 93 | `add_animation_track` | `editor_add_animation_track` | editor endpoint | editor | 否（同一能力，仅改名） | 1092 |
| 94 | `set_animation_keyframe` | `editor_set_animation_keyframe` | editor endpoint | editor | 否（同一能力，仅改名） | 1103 |
| 95 | `get_animation_info` | `editor_get_animation_info` | editor endpoint | editor | 否（同一能力，仅改名） | 1114 |
| 96 | `remove_animation` | `editor_remove_animation` | editor endpoint | editor | 否（同一能力，仅改名） | 1125 |
| 97 | `tilemap_get_info` | `editor_get_tilemap_info` | editor endpoint | editor | 否（同一能力，仅改名） | 1136 |
| 98 | `tilemap_get_used_cells` | `editor_get_tilemap_used_cells` | editor endpoint | editor | 否（同一能力，仅改名） | 1147 |
| 99 | `tilemap_clear` | `editor_remove_all_tilemap_cells` | editor endpoint | editor | 否（同一能力，仅改名） | 1158 |
| 100 | `tilemap_set_cell` | `editor_set_tilemap_cell` | editor endpoint | editor | 否（能力不变；该工具实现先修，输入/输出形式见 reason）：写编辑场景瓦片，故 editor_ + set_；但实现只调 layer.set_cell(coords) 单参，source_id/atlas_coords 未生效且会擦除格子却回报 set:true（tilemap.rs:124），先修实现 | 1169 |
| 101 | `tilemap_fill_rect` | `editor_set_tilemap_cells_in_rect` | editor endpoint | editor | 否（能力不变；该工具实现先修，输入/输出形式见 reason）：写编辑场景矩形区域瓦片，故 editor_ + set_；但同样用单参 set_cell 且回报 filled:N（tilemap.rs:158），实际未写入任何瓦片，先修实现 | 1180 |
| 102 | `tilemap_get_cell` | `editor_get_tilemap_cell` | editor endpoint | editor | 否（同一能力，仅改名） | 1191 |
| 103 | `read_resource` | `project_read_resource` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1202 |
| 104 | `add_autoload` | `project_add_autoload` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1213 |
| 105 | `remove_autoload` | `project_remove_autoload` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1224 |
| 106 | `edit_resource` | `project_edit_resource` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1235 |
| 107 | `create_resource` | `project_create_resource` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1246 |
| 108 | `get_resource_preview` | `project_get_resource_preview` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1257 |
| 109 | `get_export_info` | `project_get_export_info` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1268 |
| 110 | `list_export_presets` | `project_list_export_presets` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1279 |
| 111 | `export_project` | `project_export_game` | editor endpoint | 通用 | **是**（新契约里不存在；`unregister_until_implemented`） | 1290 |
| 112 | `read_shader` | `project_read_shader` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1301 |
| 113 | `create_shader` | `project_create_shader` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1312 |
| 114 | `edit_shader` | `project_edit_shader` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1323 |
| 115 | `assign_shader_material` | `editor_set_shader_material` | editor endpoint | editor | 否（同一能力，仅改名） | 1334 |
| 116 | `set_shader_param` | `editor_set_shader_param` | editor endpoint | editor | 否（同一能力，仅改名） | 1345 |
| 117 | `get_shader_params` | `project_get_shader_params` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1356 |
| 118 | `add_raycast` | `editor_add_raycast` | editor endpoint | editor | 否（同一能力，仅改名） | 1367 |
| 119 | `setup_collision` | `editor_setup_collision_shape` | editor endpoint | editor | 否（同一能力，仅改名） | 1378 |
| 120 | `set_physics_layers` | `editor_set_physics_layers` | editor endpoint | editor | 否（同一能力，仅改名） | 1389 |
| 121 | `get_physics_layers` | `editor_get_physics_layers` | editor endpoint | editor | 否（同一能力，仅改名） | 1400 |
| 122 | `setup_physics_body` | `editor_setup_physics_body` | editor endpoint | editor | 否（同一能力，仅改名） | 1411 |
| 123 | `get_collision_info` | `editor_get_collision_info` | editor endpoint | editor | 否（同一能力，仅改名） | 1422 |
| 124 | `add_mesh_instance` | `editor_add_mesh_instance` | editor endpoint | editor | 否（同一能力，仅改名） | 1433 |
| 125 | `setup_camera_3d` | `editor_setup_camera_3d` | editor endpoint | editor | 否（同一能力，仅改名） | 1444 |
| 126 | `setup_lighting` | `editor_setup_lighting` | editor endpoint | editor | 否（同一能力，仅改名） | 1455 |
| 127 | `set_material_3d` | `editor_set_material_3d` | editor endpoint | editor | 否（同一能力，仅改名） | 1466 |
| 128 | `setup_environment` | `editor_setup_world_environment` | editor endpoint | editor | 否（同一能力，仅改名） | 1477 |
| 129 | `add_gridmap` | `editor_add_gridmap` | editor endpoint | editor | 否（同一能力，仅改名） | 1488 |
| 130 | `add_audio_player` | `editor_add_audio_player` | editor endpoint | editor | 否（同一能力，仅改名） | 1499 |
| 131 | `get_audio_info` | `editor_get_audio_info` | editor endpoint | editor | 否（同一能力，仅改名） | 1510 |
| 132 | `get_audio_bus_layout` | `editor_get_audio_bus_layout` | editor endpoint | editor | 否（同一能力，仅改名） | 1521 |
| 133 | `add_audio_bus` | `editor_add_audio_bus` | editor endpoint | editor | 否（同一能力，仅改名） | 1532 |
| 134 | `set_audio_bus` | `editor_set_audio_bus_property` | editor endpoint | editor | 否（同一能力，仅改名） | 1543 |
| 135 | `add_audio_bus_effect` | `editor_add_audio_bus_effect` | editor endpoint | editor | 否（同一能力，仅改名） | 1554 |
| 136 | `create_theme` | `project_create_theme` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1565 |
| 137 | `set_theme_color` | `project_set_theme_color` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1576 |
| 138 | `set_theme_constant` | `project_set_theme_constant` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1587 |
| 139 | `set_theme_font_size` | `project_set_theme_font_size` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1598 |
| 140 | `set_theme_stylebox` | `project_set_theme_stylebox` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1609 |
| 141 | `setup_control` | `editor_set_control_theme` | editor endpoint | editor | 否（同一能力，仅改名） | 1620 |
| 142 | `get_theme_info` | `project_get_theme_info` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1631 |
| 143 | `create_animation_tree` | `editor_create_animation_tree` | editor endpoint | editor | 否（同一能力，仅改名） | 1642 |
| 144 | `get_animation_tree_structure` | `editor_get_animation_tree_structure` | editor endpoint | editor | 否（同一能力，仅改名） | 1653 |
| 145 | `add_state_machine_state` | `editor_add_state_machine_state` | editor endpoint | editor | 否（同一能力，仅改名） | 1664 |
| 146 | `remove_state_machine_state` | `editor_remove_state_machine_state` | editor endpoint | editor | 否（同一能力，仅改名） | 1675 |
| 147 | `add_state_machine_transition` | `editor_add_state_machine_transition` | editor endpoint | editor | 否（同一能力，仅改名） | 1686 |
| 148 | `remove_state_machine_transition` | `editor_remove_state_machine_transition` | editor endpoint | editor | 否（同一能力，仅改名） | 1697 |
| 149 | `set_blend_tree_node` | `editor_set_blend_tree_node` | editor endpoint | editor | 否（同一能力，仅改名） | 1708 |
| 150 | `set_tree_parameter` | `editor_set_animation_tree_parameter` | editor endpoint | editor | 否（同一能力，仅改名） | 1719 |
| 151 | `setup_navigation_region` | `editor_setup_navigation_region` | editor endpoint | editor | 否（同一能力，仅改名） | 1730 |
| 152 | `bake_navigation_mesh` | `editor_bake_navigation_mesh` | editor endpoint | editor | 否（能力不变；该工具实现先修，输入/输出形式见 reason）：烘焙编辑场景导航网格，故 editor_ + bake_；但实现恒返回 baked:true，NavigationRegion3D 只 set 一个属性、2D 只赋 polygon（navigation.rs:193 TODO），未真正烘焙，先修实现 | 1741 |
| 153 | `setup_navigation_agent` | `editor_setup_navigation_agent` | editor endpoint | editor | 否（同一能力，仅改名） | 1752 |
| 154 | `set_navigation_layers` | `editor_set_navigation_layers` | editor endpoint | editor | 否（同一能力，仅改名） | 1763 |
| 155 | `get_navigation_info` | `editor_get_navigation_info` | editor endpoint | editor | 否（同一能力，仅改名） | 1774 |
| 156 | `create_particles` | `editor_create_particles` | editor endpoint | editor | 否（同一能力，仅改名） | 1785 |
| 157 | `set_particle_material` | `editor_set_particle_material` | editor endpoint | editor | 否（同一能力，仅改名） | 1796 |
| 158 | `set_particle_color_gradient` | `editor_set_particle_color_gradient` | editor endpoint | editor | 否（同一能力，仅改名） | 1807 |
| 159 | `apply_particle_preset` | `editor_set_particle_preset` | editor endpoint | editor | 否（同一能力，仅改名） | 1818 |
| 160 | `get_particle_info` | `editor_get_particle_info` | editor endpoint | editor | 否（同一能力，仅改名） | 1829 |
| 161 | `find_unused_resources` | `project_find_unused_resources` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1840 |
| 162 | `analyze_signal_flow` | `editor_analyze_signal_flow` | editor endpoint | editor | 否（同一能力，仅改名） | 1851 |
| 163 | `analyze_scene_complexity` | `project_analyze_scene_complexity` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1862 |
| 164 | `find_script_references` | `project_find_script_references` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1873 |
| 165 | `detect_circular_dependencies` | `project_detect_circular_dependencies` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1884 |
| 166 | `get_project_statistics` | `project_get_statistics` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1895 |
| 167 | `run_test_scenario` | `running_game_run_test_scenario` | **game endpoint** | game | 否（同一能力，仅改名） | 1906 |
| 168 | `assert_node_state` | `running_game_assert_node_state` | **game endpoint** | game | 否（同一能力，仅改名） | 1917 |
| 169 | `assert_screen_text` | `running_game_assert_screen_text` | **game endpoint** | game | 否（同一能力，仅改名） | 1928 |
| 170 | `run_stress_test` | `running_game_run_stress_test` | **game endpoint** | game | 否（同一能力，仅改名） | 1939 |
| 171 | `get_test_report` | `editor_get_test_report` | editor endpoint | editor | 否（能力不变；该工具实现先修，输入/输出形式见 reason）：实现在编辑器进程用 Expression 取报告，故 editor_；但恒返回固定文案、未收集任何测试结果（test.rs:561），先修实现 | 1950 |
| 172 | `list_android_devices` | `os_list_android_devices` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1961 |
| 173 | `get_android_preset_info` | `project_get_android_preset_info` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1972 |
| 174 | `deploy_to_android` | `os_deploy_to_android_device` | editor endpoint | 通用 | 否（同一能力，仅改名） | 1983 |

### 3.1 新契约里**没有**旧名对应的 2 条（登记项，不是能力缺口）

| 旧名 | map 给的 new_name | disposition | hof-rs 是否依赖该能力 | 处理 |
|---|---|---|---|---|
| `navigate_to` | `running_game_move_player_to_target_via_navigation` | `unregister_until_implemented` | **不依赖**（只出现在旧的 Tester 允许名单里） | 从策略名单与夹具中**删除**，没有用别的工具顶替 |
| `export_project` | `project_export_game` | `unregister_until_implemented` | **不依赖**（只出现在旧的 Tester 禁写名单里） | 同上 |

### 3.2 新契约里**新增**的、旧契约没有的 6 条（不是改名产物）

`project_build_csharp`、`project_read_text_file`、`project_validate_scripts`、`project_write_text_file`、`editor_set_node_script_batch`、`editor_set_node_property_updates`

### 3.3 合并（GDR-17）留下的 1 条

`get_editor_performance` 与 `get_performance_monitors` 在 map 里都映射到 `editor_get_performance_monitors`（前者 `disposition = merge_into`，`merge_target = get_performance_monitors`）。hof-rs 两个旧名都没用，因此无影响。

---

## 4. BLOCKER 清单

**无能力层面的 BLOCKER。** 逐条列账如下（不留空节）：

| 项 | 旧名 | 新契约是否有对应 | 影响哪条判据 | 结论 |
|---|---|---|---|---|
| 1 | `navigate_to` | **无**（`unregister_until_implemented`） | 无 | hof-rs **不依赖**该能力：它只出现在旧的 `TESTER_ALLOW_EXACT`（"QA 能调用哪些工具"的允许名单，不是被调用的能力）。按 DR-45「旧词汇归零」从名单与夹具中删除，**没有**用别的工具顶替。 |
| 2 | `export_project` | **无**（`unregister_until_implemented`） | 无 | 同上：只出现在旧的 `MUTATING_EXACT`（禁写名单）里；工具不存在时"禁止调用它"是空真，删除后语义不变。 |

Verifier 若认为"删掉一个禁止项"也算能力损失，请裁决：我的依据是 §13.5「旧词汇归零」与 §3.6「不得臆造能力」——二者都要求不存在对应工具时**删除并上报**，而不是替代。

其余 172 条旧名 1:1（或按 disposition 说明）对应到新契约，无缺口。

---

## 5. 我修改过的既有断言（逐条：原断言 / 新断言 / 为什么语义等价）

### DR-41

| # | 位置 | 原断言 | 新断言 | 等价性说明 |
|---|---|---|---|---|
| a | `src/adapter/godot.rs`（原 `initialize_enables_the_mcp_plugin_idempotently`） | `first.contains("[editor_plugins]")`；`first.matches(MCP_PLUGIN_PATH).count() == 1`；二次调用后文件字节不变 | 换成 `initialize_removes_a_legacy_bundled_addon_idempotently`：清理后 `addons/godot_mcp_rs` 不存在、cache 行被移除而**其余行逐字保留**、`[editor_plugins]` 里其它插件名逐字保留、二次调用字节不变 | DR-4 被 DR-41 **取代**（插件通道必须拆除，不是启用）。被保留的不变式是"**幂等 + 字节保守地改动 project.godot**"，并且比原断言更强（原断言只比一次完整文件相等，新断言分别比 cache 与 project 的逐字节结果）。 |
| b | `src/adapter/godot.rs`（原 `initialize_preserves_other_enabled_plugins`） | 启用 MCP 插件后其它插件名仍在 | 它的"其它插件名逐字保留"并入 (a)；另加 `initialize_never_touches_a_project_without_the_retired_channel`：无 `[editor_plugins]` 的项目**逐字节不变** | 语义等价且更严：原测试证明的是"不破坏别人的插件项"，新测试证明同一件事，并额外要求"没这回事时一个字节都不动"。 |
| c | `src/adapter/godot.rs`（`initializes_a_minimal_project`） | 只断言 `scenes/main.tscn` 存在 | 追加 `!addons/godot_mcp_rs/plugin.cfg exists` 与 `!ADDON_MISSING.txt exists` | 新增断言，非替换；原断言（输入动作、主场景）全部保留。 |
| d | `tests/cli_init.rs`（`init_rebuilds_a0_without_mcp_or_a_model_endpoint`） | `project.contains("[editor_plugins]")` 且含 `res://addons/godot_mcp_rs/plugin.cfg` | `!project.contains("[editor_plugins]")`、`!project.contains("res://addons/godot_mcp_rs")`、`!addons/godot_mcp_rs` 存在、`!ADDON_MISSING.txt` | DR-41 明确反转为"不得启用"；"重建出的 A0 是可用工程"这一被验证目标由同一测试里保留的 `project.godot` / `leftover.txt 被清空` 断言承载。 |
| e | `tests/cli_init.rs`（`offline_overrides()`） | 两条 `-c` 覆盖（model、tools） | 追加 `adapter.godot.editor_binary=` | 不是改断言，是改测试输入：DR-44 的 doctor 会执行 `<binary> --version`，离线测试必须显式声明"没有引擎二进制"。断言（exit 0 / exit 4 / 工作区已重建）全部未变。 |
| f | `src/cli_impl.rs` doctor 项 | `godot.mcp_addon`（ok = addon 目录存在） | `godot.bundled_addon`（ok = 不存在）+ 新增 `godot.extension_cache`（ok = cache 不含旧扩展行） | DR-4 的反转：doctor 现在要报的是"旧通道不得回来"。无测试引用旧项名。 |

### DR-42

| # | 位置 | 原断言 | 新断言 | 等价性说明 |
|---|---|---|---|---|
| g | `tests/tools_policy.rs` `TESTER_MUST_BE_DENIED` | 29 条旧名（含 3 条**并非真实工具名**的合成样本：`remove_node`/`set_property`/`update_node`） | 29 条**契约内真实名字**，覆盖全部 25 个写动词 | 被验证的命题没变（"Tester 不得调用任何写类工具"），被换成真实名字后**更强**：另加 `the_role_lists_only_name_contract_tools`（`tests/tools_policy.rs:99`）保证名单里的名字必须真的在 177 条契约里，杜绝名单腐坏。`export_project`（无对应）删除并记为登记项。 |
| h | `tests/tools_policy.rs` `TESTER_MUST_BE_ALLOWED` | 7 条合成读动词样本（`list_nodes`/`read_file`/`search_nodes`/`find_node`/`analyze_scene`/`detect_collisions`）+ 14 条真实旧名 | 全部换成契约内真实名字（如 `project_list_scripts`/`project_read_script`/`project_search_file_names`/`editor_find_nodes_by_type`/`project_analyze_scene_complexity`/`project_detect_circular_dependencies`） | 合成的读动词样本原本只用于验证"读类动词对 Tester 放行"这一条规则；换成真实名字验证同一条规则，并额外获得"名字必须存在"的守护。期望值（allowed）逐条不变。`navigate_to`（无对应）删除。 |
| i | `src/tools/policy.rs` 单测 | `tool_allowed(Tester, "get_editor_errors")` 等 | 同名新名（`editor_get_errors` / `editor_simulate_input_sequence` / `editor_add_node` / `running_game_execute_gdscript`） | 逐条一对一改名，期望值不变。 |
| j | `tests/tool_discovery.rs` `tools_markdown_never_leaks_a_tool_the_role_may_not_call` | `!tester.contains("project_edit_script") && !tester.contains("editor_add_node")`（**整篇文本**子串） | `!tester.contains("### `project_edit_script`")`（**条目标题**）；Planner 同理 | 被验证的命题是"被拒的工具不会出现在该角色的**索引条目**里"。新契约的 `description` **确实会交叉引用别的工具名**（实测旧写法产生了假阳性，panic 在 `tests/tool_discovery.rs:64`），所以断言改为条目标题；"是否泄漏了一个可调用条目"这一真命题没有被放宽（列表条目由 `### `name`` 唯一确定）。 |
| k | `tests/evidence_battery.rs` / `tests/mcp_desync.rs` / `tests/mcp_reliability.rs` / `tests/launchable_gate.rs` / `tests/common/mod.rs` / `tests/runtime_semantics.rs` / `tests/developer_contract.rs` / `tests/godot_smoke.rs` / `src/adapter/*` / `src/tools/*` / `src/runtime/hygiene.rs` / `src/prompts/**` / `config/hoh.yaml` | 旧名出现在：假 MCP 的 `match tool` 分支、`call_count("...")`、`with_reply("...")`、`fail_always("...")`、prompt 散文、BatteryStep 表 | 同位置的一对一新名 | 逐条查表改名；每条映射见 §3。假通道的 `match` 分支名与调用方**同时**改名，因此"某工具被调用了几次""返回哪种形状"这些被断言的性质不变。 |
| l | `tests/fixtures/mcp/game_scene_tree_real.json`、`input_replay_smoke_t5.json` | `"tool": "<旧名>"` | 同位置 `"tool": "<新名>"` | 该字段记录"这份真实捕获是哪个工具产生的"；工具改名了，记录也必须改名，否则夹具与契约不自洽。载荷内容（`payload`/`calls`/采样）一字未动。 |
| m | `tests/tool_discovery.rs:314` | 轨迹字符串 `grep -n play_scene src/runtime/run_loop.rs` | `grep -n editor_play_scene ...` | 该字符串模拟一次真实工具调用；断言的是"代码里被调用的每个工具名都在夹具里"（DR-45 ③），因此必须同步。 |
| n | `src/runtime/policy.rs` `tool_matrix` 重写 | 前缀表：`TESTER_ALLOW_PREFIXES`（`get_`/`list_`/…）、`MUTATING_PREFIXES`（`add_`/`set_`/`update_`/…） | 四通道 + 动词表：`QA_READ_VERBS`、`MUTATING_VERBS`、`QA_ALLOW_EXACT`（`src/runtime/policy.rs:185-303`） | 旧名没有"通道"这一维，前缀规则无法机械翻译，因此按 DR-42 的规则重写。**逐条等价性已用脚本对 172 条可映射条目做全量核对**：与旧规则判定不同的只有 5 条，且全部是"旧规则因为名字不以读动词开头而误拒"的**只读**工具（见 §7.1）。`tool_allowed(Developer/Planner)` 与 `denial_reason` 的两种文案逐字未变。 |

### DR-43 / DR-44

| # | 位置 | 原断言 | 新断言 | 等价性说明 |
|---|---|---|---|---|
| o | `tests/fixtures/mcp/play_scene_ok.json`（假 MCP 回复） | 内层 JSON 只有 `{"mode":"main","playing":true}` | 追加 `endpoint`/`mcp_port`/`mcp_port_source`/`pid` | DR-43 要求 `editor_play_scene` 的回复**必须**带回游戏端点；否则该步按设计判失败。这是测试替身的形状对齐，不是放宽断言：同一测试对 `play_scene_ready` 的断言一条未减。**注意**：该文件是测试替身，不是活体捕获（活体核对留给批次二，见 §7）。 |
| p | `tests/launchable_gate.rs` `GateChannel`（内联回复） | `"editor_play_scene" => json!({"playing": true})` | 同上再加端口字段 | 同上。该替身同时扮演两个通道，登记一个端口即可，`running_game_*` 仍由它自己回答（它不实现端点路由，走 `ToolChannel::register_game_endpoint` 的默认实现）。 |
| q | `tests/mcp_desync.rs` `battery_server` | 回复表里 `editor_play_scene` 用静态夹具 | 服务器启动后把回复换成"带上**自己端口**"的版本 | 同上。这个双端点的假服务器同时扮演编辑器与游戏端点，使 DR-43 之后仍能以真实 `McpChannel` 驱动整条电池；原测试断言的 JSON-RPC 关联/去同步行为一条未减。 |
| r | `src/adapter/mod.rs:23` `GATE_STEP_IDS` | 2 个 id | 3 个 id（新增 `engine_identity`） | 行为向后兼容：`evaluate_launchable` 只对**电池已声明**的闸门步判失败（`src/adapter/mod.rs:38-46`），未声明的步跳过。因此"没有引擎二进制的适配器"与以前完全一致；只有声明了引擎二进制、且探针给出 `matches_binary != true` 的适配器才会被拦（DR-44 ⑤）。 |
| s | `tests/secret_hygiene.rs` `meta_json_is_redacted_at_the_sink` | `RunMeta { … }`（无 `engine`） | 构造器加 `engine: EngineIdentity::unavailable("not probed")`，并**新增**两条断言：`engine` 的 6 个键必须存在、`engine` 串不得含假密钥 | `RunMeta` 加字段是 DR-44 ③ 的要求；原断言（`config.api_key` 为 null、整篇不含密钥）一字未改，还扩大了覆盖范围。 |

---

## 6. 禁区自查（真实命令输出）

### 6.1 未启动 Godot / 未占端口 / 未联网 / 未调模型端点

机制层面的证据（不是形容词）：

1. **所有探针都经 `mini_swe_agent::Environment` 抽象**。批次一里唯一构造真实 `LocalEnvironment` 的地方有两处，且都**只在适配器声明了引擎二进制时才走到**：
   - `src/runtime/engine_identity.rs:23`（`probe`）—— 第一行就是 `let Some(binary) = adapter.engine_binary() else { return unavailable(...) }`；
   - `src/cli_impl.rs:164`（doctor 的 5b 段）—— 外层是 `if let Some(binary) = adapter.engine_binary()`。
2. **测试里没有任何一个适配器声明过引擎二进制**，因此 `cargo test` 期间上述两处都不会构造 `LocalEnvironment`，也就不会执行任何 `netstat` / `powershell` / `--version`：

```
$ Select-String -Path tests\*.rs -Pattern "editor_binary:" | ForEach-Object { "$($_.Filename):$($_.LineNumber): $($_.Line.Trim())" }
dual_endpoint.rs:373:             editor_binary: std::path::PathBuf::new(),
evidence_battery.rs:497:         editor_binary: std::path::PathBuf::new(),
launchable_gate.rs:149:         editor_binary: std::path::PathBuf::new(),
mcp_desync.rs:605:             editor_binary: std::path::PathBuf::new(),
result_semantics.rs:160:         editor_binary: std::path::PathBuf::new(),
start_state.rs:26:             editor_binary: std::path::PathBuf::new(),
wrap_up_budget.rs:315:         editor_binary: std::path::PathBuf::new(),
```

3. **`tests/cli_init.rs` 的 `hoh` 子进程测试显式关掉引擎探测**（否则 `hoh run` 的 doctor 预检会执行 `<binary> --version`）：

```
$ Select-String -Path tests\cli_init.rs -Pattern "editor_binary|127.0.0.1:1" | ForEach-Object { $_.Line.Trim() }
"model.base_url=http://127.0.0.1:1/v1".to_string(),
"tools.endpoint=http://127.0.0.1:1/mcp".to_string(),
// DR-44: these tests must not execute an engine binary either.
"adapter.godot.editor_binary=".to_string(),
```

4. **引擎探针的行为由 FakeEnv 断言**（命令**字符串**被记录、但从未真正执行）：

```
$ cargo test --offline --test engine_identity a_listener_that_is_the_configured_binary_matches
test a_listener_that_is_the_configured_binary_matches ... ok        ← 断言 netstat / powershell 命令被"发出"到假 Environment
$ cargo test --offline --test engine_identity a_missing_binary_fails_the_items_without_executing_anything
test a_missing_binary_fails_the_items_without_executing_anything ... ok   ← 断言 env.commands() 为空
```

5. **双端点测试用的是 loopback TCP 假服务器**（`tests/dual_endpoint.rs:76`，`TcpListener::bind("127.0.0.1:0")` 由操作系统分配端口），**没有**占用或探测 9877：

```
$ Select-String -Path tests\dual_endpoint.rs,tests\mcp_desync.rs -Pattern "9877" | Measure-Object | Select-Object -ExpandProperty Count
0        （9877 只作为**字符串**出现在 engine_identity 的假 netstat 输出与 URL 断言里，从未 bind/connect）
```

6. 模型端点：本批测试从未拨号；`tests/doctor_probe.rs`、`tests/cli_init.rs`、`tests/cli_status_rollback.rs` 一律把 `model.base_url` / `tools.endpoint` 指向 `127.0.0.1:1`（不可达的本地端口），`tests/mini_wire_model.rs` 用假 HTTP 服务。全批 `cargo test` exit 0 即证明这些路径没有被网络阻断（若真拨号会超时/失败）。

### 6.2 未改 `godot-mcp/**`

```
$ git -C godot-mcp status --porcelain
(空输出)
```

### 6.3 `PRD-mario.md` 一字未改

```
$ (Get-FileHash .spec\hof-rs\PRD-mario.md -Algorithm SHA256).Hash.ToLower()
4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a
```

与要求值逐字相同。

### 6.4 未引入新依赖

```
$ git diff --stat b6d9282~1 HEAD -- Cargo.toml Cargo.lock
(空输出)
```

### 6.5 未提交 `runs/**`、`.workspace/**`、`config/*.secret*`；未 `push`

```
$ git status --short
(空输出)                              ← 工作树干净
$ git log --name-only --pretty=format: b6d9282~1..HEAD | Where-Object { $_ -match "runs/|\.workspace/|secret" } | Select-Object -Unique
tests/secret_hygiene.rs               ← 唯一命中是**文件名**里的 "secret"（这是仓库既有的 DR-16 测试文件，不是密钥文件）
$ git rev-parse origin/master
4b9bd44054ccfefdb4b96a342a133a4896769b76   ← 仍是本批开始前的远端位（TASK-150 那一批）
$ git rev-list --count origin/master..HEAD
8                                      ← 2 个更早的未推送提交 + 本批 5 个 DR 提交 + 本报告提交
$ git rev-parse --short origin/master
4b9bd44                                ← 远端仍停在本批开始前
$ git log --oneline origin/master..HEAD
b2ed193 tests: guard the repository against the retired tool vocabulary (DR-45)
60131e5 adapter: record the engine identity and gate on it before freezing (DR-44)
1d52b24 tools: route running_game_* to the game endpoint the engine announces (DR-43)
db2eed7 tools: migrate to the 177-tool four-channel contract and rewrite the role scopes (DR-42)
b6d9282 adapter: drop the bundled GDExtension addon and its stale extension cache (DR-41)
9000518 chore(recovery): record the TASK-150 history-rewrite batch (task book, report, scripts)
e8461bf docs(spec): hof-rs engine switch to our MCP-native build - requirements v0.3, design v0.8 (DR-41..DR-47), D216
```

远端仍停在 4b9bd44、而本批 6 个提交只出现在本地 ⇒ **没有执行过 `git push`**。

### 6.6 `addon_source` 0 命中（DR-41 §13.1 第 5 条）

```
$ (Select-String -Path (Get-ChildItem -Recurse src,tests,config -File | ForEach-Object FullName) -Pattern "addon_source" | Measure-Object).Count
0
```

### 6.7 未删除/放宽既有测试换绿

- 本批**没有**新增任何 `#[ignore]`、没有 `--skip`；`tests/godot_smoke.rs` 的 7 个 `#[ignore]` 是既有状态（DR-9）。
- 所有被改动的断言与理由见 §5；没有任何一条是"为了让测试通过而放宽"。
- `cargo build --offline` 的 warning/error 命中数为 0（`Select-String -Pattern "warning|error" | Measure-Object` → `Count = 0`）。

---

## 7. 遗留风险与不确定项

### 7.1 QA 作用域重写带来的 5 处（有意的）放宽

旧前缀规则对 172 条可映射条目与新规则的判定**全量比对**后，只有以下 5 条不同，且**全部是只读动词**的工具（旧规则只因为它们不以读动词开头而拒绝）：

| 旧名 | 新名 | 动词 | 变化 |
|---|---|---|---|
| `batch_get_properties` | `running_game_get_node_properties_batch` | get | 旧拒 → 新放行 |
| `watch_signals` | `running_game_capture_signal_emissions` | capture | 旧拒 → 新放行 |
| `tilemap_get_info` | `editor_get_tilemap_info` | get | 旧拒 → 新放行 |
| `tilemap_get_used_cells` | `editor_get_tilemap_used_cells` | get | 旧拒 → 新放行 |
| `tilemap_get_cell` | `editor_get_tilemap_cell` | get | 旧拒 → 新放行 |

风险等级：低（都是只读取证工具，不写产物；DR-42 要求"按四通道 + 只读动词集重写"，这正是规则要求的结果）。**没有任何一条既有测试**断言过它们被拒绝，所以没有测试被削弱。反过来，`cross_scene_set_property`（旧名单里既在允许集又在禁写集）在新规则下稳定落为**拒绝**，比旧规则更清晰。

### 7.2 Planner 的解释（可能与 Verifier 的读法不同）

DR-42 写"Planner 只读 ⇒ 仅允许只读类动词通道"。我把 Planner 的允许集保持为**空**（`src/runtime/policy.rs:198` `PLANNER_DENY_PREFIXES = ["*"]`），理由是：
1. 它**最强地**满足"不得把任何写动词放进只读角色"；
2. §5.4 + DR-7 明确规定 Planner 不持有任何 MCP 工具，并且有既有测试断言 `!tool_allowed(Planner, <read tool>)`；
3. 反过来"让 Planner 能只读调用"是对既有测试的**削弱**（`tests/tools_policy.rs`、`tests/runtime_semantics.rs`、`tests/tool_discovery.rs` 都断言 Planner 拿不到任何工具），而 §3.7 禁止放宽既有测试来换绿。

若裁决认为 Planner 必须能调用只读工具，请显式指示：那需要同时改写上述 3 个测试文件里 6 处断言，属于**设计变更**而不是本批的迁移。

### 7.3 夹具结构对齐方式

- 夹具由 `tools_list.renamed.json` 重新序列化为**紧凑、键排序、UTF-8 无 BOM、LF、无尾换行**，与旧夹具的形态一致（旧夹具本就是"紧凑 + 键排序"的 `tools/list` 响应），因此 `McpClient::list_tool_schemas` 与 `src/tools/index.rs` 的解析路径未变。
- 与活体的**逐字**一致（`GET /mcp` 返回的名字集合与条数）**没有**在批次一证明，属 DR-47 的核对项。`tools_list.renamed.json` 亦非活体捕获，而是引擎侧文档产物。

### 7.4 DR-45 第 2 条扫描的误报边界

- 该检查**包含注释与 Markdown 散文**。我在过程中因此改写了 5 处提到旧名的注释（`src/runtime/policy.rs` 的 `DOC`：`play_scene` / `set_game_node_property` / `execute_game_script` / `start_recording` / `move_to`，以及一个测试断言 `verb_of("play_scene") == None` 换成中性名）。这是**有意的严格**：任何遗留旧名都可能误导读者，但代价是"引用历史的注释"也必须换个说法。
- 两个被排除的文件（守卫自身、契约夹具）在 §2.5 已列明；此外，旧名若出现在不在 `SCANNED_SUFFIXES` 里的文件类型（如 `.sh`、无后缀）会漏检。

### 7.5 `mcp_port_source` 的第三个取值

设计书写 `mcp_port_source ∈ {argument, auto_free_port}`。若引擎在回复里**没有声明**该字段，我记 `undeclared`（`src/tools/endpoint.rs:64`），而不是替它选一个。这会向 `meta.json.engine.mcp.game_endpoint.source` 引入第三个取值。理由：写入 `argument`/`auto_free_port` 就是在**编造事实**。若裁决要求严格二元，需要对引擎回复做一次活体确认（批次二）再收紧。

### 7.6 `engine_identity` 在"无法判定"时也关闸（比设计书更严）

DR-44 ⑤ 的原文是"`matches_binary == false` ⇒ 闸门失败"。我的实现是 `ok = (matches_binary == Some(true))`（`src/adapter/engine.rs:424`），即"探针读不到监听者"（`None`）也判失败，理由取自 §0 裁决原则第 2 条"沉默即失败"。observation 会区分 `mismatch` 与 `could not be compared`。
风险：在 `netstat`/`powershell` 输出形态与预期不符的机器上，整轮会被闸门拦住。我认为这正是要的结果（否则"用的是哪个引擎"就变成不可证），但**这是一个可能被裁决推翻的取舍**，故显式列出。

### 7.7 批次一不做、批次二必须做的核对

- 活体 `tools/list` 条数与名字（== 177、逐字一致）；
- `meta.json.engine.listener.matches_binary == true`（真实 9877 监听者是 mono 构建）；
- `version_string` 以 `4.8.dev.mono` 开头；
- `editor_play_scene` 真实回复里 `endpoint`/`mcp_port`/`mcp_port_source`/`pid` 的确切形状（决定 §7.5 是否要收紧）；
- 游戏端点上的 23 个 game-only 工具是否真的只有游戏端点可达（本批只证明了 hof-rs **不会**把 `running_game_*` 打到编辑器端点）。

### 7.8 其它未验证项

- `netstat -ano -p tcp` 与 `powershell -NoProfile -Command "(Get-Process -Id N).Path"` 的真实输出**从未在本机执行过**（离线批次），解析器只用人工构造的表格覆盖（含本地化状态列与 IPv6 形态）。
- `editor_status`（`GET /mcp` 原样响应体）恒为空对象 + reason，批次二应填。
- `version_string` 用 `<binary> --version` 的**首行非空输出**；不同构建的输出形态未活体确认。

---

## 8. 诚实披露（返工、猜错、绕过尝试）

1. **迁移方式**：旧名替换由一个**读 rename map 表**的脚本完成（整词边界、长名优先，逐文件列出命中的旧名清单），随后我人工复核了 24 个文件的全部改动行；`src/runtime/policy.rs` 与 `tests/tools_policy.rs` **完全手工重写**，未走脚本。这不属于"正则批量替换"，但也**不是**逐行手打 270 处——请按此口径审阅。脚本与中间清单在 `%TEMP%`，未入库（未污染仓库）。
2. **`navigate_to` / `export_project`** 的"无对应"是我**逐一查表 + 与 177 条契约做集合运算**得出的，不是推测；两者在 hof-rs 里只出现在策略名单中（旧夹具里当然也有）。
3. **猜错与返工（全部在提交前被自己的测试抓住）**：
   - `packed_string_array_without` 第一次写成 `enabled=PackedStringArrayPackedStringArray(...)`，被 DR-41 的字节比较测试抓出（`left: "…PackedStringArrayPackedStringArray(…)"`），改为复用原函数名 + `(` 拼接。
   - `tool_allowed` 第一次把 `is_mutating` 判在 QA 例外**之前**，导致 `running_game_create_input_recording` 被拒；被新写的 `qa_keeps_only_its_read_only_and_evidence_driving_scope` 抓出，改为"例外优先"。
   - `qa_is_denied_every_mutating_tool_of_the_contract` 第一版没有排除两条已登记例外，自己把自己判红；改为读生产常量 `QA_ALLOW_EXACT` 并断言"可达的写动词名字数 == 例外数"。
   - DR-45 第 3 条第一版把"任何引号内的四通道形状名字"都当工具名，被 DR-44 新增的 JSON 字段名（`editor_status` / `editor_endpoint` / `editor_status_reason`）打成假阳性；改为"第二段必须是契约里真实出现的动词"，并把手工排除表从 5 条缩到 1 条。
   - `the_version_string_is_never_a_code_constant` 自匹配：它扫描的文件里就写着那个字符串，改成编译期拼接的 needle。
   - DR-44 的引擎单测最初用**真实的 194 MB 引擎二进制**做 sha256 探针（5.5 s、且依赖环境），改为临时小文件（0.02 s，完全自洽）。
   - `meta_json_carries_the_engine_block_and_no_secret` 第一版把假密钥放进 `config.engine_dir`，而 sink 只清洗 `api_key`，于是它因为**错误的理由**失败；已删除该字段。
   - DR-45 第 2 条还迫使我把几处"引用历史旧名"的注释改写（见 §7.4）——这是我一开始没想到的副作用。
4. **两处我改了既有测试的地方，值得复核者特别看**：`tests/tool_discovery.rs` 的"不泄漏"断言从整篇子串改成条目标题（§5 j），以及 `tests/cli_init.rs` 的 DR-4 断言反转（§5 d）。理由都已写在 §5；若认为其中任何一条属于"放宽"，请按 fail 处理并指明。
5. **没有做**（也**没有**尝试绕过）：没有启动引擎、没有 bind/connect 9877 或任何端口、没有访问网络、没有调用任何模型端点、没有改 `godot-mcp/**`、没有改 `PRD-mario.md`、没有加依赖、没有保留别名层、没有 `push`。
6. **一次 git 历史失误（已修正，披露）**：收尾时我先对 HEAD（当时是 DR-45 提交）执行了 `git add tests/engine_identity.rs && git commit --amend -m "<DR-44 的信息>"`，把 DR-45 的提交**改坏**了（内容被并进一条错消息的提交）。发现后立即用 `git reset --mixed 57eeff0`（保留工作树）回到真正的 DR-44 提交，先 `--amend --no-edit` 把引擎测试的返工并回 DR-44，再重新提交 DR-45。当前 5 个 DR 提交的内容与消息一一对应（`git show --stat` 已核对：DR-44 = 12 个文件、DR-45 = 仅 `tests/tool_vocabulary.rs`）。
7. **推断 vs 实测**（避免把推断写成实测）：
   - 实测：`cargo test --offline` 全绿与 exit code、夹具 sha256 与条数、PRD sha256、`addon_source` 0 命中、`git -C godot-mcp status` 为空、Cargo.toml/lock diff 为空、`cargo build` 0 warning。
   - 推断（**未**活体验证）：§7.7 列出的全部批次二核对项；以及"真实 `editor_play_scene` 回复里一定有端口字段"这一前提（离线只用测试替身验证了**解析器**与**登记失败即步骤失败**两条逻辑）。
