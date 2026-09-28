#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-148 evidence: do the re-exported PCKs differ from the stale TASK-109 package?"""
import json
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DIST = r'F:\moonbit-hof-rs\godot-mcp\dist'
WORK = r'F:\moonbit-hof-rs\godot-mcp\recovery\work\task148'
OLD = ['godot-mcp-20games-exe-20260927-0927-part1of2.zip',
       'godot-mcp-20games-exe-20260927-0927-part2of2.zip']

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

print('旧包 (TASK-109, 20260927-0927)  vs  本批 (TASK-148)  —— 逐款 .pck 对比')
print('%-15s %-10s %-10s %-8s %s' % ('game', 'old_bytes', 'new_bytes', 'bytes', 'sha256'))
changed = same = 0
for g in sorted(ex):
    key = 'games/%s/%s.pck' % (g, g)
    o = old.get(key)
    n = (ex[g]['pck_sha256'], ex[g]['pck_bytes'])
    verdict = 'SAME' if o == n else 'CHANGED'
    if o == n:
        same += 1
    else:
        changed += 1
    print('%-15s %-10s %-10d %-8s %s' % (g, o[1] if o else '?', n[1],
                                         '=' if o and o[1] == n[1] else '!', verdict))
print('')
print('exe 也逐款对比（导出模板 -> 大小应恒定，sha 应恒定）:')
for g in sorted(ex):
    key = 'games/%s/%s.exe' % (g, g)
    o = old.get(key)
    n = (ex[g]['exe_sha256'], ex[g]['exe_bytes'])
    print('%-15s old=%s new=%s %s' % (g, o[0][:12] if o else '?', n[0][:12],
                                      'SAME' if o == n else 'DIFFERENT'))
print('')
print('PCK summary: changed=%d same=%d of %d' % (changed, same, len(ex)))
