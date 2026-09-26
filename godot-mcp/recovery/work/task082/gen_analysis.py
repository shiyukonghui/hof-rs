# -*- coding: utf-8 -*-
"""TASK-082 item 3: analyse gen_renamed_contract.py (tree vs low-confidence)."""
import hashlib, io, json, os, re, sys, collections

TREE = r'H:\rebuild\godot\modules\mcp_server\scripts\gen_renamed_contract.py'
LC   = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\rebuild\_low-confidence\modules\mcp_server\scripts\gen_renamed_contract.py'
OUT  = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\gen-analysis.txt'

lines = []
def w(s=''):
    lines.append(str(s))

for tag, path in (('TREE', TREE), ('LC', LC)):
    b = open(path, 'rb').read()
    w('%s %s' % (tag, path))
    w('  bytes=%d sha256=%s' % (len(b), hashlib.sha256(b).hexdigest()))
    try:
        t = b.decode('utf-8')
        w('  utf-8 decode: OK, chars=%d' % len(t))
    except UnicodeDecodeError as e:
        w('  utf-8 decode: FAIL %s' % e)
        t = b.decode('utf-8', 'replace')
    w('  CR count=%d  LF count=%d' % (b.count(b'\r'), b.count(b'\n')))
    w('  lines=%d' % (t.count('\n') + 1))
    w('')

bt = open(TREE, 'rb').read()
bl = open(LC, 'rb').read()
n = min(len(bt), len(bl))
diffs = [i for i in range(n) if bt[i] != bl[i]]
w('byte-diff count=%d first=%s' % (len(diffs), diffs[:5]))
if diffs:
    i = diffs[0]
    w('  tree ctx: %r' % bt[max(0, i - 60):i + 60])
    w('  lc   ctx: %r' % bl[max(0, i - 60):i + 60])
w('')

t = bt.decode('utf-8', 'replace')
tl = t.split('\n')

# 1) generator version
for i, ln in enumerate(tl, 1):
    if 'GENERATOR_VERSION' in ln:
        w('line %d: %s' % (i, ln.rstrip()))

w('')
# 2) duplicate-block detection: find repeated contiguous line runs >= 20 lines
w('=== duplicate contiguous blocks (>=20 identical consecutive non-blank lines repeated) ===')
norm = [l.rstrip() for l in tl]
run = 20
seen = {}
for i in range(len(norm) - run):
    key = '\n'.join(norm[i:i + run])
    if not key.strip():
        continue
    seen.setdefault(key, []).append(i + 1)
dups = [(k, v) for k, v in seen.items() if len(v) > 1]
dups.sort(key=lambda kv: kv[1][0])
if not dups:
    w('none at run>=20')
for k, v in dups[:20]:
    w('  start lines %s : first=%r' % (v, k.split('\n')[0][:100]))
    w('    last line of block: %r' % k.split('\n')[-1][:100])
w('total duplicate blocks at run=%d: %d' % (run, len(dups)))

w('')
# 3) repeated definitions / repeated table entries
w('=== repeated top-level definitions ===')
defs = collections.defaultdict(list)
for i, ln in enumerate(tl, 1):
    m = re.match(r'^(def |class |[A-Z_][A-Z0-9_]* *=)', ln)
    if m:
        defs[ln.strip()].append(i)
for k, v in defs.items():
    if len(v) > 1:
        w('  %d x line %s : %s' % (len(v), v, k[:110]))
w('total duplicated def/assign lines: %d' % sum(1 for v in defs.values() if len(v) > 1))

w('')
# 4) override tables
w('=== override tables ===')
for name in ('DESCRIPTION_OVERRIDES', 'SCHEMA_OVERRIDES'):
    idx = [i for i, ln in enumerate(tl) if re.match(r'^%s\s*=' % name, ln)]
    w('%s: assignment at %s' % (name, [i + 1 for i in idx]))
    for i in idx:
        # scan forward to closing bracket at column 0
        for j in range(i, min(i + 800, len(tl))):
            if re.match(r'^\]', tl[j]):
                w('  block %d..%d (%d lines), entries(  "old_name")=%d' % (
                    i + 1, j + 1, j - i + 1,
                    sum(1 for k in range(i, j) if re.match(r'^\s*\{', tl[k]))))
                break

w('')
# 5) optional trailing newline / BOM
w('BOM tree=%s  ends_with_newline=%s' % (bt[:3] == b'\xef\xbb\xbf', bt.endswith(b'\n')))
w('BOM lc  =%s  ends_with_newline=%s' % (bl[:3] == b'\xef\xbb\xbf', bl.endswith(b'\n')))

open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
print('written', OUT)
