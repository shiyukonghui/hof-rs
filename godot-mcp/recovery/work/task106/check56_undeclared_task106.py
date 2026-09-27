#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-106: re-run the two TASK-105 acceptance checks that produced the `fail`,
with Snake's final run pointed at the TASK-106 re-run.

`check5_assertions.py` and `check6_undeclared.py` live in the TASK-105 verifier's
own `%TEMP%\\acc105\\` directory and hard-code the 20 final-run paths; this file is
the same logic with exactly one line changed (`snake` -> `runs\\snake\\snake-task106-r1`)
and both tallies printed together, so the next independent acceptance has a
ready-made entry point whose only difference is the path it is told to read.

It is deliberately a separate file rather than a patch of the verifier's scripts:
the verifier's copy is evidence of what it ran, and is left untouched.
"""
import collections
import glob
import io
import json
import os
import sys

REPO = r"F:\moonbit-hof-rs\godot-mcp"

FINAL = {
    "pong": r"runs\pong\pong-clean-task097",
    "breakout": r"runs\breakout\breakout-clean-task097",
    "snake": r"runs\snake\snake-task106-r1",              # <- the only change
    "tetris": r"runs\tetris\tetris-task096-r2",
    "spaceinvaders": r"runs\spaceinvaders\si-task097-r1",
    "asteroids": r"runs\asteroids\ast-task098-r2",
    "pacman": r"runs\pacman\pac-task098-r2",
    "frogger": r"runs\frogger\frog-task099-r1",
    "flappy": r"runs\flappy\flappy-task099-r2",
    "game2048": r"runs\game2048\2048-task100-r2",
    "minesweeper": r"runs\minesweeper\mine-task100-r2",
    "sokoban": r"runs\sokoban\soko-task101-r2",
    "bomberman": r"runs\bomberman\bomb-task101-r4",
    "platformer": r"runs\platformer\plat-task102-r2",
    "match3": r"runs\match3\m3-task102-r3",
    "towerdefense": r"runs\towerdefense\td-task103-r3",
    "missilecommand": r"runs\missilecommand\mc-task103-r3",
    "rtype": r"runs\rtype\rt-task104-r2",
    "puzzlebobble": r"runs\puzzlebobble\pb-task104-r1",
    "lunarlander": r"runs\lunarlander\ll-task104-r1",
}

DECLARED_KEYS = ("must fail", "must-fail", "boundary", "注定失败",
                 "intentionally", "expected to fail", "declared failure", "boundary call")


def declared_tags(game):
    tags = set()
    for path in glob.glob(os.path.join(REPO, "tools", "sessions", game, "*.json")):
        try:
            with io.open(path, encoding="utf-8-sig") as handle:
                doc = json.load(handle)
        except Exception:
            continue
        for call in doc.get("calls", []) or []:
            note = (call.get("note") or "").lower()
            tag = call.get("tag") or ""
            if any(key in note for key in DECLARED_KEYS):
                tags.add(tag)
    return tags


def body(path):
    try:
        with io.open(path, encoding="utf-8-sig") as handle:
            obj = json.load(handle)
    except Exception:
        return None
    try:
        parsed = json.loads(obj["result"]["content"][0]["text"])
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else None
    lines = []

    def say(text=""):
        print(text)
        lines.append(text)

    say("== check5 (assertion tallies in the FINAL run dirs, snake -> snake-task106-r1)")
    say("%-16s %8s %8s %8s  %s" % ("game", "passed", "failed", "errors", ""))
    tot = collections.Counter()
    for game, rel in FINAL.items():
        directory = os.path.join(REPO, rel)
        passed = failed = errors = 0
        fails = []
        for path in glob.glob(os.path.join(directory, "*.json")):
            if path.endswith(".request.json"):
                continue
            b = body(path)
            if not b:
                continue
            if "all_passed" in b:
                passed += int(b.get("passed") or 0)
                failed += int(b.get("failed") or 0)
                errors += int(b.get("errors") or 0)
                if b.get("failed"):
                    fails.append("%s(scenario failed=%s errors=%s)" % (
                        os.path.basename(path)[:-5], b.get("failed"), b.get("errors")))
            elif "passed" in b:
                if b.get("passed"):
                    passed += 1
                else:
                    failed += 1
                    fails.append("%s(node_state prop=%s exp=%s act=%s)" % (
                        os.path.basename(path)[:-5], b.get("property"),
                        b.get("expected"), b.get("actual")))
        tot["passed"] += passed
        tot["failed"] += failed
        tot["errors"] += errors
        say("%-16s %8d %8d %8d  %s" % (game, passed, failed, errors,
                                       "clean" if not fails else "FAILURES: " + "; ".join(fails)))
    say("")
    say("TOTAL passed=%d failed=%d errors=%d" % (tot["passed"], tot["failed"], tot["errors"]))

    say("")
    say("== check6 (undeclared failing assertions in the FINAL run dirs)")
    say("%-16s %-40s %-9s %s" % ("game", "tag", "declared?", "what"))
    say("-" * 120)
    undeclared = []
    for game, rel in FINAL.items():
        directory = os.path.join(REPO, rel)
        declared = declared_tags(game)
        for path in sorted(glob.glob(os.path.join(directory, "*.json"))):
            if path.endswith(".request.json"):
                continue
            tag = os.path.basename(path)[:-len(".json")]
            b = body(path)
            if not b:
                continue
            fails = []
            if b.get("all_passed") is False:
                for step in b.get("results", []) or []:
                    if step.get("type") == "assert" and step.get("passed") is False:
                        fails.append("scenario:%s eq %s -> %s" % (
                            step.get("property"), step.get("expected"), step.get("actual")))
            elif b.get("passed") is False:
                fails.append("node_state:%s eq %s -> %s" % (
                    b.get("property"), b.get("expected"), b.get("actual")))
            for what in fails:
                is_declared = ("must-fail" in tag) or (tag in declared)
                say("%-16s %-40s %-9s %s" % (game, tag, "YES" if is_declared else "NO", what))
                if not is_declared:
                    undeclared.append((game, rel, tag, what))
    say("")
    say("UNDECLARED failing assertions in final runs: %d" % len(undeclared))
    for item in undeclared:
        say("   %s" % (item,))
    say("")
    say("CHECK56_TASK106 %s" % ("OK" if not undeclared else "FAIL"))

    if out_path:
        with io.open(out_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(lines) + "\n")
    return 0 if not undeclared else 1


if __name__ == "__main__":
    sys.exit(main())
