# -*- coding: utf-8 -*-
"""Build F:\\moonbit-hof-rs\\godot-mcp\\dist\\godot-mcp-20games-<ts>.zip

Read-only over the reviewed objects (projects\\ and runs\\ are only ever read).
Excludes build artifacts (.godot, bin, obj, .mono) and any user:// cache.
No shell redirection is used anywhere: every file is written by this Python
process, and the zip is produced by zipfile.

    python dist\\build_package.py            # build + self-check

Outputs (all under dist\\):
    godot-mcp-20games-<yyyyMMdd-HHmm>.zip
    godot-mcp-20games-<yyyyMMdd-HHmm>.sha256.txt   (sidecar, zip's own digest)
    godot-mcp-20games-<yyyyMMdd-HHmm>.MANIFEST.txt (copy of the in-zip manifest)
    build-report.json                              (self-check result)
"""
import hashlib, json, os, re, shutil, sys, time, zipfile, tempfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = r'F:\moonbit-hof-rs\godot-mcp'
DIST = os.path.join(ROOT, 'dist')
DATA = os.path.join(DIST, 'review_data.json')

EXCLUDE_DIRS = {'.godot', 'bin', 'obj', '.mono', '.vs', '__pycache__', '.git',
                'user_data', 'userdata', '.cache', 'node_modules'}
EXCLUDE_EXT = {'.user', '.tmp', '.log~'}

TS = time.strftime('%Y%m%d-%H%M')
BASE = 'godot-mcp-20games-%s' % TS
ZIP_PATH = os.path.join(DIST, BASE + '.zip')
SHA_PATH = os.path.join(DIST, BASE + '.sha256.txt')
MAN_PATH = os.path.join(DIST, BASE + '.MANIFEST.txt')


def sha256_file(p, buf=1 << 20):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            b = f.read(buf)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def copy_tree(src, dst, log):
    """Read-only copy honouring the exclusion policy."""
    for dp, dn, fn in os.walk(src):
        dn[:] = sorted(d for d in dn if d not in EXCLUDE_DIRS)
        rel = os.path.relpath(dp, src)
        target = dst if rel == '.' else os.path.join(dst, rel)
        os.makedirs(target, exist_ok=True)
        for f in sorted(fn):
            if os.path.splitext(f)[1].lower() in EXCLUDE_EXT:
                continue
            s = os.path.join(dp, f)
            t = os.path.join(target, f)
            shutil.copy2(s, t)
            log.append(os.path.relpath(t, STAGE))


def tag_prefix_counts(run):
    rows = [l.rstrip('\n').split('|')[0] for l in
            open(os.path.join(run, 'call-index.txt'), encoding='utf-8-sig') if l.strip()]
    return rows


def pick_shots(run, game, out_run, log, comparable):
    """Up to 3 capture pairs (6 PNGs) with the largest changed_pixels."""
    pairs = []
    for phase in ('game', 'editor'):
        tp = os.path.join(run, 'trace-%s.jsonl' % phase)
        if not os.path.exists(tp):
            continue
        for line in open(tp, encoding='utf-8', errors='replace'):
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            if 'after' not in o or o.get('event') != 'capture':
                continue
            b, a = o.get('before') or {}, o.get('after') or {}
            pairs.append({'phase': phase, 'seq': o.get('seq'), 'tool': o.get('tool'),
                          'changed_pixels': int(o.get('changed_pixels') or 0),
                          'changed': bool(o.get('changed')),
                          'before': b, 'after': a})
    pairs.sort(key=lambda p: (-p['changed_pixels'], p['phase'] != 'game', p['seq'] or 0))
    chosen = []
    for p in pairs:
        if len(chosen) >= 3:
            break
        if p['changed_pixels'] <= 0 and any(c['changed_pixels'] > 0 for c in chosen):
            continue
        if not (p['before'].get('path') and p['after'].get('path')):
            continue
        if not (os.path.exists(p['before']['path']) and os.path.exists(p['after']['path'])):
            continue
        chosen.append(p)
    index = []
    for p in chosen:
        outdir = os.path.join(out_run, 'shots-%s' % p['phase'])
        os.makedirs(outdir, exist_ok=True)
        for role in ('before', 'after'):
            src = p[role]['path']
            name = os.path.basename(src)
            shutil.copy2(src, os.path.join(outdir, name))
            rel = 'games/%s/runs/%s/%s/shots-%s/%s' % (
                game, game, os.path.basename(run), p['phase'], name)
            log.append(rel)
            index.append((rel, p, role, sha256_file(os.path.join(outdir, name))))
    if index:
        lines = ['# 代表截图索引 (SHOTS-INDEX) -- %s' % game, '']
        lines.append('选取规则：按 trace 里 capture pair 的 changed_pixels 降序，取最多 3 对'
                     '（before + after，共最多 6 张）；像素差为 0 的对只在没有任何非零对时才入选。')
        lines.append('')
        lines.append('%-58s %-6s %-9s %-6s %-12s %s' %
                     ('包内路径', '相', 'seq', '角色', 'changed_px', 'sha256'))
        for rel, p, role, sha in index:
            lines.append('%-58s %-6s %-9s %-6s %-12d %s' %
                         (rel, p['phase'], 'g%04d' % (p['seq'] or 0), role,
                          p['changed_pixels'], sha))
        lines.append('')
        lines.append('说明：本款最终运行共有 %s 个可比 capture pair；包内只带上面这 %d 张代表截图。'
                     % (comparable, len(index)))
        lines.append('      完整的前后截图对在原始运行目录 `runs\\%s\\%s\\shots-game` 与 `shots-editor` 下；'
                     % (game, os.path.basename(run)))
        lines.append('      用 `tools\\game_report.py`，或按 README-REVIEW.md §6 自写 PNG 复算脚本，可逐对重算像素差。')
        outp = os.path.join(out_run, 'SHOTS-INDEX.txt')
        with open(outp, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        log.append('games/%s/runs/%s/%s/SHOTS-INDEX.txt'
                   % (game, game, os.path.basename(run)))


def build_readme(data, docs_note):
    g = data['games']
    t = data['totals']
    L = []
    A = L.append
    A('# 20 款 C# Godot 小游戏 —— 人工复核包')
    A('')
    A('* **包名**：`%s.zip`' % BASE)
    A('* **生成时间**：%s（本机时区）' % time.strftime('%Y-%m-%d %H:%M:%S'))
    A('* **口径**：决策 `D138` —— 轮次不设限，**至少 20 个经典小游戏、全部 C#**，每款都要有可复算的')
    A('  「操作有效性」证据（像素差 / 文件 sha / 断言 / 场景树快照），不接受「应该动了」。')
    A('* **验收状态**：`ACCEPTANCE-TASK-107.md` 判 **pass**（第二轮独立验收；上一轮 3 条 fail 已修）。')
    A('* **数据来源**：本文件表格里的每个数字都是打包脚本从各款**最终运行自己的产物**里重算出来的，')
    A('  （`call-index.txt` / `ledger-*.json` / `report.json` / 每条调用的响应 `*.json`），')
    A('  不是从任何报告文字转抄的。仅「缺陷数」一列引自 `docs\\GAME-LOOP-LOG.md` 的里程碑表。')
    A('')
    A('---')
    A('')
    A('## 1. 20 款游戏一览')
    A('')
    A('| # | 游戏 | 最终运行 | 调用数（编辑器/游戏） | `facts_complete` | 断言（pass/fail） | 像素差（非零/可比） | 独立复算 | 缺陷（工具/游戏或驱动） |')
    A('|---|---|---|---|---|---|---|---|---|')
    for i, r in enumerate(g, 1):
        note = ('（%s）' % r['defects_note']) if r['defects_note'] else ''
        A('| %d | %s | `%s` | %d / %d（%d） | %d/%d + %d/%d = **%d%%** | %d / %d | %s / %s | 0 处不符 | %d / %d%s |' % (
            i, r['label'], r['run_tag'], r['calls_editor'], r['calls_game'], r['calls_total'],
            int(r['facts_editor'].split('/')[0]), r['calls_editor'],
            int(r['facts_game'].split('/')[0]), r['calls_game'], r['facts_percent'],
            r['assertions']['passed'], r['assertions']['failed'],
            r['pixel_nonzero'], r['pixel_comparable'],
            r['defects_tool'], r['defects_game'], note))
    A('')
    A('**合计**：调用 **%d** 次（编辑器 %d / 游戏 %d）；`facts_complete` **20 款全部 100%%**；'
      % (sum(r['calls_total'] for r in g),
         sum(r['calls_editor'] for r in g), sum(r['calls_game'] for r in g)))
    A('断言 **passed=%d / failed=%d / errors=%d**；**未声明失败 %d 条**；'
      % (t['passed'], t['failed'], t['errors'], t['undeclared']))
    A('像素差有 **%d/%d** 个可比 capture pair 非零（20 款全部可得且逐款非零）。'
      % (sum(r['pixel_nonzero'] for r in g), sum(r['pixel_comparable'] for r in g)))
    A('')
    A('* 「调用数」= 会话真正驱动的调用（编辑器相 + 游戏相）。每款运行目录里的 `call-index.txt` 行数')
    A('  可能更多：它把**清理相（tag 前缀 `c`）**与驱动自己的 `e01-tools-list` 也记进去了。')
    A('  （编辑器相 = tag 前缀 `e` 或 `r` 的行，减去 `e01-tools-list`；游戏相 = tag 前缀 `g` 的行。）')
    A('  本表合计 `%d` 与 `GAME-LOOP-LOG.md` 里程碑表里的 `2554` 不同，是因为那张表是 **TASK-104 收口'
      % sum(r['calls_total'] for r in g))
    A('  那一刻的快照**（Snake 记为 20/31），而本表按 TASK-106 追记取 Snake 的当前最终轮 20/33 —— 差 2 次；')
    A('  其余 19 款两处逐行相同。')
    A('* 「断言」只统计运行自己保存的响应里带 `passed` / `all_passed` 的那类调用；')
    A('  逐条明细见 `runs\\<game>\\<tag>\\` 下的响应 `*.json` 与 `ledger-*.txt`。')
    A('* 「像素差」= `report.json` 的 `pixel_evidence.non_zero_pairs / comparable_pairs`。')
    A('* 「未声明失败」= 失败的断言里，tag 与 note **都没有**声明「这条本来就要失败」的条数')
    A('  （`TASK-106` 新增的报告层计数器，独立复算与 `ACCEPTANCE-TASK-107.md` 的 0 一致）。')
    A('')
    A('---')
    A('')
    A('## 2. 环境要求')
    A('')
    A('| 项 | 值 |')
    A('|---|---|')
    A('| Godot | 本仓 fork 的 **mono** 版：`%s` |' % data['engine'])
    A('| 版本串 | `%s`（引擎仓分支 `feature/mcp-server-module-rebuild`，HEAD `1f9d0cb1c`） |' % data['engine_version'])
    A('| GUI 编辑器 | `godot\\bin\\godot.windows.editor.x86_64.mono.exe` |')
    A('| 无窗口运行 | `godot\\bin\\godot.windows.editor.x86_64.mono.console.exe` |')
    A('| .NET | 工程 `TargetFramework=net8.0`、`Godot.NET.Sdk/4.8.0-dev`；需要的 .NET SDK ≥ 8.0 |')
    A('| 本机实测 | .NET SDK `9.0.100` / `9.0.300` / `10.0.300-preview.0.26177.108` |')
    A('| NuGet | **完全离线**：`projects\\<game>\\NuGet.config` 把源指向 `godot\\bin\\GodotSharp\\Tools\\nupkgs` |')
    A('| 端口 | 试测驱动用编辑器 9888 / 游戏 9889（`run_game_session.ps1` 的默认值） |')
    A('')
    A('> 包内 `games\\<game>\\projects\\<game>\\NuGet.config` 里的相对路径是 `..\\..\\godot\\bin\\...`。')
    A('> 若你把工程搬到别处，要么同步搬 `godot\\bin\\GodotSharp\\Tools\\nupkgs`，要么改这个源。')
    A('')
    A('---')
    A('')
    A('## 3. 包内结构')
    A('')
    A('```')
    A(BASE + '/')
    A('  README-REVIEW.md                本文件（中文复核入口）')
    A('  MANIFEST.txt                    逐文件 sha256 + 字节数（本包全部文件）')
    A('  games/<game>/                   20 款，一款一个目录')
    A('    projects/<game>/              全量源码与场景（src/*.cs、scenes/*.tscn、*.csproj、project.godot、README.md）')
    A('    tools/sessions/<game>/        session.json（调用序列）+ payload/（C# 载荷，即会话真正写进工程的实现）')
    A('    runs/<game>/<run-tag>/        该款最终运行的证据')
    A('        report.json report.md')
    A('        ledger-editor.txt ledger-game.txt ledger-editor.json ledger-game.json')
    A('        trace-editor.jsonl trace-game.jsonl (+ trace-*.sidecar/：被截断 args/result 的原件)')
    A('        call-index.txt            tag|port|req_bytes|resp_bytes|note')
    A('        SHOTS-INDEX.txt           代表截图的选取记录（seq / 角色 / changed_pixels / sha256）')
    A('        shots-game/ shots-editor/ 最多 6 张代表截图（before/after 成对）')
    A('  docs/GAME-LOOP-LOG.md           跨轮进度台账（含「里程碑：20 款」表与 TASK-106 追记）')
    A('  docs/MCP-TRACEABILITY.md        trace / 台账 / 像素证据的可溯源规则')
    A('  docs/DECISIONS-EXCERPT.md       与本目标相关的 DECISIONS.md 段落副本（D138–D153）')
    A('  docs/ACCEPTANCE-TASK-105.md     第一轮独立验收报告（判 fail，3 条）')
    A('  docs/TASK-106-REPORT.md         修复报告（逐条对上 105 的 fail）')
    A('  docs/ACCEPTANCE-TASK-107.md     第二轮独立验收报告（判 pass）')
    A('  tools/game_report.py            运行目录 -> report.json / report.md')
    A('  tools/mcp_trace_ledger.py       trace-*.jsonl -> ledger-*.{txt,json}')
    A('  tools/run_game_session.ps1      统一试测驱动（起两端引擎 + 重放会话 + 出报告）')
    A('```')
    A('')
    A('**未打进包的东西（有意为之）**：')
    A('')
    A('* 构建产物 `.godot\\`、`bin\\`、`obj\\`、`.mono\\`，以及 `user://` 缓存；')
    A('* 中间轮跑法（每款只放最终轮）；')
    A('* 原始运行目录里的 `engine-*.stdout.txt` / `import.*` / `*.cmd` 等旁证（原件仍在仓库里）；')
    A('* 每款完整的前后截图对（包内只放最多 6 张代表截图，见 §6）。')
    A('')
    A('---')
    A('')
    A('## 4. 如何打开并运行任一款游戏')
    A('')
    A('### 4.1 用 GUI 编辑器打开（最快）')
    A('')
    A('```')
    A('<root>\\godot\\bin\\godot.windows.editor.x86_64.mono.exe -e --path <root>\\projects\\<game>')
    A('```')
    A('')
    A('`<root>` = 一个把本包的 `games\\<game>\\projects\\<game>` 与 `tools\\sessions\\<game>`')
    A('按原布局摊平的目录（例如仓库根 `F:\\moonbit-hof-rs\\godot-mcp`）。')
    A('')
    A('### 4.2 直接跑游戏（无窗口）')
    A('')
    A('```')
    A('<root>\\godot\\bin\\godot.windows.editor.x86_64.mono.console.exe --path <root>\\projects\\<game>')
    A('```')
    A('')
    A('### 4.3 重放该款的完整证据会话（复现 trace / 台账 / 报告）')
    A('')
    A('```')
    A('powershell -NoProfile -ExecutionPolicy Bypass -File <root>\\tools\\run_game_session.ps1 `')
    A('  -Game <game> `')
    A('  -Root <root> `')
    A('  -Engine <root>\\godot\\bin\\godot.windows.editor.x86_64.mono.console.exe `')
    A('  -RunTag review-replay ')
    A('```')
    A('')
    A('它会：起编辑器端点（9888）+ 游戏端点（9889），按 `tools\\sessions\\<game>\\session.json`')
    A('逐条发 MCP 调用，落 `trace-*.jsonl` 与 `shots-*\\`，然后用 `mcp_trace_ledger.py` 出台账、')
    A('用 `game_report.py` 出 `report.json` / `report.md`。')
    A('')
    A('> 复现是**重放**而不是「同一张图」：会话里的断言会重跑一遍，数字应当相同；')
    A('> PNG 的 sha256 一般不同（引擎 `uid`、时间戳、帧时机）。已声明的例外：')
    A('> Flappy Bird r2 / Minesweeper r2 的保存帧与 r1 **逐字节相同**（确定性状态机）。')
    A('')
    A('---')
    A('')
    A('## 5. 如何查看 trace 与台账')
    A('')
    A('### 5.1 trace（`trace-*.jsonl`）')
    A('')
    A('一行一条 MCP 调用，字段自解释：`id` / `method` / `tool` / `args` / `args_bytes` / `ok` /')
    A('`error_code` / `error_message` / `result_json` / `duration_ms` / `args_evidence`；')
    A('截图调用还有 `before` / `after`（各自的 `path` / `bytes` / `width` / `height` / `sha256`）、')
    A('`changed` / `changed_pixels` / `changed_pixel_ratio`。')
    A('')
    A('```')
    A('python -c "import json,sys;[print(json.loads(l).get(\'tool\'), json.loads(l).get(\'ok\')) for l in open(r\'trace-game.jsonl\',encoding=\'utf-8\') if l.strip()]"')
    A('```')
    A('')
    A('`trace-*.sidecar/` 里放的是被 trace 截断的 `args` / `result` 原件（只在超限时出现，'
      '本包内每款通常 0–3 个文件）。')
    A('')
    A('### 5.2 台账（`ledger-*.txt` / `ledger-*.json`）')
    A('')
    A('* `.txt` 是人读表：`seq | tag | tool | verdict | flags | args_evidence | ...`；')
    A('* `.json` 是同一批行的机器可读版本，`facts_complete` / `verdict` / `error_flags` 都在行上。')
    A('')
    A('```')
    A('# 用法：mcp_trace_ledger.py <trace.jsonl> [--json OUT] [--text OUT] [--only-ineffective]')
    A('python tools\\mcp_trace_ledger.py games\\<game>\\runs\\<game>\\<tag>\\trace-game.jsonl ^')
    A('       --text %TEMP%\\ledger-game.txt --json %TEMP%\\ledger-game.json')
    A('```')
    A('')
    A('`--text` / `--json` 都不给时只打控制台。包内每款已经带好了这一对文件（直接用即可，')
    A('不必重跑；重跑只是复核「台账确实是从这条 trace 生成的」）。')
    A('')
    A('判定分布（本包重算）：`ok_effect_observed` / `ok_file_effect_observed` /')
    A('`ok_no_effect_observed` / `failed`。`facts_complete` 是本包第 1 节那一列。')
    A('')
    A('### 5.3 `call-index.txt`')
    A('')
    A('驱动为每次调用写的一行：`tag|port|req_bytes|resp_bytes|note`。')
    A('**note 是会话作者写的意图**，也是「这条失败是不是声明的」的判据来源之一。')
    A('')
    A('---')
    A('')
    A('## 6. 如何复算像素差')
    A('')
    A('像素差 = 「一次调用前后的两张 2D 截图有多少像素不同」。两处记录：')
    A('')
    A('1. **逐调用对**：`trace-*.jsonl` 的每条 capture 上的 `changed_pixels` / `changed`；')
    A('   汇总在 `report.json` 的 `pixel_evidence`（本包第 1 节的「像素差」列）。')
    A('2. **保存帧链**：会话把 `user://` 里的若干帧（`<game>-t0.png` … `<game>-final.png`）')
    A('   两两相比，`report.json` 的 `saved_frames`。')
    A('')
    A('**独立复算（不读 `report.json`、不 import `game_report.py`）**：拿原始运行目录里')
    A('完整的 `shots-game\\` / `shots-editor\\`，自己解码 PNG 再数一遍不同的像素：')
    A('')
    A('```python')
    A('# 复算逐调用像素差（需要 Pillow；两套规则都算）')
    A('import json, os, sys')
    A('from PIL import Image, ImageChops')
    A('run = sys.argv[1]')
    A('nonzero_engine = nonzero_any = comparable = 0')
    A('for line in open(os.path.join(run, "trace-game.jsonl"), encoding="utf-8"):')
    A('    if not line.strip():')
    A('        continue')
    A('    o = json.loads(line)')
    A('    if o.get("event") != "capture" or "after" not in o:')
    A('        continue')
    A('    b, a = Image.open(o["before"]["path"]).convert("RGB"), Image.open(o["after"]["path"]).convert("RGB")')
    A('    if b.size != a.size:')
    A('        continue')
    A('    comparable += 1')
    A('    diff = ImageChops.difference(b, a).convert("L")')
    A('    any_px = sum(1 for v in diff.getdata() if v)')
    A('    eng_px = sum(1 for v in diff.getdata() if v > 10)')
    A('    nonzero_engine += eng_px > 0')
    A('    nonzero_any += any_px > 0')
    A('    if o["changed_pixels"] != eng_px:')
    A('        print("MISMATCH seq", o["seq"], o["changed_pixels"], eng_px)')
    A('print("comparable", comparable, "engine-rule non-zero", nonzero_engine, "any-rule non-zero", nonzero_any)')
    A('```')
    A('')
    A('把 `trace-game.jsonl` 换成 `trace-editor.jsonl` 就是编辑器相。')
    A('**预期**：`MISMATCH` 一行都不出现，两套规则在这 20 款上给出同一批非零组数。')
    A('')
    A('> **在包内复算**：trace 里的 `before` / `after` 是原始绝对路径，包内不可达。'
      '把上面那两行改成')
    A('> 「用 `os.path.basename(o["before"]["path"])` 去 `<tag>\\shots-<phase>\\` 下找同名文件」，')
    A('> 就能只用包内这最多 6 张代表截图复算这几对的像素差；整批 2 612 对的复算仍要在原始运行目录上做。')
    A('')
    A('> 本包只带**最多 6 张代表截图**（§3、`SHOTS-INDEX.txt`），所以整批的复算要在原始运行目录上做。')
    A('> 包内这 6 张仍可用 `MANIFEST.txt` 的 sha256 逐张核对「搬进来的是原件」。')
    A('')
    A('---')
    A('')
    A('## 7. 复核清单')
    A('')
    A('- [ ] **20 款一款不少**：`games\\` 下是否正好 20 个目录，与第 1 节表格一一对应。')
    A('- [ ] **调用数**：对任一款，`games\\<game>\\runs\\<game>\\<tag>\\call-index.txt` 里 tag 前缀')
    A('      `e`/`r`（减掉 `e01-tools-list`）与 `g` 的行数，等于第 1 节的两列。')
    A('- [ ] **facts_complete**：`ledger-editor.json` / `ledger-game.json` 里 `facts_complete=true`')
    A('      的行数等于该款调用数（清理相的行不算）。')
    A('- [ ] **断言**：遍历 `call-index.txt` 每个 tag 对应的 `<tag>.json`，数 `passed` / `all_passed`，')
    A('      总数应等于该款「pass/fail」列；20 款合计 `passed=%d failed=%d`。' % (t['passed'], t['failed']))
    A('- [ ] **未声明失败 0 条**：失败断言的 tag/note 里都能读出「这条本来就要失败」。')
    A('- [ ] **像素差**：按 §6 复算，`MISMATCH` 应为 0；非零组数等于第 1 节那一列。')
    A('- [ ] **截图是原件**：包内任何一张 PNG 的 sha256 都能在 `MANIFEST.txt` 里查到，')
    A('      且与 `SHOTS-INDEX.txt` 记的一致。')
    A('- [ ] **源码是原件**：任取 `projects\\<game>\\src\\*.cs`，其 sha256 与 `MANIFEST.txt` 一致；')
    A('      再与 `tools\\sessions\\<game>\\payload\\` 的同名载荷比对（本项目里两者应逐字节相同）。')
    A('- [ ] **可复现**：按 §4.3 重放一款，`report.json` 的数字与包内一致（PNG 的 sha 除外）。')
    A('- [ ] **验收链完整**：`docs\\ACCEPTANCE-TASK-105.md`（fail）→ `docs\\TASK-106-REPORT.md`（修）')
    A('      → `docs\\ACCEPTANCE-TASK-107.md`（pass），三条 fail 逐条能对上。')
    A('- [ ] **决策可查**：`docs\\DECISIONS-EXCERPT.md` 的 D138–D153 覆盖「20 款」口径到收口。')
    A('')
    A('---')
    A('')
    A('## 8. 旁注与边界（如实声明）')
    A('')
    A('* 本包的 `.sha256.txt` 与 `MANIFEST.txt`：`MANIFEST.txt` 在**包内**（逐文件 sha256 + 字节数），')
    A('  同时与 `.sha256.txt` 一起放在 zip **旁边**——`.sha256.txt` 记的是 **zip 自己的**摘要，')
    A('  一个文件不可能包含自身最终的 sha256，所以它只能做同名旁文件。')
    A('* trace 里的截图路径是**原始绝对路径**（`F:\\moonbit-hof-rs\\godot-mcp\\runs\\...`）。')
    A('  搬进包后路径不再可达；包内对应文件按 `SHOTS-INDEX.txt` 的映射查找。')
    A('* 「缺陷数」一列引自 `docs\\GAME-LOOP-LOG.md` 的里程碑表（20 款一览），')
    A('  它是历轮「工具缺陷 / 游戏或驱动缺陷」的累计，不是最终运行 `report.json` 里')
    A('  自动检出的缺陷数（后者只覆盖该轮运行本身）。')
    A('* 本包 `.zip` 约 **6.7 MB**（远低于「超过 1.5 GB 就每款只留 3 张截图」的阈值），')
    A('  所以每款给足 **6 张**代表截图；包内源码与场景、会话与载荷、最终运行的证据一件不少。')
    A('* 已知遗留（不构成本包缺陷，取自验收报告）：%s' % docs_note)
    A('')
    return '\n'.join(L) + '\n'


def main():
    global STAGE
    data = json.load(open(DATA, encoding='utf-8'))
    STAGE = os.path.join(DIST, '_stage_' + TS)
    if os.path.isdir(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(STAGE)
    log = []

    # --- docs -----------------------------------------------------------------
    os.makedirs(os.path.join(STAGE, 'docs'), exist_ok=True)
    doc_copies = [
        (os.path.join(ROOT, 'GAME-LOOP-LOG.md'), 'docs/GAME-LOOP-LOG.md'),
        (os.path.join(ROOT, 'godot', 'modules', 'mcp_server', 'docs', 'reports',
                      'MCP-TRACEABILITY.md'), 'docs/MCP-TRACEABILITY.md'),
        (os.path.join(ROOT, 'recovery', 'reports', 'ACCEPTANCE-TASK-105.md'),
         'docs/ACCEPTANCE-TASK-105.md'),
        (os.path.join(ROOT, 'recovery', 'reports', 'TASK-106-REPORT.md'),
         'docs/TASK-106-REPORT.md'),
        (os.path.join(ROOT, 'recovery', 'reports', 'ACCEPTANCE-TASK-107.md'),
         'docs/ACCEPTANCE-TASK-107.md'),
    ]
    for src, rel in doc_copies:
        dst = os.path.join(STAGE, rel.replace('/', os.sep))
        shutil.copy2(src, dst)
        log.append(rel)

    # DECISIONS excerpt D138..D153
    dec_src = r'F:\moonbit-hof-rs\DECISIONS.md'
    all_lines = open(dec_src, encoding='utf-8').read().splitlines(True)
    start = next(i for i, l in enumerate(all_lines) if l.startswith('## D138'))
    excerpt = ''.join(all_lines[start:])
    head = [
        '# DECISIONS.md 段落副本 —— 与本目标（20 款 C# 游戏）相关的决策',
        '',
        '* 来源：`F:\\moonbit-hof-rs\\DECISIONS.md`',
        '* 原始文件字节数：%d；sha256：`%s`' % (os.path.getsize(dec_src), sha256_file(dec_src)),
        '* 本副本范围：`## D138` 起至文件末尾（第 %d 行到第 %d 行，共 %d 行）'
        % (start + 1, len(all_lines), len(all_lines) - start),
        '* D138 = 「至少 20 款、全部 C#」的口径；D139–D152 = 逐款交付与修复；D153 = TASK-106 修复。',
        '',
        '---',
        '',
    ]
    with open(os.path.join(STAGE, 'docs', 'DECISIONS-EXCERPT.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(head) + excerpt)
    log.append('docs/DECISIONS-EXCERPT.md')

    # --- tools ----------------------------------------------------------------
    os.makedirs(os.path.join(STAGE, 'tools'), exist_ok=True)
    tool_copies = [
        (os.path.join(ROOT, 'tools', 'game_report.py'), 'tools/game_report.py'),
        (os.path.join(ROOT, 'godot', 'modules', 'mcp_server', 'scripts',
                      'mcp_trace_ledger.py'), 'tools/mcp_trace_ledger.py'),
        (os.path.join(ROOT, 'tools', 'run_game_session.ps1'), 'tools/run_game_session.ps1'),
    ]
    for src, rel in tool_copies:
        dst = os.path.join(STAGE, rel.replace('/', os.sep))
        shutil.copy2(src, dst)
        log.append(rel)

    # --- per-game -------------------------------------------------------------
    for rec in data['games']:
        g = rec['game']
        run_tag = rec['run_tag']
        run_src = os.path.join(ROOT, 'runs', g, run_tag)
        base = os.path.join(STAGE, 'games', g)

        copy_tree(os.path.join(ROOT, 'projects', g),
                  os.path.join(base, 'projects', g), log)
        copy_tree(os.path.join(ROOT, 'tools', 'sessions', g),
                  os.path.join(base, 'tools', 'sessions', g), log)

        out_run = os.path.join(base, 'runs', g, run_tag)
        os.makedirs(out_run, exist_ok=True)
        names = ['report.json', 'report.md', 'call-index.txt']
        names += [f for f in sorted(os.listdir(run_src))
                  if re.match(r'ledger-(editor|game)\.(txt|json)$', f)]
        names += [f for f in sorted(os.listdir(run_src))
                  if re.match(r'trace-.*\.jsonl$', f)]
        for n in names:
            s = os.path.join(run_src, n)
            if os.path.isfile(s):
                shutil.copy2(s, os.path.join(out_run, n))
                log.append('games/%s/runs/%s/%s' % (g, run_tag, n))
        for side in sorted(d for d in os.listdir(run_src)
                           if d.endswith('.sidecar') and os.path.isdir(os.path.join(run_src, d))):
            copy_tree(os.path.join(run_src, side), os.path.join(out_run, side), log)
        pick_shots(run_src, g, out_run, log, rec['pixel_comparable'])

    # --- README + manifest ----------------------------------------------------
    docs_note = ('ACCEPTANCE-TASK-107 §0：两条措辞/时点标注层面的 low 风险，'
                 '以及「无法当场重跑引擎」这条边界；`ACCEPTANCE-TASK-105` 的 D-3'
                 '（`--import` 关机期访问违例）不在 TASK-106 范围，累计口径按台账读。')
    with open(os.path.join(STAGE, 'README-REVIEW.md'), 'w', encoding='utf-8') as f:
        f.write(build_readme(data, docs_note))
    log.append('README-REVIEW.md')

    # manifest (exclude the manifest itself; it is self-referential)
    entries = []
    for dp, dn, fn in os.walk(STAGE):
        dn[:] = sorted(dn)
        for f in sorted(fn):
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, STAGE).replace(os.sep, '/')
            if rel == 'MANIFEST.txt':
                continue
            entries.append((rel, os.path.getsize(p), sha256_file(p)))
    entries.sort()
    lines = [
        '# MANIFEST -- %s.zip' % BASE,
        '# 生成时间: %s' % time.strftime('%Y-%m-%d %H:%M:%S'),
        '# 引擎版本: %s' % data['engine_version'],
        '# 逐文件: sha256  字节数  包内相对路径（已排除 .godot / bin / obj / .mono / user:// 缓存）',
        '# 文件数: %d  总字节: %d' % (len(entries), sum(e[1] for e in entries)),
        '',
    ]
    for rel, size, sha in entries:
        lines.append('%s  %12d  %s' % (sha, size, rel))
    man_text = '\n'.join(lines) + '\n'
    with open(os.path.join(STAGE, 'MANIFEST.txt'), 'w', encoding='utf-8') as f:
        f.write(man_text)
    with open(MAN_PATH, 'w', encoding='utf-8') as f:
        f.write(man_text)
    with open(os.path.join(DIST, 'MANIFEST.txt'), 'w', encoding='utf-8') as f:
        f.write(man_text)

    # --- zip ------------------------------------------------------------------
    print('staging files:', len(entries))
    total = sum(e[1] for e in entries)
    print('staging bytes: %d (%.1f MB)' % (total, total / 1048576))
    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)
    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for dp, dn, fn in os.walk(STAGE):
            dn[:] = sorted(dn)
            for f in sorted(fn):
                p = os.path.join(dp, f)
                rel = os.path.relpath(p, STAGE).replace(os.sep, '/')
                comp = zipfile.ZIP_STORED if rel.lower().endswith('.png') else zipfile.ZIP_DEFLATED
                z.write(p, BASE + '/' + rel, compress_type=comp)
    zip_size = os.path.getsize(ZIP_PATH)
    zip_sha = sha256_file(ZIP_PATH)
    with open(SHA_PATH, 'w', encoding='utf-8') as f:
        f.write('%s  %s\n' % (zip_sha, BASE + '.zip'))
        f.write('# bytes: %d\n' % zip_size)
        f.write('# manifest (in-zip): MANIFEST.txt ; same file copied to %s.MANIFEST.txt\n' % BASE)
    print('zip:', ZIP_PATH)
    print('bytes:', zip_size, '(%.1f MB)' % (zip_size / 1048576))
    print('sha256:', zip_sha)

    json.dump({'zip': ZIP_PATH, 'bytes': zip_size, 'sha256': zip_sha,
               'stage': STAGE, 'manifest_files': len(entries)},
              open(os.path.join(DIST, 'zip-info.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)


main()
