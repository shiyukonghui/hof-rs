#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TASK-116 fix D2: add the InputMap actions the game code already reads.

The defect: `BombermanGame.cs:1155` reads `Input.IsActionPressed("bomb_left")` and
`SokobanGame.cs:937` reads `"soko_left"`, and neither action exists in the project's
`[input]` section.  Godot's InputMap then has no such action, so those keys can never
do anything -- half the directions are simply missing.

This script appends a well-formed action block to `[input]` of one project.godot,
in exactly the byte layout Godot itself writes (copied from a sibling action in the
same file: same field order, same indentation, same `Object(InputEventKey, ...)`
form).  It refuses to touch a name that is already declared, and it can be run in a
dry-run mode that only prints the block.
"""

import io
import os
import re
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
PROJECTS = os.path.join(ROOT, "projects")

TEMPLATE = """{name}={{
"deadzone": 0.2,
"events": [Object(InputEventKey,
"resource_local_to_scene": false,
"resource_name": "",
"device": 16,
"window_id": 0,
"alt_pressed": false,
"shift_pressed": false,
"ctrl_pressed": false,
"meta_pressed": false,
"pressed": true,
"keycode": {keycode},
"physical_keycode": 0,
"key_label": 0,
"unicode": 0,
"location": 0,
"echo": false,
"script": null
)]
}}
"""


def read(path):
    for enc in ("utf-8", "utf-8-sig"):
        try:
            return io.open(path, encoding=enc).read()
        except Exception:
            continue
    return None


def declare(game, name, keycode, apply):
    path = os.path.join(PROJECTS, game, "project.godot")
    txt = read(path)
    if txt is None:
        raise SystemExit("cannot read %s" % path)
    if re.search(r"^%s=\{" % re.escape(name), txt, re.M):
        print("skip %s: `%s` is already declared" % (game, name))
        return False
    m = re.search(r"\[input\]\n", txt)
    if not m:
        # a project with no [input] section at all: append one
        block = "[input]\n" + TEMPLATE.format(name=name, keycode=keycode)
        new = txt.rstrip("\n") + "\n\n" + block
    else:
        start = m.end()
        nxt = re.search(r"\n\[[a-z_/]+\]\n", txt[start:])
        insert_at = start + (nxt.start() + 1 if nxt else len(txt[start:]))
        block = TEMPLATE.format(name=name, keycode=keycode)
        # keep exactly one trailing newline before the next section
        new = txt[:insert_at] + block + txt[insert_at:]
    if apply:
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(new)
        print("+ %s/project.godot : %s=%d" % (game, name, keycode))
    else:
        print("would add to %s/project.godot:\n%s" % (game, TEMPLATE.format(name=name, keycode=keycode)))
    return True


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--apply"]
    if len(args) < 3:
        print(__doc__)
        print("usage: add_input_action.py <game> <action> <keycode> [--apply]")
        raise SystemExit(2)
    declare(args[0], args[1], int(args[2]), apply)
