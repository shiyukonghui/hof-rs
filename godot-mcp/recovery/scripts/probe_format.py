# TASK-078 probe: inspect read/write/edit/term result text formats. READ-ONLY.
import json, glob, os, re

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

shown = {'read': 0, 'write': 0, 'edit': 0, 'term': 0, 'readarr': 0}
calls = {}
for f in fs[:8]:
    with open(f, 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get('type') == 'tool/call':
                calls[d['data']['callId']] = (d['data'].get('name'), d['data'].get('arguments'), d.get('seq'))
            elif d.get('type') == 'tool/result':
                cid = d['data'].get('message', {}).get('source', {}).get('callId')
                if cid not in calls:
                    continue
                nm, args, seq = calls[cid]
                txt = result_text(d['data']['message'])
                if nm == 'read' and shown['read'] < 3:
                    shown['read'] += 1
                    print('=== READ args=%s ===' % args[:200])
                    print(repr(txt[:400]))
                    print('...TAIL...', repr(txt[-300:]))
                    print('META', json.dumps(d['data'].get('meta'))[:300])
                if nm == 'write' and shown['write'] < 2:
                    shown['write'] += 1
                    print('=== WRITE args=%s ===' % args[:160])
                    print(repr(txt[:300]))
                if nm == 'edit' and shown['edit'] < 2:
                    shown['edit'] += 1
                    print('=== EDIT args=%s ===' % args[:300])
                    print(repr(txt[:300]))
                if nm == 'term' and shown['term'] < 3:
                    shown['term'] += 1
                    print('=== TERM args=%s ===' % args[:300])
                    print(repr(txt[:300]))
                    print('META', json.dumps(d['data'].get('meta'))[:300])
