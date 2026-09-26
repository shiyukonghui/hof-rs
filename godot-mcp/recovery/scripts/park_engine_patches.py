#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TASK-079 step 3: park the three engine patches under rebuild\\patches and emit
rebuild\\ENGINE-PATCHES-TO-REAPPLY.md (self-contained, verbatim hunks + evidence)."""
import io, json, os, re, hashlib, time

ROOT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
TEMP = os.environ['TEMP']
AE = os.path.join(TEMP, 'audit-engine')
PAT = os.path.join(ROOT, 'rebuild', 'patches')
G = os.path.join(ROOT, 'rebuild', 'godot')
SB = os.path.join(ROOT, 'work', 'patchdry2')
WORK = os.path.join(ROOT, 'work')

PATCHES = [
    dict(id=1, short='5f3e7fb441', src=os.path.join(AE, 'diff-patch1.txt'),
         name='patch1-csharp-compile-verdict-5f3e7fb441.diff',
         title='C# compile verdict — CSharpScript::is_source_newer_than_assembly()'),
    dict(id=2, short='96f631addb', src=os.path.join(AE, 'diff-patch2.txt'),
         name='patch2-projectsettings-section-publish-96f631addb.diff',
         title='ProjectSettings section publish — update_settings_section_text() + save_custom_section()'),
    dict(id=3, short='2f85141a74', src=os.path.join(AE, 'diff-patch3.txt'),
         name='patch3-save-preserving-text-2f85141a74.diff',
         title='save_preserving_text() + the editor-open call site (project_settings.cpp/.h, editor_node.cpp)'),
]

SYMBOLS = {
    1: ['is_source_newer_than_assembly'],
    2: ['update_settings_section_text', 'save_custom_section', '_save_custom_section_bnd',
        'save_custom_section'],
    3: ['save_preserving_text'],
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def guard(p):
    ap = os.path.abspath(p)
    assert ap.startswith(ROOT + '\\'), ap
    return ap


os.makedirs(PAT, exist_ok=True)
info = {'patches': [], 'generated': time.strftime('%Y-%m-%d %H:%M:%S')}

for p in PATCHES:
    raw = io.open(p['src'], encoding='utf-8', errors='replace').read()
    dst = os.path.join(PAT, p['name'])
    guard(dst)
    with io.open(dst, 'w', encoding='utf-8', newline='\n') as f:
        f.write(raw)
    files = []
    cur = None
    for line in raw.splitlines():
        m = re.match(r'^diff --git a/(\S+) b/(\S+)$', line)
        if m:
            cur = {'path': m.group(2), 'hunks': []}
            files.append(cur)
            continue
        if cur is not None and line.startswith('@@'):
            cur['hunks'].append(line)
    added = [l[1:] for l in raw.splitlines() if l.startswith('+') and not l.startswith('+++')]
    removed = [l[1:] for l in raw.splitlines() if l.startswith('-') and not l.startswith('---')]
    ins = {}
    for s in SYMBOLS[p['id']]:
        ins[s] = sum(1 for l in added if s in l)
    conn = '\n'.join(raw.splitlines()[:16])
    info['patches'].append({
        'id': p['id'], 'commit': p['short'], 'title': p['title'],
        'file': os.path.relpath(dst, ROOT), 'bytes': os.path.getsize(dst),
        'sha256': sha256(dst), 'files': files, 'added_lines': len(added),
        'removed_lines': len(removed), 'symbol_occurrences_added': ins,
        'header': conn,
    })
    print('patch%d -> %s (%d B, files=%d, +%d/-%d)' % (
        p['id'], os.path.relpath(dst, ROOT), os.path.getsize(dst), len(files),
        len(added), len(removed)))

with io.open(os.path.join(WORK, 'patch-info.json'), 'w', encoding='utf-8') as f:
    f.write(json.dumps(info, ensure_ascii=False, indent=1))

# ---- post-replay symbol + hash evidence over the sandbox ----
FILES = ['core/config/project_settings.cpp', 'core/config/project_settings.h',
         'editor/editor_node.cpp', 'modules/mono/csharp_script.cpp',
         'modules/mono/csharp_script.h']
ev = {}
for rel in FILES:
    a = os.path.join(G, rel.replace('/', os.sep))
    b = os.path.join(SB, rel.replace('/', os.sep))
    e = {'baseline_bytes': os.path.getsize(a), 'baseline_sha256': sha256(a)}
    if os.path.exists(b):
        e['patched_bytes'] = os.path.getsize(b)
        e['patched_sha256'] = sha256(b)
        txt = io.open(b, encoding='utf-8', errors='replace').read()
        e['symbols_present'] = {s: (s in txt) for s in
                                ['is_source_newer_than_assembly',
                                 'update_settings_section_text',
                                 'save_custom_section',
                                 'save_preserving_text']}
        e['symbol_counts'] = {s: txt.count(s) for s in
                              ['is_source_newer_than_assembly',
                               'update_settings_section_text',
                               'save_custom_section',
                               'save_preserving_text']}
    ev[rel] = e
info['post_replay_evidence'] = ev
with io.open(os.path.join(WORK, 'patch-info.json'), 'w', encoding='utf-8') as f:
    f.write(json.dumps(info, ensure_ascii=False, indent=1))
print('post-replay evidence:')
for k, v in ev.items():
    print('  %-42s %s' % (k, v.get('symbols_present')))
print('wrote ' + os.path.join(WORK, 'patch-info.json'))
