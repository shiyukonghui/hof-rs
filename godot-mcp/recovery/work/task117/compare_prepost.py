#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-117: compare the pre-fix (TASK-109) export with the re-export, file by file.

The point of this table: the user played the batch that is now in
`dist\\exe-task109-pre-fix`.  Saying "the new one is fixed" is only meaningful if
we can show which artifact actually changed, and which deliberately did not.
"""
import io
import json
import os

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
WORK = os.path.join(ROOT, "recovery", "work", "task117")

GAMES = ["asteroids", "bomberman", "breakout", "flappy", "frogger", "game2048",
         "lunarlander", "match3", "minesweeper", "missilecommand", "pacman",
         "platformer", "pong", "puzzlebobble", "rtype", "snake", "sokoban",
         "spaceinvaders", "tetris", "towerdefense"]


def load(name):
    with io.open(os.path.join(WORK, name), encoding="utf-8-sig") as fh:
        d = json.load(fh)
    if isinstance(d, dict):
        d = [d]
    return {r["game"]: r for r in d}


pre = load("pre-fix-hashes.json")
post = load("export-results.json")

rows = []
for g in GAMES:
    a, b = pre.get(g, {}), post.get(g, {})
    row = {"game": g}
    for k in ("exe", "pck", "dll"):
        sk, bk = k + "_sha256", k + "_sha256"
        row[k + "_pre"] = a.get(sk)
        row[k + "_post"] = b.get(bk)
        row[k + "_changed"] = (a.get(sk) != b.get(bk))
    row["pck_bytes_pre"] = a.get("pck_bytes")
    row["pck_bytes_post"] = b.get("pck_bytes")
    rows.append(row)

n_exe = sum(1 for r in rows if r["exe_changed"])
n_pck = sum(1 for r in rows if r["pck_changed"])
n_dll = sum(1 for r in rows if r["dll_changed"])

L = []
L.append("| game | exe | pck | game.dll |")
L.append("|---|---|---|---|")
for r in rows:
    L.append("| %s | %s | %s | %s |" % (
        r["game"],
        "changed" if r["exe_changed"] else "same",
        "%s (%s->%s B)" % ("CHANGED" if r["pck_changed"] else "same",
                           r["pck_bytes_pre"], r["pck_bytes_post"]),
        "CHANGED" if r["dll_changed"] else "same"))

out = {"rows": rows, "summary": {"exe_changed": n_exe, "pck_changed": n_pck,
                                 "dll_changed": n_dll, "games": len(rows)}}
with io.open(os.path.join(WORK, "prepost-compare.json"), "w", encoding="utf-8") as fh:
    fh.write(json.dumps(out, indent=1, ensure_ascii=False))
with io.open(os.path.join(WORK, "prepost-compare.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(L) + "\n")
print("\n".join(L))
print("")
print("exe changed: %d/20 ; pck changed: %d/20 ; game.dll changed: %d/20" % (n_exe, n_pck, n_dll))
