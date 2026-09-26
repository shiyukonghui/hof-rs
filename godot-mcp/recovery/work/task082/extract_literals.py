# -*- coding: utf-8 -*-
"""TASK-082 item 3d: extract the TASK-076 verbatim description literals from the C++ side."""
import hashlib, json, os, re

CPP = r'H:\rebuild\godot\modules\mcp_server\tools\editor_tilemap_write.cpp'
OLD = r'F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json'   # READ ONLY
OUT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\task076-literals.txt'
lines = []
def w(s=''):
    lines.append(str(s))

src = open(CPP, 'rb').read().decode('utf-8')
tl = src.split('\n')
w('source %s (%d lines)' % (CPP, len(tl)))
w('')
w('=== lines 520..560 (raw) ===')
for i in range(519, min(560, len(tl))):
    w('%5d: %s' % (i + 1, tl[i]))

# find ToolBuilder("<name>", ... description literal
w('')
w('=== ToolBuilder description literals for the two tilemap tools ===')
for i, ln in enumerate(tl):
    if 'editor_set_tilemap_cell"' in ln or 'editor_set_tilemap_cells_in_rect"' in ln:
        w('line %d: %s' % (i + 1, ln.strip()[:200]))

# generic: collect all C++ string literals that contain the gap sentence marker
w('')
w('=== full string literals containing the marker ===')
marker = '写格子要求目标 TileMapLayer'
for i, ln in enumerate(tl):
    if marker in ln:
        # join continuation lines until the terminating ");
        buf = []
        j = i
        while j < len(tl):
            buf.append(tl[j])
            if re.search(r'"\s*\)\s*;', tl[j]) or (tl[j].rstrip().endswith('"') and j > i):
                break
            j += 1
        joined = '\n'.join(buf)
        lits = re.findall(r'"((?:[^"\\]|\\.)*)"', joined)
        for L in lits:
            if marker in L:
                b = L.encode('utf-8')
                w('  at line %d: bytes=%d' % (i + 1, len(b)))
                w('  %s' % L)

w('')
w('=== old contract descriptions (READ ONLY source) ===')
w('old contract exists=%s' % os.path.exists(OLD))
if os.path.exists(OLD):
    oc = json.loads(open(OLD, 'rb').read().decode('utf-8'))
    w('sha256=%s' % hashlib.sha256(open(OLD, 'rb').read()).hexdigest())
    byname = {t['name']: t for t in oc['result']['tools']}
    for n in ('get_scene_tree', 'tilemap_set_cell', 'tilemap_fill_rect'):
        t = byname.get(n)
        if not t:
            w('  %s: NOT PRESENT' % n)
            continue
        d = t['description']
        w('  %s: bytes=%d  %r' % (n, len(d.encode('utf-8')), d))

open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
print('written', OUT)
