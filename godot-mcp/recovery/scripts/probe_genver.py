# TASK-078 probe 6: GENERATOR_VERSION edits + read coverage for gen_renamed_contract.py
import json, os, re

W = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work'

def load(kind):
    with open(os.path.join(W, 'events-%s.jsonl' % kind), 'r', encoding='utf-8') as f:
        for line in f:
            try:
                yield json.loads(line)
            except Exception:
                pass

print('=== edits touching GENERATOR_VERSION ===')
for e in load('edit'):
    if 'GENERATOR_VERSION' in (e.get('old') or '') + (e.get('new') or ''):
        p = (e.get('path') or '')
        if p.lower().endswith('gen_renamed_contract.py'):
            print('t=%s seq=%s' % (e['time'], e['seq']))
            print('  OLD:', (e.get('old') or '')[:200].replace('\n', ' | '))
            print('  NEW:', (e.get('new') or '')[:200].replace('\n', ' | '))

print()
print('=== read coverage gen_renamed_contract.py ===')
best = {}
total = 0
reads = 0
for e in load('read'):
    if not (e.get('path') or '').lower().endswith('gen_renamed_contract.py'):
        continue
    reads += 1
    total = max(total, e.get('totalLines') or 0)
    for n, t in e.get('lines') or []:
        if n not in best:
            best[n] = t
print('reads=%d totalLines=%d covered=%d (%.1f%%)' % (reads, total, len(best), 100.0 * len(best) / max(total, 1)))

print()
print('=== grep transcripts for GENERATOR_VERSION literals in term output ===')
for e in load('termdump'):
    out = e.get('out') or ''
    for m in re.finditer(r'GENERATOR_VERSION\s*=\s*"([^"]+)"', out):
        print('t=%s seq=%s -> %s' % (e['time'], e['seq'], m.group(1)))
