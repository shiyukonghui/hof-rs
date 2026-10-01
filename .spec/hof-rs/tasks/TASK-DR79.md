# TASK-DR79 — **不重跑**：以追加式勘误更正 T13 报告的三处机制论断与计数，并修四项管线卫生缺陷

> 你是**实现子代理**，无上游对话上下文；**本文件是唯一任务来源**。
> **规格即验收报告**：`.spec/hof-rs/tasks/TASK-SMOKE-T13-ACCEPTANCE.md`（**`verdict=fail`**，`T13A-1..9` 全在此，含**逐条复现命令**）
> ——**请逐条按它的 `reproduction` 字段自行复现后再改**。另读 `.spec/hof-rs/tasks/TASK-SMOKE-T13-REPORT.md`、`DECISIONS.md` **D289 / D293**。

## 0. 两条铁律

1. **不重跑真机轮、不起引擎、不联网**。本批只做**文档更正 + 管线卫生修复**。
2. **改动必须是追加式**（依据 `DECISIONS.md` **D289**）：对**历史报告**的更正**只能追加**（新章节/尾部），**不得改写原文、不得改动其机器可读块与证据字符串**；**原文逐字保留并标注 `superseded`/`incorrect`**。
   **`runs/**` 一律只读**（含 `runs/smoke-t13/**` 与其分析产物）⇒ 更正只落 `.spec/**` 与代码。

## 1. 更正 `TASK-SMOKE-T13-REPORT.md`（追加一节「DR-79 勘误」，逐条给出被更正的原句与正确读数）

- **① T13A-1（major，核心叙述错误）**：本轮**最初**的 `start_round_game` **成功**并发布了 **`http://127.0.0.1:53068/mcp`**——作者自己在 **04:19:22** 对 `:53068` POST 过 `tools/list` 与 `running_game_get_scene_tree`（`evidence/round/game_endpoint_*_round_author.json`），Developer 在 04:44:02 读到 `[MCP] role=game configured_port=53068`（`developer.attempt2.json` msg 77）；**`warnings.log` 那条 DR-70 是 ~04:41 追加的（非 04:17:44）**，那时唯一可能失败的是**修复期重启**（`run_loop.rs:1348`），其应答 `:55361`。
  ⇒ **更正**：删去/撤回"最初开局即失败"的叙述；**把"逐轮翻转的不变量"与"承诺与行为在整个窗口不一致"的风险陈述收窄**为实际发生的事；并把 §3.3(d) 的拒绝时间 **04:31:28 更正为 04:51:28**。
- **② T13A-2（major）**：**64 KiB 截断路径实际触发过一次**：`tester.attempt1.json` msg 98（04:56:37）`extra.hoh_output_truncated=true`、`limit 65536`、`original 81139`，运行时标记文本 `[hoh: 65536 of 81139 bytes were carried…]`。
  ⇒ **更正**"0 次/untriggered"，并**登记为"该路径的首个真机证据"**（这是一条**新获得的正面事实**）。
- **③ T13A-3（medium）**：`artifact_valid` 松弛点的**真实归因**是 **DR-70 门修复块在 `run_loop.rs:1378` 用 `artifact_valid: workspace.is_dir()`（恒真）**；被引用的 `1137/1185` 属**未触发**的 wrap-up 块。
  ⇒ **更正归因**（结论"标志太松"仍成立，但理由更强、不同）。
- **④ T13A-4/6/7/8（minor/info）**：逐条更正**计数与作用域**（verified/gap 记录数、记录类型漏 `screenshot:2`、文件/脚本/分析计数、`cite_check.txt` 行号、`warnings.log` 行数），并把 T13A-8 那条 0.85 推断**改为直接观测**（Developer 在 43 s 前直接看到 "no route file"，`attempt2` msg 135）。
- **⑤ T13A-5（minor）**：**非密钥环境值泄漏**（`DSH_TERM_CMD`，含仓外暂存路径与 `model.secret.env` 文件名）出现在 `planner.attempt1.json`、`developer.attempt1.json` 及其脱敏副本 ⇒ **必须在报告里如实登记**（密钥值本身 0 泄漏）。
- **⑥ T13A-9**：三个 `.tmp_*.json`（108/68/46 B）由 Developer 写在**仓库根**、`out_of_tree_writes` 检出但**未阻止** ⇒ 登记。

## 2. 管线卫生修复（四项，各自 TDD）

1. **越界写入**：`out_of_tree_writes` **检出但未阻止/未清理** ⇒ 让其**有界可控**（例如轮末清理轮内产生的、位于仓库根的已知临时模式，并**在记录里留痕**；**不得**用 `rm -rf`，**不得**从未展开的变量构造路径）。
2. **usage 双计**：`src/runtime/usage.rs:130` 的过滤把 DR-72 的**脱敏旁路副本** `<role>.attempt1.redacted.json` 也计入 ⇒ **修过滤（排除 `.redacted.`）**，并加**回归钉**：有旁路副本时 planner ratio 必须为 1.0（当前必红）。
3. **`artifact_valid` 恒真**：`run_loop.rs:1378` 的 `workspace.is_dir()` ⇒ 改为**有意义的检查**（或明确记录"修复重试不复评"的**意图**并加测试钉住该语义）。
4. **命令行走漏**：冻结证据中不应含 harness 命令行 ⇒ **把 `DSH_TERM_CMD` 一类纳入脱敏**（同 DR-72 家族），并加测试：合成一条含 `model.secret.env` 路径的命令行 ⇒ 被脱敏（当前必红）。

## 3. 硬约束与门

- **不得重跑真机轮**；**`runs/**` 零写入**；不改 `PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`、任何既有 `.workspace/**`；不加新依赖。
- **禁止手工写游戏**；**绝不对任何路径用 `rm -rf`**；**绝不用 PowerShell 的 `Get-Content -Raw`+`Set-Content`**；**绝不整文件重写行尾**。
- **闸门已武装**：T13 的提交**尚无通过验收**（本轮验收为 fail）⇒ **推送会被拒绝，这正是设计**；**不要尝试推送**。
- 门：`cargo test --offline` **exit 0**；**基线以本批开工前 HEAD 的真实数为准**（请自行复现算术）；`ignored` 不增长；**无测试名被删**（被要求的改名除外）；`cargo fmt --check` exit 0；**逐文件** touch `git ls-files '*.rs'`（禁通配符）；先清 `target/debug/.fingerprint/hof-rs-*`。
- **≥3 处受控植入**，各自使对应测试红，逐字节回退（`status`/`diff`/`hash-object`/`cmp`）；**机器可读块必须序列化后落盘并真的回读**。

## 4. 完成后回报（**只回报报告文件路径**）

报告：`.spec/hof-rs/tasks/TASK-DR79-REPORT.md`。必含：
1. **勘误清单**（逐条：被更正的原句 → 正确读数 → 证据文件与复现命令 → 原文是否仍原样保留并标注）；
2. 四项卫生修复的**先红→绿**证据（含回归钉与植入）；
3. 门读数与**禁区自查**（`runs/**` 未动、工作区未动、PRD/引擎/Cargo 未动、未推送、仓内无新增临时物）；
4. **遗留风险与未验证项**；5. 诚实披露。