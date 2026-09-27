# TASK-125 — NeoHorse-Jev 本地运行环境准备 + 模型权重下载（与 TASK-124 并行）

> 交接方式：子代理**只读本文件**执行；完成后把报告写到
> `F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-125-REPORT.md`，**返回值只给该路径**。
> 本文件自包含。**本轮允许联网下载**（用户已明确批准"模型下载与环境部署可同步进行"）。
> 同期另有子代理在改 `tools/playtest_agent.py`（TASK-124），**不要碰那个文件**。

---

## 0. 目标（两件事，可并行推进）

1. **下载模型权重**：`TokenRhythm/NeoHorse-Jev-4B` 完整包（约 **9.15 GB**），并**逐文件校验 SHA256**。
2. **准备本地运行环境**：让 Jev 能在这台机器上起服务（`/health` 可访问）。**先探测、再决定**，
   遇到需要"改 Windows 功能 / 重启"的操作**停下来报告**，不要擅自执行。

---

## 1. 已核实的下载来源与文件清单（一手来源：ModelScope，HTTP 200）

* HuggingFace **在本机不可达**（实测 HTTP 000 / 连接超时 21s）→ **必须走 ModelScope**。
* GitHub 仓库无 Release（`/releases` → `[]`）→ 权重只在 ModelScope。
* 许可 **Apache-2.0**、`IsAccessible=1`、**匿名 API 可取**（无需 token）。总 `StorageSize` = 9,145,375,991 B。
* **两个可信下载通道**（先用①，失败换②）：
  1. ModelScope 官方 CLI（推荐，自带断点续传）：`pip install modelscope` 然后
     `modelscope download --model TokenRhythm/NeoHorse-Jev-4B --local_dir "<DEST>"`
     （若 CLI 参数不同，以 `modelscope download --help` 实际输出为准并记录）；
  2. 文件 API 直链（TASK-123 已实测 200）：
     `https://www.modelscope.cn/api/v1/models/TokenRhythm/NeoHorse-Jev-4B/repo?Revision=master&FilePath=<相对路径>`
     —— 用 `curl.exe -sSL --ssl-no-revoke`（本机 schannel 吊销检查会导致 TLS 失败，**必须加
     `--ssl-no-revoke`**）+ `-C -` 续传 + `-o <绝对路径>`。
* 文件清单与**精确字节数**（必须逐个对上）：

| 相对路径 | 字节 |
|---|---|
| `backbone/model-00001-of-00003.safetensors` | 3,991,297,968 |
| `backbone/model-00002-of-00003.safetensors` | 3,968,952,928 |
| `backbone/model-00003-of-00003.safetensors` | 1,118,364,688 |
| `pointer_head.safetensors` | 5,245,232 |
| `tokenizer/tokenizer.json` | 19,989,325 |
| `tokenizer/chat_template.jinja` | 7,756 |
| `tokenizer/tokenizer_config.json` | 1,123 |
| `backbone/model.safetensors.index.json` | 61,862 |
| `backbone/config.json` | 3,128 |
| `backbone/preprocessor_config.json` | 390 |
| `model_manifest.json` | 716 |
| `environment.json` | 404 |
| `SHA256SUMS` | 6,741 |
| `dist/neohorse_decision-1.0.0-py3-none-any.whl` | 24,789 |
| `example_request.json` | 565 |
| `package/`（cli/engine/server/systemone/vision/image_input/_inference.py 等小文件） | 小 |
| `vision/`（example.py / http_example.py / predictor.py / README.md / base_vision_provenance.json / verification.json） | 小 |
| `infer/vllm/`、`infer/sglang/`（launch / infer / head / weight_mapping / vision / `jev_runtime/`） | 小 |
| `DEPLOYMENT.md`、`README.md`、`infer/README.md` | 12,390 / 34,818 / 4,098 |
| `assets/jev-six-demo-grid.gif`、`assets/jev-snake-demo.gif` | 23,558,309 / 17,563,273（**演示 GIF，可跳过**，报告里说明是否跳过） |

* **落点**：默认 **`F:\models\NeoHorse-Jev-4B`**（**故意放在仓库之外**；仓库内若出现权重会被
  `.gitignore` 的 `godot-mcp/models/`、`**/*.safetensors`、`**/*.gguf` 规则挡住，但仍以仓外为准）。
  **先查磁盘可用空间**（目标盘与临时盘都要 ≥12 GB），把结果写进报告。
* **校验**：下载 `SHA256SUMS`（6,741 B，逐文件校验和）→ 下完后**逐文件算 sha256 并对表**；
  不符的**如实报出并说明是否重下**。**绝不允许**"文件在就算成功"。

---

## 2. 环境准备：**先探测，再决定；不可逆动作先报告**

### 2.1 必做探测（只读，逐条记录原始输出）
1. 本机 GPU：`nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv`（已知：RTX 4090 24 GB，驱动 616.56）
2. 内存/磁盘：总内存（已知约 128 GiB）、各盘可用空间
3. WSL：`wsl --status`、`wsl -l -v`（**只读**；记录是否已装、有无发行版、WSL 版本）
4. Python：`py -0p`、`python --version`、`where python`（Jev 运行时要求 **Python 3.12**）
5. pip 与镜像可达性：PyPI 直连与镜像（如 `https://pypi.tuna.tsinghua.edu.cn/simple`）各测一次
6. 是否已有 conda/uv/venv 工具；CUDA toolkit 是否存在（`nvcc --version`）

### 2.2 环境路线（按探测结果选一条，写明理由）
* **首选 WSL2**（厂商记录栈是 Linux：python 3.12.10 / torch 2.8.0 / transformers 5.17.1 /
  triton 3.7.1 / flash-linear-attention 0.5.2 / CUDA 12.8）。若 WSL 已装且有发行版：
  在 WSL 内建 venv → 装依赖 → 准备起服务（GPU 直通需 WSL 内 `nvidia-smi` 可见）。
* **若 WSL 未安装**：**不要**擅自 `wsl --install` / 启用 Windows 功能 / 重启。**停下来**，
  在报告里写清"需要用户同意启用虚拟化功能并可能重启"，并给出确切的候选命令。
* **原生 Windows 兜底**：仅在能装齐依赖时尝试（注意 `triton` 与 `flash-linear-attention`
  基本只有 Linux 轮子，纯 Windows 很可能失败）。失败就**如实报告失败点**，不要反复试到超时。
* 依赖按仓库给定：`infer/vllm/requirements.txt` = `torch>=2.6`、`transformers==5.16.1`、
  `pydantic>=2,<3`、`safetensors>=0.4`、`requests>=2.31`、`Pillow>=10`；
  原生运行时另需 `fastapi==0.141.1`、`uvicorn==0.53.0`、`starlette==1.6.0`、`httpx==0.28.1`、`pillow==12.3.0`
  与 wheel：`python -m pip install --no-deps dist/neohorse_decision-1.0.0-py3-none-any.whl`。
  （厂商 `environment.json` 记录的是 torch 2.8.0 / transformers 5.17.0；requirements 写 5.16.1
  —— **两个版本号不一致，先把差异写进报告**，装哪个要说明理由。）

### 2.3 起服务（**只在环境就绪时做**）
* 原生：`CUDA_VISIBLE_DEVICES=0 neohorse-decision serve --model-dir "<DEST>" --port 8080`
* 就绪判据：`GET /health` 返回可读状态（并记录其 `input_modalities`）。
* **不要**打 `/v1/models`（Jev 不提供）；**不要**指望 `/v1/chat/completions`。
* 起服务用**后台 job**（或 `Start-Process`），日志落 `runs/playability/jev-serve-*.log`；
  端口占用前先查（避开 9877/9888/9889）；跑完**留下或按需停掉**，报告里写明当前状态。

---

## 3. 硬性约束（铁律）

1. **禁止一切 shell 重定向**（`>`、`>>`、`*>`、`2>&1`）；用 `-o`/`-OutFile`/Python 落盘。
2. **破坏性命令默认拒绝**（含 `Remove-Item -Recurse`、通配符、`..`）。
3. 命令尽量**从 cmd 启动**；中文写盘若乱码用 cmd/bash 或 Python UTF-8。
4. **不得改动用户机器的安全设置**（不关 SAC、不改注册表、不启用 Windows 功能）。
5. **不得**把权重或虚拟环境下进 git 仓库；**不得**对仓库做 `git add`（本任务不改代码）。
6. 下载**必须可续传**；大文件下载用后台 job 并**周期性报告进度**（不要静默 long-run）。
7. **不得杀**用户已有进程（尤其是 GameViewer/编辑器）；只操作自己起的进程。

---

## 4. 验收判据（报告逐条给证据）

| 编号 | 判据 | 证据 |
|---|---|---|
| M1 | 磁盘/内存/GPU 探测完成 | 原始命令输出 |
| M2 | 权重按清单**逐文件**下载且字节数对表 | `Get-Item` 长度 vs §1 表格 |
| M3 | **SHA256 逐文件校验** | 与 `SHA256SUMS` 对表的结果（含不符项） |
| M4 | 跳过项声明 | 演示 GIF 是否跳过 |
| M5 | 环境探测 | WSL/Python/pip/镜像逐条原始输出 |
| M6 | 环境路线与理由 | 选了哪条、为什么、放弃了哪条 |
| M7 | 依赖安装结果 | 实际安装命令 + 版本清单（`pip freeze` 关键行） |
| M8 | 服务是否起来 | `GET /health` 原文；未起来就写清失败点与报错 |
| M9 | 不可逆动作是否被拦住 | 若需启用 Windows 功能/重启，写明"已停下待批" |
| M10 | 铁律遵守 | 明写：无重定向、无破坏性命令、未改安全设置、未动仓库 |

---

## 5. 报告落点与返回值

* 报告：`F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-125-REPORT.md`
  （含：探测原始输出、下载清单与校验结果、环境路线与安装记录、服务状态与日志路径、
  待用户决定项、耗时与当前后台 job 状态）。
* **返回值只给报告路径 + 一行状态**（done/partial/failed）。
* 若下载量大导致时间长：**先让下载跑起来**，把"环境探测 + 路线决定"做完写进报告，
  下载完成后**追加更新报告**，再返回路径。
