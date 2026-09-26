# -*- coding: utf-8 -*-
"""TASK-082 item 3b: find the duplicate block + count overrides/records."""
import hashlib, json, os, re, collections

TREE = r'H:\rebuild\godot\modules\mcp_server\scripts\gen_renamed_contract.py'
DOCS = r'H:\rebuild\godot\modules\mcp_server\docs'
OUT  = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\gen-analysis2.txt'

lines = []
def w(s=''):
    lines.append(str(s))

t = open(TREE, 'rb').read().decode('utf-8')
tl = t.split('\n')
w('file lines=%d' % len(tl))

# --- repeated non-trivial single lines
w('')
w('=== identical source lines (>50 chars) repeated >=2x ===')
c = collections.defaultdict(list)
for i, ln in enumerate(tl, 1):
    s = ln.strip()
    if len(s) > 50:
        c[s].append(i)
rep = sorted(((k, v) for k, v in c.items() if len(v) > 1), key=lambda kv: kv[1][0])
for k, v in rep:
    w('  x%d lines=%s' % (len(v), v))
    w('    %s' % k[:160])
w('count=%d' % len(rep))

# --- repeated multi-line blocks, lower threshold
w('')
w('=== repeated contiguous blocks, run=8 ===')
norm = [l.rstrip() for l in tl]
run = 8
seen = collections.defaultdict(list)
for i in range(len(norm) - run):
    key = '\n'.join(norm[i:i + run])
    if len(key.strip()) < 120:
        continue
    seen[key].append(i + 1)
dups = sorted(((k, v) for k, v in seen.items() if len(v) > 1), key=lambda kv: kv[1][0])
for k, v in dups[:30]:
    w('  start lines %s' % v)
    w('    first=%r' % k.split('\n')[0][:120])
    w('    last =%r' % k.split('\n')[-1][:120])
w('count=%d' % len(dups))

# --- parse the module to count overrides without executing the transform
w('')
w('=== override tables (via ast) ===')
import ast
tree = ast.parse(t)
found = {}
for node in tree.body:
    if isinstance(node, ast.Assign):
        for tgt in node.targets:
            if isinstance(tgt, ast.Name) and tgt.id.endswith('OVERRIDES'):
                d = ast.literal_eval(node.value)
                found[tgt.id] = (node.lineno, d)
                w('%s at line %d: %d entries' % (tgt.id, node.lineno, len(d)))
                for k in d:
                    w('    - %s' % k)
tot = sum(len(v[1]) for v in found.values())
w('total override entries = %d' % tot)

# --- existing generated JSON
w('')
for name in ('tools_list.renamed.json', 'tool-rename-map.json'):
    p = os.path.join(DOCS, name)
    if not os.path.exists(p):
        w('%s MISSING' % name)
        continue
    b = open(p, 'rb').read()
    w('%s bytes=%d sha256=%s' % (name, len(b), hashlib.sha256(b).hexdigest()))
    if name.startswith('tools_list'):
        j = json.loads(b.decode('utf-8'))
        m = j.get('_meta', {})
        w('  _meta keys=%s' % sorted(m.keys()))
        w('  count=%s added_count=%s generator_version=%s' % (m.get('count'), m.get('added_count'), m.get('generator_version')))
        ov = m.get('overrides')
        if isinstance(ov, list):
            w('  _meta.overrides len=%d' % len(ov))
            kinds = collections.Counter(o.get('kind') for o in ov if isinstance(o, dict))
            w('  kinds=%s' % dict(kinds))
        elif isinstance(ov, dict):
            w('  _meta.overrides dict keys=%s' % sorted(ov.keys()))
            for k, v in ov.items():
                if isinstance(v, list):
                    w('    %s: %d' % (k, len(v)))
                else:
                    w('    %s: %r' % (k, v))
        nt = len(j.get('result', {}).get('tools', []))
        w('  result.tools=%d' % nt)
        tools = j['result']['tools']
        ed = sum(1 for x in tools if x.get('name', '').startswith('editor_'))
        gm = sum(1 for x in tools if x.get('name', '').startswith('running_game_'))
        w('  editor_*=%d  running_game_*=%d  other=%d' % (ed, gm, nt - ed - gm))
        for k in ('order_normative',):
            w('  %s=%r' % (k, m.get(k)))
        for k in ('map_sha256', 'added_tools_sha256'):
            w('  %s=%r' % (k, m.get(k)))
        w('  added_tools=%r' % (m.get('added_tools'),))

# --- TASK-076A mentions
w('')
w('=== TASK-076A / 076A references in the generator ===')
for i, ln in enumerate(tl, 1):
    if '076' in ln:
        w('  line %d: %s' % (i, ln.strip()[:170]))
w('')
w('=== script tail (last 12 lines) ===')
for i, ln in enumerate(tl[-12:], len(tl) - 11):
    w('  %d: %s' % (i, ln.rstrip()[:170]))

open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
print('written', OUT)
