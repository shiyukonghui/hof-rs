# -*- coding: utf-8 -*-
"""TASK-082 item 4 recon: find module sources whose HEAD is damaged (truncated)."""
import os, re, sys, json

ROOT = r'H:\rebuild\godot\modules\mcp_server'
BAK  = r'C:\Users\wyl\AppData\Local\Temp\mcp044-module-backup\mcp_server'
OUT  = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\head-scan.txt'

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
lines = []
def w(s=''):
    lines.append(str(s))
    print(s)

def first_lines(p, n=3):
    with open(p, 'rb') as fh:
        raw = fh.read()
    txt = raw.decode('utf-8', 'replace')
    ls = [l.rstrip() for l in txt.split('\n')]
    return ls, raw

w('=== TASK-044 backup availability ===')
w('bak exists=%s' % os.path.isdir(BAK))
if os.path.isdir(BAK):
    for rel in ('mcp_server.cpp', 'mcp_server.h', 'tool_registry.cpp', 'mcp_jsonrpc.cpp'):
        p = os.path.join(BAK, rel)
        w('  %s: %s' % (rel, (str(os.path.getsize(p)) + ' B') if os.path.exists(p) else 'MISSING'))
    b = os.path.join(BAK, 'mcp_server.cpp')
    if os.path.exists(b):
        ls, raw = first_lines(b)
        w('  --- backup mcp_server.cpp first 20 lines ---')
        for i, l in enumerate(ls[:20], 1):
            w('    %3d: %s' % (i, l[:140]))

w('')
w('=== head-damage scan over %s ===' % ROOT)
WANT_EXT = ('.cpp', '.h')
damaged = []
ok = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in ('__pycache__', '.git')]
    for fn in sorted(filenames):
        if not fn.endswith(WANT_EXT):
            continue
        p = os.path.join(dirpath, fn)
        rel = os.path.relpath(p, ROOT).replace('\\', '/')
        ls, raw = first_lines(p)
        first = next((l for l in ls if l.strip()), '')
        s = first.strip()
        has_license = s.startswith('/****') or s.startswith('/*')
        has_include = s.startswith('#include')
        has_pragma = s.startswith('#pragma')
        has_ifndef = s.startswith('#ifndef')
        looks_ok = has_license or has_include or has_pragma or has_ifndef
        # extra signals of a lost head
        inc_count = sum(1 for l in ls if l.strip().startswith('#include'))
        has_ns = any(re.match(r'namespace\s+\w+', l.strip()) for l in ls[:60])
        rec = dict(rel=rel, bytes=len(raw), first=s[:90], license=has_license,
                   includes=inc_count, ns=has_ns)
        (ok if looks_ok else damaged).append(rec)

w('files scanned: ok_head=%d damaged_head=%d' % (len(ok), len(damaged)))
w('')
w('--- DAMAGED HEAD (no license / include / pragma as first token) ---')
for r in damaged:
    w('  %-58s %7d B inc=%-3d ns=%-5s  first=%r' % (r['rel'], r['bytes'], r['includes'], r['ns'], r['first']))

w('')
w('--- suspicious: has a head token but ZERO #include ---')
for r in ok:
    if r['includes'] == 0:
        w('  %-58s %7d B ns=%-5s  first=%r' % (r['rel'], r['bytes'], r['ns'], r['first']))

open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
print('->', OUT)
