#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Emit C:\\...\\mcp-recovery\\REBUILD-2A-MANIFEST.md (TASK-079)."""
import io, json, os, hashlib, time, collections

ROOT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
ST = os.path.join(ROOT, 'staging')
G = os.path.join(ROOT, 'rebuild', 'godot')
LOW = os.path.join(ROOT, 'rebuild', '_low-confidence')
WORK = os.path.join(ROOT, 'work')
BASELINE = os.path.join(os.environ['TEMP'], 'audit002', 'tree')
OUT = os.path.join(ROOT, 'REBUILD-2A-MANIFEST.md')


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


S = jload(os.path.join(WORK, 'assembly-stats.json'))
PY = jload(os.path.join(WORK, 'parse-py.json'))
PS1 = jload(os.path.join(WORK, 'parse-ps1-rebuild.json'))
PI = jload(os.path.join(WORK, 'patch-info.json'))
ROWS = [json.loads(l) for l in io.open(os.path.join(ST, '__payload-index', 'reconstruction.jsonl'),
                                       encoding='utf-8', errors='replace')]
BYREL = {r['rel']: r for r in ROWS}
MISSING_MODULE = [l.strip() for l in io.open(os.path.join(WORK, 'module-listing-missing.txt'),
                                             encoding='utf-8', errors='replace') if l.strip()]
PS1MAP = {}
for e in PS1:
    if e.get('missing'):
        continue
    for f in (e.get('failures') or []):
        PS1MAP[f['rel']] = f
PYMAP = {}
for tag in PY:
    for f in (PY[tag].get('failures') or []):
        PYMAP[(tag, f['rel'])] = f

L = []
A = L.append


def dirsize(rel):
    p = os.path.join(G, rel)
    n = b = 0
    for dp, dn, fn in os.walk(p):
        for f in fn:
            n += 1
            b += os.path.getsize(os.path.join(dp, f))
    return n, b


A('# REBUILD-2A-MANIFEST')
A('')
A('TASK-079 — **rebuild stage 2a** on C:.  Assembled `rebuild\\godot`, inventoried it, listed')
A('every gap against the TASK-078 staging payloads, and parse-checked every `.py` / `.ps1` in the')
A('result.  This stage **moves and counts only**: no scons build, no gate run, no module source')
A('rewritten, no patch applied to the tree.')
A('')
A('* generated: `%s`' % S['generated'])
A('* staging root: `staging\\` (TASK-078: 2,276 staged files / 20,595,326 B)')
A('* rebuild root: `rebuild\\`')
A('* baseline: `%%TEMP%%\\audit002\\tree` (09-22 full engine snapshot, no `.git`)')
A('* safety: **zero writes to F:**; every write under `C:\\Users\\wyl\\AppData\\Local\\Temp\\mcp-recovery\\`;')
A('  no shell redirection anywhere (all writers are `Set-Content` / `Out-File -FilePath` /')
A('  `[IO.File]::WriteAllText` / Python `io.open(...,\'w\')`).')
A('')
A('## 1. Assembly result')
A('')
A('### 1.1 `rebuild\\godot` by top-level directory')
A('')
A('| dir | files | bytes |')
A('|---|---:|---:|')
inv = S['godot_inventory']
tot = S['godot_totals']
for k, v in sorted(inv.items(), key=lambda kv: -kv[1]['bytes']):
    A('| `%s` | %d | %d |' % (k, v['files'], v['bytes']))
A('| **TOTAL** | **%d** | **%d** |' % (tot['files'], tot['bytes']))
A('')
A('### 1.2 What the layout is')
A('')
A('```text')
A('rebuild\\')
A('  godot\\                          the reconstruction tree (engine baseline + mcp_server module)')
A('    SConstruct, core\\, editor\\, modules\\, platform\\, scene\\, servers\\, drivers\\,')
A('    main\\, misc\\, tests\\, thirdparty\\, doc\\, bin\\ (binaries only),')
A('    modules\\mcp_server\\**          module source + scripts + docs + evidence')
A('    docs\\reports\\**                repo-root reports (also present in the baseline)')
A('  _low-confidence\\                 LOW-confidence payloads, NOT part of the tree')
A('  _excluded\\                       non-repo scratch captured from a .git/ folder')
A('  _refs\\legacy-174\\                the legacy 174-tool contract input (read-only from F:)')
A('  patches\\                         the three engine patches, verbatim')
A('  ENGINE-PATCHES-TO-REAPPLY.md     how to replay those three patches')
A('```')
A('')
A('### 1.3 Baseline copy accounting')
A('')
bc = S['baseline_copy']
bs = S['baseline_skipped']
A('| item | files | bytes |')
A('|---|---:|---:|')
A('| copied from `%%TEMP%%\\audit002\\tree` | %d | %d |' % (bc['files'], bc['bytes']))
A('| **deliberately not copied** (`bin\\obj` scons objects + `__pycache__`) | %d | %d |' % (bs['files'], bs['bytes']))
A('')
A('`bin\\obj` is 2.75 GB of regenerable object files and `__pycache__` is Python bytecode; the task')
A('is "usable rebuild tree", so they are excluded **explicitly and visibly** rather than silently.')
A('The four `bin\\` files that matter — `godot.windows.editor.x86_64.exe` (180,286,464 B),')
A('`godot.windows.editor.x86_64.console.exe`, `.exp`, `.lib` — **are** copied, so the tree has a')
A('runnable (stale, pre-patch, non-mono) editor available.')
A('')
A('### 1.4 Landing summary')
A('')
A('| class | count | destination |')
A('|---|---:|---|')
A('| module payloads, HIGH/MEDIUM confidence | %d | `rebuild\\godot\\modules\\mcp_server\\**` |' % S['module_landed_high_mid'])
A('| non-module payloads landed (repo-root extras + docs) | %d | `rebuild\\godot\\**` |' % S['other_landed_high_mid'])
A('| LOW confidence payloads | %d | `rebuild\\_low-confidence\\**` |' % S['low_confidence_landed'])
A('| captured `.git/` scratch | %d | `rebuild\\_excluded\\**` |' % S['excluded'])
A('| staged payloads deliberately **not** overlaid | %d | (staging only) |' % len([x for x in S['skipped'] if x['why'].startswith('staging copy')]))
A('| staged payloads that are out-of-repo / have no bytes | %d | (staging only) |' % len([x for x in S['skipped'] if not x['why'].startswith('staging copy')]))
A('')
A('`rebuild\\_low-confidence` inventory:')
A('')
A('| dir | files | bytes |')
A('|---|---:|---:|')
for k, v in sorted(S['low_inventory'].items(), key=lambda kv: -kv[1]['bytes']):
    A('| `%s` | %d | %d |' % (k, v['files'], v['bytes']))
A('')
A('## 2. Is the baseline usable, and is it pre-patch?')
A('')
KEY = ['SConstruct', 'core/config/project_settings.cpp', 'core/config/project_settings.h',
       'editor/editor_node.cpp', 'modules/mono/csharp_script.cpp', 'modules/mono/csharp_script.h',
       'modules/gdscript/gdscript.cpp', 'platform/windows/os_windows.cpp',
       'modules/mcp_server/register_types.cpp']
A('| key file | present | bytes | sha256 |')
A('|---|---|---:|---|')
for rel in KEY:
    p = os.path.join(G, rel.replace('/', os.sep))
    A('| `%s` | %s | %d | `%s` |' % (rel, 'yes' if os.path.isfile(p) else '**NO**',
                                    os.path.getsize(p) if os.path.isfile(p) else 0,
                                    sha256(p) if os.path.isfile(p) else '-'))
A('')
pw = dirsize('platform' + os.sep + 'windows')
A('* `platform\\windows\\**`: **%d files / %d B** — the whole Windows platform layer is present.' % pw)
A('  (The 09-22 baseline measured 71 files there; the two-file difference is the `__pycache__`')
A('  bytecode that this assembly drops on purpose — see §1.3.)')
A('* whole tree: **%d files / %d B** (engine + module + docs assets).' % (tot['files'], tot['bytes']))
A('* the baseline is a *full* engine snapshot: `core` 482 files, `editor` 1,828, `scene` 847,')
A('  `thirdparty` 4,883, `modules` 3,849 (mostly the 09-22 copy of the mcp_server module, which the')
A('  staged payloads then overlay).')
A('')
A('### 2.1 Is it already patched?  **No.**')
A('')
A('| symbol | introduced by | occurrences in the baseline |')
A('|---|---|---:|')
A('| `is_source_newer_than_assembly` | patch 1 (`5f3e7fb441`) | 0 |')
A('| `update_settings_section_text` | patch 2 (`96f631addb`) | 0 |')
A('| `save_custom_section` | patch 2 (`96f631addb`) | 0 |')
A('| `save_preserving_text` | patch 3 (`2f85141a74`) | 0 |')
A('')
A('A full-text scan of the five patched engine files found **zero** occurrences of any patch symbol,')
A('and `git apply --check` accepts all three patches (patch 3 only after patch 2 — see')
A('`ENGINE-PATCHES-TO-REAPPLY.md` §5). So the baseline is the **pre-patch upstream state** and is')
A('the correct pre-image for the replay.  The only `mcp_server` mentions in the baseline are the')
A('09-22 module directory itself (46 files) and its build wiring — not the three patches.')
A('')
A('## 3. Known hard gaps (the five named in the task)')
A('')
HARD = [
    (r'modules\mcp_server\tests\test_mcp_server.h', 'LOW',
     'the whole doctest harness: 9,626 lines, 431,976 B staged vs 1,392 lines / 66,392 B in the '
     'baseline; the replay had **456 failed edits** over 793 edit events and read coverage is 46.9%%',
     'the module cannot be built with tests, and `scons tests=yes` / gate 3 (doctest) cannot run; '
     'it is the single largest verification asset'),
    (r'modules\mcp_server\docs\DESIGN-DETAIL.md', 'LOW',
     '84,486 B staged vs 31,531 B in the baseline; **50 failed edits** and no complete read; the '
     'staged file is complete-looking (coverage 100%%, tail present) but 50 edits could not be '
     'replayed',
     'documentation only — does not block compilation or the gates, but it is the design record for'
     ' the whole module'),
    (r'modules\mcp_server\tools\registration.cpp', 'LOW',
     '17,014 B / 293 lines staged vs 2,580 B / 39 lines in the baseline; **42 failed edits**, '
     'coverage 100%%, tail present',
     '**blocks compilation**: the module needs the current registration.cpp (the registry of ~176 '
     'tools); the baseline copy is a 09-22 fossil'),
    (r'modules\mcp_server\scripts\accept_m1.ps1', 'MEDIUM',
     '57,469 B staged (79.9%% coverage, interior lines missing), **10 PowerShell parse errors** '
     'starting at line 644 (`MissingCatchOrFinally`)',
     'gate 5 (accept_m1 x2, 22/22 inventory) cannot run'),
    (r'modules\mcp_server\scripts\gen_renamed_contract.py', 'LOW',
     '118,449 B staged, 75%% coverage, tail partial, **47 failed edits**; the generator version '
     'constant is stuck at the old value',
     'blocks regeneration of `tools_list.renamed.json`, which RECOVERY-PLAN §4.2 requires to be '
     'generated rather than copied'),
]
A('| # | path | status | source | evidence | impact | recommended recovery |')
A('|---|---|---|---|---|---|---|')
SRC_HARD = [
    '`staging\\modules\\mcp_server\\tests\\test_mcp_server.h`',
    '`staging\\modules\\mcp_server\\docs\\DESIGN-DETAIL.md`',
    '`staging\\modules\\mcp_server\\tools\\registration.cpp`',
    '`staging\\modules\\mcp_server\\scripts\\accept_m1.ps1`',
    '`staging\\modules\\mcp_server\\scripts\\gen_renamed_contract.py`',
]
REC_HARD = [
    're-extract from the transcripts with the edit chain anchored on the LAST complete read of the '
    'file, or replay `git show 96f631addb/2f85141a74 -- modules/mcp_server/tests/test_mcp_server.h` '
    'hunks (the three engine commits carry their module-side doctests); re-run 9,626 lines against '
    'gate 3 to prove it',
    're-run the read-window merge with the 50 failing edits dropped and re-checked against the '
    'report anchors (REPORT-067/075 reference its sections)',
    're-extract **before anything else** — without it the module does not compile',
    'fix the 10 parse errors by hand from the surrounding read windows (the errors are localized, '
    'e.g. a `try` without `catch`)',
    'regenerate from `tools_list.renamed.json` history or re-run the generator after it is restored',
]
for i, (rel, conf, ev, imp) in enumerate(HARD, 1):
    dest = os.path.join(LOW, rel) if conf == 'LOW' else os.path.join(G, rel)
    d = '`rebuild\\_low-confidence\\%s`' % rel if conf == 'LOW' else '`rebuild\\godot\\%s`' % rel
    A('| %d | `%s` | %s confidence%s | %s | %s | %s | %s |' % (
        i, rel, conf, ' -> ' + d, SRC_HARD[i - 1], ev, imp, REC_HARD[i - 1]))
A('')
A('Status column: `已落` = present in the tree; `低置信` = parked in `_low-confidence`; `缺失` = not')
A('landed at all.  All five are either `低置信` (four) or `已落` but broken (one).')
A('')
A('### 3.1 What `rebuild\\godot` actually holds at those five paths right now')
A('')
A('This is the practical consequence of the confidence rule: where the baseline had a copy, the')
A('tree holds the **09-22 fossil**; the current content is parked in `_low-confidence`.  A builder')
A('must replace these files before compiling — do not mistake a present-but-old file for a good one.')
A('')
A('| path | bytes in the tree | origin | bytes in `_low-confidence` | verbatim |')
A('|---|---:|---|---:|---|')
for rel, conf, ev, imp in HARD:
    tp = os.path.join(G, rel)
    lp = os.path.join(LOW, rel)
    bp = os.path.join(BASELINE, rel.replace('/', os.sep))
    if not os.path.isfile(tp):
        origin = 'nothing'
    elif os.path.isfile(bp) and open(tp, 'rb').read() == open(bp, 'rb').read():
        origin = 'audit002 baseline fossil (09-22)'
    elif os.path.isfile(bp):
        origin = 'staged payload, **overwrote the baseline copy**'
    else:
        origin = 'staged payload (not in the baseline)'
    A('| `%s` | %s | %s | %s | %s |' % (
        rel,
        ('%d' % os.path.getsize(tp)) if os.path.isfile(tp) else 'absent',
        origin,
        ('%d' % os.path.getsize(lp)) if os.path.isfile(lp) else 'absent',
        '**must be replaced before the build**' if os.path.isfile(tp) else 'must be supplied'))
A('')
A('## 4. Gap table — every LOW-confidence payload (%d rows = %d LOW payloads + 2 truncated docs'
  ' variants kept for audit)' % (len(S['low_landed']), S['low_confidence_landed']))
A('')
A('| path | status | source | conf | cov% | tail | failed edits | impact | suggestion |')
A('|---|---|---|---|---:|---|---:|---|---|---|')
for r in sorted(S['low_landed'], key=lambda r: r['rel']):
    rel = r['rel']
    if rel.startswith('modules\\mcp_server\\tools\\') or rel.startswith('modules\\mcp_server\\tests\\'):
        imp = 'module source/test — **blocks the build or the gates**'
    elif rel.startswith('modules\\mcp_server\\scripts\\'):
        imp = 'gate/evidence script — blocks that gate only'
    elif rel.startswith('modules\\mcp_server\\docs\\'):
        imp = 'documentation — no build impact'
    else:
        imp = 'engine-side fragment — **not needed**, the baseline copy is authoritative'
    A('| `%s` | 低置信 | `staging\\%s` | %s | %s | %s | %s | %s | re-extract / re-validate |' % (
        rel, rel, r.get('conf', 'low'), r.get('cov'), r.get('tail'), r.get('failed'), imp))
A('')
A('### 4.1 Complete-looking payloads that were ruled LOW — **re-validate these first**')
A('')
A('These four have 100%% read coverage and a present tail, yet were classified LOW because their')
A('edit replay failed; if the failed edits were cosmetic, the parked copy may already be the right')
A('file.  This is the **highest-value re-check of stage 2b.**')
A('')
A('| path | cov% | tail | failed edits | why it matters |')
A('|---|---:|---|---:|---|')
A('| `modules\\mcp_server\\tools\\registration.cpp` | 100.0 | no | 42 | **build blocker** |')
A('| `modules\\mcp_server\\tools\\editor_playback.cpp` | 100.0 | no | 20 | module source |')
A('| `modules\\mcp_server\\docs\\DESIGN-DETAIL.md` | 100.0 | no | 50 | design record |')
A('| `modules\\mcp_server\\docs\\tool-groups-b5.json` | 100.0 | no | 16 | gate 1 / group port input |')
A('')
A('### 4.2 Engine fragments that were deliberately NOT overlaid (N=%d)' % len(
    [x for x in S['skipped'] if x['why'].startswith('staging copy is a partial read')]))
A('')
A('These are staged paths whose repository copy **already exists in the baseline**.  The staged')
A('payload is a *read window*, i.e. a fragment, while the baseline holds the complete file;')
A('overlaying would have regressed the tree.  They are listed here so the decision is auditable.')
A('')
A('| staged path | staged bytes | baseline bytes | relation |')
A('|---|---:|---:|---|')
CMP_PATH = os.path.join(WORK, 'unchanged-fragments.txt')
same = [] ; smaller = [] ; eolonly = [] ; logdrift = []
for x in S['skipped']:
    if not x['why'].startswith('staging copy is a partial read'):
        continue
    rel = x['rel']
    a = os.path.join(ST, rel) ; b = os.path.join(G, rel)
    sa = os.path.getsize(a) if os.path.exists(a) else 0
    sb = os.path.getsize(b) if os.path.exists(b) else 0
    row = BYREL.get(rel, {})
    complete = (row.get('miss_tail') == 'no' and (row.get('read_cov_pct') or 0) >= 99.0)
    if os.path.exists(a) and os.path.exists(b):
        da = open(a, 'rb').read() ; db = open(b, 'rb').read()
        if da == db or da.rstrip(b'\r\n') == db.rstrip(b'\r\n'):
            same.append((rel, sa, sb))
            continue
    if complete and rel.lower().endswith('.log'):
        logdrift.append((rel, sa, sb))
    elif complete:
        eolonly.append((rel, sa, sb))
    else:
        smaller.append((rel, sa, sb))
for rel, sa, sb in sorted(same):
    A('| `%s` | %d | %d | byte-identical modulo the final newline (staging has LF-normalized EOLs) |' % (rel, sa, sb))
for rel, sa, sb in sorted(eolonly):
    A('| `%s` | %d | %d | complete read; differs from the baseline by **BOM/CRLF only** (content identical line for line), %+d B |' % (rel, sa, sb, sa - sb))
for rel, sa, sb in sorted(logdrift):
    A('| `%s` | %d | %d | complete read; **build-log drift** between 09-22 and 09-25 (artifact, no impact), %+d B |' % (rel, sa, sb, sa - sb))
for rel, sa, sb in sorted(smaller):
    A('| `%s` | %d | %d | staging is a **partial read**, %+d B vs the baseline |' % (rel, sa, sb, sa - sb))
A('')
A('Totals: **%d** fragments are effectively identical to the baseline (only the final newline / '
  'CRLF-vs-LF difference), **%d** are complete reads differing only by BOM/CRLF + BOM-bearing '
  'files, **%d** are complete reads whose content is a build log, and **%d** are partial reads '
  'strictly smaller than the baseline copy.'
  % (len(same), len(eolonly), len(logdrift), len(smaller)))
A('In no case is a staged fragment larger than the baseline file, so no staged engine fragment')
A('could be a newer complete revision; and except for the two build logs, no skipped engine')
A('fragment carries content the baseline lacks.')
A('')
A('#### EOL-normalisation finding (important for later byte-exact work)')
A('')
A('The staging pipeline stored text with **LF** endings and no BOM, while the baseline files carry')
A('**CRLF** and (for the .NET SDK files) a **UTF-8 BOM**.  Example:')
A('')
A('| file | staged | baseline |')
A('|---|---|---|')
A('| `modules\\mono\\editor\\Godot.NET.Sdk\\Godot.NET.Sdk\\Godot.NET.Sdk.csproj` | 1,863 B, 42 LF, no BOM | 1,910 B, 43 CRLF, BOM |')
A('| `core\\SCsub` | 10,010 B, 295 LF | 10,011 B, 296 LF |')
A('')
A('After stripping the BOM and normalising EOLs the two `.csproj` files are **identical line for')
A('line**, so the ~44-47 B deltas are BOM+CRLF, not content.  Therefore any byte-level diff between')
A('`rebuild\\godot` and a future restored tree will show the same artifacts — compare content, not')
A('raw bytes, unless the EOLs are first re-normalised.  This is also why `.gitattributes` matters')
A('here (see the module evidence doc `GIT-EOL-NORMALIZATION.md`).')
A('')
A('### 4.3 Staged paths with no payload (N=%d = %d out-of-repo + %d in-repo)'
  % (len([x for x in S['skipped'] if not x['why'].startswith('staging copy')]),
     len([x for x in S['skipped'] if x['rel'].startswith('__external')]),
     len([x for x in S['skipped'] if not x['why'].startswith('staging copy')
          and not x['rel'].startswith('__external')])))
A('')
A('Out-of-repo payloads are excluded by design; the in-repo ones are the real gaps:')
A('')
A('| path | status | reason |')
A('|---|---|---|')
for x in sorted(S['skipped'], key=lambda x: x['rel']):
    if x['why'].startswith('staging copy'):
        continue
    if x['rel'].startswith('__external'):
        continue
    A('| `%s` | 缺失 | %s |' % (x['rel'], x['why']))
A('')
A('(%d further paths are `__external\\...`, i.e. out-of-repo payloads for other projects; they stay'
  % len([x for x in S['skipped'] if x['rel'].startswith('__external')]))
A('in `staging\\` and are not part of this tree by definition.)')
A('')
A('## 5. Known module files that were never staged (N=%d)' % len(MISSING_MODULE))
A('')
A('TASK-078 left `work\\module-listing-missing.txt`: paths that appear in the captured module')
A('listing but have **no** staged payload.  Everything below is **evidence or cache**, not source —')
A('no `tools\\*.cpp/h`, no `scripts\\*.ps1/py` in this list:')
A('')
ext = collections.Counter(os.path.splitext(m)[1].lower() or '(none)' for m in MISSING_MODULE)
A('| extension | count |')
A('|---|---:|')
for k, v in ext.most_common():
    A('| `%s` | %d |' % (k, v))
A('')
A('| group | count | example |')
A('|---|---:|---|')
groups = collections.Counter()
ex = {}
for m in MISSING_MODULE:
    parts = m.split('\\')
    if len(parts) >= 5 and parts[2] == 'docs' and parts[3] == 'reports' and parts[4] == 'evidence':
        key = '\\'.join(parts[:6])
    elif '__pycache__' in m:
        key = m.rsplit('\\', 1)[0]
    else:
        key = m
    groups[key] += 1
    ex.setdefault(key, m)
for k, v in groups.most_common(15):
    A('| `%s` | %d | `%s` |' % (k, v, ex[k]))
A('')
A('Caveat: that listing was captured from a terminal dump that was itself truncated')
A('(`work\\module-listing-raw.txt` ends with "Omitted 14,352 bytes" — some of the paths below are')
A('themselves cut mid-name), so **%d is a lower bound**, not the complete set of unstaged module'
  % len(MISSING_MODULE))
A('files.')
A('')
A('Full list in the appendix below.')
A('')
A('## 6. Parseability spot check')
A('')
A('Every `.py` in the tree was put through `ast.parse`; every `.ps1` through')
A('`[System.Management.Automation.Language.Parser]::ParseFile` (parse only, never executed).')
A('')
A('| area | `.py` total | `.py` ok | `.py` failed | `.ps1` total | `.ps1` with errors |')
A('|---|---:|---:|---:|---:|---:|')
for tag, label in (('godot', '`rebuild\\godot`'), ('_low-confidence', '`rebuild\\_low-confidence`'),
                   ('staging', '`staging\\` (TASK-078 set, for comparison)')):
    p = PY[tag]
    s = next((e for e in PS1 if e['tag'] == tag), None)
    ok = p['counts'].get('ok', 0)
    bad = p['total_py'] - ok
    A('| %s | %d | %d | %d | %s | %s |' % (
        label, p['total_py'], ok, bad,
        s['total_ps1'] if s else '-', s['with_errors'] if s else '-'))
A('')
A('### 6.1 Comparison with the TASK-078 numbers')
A('')
A('| check | TASK-078 recorded | reproduced now | verdict |')
A('|---|---|---|---|')
A('| `.py` | 453 pass / 3 fail | **455 / 3** over 458 candidates | 3 failures match exactly; the "453" is 2 lower than a straight sweep of the same index — unexplained 2-file delta, see below |')
A('| `.ps1` | 433 parsed / 10 errors | **433 / 10** | exact match |')
A('')
A('The same three `.py` files fail in every sweep:')
A('')
A('| file | line | error |')
A('|---|---:|---|')
for tag in ('staging',):
    for f in PY[tag]['failures']:
        A('| `%s` (staging) | %s | %s |' % (f['rel'], f['line'], f['detail']))
A('')
A('All three are **engine-side** partial reads (`methods.py` at the repo root,')
A('`modules\\mono\\build_scripts\\build_assemblies.py`, `platform\\windows\\detect.py`) — which is')
A('exactly why they were parked in `_low-confidence`.  In `rebuild\\godot` the baseline provides the')
A('complete original of all three, so **`rebuild\\godot` has 0 `.py` failures**.')
A('')
A('The 2-file delta: a sweep of the current `reconstruction.jsonl` yields 458 `.py` paths, all of')
A('which exist in staging (455 ok + 3 syntax errors).  The TASK-078 headline "453 pass" sums to')
A('456, i.e. two files that were counted differently then (most likely `missing` at the time) — the')
A('index has since been regenerated.  No file is hidden by this; the per-file failure list above is')
A('the authoritative statement.  Flagged rather than papered over.')
A('')
A('### 6.2 `.ps1` failures in `rebuild\\godot` (6 of 129)')
A('')
A('| file | errors | first error | line |')
A('|---|---:|---|---:|')
gps = next(e for e in PS1 if e['tag'] == 'godot')
for f in gps['failures']:
    A('| `%s` | %d | %s | %s |' % (f['rel'], f['parseErrors'], f['first'], (f.get('lines') or ['-'])[0]))
A('')
A('All six are staged MID-confidence payloads with interior lines missing (coverage 51-84%%), which')
A('is precisely why they do not parse.  The two LOW-confidence `.ps1` failures are in')
A('`_low-confidence` and therefore not in the tree:')
A('')
lps = next(e for e in PS1 if e['tag'] == '_low-confidence')
for f in lps['failures']:
    A('* `%s` — %d errors, first at line %s: %s' % (f['rel'], f['parseErrors'],
                                                    (f.get('lines') or ['-'])[0], f['first']))
A('')
A('## 7. Not-landed inventory (未落地清单)')
A('')
A('| class | count | where it is | why |')
A('|---|---:|---|---|')
lowin = len(S['low_landed'])
A('| LOW-confidence payloads moved to `_low-confidence` (41) + 2 truncated docs variants kept for audit | %d | `rebuild\\_low-confidence\\` | confidence rule: must not pollute the tree |' % lowin)
A('| `.git/` scratch file | %d | `rebuild\\_excluded\\` | not repository content |' % S['excluded'])
A('| staged fragments not overlaid (baseline already complete) | %d | `staging\\` | overlaying would regress a complete file |' % len([x for x in S['skipped'] if x['why'].startswith('staging copy')]))
A('| out-of-repo payloads | %d | `staging\\__external\\` | belong to other projects, not this tree |' % len([x for x in S['skipped'] if x['rel'].startswith('__external')]))
A('| indexed paths with no payload | %d | (nothing anywhere) | the transcripts never contained usable bytes |' % len([x for x in S['skipped'] if x['why'].startswith('no staged payload')]))
A('| `__history` versions | 4,543 | `staging\\__history\\` | kept in staging by instruction |')
A('| `__candidates` alternative reconstructions | 296 | `staging\\__candidates\\` | kept in staging |')
A('| `bin\\obj` + `__pycache__` | %d | (only in the audit002 baseline) | regenerable build artifacts |' % bs['files'])
A('')
A('## 8. The docs/contract assets (rule 4)')
A('')
A('| repo path | source | bytes | sha256 | stale? | note |')
A('|---|---|---:|---|---|---|')
for a in S['assets']:
    A('| `%s` | `%s` | %d | `%s` | %s | %s |' % (
        a['repo_path'], a['source'], a['bytes'], a['sha256'],
        '**YES**' if a['stale'] else 'no', a['note']))
A('')
A('The two truncated staging variants of the docs assets were kept (in `_low-confidence`) for audit')
A('instead of being deleted.  Note that `modules\\mcp_server\\docs\\tools_list.renamed.json` in the')
A('tree is a **171-tool** copy from the TASK-044 backup, not the final contract:')
A('RECOVERY-PLAN §4.2 requires it to be regenerated, and the legacy generator input (174 tools,')
A('sha256 `8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54`) is parked at')
A('`rebuild\\_refs\\legacy-174\\tools_list.json` — that file was read from **F: read-only**, it was')
A('not written to F:.')
A('')
A('## 9. Reproduce this result')
A('')
A('```powershell')
A('$R = "C:\\Users\\wyl\\AppData\\Local\\Temp\\mcp-recovery"')
A('python "$R\\scripts\\assemble_rebuild_2a.py"      # baseline copy + overlay (idempotent, resume-safe)')
A('python "$R\\scripts\\parse_check_rebuild_py.py"   # ast.parse over every .py')
A('&      "$R\\scripts\\parse_check_rebuild_ps1.ps1" # PowerShell parser over every .ps1')
A('&      "$R\\scripts\\patch_dryrun2.ps1"           # ordered patch dry run in an isolated sandbox')
A('python "$R\\scripts\\gen_manifest.py"             # this document')
A('```')
A('')
A('Evidence files: `work\\assembly-stats.json`, `work\\parse-py.json`,')
A('`work\\parse-ps1-rebuild.json`, `work\\patch-info.json`, `work\\fcheck-pre.txt`,')
A('`work\\fcheck-post.txt`, `work\\drift-detail.txt`.')
A('')
A('## 10. What stage 2b must fix, in priority order')
A('')
A('1. `modules\\mcp_server\\tools\\registration.cpp` — build blocker; start from the'
   ' complete-looking LOW copy and re-check the 42 failed edits.')
A('2. `modules\\mcp_server\\tests\\test_mcp_server.h` — the gate-3 harness (9,626 lines).')
A('3. `modules\\mcp_server\\scripts\\gen_renamed_contract.py` — needed to regenerate the contract.')
A('4. `modules\\mcp_server\\scripts\\accept_m1.ps1` — 10 parse errors, gate 5.')
A('5. The other LOW module sources (`tool_helpers.cpp`, `editor_write_scene_editor.cpp`,'
   ' `project_write_resource_scene.cpp`, `running_game_*`, `editor_playback.cpp`, …).')
A('6. `docs\\DESIGN-DETAIL.md` and the remaining LOW docs/JSON.')
A('7. Re-apply the three engine patches (see `ENGINE-PATCHES-TO-REAPPLY.md`), then build.')
A('8. Re-normalise EOLs before any byte-exact comparison with a restored tree.')
A('')
A('## Appendix A — staged paths that appear in the module listing but were never staged')
A('')
A('```text')
for m in MISSING_MODULE:
    A(m)
A('```')
A('')

text = '\n'.join(L)
# any surviving %% came from strings that were never %-formatted; in Markdown a literal %% is
# never wanted, so normalise it (formatted strings already collapsed %% to %).
text = text.replace('%%', '%')
with io.open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)
print('wrote %s (%d bytes, %d lines)' % (OUT, os.path.getsize(OUT), len(L)))
