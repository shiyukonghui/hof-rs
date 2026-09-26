# TASK-078 pass 1: spool file-payload events out of the decompressed session transcripts.
# READ-ONLY on transcripts/ ; writes ONLY under C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\
# No shell redirection, no destructive command.
import json, glob, os, re, sys

ROOT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
T = os.path.join(ROOT, 'transcripts')
W = os.path.join(ROOT, 'work')
os.makedirs(W, exist_ok=True)

KINDS = ('write', 'edit', 'read', 'diff', 'termfile', 'termdump', 'termlog', 'misc')
fh = {k: open(os.path.join(W, 'events-%s.jsonl' % k), 'w', encoding='utf-8', newline='\n') for k in KINDS}
cnt = dict((k, 0) for k in KINDS)

RE_GIT = re.compile(r'\bgit\b[^\n]*\b(diff|show|status|log|stash|cat-file|rev-parse|ls-files)\b', re.I)
RE_WRITEY = re.compile(r'Set-Content|Out-File|Add-Content|WriteAllText|WriteAllBytes|New-Item[^\n]*-ItemType\s+File'
                       r'|open\([^)]*[\'"][wa]b?[\'"]\)|Copy-Item|Move-Item|>\s*[\w\\/.:-]+\.\w+', re.I)
RE_DUMPY = re.compile(r'\b(Get-Content|gc)\b|\btype\s+[A-Za-z]:\\|\bcat\s+[A-Za-z]:\\|\bhead\s+-|\btail\s+-', re.I)
RE_DIFFOUT = re.compile(r'^diff --git |^\+\+\+ b/|^@@ ', re.M)

def emit(kind, obj):
    fh[kind].write(json.dumps(obj, ensure_ascii=False) + '\n')
    cnt[kind] += 1

def texts_and_meta(dat):
    msg = dat.get('message') or {}
    out = []
    for c in msg.get('content') or []:
        if c.get('type') == 'tool-result':
            for cc in c.get('content') or []:
                if cc.get('type') == 'text':
                    out.append(cc.get('text') or '')
    return '\n'.join(out), (dat.get('meta') or {})

def main():
    fs = sorted(glob.glob(os.path.join(T, '*.jsonl')))
    nfiles = 0
    for f in fs:
        nfiles += 1
        base = os.path.basename(f)
        calls = {}
        with open(f, 'r', encoding='utf-8', errors='replace') as src:
            for line in src:
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                t = d.get('type')
                if t == 'tool/call':
                    dat = d.get('data') or {}
                    calls[dat.get('callId')] = (dat.get('name'), dat.get('arguments'), d.get('seq'), d.get('time'))
                elif t == 'tool/result':
                    dat = d.get('data') or {}
                    cid = ((dat.get('message') or {}).get('source') or {}).get('callId')
                    if cid not in calls:
                        continue
                    nm, args, seq, ctime = calls[cid]
                    try:
                        a = json.loads(args or '{}')
                    except Exception:
                        a = {}
                    txt, meta = texts_and_meta(dat)
                    rec = {'f': base, 'seq': seq, 'time': ctime, 'call': cid}
                    if nm == 'read':
                        lines = meta.get('lines')
                        if isinstance(lines, list):
                            rec.update({'path': meta.get('path') or a.get('file_path'),
                                        'offset': meta.get('offset'), 'totalLines': meta.get('totalLines'),
                                        'lang': meta.get('lang'),
                                        'lines': [[l.get('number'), l.get('text')] for l in lines]})
                            emit('read', rec)
                        else:
                            rec.update({'path': a.get('file_path'), 'text': txt[:4000],
                                        'meta': meta, 'isError': d.get('data', {}).get('isError')})
                            emit('misc', rec)
                    elif nm == 'write':
                        rec.update({'path': a.get('file_path'), 'content': a.get('content'),
                                    'result': txt[:400]})
                        emit('write', rec)
                    elif nm == 'edit':
                        rec.update({'path': a.get('file_path'), 'old': a.get('old_string'),
                                    'new': a.get('new_string'), 'replace_all': bool(a.get('replace_all')),
                                    'result': txt[:400]})
                        emit('edit', rec)
                    elif nm in ('term', 'terminal', 'bash'):
                        cmd = a.get('command') or ''
                        rec.update({'cmd': cmd, 'desc': a.get('description'), 'term': a.get('terminal'),
                                    'workdir': a.get('workdir')})
                        if RE_GIT.search(cmd) or RE_DIFFOUT.search(txt or ''):
                            rec2 = dict(rec)
                            rec2['out'] = txt
                            emit('diff', rec2)
                        if RE_WRITEY.search(cmd):
                            rec3 = dict(rec)
                            rec3['out'] = txt[:20000]
                            emit('termfile', rec3)
                        if RE_DUMPY.search(cmd) and len(txt or '') > 200:
                            rec4 = dict(rec)
                            rec4['out'] = txt
                            emit('termdump', rec4)
                        rec['out_len'] = len(txt or '')
                        emit('termlog', rec)
                    else:
                        pass
        if nfiles % 20 == 0:
            sys.stderr.write('scanned %d/%d files\n' % (nfiles, len(fs)))
            sys.stderr.flush()
    for k in KINDS:
        fh[k].close()
    print('files=%d' % nfiles)
    for k in KINDS:
        p = os.path.join(W, 'events-%s.jsonl' % k)
        print('%-9s %7d  %12d bytes' % (k, cnt[k], os.path.getsize(p)))

main()
