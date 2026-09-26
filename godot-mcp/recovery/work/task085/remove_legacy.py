# -*- coding: utf-8 -*-
"""TASK-085 guarded removal of the dead M1 legacy unit.

`tools/project.cpp` + `tools/project.h` are the pre-TASK-002 B1 unit that
registered `project_get_info` / `project_get_settings`.  Both tools were migrated
into `tools/project_read_template.cpp` (`register_project_read_template_tools`,
called from `tools/registration.cpp` and `tests/test_mcp_server.cpp`), and
`register_project_tools` is called from nowhere in the module.

Evidence that the unit is stale:
  * every recorded read event of `tools/project.cpp` (7) and `tools/project.h`
    (4) falls in the M1 window t=1789997510201..1790007934789, long before the
    GDR-19 registry change; no later session ever opened it;
  * its handlers are `Variant(const Dictionary &, String &)` and it calls
    `MCPToolRegistry::register_tool` directly, both removed by GDR-19;
  * `tools/project.h` is included by `tools/project.cpp` only.

Guards: absolute literal paths, no wildcard, no `..`, must sit under the allowed
prefix, must be regular files; the manifest (path + bytes + sha256) is printed
BEFORE anything is removed, and each path is re-checked afterwards.

usage: python remove_legacy.py [--apply]
"""
import hashlib
import io
import os
import sys

ALLOW = r"H:\rebuild\godot\modules\mcp_server\tools"
TARGETS = [
    r"H:\rebuild\godot\modules\mcp_server\tools\project.cpp",
    r"H:\rebuild\godot\modules\mcp_server\tools\project.h",
]


def guard(p):
    if not p:
        raise SystemExit("empty path")
    if not os.path.isabs(p):
        raise SystemExit("not absolute: %s" % p)
    if "*" in p or "?" in p or ".." in p:
        raise SystemExit("wildcard or .. in: %s" % p)
    if not os.path.normcase(os.path.normpath(p)).startswith(os.path.normcase(os.path.normpath(ALLOW))):
        raise SystemExit("outside the allowed prefix: %s" % p)


def main():
    print("--- removal manifest ---")
    for p in TARGETS:
        guard(p)
        if not os.path.isfile(p):
            raise SystemExit("not a regular file: %s" % p)
        raw = io.open(p, "rb").read()
        print("  %s\n    bytes=%d sha256=%s" % (p, len(raw), hashlib.sha256(raw).hexdigest()))
    if "--apply" not in sys.argv:
        print("(dry run; pass --apply to remove)")
        return
    for p in TARGETS:
        os.remove(p)
    for p in TARGETS:
        print("  removed %s -> exists=%s" % (p, os.path.exists(p)))
        if os.path.exists(p):
            raise SystemExit("still present: %s" % p)


if __name__ == "__main__":
    main()
