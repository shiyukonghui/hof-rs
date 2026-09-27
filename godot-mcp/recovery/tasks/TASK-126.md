# TASK-126 — 调研备选模型 `OmniJev`（视觉微调版类 Jev 模型），并与 NeoHorse-Jev 做选型对比

> 交接方式：子代理**只读本文件**执行；完成后把报告写到
> `F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-126-REPORT.md`，**返回值只给该路径**。
> 本文件自包含。**本任务是只读调研：不下权重、不装依赖、不改仓库代码。**
> 同期另有子代理在做 TASK-124（jev 后端协议层）与 TASK-125（NeoHorse-Jev 权重下载 + 环境）——
> **不要动** `tools/playtest_agent.py`、`recovery/tasks/TASK-124.md`、`recovery/tasks/TASK-125.md`。

---

## 0. 背景与目标

我们的试玩门需要一个**能从截图判定"游戏是否真的可玩"**的模型（用户诉求原话：
"当前在游戏验证反馈这块功能缺失无法保证游戏是可用运行的"）。

已调研的 **NeoHorse-Jev-4B**（TASK-123）结论要点：
* 它是 **4B 结构化决策模型**（prefill-only、非生成式、不是 chat LM），服务只给
  `/v1/decision`、`/v1/systemone`、`/health`，**没有 OpenAI 兼容端点**、**没有 GGUF**；
* **多模态但视觉未微调**：`model_manifest.json` 里 **`"vision_finetuning": false`**，
  视觉编码器是原版 Qwen3.5-4B；Image-NLI 60.65%，厂商自己的 **image-Doom 接近随机**
  （1.00–16.00 mean kills，random 1.00 / oracle 16.60），而 **text-state Doom 10.60–14.40**；
* 图像请求**只能 1 张图 + 1 个问题**（文本请求可一次 ≤16 问）。

用户新发现一个**做了视觉能力微调**的类 Jev 模型，要求**加入备选并调研**：

> `https://github.com/tinnel123666888/OmniJev`

**目标**：把 OmniJev 的"是什么 / 权重在哪 / 怎么起服务 / 接口形状 / 视觉能力证据 / 硬件与平台"
查清楚，并**给出选型建议**：它能否替代或补充 NeoHorse-Jev 成为我们试玩门的视觉判定后端。

---

## 1. 方法（只读探测；逐条记录 URL 与 HTTP 状态码）

1. 先 `web_search` 找资料（模型卡、公告、第三方评测）。
2. 再**直接拉原始文本**（本机实测：`curl.exe` 必须加 `--ssl-no-revoke`，否则 schannel 吊销检查会导致
   TLS 失败退出 35 / HTTP 000）：
   * `https://api.github.com/repos/tinnel123666888/OmniJev`（拿默认分支、描述、license、stars、更新时间）
   * `https://api.github.com/repos/tinnel123666888/OmniJev/contents/`（列文件树）
   * `https://raw.githubusercontent.com/tinnel123666888/OmniJev/<默认分支>/README.md`（以及 `/master/`、`/main/`）
   * `https://api.github.com/repos/tinnel123666888/OmniJev/releases`（看有没有权重 Release）
   * 若 README 指向 HuggingFace / ModelScope 仓库：**ModelScope 本机可达**（HTTP 200），
     **HuggingFace 本机不可达**（实测 HTTP 000 / 21s 超时）→ HF 只记录"存在与路径"，
     **不要**长时间重试；ModelScope 可进一步拉 `repo/files?Revision=master&Recursive=true` 拿**逐文件字节清单**。
3. 用 `Invoke-WebRequest`/`curl -o` 落盘到 `%TEMP%`；**禁止 shell 重定向**。
4. 只读！**不** `pip install`、**不**下权重、**不** `git clone` 大仓库（真要 clone 就 `--depth 1` 且先看体积）。

---

## 2. 必须回答的问题（一条都不许漏；拿不到就写 `unverifiable`）

| 编号 | 问题 |
|---|---|
| Q1 | **可达性**：仓库/raw README/releases/关联模型页在本机能否访问（逐条给 HTTP 状态码与字节数） |
| Q2 | **它是什么**：与 NeoHorse-Jev 的关系（同门？复刻？微调？独立实现？）；基座模型与参数量；作者与发布时间；许可 |
| Q3 | **视觉是否真微调**：有没有**可核原文**（模型卡字段、训练说明、`vision_finetuning` 之类标志、视觉塔是否被训练/替换）；与 NeoHorse-Jev 的 `vision_finetuning: false` 对比 |
| Q4 | **视觉能力证据**：任何**基准数字或 demo**（Image-NLI、游戏截图任务、消融表）；**区分官方自述与第三方**；有没有"图 + 多问题"支持 |
| Q5 | **权重**：在哪（GitHub Releases / HF / ModelScope）、**逐文件大小**、总量、是否需要授权/token、是否只有 BF16 或也有量化/GGUF |
| Q6 | **起服务的确切命令**：vLLM / SGLang / transformers / llama.cpp / 自带 server；**逐字抄**并注明出处；是否 OpenAI 兼容（`/v1/chat/completions`）还是 Jev 式原生决策协议（`/v1/decision`、`/v1/systemone`、`/health`） |
| Q7 | **接口形状**：输入（prompt 模板？图像字段名与格式？一次几张图？最多几个问题？）与输出（自由文本？JSON？概率？动作词表？）——要**能照着写客户端**的程度 |
| Q8 | **限值与错误语义**：图像体积/像素/token 上限、请求体上限、并发（是否无动态批处理）、错误码 |
| Q9 | **硬件与平台**：显存估算（BF16 与量化两档）、KV cache 量级、厂商记录栈（OS / python / torch / triton 之类）、Windows 可行性风险 |
| Q10 | **与我们现有实现的契合度**：能否直接用我们已实现的 `--agent=openai`（真 OpenAI 兼容）或 `--agent=jev`（原生决策协议）后端？若都不能，**需要新增哪种适配器**、改动面多大 |
| Q11 | **选型建议**：给出三选一（或组合）的明确建议 —— ①OmniJev 主用于视觉判定；②NeoHorse-Jev 状态为主 + OmniJev 补视觉；③仍只走状态、不引入视觉模型。每条给**理由与风险**，并说明还需要什么信息才能定论 |
| Q12 | **未决问题**：需要用户提供什么（HF/ModelScope token、私有权限、显卡、磁盘、许可证接受等） |

---

## 3. 硬性约束（铁律）

1. **禁止一切 shell 重定向**（`>`、`>>`、`*>`、`2>&1`）；写文件用 `-o` / `-OutFile` / Python。
2. **破坏性命令默认拒绝**；不删任何已有文件。
3. 命令尽量**从 cmd 启动**；中文写盘乱码就用 cmd/bash 或 Python UTF-8。
4. **不下权重、不装依赖、不改仓库代码、不改机器安全设置**。
5. curl 统一加 `--ssl-no-revoke`；超时给足（`--max-time 60`）但**不要**对不可达主机反复重试超过 3 次。
6. 报告里**区分"证据支持"与"推断"**；**不得**把推断写成事实；引用要带 URL 与状态码。

---

## 4. 验收判据（报告逐条给证据）

| 编号 | 判据 |
|---|---|
| R1 | Q1–Q12 全部有回答（或明确 `unverifiable` + 原因） |
| R2 | 关键结论都有**逐字原文引用**（含 URL 与 HTTP 状态码） |
| R3 | Q3（视觉是否微调）有**决定性证据**，不是转述二手文章 |
| R4 | Q6 的命令**逐字可用**，且注明来源文件与路径 |
| R5 | Q11 的选型建议**明确**（选了哪个、为什么、风险、还需要什么信息） |
| R6 | 明写本次**未下载权重、未装依赖、未改代码**，并给出所用命令清单以便复现 |

---

## 5. 报告落点与返回值

* 报告：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-126-REPORT.md`
  （含：仓库身份、与 Jev 的关系、视觉微调证据、权重清单、起服务命令、接口形状、限值、
  硬件/平台风险、与我们后端的契合度、选型建议、未决问题、所用命令与证据附录）。
* **返回值只给报告路径 + 一行状态**（done/partial/failed）。
* 若仓库或权重页不可达：**如实报告"不可达"**并给出你尝试过的 URL 与状态码，**不要编造内容**。
