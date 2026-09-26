#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-104: the post-hoc recomputation of one game's evidence.

    python recompute_readbacks.py <run-dir> <expectations.json> <game>

It deliberately does NOT import the session generator and does not look at
`report.json`. It reads only what the run itself wrote:

  * every `*.json` response file in the run directory, one per call;
  * the `call-index.txt` the driver writes, which fixes the call order;
  * the `running_game_assert_node_state` answers, which carry `actual`,
    `expected`, `operator` and `passed`;
  * the `running_game_execute_gdscript` answers, which carry the payload's own
    `Dump()` line or its own action readback.

and recomputes, with its **own** code:

  1. **the assertion literals.** Every assertion's `expected` is compared with the
     `expected` the generator recorded in `expectations.json`. That is what makes
     "every literal came from the Python second implementation" a checkable
     statement instead of a claim.
  2. **R-Type's world hash** from the printed `player` / `lives` / `score` /
     `wave` / `wave_left` and the three printed lists, with its own multiply-31
     chain.
  3. **Puzzle Bobble's board hash** from the printed board, and **Puzzle Bobble's
     initial board** from the same linear congruential generator and the same
     stabilising loop the payload documents -- so "the board the game started
     with is the one the rule produces" is not taken on trust.
  4. **Lunar Lander's world hash** from the printed position, velocity, attitude,
     fuel and step count.
  5. **Lunar Lander's whole trajectory**: the script replays the run's own call
     sequence in the order `call-index.txt` records, applying the same integer
     burn / gravity / integrate / ground-test rules, and compares EVERY printed
     checkpoint against its own integration. That is the independent
     recomputation of the integral trajectory the task asks for.
"""

import glob
import io
import json
import os
import sys

MASK32 = 0xFFFFFFFF

# --- Lunar Lander's integer tables, re-written here from the rules -------------
LL_TX = [0, 2, 3, 4, 3, 2, 0, -2, -3, -4, -3, -2]
LL_TY = [-4, -3, -2, 0, 2, 3, 4, 3, 2, 0, -2, -3]
LL_GROUND = 560
LL_HALF_H = 8
LL_FIELD_W = 800

# --- Puzzle Bobble's generator constants, re-written here from the rules -------
PB_INIT_SEED = 20251040
PB_FILL_ROWS = 4
PB_COLS = 8
PB_ROWS = 12
PB_COLORS = 6


def sign32(value):
    value &= MASK32
    return value - 0x100000000 if value >= 0x80000000 else value


def parse_args(directory):
    """tag -> the parsed payload of that call's answer."""
    out = {}
    for path in sorted(glob.glob(os.path.join(directory, "*.json"))):
        name = os.path.basename(path)
        if name.startswith(("import", "session", "call-index", "ledger")):
            continue
        tag = name[:-len(".json")]
        if tag.endswith(".request"):
            continue
        try:
            with io.open(path, encoding="utf-8-sig") as handle:
                body = json.load(handle)
        except Exception as exc:  # noqa: BLE001 - reported, never swallowed
            out[tag] = {"__parse_error__": str(exc)}
            continue
        if "error" in body:
            out[tag] = {"__error__": body["error"]}
            continue
        result = body.get("result") or {}
        content = result.get("content") or []
        if not content:
            out[tag] = {}
            continue
        text = content[0].get("text", "")
        try:
            out[tag] = json.loads(text)
        except ValueError:
            out[tag] = {"__text__": text}
    return out


def call_order(directory):
    path = os.path.join(directory, "call-index.txt")
    if not os.path.isfile(path):
        return []
    order = []
    for line in io.open(path, encoding="utf-8-sig"):
        line = line.strip()
        if not line:
            continue
        order.append(line.split("|")[0])
    return order


def dump_fields(result):
    """The payload's `Dump()` line as a key -> text map.

    Only the head is used: the trailing `last=<LastEvent>` is itself a sentence of
    `key=value` fragments, and one of them can carry the same key as a real field.
    Splitting the whole line would let that overwrite the real field (TASK-103's
    R-1 defect).
    """
    fields = {}
    head = result.split(" last=")[0]
    for part in head.split(" "):
        if "=" in part:
            key, _, value = part.partition("=")
            fields[key] = value
    return fields


def grab(text, key):
    """The value of ` key=` in an action readback, or None."""
    marker = " " + key + "="
    index = text.find(marker)
    if index < 0:
        if text.startswith(key + "="):
            rest = text[len(key) + 1:]
        else:
            return None
    else:
        rest = text[index + len(marker):]
    return rest.split(" ")[0]


def pairs(text):
    out = []
    for item in (text or "").split("|"):
        item = item.strip()
        if not item:
            continue
        out.append([int(field) for field in item.split(",")])
    return out


def board_of(text):
    """Puzzle Bobble's printed board -> the flat list of colour indices."""
    cells = []
    for row in (text or "").split("/"):
        for ch in row:
            cells.append(-1 if ch == '.' else int(ch))
    return cells


def pb_initial_board():
    board = [-1] * (PB_COLS * PB_ROWS)
    seed = PB_INIT_SEED
    for row in range(PB_FILL_ROWS):
        for col in range(PB_COLS):
            seed = (seed * 1103515245 + 12345) % (1 << 31)
            board[row * PB_COLS + col] = (seed >> 16) % PB_COLORS
    for row in range(PB_FILL_ROWS):
        for col in range(PB_COLS):
            index = row * PB_COLS + col
            for _ in range(PB_COLORS):
                value = board[index]
                bad = False
                if col >= 2 and board[index - 1] == value and board[index - 2] == value:
                    bad = True
                if row >= 2 and board[index - PB_COLS] == value and board[index - 2 * PB_COLS] == value:
                    bad = True
                if not bad:
                    break
                board[index] = (value + 1) % PB_COLORS
    return board


def pb_board_string(board):
    rows = []
    for row in range(PB_ROWS):
        rows.append("".join('.' if board[row * PB_COLS + col] < 0 else str(board[row * PB_COLS + col])
                            for col in range(PB_COLS)))
    return "/".join(rows)


class LLReplay(object):
    """The payload's rules, re-implemented for the recomputation, driven by the
    run's own call sequence and compared against every checkpoint it printed."""

    def __init__(self):
        self.pin()

    def pin(self, lx=400, ly=100, vx=0, vy=0, angle=0, fuel=500, thrust_on=False):
        self.lx, self.ly, self.vx, self.vy = lx, ly, vx, vy
        self.angle, self.fuel, self.steps = angle, fuel, 0
        self.thrust_on = thrust_on
        self.over = False
        self.min_vy = self.max_vy = vy

    def tick(self):
        if self.over:
            return
        self.steps += 1
        if self.thrust_on and self.fuel >= 1:
            self.vx += LL_TX[self.angle]
            self.vy += LL_TY[self.angle]
            self.fuel -= 1
        self.vy += 1
        self.lx += self.vx
        self.ly += self.vy
        self.min_vy = min(self.min_vy, self.vy)
        self.max_vy = max(self.max_vy, self.vy)
        if self.ly + LL_HALF_H >= LL_GROUND or self.lx < 0 or self.lx >= LL_FIELD_W:
            self.over = True


def replay_lunarlander(answers, order, report):
    sim = LLReplay()
    compared = 0
    mismatches = 0

    def compare(tag, text, keys):
        nonlocal compared, mismatches
        compared += 1
        for key, attribute in keys:
            reported = grab(text, key)
            if reported is None:
                continue
            mine = getattr(sim, attribute)
            if int(reported) != int(mine):
                mismatches += 1
                report("   REPLAY   %-30s %s: printed=%s recomputed=%s" % (tag, key, reported, mine))

    for tag in order:
        answer = answers.get(tag)
        if not isinstance(answer, dict):
            continue
        text = answer.get("result")
        if not isinstance(text, str):
            continue
        if text.startswith("forced "):
            pos = grab(text, "pos").split(",")
            vel = grab(text, "vel").split(",")
            sim.pin(lx=int(pos[0]), ly=int(pos[1]), vx=int(vel[0]), vy=int(vel[1]),
                    angle=int(grab(text, "angle")) // 30, fuel=int(grab(text, "fuel")),
                    thrust_on=grab(text, "thrust_on") == "True")
            continue
        if text.startswith("thrust_on="):
            sim.thrust_on = grab(text, "thrust_on") == "True"
            continue
        if text.startswith("burn "):
            # one impulse: applied only when the flight is on and the tank can pay
            if not sim.over and sim.fuel >= 1:
                sim.vx += LL_TX[sim.angle]
                sim.vy += LL_TY[sim.angle]
                sim.fuel -= 1
            compare(tag, text, (("vx", "vx"), ("vy", "vy"), ("fuel", "fuel")))
            continue
        if text.startswith("rotated "):
            sim.angle = int(grab(text, "angle")) // 30
            continue
        if text.startswith("stepframes "):
            applied = int(grab(text, "applied"))
            for _ in range(applied):
                if sim.over:
                    break
                sim.tick()
            compare(tag, text, (("steps", "steps"), ("x", "lx"), ("y", "ly"),
                                ("vx", "vx"), ("vy", "vy"), ("fuel", "fuel"),
                                ("min_vy", "min_vy"), ("max_vy", "max_vy")))
            continue
    return compared, mismatches


def main():
    directory = sys.argv[1]
    expectations_path = sys.argv[2]
    game = sys.argv[3]
    answers = parse_args(directory)
    order = call_order(directory)
    with io.open(expectations_path, encoding="utf-8") as handle:
        expectations = json.load(handle)

    mismatches = 0

    def report(line):
        print(line)

    print("== %s : %d response file(s) in %s" % (game, len(answers), directory))
    print("   call order entries : %d" % len(order))

    # --- 1. the literals ----------------------------------------------------------
    literal_ok = 0
    declared = 0
    for entry in expectations:
        answer = answers.get(entry["tag"])
        if answer is None:
            print("   MISSING  %-34s (no response file)" % entry["tag"])
            mismatches += 1
            continue
        if "__error__" in answer or "__parse_error__" in answer:
            if entry.get("declared_boundary") and (answer.get("__error__") or {}).get("code") == -32001:
                declared += 1
                print("   DECLARED %-34s -32001 %s" % (entry["tag"], (answer["__error__"]).get("message")))
                continue
            print("   ERROR    %-34s %s" % (entry["tag"], answer))
            mismatches += 1
            continue
        expected = answer.get("expected")
        if expected != entry["expected"]:
            print("   LITERAL  %-34s manifest=%r answer=%r" % (entry["tag"], entry["expected"], expected))
            mismatches += 1
        elif not answer.get("passed"):
            print("   FAILED   %-34s expected=%r actual=%r" % (entry["tag"], expected, answer.get("actual")))
            mismatches += 1
        else:
            literal_ok += 1
    print("   literals : %d/%d aligned with the generator's own expectations and passed"
          % (literal_ok, len(expectations) - declared))
    if declared:
        print("   declared : %d boundary assertion(s) whose expected answer is the -32001 refusal" % declared)

    # --- 2..4. the payload's own hashes -------------------------------------------
    hash_checks = 0
    for tag in sorted(answers):
        answer = answers[tag]
        if not isinstance(answer, dict):
            continue
        result = answer.get("result")
        if not isinstance(result, str):
            continue
        fields = dump_fields(result) if " last=" in result else {}
        if game == "rtype" and "state_hash" in fields and "enemy_list" in fields:
            player = [int(v) for v in fields["player"].split(",")]
            value = 0
            for item in (player[0], player[1], int(fields["lives"]), int(fields["score"]),
                         int(fields["wave"]), int(fields["wave_left"])):
                value = sign32(value * 31 + item)
            for x, y, cd in pairs(fields.get("enemy_list")):
                value = sign32(value * 31 + x)
                value = sign32(value * 31 + y)
                value = sign32(value * 31 + cd)
            for x, y in pairs(fields.get("bullet_list")):
                value = sign32(value * 31 + x)
                value = sign32(value * 31 + y)
            for x, y in pairs(fields.get("ebullet_list")):
                value = sign32(value * 31 + x)
                value = sign32(value * 31 + y)
            reported = int(fields["state_hash"])
            hash_checks += 1
            if value != reported:
                print("   hash     %-22s recomputed=%d reported=%d MISMATCH" % (tag, value, reported))
                mismatches += 1
        if game == "puzzlebobble" and "board_hash" in fields:
            value = 0
            for cell in board_of(fields["board"]):
                value = sign32(value * 31 + (cell + 1))
            reported = int(fields["board_hash"])
            hash_checks += 1
            if value != reported:
                print("   hash     %-22s recomputed=%d reported=%d MISMATCH" % (tag, value, reported))
                mismatches += 1
        if game == "lunarlander" and "state_hash" in fields:
            pos = [int(v) for v in fields["pos"].split(",")]
            vel = [int(v) for v in fields["vel"].split(",")]
            value = 0
            for item in (pos[0], pos[1], vel[0], vel[1], int(fields["angle_index"]),
                         int(fields["fuel"]), int(fields["steps"])):
                value = sign32(value * 31 + item)
            reported = int(fields["state_hash"])
            hash_checks += 1
            if value != reported:
                print("   hash     %-22s recomputed=%d reported=%d MISMATCH" % (tag, value, reported))
                mismatches += 1
    print("   hash checks        : %d" % hash_checks)

    # --- Puzzle Bobble: the initial board is a function of the rule ---------------
    if game == "puzzlebobble":
        recomputed = pb_initial_board()
        value = 0
        for cell in recomputed:
            value = sign32(value * 31 + (cell + 1))
        answer = answers.get("g13-readback-t0")
        text = answer.get("result") if isinstance(answer, dict) else None
        if isinstance(text, str):
            fields = dump_fields(text)
            same_board = fields.get("board", "") == pb_board_string(recomputed)
            same_hash = int(fields.get("board_hash", "-999999")) == value
            same_bubbles = int(fields.get("bubbles", "-1")) == len([c for c in recomputed if c >= 0])
            print("   initial  %-22s board %s  hash %s  bubbles %s"
                  % ("g13-readback-t0", "OK" if same_board else "MISMATCH",
                     "OK" if same_hash else "MISMATCH", "OK" if same_bubbles else "MISMATCH"))
            if not (same_board and same_hash and same_bubbles):
                mismatches += 1
            hash_checks += 1
        else:
            print("   initial  g13-readback-t0 MISSING")
            mismatches += 1

    # --- Lunar Lander: the whole trajectory, replayed from the run's own calls ----
    if game == "lunarlander":
        compared, bad = replay_lunarlander(answers, order, report)
        print("   replay   checkpoints compared=%d  mismatches=%d" % (compared, bad))
        mismatches += bad

    print("   assertions checked : %d" % literal_ok)
    print("   TOTAL RECOMPUTATION MISMATCHES: %d" % mismatches)
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
