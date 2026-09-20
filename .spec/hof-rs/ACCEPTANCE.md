# ACCEPTANCE — hof-rs 阶段五验收记录

- 状态：**离线范围通过（pass）；真实冒烟（E1–E6 / T=1）未执行 → 阶段一整体尚未完成**
- 依据：`REQUIREMENTS.md` v0.2（R1–R13 / C1–C10 / E1–E6 / A1–A8）、`DESIGN-DETAIL.md` v0.2（含 §12 DR-1..DR-13）、`DECISIONS.md` D1–D14
- 验收主体：**两批完全独立的验收子代理**（工作流 `hof-rs-acceptance`、`hof-rs-acceptance-2`），均未参与实现、未继承实现者结论

---

## 1. 结论

| 范围 | 结论 | 依据 |
|---|---|---|
| R1–R13（Runtime 语义）、C9/C10、DR-1..DR-12 | **pass** | 第二轮独立验收，无 blocker/major/minor 缺陷，反例由验收方自建 |
| E1–E6（T=1 真实全链路冒烟） | **未执行（not_verifiable）** | 9877 未监听；仓库仅有一个在 Developer 阶段中断的遗留 run |
| **阶段一整体** | **未完成** | `REQUIREMENTS.md` §1「阶段一附加要求（用户确认）」明确要求至少一次 T=1 真实 smoke run |

> 口径声明：本文件**不**把「离线测试全绿」当作阶段一通过。用户明确要求阶段一含一次真实 smoke run，该项未完成即阶段一未完成。

## 2. 验收轮次与关键证据

### 2.1 第一轮（verdict = fail）

| 缺陷 | 严重度 | 内容 | 状态 |
|---|---|---|---|
| A1 | blocker | 证据 `path` 用 `..` 逃逸出候选视图根未被强制（`../outside_secret.txt` → `check_paths=[]`、`bind=Ok`） | 已修（DR-10） |
| A2 | major | `tests/godot_smoke.rs` E2–E6 在前置缺失时静默 `return` → `5 passed` 且**零断言** | 已修（DR-9） |
| A3 | minor | Planner 拒绝文案对只读工具误报「may not mutate」 | 已修（DR-7） |
| A4 | minor | 缺 §6.1 要求的 doctor 人工确认项 | 已修（DR-6） |
| A5 | minor | `status`/`rollback` 错误出口落 exit 5；unknown usage 打印成 `0` | 已修（DR-8） |
| A6 | nit | `tools_policy.rs:250` 恒真断言 | 已修（精确断言） |

### 2.2 修复轮（`hof-rs-fix-round`，4 次提交）

- `971882b` DR-1/DR-2/DR-3/DR-7/DR-10（A1）
- `74b2d67` DR-4/DR-5/DR-6/DR-8/DR-9/DR-11（A6）
- `1033aaf` submit 内层闸门拒绝 `..` 逃逸
- `a351817` 确定性阶段日志随记录复制进冻结候选视图

### 2.3 第二轮（verdict = pass）

验收方自跑与自建证据（摘要）：

| 命令 | 观察 |
|---|---|
| `cargo test --all-targets` | **100 passed / 0 failed / 7 ignored**（lib 52 + 9 个集成测试二进制） |
| `cargo clean -p hof-rs; cargo clippy --all-targets -- -D warnings` | exit 0，0 warning（先 clean 强制重建，排除缓存假绿） |
| `cargo fmt --check` | exit 0 |
| `cargo test --test godot_smoke -- --ignored` | **0 passed / 7 failed**（exit 101）→ DR-9 生效，绝非伪绿 |
| `HOH_SMOKE=1 ... --ignored e2_project_boots` | panic 并打印缺失的 `runs/godot-smoke/iter-1/evidence.json` 绝对路径 |
| 自建 scratch 反例（已删除） | **18 种逃逸形态全部被拒为 `DanglingEvidence`**；阳性对照被接受 |
| `git status --short` / `git diff --stat <v0.2冻结点> -- .spec` / 两个外部仓库 `status` | 全部为空 |
| `runs/godot-smoke` 检查 | 遗留不完整 run：planner 轨迹 `LimitsExceeded`（123 条消息）、developer 无 exit 条目、无 `evidence.json`/`result.json`/`candidate` |

**A1 独立复验的逃逸矩阵**（验收方自建，设计文档未列）：
`../outside_secret.txt`、`..\outside_secret.txt`、`scripts\..\..\outside_secret.txt`、`a/../outside_secret.txt`、
`dir_inside/..`、`..`、`C:outside_secret.txt`、`C:..\outside_secret.txt`、`C:/Windows/not-in-the-view.png`、
`\\server\share\x.png`、`//server/share/x.png`、`\\.\PhysicalDrive0`、绝对路径但文件确在视图内、
视图内目录、空串、**junction 逃逸（root=cand → 兄弟 cand2，前缀相似）**、**symlink 逃逸**。
全部 `DanglingEvidence` 且 `bind = Err`；`cand` vs `cand2` 被拒证明用的是按组件比较的 `Path::starts_with`
而非朴素字符串前缀。

## 3. 逐条验收标准证据（R1–R13 / C9 / C10）

| 标准 | 结果 | 证据（第二轮验收方独立复现） |
|---|---|---|
| R1 三次独立调用 | pass | `three_independent_invocations`：恰 3 次、顺序 Planner→Developer→Tester、三者 cwd 互不相同 |
| R2 只读角色 | pass | `planner_cannot_write_artifact`：绝对路径写 → `ReadOnlyRoleWroteArtifact`，`evidence_diff.added` 恰为该文件 |
| R3 单写者 | pass | `developer_is_only_writer`：`final_version_id == hash_tree(workspace)`；`index.json` 恰 2 条版本 |
| R4 冻结候选 | pass | 4 条反例（污染副本 / 直写真实 workspace / 冻结后漂移 / candidate_id 不符）全部按预期类型失败 |
| R5 双通道 | pass | `no_third_state_channel`：第 2 轮不含 `D_1`；prompt 含禁止重建 `D_{t-1}` 声明 |
| R6 schema 双闸门 | pass | `plan_retry_then_success`（attempts=2）、`evidence_retry_exhausted`（exit 3）、`missing_artifact_counts_as_attempt` |
| R7 证据划分 | pass | `verified_gap_partition`：重复 claim_id / gap 缺指引 / verified 空记录 均被拒 |
| R8 消融纯度 | pass | 三开关逐字节比较，各自只改动一个输入 |
| R9 每轮记录 | pass | `records_all_artifacts`：plan/evidence/qa_report/usage/result/traj/logs 齐备 |
| R10 版本与回滚 | pass | 内容寻址、排除项不影响身份、回滚精确复原、篡改快照报错 |
| R11 公开性边界 | pass | 私有标记不进 prompt 与注入项；`private_excludes` 只作用于视图（不扩大哈希排除集） |
| R12 用量统计 | pass | 夹具精确数值；无 usage → `usage_known=false` 且字段为 `None`；CLI 显示 `unknown` 而非 0 |
| R13 工具边界 | pass | 29 写类工具对 Tester 全拒、27 只读类允许、Planner 全 MCP 拒绝、未知工具 default-deny |
| C9 上线 model id | pass | 假 HTTP 服务实测收到的 `model == "qwen/qwen3.8-27b"`；剥前缀配置 → `ModelIdentityViolation`(exit 2) |
| C10 显式 provider | pass | `assert_model_identity` 双校验；`provider=aliyun` 被拒 |

**断言调整复核**：4 项既有断言调整全部判为可接受，其中 2 项为**收紧**（`default_deny_unknown` 改精确文案、
`stdout.contains("ok")` 改精确失败体）；1 项（`rejects_workspace_drift` 注入点后移）系 DR-1 语义变更所必需，
反例能力未丢且新增 `evidence_diff` 断言；1 项为机械改动（`ViewSpec::default`）。**未发现删除或弱化断言。**

## 4. 未通过 / 未执行项

| 编号 | 状态 | 具体阻塞 |
|---|---|---|
| E1 | 未执行 | 需 `9877`（Godot 编辑器）与 `1234`（LM Studio）同时在线；遗留 run 未跑完 |
| E2–E6 | 未执行 | 同上；离线只能证明这些用例在缺前置时**会真实失败**（DR-9） |
| DR-13 类事项 | 未判定 | 编辑器副产物对候选身份的影响、真实 27B 的 schema 遵从率、副本耗时与快照体积 |

## 5. 遗留风险（验收方提出 + 我方追认）

1. **阶段二完全未开张**：无任何 E1 证据；「已跑通」的说法没有依据。
2. **遗留 `runs/godot-smoke/` 需先清理**：`e1` 会因 `assert!(!run_dir.exists())` 直接失败，真实冒烟前必须删除该目录。
3. **DR-1 引入的唯一无哈希断言的写窗口**：确定性阶段由 Runtime/adapter 自身触发，角色无法注入写操作，
   当前不构成越权；若将来 `build_check` 接受 agent 可控输入，此窗口会成为盲区。建议在 `build_check` 前后
   也记录 manifest 并写入确定性日志（可审计补充），列为后续项。
4. **`evidence_diff` 每类截断 50 条**：大规模越权时清单不完整（哈希仍全量变化），审计存在有界盲区。
5. **`hoh submit` 的 `view_root` 由 `HOH_ARTIFACT_DIR.parent()` 推导**：若被设为无父目录的相对值会让所有带 path 的证据
   被过度拒绝（fail-closed，非安全漏洞）。
6. **D7 的 MCP 作用域限制仍在**：Tester 截图/回放来自编辑器当前工程；靠 `candidate_id` + 双哈希 + doctor 人工确认项绑定，
   「编辑器打开的就是该 workspace」无法自动判定。
7. **`godot_smoke` 不校验产物是否为本次真实 run 产生**：放入伪造产物可能让 E2–E6 在非真实链路上通过。
8. **轮次限额可能不足**：遗留 run 的 planner 以 `LimitsExceeded` 收尾（123 条消息 ≈ 撞上 `step_limit=60`）。
   真实冒烟若再撞限额，应基于证据调整 `agent.step_limit`（配置项，不需改码）。
9. **离线验收无法覆盖**：真实 MCP payload 形状、编辑器副作用、本地 27B 的 schema 遵从率。

## 6. 下一步（阻塞于外部前置条件，需用户配合）

1. 用户打开 Godot 4.7 编辑器并打开 `F:\moonbit-hof-rs\.workspace\mario`（`project.godot` 现已含
   `[editor_plugins] enabled=PackedStringArray("res://addons/godot_mcp_rs/plugin.cfg")`，理论上打开即自动启用插件）；
   LM Studio 保持 `qwen/qwen3.8-27b` 在线（并卸载实验期残留的裸 `qwen3.8-27b` 实例，见 D6）。
2. 我方删除遗留 `runs/godot-smoke/` 后，派发 **T=1 真实冒烟**（新子代理执行，我仍不亲自写业务代码）。
3. 冒烟通过后再补齐 E1–E6 证据，并由**又一批全新验收子代理**复核，届时阶段一才算完成。
