# -*- coding: utf-8 -*-
"""task088 (5): the scratch Godot project the live traceability session runs on.

A ColorRect large enough that a colour change is a large pixel difference, so a
capture's `changed`/`changed_pixels` has an unambiguous meaning.

usage: python mk_live_proj.py
"""
from __future__ import print_function
import io, os, sys

PROJ = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task088\live-proj"


def w(rel, text):
    p = os.path.join(PROJ, rel)
    if not os.path.isdir(os.path.dirname(p)):
        os.makedirs(os.path.dirname(p))
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)
    print("  wrote %s" % p)


def main():
    if os.path.isdir(PROJ):
        for name in ("project.godot", "main.tscn", ".godot"):
            pass
    w("project.godot", """config_version=5

[application]

config/name="Mcp088Live"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.8")
""")
    w("main.tscn", """[gd_scene format=3]

[node name="Main" type="Node2D"]

[node name="ColorRect" type="ColorRect" parent="."]
offset_right = 600.0
offset_bottom = 400.0
color = Color(0.9, 0.1, 0.1, 1)
""")
    print("project root: %s" % PROJ)
    return 0


if __name__ == "__main__":
    sys.exit(main())
