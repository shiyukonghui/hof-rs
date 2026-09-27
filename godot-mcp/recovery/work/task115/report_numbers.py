#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-115: print the rows the report has to quote, straight out of coverage.json
so no number in the report is retyped."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

GROUPS = {
    "H7 (TASK-115 h7 batch)": [
        "editor_play_scene", "editor_stop_scene", "editor_set_node_selection",
        "editor_remove_node_selection", "editor_remove_output_log",
        "editor_reload_plugin", "editor_rescan_project_filesystem",
        "editor_get_test_report", "editor_analyze_screenshot_diff",
        "editor_set_auto_dismiss_dialogs",
    ],
    "H1 count_only -> readback (h1b)": [
        "editor_add_mesh_instance", "editor_setup_camera_3d", "editor_setup_lighting",
        "editor_set_material_3d", "editor_setup_world_environment",
    ],
    "TASK-113 downgraded witnesses (c4b / h2c)": [
        "editor_set_node_script", "editor_set_control_theme", "editor_remove_animation",
    ],
    "still 0 calls": [
        "editor_simulate_key", "editor_simulate_mouse_click", "editor_simulate_mouse_move",
        "editor_simulate_input_action", "editor_simulate_input_sequence",
        "os_list_android_devices", "project_get_android_preset_info",
        "os_deploy_to_android_device",
    ],
}


def main():
    with io.open(os.path.join(ROOT, "coverage.json"), "r", encoding="utf-8") as handle:
        cov = json.load(handle)
    rows = {r["tool"]: r for r in cov["tools"]}
    for title, tools in GROUPS.items():
        print("== %s ==" % title)
        print("%-42s %5s %5s %6s %-14s %-22s %s"
              % ("tool", "calls", "eff", "bnd", "tier", "readback", "status"))
        for name in tools:
            row = rows[name]
            rb = row.get("readback") or {}
            if rb.get("kind") == "witness_read":
                rbtext = "%s@%s" % (rb.get("witness_tool"), rb.get("witness_seq"))
            elif rb.get("kind") == "own_payload":
                rbtext = "own_payload"
            else:
                rbtext = "-"
            print("%-42s %5d %5d %6d %-14s %-22s %s"
                  % (name, row["calls"], row["effective"], row["boundary"],
                     row["evidence_tier"], rbtext, row["status"]))
        print()
    c = cov["corpus"]
    print("corpus: runs=%d traces=%d calls=%d distinct=%d failed=%d"
          % (c["run_dirs"], c["trace_files"], c["calls"], c["distinct_tools"], c["failed"]))
    print("buckets: %s" % cov["buckets"])
    print("status : %s" % cov["status_counts"])
    print("tier   : %s" % cov["evidence_tier_counts"])
    rb = cov["readback_declarations"]
    print("readback declarations: declared=%d verified=%d with_expect=%d content_checked=%d rejected=%d"
          % (rb["declared"], rb["verified"], rb["declared_with_expect"], rb["content_checked"],
             len(rb["rejected"])))
    reg = cov["unreachable_registry"]
    print("registry: members=%d drift=%d reclassified=%d"
          % (reg["members_total"], len(reg["drift"]), len(reg["reclassified"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
