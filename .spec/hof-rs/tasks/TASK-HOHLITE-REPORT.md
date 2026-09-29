# TASK-HOHLITE-REPORT — `hoh-lite`（Python 包 `gameloop`）参考侦察报告

- 任务书：`.spec/hof-rs/tasks/TASK-HOHLITE-REF.md`
- 只读对象：`F:\HarnessOfHarness`，HEAD `ae7cc6fbea312ab50657f6b6036b04974846e151`
  （`docs(readme): add roadmap section`，Mon Sep 28 08:01:51 2026 +0000）
- 对立方：`F:\moonbit-hof-rs`（`hof-rs`），需求 v0.3 / 设计 §15 v0.10 / 验收 v2 / 决策 D216..D235
- 本报告纪律：**只读**、**未运行 hoh-lite 的任何脚本/入口**、**未联网**、**未修改对方仓、未修改 hof-rs 代码/测试/既有 `.spec`/`godot-mcp`**；
  唯一写入是本文件。每条断言给 `路径:行` 并附原文引用；**我的解读**单列在「解读」段落，与证据分离。
- 记法：`H:` = `F:\HarnessOfHarness\hoh-lite\`；`R:` = `F:\moonbit-hof-rs\`。

---

## 1. 结论摘要（≤15 行）

1. `hoh-lite` 是论文 HoH 的**轻量另一次实现**（`gameloop` v0.1.0，Apache-2.0，Python ≥3.12，运行期零依赖），
   Planner→Developer→Tester 三角色 + 跨轮携带"开发文档 / 证据"两条通道，与我们 `hof-rs` 同源**概念**、**不同工**。
2. **它 vendored 的 Godot MCP 与我们不是同一血统**：它是 `satelliteoflove/godot-mcp` v4.1.0（MIT，Node/TS MCP server
   + GDScript addon，stdio↔WebSocket:6550↔调试器协议，**21 个 `godot_*` 工具**）；我们是引擎内 `modules/mcp_server`
   （HTTP `POST http://127.0.0.1:9877/mcp`，**177 条四前缀工具**）。**工具名交集 = 0**。⇒ 只能借概念，不能借代码；
   借代码还同时携带 Apache-2.0/ MIT 义务，且与冻结契约语义冲突。
3. **最值得采纳的 3 条**：
   - **① 工具调用回执 + 类别覆盖闸门**（`core/mcp_evidence.py` 整文件）：Runtime 侧从"每次 MCP 调用的持久回执"
     推导证据完备性（project/lifecycle/runtime_state/runtime_log/interactive_input/screenshot 六类 +
     debug cycle 定义 + 源文件新鲜度闸门 + 硬闸门 vs 过程警告分级）。这正对我们 `E2/E3` 与 `DR-49/DR-54` 的痛点。
   - **② 模型可见的"有界预览"与私有无损证据槽分离**（overlay patch：`persistCallEvidence` / `evidenceContent` /
     `700 * 1024` 上限）：因为 agent 自己的日志会截断 base64 图片，**证据必须由工具层在序列化之前落盘**。
   - **③ 绕过通道封锁**（`local_env.py` 的 PATH shim：非 headless 的 `godot` 直接拒绝、`xdotool`/`ydotool` 屏蔽）
     + **服务端按能力注册**（`--read-only-runtime` 让写工具"根本不注册"）。这是"不可用化"式的权限强制，强于我们的拒绝表。
4. 其余高价值项：历史级发布闸门（`check-public-release`）、**基础设施失败 vs 候选失败**分类、候选 hash 前后比对、
   **报告新鲜度 = mtime+size 快照比对**、attempt/summary/markdown 三层可观测、`reproducibility.json` 可复现清单、
   域策略包 + manifest + sha256、本地资产池。
5. **不建议采纳**：benchmark 神谕评分/外部 rubric judge、把权限外包给第三方 harness CLI 的 `--sandbox`、
   forth 移植其 Python/TS/GDScript、WebSocket+addon+autoload 通道、per-role 多模型/reasoning_effort、
   342 KB vendor overlay 模式、其 `usage` 缺失即 `None` 的处理（我们 R12 更严）。
6. **我们完全缺失的能力**（按价值）：① 工具调用级回执；② 私有无损证据槽；③ 绕过封锁；④ 端点/进程身份化清理；
   ⑤ 域策略包与清单；⑥ 可复现清单；⑦ 历史级发布闸门；⑧ 本地资产池。

---

## 2. §3.1 总览与一次完整迭代的时序

### 2.1 这是什么（证据）

- `H:pyproject.toml:6-7`：
  ```
  name = "gameloop"
  version = "0.1.0"
  ```
- `H:pyproject.toml:8`：`description = "General iterative game-development loop with a GameCraft adapter."`
- `H:pyproject.toml:10`：`license = "Apache-2.0"`；`H:pyproject.toml:13`：`dependencies = []`（**运行期零依赖**）。
- `H:pyproject.toml:15-22`（可选 extras，逐字）：
  ```
  gamecraft-bench = [
    "harbor==0.23.0",
  ]
  deepseek-harness = [
    "deepseek-harness-sdk==0.1.0rc6",
    "deepseek-harness-runtime-bin==0.1.0rc6",
  ]
  ```
- `H:pyproject.toml:24-37` console scripts：`gameloop`、`gameloop-gamecraft`、`gameloop-summarize`、
  `gameloop-summarize-runs`、`gameloop-godot-docs`、`gameloop-godot-mcp`、`gameloop-godot-mcp-smoke`、
  `gameloop-godot-mcp-vendor`、`gameloop-gamecraft-doctor`、`gameloop-harness-doctor`。
- `H:README.md:3-7`：
  > "HoH-lite is a lightweight, extensible implementation of the core
  > [Harness-of-Harness](https://arxiv.org/abs/2609.01481) workflow. It runs the
  > Planner–Developer–Tester loop and carries the project forward between
  > iterations."
- `H:src/gameloop/core/loop_engine.py:1`：`"""Benchmark-neutral Planner → Developer → Tester orchestration."""`
- 角色只有三个：`H:src/gameloop/core/roles.py:10-13`
  ```
  class RoleName(str, Enum):
      PLANNER = "planner"
      DEVELOPER = "developer"
      TESTER = "tester"
  ```

### 2.2 怎么跑起来

- `H:README.md:15-28`（Quick start，逐字要点）：
  ```
  You need Python 3.12+, Godot 4, and the CLI and credentials for your chosen
  harness. The bundled example also needs an external benchmark checkout,
  Node.js/npm, bubblewrap, Xvfb, xdotool, and FFmpeg for MCP and replay.
  ...
  cp .env.example .env
  # Set GAMELOOP_HOME, GAMELOOP_BENCH, and your local credentials in .env.
  gameloop-godot-mcp-vendor prepare
  gameloop --config configs/harnesses/codex-gpt-5.5.json \
    --bench /path/to/benchmark \
    --task tasks/your-task \
    --run-id my-run
  ```
- `H:README.md:30-36`：run-id 必须全新；续跑用 `--seed-trial-dir` + `--start-loop-index`，
  或 `--resume-from runs/old-run --run-id new-run`；"Partial work in an interrupted loop is left untouched in the old run."
- `H:README.md:38-41`：每次 run 写 `reproducibility.json`，"The paper used Codex CLI 0.142.5"。
- 环境变量面：`H:.env.example:5-9`（`GAMELOOP_HOME`、`GAMELOOP_BENCH`）、`:17`（`GAMELOOP_JOBS_DIR`）、
  `:22-26`（资产库与 mountpoint）、`:32-33`（Godot 二进制）、`:36`（`GAMELOOP_GODOT_MAX_CPUS=4`）、
  `:40-43`（backend/隔离逃逸口）、`:47`（MCP 启动窗口 45 s）、`:52`（`GAMELOOP_GODOT_MCP_OFFLINE_ONLY=1`）。

### 2.3 核心循环（代码级）

`H:src/gameloop/adapters/gamecraft_bench/runner.py` 是真正的外层编排（3436 行）：

| 行 | 证据（原文摘录） |
|---|---|
| `runner.py:2603` | `for ordinal in range(1, args.attempts + 1):` |
| `runner.py:2604-2607` | `loop_index = args.start_loop_index + ordinal - 1` / `runtime.begin_loop(loop_index)` / `attempt_dir = run_dir / loop_tag(loop_index)` |
| `runner.py:2627-2633` | `loop_artifacts = build_loop_artifacts(...previous_best...previous_demo_evidence...evidence_history...public_task_instruction...)` |
| `runner.py:2634-2676` | `if args.planner_mode == "harness":` → `build_project_planner_evidence_packet` → `build_project_planner_prompt` → `run_project_planner` → `loop_artifacts["development_document"] = planner_run.document` |
| `runner.py:2742-2746` | `write_developer_mcp_config(...)`；`:2749` `run_inner_repair_policy = args.llm_tester and args.tester_policy == "repair-then-next"` |
| `runner.py:2825-2839` | `runtime.invoke(RoleName.DEVELOPER, invoke_primary_developer, summarize=...)`（summarize 里带 `summarize_godot_mcp_evidence(...)`、`mcp_cleanup`） |
| `runner.py:2844-2855` | `mcp_coverage_gaps(..., role="developer", minimum_debug_cycles=1, minimum_run_count=2 if use_warm_start else 1)` |
| `runner.py:2871-2876` | `mcp_runtime_source_freshness_gaps(...)` 追加进 `developer_mcp_gaps` |
| `runner.py:2882-2891` | `if ... args.require_developer_mcp_coverage and developer_mcp_gaps:` → `trial_error = {"type": "invalid_developer_mcp_coverage", ...}` |
| `runner.py:2904-2951` | 内环验收：`tester_phase="acceptance"` 的 Tester；`while ... tester_failure_is_repairable(...) and not tester_acceptance_passed(...) and repair_index < args.max_inner_repairs` |
| `runner.py:3181-3186` | 修复失败时 `break`，注释原文："Preserve and score the last valid candidate when a repair process, MCP gate, or repair trial fails instead of replacing it with a broken copy" |
| `runner.py:3206-3213` | `final_evaluation_status = evaluate_candidate_with_verifier(...)`（外部评分） |
| `runner.py:3290-3312` | 外环 Tester：`tester_phase="next_loop"` |
| `runner.py:3313-3319` | `loaded_demo_evidence = load_next_loop_evidence_report(attempt_dir / "visual_playtest_report.json")` → `previous_demo_evidence = loaded_demo_evidence`（**跨轮证据通道**） |
| `runner.py:3390-3391` | `all_attempts.append(attempt_record)` / `write_json(attempt_dir / "attempt.json", attempt_record)` |
| `runner.py:3415-3416` | `write_json(run_dir / "summary.json", summary)` / `write_summary_markdown(run_dir, summary)` |
| `runner.py:3418-3424` | `record_skipped_role(TESTER, ...)` 若未见过；`runtime.finish_loop()` |
| `runner.py:3426-3430` | `if returncode != 0: return returncode`；`if args.stop_reward is not None and reported_reward >= args.stop_reward: break` |

### 2.4 一次迭代的时序（我按上述证据整理；**这是整理，不是新证据**）

```
loop t:
  1. begin_loop(t)                       → runtime_receipt.json 落盘（core/runtime.py:190-204）
  2. build_loop_artifacts(t)             → public_execution_snapshot / issues / loop_memory /
                                           demo_evidence_matrix / development_document(vNNN) /
                                           development_doc_delta / evidence_history
                                           （core/prompts.py:440-522）
  3. Planner（仅 loop t>1 收 evidence_packet）
     输出 = 「### Priority Order / ### Preservation Gate / ### Acceptance Gate」叠加层（150-350 词）
     Runtime 把它插进确定性脚手架文档的 "Development Focus For This Loop"
  4. Developer（warm start 自 A_{t-1}；MCP 全权）
     → 工具回执 call-*.json 落在 attempt_dir/mcp-evidence/
     → 覆盖闸门 + 源新鲜度闸门（可选硬闸门）
  5. 【内环】Tester(acceptance) → 若可修复且未超 max_inner_repairs：Developer 修复 → 再 acceptance（最多 2 轮）
  6. 外部评分（verifier / rubric judge；可 defer）
  7. 【外环】Tester(next_loop) → visual_playtest_report.json{remaining_bugs, next_loop_goals, preserve, evidence}
  8. evidence_history 追加；写 attempt.json / summary.json / summary.md
  9. finish_loop()；returncode!=0 或 reward>=stop_reward ⇒ 停
```

---

## 3. §3.2 架构对照表（`core`/`harnesses`/`policies`/`adapters`/`benchmarks`/`tools`/`templates`）

### 3.1 目录职责（证据）

| 目录 | 证据 | 职责（原文/摘录） |
|---|---|---|
| `core/` | `core/roles.py:1` `"""Role and capability contracts for the public GameLoop runtime."""`；`core/runtime.py:2-5` `"The runtime is not an agent. It owns sequencing and auditable receipts while role implementations remain replaceable harness invocations."` | 角色契约、编排、回执、证据模型、提示词与文档构建、策略、子进程、完整性、可复现、资产池、MCP 证据 |
| `harnesses/` | `harnesses/base.py:1` `"""Harness-neutral role invocation contracts."""`；`harnesses/registry.py:33-44` 注册 `CodexHarness`/`DeepSeekHarnessAdapter`/`OpenCodeHarness`/`PiHarness` | 「把一段 prompt 变成一个角色进程」的适配器 + 注册表 |
| `policies/` | `policies/generic.md:1` `### Generic playability`；`core/domain_policy.py:1` `"""Small, public, capability-oriented game-development policy packs."""` | 6 个公开域策略文档 + 选择器 + 清单 |
| `adapters/` | `adapters/gamecraft_bench/adapter.py`、`runner.py`、`local_env.py`、`artifacts.py`、`verifier.py`、`judges/codex_cli.py` | GameCraft-Bench 具体适配器（含它自己的 `LocalEnvironment` 与 verifier 入口） |
| `benchmarks/` | `benchmarks/base.py:1` `"""Small, serializable boundary between GameLoop and any benchmark."""` | 基准无关边界：`TaskSpec`/`BenchmarkContext`/`CandidateRef`/`EvaluationResult`/`BenchmarkAdapter` |
| `tools/` | `tools/godot_mcp.py:1` `"""Runtime-owned launcher for the pinned Godot MCP server and editor."""` | Godot MCP 启动器/诊断/vendor 管理/smoke/docs |
| `templates/` | `templates/development_document.md`、`development_brief.md`、`development_doc_delta.md`、`project_planner_prompt.md` | 确定性 Markdown 模板（`{{var}}` 替换） |
| `resources/` | `resources/deepseek_harness/*.yml`、`run_gamecraft_*.sh` | 打包进 wheel 的运行时资源 |
| `_vendor/` | `_vendor/godot-mcp.lock.json`、`_vendor/godot-mcp-gameloop.patch`、`_vendor/godot_mcp/**` | 上游 Godot MCP 快照 + GameLoop overlay |

### 3.2 与 `hof-rs` 的逐行对照

| hoh-lite 概念 | 其证据 | hof-rs 对应物 | 判定 |
|---|---|---|---|
| `RoleName`/`RoleBinding`（含 `WorkspaceAccess{read-only,read-write}`、`GodotMCPAccess{disabled,read-only-runtime,read-write}`） | `core/roles.py:10-24`、`:27-37` | `Role` + `tools/policy.rs` 角色白名单；`DESIGN-DETAIL §4.4` | **我们有等价，但它把"能力"做成可序列化、可在构造期拒绝的绑定**（`roles.py:44-54` 对 Planner 给 live MCP / 非 Developer 给写权限直接 `raise ValueError`） |
| `GameLoopRuntime.begin_loop/invoke/finish_loop` + `runtime_receipt.json` | `core/runtime.py:71-139`、`:190-204` | `runtime/run_loop.rs` + `runtime/record.rs` | 等价；我们有更细的 `RoleOutcome`/usage |
| 角色转移表（`PLANNER→DEVELOPER→TESTER`，`TESTER→{DEVELOPER,TESTER}`） | `core/runtime.py:144-163` | `run_loop.rs` 固定顺序 + `DR-18/DR-37` wrap-up retry | 等价；它显式允许 `TESTER→TESTER` 以支撑"内环验收 + 外环 next-loop" |
| `LoopEngine.run`（三角色 + `benchmark.evaluate`） | `core/loop_engine.py:47-83` | `run_loop.rs` | 等价（它把 `evaluate` 也放进 loop，我们**明确不做评分**，REQUIREMENTS §2.2） |
| `EvidenceBundle` 式划分（verified / gap / handoff） | `core/evidence.py:430-467`（`clean_loop_memory`：`prd_claims`/`implemented_claims`/`verified_demo_claims`/`open_issues`/`next_loop_targets`） | `model.rs EvidenceBundle{verified[],gap[],planner_handoff{...}}`（R7） | 等价概念；它用 JSON 结构 + `source` 标签，我们用互斥不变式；**它的 `preserve` 段与我们的 `preservation_constraints` 同义** |
| 工具调用回执 + 类别覆盖 | `core/mcp_evidence.py`（全文 377 行） | **无** | **缺失项（最高价值）** |
| 确定性模板渲染的 `D_t` 脚手架 | `core/prompts.py:28-32`、`:312-388`、`templates/development_document.md` | `prompts/*.md`（`include_str!` 静态，无变量）；`Planner` 输出整份 `D_t` | 结构差异：**它 = 确定性脚手架 + Planner 叠加层**；我们 = Planner 全权产物 |
| 域策略包 + manifest + sha256 | `core/domain_policy.py:39-82`、`:89-125`、`:128-142`、`:145-171`；`policies/*.md` | `prompts/skills/*.md`（静态注入） | **半缺失**：我们有权能技能文档，但**没有选择逻辑、没有清单、没有 sha256、没有注入审计** |
| 公开证据策略常量 | `core/policy.py:6-11`、`:22-28` | R11 + `runtime.private_excludes`（`DESIGN-DETAIL DR-3`） | 等价概念；它是**常量文本 + 违禁词表**，不构成强制 |
| 候选完整性（`candidate_source_sha256`） | `core/integrity.py:9-37` | `runtime/evidence.rs` 的 `candidate_id = sha256(排序 (路径,内容))` | 等价；**排除项不同**：它排除 `.godot/.import/reports/demo_outputs/logs`、`addons/godot_mcp`、`*.uid/*.import/*.tmp`、符号链接 |
| 可复现清单 | `core/reproducibility.py:50-89` | `meta.json.engine`（DR-44 引擎身份）+ `spec.sha256` | **弱缺失**：我们没有 config sha256 / harness 版本 / git dirty |
| 本地资产池 | `core/assets.py:30-127` | **无** | **缺失项** |
| Harness 抽象（4 实现 + 注册表） | `harnesses/base.py:35-39`、`registry.py:33-44` | `harness/mod.rs` + `MiniHarness`（唯一实现，C2 不可改 mini） | 架构同形、数量不同；我们的"单 harness 固定"是论文语义（H 固定），**不建议照抄多 harness 注册表** |
| Benchmark 抽象 | `benchmarks/base.py:55-82` | `adapter/mod.rs ProjectAdapter` | 概念同形；它含 `evaluate()`，我们**明确不做** |
| 子进程监督（wall/idle 双超时 + 进程组清理） | `core/execution.py:107-218` | mini `LocalEnvironment`；`DR-20` MCP 就绪等待 | 等价概念；它的 **idle timeout 注释写入 stderr**（`execution.py:149-159`）值得借 |
| 模板目录 | `templates/*.md` + `tool.setuptools.package-data`（`pyproject.toml:42-54`） | `prompts/*.md`/`skills/*.md` | 等价 |
| Godot MCP | `_vendor/godot_mcp/**`、`tools/godot_mcp.py` | `godot-mcp/godot/modules/mcp_server/**`（冻结，177 契约） | **不同血统**（见 §6） |

---

## 4. §3.3–§3.7 逐项

> 每小节内先「证据」，再以 **解读：** 开头标注我的判断。

### 4.1 §3.3 角色、循环、终止、预算与重试

**证据**

- 角色与能力绑定（构造期强制）：`core/roles.py:44-54`
  ```python
  if self.role is not RoleName.DEVELOPER:
      if self.workspace_access is WorkspaceAccess.READ_WRITE:
          raise ValueError(
              f"{self.role.value} cannot receive a read-write candidate workspace"
          )
      if self.godot_mcp is GodotMCPAccess.READ_WRITE:
          raise ValueError(
              f"{self.role.value} cannot receive read-write Godot MCP"
          )
  if self.role is RoleName.PLANNER and self.godot_mcp is not GodotMCPAccess.DISABLED:
      raise ValueError("planner cannot receive a live Godot MCP binding")
  ```
- 默认绑定三档：`core/roles.py:85-100`（Developer `READ_WRITE`/`READ_WRITE`；Tester `READ_ONLY`/`READ_ONLY_RUNTIME`；Planner `READ_ONLY`/`DISABLED`）。
- per-role 独立 harness/model/reasoning_effort：`core/roles.py:104-153`；`configs/gameloop.example.json:10-29` 三角色各自 `"harness"/"model"/"workspace_access"/"tools"`。
- 转移合法性（含 `TESTER→{DEVELOPER,TESTER}`）：`core/runtime.py:144-163`；`finish_loop` 前必须有 Developer：`runtime.py:135-137`
  > `raise RuntimeError("a loop cannot finish before the Developer stage")`
- 预算/终止/重试（`configs/gameloop.example.json`）：
  ```
  :6   "attempts": 3,
  :7   "mode": "clean",
  :36  "warm_start_latest": true,
  :37  "llm_tester": true,
  :38  "tester_policy": "repair-then-next",
  :39  "max_inner_repairs": 2,
  :40  "require_developer_mcp_coverage": false,
  :41-44  "timeout_seconds": 3600 / "developer_idle_timeout_seconds": 900 /
          "tester_timeout_seconds": 0 / "tester_idle_timeout_seconds": 1800
  ```
- `runner.py:1008-1020`（CLI）：`choices=["next-loop", "repair-then-next"]`；
  > `"repair-then-next runs bounded same-loop acceptance repair before "` … `"Maximum same-loop developer repair passes for --tester-policy repair-then-next."`
- 内环修复循环条件（逐字）：`runner.py:2945-2951`
  ```python
  while (
      trial_error is None
      and tester_failure_is_repairable(inner_acceptance_status)
      and not tester_acceptance_passed(inner_acceptance_status)
      and repair_index < args.max_inner_repairs
      and reported_trial is not None
  ):
  ```
- "可修复"的定义（把基础设施失败与超时排除在重试之外）：`runner.py:429-439`
  ```python
  return status.get("status") not in {
      "infrastructure_failed",
      "invalid_candidate_mutation",
  } and not bool(status.get("timed_out"))
  ```
- 修复失败时保留最后有效候选：`runner.py:3181-3186`（注释见 §2.3 表）。
- Planner 输出契约（与我们的 R6 逐字一致的三段标题）：`templates/project_planner_prompt.md:68-85`
  ```
  ## Project Planner Priorities
  ### Priority Order
  ### Preservation Gate
  ### Acceptance Gate
  ```
  以及 `:49-50`："Choose at most three priorities."、`:87` "Keep the complete overlay between 150 and 350 words."
- Planner 只做"叠加"，不改脚手架：`project_planner_prompt.md:54-61`
  > "The following deterministic document is the final structural baseline. It will be preserved verbatim by the runtime. Your output is inserted into its `Development Focus For This Loop` section, so do not repeat or rewrite the document."
- 两阶段 Tester 输出契约：`adapters/gamecraft_bench/prompts.py:61-115`
  - acceptance：`phase=acceptance`、`status`、`repair_required`、`acceptance_checklist`、`mismatches`、`evidence`、`recommendation`；"Do not include `next_loop_goals` in the inner acceptance report."
  - next_loop：`phase=next_loop`、`status`、`remaining_bugs`、`next_loop_goals`、`preserve`、`evidence`、`recommendation`；"Do not request same-loop repair in this outer report."
- 角色工具指导文本很长且带"预算建议"（例：Developer "roughly 8-24 successful calls"、Tester "roughly 12-30"、":124-128" "Past 27 calls, make only those missing closeout calls"）：`tools/godot_mcp.py:37-155`。
- usage 逐次记录但**归一化很弱**：`harnesses/output.py:24-92`（codex/dsh 找 `turn.completed.usage`；opencode 找 `step_finish.part.tokens`；pi 找 `message.usage`），未命中即 `usage = None`；`runner.py:1658-1669` 把它逐 attempt 记进 `command_attempts[].usage`。

**解读（我的判断，非实测）**

1. 与我们 `Planner/Developer/Tester + step_limit + wrap-up/repair` 的**结构差异有三条**：
   (a) 它的 Planner 不是 `D_t` 的唯一作者——`D_t` 由 Runtime 的确定性模板生成，Planner 只写 ≤350 词的三段叠加层。
   这把"文档结构的可验证性"从模型手里拿走，比我们 R6 的"整份 `D_t` 由 Planner 产出 + schema 校验"更不容易违约。
   (b) 它把 Tester 一分为二（内环 acceptance 闸门 / 外环 next_loop 交接），并允许 `TESTER→DEVELOPER` 同环修复最多 2 次；
   我们只有一个 QA 角色 + 每角色 wrap-up retry。
   (c) 它的预算单位混用：wall timeout + **idle** timeout + `attempts` + `max_inner_repairs` + 提示词里的"调用次数建议"，
   而 MCP 调用次数上限实际由 MCP server 侧执行（见 4.5）。我们是统一的 `step_limit` + 退出码。
2. 它的"可修复性分类"（`infrastructure_failed`/`invalid_candidate_mutation`/`timed_out` 一律不重试）与我们 `DR-56`（业务错误恰一次、传输层才重试）
   **方向一致但切法不同**：我们按 **JSON-RPC 错误类别**分，它按 **角色运行状态**分。两者互补：`DR-56` 解决"同一进程内不该重试"，
   它解决"整个角色进程不该被再拉起来"。这是一条低风险、高一致性的可借项。
3. 它的 usage 归一化**弱于我们 R12**：`usage = None` 是"缺失即静默"，而我们要求 `usage_known=false` 显式落盘且 token 字段为 null。
   ⇒ 我们在这一点上**不应向它看齐**。

### 4.2 §3.4 证据与验证

**证据**

- **Runtime 拥有的调用回执**：`tools/godot_mcp.py:1` `"""Runtime-owned launcher for the pinned Godot MCP server and editor."""`；
  回执由 overlay 在 MCP server 内写入：`_vendor/godot-mcp-gameloop.patch:5430` `+export function persistCallEvidence(`，
  `:5482-5490`
  ```js
  const receipt = {
    schema_version: 1,
    source: 'gameloop.godot-mcp-evidence',
    call_id: callId,
    completed: true,
    tool,
    arguments: args,
    expected_project: process.env.GODOT_MCP_EXPECTED_PROJECT ?? null,
    structured_content: structuredContent,
    images,
  };
  ```
  图片先落盘再记录哈希/尺寸（`patch:5460-5478`：PNG magic 校验、`sha256`、`width`/`height`、`bytes`、`ordinal`）。
- **回执校验（防御式）**：`core/mcp_evidence.py:11-12` `MAX_RECEIPTS = 5_000` / `MAX_RECEIPT_BYTES = 2 * 1024 * 1024`；
  `:276-285`
  ```python
  isinstance(value, Mapping)
  and value.get("schema_version") == 1
  and value.get("source") == "gameloop.godot-mcp-evidence"
  and value.get("completed") is True
  and isinstance(value.get("tool"), str) ...
  ```
  图片必须是**相对路径 + 哈希逐字节相符 + 非符号链接**：`mcp_evidence.py:360-377`。
- **类别覆盖闸门**：`mcp_evidence.py:161-207`，角色必需类别逐字：
  ```python
  required = {
      "developer": {"project","lifecycle","runtime_state","runtime_log","interactive_input","screenshot"},
      "tester":    {"project","lifecycle","runtime_state","runtime_log","interactive_input","screenshot"},
  }
  ```
  以及 `:190-191` `return ["no_successful_godot_mcp_calls", *gaps]`、`:199` `minimum_debug_cycles = 1 if role == "developer" else 0`。
- **debug cycle 定义**：`mcp_evidence.py:100-129`（`godot_editor_edit.run` 开环；`stop` 记 `active_cycle_stop_at_ms`；
  必须同时具备 `{runtime_state, runtime_log, interactive_input, screenshot}` 才算一个完成的 debug cycle），
  且 `:114-116` 注释：
  > "Godot retains the just-ended run/editor log after stop. Let a Developer inspect that log immediately after teardown, but do not let post-stop state/input/image calls manufacture a playtest that did not happen while the run was live."
  实现为 `:116` `active_cycle.update(call_categories & {"runtime_log"})`。
- **类别判定基于参数形状而非"有响应"**：`mcp_evidence.py:295-357`（例：`input` 只有在 `arguments["inputs"]` 非空数组、
  或 `action=="sequence"`、或 `type_text` 有 `text` 时才算；screenshot 只有 `has_valid_image` 时才算）。
- **源文件新鲜度闸门**：`mcp_evidence.py:227-273`
  ```python
  """Require runtime-affecting edits to precede the last complete MCP cycle.
  Reports, deterministic replay traces, Godot import metadata, and the vendored
  MCP addon are validated or managed elsewhere and do not invalidate a runtime
  playtest.  ``project.godot`` is also ignored because MCP lifecycle cleanup
  restores it after stopping the editor."""
  ```
  返回 `runtime_source_changed_after_last_debug_cycle:<path>`。
- **硬闸门 vs 过程警告**：`mcp_evidence.py:210-224`
  ```python
  if (warm_start and not coverage_gaps and int(summary.get("debug_cycle_count", 0) or 0) < 2):
      return ["warm_start_baseline_cycle_incomplete"]
  ```
  ;`runner.py:2877-2891` 把 `developer_mcp_warnings` 与 `developer_mcp_gaps` 分开，只有 `args.require_developer_mcp_coverage` 为真时 gap 才升级为 `trial_error`。
- **模型可见预览 vs 私有无损证据槽**：`patch:6190` `+const MAX_MODEL_CAPTURE_BASE64_CHARS = 700 * 1024;`，其上方注释（`patch:6183-6189`）：
  > "Codex serializes an MCP response into one JSONL item and truncates items at roughly 1 MiB. Individual context previews are already bounded by the Godot bridge, but a multi-frame sequence can still exceed that ceiling in aggregate. Keep enough headroom for labels, structured state, and JSON escaping; every lossless frame remains in evidenceContent for the private GameLoop evidence sink even when its preview is omitted here."
  `core/types` 侧（`patch:5244-5248`）：
  > "Optional full-fidelity blocks for GameLoop's private evidence sink. These are deliberately omitted from the MCP response so a compact preview can reach the model without duplicating a large lossless image in context."
- **证据新鲜度（报告文件本身）**：`runner.py:462-492` `_visual_report_snapshot`（记录 `(st_mtime_ns, st_size)`）；
  `runner.py:495-522` `_fresh_visual_review_status`；使用处 `runner.py:1617`（调用前快照）与 `:1652-1657`
  ```python
  fresh_review_status = _fresh_visual_review_status(before, attempt_dir, report_path, trial_dir)
  fresh_report = fresh_review_status in VISUAL_TESTER_REVIEW_STATUSES
  if fresh_report:
      review_status = fresh_review_status
  ```
  并落盘 `"fresh_report": fresh_report`（`:1663`）。
- **候选未被 Tester 改动**：`runner.py:1592` `candidate_hash_before = candidate_source_sha256(...)`；
  `:1696-1697`
  ```python
  candidate_hash_after = candidate_source_sha256(authoritative_candidate_game_dir)
  candidate_unchanged = candidate_hash_before == candidate_hash_after
  ```
  `:1718` `tester_status = "invalid_candidate_mutation"`；注释 `:1585-1588` 解释为何哈希的是 **authoritative** 候选而非 Tester 的工作副本
  （Tester 副本里的 addon/导入元数据是 Runtime 自己注入的，哈希它会把正常 setup 误判成篡改）。
- **基础设施失败 ≠ 候选失败**：`artifacts.py:52-91` `has_judge_infrastructure_failure`，其 docstring（`:53-57`）：
  > "Return whether a verifier score is incomplete because its judge failed. Missing demos or replay frames are candidate failures and remain comparable zero scores. Other per-demo judge failures mean the recorded aggregate may be zero or only partially scored, so callers must rejudge it."
  `verifier.py:118-120`：
  > "A zero threshold allows a valid low score, not missing replay or judge evidence. Callers must be able to distinguish infrastructure failure."
- **Q: 它有没有类似我们的证据分区/可启动闸门/QA 三件套？**
  - 证据分区：**有等价但形状不同**——`verified_demo_claims` + `evidence_gaps`/`remaining_bugs` + `preserve` + `next_loop_goals`
    （`core/evidence.py:430-467`、`prompts.py:101-115`），并以"互斥性"以外的**来源标签**（`source`）区分。
  - 可启动闸门：**没有独立的 `launchable` 闸门常量**；替代物是 verifier 的 `build_ok`（`verifier.py:27-28`、`artifacts.py:99`）
    与 MCP 覆盖闸门（要求 project+lifecycle+...）。**未读到**形如我们 `artifact_gate.launchable` 的独立结构。
  - QA 三件套（截图/回放/运行时节点证据）：**有，但走 `demo_outputs` 回放 + MCP 回执两条路**：
    `artifacts.py:20-40`（`SUPPORTED_DEMO_EVENT_TYPES`、`SUPPORTED_DEMO_KEYCODES`）、`:106-120` `validate_demo_trace_schema`；
    MCP 侧 `mcp_evidence.py` 六类。`templates/visual_tester_prompt.md:39-43` 明确规定
    只接受 `mouse_click/mouse_down/mouse_up/mouse_move/key_press/key_down/key_up/wait`，
    > "Treat `action`, `game_action`, `invoke`, and other custom method events as a hard evidence failure because the official evaluator cannot replay them."

**解读**

1. 这是全仓对 `hof-rs` **最有价值的一节**。我们当前证据链的薄弱点恰是"证据由谁产生、凭什么是这一轮的"：
   我们的 `capture_frames`/`execute_gdscript` 证据是**被测角色自己调用、自己转述**的，而 `DR-49` 只能用"调用前作废既有文件"
   这种局部手段保证新鲜。hoh-lite 把这件事转了 90°：**Runtime 侧持有每次工具调用的回执**（含参数、哈希过的产物图像、区分端点/项目），
   再由 Runtime 推导"覆盖是否完整、是否本轮、是否在 run 存活期间"。这是结构性更强、且**离线可测**（回执是纯文件输入）的方案。
2. `mcp_runtime_source_freshness_gaps` 是我们 `DR-49` 的**推广**：它不问"这张图是不是新的"，而问"最后一次完整观测之后，
   **还有没有会改变运行行为的源文件被改过**"，并显式豁免"由 Runtime/import 管理的产物"与 `project.godot`。
   这正对着我们 `DR-48` 假阴性（把引擎信息行当错误）与 `DR-49`（截图新鲜度）那一整族问题的根因——**判据必须落在"谁改的、改了什么"上**。
3. `evidenceContent` 分离这一条有一处**硬约束冲突**必须点名：它是在 **MCP server 内部**实现的（overlay patch 改的是 vendored server）。
   我们的对应层是**引擎侧 `modules/mcp_server`（冻结、不改）**，所以**不能照搬位置**，只能在 `hof-rs` 的 `ToolChannel` 侧做等价物：
   收到 image payload 时由我们写盘 + 哈希 + 记回执。**这一点必须在设计里写清，否则实现子代理会去改引擎。**
4. `candidate_source_sha256` 的**排除清单**（`.godot/.import/reports/demo_outputs/logs`、`addons/godot_mcp`、`*.uid/*.import/*.tmp`、符号链接）
   是一份可核对的现成清单，值得与我们 `cache_excludes`（`DESIGN-DETAIL DR-11`）逐条比对，尤其是它把
   **`addons/<被管控的 MCP addon>` 排除掉**的理由（`:24-25` `if relative.parts[:2] == ("addons", "godot_mcp"): continue`）——
   我们 DR-41 正是在处理"addon 与缓存残留污染候选身份"的同类问题。
5. 我**没有**读它是否有等价于我们 `E5` 的"快照 hash 前后一致 + 版本库三树同 hash"的**独立复算**要求；
   已读到的是"before/after 相等"的布尔判定（`runner.py:1697`）。⇒ 写到 §9。

### 4.3 §3.5 工具与 MCP 层（重点核实同源性）

**问题：`tools/godot-mcp` 与 `_vendor/godot_mcp` 到底是什么？是否与我们引擎的 `modules/mcp_server` 同源/同契约？**

**证据（来源与版本）**

- `H:tools/godot-mcp` 全文只有一行（**不是代码，是指向 vendor 的符号链接式占位**）：
  ```
  ../src/gameloop/_vendor/godot_mcp
  ```
  同形：`H:tools/godot-mcp.lock.json` → `../src/gameloop/_vendor/godot-mcp.lock.json`。
- `H:src/gameloop/_vendor/godot-mcp.lock.json:1-17`（逐字）：
  ```json
  {
    "schema_version": 2,
    "id": "satelliteoflove-godot-mcp",
    "source": "https://github.com/satelliteoflove/godot-mcp",
    "commit": "15794ee995188b2a850a73e16ed568e7414f2d04",
    "server_version": "4.1.0",
    "license": "MIT",
    "checkout": "godot_mcp",
    "vendored_source": { "sha256": "db8bc5c35e2b064b798f03b52c18aac0b471df2a1af9b5a9189f069d8eb31730", "file_count": 266 },
    "overlay": { "path": "godot-mcp-gameloop.patch", "sha256": "bc858754d8a9b159b4120093c80e1312d9b159eaa2ae26fe3e7ae8f1bab12f5c" }
  }
  ```
- `H:src/gameloop/_vendor/godot_mcp/server/package.json:2-4`：`"name": "@satelliteoflove/godot-mcp"` / `"version": "4.1.0"` / `"type": "module"`；
  `:53-57` 依赖 `@modelcontextprotocol/sdk`、`ws`、`zod`；`:52` `"license": "MIT"`；`:51` `"author": "Christopher Childress"`。
- `H:src/gameloop/_vendor/godot_mcp/server/server.json:3-6`：`"name": "io.github.satelliteoflove/godot-mcp"` / `"version": "4.1.0"`；
  `:41-43` `"transport": { "type": "stdio" }`。
- 通道架构（逐字，`_vendor/godot_mcp/docs/architecture.md:14-23`）：
  ```
  Client <-->|"stdio (JSON-RPC)"| Server
  Server <-->|"WebSocket :6550"| Addon
  ...
  2. Server ↔ editor addon. A WebSocket on 127.0.0.1:6550 by default ...
  3. Editor addon ↔ running game. No second socket ... the editor side sends
     `godot_mcp:`-prefixed debugger messages via an EditorDebuggerPlugin ... Because it rides
     the debug wire, the running game needs no extra ports, no network permissions, and no per-project setup.
  ```
  `_vendor/godot_mcp/README.md:113`：
  > "The server talks to an editor addon over a local WebSocket; the addon reaches into the running game over Godot's own debugger protocol, so the game process needs no extra ports or setup."
- 工具数量与命名（我实测统计，见下）：`architecture.md:21`
  > "The server (`server/src/`) defines the 21 tools (and no MCP resources — everything is a tool, including the scene tree via `godot_node_read get_scene_tree`), validates arguments with Zod schemas, and translates tool calls into bridge commands."
- addon 侧是 `godot/addons/godot_mcp/**`（GDScript），入口 `godot/addons/godot_mcp/plugin.cfg`；GameLoop 侧常量
  `H:src/gameloop/tools/godot_mcp.py:26`：`PLUGIN_PATH = "res://addons/godot_mcp/plugin.cfg"`。

**证据（与我方契约的逐项对照 —— 我的实测统计，方法是正则抽取两侧工具名）**

| 项 | hoh-lite vendored (`satelliteoflove/godot-mcp` 4.1.0) | 我们 (`hof-rs` 引擎 `modules/mcp_server`) |
|---|---|---|
| 工具数 | **21** | **177** |
| 命名 | `godot_<域>[_read/_edit]`（如 `godot_editor_read`、`godot_input`、`godot_runtime_state`） | 四前缀扁平：`editor_*` 104、`project_*` 48、`running_game_*` 23、`os_*` 2 |
| 名字交集 | **0**（我用两侧集合求交，结果为空） | — |
| 传输 | MCP **stdio**（`server.json:41-43`）+ 到 addon 的 `ws://127.0.0.1:6550`（`architecture.md:22`） | **HTTP `POST http://127.0.0.1:9877/mcp`，JSON-RPC 2.0**（`R:.spec/hof-rs/REQUIREMENTS.md:59`） |
| 游戏通道 | 复用引擎**调试器协议**（无第二端口，`architecture.md:23`） | 独立**游戏端点**（`editor_play_scene` 注入 `--mcp-port`，23 条 game-only；`REQUIREMENTS.md:59`、`ACCEPTANCE.md:27`） |
| 实现形态 | Node/TS server + GDScript addon（`server/src/**`、`godot/addons/godot_mcp/**`） | 引擎内 **C++ 原生模块**（`R:godot-mcp/godot/modules/mcp_server/**`） |
| 契约事实源 | `server/src/tools/*.ts`（Zod schema；有 `__toolsnaps__/*.json` 快照测试） | `R:godot-mcp/godot/modules/mcp_server/docs/tools_list.renamed.json`（177 条；`_meta.count=177`、`tool_count_in=174`、`added_count=6`、`excluded=[navigate_to, export_project]`、`merged=[get_editor_performance→editor_get_performance_monitors]`、`generator_version=1.23.0`） |
| 只读能力边界 | 服务端 `--read-only`（只注册 `readOnlyHint` 工具）/ `--read-only-runtime`（Tester：只注册只读 + `godot_input`/`godot_game_time` + 一个受控的 `runtimeEditorEdit`） | 引擎侧 **scope**（editor-only / shared / game-only）**不按角色**；角色裁剪由我们 `hof-rs` 的拒绝表做 |

（我方工具名前缀与计数来自对 `R:godot-mcp\godot\modules\mcp_server\docs\tools_list.renamed.json` 的正则统计；
其 `_meta` 亦自述 `"generated_from_sha256": "8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54"`、
`"map_path": "...godot/modules/mcp_server/docs/tool-rename-map.json"`。）

**结论（证据直接支持，非推断）**

- **不同源、不同契约、不同传输、不同实现语言，工具名交集为 0。**
  它是 `satelliteoflove/godot-mcp` v4.1.0 的一个**快照 + 342 KB overlay**，与我们引擎的 `modules/mcp_server` 无关。
- 它**不是**我们旧 GDExtension 时代 `addons/godot_mcp_rs` 的分支，也**不是**我们新契约的旧版或变体。
- **命名碰撞危险（需注意）**：它的 addon 目录叫 `addons/godot_mcp`（`tools/godot_mcp.py:26`），
  与我们已于 `DR-41` 拆除的 `addons/godot_mcp_rs` 名字高度相似。任何读者/子代理都可能把二者混为一谈。
  → 建议在我方文档中显式写明"hoh-lite 的 godot_mcp ≠ 我们的 godot_mcp_rs"。

**overlay 做了什么（我们可能想借的概念，逐条已核）**

| 机制 | patch 行 | 内容 |
|---|---|---|
| 运行时只读注册 | `patch:6125-6160` | `networkDocsEnabled()`（`GAMELOOP_GODOT_MCP_OFFLINE_ONLY !== '1'` 才注册 `docsTools`）；`runtimeControlNames = new Set(['godot_input','godot_game_time'])`；Tester 只注册只读 + 这两个 + 受控 `runtimeEditorEdit` |
| 调用预算（服务端执行） | `patch:5343-5353`、`5517-5520` | `isRuntimeReadOnlyMode()`、`successfulCallLimit()`（默认 30，`GAMELOOP_MCP_MAX_SUCCESSFUL_CALLS`），`stop` 调用豁免；超限返回文本"Runtime QA MCP budget reached"（`patch:5526-5533`） |
| 回执落盘 | `patch:5430-5510` | `persistCallEvidence`：`mkdirSync(mode:0o700)`、PNG magic 校验、`sha256`、`.pending-<uuid>` → `renameSync` 原子落盘、失败只 `logger.warning` 绝不把成功的 Godot 操作变成失败动作 |
| 无损证据槽 | `patch:5244-5248`、`6183-6190` | `evidenceContent`（不进 MCP 响应）+ 模型侧 `700 KiB` 上限 |
| 鼠标输入 | `patch:6214-6235` | 新增 `MouseButtonEntrySchema`（`position`）/`MousePositionEntrySchema`，`InputEntrySchema` 并集扩容 |

**解读**

- 对我们而言，**可借的是这 5 条机制的设计意图与判据**；**不可借的是实现位置**（我们没有可改的 server；`godot-mcp/**` 不得改）。
  其中"服务端按能力注册（写工具不存在）"在我们这里**不能落地在引擎侧**，但可以在 `hof-rs` 的 `TOOLS.md` 生成与
  `hoh tools call --role` 之间加一层"**对角色不可见**"（我们已有拒绝表，缺的是"不暴露"），并在视图目录里放 PATH shim（见 4.4）。
- 它的 overlay 用 **342 KB patch** 覆盖上游 56 个文件的行为，包括改工具 schema（`godot-input` 的鼠标成员）。
  这恰恰是我们 `DR-42/DR-45` 花大力气**消灭**的模式（契约必须有一份唯一事实源、旧词归零、不存在别名映射）。
  ⇒ 列为**不建议采纳**（见 §7）。

### 4.4 §3.6 模型/提供方抽象

**证据**

- 没有统一的"模型客户端"，而是**每个 harness CLI 一份适配器**：
  `harnesses/registry.py:33-44` 注册 `codex`/`deepseek-harness`/`opencode`/`pi`；`harnesses/base.py:12-22`
  ```python
  @dataclass(frozen=True)
  class HarnessRequest:
      binding: RoleBinding
      workspace: Path
      prompt_path: Path
      output_path: Path
      environment: Mapping[str, str]
      json_stream: bool = False
      ephemeral: bool = True
      sandbox_mode: str | None = None
      extra_config: tuple[str, ...] = ()
  ```
- Codex：`harnesses/codex.py:21-48`，逐字关键 flag：
  ```python
  command = [executable, "exec", "--ignore-user-config", "--ignore-rules"]
  if request.ephemeral: command.append("--ephemeral")
  if request.json_stream: command.append("--json")
  command.extend(["--sandbox", request.sandbox_mode or ("read-only" if ... else "workspace-write"),
                  "--skip-git-repo-check", "-C", str(request.workspace), "--model", request.binding.model,
                  "-o", str(request.output_path)])
  ```
  以及 `:50-53` `model_reasoning_effort="{...}"`。
- 提供方（OpenAI 兼容）配置：`harnesses/providers.py:8-55`（Bailian：`"npm": "@ai-sdk/openai-compatible"`、
  `"apiKey": "{env:BAILIAN_API_KEY}"`）；`:58-90`（PJLab：`"api": "openai-completions"`、`"apiKey": "$PJLAB_API_KEY"`）；
  `:93-105`（Pi：`"retry": {"enabled": True, "maxRetries": 10, "baseDelayMs": 1000, "provider": {"maxRetries": 2, "maxRetryDelayMs": 60000}}`）。
- 密钥卫生：
  - `harnesses/doctor.py:21-25` 只打印 `"credentials": {"BAILIAN_API_KEY": "set" if present else "missing"}`（`:54-57`），**从不打印值**；
  - `harnesses/deepseek.py:139-157` 支持 `*_API_KEY_FILE` 读文件注入，缺失即 `raise RuntimeError`；
  - `harnesses/deepseek.py:158-163` 对 `danger-full-access` 要求显式确认：
    > `"official standalone minimal uses danger-full-access; set GAMELOOP_DSH_ALLOW_DANGER_FULL_ACCESS=1 only in an isolated or trusted evaluation environment"`;
  - `env.py:50-95` 的 dotenv 分层带 `protected_keys`：**已存在的 shell 环境变量不会被 `.env` 覆盖**（`:57-61`、`:78`）。
- 版本 pin：`doctor.py:21-25` `EXPECTED = {"opencode": ("opencode","1.14.30","deepseek-v4-pro"), "pi": (...,"0.80.10","minimax-m3")}`；
  `deepseek.py:14-32` 把 preset/cordis 的 **sha256 常量写死在代码里**并与文件逐字节比对（`validate_minimal_bundle`）。
- 超时：每角色 **wall + idle 双超时**（`configs/gameloop.example.json:32-44`）；进程组清理
  `core/execution.py:30-63`（`terminate_process_group` → `os.killpg(SIGTERM)` → 2 s 宽限 → `SIGKILL`）；
  idle 超时写进 stderr 说明（`execution.py:149-159`）。

**与我们的差异（对照 `R:REQUIREMENTS.md` C5/C9/C10/C11）**

| 维度 | hoh-lite | hof-rs |
|---|---|---|
| 模型接入 | 每角色跑一个**外部 agent CLI**（codex/opencode/pi/dsh），模型名是 CLI 参数 | mini 的 `openai_compatible` 端点，`model.wire_model_name` 双重锁定（C9） |
| 多提供方 | 支持（4 harness × 多 provider，`configs/harnesses/*.json`） | **有意单一**（H 固定，论文语义） |
| per-role 模型 | 支持，且 per-role `reasoning_effort` | 不允许（C9/C10；换模型只改配置整体） |
| 密钥 | `.env` / `*_API_KEY_FILE`；doctor 只打印 set/missing | 环境变量 `HOH_MODEL_API_KEY`/`OPENAI_API_KEY`；不入库（C11）；且 `DR-19` 要求密钥不进子进程环境 |
| 环境隔离 | 靠 harness CLI 的 `--sandbox` 与 `--ignore-user-config/--rules/--ephemeral` | 靠位置隔离 + 哈希检测 + 工具白名单（`DESIGN-DETAIL §4.4`） |
| 超时 | wall + idle 双超时，`returncode=124` | 每角色独立限额；`DR-20` 有 MCP 就绪等待与 retry |

**解读**

1. 它在模型层面**比我们宽得多**（多 harness、多 provider、per-role 模型与 effort）；这在它的定位（跑 benchmark、比不同 harness）下合理，
   但与我们"H 固定、单 harness–model"的论文语义**正面冲突**。⇒ 只借"密钥卫生 + pin + 双超时"三点，不借多提供方架构。
2. `--ignore-user-config`/`--ignore-rules`/`--ephemeral` 这组 flag 的思想值得借：**把"跑起来的结果不依赖用户机器上的残留配置"变成启动参数**。
   我们 mini 是库、无此 flag（C2 不可改），但等价物是：**把影响运行的用户级/机器级配置显式记入 run 元数据并断言**（见 §6 A-12/A-13）。
3. 它对 DSH preset 用**代码内 sha256 常量 + 逐字节校验**，与我们 `C9` 的"双重锁定"同族。可作为我们"配置 pin"的形态参考。

### 4.5 §3.7 配置、打包、可观测性（含 benchmarks/policies/templates 机制）

**证据**

- 配置面：
  - `configs/gameloop.example.json`（46 行，全文见 §4.1 引用）；`configs/harnesses/*.json` 5 份 profile
    （`codex-gpt-5.5.json`、`dsh-minimal-deepseek-v4-flash.json`、`dsh-standard-deepseek-v4-flash.json`、
    `opencode-deepseek-v4-pro.json`、`pi-minimax-m3.json`）。
  - 打包：`pyproject.toml:39-62`（`packages.find where=["src"]`；`package-data` 含 `templates/*.md`、`policies/*.md`、
    `_vendor/godot_mcp/**/*` 与 `_vendor/godot_mcp/**/.*`；`exclude-package-data` 排除 `node_modules`/`dist`/`addon`/`coverage`）；
    `MANIFEST.in` 存在（368 B，**未读全文**）。
- 可观测性三层：
  1. **角色回执**：`runtime_receipt.json`（`core/runtime.py:190-204`：`schema_version`/`runtime: "gameloop-lite"`/
     `coordination: "deterministic-host"`/`active_loop`/`roles`/`events[]`），其中每个事件含
     `loop_index/sequence/role/status/started_at/duration_seconds/details`（`runtime.py:22-41`）。
  2. **每次尝试**：`attempt.json`（`runner.py:3357-3391`，~30 字段，含 `developer_mcp`、`developer_mcp_coverage_gaps`、
     `developer_mcp_warnings`、`inner_acceptance`、`inner_repairs[]`、`final_evaluation`、`visual_tester`、`planner`、`baseline_trial`）。
  3. **run 汇总**：`summary.json` + `summary.md`（`runner.py:3392-3416`），并有 `write_summary_markdown`
     （`runner.py:2374`）与 `summarize_attempt_rewards`（`runner.py:2348`）；另有独立 CLI `gameloop-summarize` / `gameloop-summarize-runs`。
- **生命周期回执**：`tools/godot_mcp.py:736-752` `_write_lifecycle_receipt(status, **details)` → `mcp-evidence/lifecycle.json`，
  状态值出现 `waiting_for_project`/`running`/`recovering`/`stopped`/`blocked`（`godot_mcp.py:248`、`:306`、`:327`、`:393`、`:178`）。
- **进程身份化清理**：`godot_mcp.py:755-871`（只清理"证据目录与进程 environ 绑定相符、且是进程组组长"的进程；
  不匹配则 `identity_mismatch` 并 `cleanup_blocked`），`:_process_evidence_root`（`:874-889`）读 `/proc/<pid>/environ` 的
  `GAMELOOP_MCP_EVIDENCE_DIR`，`:_godot_argv_targets_project`（`:892-910`）要求 `--path` 精确相等。
- `reproducibility.json`（`core/reproducibility.py:50-89`）：`python`/`system`/`source_revision`/`source_dirty`/
  `benchmark_revision`/`benchmark_dirty`/`config_sha256`/`roles`/`harness_versions`/`godot_version`/`paper_harness_version`。
- **发布/合规闸门**（`scripts/check-public-release`，56 行）：
  ```
  :15  if [[ -n "$(git ls-files -- tests docs)" ]]; then fail "development tests or docs are tracked in the public checkout"; fi
  :30  for commit in $(git rev-list HEAD); do
  :32    if rg -q "$forbidden_path_pattern" <<< "$paths"; then ...
  :35    if git grep -q -I -E "$machine_path_pattern" "$commit" -- .; then ...
  :38    if git grep -q -I -E "$credential_pattern" "$commit" -- .; then ...
  :43-50 python3 校验 pyproject 的 project.license 元数据
  ```
  其中 `:27` `credential_pattern='(^|[ =])((sk|rk|pk)-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16})($|[ ])'`。
- `benchmarks`/`policies`/`templates` 三个机制（**我们完全没有的**）：
  - `benchmarks`：`benchmarks/base.py:10-82` 四个 dataclass + `BenchmarkAdapter` Protocol；`registry.py:39-44` 懒加载适配器。
  - `policies`：6 个 `.md` + `domain_policy.py:89-125` 选择（显式 id 或按 task-id 前缀 / 关键词 ≥2 命中），
    `:128-142` 生成 manifest（含每个策略的 `sha256`），`:145-171` 渲染成角色化指导；
    `:150-156` 明示边界：
    > "These capability policies are implementation and testing guidance only. They cannot add requirements beyond the public task or justify access to hidden evaluator information."
  - `templates`：`core/prompts.py:28-32` 朴素 `{{var}}` 替换；`development_document.md`（156 行，含 Loop Policy / Version Context /
    Public Task Brief / Development Focus / PM Iteration Upgrade Plan / **Replay Regression Guardrails** /
    Replay-Visible Quality Heuristics / Demo Portfolio Plan / Genre Breadth Planner / Mechanics/Content/Difficulty/Visual/Demo 要求 /
    Compact Quality Checklist / Compatibility Brief）；`development_doc_delta.md`（13 行）。
- 原子写：`core/documents.py:17-38`（`O_EXCL` 临时文件 → 保留原 mode → `fsync(file)` → `os.replace` → `fsync(dir)`）。
- 只读角色的字节级还原：`tools/godot_mcp.py:370-384`
  ```python
  if runtime_qa:
      # Tester owns no candidate source. Restore the exact bytes that
      # preceded addon/editor startup, including original formatting.
      project_file.write_text(before_text, encoding="utf-8")
  ```
- 插件启用段幂等文本改写：`godot_mcp.py:664-733`（`enable_plugin_config_text`/`remove_plugin_config_text`/
  `remove_mcp_project_config`，含 `MCPGameBridge` 与 `[godot_mcp]` 段清理）。
- 每项目随机端口与 CPU 亲和：`godot_mcp.py:556-559`（`_allocate_port` 用 `bind(("127.0.0.1", 0))`）、
  `:531-553`（按项目路径 sha256 选 CPU 集合，`GAMELOOP_GODOT_MAX_CPUS` 默认 4）。

**解读**

1. `reproducibility.json` + `attempt.json` + `summary.{json,md}` + `runtime_receipt.json` 是**同一套事实的四种粒度**，
   且都能独立读。我们目前是 `meta.json` + `result.json` + 每轮 `runs/<id>/iter-<t>/*`，粒度接近，但**缺 run 级 markdown 摘要与
   config sha256 / harness 版本 / git dirty**。这是低成本、高审计收益的可借项。
2. `check-public-release` 是**唯一一项对"历史"生效的闸门**（逐 commit `git grep`）。我们的 C11 只靠 `.gitignore` + 测试，
   **没有历史扫描**；我们上一轮 §15 批次还出现过"提交信息/提交内容需逐条核对"的担忧（`R:DECISIONS.md:9197-9198`）。这条可借。
   注意：它依赖 `rg`（ripgrep）与 bash，Windows 下需改写；且它会扫**全部可达 commit**，对我们的历史（4000+ 行 DECISIONS）可能要加白名单。
3. 原子写（`fsync` 文件 + 目录）比我们现在的写盘更抗中断；我们 `runs/smoke-t6` 还出现过"目录摘要算法未文档化/不可复现"
   （`R:.spec/hof-rs/ACCEPTANCE.md:83`），原子写是同类问题的基础设施。
4. "Tester 结束后按字节还原 `project.godot`" 与我们 `DR-41/DR-53` 处理 `[editor_plugins]` 与缓存残留的思路同族，
   但更彻底：**它保存启动前原文并在只读角色结束后回写**，而不是"删掉自己加的那一行"。这值得与我方 `DR-53`（畸形 `enabled=` 不改文件）对照。

---

## 5. §3.8 许可与合规

### 5.1 事实（证据）

| 项 | 证据（逐字） |
|---|---|
| **仓根** | `F:\HarnessOfHarness\LICENSE:1-3`：`MIT License` / `Copyright (c) 2026 Hyoung Yan` |
| 仓根 README 的许可声明 | `F:\HarnessOfHarness\README.md:137-139`：`[MIT License](LICENSE). HoH-lite source under [`hoh-lite/`](hoh-lite/) is released under [Apache-2.0](hoh-lite/LICENSE), with its own [notices](hoh-lite/THIRD_PARTY_NOTICES.md).` |
| **hoh-lite 本体** | `H:LICENSE:1-3`：`Apache License / Version 2.0, January 2004`；`H:pyproject.toml:10-11`：`license = "Apache-2.0"` / `license-files = ["LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md"]` |
| hoh-lite NOTICE | `H:NOTICE:1-18`（要点逐字）：`HoH-lite` / `Copyright 2026 HoH-lite contributors` / `distributed under the Apache License, Version 2.0`；`:10-14`：`The vendored Godot MCP implementation under src/gameloop/_vendor/godot_mcp/ is originally from satelliteoflove/godot-mcp and remains available under its original MIT License. Its license and copyright notices are retained in that directory. The GameLoop-specific overlay is described in THIRD_PARTY_NOTICES.md.`；`:16-18`：`GameCraft-Bench is an external checkout and is not included in this source tree.` |
| 第三方清单 | `H:THIRD_PARTY_NOTICES.md:7-16`：`HoH-lite vendors satelliteoflove/godot-mcp at the commit recorded in src/gameloop/_vendor/godot-mcp.lock.json. The upstream project is licensed under the MIT License, retained in src/gameloop/_vendor/godot_mcp/LICENSE.`；`:14-16` 描述 overlay 内容：`adds runtime-QA capability boundaries, reliable screenshots and runtime diagnostics, bounded input/time control, UI/skeleton inspection, connection hardening, and per-process Godot port selection. It does not include private game assets, task policies, benchmark results, or demo product code.` |
| vendored 上游许可 | `H:src/gameloop/_vendor/godot_mcp/LICENSE:1-3`：`MIT License` / `Copyright (c) 2025` |
| 上游版本与快照 | `H:src/gameloop/_vendor/godot-mcp.lock.json`（见 §4.3）：commit `15794ee995188b2a850a73e16ed568e7414f2d04`、`server_version 4.1.0`、`license MIT`、`vendored_source.sha256 db8bc5c3...`、`file_count 266`、overlay `sha256 bc858754...` |
| 上游自身声明 | `_vendor/godot_mcp/server/package.json:52-53`：`"license": "MIT"`、`"author": "Christopher Childress"`；`server/README.md:11209 B`、`CHANGELOG.md:33013 B` 存在 |
| 发布闸门中的许可检查 | `H:scripts/check-public-release:13` `[[ -f LICENSE ]] || fail ...`；`:43-50` 校验 `project.license` 元数据 |

### 5.2 「可采用的**概念/设计**」 vs 「需遵守许可的**代码**」

**A. 可直接采用（无许可义务，因为不复制任何受版权保护的表达）**

以下都是**思想/判据/流程**，且我**已确认**它们不是任何一段具体代码：
- Runtime 侧"每次工具调用落回执 + 按类别算覆盖 + 定义 debug cycle + 源新鲜度闸门"的**判据设计**（`mcp_evidence.py` 的逻辑结构）。
- "模型可见的有界预览"与"私有无损证据槽"分离的**架构决策**（`evidenceContent` 的设计意图）。
- "写工具在只读角色上根本不注册"**vs** 我们的"注册但拒绝"的对比结论。
- "历史级逐 commit 扫描密钥/机器路径/禁目录"的**闸门思路**。
- "基础设施失败 ≠ 候选失败"的**分类原则**。
- attempt/summary/markdown 三层可观测与 `reproducibility.json` 的**字段清单**。
- "确定性脚手架 + Planner 叠加层"的 `D_t` 生成方式。
- 域策略包"选择 + 清单 + sha256 + 明示不可加需求"的**治理形态**。
- 原子写（`fsync` 文件与目录）、只读角色字节级还原、每项目随机端口/CPU 亲和。

> 采用方式：**由我（决策者）写进 `hof-rs` 的设计文档，再由实现子代理用 Rust 重写**；
> 不复制 hoh-lite 的 Python 源码、不复制其 Markdown 模板全文、不复制其 patch 片段。

**B. 如果复制代码，会带上什么义务（必须说清）**

| 来源 | 许可 | 复制后的义务 |
|---|---|---|
| `hoh-lite/**`（含 `core/`、`harnesses/`、`templates/`、`policies/` 等） | **Apache-2.0**（`H:LICENSE:1`、`H:pyproject.toml:10`） | 需保留 `LICENSE` 与 `NOTICE`（`H:NOTICE:1-18`）、在修改过的文件上标明改动、可能需附 `THIRD_PARTY_NOTICES.md`；**Apache-2.0 不是 copyleft**，不要求我们整体开源，但**不得移除版权与许可声明**，且专利授权条款随之生效 |
| `hoh-lite/src/gameloop/_vendor/godot_mcp/**`（266 文件） | **MIT**（`_vendor/godot_mcp/LICENSE:1`、`package.json:52`） | 复制/衍生须保留版权声明与许可全文；MIT 与 Apache-2.0 **兼容**，可并入 |
| `hoh-lite/src/gameloop/_vendor/godot-mcp-gameloop.patch`（342 KB overlay） | 由 HoH-lite 贡献者对 MIT 上游的**衍生修改** | 若复制其中任何片段：既负 MIT（上游）又负 Apache-2.0（overlay 作者）义务，并须标明"这是被修改过的上游文件" |
| `F:\HarnessOfHarness` 仓根（README/其他） | **MIT**（仓根 `LICENSE:1`） | 复制需保留声明 |
| `assets/`（182 MB，**未读**） | **无法判定**（未读到其 LICENSE/来源说明） | 不要碰；见 §9 |

**C. 我们的处境（解读）**

1. `hof-rs` 是 Rust，hoh-lite 是 Python/TS/GDScript。**逐行移植既不划算也会引入许可与风格负担**。
   我们已有 `D235` 的纪律：「**不因"别人这么做"而采纳；不照搬；不引入 Python 依赖到 Rust 项目**」（`R:DECISIONS.md:9199-9201`）——
   本报告的所有可采纳项都按"重写概念"计，而非"移植代码"。
2. **与冻结契约的额外冲突**：即使不考虑许可，它的 21 工具契约、`ws://6550`、addon + autoload、debugger 通道
   都与我们 `REQUIREMENTS.md:54-67` 的 C3/C4 与 `ACCEPTANCE.md:27-29` 的 177 = 104+50+23 恒等式**不可调和**。
   这是**比许可更硬**的理由：**不采纳其 MCP 代码或契约**。
3. 我们**不需要**新增任何第三方依赖来落地本报告的可采纳项（全部是 `hof-rs` 内的 Rust 代码与文档）。
   若要借鉴 `check-public-release`，需要开发机上有 `rg`（我们环境已用 grep 工具，属工具面而非依赖面）。

---

## 6. §3.9 可采纳清单（编号表）

> 编号 `HOHL-xx`。每条：**what / why / 证据(file:line) / 成本 / 风险 / 是否与 §1 硬约束冲突 / 优先级**。
> 硬约束 = ① `PRD-mario.md` 逐字节冻结；② 引擎 177 条契约逐字冻结；③ 离线批次不联网；④ 不改 `godot-mcp/**`；⑤ 不新增依赖（如确需先调查上报）。

| # | what | why | 证据 | 成本 | 风险 | 冲突 | 优先级 |
|---|---|---|---|---|---|---|---|
| **HOHL-01** | **Runtime 侧"每次 MCP 调用回执 + 类别覆盖闸门"**：每次调用落 `call-*.json`（tool/args/ok/endpoint/错误类别/图片 path+sha256+尺寸），再按角色算必需类别（project/lifecycle/runtime_state/runtime_log/interactive_input/screenshot）与 debug cycle 数 | 把我们"证据由角色自述"变成"由 Runtime 从回执推导"，直接对应 `E2/E3/E4/E5` 与 `DR-49/DR-54`；纯文件输入 ⇒ **离线可测** | `core/mcp_evidence.py:55-207`、`:276-357`、`:360-377`；`patch:5430-5490`；用法 `runner.py:2844-2855` | 中（新增 `mcp_receipts.rs` + 闸门 + 测试；不动引擎） | 中：类别表若与我们的工具语义不符需重定；**回执必须由我们写**（引擎不改）⇒ 需在 `tools/mcp.rs` 侧落盘 | 无（②不改契约；③不联网） | **P0** |
| **HOHL-02** | **私有无损证据槽与"模型可见有界预览"分离**：图片/回放由 Runtime 在序列化前落盘并记 hash，模型只拿有界预览 | 我们 `capture_frames` 内联 base64 的形态**仍是未验证假设**（`ACCEPTANCE.md:84-85`），且 agent 日志会截断大数据 ⇒ 证据必须不依赖 agent 的序列化 | `patch:6190` 及 `:6183-6189` 注释；`patch:5244-5248`；`mcp_evidence.py:360-377` | 中（adapter 侧写盘 + 尺寸上限 + 新鲜度） | 中：需确认我方工具返回图片的确切形态（见 §9） | 无（落在 `hof-rs`，①不改引擎） | **P0** |
| **HOHL-03** | **绕过通道封锁（不可用化）**：① 在角色视图目录前置 PATH shim，使非 `--headless/--version` 的 `godot` 直接 `exit 126`；② 屏蔽 `xdotool`/`ydotool`；③ 角色可见工具清单里"不出现"其不可用的工具 | 我们 `E3` 失败的形态之一正是"输入注入只到编辑器侧"（`ACCEPTANCE.md:40`）；我们的白名单是**拒绝**，不是**不可达** ⇒ 模型仍可绕道 shell | `local_env.py:31-60`（shim 生成，含 `exit 126` 文案）、`:57-60`（`xdotool`/`ydotool`）；`patch:6125-6160`（按能力注册） | 小-中（Windows 等价的 `.cmd` 桩 + `policy.rs` 断言） | 中：Windows 下 shim 语义与 POSIX 不同；需防误伤我们的合法 headless 构建 | 无 | **P0** |
| **HOHL-04** | **"本轮真实"的通用判据**：① 报告文件用 `(mtime_ns, size)` 快照前后比对证明"本轮新写"；② 源文件新鲜度闸门：最后一次完整观测之后不得有影响运行行为的源文件被改（显式豁免 Runtime/import 管理的产物与 `project.godot`） | 我们 `DR-49` 只对截图做了"调用前作废+新鲜度"，是**局部补丁**；这条把它推广成**通用判据**，并解释了"为什么豁免某些文件是合理的" | `runner.py:462-492`、`:495-522`、`:1617`、`:1652-1657`；`mcp_evidence.py:227-273` | 中（`record.rs`/`schema.rs` 加新鲜度工具 + 豁免清单 + 测试） | 中：豁免清单必须与我方 `cache_excludes`/`DR-3 private_excludes` 一致，否则漏判 | 无 | **P0** |
| **HOHL-05** | **候选完整性判定与"不重试"分类**：Tester 前后对 **authoritative 候选**（而非其工作副本）算 hash；不一致记独立状态 `invalid_candidate_mutation`，且该状态**永不进入修复重试** | 我们 `R4/E5` 已要求候选不被 QA 修改，但缺"独立状态码 + 明确不重试"；它给出一条**为什么哈希对象必须是规范候选而非工作副本**的成熟理由（Runtime 自己注入的 addon/导入元数据会污染哈希） | `runner.py:1585-1592`、`:1696-1697`、`:1718`、`:429-439`、`:442-459`；`core/integrity.py:9-37` | 小 | 低 | 无 | **P1** |
| **HOHL-06** | **基础设施失败 vs 候选失败**的分类与"零分不等于候选失败" | 与 `DR-27/DR-39`（区分"循环完成"与"产物可用"、gate ok≠产品达标）同族；它给出可复用的**分类判据清单**（judge 失败/缺 ffmpeg/xvfb 等 ⇒ infra，缺 demo/帧 ⇒ 候选） | `artifacts.py:52-91`；`verifier.py:118-120`；`runner.py:442-459` | 小 | 低 | 无 | **P1** |
| **HOHL-07** | **debug cycle 的显式定义与"停机后不算证据"** | 直接回应我们 `DR-50B` 的教训（端点挂死后无法区分"死前是否真跑过"）与 `DR-49` 的"旧文件伪造成功" | `mcp_evidence.py:100-129`（含 `:114-116` 注释）、`:116` | 小（并入 HOHL-01） | 低 | 无 | **P1** |
| **HOHL-08** | **硬闸门 vs 过程警告双层**（warm-start 基线 cycle 缺失只记 warning；覆盖缺失才升 hard error，且由配置开关控制） | 我们多次因"闸门过严/假阴性"返工（`DR-24/DR-48/DR-37`）；把"过程不完整"与"证据不成立"分开是**降低假阴性**的系统化做法 | `mcp_evidence.py:210-224`；`runner.py:2877-2891`、`:2882-2891` | 小 | 低 | 无 | **P1** |
| **HOHL-09** | **两阶段 Tester（内环 acceptance / 外环 next_loop）+ 同环有界修复**，且两阶段输出契约互斥（acceptance 不许写 `next_loop_goals`；next_loop 不许要求同环修复） | 我们 QA 单阶段同时承担"本轮验收"与"交接下一轮"，两件事的判据不同却混在一份 `E_t`；它证明**分开更可判定**，且"修复失败保留最后有效候选"避免用坏副本覆盖好副本 | `prompts.py:61-115`；`runner.py:2945-2951`、`:3181-3186` | 大（**属设计变更** ⇒ 必须回 `DESIGN-DETAIL` 新增条目，不能在实现里偷偷改） | 中：会改 `E_t` 语义与 CLI 退出码，需用户裁决 | 无（但触发阶段关卡回退） | **P1** |
| **HOHL-10** | **历史级发布闸门**：逐可达 commit 扫描密钥字面量/机器路径/禁目录，并校验 license 元数据 | 我们 C11 只有 `.gitignore` + 测试，**没有任何历史扫描**；我们上一批还专门警惕"提交内容需逐条核对" | `scripts/check-public-release:13-50`（尤其 `:27` 密钥正则、`:30` `git rev-list HEAD`） | 小-中（Windows 改写；加白名单） | 中：全历史扫描可能命中我方的旧证据路径；需先干跑 | 无（不联网、不加依赖；`rg` 属工具） | **P1** |
| **HOHL-11** | **可复现清单**：`config_sha256` / harness（模型）版本 / git rev + dirty / OS / 引擎版本 / 角色绑定 | 我们 `meta.json` 有引擎身份与 spec hash，但**没有配置哈希与"跑之前工作区是否脏"**；§15 批次已明确"引擎构建非位级可复现，不得用 sha 当新鲜判据"⇒ 需要多字段并列 | `core/reproducibility.py:50-89`；`README.md:38-41` | 小 | 低 | 无 | **P1** |
| **HOHL-12** | **run 级 markdown 摘要 + 独立 summarize CLI** | 我们只有 `result.json`；人能读的摘要缺失，不利于 D235 式"逐条核对提交" | `runner.py:2374`（`write_summary_markdown`）、`:3416`；`pyproject.toml:30-31` | 小 | 低 | 无 | **P1** |
| **HOHL-13** | **域策略包 + 选择 + manifest(sha256) + 明示"不可加需求"** | 我们的 `prompts/skills/*.md` 是静态注入，**没有"注入了哪些指导、其哈希是什么"的审计**；D235 要求"任何建议都要有落文" | `core/domain_policy.py:39-82`、`:89-125`、`:128-142`、`:145-171`；`policies/generic.md:1-7` | 小-中 | 中：**别让它变成"prompt 里的需求"**（P-1 要求契约在 Runtime）；必须照抄它那句"不能加需求"的边界声明 | 无 | **P1** |
| **HOHL-14** | **端点/进程身份化清理**：清理只杀"证据目录 environ 绑定相符 + `--path` 精确相等 + 进程组组长"的进程；不匹配即 `cleanup_blocked` | 我们有 `DR-44` 引擎身份**入库**，但**缺**"清理时也校验身份"⇒ 可能误杀同机其他 Godot 实例（我们的编辑器是长期打开的） | `godot_mcp.py:755-871`、`:874-889`、`:892-910`、`:913-953` | 中（Windows 用 `Get-CimInstance Win32_Process` 替 `/proc`） | 中：Windows 无 `/proc`，等价物需 spike 验证 | 无 | **P1** |
| **HOHL-15** | **本地资产池**（只读扫描 + 路径逃逸防护 + 逐字节哈希校验 + `network_access: False` 清单） | 我们没有任何"资产池"概念；阶段二要"跑出好软件"时这是空白 | `core/assets.py:30-127`（`:110-119` 逃逸防护、`:80-82` 哈希不符即删） | 小-中 | 低 | **③不联网**（它本身就是 offline-only，方向一致） | **P2** |
| **HOHL-16** | **wall + idle 双超时，idle 超时把原因写进 stderr 日志** | 我们多次出现"干烧 12 分钟"（`ACCEPTANCE.md:79`、`DR-55`）；idle 超时是最直接的止血阀 | `core/execution.py:107-218`（尤其 `:149-159`） | 小 | 低 | 无 | **P2** |
| **HOHL-17** | **单客户端独占（拒绝第二个连接）** | 我们 `DR-41` 的"双绑定"问题本质是**两个提供者争同一端口**；它给出"新人被拒而不是顶掉现有会话"的判据 | `_vendor/godot_mcp/docs/architecture.md:36`（`close code 4001 "another client is already connected"`）、`:40` | 小 | 低（引擎侧不改，只作我方 doctor 断言） | 无 | **P2** |
| **HOHL-18** | **JSON 原子写**（`O_EXCL` 临时文件 → 保留 mode → `fsync(file)` → `os.replace` → `fsync(dir)`） | 我们 `runs/smoke-t6` 有"摘要不可复现"遗留（`ACCEPTANCE.md:83`）；半写文件是审计杀手 | `core/documents.py:17-38` | 小 | 低 | 无 | **P2** |
| **HOHL-19** | **只读角色结束后按字节还原被 Runtime 改动过的工程文件** | 比"删掉自己加的那一行"更彻底；与我们 `DR-53`（畸形 `enabled=` 不改文件）同族 | `godot_mcp.py:370-384`（含 `:376-378` 注释） | 小 | 低 | 无 | **P2** |
| **HOHL-20** | **工具清单快照测试**（`__toolsnaps__/*.json` + `toollist-snapshot.test.ts` + `schema-fidelity.test.ts`） | 我们已有夹具逐字比对（`DR-42/DR-52`），可借其**per-tool snapshot 文件组织方式**做回归 | `_vendor/godot_mcp/server/src/__tests__/core/toollist-snapshot.test.ts`、`__toolsnaps__/`（21 个 json） | 小 | 低 | 无 | **P3** |
| **HOHL-21** | **issue id 命名规范**：`loop-NN-<source>-<slug>` | 我们 `DR-*`/`TC-TOOL-*` 是编号，它给"来源可读"的 id 形态 | `core/evidence.py:152`、`:189`、`:216`、`:241`、`:252`、`:261`、`:272`；`core/stages.py:6-7` | 小 | 低 | 无 | **P3** |
| **HOHL-22** | **`--ignore-user-config/--ignore-rules/--ephemeral` 式"机器残留隔离"**：我们 mini 不可改，但可把影响运行的用户级配置**显式记入 run 元数据并断言** | 它把"结果不依赖用户机器残留"变成启动参数；我们只能变成**记录 + 断言** | `harnesses/codex.py:21-30` | 小 | 低 | 无（C2 不改 mini，只记断言） | **P3** |

---

## 7. §3.10 明确不建议采纳清单（hof-lite 做了而我们**有意**不做）

| # | 不采纳项 | 它的证据 | 理由（为什么不采纳） |
|---|---|---|---|
| **N-01** | Benchmark 神谕评分 / 外部 rubric judge / reward 驱动循环 | `adapters/gamecraft_bench/verifier.py:101-120`；`runner.py:3206-3213`、`:3428-3430`（`stop_reward`）；`benchmarks/base.py:76-82`（`evaluate`） | 我们**明确非目标**（`R:REQUIREMENTS.md:39-42` §2.1/§2.2）：不复现论文分数、不实现 benchmark adapter、私有评分永不进 prompt 或 `E_t`（C7）。借它的评分机制会直接违反 C7 |
| **N-02** | 把角色权限外包给第三方 agent CLI 的 `--sandbox read-only/workspace-write` | `harnesses/codex.py:33-39` | 违反我们的 `P-1 契约在 Runtime，不在 prompt/外部工具`（`R:DESIGN-OVERVIEW.md:18`）；且 mini 是库、无此 flag（C2 不可改）。**我们的实现反而更严**：拒绝表 + 位置隔离 + 哈希检测 |
| **N-03** | 移植其 Python / TypeScript / GDScript 代码到 Rust | 全仓 | `D235` 已定"不引入 Python 依赖到 Rust 项目"（`R:DECISIONS.md:9201`）；且许可上会引入 Apache-2.0/MIT 义务（§5.2B）；逐行移植还会把它的 Linux-only（bwrap/Xvfb/xdotool）假设带进来，违反 C1（Windows 本机） |
| **N-04** | 复用其 vendored Godot MCP（21 工具 / stdio / `ws://6550` / addon + autoload / debugger 通道） | `_vendor/godot_mcp/**`、`architecture.md:14-23` | 与 C3/C4 正面冲突：我们固定 HTTP `POST 127.0.0.1:9877/mcp` + 引擎内 `modules/mcp_server` + **177 条四前缀契约**（`R:REQUIREMENTS.md:58-59`、`R:ACCEPTANCE.md:27-29`）；且 `godot-mcp/**` 不得改 |
| **N-05** | `vendor 上游 + 342 KB overlay patch` 的演进模式 | `_vendor/godot-mcp-gameloop.patch`（6879 行，改 56 文件，含改工具 schema） | 我们 `DR-42/DR-45` 的核心成果就是**消灭这种"多套词汇 + patch 叠加"**：唯一事实源、旧词归零、禁止别名映射（`R:REQUIREMENTS.md:220-222`）。这是**退步** |
| **N-06** | per-role 多 harness / 多 provider / per-role `reasoning_effort` | `core/roles.py:104-153`；`configs/gameloop.example.json:10-29`；`harnesses/registry.py:33-44`；`configs/harnesses/*.json` | 我们的 H 是**固定 harness–model 配置**（论文语义，`R:REQUIREMENTS.md:16-18`、`:191`）；C9/C10 要求模型身份配置驱动且双重锁定。per-role 换模型会破坏跨轮可比性 |
| **N-07** | `usage` 缺失即 `None`（静默） | `harnesses/output.py:36`、`:59`、`:73`（`usage = None`） | 我们 R12 更严：`usage_known=false` 且 token 字段为 `null` 而非 0（`R:REQUIREMENTS.md:103`、`R:DESIGN-DETAIL.md §3` 不变式 3）。向它看齐是**降低**我们已有的保证 |
| **N-08** | 三角色 prompt 里塞入整份 `D_t` / 整份历史 | 它自己已经纠正这个错误：`core/prompts.py:184-189` "Repeating entire QA reports and the full history here makes later planning calls attend to old prose instead of current product gaps."；`templates/development_document.md:150-152` "it is not duplicated here because repeated history competes with implementation attention." | 我们 `ALT-6` 已否决"把 177 个工具/大上下文塞进 prompt"（`R:DESIGN-OVERVIEW.md:266`）。它的裁剪实践**支持**我们已有方向；不要退回"全文注入" |
| **N-09** | `demo_outputs` 回放 trace 合约（`mouse_click/key_press/...` 白名单）作为**验收判据** | `artifacts.py:20-40`；`templates/visual_tester_prompt.md:39-43` | 我们的 `E3` 判据是 MCP 语义工具 + 截图/断言（`R:DESIGN-DETAIL.md §15.1 DR-54`），**不引入 replay trace 评分**（非目标 §2.1/§2.2）。其"事件类型白名单"思想可选择性用于我们证据的**形状校验**，但不采用其评分语义 |
| **N-10** | `danger-full-access` 默认执行形态 + bwrap/Xvfb/xdotool/ffmpeg 的 Linux 容器化运行形态 | `.env.example:37-43`、`:74-76`；`harnesses/deepseek.py:158-163`；`local_env.py:1-6` | 违反 C1（Windows 本机可编译可运行）；我们的 `A6` 明确单机单用户、不做多租户/抗恶意代码沙箱（`R:REQUIREMENTS.md:48`）。**但其"要求显式确认危险模式"的形态**可借（我们已有等价纪律） |
| **N-11** | `experiments/`、`--experiment-id`、`compat.py` 的多实验编排 | `runner.py:2348`、`:2601`；`adapters/gamecraft_bench/experiments.py`（3480 B，未读） | 属"跑 benchmark 对比不同 harness"的需求，我们非目标；引入会扩大配置面而不增加 Runtime 语义正确性 |
| **N-12** | 把 `tester_policy`（`next-loop`/`repair-then-next`）与 `external_verifier`/`require_developer_mcp_coverage` 做成用户可选开关 | `configs/gameloop.example.json:35-40`；`runner.py:1008-1020`、`:1169` | 我们的消融开关**只有论文规定的三个**（`plan_update`/`evidence_feedback`/`warm_start`，R8），且"每个开关只改一个输入"是可测判据（`R:REQUIREMENTS.md:99`）。加开关会稀释可解释性。若采纳 HOHL-09，应作为**固定语义**而非**可选开关** |

---

## 8. §3.11 我们完全缺失的能力（按对 `hof-rs` 的价值排序，含"若要引入"的最小落地设想）

> 每条给出：**缺什么 / 证据 / 最小落地设想（不改引擎、不联网、不加依赖）**。

**M-1｜工具调用级回执与覆盖闸门（最高价值）**
- 缺：`hof-rs` 的证据是"电池步骤的 payload"（`DR-17`），**没有**"每次 MCP 调用的持久回执"，因此"这一轮到底发生了什么调用"无法独立于角色自述被重建。
- 证据：hoh-lite `core/mcp_evidence.py:37-158`（回执 → 汇总）、`patch:5430-5510`（写回执）；它的用法 `runner.py:2844-2855`、`:2871-2891`。
- 最小落地：`tools/mcp.rs` 每次调用后写 `runs/<id>/iter-<t>/mcp-receipts/call-<seq>.json`
  `{schema_version, tool, args_sha256, endpoint(editor|game), ok, error_class{transport|business}, transport_attempts, duration_ms, images[]}`；
  新增 `runtime/mcp_coverage.rs`（纯函数：`summarize(receipts) -> Coverage`、`gaps(coverage, role, min_cycles)`）；
  离线测试用 `FakeToolChannel` 造回执，断言"缺 screenshot ⇒ gap""stop 之后的 state/input/screenshot 不构成 cycle"。
- 与硬约束：**无冲突**（不改引擎、不联网、不加依赖）。⇒ P0

**M-2｜私有无损证据槽**
- 缺：我们依赖工具返回内联 `image_base64`；其形态本身**仍是未验证假设**（`R:.spec/hof-rs/ACCEPTANCE.md:84-85`：
  "未验证的形态假设：内联 `image_base64` 截图应答、`user://` 备选路径、…"）。
- 证据：hoh-lite `patch:6183-6190`、`patch:5430-5478`、`patch:5244-5248`。
- 最小落地：`adapter/godot.rs` 在拿到图片 payload 时**由 Runtime 写盘**（`.hoh/evidence/<iter>/shots/*.png`）+ 记 sha256/宽高，
  证据里只引用相对路径；给模型的内容保持有界。
- 与硬约束：**无冲突**（在 `hof-rs` 侧；且 `DR-36` 已有"`.hoh/evidence/**` 必须复制进冻结候选"的前例）。⇒ P0

**M-3｜绕过通道封锁（不可用化）**
- 缺：我们的工具白名单是"调用被拒绝"；模型仍可 `godot --path ... ` 起自己的编辑器、或用 `xdotool` 直接注入输入，从而**绕过 MCP 而产不出回执证据**。
- 证据：hoh-lite `local_env.py:31-60`（godot shim，`exit 126`，只放行 `--headless|--version`）、`:57-60`（`xdotool`/`ydotool` 屏蔽）；
  `tools/godot_mcp.py:61-63` 的 prompt 里也明说 "The Runtime owns the Godot editor/MCP lifecycle; never start another editor or MCP server from the shell."
- 最小落地：Developer/Tester 视图目录前置 `.cmd`/`.bat` 桩（Windows）：拒绝非 `--headless/--version` 的 `godot*`；把该目录放 PATH 最前；
  在 `policy.rs` 加断言"角色 PATH 首项是本轮 shim 目录"；离线测试断言桩的守护语义（含反例：`--headless` 放行）。
- 与硬约束：**无冲突**（Windows 等价物；不影响我们的真实构建路径，只要桩只作用于角色子进程）。⇒ P0

**M-4｜端点/进程身份化清理**
- 缺：我们有 `DR-44` 引擎身份**入库**（`meta.json.engine` + `engine_identity` 闸门），但**清理/收尾时不校验身份** ⇒ 在我们"编辑器长期打开"的场景下可能误杀。
- 证据：hoh-lite `tools/godot_mcp.py:755-871`、`:874-889`（读 `/proc/<pid>/environ` 的 `GAMELOOP_MCP_EVIDENCE_DIR`）、`:892-910`（`--path` 精确相等）、`:913-953`。
- 最小落地：记录 `editor.pid`/`game.pid`/`listener.pid` 与本轮 run-id 的绑定（我们 `DR-51` 已让端点身份持久化）；
  收尾时用 `Get-CimInstance Win32_Process` 取 `CommandLine`，**要求 `--path` 精确等于本 workspace 且含本轮注入的环境标记**才允许终止。
- 与硬约束：**无冲突**（不改引擎；不联网）。⇒ P1

**M-5｜域策略包 + manifest + 注入审计**
- 缺：我们有 `prompts/skills/*.md`，但**没有**"本轮注入了哪些指导、它们的 sha256、它们不得增加需求"的清单与断言。
- 证据：hoh-lite `core/domain_policy.py:39-82`、`:128-142`、`:145-171`；`policies/generic.md:1-7`。
- 最小落地：把 `skills/*.md` 升级为"策略包"：`policy_id` + `sha256` + 选择依据（显式/关键词）落 `runs/<id>/policy_manifest.json`；
  测试断言"manifest 里每个 sha256 与文件一致""策略文本含不可越过公开规格的边界声明"。
- 与硬约束：**注意**——不能让策略文本变成需求源（C7/R11）；必须带"不能加需求"声明。⇒ P1

**M-6｜可复现清单（config hash / 环境版本 / 工作区脏度）**
- 缺：只有引擎身份 + spec hash；没有配置哈希与"跑之前仓/工作区是否脏"。
- 证据：hoh-lite `core/reproducibility.py:50-89`；`README.md:38-41`。
- 最小落地：在 `meta.json` 增 `config_sha256`、`hoh_binary_sha256`、`repo_revision`+`repo_dirty`、`model_endpoint_host`（**不含密钥**）、
  `engine.listener.matches_binary`（已有）。
- 与硬约束：**无冲突**（C11：只记 host，不记 key）。⇒ P1

**M-7｜历史级发布闸门**
- 缺：C11 的密钥卫生只覆盖工作树与运行期，**没有历史扫描**。
- 证据：hoh-lite `scripts/check-public-release:13-50`。
- 最小落地：`scripts/hoh-public-check.ps1`（或 Rust 子命令 `hoh verify-history`）：对每个 commit 扫密钥形态、绝对机器路径、禁目录；
  干跑后加白名单（我们仓内 `.spec/**` 与 `runs/**` 含大量路径文本）。
- 与硬约束：**无冲突**（不联网；`rg` 若缺失则退化为 `git grep`）。⇒ P1

**M-8｜本地资产池（offline-only）**
- 缺：无资产池概念；阶段二"跑出好软件"时资产来源无契约。
- 证据：hoh-lite `core/assets.py:30-127`。
- 最小落地：`adapter/godot.rs` 增 `asset_pool: Option<PathBuf>`；`hoh assets query/materialize` 两个子命令；manifest 记 `network_access: false` + 每文件 sha256。
- 与硬约束：与"离线批次不联网"**同向**。⇒ P2

**M-9｜run 级人类可读摘要与独立 summarize 命令**
- 缺：只有 `result.json`。
- 证据：hoh-lite `runner.py:2374`、`:3416`；`pyproject.toml:30-31`。
- 最小落地：`record.rs` 落 `summary.md`（循环/预算/退出码/证据覆盖/E 分区计数/未关闭项）；CLI `hoh summarize --run <id>`。
- 与硬约束：无冲突。⇒ P1（低成本）

**M-10｜原子写与 idle 超时**
- 缺：写盘非原子；超时无 idle 维度（我们吃过 730 s / 干烧 12 分钟）。
- 证据：`core/documents.py:17-38`；`core/execution.py:107-218`。
- 最小落地：`record.rs` 用 temp+rename+fsync；工具通道加 idle timeout，超时原因写 stderr 与 attempt 记录。
- 与硬约束：无冲突。⇒ P2

---

## 9. 未读到 / 无法判定清单

**未运行（纪律）**
- **未运行** `hoh-lite` 的任何脚本、console entry、`gameloop*` 命令、`scripts/*`；**未联网**（含 pip、模型端点、`npx`）；
  **未修改** `F:\HarnessOfHarness` 任何文件；**未 stage/commit/push**。所有结论来自静态阅读。

**未读（文件级）**
- `H:assets/`（182 MB）——只在目录清单里看到存在，**内容与来源许可未读**。
- `_vendor/godot_mcp/**` 中 266 个文件**只读了少数**：`LICENSE`、`README.md`（片段）、`INSTALL.md`（片段）、
  `docs/architecture.md`（片段）、`server/package.json`、`server/server.json`、`server/src/tools/*.ts`（**只抽名字**）、
  `.github/**`（未读）。**未做 schema 级逐字段比对**（我对两侧只做了**工具名集合**与**传输/前缀**的比对）。
- 未读清单（部分或全部）：`core/prompts.py`（已读全文）、`core/evidence.py`（全文）以外的
  `core/assets.py`（已读全文）、`core/domain_policy.py`（全文）——**以下未读**：
  `adapters/gamecraft_bench/{adapter,compat,experiments,local_agent,local_env(仅前 60 行),openai_bridge_exec,paths,planner,summarize_results,summarize_runs,runner(部分)}.py`、
  `adapters/gamecraft_bench/judges/{__init__,codex_cli}.py`、
  `tools/{godot_docs,godot_mcp_smoke,godot_mcp_vendor}.py`、
  `harnesses/{opencode,pi,deepseek_worker}.py`、
  `core/__init__.py`、`gameloop/{cli,locations,__init__}.py`、
  `scripts/*`（除 `check-public-release`）、`CONTRIBUTING.md`、`MANIFEST.in`、`.gitattributes`、`.gitignore`、
  `_vendor/godot_mcp/{CONTRIBUTING,INSTALL}.md`、`docs/**` 其余、`resources/**` 全文。
- `H:src/gameloop/adapters/gamecraft_bench/runner.py` 共 3436 行，我**选择性读了约 900 行**（§2.3 表格所列区域 + `:344-543` + `:1580-1709` + `:2560-2689` + `:2690-3432` 的抽样）。其余未读。

**无法判定**
1. **上游 `assets/` 的许可与来源**：未读到 `assets/` 内的 LICENSE/NOTICE/来源说明 ⇒ **不能判定能否复用其任何资产**。
2. **hoh-lite 是否存在独立于 `build_verifier` 的"可启动闸门"**（形如我们 `artifact_gate.launchable`）：
   我看到的是 verifier 的 `build_ok`（`verifier.py:27-28`）与 MCP 覆盖闸门；**未读到**独立的 launch gate 结构 ⇒ **无法判定**。
3. **hoh-lite 的候选身份模型是否与我们 `candidate_id` 等价**：读到 `CandidateRef{path, candidate_id, parent_id}`（`benchmarks/base.py:36-42`）
   与 `candidate_source_sha256`（`core/integrity.py:12-37`），但**未读到**"candidate_id 如何生成/如何与每条证据绑定"的完整链路 ⇒ **无法判定**其强度。
   我没有在 `gamecraft_bench/adapter.py`（未读）里确认 `create_context` 是否计算候选 id。
4. **`_visual_report_snapshot` 是否会因写盘时序产生假阴性**：我只读到快照机制，**没有读到**它的测试 ⇒ 不能判定鲁棒性。
5. **它是否对"角色复用了上一角色的对话上下文"有检测**：三个角色都是**独立进程**（`HarnessRuntime.execute_role` 起进程，`harnesses/runtime.py:66-89`），
   所以结构上不可能共享 messages；但**未读到**"断言三次独立调用"的测试 ⇒ 我只能说"结构上不共享"，不写成"它有 R1 的测试"。
6. **`use_warm_start` 到底把哪个目录作为 Developer 起点**：读到 `prepare_direct_candidate_trial(attempt_dir=..., previous_candidate=baseline_candidate if use_warm_start else None)`（`runner.py:2771-2774`），
   但 `prepare_direct_candidate_trial`（`runner.py:1919`）与 `local_env` 的挂载细节**未读全** ⇒ warm-start 的**精确目录语义无法判定**。
7. **`harbor`/GameCraft-Bench 外部 checkout 的任何行为**：它**不在本仓内**（`NOTICE:16-18`），我**未读** ⇒ 一切涉及
   `gamecraft_bench.*` 导入的行为（rubric、judge、score_project、LocalSubprocessEnvironment）**无法判定**。
8. **PyPI 上发布的 sdist 与仓内 `hoh-lite/` 是否一致**：**未联网，无法判定**。
9. **`godot-mcp-gameloop.patch` 是否为唯一 overlay、是否可干净应用**：lock 文件只声明一个 overlay 与其 sha256；**未尝试应用**（纪律禁止运行）⇒ **无法判定**。
10. **它 21 个工具的 schema 与我们 177 条的语义覆盖关系**：我只比对了**名字集合**（交集 0）；**未做能力矩阵比对** ⇒ 二者"能力重叠/缺失"无法给出量化结论。

---

## 10. 我给决策者的建议排序（P0..P3 及理由）

> 排序标准：**对 `hof-rs` 当前最大风险（E2/E3 可判定性与证据可信度）的边际收益 ÷ 落地成本 × 与硬约束的相容度**。
> 我**不建议**一次性全采纳；建议按批走阶段关卡（设计 → 实现 → 独立验收），每批 1~3 条。

### P0（建议**立刻**回到 `DESIGN-DETAIL` 新增一节，作为下一批的实现目标）

1. **HOHL-01 工具调用回执 + 类别覆盖闸门**（最小落地见 M-1）。
   *理由*：我们 `E2/E3` 两次 `not_met` 的根因都是"证据是否成立、是否本轮、端点是否活着"无法独立判定
   （`R:ACCEPTANCE.md:38-45`、`:89-90`）。回执是把这些变成**纯函数可判定**的唯一务实路径，且完全离线可测。
2. **HOHL-02 私有无损证据槽**。
   *理由*：`ACCEPTANCE.md:84-85` 已把我们"内联 base64 截图"列为**未验证的形态假设**；HOHL-02 同时解决"证据可信"与"上下文爆炸"。
   与 HOHL-01 是一体两面（回执里引用落盘图片）。
3. **HOHL-03 绕过通道封锁**。
   *理由*：成本最小、收益最直接。只要模型还能自己起编辑器或用输入注入工具，**上面两条都可能被绕过**（E3 的"输入注入只到编辑器侧"就是这种形态）。
4. **HOHL-04 "本轮真实"的通用判据**。
   *理由*：把 `DR-49` 的局部补丁升级为通用判据，且它显式回答了"哪些文件应当豁免"（`project.godot`、import 元数据、Runtime 管理的 addon）——
   这正是我们 `DR-41/DR-53` 反复踩的坑。

### P1（同批或紧接一批；都是低成本、低争议）

5. **HOHL-09 两阶段 Tester + 同环有界修复**。
   *理由*：价值最高但**属设计变更**（改 `E_t` 语义、退出码、可能要求用户裁决），必须走阶段关卡，不能塞进实现批次。
   建议**单独一批**：先改 `DESIGN-DETAIL`（新增 DR 条目）+ 明确"固定语义而非开关"（见 N-12），再实现、再独立验收。
6. **HOHL-05 / HOHL-06 / HOHL-07 / HOHL-08**（候选完整性不重试分类、infra vs 候选失败、debug cycle、硬闸门 vs 警告双层）。
   *理由*：全部是"判据细化"，与我们 `DR-27/DR-39/DR-48/DR-55/DR-56` 同族，能直接减少假阴性与无谓重试；成本都很小。
7. **HOHL-11 / HOHL-12 / M-9**（可复现清单、run 级 markdown 摘要）。
   *理由*：D235 明确要求"任何关键决策落文 + 变更可互查"（`R:DECISIONS.md:9199-9203`）；当前 `meta.json` 不足以支撑"为什么这次跑出来是这样"。
8. **HOHL-10 历史级发布闸门**。
   *理由*：C11 目前对"历史"零覆盖；这类闸门一旦漏一次就永久留在历史里。需要先干跑加白名单（我方 `.spec/**`/`runs/**` 含大量路径文本）。
9. **HOHL-13 域策略包 + manifest**。
   *理由*：把已有的 `skills/*.md` **可信化**（有哈希、有边界声明）；顺带满足"注入了什么指导"的审计需求。
10. **HOHL-14 端点/进程身份化清理**。
    *理由*：我们的编辑器是长期打开的（`A4`），误杀代价高；Windows 等价物需一个小 spike。

### P2（等主要风险收口后再做）

11. **HOHL-15 本地资产池**（阶段二真需要时才做；现在做是提前投资）。
12. **HOHL-16 idle 超时**、**HOHL-18 原子写**、**HOHL-19 只读角色字节级还原**、**HOHL-17 单客户端独占断言**。
    *理由*：都是"工程卫生"，单价低但会引入行为变化（尤其 idle 超时可能改变现有 run 的失败形态），建议与真机批次一起验证。

### P3（可做可不做；记录在案以备将来）

13. **HOHL-20 工具清单快照测试组织方式**（我们已有更强的逐字夹具；只借文件组织）。
14. **HOHL-21 issue id 命名规范**、**HOHL-22 机器残留隔离的记录化**。

### 我**明确建议不要**做的

- **任何形式的代码移植**（N-03）或 **MCP 契约/传输的模仿**（N-04/N-05）。
- **引入评分/benchmark adapter**（N-01），即便它的实现看起来"现成"——那会同时违反 C7 与 §2 非目标。
- **把权限外包给外部 CLI 的 sandbox 标志**（N-02）。
- **per-role 换模型 / 换 harness**（N-06）。
- **把它当作"标准答案"逐项对齐**：它的 `usage` 处理（N-07）、prompt 注入方式（N-08）、replay 评分语义（N-09）
  在我们这里都**弱于或冲突于**现有设计。D235 的纪律仍然适用：「**不因"别人这么做"而采纳；不照搬**」。

---

### 附：本报告的核对入口（便于独立复核）

| 结论 | 复核方式 |
|---|---|
| 工具名交集 = 0 | 抽取 `R:godot-mcp\godot\modules\mcp_server\docs\tools_list.renamed.json` 的 177 个 `"name"`；抽取 `H:src/gameloop/_vendor/godot_mcp/server/src/tools/*.ts` 的 `name: '<x>'`（21 个）；求交 |
| 前缀分布 104/48/23/2 | 同上，对 177 个名字取 `_` 前段并计数 |
| 它不是同一血统 | `_vendor/godot-mcp.lock.json:2-8`（upstream/commit/version/license）+ `docs/architecture.md:14-23` + `server.json:41-43` + `server/package.json:2-4` |
| 许可 | 仓根 `LICENSE:1-3`（MIT）、`hoh-lite/LICENSE:1-3`（Apache-2.0）、`hoh-lite/NOTICE:10-14`、`hoh-lite/THIRD_PARTY_NOTICES.md:7-16`、`_vendor/godot_mcp/LICENSE:1-3`（MIT） |
| 证据机制（P0 三条） | `core/mcp_evidence.py`（全文）、`_vendor/godot-mcp-gameloop.patch:5343-5353/5430-5510/6125-6160/6183-6190/5244-5248`、`adapters/gamecraft_bench/local_env.py:31-60` |
| 循环与重试 | `runner.py:2603-2607/2904-2951/3181-3186/3290-3319/3415-3424`；`core/runtime.py:144-163`；`configs/gameloop.example.json` |
