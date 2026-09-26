# TASK-078 probe 3: CRLF handling in read payloads + tools_list.renamed.json read evidence.
import json, os, collections

W = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work'

def load(kind):
    with open(os.path.join(W, 'events-%s.jsonl' % kind), 'r', encoding='utf-8') as f:
        for line in f:
            try:
                yield json.loads(line)
            except Exception:
                pass

cr = collections.Counter()
n = 0
for e in load('read'):
    n += 1
    lines = e.get('lines') or []
    hascr = sum(1 for l in lines if isinstance(l[1], str) and l[1].endswith('\r'))
    cr['cr_lines' if hascr else 'no_cr'] += 1
    if hascr and cr['cr_lines'] <= 2:
        print('CR sample', e['path'], 'lines with CR =', hascr, '/', len(lines))
    if n > 2000:
        break
print('sampled', n, dict(cr))

print('--- reads of tools_list.renamed.json ---')
evs = [e for e in load('read') if (e.get('path') or '').lower().endswith('tools_list.renamed.json')]
print('count =', len(evs))
evs.sort(key=lambda e: (e['time'], e['seq']))
for e in evs:
    cov = [l[0] for l in e['lines']]
    print('%d seq=%s off=%s total=%s lines=%d cov=%s..%s' % (e['time'], e['seq'], e.get('offset'), e.get('totalLines'), len(cov), min(cov), max(cov)))
last = evs[-1]
txt = '\n'.join(l[1] for l in last['lines'])
print('--- last read around _meta ---')
i = txt.find('"_meta"')
print(txt[i:i+700] if i >= 0 else txt[:500])
