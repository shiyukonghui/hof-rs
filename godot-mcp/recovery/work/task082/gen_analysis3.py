# -*- coding: utf-8 -*-
"""TASK-082 item 3c: raw AST dict-key analysis (duplicates preserved) + v1.22 wiring."""
import ast, collections, hashlib, io, json, os, re, sys

TREE = r'H:\rebuild\godot\modules\mcp_server\scripts\gen_renamed_contract.py'
OUT  = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\gen-analysis3.txt'
lines = []
def w(s=''):
    lines.append(str(s))

src = open(TREE, 'rb').read().decode('utf-8')
tl = src.split('\n')
tree = ast.parse(src)

for node in tree.body:
    if not isinstance(node, ast.Assign):
        continue
    for tgt in node.targets:
        if not (isinstance(tgt, ast.Name) and tgt.id.endswith('OVERRIDES')):
            continue
        d = node.value
        raw = []
        for k in d.keys:
            if isinstance(k, ast.Constant):
                raw.append((k.value, k.lineno))
        w('=== %s (line %d) raw key count=%d ===' % (tgt.id, node.lineno, len(raw)))
        c = collections.Counter(x[0] for x in raw)
        for name, ln in raw:
            dup = '  <== DUPLICATE' if c[name] > 1 else ''
            w('  line %5d  %s%s' % (ln, name, dup))
        dups = [k for k, v in c.items() if v > 1]
        w('  duplicate keys: %s' % (dups if dups else 'NONE'))
        w('  distinct=%d raw=%d' % (len(c), len(raw)))

# where the names are referenced (any occurrence)
w('')
w('=== ALL source occurrences of the suspect override names ===')
for name in ('play_scene', 'find_signal_connections', 'editor_get_scene_tree',
             'editor_set_tilemap_cell', 'editor_set_tilemap_cells_in_rect',
             'tilemap_set_cell', 'tilemap_fill_rect', 'get_scene_tree'):
    hits = [(i + 1, ln.strip()[:130]) for i, ln in enumerate(tl) if name in ln]
    w('%s: %d occurrences' % (name, len(hits)))
    for i, s in hits:
        w('    line %5d: %s' % (i, s))

# the two v1.22 sentence literals
w('')
w('=== v1.22 sentence literals ===')
for name in ('SCENE_TREE_ADDRESSABILITY_SENTENCE', 'TILEMAP_ATLAS_GAP_SENTENCE'):
    hits = [(i + 1, ln.strip()[:150]) for i, ln in enumerate(tl) if name in ln]
    w('%s: %s' % (name, hits if hits else 'NOT DEFINED'))
w('')
w('=== how DESCRIPTION_OVERRIDES is consumed / appended to ===')
for i, ln in enumerate(tl, 1):
    if re.search(r'DESCRIPTION_OVERRIDES|SCHEMA_OVERRIDES', ln):
        w('  line %5d: %s' % (i, ln.strip()[:150]))

open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
print('written', OUT)
