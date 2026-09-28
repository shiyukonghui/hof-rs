# TASK-DR47-ACCEPT — 批次二（真机 T=1 冒烟）独立验收任务书

> 你是**独立验收子代理**。你不是执行者，**不得**继承执行者或调度者的结论。
> 你只看：需求、设计、`runs/smoke-t6/**` 的**原始工件**、以及**你自己亲手复现**的证据。
> 落点：`F:\moonbit-hof-rs`。执行者报告：`.spec/hof-rs/tasks/TASK-DR47-SMOKE-REPORT.md`（**线索，非证据**）。
>
> **真机前提**：编辑器（我们的 mono 构建）仍在 9877 上运行，PID **108432**。
> **绝不**杀/重启/抢占它；**不得**占用其它端口（除经 `editor_play_scene` 自身路径）。

---

## 1. 先读

| 顺序 | 路径 | 读什么 |
|---|---|---|
| 1 | `.spec/hof-rs/tasks/TASK-DR47-SMOKE.md` + `-ADDENDUM.md` | 执行者收到的判据（addendum 取代其 §2 第 3 点） |
| 2 | `.spec/hof-rs/tasks/TASK-DR47-SMOKE-REPORT.md` | 执行者自述（含 E1..E6、6 条缺陷、§9 端点核对） |
| 3 | `.spec/hof-rs/REQUIREMENTS.md` §6（E1..E6）、§3（C3/C4/C5） | 判据原文 |
| 4 | `.spec/hof-rs/DESIGN-DETAIL.md` §13 | DR-43/DR-44/DR-47 的设计意图 |
| 5 | `DECISIONS.md` 末两条 **D219**、**D220** | D219 的端点等式（**已知有错，见 D220**）与 D220 的裁决 |

---

## 2. 你要独立复核的核心事实（**逐条自己复现**）

### 2.1 退出码与规模
- `runs/smoke-t6/exit_code` 的真实值（应为 `6`）。
- `runs/smoke-t6/iter-1/result.json` 的三角色 tokens 与 `attempts`；
  核对"四次尝试全部 `LimitsExceeded`"是否属实。
- 自己合计 tokens 是否 ≈ **26.8M**。

### 2.2 引擎身份（DR-44 活体验收）
- `runs/smoke-t6/meta.json` 的 `engine` 块：`binary.path` 是否**恰为**
  `F:/moonbit-hof-rs/godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe`；
  自己重算该文件的 **sha256** 与 `size_bytes` 是否与落盘一致；
  `listener.pid` 是否为 **108432**、`listener.matches_binary` 是否为 `true`；
  用**你自己的**探针核对 9877 的监听者 PID 与可执行体路径。
- `version_string` 是否以 `4.8.dev.mono` 开头（**自己**跑一次 `<binary> --version`，只读）。
- **DEF-D 的复核（重要）**：`engine.mcp.game_endpoint == null` 且其 `reason` 声称
  "游戏端点在本轮不存在"——但你应能从 `result.json`/trajectory 找到本轮**确实创建过**游戏端点
  （端口 65333 / 63698，pid 109964 / 101872）。**若 reason 与事实矛盾 ⇒ 缺陷成立**，并按严重度评。
  同时核对 `engine.mcp.editor_status == null` 是否也不该为空（本轮 `GET /mcp` 可读）。

### 2.3 DEF-A（**本批头号缺陷，直接决定 E2**）
- 从 `result.json.artifact_gate.reasons` 取出原文，确认"唯一错误"是引擎的
  `[MCP] capture=off (default; use --mcp-capture=on_error|every_call …)`。
- **验证它是信息行而非脚本错误**：同一轮里 `play_scene_ready` 与 `running_game_get_scene_tree` 是否
  真的成功（去 `battery_passes`、`raw/**`、trajectory 里找）。若成功 ⇒ "不可启动"是**假阴性**。
- **给出根因的可检验表述**：该串被判错是否**只因为**它含子串 `error`（来自 `on_error`）？
  请给出你的证据与置信度；若无法从仓库内证实（引擎源码只读、`godot-mcp/**` 不可改），
  **明确写"未能证实到源码级"**，不要把推断写成实测。
- **修复方向必须可逆且窄**：hof-rs 只应忽略**引擎自身 `[MCP]` 前缀 INFO 行**；
  你只需在报告里指出"修复时如何避免把真错误一起放过"，**不要**自己改代码。

### 2.4 DEF-B（假证据，必须自己抓一遍）
- 从 `battery.json` / `deterministic.json` / `raw/**` 找出 `running_game_capture_screenshot`
  三次 `-32602` 的**原文**（`save_path` 必须以 `res://` 或 `user://` 开头）。
- 核对那张 PNG 的**真实 mtime 与 sha256**：若它确实是 **2026-09-21** 的旧文件，
  而该步骤仍被记 `ok=true` 且描述为"截图已写入" ⇒ **假证据成立**。
- 明确写出：这是 **hof-rs 的调用形态**不匹配（传了文件系统路径），还是引擎契约要求的形态；
  二者都要给出文件/行号或响应原文依据。

### 2.5 DEF-C（E3 的根因，两轮可复现）
- 找出两轮游戏端点的**真实端口与 pid**（65333/109964、63698/101872），
  以及挂死（`os 10060`）与死亡（`os 10061`）的**原始响应**。
- 判断"游戏进程是否在两次调用之间退出"（可用 `running_game_*` 的失败码序列、
  `editor_play_scene` 响应里的 pid、以及后续 `GET /mcp` 探测该端口是否连接被拒来论证）。
- **不得**自己再起游戏进程；若需要活体复现，**只能**经一次真实的 `editor_play_scene`
  （它会占用编辑器与端口）——这是**允许但不鼓励**的重演，若你做了，必须在报告中说明并清理。

### 2.6 E1..E6 逐条
- 独立核对执行者的 met/not_met 判定，**特别**：
  - **E1**：`A0 version_id == A1 version_id` 是否属实（去 `versions/index.json` 与
    `meta.json.start_state`）；`D_1`、`E_1` 是否真的合法（schema 层面自己看原件）。
  - **E5**：**自己重实现一次 `hash_tree`**（或等价算法），对 workspace / `candidate` /
    `versions/<hash>` 三棵树求值，确认是否都为 `fc78d299…`，且 17 个文件逐字节同。
  - **E4**：抽 3 条 verified claim，查其 `execution_records` 是否**真实存在**且绑定同一
    `candidate_id`；抽 2 条 gap 确认无证据。
  - **E6**：执行者称构造了 2 个反例；**你要独立构造至少 1 个新反例**，
    并判断 QA 的偏差方向是否真的一律保守（有无把 gap 当 verified、或把失败说成成功）。

### 2.7 端点分区（D219 等式**已知有错**，见 D220）
- 复核执行者的实测分区 **104 / 50 / 23**（E=154、G=73、E∩G=50、E∪G=177）是否自洽：
  用 `runs/smoke-t6/**` 里两轮 `tools/list`（编辑器与游戏端点）的**原始响应**做集合运算。
- 明确写出：**D219 的 108/46/23 是错的**（新增 6 条实为 2 editor-only + 4 共享），
  并确认"并集 = 177 且准入门两条硬判据通过 ⇒ 非合约漂移"。

---

## 3. 纪律与禁项

1. **只读**：不改 `src/**`、`tests/**`、`config/**`、`godot-mcp/**`、`.spec/hof-rs/PRD-mario.md`；
   **不** `git commit`/`push`/stage；**不**改 `runs/smoke-t6/**`（那是原始证据）。
2. **不启动 Godot**、不碰 9877 的监听者、不占其它端口（§2.5 的例外须显式声明并清理）。
3. 不联网（除配置里的模型端点**不需要**你调用——**不要**调模型）。
4. 密钥：**不得**出现在任何输出／报告里（只可打印长度）。
5. `PRD-mario.md` sha256 必须仍为 `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a`。
6. **不**假设 `runs/smoke-t1..t5` 与 `smoke-t6` 可比（前者是旧契约时代）。

---

## 4. 结构化结论（写进报告 §1，并且必须返回）

```json
{
  "verdict": "pass" | "fail",
  "criteria": [ { "id": "E1|E2|E3|E4|E5|E6|DR44.identity|D219.partition|DEF-A|DEF-B|DEF-C|DEF-D",
                  "pass": true, "evidence": "命令/文件:行 + 真实输出片段" } ],
  "defects": [ { "id": "DEF-A", "confirmed": true, "severity": "major",
                 "correction": "执行者的结论是否正确/需如何改写" } ],
  "risks": [ "…" ],
  "unverified": [ "…" ]
}
```

- 对 6 条缺陷逐条给 **confirmed / refuted / partial** 与你的独立依据。
- 任何拿不到证据的，写进 `unverified`，**不得**默认成立。
- `verdict=fail` 的门槛：执行者把 not_met 报成 met、或伪造证据、或动了原始工件、
  或 6 条缺陷中有你认为**不成立**的（错告）——错告同样要指出。

---

## 5. 报告落点与必含小节

写到 `.spec/hof-rs/tasks/TASK-DR47-ACCEPTANCE.md`：

1. 结构化结论（§4 的 JSON）+ 真实命令与退出码；
2. 逐条核对表（§2.1–§2.7，每条：命令 → 原始输出 → 判定）；
3. 反例清单（你构造了什么、观测到什么、是否推翻）；
4. 对 6 条缺陷的 confirmed/refuted/partial 与严重度意见；
5. 未验证项与理由；
6. 你没有独立复核的部分（诚实列账）；
7. 对**修复批**的建议清单（按优先级；**不要**自己改代码）。

**回报给父代理只有一行：报告文件路径。**
