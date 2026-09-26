# TASK-078 probe 5: recover the generator/inspection run outputs for tools_list.renamed.json
# READ-ONLY over transcripts; writes work\gen-runs.jsonl
import json, glob, os, re

ROOT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
T = os.path.join(ROOT, 'transcripts')
W = os.path.join(ROOT, 'work')

PATS = re.compile(r'gen_renamed_contract|tools_list\.renamed\.json|added_count|_meta\.count|MCP_GENERATOR_VERSION', re.I)

def texts(dat):
    out = []
    for c in (dat.get('message') or {}).get('content') or []:
        if c.get('type') == 'tool-result':
            for cc in c.get('content') or []:
                if cc.get('type') == 'text':
                    out.append(cc.get('text') or '')
    return '\n'.join(out)

rows = []
for f in sorted(glob.glob(os.path.join(T, '*.jsonl'))):
    calls = {}
    with open(f, 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get('type') == 'tool/call':
                dat = d.get('data') or {}
                calls[dat.get('callId')] = dat
            elif d.get('type') == 'tool/result':
                dat = d.get('data') or {}
                cid = ((dat.get('message') or {}).get('source') or {}).get('callId')
                c = calls.get(cid)
                if not c:
                    continue
                if c.get('name') not in ('term', 'terminal', 'bash'):
                    continue
                try:
                    a = json.loads(c.get('arguments') or '{}')
                except Exception:
                    a = {}
                cmd = a.get('command') or ''
                if not PATS.search(cmd):
                    continue
                txt = texts(dat)
                rows.append({'time': d.get('time'), 'seq': d.get('seq'), 'f': os.path.basename(f),
                             'cmd': cmd, 'out': txt})

rows.sort(key=lambda r: (r['time'] or 0, r['seq'] or 0))
with open(os.path.join(W, 'gen-runs.jsonl'), 'w', encoding='utf-8', newline='\n') as g:
    for r in rows:
        g.write(json.dumps(r, ensure_ascii=False) + '\n')
print('rows =', len(rows))
print('time range:', rows[0]['time'], '->', rows[-1]['time'])
for r in rows[-8:]:
    print('--- t=%s seq=%s %s ---' % (r['time'], r['seq'], r['f']))
    print('CMD:', r['cmd'].replace('\n', ' ')[:220])
    print('OUT:', r['out'].replace('\r', '').replace('\n', ' | ')[:600])
