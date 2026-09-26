# TASK-078 reconciliation: answer section 2.5 (1)-(4) from PAYLOADS ONLY (no narrative).
import json, os, re, collections, ast, glob

ROOT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
W = os.path.join(ROOT, 'work')
ST = os.path.join(ROOT, 'staging')
T = os.path.join(ROOT, 'transcripts')

def load(kind):
    with open(os.path.join(W, 'events-%s.jsonl' % kind), 'r', encoding='utf-8') as f:
        for line in f:
            try:
                yield json.loads(line)
            except Exception:
                pass

recs = {r['rel'].lower().replace('\\', '/'): r for r in (json.loads(l) for l in open(os.path.join(W, 'reconstruction.jsonl'), encoding='utf-8'))}
def rec(suf):
    for k, v in recs.items():
        if k.endswith(suf.lower().replace('\\', '/')):
            return v
    return None

print('=' * 78)
print('Q1  tools_list.renamed.json - last generation + _meta.count / added_count')
print('=' * 78)
gen = [json.loads(l) for l in open(os.path.join(W, 'gen-runs.jsonl'), encoding='utf-8')]
runs = [g for g in gen if re.search(r'gen_renamed_contract\.py\s*(\||$|>)', g['cmd']) and 'git ' not in g['cmd']]
runs.sort(key=lambda g: (g['time'] or 0, g['seq'] or 0))
print('captured generator-run commands: %d (last 6)' % len(runs))
for g in runs[-6:]:
    print('  t=%s seq=%s outlen=%d  %s' % (g['time'], g['seq'], len(g['out']), g['cmd'].replace('\n', ' ')[:150]))

print()
print('-- payload evidence of _meta values (read windows of tools_list.renamed.json) --')
hits = collections.Counter()
samples = []
for e in load('read'):
    if not (e.get('path') or '').lower().endswith('tools_list.renamed.json'):
        continue
    for n, t in e.get('lines') or []:
        s = t if isinstance(t, str) else ''
        if re.search(r'"(count|added_count|generator_version|overrides)"', s):
            hits[s.strip()] += 1
            if len(samples) < 25:
                samples.append((e['time'], e['seq'], n, s.strip()))
for s in samples:
    print('  t=%s seq=%s line=%s  %s' % s)

print()
print('-- payload evidence in captured command output --')
for g in gen:
    out = g['out'] or ''
    for m in re.finditer(r'(?i)(_meta[^\n]{0,80}|added_count[^\n]{0,60}|\bcount[ =:]+1[0-9][0-9]\b[^\n]{0,40}|generator_version[^\n]{0,40})', out):
        s = m.group(1).strip()
        if re.search(r'17[0-9]|added_count|generator_version', s):
            samples.append((g['time'], g['seq'], 'cmd-out', s[:120]))
seen = set()
for t, s2, n, s in samples:
    k = s[:80]
    if n == 'cmd-out':
        if k in seen:
            continue
        seen.add(k)
        print('  t=%s seq=%s %s  %s' % (t, s2, n, s))

print()
print('-- staged reconstruction --')
r = rec('docs/tools_list.renamed.json')
print('  conf=%s bytes=%s tail=%s cov=%s%% n_read=%s' % (r['conf'], r['bytes'], r['miss_tail'], r['read_cov_pct'], r['n_read']))
p = os.path.join(ST, r['rel'])
txt = open(p, encoding='utf-8').read()
i = txt.find('"count"')
print('  staged has _meta?', '_meta' in txt, '| count occurrences:', txt.count('"count"'), '| added_count:', txt.count('"added_count"'))
print('  staged first 200 chars:', repr(txt[:200]))

print()
print('=' * 78)
print('Q2  gen_renamed_contract.py - final version recoverable?')
print('=' * 78)
r = rec('scripts/gen_renamed_contract.py')
p = os.path.join(ST, r['rel'])
src = open(p, encoding='utf-8').read()
print('  staged: conf=%s bytes=%s chosen=%s' % (r['conf'], r['bytes'], r['chosen']))
for pat in ('ADDED_TOOLS', 'ADDED_VERB_EXTENSIONS', 'GENERATOR_VERSION = "1.22.0"', 'GENERATOR_VERSION = "1.21.0"',
            'project_read_text_file', 'SCENE_TREE_ADDRESSABILITY_SENTENCE', 'TILEMAP_ATLAS_GAP_SENTENCE'):
    print('    %-42s count=%d' % (pat, src.count(pat)))
print('  notes:', '; '.join(r['notes'])[:300])
print('  version-bump edits recorded:')
bumps = []
for e in load('edit'):
    if not (e.get('path') or '').lower().endswith('gen_renamed_contract.py'):
        continue
    o = e.get('old') or ''
    n = e.get('new') or ''
    mo = re.search(r'GENERATOR_VERSION\s*=\s*"([^"]+)"', o)
    mn = re.search(r'GENERATOR_VERSION\s*=\s*"([^"]+)"', n)
    if mo and mn:
        bumps.append((e['time'], e['seq'], mo.group(1), mn.group(1)))
bumps.sort()
print('    recorded bumps = %d : %s -> %s' % (len(bumps), bumps[0][2], bumps[-1][3]))
print('    last bump:', bumps[-1])
missing = []
have = set(b[2] for b in bumps) | set(b[3] for b in bumps)
for a, b in zip([b[3] for b in bumps], [b[2] for b in bumps][1:]):
    pass
seqv = sorted(set([b[2] for b in bumps] + [b[3] for b in bumps]), key=lambda s: [int(x) for x in s.split('.')])
gaps = []
for x, y in zip(seqv, seqv[1:]):
    xi = [int(v) for v in x.split('.')]
    yi = [int(v) for v in y.split('.')]
    if yi[0] * 100 + yi[1] - (xi[0] * 100 + xi[1]) > 1:
        gaps.append('%s -> %s' % (x, y))
print('    version gaps in the recorded chain:', gaps)

print()
print('=' * 78)
print('Q3  engine patch change points - locatable from diff-class / edit payloads?')
print('=' * 78)
SYM = {
 'core/config/project_settings.cpp': ['save_custom_section', 'save_preserving_text', 'publish_settings_sections_text',
                                      '_collect_settings_for_save', 'update_settings_section_text', 'PROJECT_SETTINGS.html'],
 'core/config/project_settings.h': ['save_custom_section', 'save_preserving_text', 'publish_settings_sections_text'],
 'editor/editor_node.cpp': ['save_preserving_text'],
 'modules/mono/csharp_script.cpp': ['is_source_newer_than_assembly'],
 'modules/mono/csharp_script.h': ['is_source_newer_than_assembly'],
}
for f, syms in SYM.items():
    rr = rec(f)
    print('--', f, '(staged conf=%s bytes=%s cov=%s%%)' % (rr['conf'], rr['bytes'], rr['read_cov_pct']))
    ed = [e for e in load('edit') if (e.get('path') or '').lower().replace('\\', '/').endswith(f.lower())]
    print('   edit payloads: %d' % len(ed))
    for e in sorted(ed, key=lambda x: (x['time'], x['seq'])):
        blob = (e.get('old') or '') + '||' + (e.get('new') or '')
        tag = [s for s in syms if s in blob]
        first = re.sub(r'\s+', ' ', (e.get('new') or ''))[:110]
        print('     t=%s seq=%s sym=%s NEW~ %s' % (e['time'], e['seq'], ','.join(tag) if tag else '-', first))
    hits = []
    for e in load('diff'):
        o = e.get('out') or ''
        if any(s in o for s in syms):
            hits.append((e['time'], e['seq'], e['cmd'][:90]))
    print('   diff payloads mentioning the symbols: %d' % len(hits))
    for h in sorted(hits)[:6]:
        print('     t=%s seq=%s %s' % h)

print()
print('=' * 78)
print('Q4  the six tool scripts')
print('=' * 78)
for suf, checker in (('check_engine_anchor.ps1', 'ANCHOR'), ('mcp_evidence_guard.ps1', ''),
                     ('mcp_watch_run.ps1', ''), ('check_exit_propagation.py', ''),
                     ('check_tautologies.py', ''), ('check_hardcoded_counts.py', '')):
    rr = rec(suf)
    p = os.path.join(ST, rr['rel'])
    d = open(p, encoding='utf-8').read() if os.path.exists(p) else ''
    extra = ''
    if suf.endswith('.py'):
        try:
            ast.parse(d)
            extra = 'py=ok'
        except Exception as ex:
            extra = 'py=FAIL(%s)' % ex
    else:
        extra = 'ps1 parse errors=%s' % rr.get('ps1_parse_errors', '?')
    print('  %-28s conf=%-4s bytes=%-7s tail=%-12s chosen=%-12s %s' % (suf, rr['conf'], rr['bytes'], rr['miss_tail'], rr['chosen'], extra))
    print('     markers: %s' % ', '.join('%s=%d' % (m, d.count(m)) for m in
          ([x for x in ('ANCHOR_EQUAL', 'ANCHOR', 'git', 'sha256') if m],) [0]) if False else '')
    ms = ['def ', 'class '] if suf.endswith('.py') else ['function ', 'param(']
    print('     size/lines: %d lines; %s' % (d.count('\n') + 1, '; '.join('%s=%d' % (m, d.count(m)) for m in ms)))
