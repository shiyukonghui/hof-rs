#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-113 item C: write the content-level `expect` into the readback
declarations of the exercise manifests.

Every literal below was chosen by reading the witness call's **actual payload**
(see `dump_witnesses.py` / `probe_expects.py`) and taking a fragment of the value
the writer wrote, or - for a subtractive write - the absence of what it removed
(`expect_absent`, anchored on the subject with `expect`).

Usage:
    python recovery/work/task113/add_expects.py --check
    python recovery/work/task113/add_expects.py --write
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SESS = os.path.join(ROOT, "tools", "sessions", "_exercises")

# tool -> {"expect": [...], "expect_absent": [...]}
EXPECTS = {
    # --- TASK-111's twenty witness_read declarations (upgraded here) --------
    "editor_add_scene_instance": {"expect": ["\"Sub1\""]},
    "editor_rename_node": {"expect": ["\"name\":\"Ren1\""]},
    "editor_set_node_groups": {"expect": ["\"ex_host\""]},
    "editor_set_physics_layers": {"expect": ["\"collision_layer\":1"]},
    "editor_setup_physics_body": {"expect": ["\"PB1\""]},
    "editor_disconnect_signal": {"expect": ["\"count\":0"]},
    "editor_set_viewport_3d_camera": {"expect": ["\"position\":{\"x\":1.0,\"y\":1.0,\"z\":1.0}"]},
    "editor_create_animation": {"expect": ["\"Anim5\""]},
    "editor_add_animation_track": {"expect": ["\"path\":\"Target:scale\""]},
    "editor_set_animation_keyframe": {"expect": ["\"easing\":2.0", "\"time\":1.0"]},
    "editor_create_animation_tree": {"expect": ["\"parameters/BT/B1/blend_amount\""]},
    "editor_add_state_machine_state": {"expect": ["\"Walk\""]},
    "editor_add_state_machine_transition": {"expect": ["\"Idle\""]},
    "editor_remove_state_machine_transition": {
        "expect": ["\"transition_count\":5"],
        "expect_absent": ["\"from\":\"Idle\",\"index\":0,\"switch_mode\":\"immediate\",\"to\":\"Walk\""],
    },
    "editor_remove_state_machine_state": {
        "expect": ["\"node_path\":\"AT4\""],
        "expect_absent": ["Extra0", "Extra4"],
    },
    "editor_set_blend_tree_node": {"expect": ["parameters/BT/T1/scale"]},
    "editor_set_animation_tree_parameter": {"expect": ["parameters/Walk/backward"]},
    # `editor_set_node_script`, `editor_set_control_theme` and
    # `editor_remove_animation` are deliberately absent from this table: reading
    # their declared runs back shows that no payload of the declared witness
    # contains the written value (or post-dates the removal), so no honest
    # literal exists. They are left without `expect` on purpose and lose the
    # tier - see the TASK-113 report.
    # --- TASK-113's new families -------------------------------------------
    "editor_setup_navigation_region": {"expect": ["\"RegionA\""]},
    "editor_setup_navigation_agent": {"expect": ["\"max_speed\""]},
    "editor_set_navigation_layers": {"expect": ["\"navigation_layers\":2"]},
    "editor_bake_navigation_mesh": {"expect": ["\"baked\":true"]},
    "running_game_move_player_to_target": {"expect": ["\"position\""]},
    "editor_add_audio_bus": {"expect": ["\"Music\""]},
    "editor_add_audio_bus_effect": {"expect": ["AudioEffectAmplify"]},
    "editor_add_audio_player": {"expect": ["AudioStreamPlayer2D"]},
    "editor_set_audio_bus_property": {"expect": ["\"volume_db\":-6"]},
    "editor_create_particles": {"expect": ["\"process_material_slot\":\"process_material\""]},
    "editor_set_particle_preset": {"expect": ["\"amount\":24"]},
    "editor_set_particle_material": {"expect": ["\"damping_min\""]},
    "editor_set_particle_color_gradient": {"expect": ["\"color_stop_count\":2"]},
    "running_game_create_input_recording": {"expect": ["\"event_count\":2"]},
    "running_game_play_input_recording": {"expect": ["\"position\""]},
    "running_game_stop_input_recording": {"expect": ["\"position\""]},
}


def main(argv):
    write = "--write" in argv
    changed = 0
    seen = set()
    for dirpath, _dirs, files in os.walk(SESS):
        for name in sorted(files):
            if not name.endswith("-manifest.json"):
                continue
            path = os.path.join(dirpath, name)
            with io.open(path, "r", encoding="utf-8") as handle:
                doc = json.load(handle)
            readback = doc.get("readback") or []
            if not readback:
                continue
            touched = False
            for item in readback:
                tool = item.get("tool")
                want = EXPECTS.get(tool)
                if want is None:
                    print("NO-EXPECT  %-44s (%s)" % (tool, os.path.relpath(path, ROOT)))
                    continue
                seen.add(tool)
                item["expect"] = want["expect"]
                if want.get("expect_absent"):
                    item["expect_absent"] = want["expect_absent"]
                else:
                    item.pop("expect_absent", None)
                touched = True
            if touched and write:
                with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
                    handle.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
                changed += 1
            print("%-9s %s" % ("patched" if (touched and write) else "would-patch",
                               os.path.relpath(path, ROOT)))
    unused = sorted(set(EXPECTS) - seen)
    if unused:
        print("declared here but no manifest carries it: %s" % ", ".join(unused))
    print("%d manifest(s) %s" % (changed if write else 0,
                                 "written" if write else "in --check mode"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
