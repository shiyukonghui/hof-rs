#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-148 evidence: old (TASK-109) package vs this batch, per game.

Compares the three payload pieces that carry game behaviour:
  * <game>.exe                              - engine template + icon resources
  * <game>.pck                              - packed scenes / scripts / project settings
  * data_<game>_windows_x86_64/<game>.dll   - the compiled C# assembly (game logic)
"""
import hashlib
import json
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DIST = r'F:\moonbit-hof-rs\godot-mcp\dist'
WORK = r'F:\moonbit-hof-rs\godot-mcp\recovery\work\task148'
EXE_DIR = os.path.join(WORK, 'exe')
OLD = ['godot-mcp-20games-exe-20260927-0927-part1of2.zip',
       'godot-mcp-20games-exe-20260927-0927-part2of2.zip']

# the 9 games the user named as changed after the old package was built
NAMED = {'snake', 'game2048', 'pong', 'puzzlebobble', 'platformer',
         'asteroids', 'frogger', 'bomberman', 'flappy'}


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for c in iter(lambda: fh.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


old = {}
for n in OLD:
    with zipfile.ZipFile(os.path.join(DIST, n)) as z:
        text = z.read(n[:-4] + '/MANIFEST.txt').decode('utf-8')
        for line in text.splitlines():
            if not line.strip() or line.startswith('#'):
                continue
            parts = line.split('  ')
            if len(parts) == 3:
                old[parts[2]] = (parts[0], int(parts[1]))

with open(os.path.join(WORK, 'export-results.json'), encoding='utf-8-sig') as fh:
    ex = {r['game']: r for r in json.load(fh)}

print('%-15s %-4s %-9s %-9s %-9s' % ('game', 'name', 'exe', 'pck', 'dll'))
print('-' * 60)
summary = {'exe': [0, 0], 'pck': [0, 0], 'dll': [0, 0]}
for g in sorted(ex):
    row = []
    for kind, rel, newsha in (
            ('exe', 'games/%s/%s.exe' % (g, g), ex[g]['exe_sha256']),
            ('pck', 'games/%s/%s.pck' % (g, g), ex[g]['pck_sha256']),
            ('dll', 'games/%s/data_%s_windows_x86_64/%s.dll' % (g, g, g),
             sha_file(os.path.join(EXE_DIR, g, 'data_%s_windows_x86_64' % g, '%s.dll' % g)))):
        o = old.get(rel)
        same = (o is not None and o[0] == newsha)
        summary[kind][0 if same else 1] += 1
        row.append('same' if same else 'DIFF')
    print('%-15s %-4s %-9s %-9s %-9s' % (g, 'YES' if g in NAMED else '-', row[0], row[1], row[2]))

print('')
for kind, (same, diff) in summary.items():
    print('%-4s same=%-3d diff=%-3d' % (kind, same, diff))
