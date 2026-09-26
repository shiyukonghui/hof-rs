# -*- coding: utf-8 -*-
"""TASK-102: find a board the auto clock can play for a whole sample window.

The match3 clock sample of r2 watched a FROZEN board: `AutoTicks` climbed 4 -> 33
while `Moves`, `Score`, `BoardHash` and `Refills` never moved once.  The pinned
board (Q) had exactly one legal swap, the clock consumed it before the first
sampled frame, and `AutoStep` then found nothing -- so thirty frames of sampling
recorded a board that could not change.  This script searches, deterministically,
for a board whose auto-play survives a long window; the generator pins the one it
finds.
"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ms", os.path.join(HERE, "make_session_match3.py"))
ms = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ms)

STEPS = 60


def endurance(board, seed, target=100000, limit=1000):
    sim = ms.MSim(board, seed=seed, target=target, move_limit=limit)
    start = sim.board_hash()
    applied = sim.auto_step(STEPS)
    return applied, sim.moves, sim.score, sim.total_cleared, sim.board_hash() != start, sim.board()


candidates = [("GEN", ms.GEN_BOARD), ("PLAIN", ms.PLAIN), ("Q", ms.SWAP_BOARD)]

print("== named boards, seed 1000")
for name, board in candidates:
    applied, moves, score, cleared, changed, after = endurance(board, 1000)
    print("  %-6s applied=%2d/%d moves=%-3d score=%-5d cleared=%-4d changed=%-5s after=%s"
          % (name, applied, STEPS, moves, score, cleared, changed, after[:24]))

print("== the generated board over a few seeds")
for seed in (1, 7, 1000, 4242, 99991, 123456789):
    applied, moves, score, cleared, changed, after = endurance(ms.GEN_BOARD, seed)
    print("  seed=%-9d applied=%2d/%d moves=%-3d score=%-5d cleared=%-4d changed=%s"
          % (seed, applied, STEPS, moves, score, cleared, changed))

print("== one-cell variants of the quiet board P, looking for a long-playing one")
best = None
for r in range(ms.ROWS):
    for c in range(ms.COLS):
        for value in range(ms.COLORS):
            rows = [[int(ch) for ch in line] for line in ms.P_ROWS]
            if rows[r][c] == value:
                continue
            rows[r][c] = value
            text = "/".join("".join(str(v) for v in row) for row in rows)
            if ms.MSim(text).find_matches():
                continue
            applied, moves, score, cleared, changed, after = endurance(text, 1000)
            if applied == STEPS and changed:
                best = (text, r, c, value, moves, score, cleared, after)
                break
        if best:
            break
    if best:
        break
if best:
    print("  FOUND change=(%d,%d,%d) board=%s" % (best[1], best[2], best[3], best[0]))
    print("        moves=%d score=%d cleared=%d after=%s" % (best[4], best[5], best[6], best[7]))
else:
    print("  none")
