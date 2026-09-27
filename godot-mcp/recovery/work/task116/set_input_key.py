#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TASK-116: rebind an existing InputMap action's key inside a project.godot.

Needed because the new *player* actions take the natural keys (Space to place,
Space to swap, F to flag) and the legacy headless-test actions
(`m3_auto_move`, `mc_auto_fire`, `td_auto_step`, `mine_flag_next`) were sitting on
exactly those keys.  A player pressing Space must not silently also advance the
auto-clock, so the test-only action moves to a key a player has no reason to press
(`G`), and the action itself is kept -- sessions that inject it **by name** (which
is what `tools/sessions/*.json` do) are unaffected.
"""

import io
import os
import re
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
PROJECTS = os.path.join(ROOT, "projects")


def read(path):
    for enc in ("utf-8", "utf-8-sig"):
        try:
            return io.open(path, encoding=enc).read()
        except Exception:
            continue
    return None


def rebind(game, action, keycode):
    path = os.path.join(PROJECTS, game, "project.godot")
    txt = read(path)
    if txt is None:
        raise SystemExit("cannot read %s" % path)
    m = re.search(r"^%s=\{(.*?)\n\}" % re.escape(action), txt, re.M | re.S)
    if not m:
        raise SystemExit("%s: action `%s` not declared" % (game, action))
    body = m.group(0)
    new_body, n = re.subn(r'"keycode": \d+', '"keycode": %d' % keycode, body, count=1)
    if n != 1:
        raise SystemExit("%s: `%s` has no keycode to rebind" % (game, action))
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(txt[:m.start()] + new_body + txt[m.end():])
    print("~ %s: %s keycode -> %d" % (game, action, keycode))


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        raise SystemExit(2)
    rebind(sys.argv[1], sys.argv[2], int(sys.argv[3]))
