# TASK-078 probe 4: read coverage for hot files + last generator runs of tools_list.renamed.json
import json, os, re, collections

W = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work'

def load(kind):
    with open(os.path.join(W, 'events-%s.jsonl' % kind), 'r', encoding='utf-8') as f:
        for line in f:
            try:
                yield json.loads(line)
            except Exception:
                pass

WANT = ['test_mcp_server.h', 'project_settings.cpp', 'project_settings.h', 'editor_node.cpp',
        'csharp_script.cpp', 'csharp_script.h', 'registration.cpp', 'DESIGN-DETAIL.md',
        'tool_helpers.cpp', 'accept_m1.ps1']
cov = collections.defaultdict(lambda: {'lines': set(), 'total': 0, 'reads': 0, 'conflicts': 0})
for e in load('read'):
    p = (e.get('path') or '').lower()
    for w in WANT:
        if p.endswith(w):
            d = cov[w]
            d['reads'] += 1
            d['total'] = max(d['total'], e.get('totalLines') or 0)
            for n, t in e.get('lines') or []:
                d['lines'].add(n)
print('=== read coverage (union of line numbers) ===')
for w in WANT:
    d = cov[w]
    if not d['reads']:
        print('%-24s no reads' % w)
        continue
    tot = d['total'] or max(d['lines'])
    print('%-24s totalLines=%-6d covered=%-6d (%5.1f%%) reads=%d' % (w, tot, len(d['lines']), 100.0 * len(d['lines']) / tot, d['reads']))

print()
print('=== term/termfile commands mentioning gen_renamed_contract.py ===')
hits = []
for kind in ('diff', 'termfile', 'termdump', 'termlog'):
    for e in load(kind):
        c = e.get('cmd') or ''
        if 'gen_renamed_contract' in c:
            hits.append((e['time'], e['seq'], e['f'], kind, len(e.get('out') or ''), c[:200]))
hits.sort()
print('total =', len(hits))
for h in hits[-25:]:
    print('%d seq=%s %-9s outlen=%-7d %s' % (h[0], h[1], h[3], h[4], h[5].replace('\n', ' ')[:160]))
