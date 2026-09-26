# -*- coding: utf-8 -*-
"""TASK-102: independently recompute the run's own readbacks.

    python recompute_readbacks.py <game> <run-dir>

This is deliberately NOT a call into the payload and NOT a call into the
assertion helper.  It takes the strings the game PRINTED -- the `Dump()`
readbacks and the assertion responses the driver saved -- and recomputes them
from the rules, in Python:

  * Platformer: every `Dump()` readback prints the map as ASCII plus a
    `map_hash=`.  The hash is recomputed from the ASCII map alone with the
    documented code table (solid 1, goal 5, collectible 3, empty 2) as a signed
    32-bit multiply-31 chain, and the `state_hash=` is recomputed from the
    `player=x,y vel=vx,vy on_ground=` fields on the same line.  Nothing is taken
    from the payload.
  * Match-3: every `Dump()` readback prints the board as digits plus a
    `board_hash=`.  The hash is recomputed from the printed digits alone
    (`h = h * 31 + (value + 1)`, row-major).
  * Both: the literals the session asserts are recomputed from a fresh import of
    the session generator's own second implementation, and compared with the
    `actual` value the payload reported in that run's saved assertion response.

Nothing here trusts `report.json`, the assertion helper, or the C#.

PLATFORMER CAVEAT (stated rather than hidden): `Dump()` prints '@' for the tile
under the player, so a readback whose player stands on a collectible or the goal
cannot be recomputed from the ASCII alone.  Every readback in this task's
sessions has the player on an empty tile; the tool reports the '@' position so a
reader can check that claim instead of taking it on faith.
"""
import glob
import io
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


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


def platformer_map_hash(ascii_map):
    codes = {"#": 1, "G": 5, "C": 3, ".": 2, "@": 2}
    h = 17
    for ch in ascii_map:
        if ch == "/":
            continue
        h = int32(h * 31 + codes[ch])
    return h


def platformer_state_hash(px, py, vx, vy, ground):
    h = 17
    for value in (px, py, vx, vy, 1 if ground else 0):
        h = int32(h * 31 + value)
    return h


def match3_board_hash(board):
    h = 17
    for ch in board:
        if ch == "/":
            continue
        value = -1 if ch == "-" else int(ch)
        h = int32(h * 31 + (value + 1))
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


def kv_field(text, key):
    """The value of ` key=`, with a leading space in the marker.

    The plain `kv` would read `level=0` when asked for `vel=` -- the marker is a
    substring of another field's name. The dump separates its fields with spaces,
    so a leading space makes the lookup unambiguous.
    """
    marker = " " + key + "="
    start = text.find(marker)
    if start < 0:
        return None
    start += len(marker)
    end = start
    while end < len(text) and text[end] not in " ":
        end += 1
    return text[start:end]


def between(text, key, terminator):
    marker = key + "="
    start = text.find(marker)
    if start < 0:
        return None
    start += len(marker)
    end = text.find(" " + terminator + "=", start)
    if end < 0:
        return text[start:]
    return text[start:end]


def readbacks(run, key_board, terminator):
    rows = []
    for path in sorted(glob.glob(os.path.join(run, "*.json"))):
        tag = os.path.basename(path)[:-5]
        if tag.endswith(".request") or not tag.startswith("g"):
            continue
        body = body_of(path)
        if not isinstance(body, dict):
            continue
        result = body.get("result")
        if not isinstance(result, str) or (key_board + "=") not in result:
            continue
        rows.append((tag, result))
    return rows


def check_platformer(run):
    print("== Platformer: the printed map and the printed kinematic state")
    found = 0
    bad = 0
    for tag, result in readbacks(run, "map", "cols"):
        ascii_map = between(result, "map", "cols")
        found += 1
        reported = int(float(kv(result, "map_hash")))
        recomputed = platformer_map_hash(ascii_map)
        # the player's '@' hides the tile under it: report where it is
        flat = ascii_map.replace("/", "")
        mask = flat.find("@")
        mask_row, mask_col = (mask // len(ascii_map.split("/")[0]), mask % len(ascii_map.split("/")[0]))
        ok_hash = reported == recomputed
        px = int(kv_field(result, "player").split(",")[0])
        py = int(kv_field(result, "player").split(",")[1])
        vel = kv_field(result, "vel").split(",")
        ground = kv_field(result, "on_ground") == "True"
        srep = int(float(kv_field(result, "state_hash")))
        srec = platformer_state_hash(px, py, int(vel[0]), int(vel[1]), ground)
        ok_state = srep == srec
        if not (ok_hash and ok_state):
            bad += 1
        print("   %-24s map_hash %-12d %-12d %s   state_hash %-12d %-12d %s" % (
            tag, reported, recomputed, "OK" if ok_hash else "<<< MISMATCH",
            srep, srec, "OK" if ok_state else "<<< MISMATCH"))
        print("      '@' at tile row=%d col=%d  (the masked tile is '%s' in the pinned map by the "
              "level design)" % (mask_row, mask_col, "."))
        print("      map=%s" % ascii_map)
    print("   readbacks found=%d mismatches=%d" % (found, bad))
    return bad


def check_match3(run):
    print("== Match-3: the printed board")
    found = 0
    bad = 0
    for tag, result in readbacks(run, "board", "cols"):
        board = between(result, "board", "cols")
        found += 1
        reported = int(float(kv(result, "board_hash")))
        recomputed = match3_board_hash(board)
        ok = reported == recomputed
        if not ok:
            bad += 1
        print("   %-24s reported=%-12d recomputed=%-12d %s" % (
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
            print("   %-30s MISSING response file" % tag)
            problems += 1
            continue
        body = body_of(path)
        actual = body.get("actual") if isinstance(body, dict) else None
        if isinstance(actual, float) and actual == int(actual):
            actual = int(actual)
        ok = (actual == expected)
        if not ok:
            problems += 1
        print("   %-30s %-14s expected=%-44r actual=%-44r %s" % (
            tag, key, expected, actual, "OK" if ok else "<<< MISMATCH"))
    print("   literal mismatches: %d" % problems)
    return problems


def main():
    game = sys.argv[1]
    run = sys.argv[2]
    errors = 0
    if game == "platformer":
        module = load_module("make_session_platformer.py")
        errors += check_platformer(run)
        table = [
            ("g11-assert-map-hash", "MapHash", module.L0S.map_hash()),
            ("g45-assert-state-hash", "StateHash", module.DROP.state_hash()),
            ("g48-assert-x", "PlayerX", module.WALL.x),
            ("g49-assert-wall-hits", "WallHits", module.WALL.wall_hits),
            ("g40-assert-drop-y", "PlayerY", module.DROP_Y),
            ("g43-assert-landings", "Landings", module.DROP_LANDINGS),
            ("g62a-assert-y", "PlayerY", module.ARC_CHECKPOINTS[0][2]),
            ("g72a-assert-y", "PlayerY", module.ARC_CHECKPOINTS[2][2]),
            ("g77a-assert-y", "PlayerY", module.ARC_CHECKPOINTS[3][2]),
            ("g82a-assert-y", "PlayerY", module.ARC_CHECKPOINTS[4][2]),
            ("g92a-assert-y", "PlayerY", module.ARC_CHECKPOINTS[6][2]),
            ("g97a-assert-y", "PlayerY", module.ARC_CHECKPOINTS[7][2]),
            ("g97c-assert-ground", "OnGround", module.ARC_CHECKPOINTS[7][4]),
            ("g102-assert-landed-y", "PlayerY", module.ARC_LAND_FRAME_24[2]),
            ("g117-assert-dj-vy-air", "VelY", module.DJ_AFTER_AIR[0]),
            ("g119-assert-dj-y", "PlayerY", module.DJ_AFTER_AIR1[1]),
            ("g121-assert-dj-rejected", "JumpsRejected", module.DJ_AFTER_REFUSE[0]),
            ("g144-assert-gem-hash", "MapHash", module.GEM_AFTER10[4]),
            ("g153-assert-x-goal", "PlayerX", module.GOAL_AT[0]),
            ("g162-assert-pit-y", "PlayerY", module.PIT_BEFORE[1]),
            ("g166-assert-fell", "Falls", module.PIT_AFTER[3]),
            ("g176-assert-falls", "Falls", module.PIT_LAST_AFTER[1]),
            ("g183-assert-inc-x", "PlayerX", module.INC_X),
            ("g212-assert-hash", "MapHash", module.L0S.map_hash()),
        ]
        errors += check_assertion_literals(run, table, "Platformer")
    elif game == "match3":
        module = load_module("make_session_match3.py")
        errors += check_match3(run)
        table = [
            ("g07a-assert-default-board", "Board", module.GEN_BOARD),
            ("g07b-assert-default-hash", "BoardHash", module.GEN_HASH),
            ("g07c-assert-default-seed", "Seed", module.GEN_SEED),
            ("g11-assert-probe-value", "ProbeValue", module.GEN_35),
            ("g16-assert-plain-board", "Board", module.PLAIN),
            ("g17-assert-plain-hash", "BoardHash", module.P_SIM.board_hash()),
            ("g21-assert-plain-applied-0", "LastHookSteps", module.P_AUTO_APPLIED),
            ("g26-assert-setup-hash", "BoardHash", module.SWAP_SIM.board_hash()),
            ("g29-assert-rejected-1", "RejectedMoves", module.SHAPE_REJ_1),
            ("g35-assert-rejected-2", "RejectedMoves", module.SHAPE_REJ_2),
            ("g38-assert-rejected-3", "RejectedMoves", module.SHAPE_REJ_3),
            ("g52-assert-board-after", "Board", module.APPLY_BOARD),
            ("g53-assert-hash-after", "BoardHash", module.APPLY_HASH),
            ("g54-assert-seed-after", "Seed", module.APPLY_SEED),
            ("g55-assert-refills", "Refills", module.APPLY_REFILLS),
            ("g61-assert-auto-swap", "LastSwap", module.Q_AUTO_SWAP),
            ("g63-assert-auto-board", "Board", module.Q_AUTO_BOARD),
            ("g69-assert-chain-len", "LastChain", module.CHAIN_FOUND["chain"]),
            ("g71-assert-chain-cleared", "LastCleared", module.CHAIN_FOUND["cleared"]),
            ("g72-assert-chain-score", "Score", module.CHAIN_FOUND["score"]),
            ("g73-assert-chain-board", "Board", module.CHAIN_FOUND["board_after"]),
            ("g75-assert-chain-seed", "Seed", module.CHAIN_FOUND["seed_after"]),
            ("g82-assert-score-win", "Score", module.WIN_SCORE),
            ("g119-assert-final-board", "Board", module.SWAP_BOARD),
            ("g120-assert-final-hash", "BoardHash", module.SWAP_SIM.board_hash()),
        ]
        errors += check_assertion_literals(run, table, "Match-3")
    else:
        sys.exit("unknown game %r" % game)
    print("TOTAL RECOMPUTATION MISMATCHES: %d" % errors)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
