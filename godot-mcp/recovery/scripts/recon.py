# TASK-078 recon: enumerate tool names / shapes across all decompressed transcripts.
# READ-ONLY over transcripts/ ; writes nothing.
import json, glob, os, collections, sys

T = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\transcripts'
fs = sorted(glob.glob(os.path.join(T, '*.jsonl')))
names = collections.Counter()
shapes = collections.Counter()
argkeys = collections.defaultdict(collections.Counter)
sessions = []
nrec = 0
for f in fs:
    with open(f, 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            if not line.strip():
                continue
            nrec += 1
            try:
                d = json.loads(line)
            except Exception:
                names['<UNPARSEABLE>'] += 1
                continue
            t = d.get('type')
            if t == 'session':
                sessions.append((os.path.basename(f), d.get('id'), d.get('origin'), d.get('cwd'), d.get('createdAt')))
            elif t == 'tool/call':
                nm = d['data'].get('name')
                names[nm] += 1
                try:
                    a = json.loads(d['data'].get('arguments') or '{}')
                    for k in a:
                        argkeys[nm][k] += 1
                except Exception:
                    argkeys[nm]['<BADARGS>'] += 1
            elif t == 'tool/result':
                m = d['data'].get('meta') or {}
                shapes[str(m.get('shape'))] += 1

print('files=%d records=%d sessions=%d' % (len(fs), nrec, len(sessions)))
print('--- tool names ---')
for k, v in names.most_common(200):
    print('%7d  %s' % (v, k))
print('--- result meta.shapes ---')
for k, v in shapes.most_common(50):
    print('%7d  %s' % (v, k))
print('--- arg keys per tool ---')
for nm in sorted(argkeys):
    print(nm, dict(argkeys[nm].most_common(12)))
print('--- cwd values ---')
for c, v in collections.Counter(s[3] for s in sessions).most_common(20):
    print('%5d %s' % (v, c))
