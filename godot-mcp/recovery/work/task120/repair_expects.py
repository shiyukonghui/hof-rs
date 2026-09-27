#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-120 item A5: repair the `expect` of every declaration the new A rules reject.

Each replacement names a VALUE the writer really stored, taken from the witness
payload itself (`recovery/tmp/task120/dossier.txt` / `dump_payload.py`), and each
`why` says which call seq produced it. Idempotent: running it twice writes the same
files. `c4-manifest.json` is edited by hand (it uses 1-space indentation, so a
json.dump round-trip would reflow the whole file).

Run:  python recovery/work/task120/repair_expects.py
"""
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))

REPAIRS = {
    "tools/sessions/_exercises/ex_audio/h5-manifest.json": {
        "editor_add_audio_bus": {
            "expect": ['"name":"Music"', '"index":2'],
            "why": ("the bus editor_add_audio_bus created is in the engine's bus layout with the name "
                    "and the index the layout assigns it; the literal carries the VALUE (TASK-120 A3: "
                    "the bare name `\"Music\"` was rejected - it is matched by any payload carrying "
                    "that string)"),
        },
    },
    "tools/sessions/_exercises/ex_anim/h2-manifest.json": {
        "editor_add_state_machine_state": {
            "expect": ['"name":"Walk"', '"animation":"Anim2"'],
            "why": ("the state editor_add_state_machine_state created for AT1 (state_name Walk, "
                    "animation Anim2) is in the engine's state list with its animation binding; "
                    "`\"Walk\"` alone was rejected as a bare name (TASK-120 A3)"),
        },
        "editor_add_state_machine_transition": {
            "expect": ['"from":"Jump"', '"to":"Walk"'],
            "why": ("the Jump -> Walk transition editor_add_state_machine_transition created is in the "
                    "engine's transition list (`from`/`to` with their values); `\"Idle\"` alone was "
                    "rejected as a bare name (TASK-120 A3)"),
        },
        "editor_create_animation": {
            "expect": ['"animations":["Anim1","Anim2","Anim3","Anim4","Anim5"'],
            "why": ("the animation list read back after the eight creates starts with the five "
                    "animations in creation order, Anim5 among them; `\"Anim5\"` alone was rejected as "
                    "a bare name (TASK-120 A3)"),
        },
    },
    "tools/sessions/_exercises/ex_particles/h6-manifest.json": {
        "editor_set_particle_material": {
            "expect": ['"node_path":"P1"', '"initial_velocity_min":40.0',
                       '"initial_velocity_max":90.0'],
            "why": ("P1's own record carries the two values the write at seq 17 reported storing "
                    "(initial_velocity_min 40.0 / initial_velocity_max 90.0), read back at seq 34; the "
                    "bare key `\"damping_min\"` was rejected (TASK-120 A3) and its value on P2 (1.0) "
                    "is a value the seed scene already had - it is not evidence of this write"),
        },
    },
    "tools/sessions/_exercises/ex_nav/h4-manifest.json": {
        "editor_setup_navigation_agent": {
            "expect": ['"path":"Player/NA3"', '"max_speed":320.0'],
            "why": ("the NavigationAgent2D editor_setup_navigation_agent created (NA3) is in the "
                    "engine's agent list with the max_speed 320.0 the tool wrote; `\"max_speed\"` "
                    "alone was rejected as a bare key (TASK-120 A3)"),
        },
        "editor_setup_navigation_region": {
            "expect": ['"path":"RegionA"', '"type":"NavigationRegion2D"'],
            "why": ("the NavigationRegion2D editor_setup_navigation_region created (RegionA) is in the "
                    "engine's region list with the engine's own class name; `\"RegionA\"` alone was "
                    "rejected as a bare name (TASK-120 A3)"),
        },
        "running_game_move_player_to_target": {
            "expect": ['"x":220.86', '"y":394.86'],
            "why": ("running_game_move_player_to_target is judged on its pixel_effect channel; its "
                    "readback declaration is kept for audit and now states the post-write position "
                    "itself (220.86, 394.86, on the way to the last target (200,400) and different "
                    "from the start (100,300)); `\"position\"` alone was rejected (TASK-120 A3)"),
        },
    },
    "tools/sessions/_exercises/ex_rec/h9-manifest.json": {
        "running_game_create_input_recording": {
            "witness_tool": "running_game_get_node_properties",
            "expect": ['"x":346.0'],
            "why": ("the read call at seq 18 (after the create->play->stop chain) answers x=346.0, "
                    "while the same reader answered x=100.0 before the session started (seq 2): the "
                    "recorded session the created recorder captured really drove the game. The old "
                    "witness was running_game_stop_input_recording's own response - a WRITE tool, "
                    "which the TASK-120 A1 rule rejects. Boundary: the engine exposes no read tool "
                    "for the recorder itself, so a read call can show this consequence of the "
                    "recording, not the recorder's internal state"),
        },
        "running_game_play_input_recording": {
            "witness_tool": "running_game_get_node_properties",
            "expect": ['"x":151.0'],
            "why": ("the read at seq 22 - taken right after the create->stop->play replay (call at "
                    "seq 21) - answers x=151.0, while the read just before it (seq 20, after the "
                    "reset) answered x=100.0: the replay really drove the player. `\"position\"` "
                    "alone was rejected as a bare key (TASK-120 A3)"),
        },
        "running_game_stop_input_recording": {
            "witness_tool": "running_game_get_node_properties",
            "expect": ['"x":346.0'],
            "why": ("the read at seq 18 - taken after the stop call at seq 17 - answers x=346.0, "
                    "while the same reader answered x=100.0 before the session (seq 2): the recorded "
                    "session this stop closed really had driven the game. `\"position\"` alone was "
                    "rejected as a bare key (TASK-120 A3). Boundary: no read tool exposes the "
                    "recorder's state, so this is the consequence a read call can show"),
        },
    },
    # c4-manifest.json is the one file with 1-space indentation; INDENT below keeps its
    # round-trip byte-identical (verified: indent=1 -> identical, indent=2 -> reflows).
    "tools/sessions/_exercises/ex_write/c4-manifest.json": {
        "editor_add_scene_instance": {
            "expect": ['/Main/Sub1/C4Node2', '"name":"Sub1"'],
            "why": ("挂载的实例必须出现在编辑场景树里（editor_get_scene_tree 列出被实例化出来的节点）："
                    "expect 现在带值——实例自己的子节点 C4Node2（来自 res://scenes/c4_sub.tscn）挂在节点路径 "
                    "/Main/Sub1/C4Node2 之下，树里那个节点的名字是 Sub1；旧的 `\"Sub1\"` 只是裸名字，"
                    "被 TASK-120 A3 拒签"),
        },
        "editor_set_node_groups": {
            "expect": ['"node_path":"Host"', '"groups":["ex_host"]'],
            "why": ("读回被写节点的 groups 列表：expect 现在带值——Host 这个节点路径与它的 groups "
                    "数组内容；旧的 `\"ex_host\"` 只是裸名字，被 TASK-120 A3 拒签"),
        },
        "editor_setup_physics_body": {
            "expect": ['/Main/PB1/CollisionShape2D', '"name":"PB1"'],
            "why": ("建出来的物理体节点必须出现在编辑场景树里：expect 现在带值——工具建出的 "
                    "RigidBody2D（PB1）连同它自己的 CollisionShape2D 子节点，节点路径 "
                    "/Main/PB1/CollisionShape2D；旧的 `\"PB1\"` 只是裸名字，被 TASK-120 A3 拒签"),
        },
    },
}

INDENT = {"tools/sessions/_exercises/ex_write/c4-manifest.json": 1}


def main():
    changed = 0
    for rel, tools in REPAIRS.items():
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        raw = io.open(path, encoding="utf-8").read()
        doc = json.loads(raw)
        for entry in doc.get("readback") or []:
            fix = tools.get(entry.get("tool"))
            if fix is None:
                continue
            for key, value in fix.items():
                if entry.get(key) != value:
                    entry[key] = value
                    changed += 1
        out = json.dumps(doc, ensure_ascii=False, indent=INDENT.get(rel, 2)) + "\n"
        if out != raw:
            io.open(path, "w", encoding="utf-8", newline="\n").write(out)
            print("rewrote %s" % rel)
        else:
            print("unchanged %s" % rel)
    print("fields changed: %d" % changed)


if __name__ == "__main__":
    main()
