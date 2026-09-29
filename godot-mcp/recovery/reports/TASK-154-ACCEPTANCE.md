# TASK-154-ACCEPTANCE — TASK-154 独立验收报告

> 验收者：**独立验收子代理**（无上游对话上下文；未继承实现者或调度者的任何结论）。
> 被测：引擎仓 `F:\moonbit-hof-rs\godot-mcp\godot` HEAD **`fc63af77c3`**（起始 HEAD `28432f859f`，4 个本地提交）；
> 外层仓 `F:\moonbit-hof-rs`（= hof-rs 仓）HEAD **`f829dc2`**。
> 自产证据：`F:\moonbit-hof-rs\godot-mcp\recovery\work\task154-acc\`（脚本 + `*.out.txt`；本轮结束后引擎仓 `git status --porcelain` = 0 行、外层仓仅 `?? godot-mcp/recovery/work/task154-acc/`）。
> 本报告**未提交、未 stage**。
> 任务书要求的九个核心复核项**全部由我自己重跑**；结论与实现者报告一致的部分是我复现后的独立确认，不一致/未覆盖的部分在本报告 §5/§6/§7 显式区分。

---

## 1. 结构化结论 + 真实命令与退出码

### 1.1 结构化结论（机器可读）

```json
{
  "verdict": "pass",
  "criteria": [
    { "id": "DECOUPLED", "pass": true,
      "evidence": "git grep -n 'moonbit-hof-rs' 两个脚本 => 4 行命中，全部以 '#' 开头（注释）；非注释命中 0。9877 非注释命中 = 每文件 2 行，均为 [regex]::Escape('9877')：mcp029 L134/L296、mcp032 L132/L359，唯一使用点是 L135/L133 的 `IsMatch($PSScriptRoot, pat)` -> exit 4，以及 L297/L360 的 `-not IsMatch(...)` AND 进 test_ports_only 检查（只会拒绝/判红，从不选择端口值）；端口参数被 $TestPorts=@(9888,9889) 的 -notcontains 拒于启动前。mcp032 已无 mcp_port_guard.ps1 的 dot-source（仅 4 处注释提及）；mcp_port_guard.ps1 的 worktree/HEAD/28432f859f blob 均为 cfb7e190d38b6afff7cda3e8028be7990074a6a0，仍被 29 个脚本以真实 dot-source 语句引用（mcp032 不在其中）。" },
    { "id": "PORT_GUARD", "pass": true,
      "evidence": "7 个用例（mcp029 -EditorPort/-GamePort 9877、mcp032 -EditorPort/-GamePort 9877、mcp029 -EditorPort 1234、mcp032 -GamePort 9887、路径含 9877 的副本）全部 exit=4、OutRoot created=False、观察到的子进程数=0；静态控制流：guard 退出点 mcp029 L131/L137、mcp032 L129/L135 早于一切 `& $Curl`（L180/236、L176/266）、Start-Process（L226/L256）、OutRoot 创建（L258/259、L292/293）；两个脚本内无任何进程内网络 API（Invoke-WebRequest/Invoke-RestMethod/TcpClient/HttpClient/WebClient/System.Net 命中 0），网络只经 curl.exe 子进程；守卫前唯一执行的代码是 dot-source mcp_import_guard.ps1（该文件顶层只有 3 个 function 定义，进程/IO/网络语句全在函数体内）与一次本地文件读取。收尾 netstat 9870..9889 LISTENING = 0。" },
    { "id": "ARTIFACT_UNTOUCHED", "pass": true,
      "evidence": "modules/mcp_server/docs/tools_list.renamed.json：bytes=154272、sha256=fd00c75e5174ec923d5a91c0323afa0804f523b385eae3d4f78d8c71e1f895df、worktree blob=HEAD blob=28432f859f blob=3b1b191dc42f1cec8bc7cdd3504247c935b52f5e；`git diff --name-only 28432f859f..HEAD -- <artifact>` = 0 行；本批 diff --name-status 只有 3 个 M（MCP-SERVER-HANDOVER.md + 两个脚本）。g05 自跑时也从工件本身重算并打印 bytes=154272 sha256=fd00c75e…。" },
    { "id": "GATES.10", "pass": true,
      "evidence": "cd F:\\moonbit-hof-rs\\godot-mcp && powershell -NoProfile -ExecutionPolicy Bypass -File tools\\run_gates.ps1 -RunGates -Tag task154_acc => 运行器 exit 0，g01..g10 全部 GATE_EXIT=0（10/10）。逐门自读 runs\\gates\\task154_acc\\gNN.stdout.txt：g05 [PASS]=30 / [FAIL]=0；g04 3/3（editor=154 / game=73 / contract=177 / guard_user_port_9877 PASS）；g01 160/160（6801 断言）、g02 1586/1586（431114 断言）；g07 PROBES 10/10；g08 UNCLASSIFIED=0（total 130）；g09 DIFF_COUNT=6 SAFE_COUNT=6 RED_COUNT=0 RESULT PASS；g10 22/22（21 个 case + guard_user_port_9877）。preflight 锚点=035edfce7、HEAD=fc63af77c、verdict=ANCHOR_STRUCTURAL_EQUIVALENT。" },
    { "id": "PREEXISTING_ATTRIBUTION", "pass": true,
      "evidence": "①mcp032 `-f`：本批 10 个 hunk（-41/-44/-63/-69/-74/-191/-194/-292/-300/-515）没有一个覆盖基线 L287..291；基线 L285..291 与 HEAD L346..352 逐字符相等（-ceq 全 True）；blame 与 `git log -S \"hand-built {'Material','material'} JSON\"` 均指向 54200f0d77（2026-09-26）；同一扫描在基线与 HEAD 各得 6 个会抛 FormatError 的 `-f` 字面量；未改动的 mcp032 实跑在第 348 行抛错 exit=1。②mcp029 两处红：自跑实得 20 checks / 2 failed（wire_clear_default_is_false、wire_description_names_shared_file），而 old_fixture_readable/wire_clear_description_kept 由改前的恒 FAIL 变为 PASS；实现者那 5 条判据表达式在本批 diff 中出现 0 次；本批未触碰任何 src/二进制/契约（引擎二进制 mtime 2026-09-29 08:31:03 早于本批首提交 10:18:40，--version=035edfce7）；输入字节等价（引擎基准 = hof-rs `db2eed7^` 夹具 blob 543b49b2…、48749 B、sha256 8f8051c4…）。⇒ 两个红点均**不是**本批引入。" },
    { "id": "G09.HUMAN_GUARDRAIL", "pass": true,
      "evidence": "先证明 pathspec 能命中：`git -C <engine> ls-files -- modules/mcp_server/scripts/check_engine_anchor.ps1` => 1 行、check_hardcoded_counts.py => 1 行；`git -C F:\\moonbit-hof-rs ls-files -- godot-mcp/tools/run_gates.ps1` => 1 行。再取证：三者区间 diff 全 0 行，且 blob 三相等——check_engine_anchor.ps1 = 8f048b31ff049bc8ec394a86b0b0d37ac72823d4（worktree=HEAD=28432f859f）、check_hardcoded_counts.py = 07283d48866a119d4bf9be13843a6c0ec7fd0456（同）、run_gates.ps1 = b3c5ea655b949836f7dc640fc54c255bc526cb16（worktree=HEAD）。" },
    { "id": "TRAPS", "pass": true,
      "evidence": "陷阱①：`cmd /c ... cat-file blob db2eed7^:tests/fixtures/mcp/tools_list.json` 交给 git 的实际命令行是 `db2eed7:tests/...`（cmd 吞掉 `^`），得到 71481 B / sha256 50c5fb42…（= HEAD 内容，`HEAD:path` 与 `db2eed7:path` 同为 blob fe420c81）；正确读法得到 48749 B / 8f8051c4…：`git cat-file blob 543b49b2583bf06c3aba2a320649a31eda272e3e` 与 .NET Process+StandardOutput.BaseStream 两种读法结果一致。陷阱②：对不存在的 pathspec，`git diff --name-only` 与 `git diff --quiet --exit-code` 均 0 行 / exit 0 且无报错；`ls-files` 才是能证明命中的工具（tools/run_gates.ps1 -> 0 行，godot-mcp/tools/run_gates.ps1 -> 1 行）。" },
    { "id": "ENCODING", "pass": true,
      "evidence": "mcp029 26174 B、mcp032 35879 B：无 BOM、非 ASCII 字节 = 0、CR = 0；mcp029 的 [char]0x5171 在 L63 的**代码行**上（`-join ([char]0x5171, [char]0x4EAB)`，行尾注释），中文由码点构造；mcp029 端到端回放正常（20 检查全跑完并打印中文证据 '获取测试结果报告' 等，无乱码）。" },
    { "id": "GUARDS", "pass": true,
      "evidence": "未 push：engine `rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild` = 28432f859f，`rev-list --left-right --count origin...HEAD` = `0  4`，engine status = 0 行。hof-rs 侧 `git status --porcelain` 只有我这个未跟踪证据目录，`git diff/diff --cached --name-only` 皆空，夹具 tests/fixtures/mcp/tools_list.json = 71481 B / sha256 50c5fb42… / blob fe420c81（= HEAD blob）。无新依赖（本批只有 3 个 M，无新增文件）。既有检查未删/未放宽：mcp029 Check-id 20→20（仅 port_9877_owner_before/_after → test_ports_only/test_ports_released），mcp032 38→39（仅 port_9877_guard → 两条 test_ports_*），其余 id 全部保留。日期未编造：4 个提交时间戳 2026-09-29 10:18:40/10:18:48/10:18:56/10:37:49 与本机 Get-Date 2026-09-29 10:49:30 +08:00 同源；文档引用的 54200f0d77 = 2026-09-26 10:18:48 +0800，且该提交确实引入 `_meta.generated_from` 的 hof-rs 路径（引擎仓 blob 0775ffb0…）。" }
  ],
  "defects": [
    { "id": "DEF-1", "severity": "info",
      "what": "任务书 §2.8 的表述「mcp029 的 [char]0x5171 转义是否仍在注释行内」与被测实现不符：该转义在 L63 是可执行代码行（行尾带注释）。这正是它可工作的唯一形式（若放进注释就等于中文没被构造、非 ASCII 字节会回来）。这不是缺陷，仅为任务书措辞与实现形态不一致，记录以免后续复核者据此误判。",
      "reproduction": "Select-String mcp029 -Pattern '\\[char\\]0x' => 仅 L63: `$sharedWord = -join ([char]0x5171, [char]0x4EAB) # the word \"shared\"`；该文件非 ASCII 字节 = 0。" },
    { "id": "DEF-2", "severity": "info",
      "what": "实现者报告 §2.2 写「mcp_port_guard.ps1 仍被 30+ 个脚本点源使用」，精确值是 **29** 个脚本含真实 dot-source 语句（30 个文件只是在文本里提到该名字，其中 mcp032 的提及全部在注释里）。仅报告措辞不精确，不涉及交付物行为。",
      "reproduction": "对 modules/mcp_server/scripts/*.ps1（排除模块自身）匹配 `^\\s*\\.\\s*\\(Join-Path \\$PSScriptRoot 'mcp_port_guard\\.ps1'\\)` => 29 个文件，mcp032 不在其中。" },
    { "id": "DEF-3", "severity": "info",
      "what": "未改动的 mcp032 在本批 HEAD 上**完全无法运行**（6 个既有 `-f` 花括号缺陷，第 348 行即崩），因此本批对 mcp032 的改动只有在「把 6 处 `{` 双写」的临时副本上才能被端到端实测；仓库原件从未被本批或本验收者修改。该缺陷由实现者发现并已立 TASK-155，本验收独立确认其存在与归属。",
      "reproduction": "powershell -File mcp032_d3_d4_d6_evidence.ps1 -OutRoot <tmp> => exit=1，`FormatError ... At ...:348 char:1`；副本仅 6 行不同（L349/475/480/490/494/498）后 39 checks / 2 failed。" }
  ],
  "risks": [
    "9877 的「零网络调用」由三件事共同支撑：守卫退出点早于所有 curl/Start-Process、脚本内无进程内网络 API、以及进程树采样 0 子进程 + OutRoot 未创建。进程树采样无法观测「脚本进程内部瞬时发出的网络调用」——但该脚本不存在此类调用（grep 命中 0），残余不确定性仅限于此。",
    "两个脚本仍会调用 `netstat -ano -p TCP`（Get-ListenerPid，用于 9888/9889 的占用/释放判据）。这是对本地套接字表的一次性被动枚举，会顺带显示机器上任何 9877 监听者；它不 bind、不 connect、也不按 9877 过滤或断言（旧版对 9877 的显式枚举与 pid 断言已随 $UserPort 删除）。",
    "冻结契约 tools_list.renamed.json 的 `_meta.generated_from` 仍指向 hof-rs 路径（连同 `generated_from_sha256=8f8051c4…`），这是历史字段；HANDOVER §3.10 已声明其为历史溯源。任何后续工件的重生成都会改变 blob（现有判据会红），本轮已验证其未被触碰。",
    "mcp029 实跑会向其自身 app_userdata 日志目录追加 Godot 日志并留下 OutRoot（recovery/work/task154-acc/live-029 等）；这是脚本一贯行为，未触碰决策者真实工程。",
    "g09 三道护栏中的第 3 条（三个判据文件零 diff）仍是人工核验项（D232 裁决如此）。本条的本轮证据是「pathspec 先证明命中 + blob 三相等」，但它不是判据脚本内可复算的规则。"
  ],
  "unverified": [
    "未运行两个脚本的**旧版本**（旧 mcp029 会 `Get-ListenerPid -Port_ 9877`，违反「绝不探测 9877」；旧 mcp032 会带 9877 记账）。因此「旧版红集合」不是实测，而是由「本批未触碰 src/二进制/契约 + 输入字节等价 + 判据表达式未被本批修改」推出的结论（见 §5）。",
    "未重建引擎（本批未改任何编译输入，`--version` 仍 035edfce7，二进制 mtime 08:31:03 早于本批提交）；故未复核「重建后线上是否携带 TASK-029/032 的 override 文本」——那属于 TASK-155 的范围。",
    "未独立复现任务书 §1 那句「十门实际执行文件的可执行跨仓引用扫描 = 0」的全量 AST 扫描；我只复核了两个脚本不在十门/accept_m1 命令列表中（Select-String 命中 0），以及 mcp032 不再 dot-source 端口模块。",
    "§2.4（g09 护栏机器化）本批未做，我也未复核实现者探针仓库里 `ANCHOR_STALE_COMPILED` 反例的每一次内部细节，只复核了现行 g09 判据与 RED_COUNT=0（任务书 §2 项 4/9 的口径）。"
  ]
}
```

### 1.2 关键命令与真实退出码（全部由我本轮执行）

| # | 命令（工作目录） | 真实退出码 | 结果摘要 |
|---|---|---|---|
| 1 | `git -C F:\moonbit-hof-rs\godot-mcp\godot status --porcelain` / `rev-parse HEAD` | 0 | 0 行；`fc63af77c33368c4a1bb839c95d19750554f63a3` |
| 2 | `git -C <engine> diff --stat 28432f859f..HEAD` | 0 | 3 files changed, 181 insertions(+), 27 deletions(-) |
| 3 | `git -C <engine> grep -n -I -- 'moonbit-hof-rs' -- <两个脚本>` | 0 | 4 行，全部注释 |
| 4 | `git -C <engine> grep -n -I -- '9877' -- <两个脚本>` | 0 | 10 行：6 注释 + 4 行 `[regex]::Escape('9877')` |
| 5 | `powershell -NoProfile -ExecutionPolicy Bypass -File .\c2_refusal_guard.ps1`（`recovery\work\task154-acc`） | 0（驱动）／每用例 **4** | 7 用例：exit 4、OutRoot 未创建、子进程 0 |
| 6 | `cd F:\moonbit-hof-rs\godot-mcp; powershell ... -File tools\run_gates.ps1 -RunGates -Tag task154_acc` | **0** | 10/10 `GATE_EXIT=0`；`summary=…\runs\gates\task154_acc\summary.txt` |
| 7 | `python check_hardcoded_counts.py --root <28432f859f 导出树>` | 0 | FROZEN 70 / total **126** / UNCLASSIFIED 0 |
| 8 | `python check_hardcoded_counts.py`（HEAD） | 0 | FROZEN 74 / total **130** / UNCLASSIFIED 0 |
| 9 | `powershell ... -File modules\mcp_server\scripts\mcp029_clear_default_evidence.ps1 -OutRoot …\live-029` | **1** | 20 checks, 2 failed（×2 条红线复现） |
| 10 | `powershell ... -File <mcp032 临时副本，仅 6 处 `{` 双写> -OutRoot …\live-032-probe` | **1** | 39 checks, 2 failed（D6 ×2） |
| 11 | `powershell ... -File modules\mcp_server\scripts\mcp032_d3_d4_d6_evidence.ps1 -OutRoot …`（**未改动原件**） | **1** | 第 348 行 `FormatError`，未走完 |
| 12 | `git -C <engine> hash-object/recalc`（工件） | 0 | 154272 B / `fd00c75e…` / blob `3b1b191d…`（三处相同） |
| 13 | 尾部端口复核 `netstat -ano -p TCP`（9870..9889） | 0 | LISTENING = **0** |
| 14 | 临时副本删除后 `git -C <engine> status --porcelain` / `diff --stat` | 0 | 0 行 / 空 |

---

## 2. 逐项核对表（任务书 §2 九项）

| # | 任务书要求 | 我的独立做法 | 结论 |
|---|---|---|---|
| 1 | 去跨仓成立；9877 只用于拒绝；mcp032 不再 dot-source 端口模块、模块未改且仍被引用 | 自跑 git grep（注释/非注释分开判读）+ 逐行读守卫使用点 + blob 三比 + dot-source 语句精算 | **通过**（0 处非注释指向 hof-rs；4 处 9877 非注释全为拒绝字面量；mcp032 已无 dot-source；模块 blob `cfb7e190…` 三处相同；29 个真实消费者） |
| 2 | `-EditorPort/-GamePort 9877` ⇒ exit 4、在任何进程/网络动作之前、OutRoot 未创建；9870..9889 收尾无 LISTENING | 7 用例实测 + 控制流行号对照 + 子进程采样 + 进程内网络 API 扫描 + 尾部 netstat | **通过** |
| 3 | 工件未重生成（blob/字节/sha）；HANDOVER 只改文档、不把未发生的事写成事实 | 独立重算 sha/bytes/hash-object，与 `28432f859f` 及 g05 打印值三方对齐；读 §3.10 全文并逐句找可证伪点 | **通过**（措辞与事实相符：见 §1.1 ARTIFACT_UNTOUCHED、§5） |
| 4 | 十门 10/10；g05 30/0、g04 3/3(154/73/177)、g08 UNCLASSIFIED=0、g10 22/22；g08 计数面 126→130 自判 | 自跑门运行器 + 自读每门 stdout（不信 tail）+ 自己导出 28432f859f 模块树复算 g08 | **通过**（+4 全部是新注释里的 TASK-152/153 字面量，全部 FROZEN，无分类漏网） |
| 5 | 两个 pre-existing 红点的独立归因；若为本批引入 ⇒ fail | hunk 覆盖分析 + 基线/HEAD 逐字符比对 + blame + `git log -S` + 独立重算 6 处 `-f` + 实跑（原件与打补丁副本）+ 二进制 mtime/版本 + 判据表达式 diff + 工件 blob | **通过 / 均判为 pre-existing**（详 §5） |
| 6 | g09 护栏 3 的有效空 diff 证据（先证明 pathspec 命中） | `ls-files` 先证明命中，再给出区间 diff 0 行 + blob 三相等 | **通过** |
| 7 | 两个陷阱实测复现与正确读法 | 四个路径/读法对照 + exit code 对照 | **通过** |
| 8 | 编码安全：0 非 ASCII、无 BOM；`[char]` 转义与回放 | 逐字节扫描 + 实跑 mcp029 端到端 | **通过**（另见 DEF-1 的措辞说明） |
| 9 | 禁区自查：未 push、hof-rs 零改动、夹具未变、无新依赖、无检查被删/放宽、未编造日期 | 逐项自跑 | **通过** |

---

## 3. 反例清单（我主动构造的失败/边界用例）

1. **端口集合外任意值**：`mcp029 -EditorPort 1234`、`mcp032 -GamePort 9887` ⇒ 均 exit 4、OutRoot 未创建、子进程 0。守卫不是只挡 9877 的黑名单，而是 `{9888,9889}` 白名单。
2. **路径字面量分支**：把 mcp029 复制到 `…\task154-acc\path-with-9877-literal\` 并以**合法端口** 9888 运行 ⇒ exit 4（"the user editor port literal appears in the launch context …"），证明 `$PSScriptRoot` 分支真的会触发、且它也只能拒绝（不会因为路径含 9877 而改用 9877）。
3. **不存在 pathspec 的假绿**：`git -C <outer> diff --name-only -- tools/run_gates.ps1`、`-- definitely-not-a-file.txt`、甚至 `git diff --quiet --exit-code` ⇒ 全部 0 行 / exit 0 / 无报错；而真实改动路径 `mcp029_clear_default_evidence.ps1` 用 `--quiet --exit-code` ⇒ exit 1。证明「空 diff」本身不是证据，必须先证明 pathspec 命中。
4. **cmd 的 `^` 被吞**：`git cat-file blob db2eed7^:…` 经 `cmd /c` 变成 `db2eed7:…`（用 `cmd /c echo` 打印实际命令行证明）；结果 71481 B / `50c5fb42…`，与 `HEAD:path` 是同一 blob（`db2eed7:path` = `HEAD:path` = `fe420c81…`），而正确读法 48749 B / `8f8051c4…`。这会让人误得「hof-rs 旧夹具已不存在」。
5. **g08 的非空洞复核（反向）**：把 28432f859f 的模块树导出后复算 ⇒ 126/70；HEAD ⇒ 130/74；两侧 UNCLASSIFIED 均为 0；逐行 diff 显示新增的 4 行恰好是 mcp029:75/76 与 mcp032:78/79 的注释。⇒ 计数面变化有明确出处，不是分类器被放宽（判据文件 blob 未变）。
6. **mcp032 原件的边界**：不修改仓库、直接原样运行 ⇒ 在第 348 行崩（`{'Material','material'}` 打破 `-f`），这本身就是反例：该脚本在 HEAD 上**不可能**产出任何证据；我用只把 6 处 `{` 双写的临时副本（diff 恰好 6 行）才拿到 39/2 的实测。
7. **「拒绝」与「选择」的分离**：守卫生成的两个 pattern 变量（`$portLiteralPattern` / `$userPortLiteralPattern`）在全文仅各有 2 处使用（exit 4 / 否定的 Check 条件），没有任何 `--mcp-port=$UserPort` 或 `Get-ListenerPid -Port_ 9877` 之类的「选择」路径 —— 已用 Select-String 列出全部使用点。

---

## 4. 两个陷阱的实测复现与正确读法

### 陷阱 ①：`cmd` 把 `^` 当转义符

```
cmd /c "echo git -C F:\moonbit-hof-rs cat-file blob db2eed7^:tests/fixtures/mcp/tools_list.json"
  -> git -C F:\moonbit-hof-rs cat-file blob db2eed7:tests/fixtures/mcp/tools_list.json     # ^ 已被吞
```

| 读法 | 字节 | sha256 | blob |
|---|---|---|---|
| `cmd /c … db2eed7^:…`（**陷阱**，实际是 `db2eed7:…`） | 71481 | `50c5fb4204ee…` | `fe420c81eef34c09b5b679098e4fecd7b2d9574` |
| `git cat-file blob 543b49b2583bf06c3aba2a320649a31eda272e3e`（正确 A） | 48749 | `8f8051c4c0f8…` | `543b49b2…`（= `db2eed7^:…`） |
| .NET `Process` + `StandardOutput.BaseStream.CopyTo(FileStream)`（正确 B） | 48749 | `8f8051c4c0f8…` | 同上 |

交叉确认：`git rev-parse db2eed7^` = `b6d9282f5a…`；`git rev-parse db2eed7^:tests/fixtures/mcp/tools_list.json` = `543b49b2…`；`HEAD:path` 与 `db2eed7:path` 同为 `fe420c81…`（⇒ 陷阱输出**看起来像 HEAD**，所以尤其容易骗过复核者）。
**正确读法**：用已知 blob id，或经 `.NET Process` 的 `BaseStream` 取原始字节（**不要**经过 cmd 重定向、也不要经过 PowerShell 文本管线）。

### 陷阱 ②：`git diff` 对不存在的 pathspec 静默

| 仓库 | pathspec | `diff --name-only` 行数 | exit | `ls-files` 行数 |
|---|---|---|---|---|
| `F:\moonbit-hof-rs` | `tools/run_gates.ps1` | 0 | 0 | **0**（没命中！） |
| `F:\moonbit-hof-rs` | `godot-mcp/tools/run_gates.ps1` | 0 | 0 | **1**（命中） |
| `F:\moonbit-hof-rs` | `definitely-not-a-file.txt` | 0 | 0 | 0 |
| engine | `modules/mcp_server/scripts/does_not_exist.ps1` | 0 | 0（连 `--quiet --exit-code` 也是 0） | — |
| engine | `modules/mcp_server/scripts/mcp029_clear_default_evidence.ps1`（真实改动） | 1 | 0（`--quiet --exit-code` ⇒ **1**） | 1 |

**正确读法**：任何以 `git diff <pathspec>` 为空的「未变更」证据，都必须先用 `git ls-files -- <pathspec>`（或 `git diff --stat` 出现文件名）证明该 pathspec 真能命中；否则「零 diff」与「路径写错」不可区分。

---

## 5. 两个 pre-existing 红点的**独立归因**结论

### 5.1 mcp032 的 `-f` 花括号崩溃：**早于本批**（结论：不是本批引入）

1. **hunk 覆盖**：本批对 mcp032 的 `git diff -U0 28432f859f..HEAD` 共 10 个 hunk（起点 `-41/-44/-63/-69/-74/-191/-194/-292/-300/-515`），**没有一个**覆盖基线行 287..291；我那 6 处 `{` 所在的基线行是 288。
2. **逐字符等价**：基线 L285..291 与 HEAD L346..352 逐行 `-ceq` 全为 `True`（本批在该点之前净增 61 行，位移一致）。
3. **溯源**：`git blame` 与 `git log -S "hand-built {'Material','material'} JSON"` 都指向 **`54200f0d77`（2026-09-26 10:18:48 +0800）**，远早于本批（2026-09-29 10:18:40 起）。
4. **数量自算**：我自己扫「`-f` + 含 `{` 的字符串字面量」并用 12 个参数求值（排除占位符参数不足的假阳性）：**基线 6 个、HEAD 6 个，位置一一对应**（HEAD L349/475/480/490/494/498 ↔ 基线 L288/410/415/425/429/433）；mcp029 两个版本均为 **0 个**。
5. **实测**：未改动原件直接运行 ⇒ 第 348 行 `FormatError`、exit 1（此时引擎尚未启动，OutRoot 已在 L292 创建）；只有把 6 处 `{` 双写（diff 恰好 6 行）后才能跑出 39 checks / 2 failed。
⇒ **判为 pre-existing；不是 fail 项。**

### 5.2 mcp029 的两处内容级红（+ mcp032 的 D6 两处红）：**不是本批引入**

实测（我自己跑出来的原文）：

```
[FAIL] wire_clear_default_is_false
       live inputSchema.properties.clear.default = true (type Boolean)
[FAIL] wire_description_names_shared_file
       live description = 获取测试结果报告
[FAIL] d6_live_description_keeps_the_old_wording   live description starts with the pre-override wording + space: False
[FAIL] d6_live_description_declares_the_shape      live description = '获取运行中游戏指定节点的属性'
[PASS] old_fixture_readable        frozen fixture get_game_node_properties.description = '获取运行中游戏指定节点的属性'
[PASS] wire_clear_description_kept
[PASS] d6_contract_agrees_with_the_wire            contract description == live description = True
```

独立判据（每条都是我自产的证据）：

1. **本批没有可影响线上 wire 的改动**：`git diff --name-status 28432f859f..HEAD` = 3 个 `M`（文档 + 两个取证脚本），无任何 `modules/mcp_server/src`/头文件/契约；引擎二进制 `godot.windows.editor.x86_64.mono.console.exe` 的 `LastWriteTime` = **2026-09-29 08:31:03**，早于本批首提交 **10:18:40**，`--version` = `4.8.dev.mono.custom_build.035edfce7`（= 门锚点）。⇒ 同一二进制 + 未改的契约 ⇒ 线上 `tools/list` 逐字节只能与改前一致。
2. **4 条判据表达式未被本批修改**：`wire_clear_default_is_false`、`wire_description_names_shared_file`、`d6_live_description_keeps_the_old_wording`、`d6_live_description_declares_the_shape`（外加上文提到的 `wire_clear_description_kept`）在本批 diff 中出现 **0 次**。
3. **输入字节等价**：引擎内基准 `docs/rename-baseline-tools-list.json` 与本批无关的 blob `543b49b2…`（48749 B / sha256 `8f8051c4…`）逐字节相同 ⇒ 换源不改变任何被比较字段。
4. **红点成因是工件/二进制而非脚本**：冻结契约（blob 在本批前后都是 `3b1b191d…`）自身的 `editor_get_test_report.description` = `'获取测试结果报告'`（8 字符）、`running_game_get_node_properties.description` = `'获取运行中游戏指定节点的属性'`（14 字符），而线上与契约一致（`d6_contract_agrees_with_the_wire` PASS）；契约里 `clear.default` = `false`，但**线上**为 `true`。`git log -S '/root/Main/Actor' | -S 'user://mcp_test_report.json' | -S 'clear:true'`（工程内所有可达提交）均为 **0 个提交** ⇒ 该 shape/描述文本从未进入过契约。
5. **本批对这两个脚本的净效果是变好而非变红**：`old_fixture_readable` 与 `d6_old_wording_readable` 由改前的恒 FAIL（hof-rs 现文件已是 177 条、不含这两个工具）变为 **PASS**，`wire_clear_description_kept` 由「与空串比较」变为 **PASS**。红点数量由 4（旧 mcp029 的推断情形）收敛到 2，且剩下的 2 条与去跨仓无关。

**归因结论：两处 pre-existing 红点都不是本批引入；按任务书门槛不构成 `fail`。** 诚实边界：我没有运行旧版本（硬约束禁止其枚举 9877），所以「改前红集合」一节是**由 1+2+3+4 推出的结论**（结构上是充分的：产物侧零变化 + 输入侧零变化 + 判据侧零变化），不是旧版实跑。

---

## 6. 未验证项与理由

见 §1.1 `unverified` 四项：旧版本未实跑（硬约束）、未重建引擎（本批无编译输入变更、超出范围）、未复现任务书 §1 的全量「可执行跨仓引用扫描 = 0」（只验证了两个脚本不在门命令列表中 + mcp032 不再 dot-source 端口模块）、未逐细节复核 §2.4 探针仓库的反例（本批未做 §2.4，g09 判据本身已由我自跑）。

## 7. 我没有独立复核的部分

- **§2.4 的“不做”理由本身**：我复核了「现行 g09 判据 = `ANCHOR_STRUCTURAL_EQUIVALENT|EQUAL` 且 `RED_COUNT=0`」这一事实与门输出，但没有重新论证「护栏 3 无法在不削弱判据的前提下机器化」这一设计判断（D232 已裁决，且本项不影响验收）。
- **实现者报告引用的中间产物**：`recovery/work/task154/` 下的 `equivalence_check.ps1`、`guardrails_probe2.ps1` 等脚本的输出我**没有逐条重放**——我只用了它们被引用的事实（逐字节等价、护栏 3 探针），而任务书要求的九项我全部另建了自产证据。
- **hof-rs 侧历史**：`db2eed7` 之前的夹具内容我只经 `git cat-file` 的 blob 读取（`543b49b2…`），没有复核 hof-rs 侧那次迁移的动机与范围。

## 8. 给下一批的建议（我不改代码）

1. **TASK-155 的第一件事**：把 mcp032 的 6 处 `-f` 字面量的 `{` 双写（禁止改写证据文本措辞），使该脚本能端到端运行；这是它「不可运行」的唯一阻塞，与端口/跨仓无关。建议同时把 6 处**逐个**跑一次红→绿的过程留证。
2. **TASK-155 的第二件事（定性优先）**：mcp029 的 `clear.default=true` 与 8 字符描述说明**线上二进制/契约生成物没有携带 TASK-029 的 `SCHEMA_OVERRIDES`/`DESCRIPTION_OVERRIDES`**（而契约文件里 `clear.default` 已是 `false`、描述仍短）——先判定这是「174→177 迁移时丢了 override」还是「期望过期」，再决定改实现或改断言；**禁止**为变绿放宽断言（D233 第 2 条）。D6 的 shape 文本同理（契约从未携带）。
3. **复核纪律固化**：把「凡用 pathspec / 转义求『未变更』证据，必须先证明 pathspec 命中」写成 HANDOVER 的一行硬纪律（本轮两个陷阱已各有一份可复现的最小例子，可直接引用本报告 §4 的表）。
4. **g09 护栏 3**：若将来要机器化，必须引入跨仓视角（外层仓的 runner），且不能自指；在现有仓库结构下「冻结 + 人工核验」是最强形式，建议维持，但把本轮 §1.1 G09.HUMAN_GUARDRAIL 的三法证据模板写进验收任务书模板。
5. **文档措辞**：任务书模板里避免「转义是否仍在注释行内」这类与可实现形态冲突的表述（见 DEF-1）；实现者报告的统计口径（如「30+ 个脚本点源」）建议以可复算的判定语句为准（见 DEF-2）。

---

### 附：本报告使用的自产证据文件

`recovery/work/task154-acc/`：`c2_refusal_guard.ps1`/`.out.txt`、`c2logs/*`、`c3_c7_checks.ps1`/`.out.txt`、`c4_gates.out.txt`、`c4_g08_baseline.txt`、`c4_g08_head.txt`、`c4_g08_base_rows.txt`、`c4_g08_head_rows.txt`、`c5_static.ps1`/`.out.txt`、`c5_live.ps1`/`.out.txt`、`c5_live_029.out.txt`、`c5_live_032probe.out.txt`、`c6_traps.ps1`/`.out.txt`、`c6trap/*`、`c8_c9_checks.ps1`/`.out.txt`、`c1_removed_lines.txt`、`grep_hofrs.txt`、`grep_9877.txt`、`live-029/`、`live-032-probe/`、`live-032-original/`。
（门输出：`F:\moonbit-hof-rs\godot-mcp\runs\gates\task154_acc\`。）
