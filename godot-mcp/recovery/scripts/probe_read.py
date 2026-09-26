# TASK-078 probe 2: partial-read tails, truncation markers, path/type variants. READ-ONLY.
import json, glob, os, collections

T = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\transcripts'
fs = sorted(glob.glob(os.path.join(T, '*.jsonl')))

def result_text(msg):
    out = []
    for c in msg.get('content') or []:
        if c.get('type') == 'tool-result':
            for cc in c.get('content') or []:
                if cc.get('type') == 'text':
                    out.append(cc.get('text') or '')
    return '\n'.join(out)

tails = collections.Counter()
types = collections.Counter()
metakeys = collections.Counter()
shown = 0
for f in fs[:20]:
    calls = {}
    with open(f, 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get('type') == 'tool/call':
                calls[d['data']['callId']] = (d['data'].get('name'), d['data'].get('arguments'))
            elif d.get('type') == 'tool/result':
                cid = d['data'].get('message', {}).get('source', {}).get('callId')
                if cid not in calls:
                    continue
                nm, args = calls[cid]
                if nm != 'read':
                    continue
                txt = result_text(d['data']['message'])
                m = d['data'].get('meta') or {}
                metakeys[tuple(sorted(m.keys()))] += 1
                import re
                for pat in ('End of file - total', 'Showing lines', 'truncated', 'lines of'):
                    if pat in txt:
                        idx = txt.find(pat)
                        tails[txt[max(0, idx-40):idx+80].replace('\n', '\\n')[:140]] += 1
                mm = re.search(r'<type>([^<]*)</type>', txt)
                types[mm.group(1) if mm else '<none>'] += 1
                if m.get('offset', 1) and m.get('offset') != 1 and shown < 3:
                    shown += 1
                    print('OFFSET READ', args[:160])
                    print('  meta', json.dumps({k: m[k] for k in m if k != 'lines'})[:250])
                    print('  tail', repr(txt[-400:]))
print('--- meta key sets ---')
for k, v in metakeys.most_common(10):
    print(v, k)
print('--- type tags ---')
for k, v in types.most_common(10):
    print(v, k)
print('--- tails ---')
for k, v in tails.most_common(15):
    print(v, repr(k))
