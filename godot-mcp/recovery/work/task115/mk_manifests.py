#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-115: write the four batch manifests (calls[] + readback[]) from the
sessions that were really run.

The `calls` half is derived from the session files (tag / tool / port / note), so
it cannot drift from what the runner replayed; only `intent` is computed, by the
same rule the older manifests use:

    * a tag ending in `-probe` (or one the note calls a boundary) -> "probe";
    * a note that says setup / read-back / read-back witness      -> "setup";
    * everything else                                            -> "ok".

The `readback` half is the hand-written part: one declaration per writer, each
carrying the `expect` (and, for a removal, the `expect_absent`) that
tools/tool_coverage.py re-searches in the witness call's own payload.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SESS = os.path.join(ROOT, "tools", "sessions", "_exercises")

BATCHES = [
    {
        "manifest": "ex_editor/h7-manifest.json",
        "session": "ex_editor/h7-session.json",
        "batch": "h7",
        "project": "_exercises/ex_editor",
        "readback": [
            {
                "tool": "editor_remove_output_log",
                "witness_tool": "editor_get_output_log",
                "run": "runs/_exercises/ex_editor/h7-task115",
                "why": "the Output panel of THIS editor process is readable in-process, and after the clear the engine's own log no longer holds the startup lines it held before it (count 10 -> 1 empty line)",
                "expect": ["\"in_process\":true"],
                "expect_absent": ["Godot Engine v4.8.dev"],
            },
            {
                "tool": "editor_set_node_selection",
                "witness_tool": "editor_get_selection",
                "run": "runs/_exercises/ex_editor/h7-task115",
                "why": "the editor's own EditorSelection really answers with the node the tool selected",
                "expect": ["\"name\":\"Box\"", "\"type\":\"ColorRect\""],
            },
            {
                "tool": "editor_remove_node_selection",
                "witness_tool": "editor_get_selection",
                "run": "runs/_exercises/ex_editor/h7-task115",
                "why": "after the clear the editor's own EditorSelection really is empty, while the same reader had answered a non-empty list earlier in the run",
                "expect": ["\"count\":0", "\"nodes\":[]"],
            },
            {
                "tool": "editor_reload_plugin",
                "witness_tool": "project_get_settings",
                "run": "runs/_exercises/ex_editor/h7-task115",
                "why": "the addon the tool disabled and enabled again is the one ProjectSettings really lists as enabled",
                "expect": ["res://addons/probe_plugin/plugin.cfg"],
            },
            {
                "tool": "editor_rescan_project_filesystem",
                "witness_tool": "project_get_filesystem_tree",
                "run": "runs/_exercises/ex_editor/h7-task115",
                "why": "after the rescan the project's own filesystem tree still answers with the scene it swept",
                "expect": ["editor_probe.tscn"],
            },
            {
                "tool": "editor_play_scene",
                "witness_tool": "editor_execute_gdscript",
                "run": "runs/_exercises/ex_editor/h7-task115",
                "why": "the editor's own run bar reports playing after the tool answered playing:true, and reports not playing after the matching stop",
                "expect": ["\"result\":true"],
            },
            {
                "tool": "editor_stop_scene",
                "witness_tool": "editor_execute_gdscript",
                "run": "runs/_exercises/ex_editor/h7-task115",
                "why": "after the stop the editor's own run bar reports is_playing_scene() == false",
                "expect": ["\"result\":false"],
            },
        ],
    },
    {
        "manifest": "ex_3d/h1b-manifest.json",
        "session": "ex_3d/h1b-session.json",
        "batch": "h1b",
        "project": "_exercises/ex_3d",
        "readback": [
            {
                "tool": "editor_add_mesh_instance",
                "witness_tool": "editor_get_scene_tree",
                "run": "runs/_exercises/ex_3d/h1b2-task115",
                "why": "the MeshInstance3D the tool created is in the edited scene tree under the exact name it was given",
                "expect": ["\"name\":\"N1\"", "\"type\":\"MeshInstance3D\""],
            },
            {
                "tool": "editor_set_material_3d",
                "witness_tool": "editor_execute_gdscript",
                "run": "runs/_exercises/ex_3d/h1b2-task115",
                "why": "the engine's own MeshInstance3D::get_surface_override_material(0) answers with the material this run assigned",
                "expect": ["M:res://assets/mat3d_b.tres"],
            },
            {
                "tool": "editor_setup_camera_3d",
                "witness_tool": "editor_execute_gdscript",
                "run": "runs/_exercises/ex_3d/h1b2-task115",
                "why": "the node the tool created under the named parent really is a Camera3D",
                "expect": ["C:Camera3D"],
            },
            {
                "tool": "editor_setup_lighting",
                "witness_tool": "editor_execute_gdscript",
                "run": "runs/_exercises/ex_3d/h1b2-task115",
                "why": "the node the tool created under the named parent really is the DirectionalLight3D the first call asked for",
                "expect": ["L:DirectionalLight3D"],
            },
            {
                "tool": "editor_setup_world_environment",
                "witness_tool": "editor_execute_gdscript",
                "run": "runs/_exercises/ex_3d/h1b2-task115",
                "why": "the node the tool created for world_env_path really is a WorldEnvironment",
                "expect": ["E:WorldEnvironment"],
            },
        ],
    },
    {
        "manifest": "ex_write5/c4b-manifest.json",
        "session": "ex_write5/c4b-session.json",
        "batch": "c4b",
        "project": "_exercises/ex_write5",
        "readback": [
            {
                "tool": "editor_set_node_script",
                "witness_tool": "editor_execute_gdscript",
                "run": "runs/_exercises/ex_write5/c4b-task115",
                "why": "the node the tool named really carries that script: the engine's own Node.get_script().resource_path answers it (editor_get_node_properties cannot answer 'script' by name at all - measured -32001 in c4-v5-task111 seq 141)",
                "expect": ["S:res://src/exc4b.gd"],
            },
            {
                "tool": "editor_set_control_theme",
                "witness_tool": "editor_execute_gdscript",
                "run": "runs/_exercises/ex_write5/c4b-task115",
                "why": "the Control the tool named really carries that theme: the engine's own Control.theme.resource_path answers it",
                "expect": ["T:res://themes/c4b.tres"],
            },
        ],
    },
    {
        "manifest": "ex_anim2/h2c-manifest.json",
        "session": "ex_anim2/h2c-session.json",
        "batch": "h2c",
        "project": "_exercises/ex_anim2",
        "readback": [
            {
                "tool": "editor_remove_animation",
                "witness_tool": "editor_list_animations",
                "run": "runs/_exercises/ex_anim2/h2c-task115",
                "why": "the same AnimationPlayer is read back after the removals, and none of the five names this run created and removed is in the library any more (the run's own earlier read, before the removals, is skipped because it still holds them)",
                "expect": ["\"node_path\":\"Player\""],
                "expect_absent": ["DelA", "DelB", "DelC", "DelD", "DelE"],
            },
        ],
    },
]


def intent_of(call):
    tag = call.get("tag") or ""
    note = call.get("note") or ""
    if tag.endswith("-probe") or "boundary" in note:
        return "probe"
    lowered = note.lower()
    if ("setup" in lowered or "read-back" in lowered
            or note.startswith("setup read") or note.startswith("read the")):
        return "setup"
    return "ok"


def main():
    for spec in BATCHES:
        session_path = os.path.join(SESS, spec["session"])
        with io.open(session_path, "r", encoding="utf-8") as handle:
            session = json.load(handle)
        calls = []
        for call in session["calls"]:
            if not call.get("tool"):
                continue
            calls.append({
                "tag": call.get("tag"),
                "tool": call.get("tool"),
                "port": call.get("port"),
                "intent": intent_of(call),
                "note": call.get("note"),
            })
        manifest = {
            "_comment": session.get("_comment"),
            "batch": spec["batch"],
            "project": spec["project"],
            "calls": calls,
            "readback": spec["readback"],
        }
        out = os.path.join(SESS, spec["manifest"])
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with io.open(out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        counts = {}
        for call in calls:
            counts[call["intent"]] = counts.get(call["intent"], 0) + 1
        print("wrote %s : %d calls %s, %d readback declaration(s)"
              % (os.path.relpath(out, ROOT), len(calls), counts, len(spec["readback"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
