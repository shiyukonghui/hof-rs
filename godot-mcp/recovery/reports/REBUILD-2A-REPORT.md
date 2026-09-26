# TASK-079 — 重建阶段 2a 执行报告

> 在 C: 上组装重建树 + 逐文件缺口清单。**F: 全程零写入**。本阶段**只搬运 + 清点**：
> 未跑 scons、未跑门、未重写任何模块源码、**未对 `rebuild\godot` 打任何补丁**（补丁适用性用隔离沙箱验证）。
> 报告时间：2026-09-26 00:05（C: 本地）。

## 1. 结论摘要

| 项 | 结果 |
|---|---|
| 重建树 | `rebuild\godot\` **19,238 文件 / 1,185,231,246 B (1.10 GiB)** |
| 引擎基线 | `%TEMP%\audit002\tree`（09-22 全引擎树，无 `.git`）→ **可用，且确认「未打补丁」** |
| 模块落地 | **661** 个高/中置信载荷按原仓库相对路径落入正式树；**41** 个低置信落入 `rebuild\_low-confidence\` |
| 引擎三补丁 | 3 份 `git show` 原文已归档到 `rebuild\patches\`，并证明**按 1→2→3 顺序可干净应用**（`git apply` exit 0/0/0） |
| 契约资产 | `tools_list.renamed.json`（171 条，标注过期需重生成）、`tool-rename-map.json`（sha 与契约 `_meta.map_sha256` 一致）、legacy 174 条输入（**只读取自 F:**） |
| 可解析性 | `rebuild\godot`：`.py` **228/228 通过**；`.ps1` **129 中 6 个解析报错**（全部为 4.2 节的中置信残篇） |
| 与 TASK-078 对照 | `.ps1` **433/10 完全一致**；`.py` 复现为 **455/3**（078 记 453/3，差 2 已如实登记，见 §7） |
| F: 未触碰 | 开工/收尾两次核对：目标目录 0 子项，`LastWriteTimeUtc` 与 `CreationTimeUtc` **逐位相同**，卷剩余空间相同 |
| 阻塞 | 无硬阻塞；**构建前必须先修复 4 个模块缺口**（`registration.cpp` 为首） |

## 2. 三条铁律的合规证据

1. **F: 只读**。开工前 `work\fcheck-pre.txt`、收尾后 `work\fcheck-post.txt`：
   - 两次均为 `recurse.items=0`；
   - 目标目录 `LastWriteTimeUtc = 2026-09-25T15:19:49.0164127Z`（即事故删除时刻）**两次完全相同**，`CreationTimeUtc` 亦相同；
   - `F:` 卷剩余空间两次均为 `392,206,733,312` B；
   - 唯一一次读 F: 是**只读**读取 `F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json`（legacy 174 条输入），未写回。
2. **零 shell 重定向**。本任务所有写入均经 `Out-File -FilePath`（仅 `fcheck-*.txt`）、`[IO.File]::WriteAllText`（PS 解析结果）与 Python `io.open(...,'w')`；未出现 `>`/`>>`/`*>`/`2>&1`。
3. **破坏性命令受门控**。全部写入路径经 `guard()` 校验：必须绝对、必须以 `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\` 开头、不得含 `..` 或通配符。组装脚本是**幂等 + 可续跑**的（已存在且大小一致的文件不重写），全程**未删除任何文件**；仅在两个隔离沙箱 `work\patchdry`、`work\patchdry2` 中做过带「先打印将删清单 + 前缀校验」的清理。

## 3. 引擎基线可用性验证（①）

关键文件存在性（`rebuild\godot`，含 sha256）：

| 文件 | 存在 | 字节 |
|---|---|---|
| `SConstruct` | 是 | 53,702 |
| `core/config/project_settings.cpp` | 是 | 75,556 |
| `editor/editor_node.cpp` | 是 | 389,353 |
| `modules/mono/csharp_script.cpp` | 是 | 86,199 |
| `modules/gdscript/gdscript.cpp` | 是 | 87,346 |
| `platform/windows/**` | 是 | 69 文件 / 1,225,933 B |
| `modules/mcp_server/register_types.cpp` | 是 | 4,353 |

- 全树 **19,238 文件**；分目录：`graphify-out` 4,019、`bin` 4、`editor` 1,828、`thirdparty` 4,883、`doc` 837、`modules` 3,849、`core` 482、`scene` 847、`servers` 619、`platform` 873、`drivers` 254、`tests` 249、`misc` 400、`main` 15、`docs` 6、`.github` 26。
- **未拷入**：`bin\obj`（2.75 GB 可再生对象文件）与 84 个 `__pycache__`（共 3,168 文件 / 2,750,916,297 B）——**显式声明**，非静默丢弃；`bin\` 下的 4 个文件（含 180 MB 的 `godot.windows.editor.x86_64.exe`）**已拷入**，树内因此有一个可跑的（不过期补丁的）编辑器。

### 3.1 它是「已含补丁」的版本吗？——**不是**

对 5 个将被补丁修改的引擎文件做全文扫描，四个补丁符号的出现次数**全部为 0**：

| 符号 | 由哪个补丁引入 | 基线中出现次数 |
|---|---|---|
| `is_source_newer_than_assembly` | 补丁 1（`5f3e7fb441`） | 0 |
| `update_settings_section_text` | 补丁 2（`96f631addb`） | 0 |
| `save_custom_section` | 补丁 2 | 0 |
| `save_preserving_text` | 补丁 3（`2f85141a74`） | 0 |

并且 `git apply --check` 接受全部三个补丁（补丁 3 需在补丁 2 之后）。**结论：基线是本 fork 的「补丁前」上游状态，正是重放三补丁的正确 pre-image。**

### 3.2 一个必须记住的副作用：暂存区是 LF、基线是 CRLF

staging 的载荷统一为 **LF / 无 BOM**，而基线文本是 **CRLF**，两个 .NET SDK `.csproj` 还带 **UTF-8 BOM**。例：`Godot.NET.Sdk.csproj` staging 1,863 B / 42 LF / 无 BOM vs 基线 1,910 B / 43 CRLF / 带 BOM——**去掉 BOM、统一换行后逐行完全相同**。因此后续任何「字节级比对」都要先归一化 EOL，否则会把 EOL 差异误读成内容漂移（模块自身的证据文档 `GIT-EOL-NORMALIZATION.md` 也记了同一件事）。

## 4. 模块落地（②）

| 类别 | 数量 | 去向 |
|---|---:|---|
| 模块高/中置信 | 661 | `rebuild\godot\modules\mcp_server\**` |
| 非模块高/中置信 | 11 | `rebuild\godot\**`（其中 5 个与基线逐字节相同，判为「已在树中」） |
| 低置信 | 41 | `rebuild\_low-confidence\modules\mcp_server\**` 等 |
| `.git\` 内的草稿文件 | 1 | `rebuild\_excluded\`（非仓库内容，不污染正式树） |
| `__history` 4,543 版本 | 0 拷入 | 按指令留在 `staging\__history\` |

低置信目录构成：`modules` 40、`core` 1、`platform` 1、根目录 1（另加 2 份为审计保留的契约截断版）。

**谨慎处置（重要）**：staging 里有 **191** 个引擎/根目录路径，其载荷是「读窗口残篇」，而基线已有完整文件。逐字节比对后：**30 个只差末尾换行**、**2 个只差 BOM/CRLF**、**2 个是构建日志内容漂移**、**157 个是明显更小的残篇**（最大缺 32 万字节，如 `thirdparty/doctest/doctest.h` 1,229 B vs 323,308 B）。**没有任何一个残篇大于基线对应文件**，所以不存在「更新的完整版本被丢弃」的可能——用基线覆盖是正确的，逐条列在 MANIFEST §4.2 供审计。

## 5. 引擎三补丁改动点（③）

产物：`rebuild\ENGINE-PATCHES-TO-REAPPLY.md`（64 KB）+ `rebuild\patches\*.diff`（原文）+ `SHA256SUMS.txt`。

| # | commit | 触及文件 | hunk | +/- | 产物 sha256（前 16） |
|---|---|---|---:|---|---|
| 1 | `5f3e7fb441` | `modules/mono/csharp_script.{cpp,h}` | 3 | +40/-3 | `6b0ee95c2abde614` |
| 2 | `96f631addb` | `core/config/project_settings.{cpp,h}` | 4 | +483/-0 | `70decff99a232fd5` |
| 3 | `2f85141a74` | `project_settings.{cpp,h}` + `editor/editor_node.cpp` | 9 | +253/-28 | `41867b2962fce8c7` |

**适用性证据（隔离沙箱 `work\patchdry*`，`rebuild\godot` 未被修改）**：

| 动作 | 结果 |
|---|---|
| 原始基线上 `git apply --check patch1` | **exit 0** |
| 原始基线上 `git apply --check patch2` | **exit 0** |
| 原始基线上 `git apply --check patch3` | **exit 1（预期）**：找不到补丁 2 才引入的 `save_custom_section` — 证明**补丁 3 依赖补丁 2** |
| 沙箱内先打 patch2 再 `--check patch3` | **exit 0** |
| 沙箱内按序 `patch1 → patch2 → patch3` | **exit 0/0/0**，五个文件全部干净应用 |

重放后的可核对状态（沙箱实测，字节/行/sha256 全表见补丁清单 §5）：

| 文件 | 原始 | 补丁后 |
|---|---|---|
| `project_settings.cpp` | 75,556 B / 1,628 行 | 102,533 B / 2,178 行 |
| `project_settings.h` | 13,295 B / 238 行 | 19,002 B / 314 行 |
| `editor_node.cpp` | 389,353 B / 8,343 行 | 400,247 B / 8,361 行 |
| `csharp_script.cpp` | 86,199 B / 2,228 行 | 89,504 B / 2,242 行 |
| `csharp_script.h` | 20,978 B / 451 行 | 22,687 B / 470 行 |

补丁清单里还给出了每个 hunk 的原文与邻接上下文、新符号、ClassDB 绑定位置、以及「补丁 3 必须用**开窗**编辑器才能观察注释保留（且要同时比 **mtime**，只比字节无法区分『写了没变』与『根本没写』）」这一关键提醒。

## 6. 其它仓库资产（④）

| 仓库路径 | 来源 | 字节 | sha256 | 说明 |
|---|---|---:|---|---|
| `modules\mcp_server\docs\tools_list.renamed.json` | `%TEMP%\mcp044-module-backup\...` | 118,032 | `443f1df2…` | staging 版是**截断的读窗口**（覆盖 20.3%、缺尾）；取备份中的完整副本。`_meta` 只有 **171** 条，**不是最终 176** → 标注为过期，**必须用生成器重跑**（RECOVERY-PLAN §4.2） |
| `modules\mcp_server\docs\tool-rename-map.json` | `%TEMP%\mcp044-module-backup\...` | 70,917 | `2f552719…` | staging 版同样截断（14.8%）；完整版 sha256 与契约 `_meta.map_sha256` 一致 → 最后已知良好版本 |
| `_refs\legacy-174\tools_list.json` | `F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json`（**只读**） | 48,749 | `8f8051c4…` | **legacy 174 条输入**；其 sha256 正是契约 `_meta.generated_from_sha256`，即生成器的输入源 |

两份截断的 staging 副本没有删除，而是留在 `_low-confidence\` 供审计。

## 7. 可解析性抽检（与 TASK-078 对照）

| 区域 | `.py` 总数 | 通过 | 失败 | `.ps1` 总数 | 报错 |
|---|---:|---:|---:|---:|---:|
| `rebuild\godot` | 228 | **228** | 0 | 129 | **6** |
| `rebuild\_low-confidence` | 7 | 4 | 3 | 10 | 2 |
| `staging\`（078 的集合） | 458 | 455 | 3 | **433** | **10** |

- `.ps1`：**433/10 与 TASK-078 完全一致**。
- `.py`：078 记「453 通过 / 3 失败」（合计 456），本次对同一份 `reconstruction.jsonl` 直接扫得 **458 条**（455 通过 / 3 失败）。失败的三条逐字一致（`methods.py:60`、`modules\mono\build_scripts\build_assemblies.py:74`、`platform\windows\detect.py:1`，全是引擎侧残篇）。**差的 2 条如实登记为未解释差异**（最可能是当时被计为 `missing`，索引其后被重生成），并附上逐文件失败清单使其可核对。
- `rebuild\godot` 的 `.py` **零失败**：那三条失败文件在正式树里由基线提供了完整原件。6 个 `.ps1` 报错全部是 4.2 节的**中置信残篇**（`accept_m1.ps1` 10 错、`mcp022` 6、`mcp053` 6、`mcp027` 3、`mcp060_lib` 2、`mcp067_live` 1），清单见 MANIFEST §6.2。

## 8. 缺口表（硬缺口，逐文件）

| 路径 | 状态 | 树中当前内容 | 影响 | 建议 |
|---|---|---|---|---|
| `modules\mcp_server\tools\registration.cpp` | 低置信（17,014 B 在 `_low-confidence`） | 09-22 化石 2,580 B | **阻断编译** | **最先修**，再核 42 处失败编辑 |
| `modules\mcp_server\tests\test_mcp_server.h` | 低置信（431,976 B） | 09-22 化石 66,392 B | 门③（doctest）无法跑 | 以「最后一次完整 read」为锚重抽，或用三补丁 commit 里的模块侧 hunk 重放 |
| `modules\mcp_server\scripts\gen_renamed_contract.py` | 低置信（118,449 B） | 09-22 化石 21,390 B | 契约无法重生成 | 重抽后再跑生成器 |
| `modules\mcp_server\scripts\accept_m1.ps1` | 中置信（已落 57,469 B，覆盖原 09-22 副本） | staging 版 | 门⑤ 无法跑 | 修 10 处解析错误（如缺 `catch`） |
| `modules\mcp_server\docs\DESIGN-DETAIL.md` | 低置信（84,486 B） | 09-22 化石 31,531 B | 仅文档 | 用「完整覆盖但 50 处编辑失败」的副本做二次核验 |

另有 **4 个「看起来完整」却被判低置信**的文件（覆盖 100%、尾部完整，仅因编辑重放失败被降级），列为阶段 2b 的**最高价值复核项**：`registration.cpp`、`editor_playback.cpp`、`DESIGN-DETAIL.md`、`tool-groups-b5.json`。

以及 **516** 条「模块清单里有、但从未被暂存」的路径（MANIFEST 附录 A 全文）：全部是**证据与缓存**（377 `.json` / 108 `.log` / 20 `.txt` / 4 `.pyc` / 4 `.md` / 1 `.jsonl` / 1 `.patch` / 1 `.rewritten`），**没有一条是 `tools\*.cpp/h` 或 `scripts\*.ps1/py`**；该清单源自一次被截断的终端 dump，故 516 是**下界**。

## 9. 未落地清单（WBS：未进 rebuild 的东西）

| 类别 | 数量 | 位置 | 原因 |
|---|---:|---|---|
| 低置信载荷（+2 份审计用截断契约） | 43 | `rebuild\_low-confidence\` | 置信度规则：不得污染正式树 |
| `.git\` 草稿 | 1 | `rebuild\_excluded\` | 非仓库内容 |
| 未覆盖的读窗口残篇 | 191 | 仅 `staging\` | 覆盖会回退已完整的基线文件 |
| 仓库外载荷 | 1,406 | `staging\__external\` | 属其它工程 |
| 索引有路径但无载荷 | 39 | 无 | 记录里从来没有可用字节 |
| `__history` / `__candidates` | 4,543 / 296 | `staging\` | 按指令留在 staging |
| `bin\obj` + `__pycache__` | 3,168 | 仅在基线快照 | 可再生构建产物 |

## 10. 本阶段**未**做的事

scons 构建（未尝试）、六道门（未跑）、模块源码重写（未做）、对 `rebuild\godot` 打补丁（未做；适用性用隔离沙箱验证）。收尾核对：树中 5 个引擎文件的 sha256 与原始基线**逐位相同**（`ALL PRISTINE`）。

## 11. 产物清单

| 产物 | 路径 |
|---|---|
| 组装结果 / 缺口表 / 解析抽检 / 未落地清单 | `REBUILD-2A-MANIFEST.md`（104,883 B） |
| 本报告 | `REBUILD-2A-REPORT.md` |
| 三补丁可执行清单 | `rebuild\ENGINE-PATCHES-TO-REAPPLY.md`（64,085 B） |
| 补丁原文 + 校验和 | `rebuild\patches\*.diff`、`rebuild\patches\SHA256SUMS.txt` |
| 重建树 | `rebuild\godot\`（19,238 文件 / 1.10 GiB） |
| 低置信隔离区 / 排除区 / 参考输入 | `rebuild\_low-confidence\`、`rebuild\_excluded\`、`rebuild\_refs\legacy-174\` |
| 机器可读证据 | `work\assembly-stats.json`、`work\parse-py.json`、`work\parse-ps1-rebuild.json`、`work\patch-info.json`、`work\fcheck-pre.txt`、`work\fcheck-post.txt`、`work\drift-detail.txt` |
| 复现脚本 | `scripts\assemble_rebuild_2a.py`、`scripts\parse_check_rebuild_py.py`、`scripts\parse_check_rebuild_ps1.ps1`、`scripts\patch_dryrun.ps1`、`scripts\patch_dryrun2.ps1`、`scripts\park_engine_patches.py`、`scripts\gen_patch_manifest.py`、`scripts\gen_manifest.py` |
| 隔离沙箱（补丁适用性证据，可随时删） | `work\patchdry\`（5 文件）、`work\patchdry2\`（5 文件）——**声明**，非垃圾 |

## 12. 遗留风险与下一步建议

1. **`registration.cpp` 是唯一的编译级阻断**，且它是「看起来完整」的低置信文件——先做它的二次核验，可能立刻解锁构建。
2. 三个 `.ps1` 与 `accept_m1.ps1` 的解析错误都是**局部尾部/中段缺失**，修起来比分文件更便宜，但**不要在阶段 2a 之后的阶段偷改实现**：按流程应作为新决策下发给实现子代理。
3. 契约文件（`tools_list.renamed.json`）当前是 171 条旧版，**绝不能当作门①的基准**；必须先用恢复后的 `gen_renamed_contract.py` 重生成，并与 `DECISIONS.md` D110–D135 记录的 sha/计数对照。
4. 补丁 3 的行为（`project.godot` 注释保留）只能在**开窗**编辑器下验证，且必须同时看 mtime——这一点已写进补丁清单。
5. EOL：任何后续「逐字节」断言前先归一化，否则会得到大量假失败。
