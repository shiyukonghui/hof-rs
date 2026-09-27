#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TASK-116 fix D1: the shipped games had player input switched off.

The defect
----------
Every one of these games declares

    /// <summary>When false the ship ignores input (determinism rule: no polling by default).</summary>
    [Export] public bool PollInput = false;

and every `Input.IsActionPressed` / `IsActionJustPressed` call sits behind
`if (PollInput)`.  That was chosen for deterministic headless testing (D138's
"determinism rule": a fresh process must not move by itself), but its consequence
is that a *human* who launches the game gets a picture that ignores the keyboard
completely.  The gate measures exactly that: every declared action reports
`key_event=False action_state=False`.

The fix
-------
Flip the **field initialiser** to `true`, and keep every test-only path that
switches it off (`SetPollInput(false)`, `ForceTestState`, Reset-for-test) exactly
as it is.  Listening to the keyboard is not the same thing as moving by itself:
`AutoClock` / `AutoPlay` / `DriftSpeed` keep their deterministic defaults, so a
fresh process is still still until a key is pressed.

This script does the one-line replacement, rewrites the doc comment that claimed
"no polling by default", and prints a diff so the change is reviewable.  It never
touches a file outside projects/<game>/src/.
"""

import io
import os
import re
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
PROJECTS = os.path.join(ROOT, "projects")

DECL = re.compile(r"^(?P<indent>\s*)\[Export\]\s*public\s+bool\s+PollInput\s*=\s*(?P<val>true|false)\s*;(?P<tail>.*)$")

NEW_DOC = ("/// <summary>When true the game reads its player's keyboard. The test driver switches this\n"
           "/// OFF explicitly (<see cref=\"SetPollInput\"/>, <see cref=\"ForceTestState\"/>) when it needs\n"
           "/// a frozen, deterministic state; the deterministic defaults live in AutoClock / AutoPlay /\n"
           "/// DriftSpeed, not here (TASK-116 defect D1).</summary>")

OLD_DOC_HINTS = ("no polling by default", "ignores input", "determinism rule")


def read(path):
    for enc in ("utf-8", "utf-8-sig"):
        try:
            return io.open(path, encoding=enc).read()
        except Exception:
            continue
    return None


def main(apply):
    games = sorted(d for d in os.listdir(PROJECTS)
                   if os.path.isdir(os.path.join(PROJECTS, d))
                   and not d.startswith("_") and not d.startswith("mcp"))
    changed = []
    for g in games:
        sdir = os.path.join(PROJECTS, g, "src")
        for dirpath, _dn, fns in os.walk(sdir):
            for fn in sorted(fns):
                if not fn.endswith(".cs"):
                    continue
                p = os.path.join(dirpath, fn)
                txt = read(p)
                if txt is None:
                    print("!! cannot decode %s" % p)
                    continue
                lines = txt.splitlines(True)
                hit = None
                for i, line in enumerate(lines):
                    if DECL.match(line.rstrip("\r\n")) and DECL.match(line.rstrip("\r\n")).group("val") == "false":
                        hit = i
                        break
                if hit is None:
                    continue
                old = lines[hit]
                new = DECL.sub(lambda m: "%s[Export] public bool PollInput = true;%s"
                               % (m.group("indent"), m.group("tail")), old.rstrip("\r\n")) + "\n"
                out = list(lines)
                out[hit] = new
                # the doc comment directly above, if it still claims no polling
                j = hit - 1
                while j >= 0 and out[j].strip().startswith("///"):
                    j -= 1
                doc_start, doc_end = j + 1, hit - 1
                if doc_end >= doc_start:
                    doc = "".join(out[doc_start:doc_end + 1])
                    if any(h in doc for h in OLD_DOC_HINTS):
                        indent = re.match(r"^(\s*)", out[doc_start]).group(1)
                        out[doc_start:doc_end + 1] = [
                            (indent + l if l else l) + "\n" for l in NEW_DOC.split("\n")]
                changed.append((p, old.rstrip("\r\n"), new.rstrip("\r\n")))
                if apply:
                    with io.open(p, "w", encoding="utf-8", newline="") as fh:
                        fh.write("".join(out))
    for p, old, new in changed:
        print("%s\n  - %s\n  + %s" % (os.path.relpath(p, ROOT), old, new))
    print("\n%d file(s) %s" % (len(changed), "rewritten" if apply else "would change (dry run)"))
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
