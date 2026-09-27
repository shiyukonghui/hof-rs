#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-111: reclassify the H1 / H2 / H3 families in the unreachable register.

TASK-108 section 5.3 inferred these three families were structurally unreachable
because the 20-game corpus is 2D-only and never uses AnimationPlayer or
TileMapLayer. The inference is about the corpus, not about the tools: this batch
built three exercise projects that ship the one precondition each family actually
needs, and called every member of the family for real.

The register's own rule is explicit: never delete an entry silently - move it to
`reclassified` with the demonstration. That is what this script does.

Usage: python recovery/work/task111/reclassify.py
"""
import io
import json
import os

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
REGISTRY = os.path.join(ROOT, "tools", "tool_coverage_unreachable.json")

H1_RUN = "runs/_exercises/ex_3d/h1-task111/trace-editor.jsonl"
H2_RUN = "runs/_exercises/ex_anim2/h2b-task111/trace-editor.jsonl"
H3_RUN = "runs/_exercises/ex_grid/h3-task111/trace-editor.jsonl"

H1_TOOLS = ["editor_add_mesh_instance", "editor_set_material_3d", "editor_setup_camera_3d",
            "editor_set_viewport_3d_camera", "editor_get_viewport_3d_camera",
            "editor_setup_lighting", "editor_setup_world_environment"]
H2_TOOLS = ["editor_create_animation", "editor_add_animation_track", "editor_set_animation_keyframe",
            "editor_remove_animation", "editor_list_animations", "editor_get_animation_info",
            "editor_create_animation_tree", "editor_get_animation_tree_structure",
            "editor_add_state_machine_state", "editor_add_state_machine_transition",
            "editor_remove_state_machine_state", "editor_remove_state_machine_transition",
            "editor_set_blend_tree_node", "editor_set_animation_tree_parameter"]
H3_TOOLS = ["editor_add_gridmap", "editor_get_tilemap_cell", "editor_get_tilemap_info",
            "editor_get_tilemap_used_cells", "editor_remove_all_tilemap_cells",
            "editor_set_tilemap_cell", "editor_set_tilemap_cells_in_rect"]

WHY = {
    "H1": ("the corpus has no 3D scene, but the family needs only a project that ships one: "
           "projects/_exercises/ex_3d carries scenes/probe3d.tscn (Node3D root + a MeshInstance3D "
           "with a BoxMesh) and every member of H1 then ran for real - the camera tools answer with "
           "the engine's own viewport read-back, the lighting/environment tools create their nodes, "
           "and editor_set_material_3d assigns a StandardMaterial3D to the surface."),
    "H2": ("the corpus drives motion with its own integer kinematics, but the family needs only an "
           "AnimationPlayer with a default library plus a node for a track to address: "
           "projects/_exercises/ex_anim2 carries scenes/anim.tscn (AnimRoot / Target / Player). All "
           "14 members ran: 8 animations, 3 value tracks with keys, 5 AnimationTrees whose root the "
           "tool makes an AnimationNodeStateMachine, 11 states, 10 transitions, 5 blend-tree nodes "
           "and 5 parameter writes, each with a boundary probe."),
    "H3": ("the write half's own contract said the caller must supply a TileSet that already holds a "
           "TileSetAtlasSource, and none of the 20 games does. projects/_exercises/ex_grid supplies "
           "exactly that (assets/tileset.tres + scenes/grid.tscn, built by mk_probe.gd from the "
           "engine's own ResourceSaver, plus assets/meshlib.tres for editor_add_gridmap). With it, "
           "editor_set_tilemap_cell and editor_set_tilemap_cells_in_rect succeed - the exact "
           "precondition the description names - and the readers report the cells back."),
}


def main():
    with io.open(REGISTRY, "r", encoding="utf-8") as handle:
        doc = json.load(handle)
    existing = {entry["tool"] for entry in doc.get("reclassified") or []}
    entries = []
    for code, tools, run in (("H1", H1_TOOLS, H1_RUN), ("H2", H2_TOOLS, H2_RUN),
                             ("H3", H3_TOOLS, H3_RUN)):
        for tool in tools:
            if tool in existing:
                continue
            entries.append({"tool": tool, "from": code, "why": WHY[code], "evidence": run,
                            "batch": {"H1": "h1", "H2": "h2b", "H3": "h3"}[code],
                            "task": "TASK-111"})
    doc["reclassified"] = (doc.get("reclassified") or []) + entries
    doc["_reclassified_comment"] = (
        "TASK-110 batch c23 called six of the register's 'structurally unreachable' tools for real; "
        "TASK-111 batches h1/h2/h3 added 28 more (all of H1, H2 and H3). Every entry stays here with "
        "the run that demonstrated it instead of being deleted silently, so the inference's error "
        "stays auditable.")
    with io.open(REGISTRY, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    print("reclassified: +%d (total %d)" % (len(entries), len(doc["reclassified"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
