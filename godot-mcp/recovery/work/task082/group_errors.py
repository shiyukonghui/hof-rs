# -*- coding: utf-8 -*-
"""TASK-082 item 4: group build3 errors by owning file and by error code."""
import collections, re, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
LOG = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs\task082_build3_keepgoing.txt'
ERR = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs\task082_build3_keepgoing.err.txt'
OUT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\build3-errors.txt'


def load(p):
    raw = open(p, 'rb').read()
    for enc in ('utf-8', 'cp936'):
        try:
            return raw.decode(enc), enc
        except Exception:
            continue
    return raw.decode('utf-8', 'replace'), 'utf-8/replace'


o, eo = load(LOG)
e, ee = load(ERR)
print('stdout enc=%s lines=%d' % (eo, o.count('\n') + 1))
print('stderr enc=%s lines=%d' % (ee, e.count('\n') + 1))

errlines = [l for l in e.split('\n') if re.search(r':\s*(error|fatal error)\s+[A-Z]+\d+:', l)]
fatal = [l for l in e.split('\n') if 'scons: ***' in l]

byfile = collections.OrderedDict()
codes = collections.Counter()
for l in errlines:
    m = re.match(r'^\s*(.*?)\((\d+)\)\s*:\s*(?:fatal )?error\s+([A-Z]+\d+)\s*:', l)
    if not m:
        continue
    f, ln, code = m.group(1), m.group(2), m.group(3)
    f = f.replace('\\', '/').lstrip('.')
    f = re.sub(r'^/', '', f)
    byfile.setdefault(f, []).append((int(ln), code, l.strip()))
    codes[code] += 1

# module-only
mod = {k: v for k, v in byfile.items() if 'mcp_server' in k}
other = {k: v for k, v in byfile.items() if 'mcp_server' not in k}

out = []
def w(s=''):
    out.append(str(s))
    print(s)

w('=== ERROR TOTALS ===')
w('total error lines    : %d' % len(errlines))
w('distinct files       : %d' % len(byfile))
w('  module mcp_server  : %d files, %d errors' % (len(mod), sum(len(v) for v in mod.values())))
w('  other/engine       : %d files, %d errors' % (len(other), sum(len(v) for v in other.values())))
w('')
w('=== error codes (all) ===')
for c, n in codes.most_common():
    w('  %-8s %d' % (c, n))
w('')
w('=== failing targets (scons ***) : %d ===' % len(fatal))
for l in fatal:
    w('  ' + l.strip())
w('')
w('=== MODULE mcp_server errors, per file ===')
for f in sorted(mod, key=lambda k: -len(mod[k])):
    v = sorted(mod[f])
    w('%-52s %4d errors   first@line %d   codes=%s' % (f, len(v), v[0][0], sorted({x[1] for x in v})))
w('')
w('=== MODULE mcp_server: first 12 error lines of each file ===')
for f in sorted(mod, key=lambda k: -len(mod[k])):
    v = sorted(mod[f])
    w('--- %s (%d errors) ---' % (f, len(v)))
    for ln, code, txt in v[:12]:
        w('   %s' % txt)
w('')
w('=== ENGINE errors (non-module), grouped ===')
for f in sorted(other, key=lambda k: -len(other[k])):
    w('%-60s %4d errors  codes=%s' % (f, len(other[f]), sorted({x[1] for x in other[f]})))
w('')
w('=== tail of stdout ===')
ol = [l for l in o.split('\n') if l.strip()]
for l in ol[-15:]:
    w('  ' + l)

open(OUT, 'w', encoding='utf-8').write('\n'.join(out))
print('->', OUT)
