# -*- coding: utf-8 -*-
"""Cross-check the tag-prefix call counting against the TASK-104 milestone table."""
import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'F:\moonbit-hof-rs\godot-mcp'

FINALS = [
    ('pong', 'pong-clean-task097', 23, 29),
    ('breakout', 'breakout-clean-task097', 21, 34),
    ('snake', 'snake-task106-r1', 20, 33),
    ('tetris', 'tetris-task096-r2', 6, 36),
    ('spaceinvaders', 'si-task097-r1', 15, 44),
    ('asteroids', 'ast-task098-r2', 16, 55),
    ('pacman', 'pac-task098-r2', 16, 64),
    ('frogger', 'frog-task099-r1', 16, 74),
    ('flappy', 'flappy-task099-r2', 14, 78),
    ('game2048', '2048-task100-r2', 16, 113),
    ('minesweeper', 'mine-task100-r2', 14, 141),
    ('sokoban', 'soko-task101-r2', 14, 176),
    ('bomberman', 'bomb-task101-r4', 14, 219),
    ('platformer', 'plat-task102-r2', 14, 214),
    ('match3', 'm3-task102-r3', 14, 131),
    ('towerdefense', 'td-task103-r3', 14, 131),
    ('missilecommand', 'mc-task103-r3', 14, 113),
    ('rtype', 'rt-task104-r2', 14, 209),
    ('puzzlebobble', 'pb-task104-r1', 14, 143),
    ('lunarlander', 'll-task104-r1', 14, 216),
]
for game, tag, me, mg in FINALS:
    d = os.path.join(ROOT, 'runs', game, tag)
    rows = [l.rstrip('\n').split('|')[0] for l in
            open(os.path.join(d, 'call-index.txt'), encoding='utf-8-sig') if l.strip()]
    ed = [t for t in rows if t[0] in 'er']
    tools_list = 1 if 'e01-tools-list' in ed else 0
    ce = len(ed) - tools_list
    cg = sum(1 for t in rows if t.startswith('g'))
    cc = sum(1 for t in rows if t.startswith('c'))
    ok = 'OK ' if (ce == me and cg == mg) else '** '
    print('%s%-15s editor=%3d(%d tags - %d toolslist, exp %3d) game=%3d(exp %3d) cleanup=%d total=%d' %
          (ok, game, ce, len(ed), tools_list, me, cg, mg, cc, len(rows)))
