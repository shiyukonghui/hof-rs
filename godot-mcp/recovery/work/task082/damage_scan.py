# -*- coding: utf-8 -*-
"""TASK-082 item 4 recon: structural damage scan over every module .cpp/.h."""
import os, re, sys

ROOT = r'H:\rebuild\godot\modules\mcp_server'
OUT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\damage-scan.txt'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
lines = []
def w(s=''):
    lines.append(str(s))
    print(s)

def last_nonblank(ls):
    for l in reversed(ls):
        if l.strip():
            return l.strip()
    return ''

rows = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in ('__pycache__', '.git')]
    for fn in sorted(filenames):
        if not fn.endswith(('.cpp', '.h')):
            continue
        p = os.path.join(dirpath, fn)
        rel = os.path.relpath(p, ROOT).replace('\\', '/')
        raw = open(p, 'rb').read()
        txt = raw.decode('utf-8', 'replace')
        # strip line comments and strings crudely for the brace count
        stripped = re.sub(r'//[^\n]*', '', txt)
        stripped = re.sub(r'/\*.*?\*/', '', stripped, flags=re.S)
        stripped = re.sub(r'"(?:[^"\\]|\\.)*"', '""', stripped)
        stripped = re.sub(r"'(?:[^'\\]|\\.)*'", "''", stripped)
        ob = stripped.count('{')
        cb = stripped.count('}')
        op = stripped.count('(')
        cp = stripped.count(')')
        ls = txt.split('\n')
        first = next((l.strip() for l in ls if l.strip()), '')
        last = last_nonblank(ls)
        ok_first = first.startswith(('/*', '#include', '#pragma', '#ifndef'))
        ok_last = last.endswith(('}', '#endif', ')', ';')) or last.endswith('*/')
        rows.append(dict(rel=rel, bytes=len(raw), lines=len(ls), bd=ob - cb, pd=op - cp,
                         ok_first=ok_first, ok_last=ok_last, first=first[:70], last=last[:70]))

bad = [r for r in rows if r['bd'] != 0 or not r['ok_first'] or not r['ok_last']]
w('scanned=%d  clean=%d  flagged=%d' % (len(rows), len(rows) - len(bad), len(bad)))
w('')
w('%-52s %8s %6s %5s %5s %-6s %-6s' % ('rel', 'bytes', 'lines', 'bd', 'pd', 'head', 'tail'))
for r in bad:
    w('%-52s %8d %6d %5d %5d %-6s %-6s' % (r['rel'], r['bytes'], r['lines'], r['bd'], r['pd'],
                                            'ok' if r['ok_first'] else 'BAD',
                                            'ok' if r['ok_last'] else 'BAD'))
w('')
w('--- flagged: head BAD ---')
for r in bad:
    if not r['ok_first']:
        w('  %s (%d B) first=%r' % (r['rel'], r['bytes'], r['first']))
w('')
w('--- flagged: tail BAD ---')
for r in bad:
    if not r['ok_last']:
        w('  %s (%d B) last=%r' % (r['rel'], r['bytes'], r['last']))
w('')
w('--- flagged: brace/paren delta != 0 ---')
for r in bad:
    if r['bd'] != 0 or r['pd'] != 0:
        w('  %s (%d B, %d lines) brace_delta=%d paren_delta=%d last=%r'
          % (r['rel'], r['bytes'], r['lines'], r['bd'], r['pd'], r['last']))

open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
print('->', OUT)
