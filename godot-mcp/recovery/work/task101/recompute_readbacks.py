# -*- coding: utf-8 -*-
"""TASK-101: independently recompute the run's own readbacks.

    python recompute_readbacks.py <game> <run-dir>

This is deliberately NOT a call into the payload and NOT a call into the
assertion helper.  It takes the strings the game PRINTED -- the `Dump()`
readbacks and the assertion responses the driver saved -- and recomputes them
from the rules, in Python:

  * Sokoban: every `Dump()` readback prints the board as ASCII plus a
    `hash=` number.  The hash is recomputed from the ASCII board alone with the
    documented code table (wall 2, floor 1, goal 3, box 4, box-on-goal 5,
    player 6, player-on-goal 7, player-on-box 8, player-on-box-on-goal 9), as a
    signed 32-bit multiply-31 chain.  A payload that printed a hash not derived
    from the board it printed fails here.
  * Bomberman: every `Dump()` readback prints the field as ASCII plus a
    `grid_hash=`.  The grid hash is recomputed from the ASCII field alone
    (hard wall 1, floor 2, brick 3).
  * Both: the four blast literals / box lists the session asserts are recomputed
    from a fresh import of the session generator's own second implementation, and
    compared byte for byte with the `actual` value the payload reported in the
    run's saved assertion responses.

Nothing here trusts `report.json`, the assertion helper, or the C#.
"""
import glob
import io
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def load_module(name):
    path = os.path.join(HERE, name)
    spec = importlib.util.spec_from_file_location(name[:-3], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def body_of(path):
    with io.open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        doc = json.load(handle)
    if "error" in doc:
        return None
    content = (doc.get("result") or {}).get("content") or []
    if not content:
        return None
    try:
        return json.loads(content[0].get("text", ""))
    except ValueError:
        return None


def int32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value >= 0x80000000 else value


def sokoban_hash(board):
    codes = {"#": 2, " ": 1, ".": 3, "$": 4, "*": 5, "@": 6, "+": 7}
    h = 17
    for ch in board:
        if ch == "/":
            continue
        h = int32(h * 31 + codes[ch])
    return h


def bomberman_hash(field):
    codes = {"#": 1, "B": 3}
    h = 17
    for ch in field:
        if ch == "/":
            continue
        h = int32(h * 31 + codes.get(ch, 2))
    return h


def kv(text, key):
    marker = key + "="
    start = text.find(marker)
    if start < 0:
        return None
    start += len(marker)
    end = start
    while end < len(text) and text[end] not in " ":
        end += 1
    return text[start:end]


def between(text, key, terminator):
    """The value of `key=`, up to the next ` <terminator>=`.

    The board and the field print as rows joined by '/', and a row can contain a
    SPACE, so a plain split-on-space would truncate them at the first floor cell.
    """
    marker = key + "="
    start = text.find(marker)
    if start < 0:
        return None
    start += len(marker)
    end = text.find(" " + terminator + "=", start)
    if end < 0:
        return text[start:]
    return text[start:end]


def check_readbacks(run, prefix, key_board, key_hash, rule, label):
    print("== %s: %s readbacks" % (label, key_board))
    found = 0
    bad = 0
    for path in sorted(glob.glob(os.path.join(run, "*.json"))):
        tag = os.path.basename(path)[:-5]
        if tag.endswith(".request") or not tag.startswith(("g", "e")):
            continue
        body = body_of(path)
        if not isinstance(body, dict):
            continue
        result = body.get("result")
        if not isinstance(result, str) or (key_board + "=") not in result:
            continue
        found += 1
        board = between(result, key_board, "cols")
        reported = int(float(kv(result, key_hash)))
        recomputed = rule(board)
        ok = reported == recomputed
        if not ok:
            bad += 1
        print("   %-26s reported=%-12d recomputed=%-12d %s" % (
            tag, reported, recomputed, "OK" if ok else "<<< MISMATCH"))
        print("      board=%s" % board)
    print("   readbacks found=%d mismatches=%d" % (found, bad))
    return bad


def check_assertion_literals(run, table, label):
    print("== %s: the recomputed literals the payload actually reported" % label)
    problems = 0
    for tag, key, expected in table:
        path = os.path.join(run, tag + ".json")
        if not os.path.isfile(path):
            print("   %-24s MISSING response file" % tag)
            problems += 1
            continue
        body = body_of(path)
        actual = None
        if isinstance(body, dict):
            actual = body.get("actual")
        if isinstance(actual, float) and actual == int(actual):
            actual = int(actual)
        ok = (actual == expected)
        if not ok:
            problems += 1
        print("   %-24s %-12s expected=%-40r actual=%-40r %s" % (
            tag, key, expected, actual, "OK" if ok else "<<< MISMATCH"))
    print("   literal mismatches: %d" % problems)
    return problems


def main():
    game = sys.argv[1]
    run = sys.argv[2]
    if game == "sokoban":
        module = load_module("make_session_sokoban.py")
        bad = check_readbacks(run, "sokoban", "board", "hash", sokoban_hash, "Sokoban")
        table = [
            ("g46-assert-box-list", "BoxList", module.PUSH_WIN.box_list()),
            ("g47-assert-hash", "BoardHash", module.PUSH_WIN_HASH),
            ("g89-assert-box-list", "BoxList", module.L1_WIN.box_list()),
            ("g90-assert-hash", "BoardHash", module.L1_WIN_HASH),
            ("g97-assert-box-list", "BoxList", module.L1_AFTER_UNDO.box_list()),
            ("g98-assert-hash", "BoardHash", module.L1_UNDO_HASH),
            ("g127-assert-dead-list", "DeadlockList", module.CORNER_AFTER.dead_list()),
            ("g131-assert-hash", "BoardHash", module.CORNER_AFTER_HASH),
            ("g115-assert-hash", "BoardHash", module.BLOCKED_RUN.board_hash()),
            ("g142-assert-last-hook", "LastHookSteps", module.AUTO2_ACCEPT2),
            ("g149-assert-last-hook-3", "LastHookSteps", module.AUTO2_ACCEPT3),
            ("g150-assert-steps-5", "Steps", module.AUTO2.steps),
        ]
        bad += check_assertion_literals(run, table, "Sokoban")
    elif game == "bomberman":
        module = load_module("make_session_bomberman.py")
        bad = check_readbacks(run, "bomberman", "field", "grid_hash", bomberman_hash, "Bomberman")
        table = [
            ("g73-assert-blast", "LastBlast", module.BOMB1_BLAST),
            ("g79-assert-grid-hash", "GridHash", module.BOMB1.grid_hash()),
            ("g85-assert-blast", "LastBlast", module.CORRIDOR_BLAST),
            ("g86-assert-blast-count", "LastBlastCount", len(module.CORRIDOR_SIM.last_blast)),
            ("g93-assert-hash", "GridHash", module.CORRIDOR_SIM.grid_hash()),
            ("g109-assert-blast", "LastBlast", module.CHAIN_BLAST),
            ("g110-assert-blast-count", "LastBlastCount", len(module.CHAIN_SIM.last_blast)),
            ("g114-assert-enemy-list", "EnemyList", module.CHASE_LIST3),
            ("g115-assert-unit-hash", "UnitHash", module.CHASE_HASH3),
            ("g117-assert-enemy-list", "EnemyList", module.CHASE_LIST4),
            ("g158-assert-blast", "LastBlast", module.WIN_BLAST),
            ("g167-assert-hash", "GridHash", module.WIN.grid_hash()),
            ("g172-assert-last-hook", "LastHookSteps", module.TICK_ACCEPT2),
            ("g174-assert-bomb-fuse", "BombList", module.TICK_SIM.bomb_list()),
        ]
        bad += check_assertion_literals(run, table, "Bomberman")
    else:
        sys.exit("unknown game %r" % game)
    print("TOTAL RECOMPUTATION MISMATCHES: %d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
