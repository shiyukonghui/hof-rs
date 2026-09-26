#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103: the post-hoc recomputation of one game's evidence.

    python recompute_readbacks.py <run-dir> <expectations.json> <game>

It deliberately does NOT import the session generator and does not look at
`report.json`. It reads only what the run itself wrote:

  * every `*.json` response file in the run directory, one per call;
  * the `running_game_assert_node_state` answers, which carry `actual`,
    `expected`, `operator` and `passed`;
  * the `running_game_execute_gdscript` answers, which carry the payload's own
    `Dump()` line.

and recomputes, with its **own** code:

  1. **the assertion literals.** Every assertion's `expected` is compared with the
     `expected` the generator recorded in `expectations.json`. That is what makes
     "every literal came from the Python second implementation" a checkable
     statement instead of a claim.
  2. **the map hash** of Tower Defense, from the ASCII grid the payload printed,
     with its own multiply-31 chain (ground 2 / path 1 / spawn 4 / exit 5).
  3. **the path hash** of Tower Defense, by walking the printed grid again with
     its own walk (right, down, left, up; never back the way it came).
  4. **the city hash and the world hash** of Missile Command, from the printed
     `city_list` / `incoming` / `interceptors` / `blasts` / `score` / `wave` /
     `steps` with its own multiply-31 chain.
  5. **the hash of the printed board/list against the payload's own hash field**,
     so "the hash the game reported is a function of the state it printed" is not
     taken on trust.
"""

import glob
import io
import json
import os
import sys

MASK32 = 0xFFFFFFFF


def sign32(value):
    value &= MASK32
    return value - 0x100000000 if value >= 0x80000000 else value


def parse_args(directory):
    """tag -> the text payload of that call's answer (the JSON inside `content`)."""
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


def recompute_path(rows):
    rows = list(rows)
    start = None
    for row_index, row in enumerate(rows):
        for col_index, ch in enumerate(row):
            if ch == 'S':
                start = (col_index, row_index)
    if start is None:
        return None
    order = ((1, 0), (0, 1), (-1, 0), (0, -1))
    col, row = start
    previous = (-1, -1)
    path = []
    for _ in range(len(rows) * len(rows[0]) + 4):
        path.append((col, row))
        if rows[row][col] == 'E':
            break
        moved = False
        for dc, dr in order:
            nc, nr = col + dc, row + dr
            if not (0 <= nr < len(rows) and 0 <= nc < len(rows[0])):
                continue
            if (nc, nr) == previous or rows[nr][nc] not in '#SE':
                continue
            previous, col, row = (col, row), nc, nr
            moved = True
            break
        if not moved:
            break
    return path


def dump_fields(result):
    """The payload's `Dump()` line as a key -> text map.

    Only the head is used: the trailing `last=<LastEvent>` is itself a sentence of
    `key=value` fragments, and one of them can carry the same key as a real field
    (`MissileCommandGame.StepFrames`'s readback says `incoming=0`). Splitting the
    whole line would let that overwrite the real `incoming=<list>`, which is
    exactly what the first version of this recomputation did.
    """
    fields = {}
    head = result.split(" last=")[0]
    for part in head.split(" "):
        if "=" in part:
            key, _, value = part.partition("=")
            fields[key] = value
    return fields


def missiles(text):
    out = []
    for item in (text or "").split("|"):
        item = item.strip()
        if not item:
            continue
        fields = [int(field) for field in item.split(",")]
        if len(fields) != 8:
            raise SystemExit("FATAL: a missile record has %d field(s): %r" % (len(fields), item))
        out.append(fields)
    return out


def main():
    directory = sys.argv[1]
    expectations_path = sys.argv[2]
    game = sys.argv[3]
    answers = parse_args(directory)
    with io.open(expectations_path, encoding="utf-8") as handle:
        expectations = json.load(handle)

    mismatches = 0
    checked = 0
    print("== %s : %d response file(s) in %s" % (game, len(answers), directory))

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
            # The one assertion this session declares as a boundary: it reads a
            # property that does not exist, so the *expected* answer is the -32001
            # refusal, not a comparison.
            if entry.get("declared_boundary") and (answer.get("__error__") or {}).get("code") == -32001:
                declared += 1
                print("   DECLARED %-34s -32001 %s" % (entry["tag"], (answer["__error__"]).get("message")))
                continue
            print("   ERROR    %-34s %s" % (entry["tag"], answer))
            mismatches += 1
            continue
        checked += 1
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

    # --- 2..5. the payload's own hashes ------------------------------------------
    hash_checks = 0
    for tag, answer in sorted(answers.items()):
        if not isinstance(answer, dict):
            continue
        result = answer.get("result")
        if not isinstance(result, str):
            continue
        if game == "towerdefense" and "map=" in result and "path_hash=" in result:
            fields = dump_fields(result)
            rows = fields.get("map", "").split("/")
            if len(rows) >= 2 and all(rows):
                value = 0
                for row in rows:
                    for ch in row:
                        weight = 1 if ch == '#' else 4 if ch == 'S' else 5 if ch == 'E' else 2
                        value = sign32(value * 31 + weight)
                reported = int(fields["map_hash"])
                print("   map      %-22s recomputed=%d reported=%d %s"
                      % (tag, value, reported, "OK" if value == reported else "MISMATCH"))
                mismatches += 0 if value == reported else 1
                hash_checks += 1
                path = recompute_path(rows)
                if path is not None:
                    path_value = 0
                    for col, row in path:
                        path_value = sign32(path_value * 31 + row * len(rows[0]) + col)
                    reported_len = int(fields["path_len"])
                    reported_hash = int(fields["path_hash"])
                    ok = path_value == reported_hash and len(path) == reported_len
                    print("   path     %-22s recomputed len=%d hash=%d reported len=%d hash=%d %s"
                          % (tag, len(path), path_value, reported_len, reported_hash,
                             "OK" if ok else "MISMATCH"))
                    mismatches += 0 if ok else 1
                    hash_checks += 1
        if game == "missilecommand" and "city_hash=" in result and "world_hash=" in result:
            fields = dump_fields(result)
            cities = [1 if flag == "1" else 0 for flag in fields.get("city_list", "").split("|")] \
                if fields.get("city_list") else []
            city_hash = 0
            for flag in cities:
                city_hash = sign32(city_hash * 31 + flag)
            ok = city_hash == int(fields["city_hash"])
            print("   city     %-22s recomputed=%d reported=%s %s"
                  % (tag, city_hash, fields["city_hash"], "OK" if ok else "MISMATCH"))
            mismatches += 0 if ok else 1
            hash_checks += 1

            world = 0
            for flag in cities:
                world = sign32(world * 31 + flag)
            for m in missiles(fields.get("incoming", "")):
                world = sign32(world * 31 + m[0])
                world = sign32(world * 31 + m[1])
                world = sign32(world * 31 + m[4])
            for m in missiles(fields.get("interceptors", "")):
                world = sign32(world * 31 + m[0])
                world = sign32(world * 31 + m[1])
                world = sign32(world * 31 + m[4])
            for blast in missiles(fields.get("blasts", "")):
                world = sign32(world * 31 + blast[0])
                world = sign32(world * 31 + blast[1])
                world = sign32(world * 31 + blast[2])
            world = sign32(world * 31 + int(fields["score"]))
            world = sign32(world * 31 + int(fields["wave"]))
            world = sign32(world * 31 + int(fields["steps"]))
            ok = world == int(fields["world_hash"])
            print("   world    %-22s recomputed=%d reported=%s %s"
                  % (tag, world, fields["world_hash"], "OK" if ok else "MISMATCH"))
            mismatches += 0 if ok else 1
            hash_checks += 1

    print("   assertions checked : %d" % checked)
    print("   hash checks        : %d" % hash_checks)
    print("   TOTAL RECOMPUTATION MISMATCHES: %d" % mismatches)
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
