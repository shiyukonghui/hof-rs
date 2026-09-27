#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-115: reclassify the H7 register entries that the h7 batch really called,
and record the half that stays out.

Same contract as recovery/work/task114/reclassify_h8.py:

    * `members` is NEVER edited (all 74 entries stay, so the inference's error
      stays auditable);
    * every tool TASK-115 exercised gets (or refreshes) an entry under
      `reclassified` with the run that demonstrated it;
    * the run of this script twice is a no-op: an entry this script wrote before
      is replaced, not appended;
    * the H7 category keeps a `still_out` sub-list naming the five
      editor_simulate_* tools, each with why / evidence / the condition under
      which it would become measurable - because leaving them as a bare
      "structurally unreachable" list is exactly the kind of unqualified claim
      this register exists to prevent.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REGISTRY = os.path.join(ROOT, "tools", "tool_coverage_unreachable.json")

RUN_H7 = "runs/_exercises/ex_editor/h7-task115/trace-editor.jsonl"

# tool -> (why, evidence)
H7_RECLASSIFIED = {
    "editor_play_scene": (
        "the editor's own scene player IS reachable from the editor endpoint: five releases of the project's main/current/custom scene each really created a game child process (--mcp-port 61849/61856/61861/61865/9899 answered in args_injected, pid + endpoint in the answer), and the editor's own run bar state was read back by editor_execute_gdscript -> EditorInterface.is_playing_scene(), true after play and false after the matching stop. The tools that start and stop the editor's player were never about the game endpoint.",
        RUN_H7),
    "editor_stop_scene": (
        "same run: five stops each answered stopped:true and killed the child, a sixth answered {stopped:false, 'No scene playing'} (the documented honest answer, not a failure), and is_playing_scene() read back false. The stop tool is the module's only 'no orphan game process' lever, and this run used it five times with no orphan left (post-run tasklist shows no godot process).",
        RUN_H7),
    "editor_set_node_selection": (
        "the editor's own EditorSelection is writable through the editor endpoint: nine calls (node_paths, node_path, mode=replace/add) each answered with the selection the engine holds, and editor_get_selection read the same node back by name and type (five content-level witnesses).",
        RUN_H7),
    "editor_remove_node_selection": (
        "same run: five clears answered cleared:1/1/1/3/0 and editor_get_selection then answered {\"count\":0,\"nodes\":[]} - the empty selection is a valid, verifiable answer, which is what the register's 'GUI state is not reachable' inference got wrong.",
        RUN_H7),
    "editor_remove_output_log": (
        "the Output panel of the editor process is both readable and clearable here: the panel held 10 lines (including 'Godot Engine v4.8.dev.custom_build') before the clear and one empty line after it, read back by editor_get_output_log in the same run (expect 'in_process':true + expect_absent 'Godot Engine v4.8.dev').",
        RUN_H7),
    "editor_reload_plugin": (
        "with a real addon enabled (projects/_exercises/ex_editor/addons/probe_plugin, listed by ProjectSettings' editor_plugins/enabled) five calls each answered {reloading:true, plugins:['res://addons/probe_plugin/plugin.cfg']}; the enabled list itself was read back by project_get_settings. NOTE: the success is NOT pixel/file observable (verdict ok_no_effect_observed), so this tool's only honest evidence channel is the read-back.",
        RUN_H7),
    "editor_rescan_project_filesystem": (
        "EditorFileSystem::scan() is reachable through the editor endpoint: five calls each answered {reloaded:true}, and project_get_filesystem_tree read the project back with its scenes and addon files after the rescan.",
        RUN_H7),
    "editor_get_test_report": (
        "the register's 'it needs an editor-side test run' inference is wrong by measurement: the tool reads the user:// bridge file the GAME process persists and otherwise answers honestly from this process' accumulator. Five calls each answered source=editor_process with no_results:true (total 0), the opt-in clear:true arm answered cleared:['editor_process'], and a mistyped clear is -32602. It is a read tool, so its own payload is substantive evidence: counted 达标 by tools/tool_coverage.py.",
        RUN_H7),
    "editor_analyze_screenshot_diff": (
        "same class of correction: the comparison is CPU-side (Image::load / load_png_from_buffer) and needs no display server and no editor-side test run at all. Five calls measured real pairs (8x8 identical -> changed_pixels 0; two differing 8x8 PNGs -> changed_pixels 32; threshold 0 and 255 at the inclusive/exclusive ends) and three refusals were measured (missing image -32001, 8x8 vs 16x16 size mismatch -32602, threshold 300 -32602). Counted 达标.",
        RUN_H7),
    "editor_set_auto_dismiss_dialogs": (
        "called seven times, and every well-formed call is the honest -32000 the implementation documents ('this engine has no process-wide auto-dismiss setting for editor dialogs'), plus two -32602 for the malformed ones. So the tool is REACHABLE and its contract is exercised, but it can never produce a success: its provider is a deliberate not-implemented, not a missing subsystem. It therefore stays at evidence tier count_only (7 boundary calls, 0 effective) BY DESIGN, and the register entry for it should read 'measured, boundary-only' rather than 'unreachable'.",
        RUN_H7),
}

H7_STILL_OUT_WHY = (
    "TASK-115 split the original H7 inference in two by measurement. The GUI-state half "
    "(selection, Output panel, run bar, addon list, test-report bridge, screenshot diff) is "
    "reachable and was exercised in runs/_exercises/ex_editor/h7-task115 - see `reclassified`. "
    "What remains out is the five `editor_simulate_*` tools, and the reason is a SCOPE decision "
    "(D59 / GDR-21), not a capability gap: they are compiled into this build, they are "
    "registered on the editor endpoint, and in a real editor the Input / InputMap singletons "
    "they need always exist (`editor_input_simulation.cpp:121-144`: 'Input is created by "
    "Main::setup2 in every engine process, so in a real editor these never fail'). What they "
    "cannot do is drive a running game: they call "
    "`Input::get_singleton()->parse_input_event()` on the EDITOR process' own queue and write "
    "the EDITOR process' own InputMap, so an event injected there never reaches a game child "
    "(REPORT-013 measures exactly that: an EditorPlugin inside the editor counts the event "
    "while the game process' counters stay untouched). The loop deliberately verifies game "
    "behaviour through the game endpoint's `running_game_*` input tools instead, which is why "
    "these five are not part of the corpus."
)

H7_STILL_OUT = {
    "tools": [
        "editor_simulate_key",
        "editor_simulate_mouse_click",
        "editor_simulate_mouse_move",
        "editor_simulate_input_action",
        "editor_simulate_input_sequence",
    ],
    "why": H7_STILL_OUT_WHY,
    "evidence": ("godot/modules/mcp_server/tools/editor_input_simulation.cpp:53-112 "
                 "(the D59 / GDR-21 header) and :121-144 (the Input / InputMap prerequisite); "
                 "docs/tool-rename-map.json's `reason` for each of the five ('only parses the "
                 "event into the editor process' Input'); REPORT-013 (the two-sided wire measurement). "
                 "TASK-115 did NOT call them, so this entry is still an inference about the "
                 "corpus, not a measurement of these five."),
    "measurable_when": (
        "The precondition is not a missing subsystem; it is a decision. They become measurable "
        "the day an editor-side input observation is added to the verification loop, i.e. a run "
        "that (a) drives the EDITOR endpoint with them on purpose, (b) reads the effect out of "
        "the editor process itself (an EditorPlugin or editor_execute_gdscript counting "
        "Input events) rather than out of the game, and (c) declares in the batch's own notes "
        "that the game endpoint is NOT expected to see anything - which is the fact REPORT-013 "
        "already established. Under the current ledger rules such a batch could reach at most "
        "ok_no_effect_observed (an input queue is invisible to the screenshot and file-effect "
        "channels), so it would buy count-coverage plus a boundary, not a tier."),
}

H8_EXTERNAL_DEVICE = {
    "tools": [
        "os_list_android_devices",
        "os_deploy_to_android_device",
        "project_get_android_preset_info",
    ],
    "why": ("Not registered as unreachable: the code path exists and is compiled; what is "
            "absent is the outside world. TASK-114 and TASK-115 both measured 0 calls because "
            "this machine has no Android device attached and no Android SDK/preset, and the "
            "loop's endpoint is the desktop editor. The register therefore keeps them under "
            "'needs an external device', not under 'structurally unreachable'."),
    "evidence": ("tools/tool_coverage.py reports 0 calls for all three in mode=all-runs; "
                 "project_get_android_preset_info needs an export_presets.cfg entry for the "
                 "Android platform (ex_editor ships Windows Desktop presets only), and "
                 "os_list_android_devices / os_deploy_to_android_device need `adb` plus a "
                 "connected device."),
    "measurable_when": ("an Android platform preset is added to an exercise project (an "
                        "offline, SDK-free fact) AND a device or emulator is reachable over "
                        "adb. Until then these three stay out of the miss count by policy."),
}

COMMENT = (
    "TASK-110 batch c23 called six of the register's 'structurally unreachable' tools for real; "
    "TASK-111 batches h1/h2/h3 added 28 more (all of H1, H2 and H3). Every entry stays here with "
    "the run that demonstrated it instead of being deleted silently, so the inference's error "
    "stays auditable. TASK-113 batches h4/h5/h6/h9 added the remaining 20 (all of H4, H5 and H6, "
    "and the three recording tools of H9). TASK-114 added the two H8 export readers. TASK-115 "
    "added the ten reachable H7 members (the batch that also SPLIT the H7 inference: the "
    "editor_simulate_* five stay out by the D59 / GDR-21 scope decision, recorded under "
    "categories.H7.still_out, and the three H8 Android tools are recorded as needing an external "
    "device under categories.H8.external_device). 66 of the 74 members are now measured."
)


def main():
    with io.open(REGISTRY, "r", encoding="utf-8") as handle:
        doc = json.load(handle)

    existing = {r["tool"]: i for i, r in enumerate(doc.get("reclassified") or [])}
    added, refreshed = 0, 0
    for tool, (why, evidence) in H7_RECLASSIFIED.items():
        entry = {
            "tool": tool,
            "from": "H7",
            "why": why,
            "evidence": evidence,
            "batch": "h7",
            "task": "TASK-115",
        }
        if tool in existing:
            doc["reclassified"][existing[tool]] = entry
            refreshed += 1
        else:
            doc["reclassified"].append(entry)
            added += 1

    doc["categories"]["H7"]["still_out"] = H7_STILL_OUT
    doc["categories"]["H7"]["why_unreachable"] = (
        "SUPERSEDED BY MEASUREMENT (TASK-115). The original inference below was a single "
        "claim about a mixed family, and it was wrong for ten of its nineteen members: the "
        "editor's own GUI state (selection, Output panel, run bar, addon list, test-report "
        "bridge file, screenshot diff) is fully readable and writable through the editor "
        "endpoint. What is really left is the five editor_simulate_* tools, whose exclusion "
        "is a scope decision (D59 / GDR-21), not a missing subsystem - see `still_out`. "
        "ORIGINAL TEXT, kept for audit: " + doc["categories"]["H7"].get("why_unreachable", "")
    )
    doc["categories"]["H7"]["supporting_evidence"] = (
        "TASK-115: runs/_exercises/ex_editor/h7-task115 (82 calls, 169 named tools in the "
        "whole corpus after the batch); tools/sessions/_exercises/ex_editor/h7-manifest.json "
        "(7 content-level read-back declarations, all verified). ORIGINAL TEXT, kept for "
        "audit: " + doc["categories"]["H7"].get("supporting_evidence", "")
    )

    doc["categories"]["H8"]["external_device"] = H8_EXTERNAL_DEVICE
    doc["_reclassified_comment"] = COMMENT
    doc["_task115_note"] = (
        "TASK-115 edited `categories.H7.why_unreachable` / `supporting_evidence` (appending, "
        "never deleting, the original inference with an explicit 'SUPERSEDED BY MEASUREMENT' "
        "marker) and added `categories.H7.still_out` + `categories.H8.external_device`. "
        "`members` was not touched: all 74 entries are still there."
    )

    with io.open(REGISTRY, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")

    print("reclassify_h7: members=%d (unchanged), reclassified=%d (added %d, refreshed %d)"
          % (len(doc["members"]), len(doc["reclassified"]), added, refreshed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
