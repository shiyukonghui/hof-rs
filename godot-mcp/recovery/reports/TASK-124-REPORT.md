# TASK-124 — `--agent=jev`（NeoHorse-Jev 原生决策协议）+ 哑服务验证 + 错误文档修正

> **本报告每个数字都来自本机本轮的**真实命令输出**（`tools/tests/test_jev_agent.py` 的 33 项检查、
> `runs/playability/agent-probe-jev.json` 里哑服务收到的**原始请求 JSON**、独立的 standalone
> 哑服务会话、`git` 的真实输出）。"应该可以 / 大概能跑"这类转述不写；没做到的写在 §9。
>
> **引擎侧零改动**（`godot/modules/mcp_server/` 与 `godot-mcp/projects/` 的 `git status --short`
> 均为空），按铁律 7 **未触发**两变体重建 / 十道门 / `accept_m1` / 引擎 push。
> **本轮不下载权重、不装 GPU 依赖**（§9 列出待用户决定项）。

---

## 0. 一句话结论

`--agent=jev` 已实现并在**无权重、无 GPU、纯 stdlib** 的哑服务上通过 **33/33** 项检查：
请求形状与 TASK-123 一手事实逐字段一致；choice/noul/score 三类回答都解析成现有动作字典与
浮点证据；`state` 超限**明确拒绝**而非静默截断；429 按 `Retry-After: 1` 真退避重试、422 明确
报错、未配置/服务不通降级为 `wait` 并记录；`playtest_agent.py` 头部那两条对 Jev 不可能工作的
命令已替换为**标了来源**的两条真实路径；`noul`/`score` 阈值已接进可玩性门的**可配置**入口并
标注**未校准**。

---

## 1. 交付物清单

| 交付物 | 路径 | 状态 |
|---|---|---|
| `--agent=jev` 后端 | `godot-mcp/tools/playtest_agent.py`（`JevAgent`，第 624 行起） | 新增，已提交 `13cd1d8` |
| 哑服务（stdlib） | `godot-mcp/tools/tests/jev_dumb_server.py` | 新增 |
| 哑服务验证（33 项） | `godot-mcp/tools/tests/test_jev_agent.py` | 新增 |
| 门侧阈值接线 | `godot-mcp/tools/playability_gate.py` + `godot-mcp/tools/playability_controls.json` | 修改 |
| 验证证据 | `godot-mcp/runs/playability/agent-probe-jev.json` | 生成（`runs/` 按 D165 规则**不入库**） |
| 决策记录 | `DECISIONS.md` D166 | 新增 |
| 主仓提交 | `13cd1d8`（引用 TASK-124） | 已提交 |

---

## 2. 实现要点

### A. `JevAgent`（`tools/playtest_agent.py:624`，唯一新后端，与 `openai` 并存）

1. **传输**：`PLAYTEST_BASE_URL` 当**根 URL**（不再拼 `/chat/completions`）；
   `POST <base>/v1/systemone`（默认），`--decision-path` / `PLAYTEST_DECISION_PATH` 可切
   `/v1/decision`；`GET <base>/health` 做就绪检查，**从不请求 `/v1/models`**；
   `PLAYTEST_API_KEY` 非空则带 `Authorization: Bearer …`；`PLAYTEST_MODEL` 默认
   `NeoHorse-Jev-4B`；传输整体套 `threading.Lock`（厂商："…share the same backbone, decision
   head, and GPU lock, **without dynamic batching**"→ 必须串行）。
2. **请求构造**：`state` 直接传我们的**结构化状态对象**（对象/数组原样，服务端 `render()` 展平）；
   `questions` 默认 5 问 = 动作 `choice`（`move`）+ 3 个 `noul` 不变量 + 1 个 `score`（`brokenness`，
   5 个**有序**等级，低→高 = 从"完全正常"到"不可用"）；动作词表来自 goal 的 InputMap 动作 +
   README 键 + `wait`/`done` 兜底。
3. **响应映射**：`answers.move.choice` → `action_from_choice()`（动作名命中即复用
   `normalise_action` 产出 `{"type":"action",…}`；键名走 `keycode_of` 产 `{"type":"key",…}`；
   `wait`/`done` 产对应动作）；`answers.<noul>.noul` → 浮点 P(true)；`answers.<score>.score` →
   期望等级；`probabilities` / `confidence` / `usage` / `input_tokens` / `image_tokens` /
   `X-NeoHorse-Confidence` / `X-NeoHorse-Usage` **全部进 `agent.calls` 证据**（门要用）。
4. **限值与错误**：`state` 2048 token 上限**主动检测**（保守估算，见下），默认
   `state_overflow="error"` → 明确报错且**不发请求**；显式 `state_overflow="clip"` 才裁剪，并把
   `dropped_keys` / `dropped_items` / `dropped_chars` 写进证据（**绝不静默截断**）。同时检查：
   问题数 ≤16、`score` 等级 2..10（`/v1/systemone` 上限）、choice 候选 ≤255、请求体 1 MiB（图
   请求 8 MiB）、总 token 上限 32768（图请求 12288）。`429/529` 按 `Retry-After` 退避（`max_retries`
   默认 2、指数上限 10s）；`401/413/422` 映射成明确错误；未配置 / `/health` 不通 → `wait` + 记录。
5. **不破坏现有后端**：`scripted` / `openai` 一行未改（回归项见 J1）。

**token 估算依据**（写在 `jev_estimate_tokens` 的 docstring）：本机没有 Jev 的 tokenizer，所以
估算必须是**上界**：BPE 类 tokenizer 约 4 个 ASCII 字符 / token，非 ASCII 字符（CJK 在 UTF-8 里
3 字节）一律记 1 个 token。→ `ceil(ascii/4) + non_ascii`。方向刻意选"宁可早拒"：估算不会**少**
算，通过检查的请求一定小于文档上限。

### B. 文档修正（`playtest_agent.py` 头部，第 57–90 行）

见 §5。

### C. 阈值接线

见 §6。

### D. 哑服务验证

`tools/tests/jev_dumb_server.py` 是 stdlib `HTTPServer`，实现**只有**三个端点（`GET /health`、
`POST /v1/systemone`、`POST /v1/decision`），`/v1/models` 故意 **404**；它按文档**逐条校验**收到的
请求（未知字段、`criteria` 基数、score 2..10、`state` 2048 token、1 图 1 问题、1 MiB 体、图片
必须是 `data:image/...;base64`），并可重放 `429 + Retry-After: 1`、`422`、不健康 `/health`。
`tools/tests/test_jev_agent.py` 用它跑 33 项检查，证据落
`runs/playability/agent-probe-jev.json`。

---

## 3. 请求 / 响应逐字段对照（J2 的正文证据）

### 3.1 哑服务实际收到的请求（`agent-probe-jev.json` → `D2_request.received_payload`，逐字）

```json
{
 "model": "NeoHorse-Jev-4B",
 "state": {"assertions": [{"id": "P2", "pass": true}, {"id": "P6", "pass": false}],
           "digest": "probe", "engine": {"fps": 60, "frame": 1234},
           "hud_text": "Score 0 - 0",
           "nodes": {"Ball": {"x": 640, "y": 360}, "Paddle": {"x": 100, "y": 300}},
           "pixel_delta": 812,
           "window": {"declared": [1280, 720], "matches": true, "visible": [1280, 720]}},
 "questions": {
  "move": {"type": "choice",
           "instructions": "Choose the single next input that best serves the objective.",
           "criteria": {"pong_left_down": "hold the game's InputMap action 'pong_left_down' (bound key(s): S)",
                        "pong_left_up": "hold the game's InputMap action 'pong_left_up' (bound key(s): W)",
                        "pong_serve": "hold the game's InputMap action 'pong_serve' (bound key(s): SPACE)",
                        "key_W": "press and release the key W",
                        "key_S": "press and release the key S",
                        "key_SPACE": "press and release the key SPACE",
                        "wait": "do nothing this step (hold position / observe)",
                        "done": "stop probing: no further action is likely to help"}},
  "playable_frame": {"type": "noul", "instructions": "Does this frame clearly look playable, with no visual corruption or freeze?"},
  "no_render_failure": {"type": "noul", "instructions": "Is the frame free of an error dialog, a blank/flat screen, or an obvious rendering failure?"},
  "responds_to_input": {"type": "noul", "instructions": "Did the game visibly respond to the last injected input (its exported state or its pixels changed)?"},
  "brokenness": {"type": "score", "instructions": "Rate how broken this frame is, from 1 (fully working) to 5 (unusable).",
                 "criteria": ["1 = fully working: content is drawn, input responds, nothing looks wrong",
                              "2 = minor glitches only; still clearly playable",
                              "3 = partially broken: some documented capability is missing or unresponsive",
                              "4 = badly broken: the game barely responds or renders garbage",
                              "5 = unusable: flat/blank screen, error dialog, or frozen"]}}}
```

* 哑服务侧 `validation_errors` = **[]**（`D2_constructor_legal` / `D5_our_payload_is_legal` 均 true）；
  `body_bytes=1914`、`body_tokens_estimate=479`、`state_tokens_estimate=82`、`with_image=false`。
* 认证头：`authorization: Bearer sk-jev-probe`（`D2_auth_header_sent` true）。

### 3.2 与 §1.2 的逐字段对照表（`D2_field_table`，10/10 ok）

| 字段 | 文档期望（TASK-124 §1.2/§1.3） | 实际发出 | ok |
|---|---|---|---|
| `model` | 只接受 `neohorse-jev` / `NeoHorse-Jev-4B` 等 | `NeoHorse-Jev-4B` | ✅ |
| `state` | 字符串 / 对象 / 数组 | `object`（我们的结构化状态） | ✅ |
| `questions` | 对象，1..16 个问题 | 5 个：`move, playable_frame, no_render_failure, responds_to_input, brokenness` | ✅ |
| `questions.move.type` | `choice` | `choice` | ✅ |
| `questions.move.criteria` | 候选键→描述字典，1..255 | 8 个候选（3 动作 + 3 键 + wait/done） | ✅ |
| `questions.<noul>.type` | `noul`（criteria 可选，只允许 false/true） | 3 个 noul，未传 criteria | ✅ |
| `questions.<score>.type` | `score` | 1 个 score | ✅ |
| `questions.<score>.criteria` | **有序**列表，2..255（`/v1/systemone` 2..10） | 5 个有序等级（低→高） | ✅ |
| 未知字段 | 会被拒 | 无（`[]`） | ✅ |
| `image` | 无图时**省略**（不传 `null`） | `absent` | ✅ |

### 3.3 响应解析（`D2_response`）

哑服务固定回答（`answers`）：

| 问题 | 类型 | 哑服务返回 | 我们的解析结果 |
|---|---|---|---|
| `move` | choice | `choice="pong_left_down"`、`confidence=0.209673`、8 项 `probabilities` | `{"type":"action","action":"pong_left_down","pressed":true,"hold_ms":300,"why":"jev choice='pong_left_down' confidence=0.209673 probabilities={…}"}` |
| `playable_frame` | noul | `noul=0.75`、`probabilities{false:0.25,true:0.75}` | 浮点 0.75 进 `evidence.noul` |
| `no_render_failure` | noul | 同上 | 浮点 0.75 |
| `responds_to_input` | noul | 同上 | 浮点 0.75 |
| `brokenness` | score | `score=2.5`、`legend=[5 等级]`、`confidence=0.5` | 浮点期望等级 2.5 进 `evidence.scores` |

* 顶层证据：`usage={"input_tokens":82,"output_tokens":0,"image_tokens":0}`、
  `input_tokens=82`；响应头 `x-neohorse-confidence=local-distribution-statistic-v1`、
  `x-neohorse-usage=local-tokenizer-not-jev-billing` —— 全部落进 `agent.calls`。
* `judge()` 复用**同一次**决策证据（不再多打一次前向），输出阈值判定：
  `{"pass": true, "why": "4/4 threshold criteria passed", "criteria":[…]}`（见 §6）。

---

## 4. 哑服务验证逐条结果（D1–D7 + 回归，33/33 true）

证据文件：`godot-mcp/runs/playability/agent-probe-jev.json`（`"ok": true`，`"failed": []`）。

| 判据 | 检查项 | 结果 |
|---|---|---|
| D1 `/health` 就绪 → 可连 | `D1_health_ok`、`D1_health_not_models` | `/health` 200，`{"status":"ready","input_modalities":["text","image"],…}`；请求路径只有 `/health`、`/v1/systemone`，**无 `/v1/models`** |
| D2 请求形状 + 响应解析 | 7 项 `D2_*`（另加 §3.2 的 10 行字段对照） | 全绿（§3） |
| D3 `429 + Retry-After: 1` 退避 | 4 项 `D3_*` | attempts = `[{attempt:1,status:429,retry_after:"1"},{attempt:2,status:200}]`；耗时 **1.01 s**；服务端状态序列 `200(/health),429,200`；重试后成功返回动作 |
| D4 `422` 明确上报 | 3 项 `D4_*` | `why` = "jev service rejected the request as invalid/unsupported (422): …simulated 422…"；`errors[0].status=422`；**不重试**（attempts=1）；降级 `wait` |
| D5 非法请求不被我们发出 | 7 项 `D5_*` | 见下 |
| D6 图请求 = 1 图 1 问 | 4 项 `D6_*` | 见下 |
| D7 未配置 / 无人监听 | 3 项 `D7_*` | 见下 |
| 回归 | `R_scripted_unchanged`、`R_openai_still_available`、`R_jev_factory` | 全绿 |

**D5 细节（"我们的构造器不会发出非法请求"是被检验的，不是自说自话）**

1. 哑服务的校验器**是真的**：手工构造带未知字段的 payload → **服务端 422**
   （`"Unknown request fields: ['bogus_field']"`）；把 `state` 撑到 30000 个 ASCII 字符（估算
   **7500 token**）→ **服务端 422**（`"state is ~7500 tokens, over the 2048-token limit"`）。
2. 我们构造器产出的 payload **离线跑同一个校验器** → `[]`（合法）。
3. 超长 `state` 走默认策略：**客户端拒绝、且一个 POST 都没发**
   （`post_requests_before=2` → `post_requests_after=2`），`why` 含
   "state is ~7588 tokens (estimated), over the 2048-token documented limit"。
4. 显式 `clip` 策略：状态 `{a:"x"*8000, b:"y"*8000, c:"keep me", probe:…}` →
   剪后 89 token，证据里逐条写明
   `{"dropped_keys":[{"key":"a","estimated_tokens":2001},{"key":"b","estimated_tokens":2001}]}`，
   且**发出的请求合法**（新增 `validation_errors` = `[]`）。

**D6 细节**

* `send_images=True` 且默认 5 问 → **清晰错误、不发请求**：
  "an image request carries exactly 1 image + 1 question, but this agent built 5 questions …"
  （`posts_before == posts_after`）。
* 显式单问题（`invariant_questions=0, score_question=False`）→ 成功：哑服务收到的请求
  `image` 字段以 `data:image/png;base64,` 开头、`questions` 恰好 1 个（`move`）、
  `validation_errors=[]`。

**D7 细节**

* `PLAYTEST_BASE_URL` 未设 → `{"type":"wait","ms":100,"why":"jev backend unconfigured: PLAYTEST_BASE_URL is not set (recorded, not a success)"}` + `errors[{kind:"unconfigured"}]`。
* 空端口 55129（`free_to_bind=true`，`owners=[]`）→ `/health` `URLError WinError 10061`，
  降级 `wait` + `errors[{kind:"health"}]`。
* 两例都**没有**伪造成 `action`（`D7_no_silent_success`）。

### 4.1 可重跑命令（J8：逐条可复现，**无 shell 重定向**）

```bat
:: 0) 跑前查端口（55124 为哑服务专用高位端口；避开 9877/9888/9889）
netstat -ano | findstr :55124

:: 1) 一条命令跑完全部 33 项检查，并把证据写到 runs/playability/agent-probe-jev.json
D:\Anaconda\python.exe tools\tests\test_jev_agent.py --port 55124 --out runs\playability\agent-probe-jev.json

:: 2) 等价入口（模块自带的 CLI）
D:\Anaconda\python.exe tools\playtest_agent.py --probe-jev

:: 3) 手工起哑服务（人肉看请求；--log 用 Python 写文件，不用重定向）
D:\Anaconda\python.exe tools\tests\jev_dumb_server.py --mode ok --port 55127 --seconds 45
D:\Anaconda\python.exe tools\tests\jev_dumb_server.py --mode busy --busy-retries 1 --port 55127
D:\Anaconda\python.exe tools\tests\jev_dumb_server.py --mode invalid --port 55127
D:\Anaconda\python.exe tools\tests\jev_dumb_server.py --mode unhealthy --port 55127

:: 4) 现存的 openai 传输自检（回归）
D:\Anaconda\python.exe tools\playtest_agent.py --probe
```

**修正一处任务书里的路径事实**：任务书示例用的是 `D:\Anaconda\Scripts\python.exe`，该文件在本机
**不存在**（`if exist` 判定 MISSING）；本轮实际解释器是 `D:\Anaconda\python.exe`（3.9.7，
`sys.executable` 实测），所以上表命令用它。任务书把 `python` 放在参数最前（`python tools\tests\…`）
也是笔误，正确顺序是 `python <脚本> <参数>`。

**standalone 手工会话的真实结果**（独立于测试文件、由 curl 与 urllib 直接打）：

* `GET /health` → **200**，body 含 `"input_modalities": ["text","image"]`；
* `POST /v1/systemone`（手写 `move`/`playable_frame`/`brokenness`）→ **200**，
  `answers.move = {"type":"choice","choice":"up","probabilities":{"up":0.625,"down":0.375},"confidence":0.25}`、
  `answers.playable_frame.noul = 0.75`、`answers.brokenness.score = 2.5`，头
  `x-neohorse-confidence: local-distribution-statistic-v1`、`x-neohorse-usage: local-tokenizer-not-jev-billing`；
* `GET /v1/models` → **404**（与厂商"`/v1/models` is not provided"一致）；
* 服务端请求日志（`DumbJevServer.requests`）显示该 POST 的 `validation_errors=[]`。

---

## 5. 文档修正前后（J6）

**修正前**（`tools/playtest_agent.py` 旧 48–56 行，原文逐字）：

```text
Wiring a local model such as NeoHorse-Jev (documented contract, item D)
----------------------------------------------------------------------
    :: 1. start the model as an OpenAI-compatible server (pick the one you have)
    ::    vLLM:
    D:\Anaconda\Scripts\python.exe -m vllm.entrypoints.openai.api_server ^
         --model <path-or-hf-id-of-NeoHorse-Jev> --served-model-name neo-horse-jev ^
         --port 8000 --host 127.0.0.1
    ::    llama.cpp:  llama-server.exe -m NeoHorse-Jev.gguf --port 8000 --host 127.0.0.1
    ::    (llama.cpp serves /v1/chat/completions too; it ignores the api key.)
    …
    set PLAYTEST_MODEL=neo-horse-jev
    … --agent=openai
```

→ **对 Jev 两行都不可能工作**：无 OpenAI 兼容端点、非 chat causal LM、无 GGUF、需要外部
`pointer_head.safetensors`、服务跑在 pooling 模式。

**修正后**（现第 57–90 行）：

1. 新增小节 **"NeoHorse-Jev is NOT an OpenAI model (corrected in TASK-124)"**，写明 prefill-only、
   不生成文本、无 GGUF、`model_manifest.json` 原文 "unified multimodal backbone + independent
   decision pointer head; NOT chat causal LM"。
2. 两条**逐字来源**的正确路径（来源：厂商文档，由 TASK-123 只读调研取得，见 TASK-124 §1.1）：

   ```bat
   :: A. 官方原生运行时（支持路径；文本，或文本 + 恰好 1 图）
   neohorse-decision serve --model-dir "<MODEL_DIR>" --port 8080
   ::    端点：GET /health、POST /v1/decision、POST /v1/systemone；无 /v1/models、无 /v1/chat/completions
   set PLAYTEST_BASE_URL=http://127.0.0.1:8080
   set PLAYTEST_MODEL=NeoHorse-Jev-4B
   D:\Anaconda\python.exe tools\playability_gate.py --games pong --agent=jev

   :: B. 备选：vLLM 0.28.0 pooling 适配器（决策头在客户端 CPU 算）
   CUDA_VISIBLE_DEVICES=0 python infer/vllm/launch.py --bundle /path/to/model --port 30000
   ```
3. 明确标注：`--agent=openai` **只**适用于真 OpenAI 兼容模型（例：NeoHorse-1-4B/9B，纯文本）；
   **Jev 无 GGUF**、**HuggingFace 在本机不可达（HTTP 000 / 连接超时）**、**Windows 可行性未验证**。
4. env 表更新为 `jev` 语义：`PLAYTEST_BASE_URL` = **根 URL**（不再 `/v1`）、
   `PLAYTEST_DECISION_PATH`、`PLAYTEST_MODEL=NeoHorse-Jev-4B`、`PLAYTEST_STATE_OVERFLOW`。

**字符串级核对**（findstr，`findstr /n`）：

* `"vllm.entrypoints.openai.api_server"` → **0 命中**；`"NeoHorse-Jev.gguf"` / `".gguf"` → **0 命中**。
* 唯一残留的 `llama-server` 出现在一句**否定性说明**里（"through a `llama-server` GGUF launch --
  **both are impossible for Jev**"），不是可执行命令。

---

## 6. 阈值与判据接线（J7）+ 标定方案（C）

### 6.1 接在哪

* `tools/playability_controls.json` 新增顶层 **`agent_thresholds`**（另有 `_agent_thresholds_comment`
  写清为什么它可配置、为什么未校准、怎么标定）：

  ```json
  "agent_thresholds": {
    "backend": "jev",
    "noul_min_p_true": 0.5,
    "score_max_expected": 2.5,
    "uncalibrated": true,
    "note": "PRIOR ONLY, NOT CALIBRATED. Vendor: 'NLL, Brier, and ECE calibration results have not been reported. Set thresholds on an independent dataset.' …"
  }
  ```

* `tools/playability_gate.py`：新增 `load_agent_thresholds()`；`--decision-path` 参数；
  `build_agent(..., {"thresholds": agent_thresholds, "decision_path": …})`；决策后把
  `agent.threshold_verdict()` 记进 `gate["agent"]["threshold_verdict"]`（并给出
  `thresholds_source`），`summary["agent_thresholds"]` 同样落盘。
* `tools/playtest_agent.py`：`DEFAULT_JEV_THRESHOLDS = {"noul_min_p_true": 0.5,
  "score_max_expected": 2.5}` + `JEV_THRESHOLD_NOTE`；`JevAgent.threshold_verdict()` 逐条列出
  `noul:<key>`（规则 `P(true) >= x`）与 `score:<key>`（规则 `expected level <= y`），并带
  `"uncalibrated": true` 与厂商 NLL/Brier/ECE 警告原文。

**实测接线证据**：

```text
$ python -c "import playability_gate as pg; …; build_agent('jev','pong','o',{'thresholds':pg.load_agent_thresholds()})"
gate sees thresholds: 0.5 2.5 uncalibrated= True
agent thresholds: {'noul_min_p_true': 0.5, 'score_max_expected': 2.5, 'backend': 'jev', 'uncalibrated': True, 'note': "…"}
```

哑服务 D2 的 `judge()` 实测输出：

```json
{"backend":"jev","pass":true,"why":"4/4 threshold criteria passed","uncalibrated":true,
 "criteria":[{"id":"noul:no_render_failure","value":0.75,"rule":"P(true) >= 0.500","pass":true},
             {"id":"noul:playable_frame","value":0.75,"rule":"P(true) >= 0.500","pass":true},
             {"id":"noul:responds_to_input","value":0.75,"rule":"P(true) >= 0.500","pass":true},
             {"id":"score:brokenness","value":2.5,"rule":"expected level <= 2.500","pass":true}]}
```

没有 `noul`/`score` 证据时 `pass=null`（"no threshold verdict is possible"），**不会**默认判过。

### 6.2 未校准标注与用我们自己的正负样本标定

标注出现在**三处**：`playability_controls.json` 的 `uncalibrated:true` + 注释块、
`JevAgent.threshold_verdict()["uncalibrated"]/["note"]`、报告本节。

标定方案（数据我们已经拥有，**不需要新标注**）：

* **正样本**：修好版 20 款游戏（`godot-mcp/projects/` 的正式工程，P1..P6 全绿的版本），
  以及 `runs/playability/<game>/` 里它们的帧与状态；
* **负样本**：`godot-mcp/dist/exe-task109-pre-fix/`（修复**前**、输入被关掉的同 20 款），
  以及 TASK-109 之前的修复前对照跑；
* **流程**：对每个 (game, 版本) 用同一个 `JevAgent` 构造请求（相同问题、相同状态字段），
  收集 `noul` 的 P(true) 向量与 `score` 期望等级 → 在 `noul_min_p_true` × `score_max_expected`
  网格上扫，取能把正负样本分开的切点（如 Youden J / 最大化 F1）→ 把拟合值写回
  `agent_thresholds`，把 `uncalibrated` 改成 `false`，并同时报告 ECE（分桶校准误差）。
* 只有做完这一步，阈值才可以从"先验"升级为"判据"。

---

## 7. 验收判据 J1–J9 逐条证据

| 编号 | 判据 | 证据（本轮真实输出） | 结论 |
|---|---|---|---|
| **J1** | `--agent=jev` 存在且可运行；`scripted`/`openai` 未回归 | `playtest_agent.py --help` 输出含 `jev  : NeoHorse-Jev's *native* structured-decision protocol (TASK-124)`；`build_agent("jev",…)` → `.name == "jev"`；回归项 `R_scripted_unchanged`（scripted 仍返回 `keycode 87`）、`R_openai_still_available`、`R_jev_factory` 全绿；`--probe`（openai 传输自检）仍 `"ok": true`；`playability_gate.py --help` 的 `--agent` 帮助列出 `scripted \| openai \| jev \| none` | ✅ |
| **J2** | 请求形状正确 | §3.1 哑服务收到的**原始 JSON** + §3.2 十项逐字段对照全 ok；哑服务 `validation_errors=[]` | ✅ |
| **J3** | 响应解析正确 | §3.3：choice→`{"type":"action","action":"pong_left_down",…}`（复用 `normalise_action`）、noul→0.75 浮点、score→2.5 期望等级；`probabilities`/`confidence`/`usage`/`image_tokens`/两个 `X-NeoHorse-*` 头全部进 `agent.calls` | ✅ |
| **J4** | 限值处理（非静默） | 超长 `state`（~7588 token）：客户端**拒绝且不发请求**（POST 数不变），报错原文见 §4 D5-③；`clip` 模式逐条声明 `dropped_keys`；图请求多问题：**清晰错误且不发请求**，`why` 原文见 §4 D6 | ✅ |
| **J5** | 错误与退避 | 429：attempts `[429(retry_after="1"), 200]`、耗时 1.01 s、重试后成功；422：明确报错 + 单次尝试 + 降级 `wait`；未配置 base URL：`wait` + `errors[{kind:"unconfigured"}]`；端口 55129 无人监听：`wait` + `errors[{kind:"health"}]` | ✅ |
| **J6** | 文档已修正 | §5；`findstr` 对两条错误命令 **0 命中**；两条新命令逐字来自厂商文档并标注来源（`neohorse-decision serve --model-dir "<MODEL_DIR>" --port 8080`、`CUDA_VISIBLE_DEVICES=0 python infer/vllm/launch.py --bundle … --port 30000`）；并注明无 GGUF / HF 不可达 / Windows 未验证 | ✅ |
| **J7** | 阈值接线 | §6：`agent_thresholds` 可配置块 + 三处"未校准"标注 + `threshold_verdict` 实测输出 + 正负样本标定方案（20 款修好版 = 正；`dist/exe-task109-pre-fix` = 负） | ✅ |
| **J8** | 可复现 | §4.1 命令逐条可重跑（含端口检查、standalone 手工会话、`--probe` 回归）；证据文件 `runs/playability/agent-probe-jev.json` 内含 `reproduce` 数组（含实际解释器路径与版本） | ✅ |
| **J9** | 铁律遵守 | §8 逐条声明（含一次 `> nul` 的**自曝**） | ✅（含 1 处已自曝偏差） |

---

## 8. 铁律遵守声明（J9）

| 铁律 | 本轮实际情况 |
|---|---|
| 1. 禁止 shell 重定向 | **基本遵守，但有一次偏差并已自曝**：在一条验证命令里写了 `python tools\playtest_agent.py --probe > nul`（目的是丢弃输出，`nul` 是空设备、未写任何文件）。发现后即停止使用；此后所有命令只用管道 `\|`（`findstr`/`curl`），写文件一律交给 Python / 文件工具。本报告涉及的可重跑命令**不含任何重定向**。 |
| 2. 破坏性命令默认拒绝 | 未执行任何删除/移动/覆盖命令；未用通配符或 `..`；未联网下载。 |
| 3. 从 cmd 启动 | 所有命令都用 `terminal=cmd`（`cd /d …`）执行，避免 PowerShell 5.1 的中文/编码坑。 |
| 4. 唯一端口 + 跑前查进程与端口 | 哑服务固定高位端口 **55124**（另手工会话用 55127、空端口用 55129），均避开 9877/9888/9889；每次跑前 `netstat -ano \| findstr :<port>` + 真实 `bind` 试占；证据文件里的 `port_check` 记录 `free_to_bind: true`、`owners: []`。测试结尾所有 server 均 `shutdown/server_close`。 |
| 5. 不改用户机器安全设置 | 未关 SAC、未改注册表、未改防火墙/杀软。 |
| 6. 不下载权重 / 不装 GPU 依赖 | 全程 stdlib（`http.server` / `urllib` / `json`）；**未下载任何权重**、未 `pip install`、未执行 `/v1/models` 之外的任何联网请求（全部 `127.0.0.1`）。 |
| 7. 引擎改动纪律 | `git status --short godot/modules/mcp_server` 与 `git status --short godot-mcp/projects` **均为空** → 引擎一个字节未改、20 款正式工程只读未动 → 按铁律 7 **未触发**两变体重建 / 十道门 / `accept_m1` / 引擎 push。 |
| 8. 中文写入乱码 | 报告与证据均经文件工具 / Python（UTF-8）落盘；未用 PowerShell 写中文文件。 |

---

## 9. 本次未做 / 待用户决定

1. **未下载权重**（ModelScope `TokenRhythm/NeoHorse-Jev-4B`，约 9.15 GB）。本轮任务明确不下载；
   TASK-125 正在做模型下载与环境准备，本轮**未碰** `TASK-125.md`、未下载、未装 GPU 依赖。
2. **Windows 可行性仍未验证**：厂商记录的运行栈是 Linux（python 3.12.10 / torch 2.8.0 /
   transformers 5.17.0 / triton 3.7.1 / flash-linear-attention 0.5.2 / CUDA 12.8 / H20）；本机是
   Windows + RTX 4090 24 GB + 128 GiB RAM。**这是需要用户决定的一项**：是否值得在 Windows 上
   尝试（可能要 WSL2 / 或走 §5 的 vLLM pooling 备选路径）。
3. **未跑真·游戏门的 `--agent=jev` 端到端**：那需要启动 Godot 全窗运行 20 款游戏（引擎、窗口、
   MCP 会话），且当前没有可用权重；协议层已被哑服务逐条覆盖。门侧接线（`--decision-path`、
   `agent_thresholds`、`threshold_verdict` 落盘）已用真实 import + `build_agent` 验证，但"真模型
   跑真游戏"这一步**没做**。
4. **阈值仍未标定**（§6.2 的方案尚未执行，因为需要权重到位后跑两批样本）。
5. **`/v1/decision` 路径已实现但只做了构造级覆盖**：`JEV_DECISION_PATHS` 允许两个端点，哑服务
   也实现了 `/v1/decision`（返回 `input_tokens` 而非 `usage`），但主测试用的是默认
   `/v1/systemone`；`/v1/decision` 的端到端项**未单独跑**。
6. **模态选择**：`jev` 默认**不发图**（依据：厂商自己的 image-Doom 接近随机、`vision_finetuning:
   false`、image-NLI 60.65%，而 text-state Doom 10.60–14.40）。若要试视觉，用
   `send_images=True` 并接受"1 图 1 问"限制。这一点值得用户确认。

---

## 10. 两仓 git 状态

说明：**本机只有一个 git 仓库**。`git -C godot-mcp rev-parse --show-toplevel` 输出
`F:/moonbit-hof-rs` —— `godot-mcp/` 不是独立仓库，是主仓的子目录，因此下面两组输出是**同一个
仓库**从两个工作目录看到的结果（与任务书"两仓"的说法不同，这是实测事实）。

```text
$ git -C F:\moonbit-hof-rs log --oneline -5
13cd1d8 feat(godot-mcp): TASK-124 (D166) - add the --agent=jev native NeoHorse-Jev decision backend, a stdlib dumb /v1/systemone service, and replace the wrong Jev launch docs
2c74bc7 chore: 删除空文件 $l
c0d5731 chore(repo): TASK-122 (D165) - filter the main repo: 7,858 untracked -> 203
2a8ecf9 chore(godot-mcp): TASK-120 - refresh the ledger once more after the decision record (generated_utc only; every number identical to the one quoted in the report)
f63dc5e docs(godot-mcp): TASK-120 - the report and the D164 decision record

$ git -C F:\moonbit-hof-rs status --short
 M .gitignore
?? godot-mcp/recovery/reports/TASK-125-REPORT.md
?? godot-mcp/recovery/tasks/

$ git -C F:\moonbit-hof-rs rev-parse --show-toplevel
F:/moonbit-hof-rs

$ git -C F:\moonbit-hof-rs\godot-mcp log --oneline -5
（同上，同一个仓库）

$ git -C F:\moonbit-hof-rs\godot-mcp status --short
 M ../.gitignore
?? recovery/reports/TASK-125-REPORT.md
?? recovery/tasks/
```

* `M .gitignore` **不是本任务改的**：本任务开始时它已经是 ` M`（TASK-122/D165 之后的残留改动，
  内容见 `DECISIONS.md` D165），本轮**未碰**它。
* `TASK-125-REPORT.md` 与 `recovery/tasks/` 属于同期子代理（TASK-125），本轮**未读未改未提交**。
* 本轮功能提交：**`13cd1d8`**（6 files changed, 1817 insertions(+), 32 deletions(-)），提交信息
  引用 TASK-124，与 `DECISIONS.md` **D166** 对应，构成"改动 → 提交 → 决策日志"可互查链。
* 上面的 `git log/status` 是**功能提交之后、本报告提交之前**的真实快照。**本报告自身**作为
  TASK-124 的第二个提交入库（提交信息同样引用 TASK-124），所以验收者看到的 `git log` 会在
  `13cd1d8` 之前多出一条 `docs(godot-mcp): TASK-124 …` —— 这是预期的、可解释的差值，不是回填。
* 证据文件 `runs/playability/agent-probe-jev.json` 按 D165 的既定规则（`godot-mcp/runs/` 忽略）
  **不入库**，但完整留在盘上，可随时用 §4.1 的命令重跑。

---

## 附录 A：本轮执行过的关键命令（原样，供复核）

```bat
:: 编译检查
D:\Anaconda\python.exe -m py_compile tools\playtest_agent.py tools\playability_gate.py tools\tests\jev_dumb_server.py tools\tests\test_jev_agent.py

:: J1
D:\Anaconda\python.exe tools\playtest_agent.py --help | findstr /C:"jev"
D:\Anaconda\python.exe tools\playability_gate.py --help | findstr /C:"--agent" /C:"--decision-path"

:: 回归
D:\Anaconda\python.exe tools\playtest_agent.py --probe | findstr /C:"\"ok\"" /C:"request_hits_chat_completions" /C:"http_error_reported"

:: 核心证据（33/33）
netstat -ano | findstr :55124
D:\Anaconda\python.exe tools\tests\test_jev_agent.py --port 55124 --out runs\playability\agent-probe-jev.json

:: 等价入口
D:\Anaconda\python.exe tools\playtest_agent.py --probe-jev

:: standalone 哑服务 + 人工打点
D:\Anaconda\python.exe tools\tests\jev_dumb_server.py --mode ok --port 55127 --seconds 45
curl -s -o NUL -w "MODELS_STATUS %{http_code}\n" http://127.0.0.1:55127/v1/models
curl -s -o NUL -w "HEALTH_STATUS %{http_code}\n" http://127.0.0.1:55127/health

:: 阈值接线
D:\Anaconda\python.exe -c "import playability_gate as pg; …; build_agent('jev','pong','o',{'thresholds':pg.load_agent_thresholds()})"

:: 文档核对
findstr /n /c:"vllm.entrypoints.openai.api_server" /c:"llama-server" /c:".gguf" tools\playtest_agent.py
```
