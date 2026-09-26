# -*- coding: utf-8 -*-
"""task088: guarded deletion of the four variant-stale build objects.

Iron rule 3: destructive commands are refused by default. This one runs only if
every path

  * is absolute,
  * lives under the single whitelisted prefix H:\\rebuild\\godot\\bin\\obj\\,
  * is non-empty (a real file, not a directory),
  * contains no wildcard and no `..`,
  * is one of the four paths the TRACKED build script names
    (modules/mcp_server/scripts/mcp057_build_mono.cmd lines 130-142).

Every path is printed with its size before anything is removed. `--apply` is
required; without it the script is a dry run.

usage: python del_stale_objs.py [--apply]
"""
from __future__ import print_function
import io, os, sys

PREFIX = "H:\\rebuild\\godot\\bin\\obj\\"
TARGETS = [
    "bin\\obj\\modules\\mcp_server\\tests\\test_mcp_server.windows.editor.x86_64.obj",
    "bin\\obj\\tests\\test_main.windows.editor.x86_64.obj",
    "bin\\obj\\modules\\mcp_server\\mcp_trace.windows.editor.x86_64.obj",
    "bin\\obj\\modules\\mcp_server\\mcp_trace.windows.editor.x86_64.mono.obj",
]
ROOT = "H:\\rebuild\\godot"
BAD_CHARS = ("*", "?", "..")


def main():
    apply = "--apply" in sys.argv
    plan = []
    for rel in TARGETS:
        full = os.path.join(ROOT, rel)
        if any(c in full for c in BAD_CHARS):
            raise SystemExit("REFUSED: wildcard or parent traversal in %s" % full)
        if not os.path.isabs(full):
            raise SystemExit("REFUSED: not absolute: %s" % full)
        if not full.lower().startswith(PREFIX.lower()):
            raise SystemExit("REFUSED: outside the whitelisted prefix: %s" % full)
        plan.append(full)
    print("whitelist prefix : %s" % PREFIX)
    print("targets          : %d" % len(plan))
    for full in plan:
        if os.path.isfile(full):
            print("  PRESENT %10d  %s" % (os.path.getsize(full), full))
        else:
            print("  absent            %s" % full)
    if not apply:
        print("DRY RUN (pass --apply to remove the PRESENT ones)")
        return 0
    removed = 0
    for full in plan:
        if os.path.isfile(full):
            if os.path.isdir(full):
                raise SystemExit("REFUSED: %s is a directory" % full)
            os.remove(full)
            removed += 1
            print("  removed %s" % full)
    print("removed=%d" % removed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
