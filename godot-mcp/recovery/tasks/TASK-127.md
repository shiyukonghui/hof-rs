# TASK-127 — 部署 PlayJev（视觉判定后端）：定位/校验权重 → 本地部署 → 最小适配器 → 本地端到端实测

> 子代理**只读本文件**执行；完成后报告写到
> `F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-127-REPORT.md`，**返回值只给该路径 + 一行状态**。
> 自包含。**用户已决定：主攻 PlayJev；视觉一律本地部署，截图不出本机——禁止调用任何第三方端点。**

---

## 0. 背景（已核实事实）

* 我们的试玩门需要"**从截图判定画面是否可用**"的能力。已部署的 **NeoHorse-Jev-4B** 是**文本状态强、视觉弱**
  （`vision_finetuning: false`、Image-NLI 60.65%、厂商 image-Doom 接近随机），且**图像请求硬限制 1 图 1 问**。
* TASK-126 调研发现 **`OmniJev/PlayJev`（0.8B）** 才是"做了视觉微调"的那个：
  * 官方原文 "**full fine-tuning of the 0.8B base**"（视觉塔确证参与训练）；
  * 自带 **`playjev/serve.py`**，暴露 **`POST /v1/systemone` + `GET /health`**（与我们已实现的 `--agent=jev` **同协议**）；
  * 厂商记录推理约 **3 GB**、**43 ms / H200**；公开 demo 端点在 1 张图 + 3 个问题（choice/noul/score）下返回
    逐问概率 + `abstain` + confidence；
  * 与 Jev 的差异点（适配器估计 ~100–150 行）：**`state.frames` 而非 `state`+`image`**、**图像路径强制 `choice`**、**`abstain` 容错**。
    ⚠️ 这几条来自二手摘要，**必须以仓库里 `serve.py` 的真实代码为准**（见 §2.3）。
* 备选（**本轮不做，仅登记**）：`tinnel123666888/OmniJev`（v1.1，4 个 tar.gz + SHA256SUMS，但**无 HTTP 服务**、
  视觉微调不可核验、LICENSE 写 Qwen3-VL-4B-Instruct 而 README 写 Qwen3.5-4B 自相矛盾）。
* 网络现实（TASK-125/126 实测）：**Windows 侧 GitHub 可达、HuggingFace 不可达（HTTP 000）**；
  **WSL 内 GitHub 不可达**（需镜像）。→ **GitHub 产物先在 Windows 侧取，再拷进 WSL**。
* 已部署且**正在运行**的 Jev 服务（**不要碰**）：WSL2 Ubuntu 26.04、venv `/opt/jev-venv`（Py 3.12.13）、
  服务 `0.0.0.0:8080`、`/health` → `{"status":"ready","model":"NeoHorse-Jev-4B","input_modalities":["text","image"]}`、
  权重在 `F:\models\NeoHorse-Jev-4B`、日志 `runs/playability/jev-serve-detached-*.log`、**占显存约 13.3 GB**。

---

## 1. 目标

1. **定位并核实 PlayJev 的源码、权重与许可**（拿不到就如实报告"不可达/需镜像"，不要编）。
2. **本地部署**：在 WSL2 内用**独立 venv**（`/opt/playjev-venv`，**不要动 `/opt/jev-venv`**）、
   **独立端口（默认 8081）**起服务，`GET /health` 就绪。
3. **最小适配器**：让我们的 agent 能用它，支持**一张图 + 多个问题**（choice/noul/score），
   并把 probabilities / abstain / confidence **全进证据**。
4. **本地端到端实测**：用**我们自己游戏的真实截图**在**本地服务**上跑通并留证（**不调用任何第三方端点**）。

---

## 2. 步骤与要求

### 2.1 定位（Windows 侧做网络请求）
* 用 `web_search` + `curl.exe -sSL --ssl-no-revoke`（**must**: `--ssl-no-revoke`，否则本机 TLS 失败）查：
  * GitHub 组织/仓库：`OmniJev/PlayJev`（也要试 `OmniJev`、`playjev`、`TokenRhythm` 之外的别名）；
  * `https://api.github.com/repos/<org>/<repo>`、`/releases`、`/contents/`、raw `README.md`；
  * ModelScope（本机可达）：搜 `PlayJev`；HuggingFace **只记状态码**（预期 000），**不重试超过 3 次**。
* **记录每条 URL 的 HTTP 状态码与字节数**。

### 2.2 权重与许可
* 明确：**权重在哪**（GitHub Release / HF / ModelScope）、**逐文件大小与总量**、**是否有 SHA256SUMS**、
  **许可与基座许可**（0.8B 基座是谁、能否本地商用/研究用；把 LICENSE 原文关键句抄下来）。
* **若权重只在 HuggingFace**：**停下**，报告"本机两侧都不可达，需要镜像或代理"，并列出候选镜像方案。**不要**硬试。

### 2.3 部署（WSL2，独立环境与端口）
* 独立 venv：`/opt/playjev-venv`（Python 3.12；若 WSL 里已有 3.12 安装路径可复用，**不要**重建 Jev 的 venv）。
* 依赖按仓库 `requirements.txt`/README 的实际要求装；若与 Jev 环境冲突，**宁可另建 venv 也不要动 `/opt/jev-venv`**。
* 起服务：优先仓库自带 `playjev/serve.py`；**端口 8081**（先查端口占用）；用 `setsid`/`nohup` detached，
  日志落 `runs/playability/playjev-serve-*.log`（`runs/` 不入库）。
* 就绪判据：`GET /health` 可读（记录原文）。**同时确认 8080 上的 Jev 服务仍活着**（别把它搞挂）。

### 2.4 先读代码，再写适配器（**顺序不可颠倒**）
* **逐字读出** `playjev/serve.py`（及相关 schema/engine 文件）里的：请求字段名与嵌套结构、
  图像传法（base64 data URL？frames 数组？路径？）、问题类型与 `criteria` 规则、
  返回结构（含 `abstain` 的确切语义）、限值与错误码、是否支持"1 图多问"。
  把这些**抄进报告**（带文件路径与行号），并**与我们 JevAgent 的假设逐条对照，列出差异**。
* 适配器实现（`tools/playtest_agent.py`）：
  * 新增 `--agent=playjev`（或给 `JevAgent` 加 `--protocol=playjev` 等价开关；**不要破坏 `jev`/`openai`/`scripted`**）；
  * 请求构造/响应映射按 §2.4 的真实代码写；**支持一张图 + N 个问题**；
  * `abstain` 必须**显式处理**（例如 abstain=true 时降级为"不可判定"并记录，**不得**当成功）；
  * probabilities / abstain / confidence / usage 全进证据；串行化（单 GPU）；
  * 配置沿用 `PLAYTEST_BASE_URL` / `PLAYTEST_MODEL`（默认端口 8081）。

### 2.5 本地端到端实测（核心证据）
* 素材：**我们自己的游戏截图**（从 `runs/playability/<game>/frames/*.png` 或 `runs/playability-exe/**` 取；
  需要"画面正常"与"画面异常（黑屏/冻结/控件缺失）"各若干张，**说明每张的来源与它代表什么**）。
* 每次请求：**1 张图 + 3 个问题**（一个 `choice` 动作、一个 `noul` 可玩性、一个 `score` 损坏度）→ 断言 HTTP 200、
  解析成功、概率与 abstain 落库；把请求与响应**逐字**存到 `runs/playability/playjev-probe.json`。
* **必须**在报告里给出**可重跑命令**（逐条），并声明：**全程本地，无第三方端点**。

---

## 3. 硬性约束（铁律）

1. **禁止一切 shell 重定向**（`>`、`>>`、`*>`、`2>&1`、`> nul`）；用 `-o` / `-OutFile` / Python 落盘。
2. **破坏性命令默认拒绝**（`Remove-Item -Recurse`、通配符、`..`）。
3. 命令尽量**从 cmd 启动**；中文写盘乱码用 cmd/bash 或 Python UTF-8。
4. **不得**改机器安全设置；**不得**启用 Windows 功能/重启；**不得**杀用户进程或其他会话的服务。
5. **不要碰** `/opt/jev-venv`、8080 端口上的 Jev 服务、`F:\models\NeoHorse-Jev-4B` 的权重文件。
6. **禁止调用任何第三方端点做图像推理**（`api1.omnijev.net` 这类一律不用）；只用本机服务。
7. 权重与 venv **不得入库**；`git add` 只允许加你自己改的**源码/文档**（并在提交信息里引用本任务号）。
8. 大文件下载**必须可续传**，用后台 job，并周期性报告进度。

---

## 4. 验收判据（报告逐条给证据）

| 编号 | 判据 |
|---|---|
| P1 | PlayJev 源码与**权重来源**已定位（URL + 状态码）；权重清单逐文件大小 |
| P2 | 许可与基座已核实（LICENSE 关键句原文） |
| P3 | 权重已下载并**逐文件 SHA256 对表**（若有 SHA256SUMS；没有就说明如何核验） |
| P4 | WSL2 独立 venv `/opt/playjev-venv` 装好（`pip freeze` 关键行），**未动 `/opt/jev-venv`** |
| P5 | 服务在**8081** 就绪（`/health` 原文），且 **8080 的 Jev 仍存活**（同时给出证据） |
| P6 | `serve.py` 的真实请求/响应形状**被逐字抄录**（文件+行号），并列出与 JevAgent 假设的差异 |
| P7 | 适配器实现，且 `jev`/`openai`/`scripted` **未回归**（给 `--help` 与自测输出） |
| P8 | **1 图 + 3 问**本地实测 200（请求/响应逐字落盘 + 可重跑命令） |
| P9 | `abstain` 被显式处理（构造一次 abstain 或说明为何构造不出） |
| P10 | 明写：**无第三方端点**、无重定向、无破坏性命令、未改安全设置；两仓 `git log --oneline -5` 与 `status` |

---

## 5. 报告落点与返回值

* 报告：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-127-REPORT.md`
  （含：定位过程与状态码、权重与许可、部署记录、**serve.py 真实协议摘录**、适配器改动、
  本地实测证据与可重跑命令、P1–P10 逐条证据、遗留与待决项）。
* **返回值只给报告路径 + 一行状态**。若权重不可达：**如实报告并停下**，不要编造。
