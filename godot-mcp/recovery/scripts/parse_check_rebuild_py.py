#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TASK-079 parse check: ast.parse over EVERY .py in rebuild\\godot (+ rebuild\\_low-confidence).
Writes work\\parse-py.json.  Read-only over the tree; output only under mcp-recovery\\work."""
import ast, io, json, os, collections

ROOT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
TREES = [('godot', os.path.join(ROOT, 'rebuild', 'godot')),
         ('_low-confidence', os.path.join(ROOT, 'rebuild', '_low-confidence')),
         ('staging', os.path.join(ROOT, 'staging'))]
OUT = os.path.join(ROOT, 'work', 'parse-py.json')


def parses(p):
    try:
        raw = open(p, 'rb').read()
    except Exception as e:
        return {'status': 'read-error', 'detail': str(e), 'line': None}
    try:
        src = raw.decode('utf-8')
    except UnicodeDecodeError as e:
        return {'status': 'decode-error', 'detail': str(e), 'line': None}
    try:
        ast.parse(src)
        return {'status': 'ok', 'detail': None, 'line': None}
    except SyntaxError as e:
        return {'status': 'syntax-error', 'detail': '%s: %s' % (type(e).__name__, e.msg), 'line': e.lineno}
    except Exception as e:
        return {'status': 'error', 'detail': '%s: %s' % (type(e).__name__, e), 'line': None}


report = {}
for tag, base in TREES:
    rows = []
    if not os.path.isdir(base):
        report[tag] = {'missing': True}
        continue
    for dirpath, dirnames, filenames in os.walk(base):
        for fn in filenames:
            if not fn.lower().endswith('.py'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, base)
            r = parses(fp)
            r['rel'] = rel
            r['bytes'] = os.path.getsize(fp)
            rows.append(r)
    c = collections.Counter(r['status'] for r in rows)
    report[tag] = {
        'root': base,
        'total_py': len(rows),
        'counts': dict(c),
        'failures': sorted([r for r in rows if r['status'] != 'ok'],
                           key=lambda r: r['rel']),
    }

with io.open(OUT, 'w', encoding='utf-8') as f:
    f.write(json.dumps(report, ensure_ascii=False, indent=1))

for tag in report:
    d = report[tag]
    if d.get('missing'):
        print('%-16s MISSING' % tag)
        continue
    print('%-16s total=%-5d %s failures=%d' % (tag, d['total_py'], d['counts'],
                                               len(d['failures'])))
    for r in d['failures']:
        print('    line %-6s %-90s %s' % (r['line'], r['rel'][:90], r['detail']))
print('wrote ' + OUT)
