# TASK-078 probe 7: find captured tree listings (git ls-files / recursive dir listings) to measure payload coverage.
import json, glob, os, re, collections

ROOT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
T = os.path.join(ROOT, 'transcripts')
W = os.path.join(ROOT, 'work')

def texts(dat):
    out = []
    for c in (dat.get('message') or {}).get('content') or []:
        if c.get('type') == 'tool-result':
            for cc in c.get('content') or []:
                if cc.get('type') == 'text':
                    out.append(cc.get('text') or '')
    return '\n'.join(out)

RE_LISTING = re.compile(r'git\s+ls-files|git\s+ls-tree|--name-only|dir\s+/b|Get-ChildItem[^\n]*-Recurse|find\s+/c|/s\s+/b', re.I)
best = []
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
                if not c or c.get('name') not in ('term', 'terminal', 'bash'):
                    continue
                try:
                    a = json.loads(c.get('arguments') or '{}')
                except Exception:
                    a = {}
                cmd = a.get('command') or ''
                if not RE_LISTING.search(cmd):
                    continue
                out = texts(dat)
                n = out.count('\n')
                if n > 40:
                    best.append((n, d.get('time'), d.get('seq'), os.path.basename(f), cmd[:160], out))

best.sort(reverse=True)
print('captured listing commands with >40 lines: %d' % len(best))
for b in best[:8]:
    print('lines=%d t=%s seq=%s %s' % (b[0], b[1], b[2], b[4].replace('\n', ' ')[:120]))

if best:
    n, t, s, fn, cmd, out = best[0]
    with open(os.path.join(W, 'tree-listing.txt'), 'w', encoding='utf-8', newline='\n') as g:
        g.write('source=%s seq=%s time=%s\ncommand:\n%s\n\n--- output ---\n' % (fn, s, t, cmd))
        g.write(out)
    print('wrote work/tree-listing.txt (%d lines)' % n)
    # try to count module files mentioned
    mods = set(re.findall(r'^[\s\d:]*((?:modules/mcp_server|modules\\mcp_server)\S*)', out, re.M))
    print('module-looking entries in that listing: %d' % len(mods))
