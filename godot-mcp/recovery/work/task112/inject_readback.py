#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-112 item B: inject the `readback` declarations into the session manifests.

A declaration is the *claim* that an independent read call in the same run read
back what a write call wrote. It is written here by hand (the pairing is a
semantic judgement - which reader reads the object the writer wrote - and cannot
be derived from the trace), and `tools/tool_coverage.py` re-verifies every one of
them against the run's own rows before it grants the `readback` tier.

Run:  python recovery/work/task112/inject_readback.py [--check]
      --check only prints what is already declared (no write).
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SESS = os.path.join(ROOT, "tools", "sessions", "_exercises")

# (manifest, writer, run, witness, why)
DECLARATIONS = [
    # --- c4-v5 (the A batch's closing run) ---------------------------------
    ("ex_write/c4-manifest.json", "editor_add_scene_instance",
     "runs/_exercises/ex_write5/c4-v5-task111", "editor_get_scene_tree",
     "挂载的实例必须出现在编辑场景树里（editor_get_scene_tree 列出被实例化出来的节点）"),
    ("ex_write/c4-manifest.json", "editor_rename_node",
     "runs/_exercises/ex_write5/c4-v5-task111", "editor_get_node_properties",
     "读回被改名节点的 name（重命名后按新名字仍可寻址）"),
    ("ex_write/c4-manifest.json", "editor_set_node_groups",
     "runs/_exercises/ex_write5/c4-v5-task111", "editor_get_node_groups",
     "读回被写节点的 groups 列表"),
    ("ex_write/c4-manifest.json", "editor_set_node_script",
     "runs/_exercises/ex_write5/c4-v5-task111", "editor_get_node_properties",
     "读回被写节点的 script 属性（不是工具自己响应里的 attached:true）"),
    ("ex_write/c4-manifest.json", "editor_set_physics_layers",
     "runs/_exercises/ex_write5/c4-v5-task111", "editor_get_node_properties",
     "读回同一个节点的 collision_layer / collision_mask"),
    ("ex_write/c4-manifest.json", "editor_setup_physics_body",
     "runs/_exercises/ex_write5/c4-v5-task111", "editor_get_scene_tree",
     "建出来的物理体节点必须出现在编辑场景树里"),
    ("ex_write/c4-manifest.json", "editor_set_control_theme",
     "runs/_exercises/ex_write5/c4-v5-task111", "editor_get_node_properties",
     "读回同一个 Control 的 theme 属性（不是工具自己响应里的 applied:true）"),
    ("ex_write/c4-manifest.json", "editor_connect_signal",
     "runs/_exercises/ex_write5/c4-v5-task111", "editor_list_signal_connections",
     "读回同一节点的连接表，连接真的在里面"),
    # --- c5 ----------------------------------------------------------------
    ("ex_write6/c5-manifest.json", "editor_disconnect_signal",
     "runs/_exercises/ex_write6/c5-task111", "editor_list_signal_connections",
     "断开之后再读一次连接表：count=0（同一次运行、同一个节点）"),
    # --- H1 3D -------------------------------------------------------------
    ("ex_3d/h1-manifest.json", "editor_set_viewport_3d_camera",
     "runs/_exercises/ex_3d/h1-task111", "editor_get_viewport_3d_camera",
     "下一次调用读回上一次写入的 fov/position"),
    # --- H2 动画 -----------------------------------------------------------
    ("ex_anim/h2-manifest.json", "editor_create_animation",
     "runs/_exercises/ex_anim2/h2b-task111", "editor_list_animations",
     "读回动画列表，新建的动画在其中"),
    ("ex_anim/h2-manifest.json", "editor_add_animation_track",
     "runs/_exercises/ex_anim2/h2b-task111", "editor_get_animation_info",
     "读回同一动画的轨道表"),
    ("ex_anim/h2-manifest.json", "editor_set_animation_keyframe",
     "runs/_exercises/ex_anim2/h2b-task111", "editor_get_animation_info",
     "读回同一动画的关键帧"),
    ("ex_anim/h2-manifest.json", "editor_remove_animation",
     "runs/_exercises/ex_anim2/h2b-task111", "editor_list_animations",
     "读回动画列表，被删的动画不在了"),
    ("ex_anim/h2-manifest.json", "editor_create_animation_tree",
     "runs/_exercises/ex_anim2/h2b-task111", "editor_get_animation_tree_structure",
     "读回 AnimationTree 的结构（tree_root / 状态机）"),
    ("ex_anim/h2-manifest.json", "editor_add_state_machine_state",
     "runs/_exercises/ex_anim2/h2b-task111", "editor_get_animation_tree_structure",
     "读回状态机里的状态列表"),
    ("ex_anim/h2-manifest.json", "editor_remove_state_machine_state",
     "runs/_exercises/ex_anim2/h2b-task111", "editor_get_animation_tree_structure",
     "读回状态机里的状态列表，被删的状态不在了"),
    ("ex_anim/h2-manifest.json", "editor_add_state_machine_transition",
     "runs/_exercises/ex_anim2/h2b-task111", "editor_get_animation_tree_structure",
     "读回状态机里的迁移列表"),
    ("ex_anim/h2-manifest.json", "editor_remove_state_machine_transition",
     "runs/_exercises/ex_anim2/h2b-task111", "editor_get_animation_tree_structure",
     "读回状态机里的迁移列表，被删的迁移不在了"),
    ("ex_anim/h2-manifest.json", "editor_set_blend_tree_node",
     "runs/_exercises/ex_anim2/h2b-task111", "editor_get_animation_tree_structure",
     "读回混合树节点真的挂在树上"),
    ("ex_anim/h2-manifest.json", "editor_set_animation_tree_parameter",
     "runs/_exercises/ex_anim2/h2b-task111", "editor_get_animation_tree_structure",
     "读回参数表里出现被写的参数"),
    # --- H3 TileMap / GridMap ---------------------------------------------
    ("ex_grid/h3-manifest.json", "editor_add_gridmap",
     "runs/_exercises/ex_grid/h3-task111", "editor_get_scene_tree",
     "建出来的 GridMap 节点必须出现在编辑场景树里"),
]


def main(argv):
    check = "--check" in argv
    by_manifest = {}
    for manifest, writer, run, witness, why in DECLARATIONS:
        by_manifest.setdefault(manifest, []).append({
            "tool": writer, "run": run, "witness_tool": witness, "why": why,
        })
    for manifest, entries in sorted(by_manifest.items()):
        path = os.path.join(SESS, manifest.replace("/", os.sep))
        with io.open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        existing = text.find('"readback"')
        if check:
            print("%-32s readback present=%s entries=%d"
                  % (manifest, existing >= 0, len(entries)))
            continue
        if existing >= 0:
            print("%-32s already declares readback; left alone" % manifest)
            continue
        body = json.dumps(entries, ensure_ascii=False, indent=4)
        body = "\n".join("  " + line if line.strip() else line
                         for line in body.splitlines())
        # the manifest's own array closes with `  ]` right before the final `}`
        needle = "  ]\n}\n"
        if not text.endswith(needle):
            sys.stderr.write("inject_readback: %s does not end with %r\n" % (manifest, needle))
            return 2
        text = text[: -len(needle)] + "  ],\n  \"readback\": " + body.lstrip() + "\n}\n"
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        print("%-32s injected %d declaration(s)" % (manifest, len(entries)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
