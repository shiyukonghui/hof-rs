# TASK-078 probe 8: compare a captured module tree listing against the staged recovery set.
import json, glob, os, re, collections

ROOT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
T = os.path.join(ROOT, 'transcripts')
W = os.path.join(ROOT, 'work')
ST = os.path.join(ROOT, 'staging')

def texts(dat):
    out = []
    for c in (dat.get('message') or {}).get('content') or []:
        if c.get('type') == 'tool-result':
            for cc in c.get('content') or []:
                if cc.get('type') == 'text':
                    out.append(cc.get('text') or '')
    return '\n'.join(out)

WANT = 1790248800206
found = None
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
                calls[dat.get('callId')] = (dat, d.get('time'), d.get('seq'))
            elif d.get('type') == 'tool/result':
                dat = d.get('data') or {}
                if d.get('time') != WANT:
                    continue
                found = (os.path.basename(f), d.get('time'), d.get('seq'), texts(dat), None)
                # also collect every module listing output (relative paths)
    if found:
        break

print('found listing event:', found[0] if found else None, found[1] if found else None, found[2] if found else None)
if found:
    out = found[3]
    paths = set()
    for m in re.finditer(r'modules[\\/]mcp_server[\\/][^\s"\']+', out):
        p = m.group(0).replace('/', '\\')
        paths.add(p.lower())
    print('distinct modules\\mcp_server paths in the listing: %d' % len(paths))
    recs = [json.loads(l) for l in open(os.path.join(W, 'reconstruction.jsonl'), encoding='utf-8')]
    staged = set(r['rel'].lower() for r in recs if r['rel'].lower().startswith('modules\\mcp_server'))
    print('staged modules\\mcp_server paths: %d' % len(staged))
    missing = sorted(p for p in paths if p not in staged)
    print('in listing but NOT staged: %d' % len(missing))
    for p in missing[:40]:
        print('   -', p)
    with open(os.path.join(W, 'module-listing-missing.txt'), 'w', encoding='utf-8', newline='\n') as g:
        g.write('\n'.join(missing))
