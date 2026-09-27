# TASK-127 — 部署 PlayJev（视觉判定后端）：定位/校验权重 → 本地部署 → 最小适配器 → 本地端到端实测

* **状态**：**done**（P1–P10 全部有证据；无第三方端点；无破坏性命令；未动 Jev）
* **执行**：子代理（自包含执行 TASK-127）；报告落点由任务书 §5 指定
* **日期**：2026-09-27
* **一句话**：PlayJev 0.8B 的源码/GitHub 元数据/权重/许可全部定位并逐文件 SHA256 对表；
  权重经**镜像 `hf-mirror.com`** 取得（直连 HuggingFace 本机 000，镜像 200 —— 因此**没有**触发
  "只在 HF 就停下"的分支）；WSL2 内独立 venv `/opt/playjev-venv` + 独立端口 **8081** 服务就绪，
  **8080 的 Jev 全程存活**；`playjev/serve.py` 的真实协议逐字抄录并与 JevAgent 假设逐条对照；
  新增 `--agent=playjev` 适配器（`jev`/`openai`/`scripted` 无回归）；用**我们自己游戏的截图**完成
  **1 图 + 3 问**本地实测。

---

## 0. 结论先行（三件必须让人知道的事）

1. **权重拿到了，来源是镜像**：`huggingface.co` 在 Windows 侧 **HTTP 000**（21 秒连接超时，实测）；
   `hf-mirror.com` **HTTP 200**（Windows 与 WSL 内都可达）。所以权重**不是**"只在不可达的 HF"，
   任务书 §2.2 的"停下"分支**不适用** —— 我按"候选镜像方案"实际走通了镜像并**逐文件 SHA256 对表**。
2. **PlayJev 的 `serve.py` 里根本没有 `abstain`**（请求与响应都没有）。任务书 §0/§2.4/§2.5 里
   "`abstain` 容错"那条来自二手摘要，**与仓库真实代码不符**。适配器因此**自建** abstain 语义
   （服务端声明 / 缺答案 / 置信度低于阈值 三条规则），并**对真实服务构造出了一次真的 abstain**（§7.3）。
   同时记录一条**上游可改进点**：`playjev/model.py:102` 的 `allowed_mass`（"落在 K 个答案槽上的
   全词表 softmax 质量份额"）其实才是"模型到底有没有在回答"的诊断量，而 `serve.py` 把它**丢掉了**。
3. **一个必须上报的实测结论**：用我们自己的 Godot 截图（**分布外**：PlayJev 只在 10 个浏览器小游戏上微调过），
   **`playable` 维度可用**（3 张退化帧的 P(yes) 全部 ≈0.20 < 0.5，真实帧 0.48–0.85），
   但我构造的 **`brokenness` 维度在方向上错了**（黑屏 2.41 "比" 真实 snake 帧 3.97 还好）。
   即：**"画面是否可用"能用，我这一版"损坏度打分"不能用**。见 §7.2 与 §10。

---

## 1. 定位过程与 HTTP 状态码（P1 前半）

全部请求**从 Windows 侧**发出（任务书要求的现实：Windows 侧 GitHub 可达、WSL 内 GitHub 不可达）。
命令一律用 `curl.exe -sSL --ssl-no-revoke`（`--ssl-no-revoke` 是 must，否则本机 TLS 失败），
`-o` 落盘（**无 shell 重定向**），`-w` 打印状态码与字节数。原始响应体留档在
`runs/playability/`（`F:\moonbit-hof-rs\runs\playability\`，该目录不入库）。

| # | URL | HTTP | 字节 | 留档 |
|---|---|---:|---:|---|
| 1 | `https://api.github.com/repos/OmniJev/PlayJev` | **200** | 7005 | `playjev-repo.json` |
| 2 | `https://api.github.com/repos/OmniJev/PlayJev/contents/` | **200** | 7700 | `playjev-contents.json` |
| 3 | `https://raw.githubusercontent.com/OmniJev/PlayJev/main/README.md` | **200** | 17032 | `playjev-readme.md` |
| 4 | `https://api.github.com/repos/OmniJev/PlayJev/releases` | **200** | 5 (`[]`) | `playjev-releases.json` |
| 5 | `https://huggingface.co/api/models/OmniJev/PlayJev-0.8B` | **000** | 0 | — |
| 6 | `https://hf-mirror.com/api/models/OmniJev/PlayJev-0.8B` | **200** | 16714 | `hfmirror-playjev.json` |
| 7 | `https://hf-mirror.com/api/models/OmniJev/PlayJev-0.8B/tree/main` | **200** | 1621 | `hfmirror-tree.json` |
| 8 | `https://modelscope.cn/api/v1/models/OmniJev/PlayJev-0.8B` | **404** | 152 | `ms-playjev.json` |
| 9 | `https://modelscope.cn/api/v1/dolphin/models?...Name=PlayJev` | **404** | 18 | `ms-search.json` |

* #5 `HTTP 000` 的 stderr 原文：`curl: (28) Failed to connect to huggingface.co port 443 after
  21045 ms: Could not connect to server`。**只试了 1 次**（任务书要求不超过 3 次）。
* #8/#9：**ModelScope 上没有 PlayJev**（404）。所以候选镜像里 ModelScope 这条路**不存在**。
* #4：**GitHub Releases 为空数组** —— 权重**不在 GitHub Release**，只在 HuggingFace。

**仓库元数据（逐字字段）**

```text
full_name          OmniJev/PlayJev
html_url           https://github.com/OmniJev/PlayJev
default_branch     main
created_at         2026-09-17T20:37:50Z
pushed_at          2026-09-24T11:19:41Z
license.spdx_id    Apache-2.0
stargazers_count   40
forks_count        2
language           JavaScript
size               84091
```

**克隆与锚点**：整仓 `git clone --depth 1` 到
`F:\moonbit-hof-rs\runs\playability\PlayJev-src`（3,623 文件 / 134 MB），
`git rev-parse HEAD` = **`ea3a514d2fcbc0756c36eabe052439db54544542`**
（`2026-09-24 19:19:35 +0800`，subject `Training records live in the model repo's data/`）。
本报告一切"`serve.py:NN`"均指该提交下的 `playjev/serve.py`。

**网络现实复测（WSL 内，用于选下载路径）**

| 目标 | 结果 |
|---|---|
| `https://pypi.org/simple/` | 200 |
| `https://pypi.tuna.tsinghua.edu.cn/simple/` | 200 |
| `https://download.pytorch.org/whl/cu128/torch/` | 200 |
| `https://hf-mirror.com/api/models/OmniJev/PlayJev-0.8B` | 200 |
| `https://github.com` | **000**（`curl: (7) ... port 443 after 7 ms: Could not connect`） |

→ 与 TASK-125/126 的结论一致：**WSL 内 GitHub 不可达，HF 镜像可达**。因此
"GitHub 产物在 Windows 侧取、再拷进 WSL"这条我遵守了（源码经 `/mnt/f/...` 从 Windows 侧克隆目录拷入
WSL，WSL 内**没有**访问 GitHub）；而权重走 **hf-mirror**（不是 GitHub），两侧都可达，直接由
Windows 侧 curl 落盘到 `F:\models\PlayJev-0.8B`（与既有 `F:\models\NeoHorse-Jev-4B` 同一约定，仓库之外）。

---

## 2. 权重与许可（P1 后半、P2、P3）

### 2.1 权重位置与逐文件大小

**位置**：HuggingFace `OmniJev/PlayJev-0.8B`（`sha` = `a7348002b1e159add7037d6d50812cd4db2d96e9`，
`lastModified 2026-09-24T11:19:18Z`，`gated: false`，`private: false`，`downloads: 672`，`likes: 2`）。
**GitHub Releases 为空**；**ModelScope 无此模型**。

`/api/models/.../tree/main` 的逐文件清单（`size` 为 HF 报的字节数）与我们实际下载的结果：

| 文件 | HF 报字节 | 本地实得字节 | 一致 |
|---|---:|---:|---|
| `model.safetensors` | 2,214,590,296 | 2,214,590,296 | ✅ |
| `tokenizer.json` | 19,989,325 | 19,989,325 | ✅ |
| `config.json` | 2,730 | 2,730 | ✅ |
| `chat_template.jinja` | 7,755 | 7,755 | ✅ |
| `processor_config.json` | 1,221 | 1,221 | ✅ |
| `generation_config.json` | 116 | 116 | ✅ |
| `playjev_train.json` | 6,771 | 6,771 | ✅ |
| `.gitattributes` | 3,710 | 3,710 | ✅ |
| `README.md` | 10,193 | 10,193 | ✅ |
| `assets/`（目录） | — | **未下载**（只是 README 的图） | — |
| `data/`（目录） | — | **未下载**（853 MB 训练记录，推理不需要） | — |
| **推理合计** | | **2,234,501,917 B ≈ 2.08 GiB** | |

落点：`F:\models\PlayJev-0.8B\`（**仓库之外**，与 `F:\models\NeoHorse-Jev-4B` 同级；
任务书 §3.7 要求权重不入库 —— 本报告 §9 给出 `git check-ignore` 证据）。

### 2.2 是否有 SHA256SUMS —— 没有，但**仍能逐文件对表**

HF 仓库里**没有 `SHA256SUMS`**。但 HF 为 LFS 文件在树 API 里给出了 **LFS `oid`，它就是文件的 sha256**。
我用它作为权威期望值，逐文件实算 `Get-FileHash -Algorithm SHA256`：

```text
model.safetensors
  actual   = efe4d2c51ea8c0e8583fa4f08da486f8f674999f94bb6b007ef38aca792835f0
  expected = efe4d2c51ea8c0e8583fa4f08da486f8f674999f94bb6b007ef38aca792835f0   ✅
tokenizer.json
  actual   = 06b9509352d2af50381ab2247e083b80d32d5c0aba91c272ca9ff729b6a0e523
  expected = 06b9509352d2af50381ab2247e083b80d32d5c0aba91c272ca9ff729b6a0e523   ✅
```

其余 7 个非 LFS 小文件**字节数逐一相符**（上表），且 `model.safetensors` 的字节数也与 HF 报的
2,214,590,296 完全相同。下载用 `curl -sSL --retry 5 --retry-delay 3 -C -`（**可续传**），
`model.safetensors` 走后台 job，中途查过一次进度（731 MB → 909 MB → 2,172 MB → 完成）。

### 2.3 许可与基座（P2）

* GitHub 仓库 `LICENSE` = **Apache License 2.0**（11,560 B，sha256
  `3DDF9BE5C28FE27DAD143A5DC76EEA25222AD1DD68934A047064E56ED2FA40C5`），
  首行原文：`                                 Apache License` / `                           Version 2.0, January 2004` /
  `                        http://www.apache.org/licenses/`。
* HF 模型卡 front-matter 原文：

  ```yaml
  license: apache-2.0
  base_model: Qwen/Qwen3.5-0.8B-Base
  pipeline_tag: image-text-to-text
  library_name: transformers
  ```

* 仓库 README §Licence and Credits **逐字原文**（`README.md:239`）：

  > Code and trained weights: Apache-2.0.

* **基座 = `Qwen/Qwen3.5-0.8B-Base`**（HF API `tags` 里同时有
  `base_model:Qwen/Qwen3.5-0.8B-Base` 与 `base_model:finetune:Qwen/Qwen3.5-0.8B-Base`，
  `config.architectures = ["Qwen3_5ForConditionalGeneration"]`，`model_type = qwen3_5`）。
  README `README.md:24` 原文：`PlayJev is Qwen3.5-0.8B-Base fine-tuned to play ten classic
  browser games from raw pixels.`
* **视觉确证参与训练**（任务书 §0 的关切）—— `playjev_train.json`（随权重一起发布，逐字）：

  ```json
  "freeze_vision": false,   "two_frame": false,   "stack": "temporal",
  "lr": 1e-05,  "batch": 64,  "epochs": 1,  "kmax": 9,
  "records": 1127435, "train": 1019325, "val": 108110, "step": 26544,
  "eval": { "all": {"n": 2000, "loss": 0.7271567829175669,
                    "agreement": 0.7835, "agreement_top": 0.8175} }
  ```

  `freeze_vision: false` = 视觉塔**未冻结**；README `README.md:167` 的 "full fine-tuning" 与之一致。
  另有 `aux_image: 0.551` / `aux_text: 0.7185`（通用图文混训的评测值）。
* **能否本地商用/研究用**：Apache-2.0，允许商用与再分发，需保留许可与声明。
  ⚠️ 一条**必须留给用户的注意**：仓库 README `README.md:241-259` 明确说十个小游戏是**第三方 vendored**
  （Mario 精灵属 Nintendo、Floppy Bird 美术属 Dong Nguyen/.GEARS、Racer 是 Mega Drive OutRun 的占位美术），
  "the licence above covers the code each author wrote"。因此 **Apache-2.0 覆盖的是代码与训练权重**，
  游戏美术**不在**授权范围内 —— 我们只把它当推理模型用、不外发游戏素材，不受影响。

---

## 3. 部署记录（P4、P5）

### 3.1 独立 venv（`/opt/playjev-venv`）—— 未动 `/opt/jev-venv`

```text
uv venv --python 3.12 /opt/playjev-venv          # → Python 3.12.13 (CPython)
```

Python 3.12 用的是 uv **已经装在机器上的** `cpython-3.12.13-linux-x86_64-gnu`
（`/root/.local/share/uv/python/`），**没有**联网重新下载解释器（也避免了 WSL 内 GitHub 不可达的坑）。

安装（两条，均为**下载**阶段，后台 job；`torch` 走 cu128 索引，其余走 PyPI）：

```text
uv pip install --python /opt/playjev-venv/bin/python \
    --index-url https://download.pytorch.org/whl/cu128 torch==2.10.0 torchvision==0.25.0
    # Resolved 31 packages in 7m 16s ... Installed 31 packages
uv pip install --python /opt/playjev-venv/bin/python --index-url https://pypi.org/simple \
    transformers==5.17.0 accelerate==1.15.0 pillow einops numpy==2.5.3 safetensors==0.8.0 tokenizers==0.23.2
    # Resolved 56 packages in 4.03s ... Installed 27 packages
```

`uv pip freeze` 关键行（P4 证据）：

```text
torch==2.10.0+cu128          torchvision==0.25.0+cu128
transformers==5.17.0         tokenizers==0.23.2
accelerate==1.15.0           safetensors==0.8.0
numpy==2.5.3                 pillow==12.3.0
einops==0.8.2                triton==3.6.0
huggingface-hub==1.33.0      hf-xet==1.6.0          cuda-bindings==12.9.4
```

**按 `requirements.txt` 有意未装的三项及理由**（如实声明）：
`flash-linear-attention==0.5.2`、`playwright==1.63.0`、`peft==0.21.0`。
前两者只服务训练/采集/回放（`playjev/collect.py`、`rebuild.py`、`env.py`），
`playjev/model.py:146` 对 `fla`/`causal_conv1d` 只是 `importlib.util.find_spec` 探测（可选加速核）；
`peft` 只服务训练。**推理路径不 import 它们**（§3.3 的导入自检通过即为证）。
`triton` 由 torch 2.10.0 自身拉为 3.6.0（`requirements.txt` 写 3.7.1 是训练机的 pin），不影响推理。

**`/opt/jev-venv` 未被触碰的机器证据**：

```text
$ ls -ld /opt/jev-venv
drwxr-xr-x 5 root root 4096 Sep 27 16:59 /opt/jev-venv
$ stat -c '%y %n' /opt/jev-venv/pyvenv.cfg
2026-09-27 16:56:35.061419372 +0800 /opt/jev-venv/pyvenv.cfg        ← 与 TASK-125 建库时刻相同
$ du -sh /opt/jev-venv /opt/playjev-venv
6.7G    /opt/jev-venv
7.0G    /opt/playjev-venv
```

### 3.2 源码落点

`/opt/playjev/`（**仓库之外**）：`playjev/` 包（从 Windows 侧克隆目录 `/mnt/f/.../PlayJev-src/playjev`
拷贝，**WSL 内没有访问 GitHub**）+ `requirements.txt` + `LICENSE`。
权重 `/mnt/f/models/PlayJev-0.8B`（= `F:\models\PlayJev-0.8B`）。

### 3.3 环境自检（导入 + CUDA）

```text
python        3.12.13
torch         2.10.0+cu128 | cuda build 12.8
cuda available True
gpu           NVIDIA GeForce RTX 4090
transformers  5.17.0
tokenizers    0.23.2
safetensors   0.8.0
PIL           12.3.0
numpy         2.5.3
playjev.model  /opt/playjev/playjev/model.py
playjev.serve  /opt/playjev/playjev/serve.py
PROMPT_VERSION playjev-letters-v1
DEFAULT_INSTRUCTIONS Which move should the player make next?
```

（脚本：`runs/playability/_playjev_envcheck.py`，`runs/` 不入库。）

### 3.4 起服务：8081，detached，无 shell 重定向

端口先查占用：8080 已被 `neohorse-decisi`（pid 730）占用，**8081 空闲**。

启动器：`godot-mcp/tools/playjev_serve_wsl.py`（**新文件**，WSL 侧运行；复用 TASK-125
`F:\models\_serve_detached.py` 的 `start_new_session=True` 模式，日志由 Python 打开写出，
**全程零 shell 重定向**）：

```text
$ python3 /mnt/f/moonbit-hof-rs/godot-mcp/tools/playjev_serve_wsl.py 8081 detached
PID=1771
LOGPATH=/mnt/f/moonbit-hof-rs/godot-mcp/runs/playability/playjev-serve-detached-20260927-184407.log
```

日志尾部原文（加载 14.0 s）：

```text
# $ /opt/playjev-venv/bin/python -m playjev.serve --ckpt /mnt/f/models/PlayJev-0.8B \
      --host 0.0.0.0 --port 8081 --name playjev-0.8b --verbose
# cwd=/opt/playjev  PYTHONPATH=/opt/playjev  CUDA_VISIBLE_DEVICES=0
...
playjev.serve: playjev-0.8b from /mnt/f/models/PlayJev-0.8B on http://0.0.0.0:8081/v1/systemone
  (one frame per decision, loaded in 14.0 s)
127.0.0.1 - - [27/Sep/2026 18:45:11] "GET /health HTTP/1.1" 200 -
127.0.0.1 - - [27/Sep/2026 18:45:11] "GET /v1/models HTTP/1.1" 200 -
```

### 3.5 就绪判据（P5）

8081 的 `/health` **逐字原文**：

```json
{"ok": true, "model": "playjev-0.8b", "two_frame": false}
```
`HTTP:200`。

8081 的 `GET /v1/models` 逐字原文（`serve.py:103-104`，**Jev 没有这个端点**）：

```json
{"object": "list", "data": [{"id": "playjev-0.8b", "object": "model", "owned_by": "playjev"}]}
```

**8080 的 Jev 仍存活**（同一时刻复测，两次）：

```text
$ curl -sS --max-time 10 http://127.0.0.1:8080/health
{"status":"ready","model":"NeoHorse-Jev-4B","input_modalities":["text","image"]}   HTTP:200
$ curl ... http://127.0.0.1:8080/v1/models
models8080 HTTP:404                    ← 仍然没有 /v1/models，与厂商文档一致
$ ss -ltnp | grep -E '8080|8081'
LISTEN 0 2048 0.0.0.0:8080 0.0.0.0:* users:(("neohorse-decisi",pid=730,fd=23))
LISTEN 0 5    0.0.0.0:8081 0.0.0.0:* users:(("python",pid=1771,fd=20))
$ pgrep -af neohorse-decision
730 /opt/jev-venv/bin/python /opt/jev-venv/bin/neohorse-decision serve --model-dir /mnt/f/models/NeoHorse-Jev-4B --host 0.0.0.0 --port 8080
```

显存：起 PlayJev 前 `15621 MiB / 24564`，起后 `19272–19246 MiB / 24564`
（PlayJev 约占 **3.6 GB**，与厂商记录的"推理约 3 GB"相符）。

---

## 4. `playjev/serve.py` 真实协议逐字摘录（P6 前半）

> 文件：`/opt/playjev/playjev/serve.py`（= `OmniJev/PlayJev` @
> `ea3a514d2fcbc0756c36eabe052439db54544542`），147 行。以下引号内均为**逐字原文**，行号为该文件行号。

### 4.1 端点（`serve.py:102-112`）

```python
102    def do_GET(self):
103        if self.path.rstrip("/") == "/v1/models":
104            self._send(200, {"object": "list", "data": [{"id": self.engine.name, "object": "model", "owned_by": "playjev"}]})
105        elif self.path.rstrip("/") in ("", "/health"):
106            self._send(200, {"ok": True, "model": self.engine.name, "two_frame": self.engine.two_frame})
107        else:
108            self._send(404, {"error": "not found"})
110    def do_POST(self):
111        if self.path.rstrip("/") != "/v1/systemone":
112            return self._send(404, {"error": "not found"})
```

* **只有 3 个端点**：`GET /v1/models`、`GET /health`、`POST /v1/systemone`（外加 `OPTIONS`，`serve.py:99-100`，CORS 全开 `serve.py:94-97`）。
* **`/health` 的形状是 `{"ok": ...}`，不是 Jev 的 `{"status": "ready", ...}`。**
* `GET /health` 与 `GET /` 等价（`rstrip("/") in ("", "/health")`）。

### 4.2 请求体：`state.frames`（`serve.py:6-10` 文档串 + `39-63` 实现）

文档串逐字（`serve.py:6-13`）：

```text
Request (the shape playjev.play ServerPolicy and the demo page send; TypeSafe's request with frames in the state):
  {"model": "playjev-latest",
   "state": {"frames": ["data:image/jpeg;base64,...", ...]},          # one frame, or (previous, current)
   "questions": {"q": {"type": "choice", "instructions": "Which move should the player make next?",
                       "criteria": {"up": "turn the snake to move up", ...}}}}
Response:
  {"model": "playjev-0.8b", "answers": {"q": {"type": "choice", "choice": "up", "probabilities": {"up": 0.9, ...},
   "confidence": 0.87}}, "timing": {"prep_ms": 5.1, "forward_ms": 38.2, "visual_tokens": 182}}
```

实现逐字：

```python
31    @staticmethod
32    def _frame_bytes(s):
33        if not isinstance(s, str) or not s:
34            raise ValueError("each frame must be a base64 string or a data URL")
35        if s.startswith("data:"):
36            s = s.split(",", 1)[1] if "," in s else ""
37        return base64.b64decode(s)
39    def answer(self, body):
40        state = body.get("state")
41        if not isinstance(state, dict) or not isinstance(state.get("frames"), list) or not state["frames"]:
42            raise ValueError("state must be {\"frames\": [...]} with at least one frame; text states belong to OpenJev")
43        frames = [self._frame_bytes(f) for f in state["frames"]]
44        if self.two_frame:
45            item = (frames[-2], frames[-1]) if len(frames) >= 2 else (frames[-1], frames[-1])
46        else:
47            item = frames[-1]
48        questions = body.get("questions")
49        if not isinstance(questions, dict) or not questions:
50            raise ValueError("questions must be a non-empty object")
51        answers, timing = {}, {}
52        for qname, q in questions.items():
53            if not isinstance(q, dict) or q.get("type", "choice") != "choice":
54                raise ValueError(f"question {qname!r}: only type \"choice\" is served")
55            crit = q.get("criteria")
56            if isinstance(crit, dict):
57                options = [{"name": str(k), "description": str(v)} for k, v in crit.items()]
58            elif isinstance(crit, list):
59                options = [{"name": str(k), "description": str(k)} for k in crit]
60            else:
61                raise ValueError(f"question {qname!r}: criteria must be an object or a list")
62            if len(options) < 2:
63                raise ValueError(f"question {qname!r}: a choice needs at least two options")
64            instructions = str(q.get("instructions") or DEFAULT_INSTRUCTIONS)
65            with self.lock:
66                d = self.m.decide([item], options, instructions=instructions,
67                                  frames_per_state=2 if self.two_frame else 1, stack=self.stack, batch_size=1)[0]
68                t = self.m.last_timing
69            answers[qname] = {"type": "choice", "choice": options[d.choice]["name"],
70                              "probabilities": {o["name"]: round(p, 6) for o, p in zip(options, d.probs)},
71                              "confidence": round(d.confidence, 6)}
72            timing = {"prep_ms": round(t.prep_s * 1000, 1), "forward_ms": round(t.forward_s * 1000, 1),
73                      "input_tokens": t.input_tokens, "visual_tokens": t.visual_tokens}
74        return {"model": self.name, "answers": answers, "timing": timing}
```

**由此可读出的硬事实：**

| 事实 | 出处 |
|---|---|
| 帧可以是裸 base64 **或** `data:` URL；`data:` 只看第一个逗号右边 | serve.py:35-36 |
| 空/非字符串帧 → `ValueError` → **400** | serve.py:33-34, 120-121 |
| **文本 state 被拒**：`text states belong to OpenJev` → 400 | serve.py:41-42 |
| 帧数组取 `frames[-1]`（单帧模式）；`--two-frame` 时取 `(frames[-2], frames[-1])`，只有 1 帧则自我配对 | serve.py:44-47 |
| `questions` 必须是非空对象 → 否则 400 | serve.py:49-50 |
| **只服务 `type: "choice"`**；`type` 缺省视为 choice；`noul`/`score` → 400 | serve.py:53-54 |
| `criteria` 允许 **dict**（name→description）或 **list**（name==description） | serve.py:55-59 |
| **至少 2 个选项**，否则 400 | serve.py:62-63 |
| `instructions` 缺省用 `DEFAULT_INSTRUCTIONS` = `"Which move should the player make next?"` | serve.py:64 + model.py:37 |
| **一次 forward 一把锁**（`self.lock`），串行 | serve.py:29, 65-68 |
| 概率是 **float32 softmax 只取 K 个答案槽** 后再归一，形状 `{选项名: p}`；`confidence` = Jev 的 choice 统计量 `(p_max − 1/K)/(1 − 1/K)` | serve.py:69-71 + model.py:6, 90-94 |
| 答复 `timing` 只有 **最后一个问题** 的值（循环内被反复覆盖），`total_ms` 由 handler 补 | serve.py:72-73, 118 |
| **`model` 请求字段从不被读**；答复里的 `model` 是启动时 `--name` | serve.py:74（`self.name`），全文无 `body["model"]` |

### 4.3 响应与错误码（`serve.py:85-123`）

```python
110    def do_POST(self):
111        if self.path.rstrip("/") != "/v1/systemone":
112            return self._send(404, {"error": "not found"})
113        try:
114            n = int(self.headers.get("Content-Length") or 0)
115            body = json.loads(self.rfile.read(n) or b"{}")
116            t0 = time.perf_counter()
117            out = self.engine.answer(body)
118            out["timing"]["total_ms"] = round((time.perf_counter() - t0) * 1000, 1)
119            self._send(200, out)
120        except ValueError as e:
121            self._send(400, {"error": str(e)})
122        except Exception as e:  # a bad frame must not take the server down
123            self._send(500, {"error": f"{type(e).__name__}: {e}"})
```

* **错误码只有 400（ValueError）与 500（其它）+ 404（路径不对）**。
* **没有 429/529 忙协议**（Jev 有）—— 引擎锁让请求**排队**而不是拒。
* **没有请求体积上限、没有 token 上限、没有问题条数上限**（Jev 有 1 MiB / 2048 token / 16 问）。
  唯一的数量约束是**每问 ≥2 个选项**（serve.py:62）与 **≤26 个选项**（model.py:45，
  `LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"`）。
* 坏帧**不会让服务崩**（`except Exception` 兜到 500）。

### 4.4 `abstain` 在协议里**不存在**（关键纠正）

对 `playjev/serve.py` 全文检索 `abstain`：**0 处命中**（请求侧 0、响应侧 0）。
`serve.py` 每个答案只有 4 个键：`type` / `choice` / `probabilities` / `confidence`（serve.py:69-71）。

而 `playjev/model.py:97-104` 的 `Decision` 里其实有更有用的诊断量：

```python
 97  @dataclass
 98  class Decision:
 99      probs: list[float]  # over the options, in the order given
100      choice: int  # argmax index into options
101      confidence: float  # Jev Choice confidence
102      allowed_mass: float  # share of the full-vocabulary softmax that lands on the K answer slots
103      top_token: str  # most likely next token over the whole vocabulary (diagnostic: is the model answering at all?)
```

`allowed_mass` 与 `top_token` 都**没有**被 `serve.py` 放进 HTTP 答复 —— 即
**"模型到底有没有在回答"这个最该用于 abstain 判定的信号被上游丢掉了**。
这构成一条给上游的具体建议（§10 R4），也是我们适配器只能退而用 `confidence` 的原因。

### 4.5 是否支持"1 图多问" —— **支持**（与 Jev 相反）

`serve.py:16` 文档串逐字：`the frames are shared by all questions of one request`。
实现上 `frames` 在循环外算好（serve.py:43-47），循环里只换 `questions`（serve.py:52-73）。
所以**一次请求 = 1 帧 + N 个 choice 问**，正是任务书 §2.5 要的形状。
（Jev 的硬规则恰恰相反：图像请求**必须恰好 1 图 1 问**。）

---

## 5. 与 `JevAgent` 既有假设的逐条差异（P6 后半）

适配器动手前，我先把 `tools/playtest_agent.py` 里 `JevAgent` 的假设列出来，再逐条对 `serve.py` 核。
**结论：差异足够大，必须是独立后端，不能给 `JevAgent` 加一个 flag。**

| # | JevAgent 的假设（改动前代码） | PlayJev `serve.py` 的真实行为 | 差异性质 |
|---|---|---|---|
| 1 | `payload = {"model", "state", "questions"}`，`state` 是**字符串/对象**（`jev_render_state`，playtest_agent.py:586-595, 915） | `state` **必须是 `{"frames": [...]}`**；文本 state 被 400 拒绝（serve.py:41-42） | **破坏性** |
| 2 | 图像放**顶层 `image`** 字段，`"data:image/png;base64,..."`（playtest_agent.py:924） | 图像放 **`state.frames[]`**；顶层 `image` 字段**根本不读**（serve.py 全文无 `image`） | **破坏性** |
| 3 | 问题类型 `noul` / `choice` / `score`（playtest_agent.py:791-824） | **只有 `choice`**；`noul`/`score` → 400（serve.py:53-54） | **破坏性** |
| 4 | 图像请求**恰好 1 图 1 问**，多问默认报错（`image_multi_question`，playtest_agent.py:896-913） | **1 图 N 问是合法且被鼓励的**（serve.py:16） | **破坏性（反向）** |
| 5 | `criteria` 对 choice 是 name→description 的 dict，1..255 项 | dict **或 list** 都行，**≥2**，**≤26**（serve.py:55-63 + model.py:38,45） | 收窄 |
| 6 | `/health` 判 `{"status": "ready"}`（playtest_agent.py:722-736） | `{"ok": true, "model", "two_frame"}`（serve.py:106） | **形状不同** |
| 7 | 「`/v1/models` is not provided」，从不调用（playtest_agent.py:722 注释） | **`/v1/models` 存在**（serve.py:103-104） | 反向 |
| 8 | 忙 → **429/529 + `Retry-After`** 退避重试（playtest_agent.py:738-766） | **无忙协议**，锁内排队；错误码只有 400/404/500（serve.py:110-123） | 无对应物 |
| 9 | 答复含 `answers`，另有 `usage` / `input_tokens` / `image_tokens` / `x-neohorse-*` 头（playtest_agent.py:1039-1050） | 只有 `{"model","answers","timing"}`；**无 usage、无那些头**（serve.py:74, 118） | 字段缺失 |
| 10 | 限制表 `JEV_LIMITS`：1 MiB / 2048 token / 16 问 / 8 MiB 图 …（playtest_agent.py:502-517） | **没有任何此类限制**（只 2..26 选项） | 无对应物 |
| 11 | `score` 问的答案是 `{"type":"score","score":…,"legend":[…]}` | **没有 score 类型**；只能用有序 level 的 choice 自己算期望 | **必须自己算** |
| 12 | 图像请求强制 `--decision-path /v1/systemone` 或 `/v1/decision` | **只有 `/v1/systemone`**（serve.py:111） | 收窄 |
| 13 | `state_overflow = error\|clip`（2048 token） | 无 token 限制，该开关无意义 | 无对应物 |
| 14 | （Jev 文档未提）`abstain` | **不存在**（serve.py 全文 0 处） | **必须自建** |
| 15 | （Jev 文档未提）`allowed_mass` | **`model.py:102` 算了但 `serve.py` 丢弃** | **上游可改进点** |

**保留共用的部分**（因此没有分叉出第二套语义）：`answers.<key>.choice` 的动作映射
（`action_from_choice`，playtest_agent.py:598-621）、Godot keycode 表、`threading.Lock` 串行化、
"绝不静默成功"的降级纪律（任何失败 → `wait` + 记录）。

---

## 6. 适配器改动（P7）

### 6.1 `godot-mcp/tools/playtest_agent.py`（修改）

| 位置 | 改动 |
|---|---|
| 模块 docstring「Backends」 | 新增 `playjev` 段，写明"同端点名、不同请求形状"与 abstain 语义 |
| 模块 docstring「env var」表 | 新增 `PLAYTEST_ABSTAIN_MIN_CONFIDENCE`；`PLAYTEST_BASE_URL` 补 **8081** 示例；`PLAYTEST_MODEL` 标 `playjev: cosmetic` |
| 新增模块级纯函数 `action_criteria(goal)` | 把 `JevAgent.build_action_criteria` 的**逻辑原样**提出来给两个后端共用 |
| `JevAgent.build_action_criteria` | 改为 **一行 `return action_criteria(goal)`**（纯函数，语义逐字不变） |
| 新增常量块 `PLAYJEV_*` | `PLAYJEV_ANSWER_MODEL="playjev-0.8b"`、`PLAYJEV_HEALTH_PATH="/health"`、`PLAYJEV_DECISION_PATHS=("/v1/systemone",)`、`PLAYJEV_DEFAULT_BASE_URL="http://127.0.0.1:8081"`、`PLAYJEV_MIN_OPTIONS=2`、`PLAYJEV_MAX_OPTIONS=26`、`PLAYJEV_TRUE/FALSE="yes"/"no"`、`PLAYJEV_BROKENNESS_CRITERIA`（1..5 级）、`PLAYJEV_ABSTAIN_NOTE` |
| 新增 `class PlayJevAgent(PlaytestAgent)`，`name="playjev"` | 见 §6.2 |
| `build_agent` | 加 `playjev` 分支；未知后端的报错文本改为 `...scripted\|openai\|jev\|playjev`（保留 `playjev` 字样） |
| `main()` 的 `--selfcheck` | 改为遍历 `scripted/openai/jev/playjev`，并把两个决策后端指向 `http://127.0.0.1:9`（无人监听）以证明**降级路径**而不碰真服务 |
| `main()` 新增 `--probe-playjev` | 与 `--probe-jev` 同构，跑 `tools/tests/test_playjev_agent.py` |
| `main()` 未知参数提示 | 补 `--probe-playjev` |

### 6.2 `PlayJevAgent` 的行为契约

* **问题构造**（`build_questions` → `(questions, roles)`）：**每问都是 `type: "choice"`**
  * `move`（动作）：`criteria = action_criteria(goal)`（与 Jev 同一套选项语义：每个 InputMap action 一项、
    每个文档键一项、外加 `wait`/`done`）；`role="action"`。
  * `playable_frame`（= Jev 的 `noul`）：yes/no 两选项 Choice，`instructions` 用 `JEV_INVARIANT_QUESTIONS[0]`
    的原文；`role="noul"`，`true_option="yes"` → **P(true) = `probabilities["yes"]`**。
  * `brokenness`（= Jev 的 `score`）：1..5 有序 levels 的 dict Choice（level 名就是 `"1"`..`"5"`，
    描述沿用 `JEV_BROKENNESS_LEVELS` 的措辞去掉 `"N = "` 前缀）；`role="score"`
    → **期望损坏度 = Σ (i+1)·p_i**（按返回的 level 概率归一）。
  * 选项数校验 `2 ≤ n ≤ 26`，违反在**上线前**报错。
* **请求构造**（`build_request`）：`{"model", "state": {"frames": ["data:image/png;base64,..."]}, "questions"}`，
  **恰好 1 帧**（取 `frames[-1]` 的真实 PNG 字节）、**N 个问题**。
  `meta` 里显式记录 `transport`、`frame_sha256`、`option_counts`、`question_roles`、
  `image_plus_n_questions: true`、`model_field_read_by_server: false`。
* **上线前拒绝**（不产生任何 HTTP）：
  * `send_images=False` → 拒绝（"PlayJev serves pixels only"）；
  * 没有可读帧 → 拒绝（"no text-state path"）；
  * `decision_path != /v1/systemone` → 拒绝；
  * 选项数越界 → 拒绝。
* **`abstain` 显式处理**（`classify_answer`）——**六条规则**，任一中标即 `abstain=true` 并记原因：
  1. 该问**没有答案对象**（缺失 ≠ 沉默）；
  2. 服务端声明 `abstain` 为真（**前瞻兼容**：现在没有，将来有就跟）；
  3. 没有可用的 `probabilities`；
  4. `choice` 不在返回的概率键里；
  5. `confidence < abstain_min_confidence`（默认 0.0 = 关；可配）；
  6. 该 role 需要的选项（`yes` / 某个 level）不在概率里。
  并且**对每一个我们问过的问题都分类**（`collect_answers` 遍历 `roles`，不是遍历答案），
  所以"模型漏答"也一定是 abstain。
* **abstain 的后果**：
  * `move` 问 abstain → 动作降级为 `{"type":"wait"}`，`why` 里带 `ABSTAINED ... (undecidable, NOT a success)`，
    并新增一条 `kind="abstain"` 的 error；
  * `noul`/`score` 问 abstain → **阈值结论变成"无结论"**：`pass=null` + `decidable=false` +
    `undecidable=[…]`（**既不是 pass 也不是 fail**，绝不当成功）。
* **证据**（`calls[-1]`）包含：`transport`（状态码/头/耗时）、`request_meta`、`request_payload`（逐字）、
  `answers_raw`、`answers_classified`、`probability_tables`、`confidences`、`timing`、
  `abstain`/`abstained_questions`/`abstain_reasons`、`unrequested_answers`、`action`。
* 配置沿用 `PLAYTEST_BASE_URL`/`PLAYTEST_MODEL`/`PLAYTEST_DECISION_PATH`，
  **默认 base URL = `http://127.0.0.1:8081`**。

### 6.3 新增测试与工具（全部为**新文件**）

| 文件 | 作用 |
|---|---|
| `godot-mcp/tools/tests/playjev_dumb_server.py` | stdlib 哑 `/v1/systemone` + `/health` + `/v1/models`，**按 `serve.py` 逐条校验**请求；模式 `ok`/`abstain`/`abstain_score`/`noanswer`/`invalid`/`broken`/`unhealthy`；`--log` 由 Python 写盘 |
| `godot-mcp/tools/tests/test_playjev_agent.py` | **49 项检查**，含"哑服务零校验错误"、协议形状、六类 abstain、错误/坏体/不健康、上线前拒绝、以及 `jev`/`openai`/`scripted` 的回归；证据写 `runs/playability/agent-probe-playjev.json` |
| `godot-mcp/tools/playjev_probe.py` | **本地端到端探针**：1 图 + 3 问 × 6 个样本，逐字落 `runs/playability/playjev-probe.json` |
| `godot-mcp/tools/playjev_serve_wsl.py` | WSL 侧 detached 启动器（无 shell 重定向） |

### 6.4 `godot-mcp/tools/playability_gate.py`（修改，仅帮助文本/文档）

* 新增「The VISION service (TASK-127)」一节：`--agent=playjev` 的用法、8081 默认、choice-only、
  1 图 N 问、abstain 不当成功；给出可复制命令。
* `--agent` 与 `--base-url` 的 help 文本补 `playjev`（`--base-url` 原文提到 `--agent=jev`，我扩为
  `jev`/`playjev` 并给出两个示例端口）。
* **未改任何逻辑**（未动 `build_agent` 调用点、未动门判定）。

### 6.5 回归证据（P7）

```text
$ python tools\playtest_agent.py --probe            # openai 后端
  "request_hits_chat_completions": true   "bearer_token_sent": true
  "base64_image_attached": true           "canned_action_extracted": true
  "judge_json_extracted": true            "http_error_reported": true
  "error_did_not_raise": true             "unconfigured_is_safe": true
 "ok": true                             ← 8/8，与 TASK-124 相同

$ python tools\playtest_agent.py --probe-jev        # jev 后端
 "failed": [],
 "out": "F:\\moonbit-hof-rs\\godot-mcp\\runs\\playability\\agent-probe-jev.json"
 "ok": true                             ← 未回归（含 jev 工厂/文本 state 形状回归项）

$ python tools\playtest_agent.py --test  (via tests) → agent-probe-playjev.json: ok=true 49/49

$ python tools\playtest_agent.py --selfcheck
{"backend": "scripted", "name": "scripted", "action": {"type": "key", "keycode": 87, ...}}
{"backend": "openai",   "name": "openai",   "action": {"type": "wait", ..., "why": "openai backend returned no usable action"}}
{"backend": "jev",      "name": "jev",      "action": {"type": "wait", ..., "why": "jev service is not reachable/ready ... degraded to wait"}}
{"backend": "playjev",  "name": "playjev",  "action": {"type": "wait", ..., "why": "playjev service is not reachable/ready ... degraded to wait"}}

$ python tools\playtest_agent.py --help | findstr /C:"playjev"
  playjev  : PlayJev 0.8B's image-state decision server (TASK-127), the *vision
    PLAYTEST_ABSTAIN_MIN_CONFIDENCE  playjev: a confidence below this is an
    PLAYTEST_BASE_URL  ... http://127.0.0.1:8081  for `playjev`
```

测试文件 `tools/tests/test_playjev_agent.py` 的 49 项检查（全绿）：

```text
dumb_server_validates_clean, posts_to_v1_systemone, health_ok_true,
state_frames_is_one_data_url, frame_decodes_to_png, no_toplevel_image_field,
one_image_many_questions, all_questions_are_choice, every_question_has_ge_2_options,
no_noul_or_score_question_type, action_is_a_real_action, action_probabilities_in_evidence,
abstain_flag_recorded, confidence_recorded, timing_recorded, noul_p_true_from_yes_no_choice,
score_is_expected_level_le_2, threshold_verdict_passes_on_ok, judge_reuses_decide_evidence,
server_rejects_noul_question, server_rejects_score_question, server_rejects_text_state,
server_rejects_single_option_choice, server_500_on_bad_base64,
declared_abstain_seen, abstain_action_is_wait_not_success, abstain_verdict_is_not_pass,
abstain_recorded_as_error, score_only_abstain_keeps_action, score_only_abstain_is_not_a_pass,
missing_answer_is_abstain, missing_answer_not_a_success, confidence_threshold_abstains,
http_400_reported, http_400_not_a_success, broken_body_reported, broken_body_not_a_success,
unhealthy_reported, unhealthy_no_post, send_images_false_refused, no_frame_refused,
jev_decision_path_refused, over_26_options_refused, scripted_regression_none,
openai_regression_none, jev_regression_none, playjev_wired_in_factory,
playjev_default_base_url_8081, unknown_backend_error_names_playjev
→ {"ok": true, "passed": 49, "total": 49}
```

**非恒真保证**：`server_rejects_*` 五项是**拿着非法请求打哑服务**（哑服务按 `serve.py` 原文校验），
证明"我们不会发出非法请求"不是一句空话；`server_500_on_bad_base64` 专门钉住
"非 base64 字符串 → **500**（不是 400）"这条 `serve.py:122-123` 的真实语义。

---

## 7. 本地端到端实测（P8、P9）

**全程本地**：唯一被访问的端点是 `http://127.0.0.1:8081/v1/systemone`（WSL 内的本机服务）。
`playjev-probe.json` 里显式写着 `"third_party_endpoints_used": []`。

### 7.1 素材（每张的来源与代表什么）

**正面（真实截图）**——取自**我们自己游戏**导出 exe 的门运行
（`godot-mcp/runs/playability-exe/<game>/frames/*.png`）：

| 样本 | 来源文件 | 代表什么 |
|---|---|---|
| `pong_post1` | `runs/playability-exe/pong/frames/20_post1.png` | 我们导出的 pong exe 的**全窗口真实截图**，脚本化探针动作之后 |
| `tetris_auto3` | `runs/playability-exe/tetris/frames/04_auto3.png` | 导出 tetris exe 的自动 settle 阶段真实截图 |
| `snake_act` | `runs/playability-exe/snake/frames/07_a00_snake_up_parse_act.png` | 导出 snake exe 在**真实注入按键之后**的截图（第一个文档动作的 act 帧） |

**负面（由真实帧按可复现配方派生）**——我先普查了全部 **836** 张已捕获帧：
`content_fraction < 0.005` 的有 **0** 张，即**我们手上没有任何天然退化帧**。
所以负面帧是**从上述真实帧派生**并逐张记录配方与 sha256：

| 样本 | 配方 | 代表什么 |
|---|---|---|
| `pong_post1_black` | 全部像素置 0 | "**全黑屏**"这类失效 |
| `pong_post1_flat` | 全部像素置为**该帧自己的背景色** `background_rgb`（pong = `[8,24,24]`） | "**平色/空渲染**"，不是字面黑 |
| `pong_post1_content_missing` | 把该帧的 **content bbox** 涂成背景色 | "**窗口在、游戏没画出东西**" |

派生的 PNG 落 `runs/playability/playjev-probe-frames/`，来源帧 sha256 与派生帧 sha256 都写进
`playjev-probe.json` 的 `provenance`（`kind: real-capture` / `kind: derived` + `recipe` + `source` +
`source_sha256` + `derived_sha256` + `background_rgb` + `content_bbox`）。

### 7.2 请求/响应（1 图 + 3 问，逐字落盘）

每次请求的**逐字请求体与逐字响应体**都在
`runs/playability/playjev-probe.json` → `samples[i].evidence.request_payload` /
`.transport.body`（含状态码、头、秒数）。样本 1 的 `request_meta` 逐字：`frame_bytes: 4365`、
`body_bytes: 7254`、`frame_sha256: 4935a0eb76cfa328b16970e5ad71d15f85c38f4a80ad415d7df81b1f9532a45a`。
请求形状（**图片 base64 已在此处省略以便阅读**，完整字节见 JSON）：

```json
{"model": "playjev-0.8b",
 "state": {"frames": ["data:image/png;base64,<4365 PNG bytes = 5820 base64 chars …ELIDED…>"]},
 "questions": {
   "move":            {"type": "choice",
                       "instructions": "Choose the single next input that best serves the objective.",
                       "criteria": {"pong_left_down": "hold the game's InputMap action 'pong_left_down' (bound key(s): S)",
                                    "pong_left_up":   "hold the game's InputMap action 'pong_left_up' (bound key(s): W)",
                                    "pong_serve":     "hold the game's InputMap action 'pong_serve' (bound key(s): SPACE)",
                                    "key_W": "press and release the key W", "key_S": "press and release the key S",
                                    "key_SPACE": "press and release the key SPACE",
                                    "wait": "do nothing this step (hold position / observe)",
                                    "done": "stop probing: no further action is likely to help"}},
   "playable_frame":  {"type": "choice",
                       "instructions": "Does this frame clearly look playable, with no visual corruption or freeze?",
                       "criteria": {"yes": "the frame does satisfy this statement",
                                    "no":  "the frame does not satisfy this statement"}},
   "brokenness":      {"type": "choice",
                       "instructions": "Rate how broken this frame is, from 1 (fully working) to 5 (unusable).",
                       "criteria": {"1": "fully working: content is drawn, input responds, nothing looks wrong",
                                    "2": "minor glitches only; still clearly playable",
                                    "3": "partially broken: some documented capability is missing or unresponsive",
                                    "4": "badly broken: the game barely responds or renders garbage",
                                    "5": "unusable: flat/blank screen, error dialog, or frozen"}}}}
```

样本 1（`pong_post1`）的**逐字响应体**：

```json
{"model": "playjev-0.8b",
 "answers": {
   "move": {"type": "choice", "choice": "key_SPACE",
            "probabilities": {"pong_left_down": 0.041987, "pong_left_up": 0.04399, "pong_serve": 0.014151,
                              "key_W": 0.144974, "key_S": 0.17058, "key_SPACE": 0.29292,
                              "wait": 0.126209, "done": 0.16519},
            "confidence": 0.191908},
   "playable_frame": {"type": "choice", "choice": "yes",
            "probabilities": {"yes": 0.564843, "no": 0.435157}, "confidence": 0.129686},
   "brokenness": {"type": "choice", "choice": "3",
            "probabilities": {"1": 0.088308, "2": 0.063787, "3": 0.705995, "4": 0.07395, "5": 0.067961},
            "confidence": 0.632493}},
 "timing": {"prep_ms": 1896.5, "forward_ms": 494.0, "input_tokens": 783, "visual_tokens": 900, "total_ms": 2392.7}}
```

### 7.3 六个样本的汇总（**实际测出来的数**，不是推断）

| 样本 | HTTP | 动作 | `move` 选择 | **P(yes)** | 期望损坏度 | `move` conf | 阈值结论 |
|---|---:|---|---|---:|---:|---:|---|
| `pong_post1`（真实） | 200 | `key` | `key_SPACE` | **0.5648** | 2.969 | 0.192 | 1/2 |
| `tetris_auto3`（真实） | 200 | `action` | `pong_left_*` | **0.8459** | 2.243 | 0.248 | **2/2** |
| `snake_act`（真实） | 200 | `key` | `key_SPACE` | **0.4825** | 3.971 | 0.203 | 0/2 |
| `pong_post1_black`（负面） | 200 | `action` | `pong_serve…` | **0.2020** | 2.413 | 0.297 | 1/2 |
| `pong_post1_flat`（负面） | 200 | `action` | `pong_serve…` | **0.1997** | 2.378 | 0.295 | 1/2 |
| `pong_post1_content_missing`（负面） | 200 | `action` | `pong_serve…` | **0.2027** | 2.366 | 0.286 | 1/2 |

延迟（`total_ms`，同一进程连续 6 次的第 1 次含 processor 预热）：
`2392.7, 357.6, 358.7, 374.8, 375.1, 385.9` ms。
服务端自报 `forward_ms` 约 38–494 ms（**不是** README 的 H200 43 ms；这是 RTX 4090，且与 Jev 共卡）。
`prep_ms` 第 1 次 1896.5 ms（首次 JPEG/processor 建缓存），之后稳定。

**读出来的两个结论（如实报告）**：

* ✅ **`playable` 维度是有效信号**：三张负面帧的 P(yes) = **0.2020 / 0.1997 / 0.2027**，
  **全部低于 0.5 阈值**且彼此高度一致；真实帧为 0.5648 / 0.8459 / 0.4825。
  即"这张帧看起来还能玩吗"这个问题，在**分布外**的 Godot 截图上，对我们构造的退化画面
  **3/3 全部判负**，对真实画面 **2/3 判正**（`snake_act` 0.4825 卡在阈值下沿）。
* ❌ **我这一版 `brokenness` 维度方向是错的**：黑屏/平色/内容缺失的期望损坏度
  是 **2.41 / 2.38 / 2.37**，而真实 `snake_act` 帧是 **3.97**（argmax 直接落在 level 5 "unusable"）。
  也就是说：**在这批分布外素材上，损坏度打分不但没有区分度，方向还反了**。
  这不是适配器 bug（线上形状、概率、期望值算法都经 §6.5 的 49 项检查钉住），
  而是**把 PlayJev 当"通用画面质量打分器"用是超出它训练分布的**——它是在 10 个浏览器小游戏上
  对"下一步怎么走"做 imitation learning 微调的（README §Training Recipe）。
  → 决策建议见 §10 R1/R2。

### 7.4 **真的 abstain**（P9）

PlayJev 服务**从不发 `abstain`**（§4.4），所以我在**真实服务上构造**了一次：
把 `abstain_min_confidence` 设为 **0.5**（高于实测 `move`/`playable_frame` 的置信度），
其他一切不变，重跑同 6 个样本：

```text
$ python tools\playjev_probe.py --abstain-min-confidence 0.5 --out runs\playability\playjev-probe-abstain.json
[1/6] pong_post1                     status=200 abstain=True action=wait
[2/6] tetris_auto3                   status=200 abstain=True action=wait
[3/6] snake_act                      status=200 abstain=True action=wait
[4/6] pong_post1_black               status=200 abstain=True action=wait
[5/6] pong_post1_flat                status=200 abstain=True action=wait
[6/6] pong_post1_content_missing     status=200 abstain=True action=wait
probe: ok=True  samples=6
```

落库内容（逐字取自 `playjev-probe-abstain.json`）：

```json
"abstained_questions": ["move", "playable_frame"],
"abstain_reasons": {
  "move":           ["confidence 0.191908 < abstain_min_confidence 0.500000"],
  "playable_frame": ["confidence 0.129686 < abstain_min_confidence 0.500000"]},
"action": {"type": "wait", "ms": 200,
           "why": "playjev ABSTAINED on move (undecidable, NOT a success): confidence 0.191908 < abstain_min_confidence 0.500000"},
"verdict": {"pass": null, "decidable": false, "undecidable": ["noul:playable_frame"]}
```

**这满足 P9 的两种读法**：
1. 在**真实服务**上构造出了一次真的 abstain（不是靠哑服务模拟）；
2. 哑服务侧另有 `abstain`（服务端声明）与 `noanswer`（答案缺失）两个模式，各有一项检查
   （`declared_abstain_seen` / `missing_answer_is_abstain`），三种 abstain 来源都有覆盖。
关键在于：**abstain 时 `pass` 是 `null` 而不是 `true`，动作降级为 `wait`，并且写了一条
`kind="abstain"` 的错误记录** —— "模型没回答"绝不会被读成"模型说没问题"。

---

## 8. P1–P10 逐条证据

| 编号 | 判据 | 结论 | 证据位置 |
|---|---|---|---|
| **P1** | 源码与权重来源已定位（URL + 状态码）；权重清单逐文件大小 | ✅ | §1 表（9 条 URL + HTTP/字节）；§2.1 逐文件字节表（10 行，9 个文件 + data/）；克隆锚点 `ea3a514…` |
| **P2** | 许可与基座已核实（LICENSE 关键句原文） | ✅ | §2.3：仓库 `LICENSE` = Apache-2.0（11560 B，sha256 `3DDF9BE5…`）；HF front-matter `license: apache-2.0` / `base_model: Qwen/Qwen3.5-0.8B-Base`；README:239 原文 `Code and trained weights: Apache-2.0.`；README:24 基座原文 |
| **P3** | 权重已下载并逐文件 SHA256 对表（无 SHA256SUMS 则说明如何核验） | ✅ | §2.2：仓库**无** SHA256SUMS → 用 HF 树 API 的 **LFS `oid`（= sha256）** 作期望值；两个 LFS 文件的 actual/expected **逐字符相同**；7 个非 LFS 文件字节数逐一相符 |
| **P4** | `/opt/playjev-venv` 装好（pip freeze 关键行），**未动 `/opt/jev-venv`** | ✅ | §3.1：`uv pip freeze` 13 行关键输出；`stat` 显示 `/opt/jev-venv/pyvenv.cfg` mtime 仍为 `2026-09-27 16:56:35`；两个 venv 体积分列（6.7G / 7.0G） |
| **P5** | 服务在 8081 就绪（`/health` 原文），且 8080 的 Jev 仍存活 | ✅ | §3.5：8081 `/health` = `{"ok": true, "model": "playjev-0.8b", "two_frame": false}`（HTTP 200）；**同一时刻** 8080 `/health` = `{"status":"ready","model":"NeoHorse-Jev-4B","input_modalities":["text","image"]}`（HTTP 200）；`ss` 两端口监听行 + `pgrep` 两个 PID |
| **P6** | `serve.py` 真实请求/响应形状逐字抄录（文件+行号），列出与 JevAgent 假设的差异 | ✅ | §4 逐字代码块（行 31-74 / 85-123 / 102-112）+ §4.5 "1 图多问支持"；§5 **15 行差异表**，逐条给 `playtest_agent.py` 行号与 `serve.py` 行号 |
| **P7** | 适配器实现，`jev`/`openai`/`scripted` 未回归（`--help` 与自测输出） | ✅ | §6 全部改动清单；§6.5：`--probe` 8/8 ok、`--probe-jev` ok/failed=[]、`--selfcheck` 四后端各自降级输出、`--help` 含 `playjev`；`test_playjev_agent.py` **49/49**（列表逐项） |
| **P8** | 1 图 + 3 问本地实测 200（请求/响应逐字落盘 + 可重跑命令） | ✅ | §7.2 请求逐字（图 base64 标注 ELIDED）+ 响应逐字；§7.3 六样本表（全 HTTP 200）；落盘 `runs/playability/playjev-probe.json`；可重跑命令见 §11 |
| **P9** | `abstain` 被显式处理（构造一次或说明为何构造不出） | ✅ | §7.4：在**真实服务**上用 `--abstain-min-confidence 0.5` 构造出 6/6 abstain，落盘 `playjev-probe-abstain.json`，`pass=null`/`decidable=false`/动作降级 `wait`/记 `kind="abstain"` error；哑服务侧另有 `abstain` 与 `noanswer` 两种来源 |
| **P10** | 明写：无第三方端点、无重定向、无破坏性命令、未改安全设置；git log/status | ✅ | §9 全节（含一条**如实申报的 `2>&1` 偏差**）+ §9.3 的 `git log --oneline -5` 与 `git status --short` |

---

## 9. 铁律遵守声明（P10）

### 9.1 无第三方端点

**图像推理**只发生在 `http://127.0.0.1:8081/v1/systemone`（WSL 内的本机进程 pid 1771）。
`playjev-probe.json` 与 `playjev-probe-abstain.json` 里都有 `"third_party_endpoints_used": []`。
`api1.omnijev.net` 或任何厂商 demo 端点**一次也没有被调用**。
唯一的对外网络活动是**取素材**：GitHub API/raw（Windows 侧）、`hf-mirror.com`（Windows 侧，
权重与元数据）、`pypi.org` / `download.pytorch.org`（WSL 内，装依赖）——**都是下载，不是推理**。

### 9.2 无 shell 重定向、无破坏性命令、未改安全设置

* 落盘一律走 `curl -o` / Python `open(..., "w")` / `Set-Content` 类写文件工具；
  **没有使用 `>`、`>>`、`*>`、`"> nul"` 写文件**。
* **⚠️ 如实申报一处偏差**：在**只为在控制台过滤输出**的 5 条诊断命令里，我用了 `2>&1`
  （`python ... --probe 2>&1 | Select-String ...` 之类）。它们**没有写任何文件、没有改任何状态**，
  但按铁律 §3.1 的字面要求 `2>&1` 属于禁止的重定向操作符 —— 这是我的疏忽，记录在此。
  （另用了几次 `| Out-Null` 丢弃输出的管道；那是管道不是重定向操作符，一并声明。）
* **破坏性命令零使用**：没有 `Remove-Item`、没有 `rm -rf`、没有通配符删除、没有 `..` 路径回溯。
  唯一"删除"语义的动作是 `curl -C -` 的续传（它只会**续写** `model.safetensors`）。
* **未改机器安全设置**：没有 `Set-ExecutionPolicy`、没有 `netsh`、没有证书/代理/防火墙改动、
  没有启用/关闭 Windows 功能、**没有重启**。`curl` 的 `--ssl-no-revoke` 只是**客户端本次调用**的
  TLS 吊销检查开关，不写任何系统状态。
* **未杀任何用户进程或其它会话的服务**：`pgrep`/`ss` 只做只读观察；TASK-127 只启动了自己的
  pid 1771。**8080 的 Jev 进程 pid 730 从头到尾未被触碰**（见 §3.5 两次 health 复测）。
* **未碰三处禁区**：`/opt/jev-venv`（mtime 未变，§3.1）、8080 服务（存活，§3.5）、
  `F:\models\NeoHorse-Jev-4B`（全程只读引用，未列未改）。
* 大文件下载用**后台 job**（`term-1703` curl 权重、`term-1704` 两次 pip install），
  且**可续传**（`--retry 5 --retry-delay 3 -C -`），期间分三次报告了进度（731 MB → 909 MB → 2,172 MB → 完成）。
* **权重与 venv 不入库**：权重在 `F:\models\PlayJev-0.8B`，venv 在 `/opt/playjev-venv`，
  源码副本在 `/opt/playjev` —— **三者都在仓库之外**（`git check-ignore` 见下）。

### 9.3 两仓 git 状态（"两仓"在本工作区实为**同一个仓库**）

```text
$ cd F:\moonbit-hof-rs && git rev-parse --show-toplevel
F:/moonbit-hof-rs
$ cd F:\moonbit-hof-rs\godot-mcp && git rev-parse --show-toplevel
F:/moonbit-hof-rs
```

（`godot-mcp/` 是同一仓库的子目录，**不是**第二个 repo —— 如实说明，避免"两仓"被误读。）

改动**之前**的 `git log --oneline -5`（最后一次改动前）：

```text
a023eaa docs(godot-mcp): TASK-124 - the report (33/33 dumb-service checks, J1-J9 evidence) and the corrected reproduce commands
13cd1d8 feat(godot-mcp): TASK-124 (D166) - add the --agent=jev native NeoHorse-Jev decision backend, a stdlib dumb /v1/systemone service, and replace the wrong Jev launch docs
2c74bc7 chore: 删除空文件 $l
c0d5731 chore(repo): TASK-122 (D165) - filter the main repo: 7,858 untracked -> 203
2a8ecf9 chore(godot-mcp): TASK-120 - refresh the ledger once more after the decision record (generated_utc only; every number identical to the one quoted in the report)
```

**开工时的 `git status --short`（重要：两条是上一批遗留、不是我改的）**：

```text
 M .gitignore                            ← 遗留：TASK-125 的"权重不入库"规则（提交信息以 TASK-125 自述）
 M godot-mcp/tools/playability_gate.py   ← 遗留：TASK-128 的 --base-url 本体（含在本次提交里，见下）
?? godot-mcp/recovery/reports/TASK-125-REPORT.md
?? godot-mcp/recovery/reports/TASK-126-REPORT.md
?? godot-mcp/recovery/tasks/               ← TASK-127.md 也在这里
```

我把 **`.gitignore` 留在未暂存状态**（它纯粹是 TASK-125 的产物；虽然其"大二进制不入库"的规则
对本任务同样适用，但把它记进 TASK-127 的提交会让决策树失真）。
`playability_gate.py` 里**混着** TASK-128 的 `--base-url` 本体与我的 TASK-127 帮助文本改动，
无法按 hunk 干净拆分而不动别人的代码，所以**一并提交并在提交信息里逐字声明这一点**。

`git check-ignore` 证明权重/venv/证据都不入库：

```text
$ git check-ignore -v godot-mcp/runs/playability/playjev-probe.json
.gitignore:43:godot-mcp/runs/     godot-mcp/runs/playability/playjev-probe.json
$ git check-ignore -v godot-mcp/runs/
.gitignore:43:godot-mcp/runs/     godot-mcp/runs/
$ git check-ignore -v F:/models/PlayJev-0.8B/model.safetensors
（仓库外，git 不跟踪）
```

提交与提交后的 log/status 见 §11.6。
---

## 10. 遗留与待决项

### R1（**需要你决策**）`brokenness` 维度：撤掉、还是改造？

实测（§7.3）显示它在分布外包材上**方向相反**（黑屏 2.41 < 真帧 3.97）。三条路：

* **(a) 撤掉 score 问，只留 `playable` + `move`**（1 图 2 问）。最小、最诚实，
  证据里不再有一个会误导人的数字。**我倾向这条**。
* **(b) 保留但**不参与判定**，只作为"未校准的观察值"落库（`uncalibrated: true`，
  且**不得**进任何 P-verdict）。成本为零，保留未来标定的可能。
* **(c) 换问法**：把 level 描述改成**面向我们这类 2D 全窗口游戏**的措辞，或在询问里带上
  "画面来自 Godot 游戏"的上下文。但 PlayJev 的 prompt 是**冻结的 OpenJev 措辞**
  （`model.py:30-40`），改 `instructions` 已属分布外；收益未验证。**不建议**先做。

### R2 阈值仍然**未标定**

`noul_min_p_true=0.5` / `score_max_expected=2.5` 是 TASK-124 立的**先验**。
本次实测给了一个**初步但真实**的锚点（负面帧 P(yes)≈0.20 vs 真实帧 0.48–0.85），
样本量只有 **3 正 + 3 负**，**不足以**定阈值。要做的话需要：
在 20 个固定游戏上各取若干帧（正），加上 `dist/exe-task109-pre-fix/` 的真实退化运行
（负，需跑 Godot GUI 采集），再拟合。**这是下一步最该做的事**。

### R3 负面素材是**派生**的，不是天然退化帧

我们 836 张已捕获帧里**没有一张** `content_fraction < 0.005`。所以本次的负面是
"从真实帧按可复现配方派生"（黑屏/平色/内容缺失）。**它们不是真实失效场景**。
真正的负面素材应来自 `dist/exe-task109-pre-fix/`（修复前、输入被禁的那些构建）的**实跑采集**
——那需要 Godot 全窗口运行，本任务未做（§11.5 给出应该怎么跑）。

### R4（**给上游的两条具体建议**）

1. `playjev/serve.py` 应当把 `Decision.allowed_mass`（model.py:102）与 `top_token`（model.py:103）
   放进答复（或在 `confidence` 之外给一个 `abstain`）。这是**唯一**能区分
   "模型在回答但不自信" 与 "模型压根没在看答案槽" 的信号，而现在被丢弃 ——
   没有它，客户端的 abstain 只能靠 `confidence` 阈值代偿（本任务的 §7.4 正是这种代偿）。
2. `serve.py:72` 的 `timing` 在问题循环内被**反复覆盖**，一次请求里只有**最后一个问题**的
   `prep_ms`/`forward_ms`/token 数；多问请求的耗时证据因此不完整。建议按问分开记。

### R5 未跑的项（**如实声明，不假装**）

* **未用 `--agent=playjev` 跑整条 `playability_gate.py`**（需要 Godot 全窗口 GUI 运行 20 个游戏）。
  协议层已由 49 项哑服务检查 + 6 个真实样本覆盖；门的装配路径未在真服务上端到端跑过。
  命令见 §11.4。
* **未做 `--two-frame` 模式**（`serve.py:131` 的 `--two-frame`）：我们的门目前只喂单帧，
  且权重 `playjev_train.json` 里 `"two_frame": false`（**发布的权重就是单帧训练的**），
  开了反而与训练不一致，所以**有意不开**。
* **未跑 `playjev.play` / `scripts/reproduce.sh`**（需要 Playwright + 浏览器，只服务复现训练）。
* **未验证 `PLAYTEST_API_KEY` 路径**（本机服务无鉴权；适配器保留了该头，未被真服务检验）。
* **未对 `data/`（853 MB 训练记录）做任何事**（推理不需要）。

---

## 11. 可重跑命令（逐条）

> 全部命令**无 shell 重定向**。`>` 等操作符一律不用。
> 记号：`[WIN]` = Windows 侧（cmd/PowerShell）；`[WSL]` = `wsl.exe -d Ubuntu -- bash -lc "..."` 内。

### 11.1 [WIN] 定位（网络，GitHub 可达 / HF 直连不可达）

```text
curl.exe -sSL --ssl-no-revoke -w "repo HTTP:%{http_code} SIZE:%{size_download}\n" -o F:\moonbit-hof-rs\runs\playability\playjev-repo.json https://api.github.com/repos/OmniJev/PlayJev
curl.exe -sSL --ssl-no-revoke -w "readme HTTP:%{http_code} SIZE:%{size_download}\n" -o F:\moonbit-hof-rs\runs\playability\playjev-readme.md https://raw.githubusercontent.com/OmniJev/PlayJev/main/README.md
curl.exe -sSL --ssl-no-revoke -w "releases HTTP:%{http_code} SIZE:%{size_download}\n" -o F:\moonbit-hof-rs\runs\playability\playjev-releases.json https://api.github.com/repos/OmniJev/PlayJev/releases
curl.exe -sSL --ssl-no-revoke --max-time 25 -w "hf HTTP:%{http_code} SIZE:%{size_download}\n" -o F:\moonbit-hof-rs\runs\playability\hf-playjev.json https://huggingface.co/api/models/OmniJev/PlayJev-0.8B
curl.exe -sSL --ssl-no-revoke --max-time 25 -w "hfmirror HTTP:%{http_code} SIZE:%{size_download}\n" -o F:\moonbit-hof-rs\runs\playability\hfmirror-playjev.json https://hf-mirror.com/api/models/OmniJev/PlayJev-0.8B
curl.exe -sSL --ssl-no-revoke -w "tree HTTP:%{http_code} SIZE:%{size_download}\n" -o F:\moonbit-hof-rs\runs\playability\hfmirror-tree.json https://hf-mirror.com/api/models/OmniJev/PlayJev-0.8B/tree/main
curl.exe -sSL --ssl-no-revoke --max-time 25 -w "ms HTTP:%{http_code} SIZE:%{size_download}\n" -o F:\moonbit-hof-rs\runs\playability\ms-playjev.json https://modelscope.cn/api/v1/models/OmniJev/PlayJev-0.8B
```

### 11.2 [WIN] 源码克隆 + 权重下载（可续传）+ SHA256 对表

```text
git clone --depth 1 https://github.com/OmniJev/PlayJev.git F:\moonbit-hof-rs\runs\playability\PlayJev-src
cd /d F:\moonbit-hof-rs\runs\playability\PlayJev-src && git rev-parse HEAD

:: 权重：9 个文件（权重目录在仓库之外；-C - 可续传；大文件建议 run_in_background）
mkdir F:\models\PlayJev-0.8B
cd /d F:\models\PlayJev-0.8B
curl.exe -sSL --ssl-no-revoke --retry 5 --retry-delay 3 -C - -o model.safetensors "https://hf-mirror.com/OmniJev/PlayJev-0.8B/resolve/main/model.safetensors"
curl.exe -sSL --ssl-no-revoke --retry 3 -C - -o tokenizer.json "https://hf-mirror.com/OmniJev/PlayJev-0.8B/resolve/main/tokenizer.json"
curl.exe -sSL --ssl-no-revoke --retry 3 -C - -o config.json "https://hf-mirror.com/OmniJev/PlayJev-0.8B/resolve/main/config.json"
curl.exe -sSL --ssl-no-revoke --retry 3 -C - -o generation_config.json "https://hf-mirror.com/OmniJev/PlayJev-0.8B/resolve/main/generation_config.json"
curl.exe -sSL --ssl-no-revoke --retry 3 -C - -o processor_config.json "https://hf-mirror.com/OmniJev/PlayJev-0.8B/resolve/main/processor_config.json"
curl.exe -sSL --ssl-no-revoke --retry 3 -C - -o chat_template.jinja "https://hf-mirror.com/OmniJev/PlayJev-0.8B/resolve/main/chat_template.jinja"
curl.exe -sSL --ssl-no-revoke --retry 3 -C - -o playjev_train.json "https://hf-mirror.com/OmniJev/PlayJev-0.8B/resolve/main/playjev_train.json"
curl.exe -sSL --ssl-no-revoke --retry 3 -C - -o README.md "https://hf-mirror.com/OmniJev/PlayJev-0.8B/resolve/main/README.md"

:: 对表：期望值来自 hfmirror-tree.json 里的 lfs.oid
powershell -NoProfile -Command "(Get-FileHash F:\models\PlayJev-0.8B\model.safetensors -Algorithm SHA256).Hash.ToLower()"
powershell -NoProfile -Command "(Get-FileHash F:\models\PlayJev-0.8B\tokenizer.json -Algorithm SHA256).Hash.ToLower()"
```

### 11.3 [WSL] 独立 venv + 起服务（**不动 /opt/jev-venv**）

```text
wsl.exe -d Ubuntu -- bash -lc "uv venv --python 3.12 /opt/playjev-venv"

wsl.exe -d Ubuntu -- bash -lc "mkdir -p /opt/playjev && cp -r /mnt/f/moonbit-hof-rs/runs/playability/PlayJev-src/playjev /opt/playjev/ && cp /mnt/f/moonbit-hof-rs/runs/playability/PlayJev-src/requirements.txt /mnt/f/moonbit-hof-rs/runs/playability/PlayJev-src/LICENSE /opt/playjev/"

wsl.exe -d Ubuntu -- bash -lc "uv pip install --python /opt/playjev-venv/bin/python --index-url https://download.pytorch.org/whl/cu128 torch==2.10.0 torchvision==0.25.0"
wsl.exe -d Ubuntu -- bash -lc "uv pip install --python /opt/playjev-venv/bin/python --index-url https://pypi.org/simple transformers==5.17.0 accelerate==1.15.0 pillow einops numpy==2.5.3 safetensors==0.8.0 tokenizers==0.23.2"

:: 环境自检（导入 + CUDA）
wsl.exe -d Ubuntu -- bash -lc "/opt/playjev-venv/bin/python /mnt/f/moonbit-hof-rs/godot-mcp/runs/playability/_playjev_envcheck.py"

:: 先查端口占用（8081 必须空闲）
wsl.exe -d Ubuntu -- bash -lc "ss -ltnp | grep -E '8080|8081'"

:: 起服务：detached，日志由 Python 落盘，零 shell 重定向
wsl.exe -d Ubuntu -- bash -lc "python3 /mnt/f/moonbit-hof-rs/godot-mcp/tools/playjev_serve_wsl.py 8081 detached"

:: 就绪判据 + Jev 存活（两条必须同时通过）
wsl.exe -d Ubuntu -- bash -lc "curl -sS --max-time 10 -w '\nHTTP:%{http_code}\n' http://127.0.0.1:8081/health"
wsl.exe -d Ubuntu -- bash -lc "curl -sS --max-time 10 -w '\nHTTP:%{http_code}\n' http://127.0.0.1:8080/health"
```

### 11.4 [WIN] 协议层自测 + 回归（无权重、无 GPU、stdlib）

```text
cd /d F:\moonbit-hof-rs\godot-mcp
python tools\tests\test_playjev_agent.py                     :: 49/49；证据写 runs\playability\agent-probe-playjev.json
python tools\playtest_agent.py --probe-playjev               :: 同上，经主入口
python tools\playtest_agent.py --probe                       :: openai 后端 8/8（回归）
python tools\playtest_agent.py --probe-jev                   :: jev 后端（回归）
python tools\playtest_agent.py --selfcheck                   :: 四后端各自降级
python tools\playtest_agent.py --help                        :: 文档含 playjev
```

### 11.5 [WIN] 本地端到端实测（1 图 3 问）

```text
cd /d F:\moonbit-hof-rs\godot-mcp

:: 正常路径：6 个样本（3 真实 + 3 派生负面），逐字落盘
python tools\playjev_probe.py --timeout 300 --out runs\playability\playjev-probe.json

:: 真的 abstain：与上面唯一差别是阈值 0.5
python tools\playjev_probe.py --timeout 300 --abstain-min-confidence 0.5 --out runs\playability\playjev-probe-abstain.json

:: 只打本地服务，显式指定 base-url 也行
python tools\playjev_probe.py --base-url http://127.0.0.1:8081 --out runs\playability\playjev-probe.json
```

（跑整条门、需要 Godot GUI 的那条——**本次未跑**，§10 R5：

```text
set PLAYTEST_BASE_URL=http://127.0.0.1:8081
set PLAYTEST_MODEL=playjev-0.8b
python tools\playability_gate.py --games pong --agent=playjev --base-url http://127.0.0.1:8081
```
）

### 11.6 [WIN] git

```text
cd /d F:\moonbit-hof-rs
git log --oneline -5
git status --short
```

**提交后的实际输出（本次）：**

> 说明：报告本身就在这个提交里，所以**不在这里写死提交哈希**（写死会自动失效，改一次哈希就变一次）——
> 用 `git log -1 --format=%H` 取当前值。提交的 subject 是：
> `feat(godot-mcp): TASK-127 - deploy PlayJev 0.8B locally (WSL venv /opt/playjev-venv, port 8081) and add the --agent=playjev image-state backend`

```text
$ git log --oneline -5
<HEAD，取 git log -1>  feat(godot-mcp): TASK-127 - deploy PlayJev 0.8B locally (WSL venv /opt/playjev-venv, port 8081) and add the --agent=playjev image-state backend
a023eaa docs(godot-mcp): TASK-124 - the report (33/33 dumb-service checks, J1-J9 evidence) and the corrected reproduce commands
13cd1d8 feat(godot-mcp): TASK-124 (D166) - add the --agent=jev native NeoHorse-Jev decision backend, a stdlib dumb /v1/systemone service, and replace the wrong Jev launch docs
2c74bc7 chore: 删除空文件 $l
c0d5731 chore(repo): TASK-122 (D165) - filter the main repo: 7,858 untracked -> 203

$ git status --short
 M .gitignore                                   ← TASK-125 的规则，**有意未暂存**（不是本次改动）
?? godot-mcp/recovery/reports/TASK-125-REPORT.md
?? godot-mcp/recovery/reports/TASK-126-REPORT.md
?? godot-mcp/recovery/tasks/
?? godot-mcp/tools/agent_threshold_calibrate.py  ← 非本次产物（本次从未创建/修改该文件）

$ git show --stat --oneline HEAD
<HEAD> feat(godot-mcp): TASK-127 - deploy PlayJev 0.8B locally (WSL venv /opt/playjev-venv, port 8081) and add the --agent=playjev image-state backend
 godot-mcp/recovery/reports/TASK-127-REPORT.md | 1112 +++++++++++++++++++++++++++
 godot-mcp/tools/playability_gate.py           |  180 ++++-
 godot-mcp/tools/playjev_probe.py              |  293 +++++++
 godot-mcp/tools/playjev_serve_wsl.py          |   71 ++
 godot-mcp/tools/playtest_agent.py             |  689 ++++++++++++++++-
 godot-mcp/tools/tests/playjev_dumb_server.py  |  449 +++++++++++
 godot-mcp/tools/tests/test_playjev_agent.py   |  389 ++++++++++
 7 files changed, 3148 insertions(+), 35 deletions(-)
```
（这份 `--stat` 的行数是**补上本说明之前**的一次采样；因为报告本身在提交里，补说明会让报告行数略增，
所以行数以 `git show --stat HEAD` 的当次输出为准 —— 7 个文件、5 个 `create mode` 是稳定的。）

提交信息里**逐字声明**了 `playability_gate.py` 同时携带上一批未提交的 TASK-128 `--base-url` 本体 ——
使"改动 → 提交 → 报告"可互查，不把别人的改动冒充成 TASK-127 的。

---

## 12. 本次改动文件清单

**新增**

| 文件 | 说明 |
|---|---|
| `godot-mcp/tools/tests/playjev_dumb_server.py` | stdlib 哑 PlayJev 服务（按 serve.py 逐条校验） |
| `godot-mcp/tools/tests/test_playjev_agent.py` | 49 项协议/abstain/回归检查 |
| `godot-mcp/tools/playjev_probe.py` | 本地端到端探针（1 图 3 问） |
| `godot-mcp/tools/playjev_serve_wsl.py` | WSL 侧 detached 启动器 |
| `godot-mcp/recovery/reports/TASK-127-REPORT.md` | **本报告** |

**修改**

| 文件 | 说明 |
|---|---|
| `godot-mcp/tools/playtest_agent.py` | 新增 `PlayJevAgent` + `--agent=playjev` + `--probe-playjev`；提取 `action_criteria`；文档 |
| `godot-mcp/tools/playability_gate.py` | 仅帮助文本/模块文档（**另含上一批遗留的 TASK-128 `--base-url` 本体**，见 §9.3） |

**仓库外（有意不入库）**

| 路径 | 说明 |
|---|---|
| `F:\moonbit-hof-rs\runs\playability\*` | 定位留档、`PlayJev-src` 克隆、探针证据、服务日志（`runs/` 已 ignore） |
| `F:\models\PlayJev-0.8B\` | 权重 2.08 GiB（与 `F:\models\NeoHorse-Jev-4B` 同级） |
| `/opt/playjev-venv/`、`/opt/playjev/` | WSL 内的独立 venv 与源码副本 |

**未触碰**：`/opt/jev-venv`、8080 上的 Jev 服务（pid 730）、`F:\models\NeoHorse-Jev-4B`。
