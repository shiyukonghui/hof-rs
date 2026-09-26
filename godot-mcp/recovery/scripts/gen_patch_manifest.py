#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Emit rebuild\\ENGINE-PATCHES-TO-REAPPLY.md from work\\patch-info.json."""
import io, json, os, time

ROOT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
WORK = os.path.join(ROOT, 'work')
OUT = os.path.join(ROOT, 'rebuild', 'ENGINE-PATCHES-TO-REAPPLY.md')

info = json.load(io.open(os.path.join(WORK, 'patch-info.json'), encoding='utf-8'))
ev = info['post_replay_evidence']

PURPOSE = {
    1: """The engine never had a C# compile verdict: `CSharpScript::reload()` returns OK
unconditionally and only looks the type up in the assembly that was already built, so the
module's validation tools had to answer `unverifiable` for every `.cs` file.  The patch adds
**one public read-only accessor**, `CSharpScript::is_source_newer_than_assembly()`, which lifts
the mtime comparison that `_update_exports()` already performs.  It changes **no** signature and
**no** existing semantics (`reload()` is byte-identical).""",
    2: """`ProjectSettings::save_custom()` / `_save_settings_text()` can only rewrite the whole
file, so the module had to do text surgery on `project.godot` (nine recorded risks, R1-R9).  The
patch adds a **section-scoped write path**: `update_settings_section_text()` serialises exactly
one section through the *same* `VariantWriter` the full writer uses, and `save_custom_section()`
writes it back while copying every other byte through — comments, key order, BOM
(re-added `EF BB BF`), and CRLF are preserved verbatim.  Pure addition, `+483/-0`, no existing
behaviour touched; ClassDB binding included.""",
    3: """`editor/editor_node.cpp` calls `ProjectSettings::save()` on editor open (the
`!cmdline_mode` branch that `--import` and `--headless` never reach).  That is the whole-file
writer, which regenerated `project.godot` and deleted every hand-written comment.  The patch adds
`ProjectSettings::save_preserving_text()` (publishing section by section through patch 2's
`update_settings_section_text()`) and repoints that one call site at it.  `save()`,
`save_custom()` and `save_custom_section()` keep their observable behaviour; the collection and
the two I/O halves of `save_custom_section()` are **extracted, not rewritten**.""",
}

DEP = {
    1: 'none — applies to the pristine baseline',
    2: 'none in the strict sense (its context does not need patch 1) — but the historical order is 1 -> 2 -> 3',
    3: '**REQUIRES patch 2** — its `project_settings.cpp` hunk context contains `save_custom_section()`, which patch 2 introduces. Applied to a pristine baseline it fails with `patch does not apply` (see §5).',
}

lines = []
A = lines.append
A('# ENGINE-PATCHES-TO-REAPPLY')
A('')
A('TASK-079 (rebuild stage 2a) — the three engine-fork patches that lived in the deleted tree,')
A('parked as **verbatim `git show` output** plus everything needed to replay them.  No patch was')
A('applied to `rebuild\\godot` in this stage: the applicability evidence in §5 comes from isolated')
A('sandboxes under `work\\patchdry\\` and `work\\patchdry2\\`.')
A('')
A('* generated: `%s`' % info['generated'])
A('* patch artifacts: `rebuild\\patches\\*.diff` (verbatim copies, sha256 below)')
A('* baseline: `%%TEMP%%\\audit002\\tree` (09-22 full engine snapshot, no `.git`), copied to `rebuild\\godot`')
A('* source of the diff text: `%%TEMP%%\\audit-engine\\diff-patch{1,2,3}.txt`, written on 2026-09-25 by the')
A('  TASK-069/070 audit of `git show <commit>`; these are the **STDOUT bytes of the real command**,')
A('  not a reconstruction.  The text is also captured in the session transcripts')
A('  (`staging\\__payload-index\\events-diff.jsonl`).')
A('')
A('## 1. Baseline identity (what the patches must be applied to)')
A('')
A('`rebuild\\godot` inherits the audit002 baseline.  The five patched engine files are **pristine**')
A('there — a symbol scan found **zero** occurrences of any patch symbol, so the baseline is the')
A('pre-patch upstream state and the replay starts from a clean pre-image:')
A('')
A('| file | baseline bytes | baseline sha256 | is_source_newer_than_assembly | update_settings_section_text | save_custom_section | save_preserving_text |')
A('|---|---|---|---|---|---|---|')
for rel, e in ev.items():
    A('| `%s` | %d | `%s` | 0 | 0 | 0 | 0 |' % (rel, e['baseline_bytes'], e['baseline_sha256']))
A('')
A('## 2. Order, commands, expected result')
A('')
A('Apply **strictly in order 1 -> 2 -> 3**, from the repository root (`rebuild\\godot`), with `-p1`:')
A('')
A('```powershell')
A('$G = "C:\\Users\\wyl\\AppData\\Local\\Temp\\mcp-recovery\\rebuild\\godot"')
A('$P = "C:\\Users\\wyl\\AppData\\Local\\Temp\\mcp-recovery\\rebuild\\patches"')
A('foreach ($n in 1,2,3) {')
A('  $f = Get-ChildItem $P -Filter ("patch" + $n + "-*.diff") | Select-Object -First 1')
A('  git -C $G apply -p1 --whitespace=nowarn $f.FullName')
A('  if ($LASTEXITCODE -ne 0) { throw ("patch " + $n + " failed: " + $f.Name) }')
A('}')
A('```')
A('')
A('Dry-run first (`--check`) if you want a no-write rehearsal; the same command with `--check`')
A('was used to produce §5.')
A('')
A('## 3. Patch table')
A('')
A('| # | commit | subject | artifact | bytes | sha256 | files | hunks | +/- |')
A('|---|---|---|---|---|---|---|---|---|')
SUBJ = {
    1: 'mcp_server: TASK-055 - a real C# compile verdict (D112 engine patch + recorded build diagnostics)',
    2: 'mcp_server: TASK-057 three closures and engine patch 2 (ProjectSettings section publish)',
    3: 'mcp_server: TASK-067 list the build\'s script languages, and publish project.godot by section on editor open',
}
for p in info['patches']:
    nh = sum(len(f['hunks']) for f in p['files'])
    A('| %d | `%s` | %s | `%s` | %d | `%s` | %d | %d | +%d/-%d |' % (
        p['id'], p['commit'], SUBJ[p['id']], p['file'], p['bytes'], p['sha256'],
        len(p['files']), nh, p['added_lines'], p['removed_lines']))
A('')
A('New symbols, as *occurrences on added lines* of each diff:')
A('')
for p in info['patches']:
    A('* **patch %d**: %s' % (p['id'], ', '.join(
        '`%s` x%d' % (k, v) for k, v in p['symbol_occurrences_added'].items())))
A('')
A('## 4. The patches, verbatim')
A('')
for p in info['patches']:
    A('### 4.%d patch %d — `%s`' % (p['id'], p['id'], p['commit']))
    A('')
    A('**%s**' % p['title'])
    A('')
    A('* files touched: %s' % ', '.join('`%s` (%d hunks)' % (f['path'], len(f['hunks'])) for f in p['files']))
    A('* hunk headers:')
    for f in p['files']:
        for h in f['hunks']:
            A('  * `%s`  %s' % (f['path'], h))
    A('* dependency: %s' % DEP[p['id']])
    A('')
    A('**Why it exists / contract.**')
    A('')
    A('```text')
    A(PURPOSE[p['id']])
    A('```')
    A('')
    A('**Raw `git show` output (contains the commit message and the full hunks with their')
    A('pre-image context; this is the applicable text).**')
    A('')
    A('```diff')
    raw = io.open(os.path.join(ROOT, p['file']), encoding='utf-8', errors='replace').read()
    A(raw.rstrip('\n'))
    A('```')
    A('')
A('## 5. Applicability evidence (isolated sandbox, `rebuild\\godot` NOT modified)')
A('')
A('Every run below used a sandbox holding copies of the five engine files taken from')
A('`rebuild\\godot`, so the tree itself is untouched.')
A('')
A('| # | command | sandbox | exit | meaning |')
A('|---|---|---|---|---|')
A('| 1 | `git apply --check patch1` on pristine | `work\\patchdry` | **0** | patch 1 applies to the baseline as-is |')
A('| 2 | `git apply --check patch2` on pristine | `work\\patchdry` | **0** | patch 2 applies to the baseline as-is |')
A('| 3 | `git apply --check patch3` on pristine | `work\\patchdry` | **1** | *expected*: context needs `save_custom_section()` from patch 2 |')
A('| 4 | `git apply patch2` then `git apply --check patch3` | `work\\patchdry` | 0 / **0** | patch 3 applies once patch 2 is in |')
A('| 5 | `git apply patch1; patch2; patch3` in order | `work\\patchdry2` | **0 / 0 / 0** | the whole replay is clean end to end |')
A('')
A('The only failure text (row 3) is git searching for the patch-2 pre-image:')
A('')
A('```text')
A('error: while searching for:')
A('    return OK;')
A('}')
A('')
A('Error ProjectSettings::save_custom_section(const String &p_path, const String &p_section, const CustomMap &p_custom) {')
A('...')
A('error: patch failed: core/config/project_settings.cpp:1679')
A('error: core/config/project_settings.cpp: patch does not apply')
A('```')
A('')
A('Per-file state across the ordered replay in `work\\patchdry2` (bytes / lines / sha256):')
A('')
A('| file | pristine | after patch1 | after patch2 | after patch3 |')
A('|---|---|---|---|---|')
STATE = {
    'core/config/project_settings.cpp': [
        '75556 / 1628 / `c76f85acfb214ddadf16cd08742eec5c73a20d6753843bcb33f5e552f745886c`',
        '75556 / 1628 / `c76f85acfb214ddadf16cd08742eec5c73a20d6753843bcb33f5e552f745886c`',
        '95158 / 2027 / `daeb00777088b36cacf747bfb8d16b3ce4150bce9840314abef3e4ddfa1a3b04`',
        '102533 / 2178 / `e9c4f6fb143afcdd63939574e0067a4aff929ff47d2893b996da218415d05f68`'],
    'core/config/project_settings.h': [
        '13295 / 238 / `1e4e7d6e24b559f6c27e6f6b02f21de68967bea0c226d25f4f6680a660a2d994`',
        '13295 / 238 / `1e4e7d6e24b559f6c27e6f6b02f21de68967bea0c226d25f4f6680a660a2d994`',
        '16043 / 272 / `9680b051cdb862a8b895bca3cf0228163390e9c32207279a2cfdd4e9c2d1daa1`',
        '19002 / 314 / `b8491ca81d1a8f8cdb986325812948e74406904614a0503704184452e19b7d79`'],
    'editor/editor_node.cpp': [
        '389353 / 8343 / `8110094827f6d7da6209ad2e1c7f371f96f63307255300630b78803c70cd2321`',
        '389353 / 8343 / `8110094827f6d7da6209ad2e1c7f371f96f63307255300630b78803c70cd2321`',
        '389353 / 8343 / `8110094827f6d7da6209ad2e1c7f371f96f63307255300630b78803c70cd2321`',
        '400247 / 8361 / `699bfc817f99ce25cd45678cb3213dea203b49e1a85c4f4f54f7d1b597647ec8`'],
    'modules/mono/csharp_script.cpp': [
        '86199 / 2228 / `842199675aa4775830508b10d209bde494edd66786114776627548d41177d0db`',
        '89504 / 2242 / `7fef858f8f51a177390f1a878591a4567943ce2b78965b599e47b04b85975eb8`',
        '89504 / 2242 / `7fef858f8f51a177390f1a878591a4567943ce2b78965b599e47b04b85975eb8`',
        '89504 / 2242 / `7fef858f8f51a177390f1a878591a4567943ce2b78965b599e47b04b85975eb8`'],
    'modules/mono/csharp_script.h': [
        '20978 / 451 / `41fe4bdf644b6cdf1621d18ffcecb6deaa8447225764909e233630a5553cc5cd`',
        '22687 / 470 / `499bdbc4e2e8340125bc88e79065826da5753ee07da7070bf4ba58952ae16f0b`',
        '22687 / 470 / `499bdbc4e2e8340125bc88e79065826da5753ee07da7070bf4ba58952ae16f0b`',
        '22687 / 470 / `499bdbc4e2e8340125bc88e79065826da5753ee07da7070bf4ba58952ae16f0b`'],
}
for f, st in STATE.items():
    A('| `%s` | %s | %s | %s | %s |' % (f, st[0], st[1], st[2], st[3]))
A('')
A('## 6. Post-replay acceptance check')
A('')
A('After the three patches are applied, these symbols must be present (checked on the patched')
A('sandbox; the counts are plain substring counts):')
A('')
A('| file | is_source_newer_than_assembly | update_settings_section_text | save_custom_section | save_preserving_text |')
A('|---|---|---|---|---|')
for rel, e in ev.items():
    c = e.get('symbol_counts', {})
    A('| `%s` | %d | %d | %d | %d |' % (
        rel, c.get('is_source_newer_than_assembly', 0), c.get('update_settings_section_text', 0),
        c.get('save_custom_section', 0), c.get('save_preserving_text', 0)))
A('')
A('And the sha256 of the five files must equal the "after patch3" column of §5.')
A('')
A('## 7. What else the next stage needs')
A('')
A('* The patches do **not** touch `modules/mcp_server/**`; the module side of patch 1 and patch 3')
A('  (e.g. `tools/csharp_verdict.{h,cpp}`, `tools/project_read_files.cpp`, the doctests in')
A('  `tests/test_mcp_server.h`) is *inside the module tree* and is still a **gap** — see')
A('  `REBUILD-2A-MANIFEST.md` §gap table.')
A('* `editor_node.cpp` in the baseline is 389,353 B / 8,343 lines; `git apply` matched its hunk')
A('  exactly, so the baseline revision is compatible with the patch as recorded.')
A('* Hand-written `project.godot` comment preservation (patch 2/3 behaviour) can only be observed')
A('  with a **windowed** editor run (`-e --path <proj>`, no `--headless`); byte equality alone')
A('  cannot distinguish "wrote but unchanged" from "never wrote" — compare **mtime** as well.')
A('* No compilation (`scons`) was attempted in this stage.')
A('')
A('## 8. Provenance summary')
A('')
A('| item | value |')
A('|---|---|')
A('| diff text command 1 | `git show 5f3e7fb441 -- modules/mono/csharp_script.cpp modules/mono/csharp_script.h` |')
A('| diff text command 2 | `git show 96f631addb -- core/config/project_settings.cpp core/config/project_settings.h` |')
A('| diff text command 3 | `git show 2f85141a74 -- core/config/project_settings.cpp core/config/project_settings.h editor/editor_node.cpp` |')
A('| captured stdout | `%TEMP%\\audit-engine\\diff-patch{1,2,3}.txt` (2026-09-25 16:06-16:07) |')
A('| transcript cross-reference | `staging\\__payload-index\\events-diff.jsonl` rows for the same commands |')
A('| decision log cross-reference | `F:\\moonbit-hof-rs\\DECISIONS.md` D113 (patch 1), D115 (patch 2), D125 (patch 3) |')
A('| F: writes | none |')
A('')

with io.open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines))
print('wrote %s (%d bytes)' % (OUT, os.path.getsize(OUT)))
