# TASK-DR47-SMOKE-ADDENDUM — 准入门判据修正 + 调度者实测的活体前置（D219）

> **与 `TASK-DR47-SMOKE.md` 同读；本文件优先，并**取代**其 §2 第 3 点（"名字集合严格相等"）。**

## 1. 为什么修正：我原来的判据是错的

`TASK-DR47-SMOKE.md` §2 第 3 点要求"活体 `tools/list` 名字集合与夹具**严格相等**，否则停止"。
**这条在真机上是假的**，因为**契约总数 ≠ 单个端点的可见数**：引擎按 `scope` 把工具分到编辑器/游戏两个端点。

调度者在本机**实测**（原始输出，2026-09-29）：

```
LISTEN 9877  PID=108432
PATH=F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.exe
GET http://127.0.0.1:9877/mcp ->
{"connections":1,"frame_count":2738,"is_editor":true,"listening":true,"pending":0,
 "pending_connections":0,"port":9877,"server":"godot-mcp-rs","status":"ok",
 "tools":154,"transport":"streamable-http"}
引擎启动行：Godot Engine v4.8.dev.mono.custom_build.ba1587c71
[MCP] role=editor configured_port=9877 source=cmdline listen=true
```

**154 ≠ 177，但这不是缺陷**。集合关系（与引擎侧 M 线历史数字完全自洽）：

| 集合 | 大小 | 恒等式 |
|---|---|---|
| 契约总数 | **177** | 108 editor-only + **46 两端共有** + 23 game-only |
| **编辑器端点** | **154** | 108 + 46 |
| 游戏端点（M 线实测，需你在本批复核） | **69** | 23 + 46 |

参照点：171 条契约时是 editor 148 / game 69 / editor-only 102 / game-only 23，
即**交集恒为 46**；契约后来长出的 6 条工具全是 **editor-only**（与实现者报告 §3.2 的"新增 6 条"一致）。

---

## 2. 修正后的准入门（**必须照此判定**）

设 `F` = 夹具名集合（应为 177），`E` = 活体**编辑器端点**名字集合，`G` = 活体**游戏端点**名字集合
（`G` 只有在 `editor_play_scene` 成功后才可能存在）。依次判：

1. **`E ⊆ F`** —— 编辑器端点**不得**出现夹具里没有的名字。出现 ⇒ **停止**（真·合约漂移），把多出的名字列出。
2. **`|F \ E| == 23`**，且这 23 个名字**全部**是 `running_game_*` 通道。
   - 若差集不是 23、或含有非 `running_game_*` 的名字 ⇒ **停止**，按"缺少的 / 多出的 / 通道不符的"三列列出。
   - 这 23 条**不是缺失能力**：它们本就只在游戏端点。**不得**因为"编辑器端点取不到"就判缺陷。
3. **`name` / `description` / `inputSchema` 逐字比较**：对 `E ∩ F` 的每个名字逐字段比对；
   有差异 ⇒ 允许开跑，但**逐条列出**（这是"离线文档源 vs 活体"的已知风险面）。
4. **夹具专用字段**：通报你在 D218（验收报告 §2）已得的结论——验收者实测夹具
   **没有**夹具专用键（仅少了源文件顶层 `_meta`）。你只需复核一次，并写明夹具相对
   `tools_list.renamed.json` 多/少哪些键。
5. **并集判据（强判据，能做就做）**：若游戏端点可达，`|E ∪ G| == 177` 且 `|G| == 69`
   （= 108 + 46 + 23）。**做不到就如实标"未做"**，不得默认成立。
6. 记录：`E` 条数、`G` 条数（若可达）、`GET /mcp` 的 `tools` 字段、以及**你把哪 23 条判为 game-only**。

> 若第 1/2 条不通过 ⇒ **停止并报告**，不要开跑冒烟（那会浪费一整轮真机预算且证据不可比）。

---

## 3. 游戏端点怎么来（**不许自己起游戏进程**）

- 游戏端点**只能**由 `editor_play_scene` 创建：它给子进程注入 `--mcp-port`，
  并在响应里回 `mcp_port` / `mcp_port_source` / `endpoint` / `pid`。
- **禁止**你自己用别的端口手起一个游戏进程来"验证集合"——那会污染端口归属并使证据不可比。
- 若你需要在冒烟**之前**就拿到 `G`（例如为了先判 §2 第 5 条）：这**不允许**，
  因为那需要调用一次 `editor_play_scene`（属于真机动作）。
  此时请把第 5 条标为"**冒烟后再判**"，并在报告里说明顺序。

---

## 4. 其余要求与禁项

`TASK-DR47-SMOKE.md` §1（前置核对）、§3–§7 全部照旧，特别重申：

- **不得**杀掉/重启/抢占 9877 上的编辑器（PID **108432**，是我启动的；它必须活到最后）；
- **不得**自己删除/修改 `.workspace/mario` 里的任何东西；
  调度者已用产品路径（`hoh init`，不带 `--fresh-workspace`）完成真实清理，结果是：
  `addons/` 已空、`.godot/extension_list.cfg` **已删除**、`project.godot` 中 `editor_plugins` 计数 **0**、
  而 `scenes/main.tscn` 与全部 `scripts/*.gd` **完好**。这些**不用你重做**，但你可以复核；
- **不得**改 `src/**`、`tests/**`、`config/hoh.yaml`、`godot-mcp/**`、`PRD-mario.md`；
  发现缺陷就写缺陷，**不要自己修**；
- **不得** `git commit`/`push`/stage；不删改既有 `runs/smoke-t1..t5`；
- 密钥只经环境变量，**不得**出现在任何输出/日志/报告/`runs/**` 里（只可打印长度）。

---

## 5. 报告里必须新增的一节

除 `TASK-DR47-SMOKE.md` §7 的 8 节外，再加一节：
**"§9 端点集合核对（D219 修正判据）"**，逐条给出 §2 的 1–6 项结论与原始输出，
并显式区分「**实测**」与「**未做**」。

---

## 6. 密钥怎么装进环境（**已验证可行的读取方式**）

`config/model.secret.env` 是给人工 source 的文件，**不会被自动读取**；`hoh run` 需要进程环境变量
`HOH_MODEL_API_KEY`（其次 `OPENAI_API_KEY`）。用 **bash**（不要用 PowerShell 的 `Get-Content`，
对无 BOM 的 UTF-8 文件它会读成乱码）：

```bash
export HOH_MODEL_API_KEY=$(grep '^HOH_MODEL_API_KEY=' config/model.secret.env | cut -d= -f2- | tr -d '\r\n')
echo "key length: ${#HOH_MODEL_API_KEY}"     # 只可打印长度，不得打印值
```

**禁止**把密钥写进任何命令回显、日志、报告、`runs/**`；只允许打印**长度**。
