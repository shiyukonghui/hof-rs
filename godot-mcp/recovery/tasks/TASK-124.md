# TASK-124 — 为 NeoHorse-Jev 增加 `--agent=jev` 后端（协议层 + 哑服务验证），并修正 `playtest_agent.py` 的错误文档

> 交接方式：子代理**只读本文件**执行；完成后把报告写到
> `F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-124-REPORT.md`，**返回值只给该路径**。
> 本文件自包含：下面"事实"节里每条协议细节都由 TASK-123 的只读调研从一手来源取得（URL + HTTP 200，
> 原文见该轮会话；关键处已逐字引用）。**不要**依赖会话上下文。

---

## 0. 背景与目标

用户希望"让本地模型试玩游戏，以判定游戏是否真的可玩"。用户指定模型 **NeoHorse-Jev**
（ModelScope `TokenRhythm/NeoHorse-Jev-4B`；源码 `github.com/TokenRhythm/NeoHorse`）。

调研（TASK-123）结论：**Jev 是"结构化决策模型"（prefill-only，非生成式）**，不是聊天模型，
**服务端没有 OpenAI 兼容端点**；我们仓库 `tools/playtest_agent.py` 现在文档里写的
"`vllm.entrypoints.openai.api_server --model <NeoHorse-Jev>`" 与"`llama-server -m NeoHorse-Jev.gguf`"
**对 Jev 都不可能工作**（不是 chat causal LM、无 GGUF、需要外部 `pointer_head.safetensors`、
服务运行在 pooling 模式）。

**本任务目标**：把 Jev 的原生决策协议接进 `tools/playtest_agent.py`（新增 `--agent=jev`），
并用**哑服务**验证协议层正确；同时修正错误文档。**本轮不下载权重、不装 GPU 依赖**
（权重约 9.15 GB，ModelScope 可取、HuggingFace 在本机不可达；Windows 可行性待用户决定）。

---

## 1. 事实（一手来源，逐字）

### 1.1 服务与端点
* 原生运行时：`neohorse-decision serve --model-dir "<MODEL_DIR>" --port 8080`
* 端点（**只有**这三个）：
  * `POST /v1/decision` —— 原生决策 API
  * `POST /v1/systemone` —— 响应含 `model`、`answers`、`usage`
  * `GET /health` —— 就绪状态与 `input_modalities`
* 原文："Only the endpoints and protocol scope described here are supported; **`/v1/models` is not provided**."
* 备选后端（vLLM 0.28.0 pooling 适配器）：`CUDA_VISIBLE_DEVICES=0 python infer/vllm/launch.py --bundle /path/to/model --port 30000`
  （内部用 `--runner pooling --convert embed` + 自定义 chat template + `--limit-mm-per-prompt {"image":1,"video":0}` + `--max-model-len 12288` + `--gpu-memory-utilization 0.4`；
  `infer.py` 打 `/pooling` 拿 token embedding，**决策头在客户端 CPU 上算**）。SGLang 0.5.17 同构。
* **Jev 没有** `/v1/chat/completions`、没有 `choices[].message.content`、不生成文本。

### 1.2 请求形状（typed JSON）
```json
{
  "state": "The left path is clear; the path ahead is blocked.",
  "questions": {
    "move": {
      "type": "choice",
      "instructions": "Choose a clear direction.",
      "criteria": {"left": "Turn left", "forward": "Go forward"}
    }
  }
}
```
* 允许字段**只有** `model`、`state`、`questions`、`image`；未知字段会被拒：
  `unknown = set(request) - {'model','state','questions','image'}` → `ValueError('Unknown request fields: ...')`。
* `model` 只接受 `neohorse-jev` 或 `NeoHorse-Jev-4B`（服务端接受的名字集还有
  `TokenRhythm/NeoHorse-Jev-4B`、`NeoHorse-JEV-4B` 等，响应统一回 `NeoHorse-Jev-4B`）。
* `state` 可以是**字符串 / 对象 / 数组**；运行时 `render()` 会**把字段名当标签**展平
  （`{"k":{"a":1}}` → `k:\n  a: 1`；列表 → `- item` 行）。→ **我们的结构化状态 JSON 可几乎原样传**。
* `image`（可选）：`data:image/png;base64,...` / `data:image/jpeg;base64,...`，或客户端本地路径；
  **不接受外链与服务端路径**；无图时**省略**该字段，**不要传 `null`**。

### 1.3 问题类型与 `criteria` 规则
| 类型 | criteria | 含义 |
|---|---|---|
| `noul` | 可选（只允许 `false`/`true` 两个键） | 判断条件真假；答案 = P(true) ∈ [0,1] |
| `choice` | 候选键→描述字典，**1..255 项** | 从候选中选一个；答案 = argmax + 各候选概率 + confidence |
| `score` | **有序**描述列表（低→高），**2..255 项**（`/v1/systemone` 上限 2–10） | 评级分布 + 期望等级（可为小数） |

### 1.4 响应形状
* `answers.<question_key>`：
  * Choice → `type`、`choice`、`probabilities`、`confidence`
  * Noul → `type`、`noul`（原生 API 另留 yes/no `probabilities`）
  * Score → `type`、`score`、`legend`、`probabilities`、`confidence`
* 顶层：`/v1/decision` → `model`、`answers`、`input_tokens`（有图再加 `image_tokens`）；
  `/v1/systemone` → `model`、`answers`、`usage{input_tokens, output_tokens, image_tokens}`。
* `confidence` **不是校准概率**：
  * Choice：`(max(p) - 1/K) / (1 - 1/K)`
  * Score：`1 - sum_i p_i * abs(i - argmax(p)) / (L - 1)`
* 响应头：`X-NeoHorse-Confidence: local-distribution-statistic-v1`；systemone 另有
  `X-NeoHorse-Usage: local-tokenizer-not-jev-billing`。

### 1.5 限值与错误
* 文本：`state` **2,048 tokens**；每个问题分支 8,192；**每请求最多 16 个问题**；展开后总长
  **32,768 tokens**；请求体 1 MiB。
* 图像：**恰好 1 图 + 1 问题**；请求体 8 MiB；解码后 ≤4 MiB；≤4,194,304 像素；图像 token 1,024；
  整请求 12,288 tokens。
* 超限**直接拒绝，不静默截断**。错误码：`401` 认证、`413` 体积、`422` 非法/不支持、
  `429` 原生决策 worker 忙、`529` systemone worker 忙；**忙时返回 `Retry-After: 1`**。
* 原文："HTTP text and image requests share the same backbone, decision head, and GPU lock,
  **without dynamic batching**."（→ 并发必须串行化）
* 厂商警告："NLL, Brier, and ECE calibration results have not been reported. Set thresholds on an
  independent dataset." 以及 "Multiple questions in one request do not imply a single shared forward pass."

### 1.6 权重与环境（本轮**不下载**，仅供报告引用）
* ModelScope `TokenRhythm/NeoHorse-Jev-4B`：Apache-2.0、无需申请（匿名 files API 可取清单）；
  完整包约 **9.15 GB**（backbone BF16 8.46 GiB = 3 个 safetensors + `pointer_head.safetensors` 5.25 MB
  + tokenizer + `model_manifest.json` + `dist/neohorse_decision-1.0.0-py3-none-any.whl`）；
  **没有 GGUF、没有量化版 Jev**。
* HuggingFace 在本机**不可达**（实测 HTTP 000 / 连接超时）。
* 厂商记录的运行栈是 **Linux**（python 3.12.10、torch 2.8.0、transformers 5.17.0、triton 3.7.1、
  flash-linear-attention 0.5.2、CUDA 12.8、GPU H20）。本机是 **Windows + RTX 4090 24 GB + 128 GiB RAM**
  → **Windows 可行性未验证**，是待用户决定项。
* 模态真相：`model_manifest.json` 写 `"format": "unified multimodal backbone + independent decision
  pointer head; NOT chat causal LM"`、`"vision_source": "Qwen/Qwen3.5-4B"`、**`"vision_finetuning": false`**；
  Image-NLI 60.65%；厂商自己的 image-Doom 结果接近随机（1.00–16.00 mean kills，random 基线 1.00、
  oracle 16.60），而 text-state Doom 为 10.60–14.40。→ **视觉可用但弱，状态文本是强路径。**
* 同门 **NeoHorse-1-4B/9B 才是纯文本 LLM 且有真 OpenAI 兼容端点**（`vllm serve ... --served-model-name neohorse-1-4B`
  → `/v1/chat/completions`），并有 GGUF 量化版；但它们**纯文本**。

### 1.7 我们现有实现的错处（必须修）
`tools/playtest_agent.py` 头部 docstring（约 36–56 行）写着：
* `python -m vllm.entrypoints.openai.api_server --model <path-or-hf-id-of-NeoHorse-Jev> --served-model-name neo-horse-jev`
* `llama-server.exe -m NeoHorse-Jev.gguf`
→ **对 Jev 都不可能工作**（见 §1.1/§1.6）。
`_chat()` 读 `data["choices"][0]["message"]["content"]`；`normalise_action` 期望
`{"type":"key","keycode":<int>,...}`——后者可复用，前者对 Jev 无意义。

---

## 2. 交付物

### A. `tools/playtest_agent.py` 新增 `--agent=jev`
1. **传输**：`POST {base}/v1/systemone`（路径可配，默认 `/v1/systemone`；`--decision-path` 或等价开关可切 `/v1/decision`）；
   `base` 复用 `PLAYTEST_BASE_URL` 语义（作为**根 URL**，不再拼 `/chat/completions`）；
   `PLAYTEST_MODEL` 默认 `NeoHorse-Jev-4B`；支持 `PLAYTEST_API_KEY`（有则加 `Authorization`）；
   就绪检查打 `GET /health`（**不要**打 `/v1/models`）。
2. **请求构造**：
   * `state` ← 我们的**结构化状态**（对象/数组直接传；包含 goal、状态探针、HUD 文本、像素差数字、
     窗口尺寸比对、断言结果等）；
   * `questions`：**动作**用 `choice`（`criteria` = 动作词表，键即动作名，描述写清语义）；
     **可玩性判定**用 `noul`（例如 "Does this frame clearly look playable, with no visual corruption or freeze?"）
     与/或 `score`（例如 "How broken is this frame?" + 2–10 个有序等级）；
   * **文本请求**：允许一次带多个问题（≤16），默认一次带"动作 + 2~3 个不变量 + 1 个 score"；
   * **图像请求**：**只能 1 图 + 1 问题**——实现必须**显式限制并在超限时给出清晰错误**，
     不要把多问题请求悄悄发成图请求。
3. **响应映射**：
   * `answers.<动作键>.choice` → 复用 `normalise_action`/`keycode_of` 得到现有动作字典；
   * `answers.<noul 键>.noul` → 浮点 P(true)；`answers.<score 键>.score` → 期望等级；
   * **把 probabilities / confidence / usage / image_tokens 全部记进 agent 输出证据**（门要用）。
4. **限值与错误**：
   * `state` 的 2,048 token 上限：**主动检测并给出明确错误或显式裁剪（须在证据里声明裁掉了什么）**，
     **绝不静默截断**；实现一个保守的 token 估算（说明依据）；
   * `429`/`529`：按 `Retry-After`（默认 1s）退避重试，次数可配、有上限；
   * `413`/`422`/`401`：映射成明确错误信息；
   * **未配置 `PLAYTEST_BASE_URL` 或服务不通**：安全降级为 `wait` 动作并记录原因（**不得静默成功**）；
   * 并发：串行化（服务无动态批处理），实现里显式串行。
5. **不要破坏现有后端**：`scripted` / `openai` 行为保持不变（`openai` 后端保留给"真 OpenAI 兼容"的模型）。

### B. 修正文档
把 §1.7 指出的两行错误命令替换为**两条正确路径**（逐字采用 §1.1 的命令，并注明来源）：
* `--agent=openai` ← 只适用于真 OpenAI 兼容模型（例：NeoHorse-1-4B/9B，纯文本）；
* `--agent=jev` ← 原生 `neohorse-decision serve`（`/health`、`/v1/decision`、`/v1/systemone`）或 vLLM pooling 适配器。
并注明：**Jev 无 GGUF**、**HuggingFace 在本机不可达**、**Windows 可行性未验证**。

### C. 阈值与判据接线
* 把 `noul` 的 P(true) 与 `score` 期望等级接进可玩性门的**可配置阈值**（默认值须标注"仅先验、**未校准**"，
  并引用厂商的 NLL/Brier/ECE 警告）；
* 在报告里写明**如何用我们自己的正负样本标定阈值**：修好版 20 款（正）与
  `dist/exe-task109-pre-fix` 之前的修复前版本（负，输入被关）构成天然标签集。

### D. 哑服务验证（**本轮的核心证据**）
在 `tools/tests/` 下写一个**本地 HTTP 哑服务**（stdlib 即可，不装依赖），至少覆盖：
1. `/health` 就绪 → agent 判定可连；
2. `/v1/systemone` 返回固定 `answers`（choice + noul + score 各一）→ **请求形状与响应解析正确**；
3. 返回 `429` + `Retry-After: 1` → **退避重试生效**（记录尝试次数）；
4. 返回 `422` → **错误被明确上报**；
5. 请求体里**含未知字段/超长 state** → 自检证明我们的构造器**不会**发出非法请求（或发出后按预期报错）；
6. 未配置 base URL / 端口无人监听 → **安全降级为 wait 并记录**。
把哑服务运行日志与 agent 侧证据存到 `runs/playability/agent-probe-jev.json`（或同目录等价物），
**并给出可重跑命令**（本文档要求：命令必须能被别人照着复现）。

---

## 3. 硬性约束（铁律）

1. **禁止一切 shell 重定向**（`>`、`>>`、`*>`、`2>&1`）；写文件用 `-OutFile` 或 Python/编辑工具。
2. **破坏性命令默认拒绝**：非空、绝对路径、白名单前缀、先打印清单；含通配符或 `..` 直接抛错。
3. 运行与构建**从 cmd 启动**（避免 PowerShell 5.1 的中文/编码坑）。
4. **唯一端口 + 跑前查进程与端口**；用 5xxxx 高位端口做哑服务，避开 9877（用户编辑器）/9888/9889。
5. **不得改动用户机器的安全设置**（不关 SAC、不改注册表）。
6. **不得联网下载模型权重**（本轮明确不做）；不 `pip install` GPU 依赖。
7. 若改了 `godot/modules/mcp_server/`（本任务**预期不需要**），则必须重建两变体 + 十道门全绿 +
   `accept_m1 22/22` + push 引擎 fork；**未改引擎就要在报告里明确写"未触发"及依据**。
8. 中文写入若遇乱码，用 `cmd`/`bash` 终端或 Python（UTF-8）落盘。

---

## 4. 验收判据（报告必须逐条给出证据）

| 编号 | 判据 | 证据要求 |
|---|---|---|
| J1 | `--agent=jev` 存在且可运行 | `--help` 输出含 `jev`；`scripted`/`openai` 未回归 |
| J2 | 请求形状正确 | 哑服务侧打印收到的 JSON；与 §1.2 逐字段对照（字段名、类型、`questions` 结构） |
| J3 | 响应解析正确 | choice→动作字典；noul→浮点；score→期望等级；probabilities/confidence/usage 进证据 |
| J4 | 限值处理 | 超长 state 与"图请求多问题"两条路径都被拒并给出清晰错误（非静默） |
| J5 | 错误与退避 | `429` 按 `Retry-After` 重试（记录次数）、`422` 明确报错、未配置时降级为 wait 并记录 |
| J6 | 文档已修正 | `playtest_agent.py` 头部不再出现那两条错误命令；新命令逐字可用且标了来源 |
| J7 | 阈值接线 | 门侧有可配置阈值 + "未校准"标注 + 自己的正负样本标定方案 |
| J8 | 可复现 | 哑服务验证的命令行逐条可重跑（报告里给出） |
| J9 | 铁律遵守 | 报告里明写：无重定向、无破坏性命令、端口检查、未联网下载、引擎是否改动 |

---

## 5. 报告落点与返回值

* 报告：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-124-REPORT.md`
  （含：实现要点、请求/响应逐字段对照、哑服务验证逐条结果与命令、文档修正前后、阈值方案、J1–J9 逐条证据、
  本次未做/待用户决定项、两仓 `git log --oneline -5` 与 `git status --short`）。
* 主仓提交（提交信息引用本任务号）。
* **返回值只给报告路径**（外加一行状态），不要贴长摘要。
