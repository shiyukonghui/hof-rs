import io, json, os, sys, re

ROOT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
DIFF = os.path.join(ROOT, 'staging', '__payload-index', 'events-diff.jsonl')
OUT = os.path.join(ROOT, 'work', 'patch-events-scan.txt')
HASHES = ['96f631addb', '2f85141a74', '5f3e7fb441']

os.makedirs(os.path.dirname(OUT), exist_ok=True)
rows = []
with io.open(DIFF, encoding='utf-8', errors='replace') as f:
    for ln, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        cmd = d.get('cmd') or ''
        out = d.get('out') or ''
        hit = [h for h in HASHES if h in cmd or h in out]
        if hit:
            rows.append({
                'ln': ln,
                'f': d.get('f'),
                'seq': d.get('seq'),
                'time': d.get('time'),
                'cmd': cmd,
                'outlen': len(out),
                'diffgit': out.count('diff --git'),
                'hunks': out.count('@@ '),
                'hashes': hit,
                'out_head': out[:400],
            })

rows.sort(key=lambda r: (r['time'] or '', r['ln']))
with io.open(OUT, 'w', encoding='utf-8') as f:
    f.write('total matching diff events: %d\n\n' % len(rows))
    for r in rows:
        f.write('=' * 100 + '\n')
        f.write('ln=%s f=%s seq=%s time=%s outlen=%s diffgit=%s hunks=%s hashes=%s\n' % (
            r['ln'], r['f'], r['seq'], r['time'], r['outlen'], r['diffgit'], r['hunks'], r['hashes']))
        f.write('CMD: ' + (r['cmd'] or '')[:1000] + '\n')
        f.write('OUT_HEAD:\n' + r['out_head'] + '\n')

print('rows', len(rows))
print('with diffgit>0 and hunks>0:',
      sum(1 for r in rows if r['diffgit'] > 0 and r['hunks'] > 0))
print('wrote', OUT)
