# -*- coding: utf-8 -*-
"""Decode a build log and extract the compile errors + their owning targets."""
import re, sys, collections

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def load(p):
    raw = open(p, 'rb').read()
    for enc in ('utf-8', 'cp936', 'cp1252'):
        try:
            return raw.decode(enc), enc, raw
        except Exception:
            continue
    return raw.decode('utf-8', 'replace'), 'utf-8/replace', raw

def report(tag, out, err):
    print('=' * 78)
    print('### %s' % tag)
    print('=' * 78)
    o, eo, ro = load(out)
    e, ee, re_ = load(err)
    print('stdout: decoded=%s bytes=%d lines=%d CR=%d' % (eo, len(ro), o.count('\n') + 1, ro.count(b'\r')))
    print('stderr: decoded=%s bytes=%d lines=%d CR=%d' % (ee, len(re_), e.count('\n') + 1, re_.count(b'\r')))

    ol = o.split('\n')
    el = e.split('\n')

    print('')
    print('--- stderr non-warning lines ---')
    for ln in el:
        s = ln.strip()
        if not s:
            continue
        if s.startswith('WARNING:') or s.startswith('You can install') or s.startswith('See the documentation') or s.startswith('https://') or s.startswith('Alternatively,'):
            continue
        print('  %s' % s)

    print('')
    err_lines = [l for l in el if re.search(r':\s*(error|fatal error)\s+[A-Z]+\d+:', l)]
    print('--- distinct error lines: %d ---' % len(err_lines))
    seen = []
    for l in err_lines:
        if l not in seen:
            seen.append(l)
    for l in seen:
        print('  %s' % l.strip())

    print('')
    owners = [l.strip() for l in el if l.strip().startswith('scons: ***')]
    print('--- failing targets (scons ***): %d ---' % len(owners))
    for l in owners:
        print('  %s' % l)

    print('')
    print('--- last 12 stdout lines ---')
    for l in ol[-13:]:
        if l.strip():
            print('  %s' % l)

    print('')
    print('--- module mcp_server compiles in stdout ---')
    mods = [l.strip() for l in ol if 'mcp_server' in l]
    print('  count=%d' % len(mods))
    for l in mods:
        print('  %s' % l)

report(sys.argv[1], sys.argv[2], sys.argv[3])
