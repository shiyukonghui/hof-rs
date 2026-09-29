# TASK-DR64-ACCEPTANCE — E1 根因离线诊断的独立验收

- 任务书：`.spec/hof-rs/tasks/TASK-DR64-ACCEPT.md`（本报告的判据来源）；被诊断对象：`.spec/hof-rs/tasks/TASK-DR64.md` / `TASK-DR64-REPORT.md`。
- 判据口径：`REQUIREMENTS.md:112`（E1）、`DECISIONS.md` **D243**（E1 现状与未解之因）、**D257**（队列重排）。
- 性质：**独立验收、离线、只读**。我没有上游对话上下文，下列每一条证据都是**我自己跑出来/读出来的**；实现者报告只当线索。
- 我的落点：`F:\moonbit-hof-rs`（外层仓）。我开工/收工时的 HEAD（两者相同）：`5c83a5f67dde2500974cdcff26cdf881eedd377f`。
- 未启动 Godot、未碰端口、未联网、未调模型端点、未跑 `cargo`、未重跑真机、未 commit、未 push、未 stage、未修改任何既有文件。
- 仓外临时物：`C:\Users\wyl\AppData\Local\Temp\dr64acc`（我的 Python/pwsh 脚本 + 工作区拷贝 ws0/ws1/ws2），取证完成后**已删除**（§9）。本报告是本次唯一新增文件。

---

## 1. 结构化结论

```json
{
  "verdict": "pass",
  "criteria": [
    {
      "id": "MEASUREMENT_REACHES_ENGINEERING_WRITES",
      "pass": true,
      "evidence": "我按 src/runtime/policy.rs:68-97 独立重实现 hash_tree（Python，未照抄），排除集 {.hoh,.git,.godot,.import}：对 .workspace/mario、runs/smoke-t7/iter-1/candidate、runs/smoke-t7/versions/fc78d299… 三棵树各得 17 文件 / digest=fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c。仓外拷贝对照：ws0（未改）= fc78d299…；ws1（新增 scripts/hoh_probe.gd，5 B）= d7241bae56a1569cfee09413ce99f2717d2bd69e3cd3c0f312e8f47b689e754d（≠A_0）；ws2（新增 .hoh/scratch/probe.txt）= fc78d299…（不变）。排除集来源：src/runtime/policy.rs:38-47 + src/adapter/godot.rs:3354-3357 + config/hoh.yaml:47。HOH_SCRATCH_DIR=<view>/.hoh/scratch（src/runtime/invoke.rs:44），落在 .hoh 前缀内，被 is_excluded（policy.rs:51-55）排除。"
    },
    {
      "id": "LIMIT_ATTRIBUTION",
      "pass": true,
      "evidence": "上限 = step_limit（config/hoh.yaml:14 = 150）→ src/harness/mini.rs:67 → mini rust/src/agent.rs:161-165 第一支（n_calls >= step_limit → FlowInterrupt::limits_exceeded）。实测：traj info.config.agent.step_limit=150、info.model_stats.api_calls=150、result.json.usage[planner/developer/tester].calls 全 150、attempts[*].exit_status=LimitsExceeded（documents: runs/smoke-t7/iter-1/result.json:13-135）。墙钟：developer duration_ms=3095229（3095.2 s）< 3600（config/hoh.yaml:18），剩余 505 s；墙钟支是 agent.rs:167-171 的 time_exceeded，其 exit_status 字符串是 TimeExceeded（mini rust/src/lib.rs:204-221），未出现。成本支被结构禁用（agent.rs:163 要求 cost_limit>0.0；config/hoh.yaml:17 = 0.0）。"
    },
    {
      "id": "NO_PROGRESS_IS_DESCRIPTION",
      "pass": true,
      "evidence": "唯一发射点 run_loop.rs:797-807（h_dev_after==h_dev_before → ContractViolation::NoProgress.code() → 仅 iter_warnings.push + append_warning）；全仓 NoProgress 仅 model.rs:345（枚举）/ :356（\"no_progress\"）/ run_loop.rs:799（唯一使用者）；model.rs:344 注释即 \"Warning only\"。原始记录：runs/smoke-t7/warnings.log 第 2 行 \"iteration 1: no_progress (the developer stage produced no change)\"；result.json:2-10 ok=true、failed_role=null、reason=\"ok\"、warnings 含 no_progress；runs/smoke-t7/exit_code=0、meta.json.exit_code=0。⇒ 它是\"Developer 未改动被哈希文件\"这一事实的**描述标签**，不是因；它也不是 LimitsExceeded 的果（planner/tester 同为 LimitsExceeded 却各有合法工件，result.json.attempts[0]/[2].artifact_valid=true）。"
    },
    {
      "id": "FALSE_GREEN_CLAIM",
      "pass": true,
      "evidence": "同一份 result.json 同时是：ok=true（:2）、failed_role=null（:3）、artifact_gate.launchable=true（:137-141）、candidate_id=version_id=fc78d299…（:11-12，= A_0，我独立复算确认），而 Developer 零工程增量。REQUIREMENTS.md:112 的 E1 含 \"Developer 产出 Godot 工程增量\" 这一分句 ⇒ 该轮 E1 未 met。全仓无任何布尔字段把\"零增量\"变红（NoProgress 只是 warnings 字符串）⇒ 只以 ok/退出码/launchable 为判据的自动化会**漏报 E1 失败**。指控成立。"
    },
    {
      "id": "TEST_LEVEL_FALSE_GREEN",
      "pass": true,
      "evidence": "tests/artifact_hygiene.rs:112-115 只做 prompt.contains(\"$HOH_SCRATCH_DIR\")（+ :116-119 的 tmp_/.bak 包含断言）；tests/developer_contract.rs:57-74 只对 godot-dev.md 做一组 needle 的 contains 断言（含 \"$HOH_HOH_BIN tools call\"）。两者都不执行命令、不触碰真实 shell ⇒ 对\"提示词语法在角色真实 shell（mini rust/src/environments/local.rs:66-76 在 Windows 用 cmd /C raw_arg）里是否可执行\"**结构性盲**，只要字符串还在就永远绿。判断：与 E1 的失败**无因果贡献**，是检测缺口（相关，非因）；报告也没有把它写成因。"
    },
    {
      "id": "REPAIRS_AND_TESTS_ACTIONABLE",
      "pass": true,
      "evidence": "修法 1（提示词/工具索引/证据剧本按平台渲染，或把角色 shell 改 POSIX，并加契约测试）与修法 2（DoD 降噪 + 把\"先产生工程写入\"变成显式违约码/门）都落到具体文件行，各自列了风险与回退点（git revert；不动引擎树）。§5(a) 的 API 我逐一核实存在且 public：snapshot.rs:77 snapshot_role（返回 VersionEntry.version_id=?详见 :92-101）、policy.rs:121 tree_manifest、policy.rs:149 diff_manifests（返回 EvidenceDiff.added/modified/removed）、snapshot.rs:56 VersionStore::new；§5(b) 所需 mini_swe_agent::LocalEnvironment / LocalEnvironmentConfig 由 mini rust/src/environments/mod.rs:7 pub use、lib.rs:25 导出，role_env 在 src/runtime/invoke.rs:28。⇒ 不空洞，可执行。缺陷见 DEF-3/DEF-7（引用错误与测试设计的排除集来源未绑死）。"
    },
    {
      "id": "GUARDS",
      "pass": true,
      "evidence": "我用历史同一口径（pwsh 递归 -Force -File，仓根相对路径小写、\\→/、TAB 三列、LF、无尾随换行、Sort-Object 文化排序、UTF-8 后 SHA256）复算：runs/smoke-t6 files=135 digest=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03（与 DR-54/57/59/61/62 逐字一致）、runs 全域 files=5147 digest=01ff775e36935d3d92dab6919fe030389a8ff53483c52e87288ad711ec840dc3（同历史）、runs/smoke-t7 files=115、runs 最新 mtime=2026-09-29 14:44:16、.workspace/mario files=259 digest=4e494547416b2e87ba025d686afef9447d4f92c027917d1790e6fc9deaeaa84a（同 DR-59/61/62）。PRD sha256=4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a、mtime 2026-09-20 23:21:21。引擎树用嵌套仓：toplevel=F:/moonbit-hof-rs/godot-mcp/godot、HEAD=fc63af77c33368c4a1bb839c95d19750554f63a3、status --porcelain=0（含 -uall=0）、ls-files=15049、modules/mcp_server=721；外层 git ls-files godot-mcp=6484、git ls-files godot-mcp/godot=0、git check-ignore -v → .gitignore:33:godot-mcp/godot/。仓内 git status --porcelain -uall=2（= TASK-DR64-REPORT.md + TASK-DR64-ACCEPT.md 两个未跟踪 spec 文件）。/tmp/dr64 与 C:/Users/wyl/AppData/Local/Temp/dr64 均不存在（自报删除属实）。三个假绿陷阱逐个实测（§8）。"
    },
    {
      "id": "HONESTY",
      "pass": true,
      "evidence": "报告 §7 把\"实测/推断\"分栏并逐条标注，未见编造输出或日期：其自报 digest 口径（\"<relpath>\\0<size>\\0<sha256>\" 排序后取 SHA256）我用 Python 复现得 smoke-t6=6bfc3e62d8abe1213d3de1535cf469148281c68f8f6884d273ac697452f97334、smoke-t7=e741d61d2cca78b54adb4896b04b9537ff3abc3da8118c89772c903cc9a33337，与报告逐字一致；其 $HOH_HOH_BIN 引用数（developer 9 / planner 2 / tester 4、planner %HOH_HOH_BIN% 1）我按\"命令文本内出现次数\"复现**完全一致**；shell 错误计数 10/4/3 与 quote-EOF 首现步 67、115/150 显式 bash -c、首个失败族步点均复现。但它有一处**实测标注不成立**（DEF-1：第 38 步那个\"成功的 hoh tools call\"其实是 hof CLI 的 config 报错；首个真实工具结果在第 46 步）与若干数字/引用瑕疵（DEF-2..DEF-6、DEF-8）。这些都**不改变结论**，且 DEF-1 的方向是**低估了它自己的证据**。"
    }
  ],
  "defects": [
    {
      "id": "DEF-1",
      "severity": "minor",
      "what": "TASK-DR64-REPORT.md:209/265 把\"第一个成功的 `hoh tools call` 在第 38 步\"列为实测（判据 rc==0 且输出非空），据此量化\"25.3% (38/150) 预算在第一次成功前烧掉\"。但第 38 步的输出是 hof CLI 自身的错误 \"hoh: could not find config file for config/hoh.yaml\"，不是 MCP 工具结果；首个**真实工具结果**出现在第 46 步（输出以 {\"content\":[{\"text\":\"{\\\"available\\\":true,... 开头）。正确量化应为 46/150 = 30.7%。",
      "reproduction": "python 解析 runs/smoke-t7/iter-1/traj/developer.attempt1.json，按 assistant-with-tool_calls 编号：step 38 命令 `bash -lc 'mkdir -p \"$HOH_SCRATCH_DIR/args\"; ... \"$HOH_HOH_BIN\" tools call editor_get_errors ...'` → `<returncode>0</returncode>\\n<output>\\nhoh: could not find config file for config/hoh.yaml`；step 46 输出 `{\"content\":[{\"text\":\"{\\\"available\\\":true,\\\"count\\\":1,...`。"
    },
    {
      "id": "DEF-2",
      "severity": "minor",
      "what": "TASK-DR64-REPORT.md:162 的表 B 把 `project_set_setting` 计为 1，与其 §Q4-C 自己写的\"含 project_set_setting ×2\"矛盾（也不符原始数据）。",
      "reproduction": "对 185 条命令正则 `tools\\s+call\\s+(\\w+)` 计数：project_set_setting=2（同一 commanding message step 144 内两次调用，见 messages[325] 命令文本）。"
    },
    {
      "id": "DEF-3",
      "severity": "minor",
      "what": "TASK-DR64-REPORT.md:315 §5(a) 引 `policy.rs:3348-3358` 作为 cache_excludes 的\"自写警告\"；`src/runtime/policy.rs` 全长只有 452 行，该引用不可能命中。真实位置是 `src/adapter/godot.rs:3345-3358`（DR-11 注释 + cache_excludes）。",
      "reproduction": "wc -l src/runtime/policy.rs → 452；sed -n '3345,3360p' src/adapter/godot.rs → 命中 DR-11 警告与 fn cache_excludes。"
    },
    {
      "id": "DEF-4",
      "severity": "info",
      "what": "TASK-DR64-REPORT.md:22 说\"三个角色的 150 条 assistant 消息全部 content 为空\"；\"150\"只对 developer 成立。planner 有 131 条 assistant（149 次调用）、tester 137 条（182 次调用），150 是 api_calls。\"content 全空、无 reasoning_content\"这一实质结论为真。",
      "reproduction": "统计三份 traj：planner assistant=131/with_tool_calls=131/nonempty_content=0；developer=150/150/0；tester=137/137/0；info.model_stats.api_calls 三者皆 150。"
    },
    {
      "id": "DEF-5",
      "severity": "info",
      "what": "TASK-DR64-REPORT.md:233 引用 messages[10] 的隐藏环境变量写作 `=F:=F:\\moonbit-hof-rs\\.workspace\\mario`；原始记录里该行是 `!F:=F:\\moonbit-hof-rs\\.workspace\\mario`（首字符为 `!`，非 `=`）。cwd 证据本身成立。",
      "reproduction": "python: messages[10].content 中 needle '!F:=F:\\\\moonbit-hof-rs' 命中、'=F:=F:\\\\moonbit-hof-rs' 不命中。"
    },
    {
      "id": "DEF-6",
      "severity": "minor",
      "what": "TASK-DR64-REPORT.md:332-341 为 `runs/**` 自证另立 digest 口径（`<relpath>\\0<size>\\0<sha256>` 行 + 排序 + SHA256），值 6bfc3e62…（t6）/ e741d61d…（t7）。该口径我可复现，但**不是**本仓历史基线口径（c144ef32…7a9c03 / runs 全域 01ff775e…40dc3），因此它的\"期间未动\"证明无法与 DR-54/57/59/61/62 记录交叉核对。验收任务书要求\"自证 runs/smoke-t6 = c144ef32…\"，报告未做；由我补齐（§8.4）。",
      "reproduction": "我用的规范口径（pwsh digest2.ps1，见 §8.4）复算 c144ef32…；报告口径用 Python 复现 6bfc3e62…，两者都真实，但口径不同不可比。"
    },
    {
      "id": "DEF-7",
      "severity": "minor",
      "what": "TASK-DR64-REPORT.md:310-316 提议的 tests/e1_reachability.rs 未说明 `excludes` 从哪来。若测试自带 ['.hoh','.git','.godot','.import'] 字面量，则它自报的\"把 scripts 塞进 GodotConfig::cache_excludes 即变红\"这种方法论植入**不会**让该测试变红（测试根本没读配置）⇒ 该测试只能钉住 hash_tree 的内部逻辑，钉不住\"运行时实际使用的排除集没有被配歪\"。",
      "reproduction": "读 src/runtime/run_loop.rs:358 `HashExcludes::new(orchestrator.adapter.cache_excludes()).merged()` 与 config/hoh.yaml:47 即可看出排除集是配置驱动；测试若不读同一配置则不覆盖该接缝。"
    },
    {
      "id": "DEF-8",
      "severity": "info",
      "what": "TASK-DR64-REPORT.md:183 把 mtime 普查窗口起点的依据写成\"轨迹文件 mtime 13:40\"；developer.attempt1.json 的 mtime 是 14:32，13:40 是 planner.attempt1.json 的 mtime，而 developer 的会话起点实际是 13:36:06（首条 assistant 时间戳）。窗口起点晚于会话起点 4 分钟。",
      "reproduction": "ls -la traj → planner 13:40 / developer 14:32 / tester 14:41；python datetime.fromtimestamp(1790660166) → 2026-09-29 13:36:06。**但**我另跑更宽窗口 find .workspace/mario（排除 .hoh）mtime∈[13:30,13:41) → 0 个文件、mtime≥2026-09-29 00:00 的非 .hoh 文件只有 4 个 .godot 文件 + 13:21 的 project.godot ⇒ 窗口选择**没有**掩盖任何工程写入，结论不受影响。"
    }
  ],
  "risks": [
    "报告的头号\"主因排序（shell 契约 > 预算 > DoD）\"自评为推断（≈0.6）；我未能分离三个约束（离线且禁止真机重跑）。若只修 shell 通道，下一轮真机仍可能 A_1==A_0。",
    "\"编辑器侧异步落盘是否会被 no_progress 窗口漏掉\"仍是未测项（报告 §7-4 自陈），本轮因没有任何工程写入成功而既未证实也未证伪。",
    "修法 1(a) 使提示词成为平台相关产物；修法 2(b) 引入新违约码会改 result.json schema 与既有测试期望。两者都需要专项回归，不能与判定 E1 的真机轮混在一起。",
    "§5(b) 契约测试会起真实 shell；在非 Windows 平台上它天然是绿的，\"先红\"只在 Windows 成立，需显式平台门控，否则会被误当成\"已修\"。"
  ],
  "unverified": [
    "修复后真机一轮是否真能得到 A_1 != A_0（需要真机，本轮禁止；这是唯一能关闭问题的证据）。",
    "三个约束（shell 错配 / 步数预算 / DoD 指向当时不可通过的电池）的因果权重与排序。",
    "project_set_setting 那次写入究竟被哪一层吞掉（cmd 引号解析 / hoh CLI / 引擎拒绝）。",
    "planner/tester 是否也被同一 shell 错配以同粒度吃掉预算（只做了字符串计数与终态核对）。",
    "smoke-t7 当时二进制里 input_channel_probe / node_and_collision_assertions 两个电池步的根因（该项依赖 TASK-SMOKE-T7-REPORT 与已修代码的对照，我只核实了\"HEAD 上已被 DR-58 修好\"与 battery_passes[0] 的两项 false）。",
    "我没有执行 Rust 的 hash_tree 本身（本批不跑 cargo）；我的 Python 重实现逐字复现了运行时 digest，但不等同于执行生产代码路径。"
  ]
}
```

**总判：`verdict = pass`（8/8 criteria，无 blocker；1 minor+若干 info 的缺陷不改变结论）。**
一句话：**E1 的判据可达（加 1 个 5 字节工程文件即改变摘要），那一轮 `A_1 == A_0` 是真实的零增量而非测量缺陷；上限归因正确（step_limit=150 用满、墙钟 3095.2/3600 s 未达、TimeExceeded 是另一中断种类）；`no_progress` 是描述标签而非因；两级假绿指控成立；两条修法与两个测试可执行、不空洞；禁区全部守住。**

---

## 2. 逐项核对表

| # | 核对项（任务书） | 结论 | 我的证据 |
|---|---|---|---|
| 1 | 头号命题：测量能否看见 Developer 的工程写入 | **pass（可达）** | §3 对照实验：A_0=fc78d299…（三棵树），+scripts/hoh_probe.gd(5 B) ⇒ d7241bae… ≠ A_0 |
| 1b | 排除集是否 = {.hoh,.git,.godot,.import}；HOH_SCRATCH_DIR 是否在内 | **pass** | policy.rs:38-47 / godot.rs:3354-3357 / config/hoh.yaml:47；invoke.rs:44 `.hoh/scratch`，被 policy.rs:51-55 前缀命中 |
| 2 | LimitsExceeded 归因 step_limit=150，非墙钟；墙钟走另一中断种类 | **pass** | config/hoh.yaml:14/17/18；traj step_limit=150/api_calls=150；agent.rs:161-171；lib.rs:204-221；result.json durations 3095229 < 3600000 |
| 3 | no_progress 只是 warning；ok=true/failed_role=null/exit_code=0；判定因/果/描述 | **pass（描述）** | run_loop.rs:797-807；model.rs:344-345/356；warnings.log:2；result.json:2-3,6-10；meta.json.exit_code=0 |
| 4 | 自动化假绿：ok=true + 退出码 0 而 E1 not_met | **pass（成立）** | result.json ok/launchable/candidate_id，配合 A_1==A_0 与我复算 |
| 5 | 测试级假绿（两处只做包含断言）；与 E1 是否因果 | **pass（定义盲）；因果=无，仅检测缺口** | artifact_hygiene.rs:112-115；developer_contract.rs:57-74 |
| 6 | 两条修法可执行/最小/风险已列；两个最小测试能否钉死（先红后绿） | **pass，含 2 处需补强** | APIs 全部存在（snapshot.rs:56/77、policy.rs:121/149、mini mod.rs:7）；DEF-3/DEF-7 |
| 7 | 禁区：runs/** 未动（含口径自证）、PRD sha、引擎树用嵌套仓、6484/0、临时物 | **pass** | §8.4/§8.5；规范摘要 c144ef32…/01ff775e…；嵌套 HEAD fc63af77、status 0、ls-files 15049；外层 6484/0；.gitignore:33 |
| 7b | 三个假绿陷阱各实测（含 cmd 的 `^`） | **pass** | §8.6：git diff 空 pathspec exit 0；bash `HEAD^`=bdf654b1… vs cmd 得 fc63af77…；`echo A^B`=AB |
| 8 | 诚实性：实测/推断标注 | **pass，含 DEF-1** | §8.7；报告 §7 分栏属实；DEF-1 是该报告唯一\"实测标注不成立\"处，且方向为低估自身证据 |

---

## 3. 我自己的对照实验（加文件 ⇒ 摘要变）

**重实现**（仓外 `C:\Users\wyl\AppData\Local\Temp\dr64acc\hash_tree.py`，按 `policy.rs:68-97`：WalkDir 枚举普通文件、跳过排除前缀、按 relpath **UTF-8 字节序**排序、对每条喂 `relpath\n{len}\n{bytes}\n`、sha256 hex；不跟随符号链接）：

```
$ python hash_tree.py .workspace/mario runs/smoke-t7/iter-1/candidate \
    runs/smoke-t7/versions/fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c
.workspace/mario
  files: 17  digest: fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c
    project.godot
    scenes/main.tscn
    scripts/README.md
    scripts/{brick,coin,enemy,goal,main,player,question_block}.gd 及各自 .gd.uid
runs/smoke-t7/iter-1/candidate
  files: 17  digest: fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c
runs/smoke-t7/versions/fc78d299…
  files: 17  digest: fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c
```

**对照实验**（工作区**复制到仓外**，绝不碰真工作区）：

```
$ cp -a .workspace/mario /tmp/dr64acc/ws0 ; cp -a ... ws1 ; cp -a ... ws2
$ printf 'pass\n' > /tmp/dr64acc/ws1/scripts/hoh_probe.gd      # 新工程文件，5 字节
$ mkdir -p /tmp/dr64acc/ws2/.hoh/scratch ; printf 'pass\n' > /tmp/dr64acc/ws2/.hoh/scratch/probe.txt
$ stat -c '%s %n' /tmp/dr64acc/ws1/scripts/hoh_probe.gd
5 /tmp/dr64acc/ws1/scripts/hoh_probe.gd
$ python hash_tree.py /tmp/dr64acc/ws0 /tmp/dr64acc/ws1 /tmp/dr64acc/ws2
  files: 17  digest: fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c
  files: 18  digest: d7241bae56a1569cfee09413ce99f2717d2bd69e3cd3c0f312e8f47b689e754d
  files: 17  digest: fc78d299e6dcc9711d5d38c6d04191e586def586d9d0daec70358f3353579d3c
```

**读法**：ws0（未改）= A_0；ws1（+1 个工程文件）**≠** A_0 ⇒ 判据可达；ws2（+1 个 `.hoh/**` 文件）**=** A_0 ⇒ 被排除的只有运行时/缓存路径。
（报告用的 8 字节探针得到 `c541c5bb…`；我用 5 字节，摘要不同是内容不同所致，判据同一条：**加工程文件必变**。）

---

## 4. 对\"测量可达\"的独立判定

**可达。** 依据：

1. 我复算的 A_0 与运行时记录逐字一致（`result.json.candidate_id`、`versions/index.json` 目录名、`run_loop.rs:421` 的 A_0 取点）。
2. 被哈希的 17 个文件**就是** Developer 的合法靶子（`project.godot` / `scenes/main.tscn` / `scripts/**`），其中没有一个在排除集里。
3. 对照实验对 **1 个文件 / 5 字节**即敏感。
4. 该轮相等是**真实的零增量**，不是测量缺陷：我独立 mtime 普查（不依赖轨迹）显示 Developer 窗口内 `.hoh` 之外被改动的 4 个文件全在 `.godot/**`（被排除），`.hoh/scratch` 22 个（被排除），工程文件 0 个；`.workspace/mario` 与 `runs/smoke-t7/iter-1/candidate`、存储版本三棵树字节同摘要。
5. 轨迹侧的 cwd 证据也指向同一目录（messages[10] env dump 含 `F:\moonbit-hof-rs\.workspace\mario`；cmd 专有变量 `!F:=…`）⇒ 测量目标 = 写入目标，不存在\"哈希另一棵树\"的错位。

> 附加限制（如实）：我没有执行 Rust 的 `hash_tree`（本批不跑 cargo）；但我的重实现与运行时 digest **逐字相同**且算法逐行对照过 `policy.rs:68-97`，这比\"两套独立实现互证\"更强，仍不等同于执行生产代码路径。

---

## 5. 对\"自动化假绿\"的独立判定

**成立，且是本批最关键的结论。**

同一份 `runs/smoke-t7/iter-1/result.json` 里同时存在：

- `"ok": true`（:2）、`"failed_role": null`（:3）、`"reason": "ok"`（:4）；
- `"artifact_gate": { "launchable": true }`（:137-141）；
- `"candidate_id" == "version_id" == fc78d299…`（:11-12）= 我复算的 A_0；
- `"warnings": [..., "no_progress"]`（:6-10）——唯一反映零增量的痕迹；
- `runs/smoke-t7/exit_code` = `0`、`meta.json.exit_code` = `0`。

而 `REQUIREMENTS.md:112` 的 E1 明确含\"Developer 产出 Godot 工程增量\"。⇒ **一条 ok=true/exit 0/launchable=true 的轮次可以完全不满足 E1**，且没有任何布尔字段会变红。因此\"仅看 ok/退出码会漏报 E1 失败\"的指控**成立**。

必须说清的两点限定（避免把正确结论读过头）：
1. `ok` 的语义在代码里是\"流水线跑完\"（run_loop.rs:1259-1268 的 `ok: true` 是成功路径硬编码），不是\"E1 met\"；报告没有把它写成 E1 的判据。
2. 检测零增量所需的数据**已经存在**（`no_progress` 字符串 + A_0/A_1 两个 hash），缺的是**把它变成判据的信号**。因此这是\"自动化判据设计缺陷\"，不是\"证据缺失\"。

---

## 6. 对\"测试级假绿\"的独立判定

- `tests/artifact_hygiene.rs:112-115`：`assert!(prompt.contains("$HOH_SCRATCH_DIR"), …)`（另有 `tmp_`/`.bak` 包含断言）。纯字符串包含。
- `tests/developer_contract.rs:57-74`：对 `godot-dev.md` 做一组 `needle` 的 `contains`（含 `"$HOH_HOH_BIN tools call"`、`--args-file`、各工具名）。纯字符串包含。
- 两者都**不执行命令、不实例化真实 shell**；而角色真实 shell 在 Windows 上是 `cmd /C`（mini `rust/src/environments/local.rs:66-76`），提示词/技能/工具索引/证据剧本给的是 `$HOH_…`（`developer.md:23`、`prompts/mod.rs:32/44/60`、`tools/index.rs:152`、`adapter/godot.rs:3497-3520`）⇒ 只要那些字面量还在文本里，测试**永远绿**，无论语法在真实 shell 里是否可跑。
- **因果判定**：与 E1 失败**无因果贡献**——失败的行为是\"提示词契约与真实 shell 不匹配\"，这两条测试只是**看不见**它（检测缺口/相关）。报告把它称为\"测试级假绿\"并在 §5(b) 给出修复方向，措辞未越界。

---

## 7. 对修法与两个最小测试的判定

**整体可执行、非空洞**，但有两处需补强（DEF-3/DEF-7）：

| 项 | 判定 | 我的依据 / 补强建议 |
|---|---|---|
| 修法 1（平台化提示词 / POSIX shell / 契约测试） | 可执行、最小、风险与回退点已列 | 真实错配点我逐条核实：`developer.md:23`、`mod.rs:32/44/60`、`index.rs:152` ↔ `local.rs:66-76`；三份 traj 的命令计数复现（developer `$HOH_HOH_BIN` 9 次、planner 2 + `%…%` 1、tester 4）。**建议**：提示词渲染收口到单一函数，避免跨平台采样分叉；回退就是 revert。 |
| 修法 2（DoD 降噪 + 预算结构化 + 显式违约码） | 可执行；风险（schema/既有测试、慢角色误伤）已列 | 该修法同时治 §5 的自动化假绿，方向正确。**建议**：新增的是\"可机读信号\"（布尔字段或独立违约码），别继续只用 warning 字符串。 |
| §5(a) `e1_reachability.rs` | **能钉住 hash_tree 逻辑，但设计未钉住\"运行时排除集来自配置\"这一接缝**（DEF-7） | API 全部存在：`VersionStore::new`（snapshot.rs:56）、`snapshot_role`（:77）、`tree_manifest`（policy.rs:121）、`diff_manifests`（policy.rs:149，返回 `EvidenceDiff.added`）；`HohConfig`/`GodotConfig` 在集成测试里已被 import（tests/common/mod.rs:10、tests/evidence_battery.rs:25）。**替代设计**：排除集不要写字面量，改为从运行时同一来源取（载入 `config/hoh.yaml` 的 `adapter.godot.cache_excludes` 或 `GodotConfig`），并**额外断言** `merged() == [".hoh",".git",".godot",".import"]`；这样\"把 scripts 塞进 cache_excludes\"的植入才真能把测试变红。 |
| §5(b) `role_shell_contract.rs` | **设计成立、先红可预期**，但需补两处细节 | `mini_swe_agent::{LocalEnvironment, LocalEnvironmentConfig}` 经 mini `environments/mod.rs:7` 与 `lib.rs:25` 公开导出，`role_env` 在 `invoke.rs:28`，测试可直接构造。**补强**：(i) 明确占位符替换规则（`<tool>` / `<path>` / 桩可执行文件的落点）与\"抽出的命令\"的抽取函数，避免测试自身漂移；(ii) 显式平台门控，并把期望的红色文本锚到真实记录（如 `messages[76]` 的 `'$HOH_HOH_BIN\" tools call …' is not recognized …`），否则非 Windows 上\"先红\"不成立、可能被误判为已修。 |

---

## 8. 禁区自查、陷阱实测与诚实性核查（全部为我的原始输出）

### 8.1 仓库状态 / 我改了什么

```
$ git rev-parse HEAD
5c83a5f67dde2500974cdcff26cdf881eedd377f
$ git status --porcelain -uall
?? .spec/hof-rs/tasks/TASK-DR64-ACCEPT.md
?? .spec/hof-rs/tasks/TASK-DR64-REPORT.md
$ git log --oneline -3
5c83a5f docs(spec): D257 - reorder the queue ...
e1fb58a docs(spec): D256 - DR-60 independently accepted (PASS 8/8) ...
836ad54 docs(spec): stage DR-65 ...
```

两个未跟踪项都是 spec 任务书/报告，**没有**临时物、**没有**源码/配置改动、**没有**新提交。我全程只读；本报告是唯一新增文件。

### 8.2 `.workspace/mario` 未被本批动过（用历史同一口径）

```
$ (pwsh digest2.ps1，口径见 §8.4)
.workspace/mario files=259 digest=4e494547416b2e87ba025d686afef9447d4f92c027917d1790e6fc9deaeaa84a
$ find .workspace/mario -type f -printf '%T+ %p\n' | sort -r | head -1
2026-09-29+14:32:28.7396764000 .workspace/mario/.godot/editor/editor_layout.cfg
```

`4e494547…` 与 DR-59/61/62 记录逐字一致 ⇒ 自那以后（含本诊断批）`.workspace/mario/**` 未变。

### 8.3 mtime 普查（独立于轨迹的\"零工程写入\"证据）

```
$ find .workspace/mario -path .workspace/mario/.hoh -prune -o -type f \
    -newermt '2026-09-29 13:40:00' ! -newermt '2026-09-29 14:33:00' -print
.workspace/mario/.godot/editor/editor_layout.cfg
.workspace/mario/.godot/editor/filesystem_cache10
.workspace/mario/.godot/editor/script_editor_cache.cfg
.workspace/mario/.godot/editor/shader_editor_cache.cfg        (count = 4)
$ find .workspace/mario/.hoh/scratch -type f -newermt '2026-09-29 13:40:00' ! -newermt '2026-09-29 14:33:00' | wc -l
22
$ find .workspace/mario -path .workspace/mario/.hoh -prune -o -type f \
    -newermt '2026-09-29 13:30:00' ! -newermt '2026-09-29 13:41:00' -print   # 覆盖会话真实起点 13:36:06
(空)
$ ls -la --time-style=full-iso .workspace/mario/project.godot
-rw-r--r-- 1700 2026-09-29 13:21:03.803296800 +0800 project.godot
$ sha256sum .workspace/mario/project.godot
e4855a18cf765e206c6aad87bfd499c76e5a9d4245b6ca88b00e3e68a91b4246
$ grep -c godot_mcp project.godot          -> 0
$ cmp .hoh/scratch/project.godot.pre_iter1 project.godot   -> IDENTICAL（备份 mtime 14:28:20）
$ ls .hoh/scratch/args/ | grep -E 'set_capture|set_trace'  -> （无命中）
```

⇒ 工程写入 0 个；`.hoh` 外被动的只有排除路径 `.godot/**`。报告的四条\"那次写入未落地\"测量我全部复现。

### 8.4 `runs/**` 未动 + 规范口径自证

口径（与 DR-54/57/59/61/62 同一算法）：递归 `-Force -File`；每文件 = **相对仓根**路径（`\`→`/`、转小写）+ 字节长度 + SHA256(小写 hex)，三列 `\t`、行间 `\n`、无尾随换行，行按 **PowerShell `Sort-Object`（文化敏感；本机 zh-CN）** 升序，整体 UTF-8 后 SHA256。

```
$ pwsh digest2.ps1 -Sub 'runs/smoke-t6'
runs/smoke-t6 files=135 digest=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03
$ pwsh digest2.ps1 -Sub 'runs'
runs files=5147 digest=01ff775e36935d3d92dab6919fe030389a8ff53483c52e87288ad711ec840dc3
$ pwsh digest2.ps1 -Sub 'runs/smoke-t7'
runs/smoke-t7 files=115 digest=6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7
$ newest under runs
F:\moonbit-hof-rs\runs\smoke-t7-experiment\e5_hash_tree.json 2026-09-29 14:44:16
```

- `c144ef32…7a9c03` 与 `01ff775e…40dc3` 分别与 DR-54/57/59/61/62 的 `smoke-t6` / `runs 全域` 记录**逐字一致** ⇒ 口径同源、期间未动（`runs` 最新 mtime 14:44:16 远早于本批）。
- `runs/smoke-t7 = 6e4c1595…`（历史未留存该规范值；实现者报告用的是它自己的口径）。
- **DEF-6**：报告的 `runs/**` 自证口径（`\0` 分隔 + 排序 + SHA256）与上述规范口径不同；我用 Python 复现其值 `t6=6bfc3e62…` / `t7=e741d61d…` 与报告逐字一致（口径自洽），但不能与历史基线交叉核对。**验收任务书要求的\"自证 c144ef32…\"由我补齐，且通过。**

### 8.5 PRD 与引擎树

```
$ sha256sum .spec/hof-rs/PRD-mario.md
4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a
   （mtime 2026-09-20 23:21:21，与 meta.json.spec.sha256 / D243 逐字一致）
$ git -C godot-mcp/godot rev-parse --show-toplevel   -> F:/moonbit-hof-rs/godot-mcp/godot
$ git -C godot-mcp/godot rev-parse HEAD
fc63af77c33368c4a1bb839c95d19750554f63a3
$ git -C godot-mcp/godot log -1 --format='%H %ci %s'
fc63af77c33368c4a1bb839c95d19750554f63a3 2026-09-29 10:37:49 +0800 evid: fix a comment typo in the mcp029 guard block (TASK-154)
$ git -C godot-mcp/godot status --porcelain | wc -l   -> 0    （-uall 亦 0）
$ git -C godot-mcp/godot ls-files | wc -l             -> 15049
$ git -C godot-mcp/godot ls-files modules/mcp_server | wc -l -> 721
$ find godot-mcp/godot -type f -newermt '2026-09-29 19:00' | wc -l -> 0
# ---- D242 收窄（数字核对）----
$ git ls-files godot-mcp | wc -l          -> 6484
$ git ls-files godot-mcp/godot | wc -l    -> 0
$ git check-ignore -v godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe
.gitignore:33:godot-mcp/godot/	godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe
```

**数字全部相符，无缺陷**：外层仓在 `godot-mcp/` 下确实跟踪 6484 个文件、对 `godot-mcp/godot/` 是 0（`.gitignore:33`），报告对 D242 的收窄准确；引擎\"未变更\"只用嵌套仓 + mtime 证明，未用外层 `git diff`。

### 8.6 三个假绿陷阱实测

```
# ① git diff 对不存在 pathspec 不报错（空输出不可当证据）
$ git diff --stat -- definitely/not/a/real/path ; echo exit=$?   -> exit=0（空）
$ git diff --stat -- src/runtime/run_loop.rs ; echo exit=$?      -> exit=0（空，形状无差别）
# ② cmd 的 ^ 静默改写 revision（故 rev^ 一律在 bash 做）
$ (bash) git -C godot-mcp/godot rev-parse HEAD^   -> bdf654b1086d27999e2a278ad187fadc40ce034c
$ (bash) git -C godot-mcp/godot rev-parse HEAD    -> fc63af77c33368c4a1bb839c95d19750554f63a3
$ cmd //c "git -C godot-mcp/godot rev-parse HEAD^" -> fc63af77c33368c4a1bb839c95d19750554f63a3   ← caret 被吃
$ cmd //c "echo A^B"   -> AB
$ cmd //c "echo A^^B"  -> A^B
$ cmd /C "echo hi"     -> 打印 cmd 横幅、未执行（MSYS 把 /C 当路径）
# ③ 外层仓不跟踪引擎树（外层 status 干净 ≠ 引擎未变）
$ git ls-files godot-mcp/godot | wc -l -> 0（见 §8.5）
```

三个陷阱的读法与报告一致；报告没有依赖 `rev^` 的结论。

### 8.7 诚实性核查（实测/推断 vs 我的复现）

| 报告主张 | 我的复现 | 判定 |
|---|---|---|
| A_0 = A_1 = fc78d299…，17 文件在三棵树上相同 | 逐字复现 | 真 |
| 加 1 个 `scripts/*.gd` 换摘要、加 `.hoh/**` 不变 | 复现（我 5 B → d7241bae…） | 真 |
| 排除集 {.hoh,.git,.godot,.import} | 逐行核实 | 真 |
| 上限 step_limit=150、三色 calls=150、墙钟 3095.2/3600 | 复现（config/hoh.yaml:14、traj、result.json） | 真 |
| TimeExceeded 是另一中断种类 | 复现（lib.rs:204-221 + agent.rs:167-171） | 真 |
| `no_progress` 唯一发射点、仅 warning、ok=true/exit 0 | 复现 | 真 |
| Developer：150 条 assistant、185 次调用全 bash、工程写 0、写动词 1 步 | 复现（185 bash、8 个写动词工具全 0） | 真（表 B 的 `project_set_setting=1` 除外，见 DEF-2） |
| $HOH_HOH_BIN：developer 9 / planner 2 / tester 4；planner `%…%` 1 | 按命令文本计数**完全一致** | 真 |
| shell 错误签名 10/4/3、quote-EOF 首现 step 67、115/150 显式 bash -c、首个包裹 step 29、此后 121 步仅 6 步未包 | 逐项复现（含 115、[31,32,33,34,35,42]） | 真 |
| \"第一个**成功**的 hoh tools call 在第 38 步 / 25.3%\" | 第 38 步输出是 CLI 报错；首个真实工具结果在 step 46（30.7%） | **DEF-1（实测标注不成立）** |
| `project_set_setting` 未落地：备份在、原件未变（mtime 13:21:03 / sha e4855a18…）、两个 args 文件不存在、命令输出为空 | 全部复现 | 真 |
| 三条树 / mtime 普查 / runs 未动 / PRD sha / 引擎嵌套仓 | 全部复现（§8.2-8.5） | 真 |
| 三份 traj assistant content 全空、无 reasoning_content | 复现（nonempty=0；无 reasoning_content） | 真（\"150 条\"对 planner/tester 不成立，DEF-4） |
| §7 的推断分栏 | 分栏属实，未见推断冒充实测 | 真 |

---

## 9. 我没有独立复核的部分 / 未验证项

1. **真机验证**：修复后 `A_1 != A_0` 需真机轮（本批禁止）；本轮所有结论都建立在冻结证据 + 离线对照上。
2. **因果权重**：shell 错配 / 步数预算 / DoD 三者的主因排序是报告自评的推断（≈0.6），我无法在离线分离；我只逐项核实了\"每个约束点的可测分量\"确实存在。
3. **project_set_setting 被哪一层吞掉**：备份 `cp` 落地、`printf` 目标缺失、两次 `hoh tools call` 输出为空——机制（cmd 引号截断 / hoh 失败 / 引擎拒绝）未定，报告也标为推断（§7-2）。我未新增实验。
4. **planner/tester 的同粒度时间线**：只做命令计数与终态（LimitsExceeded、artifact_valid=true），未逐步归类。
5. **两个电池 false 步的根因**：依赖 TASK-SMOKE-T7-REPORT 与已修代码的对照；我核实的只是\"battery_passes[0] 的两项 false\"与\"HEAD 上 scene_path/顶层 name 两处已被 DR-58 修好\"（godot.rs:1253-1257、:1596-1606）。
6. **Rust 生产代码路径**：本批不跑 `cargo`，我的 `hash_tree` 是 Python 重实现（与运行时 digest 逐字一致）。
7. **报告自报的 `rm -rf /tmp/dr64`**：我只核实了\"现在两处都不存在\"，无法核实删除动作本身。
8. 报告的 §6.4 `cmd` 变体、§6.3 的 `status --porcelain -- <不存在>` 一条我以等价命令实测通过，未逐字照抄其命令串。

---

## 10. 给下一批的建议（**我不修任何东西**）

1. **先采纳\"自动化假绿\"的修法**：让零增量成为可机读的**红色信号**（独立违约码/布尔字段），而不是 warnings 字符串——这是本批最重要的可交付改进，直接关系到\"未来的绿是否可信\"。
2. **实现测试时按 DEF-7 补强 (a)**：排除集从运行时同一配置来源取，并断言 `{.hoh,.git,.godot,.import}`；否则测试钉不住配置接缝。
3. **实现测试 (b) 时补 DEF 两点**：占位符抽取规则写进测试、平台门控，并把\"期望的红色文本\"锚到真实轨迹记录（如 developer 轨迹 step 27 的命令输出）。
4. **修法 1 优先于修法 2**（它是乘数），但**先跑一个便宜的离线契约红**（`role_shell_contract.rs` 的先红），再决定是否直接烧真机。
5. **下一轮真机判 E1 时，任务书应要求同时报出**：`A_0`、`A_1`、Developer 的工程写入计数、以及 `no_progress` 是否存在——不要让 exit 0 单独承载判定。
6. **沿用规范 digest 口径**（或同时记录两套）做禁区自证，避免像 DEF-6 那样\"自洽但不可与历史核对\"。
7. 未关闭的观测项（报告 §7-4 的\"编辑器异步落盘\"风险）应在真机轮里加一条\"写入后立即 hash、下一帧再 hash\"的对照，而不是继续悬着。

---

## 11. 诚实披露

1. **只读纪律**：我未修改任何既有文件（源码/测试/配置/`runs/**`/`.workspace/mario/**`/`PRD-mario.md`/`DECISIONS.md`/`godot-mcp/**`），未 commit/push/stage；本报告是唯一新增文件。
2. **离线纪律**：未启动 Godot、未碰端口、未联网、未调模型端点、未跑 cargo。全部操作是：读文件、离线 Python、只读 pwsh 摘要、只读 git、`find`/`ls`/`sha256sum`/`cmp`、`cmd //c echo`。
3. **仓外临时物**：`C:\Users\wyl\AppData\Local\Temp\dr64acc`（脚本 + ws0/ws1/ws2 拷贝）**已删除**，删除后 `runs` 规范摘要仍为 `01ff775e…`、仓库未跟踪项仍只有两个 spec 文件（外加本报告）。
4. **我没有\"顺手修\"任何东西**：包括 DEF-1..DEF-8 与两级假绿。它们留给后续实现批。
5. **我的独立性与限制**：我没有读实现者的中间过程，也不继承其结论；但我的判定建立在**同一批冻结证据**上（真机重跑被禁止），因此\"修复后是否真能 E1 met\"仍在未验证项里。
6. **不声称 E1/E3 已 met**：E1 仍 `not_met`；本报告只对诊断批的结论与证据作判定。

**报告写完后不再修改。**
