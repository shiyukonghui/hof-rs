# TASK-126 报告 — 备选模型 `OmniJev` 调研与选型对比

* 执行者：只读调研子代理（本任务书自包含）
* 执行日期：2026-09-27（本机时间）
* 结论状态：**done**（Q1–Q12 全部作答；其中列明哪些是 `unverifiable` 及其原因）
* 硬性约束遵守：**未下载权重、未安装依赖、未修改任何仓库文件、未改机器安全设置、未使用任何 shell 重定向**。
  本报告本身是本任务唯一允许的写入产物。

> **重要口径说明（先读）**
> 本任务书给出的目标 URL 是 `https://github.com/tinnel123666888/OmniJev`，该仓库就是本报告的主对象。
> 调研中发现存在**第二个同名项目** `OmniJev/PlayJev`（GitHub 组织 `OmniJev`，0.8B、**全参数微调**、
> 自带 `/v1/systemone` 服务）。它是一个**更贴合"视觉微调版类 Jev"字面描述**的候选，且与我们的
> `--agent=jev` 后端**接口更近**。因此本报告**同时**给出两者的数据，并在 Q11 里把两者作为不同选项对待。
> 这一点也升级为 Q12 的第 1 号未决问题（用户需要确认"OmniJev"到底指哪一个）。

---

## 0. TL;DR（决策摘要）

| 项 | `tinnel123666888/OmniJev`（主对象，LoRA 决策模型） | `OmniJev/PlayJev`（同门，0.8B 全参数微调） |
|---|---|---|
| 是什么 | 4B/2B/0.8B 的 **prefill-only 决策模型**（LoRA adapter + 决策头 + ordinal 头），非生成式 | 0.8B **全参数微调**的图像决策模型（原 Qwen3.5-0.8B-Base），十款浏览器小游戏 |
| 视觉塔是否微调 | 官方原文只写 "fine-tunes Qwen3.5 vision-language backbones with **LoRA**"；**无 `vision_finetuning` 类字段**；LICENSE 里那条 backbone 名与 README 自相矛盾 → **证据不足**，判 `无法证实`（见 Q3） | 官方原文 "**full fine-tuning** of the 0.8B base"（模型卡训练段）→ **视觉塔在训练里**（`证据支持`，仍未逐模块核验） |
| 起服务 | 仓库内**没有任何 HTTP 服务**；只有 `mso.infer.MSO1.system_one()` 与 CLI；公开 demo 服务是另一套 `/api/*` | 仓库内有 **`playjev/serve.py`**，暴露 **`POST /v1/systemone`** + `GET /health` + `GET /v1/models` |
| 是否 OpenAI 兼容 | **否**（无 `/v1/chat/completions`） | **否**（无 `/v1/chat/completions`），但原生决策协议 |
| 与我们后端的契合度 | `--agent=openai` ✗；`--agent=jev` **几乎可用但缺 HTTP 服务**，需新增"本地直调"适配器 | `--agent=jev` **最近**：同一 `/v1/systemone` 语义，但 payload 字段名/形状需一个小适配器（`state.frames` vs `state`+`image`，`criteria` dict vs 我们的 `questions`） |
| 选型 | 见 Q11：**推荐 ②（文本状态为主 + 视觉模型补判定），视觉侧优先 PlayJev，次选 tinnel/OmniJev** | 同上 |

---

## 1. Q1 — 可达性（逐条 HTTP 状态码 + 字节数）

**探测环境**：Windows 10/11，`curl.exe`（schannel），统一 `--ssl-no-revoke --max-time 60`（HF 例外见下）。
落盘一律用 `-o`/Python，**全程零 shell 重定向**。响应体落在 `%TEMP%\t126_*`（不进入仓库）。

| # | URL | 状态码 | 字节数 | 备注 |
|---|---|---|---|---|
| 1 | `https://api.github.com/repos/tinnel123666888/OmniJev` | **200** | 5894 | 默认分支 `main`，stars 90，fork 6，created `2026-09-23T10:25:10Z`，pushed `2026-09-26T08:14:41Z`，`size` 23144 KB |
| 2 | `.../contents/` | **200** | 7450 | 顶层 9 个条目（见 §2） |
| 3 | `.../releases` | **200** | 16702 | 1 个 release：`v1.1`，6 个 asset（见 Q5） |
| 4 | `.../git/trees/main?recursive=1` | **200** | 23343 | `truncated: false`，79 个条目 |
| 5 | `https://raw.githubusercontent.com/tinnel123666888/OmniJev/main/README.md` | **200** | 21960 | |
| 6 | `.../main/README_zh.md` | **200** | 21166 | |
| 7 | `.../main/requirements.txt` | **200** | 150 | |
| 8 | `.../main/LICENSE` | **200** | 11720 | Apache-2.0 |
| 9 | `.../main/mso/infer.py` | **200** | 23511 | |
| 10 | `.../main/mso/video.py` / `panels.py` / `head.py` / `branch.py` / `templates.py` / `fast_kernels.py` | **200** | 3555 / 3504 / 7299 / 11402 / 10513 / 2584 | |
| 11 | `.../main/docs/release_v11.json` | **200** | 9754 | 逐文件字节清单 |
| 12 | `.../main/docs/demos_v11.md` | **200** | 6144 | |
| 13 | `.../main/docs/v12_development.md` | **200** | 1729 | |
| 14 | `.../master/README.md` | **200** | 21960 | **注意**：与 `main` 逐字节同长；GitHub 对不存在分支的 raw 路径会回落到默认分支，故**不能据此断定 `master` 分支存在** |
| 15 | `https://api.github.com/repos/OmniJev/PlayJev` | **200** | 7005 | 第二个同名项目 |
| 16 | `https://raw.githubusercontent.com/OmniJev/PlayJev/main/README.md` | **200** | 17032 | |
| 17 | `.../playjev/serve.py` / `model.py` / `train_sft.py`(tree 中确认) | **200** | 7596 / 15888 / — | |
| 18 | `.../docs/HF_MODEL_CARD.md` / `docs/DEMO.md` | **200** | 9777 / 4567 | |
| 19 | `https://omnijev.net/` | **200** | 41433 | 项目主页 |
| 20 | `https://omnijev.net/try.html` | **200** | 34473 | 在线试玩页；内含 `meta name="omnijev-api-base" content="https://api1.omnijev.net/"` |
| 21 | `https://api1.omnijev.net/api/status` | **200** | 159 | 见 Q6 |
| 22 | `https://api1.omnijev.net/api/presets` | **200** | 3966 | |
| 23 | `https://api1.omnijev.net/api/examples` | **200** | 3285 | |
| 24 | `https://api1.omnijev.net/api/preset_img/phone` | **200** | 731073 | `content-type: image/png` |
| 25 | `POST https://api1.omnijev.net/api/ask` | **200** | 785 | **实测**多问题推理成功（见 Q4/Q7） |
| 26 | `POST https://api1.omnijev.net/api/ask`（带 `preset` 字段尝试） | **400** | 71 | `{"error": "unsupported image format; use PNG, JPEG, WebP, GIF, or BMP"}` |
| 27 | `https://huggingface.co/api/models/tinnel123/OmniJev` | **000** | 0 | `curl: (28) Failed to connect to huggingface.co port 443 after 21082 ms` |
| 28 | `https://huggingface.co/tinnel123/OmniJev/resolve/v1.1/{adapter_config.json,head_meta.json,README.md,model_manifest.json}` | **000 ×4** | 0 | 同上，各约 21s 超时。**按任务书要求不做长重试** |
| 29 | `https://modelscope.cn/api/v1/models/tinnel123/OmniJev` | **404** | 152 | 模型页不存在 |
| 30 | `https://modelscope.cn/api/v1/models/tinnel123/OmniJev/repo/files?Revision=master&Recursive=true` | **404** | 155 | 同上 |
| 31 | `https://modelscope.cn/api/v1/models/OmniJev/PlayJev-0.8B` | **404** | 152 | 也不在 ModelScope |
| 32 | `https://modelscope.cn/models/tinnel123/OmniJev`（网页） | **200** | 4933 | 只返回前端空壳页面，非有效数据 |
| 33 | `https://modelscope.cn/api/v1/models/Qwen/Qwen2.5-0.5B-Instruct`（**对照项**） | **200** | 13474 | 证明 ModelScope API 本身本机可达 |
| 34 | `https://modelscope.cn/api/v1/models/AI-ModelScope/stable-diffusion-v1-5/repo/files?Revision=master`（**对照项**） | **200** | 5379 | 返回 `{"Code":200,"Data":{"Files":[...]}}`，证明**逐文件清单 API 本机可用**；也证明 #29/#30 的 404 是"仓库不存在"而非"接口不可用" |
| 35 | `https://api.github.com/repos/OmniJev/openJev` | **404** | 132 | PlayJev README 里的 "OpenJev" 链接在 `OmniJev/openJev` 下不存在（另一个组织/仓库已改名或私有） |
| 36 | `https://api.github.com/search/repositories?q=OmniJev` | **200** | 12612 | 共 2 个命中（本仓库 + `shapsider/OmniJev` 第三方同名） |
| 37 | `https://api.github.com/orgs/OmniJev/repos?per_page=50` | **200** | 13054 | 仅返回 `OmniJev/awesome-jev-gallery` 等（PlayJev 未在该首页列出，但 #15 可直接访问） |

**结论**：GitHub 侧（仓库、raw、releases、API）**完全可达**；项目官网与公开 demo 推理服务**可达**；
**HuggingFace 本机不可达（000，约 21s 连接超时，实测 5 次）**；**ModelScope 上不存在本模型**（对照项证明
ModelScope 接口本身可达）。因此**权重页的逐文件清单无法从 HF 直接核验**，但 **GitHub Release 的 v1.1
manifest 与 SHA256SUMS 已提供等价信息**（见 Q5）。

---

## 2. 仓库身份（原始文本证据）

`api.github.com/repos/tinnel123666888/OmniJev`（HTTP 200，5894 B）原文片段：

```json
"full_name": "tinnel123666888/OmniJev",
"description": null,
"fork": false,
"created_at": "2026-09-23T10:25:10Z",
"updated_at": "2026-09-27T08:58:32Z",
"pushed_at": "2026-09-26T08:14:41Z",
"size": 23144,
"stargazers_count": 90,
"forks_count": 6,
"open_issues_count": 2,
"language": "Python",
"license": { "key": "other", "name": "Other", "spdx_id": "NOASSERTION", "url": null },
"default_branch": "main"
```

> 说明：GitHub API 把许可识别为 `NOASSERTION`（无法自动识别），但仓库内 `LICENSE`（200，11720 B）正文
> 明确是 Apache-2.0：

```
OmniJev - inference code and model weights
Copyright 2026 Beijing Zhongguancun Academy, Institute of Automation of the Chinese Academy of Sciences, and Zevo
(北京中关村学院、中国科学院自动化研究所、智进化)

Licensed under the Apache License, Version 2.0 (full text below). The backbone model (Qwen3-VL-4B-Instruct) keeps its own license.
```

> ⚠️ **发现一处官方材料内部不一致（证据，不是推断）**：`LICENSE` 第 5 行写基座是 **`Qwen3-VL-4B-Instruct`**，
> 而 `README.md`（L45–L47）与 `docs/release_v11.json`（`"base_model": "Qwen/Qwen3.5-4B"`）一律写
> **`Qwen/Qwen3.5-4B`**。两者不可能同时正确，落地前必须向发布方确认（→ Q12）。

顶层文件树（`contents/` 200 + `git/trees/main?recursive=1` 200，共 79 项，`truncated:false`）：

```
.gitignore  LICENSE  README.md  README_zh.md  requirements.txt
bench/     speed_bench.py, summarize_v11.py
docs/      release_v11.json, results_v11.json(1.4MB), results_v11_zh.md(80KB),
           dataset_scores_v11.json(308KB), dataset_scores_v11.md, demos_v11.md,
           scorecard_v05.md, v12_development.md, media/*
mso/       __init__.py, action.py, action_infer.py, branch.py, fast_kernels.py, head.py,
           infer.py(23.5KB), panels.py, records.py, templates.py, v04.py, video.py
tests/     test_action.py, test_panels.py
```

**注意：仓库里没有任何 server/serve/api/http 实现文件**（79 项全量树中无 `serve.py`/`server.py`/`app.py`）。

---

## 3. Q2 — 它是什么 / 与 Jev 的关系 / 基座 / 作者 / 时间 / 许可

**官方自述原文**（`README.md` HTTP 200）：

| 维度 | 原文（逐字） | 出处 |
|---|---|---|
| 自我定位 | "OmniJev is a *System One* decision model. You do not prompt it for text; you give it a state (images, video frames, screenshots, a camera feed, optional context) and a set of **typed questions**, and it returns a probability distribution for every question in **one forward pass with 0 generated tokens**" | README L29 |
| 标题 | "**An omni-modal Jev · 全模态 Jev**" / "*One forward pass, zero generated tokens*" | README L5–L7 |
| 与 Jev 的关系 | 接口契约**对齐 Jev/TypeSafe**："Contract (mirrors TypeSafe's POST /v1/systemone answers, plus our two additions)"，两个自有扩展是 `abstain` 与 region 选项 | `mso/infer.py` L4–L10 |
| 是否复刻/同门 | 文本**未声明**与 NeoHorse-Jev 或 TypeSafe 的代码/权重血缘；只声明 API 兼容。**判为"独立实现 + 协议兼容"** | — |
| 微调方式 | "v1.1 uses Qwen3.5 0.8B, 2B and 4B backbones with **rank-32 LoRA**, decision and ordinal heads, LM features, prefix-branch inference and multi-image panels. This continuation trained for 5,000 / 4,000 / 3,000 steps respectively." | README L257 |
| 基座与参数量 | 三档：`OmniJev-4B` ← Qwen3.5-4B；`OmniJev-2B` ← Qwen3.5-2B；`OmniJev-0.8B` ← Qwen3.5-0.8B（README L43–47 + `release_v11.json`） | README / release manifest |
| 作者单位 | "Beijing Zhongguancun Academy · Institute of Automation, Chinese Academy of Sciences · Zevo" | README L13, L278 |
| 贡献者 | Tianrun Xu（徐添润，Core Developer）、Hongbang Fan、Jiahao Lin、Zilin Zhu、Zhenxin Diao、Longteng Guo（Project Lead）、Jing Liu（Corresponding Author）；联系 `s-xtr24@bza.edu.cn` | README L280–290 |
| 时间 | 仓库创建 **2026-09-23**；`v1.1` release 发布 **2026-09-26T02:09:34Z**；citation `year = {2026}` | repo API / releases API / README L265–272 |
| 许可 | **Apache-2.0**（代码 + 权重），"the backbone keeps its own license" | README L263 + LICENSE |

**第二对象 `OmniJev/PlayJev`**（HTTP 200）原文：

> "PlayJev: A Multimodal JEV-Like Model for Small Games" / "PlayJev is **Qwen3.5-0.8B-Base** fine-tuned to play ten classic browser games from raw pixels. One frame goes in, one forward pass runs, one move comes out, **43 ms on an H200**."（README L5, L24–25）
> "Code and trained weights: Apache-2.0."（L239） · 模型卡 `base_model: Qwen/Qwen3.5-0.8B-Base`，`license: apache-2.0`，`pipeline_tag: image-text-to-text`

---

## 4. Q3 — 视觉是否**真**微调（本任务的关键；含与 NeoHorse-Jev 的对比）

### 4.1 对 `tinnel123666888/OmniJev`：**无法证实（`unverifiable` / 证据不足），且现有证据偏向"未对视觉塔做适配器训练"**

**支持性证据（逐字，均带 URL + 状态码）**

1. README L23（`raw.githubusercontent.com/.../main/README.md`，**200**，21960 B）：
   > "OmniJev fine-tunes Qwen3.5 vision-language backbones with **LoRA**, decision heads and an ordinal head."
   —— 只说 "with LoRA"，**没有**任何一句说视觉编码器被训练、替换或解冻。
2. README L257（同 URL，**200**）：
   > "v1.1 uses Qwen3.5 0.8B, 2B and 4B backbones with **rank-32 LoRA**, decision and ordinal heads, LM features, prefix-branch inference and **multi-image panels**."
   —— 列的适配物只有 LoRA + 决策头 + ordinal 头，**未提视觉塔**。
3. `mso/infer.py`（**200**，23511 B）L61–L64 的加载代码只有三处可训练物：
   ```python
   T.add_option_tokens(base, self.proc, os.path.join(ckpt, "new_tok_emb.pt"))
   backbone = PeftModel.from_pretrained(base, ckpt).eval()
   self.model = T.MSO(backbone, base.config.text_config.hidden_size, head_norm=T.head_norm_of(ckpt)).to(self.dev)
   self.model.head.load_state_dict(torch.load(os.path.join(ckpt, "head.pt"), ...), strict=False)
   ```
   基座文本塔走 `PeftModel`（LoRA），决策头走 `head.pt`，ordinal 头走 `ord.pt`；**视觉塔未见任何单独权重文件或解冻标志**。
4. LICENSE（**200**，11720 B）第 5 行把基座写成 `Qwen3-VL-4B-Instruct`，与其余材料的 `Qwen/Qwen3.5-4B` 冲突 —— 说明发布方对基座口径本身都没统一，进一步降低了"视觉塔被训练"的可信度。
5. **本仓库没有 `vision_finetuning` 类字段可核**（79 项全量文件树 + 全部已抓到的 JSON 中均不存在；`docs/release_v11.json` 只有 `name/repo_id/base_model/files/training_steps_this_stage/published_revision/tag`）。

**被观察到的定量事实（`证据支持`，来自 release manifest，HTTP 200）**

| 文件 | bytes |
|---|---:|
| `adapter_model.safetensors`（4B 的 LoRA） | 243,854,336 |
| `head.pt`（4B） | 29,418,795 |
| `ord.pt`（4B） | 10,497,109 |
| `new_tok_emb.pt`（4B） | 22,085 |
| `tokenizer.json` | 19,989,712 |

**由该事实做的推断（明确标注为 `推断`，不是事实）**：243.9 MB 的 rank-32 LoRA 容量与"只对语言塔
（+ 头）做低秩适配"量级吻合；若视觉塔也被纳入 LoRA 适配，适配器应有显著更大的额外容量。**但**在
HF 不可达（Q1 #27/#28，HTTP 000）的前提下，`adapter_config.json` 的 `target_modules` 无法读取，
因此**无法给出决定性证据**。→ 判定：**Q3 对主对象 = `unverifiable`，只能给出"官方未声明 + 无标志 + 加载代码无视觉塔"的反向证据**。

**同时必须写清的反向事实（避免误读）**：v1.1 **确实在推理侧用了视觉输入**，且为此专门修过 bug：
`mso/panels.py`（**200**，3504 B）docstring：
> "The whole stack encodes exactly one image per record ... Every record that carries more than one image
> therefore had its extra images silently dropped while its prompt still said 'the first picture ... the
> second picture', which makes those questions unanswerable rather than merely hard."
`mso/video.py`（**200**，3555 B）：16 帧拼 4×4 mosaic 后当**一张图**送入。
→ **"视觉输入路径存在且被认真修" ≠ "视觉塔被微调"**，这两件事在本任务里必须分开记录。

### 4.2 对 `OmniJev/PlayJev`：**有决定性文本证据（`证据支持`）**

`docs/HF_MODEL_CARD.md`（`raw.githubusercontent.com/OmniJev/PlayJev/main/docs/HF_MODEL_CARD.md`，**200**，9777 B）：

> L141: "📸 **2.2M frames** — **full fine-tuning of the 0.8B base**, a fifth of each epoch on general image and text questions"
> L151: "**Full fine-tuning**, batch 64, learning rate 2e-5 from the base and 1e-5 for a round, fp32 master weights with bf16 autocast."

`README.md`（**200**，17032 B）L167（Training Recipe 表）：

> | **Cloning** | One epoch, batch 64, lr 2e-5, **full fine-tuning**, bf16 autocast on fp32 master weights. |

并且 `playjev/model.py`（**200**，15888 B）的加载路径就是普通全参模型（无 `PeftModel`）：
```python
from transformers import AutoModelForImageTextToText, AutoProcessor
self.model = AutoModelForImageTextToText.from_pretrained(self.model_id, dtype=..., device_map=..., local_files_only=local)
```
外加 L14–15 明确引用视觉塔的 patch 机制：
> "`stack=\"temporal\"` puts the previous frame in temporal slot 0 and the current frame in slot 1 of the **vision tower's 2-frame patch**"

**结论**：PlayJev 是**全参数微调**（因而**视觉塔参与训练**），这是可核原文的直接证据；但"视觉塔每一层
都被更新"仍属**由全参微调推出的推断**（未逐模块核验），本报告按 `证据支持 + 推断` 双重标注。

### 4.3 与 NeoHorse-Jev 的对比（承接 TASK-123）

| 维度 | NeoHorse-Jev-4B（TASK-123，引自本任务书与 `TASK-124.md`） | tinnel/OmniJev v1.1 | PlayJev |
|---|---|---|---|
| 视觉标志字段 | `model_manifest.json` 里 **`"vision_finetuning": false`**，视觉编码器是原版 Qwen3.5-4B | **无该字段**；官方未声明视觉塔被训练 | 无该字段；但官方声明**全参微调** |
| 视觉能力 | Image-NLI 60.65%；**image-Doom 接近随机**（1.00–16.00 mean kills，random 1.00 / oracle 16.60）；text-state Doom 10.60–14.40 | 见 Q4（官方自述 30 族 macro 70.00%，含 `game` 90.36 / `atari` 63.87） | 十款小游戏 **16 held-out 回合 argmax**，mean vs teacher **0.57**；MMBench dev 0.78 |
| 图像请求限制 | **只能 1 张图 + 1 个问题** | **1 张图（多帧视频=1 张 mosaic）+ ≤12 问**（官方自述；实测 3 问 1 次请求成功） | 1 帧（`--two-frame` 时 2 帧进 temporal patch）+ 多问题共享 |

> **一句话对比**：NeoHorse-Jev 是"视觉未微调、文本状态强"；`tinnel/OmniJev` 是"**视觉是否微调未证实**、
> 但视觉输入路径可用且基准自述高"；`PlayJev` 是"**视觉确实参与全参训练**、但领域窄（十款网页小游戏）、
> 参数小（0.8B）"。

---

## 5. Q4 — 视觉能力证据（区分官方自述 / 第三方；图 + 多问题）

### 5.1 官方基准（`README.md` HTTP 200；`docs/results_v11.json` 1.4MB；`docs/results_v11_zh.md` 80KB）

**30 族汇总（README L118–126 原表）**：

| Model | Families | Questions | Macro accuracy % | Micro accuracy % | Mean family ECE % ↓ |
|---|---:|---:|---:|---:|---:|
| Base 0.8B | 30 | 21,456 | 40.07 | 40.04 | 20.83 |
| SFT 0.8B | 30 | 41,951 | 47.86 | 48.09 | — |
| v1.1 0.8B | 30 | 41,975 | 64.52 | 65.40 | 4.30 |
| Base 2B | 30 | 21,456 | 36.30 | 35.94 | 34.21 |
| v1.1 2B | 30 | 41,975 | 64.46 | 65.42 | 6.27 |
| Base 4B | 30 | 21,456 | 40.12 | 39.79 | 30.04 |
| **v1.1 4B** | 30 | 41,975 | **70.00** | **70.82** | 5.89 |

**与"游戏截图判定"最相关的族（README L130–162 原表摘录）**：

| Family | Base 4B | **v1.1 4B** | 备注 |
|---|---:|---:|---|
| `game` | 15.36 | **90.36** | 逐帧游戏决策 |
| `atari` | 34.29 | **63.87** | JAT Atari |
| `mario` | 46.78 | 56.05 | **README L110 自曝**："Mario next-action accuracy is 43.52% (193 questions), not the mixed 56.05%" |
| `snake` | 44.86 | 84.47 | |
| `gomoku` / `chess2` / `chess3` / `xiangqi` | 16.60 / 16.74 / 5.49 / 10.15 | 70.60 / 62.40 / 22.67 / 23.67 | 棋类弱 |
| `events` / `video` / `lvb` | 55.56 / 49.11 / 59.02 | 89.13 / 62.81 / 56.80 | **LVB 低于 base** |
| `vqa`（OK-VQA） | 85.73 | 93.47 | **README L110 自曝**："OK-VQA 93.47% uses supplied candidates including the gold answer, not official open-ended VQA scoring" |
| `pope` | 86.42 | 84.73 | **低于 base** |
| `androidcontrol` / `web` / `webtest` / `wiki` / `run` | 28.81 / 31.28 / 30.45 / 33.74 | 77.30 / 76.80 / 77.40 / 72.13 | |

**官网（`omnijev.net` HTTP 200，41433 B）另一组带 n 的评测**（HTML 原文提取，与 README 数字**不完全一致**，
例如官网 Catch game 4B=87.0 而 README `game`=90.36；官网 OK-VQA 4B=80.9 而 README `vqa`=93.47）——
**两套官方数字口径不同，禁止混用**：

| Benchmark | Qwen3.5-0.8B ZS | OmniJev-0.8B | OmniJev-2B | Qwen3.5-4B ZS | **OmniJev-4B** | n |
|---|---:|---:|---:|---:|---:|---:|
| LIBERO-10（机器人，每帧 8 题） | 55.1 | 77.1 | 72.4 | 29.9 | **80.7** | 1,504 |
| Mind2Web test（task/website/domain） | 40.1 | 59.6 | 63.1 | 30.3 | **73.3** | 1,500 |
| Grid pointing（96 格网页定位） | 38.4 | 47.4 | 62.5 | 42.1 | **73.7** | 1,500 |
| Charades-STA（视频事件定位） | 39.0 | 81.1 | 82.6 | 54.3 | **85.9** | 1,500 |
| **Catch game（逐帧游戏决策）** | 40.9 | 66.1 | 72.8 | 15.1 | **87.0** | 1,504 |
| HaGRID + safety（手势/火/烟/武器） | 52.9 | 96.9 | 98.4 | 68.3 | **98.7** | 1,500 |
| OK-VQA（答案候选池） | 79.3 | 65.6 | 76.5 | 86.0 | **80.9** | 1,500 |
| LongVideoBench val | 41.0 | 48.6 | 50.2 | 58.5 | **58.2** | 500 |

### 5.2 官方**自曝的局限**（这部分是可信度加分项，必须并列引用）

* README L23："The current training manifest is still being audited; the earlier 270,000-record figure is **not an exact count** for this release."
* README L25："The released demonstrations are **offline replays**; reliable **closed-loop gameplay and robot control have not been established**."
* README L61："These are recorded-trajectory replays, **not live model-controlled runs**. Some inputs may overlap training; they are illustrations, **not new benchmark results**."
* README L110："these are **capped task-family aggregates, not complete per-dataset benchmark results**."
* README L166："The table reports existing evaluations, **not a matched-sample ablation**."
* README L170："**Multi-image SFT retraining and inference over the newly frozen 272,561-question set are not completed.**"
* README L176："4B has the highest 30-family macro accuracy, but **POPE (84.73% vs 86.42% base) and LVB (56.80% vs 59.02% base) remain lower**."
* `docs/demos_v11.md` L28："This replay does **not** demonstrate gameplay competence. Its next-action match rate is 24/28, **exactly the same as always choosing `right_B`** on this clip."
* `docs/demos_v11.md` L35："Some records may overlap training. These videos are illustrations, **not benchmark scores or evidence of episode-level generalization**."
* README L198：延迟数字是**历史测量**（"one idle A800-SXM4-40GB: 4B 294/292/344/436 ms" 对应 1/3/6/12 问），"**not new v1.1 serving benchmarks**"。

### 5.3 第三方

* `web_search` 命中一篇中文解读 [`让决策模型"看见"：OmniJev 试图把图像接进 Jev 的决策闭环`](https://blog.csdn.net/qq_40943760/article/details/166373989)（CSDN，二手转述）——**未作为证据采用**。
* 另有**第三方同名仓库** `shapsider/OmniJev`（17 stars，"multimodal finite-choice decision interface and MuJoCo embodied workbench"，HTTP 200 in search results）——**与目标仓库无关**，不作为证据。
* 结论：**本轮未找到可用的独立第三方评测**（第三方评测 = `unverifiable`）。

### 5.4 "图 + 多问题"支持 —— **实测成功**（这是本报告最硬的一条一手证据）

用公开 demo 服务 `https://api1.omnijev.net/api/ask` 做了一次**真实推理**（Python `urllib`，带浏览器
`User-Agent`；**未下载权重、未装依赖**）：

* 输入：`api1.omnijev.net/api/preset_img/phone` 的 PNG（731,073 B）转 data URL + **3 个不同类型的问题**
  （1×`choice` + 1×`noul` + 1×`score`）。
* 结果：**HTTP 200，785 B，wall 27.69 s（含上传），服务自报 `wall_s: 0.1793`**。响应逐字：

```json
{"answers":[
 {"id":"q0","question":{"type":"choice","instructions":"Is this a phone screen?",
   "options":[{"key":"yes","text":"yes"},{"key":"no","text":"no"},{"abstain":true}]},
  "answer":{"choice":"yes","probabilities":{"yes":0.9993,"no":0.0003},
            "abstain":0.0003,"valid":true,"confidence":0.999}},
 {"id":"q1","question":{"type":"noul","instructions":"This screen shows an error dialog."},
  "answer":{"noul":0.0003}},
 {"id":"q2","question":{"type":"score","instructions":"How cluttered is this screen?",
   "levels":["clean","busy","very busy"]},
  "answer":{"score":"very busy","probabilities":{"clean":0.1138,"busy":0.3867,"very busy":0.4995},
            "confidence":0.2492}}],
 "wall_s":0.1793,"queued_s":0.0,"n_questions":3,"video":null}
```

→ **一次请求 = 1 张图 + 3 个问题**，返回每问的概率分布 + `abstain` + `confidence`。这与 NeoHorse-Jev
"1 图 1 问"的限制形成**明确对比**，是选型的核心论据之一（同时再次提醒：该服务自报模型名是
`omnijev-0.5`，与 v1.1 4B **不是同一版本**，见 Q6 注）。

---

## 6. Q5 — 权重：在哪 / 逐文件大小 / 总量 / 授权 / 量化

### 6.1 位置（可达性见 Q1）

| 渠道 | URL | 状态 |
|---|---|---|
| GitHub Releases | `https://github.com/tinnel123666888/OmniJev/releases/tag/v1.1` | **200**（API 16702 B） |
| HuggingFace（README/官网指向） | `https://huggingface.co/tinnel123/OmniJev`（4B）、`-4B`(mirror)、`-2B`、`-0.8B`、`-SFT-0.8B` | **本机不可达（000）**，仅登记路径 |
| ModelScope | 尝试 `tinnel123/OmniJev`、`OmniJev/PlayJev-0.8B` | **均 404，不存在** |
| PlayJev 权重（对照） | `https://huggingface.co/OmniJev/PlayJev-0.8B` | **本机不可达（000）**，仅登记路径 |

### 6.2 `v1.1` GitHub Release 资产（`releases` API HTTP 200，逐字）

| asset | bytes | download_count | sha256 |
|---|---:|---:|---|
| `OmniJev-4B-v1.1.tar.gz` | 268,393,338 | 17 | `fbb4450a9e6180acce6a955982d4bc8eab21a6fe0112e9091ad8521c0818297d` |
| `OmniJev-2B-v1.1.tar.gz` | 152,402,828 | 2 | `1587f51d2e6c88422213b6b606dd9c24515eef62622390f6ec05014f5bce18f4` |
| `OmniJev-0.8B-v1.1.tar.gz` | 100,548,082 | 7 | `55491996e4dcedfaa1659841ccd2011fe87431cda0d91467d60da522c1e17cb5` |
| `OmniJev-SFT-0.8B-v1.1.tar.gz` | 80,937,105 | 6 | `deb98e945820a8032c7aac1c8873566e49d40539376d2fb0ef010c0b98a0951d` |
| `OmniJev-v1.1-demo-pack.zip` | 14,281,614 | 7 | `5bbefa6e16f86fddeb59dad0c3e7600bd17efceceed55257c610b0564c963f54` |
| `SHA256SUMS` | 364 | 1 | `0c1bfa2ebac77a6e1f83de43fe297ae880dfb883cd8257af20e227315d2d98ba` |

Release body（逐字）：
> "Each archive contains a **LoRA adapter**, applicable **decision/ordinal heads**, tokenizer/processor and model card; **the Qwen3.5 backbone must be downloaded separately**. SHA256SUMS verifies the archives, and each archive contains a per-file `release_manifest.json`. **No smoke-test weights are included.**"

### 6.3 逐文件字节清单（`docs/release_v11.json` HTTP 200，9754 B；含 sha256）

**OmniJev-4B（= `tinnel123/OmniJev`，两 repo 文件清单逐字节相同）**：

| 文件 | bytes |
|---|---:|
| `adapter_model.safetensors` | 243,854,336 |
| `head.pt` | 29,418,795 |
| `tokenizer.json` | 19,989,712 |
| `ord.pt` | 10,497,109 |
| `new_tok_emb.pt` | 22,085 |
| `chat_template.jinja` | 7,756 |
| `adapter_config.json` | 1,269 |
| `tokenizer_config.json` | 1,226 |
| `processor_config.json` | 1,189 |
| `head_meta.json` | 1,061 |
| **合计** | **≈ 305.8 MB**（不含基座） |
| `training_steps_this_stage` | 3,000 |
| `published_revision` | `ffe5f436eaf22e20e2f041f8e74e121fd057a6cb` |

* 2B：adapter 125,087,712 + head 25,224,491 + ord 8,399,957 + tokenizer 19,989,712 + … ≈ **178.7 MB**，`training_steps_this_stage` 4,000
* 0.8B：adapter 81,833,800 + head 16,835,883 + ord 4,205,653 + tokenizer 19,989,712 + … ≈ **122.9 MB**，`training_steps_this_stage` 5,000
* SFT-0.8B：adapter 81,833,800 + tokenizer 19,989,343 + …，`training_steps_this_stage` 12,500（**无 head/ord**，因为它是生成式基线）

**总量（推断，明确标注）**：`tinnel/OmniJev-4B` = **约 306 MB 适配器/头 + 基座 `Qwen/Qwen3.5-4B` 另计
（README 要求单独 `hf download`）**。4B BF16 基座约 8 GB 量级（**推断**，未下载、未核验）。

### 6.4 是否需要授权 / token、量化 / GGUF

* **授权/token**：三个渠道（GitHub Release / 官网 demo）**均未要求 HF token 或登录**；README 的
  `hf download` 命令也未见 `--token`。HF 页是否 gated **无法核验（HF 不可达）** → `unverifiable`。
* **量化 / GGUF**：仓库内**没有任何量化或 GGUF 产物**（79 项全量树无 `.gguf`/`.q4*`/`bitnet` 类文件；
  Release 只有 4 个 `.tar.gz` + demo pack）。格式是 **PEFT LoRA adapter（safetensors）+ 自定义 `.pt` 头**，
  **不是**可直接喂给 llama.cpp 的完整权重。→ **无量化版、无 GGUF**（`证据支持`）。

---

## 7. Q6 — 起服务的确切命令（逐字抄 + 出处）

### 7.1 `tinnel123666888/OmniJev`：**仓库内没有 HTTP 服务**，只有进程内 Python API 与 CLI

**（a）环境与取权重 —— 出处 `README.md` L202–208（HTTP 200），逐字：**

```bash
git clone https://github.com/tinnel123666888/OmniJev && cd OmniJev
python -m venv venv && ./venv/bin/pip install -r requirements.txt     # torch, transformers>=5, pillow

hf download tinnel123/OmniJev --revision v1.1 --local-dir ckpt                       # the OmniJev weights
hf download Qwen/Qwen3.5-4B --local-dir base               # the backbone (or symlink a local copy)
```

`requirements.txt`（HTTP 200，150 B）逐字：
```
torch>=2.4
transformers>=5.0
peft>=0.15
accelerate
safetensors
pillow
# video input (mso/video.py) also needs the ffmpeg and ffprobe binaries on PATH
```
README L51 补充："`pip install fla-core` is optional and turns on the fast linear-attention kernels."

**（b）进程内调用 —— 出处 `README.md` L212–226，逐字：**

```python
from mso.infer import MSO1

m = MSO1("ckpt", "base")
answers = m.system_one(
    {"images": ["screen.png"]},
    {"op":   {"type": "choice", "instructions": "Which operation comes next?",
              "criteria": {"click": "tap an element", "type text": "", "scroll": ""}},
     "risk": {"type": "score",  "instructions": "How irreversible is the next action?",
              "levels": ["harmless", "needs care", "irreversible"]},
     "err":  {"type": "noul",   "instructions": "This screen shows an error dialog."}})
```

**（c）CLI —— 出处 `mso/infer.py` L15–18（docstring，HTTP 200），逐字：**

```bash
python -m mso.infer --ckpt <ckpt_dir> --model <base> --image img.jpg \
   --questions '{"q1":{"type":"noul","instructions":"There is a cat."},
                 "q2":{"type":"choice","instructions":"Which animal?","criteria":{"cat":null,"dog":null}}}'
```
（同文件 L406–416 确认 argparse 参数为 `--ckpt --model --image --questions [--tiny]`，**无 `--port`/`--host`**。）

**（d）公开 demo 服务（不是本仓库代码，是发布方运营的实例）—— 出处 `https://omnijev.net/try.html`（HTTP 200，34473 B）**
第 5 行与第 132–133 行逐字：
```html
<meta name="omnijev-api-base" content="https://api1.omnijev.net/">
```
```javascript
var API_BASE=(document.querySelector('meta[name="omnijev-api-base"]').content||'').replace(/\/+$/,'');
function apiUrl(path){return API_BASE+'/'+String(path).replace(/^\/+/, '');}
```
实际端点（从该页 JS 提取 + 实测）：`GET /api/status`、`GET /api/presets`、`GET /api/examples`、
`GET /api/preset_img/<id>`、`POST /api/upload_image`、`POST /api/prep_video`、**`POST /api/ask`**。
实测 `GET /api/status`（HTTP 200，159 B）逐字：
```json
{"service": "omnijev", "status": "ready", "ready": true, "error": null, "model": "omnijev-0.5", "device": "cuda:0", "loading_s": 34.9, "queue": 0, "asks": 353}
```
> ⚠️ **该实例自报 `"model": "omnijev-0.5"`，不是 v1.1 的 0.8B/2B/4B**；其服务端实现**不在公开仓库内**，
> 不能当作"OmniJev 自带 server"使用。

### 7.2 `OmniJev/PlayJev`：**仓库内有自带服务**（这是最接近我们需求的一项）

**出处 `playjev/serve.py`（`raw.githubusercontent.com/OmniJev/PlayJev/main/playjev/serve.py`，HTTP 200，7596 B）
第 1–18 行 docstring + 第 126–139 行 `main()`，逐字：**

```python
"""PlayJev server: the OpenJev /v1/systemone endpoint for image states.

    python -m playjev.serve --ckpt /path/to/ckpt --port 18732            # one frame per decision
    python -m playjev.serve --ckpt /path/to/ckpt --port 18732 --two-frame  # (previous, current) temporal stack
...
Every question is a Choice over its criteria (a dict name -> description, or a list of names); the frames are
shared by all questions of one request. Text states are refused with 400: that is OpenJev's job. Requests are
served one at a time (one forward each); CORS is open so the demo page can call this from any origin.
"""
```
```python
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt", required=True, help="checkpoint directory or HF id for PlayJevModel")
    p.add_argument("--host", default="127.0.0.1"); p.add_argument("--port", type=int, default=18732)
    p.add_argument("--device", default="cuda:0"); p.add_argument("--name", default="playjev-0.8b")
    p.add_argument("--two-frame", action="store_true", ...)
    p.add_argument("--stack", default="temporal", choices=["temporal", "separate"])
    p.add_argument("--template", default="plain", choices=["plain", "chat"])
    p.add_argument("--verbose", action="store_true", ...)
```
README L104 的另一条用法（同仓库 HTTP 200，逐字）：
```
playjev.serve --ckpt <ckpt> --port 18732    # the checkpoint at /v1/systemone in the OpenJev request shape;
                                            # the demo switches every tile to it with ?server=http://127.0.0.1:18732
```
以及 README L84（权重走 HF，**本机不可达**）：
```
python -m playjev.play snake --policy local --ckpt OmniJev/PlayJev-0.8B --episodes 1
```

### 7.3 OpenAI 兼容 vs 原生决策协议

| 模型 | `/v1/chat/completions` | `/v1/systemone` | `/v1/decision` | `/health` | `/v1/models` |
|---|---|---|---|---|---|
| NeoHorse-Jev（基线） | ✗ | ✓ | ✓ | ✓ | ✗ |
| tinnel/OmniJev（仓库） | ✗（无任何 HTTP 服务） | ✗（仅进程内 `system_one()`；docstring 说"镜像"该契约） | ✗ | ✗ | ✗ |
| tinnel/OmniJev（公开 demo 实例） | ✗ | ✗ | ✗ | ✗（有 `GET /api/status`） | ✗ |
| PlayJev | ✗ | **✓**（`serve.py` L111 只看 `self.path.rstrip("/") != "/v1/systemone"` → 其余 POST 全 404） | ✗ | **✓**（L105） | **✓**（L103） |

→ **两者都不是 OpenAI 兼容**，都是 Jev 式原生决策协议路由；`tinnel/OmniJev` 连原生 HTTP 路由都没有。

---

## 8. Q7 — 接口形状（细到"能照着写客户端"）

### 8.1 `tinnel/OmniJev` 进程内 API（出处 `mso/infer.py` L369–L386，HTTP 200）

**输入**
```python
m.system_one(
  state,      # {"images": [path, ...], "video": {"n_frames":16,"cols":4,"tile":384,"timestamps":[...],"duration":s} 或 None}
  questions,  # {"<qid>": question}, question = {"type":"choice"|"noul"|"score",
              #   "instructions": str,
              #   "criteria": {key: rubric},        # Jev 原生形状（choice/score）
              #   "levels": [str, ...],             # score 有序档
              #   "options": [{"key":..,"text":..} | {"key":..,"region":{"box":[x1,y1,x2,y2]}}],  # 自有扩展；坐标 0–1000
              #   "region": {...} }                 # noul 的区域限定
  packed=True)
```
**图像语义（逐字，`system_one` docstring）**：
> "The model encodes **exactly one image per request**. Several stills are **tiled into a single numbered panel** in reading order, so a question may refer to 'the second picture' ... Set `MSO_NO_PANELS=1` to restore that older behaviour. With `video`, `images[0]` is **already the 4x4 frame mosaic** and is passed through untouched. `packed=True` answers every question in one forward (state encoded once)."

→ **一次请求 1 张图（多图=拼板、视频=4×4 mosaic），问题数不限（官方口径见下）**。

**输出（`_finish()` L233–L261，逐字键名）**
```python
# noul
{"noul": 0.0003, "latency_s": 0.18}
# choice
{"choice": "yes", "probabilities": {"yes": 0.999, "no": 0.001},
 "abstain": 0.02, "valid": true, "confidence": 0.999, "latency_s": 0.18}
# score
{"score": "very busy", "probabilities": {"clean": 0.11, "busy": 0.39, "very busy": 0.50},
 "confidence": 0.25, "latency_s": 0.18}
# packed 模式额外：res[qid]["latency_total_s"] = ...
# 无可渲染选项时：{"choice": None, "score": None, "probabilities": {}, "abstain": 1.0, "valid": False, "confidence": 0.0}
```
`confidence = (K*p_max - 1)/(K - 1)`，Jev 定义（`mso/infer.py` L9 逐字）。`valid=False` 表示
`sum(mu)>1` 被**重归一化**（选项独立性失效），见 `mso/head.py` L9–L21。

### 8.2 `tinnel/OmniJev` 公开 demo HTTP 形状（**实测**，`POST /api/ask`，HTTP 200）

**请求**
```json
{"questions":[{"type":"choice","instructions":"...","options":["yes","no"]},
              {"type":"noul","instructions":"..."},
              {"type":"score","instructions":"...","levels":["clean","busy","very busy"]}],
 "image":"data:image/png;base64,<...>"}
```
* `questions` 是**数组**（不是 map），每项自带 `type`。
* `image` 在实测中**只接受 data URL**（或后端已上传的图片 id）；直接给 `{"preset":"phone"}` 会被
  判定为非法图像格式 → **HTTP 400 `unsupported image format; use PNG, JPEG, WebP, GIF, or BMP`**。
* 区域选项形状（`try.html` L269–L270，逐字）：`{key: 'region N', box: [x1,y1,x2,y2]}`，坐标 **0–1000**。

**响应**：见 Q4 §5.4 逐字 JSON；含 `answers[]`（每项 `{id, question, answer}`）、`wall_s`、`queued_s`、
`n_questions`、`video`。`choice` 的 `answer` 另含 `abstain` 与 `valid`。

### 8.3 `PlayJev` `/v1/systemone`（出处 `playjev/serve.py` L6–L13 + L39–L74 + L110–L123，HTTP 200）

**请求（docstring 逐字）**
```json
{"model": "playjev-latest",
 "state": {"frames": ["data:image/jpeg;base64,...", "..."]},
 "questions": {"q": {"type": "choice", "instructions": "Which move should the player make next?",
                     "criteria": {"up": "turn the snake to move up", "...": "..."}}}}
```
* `state` **必须是** `{"frames":[...]}`（1 帧，或 `--two-frame` 时按 (previous, current) 取 `frames[-2]/[-1]`）；
  文案帧只接受 base64 字符串或 data URL（`_frame_bytes()` L31–L37）。
* **只支持 `type: "choice"`**（L53–L54：`q.get("type","choice") != "choice"` → 400 "only type \"choice\" is served"）；
  `criteria` 必须是 **dict 或 list**（≥2 项，L55–L63）。
* **文本状态被明确拒收**："Text states are refused with 400: that is OpenJev's job."

**响应（docstring 逐字）**
```json
{"model": "playjev-0.8b", "answers": {"q": {"type": "choice", "choice": "up",
  "probabilities": {"up": 0.9, "...": 0.1}, "confidence": 0.87}},
 "timing": {"prep_ms": 5.1, "forward_ms": 38.2, "visual_tokens": 182, "total_ms": 41.3}}
```
注意：`answers` 是 **map（键 = 问题名）**，与 tinnel 的**数组**不同；`choice` 返回的是**选项名字符串**
（不是索引）；**没有 `abstain` 字段**（因为它 softmax 在字母槽上）。

**提示词契约（出处 `playjev/model.py` L34–L73，HTTP 200）**：`openjev-letters-v1` 冻结措辞，选项渲染为
`A..Z` 字母槽，末尾 `Answer:`（`PLAIN_ANSWER_CUE = "Answer:"`）；只支持 **≤26 个选项**
（L45–L46：`if len(options) > len(LETTERS): raise ValueError(f"{len(options)} options exceed the {len(LETTERS)} letter slots")`）。

---

## 9. Q8 — 限值与错误语义

### 9.1 `tinnel/OmniJev`

| 项 | 值 | 出处 / 性质 |
|---|---|---|
| 图像预算（tinnel 代码默认） | `max_pixels = 768*28*28 = 602,112 px`（`MSO1.__init__` 默认参数，`mso/infer.py` L40） | `证据支持` |
| 图像预算（官方服务口径） | "**a 768-token image budget**"，"all questions about the same image in **one request**" | 官网 `omnijev.net` HTTP 200，`证据支持` |
| 一次几张图 | **1**（多图→拼板；视频→4×4 mosaic 当 1 张） | `mso/infer.py` docstring / `mso/panels.py` docstring |
| 一次几个问题 | README L37："**Twelve questions about the same screenshot cost about as much as one**"；实测 3 问 ✓，**官方未写硬上限** | `证据支持`（12 为性能口径，不是硬限） |
| 上传体积（公开 demo） | 图片 **≤8 MB**（PNG/JPEG/WebP/GIF/BMP）；视频 **≤60 MB**（MP4/WebM/MOV/M4V） | `try.html` L100/L118（`upload_note`）逐字："PNG/JPEG/WebP/GIF/BMP up to 8 MB · MP4/WebM/MOV/M4V up to 60 MB" |
| 请求体上限 | 公开 demo **未文档化** → `unverifiable` | — |
| 并发 | 公开 demo `status` 有 `"queue": 0` 字段，**但无并发/动态批处理文档**；仓库内**无 server 代码可核** → `unverifiable` | — |
| 错误码 | 实测 `400 {"error":"unsupported image format; use PNG, JPEG, WebP, GIF, or BMP"}`；`try.html` L310 另显示业务错误串 `uploaded image is missing; upload it again` | `证据支持` |
| 视频参数 | 16 帧、4 列、每格 384 px、时间戳水印，`frames = (i+0.5)/16*dur`；`dur < 1.0s` → `ValueError("video shorter than one second")`；需 `ffmpeg`/`ffprobe` 在 PATH | `mso/video.py` L16/L61–L88，`证据支持` |
| 拼板上限 | `_grid(n)`：≤1→1×1，2→2×1，≤4→2×2，否则 3 列；每图 `thumbnail(max_side=448)` | `mso/panels.py` L25–L51 |

### 9.2 `PlayJev`

| 项 | 值 | 出处 |
|---|---|---|
| 帧数 | 1（默认）；`--two-frame` 时 2 帧进视觉塔的 temporal patch 槽 | `serve.py` L44–L47 / `model.py` L14–L15 |
| 图像缩放 | `long_side=None` 默认**不缩放**（`_to_image` 仅在给了 `long_side` 时 resize）；训练/采集用 **448 px JPEG** | `model.py` L187–L193 / README L166 |
| 选项数 | **≤26**（字母槽） | `model.py` L38/L45–L46 |
| 问题类型 | **仅 `choice`** | `serve.py` L53–L54 |
| 问题数/请求 | 无硬限（`questions` 非空即可），但**串行逐问 forward**："for qname, q in questions.items(): ... with self.lock:" → **N 个问题 = N 次 forward**（与 tinnel 的"打包一次 forward"本质不同） | `serve.py` L51–L74 |
| 并发 | **无动态批处理**："Requests are served one at a time (one forward each)"，且 `threading.Lock()` 串行化 | `serve.py` L16–L17, L29, L65 |
| 错误码 | `400 {"error": "..."}`（参数/帧/题目不合规）；`500 {"error": "TypeName: msg"}`（其他异常，"a bad frame must not take the server down"）；未知路径 `404 {"error":"not found"}`；CORS 全开 `Access-Control-Allow-Origin: *` | `serve.py` L108/L120–L123/L94–L97 |
| 请求体上限 | 代码未设 `Content-Length` 上限（读 `int(self.headers.get("Content-Length") or 0)`） | `serve.py` L114 |
| 速度 | "43 ms on an H200"（README L25）；样例响应 `forward_ms: 38.2`、`visual_tokens: 182` | README / `serve.py` L13 |

---

## 10. Q9 — 硬件与平台

| 项 | `tinnel/OmniJev-4B`（BF16） | `tinnel/OmniJev-0.8B` | `PlayJev-0.8B` |
|---|---|---|---|
| 权重体积 | **≈306 MB** 适配器/头（实测清单）+ 基座另计 | **≈123 MB** + 基座 | 全参 0.8B，**约 1.6 GB BF16（推断）** |
| 显存估算（BF16） | 基座 BF16 ≈8 GB + 适配器/头 ≈0.3 GB → **≈8–9 GB 起**（**推断**，未下载验证）；官方 demo 跑在 `cuda:0`，演示推理用 **8× MLU590**（`docs/demos_v11.md` L52） | **≈2 GB 起**（推断） | README L90 逐字："a CUDA GPU, **about 3 GB for inference** and **17 GB for training at batch 64**"（**证据支持**） |
| 量化档 | **无任何量化/GGUF 产物**（Q5 §6.4）→ 只能 BF16/FP16 或自行量化 | 同左 | 同左 |
| KV cache | **prefill-only、0 生成 token**（README L7/L29）→ 无自回归 KV 增长；但**前缀分支**会按 (问题 × 选项) 行数占用激活 | 同左 | 一次 forward 取 `Answer:` 位置的字母 softmax，**0 生成 token** |
| 延迟（官方） | v1.1 4B："historical" A800-SXM4-40GB：1/3/6/12 问 = **294/292/344/436 ms**（README L198）；官网 A100：**768-token 图像预算、同图所有问题合一次请求、12 次运行中位数**（`omnijev.net` 原文） | 216/216/218/236 ms（README L198） | H200 **43 ms/move**（README L25）；模型卡自曝 open problem："at 83 to 100 ms per step the decision lands one step late"（HF_MODEL_CARD L161） |
| 厂商记录栈 | 训练栈**未公开**；README 只给 `torch>=2.4 / transformers>=5.0 / peft>=0.15 / accelerate / safetensors / pillow`，可选 `fla-core`（Triton 线性注意力核）；`mso/infer.py` 支持 `cuda` / `cpu` / **`mlu`**（寒武纪）三后端，并有 `MSO_ATTN` 覆盖注意力实现 | 同左 | README L90/L95："**Python 3.12**, a CUDA GPU"、"`pip install -r requirements.txt && playwright install chromium`"（训练/采集还需 Playwright + Chromium） |
| Windows 可行性风险 | **中高**：① 官方全部示例是 `./venv/bin/pip`（POSIX）与 A800/A100/MLU590（Linux）——**无 Windows 记录**；② `mso/video.py` 的 `font()` 只找 `/usr/share/fonts/...`（Linux 路径），Windows 上会回落到 `ImageFont.load_default()`；③ 视频路径依赖 `ffmpeg`/`ffprobe` 在 PATH；④ 线性注意力走 Triton/`fla`，Windows 上 Triton 轮子稀缺（`MSO_BRANCH=0` 可关，但官方说混合骨干"cannot isolate options with a mask"） | 同左 | **中**：Python 3.12 + torch + transformers 在 Windows 可跑；但训练/采集脚本依赖 **Playwright + headless Chromium**，且 `scripts/reproduce.sh` 是 bash |

---

## 11. Q10 — 与我们现有实现的契合度

**我们现有的两个后端**（引用 `godot-mcp/tools/playtest_agent.py`，只读查阅）：

* `--agent=openai`：真 OpenAI 兼容（`/v1/chat/completions`，多图 `image_url` data URL），`send_images` 默认 **True**，`max_images` 默认 3（L306–L307, L357–L370, L450–L457）。
* `--agent=jev`：原生决策协议。`JEV_DECISION_PATHS = ("/v1/systemone", "/v1/decision")`（L501）；
  `send_images` 默认 **False**（L649：`# text state is the strong path`）；payload 形状（L915–L924）：
  ```python
  payload = {"model": self.model, "state": state_value, "questions": questions}
  if with_image:
      payload["image"] = "data:image/png;base64,%s" % base64.b64encode(data).decode("ascii")
  ```
  且 `questions` 是我们自己构造的 **typed map**（`noul`/`choice`/`score` + `criteria` dict/list），
  **沿用 NeoHorse-Jev 文档的硬限**：`state` 2048 token、16 问/请求、1 MiB 文本体 / 8 MiB 图像体、
  **1 图 + 1 问**、`score` 2..10 档（L503–L516, L801–L804）。

### 契合度矩阵

| 目标 | `--agent=openai` | `--agent=jev`（现状） | 结论 |
|---|---|---|---|
| `tinnel/OmniJev` | ✗ **不可能**（无 `/v1/chat/completions`，无 HTTP 服务） | ✗ 直接不可能（**仓库根本没有 HTTP server**）；且其图像入参是**本地文件路径**或 data URL 到**它自己的 `/api/ask`**，`state` 语义也不同 | **需要新增第三种适配器（进程内/自定义 HTTP）** |
| `PlayJev` | ✗（无 `/v1/chat/completions`） | ★ **最近但不同形** | **需要一等适配器（小改）** |

### 若要用 `--agent=jev` 驱动 PlayJev，逐项差异（这就是"改动面"）

| 差异点 | 我们现有 `JevAgent` 发什么 | PlayJev 要什么 | 改动 |
|---|---|---|---|
| 图像载体 | `payload["image"] = "data:image/png;base64,..."`（**单数、顶层**） | `state.frames = ["data:image/jpeg;base64,...", ...]`（**数组、嵌在 state 里**） | 需按 `state` 分支：文本请求发 `state` 字符串，图像请求改发 `{"frames":[...]}` |
| `state` 字段 | 自由 JSON/字符串（我们渲染结构化状态） | 必须是 `{"frames":[...]}`；**文本 state 被 400 拒收** | 同上 |
| `questions` 形状 | 我们构造 typed map，`criteria` 可为 dict 或 list（NeoHorse 语义） | **只接受 `type:"choice"`**；`criteria` dict/list；**其余类型 400** | 图像路径上必须只发 choice |
| 返回解析 | `data.get("answers")` → dict，键为 qid，值含 `choice/probabilities/confidence`（NeoHorse） | **同形**（`answers` 是 dict，键为问题名，值 `{type,choice,probabilities,confidence}`） | **几乎无需改** |
| `abstain` | 我们可能读 `abstain` | **PlayJev 不返回** | 需容忍缺失 |
| 问题数 | 图像请求**强制 1 问**（L900–L913，否则报错，除非 `image_multi_question="trim"`） | 允许多问，但**串行 N 次 forward** | 策略选择 |
| `/health` 就绪探针 | 我们探 `GET <base>/health` | PlayJev 有 `/health`（L105）→ **兼容** | 无需改 |
| `/v1/models` | 我们**从不请求**（TASK-124 明确） | PlayJev 提供但不被调用 | 无需改 |

→ **PlayJev 的改动面 = 约 100–150 行、单文件、单适配器**：payload 分支（`state.frames` vs `state`+`image`）
+ 图像路径强制 choice + `abstain` 容错。**`decide()` 的解析主干、错误处理、限值校验可复用。**

→ **tinnel/OmniJev 的改动面更大**：它**不提供 HTTP 服务**，我们只有两条路：(a) 新增一个**进程内**适配器
（import `mso.infer`，`MSO1(ckpt, base)`，把我们的帧写成临时文件后调 `system_one({"images":[path]}, questions)`），
这会把推理**绑进 gate 进程**、要求 gate 跑在 GPU 机上；(b) 自己写一个薄 HTTP 包装（仓库外代码）。
另外它的 `choice` 语义多一个 `abstain`（对我们反而是**加分**：能表达"以上都不是"）。

---

## 12. Q11 — 选型建议（明确）

### 推荐：**② NeoHorse-Jev 文本状态为主 + 视觉模型补"画面判定"**；视觉侧**优先 PlayJev**，次选 tinnel/OmniJev 的 4B

**理由（按证据强度排序）**

1. **主路径不该换**：NeoHorse-Jev 的 **text-state Doom 10.60–14.40**（TASK-123）显著优于其 image-Doom
   的"接近随机"，说明"结构化状态"是当前唯一**有实测支撑**的判定通道。OmniJev 全部数字都是**官方自述的
   离线静态评测**，且官方自己声明"**not a matched-sample ablation**""**not new benchmark results**""
   **closed-loop … not been established**"。用它当**唯一**后端，等于把试玩门建在一组未经我们复现的数字上。
2. **视觉判定这一格确实是空的**，而且我们的诉求就是它（"当前在游戏验证反馈这块功能缺失无法保证游戏是
   可用运行的"）。以 OmniJev-4B 的 `game` 90.36 / `atari` 63.87 / `safety` 99.53 自述值看，
   "这一帧是不是游戏画面 / 有没有渲染出来 / 有没有错误弹窗 / 画面是否卡住"这类 **noul + score** 问题
   正好落在它的训练分布里，且**一次请求 1 图 N 问**（实测 3 问 0.18 s）比 NeoHorse 的 1 图 1 问好用得多。
3. **PlayJev 优先于 tinnel/OmniJev 作为"第一个"视觉后端**，因为：(a) 它**自带 `/v1/systemone`**，
   与我们已经实现的 `--agent=jev` **同一协议**，适配器最小；(b) 官方明确 **full fine-tuning**，
   视觉塔确实参与训练（Q3 唯一一条决定性证据在这边）；(c) **3 GB 推理显存**、H200 43 ms，
   单卡消费级可跑。(d) 它的弱点也明确且**对我们是可接受的**：只支持 `choice`、只有十款网页小游戏域、
   MMBench 0.78。
4. **tinnel/OmniJev-4B 作为"广域视觉判定"的第二选择**：覆盖手机/网页/机器人/视频/棋盘/音频，
   有 `score`/`noul`/region 选项与 `abstain`（可表达"以上都不是"，对"这画面根本不是游戏"极有用），
   且**权重小（306 MB 适配器）**。代价是无 HTTP 服务、需自建服务进程、无量化、Windows 记录为零。

**风险与被否决方案**

| 方案 | 判断 | 风险 / 否决理由 |
|---|---|---|
| ① OmniJev 主用于视觉判定（替换 NeoHorse） | **否决** | ① 若指 tinnel/OmniJev：无 HTTP 服务 + 视觉是否微调**未证实** + 全部数字为官方自述且官方自曝多处口径问题（Mario 43.52% vs 56.05%、OK-VQA 含 gold answer、genmcq 标签缺陷已撤回）；② 官方明确"**closed-loop gameplay … not established**"；③ 无量化/无 GGUF，Windows 记录为零 |
| ② NeoHorse 状态为主 + 视觉模型补视觉 | **推荐** | 风险：多一个后端 = 多一套健康检查/降级/证据链；两套协议的限值语义不同（1 图 1 问 vs 1 图 N 问）。**缓解**：视觉判定只做**独立的 noul/score 证据项**，不参与动作选择，失败不影响主判定 |
| ③ 仍只走状态、不引入视觉模型 | **备选（成本优先时）** | 风险：**明确保留"渲染层故障"盲区**（黑屏、花屏、UI 错位、卡在 loading——状态 JSON 完全可能正常）。若选③，**必须在门报告里显式记录该盲区**，并给出"我们接受它"的决策记录 |
| ④ 用 PlayJev 直接做**动作**选择 | **否决（超出本任务范围）** | PlayJev 只在**十款网页小游戏**上验证（`vs teacher mean 0.57`，Breakout 0.14 / Floppy 0.18）；我们的 Godot 游戏不在其分布内。它适合**判定**，不适合当万能玩家 |

**还需要什么信息才能定论（→ Q12）**：见下节。

---

## 13. Q12 — 未决问题（需要用户/发布方提供）

**用户侧（阻塞决策的）**

1. **"OmniJev" 到底指哪一个？** 任务书写 `tinnel123666888/OmniJev`，但描述（"做了视觉能力微调的类 Jev 模型"）
   更贴合 `OmniJev/PlayJev`（0.8B 全参微调 + 自带 `/v1/systemone`）。**两者结论不同**，请确认主对象或"两个都要"。
2. **部署机规格**：GPU 型号与显存、磁盘可用空间、OS（是否有 Linux 机器，还是必须在 Windows 上跑）。
   * 这直接决定选 4B（≈8–9 GB 显存 + 基座 ~8 GB 下载）还是 0.8B（≈2–3 GB）。
3. **HuggingFace 可达性/凭据**：本机 HF **完全不可达（HTTP 000，5 次实测）**。三档方案都需要
   **基座**（`Qwen/Qwen3.5-4B/2B/0.8B`）与 **adapter**；GitHub Release 只有 adapter + 头，
   **不含基座**。请提供：可用镜像（如 `hf-mirror`）、公司代理、或已落地的本地基座路径。
   * 注意：ModelScope **确认不存在**这两个模型的镜像（Q1 #29–#32，对照项 200）。
4. **许可证口径**：`LICENSE` 说基座是 `Qwen3-VL-4B-Instruct`，README/manifest 说是 `Qwen/Qwen3.5-4B`。
   需要发布方澄清，否则**基座许可证继承不了**（我们商用/再分发的合规审查会卡在这里）。
5. **是否接受"门进程绑 GPU 机"**：tinnel/OmniJev 无 HTTP 服务，若选它，我们需要自建服务或把推理
   绑进 gate 进程。请确认我们的部署拓扑允不允许。
6. **是否接受第三方模型的网络依赖**：视觉判定若走 `api1.omnijev.net`（公开 demo）意味着**把游戏截图发给
   第三方**，且该实例跑的是 `omnijev-0.5`（非 v1.1）。请确认数据合规与是否允许。

**发布方侧（影响可用性的）**

7. `tinnel123666888/OmniJev` 的**视觉塔是否参与训练**：请给出 `adapter_config.json` 的 `target_modules`
   或训练脚本；若是，请给出与 NeoHorse-Jev 同样的 `vision_finetuning` 类标志。
8. `tinnel/OmniJev` 的 **HTTP 服务端实现**在哪里（`/api/ask` 那套是否开源）？有无并发/动态批处理与请求体上限文档？
9. `PlayJev` 的 **HF 仓库是否 gated**、是否可离线取全量权重；`--two-frame` 权重是否另有 checkpoint。

**已明确 `unverifiable`（无法在本机闭环，非"未查"）**

* HF 模型卡的字段（`adapter_config.json` / `head_meta.json` / `model_manifest.json`）——**HF 本机不可达（000）**。
* 第三方独立评测——**未找到**（仅有 1 篇 CSDN 二手解读，未采用）。
* tinnel/OmniJev 的请求体上限、并发语义——**仓库内无 server 代码可核**。
* 4B BF16 的**实测**显存占用——**未下载权重**（本任务明令禁止），只能给量级推断。

---

## 14. Q1–Q12 覆盖对照（自检）

| 编号 | 状态 | 落点 |
|---|---|---|
| Q1 | ✅ 完成 | §1（37 条 URL + 状态码 + 字节数） |
| Q2 | ✅ 完成 | §2、§3 |
| Q3 | ⚠️ **主对象 `unverifiable`**（已给反向证据链）；PlayJev 有决定性证据 | §4 |
| Q4 | ✅ 完成（官方自述 + 自曝局限 + 实测图+多问题；第三方 `unverifiable`） | §5 |
| Q5 | ✅ 完成（逐文件字节 + SHA256 + 无量化/无 GGUF；HF 页 gated 与否 `unverifiable`） | §6 |
| Q6 | ✅ 完成（逐字命令 + 出处行号；两者均非 OpenAI 兼容） | §7 |
| Q7 | ✅ 完成（请求/响应形状，含实测 JSON） | §8 |
| Q8 | ✅ 完成（含 `unverifiable` 项） | §9 |
| Q9 | ✅ 完成（含推断标注） | §10 |
| Q10 | ✅ 完成（契合度矩阵 + 逐项差异 + 改动面估计） | §11 |
| Q11 | ✅ 完成（明确选②，含被否决方案与风险） | §12 |
| Q12 | ✅ 完成（6 条用户侧 + 3 条发布方侧 + 4 条 unverifiable） | §13 |

**验收判据自检（R1–R6）**

| 判据 | 自检 |
|---|---|
| R1 Q1–Q12 全有回答 | ✅ §14 对照表 |
| R2 关键结论有逐字原文引用（含 URL 与状态码） | ✅ 每节均带 URL + HTTP 码 + 字节数；原文用引用块 |
| R3 Q3 有决定性证据、非二手转述 | ⚠️ 对主对象**没有**决定性证据（HF 不可达），已**如实标注 `unverifiable` + 全部反向证据**，未把推断写成事实；对 PlayJev 有决定性原文（`full fine-tuning`） |
| R4 Q6 命令逐字可用 + 注明来源文件与路径 | ✅ §7（README 行号 / `mso/infer.py` L15–18 / `playjev/serve.py` L1–18 & L126–139） |
| R5 Q11 建议明确 | ✅ §12（选了②，给了理由、风险、被否决方案、还需什么信息） |
| R6 明写未下载权重/未装依赖/未改代码 + 命令清单 | ✅ §0 与 §15 |

---

## 15. 附录 A — 本次所用命令清单（可复现）与"未做"声明

**声明（逐条对应铁律）**
* **未下载任何权重**（GitHub Release 的 `.tar.gz` 只读取了 API 元数据里的 `size`/`sha256`/`download_count`，**没有 GET 其内容**）。
* **未安装任何依赖**（未执行任何 `pip install` / `hf download` / `git clone`）。
* **未修改任何仓库文件**（`F:\moonbit-hof-rs` 下只读；唯一写入是本报告 `recovery/reports/TASK-126-REPORT.md`）。
* **未改机器安全设置**（未关闭证书吊销检查，只在 curl 参数里加 `--ssl-no-revoke`）。
* **未使用任何 shell 重定向**（`>`、`>>`、`*>`、`2>&1` 全程零出现；落盘一律 `-o` / Python `open`）。
* 对 HuggingFace **恰好尝试 5 次**（1 次 API + 4 次 resolve），每次约 21s 超时；**未做长重试**。
* 探测全部落在 `%TEMP%\t126_*`，`%TEMP%` 目录名 `C:\Users\wyl\AppData\Local\Temp`。

**核心命令（GitHub / raw / 官网）**
```
curl.exe --ssl-no-revoke --max-time 60 -sS -o "%TEMP%\t126_repo.json"     -w "HTTP=%{http_code} size=%{size_download}\n" https://api.github.com/repos/tinnel123666888/OmniJev
curl.exe --ssl-no-revoke --max-time 60 -sS -o "%TEMP%\t126_contents.json" -w "HTTP=%{http_code} size=%{size_download}\n" https://api.github.com/repos/tinnel123666888/OmniJev/contents/
curl.exe --ssl-no-revoke --max-time 60 -sS -o "%TEMP%\t126_releases.json" -w "HTTP=%{http_code} size=%{size_download}\n" https://api.github.com/repos/tinnel123666888/OmniJev/releases
curl.exe --ssl-no-revoke --max-time 60 -sS -o "%TEMP%\t126_tree.json"     -w "HTTP=%{http_code} size=%{size_download}\n" "https://api.github.com/repos/tinnel123666888/OmniJev/git/trees/main?recursive=1"
curl.exe --ssl-no-revoke --max-time 60 -sS -o "%TEMP%\t126_README.md"     -w "HTTP=%{http_code} size=%{size_download}\n" https://raw.githubusercontent.com/tinnel123666888/OmniJev/main/README.md
curl.exe --ssl-no-revoke --max-time 60 -sS -o "%TEMP%\t126_README_zh.md"  -w "HTTP=%{http_code} size=%{size_download}\n" https://raw.githubusercontent.com/tinnel123666888/OmniJev/main/README_zh.md
curl.exe --ssl-no-revoke --max-time 60 -sS -o "%TEMP%\t126_requirements.txt" -w "HTTP=%{http_code} size=%{size_download}\n" https://raw.githubusercontent.com/tinnel123666888/OmniJev/main/requirements.txt
curl.exe --ssl-no-revoke --max-time 60 -sS -o "%TEMP%\t126_LICENSE"       -w "HTTP=%{http_code} size=%{size_download}\n" https://raw.githubusercontent.com/tinnel123666888/OmniJev/main/LICENSE
curl.exe --ssl-no-revoke --max-time 60 -sS -o "%TEMP%\t126_README_master.md" -w "HTTP=%{http_code} size=%{size_download}\n" https://raw.githubusercontent.com/tinnel123666888/OmniJev/master/README.md
:: 循环拉取 mso/infer.py, mso/video.py, mso/panels.py, mso/head.py, mso/branch.py, mso/templates.py,
::   mso/fast_kernels.py, docs/release_v11.json, docs/demos_v11.md, docs/v12_development.md  （各 HTTP=200）
curl.exe --ssl-no-revoke --max-time 60 -sS -o "%TEMP%\t126_playjev_repo.json" -w "HTTP=%{http_code} size=%{size_download}\n" https://api.github.com/repos/OmniJev/PlayJev
curl.exe --ssl-no-revoke --max-time 60 -sS -o "%TEMP%\t126_playjev_readme.md" -w "HTTP=%{http_code} size=%{size_download}\n" https://raw.githubusercontent.com/OmniJev/PlayJev/main/README.md
:: 循环拉取 playjev/serve.py, playjev/model.py, playjev/mixdata.py, docs/HF_MODEL_CARD.md, docs/DEMO.md,
::   scripts/general/eval_typesafe.py  （各 HTTP=200）
curl.exe --ssl-no-revoke --max-time 30 -sS -o "%TEMP%\t126_omnijev_site.html" -w "HTTP=%{http_code} size=%{size_download}\n" https://omnijev.net/
curl.exe --ssl-no-revoke --max-time 30 -sS -o "%TEMP%\t126_omnijev_try.html"  -w "HTTP=%{http_code} size=%{size_download}\n" https://omnijev.net/try.html
curl.exe --ssl-no-revoke --max-time 30 -sS -o "%TEMP%\t126_api_status.json"   -w "HTTP=%{http_code} size=%{size_download}\n" https://api1.omnijev.net/api/status
curl.exe --ssl-no-revoke --max-time 30 -sS -o "%TEMP%\t126_api_presets.json"  -w "HTTP=%{http_code} size=%{size_download}\n" https://api1.omnijev.net/api/presets
curl.exe --ssl-no-revoke --max-time 30 -sS -o "%TEMP%\t126_preset_phone.png"  -w "HTTP=%{http_code} size=%{size_download} type=%{content_type}\n" https://api1.omnijev.net/api/preset_img/phone
:: 多问题实测（POST body 由 write 工具写 JSON，图片用 Python base64，落盘用 Python open，无重定向）
python  %TEMP%\t126_ask.py        :: POST https://api1.omnijev.net/api/ask  → HTTP 200, 785 B, 3 问
```
**HF / ModelScope 探测（不可达与对照）**
```
curl.exe --ssl-no-revoke --max-time 25 -sS -o "%TEMP%\t126_hf_api.json" -w "HTTP=%{http_code} size=%{size_download} time=%{time_total}\n" https://huggingface.co/api/models/tinnel123/OmniJev
::   → HTTP=000 size=0 time=21.097568   curl: (28) Failed to connect to huggingface.co port 443 after 21082 ms
:: 4 次 resolve 探测：https://huggingface.co/tinnel123/OmniJev/resolve/v1.1/{adapter_config.json,head_meta.json,README.md,model_manifest.json}
::   → 均 HTTP=000（各约 21s）
curl.exe --ssl-no-revoke --max-time 40 -sS -o "%TEMP%\t126_ms_omnijev.json" -w "HTTP=%{http_code} size=%{size_download}\n" "https://modelscope.cn/api/v1/models/tinnel123/OmniJev"                       :: → 404 / 152 B
curl.exe --ssl-no-revoke --max-time 40 -sS -o "%TEMP%\t126_ms_files.json"   -w "HTTP=%{http_code} size=%{size_download}\n" "https://modelscope.cn/api/v1/models/tinnel123/OmniJev/repo/files?Revision=master&Recursive=true"  :: → 404 / 155 B
curl.exe --ssl-no-revoke --max-time 40 -sS -o "%TEMP%\t126_ms_playjev.json" -w "HTTP=%{http_code} size=%{size_download}\n" "https://modelscope.cn/api/v1/models/OmniJev/PlayJev-0.8B"                    :: → 404 / 152 B
:: 对照项（证明 ModelScope 本身可达）
curl.exe --ssl-no-revoke --max-time 40 -sS -o "%TEMP%\t126_ms_ping.json"    -w "HTTP=%{http_code} size=%{size_download}\n" "https://modelscope.cn/api/v1/models/Qwen/Qwen2.5-0.5B-Instruct"          :: → 200 / 13474 B
curl.exe --ssl-no-revoke --max-time 40 -sS -o "%TEMP%\t126_ms_control3.json" -w "HTTP=%{http_code} size=%{size_download}\n" "https://modelscope.cn/api/v1/models/AI-ModelScope/stable-diffusion-v1-5/repo/files?Revision=master&Recursive=false"  :: → 200 / 5379 B
```

## 16. 附录 B — 本机事实与便于复核的一手读数

* 读 `F:\moonbit-hof-rs\godot-mcp\recovery\tasks\TASK-126.md`（1–99 行）作为任务书；同期**未触碰**
  `tools/playtest_agent.py`、`recovery/tasks/TASK-124.md`、`recovery/tasks/TASK-125.md`（仅**只读**查阅
  `playtest_agent.py` 与 `TASK-124.md`/`TASK-124-REPORT.md` 以判定 Q10 契合度）。
* 公开 demo 服务实测：`POST /api/ask` → **HTTP 200, 785 B, 3 问, `wall_s=0.1793`, `queued_s=0.0`**；
  `GET /api/status` → **HTTP 200**，`{"service":"omnijev","status":"ready","ready":true,"model":"omnijev-0.5","device":"cuda:0","loading_s":34.9,"queue":0,"asks":353}`。
* 探测期间 GitHub API 未触发限流（全部 200，无 `X-RateLimit-Remaining: 0` 反馈）；`search/code` 返回
  **401**（需要 token，未使用 token，故放弃该路径）。

---

*报告结束。若需我继续（例如把 Q11 落成详细设计、或复现 PlayJev 的 3 GB 推理路径），请另行下发任务书；
本报告不含任何未标注来源的推断。*
