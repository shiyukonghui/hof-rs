#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-148 evidence: are the freshly built assemblies really built from the CURRENT
sources, and did the stale TASK-109 package miss those changes?

Method: take every string literal of the current `projects/<game>/src/*.cs`, look for it
(UTF-16LE, which is how the .NET #US heap stores literals, plus UTF-8 as a fallback) in
the OLD packaged DLL and in the NEW DLL.  A literal that is in the new DLL but not in the
old one is direct proof that (a) the old package predates the source change and (b) the new
export contains it.
"""
import json
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = r'F:\moonbit-hof-rs\godot-mcp'
DIST = os.path.join(ROOT, 'dist')
WORK = os.path.join(ROOT, 'recovery', 'work', 'task148')
EXE_DIR = os.path.join(WORK, 'exe')
OLD = ['godot-mcp-20games-exe-20260927-0927-part1of2.zip',
       'godot-mcp-20games-exe-20260927-0927-part2of2.zip']
NAMED = ['snake', 'game2048', 'pong', 'puzzlebobble', 'platformer',
         'asteroids', 'frogger', 'bomberman', 'flappy']

with open(os.path.join(WORK, 'export-results.json'), encoding='utf-8-sig') as fh:
    ex = {r['game']: r for r in json.load(fh)}


def literals(game, minlen=8, limit=40):
    out = []
    src_dir = os.path.join(ROOT, 'projects', game, 'src')
    for fn in sorted(os.listdir(src_dir)):
        if not fn.endswith('.cs'):
            continue
        text = open(os.path.join(src_dir, fn), encoding='utf-8', errors='replace').read()
        for m in re.finditer(r'"((?:[^"\\]|\\.){%d,60})"' % minlen, text):
            s = m.group(1)
            if s not in out:
                out.append(s)
        if len(out) >= limit:
            break
    return out[:limit]


def find(hay, s):
    return (s.encode('utf-16-le') in hay) or (s.encode('utf-8') in hay)


print('%-15s %-6s %-6s %-6s %-6s' % ('game', 'lits', 'in_old', 'in_new', 'new_only'))
print('-' * 50)
for g in NAMED:
    lits = literals(g)
    rel = 'games/%s/data_%s_windows_x86_64/%s.dll' % (g, g, g)
    old_blob = None
    for n in OLD:
        with zipfile.ZipFile(os.path.join(DIST, n)) as z:
            try:
                old_blob = z.read(n[:-4] + '/' + rel)
                break
            except KeyError:
                continue
    new_blob = open(os.path.join(EXE_DIR, g, 'data_%s_windows_x86_64' % g, '%s.dll' % g), 'rb').read()
    in_old = in_new = new_only = 0
    for s in lits:
        o = old_blob is not None and find(old_blob, s)
        n = find(new_blob, s)
        in_old += o
        in_new += n
        new_only += (n and not o)
    print('%-15s %-6d %-6d %-6d %-6d' % (g, len(lits), in_old, in_new, new_only))
